#!/usr/bin/env python3
"""Campaign-scoped fit validation and 24-model parameter-table products.

This helper exists because the burst-2 Markdown parameter tables were made by
an unsaved one-off formatter and no repository script regenerates them.  It
does not fit, select, or alter scientific results.  The canonical engine ECSV
and JSON remain the only numerical authorities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path

import numpy as np
from astropy.table import Column, Table


REPO = Path(__file__).resolve().parents[2]
FIT_ROOT = REPO / "results" / "convention_check"

MODEL_NAMES = {
    "BAND": "Band",
    "CPL": "CPL",
    "SBPL": "SBPL",
    "DSBPL": "DSBPL",
    "BANDBB": "Band+BB",
    "CPLBB": "CPL+BB",
    "SBPLF": "SBPLfree",
    "DSBPLF": "DSBPLfree",
    "BANDPL": "Band+PL",
    "BANDCPL": "Band+CPL",
    "CPLPL": "CPL+PL",
    "CPLCPL": "CPL+CPL",
    "BANDRCPL": "BandR+CPL",
    "BANDCUT": "BandxCut",
    "SBPLCUT": "SBPLxCut",
    "SBPLPL": "SBPL+PL",
    "SBPLCPL": "SBPL+CPL",
    "BANDBBPL": "Band+BB+PL",
    "BANDBBCPL": "Band+BB+CPL",
    "CPLBBPL": "CPL+BB+PL",
    "CPLBBCPL": "CPL+BB+CPL",
    "SBPLBB": "SBPL+BB",
    "SBPLBBPL": "SBPL+BB+PL",
    "SBPLBBCPL": "SBPL+BB+CPL",
}

# This is scripts/10's ACTIVE_SPECS order for ``--models highe``.  It is
# scientifically material when two AIC values are exactly equal because
# Python's ``min`` keeps the first candidate.  Never alphabetize it.
HIGHE_PREFIXES = tuple(MODEL_NAMES)

FAMILY_PREFIXES = {
    "default": HIGHE_PREFIXES[:6],
    "shape": HIGHE_PREFIXES[:8],
    "highe": HIGHE_PREFIXES,
    "threecomp": tuple(
        prefix for prefix in HIGHE_PREFIXES
        if prefix not in {
            "DSBPL", "SBPLF", "DSBPLF", "BANDRCPL", "BANDCUT", "SBPLCUT",
        }
    ),
}
FAMILY_ORDER = ("default", "shape", "highe", "threecomp")
MERGE_PRIORITY = (
    "highe_retry", "threecomp_retry", "shape_retry", "default_retry",
    "threecomp", "shape", "default",
)

CAMPAIGN_TRIGGERS = (
    "bn081224887", "bn090530760", "bn090620400", "bn090719063",
    "bn090804940", "bn090809978", "bn090829672", "bn091209001",
    "bn100122616", "bn100130729", "bn100612726", "bn100614498",
    "bn100707032", "bn101126198", "bn101225377", "bn110605183",
    "bn110618366", "bn110721200", "bn110920546", "bn110928180",
)
BROADBAND_TRIGGERS = {"bn081224887", "bn110721200"}
RESPONSE_BLOCKED = {
    "bn100130729": (
        "RESPONSE_UNCOVERED: adopted source/blocks precede every available "
        "RSP2 matrix; no spectral family may be retried or promoted"
    ),
}
MERGE_POLICY_VERSION = "campaign20-p1-fail-to-ok-v2"

# Source-model free-parameter counts used by scripts/10's winner selection.
# The stored AIC/BIC columns additionally include EAC/LAT nuisance parameters;
# those nuisance counts are audited below but must not change relative ranking.
SOURCE_K = {
    "BAND": 4, "CPL": 3, "SBPL": 4, "DSBPL": 6,
    "SBPLF": 5, "DSBPLF": 8, "BANDBB": 6, "CPLBB": 5,
    "SBPLBB": 6, "BANDPL": 6, "BANDCPL": 7, "CPLPL": 5,
    "CPLCPL": 6, "SBPLPL": 6, "SBPLCPL": 7,
    "BANDRCPL": 7, "BANDCUT": 5, "SBPLCUT": 5,
    "BANDBBPL": 8, "BANDBBCPL": 9, "CPLBBPL": 7,
    "CPLBBCPL": 8, "SBPLBBPL": 8, "SBPLBBCPL": 9,
}

MODEL_PREFIX_BY_CANON = {
    re.sub(r"[^A-Z0-9]", "", display.upper()): prefix
    for prefix, display in MODEL_NAMES.items()
}
MODEL_PREFIX_BY_CANON.update({
    re.sub(r"[^A-Z0-9]", "", prefix.upper()): prefix
    for prefix in MODEL_NAMES
})
MODEL_PREFIX_BY_CANON.update({"2SBPL": "DSBPL", "2SBPLFREE": "DSBPLF"})


def winner_prefix(value: str) -> str:
    """Translate the engine's display-name winner to its table prefix."""
    key = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    if key not in MODEL_PREFIX_BY_CANON:
        raise KeyError(f"unknown BEST_AIC_MODEL value: {value!r}")
    return MODEL_PREFIX_BY_CANON[key]

RESERVED_SUFFIXES = {
    "STATUS", "N2LL", "MINOS_OK", "ERROR_METHOD", "VALID", "AIC", "BIC",
    "EPK_CURVE", "WIDTH_HM",
}


def finite(value) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def fmt(value) -> str:
    if not finite(value):
        return "---"
    return f"{float(value):.4g}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def model_prefixes(table: Table) -> list[str]:
    found = [c[:-4] for c in table.colnames if c.endswith("_AIC")]
    unknown = [p for p in found if p not in MODEL_NAMES]
    assert not unknown, f"unknown model prefixes: {unknown}"
    assert len(found) == len(set(found)), f"duplicate model prefixes: {found}"
    return found


def usable_model_cell(row, prefix: str) -> bool:
    return (str(row[f"{prefix}_STATUS"]).upper() == "OK"
            and finite(row[f"{prefix}_N2LL"])
            and finite(row[f"{prefix}_AIC"])
            and finite(row[f"{prefix}_BIC"]))


def load_fit(trig: str, fit_root: Path = FIT_ROOT):
    root = fit_root / trig
    ecsv = root / "spectral_fits.ecsv"
    sidecar = root / "spectral_fits.json"
    table = Table.read(ecsv, format="ascii.ecsv")
    meta = json.loads(sidecar.read_text())
    return table, meta, ecsv, sidecar


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "1.0"}


def _replace_string_column(table: Table, name: str, values, width: int = 256) -> None:
    """Replace, rather than assign into, fixed-width Astropy string columns."""
    vals = [str(v) for v in values]
    width = max(width, max((len(v) for v in vals), default=1))
    table.replace_column(name, Column(np.asarray(vals, dtype=f"U{width}"), name=name))


def _text_values(column) -> list[str]:
    return ["" if np.ma.is_masked(v) else str(v) for v in column]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z")


def _file_record(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.is_file(),
        "sha256": sha256(path) if path.is_file() else None,
        "bytes": path.stat().st_size if path.is_file() else None,
    }


