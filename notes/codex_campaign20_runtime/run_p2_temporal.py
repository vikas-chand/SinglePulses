#!/usr/bin/env python3
"""Run and validate campaign-20 P2 temporal products, one burst at a time.

This campaign-owned controller preserves the six-command order in the execution
brief.  It does not alter pipeline code.  The managed sandbox cannot construct a
``ProcessPoolExecutor``; the existing sitecustomize transport shim is enabled only
for scripts/46 and the Bala wrapper.  All scientific estimators remain unchanged.

The default scripts/44 invocation is retained.  Its step-9 function resolves the
legacy nested sweep fit, however, so a second render is made in /private/tmp with
the current convention-check table staged at the layout scripts/44 expects.  Only
that SHA-bound step-9 PNG is promoted to the burst product directory.

Normal output added by this controller:

  results/sweep106/<trig>/p2_temporal_summary.json
  results/sweep106/<trig>/<trig>_step44_nonspectral.source.json
  results/sweep106/<trig>/<trig>_step9_qc.source.json
  logs/codex_campaign20/p2/<trig>/*.log
  logs/codex_campaign20/p2/<trig>/*.status.json
  logs/codex_campaign20/p2/status/<trig>.json

Figures remain PRODUCER products and are always stamped UNGATED here.  This file
does not perform, infer, or record a verifier verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REPO = Path("/Users/salim/Desktop/Projects/SingleRest/Two_Breaks")
RUNTIME = REPO / "notes" / "codex_campaign20_runtime"
PYTHON = Path("/Users/salim/anaconda3/envs/threeML/bin/python")
MVT_PYTHON = Path("/Users/salim/anaconda3/envs/mvt/bin/python")
HANDBOOK = Path("/Users/salim/Desktop/Projects/GRB_Handbook_Project")
SWEEP = REPO / "results" / "sweep106"
FIT_ROOT = REPO / "results" / "convention_check"
MVT_ROOT = REPO / "results" / "mvt_upstream" / "run_step7"
LOG_ROOT = REPO / "logs" / "codex_campaign20" / "p2"

TRIGGERS = (
    "bn081224887", "bn090530760", "bn090620400", "bn090719063",
    "bn090804940", "bn090809978", "bn090829672", "bn091209001",
    "bn100122616", "bn100130729", "bn100612726", "bn100614498",
    "bn100707032", "bn101126198", "bn101225377", "bn110605183",
    "bn110618366", "bn110721200", "bn110920546", "bn110928180",
)

SCHEMA = "codex_campaign20.p2_temporal_summary.v1"
PHASE_SCHEMA = "codex_campaign20.p2_phase_status.v2"
STEP9_SCHEMA = "codex_campaign20.step9_current_fit_source.v1"
STEP44_BASE_SCHEMA = "codex_campaign20.step44_nonspectral_source.v2"
TEMPORAL_ROW_SCHEMA = "codex_campaign20.temporal_catalog_row_source.v1"
GATE_STATUS = "UNGATED_PENDING_INDEPENDENT_CLAUDE_FIGURE_VERIFICATION"

APPROVED_CATALOG = REPO / "results" / "background_intervals.ecsv"
TEMPORAL_CATALOG = REPO / "results" / "temporal_catalog_all106.ecsv"
LATBRIGHT_LAG = (
    Path("/Users/salim/Desktop/LATBright/GRB260226A") /
    "s02c_spectral_lag.py"
)
HANDBOOK_TEMPORAL = HANDBOOK / "grb_pipeline" / "analysis" / "temporal.py"
RESPONSE_BLOCKED = {
    "bn100130729": (
        "RESPONSE_UNCOVERED: approved source/blocks precede every approved "
        "detector RSP2 matrix"
    )
}

T90_LABEL = (
    "windowed count-space T90 inside the approved SRC interval; fitted "
    "background held fixed; background-model uncertainty not propagated"
)
BALA_LABEL = (
    "Bala windowed MVT — CANONICAL; engine-selected result.json value, "
    "never reselected by the campaign controller"
)
CWT_LABEL = (
    "CWT global MVT — NONCANONICAL cross-check; grid-quantized, with the "
    "reported uncertainty equal to half the scale-grid spacing"
)
HAAR_LABEL = "Haar global MVT — NONCANONICAL in-chain cross-check"
LAG_LABEL = (
    "LATBright s02c DCCF lag; positive = soft 25–50 keV photons lag "
    "hard 100–300 keV photons"
)

STEP44_FIGURES = (
    "step1_inventory", "step3_background", "step4_source",
    "step5_binning", "step7_temporal", "step9_qc",
)
STEP44_NONSPECTRAL_FIGURES = STEP44_FIGURES[:-1]
STEP47B_FIGURES = ("step7_pulse", "step7_lag", "step7_mvt")


class ValidationError(RuntimeError):
    """A product exists but does not satisfy its P2 contract."""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "1.0", "yes"}


def optional_float(value: Any) -> float | None:
    return float(value) if finite(value) else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, label: str) -> Path:
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValidationError(f"{label} missing or empty: {path}")
    return path


def require_fresh(path: Path, label: str, not_before_ns: int) -> Path:
    require_file(path, label)
    if path.stat().st_mtime_ns < not_before_ns:
        raise ValidationError(
            f"{label} was not rewritten by this invocation: {path}"
        )
    return path


def read_json(path: Path, label: str) -> dict[str, Any]:
    require_file(path, label)
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        raise ValidationError(f"{label} invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object: {path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    def clean(item: Any) -> Any:
        if isinstance(item, dict):
            return {str(key): clean(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(val) for val in item]
        if isinstance(item, float) and not math.isfinite(item):
            return None
        return item

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(clean(value), indent=2, sort_keys=False,
                                    allow_nan=False) + "\n")
    os.replace(temporary, path)


def artifact(path: Path) -> dict[str, Any]:
    require_file(path, "artifact")
    return {"path": str(path), "sha256": sha256(path),
            "bytes": path.stat().st_size}


_INPUT_SHA_CACHE: dict[tuple[str, int, int], str] = {}


def input_artifact(path: Path, label: str, *, optional: bool = False) -> dict[str, Any]:
    """Content-bind a phase input without rehashing static TTE files six times."""
    if not path.is_file() or path.stat().st_size <= 0:
        if optional:
            return {"path": str(path), "exists": False}
        raise ValidationError(f"{label} missing or empty: {path}")
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    digest = _INPUT_SHA_CACHE.get(key)
    if digest is None:
        digest = sha256(path)
        _INPUT_SHA_CACHE[key] = digest
    return {
        "path": str(path), "exists": True, "sha256": digest,
        "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
    }


def object_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"),
                   default=str).encode()
    ).hexdigest()


def blocks_path(trig: str) -> Path:
    return SWEEP / trig / "blocks" / f"bb_blocks_spectral_{trig}.ecsv"


def approved_rows(trig: str):
    from astropy.table import Table

    table = Table.read(APPROVED_CATALOG, format="ascii.ecsv")
    rows = table[[str(v).strip() == trig for v in table["TRIGGER_NAME"]]]
    if not len(rows):
        raise ValidationError(f"no approved rows for {trig}")
    return rows


def approved_reference_detector(trig: str) -> str:
    rows = approved_rows(trig)
    nais = [row for row in rows if str(row["DETECTOR"]).strip().startswith("n")]
    if not nais:
        raise ValidationError(f"{trig}: no approved NaI detector")
    row = min(
        nais,
        key=lambda item: float(item["DET_ANGLE"])
        if finite(item["DET_ANGLE"]) else 999.0,
    )
    return str(row["DETECTOR"]).strip()


def latest_tte(trig: str, det: str) -> Path:
    pattern = re.compile(
        rf"glg_tte_{re.escape(det)}_{re.escape(trig)}_v(\d+)\.fits?(\.gz)?$"
    )
    candidates: list[tuple[int, bool, str, Path]] = []
    for path in (REPO / "data" / trig).glob(f"glg_tte_{det}_{trig}_v*"):
        match = pattern.fullmatch(path.name)
        if match:
            candidates.append((int(match.group(1)), match.group(2) is None,
                               path.name, path))
    if not candidates:
        raise ValidationError(f"{trig}: no TTE for approved detector {det}")
    return max(candidates)[3]


def block_window(trig: str, detector: str) -> tuple[float, float]:
    from astropy.table import Table

    table = Table.read(require_file(blocks_path(trig), "adopted blocks"),
                       format="ascii.ecsv")
    rows = table[[str(value).strip() == detector for value in table["DETECTOR"]]]
    if not len(rows):
        raise ValidationError(f"{trig}: no adopted blocks for {detector}")
    start = min(float(value) for value in rows["T_START"])
    stop = max(float(value) for value in rows["T_STOP"])
    if not (finite(start) and finite(stop) and stop > start):
        raise ValidationError(f"{trig}: invalid adopted block span for {detector}")
    return start, stop


_MVT_ENGINE_MODULE = None


def mvt_engine_module():
    """Load the live Handbook engine whose own identity contract governs resume."""
    global _MVT_ENGINE_MODULE
    if _MVT_ENGINE_MODULE is not None:
        return _MVT_ENGINE_MODULE
    import importlib.util

    path = HANDBOOK / "grb_pipeline" / "analysis" / "mvt_engine.py"
    spec = importlib.util.spec_from_file_location(
        "_codex_campaign20_live_mvt_engine", require_file(path, "MVT engine")
    )
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load live MVT engine: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _MVT_ENGINE_MODULE = module
    return module


def approved_window(trig: str, ref_detector: str | None = None) -> dict[str, float]:
    rows = approved_rows(trig)
    starts = [float(r["SRC_START"]) for r in rows]
    stops = [float(r["SRC_STOP"]) for r in rows]
    if max(starts) - min(starts) > 1e-6 or max(stops) - min(stops) > 1e-6:
        raise ValidationError(f"approved SRC window differs between detectors: {trig}")
    selected = rows[0]
    if ref_detector is not None:
        matches = rows[[str(v).strip() == ref_detector for v in rows["DETECTOR"]]]
        if len(matches) != 1:
            raise ValidationError(
                f"{trig}: temporal REF_DET {ref_detector!r} has {len(matches)} approved rows"
            )
        selected = matches[0]
    return {
        "src_start_s": starts[0],
        "src_stop_s": stops[0],
        "bkg_pos_start_s": float(selected["BKG_POS_START"]),
    }


def temporal_row_payload(trig: str) -> dict[str, Any]:
    from astropy.table import Table
    import numpy as np

    path = TEMPORAL_CATALOG
    require_file(path, "temporal catalog")
    table = Table.read(path, format="ascii.ecsv")
    rows = table[[str(v).strip() == trig for v in table["TRIGGER_NAME"]]]
    if len(rows) != 1:
        raise ValidationError(f"expected one temporal row for {trig}; found {len(rows)}")
    payload: dict[str, Any] = {}
    for name in table.colnames:
        value = rows[0][name]
        if np.ma.is_masked(value):
            payload[name] = None
            continue
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, bytes):
            value = value.decode()
        if isinstance(value, float) and not math.isfinite(value):
            value = None
        payload[name] = value
    return payload


def temporal_row_receipt_path(trig: str) -> Path:
    return SWEEP / trig / f"{trig}_temporal_catalog_row.source.json"


def record_temporal_row_receipt(
    trig: str, not_before_ns: int, input_fingerprint: str
) -> dict[str, Any]:
    require_fresh(TEMPORAL_CATALOG, "fresh temporal catalog", not_before_ns)
    payload = temporal_row_payload(trig)
    receipt = {
        "schema_version": TEMPORAL_ROW_SCHEMA,
        "trigger": trig,
        "generated_utc": utcnow(),
        "source_catalog": str(TEMPORAL_CATALOG),
        "source_catalog_sha256_at_generation": sha256(TEMPORAL_CATALOG),
        "row": payload,
        "row_sha256": object_sha256(payload),
        "input_fingerprint": input_fingerprint,
        "script": str(REPO / "scripts" / "46_temporal_all106.py"),
        "script_sha256": sha256(REPO / "scripts" / "46_temporal_all106.py"),
        "estimator_script": str(REPO / "scripts" / "40_temporal_survey.py"),
        "estimator_script_sha256": sha256(REPO / "scripts" / "40_temporal_survey.py"),
        "pythonhashseed": 0,
    }
    path = temporal_row_receipt_path(trig)
    atomic_json(path, receipt)
    return {**receipt, "receipt": artifact(path)}


def validate_temporal_row_receipt(trig: str) -> dict[str, Any]:
    path = temporal_row_receipt_path(trig)
    receipt = read_json(path, "temporal-row source receipt")
    payload = temporal_row_payload(trig)
    if receipt.get("schema_version") != TEMPORAL_ROW_SCHEMA \
            or receipt.get("trigger") != trig \
            or receipt.get("source_catalog") != str(TEMPORAL_CATALOG) \
            or receipt.get("row") != payload \
            or receipt.get("row_sha256") != object_sha256(payload):
        raise ValidationError(f"{trig}: temporal-row receipt is stale or malformed")
    if receipt.get("script_sha256") != sha256(REPO / "scripts" / "46_temporal_all106.py") \
            or receipt.get("estimator_script_sha256") != sha256(
                REPO / "scripts" / "40_temporal_survey.py"
            ) or receipt.get("pythonhashseed") != 0:
        raise ValidationError(f"{trig}: temporal-row producer identity is stale")
    return artifact(path)


def temporal_row(
    trig: str, *, require_receipt: bool = True
) -> tuple[dict[str, Any], dict[str, Any]]:
    from astropy.table import Table
    import numpy as np

    path = TEMPORAL_CATALOG
    require_file(path, "temporal catalog")
    table = Table.read(path, format="ascii.ecsv")
    rows = table[[str(v).strip() == trig for v in table["TRIGGER_NAME"]]]
    if len(rows) != 1:
        raise ValidationError(f"expected one temporal row for {trig}; found {len(rows)}")
    row = rows[0]
    ref = str(row["REF_DET"]).strip()
    if not ref or not finite(row["T90"]):
        raise ValidationError(f"{trig}: temporal row lacks REF_DET or finite T90")
    t90 = float(row["T90"])
    t1, t2 = float(row["T90_START"]), float(row["T90_STOP"])
    if not (t90 > 0 and finite(t1) and finite(t2) and t2 > t1):
        raise ValidationError(f"{trig}: invalid T90 interval/value")
    if ref != approved_reference_detector(trig):
        raise ValidationError(
            f"{trig}: temporal REF_DET {ref} is not the approved minimum-angle NaI"
        )
    t90_err = optional_float(row["T90_ERR"])
    t90_lo = optional_float(row["T90_ERR_LO"])
    t90_hi = optional_float(row["T90_ERR_HI"])
    if t90_err is None or not (0 < t90_err < t90):
        raise ValidationError(f"{trig}: T90_ERR must be positive and smaller than T90")
    if t90_lo is None or t90_hi is None or t90_lo < 0 or t90_hi < 0:
        raise ValidationError(f"{trig}: asymmetric T90 errors are missing or negative")
    bin_s = float(row["BIN_MS"]) / 1000.0
    if not finite(bin_s) or bin_s <= 0:
        raise ValidationError(f"{trig}: invalid temporal bin size")
    if not math.isclose(t90, t2 - t1, rel_tol=0.0,
                        abs_tol=max(1e-9, bin_s * 1e-6)):
        raise ValidationError(f"{trig}: T90 differs from T90_STOP-T90_START")
    tail_sig = optional_float(row["TAIL_OUTSIDE_WINDOW_SIG"])
    truncated = truthy(row["T90_WINDOW_TRUNCATED"])
    lower = truncated or (
        tail_sig is not None and tail_sig >= 3.0
    )
    lower_reasons = []
    if truncated:
        lower_reasons.append("t5/t95 reached the approved source-window edge")
    if tail_sig is not None and tail_sig >= 3.0:
        lower_reasons.append(
            f"TAIL_OUTSIDE_WINDOW_SIG={tail_sig:.6g} >= 3"
        )
    src = approved_window(trig, ref)
    tolerance = bin_s * 1.01
    if t1 < src["src_start_s"] - tolerance or t2 > src["src_stop_s"] + tolerance:
        raise ValidationError(f"{trig}: T90 interval lies outside the approved source window")
    block_start, block_stop = block_window(trig, ref)
    block_span = block_stop - block_start
    span_ratio = max(t90 / block_span, block_span / t90)
    if span_ratio > 2.0:
        raise ValidationError(
            f"{trig}: T90/block-span sanity ratio {span_ratio:.3g} exceeds 2"
        )
    t90_out = {
        "estimator_label": T90_LABEL,
        "t90_s": t90,
        "t90_err_s": t90_err,
        "t90_err_lo_s": t90_lo,
        "t90_err_hi_s": t90_hi,
        "t90_start_s": t1,
        "t90_stop_s": t2,
        "ref_detector": ref,
        "band_keV": [8.0, 900.0],
        "bin_ms": float(row["BIN_MS"]),
        "approved_src_window_s": [src["src_start_s"], src["src_stop_s"]],
        "adopted_block_window_s": [block_start, block_stop],
        "t90_to_block_span_sanity_ratio": span_ratio,
        "lower_limit": lower,
        "lower_limit_reason": "; ".join(lower_reasons) if lower else None,
        "t90_window_truncated": truncated,
        "tail_outside_window_counts": optional_float(row["TAIL_OUTSIDE_WINDOW_CTS"]),
        "tail_outside_window_sigma": tail_sig,
        "tail_outside_window_interval_s": [
            src["src_stop_s"], src["bkg_pos_start_s"]
        ],
    }
    # Repair-aware (phase 7, PI ruling 5): once row_repair has run, MVT_S/
    # MVT_ERR_S/MVT_TYPE carry the CANONICAL (Bala) values and the original
    # in-chain Haar is preserved in MVT_HAAR_*.  The haar block below must
    # keep describing the HAAR estimator (the 47b figure cross-check depends
    # on it), so read from the preserved columns when the row is repaired.
    repaired = ("MVT_ESTIMATOR" in table.colnames
                and str(row["MVT_ESTIMATOR"]).strip() != ""
                and not np.ma.is_masked(row["MVT_ESTIMATOR"]))
    h_s, h_e, h_t = (("MVT_HAAR_S", "MVT_HAAR_ERR_S", "MVT_HAAR_TYPE")
                     if repaired else ("MVT_S", "MVT_ERR_S", "MVT_TYPE"))
    mvt_type = str(row[h_t]).strip().lower()
    if mvt_type not in {"detection", "limit"}:
        raise ValidationError(f"{trig}: invalid Haar MVT type {mvt_type!r}")
    haar_value = optional_float(row[h_s])
    if haar_value is None or haar_value <= 0:
        raise ValidationError(f"{trig}: invalid Haar MVT")
    is_limit = mvt_type == "limit"
    haar_err = None if is_limit else optional_float(row[h_e])
    if not is_limit and (haar_err is None or haar_err <= 0):
        raise ValidationError(f"{trig}: Haar detection lacks positive uncertainty")
    haar = {
        "estimator_label": HAAR_LABEL,
        "mvt_s": haar_value,
        "mvt_err_s": haar_err,
        "type": mvt_type,
        "upper_limit": is_limit,
        "limit_relation": "<" if is_limit else None,
        "band_keV": [8.0, 900.0],
        "display": f"< {haar_value:.9g} s" if is_limit else (
            f"{haar_value:.9g} ± {haar_err:.9g} s" if haar_err is not None
            else f"{haar_value:.9g} s (uncertainty unavailable)"
        ),
    }
    source = validate_temporal_row_receipt(trig) if require_receipt else artifact(path)
    return {"t90": t90_out, "haar": haar}, source


def validate_cwt(trig: str) -> tuple[dict[str, Any], dict[str, Any]]:
    path = REPO / "results" / "mvt_cwt" / f"{trig}_mvt_cwt.json"
    value = read_json(path, "CWT result")
    if value.get("trig") != trig:
        raise ValidationError(f"CWT trigger mismatch: {value.get('trig')} != {trig}")
    if value.get("script_sha256") != sha256(
        REPO / "scripts" / "47_mvt_cwt_crosscheck.py"
    ):
        raise ValidationError(f"{trig}: CWT result was not made by current scripts/47")
    mvt, err = optional_float(value.get("mvt_cwt_s")), optional_float(value.get("mvt_cwt_err_s"))
    # AMENDMENT 2026-08-27 (paper recovery; PRESENTED for PI review, not yet
    # approved): a COMPLETED CWT scan with no finite crossing is an honest
    # estimator REFUSAL, not an invalid product (campaign precedent: burst #4
    # "no finite crossing"; 3/25 existing products are this class, incl.
    # bn090530760 which already has a paper). Refusal is carried first-class:
    # mvt_s=None + cwt_refused=True; downstream receipts/figures must LABEL
    # the absence (Temporal.md refusal doctrine), never invent a value.
    cwt_refused = (mvt is None and err is None
                   and optional_float(value.get("n_sim")) == 10000
                   and optional_float(value.get("alpha1")) is not None)
    if cwt_refused:
        mvt = err = None
    elif mvt is None or err is None or mvt <= 0 or err <= 0:
        raise ValidationError(f"{trig}: invalid CWT MVT/error")
    detector = str(value.get("detector", "")).strip()
    if detector != approved_reference_detector(trig):
        raise ValidationError(f"{trig}: CWT detector {detector!r} is not the approved reference NaI")
    try:
        band = [float(item) for item in value.get("band_keV", [])]
        window = [float(item) for item in value.get("window_s", [])]
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{trig}: malformed CWT band/window") from exc
    expected_window = list(block_window(trig, detector))
    if band != [8.0, 900.0] or len(window) != 2 or any(
        not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-6)
        for observed, expected in zip(window, expected_window)
    ):
        raise ValidationError(f"{trig}: CWT band or adopted-block window mismatch")
    fixed = {
        "dt_s": 0.004, "dj": 0.25, "max_scale_s": 1.0,
        "n_sim": 10000, "noise_percentile": 99.5,
    }
    for key, expected in fixed.items():
        observed = optional_float(value.get(key))
        if observed is None or not math.isclose(
            observed, float(expected), rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValidationError(f"{trig}: CWT {key}={value.get(key)!r}, expected {expected}")
    if "canon = Bala" not in str(value.get("role", "")):
        raise ValidationError(f"{trig}: CWT sidecar does not identify Bala as canonical")
    out = {
        "estimator_label": CWT_LABEL,
        "mvt_s": mvt,
        "mvt_err_s": err,
        "cwt_refused": bool(cwt_refused),
        "detector": detector,
        "band_keV": band,
        "window_s": window,
        "dt_s": value.get("dt_s"),
        "dj": value.get("dj"),
        "max_scale_s": value.get("max_scale_s"),
        "n_simulations": value.get("n_sim"),
        "noise_percentile": value.get("noise_percentile"),
        "role": value.get("role"),
    }
    return out, artifact(path)


def validate_bala(trig: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    base = MVT_ROOT / trig
    path = base / "result.json"
    value = read_json(path, "Bala result")
    if value.get("trigger") != trig or value.get("engine") != "mvtfermi_upstream":
        raise ValidationError(f"{trig}: Bala trigger/engine mismatch")
    if value.get("status") not in {"detection", "limit"}:
        raise ValidationError(f"{trig}: invalid Bala status {value.get('status')!r}")
    if not value.get("identity"):
        raise ValidationError(f"{trig}: Bala result has no identity")
    engine = mvt_engine_module()
    snapshot = engine.snapshot_from_catalog(str(APPROVED_CATALOG), trig)
    settings = engine.MVTSettings(seed=20260718, cores=1)
    config = engine.build_config(snapshot, str(base), settings)
    catalog_sha = sha256(APPROVED_CATALOG)
    expected_identity = engine._identity(
        trig, snapshot, config, settings, catalog_sha,
        str(REPO / "data"), str(MVT_PYTHON),
    )
    if value.get("identity") != expected_identity:
        raise ValidationError(
            f"{trig}: Bala result identity is stale for current catalog/TTE/code/env"
        )
    if value.get("snapshot") != snapshot or value.get("config") != config:
        raise ValidationError(f"{trig}: Bala snapshot/config differs from live engine inputs")
    mvt, delta = optional_float(value.get("mvt_s")), optional_float(value.get("delta_s"))
    if mvt is None or delta is None or mvt <= 0 or delta <= 0:
        raise ValidationError(f"{trig}: Bala result lacks positive mvt_s/delta_s")
    interval = [optional_float(value.get("interval_start_s")),
                optional_float(value.get("interval_stop_s"))]
    if None in interval or interval[1] <= interval[0]:
        raise ValidationError(f"{trig}: invalid Bala selected interval")
    if not math.isclose(interval[1] - interval[0], delta,
                        rel_tol=0.0, abs_tol=1e-9):
        raise ValidationError(f"{trig}: Bala interval length differs from engine delta_s")
    summary_csv = Path(str(value.get("artifacts", {}).get("summary_csv", "")))
    expected_summary = (
        base / "upstream" / f"BN{trig[2:]}_MVT" / f"BN{trig[2:]}_MVT.csv"
    )
    if summary_csv.resolve() != expected_summary.resolve():
        raise ValidationError(f"{trig}: Bala summary CSV path escapes canonical burst output")
    worker = base / "worker_return.json"
    manifest_path = base / "staging_manifest.json"
    approval_path = base / "approval_snapshot.json"
    config_path = base / "config_MVT_fermi.yaml"
    require_file(summary_csv, "Bala summary CSV")
    require_file(worker, "Bala worker return")
    manifest = read_json(manifest_path, "Bala staging manifest")
    require_file(approval_path, "Bala approval snapshot")
    require_file(config_path, "Bala config")
    expected_fingerprint = engine.fingerprint(
        snapshot, config, manifest, settings, catalog_sha
    )
    provenance = value.get("provenance", {})
    if provenance.get("seed") != 20260718:
        raise ValidationError(f"{trig}: Bala seed is {provenance.get('seed')}, expected 20260718")
    if provenance.get("catalog_sha256") != catalog_sha \
            or provenance.get("fingerprint") != expected_fingerprint:
        raise ValidationError(f"{trig}: Bala provenance fingerprint is stale")
    if list(value.get("detectors", [])) != list(snapshot["nai"]):
        raise ValidationError(f"{trig}: Bala detector set differs from approved NaIs")
    err = optional_float(value.get("mvt_err_s"))
    if value["status"] == "detection" and (err is None or err <= 0):
        raise ValidationError(f"{trig}: Bala detection lacks a positive uncertainty")
    if value["status"] == "detection" and value.get("limit_relation") is not None:
        raise ValidationError(f"{trig}: Bala detection carries a limit relation")
    if value["status"] == "limit" and value.get("limit_relation") != ">":
        raise ValidationError(f"{trig}: Bala limit does not preserve engine relation '>'")
    significance = optional_float(value.get("significance"))
    if significance is None:
        raise ValidationError(f"{trig}: Bala result lacks finite selection significance")
    out = {
        "estimator_label": BALA_LABEL,
        "mvt_s": mvt,
        "mvt_err_s": err,
        "delta_s": delta,
        "interval_s": interval,
        "band_keV": [float(config["en_lo"]), float(config["en_hi"])],
        "status": value["status"],
        "limit_relation": value.get("limit_relation"),
        "significance": significance,
        "significance_label": (
            "engine selection weighted-mean statistic; not a Gaussian z-score"
        ),
        "detectors": list(value.get("detectors", [])),
        "diagnostics": value.get("diagnostics", {}),
        "seed": provenance.get("seed"),
        "fingerprint": provenance.get("fingerprint"),
        "approval": {
            "approved_by": provenance.get("approved_by"),
            "approved_utc": provenance.get("approved_utc"),
            "approval_mode": provenance.get("approval_mode"),
        },
    }
    return out, [
        artifact(path), artifact(summary_csv), artifact(worker),
        artifact(manifest_path), artifact(approval_path), artifact(config_path),
    ]


def validate_lag(trig: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = SWEEP / trig
    path = root / f"{trig}_step7_lag_latbright.json"
    figure = root / f"{trig}_step7_lag_latbright.png"
    value = read_json(path, "validated lag result")
    if value.get("trig") != trig:
        raise ValidationError(f"{trig}: lag trigger mismatch")
    if value.get("script_sha256") != sha256(
        REPO / "scripts" / "47c_lag_latbright.py"
    ):
        raise ValidationError(f"{trig}: lag result was not made by current scripts/47c")
    detector = str(value.get("detector", "")).strip()
    if detector != approved_reference_detector(trig):
        raise ValidationError(f"{trig}: lag detector {detector!r} is not the approved reference NaI")
    if [float(x) for x in value.get("soft_keV", [])] != [25.0, 50.0] or \
       [float(x) for x in value.get("hard_keV", [])] != [100.0, 300.0]:
        raise ValidationError(f"{trig}: lag bands are not 25–50/100–300 keV")
    convention = str(value.get("convention", ""))
    if "POSITIVE" not in convention or "soft lags hard" not in convention:
        raise ValidationError(f"{trig}: lag convention absent or wrong")
    tau = optional_float(value.get("tau_s"))
    sl = optional_float(value.get("sigma_l_s"))
    sr = optional_float(value.get("sigma_r_s"))
    if tau is None or sl is None or sr is None or sl <= 0 or sr <= 0:
        raise ValidationError(f"{trig}: invalid lag value/errors")
    windows = value.get("windows", {})
    scans = [float(x) for x in windows.get("scan_taus_s", [])]
    scan_halves = [float(x) for x in windows.get("scan_halves_s", [])]
    sys_win = optional_float(windows.get("window_systematic_s"))
    if len(scans) < 2 or len(scan_halves) != len(scans) or sys_win is None:
        raise ValidationError(f"{trig}: lag scan/systematic missing")
    if not all(finite(item) for item in scans + scan_halves) \
            or not all(item > 0 for item in scan_halves):
        raise ValidationError(f"{trig}: lag scan contains non-finite or invalid entries")
    expected = 0.5 * (max(scans) - min(scans))
    if not math.isclose(sys_win, expected, rel_tol=0.0, abs_tol=1e-9):
        raise ValidationError(f"{trig}: lag window systematic {sys_win} != {expected}")
    src = approved_window(trig, detector)
    span = src["src_stop_s"] - src["src_start_s"]
    expected_analysis = [src["src_start_s"] - 2.0, src["src_stop_s"] + 2.0]
    observed_analysis = [float(item) for item in value.get("window_s", [])]
    if len(observed_analysis) != 2 or any(
        not math.isclose(left, right, rel_tol=0.0, abs_tol=1e-9)
        for left, right in zip(observed_analysis, expected_analysis)
    ):
        raise ValidationError(f"{trig}: lag analysis window is not approved SRC +/- 2 s")
    expected_search = max(2.0, span / 4.0)
    search_half = optional_float(windows.get("search_half_s"))
    fit_half = optional_float(windows.get("fit_half_s"))
    expected_halves = sorted({
        round(max(0.5, span / divisor), 2) for divisor in (16, 8, 6, 4)
    })
    expected_halves = [item for item in expected_halves if item <= expected_search] \
        or [max(0.5, span / 8.0)]
    if search_half is None or fit_half is None \
            or not math.isclose(search_half, expected_search, rel_tol=0.0, abs_tol=1e-12) \
            or len(scan_halves) != len(expected_halves) \
            or any(not math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)
                   for left, right in zip(scan_halves, expected_halves)):
        raise ValidationError(f"{trig}: lag scan windows differ from pulse-scaled defaults")
    median_tau = statistics.median(scans)
    candidates = [
        index for index, half in enumerate(scan_halves)
        if half >= max(0.5, span / 8.0)
    ] or list(range(len(scans)))
    chosen = min(candidates, key=lambda index: abs(scans[index] - median_tau))
    if not math.isclose(fit_half, scan_halves[chosen], rel_tol=0.0, abs_tol=1e-12) \
            or not math.isclose(tau, scans[chosen], rel_tol=0.0, abs_tol=1e-9):
        raise ValidationError(f"{trig}: lag headline is not the engine's scan-median choice")
    if not math.isclose(optional_float(value.get("dt_s")) or -1.0, 0.016,
                        rel_tol=0.0, abs_tol=1e-12):
        raise ValidationError(f"{trig}: lag time grid is not 16 ms")
    mc = value.get("mc", {})
    if mc.get("n_ccf") != 10000 or mc.get("n_lag") != 1000 \
            or mc.get("seed") != 20260815:
        raise ValidationError(f"{trig}: lag MC counts/seed differ from producer contract")
    out = {
        "estimator_label": LAG_LABEL,
        "tau_s": tau,
        "sigma_l_s": sl,
        "sigma_r_s": sr,
        "window_systematic_s": sys_win,
        "peak_significance_sigma": optional_float(value.get("peak_sig")),
        "dt_s": value.get("dt_s"),
        "analysis_window_s": observed_analysis,
        "search_half_s": search_half,
        "fit_half_s": fit_half,
        "scan_half_widths_s": scan_halves,
        "scan_taus_s": scans,
        "soft_band_keV": [25.0, 50.0],
        "hard_band_keV": [100.0, 300.0],
        "positive_means": "soft photons lag hard photons",
        "mc": {"n_ccf": 10000, "n_lag": 1000, "seed": 20260815},
    }
    return out, [artifact(path), artifact(figure)]


ROW_REPAIR_SCHEMA = "codex_campaign20.temporal_row_repair.v1"
ROW_REPAIR_COLUMNS = ("LAG_CONVENTION", "MVT_ESTIMATOR", "MVT_HAAR_TYPE",
                      "LAG_WINDOW_SYS_S", "MVT_HAAR_S", "MVT_HAAR_ERR_S")


def row_repair_sidecar_path(trig: str) -> Path:
    return SWEEP / trig / f"{trig}_row_repair.json"


def _lag_convention_text(lag: dict[str, Any]) -> str:
    return (
        "scripts/47c (LATBright s02c DCCF, unmodified import): POSITIVE = soft "
        "25-50 keV lags hard 100-300 keV (Norris+1996); LAG_ERR_S = max of the "
        "asymmetric MC errors (stat only); window systematic "
        f"{lag['window_systematic_s']:.6g} s in LAG_WINDOW_SYS_S, NOT folded in; "
        "full detail in the step7_lag_latbright.json sidecar"
    )


def _mvt_estimator_text(bala: dict[str, Any]) -> str:
    return (
        BALA_LABEL + "; seed 20260718; original in-chain Haar preserved in "
        "MVT_HAAR_S/MVT_HAAR_ERR_S/MVT_HAAR_TYPE"
    )


def repair_row(trig: str) -> dict[str, Any]:
    """Phase 7 (PI ruling 5 + repair-step choice, 2026-08-30): REPLACE the
    catalog row's handbook LAG_*/MVT_* with the validated phase-4/6 estimators.

    Fail-closed: values come ONLY through validate_lag / validate_bala.  A Bala
    structural refusal is a TYPED refusal here (the fallback policy for
    Bala-refused bursts is an OPEN PI decision; do not improvise one)."""
    from astropy.table import Table
    import numpy as np

    lag, _lag_sources = validate_lag(trig)
    try:
        bala, _bala_sources = validate_bala(trig)
    except ValidationError as exc:
        raise ValidationError(
            f"{trig}: row_repair requires the canonical Bala result "
            f"(F-STRUCTURAL if Bala refused; fallback policy is an open PI "
            f"decision): {exc}"
        )
    bala_err = optional_float(bala.get("mvt_err_s"))
    bala_status = str(bala.get("status", "")).strip().lower()
    if bala_status == "detection" and (bala_err is None or bala_err <= 0):
        raise ValidationError(f"{trig}: Bala detection lacks positive mvt_err_s")

    require_file(TEMPORAL_CATALOG, "temporal catalog")
    table = Table.read(TEMPORAL_CATALOG, format="ascii.ecsv")
    meta = table.meta.get("stale_pending_rewalk")
    if not isinstance(meta, dict) or "rewalked_triggers" not in meta:
        raise ValidationError(
            "temporal catalog lacks the stale_pending_rewalk header "
            "(PI ruling 5 precondition; see Temporal.md banner)"
        )
    mask = [str(v).strip() == trig for v in table["TRIGGER_NAME"]]
    if sum(mask) != 1:
        raise ValidationError(f"expected one temporal row for {trig}; found {sum(mask)}")
    index = mask.index(True)

    def _set_str(name: str, value: str) -> None:
        # a numpy U<n> column silently TRUNCATES longer assignments; rebuild
        # the column from python strings so the full text survives
        if name in table.colnames:
            values = ["" if np.ma.is_masked(item) else str(item)
                      for item in table[name]]
        else:
            values = [""] * len(table)
        values[index] = value
        if name in table.colnames:
            table.replace_column(name, values)   # keeps column ORDER stable
        else:
            table[name] = values

    for name in ("LAG_WINDOW_SYS_S", "MVT_HAAR_S", "MVT_HAAR_ERR_S"):
        if name not in table.colnames:
            table[name] = np.full(len(table), np.nan)

    row = table[index]
    before = {name: (None if np.ma.is_masked(row[name]) else
                     (row[name].item() if hasattr(row[name], "item") else row[name]))
              for name in ("LAG_S", "LAG_ERR_S", "LAG_SIG", "LAG_ACCEPTED",
                           "MVT_S", "MVT_ERR_S", "MVT_TYPE")}
    already = ("MVT_ESTIMATOR" in table.colnames
               and not np.ma.is_masked(row["MVT_ESTIMATOR"])
               and str(row["MVT_ESTIMATOR"]).strip() != "")
    if not already:
        # first repair: preserve the in-chain Haar before overwriting
        table["MVT_HAAR_S"][index] = float(row["MVT_S"])
        table["MVT_HAAR_ERR_S"][index] = float(row["MVT_ERR_S"])
        _set_str("MVT_HAAR_TYPE", str(row["MVT_TYPE"]).strip())

    table["LAG_S"][index] = float(lag["tau_s"])
    table["LAG_ERR_S"][index] = max(float(lag["sigma_l_s"]), float(lag["sigma_r_s"]))
    peak = optional_float(lag.get("peak_significance_sigma"))
    table["LAG_SIG"][index] = peak if peak is not None else np.nan
    table["LAG_ACCEPTED"][index] = True
    table["LAG_WINDOW_SYS_S"][index] = float(lag["window_systematic_s"])
    _set_str("LAG_CONVENTION", _lag_convention_text(lag))
    table["MVT_S"][index] = float(bala["mvt_s"])
    table["MVT_ERR_S"][index] = bala_err if bala_err is not None else np.nan
    _set_str("MVT_TYPE", bala_status)
    _set_str("MVT_ESTIMATOR", _mvt_estimator_text(bala))

    rewalked = list(meta.get("rewalked_triggers") or [])
    if trig not in rewalked:
        rewalked.append(trig)
    meta["rewalked_triggers"] = sorted(rewalked)
    table.meta["stale_pending_rewalk"] = meta

    temporary = TEMPORAL_CATALOG.with_suffix(".ecsv.tmp")
    table.write(temporary, format="ascii.ecsv", overwrite=True)
    os.replace(temporary, TEMPORAL_CATALOG)

    check = Table.read(TEMPORAL_CATALOG, format="ascii.ecsv")
    if len(check) != len(table) or trig not in (
        check.meta.get("stale_pending_rewalk", {}).get("rewalked_triggers", [])
    ):
        raise ValidationError(f"{trig}: post-repair catalog readback failed")

    after = {name: (table[name][index].item()
                    if hasattr(table[name][index], "item") else table[name][index])
             for name in ("LAG_S", "LAG_ERR_S", "LAG_SIG", "LAG_ACCEPTED",
                          "LAG_WINDOW_SYS_S", "LAG_CONVENTION",
                          "MVT_S", "MVT_ERR_S", "MVT_TYPE", "MVT_ESTIMATOR",
                          "MVT_HAAR_S", "MVT_HAAR_ERR_S", "MVT_HAAR_TYPE")}
    sidecar = {
        "schema_version": ROW_REPAIR_SCHEMA,
        "trigger": trig,
        "generated_utc": utcnow(),
        "argv": list(sys.argv),
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256(Path(__file__).resolve()),
        "ruling": ("PI 2026-08-30 ruling 5 + repair-step choice: REPLACE the "
                   "handbook lag (sign-inverted, L26) and Haar MVT with the "
                   "validated scripts/47c lag and canonical Bala MVT, labelled"),
        "before": before,
        "after": after,
        "lag_source": input_artifact(
            SWEEP / trig / f"{trig}_step7_lag_latbright.json", "validated lag"),
        "bala_source": input_artifact(MVT_ROOT / trig / "result.json", "Bala result"),
        "catalog_sha256_after": sha256(TEMPORAL_CATALOG),
        "rewalked_triggers": meta["rewalked_triggers"],
    }
    atomic_json(row_repair_sidecar_path(trig), sidecar)
    return sidecar


def validate_row_repair(trig: str) -> dict[str, Any]:
    from astropy.table import Table
    import numpy as np

    lag, _ = validate_lag(trig)
    bala, _ = validate_bala(trig)
    sidecar = read_json(row_repair_sidecar_path(trig), "row-repair sidecar")
    if sidecar.get("trigger") != trig \
            or sidecar.get("schema_version") != ROW_REPAIR_SCHEMA:
        raise ValidationError(f"{trig}: row-repair sidecar is malformed")
    if sidecar.get("script_sha256") != sha256(Path(__file__).resolve()):
        raise ValidationError(f"{trig}: row-repair sidecar was made by a stale controller")
    table = Table.read(TEMPORAL_CATALOG, format="ascii.ecsv")
    meta = table.meta.get("stale_pending_rewalk")
    if not isinstance(meta, dict) or trig not in (meta.get("rewalked_triggers") or []):
        raise ValidationError(f"{trig}: not listed in stale_pending_rewalk.rewalked_triggers")
    rows = table[[str(v).strip() == trig for v in table["TRIGGER_NAME"]]]
    if len(rows) != 1:
        raise ValidationError(f"expected one temporal row for {trig}; found {len(rows)}")
    row = rows[0]
    if "POSITIVE = soft" not in str(row["LAG_CONVENTION"]) \
            or "Bala" not in str(row["MVT_ESTIMATOR"]):
        raise ValidationError(f"{trig}: repaired row lacks estimator labels")
    if not math.isclose(float(row["LAG_S"]), float(lag["tau_s"]),
                        rel_tol=0.0, abs_tol=1e-9):
        raise ValidationError(f"{trig}: row LAG_S differs from the validated 47c lag")
    expected_err = max(float(lag["sigma_l_s"]), float(lag["sigma_r_s"]))
    if not math.isclose(float(row["LAG_ERR_S"]), expected_err,
                        rel_tol=0.0, abs_tol=1e-9):
        raise ValidationError(f"{trig}: row LAG_ERR_S differs from max(sigma_l, sigma_r)")
    if not math.isclose(float(row["LAG_WINDOW_SYS_S"]),
                        float(lag["window_systematic_s"]),
                        rel_tol=0.0, abs_tol=1e-9):
        raise ValidationError(f"{trig}: row LAG_WINDOW_SYS_S differs from the 47c scan")
    if not math.isclose(float(row["MVT_S"]), float(bala["mvt_s"]),
                        rel_tol=0.0, abs_tol=1e-9):
        raise ValidationError(f"{trig}: row MVT_S differs from the canonical Bala value")
    if str(row["MVT_TYPE"]).strip().lower() != str(bala.get("status", "")).strip().lower():
        raise ValidationError(f"{trig}: row MVT_TYPE differs from the Bala status")
    haar_type = str(row["MVT_HAAR_TYPE"]).strip().lower()
    haar_value = optional_float(row["MVT_HAAR_S"])
    if haar_type not in {"detection", "limit"} or haar_value is None or haar_value <= 0:
        raise ValidationError(f"{trig}: preserved Haar columns are invalid")
    validate_temporal_row_receipt(trig)
    return {
        "lag_s": float(row["LAG_S"]),
        "lag_err_s": float(row["LAG_ERR_S"]),
        "lag_window_sys_s": float(row["LAG_WINDOW_SYS_S"]),
        "lag_convention": str(row["LAG_CONVENTION"]),
        "mvt_s": float(row["MVT_S"]),
        "mvt_type": str(row["MVT_TYPE"]),
        "mvt_estimator": str(row["MVT_ESTIMATOR"]),
        "haar_preserved": {"mvt_s": haar_value,
                           "mvt_err_s": optional_float(row["MVT_HAAR_ERR_S"]),
                           "type": haar_type},
        "sidecar": artifact(row_repair_sidecar_path(trig)),
    }


def _close(left: Any, right: Any, tolerance: float = 1e-9) -> bool:
    return finite(left) and finite(right) and math.isclose(
        float(left), float(right), rel_tol=0.0, abs_tol=tolerance
    )


def validate_temporal_figures(
    trig: str, bala: dict[str, Any], cwt: dict[str, Any], haar: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = SWEEP / trig
    sidecar = root / f"{trig}_step7_figs.json"
    value = read_json(sidecar, "temporal-figure sidecar")
    if value.get("trig") != trig:
        raise ValidationError(f"{trig}: temporal-figure trigger mismatch")
    if str(value.get("detector", "")).strip() != approved_reference_detector(trig):
        raise ValidationError(f"{trig}: temporal figures use the wrong reference NaI")
    expected_sha = sha256(REPO / "scripts" / "47b_temporal_figs.py")
    if value.get("script_sha256") != expected_sha:
        raise ValidationError(f"{trig}: temporal figures were not made by current scripts/47b")
    expected_names = [f"{trig}_{suffix}.png" for suffix in STEP47B_FIGURES]
    if value.get("figures") != expected_names:
        raise ValidationError(f"{trig}: expected exactly three 47b figures")
    estimators = value.get("mvt", {}).get("estimators", [])
    if len(estimators) != 3:
        raise ValidationError(f"{trig}: expected exactly three MVT estimator entries")
    expected_values = [bala["mvt_s"], cwt["mvt_s"], haar["mvt_s"]]
    expected_words = ["Bala", "CWT", "Haar"]
    for index, (entry, target, word) in enumerate(zip(estimators, expected_values,
                                                      expected_words)):
        if word not in str(entry.get("label", "")) or not _close(entry.get("value_s"), target):
            raise ValidationError(f"{trig}: 47b estimator {index} is not current {word}")
    expected_errors = [bala["mvt_err_s"], cwt["mvt_err_s"], haar["mvt_err_s"]]
    for index, (entry, target) in enumerate(zip(estimators, expected_errors)):
        observed = entry.get("err_s")
        if target is None:
            if observed is not None and finite(observed):
                raise ValidationError(f"{trig}: 47b estimator {index} has an unexpected error")
        elif not _close(observed, target):
            raise ValidationError(f"{trig}: 47b estimator {index} error is stale")
    if bool(estimators[2].get("upper_limit")) != bool(haar["upper_limit"]):
        raise ValidationError(f"{trig}: 47b Haar limit flag mismatch")
    gowri = value.get("gowri", {})
    if value.get("best_pulse") not in {"norris", "kocevski", "gowri"}:
        raise ValidationError(f"{trig}: 47b sidecar lacks a recognized best pulse model")
    r2 = optional_float(gowri.get("r2"))
    phi = optional_float(gowri.get("phi"))
    r2_pass = bool(r2 is not None and r2 >= 0.7)
    if bool(gowri.get("r2_pass")) != r2_pass:
        raise ValidationError(f"{trig}: 47b Gowri R2 pass flag is inconsistent")
    if phi is not None and phi <= 0:
        raise ValidationError(f"{trig}: 47b Gowri phi is not physically valid")
    quote_phi = r2_pass and phi is not None
    out = {
        "best_pulse_model": value.get("best_pulse"),
        "gowri": {
            "phi_raw": phi,
            "phi_err_raw": optional_float(gowri.get("phi_err")),
            "phi_class": gowri.get("phi_class"),
            "r2": r2,
            "r2_pass": r2_pass,
            "quote_phi": quote_phi,
            "reported_phi": phi if quote_phi else None,
            "reporting_rule": "quote phi only when Gowri R2 >= 0.7",
        },
    }
    products = [artifact(sidecar)] + [artifact(root / name) for name in expected_names]
    return out, products


def record_step44_nonspectral(trig: str, not_before_ns: int) -> dict[str, Any]:
    """Bind the five non-spectral scripts/44 figures to this exact run."""
    root = SWEEP / trig
    products = []
    for suffix in STEP44_NONSPECTRAL_FIGURES:
        path = require_fresh(
            root / f"{trig}_{suffix}.png",
            f"fresh scripts/44 {suffix}", not_before_ns,
        )
        products.append({**artifact(path), "mtime_ns": path.stat().st_mtime_ns})
    receipt = {
        "schema_version": STEP44_BASE_SCHEMA,
        "trigger": trig,
        "generated_utc": utcnow(),
        "script": str(REPO / "scripts" / "44_step_figures.py"),
        "script_sha256": sha256(REPO / "scripts" / "44_step_figures.py"),
        "command": [
            str(PYTHON), str(REPO / "scripts" / "44_step_figures.py"),
            "--trig", trig,
        ],
        "invocation_not_before_ns": not_before_ns,
        "artifacts": products,
        "figure_gate_status": GATE_STATUS,
        "verifier": None,
    }
    path = root / f"{trig}_step44_nonspectral.source.json"
    atomic_json(path, receipt)
    return {**receipt, "receipt": artifact(path)}


def validate_step44_nonspectral(trig: str) -> list[dict[str, Any]]:
    """Validate fresh non-spectral step figures without requiring a P1 fit."""
    root = SWEEP / trig
    path = root / f"{trig}_step44_nonspectral.source.json"
    receipt = read_json(path, "non-spectral step-figure source sidecar")
    if receipt.get("schema_version") != STEP44_BASE_SCHEMA \
            or receipt.get("trigger") != trig:
        raise ValidationError(f"{trig}: malformed non-spectral step-figure sidecar")
    script = REPO / "scripts" / "44_step_figures.py"
    if receipt.get("script_sha256") != sha256(script):
        raise ValidationError(f"{trig}: non-spectral step figures use stale scripts/44")
    expected_command = [str(PYTHON), str(script), "--trig", trig]
    if receipt.get("command") != expected_command:
        raise ValidationError(f"{trig}: non-spectral step-figure command mismatch")
    if receipt.get("figure_gate_status") != GATE_STATUS:
        raise ValidationError(f"{trig}: non-spectral figure gate is not UNGATED")
    expected_paths = [
        root / f"{trig}_{suffix}.png" for suffix in STEP44_NONSPECTRAL_FIGURES
    ]
    recorded = receipt.get("artifacts", [])
    if len(recorded) != len(expected_paths):
        raise ValidationError(f"{trig}: non-spectral artifact count mismatch")
    products: list[dict[str, Any]] = []
    for expected, entry in zip(expected_paths, recorded):
        current = artifact(expected)
        if entry.get("path") != str(expected) or entry.get("sha256") != current["sha256"] \
                or entry.get("bytes") != current["bytes"] \
                or entry.get("mtime_ns") != expected.stat().st_mtime_ns \
                or entry.get("mtime_ns", -1) < receipt.get("invocation_not_before_ns", 0):
            raise ValidationError(
                f"{trig}: non-spectral figure differs from source sidecar: {expected.name}"
            )
        products.append(current)
    products.append(artifact(path))
    return products


def validate_step44(trig: str) -> list[dict[str, Any]]:
    root = SWEEP / trig
    products = validate_step44_nonspectral(trig)
    source_path = root / f"{trig}_step9_qc.source.json"
    source = read_json(source_path, "current-fit step9 source sidecar")
    fit = validate_current_fit(trig)
    step9 = root / f"{trig}_step9_qc.png"
    if source.get("schema_version") != STEP9_SCHEMA or source.get("trigger") != trig:
        raise ValidationError(f"{trig}: malformed step9 source sidecar")
    if source.get("source_fit_sha256") != sha256(require_file(fit, "current fit")):
        raise ValidationError(f"{trig}: step9 is not bound to the current fit table")
    if source.get("source_fit") != str(fit):
        raise ValidationError(f"{trig}: step9 source path is not canonical convention_check")
    blocks = require_file(blocks_path(trig), "adopted blocks")
    if source.get("source_blocks") != str(blocks) \
            or source.get("source_blocks_sha256") != sha256(blocks):
        raise ValidationError(f"{trig}: step9 is not bound to the adopted blocks")
    script = REPO / "scripts" / "44_step_figures.py"
    if source.get("script_sha256") != sha256(script):
        raise ValidationError(f"{trig}: step9 was not rendered by current scripts/44")
    if source.get("output_sha256") != sha256(step9):
        raise ValidationError(f"{trig}: step9 PNG hash differs from its source sidecar")
    if source.get("output") != str(step9):
        raise ValidationError(f"{trig}: step9 output path differs from its source sidecar")
    if source.get("figure_gate_status") != GATE_STATUS:
        raise ValidationError(f"{trig}: step9 gate status is not UNGATED")
    products.append(artifact(step9))
    products.append(artifact(source_path))
    return products


def validate_current_fit(trig: str) -> Path:
    """Require the promoted P1 table, never the legacy nested sweep table."""
    from astropy.table import Table

    path = require_file(FIT_ROOT / trig / "spectral_fits.ecsv",
                        "current convention-check fit")
    table = Table.read(path, format="ascii.ecsv")
    prefixes = [name[:-4] for name in table.colnames if name.endswith("_AIC")]
    if len(prefixes) != 24 or len(set(prefixes)) != 24:
        raise ValidationError(
            f"{trig}: current convention-check fit has {len(set(prefixes))} models, expected 24"
        )
    blocks = sorted(int(value) for value in table["BLOCK"])
    if not blocks or blocks[0] != -1 or blocks != list(range(-1, max(blocks) + 1)):
        raise ValidationError(f"{trig}: current fit block rows are incomplete: {blocks}")
    return path


def validate_phase_statuses(
    trig: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Require current invocation receipts before any estimator can be quoted."""
    products: list[dict[str, Any]] = []
    declared_partial: list[str] = []
    controller_sha = sha256(Path(__file__).resolve())
    for phase in phases(trig):
        path = LOG_ROOT / trig / f"{phase.number:02d}_{phase.name}.status.json"
        status = read_json(path, f"P2 phase-{phase.number} status")
        current_manifest = phase_input_manifest(trig, phase)
        current_input = object_sha256(current_manifest)
        structural = (
            status.get("schema_version") == PHASE_SCHEMA,
            status.get("trigger") == trig,
            status.get("phase_number") == phase.number,
            status.get("phase") == phase.name,
            status.get("command") == list(phase.command),
            status.get("cwd") == str(phase.cwd),
            status.get("implementation_sha256") == phase_implementation_sha(phase),
            status.get("controller_sha256") == controller_sha,
            status.get("threadpool_transport_shim") == phase.thread_shim,
            status.get("pythonhashseed") == 0,
            status.get("input_fingerprint") == current_input,
            object_sha256(status.get("input_manifest")) == current_input,
            status.get("return_code") == 0,
        )
        if not all(structural):
            raise ValidationError(
                f"{trig}: phase {phase.number} status is stale or does not bind current inputs"
            )
        errors = status.get("validation_errors") or []
        if status.get("state") == "COMPLETE":
            if errors:
                raise ValidationError(
                    f"{trig}: COMPLETE phase {phase.number} carries validation errors"
                )
        elif phase.name == "step_figures" and trig in RESPONSE_BLOCKED:
            if not errors or any(
                not (
                    str(item).startswith("step9 current-fit supplement:")
                    or str(item).startswith("validation:")
                )
                for item in errors
            ) or any(
                "current" not in str(item).lower() and "step9" not in str(item).lower()
                for item in errors
            ):
                raise ValidationError(
                    f"{trig}: response-blocked phase-2 failure contains non-step9 errors"
                )
            validate_step44_nonspectral(trig)
            declared_partial.append(
                RESPONSE_BLOCKED[trig] + "; current-fit step9 unavailable"
            )
        else:
            raise ValidationError(
                f"{trig}: phase {phase.number} is {status.get('state')}, not COMPLETE"
            )
        if phase.name == "row_repair":
            # phase 7 is the last row writer; the standing receipt must carry
            # ITS input fingerprint (phase 1's receipt is superseded).
            receipt = read_json(
                temporal_row_receipt_path(trig), "temporal-row source receipt"
            )
            if receipt.get("input_fingerprint") != current_input:
                raise ValidationError(f"{trig}: temporal-row receipt input is stale")
            validate_temporal_row_receipt(trig)
        products.append(artifact(path))
    return products, declared_partial


