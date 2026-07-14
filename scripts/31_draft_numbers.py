#!/usr/bin/env python
"""
31_draft_numbers.py  --  Compute every population number the Li-style draft needs,
from the PROVISIONAL clean re-fit (results/clean_per_burst/, corrected backgrounds
+ clean blocks + multi-start BB engine).  Output: results/draft_numbers.json + a
printed summary.  THESE ARE PROVISIONAL (pending Khushboo's human backgrounds).

Flux is integrated with astromodels over 10-1000 keV; needs the threeML env with
CALDB pointed at the env (see the bash wrapper).
"""
import glob, os, json, warnings
import numpy as np
from astropy.table import Table, vstack
import astromodels as am
from scipy import stats, odr

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEV2ERG = 1.602176634e-9
EGRID = np.geomspace(10.0, 1000.0, 400)   # GBM NaI band for flux

# per-burst fit root + output tag are env-overridable (authoritative consensus run
# uses FIT_ROOT=results/clean_per_burst_consensus so the provisional dir is untouched)
CPB = os.environ.get("FIT_ROOT", os.path.join(ROOT, "results/clean_per_burst"))
OTAG = os.environ.get("OUT_TAG", "")

# ---------- 1. combine clean_per_burst, tag trigger from dir ----------
rows = []
for f in sorted(glob.glob(f"{CPB}/*/spectral_fits.ecsv")):
    trig = os.path.basename(os.path.dirname(f))
    t = Table.read(f, format="ascii.ecsv")
    t["TRIGGER"] = trig
    rows.append(t)
T = vstack(rows)
T = T[T["BLOCK"] >= 0]                      # real time bins only
T.write(f"{ROOT}/results/clean_sample_all_models{OTAG}.ecsv", format="ascii.ecsv", overwrite=True)

def g(row, col):
    try:
        v = row[col]
        return float(v) if np.isfinite(float(v)) else np.nan
    except Exception:
        return np.nan

def vb(row, col):
    try:
        return bool(row[col])
    except Exception:
        return False

# ---------- flux integrators (astromodels, exact fit params) ----------
# widen default bounds so steep fitted indices (alpha<-1.5 etc.) still integrate
# over the finite 10-1000 keV band; bounds are astromodels guards, not physics here.
def eflux_band(K, alpha, Ep, beta):
    fn = am.Band()
    fn.alpha.bounds = (-20, 10); fn.beta.bounds = (-20, 0); fn.xp.bounds = (1, 1e6)
    fn.K = K; fn.alpha = alpha; fn.xp = Ep; fn.beta = beta; fn.piv = 100.0
    N = fn(EGRID)
    return np.trapz(N * EGRID, EGRID) * KEV2ERG, np.trapz(N, EGRID)   # erg flux, photon flux

def eflux_cpl(K, index, xc):
    fn = am.Cutoff_powerlaw()
    fn.index.bounds = (-20, 10); fn.xc.bounds = (0.1, 1e7)
    fn.K = K; fn.index = index; fn.xc = xc; fn.piv = 100.0
    N = fn(EGRID)
    return np.trapz(N * EGRID, EGRID) * KEV2ERG, np.trapz(N, EGRID)

def eflux_bb(K, kT):
    fn = am.Blackbody(); fn.kT.bounds = (0.01, 1e5)
    fn.K = K; fn.kT = kT
    N = fn(EGRID)
    return np.trapz(N * EGRID, EGRID) * KEV2ERG, np.trapz(N, EGRID)

