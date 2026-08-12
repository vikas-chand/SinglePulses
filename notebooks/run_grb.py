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
THREEML = "/home/aurora/anaconda3/envs/threeML/bin/python"
THREEML_PREFIX = os.path.dirname(os.path.dirname(THREEML))  # conda env root


def heavy_env(base):
    """Add the CALDB exports (AGENTS.md §2) + kernel path so nbconvert runs under
    the threeML env. Without CALDB, `import threeML` aborts on alias_config.fits;
    without JUPYTER_PATH, the notebook's `python3` kernelspec resolves to a
    user-level kernel that lacks threeML."""
    fermi = os.path.join(THREEML_PREFIX, "share", "fermitools")
    caldb = os.path.join(fermi, "data", "caldb")
    e = dict(base,
             FERMI_DIR=fermi,
             CALDB=caldb,
             CALDBCONFIG=os.path.join(caldb, "software", "tools", "caldb.config"),
             CALDBALIAS=os.path.join(caldb, "software", "tools", "alias_config.fits"),
             CALDBROOT=caldb,
             EXTFILESSYS=os.path.join(fermi, "refdata", "fermi"),
             OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    # Env kernels are searched after user kernels; put the env first so the
    # `python3` kernelspec that points at THREEML wins.
    env_jup = os.path.join(THREEML_PREFIX, "share", "jupyter")
    e["JUPYTER_PATH"] = env_jup + (os.pathsep + base["JUPYTER_PATH"]
                                   if base.get("JUPYTER_PATH") else "")
    return e

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
    return subprocess.call(cmd, env=heavy_env(env), cwd=ROOT)

if __name__ == "__main__":
    raise SystemExit(main())
