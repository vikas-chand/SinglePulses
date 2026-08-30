#!/usr/bin/env python3
"""Fresh-source report and paper assembler for campaign bursts 3 through 22.

This campaign-owned helper never fits data. Scientific values come only from
the approved P0 catalog and block table, the hash-bound P1 promotion chain,
the promoted convention_check fit, p2_temporal_summary.json, and normalized
P3/P4 authorities. Missing products stay missing. Legacy nested sweep fits
are never a fallback.

The build command first runs the brief-exact scripts/48 invocation and records
its outcome. That command currently warns because --out is absent; its output
is not used as scientific authority. The adapter then writes the standalone
report and paper from fresh sources.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from astropy.table import Table
from PIL import Image


REPO = Path(__file__).resolve().parents[2]
FIT_ROOT = REPO / "results" / "convention_check"
SWEEP_ROOT = REPO / "results" / "sweep106"
PAPER_ROOT = REPO / "paper"
REFS_SOURCE = PAPER_ROOT / "GRB081222" / "refs.bib"
APPROVED_CATALOG = REPO / "results" / "background_intervals.ecsv"
MANIFEST_PATH = REPO / "notes" / "CODEX_CAMPAIGN20_MANIFEST.md"
PROGRESS_PATH = REPO / "notes" / "CODEX_CAMPAIGN20_PROGRESS.md"
GATE = "UNGATED — independent Claude figure verification pending"
PRODUCER = "Codex (AI), PRODUCER"
SCHEMA = "codex_campaign20.report_paper_assembly.v1"
PDF_MARKER_DECLARATION = (
    "Campaign-wide P5 deviation: the required PDF artifact-operation marker was "
    "successfully run once before fixture authoring with expected-output-count=1 "
    "for that fixture, not the final campaign count of 20; duplicate marker calls "
    "are forbidden. Scientific figures remain UNGATED."
)
_RUNTIME_MODULES: dict[str, Any] = {}

CAMPAIGN = (
    (3, "bn081224887", "GRB 081224"),
    (4, "bn090530760", "GRB 090530"),
    (5, "bn090620400", "GRB 090620"),
    (6, "bn090719063", "GRB 090719"),
    (7, "bn090804940", "GRB 090804"),
    (8, "bn090809978", "GRB 090809"),
    (9, "bn090829672", "GRB 090829"),
    (10, "bn091209001", "GRB 091209"),
    (11, "bn100122616", "GRB 100122"),
    (12, "bn100130729", "GRB 100130"),
    (13, "bn100612726", "GRB 100612"),
    (14, "bn100614498", "GRB 100614"),
    (15, "bn100707032", "GRB 100707"),
    (16, "bn101126198", "GRB 101126"),
    (17, "bn101225377", "GRB 101225"),
    (18, "bn110605183", "GRB 110605"),
    (19, "bn110618366", "GRB 110618"),
    (20, "bn110721200", "GRB 110721"),
    (21, "bn110920546", "GRB 110920"),
    (22, "bn110928180", "GRB 110928"),
)
CAMPAIGN_MAP = {trig: (number, grb) for number, trig, grb in CAMPAIGN}
BROADBAND = {"bn081224887", "bn110721200"}
TERMINAL = {"DONE", "PARTIAL", "FAILED"}
RESPONSE_BLOCKED = {"bn100130729"}

CANONICAL_PREFIXES = (
    # Exact scripts/10 HIGHE order, enforced by campaign_products.HIGHE_PREFIXES.
    "BAND", "CPL", "SBPL", "DSBPL", "BANDBB", "CPLBB", "SBPLF",
    "DSBPLF", "BANDPL", "BANDCPL", "CPLPL", "CPLCPL", "BANDRCPL",
    "BANDCUT", "SBPLCUT", "SBPLPL", "SBPLCPL", "BANDBBPL", "BANDBBCPL",
    "CPLBBPL", "CPLBBCPL", "SBPLBB", "SBPLBBPL", "SBPLBBCPL",
)
BB_PEAK_FACTOR = 3.9207
THERMAL_LRT_GATE = 9.2
L28_TRUST_KEV = 20.0
L28_CLEAR_KEV = 30.0

MODEL_NAMES = {
    "BAND": "Band", "CPL": "CPL", "SBPL": "SBPL", "DSBPL": "DSBPL",
    "BANDBB": "Band+BB", "CPLBB": "CPL+BB",
    "SBPLF": "SBPLfree", "DSBPLF": "DSBPLfree",
    "BANDPL": "Band+PL", "BANDCPL": "Band+CPL",
    "CPLPL": "CPL+PL", "CPLCPL": "CPL+CPL",
    "BANDRCPL": "BandR+CPL", "BANDCUT": "BandxCut",
    "SBPLCUT": "SBPLxCut", "SBPLPL": "SBPL+PL",
    "SBPLCPL": "SBPL+CPL", "BANDBBPL": "Band+BB+PL",
    "BANDBBCPL": "Band+BB+CPL", "CPLBBPL": "CPL+BB+PL",
    "CPLBBCPL": "CPL+BB+CPL", "SBPLBB": "SBPL+BB",
    "SBPLBBPL": "SBPL+BB+PL", "SBPLBBCPL": "SBPL+BB+CPL",
}
DISPLAY_TO_PREFIX = {
    re.sub(r"[^A-Z0-9]", "", display.upper()): prefix
    for prefix, display in MODEL_NAMES.items()
}
DISPLAY_TO_PREFIX.update({
    "DSBPLFREE": "DSBPLF", "SBPLFREE": "SBPLF",
    "BANDXCUT": "BANDCUT", "SBPLXCUT": "SBPLCUT",
})


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_hyphens(value: str) -> str:
    """Keep generated prose TeX-safe by eliminating Unicode dash codepoints."""
    return re.sub(r"[\u2010-\u2015]", "-", value)


def runtime_module(stem: str) -> Any:
    """Load a notes-owned producer validator without invoking its CLI."""
    if stem in _RUNTIME_MODULES:
        return _RUNTIME_MODULES[stem]
    path = Path(__file__).resolve().parent / (stem + ".py")
    name = "codex_campaign20_runtime_" + stem
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load runtime validator " + str(path))
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    _RUNTIME_MODULES[stem] = module
    return module


def without_generated_utc(value: dict[str, Any]) -> dict[str, Any]:
    cleaned = json.loads(json.dumps(value))
    cleaned.pop("generated_utc", None)
    return cleaned


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_ok(path: Path) -> bool:
    """Mirror the P3 producer's current PNG-integrity contract."""
    try:
        if not path.is_file() or path.stat().st_size <= 8:
            return False
        with path.open("rb") as stream:
            if stream.read(8) != b"\x89PNG\r\n\x1a\n":
                return False
        with Image.open(path) as image:
            if image.width <= 0 or image.height <= 0:
                return False
            image.verify()
        return True
    except Exception:
        return False


def pdf_ok(path: Path) -> bool:
    """Mirror the P3 producer's current PDF magic/EOF contract."""
    try:
        if not path.is_file() or path.stat().st_size <= 5:
            return False
        with path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                return False
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - 2048), os.SEEK_SET)
            return b"%%EOF" in stream.read()
    except OSError:
        return False


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + "." + str(os.getpid()) + ".tmp")
    temporary.write_text(value)
    os.replace(temporary, path)


def atomic_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, indent=2) + "\n")


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "missing " + display_path(path)
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        return None, "unreadable " + str(path) + ": " + type(exc).__name__ + ": " + str(exc)
    if not isinstance(value, dict):
        return None, "not a JSON object: " + str(path)
    return value, None


def finite(value: Any) -> bool:
    if np.ma.is_masked(value):
        return False
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def truthy(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return str(value).strip().lower() in {"true", "yes", "1", "ok"}


def canon_model(value: Any) -> str:
    key = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return DISPLAY_TO_PREFIX.get(key, key)


def grb_for_trigger(trig: str) -> str:
    if trig in CAMPAIGN_MAP:
        return CAMPAIGN_MAP[trig][1]
    match = re.fullmatch(r"bn(\d{6})\d{3}", trig)
    if not match:
        raise ValueError("invalid trigger " + trig)
    return "GRB " + match.group(1)


def paper_slug(grb: str) -> str:
    return grb.replace(" ", "")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def source_record(path: Path, role: str) -> dict[str, Any]:
    return {
        "role": role, "path": str(path), "repo_relative": display_path(path),
        "sha256": sha256(path), "bytes": path.stat().st_size,
    }


def tag_for(block: int) -> str:
    return "TINT" if block == -1 else "bin" + str(block)


def bin_label(block: int) -> str:
    return "T_INT" if block == -1 else str(block)


def normalize_bin(value: Any) -> str:
    text = str(value).strip().lower()
    if text in {"tint", "-1"}:
        return "tint"
    number = float(text)
    if not number.is_integer() or number < 0:
        raise ValueError("invalid bin " + repr(value))
    return str(int(number))


@dataclass
class Winner:
    block: int
    start: float
    stop: float
    prefix: str | None
    model: str
    aic: float | None
    margin: float | None
    ties: list[str]
    failed: list[str]
    params_md: str
    params_tex: str


@dataclass
class Context:
    trig: str
    grb: str
    number: int | None
    fit_path: Path
    fit_json_path: Path
    p2_path: Path
    grid: Path
    param_root: Path
    approved_path: Path
    blocks_path: Path
    p4_path: Path
    table: Table | None = None
    approved_rows: Table | None = None
    blocks: Table | None = None
    fit_meta: dict[str, Any] = field(default_factory=dict)
    promotion_receipt: dict[str, Any] = field(default_factory=dict)
    stage_manifest: dict[str, Any] = field(default_factory=dict)
    p2: dict[str, Any] = field(default_factory=dict)
    p2_artifacts_valid: bool = False
    p3: dict[str, Any] = field(default_factory=dict)
    p4: dict[str, Any] = field(default_factory=dict)
    panels: list[tuple[Path, dict[str, Any], Path]] = field(default_factory=list)
    montages: list[tuple[Path, dict[str, Any], Path]] = field(default_factory=list)
    params: list[tuple[Path, dict[str, Any], Path]] = field(default_factory=list)
    p4_tables: list[Path] = field(default_factory=list)
    p3_failures: dict[tuple[str, str], str] = field(default_factory=dict)
    prefixes: list[str] = field(default_factory=list)
    winners: list[Winner] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)

    @property
    def p2_complete(self) -> bool:
        return bool(self.p2.get("complete"))

    @property
    def temporal_values_available(self) -> bool:
        claimed = self.p2_complete or bool(self.p2.get("temporal_values_complete"))
        return claimed and self.p2_artifacts_valid

    @property
    def expected_pairs(self) -> int:
        if self.table is None:
            return 0
        return len(self.table) * len(CANONICAL_PREFIXES)

    @property
    def spectroscopy_available(self) -> bool:
        exact = self.table is not None and (
            tuple(self.prefixes) == CANONICAL_PREFIXES
            or (self.number is None and len(self.prefixes) == 24
                and len(set(self.prefixes)) == 24))
        # The completed burst-2 fixture predates campaign receipts and is allowed
        # only for tests. Campaign bursts require the full promotion chain.
        promoted = self.number is None or bool(
            self.promotion_receipt and self.stage_manifest)
        contract_valid = self.number is None or not any(
            item.startswith("P1 ") for item in self.anomalies)
        return exact and promoted and contract_valid

    @property
    def p3_fresh_complete(self) -> bool:
        return bool(
            self.spectroscopy_available and self.p3
            and self.p3.get("status") != "RESPONSE_BLOCKED"
            and self.expected_pairs > 0
            and len(self.panels) == self.expected_pairs
            and not self.p3_failures
            and not any(item.startswith("P3 ") for item in self.anomalies))

    @property
    def p4_fresh_complete(self) -> bool:
        expected_parameters = len(
            self.p4.get("parameter_evolution", {}).get("models", []))
        return bool(
            self.spectroscopy_available and self.p4.get("state") == "COMPLETE"
            and self.table is not None
            and len(self.montages) == len(self.table)
            and len(self.p4_tables) == len(self.table)
            and len(self.params) == expected_parameters
            and not any(item.startswith("P4 ") for item in self.anomalies))


def record_source(ctx: Context, path: Path, role: str) -> None:
    if path.is_file() and not any(item["path"] == str(path) for item in ctx.sources):
        ctx.sources.append(source_record(path, role))


def row_float(row: Any, column: str) -> float | None:
    if column not in row.colnames or not finite(row[column]):
        return None
    return float(row[column])


def measurement(row: Any, column: str, latex: bool = False) -> str:
    value = row_float(row, column)
    if value is None:
        return "unavailable"
    neg = row_float(row, column + "_NEG_ERR")
    pos = row_float(row, column + "_POS_ERR")
    sym = row_float(row, column + "_ERR")
    base = f"{value:.3g}"
    if neg is not None and pos is not None:
        if latex:
            return base + "^{+" + f"{abs(pos):.2g}" + "}_{-" + f"{abs(neg):.2g}" + "}"
        return base + " (+" + f"{abs(pos):.2g}" + "/-" + f"{abs(neg):.2g}" + ")"
    if sym is not None:
        return base + (" \\pm " if latex else " ± ") + f"{abs(sym):.2g}"
    return base


def parameter_specs(prefix: str) -> list[tuple[str, str, str]]:
    if prefix.startswith("DSBPL"):
        base = [("ALPHA1", "alpha1", r"\alpha_1"), ("XB", "Eb", r"E_{\rm b}"),
                ("ALPHA2", "alpha2", r"\alpha_2"), ("XP", "Ep", r"E_{\rm p}"),
                ("BETA", "beta", r"\beta")]
    elif prefix.startswith("SBPL"):
        base = [("ALPHA", "alpha", r"\alpha"), ("EBREAK", "Ebreak", r"E_{\rm break}"),
                ("BETA", "beta", r"\beta")]
    elif prefix.startswith("BAND"):
        base = [("ALPHA", "alpha", r"\alpha"), ("EP", "Ep", r"E_{\rm p}"),
                ("BETA", "beta", r"\beta")]
    elif prefix.startswith("CPL"):
        base = [("INDEX", "index", r"\Gamma"), ("XC", "Ec", r"E_{\rm c}")]
    else:
        base = []
    return base + [
        ("KT", "kT", "kT"), ("PL_INDEX", "PL index", r"\Gamma_{\rm PL}"),
        ("HE_INDEX", "HE index", r"\Gamma_{\rm HE}"),
        ("HE_XC", "HE Ec", r"E_{\rm c,HE}"), ("EC", "Ec,mult", r"E_{\rm c,mult}"),
    ]


def winner_params(row: Any, prefix: str) -> tuple[str, str]:
    md: list[str] = []
    tex: list[str] = []
    energy = {"XB", "XP", "EP", "EBREAK", "XC", "KT", "HE_XC", "EC"}
    for suffix, plain_label, tex_label in parameter_specs(prefix):
        column = prefix + "_" + suffix
        if row_float(row, column) is None:
            continue
        unit_md = " keV" if suffix in energy else ""
        unit_tex = r"\,\mathrm{keV}" if suffix in energy else ""
        md.append(plain_label + "=" + measurement(row, column) + unit_md)
        tex.append("$" + tex_label + "=" + measurement(row, column, True) + unit_tex + "$")
        if len(md) == 6:
            break
    return ", ".join(md) or "parameters unavailable", ", ".join(tex) or "parameters unavailable"


def winner_from_row(row: Any, prefixes: list[str]) -> Winner:
    usable: list[tuple[float, str]] = []
    failed: list[str] = []
    for prefix in prefixes:
        status = str(row[prefix + "_STATUS"]).strip().upper()
        if status == "FAIL":
            failed.append(MODEL_NAMES.get(prefix, prefix))
        aic = row_float(row, prefix + "_AIC")
        valid = truthy(row[prefix + "_VALID"]) if prefix + "_VALID" in row.colnames else True
        if status == "OK" and valid and aic is not None:
            usable.append((aic, prefix))
    usable.sort()
    block = int(float(row["BLOCK"]))
    start, stop = float(row["T_START"]), float(row["T_STOP"])
    if not usable:
        return Winner(block, start, stop, None, "INCONCLUSIVE", None, None,
                      [], failed, "parameters unavailable", "parameters unavailable")
    best_aic, prefix = usable[0]
    ties = [MODEL_NAMES.get(item, item) for aic, item in usable if aic - best_aic < 2.0]
    margin = usable[1][0] - best_aic if len(usable) > 1 else None
    md, tex = winner_params(row, prefix)
    return Winner(block, start, stop, prefix, MODEL_NAMES.get(prefix, prefix),
                  best_aic, margin, ties, failed, md, tex)


def resolve_source(value: Any) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (REPO / path).resolve()


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def bound_artifact(ctx: Context, item: Any, role: str,
                   root: Path | None = None) -> Path | None:
    """Resolve a normalized artifact record and require its declared hash."""
    if not isinstance(item, dict) or not item.get("path"):
        ctx.anomalies.append(role + " artifact record missing path")
        return None
    path = resolve_source(item["path"])
    if root is not None and not inside(path, root):
        ctx.anomalies.append(role + " artifact outside authority root: " + str(path))
        return None
    digest = item.get("sha256")
    if not digest:
        ctx.anomalies.append(role + " artifact lacks required SHA-256: " + str(path))
        return None
    if not path.is_file():
        ctx.anomalies.append(role + " artifact missing: " + str(path))
        return None
    if sha256(path) != str(digest):
        ctx.anomalies.append(role + " artifact hash mismatch: " + str(path))
        return None
    if finite(item.get("bytes")) and path.stat().st_size != int(item["bytes"]):
        ctx.anomalies.append(role + " artifact byte-count mismatch: " + str(path))
        return None
    record_source(ctx, path, role)
    return path


