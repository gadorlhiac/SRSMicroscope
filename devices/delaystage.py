#! /usr/bin/env python

import numpy as np
import time
from .device import *

# Commands from sub-class devices don't need to include the newline
# character as it is included here

class PositionerError(Exception):
    _pos_errors = np.array(
        [
          'Not used', 'Not used', 'Not used', 'Not used',
          'Driver overheating', 'Driver fault', 'Not used', 'Not used',
          'No parameters in memory', 'Homing time out', 'Not used',
          'Newport reserved', 'RMS current limit', 'Not used',
          'Positive end of run', 'Negative end'
        ]
     )

    """Exception for positioner error"""
    def __init__(self, error_code):
        mask = []
        for b in map(int, list(error_code)):
            mask.append(bool(b))

        self.msg = ', '.join(_positioner_errors[mask])

    def __str__(self):
        return self.msg

class CommandError(Exception):
    _cmd_errors = {
        '@' : 'No error',
        'A' : 'Unknown message code or floating point controller address',
        'B' : 'Controller address not correct',
        'C' : 'Parameter missing or out of range',
        'D' : 'Command not allowed',
        'E' : 'Home sequence already started.',
        'G' : 'Displacement out of limits.',
        'H' : 'Command not allowed in NOT REFERENCED state.',
        'I' : 'Command not allowed in CONFIGURATION state.',
        'J' : 'Command not allowed in DISABLE state.',
        'K' : 'Command not allowed in READY state.',
        'L' : 'Command not allowed in HOMING state.',
        'M' : 'Command not allowed in MOVING state.',
        'N' : 'Current position out of software limit.',
        'S' : 'Communication Time Out.',
        'U' : 'Error during EEPROM access.',
        'V' : 'Error during command execution.'
    }
    def __init__(self, error_code):
        mask = []
        for b in map(int, list(error_code)):
            mask.append(bool(b))

        self.msg = ', '.join(_positioner_errors[mask])

    def __str__(self):
        return self.msg

class DelayStage(Device):
    def __init__(self, port=None, com_time=0.1):
        self._states = {
            '0A' : 'NOT REFERENCED from RESET.',
            '0B' : 'NOT REFERENCED from HOMING.',
            '0C' : 'NOT REFERENCED from CONFIGURATION.',
            '0D' : 'NOT REFERENCED from DISABLE.',
            '0E' : 'NOT REFERENCED from READY.',
            '0F' : 'NOT REFERENCED from MOVING.',
            '10' : 'NOT REFERENCED - NO PARAMETERS IN MEMORY.',
            '14' : 'CONFIGURATION.',
            '1E' : 'HOMING.',
            '28' : 'MOVING.',
            '32' : 'READY from HOMING.',
            '33' : 'READY from MOVING.',
            '34' : 'READY from DISABLE.',
            '3C' : 'DISABLE from READY.',
            '3D' : 'DISABLE from MOVING.'
        }
        self._com_time = com_time # Wait time for read/write
        self._pos_error = '0000'
        self._cmd_error = '@'
        self._pos = 0
        self._state = '0A'
        # Initialize serial communications with port and open that port
        Device.__init__(self, port)
        self.open_com()

        # 'Home' the delay stage and get current position,
        # a value from -100 to 100 mm

        #print('Homing the delay stage, and entering command receptive state')
        #self.write('1OR', self._com_time)
        #self._pos = None

    def set_home(self):
        self.write('1HT1')

    # Gets the positioner state.  The output is a string with 6 characters such
    # that the first 4 characters correspond to an error code and the last 2
    # to the state of the device.
    def query_state(self):
        self.write('1TS', self._com_time)
        line = self.read()
        self._pos_error = line[3:7]
        self._state = line[7:9]

    @property
    def state(self):
        return self._states[self._state]

    # Stop any motion
    def stop_motion():
        self.write('1ST', self._com_time)

    # Enter DISABLE state
    def disable():
        self.write('1MM0', self._com_time)

    # Re-enter READY state
    def enable():
        self.write('1MM1', self._com_time)

    ############################################################################
    # Poperty and setter functions for delay stage position.
    # Setter function will move the delay stage, using the absolute motion
    # command - NOT the relative motion command.  Time for motion is calculated
    # from relative move, and is used as the program waiting time.

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, val):
        try:
            relative_move = np.abs(self._pos - value)

            self.write('1PT%f' % relative_move, self._com_time)
            t = float(self.read()[3:])

            self.write('1PA%f' % val, t + self._com_time)

            self.write('1TE', self._com_time) # Last command error
            self._cmd_error = self.read()[3]

            if self._cmd_error != '@':
                raise CommandError(self._cmd_error)

            self.query_state()
            if int(self._error, 16):
               raise PositionerError(self._pos_error)

            self.write('1TP?', self._com_time)
            self._pos = float(self.read()[3:])

        except PositionerError:
            print('Position Not Moved!')

        except CommandError:
            print('Position Not Moved!')

    ############################################################################
    # Velocity property and setter functions.
    @property
    def vel(self):
        return self._vel

    @vel.setter
    def vel(self, val):
        try:
            self.write('1VA%f' % val, self._com_time)

            self.write('1TE', self._com_time) # Last command error
            self._cmd_error = self.read()[3]

            if self._cmd_error != '@':
                raise CommandError(self._cmd_error)

            self.query_state()
            if int(self._error, 16):
               raise PositionerError(self._pos_error)

        except PositionerError:
            print('Position Not Moved!')

        except CommandError:
            print('Position Not Moved!')

        self.write('1VA?', self._com_time)
        self._vel = float(self.read()[3:])

    ############################################################################
    # Acceleration property and setter functions.

    @property
    def accel(self):
        return self._accel

    @property
    def accel(self, val):
        try:
            self.write('1AC%f' % val, self._com_time)

            self.write('1TE', self._com_time) # Last command error
            self._cmd_error = self.read()[3]

            if self._cmd_error != '@':
                raise CommandError(self._cmd_error)

            self.query_state()
            if int(self._error, 16):
               raise PositionerError(self._pos_error)

        except PositionerError:
            print('Position Not Moved!')

        except CommandError:
            print('Position Not Moved!')

        self.write('1AC?', self._com_time)
        self._accel = float(self.read()[3:])
           