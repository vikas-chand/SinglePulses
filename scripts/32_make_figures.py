#!/usr/bin/env python
"""
32_make_figures.py -- Publication figures from the CLEAN catalog, WITH error bars
from the real fit uncertainties (MINUIT parameter errors) and Monte-Carlo
propagated flux errors.  Project figure style (serif/stix, ticks-in, dpi 300).
Run in threeML env with CALDB pointed at the env (flux needs astromodels).
Outputs: paper/two_break_figures/{fig_dist,fig_evol,fig_corr,fig_lines}.pdf
Also prints the Table-6 (correlation) slope + scatter cells (OLS).
"""
import os, warnings
import numpy as np
from astropy.table import Table
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats, odr
import astromodels as am
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = f"{ROOT}/paper/two_break_figures"; os.makedirs(FIGDIR, exist_ok=True)
KEV2ERG = 1.602176634e-9; EGRID = np.geomspace(10, 1000, 400)
LN10 = np.log(10)

plt.rcParams.update({
    "font.family": "serif", "mathtext.fontset": "stix", "font.size": 11,
    "axes.labelsize": 13, "axes.titlesize": 12, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "legend.fontsize": 9,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.minor.visible": True, "ytick.minor.visible": True,
    "axes.linewidth": 0.9, "savefig.dpi": 300, "figure.dpi": 110,
    "pdf.fonttype": 42,
})
CTIER = {"Gold": "#c8951b", "Silver": "#7f7f7f", "Bronze": "#8c5a3c"}

T = Table.read(f"{ROOT}/results/clean_sample_all_models.ecsv", format="ascii.ecsv")
T = T[T["BLOCK"] >= 0]
trig = np.array(T["TRIGGER"])
def C(c): return np.array(T[c], float) if c in T.colnames else np.full(len(T), np.nan)
def Bv(c): return np.array(T[c], bool) if c in T.colnames else np.zeros(len(T), bool)

bandv = Bv("BAND_VALID")
alpha = np.where(bandv, C("BAND_ALPHA"), np.nan); ealp = C("BAND_ALPHA_ERR")
Ep    = np.where(bandv, C("BAND_EP"), np.nan);    eEp  = C("BAND_EP_ERR")
beta  = np.where(bandv, C("BAND_BETA"), np.nan);  ebeta = C("BAND_BETA_ERR")
Kb    = C("BAND_K"); eKb = C("BAND_K_ERR")
kt = np.where(Bv("BANDBB_VALID") & (C("LRT_BANDBB_BAND") >= 14), C("BANDBB_KT"), np.nan)
kt = np.where(np.isfinite(kt), kt, np.where(Bv("CPLBB_VALID") & (C("LRT_CPLBB_CPL") >= 14), C("CPLBB_KT"), np.nan))
ekt = np.where(np.isfinite(C("BANDBB_KT_ERR")), C("BANDBB_KT_ERR"), C("CPLBB_KT_ERR"))
xb = np.where(Bv("DSBPL_VALID"), C("DSBPL_XB"), np.nan); exb = C("DSBPL_XB_ERR")
xp = np.where(Bv("DSBPL_VALID"), C("DSBPL_XP"), np.nan); exp_ = C("DSBPL_XP_ERR")
tmid = C("T_MID")

# ---------- central flux (astromodels) ----------
def fband(K,a,Ep_,b):
    f=am.Band(); f.alpha.bounds=(-20,10); f.beta.bounds=(-20,0); f.xp.bounds=(1,1e6)
    f.K=K;f.alpha=a;f.xp=Ep_;f.beta=b;f.piv=100.; N=f(EGRID)
    return np.trapz(N*EGRID,EGRID)*KEV2ERG, np.trapz(N,EGRID)
def fbb(K,kT):
    f=am.Blackbody(); f.kT.bounds=(0.01,1e5); f.K=K;f.kT=kT; N=f(EGRID)
    return np.trapz(N*EGRID,EGRID)*KEV2ERG
def fcpl(K,i,xc):
    f=am.Cutoff_powerlaw(); f.index.bounds=(-20,10); f.xc.bounds=(0.1,1e7)
    f.K=K;f.index=i;f.xc=xc;f.piv=100.; N=f(EGRID)
    return np.trapz(N*EGRID,EGRID)*KEV2ERG