def load_p0_authorities(ctx: Context) -> None:
    if ctx.approved_path.is_file():
        try:
            catalog = Table.read(ctx.approved_path, format="ascii.ecsv")
            mask = [str(value).strip() == ctx.trig
                    for value in catalog["TRIGGER_NAME"]]
            rows = catalog[mask]
            if not len(rows):
                ctx.anomalies.append("P0 approved catalog has no rows for " + ctx.trig)
            else:
                ctx.approved_rows = rows
                detectors = [str(value).strip() for value in rows["DETECTOR"]]
                if len(detectors) != len(set(detectors)):
                    ctx.anomalies.append("P0 approved detector rows are duplicated")
                starts = {round(float(value), 9) for value in rows["SRC_START"]}
                stops = {round(float(value), 9) for value in rows["SRC_STOP"]}
                if len(starts) != 1 or len(stops) != 1:
                    ctx.anomalies.append("P0 approved source window differs by detector")
                required = ("APPROVED_BY", "APPROVED_UTC", "APPROVAL_MODE")
                if any(not str(row[name]).strip() for row in rows for name in required):
                    ctx.anomalies.append("P0 approved rows lack a complete gate stamp")
            record_source(ctx, ctx.approved_path, "p0_approved_selection_catalog")
        except Exception as exc:
            ctx.anomalies.append(
                "P0 approved catalog unreadable: " + type(exc).__name__ + ": " + str(exc))
    else:
        ctx.anomalies.append("P0 approved catalog missing: " + display_path(ctx.approved_path))

    if ctx.blocks_path.is_file():
        try:
            blocks = Table.read(ctx.blocks_path, format="ascii.ecsv")
            if any(str(value).strip() != ctx.trig for value in blocks["TRIGGER_NAME"]):
                ctx.anomalies.append("P0 block table trigger mismatch")
            for detector in sorted({str(value).strip() for value in blocks["DETECTOR"]}):
                selected = blocks[[str(value).strip() == detector
                                   for value in blocks["DETECTOR"]]]
                indices = [int(value) for value in selected["BLOCK_INDEX"]]
                if indices != list(range(len(indices))):
                    ctx.anomalies.append(
                        "P0 block indices incomplete or out of order for " + detector +
                        ": " + str(indices))
            ctx.blocks = blocks
            record_source(ctx, ctx.blocks_path, "p0_adopted_block_table")
        except Exception as exc:
            ctx.anomalies.append(
                "P0 block table unreadable: " + type(exc).__name__ + ": " + str(exc))
    else:
        ctx.anomalies.append("P0 block table missing: " + display_path(ctx.blocks_path))


def load_promotion_chain(ctx: Context, fit_root: Path) -> None:
    """Find exactly one receipt that binds the current canonical ECSV/JSON."""
    if ctx.table is None or not ctx.fit_json_path.is_file():
        return
    receipt_root = fit_root / ctx.trig / "promotion_receipts"
    stage_root = fit_root / ctx.trig / "merge_staging"
    if not receipt_root.is_dir():
        ctx.anomalies.append("P1 promotion receipt directory missing: " + str(receipt_root))
        return
    current_ecsv = sha256(ctx.fit_path)
    current_json = sha256(ctx.fit_json_path)
    candidates: list[tuple[Path, dict[str, Any], Path, dict[str, Any]]] = []
    for path in sorted(receipt_root.glob("*.json")):
        receipt, error = load_json(path)
        if receipt is None:
            ctx.anomalies.append("P1 promotion receipt " + str(error))
            continue
        if receipt.get("trigger") != ctx.trig \
                or receipt.get("ecsv_sha256") != current_ecsv \
                or receipt.get("json_sha256") != current_json:
            continue
        fingerprint = str(receipt.get("input_fingerprint", ""))
        stage_dir = resolve_source(receipt.get("stage_dir", ""))
        if not fingerprint or not inside(stage_dir, stage_root) \
                or stage_dir.name != fingerprint:
            ctx.anomalies.append("P1 matching receipt has invalid stage directory: " + path.name)
            continue
        manifest_path = stage_dir / "family_merge_manifest.json"
        manifest, error = load_json(manifest_path)
        if manifest is None:
            ctx.anomalies.append("P1 stage manifest " + str(error))
            continue
        required = (
            manifest.get("trigger") == ctx.trig,
            manifest.get("input_fingerprint") == fingerprint,
            manifest.get("ecsv_sha256") == current_ecsv,
            manifest.get("json_sha256") == current_json,
            tuple(manifest.get("model_prefixes", [])) == CANONICAL_PREFIXES,
            int(manifest.get("models", -1)) == 24,
            int(manifest.get("rows", -1)) == len(ctx.table),
        )
        if not all(required):
            ctx.anomalies.append("P1 matching receipt has an invalid stage manifest: " + path.name)
            continue
        authority_ok = True
        for name, authority in manifest.get("authorities", {}).items():
            if not isinstance(authority, dict) or not authority.get("exists"):
                continue
            authority_path = resolve_source(authority.get("path", ""))
            if not authority_path.is_file() \
                    or sha256(authority_path) != authority.get("sha256"):
                ctx.anomalies.append(
                    "P1 stage authority changed or missing (" + str(name) + "): " +
                    str(authority_path))
                authority_ok = False
        if authority_ok:
            candidates.append((path, receipt, manifest_path, manifest))
    if len(candidates) != 1:
        ctx.anomalies.append(
            "P1 promotion receipt unavailable/ambiguous for current canonical pair: " +
            str(len(candidates)) + " matching validated receipts")
        return
    receipt_path, receipt, manifest_path, manifest = candidates[0]
    ctx.promotion_receipt = receipt
    ctx.stage_manifest = manifest
    record_source(ctx, receipt_path, "p1_promotion_receipt")
    record_source(ctx, manifest_path, "p1_family_merge_manifest")
    merge = ctx.fit_meta.get("campaign_merge", {})
    if merge.get("input_fingerprint") != receipt.get("input_fingerprint"):
        ctx.anomalies.append("P1 fit metadata fingerprint differs from promotion receipt")


def validate_fit_contract(ctx: Context) -> None:
    if ctx.table is None:
        return
    if tuple(ctx.prefixes) != CANONICAL_PREFIXES:
        ctx.anomalies.append(
            "P1 canonical model registry mismatch: " + repr(tuple(ctx.prefixes)))
    blocks = [int(float(value)) for value in ctx.table["BLOCK"]]
    expected = [-1] + list(range(len(blocks) - 1)) if blocks else []
    if blocks != expected:
        ctx.anomalies.append("P1 block rows incomplete, duplicated, or out of order: " + str(blocks))
    resolved = [row for row in ctx.table if int(float(row["BLOCK"])) >= 0]
    meta = ctx.fit_meta
    if not meta:
        return
    if meta.get("trigger") not in {None, ctx.trig}:
        ctx.anomalies.append("P1 JSON trigger mismatch")
    if tuple(meta.get("models", [])) != tuple(MODEL_NAMES[p] for p in CANONICAL_PREFIXES):
        ctx.anomalies.append("P1 JSON model registry/order differs from canonical 24")
    if int(meta.get("n_blocks", -1)) != len(resolved):
        ctx.anomalies.append("P1 JSON n_blocks differs from resolved fit rows")
    starts = meta.get("bin_starts", [])
    stops = meta.get("bin_stops", [])
    expected_starts = [float(row["T_START"]) for row in resolved]
    expected_stops = [float(row["T_STOP"]) for row in resolved]
    if len(starts) != len(expected_starts) or any(
            not math.isclose(float(left), right, rel_tol=0, abs_tol=1e-8)
            for left, right in zip(starts, expected_starts)):
        ctx.anomalies.append("P1 JSON bin_starts differ from canonical fit rows")
    if len(stops) != len(expected_stops) or any(
            not math.isclose(float(left), right, rel_tol=0, abs_tol=1e-8)
            for left, right in zip(stops, expected_stops)):
        ctx.anomalies.append("P1 JSON bin_stops differ from canonical fit rows")
    if ctx.blocks is not None:
        block_pairs = sorted({
            (float(row["T_START"]), float(row["T_STOP"])) for row in ctx.blocks
        })
        fit_pairs = list(zip(expected_starts, expected_stops))
        if len(block_pairs) != len(fit_pairs) or any(
                not (math.isclose(a, c, rel_tol=0, abs_tol=1e-8) and
                     math.isclose(b, d, rel_tol=0, abs_tol=1e-8))
                for (a, b), (c, d) in zip(block_pairs, fit_pairs)):
            ctx.anomalies.append("P1 fit bins differ from the adopted P0 block table")
    if ctx.approved_rows is not None:
        approved = {str(value).strip() for value in ctx.approved_rows["DETECTOR"]}
        fit_dets = {str(value).strip() for value in meta.get("fit_dets", [])}
        if approved != fit_dets:
            ctx.anomalies.append(
                "P1 fit detector set differs from adopted approved rows: approved=" +
                repr(sorted(approved)) + ", fit=" + repr(sorted(fit_dets)))


def expected_p3_pairs(ctx: Context) -> set[tuple[str, str]]:
    if ctx.table is None:
        return set()
    bins = {"tint" if int(float(row["BLOCK"])) == -1
            else str(int(float(row["BLOCK"]))) for row in ctx.table}
    return {(bin_arg, model) for bin_arg in bins for model in CANONICAL_PREFIXES}


def load_p3_with_producer_validator(ctx: Context, stored: dict[str, Any]) -> None:
    """Consume the one hardened P3 validator used by the P4 producer."""
    validator = runtime_module("run_p4_products")
    closure = validator.validate_p3_closure(ctx.trig)
    fresh = closure["summary"]
    if without_generated_utc(fresh) != without_generated_utc(stored):
        raise RuntimeError(
            "stored P3 closure differs from fresh producer-validator closure")
    ctx.p3 = stored
    record_source(
        ctx, Path(validator.__file__).resolve(),
        "p3_p4_read_only_validator_implementation")
    summary_path = ctx.grid / "sweep_summary.json"
    status_path = ctx.grid / "sweep_status.txt"
    record_source(ctx, summary_path, "p3_no_model_dropped_closure")
    record_source(ctx, status_path, "p3_no_model_dropped_status")
    failure_records = {
        (normalize_bin(item.get("bin")), canon_model(item.get("model"))): item
        for item in stored.get("failed_pairs", [])
    }
    for pair, result in closure["validations"].items():
        if not result.ok:
            record = failure_records.get(pair, {})
            ctx.p3_failures[pair] = str(
                record.get("reason") or result.reason or "reason unavailable")
            continue
        sidecar = Path(result.sidecar).resolve()
        side, error = load_json(sidecar)
        if side is None:
            raise RuntimeError("fresh validator returned unreadable sidecar: " + str(error))
        png = sidecar.with_suffix(".png")
        pdf = sidecar.with_suffix(".pdf")
        ctx.panels.append((sidecar, side, png))
        record_source(ctx, sidecar, "p3_panel_sidecar")
        record_source(ctx, png, "p3_panel_png")
        record_source(ctx, pdf, "p3_panel_pdf")


def load_p3(ctx: Context) -> None:
    p3_path = ctx.grid / "sweep_summary.json"
    p3, error = load_json(p3_path)
    if p3 is None:
        if error:
            ctx.anomalies.append("P3 " + error)
        return
    ctx.p3 = p3
    if p3.get("trigger") != ctx.trig:
        ctx.anomalies.append("P3 trigger mismatch")
        return
    if p3.get("status") == "RESPONSE_BLOCKED":
        if ctx.trig not in RESPONSE_BLOCKED or int(p3.get("pairs", -1)) != 0:
            ctx.anomalies.append("P3 response-blocked closure is inconsistent")
        record_source(ctx, p3_path, "p3_response_blocked_closure")
        return
    if ctx.number is not None:
        try:
            load_p3_with_producer_validator(ctx, p3)
        except Exception as exc:
            ctx.p3 = {}
            ctx.anomalies.append(
                "P3 hardened producer validator rejected closure: " +
                type(exc).__name__ + ": " + str(exc))
        return
    record_source(ctx, p3_path, "p3_no_model_dropped_closure")
    if not finite(p3.get("aic_tolerance")) or not math.isclose(
            float(p3["aic_tolerance"]), 0.1, rel_tol=0, abs_tol=1e-12):
        ctx.anomalies.append("P3 AIC tolerance differs from the 0.1 contract")
    if int(p3.get("pool_size", -1)) != 16:
        ctx.anomalies.append("P3 closure does not record the required 16-slot pool")
    if int(p3.get("retry_limit", -1)) != 1:
        ctx.anomalies.append("P3 closure does not record the required one retry")
    canonical = resolve_source(p3.get("canonical_fit_table", ""))
    if canonical != ctx.fit_path.resolve():
        ctx.anomalies.append("P3 closure is not bound to the canonical fit table")
    expected = expected_p3_pairs(ctx)
    if tuple(canon_model(item) for item in p3.get("models", [])) != CANONICAL_PREFIXES:
        ctx.anomalies.append("P3 model registry/order differs from canonical 24")
    row_count = len(ctx.table) if ctx.table is not None else 0
    expected_bins = ["tint"] + [str(number) for number in range(max(0, row_count - 1))]
    try:
        observed_bins = [normalize_bin(item) for item in p3.get("bins", [])]
    except Exception as exc:
        observed_bins = []
        ctx.anomalies.append("P3 bin registry invalid: " + str(exc))
    if observed_bins != expected_bins:
        ctx.anomalies.append("P3 bin registry differs from canonical fit rows")
    observed: list[tuple[str, str]] = []
    for entry in list(p3.get("valid_triplets", [])) + list(p3.get("failed_pairs", [])):
        try:
            observed.append((normalize_bin(entry.get("bin")), canon_model(entry.get("model"))))
        except Exception as exc:
            ctx.anomalies.append("P3 closure pair invalid: " + str(exc))
    if len(observed) != len(set(observed)):
        ctx.anomalies.append("P3 closure contains duplicate model-bin pairs")
    if set(observed) != expected:
        missing = len(expected - set(observed))
        extra = len(set(observed) - expected)
        ctx.anomalies.append(
            "P3 exact pair-set mismatch: missing=" + str(missing) + ", extra=" + str(extra))
    valid_entries = list(p3.get("valid_triplets", []))
    failed_entries = list(p3.get("failed_pairs", []))
    for entry in failed_entries:
        try:
            pair = (normalize_bin(entry.get("bin")), canon_model(entry.get("model")))
            ctx.p3_failures[pair] = str(entry.get("reason", "reason unavailable"))
        except Exception:
            continue
    if int(p3.get("pairs", -1)) != len(expected) \
            or int(p3.get("ok", -1)) != len(valid_entries) \
            or int(p3.get("fail", -1)) != len(failed_entries):
        ctx.anomalies.append("P3 pair/OK/FAIL counts differ from closure entries")
    if failed_entries:
        ctx.anomalies.append(
            "P3 has " + str(len(failed_entries)) + " persistent model-bin failures")

    rows_by_bin = {
        "tint" if int(float(row["BLOCK"])) == -1 else str(int(float(row["BLOCK"]))): row
        for row in (ctx.table if ctx.table is not None else [])
    }
    for entry in valid_entries:
        try:
            entry_pair = (
                normalize_bin(entry.get("bin")), canon_model(entry.get("model")))
        except Exception as exc:
            ctx.anomalies.append("P3 valid-triplet pair invalid: " + str(exc))
            continue
        raw = entry.get("sidecar")
        if not raw:
            ctx.anomalies.append("P3 valid-triplet entry lacks sidecar")
            ctx.p3_failures[entry_pair] = "fresh validation: sidecar path absent"
            continue
        path = resolve_source(raw)
        if not inside(path, ctx.grid):
            ctx.anomalies.append("P3 sidecar outside canonical grid: " + str(path))
            ctx.p3_failures[entry_pair] = (
                "fresh validation: sidecar outside canonical grid: " + str(path))
            continue
        side, side_error = load_json(path)
        if side is None:
            ctx.anomalies.append("P3 panel " + str(side_error))
            ctx.p3_failures[entry_pair] = "fresh validation: " + str(side_error)
            continue
        try:
            side_bin = normalize_bin(side.get("bin"))
            side_model = canon_model(side.get("model"))
            if (side_bin, side_model) != entry_pair:
                raise ValueError("closure pair and sidecar pair differ")
            if str(side.get("trig", "")).strip() != ctx.trig:
                raise ValueError("sidecar trigger differs from the campaign burst")
            if side.get("script") != "41c_paper_sed.py":
                raise ValueError("sidecar is not a scripts/41c product")
            row = rows_by_bin[side_bin]
            current = row_float(row, side_model + "_AIC")
            stored = float(side.get("aic_stored"))
            rendered = float(side.get("aic_live"))
            if current is None or abs(stored - current) > 0.1 or abs(rendered - current) > 0.1:
                raise ValueError("panel AIC differs from canonical fit by more than 0.1")
            png = path.with_suffix(".png")
            pdf = path.with_suffix(".pdf")
            if not png_ok(png):
                raise ValueError("panel PNG missing or invalid")
            if not pdf_ok(pdf):
                raise ValueError("panel PDF missing or invalid")
        except Exception as exc:
            ctx.anomalies.append(
                "P3 panel failed fresh binding: " + path.name + ": " + str(exc))
            ctx.p3_failures[entry_pair] = "fresh validation: " + str(exc)
            continue
        ctx.panels.append((path, side, png))
        record_source(ctx, path, "p3_panel_sidecar")
        record_source(ctx, png, "p3_panel_png")
        record_source(ctx, pdf, "p3_panel_pdf")
    validated_pairs = {
        (normalize_bin(side.get("bin")), canon_model(side.get("model")))
        for _, side, _ in ctx.panels
    }
    for pair in expected - validated_pairs:
        ctx.p3_failures.setdefault(pair, "fresh validation: expected triplet unavailable")
    if len(ctx.panels) != len(valid_entries):
        ctx.anomalies.append(
            "P3 validated panel count " + str(len(ctx.panels)) +
            " differs from closure OK count " + str(len(valid_entries)))


