#! /usr/bin/env python

from experiments.basicexperiment import *
from experiments.calibrator import *
from experiments.controllers.gui.ControlCombo import *
from pyforms.controls import ControlDir, ControlDockWidget
import time

class DirError(Exception):
    """Exception for working directory error"""
    def __init__(self):
        self.msg = 'Enter a working directory error'

    def __str__(self):
        return self.msg

class ExpmtError(Exception):
    """Exception for positioner error"""
    def __init__(self):
        self.msg = 'Choose an experiment.'

    def __str__(self):
        return self.msg

class Selector(BaseWidget):
    def __init__(self):
        BaseWidget.__init__(self)
        self.set_margin(10)
        self._dir_sele = ControlDir()

        self._expmt_list = ControlCombo()
        self._expmt_list += ('', 0)
        self._expmt_list += ('Basic Controller', 1)
        self._expmt_list += ('Time Zero Calibration', 2)

        self._start_button = ControlButton('Start')

    @property
    def dir(self):
        return self._dir_sele.value

    @property
    def expmt(self):
        return self._expmt_list.value


class SRSMicroscope(BaseWidget):
    def __init__(self):
        BaseWidget.__init__(self, 'SRS Microscope')
        self.set_margin(10)

        self._open_panel = ControlDockWidget()
        self._selector = Selector()
        self._selector._start_button.value = self._new_experiment

        self._open_panel.value = self._selector

        self._expmt_panel = ControlEmptyWidget()
        self._expmt_panel.hide()

        self.mainmenu = [ { 'File' : [ { 'Save' : self.save } ] } ]

        self.calibfile = 'calibration/t0_calibration.yaml'

    def _new_experiment(self):
        tmp = ''
        with open('calibration/formset.yaml') as f:
            for line in f:
                tmp += line
            formset = yaml.load(tmp)
        try:
            if self._selector.dir == '':
                raise DirError
            if self._selector.expmt == 0:
                raise ExpmtError
            elif self._selector.expmt == 1:
                self.expmt = BasicExperiment(formset, self.calibfile, self._selector.dir)
                self.expmt.parent = self._expmt_panel
                self._expmt_panel.value = self.expmt
                self.value = self.expmt
                self._expmt_panel.show()
                self._open_panel.hide()
            elif self._selector.expmt == 2:
                self.expmt = Calibrator(formset, self.calibfile, self._selector.dir)
                self.expmt.parent = self._expmt_panel
                self._expmt_panel.value = self.expmt
                self.value = self.expmt
                self._expmt_panel.show()
                self._open_panel.hide()

        except DirError as e:
            print(e)
        except ExpmtError as e:
            print(e)

    def save(self):
        tmp = time.localtime()[0:3]
    #    date = '%i-%i-%i' % (tmp[0], tmp[1], tmp[2])
    #    with open('%s/%s_ExpmtLog' % (self._selector.dir, date), 'w') as f:
    #        f.write(self.expmt.expmt_history.value)

    def closeEvent(self, event):
        self.expmt.beforeClose()
        super(BaseWidget, self).closeEvent(event)

if __name__ == "__main__" : pyforms.start_app(SRSMicroscope)