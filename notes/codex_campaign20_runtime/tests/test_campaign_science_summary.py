from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from astropy.table import Table


RUNTIME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME))

import campaign_science_summary as css  # noqa: E402


class CampaignScienceSummaryFixtureTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="campaign_science_summary_")
        self.root = Path(self.temp.name)
        self.trig = "bn081224887"
        self._write_fixture()

    def tearDown(self):
        self.temp.cleanup()

    def _json(self, relative: str, payload: dict):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return path

    def _write_fixture(self):
        fit_dir = self.root / "results" / "convention_check" / self.trig
        fit_dir.mkdir(parents=True)
        fit = Table({
            "BLOCK": [-1, 0, 1],
            "T_START": [0.0, 0.0, 1.0],
            "T_STOP": [2.0, 1.0, 2.0],
            "T_MID": [1.0, 0.5, 1.5],
            "N_DETS": [4, 4, 5],
            "PLUGIN_DETS": ["n6,n7,b1,lle", "n6,n7,b1,lle",
                            "n6,n7,b1,lle,LAT"],
            "EAC_DETS": ["n7,b1,lle"] * 3,
            "EAC_SKIPPED": [""] * 3,
            "BEST_AIC_MODEL": ["BAND", "BANDBB", "CPLBB"],
            "BAND_STATUS": ["OK", "OK", "OK"],
            "BAND_VALID": [True, True, True],
            "BAND_ALPHA": [-0.60, -0.50, -0.80],
            "BAND_ALPHA_ERR": [0.1, 0.1, 0.2],
            "BAND_ALPHA_NEG_ERR": [0.1, 0.1, 0.2],
            "BAND_ALPHA_POS_ERR": [0.1, 0.1, 0.2],
            "CPL_STATUS": ["OK", "OK", "OK"],
            "CPL_VALID": [True, True, True],
            "BANDBB_STATUS": ["OK", "OK", "OK"],
            "BANDBB_VALID": [True, True, False],
            "BANDBB_KT": [5.0, 4.0, 5.0],
            "BANDBB_KT_ERR": [0.5, 0.4, 0.5],
            "BANDBB_KT_NEG_ERR": [0.4, 0.3, 0.4],
            "BANDBB_KT_POS_ERR": [0.6, 0.5, 0.6],
            "CPLBB_STATUS": ["OK", "FAIL", "OK"],
            "CPLBB_VALID": [True, False, True],
            "CPLBB_KT": [6.0, float("nan"), 8.0],
            "CPLBB_KT_ERR": [0.5, float("nan"), 0.7],
            "CPLBB_KT_NEG_ERR": [0.4, float("nan"), 0.6],
            "CPLBB_KT_POS_ERR": [0.6, float("nan"), 0.8],
            "LRT_BANDBB_BAND": [1.0, 10.0, 12.0],
            "LRT_CPLBB_CPL": [1.0, float("nan"), 9.3],
        })
        # The campaign authority is exactly scripts/10's 24-model highe
        # registry.  Keep the hand-authored science columns above, then add
        # the common contract columns in canonical AIC-column order.
        for index, prefix in enumerate(css.HIGHE_PREFIXES):
            defaults = {
                "STATUS": ["OK"] * 3,
                "N2LL": [100.0 + index] * 3,
                "VALID": [True] * 3,
                "AIC": [110.0 + index] * 3,
                "BIC": [120.0 + index] * 3,
            }
            for suffix, values in defaults.items():
                name = f"{prefix}_{suffix}"
                if name not in fit.colnames:
                    fit[name] = values
        fit.write(fit_dir / "spectral_fits.ecsv", format="ascii.ecsv")
        self._json(
            f"results/convention_check/{self.trig}/spectral_fits.json",
            {
                "trigger": self.trig,
                "fit_dets": ["n6", "n7", "b1", "lle"],
                "LLE_RANGES": ["20000-100000"],
                "n_blocks": 2,
                "models": [css.MODEL_NAMES[prefix]
                           for prefix in css.HIGHE_PREFIXES],
                "bin_starts": [0.0, 1.0],
                "bin_stops": [1.0, 2.0],
            },
        )

        temporal = Table({
            "TRIGGER_NAME": [self.trig],
            "REF_DET": ["n6"],
            "T90": [1.8],
            "T90_ERR": [0.2],
            "T90_ERR_LO": [0.15],
            "T90_ERR_HI": [0.25],
            "T90_START": [0.1],
            "T90_STOP": [1.9],
            "T50": [0.8],
            "T90_WINDOW_TRUNCATED": [False],
            "TAIL_OUTSIDE_WINDOW_CTS": [42.0],
            "TAIL_OUTSIDE_WINDOW_SIG": [4.0],
            "MVT_S": [0.25],
            "MVT_ERR_S": [float("nan")],
            "MVT_TYPE": ["limit"],
        })
        temporal_path = self.root / "results" / "temporal_catalog_all106.ecsv"
        temporal_path.parent.mkdir(parents=True, exist_ok=True)
        temporal.write(temporal_path, format="ascii.ecsv")

        self._json(
            f"results/mvt_upstream/run_step7/{self.trig}/result.json",
            {
                "trigger": self.trig,
                "engine": "mvtfermi_upstream",
                "status": "detection",
                "mvt_s": 0.03,
                "mvt_err_s": 0.002,
                "delta_s": 2.0,
                "interval_start_s": 0.0,
                "interval_stop_s": 2.0,
                "significance": 5.5,
                "delta_curve": [{
                    "delta_s": 2.0,
                    "interval_start_s": 0.0,
                    "mvt_s": 0.03,
                    "mvt_err_s": 0.002,
                    "significance_z": 2.1,
                    "significance_weighted": 5.5,
                    "snr": 20.0,
                }],
            },
        )
        self._json(
            f"results/mvt_cwt/{self.trig}_mvt_cwt.json",
            {
                "trig": self.trig,
                "mvt_cwt_s": 0.12,
                "mvt_cwt_err_s": 0.01,
                "band_keV": [8.0, 900.0],
                "dt_s": 0.004,
                "dj": 0.25,
                "noise_percentile": 99.5,
            },
        )
        self._json(
            f"results/sweep106/{self.trig}/{self.trig}_step7_lag_latbright.json",
            {
                "trig": self.trig,
                "tau_s": 0.2,
                "sigma_l_s": 0.03,
                "sigma_r_s": 0.04,
                "peak_sig": 8.0,
                "soft_keV": [25.0, 50.0],
                "hard_keV": [100.0, 300.0],
                "convention": "POSITIVE = soft lags hard",
                "windows": {
                    "scan_halves_s": [0.5, 1.0],
                    "window_systematic_s": 0.05,
                },
            },
        )
        self._json(
            f"results/sweep106/{self.trig}/p2_temporal_summary.json",
            {
                "schema_version": css.P2_SCHEMA,
                "trigger": self.trig,
                "complete": True,
                "provisional": True,
                "t90": {
                    "estimator_label": (
                        "windowed count-space T90 inside the approved SRC interval"
                    ),
                    "t90_s": 1.8,
                    "t90_err_s": 0.2,
                    "t90_err_lo_s": 0.15,
                    "t90_err_hi_s": 0.25,
                    "t90_start_s": 0.1,
                    "t90_stop_s": 1.9,
                    "ref_detector": "n6",
                    "approved_src_window_s": [0.0, 2.0],
                    "lower_limit": True,
                    "lower_limit_reason": ">=3 sigma tail",
                    "t90_window_truncated": False,
                    "tail_outside_window_counts": 42.0,
                    "tail_outside_window_sigma": 4.0,
                    "tail_outside_window_interval_s": [2.0, 4.0],
                },
                "mvt": {
                    "canonical_bala": {
                        "estimator_label": "Bala windowed MVT — CANONICAL",
                        "mvt_s": 0.03,
                        "mvt_err_s": 0.002,
                        "delta_s": 2.0,
                        "interval_s": [0.0, 2.0],
                        "status": "detection",
                        "limit_relation": None,
                        "significance": 5.5,
                        "detectors": ["n6", "n7"],
                    },
                    "noncanonical_cwt": {
                        "estimator_label": "CWT global MVT — NONCANONICAL",
                        "mvt_s": 0.12,
                        "mvt_err_s": 0.01,
                        "band_keV": [8.0, 900.0],
                        "window_s": [0.0, 2.0],
                        "dt_s": 0.004,
                        "dj": 0.25,
                        "noise_percentile": 99.5,
                    },
                    "noncanonical_haar": {
                        "estimator_label": "Haar global MVT — NONCANONICAL",
                        "mvt_s": 0.25,
                        "mvt_err_s": None,
                        "type": "limit",
                        "upper_limit": True,
                    },
                },
                "lag": {
                    "estimator_label": "LATBright s02c DCCF lag",
                    "tau_s": 0.2,
                    "sigma_l_s": 0.03,
                    "sigma_r_s": 0.04,
                    "window_systematic_s": 0.05,
                    "peak_significance_sigma": 8.0,
                    "scan_half_widths_s": [0.5, 1.0],
                    "scan_taus_s": [0.15, 0.25],
                    "soft_band_keV": [25.0, 50.0],
                    "hard_band_keV": [100.0, 300.0],
                    "positive_means": "soft photons lag hard photons",
                },
            },
        )

        grid = self.root / "results" / "convention_check" / f"sed_grid_{self.trig}"
        self._json(
            f"results/convention_check/sed_grid_{self.trig}/sweep_summary.json",
            {"trigger": self.trig, "pairs": 72, "ok": 70, "fail": 2,
             "models": list(css.HIGHE_PREFIXES),
             "bins": ["tint", "0", "1"],
             "visual_verdict": "UNGATED"},
        )
        self._json(
            f"results/convention_check/sed_grid_{self.trig}/montage/fallback_montage_audit.json",
            {"trigger": self.trig, "repaired": 1, "preserved": 2},
        )
        for tag in ("TINT", "bin0", "bin1"):
            self._json(
                f"results/convention_check/sed_grid_{self.trig}/montage/"
                f"{self.trig}_montage_{tag}.json",
                {"tag": tag, "n_panels": 24,
                 "n_missing": 0 if tag == "bin1" else 1,
                 "order": [f"M{i}" for i in range(24)]},
            )
        self._json(
            f"results/convention_check/sed_grid_{self.trig}/tables/tables_manifest.json",
            {"trigger": self.trig, "n_spectra": 3, "n_models": 24},
        )
        self._json(
            f"results/convention_check/param_evolution/{self.trig}_paramevo_BAND.json",
            {"trig": self.trig, "model": "BAND"},
        )
        montage_root = (self.root / "results" / "convention_check" /
                        f"sed_grid_{self.trig}" / "montage")
        table_manifest = (self.root / "results" / "convention_check" /
                          f"sed_grid_{self.trig}" / "tables" /
                          "tables_manifest.json")
        self._json(
            f"results/convention_check/sed_grid_{self.trig}/p4_products_summary.json",
            {
                "schema_version": css.P4_SCHEMA,
                "trigger": self.trig,
                "state": "COMPLETE",
                "provisional": True,
                "montages": {
                    "n_tags": 3,
                    "fallback_audit": {
                        "path": str(montage_root / "fallback_montage_audit.json"),
                        "sha256": "fixture",
                    },
                    "tags": [{
                        "tag": tag,
                        "bin": "tint" if tag == "TINT" else tag[3:],
                        "n_panels": 24,
                        "n_missing": 0 if tag == "bin1" else 1,
                        "n_fit_failures": 0,
                        "fallback": tag == "TINT",
                        "sidecar": {
                            "path": str(montage_root /
                                        f"{self.trig}_montage_{tag}.json"),
                            "sha256": "fixture",
                        },
                    } for tag in ("TINT", "bin0", "bin1")],
                },
                "parameter_evolution": {
                    "n_models": 1,
                    "products": [{
                        "model": "BAND",
                        "winner_bins": [0],
                        "sidecar": {
                            "path": str(self.root / "results" /
                                        "convention_check" / "param_evolution" /
                                        f"{self.trig}_paramevo_BAND.json"),
                            "sha256": "fixture",
                        },
                    }],
                },
                "all_model_tables": {
                    "n_spectra": 3,
                    "n_models_per_spectrum": 24,
                    "manifest": {
                        "path": str(table_manifest),
                        "sha256": "fixture",
                    },
                },
            },
        )
        self.assertTrue(grid.is_dir())

    def test_scientific_fields_are_labeled_and_provisional(self):
        data = css.build_campaign(
            self.root, (self.trig, "bn090530760"))
        burst = data["bursts"][0]
        missing = data["bursts"][1]

        band = burst["spectral"]["band_alpha_resolved"]
        self.assertEqual(band["n_usable_band_fits"], 2)
        self.assertEqual(band["range"], {"min": -0.8, "max": -0.5})
        self.assertEqual(band["n_above_minus_two_thirds"], 1)
        self.assertEqual(band["n_at_or_below_minus_two_thirds"], 1)
        self.assertIn("Band-model fit", band["value_origin"])

        candidates = burst["spectral"]["thermal_candidates"]
        self.assertEqual(len(candidates), 2)
        bandbb = next(item for item in candidates
                      if item["composite_model"] == "BANDBB")
        cplbb = next(item for item in candidates
                     if item["composite_model"] == "CPLBB")
        self.assertAlmostEqual(bandbb["bb_peak_keV"], 3.9207 * 4.0)
        self.assertEqual(bandbb["bb_peak_vs_8keV"], "AT_OR_ABOVE_8_KEV")
        self.assertEqual(bandbb["l28_edge_class"], "EDGE_CONSTRAINED")
        self.assertFalse(bandbb["population_promotion_eligible"])
        self.assertEqual(cplbb["l28_edge_class"], "IN_BAND")
        self.assertTrue(cplbb["l28_edge_population_threshold_pass"])
        self.assertFalse(cplbb["population_promotion_eligible"])
        self.assertTrue(all(item["residual_evidence"]["state"] ==
                            css.RESIDUAL_STATE for item in candidates))

        temporal = burst["temporal"]
        self.assertTrue(temporal["t90_tail"]["lower_limit"])
        self.assertEqual(temporal["t90_tail"]["tail_significance_sigma"], 4.0)
        self.assertEqual(
            temporal["mvt"]["bala_windowed_canonical"]["mvt_s"], 0.03)
        self.assertEqual(
            temporal["mvt"]["bala_windowed_canonical"]["delta_s"], 2.0)
        self.assertIn(
            "CWT", temporal["mvt"]["cwt_global_crosscheck"]["estimator_label"])
        self.assertEqual(
            temporal["mvt"]["cwt_global_crosscheck"]["error_interpretation"],
            "HALF_CWT_SCALE_GRID_SPACING")
        self.assertEqual(
            temporal["mvt"]["bala_windowed_canonical"]
            ["significance_semantics"],
            "ENGINE_SELECTION_WEIGHTED_MEAN_STATISTIC_NOT_GAUSSIAN_Z")
        self.assertEqual(
            temporal["mvt"]["bala_windowed_canonical"]
            ["selected_delta_significance_z"], 2.1)
        self.assertTrue(
            temporal["mvt"]["haar_in_chain_crosscheck"]["upper_limit"])
        self.assertEqual(temporal["lag"]["window_systematic_s"], 0.05)

        broadband = burst["broadband"]
        self.assertEqual(broadband["fit_dets"], ["n6", "n7", "b1", "lle"])
        self.assertEqual(broadband["lle_ranges_keV"], ["20000-100000"])
        self.assertEqual(broadband["lat_plugin_blocks"], [1])
        self.assertFalse(broadband["matched_gbm_only_counterfactual_present"])
        self.assertEqual(
            broadband["extra_band_effect_state"],
            "NOT_IDENTIFIABLE_WITHOUT_MATCHED_GBM_ONLY_REFIT")

        self.assertTrue(burst["product_presence"]["p3_sweep_summary_json"])
        self.assertEqual(burst["product_presence"]["p4_montage_summary_count"], 3)
        self.assertEqual(missing["availability_status"], "CANONICAL_FIT_MISSING")
        self.assertTrue(data["provisional"])

    def test_json_and_markdown_are_serializable_without_nan(self):
        data = css.build_campaign(self.root, (self.trig,))
        encoded = json.dumps(data, allow_nan=False)
        markdown = css.render_markdown(data)
        out_json = self.root / "appendix" / "campaign.json"
        out_markdown = self.root / "appendix" / "campaign.md"
        css._atomic_write(out_json, encoded + "\n")
        css._atomic_write(out_markdown, markdown)
        self.assertIn("BAND_ALPHA", markdown)
        self.assertIn("UNGATED_NOT_ADJUDICATED", markdown)
        self.assertIn("NOT_IDENTIFIABLE_WITHOUT_MATCHED_GBM_ONLY_REFIT", markdown)
        self.assertIn(self.trig, encoded)
        self.assertEqual(json.loads(out_json.read_text())["schema"],
                         "campaign_science_summary.v2")
        self.assertEqual(out_markdown.read_text(), markdown)

    def test_valid_temporal_values_survive_incomplete_non_temporal_p2_state(self):
        path = (self.root / "results" / "sweep106" / self.trig /
                "p2_temporal_summary.json")
        value = json.loads(path.read_text())
        value["complete"] = False
        value["temporal_values_complete"] = True
        value["validation_errors"] = [
            "step/QC figures: current-fit Step-9 unavailable"
        ]
        path.write_text(json.dumps(value, indent=2) + "\n")

        data = css.build_campaign(self.root, (self.trig,))
        burst = data["bursts"][0]
        p2 = burst["product_presence"]["p2_temporal_summary"]
        self.assertTrue(p2["valid"])
        self.assertFalse(p2["complete"])
        self.assertTrue(p2["temporal_values_complete"])
        self.assertEqual(burst["temporal"]["t90_tail"]["t90_s"], 1.8)
        self.assertEqual(
            burst["temporal"]["mvt"]["bala_windowed_canonical"]["mvt_s"],
            0.03)
        self.assertTrue(any("P2 product is incomplete" in message
                            for message in burst["input_errors"]))

    def test_partial_model_table_is_not_exposed_as_canonical_science(self):
        fit_path = (self.root / "results" / "convention_check" / self.trig /
                    "spectral_fits.ecsv")
        fit = Table.read(fit_path, format="ascii.ecsv")
        for column in [name for name in fit.colnames
                       if name.startswith("SBPLBBCPL_")]:
            fit.remove_column(column)
        fit.write(fit_path, format="ascii.ecsv", overwrite=True)

        data = css.build_campaign(self.root, (self.trig,))
        burst = data["bursts"][0]
        self.assertEqual(burst["availability_status"],
                         "CANONICAL_SCHEMA_INVALID")
        self.assertFalse(burst["spectral"]["canonical_schema"]["valid"])
        self.assertEqual(
            burst["spectral"]["band_alpha_resolved"]["n_usable_band_fits"], 0)
        self.assertEqual(burst["spectral"]["thermal_candidates"], [])

    def test_raw_temporal_files_are_not_a_fallback_without_p2_authority(self):
        path = (self.root / "results" / "sweep106" / self.trig /
                "p2_temporal_summary.json")
        path.unlink()
        data = css.build_campaign(self.root, (self.trig,))
        temporal = data["bursts"][0]["temporal"]
        self.assertFalse(temporal["t90_tail"]["present"])
        self.assertFalse(
            temporal["mvt"]["bala_windowed_canonical"]["present"])
        self.assertFalse(temporal["lag"]["present"])

    def test_partial_p4_does_not_count_stale_raw_sidecars(self):
        path = (self.root / "results" / "convention_check" /
                f"sed_grid_{self.trig}" / "p4_products_summary.json")
        value = {
            "schema_version": css.P4_SCHEMA,
            "trigger": self.trig,
            "state": "PARTIAL",
            "errors": ["montage validation failed"],
            "provisional": True,
        }
        path.write_text(json.dumps(value, indent=2) + "\n")
        data = css.build_campaign(self.root, (self.trig,))
        p4 = data["bursts"][0]["p3_p4"]
        self.assertFalse(p4["p4_authority"]["valid"])
        self.assertEqual(p4["p4_montages"]["sidecars_present"], 0)
        self.assertFalse(p4["p4_parameter_tables"]["manifest_present"])
        self.assertTrue(any("invalid/incomplete P4 authority" in message
                            for message in data["bursts"][0]["input_errors"]))