def load_p4(ctx: Context) -> None:
    p4, error = load_json(ctx.p4_path)
    if p4 is None:
        if error:
            ctx.anomalies.append("P4 " + error)
        return
    if ctx.number is not None:
        try:
            p4_validator = runtime_module("run_p4_products")
            fresh_p4 = p4_validator.collect_summary(ctx.trig)
            if without_generated_utc(fresh_p4) != without_generated_utc(p4):
                raise RuntimeError(
                    "stored P4 summary differs from fresh read-only producer validation")
            record_source(
                ctx, Path(p4_validator.__file__).resolve(),
                "p3_p4_read_only_validator_implementation")
        except Exception as exc:
            ctx.anomalies.append(
                "P4 hardened producer validator rejected products: " +
                type(exc).__name__ + ": " + str(exc))
            return
    ctx.p4 = p4
    record_source(ctx, ctx.p4_path, "p4_products_summary")
    if p4.get("schema_version") != "codex_campaign20.p4_products_summary.v1":
        ctx.anomalies.append("P4 normalized summary schema mismatch")
    if p4.get("provisional") is not True \
            or "UNGATED" not in str(p4.get("figure_gate_status", "")) \
            or p4.get("figure_verifier") is not None:
        ctx.anomalies.append("P4 provisional/figure-gate declaration mismatch")
    if p4.get("trigger") != ctx.trig:
        ctx.anomalies.append("P4 summary trigger mismatch")
        return
    if p4.get("state") != "COMPLETE":
        ctx.anomalies.append(
            "P4 summary is " + str(p4.get("state")) + ": " +
            " | ".join(map(str, p4.get("errors", []))))
        return
    canonical = bound_artifact(ctx, p4.get("canonical_fit"), "p4_canonical_fit", ctx.fit_path.parent)
    if canonical is None or canonical.resolve() != ctx.fit_path.resolve():
        ctx.anomalies.append("P4 summary is not bound to the canonical fit")
        return
    metadata = bound_artifact(
        ctx, p4.get("canonical_fit_metadata"), "p4_canonical_fit_metadata",
        ctx.fit_path.parent)
    adopted = bound_artifact(
        ctx, p4.get("adopted_blocks"), "p4_adopted_blocks", ctx.blocks_path.parent)
    p3_summary = bound_artifact(
        ctx, p4.get("p3_closure"), "p4_bound_p3_closure", ctx.grid)
    p3_status = bound_artifact(
        ctx, p4.get("p3_status"), "p4_bound_p3_status", ctx.grid)
    if metadata != ctx.fit_json_path.resolve() or adopted != ctx.blocks_path.resolve() \
            or p3_summary != (ctx.grid / "sweep_summary.json").resolve() \
            or p3_status != (ctx.grid / "sweep_status.txt").resolve():
        ctx.anomalies.append("P4 normalized authority-chain path binding mismatch")
        return

    montage_root = ctx.grid / "montage"
    bound_artifact(
        ctx, p4.get("montages", {}).get("fallback_audit"),
        "p4_montage_fallback_audit", montage_root)
    tags = p4.get("montages", {}).get("tags", [])
    for entry in tags:
        png = bound_artifact(ctx, entry.get("png"), "p4_montage_png", montage_root)
        sidecar = bound_artifact(
            ctx, entry.get("sidecar"), "p4_montage_sidecar", montage_root)
        if png is None or sidecar is None:
            continue
        side, side_error = load_json(sidecar)
        if side is None:
            ctx.anomalies.append("P4 montage " + str(side_error))
            continue
        if str(side.get("tag")) != str(entry.get("tag")) \
                or int(side.get("n_missing", -1)) != int(entry.get("n_missing", -2)) \
                or int(side.get("n_panels", -1)) != 24:
            ctx.anomalies.append("P4 montage summary/sidecar mismatch: " + sidecar.name)
            continue
        ctx.montages.append((sidecar, side, png))

    raw_winners: dict[int, str] = {}
    if ctx.table is not None:
        for row in ctx.table:
            finite_aics = {prefix: row_float(row, prefix + "_AIC")
                           for prefix in CANONICAL_PREFIXES}
            usable = {key: value for key, value in finite_aics.items() if value is not None}
            if usable:
                raw_winners[int(float(row["BLOCK"]))] = min(usable, key=usable.get)
    resolved_count = sum(block >= 0 for block in raw_winners)
    expected_models = sorted(set(raw_winners.values()))
    declared_models = [canon_model(item) for item in
                       p4.get("parameter_evolution", {}).get("models", [])]
    if declared_models != expected_models:
        ctx.anomalies.append(
            "P4 parameter-evolution model registry differs from the raw-AIC winner union")
    for entry in p4.get("parameter_evolution", {}).get("products", []):
        png = bound_artifact(ctx, entry.get("png"), "p4_parameter_png", ctx.param_root)
        pdf = bound_artifact(ctx, entry.get("pdf"), "p4_parameter_pdf", ctx.param_root)
        sidecar = bound_artifact(
            ctx, entry.get("sidecar"), "p4_parameter_sidecar", ctx.param_root)
        if png is None or pdf is None or sidecar is None:
            continue
        side, side_error = load_json(sidecar)
        if side is None:
            ctx.anomalies.append("P4 parameters " + str(side_error))
            continue
        prefix = canon_model(side.get("prefix"))
        expected_bins = sorted(
            block for block, winner in raw_winners.items()
            if block >= 0 and winner == prefix)
        source = resolve_source(side.get("source_table", ""))
        script_path = REPO / "scripts" / "41d_param_evolution.py"
        valid = (
            side.get("trig") == ctx.trig and side.get("script") == "41d_param_evolution.py"
            and script_path.is_file() and side.get("script_sha256") == sha256(script_path)
            and side.get("no_refit") is True and source == ctx.fit_path.resolve()
            and side.get("winner_bins") == expected_bins
            and int(side.get("n_blocks", -1)) == resolved_count
            and entry.get("winner_bins") == expected_bins
        )
        if not valid:
            ctx.anomalies.append("P4 parameter-evolution provenance stale: " + sidecar.name)
            continue
        ctx.params.append((sidecar, side, png))
    validated_models = sorted(canon_model(side.get("prefix"))
                              for _, side, _ in ctx.params)
    if validated_models != expected_models:
        ctx.anomalies.append(
            "P4 parameter-evolution closure is " +
            repr(validated_models) + "; expected " + repr(expected_models))

    tables = p4.get("all_model_tables", {})
    manifest_path = bound_artifact(
        ctx, tables.get("manifest"), "p4_all_model_tables_manifest", ctx.grid / "tables")
    combined = bound_artifact(
        ctx, tables.get("combined"), "p4_all_model_tables_combined", ctx.grid / "tables")
    for entry in tables.get("products", []):
        path = bound_artifact(ctx, entry, "p4_per_bin_all_model_table", ctx.grid / "tables")
        if path is not None:
            ctx.p4_tables.append(path)
    expected_tables = len(ctx.table) if ctx.table is not None else 0
    if manifest_path is None or combined is None or len(ctx.p4_tables) != expected_tables:
        ctx.anomalies.append(
            "P4 all-model table closure is " + str(len(ctx.p4_tables)) +
            "/" + str(expected_tables))


def load_context(trig: str, fit_root: Path = FIT_ROOT,
                 sweep_root: Path = SWEEP_ROOT,
                 p2_override: Path | None = None) -> Context:
    """Read only the approved/fresh, hash-bound campaign authority chain."""
    grb = grb_for_trigger(trig)
    number = CAMPAIGN_MAP.get(trig, (None, grb))[0]
    fit_path = fit_root / trig / "spectral_fits.ecsv"
    fit_json_path = fit_root / trig / "spectral_fits.json"
    p2_path = p2_override or sweep_root / trig / "p2_temporal_summary.json"
    grid = fit_root / ("sed_grid_" + trig)
    blocks_path = sweep_root / trig / "blocks" / ("bb_blocks_spectral_" + trig + ".ecsv")
    ctx = Context(trig, grb, number, fit_path, fit_json_path, p2_path,
                  grid, fit_root / "param_evolution", APPROVED_CATALOG,
                  blocks_path, grid / "p4_products_summary.json")

    load_p0_authorities(ctx)

    if fit_path.is_file():
        try:
            ctx.table = Table.read(fit_path, format="ascii.ecsv")
            ctx.prefixes = [name[:-4] for name in ctx.table.colnames
                            if name.endswith("_AIC")]
            record_source(ctx, fit_path, "fresh_convention_check_fit_ecsv")
        except Exception as exc:
            ctx.anomalies.append("P1 fit unreadable: " + type(exc).__name__ + ": " + str(exc))
            ctx.table = None
    else:
        ctx.anomalies.append("P1 fit missing: " + display_path(fit_path))

    fit_meta, error = load_json(fit_json_path)
    if fit_meta is not None:
        ctx.fit_meta = fit_meta
        record_source(ctx, fit_json_path, "fresh_convention_check_fit_json")
    elif error:
        ctx.anomalies.append("P1 metadata " + error)
    validate_fit_contract(ctx)
    load_promotion_chain(ctx, fit_root)

    p2, error = load_json(p2_path)
    if p2 is not None:
        ctx.p2 = p2
        record_source(ctx, p2_path, "normalized_p2_temporal_summary")
        if p2.get("trigger") != trig:
            ctx.anomalies.append("P2 trigger mismatch")
        if ctx.number is not None and p2.get("schema_version") != \
                "codex_campaign20.p2_temporal_summary.v1":
            ctx.anomalies.append("P2 normalized summary schema mismatch")
        if ctx.number is not None and (
                p2.get("provisional") is not True
                or "UNGATED" not in str(p2.get("figure_gate_status", ""))
                or p2.get("figure_verifier") is not None):
            ctx.anomalies.append("P2 provisional/figure-gate declaration mismatch")
        artifacts = p2.get("artifacts", [])
        valid_artifacts = 0
        for artifact_item in artifacts:
            if bound_artifact(
                    ctx, artifact_item, "p2_normalized_receipt_or_artifact") is not None:
                valid_artifacts += 1
        ctx.p2_artifacts_valid = (
            valid_artifacts == len(artifacts) and
            (bool(artifacts) or ctx.number is None))
        if ctx.number is not None:
            try:
                p2_validator = runtime_module("run_p2_temporal")
                fresh_p2 = p2_validator.collect_summary(trig)
                if without_generated_utc(fresh_p2) != without_generated_utc(p2):
                    raise RuntimeError(
                        "stored normalized summary differs from fresh read-only validation")
                record_source(
                    ctx, Path(p2_validator.__file__).resolve(),
                    "p2_read_only_validator_implementation")
            except Exception as exc:
                ctx.p2_artifacts_valid = False
                ctx.anomalies.append(
                    "P2 fresh validator rejected normalized authority: " +
                    type(exc).__name__ + ": " + str(exc))
        if not ctx.p2_artifacts_valid:
            ctx.anomalies.append(
                "P2 normalized artifact/receipt closure invalid: " +
                str(valid_artifacts) + "/" + str(len(artifacts)))
        if not p2.get("complete"):
            errors = p2.get("validation_errors") or ["summary marked incomplete"]
            ctx.anomalies.extend("P2: " + str(item) for item in errors)
    elif error:
        ctx.anomalies.append("P2 " + error)

    if ctx.spectroscopy_available:
        load_p3(ctx)
        load_p4(ctx)
    elif ctx.table is None:
        # The sole scientific exception is the explicit zero-pair #12
        # RESPONSE_BLOCKED closure, which explains why no P1 table can exist.
        load_p3(ctx)
        if ctx.p3 and (
                ctx.trig not in RESPONSE_BLOCKED
                or ctx.p3.get("status") != "RESPONSE_BLOCKED"):
            ctx.anomalies.append(
                "P3 non-blocked authority refused because P1 is unavailable")
            ctx.p3 = {}
    else:
        if ctx.grid.joinpath("sweep_summary.json").is_file():
            ctx.anomalies.append(
                "P3 candidate refused because the campaign P1 contract did not pass")
        if ctx.p4_path.is_file():
            ctx.anomalies.append(
                "P4 candidate refused because the campaign P1 contract did not pass")

    if ctx.table is not None:
        ctx.winners = [winner_from_row(row, ctx.prefixes) for row in ctx.table]
    audit_montages(ctx)
    return ctx


def audit_montages(ctx: Context) -> None:
    if not ctx.p3 or ctx.table is None:
        return
    valid_pairs = {
        (normalize_bin(side.get("bin")), canon_model(side.get("model")))
        for _, side, _ in ctx.panels
    }
    failures = expected_p3_pairs(ctx) - valid_pairs
    by_tag = {str(side.get("tag")): side for _, side, _ in ctx.montages}
    for row in ctx.table:
        block = int(float(row["BLOCK"]))
        tag = tag_for(block)
        bin_arg = "tint" if block == -1 else str(block)
        expected = sum(1 for failed_bin, _ in failures if failed_bin == bin_arg)
        if tag not in by_tag:
            ctx.anomalies.append("P4 montage sidecar missing for " + tag)
            continue
        observed = int(by_tag[tag].get("n_missing", -1))
        if observed != expected:
            ctx.anomalies.append(
                "P4 " + tag + " n_missing=" + str(observed) +
                ", P3 closure requires " + str(expected))
        panels = int(by_tag[tag].get("n_panels", -1))
        if panels != len(set(ctx.prefixes)):
            ctx.anomalies.append(
                "P4 " + tag + " n_panels=" + str(panels) +
                ", canonical registry has " + str(len(set(ctx.prefixes))))


class FigureRegistry:
    def __init__(self, ctx: Context, paper_dir: Path):
        self.ctx = ctx
        self.paper_dir = paper_dir
        self.figure_dir = paper_dir / "figs"
        self.entries: list[dict[str, Any]] = []

    @staticmethod
    def inside(path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except (ValueError, OSError):
            return False

    def stage(self, source: Path, kind: str,
              metadata: dict[str, Any] | None = None) -> Path | None:
        if not source.is_file():
            self.ctx.anomalies.append(
                "figure missing (" + kind + "): " + display_path(source))
            return None
        if source.suffix.lower() != ".png":
            return None
        self.figure_dir.mkdir(parents=True, exist_ok=True)
        destination = self.figure_dir / source.name
        digest = sha256(source)
        collision = next(
            (entry for entry in self.entries
             if Path(entry["destination"]).name == source.name
             and entry["source_sha256"] != digest), None)
        if collision is not None:
            destination = self.figure_dir / (
                kind + "_" + digest[:12] + "_" + source.name)
        if not destination.exists() or sha256(destination) != digest:
            temporary = destination.with_name(
                "." + destination.name + "." + str(os.getpid()) + ".tmp")
            shutil.copy2(source, temporary)
            if sha256(temporary) != digest:
                temporary.unlink(missing_ok=True)
                raise RuntimeError("staged figure copy hash mismatch: " + str(source))
            os.replace(temporary, destination)
        if sha256(destination) != digest:
            raise RuntimeError("staged figure destination is stale: " + str(destination))
        item: dict[str, Any] = {
            "kind": kind, "source": str(source),
            "source_repo_relative": display_path(source),
            "source_sha256": digest, "destination": str(destination),
            "destination_sha256": sha256(destination),
            "bytes": destination.stat().st_size, "figure_gate_status": GATE,
        }
        if metadata:
            item["metadata"] = metadata
        if not any(old["destination"] == str(destination) for old in self.entries):
            self.entries.append(item)
        return destination

    def named(self, name: str) -> Path | None:
        for item in self.entries:
            path = Path(item["destination"])
            if path.name == name:
                return path
        return None

    def pair(self, block: int, prefix: str) -> Path | None:
        bin_arg = "tint" if block == -1 else str(block)
        for item in self.entries:
            meta = item.get("metadata", {})
            if item["kind"] == "p3_sed" and meta.get("bin") == bin_arg \
                    and meta.get("model") == prefix:
                return Path(item["destination"])
        return None

    def montage(self, block: int) -> Path | None:
        tag = tag_for(block)
        for item in self.entries:
            if item["kind"] == "p4_montage" \
                    and item.get("metadata", {}).get("tag") == tag:
                return Path(item["destination"])
        return None


def stage_figures(ctx: Context, paper_dir: Path, sweep_root: Path) -> FigureRegistry:
    registry = FigureRegistry(ctx, paper_dir)
    allowed_p2 = sweep_root / ctx.trig
    for artifact in ctx.p2.get("artifacts", []):
        raw = artifact.get("path") if isinstance(artifact, dict) else None
        if not raw:
            continue
        source = Path(str(raw))
        if not source.is_absolute():
            source = REPO / source
        # Normalized P2 contains both image and non-image provenance artifacts.
        # Non-images are authorities, not candidate figures.
        if source.suffix.lower() != ".png":
            continue
        if not registry.inside(source, allowed_p2):
            ctx.anomalies.append("P2 artifact outside burst root: " + str(source))
            continue
        expected_hash = artifact.get("sha256")
        if not expected_hash:
            ctx.anomalies.append(
                "P2 PNG lacks required SHA-256; not staged: " + str(source))
            continue
        if not source.is_file() or sha256(source) != expected_hash:
            ctx.anomalies.append(
                "P2 artifact hash mismatch/missing; not staged: " + str(source))
            continue
        registry.stage(source, "p2_step_or_temporal")

    for sidecar, side, png in ctx.panels:
        raw_bin = str(side.get("bin", "")).strip().lower()
        bin_arg = "tint" if raw_bin in {"tint", "-1"} else str(int(float(raw_bin)))
        registry.stage(
            png, "p3_sed",
            {"bin": bin_arg, "model": canon_model(side.get("model")),
             "fit_mode": side.get("fit_mode")})
    for sidecar, side, png in ctx.montages:
        registry.stage(
            png, "p4_montage",
            {"tag": str(side.get("tag")), "n_missing": side.get("n_missing")})
    for sidecar, side, png in ctx.params:
        registry.stage(
            png, "p4_parameter_evolution",
            {"model": str(side.get("model")), "prefix": str(side.get("prefix"))})
    return registry


def fmt(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}g}" if finite(value) else "unavailable"


def temporal_statements(ctx: Context) -> list[str]:
    if not ctx.temporal_values_available:
        return [
            "The temporal suite is incomplete; no temporal value is substituted "
            "from a legacy catalog."
        ]
    t90 = ctx.p2.get("t90", {})
    mvt = ctx.p2.get("mvt", {})
    bala = mvt.get("canonical_bala", {})
    cwt = mvt.get("noncanonical_cwt", {})
    haar = mvt.get("noncanonical_haar", {})
    lag = ctx.p2.get("lag", {})
    pulse = ctx.p2.get("pulse", {})
    relation = ">=" if t90.get("lower_limit") else "="
    t90_text = "T90 " + relation + " " + fmt(t90.get("t90_s"))
    if finite(t90.get("t90_err_lo_s")) and finite(t90.get("t90_err_hi_s")):
        t90_text += " (+" + fmt(t90.get("t90_err_hi_s")) + "/-" + \
            fmt(t90.get("t90_err_lo_s")) + ")"
    elif finite(t90.get("t90_err_s")):
        t90_text += " ± " + fmt(t90.get("t90_err_s"))
    t90_text += " s"
    if t90.get("lower_limit"):
        t90_text += " (lower-limit reason: " + \
            str(t90.get("lower_limit_reason") or "source-window/tail rule") + ")"
    bala_status = str(bala.get("status", "unavailable"))
    if bala_status == "limit":
        limit_relation = str(bala.get("limit_relation") or ">")
        if limit_relation not in {">", ">=", "≥"}:
            limit_relation = ">"
        bala_text = limit_relation + " " + fmt(bala.get("mvt_s"), 4)
    else:
        bala_text = fmt(bala.get("mvt_s"), 4)
        if finite(bala.get("mvt_err_s")):
            bala_text += " ± " + fmt(bala.get("mvt_err_s"), 3)
    cwt_text = fmt(cwt.get("mvt_s"), 4)
    if finite(cwt.get("mvt_err_s")):
        cwt_text += " ± " + fmt(cwt.get("mvt_err_s"), 3)
    haar_relation = "<" if haar.get("upper_limit") else "="
    haar_text = haar_relation + " " + fmt(haar.get("mvt_s"), 4)
    if not haar.get("upper_limit") and finite(haar.get("mvt_err_s")):
        haar_text += " ± " + fmt(haar.get("mvt_err_s"), 3)
    interval = bala.get("interval_s")
    interval_text = "unavailable"
    if isinstance(interval, list) and len(interval) == 2 \
            and all(finite(item) for item in interval):
        duration = float(interval[1]) - float(interval[0])
        interval_text = (
            "[" + fmt(interval[0], 5) + ", " + fmt(interval[1], 5) +
            "] s (window length " + fmt(duration, 5) + " s)")
    statements = [
        "Provisional " + str(t90.get("estimator_label", "windowed T90")) +
        ": " + t90_text + ".",
        "Provisional MVT values retain estimator labels: Bala windowed "
        "(CANONICAL, engine-selected; status=" +
        bala_status + ") " + bala_text + " s, engine-selected delta_s=" +
        fmt(bala.get("delta_s"), 4) + " s in interval " + interval_text +
        "; CWT global/grid-quantized " + cwt_text +
        " s; Haar in-chain " + haar_text + " s.",
        "Provisional window-scanned lag (25–50 versus 100–300 keV; positive "
        "means soft photons lag hard photons): tau=" + fmt(lag.get("tau_s"), 4) +
        " (+" + fmt(lag.get("sigma_r_s"), 3) + "/-" +
        fmt(lag.get("sigma_l_s"), 3) + ") ± " +
        fmt(lag.get("window_systematic_s"), 3) + "_win s.",
    ]
    tail_sigma = t90.get("tail_outside_window_sigma")
    tail_interval = t90.get("tail_outside_window_interval_s")
    if finite(tail_sigma) and isinstance(tail_interval, list) \
            and len(tail_interval) == 2 and all(finite(item) for item in tail_interval):
        statements.append(
            "Provisional outside-window tail diagnostic: " + fmt(tail_sigma, 4) +
            " sigma over [" + fmt(tail_interval[0], 5) + ", " +
            fmt(tail_interval[1], 5) + "] s. " +
            ("The lower-limit flag also limits the spectroscopic coverage; "
             "no unmodeled tail spectrum is inferred."
             if t90.get("lower_limit") else
             "This diagnostic does not trigger the lower-limit rule."))
    if t90.get("lower_limit"):
        statements.append(
            "The same approved-source-window truncation/tail condition limits "
            "spectroscopic coverage; no spectrum is inferred outside the fitted "
            "source interval. Exact reason: " +
            str(t90.get("lower_limit_reason") or "unavailable") + ".")
    gowri = pulse.get("gowri", {})
    if gowri.get("quote_phi") and finite(gowri.get("reported_phi")) \
            and finite(gowri.get("phi_err_raw")):
        statements.append(
            "Provisional pulse winner " +
            str(pulse.get("best_pulse_model", "unavailable")) +
            "; Gowri R2 passes and phi=" +
            fmt(gowri.get("reported_phi"), 3) + " ± " +
            fmt(gowri.get("phi_err_raw"), 2) + ".")
    else:
        statements.append(
            "Provisional pulse winner " +
            str(pulse.get("best_pulse_model", "unavailable")) +
            "; phi is not quoted because the Gowri R2 gate and a finite "
            "uncertainty are both required.")
    return statements