def collect_summary(trig: str) -> dict[str, Any]:
    phase_sources, phase_errors = validate_phase_statuses(trig)
    temporal, temporal_source = temporal_row(trig)
    cwt, cwt_source = validate_cwt(trig)
    bala, bala_sources = validate_bala(trig)
    lag, lag_sources = validate_lag(trig)
    repaired_row = validate_row_repair(trig)
    pulse, fig_sources = validate_temporal_figures(
        trig, bala=bala, cwt=cwt, haar=temporal["haar"]
    )
    # Step-9 is bound to the promoted P1 table.  A burst can have valid timing
    # estimators even when spectroscopy is structurally unavailable (campaign
    # burst #12 is RESPONSE_UNCOVERED).  Preserve those validated measurements
    # in an explicitly incomplete summary instead of discarding them wholesale.
    step_errors: list[str] = list(phase_errors)
    try:
        step_sources = validate_step44(trig)
    except Exception as exc:
        try:
            step_sources = validate_step44_nonspectral(trig)
        except Exception as base_exc:
            step_sources = []
            step_errors.append(
                f"non-spectral step figures: {type(base_exc).__name__}: {base_exc}"
            )
        step_errors.append(
            f"step/QC figures: {type(exc).__name__}: {exc}"
        )
    sources = phase_sources + [temporal_source, cwt_source] + bala_sources \
        + lag_sources + fig_sources + step_sources
    return {
        "schema_version": SCHEMA,
        "trigger": trig,
        "generated_utc": utcnow(),
        "producer": "Codex (AI)",
        "provisional": True,
        "complete": not step_errors,
        "temporal_values_complete": True,
        "validation_errors": step_errors,
        "figure_gate_status": GATE_STATUS,
        "figure_verifier": None,
        "t90": temporal["t90"],
        "mvt": {
            "canonical_bala": bala,
            "noncanonical_cwt": cwt,
            "noncanonical_haar": temporal["haar"],
        },
        "lag": lag,
        "catalog_row_canonical": repaired_row,
        "pulse": pulse,
        "artifacts": sources,
        "reporting_rules": [
            "All values are provisional.",
            "Use only canonical_bala for an unlabeled campaign MVT; in prose, retain its estimator label.",
            "CWT and Haar are noncanonical global cross-checks and must remain labeled.",
            "T90 is windowed; lower_limit=true must be stated wherever T90 is quoted.",
            "Lag must carry both asymmetric statistical errors and the fit-window systematic.",
            "Positive lag means 25–50 keV photons arrive after 100–300 keV photons.",
            "No figure is verified by this producer-side controller.",
            "Catalog LAG_*/MVT_* for this burst were REPLACED by phase 7 "
            "(row_repair) with the validated 47c lag and canonical Bala MVT; "
            "the header's rewalked_triggers lists this trigger (PI ruling 5, "
            "2026-08-30).",
        ],
    }


