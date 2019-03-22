#! /usr/bin/env python

import pyforms
import threading
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class Controller(BaseWidget):
    """
    Base class Controller.  Integrates GUI elements with device/server control.

    Args:
        formset (dict/list): dictionary/list for GUI organization.
        title (str): name of GUI window.
    """
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
        """Basic device GUI items"""
        self._action_history = ControlTextArea('Action and Error Log')
        self._action_history.readonly = True


    ############################################################################
    # Logging

    def _update_history(self):
        """Update device's action history"""
        try:
            t = time.asctime(time.localtime())
            self._action_history += '%s: %s' % (t, self.last_action)
        except NameError as e:
            self.last_action = 'No known connection or action.'

    @property
    def action_history(self):
        """Property to return action history"""
        return self._action_history

    def _status(self):
        """Empty device status function"""
        while 1:
            pass