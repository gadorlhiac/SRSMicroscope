#! /usr/bin/env python

from .controllers.insightcontroller import *
from .controllers.stagecontroller import *
from .controllers.zidaqcontroller import *
from pyforms.controls import ControlButton, ControlEmptyWidget
from .controllers.gui import ControlMatplotlib
from .experiment import *
import yaml
import time

from AnyQt.QtCore import QThread

class BasicExperiment(Experiment):
    """
    Extended experiment class for fsSRS imaging.

    Args:
        formset (dict/list): dictionary/list for GUI organization.
        calibfile (str): path to yaml file for calibration, e.g., time 0.
        logdir (str): path for working directory
    """
    def __init__(self, formset, calibfile, logdir):
        # Variables defined only for the experiment and not laser etc
        self._omega = 1000 # Raman shift

        Experiment.__init__(self, formset, calibfile, logdir)
        self.set_margin(10)

        self._calc_omega()
        #self._figure = plt.figure(1)
        #self._ax = self._figure.add_subplot(111)
        #self._img = self._ax.imshow(np.zeros([512, 512]))
        #plt.ion()
        self._dwell = float(self._dwell_text.value.strip())/1e6
        # Calibration dictionary structure: self.calib_dict = {'stage': {}, 'dsmpos': {}}

    ############################################################################
    # GUI Widgets

    def _expmt_widgets(self):
        """Experiment specific GUI objects.  Separate from device GUI objects"""
        # Experiment history log from parent Experiment class
        Experiment._expmt_widgets(self)
        self._wl_label = ControlLabel('Main Wavelength: %s' \
                                                % (str(self._insight.opo_wl)))
        self._omega_text = ControlText('Raman Shift (cm-1):')
        self._omega_text.value = '%.2f' % (self._omega)
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

        self._img = ControlMatplotlib(value=np.zeros([512,512]))
        self._acquire_button = ControlButton('Acquire Image')
        self._acquire_button.value = self._rtd

        self._expmt_panel.value = [ self._wl_label,
                                    self._dwell_text, self._set_dwell_button,
                                    self._omega_text, self._set_omega_button,
                                    self._optimize_button, self._acquire_button,
                                    self._tuned_spectrum_button,
                                    self._img,
                                    self._expmt_history]

    ############################################################################
    # Wavelength/wavenumber conversion functions

    def _calc_omega(self):
        """Return Raman shift from current OPO wavelength."""
        self._omega = (10000000./self._insight.opo_wl) - (10000000./1040.)

    def _calc_wl(self, omega):
        """For a Raman shift find the wavelength OPO needs to be tuned to."""
        wl = ((10000000.)*1040.)/((1040.*omega)+10000000.)
        return int(round(wl))

    ############################################################################
    # Set dwell time and Raman shift

    def _set_dwell(self):
        """Changing pixel dwell time automatically adjusts zidaq TC and sample rate."""
        self._dwell = float(self._dwell_text.value.strip())/1e6
        self._zidaq.tc_text.value = str(self._dwell/3.)
        self._zidaq.set_tc_button.click()
        tc = self._zidaq.tc

        self._zidaq.rate_text.value = str(2./dwell)
        self._zidaq.set_rate_button.click()
        rate = self._zidaq.rate

        msg = 'Lockin TC changed to %f.  Sampling rate changed to %f' % (tc, rate)

    def _set_omega(self):
        """Appropriately tune wavelength and delay stage for a specified omega"""
        # Need access to tune_wl_val and tune_wl_button on the insight
        # Need access to absmov_button and gotopos_text on the stage
        try:
            # Tune wl
            wl = self._calc_wl(float(self._omega_text.value))
            self._insight.tune_wl_val.value = str(wl)
            self._insight.tune_wl_button.click()
            self._calc_omega()
            self._omega_text.value = '%.2f' % (self._omega)
            self._wl_label.value = 'Main Wavelength: %s' % (str(self._insight.opo_wl))

            # Tune delay appropriately
            move = self._calib_dict['stage'][str(wl)]
            self._delaystage.gotopos_text.value = str(move)
            self._delaystage.absmov_button.click()

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

    def _rtd(self):
        self._daq_reader = QThread()
        self._zidaq.start_daq((512, 512), self._dwell, num_frames=3)
        self._zidaq.moveToThread(self._daq_reader)
        self._zidaq.daqData.connect(self._img.read_daq)
        self._daq_reader.started.connect(self._zidaq.read_daq)
        self._daq_reader.start()


    def update_plot1(self,y):
        if self.dgen1.mutex.tryLock():
            y1 = copy(y)
            self.dgen1.mutex.unlock()
            self.p1curve.setData(self.x1,y1)


    def _acquire(self):
        """Defines metadata from current parameters.  Acquires image. Closes laser shutters"""
        meta = self._get_metadata()

        # Open laser shutters
        self._insight.main_shutter_button.click()
        self._insight.fixed_shutter_button.click()

        # Figure out how to add trigger for olympus

        # Acquire data from lockin
        self._zidaq.start_daq((512, 512), self._dwell, num_frames=3)

        while self._zidaq.acquiring:
            daq_data = self._zidaq.read_daq()
            if daq_data.any():
                self._daq_queue.put(daq_data)

        self._daq_queue.put('Done')

        # Image formation and data storage
        self._data.store(daq_data, meta)

        # Close shutters again
        self._insight.main_shutter_button.click()
        self._insight.fixed_shutter_button.click()


    def _tuned_spectrum(self):
        """Acquires a spectrum over calibrated wavelength range"""
        keys = self._calib_dict['stage'].keys()
        omegas = np.zeros([len(keys)])
        srs = np.zeros([len(keys)])
        for i, wl in enumerate(keys):
            print(wl)
            self._insight.tune_wl_val.value = str(wl)
            self._insight.tune_wl_button.click()
            time.sleep(3)
            self._calc_omega()
            self._omega_text.value = '%.2f' % (self._omega)

            move = self._calib_dict['stage'][str(wl)]
            self._delaystage.gotopos_text.value = str(move)
            self._delaystage.absmov_button.click()
            time.sleep(1)

            x, y, frame, line = self._zidaq.poll()
            omegas[i] = self._omega
            srs[i] = np.mean((x**2 + y**2)**0.5)

    def _get_metadata(self):
        """Todo: Return metadata dictionary based on current parameters"""
        meta = {}
        meta['olympus/objective'] = 'UPLSAPO60XWIR'
        meta['olympus/dwell'] = '2'
        meta['olympus/pixsize'] = '1'

        meta['insight/wavelength'] = '802'
        meta['insight/opo_power'] = '10'
        meta['insight/fixed_power'] = '10'
        meta['insight/error'] = 'false'

        meta['stage/position'] = '-44'
        meta['stage/error'] = 'false'

        meta['zidaq/frequency'] = '10280000'
        meta['zidaq/tc'] = '.00002'
        meta['zidaq/rate'] = '260000'
        return meta

    ############################################################################
    # Functions for optimizing signal vs delay stage position

    def _optimizer(self):
        """Start thread for optimize function from parent class using current delay stage position."""
        self._optimizerThread = threading.Thread(name='Signal Optimizer Thread', \
                            target=self._optimize, args=(self._delaystage.pos,))
        self._optimizerThread.daemon = True
        self._optimizerThread.start()