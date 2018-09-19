#! /usr/bin/env python

import pyforms
import threading
from .devices.insight import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class InsightController(Insight, BaseWidget):
    def __init__(self, port, com_time):
        #Insight.__init__(self, port='/dev/tty2', com_time=0.1)
        Insight.__init__(self, port=port, com_time=com_time)
        BaseWidget.__init__(self, 'Insight DS+ Controls')
        self.set_margin(10)

        # Emission and shutter operation
        self._emission_button = ControlButton('Laser Off')
        self._emission_button.value = self._emission
        self._main_shutter_button = ControlButton('Main Shutter Closed')
        self._main_shutter_button.value = self._main_shutter_control
        self._fixed_shutter_button = ControlButton('1040 nm Shutter Closed')
        self._fixed_shutter_button.value = self._fixed_shutter_control

        # OPO Tuning
        self._main_wl_label = ControlLabel('Main Wavelength (nm): %s' \
                                                            % str(self.opo_wl))
        self._tune_wl_val = ControlText('Set Wavelength (nm):')
        self._tune_wl_button = ControlButton('Set')
        self._tune_wl_button.value = self._tune_wl

        # Define statistics displays
        self._stats_labels()

        # Action and error log
        self._action_history = ControlTextArea('Action and Error Log')
        self._action_history.readonly = True
        self._state_label = ControlLabel('%s' % (self.state))
        self._update_history()

        # Stored buffer with fault codes
        self._code_history = ControlTextArea('Status Buffer History')
        self._code_history.readonly = True
        self._update_code_history()

        # Layout and querying thread
        self._organization()

        self.queryThread = threading.Thread(target=self._insight_status)
        self.queryThread.start()

        #self.statsThread = threading.Thread(target=self._update_stats_labels)
        #self.statsThread.start()

    def _insight_status(self):
        count = 1 # Counter to see if we should update stats or code history.
        while 1:
            time.sleep(2)
            full_state = self.check_errors()
            self._state_label.value = self.state
            if self.state == 'RUN':
                self._emission_button.label = 'Laser On'
                self._emission_button._form.setStyleSheet('QPushButton \
                                                        {background-color: \
                                                        #A3C1DA; color: red;}')
            count += 1
            if count % 15 == 0: # Every 30 s
                self.laser_stats()
                self._diode1_temp_label.value = 'Diode 1 Temperature: %s' % \
                                                            (self.diode1_temp)
                self._diode2_temp_label.value = 'Diode 2 Temperature: %s' % \
                                                            (self.diode2_temp)
                self._diode1_curr_label.value = 'Diode 1 Current: %s' % \
                                                            (self.diode1_curr)
                self._diode2_curr_label.value = 'Diode 2 Current: %s' % \
                                                            (self.diode2_curr)
            elif count == 300: # Every 10 minutes
                self._update_code_history()
                count = 1

    def _stats_labels(self):
        self._diode1_hrs_label = ControlLabel('Diode 1 Hours: \
                                                %s' % (self.diode1_hrs))
        self._diode2_hrs_label = ControlLabel('Diode 2 Hours: \
                                                %s' % (self.diode2_hrs))
        self._diode1_temp_label = ControlLabel('Diode 1 Temperature: \
                                                %s' % (self.diode1_temp))
        self._diode2_temp_label = ControlLabel('Diode 2 Temperature: \
                                                %s'  % (self.diode2_temp))
        self._diode1_curr_label = ControlLabel('Diode 1 Current: \
                                                %s' % (self.diode1_curr))
        self._diode2_curr_label = ControlLabel('Diode 2 Current: \
                                                %s' % (self.diode2_curr))

    def _emission(self):
        if self._emission_button.label == 'Laser Off':
            self.turnon()
        else:
            self.turnoff()
            self._emission_button._form.setStyleSheet('QPushButton \
                                                        {background-color: \
                                                        light gray; color: black;}')
        self._update_history()

    def _main_shutter_control(self):
        if self.main_shutter == 0:
            self.main_shutter = 1
            self._main_shutter_button.label = 'Main Shutter Open'
            self._main_shutter_button._form.setStyleSheet('QPushButton \
                                                        {background-color: \
                                                        #A3C1DA; color: red;}')
        else:
            self.main_shutter = 0
            self._main_shutter_button.label = 'Main Shutter Closed'
            self._main_shutter_button._form.setStyleSheet('QPushButton \
                                                        {background-color: \
                                                        light gray; color: black;}')
        self._update_history()

    def _fixed_shutter_control(self):
        if self.fixed_shutter == 0:
            self.fixed_shutter = 1
            self._fixed_shutter_button.label = '1040 nm Shutter Open'
            self._fixed_shutter_button._form.setStyleSheet('QPushButton \
                                                        {background-color: \
                                                        #A3C1DA; color: red;}')
        else:
            self.fixed_shutter = 0
            self._fixed_shutter_button.label = '1040 nm Shutter Closed'
            self._fixed_shutter_button._form.setStyleSheet('QPushButton \
                                                        {background-color: \
                                                        light gray; color: black;}')
        self._update_history()

    def _tune_wl(self):
        self.opo_wl = int(self._tune_wl_val.value.strip())
        self._update_history()
        self._main_wl_label.value = 'Main Wavelength (nm): %s' \
                                                            % (str(self.opo_wl))

    def _update_history(self):
        t = time.asctime(time.localtime())
        self._action_history += '%s: %s' % (t, self.last_action)

    def _update_code_history(self):
        t = time.asctime(time.localtime())
        string = self.read_history()
        self._code_history += 'Time of buffer reading: %s\n %s' \
                                                                % (t, string)
        self._update_history()

    def _organization(self):
        self.formset = [
        ('', 'h5:Laser Operation', ''),
        ('_emission_button', '_main_shutter_button', '_fixed_shutter_button'),
        ('', 'h5:Wavelength Selection', ''),
        ('_main_wl_label'),
        ('_tune_wl_val','','_tune_wl_button'),
        ('', 'h5:Laser Statistics', ''),
        ('', 'Laser State:', '_state_label', ''),
        ('_diode1_hrs_label', '', '_diode2_hrs_label'),
        ('_diode1_temp_label', '', '_diode2_temp_label'),
        ('_diode1_curr_label', '', '_diode2_curr_label'),
        ('','h5:Logs',''),
        ('_action_history', '||', '_code_history')
        ]

#if __name__ == "__main__" : pyforms.start_app(InsightController)