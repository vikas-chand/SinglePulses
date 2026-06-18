#!/usr/bin/env python
"""
Upgrade the correlation fits to the Burgess/Mei standard: a Bayesian linear fit
in log-log with INTRINSIC SCATTER (D'Agostini 2005), reporting slope m,
normalization K at a pivot, intrinsic scatter sigma_sc, plus Spearman rho, p, N.
Also: per-burst slopes (where N>=3) and jet-composition classification from the
Ep-kT slope (baryonic m<1.5, magnetic m>=1.5, a la Burgess+2014).

Correlations (sample-wide, observer frame):
  - nu_m vs nu_c  (DSBPL two breaks)   [note orientation: log nu_m = m log nu_c + b]
  - Ep   vs kT    (BB+SBPL proxy)      [Burgess orientation: Ep ~ kT^m]
Outputs /tmp/intrinsic_fits.txt (+ json).
"""
import os, json, warnings
warnings.filterwarnings('ignore'); os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np
from astropy.table import Table
from scipy.stats import spearmanr
from scipy.optimize import minimize
try:
    import emcee; HAVE_EMCEE = True
except Exception:
    HAVE_EMCEE = False

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = Table.read(os.path.join(BASE,'results','sample_all_models.ecsv'), format='ascii.ecsv')
b = t[t['BLOCK'] >= 0]
XBB,XPB,EPB,KTB = (10,900),(30,5000),(30,5000),(1,200)
LRT=9.2

def col(name): return np.asarray(b[name], float) if name in b.colnames else np.full(len(b),np.nan)

def logerr(val, err):
    """symmetric error in log10 from value+error (fractional)."""
    val = np.asarray(val,float); err = np.asarray(err,float)
    err = np.where(np.isfinite(err) & (err>0), err, 0.15*np.abs(val))  # default 15%
    return err/(np.abs(val)*np.log(10))

def dagostini_fit(x, y, sx, sy, pivot):
    """log-log linear fit with intrinsic scatter. x,y already log10; sx,sy log10 errs.
    Model: y = m*(x-pivot) + c ; scatter s. Returns dict with m, c, s_sc, K=10^c, errs."""
    def negln(p):
        m, c, ls = p; s2 = np.exp(2*ls)
        V = sy**2 + (m*sx)**2 + s2
        r = y - (m*(x-pivot) + c)
        return 0.5*np.sum(r**2/V + np.log(2*np.pi*V))
    # init from OLS
    m0,c0 = np.polyfit(x-pivot, y, 1)
    res = minimize(negln, [m0, c0, np.log(np.std(y-(m0*(x-pivot)+c0))+1e-3)],
                   method='Nelder-Mead', options={'xatol':1e-4,'fatol':1e-4,'maxiter':5000})
    m,c,ls = res.x; s_sc = float(np.exp(ls))
    out = dict(m=float(m), c=float(c), s_sc=s_sc, K=float(10**c), pivot=float(pivot), N=len(x))
    if HAVE_EMCEE and len(x) >= 5:
        nw, nd = 24, 3
        p0 = np.array([m,c,ls]) + 1e-3*np.random.default_rng(0).standard_normal((nw,nd))
        def lnp(p):
            if not (-5<p[0]<5 and -10<p[1]<10 and -8<p[2]<3): return -np.inf
            return -negln(p)
        sm = emcee.EnsembleSampler(nw, nd, lnp)
        sm.run_mcmc(p0, 2000, progress=False)
        ch = sm.get_chain(discard=600, flat=True)
        out['m_err']  = float(np.std(ch[:,0]))
        out['s_sc_err']= float(np.std(np.exp(ch[:,2])))
        out['m'] = float(np.median(ch[:,0])); out['s_sc']=float(np.median(np.exp(ch[:,2])))
        out['K'] = float(10**np.median(ch[:,1]))
    else:
        out['m_err'] = np.nan; out['s_sc_err'] = np.nan
    return out

def cpl_peak(i,xc): return (2+i)*xc if i>-2 else np.nan

# ---------- gather pairs (with errors + per-burst burst id) ----------
# (A) DSBPL two breaks: nu_c=xb, nu_m=xp
A_xc=[];A_xm=[];A_exc=[];A_exm=[];A_trig=[]
for r in b:
    xc_,xp_=float(r['DSBPL_XB']),float(r['DSBPL_XP'])
    rail=(xc_<=XBB[0]*1.02 or xc_>=XBB[1]*0.98 or xp_<=XPB[0]*1.02 or xp_>=XPB[1]*0.98)
    if (bool(r['DSBPL_VALID']) and np.isfinite(xc_) and np.isfinite(xp_) and not rail and xc_<xp_
            and np.isfinite(r['LRT_DSBPL_SBPL']) and r['LRT_DSBPL_SBPL']>=LRT):
        A_xc.append(xc_);A_xm.append(xp_)
        A_exc.append(float(r['DSBPL_XB_ERR']) if 'DSBPL_XB_ERR' in b.colnames else np.nan)
        A_exm.append(float(r['DSBPL_XP_ERR']) if 'DSBPL_XP_ERR' in b.colnames else np.nan)
        A_trig.append(str(r['TRIGGER_NAME']))
