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
    """
    Facilitates serial communication with Insight DS+ laser.

    Args:
        port (str): COM for serial communication.  This is a windows feature.
        com_time (float): wait time to allow read/write of serial commands.
    """
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
        #######################################################################
        # Variables

        # Not intended to be accessed directly, only through properties
        self._com_time = com_time
        self._opo_wl = 0
        self._main_shutter = 0
        self._fixed_shutter = 0

        self._state = 0
        self._states = ['Initializing', 'Ready to turn on',
                        'Turning on and/or optimizing', 'RUN', 'Moving to Align mode',
                        'Align mode', 'Exiting Align mode', 'Reserved']

        self._dsmpos = '50'
        self._dsmmin = '0'
        self._dsmmax = '100'

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

        self.write(b'CONT:DSMPOS?', self._com_time)
        self._dsmpos = self.read().strip()

        self.write(b'CONT:SLMIN?', self._com_time)
        self._dsmmin = self.read().strip()

        self.write(b'CONT:SLMAX?', self._com_time)
        self._dsmmax = self.read().strip()

        time.sleep(self._com_time)
        self.laser_hrs()
        time.sleep(self._com_time)
        self.laser_stats()

    ############################################################################
    # Laser on/off

    def turnon(self):
        """Turn laser on."""
        try:
            self.write(b'ON', self._com_time)
            self.check_errors()
            self.last_action = 'Laser turning on.'
        except OperationError as e:
            self.last_action = 'Operation error turning on: %s' % (str(e))
        except Exception as e:
            self.last_action = 'Error turning on: %s' % (str(e))

    def turnoff(self):
        """Turn laser off.  Enters hibernate mode"""
        try:
            self.write(b'OFF', self._com_time)
            self.check_errors()
            self.last_action = 'Laser entering hibernate mode.'
        except OperationError as e:
            self.last_action = 'Operation error turning off: %s' % (str(e))
        except Exception as e:
            self.last_action = 'Error turning off: %s' % (str(e))

    ############################################################################
    # Laser state and error history

    # Read errors is same command as query state but separate functions to allow
    # flexibility in error handling
    def query_state(self):
        """Gets current state and any errors."""
        self.write(b'*STB?', self._com_time)
        s = int(self.read())
        masked = s & 0x007F0000
        self._state = masked >> 16
        self._main_shutter = s & 0x00000004
        self._fixed_shutter = s & 0x00000008
        return s

    def check_errors(self):
        """As query state, but returns more information"""
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
            self.last_action = 'Operation error while checking errors: %s' % (str(e))
        except Exception as e:
            self.last_action = 'Error while checking errors: %s' % (str(e))
        finally:
            return full_state

    def read_history(self):
        """Reads error code history from the insight startup buffer"""
        # Note: The Insight manual in the description of the serial commands
        # lists the history code as 'READ:HIStory?'. This is incorrect.
        # Appendix B, where the codes are explained cites the correct code:
        # 'READ:AHIS?'
        try:
            self.write(b'READ:AHIS?', self._com_time)
            codes = self.read().strip().split(' ')
            string = ''
            for code in codes:
                string += '%s: %s\n' % (code, self.fault_codes[code])

            self.last_action = 'Read from history buffer.'
            return string
        except Exception as e:
            self.last_action = 'Error while reading history: %s' % (str(e))

    # Number of diode on hours
    def laser_hrs(self):
        """Reads the laser diode hours"""
        self.write(b'READ:PLASer:DIODe1:HOURS?', self._com_time)
        self.diode1_hrs = self.read().strip()
        self.write(b'READ:PLASer:DIODe2:HOURS?', self._com_time)
        self.diode2_hrs = self.read().strip()

    # Temperature, humidity and diode current
    def laser_stats(self):
        """Reads temperature, humidity and current"""
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

    ############################################################################
    # Accessible properties for laser state OPO wavelength tuning, and shutter
    # control

    # Current laser status
    @property
    def state(self):
        """Property to return current state in text form"""
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

    # For OPO tuning
    @property
    def opo_wl(self):
        """Property to return current OPO wl"""
        return self._opo_wl

    @opo_wl.setter
    def opo_wl(self, val):
        """
        OPO wavelength setter.  Writes to change, and reads back current wavelength
        as well as the new DeepSee position.
        Args:
            val (int): Wavelength, 680-1300.
        """
        try:
            self.write(b'WAVelength %i' % (val), self._com_time + 2)
            self.check_errors()
            self.write(b'WAVelength?', self._com_time)

            wl = int(self.read().strip())
            if wl != val:
                raise TuningError

            self._opo_wl = wl
            pos = self.dsmpos
            self.last_action = 'Wavelength changed to: %i. DSM position %s' \
                                                        % (self._opo_wl, pos)
        except OperationError as e:
            self.last_action = 'Operation error changing wavelength: %s' % (str(e))
        except TuningError as e:
            self.last_action = str(e)
        except Exception as e:
            self.last_action = 'Error while changing wavelength: %s' % (str(e))

    # Shutter control
    @property
    def main_shutter(self):
        """Property for main shutter status.  Returns 1 if open"""
        return self._main_shutter

    @main_shutter.setter
    def main_shutter(self, val):
        """
        Main shutter setter.  Opens or closes the shutter.

        Args:
            val (int): 0 for close, 1 for open.
        """
        msg = ['closed.', 'opened.']
        try:
            self.write(b'SHUTter %i' % (val), self._com_time)
            self.check_errors()
            self._main_shutter = val
            self.last_action = 'Main shutter %s' % (msg[val])
        except OperationError as e:
            self.last_action = 'Operation error while operating shutter: %s' % (str(e))
        except Exception as e:
            self.last_action = 'Error while operating shutter: %s' % (str(e))

    @property
    def fixed_shutter(self):
        """Property for fundamental shutter status. Returns 1 if open"""
        return self._fixed_shutter

    @fixed_shutter.setter
    def fixed_shutter(self, val):
        """
        Fundamental shutter setter.  Opens or closes the shutter.

        Args:
            val (int): 0 for close, 1 for open.
        """
        msg = ['closed.', 'opened.']
        try:
            self.write(b'IRSHUTter %i' % (val), self._com_time)
            self.check_errors()
            self._fixed_shutter = val
            self.last_action = 'Fixed shutter %s' % (msg[val])
        except OperationError as e:
            self.last_action = 'Operation error while operating shutter: %s' % (str(e))
        except Exception as e:
            self.last_action = 'Error while operating shutter: %s' % (str(e))

    ############################################################################
    # DeepSee

    # Get current DeepSee position
    @property
    def dsmpos(self):
        """Property to get the current DeepSee motor position"""
        self.write(b'CONT:DSMPOS?', self._com_time)
        self._dsmpos = self.read().strip()
        return self._dsmpos

    @dsmpos.setter
    def dsmpos(self, val):
        """
        DeepSee motor position setter.  Will not move beyond wavelength dependent min/max values.

        Args:
            val (str): string of a float position from 0 - 100.  Not clear units.
        """
        try:
            self.write(b'CONT:DSMPOS %s' % (val), self._com_time)
            self.check_errors()
            self.write(b'CONT:DSMPOS?', self._com_time)
            self._dsmpos = self.read().strip()
            self.last_action = 'DSMPOS set to %s' % (self._dsmpos)
        except OperationError as e:
            self.last_action = 'Operation error while setting DSMPOS: %s' % (str(e))
        except Exception as e:
            self.last_action = 'Error while setting DSMPOS: %s' % (str(e))

    @property
    def dsmmin(self):
        """Return DeepSee motor min position for current wavelength."""
        self.write(b'CONT:SLMIN?', self._com_time)
        self._dsmmin = self.read().strip()
        return self._dsmmin

    @property
    def dsmmax(self):
        """Return DeepSee motor max position for current wavelength."""
        self.write(b'CONT:SLMAX?', self._com_time)
        self._dsmmax = self.read().strip()
        return self._dsmmax