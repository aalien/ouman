#!/usr/bin/env python3

import time
from ouman import Ouman

ouman = Ouman('EH-203.xml')
ouman.connect('/dev/ttyUSB0')

try:
    for mp in ouman.measurepoints():
        val = mp.read()
        print('ouman %s=%.1f' % (mp.name, val))  # + mp.unit)
finally:
    ouman.close()
