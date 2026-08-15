#!/usr/bin/env python
"""scripts/47_mvt_cwt_crosscheck.py — Vianello CWT MVT cross-check.

EXTENSION to the settled temporal set (Temporal.md canon: Bala upstream =
CANONICAL, Haar = in-chain cross-check). Vikas, 2026-08-15: "if you want to
crosscheck you can with Vianello's CWT we have used in [LAT]Bright". Third
estimator differing at the PRIMITIVE (false-corroboration rule).

The four CWT functions are VERBATIM from the faithful LATBright implementation
(GRB260226A/s02g_mvt_gbm.py:351-514, itself code-matched to Vianello et al.
2018, github.com/giacomov/mvts): pycwt DOG(2), s0=2dt, dj=0.25; observed power
(global_ws + lag1-autocorr)/scale; noise floor = 10,000 Poisson realizations
through the IDENTICAL pipeline scored global_ws/scale; MVT = smallest scale
where observed exceeds the 99.5th percentile.

DECLARED DEVIATIONS from s02g: (a) background is an LSQ poly-2 on 128 ms bins
over the APPROVED Stage-1 background windows (s02g used gtburst's Cash-LRT
poly); (b) detector = the approved reference NaI from Stage-1, not
brightest-by-counts; (c) energy cut on channel CENTERS (E_MIN+E_MAX)/2.

Heavy tier: conda activate threeML (pycwt 0.4.0b0 confirmed).
Usage: python scripts/47_mvt_cwt_crosscheck.py --trig bn081125496
"""
import os, sys, json, argparse, hashlib, functools, multiprocessing
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DT_FINE = 0.004
COARSE = 0.128
E_LO, E_HI = 8.0, 900.0
DJ = 0.25
MAX_SCALE = 1.0
N_SIM = 10000


# ---- verbatim from LATBright s02g_mvt_gbm.py:351-514 (Vianello CWT) ----
def _cwt_raw(signal, dt, dj=0.25, max_scale_sec=1.0):
    import pycwt as _pycwt
    data = np.array(signal, dtype=float)
    N = len(data)
    if N > 0 and (N & (N - 1)) != 0:
        N2 = int(2 ** np.ceil(np.log2(N)))
        padded = np.full(N2, np.mean(data))
        padded[:N] = data
        data = padded
    N = len(data)
    data_std = np.std(data)
    if data_std == 0:
        return None
    data = (data - np.mean(data)) / data_std
    variance = np.var(data)
    alpha1 = np.corrcoef(data[:-1], data[1:])[0, 1]
    s0 = 2.0 * dt
    mother = _pycwt.DOG(2)
    J = int(np.floor(np.log2(max_scale_sec / s0) / dj))
    if J < 1:
        J = 1
    wave, scales, freqs, coi, fft, fftfreqs = _pycwt.cwt(data, dt, dj, s0, J, mother)
    power = np.abs(wave) ** 2
    global_ws = variance * (np.sum(power.conj().T, axis=0).real / N)
    keep = scales <= max_scale_sec
    return {"global_ws": global_ws[keep], "scales": scales[keep],
            "autocorrelation": alpha1}


def cwt_wavelet_spectrum(signal, dt, dj=0.25, max_scale_sec=1.0):
    result = _cwt_raw(signal, dt, dj=dj, max_scale_sec=max_scale_sec)
    if result is None:
        return np.array([]), np.array([]), 0.0
    global_power = (result["global_ws"] + result["autocorrelation"]) / result["scales"]
    return result["scales"], global_power, result["autocorrelation"]


def _bg_worker(i, lam, N, dt, dj, max_scale_sec):
    rng = np.random.default_rng(seed=42 + i)
    sim_counts = rng.poisson(lam, N).astype(float)
    result = _cwt_raw(sim_counts, dt, dj=dj, max_scale_sec=max_scale_sec)
    if result is None:
        return None
    return np.array(result["global_ws"] / result["scales"], dtype=np.float16)


def cwt_background_spectrum(mean_rate, dt, N, n_simulations=10000, dj=0.25,
                            max_scale_sec=1.0,
                            percentiles=(0.5, 5, 16, 50, 84, 95, 99.5)):
    lam = max(mean_rate, 0.01)
    result0 = _cwt_raw(np.random.default_rng(0).poisson(lam, N).astype(float),
                       dt, dj=dj, max_scale_sec=max_scale_sec)
    if result0 is None:
        return np.array([]), {}
    scales = result0["scales"]
    n_scales = len(scales)
    worker_fn = functools.partial(_bg_worker, lam=lam, N=N, dt=dt,
                                  dj=dj, max_scale_sec=max_scale_sec)
    n_cpus = min(12, max(1, multiprocessing.cpu_count() - 2))
    print(f"  {n_simulations} MC sims on {n_cpus} cores...", flush=True)
    all_power = np.zeros((n_simulations, n_scales))
    with multiprocessing.Pool(n_cpus) as pool:
        for idx, pw in enumerate(pool.imap_unordered(worker_fn,
                                                     range(n_simulations),
                                                     chunksize=100)):
            if pw is not None and len(pw) == n_scales:
                all_power[idx, :] = pw
    return scales, {p: np.percentile(all_power, p, axis=0) for p in percentiles}


