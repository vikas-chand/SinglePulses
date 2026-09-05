#!/usr/bin/env python3
"""Plan and validate the campaign P3 SED grid.

The actual engine calls are launched by ``run_sed_sweep.zsh``.  Keeping the
pool in zsh is deliberate: the campaign sandbox cannot use Python process
pools, and the PI requires sixteen independent, one-core shell jobs.

This helper supports both one-burst resume runs and a campaign-wide worklist.
Its principal modes are:

``run`` (default)
    Delegate to the zsh runner.
``plan``
    Derive the exact model prefixes and bins from the canonical merged fit
    table, validate existing 41c triplets, and write only missing pairs.
``check``
    Validate one pair after an engine call.
``finalize``
    Rescan the full grid and write the 41e-compatible status and a provenance
    summary.  A reusable panel must have PNG/PDF/JSON files and both AICs in
    the sidecar must agree with the current canonical table within 0.1.
``campaign-plan`` / ``campaign-finalize``
    Build and close one worklist spanning every requested trigger.  This is
    the authoritative campaign path; per-trigger scheduling would violate the
    PI's shell-level parallelism ruling.

No figure is visually verified here.  All products remain UNGATED pending the
independent Claude figure-verifier pass.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from astropy.table import Table
from PIL import Image


REPO = Path(__file__).resolve().parents[2]
RUNTIME = Path(__file__).resolve().parent
WRAPPER = RUNTIME / "run_sed_sweep.zsh"
FIT_ROOT = REPO / "results" / "convention_check"
FIT_ENGINE = REPO / "scripts" / "10_spectral_fit_burst.py"
SED_ENGINE = REPO / "scripts" / "41c_paper_sed.py"
POOL_SIZE = 16
AIC_TOL = 0.1
TIME_TOL = 1.0e-8
CAMPAIGN_TRIGGERS = (
    "bn081224887", "bn090530760", "bn090620400", "bn090719063",
    "bn090804940", "bn090809978", "bn090829672", "bn091209001",
    "bn100122616", "bn100130729", "bn100612726", "bn100614498",
    "bn100707032", "bn101126198", "bn101225377", "bn110605183",
    "bn110618366", "bn110721200", "bn110920546", "bn110928180",
)
RESPONSE_BLOCKED = {
    "bn100130729": (
        "RESPONSE_UNCOVERED: adopted source/blocks precede every available "
        "RSP2 matrix; P1 has no canonical 24-model table"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _engine_registry() -> tuple[tuple[str, str], ...]:
    """Read name/prefix pairs from scripts/10's literal model registries.

    This keeps the helper bound to the engine authority (NR-10) without
    importing the heavy fitting module or duplicating its 24-name registry.
    THREECOMP_MODEL_SPECS is a subset/reordering and introduces no new model.
    """
    tree = ast.parse(FIT_ENGINE.read_text(), filename=str(FIT_ENGINE))
    wanted = {"MODEL_SPECS", "SHAPE_MODEL_SPECS", "HIGHE_MODEL_SPECS"}
    found: dict[str, list[tuple[str, str]]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in wanted:
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            raise RuntimeError(f"{target.id} is no longer a literal registry")
        entries: list[tuple[str, str]] = []
        for item in node.value.elts:
            if not isinstance(item, ast.Dict):
                raise RuntimeError(f"{target.id} contains a non-dict entry")
            values = {}
            for key, value in zip(item.keys, item.values):
                if (isinstance(key, ast.Constant) and isinstance(key.value, str)
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, str)):
                    values[key.value] = value.value
            if "name" not in values or "prefix" not in values:
                raise RuntimeError(f"cannot read name/prefix from {target.id}")
            entries.append((values["name"], values["prefix"]))
        found[target.id] = entries
    if set(found) != wanted:
        raise RuntimeError(f"engine registry parse incomplete: {sorted(found)}")
    combined = tuple(found[name][index]
                     for name in ("MODEL_SPECS", "SHAPE_MODEL_SPECS",
                                  "HIGHE_MODEL_SPECS")
                     for index in range(len(found[name])))
    prefixes = [prefix for _, prefix in combined]
    if len(combined) != 24 or len(set(prefixes)) != 24:
        raise RuntimeError(
            f"engine registry has {len(set(prefixes))} unique models, expected 24")
    return combined


ENGINE_REGISTRY = _engine_registry()
ENGINE_PREFIXES = tuple(prefix for _, prefix in ENGINE_REGISTRY)
NAME_TO_PREFIX = {
    re.sub(r"[^A-Z0-9]", "", name.upper()): prefix
    for name, prefix in ENGINE_REGISTRY
}
NAME_TO_PREFIX.update({prefix: prefix for prefix in ENGINE_PREFIXES})
CURRENT_41C_SHA256 = sha256(SED_ENGINE)


def canon(value: object) -> str:
    """Canonicalize the display name used by a 41c sidecar to its prefix."""
    key = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return NAME_TO_PREFIX.get(key, key)


def finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def normalize_bin(value: object) -> str:
    text = str(value).strip()
    if text.lower() == "tint" or text == "-1":
        return "tint"
    number = float(text)
    if not number.is_integer() or number < 0:
        raise ValueError(f"invalid bin argument {value!r}")
    return str(int(number))


def tag_for(bin_arg: str) -> str:
    return "TINT" if bin_arg == "tint" else f"bin{int(bin_arg)}"


@dataclass(frozen=True)
class Contract:
    trig: str
    fit_path: Path
    metadata_path: Path
    blocks_path: Path
    table: Table
    metadata: dict[str, object]
    models: tuple[str, ...]
    bins: tuple[str, ...]
    row_for_bin: dict[str, object]
    plugin_dets_for_bin: dict[str, tuple[str, ...]]
    fit_sha256: str
    metadata_sha256: str
    blocks_sha256: str

    @property
    def pairs(self) -> tuple[tuple[str, str], ...]:
        return tuple((bin_arg, model) for bin_arg in self.bins
                     for model in self.models)


@dataclass(frozen=True)
class Validation:
    ok: bool
    reason: str
    sidecar: Path | None = None
    aic_current: float | None = None
    aic_stored: float | None = None
    aic_rendered: float | None = None
    fit_mode: str | None = None
    png_sha256: str | None = None
    pdf_sha256: str | None = None
    sidecar_sha256: str | None = None


def _plugin_dets(value: object) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value).split(",") if part.strip())


def _same_times(left: Iterable[object], right: Iterable[object]) -> bool:
    a = [float(value) for value in left]
    b = [float(value) for value in right]
    return (len(a) == len(b)
            and all(abs(x - y) <= TIME_TOL for x, y in zip(a, b)))


def _required_metadata(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"canonical fit metadata missing: {path}")
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:
        raise RuntimeError(
            f"canonical fit metadata is unreadable: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"canonical fit metadata is not an object: {path}")
    return payload


def load_contract(trig: str, fit_path: Path | None = None,
                  blocks_path: Path | None = None) -> Contract:
    """Read and cross-check the canonical table, metadata, and adopted blocks."""
    path = (fit_path or (FIT_ROOT / trig / "spectral_fits.ecsv")).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"canonical fit table missing: {path}")
    table = Table.read(path, format="ascii.ecsv")
    metadata_path = path.with_name("spectral_fits.json")
    metadata = _required_metadata(metadata_path)
    if str(metadata.get("trigger", "")).strip() != trig:
        raise RuntimeError(f"{trig}: canonical metadata trigger mismatch")

    models = tuple(c[:-4] for c in table.colnames if c.endswith("_AIC"))
    if (len(models) != 24 or len(set(models)) != 24
            or set(models) != set(ENGINE_PREFIXES)):
        missing = sorted(set(ENGINE_PREFIXES) - set(models))
        extra = sorted(set(models) - set(ENGINE_PREFIXES))
        raise RuntimeError(
            f"{trig}: canonical table has {len(set(models))} unique AIC prefixes, "
            f"not the exact engine 24 (missing={missing}, extra={extra})"
        )
    for model in models:
        if f"{model}_STATUS" not in table.colnames:
            raise RuntimeError(f"{trig}: canonical table lacks {model}_STATUS")

    required_context = {"BLOCK", "T_START", "T_STOP", "N_DETS", "PLUGIN_DETS"}
    missing_context = sorted(required_context - set(table.colnames))
    if missing_context:
        raise RuntimeError(f"{trig}: canonical table lacks {missing_context}")
    block_values: list[int] = []
    for raw in table["BLOCK"]:
        value = float(raw)
        if not value.is_integer():
            raise RuntimeError(f"{trig}: non-integral BLOCK value {raw!r}")
        block_values.append(int(value))
    if len(block_values) != len(set(block_values)):
        raise RuntimeError(f"{trig}: duplicate BLOCK rows in canonical table")
    if -1 not in block_values:
        raise RuntimeError(f"{trig}: canonical table has no TINT (BLOCK=-1) row")
    if any(value < -1 for value in block_values):
        raise RuntimeError(f"{trig}: canonical table has BLOCK below -1")
    resolved = sorted(value for value in block_values if value >= 0)
    if not resolved:
        raise RuntimeError(f"{trig}: canonical table has no resolved blocks")
    if resolved != list(range(len(resolved))):
        raise RuntimeError(f"{trig}: resolved BLOCK rows are not contiguous: {resolved}")

    bins = ("tint",) + tuple(str(v) for v in resolved)
    rows = {
        ("tint" if block == -1 else str(block)): table[index]
        for index, block in enumerate(block_values)
        if block >= -1
    }
    plugin_context: dict[str, tuple[str, ...]] = {}
    for bin_arg, row in rows.items():
        dets = _plugin_dets(row["PLUGIN_DETS"])
        if not dets:
            raise RuntimeError(f"{trig} {bin_arg}: empty PLUGIN_DETS")
        if int(row["N_DETS"]) != len(dets):
            raise RuntimeError(
                f"{trig} {bin_arg}: N_DETS={row['N_DETS']} != {len(dets)} plugins")
        plugin_context[bin_arg] = dets

    reference = str(metadata.get("reference_det", "")).strip()
    canonical = str(metadata.get("canonical_det", "")).strip()
    raw_fit_dets = metadata.get("fit_dets", [])
    if not isinstance(raw_fit_dets, list):
        raise RuntimeError(f"{trig}: metadata fit_dets is not a list")
    fit_dets = tuple(str(value).strip() for value in raw_fit_dets)
    if not reference or not canonical or not fit_dets:
        raise RuntimeError(f"{trig}: incomplete reference/canonical/fit_dets metadata")
    for bin_arg, dets in plugin_context.items():
        if reference not in dets:
            raise RuntimeError(f"{trig} {bin_arg}: reference {reference} absent from plugins")
        non_lat = tuple(det for det in dets if det.upper() != "LAT")
        if any(det not in fit_dets for det in non_lat):
            raise RuntimeError(
                f"{trig} {bin_arg}: plugin context {non_lat} is outside fit_dets {fit_dets}")

    blocks_path = (blocks_path or (
        REPO / "results" / "sweep106" / trig / "blocks" /
        f"bb_blocks_spectral_{trig}.ecsv")).resolve()
    if not blocks_path.is_file():
        raise FileNotFoundError(f"{trig}: adopted block product missing: {blocks_path}")
    recorded_blocks = metadata.get("blocks_file")
    if not recorded_blocks or _resolve_from_repo(recorded_blocks) != blocks_path:
        raise RuntimeError(
            f"{trig}: metadata blocks_file is not the adopted campaign block product: "
            f"{recorded_blocks!r}")
    blocks = Table.read(blocks_path, format="ascii.ecsv")
    if not {"DETECTOR", "BLOCK_INDEX", "T_START", "T_STOP"}.issubset(blocks.colnames):
        raise RuntimeError(f"{trig}: adopted block schema is incomplete")
    mask = [str(value).strip() == reference for value in blocks["DETECTOR"]]
    ref_blocks = blocks[mask]
    if len(ref_blocks) != len(resolved):
        raise RuntimeError(
            f"{trig}: {len(ref_blocks)} reference-detector blocks != {len(resolved)} rows")
    order = sorted(range(len(ref_blocks)), key=lambda index: int(ref_blocks["BLOCK_INDEX"][index]))
    indices = [int(ref_blocks["BLOCK_INDEX"][index]) for index in order]
    if indices != resolved:
        raise RuntimeError(f"{trig}: block product indices {indices} != canonical {resolved}")
    table_starts = [rows[str(index)]["T_START"] for index in resolved]
    table_stops = [rows[str(index)]["T_STOP"] for index in resolved]
    block_starts = [ref_blocks["T_START"][index] for index in order]
    block_stops = [ref_blocks["T_STOP"][index] for index in order]
    if not _same_times(table_starts, block_starts) or not _same_times(table_stops, block_stops):
        raise RuntimeError(f"{trig}: canonical resolved intervals differ from adopted blocks")
    if int(metadata.get("n_blocks", -1)) != len(resolved):
        raise RuntimeError(f"{trig}: metadata n_blocks does not match canonical rows")
    if (not _same_times(metadata.get("bin_starts", []), table_starts)
            or not _same_times(metadata.get("bin_stops", []), table_stops)):
        raise RuntimeError(f"{trig}: metadata bin edges differ from canonical rows")
    if metadata.get("RANGES_CONVENTION") != "Chand2020_ApJ903_9":
        raise RuntimeError(f"{trig}: non-authoritative energy-range convention")

    return Contract(
        trig=trig, fit_path=path, metadata_path=metadata_path,
        blocks_path=blocks_path, table=table, metadata=metadata,
        models=models, bins=bins, row_for_bin=rows,
        plugin_dets_for_bin=plugin_context,
        fit_sha256=sha256(path), metadata_sha256=sha256(metadata_path),
        blocks_sha256=sha256(blocks_path),
    )


def default_grid(trig: str) -> Path:
    return FIT_ROOT / f"sed_grid_{trig}"


def _magic_ok(path: Path, magic: bytes) -> bool:
    try:
        if not path.is_file() or path.stat().st_size <= len(magic):
            return False
        with path.open("rb") as stream:
            return stream.read(len(magic)) == magic
    except OSError:
        return False


def _png_ok(path: Path) -> bool:
    if not _magic_ok(path, b"\x89PNG\r\n\x1a\n"):
        return False
    try:
        with Image.open(path) as image:
            if image.width <= 0 or image.height <= 0:
                return False
            image.verify()
        return True
    except Exception:
        return False


def _pdf_ok(path: Path) -> bool:
    if not _magic_ok(path, b"%PDF-"):
        return False
    try:
        with path.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - 2048), os.SEEK_SET)
            return b"%%EOF" in stream.read()
    except OSError:
        return False


def _pair_from_filename(path: Path, trig: str) -> tuple[str, str] | None:
    pattern = rf"^{re.escape(trig)}_SED_(TINT|bin[0-9]+)_(.+)$"
    match = re.match(pattern, path.stem)
    if not match:
        return None
    tag, display_model = match.groups()
    bin_arg = "tint" if tag == "TINT" else str(int(tag[3:]))
    return bin_arg, canon(display_model)


def _sidecar_pair(path: Path, trig: str) -> tuple[str, str] | None:
    try:
        side = json.loads(path.read_text())
        return normalize_bin(side["bin"]), canon(side["model"])
    except Exception:
        return _pair_from_filename(path, trig)


def _resolve_from_repo(value: object) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (REPO / path).resolve()


def display_coverage_mismatch(contract: Contract, bin_arg: str) -> str | None:
    """Describe bands present in the fit that current 41c cannot replay.

    scripts/41c currently constructs only approved GBM detector plugins.  It
    removes the approved ``lle`` row and has no LAT plugin path.  Such a panel
    must be refused, even if a GBM-only likelihood happens to land within the
    numeric AIC tolerance by chance.  We still schedule both required attempts
    so the structural limitation is evidenced rather than silently skipped.
    """
    expected = contract.plugin_dets_for_bin[bin_arg]
    missing = [det for det in expected if det.lower() == "lle" or det.upper() == "LAT"]
    if missing:
        return (
            "STRUCTURAL_COVERAGE_MISMATCH: canonical fit uses "
            f"{','.join(expected)} but current scripts/41c has no "
            f"{'+'.join(missing)} display-plugin path; bands are not dropped")
    fit_dets = tuple(str(value).strip()
                     for value in contract.metadata.get("fit_dets", []))
    expected_non_lat = tuple(det for det in expected if det.upper() != "LAT")
    if expected_non_lat != fit_dets:
        return (
            "STRUCTURAL_PLUGIN_CONTEXT_MISMATCH: canonical row uses "
            f"{','.join(expected_non_lat)} while current scripts/41c builds the "
            f"metadata-wide {','.join(fit_dets)} set")
    row = contract.row_for_bin[bin_arg]
    # 41c defines TINT as the union of the resolved block product.  Preserve a
    # distinct engine TINT interval as a declared structural refusal.
    if bin_arg == "tint":
        first = contract.row_for_bin[contract.bins[1]]
        last = contract.row_for_bin[contract.bins[-1]]
        if (abs(float(row["T_START"]) - float(first["T_START"])) > TIME_TOL
                or abs(float(row["T_STOP"]) - float(last["T_STOP"])) > TIME_TOL):
            return (
                "STRUCTURAL_INTERVAL_MISMATCH: canonical TINT differs from the "
                "resolved-block union used by current scripts/41c")
    return None


def _argv_option(argv: list[object], flag: str) -> str | None:
    positions = [index for index, value in enumerate(argv) if str(value) == flag]
    if len(positions) != 1 or positions[0] + 1 >= len(argv):
        return None
    return str(argv[positions[0] + 1])


def _candidate_sidecars(grid: Path, contract: Contract) -> dict[tuple[str, str], list[Path]]:
    out = {pair: [] for pair in contract.pairs}
    if not grid.is_dir():
        return out
    for path in sorted(grid.glob(f"{contract.trig}_SED_*.json")):
        pair = _sidecar_pair(path, contract.trig)
        if pair in out:
            out[pair].append(path)
    return out


def quarantine_invalid_panels(contract: Contract, grid: Path,
                              label: str) -> list[dict[str, object]]:
    """Move stale/partial 41c products aside so 41e cannot mistake them as live.

    This is recoverable rather than destructive.  41e discovers panels by PNG
    presence and does not itself validate sidecars, so leaving an old invalid
    PNG in the grid would silently defeat the no-model-dropped closure.
    """
    if not grid.is_dir():
        return []
    grouped: dict[Path, list[Path]] = {}
    for suffix in (".json", ".png", ".pdf"):
        for path in grid.glob(f"{contract.trig}_SED_*{suffix}"):
            pair = _pair_from_filename(path, contract.trig)
            if pair in contract.pairs:
                grouped.setdefault(path.with_suffix(""), []).append(path)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = grid / "quarantine" / f"{label}_{stamp}"
    moved: list[dict[str, object]] = []
    for stem, members in sorted(grouped.items(), key=lambda item: str(item[0])):
        pair = _pair_from_filename(stem, contract.trig)
        if pair is None:
            continue
        sidecar = stem.with_suffix(".json")
        result = (validate_sidecar(sidecar, contract, pair)
                  if sidecar in members
                  else Validation(False, "orphan panel without JSON sidecar"))
        if result.ok:
            continue
        destination.mkdir(parents=True, exist_ok=True)
        targets = []
        for source in members:
            target = destination / source.name
            if target.exists():
                raise RuntimeError(f"quarantine collision: {target}")
            source_hash = sha256(source)
            source.replace(target)
            targets.append({"path": str(target), "sha256": source_hash})
        moved.append({
            "bin": pair[0],
            "model": pair[1],
            "reason": result.reason,
            "files": targets,
        })

    if moved:
        manifest = grid / "logs" / "quarantine_manifest.jsonl"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "trigger": contract.trig,
            "label": label,
            "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "recoverable_destination": str(destination),
            "moved": moved,
        }
        with manifest.open("a") as stream:
            stream.write(json.dumps(record) + "\n")
    return moved


def validate_sidecar(path: Path, contract: Contract,
                     pair: tuple[str, str]) -> Validation:
    bin_arg, model = pair
    png = path.with_suffix(".png")
    pdf = path.with_suffix(".pdf")
    if not _png_ok(png):
        return Validation(False, f"missing or invalid PNG for {path.name}")
    if not _pdf_ok(pdf):
        return Validation(False, f"missing or invalid PDF for {path.name}")
    try:
        side = json.loads(path.read_text())
    except Exception as exc:
        return Validation(False, f"unreadable JSON {path.name}: {type(exc).__name__}")
    if not isinstance(side, dict):
        return Validation(False, f"sidecar is not a JSON object: {path.name}")

    try:
        side_pair = (normalize_bin(side["bin"]), canon(side["model"]))
    except Exception as exc:
        return Validation(False, f"invalid pair metadata in {path.name}: {exc}")
    file_pair = _pair_from_filename(path, contract.trig)
    if file_pair != pair:
        return Validation(False, f"filename pair {file_pair} != expected {pair}")
    if side_pair != pair:
        return Validation(False, f"sidecar pair {side_pair} != expected {pair}")
    if str(side.get("trig", "")).strip() != contract.trig:
        return Validation(False, f"sidecar trigger does not equal {contract.trig}")
    if side.get("script") != "41c_paper_sed.py":
        return Validation(False, "sidecar is not a scripts/41c product")
    if side.get("script_sha256") != CURRENT_41C_SHA256:
        return Validation(
            False,
            "sidecar scripts/41c hash is stale: "
            f"{side.get('script_sha256')!r} != {CURRENT_41C_SHA256}",
        )

    # The current producer records its full argv (NR-7).  Bind it
    # semantically to this exact canonical fit root and output grid rather
    # than accepting an AIC coincidence from another run.
    argv = side.get("argv")
    if not isinstance(argv, list):
        return Validation(False, "sidecar argv is missing or malformed")
    if _argv_option(argv, "--trig") != contract.trig:
        return Validation(False, "sidecar argv trigger mismatch")
    try:
        argv_bin = normalize_bin(_argv_option(argv, "--bin"))
    except Exception:
        argv_bin = None
    if argv_bin != bin_arg:
        return Validation(False, f"sidecar argv bin {argv_bin!r} != {bin_arg}")
    if canon(_argv_option(argv, "--model")) != model:
        return Validation(False, "sidecar argv model mismatch")
    argv_out = _argv_option(argv, "--out")
    if argv_out is None or _resolve_from_repo(argv_out) != path.parent.resolve():
        return Validation(False, "sidecar argv output grid mismatch")
    argv_fit_root = _argv_option(argv, "--fit-root")
    expected_fit_root = contract.fit_path.parent.parent.resolve()
    if argv_fit_root is None or _resolve_from_repo(argv_fit_root) != expected_fit_root:
        return Validation(False, "sidecar argv fit-root mismatch")
    if "--ul-arrows" in [str(value) for value in argv]:
        return Validation(False, "sidecar argv enabled non-contract upper-limit arrows")
    try:
        rebin = [float(value) for value in side.get("rebin", [])]
    except Exception:
        rebin = []
    if rebin != [5.0, 5.0] or side.get("ul_arrows") is not False:
        return Validation(False, "sidecar does not use strict XSPEC rebin 5 5")
    if side.get("rng_seed") != 20260814:
        return Validation(False, "sidecar RNG seed is not the frozen 20260814 seed")
    if side.get("ranges_convention") != contract.metadata.get("RANGES_CONVENTION"):
        return Validation(False, "sidecar energy-range convention mismatch")

    authority_mtime = max(contract.fit_path.stat().st_mtime_ns,
                          contract.metadata_path.stat().st_mtime_ns)
    artifact_mtime = min(path.stat().st_mtime_ns, png.stat().st_mtime_ns,
                         pdf.stat().st_mtime_ns)
    if artifact_mtime < authority_mtime:
        return Validation(
            False,
            "triplet predates the current canonical ECSV/JSON authority",
        )

    row = contract.row_for_bin[bin_arg]
    try:
        interval = [float(value) for value in side.get("interval_s", [])]
    except Exception:
        interval = []
    expected_interval = [float(row["T_START"]), float(row["T_STOP"])]
    if not _same_times(interval, expected_interval):
        return Validation(
            False,
            f"sidecar interval {interval} != canonical {expected_interval}",
        )
    expected_reference = str(contract.metadata["reference_det"])
    if str(side.get("reference", "")) != expected_reference:
        return Validation(False, "sidecar reference detector mismatch")
    side_dets = tuple(str(value) for value in side.get("detectors", []))
    expected_dets = contract.plugin_dets_for_bin[bin_arg]
    if side_dets != expected_dets:
        coverage = display_coverage_mismatch(contract, bin_arg)
        detail = coverage or "detector/plugin context mismatch"
        return Validation(
            False,
            f"{detail}; sidecar detectors={side_dets}, canonical={expected_dets}",
        )
    groups = side.get("groups")
    if not isinstance(groups, dict) or tuple(groups) != expected_dets:
        return Validation(False, "sidecar grouped-data detector context mismatch")

    column = f"{model}_AIC"
    current = row[column]
    stored = side.get("aic_stored")
    rendered = side.get("aic_live")
    status = str(row[f"{model}_STATUS"]).strip().upper()
    if status != "OK":
        return Validation(False, f"canonical {model}_STATUS={status}, not OK")
    if not finite(current):
        return Validation(False, f"canonical {column} is non-finite")
    if not finite(stored):
        return Validation(False, "sidecar aic_stored is non-finite")
    if not finite(rendered):
        return Validation(False, "sidecar aic_live is non-finite")
    current_f = float(current)
    stored_f = float(stored)
    rendered_f = float(rendered)
    if abs(stored_f - current_f) > AIC_TOL:
        return Validation(
            False,
            f"sidecar stored AIC {stored_f:.4f} != canonical {current_f:.4f}",
        )
    if abs(rendered_f - current_f) > AIC_TOL:
        return Validation(
            False,
            f"sidecar rendered AIC {rendered_f:.4f} != canonical {current_f:.4f}",
        )
    fit_mode = str(side.get("fit_mode", ""))
    if fit_mode not in {"live", "frozen_replay"}:
        return Validation(False, f"invalid/missing fit_mode {fit_mode!r}")
    if fit_mode == "frozen_replay" and side.get("band") == "drawn":
        return Validation(False, "frozen replay sidecar claims a drawn error band")
    if (not finite(side.get("pgstat")) or not finite(side.get("n2ll_live"))
            or abs(float(side["pgstat"]) - float(side["n2ll_live"])) > 1.0e-6):
        return Validation(False, "sidecar PGstat/n2ll provenance is inconsistent")
    try:
        nchan = int(side["n_active_channels"])
        dof = int(side["dof"])
    except Exception:
        return Validation(False, "sidecar active-channel/dof metadata is malformed")
    kfree = nchan - dof
    if kfree <= 0 or abs(rendered_f - (float(side["pgstat"]) + 2.0 * kfree)) > 1.0e-3:
        return Validation(False, "sidecar AIC is inconsistent with PGstat and k free")
    return Validation(True, "validated current-authority PNG/PDF/JSON triplet",
                      sidecar=path,
                      aic_current=current_f, aic_stored=stored_f,
                      aic_rendered=rendered_f, fit_mode=fit_mode,
                      png_sha256=sha256(png), pdf_sha256=sha256(pdf),
                      sidecar_sha256=sha256(path))


def _tail_reason(grid: Path, pair: tuple[str, str]) -> str | None:
    bin_arg, model = pair
    logs = grid / "logs"
    matches = sorted(logs.glob(f"{tag_for(bin_arg)}_{model}_attempt*.log"),
                     key=lambda p: (p.stat().st_mtime_ns, p.name))
    if not matches:
        return None
    path = matches[-1]
    try:
        with path.open("rb") as stream:
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(max(0, size - 65536), os.SEEK_SET)
            lines = stream.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None
    priorities = (
        "STRUCTURAL mismatch",
        "RuntimeError:",
        "ValueError:",
        "IndexError:",
        "KeyError:",
        "Traceback",
        "ENGINE_EXIT_CODE:",
    )
    for needle in priorities:
        for line in reversed(lines):
            if needle in line:
                return re.sub(r"\s+", " ", line.strip())[:500]
    nonempty = [re.sub(r"\s+", " ", line.strip()) for line in lines if line.strip()]
    return nonempty[-1][:500] if nonempty else None


def scan_grid(contract: Contract, grid: Path) -> dict[tuple[str, str], Validation]:
    candidates = _candidate_sidecars(grid, contract)
    return {pair: scan_pair(contract, grid, pair, candidates[pair])
            for pair in contract.pairs}


def scan_pair(contract: Contract, grid: Path, pair: tuple[str, str],
              candidates: list[Path] | None = None) -> Validation:
    if candidates is None:
        candidates = _candidate_sidecars(grid, contract)[pair]
    failures: list[str] = []
    for path in candidates:
        result = validate_sidecar(path, contract, pair)
        if result.ok:
            return result
        failures.append(result.reason)
    reason = failures[-1] if failures else "no PNG/PDF/JSON triplet"
    log_reason = _tail_reason(grid, pair)
    if log_reason:
        reason = f"{reason}; latest log: {log_reason}"
    return Validation(False, reason)


def failure_class(contract: Contract, pair: tuple[str, str],
                  result: Validation) -> str:
    bin_arg, model = pair
    status = str(contract.row_for_bin[bin_arg][f"{model}_STATUS"]).strip().upper()
    if status != "OK" or not finite(contract.row_for_bin[bin_arg][f"{model}_AIC"]):
        return "ENGINE_TABLE_FAILURE"
    if display_coverage_mismatch(contract, bin_arg):
        return "STRUCTURAL_DISPLAY_MISMATCH"
    if "STRUCTURAL mismatch" in result.reason or "STRUCTURAL_" in result.reason:
        return "STRUCTURAL_LIKELIHOOD_MISMATCH"
    if "hash is stale" in result.reason or "predates" in result.reason:
        return "STALE_ARTIFACT"
    return "PRODUCT_FAILURE"


def attempt_evidence(grid: Path, pair: tuple[str, str]) -> list[dict[str, object]]:
    bin_arg, model = pair
    tag = tag_for(bin_arg)
    records = []
    observed_attempts = set()
    for candidate in (grid / "logs").glob(f"{tag}_{model}_attempt*.log"):
        match = re.search(r"_attempt([0-9]+)\.log$", candidate.name)
        if match:
            observed_attempts.add(int(match.group(1)))
    for attempt in sorted(observed_attempts | {1, 2}):
        status_path = grid / "logs" / "status" / f"{tag}_{model}_attempt{attempt}.status"
        log_path = grid / "logs" / f"{tag}_{model}_attempt{attempt}.log"
        if not status_path.is_file() and not log_path.is_file():
            continue
        status_text = (status_path.read_text(errors="replace").strip()
                       if status_path.is_file() else None)
        records.append({
            "attempt": attempt,
            "status_path": str(status_path) if status_path.is_file() else None,
            "status_sha256": sha256(status_path) if status_path.is_file() else None,
            "status": status_text,
            "log_path": str(log_path) if log_path.is_file() else None,
            "log_sha256": sha256(log_path) if log_path.is_file() else None,
        })
    return records


def two_attempt_gaps(
        contract: Contract, grid: Path,
        results: dict[tuple[str, str], Validation]) -> list[dict[str, object]]:
    missing = []
    for pair, result in results.items():
        if result.ok:
            continue
        evidence = attempt_evidence(grid, pair)
        attempts = {int(item["attempt"]) for item in evidence
                    if item.get("status_path") and item.get("log_path")}
        if attempts != {1, 2}:
            missing.append({"bin": pair[0], "model": pair[1],
                            "attempts_with_status_and_log": sorted(attempts)})
    return missing


def write_worklist(path: Path, pairs: Iterable[tuple[str, str]]) -> int:
    materialized = list(pairs)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(f"{bin_arg}\t{model}\n" for bin_arg, model in materialized)
    path.write_text(text)
    return len(materialized)


def _clean_reason(reason: str) -> str:
    return re.sub(r"\s+", " ", reason).strip()[:700]


def write_status(path: Path, contract: Contract,
                 results: dict[tuple[str, str], Validation]) -> None:
    """Write the token order actually consumed by scripts/41e_sed_montage.py."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for bin_arg, model in contract.pairs:
        result = results[(bin_arg, model)]
        if result.ok:
            lines.append(f"OK {model} {bin_arg}")
        else:
            lines.append(f"FAIL {model} {bin_arg} {_clean_reason(result.reason)}")
    path.write_text("\n".join(lines) + "\n")


