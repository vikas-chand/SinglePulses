"""Adopted 2026-08-29 (external design survey item 3 / our A-gotchas list):
time-system conversions must round-trip exactly; never hand-converted.
Fermi MET epoch = 2001-01-01 00:00:00 UTC."""
import numpy as np
from astropy.time import Time, TimeDelta

FERMI_EPOCH = Time('2001-01-01T00:00:00', scale='utc')

def met_to_time(met_s):
    return FERMI_EPOCH + TimeDelta(np.asarray(met_s, dtype=float), format='sec')

def test_met_utc_roundtrip_microsecond():
    for met in (0.0, 2.456e8, 4.6e8, 7.87e8):   # spans the campaign era
        t = met_to_time(met)
        back = (t - FERMI_EPOCH).sec
        assert abs(back - met) < 1e-6, (met, back)

def test_epoch_is_2001():
    assert met_to_time(0.0).isot.startswith('2001-01-01T00:00:00')
