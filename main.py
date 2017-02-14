#!/usr/bin/env python2

from ouman import Ouman
import eh203
import time

ouman = Ouman('/dev/ttyUSB0')
try:
    while True:
        for name, i in eh203.SENSORS:
            val = ouman.read(i)
            print name, val
        time.sleep(1)
finally:
    ouman.close()
