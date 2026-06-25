#!/usr/bin/env python
"""
fetch_tte.py -- lightweight TTE downloader for the background-approval handoff.

Downloads ONLY the GBM TTE event files the background picker needs (one per
(trigger, detector) row in results/background_starting_points.ecsv), straight from
the public HEASARC Fermi/GBM trigger archive. STDLIB ONLY (urllib + re) -- no
threeML, no fermitools, no requests -- so the picker environment stays light.

The picker plots light curves from these TTE files; it does NOT need CSPEC/RSP
(those are only for the downstream spectral fits, which run on Vikas's side).

Archive layout (verified):
  https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/triggers/<YYYY>/<trigger>/current/
  -> glg_tte_<det>_<trigger>_v<NN>.fit   (highest version chosen)

Usage:
  python handoff_background_approval/fetch_tte.py                 # all needed TTE
  python handoff_background_approval/fetch_tte.py --burst bn110721200
  python handoff_background_approval/fetch_tte.py --limit 5       # first 5 bursts
Re-runnable: files already present in data/<trigger>/ are skipped.
"""
import os
import re
import sys
import glob
import argparse
import urllib.request
from astropy.table import Table

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')
MANIFEST = os.path.join(BASE, 'results', 'background_starting_points.ecsv')
ARCHIVE = 'https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/triggers'
TIMEOUT = 60


def year_of(trigger):
    """bnYYMMDDFFF -> 20YY (GBM triggers are all post-2008)."""
    return 2000 + int(trigger[2:4])


def list_dir(url):
    """Return the set of filenames linked in an Apache directory listing."""
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        html = r.read().decode('utf-8', 'replace')
    return set(re.findall(r'href="([^"?/][^"]*)"', html))


def best_tte(names, trigger, det):
    """Highest-version glg_tte_<det>_<trigger>_vNN.fit(.gz) in a listing, or None."""
    pat = re.compile(rf'^glg_tte_{re.escape(det)}_{re.escape(trigger)}_v(\d+)\.fit(\.gz)?$')
    cands = [(int(m.group(1)), n) for n in names for m in [pat.match(n)] if m]
    return max(cands)[1] if cands else None


def have_tte(trigger, det):
    g = os.path.join(DATA, trigger)
    return bool(glob.glob(os.path.join(g, f'glg_tte_{det}_*.fit.gz'))
               or glob.glob(os.path.join(g, f'glg_tte_{det}_*.fit')))


def download(url, dest):
    tmp = dest + '.part'
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r, open(tmp, 'wb') as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, dest)
    return os.path.getsize(dest)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--burst', default=None, help='single trigger')
    ap.add_argument('--limit', type=int, default=None, help='first N bursts only')
    args = ap.parse_args()

    man = Table.read(MANIFEST, format='ascii.ecsv')
    need = {}
    for r in man:
        trig = str(r['TRIGGER_NAME']).strip()
        det = str(r['DETECTOR']).strip()
        if args.burst and trig != args.burst:
            continue
        need.setdefault(trig, set()).add(det)
    trigs = sorted(need)
    if args.limit:
        trigs = trigs[:args.limit]

    n_ok = n_skip = n_miss = 0
    for i, trig in enumerate(trigs, 1):
        os.makedirs(os.path.join(DATA, trig), exist_ok=True)
        todo = sorted(d for d in need[trig] if not have_tte(trig, d))
        if not todo:
            n_skip += len(need[trig])
            print(f'[{i}/{len(trigs)}] {trig}: all present, skip')
            continue
        url = f'{ARCHIVE}/{year_of(trig)}/{trig}/current/'
        try:
            names = list_dir(url)
        except Exception as exc:
            print(f'[{i}/{len(trigs)}] {trig}: LISTING FAILED ({type(exc).__name__}: {exc})')
            n_miss += len(todo)
            continue
        for det in todo:
            fn = best_tte(names, trig, det)
            if fn is None:
                print(f'    {det}: NOT in archive listing')
                n_miss += 1
                continue
            dest = os.path.join(DATA, trig, fn)
            try:
                kb = download(url + fn, dest) / 1024
                print(f'    {det}: {fn} ({kb:.0f} KB)')
                n_ok += 1
            except Exception as exc:
                print(f'    {det}: DOWNLOAD FAILED ({type(exc).__name__}: {exc})')
                n_miss += 1

    print(f'\ndone: {n_ok} downloaded, {n_skip} already present, {n_miss} missing/failed')
    if n_miss:
        print('Some files are missing -- re-run to retry, or ask Vikas to share them.')
        sys.exit(1)


if __name__ == '__main__':
    main()
