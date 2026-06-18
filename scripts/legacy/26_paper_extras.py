#!/usr/bin/env python
"""Extras for the elevated ApJ draft:
 (1) nuFnu time-resolved spectral-evolution figure for GRB130427A (Burgess Fig.2 analog)
 (2) low-energy photon-index distribution vs synchrotron lines-of-death (-2/3, -3/2)
 (3) authoritative curvature split at dAIC>6 AND dAIC>=10 (reconcile 78/22)
 (4) F_BB/F_tot for BB-significant bins (Burgess Table 1 column)
 (5) per-burst Ep-kT table rows (N>=5) with jet type
"""
import os, json, warnings, importlib.util
warnings.filterwarnings('ignore'); os.environ.setdefault('OMP_NUM_THREADS','1')
_FD='/Users/salim/anaconda3/envs/threeML/share/fermitools'
for k,v in {'FERMI_DIR':_FD,'CALDB':_FD+'/data/caldb','CALDBALIAS':_FD+'/data/caldb/software/tools/alias_config.fits','CALDBCONFIG':_FD+'/data/caldb/software/tools/caldb.config','CALDBROOT':_FD+'/data/caldb','EXTFILESSYS':_FD+'/refdata/fermi'}.items(): os.environ[k]=v
import numpy as np
from astropy.table import Table
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm

BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG=os.path.join(BASE,'results','figures')
spec=importlib.util.spec_from_file_location('s10',os.path.join(BASE,'scripts','10_spectral_fit_burst.py'))
s10=importlib.util.module_from_spec(spec); spec.loader.exec_module(s10)
BUILD={s['name']:s['build'] for s in s10.MODEL_SPECS}
EG=np.logspace(np.log10(8),np.log10(40000),400); K2E=1.602176634e-9

def seed(r,m):
    d={'Band':{'band_alpha':r['BAND_ALPHA'],'band_Ep':r['BAND_EP'],'band_beta':r['BAND_BETA'],'band_K':r['BAND_K']},
       'CPL':{'cpl_index':r['CPL_INDEX'],'cpl_xc':r['CPL_XC'],'cpl_K':r['CPL_K']},
       'SBPL':{'sbpl_alpha':r['SBPL_ALPHA'],'sbpl_break':r['SBPL_EBREAK'],'sbpl_beta':r['SBPL_BETA'],'sbpl_K':r['SBPL_K']},
       'DSBPL':{'dsbpl_alpha1':r['DSBPL_ALPHA1'],'dsbpl_xb':r['DSBPL_XB'],'dsbpl_alpha2':r['DSBPL_ALPHA2'],'dsbpl_xp':r['DSBPL_XP'],'dsbpl_beta':r['DSBPL_BETA'],'dsbpl_K':r['DSBPL_K']},
       'Band+BB':{'band_alpha':r['BANDBB_ALPHA'],'band_Ep':r['BANDBB_EP'],'band_beta':r['BANDBB_BETA'],'band_K':r['BANDBB_K_BAND'],'bb_kT':r['BANDBB_KT'],'bb_K':r['BANDBB_K_BB']},
       'CPL+BB':{'cpl_index':r['CPLBB_INDEX'],'cpl_xc':r['CPLBB_XC'],'cpl_K':r['CPLBB_K_CPL'],'bb_kT':r['CPLBB_KT'],'bb_K':r['CPLBB_K_BB']}}
    return d.get(m)
def nuFnu(r,m):
    sd=seed(r,m)
    if sd is None or any(not np.isfinite(v) for v in sd.values()): return None
    fn=BUILD[m](sd); NE=np.asarray(fn(EG),float)
    return EG*EG*NE*K2E  # keV^2 * ph/cm2/s/keV -> ~ erg-ish nuFnu (arb. but consistent)

# ---------- (1) nuFnu evolution of GRB130427A ----------
trig='bn130427324'
t=Table.read(os.path.join(BASE,'results','per_burst',trig,'spectral_fits.ecsv'),format='ascii.ecsv')
b=t[t['BLOCK']>=0]; b.sort('T_START')
tc=0.5*(np.asarray(b['T_START'],float)+np.asarray(b['T_STOP'],float))
norm=(tc-tc.min())/(tc.max()-tc.min()+1e-9)
fig,ax=plt.subplots(figsize=(7,5.2))
nplot=0
for r,frac in zip(b,norm):
    y=nuFnu(r,str(r['BEST_AIC_MODEL']))
    if y is None or not np.all(np.isfinite(y)): continue
    ax.plot(EG,y/np.nanmax(y),color=cm.plasma(frac),lw=0.8,alpha=0.7); nplot+=1
ax.set_xscale('log'); ax.set_yscale('log'); ax.set_ylim(1e-3,2)
ax.set_xlabel('Energy [keV]'); ax.set_ylabel(r'$\nu F_\nu$ (peak-normalized)')
ax.set_title(f'GRB 130427A — time-resolved $\\nu F_\\nu$ evolution ({nplot} bins)')
sm=cm.ScalarMappable(cmap='plasma'); sm.set_array([tc.min(),tc.max()])
cb=fig.colorbar(sm,ax=ax); cb.set_label('time since trigger [s]')
ax.tick_params(direction='in',which='both',top=True,right=True); ax.minorticks_on()
fig.tight_layout(); fig.savefig(f'{FIG}/fig_nufnu_evolution_130427A.png',dpi=170,bbox_inches='tight'); plt.close(fig)
print('wrote fig_nufnu_evolution_130427A.png  (',nplot,'bins )')

