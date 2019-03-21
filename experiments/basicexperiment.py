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

class BasicExperiment(BaseWidget):
    def __init__(self):
        BaseWidget.__init__(self)
        self.set_margin(10)

        # Variables defined only for the experiment and not laser etc
        self.omega = 1000 # Raman shift
        self.t0_dict = {} # Dictionary of time zero overlaps, saved to json

        self._insight_panel = ControlEmptyWidget(margin=10)
        self._stage_panel = ControlEmptyWidget(margin=10, side='right')
        self._zidaq_panel = ControlEmptyWidget(margin=10)
        self._expmt_panel = ControlEmptyWidget(margin=10)

        self.insight = InsightController('COM6', 0.07)
        self.insight.parent = self
        self._insight_panel.value = self.insight

        self.delaystage = StageController('COM7', 0.03)
        self.delaystage.parent = self
        self._stage_panel.value = self.delaystage

        self.zidaq = ziDAQController()
        self.zidaq.parent = self
        self._zidaq_panel.value = self.zidaq

        self.expmt_history = ControlTextArea('Experiment Log')
        self.expmt_history.readonly = True

        # Organization and parameter initialization
        self._calc_omega()
        self._load_calibration()

        self._expmt_controls()
        self._organization()

    def _expmt_controls(self):
        self._wl_label = ControlLabel('Main Wavelength: %s' \
                                                % (str(self.insight.opo_wl)))
        self._omega_text = ControlText('Raman Shift (cm-1):')
        self._omega_text.value = '%.2f' % (self.omega)
        self._set_omega_button = ControlButton('Set Omega')
        self._set_omega_button.value = self._set_omega

        self._optimize_button = ControlButton('Optimize Signal')
        self._optimize_button.value = self._optimizer

        self._tuned_spectrum_button = ControlButton('Tuned Spectrum')
        self._tuned_spectrum_button.value = self._tune_spectrum

        self._expmt_panel.value = [ self._wl_label,
                                    self._omega_text, self._set_omega_button,
                                    self._optimize_button,
                                    self._tuned_spectrum_button,
                                    self.expmt_history]

    #    self.mainmenu = [
    #    { 'File': [
    #            {'Save as': self.save_window, 'icon': 'path-to-image.png'},
    #            {'Open as': self.load_window, 'icon': QtGui.QIcon('path-to-image.png')},
    #            '-',
    #            {'Exit': self.__exit},
    #        ]
    #    }
    #]

    def _tune_spectrum(self):
        keys = self.t0_dict.keys()
        omegas = np.zeros([len(keys)])
        srs = np.zeros([len(keys)])
        for i, wl in enumerate(keys):
            print(wl)
            self.insight.tune_wl_val.value = str(wl)
            self.insight.tune_wl_button.click()
            time.sleep(3)
            self._calc_omega()
            self._omega_text.value = '%.2f' % (self.omega)

            move = self.t0_dict[str(wl)]
            self.delaystage.gotopos_text.value = str(move)
            self.delaystage.absmov_button.click()
            time.sleep(1)

            x, y = self.zidaq.poll()
            omegas[i] = self.omega
            srs[i] = np.mean((x**2 + y**2)**0.5)

        plt.plot(omegas, srs*1e6, 'o')
        plt.xlabel(r'Wavenumber (cm$^{-1}$)')
        plt.ylabel(r'Demodulated voltage ($\mu$V)')
        plt.title('PDMS SRS Spectrum')
        plt.savefig('calibration/spectrum_test.svg')

    def _update_history(self, msg):
        t = time.asctime(time.localtime())
        self.expmt_history += '%s: %s' % (t, msg)

    def _calc_omega(self):
        self.omega = (10000000./self.insight.opo_wl) - (10000000./1040.)

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
            self._wl_label.value = 'Main Wavelength: %s' \
                                                % (str(self.insight.opo_wl))

            # Tune delay appropriately
            move = self.t0_dict[wl]
            self.delaystage.gotopos_text.value = str(move)
            self.delaystage.absmov_button.click()
        except KeyError as e:
            msg = 'No delay stage calibration for %i nm' % (wl)
            alert = AlertWindow('Alert', msg)
            self._update_history(msg)
        except Exception as e:
            msg = str(e)
            alert = AlertWindow('Alert', msg)
            self._update_history(msg)

    def _calc_wl(self, omega):
        wl = ((10000000.)*1040.)/((1040.*omega)+10000000.)
        return int(round(wl))

    def _load_calibration(self):
        try:
            with open('calibration/t0_calibration.json') as f:
                tmp = ''
                for line in f:
                    tmp += line
                self.t0_dict = json.loads(tmp)
        except FileNotFoundError as e:
            msg = 'No time zero calibration found'
            alert = AlertWindow('Alert', msg)
            self._update_history(msg)

    ############################################################################
    # Functions for optimizing signal vs delay stage position

    def _optimizer(self):
        self._optimizerThread = threading.Thread(target=self._optimize)
        self._optimizerThread.start()

    def _optimize(self, plot=True):
        # Optimize lockin signal as a function of delay for the current wl
        pos = self.delaystage.pos
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

        wl = int(self.insight.opo_wl)
        max_pos = pos_range[np.argmax(r)]
        self.t0_dict[wl] = max_pos

        self.delaystage.gotopos_text.value = str(max_pos)
        self.delaystage.absmov_button.click()

        calib = json.dumps(self.t0_dict)

        with open('calibration/t0_calibration.json', 'w') as f:
            f.write(calib)

        msg = 'Signal maximum for %d nm found at %f.  Calibration updated.' \
                                                                % (wl, max_pos)

        self._update_history(msg)
        if plot:
            plt.plot(pos_range, r*1e6, 'o')
            plt.xlabel('Delay stage position (mm)')
            plt.ylabel(r'Demodulated voltage ($\mu$V)')
            plt.title('Signal vs Delay at %i nm' % (wl))
            plt.savefig('calibration/%i.svg' % (wl))
            plt.show()

    def _calibrate(self):
        # Add warning that calibration requires a standard sample
        # Need to decide what that is? KDP SFG with some filters on lockin?
        # Otherwise can use optimize function to maximize signal for 1 wl
        # This function will call optimize for multiple wavelengths
        # dict = json.dumps(dict)
        pass

    def _organization(self):
        self.formset = [{
            'Experiment Control: SRS (fs)': ['_expmt_panel'],
            'Laser and Delay Stage Controls': [('_insight_panel', '||', '_stage_panel')],
            'ZI Lock-in Controls': ['_zidaq_panel'],
        }]

#if __name__ == "__main__" : pyforms.start_app(BasicExperiment)