def partial_summary(trig: str, errors: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "trigger": trig,
        "generated_utc": utcnow(),
        "producer": "Codex (AI)",
        "provisional": True,
        "complete": False,
        "temporal_values_complete": False,
        "figure_gate_status": GATE_STATUS,
        "figure_verifier": None,
        "validation_errors": errors,
        "reporting_rules": [
            "This P2 product is incomplete; missing values must not be inferred or replaced from legacy catalogs.",
            "No figure is verified by this producer-side controller.",
        ],
    }


def base_env(thread_shim: bool) -> dict[str, str]:
    env = os.environ.copy()
    fermi = Path("/Users/salim/anaconda3/envs/threeML/share/fermitools")
    env.update({
        "PYTHONHASHSEED": "0",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "MPLBACKEND": "Agg",
        "PYTHONUNBUFFERED": "1",
        "MPLCONFIGDIR": "/private/tmp/codex_campaign20_mpl/p2",
        "NUMBA_CACHE_DIR": "/private/tmp/codex_campaign20_numba/p2",
        "XDG_CACHE_HOME": "/private/tmp/codex_campaign20_xdg/p2",
        "FERMI_DIR": str(fermi),
        "CALDB": str(fermi / "data" / "caldb"),
        "CALDBCONFIG": str(fermi / "data" / "caldb" / "software" / "tools" / "caldb.config"),
        "CALDBALIAS": str(fermi / "data" / "caldb" / "software" / "tools" / "alias_config.fits"),
        "CALDBROOT": str(fermi / "data" / "caldb"),
        "EXTFILESSYS": str(fermi / "refdata" / "fermi"),
    })
    old = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(RUNTIME) + (os.pathsep + old if old else "")
    if thread_shim:
        env["CODEX_CAMPAIGN20_THREAD_EXECUTOR"] = "1"
    else:
        env.pop("CODEX_CAMPAIGN20_THREAD_EXECUTOR", None)
    return env


