#! /usr/bin/env python

from .controllers.insightcontroller import *
from .controllers.stagecontroller import *
from .controllers.zidaqcontroller import *
from pyforms.controls import ControlButton, ControlEmptyWidget
from .experiment import *
import yaml
import time

class Calibrator(BaseWidget):
    """
    Extended experiment class for wavelength vs stage delay.

    Args:
        formset (dict/list): dictionary/list for GUI organization.
        calibfile (str): path to yaml file for calibration, e.g., time 0.
        logdir (str): path for working directory
    """
    def __init__(self, formset, calibfile, logdir):
        Experiment.__init__(self, formset, calibfile, logdir)
        self.set_margin(10)

    def _expmt_widgets(self):
        """Experiment specific GUI objects.  Separate from device GUI objects"""
        # Experiment history log from parent Experiment class
        Experiment._expmt_widgets(self)

        self._wl_range_text = ControlText('Wavelength Range to Calibrate:')

        self._calibrate_button = ControlButton('Calibrate')
        self._calibrate_button.value = self._calibrator

        self._expmt_panel.value = [ self._wl_range_text,
                                    self._calibrate_button,
                                    self.expmt_history]

    ############################################################################
    # Functions for optimizing signal vs delay stage position

    def _get_wavelength_range(self):
        """Parse user specified wavelength calibration range"""
        text = self._wl_range_text.value
        wlrange = text.split('-')
        wlmin = int(wlrange[0])
        wlmax = int(wlrange[1])
        return np.linspace(wlmin, wlmax, wlmin-wlmax+1)

    def _calibrator(self):
        """Start calibration thread with target _calibrate"""
        self._calibratorThread = threading.Thread(target=self._calibrate)
        self._calibratorThread.start()

    def _calibrate(self):
        """
        Call parent _optimize iteratively over wavelength range specified.
        Use current calibration as starting position, if not guess
        """
        wls = self._get_wavelength_range()
        for i, wl in enumerate(wls):
            self.insight.tune_wl_val.value = str(int(wl))
            self.insight.tune_wl_button.click()
            print(wl)
            time.sleep(2)
            try:
                self._optimize(self.t0_dict['stage'][str(int(wl))])
            except KeyError as e:
                self._optimize(self.t0_dict['stage'][str(int(wl) - 1)] + .25)