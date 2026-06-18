#!/usr/bin/env python
"""
Why do we get different Bayesian blocks than Burgess, following the 'same' method?
Bayesian Blocks is deterministic GIVEN its inputs, but several inputs Burgess
never published change the block count. Sweep them and show the sensitivity.

Knobs:
  p0   : Scargle false-alarm prior (ncp_prior). LOWER p0 -> FEWER blocks.
  dt   : light-curve resolution for count-rate (measures) mode.
  bkg  : raw counts vs background-subtracted rate.
  mode : 'events' (photon arrival times) vs 'measures' (binned count rate).
Compare to Burgess 110721A ~5-7 bins (his explicit low end, paper line 472).
"""
import warnings; warnings.filterwarnings('ignore')
import glob, numpy as np
from astropy.io import fits
from astropy.stats import bayesian_blocks

BURG = {'110721A': ('bn110721200', 'n6'),
        '100707A': ('bn100707032', 'n7'),
        '090719A': ('bn090719063', 'n7'),
        '130427A': ('bn130427324', 'n6')}
ELO, EHI = 8.0, 300.0


def load(trig, det):
    f = sorted(glob.glob(f'data/{trig}/glg_tte_{det}_*.fit*'))
    with fits.open(f[0]) as h:
        ev = h['EVENTS'].data
        t0 = next(hh.header['TRIGTIME'] for hh in h if 'TRIGTIME' in hh.header)
        tt = np.asarray(ev['TIME']) - t0
        eb = h['EBOUNDS'].data
        emid = 0.5*(np.asarray(eb['E_MIN'])+np.asarray(eb['E_MAX']))
        m = (emid[ev['PHA']] >= ELO) & (emid[ev['PHA']] <= EHI)
    return np.sort(tt[m])


def window(tt):
    dt = 0.256
    e = np.arange(-50, 150, dt); c = 0.5*(e[:-1]+e[1:])
    h, _ = np.histogram(tt, bins=e); rate = h/dt
    quiet = (c < -20) | (c > 60)
    b = np.median(rate[quiet]); noise = np.sqrt(max(b, 1e-6)/dt)
    net = np.convolve(rate-b, np.ones(3)/3, mode='same')
    pk = int(np.argmax(net))
    lo = pk
    while lo > 0 and net[lo-1] > 1.0*noise:
        lo -= 1
    hi = pk
    while hi < len(net)-1 and net[hi+1] > 1.0*noise:
        hi += 1
    return float(c[lo]-0.5), float(c[hi]+0.5), b


def nblk_measures(tt, lo, hi, dt, p0, bkgsub=False, blevel=0.0):
    e = np.arange(lo, hi+dt, dt); c = 0.5*(e[:-1]+e[1:])
    h, _ = np.histogram(tt, bins=e); rate = h/dt
    if bkgsub:
        rate = rate - blevel
    err = np.sqrt(np.maximum(h, 1))/dt
    return len(bayesian_blocks(c, rate, err, fitness='measures', p0=p0)) - 1


print('=== p0 sensitivity (measures mode, dt=0.064 s, raw counts) ===')
print(f'{"GRB":9s} ' + ' '.join(f'p0={p:<6g}' for p in [0.5, 0.1, 0.05, 0.01, 0.005, 0.001]))
data = {}
for name, (trig, det) in BURG.items():
    tt = load(trig, det); lo, hi, b = window(tt); data[name] = (tt, lo, hi, b)
    row = [nblk_measures(tt, lo, hi, 0.064, p) for p in [0.5, 0.1, 0.05, 0.01, 0.005, 0.001]]
    print(f'{name:9s} ' + ' '.join(f'{n:<8d}' for n in row))

print('\n=== dt (resolution) sensitivity (measures, p0=0.01, raw) ===')
print(f'{"GRB":9s} ' + ' '.join(f'dt={d:<6g}' for d in [0.032, 0.064, 0.256, 1.0, 2.0]))
for name in BURG:
    tt, lo, hi, b = data[name]
    row = [nblk_measures(tt, lo, hi, d, 0.01) for d in [0.032, 0.064, 0.256, 1.0, 2.0]]
    print(f'{name:9s} ' + ' '.join(f'{n:<8d}' for n in row))

print('\n=== background subtraction (measures, dt=0.256, p0=0.01) ===')
print(f'{"GRB":9s} {"raw":>6s} {"bkgsub":>7s}')
for name in BURG:
    tt, lo, hi, b = data[name]
    raw = nblk_measures(tt, lo, hi, 0.256, 0.01, bkgsub=False)
    sub = nblk_measures(tt, lo, hi, 0.256, 0.01, bkgsub=True, blevel=b)
    print(f'{name:9s} {raw:>6d} {sub:>7d}')

print('\n=== events vs measures mode (p0=0.01, raw) ===')
print(f'{"GRB":9s} {"events":>7s} {"measures(64ms)":>15s}')
for name in BURG:
    tt, lo, hi, b = data[name]
    src = tt[(tt >= lo) & (tt <= hi)]
    if src.size > 200_000:
        nev = -1   # event-mode is O(N^2) — skip (would hang on bright bursts)
    else:
        try:
            nev = len(bayesian_blocks(src, fitness='events', p0=0.01)) - 1
        except Exception:
            nev = -1
    nm = nblk_measures(tt, lo, hi, 0.064, 0.01)
    print(f'{name:9s} {nev:>7d} {nm:>15d}')

print('\nBurgess: 110721A ~5-7 bins (paper line 472, explicit low end);'
      ' others ~10-30.')