# ---------- 2. per-block reduction ----------
per = []   # one dict per valid Band block
for r in T:
    d = {"trig": str(r["TRIGGER"]), "block": int(r["BLOCK"]), "tmid": g(r, "T_MID")}
    # Band reference (alpha, Ep, flux) -- always our reference continuum.
    # Capture alpha/Ep/beta from the catalog INDEPENDENTLY of flux integration so
    # the parameter distributions are unbiased even where flux integration fails.
    if vb(r, "BAND_VALID"):
        a, Ep, be, K = g(r,"BAND_ALPHA"), g(r,"BAND_EP"), g(r,"BAND_BETA"), g(r,"BAND_K")
        if np.all(np.isfinite([a, Ep, be])):
            d.update(alpha=a, Ep=Ep, beta=be)
        if np.all(np.isfinite([a, Ep, be, K])):
            try:
                F, Fph = eflux_band(K, a, Ep, be)
                d.update(F=F, Fph=Fph)
            except Exception:
                pass
    # best AIC model -- only count winners that pass the physical-validity gate
    # (scripts/10 has a silent fallback that lets a railed model win in ~4% of bins)
    bm = str(r["BEST_AIC_MODEL"]) if r["BEST_AIC_MODEL"] is not None else ""
    BMCOL = {"Band":"BAND","CPL":"CPL","SBPL":"SBPL","DSBPL":"DSBPL",
             "Band+BB":"BANDBB","CPL+BB":"CPLBB"}
    d["best"] = bm if (bm in BMCOL and vb(r, BMCOL[bm]+"_VALID")) else ""
    # +BB significance: dAIC>=10 vs the parent continuum (= LRT>=14 for 2 extra
    # params; Li+2021 dDIC>=10 analog). Take Band+BB if it passes, else CPL+BB.
    LRT_SIG = 14.0   # dAIC>=10  <=>  LRT >= 10 + 2*Dk, Dk=2
    kT = np.nan; fbb = np.nan
    if vb(r, "BANDBB_VALID") and g(r,"LRT_BANDBB_BAND") >= LRT_SIG:
        kT = g(r, "BANDBB_KT")
        try:
            Fc,_ = eflux_band(g(r,"BANDBB_K_BAND"), g(r,"BANDBB_ALPHA"), g(r,"BANDBB_EP"), g(r,"BANDBB_BETA"))
            Fb,_ = eflux_bb(g(r,"BANDBB_K_BB"), kT)
            fbb = Fb/(Fb+Fc) if (Fb+Fc) > 0 else np.nan
        except Exception:
            pass
    elif vb(r, "CPLBB_VALID") and g(r,"LRT_CPLBB_CPL") >= LRT_SIG:
        kT = g(r, "CPLBB_KT")
        try:
            Fc,_ = eflux_cpl(g(r,"CPLBB_K_CPL"), g(r,"CPLBB_INDEX"), g(r,"CPLBB_XC"))
            Fb,_ = eflux_bb(g(r,"CPLBB_K_BB"), kT)
            fbb = Fb/(Fb+Fc) if (Fb+Fc) > 0 else np.nan
        except Exception:
            pass
    d["kT"] = kT; d["fbb"] = fbb
    # dBIC cross-check: BB passes the (conservative, inflated-N) stored BIC?
    d["bb_dbic"] = bool((vb(r,"BANDBB_VALID") and np.isfinite(g(r,"BANDBB_BIC")) and np.isfinite(g(r,"BAND_BIC")) and g(r,"BANDBB_BIC") < g(r,"BAND_BIC"))
                        or (vb(r,"CPLBB_VALID") and np.isfinite(g(r,"CPLBB_BIC")) and np.isfinite(g(r,"CPL_BIC")) and g(r,"CPLBB_BIC") < g(r,"CPL_BIC")))
    # DSBPL breaks (nu_c=xb, nu_m=xp)
    if vb(r, "DSBPL_VALID"):
        xb, xp = g(r,"DSBPL_XB"), g(r,"DSBPL_XP")
        if np.isfinite(xb) and np.isfinite(xp) and 0 < xb < xp:
            d["xb"] = xb; d["xp"] = xp; d["lrt_2break"] = g(r,"LRT_DSBPL_SBPL")
    # ---- curvature classification (gated) ----
    singles = [g(r,c) for c,v in [("BAND_AIC","BAND_VALID"),("CPL_AIC","CPL_VALID"),
                                   ("SBPL_AIC","SBPL_VALID")] if vb(r,v) and np.isfinite(g(r,c))]
    curv = {}
    if vb(r,"DSBPL_VALID") and np.isfinite(g(r,"DSBPL_AIC")): curv["DSBPL"]=g(r,"DSBPL_AIC")
    if vb(r,"BANDBB_VALID") and g(r,"LRT_BANDBB_BAND")>0 and np.isfinite(g(r,"BANDBB_AIC")): curv["BANDBB"]=g(r,"BANDBB_AIC")
    if vb(r,"CPLBB_VALID") and g(r,"LRT_CPLBB_CPL")>0 and np.isfinite(g(r,"CPLBB_AIC")): curv["CPLBB"]=g(r,"CPLBB_AIC")
    if singles and curv:
        s = min(singles); cname = min(curv, key=curv.get); c = curv[cname]
        d["dAIC"] = s - c            # >0 => curvature preferred
        d["curv_winner"] = cname
        # genuine two-break: DSBPL wins AND dAIC(DSBPL vs SBPL)>=10 (= LRT>=14),
        # harmonized with the +BB significance rule. NOTE: DSBPL has no
        # convergence guard in scripts/10, so this count is a LOWER LIMIT.
        genuine = (cname=="DSBPL" and "xb" in d and g(r,"LRT_DSBPL_SBPL")>=14.0)
        d["genuine_two_break"] = bool(genuine)
    per.append(d)

