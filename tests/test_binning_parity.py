"""The deterministic binning parity guard (canon 27b vs grb_pipeline port)."""
import os, subprocess, sys
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_parity():
    cp = subprocess.run(
        [sys.executable, os.path.join(BASE, 'scripts', 'parity_grb.py')],
        capture_output=True, text=True, timeout=300)
    out = cp.stdout + cp.stderr
    if cp.returncode != 0 and ('ModuleNotFoundError' in out or 'ImportError' in out):
        pytest.skip(f'grb_pipeline not importable here: {out.strip()[-120:]}')
    assert cp.returncode == 0, out[-800:]
