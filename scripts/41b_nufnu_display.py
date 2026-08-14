#!/usr/bin/env python
"""Faithful, table-driven :math:`\nu F_\nu` displays for one GRB.

This is the non-refitting replacement for ``scripts/41_nuFnu_panels.py``.  Its
central invariant is deliberately narrow and testable: a displayed source-model
curve is the engine component evaluated at *every* source parameter serialized in
``spectral_fits.ecsv``.  There is no optimizer and no fallback fit in this module.

The current engine product does not serialize fitted effective-area-correction
(EAC) nuisance constants, the joint covariance, or hashes of the background/TTE/
response inputs.  Consequently, the free source parameters can be restored exactly,
but non-reference-detector folded diagnostics and covariance bands cannot.  Those
elements are omitted.  Reference-detector points/residuals are explicitly labelled
as a reconstruction from the current, unbound inputs rather than an archival replay.

Modes and CLI are compatible with ``scripts/41_nuFnu_panels.py``::

  --mode bin   --bin N|tint     one bin, every registered model
  --mode model --model NAME     one model over all ordinary bins
  --mode best                   engine winner over all ordinary bins
  --mode binall --bin N|tint    one bin, top eight VALID models overlaid

Grids are paginated at four SED/residual pairs per PDF page.  PNG page previews and
a vertically assembled legacy-name PNG are also written.  This keeps the diagnostic
atlas readable when printed while preserving the old output stem for consumers.

Heavy environment: threeML + astromodels + CALDB, exactly as for the live script.
The display rebuilds plugins and evaluates stored models; it never runs the fit
engine.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.table import Row, Table
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from threeML import Model, PointSource


ROOT = Path(__file__).resolve().parents[1]

# Inventory found scripts/41 as the closest existing implementation.  Import only
# its already-verified XSPEC grouping/unfolding primitives; none of its fitting or
# covariance-refit helpers are used here.
_legacy_spec = importlib.util.spec_from_file_location(
    "nufnu41_primitives", ROOT / "scripts" / "41_nuFnu_panels.py"
)
if _legacy_spec is None or _legacy_spec.loader is None:
    raise RuntimeError("cannot load scripts/41_nuFnu_panels.py primitives")
_legacy = importlib.util.module_from_spec(_legacy_spec)
sys.modules.setdefault("nufnu41_primitives", _legacy)
_legacy_spec.loader.exec_module(_legacy)

eng = _legacy.eng
_rebin_for_plot = _legacy._rebin_for_plot
_ev = _legacy._ev
unfold_detector = _legacy.unfold_detector

sys.path.insert(0, str(ROOT / "scripts"))
from plot_style import PUB, apply_pub_style, det_color  # noqa: E402

apply_pub_style()


ALL_SPECS = (
    list(eng.MODEL_SPECS)
    + list(eng.SHAPE_MODEL_SPECS)
    + list(eng.HIGHE_MODEL_SPECS)
)
SPEC_BY_NAME = {spec["name"]: spec for spec in ALL_SPECS}
SPEC_BY_PREFIX = {spec["prefix"]: spec for spec in ALL_SPECS}
SPEC_INDEX = {spec["prefix"]: index for index, spec in enumerate(ALL_SPECS)}
_NAI_ID_INDEX = {
    detector: index
    for index, detector in enumerate(
        [*(f"n{number}" for number in range(10)), "na", "nb"]
    )
}


def _specs_for_columns(columns: Sequence[str]) -> Tuple[Mapping[str, object], ...]:
    """Return the engine model suite actually serialized in a table schema."""
    names = set(str(column) for column in columns)
    present = []
    for spec in ALL_SPECS:
        prefix = str(spec["prefix"])
        sentinels = {
            f"{prefix}_STATUS",
            f"{prefix}_VALID",
            f"{prefix}_AIC",
        }
        overlap = sentinels & names
        if overlap and overlap != sentinels:
            raise DisplayInvariantError(
                f"partial engine result schema for {spec['name']}: "
                f"present={sorted(overlap)}, required={sorted(sentinels)}"
            )
        if overlap:
            present.append(spec)
    return tuple(present)


def _specs_for_row(row: Row) -> Tuple[Mapping[str, object], ...]:
    specs = _specs_for_columns(row.colnames)
    if not specs:
        raise DisplayInvariantError("fit row contains no registered engine model results")
    return specs

REBIN_SIG = 5.0
REBIN_MAX = 5
PANELS_PER_PAGE = 4
GRID_COLUMNS = 2
OVERLAY_MAX_MODELS = 8
DETECTED_PAD_DEX = 0.08
Y_PAD_DEX = 0.25
AIC_INVARIANT_ATOL = 1.0e-6
INTERVAL_ATOL = 5.0e-7
ENERGY_CONTIGUITY_RTOL = 1.0e-6

FOLDED_PROVENANCE_WARNING = (
    "Folded diagnostics use current, unbound background/TTE/RSP inputs "
    "(fit-sidecar omission)."
)

NUFNU_LABEL = (
    r"$\nu F_\nu$" + "\n" + r"(keV$^2$ s$^{-1}$ cm$^{-2}$ keV$^{-1}$)"
)
ENERGY_LABEL = "Energy (keV)"
RESID_LABEL = r"resid ($\sigma$)"


class DisplayInvariantError(RuntimeError):
    """An engine reference needed for an honest display was absent or inconsistent."""


_MODEL_FROM_ROW_ERRORS: Dict[str, str] = {}


@dataclass
class FitProduct:
    table_path: Path
    table: Table
    metadata_path: Path
    metadata: Mapping[str, object]
    blocks_path: Path
    block_significance: Mapping[int, float]
    background_path: Path
    reference_det: str
    fit_dets: Tuple[str, ...]
    rows_by_block: Mapping[int, Row]

    @property
    def ordinary_rows(self) -> List[Row]:
        return [self.rows_by_block[index] for index in sorted(self.rows_by_block) if index >= 0]


@dataclass
class BlockDisplay:
    row: Row
    block_index: int
    significance: Optional[float]
    plugins: List[object]
    detector_names: List[str]
    rebin: Tuple[float, int]
    detected_domains: Tuple[Tuple[float, float], ...]
    detected_span: Optional[Tuple[float, float]]
    axis_span: Optional[Tuple[float, float]]
    winner_spec: Optional[Mapping[str, object]]
    winner_component: Optional[object]
    unfolded_under_winner: Dict[str, Mapping[str, np.ndarray]] = field(default_factory=dict)
    omitted_eac: Tuple[str, ...] = ()
    missing_detectors: Tuple[str, ...] = ()
    error: Optional[str] = None


@dataclass
class PanelDisplay:
    block: BlockDisplay
    spec: Optional[Mapping[str, object]]
    component: Optional[object]
    residuals: Dict[str, Mapping[str, np.ndarray]]
    title: str
    is_best: bool
    error: Optional[str] = None


def _split_csv(value: object) -> Tuple[str, ...]:
    if value is None or np.ma.is_masked(value):
        return ()
    return tuple(x.strip() for x in str(value).split(",") if x.strip())


def _finite_float(value: object, label: str) -> float:
    if value is None or np.ma.is_masked(value):
        raise ValueError(f"{label} is missing")
    try:
        number = float(value)
    except Exception as exc:
        raise ValueError(f"{label} is not numeric") from exc
    if not np.isfinite(number):
        raise ValueError(f"{label} is non-finite")
    return number


def _status(row: Row, spec: Mapping[str, object]) -> str:
    column = f"{spec['prefix']}_STATUS"
    if column not in row.colnames or np.ma.is_masked(row[column]):
        return "MISSING"
    return str(row[column]).strip()


def _valid(row: Row, spec: Mapping[str, object]) -> bool:
    column = f"{spec['prefix']}_VALID"
    if column not in row.colnames or np.ma.is_masked(row[column]):
        return False
    return bool(row[column])


def engine_aic(row: Row, spec: Mapping[str, object]) -> Optional[float]:
    column = f"{spec['prefix']}_AIC"
    if column not in row.colnames:
        return None
    try:
        return _finite_float(row[column], column)
    except ValueError:
        return None


def required_model_columns(spec: Mapping[str, object]) -> Tuple[str, ...]:
    """Columns that define the complete free source component for ``spec``."""
    prefix = str(spec["prefix"])
    return tuple(f"{prefix}_{suffix}" for suffix in spec["pmap"])


def model_from_row(spec: Mapping[str, object], row: Row):
    """Build ``spec`` and set every free source parameter from the engine row.

    ``spec['pmap']`` is the engine's serialization authority.  No boundary clamp,
    seed transformation, default substitution, or optimization is permitted here.
    The function returns ``None`` on any incomplete/non-finite/ambiguous mapping;
    callers obtain the human-readable reason through :func:`model_from_row_error`
    and put it on the panel.
    """
    prefix = str(spec["prefix"])
    _MODEL_FROM_ROW_ERRORS.pop(prefix, None)
    try:
        component = spec["build"]({})
    except Exception as exc:
        _MODEL_FROM_ROW_ERRORS[prefix] = f"engine builder failed: {exc}"
        return None

    parameters = getattr(component, "parameters", {})
    leaf_map: Dict[str, List[object]] = {}
    free_leaves = set()
    for path, parameter in parameters.items():
        leaf = str(path).split(".")[-1]
        leaf_map.setdefault(leaf, []).append(parameter)
        if bool(getattr(parameter, "free", False)):
            free_leaves.add(leaf)

    targets = set(str(short) for short in spec["pmap"].values())
    if free_leaves != targets:
        missing = sorted(targets - free_leaves)
        extra = sorted(free_leaves - targets)
        _MODEL_FROM_ROW_ERRORS[prefix] = (
            f"engine schema drift: missing free targets={missing}; extra free params={extra}"
        )
        return None

    assignments: List[Tuple[object, float, str]] = []
    for suffix, short_name in spec["pmap"].items():
        column = f"{prefix}_{suffix}"
        if column not in row.colnames:
            _MODEL_FROM_ROW_ERRORS[prefix] = f"required engine column {column} is absent"
            return None
        try:
            value = _finite_float(row[column], column)
        except ValueError as exc:
            _MODEL_FROM_ROW_ERRORS[prefix] = str(exc)
            return None
        matches = leaf_map.get(str(short_name), [])
        if len(matches) != 1:
            _MODEL_FROM_ROW_ERRORS[prefix] = (
                f"parameter target {short_name!r} matched {len(matches)} component leaves"
            )
            return None
        assignments.append((matches[0], value, column))

    for parameter, value, column in assignments:
        try:
            parameter.value = value
        except Exception as exc:
            _MODEL_FROM_ROW_ERRORS[prefix] = f"{column}={value!r} rejected by engine model: {exc}"
            return None
        restored = float(parameter.value)
        if restored != value:
            _MODEL_FROM_ROW_ERRORS[prefix] = (
                f"{column} changed during assignment ({value!r} -> {restored!r})"
            )
            return None

    return component


def model_from_row_error(spec: Mapping[str, object]) -> str:
    return _MODEL_FROM_ROW_ERRORS.get(str(spec["prefix"]), "unknown row-to-model failure")


def _resolve_fit_table(trig: str, out_dir: Path) -> Path:
    candidates = []
    override = os.environ.get("FITS_TABLE")
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend(
        [
            out_dir / trig / "spectral_fits.ecsv",
            ROOT / "results" / "clean_per_burst_human_final" / trig / "spectral_fits.ecsv",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    rendered = "\n  ".join(str(path) for path in candidates)
    raise DisplayInvariantError(
        "no engine fit table found; refusing an unverified display. Checked:\n  " + rendered
    )


def _resolve_blocks_path(trig: str, metadata: Mapping[str, object]) -> Path:
    recorded = metadata.get("blocks_file")
    if not recorded:
        raise DisplayInvariantError("spectral_fits.json has no blocks_file provenance")
    recorded_path = Path(str(recorded)).expanduser()
    override = os.environ.get("BLOCKS_ROOT")
    if override:
        override_path = Path(override).expanduser()
        if override_path.is_dir():
            override_path = override_path / f"bb_blocks_spectral_{trig}.ecsv"
        if not override_path.is_file():
            raise DisplayInvariantError(f"BLOCKS_ROOT resolves to missing file: {override_path}")
        if recorded_path.exists() and override_path.resolve() != recorded_path.resolve():
            raise DisplayInvariantError(
                "BLOCKS_ROOT disagrees with spectral_fits.json; refusing to mix runs: "
                f"{override_path.resolve()} != {recorded_path.resolve()}"
            )
        return override_path.resolve()
    if not recorded_path.is_file():
        raise DisplayInvariantError(f"recorded blocks_file does not exist: {recorded_path}")
    return recorded_path.resolve()


def _load_block_significance(
    trig: str,
    blocks_path: Path,
    canonical_det: str,
    rows_by_block: Mapping[int, Row],
) -> Mapping[int, float]:
    blocks = Table.read(blocks_path, format="ascii.ecsv")
    if "TRIGGER_NAME" in blocks.colnames:
        blocks = blocks[np.asarray(blocks["TRIGGER_NAME"]).astype(str) == trig]
    if "DETECTOR" in blocks.colnames:
        chosen = blocks[np.asarray(blocks["DETECTOR"]).astype(str) == canonical_det]
        if not len(chosen):
            raise DisplayInvariantError(
                f"block product has DETECTOR rows but none for canonical detector "
                f"{canonical_det!r}"
            )
        blocks = chosen

    significance: Dict[int, float] = {}
    for block_row in blocks:
        index = int(block_row["BLOCK_INDEX"])
        if index not in rows_by_block:
            continue
        if index in significance:
            raise DisplayInvariantError(
                f"duplicate canonical significance rows for BLOCK_INDEX={index}"
            )
        fit_row = rows_by_block[index]
        fit_start = _finite_float(fit_row["T_START"], "T_START")
        fit_stop = _finite_float(fit_row["T_STOP"], "T_STOP")
        block_start = _finite_float(block_row["T_START"], "block T_START")
        block_stop = _finite_float(block_row["T_STOP"], "block T_STOP")
        if not (
            abs(fit_start - block_start) <= INTERVAL_ATOL
            and abs(fit_stop - block_stop) <= INTERVAL_ATOL
        ):
            raise DisplayInvariantError(
                f"block {index} interval differs between fit and block products"
            )
        significance[index] = _finite_float(block_row["SIGNIFICANCE"], "SIGNIFICANCE")

    missing = sorted(index for index in rows_by_block if index >= 0 and index not in significance)
    if missing:
        raise DisplayInvariantError(f"no block significance found for ordinary bins {missing}")
    return significance


def load_fit_product(trig: str, out_dir: Path) -> FitProduct:
    table_path = _resolve_fit_table(trig, out_dir)
    table = Table.read(table_path, format="ascii.ecsv")
    if "BLOCK" not in table.colnames:
        raise DisplayInvariantError(f"{table_path} has no BLOCK column")

    metadata_path = table_path.with_suffix(".json")
    if not metadata_path.is_file():
        raise DisplayInvariantError(
            f"missing fit sidecar {metadata_path}; reference detector/run provenance unavailable"
        )
    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    if str(metadata.get("trigger", "")).strip() != trig:
        raise DisplayInvariantError(
            f"fit sidecar trigger {metadata.get('trigger')!r} does not match {trig!r}"
        )

    reference_det = str(metadata.get("reference_det", "")).strip()
    sidecar_fit_dets = tuple(
        str(det).strip() for det in metadata.get("fit_dets", []) if str(det).strip()
    )
    if not reference_det or not sidecar_fit_dets:
        raise DisplayInvariantError("fit sidecar lacks reference_det or fit_dets")
    if reference_det not in sidecar_fit_dets:
        raise DisplayInvariantError("fit sidecar reference_det is not in fit_dets")

    recorded_models = tuple(str(name) for name in metadata.get("models", []))
    if not recorded_models or len(set(recorded_models)) != len(recorded_models):
        raise DisplayInvariantError("fit sidecar has an empty or duplicate model registry")
    unknown_models = [name for name in recorded_models if name not in SPEC_BY_NAME]
    if unknown_models:
        raise DisplayInvariantError(
            f"fit sidecar contains models absent from the current engine: {unknown_models}"
        )
    table_specs = _specs_for_columns(table.colnames)
    table_models = tuple(str(spec["name"]) for spec in table_specs)
    if recorded_models != table_models:
        raise DisplayInvariantError(
            "fit sidecar model registry differs from the table/current engine; "
            f"sidecar={recorded_models!r}, table={table_models!r}"
        )
    for key, current in (("NAI_RANGES", eng.NAI_RANGES), ("BGO_RANGES", eng.BGO_RANGES)):
        recorded = tuple(str(value) for value in metadata.get(key, []))
        expected = tuple(str(value) for value in current)
        if recorded != expected:
            raise DisplayInvariantError(
                f"fit sidecar {key}={recorded!r} differs from current engine {expected!r}"
            )

    rows_by_block: Dict[int, Row] = {}
    row_detector_order: List[str] = list(sidecar_fit_dets)
    for row in table:
        index = int(row["BLOCK"])
        if index in rows_by_block:
            raise DisplayInvariantError(f"duplicate fit row for BLOCK={index}")
        if "PLUGIN_DETS" not in row.colnames:
            raise DisplayInvariantError("fit row has no PLUGIN_DETS provenance")
        for detector in _split_csv(row["PLUGIN_DETS"]):
            if detector not in row_detector_order:
                row_detector_order.append(detector)
        rows_by_block[index] = row
    expected_blocks = int(metadata.get("n_blocks", len([x for x in rows_by_block if x >= 0])))
    ordinary = sorted(index for index in rows_by_block if index >= 0)
    if any(index >= expected_blocks for index in ordinary):
        raise DisplayInvariantError(
            f"ordinary fit rows {ordinary} exceed sidecar n_blocks={expected_blocks}"
        )

    starts = list(metadata.get("bin_starts", []))
    stops = list(metadata.get("bin_stops", []))
    if len(starts) != expected_blocks or len(stops) != expected_blocks:
        raise DisplayInvariantError("fit sidecar bin edge arrays do not match n_blocks")
    for index in ordinary:
        row = rows_by_block[index]
        if not (
            abs(_finite_float(row["T_START"], "T_START") - float(starts[index]))
            <= INTERVAL_ATOL
            and abs(_finite_float(row["T_STOP"], "T_STOP") - float(stops[index]))
            <= INTERVAL_ATOL
        ):
            raise DisplayInvariantError(f"fit row {index} disagrees with sidecar bin edges")

    blocks_path = _resolve_blocks_path(trig, metadata)
    canonical_det = str(metadata.get("canonical_det") or reference_det).strip()
    block_significance = _load_block_significance(
        trig, blocks_path, canonical_det, rows_by_block
    )

    background_path = Path(
        os.environ.get("BKG_FILE", ROOT / "results" / "background_intervals.ecsv")
    ).expanduser()
    if not background_path.is_file():
        raise DisplayInvariantError(f"background catalog does not exist: {background_path}")

    return FitProduct(
        table_path=table_path,
        table=table,
        metadata_path=metadata_path.resolve(),
        metadata=metadata,
        blocks_path=blocks_path,
        block_significance=block_significance,
        background_path=background_path.resolve(),
        reference_det=reference_det,
        fit_dets=tuple(row_detector_order),
        rows_by_block=rows_by_block,
    )


def _load_backgrounds(product: FitProduct, trig: str) -> Mapping[str, Tuple[Tuple[float, float], Tuple[float, float]]]:
    table = Table.read(product.background_path, format="ascii.ecsv")
    subset = table[np.asarray(table["TRIGGER_NAME"]).astype(str) == trig]
    return {
        str(row["DETECTOR"]).strip(): (
            (
                _finite_float(row["BKG_NEG_START"], "BKG_NEG_START"),
                _finite_float(row["BKG_NEG_STOP"], "BKG_NEG_STOP"),
            ),
            (
                _finite_float(row["BKG_POS_START"], "BKG_POS_START"),
                _finite_float(row["BKG_POS_STOP"], "BKG_POS_STOP"),
            ),
        )
        for row in subset
    }


def _set_source_position(trig: str) -> None:
    sample = Table.read(ROOT / "results" / "grb_sample.ecsv", format="ascii.ecsv")
    mask = np.asarray(sample["TRIGGER_NAME"]).astype(str) == trig
    if np.count_nonzero(mask) != 1:
        raise DisplayInvariantError(f"expected one grb_sample row for {trig}")
    row = sample[mask][0]
    eng.SRC_RA = _finite_float(row["RA"], "RA")
    eng.SRC_DEC = _finite_float(row["DEC"], "DEC")


def _row_eac_dets(row: Row) -> Tuple[str, ...]:
    if "EAC_DETS" not in row.colnames:
        raise DisplayInvariantError(
            "fit row has no EAC_DETS provenance; refusing unit-normalization fallback"
        )
    return _split_csv(row["EAC_DETS"])


def _stored_eac(row: Row, prefix: str, detector: str):
    """The FITTED effective-area constant for this model and detector, or None.

    2026-08-13: scripts/10 now writes <PREFIX>_EAC_<DET>, and
    scripts/49_recover_eac.py backfills the existing catalog by profiling only
    those constants with every source parameter frozen (each recovered value is
    accepted only if it reproduces the stored AIC). Before that the values were
    fitted and discarded, which is why this renderer originally had to drop every
    non-reference detector — surrendering the whole high-energy constraint rather
    than draw a folded model it could not reproduce.

    Returns None when the column is absent or non-finite; the caller must then
    omit the detector exactly as before. We never substitute unity.
    """
    if not prefix:
        return None
    column = f"{prefix}_EAC_{str(detector).strip().upper()}"
    if column not in row.colnames:
        return None
    try:
        value = float(row[column])
    except Exception:
        return None
    if not np.isfinite(value):
        return None
    lo, hi = eng.EFFAREA_BOUNDS
    if not (lo - 1e-9 <= value <= hi + 1e-9):
        return None                      # outside the fitted bounds: not ours
    return value


def _validate_requested_detectors(
    product: FitProduct, requested: Sequence[str], cli_reference: str
) -> List[str]:
    dets = [str(det).strip() for det in requested if str(det).strip()]
    if not dets:
        raise DisplayInvariantError("no detectors requested")
    if len(set(dets)) != len(dets):
        raise DisplayInvariantError(f"duplicate detector(s) in --dets: {dets}")
    unknown = [det for det in dets if det not in product.fit_dets]
    if unknown:
        raise DisplayInvariantError(
            f"requested detectors {unknown} were not in engine fit_dets={list(product.fit_dets)}"
        )
    if cli_reference != product.reference_det:
        raise DisplayInvariantError(
            f"--ref {cli_reference!r} differs from engine reference_det "
            f"{product.reference_det!r}"
        )
    if product.reference_det not in dets:
        raise DisplayInvariantError(
            f"requested detector set must include engine reference {product.reference_det!r}"
        )
    return dets


def _valid_aic_state(row: Row) -> Tuple[str, Optional[float]]:
    valid_pairs = []
    for spec in _specs_for_row(row):
        value = engine_aic(row, spec)
        if _status(row, spec) == "OK" and _valid(row, spec) and value is not None:
            valid_pairs.append((value, str(spec["name"])))

    stored_winner = str(row["BEST_AIC_MODEL"]).strip()
    if not valid_pairs:
        if stored_winner != "INCONCLUSIVE":
            raise DisplayInvariantError(
                f"engine winner is {stored_winner!r}, but row has no finite VALID models"
            )
        return stored_winner, None

    valid_pairs.sort(key=lambda item: item[0])
    valid_zero, calculated_winner = valid_pairs[0]
    if stored_winner not in SPEC_BY_NAME:
        raise DisplayInvariantError(f"engine winner {stored_winner!r} is not registered")
    winner_spec = SPEC_BY_NAME[stored_winner]
    if _status(row, winner_spec) != "OK" or not _valid(row, winner_spec):
        raise DisplayInvariantError(
            f"stored winner {stored_winner!r} is not STATUS=OK and VALID"
        )
    winner_aic = engine_aic(row, winner_spec)
    if winner_aic is None or abs(winner_aic - valid_zero) > AIC_INVARIANT_ATOL:
        raise DisplayInvariantError(
            f"stored winner {stored_winner!r} is not the finite VALID AIC minimum "
            f"({winner_aic!r} versus {valid_zero!r}, argmin={calculated_winner!r})"
        )
    return stored_winner, valid_zero


def _validate_row_detectors(row: Row, product: FitProduct, requested: Sequence[str]) -> None:
    if "PLUGIN_DETS" not in row.colnames:
        raise DisplayInvariantError("fit row has no PLUGIN_DETS")
    row_dets = _split_csv(row["PLUGIN_DETS"])
    unknown = [det for det in row_dets if det not in product.fit_dets]
    if unknown:
        raise DisplayInvariantError(
            f"row PLUGIN_DETS contains detectors absent from product registry: {unknown}"
        )


def _build_plugins(
    trig: str,
    row: Row,
    detector_names: Sequence[str],
    backgrounds: Mapping[str, Tuple[Tuple[float, float], Tuple[float, float]]],
    eac_prefix: str = "",
    restored: Optional[set] = None,
) -> List[object]:
    """Rebuild the block's plugins.

    When `eac_prefix` names the model being displayed and the row carries that
    model's fitted EAC constant for a detector, the constant is RESTORED with
    threeML's own `fix_effective_area_correction` and the detector's name is
    added to `restored`. Otherwise the correction is left free, the detector is
    not folded, and the caller omits it — the original fail-closed behaviour.
    """
    start = _finite_float(row["T_START"], "T_START")
    stop = _finite_float(row["T_STOP"], "T_STOP")
    eac_dets = set(_row_eac_dets(row))
    plugins = []
    for detector in detector_names:
        if detector not in backgrounds:
            raise DisplayInvariantError(
                f"approved background row absent for requested detector {detector!r}"
            )
        pre, post = backgrounds[detector]
        built = eng.build_spectrumlike_per_block(
            trig, detector, pre, post, [start], [stop]
        )
        if not built or built[0] is None:
            raise DisplayInvariantError(
                f"engine could not rebuild plugin {detector} for [{start:.8f},{stop:.8f}] s"
            )
        plugin = built[0]
        if detector in eac_dets:
            stored = _stored_eac(row, eac_prefix, detector)
            try:
                if stored is None:
                    plugin.use_effective_area_correction(*eng.EFFAREA_BOUNDS)
                else:
                    # native: sets the value AND fixes it (SpectrumLike.py:2242)
                    plugin.fix_effective_area_correction(stored)
                    if restored is not None:
                        restored.add(detector)
            except Exception as exc:
                raise DisplayInvariantError(
                    f"row says EAC was fitted for {detector}, but activation failed: {exc}"
                ) from exc
        plugins.append(plugin)
    return plugins


def _group_contiguous_channels(
    energy_lo: np.ndarray,
    energy_hi: np.ndarray,
    observed: np.ndarray,
    background: np.ndarray,
    predicted: np.ndarray,
    background_variance: Optional[np.ndarray],
    rebin: Tuple[float, int],
) -> Mapping[str, np.ndarray]:
    """Apply the proven XSPEC grouping primitive without crossing masked gaps."""
    keys = ("lo", "hi", "obs", "bkg", "pred", "var", "ul")
    if not len(energy_lo):
        return {
            key: np.asarray([], dtype=bool if key == "ul" else float)
            for key in keys
        }

    # The imported XSPEC grouping helper assumes its input channels are adjacent.
    # Active-measurement masks remove channels (notably the NaI K edge), so feeding
    # the compressed arrays in one call would group across an unmeasured gap.
    adjacent = np.isclose(
        energy_hi[:-1],
        energy_lo[1:],
        rtol=ENERGY_CONTIGUITY_RTOL,
        atol=0.0,
    )
    boundaries = [0] + (np.flatnonzero(~adjacent) + 1).tolist() + [len(energy_lo)]
    pieces = []
    for start, stop in zip(boundaries[:-1], boundaries[1:]):
        variance = (
            None
            if background_variance is None
            else background_variance[start:stop]
        )
        pieces.append(
            _rebin_for_plot(
                energy_lo[start:stop],
                energy_hi[start:stop],
                observed[start:stop],
                background[start:stop],
                predicted[start:stop],
                variance,
                float(rebin[0]),
                int(rebin[1]),
            )
        )
    return {
        key: np.concatenate([np.asarray(piece[key]) for piece in pieces])
        for key in keys
    }


def _raw_groups(plugin: object, rebin: Tuple[float, int]) -> Mapping[str, np.ndarray]:
    """Model-independent plot groups, preserving every masked energy gap."""
    mask = np.asarray(plugin.mask, dtype=bool)
    bounds = np.asarray(plugin.response.ebounds, dtype=float)
    energy_lo = bounds[:-1][mask]
    energy_hi = bounds[1:][mask]
    observed = np.asarray(plugin.observed_counts, dtype=float)[mask]
    background = np.asarray(plugin.background_counts, dtype=float)[mask]
    background_errors = getattr(plugin, "background_count_errors", None)
    background_variance = (
        np.asarray(background_errors, dtype=float)[mask] ** 2
        if background_errors is not None
        else None
    )
    return _group_contiguous_channels(
        energy_lo,
        energy_hi,
        observed,
        background,
        np.zeros_like(observed),
        background_variance,
        rebin,
    )


def unfold_detector(plugin: object, nufnu_fn, sig_floor: float, max_group: int):
    """Legacy ratio unfolding extended to preserve masked energy discontinuities."""
    if not hasattr(plugin, "observed_counts"):
        return None
    try:
        energy_lo, energy_hi, observed, background, background_variance, predicted = (
            _legacy._plugin_counts(plugin)
        )
        groups = _group_contiguous_channels(
            np.asarray(energy_lo, dtype=float),
            np.asarray(energy_hi, dtype=float),
            np.asarray(observed, dtype=float),
            np.asarray(background, dtype=float),
            np.asarray(predicted, dtype=float),
            (
                None
                if background_variance is None
                else np.asarray(background_variance, dtype=float)
            ),
            (float(sig_floor), int(max_group)),
        )
        midpoint = np.sqrt(groups["lo"] * groups["hi"])
        xerr = np.vstack((midpoint - groups["lo"], groups["hi"] - midpoint))
        model_nufnu = _ev(nufnu_fn, midpoint)
        good = groups["pred"] > 0.5
        net = groups["obs"] - groups["bkg"]
        sigma = np.sqrt(groups["var"])
        nufnu = np.full_like(midpoint, np.nan)
        nufnu_error = np.full_like(midpoint, np.nan)
        residual = np.full_like(midpoint, np.nan)
        nufnu[good] = model_nufnu[good] * net[good] / groups["pred"][good]
        nufnu_error[good] = (
            model_nufnu[good] * sigma[good] / groups["pred"][good]
        )
        residual[good] = (net[good] - groups["pred"][good]) / sigma[good]
        is_upper_limit = np.asarray(groups["ul"], dtype=bool)
        drawable_upper_limit = is_upper_limit & good
        nufnu[drawable_upper_limit] = (
            model_nufnu[drawable_upper_limit]
            * (
                np.maximum(net[drawable_upper_limit], 0.0)
                + 2.0 * sigma[drawable_upper_limit]
            )
            / groups["pred"][drawable_upper_limit]
        )
        return {
            "emid": midpoint,
            "xerr": xerr,
            "nufnu": nufnu,
            "nufnu_err": nufnu_error,
            "resid": residual,
            "is_ul": is_upper_limit,
        }
    except Exception:
        return None


def detected_energy_domains(
    plugins: Sequence[object], rebin: Tuple[float, int]
) -> Tuple[Tuple[float, float], ...]:
    """Union of detected grouped-channel domains across plotted detectors."""
    intervals: List[Tuple[float, float]] = []
    for plugin in plugins:
        if not hasattr(plugin, "observed_counts"):
            continue
        groups = _raw_groups(plugin, rebin)
        detected = ~np.asarray(groups["ul"], dtype=bool)
        for lo, hi in zip(
            np.asarray(groups["lo"], dtype=float)[detected],
            np.asarray(groups["hi"], dtype=float)[detected],
        ):
            if np.isfinite(lo) and np.isfinite(hi) and hi > lo > 0:
                intervals.append((float(lo), float(hi)))
    if not intervals:
        return ()

    merged: List[List[float]] = []
    for lo, hi in sorted(intervals):
        if not merged or not (
            lo < merged[-1][1]
            or np.isclose(
                lo,
                merged[-1][1],
                rtol=ENERGY_CONTIGUITY_RTOL,
                atol=0.0,
            )
        ):
            merged.append([lo, hi])
        else:
            merged[-1][1] = max(merged[-1][1], hi)
    return tuple((float(lo), float(hi)) for lo, hi in merged)


def detected_energy_span(
    plugins: Sequence[object], rebin: Tuple[float, int]
) -> Optional[Tuple[float, float]]:
    """Compatibility helper: outer hull of :func:`detected_energy_domains`."""
    domains = detected_energy_domains(plugins, rebin)
    return (domains[0][0], domains[-1][1]) if domains else None


def _attach_component(component: object, plugins: Sequence[object]) -> Model:
    """Attach a stored component for forward evaluation; no minimizer is created."""
    source = PointSource(
        "grb", eng.SRC_RA, eng.SRC_DEC, spectral_shape=component
    )
    model = Model(source)
    for plugin in plugins:
        plugin.set_model(model)
    return model


def _nufnu_function(component: object):
    return lambda energy: np.asarray(energy, dtype=float) ** 2 * _ev(
        component, np.asarray(energy, dtype=float)
    )


def _same_groups(
    first: Mapping[str, np.ndarray], second: Mapping[str, np.ndarray]
) -> bool:
    return (
        np.array_equal(np.asarray(first["is_ul"]), np.asarray(second["is_ul"]))
        and np.allclose(
            np.asarray(first["emid"], dtype=float),
            np.asarray(second["emid"], dtype=float),
            rtol=0.0,
            atol=0.0,
        )
        and np.allclose(
            np.asarray(first["xerr"], dtype=float),
            np.asarray(second["xerr"], dtype=float),
            rtol=0.0,
            atol=0.0,
        )
    )


def prepare_block(
    trig: str,
    row: Row,
    product: FitProduct,
    detector_names: Sequence[str],
    backgrounds: Mapping[str, Tuple[Tuple[float, float], Tuple[float, float]]],
    rebin: Tuple[float, int],
) -> BlockDisplay:
    index = int(row["BLOCK"])
    _validate_row_detectors(row, product, detector_names)
    winner_name, _ = _valid_aic_state(row)
    row_detectors = _split_csv(row["PLUGIN_DETS"])
    available = [det for det in detector_names if det in row_detectors]
    missing = tuple(det for det in detector_names if det not in row_detectors)
    eac_dets = set(_row_eac_dets(row))
    _winner_spec = SPEC_BY_NAME.get(winner_name)
    _eac_prefix = str(_winner_spec["prefix"]) if _winner_spec else ""
    eac_restored: set = set()
    try:
        plugins = _build_plugins(trig, row, available, backgrounds,
                                 eac_prefix=_eac_prefix, restored=eac_restored)
    except DisplayInvariantError as exc:
        return BlockDisplay(
            row=row,
            block_index=index,
            significance=product.block_significance.get(index),
            plugins=[],
            detector_names=list(available),
            rebin=(float(rebin[0]), int(rebin[1])),
            detected_domains=(),
            detected_span=None,
            axis_span=None,
            winner_spec=SPEC_BY_NAME.get(winner_name),
            winner_component=None,
            missing_detectors=missing,
            error=f"PLUGIN RECONSTRUCTION FAILED — {exc}",
        )
    domains = detected_energy_domains(plugins, rebin)
    detected = (domains[0][0], domains[-1][1]) if domains else None
    axis_span = None
    if detected is not None:
        pad = 10.0 ** DETECTED_PAD_DEX
        axis_span = (detected[0] / pad, detected[1] * pad)

    block = BlockDisplay(
        row=row,
        block_index=index,
        significance=product.block_significance.get(index),
        plugins=plugins,
        detector_names=list(available),
        rebin=(float(rebin[0]), int(rebin[1])),
        detected_domains=domains,
        detected_span=detected,
        axis_span=axis_span,
        winner_spec=SPEC_BY_NAME.get(winner_name),
        winner_component=None,
        missing_detectors=missing,
    )
    if detected is None:
        block.error = "NO DETECTED CHANNELS — MODEL NOT DRAWN"
        return block
    if block.winner_spec is None:
        block.error = f"engine winner {winner_name!r} cannot be constructed"
        return block

    winner_component = model_from_row(block.winner_spec, row)
    if winner_component is None:
        block.error = "winner unavailable: " + model_from_row_error(block.winner_spec)
        return block
    block.winner_component = winner_component
    _attach_component(winner_component, plugins)

    # A detector is omitted only if its FITTED EAC could not be restored. Where
    # scripts/10 (new fits) or scripts/49_recover_eac.py (backfill) supplied the
    # constant, it is fixed to that value and the detector is folded normally.
    # A unit default is still never substituted — that would move the unfolded
    # points and recreate the display-layer refit bug this file exists to end.
    omitted = tuple(det for det in available
                    if det in eac_dets and det not in eac_restored)
    block.omitted_eac = omitted
    print(
        f"BLOCK {index}: detected span {detected[0]:.3f}-{detected[1]:.3f} keV; "
        f"axis {axis_span[0]:.3f}-{axis_span[1]:.3f} keV "
        f"({DETECTED_PAD_DEX:.2f}-dex pad); detected domains={len(domains)}"
    )
    if missing:
        print("ROW-MISSING REQUESTED DETECTORS: " + ",".join(missing))
    if omitted:
        print(
            "COUNT DIAGNOSTICS OMITTED (fitted EAC values not serialized): "
            + ",".join(omitted)
        )
    drawable = [det for det in available if det not in omitted]
    diagnostic_failures = []
    for plugin, detector in zip(plugins, available):
        if detector not in drawable:
            continue
        if not hasattr(plugin, "observed_counts"):
            diagnostic_failures.append(f"{detector}: no folded counts")
            continue
        unfolded = unfold_detector(
            plugin, _nufnu_function(winner_component), float(rebin[0]), int(rebin[1])
        )
        if unfolded is None:
            diagnostic_failures.append(f"{detector}: winner unfolding failed")
            continue
        block.unfolded_under_winner[detector] = unfolded
    if diagnostic_failures:
        block.error = "; ".join(diagnostic_failures)
    if not block.unfolded_under_winner:
        block.error = "no detector has reconstructible winner-unfolded data"
    return block


def _block_text(block: BlockDisplay) -> str:
    start = _finite_float(block.row["T_START"], "T_START")
    stop = _finite_float(block.row["T_STOP"], "T_STOP")
    if block.block_index < 0:
        return f"T_INT [{start:.2f}, {stop:.2f}] s"
    if block.significance is None:
        raise DisplayInvariantError(f"block {block.block_index} has no significance")
    return (
        f"bin {block.block_index} [{start:.2f}, {stop:.2f}] s; "
        rf"$S={block.significance:.1f}\,\sigma$"
    )


def _model_title(row: Row, spec: Mapping[str, object]) -> Tuple[str, bool]:
    winner, valid_zero = _valid_aic_state(row)
    name = str(spec["name"])
    status = _status(row, spec)
    is_best = name == winner
    value = engine_aic(row, spec)
    if status != "OK" or value is None:
        return f"{'[BEST] ' if is_best else ''}{name} — engine: no fit", is_best
    if valid_zero is None:
        delta_text = r"$\Delta$AIC$_{\rm valid}$ unavailable"
    else:
        delta_text = rf"$\Delta$AIC$_{{\rm valid}}={value - valid_zero:+.1f}$"
    validity = "" if _valid(row, spec) else "  [INVALID]"
    return f"{'[BEST] ' if is_best else ''}{name}  {delta_text}{validity}", is_best


def prepare_panel(block: BlockDisplay, spec: Mapping[str, object], include_block_text: bool) -> PanelDisplay:
    model_title, is_best = _model_title(block.row, spec)
    title = f"{_block_text(block)}\n{model_title}" if include_block_text else model_title
    if _status(block.row, spec) != "OK":
        return PanelDisplay(
            block=block,
            spec=spec,
            component=None,
            residuals={},
            title=title,
            is_best=is_best,
            error=f"ENGINE STATUS={_status(block.row, spec)}; CURVE UNAVAILABLE",
        )

    component = model_from_row(spec, block.row)
    if component is None:
        return PanelDisplay(
            block=block,
            spec=spec,
            component=None,
            residuals={},
            title=title,
            is_best=is_best,
            error=model_from_row_error(spec),
        )
    if block.detected_span is None:
        return PanelDisplay(
            block=block,
            spec=spec,
            component=component,
            residuals={},
            title=title,
            is_best=is_best,
            error=block.error or "NO DETECTED CHANNELS — MODEL NOT DRAWN",
        )

    _attach_component(component, block.plugins)
    residuals: Dict[str, Mapping[str, np.ndarray]] = {}
    for plugin, detector in zip(block.plugins, block.detector_names):
        common = block.unfolded_under_winner.get(detector)
        if common is None:
            continue
        candidate = unfold_detector(
            plugin,
            _nufnu_function(component),
            float(block.rebin[0]),
            int(block.rebin[1]),
        )
        if candidate is None:
            return PanelDisplay(
                block=block,
                spec=spec,
                component=component,
                residuals=residuals,
                title=title,
                is_best=is_best,
                error=f"candidate residual evaluation failed for {detector}",
            )
        if not _same_groups(common, candidate):
            raise DisplayInvariantError(
                f"rebin groups moved between winner and {spec['name']} for {detector}"
            )
        residuals[detector] = candidate

    return PanelDisplay(
        block=block,
        spec=spec,
        component=component,
        residuals=residuals,
        title=title,
        is_best=is_best,
        error=block.error,
    )


def _detector_colour(detector: str, detector_names: Sequence[str]) -> str:
    del detector_names  # colour is detector identity, never CLI order/subsetting
    return det_color(detector, _NAI_ID_INDEX.get(str(detector).lower(), 0))


def _model_colour(spec: Mapping[str, object]) -> object:
    # Stable registry index: colour is model identity, never AIC rank.
    index = SPEC_INDEX[str(spec["prefix"])]
    return plt.get_cmap("viridis")((index + 1) / (len(ALL_SPECS) + 1))


def _curve_values(component: object, energy: np.ndarray) -> np.ndarray:
    return np.asarray(energy, dtype=float) ** 2 * _ev(component, energy)


def _plot_segmented_curve(
    ax,
    component: object,
    detected_domains: Sequence[Tuple[float, float]],
    axis_span: Tuple[float, float],
    color: object,
    linewidth: float,
    label: Optional[str] = None,
    zorder: int = 4,
) -> None:
    axis_lo, axis_hi = axis_span
    segments: List[Tuple[float, float, str]] = []
    cursor = axis_lo
    for raw_lo, raw_hi in detected_domains:
        lo = max(axis_lo, raw_lo)
        hi = min(axis_hi, raw_hi)
        if hi <= lo:
            continue
        if lo > cursor:
            segments.append((cursor, lo, ":"))
        segments.append((lo, hi, "-"))
        cursor = max(cursor, hi)
    if cursor < axis_hi:
        segments.append((cursor, axis_hi, ":"))
    label_pending = label
    for lo, hi, linestyle in segments:
        if not (np.isfinite(lo) and np.isfinite(hi) and hi > lo > 0):
            continue
        energy = np.geomspace(lo, hi, 120)
        values = _curve_values(component, energy)
        good = np.isfinite(values) & (values > 0)
        if np.count_nonzero(good) < 2:
            continue
        ax.plot(
            energy[good],
            values[good],
            color=color,
            linewidth=linewidth,
            linestyle=linestyle,
            label=label_pending,
            zorder=zorder,
        )
        label_pending = None


def _within_axis(block: BlockDisplay, energies: np.ndarray) -> np.ndarray:
    values = np.asarray(energies, dtype=float)
    if block.axis_span is None:
        return np.ones(values.shape, dtype=bool)
    return (values >= block.axis_span[0]) & (values <= block.axis_span[1])


def _draw_unfolded_data(ax, block: BlockDisplay) -> List[float]:
    y_values: List[float] = []
    for detector in block.detector_names:
        unfolded = block.unfolded_under_winner.get(detector)
        if unfolded is None:
            continue
        color = _detector_colour(detector, block.detector_names)
        energy = np.asarray(unfolded["emid"], dtype=float)
        within = _within_axis(block, energy)
        detected = (
            within
            & ~np.asarray(unfolded["is_ul"], dtype=bool)
            & np.isfinite(unfolded["nufnu"])
            & np.isfinite(unfolded["nufnu_err"])
            & (np.asarray(unfolded["nufnu"]) > 0)
        )
        if np.any(detected):
            ax.errorbar(
                energy[detected],
                np.asarray(unfolded["nufnu"])[detected],
                yerr=np.asarray(unfolded["nufnu_err"])[detected],
                xerr=np.asarray(unfolded["xerr"])[:, detected],
                fmt="o",
                markersize=PUB["ms_data"],
                markeredgecolor="black",
                markeredgewidth=PUB["lw_reference"],
                color=color,
                alpha=0.9,
                elinewidth=PUB["lw_reference"],
                capsize=0,
                linewidth=0,
                zorder=6,
            )
            centre = np.asarray(unfolded["nufnu"])[detected]
            error = np.asarray(unfolded["nufnu_err"])[detected]
            y_values.extend(centre[np.isfinite(centre) & (centre > 0)].tolist())
            upper = centre + error
            y_values.extend(upper[np.isfinite(upper) & (upper > 0)].tolist())

        upper_limit = (
            within
            & np.asarray(unfolded["is_ul"], dtype=bool)
            & np.isfinite(unfolded["nufnu"])
            & (np.asarray(unfolded["nufnu"]) > 0)
        )
        if np.any(upper_limit):
            energy_ul = energy[upper_limit]
            value = np.asarray(unfolded["nufnu"])[upper_limit]
            ax.errorbar(
                energy_ul,
                value,
                xerr=np.asarray(unfolded["xerr"])[:, upper_limit],
                fmt="none",
                color=color,
                alpha=0.75,
                elinewidth=PUB["lw_reference"],
                capsize=0,
                zorder=5,
            )
            ax.scatter(
                energy_ul,
                value,
                marker=r"$\downarrow$",
                s=PUB["ms_data"] ** 2,
                color=color,
                alpha=0.85,
                zorder=6,
            )
            y_values.extend(value[np.isfinite(value) & (value > 0)].tolist())
    return y_values


def _draw_residuals(ax, panel: PanelDisplay) -> List[float]:
    residual_values: List[float] = []
    for detector in panel.block.detector_names:
        unfolded = panel.residuals.get(detector)
        if unfolded is None:
            continue
        energy = np.asarray(unfolded["emid"], dtype=float)
        detected = (
            _within_axis(panel.block, energy)
            & ~np.asarray(unfolded["is_ul"], dtype=bool)
            & np.isfinite(unfolded["resid"])
        )
        if not np.any(detected):
            continue
        values = np.asarray(unfolded["resid"])[detected]
        color = _detector_colour(detector, panel.block.detector_names)
        ax.errorbar(
            energy[detected],
            values,
            yerr=np.ones_like(values),
            xerr=np.asarray(unfolded["xerr"])[:, detected],
            fmt="o",
            markersize=PUB["ms_data"],
            markeredgecolor="black",
            markeredgewidth=PUB["lw_reference"],
            color=color,
            alpha=0.85,
            elinewidth=PUB["lw_reference"],
            capsize=0,
            linewidth=0,
            zorder=4,
        )
        residual_values.extend(values.tolist())
    return residual_values


def _set_y_limits(ax, y_values: Sequence[float], component: Optional[object], block: BlockDisplay) -> None:
    positive = np.asarray([value for value in y_values if np.isfinite(value) and value > 0])
    if positive.size == 0 and component is not None and block.detected_domains:
        energy = np.concatenate(
            [np.geomspace(lo, hi, 80) for lo, hi in block.detected_domains]
        )
        values = _curve_values(component, energy)
        positive = values[np.isfinite(values) & (values > 0)]
    if positive.size == 0:
        return
    log_values = np.log10(positive)
    low, high = np.nanpercentile(log_values, [1.0, 99.7])
    if not (np.isfinite(low) and np.isfinite(high)):
        return
    if high <= low:
        high = low + 1.0
    ax.set_ylim(10.0 ** (low - Y_PAD_DEX), 10.0 ** (high + Y_PAD_DEX))


def _set_residual_limits(ax, values: Sequence[float]) -> None:
    finite = np.abs(np.asarray([value for value in values if np.isfinite(value)]))
    span = 4.0
    if finite.size:
        span = max(span, float(np.nanpercentile(finite, 99.7)) + 1.0)
    ax.set_ylim(-span, span)


def _draw_panel(fig, grid_cell, panel: PanelDisplay):
    inner = grid_cell.subgridspec(2, 1, height_ratios=[3, 1], hspace=0.0)
    ax = fig.add_subplot(inner[0])
    residual_ax = fig.add_subplot(inner[1], sharex=ax)

    ax.set_xscale("log")
    ax.set_yscale("log")
    residual_ax.set_xscale("log")
    ax.set_ylabel(NUFNU_LABEL)
    residual_ax.set_xlabel(ENERGY_LABEL)
    residual_ax.text(
        0.02,
        0.90,
        RESID_LABEL,
        transform=residual_ax.transAxes,
        ha="left",
        va="top",
        fontsize=PUB["legend_size"],
        color="0.25",
        zorder=10,
    )
    plt.setp(ax.get_xticklabels(), visible=False)
    residual_ax.axhline(0.0, color="black", linewidth=PUB["lw_reference"], zorder=1)

    block = panel.block
    y_values = _draw_unfolded_data(ax, block)
    if block.axis_span is not None:
        ax.set_xlim(*block.axis_span)
        residual_ax.set_xlim(*block.axis_span)

    if panel.component is not None and block.detected_span is not None and block.axis_span is not None:
        _plot_segmented_curve(
            ax,
            panel.component,
            block.detected_domains,
            block.axis_span,
            color="black",
            linewidth=PUB["lw_primary"],
        )

    residual_values = _draw_residuals(residual_ax, panel)
    _set_y_limits(ax, y_values, panel.component, block)
    _set_residual_limits(residual_ax, residual_values)
    ax.set_title(panel.title, fontsize=PUB["tick_size"], loc="left")

    if panel.error:
        ax.text(
            0.5,
            0.5,
            "UNAVAILABLE\n" + panel.error,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=PUB["legend_size"],
            color="black",
        )
    return ax, residual_ax


def _detector_legend_handles(blocks: Sequence[BlockDisplay]) -> List[Line2D]:
    if not blocks:
        return []
    detector_names: List[str] = []
    for block in blocks:
        for detector in [*block.detector_names, *block.missing_detectors]:
            if detector not in detector_names:
                detector_names.append(detector)
    omitted_any = {
        detector: any(detector in block.omitted_eac for block in blocks)
        for detector in detector_names
    }
    missing_any = {
        detector: any(detector in block.missing_detectors for block in blocks)
        for detector in detector_names
    }
    handles = []
    for detector in detector_names:
        color = _detector_colour(detector, detector_names)
        if omitted_any[detector]:
            label = f"{detector.upper()} — span only; fitted EAC not stored"
            marker = "x"
        else:
            label = f"{detector.upper()} data"
            marker = "o"
        if missing_any[detector]:
            label += " (absent in some fit rows)"
        handles.append(
            Line2D(
                [],
                [],
                color=color,
                marker=marker,
                linestyle="none",
                markersize=PUB["ms_data"],
                markeredgecolor="black" if marker == "o" else color,
                markeredgewidth=PUB["lw_reference"],
                label=label,
            )
        )
    handles.append(
        Line2D(
            [],
            [],
            color="0.25",
            marker=r"$\downarrow$",
            linestyle="none",
            markersize=PUB["ms_data"],
            label=r"$2\sigma$ upper limit (bare arrow)",
        )
    )
    return handles


def _footer(blocks: Sequence[BlockDisplay], extra: Optional[str] = None) -> str:
    winners = sorted(
        {
            str(block.winner_spec["name"])
            for block in blocks
            if block.winner_spec is not None
        }
    )
    unfolded = ", ".join(winners) if winners else "unavailable"
    omitted = sorted({det for block in blocks for det in block.omitted_eac})
    missing = sorted({det for block in blocks for det in block.missing_detectors})
    line1 = (
        f"Points: ratio-unfolded under the engine winner ({unfolded}); residuals: "
        "count-space. No 68% band (joint covariance not stored)."
    )
    line2 = (
        f"Axis: detected non-upper-limit domains + {DETECTED_PAD_DEX:.2f}-dex outer pad; "
        "curves are solid only in those domains and dotted elsewhere."
    )
    if omitted:
        line2 += " Folded diagnostics omitted (EAC not stored): " + ", ".join(
            det.upper() for det in omitted
        ) + "."
    if missing:
        line2 += " Row-missing requested detectors: " + ", ".join(
            det.upper() for det in missing
        ) + "."
    paragraphs = [line1, line2, FOLDED_PROVENANCE_WARNING]
    if extra:
        paragraphs.append(extra)
    # Manual wrapping is part of the print contract.  Matplotlib's ``wrap=True``
    # is applied after tight-bbox discovery, so an unbroken provenance sentence
    # can silently widen the canvas and shrink the scientific panel on the page.
    return "\n".join(
        wrapped
        for paragraph in paragraphs
        for wrapped in textwrap.wrap(paragraph, width=90)
    )


def _winner_frame(fig, axes_pair: Tuple[object, object]) -> None:
    ax, residual_ax = axes_pair
    boxes = [ax.get_position(), residual_ax.get_position()]
    x0 = min(box.x0 for box in boxes)
    y0 = min(box.y0 for box in boxes)
    x1 = max(box.x1 for box in boxes)
    y1 = max(box.y1 for box in boxes)
    frame = Rectangle(
        (x0, y0),
        x1 - x0,
        y1 - y0,
        transform=fig.transFigure,
        facecolor="none",
        edgecolor="black",
        linewidth=PUB["lw_primary"] * 1.5,
        zorder=20,
        clip_on=False,
    )
    fig.add_artist(frame)


def _chunks(items: Sequence[PanelDisplay], size: int) -> Iterable[Sequence[PanelDisplay]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _assemble_vertical_png(page_paths: Sequence[Path], output_path: Path) -> None:
    if len(page_paths) == 1:
        # Render once more to the legacy name would risk a style divergence; copy bytes.
        output_path.write_bytes(page_paths[0].read_bytes())
        return
    try:
        from PIL import Image
    except ImportError as exc:
        raise DisplayInvariantError(
            "Pillow is required to assemble the legacy-name multipage PNG"
        ) from exc
    images = [Image.open(path).convert("RGB") for path in page_paths]
    width = max(image.width for image in images)
    height = sum(image.height for image in images)
    canvas = Image.new("RGB", (width, height), "white")
    y_offset = 0
    for image in images:
        canvas.paste(image, (0, y_offset))
        y_offset += image.height
    canvas.save(output_path, dpi=(PUB["dpi"], PUB["dpi"]))
    for image in images:
        image.close()


def _render_grid(
    panels: Sequence[PanelDisplay],
    output_path: Path,
    figure_title: str,
) -> Path:
    pages = list(_chunks(list(panels), PANELS_PER_PAGE))
    if not pages:
        raise DisplayInvariantError("no panels requested")
    pdf_path = output_path.with_suffix(".pdf")
    page_paths: List[Path] = []
    with PdfPages(pdf_path) as pdf:
        for page_number, page_panels in enumerate(pages, start=1):
            rows = int(np.ceil(len(page_panels) / GRID_COLUMNS))
            fig = plt.figure(
                figsize=(PUB["figwidth"], PUB["figwidth"] * 1.2)
            )
            grid = fig.add_gridspec(
                rows,
                GRID_COLUMNS,
                hspace=0.40,
                wspace=0.34,
                top=0.78,
                bottom=0.20,
                left=0.10,
                right=0.98,
            )
            winner_axes = []
            for index, panel in enumerate(page_panels):
                axes_pair = _draw_panel(
                    fig, grid[index // GRID_COLUMNS, index % GRID_COLUMNS], panel
                )
                if panel.is_best:
                    winner_axes.append(axes_pair)

            page_blocks = [panel.block for panel in page_panels]
            handles = _detector_legend_handles(page_blocks)
            fig.legend(
                handles=handles,
                loc="upper center",
                bbox_to_anchor=(0.5, 0.91),
                ncol=min(3, len(handles)),
                fontsize=PUB["legend_size"],
            )
            page_suffix = f" — page {page_number}/{len(pages)}" if len(pages) > 1 else ""
            fig.suptitle(
                figure_title + page_suffix,
                fontsize=PUB["font_size"],
                y=0.985,
            )
            fig.text(
                0.5,
                0.025,
                _footer(page_blocks),
                ha="center",
                va="bottom",
                fontsize=PUB["legend_size"],
                color="0.25",
            )
            fig.canvas.draw()
            for axes_pair in winner_axes:
                _winner_frame(fig, axes_pair)

            page_path = output_path.with_name(
                f"{output_path.stem}_p{page_number:02d}{output_path.suffix}"
            )
            fig.savefig(page_path, bbox_inches="tight")
            pdf.savefig(fig, bbox_inches="tight")
            page_paths.append(page_path)
            plt.close(fig)

    _assemble_vertical_png(page_paths, output_path)
    print(f"WROTE {output_path}")
    print(f"WROTE {pdf_path} ({len(pages)} page(s))")
    for page_path in page_paths:
        print(f"WROTE {page_path}")
    return output_path


def _ranked_valid_specs(row: Row) -> Tuple[List[Tuple[float, Mapping[str, object]]], List[str]]:
    winner, _ = _valid_aic_state(row)
    ranked = []
    for spec in _specs_for_row(row):
        value = engine_aic(row, spec)
        if _status(row, spec) == "OK" and _valid(row, spec) and value is not None:
            ranked.append((value, spec))
    ranked.sort(key=lambda item: item[0])
    if not ranked:
        # An engine-declared INCONCLUSIVE row is still a displayable result.  The
        # overlay must show that state on the page, not invent a curve or abort.
        return [], []
    shown = ranked[:OVERLAY_MAX_MODELS]
    if winner not in {str(spec["name"]) for _, spec in shown}:
        winner_pair = next((pair for pair in ranked if str(pair[1]["name"]) == winner), None)
        if winner_pair is None:
            raise DisplayInvariantError(f"VALID ranked set omits engine winner {winner!r}")
        shown = shown[:-1] + [winner_pair]
        shown.sort(key=lambda item: item[0])
    shown_names = {str(spec["name"]) for _, spec in shown}
    dropped = [str(spec["name"]) for _, spec in ranked if str(spec["name"]) not in shown_names]
    return shown, dropped


def _render_overlay(
    block: BlockDisplay,
    output_path: Path,
    figure_title: str,
) -> Path:
    shown, dropped = _ranked_valid_specs(block.row)
    winner_name, valid_zero = _valid_aic_state(block.row)

    fig = plt.figure(figsize=(PUB["figwidth"], PUB["figwidth"] * 1.15))
    grid = fig.add_gridspec(
        1,
        1,
        top=0.68,
        bottom=0.25,
        left=0.10,
        right=0.98,
    )
    inner = grid[0, 0].subgridspec(2, 1, height_ratios=[3, 1], hspace=0.0)
    ax = fig.add_subplot(inner[0])
    residual_ax = fig.add_subplot(inner[1], sharex=ax)
    ax.set_xscale("log")
    ax.set_yscale("log")
    residual_ax.set_xscale("log")
    ax.set_ylabel(NUFNU_LABEL)
    residual_ax.set_xlabel(ENERGY_LABEL)
    residual_ax.text(
        0.02,
        0.90,
        RESID_LABEL,
        transform=residual_ax.transAxes,
        ha="left",
        va="top",
        fontsize=PUB["legend_size"],
        color="0.25",
        zorder=10,
    )
    plt.setp(ax.get_xticklabels(), visible=False)
    residual_ax.axhline(0.0, color="black", linewidth=PUB["lw_reference"], zorder=1)

    y_values = _draw_unfolded_data(ax, block)
    if block.axis_span is not None:
        ax.set_xlim(*block.axis_span)
        residual_ax.set_xlim(*block.axis_span)
    else:
        # Do not let Matplotlib manufacture scientific-looking tick values for a
        # block whose detected energy support is absent.
        ax.set_xticks([])
        ax.set_yticks([])
        residual_ax.set_xticks([])
        residual_ax.set_yticks([])

    model_handles = []
    winner_component = None
    unavailable = []
    winner_drawn = False
    for value, spec in shown:
        component = model_from_row(spec, block.row)
        if component is None:
            reason = model_from_row_error(spec)
            unavailable.append(f"{spec['name']}: {reason}")
            model_handles.append(
                Line2D(
                    [],
                    [],
                    color="0.35",
                    marker="x",
                    linestyle="none",
                    markersize=PUB["ms_data"],
                    label=f"{spec['name']}  [CURVE UNAVAILABLE]",
                )
            )
            continue
        is_winner = str(spec["name"]) == winner_name
        color = "black" if is_winner else _model_colour(spec)
        linewidth = PUB["lw_primary"] * 1.5 if is_winner else PUB["lw_secondary"]
        if block.detected_span is None or block.axis_span is None:
            unavailable.append(f"{spec['name']}: no detected energy domain")
            model_handles.append(
                Line2D(
                    [],
                    [],
                    color="0.35",
                    marker="x",
                    linestyle="none",
                    markersize=PUB["ms_data"],
                    label=f"{spec['name']}  [NO DETECTED DOMAIN]",
                )
            )
            continue
        _plot_segmented_curve(
            ax,
            component,
            block.detected_domains,
            block.axis_span,
            color=color,
            linewidth=linewidth,
            zorder=7 if is_winner else 3,
        )
        label = (
            ("[BEST] " if is_winner else "")
            + f"{spec['name']}  "
            + rf"$\Delta$AIC$_{{\rm valid}}={value - valid_zero:+.1f}$"
        )
        model_handles.append(
            Line2D(
                [],
                [],
                color=color,
                linewidth=linewidth,
                linestyle="-",
                label=label,
            )
        )
        if is_winner:
            winner_component = component
            winner_drawn = True

    winner_panel = PanelDisplay(
        block=block,
        spec=block.winner_spec,
        component=block.winner_component,
        residuals={},
        title="",
        is_best=True,
    )
    if block.winner_spec is not None:
        winner_panel = prepare_panel(block, block.winner_spec, include_block_text=False)
    residual_values = _draw_residuals(residual_ax, winner_panel)
    diagnostic_messages = []
    if valid_zero is None:
        diagnostic_messages.append("NO FINITE STATUS=OK, VALID ENGINE MODELS")
    if winner_panel.error or block.error:
        diagnostic_messages.append(str(winner_panel.error or block.error))
    if unavailable:
        diagnostic_messages.append("; ".join(unavailable))
    diagnostic_error = " | ".join(diagnostic_messages) or None
    if diagnostic_error:
        ax.text(
            0.02,
            0.05,
            "FOLDED DIAGNOSTIC WARNING\n"
            + textwrap.fill(str(diagnostic_error), width=55),
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=PUB["legend_size"],
            color="black",
            zorder=20,
        )
    _set_y_limits(ax, y_values, winner_component, block)
    _set_residual_limits(residual_ax, residual_values)

    handles = _detector_legend_handles([block]) + model_handles
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.91),
        ncol=min(3, len(handles)),
        fontsize=PUB["legend_size"],
    )
    fig.suptitle(figure_title, fontsize=PUB["font_size"], y=0.985)
    extras = []
    if dropped:
        extras.append(
            "VALID models omitted by the eight-curve cap: " + ", ".join(dropped) + "."
        )
    if diagnostic_error:
        extras.append("Folded diagnostic warning: " + str(diagnostic_error) + ".")
    fig.text(
        0.5,
        0.025,
        _footer([block], extra=" ".join(extras) if extras else None),
        ha="center",
        va="bottom",
        fontsize=PUB["legend_size"],
        color="0.25",
    )
    fig.canvas.draw()
    if winner_drawn:
        _winner_frame(fig, (ax, residual_ax))
    fig.savefig(output_path, bbox_inches="tight")
    pdf_path = output_path.with_suffix(".pdf")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    print(f"WROTE {output_path}")
    print(f"WROTE {pdf_path}")
    if dropped:
        print("DROPPED VALID MODELS (engine-AIC order after cap): " + ", ".join(dropped))
    return output_path


def _select_block_row(product: FitProduct, which: object) -> Row:
    token = str(which).strip().lower()
    try:
        index = -1 if token in {"tint", "t_int", "-1"} else int(token)
    except ValueError as exc:
        raise DisplayInvariantError(
            f"invalid block token {which!r}; use an integer or tint"
        ) from exc
    if index not in product.rows_by_block:
        raise DisplayInvariantError(f"no engine fit row for BLOCK={index}")
    return product.rows_by_block[index]


def _validated_rebin(rebin: Sequence[float]) -> Tuple[float, int]:
    significance = float(rebin[0])
    max_channels = float(rebin[1])
    if not np.isfinite(significance) or significance <= 0:
        raise DisplayInvariantError("rebin SIG must be finite and > 0")
    if (
        not np.isfinite(max_channels)
        or max_channels < 1
        or not max_channels.is_integer()
    ):
        raise DisplayInvariantError("rebin MAXCH must be a positive integer")
    return significance, int(max_channels)


def run(
    trig: str,
    dets: Sequence[str],
    ref: str,
    mode: str,
    which: object,
    out: str,
    rebin: Tuple[float, int],
) -> str:
    rebin = _validated_rebin(rebin)
    out_dir = Path(out).expanduser()
    product = load_fit_product(trig, out_dir)
    detector_names = _validate_requested_detectors(product, dets, ref)
    _set_source_position(trig)
    backgrounds = _load_backgrounds(product, trig)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"ENGINE TABLE {product.table_path}")
    print(f"FIT SIDECAR {product.metadata_path}")
    print(f"BLOCK PRODUCT {product.blocks_path}")
    print(f"BACKGROUND CATALOG {product.background_path}")
    print(f"ENGINE REFERENCE {product.reference_det}; FIT DETECTORS {','.join(product.fit_dets)}")
    print("PROVENANCE WARNING: " + FOLDED_PROVENANCE_WARNING)

    if mode == "bin":
        row = _select_block_row(product, which)
        block = prepare_block(
            trig, row, product, detector_names, backgrounds, rebin
        )
        panels = [
            prepare_panel(block, spec, include_block_text=False)
            for spec in _specs_for_row(row)
        ]
        filename = out_dir / f"{trig}_nuFnu_bin{block.block_index}_allmodels.png"
        title = (
            f"{trig} — {_block_text(block)} — every engine model\n"
            f"Points unfolded under {block.winner_spec['name'] if block.winner_spec else 'no winner'}; "
            "stored-parameter evaluation only"
        )
        return str(_render_grid(panels, filename, title))

    if mode == "model":
        spec = SPEC_BY_NAME.get(str(which)) or SPEC_BY_PREFIX.get(str(which))
        if spec is None:
            choices = ", ".join(SPEC_BY_NAME)
            raise DisplayInvariantError(f"unknown model {which!r}; choose from {choices}")
        panels = []
        for row in product.ordinary_rows:
            block = prepare_block(
                trig, row, product, detector_names, backgrounds, rebin
            )
            panels.append(prepare_panel(block, spec, include_block_text=True))
        filename = out_dir / f"{trig}_nuFnu_{spec['prefix']}_allbins.png"
        title = (
            f"{trig} — {spec['name']} across all bins\n"
            "Each bin's points are unfolded under that bin's engine winner"
        )
        return str(_render_grid(panels, filename, title))

    if mode == "best":
        panels = []
        for row in product.ordinary_rows:
            block = prepare_block(
                trig, row, product, detector_names, backgrounds, rebin
            )
            if block.winner_spec is None:
                panels.append(
                    PanelDisplay(
                        block=block,
                        spec=None,
                        component=None,
                        residuals={},
                        title=(
                            f"{_block_text(block)}\n"
                            "[NO VALID ENGINE WINNER]"
                        ),
                        is_best=False,
                        error=block.error or "engine result is INCONCLUSIVE",
                    )
                )
                continue
            panels.append(prepare_panel(block, block.winner_spec, include_block_text=True))
        filename = out_dir / f"{trig}_nuFnu_best_montage.png"
        title = (
            f"{trig} — engine winner per bin\n"
            "Stored-parameter evaluation only; points unfolded under each winner"
        )
        return str(_render_grid(panels, filename, title))

    if mode == "binall":
        row = _select_block_row(product, which)
        block = prepare_block(
            trig, row, product, detector_names, backgrounds, rebin
        )
        token = "TINT" if block.block_index < 0 else f"bin{block.block_index}"
        filename = out_dir / f"{trig}_nuFnu_{token}_allmodels_overlay.png"
        title = (
            f"{trig} — {_block_text(block)} — top VALID models by stored engine AIC\n"
            f"[BEST] marked; points and residuals under "
            f"{block.winner_spec['name'] if block.winner_spec else 'no winner'}"
        )
        return str(_render_overlay(block, filename, title))

    raise DisplayInvariantError("mode must be bin|model|best|binall")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trig", required=True)
    parser.add_argument("--dets", default="na,nb,b1")
    parser.add_argument("--ref", default="na")
    parser.add_argument(
        "--mode", default="best", choices=["bin", "model", "best", "binall"]
    )
    parser.add_argument("--bin", dest="which", default=None)
    parser.add_argument("--model", dest="model", default=None)
    parser.add_argument(
        "--rebin",
        nargs=2,
        type=float,
        default=[REBIN_SIG, REBIN_MAX],
        metavar=("SIG", "MAXCH"),
        help="pyXSPEC 'setplot rebin SIG MAXCH' (default 5 5)",
    )
    parser.add_argument("--out", default=str(ROOT / "results" / "figures"))
    args = parser.parse_args(argv)
    which = (
        args.which
        if args.mode in {"bin", "binall"}
        else (args.model if args.mode == "model" else None)
    )
    if args.mode in {"bin", "binall"} and which is None:
        parser.error(f"--mode {args.mode} requires --bin N|tint")
    if args.mode == "model" and which is None:
        parser.error("--mode model requires --model NAME")
    try:
        run(
            args.trig,
            args.dets.split(","),
            args.ref,
            args.mode,
            which,
            args.out,
            (float(args.rebin[0]), float(args.rebin[1])),
        )
    except DisplayInvariantError as exc:
        raise SystemExit(f"DISPLAY INVARIANT FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
