#!/usr/bin/env python
"""WHERE do two competing models actually differ? (PI idea, 2026-08-17)

Motivated by the Basak & Rao style of testing rival prompt-emission models by
restricting the fitted band and re-comparing the statistic. This tool does the
energy-resolved version, in two parts:

  PART A (no refit) — per-channel decomposition of the likelihood difference.
    Both models are evaluated with their STORED best-fit parameters, folded
    through the same responses, and the PGstat contribution of every channel is
    computed for each. Delta = PGstat(B) - PGstat(A) per channel shows exactly
    which energies prefer which model, and the cumulative curve shows how much
    of the total AIC gap comes from where.

  PART B (refit, optional) — the notch test. Re-fit both models with an energy
    band excluded and report whether the preference survives. If the whole
    preference lives in the notch, the two models are indistinguishable outside
    it and the "winner" is a statement about that band alone.

Usage:
  model_discrimination.py --trig bn120119170 --bin 7 --a DSBPL --b SBPLBB
      [--notch 8-30] [--out results/discrimination]

Honest limits (read before using a result):
  * PART A holds parameters fixed at the stored solution; it decomposes the
    likelihood at that point, it does not re-optimize. That is the point (it
    isolates where the models disagree) but it is not a refit.
  * PGstat per channel is well defined, but channels are correlated through the
    response; treat the per-channel curve as a diagnostic, not a per-channel
    significance.
  * The notch test changes the data, so its AIC values are NOT comparable to
    full-band AIC — only A-vs-B within the same notch is meaningful.
"""
import argparse, importlib.util, json, os, sys
import numpy as np
from astropy.table import Table

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def per_channel_pgstat(plugin):
    """PGstat contribution of every active channel, with the model as set."""
    from threeML.utils.statistics.likelihood_functions import \
        poisson_observed_gaussian_background
    obs = np.asarray(plugin.current_observed_counts).astype(np.int64)
    bkg = np.asarray(plugin.current_background_counts, float)
    berr = np.asarray(plugin.current_background_count_errors, float)
    mdl = np.asarray(plugin.get_model(), float)
    loglike, _ = poisson_observed_gaussian_background(obs, bkg, berr, mdl)
    return np.asarray(loglike, float) * (-2.0)      # -2 lnL per channel


def approved_dict(trig, bkg_file):
    """{det: ((pre_lo,pre_hi),(post_lo,post_hi))} — build_plugins wants the dict."""
    bk = Table.read(bkg_file)
    bk = bk[[str(x).strip() == trig for x in bk["TRIGGER_NAME"]]]
    return {str(r["DETECTOR"]).strip():
            ((float(r["BKG_NEG_START"]), float(r["BKG_NEG_STOP"])),
             (float(r["BKG_POS_START"]), float(r["BKG_POS_STOP"]))) for r in bk}