F=np.full(len(T),np.nan); Fph=np.full(len(T),np.nan); fbbr=np.full(len(T),np.nan)
for i in range(len(T)):
    if bandv[i] and np.all(np.isfinite([alpha[i],Ep[i],beta[i],Kb[i]])):
        try: F[i],Fph[i]=fband(Kb[i],alpha[i],Ep[i],beta[i])
        except Exception: pass
    r=T[i]
    try:
        if bool(r["BANDBB_VALID"]) and float(r["LRT_BANDBB_BAND"])>=14:
            Fc,_=fband(float(r["BANDBB_K_BAND"]),float(r["BANDBB_ALPHA"]),float(r["BANDBB_EP"]),float(r["BANDBB_BETA"]))
            Fb=fbb(float(r["BANDBB_K_BB"]),float(r["BANDBB_KT"])); fbbr[i]=Fb/(Fb+Fc)
        elif bool(r["CPLBB_VALID"]) and float(r["LRT_CPLBB_CPL"])>=14:
            Fc=fcpl(float(r["CPLBB_K_CPL"]),float(r["CPLBB_INDEX"]),float(r["CPLBB_XC"]))
            Fb=fbb(float(r["CPLBB_K_BB"]),float(r["CPLBB_KT"])); fbbr[i]=Fb/(Fb+Fc)
    except Exception: pass

# ---------- Monte-Carlo flux uncertainties (Band, from fit errors) ----------
def band_flux_mc(K,a,Ep_,b,g):
    a=np.clip(a,-1.9,3.0); b=np.clip(b,-12,-1.01)
    A=a[:,None];Bt=b[:,None];P=Ep_[:,None];Kk=K[:,None];G=g[None,:]
    Ec=(a-b)*Ep_/(2+a)
    lowE=Kk*(G/100.)**A*np.exp(-(2+A)*G/P)
    hiE =Kk*(G/100.)**Bt*np.exp(Bt-A)*((A-Bt)*P/((2+A)*100.))**(A-Bt)
    NE=np.where(G<Ec[:,None],lowE,hiE)
    return np.trapz(NE*G,G,axis=1)*KEV2ERG, np.trapz(NE,G,axis=1)
rng=np.random.default_rng(42); Ns=200
F16=np.full(len(T),np.nan);F84=np.full(len(T),np.nan)
Fph16=np.full(len(T),np.nan);Fph84=np.full(len(T),np.nan)
for i in range(len(T)):
    if not (np.isfinite(F[i]) and bandv[i]): continue
    def dr(v,e): return v+(e if np.isfinite(e) and e>0 else 0.0)*rng.standard_normal(Ns)
    sa=dr(alpha[i],ealp[i]); sE=np.clip(dr(Ep[i],eEp[i]),5,None)
    sb=np.clip(dr(beta[i],ebeta[i]),-12,-1.01); sK=np.clip(dr(Kb[i],eKb[i]),1e-12,None)
    try:
        fe,fp=band_flux_mc(sK,sa,sE,sb,EGRID)
        fe=fe[np.isfinite(fe)&(fe>0)]; fp=fp[np.isfinite(fp)&(fp>0)]
        if len(fe)>20: F16[i],F84[i]=np.percentile(fe,[16,84])
        if len(fp)>20: Fph16[i],Fph84[i]=np.percentile(fp,[16,84])
    except Exception: pass

def eb_log(v,lo,hi):                       # asym err in dex about log10(v)
    with np.errstate(all="ignore"):
        e=np.vstack([np.log10(v)-np.log10(lo), np.log10(hi)-np.log10(v)])
    return np.where(np.isfinite(e)&(e>0), e, 0.0)
def eb_lin(v,lo,hi):
    e=np.vstack([v-lo, hi-v]); return np.where(np.isfinite(e)&(e>0), e, 0.0)
def derr_dex(v,e):                         # symmetric dex err from linear err
    return np.where(np.isfinite(e)&(v>0), e/(v*LN10), 0.0)

import collections
cnt=collections.Counter(trig)
def tier(bn): n=cnt[bn]; return "Gold" if n>=10 else ("Silver" if n>=5 else "Bronze")
tiers=np.array([tier(b) for b in trig])
def odrfit(x,y):
    m=np.isfinite(x)&np.isfinite(y); x,y=x[m],y[m]
    o=odr.ODR(odr.RealData(x,y),odr.Model(lambda B_,t:B_[0]*t+B_[1]),beta0=[1,0]).run()
    return o.beta[0],o.sd_beta[0],float(np.std(y-(o.beta[0]*x+o.beta[1]))),int(len(x))
EBKW=dict(elinewidth=0.5, ecolor="0.55", capsize=0, alpha=0.85)

