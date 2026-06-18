#!/usr/bin/env python
"""How many blocks with 3ML use_background=True (background-aware BB) vs our
raw-event astropy BB, on the brightest NaI, same window, same p0. Answers:
does background-aware change-point finding give different (fewer/cleaner) bins?"""
import os, sys, glob, warnings
warnings.filterwarnings('ignore')
os.environ.setdefault('OMP_NUM_THREADS', '1')

# CALDB env (mirror scripts/10) — required before any threeML/gtburst import
_FD = '/Users/salim/anaconda3/envs/threeML/share/fermitools'
if not os.environ.get('CALDB') or '/refdata/fermi' in os.environ.get('CALDBALIAS', ''):
    os.environ['FERMI_DIR'] = _FD
    os.environ['CALDB'] = _FD + '/data/caldb'
    os.environ['CALDBALIAS'] = _FD + '/data/caldb/software/tools/alias_config.fits'
    os.environ['CALDBCONFIG'] = _FD + '/data/caldb/software/tools/caldb.config'
    os.environ['CALDBROOT'] = _FD + '/data/caldb'
    os.environ['EXTFILESSYS'] = _FD + '/refdata/fermi'
import numpy as np
from astropy.io import fits
from astropy.table import Table
import astropy.stats as astats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data'); RES = os.path.join(BASE, 'results')
P0 = 0.01
BURG = ['bn081224887', 'bn090719063', 'bn100707032',
        'bn110721200', 'bn110920546', 'bn130427324']
PUB = {'bn081224887': '~?', 'bn090719063': '~?', 'bn100707032': '~?',
       'bn110721200': '5-7', 'bn110920546': '~?', 'bn130427324': '~?'}

single = Table.read(os.path.join(RES, 'single_pulse_grbs.ecsv'), format='ascii.ecsv')
bkg = Table.read(os.path.join(RES, 'background_intervals_prototype.ecsv'), format='ascii.ecsv')


def find(trig, kind, det):
    for pat in (f'glg_{kind}_{det}_*.fit.gz', f'glg_{kind}_{det}_*.fit',
                f'glg_{kind}_{det}_*.rsp2', f'glg_{kind}_{det}_*.rsp'):
        m = glob.glob(os.path.join(DATA, trig, pat))
        if m:
            return m[0]
    return None


def best_nai_with_bkg(trig):
    bk = bkg[bkg['TRIGGER_NAME'] == trig]
    nais = sorted({str(r['DETECTOR']).strip() for r in bk
                   if str(r['DETECTOR']).strip().startswith('n')})
    sp = single[single['TRIGGER_NAME'] == trig]
    pref = str(sp[0]['DETECTOR']).strip() if len(sp) else None
    if pref in nais:
        return pref
    return nais[0] if nais else None


def raw_event_nblocks(trig, det, lo, hi, band=(8, 900)):
    tte = find(trig, 'tte', det)
    with fits.open(tte) as h:
        ev = h['EVENTS'].data
        t0 = h['PRIMARY'].header.get('TRIGTIME', 0.0)
        eb = h['EBOUNDS'].data; emid = 0.5*(np.asarray(eb['E_MIN'])+np.asarray(eb['E_MAX']))
        tt = np.asarray(ev['TIME']) - t0
        m = (emid[ev['PHA']] >= band[0]) & (emid[ev['PHA']] <= band[1])
        tt = np.sort(tt[m]); tt = tt[(tt >= lo) & (tt <= hi)]
    if tt.size > 500_000:
        dt = 0.064; e = np.arange(lo, hi+dt, dt); c = 0.5*(e[:-1]+e[1:])
        cn, _ = np.histogram(tt, bins=e)
        return len(astats.bayesian_blocks(c, cn/dt, np.sqrt(np.maximum(cn,1))/dt,
                   fitness='measures', p0=P0))-1, tt.size
    return len(astats.bayesian_blocks(tt, fitness='events', p0=P0))-1, tt.size


def threeml_bg_nblocks(trig, det, lo, hi, pre_str, post_str):
    from threeML import TimeSeriesBuilder
    tte = find(trig, 'tte', det); rsp = find(trig, 'cspec', det) or find(trig, 'tte', det)
    tsb = TimeSeriesBuilder.from_gbm_tte(det, tte, rsp_file=rsp, verbose=False)
    tsb.set_background_interval(pre_str, post_str)
    tsb.create_time_bins(lo, hi, method='bayesblocks', p0=P0, use_background=True)
    return len(tsb.bins)


print(f'{"trigger":13s} {"det":4s} {"window":>16s} {"raw_evt":>8s} {"use_bg":>7s} {"nev":>9s} {"Burgess":>8s}')
for trig in BURG:
    det = best_nai_with_bkg(trig)
    bk = bkg[(bkg['TRIGGER_NAME'] == trig) & (bkg['DETECTOR'] == det)][0]
    pre = (float(bk['BKG_NEG_START']), float(bk['BKG_NEG_STOP']))
    post = (float(bk['BKG_POS_START']), float(bk['BKG_POS_STOP']))
    lo, hi = pre[1], post[0]
    pre_str = f'{pre[0]:.3f}-{pre[1]:.3f}'; post_str = f'{post[0]:.3f}-{post[1]:.3f}'
    try:
        n_raw, nev = raw_event_nblocks(trig, det, lo, hi)
    except Exception as e:
        n_raw, nev = -1, -1; print('  raw err', trig, e)
    try:
        n_bg = threeml_bg_nblocks(trig, det, lo, hi, pre_str, post_str)
    except Exception as e:
        n_bg = -1; print('  3ML err', trig, type(e).__name__, str(e)[:90])
    print(f'{trig:13s} {det:4s} [{lo:6.1f},{hi:6.1f}] {n_raw:>8d} {n_bg:>7d} {nev:>9d} {PUB[trig]:>8s}',
          flush=True)