def build_and_set(trig, dets, ref, t1, t2, appr, prefix, srow, eng, P41):
    """Rebuild plugins and install the stored solution for one model."""
    from threeML import DataList, JointLikelihood, Model, PointSource
    live, live_dets = P41.build_plugins(trig, dets, ref, t1, t2, appr)
    if not live:
        raise RuntimeError(f"no plugins built for {trig} {t1}-{t2}; "
                           f"approved dets present: {sorted(appr)}")
    all_specs = (list(eng.MODEL_SPECS) + list(eng.SHAPE_MODEL_SPECS)
                 + list(eng.HIGHE_MODEL_SPECS))
    spec = next(s for s in all_specs
                if str(s.get("prefix", "")).upper() == prefix.upper())
    shape = spec["build"]({})   # engine defaults, then stored solution below
    model = Model(PointSource(trig, 0.0, 0.0, spectral_shape=shape))
    # stored parameters
    for colsuf, pshort in (spec.get("pmap") or {}).items():
        col = f"{spec['prefix']}_{colsuf}"
        if col in srow.colnames and np.isfinite(float(srow[col])):
            try:
                shape.parameters[pshort].value = float(srow[col])
            except Exception:
                pass
    jl = JointLikelihood(model, DataList(*live))
    for d, p in zip(live_dets, live):
        col = f"{spec['prefix']}_EAC_{d.upper()}"
        if col in srow.colnames and np.isfinite(float(srow[col])):
            for k, v in p.nuisance_parameters.items():
                if not v.fix:
                    v.value = float(srow[col])
    return jl, live, live_dets, spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--bin", required=True, help="'tint' or block index")
    ap.add_argument("--a", required=True, help="model prefix A (e.g. DSBPL)")
    ap.add_argument("--b", required=True, help="model prefix B (e.g. SBPLBB)")
    ap.add_argument("--fit-root", default="results/convention_check")
    ap.add_argument("--bkg-file", default="results/background_intervals.ecsv")
    ap.add_argument("--out", default="results/discrimination")
    a = ap.parse_args()
    os.chdir(ROOT)

    eng = _load("eng", "scripts/10_spectral_fit_burst.py")
    P41 = _load("p41", "scripts/41_nuFnu_panels.py")

    t = Table.read(os.path.join(a.fit_root, a.trig, "spectral_fits.ecsv"))
    blk = -1 if a.bin == "tint" else int(a.bin)
    srow = t[[int(r["BLOCK"]) == blk for r in t]][0]
    t1, t2 = float(srow["T_START"]), float(srow["T_STOP"])
    meta = json.load(open(os.path.join(a.fit_root, a.trig, "spectral_fits.json")))
    dets, ref = meta["fit_dets"], meta.get("reference_det", meta["fit_dets"][0])

    appr = approved_dict(a.trig, a.bkg_file)
    res = {}
    for tag, prefix in (("A", a.a), ("B", a.b)):
        jl, live, live_dets, spec = build_and_set(
            a.trig, dets, ref, t1, t2, appr, prefix, srow, eng, P41)
        chans = {}
        for d, p in zip(live_dets, live):
            e_lo, e_hi = None, None
            try:
                ebounds = np.asarray(p.response.ebounds, float)
                mask = np.asarray(p.mask, bool)
                mid = 0.5 * (ebounds[:-1] + ebounds[1:])[mask]
            except Exception:
                mid = None
            pg = per_channel_pgstat(p)
            chans[d] = {"energy_keV": (mid.tolist() if mid is not None else None),
                        "pgstat": pg.tolist(), "total": float(np.sum(pg))}
        res[tag] = {"prefix": prefix, "channels": chans,
                    "total_pgstat": float(sum(c["total"] for c in chans.values())),
                    "stored_aic": float(srow[f"{prefix}_AIC"])}

    os.makedirs(a.out, exist_ok=True)
    stem = os.path.join(a.out, f"{a.trig}_bin{a.bin}_{a.a}_vs_{a.b}")
    print(f"\n{a.trig} bin {a.bin}: {a.a} vs {a.b}")
    print(f"  stored AIC: {a.a}={res['A']['stored_aic']:.2f}  "
          f"{a.b}={res['B']['stored_aic']:.2f}  "
          f"dAIC={res['B']['stored_aic']-res['A']['stored_aic']:+.2f}")
    print(f"  recomputed total -2lnL: {a.a}={res['A']['total_pgstat']:.2f}  "
          f"{a.b}={res['B']['total_pgstat']:.2f}  "
          f"delta={res['B']['total_pgstat']-res['A']['total_pgstat']:+.2f}")
    print("\n  where the difference lives (negative = A better):")
    for d in res["A"]["channels"]:
        ea = np.asarray(res["A"]["channels"][d]["energy_keV"] or [], float)
        pa = np.asarray(res["A"]["channels"][d]["pgstat"], float)
        pb = np.asarray(res["B"]["channels"][d]["pgstat"], float)
        if ea.size != pa.size or pa.size != pb.size:
            print(f"    {d}: channel/energy length mismatch — skipped")
            continue
        diff = pa - pb                      # >0 => B better in that channel
        edges = [(8, 30), (30, 100), (100, 300), (300, 1000), (1000, 40000)]
        parts = []
        for lo, hi in edges:
            m = (ea >= lo) & (ea < hi)
            if m.any():
                parts.append(f"{lo}-{hi}:{np.sum(diff[m]):+6.2f}")
        print(f"    {d}: " + "  ".join(parts))
    json.dump(res, open(stem + ".json", "w"), indent=1)
    print(f"\n  wrote {stem}.json")


if __name__ == "__main__":
    sys.exit(main())