# --- "well-constrained" masks: drop the tail of poorly-determined fits whose
#     MINUIT errors are enormous (they exploded the autoscaled error bars) ---
def okpos(v,e,thr=1.0):            # positive quantity: relative error < thr
    return np.isfinite(v)&np.isfinite(e)&(v>0)&(np.abs(e)<thr*np.abs(v))
def okabs(v,e,thr=0.5):            # linear quantity (alpha): |err| < thr
    return np.isfinite(v)&np.isfinite(e)&(np.abs(e)<thr)
def okflux(v,lo,hi,thr=0.5):       # MC flux: half-width in dex < thr
    with np.errstate(all="ignore"):
        d=0.5*(np.log10(hi)-np.log10(lo))
    return np.isfinite(d)&(d>=0)&(d<thr)&np.isfinite(v)&(v>0)
def lims(arr,lo=1,hi=99,pad=0.07):  # tight axis limits from data percentiles
    a=arr[np.isfinite(arr)]; x0,x1=np.percentile(a,[lo,hi]); d=(x1-x0)*pad
    return x0-d, x1+d

# ============================================================ FIG 1: distributions
try:
    fig,ax=plt.subplots(2,3,figsize=(9.6,6.0))
    panels=[("$\\alpha$ (Band)",alpha,(-2.2,1.0),False,[(-2/3,"$-2/3$"),(-3/2,"$-3/2$")]),
            ("$\\log_{10}(E_{\\rm p}/{\\rm keV})$",np.log10(Ep),(1.0,4.0),False,[]),
            ("$kT$ (keV)",kt,None,True,[]),
            ("$\\log_{10}(F/{\\rm erg\\,cm^{-2}s^{-1}})$",np.log10(F),None,False,[]),
            ("$N_{\\rm bins}$ per burst",np.array([cnt[b] for b in trig]),None,False,[])]
    for k,(lab,arr,rng_,logx,vlines) in enumerate(panels):
        a=ax.flat[k]
        for tg in ["Gold","Silver","Bronze"]:
            d=arr[(tiers==tg)&np.isfinite(arr)]
            if logx: d=np.log10(d[d>0])
            if len(d)<3: continue
            a.hist(d,bins=22,range=(rng_ if (rng_ and not logx) else None),density=True,
                   histtype="step",lw=1.6,color=CTIER[tg],label=f"{tg} ({(tiers==tg).sum()})")
        for vx,vl in vlines:
            a.axvline(vx,ls="--",lw=0.9,color="k",alpha=0.6); a.text(vx,a.get_ylim()[1]*0.55,vl,fontsize=8,ha="center")
        a.set_xlabel(("$\\log_{10}$ "+lab) if logx else lab); a.set_ylabel("PDF")
        if k==0: a.legend(framealpha=0.9,edgecolor="0.6",loc="upper left")
    ax.flat[5].axis("off")
    ax.flat[5].text(0.05,0.5,"Per-bin distributions\nby coverage tier\n(Gold $\\geq$10 bins,\nSilver 5–9, Bronze $\\leq$4).",fontsize=10,va="center")
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/fig_dist.pdf"); plt.close(fig); print("OK fig_dist")
except Exception as e: print("ERR fig_dist",e)