@dataclass(frozen=True)
class Phase:
    number: int
    name: str
    command: tuple[str, ...]
    cwd: Path
    thread_shim: bool
    validator: Callable[[str], Any]


def phase_dependency_paths(phase: Phase) -> tuple[Path, ...]:
    scripts = REPO / "scripts"
    mapping = {
        "temporal_catalog": (
            scripts / "46_temporal_all106.py", scripts / "40_temporal_survey.py",
            HANDBOOK_TEMPORAL, RUNTIME / "sitecustomize.py",
        ),
        "step_figures": (
            scripts / "44_step_figures.py", scripts / "40_temporal_survey.py",
        ),
        "cwt": (scripts / "47_mvt_cwt_crosscheck.py",),
        "bala": (
            HANDBOOK / "grb_pipeline" / "pipeline" / "mvt_runner.py",
            HANDBOOK / "grb_pipeline" / "analysis" / "mvt_engine.py",
            HANDBOOK / "grb_pipeline" / "analysis" / "mvt_worker.py",
            HANDBOOK / "requirements-mvt.lock", RUNTIME / "sitecustomize.py",
        ),
        "temporal_figures": (
            scripts / "47b_temporal_figs.py", scripts / "40_temporal_survey.py",
            scripts / "47_mvt_cwt_crosscheck.py", HANDBOOK_TEMPORAL,
        ),
        "lag": (scripts / "47c_lag_latbright.py", LATBRIGHT_LAG),
        "row_repair": (
            RUNTIME / "run_p2_temporal.py",
            scripts / "47c_lag_latbright.py", LATBRIGHT_LAG,
            HANDBOOK / "grb_pipeline" / "analysis" / "mvt_engine.py",
        ),
    }
    return mapping[phase.name]


