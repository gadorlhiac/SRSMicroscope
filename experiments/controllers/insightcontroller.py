#! /usr/bin/env python

import pyforms
import threading
from .devices.insight import *
#from pyforms import BaseWidget
from .controller import *
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class InsightController(Insight, Controller):
    """
    Extended Insight controller.  Inherits from controller and insight device for
    integration of gui elements and insight ds+ laser control.

    Args:
        port (str): COM for serial communication.  This is a windows feature.
        com_time (float): wait time to allow read/write of serial commands.
        formset (dict/list): dictionary/list for GUI organization.
    """
    def __init__(self, port, com_time, formset):
        Insight.__init__(self, port=port, com_time=com_time)
        Controller.__init__(self, formset, 'Insight DS+ Controls')
        self.set_margin(10)

        self._button_off = 'QPushButton{background-color: light gray; color: black;}'
        self._button_on = 'QPushButton{background-color: #A3C1DA; color: red;}'

        self._update_code_history()

    ############################################################################
    # GUI Widgets

    def _widgets(self):
        """Insight GUI items for operation and status display"""
        # Action and error log from parent Controller class
        Controller._widgets(self)

        # Emission and shutter operation
        self.emission_button = ControlButton('Laser Off')
        self.emission_button.value = self._emission
        self.main_shutter_button = ControlButton('Main Shutter Closed')
        self.main_shutter_button.value = self._main_shutter_control
        self.fixed_shutter_button = ControlButton('1040 nm Shutter Closed')
        self.fixed_shutter_button.value = self._fixed_shutter_control

        # OPO Tuning
        self.tune_wl_val = ControlText('Set Wavelength (nm):')
        self.tune_wl_button = ControlButton('Set')
        self.tune_wl_button.value = self._tune_wl
        self._main_wl_label = ControlLabel('Main Wavelength (nm): %s' \
                                                            % str(self.opo_wl))

        # Define statistics displays
        self._stats_labels()

        self._state_label = ControlLabel('%s' % (self.state))

        # Stored buffer with fault codes
        self._code_history = ControlTextArea('Status Buffer History')
        self._code_history.readonly = True

    def _stats_labels(self):
        """Defines the stats widgets, called in _widgets"""
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

    ############################################################################
    # Laser on/off and shutter control

    def _emission(self):
        """Turns the laser on or off"""
        if self.emission_button.label == 'Laser Off':
            self.turnon()
        else:
            self.turnoff()
            self.emission_button.label = 'Laser Off'
            self.emission_button._form.setStyleSheet(self._button_off)
        self._update_history()

    def _main_shutter_control(self):
        """Opens the shutter for the OPO output."""
        if self.main_shutter == 0:
            self.main_shutter = 1
            self.main_shutter_button.label = 'Main Shutter Open'
            self.main_shutter_button._form.setStyleSheet(self._button_on)
        else:
            self.main_shutter = 0
            self.main_shutter_button.label = 'Main Shutter Closed'
            self.main_shutter_button._form.setStyleSheet(self._button_off)
        self._update_history()

    def _fixed_shutter_control(self):
        """Opens the shutter for the fundamental output."""
        if self.fixed_shutter == 0:
            self.fixed_shutter = 1
            self.fixed_shutter_button.label = '1040 nm Shutter Open'
            self.fixed_shutter_button._form.setStyleSheet(self._button_on)
        else:
            self.fixed_shutter = 0
            self.fixed_shutter_button.label = '1040 nm Shutter Closed'
            self.fixed_shutter_button._form.setStyleSheet(self._button_off)
        self._update_history()


    ############################################################################
    # Laser tuning

    def _tune_wl(self):
        """Tunes OPO wavelength"""
        self.opo_wl = int(self.tune_wl_val.value.strip())
        self._update_history()
        self._main_wl_label.value = 'Main Wavelength (nm): %s' % (str(self.opo_wl))

    ############################################################################
    # Overload Controller parent _status function, and additional logging box for
    # insight

    def _status(self):
        """
        Checks laser status to see if running or shutters open.  Updates stats
        every 30s or 10 minutes
        """
        count = 1 # Counter to see if we should update stats or code history.
        while 1:
            time.sleep(2)
            full_state = self.check_errors()
            self._state_label.value = self.state
            if self.state == 'RUN':
                self.emission_button.label = 'Laser On'
                self.emission_button._form.setStyleSheet(self._button_on)

            if self.main_shutter == 1:
                self.main_shutter_button.label = 'Main Shutter Open'
                self.main_shutter_button._form.setStyleSheet(self._button_on)

            if self.fixed_shutter == 1:
                self.fixed_shutter_button.label = '1040 nm Shutter Open'
                self.fixed_shutter_button._form.setStyleSheet(self._button_on)

            count += 1
            if count % 15 == 0: # Every 30 s
                self.laser_stats()
                self._diode1_temp_label.value = 'Diode 1 Temperature: %s' % (self.diode1_temp)
                self._diode2_temp_label.value = 'Diode 2 Temperature: %s' % (self.diode2_temp)
                self._diode1_curr_label.value = 'Diode 1 Current: %s' % (self.diode1_curr)
                self._diode2_curr_label.value = 'Diode 2 Current: %s' % (self.diode2_curr)
            elif count == 300: # Every 10 minutes
                self._update_code_history()
                count = 1

    def _update_code_history(self):
        """Writes the error code history"""
        t = time.asctime(time.localtime())
        string = self.read_history()
        self._code_history += 'Time of buffer reading: %s\n %s' \
                                                                % (t, string)
        self._update_history()

    @property
    def code_history(self):
        """Property to retrieve the error code history"""
        return self._code_history