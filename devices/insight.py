#! /usr/bin/env python

import time
from device import *

class TuningError(Exception):
    """Exception for Tuning Error"""
    def __init__(self):
        self.msg = 'Wavelength not changed'

    def __str__(self):
        return self.msg

class Insight(Device):
    _states = ['Initializing', 'Ready to turn on',
               'Turning on and/or optimizing', 'RUN', 'Moving to Align mode',
               'Align mode', 'Exiting Align mode', 'Reserved']

    def __init__(self, port=None, com_time=0.1):
        # Variables
        ######################################################################
        # Not intended to be accessed directly, only through properties
        self._com_time = com_time
        self._state = 0
        self._opo_wl = 0
        self._main_shutter = 0
        self._fixed_shutter = 0

        # Access directly
        self.diode1_temp = 0
        self.diode2_temp = 0
        self.humidity = 0
        self.diode1_curr = 0
        self.diode2_curr = 0
        self.diode1_hrs = 0
        self.diode2_hrs = 0

        # Initialize the values where needed
        self.laser_hrs()
        self.laser_stats()
        self.write('WAVelength?', self._com_time)
        self._opo_wl = int(self.read())

        # Initialize serial communications with port and open that port
        Device.__init__(self, port)
        self.open_com()

    def query_state(self):
        self.write('*STB?', self._com_time)
        s = int(self.read())
        masked = s & 0x007F0000
        self._state = masked >> 16

    def laser_hrs(self):
        self.write('READ:PLASer:DIODe1:HOURS?', self._com_time)
        self.diode1_hrs = float(self.read())
        self.write('READ:PLASer:DIODe2:HOURS?', self._com_time)
        self.diode2_hrs = float(self.read())

    def laser_stats(self):
        self.write('READ:PLASer:DIODe1:TEMPerature?', self._com_time)
        self.diode1_temp = float(self.read())
        self.write('READ:PLASer:DIODe2:TEMPerature?', self._com_time)
        self.diode2_temp = float(self.read())

        self.write('READ:HUMidity?', self._com_time)
        self.humidity = float(self.read())

        self.write('READ:PLASer:DIODe1:CURRent?', self._com_time)
        self.diode1_curr = float(self.read())
        self.write('READ:PLASer:DIODe2:CURRent?', self._com_time)
        self.diode2_curr = float(self.read())

    def turnon(self):
        self.write('ON', self._com_time)

    def turnoff(self):
        self.write('OFF', self._com_time)

    @property
    def state(self):
        if self._state < 25:
            return _states[0]
        elif self._state == 25:
            return _states[1]
        elif self._states < 50:
            return _states[2]
        elif self._states == 50:
            return _states[3]
        elif self._states < 60:
            return _states[4]
        elif self._states == 60:
            return _states[5]
        elif self._states < 70:
            return _states[6]
        else:
            return _states[7]

    @property
    def opo_wl(self):
        return self._opo_wl

    @opo_wl.setter
    def opo_wl(self, val):
        try:
            self.write('WAVelength %i' % val, self._com_time)
            self.write('WAVelength?', self._com_time)
            if int(self.read()) != val:
                raise TuningError

            self._opo_wl = int(self.read())
        except:
            print('Wavelength not changed')

    @property
    def main_shutter(self):
        return self._main_shutter

    @main_shutter.setter
    def main_shutter(self, val):
        self.write('SHUTter %i' % val)
        self._main_shutter = val

    @property
    def fixed_shutter(self):
        return self._fixed_shutter

    @fixed_shutter.setter
    def fixed_shutter(self, val):
        self.write('IRSHUTter %i' % val)
        self._fixed_shutter = val

    # Need deepsee stuff