def phase_implementation_sha(phase: Phase) -> str:
    records = [
        input_artifact(path, f"{phase.name} implementation dependency")
        for path in phase_dependency_paths(phase)
    ]
    return object_sha256(records)


def phase_input_manifest(trig: str, phase: Phase) -> dict[str, Any]:
    rows = approved_rows(trig)
    detectors = sorted({
        str(value).strip() for value in rows["DETECTOR"]
        if str(value).strip().startswith(("n", "b"))
    })
    common: dict[str, Any] = {
        "approved_catalog": input_artifact(APPROVED_CATALOG, "approved catalog"),
        "adopted_blocks": input_artifact(blocks_path(trig), "adopted blocks"),
        "approved_gbm_tte": [
            input_artifact(latest_tte(trig, det), f"{trig} {det} TTE")
            for det in detectors
        ],
    }
    if phase.name == "step_figures":
        response_records = []
        for det in detectors:
            paths = sorted((REPO / "data" / trig).glob(
                f"glg_cspec_{det}_{trig}_v*.rsp*"
            ))
            response_records.extend(
                input_artifact(path, f"{trig} {det} response") for path in paths
            )
        common["responses_seen_by_scripts44"] = response_records
        common["current_fit"] = input_artifact(
            FIT_ROOT / trig / "spectral_fits.ecsv", "current fit", optional=True
        )
    if phase.name == "temporal_figures":
        common.update({
            "temporal_row_receipt": input_artifact(
                temporal_row_receipt_path(trig), "temporal-row receipt",
                optional=True,
            ),
            "cwt_result": input_artifact(
                REPO / "results" / "mvt_cwt" / f"{trig}_mvt_cwt.json",
                "CWT result", optional=True,
            ),
            "bala_result": input_artifact(
                MVT_ROOT / trig / "result.json", "Bala result", optional=True
            ),
        })
    if phase.name == "lag":
        common["step7_figs_for_annotation"] = input_artifact(
            SWEEP / trig / f"{trig}_step7_figs.json",
            "step7 figure sidecar", optional=True,
        )
    return common