# ============================================================ FIG 2: 130427A evolution
try:
    bn="bn130427324"; s=trig==bn; o=np.argsort(tmid[s]); t=tmid[s][o]
    Eo=Ep[s][o];Ao=alpha[s][o];Ko=kt[s][o];Fo=F[s][o]
    eEo=eEp[s][o];eAo=ealp[s][o];eKo=ekt[s][o]
    F16o=F16[s][o];F84o=F84[s][o]
    # left column: 4 shared-x rows (tight); right column: 3 independent panels
    # (own xlabels + titles), so it needs its OWN generous vertical spacing.
    fig=plt.figure(figsize=(9.6,6.6))
    gs0=fig.add_gridspec(1,2,width_ratios=[1.25,1],wspace=0.30)
    gl=gs0[0].subgridspec(4,1,hspace=0.08)
    gr=gs0[1].subgridspec(3,1,hspace=0.55)
    axF=fig.add_subplot(gl[0]);axE=fig.add_subplot(gl[1],sharex=axF)
    axA=fig.add_subplot(gl[2],sharex=axF);axK=fig.add_subplot(gl[3],sharex=axF)
    axF.errorbar(t,Fo,yerr=eb_lin(Fo,F16o,F84o),fmt="-o",ms=3,color="#1f4e79",lw=1,**EBKW); axF.set_yscale("log"); axF.set_ylabel("$F$\n(erg cm$^{-2}$s$^{-1}$)")
    axE.errorbar(t,Eo,yerr=eEo,fmt="o",ms=3,color="#b3202c",**EBKW); axE.set_yscale("log"); axE.set_ylabel("$E_{\\rm p}$ (keV)")
    axA.errorbar(t,Ao,yerr=eAo,fmt="o",ms=3,color="#2e7d32",**EBKW); axA.set_ylabel("$\\alpha$")
    axA.axhline(-2/3,ls="--",lw=0.8,color="k",alpha=0.6); axA.axhline(-3/2,ls=":",lw=0.8,color="k",alpha=0.6)
    axK.errorbar(t,Ko,yerr=eKo,fmt="o",ms=3,color="#6a3d9a",**EBKW); axK.set_yscale("log"); axK.set_ylabel("$kT$ (keV)"); axK.set_xlabel("Time since trigger (s)")
    for a in (axF,axE,axA): plt.setp(a.get_xticklabels(),visible=False)
    axF.set_title("GRB 130427A",fontsize=11,loc="left")
    c1=fig.add_subplot(gr[0]);c2=fig.add_subplot(gr[1]);c3=fig.add_subplot(gr[2])
    m=np.isfinite(Ao)&np.isfinite(Fo)
    c1.errorbar(Ao[m],Fo[m],xerr=eAo[m],yerr=eb_lin(Fo,F16o,F84o)[:,m],fmt="o",ms=4,color="#1f4e79",**EBKW); c1.set_yscale("log")
    c1.set_xlabel("$\\alpha$");c1.set_ylabel("$F$");c1.set_title("$F$–$\\alpha$",fontsize=9,loc="left")
    m=np.isfinite(Eo)&np.isfinite(Fo)
    c2.errorbar(Eo[m],Fo[m],xerr=eEo[m],yerr=eb_lin(Fo,F16o,F84o)[:,m],fmt="o",ms=4,color="#b3202c",**EBKW); c2.set_xscale("log");c2.set_yscale("log")
    c2.set_xlabel("$E_{\\rm p}$ (keV)");c2.set_ylabel("$F$");c2.set_title("$F$–$E_{\\rm p}$",fontsize=9,loc="left")
    m=np.isfinite(Eo)&np.isfinite(Ao)
    c3.errorbar(Eo[m],Ao[m],xerr=eEo[m],yerr=eAo[m],fmt="o",ms=4,color="#2e7d32",**EBKW); c3.set_xscale("log")
    c3.set_xlabel("$E_{\\rm p}$ (keV)");c3.set_ylabel("$\\alpha$");c3.set_title("$\\alpha$–$E_{\\rm p}$",fontsize=9,loc="left")
    fig.savefig(f"{FIGDIR}/fig_evol.pdf",bbox_inches="tight"); plt.close(fig); print("OK fig_evol (n=%d)"%s.sum())
except Exception as e: print("ERR fig_evol",e)

