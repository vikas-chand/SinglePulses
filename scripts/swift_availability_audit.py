#!/usr/bin/env python
"""
Swift-BAT/XRT availability audit for the 106 single-pulse Fermi/GBM GRBs.

GROUNDING: uses REAL astroquery HEASARC queries only. No fabricated matches.

HEASARC tables used (printed at runtime, auditable):
  - swiftgrbba : "Swift Gamma Ray Burst Compilation by Burst Advocate"
                 (actively maintained, 2004->present; date in NAME, time in
                  TRIGGER_TIME; RA/DEC + ERROR_RADIUS [arcmin]; BAT_T90;
                  XRT_FIRST_OBS [s post-trigger], XRT_RA/DEC)
  - swiftgrb   : "Swift Gamma Ray Bursts Catalog" (frozen 2004-2012; used only
                  to enrich matched pre-2013 bursts with the precise BAT event
                  window BAT_START/BAT_STOP and XRT_ONSOURCE settle time, and
                  ISO trigger datetime).

Match = TIME COINCIDENCE (Swift trigger within a few minutes of the Fermi
trigger) AND POSITION consistency (Swift arcmin-precise position within the
GBM few-degree error circle). Same-day + close-position => same GRB.

Run:  /Users/salim/anaconda3/envs/threeML/bin/python scripts/swift_availability_audit.py
"""
import warnings, re, sys
warnings.filterwarnings("ignore")
import numpy as np
from astropy.table import Table
from astropy.coordinates import SkyCoord, Angle
import astropy.units as u
from astropy.time import Time
from astroquery.heasarc import Heasarc

# ---- config ----
TIME_TOL_S      = 180.0    # +/- 3 min => same trigger
POS_TOL_DEG     = 8.0      # generous GBM systematic error circle for a candidate
POS_CONFIRM_DEG = 5.0      # <= this is a confident position match
BAT_PROMPT_MARGIN_S = 5.0  # slack around T90 for BAT prompt-overlap logic

REPO = "/Users/salim/Desktop/Projects/SingleRest/Two_Breaks"
SP   = f"{REPO}/results/single_pulse_grbs.ecsv"
GS   = f"{REPO}/results/grb_sample.ecsv"
OUT  = f"{REPO}/results/swift_availability.ecsv"

# --------------------------------------------------------------------------
def parse_bn_utc(trig_name):
    """bnYYMMDDfff -> (Time UTC, T0_seconds_of_day). fff/1000*86400."""
    m = re.match(r"bn(\d{2})(\d{2})(\d{2})(\d{3})", trig_name)
    if not m:
        return None, None
    yy, mm, dd, fff = m.groups()
    year = 2000 + int(yy)
    frac = int(fff) / 1000.0
    t0_s = frac * 86400.0
    iso_date = f"{year:04d}-{int(mm):02d}-{int(dd):02d}"
    t = Time(iso_date, format="iso", scale="utc") + t0_s * u.s
    return t, t0_s

def swift_name_to_time(name, time_str):
    """swiftgrbba: date from 'GRB YYMMDDx', time from TRIGGER_TIME 'HH:MM:SS'."""
    m = re.search(r"(\d{6})", name)
    if not m:
        return None
    six = m.group(1)
    yy, mm, dd = int(six[0:2]), int(six[2:4]), int(six[4:6])
    year = 2000 + yy if yy < 90 else 1900 + yy
    ts = str(time_str).strip()
    hm = re.match(r"(\d{1,2}):(\d{2}):(\d{2})", ts)
    if not hm:
        # no time-of-day -> put at noon, will still match by date within TIME_TOL only if fff~0.5
        secs = 0.0
        return None
    hh, mi, ss = map(int, hm.groups())
    try:
        t = Time(f"{year:04d}-{mm:02d}-{dd:02d} {hh:02d}:{mi:02d}:{ss:02d}",
                 format="iso", scale="utc")
    except Exception:
        return None
    return t

# --------------------------------------------------------------------------
print("=" * 78)
print("HEASARC tables used:")
print("  primary : swiftgrbba  (Swift Gamma Ray Burst Compilation by Burst Advocate)")
print("  enrich  : swiftgrb    (Swift Gamma Ray Bursts Catalog, 2004-2012)")
print("=" * 78)

h = Heasarc()

# ---- pull swiftgrbba (all rows) ----
print("Querying swiftgrbba (full catalog) ...")
ba = h.query_region(
    SkyCoord(0, 0, unit="deg"), mission="swiftgrbba", radius=180 * u.deg,
    fields=("NAME,TRIGGER_TIME,RA,DEC,ERROR_RADIUS,BAT_T90,"
            "XRT_FIRST_OBS,XRT_RA,XRT_DEC,XRT_ERROR_RADIUS,"
            "XRT_11HR_FLUX,XRT_EARLY_FLUX,OTHER_OBS"),
    resultmax=100000,
)
print(f"  swiftgrbba rows: {len(ba)}")

