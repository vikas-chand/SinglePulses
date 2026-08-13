#!/usr/bin/env python
"""Lag-MVT curvature test (project #37) from the temporal catalog.
Prediction (curvature): tau_lag ~ (E_h/E_l - 1) * dt_MVT  -> slope E_h/E_l-1, intercept 0.
Reads results/temporal_catalog_human.ecsv; writes temporal_properties/{figures,results}/."""
import os, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from astropy.table import Table
from scipy import stats
ROOT="/Users/salim/Desktop/Projects/SingleRest/Two_Breaks"; os.chdir(ROOT)
plt.rcParams.update({"font.family":"serif","mathtext.fontset":"stix","font.size":13,
    "xtick.direction":"in","ytick.direction":"in","xtick.top":True,"ytick.right":True,
    "xtick.minor.visible":True,"ytick.minor.visible":True})

t=Table.read("results/temporal_catalog_human.ecsv",format="ascii.ecsv")
# lag/MVT bands from scripts/40: E_SOFT/E_HARD -> E_h/E_l for the curvature slope
E_SOFT=(25.,50.); E_HARD=(100.,300.)   # matches scripts/40 defaults; verify vs the run
Eh=np.sqrt(E_HARD[0]*E_HARD[1]); El=np.sqrt(E_SOFT[0]*E_SOFT[1]); slope_pred=Eh/El-1.0
lag=np.array(t["LAG_S"],float); lag_e=np.array(t["LAG_ERR_S"],float)
mvt=np.array(t["MVT_S"],float); mvt_e=np.array(t["MVT_ERR_S"],float)
acc=np.array(t["LAG_ACCEPTED"],bool) if "LAG_ACCEPTED" in t.colnames else np.isfinite(lag)
# clean: positive lag (curvature predicts +), finite MVT, lag accepted
m=acc & np.isfinite(lag)&np.isfinite(mvt)&(mvt>0)&(lag>0)
n=int(m.sum())
out=[]
out.append(f"lag-MVT: {n} bursts with accepted +lag and finite MVT (of {len(t)})")
out.append(f"curvature slope prediction E_h/E_l-1 = {slope_pred:.3f}  (E_h={Eh:.0f}, E_l={El:.0f} keV)")
if n>=5:
    x=np.log10(mvt[m]); y=np.log10(lag[m])
    rho,p=stats.spearmanr(mvt[m],lag[m])
    sl,inter,r,pp,se=stats.linregress(x,y)
    out.append(f"Spearman rho(MVT,lag) = {rho:+.3f}  (p={p:.2g})")
    out.append(f"log-log fit: slope={sl:.2f}+/-{se:.2f}, intercept={inter:.2f} (in log space)")
    out.append(f"  -> compare fitted slope to 1.0 (linear tau~dt) and check if lag~slope_pred*MVT")
    fig,ax=plt.subplots(figsize=(7,6))
    ax.errorbar(mvt[m]*1000,lag[m],xerr=mvt_e[m]*1000 if np.isfinite(mvt_e[m]).any() else None,
                yerr=lag_e[m] if np.isfinite(lag_e[m]).any() else None,
                fmt="o",ms=5,color="#2c7fb8",alpha=0.8,elinewidth=0.8,capsize=0,lw=0,label=f"single pulses (N={n})")
    xg=np.logspace(np.log10(np.nanmin(mvt[m]*1000)),np.log10(np.nanmax(mvt[m]*1000)),50)
    ax.plot(xg,slope_pred*(xg/1000.),"k--",lw=1.8,label=r"curvature: $\tau=(E_h/E_l-1)\,\delta t_{MVT}$")
    ax.plot(xg,(xg/1000.),":",color="0.5",lw=1.2,label=r"$\tau=\delta t_{MVT}$ (slope 1)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(r"MVT $\delta t$ [ms]"); ax.set_ylabel(r"spectral lag $\tau$ [s]")
    ax.legend(fontsize=10,framealpha=0.9,edgecolor="0.6")
    ax.set_title(f"Lag vs MVT — single-pulse GRBs  ($\\rho$={rho:+.2f})",fontsize=12)
    fig.tight_layout(); fig.savefig("temporal_properties/figures/lag_vs_mvt.png",dpi=180,bbox_inches="tight")
    out.append("wrote temporal_properties/figures/lag_vs_mvt.png")
else:
    out.append("too few points for the correlation (<5) — check the survey output / cleanness")
open("temporal_properties/results/lag_mvt_stats.txt","w").write("\n".join(out)+"\n")
print("\n".join(out))
