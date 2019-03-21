#! /usr/bin/env python

import pyforms
import threading
from .devices.delaystage import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class StageController(DelayStage, BaseWidget):
    def __init__(self, port, com_time):
        DelayStage.__init__(self, port=port, com_time=com_time)
        BaseWidget.__init__(self, 'Delay Stage Controls')
        self.set_margin(10)

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

        # Activity log
        self._action_history = ControlTextArea('Action and Error Log')
        self._action_history.readonly = True
        self._update_history()

        # State of the stage
        self._state_label = ControlLabel('%s' % (self.state))

        self._organization()

        # Constant querying thread
        self.queryThread = threading.Thread(name='Stage Query Thread', target=self._stage_status)
        self.queryThread.daemon = True
        self.queryThread.start()

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
    # Logging

    def _stage_status(self):
        while 1:
            time.sleep(1)
            self.query_state()
            self._state_label.value = self.state
            self._pos_label.value = '%f' % (self.pos)
            self._vel_label.value = '%f' % (self.vel)
            self._accel_label.value = '%f' % (self.accel)

    def _update_history(self):
        t = time.asctime(time.localtime())
        self._action_history += '%s: %s' % (t, self.last_action)

    ############################################################################
    # GUI organization

    def _organization(self):
        self.formset = [
        ('h5:Delay Stage State:','_state_label'),
        ('', 'h5:Delay Stage Operation', ''),
        ('_home_button', '', '_disable_button', '','_enable_button'),
        ('', 'Current Position (mm):', '_pos_label'),
        ('gotopos_text', '', 'absmov_button'),
        ('Make a relative move (mm)'),
        ('_movrev_button', '', '_relmov_text', '', '_movfor_button'),
        ('', '', ''),
        ('', 'Current Velocity (mm/s):', '_vel_label'),
        ('', '_vel_text', '_vel_button'),
        ('', 'Current Acceleration (mm/s2):', '_accel_label'),
        ('', '_accel_text', '_accel_button'),
        ('_action_history')
        ]

#if __name__ == "__main__" : pyforms.start_app(StageController)