# ---- pull swiftgrb (frozen, has ISO datetime + BAT window + XRT settle) ----
print("Querying swiftgrb (full catalog) ...")
sg = h.query_region(
    SkyCoord(0, 0, unit="deg"), mission="swiftgrb", radius=180 * u.deg,
    fields=("NAME,RA,DEC,TRIGGER_TIME,BAT_T90,BAT_DETECTION,BAT_START,BAT_STOP,"
            "XRT_DETECTION,XRT_RA,XRT_DEC,XRT_ONSOURCE"),
    resultmax=100000,
)
print(f"  swiftgrb rows:  {len(sg)}")

# Build swiftgrb ISO-time lookup by SkyCoord for enrichment of matched bursts
sg_times, sg_valid = [], []
for r in sg:
    ts = str(r["TRIGGER_TIME"]).strip()
    try:
        sg_times.append(Time(ts.replace("T", " "), format="iso", scale="utc"))
        sg_valid.append(True)
    except Exception:
        sg_times.append(None); sg_valid.append(False)

# Precompute swiftgrbba times + coords
ba_times = []
for r in ba:
    ba_times.append(swift_name_to_time(str(r["NAME"]), r["TRIGGER_TIME"]))
ba_ra = np.array([float(r["RA"]) if r["RA"] not in ("", None) else np.nan for r in ba])
ba_dec = np.array([float(r["DEC"]) if r["DEC"] not in ("", None) else np.nan for r in ba])

# --------------------------------------------------------------------------
# Load Fermi sample
sp = Table.read(SP)
gs = Table.read(GS)
gs_by_trig = {str(r["TRIGGER_NAME"]): r for r in gs}

print(f"\nFermi single-pulse sample: {len(sp)} bursts")

rows = []
ambiguous = []
missing_radec = []