P = Table(rows=[{k:dd.get(k,np.nan) for k in
    ["trig","block","tmid","alpha","Ep","beta","F","Fph","best","kT","fbb",
     "xb","xp","dAIC","curv_winner","genuine_two_break","lrt_2break","bb_dbic"]} for dd in per])

# ---------- 3. statistics ----------
out = {}
out["n_bursts"] = len(set(P["trig"]))
out["n_spec"] = len(P)
# bins per burst -> tiers
import collections
cnt = collections.Counter(P["trig"])
gold   = [k for k,v in cnt.items() if v >= 10]
silver = [k for k,v in cnt.items() if 5 <= v <= 9]
bronze = [k for k,v in cnt.items() if v <= 4]
out["tiers"] = {"gold":len(gold),"silver":len(silver),"bronze":len(bronze),
                "gold_bins":int(sum(cnt[k] for k in gold)),
                "silver_bins":int(sum(cnt[k] for k in silver)),
                "bronze_bins":int(sum(cnt[k] for k in bronze))}
out["bins_per_burst"] = {"median":float(np.median(list(cnt.values()))),
                         "min":int(min(cnt.values())),"max":int(max(cnt.values()))}

def fin(a):
    a=np.asarray(a,float); return a[np.isfinite(a)]
al = fin(P["alpha"]); ep = fin(P["Ep"]); be = fin(P["beta"])
out["alpha"] = {"n":len(al),"median":float(np.median(al)),
                "q1":float(np.percentile(al,25)),"q3":float(np.percentile(al,75)),
                "frac_above_2_3":float(np.mean(al > -2/3)),
                "frac_above_3_2":float(np.mean(al > -3/2))}
out["Ep"] = {"n":len(ep),"median":float(np.median(ep)),
             "min":float(np.min(ep)),"max":float(np.max(ep)),
             "q1":float(np.percentile(ep,25)),"q3":float(np.percentile(ep,75))}
out["beta"] = {"n":len(be),"median":float(np.median(be))}

# model census
mc = collections.Counter([b for b in P["best"] if b])
out["best_model_census"] = {k:int(v) for k,v in mc.most_common()}

# curvature split
dA = np.asarray(P["dAIC"],float); gtb = np.asarray(P["genuine_two_break"],float)
def split(thr):
    sel = np.isfinite(dA) & (dA > thr)
    n = int(sel.sum())
    tb = int(np.nansum(gtb[sel]))
    return {"n_curv_required":n, "two_break":tb, "thermal_or_degen":n-tb,
            "frac_two_break":(tb/n if n else np.nan),
            "frac_thermal":((n-tb)/n if n else np.nan)}
