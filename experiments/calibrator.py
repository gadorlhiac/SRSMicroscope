#! /usr/bin/env python

from .controllers.insightcontroller import *
from .controllers.stagecontroller import *
from .controllers.zidaqcontroller import *
from .controllers.gui.alertwindow import *
from pyforms.controls import ControlButton, ControlEmptyWidget
import json
import time

# Todo: add a calibration routine which finds t0 vs wavelength and saves the
# output to a json which will be searched for.  If not present, can opt to
# maximize signal at the wavelength chosen or user manually steps using the
# delay stage themselves

class Calibrator(BaseWidget):
    def __init__(self):
        BaseWidget.__init__(self)
        self.set_margin(10)

        # Variables defined only for the experiment and not laser etc
        self.omega = 1000 # Raman shift

        # Dictionary of time zero overlaps, saved to json
        self.t0_dict = {'stage': {}, 'dsmpos': {}}

        self._insight_panel = ControlEmptyWidget(margin=10)
        self._stage_panel = ControlEmptyWidget(margin=10, side='right')
        self._zidaq_panel = ControlEmptyWidget(margin=10)
        self._expmt_panel = ControlEmptyWidget(margin=10)

        self.insight = InsightController('COM6', 0.07)
        self.insight.parent = self
        self._insight_panel.value = self.insight

        self.delaystage = StageController('COM7', 0.05)
        self.delaystage.parent = self
        self._stage_panel.value = self.delaystage

        self.zidaq = ziDAQController()
        self.zidaq.parent = self
        self._zidaq_panel.value = self.zidaq

        # Organization and parameter initialization
        self._expmt_controls()
        self._load_calibration()

        self._organization()

    def _expmt_controls(self):
        self._wl_range_text = ControlText('Wavelength Range to Calibrate:')

        self.expmt_history = ControlTextArea('Experiment Log')
        self.expmt_history.readonly = True

        self._calibrate_button = ControlButton('Calibrate')
        self._calibrate_button.value = self._calibrator

        self._expmt_panel.value = [ self._wl_range_text,
                                    self._calibrate_button,
                                    self.expmt_history]

    def _update_history(self, msg):
        t = time.asctime(time.localtime())
        self.expmt_history += '%s: %s' % (t, msg)

    def _load_calibration(self):
        try:
            with open('calibration/t0_calibration.json') as f:
                tmp = ''
                for line in f:
                    tmp += line
                self.t0_dict = json.loads(tmp)
            msg = 'Calibration found for:\n'
            for key in self.t0_dict['stage'].keys():
                msg += '\t%s nm\n' % (key)
            self._update_history(msg)

        except FileNotFoundError as e:
            msg = 'No time zero calibration found'
            alert = AlertWindow('Alert', msg)
            self._update_history(msg)

    ############################################################################
    # Functions for optimizing signal vs delay stage position

    def _calibrator(self):
        self._calibratorThread = threading.Thread(target=self._calibrate)
        self._calibratorThread.start()

    def _optimize(self, pos):
        # Optimize lockin signal as a function of delay for the current wl
        pos_range = np.linspace(pos - .1, pos + .1, 200)
        self.delaystage.gotopos_text.value = str(pos_range[0])
        self.delaystage.absmov_button.click()

        r = np.zeros([len(pos_range)])
        for i, p in enumerate(pos_range):
            print(i)
            self.delaystage.gotopos_text.value = str(p)
            self.delaystage.absmov_button.click()
            time.sleep(.2)
            x, y = self.zidaq.poll()
            r[i] = np.mean((x**2 + y**2)**0.5)

        wl = str(self.insight.opo_wl)
        max_pos = pos_range[np.argmax(r)]
        self.t0_dict['stage'][wl] = max_pos
        self.t0_dict['dsmpos'][wl] = self.insight.dsmpos

        calib = json.dumps(self.t0_dict)
        with open('calibration/t0_calibration.json', 'w') as f:
            f.write(calib)

        msg = 'Signal maximum for %s nm found at %f.  Calibration updated.' \
                                                                % (wl, max_pos)

        self._update_history(msg)

        plt.plot(pos_range, r*1e6, 'o')
        plt.xlabel('Delay stage position (mm)')
        plt.ylabel(r'Demodulated voltage ($\mu$V)')
        plt.title('Signal vs Delay at %s' % (wl))
        plt.savefig('calibration/%s.svg' % (wl))
        plt.cla()
        plt.clf()

    def _get_wavelength_range(self):
        text = self._wl_range_text.value
        wlrange = text.split('-')
        wlmin = int(wlrange[0])
        wlmax = int(wlrange[1])
        return np.linspace(wlmin, wlmax, wlmin-wlmax+1)

    def _calibrate(self):
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

    def _organization(self):
        self.formset = [{
            'Calibration': ['_expmt_panel'],
            'Laser and Delay Stage Controls': [('_insight_panel', '||', '_stage_panel')],
            'ZI Lock-in Controls': ['_zidaq_panel'],
        }]