# ============================================================ FIG 3: break/temp correlations
try:
    import json as _json
    DN=_json.load(open(f"{ROOT}/results/draft_numbers.json"))
    EBL=dict(elinewidth=0.35, ecolor="0.7", capsize=0, alpha=0.55)   # light, dense panels
    fig=plt.figure(figsize=(9.6,8.0))
    gsc=fig.add_gridspec(2,2,hspace=0.30,wspace=0.25)
    # (a) nu_m vs nu_c -- red line = TRUE D'Agostini fit (from scripts/31 JSON)
    a=fig.add_subplot(gsc[0,0]); m=np.isfinite(xb)&np.isfinite(xp)&(xb>0)&(xp>0)&(xb<xp)
    lx,ly=np.log10(xb[m]),np.log10(xp[m]); okm=(okpos(xb,exb)&okpos(xp,exp_))[m]
    a.errorbar(lx,ly,xerr=derr_dex(xb[m],exb[m])*okm,yerr=derr_dex(xp[m],exp_[m])*okm,fmt="o",ms=4,color="#34699a",**EBL)
    da=DN["nu_m_nu_c"]["dagostini"]; sl,sle,sc=da["slope"],da["slope_err"],da["sigma_sc_dex"]
    xs=np.array([lx.min(),lx.max()])
    a.plot(xs,sl*xs+da["norm"],"-",color="#b3202c",lw=1.6)
    a.plot(xs,xs+np.median(ly-lx),"--",color="k",lw=0.8,alpha=0.5)
    a.set_xlim(*lims(lx)); a.set_ylim(*lims(ly))
    a.set_xlabel("$\\log_{10}\\,\\nu_c$ (keV)");a.set_ylabel("$\\log_{10}\\,\\nu_m$ (keV)")
    a.set_title("(a) $\\nu_m$–$\\nu_c$",fontsize=10,loc="left")
    a.text(0.04,0.96,f"$\\rho={DN['nu_m_nu_c']['rho']:.2f}$, $N={DN['nu_m_nu_c']['n']}$\nslope$={sl:.2f}\\pm{sle:.2f}$\n$\\sigma_{{\\rm sc}}={sc:.2f}$ dex",
           transform=a.transAxes,fontsize=8.5,va="top")
    # (b) Ep vs kT (constrained-error mask applied to BOTH series)
    a=fig.add_subplot(gsc[0,1]); m=np.isfinite(Ep)&np.isfinite(kt); okm=(okpos(Ep,eEp)&okpos(kt,ekt))[m]
    a.errorbar(np.log10(kt[m]),np.log10(Ep[m]),xerr=derr_dex(kt[m],ekt[m])*okm,yerr=derr_dex(Ep[m],eEp[m])*okm,fmt="o",ms=3,color="0.6",label="all bursts",**EBL)
    s4=(trig=="bn130427324")&m; ok4=(okpos(kt,ekt)&okpos(Ep,eEp))[s4]
    a.errorbar(np.log10(kt[s4]),np.log10(Ep[s4]),xerr=derr_dex(kt[s4],ekt[s4])*ok4,yerr=derr_dex(Ep[s4],eEp[s4])*ok4,fmt="o",ms=4,color="#b3202c",label="GRB 130427A",elinewidth=0.5,ecolor="#b3202c",capsize=0)
    a.set_xlim(*lims(np.log10(kt[m]))); a.set_ylim(*lims(np.log10(Ep[m])))
    a.set_xlabel("$\\log_{10}\\,kT$ (keV)");a.set_ylabel("$\\log_{10}\\,E_{\\rm p}$ (keV)")
    a.set_title("(b) $E_{\\rm p}$–$kT$",fontsize=10,loc="left")
    a.text(0.04,0.96,f"$\\rho={stats.spearmanr(np.log10(kt[m]),np.log10(Ep[m]))[0]:.2f}$, $N={int(m.sum())}$",transform=a.transAxes,fontsize=8.5,va="top")
    a.legend(framealpha=0.9,edgecolor="0.6",loc="lower right")
    # (c)/(d): energy- and photon-flux versions SIDE BY SIDE sharing y
    def fluxpair(cell,yv,ye,ylab,tag,surv):
        sub=cell.subgridspec(1,2,wspace=0.06)
        aL=fig.add_subplot(sub[0]); aR=fig.add_subplot(sub[1],sharey=aL)
        mE=np.isfinite(yv)&np.isfinite(F); mP=np.isfinite(yv)&np.isfinite(Fph)
        rE=stats.spearmanr(np.log10(F[mE]),np.log10(yv[mE]))[0]
        rP=stats.spearmanr(np.log10(Fph[mP]),np.log10(yv[mP]))[0]
        aL.errorbar(np.log10(F[mE]),np.log10(yv[mE]),xerr=eb_log(F,F16,F84)[:,mE]*okflux(F,F16,F84)[mE],
                    yerr=derr_dex(yv[mE],ye[mE])*okpos(yv,ye)[mE],fmt="o",ms=3,color="#1f4e79",**EBL)
        aR.errorbar(np.log10(Fph[mP]),np.log10(yv[mP]),xerr=eb_log(Fph,Fph16,Fph84)[:,mP]*okflux(Fph,Fph16,Fph84)[mP],
                    yerr=derr_dex(yv[mP],ye[mP])*okpos(yv,ye)[mP],fmt="o",ms=3,color="#cc7a00",**EBL)
        aL.set_xlim(*lims(np.log10(F[mE]))); aR.set_xlim(*lims(np.log10(Fph[mP])))
        aL.set_ylim(*lims(np.log10(yv[mE])))
        aL.set_xlabel("$\\log_{10}F_{\\rm energy}$",fontsize=10); aR.set_xlabel("$\\log_{10}F_{\\rm photon}$",fontsize=10)
        aL.set_ylabel(ylab); plt.setp(aR.get_yticklabels(),visible=False)
        aL.set_title(tag,fontsize=10,loc="left")
        aL.text(0.05,0.95,f"$\\rho={rE:.2f}$",transform=aL.transAxes,fontsize=9,va="top",color="#1f4e79")
        aR.text(0.05,0.95,f"$\\rho={rP:.2f}$",transform=aR.transAxes,fontsize=9,va="top",color="#cc7a00")
        aR.text(0.95,0.05,surv,transform=aR.transAxes,fontsize=8,ha="right",style="italic")
    fluxpair(gsc[1,0],Ep,eEp,"$\\log_{10}\\,E_{\\rm p}$ (keV)","(c) $E_{\\rm p}$ vs flux","collapses")
    fluxpair(gsc[1,1],kt,ekt,"$\\log_{10}\\,kT$ (keV)","(d) $kT$ vs flux","survives")
    fig.savefig(f"{FIGDIR}/fig_corr.pdf",bbox_inches="tight"); plt.close(fig); print("OK fig_corr")
