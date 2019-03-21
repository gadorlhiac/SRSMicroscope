#! /usr/bin/env python

import pyforms
import threading
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class Controller(BaseWidget):
    def __init__(self, port, com_time):
        BaseWidget.__init__(self, 'Controller')
        self.set_margin(10)

        self._widgets()
        self._update_history()

        # Layout
        self._organization()

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

    ############################################################################
    # GUI organization

    def _organization(self):
        self.formset = [ ('','h5:Logs',''),
                         ('_action_history') ]