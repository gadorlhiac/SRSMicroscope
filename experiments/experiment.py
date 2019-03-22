from .controllers.insightcontroller import *
from .controllers.stagecontroller import *
from .controllers.zidaqcontroller import *
from pyforms.controls import ControlButton, ControlEmptyWidget
from .experiment import *
import yaml
import time

class Experiment(BaseWidget):
    def __init__(self, formset, calibfile, logdir):
        BaseWidget.__init__(self)
        self.set_margin(10)

        self.logdir = logdir

        self.calibfile = 'calibration/t0_calibration.yaml'
        self.calib_dict = {}

        self._insight_panel = ControlEmptyWidget(margin=10)
        self._stage_panel = ControlEmptyWidget(margin=10, side='right')
        self._zidaq_panel = ControlEmptyWidget(margin=10)
        self._expmt_panel = ControlEmptyWidget(margin=10)

        self.insight = InsightController('COM6', 0.07, formset['insight'])
        self.insight.parent = self
        self._insight_panel.value = self.insight

        self.delaystage = StageController('COM7', 0.05, formset['stage'])
        self.delaystage.parent = self
        self._stage_panel.value = self.delaystage

        self.zidaq = ziDAQController(formset['zidaq'])
        self.zidaq.parent = self
        self._zidaq_panel.value = self.zidaq

        # Organization and parameter initialization
        self._expmt_widgets()
        self._load_calibration(self.calibfile)

        self.formset = formset['expmt']

    ############################################################################
    # GUI Widgets

    def _expmt_widgets(self):
        self.expmt_history = ControlTextArea('Experiment Log')
        self.expmt_history.readonly = True

        self._expmt_panel.value = [self.expmt_history]

    ############################################################################
    # Logging and calibration

    def _update_history(self, msg):
        t = time.asctime(time.localtime())
        self.expmt_history += '%s: %s' % (t, msg)

    def _load_calibration(self, calibfile):
        try:
            with open(calibfile) as f:
                tmp = ''
                for line in f:
                    tmp += line
                self.calib_dict = yaml.load(tmp)
            msg = 'Calibration found'
            self._update_history(msg)

        except FileNotFoundError as e:
            msg = 'No calibration found'
            self._update_history(msg)

    ############################################################################
    # Functions for optimizing signal vs delay stage position

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
        self.calib_dict['stage'][wl] = max_pos
        self.calib_dict['dsmpos'][wl] = self.insight.dsmpos

        calib = yaml.dump(self.calib_dict)
        with open(self.calibfile, 'w') as f:
            f.write(calib)

        msg = 'Max signal for %s nm at %f.  Calibration updated.' % (wl, max_pos)

        self._update_history(msg)

        plt.plot(pos_range, r*1e6, 'o')
        plt.xlabel('Delay stage position (mm)')
        plt.ylabel(r'Demodulated voltage ($\mu$V)')
        plt.title('Signal vs Delay at %s' % (wl))
        plt.savefig('calibration/%s.svg' % (wl))
        plt.cla()
        plt.clf()

    ############################################################################
    # Save logs on close

    def beforeClose(self):
        with open('%s/log_zidaq.txt' % (self.logdir), 'w') as f:
            log = self.zidaq.action_history
            f.write(log)

        with open('%s/log_insight.txt' % (self.logdir), 'w') as f:
            log = self.insight.action_history
            log += '\n\n ----Beginning Code History----\n\n'
            log += self.insight.code_history
            f.write(log)

        with open('%s/log_stage.txt' % (self.logdir), 'w') as f:
            log = self.stage.action_history
            f.write(log)

        with open('%s/log_expmt.txt' % (self.logdir), 'w') as f:
            log = self.stage.expmt_history
            f.write(log)

    def closeEvent(self, event):
        self.beforeClose()
        super().closeEvent(event)