except Exception as e: print("ERR fig_corr",e)

# ============================================================ FIG 4: alpha_max vs Ep
try:
    fig,a=plt.subplots(figsize=(5.4,4.3))
    amax=[];epm=[];ea=[];ee=[];col=[]
    for bn in np.unique(trig):
        s=(trig==bn)&np.isfinite(alpha)&np.isfinite(Ep)
        if s.sum()>=1:
            j=np.nanargmax(np.where(s,alpha,-np.inf)); amax.append(alpha[j]); epm.append(Ep[j])
            ea.append(ealp[j] if np.isfinite(ealp[j]) else 0); ee.append(eEp[j] if np.isfinite(eEp[j]) else 0)
            col.append("#b3202c" if alpha[j]>-0.5 else "#34699a")
    amax=np.array(amax);epm=np.array(epm);ea=np.array(ea);ee=np.array(ee)
    # draw error bars only where reasonably constrained (else they explode the frame)
    ead=np.where(ea<0.6,ea,np.nan); eed=np.where((ee>0)&(ee<epm),ee,np.nan)
    a.errorbar(epm,amax,xerr=eed,yerr=ead,fmt="o",ms=4,ecolor="0.6",elinewidth=0.5,capsize=0,linestyle="none",
               markerfacecolor="none",markeredgecolor="none")
    a.scatter(epm,amax,s=20,c=col,alpha=0.85,zorder=3)
    a.set_ylim(np.nanmin(amax)-0.25, np.nanmax(amax)+0.3)
    for y,ls,lab,cc in [(-2/3,"--","slow-cool $-2/3$","k"),(-3/2,":","fast-cool $-3/2$","k"),(-0.5,"-.","photosph. $-0.5$","#b3202c")]:
        a.axhline(y,ls=ls,color=cc,lw=1.0); a.text(a.get_xlim()[1],y,"  "+lab,fontsize=8,va="bottom",color=cc)
    a.set_xscale("log"); a.set_xlabel("$E_{\\rm p}$ (keV)"); a.set_ylabel("$\\alpha_{\\rm max}$ per burst")
    a.set_title("Hardest low-energy index vs peak energy",fontsize=10,loc="left")
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/fig_lines.pdf"); plt.close(fig)
    print("OK fig_lines (%d>-0.5 / %d)"%(np.sum(amax>-0.5),len(amax)))
except Exception as e: print("ERR fig_lines",e)

# ============================================================ Table 6 cells (OLS)
print("\n=== Table 6 OLS slope + residual scatter ===")
def cell(name,x,y,xlog,ylog,efold=False):
    X=np.log10(x) if xlog else x; Y=np.log10(y) if ylog else y
    m=np.isfinite(X)&np.isfinite(Y); X,Y=X[m],Y[m]
    if efold:
        k,c=np.polyfit(X,np.log(y[m]),1); print(f"{name}: k(e-fold)={k:.2f} scatter={np.std(np.log(y[m])-(k*X+c))/LN10:.2f}dex N={len(X)}"); return
    sl,c=np.polyfit(X,Y,1); print(f"{name}: slope={sl:.2f} scatter={np.std(Y-(sl*X+c)):.2f}{'dex' if ylog else 'a'} N={len(X)}")
cell("F-alpha",alpha,F,False,True,efold=True); cell("F-Ep",Ep,F,True,True)
cell("alpha-Ep",Ep,alpha,True,False); cell("Ep-kT",kt,Ep,True,True); cell("kT-flux",Fph,kt,True,True)
