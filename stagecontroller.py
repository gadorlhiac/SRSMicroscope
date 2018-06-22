#! /usr/bin/env python

import pyforms
import threading
from devices.delaystage import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlNumber, ControlDockWidget

class StageController(DelayStage, BaseWidget):
    def __init__(self):
        DelayStage.__init__(self, port='/dev/tty2', com_time=0.1)
        BaseWidget.__init__(self, 'Delay Stage Controls')

        self._pos_label = ControlLabel('%f' % (self.pos))
        self._gotopos_text = ControlText('Move to position:')
        self._absmov_button = ControlButton()
        self._absmov_button.value = self._absmov

        self._movfor_button = ControlButton('Forward')
        self._movfor_button.value = self._movfor
        self._relmov_text = ControlText()
        self._movrev_button = ControlButton('Reverse')
        self._movrev_button.value = self._movrev

        self._state_label = ControlLabel('%s' % (self.state))

        self.organization()

        queryThread = threading.Thread(target=self._stage_status)
        queryThread.start()

    def _stage_status(self):
        while 1:
            time.sleep(2)
            self.query_state()
            self._state_label.value = self.state
            print('ell')

    def _movfor(self):
        relmove = float(self._relmov_text.value)
        self.pos = (self.pos + relmov)

    def _movrev(self):
        relmove = -1*float(self._relmov_text.value)
        self.pos = (self.pos - relmov)

    def _absmov(self):
        self.pos = float(self._gotopos_text)

    def organization(self):
        self.formset = [
        ('h5:Current Position (mm):', '_pos_label'),
        ('_gotopos_text', '||', '_absmov_button'),
        ('h5:Make a relative move (mm)'),
        ('_movrev_button', '||', '_relmov_text', '_movfor_button'),
        ('h5:Delay Stage State','_state_label')
        ]

    def update(self):
        self.pos_label.value = "new"

if __name__ == "__main__" : pyforms.start_app(StageController)