def phase_input_fingerprint(trig: str, phase: Phase) -> str:
    return object_sha256(phase_input_manifest(trig, phase))


def fresh_output_paths(trig: str, phase: Phase) -> tuple[Path, ...]:
    root = SWEEP / trig
    mapping = {
        "temporal_catalog": (TEMPORAL_CATALOG,),
        "cwt": (REPO / "results" / "mvt_cwt" / f"{trig}_mvt_cwt.json",),
        "temporal_figures": (
            root / f"{trig}_step7_figs.json",
            *(root / f"{trig}_{suffix}.png" for suffix in STEP47B_FIGURES),
        ),
        "lag": (
            root / f"{trig}_step7_lag_latbright.json",
            root / f"{trig}_step7_lag_latbright.png",
        ),
        "row_repair": (
            TEMPORAL_CATALOG,
            root / f"{trig}_row_repair.json",
        ),
    }
    return tuple(mapping.get(phase.name, ()))


def validate_fresh_outputs(trig: str, phase: Phase, not_before_ns: int) -> None:
    for path in fresh_output_paths(trig, phase):
        require_fresh(path, f"fresh {phase.name} output", not_before_ns)


def phases(trig: str) -> list[Phase]:
    return [
        Phase(1, "temporal_catalog", (
            str(PYTHON), str(REPO / "scripts" / "46_temporal_all106.py"),
            "--only", trig, "--workers", "1"), REPO, True,
              lambda value: temporal_row(value)),
        Phase(2, "step_figures", (
            str(PYTHON), str(REPO / "scripts" / "44_step_figures.py"),
            "--trig", trig), REPO, False, validate_step44),
        Phase(3, "cwt", (
            str(PYTHON), str(REPO / "scripts" / "47_mvt_cwt_crosscheck.py"),
            "--trig", trig), REPO, False, validate_cwt),
        Phase(4, "bala", (
            str(PYTHON), "-m", "grb_pipeline.pipeline.mvt_runner",
            "--catalog", str(REPO / "results" / "background_intervals.ecsv"),
            "--data-root", str(REPO / "data"),
            "--output-root", str(MVT_ROOT),
            "--mvt-python", str(MVT_PYTHON),
            "--workers", "1", "--inner-cores", "1",
            "--seed", "20260718", "--resume", "--triggers", trig),
              HANDBOOK, True, validate_bala),
        Phase(5, "temporal_figures", (
            str(PYTHON), str(REPO / "scripts" / "47b_temporal_figs.py"),
            "--trig", trig), REPO, False,
              lambda value: validate_temporal_figures(
                  value, validate_bala(value)[0], validate_cwt(value)[0],
                  temporal_row(value)[0]["haar"])),
        Phase(6, "lag", (
            str(PYTHON), str(REPO / "scripts" / "47c_lag_latbright.py"),
            "--trig", trig), REPO, False, validate_lag),
        # Phase 7 (PI ruling 5 + repair choice, 2026-08-30): the catalog row's
        # LAG_*/MVT_* came from scripts/40's handbook estimators (inverted lag,
        # L26; Haar MVT). This phase REPLACES them with the validated phase-4/6
        # values (Bala canonical MVT; scripts/47c s02c lag, standard convention),
        # adds label columns, appends the trigger to the catalog header's
        # stale_pending_rewalk.rewalked_triggers, and re-records the row receipt.
        Phase(7, "row_repair", (
            str(PYTHON), str(RUNTIME / "run_p2_temporal.py"),
            "repair-row", "--triggers", trig), REPO, False, validate_row_repair),
    ]


