#! /usr/bin/env python

import pyforms
import threading
from .devices.delaystage import *
from .controller import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class StageController(DelayStage, Controller):
    def __init__(self, port, com_time, formset):
        DelayStage.__init__(self, port=port, com_time=com_time)
        Controller.__init__(self, formset, 'Delay Stage')
        self.set_margin(10)

    ############################################################################
    # GUI Widgets

    def _widgets(self):
        # Action and error log from parent Controller class
        Controller._widgets(self)

        # Home, Enable and Disable stage buttons
        self._home_button = ControlButton('Home')
        self._home_button.value = self._home
        self._disable_button = ControlButton('Disable')
        self._disable_button.value = self._disable
        self._enable_button = ControlButton('Enable')
        self._enable_button.value = self._enable

        # Motion widgets
        self._pos_label = ControlLabel('%f' % (self.pos))
        self.gotopos_text = ControlText('Move to position:')
        self.absmov_button = ControlButton('>')
        self.absmov_button.value = self._absmov

        self._movfor_button = ControlButton('>>')
        self._movfor_button.value = self._movfor
        self._relmov_text = ControlText()
        self._movrev_button = ControlButton('<<')
        self._movrev_button.value = self._movrev

        # Velocity and acceleration widgets
        self._vel_button = ControlButton('Set')
        self._vel_button.value = self._set_vel
        self._vel_text = ControlText('Set velocity:')
        self._vel_label = ControlLabel('%f' % (self.vel))

        self._accel_button = ControlButton('Set')
        self._accel_button.value = self._set_accel
        self._accel_text = ControlText('Set acceleration:')
        self._accel_label = ControlLabel('%f' % (self.accel))

        # State of the stage
        self._state_label = ControlLabel('%s' % (self.state))

    ############################################################################
    # Home and enable stage functions

    def _disable(self):
        self.disable()
        self._state_label.value = self.state
        self._update_history()

    def _enable(self):
        self.enable()
        self._state_label.value = self.state
        self._update_history()

    def _home(self):
        self.home()
        self._state_label.value = self.state
        self._update_history()

    ############################################################################
    # Motion functions

    def _movfor(self):
        try:
            relmove = float(self._relmov_text.value)
            self.pos = (self.pos + relmove)
            self._pos_label.value = '%f' % (self.pos)
        except TypeError and ValueError:
            self.last_action = 'Improper value entered for motion.'
        finally:
            self._update_history()

    def _movrev(self):
        try:
            relmove = -1*float(self._relmov_text.value)
            self.pos = (self.pos + relmove)
            self._pos_label.value = '%f' % (self.pos)
        except TypeError and ValueError:
            self.last_action = 'Improper value entered for motion.'
        finally:
            self._update_history()

    def _absmov(self):
        try:
            self.pos = float(self.gotopos_text.value)
            self._pos_label.value = '%f' % (self.pos)
        except TypeError and ValueError:
            self.last_action = 'Improper value entered for motion.'
        finally:
            self._update_history()

    ############################################################################
    # Velocity and acceleration functions

    def _set_vel(self):
        try:
            self.vel = float(self._vel_text.value)
            self._vel_label.value = '%f' % (self.vel)
        except TypeError and ValueError:
            self.last_action = 'Improper value entered for velocity'
        finally:
            self._update_history()

    def _set_accel(self):
        try:
            self.accel = float(self._accel_text.value)
            self._accel_label.value = '%f' % (self.accel)
        except TypeError and ValueError:
            self.last_action = 'Improper value entered for acceleration'
        finally:
            self._update_history()

    ############################################################################
    # Overload Controller parent _status function

    def _status(self):
        while 1:
            time.sleep(1)
            self.query_state()
            self._state_label.value = self.state
            self._pos_label.value = '%f' % (self.pos)
            self._vel_label.value = '%f' % (self.vel)
            self._accel_label.value = '%f' % (self.accel)