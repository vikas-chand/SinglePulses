import sys, subprocess, os, json
from concurrent.futures import ThreadPoolExecutor, as_completed
os.chdir('/Users/salim/Desktop/Projects/SingleRest/Two_Breaks')
bursts = open(sys.argv[1]).read().split()
TIMEOUT = int(sys.argv[2]) if len(sys.argv)>2 else 200
def approve(t):
    out=f'results/approval/{t}_codex.json'
    if os.path.exists(out): return (t,'skip')
    prompt=(f"INDEPENDENTLY approve Stage-1 GBM background selection for GRB {t} (judge from data+rules). "
      "1) Read rules dev/ai_guides/{detector_selection,background_selection,source_selection}.md — the LC PNGs carry an orange imodpoly_mad BASELINE + red TRANSIENT shade; use them + the near-edge cap. "
      f"2) Read results/approval/{t}_pending.json. 3) LOOK at each detector PNG (png_path), place pre/post windows NEAR the burst on the same smooth baseline (interpolate) per rules. "
      f"4) Write ONLY JSON to results/approval/{t}_codex.json: {{detectors:[...],windows:{{det:{{pre:[a,b],post:[c,d]}}}},source:{{t1,t2}},reasoning,deviations}}. Times s rel trigger.")
    try:
        subprocess.run(['codex','exec','-C',os.getcwd(),'-s','workspace-write',
            '-c','sandbox_permissions=["disk-full-read-access"]','-c','model_reasoning_effort="high"',
            prompt], capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return (t,'TIMEOUT')
    except Exception as e:
        return (t,f'ERR:{type(e).__name__}')
    return (t,'OK' if os.path.exists(out) else 'NO_OUTPUT')
res={}
with ThreadPoolExecutor(max_workers=5) as ex:
    for fut in as_completed({ex.submit(approve,t):t for t in bursts}):
        t,st=fut.result(); res[t]=st; print(f"{t}: {st}", flush=True)
import collections
print("SUMMARY:", dict(collections.Counter(res.values())))