def render_current_step9(trig: str, log_path: Path) -> dict[str, Any]:
    """Render scripts/44 step9 against the current convention table in /tmp."""
    fit = validate_current_fit(trig)
    blocks = require_file(
        SWEEP / trig / "blocks" / f"bb_blocks_spectral_{trig}.ecsv",
        "adopted blocks",
    )
    fit_sha_before = sha256(fit)
    with tempfile.TemporaryDirectory(prefix=f"codex_campaign20_step9_{trig}_",
                                     dir="/private/tmp") as temporary:
        out = Path(temporary)
        (out / "blocks").mkdir(parents=True)
        (out / trig).mkdir(parents=True)
        shutil.copy2(blocks, out / "blocks" / blocks.name)
        shutil.copy2(fit, out / trig / "spectral_fits.ecsv")
        command = (
            str(PYTHON), str(REPO / "scripts" / "44_step_figures.py"),
            "--trig", trig, "--out", str(out),
        )
        started = utcnow()
        with log_path.open("w") as log:
            log.write(f"STARTED_UTC: {started}\n")
            log.write("PURPOSE: regenerate only step9 with current convention-check fit staged in /private/tmp\n")
            log.write("COMMAND: " + " ".join(command) + "\n")
            log.flush()
            result = subprocess.run(command, cwd=REPO, env=base_env(False),
                                    stdout=log, stderr=subprocess.STDOUT, text=True)
            log.write(f"RETURN_CODE: {result.returncode}\nFINISHED_UTC: {utcnow()}\n")
        if result.returncode != 0:
            raise ValidationError(f"current-fit step9 subprocess exited {result.returncode}")
        rendered = require_file(out / f"{trig}_step9_qc.png", "current-fit step9 render")
        if sha256(fit) != fit_sha_before:
            raise ValidationError(f"{trig}: convention fit changed during step9 render")
        destination = SWEEP / trig / f"{trig}_step9_qc.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = destination.with_name(f".{destination.name}.tmp.{os.getpid()}")
        shutil.copy2(rendered, staging)
        os.replace(staging, destination)
        source = {
            "schema_version": STEP9_SCHEMA,
            "trigger": trig,
            "generated_utc": utcnow(),
            "method": "scripts/44 in temporary expected-layout staging; only step9 promoted",
            "source_fit": str(fit),
            "source_fit_sha256": fit_sha_before,
            "source_blocks": str(blocks),
            "source_blocks_sha256": sha256(blocks),
            "script": str(REPO / "scripts" / "44_step_figures.py"),
            "script_sha256": sha256(REPO / "scripts" / "44_step_figures.py"),
            "command": list(command),
            "output": str(destination),
            "output_sha256": sha256(destination),
            "figure_gate_status": GATE_STATUS,
            "verifier": None,
            "declaration": (
                "The brief-required default scripts/44 render was run first. Its step9 "
                "resolved the legacy nested sweep fit and is superseded by this SHA-bound render."
            ),
        }
        sidecar = SWEEP / trig / f"{trig}_step9_qc.source.json"
        atomic_json(sidecar, source)
        return source


