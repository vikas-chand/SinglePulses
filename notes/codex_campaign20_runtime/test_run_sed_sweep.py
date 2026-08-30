#!/usr/bin/env python3
"""Producer-side contract tests for the campaign P3 shell sweep.

These tests use temporary files only.  They never invoke scripts/41c or touch a
campaign product directory.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from astropy.table import Table
from PIL import Image


RUNTIME = Path(__file__).resolve().parent
REPO = RUNTIME.parents[1]
sys.path.insert(0, str(RUNTIME))

import repair_sed_montage as repair  # noqa: E402
import run_sed_sweep as sweep  # noqa: E402


class SedSweepContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p3_contract_test_")
        self.root = Path(self.temp.name)
        self.trig = "bnTEST000"
        fit_dir = self.root / "fits" / self.trig
        fit_dir.mkdir(parents=True)
        names = ["BLOCK", "T_START", "T_STOP", "N_DETS", "PLUGIN_DETS"]
        rows = [
            [-1, 0.0, 1.0, 2, "n0,b0"],
            [0, 0.0, 1.0, 2, "n0,b0"],
        ]
        table = Table(rows=rows, names=names)
        for index, model in enumerate(sweep.ENGINE_PREFIXES):
            table[f"{model}_STATUS"] = ["OK", "OK"]
            table[f"{model}_AIC"] = [120.0 + index, 120.0 + index]
        self.fit_path = fit_dir / "spectral_fits.ecsv"
        table.write(self.fit_path, format="ascii.ecsv")
        self.blocks_path = self.root / "blocks.ecsv"
        self.meta_path = fit_dir / "spectral_fits.json"
        metadata = {
            "trigger": self.trig,
            "reference_det": "n0",
            "canonical_det": "n0",
            "fit_dets": ["n0", "b0"],
            "blocks_file": str(self.blocks_path),
            "n_blocks": 1,
            "bin_starts": [0.0],
            "bin_stops": [1.0],
            "RANGES_CONVENTION": "Chand2020_ApJ903_9",
        }
        self.meta_path.write_text(json.dumps(metadata))
        Table(rows=[[self.trig, "n0", 0, 0.0, 1.0]],
              names=["TRIGGER_NAME", "DETECTOR", "BLOCK_INDEX",
                     "T_START", "T_STOP"]).write(
                         self.blocks_path, format="ascii.ecsv")
        rows_by_bin = {"tint": table[0], "0": table[1]}
        self.contract = sweep.Contract(
            trig=self.trig,
            fit_path=self.fit_path,
            metadata_path=self.meta_path,
            blocks_path=self.blocks_path,
            table=table,
            metadata=metadata,
            models=tuple(sweep.ENGINE_PREFIXES),
            bins=("tint", "0"),
            row_for_bin=rows_by_bin,
            plugin_dets_for_bin={"tint": ("n0", "b0"), "0": ("n0", "b0")},
            fit_sha256=sweep.sha256(self.fit_path),
            metadata_sha256=sweep.sha256(self.meta_path),
            blocks_sha256=sweep.sha256(self.blocks_path),
        )
        self.grid = self.root / "grid"
        self.grid.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def make_triplet(self, *, script_hash=None, detectors=None,
                     bin_arg="0", model="BAND") -> Path:
        display = next(name for name, prefix in sweep.ENGINE_REGISTRY
                       if prefix == model).replace("+", "")
        stem = self.grid / f"{self.trig}_SED_{sweep.tag_for(bin_arg)}_{display}"
        Image.new("RGB", (12, 8), "white").save(stem.with_suffix(".png"))
        stem.with_suffix(".pdf").write_bytes(b"%PDF-1.4\n1 0 obj\nendobj\n%%EOF\n")
        chosen = tuple(detectors or self.contract.plugin_dets_for_bin[bin_arg])
        payload = {
            "script": "41c_paper_sed.py",
            "script_sha256": script_hash or sweep.CURRENT_41C_SHA256,
            "argv": [
                "--trig", self.trig, "--bin", bin_arg, "--model", model,
                "--out", str(self.grid), "--fit-root",
                str(self.contract.fit_path.parent.parent),
            ],
            "trig": self.trig,
            "bin": bin_arg,
            "model": next(name for name, prefix in sweep.ENGINE_REGISTRY
                          if prefix == model),
            "detectors": list(chosen),
            "reference": "n0",
            "interval_s": [0.0, 1.0],
            "groups": {det: {"groups": 1, "plotted": 1, "eac": 1.0}
                       for det in chosen},
            "fit_mode": "live",
            "aic_live": 120.0,
            "aic_stored": 120.0,
            "n2ll_live": 110.0,
            "pgstat": 110.0,
            "dof": 95,
            "n_active_channels": 100,
            "band": "drawn",
            "rebin": [5, 5],
            "ul_arrows": False,
            "rng_seed": 20260814,
            "ranges_convention": "Chand2020_ApJ903_9",
        }
        path = stem.with_suffix(".json")
        path.write_text(json.dumps(payload))
        return path

    def test_engine_registry_is_exact_current_24(self):
        self.assertEqual(len(sweep.ENGINE_PREFIXES), 24)
        self.assertEqual(len(set(sweep.ENGINE_PREFIXES)), 24)
        self.assertEqual(sweep.canon("DSBPLfree"), "DSBPLF")
        self.assertEqual(sweep.canon("BandxCut"), "BANDCUT")

    def test_load_contract_crosschecks_current_table_metadata_and_blocks(self):
        loaded = sweep.load_contract(
            self.trig, self.fit_path, self.blocks_path)
        self.assertEqual(loaded.models, tuple(sweep.ENGINE_PREFIXES))
        self.assertEqual(loaded.bins, ("tint", "0"))
        self.assertEqual(loaded.plugin_dets_for_bin["0"], ("n0", "b0"))

    def test_current_triplet_passes_full_machine_contract(self):
        path = self.make_triplet()
        result = sweep.validate_sidecar(path, self.contract, ("0", "BAND"))
        self.assertTrue(result.ok, result.reason)
        self.assertEqual(result.fit_mode, "live")
        self.assertEqual(len(result.png_sha256), 64)

    def test_stale_41c_hash_is_rejected(self):
        path = self.make_triplet(script_hash="0" * 64)
        result = sweep.validate_sidecar(path, self.contract, ("0", "BAND"))
        self.assertFalse(result.ok)
        self.assertIn("hash is stale", result.reason)

    def test_triplet_older_than_fit_authority_is_rejected(self):
        path = self.make_triplet()
        future = time.time() + 2.0
        os.utime(self.fit_path, (future, future))
        result = sweep.validate_sidecar(path, self.contract, ("0", "BAND"))
        self.assertFalse(result.ok)
        self.assertIn("predates", result.reason)

    def test_every_band_mismatch_is_refused_not_accepted_by_aic(self):
        broad = replace(
            self.contract,
            metadata={**self.contract.metadata, "fit_dets": ["n0", "b0", "lle"]},
            plugin_dets_for_bin={"tint": ("n0", "b0", "lle"),
                                 "0": ("n0", "b0", "lle")},
        )
        path = self.make_triplet(detectors=("n0", "b0"))
        result = sweep.validate_sidecar(path, broad, ("0", "BAND"))
        self.assertFalse(result.ok)
        self.assertIn("STRUCTURAL_COVERAGE_MISMATCH", result.reason)
        self.assertIn("bands are not dropped", result.reason)

    def test_quarantine_is_recoverable_and_hash_recorded(self):
        path = self.make_triplet(script_hash="0" * 64)
        old_hash = sweep.sha256(path)
        moved = sweep.quarantine_invalid_panels(
            self.contract, self.grid, "unit_test")
        self.assertEqual(len(moved), 1)
        self.assertFalse(path.exists())
        json_targets = [item for item in moved[0]["files"]
                        if str(item["path"]).endswith(".json")]
        self.assertEqual(json_targets[0]["sha256"], old_hash)
        self.assertTrue(Path(json_targets[0]["path"]).is_file())

    def test_native_montage_with_missing_pair_requires_classified_fallback(self):
        montage = self.grid / "montage"
        montage.mkdir()
        png = montage / f"{self.trig}_montage_bin0.png"
        sidecar = png.with_suffix(".json")
        Image.new("RGB", (12, 8), "white").save(png)
        row = self.contract.row_for_bin["0"]
        aics = {model: float(row[f"{model}_AIC"])
                for model in self.contract.models}
        order = sorted(aics, key=aics.get)
        sidecar.write_text(json.dumps({
            "script": "41e_sed_montage.py",
            "script_sha256": repair._sha256(REPO / "scripts" / "41e_sed_montage.py"),
            "tag": "bin0",
            "interval_s": [0.0, 1.0],
            "winner": order[0],
            "order": order,
            "daic": {model: aics[model] - aics[order[0]] for model in order},
            "n_panels": 24,
            "n_missing": 1,
            "compositing_only": True,
        }))
        (self.grid / "sweep_summary.json").write_text("{}")
        expected = {
            "order": order,
            "n_missing": 1,
            "n_fit_failures": 0,
        }
        ok, reasons = repair._audit_existing(
            png, sidecar, expected, "bin0", self.contract, "0", self.grid)
        self.assertFalse(ok)
        self.assertTrue(any("classified refusal" in reason for reason in reasons))

    def test_shell_pool_is_exactly_16_and_syntax_valid(self):
        wrapper = RUNTIME / "run_sed_sweep.zsh"
        text = wrapper.read_text()
        self.assertIn("POOL_SIZE=16", text)
        self.assertIn("slot<=POOL_SIZE", text)
        self.assertNotIn("for _ in {1..$POOL_SIZE}", text)
        self.assertLess(text.index("--mode campaign-plan"),
                        text.index("while IFS=$'\\t' read"))
        proc = subprocess.run(["zsh", "-n", str(wrapper)], capture_output=True,
                              text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        probe = subprocess.run(
            ["zsh", "-fc",
             "POOL_SIZE=16; n=0; for ((slot=1;slot<=POOL_SIZE;slot++)); "
             "do ((n++)); done; print -r -- $n"],
            capture_output=True, text=True)
        self.assertEqual(probe.stdout.strip(), "16")

    def test_final_status_has_one_line_per_pair_and_retry_evidence_is_exact(self):
        results = {pair: sweep.Validation(False, "STRUCTURAL mismatch")
                   for pair in self.contract.pairs}
        status = self.grid / "sweep_status.txt"
        sweep.write_status(status, self.contract, results)
        lines = status.read_text().splitlines()
        self.assertEqual(len(lines), 48)
        self.assertTrue(all(line.startswith("FAIL ") for line in lines))
        pair = ("0", "BAND")
        one = {candidate: sweep.Validation(True, "ok")
               for candidate in self.contract.pairs}
        one[pair] = sweep.Validation(False, "STRUCTURAL mismatch")
        self.assertEqual(len(sweep.two_attempt_gaps(self.contract, self.grid, one)), 1)
        for attempt in (1, 2):
            log = self.grid / "logs" / f"bin0_BAND_attempt{attempt}.log"
            state = self.grid / "logs" / "status" / f"bin0_BAND_attempt{attempt}.status"
            log.parent.mkdir(parents=True, exist_ok=True)
            state.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("ENGINE_EXIT_CODE: 1\n")
            state.write_text(f"FAIL\\tBAND\\t0\\tattempt={attempt}\n")
        self.assertEqual(sweep.two_attempt_gaps(self.contract, self.grid, one), [])

    def test_existing_41c_schema_has_required_provenance_keys(self):
        source = (REPO / "scripts" / "41c_paper_sed.py").read_text()
        for token in ("script_sha256", "argv=sys.argv[1:]", "fit_mode=fit_mode",
                      "aic_live=aic", "aic_stored=stored_aic", "rng_seed=20260814"):
            self.assertIn(token, source)

    def test_live_completed_example_has_exact_canonical_model_schema(self):
        path = REPO / "results" / "convention_check" / "bn081222204" / "spectral_fits.ecsv"
        self.assertTrue(path.is_file())
        table = Table.read(path, format="ascii.ecsv")
        models = {name[:-4] for name in table.colnames if name.endswith("_AIC")}
        self.assertEqual(models, set(sweep.ENGINE_PREFIXES))
        self.assertIn(-1, [int(value) for value in table["BLOCK"]])
        self.assertTrue(all(str(value).strip() for value in table["PLUGIN_DETS"]))


if __name__ == "__main__":
    unittest.main()
