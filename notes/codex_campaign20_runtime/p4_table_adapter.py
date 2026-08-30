#!/usr/bin/env python3
"""Build campaign P4 tables in the saved burst-2 per-bin Markdown format.

``campaign_products.py`` is the frozen P1 merge/promote authority during this
campaign and cannot be edited without invalidating its recorded SHA.  Its table
mode is still invoked first, but its current formatter differs from the saved
``sed_grid_bn081222204/tables/*_params.md`` authority (notably AIC/error
precision and an extra prose footer).  This P4-only adapter rewrites only those
derived table products from the same canonical ECSV/JSON; it never changes a
fit, selection, script, catalog, or non-table product.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import campaign_products as base


REPO = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
SCHEMA = "codex_campaign20.p4_all_model_tables.v1"


def _path_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path.resolve())


def _finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "1.0"}


def _value(value: object) -> str:
    return f"{float(value):.4g}" if _finite(value) else "---"


def _error(value: object) -> str:
    return f"{abs(float(value)):.2g}" if _finite(value) else "---"


def _signed_error(value: object) -> str:
    if not _finite(value):
        return "---"
    number = float(value)
    rendered = f"{number:.2g}"
    return rendered if number < 0 else "+" + rendered


def _aic(value: object) -> str:
    return f"{float(value):.1f}" if _finite(value) else "---"


def _daic(value: object) -> str:
    return f"{float(value):.2f}" if _finite(value) else "---"


def _params(table, row, prefix: str) -> str:
    if str(row[f"{prefix}_STATUS"]).strip().upper() != "OK":
        return f"STATUS={row[f'{prefix}_STATUS']} (no accepted fitted solution)"
    columns = set(table.colnames)
    pieces: list[str] = []
    for suffix in base.parameter_bases(table, prefix):
        key = f"{prefix}_{suffix}"
        neg, pos, symmetric = key + "_NEG_ERR", key + "_POS_ERR", key + "_ERR"
        if neg in columns and pos in columns and _finite(row[neg]) and _finite(row[pos]):
            pieces.append(
                f"{suffix}={_value(row[key])} "
                f"{_signed_error(row[neg])}/{_signed_error(row[pos])}")
        elif symmetric in columns and _finite(row[symmetric]):
            pieces.append(f"{suffix}={_value(row[key])} ±{_error(row[symmetric])}")
        else:
            pieces.append(f"{suffix}={_value(row[key])}")
    lead = prefix + "_EAC_"
    for column in table.colnames:
        if column.startswith(lead) and not column.endswith("_ERR"):
            detector = column[len(lead):].lower()
            value = (f"{float(row[column]):.3f}"
                     if _finite(row[column]) else "---")
            pieces.append(f"EAC_{detector}={value}")
    return "; ".join(pieces) if pieces else "no stored parameters"


def table_text(table, row, prefixes: list[str]) -> str:
    block = int(row["BLOCK"])
    tag = "TINT" if block < 0 else f"bin{block}"
    winner = base.winner_prefix(row["BEST_AIC_MODEL"])
    finite_aics = [float(row[f"{prefix}_AIC"]) for prefix in prefixes
                   if _finite(row[f"{prefix}_AIC"])]
    minimum = min(finite_aics) if finite_aics else float("nan")
    registry_index = {prefix: index for index, prefix in enumerate(prefixes)}
    ordered = sorted(
        prefixes,
        key=lambda prefix: (
            0 if _finite(row[f"{prefix}_AIC"]) else 1,
            float(row[f"{prefix}_AIC"])
            if _finite(row[f"{prefix}_AIC"]) else float("inf"),
            registry_index[prefix],
        ),
    )
    lines = [
        f"# {tag}  [{float(row['T_START']):.2f}, {float(row['T_STOP']):.2f}] s "
        "— all 24 models (AIC-sorted)",
        "",
        "| model | AIC | dAIC | valid | parameters |",
        "|---|---|---|---|---|",
    ]
    for prefix in ordered:
        raw_aic = row[f"{prefix}_AIC"]
        delta = (float(raw_aic) - minimum
                 if _finite(raw_aic) and _finite(minimum) else float("nan"))
        valid = (
            str(row[f"{prefix}_STATUS"]).strip().upper() == "OK"
            and _truthy(row[f"{prefix}_VALID"])
            and _finite(raw_aic)
        )
        marker = " **(winner)**" if prefix == winner else ""
        lines.append(
            f"| {prefix}{marker} | {_aic(raw_aic)} | {_daic(delta)} | "
            f"{'yes' if valid else 'NO'} | {_params(table, row, prefix)} |")
    if len(ordered) != 24 or sum(" **(winner)**" in line for line in lines) != 1:
        raise RuntimeError("table does not contain the exact 24-model/one-winner closure")
    return "\n".join(lines) + "\n"


def _quarantine_stale(out: Path, expected: set[str]) -> list[dict[str, str]]:
    stale = sorted(
        path for path in out.glob("*_params.md")
        if re.fullmatch(r"(?:TINT|bin[0-9]+)_params\.md", path.name)
        and path.name not in expected
    )
    if not stale:
        return []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = out / "quarantine" / f"stale_tables_{stamp}"
    destination.mkdir(parents=True, exist_ok=False)
    records = []
    for source in stale:
        target = destination / source.name
        digest = base.sha256(source)
        source.replace(target)
        records.append({"path": str(target), "sha256": digest})
    return records


def build(trig: str, fit_root: Path) -> dict:
    fit_root = fit_root.resolve()
    # Preserve the inventory-first extension path: the existing table producer
    # runs, then this adapter normalizes only its presentation layer.
    base.make_tables(trig, fit_root=fit_root)
    table, metadata, ecsv, metadata_path = base.load_fit(trig, fit_root)
    found = base.model_prefixes(table)
    if len(found) != 24 or set(found) != set(base.HIGHE_PREFIXES):
        raise RuntimeError(f"{trig}: table does not contain the exact engine 24 models")
    # The current campaign P1 table already uses this order.  Reassert it here
    # so exact-AIC ties never inherit a historical column-merge order.
    prefixes = list(base.HIGHE_PREFIXES)
    if metadata.get("trigger") != trig:
        raise RuntimeError(f"{trig}: canonical metadata trigger mismatch")
    blocks = sorted(int(value) for value in table["BLOCK"])
    if blocks != [-1] + list(range(int(metadata["n_blocks"]))):
        raise RuntimeError(f"{trig}: canonical table block closure is incomplete")

    out = fit_root / f"sed_grid_{trig}" / "tables"
    expected_names = {
        "TINT_params.md" if int(row["BLOCK"]) < 0
        else f"bin{int(row['BLOCK'])}_params.md"
        for row in table
    }
    quarantined = _quarantine_stale(out, expected_names)
    products = []
    texts = []
    for row in sorted(table, key=lambda value: int(value["BLOCK"])):
        block = int(row["BLOCK"])
        name = "TINT_params.md" if block < 0 else f"bin{block}_params.md"
        text = table_text(table, row, prefixes)
        path = out / name
        base._atomic_write_text(path, text)
        products.append({
            "file": name,
            "block": block,
            "interval_s": [float(row["T_START"]), float(row["T_STOP"])],
            "sha256": base.sha256(path),
            "rows": 24,
            "winner": base.winner_prefix(row["BEST_AIC_MODEL"]),
        })
        texts.append(text)

    combined = out / "ALL_MODELS_TABLES.md"
    combined_text = (
        f"# {trig} — all models, all bins (campaign-20 P4; provisional)\n\n"
        + "\n".join(texts)
    )
    base._atomic_write_text(combined, combined_text)
    manifest = {
        "schema_version": SCHEMA,
        "script": _path_label(SCRIPT),
        "script_sha256": base.sha256(SCRIPT),
        "base_formatter": str((SCRIPT.parent / "campaign_products.py").relative_to(REPO)),
        "base_formatter_sha256": base.sha256(SCRIPT.parent / "campaign_products.py"),
        "trigger": trig,
        "source": _path_label(ecsv),
        "source_sha256": base.sha256(ecsv),
        "source_metadata": _path_label(metadata_path),
        "source_metadata_sha256": base.sha256(metadata_path),
        "n_models": 24,
        "n_spectra": len(table),
        "products": products,
        "combined": combined.name,
        "combined_sha256": base.sha256(combined),
        "quarantined_stale_tables": quarantined,
        "provisional": True,
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    manifest_path = out / "tables_manifest.json"
    base._atomic_write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trig", required=True)
    parser.add_argument("--fit-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.trig, args.fit_root), indent=2))


if __name__ == "__main__":
    main()