out["curvature_split_dAIC6"]  = split(6)
out["curvature_split_dAIC10"] = split(10)
out["n_blocks_with_curv_test"] = int(np.isfinite(dA).sum())

# F_BB/F_tot
fbb = fin(P["fbb"])
out["fbb"] = {"n":len(fbb),"median":float(np.median(fbb)),
              "q1":float(np.percentile(fbb,25)),"q3":float(np.percentile(fbb,75))}

# ---- correlations (Band reference) ----
def sp(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float); m=np.isfinite(x)&np.isfinite(y)
    if m.sum()<5: return {"n":int(m.sum())}
    rho,p=stats.spearmanr(x[m],y[m]); return {"n":int(m.sum()),"rho":float(rho),"p":float(p)}

A=np.asarray(P["alpha"],float); EP=np.asarray(P["Ep"],float)
F=np.asarray(P["F"],float); FP=np.asarray(P["Fph"],float)
m=np.isfinite(A)&np.isfinite(F)
# F-alpha exponential: ln F = ln F0 + k alpha
if m.sum()>=5:
    k,lnF0=np.polyfit(A[m],np.log(F[m]),1)
    out["F_alpha"]={**sp(A,F),"k":float(k),"F0":float(np.exp(lnF0)),
                    "pearson":float(stats.pearsonr(A[m],np.log(F[m]))[0])}
# F-Ep power law (energy flux AND photon flux -> induction test)
mm=np.isfinite(np.log(EP))&np.isfinite(np.log(F))
if mm.sum()>=5:
    s,_=np.polyfit(np.log10(EP[mm]),np.log10(F[mm]),1)
    out["F_Ep_energy"]={**sp(EP,F),"slope":float(s)}
out["F_Ep_photon"]=sp(EP,FP)
# alpha-Ep
out["alpha_Ep"]=sp(EP,A)   # vs Ep (use log via spearman rank-invariant)
# kT-flux (energy & photon) -- Mei induction test
KT=np.asarray(P["kT"],float)
out["kT_Fenergy"]=sp(F,KT); out["kT_Fphoton"]=sp(FP,KT)
out["Ep_Fenergy"]=sp(F,EP); out["Ep_Fphoton"]=sp(FP,EP)

# ---- nu_m - nu_c (two-break) ----
def dagostini(x, y, sx, sy):
    """True D'Agostini (2005) errors-in-both-variables fit with free intrinsic
    scatter: minimize -2lnL with sigma_eff^2 = sig_sc^2 + sy^2 + m^2 sx^2.
    Returns (m, m_err, c, sig_sc) with errors from the BFGS inverse Hessian."""
    from scipy.optimize import minimize
    def nll(th):
        mm, cc, lns = th
        s2 = np.exp(2*lns) + sy**2 + mm**2 * sx**2
        return 0.5*np.sum(np.log(2*np.pi*s2) + (y - mm*x - cc)**2 / s2)
    sl0, c0 = np.polyfit(x, y, 1)
    res = minimize(nll, [sl0, c0, np.log(max(np.std(y - sl0*x - c0), 1e-3))],
                   method="BFGS")
    mm, cc, lns = res.x
    merr = float(np.sqrt(res.hess_inv[0, 0])) if res.hess_inv is not None else np.nan
    return float(mm), merr, float(cc), float(np.exp(lns))

