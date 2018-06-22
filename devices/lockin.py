#! /usr/bin/env python

import numpy as np
import serial
import time

class Lockin(Device):
    def __init__(self, port=None):
        Device.__init__(self, port)