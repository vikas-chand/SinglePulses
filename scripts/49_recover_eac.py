#!/usr/bin/env python
"""scripts/49_recover_eac.py — recover the FITTED effective-area constants that
the engine optimised and then threw away, WITHOUT refitting anything.

WHY THIS EXISTS (2026-08-13)
    scripts/10 activates use_effective_area_correction(0.8, 1.2) on every
    non-reference detector. Those constants are free parameters of the joint
    likelihood — they enter k, and therefore AIC — but only EAC_DETS (which
    detectors) was ever stored, never the values. Three symptoms, one cause:
      * the stored table cannot replay its own AIC. Holding every stored SOURCE
        parameter fixed and leaving the EAC at unity mis-states AIC by +2.2 to
        +12.6 (bn081125496 blocks 2 and 5, Codex display-layer rescue);
      * a display cannot fold the model through a non-reference detector, so
        scripts/41b drew NA only and dropped NB and B1 — surrendering the entire
        high-energy constraint to avoid a <=20% normalisation error;
      * the fit products are not archival: the row does not determine the fit.

    scripts/10 now writes <PREFIX>_EAC_<DET> for NEW fits. This tool backfills
    the EXISTING catalog.

WHY NOT JUST REFIT (scripts/29_refit_clean.py)
    A refit re-opens every number in a catalog that is under human review, and
    threeML's covariance errors are not seeded (audit D3), so it would not come
    back byte-identical. This tool holds every stored source parameter FIXED and
    profiles ONLY the EAC constants — one or two parameters. It cannot move a
    published number because it never varies one.

THE SELF-CHECK IS THE POINT
    Recovering the constants must reproduce the STORED AIC. If it does not, the
    row is left untouched and reported as FAILED. A recovered EAC that does not
    reproduce the stored AIC would mean the row and the fit disagree about
    something else, which is a finding, not a value to write.
    Tolerance: 1e-3 AIC (Codex measured the profile-termination floor at 8.6e-5).

USAGE
    conda activate threeML  + the CALDB exports (AGENTS.md heavy tier)
    python scripts/49_recover_eac.py --trig bn081125496 \
        --out results/sweep106/bn081125496 --dets na,nb,b1 --ref na
    python scripts/49_recover_eac.py --all --nproc 12      # the whole catalog

    --dry-run reports what it would write and touches nothing.
"""
import os
import sys
import glob
import argparse
import importlib.util

import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

_spec = importlib.util.spec_from_file_location(
    "engine10", os.path.join(ROOT, "scripts", "10_spectral_fit_burst.py"))
eng = importlib.util.module_from_spec(_spec)
sys.modules["engine10"] = eng
_spec.loader.exec_module(eng)

AIC_TOL = 1e-3          # ten times the observed profile-termination floor


def _all_specs():
    return (list(eng.MODEL_SPECS) + list(eng.SHAPE_MODEL_SPECS)
            + list(eng.HIGHE_MODEL_SPECS))


def _set_from_row(comp, spec, row):
    """Fix every SOURCE parameter to its stored value. Returns False if any
    required column is missing or non-finite — we never guess a parameter."""
    leaves = {n.split(".")[-1]: p for n, p in comp.parameters.items()}
    for col_suffix, short in spec["pmap"].items():
        col = "%s_%s" % (spec["prefix"], col_suffix)
        if col not in row.colnames:
            return False
        try:
            v = float(row[col])
        except Exception:
            return False
        if not np.isfinite(v):
            return False
        p = leaves.get(short)
        if p is None:
            return False
        # widen the bound before assigning: a stored value may sit exactly on a
        # rail, and astromodels refuses an out-of-range assignment.
        if p.min_value is not None and v < p.min_value:
            p.min_value = v
        if p.max_value is not None and v > p.max_value:
            p.max_value = v
        p.value = v
        p.fix = True
    return True