def write_summary(path: Path, contract: Contract, grid: Path,
                  results: dict[tuple[str, str], Validation], attempt: int | None,
                  final_quarantined: list[dict[str, object]] | None = None) -> dict:
    valid = []
    failed = []
    for bin_arg, model in contract.pairs:
        result = results[(bin_arg, model)]
        if result.ok:
            valid.append({
                "bin": bin_arg,
                "model": model,
                "sidecar": str(result.sidecar),
                "aic_current": result.aic_current,
                "aic_stored": result.aic_stored,
                "aic_rendered": result.aic_rendered,
                "fit_mode": result.fit_mode,
                "png_sha256": result.png_sha256,
                "pdf_sha256": result.pdf_sha256,
                "sidecar_sha256": result.sidecar_sha256,
            })
        else:
            failed.append({
                "bin": bin_arg,
                "model": model,
                "failure_class": failure_class(contract, (bin_arg, model), result),
                "reason": result.reason,
                "attempt_evidence": attempt_evidence(grid, (bin_arg, model)),
            })
    structural_context = {
        bin_arg: reason for bin_arg in contract.bins
        if (reason := display_coverage_mismatch(contract, bin_arg)) is not None
    }
    evidence_gaps = (two_attempt_gaps(contract, grid, results)
                     if attempt is None else [])
    payload = {
        "trigger": contract.trig,
        "canonical_fit_table": str(contract.fit_path),
        "canonical_fit_sha256": contract.fit_sha256,
        "canonical_fit_metadata": str(contract.metadata_path),
        "canonical_fit_metadata_sha256": contract.metadata_sha256,
        "adopted_blocks": str(contract.blocks_path),
        "adopted_blocks_sha256": contract.blocks_sha256,
        "sed_engine": str(SED_ENGINE),
        "sed_engine_sha256": CURRENT_41C_SHA256,
        "grid": str(grid),
        "models": list(contract.models),
        "bins": list(contract.bins),
        "plugin_dets_by_bin": {
            bin_arg: list(contract.plugin_dets_for_bin[bin_arg])
            for bin_arg in contract.bins
        },
        "known_structural_display_mismatches": structural_context,
        "bands_are_never_silently_dropped": True,
        "pairs": len(contract.pairs),
        "ok": len(valid),
        "fail": len(failed),
        "valid_triplets": valid,
        "failed_pairs": failed,
        "pool_size": POOL_SIZE,
        "retry_limit": 1,
        "attempt_snapshot": attempt,
        "persistent_failure_attempt_evidence_complete": not evidence_gaps,
        "persistent_failure_attempt_evidence_gaps": evidence_gaps,
        "final_quarantined_invalid_stems": len(final_quarantined or []),
        "final_quarantine_records": final_quarantined or [],
        "aic_tolerance": AIC_TOL,
        "triplet_contract": (
            "current 41c hash + argv + canonical interval/plugin context + "
            "strict rebin + seed + current AIC + PGstat/k consistency + freshness"),
        "visual_verdict": "UNGATED — independent Claude figure verification pending",
        "provisional": True,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def _closure_paths(grid: Path, attempt: int | None) -> tuple[Path, Path]:
    suffix = f"_attempt{attempt}" if attempt is not None else ""
    return (grid / f"sweep_status{suffix}.txt",
            grid / f"sweep_summary{suffix}.json")


def write_blocked_closure(trig: str, grid: Path, attempt: int | None) -> dict:
    """Materialize an explicit closure for a known response-blocked trigger."""
    reason = RESPONSE_BLOCKED[trig]
    status, summary = _closure_paths(grid, attempt)
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(f"BLOCKED RESPONSE_UNCOVERED {reason}\n")
    payload = {
        "trigger": trig,
        "grid": str(grid),
        "status": "RESPONSE_BLOCKED",
        "reason": reason,
        "models": [],
        "bins": [],
        "pairs": 0,
        "ok": 0,
        "fail": 0,
        "blocked": 1,
        "pool_size": POOL_SIZE,
        "retry_limit": 1,
        "attempt_snapshot": attempt,
        "visual_verdict": "NO SED PRODUCTS — response blocked before P1",
        "provisional": True,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    summary.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def _campaign_contracts(triggers: list[str]) -> tuple[list[Contract], list[str]]:
    if not triggers:
        raise RuntimeError("campaign trigger list is empty")
    if len(triggers) != len(set(triggers)):
        raise RuntimeError(f"duplicate campaign triggers: {triggers}")
    blocked = [trig for trig in triggers if trig in RESPONSE_BLOCKED]
    # Load every non-blocked authority before planning or quarantining anything.
    # One incomplete P1 trigger therefore aborts the entire launch preflight.
    contracts = [load_contract(trig) for trig in triggers if trig not in RESPONSE_BLOCKED]
    return contracts, blocked


def do_campaign_plan(args: argparse.Namespace) -> int:
    contracts, blocked = _campaign_contracts(args.triggers)
    pending: list[tuple[str, str, str]] = []
    per_trigger = []
    for contract in contracts:
        grid = default_grid(contract.trig)
        quarantined = []
        if args.quarantine_invalid:
            label = (f"pre_attempt{args.attempt}" if args.attempt is not None
                     else "pre_campaign_plan")
            quarantined = quarantine_invalid_panels(contract, grid, label)
        results = scan_grid(contract, grid)
        missing = [pair for pair in contract.pairs if not results[pair].ok]
        pending.extend((contract.trig, bin_arg, model)
                       for bin_arg, model in missing)
        structural_context = {
            bin_arg: reason for bin_arg in contract.bins
            if (reason := display_coverage_mismatch(contract, bin_arg)) is not None
        }
        per_trigger.append({
            "trigger": contract.trig,
            "pairs": len(contract.pairs),
            "reused_valid_triplets": len(contract.pairs) - len(missing),
            "pending": len(missing),
            "quarantined_invalid_stems": len(quarantined),
            "canonical_fit_sha256": contract.fit_sha256,
            "canonical_fit_metadata_sha256": contract.metadata_sha256,
            "adopted_blocks_sha256": contract.blocks_sha256,
            "known_structural_display_mismatches": structural_context,
            "bands_are_never_silently_dropped": True,
        })
    for trig in blocked:
        payload = write_blocked_closure(trig, default_grid(trig), args.attempt)
        per_trigger.append({"trigger": trig, "status": payload["status"],
                            "reason": payload["reason"], "pairs": 0,
                            "pending": 0})

    args.worklist.parent.mkdir(parents=True, exist_ok=True)
    args.worklist.write_text("".join(
        f"{trig}\t{bin_arg}\t{model}\n"
        for trig, bin_arg, model in pending
    ))
    payload = {
        "triggers_requested": args.triggers,
        "ready_triggers": [contract.trig for contract in contracts],
        "response_blocked": blocked,
        "attempt": args.attempt,
        "pairs": sum(item["pairs"] for item in per_trigger),
        "pending": len(pending),
        "pool_size": POOL_SIZE,
        "worklist": str(args.worklist),
        "per_trigger": per_trigger,
        "provisional": True,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if args.campaign_summary_out:
        args.campaign_summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.campaign_summary_out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0


def do_campaign_finalize(args: argparse.Namespace) -> int:
    contracts, blocked = _campaign_contracts(args.triggers)
    per_trigger = []
    for contract in contracts:
        grid = default_grid(contract.trig)
        final_quarantined = []
        if args.attempt is None:
            # Attempt 2 can leave a well-formed but scientifically invalid
            # GBM-only or stale panel behind.  Move every such stem out of the
            # primary grid before the delivery closure so 41e/report tooling
            # cannot discover it by filename alone.
            final_quarantined = quarantine_invalid_panels(
                contract, grid, "post_attempt2_final")
        results = scan_grid(contract, grid)
        status, summary = _closure_paths(grid, args.attempt)
        write_status(status, contract, results)
        per_trigger.append(write_summary(
            summary, contract, grid, results, args.attempt,
            final_quarantined=final_quarantined))
    for trig in blocked:
        per_trigger.append(write_blocked_closure(
            trig, default_grid(trig), args.attempt))

    payload = {
        "triggers_requested": args.triggers,
        "ready_triggers": [contract.trig for contract in contracts],
        "response_blocked": blocked,
        "pairs": sum(item["pairs"] for item in per_trigger),
        "ok": sum(item["ok"] for item in per_trigger),
        "fail": sum(item["fail"] for item in per_trigger),
        "blocked": sum(int(item.get("blocked", 0)) for item in per_trigger),
        "persistent_failure_attempt_evidence_gaps": sum(
            len(item.get("persistent_failure_attempt_evidence_gaps", []))
            for item in per_trigger),
        "pool_size": POOL_SIZE,
        "retry_limit": 1,
        "attempt_snapshot": args.attempt,
        "per_trigger": [{
            "trigger": item["trigger"],
            "status": item.get("status", "GRID_CLOSED"),
            "pairs": item["pairs"],
            "ok": item["ok"],
            "fail": item["fail"],
            "blocked": item.get("blocked", 0),
            "persistent_failure_attempt_evidence_complete": item.get(
                "persistent_failure_attempt_evidence_complete", True),
            "reason": item.get("reason"),
        } for item in per_trigger],
        "provisional": True,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if args.campaign_summary_out:
        args.campaign_summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.campaign_summary_out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({k: payload[k] for k in (
        "pairs", "ok", "fail", "blocked",
        "persistent_failure_attempt_evidence_gaps",
        "pool_size", "provisional")},
        indent=2))
    return 0 if (payload["fail"] == 0 and payload["blocked"] == 0
                 and payload["persistent_failure_attempt_evidence_gaps"] == 0) else 2


def do_plan(args: argparse.Namespace) -> int:
    contract = load_contract(args.trig)
    grid = args.grid or default_grid(args.trig)
    quarantined = []
    if args.quarantine_invalid:
        label = f"pre_attempt{args.attempt}" if args.attempt is not None else "pre_plan"
        quarantined = quarantine_invalid_panels(contract, grid, label)
    results = scan_grid(contract, grid)
    pending = [pair for pair in contract.pairs if not results[pair].ok]
    count = write_worklist(args.worklist, pending)
    print(json.dumps({
        "trigger": args.trig,
        "models": len(contract.models),
        "bins": len(contract.bins),
        "pairs": len(contract.pairs),
        "reused_valid_triplets": len(contract.pairs) - count,
        "pending": count,
        "quarantined_invalid_stems": len(quarantined),
        "worklist": str(args.worklist),
    }, indent=2))
    return 0


def do_check(args: argparse.Namespace) -> int:
    contract = load_contract(args.trig)
    grid = args.grid or default_grid(args.trig)
    pair = (normalize_bin(args.bin_arg), canon(args.model))
    if pair not in contract.pairs:
        print(f"FAIL {pair[1]} {pair[0]} pair is outside canonical grid")
        return 2
    result = scan_pair(contract, grid, pair)
    if result.ok:
        print(f"OK {pair[1]} {pair[0]} {result.sidecar}")
        return 0
    print(f"FAIL {pair[1]} {pair[0]} {_clean_reason(result.reason)}")
    return 1


def do_finalize(args: argparse.Namespace) -> int:
    contract = load_contract(args.trig)
    grid = args.grid or default_grid(args.trig)
    results = scan_grid(contract, grid)
    status = args.status_out or (grid / "sweep_status.txt")
    summary = args.summary_out or (grid / "sweep_summary.json")
    write_status(status, contract, results)
    payload = write_summary(summary, contract, grid, results, args.attempt)
    print(json.dumps({k: payload[k] for k in ("trigger", "pairs", "ok", "fail",
                                               "pool_size", "provisional")}, indent=2))
    return 0 if payload["fail"] == 0 else 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trig")
    parser.add_argument("--workers", type=int, default=POOL_SIZE)
    parser.add_argument("--mode", choices=("run", "plan", "check", "finalize",
                                            "campaign-plan", "campaign-finalize"),
                        default="run")
    parser.add_argument("--attempt", type=int, default=None)
    parser.add_argument("--worklist", type=Path)
    parser.add_argument("--status-out", type=Path)
    parser.add_argument("--summary-out", type=Path)
    parser.add_argument("--grid", type=Path)
    parser.add_argument("--quarantine-invalid", action="store_true")
    parser.add_argument("--bin", dest="bin_arg")
    parser.add_argument("--model")
    parser.add_argument("--triggers", nargs="+")
    parser.add_argument("--campaign-summary-out", type=Path)
    args = parser.parse_args()
    if args.workers != POOL_SIZE:
        parser.error(f"campaign contract requires exactly {POOL_SIZE} shell slots")

    if args.mode == "run":
        if args.trig is None:
            parser.error("--mode run requires --trig (use the zsh --campaign path for campaign execution)")
        proc = subprocess.run(["zsh", str(WRAPPER), args.trig], cwd=REPO,
                              env=os.environ.copy())
        raise SystemExit(proc.returncode)
    if args.mode == "plan":
        if args.trig is None:
            parser.error("--mode plan requires --trig")
        if args.worklist is None:
            parser.error("--mode plan requires --worklist")
        raise SystemExit(do_plan(args))
    if args.mode in {"campaign-plan", "campaign-finalize"}:
        if not args.triggers:
            parser.error(f"--mode {args.mode} requires --triggers")
        if args.mode == "campaign-plan":
            if args.worklist is None:
                parser.error("--mode campaign-plan requires --worklist")
            raise SystemExit(do_campaign_plan(args))
        raise SystemExit(do_campaign_finalize(args))
    if args.mode == "check":
        if args.trig is None:
            parser.error("--mode check requires --trig")
        if args.bin_arg is None or args.model is None:
            parser.error("--mode check requires --bin and --model")
        raise SystemExit(do_check(args))
    if args.trig is None:
        parser.error("--mode finalize requires --trig")
    raise SystemExit(do_finalize(args))


if __name__ == "__main__":
    main()