class CampaignScienceSummaryLiveSchemaTest(unittest.TestCase):
    """Lock the aggregator to real producer schemas already in this repo."""

    root = css.REPO

    def test_live_promoted_fit_schema(self):
        trig = "bn081125496"
        path = self.root / "results" / "convention_check" / trig / "spectral_fits.ecsv"
        if not path.is_file():
            self.skipTest(f"live canonical example absent: {path}")
        errors = []
        table, meta, _, _, schema = css._load_canonical(
            self.root, trig, errors)
        self.assertIsNotNone(table)
        self.assertEqual(schema["model_prefixes"], list(css.HIGHE_PREFIXES))
        self.assertTrue(schema["valid"], schema["issues"])
        self.assertEqual(meta["models"],
                         [css.MODEL_NAMES[p] for p in css.HIGHE_PREFIXES])

    def test_live_temporal_catalog_schema(self):
        path = self.root / "results" / "temporal_catalog_all106.ecsv"
        table = Table.read(path, format="ascii.ecsv")
        required = {
            "TRIGGER_NAME", "REF_DET", "T90", "T90_ERR",
            "T90_ERR_LO", "T90_ERR_HI", "T90_WINDOW_TRUNCATED",
            "T90_START", "T90_STOP", "T50", "MVT_S", "MVT_ERR_S",
            "MVT_TYPE", "TAIL_OUTSIDE_WINDOW_CTS",
            "TAIL_OUTSIDE_WINDOW_SIG",
        }
        self.assertFalse(required - set(table.colnames))
        triggers = [str(value).strip() for value in table["TRIGGER_NAME"]]
        self.assertEqual(len(triggers), len(set(triggers)))

    def test_live_bala_cwt_and_lag_semantics(self):
        trig = "bn081222204"
        bala = json.loads((self.root / "results" / "mvt_upstream" /
                           "run_step7" / trig / "result.json").read_text())
        self.assertEqual(bala["trigger"], trig)
        self.assertEqual(bala["engine"], "mvtfermi_upstream")
        self.assertIn(bala["status"], {"detection", "limit"})
        selected = [point for point in bala["delta_curve"]
                    if abs(float(point["delta_s"]) - float(bala["delta_s"])) < 1e-9
                    and abs(float(point["interval_start_s"])
                            - float(bala["interval_start_s"])) < 1e-6]
        self.assertEqual(len(selected), 1)
        # delta_curve is serialized from the upstream CSV at two decimals;
        # the headline preserves the worker's full-precision weighted value.
        self.assertAlmostEqual(float(bala["significance"]),
                               float(selected[0]["significance_weighted"]),
                               delta=0.01)
        self.assertNotEqual(float(bala["significance"]),
                            float(selected[0]["significance_z"]))

        cwt = json.loads((self.root / "results" / "mvt_cwt" /
                          f"{trig}_mvt_cwt.json").read_text())
        self.assertEqual(cwt["trig"], trig)
        self.assertEqual(cwt["band_keV"], [8.0, 900.0])
        for key in ("mvt_cwt_s", "mvt_cwt_err_s", "dt_s", "dj",
                    "noise_percentile", "role"):
            self.assertIn(key, cwt)

        lag = json.loads((self.root / "results" / "sweep106" / trig /
                          f"{trig}_step7_lag_latbright.json").read_text())
        self.assertEqual(lag["trig"], trig)
        self.assertEqual(lag["soft_keV"], [25.0, 50.0])
        self.assertEqual(lag["hard_keV"], [100.0, 300.0])
        self.assertIn("POSITIVE", lag["convention"])
        self.assertIn("soft lags hard", lag["convention"])
        scans = [float(value) for value in lag["windows"]["scan_taus_s"]]
        self.assertAlmostEqual(
            float(lag["windows"]["window_systematic_s"]),
            0.5 * (max(scans) - min(scans)), places=10)

    def test_live_montage_sidecar_schema(self):
        trig = "bn081222204"
        paths = sorted((self.root / "results" / "convention_check" /
                        f"sed_grid_{trig}" / "montage").glob(
                            f"{trig}_montage_*.json"))
        if not paths:
            self.skipTest("live montage sidecars absent")
        for path in paths:
            with self.subTest(path=path.name):
                sidecar = json.loads(path.read_text())
                self.assertEqual(sidecar["n_panels"], 24)
                self.assertEqual(len(sidecar["order"]), 24)
                self.assertEqual(set(sidecar["order"]), set(css.HIGHE_PREFIXES))
                self.assertGreaterEqual(sidecar["n_missing"], 0)

    def test_live_p3_sed_and_p4_parameter_sidecar_schemas(self):
        trig = "bn081222204"
        grid = (self.root / "results" / "convention_check" /
                f"sed_grid_{trig}")
        sed_paths = sorted(grid.glob(f"{trig}_SED_*.json"))
        if not sed_paths:
            self.skipTest("live P3 SED sidecars absent")
        sed = json.loads(sed_paths[0].read_text())
        required = {
            "script", "script_sha256", "trig", "bin", "model",
            "detectors", "reference", "interval_s", "aic_live",
            "aic_stored", "pgstat", "dof", "fitted_range_keV",
            "display_frame", "rng_seed",
        }
        self.assertFalse(required - set(sed))
        self.assertEqual(sed["trig"], trig)
        self.assertLessEqual(
            abs(float(sed["aic_live"]) - float(sed["aic_stored"])), 0.1)

        par_paths = sorted((self.root / "results" / "convention_check" /
                            "param_evolution").glob(
                                f"{trig}_paramevo_*.json"))
        if not par_paths:
            self.skipTest("live P4 parameter-evolution sidecars absent")
        par = json.loads(par_paths[0].read_text())
        self.assertEqual(par["trig"], trig)
        self.assertTrue(par["no_refit"])
        self.assertIn(par["prefix"], css.HIGHE_PREFIXES)
        self.assertIsInstance(par["winner_bins"], list)
        self.assertTrue(par["source_table"].endswith(
            f"results/convention_check/{trig}/spectral_fits.ecsv"))


if __name__ == "__main__":
    unittest.main()