XB=np.asarray(P["xb"],float); XP=np.asarray(P["xp"],float)
# break errors from the combined catalog (P is built row-for-row from T)
assert len(P)==len(T)
EXB=np.asarray(T["DSBPL_XB_ERR"],float); EXP=np.asarray(T["DSBPL_XP_ERR"],float)
m=np.isfinite(XB)&np.isfinite(XP)
nb={"n":int(m.sum())}
if m.sum()>=5:
    lxb,lxp=np.log10(XB[m]),np.log10(XP[m])
    rho,p=stats.spearmanr(lxb,lxp)
    # estimator 1: OLS
    sl_ols=float(np.polyfit(lxb,lxp,1)[0])
    # estimator 2: unweighted ODR (symmetric)
    dat=odr.RealData(lxb,lxp); od=odr.ODR(dat,odr.Model(lambda B,x:B[0]*x+B[1]),beta0=[1,0])
    o=od.run()
    resid=lxp-(o.beta[0]*lxb+o.beta[1])
    # estimator 3 (PRIMARY): true D'Agostini with per-point dex errors
    sx=EXB[m]/(XB[m]*np.log(10)); sy=EXP[m]/(XP[m]*np.log(10))
    ok=np.isfinite(sx)&np.isfinite(sy)&(sx>0)&(sy>0)
    da_m,da_me,da_c,da_s = dagostini(lxb[ok],lxp[ok],sx[ok],sy[ok])
    nb={"n":int(m.sum()),"rho":float(rho),"p":float(p),
        "dagostini":{"slope":da_m,"slope_err":da_me,"norm":da_c,
                     "sigma_sc_dex":da_s,"n":int(ok.sum())},
        "odr_slope":float(o.beta[0]),"odr_slope_err":float(o.sd_beta[0]),
        "odr_scatter":float(np.std(resid)),"ols_slope":sl_ols,
        "norm":float(o.beta[1]),
        # legacy keys (= ODR values) kept for backward compat
        "slope":float(o.beta[0]),"slope_err":float(o.sd_beta[0]),
        "sigma_sc_dex":float(np.std(resid))}
    # constrained subset (both breaks with rel. error < 1) -- robustness
    mc=m&np.isfinite(EXB)&np.isfinite(EXP)&(EXB<XB)&(EXP<XP)
    if mc.sum()>=5:
        lxbc,lxpc=np.log10(XB[mc]),np.log10(XP[mc])
        rc,pc=stats.spearmanr(lxbc,lxpc)
        sxc=EXB[mc]/(XB[mc]*np.log(10)); syc=EXP[mc]/(XP[mc]*np.log(10))
        dm,dme,dc_,ds=dagostini(lxbc,lxpc,sxc,syc)
        nb["constrained"]={"n":int(mc.sum()),"rho":float(rc),"p":float(pc),
                           "dagostini_slope":dm,"dagostini_slope_err":dme,
                           "dagostini_sigma":ds}
    # boundary robustness: exclude nu_c within ~2x the 8-keV NaI fit edge
    mb=m&(XB>=15.0)
    if mb.sum()>=5:
        rb_,pb_=stats.spearmanr(np.log10(XB[mb]),np.log10(XP[mb]))
        nb["xb_gt15keV"]={"n":int(mb.sum()),"rho":float(rb_),"p":float(pb_),
                          "frac_below_15keV":float(np.mean(XB[m]<15.0))}
    # within/between decomposition
    trig=np.asarray(P["trig"])[m]
    bursts=np.unique(trig)
    bx=[];by=[];wx=[];wy=[]
    for bn in bursts:
        s=trig==bn
        if s.sum()>=1:
            bx.append(np.mean(lxb[s])); by.append(np.mean(lxp[s]))
        if s.sum()>=3:
            wx.extend(lxb[s]-np.mean(lxb[s])); wy.extend(lxp[s]-np.mean(lxp[s]))
    if len(bx)>=5:
        rb,pb=stats.spearmanr(bx,by); nb["between"]={"n":len(bx),"rho":float(rb),"p":float(pb)}
    if len(wx)>=5:
        rw,pw=stats.spearmanr(wx,wy); nb["within"]={"n":len(wx),"rho":float(rw),"p":float(pw)}
out["nu_m_nu_c"]=nb

