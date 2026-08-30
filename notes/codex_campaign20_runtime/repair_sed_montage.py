#!/usr/bin/env python3
"""Audit scripts/41e montages and repair only missing/incomplete products.

The prescribed order remains: run ``scripts/41e_sed_montage.py`` first, then
run this adapter.  41e assumes at least one panel and omits models whose AIC is
non-finite.  This campaign-owned fallback guarantees one explicitly labeled
cell for every canonical model without fitting or inventing scientific data.

Validated 41c panels are composited as-is.  Missing triplets and engine fit
failures are gray placeholders.  All fallback products remain UNGATED pending
independent Claude figure verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import textwrap
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from run_sed_sweep import (
    REPO,
    Contract,
    Validation,
    _png_ok,
    default_grid,
    failure_class,
    load_contract,
    scan_grid,
    tag_for,
)


COLS = 4
CELL_W = 560
PANEL_H = 410
CAP_H = 92
TITLE_H = 112
PAD = 10
RED = (190, 42, 42)
GRAY = (242, 242, 242)
MID_GRAY = (125, 125, 125)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_closure(contract: Contract, grid: Path) -> dict:
    """Require a final P3 closure bound to the same canonical authorities."""
    summary_path = grid / "sweep_summary.json"
    status_path = grid / "sweep_status.txt"
    if not summary_path.is_file() or not status_path.is_file():
        raise RuntimeError("final P3 sweep_summary.json/sweep_status.txt is missing")
    try:
        summary = json.loads(summary_path.read_text())
    except Exception as exc:
        raise RuntimeError(f"final P3 closure is unreadable: {exc}") from exc
    checks = (
        summary.get("trigger") == contract.trig,
        summary.get("canonical_fit_sha256") == contract.fit_sha256,
        summary.get("canonical_fit_metadata_sha256") == contract.metadata_sha256,
        summary.get("adopted_blocks_sha256") == contract.blocks_sha256,
        summary.get("models") == list(contract.models),
        summary.get("bins") == list(contract.bins),
        summary.get("pairs") == len(contract.pairs),
        summary.get("attempt_snapshot") is None,
        summary.get("persistent_failure_attempt_evidence_complete") is True,
        summary.get("persistent_failure_attempt_evidence_gaps") == [],
    )
    if not all(checks):
        raise RuntimeError("final P3 closure is stale or incomplete")
    return {
        "summary_path": summary_path,
        "summary_sha256": _sha256(summary_path),
        "status_path": status_path,
        "status_sha256": _sha256(status_path),
    }


def _font(size: int):
    candidates = (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "1.0"}


def _model_order(contract: Contract, bin_arg: str) -> list[str]:
    """All 24: finite AIC ascending, then non-finite in registry-column order."""
    row = contract.row_for_bin[bin_arg]
    registry_index = {model: index for index, model in enumerate(contract.models)}
    return sorted(
        contract.models,
        key=lambda model: (
            0 if _finite(row[f"{model}_AIC"]) else 1,
            float(row[f"{model}_AIC"])
            if _finite(row[f"{model}_AIC"]) else float("inf"),
            registry_index[model],
        ),
    )


def _fit_status(contract: Contract, bin_arg: str, model: str) -> str:
    column = f"{model}_STATUS"
    if column not in contract.table.colnames:
        return "UNKNOWN"
    return str(contract.row_for_bin[bin_arg][column]).strip().upper()


def _fit_valid(contract: Contract, bin_arg: str, model: str) -> bool | None:
    column = f"{model}_VALID"
    if column not in contract.table.colnames:
        return None
    return _truthy(contract.row_for_bin[bin_arg][column])


def _expected_state(contract: Contract, bin_arg: str,
                    validations: dict[tuple[str, str], Validation]) -> dict:
    order = _model_order(contract, bin_arg)
    row = contract.row_for_bin[bin_arg]
    finite_aics = [float(row[f"{model}_AIC"]) for model in order
                   if _finite(row[f"{model}_AIC"])]
    raw_winner = order[0] if finite_aics else None
    cells = []
    for rank, model in enumerate(order, start=1):
        result = validations[(bin_arg, model)]
        status = _fit_status(contract, bin_arg, model)
        aic = (float(row[f"{model}_AIC"])
               if _finite(row[f"{model}_AIC"]) else None)
        # A literal fit failure is always displayed as a placeholder even if a
        # stale-looking but numerically matching triplet happens to exist.
        render_panel = bool(result.ok and status == "OK")
        if status != "OK":
            placeholder_reason = f"ENGINE FIT FAILURE: STATUS={status}"
        elif not result.ok:
            placeholder_reason = result.reason
        else:
            placeholder_reason = None
        state_class = (None if result.ok else
                       failure_class(contract, (bin_arg, model), result))
        cells.append({
            "rank": rank,
            "model": model,
            "aic": aic,
            "delta_aic": (aic - finite_aics[0]
                          if aic is not None and finite_aics else None),
            "fit_status": status,
            "fit_valid": _fit_valid(contract, bin_arg, model),
            "triplet_valid": bool(result.ok),
            "triplet_sidecar": str(result.sidecar) if result.sidecar else None,
            "rendering": "validated_41c_panel" if render_panel else "placeholder",
            "failure_class": state_class,
            "placeholder_reason": placeholder_reason,
        })
    return {
        "order": order,
        "raw_finite_aic_winner": raw_winner,
        "cells": cells,
        "n_missing": sum(not validations[(bin_arg, model)].ok for model in order),
        "n_valid_triplets": sum(validations[(bin_arg, model)].ok for model in order),
        "n_fit_failures": sum(_fit_status(contract, bin_arg, model) != "OK"
                              for model in order),
        "n_placeholders": sum(cell["rendering"] == "placeholder" for cell in cells),
    }


def _audit_existing(png: Path, sidecar: Path, expected: dict,
                    tag: str, contract: Contract, bin_arg: str,
                    grid: Path) -> tuple[bool, list[str]]:
    reasons = []
    if not _png_ok(png):
        reasons.append("montage PNG missing or invalid")
    try:
        data = json.loads(sidecar.read_text())
    except Exception as exc:
        reasons.append(f"montage sidecar missing or unreadable: {type(exc).__name__}")
        return False, reasons
    if data.get("tag") != tag:
        reasons.append(f"sidecar tag {data.get('tag')!r} != {tag!r}")
    row = contract.row_for_bin[bin_arg]
    expected_interval = [float(row["T_START"]), float(row["T_STOP"])]
    try:
        interval = [float(value) for value in data.get("interval_s", [])]
    except Exception:
        interval = []
    if (len(interval) != 2
            or any(abs(left - right) > 1.0e-8
                   for left, right in zip(interval, expected_interval))):
        reasons.append(f"sidecar interval {interval} != {expected_interval}")
    order = data.get("order")
    if not isinstance(order, list) or len(order) != 24:
        reasons.append(f"len(order)={len(order) if isinstance(order, list) else 'invalid'} != 24")
    elif order != expected["order"]:
        reasons.append("sidecar order does not match finite-first canonical order")
    if data.get("n_panels") != 24:
        reasons.append(f"n_panels={data.get('n_panels')!r} != 24")
    if data.get("n_missing") != expected["n_missing"]:
        reasons.append(
            f"n_missing={data.get('n_missing')!r} != independently counted "
            f"{expected['n_missing']}"
        )
    script = data.get("script")
    if script == "41e_sed_montage.py":
        expected_script_sha = _sha256(REPO / "scripts" / "41e_sed_montage.py")
        if data.get("script_sha256") != expected_script_sha:
            reasons.append("native 41e script hash is stale")
        if expected["n_missing"]:
            reasons.append(
                "native montage has missing panels; classified refusal cells require fallback")
    elif script == "notes/codex_campaign20_runtime/repair_sed_montage.py":
        if data.get("script_sha256") != _sha256(Path(__file__)):
            reasons.append("fallback script hash is stale")
        if data.get("canonical_fit_sha256") != contract.fit_sha256:
            reasons.append("fallback canonical-fit hash is stale")
        if data.get("trigger") != contract.trig or data.get("bin") != bin_arg:
            reasons.append("fallback trigger/bin identity is stale")
        path_bindings = (
            ("canonical_fit_table", contract.fit_path),
            ("canonical_fit_metadata", contract.metadata_path),
            ("adopted_blocks", contract.blocks_path),
            ("p3_closure", grid / "sweep_summary.json"),
            ("p3_status", grid / "sweep_status.txt"),
        )
        for key, expected_path in path_bindings:
            raw_path = Path(str(data.get(key, "")))
            observed_path = (raw_path.resolve() if raw_path.is_absolute()
                             else (REPO / raw_path).resolve())
            if observed_path != expected_path.resolve():
                reasons.append(f"fallback {key} path is stale")
        bindings = (
            ("canonical_fit_metadata_sha256", contract.metadata_sha256),
            ("adopted_blocks_sha256", contract.blocks_sha256),
            ("p3_closure_sha256", _sha256(grid / "sweep_summary.json")
             if (grid / "sweep_summary.json").is_file() else None),
            ("p3_status_sha256", _sha256(grid / "sweep_status.txt")
             if (grid / "sweep_status.txt").is_file() else None),
        )
        for key, expected_hash in bindings:
            if expected_hash is None or data.get(key) != expected_hash:
                reasons.append(f"fallback {key} is stale")
        count_bindings = (
            ("order_length", 24),
            ("n_valid_triplets", expected["n_valid_triplets"]),
            ("n_fit_failures", expected["n_fit_failures"]),
            ("n_fit_failure_placeholders", expected["n_fit_failures"]),
            ("n_placeholders", expected["n_placeholders"]),
        )
        for key, expected_value in count_bindings:
            if data.get(key) != expected_value:
                reasons.append(f"fallback {key} differs from current closure")
        cells = data.get("cells")
        if not isinstance(cells, list) or len(cells) != 24:
            reasons.append("fallback does not enumerate exactly 24 cells")
        else:
            keys = ("rank", "model", "aic", "delta_aic", "fit_status",
                    "fit_valid", "triplet_valid", "triplet_sidecar",
                    "rendering", "failure_class", "placeholder_reason")
            for observed, required in zip(cells, expected["cells"]):
                if not isinstance(observed, dict):
                    reasons.append("fallback contains a malformed cell")
                    break
                mismatch = False
                for key in keys:
                    left, right = observed.get(key), required.get(key)
                    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                        if abs(float(left) - float(right)) > 1.0e-8:
                            mismatch = True
                            break
                    elif left != right:
                        mismatch = True
                        break
                if mismatch:
                    reasons.append(
                        f"fallback cell {required['model']} differs from current closure")
                    break
    else:
        reasons.append(f"unknown montage producer {script!r}")

    # P4 is prescribed after the final P3 closure.  Requiring the montage to
    # postdate that closure prevents a failed 41e call from silently reusing a
    # montage left by an earlier fit/sweep.
    closure = grid / "sweep_summary.json"
    if not closure.is_file():
        reasons.append("final P3 sweep_summary.json is missing")
    elif png.is_file() and sidecar.is_file():
        closure_mtime = closure.stat().st_mtime_ns
        if min(png.stat().st_mtime_ns, sidecar.stat().st_mtime_ns) < closure_mtime:
            reasons.append("montage predates the final P3 closure")

    finite_aics = {
        model: float(row[f"{model}_AIC"])
        for model in contract.models if _finite(row[f"{model}_AIC"])
    }
    winner = min(finite_aics, key=finite_aics.get) if finite_aics else None
    if data.get("raw_finite_aic_winner", data.get("winner")) != winner:
        reasons.append("montage winner is stale")
    if script == "41e_sed_montage.py" and finite_aics:
        expected_daic = {model: value - finite_aics[winner]
                         for model, value in finite_aics.items()}
        daic = data.get("daic")
        if not isinstance(daic, dict) or set(daic) != set(expected_daic):
            reasons.append("native montage dAIC keys are stale")
        elif any(abs(float(daic[model]) - value) > 1.0e-8
                 for model, value in expected_daic.items()):
            reasons.append("native montage dAIC values are stale")
    if (expected["n_fit_failures"]
            and data.get("n_fit_failure_placeholders") != expected["n_fit_failures"]):
        reasons.append("fit failures are not represented by explicit placeholders")
    return not reasons, reasons


def _fit_text(draw: ImageDraw.ImageDraw, center: tuple[int, int], text: str,
              font, width: int = 44, max_lines: int = 7) -> None:
    lines = textwrap.wrap(str(text), width=width) or [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max(1, width - 3)] + "..."
    draw.multiline_text(center, "\n".join(lines), font=font, fill=MID_GRAY,
                        anchor="mm", align="center", spacing=6)


def _render_fallback(contract: Contract, bin_arg: str, expected: dict,
                     png: Path, sidecar: Path, repair_reasons: list[str],
                     closure: dict) -> dict:
    row = contract.row_for_bin[bin_arg]
    tag = tag_for(bin_arg)
    rows_n = math.ceil(24 / COLS)
    width = COLS * (CELL_W + PAD) + PAD
    height = TITLE_H + rows_n * (PANEL_H + CAP_H + PAD) + PAD
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = _font(32)
    cap_font = _font(20)
    small_font = _font(17)
    placeholder_font = _font(24)
    draw.text(
        (PAD + 4, 15),
        f"{contract.trig} — {tag} [{float(row['T_START']):.2f}, "
        f"{float(row['T_STOP']):.2f}] s — FALLBACK STATUS MONTAGE",
        fill="black", font=title_font,
    )
    draw.text(
        (PAD + 4, 61),
        f"24 canonical models | {expected['n_valid_triplets']} validated triplets | "
        f"{expected['n_missing']} missing | UNGATED",
        fill=(80, 80, 80), font=small_font,
    )

    for index, cell in enumerate(expected["cells"]):
        grid_row, grid_col = divmod(index, COLS)
        x = PAD + grid_col * (CELL_W + PAD)
        y = TITLE_H + grid_row * (PANEL_H + CAP_H + PAD)
        draw.rectangle((x, y, x + CELL_W, y + PANEL_H), fill=GRAY,
                       outline=(180, 180, 180), width=2)
        if cell["rendering"] == "validated_41c_panel":
            panel_path = Path(cell["triplet_sidecar"]).with_suffix(".png")
            with Image.open(panel_path) as source:
                panel = ImageOps.contain(source.convert("RGB"),
                                         (CELL_W, PANEL_H), Image.Resampling.LANCZOS)
            px = x + (CELL_W - panel.width) // 2
            py = y + (PANEL_H - panel.height) // 2
            canvas.paste(panel, (px, py))
        else:
            if cell["fit_status"] != "OK":
                label = "FIT FAILURE"
            elif str(cell.get("failure_class", "")).startswith("STRUCTURAL"):
                label = "STRUCTURAL REFUSAL"
            elif cell.get("failure_class") == "STALE_ARTIFACT":
                label = "STALE PANEL REFUSED"
            else:
                label = "PANEL UNAVAILABLE"
            reason = cell["placeholder_reason"] or "No validated 41c triplet"
            _fit_text(draw, (x + CELL_W // 2, y + PANEL_H // 2),
                      f"{label}\n\n{reason}", placeholder_font)

        aic_text = (f"AIC={cell['aic']:.2f}, dAIC={cell['delta_aic']:.2f}"
                    if cell["aic"] is not None else "AIC=non-finite")
        valid_text = ("VALID" if cell["fit_valid"] is True else
                      "INVALID" if cell["fit_valid"] is False else "VALID=?")
        caption = (f"#{cell['rank']} {cell['model']} | {aic_text}\n"
                   f"STATUS={cell['fit_status']} | {valid_text} | "
                   f"{cell['rendering']}")
        draw.multiline_text((x + 6, y + PANEL_H + 7), caption,
                            fill="black", font=cap_font, spacing=3)
        if cell["model"] == expected["raw_finite_aic_winner"]:
            for offset in range(4):
                draw.rectangle((x - offset, y - offset,
                                x + CELL_W + offset,
                                y + PANEL_H + CAP_H - 4 + offset),
                               outline=RED)

    png.parent.mkdir(parents=True, exist_ok=True)
    temporary_png = png.with_name(f".{png.name}.{os.getpid()}.tmp.png")
    canvas.save(temporary_png)
    os.replace(temporary_png, png)
    if not _png_ok(png):
        raise RuntimeError(f"fallback montage failed PNG verification: {png}")

    payload = {
        "script": "notes/codex_campaign20_runtime/repair_sed_montage.py",
        "script_sha256": _sha256(Path(__file__)),
        "trigger": contract.trig,
        "tag": tag,
        "bin": bin_arg,
        "interval_s": [float(row["T_START"]), float(row["T_STOP"])],
        "repair_after_41e_attempt": True,
        "repair_reasons": repair_reasons,
        "fallback_status_montage": True,
        "scientific_refit": False,
        "compositing_only": True,
        "order": expected["order"],
        "order_length": len(expected["order"]),
        "n_panels": 24,
        "n_missing": expected["n_missing"],
        "n_valid_triplets": expected["n_valid_triplets"],
        "n_fit_failures": expected["n_fit_failures"],
        "n_fit_failure_placeholders": expected["n_fit_failures"],
        "n_placeholders": expected["n_placeholders"],
        "raw_finite_aic_winner": expected["raw_finite_aic_winner"],
        "cells": expected["cells"],
        "canonical_fit_table": str(contract.fit_path),
        "canonical_fit_sha256": _sha256(contract.fit_path),
        "canonical_fit_metadata": str(contract.metadata_path),
        "canonical_fit_metadata_sha256": contract.metadata_sha256,
        "adopted_blocks": str(contract.blocks_path),
        "adopted_blocks_sha256": contract.blocks_sha256,
        "p3_closure": str(closure["summary_path"]),
        "p3_closure_sha256": closure["summary_sha256"],
        "p3_status": str(closure["status_path"]),
        "p3_status_sha256": closure["status_sha256"],
        "visual_verdict": "UNGATED — independent Claude figure verification pending",
        "provisional": True,
        "generated_utc": _utc_now(),
    }
    temporary_json = sidecar.with_name(f".{sidecar.name}.{os.getpid()}.tmp")
    temporary_json.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary_json, sidecar)
    return payload


def _quarantine_existing(png: Path, sidecar: Path, montage_dir: Path,
                         tag: str) -> list[dict[str, str]]:
    existing = [path for path in (png, sidecar) if path.exists()]
    if not existing:
        return []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = montage_dir / "quarantine" / f"{tag}_{stamp}"
    destination.mkdir(parents=True, exist_ok=True)
    moved = []
    for source in existing:
        target = destination / source.name
        if target.exists():
            raise RuntimeError(f"montage quarantine collision: {target}")
        source_hash = _sha256(source)
        source.replace(target)
        moved.append({"path": str(target), "sha256": source_hash})
    return moved


def repair_montages(trig: str, grid: Path | None = None,
                     montage_dir: Path | None = None,
                     fit_table: Path | None = None) -> dict:
    contract = load_contract(trig, fit_table)
    grid = grid or default_grid(trig)
    montage_dir = montage_dir or (grid / "montage")
    closure = _load_closure(contract, grid)
    validations = scan_grid(contract, grid)
    decisions = []
    for bin_arg in contract.bins:
        tag = tag_for(bin_arg)
        stem = montage_dir / f"{trig}_montage_{tag}"
        png = stem.with_suffix(".png")
        sidecar = stem.with_suffix(".json")
        expected = _expected_state(contract, bin_arg, validations)
        complete, reasons = _audit_existing(
            png, sidecar, expected, tag, contract, bin_arg, grid)
        if complete:
            decisions.append({
                "tag": tag,
                "action": "PRESERVED_COMPLETE_41E_OR_FALLBACK",
                "png": str(png),
                "sidecar": str(sidecar),
                "n_missing": expected["n_missing"],
            })
            continue
        moved = _quarantine_existing(png, sidecar, montage_dir, tag)
        payload = _render_fallback(
            contract, bin_arg, expected, png, sidecar, reasons, closure)
        assert len(payload["order"]) == payload["n_panels"] == 24
        assert payload["n_missing"] == sum(
            not validations[(bin_arg, model)].ok for model in contract.models)
        decisions.append({
            "tag": tag,
            "action": "REPAIRED_WITH_FALLBACK",
            "repair_reasons": reasons,
            "quarantined": moved,
            "png": str(png),
            "sidecar": str(sidecar),
            "n_missing": payload["n_missing"],
            "n_fit_failures": payload["n_fit_failures"],
        })

    audit = {
        "script": "notes/codex_campaign20_runtime/repair_sed_montage.py",
        "script_sha256": _sha256(Path(__file__)),
        "trigger": trig,
        "prescribed_41e_must_run_first": True,
        "canonical_fit_table": str(contract.fit_path),
        "canonical_fit_sha256": contract.fit_sha256,
        "canonical_fit_metadata": str(contract.metadata_path),
        "canonical_fit_metadata_sha256": contract.metadata_sha256,
        "adopted_blocks": str(contract.blocks_path),
        "adopted_blocks_sha256": contract.blocks_sha256,
        "p3_closure": str(closure["summary_path"]),
        "p3_closure_sha256": closure["summary_sha256"],
        "p3_status": str(closure["status_path"]),
        "p3_status_sha256": closure["status_sha256"],
        "grid": str(grid),
        "montage_dir": str(montage_dir),
        "bins": list(contract.bins),
        "models": list(contract.models),
        "n_models": len(contract.models),
        "repaired": sum(item["action"] == "REPAIRED_WITH_FALLBACK"
                        for item in decisions),
        "preserved": sum(item["action"].startswith("PRESERVED")
                         for item in decisions),
        "decisions": decisions,
        "visual_verdict": "UNGATED — independent Claude figure verification pending",
        "provisional": True,
        "generated_utc": _utc_now(),
    }
    montage_dir.mkdir(parents=True, exist_ok=True)
    audit_path = montage_dir / "fallback_montage_audit.json"
    temporary = audit_path.with_name(f".{audit_path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(audit, indent=2) + "\n")
    os.replace(temporary, audit_path)
    audit["audit_path"] = str(audit_path)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trig", required=True)
    parser.add_argument("--grid", type=Path)
    parser.add_argument("--montage-dir", type=Path)
    parser.add_argument("--fit-table", type=Path,
                        help="test/diagnostic override; campaign default is canonical convention_check")
    args = parser.parse_args()
    result = repair_montages(args.trig, args.grid, args.montage_dir,
                             args.fit_table)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
