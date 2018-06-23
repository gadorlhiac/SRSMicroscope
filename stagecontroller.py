#! /usr/bin/env python

import pyforms
import threading
from devices.delaystage import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class StageController(DelayStage, BaseWidget):
    def __init__(self):
        DelayStage.__init__(self, port='/dev/tty2', com_time=0.1)
        BaseWidget.__init__(self, 'Delay Stage Controls')
        self.set_margin(10)

        self._home_button = ControlButton('Home')
        self._home_button.value = self.home
        self._disable_button = ControlButton('Disable')
        self._disable_button.value = self.disable
        self._enable_button = ControlButton('Enable')
        self._enable_button.value = self.enable

        self._pos_label = ControlLabel('%f' % (self.pos))
        self._gotopos_text = ControlText('Move to position:')
        self._absmov_button = ControlButton('>')
        self._absmov_button.value = self._absmov

        self._movfor_button = ControlButton('>>')
        self._movfor_button.value = self._movfor
        self._relmov_text = ControlText()
        self._movrev_button = ControlButton('<<')
        self._movrev_button.value = self._movrev

        self._action_history = ControlTextArea('Action and Error History')
        self._action_history.readonly = True
        self._update_history()
        self._state_label = ControlLabel('%s' % (self.state))

        self.organization()

        queryThread = threading.Thread(target=self._stage_status)
        queryThread.start()

    def _stage_status(self):
        while 1:
            time.sleep(2)
            self.query_state()
            self._state_label.value = self.state

    def _movfor(self):
        try:
            relmove = float(self._relmov_text.value)
            self.pos = (self.pos + relmove)
            self._update_history()
        except TypeError and ValueError:
            self.last_action = 'Improper value entered for motion.'
            self._update_history()

    def _movrev(self):
        try:
            relmove = -1*float(self._relmov_text.value)
            self.pos = (self.pos - relmove)
            self._update_history()
        except TypeError and ValueError:
            self.last_action = 'Improper value entered for motion.'
            self._update_history()

    def _absmov(self):
        try:
            self.pos = float(self._gotopos_text.value)
            self._update_history()
        except TypeError and ValueError:
            self.last_action = 'Improper value entered for motion.'
            self._update_history()

    def _update_history(self):
        t = time.asctime(time.localtime())
        self._action_history.__add__('%s: %s' % (t, self.last_action))

    def organization(self):
        self.formset = [
        ('_home_button', '', '_disable_button', '','_enable_button'),
        ('', 'h5:Current Position (mm):', '_pos_label'),
        ('_gotopos_text', '', '_absmov_button'),
        ('h5:Make a relative move (mm)'),
        ('_movrev_button', '', '_relmov_text', '', '_movfor_button'),
        ('h5:Delay Stage State:','_state_label'),
        ('_history')
        ]

if __name__ == "__main__" : pyforms.start_app(StageController)