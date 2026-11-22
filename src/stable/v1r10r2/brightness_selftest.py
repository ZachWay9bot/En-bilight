#!/usr/bin/env python3
from effects_r10 import DEFAULT, validate, Effects
for val in (1,54,255):
    assert validate(dict(DEFAULT,brightness=val))['brightness']==val
for val in (0,256):
    try: validate(dict(DEFAULT,brightness=val));raise AssertionError(val)
    except ValueError:pass
fx=Effects(dict(DEFAULT,smooth_pct=0,deadband=0))
raw=bytearray([55,33,101])*314
assert fx.apply(raw)==raw
print('BRIGHTNESS_SELFTEST_PASS 1..255; 54 default; RGB neutral')