def p2_execution_statement(ctx: Context) -> str:
    if not ctx.p2 or not ctx.p2_artifacts_valid:
        return (
            "P2 execution receipts are unavailable; no command or transport-shim "
            "provenance is inferred.")
    return (
        "Normalized P2 receipt declaration: the exact default scripts/44 command "
        "ran first; an extra current-fit SHA-bound step-9 supplement ran between "
        "brief commands 2 and 3. Bala used --inner-cores 1 --seed 20260718 "
        "--resume. The ProcessPool-to-ThreadPool transport shim applied only to "
        "scripts/46 and Bala and did not change estimators, seeds, selections, or "
        "scientific results.")


def band_alpha_records(ctx: Context) -> list[tuple[int, float, float, Any]]:
    records: list[tuple[int, float, float, Any]] = []
    if not ctx.spectroscopy_available:
        return records
    for row in ctx.table:
        block = int(float(row["BLOCK"]))
        if block < 0 or "BAND_STATUS" not in row.colnames:
            continue
        if str(row["BAND_STATUS"]).strip().upper() != "OK" \
                or not truthy(row["BAND_VALID"]) \
                or row_float(row, "BAND_ALPHA") is None:
            continue
        records.append((block, float(row["T_START"]), float(row["T_STOP"]), row))
    return records


def slope_summary(ctx: Context) -> str:
    if not ctx.spectroscopy_available:
        return "The Band-alpha census is unavailable because exact promoted P1 authority is absent."
    records = band_alpha_records(ctx)
    values = [float(row["BAND_ALPHA"]) for _, _, _, row in records]
    resolved = sum(int(float(row["BLOCK"])) >= 0 for row in ctx.table)
    if not values:
        return "No resolved status-OK, physically valid Band fit has a finite BAND_ALPHA."
    harder = sum(value > -2.0 / 3.0 for value in values)
    comparison = (
        str(harder) + " of " + str(len(values)) +
        " usable Band-alpha central values are harder than -2/3"
        if harder else
        "none of " + str(len(values)) +
        " usable Band-alpha central values is harder than -2/3"
    )
    return (
        "Provisional Band-model low-energy slope census (not a mixed winning-model "
        "index): among " + str(len(values)) + "/" + str(resolved) +
        " resolved status-OK, physically valid Band fits, BAND_ALPHA=" +
        f"{min(values):.3g}" + " to " + f"{max(values):.3g}" +
        "; " + comparison + ". The count uses fitted central values; the "
        "per-bin table retains parameter errors. This diagnostic does not "
        "identify an emission mechanism.")


def report_band_alpha_table(ctx: Context) -> list[str]:
    records = band_alpha_records(ctx)
    if not records:
        return ["> Missing: no usable resolved Band-alpha measurements.", ""]
    lines = [
        "| bin | provisional interval (s) | provisional BAND_ALPHA | central value vs -2/3 |",
        "|---:|---:|---:|---|",
    ]
    for block, start, stop, row in records:
        alpha = float(row["BAND_ALPHA"])
        lines.append(
            "| " + str(block) + " | [" + f"{start:.6g}" + ", " +
            f"{stop:.6g}" + "] | " + measurement(row, "BAND_ALPHA") +
            " | " + ("above" if alpha > -2.0 / 3.0 else "at or below") + " |")
    return lines + [""]


def tail_summary(ctx: Context) -> str:
    if not ctx.spectroscopy_available:
        return "The terminal time-bin phase is unavailable without exact promoted P1 authority."
    resolved = [item for item in ctx.winners if item.block >= 0]
    if not resolved:
        return "The terminal time-bin phase is unavailable."
    tail = max(resolved, key=lambda item: item.block)
    return (
        "Provisional operational tail phase: the final resolved bin is " +
        str(tail.block) + " [" + f"{tail.start:.6g}" + ", " +
        f"{tail.stop:.6g}" + "] s, with nominal AIC minimum " + tail.model +
        " and ΔAIC<2 tie set " + (", ".join(tail.ties) or "none") +
        ". Calling it the tail identifies time order only; it does not by "
        "itself establish high-latitude emission.")


def thermal_statements(ctx: Context) -> list[str]:
    if not ctx.spectroscopy_available:
        return ["The BB-like candidate census is unavailable without exact promoted P1 authority."]
    candidates: list[str] = []
    pairs = (
        ("BAND", "BANDBB", "LRT_BANDBB_BAND", "Band+BB versus Band"),
        ("CPL", "CPLBB", "LRT_CPLBB_CPL", "CPL+BB versus CPL"),
    )
    for row in ctx.table:
        for parent, child, lrt_column, label in pairs:
            lrt = row_float(row, lrt_column)
            if str(row[child + "_STATUS"]).strip().upper() != "OK" \
                    or not truthy(row[child + "_VALID"]) \
                    or str(row[parent + "_STATUS"]).strip().upper() != "OK" \
                    or lrt is None or lrt < THERMAL_LRT_GATE:
                continue
            kt = row_float(row, child + "_KT")
            peak = BB_PEAK_FACTOR * kt if kt is not None else None
            if peak is None:
                edge_class = "UNAVAILABLE"
                edge_check = "unavailable"
            elif peak < L28_TRUST_KEV:
                edge_class = "EDGE_CONSTRAINED"
                edge_check = "at or above 8 keV" if peak >= 8.0 else "below 8 keV"
            elif peak < L28_CLEAR_KEV:
                edge_class = "EDGE_MARGINAL"
                edge_check = "at or above 8 keV"
            else:
                edge_class = "IN_BAND"
                edge_check = "at or above 8 keV"
            candidates.append(
                bin_label(int(float(row["BLOCK"]))) + ": " + label +
                ", stored nested LRT=" + fmt(lrt, 4) + " (gate >=9.2), kT=" +
                measurement(row, child + "_KT") + " keV, 3.9207*kT=" +
                fmt(peak, 4) + " keV (" + edge_check + "), L28=" + edge_class)
    if not candidates:
        return [
            "No status-OK, physically valid Band+BB-versus-Band or CPL+BB-versus-CPL "
            "pair passes the stored nested-LRT >=9.2 statistical-candidate gate. "
            "A BB-like model in an AIC tie set remains ranking morphology, not a "
            "thermal candidate."
        ]
    return [
        "Provisional nested-pair BB statistical candidates: " + "; ".join(candidates) + ".",
        "These are statistical candidates only. The component-LRT boundary is not "
        "simulation-calibrated; residual evidence is UNGATED/not adjudicated. The "
        "8 keV check alone never promotes evidence. LET extrapolation, per-NaI "
        "coherence, background sanity, and the L25 BB-versus-low-break identity "
        "comparison are unverified. L28's transfer from a 2SBPL boundary to "
        "3.9207*kT is project policy, not a calibrated detector theorem.",
    ]


def broadband_statements(ctx: Context) -> list[str]:
    if ctx.trig not in BROADBAND:
        return []
    if not ctx.spectroscopy_available:
        return [
            "Broadband fit effects are unavailable without an exact hash-bound "
            "promoted P1 authority; no legacy GBM/LLE/LAT result is substituted."
        ]
    fit_dets = [str(item) for item in ctx.fit_meta.get("fit_dets", [])]
    lle = "lle" in fit_dets
    lat_blocks: list[int] = []
    if ctx.table is not None and "PLUGIN_DETS" in ctx.table.colnames:
        for row in ctx.table:
            plugins = {item.strip() for item in str(row["PLUGIN_DETS"]).split(",")}
            if "LAT" in plugins:
                lat_blocks.append(int(float(row["BLOCK"])))
    range_text = ", ".join(str(item) for item in ctx.fit_meta.get("LLE_RANGES", []))
    blocks = ", ".join(bin_label(item) for item in lat_blocks) or "none"
    degradation = ctx.promotion_receipt.get("broadband_degradation_reason")
    degradation_problem = ctx.promotion_receipt.get("broadband_degradation")
    degradation_text = (
        " The hash-bound promotion receipt records degradation=" +
        str(degradation_problem) + "; declared exact reason=" + str(degradation) + "."
        if degradation_problem or degradation else
        (" No hash-bound degradation reason is available."
         if not lat_blocks else ""))
    return [
        "Every-band rule: every band with usable data enters by data quality, never "
        "by detection significance. Broadband likelihood/plugin coverage is GBM NaI/BGO" +
        (" + LLE" if lle else "; required LLE is absent") +
        (" + LAT" if lat_blocks else "; no LAT block attached") +
        ". LAT-attached rows: " + blocks + "." + degradation_text,
        "Fresh fit metadata serializes LLE=" + (range_text or "not serialized") +
        " keV (20–100 MeV when 20000–100000 keV is present). LAT is selected "
        "above 100 MeV; scripts/10 serializes no finite LAT upper cut. LAT enters "
        "only the listed rows, and T_INT has no LAT unless explicitly listed.",
        "No matched GBM-only or GBM+LLE-only 24-model counterfactual was "
        "produced. The incremental effect of LLE or LAT is not isolated, so "
        "no winner or parameter change is attributed to either extra band. The "
        "defensible statement is only that LLE/LAT expanded joint likelihood coverage.",
    ]


def band_range_statement(ctx: Context) -> str:
    if not ctx.spectroscopy_available:
        return (
            "Energy ranges are not quoted because the exact promoted P1 contract "
            "is unavailable; candidate metadata, if present, is not scientific authority.")
    nai = ", ".join(map(str, ctx.fit_meta.get("NAI_RANGES", []))) or "unavailable"
    bgo = ", ".join(map(str, ctx.fit_meta.get("BGO_RANGES", []))) or "unavailable"
    exclude = ", ".join(map(str, ctx.fit_meta.get("NAI_EXCLUDE", []))) or "none"
    configured_lle = ", ".join(map(str, ctx.fit_meta.get("LLE_RANGES", [])))
    lle = (configured_lle or "range unavailable") if \
        "lle" in {str(item) for item in ctx.fit_meta.get("fit_dets", [])} else "not used"
    return (
        "Every-band rule: available bands were included by data quality, never "
        "detection significance. Serialized fit ranges are NaI " + nai +
        " keV with K-edge exclusion " + exclude + " keV; BGO " + bgo +
        " keV; LLE " + lle + " keV where present. LAT, where attached, uses "
        ">100 MeV with no finite upper cut serialized by scripts/10.")


def closure_statement(ctx: Context) -> str:
    if not ctx.p3:
        return "P3 no-model-dropped closure is missing; no completeness claim is made."
    if ctx.p3.get("status") == "RESPONSE_BLOCKED":
        return (
            "P3 is structurally RESPONSE_BLOCKED before spectroscopy: " +
            str(ctx.p3.get("reason", "reason unavailable")) +
            ". No SED pair was attempted, and no archival fit is substituted.")
    total = len(expected_p3_pairs(ctx))
    current_ok = len(ctx.panels)
    current_fail = max(0, total - current_ok)
    return (
        "Provisional no-model-dropped closure, freshly revalidated at assembly: " +
        str(current_ok) + "/" + str(total) +
        " model-bin PNG/PDF/JSON triplets pass mechanical checks; " +
        str(current_fail) +
        " persistent failure or refusal remains. Missing panels stay labeled "
        "in montages. This producer did not visually verify them.")


def p3_failure_statements(ctx: Context) -> list[str]:
    if not ctx.p3:
        return ["P3 closure is missing; no pair ledger is available."]
    if ctx.p3.get("status") == "RESPONSE_BLOCKED":
        return [
            "No model-bin pair exists because P3 is RESPONSE_BLOCKED: " +
            str(ctx.p3.get("reason", "reason unavailable"))]
    if not ctx.p3_failures:
        return ["No persistent or freshly detected P3 model-bin failure is recorded."]
    model_index = {model: index for index, model in enumerate(CANONICAL_PREFIXES)}

    def order(item: tuple[tuple[str, str], str]) -> tuple[int, int]:
        (bin_arg, model), _ = item
        bin_index = -1 if bin_arg == "tint" else int(bin_arg)
        return bin_index, model_index.get(model, len(model_index))

    return [
        bin_arg + "/" + model + ": " + reason
        for (bin_arg, model), reason in sorted(ctx.p3_failures.items(), key=order)
    ]


def approved_source_window(ctx: Context) -> tuple[float, float] | None:
    if ctx.approved_rows is None or not len(ctx.approved_rows):
        return None
    starts = {round(float(value), 9) for value in ctx.approved_rows["SRC_START"]}
    stops = {round(float(value), 9) for value in ctx.approved_rows["SRC_STOP"]}
    if len(starts) != 1 or len(stops) != 1:
        return None
    return float(next(iter(starts))), float(next(iter(stops)))


def tint_coverage_statement(ctx: Context) -> str:
    source = approved_source_window(ctx)
    if source is None:
        return "The approved source interval is unavailable; T_INT coverage cannot be audited."
    if not ctx.spectroscopy_available:
        return (
            "Approved source interval: [" + fmt(source[0], 7) + ", " +
            fmt(source[1], 7) + "] s. No exact promoted T_INT authority exists "
            "for comparison; a candidate table is not substituted.")
    tint = next((row for row in ctx.table if int(float(row["BLOCK"])) == -1), None)
    if tint is None:
        return "The canonical table has no T_INT row; integrated coverage is unavailable."
    fitted = (float(tint["T_START"]), float(tint["T_STOP"]))
    same = all(math.isclose(left, right, rel_tol=0, abs_tol=1e-8)
               for left, right in zip(source, fitted))
    if same:
        comparison = "matches the approved source interval"
    else:
        comparison = (
            "differs from the approved source interval [" + fmt(source[0], 7) +
            ", " + fmt(source[1], 7) + "] s; the coverage gap is declared because "
            "the known scripts/10 T_INT audit item remains open")
    return (
        "Provisional T_INT fitted/block span: [" + fmt(fitted[0], 7) + ", " +
        fmt(fitted[1], 7) + "] s; it " + comparison + ".")


def approved_detector_statement(ctx: Context) -> str:
    if ctx.approved_rows is None:
        return "Approved detector rows are unavailable."
    detectors = []
    for row in ctx.approved_rows:
        detector = str(row["DETECTOR"]).strip()
        angle = row_float(row, "DET_ANGLE")
        detectors.append(
            detector + " (DET_ANGLE=" +
            (fmt(angle, 5) + " deg" if angle is not None else "unavailable") + ")")
    stamps = sorted({
        str(row["APPROVED_BY"]) + " / " + str(row["APPROVAL_MODE"]) +
        " / " + str(row["APPROVED_UTC"])
        for row in ctx.approved_rows
    })
    return (
        "Adopted approved detectors: " + ", ".join(detectors) +
        ". Gate stamp(s): " + "; ".join(stamps) +
        ". These rows are inherited, not re-selected.")


def report_background_table(ctx: Context) -> list[str]:
    if ctx.approved_rows is None:
        return ["> Missing: approved detector/background rows.", ""]
    lines = [
        "| detector | provisional approved negative background (s) | provisional approved positive background (s) | window source |",
        "|---|---:|---:|---|",
    ]
    for row in ctx.approved_rows:
        lines.append(
            "| " + str(row["DETECTOR"]) + " | [" + fmt(row["BKG_NEG_START"], 7) +
            ", " + fmt(row["BKG_NEG_STOP"], 7) + "] | [" +
            fmt(row["BKG_POS_START"], 7) + ", " + fmt(row["BKG_POS_STOP"], 7) +
            "] | " + str(row["WINDOW_SOURCE"]) + " |")
    return lines + [""]


def report_blocks_table(ctx: Context) -> list[str]:
    if ctx.blocks is None:
        return ["> Missing: adopted block table.", ""]
    lines = [
        "| detector | block | provisional interval (s) | significance | merged | constituents | polynomial order |",
        "|---|---:|---:|---:|---|---:|---:|",
    ]
    for row in ctx.blocks:
        lines.append(
            "| " + str(row["DETECTOR"]) + " | " +
            str(int(row["BLOCK_INDEX"])) + " | [" +
            fmt(row["T_START"], 7) + ", " + fmt(row["T_STOP"], 7) + "] | " +
            fmt(row["SIGNIFICANCE"], 5) + " | " + str(row["IS_MERGED"]) +
            " | " + str(row["CONSTITUENT_COUNT"]) + " | " +
            str(row["POLY_ORDER"]) + " |")
    return lines + [""]


