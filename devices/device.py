#! /usr/bin/env python

import serial
import time

class ComError(Exception):
    """Exception for no com input"""
    def __init__(self):
        self.msg = 'Enter communication port as string, e.g. \'COM1\''

    def __str__(self):
        return self.msg

class Device(object):
    num_devices = 0
    def __init__(self, port = None):
        # Communication port must be provided or initialization will fail
        if port == None:
            raise ComError
        try:
            self.com = serial.Serial(timeout=0, baudrate=115200)
            self.com.port = port
        except serial.SerialException:
            print('Serial port already open.')
        Device.num_devices += 1

    def __del__(self):
        if Device.num_devices != 0:
            Device.num_devices -= 1
        else:
            pass

    def open_com(self):
        self.com.open()

    def close_com(self):
        self.com.close()

    def write(self, command, waittime):
        # Commands from sub-class devices don't need to include the newline
        # character as it is included here
        self.com.write(b'%s\n' % (command))
        time.sleep(waittime)

    def read(self):
        return self.com.readline()