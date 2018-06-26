#! /usr/bin/env python

from .controllers.insightcontroller import *
from .controllers.stagecontroller import *
from .controllers.zidaqcontroller import *
from pyforms.controls import ControlDir, ControlEmptyWidget

class BasicExperiment(BaseWidget):
    def __init__(self):
        BaseWidget.__init__(self)
        self.set_margin(10)

        self._insight_panel = ControlEmptyWidget(margin=10)
        self._stage_panel = ControlEmptyWidget(margin=10, side='right')
        self._zidaq_panel = ControlEmptyWidget(margin=10)

        self.insight = InsightController('/dev/tty2', 0.1)
        self.insight.parent = self
        self._insight_panel.value = self.insight


        self.delaystage = StageController('/dev/tty2', 0.1)
        self.delaystage.parent = self
        self._stage_panel.value = self.delaystage

        self.zidaq = ziDAQController()
        self._zidaq_panel.parent = self
        self._zidaq_panel.value = self.zidaq

        self._organization()

    def _organization(self):
        self.formset = [{
            #('', 'h5:Insight','', 'h5:Delay Stage', '','h5:ZI Lock-in')
            'Laser and Delay Stage Controls': [('_insight_panel', '||', '_stage_panel')],
            'ZI Lock-in Controls': ['_zidaq_panel']
            #('_insight_panel', '', '_stage_panel', '', '_zidaq_panel')
        }]

#if __name__ == "__main__" : pyforms.start_app(BasicExperiment)