def winner_census(ctx: Context) -> dict[str, int]:
    census: dict[str, int] = {}
    if not ctx.spectroscopy_available:
        return census
    for winner in ctx.winners:
        census[winner.model] = census.get(winner.model, 0) + 1
    return dict(sorted(census.items(), key=lambda item: (-item[1], item[0])))


def report_figure(path: Path | None, report_path: Path, caption: str) -> list[str]:
    if path is None or not path.is_file():
        return ["> Figure missing: " + caption + " No image is embedded.", ""]
    relative = os.path.relpath(path, report_path.parent)
    return [
        "![" + caption + "](" + relative + ")", "",
        "*" + caption + " All values are provisional; figure status: " + GATE + ".*", "",
    ]


def render_report(ctx: Context, figures: FigureRegistry,
                  report_path: Path, legacy_result: dict[str, Any]) -> str:
    lines = [
        "# " + ctx.grb + " — " + ctx.trig, "",
        "**Producer report. Every quantitative value is PROVISIONAL. Every new "
        "figure is " + GATE + ". This is not a verifier verdict or PI delivery.**", "",
        "- Campaign burst: #" + (str(ctx.number) if ctx.number is not None else "fixture"),
        "- Generated UTC: " + utcnow(),
        "- Fresh fit authority: " + display_path(ctx.fit_path),
        "- P2 authority: " + display_path(ctx.p2_path),
        "- Model closure: " + str(len(set(ctx.prefixes))) + "/24 models", "",
        "## Step 0b - literature harvest", "",
        "This paper cites only the applicable method entries already present in the "
        "unchanged burst-2 refs.bib (AIC, Bayesian blocks, GBM spectral fitting, and "
        "3ML); unrelated burst-specific entries are not reused. No reference was "
        "added or hand-written. Because no "
        "authorized burst-specific citation/redshift source is present, those "
        "claims and rest-frame quantities are omitted.", "",
        "## Step 0 — identity and scope", "",
        ctx.grb + " is reported as one single-pulse campaign member. No "
        "burst-specific literature claim is introduced by the assembler; the "
        "unchanged bibliography supplies method references only. Redshift and "
        "rest-frame values are omitted unless a fresh authorized sidecar supplies them.", "",
        "## Step 1 — data inventory", "",
    ]
    if ctx.spectroscopy_available:
        lines += [
            "Fresh fit metadata lists detector plugins: " +
            (", ".join(map(str, ctx.fit_meta.get("fit_dets", []))) or "unavailable") +
            ". Reference detector: " +
            str(ctx.fit_meta.get("reference_det",
                                 ctx.fit_meta.get("canonical_det", "unavailable"))) +
            ". These are fit-product facts, not a new selection.", "",
            band_range_statement(ctx), ""]
    else:
        lines += [
            "> Missing: exact promoted P1 metadata. Candidate fit metadata, if "
            "present, is inventoried as unvalidated evidence but does not drive "
            "plugin, energy-range, T_INT, or science claims.", ""]
    lines += report_figure(
        figures.named(ctx.trig + "_step1_inventory.png"), report_path,
        "Step 1 producer inventory and response coverage.")
    lines += [
        "## Step 2 — detector selection", "",
        approved_detector_statement(ctx) + " A missing approved detector is a "
        "reported degradation, not permission to substitute another detector.", "",
        "## Step 3 — background selection", "",
        "Approved Stage-1 background intervals are inherited by the engines and "
        "listed below from the hash-recorded primary catalog. The assembler does "
        "not reopen the decision or copy values from legacy reports.", ""]
    lines += report_background_table(ctx)
    lines += report_figure(
        figures.named(ctx.trig + "_step3_background.png"), report_path,
        "Step 3 approved-background diagnostic.")
    lines += ["## Step 4 — source interval", ""]
    source_window = approved_source_window(ctx)
    if source_window is not None:
        lines += [
            "Provisional approved source interval: [" +
            f"{source_window[0]:.6g}" + ", " + f"{source_window[1]:.6g}" +
            "] s, common to all adopted detector rows and inherited unchanged.", ""]
    else:
        lines += ["> Missing: consistent approved source-window provenance; no interval is guessed.", ""]
    lines += report_figure(
        figures.named(ctx.trig + "_step4_source.png"), report_path,
        "Step 4 adopted source-window diagnostic.")

    # PI-required presentation order: temporal precedes spectroscopy.
    lines += ["## Step 7 — temporal analysis (presented before spectroscopy)", ""]
    for statement in temporal_statements(ctx):
        lines += [statement, ""]
    lines += [p2_execution_statement(ctx), ""]
    for suffix, caption in (
        ("step7_temporal", "Windowed and energy-resolved duration diagnostic."),
        ("step7_pulse", "Pulse-shape model comparison."),
        ("step7_mvt", "Labeled Bala, CWT, and Haar MVT comparison."),
        ("step7_lag_latbright", "Window-scanned 25–50 versus 100–300 keV lag."),
    ):
        lines += report_figure(
            figures.named(ctx.trig + "_" + suffix + ".png"), report_path, caption)

    lines += ["## Step 5 — time binning", ""]
    resolved = ([winner for winner in ctx.winners if winner.block >= 0]
                if ctx.spectroscopy_available else [])
    if resolved:
        lines += [
            "Provisional grid: " + str(len(resolved)) +
            " resolved bins spanning [" + f"{resolved[0].start:.6g}" + ", " +
            f"{resolved[-1].stop:.6g}" + "] s, plus T_INT.", ""]
    else:
        if ctx.blocks is not None:
            intervals = sorted({
                (float(row["T_START"]), float(row["T_STOP"])) for row in ctx.blocks})
            lines += [
                "Adopted P0 block grid contains " + str(len(intervals)) +
                " unique intervals; no canonical spectral row is inferred from it.", ""]
        else:
            lines += ["> Missing: adopted and canonical bin rows.", ""]
    lines += report_blocks_table(ctx)
    lines += [tint_coverage_statement(ctx), ""]
    lines += report_figure(
        figures.named(ctx.trig + "_step5_binning.png"), report_path,
        "Step 5 Bayesian-block and significance-merge binning.")

    lines += ["## Step 6 — time-resolved spectroscopy", ""]
    if ctx.spectroscopy_available:
        lines += [
            "The fresh promoted table ranks all status-OK, physical-validity-passing "
            "fits across the exact canonical 24-model registry. The nominal AIC "
            "minimum is listed first, but every model at ΔAIC < 2 is reported as "
            "tied; no nominal winner is treated as unique physical identity.", ""]
    else:
        lines += [
            "> Spectroscopy incomplete: no exact promoted 24-model P1 authority is "
            "available. No spectral value is recovered from a legacy fit.", ""]
    if ctx.spectroscopy_available and ctx.winners:
        lines += [
            "| bin | provisional interval (s) | nominal AIC minimum | provisional AIC | "
            "ΔAIC to second | ΔAIC<2 tie set | provisional parameters | persistent FAILs |",
            "|---|---:|---|---:|---:|---|---|---|"]
        for winner in ctx.winners:
            lines.append(
                "| " + bin_label(winner.block) + " | [" +
                f"{winner.start:.6g}" + ", " + f"{winner.stop:.6g}" + "] | " +
                winner.model + " | " + fmt(winner.aic, 7) + " | " +
                fmt(winner.margin, 3) + " | " +
                (", ".join(winner.ties) or "none") + " | " +
                winner.params_md + " | " +
                (", ".join(winner.failed) or "none") + " |")
        lines.append("")
    else:
        lines += ["> Missing: no fresh spectral ranking is available.", ""]
    lines += [slope_summary(ctx), ""]
    lines += report_band_alpha_table(ctx)
    lines += [tail_summary(ctx), "", tint_coverage_statement(ctx), ""]
    for statement in thermal_statements(ctx) + broadband_statements(ctx):
        lines += [statement, ""]

    lines += ["## Step 8 — SED grid and parameter evolution", "",
              closure_statement(ctx), ""]
    failures = p3_failure_statements(ctx)
    lines += ["Persistent P3 pair ledger:", ""]
    lines.extend("- " + item for item in failures)
    lines.append("")
    integrated = (next((item for item in ctx.winners if item.block == -1), None)
                  if ctx.spectroscopy_available else None)
    lines += report_figure(
        figures.pair(-1, integrated.prefix)
        if integrated is not None and integrated.prefix else None,
        report_path,
        "Integrated SED for nominal " +
        (integrated.model if integrated is not None else "unavailable") +
        " AIC minimum.")
    lines += report_figure(
        figures.montage(-1), report_path,
        "Integrated 24-model AIC-ordered montage; failures remain placeholders.")
    lines += [
        "Parameter-evolution model selection follows the raw finite-AIC minimum "
        "used by scripts/41d and the P4 validator. It may differ from this "
        "report's status-OK, physical-validity-gated nominal-winner table.", ""]
    parameter_entries = [
        item for item in figures.entries
        if item["kind"] == "p4_parameter_evolution"]
    for item in parameter_entries:
        model = item.get("metadata", {}).get("model", "model")
        lines += report_figure(
            Path(item["destination"]), report_path,
            "Provisional " + str(model) + " parameter evolution.")
    if not parameter_entries:
        lines += [
            "> Parameter-evolution products missing: no validated P4 parameter "
            "figure is embedded.", ""]
    if ctx.p4_tables:
        lines += ["Hash-bound per-spectrum 24-model parameter tables:", ""]
        for path in ctx.p4_tables:
            relative = os.path.relpath(path, report_path.parent)
            lines.append(
                "- [" + path.name + "](" + relative + ") — SHA-256 `" +
                sha256(path) + "`")
        lines.append("")
    else:
        lines += ["> Missing: P4 per-spectrum all-model parameter tables.", ""]

    lines += ["## Step 9 — quality control", ""]
    lines += report_figure(
        figures.named(ctx.trig + "_step9_qc.png"), report_path,
        "Step 9 producer-side QC bound to the current fit.")
    lines += [
        "Mechanical hash checks (and AIC checks where spectroscopy exists) are not "
        "visual verification. Every "
        "figure remains UNGATED for the independent Claude-side pass.", "",
        "## Discussion", "", slope_summary(ctx), "", tail_summary(ctx), ""]
    for statement in thermal_statements(ctx):
        lines += [statement, ""]
    lines += [
        "Timing quantities remain estimator-labeled, and the lag retains its "
        "fit-window systematic. This burst alone cannot establish a population relation.", "",
        "## Analysis provenance", "",
        authority_statement(ctx), "",
        merge_evidence_statement(ctx), "",
        p2_execution_statement(ctx), "",
        script48_statement(legacy_result), "",
        PDF_MARKER_DECLARATION, "",
        "Figure state: " + GATE + ". Producer: " + PRODUCER +
        ". No verifier verdict was written.", "",
        "## Numbered summary", ""]
    summaries = temporal_statements(ctx)[:3] + [slope_summary(ctx), tail_summary(ctx)] \
        + thermal_statements(ctx)[:1] + [closure_statement(ctx)]
    lines.extend(str(index) + ". " + value for index, value in enumerate(summaries, 1))
    lines += ["", "## Appendix A — per-bin all-model montages", ""]
    for winner in resolved:
        lines += report_figure(
            figures.montage(winner.block), report_path,
            "Bin " + str(winner.block) + " all-model montage.")
    lines += ["## Appendix B — complete persistent P3 failure ledger", ""]
    lines.extend("- " + item for item in failures)
    lines.append("")
    lines += ["## Explicit anomalies, deviations, and unfinished items", ""]
    if ctx.anomalies:
        lines.extend("- " + item for item in ctx.anomalies)
    else:
        lines.append("- No mechanical assembly anomaly; visual verification is unfinished.")
    lines.append("- " + PDF_MARKER_DECLARATION)
    lines += ["", "**Final producer state: all numbers provisional; all figures " + GATE + ".**", ""]
    return normalize_hyphens("\n".join(lines))


def tex_escape(value: Any) -> str:
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
        "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "/": r"/\allowbreak{}",
        "<": r"\textless{}", ">": r"\textgreater{}",
        "±": r"$\pm$", "Δ": r"$\Delta$", "α": r"$\alpha$",
        "–": "--", "—": "---", "≥": r"$\geq$", "≤": r"$\leq$",
    }
    return "".join(replacements.get(char, char) for char in str(value))


def tex_hash(value: Any) -> str:
    text = str(value)
    return r"\texttt{" + r"\allowbreak{}".join(
        tex_escape(text[index:index + 8]) for index in range(0, len(text), 8)
    ) + "}"


def tex_breakable_filename(value: Any) -> str:
    escaped = tex_escape(value).replace(r"\_", r"\_\allowbreak{}")
    return r"\texttt{" + escaped + "}"


def tex_figure(path: Path | None, caption: str, label: str,
               wide: bool = False) -> str:
    if path is None or not path.is_file():
        return (
            r"\par\noindent\textbf{Figure missing:} " + tex_escape(caption) +
            " No image is embedded; the absence remains explicit.\n")
    environment = "figure*" if wide else "figure"
    width = r"\textwidth" if wide else r"\columnwidth"
    return (
        "\\" + "begin{" + environment + "}\n" +
        r"\includegraphics[width=" + width + "]{figs/" +
        tex_escape(path.name) + "}\n" +
        r"\caption{" + tex_escape(caption) +
        " All values are provisional; this producer figure is UNGATED "
        "pending independent Claude verification. " +
        r"\label{" + label + "}}\n" +
        "\\" + "end{" + environment + "}\n")


def tex_winner_table(ctx: Context) -> str:
    if not ctx.spectroscopy_available or not ctx.winners:
        return "No fresh canonical winner table is available."
    rows: list[str] = []
    parameter_items: list[str] = []
    for winner in ctx.winners:
        label = r"T$_{\rm INT}$" if winner.block == -1 else str(winner.block)
        rows.append(
            label + " & " +
            "$[" + f"{winner.start:.3f}" + "," + f"{winner.stop:.3f}" + "]$ & " +
            tex_escape(winner.model) + " & " + fmt(winner.aic, 7) + " & " +
            fmt(winner.margin, 3) + " & " +
            tex_escape(", ".join(winner.ties) or "none") + " & " +
            str(len(winner.failed)) + r" \\")
        parameter_items.append(
            r"\item[" + label + " (" + tex_escape(winner.model) + ")] " +
            winner.params_tex + "; persistent FAIL models: " +
            tex_escape(", ".join(winner.failed) or "none") + ".")
    header = (
        r"Bin & Interval (s) & Nominal model & AIC & $\Delta$AIC$_2$ & "
        r"Tie set & $N_{\rm FAIL}$ \\ \hline")
    return (
        r"""\onecolumngrid
{\scriptsize
\setlength\LTleft{0pt}\setlength\LTright{0pt}
\begin{longtable}{lccrrp{0.28\textwidth}c}
\caption{Provisional AIC ranking by interval. A nominal minimum is not called
unique when another valid model has $\Delta\mathrm{AIC}<2$.\label{tab:winners}}\\
\hline
""" + header + r"""
\endfirsthead
\multicolumn{7}{c}{Table \thetable\ continued}\\\hline
""" + header + r"""
\endhead
\hline\multicolumn{7}{r}{Continued on next page}\\
\endfoot
\hline
\endlastfoot
""" + "\n".join(rows) + r"""
\end{longtable}
\noindent\textit{Note.} All values are provisional. Only status-OK,
physical-validity-passing fits enter the ranking. Persistent failures remain
explicit below.
}
\twocolumngrid
\paragraph{Provisional nominal-winner parameters and persistent failures.}
\begin{description}
""" + "\n".join(parameter_items) + r"""
\end{description}
""")


def tex_band_alpha_table(ctx: Context) -> str:
    records = band_alpha_records(ctx)
    if not records:
        return "No usable resolved Band-alpha measurements are available."
    rows = []
    for block, start, stop, row in records:
        alpha = float(row["BAND_ALPHA"])
        rows.append(
            str(block) + " & $[" + f"{start:.3f}" + "," + f"{stop:.3f}" +
            "]$ & $" + measurement(row, "BAND_ALPHA", True) + "$ & " +
            ("above" if alpha > -2.0 / 3.0 else "at or below") + r" \\")
    header = (
        r"Bin & Interval (s) & Band $\alpha$ & Central value vs. $-2/3$ \\ \hline")
    return (
        r"""\onecolumngrid
{\scriptsize
\begin{longtable}{lccc}
\caption{Provisional resolved-bin Band-alpha census. The comparison uses
central fitted values; uncertainties remain explicit.\label{tab:bandalpha}}\\
\hline
""" + header + r"""
\endfirsthead
\multicolumn{4}{c}{Table \thetable\ continued}\\\hline
""" + header + r"""
\endhead
\hline\multicolumn{4}{r}{Continued on next page}\\
\endfoot
\hline
\endlastfoot
""" + "\n".join(rows) + r"""
\end{longtable}
\noindent\textit{Note.} Selection: BLOCK$\geq0$, BAND\_STATUS=OK,
BAND\_VALID=true, and finite BAND\_ALPHA. These are Band-model values, not
mixed winning-model indices.
}
\twocolumngrid
""")


def tex_background_table(ctx: Context) -> str:
    if ctx.approved_rows is None:
        return "The approved detector/background rows are unavailable."
    rows = []
    for row in ctx.approved_rows:
        rows.append(
            tex_escape(row["DETECTOR"]) + " & $[" + fmt(row["BKG_NEG_START"], 7) +
            "," + fmt(row["BKG_NEG_STOP"], 7) + "]$ & $[" +
            fmt(row["BKG_POS_START"], 7) + "," + fmt(row["BKG_POS_STOP"], 7) +
            "]$ & " + tex_escape(row["WINDOW_SOURCE"]) + r" \\")
    return (
        r"""\begin{deluxetable*}{lccc}
\tabletypesize{\scriptsize}
\tablecaption{Adopted Stage-1 background intervals.\label{tab:background}}
\tablehead{\colhead{Detector} & \colhead{Negative interval (s)} &
\colhead{Positive interval (s)} & \colhead{Window source}}
\startdata
""" + "\n".join(rows) + r"""
\enddata
\tablecomments{All values are provisional for this producer report. The
approved rows and their gate stamps are inherited, not re-adjudicated.}
\end{deluxetable*}
""")


