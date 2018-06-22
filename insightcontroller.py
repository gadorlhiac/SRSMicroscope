#! /usr/bin/env python

import pyforms
import threading
from devices.insight import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class InsightController(Insight, BaseWidget):
    def __init__(self):
        Insight.__init__(self, port='/dev/tty2', com_time=0.1)
        BaseWidget.__init__(self, 'Insight DS+ Controls')

        self._emission_button = ControlButton('Laser Off')
        self._emission_button.value = self._emission
        self._main_shutter_button = ControlButton('Main Shutter')
        self._main_shutter_button.value = self._main_shutter_control
        self._fixed_shutter_button = ControlButton('1040 nm Shutter')
        self._fixed_shutter_button.value = self._fixed_shutter_control

        self._state_label = ControlLabel('%s' % (self.state))
        self._stats_labels()

        self.area = ControlTextArea()
        self.area.readonly = True
        self.area.__add__('%s\n%s' % (self.diode1_curr, self.diode1_hrs))

        queryThread = threading.Thread(target=self._stage_status)
        queryThread.start()

        statsThread = threading.Thread(target=self._update_stats_labels)
        statsThread.start()

    def _stage_status(self):
        while 1:
            time.sleep(2)
            self.query_state()
            self._state_label.value = self.state

    def _stats_labels(self):
        self._diode1_hrs_label = ControlLabel('Diode 1 Hours: \
                                                %s' % self.diode1_hrs)
        self._diode2_hrs_label = ControlLabel('Diode 2 Hours: \
                                                %s' % self.diode2_hrs)
        self._diode1_temp_label = ControlLabel('Diode 1 Temperature: \
                                                %s' % self.diode1_temp)
        self._diode2_temp_label = ControlLabel('Diode 2 Temperature: \
                                                %s' % self.diode2_temp)
        self._diode1_curr_label = ControlLabel('Diode 1 Current: \
                                                %s' % self.diode1_curr)
        self._diode2_curr_label = ControlLabel('Diode 2 Current: \
                                                %s' % self.diode2_curr)
    # Don't need to bother updating hours
    def _update_stats_labels(self):
        while 1:
            time.sleep(60)
            self.laser_stats()
            self._diode1_temp_label.value = 'Diode 1 Temperature: %s' % \
                                                            self.diode1_temp
            self._diode2_temp_label.value = 'Diode 2 Temperature: %s' % \
                                                            self.diode2_temp
            self._diode1_curr_label.value = 'Diode 1 Current: %s' % \
                                                            self.diode1_curr
            self._diode2_curr_label.value = 'Diode 2 Current: %s' % \
                                                            self.diode2_curr

    def _emission(self):
        if self._emission_button.label == 'Laser Off':
            print('Turning On')
            self.turnon()
        else:
            self.turnoff()

    def _main_shutter_control(self):
        if self.main_shutter == 0:
            self.main_shutter = 1
        else:
            self.main_shutter = 0

    def _fixed_shutter_control(self):
        if self.main_shutter == 0:
            self.fixed_shutter = 1
        else:
            self.fixed_shutter = 0

    def organization(self):
        self.formset = [
        ('', 'h5:Current Position (mm):', '_pos_label'),
        ('_gotopos_text', '', '_absmov_button'),
        ('h5:Make a relative move (mm)'),
        ('_movrev_button', '', '_relmov_text', '', '_movfor_button'),
        ('h5:Delay Stage State','_state_label')
        ]

if __name__ == "__main__" : pyforms.start_app(InsightController)