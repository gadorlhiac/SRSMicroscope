#! /usr/bin/env python

from .controllers.insightcontroller import *
from .controllers.stagecontroller import *
from .controllers.zidaqcontroller import *
from pyforms.controls import ControlButton, ControlEmptyWidget

class BasicExperiment(BaseWidget):
    def __init__(self):
        BaseWidget.__init__(self)
        self.set_margin(10)

        # Variables defined only for the experiment and not laser etc
        self.omega = 1000 # Raman shift

        self._insight_panel = ControlEmptyWidget(margin=10)
        self._stage_panel = ControlEmptyWidget(margin=10, side='right')
        self._zidaq_panel = ControlEmptyWidget(margin=10)
        self._experiment_panel = ControlEmptyWidget(margin=10)

        self.insight = InsightController('COM6', 0.07)
        self.insight.parent = self
        self._insight_panel.value = self.insight

        self.delaystage = StageController('COM7', 0.03)
        self.delaystage.parent = self
        self._stage_panel.value = self.delaystage

        self.zidaq = ziDAQController()
        self.zidaq.parent = self
        self._zidaq_panel.value = self.zidaq

        # Organization and parameter initialization
        self._calc_omega()
        self._organization()
        #self._experiment_organization()
        self._experiment_controls()

    def _experiment_controls(self):
        self._wl_label = ControlLabel('Main Wavelength: %s' \
                                                % (str(self.insight.opo_wl)))
        self._omega_text = ControlText('Raman Shift (cm-1):')
        self._omega_text.value = '%.2f' % (self.omega)
        self._set_omega_button = ControlButton('Set Omega')
        self._set_omega_button.value = self._set_omega

        self._experiment_panel.value = [
            self._wl_label,
            self._omega_text, self._set_omega_button]

    def _calc_omega(self):
        self.omega = (10000000./self.insight.opo_wl) - (10000000./1040.)

    def _set_omega(self):
        try:
            wl = self._calc_wl(float(self._omega_text.value))
            self.insight.tune_wl_val.value = str(wl)
            self.insight.tune_wl_button.click()
            self._calc_omega()
            self._omega_text.value = '%.2f' % (self.omega)
            self._wl_label.value = 'Main Wavelength: %s' \
                                                % (str(self.insight.opo_wl))
        except Exception as e:
            pass

    def _calc_wl(self, omega):
        wl = ((10000000.)*1040.)/((1040.*omega)+10000000.)
        return int(round(wl))

    def _experiment_organization(self):
        self._experiment_panel.formset = [
                ('','_test_button','')
        ]

    def _organization(self):
        self.formset = [{
            'Experiment Control: SRS (fs)': ['_experiment_panel'],
            'Laser and Delay Stage Controls': [('_insight_panel', '||', '_stage_panel')],
            'ZI Lock-in Controls': ['_zidaq_panel'],
        }]

#if __name__ == "__main__" : pyforms.start_app(BasicExperiment)