def tex_blocks_table(ctx: Context) -> str:
    if ctx.blocks is None:
        return "The adopted block table is unavailable."
    rows = []
    for row in ctx.blocks:
        rows.append(
            tex_escape(row["DETECTOR"]) + " & " + str(int(row["BLOCK_INDEX"])) +
            " & $[" + fmt(row["T_START"], 7) +
            "," + fmt(row["T_STOP"], 7) + "]$ & " +
            fmt(row["SIGNIFICANCE"], 5) + " & " + tex_escape(row["IS_MERGED"]) +
            " & " + tex_escape(row["CONSTITUENT_COUNT"]) + " & " +
            tex_escape(row["POLY_ORDER"]) + r" \\")
    header = (
        r"Detector & Block & Interval (s) & Significance & Merged & "
        r"Constituents & Polynomial order \\ \hline")
    return (
        r"""\onecolumngrid
{\scriptsize
\begin{longtable}{llccccc}
\caption{Provisional adopted block grid.\label{tab:blocks}}\\
\hline
""" + header + r"""
\endfirsthead
\multicolumn{7}{c}{Table \thetable\ continued}\\\hline
""" + header + r"""
\endhead
\hline\multicolumn{7}{r}{Continued on next page}\\
\endfoot
\hline
\endlastfoot
""" + "\n".join(rows) + r"""
\end{longtable}
\noindent\textit{Note.} The Stage-1/2 grid is adopted without re-binning.
}
\twocolumngrid
""")


def render_tex(ctx: Context, figures: FigureRegistry,
               legacy_result: dict[str, Any]) -> str:
    temporal = temporal_statements(ctx)
    integrated = (next((item for item in ctx.winners if item.block == -1), None)
                  if ctx.spectroscopy_available else None)
    resolved = ([item for item in ctx.winners if item.block >= 0]
                if ctx.spectroscopy_available else [])
    detector_text = (
        ", ".join(map(str, ctx.fit_meta.get("fit_dets", []))) or "unavailable"
        if ctx.spectroscopy_available else "unavailable")
    reference = (
        ctx.fit_meta.get("reference_det",
                         ctx.fit_meta.get("canonical_det", "unavailable"))
        if ctx.spectroscopy_available else "unavailable")
    source_window = approved_source_window(ctx)
    if source_window is not None:
        source_text = "[" + f"{source_window[0]:.6g}" + ", " + \
            f"{source_window[1]:.6g}" + "] s"
    else:
        source_text = "unavailable"
    if resolved:
        binning = (
            "The provisional grid contains " + str(len(resolved)) +
            " resolved bins spanning " + f"{resolved[0].start:.6g}" + "--" +
            f"{resolved[-1].stop:.6g}" + " s, plus the integrated row.")
    else:
        if ctx.blocks is not None:
            intervals = sorted({
                (float(row["T_START"]), float(row["T_STOP"])) for row in ctx.blocks})
            binning = (
                "The adopted P0 grid contains " + str(len(intervals)) +
                " unique intervals; no spectral row is inferred from it.")
        else:
            binning = "The adopted and canonical bin grids are unavailable."

    if ctx.temporal_values_available and ctx.spectroscopy_available:
        analysis_scope = "timing and exact 24-model spectral analysis"
    elif ctx.temporal_values_available:
        analysis_scope = "temporal analysis and response-blocked spectroscopy status"
    elif ctx.spectroscopy_available:
        analysis_scope = "exact 24-model spectral analysis with incomplete timing"
    else:
        analysis_scope = "incomplete producer status"
    abstract = [
        "We present the producer-side " + analysis_scope + " of " + ctx.grb +
        ". Every quantitative value is provisional, and every figure is UNGATED "
        "pending independent Claude verification."
    ]
    if ctx.temporal_values_available:
        abstract.append(temporal[0])
    if integrated:
        abstract.append(
            "The provisional integrated AIC minimum is " + integrated.model +
            "; the tie set is " + ", ".join(integrated.ties) + ".")
    abstract.append(
        "No BB-like component is interpreted as thermal or photospheric "
        "without independent residual evidence.")

    parameter_figures = [
        Path(item["destination"]) for item in figures.entries
        if item["kind"] == "p4_parameter_evolution"
    ]
    parameter_blocks = "\n".join(
        tex_figure(path, "Provisional parameter evolution: " + path.stem,
                   "fig:param" + str(index))
        for index, path in enumerate(parameter_figures, 1))
    appendix = "\n".join(
        tex_figure(
            figures.montage(item.block),
            "Bin " + str(item.block) +
            " all-model AIC-ordered montage; persistent failures are placeholders.",
            "fig:montage" + str(item.block), True)
        for item in resolved)
    if not appendix:
        appendix = "No per-bin montage is available; no broken figure reference is emitted."
    anomalies = list(ctx.anomalies) + [PDF_MARKER_DECLARATION]
    if not ctx.anomalies:
        anomalies.insert(0,
            "No mechanical assembly anomaly; visual verification remains unfinished.")
    anomaly_items = "\n".join(r"\item " + tex_escape(item) for item in anomalies)
    summary = temporal[:3] + [slope_summary(ctx), tail_summary(ctx)] + \
        thermal_statements(ctx)[:1] + [closure_statement(ctx)]
    summary_items = "\n".join(r"\item " + tex_escape(item) for item in summary)
    broadband = "\n\n".join(tex_escape(item) for item in broadband_statements(ctx))
    thermal = "\n\n".join(tex_escape(item) for item in thermal_statements(ctx))
    p3_failures = "\n".join(
        r"\item " + tex_escape(item) for item in p3_failure_statements(ctx))
    p4_table_items = "\n".join(
        r"\item " + tex_breakable_filename(path.name) + "; SHA-256 " +
        tex_hash(sha256(path))
        for path in ctx.p4_tables)
    if not p4_table_items:
        p4_table_items = r"\item No hash-bound per-spectrum all-model table is available."
    spectroscopy_intro = (
        "The exact canonical 24-model grid is ranked with AIC. The nominal minimum "
        "is not called unique when another valid fit has Delta AIC below 2. Fit "
        "failures remain explicit."
        if ctx.spectroscopy_available else
        "No exact promoted 24-model P1 authority is available. Spectroscopy is "
        "incomplete, and no value is recovered from a legacy fit."
    )
    legacy = script48_statement({
        **legacy_result,
        "log": Path(str(legacy_result.get("log"))).name,
    }) + " " + PDF_MARKER_DECLARATION
    method_statement = (
        "The promoted P1 product uses joint GBM forward-folding with 3ML"
        if ctx.spectroscopy_available else
        "No validated P1 spectral authority exists, so no forward-folded spectral "
        "analysis is claimed for this burst.")
    inventory_statement = (
        "Fresh fit metadata lists " + detector_text +
        "; the reference plugin is " + str(reference) + "."
        if ctx.spectroscopy_available else
        "No exact promoted P1 metadata is admitted; fit-plugin, energy-range, "
        "and reference-detector claims are unavailable even if a candidate file exists.")
    integrated_figure = (
        figures.pair(-1, integrated.prefix)
        if integrated is not None and integrated.prefix else None)
    sed_clearpage = r"\clearpage" if (
        integrated_figure is not None
        or figures.montage(-1) is not None or parameter_figures
    ) else ""
    refs_digest = sha256(REFS_SOURCE) if REFS_SOURCE.is_file() else "unavailable"
    refs_digest_tex = tex_hash(refs_digest)

    grb_tex = ctx.grb.replace(" ", "~")
    content = r"""%% Producer paper: every number provisional; every figure UNGATED.
\documentclass[twocolumn]{aastex631}
\newcommand{\grb}{GRB_VALUE}
\newcommand{\trig}{TRIG_VALUE}
\shorttitle{\grb}
\shortauthors{Chand, Sharma, \& Joshi}
\begin{document}
\title{\grb}
\author{Agentic AI Report by Vikas Chand, Khushboo Sharma, and Jagdish C. Joshi}
\noaffiliation

\begin{abstract}
ABSTRACT_VALUE
\end{abstract}
\keywords{Gamma-ray bursts (629) --- Time domain astronomy (2109)}

\section{Step 0b: Literature Harvest}\label{sec:literature}

This paper cites only the applicable method entries already present in the
unchanged \texttt{refs.bib} (SHA-256 REFS_SHA_TEX_VALUE); unrelated
burst-specific entries are not reused. No BibTeX was added or hand-written.
In the absence of an authorized burst-specific
citation/redshift source, burst-specific literature claims, redshift, and
rest-frame quantities are omitted.

\section{Step 0: Identity and Scope}\label{sec:identity}

\grb\ is campaign burst \#NUMBER_VALUE (\textit{Fermi} trigger \trig).
This document is a producer product, not a verification verdict. No
burst-specific citation is added. Redshift and rest-frame quantities are not
inferred from legacy products.

\section{Step 1: Data Inventory}\label{sec:inventory}

INVENTORY_VALUE ENERGY_RANGE_VALUE METHOD_VALUE

FIG_STEP1

\section{Step 2: Detector Selection}\label{sec:detectors}

\begin{sloppypar}
APPROVED_DETECTOR_VALUE Missing approved plugins would be reported rather
than silently replaced.
\end{sloppypar}

\section{Step 3: Background Selection}\label{sec:background}

Approved Stage-1 backgrounds are inherited. This assembler does not reopen
the catalog or reconstruct intervals from legacy prose.

BACKGROUND_TABLE

FIG_STEP3

\section{Step 4: Source Interval}\label{sec:source}

The hash-recorded primary approved catalog records the adopted source interval as
\texttt{SOURCE_VALUE}. An unavailable interval is not guessed.

FIG_STEP4

\section{Step 7: Timing Analysis}\label{sec:timing}

Timing is presented before spectroscopy. All values remain provisional, and
the estimator label is part of each result.

TEMPORAL_VALUE

P2_EXECUTION_VALUE

FIG_TEMPORAL
FIG_PULSE
FIG_MVT
FIG_LAG

\section{Step 5: Time Binning}\label{sec:binning}

BINNING_VALUE Bayesian blocks follow the campaign method
\citep{2013ApJ...764..167S}.

BLOCKS_TABLE

TINT_COVERAGE_VALUE

FIG_STEP5

\section{Step 6: Time-resolved Spectroscopy}\label{sec:spectroscopy}

SPECTROSCOPY_INTRO \citep{1974ITAC...19..716A}

WINNER_TABLE

SLOPE_VALUE

ALPHA_TABLE

TAIL_VALUE

TINT_COVERAGE_VALUE

THERMAL_VALUE

BROADBAND_VALUE

\section{Step 8: SED Grid and Parameter Evolution}\label{sec:sed}

CLOSURE_VALUE

The complete persistent pair ledger is:
\begin{sloppypar}
\begin{itemize}
P3_FAILURE_VALUE
\end{itemize}
\end{sloppypar}

FIG_SED
FIG_MONTAGE
Parameter-evolution models follow the raw finite-AIC minimum used by
scripts/41d and the P4 validator. They may differ from the report's status-OK,
physical-validity-gated nominal winners.
PARAMETER_FIGURES

Hash-bound per-spectrum 24-model parameter tables are listed here and in the
staging manifest:
\begin{itemize}
P4_TABLE_VALUE
\end{itemize}

SED_CLEARPAGE_VALUE

\section{Step 9: Quality Control}\label{sec:qc}

Mechanical hash checks (and AIC checks where spectroscopy exists) establish
source consistency but are not visual verification. Every included figure remains UNGATED pending
independent Claude verification.

FIG_STEP9

\section{Discussion}\label{sec:discussion}

SLOPE_VALUE

TAIL_VALUE

THERMAL_VALUE

Timing values retain their estimator and window labels. This single burst
does not establish a population relation.

\section{Analysis Provenance}\label{sec:provenance}

\begin{sloppypar}
AUTHORITY_VALUE P2_EXECUTION_VALUE MERGE_VALUE LEGACY_VALUE The producer is
PRODUCER_VALUE. All
values are provisional and all figures are UNGATED pending independent
Claude verification.
\end{sloppypar}

\section{Summary}\label{sec:summary}

\begin{enumerate}
SUMMARY_VALUE
\end{enumerate}

\section{Declared Anomalies and Unfinished Work}\label{sec:anomalies}
\begin{sloppypar}
\begin{itemize}
ANOMALY_VALUE
\end{itemize}
\end{sloppypar}

\begin{acknowledgments}
\textit{Fermi} public data; analysis with 3ML
\citep{2015arXiv150708343V}. Producer-side product only: every value is
provisional and every figure is UNGATED pending independent verification.
\end{acknowledgments}

\appendix
\section{Per-bin All-model Montages}\label{app:montages}

APPENDIX_VALUE

\section{Complete Persistent P3 Failure Ledger}\label{app:p3failures}
\begin{sloppypar}
\begin{itemize}
P3_FAILURE_VALUE
\end{itemize}
\end{sloppypar}

\bibliography{refs}
\bibliographystyle{aasjournal}
\end{document}
"""
    values = {
        "GRB_VALUE": grb_tex,
        "TRIG_VALUE": tex_escape(ctx.trig),
        "NUMBER_VALUE": str(ctx.number if ctx.number is not None else "fixture"),
        "REFS_SHA_TEX_VALUE": refs_digest_tex,
        "ABSTRACT_VALUE": tex_escape(" ".join(abstract)),
        "DETECTOR_VALUE": tex_escape(detector_text),
        "REFERENCE_VALUE": tex_escape(reference),
        "INVENTORY_VALUE": tex_escape(inventory_statement),
        "ENERGY_RANGE_VALUE": tex_escape(band_range_statement(ctx)),
        "METHOD_VALUE": tex_escape(method_statement) +
        (r" \citep{2009ApJ...702..791M,2015arXiv150708343V}."
         if ctx.spectroscopy_available else ""),
        "APPROVED_DETECTOR_VALUE": tex_escape(approved_detector_statement(ctx)),
        "BACKGROUND_TABLE": tex_background_table(ctx),
        "SOURCE_VALUE": tex_escape(source_text),
        "TEMPORAL_VALUE": "\n\n".join(tex_escape(item) for item in temporal),
        "P2_EXECUTION_VALUE": tex_escape(p2_execution_statement(ctx)),
        "BINNING_VALUE": tex_escape(binning),
        "BLOCKS_TABLE": tex_blocks_table(ctx),
        "TINT_COVERAGE_VALUE": tex_escape(tint_coverage_statement(ctx)),
        "SPECTROSCOPY_INTRO": tex_escape(spectroscopy_intro),
        "WINNER_TABLE": tex_winner_table(ctx),
        "SLOPE_VALUE": tex_escape(slope_summary(ctx)),
        "ALPHA_TABLE": tex_band_alpha_table(ctx),
        "TAIL_VALUE": tex_escape(tail_summary(ctx)),
        "THERMAL_VALUE": thermal,
        "BROADBAND_VALUE": broadband,
        "CLOSURE_VALUE": tex_escape(closure_statement(ctx)),
        "P3_FAILURE_VALUE": p3_failures,
        "PARAMETER_FIGURES": parameter_blocks,
        "P4_TABLE_VALUE": p4_table_items,
        "SUMMARY_VALUE": summary_items,
        "ANOMALY_VALUE": anomaly_items,
        "AUTHORITY_VALUE": tex_escape(authority_statement(ctx)),
        "MERGE_VALUE": tex_escape(merge_evidence_statement(ctx, True)),
        "LEGACY_VALUE": tex_escape(legacy),
        "PRODUCER_VALUE": tex_escape(PRODUCER),
        "APPENDIX_VALUE": appendix,
        "SED_CLEARPAGE_VALUE": sed_clearpage,
        "FIG_STEP1": tex_figure(
            figures.named(ctx.trig + "_step1_inventory.png"),
            "Producer inventory and response coverage.", "fig:step1"),
        "FIG_STEP3": tex_figure(
            figures.named(ctx.trig + "_step3_background.png"),
            "Approved-background diagnostic.", "fig:step3"),
        "FIG_STEP4": tex_figure(
            figures.named(ctx.trig + "_step4_source.png"),
            "Adopted source-window diagnostic.", "fig:step4"),
        "FIG_TEMPORAL": tex_figure(
            figures.named(ctx.trig + "_step7_temporal.png"),
            "Windowed and energy-resolved duration diagnostic.",
            "fig:temporal", True),
        "FIG_PULSE": tex_figure(
            figures.named(ctx.trig + "_step7_pulse.png"),
            "Pulse-shape comparison.", "fig:pulse"),
        "FIG_MVT": tex_figure(
            figures.named(ctx.trig + "_step7_mvt.png"),
            "Bala, CWT, and Haar MVT estimators.", "fig:mvt"),
        "FIG_LAG": tex_figure(
            figures.named(ctx.trig + "_step7_lag_latbright.png"),
            "Window-scanned 25--50 versus 100--300 keV lag.", "fig:lag"),
        "FIG_STEP5": tex_figure(
            figures.named(ctx.trig + "_step5_binning.png"),
            "Bayesian-block and significance-merge grid.", "fig:step5"),
        "FIG_SED": tex_figure(
            figures.pair(-1, integrated.prefix)
            if integrated is not None and integrated.prefix else None,
            "Integrated SED for the nominal " +
            (integrated.model if integrated else "unavailable") +
            " AIC minimum.", "fig:sedtint"),
        "FIG_MONTAGE": tex_figure(
            figures.montage(-1),
            "Integrated all-model AIC-ordered montage; failures are placeholders.",
            "fig:montagetint", True),
        "FIG_STEP9": tex_figure(
            figures.named(ctx.trig + "_step9_qc.png"),
            "Producer-side QC bound to the current fit.", "fig:step9"),
    }
    # Longest keys first protects tokens such as SLOPE_VALUE from accidental
    # partial replacement by a shorter future key.
    for key in sorted(values, key=len, reverse=True):
        content = content.replace(key, values[key])
    return normalize_hyphens(content)


def write_scope(trig: str, report_path: Path | None = None,
                paper_dir: Path | None = None) -> list[str]:
    grb = grb_for_trigger(trig)
    report = report_path or SWEEP_ROOT / trig / ("REPORT_" + trig + ".md")
    paper = paper_dir or PAPER_ROOT / paper_slug(grb)
    return [
        str(report),
        str(paper / "main.tex"),
        str(paper / "refs.bib"),
        str(paper / "figs" / "*.png"),
        str(paper / "staging_manifest.json"),
        str(paper / "script48_exact.log"),
        str(paper / "compile.log"),
        str(paper / "main.aux"),
        str(paper / "main.bbl"),
        str(paper / "main.blg"),
        str(paper / "main.log"),
        str(paper / "main.out"),
        str(paper / "main.pdf"),
        str(paper / (paper_slug(grb) + ".pdf")),
    ]


def invoke_script48_exact(trig: str, paper_dir: Path) -> dict[str, Any]:
    """Run the exact brief command before the fresh adapter.

    The absent --out path currently causes a caught warning and exit zero.
    Capturing that is mandatory. No sweep destination is passed, so this
    legacy reader cannot become the report authority.
    """
    command = ["python", "scripts/48_burst_report.py", "--trig", trig]
    process = subprocess.run(
        command, cwd=REPO, capture_output=True, text=True, check=False)
    warning_text_captured = bool((process.stdout + process.stderr).strip())
    log_path = paper_dir / "script48_exact.log"
    atomic_text(
        log_path,
        "COMMAND: " + " ".join(command) + "\n" +
        "RETURN_CODE: " + str(process.returncode) + "\n" +
        "STDOUT:\n" + process.stdout + "\nSTDERR:\n" + process.stderr)
    return {
        "command": command,
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "log": str(log_path),
        "warning_text_captured": warning_text_captured,
        "used_as_scientific_authority": False,
        "deviation": (
            "Brief-exact script48 invocation had no --out destination. "
            "The fresh-source adapter writes the required report instead."),
    }


