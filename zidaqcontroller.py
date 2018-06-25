#! /usr/bin/env python

import pyforms
import time
import threading
import matplotlib.pyplot as plt
import numpy as np
from servers.zidaq import *
from gui.ControlMatplotlib import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class ziDAQController(ziDAQ, BaseWidget):
    def __init__(self):
        ziDAQ.__init__(self)
        BaseWidget.__init__(self, 'ZI HF2LI')
        self.set_margin(10)

        self.test = ControlMatplotlib(default=self._scope)


        self.scopeThread = threading.Thread(target=self._plot_scope)
        self.scopeThread.start()

    def _plot_scope(self):
        while 1:
            time.sleep(0.05)
            self._poll_scope()
            self.test.value = self._scope


if __name__ == "__main__" : pyforms.start_app(ziDAQController)