# (B) BB proxy: kT, Ep (lower-AIC of Band+BB / CPL+BB)
B_kt=[];B_ep=[];B_ekt=[];B_eep=[];B_trig=[]
for r in b:
    cand=[]
    if bool(r['BANDBB_VALID']) and np.isfinite(r['LRT_BANDBB_BAND']) and r['LRT_BANDBB_BAND']>=LRT:
        kt,ep=float(r['BANDBB_KT']),float(r['BANDBB_EP'])
        if KTB[0]*1.02<kt<KTB[1]*0.98 and ep>EPB[0]*1.02:
            cand.append((float(r['BANDBB_AIC']),kt,ep,float(r['BANDBB_KT_ERR']),float(r['BANDBB_EP_ERR'])))
    if bool(r['CPLBB_VALID']) and np.isfinite(r['LRT_CPLBB_CPL']) and r['LRT_CPLBB_CPL']>=LRT:
        kt=float(r['CPLBB_KT']);ep=cpl_peak(float(r['CPLBB_INDEX']),float(r['CPLBB_XC']))
        if KTB[0]*1.02<kt<KTB[1]*0.98 and np.isfinite(ep) and ep>0:
            cand.append((float(r['CPLBB_AIC']),kt,ep,float(r['CPLBB_KT_ERR']),np.nan))
    if cand:
        cand.sort(); _,kt,ep,ekt,eep=cand[0]
        B_kt.append(kt);B_ep.append(ep);B_ekt.append(ekt);B_eep.append(eep);B_trig.append(str(r['TRIGGER_NAME']))

res={}
# (A) nu_m ~ nu_c^m   (x=nu_c, y=nu_m)
xc=np.array(A_xc);xm=np.array(A_xm)
fa=dagostini_fit(np.log10(xc),np.log10(xm),logerr(xc,np.array(A_exc)),logerr(xm,np.array(A_exm)),np.log10(100.))
fa['rho'],fa['p']=spearmanr(xc,xm); fa['relation']='nu_m ∝ nu_c^m (pivot nu_c=100 keV)'
res['A_num_vs_nuc']=fa
# (B) Ep ~ kT^m
kt=np.array(B_kt);ep=np.array(B_ep)
fb=dagostini_fit(np.log10(kt),np.log10(ep),logerr(kt,np.array(B_ekt)),logerr(ep,np.array(B_eep)),np.log10(10.))
fb['rho'],fb['p']=spearmanr(kt,ep); fb['relation']='Ep ∝ kT^m (pivot kT=10 keV)'
res['B_Ep_vs_kT']=fb

# ---------- per-burst slopes + jet composition (Ep-kT) ----------
def per_burst(trigs, X, Y, minN=3):
    trigs=np.array(trigs);X=np.array(X);Y=np.array(Y);out=[]
    for tr in sorted(set(trigs)):
        m=trigs==tr
        if m.sum()>=minN:
            s=np.polyfit(np.log10(X[m]),np.log10(Y[m]),1)[0]
            out.append((tr,int(m.sum()),float(s)))
    return out
pb_ept=per_burst(B_trig,B_kt,B_ep)
pb_num=per_burst(A_trig,A_xc,A_xm)

L=[]
L.append(f"INTRINSIC-SCATTER FITS (D'Agostini; emcee={HAVE_EMCEE})")
def show(tag):
    r=res[tag]
    L.append(f"{r['relation']}")
    L.append(f"   N={r['N']}  m={r['m']:.2f}±{r.get('m_err',float('nan')):.2f}  "
             f"K={r['K']:.2f}  sigma_sc={r['s_sc']:.2f}±{r.get('s_sc_err',float('nan')):.2f} dex  "
             f"rho={r['rho']:.2f}  p={r['p']:.1e}")
show('A_num_vs_nuc'); show('B_Ep_vs_kT')
L.append("")
L.append(f"PER-BURST Ep-kT slopes (N>=3 sig bins): {len(pb_ept)} bursts")
for tr,n,s in pb_ept:
    jet='baryonic' if s<1.5 else 'magnetic'
    L.append(f"   {tr}: N={n} slope={s:.2f} -> {jet}")
nbary=sum(1 for _,_,s in pb_ept if s<1.5); nmag=len(pb_ept)-nbary
L.append(f"   -> baryonic:{nbary} magnetic:{nmag}")
L.append(f"PER-BURST nu_m-nu_c slopes (N>=3): {len(pb_num)} bursts")
for tr,n,s in pb_num: L.append(f"   {tr}: N={n} slope={s:.2f}")
rep="\n".join(L); open('/tmp/intrinsic_fits.txt','w').write(rep+"\n")
json.dump({'fits':res,'per_burst_EpkT':pb_ept,'per_burst_numnuc':pb_num},
          open('/tmp/intrinsic_fits.json','w'),indent=1,default=float)
print(rep)