def run_phase(trig: str, phase: Phase, force: bool) -> dict[str, Any]:
    log_dir = LOG_ROOT / trig
    log_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{phase.number:02d}_{phase.name}"
    log_path = log_dir / f"{stem}.log"
    status_path = log_dir / f"{stem}.status.json"
    controller_sha = sha256(Path(__file__).resolve())
    input_error = None
    try:
        input_manifest = phase_input_manifest(trig, phase)
    except Exception as exc:
        input_error = f"{type(exc).__name__}: {exc}"
        input_manifest = {"preflight_error": input_error}
    input_fingerprint = object_sha256(input_manifest)

    if not force and status_path.is_file():
        try:
            previous = read_json(status_path, "phase status")
            if (previous.get("schema_version") == PHASE_SCHEMA
                    and previous.get("state") == "COMPLETE"
                    and previous.get("command") == list(phase.command)
                    and previous.get("cwd") == str(phase.cwd)
                    and previous.get("threadpool_transport_shim") == phase.thread_shim
                    and previous.get("implementation_sha256") == phase_implementation_sha(phase)
                    and previous.get("controller_sha256") == controller_sha
                    and previous.get("input_fingerprint") == input_fingerprint
                    and input_error is None):
                phase.validator(trig)
                print(f"  {trig} P2.{phase.number} {phase.name}: REUSED")
                return {**previous, "reused_this_invocation": True}
        except Exception:
            pass

    started_utc = utcnow()
    started = time.monotonic()
    started_wall_ns = time.time_ns()
    print(f"  {trig} P2.{phase.number} {phase.name}: RUN")
    with log_path.open("w") as log:
        log.write(f"STARTED_UTC: {started_utc}\n")
        log.write(f"THREADPOOL_SHIM: {phase.thread_shim}\n")
        log.write("PYTHONHASHSEED: 0\n")
        log.write(f"CWD: {phase.cwd}\n")
        log.write("COMMAND: " + " ".join(phase.command) + "\n")
        log.flush()
        result = subprocess.run(phase.command, cwd=phase.cwd,
                                env=base_env(phase.thread_shim), stdout=log,
                                stderr=subprocess.STDOUT, text=True)
        log.write(f"RETURN_CODE: {result.returncode}\nFINISHED_UTC: {utcnow()}\n")

    errors: list[str] = []
    if input_error is not None:
        errors.append(f"input preflight: {input_error}")
    supplement = None
    base_step_receipt = None
    temporal_receipt = None
    if phase.name == "step_figures":
        if result.returncode == 0:
            try:
                base_step_receipt = record_step44_nonspectral(
                    trig, started_wall_ns
                )
            except Exception as exc:
                errors.append(
                    f"non-spectral step-figure receipt: {type(exc).__name__}: {exc}"
                )
        try:
            supplement = render_current_step9(
                trig, log_dir / "02b_step9_current_fit.log"
            )
        except Exception as exc:
            errors.append(f"step9 current-fit supplement: {type(exc).__name__}: {exc}")
    elif result.returncode == 0:
        try:
            validate_fresh_outputs(trig, phase, started_wall_ns)
            if phase.name in ("temporal_catalog", "row_repair"):
                # scripts/46 (phase 1) and repair-row (phase 7) each update one
                # row in a shared 106-row catalog.  Bind the row now so later
                # bursts may rewrite the shared file without invalidating this
                # burst's provenance.  Phase 7 is the LAST writer: its receipt
                # supersedes phase 1's and is the one the summary validates.
                temporal_row(trig, require_receipt=False)
                temporal_receipt = record_temporal_row_receipt(
                    trig, started_wall_ns, input_fingerprint
                )
        except Exception as exc:
            errors.append(f"fresh-output check: {type(exc).__name__}: {exc}")
    try:
        phase.validator(trig)
    except Exception as exc:
        errors.append(f"validation: {type(exc).__name__}: {exc}")
    if result.returncode != 0:
        errors.insert(0, f"command exit code {result.returncode}")
    state = "COMPLETE" if not errors else "FAILED"
    status = {
        "schema_version": PHASE_SCHEMA,
        "trigger": trig,
        "phase_number": phase.number,
        "phase": phase.name,
        "state": state,
        "started_utc": started_utc,
        "finished_utc": utcnow(),
        "elapsed_s": time.monotonic() - started,
        "command": list(phase.command),
        "cwd": str(phase.cwd),
        "implementation_sha256": phase_implementation_sha(phase),
        "controller_sha256": controller_sha,
        "input_fingerprint": input_fingerprint,
        "input_manifest": input_manifest,
        "return_code": result.returncode,
        "threadpool_transport_shim": phase.thread_shim,
        "pythonhashseed": 0,
        "log": str(log_path),
        "validation_errors": errors,
        "step44_nonspectral_receipt": base_step_receipt,
        "temporal_row_receipt": temporal_receipt,
        "step9_supplement": supplement,
        "figure_gate_status": GATE_STATUS if phase.name in {
            "step_figures", "temporal_figures", "lag"
        } else None,
    }
    atomic_json(status_path, status)
    print(f"  {trig} P2.{phase.number} {phase.name}: {state}")
    return status


def selected_triggers(values: list[str] | None) -> list[str]:
    if not values:
        return list(TRIGGERS)
    unknown = sorted(set(values) - set(TRIGGERS))
    if unknown:
        raise ValidationError(f"triggers outside campaign #3–#22: {unknown}")
    wanted = set(values)
    return [trig for trig in TRIGGERS if trig in wanted]


def plan(values: list[str]) -> None:
    for trig in values:
        print(f"{trig}:")
        for phase in phases(trig):
            shim = " thread-shim" if phase.thread_shim else ""
            print(f"  {phase.number}. cwd={phase.cwd}{shim}")
            print("     " + " ".join(phase.command))
        print("     supplement: scripts/44 current-fit step9 via /private/tmp (SHA-bound)")


def validate_one(trig: str, write_summary: bool) -> tuple[bool, dict[str, Any]]:
    try:
        summary = collect_summary(trig)
        ok = bool(summary.get("complete"))
    except Exception as exc:
        summary = partial_summary(trig, [f"{type(exc).__name__}: {exc}"])
        ok = False
    if write_summary:
        atomic_json(SWEEP / trig / "p2_temporal_summary.json", summary)
    return ok, summary


def run_one(trig: str, force: bool) -> bool:
    print(f"P2 START {trig} {utcnow()}")
    phase_status = [run_phase(trig, phase, force) for phase in phases(trig)]
    ok, summary = validate_one(trig, write_summary=True)
    overall = {
        "schema_version": "codex_campaign20.p2_burst_status.v1",
        "trigger": trig,
        "finished_utc": utcnow(),
        "state": "COMPLETE" if ok and all(
            item["state"] == "COMPLETE" for item in phase_status
        ) else "FAILED",
        "phases": phase_status,
        "summary": str(SWEEP / trig / "p2_temporal_summary.json"),
        "summary_complete": summary.get("complete", False),
        "figure_gate_status": GATE_STATUS,
    }
    atomic_json(LOG_ROOT / "status" / f"{trig}.json", overall)
    print(f"P2 END {trig} {overall['state']} {utcnow()}")
    return overall["state"] == "COMPLETE"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("mode", choices=("run", "validate", "plan", "repair-row"))
    result.add_argument("--triggers", nargs="*", default=None)
    result.add_argument("--force", action="store_true",
                        help="rerun phases whose prior status and products validate")
    result.add_argument("--write-summary", action="store_true",
                        help="with validate, write the normalized summary product")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        triggers = selected_triggers(args.triggers)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.mode == "plan":
        plan(triggers)
        return 0
    if args.mode == "repair-row":
        outcomes = []
        for trig in triggers:
            try:
                repair_row(trig)
                outcomes.append(True)
                print(f"{trig}: ROW REPAIRED")
            except ValidationError as exc:
                outcomes.append(False)
                print(f"{trig}: ROW REPAIR REFUSED: {exc}", file=sys.stderr)
        return 0 if all(outcomes) else 1
    if args.mode == "validate":
        outcomes = []
        for trig in triggers:
            ok, summary = validate_one(trig, write_summary=args.write_summary)
            outcomes.append(ok)
            print(f"{trig}: {'COMPLETE' if ok else 'FAILED'}")
            if not ok:
                print("  " + "\n  ".join(summary.get("validation_errors", [])))
        return 0 if all(outcomes) else 1
    outcomes = [run_one(trig, force=args.force) for trig in triggers]
    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