def compile_paper(paper_dir: Path) -> dict[str, Any]:
    commands = [
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        ["bibtex", "main"],
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
    ]
    log_path = paper_dir / "compile.log"
    attempted_tex = paper_dir / "main.tex"
    attempted_tex_sha256 = sha256(attempted_tex) if attempted_tex.is_file() else None
    main_pdf = paper_dir / "main.pdf"
    searchable = paper_dir / (paper_dir.name + ".pdf")
    # Exact build targets only: an earlier successful PDF must never survive a
    # failed rebuild and masquerade as current output.
    for stale in (
            main_pdf, searchable, paper_dir / "main.aux", paper_dir / "main.bbl",
            paper_dir / "main.blg", paper_dir / "main.log", paper_dir / "main.out"):
        stale.unlink(missing_ok=True)
    results: list[dict[str, Any]] = []
    with log_path.open("w") as stream:
        for command in commands:
            stream.write("\nCOMMAND: " + " ".join(command) + "\n")
            stream.flush()
            try:
                process = subprocess.run(
                    command, cwd=paper_dir, stdout=stream,
                    stderr=subprocess.STDOUT, text=True, check=False)
                results.append({
                    "command": command, "returncode": process.returncode})
            except FileNotFoundError as exc:
                results.append({
                    "command": command, "returncode": 127,
                    "error": type(exc).__name__ + ": " + str(exc)})
    final_log = paper_dir / "main.log"
    final_text = final_log.read_text(errors="replace") if final_log.is_file() else ""
    undefined_patterns = (
        r"LaTeX Warning: Citation .* undefined",
        r"LaTeX Warning: Reference .* undefined",
        r"There were undefined references",
        r"There were undefined citations",
    )
    undefined = [pattern for pattern in undefined_patterns
                 if re.search(pattern, final_text, flags=re.IGNORECASE)]
    success = (
        len(results) == len(commands) and
        all(item["returncode"] == 0 for item in results) and
        main_pdf.is_file() and not undefined)
    if success:
        temporary = searchable.with_name("." + searchable.name + ".tmp")
        shutil.copy2(main_pdf, temporary)
        os.replace(temporary, searchable)
    else:
        # A PDF produced by an early pass is not a completed four-command paper.
        # Remove it so a later-stage failure cannot masquerade as current output.
        main_pdf.unlink(missing_ok=True)
        searchable.unlink(missing_ok=True)
    return {
        "sequence": commands, "results": results, "success": success,
        "log": str(log_path),
        "attempted_main_tex_sha256": attempted_tex_sha256,
        "undefined_citation_or_reference_warnings": undefined,
        "main_pdf": str(main_pdf) if main_pdf.is_file() else None,
        "searchable_pdf": str(searchable) if success else None,
        "main_pdf_sha256": sha256(main_pdf) if main_pdf.is_file() else None,
        "searchable_pdf_sha256": sha256(searchable) if success else None,
    }


def recommend_status(ctx: Context,
                     compilation: dict[str, Any] | None) -> tuple[str, str]:
    if ctx.table is None:
        if ctx.p3.get("status") == "RESPONSE_BLOCKED" \
                and ctx.temporal_values_available:
            blocked_reasons = [
                "RESPONSE_UNCOVERED blocks P1/P3/P4 spectroscopy",
                "validated temporal values and P0/P2/P5 products remain reportable",
            ]
            if not ctx.p2_complete:
                blocked_reasons.append("P2 remains incomplete because current-fit step9 is unavailable")
            if compilation is not None and not compilation.get("success"):
                blocked_reasons.append("paper compilation failed")
            return (
                "PARTIAL",
                "; ".join(blocked_reasons))
        reason = next(
            (item for item in ctx.anomalies if item.startswith("P1 fit")),
            "P1 fit unavailable")
        return "FAILED", reason
    reasons: list[str] = []
    if tuple(ctx.prefixes) != CANONICAL_PREFIXES:
        reasons.append("P1 canonical model registry/order is not exact")
    if not ctx.promotion_receipt or not ctx.stage_manifest:
        reasons.append("P1 promotion receipt/stage manifest unavailable or ambiguous")
    if not ctx.p2_complete:
        reasons.append("P2 temporal summary incomplete")
    if not ctx.p3:
        reasons.append("P3 closure missing")
    elif not ctx.p3_fresh_complete:
        reasons.append(
            "P3 fresh closure has " + str(len(ctx.p3_failures)) +
            " missing/invalid pair(s)")
    if not ctx.p4_fresh_complete:
        reasons.append("P4 normalized product closure is not freshly COMPLETE")
    if len(ctx.montages) != len(ctx.table):
        reasons.append(
            "P4 montage closure is " + str(len(ctx.montages)) +
            "/" + str(len(ctx.table)))
    if len(ctx.p4_tables) != len(ctx.table):
        reasons.append(
            "P4 table closure is " + str(len(ctx.p4_tables)) +
            "/" + str(len(ctx.table)))
    expected_parameters = len(
        ctx.p4.get("parameter_evolution", {}).get("models", []))
    if len(ctx.params) != expected_parameters:
        reasons.append(
            "P4 parameter-evolution closure is " + str(len(ctx.params)) +
            "/" + str(expected_parameters))
    unresolved = ctx.fit_meta.get("campaign_merge", {}).get("unresolved", [])
    if unresolved:
        reasons.append("P1 campaign merge has unresolved model cells")
    integrity_prefixes = (
        "P0 ", "P1 ", "P2 artifact", "P2 PNG", "P3 ", "P4 ", "figure missing",
    )
    integrity = [
        item for item in ctx.anomalies
        if item.startswith(integrity_prefixes)
    ]
    if integrity:
        reasons.append(str(len(integrity)) + " source/figure integrity anomaly(s)")
    if compilation is not None and not compilation.get("success"):
        reasons.append("paper compilation failed")
    if reasons:
        return "PARTIAL", "; ".join(reasons)
    return "DONE", "P0-P6 assembled; independent figure verification remains"


def enforce_build_paths(args: argparse.Namespace, fit_root: Path,
                        sweep_root: Path, report_path: Path,
                        paper_dir: Path) -> None:
    """Campaign writes fail closed to the brief's exact canonical locations."""
    if args.trig in CAMPAIGN_MAP:
        expected_report = SWEEP_ROOT / args.trig / ("REPORT_" + args.trig + ".md")
        expected_paper = PAPER_ROOT / paper_slug(grb_for_trigger(args.trig))
        violations = []
        if fit_root != FIT_ROOT.resolve():
            violations.append("--fit-root")
        if sweep_root != SWEEP_ROOT.resolve():
            violations.append("--sweep-root")
        if args.p2_summary is not None:
            violations.append("--p2-summary")
        if report_path.resolve() != expected_report.resolve():
            violations.append("--report-path")
        if paper_dir.resolve() != expected_paper.resolve():
            violations.append("--paper-dir")
        if args.no_compile:
            violations.append("--no-compile")
        if args.allow_fixture:
            violations.append("--allow-fixture")
        if violations:
            raise SystemExit(
                "campaign build refuses noncanonical/test options: " +
                ", ".join(violations))
    elif not args.allow_fixture:
        raise SystemExit(
            args.trig + " is outside campaign 3-22; --allow-fixture is tests only")


def build(args: argparse.Namespace) -> int:
    fit_root = args.fit_root.resolve()
    sweep_root = args.sweep_root.resolve()
    grb = grb_for_trigger(args.trig)
    report_path = args.report_path or (
        sweep_root / args.trig / ("REPORT_" + args.trig + ".md"))
    paper_dir = args.paper_dir or PAPER_ROOT / paper_slug(grb)
    enforce_build_paths(args, fit_root, sweep_root, report_path, paper_dir)
    if args.trig in CAMPAIGN_MAP:
        if not MANIFEST_PATH.is_file():
            raise SystemExit("campaign build requires the queue manifest before any write")
        queue_guard(MANIFEST_PATH.read_text(), args.trig)
    paper_dir.mkdir(parents=True, exist_ok=True)

    # Required order: brief-exact script first; fresh-source adapter second.
    legacy = invoke_script48_exact(args.trig, paper_dir)
    ctx = load_context(
        args.trig, fit_root, sweep_root,
        args.p2_summary.resolve() if args.p2_summary else None)
    warning = (legacy.get("stdout") or "") + (legacy.get("stderr") or "")
    ctx.anomalies.append(
        "Declared script48 deviation: exact invocation returned " +
        str(legacy["returncode"]) + " and was not used as authority" +
        ("; warning captured" if warning.strip() else "; no warning text captured"))
    figures = stage_figures(ctx, paper_dir, sweep_root)

    refs_target = paper_dir / "refs.bib"
    if REFS_SOURCE.is_file():
        if refs_target.is_file() and sha256(refs_target) != sha256(REFS_SOURCE):
            ctx.anomalies.append(
                "Existing refs.bib differed and was replaced by unchanged burst-2 authority")
        refs_temporary = refs_target.with_name(
            "." + refs_target.name + "." + str(os.getpid()) + ".tmp")
        shutil.copy2(REFS_SOURCE, refs_temporary)
        os.replace(refs_temporary, refs_target)
    else:
        ctx.anomalies.append("Bibliography authority missing: " + display_path(REFS_SOURCE))

    main_tex = paper_dir / "main.tex"
    atomic_text(report_path, render_report(ctx, figures, report_path, legacy))
    atomic_text(main_tex, render_tex(ctx, figures, legacy))
    compilation = None if args.no_compile else compile_paper(paper_dir)
    if compilation is not None and not compilation.get("success"):
        ctx.anomalies.append(compile_failure_statement(compilation))
        # There is deliberately no PDF on this branch. Re-render the textual
        # deliverables so the failed build cannot be hidden from either format.
        atomic_text(report_path, render_report(ctx, figures, report_path, legacy))
        atomic_text(main_tex, render_tex(ctx, figures, legacy))
        compilation["final_main_tex_sha256_after_failure_annotation"] = sha256(main_tex)
        compilation["failure_annotation_not_compiled"] = True
    status, reason = recommend_status(ctx, compilation)
    assembler_path = Path(__file__).resolve()
    recorded_argv = [sys.executable] + [str(item) for item in sys.argv]
    argv_sha = hashlib.sha256(
        json.dumps(recorded_argv, separators=(",", ":")).encode()).hexdigest()
    manifest = {
        "schema_version": SCHEMA, "trigger": ctx.trig, "grb": ctx.grb,
        "campaign_number": ctx.number, "generated_utc": utcnow(),
        "producer": PRODUCER, "provisional": True,
        "figure_gate_status": GATE, "figure_verifier": None,
        "scientific_sources": ctx.sources,
        "assembler_invocation": {
            "argv": recorded_argv,
            "argv_sha256": argv_sha,
            "cwd": str(REPO),
            "implementation": source_record(
                assembler_path, "report_paper_assembler_implementation"),
        },
        "script48_exact_invocation": legacy,
        "staged_figures": figures.entries,
        "write_scope": write_scope(ctx.trig, report_path, paper_dir),
        "outputs": {
            "report": source_record(report_path, "standalone_markdown_report"),
            "main_tex": source_record(main_tex, "paper_source"),
            "refs_bib": source_record(refs_target, "unchanged_burst2_bibliography")
            if refs_target.is_file() else None,
            "main_pdf": source_record(
                paper_dir / "main.pdf", "compiled_paper_pdf")
            if (paper_dir / "main.pdf").is_file() else None,
            "searchable_pdf": source_record(
                paper_dir / (paper_slug(grb) + ".pdf"), "named_searchable_paper_pdf")
            if (paper_dir / (paper_slug(grb) + ".pdf")).is_file() else None,
            "compile_log": source_record(
                paper_dir / "compile.log", "paper_compile_log")
            if (paper_dir / "compile.log").is_file() else None,
            "script48_log": source_record(
                paper_dir / "script48_exact.log", "script48_exact_log"),
            "main_log": source_record(
                paper_dir / "main.log", "final_latex_main_log")
            if (paper_dir / "main.log").is_file() else None,
        },
        "model_count": len(set(ctx.prefixes)),
        "fit_rows": len(ctx.table) if ctx.table is not None else 0,
        "winner_census": winner_census(ctx),
        "p3_closure": {
            "declared_pairs": ctx.p3.get("pairs") if ctx.p3 else None,
            "declared_ok": ctx.p3.get("ok") if ctx.p3 else None,
            "declared_fail": ctx.p3.get("fail") if ctx.p3 else None,
            "fresh_expected_pairs": len(expected_p3_pairs(ctx)),
            "fresh_valid_triplets": len(ctx.panels),
            "fresh_missing_or_invalid": max(
                0, len(expected_p3_pairs(ctx)) - len(ctx.panels)),
        },
        "anomalies": ctx.anomalies,
        "pdf_artifact_marker_declaration": PDF_MARKER_DECLARATION,
        "compile": compilation or {
            "skipped": True, "reason": "--no-compile test option"},
        "recommended_boundary_status": status,
        "recommended_boundary_reason": reason,
        "reporting_rules": [
            "Every quantitative value is provisional.",
            "Every figure is UNGATED pending independent Claude verification.",
            "Delta AIC below 2 is a tie.",
            "A BB-like fit is not a photospheric detection.",
            "Missing values are not replaced from legacy sweep fits.",
        ],
    }
    staging_path = paper_dir / "staging_manifest.json"
    atomic_json(staging_path, manifest)
    print(json.dumps({
        "trigger": ctx.trig, "report": str(report_path),
        "paper": str(paper_dir), "staging_manifest": str(staging_path),
        "recommended_status": status, "reason": reason,
        "figures_staged": len(figures.entries),
        "compiled": bool(compilation and compilation.get("success")),
        "figure_gate_status": GATE,
        "write_scope": manifest["write_scope"],
    }, indent=2))
    return 0 if status == "DONE" else 2


