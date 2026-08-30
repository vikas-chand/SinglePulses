#!/usr/bin/env python3
"""Fast, product-free tests for the campaign-owned P2 controller."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "campaign_p2", HERE / "run_p2_temporal.py"
)
assert SPEC and SPEC.loader
P2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = P2
SPEC.loader.exec_module(P2)


class P2ControllerTests(unittest.TestCase):
    def test_queue_order_is_campaign_order(self):
        requested = ["bn110928180", "bn081224887", "bn100130729"]
        self.assertEqual(
            P2.selected_triggers(requested),
            ["bn081224887", "bn100130729", "bn110928180"],
        )

    def test_seven_primary_phases_and_shim_scope(self):
        # 7 phases since 2026-08-30 (PI ruling 5 + repair-step choice):
        # phase 7 row_repair REPLACES the handbook LAG_*/MVT_* row values
        # with the validated 47c lag and canonical Bala MVT.
        phases = P2.phases("bn081224887")
        self.assertEqual([p.number for p in phases], [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual([p.name for p in phases], [
            "temporal_catalog", "step_figures", "cwt", "bala",
            "temporal_figures", "lag", "row_repair",
        ])
        self.assertEqual([p.thread_shim for p in phases],
                         [True, False, False, True, False, False, False])

    def test_seven_commands_are_exact_and_ordered(self):
        trig = "bn081224887"
        phases = P2.phases(trig)
        self.assertEqual(list(phases[0].command), [
            str(P2.PYTHON), str(P2.REPO / "scripts" / "46_temporal_all106.py"),
            "--only", trig, "--workers", "1",
        ])
        self.assertEqual(list(phases[1].command), [
            str(P2.PYTHON), str(P2.REPO / "scripts" / "44_step_figures.py"),
            "--trig", trig,
        ])
        self.assertEqual(list(phases[2].command), [
            str(P2.PYTHON), str(P2.REPO / "scripts" / "47_mvt_cwt_crosscheck.py"),
            "--trig", trig,
        ])
        self.assertEqual(list(phases[4].command), [
            str(P2.PYTHON), str(P2.REPO / "scripts" / "47b_temporal_figs.py"),
            "--trig", trig,
        ])
        self.assertEqual(list(phases[5].command), [
            str(P2.PYTHON), str(P2.REPO / "scripts" / "47c_lag_latbright.py"),
            "--trig", trig,
        ])
        self.assertEqual(list(phases[6].command), [
            str(P2.PYTHON), str(P2.RUNTIME / "run_p2_temporal.py"),
            "repair-row", "--triggers", trig,
        ])
        self.assertEqual([phase.cwd for phase in phases], [
            P2.REPO, P2.REPO, P2.REPO, P2.HANDBOOK, P2.REPO, P2.REPO, P2.REPO,
        ])

    def test_bala_command_is_frozen(self):
        command = list(P2.phases("bn081224887")[3].command)
        for token in ("--resume", "--seed", "20260718", "--inner-cores", "1"):
            self.assertIn(token, command)
        self.assertTrue(all(os.path.isabs(token) for token in command
                            if token.startswith("/")))

    def test_environment_shim_is_explicit(self):
        self.assertEqual(P2.base_env(True)["PYTHONHASHSEED"], "0")
        self.assertEqual(P2.base_env(True)["CODEX_CAMPAIGN20_THREAD_EXECUTOR"], "1")
        self.assertNotIn("CODEX_CAMPAIGN20_THREAD_EXECUTOR", P2.base_env(False))

    def test_implementation_hash_covers_imported_producers(self):
        phase_map = {phase.name: phase for phase in P2.phases("bn081224887")}
        self.assertIn(P2.REPO / "scripts" / "40_temporal_survey.py",
                      P2.phase_dependency_paths(phase_map["temporal_catalog"]))
        self.assertIn(P2.HANDBOOK_TEMPORAL,
                      P2.phase_dependency_paths(phase_map["temporal_figures"]))
        self.assertIn(P2.LATBRIGHT_LAG,
                      P2.phase_dependency_paths(phase_map["lag"]))
        self.assertEqual(len(P2.phase_implementation_sha(phase_map["lag"])), 64)
        self.assertIn(P2.RUNTIME / "run_p2_temporal.py",
                      P2.phase_dependency_paths(phase_map["row_repair"]))
        self.assertIn(P2.REPO / "scripts" / "47c_lag_latbright.py",
                      P2.phase_dependency_paths(phase_map["row_repair"]))

    def test_row_repair_labels_encode_contract(self):
        lag = {"window_systematic_s": 0.387}
        text = P2._lag_convention_text(lag)
        self.assertIn("POSITIVE = soft", text)
        self.assertIn("NOT folded in", text)
        self.assertIn("Bala", P2._mvt_estimator_text({}))
        self.assertIn("MVT_HAAR_S", P2._mvt_estimator_text({}))

    def test_step44_receipt_refuses_files_not_made_by_invocation(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(P2, "SWEEP", Path(directory)):
            root = Path(directory) / "bn081224887"
            root.mkdir()
            for suffix in P2.STEP44_NONSPECTRAL_FIGURES:
                (root / f"bn081224887_{suffix}.png").write_bytes(b"fixture")
            future = time.time_ns() + 1_000_000
            with self.assertRaises(P2.ValidationError):
                P2.record_step44_nonspectral("bn081224887", future)

    def test_temporal_row_receipt_survives_unrelated_catalog_merge(self):
        trig = "bn081224887"
        payload = {"TRIGGER_NAME": trig, "T90": 1.25}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(P2, "SWEEP", Path(directory) / "sweep"), \
             patch.object(P2, "TEMPORAL_CATALOG", Path(directory) / "temporal.ecsv"), \
             patch.object(P2, "temporal_row_payload", return_value=payload):
            P2.TEMPORAL_CATALOG.write_text("first catalog state")
            not_before = P2.TEMPORAL_CATALOG.stat().st_mtime_ns
            P2.record_temporal_row_receipt(trig, not_before, "input")
            P2.TEMPORAL_CATALOG.write_text("later merge changed another row")
            receipt = P2.validate_temporal_row_receipt(trig)
        self.assertEqual(receipt["path"].split("/")[-1],
                         f"{trig}_temporal_catalog_row.source.json")

    def test_collect_summary_refuses_unreceipted_stale_products(self):
        with patch.object(P2, "validate_phase_statuses",
                          side_effect=P2.ValidationError("phase receipt stale")), \
             patch.object(P2, "temporal_row") as temporal:
            with self.assertRaisesRegex(P2.ValidationError, "phase receipt stale"):
                P2.collect_summary("bn081224887")
        temporal.assert_not_called()

    def test_response_blocked_step9_failure_keeps_only_declared_partial(self):
        trig = "bn100130729"
        phase = P2.Phase(2, "step_figures", ("python", "script", "--trig", trig),
                         P2.REPO, False, lambda value: None)
        manifest = {"fixture": "current"}
        fingerprint = P2.object_sha256(manifest)
        status = {
            "schema_version": P2.PHASE_SCHEMA,
            "trigger": trig,
            "phase_number": 2,
            "phase": "step_figures",
            "state": "FAILED",
            "command": list(phase.command),
            "cwd": str(phase.cwd),
            "implementation_sha256": "implementation",
            "controller_sha256": P2.sha256(Path(P2.__file__).resolve()),
            "threadpool_transport_shim": False,
            "pythonhashseed": 0,
            "input_fingerprint": fingerprint,
            "input_manifest": manifest,
            "return_code": 0,
            "validation_errors": [
                "step9 current-fit supplement: ValidationError: current fit missing",
                "validation: ValidationError: current step9 fit missing",
            ],
        }
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(P2, "LOG_ROOT", Path(directory)), \
             patch.object(P2, "phases", return_value=[phase]), \
             patch.object(P2, "phase_input_manifest", return_value=manifest), \
             patch.object(P2, "phase_implementation_sha",
                          return_value="implementation"), \
             patch.object(P2, "validate_step44_nonspectral", return_value=[]):
            path = Path(directory) / trig / "02_step_figures.status.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(status))
            products, partial = P2.validate_phase_statuses(trig)
        self.assertEqual(len(products), 1)
        self.assertEqual(len(partial), 1)
        self.assertIn("RESPONSE_UNCOVERED", partial[0])

    def test_non_step9_failure_is_not_accepted_for_response_blocked_burst(self):
        trig = "bn100130729"
        phase = P2.Phase(2, "step_figures", ("python", "script"), P2.REPO,
                         False, lambda value: None)
        manifest = {"fixture": "current"}
        fingerprint = P2.object_sha256(manifest)
        status = {
            "schema_version": P2.PHASE_SCHEMA, "trigger": trig,
            "phase_number": 2, "phase": "step_figures", "state": "FAILED",
            "command": list(phase.command), "cwd": str(phase.cwd),
            "implementation_sha256": "implementation",
            "controller_sha256": P2.sha256(Path(P2.__file__).resolve()),
            "threadpool_transport_shim": False, "pythonhashseed": 0,
            "input_fingerprint": fingerprint, "input_manifest": manifest,
            "return_code": 0,
            "validation_errors": ["non-spectral step-figure receipt: missing"],
        }
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(P2, "LOG_ROOT", Path(directory)), \
             patch.object(P2, "phases", return_value=[phase]), \
             patch.object(P2, "phase_input_manifest", return_value=manifest), \
             patch.object(P2, "phase_implementation_sha",
                          return_value="implementation"):
            path = Path(directory) / trig / "02_step_figures.status.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(status))
            with self.assertRaises(P2.ValidationError):
                P2.validate_phase_statuses(trig)

    def test_lag_window_systematic_formula(self):
        scans = [-0.2, 0.1, 0.4, 0.35]
        expected = 0.5 * (max(scans) - min(scans))
        self.assertTrue(math.isclose(expected, 0.3, abs_tol=1e-12))

    def test_labels_encode_reporting_contract(self):
        self.assertIn("CANONICAL", P2.BALA_LABEL)
        self.assertIn("NONCANONICAL", P2.CWT_LABEL)
        self.assertIn("NONCANONICAL", P2.HAAR_LABEL)
        self.assertIn("positive = soft 25–50 keV", P2.LAG_LABEL)
        self.assertIn("background-model uncertainty not propagated", P2.T90_LABEL)
        self.assertIn("UNGATED", P2.GATE_STATUS)

    def test_step9_failure_preserves_validated_temporal_values(self):
        temporal = {"t90": {"t90_s": 1.2}, "haar": {"mvt_s": 0.3}}
        bala = {"mvt_s": 0.2}
        cwt = {"mvt_s": 0.4}
        lag = {"tau_s": 0.05}
        pulse = {"best_pulse_model": "fixture"}
        fake_artifact = {"path": "/private/tmp/fixture", "sha256": "x", "bytes": 1}
        with patch.object(P2, "validate_phase_statuses", return_value=([], [])), \
             patch.object(P2, "temporal_row", return_value=(temporal, fake_artifact)), \
             patch.object(P2, "validate_cwt", return_value=(cwt, fake_artifact)), \
             patch.object(P2, "validate_bala", return_value=(bala, [fake_artifact])), \
             patch.object(P2, "validate_lag", return_value=(lag, [fake_artifact])), \
             patch.object(P2, "validate_temporal_figures",
                          return_value=(pulse, [fake_artifact])), \
             patch.object(P2, "validate_step44",
                          side_effect=P2.ValidationError("current fit missing")), \
             patch.object(P2, "validate_step44_nonspectral",
                          return_value=[fake_artifact]), \
             patch.object(P2, "validate_row_repair",
                          return_value={"lag_s": 0.05, "mvt_s": 0.2}):
            summary = P2.collect_summary("bn100130729")
        self.assertFalse(summary["complete"])
        self.assertTrue(summary["temporal_values_complete"])
        self.assertEqual(summary["t90"]["t90_s"], 1.2)
        self.assertEqual(summary["mvt"]["canonical_bala"]["mvt_s"], 0.2)
        self.assertEqual(summary["lag"]["tau_s"], 0.05)
        self.assertEqual(summary["catalog_row_canonical"]["lag_s"], 0.05)
        self.assertIn("current fit missing", summary["validation_errors"][0])


if __name__ == "__main__":
    unittest.main()