# ---- spectral evolution classification: RISE-PHASE discriminator ----
# Lu+2012/Basak+2014 physics: HTS = Ep is already maximal at pulse onset and
# decays; IT = Ep RISES with the flux during the rising phase. The whole-pulse
# Ep-flux correlation cannot separate them (both decay together in a FRED tail),
# so we classify on the pre-peak behavior and fall back to the Ep-maximum
# position when the rise is under-sampled.
trig=np.asarray(P["trig"])          # restore full-length (was masked above)
TM=np.asarray(P["tmid"],float)
evo={"HTS":0,"IT":0,"ambiguous":0,"tested":0,"detail":[]}
for bn in np.unique(trig):
    s=(trig==bn)&np.isfinite(EP)&np.isfinite(TM)&np.isfinite(FP)
    if s.sum()<4: continue
    evo["tested"]+=1
    o=np.argsort(TM[s]); t=TM[s][o]; ep=EP[s][o]; fp=FP[s][o]
    ipk=int(np.argmax(fp))                  # flux-peak bin
    iep=int(np.argmax(ep))                  # Ep-peak bin
    r_t,_=stats.spearmanr(t,ep)             # whole-pulse Ep trend
    cls="ambiguous"; r_rise=np.nan
    if ipk>=2:                              # >=3 bins through the flux peak
        r_rise,_=stats.spearmanr(t[:ipk+1],ep[:ipk+1])
        if   r_rise>=0.5:  cls="IT"         # Ep rising into the peak
        elif r_rise<=-0.5: cls="HTS"        # Ep falling from the start
    if cls=="ambiguous":                    # under-sampled rise: Ep-max position
        if   iep==0 and r_t<0:  cls="HTS"   # hardest at onset, decaying
        elif iep>=ipk and ipk>0: cls="IT"   # Ep peaks with/after the flux peak
    evo[cls]+=1
    evo["detail"].append({"trig":bn,"n":int(len(t)),"i_fluxpeak":ipk,"i_Eppeak":iep,
                          "r_rise":(float(r_rise) if np.isfinite(r_rise) else None),
                          "r_Ep_time":float(r_t),"cls":cls})
out["evolution"]=evo
# sensitivity: counts under the old whole-pulse rules, both orderings
def evo_wholepulse(it_first=True,thr=0.3):
    c={"HTS":0,"IT":0,"ambiguous":0}
    for bn in np.unique(trig):
        s=(trig==bn)&np.isfinite(EP)&np.isfinite(TM)&np.isfinite(FP)
        if s.sum()<4: continue
        r_t,_=stats.spearmanr(TM[s],EP[s]); r_f,_=stats.spearmanr(FP[s],EP[s])
        if it_first:
            cls="IT" if r_f>thr else ("HTS" if r_t<-thr else "ambiguous")
        else:
            cls="HTS" if r_t<-thr else ("IT" if r_f>thr else "ambiguous")
        c[cls]+=1
    return c
out["evolution_sensitivity"]={"wholepulse_IT_first":evo_wholepulse(True),
                              "wholepulse_HTS_first":evo_wholepulse(False)}

# ---- Burgess Ep-kT per burst ----
mm=np.isfinite(EP)&np.isfinite(KT)
trig=np.asarray(P["trig"])
perb=[]
for bn in np.unique(trig[mm]):
    s=mm&(trig==bn)
    if s.sum()>=4:
        rho,p=stats.spearmanr(EP[s],KT[s])
        perb.append({"trig":bn,"n":int(s.sum()),"rho":float(rho),"p":float(p)})
perb=sorted(perb,key=lambda d:-d["n"])
out["epkt_perburst"]={"n_bursts_tested":len(perb),
                      "frac_positive":float(np.mean([d["rho"]>0 for d in perb])) if perb else np.nan,
                      "n_sig_positive":int(np.sum([(d["rho"]>0 and d["p"]<0.05) for d in perb])),
                      "top":perb[:12]}