def _atomic_write_text(path: Path, text: str) -> None:
    """Write a small campaign artifact without exposing a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def _family_from_label(label: str) -> str:
    family = label[:-6] if label.endswith("_retry") else label
    if family not in FAMILY_PREFIXES:
        raise AssertionError(f"unknown family label {label!r}")
    return family


def _read_family(trig: str, family: str, directory: Path):
    """Read a complete engine family and enforce its exact registry contract."""
    assert family in FAMILY_PREFIXES, family
    ecsv = directory / "spectral_fits.ecsv"
    sidecar = directory / "spectral_fits.json"
    assert ecsv.is_file() and sidecar.is_file(), (
        "missing family artifact", trig, family, directory)
    table = Table.read(ecsv, format="ascii.ecsv")
    meta = json.loads(sidecar.read_text())
    prefixes = tuple(model_prefixes(table))
    expected = FAMILY_PREFIXES[family]
    assert prefixes == expected, (trig, family, prefixes, expected)
    assert meta.get("models") == [MODEL_NAMES[p] for p in expected], (
        trig, family, meta.get("models"), [MODEL_NAMES[p] for p in expected])
    assert meta.get("trigger") == trig, (meta.get("trigger"), trig)
    assert "n_blocks" in meta
    blocks = [int(v) for v in table["BLOCK"]]
    assert len(set(blocks)) == len(blocks), (trig, family, "duplicate blocks")
    assert sorted(blocks) == [-1] + list(range(int(meta["n_blocks"]))), (
        trig, family, blocks, meta["n_blocks"])
    assert len(table) == int(meta["n_blocks"]) + 1
    for prefix in expected:
        for suffix in ("STATUS", "N2LL", "AIC", "BIC", "VALID"):
            assert f"{prefix}_{suffix}" in table.colnames, (
                trig, family, prefix, suffix)
    return table, meta, ecsv, sidecar


def _attempt_evidence(trig: str, label: str, directory: Path,
                      log_root: Path) -> dict:
    """Capture output and log evidence without treating absent evidence as success."""
    family = _family_from_label(label)
    logfile = log_root / f"{trig}_{label}.log"
    statusfile = log_root / "status" / f"{trig}_{label}.status"
    record = {
        "label": label,
        "family": family,
        "output_dir": str(directory),
        "ecsv": _file_record(directory / "spectral_fits.ecsv"),
        "json": _file_record(directory / "spectral_fits.json"),
        "log": _file_record(logfile),
        "pool_status": _file_record(statusfile),
        "pool_status_fields": None,
        "output_state": "MISSING",
        "validation_error": None,
        "literal_fail_count": None,
        "failed_cells": [],
        "command": None,
        "engine_exit_code": None,
        "started_utc": None,
        "finished_utc": None,
        "include_lat_in_command": None,
        "lle_approved_message_in_log": None,
        "lle_in_fit_dets": None,
        "lle_in_every_plugin_row": None,
        "lat_plugin_blocks": [],
    }
    log_text = logfile.read_text(errors="replace") if logfile.is_file() else None
    if statusfile.is_file():
        # The first campaign launch used zsh ``print -r`` with "\\t", so its
        # records contain literal backslash-t.  Later launches contain tabs.
        status_lines = statusfile.read_text(errors="replace").splitlines()
        if status_lines:
            record["pool_status_fields"] = status_lines[0].replace(
                "\\t", "\t").split("\t")
    if log_text is not None:
        command = next((line.partition("COMMAND:")[2].strip()
                        for line in log_text.splitlines()
                        if line.startswith("COMMAND:")), None)
        exit_text = next((line.partition("ENGINE_EXIT_CODE:")[2].strip()
                          for line in log_text.splitlines()
                          if line.startswith("ENGINE_EXIT_CODE:")), None)
        record["started_utc"] = next((
            line.partition("STARTED_UTC:")[2].strip()
            for line in log_text.splitlines() if line.startswith("STARTED_UTC:")), None)
        record["finished_utc"] = next((
            line.partition("FINISHED_UTC:")[2].strip()
            for line in log_text.splitlines() if line.startswith("FINISHED_UTC:")), None)
        record["command"] = command
        record["engine_exit_code"] = (int(exit_text)
                                      if exit_text and exit_text.lstrip("-").isdigit()
                                      else exit_text)
        record["include_lat_in_command"] = (
            "--include-lat" in command.split() if command else False)
        record["lle_approved_message_in_log"] = (
            "LLE data present — using APPROVED LLE bkg window" in log_text)
    try:
        table, meta, _, _ = _read_family(trig, family, directory)
        failures = []
        for row in table:
            for prefix in FAMILY_PREFIXES[family]:
                status = str(row[f"{prefix}_STATUS"])
                if status == "FAIL":
                    failures.append({"block": int(row["BLOCK"]),
                                     "model": prefix, "status": status})
        fit_dets = [str(v) for v in meta.get("fit_dets", [])]
        plugins = [str(v).split(",") for v in table["PLUGIN_DETS"]]
        record.update({
            "output_state": "COMPLETE",
            "literal_fail_count": len(failures),
            "failed_cells": failures,
            "fit_dets": fit_dets,
            "lle_in_fit_dets": "lle" in fit_dets,
            "lle_in_every_plugin_row": all("lle" in v for v in plugins),
            "lat_plugin_blocks": [int(row["BLOCK"]) for row, dets in zip(table, plugins)
                                  if "LAT" in dets],
            "models": list(FAMILY_PREFIXES[family]),
            "rows": len(table),
        })
    except Exception as exc:
        if record["ecsv"]["exists"] or record["json"]["exists"]:
            record["output_state"] = "INVALID"
        record["validation_error"] = f"{type(exc).__name__}: {exc}"
    return record


def _quarantine_record(family_root: Path, family: str) -> str | None:
    """Return the manifest path+reason if this family's outputs were quarantined.

    An auditable removal, not an unexplained absence: some
    *QUARANTINE_MANIFEST.json beside the burst's fit directory must list the
    family directory in its ``moved[].from``.  Returns None otherwise.
    """
    import json as _json
    burst_root = family_root.parent
    target = str(family_root / family)
    for manifest in sorted(burst_root.glob("*/*QUARANTINE_MANIFEST.json")):
        try:
            data = _json.loads(manifest.read_text())
        except Exception:
            continue
        for entry in data.get("moved", []):
            frm = str(entry.get("from", ""))
            if frm.endswith(target) or target.endswith(frm):
                return f"{manifest.name}: {str(data.get('reason',''))[:120]}"
    return None


def _retry_compliance(trig: str, attempts: list[dict], family_root: Path,
                      log_root: Path,
                      base_model_complete: bool = False) -> list[dict]:
    """Prove that each eligible family received one, and only one, retry.

    SINGLE-RUN COMPLETENESS (PI ruling 2026-09-01, "Teach the tool single-run
    completeness"): the base family may be produced by ONE engine process that
    fits the whole model menu (`--models highe`; ACTIVE_SPECS is cumulative).
    When that happens the other families are never attempted at all, and there
    is nothing for them to retry -- their retry contract is VACUOUS, not
    unsatisfied.  This is only granted when BOTH hold:
      (a) the base table is model-complete (every model in its own sidecar
          menu has an _AIC column), and
      (b) the family HAS NO TABLE, so it can contribute no cells at all.
          Three auditable sub-cases are distinguished in the receipt: it was never attempted (no table, sidecar, log or
          pool status), OR its outputs were deliberately QUARANTINED and that
          removal is recorded in a quarantine manifest beside the fit root,
          naming the family directory it moved and the reason.  The second
          case is the real one after a Stage-1 amendment: the family DID run
          earlier, its table is now superseded, and re-admitting it would let
          pre-amendment cells overwrite the fresh base (the merge priority
          places *_retry ABOVE the base).  A family whose outputs are simply
          absent with no manifest and no explanation still FAILS.
    A family that WAS attempted and came back incomplete still fails, which is
    the case the original assertion existed to catch.  Rationale: the
    single-process route is chosen precisely to make the NR-8 merge-integrity
    class structurally impossible, and the promotion gate must not force a
    multi-family merge back into existence to satisfy a bookkeeping check."""
    by_label = {attempt["label"]: attempt for attempt in attempts}
    assert len(by_label) == 8, (trig, sorted(by_label))
    terminal_pool_states = {
        "COMPLETE", "FAILED", "REUSED", "BLOCKED_INVALID_EXISTING",
    }
    compliance = []
    for family in FAMILY_ORDER:
        initial = by_label[family]
        retry = by_label[f"{family}_retry"]
        initial_complete = initial["output_state"] == "COMPLETE"
        eligible = initial_complete and int(initial["literal_fail_count"] or 0) > 0
        pool_state = (retry["pool_status_fields"][0]
                      if retry["pool_status_fields"] else None)
        terminal_pool = pool_state in terminal_pool_states
        terminal_log = (retry["engine_exit_code"] is not None
                        or retry["finished_utc"] is not None)
        complete_artifact = retry["output_state"] == "COMPLETE"
        terminal_evidence = complete_artifact or terminal_pool or terminal_log
        any_retry_evidence = any([
            retry["ecsv"]["exists"], retry["json"]["exists"],
            retry["log"]["exists"], retry["pool_status"]["exists"],
        ])

        exact_dir = family_root / f"{family}_retry"
        extra_paths = []
        for path in sorted(family_root.glob(f"{family}_retry*")):
            if path != exact_dir and path.exists():
                extra_paths.append(str(path))
        for path in sorted(log_root.glob(f"{trig}_{family}_retry*")):
            if path not in {
                    log_root / f"{trig}_{family}_retry.log",
                    log_root / "status" / f"{trig}_{family}_retry.status"}:
                extra_paths.append(str(path))
        # Status files live one level lower and therefore need their own scan.
        status_root = log_root / "status"
        if status_root.is_dir():
            for path in sorted(status_root.glob(f"{trig}_{family}_retry*")):
                if path != status_root / f"{trig}_{family}_retry.status":
                    extra_paths.append(str(path))

        any_initial_evidence = any([
            initial["ecsv"]["exists"], initial["json"]["exists"],
            initial["log"]["exists"], initial["pool_status"]["exists"],
        ])
        outputs_absent = not (initial["ecsv"]["exists"] or initial["json"]["exists"])
        quarantined = _quarantine_record(family_root, family)
        never_attempted = (not any_initial_evidence and not any_retry_evidence
                           and not extra_paths)
        if not initial_complete and base_model_complete and outputs_absent:
            # A family with NO TABLE cannot contribute a single cell to the
            # merge.  If the base is model-complete the retry mandate is
            # already discharged by the base itself, so this family's retry
            # status is moot.  The sub-case is recorded for audit.
            compliant = True
            if never_attempted:
                outcome = "NOT_REQUIRED_NEVER_ATTEMPTED"
                reason = ("base run is model-complete and this family was never "
                          "attempted; nothing to retry (single-process route)")
            elif quarantined:
                outcome = "NOT_REQUIRED_SUPERSEDED_QUARANTINED"
                reason = ("base run is model-complete and this family's outputs "
                          f"are quarantined as superseded: {quarantined}")
            else:
                outcome = "NOT_REQUIRED_NO_OUTPUT_PRODUCED"
                reason = ("base run is model-complete and this family produced "
                          "no table (attempt evidenced but no output); it can "
                          "contribute no cells to the merge")
        elif not initial_complete:
            compliant = False
            outcome = "INITIAL_NOT_COMPLETE"
            reason = "retry eligibility cannot be established"
        elif eligible and extra_paths:
            compliant = False
            outcome = "MULTIPLE_RETRY_LABELS"
            reason = "more than the single mandated retry label is evidenced"
        elif eligible and terminal_evidence:
            compliant = True
            if complete_artifact:
                outcome = "COMPLETE_ARTIFACT"
            elif terminal_pool:
                outcome = f"TERMINAL_POOL_{pool_state}"
            else:
                outcome = f"TERMINAL_LOG_EXIT_{retry['engine_exit_code']}"
            reason = "eligible initial family has one terminal retry attempt"
        elif eligible:
            compliant = False
            outcome = "RETRY_MISSING_OR_NONTERMINAL"
            reason = "eligible initial family lacks a complete or terminal retry"
        elif any_retry_evidence or extra_paths:
            compliant = False
            outcome = "INELIGIBLE_RETRY_EVIDENCED"
            reason = "initial family has no literal STATUS=FAIL"
        else:
            compliant = True
            outcome = "NOT_REQUIRED"
            reason = "initial family has no literal STATUS=FAIL"
        compliance.append({
            "family": family,
            "initial_state": initial["output_state"],
            "initial_literal_fail_count": initial["literal_fail_count"],
            "initial_failed_cells": initial["failed_cells"],
            "eligible": eligible,
            "retry_label": f"{family}_retry",
            "complete_retry_artifact": complete_artifact,
            "terminal_pool_state": pool_state if terminal_pool else None,
            "terminal_log": terminal_log,
            "any_retry_evidence": any_retry_evidence,
            "extra_retry_evidence": extra_paths,
            "attempted": terminal_evidence,
            "outcome": outcome,
            "compliant": compliant,
            "reason": reason,
        })
    return compliance


def status_matrix(trig: str, fit_root: Path = FIT_ROOT,
                  log_root: Path | None = None,
                  repo_root: Path = REPO) -> dict:
    """Return the auditable family/model/block matrix for one P1 burst."""
    log_root = log_root or (repo_root / "logs" / "codex_campaign20" / "p1")
    family_root = fit_root / trig / "family_runs"
    labels = list(FAMILY_ORDER) + [f"{family}_retry" for family in FAMILY_ORDER]
    attempts = [
        _attempt_evidence(trig, label, family_root / label, log_root)
        for label in labels
    ]
    matrix = []
    for attempt in attempts:
        if attempt["output_state"] != "COMPLETE":
            continue
        family = attempt["family"]
        table, _, _, _ = _read_family(
            trig, family, Path(attempt["output_dir"]))
        for row in table:
            for prefix in FAMILY_PREFIXES[family]:
                matrix.append({
                    "attempt": attempt["label"],
                    "family": family,
                    "block": int(row["BLOCK"]),
                    "model": prefix,
                    "status": str(row[f"{prefix}_STATUS"]),
                    "usable": usable_model_cell(row, prefix),
                })

    blocks = (repo_root / "results" / "sweep106" / trig / "blocks" /
              f"bb_blocks_spectral_{trig}.ecsv")
    bkg = repo_root / "results" / "background_intervals.ecsv"
    engine = repo_root / "scripts" / "10_spectral_fit_burst.py"
    broadband = trig in BROADBAND_TRIGGERS
    initial = {a["family"]: a for a in attempts if a["label"] == a["family"]}
    return {
        "trigger": trig,
        "generated_utc": _utc_now(),
        "response_state": "RESPONSE_BLOCKED" if trig in RESPONSE_BLOCKED else "READY",
        "response_reason": RESPONSE_BLOCKED.get(trig),
        "registry": {
            family: {"prefixes": list(FAMILY_PREFIXES[family]),
                     "display_names": [MODEL_NAMES[p] for p in FAMILY_PREFIXES[family]]}
            for family in FAMILY_ORDER
        },
        "merge_priority": list(MERGE_PRIORITY),
        "attempts": attempts,
        "status_matrix": matrix,
        "authorities": {
            "merge_helper": _file_record(Path(__file__).resolve()),
            "engine": _file_record(engine),
            "blocks": _file_record(blocks),
            "background_catalog": _file_record(bkg),
        },
        "broadband_evidence": {
            "required": broadband,
            "initial_include_lat_commands": {
                family: initial[family]["include_lat_in_command"]
                for family in FAMILY_ORDER
            } if broadband else {},
            "initial_lle_approved_log_messages": {
                family: initial[family]["lle_approved_message_in_log"]
                for family in FAMILY_ORDER
            } if broadband else {},
            "initial_lle_sidecars": {
                family: initial[family]["lle_in_fit_dets"]
                for family in FAMILY_ORDER
            } if broadband else {},
            "initial_lat_plugin_blocks": {
                family: initial[family]["lat_plugin_blocks"]
                for family in FAMILY_ORDER
            } if broadband else {},
        },
        "provisional": True,
    }


def build_retry_worklist(triggers: list[str], output: Path,
                         fit_root: Path = FIT_ROOT,
                         log_root: Path | None = None,
                         repo_root: Path = REPO) -> dict:
    """Write exactly one retry per initial family containing literal FAIL."""
    unknown = [trig for trig in triggers if trig not in CAMPAIGN_TRIGGERS]
    assert not unknown, f"triggers outside campaign: {unknown}"
    entries = []
    decisions = []
    matrices = []
    for trig in triggers:
        matrix = status_matrix(trig, fit_root, log_root, repo_root)
        matrices.append(matrix)
        if trig in RESPONSE_BLOCKED:
            decisions.append({"trigger": trig, "decision": "RESPONSE_BLOCKED",
                              "reason": RESPONSE_BLOCKED[trig]})
            continue
        initial = {attempt["family"]: attempt for attempt in matrix["attempts"]
                   if attempt["label"] == attempt["family"]}
        for family in FAMILY_ORDER:
            attempt = initial[family]
            if attempt["output_state"] != "COMPLETE":
                decisions.append({
                    "trigger": trig, "family": family, "decision": "NO_RETRY",
                    "reason": f"initial family is {attempt['output_state']}; retry eligibility "
                              "requires a complete initial output with literal STATUS=FAIL",
                })
            elif int(attempt["literal_fail_count"]) > 0:
                label = f"{family}_retry"
                entries.append((trig, family, label))
                decisions.append({
                    "trigger": trig, "family": family, "decision": "RETRY_ONCE",
                    "label": label,
                    "literal_fail_count": attempt["literal_fail_count"],
                    "failed_cells": attempt["failed_cells"],
                })
            else:
                decisions.append({"trigger": trig, "family": family,
                                  "decision": "NO_RETRY",
                                  "reason": "initial family has no literal STATUS=FAIL"})

    lines = ["# trigger\tmodel_family\toutput_label"]
    lines.extend("\t".join(entry) for entry in entries)
    output.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(output, "\n".join(lines) + "\n")
    report = {
        "generated_utc": _utc_now(),
        "policy": "one retry iff the complete initial family has literal STATUS=FAIL",
        "triggers": triggers,
        "entries": [{"trigger": t, "family": f, "label": label}
                    for t, f, label in entries],
        "decisions": decisions,
        "worklist": _file_record(output),
        "matrix_sha256": hashlib.sha256(json.dumps(
            matrices, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "provisional": True,
    }
    report_path = output.with_suffix(output.suffix + ".json")
    _atomic_write_text(report_path, json.dumps(report, indent=2) + "\n")
    report["report"] = _file_record(report_path)
    return report


def _selection_lnn(row, prefixes: list[str]) -> float:
    """Recover ln(Ndata) from stored BIC/AIC, whose k includes nuisances."""
    vals = []
    for prefix in prefixes:
        n2ll = row[f"{prefix}_N2LL"]
        aic = row[f"{prefix}_AIC"]
        bic = row[f"{prefix}_BIC"]
        if not (finite(n2ll) and finite(aic) and finite(bic)):
            continue
        two_k = float(aic) - float(n2ll)
        if two_k > 0:
            vals.append(2.0 * (float(bic) - float(n2ll)) / two_k)
    if not vals:
        raise AssertionError("cannot recover ln(Ndata) for BIC winner recomputation")
    if max(vals) - min(vals) > 1e-5:
        raise AssertionError(f"inconsistent inferred ln(Ndata): {vals}")
    return float(np.median(vals))


def _nuisance_count_audit(row, prefixes: list[str]) -> float:
    """Assert AIC-N2LL contains one common nuisance count across models."""
    nuis = []
    for prefix in prefixes:
        if (str(row[f"{prefix}_STATUS"]).upper() != "OK"
                or not finite(row[f"{prefix}_N2LL"])
                or not finite(row[f"{prefix}_AIC"])):
            continue
        k_total = (float(row[f"{prefix}_AIC"]) - float(row[f"{prefix}_N2LL"])) / 2.0
        nuis.append(k_total - SOURCE_K[prefix])
    if not nuis:
        raise AssertionError(f"block {row['BLOCK']}: no successful model for nuisance audit")
    if max(nuis) - min(nuis) > 1e-6:
        raise AssertionError(f"block {row['BLOCK']}: inconsistent nuisance counts {nuis}")
    if abs(nuis[0] - round(nuis[0])) > 1e-6:
        raise AssertionError(f"block {row['BLOCK']}: non-integral nuisance count {nuis[0]}")
    return float(nuis[0])


def _bound_and_sharpness_stamps(row, prefixes: list[str]) -> tuple[str, str]:
    """Reproduce scripts/10's two row-level rail diagnostics after repairs."""
    rail_at: dict[float, list[str]] = {}
    for prefix in prefixes:
        if str(row[f"{prefix}_STATUS"]).upper() != "OK":
            continue
        if prefix == "BANDRCPL":
            peak = ("EP", 2000.0)
        elif prefix.startswith("BAND"):
            peak = ("EP", 50000.0)
        elif prefix.startswith("DSBPL"):
            peak = ("XP", 50000.0)
        elif prefix.startswith("SBPL"):
            peak = ("EBREAK", 50000.0)
        else:
            peak = None
        if peak is not None:
            suffix, hi = peak
            col = f"{prefix}_{suffix}"
            if col in row.colnames and finite(row[col]) and float(row[col]) >= 0.98 * hi:
                rail_at.setdefault(hi, []).append(MODEL_NAMES[prefix])
    bound = [f"{hi:g}:{'+'.join(sorted(set(names)))}"
             for hi, names in rail_at.items() if len(set(names)) >= 2]

    sharp = []
    if "SBPLF" in prefixes and str(row["SBPLF_STATUS"]).upper() == "OK":
        v = row["SBPLF_SCALE"]
        if finite(v) and ((float(v) - 0.01) < 0.02 * 1.99
                          or (2.0 - float(v)) < 0.02 * 1.99):
            sharp.append(f"SBPLfree:SCALE@{float(v):g}")
    if "DSBPLF" in prefixes and str(row["DSBPLF_STATUS"]).upper() == "OK":
        for suffix in ("N1", "N2"):
            v = row[f"DSBPLF_{suffix}"]
            if finite(v) and ((float(v) - 0.5) < 0.02 * 9.5
                              or (10.0 - float(v)) < 0.02 * 9.5):
                sharp.append(f"DSBPLfree:{suffix}@{float(v):g}")
    return ";".join(bound), ";".join(sharp)


def _recompute_selection(table: Table, prefixes: list[str]) -> None:
    """Recompute engine selection summaries after a row-level repair merge."""
    lrt_pairs = {
        "LRT_BANDBB_BAND": ("BAND", "BANDBB"),
        "LRT_CPLBB_CPL": ("CPL", "CPLBB"),
        "LRT_DSBPL_SBPL": ("SBPL", "DSBPL"),
    }
    best_aic_values = []
    best_bic_values = []
    lrt_invalid_values = []
    bound_values = []
    sharp_values = []
    for row in table:
        _nuisance_count_audit(row, prefixes)
        ln_n = _selection_lnn(row, prefixes)
        valid = [
            p for p in prefixes
            if str(row[f"{p}_STATUS"]).upper() == "OK"
            and _truthy(row[f"{p}_VALID"])
            and finite(row[f"{p}_N2LL"])
        ]
        best_aic_values.append(MODEL_NAMES[min(
            valid, key=lambda p: float(row[f"{p}_N2LL"]) + 2 * SOURCE_K[p]
        )] if valid else "INCONCLUSIVE")
        best_bic_values.append(MODEL_NAMES[min(
            valid, key=lambda p: float(row[f"{p}_N2LL"]) + SOURCE_K[p] * ln_n
        )] if valid else "INCONCLUSIVE")
        invalid = []
        for target, (parent, child) in lrt_pairs.items():
            if (str(row[f"{parent}_STATUS"]).upper() == "OK"
                    and str(row[f"{child}_STATUS"]).upper() == "OK"
                    and finite(row[f"{parent}_N2LL"])
                    and finite(row[f"{child}_N2LL"])):
                value = float(row[f"{parent}_N2LL"]) - float(row[f"{child}_N2LL"])
                if value < -0.5:
                    invalid.append(f"{target}={value:.2f}")
                    value = float("nan")
            else:
                value = float("nan")
            row[target] = value
        lrt_invalid_values.append(";".join(invalid))
        bound, sharp = _bound_and_sharpness_stamps(row, prefixes)
        bound_values.append(bound)
        sharp_values.append(sharp)

    _replace_string_column(table, "BEST_AIC_MODEL", best_aic_values, width=32)
    _replace_string_column(table, "BEST_BIC_MODEL", best_bic_values, width=32)
    _replace_string_column(table, "LRT_INVALID", lrt_invalid_values, width=512)
    _replace_string_column(table, "BOUND_CAPPED", bound_values, width=512)
    _replace_string_column(table, "SHARPNESS_CAPPED", sharp_values, width=512)


def _normal(value):
    """Stable scalar form for exact context comparisons, including masks."""
    if np.ma.is_masked(value):
        return "<MASKED>"
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return str(value)


def _same_scalar(left, right) -> bool:
    a, b = _normal(left), _normal(right)
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return a == b
    return a == b


def _json_equal(key: str, left, right) -> bool:
    if key == "blocks_file":
        return Path(left).resolve() == Path(right).resolve()
    if key in {"bin_starts", "bin_stops"}:
        return np.allclose(np.asarray(left, float), np.asarray(right, float),
                           rtol=0.0, atol=1e-9)
    return left == right


def _preflight_family(base: Table, base_meta: dict, other: Table,
                      other_meta: dict, source: Path) -> None:
    """Fail closed unless a family output describes the identical likelihood rows."""
    bblocks = [int(v) for v in base["BLOCK"]]
    oblocks = [int(v) for v in other["BLOCK"]]
    assert len(set(bblocks)) == len(bblocks), f"duplicate base blocks: {bblocks}"
    assert len(set(oblocks)) == len(oblocks), f"duplicate incoming blocks: {oblocks}"
    assert sorted(oblocks) == sorted(bblocks), (source, oblocks, bblocks)
    bidx = {int(v): i for i, v in enumerate(base["BLOCK"])}
    oidx = {int(v): i for i, v in enumerate(other["BLOCK"])}
    context = ("T_START", "T_STOP", "T_MID", "N_DETS", "PLUGIN_DETS",
               "EAC_DETS", "EAC_SKIPPED")
    for col in context:
        assert col in base.colnames and col in other.colnames, (source, col)
    for block in sorted(bidx):
        for col in context:
            bv = _normal(base[col][bidx[block]])
            ov = _normal(other[col][oidx[block]])
            if isinstance(bv, float) and isinstance(ov, float):
                assert abs(bv - ov) <= 1e-9, (source, block, col, bv, ov)
            else:
                assert bv == ov, (source, block, col, bv, ov)

    immutable = ("trigger", "canonical_det", "reference_det", "grid_type",
                 "blocks_file", "fit_dets", "n_blocks", "NAI_RANGES",
                 "NAI_EXCLUDE", "BGO_RANGES", "LLE_RANGES",
                 "RANGES_CONVENTION", "bin_starts", "bin_stops")
    for key in immutable:
        assert key in base_meta and key in other_meta, (source, key)
        assert _json_equal(key, base_meta[key], other_meta[key]), (
            source, key, base_meta[key], other_meta[key])

    incoming_prefixes = model_prefixes(other)
    assert set(incoming_prefixes).issubset(HIGHE_PREFIXES), (
        source, incoming_prefixes)
    expected_models = [MODEL_NAMES[p] for p in incoming_prefixes]
    assert other_meta.get("models") == expected_models, (
        source, other_meta.get("models"), expected_models)


def _discover_merge_candidates(trig: str, family_root: Path,
                               base: Table, base_meta: dict) -> tuple[list[Path], list[dict]]:
    """Select only complete family outputs from the identical likelihood rows."""
    incoming = []
    discovery = []
    for label in MERGE_PRIORITY:
        family = _family_from_label(label)
        directory = family_root / label
        try:
            other, other_meta, ecsv, sidecar = _read_family(trig, family, directory)
            _preflight_family(base, base_meta, other, other_meta, directory)
            state = "COMPLETE_COMPATIBLE"
            incoming.append(directory)
            reason = None
            hashes = {"ecsv_sha256": sha256(ecsv), "json_sha256": sha256(sidecar)}
        except Exception as exc:
            exists = ((directory / "spectral_fits.ecsv").exists()
                      or (directory / "spectral_fits.json").exists())
            state = "EXCLUDED_INCOMPATIBLE" if exists else "EXCLUDED_MISSING"
            reason = f"{type(exc).__name__}: {exc}"
            hashes = {
                "ecsv_sha256": (sha256(directory / "spectral_fits.ecsv")
                                if (directory / "spectral_fits.ecsv").is_file() else None),
                "json_sha256": (sha256(directory / "spectral_fits.json")
                                if (directory / "spectral_fits.json").is_file() else None),
            }
        discovery.append({
            "label": label, "family": family, "dir": str(directory),
            "state": state, "reason": reason, **hashes,
        })
    return incoming, discovery


def _add_missing_prefix_column(table: Table, other: Table, col: str) -> None:
    """Add a model-specific column that exists only in a successful retry."""
    src = other[col]
    kind = src.dtype.kind
    if kind in "iufc":
        values = np.full(len(table), np.nan, dtype=float)
    elif kind == "b":
        values = np.zeros(len(table), dtype=bool)
    else:
        width = max(32, int(getattr(src.dtype, "itemsize", 32) // 4))
        values = np.asarray([""] * len(table), dtype=f"U{width}")
    table.add_column(Column(values, name=col))


def merge_repairs(trig: str, base_dir: Path, incoming_dirs: list[Path],
                  fit_root: Path = FIT_ROOT,
                  staging_dir: Path | None = None,
                  log_root: Path | None = None,
                  repo_root: Path = REPO) -> dict:
    """Stage a content-addressed 24-model table without mutating its highe base.

    Only a literal ``FAIL`` in the immutable highe base can be replaced, and
    only by a fully usable ``OK`` cell.  Incoming runs are sorted by the locked
    priority rather than by caller order.
    """
    if trig in RESPONSE_BLOCKED:
        raise AssertionError(f"{trig}: {RESPONSE_BLOCKED[trig]}")
    assert base_dir.name == "highe", (
        "the immutable base must be the initial highe directory", base_dir)
    table, meta, base_ecsv, base_json = _read_family(trig, "highe", base_dir)
    base_original = table.copy(copy_data=True)
    base_hashes_before = {"ecsv": sha256(base_ecsv), "json": sha256(base_json)}
    prefixes = list(HIGHE_PREFIXES)
    by_block = {int(row["BLOCK"]): i for i, row in enumerate(table)}
    assert len(by_block) == len(table), "duplicate blocks in highe base"
    for row in table:
        for prefix in prefixes:
            assert str(row[f"{prefix}_STATUS"]) in {"OK", "FAIL"}, (
                trig, row["BLOCK"], prefix, row[f"{prefix}_STATUS"])

    family_root = base_dir.parent
    log_root = log_root or (repo_root / "logs" / "codex_campaign20" / "p1")
    all_labels = list(FAMILY_ORDER) + [f"{family}_retry" for family in FAMILY_ORDER]
    attempt_evidence = [
        _attempt_evidence(trig, label, family_root / label, log_root)
        for label in all_labels
    ]
    declared_models = list(meta.get("models") or [])
    aic_cols = {c[:-4] for c in table.colnames if c.endswith("_AIC")}
    base_model_complete = bool(declared_models) and len(aic_cols) >= len(declared_models)
    retry_compliance = _retry_compliance(
        trig, attempt_evidence, family_root, log_root,
        base_model_complete=base_model_complete)
    noncompliant = [entry for entry in retry_compliance if not entry["compliant"]]
    assert not noncompliant, ("P1 retry contract is incomplete", trig, noncompliant)
    compatible_dirs, discovery = _discover_merge_candidates(
        trig, family_root, table, meta)

    incoming_by_label = {}
    for directory in incoming_dirs:
        label = directory.name
        assert label in MERGE_PRIORITY, ("incoming label not in locked priority", label)
        assert label not in incoming_by_label, ("duplicate incoming label", label)
        incoming_by_label[label] = directory
    expected_incoming = {directory.name: directory for directory in compatible_dirs}
    assert set(incoming_by_label) == set(expected_incoming), (
        "all and only complete, likelihood-compatible priority inputs must be merged",
        sorted(incoming_by_label), sorted(expected_incoming))
    for label, directory in incoming_by_label.items():
        assert directory.resolve() == expected_incoming[label].resolve(), (
            "incoming path is not the discovered family artifact", label,
            directory, expected_incoming[label])
    ordered_labels = [label for label in MERGE_PRIORITY if label in incoming_by_label]
    ordered_dirs = [incoming_by_label[label] for label in ordered_labels]

    source_records = [{
        "label": "highe", "family": "highe", "role": "immutable_highe_base",
        "dir": str(base_dir), "ecsv_sha256": base_hashes_before["ecsv"],
        "json_sha256": base_hashes_before["json"],
    }]
    source_tables = {}
    for label, incoming_dir in zip(ordered_labels, ordered_dirs):
        family = _family_from_label(label)
        other, other_meta, incoming_ecsv, incoming_json = _read_family(
            trig, family, incoming_dir)
        _preflight_family(table, meta, other, other_meta, incoming_dir)
        if label.endswith("_retry"):
            initial_dir = incoming_dir.parent / family
            initial, _, _, _ = _read_family(trig, family, initial_dir)
            assert any(str(initial[f"{prefix}_STATUS"][i]) == "FAIL"
                       for prefix in FAMILY_PREFIXES[family]
                       for i in range(len(initial))), (
                "retry exists without an eligible literal FAIL in its initial family",
                trig, family, incoming_dir)
        source_tables[label] = other
        source_records.append({
            "label": label, "family": family, "role": "repair_candidate",
            "priority": MERGE_PRIORITY.index(label), "dir": str(incoming_dir),
            "ecsv_sha256": sha256(incoming_ecsv),
            "json_sha256": sha256(incoming_json),
        })

    repairs = []
    unused_eligible = []
    selected_by = {}
    for label in ordered_labels:
        incoming_dir = incoming_by_label[label]
        other = source_tables[label]
        other_prefixes = list(FAMILY_PREFIXES[_family_from_label(label)])
        for other_row in other:
            block = int(other_row["BLOCK"])
            assert block in by_block
            i = by_block[block]
            old = base_original[i]
            for prefix in other_prefixes:
                # Eligibility is anchored to the immutable highe result, not
                # to a previously merged transient row.
                if str(old[f"{prefix}_STATUS"]) != "FAIL":
                    continue
                if not usable_model_cell(other_row, prefix):
                    continue
                pair = (block, prefix)
                if pair in selected_by:
                    unused_eligible.append({
                        "block": block, "model": prefix, "from": str(incoming_dir),
                        "label": label, "reason": "higher-priority usable repair selected",
                        "selected_from": selected_by[pair],
                    })
                    continue
                copied = []
                lead = prefix + "_"
                for col in other.colnames:
                    if not col.startswith(lead):
                        continue
                    if col not in table.colnames:
                        _add_missing_prefix_column(table, other, col)
                    table[col][i] = other_row[col]
                    copied.append(col)
                assert usable_model_cell(table[i], prefix), (label, block, prefix)
                selected_by[pair] = label
                repairs.append({
                    "block": block, "model": prefix, "from": str(incoming_dir),
                    "label": label, "columns": len(copied),
                })

    _recompute_selection(table, prefixes)
    original_by_block = {int(row["BLOCK"]): row for row in base_original}
    unresolved = []
    for row in table:
        block = int(row["BLOCK"])
        old = original_by_block[block]
        for prefix in prefixes:
            if str(old[f"{prefix}_STATUS"]) == "OK":
                for col in base_original.colnames:
                    if col.startswith(prefix + "_"):
                        assert _same_scalar(row[col], old[col]), (
                            "successful highe cell changed", block, prefix, col,
                            _normal(old[col]), _normal(row[col]))
            elif not usable_model_cell(row, prefix):
                unresolved.append({
                    "block": block, "model": prefix,
                    "status": str(row[f"{prefix}_STATUS"]),
                    "attempts": {
                        label: str(source_tables[label][
                            [int(v) for v in source_tables[label]["BLOCK"]].index(block)
                        ][f"{prefix}_STATUS"])
                        for label in ordered_labels
                        if prefix in FAMILY_PREFIXES[_family_from_label(label)]
                    },
                })

    source_matrix = []
    for label, other in [("highe", base_original)] + [
            (label, source_tables[label]) for label in ordered_labels]:
        family = _family_from_label(label)
        for row in other:
            for prefix in FAMILY_PREFIXES[family]:
                source_matrix.append({
                    "attempt": label, "family": family, "block": int(row["BLOCK"]),
                    "model": prefix, "status": str(row[f"{prefix}_STATUS"]),
                    "usable": usable_model_cell(row, prefix),
                })
    attempt_status_matrix = []
    for attempt in attempt_evidence:
        if attempt["output_state"] != "COMPLETE":
            continue
        label = attempt["label"]
        family = attempt["family"]
        other, _, _, _ = _read_family(
            trig, family, Path(attempt["output_dir"]))
        for row in other:
            for prefix in FAMILY_PREFIXES[family]:
                attempt_status_matrix.append({
                    "attempt": label, "family": family,
                    "block": int(row["BLOCK"]), "model": prefix,
                    "status": str(row[f"{prefix}_STATUS"]),
                    "usable": usable_model_cell(row, prefix),
                })

    blocks_path = Path(meta["blocks_file"])
    if not blocks_path.is_absolute():
        blocks_path = repo_root / blocks_path
    authorities = {
        "merge_helper": _file_record(Path(__file__).resolve()),
        "engine": _file_record(repo_root / "scripts" / "10_spectral_fit_burst.py"),
        "blocks": _file_record(blocks_path),
        "background_catalog": _file_record(repo_root / "results" /
                                             "background_intervals.ecsv"),
    }
    fingerprint_payload = {
        "policy": MERGE_POLICY_VERSION,
        "trigger": trig,
        "priority": ordered_labels,
        "sources": [{key: source[key] for key in
                     ("label", "family", "ecsv_sha256", "json_sha256")}
                    for source in source_records],
        "attempts": [{
            "label": attempt["label"],
            "output_state": attempt["output_state"],
            "ecsv_sha256": attempt["ecsv"]["sha256"],
            "json_sha256": attempt["json"]["sha256"],
            "log_sha256": attempt["log"]["sha256"],
            "pool_status_sha256": attempt["pool_status"]["sha256"],
            "engine_exit_code": attempt["engine_exit_code"],
            "finished_utc": attempt["finished_utc"],
        } for attempt in attempt_evidence],
        "retry_compliance": retry_compliance,
        "discovery": discovery,
        "authorities": {key: value["sha256"] for key, value in authorities.items()},
    }
    fingerprint = hashlib.sha256(json.dumps(
        fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    stage_root = staging_dir or (fit_root / trig / "merge_staging")
    out_dir = stage_root / fingerprint
    stage_root.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix=".building-", dir=stage_root))
    out_ecsv = tmp_dir / "spectral_fits.ecsv"
    out_json = tmp_dir / "spectral_fits.json"
    try:
        table.write(out_ecsv, format="ascii.ecsv", overwrite=False)
        assert meta["models"] == [MODEL_NAMES[p] for p in prefixes]
        meta["campaign_merge"] = {
            "policy_version": MERGE_POLICY_VERSION,
            "input_fingerprint": fingerprint,
            "base": str(base_dir),
            "incoming_priority": [str(p) for p in ordered_dirs],
            "retry_compliance": retry_compliance,
            "discovery": discovery,
            "repairs": repairs,
            "unused_eligible": unused_eligible,
            "unresolved": unresolved,
        }
        _atomic_write_text(out_json, json.dumps(meta, indent=2, default=float) + "\n")

        check, check_meta, _, _ = _read_family(trig, "highe", tmp_dir)
        assert check_meta["campaign_merge"]["input_fingerprint"] == fingerprint
        assert [int(v) for v in check["BLOCK"]] == [int(v) for v in table["BLOCK"]]
        for col in ("BEST_AIC_MODEL", "BEST_BIC_MODEL", "LRT_INVALID",
                    "BOUND_CAPPED", "SHARPNESS_CAPPED"):
            assert _text_values(check[col]) == _text_values(table[col]), col
        assert [str(v) for v in check["PLUGIN_DETS"]] == [
            str(v) for v in base_original["PLUGIN_DETS"]]

        manifest = {
            "trigger": trig,
            "generated_utc": _utc_now(),
            "policy_version": MERGE_POLICY_VERSION,
            "input_fingerprint": fingerprint,
            "stage_dir": str(out_dir),
            "base": str(base_ecsv),
            "incoming": [str(p / "spectral_fits.ecsv") for p in ordered_dirs],
            "incoming_priority": ordered_labels,
            "sources": source_records,
            "source_status_matrix": source_matrix,
            "attempt_status_matrix": attempt_status_matrix,
            "attempt_evidence": attempt_evidence,
            "retry_compliance": retry_compliance,
            "discovery": discovery,
            "authorities": authorities,
            "broadband_evidence": {
                "required": trig in BROADBAND_TRIGGERS,
                "include_lat_commands": {
                    a["label"]: a["include_lat_in_command"] for a in attempt_evidence},
                "lle_approved_log_messages": {
                    a["label"]: a["lle_approved_message_in_log"] for a in attempt_evidence},
                "lle_sidecars": {
                    a["label"]: a["lle_in_fit_dets"] for a in attempt_evidence},
                "lat_plugin_blocks": {
                    a["label"]: a["lat_plugin_blocks"] for a in attempt_evidence},
            },
            "repairs": repairs,
            "unused_eligible": unused_eligible,
            "unresolved": unresolved,
            "models": len(prefixes),
            "model_prefixes": prefixes,
            "model_display_names": [MODEL_NAMES[p] for p in prefixes],
            "rows": len(table),
            "blocks": [int(v) for v in table["BLOCK"]],
            "ecsv_sha256": sha256(out_ecsv),
            "json_sha256": sha256(out_json),
            "immutable_base_hashes_before": base_hashes_before,
            "promotion_target": str(fit_root / trig),
            "provisional": True,
        }
        _atomic_write_text(tmp_dir / "family_merge_manifest.json",
                           json.dumps(manifest, indent=2) + "\n")
        assert {"ecsv": sha256(base_ecsv), "json": sha256(base_json)} == base_hashes_before
        if out_dir.exists():
            existing = json.loads((out_dir / "family_merge_manifest.json").read_text())
            assert existing["input_fingerprint"] == fingerprint
            assert existing["ecsv_sha256"] == sha256(out_dir / "spectral_fits.ecsv")
            assert existing["json_sha256"] == sha256(out_dir / "spectral_fits.json")
            assert existing["ecsv_sha256"] == manifest["ecsv_sha256"]
            assert existing["json_sha256"] == manifest["json_sha256"]
            shutil.rmtree(tmp_dir)
            return existing
        os.replace(tmp_dir, out_dir)
        return manifest
    except BaseException:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        raise


def stage_p1(trig: str, fit_root: Path = FIT_ROOT,
             staging_dir: Path | None = None,
             log_root: Path | None = None,
             repo_root: Path = REPO) -> dict:
    """Discover complete family attempts and stage them in locked priority."""
    if trig in RESPONSE_BLOCKED:
        raise AssertionError(f"{trig}: {RESPONSE_BLOCKED[trig]}")
    family_root = fit_root / trig / "family_runs"
    base_dir = family_root / "highe"
    base, base_meta, _, _ = _read_family(trig, "highe", base_dir)
    incoming, _ = _discover_merge_candidates(
        trig, family_root, base, base_meta)
    return merge_repairs(
        trig, base_dir, incoming, fit_root=fit_root, staging_dir=staging_dir,
        log_root=log_root, repo_root=repo_root)


def _validate_stage(trig: str, stage_dir: Path,
                    repo_root: Path = REPO) -> tuple[dict, Table, dict]:
    manifest_path = stage_dir / "family_merge_manifest.json"
    assert manifest_path.is_file(), ("missing stage manifest", stage_dir)
    manifest = json.loads(manifest_path.read_text())
    assert manifest.get("trigger") == trig
    assert manifest.get("policy_version") == MERGE_POLICY_VERSION
    fingerprint = manifest.get("input_fingerprint")
    assert fingerprint and stage_dir.name == fingerprint, (
        "stage is not in its content-addressed directory", stage_dir, fingerprint)
    table, meta, ecsv, sidecar = _read_family(trig, "highe", stage_dir)
    assert sha256(ecsv) == manifest["ecsv_sha256"]
    assert sha256(sidecar) == manifest["json_sha256"]
    assert tuple(model_prefixes(table)) == HIGHE_PREFIXES
    assert meta.get("campaign_merge", {}).get("input_fingerprint") == fingerprint

    base = next(source for source in manifest["sources"]
                if source["role"] == "immutable_highe_base")
    base_dir = Path(base["dir"])
    assert sha256(base_dir / "spectral_fits.ecsv") == base["ecsv_sha256"], (
        "immutable highe base changed after staging", base_dir)
    assert sha256(base_dir / "spectral_fits.json") == base["json_sha256"], (
        "immutable highe sidecar changed after staging", base_dir)
    for authority in manifest["authorities"].values():
        if authority["exists"]:
            path = Path(authority["path"])
            assert path.is_file() and sha256(path) == authority["sha256"], (
                "authority changed after staging", path)
    return manifest, table, meta


def _copy_to_temp(source: Path, target: Path) -> Path:
    """Copy next to target and fsync, ready for a same-filesystem replace."""
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.promote-", dir=target.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        shutil.copy2(source, tmp)
        with tmp.open("rb") as stream:
            os.fsync(stream.fileno())
        assert sha256(tmp) == sha256(source)
        return tmp
    except BaseException:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def promote_stage(trig: str, stage_dir: Path, fit_root: Path = FIT_ROOT,
                  repo_root: Path = REPO,
                  broadband_degradation_reason: str | None = None) -> dict:
    """Backup and atomically replace the canonical ECSV/JSON pair.

    POSIX has no two-file transaction.  Each file is replaced atomically and
    any failure rolls the pair back from the content-addressed backup.
    """
    if trig in RESPONSE_BLOCKED:
        raise AssertionError(f"{trig}: {RESPONSE_BLOCKED[trig]}")
    manifest, table, meta = _validate_stage(trig, stage_dir, repo_root)
    plugins = [str(v).split(",") for v in table["PLUGIN_DETS"]]
    broadband_problem = None
    if trig in BROADBAND_TRIGGERS:
        if "lle" not in [str(v) for v in meta.get("fit_dets", [])] or not all(
                "lle" in dets for dets in plugins):
            broadband_problem = "LLE absent from sidecar or at least one spectrum"
        elif not any("LAT" in dets for row, dets in zip(table, plugins)
                     if int(row["BLOCK"]) >= 0):
            broadband_problem = "LAT plugin absent from every resolved spectrum"
    if broadband_problem:
        assert broadband_degradation_reason, (
            broadband_problem,
            "promotion requires an explicit --broadband-degradation-reason")

    target = fit_root / trig
    target.mkdir(parents=True, exist_ok=True)
    lock = target / ".campaign_products_promotion.lock"
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(f"promotion lock already exists: {lock}") from exc
    os.write(lock_fd, f"pid={os.getpid()} utc={_utc_now()}\n".encode())
    os.close(lock_fd)

    source_ecsv = stage_dir / "spectral_fits.ecsv"
    source_json = stage_dir / "spectral_fits.json"
    target_ecsv = target / "spectral_fits.ecsv"
    target_json = target / "spectral_fits.json"
    previous_exists = target_ecsv.exists() or target_json.exists()
    assert target_ecsv.exists() == target_json.exists(), (
        "canonical pair is incomplete; refusing promotion", target)
    previous = None
    backup_dir = None
    tmp_ecsv = tmp_json = None
    try:
        if previous_exists:
            previous = {"ecsv_sha256": sha256(target_ecsv),
                        "json_sha256": sha256(target_json)}
            if (previous["ecsv_sha256"] == manifest["ecsv_sha256"]
                    and previous["json_sha256"] == manifest["json_sha256"]):
                return {
                    "trigger": trig, "status": "ALREADY_PROMOTED",
                    "stage_dir": str(stage_dir), "target": str(target),
                    "ecsv_sha256": previous["ecsv_sha256"],
                    "json_sha256": previous["json_sha256"],
                }
            backup_key = hashlib.sha256(
                f"{previous['ecsv_sha256']}:{previous['json_sha256']}".encode()
            ).hexdigest()
            backup_dir = target / "promotion_backups" / backup_key
            if backup_dir.exists():
                assert sha256(backup_dir / "spectral_fits.ecsv") == previous["ecsv_sha256"]
                assert sha256(backup_dir / "spectral_fits.json") == previous["json_sha256"]
            else:
                backup_dir.parent.mkdir(parents=True, exist_ok=True)
                tmp_backup = Path(tempfile.mkdtemp(
                    prefix=".backup-", dir=backup_dir.parent))
                shutil.copy2(target_ecsv, tmp_backup / "spectral_fits.ecsv")
                shutil.copy2(target_json, tmp_backup / "spectral_fits.json")
                backup_manifest = {
                    "trigger": trig, "created_utc": _utc_now(),
                    "source": str(target), **previous,
                }
                _atomic_write_text(tmp_backup / "backup_manifest.json",
                                   json.dumps(backup_manifest, indent=2) + "\n")
                os.replace(tmp_backup, backup_dir)

        tmp_ecsv = _copy_to_temp(source_ecsv, target_ecsv)
        tmp_json = _copy_to_temp(source_json, target_json)
        os.replace(tmp_ecsv, target_ecsv)
        tmp_ecsv = None
        os.replace(tmp_json, target_json)
        tmp_json = None
        assert sha256(target_ecsv) == manifest["ecsv_sha256"]
        assert sha256(target_json) == manifest["json_sha256"]
        validate_result = validate(
            trig, 24, trig in BROADBAND_TRIGGERS,
            trig in BROADBAND_TRIGGERS and broadband_problem is None,
            fit_root=fit_root)
        receipt = {
            "trigger": trig, "status": "PROMOTED", "promoted_utc": _utc_now(),
            "stage_dir": str(stage_dir),
            "input_fingerprint": manifest["input_fingerprint"],
            "target": str(target), "backup_dir": str(backup_dir) if backup_dir else None,
            "previous": previous,
            "ecsv_sha256": manifest["ecsv_sha256"],
            "json_sha256": manifest["json_sha256"],
            "validation": validate_result,
            "broadband_degradation": broadband_problem,
            "broadband_degradation_reason": broadband_degradation_reason,
            "provisional": True,
        }
        receipt_dir = target / "promotion_receipts"
        receipt_path = receipt_dir / f"{manifest['input_fingerprint']}.json"
        _atomic_write_text(receipt_path, json.dumps(receipt, indent=2) + "\n")
        receipt["receipt"] = _file_record(receipt_path)
        return receipt
    except BaseException:
        # Roll back only the two explicitly targeted canonical files.
        if previous is not None and backup_dir is not None:
            rollback_ecsv = _copy_to_temp(backup_dir / "spectral_fits.ecsv", target_ecsv)
            rollback_json = _copy_to_temp(backup_dir / "spectral_fits.json", target_json)
            os.replace(rollback_ecsv, target_ecsv)
            os.replace(rollback_json, target_json)
        elif not previous_exists:
            for path in (target_ecsv, target_json):
                if path.exists():
                    path.unlink()
        raise
    finally:
        for tmp in (tmp_ecsv, tmp_json):
            if tmp is not None and tmp.exists():
                tmp.unlink()
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def validate(trig: str, expected: int, require_lle: bool, require_lat: bool,
             fit_root: Path = FIT_ROOT) -> dict:
    table, meta, ecsv, sidecar = load_fit(trig, fit_root)
    prefixes = model_prefixes(table)
    blocks = sorted(int(v) for v in table["BLOCK"])
    expected_blocks = [-1] + list(range(int(meta["n_blocks"])))
    failures = []
    for row in table:
        for prefix in prefixes:
            if not usable_model_cell(row, prefix):
                failures.append({"block": int(row["BLOCK"]), "model": prefix,
                                 "status": str(row[f"{prefix}_STATUS"])})

    assert len(prefixes) == expected, (len(prefixes), expected, prefixes)
    if expected == 24:
        assert tuple(prefixes) == HIGHE_PREFIXES, prefixes
    assert len(table) == int(meta["n_blocks"]) + 1
    assert blocks == expected_blocks, (blocks, expected_blocks)
    assert meta["trigger"] == trig
    assert meta.get("models") == [MODEL_NAMES[p] for p in prefixes], (
        meta.get("models"), [MODEL_NAMES[p] for p in prefixes])
    if require_lle:
        assert "lle" in meta.get("fit_dets", [])
        assert all("lle" in str(v).split(",") for v in table["PLUGIN_DETS"])
    if require_lat:
        resolved = [str(r["PLUGIN_DETS"]).split(",") for r in table
                    if int(r["BLOCK"]) >= 0]
        assert any("LAT" in dets for dets in resolved), resolved

    result = {
        "trigger": trig,
        "rows": len(table),
        "models": len(prefixes),
        "prefixes": prefixes,
        "failures": failures,
        "fit_dets": list(meta.get("fit_dets", [])),
        "lat_blocks": [int(r["BLOCK"]) for r in table
                       if "LAT" in str(r["PLUGIN_DETS"]).split(",")],
        "ecsv_sha256": sha256(ecsv),
        "json_sha256": sha256(sidecar),
    }
    return result


def parameter_bases(table: Table, prefix: str) -> list[str]:
    bases = []
    lead = prefix + "_"
    for col in table.colnames:
        if not col.startswith(lead):
            continue
        suffix = col[len(lead):]
        if suffix in RESERVED_SUFFIXES or suffix.startswith("EAC_"):
            continue
        if suffix.endswith("_ERR") or suffix.endswith("_NEG_ERR") or suffix.endswith("_POS_ERR"):
            continue
        bases.append(suffix)
    return bases


def value_with_error(row, prefix: str, base: str, cols: set[str]) -> str:
    key = f"{prefix}_{base}"
    value = fmt(row[key])
    neg_key = key + "_NEG_ERR"
    pos_key = key + "_POS_ERR"
    err_key = key + "_ERR"
    if neg_key in cols and pos_key in cols and finite(row[neg_key]) and finite(row[pos_key]):
        return f"{base}={value} -{fmt(abs(float(row[neg_key])))}/+{fmt(abs(float(row[pos_key])))}"
    if err_key in cols and finite(row[err_key]):
        return f"{base}={value} ±{fmt(abs(float(row[err_key])))}"
    return f"{base}={value}"


def row_parameters(row, table: Table, prefix: str) -> str:
    cols = set(table.colnames)
    if str(row[f"{prefix}_STATUS"]).upper() != "OK":
        return f"STATUS={row[f'{prefix}_STATUS']} (no finite fitted solution)"
    pieces = [value_with_error(row, prefix, base, cols)
              for base in parameter_bases(table, prefix)]
    for col in table.colnames:
        lead = prefix + "_EAC_"
        if col.startswith(lead) and not col.endswith("_ERR"):
            pieces.append(f"EAC_{col[len(lead):].lower()}={fmt(row[col])}")
    return "; ".join(pieces) if pieces else "no stored parameters"


def table_text(table: Table, row, prefixes: list[str]) -> str:
    block = int(row["BLOCK"])
    tag = "TINT" if block < 0 else f"bin{block}"
    winner = winner_prefix(row["BEST_AIC_MODEL"])
    finite_aics = [float(row[f"{p}_AIC"]) for p in prefixes
                   if finite(row[f"{p}_AIC"])]
    amin = min(finite_aics) if finite_aics else float("nan")
    ordered = sorted(prefixes,
                     key=lambda p: float(row[f"{p}_AIC"])
                     if finite(row[f"{p}_AIC"]) else float("inf"))
    lines = [
        f"# {tag}  [{float(row['T_START']):.2f}, {float(row['T_STOP']):.2f}] s — all 24 models (AIC-sorted)",
        "",
        "| model | AIC | dAIC | valid | parameters |",
        "|---|---|---|---|---|",
    ]
    for prefix in ordered:
        aic = row[f"{prefix}_AIC"]
        daic = float(aic) - amin if finite(aic) and finite(amin) else float("nan")
        valid = (str(row[f"{prefix}_STATUS"]).upper() == "OK" and
                 str(row[f"{prefix}_VALID"]).lower() in {"true", "1", "1.0"} and
                 finite(aic))
        marker = " **(winner)**" if prefix == winner else ""
        lines.append(
            f"| {prefix}{marker} | {fmt(aic)} | {fmt(daic)} | "
            f"{'yes' if valid else 'NO'} | {row_parameters(row, table, prefix)} |"
        )
    lines += [
        "",
        f"Engine valid winner: `{winner}`. Failed or invalid models remain in the table; "
        "dAIC is referenced to the lowest finite raw AIC for transparency.",
        "",
    ]
    assert len(ordered) == 24
    assert sum(" **(winner)**" in line for line in lines) == 1
    return "\n".join(lines)


def make_tables(trig: str, fit_root: Path = FIT_ROOT) -> dict:
    table, meta, ecsv, _ = load_fit(trig, fit_root)
    prefixes = model_prefixes(table)
    assert len(prefixes) == 24, prefixes
    out = fit_root / f"sed_grid_{trig}" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    products = []
    all_text = []
    for row in sorted(table, key=lambda r: int(r["BLOCK"])):
        block = int(row["BLOCK"])
        name = "TINT_params.md" if block < 0 else f"bin{block}_params.md"
        text = table_text(table, row, prefixes)
        path = out / name
        path.write_text(text)
        products.append({"file": name, "sha256": sha256(path), "rows": 24,
                         "winner": winner_prefix(row["BEST_AIC_MODEL"])})
        all_text.append(text)
    combined = out / "ALL_MODELS_TABLES.md"
    combined.write_text("\n\n---\n\n".join(all_text))
    manifest = {
        "trigger": trig,
        "source": str(ecsv.relative_to(REPO)),
        "source_sha256": sha256(ecsv),
        "n_models": 24,
        "n_spectra": len(table),
        "products": products,
        "combined_sha256": sha256(combined),
        "provisional": True,
    }
    manifest_path = out / "tables_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def science_summary(trig: str, fit_root: Path = FIT_ROOT) -> dict:
    table, meta, ecsv, _ = load_fit(trig, fit_root)
    prefixes = model_prefixes(table)
    rows = []
    for row in table:
        winner = winner_prefix(row["BEST_AIC_MODEL"])
        valid_order = sorted(
            (float(row[f"{p}_AIC"]), p) for p in prefixes
            if str(row[f"{p}_STATUS"]).upper() == "OK"
            and str(row[f"{p}_VALID"]).lower() in {"true", "1", "1.0"}
            and finite(row[f"{p}_AIC"])
        )
        gap = (valid_order[1][0] - valid_order[0][0]
               if len(valid_order) > 1 else float("nan"))
        rows.append({
            "block": int(row["BLOCK"]),
            "t_start": float(row["T_START"]),
            "t_stop": float(row["T_STOP"]),
            "winner": winner,
            "winner_display": MODEL_NAMES.get(winner, winner),
            "aic": float(row[f"{winner}_AIC"]) if winner in prefixes else float("nan"),
            "delta_aic_second_valid": gap,
            "ties_delta_aic_lt_2": [p for a, p in valid_order
                                     if a - valid_order[0][0] < 2.0],
            "plugin_dets": str(row["PLUGIN_DETS"]),
        })
    resolved = [r for r in rows if r["block"] >= 0]
    return {
        "trigger": trig,
        "fit_source": str(ecsv.relative_to(REPO)),
        "fit_sha256": sha256(ecsv),
        "fit_dets": list(meta.get("fit_dets", [])),
        "n_blocks": int(meta["n_blocks"]),
        "winner_census_resolved": dict(Counter(r["winner"] for r in resolved)),
        "rows": rows,
        "provisional": True,
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    pval = sub.add_parser("validate")
    pval.add_argument("--trig", required=True)
    pval.add_argument("--expected", type=int, default=24)
    pval.add_argument("--require-lle", action="store_true")
    pval.add_argument("--require-lat", action="store_true")
    pval.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    ptab = sub.add_parser("tables")
    ptab.add_argument("--trig", required=True)
    ptab.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    psci = sub.add_parser("summary")
    psci.add_argument("--trig", required=True)
    psci.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    pmerge = sub.add_parser("merge-repairs")
    pmerge.add_argument("--trig", required=True)
    pmerge.add_argument("--base-dir", required=True, type=Path)
    pmerge.add_argument("--incoming-dir", action="append", default=[], type=Path)
    pmerge.add_argument("--staging-dir", type=Path,
                        help="staging root; the input fingerprint is appended")
    pmerge.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    pmerge.add_argument("--log-root", type=Path)
    pmerge.add_argument("--repo-root", type=Path, default=REPO)
    pstage = sub.add_parser("stage-p1")
    pstage.add_argument("--trig", required=True)
    pstage.add_argument("--staging-dir", type=Path,
                        help="staging root; the input fingerprint is appended")
    pstage.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    pstage.add_argument("--log-root", type=Path)
    pstage.add_argument("--repo-root", type=Path, default=REPO)
    pstatus = sub.add_parser("status-matrix")
    pstatus.add_argument("--trig", required=True)
    pstatus.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    pstatus.add_argument("--log-root", type=Path)
    pstatus.add_argument("--repo-root", type=Path, default=REPO)
    pstatus.add_argument("--out", type=Path)
    pretry = sub.add_parser("retry-worklist")
    pretry.add_argument("--trig", action="append", dest="triggers")
    pretry.add_argument("--out", required=True, type=Path)
    pretry.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    pretry.add_argument("--log-root", type=Path)
    pretry.add_argument("--repo-root", type=Path, default=REPO)
    ppromote = sub.add_parser("promote-p1")
    ppromote.add_argument("--trig", required=True)
    ppromote.add_argument("--stage-dir", required=True, type=Path)
    ppromote.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    ppromote.add_argument("--repo-root", type=Path, default=REPO)
    ppromote.add_argument("--broadband-degradation-reason")
    args = parser.parse_args()

    if args.command == "validate":
        result = validate(args.trig, args.expected, args.require_lle,
                          args.require_lat, fit_root=args.fit_root)
    elif args.command == "tables":
        result = make_tables(args.trig, fit_root=args.fit_root)
    elif args.command == "merge-repairs":
        result = merge_repairs(args.trig, args.base_dir, args.incoming_dir,
                               fit_root=args.fit_root,
                               staging_dir=args.staging_dir,
                               log_root=args.log_root,
                               repo_root=args.repo_root)
    elif args.command == "stage-p1":
        result = stage_p1(args.trig, fit_root=args.fit_root,
                          staging_dir=args.staging_dir,
                          log_root=args.log_root,
                          repo_root=args.repo_root)
    elif args.command == "status-matrix":
        result = status_matrix(args.trig, fit_root=args.fit_root,
                               log_root=args.log_root,
                               repo_root=args.repo_root)
        if args.out:
            _atomic_write_text(args.out, json.dumps(result, indent=2) + "\n")
    elif args.command == "retry-worklist":
        result = build_retry_worklist(
            args.triggers or list(CAMPAIGN_TRIGGERS), args.out,
            fit_root=args.fit_root, log_root=args.log_root,
            repo_root=args.repo_root)
    elif args.command == "promote-p1":
        result = promote_stage(
            args.trig, args.stage_dir, fit_root=args.fit_root,
            repo_root=args.repo_root,
            broadband_degradation_reason=args.broadband_degradation_reason)
    else:
        result = science_summary(args.trig, fit_root=args.fit_root)
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