def find_mvt_cwt(observed_power, noise_upper, scales):
    if len(scales) == 0:
        return np.nan, np.nan
    for i in range(len(scales)):
        if observed_power[i] > noise_upper[i]:
            mvt = scales[i]
            err = (scales[i] - scales[i - 1]) / 2.0 if i > 0 else scales[i] * 0.5
            return mvt, err
    return np.nan, np.nan
# ---- end verbatim block ----


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "mvt_cwt"))
    a = ap.parse_args()

    from astropy.table import Table
    from astropy.io import fits
    import glob as _glob

    appr = Table.read(os.path.join(ROOT, "results", "background_intervals.ecsv"))
    rows = appr[[str(x).strip() == a.trig for x in appr["TRIGGER_NAME"]]]
    nais = [r for r in rows if str(r["DETECTOR"]).strip().startswith("n")]
    ref = min(nais, key=lambda r: float(r["DET_ANGLE"]))
    det = str(ref["DETECTOR"]).strip()
    b_neg = (float(ref["BKG_NEG_START"]), float(ref["BKG_NEG_STOP"]))
    b_pos = (float(ref["BKG_POS_START"]), float(ref["BKG_POS_STOP"]))

    blocks = Table.read(os.path.join(ROOT, "results", "sweep106", a.trig, "blocks",
                                     f"bb_blocks_spectral_{a.trig}.ecsv"))
    bt = blocks[[str(x).strip() == det for x in blocks["DETECTOR"]]]
    t1, t2 = float(bt["T_START"][0]), float(bt["T_STOP"][-1])

    tte = sorted(_glob.glob(os.path.join(ROOT, "data", a.trig,
                                         f"glg_tte_{det}_{a.trig}_v*.fit*")))[-1]
    with fits.open(tte) as h:
        eb = h["EBOUNDS"].data
        ecen = 0.5 * (eb["E_MIN"] + eb["E_MAX"])
        ev = h["EVENTS"].data
        trigt = float(h[0].header.get("TRIGTIME"))
        t = np.asarray(ev["TIME"], float) - trigt
        e = ecen[np.asarray(ev["PHA"], int)]
    m = (e >= E_LO) & (e < E_HI)
    t = t[m]

    # fine binning over the full approved span; LSQ poly-2 background on the
    # APPROVED windows (declared deviation vs s02g's Cash poly)
    span = (b_neg[0], b_pos[1])
    edges = np.arange(span[0], span[1] + DT_FINE, DT_FINE)
    cts, _ = np.histogram(t, bins=edges)
    tc = 0.5 * (edges[:-1] + edges[1:])
    cedges = np.arange(span[0], span[1] + COARSE, COARSE)
    ccts, _ = np.histogram(t, bins=cedges)
    ctc = 0.5 * (cedges[:-1] + cedges[1:])
    crate = ccts / COARSE
    bm = ((ctc >= b_neg[0]) & (ctc <= b_neg[1])) | ((ctc >= b_pos[0]) & (ctc <= b_pos[1]))
    pc = np.polyfit(ctc[bm], crate[bm], 2)
    net = cts - np.polyval(pc, tc) * DT_FINE

    w = (tc >= t1) & (tc <= t2)
    net_burst = net[w]
    mean_cts_bin = float(np.mean(cts[w]))     # raw counts/bin drives the Poisson floor

    scales, obs_power, alpha1 = cwt_wavelet_spectrum(net_burst, DT_FINE,
                                                     dj=DJ, max_scale_sec=MAX_SCALE)
    nsc, noise = cwt_background_spectrum(mean_cts_bin, DT_FINE, len(net_burst),
                                         n_simulations=N_SIM, dj=DJ,
                                         max_scale_sec=MAX_SCALE)
    mvt, err = find_mvt_cwt(obs_power, noise[99.5], scales)
    print(f"CWT MVT ({a.trig}, {det}, {E_LO:.0f}-{E_HI:.0f} keV, window "
          f"[{t1:.2f},{t2:.2f}] s): {mvt*1e3:.2f} +/- {err*1e3:.2f} ms "
          f"(99.5th pct floor, {N_SIM} sims)", flush=True)

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.abspath(__file__), "rb") as fh:
        src_sha = hashlib.sha256(fh.read()).hexdigest()
    out = dict(script="47_mvt_cwt_crosscheck.py", script_sha256=src_sha,
               trig=a.trig, detector=det, band_keV=[E_LO, E_HI],
               window_s=[t1, t2], dt_s=DT_FINE, dj=DJ, max_scale_s=MAX_SCALE,
               n_sim=N_SIM, mean_counts_per_bin=mean_cts_bin, alpha1=alpha1,
               mvt_cwt_s=float(mvt), mvt_cwt_err_s=float(err),
               noise_percentile=99.5,
               provenance="verbatim CWT from LATBright s02g:351-514 (Vianello 2018); "
                          "declared deviations: LSQ poly-2 bkg on approved windows, "
                          "approved ref NaI, channel-center energy cut",
               role="EXTENSION cross-check; canon = Bala upstream (Temporal.md)")
    with open(os.path.join(a.out, f"{a.trig}_mvt_cwt.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("WROTE", os.path.join(a.out, f"{a.trig}_mvt_cwt.json"))


if __name__ == "__main__":
    main()
