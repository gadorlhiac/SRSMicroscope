#! /usr/bin/env python

import pyforms
import threading
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class Controller(BaseWidget):
    def __init__(self, formset, title='Controller'):
        BaseWidget.__init__(self, title)
        self.set_margin(10)

        # GUI widgets
        self._widgets()

        # GUI Organization
        self.formset = formset

        # Record initiliazation
        self._update_history()

        # Status query threading
        self.queryThread = threading.Thread(name='%s Query Thread' % (title), target=self._status)
        self.queryThread.daemon = True
        self.queryThread.start()

    ############################################################################
    # GUI Widgets

    def _widgets(self):
        self._action_history = ControlTextArea('Action and Error Log')
        self._action_history.readonly = True


    ############################################################################
    # Logging

    def _update_history(self):
        try:
            t = time.asctime(time.localtime())
            self._action_history += '%s: %s' % (t, self.last_action)
        except NameError as e:
            self.last_action = 'No known connection or action.'

    @property
    def action_history(self):
        return self._action_history

    def _status(self):
        while 1:
            pass