for srow in sp:
    trig = str(srow["TRIGGER_NAME"])
    has_lat = bool(srow["HAS_LAT"])
    t90 = float(srow["T90"])

    t_bn, t0_s = parse_bn_utc(trig)

    # authoritative Fermi trigger time: prefer grb_sample MJD, cross-check bn
    grow = gs_by_trig.get(trig)
    if grow is not None and grow["RA"] not in ("", None):
        ra_f = float(grow["RA"]); dec_f = float(grow["DEC"])
        t_fermi = Time(float(grow["TRIGGER_TIME"]), format="mjd", scale="utc")
    else:
        ra_f = dec_f = np.nan
        t_fermi = t_bn
        missing_radec.append(trig)

    c_f = SkyCoord(ra_f, dec_f, unit="deg") if np.isfinite(ra_f) else None

    # ---- search swiftgrbba by time coincidence ----
    cands = []
    for i, tb in enumerate(ba_times):
        if tb is None:
            continue
        dt = (tb - t_fermi).sec
        if abs(dt) <= TIME_TOL_S:
            pos_off = np.nan
            if c_f is not None and np.isfinite(ba_ra[i]) and np.isfinite(ba_dec[i]):
                pos_off = c_f.separation(
                    SkyCoord(ba_ra[i], ba_dec[i], unit="deg")).deg
            cands.append((i, dt, pos_off))

    # keep candidates that are position-consistent (or position unknown)
    good = [c for c in cands if (not np.isfinite(c[2])) or c[2] <= POS_TOL_DEG]

    matched = None
    if len(good) == 1:
        matched = good[0]
    elif len(good) > 1:
        # pick the closest in position (fallback: closest in time)
        good_sorted = sorted(
            good, key=lambda c: (c[2] if np.isfinite(c[2]) else 1e9, abs(c[1])))
        matched = good_sorted[0]
        second = good_sorted[1]
        # flag ambiguity only if two are both position-confirmed and close
        if (np.isfinite(matched[2]) and matched[2] <= POS_TOL_DEG and
                np.isfinite(second[2]) and second[2] <= POS_TOL_DEG):
            ambiguous.append((trig, [ (str(ba['NAME'][c[0]]).strip(), round(c[1],1),
                              round(c[2],3) if np.isfinite(c[2]) else None) for c in good_sorted]))

    if matched is None:
        rows.append(dict(
            TRIGGER_NAME=trig, SWIFT_GRB="", HAS_SWIFT=False, HAS_BAT=False,
            HAS_XRT=False, XRT_note="no Swift match",
            T_OFFSET_S=np.nan, POS_OFFSET_DEG=np.nan, HAS_LAT=has_lat))
        continue

    i, dt, pos_off = matched
    sw = ba[i]
    sw_name = str(sw["NAME"]).strip()

    # position confidence
    pos_conf = (not np.isfinite(pos_off)) or (pos_off <= POS_CONFIRM_DEG)

    # ---- BAT: a swiftgrbba entry IS a BAT-triggered GRB ----
    has_bat = True  # entry in the BAT-GRB compilation => BAT triggered

    # ---- XRT: did XRT observe / detect ----
    xrt_first = sw["XRT_FIRST_OBS"]
    try:
        xrt_first = float(xrt_first)
    except Exception:
        xrt_first = np.nan
    # A genuine XRT detection needs a real localisation (RA/DEC not both the
    # 0.0 null placeholder) confirmed by a positive error radius or flux, OR a
    # positive settle time. RA==DEC==err==flux==0 is the "not detected" null.
    def _f(v):
        try: return float(v)
        except Exception: return np.nan
    xrt_ra = _f(sw["XRT_RA"]); xrt_dec = _f(sw["XRT_DEC"])
    xrt_err = _f(sw["XRT_ERROR_RADIUS"])
    xrt_11 = _f(sw["XRT_11HR_FLUX"]); xrt_early = _f(sw["XRT_EARLY_FLUX"])
    has_xrt_pos = (np.isfinite(xrt_ra) and np.isfinite(xrt_dec)
                   and not (xrt_ra == 0.0 and xrt_dec == 0.0))
    has_xrt_signal = ((np.isfinite(xrt_err) and xrt_err > 0)
                      or (np.isfinite(xrt_11) and xrt_11 > 0)
                      or (np.isfinite(xrt_early) and xrt_early > 0)
                      or (np.isfinite(xrt_first) and xrt_first > 0))
    has_xrt = bool(has_xrt_pos and has_xrt_signal)

    # ---- enrich from swiftgrb (frozen table) for BAT window + XRT settle ----
    bat_start = bat_stop = xrt_onsource = np.nan
    c_sw = SkyCoord(float(sw["RA"]), float(sw["DEC"]), unit="deg") if (
        sw["RA"] not in ("", None)) else None
    if c_sw is not None:
        best_j, best_sep = None, 1e9
        for j in range(len(sg)):
            if not sg_valid[j]:
                continue
            try:
                sepj = c_sw.separation(
                    SkyCoord(float(sg["RA"][j]), float(sg["DEC"][j]), unit="deg")).deg
            except Exception:
                continue
            if sepj < best_sep:
                best_sep, best_j = sepj, j
        if best_j is not None and best_sep < 0.05 and sg_times[best_j] is not None:
            if abs((sg_times[best_j] - t_fermi).sec) <= TIME_TOL_S:
                try: bat_start = float(sg["BAT_START"][best_j])
                except Exception: pass
                try: bat_stop = float(sg["BAT_STOP"][best_j])
                except Exception: pass
                try: xrt_onsource = float(sg["XRT_ONSOURCE"][best_j])
                except Exception: pass

    # ---- XRT prompt-overlap note ----
    # XRT slews after the trigger; its first data starts at xrt_first (or
    # xrt_onsource) seconds. Prompt overlap requires that start < T90.
    xrt_start_s = xrt_onsource if np.isfinite(xrt_onsource) else xrt_first
    if not has_xrt:
        xrt_note = "no XRT detection (BAT-only)"
    elif np.isfinite(xrt_start_s):
        if xrt_start_s <= 0:
            xrt_note = (f"XRT detected but settle/start time unfilled in catalog; "
                        f"T90={t90:.1f}s (typical XRT slew ~60-100s => afterglow)")
        elif xrt_start_s < t90 + BAT_PROMPT_MARGIN_S:
            xrt_note = (f"XRT starts +{xrt_start_s:.0f}s < T90={t90:.1f}s "
                        f"-> plausible prompt overlap")
        else:
            xrt_note = (f"XRT starts +{xrt_start_s:.0f}s > T90={t90:.1f}s "
                        f"-> afterglow only")
    else:
        xrt_note = f"XRT observed, start time unknown; T90={t90:.1f}s"

    if not pos_conf and np.isfinite(pos_off):
        xrt_note += f" [BORDERLINE pos {pos_off:.1f}deg]"

    rows.append(dict(
        TRIGGER_NAME=trig,
        SWIFT_GRB=sw_name,
        HAS_SWIFT=True,
        HAS_BAT=bool(has_bat),
        HAS_XRT=bool(has_xrt),
        XRT_note=xrt_note,
        T_OFFSET_S=round(float(dt), 1),
        POS_OFFSET_DEG=(round(float(pos_off), 3) if np.isfinite(pos_off) else np.nan),
        HAS_LAT=has_lat,
        _bat_start=bat_start, _bat_stop=bat_stop, _xrt_start=xrt_start_s, _t90=t90,
    ))

