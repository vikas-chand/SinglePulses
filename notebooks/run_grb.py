#!/usr/bin/env python
"""Run the ONE per-GRB notebook on a given GRB's config (FermiPy-style).

  python notebooks/run_grb.py bn130427324               # -> how to open interactively
  python notebooks/run_grb.py bn130427324 --execute      # -> outputs/bn130427324.ipynb
  python notebooks/run_grb.py bn130427324 --depth full --execute

Interactive: it just tells you the env var to set. --execute runs the notebook
headless via jupyter nbconvert in the threeML env and writes an executed copy.
The notebook itself is NEVER copied per burst — only the config selects the GRB.
"""
import argparse, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = os.path.join(ROOT, "notebooks", "Two_Breaks_single_GRB_pipeline.ipynb")
THREEML = "/Users/salim/anaconda3/envs/threeML/bin/python"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("grb")
    ap.add_argument("--depth", choices=["quick", "full"], default=None)
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    env = dict(os.environ, GRB=a.grb, MPLBACKEND="Agg")
    if a.depth:
        env["DEPTH"] = a.depth
    if not a.execute:
        print(f"Open the notebook with the burst selected:\n"
              f"  GRB={a.grb} {'DEPTH='+a.depth+' ' if a.depth else ''}jupyter lab "
              f"{os.path.relpath(NB, ROOT)}\n"
              f"(or set `grb:` in notebooks/configs/{a.grb}.yaml and Run All)")
        return 0
    outdir = os.path.join(ROOT, "notebooks", "outputs")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{a.grb}.ipynb")
    cmd = [THREEML, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
           "--ExecutePreprocessor.timeout=1800", "--output", out, NB]
    print("executing:", " ".join(cmd))
    return subprocess.call(cmd, env=env, cwd=ROOT)

if __name__ == "__main__":
    raise SystemExit(main())