# ---------- (2) low-energy index distribution ----------
S=Table.read(os.path.join(BASE,'results','sample_all_models.ecsv'),format='ascii.ecsv')
sb=S[S['BLOCK']>=0]
ba=np.asarray(sb['BAND_ALPHA'],float); sa=np.asarray(sb['SBPL_ALPHA'],float); ci=np.asarray(sb['CPL_INDEX'],float)
fig,ax=plt.subplots(figsize=(7,4.6))
for arr,lab,c in [(ba,'Band $\\alpha$','#1f77b4'),(ci,'CPL index','#2ca02c'),(sa,'SBPL $\\alpha$','#d62728')]:
    a=arr[np.isfinite(arr)&(arr>-3)&(arr<2)]
    ax.hist(a,bins=40,histtype='step',lw=1.6,label=f'{lab} (med {np.median(a):.2f})',color=c)
ax.axvline(-2/3,ls='--',color='0.4',label='$-2/3$ slow-cooled'); ax.axvline(-3/2,ls=':',color='0.4',label='$-3/2$ fast-cooled')
ax.set_xlabel('low-energy photon index'); ax.set_ylabel('time bins')
ax.set_title('Low-energy index vs synchrotron lines-of-death')
ax.legend(fontsize=8); ax.tick_params(direction='in',which='both',top=True,right=True); ax.minorticks_on()
fig.tight_layout(); fig.savefig(f'{FIG}/fig_lowE_index.png',dpi=170,bbox_inches='tight'); plt.close(fig)
ba_med=np.nanmedian(ba[np.isfinite(ba)&(ba>-3)&(ba<2)])
print(f'wrote fig_lowE_index.png   Band-alpha median={ba_med:.2f}')

# ---------- (3) curvature split at dAIC>6 and >=10 ----------
MOD=['BAND','CPL','SBPL','DSBPL','BANDBB','CPLBB']
def split(thr):
    nc=nt=n2=nd=0
    for r in sb:
        a={m:float(r[f'{m}_AIC']) for m in MOD}
        if not np.all(np.isfinite(list(a.values()))):
            a={m:v for m,v in a.items() if np.isfinite(v)}
        best_single=min(a.get('BAND',1e9),a.get('CPL',1e9),a.get('SBPL',1e9))
        therm=min(a.get('BANDBB',1e9),a.get('CPLBB',1e9)); twob=a.get('DSBPL',1e9)
        if min(therm,twob)<best_single-thr:
            nc+=1
            if abs(therm-twob)<=thr: nd+=1
            elif therm<twob: nt+=1
            else: n2+=1
    return nc,nt,nd,n2
for thr in (6,10):
    nc,nt,nd,n2=split(thr)
    print(f'dAIC>{thr}: curvature-required={nc}  thermal-proxy={nt}  degenerate={nd}  two-break={n2}'
          f'  ({100*(nt+nd)/max(nc,1):.0f}% thermal-or-degenerate)')

# ---------- (4) F_BB/F_tot for BB-significant bins ----------
def bbfrac(r):
    # use the +BB model that is BB-significant (prefer lower AIC)
    cands=[]
    if bool(r['BANDBB_VALID']) and np.isfinite(r['LRT_BANDBB_BAND']) and r['LRT_BANDBB_BAND']>=9.2:
        cands.append(('Band+BB',float(r['BANDBB_AIC']),
                      {'bb_kT':r['BANDBB_KT'],'bb_K':r['BANDBB_K_BB']},
                      {'band_alpha':r['BANDBB_ALPHA'],'band_Ep':r['BANDBB_EP'],'band_beta':r['BANDBB_BETA'],'band_K':r['BANDBB_K_BAND']}))
    if bool(r['CPLBB_VALID']) and np.isfinite(r['LRT_CPLBB_CPL']) and r['LRT_CPLBB_CPL']>=9.2:
        cands.append(('CPL+BB',float(r['CPLBB_AIC']),
                      {'bb_kT':r['CPLBB_KT'],'bb_K':r['CPLBB_K_BB']},
                      {'cpl_index':r['CPLBB_INDEX'],'cpl_xc':r['CPLBB_XC'],'cpl_K':r['CPLBB_K_CPL']}))
    if not cands: return np.nan
    cands.sort(key=lambda c:c[1]); name,_,bbsd,_=cands[0]
    try:
        bb=s10._setup_bb({'bb_kT':float(bbsd['bb_kT']),'bb_K':float(bbsd['bb_K'])})
        tot=BUILD[name](seed(r,name))
        Fbb=np.trapz(EG*np.asarray(bb(EG),float),EG); Ftot=np.trapz(EG*np.asarray(tot(EG),float),EG)
        return float(Fbb/Ftot) if Ftot>0 else np.nan
    except Exception: return np.nan
fr=np.array([bbfrac(r) for r in sb]); fr=fr[np.isfinite(fr)&(fr>0)&(fr<1)]
print(f'F_BB/F_tot (BB-sig bins): N={len(fr)} median={np.median(fr):.2f} '
      f'range[{np.percentile(fr,16):.2f},{np.percentile(fr,84):.2f}]  (Burgess: 0.27-0.39)')

# ---------- (5) per-burst Ep-kT table (N>=5) ----------
try:
    pb=json.load(open('/tmp/intrinsic_fits.json'))['per_burst_EpkT']
    print('\nPer-burst Ep-kT (N>=5):')
    for tr,n,s in pb:
        if n>=5: print(f'  {tr}  N={n}  alpha={s:.2f}  {"baryonic" if s<1.5 else "magnetic"}')
except Exception as e:
    print('per-burst table: rerun script 25 first', e)
