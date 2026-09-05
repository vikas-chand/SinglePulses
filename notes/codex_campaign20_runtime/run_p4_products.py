#!/usr/bin/env python3
"""Run and validate campaign-20 P4 products in burst reporting order.

For every requested burst with a canonical 24-model fit, this controller runs:

1. the prescribed ``scripts/41e_sed_montage.py``;
2. the campaign-owned ``repair_sed_montage.py`` audit/fallback;
3. ``scripts/41d_param_evolution.py`` with the brief's exact fit-root/out args;
4. ``campaign_products.py tables``.

The montage validator obtains missing pairs independently from the P3 triplet
validator.  It then requires each montage sidecar to contain all 24 canonical
models, in the finite-AIC-first canonical order, and to report exactly that
independent missing count.  Parameter-evolution figures and all-model tables
are SHA-bound to the canonical fit.  This is producer-side mechanical QC only:
every figure remains UNGATED pending independent Claude figure verification.

A trigger without a canonical fit is recorded PARTIAL and no P4 producer is
launched for it.  In particular, this preserves the honest response-coverage
failure for bn100130729 rather than substituting an archival fit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/salim/Desktop/Projects/SingleRest/Two_Breaks")
RUNTIME = REPO / "notes" / "codex_campaign20_runtime"
PYTHON = Path("/Users/salim/anaconda3/envs/threeML/bin/python")
FIT_ROOT = REPO / "results" / "convention_check"
PARAM_ROOT = FIT_ROOT / "param_evolution"
LOG_ROOT = REPO / "logs" / "codex_campaign20" / "p4"

TRIGGERS = (
    "bn081224887", "bn090530760", "bn090620400", "bn090719063",
    "bn090804940", "bn090809978", "bn090829672", "bn091209001",
    "bn100122616", "bn100130729", "bn100612726", "bn100614498",
    "bn100707032", "bn101126198", "bn101225377", "bn110605183",
    "bn110618366", "bn110721200", "bn110920546", "bn110928180",
)

RESPONSE_BLOCKED = {
    "bn100130729": (
        "RESPONSE_UNCOVERED: adopted source/blocks precede every available "
        "RSP2 response matrix; no canonical 24-model P1 table exists"
    )
}

SUMMARY_SCHEMA = "codex_campaign20.p4_products_summary.v1"
PHASE_SCHEMA = "codex_campaign20.p4_phase_status.v1"
BURST_SCHEMA = "codex_campaign20.p4_burst_status.v1"
GATE_STATUS = "UNGATED_PENDING_INDEPENDENT_CLAUDE_FIGURE_VERIFICATION"


class ValidationError(RuntimeError):
    pass


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


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


def read_json(path: Path, label: str) -> dict[str, Any]:
    require_file(path, label)
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        raise ValidationError(f"{label} invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object: {path}")
    return value


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(_clean_json(value), indent=2,
                                    allow_nan=False) + "\n")
    os.replace(temporary, path)


def artifact(path: Path) -> dict[str, Any]:
    require_file(path, "artifact")
    return {"path": str(path), "sha256": sha256(path),
            "bytes": path.stat().st_size}


def runtime_modules():
    if str(RUNTIME) not in sys.path:
        sys.path.insert(0, str(RUNTIME))
    import repair_sed_montage as repair
    import run_sed_sweep as p3
    return p3, repair


def products_module():
    if str(RUNTIME) not in sys.path:
        sys.path.insert(0, str(RUNTIME))
    import campaign_products as products
    return products


def table_adapter_module():
    if str(RUNTIME) not in sys.path:
        sys.path.insert(0, str(RUNTIME))
    import p4_table_adapter as adapter
    return adapter


def load_contract(trig: str):
    p3, _ = runtime_modules()
    try:
        return p3.load_contract(trig)
    except Exception as exc:
        raise ValidationError(f"canonical fit unavailable/invalid: {type(exc).__name__}: {exc}") from exc


def default_grid(trig: str) -> Path:
    return FIT_ROOT / f"sed_grid_{trig}"


def selected_triggers(values: list[str] | None) -> list[str]:
    if not values:
        return list(TRIGGERS)
    unknown = sorted(set(values) - set(TRIGGERS))
    if unknown:
        raise ValidationError(f"triggers outside campaign #3–#22: {unknown}")
    wanted = set(values)
    return [trig for trig in TRIGGERS if trig in wanted]


def base_env() -> dict[str, str]:
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
        "MPLCONFIGDIR": "/private/tmp/codex_campaign20_mpl/p4",
        "NUMBA_CACHE_DIR": "/private/tmp/codex_campaign20_numba/p4",
        "XDG_CACHE_HOME": "/private/tmp/codex_campaign20_xdg/p4",
        "FERMI_DIR": str(fermi),
        "CALDB": str(fermi / "data" / "caldb"),
        "CALDBCONFIG": str(fermi / "data" / "caldb" / "software" / "tools" / "caldb.config"),
        "CALDBALIAS": str(fermi / "data" / "caldb" / "software" / "tools" / "alias_config.fits"),
        "CALDBROOT": str(fermi / "data" / "caldb"),
        "EXTFILESSYS": str(fermi / "refdata" / "fermi"),
    })
    old = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(RUNTIME) + (os.pathsep + old if old else "")
    env.pop("CODEX_CAMPAIGN20_THREAD_EXECUTOR", None)
    return env


def commands(trig: str) -> list[dict[str, Any]]:
    return [
        {
            "number": 1,
            "name": "montage_41e",
            "command": [str(PYTHON), str(REPO / "scripts" / "41e_sed_montage.py"),
                        "--trig", trig],
            "implementation": REPO / "scripts" / "41e_sed_montage.py",
        },
        {
            "number": 2,
            "name": "montage_audit_fallback",
            "command": [str(PYTHON), str(RUNTIME / "repair_sed_montage.py"),
                        "--trig", trig],
            "implementation": RUNTIME / "repair_sed_montage.py",
        },
        {
            "number": 3,
            "name": "parameter_evolution",
            "command": [str(PYTHON), str(REPO / "scripts" / "41d_param_evolution.py"),
                        "--trig", trig,
                        "--fit-root", "results/convention_check",
                        "--out", "results/convention_check/param_evolution"],
            "implementation": REPO / "scripts" / "41d_param_evolution.py",
        },
        {
            "number": 4,
            "name": "all_model_tables",
            "command": [str(PYTHON), str(RUNTIME / "p4_table_adapter.py"),
                        "--trig", trig,
                        # campaign_products' table manifest calls relative_to(REPO).
                        # Passing the absolute authority is therefore material, not
                        # cosmetic: the brief's relative spelling raises ValueError.
                        "--fit-root", str(FIT_ROOT)],
            "implementation": RUNTIME / "p4_table_adapter.py",
        },
    ]


def _pair_from_record(p3, record: dict[str, Any]) -> tuple[str, str]:
    try:
        return p3.normalize_bin(record["bin"]), p3.canon(record["model"])
    except Exception as exc:
        raise ValidationError(f"malformed P3 pair record: {record!r}: {exc}") from exc


def _record_map(p3, records: Any, label: str) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(records, list):
        raise ValidationError(f"P3 closure {label} is not a list")
    mapped: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValidationError(f"P3 closure {label} contains a non-object")
        pair = _pair_from_record(p3, record)
        if pair in mapped:
            raise ValidationError(f"P3 closure {label} duplicates {pair}")
        mapped[pair] = record
    return mapped


def validate_p3_closure(trig: str) -> dict[str, Any]:
    """Bind P4 to the final, current-authority P3 closure and its exact grid.

    A mere ``sweep_summary.json`` mtime is not provenance.  This check compares
    its ECSV/JSON/block hashes, pair census, selected triplet hashes, persistent
    failure classes, two-attempt evidence, and the 41e status token stream to a
    fresh scan of the canonical grid.  It also rejects multiple simultaneously
    valid sidecars for one pair, which would otherwise make 41e's glob choice
    order-dependent.
    """
    p3, _ = runtime_modules()
    contract = load_contract(trig)
    grid = default_grid(trig)
    summary_path = grid / "sweep_summary.json"
    status_path = grid / "sweep_status.txt"
    summary = read_json(summary_path, "final P3 sweep closure")
    require_file(status_path, "final P3 sweep status")

    identity_checks = (
        (summary.get("trigger") == trig, "trigger"),
        (summary.get("canonical_fit_sha256") == contract.fit_sha256,
         "canonical ECSV hash"),
        (summary.get("canonical_fit_metadata_sha256") == contract.metadata_sha256,
         "canonical JSON hash"),
        (summary.get("adopted_blocks_sha256") == contract.blocks_sha256,
         "adopted-block hash"),
        (summary.get("sed_engine_sha256") == p3.CURRENT_41C_SHA256,
         "SED-engine hash"),
        (summary.get("models") == list(contract.models), "model order"),
        (summary.get("bins") == list(contract.bins), "bin order"),
        (summary.get("pairs") == len(contract.pairs), "pair count"),
        (summary.get("pool_size") == 16, "pool size"),
        (summary.get("retry_limit") == 1, "retry limit"),
        (summary.get("aic_tolerance") == p3.AIC_TOL, "AIC tolerance"),
        (summary.get("attempt_snapshot") is None, "final-attempt marker"),
        (summary.get("bands_are_never_silently_dropped") is True,
         "every-band declaration"),
        (summary.get("persistent_failure_attempt_evidence_complete") is True,
         "persistent-failure evidence declaration"),
        (summary.get("persistent_failure_attempt_evidence_gaps") == [],
         "persistent-failure evidence gaps"),
    )
    failed_identity = [label for ok, label in identity_checks if not ok]
    if failed_identity:
        raise ValidationError(
            f"{trig}: final P3 closure is stale/malformed: {failed_identity}")
    if "UNGATED" not in str(summary.get("visual_verdict", "")):
        raise ValidationError(f"{trig}: final P3 closure lacks UNGATED status")
    for field, expected in (
        ("canonical_fit_table", contract.fit_path),
        ("canonical_fit_metadata", contract.metadata_path),
        ("adopted_blocks", contract.blocks_path),
        ("sed_engine", p3.SED_ENGINE),
        ("grid", grid),
    ):
        if _resolve_source(str(summary.get(field, ""))) != expected.resolve():
            raise ValidationError(f"{trig}: P3 closure {field} is not canonical")
    expected_plugins = {
        bin_arg: list(contract.plugin_dets_for_bin[bin_arg])
        for bin_arg in contract.bins
    }
    if summary.get("plugin_dets_by_bin") != expected_plugins:
        raise ValidationError(f"{trig}: P3 closure plugin contexts are stale")
    expected_structural = {
        bin_arg: reason for bin_arg in contract.bins
        if (reason := p3.display_coverage_mismatch(contract, bin_arg)) is not None
    }
    if summary.get("known_structural_display_mismatches") != expected_structural:
        raise ValidationError(f"{trig}: P3 structural-coverage declaration is stale")

    authority_mtime = max(
        contract.fit_path.stat().st_mtime_ns,
        contract.metadata_path.stat().st_mtime_ns,
        contract.blocks_path.stat().st_mtime_ns,
    )
    if min(summary_path.stat().st_mtime_ns, status_path.stat().st_mtime_ns) < authority_mtime:
        raise ValidationError(f"{trig}: final P3 closure predates a canonical authority")

    validations = p3.scan_grid(contract, grid)
    candidates = p3._candidate_sidecars(grid, contract)
    valid_records = _record_map(p3, summary.get("valid_triplets"), "valid_triplets")
    failed_records = _record_map(p3, summary.get("failed_pairs"), "failed_pairs")
    expected_ok = {pair for pair, result in validations.items() if result.ok}
    expected_fail = set(contract.pairs) - expected_ok
    if set(valid_records) != expected_ok or set(failed_records) != expected_fail:
        raise ValidationError(f"{trig}: P3 closure pair census differs from current scan")
    if summary.get("ok") != len(expected_ok) or summary.get("fail") != len(expected_fail):
        raise ValidationError(f"{trig}: P3 closure OK/FAIL totals are stale")

    for pair in contract.pairs:
        result = validations[pair]
        currently_valid = [
            path for path in candidates[pair]
            if p3.validate_sidecar(path, contract, pair).ok
        ]
        if result.ok:
            if len(currently_valid) != 1:
                raise ValidationError(
                    f"{trig} {pair}: {len(currently_valid)} current-valid sidecars; "
                    "41e glob selection would be ambiguous")
            record = valid_records[pair]
            chosen = currently_valid[0]
            if _resolve_source(str(record.get("sidecar", ""))) != chosen.resolve():
                raise ValidationError(f"{trig} {pair}: P3 selected sidecar path is stale")
            png, pdf = chosen.with_suffix(".png"), chosen.with_suffix(".pdf")
            for key, path in (("sidecar_sha256", chosen), ("png_sha256", png),
                              ("pdf_sha256", pdf)):
                if record.get(key) != sha256(path):
                    raise ValidationError(f"{trig} {pair}: P3 {key} differs from disk")
            if record.get("fit_mode") != result.fit_mode:
                raise ValidationError(f"{trig} {pair}: P3 fit mode differs from current scan")
        else:
            if currently_valid:
                raise ValidationError(f"{trig} {pair}: failed closure has a valid triplet")
            record = failed_records[pair]
            expected_class = p3.failure_class(contract, pair, result)
            if record.get("failure_class") != expected_class:
                raise ValidationError(
                    f"{trig} {pair}: failure class {record.get('failure_class')!r} "
                    f"!= {expected_class!r}")
            current_evidence = p3.attempt_evidence(grid, pair)
            if record.get("attempt_evidence") != current_evidence:
                raise ValidationError(f"{trig} {pair}: attempt evidence changed after closure")
            attempts = {
                int(item["attempt"]) for item in current_evidence
                if item.get("status_path") and item.get("log_path")
            }
            if attempts != {1, 2}:
                raise ValidationError(
                    f"{trig} {pair}: persistent failure lacks both attempts: {sorted(attempts)}")

    status_lines = [line for line in status_path.read_text().splitlines() if line.strip()]
    if len(status_lines) != len(contract.pairs):
        raise ValidationError(f"{trig}: P3 status has {len(status_lines)} lines")
    for pair, line in zip(contract.pairs, status_lines):
        bin_arg, model = pair
        parts = line.split(maxsplit=3)
        expected_state = "OK" if validations[pair].ok else "FAIL"
        if len(parts) < 3 or parts[:3] != [expected_state, model, bin_arg]:
            raise ValidationError(f"{trig} {pair}: malformed/stale P3 status line {line!r}")
        if expected_state == "FAIL" and (len(parts) != 4 or not parts[3].strip()):
            raise ValidationError(f"{trig} {pair}: P3 FAIL line has no reason")

    return {
        "contract": contract,
        "validations": validations,
        "summary": summary,
        "summary_artifact": artifact(summary_path),
        "status_artifact": artifact(status_path),
    }


def expected_evolution(contract) -> tuple[dict[int, str], list[str]]:
    winners: dict[int, str] = {}
    for row in contract.table:
        aics = {model: float(row[f"{model}_AIC"])
                for model in contract.models if finite(row[f"{model}_AIC"])}
        if aics:
            winners[int(row["BLOCK"])] = min(aics, key=aics.get)
    return winners, sorted(set(winners.values()))


def validate_montages(trig: str, closure: dict[str, Any] | None = None) -> dict[str, Any]:
    p3, repair = runtime_modules()
    closure = closure or validate_p3_closure(trig)
    contract = closure["contract"]
    grid = default_grid(trig)
    montage_dir = grid / "montage"
    validations = closure["validations"]
    audit_path = montage_dir / "fallback_montage_audit.json"
    audit = read_json(audit_path, "montage fallback audit")
    if audit.get("trigger") != trig or audit.get("n_models") != 24:
        raise ValidationError(f"{trig}: malformed montage fallback audit")
    if audit.get("bins") != list(contract.bins):
        raise ValidationError(f"{trig}: fallback audit bin order is stale")
    if "UNGATED" not in str(audit.get("visual_verdict", "")):
        raise ValidationError(f"{trig}: montage audit lacks UNGATED status")
    if audit.get("script") != "notes/codex_campaign20_runtime/repair_sed_montage.py":
        raise ValidationError(f"{trig}: montage audit producer is unknown")
    if audit.get("script_sha256") != sha256(RUNTIME / "repair_sed_montage.py"):
        raise ValidationError(f"{trig}: montage audit helper hash is stale")
    audit_bindings = (
        ("canonical_fit_table", contract.fit_path, "canonical_fit_sha256",
         contract.fit_sha256),
        ("canonical_fit_metadata", contract.metadata_path,
         "canonical_fit_metadata_sha256", contract.metadata_sha256),
        ("adopted_blocks", contract.blocks_path, "adopted_blocks_sha256",
         contract.blocks_sha256),
        ("p3_closure", default_grid(trig) / "sweep_summary.json",
         "p3_closure_sha256", closure["summary_artifact"]["sha256"]),
        ("p3_status", default_grid(trig) / "sweep_status.txt",
         "p3_status_sha256", closure["status_artifact"]["sha256"]),
    )
    for path_key, expected_path, hash_key, expected_hash in audit_bindings:
        if (_resolve_source(str(audit.get(path_key, ""))) != expected_path.resolve()
                or audit.get(hash_key) != expected_hash):
            raise ValidationError(f"{trig}: montage audit {path_key} binding is stale")
    decisions = {item.get("tag"): item for item in audit.get("decisions", [])}
    if len(decisions) != len(contract.bins):
        raise ValidationError(f"{trig}: fallback audit lacks one decision per tag")

    products = []
    missing_total = 0
    for bin_arg in contract.bins:
        tag = p3.tag_for(bin_arg)
        expected = repair._expected_state(contract, bin_arg, validations)
        sidecar_path = montage_dir / f"{trig}_montage_{tag}.json"
        png_path = montage_dir / f"{trig}_montage_{tag}.png"
        if not p3._png_ok(png_path):
            raise ValidationError(f"{trig} {tag}: montage PNG missing/invalid")
        sidecar = read_json(sidecar_path, f"{tag} montage sidecar")
        complete, reasons = repair._audit_existing(
            png_path, sidecar_path, expected, tag, contract, bin_arg, grid)
        if not complete:
            raise ValidationError(
                f"{trig} {tag}: montage fails current audit: {'; '.join(reasons)}")
        order = sidecar.get("order")
        if not isinstance(order, list) or len(order) != 24:
            raise ValidationError(f"{trig} {tag}: montage order length is not 24")
        if order != expected["order"] or set(order) != set(contract.models):
            raise ValidationError(f"{trig} {tag}: montage order differs from canonical 24")
        if sidecar.get("n_panels") != 24:
            raise ValidationError(f"{trig} {tag}: n_panels={sidecar.get('n_panels')} != 24")
        independent_missing = sum(
            not validations[(bin_arg, model)].ok for model in contract.models
        )
        if sidecar.get("n_missing") != independent_missing:
            raise ValidationError(
                f"{trig} {tag}: n_missing={sidecar.get('n_missing')} != "
                f"independent P3 count {independent_missing}"
            )
        decision = decisions.get(tag)
        if (not decision or decision.get("n_missing") != independent_missing
                or _resolve_source(str(decision.get("png", ""))) != png_path.resolve()
                or _resolve_source(str(decision.get("sidecar", ""))) != sidecar_path.resolve()):
            raise ValidationError(f"{trig} {tag}: fallback audit decision is stale")
        if sidecar.get("fallback_status_montage"):
            if sidecar.get("canonical_fit_sha256") != sha256(contract.fit_path):
                raise ValidationError(f"{trig} {tag}: fallback montage fit hash is stale")
            for hash_key, expected_hash in (
                ("canonical_fit_metadata_sha256", contract.metadata_sha256),
                ("adopted_blocks_sha256", contract.blocks_sha256),
                ("p3_closure_sha256", closure["summary_artifact"]["sha256"]),
                ("p3_status_sha256", closure["status_artifact"]["sha256"]),
            ):
                if sidecar.get(hash_key) != expected_hash:
                    raise ValidationError(
                        f"{trig} {tag}: fallback montage {hash_key} is stale")
            if "UNGATED" not in str(sidecar.get("visual_verdict", "")):
                raise ValidationError(f"{trig} {tag}: fallback montage is not UNGATED")
        missing_total += independent_missing
        products.append({
            "tag": tag,
            "bin": bin_arg,
            "n_panels": 24,
            "n_missing": independent_missing,
            "n_fit_failures": expected["n_fit_failures"],
            "fallback": bool(sidecar.get("fallback_status_montage")),
            "png": artifact(png_path),
            "sidecar": artifact(sidecar_path),
        })
    return {
        "tags": products,
        "n_tags": len(products),
        "n_missing_pairs": missing_total,
        "independent_p3_pairs": len(contract.pairs),
        "fallback_audit": artifact(audit_path),
    }


def _resolve_source(path_text: str) -> Path:
    path = Path(path_text)
    return path.resolve() if path.is_absolute() else (REPO / path).resolve()


def validate_parameter_evolution(
        trig: str, closure: dict[str, Any] | None = None) -> dict[str, Any]:
    p3, _ = runtime_modules()
    closure = closure or validate_p3_closure(trig)
    contract = closure["contract"]
    winners, models = expected_evolution(contract)
    script_sha = sha256(REPO / "scripts" / "41d_param_evolution.py")
    n_blocks = sum(int(row["BLOCK"]) >= 0 for row in contract.table)
    expected_stems = {f"{trig}_paramevo_{model}" for model in models}
    actual_files = {
        path.name for path in PARAM_ROOT.glob(f"{trig}_paramevo_*")
        if path.is_file() and path.suffix in {".png", ".pdf", ".json"}
    }
    expected_files = {
        stem + suffix for stem in expected_stems
        for suffix in (".png", ".pdf", ".json")
    }
    if actual_files != expected_files:
        extra = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        raise ValidationError(
            f"{trig}: parameter-evolution file set is stale "
            f"(extra={extra}, missing={missing})")
    authority_mtime = max(
        contract.fit_path.stat().st_mtime_ns,
        contract.metadata_path.stat().st_mtime_ns,
        contract.blocks_path.stat().st_mtime_ns,
        Path(closure["summary_artifact"]["path"]).stat().st_mtime_ns,
    )
    products = []
    for model in models:
        stem = PARAM_ROOT / f"{trig}_paramevo_{model}"
        png, pdf, sidecar_path = stem.with_suffix(".png"), stem.with_suffix(".pdf"), stem.with_suffix(".json")
        if not p3._png_ok(png):
            raise ValidationError(f"{trig} {model}: parameter-evolution PNG missing/invalid")
        if not p3._pdf_ok(pdf):
            raise ValidationError(f"{trig} {model}: parameter-evolution PDF missing/invalid")
        sidecar = read_json(sidecar_path, f"{model} parameter-evolution sidecar")
        if sidecar.get("trig") != trig or sidecar.get("prefix") != model:
            raise ValidationError(f"{trig} {model}: parameter-evolution identity mismatch")
        if sidecar.get("script_sha256") != script_sha or sidecar.get("no_refit") is not True:
            raise ValidationError(f"{trig} {model}: parameter-evolution provenance mismatch")
        expected_argv = [
            "--trig", trig,
            "--fit-root", "results/convention_check",
            "--out", "results/convention_check/param_evolution",
        ]
        if sidecar.get("argv") != expected_argv:
            raise ValidationError(f"{trig} {model}: parameter-evolution argv is stale")
        if _resolve_source(str(sidecar.get("source_table", ""))) != contract.fit_path.resolve():
            raise ValidationError(f"{trig} {model}: parameter-evolution uses a stale fit table")
        expected_bins = sorted(block for block, winner in winners.items()
                               if block >= 0 and winner == model)
        if sidecar.get("winner_bins") != expected_bins:
            raise ValidationError(f"{trig} {model}: winner-bin list is stale")
        if sidecar.get("n_blocks") != n_blocks or not sidecar.get("params"):
            raise ValidationError(f"{trig} {model}: parameter-evolution shape metadata invalid")
        if min(png.stat().st_mtime_ns, pdf.stat().st_mtime_ns,
               sidecar_path.stat().st_mtime_ns) < authority_mtime:
            raise ValidationError(
                f"{trig} {model}: parameter-evolution product predates its authority")
        products.append({
            "model": model,
            "winner_bins": expected_bins,
            "png": artifact(png),
            "pdf": artifact(pdf),
            "sidecar": artifact(sidecar_path),
        })
    return {"models": models, "n_models": len(models), "products": products}


def validate_tables(trig: str, closure: dict[str, Any] | None = None) -> dict[str, Any]:
    closure = closure or validate_p3_closure(trig)
    contract = closure["contract"]
    products_module_value = products_module()
    adapter = table_adapter_module()
    table_dir = default_grid(trig) / "tables"
    manifest_path = table_dir / "tables_manifest.json"
    manifest = read_json(manifest_path, "all-model table manifest")
    if manifest.get("trigger") != trig or manifest.get("n_models") != 24:
        raise ValidationError(f"{trig}: table manifest identity/model count mismatch")
    if manifest.get("n_spectra") != len(contract.table):
        raise ValidationError(f"{trig}: table manifest spectrum count is stale")
    if manifest.get("source_sha256") != sha256(contract.fit_path):
        raise ValidationError(f"{trig}: tables are not bound to current canonical fit")
    if (manifest.get("schema_version") != adapter.SCHEMA
            or manifest.get("script_sha256") != sha256(RUNTIME / "p4_table_adapter.py")
            or manifest.get("base_formatter_sha256") != sha256(
                RUNTIME / "campaign_products.py")):
        raise ValidationError(f"{trig}: table formatter provenance is stale")
    if (_resolve_source(str(manifest.get("script", "")))
            != (RUNTIME / "p4_table_adapter.py").resolve()
            or _resolve_source(str(manifest.get("base_formatter", "")))
            != (RUNTIME / "campaign_products.py").resolve()
            or manifest.get("provisional") is not True):
        raise ValidationError(f"{trig}: table formatter identity/declaration is stale")
    source = _resolve_source(str(manifest.get("source", "")))
    if source != contract.fit_path.resolve():
        raise ValidationError(f"{trig}: table manifest source path is not canonical")
    metadata_source = _resolve_source(str(manifest.get("source_metadata", "")))
    if (metadata_source != contract.metadata_path.resolve()
            or manifest.get("source_metadata_sha256") != contract.metadata_sha256):
        raise ValidationError(f"{trig}: tables are not bound to current canonical JSON")
    expected_names = {
        "TINT_params.md" if int(row["BLOCK"]) < 0 else f"bin{int(row['BLOCK'])}_params.md"
        for row in contract.table
    }
    actual_names = {
        path.name for path in table_dir.iterdir()
        if path.is_file() and re.fullmatch(r"(?:TINT|bin[0-9]+)_params\.md", path.name)
    }
    if actual_names != expected_names:
        raise ValidationError(
            f"{trig}: stale/missing per-spectrum tables "
            f"(extra={sorted(actual_names - expected_names)}, "
            f"missing={sorted(expected_names - actual_names)})")
    entries = manifest.get("products", [])
    if len(entries) != len(expected_names) or {entry.get("file") for entry in entries} != expected_names:
        raise ValidationError(f"{trig}: table manifest does not cover every spectrum")
    entries_by_name = {str(entry.get("file")): entry for entry in entries}
    products = []
    expected_texts = []
    found_prefixes = products_module_value.model_prefixes(contract.table)
    if (len(found_prefixes) != 24
            or set(found_prefixes) != set(products_module_value.HIGHE_PREFIXES)):
        raise ValidationError(f"{trig}: table formatter did not find 24 models")
    prefixes = list(products_module_value.HIGHE_PREFIXES)
    authority_mtime = max(
        contract.fit_path.stat().st_mtime_ns,
        contract.metadata_path.stat().st_mtime_ns,
        contract.blocks_path.stat().st_mtime_ns,
        Path(closure["summary_artifact"]["path"]).stat().st_mtime_ns,
    )
    for row in sorted(contract.table, key=lambda value: int(value["BLOCK"])):
        block = int(row["BLOCK"])
        name = "TINT_params.md" if block < 0 else f"bin{block}_params.md"
        entry = entries_by_name[name]
        path = table_dir / name
        require_file(path, "per-spectrum all-model table")
        if entry.get("rows") != 24 or entry.get("sha256") != sha256(path):
            raise ValidationError(f"{trig}: invalid table manifest entry {entry.get('file')}")
        expected_winner = products_module_value.winner_prefix(row["BEST_AIC_MODEL"])
        if entry.get("winner") != expected_winner:
            raise ValidationError(f"{trig}: {name} manifest winner is stale")
        expected_interval = [float(row["T_START"]), float(row["T_STOP"])]
        try:
            observed_interval = [float(value) for value in entry.get("interval_s", [])]
        except Exception:
            observed_interval = []
        if (entry.get("block") != block or len(observed_interval) != 2
                or any(abs(left - right) > 1.0e-8
                       for left, right in zip(observed_interval, expected_interval))):
            raise ValidationError(f"{trig}: {name} manifest interval/block is stale")
        expected_text = adapter.table_text(
            contract.table, row, prefixes)
        if path.read_text() != expected_text:
            raise ValidationError(f"{trig}: {name} content differs from current fit")
        expected_texts.append(expected_text)
        lines = path.read_text().splitlines()
        model_rows = [line for line in lines if line.startswith("| ")][1:]
        if len(model_rows) != 24 or sum(" **(winner)**" in line for line in model_rows) != 1:
            raise ValidationError(f"{trig}: {path.name} does not contain 24 rows/one winner")
        products.append(artifact(path))
    combined = table_dir / "ALL_MODELS_TABLES.md"
    require_file(combined, "combined all-model tables")
    if (manifest.get("combined") != combined.name
            or manifest.get("combined_sha256") != sha256(combined)):
        raise ValidationError(f"{trig}: combined table hash mismatch")
    expected_combined = (
        f"# {trig} — all models, all bins (campaign-20 P4; provisional)\n\n"
        + "\n".join(expected_texts)
    )
    if combined.read_text() != expected_combined:
        raise ValidationError(f"{trig}: combined all-model table differs from current fit")
    product_paths = [table_dir / name for name in expected_names]
    product_paths.extend((combined, manifest_path))
    if min(path.stat().st_mtime_ns for path in product_paths) < authority_mtime:
        raise ValidationError(f"{trig}: all-model tables predate a current authority")
    return {
        "n_spectra": len(entries),
        "n_models_per_spectrum": 24,
        "manifest": artifact(manifest_path),
        "combined": artifact(combined),
        "products": products,
    }


def collect_summary(trig: str) -> dict[str, Any]:
    closure = validate_p3_closure(trig)
    contract = closure["contract"]
    montages = validate_montages(trig, closure)
    evolution = validate_parameter_evolution(trig, closure)
    tables = validate_tables(trig, closure)
    return {
        "schema_version": SUMMARY_SCHEMA,
        "trigger": trig,
        "generated_utc": utcnow(),
        "producer": "Codex (AI)",
        "state": "COMPLETE",
        "provisional": True,
        "figure_gate_status": GATE_STATUS,
        "figure_verifier": None,
        "canonical_fit": artifact(contract.fit_path),
        "canonical_fit_metadata": artifact(contract.metadata_path),
        "adopted_blocks": artifact(contract.blocks_path),
        "p3_closure": closure["summary_artifact"],
        "p3_status": closure["status_artifact"],
        "montages": montages,
        "parameter_evolution": evolution,
        "all_model_tables": tables,
        "declarations": [
            "Every montage has 24 cells; unavailable P3 triplets remain explicit placeholders.",
            "Montage n_missing values are independently recomputed from the P3 triplet validator.",
            "No figure has been visually verified by this producer-side controller.",
        ],
    }


def partial_summary(
        trig: str, errors: list[str], p3_closure: dict[str, Any] | None = None
        ) -> dict[str, Any]:
    payload = {
        "schema_version": SUMMARY_SCHEMA,
        "trigger": trig,
        "generated_utc": utcnow(),
        "producer": "Codex (AI)",
        "state": "PARTIAL",
        "provisional": True,
        "figure_gate_status": GATE_STATUS,
        "figure_verifier": None,
        "errors": errors,
        "declaration": "Missing/failed P4 products are reported; no archival fit is substituted.",
    }
    if p3_closure is not None:
        payload["p3_closure"] = p3_closure
    return payload


def validate_blocked_p3_closure(trig: str) -> dict[str, Any]:
    """Validate the explicit zero-pair closure for a response-blocked burst."""
    if trig not in RESPONSE_BLOCKED:
        raise ValidationError(f"{trig}: not a declared response-blocked burst")
    grid = default_grid(trig)
    summary_path = grid / "sweep_summary.json"
    status_path = grid / "sweep_status.txt"
    summary = read_json(summary_path, "response-blocked P3 closure")
    require_file(status_path, "response-blocked P3 status")
    expected = RESPONSE_BLOCKED[trig]
    checks = (
        summary.get("trigger") == trig,
        summary.get("status") == "RESPONSE_BLOCKED",
        summary.get("pairs") == 0,
        summary.get("ok") == 0,
        summary.get("fail") == 0,
        summary.get("blocked") == 1,
        summary.get("models") == [],
        summary.get("bins") == [],
        "RESPONSE_UNCOVERED" in str(summary.get("reason", "")),
        status_path.read_text().startswith("BLOCKED RESPONSE_UNCOVERED "),
    )
    if not all(checks):
        raise ValidationError(f"{trig}: malformed response-blocked P3 closure")
    if expected.split(":", 1)[0] not in str(summary.get("reason", "")):
        raise ValidationError(f"{trig}: response-blocked reason is inconsistent")
    return {"summary": artifact(summary_path), "status": artifact(status_path)}


def run_command(trig: str, specification: dict[str, Any]) -> dict[str, Any]:
    log_dir = LOG_ROOT / trig
    log_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{specification['number']:02d}_{specification['name']}"
    log_path = log_dir / f"{stem}.log"
    status_path = log_dir / f"{stem}.status.json"
    started_utc = utcnow()
    started = time.monotonic()
    command = specification["command"]
    print(f"  {trig} P4.{specification['number']} {specification['name']}: RUN")
    with log_path.open("w") as log:
        log.write(f"STARTED_UTC: {started_utc}\n")
        log.write(f"CWD: {REPO}\n")
        log.write("FIGURE_GATE: " + GATE_STATUS + "\n")
        log.write("COMMAND: " + " ".join(command) + "\n")
        log.flush()
        result = subprocess.run(command, cwd=REPO, env=base_env(), stdout=log,
                                stderr=subprocess.STDOUT, text=True)
        log.write(f"RETURN_CODE: {result.returncode}\nFINISHED_UTC: {utcnow()}\n")
    validation_errors: list[str] = []
    validator = {
        "montage_audit_fallback": validate_montages,
        "parameter_evolution": validate_parameter_evolution,
        "all_model_tables": validate_tables,
    }.get(specification["name"])
    if validator is not None:
        try:
            validator(trig)
        except Exception as exc:
            validation_errors.append(f"{type(exc).__name__}: {exc}")
            with log_path.open("a") as log:
                log.write("VALIDATION_ERROR: " + validation_errors[-1] + "\n")
    phase_complete = result.returncode == 0 and not validation_errors
    status = {
        "schema_version": PHASE_SCHEMA,
        "trigger": trig,
        "phase_number": specification["number"],
        "phase": specification["name"],
        "state": "COMPLETE" if phase_complete else "FAILED",
        "started_utc": started_utc,
        "finished_utc": utcnow(),
        "elapsed_s": time.monotonic() - started,
        "attempt": 1,
        "retry_of": None,
        "command": command,
        "cwd": str(REPO),
        "return_code": result.returncode,
        "validation_errors": validation_errors,
        "implementation": str(specification["implementation"]),
        "implementation_sha256": sha256(require_file(
            specification["implementation"], "P4 implementation")),
        "log": str(log_path),
        "figure_gate_status": GATE_STATUS if specification["number"] <= 3 else None,
    }
    atomic_json(status_path, status)
    return status


def validate_one(trig: str, write_summary: bool) -> tuple[bool, dict[str, Any]]:
    if trig in RESPONSE_BLOCKED:
        errors = [RESPONSE_BLOCKED[trig]]
        closure = None
        try:
            closure = validate_blocked_p3_closure(trig)
        except Exception as exc:
            errors.append(f"P3 closure: {type(exc).__name__}: {exc}")
        summary = partial_summary(trig, errors, closure)
        if write_summary:
            atomic_json(default_grid(trig) / "p4_products_summary.json", summary)
        return False, summary
    try:
        summary = collect_summary(trig)
        ok = True
    except Exception as exc:
        summary = partial_summary(trig, [f"{type(exc).__name__}: {exc}"])
        ok = False
    if write_summary and (default_grid(trig).is_dir() or ok):
        atomic_json(default_grid(trig) / "p4_products_summary.json", summary)
    return ok, summary


def preflight_partial(trig: str, reason: str) -> dict[str, Any]:
    log_dir = LOG_ROOT / trig
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "00_preflight.log").write_text(
        f"{utcnow()} PARTIAL {reason}\nNo P4 producer launched; no archival fit substituted.\n"
    )
    status = {
        "schema_version": BURST_SCHEMA,
        "trigger": trig,
        "state": "PARTIAL",
        "finished_utc": utcnow(),
        "reason": reason,
        "phases": [],
        "figure_gate_status": GATE_STATUS,
    }
    closure = None
    summary_errors = [reason]
    if trig in RESPONSE_BLOCKED:
        try:
            closure = validate_blocked_p3_closure(trig)
        except Exception as exc:
            status["p3_closure_error"] = f"{type(exc).__name__}: {exc}"
            summary_errors.append("P3 closure: " + status["p3_closure_error"])
    summary = partial_summary(trig, summary_errors, closure)
    atomic_json(default_grid(trig) / "p4_products_summary.json", summary)
    status["summary"] = str(default_grid(trig) / "p4_products_summary.json")
    atomic_json(LOG_ROOT / "status" / f"{trig}.json", status)
    return status


def run_one(trig: str, force: bool) -> bool:
    overall_path = LOG_ROOT / "status" / f"{trig}.json"
    if not force and overall_path.is_file():
        try:
            prior = read_json(overall_path, "P4 burst status")
            ok, _ = validate_one(trig, write_summary=False)
            if prior.get("state") == "COMPLETE" and ok:
                print(f"P4 {trig}: REUSED COMPLETE")
                return True
        except Exception:
            pass
    try:
        validate_p3_closure(trig)
    except Exception as exc:
        reason = RESPONSE_BLOCKED.get(trig, f"{type(exc).__name__}: {exc}")
        preflight_partial(trig, reason)
        print(f"P4 {trig}: PARTIAL — {reason}")
        return False

    print(f"P4 START {trig} {utcnow()}")
    statuses = [run_command(trig, item) for item in commands(trig)]
    ok, summary = validate_one(trig, write_summary=True)
    native_failed = statuses[0]["state"] == "FAILED"
    downstream_ok = all(item["state"] == "COMPLETE" for item in statuses[1:])
    # A 41e failure is an anticipated recoverable path only when the independent
    # fallback and every downstream validator complete.
    recovered_native = bool(native_failed and ok and downstream_ok)
    state = "COMPLETE" if ok and downstream_ok and (
        statuses[0]["state"] == "COMPLETE" or recovered_native
    ) else "PARTIAL"
    overall = {
        "schema_version": BURST_SCHEMA,
        "trigger": trig,
        "state": state,
        "finished_utc": utcnow(),
        "phases": statuses,
        "native_41e_failure_recovered_by_fallback": recovered_native,
        "summary": str(default_grid(trig) / "p4_products_summary.json"),
        "summary_state": summary.get("state"),
        "errors": summary.get("errors", []),
        "figure_gate_status": GATE_STATUS,
    }
    atomic_json(overall_path, overall)
    print(f"P4 END {trig} {state} {utcnow()}")
    return state == "COMPLETE"


def plan(triggers: list[str]) -> None:
    for trig in triggers:
        print(f"{trig}:")
        try:
            if trig in RESPONSE_BLOCKED:
                validate_blocked_p3_closure(trig)
                raise ValidationError(RESPONSE_BLOCKED[trig])
            validate_p3_closure(trig)
        except Exception as exc:
            print(f"  PARTIAL preflight: {exc}; no command will run")
            continue
        for item in commands(trig):
            print(f"  {item['number']}. " + " ".join(item["command"]))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("mode", choices=("run", "validate", "plan"))
    result.add_argument("--triggers", nargs="*", default=None)
    result.add_argument("--force", action="store_true")
    result.add_argument("--write-summary", action="store_true",
                        help="with validate, write p4_products_summary.json")
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
    if args.mode == "validate":
        outcomes = []
        for trig in triggers:
            ok, summary = validate_one(trig, write_summary=args.write_summary)
            outcomes.append(ok)
            print(f"{trig}: {'COMPLETE' if ok else 'PARTIAL'}")
            for error in summary.get("errors", []):
                print(f"  {error}")
        return 0 if all(outcomes) else 1
    outcomes = [run_one(trig, force=args.force) for trig in triggers]
    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
