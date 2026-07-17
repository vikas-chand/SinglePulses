"""Every pipeline script must at least compile (the cheapest regression net)."""
import glob, os, py_compile
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = sorted(
    p for p in glob.glob(os.path.join(BASE, 'scripts', '*.py'))
    if '/legacy/' not in p and not p.endswith('.bak')
)


@pytest.mark.parametrize('path', SCRIPTS, ids=[os.path.basename(p) for p in SCRIPTS])
def test_compiles(path):
    py_compile.compile(path, doraise=True)
