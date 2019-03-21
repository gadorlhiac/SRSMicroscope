class Experiment(BaseWidget):
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
        self.expmt_history = ControlTextArea('Experiment Log')
        self.expmt_history.readonly = True

        self._expmt_panel.value = [self.expmt_history]

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


    def _organization(self):
        self.formset = [{
            'Experiment': ['_expmt_panel'],
            'Laser and Delay Stage Controls': [('_insight_panel', '||', '_stage_panel')],
            'ZI Lock-in Controls': ['_zidaq_panel'],
        }]