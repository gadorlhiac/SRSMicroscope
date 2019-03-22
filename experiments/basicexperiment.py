#! /usr/bin/env python

from .controllers.insightcontroller import *
from .controllers.stagecontroller import *
from .controllers.zidaqcontroller import *
from pyforms.controls import ControlButton, ControlEmptyWidget
from .experiment import *
import yaml
import time

class BasicExperiment(Experiment):
    def __init__(self, formset, calibfile, logdir):
        # Variables defined only for the experiment and not laser etc
        self.omega = 1000 # Raman shift

        Experiment.__init__(self, formset, calibfile, logdir)
        self.set_margin(10)

        self._calc_omega()
        # Calibration dictionary structure: self.calib_dict = {'stage': {}, 'dsmpos': {}}

    ############################################################################
    # GUI Widgets

    def _expmt_widgets(self):
        # Experiment history log from parent Experiment class
        Experiment._expmt_widgets(self)
        self._wl_label = ControlLabel('Main Wavelength: %s' \
                                                % (str(self.insight.opo_wl)))
        self._omega_text = ControlText('Raman Shift (cm-1):')
        self._omega_text.value = '%.2f' % (self.omega)
        self._set_omega_button = ControlButton('Set Omega')
        self._set_omega_button.value = self._set_omega

        self._dwell_text = ControlText('Pixel Dwell Time (us):')
        self._dwell_text.value = '2'
        self._set_dwell_button = ControlButton('Set Lockin')
        self._set_dwell_button.value = self._set_dwell

        self._optimize_button = ControlButton('Optimize Signal')
        self._optimize_button.value = self._optimizer

        self._tuned_spectrum_button = ControlButton('Tuned Spectrum')
        self._tuned_spectrum_button.value = self._tuned_spectrum

        self._expmt_panel.value = [ self._wl_label,
                                    self._dwell_text, self._set_dwell_button,
                                    self._omega_text, self._set_omega_button,
                                    self._optimize_button,
                                    self._tuned_spectrum_button,
                                    self.expmt_history]

    ############################################################################
    # Wavelength/wavenumber conversion functions

    def _calc_omega(self):
        self.omega = (10000000./self.insight.opo_wl) - (10000000./1040.)

    def _calc_wl(self, omega):
        wl = ((10000000.)*1040.)/((1040.*omega)+10000000.)
        return int(round(wl))

    ############################################################################
    # Set dwell time and Raman shift

    def _set_dwell(self):
        dwell = float(self._dwell_text.value.strip())/1e6
        self.zidaq.tc_text.value = str(dwell/3.)
        self.zidaq.set_tc_button.click()
        tc = self.zidaq.tc

        self.zidaq.rate_text.value = str(2./dwell)
        self.zidaq.set_rate_button.click()
        rate = self.zidaq.rate

        msg = 'Lockin TC changed to %f.  Sampling rate changed to %f' % (tc, rate)

    def _set_omega(self):
        # Need access to tune_wl_val and tune_wl_button on the insight
        # Need access to absmov_button and gotopos_text on the stage
        try:
            # Tune wl
            wl = self._calc_wl(float(self._omega_text.value))
            self.insight.tune_wl_val.value = str(wl)
            self.insight.tune_wl_button.click()
            self._calc_omega()
            self._omega_text.value = '%.2f' % (self.omega)
            self._wl_label.value = 'Main Wavelength: %s' % (str(self.insight.opo_wl))

            # Tune delay appropriately
            move = self.calib_dict['stage'][str(wl)]
            self.delaystage.gotopos_text.value = str(move)
            self.delaystage.absmov_button.click()

            msg = 'Wavelength changed to %i nm.  Delay stage moved.' % (wl)
            self._update_history(msg)
        except KeyError as e:
            msg = 'Wavelength changed to %i nm. No delay stage calibration' % (wl)
            self._update_history(msg)
        except Exception as e:
            msg = 'Wavelength note changed. %s' % (str(e))
            self._update_history(msg)

    ############################################################################
    # Spectra and image functions

    def _tuned_spectrum(self):
        keys = self.calib_dict['stage'].keys()
        omegas = np.zeros([len(keys)])
        srs = np.zeros([len(keys)])
        for i, wl in enumerate(keys):
            print(wl)
            self.insight.tune_wl_val.value = str(wl)
            self.insight.tune_wl_button.click()
            time.sleep(3)
            self._calc_omega()
            self._omega_text.value = '%.2f' % (self.omega)

            move = self.calib_dict['stage'][str(wl)]
            self.delaystage.gotopos_text.value = str(move)
            self.delaystage.absmov_button.click()
            time.sleep(1)

            x, y = self.zidaq.poll()
            omegas[i] = self.omega
            srs[i] = np.mean((x**2 + y**2)**0.5)

    ############################################################################
    # Functions for optimizing signal vs delay stage position

    def _optimizer(self):
        self._optimizerThread = threading.Thread(name='Signal Optimizer Thread', \
                            target=self._optimize, args=(self.delaystage.pos,))
        self._optimizerThread.daemon = True
        self._optimizerThread.start()