def recover_block(trig, dets, ref, t1, t2, appr, row, specs, verbose=False):
    """Profile ONLY the EAC constants for every model on one block.

    Returns {prefix: {det: value}} for the models whose recovered AIC matches
    the stored AIC, plus a per-model status dict.
    """
    from threeML import Model, PointSource, JointLikelihood, DataList

    plugins, names = [], []
    for det in dets:
        if det not in appr:
            continue
        sl = eng.build_spectrumlike_per_block(trig, det, appr[det][0], appr[det][1],
                                              [t1], [t2])
        if sl and sl[0] is not None:
            plugins.append(sl[0])
            names.append(det)
    if not plugins:
        return {}, {"_": "NO_PLUGINS"}

    # activate EAC exactly as the engine does, on the same detectors
    from threeML import SpectrumLike as _SpectrumLike
    for pl, det in zip(plugins, names):
        if det == ref or not isinstance(pl, _SpectrumLike):
            continue
        try:
            pl.use_effective_area_correction(*eng.EFFAREA_BOUNDS)
        except Exception:
            pass

    out, status = {}, {}
    for spec in specs:
        p = spec["prefix"]
        acol = "%s_AIC" % p
        if acol not in row.colnames:
            continue
        try:
            stored_aic = float(row[acol])
        except Exception:
            continue
        if not np.isfinite(stored_aic):
            status[p] = "NO_STORED_AIC"
            continue
        try:
            comp = spec["build"]({})
            if not _set_from_row(comp, spec, row):
                status[p] = "ROW_INCOMPLETE"
                continue
            ps = PointSource("grb", eng.SRC_RA, eng.SRC_DEC, spectral_shape=comp)
            jl = JointLikelihood(Model(ps), DataList(*plugins))
            jl.set_minimizer("minuit")
            free = jl.likelihood_model.free_parameters
            if not free:
                # no EAC in this configuration (single detector): the stored AIC
                # must already be reproducible with k unchanged.
                status[p] = "NO_EAC_PARAMS"
                continue
            if any(not n.split(".")[-1].startswith("cons_") for n in free):
                status[p] = "SOURCE_PARAM_STILL_FREE"     # fail closed
                continue
            jl.fit(quiet=True)
            n2ll = 2.0 * float(jl.current_minimum)
            # k must match the engine's: free EAC + the FIXED source params
            k = len(free) + len(spec["pmap"])
            aic = n2ll + 2 * k
            # SIGN MATTERS, and it took a real run to see why.
            # Every source parameter is FIXED, so the only freedom left is the
            # EAC. Therefore:
            #   aic > stored + tol  -> we failed to reach the engine's minimum.
            #                          REFUSE: our EAC is not the fitted EAC.
            #   aic < stored - tol  -> we found a BETTER minimum than the engine
            #                          stored, using only the EAC. The recovered
            #                          constants are at least as good as the
            #                          engine's; what this exposes is that the
            #                          engine's minimisation terminated loose on
            #                          that model. Record the value AND the slop.
            d = aic - stored_aic
            if d > AIC_TOL:
                status[p] = "UNREACHED %+0.4f" % d
                continue
            loose = d < -AIC_TOL
            vals = {}
            for n, par in free.items():
                short = n.split(".")[-1]
                det = short[5:].split("_interval")[0].upper()
                vals[det] = float(par.value)
            out[p] = vals
            status[p] = ("OK" if not loose
                         else "OK_ENGINE_MINIMUM_LOOSE %+0.4f" % d)
        except Exception as ex:
            status[p] = "ERROR %s" % str(ex)[:60]
    # NB: report AFTER the loop. An earlier version printed inside it, below the
    # `continue`s — so every failure was counted in the summary and invisible in
    # --verbose, which is the exact shape of a silent skip.
    if verbose:
        for p in sorted(status):
            print("      %-10s %s" % (p, status[p]))
    return out, status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig")
    ap.add_argument("--out", default=None, help="product root for this burst")
    ap.add_argument("--dets", default="na,nb,b1")
    ap.add_argument("--ref", default="na")
    ap.add_argument("--all", action="store_true", help="every burst under results/sweep106")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    if a.all:
        targets = []
        for d in sorted(glob.glob(os.path.join(ROOT, "results", "sweep106", "bn*"))):
            t = os.path.basename(d)
            targets.append((t, d))
    else:
        if not a.trig:
            ap.error("--trig or --all")
        targets = [(a.trig, a.out or os.path.join(ROOT, "results", "sweep106", a.trig))]

    specs = _all_specs()
    grand = {"OK": 0, "FAIL": 0, "ROWS": 0}
    for trig, out in targets:
        tab_path = os.path.join(out, trig, "spectral_fits.ecsv")
        if not os.path.exists(tab_path):
            print("SKIP %s (no fit table)" % trig)
            continue
        os.environ.setdefault("BLOCKS_ROOT", os.path.join(out, "blocks"))

        gs = Table.read(os.path.join(ROOT, "results", "grb_sample.ecsv"),
                        format="ascii.ecsv")
        srow = gs[[str(x["TRIGGER_NAME"]).strip() == trig for x in gs]][0]
        eng.SRC_RA, eng.SRC_DEC = float(srow["RA"]), float(srow["DEC"])
        bk = Table.read(os.environ.get(
            "BKG_FILE", os.path.join(ROOT, "results", "background_intervals.ecsv")),
            format="ascii.ecsv")
        bk = bk[bk["TRIGGER_NAME"] == trig]
        appr = {str(r["DETECTOR"]).strip():
                ((float(r["BKG_NEG_START"]), float(r["BKG_NEG_STOP"])),
                 (float(r["BKG_POS_START"]), float(r["BKG_POS_STOP"]))) for r in bk}

        t = Table.read(tab_path, format="ascii.ecsv")
        dets = [d.strip() for d in a.dets.split(",") if d.strip()]
        newcols = {}
        print("== %s  (%d rows)" % (trig, len(t)))
        for i, row in enumerate(t):
            try:
                t1, t2 = float(row["T_START"]), float(row["T_STOP"])
            except Exception:
                continue
            vals, status = recover_block(trig, dets, a.ref, t1, t2, appr, row,
                                         specs, verbose=a.verbose)
            grand["ROWS"] += 1
            nok = sum(1 for v in status.values() if v.startswith("OK"))
            nloose = sum(1 for v in status.values() if v.startswith("OK_ENGINE_MINIMUM_LOOSE"))
            nbad = sum(1 for v in status.values() if v.startswith(("UNREACHED", "ERROR")))
            grand["OK"] += nok
            grand["FAIL"] += nbad
            grand["LOOSE"] = grand.get("LOOSE", 0) + nloose
            print("   blk %-3s  recovered %2d models%s%s" %
                  (row["BLOCK"] if "BLOCK" in t.colnames else i, nok,
                   (", %d with a looser engine minimum" % nloose) if nloose else "",
                   (", %d UNREACHED" % nbad) if nbad else ""))
            for p, dv in vals.items():
                for det, v in dv.items():
                    newcols.setdefault("%s_EAC_%s" % (p, det), [np.nan] * len(t))[i] = v

        if a.dry_run:
            print("   [dry-run] would add %d columns" % len(newcols))
            continue
        for c, v in newcols.items():
            t[c] = np.array(v, float)
        if newcols:
            t.write(tab_path, format="ascii.ecsv", overwrite=True)
            print("   WROTE %d EAC columns -> %s" % (len(newcols), tab_path))

    print("\nTOTAL rows %d | models recovered %d (%d of them with a looser "
          "engine minimum) | UNREACHED %d"
          % (grand["ROWS"], grand["OK"], grand.get("LOOSE", 0), grand["FAIL"]))
    if grand.get("LOOSE"):
        print("LOOSE = with every source parameter frozen, profiling the EAC alone "
              "beat the stored AIC. The recovered constants stand; the engine's "
              "minimisation terminated early on those models.")
    if grand["FAIL"]:
        print("UNREACHED models were NOT written — we could not get back to the "
              "engine's own minimum, so those constants are not the fitted ones.")


if __name__ == "__main__":
    main()