def parse_manifest(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    tick = r"\x60"
    pattern = re.compile(
        r"^\|\s*\d+\s*\|\s*" + tick + r"(bn\d{9})" + tick +
        r"\s*\|\s*[^|]+\|\s*([^|]+)\|")
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            rows[match.group(1)] = match.group(2).strip()
    return rows


def queue_guard(text: str, trig: str) -> None:
    rows = parse_manifest(text)
    number = CAMPAIGN_MAP[trig][0]
    for previous_number, previous_trig, _ in CAMPAIGN:
        if previous_number >= number:
            break
        status = rows.get(previous_trig)
        if status not in TERMINAL:
            raise RuntimeError(
                "queue-order guard: " + previous_trig + " is " +
                str(status) + "; cannot close " + trig)


def products_text(trig: str, grb: str) -> str:
    products: list[str] = []
    blocks = SWEEP_ROOT / trig / "blocks" / ("bb_blocks_spectral_" + trig + ".ecsv")
    fit_dir = FIT_ROOT / trig
    grid = FIT_ROOT / ("sed_grid_" + trig)
    if APPROVED_CATALOG.is_file() and blocks.is_file():
        products.append("P0 approved rows/adopted blocks")
    if (fit_dir / "spectral_fits.ecsv").is_file() \
            and (fit_dir / "spectral_fits.json").is_file():
        products.append("P1 promoted fit")
    elif trig in RESPONSE_BLOCKED and (grid / "sweep_summary.json").is_file():
        products.append("P1 RESPONSE_UNCOVERED record")
    if (SWEEP_ROOT / trig / "p2_temporal_summary.json").is_file():
        products.append("P2 normalized temporal summary")
    if (grid / "sweep_summary.json").is_file():
        products.append("P3 closure")
    if (grid / "p4_products_summary.json").is_file():
        products.append("P4 normalized products/tables")
    if (SWEEP_ROOT / trig / ("REPORT_" + trig + ".md")).is_file():
        products.append("P5 standalone report")
    paper = PAPER_ROOT / paper_slug(grb)
    if (paper / "main.tex").is_file():
        products.append("P5 paper source")
    if (paper / (paper_slug(grb) + ".pdf")).is_file():
        products.append("P5 searchable PDF")
    if (paper / "staging_manifest.json").is_file():
        products.append("source/staging manifest")
    return ", ".join(products) or "no campaign boundary products"


def update_manifest_row(text: str, trig: str,
                        status: str, reason: str) -> str:
    number, grb = CAMPAIGN_MAP[trig]
    tick = chr(96)
    replacement = (
        "| " + str(number) + " | " + tick + trig + tick + " | " + grb +
        " | " + status + " | " + products_text(trig, grb) + " | " +
        reason.replace("|", "/") + " |")
    pattern = re.compile(
        r"^\|\s*" + str(number) + r"\s*\|\s*\x60" +
        re.escape(trig) + r"\x60\s*\|.*$", re.MULTILINE)
    updated, count = pattern.subn(replacement, text)
    if count != 1:
        raise RuntimeError(
            "manifest row replacement matched " + str(count) + " rows")
    return updated


def merge_evidence_statement(ctx: Context, short_fingerprint: bool = False) -> str:
    merge = ctx.fit_meta.get("campaign_merge", {})
    if not merge:
        return "P1 campaign-merge evidence unavailable."
    retries = merge.get("retry_compliance", [])
    repairs = merge.get("repairs", [])
    unresolved = merge.get("unresolved", [])
    unused = merge.get("unused_eligible", [])
    degradation = ctx.promotion_receipt.get("broadband_degradation")
    degradation_reason = ctx.promotion_receipt.get("broadband_degradation_reason")
    fingerprint = str(merge.get("input_fingerprint", "unavailable"))
    fingerprint_text = (
        fingerprint[:12] + "... (full SHA-256 in staging manifest)"
        if short_fingerprint and len(fingerprint) > 12 else fingerprint)
    retry_parts: list[str] = []
    if isinstance(retries, list):
        for item in retries:
            if not isinstance(item, dict):
                continue
            retry_parts.append(
                str(item.get("family", "unknown")) + ":" +
                str(item.get("outcome", "unavailable")) +
                ", initial FAIL cells=" +
                str(item.get("initial_literal_fail_count", "unavailable")) +
                ", compliant=" + str(item.get("compliant", "unavailable")))
    elif isinstance(retries, dict):
        retry_parts = [str(key) + ":" + str(value)
                       for key, value in sorted(retries.items())]

    def pair_name(item: dict[str, Any]) -> str:
        try:
            block = bin_label(int(item.get("block")))
        except Exception:
            block = str(item.get("block", "?"))
        return block + "/" + MODEL_NAMES.get(
            canon_model(item.get("model")), str(item.get("model", "?")))

    repair_parts = [
        pair_name(item) + " <- " + str(item.get("label", "source unavailable"))
        for item in repairs if isinstance(item, dict)]
    unresolved_parts = []
    for item in unresolved:
        if not isinstance(item, dict):
            continue
        attempts = item.get("attempts", {})
        attempts_text = ", ".join(
            str(key) + "=" + str(value) for key, value in sorted(attempts.items())) \
            if isinstance(attempts, dict) else str(attempts)
        unresolved_parts.append(
            pair_name(item) + " (" + (attempts_text or "attempts unavailable") + ")")
    statement = (
        "P1 merge fingerprint=" + fingerprint_text + ". Retry compliance: " +
        ("; ".join(retry_parts) or "unavailable") + ". Repairs (" +
        str(len(repair_parts)) + "): " +
        ("; ".join(repair_parts) or "none") + ". Unused eligible repairs=" +
        str(len(unused)) + ". Unresolved pairs (" + str(len(unresolved_parts)) +
        "): " + ("; ".join(unresolved_parts) or "none") + ".")
    if degradation is not None or degradation_reason:
        statement += (
            " Promotion receipt broadband degradation=" + str(degradation) +
            "; exact reason=" + str(degradation_reason) + ".")
    return statement


def authority_statement(ctx: Context) -> str:
    """Describe only authority branches that are actually present and valid."""
    items = ["the hash-recorded approved P0 catalog and adopted block table"]
    if ctx.spectroscopy_available:
        items.append(
            "the unique validated P1 promotion receipt/stage manifest and its "
            "promoted convention-check ECSV/JSON")
    elif ctx.table is not None:
        items.append(
            "a candidate P1 pair inspected but excluded from quantitative use "
            "because its complete promotion/contract gate did not pass")
    else:
        items.append("no P1 spectral authority")
    if ctx.temporal_values_available:
        items.append("the validated normalized P2 timing authority and hash-bound artifacts")
    elif ctx.p2:
        items.append("an incomplete normalized P2 status product, without timing substitution")
    else:
        items.append("no normalized P2 authority")
    if ctx.p3.get("status") == "RESPONSE_BLOCKED":
        items.append("the normalized P3 RESPONSE_BLOCKED closure")
    elif ctx.p3_fresh_complete:
        items.append("the freshly revalidated normalized P3 triplet closure")
    elif ctx.p3:
        items.append("an incomplete P3 status product, not a completeness authority")
    else:
        items.append("no P3 closure")
    if ctx.p4_fresh_complete:
        items.append("the normalized hash-bound P4 product authority")
    elif ctx.p4:
        items.append("an incomplete P4 status product, not a product authority")
    else:
        items.append("no COMPLETE P4 product authority")
    return (
        "Scientific statements are conditional on " + "; ".join(items) +
        ". Legacy nested sweep fits and reports are never fallback sources.")


def script48_statement(legacy_result: dict[str, Any]) -> str:
    warning = bool(legacy_result.get("warning_text_captured"))
    return (
        "Brief-exact scripts/48 invocation returned " +
        str(legacy_result.get("returncode")) + "; output was captured in " +
        str(legacy_result.get("log")) + ". " +
        ("Warning text was captured. " if warning else
         "No warning text was captured. ") +
        "Its output was not used as scientific authority. The fresh adapter "
        "report is therefore a declared implementation deviation, not a silent one.")


def compile_failure_statement(compilation: dict[str, Any]) -> str:
    failed = [
        " ".join(map(str, item.get("command", []))) +
        " -> " + str(item.get("returncode"))
        for item in compilation.get("results", [])
        if int(item.get("returncode", 1)) != 0
    ]
    undefined = compilation.get("undefined_citation_or_reference_warnings", [])
    return (
        "P5 paper compilation failed; failed command(s): " +
        ("; ".join(failed) or "sequence incomplete") +
        "; undefined citation/reference diagnostics=" + repr(undefined) +
        ". Incomplete PDFs were removed.")


def phase_state_statement(ctx: Context, p5_state: str = "DONE") -> str:
    p0 = "DONE" if ctx.approved_rows is not None and ctx.blocks is not None else "PARTIAL"
    if ctx.spectroscopy_available:
        p1 = "DONE"
    elif ctx.p3.get("status") == "RESPONSE_BLOCKED":
        p1 = "RESPONSE_BLOCKED"
    else:
        p1 = "PARTIAL"
    if ctx.p2_complete:
        p2 = "DONE"
    elif ctx.temporal_values_available:
        p2 = "PARTIAL_WITH_VALID_TIMING"
    else:
        p2 = "PARTIAL"
    if ctx.p3.get("status") == "RESPONSE_BLOCKED":
        p3 = "RESPONSE_BLOCKED"
    elif ctx.p3_fresh_complete:
        p3 = "DONE"
    elif ctx.p3:
        p3 = "PARTIAL"
    else:
        p3 = "MISSING"
    p4 = "DONE" if ctx.p4_fresh_complete else (
        "PARTIAL" if ctx.p4 else "UNAVAILABLE")
    return (
        "P0=" + p0 + ", P1=" + p1 + ", P2=" + p2 +
        ", P3=" + p3 + ", P4=" + p4 + ", P5=" + p5_state +
        ", P6=BOUNDARY")


def p6_progress(ctx: Context, status: str, wall_clock: str,
                reason: str, boundary_utc: str, p5_state: str) -> str:
    temporal = temporal_statements(ctx)
    anomalies = ctx.anomalies or [
        "No mechanical anomaly; visual verification remains pending."]
    return "\n".join([
        "<!-- CODEX_CAMPAIGN20_P6_" + ctx.trig + "_BEGIN -->",
        "## Burst #" + str(ctx.number) + " - " + ctx.trig +
        " (" + ctx.grb + ") - " + status, "",
        "- Boundary UTC: " + boundary_utc + "; wall-clock: " + wall_clock + ".",
        "- Validated phase states: " + phase_state_statement(ctx, p5_state) + ".",
        "- Provisional winner census: " +
        json.dumps(winner_census(ctx), sort_keys=True) + ".",
        "- Provisional temporal values with labels: " + " ".join(temporal[:3]),
        "- Products written: " + products_text(ctx.trig, ctx.grb) + ".",
        "- Boundary reason: " + reason + ".",
        "- Retry/repair evidence: " + merge_evidence_statement(ctx),
        "- Anomalies and deviations: " + " | ".join(anomalies + [PDF_MARKER_DECLARATION]),
        "- Figure state: " + GATE + "; no producer self-verification.",
        "- What remains: " +
        (reason + "; " if status != "DONE" else "") +
        "independent Claude verification and the PI gate.", "",
        "<!-- CODEX_CAMPAIGN20_P6_" + ctx.trig + "_END -->", "",
    ])


def vision_entry(ctx: Context, status: str, reason: str,
                 boundary_utc: str) -> str:
    lag_mc = ctx.p2.get("lag", {}).get("mc", {})
    return "\n".join([
        "<!-- CODEX_CAMPAIGN20_VISION_P5_" + ctx.trig + "_BEGIN -->",
        "## Producer entry - P5/P6 assembly - " + boundary_utc, "",
        "- Role: " + PRODUCER + "; boundary status: " + status + ".",
        "- What ran: exact `python scripts/48_burst_report.py --trig " + ctx.trig +
        "` capture, followed by the fresh-authority Markdown/AASTeX assembler, "
        "four-pass PDF compilation, and P6 source binding.",
        "- Fresh authority state: " + authority_statement(ctx),
        "- " + closure_statement(ctx),
        "- Retry/repair evidence: " + merge_evidence_statement(ctx),
        "- Boundary reason: " + reason + ".",
        "- Anomalies/deviations: " + " | ".join(ctx.anomalies + [PDF_MARKER_DECLARATION]),
        "- Figure state: " + GATE +
        ". The producer wrote no verifier verdict.",
        "- Seeds: P2 Bala seed=" +
        str(ctx.p2.get("mvt", {}).get("canonical_bala", {}).get("seed", "unavailable")) +
        "; lag Monte Carlo seed=" + str(lag_mc.get("seed", "unavailable")) +
        ", n_ccf=" + str(lag_mc.get("n_ccf", "unavailable")) +
        ", n_lag=" + str(lag_mc.get("n_lag", "unavailable")) +
        "; no stochastic computation occurred in P5/P6.", "",
        "- Figure-verifier verdict: ",
        "- Report-verifier verdict: ", "",
        "<!-- CODEX_CAMPAIGN20_VISION_P5_" + ctx.trig + "_END -->", "",
    ])


def upsert_marked_block(text: str, begin: str, end: str, block: str) -> str:
    start = text.find(begin)
    finish = text.find(end)
    if start == -1 and finish == -1:
        return text.rstrip() + "\n\n" + block
    if start == -1 or finish == -1 or finish < start:
        raise RuntimeError("incomplete existing bookkeeping marker: " + begin)
    finish += len(end)
    return text[:start].rstrip() + "\n\n" + block.rstrip() + "\n" + text[finish:].lstrip("\n")


def validate_staging_binding(staging_path: Path, staging: dict[str, Any],
                             ctx: Context) -> None:
    if staging.get("trigger") != ctx.trig or staging.get("schema_version") != SCHEMA:
        raise RuntimeError("staging manifest identity/schema mismatch")

    def check_record(record: Any, label: str) -> None:
        if not isinstance(record, dict) or not record.get("path") or not record.get("sha256"):
            raise RuntimeError(label + " lacks path/SHA-256")
        path = resolve_source(record["path"])
        if not path.is_file() or sha256(path) != record["sha256"]:
            raise RuntimeError(label + " changed or is missing: " + str(path))

    invocation = staging.get("assembler_invocation", {})
    check_record(invocation.get("implementation"), "assembler implementation")
    argv = invocation.get("argv")
    if not isinstance(argv, list) or "build" not in argv \
            or "--trig" not in argv or ctx.trig not in argv:
        raise RuntimeError("assembler invocation argv is absent or not bound to this build")
    current_argv_sha = hashlib.sha256(
        json.dumps(argv, separators=(",", ":")).encode()).hexdigest()
    if current_argv_sha != invocation.get("argv_sha256"):
        raise RuntimeError("assembler invocation argv hash mismatch")

    recorded_sources = {}
    for record in staging.get("scientific_sources", []):
        check_record(record, "scientific source")
        recorded_sources[str(resolve_source(record["path"]))] = record["sha256"]
    for current in ctx.sources:
        current_path = str(resolve_source(current["path"]))
        if recorded_sources.get(current_path) != current["sha256"]:
            raise RuntimeError("current scientific source is not bound by staging: " + current_path)
    for record in staging.get("staged_figures", []):
        source = resolve_source(record.get("source", ""))
        destination = resolve_source(record.get("destination", ""))
        if not source.is_file() or sha256(source) != record.get("source_sha256"):
            raise RuntimeError("staged figure source changed: " + str(source))
        if not destination.is_file() or sha256(destination) != record.get("destination_sha256"):
            raise RuntimeError("staged figure destination changed: " + str(destination))
    outputs = staging.get("outputs", {})
    for name in ("report", "main_tex", "refs_bib", "compile_log", "script48_log"):
        check_record(outputs.get(name), "output " + name)
    compilation = staging.get("compile", {})
    if len(compilation.get("sequence", [])) != 4 \
            or len(compilation.get("results", [])) != 4:
        raise RuntimeError("compile provenance does not contain all four commands/return codes")
    if outputs.get("main_log") is not None:
        check_record(outputs.get("main_log"), "output main_log")
    if compilation.get("success"):
        check_record(outputs.get("main_log"), "output main_log")
        check_record(outputs.get("main_pdf"), "output main_pdf")
        check_record(outputs.get("searchable_pdf"), "output searchable_pdf")
        if compilation.get("attempted_main_tex_sha256") != outputs["main_tex"]["sha256"]:
            raise RuntimeError("successful PDF was not compiled from final main.tex")
    elif outputs.get("main_pdf") is not None or outputs.get("searchable_pdf") is not None:
        raise RuntimeError("failed compilation retained a PDF output")
    recalculated, _ = recommend_status(ctx, compilation)
    if recalculated != staging.get("recommended_boundary_status"):
        raise RuntimeError(
            "staging recommendation is stale: " + str(staging.get("recommended_boundary_status")) +
            " != current " + recalculated)


def bookkeep(args: argparse.Namespace) -> int:
    if args.trig not in CAMPAIGN_MAP:
        raise SystemExit("bookkeeping limited to campaign triggers")
    if not MANIFEST_PATH.is_file() or not PROGRESS_PATH.is_file():
        raise SystemExit("campaign manifest and progress files must exist")
    manifest_text = MANIFEST_PATH.read_text()
    queue_guard(manifest_text, args.trig)
    ctx = load_context(args.trig)
    staging_path = PAPER_ROOT / paper_slug(ctx.grb) / "staging_manifest.json"
    staging, error = load_json(staging_path)
    if staging is None:
        raise SystemExit("cannot close P6: " + str(error))
    try:
        validate_staging_binding(staging_path, staging, ctx)
    except Exception as exc:
        raise SystemExit("cannot close P6: stale/unbound staging manifest: " + str(exc))
    recommended = staging.get("recommended_boundary_status")
    if args.status == "DONE" and recommended != "DONE":
        raise SystemExit(
            "assembler recommends " + str(recommended) +
            "; refusing a DONE overstatement")
    reason = args.reason or str(
        staging.get("recommended_boundary_reason", "reason unavailable"))
    boundary_utc = str(staging.get("generated_utc", "unavailable"))
    p5_state = "DONE" if staging.get("compile", {}).get("success") else "PARTIAL"

    progress_text = PROGRESS_PATH.read_text()
    progress_begin = "<!-- CODEX_CAMPAIGN20_P6_" + args.trig + "_BEGIN -->"
    progress_end = "<!-- CODEX_CAMPAIGN20_P6_" + args.trig + "_END -->"
    progress_text = upsert_marked_block(
        progress_text, progress_begin, progress_end,
        p6_progress(ctx, args.status, args.wall_clock, reason, boundary_utc, p5_state))

    vision_path = SWEEP_ROOT / args.trig / "VISION_QC.md"
    vision_text = vision_path.read_text() if vision_path.is_file() else \
        "# VISION_QC - " + args.trig + "\n\nProducer entries only.\n"
    vision_begin = "<!-- CODEX_CAMPAIGN20_VISION_P5_" + args.trig + "_BEGIN -->"
    vision_end = "<!-- CODEX_CAMPAIGN20_VISION_P5_" + args.trig + "_END -->"
    vision_text = upsert_marked_block(
        vision_text, vision_begin, vision_end,
        vision_entry(ctx, args.status, reason, boundary_utc))

    updated_manifest = update_manifest_row(
        manifest_text, args.trig, args.status, reason)
    # Crash-recoverable order: resumable detail ledgers first; the one-row
    # campaign manifest is the final commit marker.
    atomic_text(PROGRESS_PATH, normalize_hyphens(progress_text))
    atomic_text(vision_path, normalize_hyphens(vision_text))
    atomic_text(MANIFEST_PATH, normalize_hyphens(updated_manifest))
    print(json.dumps({
        "trigger": args.trig, "status": args.status,
        "manifest": str(MANIFEST_PATH), "progress": str(PROGRESS_PATH),
        "vision_qc": str(vision_path), "figure_gate_status": GATE,
        "verifier_verdict_written": False,
    }, indent=2))
    return 0


def show_scope(args: argparse.Namespace) -> int:
    print(json.dumps({
        "build_may_write": write_scope(args.trig),
        "bookkeep_may_write": [
            str(MANIFEST_PATH), str(PROGRESS_PATH),
            str(SWEEP_ROOT / args.trig / "VISION_QC.md"),
        ],
        "never_writes": [
            "scripts/", "dev/ai_guides/", "approved catalogs",
            "other burst products", ".git/",
        ],
    }, indent=2))
    return 0


def dry_run(args: argparse.Namespace) -> int:
    """Read and render in memory; write nothing and invoke no external command."""
    ctx = load_context(
        args.trig, args.fit_root.resolve(), args.sweep_root.resolve(),
        args.p2_summary.resolve() if args.p2_summary else None)
    temporary_paper = Path("/private/tmp/codex_campaign20_dry_run") / paper_slug(ctx.grb)
    figures = FigureRegistry(ctx, temporary_paper)
    legacy_fixture = {
        "returncode": "not invoked in dry-run",
        "log": "not written in dry-run",
        "used_as_scientific_authority": False,
    }
    report = render_report(
        ctx, figures, Path("/private/tmp/REPORT_" + ctx.trig + ".md"),
        legacy_fixture)
    tex = render_tex(ctx, figures, legacy_fixture)
    print(json.dumps({
        "trigger": ctx.trig, "scientific_sources_read": ctx.sources,
        "models": len(set(ctx.prefixes)),
        "fit_rows": len(ctx.table) if ctx.table is not None else 0,
        "p2_complete": ctx.p2_complete,
        "temporal_values_available": ctx.temporal_values_available,
        "p3_pairs": ctx.p3.get("pairs") if ctx.p3 else None,
        "p3_fail": ctx.p3.get("fail") if ctx.p3 else None,
        "anomalies": ctx.anomalies,
        "report_chars_rendered_in_memory": len(report),
        "tex_chars_rendered_in_memory": len(tex),
        "includegraphics_emitted": r"\includegraphics" in tex,
        "would_write": write_scope(ctx.trig),
        "actual_writes": [],
    }, indent=2))
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build")
    build_parser.add_argument("--trig", required=True)
    build_parser.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    build_parser.add_argument("--sweep-root", type=Path, default=SWEEP_ROOT)
    build_parser.add_argument("--p2-summary", type=Path)
    build_parser.add_argument("--report-path", type=Path)
    build_parser.add_argument("--paper-dir", type=Path)
    build_parser.add_argument("--no-compile", action="store_true",
                              help="unit tests and dry runs only")
    build_parser.add_argument("--allow-fixture", action="store_true",
                              help="allow completed bn081222 fixture")
    build_parser.set_defaults(func=build)

    ledger = commands.add_parser("bookkeep")
    ledger.add_argument("--trig", required=True)
    ledger.add_argument("--status", choices=sorted(TERMINAL), required=True)
    ledger.add_argument("--wall-clock", required=True)
    ledger.add_argument("--reason", default="")
    ledger.set_defaults(func=bookkeep)

    scope = commands.add_parser("scope")
    scope.add_argument("--trig", required=True)
    scope.set_defaults(func=show_scope)

    dry = commands.add_parser("dry-run")
    dry.add_argument("--trig", required=True)
    dry.add_argument("--fit-root", type=Path, default=FIT_ROOT)
    dry.add_argument("--sweep-root", type=Path, default=SWEEP_ROOT)
    dry.add_argument("--p2-summary", type=Path)
    dry.set_defaults(func=dry_run)
    return parser


def main() -> None:
    args = make_parser().parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
