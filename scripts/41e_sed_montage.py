#!/usr/bin/env python
"""scripts/41e_sed_montage.py — per-bin montage of ALL model SEDs in one figure
(Vikas, 2026-08-15: "make a montage in a single figure all the 24 models for a
bin and mark the best fit there as we did in LATBright").

Pure compositing of the ALREADY-RENDERED, guard-passed 41c PNGs — no refits, no
re-plotting. Panels are AIC-ORDERED (winner top-left, red frame + WINNER tag);
every refused (model, bin) pair gets a labeled placeholder cell so absence is
visible, never silent. Per-cell caption: rank, model, dAIC to winner, validity.
Provenance sidecar JSON per montage.

Light tier: python3 with PIL + astropy.
Usage: python3 scripts/41e_sed_montage.py [--tag bin4 ...]  (default: all bins)
"""
import os, re, sys, glob, json, hashlib, argparse
import numpy as np
from astropy.table import Table
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID = os.path.join(ROOT, "results", "convention_check", "sed_grid")
OUT = os.path.join(GRID, "montage")
TRIG = "bn081125496"

COLS, CELL_W = 5, 700
CAP_H, TITLE_H, PAD = 46, 84, 8
RED = (196, 45, 45)
GRAY_BG = (243, 243, 243)


def _font(size):
    for cand in (os.path.join(os.path.dirname(np.__file__), "..", "matplotlib",
                              "mpl-data", "fonts", "ttf", "DejaVuSans.ttf"),
                 "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(os.path.abspath(cand), size)
        except Exception:
            continue
    return ImageFont.load_default()


def canon(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="*", default=None)
    a = ap.parse_args()

    t = Table.read(os.path.join(ROOT, "results", "convention_check", TRIG,
                                "spectral_fits.ecsv"))
    prefixes = sorted({c[:-4] for c in t.colnames if c.endswith("_AIC")})
    refusals = {}
    status = os.path.join(GRID, "sweep_status.txt")
    for line in open(status):
        if line.startswith("FAIL"):
            parts = line.split()
            refusals[(parts[1], parts[2])] = ("crash" if len(parts) < 4 or "live AIC"
                                              not in line else "guard")
    os.makedirs(OUT, exist_ok=True)
    f_cap = _font(22)
    f_small = _font(17)
    f_title = _font(34)
    with open(os.path.abspath(__file__), "rb") as fh:
        src_sha = hashlib.sha256(fh.read()).hexdigest()

    for row in t:
        blk = int(row["BLOCK"])
        tag = "TINT" if blk == -1 else f"bin{blk}"
        bin_arg = "tint" if blk == -1 else str(blk)
        if a.tags and tag not in a.tags:
            continue
        aics = {p: float(row[f"{p}_AIC"]) for p in prefixes
                if np.isfinite(row[f"{p}_AIC"])}
        order = sorted(aics, key=aics.get)
        win = order[0]
        figs = {canon(os.path.basename(f).rsplit("_", 1)[-1][:-4]): f
                for f in glob.glob(os.path.join(GRID, f"{TRIG}_SED_{tag}_*.png"))}
        # cell geometry from the first available panel's aspect
        sample = Image.open(next(iter(figs.values())))
        cell_h = int(CELL_W * sample.height / sample.width)
        rows_n = int(np.ceil(len(order) / COLS))
        W = COLS * (CELL_W + PAD) + PAD
        H = TITLE_H + rows_n * (cell_h + CAP_H + PAD) + PAD
        canvas = Image.new("RGB", (W, H), "white")
        dr = ImageDraw.Draw(canvas)
        dr.text((PAD + 4, 20),
                f"{TRIG} — {tag} [{row['T_START']:.2f}, {row['T_STOP']:.2f}] s — "
                f"{len(order)} models, AIC-ordered — winner {win}",
                fill="black", font=f_title)
        n_missing = 0
        for i, p in enumerate(order):
            r, c = divmod(i, COLS)
            x = PAD + c * (CELL_W + PAD)
            y = TITLE_H + r * (cell_h + CAP_H + PAD)
            valid = bool(row[f"{p}_VALID"]) if f"{p}_VALID" in t.colnames else True
            if p in figs:
                im = Image.open(figs[p]).convert("RGB").resize(
                    (CELL_W, cell_h), Image.LANCZOS)
                canvas.paste(im, (x, y))
            else:
                n_missing += 1
                dr.rectangle([x, y, x + CELL_W, y + cell_h], fill=GRAY_BG,
                             outline=(180, 180, 180), width=2)
                why = refusals.get((p, bin_arg), "?")
                msg = ("REFUSED (guard):\nlive fit did not reproduce\nthe stored solution"
                       if why == "guard" else
                       "UNAVAILABLE (crash):\nall native draws railed;\nfit sits in a bound corner")
                dr.multiline_text((x + CELL_W // 2, y + cell_h // 2), msg,
                                  fill=(120, 120, 120), font=f_cap, anchor="mm",
                                  align="center", spacing=6)
            cap = (f"#{i+1}  {p}  dAIC={aics[p]-aics[win]:.2f}"
                   + ("" if valid else "  [INVALID]"))
            dr.text((x + 6, y + cell_h + 8), cap, fill="black", font=f_cap)
            if p == win:
                for wpx in range(5):
                    dr.rectangle([x - wpx, y - wpx, x + CELL_W + wpx,
                                  y + cell_h + CAP_H - 6 + wpx], outline=RED)
                dr.text((x + CELL_W - 6, y + cell_h + 8), "WINNER", fill=RED,
                        font=f_cap, anchor="ra")
        dr.text((W - PAD - 4, TITLE_H - 26),
                f"panels = guard-passed 41c figures | {n_missing} refused cells labeled",
                fill=(90, 90, 90), font=f_small, anchor="ra")
        stem = os.path.join(OUT, f"{TRIG}_montage_{tag}")
        canvas.save(stem + ".png")
        prov = dict(script="41e_sed_montage.py", script_sha256=src_sha,
                    tag=tag, interval_s=[float(row["T_START"]), float(row["T_STOP"])],
                    winner=win, order=order,
                    daic={p: aics[p] - aics[win] for p in order},
                    n_panels=len(order), n_missing=n_missing,
                    compositing_only=True)
        with open(stem + ".json", "w") as fh:
            json.dump(prov, fh, indent=1)
        print("WROTE", stem + ".png")


if __name__ == "__main__":
    main()