out["epkt_global"]=sp(EP,KT)
# 130427A Ep-kT slope, with the estimator stated (ODR + D'Agostini w/ errors)
s130=(trig=="bn130427324")&np.isfinite(EP)&np.isfinite(KT)
if s130.sum()>=5:
    lx,ly=np.log10(KT[s130]),np.log10(EP[s130])
    o=odr.ODR(odr.RealData(lx,ly),odr.Model(lambda B,x:B[0]*x+B[1]),beta0=[1,1]).run()
    ekt=np.where(np.isfinite(np.asarray(T["BANDBB_KT_ERR"],float)),
                 np.asarray(T["BANDBB_KT_ERR"],float),np.asarray(T["CPLBB_KT_ERR"],float))
    sx=(ekt[s130]/(KT[s130]*np.log(10))); sy=(np.asarray(T["BAND_EP_ERR"],float)[s130]/(EP[s130]*np.log(10)))
    okk=np.isfinite(sx)&np.isfinite(sy)&(sx>0)&(sy>0)
    da=dagostini(lx[okk],ly[okk],sx[okk],sy[okk]) if okk.sum()>=5 else (np.nan,)*4
    out["epkt_130427A"]={"n":int(s130.sum()),"rho":float(stats.spearmanr(KT[s130],EP[s130])[0]),
        "odr_slope":float(o.beta[0]),"odr_slope_err":float(o.sd_beta[0]),
        "dagostini_slope":float(da[0]),"dagostini_slope_err":float(da[1]),
        "ols_slope":float(np.polyfit(lx,ly,1)[0])}
# dBIC cross-check on the BB-significant sample
DB=np.asarray(P["bb_dbic"],bool)
out["bb_dbic_check"]={"n_kT_sig":int(np.isfinite(KT).sum()),
    "n_also_dbic":int(np.sum(DB[np.isfinite(KT)])),
    "frac":float(np.mean(DB[np.isfinite(KT)])) if np.isfinite(KT).sum() else np.nan}

# ---- extra scalars + per-burst correlation fractions ----
out["alpha"]["std"]=float(np.std(al))
out["logEp"]={"median":float(np.median(np.log10(ep))),"std":float(np.std(np.log10(ep)))}
out["kT"]={"n":int(np.isfinite(KT).sum()),
           "median":float(np.nanmedian(KT)),
           "p5":float(np.nanpercentile(KT,5)),"p95":float(np.nanpercentile(KT,95)),
           "min":float(np.nanmin(KT)),"max":float(np.nanmax(KT))}

def pb_frac(xa, ya, nmin=5):
    xa=np.asarray(xa,float); ya=np.asarray(ya,float)
    nb=npos=nsig=0
    for bn in np.unique(trig):
        s=(trig==bn)&np.isfinite(xa)&np.isfinite(ya)
        if s.sum()>=nmin:
            nb+=1
            rho,p=stats.spearmanr(xa[s],ya[s])
            if rho>0: npos+=1
            if rho>0 and p<0.05: nsig+=1
    return {"n_bursts":nb,"frac_pos":(npos/nb if nb else np.nan),
            "frac_sig_pos":(nsig/nb if nb else np.nan),"n_pos":npos,"n_sig":nsig}
out["pb_F_alpha"]=pb_frac(A, F)      # F vs alpha (energy flux)
out["pb_F_Ep"]   =pb_frac(EP, F)     # F vs Ep (energy flux)
def pb_frac_neg(xa, ya, nmin=5):
    xa=np.asarray(xa,float); ya=np.asarray(ya,float)
    nb=nneg=nsig=0
    for bn in np.unique(trig):
        s=(trig==bn)&np.isfinite(xa)&np.isfinite(ya)
        if s.sum()>=nmin:
            nb+=1
            rho,p=stats.spearmanr(xa[s],ya[s])
            if rho<0: nneg+=1
            if rho<0 and p<0.05: nsig+=1
    return {"n_bursts":nb,"frac_neg":(nneg/nb if nb else np.nan),
            "frac_sig_neg":(nsig/nb if nb else np.nan),"n_neg":nneg,"n_sig":nsig}
out["pb_alpha_Ep"]=pb_frac_neg(EP, A)   # alpha vs Ep (anti-corr: harder spectra, higher Ep -> ...)
out["pb_kT_flux"] =pb_frac(FP, KT)      # kT vs photon flux

