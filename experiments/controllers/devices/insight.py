#! /usr/bin/env python

import time
from .device import *

class TuningError(Exception):
    """Exception for Tuning Error"""
    def __init__(self):
        self.msg = 'Wavelength not changed. Invalid wavelength.'

    def __str__(self):
        return self.msg

class OperationError(Exception):
    """Exception for all other Insight Errors"""
    def __init__(self, mask):
        self._errors = np.array([
                'CDRH interlock open. Laser forced off.',
                'Keyswitch interlock open. Laser forced off.',
                'Power supply interlock open. Laser forced off.',
                'Internal interlock open. Laser forced off.',
                'Warning. Check history.',
                'Fault. Check history.'])
        self.msg = self._errors[mask][0]

    def __str__(self):
        return self.msg

class Insight(Device):
    def __init__(self, port=None, com_time=0.1):
        # Initialize serial communications with port and open that port
        Device.__init__(self, port)
        self.open_com()
        self.fault_codes = {'000': 'Normal operation.',
            '056': 'Fault: Hardware timeout. Notify S-P if it continues.',
            '066': 'Fault: Software timeout. Speak with system operator.',
            '088': 'Fault: Diode thermistor short. Contact S-P.',
            '089': 'Fault: Diode thermistor open. Contact S-P.',
            '090': 'Fault: Diodes too hot (T>30).  Check cooling system.',
            '091': 'Fault: Diodes warm (T>27).  Check cooling system.',
            '092': 'Fault: Diodes cold (T<17). Check cooling system.',
            '117': 'Fault: Internal interlock opened. Contact S-P.',
            '118': 'Fault: CDRH interlock open.',
            '119': 'Fault: Power supply interlock. Check cable.',
            '120': 'Fault: Key switch interlock. Turn key.',
            '129': 'Fault: Very high humidity. Change purge cartridge.',
            '130': 'Warning: High humidity. Change purge cartridge soon.',
            '481': 'Fault: Slow diode ramp. Contact S-P.',
            '482': 'Fault: Low fs osc power. Contact S-P.',
            '483': 'Fault: low FTO power. Try different wavelengths. Contact S-P.'}
        # Variables
        #######################################################################
        # Not intended to be accessed directly, only through properties
        self._com_time = com_time
        self._state = 0
        self._opo_wl = 0
        self._main_shutter = 0
        self._fixed_shutter = 0
        self._states = ['Initializing', 'Ready to turn on',
                        'Turning on and/or optimizing', 'RUN', 'Moving to Align mode',
                        'Align mode', 'Exiting Align mode', 'Reserved']

        # Access directly
        self.diode1_temp = ''
        self.diode2_temp = ''
        self.humidity = ''
        self.diode1_curr = ''
        self.diode2_curr = ''
        self.diode1_hrs = ''
        self.diode2_hrs = ''

        # Initialize the values where needed
        self.write(b'WAVelength?', self._com_time)
        self._opo_wl = int(self.read().strip())
        time.sleep(self._com_time)
        self.laser_hrs()
        time.sleep(self._com_time)
        self.laser_stats()

    # Read errors is same command as query state but separate functions to allow
    # flexibility in error handling
    def query_state(self):
        self.write(b'*STB?', self._com_time)
        s = int(self.read())
        masked = s & 0x007F0000
        self._state = masked >> 16
        return s

    def check_errors(self):
        full_state = self.query_state()
        try:
            masks = [0x00000200, 0x00000400, 0x00000800, 0x00001000, 0x00004000,
                 0x00008000]
            codes = []
            for mask in masks:
                masked = s & mask
                codes.append([bool(masked)])
            if any(codes):
                raise OperationError
        except OperationError as e:
            self.last_action = e.msg
        except Exception as e:
            self.last_action = 'check errors. %s' % (str(e))
        finally:
            return full_state

    def read_history(self):
        # Note: The Insight manual in the description of the serial commands
        # lists the history code as 'READ:HIStory?'. This is incorrect.
        # Appendix B, where the codes are explained cites the correct code:
        # 'READ:AHIS?'
        try:
            self.write(b'READ:AHIS?', self._com_time)
            codes = self.read().strip().split(' ')
            print(codes)
            string = ''
            for code in codes:
                print(code)
                print(self.fault_codes[code])
                string += '%s: %s\n' (code, self.fault_codes[code])

            self.last_action = 'Read from history buffer.'
            return string
        except Exception as e:
            self.last_action = 'Read history. %s' % (str(e))

    def laser_hrs(self):
        self.write(b'READ:PLASer:DIODe1:HOURS?', self._com_time)
        self.diode1_hrs = self.read().strip()
        self.write(b'READ:PLASer:DIODe2:HOURS?', self._com_time)
        self.diode2_hrs = self.read().strip()

    def laser_stats(self):
        self.write(b'READ:PLASer:DIODe1:TEMPerature?', self._com_time)
        self.diode1_temp = self.read().strip()
        self.write(b'READ:PLASer:DIODe2:TEMPerature?', self._com_time)
        self.diode2_temp = self.read().strip()

        self.write(b'READ:HUMidity?', self._com_time)
        self.humidity = self.read().strip()

        self.write(b'READ:PLASer:DIODe1:CURRent?', self._com_time)
        self.diode1_curr = self.read().strip()
        self.write(b'READ:PLASer:DIODe2:CURRent?', self._com_time)
        self.diode2_curr = self.read().strip()

    def turnon(self):
        try:
            self.write(b'ON', self._com_time)
            self.check_errors()
            self.last_action = 'Laser turning on.'
        except OperationError as e:
            self.last_action = e.msg
        except Exception as e:
            self.last_action = 'turnon. %s' % (str(e))

    def turnoff(self):
        try:
            self.write(b'OFF', self._com_time)
            self.check_errors()
            self.last_action = 'Laser entering hibernate mode.'
        except OperationError as e:
            self.last_action = e.msg
        except Exception as e:
            self.last_action = 'turnoff. %s' % (str(e))

    @property
    def state(self):
        if self._state < 25:
            return self._states[0]
        elif self._state == 25:
            return self._states[1]
        elif self._state < 50:
            return self._states[2]
        elif self._state == 50:
            return self._states[3]
        elif self._state < 60:
            return self._states[4]
        elif self._state == 60:
            return self._states[5]
        elif self._state < 70:
            return self._states[6]
        else:
            return self._states[7]

    @property
    def opo_wl(self):
        return self._opo_wl

    @opo_wl.setter
    def opo_wl(self, val):
        try:
            print(b'WAVelength %s' % (val))
            self.write(b'WAVelength %s' % (val), self._com_time)
            self.check_errors()
            self.write(b'WAVelength?', self._com_time)
            if int(self.read()) != val:
                raise TuningError

            self._opo_wl = int(self.read().strip())
            self.last_action = 'Wavelength changed to: ' % (self._opo_wl)
        except OperationError as e:
            self.last_action = e.msg
        except TuningError as e:
            self.last_action = e.msg
        except Exception as e:
            self.last_action = 'Opo_wl setter. %s' % (str(e))

    @property
    def main_shutter(self):
        return self._main_shutter

    @main_shutter.setter
    def main_shutter(self, val):
        msg = ['closed.', 'opened.']
        try:
            self.write(b'SHUTter %i' % (val), self._com_time)
            self.check_errors()
            self._main_shutter = val
            self.last_action = 'Main shutter %s' % (msg[val])
        except OperationError as e:
            self.last_action = e.msg
        except Exception as e:
            self.last_action = 'Main shutter setter. %s' % (str(e))

    @property
    def fixed_shutter(self):
        return self._fixed_shutter

    @fixed_shutter.setter
    def fixed_shutter(self, val):
        msg = ['closed.', 'opened.']
        try:
            self.write(b'IRSHUTter %i' % (val), self._com_time)
            self.check_errors()
            self._fixed_shutter = val
            self.last_action = 'Fixed shutter %s' % (msg[val])
        except OperationError as e:
            self.last_action = e.msg
        except Exception as e:
            self.last_action = 'Fixed shutter setter. %s' % (str(e))


    # Need deepsee stuff