#!/usr/bin/env python
"""
Phase 0b: full-sample re-fit on the CLEAN foundation.
For all 106 bursts, run scripts/10 with:
  --blocks-file results/clean_blocks/...   (uniform clean Bayesian blocks)
  --bkg-file    results/background_intervals_clean.ecsv  (corrected backgrounds)
  --out-dir     results/clean_per_burst/<trig>
  --include-bgo (NaI+BGO+LLE; BB multi-start is built into scripts/10)
Resumable: skips bursts whose spectral_fits.ecsv already exists. Parallel.
Per-burst timeout guards against a hung BB on extreme-count bursts.
"""
import os, glob, sys, time, subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS=os.path.join(BASE,'scripts'); RES=os.path.join(BASE,'results')
PY='/Users/salim/anaconda3/envs/threeML/bin/python'
S10=os.path.join(SCRIPTS,'10_spectral_fit_burst.py')
CLEANBLK=os.path.join(RES,'clean_blocks'); CLEANBKG=os.path.join(RES,'background_intervals_clean.ecsv')
OUTROOT=os.path.join(RES,'clean_per_burst'); os.makedirs(OUTROOT,exist_ok=True)
NPROC=int(os.environ.get('NPROC','8')); TIMEOUT=7200
_FD='/Users/salim/anaconda3/envs/threeML/share/fermitools'
ENV={**os.environ,'PYTHONUNBUFFERED':'1','MPLBACKEND':'Agg','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
     'FERMI_DIR':_FD,'CALDB':_FD+'/data/caldb','CALDBALIAS':_FD+'/data/caldb/software/tools/alias_config.fits',
     'CALDBCONFIG':_FD+'/data/caldb/software/tools/caldb.config','CALDBROOT':_FD+'/data/caldb','EXTFILESSYS':_FD+'/refdata/fermi'}

trigs=sorted(os.path.basename(f).split('bb_blocks_spectral_')[1].split('.ecsv')[0]
             for f in glob.glob(f'{CLEANBLK}/bb_blocks_spectral_*.ecsv'))

def run(trig):
    out=os.path.join(OUTROOT,trig); os.makedirs(out,exist_ok=True)
    done=os.path.join(out,'spectral_fits.ecsv')
    if os.path.exists(done): return (trig,'skip',0)
    blk=os.path.join(CLEANBLK,f'bb_blocks_spectral_{trig}.ecsv')
    log=os.path.join(out,'refit.log')
    cmd=[PY,S10,'--trigger',trig,'--include-bgo','--no-log',
         '--blocks-file',blk,'--bkg-file',CLEANBKG,'--out-dir',out]
    t0=time.time()
    try:
        with open(log,'w') as lf:
            subprocess.run(cmd,stdout=lf,stderr=subprocess.STDOUT,env=ENV,timeout=TIMEOUT,check=False)
    except subprocess.TimeoutExpired:
        return (trig,'TIMEOUT',time.time()-t0)
    return (trig, 'ok' if os.path.exists(done) else 'FAIL', time.time()-t0)

if __name__=='__main__':
    todo=[t for t in trigs if not os.path.exists(os.path.join(OUTROOT,t,'spectral_fits.ecsv'))]
    print(f'{len(trigs)} bursts, {len(todo)} to fit ({len(trigs)-len(todo)} already done), {NPROC} workers',flush=True)
    n_ok=n_fail=0
    with ProcessPoolExecutor(max_workers=NPROC) as ex:
        futs={ex.submit(run,t):t for t in trigs}
        for fu in as_completed(futs):
            trig,st,dt=fu.result()
            if st in ('ok','skip'): n_ok+=1
            else: n_fail+=1
            print(f'[{n_ok+n_fail}/{len(trigs)}] {trig}: {st} ({dt:.0f}s)',flush=True)
    print(f'\nDONE: {n_ok} ok/skip, {n_fail} failed. -> {OUTROOT}',flush=True)