# ---- model-separation "inconclusive" fraction ----
# top2_gap = best vs SECOND-best AIC ("no decisive single winner");
# full_spread = best vs WORST valid AIC ("all models within X") -- different
# statements; the paper must quote each with its own denominator.
aic_cols=[("BAND_AIC","BAND_VALID"),("CPL_AIC","CPL_VALID"),("SBPL_AIC","SBPL_VALID"),
          ("DSBPL_AIC","DSBPL_VALID"),("BANDBB_AIC","BANDBB_VALID"),("CPLBB_AIC","CPLBB_VALID")]
gap=[]; spread=[]
for r in T:
    aics=[g(r,c) for c,v in aic_cols if vb(r,v) and np.isfinite(g(r,c))]
    if len(aics)>=2:
        aics=sorted(aics); gap.append(aics[1]-aics[0]); spread.append(aics[-1]-aics[0])
gap=np.array(gap); spread=np.array(spread)
out["model_separation"]={"n":len(gap),
    "n_top2_lt10":int(np.sum(gap<10)),
    "frac_inconclusive_dAIC6":float(np.mean(gap<6)),
    "frac_inconclusive_dAIC10":float(np.mean(gap<10)),
    "frac_decisive_dAIC10":float(np.mean(gap>=10)),
    "frac_allvalid_within10":float(np.mean(spread<10)),
    "frac_allvalid_within6":float(np.mean(spread<6)),
    "frac_of_all_1057_top2_lt10":float(np.sum(gap<10)/len(T))}

with open(f"{ROOT}/results/draft_numbers{OTAG}.json","w") as fh:
    json.dump(out,fh,indent=2)

# ---------- print ----------
print("="*70)
print(f"bursts={out['n_bursts']}  time-resolved spectra={out['n_spec']}")
print(f"tiers: Gold(>=10) {out['tiers']['gold']}  Silver(5-9) {out['tiers']['silver']}  Bronze(<=4) {out['tiers']['bronze']}")
print(f"bins/burst median={out['bins_per_burst']['median']} ({out['bins_per_burst']['min']}-{out['bins_per_burst']['max']})")
print(f"alpha(Band): n={out['alpha']['n']} median={out['alpha']['median']:.2f} [{out['alpha']['q1']:.2f},{out['alpha']['q3']:.2f}]  >-2/3:{out['alpha']['frac_above_2_3']*100:.0f}%  >-3/2:{out['alpha']['frac_above_3_2']*100:.0f}%")
print(f"Ep(Band): median={out['Ep']['median']:.0f} keV [{out['Ep']['min']:.0f},{out['Ep']['max']:.0f}]  beta median={out['beta']['median']:.2f}")
print(f"best-model census: {out['best_model_census']}")
print(f"curvature(dAIC>6): {out['curvature_split_dAIC6']}")
print(f"curvature(dAIC>=10): {out['curvature_split_dAIC10']}")
print(f"F_BB/F_tot: n={out['fbb']['n']} median={out['fbb']['median']:.3f} [{out['fbb']['q1']:.3f},{out['fbb']['q3']:.3f}]")
print(f"F-alpha: {out.get('F_alpha')}")
print(f"F-Ep energy: {out.get('F_Ep_energy')}  | F-Ep photon: {out['F_Ep_photon']}")
print(f"Ep-F energy: {out['Ep_Fenergy']}  | Ep-F photon: {out['Ep_Fphoton']}")
print(f"kT-F energy: {out['kT_Fenergy']}  | kT-F photon: {out['kT_Fphoton']}")
print(f"nu_m-nu_c: {out['nu_m_nu_c']}")
print(f"Ep-kT global: {out['epkt_global']}")
print(f"Ep-kT per-burst: tested={out['epkt_perburst']['n_bursts_tested']} frac_pos={out['epkt_perburst']['frac_positive']} n_sig_pos={out['epkt_perburst']['n_sig_positive']}")
for d in out['epkt_perburst']['top'][:6]:
    print(f"    {d['trig']}: n={d['n']} rho={d['rho']:.2f} p={d['p']:.3f}")
print("="*70)
print("WROTE results/draft_numbers.json")
