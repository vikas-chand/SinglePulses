#!/usr/bin/env python3
"""Build a provisional machine-readable campaign data appendix.

Inputs are restricted to the canonical convention-check fits and already
materialized P2/P3/P4 summaries.  This script performs no fit, figure review,
residual adjudication, or scientific claim promotion.  Output paths are
required so importing or inspecting the module cannot write campaign notes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from astropy.table import Table

try:  # direct script execution
    from campaign_products import HIGHE_PREFIXES, MODEL_NAMES
except ModuleNotFoundError:  # ``python -m notes.codex_campaign20_runtime...``
    from .campaign_products import HIGHE_PREFIXES, MODEL_NAMES


REPO = Path(__file__).resolve().parents[2]
CAMPAIGN_TRIGGERS = (
    "bn081224887", "bn090530760", "bn090620400", "bn090719063",
    "bn090804940", "bn090809978", "bn090829672", "bn091209001",
    "bn100122616", "bn100130729", "bn100612726", "bn100614498",
    "bn100707032", "bn101126198", "bn101225377", "bn110605183",
    "bn110618366", "bn110721200", "bn110920546", "bn110928180",
)
BROADBAND_TRIGGERS = {"bn081224887", "bn110721200"}
RESPONSE_BLOCKED = {"bn100130729"}

LINE_OF_DEATH = -2.0 / 3.0
THERMAL_LRT_GATE = 9.2
BB_PEAK_FACTOR = 3.9207
NAI_LOWER_EDGE_KEV = 8.0
L28_TRUST_KEV = 20.0
L28_CLEAR_KEV = 30.0
RESIDUAL_STATE = "UNGATED_NOT_ADJUDICATED"
P2_SCHEMA = "codex_campaign20.p2_temporal_summary.v1"
P4_SCHEMA = "codex_campaign20.p4_products_summary.v1"

THERMAL_PAIRS = (
    {
        "parent": "BAND",
        "child": "BANDBB",
        "lrt_column": "LRT_BANDBB_BAND",
        "label": "Band+BB versus Band",
    },
    {
        "parent": "CPL",
        "child": "CPLBB",
        "lrt_column": "LRT_CPLBB_CPL",
        "label": "CPL+BB versus CPL",
    },
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finite(value: object) -> bool:
    try:
        return not np.ma.is_masked(value) and math.isfinite(float(value))
    except Exception:
        return False


def _float(value: object) -> float | None:
    return float(value) if _finite(value) else None


def _truth(value: object) -> bool | None:
    if value is None or np.ma.is_masked(value):
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "1.0", "yes"}:
        return True
    if text in {"false", "0", "0.0", "no"}:
        return False
    return None


def _text(value: object) -> str | None:
    if value is None or np.ma.is_masked(value):
        return None
    text = str(value).strip()
    return text if text and text not in {"--", "nan", "None"} else None


def _row_value(row, column: str) -> object | None:
    return row[column] if row is not None and column in row.colnames else None


def _read_json(path: Path, errors: list[str]) -> dict | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise TypeError("top-level JSON is not an object")
        return value
    except Exception as exc:
        errors.append(f"{path}: {type(exc).__name__}: {exc}")
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _presence(path: Path, root: Path) -> dict:
    return {"path": _relative(path, root), "exists": path.is_file()}


def _canonical_schema(table: Table | None, meta: dict | None, trig: str,
                      ecsv: Path, sidecar: Path) -> dict:
    """Validate the promoted P1 authority before exposing science values.

    A table with fewer than 24 model families is an in-progress family output,
    not a canonical campaign fit.  This guard prevents a resumed run from
    silently summarizing the old 6/8/18-model tables while P1 is still active.
    """
    issues: list[str] = []
    prefixes: list[str] = []
    blocks: list[int] = []
    if table is None:
        issues.append("canonical ECSV is missing or unreadable")
    else:
        prefixes = [column[:-4] for column in table.colnames
                    if column.endswith("_AIC")]
        if tuple(prefixes) != tuple(HIGHE_PREFIXES):
            issues.append(
                f"model registry/order is {prefixes!r}; expected "
                f"{list(HIGHE_PREFIXES)!r}"
            )
        required_context = {
            "BLOCK", "T_START", "T_STOP", "T_MID", "N_DETS",
            "PLUGIN_DETS", "EAC_DETS", "EAC_SKIPPED", "BEST_AIC_MODEL",
            "LRT_BANDBB_BAND", "LRT_CPLBB_CPL",
        }
        missing_context = sorted(required_context - set(table.colnames))
        if missing_context:
            issues.append(f"missing context columns: {missing_context}")
        for prefix in HIGHE_PREFIXES:
            missing = [f"{prefix}_{suffix}" for suffix in
                       ("STATUS", "N2LL", "VALID", "AIC", "BIC")
                       if f"{prefix}_{suffix}" not in table.colnames]
            if missing:
                issues.append(f"{prefix} missing columns: {missing}")
        if "BLOCK" in table.colnames:
            try:
                blocks = [int(value) for value in table["BLOCK"]]
            except Exception as exc:
                issues.append(f"BLOCK conversion failed: {exc}")
            if len(blocks) != len(set(blocks)):
                issues.append(f"duplicate BLOCK rows: {blocks}")

    if meta is None:
        issues.append("canonical JSON sidecar is missing or unreadable")
    else:
        if meta.get("trigger") != trig:
            issues.append(
                f"sidecar trigger {meta.get('trigger')!r} does not match {trig}"
            )
        expected_models = [MODEL_NAMES[prefix] for prefix in HIGHE_PREFIXES]
        if meta.get("models") != expected_models:
            issues.append(
                f"sidecar model registry is {meta.get('models')!r}; expected "
                f"{expected_models!r}"
            )
        try:
            n_blocks = int(meta["n_blocks"])
        except Exception as exc:
            n_blocks = None
            issues.append(f"sidecar n_blocks missing/invalid: {exc}")
        if n_blocks is not None and table is not None:
            expected_blocks = [-1] + list(range(n_blocks))
            if sorted(blocks) != expected_blocks:
                issues.append(
                    f"BLOCK rows are {sorted(blocks)!r}; expected "
                    f"{expected_blocks!r}"
                )
            if len(table) != n_blocks + 1:
                issues.append(
                    f"table has {len(table)} rows; sidecar requires {n_blocks + 1}"
                )
            starts = meta.get("bin_starts")
            stops = meta.get("bin_stops")
            if not (isinstance(starts, list) and len(starts) == n_blocks):
                issues.append("sidecar bin_starts length does not match n_blocks")
            if not (isinstance(stops, list) and len(stops) == n_blocks):
                issues.append("sidecar bin_stops length does not match n_blocks")
        fit_dets = meta.get("fit_dets")
        if not isinstance(fit_dets, list) or not fit_dets:
            issues.append("sidecar fit_dets is missing or empty")

    return {
        "valid": not issues,
        "issues": issues,
        "model_prefixes": prefixes,
        "n_models": len(prefixes),
        "blocks": blocks,
        "ecsv_sha256": _sha256(ecsv) if ecsv.is_file() else None,
        "json_sha256": _sha256(sidecar) if sidecar.is_file() else None,
    }


def _edge_class(bb_peak_kev: float | None) -> str:
    if bb_peak_kev is None:
        return "UNAVAILABLE"
    if bb_peak_kev < L28_TRUST_KEV:
        return "EDGE_CONSTRAINED"
    if bb_peak_kev < L28_CLEAR_KEV:
        return "EDGE_MARGINAL"
    return "IN_BAND"


def _model_ok(row, prefix: str) -> bool:
    return _text(_row_value(row, f"{prefix}_STATUS")) == "OK"


def _model_valid(row, prefix: str) -> bool:
    return _truth(_row_value(row, f"{prefix}_VALID")) is True


def _temporal_index(path: Path, errors: list[str]) -> tuple[dict[str, Any], dict]:
    presence = _presence(path, path.parents[1] if len(path.parents) > 1 else path.parent)
    if not path.is_file():
        return {}, presence
    try:
        table = Table.read(path, format="ascii.ecsv")
        key = "TRIGGER_NAME"
        if key not in table.colnames:
            raise KeyError(key)
        index: dict[str, Any] = {}
        duplicates = []
        for row in table:
            trig = str(row[key]).strip()
            if trig in index:
                duplicates.append(trig)
            index[trig] = row
        if duplicates:
            errors.append(f"{path}: duplicate trigger rows {sorted(set(duplicates))}")
        return index, presence
    except Exception as exc:
        errors.append(f"{path}: {type(exc).__name__}: {exc}")
        return {}, presence


def _band_alpha_summary(table: Table | None) -> dict:
    values = []
    n_resolved = 0
    if table is not None:
        for row in table:
            block = int(row["BLOCK"])
            if block < 0:
                continue
            n_resolved += 1
            if not (_model_ok(row, "BAND") and _model_valid(row, "BAND")
                    and _finite(_row_value(row, "BAND_ALPHA"))):
                continue
            alpha = float(row["BAND_ALPHA"])
            neg = _float(_row_value(row, "BAND_ALPHA_NEG_ERR"))
            pos = _float(_row_value(row, "BAND_ALPHA_POS_ERR"))
            values.append({
                "block": block,
                "t_start_s": _float(_row_value(row, "T_START")),
                "t_stop_s": _float(_row_value(row, "T_STOP")),
                "band_alpha": alpha,
                "err_symmetric": _float(_row_value(row, "BAND_ALPHA_ERR")),
                "err_negative_signed_offset": neg,
                "err_positive_signed_offset": pos,
                "err_minus_magnitude": abs(neg) if neg is not None else None,
                "err_plus_magnitude": abs(pos) if pos is not None else None,
                "error_column_convention": (
                    "engine NEG_ERR/POS_ERR are signed parameter offsets"
                ),
                "relative_to_minus_two_thirds": (
                    "ABOVE" if alpha > LINE_OF_DEATH else "AT_OR_BELOW"
                ),
            })
    alphas = [item["band_alpha"] for item in values]
    return {
        "parameter": "BAND_ALPHA",
        "value_origin": "Band-model fit; not the winning-model slope",
        "selection": (
            "BLOCK>=0; BAND_STATUS=OK; BAND_VALID=true; finite BAND_ALPHA"
        ),
        "comparison_basis": "central fitted values; parameter errors not used in count",
        "line_of_death": LINE_OF_DEATH,
        "n_resolved_rows": n_resolved,
        "n_usable_band_fits": len(values),
        "range": {
            "min": min(alphas) if alphas else None,
            "max": max(alphas) if alphas else None,
        },
        "n_above_minus_two_thirds": sum(v > LINE_OF_DEATH for v in alphas),
        "n_at_or_below_minus_two_thirds": sum(v <= LINE_OF_DEATH for v in alphas),
        "values": values,
    }


def _thermal_candidates(table: Table | None) -> list[dict]:
    candidates = []
    if table is None:
        return candidates
    for row in table:
        block = int(row["BLOCK"])
        for pair in THERMAL_PAIRS:
            child = pair["child"]
            parent = pair["parent"]
            lrt = _float(_row_value(row, pair["lrt_column"]))
            if not (_model_ok(row, child) and _model_valid(row, child)
                    and _model_ok(row, parent) and lrt is not None
                    and lrt >= THERMAL_LRT_GATE):
                continue
            kt = _float(_row_value(row, f"{child}_KT"))
            kt_neg = _float(_row_value(row, f"{child}_KT_NEG_ERR"))
            kt_pos = _float(_row_value(row, f"{child}_KT_POS_ERR"))
            peak = BB_PEAK_FACTOR * kt if kt is not None else None
            candidates.append({
                "block": block,
                "scope": "TIME_INTEGRATED" if block < 0 else "TIME_RESOLVED",
                "t_start_s": _float(_row_value(row, "T_START")),
                "t_stop_s": _float(_row_value(row, "T_STOP")),
                "nested_pair": pair["label"],
                "parent_model": parent,
                "composite_model": child,
                "parent_status": _text(_row_value(row, f"{parent}_STATUS")),
                "parent_valid": _truth(_row_value(row, f"{parent}_VALID")),
                "composite_status": _text(_row_value(row, f"{child}_STATUS")),
                "composite_valid": _truth(_row_value(row, f"{child}_VALID")),
                "lrt_column": pair["lrt_column"],
                "lrt": lrt,
                "lrt_gate": THERMAL_LRT_GATE,
                "gate_pass": True,
                "classification": "STATISTICAL_CANDIDATE_ONLY",
                "boundary_calibration": "NOT_SIMULATION_CALIBRATED",
                "kT_keV": kt,
                "kT_err_symmetric_keV": _float(_row_value(row, f"{child}_KT_ERR")),
                "kT_neg_err_signed_offset_keV": kt_neg,
                "kT_pos_err_signed_offset_keV": kt_pos,
                "kT_err_minus_magnitude_keV": (
                    abs(kt_neg) if kt_neg is not None else None
                ),
                "kT_err_plus_magnitude_keV": (
                    abs(kt_pos) if kt_pos is not None else None
                ),
                "error_column_convention": (
                    "engine NEG_ERR/POS_ERR are signed parameter offsets"
                ),
                "bb_peak_factor": BB_PEAK_FACTOR,
                "bb_peak_keV": peak,
                "nai_lower_edge_keV": NAI_LOWER_EDGE_KEV,
                "bb_peak_vs_8keV": (
                    "AT_OR_ABOVE_8_KEV" if peak is not None and peak >= NAI_LOWER_EDGE_KEV
                    else "BELOW_8_KEV" if peak is not None else "UNAVAILABLE"
                ),
                "l28_edge_class": _edge_class(peak),
                "l28_thresholds_keV": [L28_TRUST_KEV, L28_CLEAR_KEV],
                "l28_bb_transfer": "PROJECT_INFERENCE_FROM_2SBPL_EDGE_POLICY",
                "l28_edge_population_threshold_pass": bool(
                    peak is not None and peak >= L28_CLEAR_KEV
                ),
                "population_promotion_eligible": False,
                "population_promotion_blockers": [
                    "RESIDUAL_EVIDENCE_UNGATED",
                    "COMPONENT_LRT_NOT_SIMULATION_CALIBRATED",
                    *(["L28_EDGE_CLASS_NOT_CLEAR"]
                      if peak is None or peak < L28_CLEAR_KEV else []),
                ],
                "residual_evidence": {
                    "state": RESIDUAL_STATE,
                    "adjudicated": False,
                    "source_used": None,
                },
            })
    return candidates


def _empty_p2_temporal(root: Path, trig: str) -> tuple[dict, dict, dict]:
    p2_path = root / "results" / "sweep106" / trig / "p2_temporal_summary.json"
    t90 = {
        "present": False,
        "source": _relative(p2_path, root),
        "estimator_label": "WINDOWED_COUNT_SPACE_T90_APPROVED_SOURCE",
        "lower_limit": None,
        "lower_limit_basis": "P2_SUMMARY_MISSING_OR_INVALID",
    }
    mvt = {
        "bala_windowed_canonical": {
            "present": False,
            "source": _relative(p2_path, root),
            "estimator_label": "BALA_WINDOWED_CANONICAL",
            "selection_source": "P2-validated result.json engine-selected row",
        },
        "cwt_global_crosscheck": {
            "present": False,
            "source": _relative(p2_path, root),
            "estimator_label": "CWT_GLOBAL_GRID_QUANTIZED_CROSSCHECK",
            "error_interpretation": "HALF_CWT_SCALE_GRID_SPACING",
        },
        "haar_in_chain_crosscheck": {
            "present": False,
            "source": _relative(p2_path, root),
            "estimator_label": "HAAR_GLOBAL_IN_CHAIN_CROSSCHECK",
        },
    }
    lag = {
        "present": False,
        "source": _relative(p2_path, root),
        "estimator_label": "LATBRIGHT_DCCF_ASYMMETRIC_GAUSSIAN",
        "convention": "POSITIVE = soft 25–50 keV photons lag hard 100–300 keV photons",
    }
    return t90, mvt, lag


def _selected_bala_z(raw: dict | None, delta_s: float | None,
                     interval_start_s: float | None) -> float | None:
    """Return the z-score for the engine-selected row, never reselect a row."""
    if raw is None or delta_s is None:
        return None
    matches = []
    for point in raw.get("delta_curve", []):
        if not isinstance(point, dict):
            continue
        delta = _float(point.get("delta_s"))
        start = _float(point.get("interval_start_s"))
        if delta is None or not math.isclose(delta, delta_s, abs_tol=1e-9):
            continue
        if (interval_start_s is not None and start is not None
                and not math.isclose(start, interval_start_s, abs_tol=1e-6)):
            continue
        matches.append(_float(point.get("significance_z")))
    finite = [value for value in matches if value is not None]
    return finite[0] if len(finite) == 1 else None


def _p2_temporal(root: Path, trig: str,
                 errors: list[str]) -> tuple[dict, dict, dict, dict]:
    """Read the normalized, fail-closed P2 summary.

    Direct raw files are intentionally not a fallback.  The P2 controller
    validates the temporal row, current-fit Step-9 binding, Bala identity,
    CWT/lag script hashes, bands, conventions, and window systematic.  A
    partial P2 summary explicitly forbids substitution from legacy catalogs.
    """
    path = root / "results" / "sweep106" / trig / "p2_temporal_summary.json"
    record = {
        "path": _relative(path, root),
        "exists": path.is_file(),
        "valid": False,
        "complete": False,
        "temporal_values_complete": False,
        "schema_version": None,
    }
    empty_t90, empty_mvt, empty_lag = _empty_p2_temporal(root, trig)
    value = _read_json(path, errors)
    if value is None:
        return empty_t90, empty_mvt, empty_lag, record
    record["schema_version"] = value.get("schema_version")
    record["complete"] = value.get("complete") is True
    record["temporal_values_complete"] = (
        value.get("temporal_values_complete") is True
    )
    record["validation_errors"] = value.get("validation_errors") or []
    issues = []
    if value.get("schema_version") != P2_SCHEMA:
        issues.append(f"schema_version={value.get('schema_version')!r}")
    if value.get("trigger") != trig:
        issues.append(f"trigger={value.get('trigger')!r}")
    values_complete = (value.get("complete") is True or
                       value.get("temporal_values_complete") is True)
    if not values_complete:
        issues.append(
            "neither complete nor temporal_values_complete is true; "
            f"validation_errors={value.get('validation_errors')!r}"
        )
    for key in ("t90", "mvt", "lag"):
        if not isinstance(value.get(key), dict):
            issues.append(f"missing object {key}")
    if issues:
        message = f"{path}: invalid/incomplete P2 authority: " + "; ".join(issues)
        errors.append(message)
        record["issues"] = issues
        return empty_t90, empty_mvt, empty_lag, record
    if value.get("complete") is not True:
        # The timing values are validated, but a non-timing P2 product (for
        # response-blocked #12, the current-fit Step-9 figure) is incomplete.
        # Preserve both facts; do not demote the estimators or fake a full pass.
        errors.append(
            f"{path}: temporal values validated but P2 product is incomplete: "
            f"{value.get('validation_errors')!r}"
        )

    t90_in = value["t90"]
    mvt_in = value["mvt"]
    bala = mvt_in.get("canonical_bala")
    cwt = mvt_in.get("noncanonical_cwt")
    haar = mvt_in.get("noncanonical_haar")
    lag_in = value["lag"]
    for name, item in (("canonical_bala", bala), ("noncanonical_cwt", cwt),
                       ("noncanonical_haar", haar)):
        if not isinstance(item, dict):
            issues.append(f"mvt.{name} is not an object")
    if issues:
        errors.append(f"{path}: malformed complete P2 summary: " + "; ".join(issues))
        record["issues"] = issues
        return empty_t90, empty_mvt, empty_lag, record

    lower = _truth(t90_in.get("lower_limit"))
    if lower is True:
        lower_basis = t90_in.get("lower_limit_reason") or "P2_LOWER_LIMIT_TRUE"
    else:
        lower_basis = "P2_LOWER_LIMIT_FALSE" if lower is False else "P2_LIMIT_UNKNOWN"
    t90 = {
        "present": True,
        "source": _relative(path, root),
        "estimator_label": t90_in.get("estimator_label"),
        "reference_detector": t90_in.get("ref_detector"),
        "band_keV": [8.0, 900.0],
        "t90_s": _float(t90_in.get("t90_s")),
        "t90_err_s": _float(t90_in.get("t90_err_s")),
        "t90_err_negative_s": _float(t90_in.get("t90_err_lo_s")),
        "t90_err_positive_s": _float(t90_in.get("t90_err_hi_s")),
        "t90_start_s": _float(t90_in.get("t90_start_s")),
        "t90_stop_s": _float(t90_in.get("t90_stop_s")),
        "approved_src_window_s": t90_in.get("approved_src_window_s"),
        "window_truncated": _truth(t90_in.get("t90_window_truncated")),
        "tail_outside_window_counts": _float(
            t90_in.get("tail_outside_window_counts")),
        "tail_significance_sigma": _float(
            t90_in.get("tail_outside_window_sigma")),
        "tail_outside_window_interval_s": t90_in.get(
            "tail_outside_window_interval_s"),
        "tail_lower_limit_threshold_sigma": 3.0,
        "lower_limit": lower,
        "lower_limit_basis": lower_basis,
        "comparability": "WINDOW_BAND_AND_ESTIMATOR_DEPENDENT",
    }

    interval = bala.get("interval_s") or [None, None]
    delta = _float(bala.get("delta_s"))
    interval_start = _float(interval[0]) if len(interval) > 0 else None
    interval_stop = _float(interval[1]) if len(interval) > 1 else None
    raw_bala_path = (root / "results" / "mvt_upstream" / "run_step7" /
                     trig / "result.json")
    raw_bala = _read_json(raw_bala_path, errors)
    selected_z = _selected_bala_z(raw_bala, delta, interval_start)
    weighted = _float(bala.get("significance"))
    mvt = {
        "bala_windowed_canonical": {
            "present": True,
            "source": _relative(raw_bala_path, root),
            "p2_authority": _relative(path, root),
            "estimator_label": bala.get("estimator_label"),
            "engine": "mvtfermi_upstream",
            "status": bala.get("status"),
            "limit_relation": bala.get("limit_relation"),
            "mvt_s": _float(bala.get("mvt_s")),
            "mvt_err_s": _float(bala.get("mvt_err_s")),
            "delta_s": delta,
            "interval_start_s": interval_start,
            "interval_stop_s": interval_stop,
            "significance": weighted,
            "significance_semantics": (
                "ENGINE_SELECTION_WEIGHTED_MEAN_STATISTIC_NOT_GAUSSIAN_Z"
            ),
            "selected_delta_significance_z": selected_z,
            "selection_source": "P2-validated result.json engine-selected row",
            "detectors": bala.get("detectors"),
        },
        "cwt_global_crosscheck": {
            "present": True,
            "source": _relative(path, root),
            "estimator_label": cwt.get("estimator_label"),
            "mvt_s": _float(cwt.get("mvt_s")),
            "mvt_err_s": _float(cwt.get("mvt_err_s")),
            "band_keV": cwt.get("band_keV"),
            "window_s": cwt.get("window_s"),
            "dt_s": _float(cwt.get("dt_s")),
            "dj": _float(cwt.get("dj")),
            "noise_percentile": _float(cwt.get("noise_percentile")),
            "error_interpretation": "HALF_CWT_SCALE_GRID_SPACING",
        },
        "haar_in_chain_crosscheck": {
            "present": True,
            "source": _relative(path, root),
            "estimator_label": haar.get("estimator_label"),
            "mvt_s": _float(haar.get("mvt_s")),
            "mvt_err_s": _float(haar.get("mvt_err_s")),
            "type": haar.get("type"),
            "upper_limit": _truth(haar.get("upper_limit")),
        },
    }
    lag_out = {
        "present": True,
        "source": _relative(path, root),
        "estimator_label": lag_in.get("estimator_label"),
        "tau_s": _float(lag_in.get("tau_s")),
        "sigma_l_s": _float(lag_in.get("sigma_l_s")),
        "sigma_r_s": _float(lag_in.get("sigma_r_s")),
        "stat_error_minus_s": _float(lag_in.get("sigma_l_s")),
        "stat_error_plus_s": _float(lag_in.get("sigma_r_s")),
        "window_systematic_s": _float(lag_in.get("window_systematic_s")),
        "peak_significance_sigma": _float(lag_in.get("peak_significance_sigma")),
        "soft_keV": lag_in.get("soft_band_keV"),
        "hard_keV": lag_in.get("hard_band_keV"),
        "convention": lag_in.get("positive_means"),
        "fit_window_scan_s": lag_in.get("scan_half_widths_s"),
        "fit_window_scan_taus_s": lag_in.get("scan_taus_s"),
    }
    record["valid"] = True
    return t90, mvt, lag_out, record


def _broadband(table: Table | None, meta: dict | None, trig: str) -> dict:
    if trig not in BROADBAND_TRIGGERS:
        return {"applicable": False}
    fit_dets = [str(value) for value in (meta or {}).get("fit_dets", [])]
    lat_blocks = []
    plugin_dets_by_block = {}
    lle_rows = []
    if table is not None and "PLUGIN_DETS" in table.colnames:
        for row in table:
            block = int(row["BLOCK"])
            dets = [item.strip() for item in str(row["PLUGIN_DETS"]).split(",")
                    if item.strip()]
            plugin_dets_by_block[str(block)] = dets
            lle_rows.append("lle" in dets)
            if block >= 0 and any(item.upper() == "LAT" for item in dets):
                lat_blocks.append(block)
    lle_in_fit_dets = "lle" in fit_dets
    lle_every_row = bool(lle_rows) and all(lle_rows)
    coverage_issues = []
    if not lle_in_fit_dets:
        coverage_issues.append("LLE_MISSING_FROM_FIT_DETS")
    if not lle_every_row:
        coverage_issues.append("LLE_MISSING_FROM_ONE_OR_MORE_SPECTRA")
    if not lat_blocks:
        coverage_issues.append(
            "NO_LAT_PLUGIN_BLOCKS; REQUIRE_DECLARED_LAT_BUILD_DEGRADATION"
        )
    return {
        "applicable": True,
        "fit_dets": fit_dets,
        "lle_in_fit_dets": lle_in_fit_dets,
        "lle_in_every_spectrum": lle_every_row,
        "lle_ranges_keV": (meta or {}).get("LLE_RANGES"),
        "lle_energy_range_MeV": [20.0, 100.0],
        "lat_plugin_blocks": lat_blocks,
        "lat_block_count": len(lat_blocks),
        "plugin_dets_by_block": plugin_dets_by_block,
        "lat_energy_range_MeV": {"lower_exclusive": 100.0, "upper": None},
        "lat_energy_label": ">100 MeV (no finite upper cut recorded by scripts/10)",
        "tint_lat_included": "LAT" in plugin_dets_by_block.get("-1", []),
        "coverage_contract_status": (
            "FULL_GBM_LLE_AND_AT_LEAST_ONE_LAT_BLOCK"
            if not coverage_issues else "DEGRADED_OR_INCOMPLETE"
        ),
        "coverage_contract_issues": coverage_issues,
        "matched_gbm_only_counterfactual_present": False,
        "extra_band_effect_state": "NOT_IDENTIFIABLE_WITHOUT_MATCHED_GBM_ONLY_REFIT",
        "no_counterfactual_limitation": True,
    }


def _p3_p4(root: Path, trig: str, expected_bins: int,
           errors: list[str]) -> dict:
    grid = root / "results" / "convention_check" / f"sed_grid_{trig}"
    sweep_path = grid / "sweep_summary.json"
    sweep = _read_json(sweep_path, errors)
    sweep_issues = []
    if sweep is not None:
        if sweep.get("trigger") != trig:
            sweep_issues.append(f"trigger={sweep.get('trigger')!r}")
        for key in ("pairs", "ok", "fail"):
            if not isinstance(sweep.get(key), int) or sweep[key] < 0:
                sweep_issues.append(f"{key}={sweep.get(key)!r}")
        if not sweep_issues and sweep["ok"] + sweep["fail"] != sweep["pairs"]:
            sweep_issues.append("ok + fail does not equal pairs")
        if sweep.get("status") != "RESPONSE_BLOCKED":
            if sweep.get("models") != list(HIGHE_PREFIXES):
                sweep_issues.append("models do not match the canonical 24 registry")
            if not isinstance(sweep.get("bins"), list):
                sweep_issues.append("bins is not a list")
            elif expected_bins and len(sweep["bins"]) != expected_bins:
                sweep_issues.append(
                    f"bins={len(sweep['bins'])}; expected {expected_bins}"
                )
        if sweep_issues:
            errors.append(
                f"{sweep_path}: invalid P3 closure: " + "; ".join(sweep_issues)
            )

    p4_path = grid / "p4_products_summary.json"
    p4 = _read_json(p4_path, errors)
    p4_issues = []
    if p4 is not None:
        if p4.get("schema_version") != P4_SCHEMA:
            p4_issues.append(f"schema_version={p4.get('schema_version')!r}")
        if p4.get("trigger") != trig:
            p4_issues.append(f"trigger={p4.get('trigger')!r}")
        if p4.get("state") != "COMPLETE":
            p4_issues.append(
                f"state={p4.get('state')!r}; errors={p4.get('errors')!r}"
            )
        for key in ("montages", "parameter_evolution", "all_model_tables"):
            if not isinstance(p4.get(key), dict):
                p4_issues.append(f"missing object {key}")
        if not any(issue.startswith("missing object") for issue in p4_issues):
            tags = p4["montages"].get("tags")
            if not isinstance(tags, list):
                p4_issues.append("montages.tags is not a list")
                tags = []
            if p4["montages"].get("n_tags") != len(tags):
                p4_issues.append("montages.n_tags does not match tags length")
            if expected_bins and len(tags) != expected_bins:
                p4_issues.append(
                    f"montage tag count={len(tags)}; expected {expected_bins}"
                )
            missing_sum = 0
            for item in tags:
                if item.get("n_panels") != 24:
                    p4_issues.append(
                        f"montage {item.get('tag')}: n_panels != 24"
                    )
                missing = item.get("n_missing")
                if not isinstance(missing, int) or not 0 <= missing <= 24:
                    p4_issues.append(
                        f"montage {item.get('tag')}: invalid n_missing={missing!r}"
                    )
                else:
                    missing_sum += missing
            if (sweep is not None and not sweep_issues
                    and sweep.get("status") != "RESPONSE_BLOCKED"
                    and missing_sum != sweep.get("fail")):
                p4_issues.append(
                    f"sum montage n_missing={missing_sum}; P3 fail={sweep.get('fail')}"
                )
            evolution = p4["parameter_evolution"]
            products = evolution.get("products")
            if not isinstance(products, list):
                p4_issues.append("parameter_evolution.products is not a list")
            elif evolution.get("n_models") != len(products):
                p4_issues.append(
                    "parameter_evolution.n_models does not match products length"
                )
            tables = p4["all_model_tables"]
            if tables.get("n_models_per_spectrum") != 24:
                p4_issues.append("all-model tables do not have 24 rows per spectrum")
            if expected_bins and tables.get("n_spectra") != expected_bins:
                p4_issues.append(
                    f"table n_spectra={tables.get('n_spectra')}; expected {expected_bins}"
                )
        if p4_issues:
            errors.append(
                f"{p4_path}: invalid/incomplete P4 authority: "
                + "; ".join(p4_issues)
            )

    p4_valid = p4 is not None and not p4_issues
    montage_records = []
    montage_audit = None
    par_records = []
    table_manifest = None
    if p4_valid:
        montage = p4["montages"]
        montage_audit = montage.get("fallback_audit")
        for item in montage.get("tags", []):
            sidecar = item.get("sidecar") or {}
            montage_records.append({
                "tag": item.get("tag"),
                "bin": item.get("bin"),
                "path": _relative(Path(str(sidecar.get("path", ""))), root),
                "readable": bool(sidecar.get("sha256")),
                "n_panels": item.get("n_panels"),
                "n_missing": item.get("n_missing"),
                "n_fit_failures": item.get("n_fit_failures"),
                "order_length": 24,
                "fallback": item.get("fallback"),
            })
        for item in p4["parameter_evolution"].get("products", []):
            sidecar = item.get("sidecar") or {}
            par_records.append({
                "model": item.get("model"),
                "winner_bins": item.get("winner_bins"),
                "sidecar": _relative(Path(str(sidecar.get("path", ""))), root),
            })
        table_manifest = p4["all_model_tables"].get("manifest")

    if sweep is None:
        closure_state = "MISSING"
    elif sweep_issues:
        closure_state = "INVALID"
    elif sweep.get("status") == "RESPONSE_BLOCKED":
        closure_state = "RESPONSE_BLOCKED"
    elif sweep.get("fail") == 0:
        closure_state = "GRID_CLOSED_COMPLETE"
    else:
        closure_state = "GRID_CLOSED_WITH_STRUCTURAL_FAILURES"
    return {
        "p3_sweep": {
            "source": _relative(sweep_path, root),
            "file_exists": sweep_path.is_file(),
            "present": sweep is not None and not sweep_issues,
            "schema_valid": sweep is not None and not sweep_issues,
            "pairs": sweep.get("pairs") if sweep else None,
            "ok": sweep.get("ok") if sweep else None,
            "fail": sweep.get("fail") if sweep else None,
            "status": closure_state,
            "visual_verdict": sweep.get("visual_verdict") if sweep else None,
            "issues": sweep_issues,
        },
        "p4_montages": {
            "p4_authority": _relative(p4_path, root),
            "p4_authority_present": p4_valid,
            "fallback_audit": montage_audit,
            "fallback_audit_present": bool(
                isinstance(montage_audit, dict) and montage_audit.get("sha256")
            ),
            "expected_bins": expected_bins,
            "sidecars_present": len(montage_records),
            "all_expected_sidecars_present": (
                p4_valid and len(montage_records) == expected_bins
                if expected_bins else False
            ),
            "sidecars": montage_records,
            "residual_evidence_state": RESIDUAL_STATE,
        },
        "p4_parameter_evolution": {
            "summary_count": len(par_records),
            "summaries": par_records,
        },
        "p4_parameter_tables": {
            "manifest": table_manifest,
            "manifest_present": bool(
                isinstance(table_manifest, dict) and table_manifest.get("sha256")
            ),
            "n_spectra": (
                p4["all_model_tables"].get("n_spectra") if p4_valid else None
            ),
            "n_models": (
                p4["all_model_tables"].get("n_models_per_spectrum")
                if p4_valid else None
            ),
        },
        "p4_authority": {
            "path": _relative(p4_path, root),
            "file_exists": p4_path.is_file(),
            "valid": p4_valid,
            "state": p4.get("state") if p4 else None,
            "issues": p4_issues,
        },
    }


def _load_canonical(root: Path, trig: str, errors: list[str]):
    fit_dir = root / "results" / "convention_check" / trig
    ecsv = fit_dir / "spectral_fits.ecsv"
    sidecar = fit_dir / "spectral_fits.json"
    table = None
    meta = _read_json(sidecar, errors)
    if ecsv.is_file():
        try:
            table = Table.read(ecsv, format="ascii.ecsv")
        except Exception as exc:
            errors.append(f"{ecsv}: {type(exc).__name__}: {exc}")
    schema = _canonical_schema(table, meta, trig, ecsv, sidecar)
    if not schema["valid"]:
        errors.extend(f"{ecsv}: canonical schema: {issue}"
                      for issue in schema["issues"])
    return table, meta, ecsv, sidecar, schema


def _product_presence(root: Path, trig: str, temporal_present: bool,
                      table: Table | None, meta: dict | None,
                      p3p4: dict, mvt: dict, lag: dict,
                      ecsv: Path, sidecar: Path, canonical_schema: dict,
                      p2_record: dict) -> dict:
    return {
        "canonical_fit_table": _presence(ecsv, root),
        "canonical_fit_sidecar": _presence(sidecar, root),
        "canonical_schema_valid": canonical_schema["valid"],
        "canonical_model_count": canonical_schema["n_models"],
        "temporal_catalog_row": temporal_present,
        "p2_temporal_summary": p2_record,
        "bala_result_json": mvt["bala_windowed_canonical"]["present"],
        "cwt_summary_json": mvt["cwt_global_crosscheck"]["present"],
        "lag_summary_json": lag["present"],
        "p3_sweep_summary_json": p3p4["p3_sweep"]["present"],
        "p4_montage_summary_count": p3p4["p4_montages"]["sidecars_present"],
        "p4_montage_expected_count": p3p4["p4_montages"]["expected_bins"],
        "p4_parameter_evolution_summary_count": (
            p3p4["p4_parameter_evolution"]["summary_count"]),
        "p4_parameter_tables_manifest": (
            p3p4["p4_parameter_tables"]["manifest_present"]),
        "canonical_rows": len(table) if table is not None else 0,
        "fit_dets_recorded": bool(meta and "fit_dets" in meta),
    }


def build_burst(root: Path, trig: str, campaign_index: int,
                temporal_rows: dict[str, Any]) -> dict:
    errors: list[str] = []
    table, meta, ecsv, sidecar, canonical_schema = _load_canonical(
        root, trig, errors)
    science_table = table if canonical_schema["valid"] else None
    temporal_row = temporal_rows.get(trig)
    t90, mvt, lag, p2_record = _p2_temporal(root, trig, errors)
    p3p4 = _p3_p4(
        root, trig, len(science_table) if science_table is not None else 0,
        errors)
    products = _product_presence(
        root, trig, temporal_row is not None, table, meta, p3p4, mvt, lag,
        ecsv, sidecar, canonical_schema, p2_record)
    if trig in RESPONSE_BLOCKED and not canonical_schema["valid"]:
        availability = "RESPONSE_BLOCKED"
    elif table is None:
        availability = "CANONICAL_FIT_MISSING"
    elif not canonical_schema["valid"]:
        availability = "CANONICAL_SCHEMA_INVALID"
    elif errors:
        availability = "CANONICAL_AVAILABLE_WITH_SUMMARY_ERRORS"
    else:
        availability = "CANONICAL_AVAILABLE"
    return {
        "campaign_index": campaign_index,
        "trigger": trig,
        "grb_name": f"GRB {trig[2:8]}",
        "availability_status": availability,
        "provisional": True,
        "product_presence": products,
        "spectral": {
            "canonical_source": _relative(ecsv, root),
            "fit_metadata_source": _relative(sidecar, root),
            "n_rows": len(table) if table is not None else 0,
            "canonical_schema": canonical_schema,
            "n_resolved_bins": (
                sum(int(row["BLOCK"]) >= 0 for row in science_table)
                if science_table is not None else 0
            ),
            "band_alpha_resolved": _band_alpha_summary(science_table),
            "thermal_candidates": _thermal_candidates(science_table),
            "residual_evidence": {
                "state": RESIDUAL_STATE,
                "adjudicated": False,
                "figures_used_for_classification": False,
            },
        },
        "temporal": {
            "t90_tail": t90,
            "mvt": mvt,
            "lag": lag,
        },
        "broadband": _broadband(science_table, meta, trig),
        "p3_p4": p3p4,
        "input_errors": errors,
    }


def _aggregate(bursts: list[dict]) -> dict:
    alpha_values = [
        item["band_alpha"]
        for burst in bursts
        for item in burst["spectral"]["band_alpha_resolved"]["values"]
    ]
    candidates = [
        candidate
        for burst in bursts
        for candidate in burst["spectral"]["thermal_candidates"]
    ]
    lower_limits = [burst["temporal"]["t90_tail"]["lower_limit"]
                    for burst in bursts]
    return {
        "burst_count": len(bursts),
        "availability_status_counts": dict(Counter(
            burst["availability_status"] for burst in bursts)),
        "band_alpha_resolved": {
            "parameter": "BAND_ALPHA",
            "value_origin": "Band-model fits only",
            "line_of_death": LINE_OF_DEATH,
            "n_values": len(alpha_values),
            "range": {
                "min": min(alpha_values) if alpha_values else None,
                "max": max(alpha_values) if alpha_values else None,
            },
            "n_above_minus_two_thirds": sum(v > LINE_OF_DEATH for v in alpha_values),
            "n_at_or_below_minus_two_thirds": sum(v <= LINE_OF_DEATH for v in alpha_values),
        },
        "thermal_candidates": {
            "gate": "valid composite; parent STATUS=OK; nested LRT>=9.2",
            "count_all": len(candidates),
            "count_time_resolved": sum(c["scope"] == "TIME_RESOLVED"
                                       for c in candidates),
            "count_time_integrated": sum(c["scope"] == "TIME_INTEGRATED"
                                         for c in candidates),
            "counts_by_composite": dict(Counter(
                c["composite_model"] for c in candidates)),
            "counts_by_l28_class": dict(Counter(
                c["l28_edge_class"] for c in candidates)),
            "residual_evidence_state": RESIDUAL_STATE,
        },
        "t90_lower_limit_counts": {
            "true": sum(value is True for value in lower_limits),
            "false": sum(value is False for value in lower_limits),
            "unknown": sum(value is None for value in lower_limits),
        },
        "broadband_triggers": sorted(BROADBAND_TRIGGERS),
        "broadband_counterfactual_state": (
            "NOT_IDENTIFIABLE_WITHOUT_MATCHED_GBM_ONLY_REFIT"
        ),
    }


def build_campaign(root: Path = REPO,
                   triggers: tuple[str, ...] = CAMPAIGN_TRIGGERS) -> dict:
    errors: list[str] = []
    temporal_path = root / "results" / "temporal_catalog_all106.ecsv"
    temporal_rows, temporal_presence = _temporal_index(temporal_path, errors)
    start = 3 if tuple(triggers) == CAMPAIGN_TRIGGERS else 1
    bursts = [build_burst(root, trig, start + index, temporal_rows)
              for index, trig in enumerate(triggers)]
    return {
        "schema": "campaign_science_summary.v2",
        "generated_utc": _utc_now(),
        "role": "PRODUCER_DATA_AGGREGATION",
        "scope": list(triggers),
        "provisional": True,
        "source_policy": (
            "promoted exact-24-model canonical fits plus normalized, "
            "materialized P2/P3/P4 authorities; no legacy-product fallback"
        ),
        "thresholds": {
            "band_alpha_line_of_death": LINE_OF_DEATH,
            "thermal_nested_lrt": THERMAL_LRT_GATE,
            "bb_peak_factor": BB_PEAK_FACTOR,
            "nai_lower_edge_keV": NAI_LOWER_EDGE_KEV,
            "l28_edge_constrained_below_keV": L28_TRUST_KEV,
            "l28_edge_marginal_below_keV": L28_CLEAR_KEV,
            "tail_lower_limit_sigma": 3.0,
        },
        "residual_evidence_policy": RESIDUAL_STATE,
        "temporal_catalog": temporal_presence,
        "global_input_errors": errors,
        "cross_burst": _aggregate(bursts),
        "bursts": bursts,
    }


def _fmt(value: object, digits: int = 4) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}g}"
    return str(value).replace("|", "\\|")


def render_markdown(data: dict) -> str:
    lines = [
        "# Provisional campaign data appendix — bursts #3–#22",
        "",
        f"- Schema: `{data['schema']}`",
        f"- Generated UTC: `{data['generated_utc']}`",
        f"- Source policy: `{data['source_policy']}`",
        f"- Residual evidence: `{data['residual_evidence_policy']}`",
        "- Status: `PROVISIONAL`",
        "",
        "## Product/status matrix",
        "",
        "| # | Trigger | Availability | Fit rows | Temporal | Bala | CWT | Lag | P3 | Montages | Tables | Errors |",
        "|---:|---|---|---:|---|---|---|---|---|---:|---|---:|",
    ]
    for burst in data["bursts"]:
        p = burst["product_presence"]
        lines.append(
            f"| {burst['campaign_index']} | `{burst['trigger']}` | "
            f"{burst['availability_status']} | {p['canonical_rows']} | "
            f"{_fmt(p['temporal_catalog_row'])} | {_fmt(p['bala_result_json'])} | "
            f"{_fmt(p['cwt_summary_json'])} | {_fmt(p['lag_summary_json'])} | "
            f"{_fmt(p['p3_sweep_summary_json'])} | "
            f"{p['p4_montage_summary_count']}/{p['p4_montage_expected_count']} | "
            f"{_fmt(p['p4_parameter_tables_manifest'])} | "
            f"{len(burst['input_errors'])} |"
        )

    lines += [
        "",
        "## Band-fit alpha values in resolved bins",
        "",
        "`BAND_ALPHA` only; selection = `BLOCK>=0`, `BAND_STATUS=OK`, "
        "`BAND_VALID=true`, finite alpha. Counts use central values.",
        "",
        "| Trigger | Resolved rows | Usable Band fits | Range | > −2/3 | ≤ −2/3 |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for burst in data["bursts"]:
        band = burst["spectral"]["band_alpha_resolved"]
        span = (f"{_fmt(band['range']['min'])} to {_fmt(band['range']['max'])}"
                if band["range"]["min"] is not None else "—")
        lines.append(
            f"| `{burst['trigger']}` | {band['n_resolved_rows']} | "
            f"{band['n_usable_band_fits']} | {span} | "
            f"{band['n_above_minus_two_thirds']} | "
            f"{band['n_at_or_below_minus_two_thirds']} |"
        )

    lines += [
        "",
        "## Thermal statistical-candidate rows",
        "",
        "Gate = valid Band+BB/CPL+BB composite, successful parent, nested "
        "LRT ≥ 9.2. Residual evidence remains `UNGATED_NOT_ADJUDICATED`.",
        "",
        "| Trigger | Block | Scope | Pair | LRT | kT (keV) | 3.9207 kT (keV) | vs 8 keV | L28 class | Residual state |",
        "|---|---:|---|---|---:|---:|---:|---|---|---|",
    ]
    thermal_rows = 0
    for burst in data["bursts"]:
        for item in burst["spectral"]["thermal_candidates"]:
            thermal_rows += 1
            lines.append(
                f"| `{burst['trigger']}` | {item['block']} | {item['scope']} | "
                f"{item['nested_pair']} | {_fmt(item['lrt'])} | "
                f"{_fmt(item['kT_keV'])} | {_fmt(item['bb_peak_keV'])} | "
                f"{item['bb_peak_vs_8keV']} | {item['l28_edge_class']} | "
                f"{item['residual_evidence']['state']} |"
            )
    if not thermal_rows:
        lines.append("| — | — | — | — | — | — | — | — | — | UNGATED_NOT_ADJUDICATED |")

    lines += [
        "",
        "## Temporal estimators",
        "",
        "| Trigger | Windowed T90 (s) | Tail σ | T90 lower limit | Bala canonical (s) | Δ window (s) | CWT global (s) | Haar in-chain (s/type) | Lag τ (s) | Lag stat −/+ (s) | Window systematic (s) |",
        "|---|---:|---:|---|---:|---:|---:|---|---:|---|---:|",
    ]
    for burst in data["bursts"]:
        temporal = burst["temporal"]
        t90 = temporal["t90_tail"]
        bala = temporal["mvt"]["bala_windowed_canonical"]
        cwt = temporal["mvt"]["cwt_global_crosscheck"]
        haar = temporal["mvt"]["haar_in_chain_crosscheck"]
        lag = temporal["lag"]
        lag_err = (f"{_fmt(lag.get('sigma_l_s'))}/{_fmt(lag.get('sigma_r_s'))}"
                   if lag["present"] else "—")
        haar_value = (f"{_fmt(haar.get('mvt_s'))}/{_fmt(haar.get('type'))}"
                      if haar["present"] else "—")
        lines.append(
            f"| `{burst['trigger']}` | {_fmt(t90.get('t90_s'))} | "
            f"{_fmt(t90.get('tail_significance_sigma'))} | "
            f"{_fmt(t90.get('lower_limit'))} | {_fmt(bala.get('mvt_s'))} | "
            f"{_fmt(bala.get('delta_s'))} | {_fmt(cwt.get('mvt_s'))} | {haar_value} | "
            f"{_fmt(lag.get('tau_s'))} | {lag_err} | "
            f"{_fmt(lag.get('window_systematic_s'))} |"
        )

    lines += [
        "",
        "## Broadband product fields (#3 and #20)",
        "",
        "| Trigger | fit_dets | LLE ranges (keV) | LAT blocks | Counterfactual |",
        "|---|---|---|---|---|",
    ]
    for burst in data["bursts"]:
        broad = burst["broadband"]
        if not broad.get("applicable"):
            continue
        lines.append(
            f"| `{burst['trigger']}` | `{','.join(broad['fit_dets'])}` | "
            f"`{','.join(broad.get('lle_ranges_keV') or [])}` | "
            f"`{','.join(map(str, broad['lat_plugin_blocks']))}` | "
            f"{broad['extra_band_effect_state']} |"
        )

    lines += [
        "",
        "## Input errors and missing summaries",
        "",
        "| Trigger | Input errors |",
        "|---|---|",
    ]
    for burst in data["bursts"]:
        messages = "; ".join(burst["input_errors"]) or "—"
        lines.append(f"| `{burst['trigger']}` | {_fmt(messages)} |")
    if data["global_input_errors"]:
        lines.append(f"| `GLOBAL` | {_fmt('; '.join(data['global_input_errors']))} |")
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(text)
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--triggers", nargs="+", default=list(CAMPAIGN_TRIGGERS))
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-markdown", type=Path, required=True)
    args = parser.parse_args()
    data = build_campaign(args.repo_root.resolve(), tuple(args.triggers))
    _atomic_write(args.out_json, json.dumps(data, indent=2, allow_nan=False) + "\n")
    _atomic_write(args.out_markdown, render_markdown(data))
    print(json.dumps({
        "schema": data["schema"],
        "bursts": len(data["bursts"]),
        "thermal_candidates": data["cross_burst"]["thermal_candidates"]["count_all"],
        "out_json": str(args.out_json),
        "out_markdown": str(args.out_markdown),
        "provisional": True,
    }, indent=2))


if __name__ == "__main__":
    main()