# --------------------------------------------------------------------------
# Build output table
out = Table()
out["TRIGGER_NAME"]   = [r["TRIGGER_NAME"] for r in rows]
out["SWIFT_GRB"]      = [r["SWIFT_GRB"] for r in rows]
out["HAS_SWIFT"]      = [r["HAS_SWIFT"] for r in rows]
out["HAS_BAT"]        = [r["HAS_BAT"] for r in rows]
out["HAS_XRT"]        = [r["HAS_XRT"] for r in rows]
out["XRT_note"]       = [r["XRT_note"] for r in rows]
out["T_OFFSET_S"]     = [r["T_OFFSET_S"] for r in rows]
out["POS_OFFSET_DEG"] = [r["POS_OFFSET_DEG"] for r in rows]
out["HAS_LAT"]        = [r["HAS_LAT"] for r in rows]
out.meta["HEASARC_TABLES"] = "swiftgrbba (primary); swiftgrb (enrichment)"
out.meta["TIME_TOL_S"] = TIME_TOL_S
out.meta["POS_TOL_DEG"] = POS_TOL_DEG
out.write(OUT, format="ascii.ecsv", overwrite=True)

# --------------------------------------------------------------------------
# Summary
n = len(rows)
n_swift = sum(r["HAS_SWIFT"] for r in rows)
n_bat   = sum(r["HAS_BAT"] for r in rows)
n_xrt   = sum(r["HAS_XRT"] for r in rows)
n_both  = sum(r["HAS_BAT"] and r["HAS_XRT"] for r in rows)
n_lat   = sum(bool(r["HAS_LAT"]) for r in rows)

# joint-prompt candidate = BAT triggered (BAT event window covers prompt).
# BAT_START/STOP ~ T-240..+960 always covers a single-pulse GRB prompt.
n_joint_prompt = n_bat  # every BAT-triggered burst has prompt BAT coverage

# XRT prompt-overlap subset
n_xrt_prompt = sum(1 for r in rows
                   if r["HAS_XRT"] and "plausible prompt overlap" in r["XRT_note"])

print("\n" + "=" * 78)
print("SWIFT AVAILABILITY SUMMARY  (Fermi single-pulse sample)")
print("=" * 78)
print(f"  Total Fermi single-pulse bursts : {n}")
print(f"  Matched a Swift GRB (HAS_SWIFT)  : {n_swift}")
print(f"  Swift-BAT triggered (HAS_BAT)    : {n_bat}")
print(f"  Swift-XRT observed  (HAS_XRT)    : {n_xrt}")
print(f"  BAT AND XRT both                 : {n_both}")
print(f"  JOINT-PROMPT candidates          : {n_joint_prompt}")
print(f"     (BAT triggered => BAT event window ~T-240..+960 s covers the prompt)")
print(f"  ...of which XRT also plausibly overlaps prompt (start < T90): {n_xrt_prompt}")
print(f"  Fermi GBM+LLE+LAT coverage (HAS_LAT=True): {n_lat}  "
      f"(all {n} have GBM; {n_lat} additionally have LAT/LLE)")

if missing_radec:
    print(f"\n  NOTE: {len(missing_radec)} burst(s) lacked RA/DEC in grb_sample "
          f"(matched on time only): {missing_radec}")

if ambiguous:
    print(f"\n  AMBIGUOUS matches ({len(ambiguous)}) — multiple position-confirmed "
          f"Swift candidates within tolerance:")
    for trig, cs in ambiguous:
        print(f"    {trig}: {cs}")
else:
    print("\n  No ambiguous (multi-candidate position-confirmed) matches.")

# List the matched bursts for the record
print("\n  MATCHED BURSTS:")
for r in rows:
    if r["HAS_SWIFT"]:
        po = r["POS_OFFSET_DEG"]
        po_s = f"{po:.2f}deg" if po == po else "pos?"
        print(f"    {r['TRIGGER_NAME']} <-> {r['SWIFT_GRB']:12s} "
              f"dt={r['T_OFFSET_S']:+.0f}s off={po_s:8s} "
              f"BAT={int(r['HAS_BAT'])} XRT={int(r['HAS_XRT'])} | {r['XRT_note']}")

print(f"\nWrote: {OUT}")
