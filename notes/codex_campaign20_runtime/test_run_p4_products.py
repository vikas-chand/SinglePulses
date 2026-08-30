#!/usr/bin/env python3
"""Product-free unit tests for the campaign P4 controller."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from astropy.table import Table


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("campaign_p4", HERE / "run_p4_products.py")
assert SPEC and SPEC.loader
P4 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = P4
SPEC.loader.exec_module(P4)


class P4ControllerTests(unittest.TestCase):
    def test_requested_triggers_are_restored_to_queue_order(self):
        self.assertEqual(
            P4.selected_triggers(["bn110928180", "bn081224887", "bn100130729"]),
            ["bn081224887", "bn100130729", "bn110928180"],
        )

    def test_four_prescribed_phases(self):
        specs = P4.commands("bn081224887")
        self.assertEqual([item["name"] for item in specs], [
            "montage_41e", "montage_audit_fallback",
            "parameter_evolution", "all_model_tables",
        ])
        self.assertIn("41e_sed_montage.py", specs[0]["command"][1])
        self.assertIn("repair_sed_montage.py", specs[1]["command"][1])
        self.assertIn("41d_param_evolution.py", specs[2]["command"][1])
        self.assertIn("p4_table_adapter.py", specs[3]["command"][1])

    def test_41d_arguments_are_exact(self):
        command = P4.commands("bn081224887")[2]["command"]
        self.assertEqual(command[-4:], [
            "--fit-root", "results/convention_check",
            "--out", "results/convention_check/param_evolution",
        ])

    def test_environment_is_deterministic_without_pool_shim(self):
        env = P4.base_env()
        self.assertEqual(env["PYTHONHASHSEED"], "0")
        self.assertEqual(env["MPLBACKEND"], "Agg")
        self.assertNotIn("CODEX_CAMPAIGN20_THREAD_EXECUTOR", env)

    def test_gate_and_known_partial_are_explicit(self):
        self.assertIn("UNGATED", P4.GATE_STATUS)
        self.assertIn("RESPONSE_UNCOVERED", P4.RESPONSE_BLOCKED["bn100130729"])

    def test_all_command_paths_are_absolute(self):
        for item in P4.commands("bn081224887"):
            self.assertTrue(os.path.isabs(item["command"][0]))
            self.assertTrue(os.path.isabs(item["command"][1]))

    def test_tables_command_passes_absolute_fit_root(self):
        command = P4.commands("bn081224887")[3]["command"]
        self.assertEqual(command[-2:], ["--fit-root", str(P4.FIT_ROOT)])
        self.assertTrue(Path(command[-1]).is_absolute())

    def test_duplicate_current_valid_sidecars_fail_p3_preflight(self):
        trig = "bn081224887"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fit_root = root / "fit"
            fit_dir = fit_root / trig
            grid = fit_root / f"sed_grid_{trig}"
            fit_dir.mkdir(parents=True)
            grid.mkdir(parents=True)
            fit = fit_dir / "spectral_fits.ecsv"
            metadata = fit_dir / "spectral_fits.json"
            blocks = root / "blocks.ecsv"
            for path, text in ((fit, "fit"), (metadata, "meta"), (blocks, "blocks")):
                path.write_text(text)
            sidecars = [grid / "first.json", grid / "second.json"]
            for index, sidecar in enumerate(sidecars):
                sidecar.write_text(f"side{index}")
                sidecar.with_suffix(".png").write_bytes(b"png")
                sidecar.with_suffix(".pdf").write_bytes(b"pdf")
            contract = SimpleNamespace(
                trig=trig,
                fit_path=fit,
                metadata_path=metadata,
                blocks_path=blocks,
                fit_sha256=P4.sha256(fit),
                metadata_sha256=P4.sha256(metadata),
                blocks_sha256=P4.sha256(blocks),
                models=("BAND",),
                bins=("tint",),
                pairs=(("tint", "BAND"),),
                plugin_dets_for_bin={"tint": ("n0",)},
            )
            result = SimpleNamespace(ok=True, fit_mode="live")
            fake_p3 = SimpleNamespace(
                CURRENT_41C_SHA256="sed-sha", AIC_TOL=0.1,
                SED_ENGINE=root / "41c.py",
                normalize_bin=lambda value: str(value),
                canon=lambda value: str(value),
                display_coverage_mismatch=lambda contract, bin_arg: None,
                scan_grid=lambda contract, grid: {("tint", "BAND"): result},
                _candidate_sidecars=lambda grid, contract: {
                    ("tint", "BAND"): sidecars},
                validate_sidecar=lambda path, contract, pair: result,
            )
            summary = {
                "trigger": trig,
                "canonical_fit_table": str(fit),
                "canonical_fit_sha256": contract.fit_sha256,
                "canonical_fit_metadata": str(metadata),
                "canonical_fit_metadata_sha256": contract.metadata_sha256,
                "adopted_blocks": str(blocks),
                "adopted_blocks_sha256": contract.blocks_sha256,
                "sed_engine": str(root / "41c.py"),
                "sed_engine_sha256": "sed-sha",
                "grid": str(grid),
                "models": ["BAND"], "bins": ["tint"], "pairs": 1,
                "ok": 1, "fail": 0, "pool_size": 16, "retry_limit": 1,
                "aic_tolerance": 0.1,
                "attempt_snapshot": None,
                "bands_are_never_silently_dropped": True,
                "persistent_failure_attempt_evidence_complete": True,
                "persistent_failure_attempt_evidence_gaps": [],
                "plugin_dets_by_bin": {"tint": ["n0"]},
                "known_structural_display_mismatches": {},
                "valid_triplets": [{
                    "bin": "tint", "model": "BAND",
                    "sidecar": str(sidecars[0]), "fit_mode": "live",
                    "sidecar_sha256": P4.sha256(sidecars[0]),
                    "png_sha256": P4.sha256(sidecars[0].with_suffix(".png")),
                    "pdf_sha256": P4.sha256(sidecars[0].with_suffix(".pdf")),
                }],
                "failed_pairs": [],
                "visual_verdict": "UNGATED — pending",
            }
            (grid / "sweep_summary.json").write_text(json.dumps(summary))
            (grid / "sweep_status.txt").write_text("OK BAND tint\n")
            with (mock.patch.object(P4, "FIT_ROOT", fit_root),
                  mock.patch.object(P4, "load_contract", return_value=contract),
                  mock.patch.object(P4, "runtime_modules",
                                    return_value=(fake_p3, SimpleNamespace()))):
                with self.assertRaisesRegex(P4.ValidationError, "glob selection.*ambiguous"):
                    P4.validate_p3_closure(trig)

    def test_parameter_evolution_rejects_stale_extra_glob(self):
        trig = "bn081224887"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for name in ("fit", "meta", "blocks", "closure"):
                (root / name).write_text(name)
            table = Table({"BLOCK": [-1], "BAND_AIC": [1.0]})
            contract = SimpleNamespace(
                table=table, models=("BAND",),
                fit_path=root / "fit", metadata_path=root / "meta",
                blocks_path=root / "blocks",
            )
            for suffix in (".png", ".pdf", ".json"):
                (root / f"{trig}_paramevo_BAND{suffix}").write_text("x")
            (root / f"{trig}_paramevo_CPL.png").write_text("stale")
            closure = {
                "contract": contract,
                "summary_artifact": {"path": str(root / "closure")},
            }
            with mock.patch.object(P4, "PARAM_ROOT", root):
                with self.assertRaisesRegex(P4.ValidationError, "file set is stale"):
                    P4.validate_parameter_evolution(trig, closure)

    def test_montage_repair_rejects_stale_p3_hash(self):
        p3, repair = P4.runtime_modules()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fit, metadata, blocks = root / "fit", root / "meta", root / "blocks"
            for path in (fit, metadata, blocks):
                path.write_text(path.name)
            contract = SimpleNamespace(
                trig="bn081224887", fit_sha256=P4.sha256(fit),
                metadata_sha256=P4.sha256(metadata),
                blocks_sha256=P4.sha256(blocks),
                models=("BAND",), bins=("tint",),
                pairs=(("tint", "BAND"),),
            )
            payload = {
                "trigger": contract.trig,
                "canonical_fit_sha256": "wrong",
                "canonical_fit_metadata_sha256": contract.metadata_sha256,
                "adopted_blocks_sha256": contract.blocks_sha256,
                "models": ["BAND"], "bins": ["tint"], "pairs": 1,
                "attempt_snapshot": None,
                "persistent_failure_attempt_evidence_complete": True,
                "persistent_failure_attempt_evidence_gaps": [],
            }
            (root / "sweep_summary.json").write_text(json.dumps(payload))
            (root / "sweep_status.txt").write_text("FAIL BAND tint structural\n")
            with self.assertRaisesRegex(RuntimeError, "stale or incomplete"):
                repair._load_closure(contract, root)

    def test_broadband_structural_failures_become_24_placeholders(self):
        p3, repair = P4.runtime_modules()
        products = P4.products_module()
        models = list(products.HIGHE_PREFIXES)
        columns = {}
        for index, model in enumerate(models):
            columns[f"{model}_AIC"] = [float(index)]
            columns[f"{model}_STATUS"] = ["OK"]
            columns[f"{model}_VALID"] = [True]
        table = Table(columns)
        contract = SimpleNamespace(
            models=tuple(models), table=table,
            row_for_bin={"tint": table[0]},
        )
        validations = {
            ("tint", model): p3.Validation(
                False, "STRUCTURAL_COVERAGE_MISMATCH: LLE/LAT not dropped")
            for model in models
        }
        with mock.patch.object(
                repair, "failure_class",
                return_value="STRUCTURAL_DISPLAY_MISMATCH"):
            expected = repair._expected_state(contract, "tint", validations)
        self.assertEqual(expected["n_missing"], 24)
        self.assertEqual(expected["n_placeholders"], 24)
        self.assertEqual(len(expected["cells"]), 24)
        self.assertTrue(all(
            cell["rendering"] == "placeholder"
            and cell["failure_class"] == "STRUCTURAL_DISPLAY_MISMATCH"
            for cell in expected["cells"]
        ))

    def test_live_burst2_table_format_is_byte_exact(self):
        """The saved burst-2 products are the brief's formatting authority."""
        adapter = P4.table_adapter_module()
        products = adapter.base
        trig = "bn081222204"
        source_fit = P4.REPO / "results" / "convention_check" / trig
        authority_tables = (
            P4.REPO / "results" / "convention_check" /
            f"sed_grid_{trig}" / "tables"
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fit_root = root / "results" / "convention_check"
            target_fit = fit_root / trig
            target_fit.mkdir(parents=True)
            shutil.copy2(source_fit / "spectral_fits.ecsv", target_fit)
            shutil.copy2(source_fit / "spectral_fits.json", target_fit)
            with mock.patch.object(products, "REPO", root.resolve()):
                adapter.build(trig, fit_root=fit_root)
            generated = fit_root / f"sed_grid_{trig}" / "tables"
            authority_names = sorted(
                path.name for path in authority_tables.glob("*_params.md"))
            self.assertTrue(authority_names)
            for name in authority_names:
                self.assertEqual(
                    (generated / name).read_bytes(),
                    (authority_tables / name).read_bytes(),
                    name,
                )


if __name__ == "__main__":
    unittest.main()
