#!/usr/bin/python

from pyforms import BaseWidget
from pyforms.controls import ControlLabel

class AlertWindow(BaseWidget):
    def __init__(self, category, msg):
        BaseWidget.__init__(self, '%s' % (category))
        self.msg = ControlLabel('%s' % (msg))