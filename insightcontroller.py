#! /usr/bin/env python

import pyforms
import threading
from devices.insight import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlNumber, ControlDockWidget

class InsightController(DelayStage, BaseWidget):
    def __init__(self):
        DelayStage.__init__(self, port='/dev/tty2', com_time=0.1)
        BaseWidget.__init__(self, 'Delay Stage Controls')

if __name__ == "__main__" : pyforms.start_app(InsightController)