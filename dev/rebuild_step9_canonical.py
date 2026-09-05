#!/usr/bin/env python3
"""Rebuild the step-9 QC scorecard from the CANONICAL campaign fit table.

Root cause (figure-verifier BLOCKING find, 2026-08-17, GRB 090530): the driver
called scripts/44 with its default --out (results/sweep106), whose per-burst
spectral_fits.ecsv is the STALE pre-campaign table — so step9's evidence bars
contradicted the package's own SEDs (the bn200524211 label-primitive class).

This shim imports scripts/44 unmodified and calls fig_step9 against a temp
root whose <trig>/spectral_fits.ecsv symlinks to
results/convention_check/<trig>/spectral_fits.ecsv, then installs the PNG
into results/sweep106/<trig>/ (the paper-staging location).
Usage: rebuild_step9_canonical.py --trig <TRIG>
"""
import argparse, importlib.util, os, shutil, sys, tempfile

ROOT = "/Users/salim/Desktop/Projects/SingleRest/Two_Breaks"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trig", required=True)
    a = ap.parse_args()
    os.chdir(ROOT)

    canon = os.path.join(ROOT, "results", "convention_check", a.trig,
                         "spectral_fits.ecsv")
    if not os.path.exists(canon):
        print(f"{a.trig}: no canonical table — cannot rebuild step9")
        return 2

    spec = importlib.util.spec_from_file_location(
        "step44", os.path.join(ROOT, "scripts", "44_step_figures.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, a.trig))
        os.symlink(canon, os.path.join(td, a.trig, "spectral_fits.ecsv"))
        m.fig_step9(a.trig, td)
        made = [f for f in os.listdir(td) if f.endswith(".png")] + \
               [os.path.join(a.trig, f) for f in os.listdir(os.path.join(td, a.trig))
                if f.endswith(".png")]
        if not made:
            print(f"{a.trig}: fig_step9 produced no PNG")
            return 3
        src = os.path.join(td, made[0])
        dst = os.path.join(ROOT, "results", "sweep106", a.trig,
                           f"{a.trig}_step9_qc.png")
        shutil.copy2(src, dst)
        for js in [f for f in os.listdir(td) if f.endswith(".json")]:
            shutil.copy2(os.path.join(td, js),
                         os.path.join(ROOT, "results", "sweep106", a.trig, js))
        print(f"{a.trig}: step9 rebuilt from CANONICAL table -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
