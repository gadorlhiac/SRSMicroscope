#!/usr/bin/env python

import serial
import time
from AnyQt.QtCore import QObject

class ComError(Exception):
    """Exception for no com input -- For delay stage and insight"""
    def __init__(self):
        self.msg = 'Enter communication port as string, e.g. \'COM1\''

    def __str__(self):
        return self.msg

class Device(QObject):
    """
    Base device class. Opens serial communications.

    Args:
        port (str): COM port.  Windows assumed.
    """
    num_devices = 0
    def __init__(self, port = None):
        QObject.__init__(self)
        # Communication port must be provided or initialization will fail
        if port == None:
            raise ComError
        try:
            self.com = serial.Serial(timeout=0, baudrate=115200)
            self.com.port = port
            self.last_action = 'Port opened.'
        except serial.SerialException:
            self.last_action = 'Serial port already open.'
        Device.num_devices += 1

    def __del__(self):
        if Device.num_devices != 0:
            Device.num_devices -= 1
        else:
            pass

    def open_com(self):
        """Open the communication port"""
        self.com.open()

    def close_com(self):
        """Close the communication port"""
        self.com.close()

    def write(self, command, waittime):
        """
        Write serial command. Includes newline character.

        Args:
            command (bytes): serial command string as byte type. b''
            waittime (float): time to wait after write before read. Units (s)
        """
        # Commands from sub-class devices don't need to include the newline
        # character as it is included here
        self.com.write(b'%b\n' % (command))
        time.sleep(waittime)

    def read(self):
        """Return a readline from serial buffer as string"""
        return self.com.readline().decode('ascii')