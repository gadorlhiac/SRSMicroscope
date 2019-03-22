from .controllers.insightcontroller import *
from .controllers.stagecontroller import *
from .controllers.zidaqcontroller import *
from pyforms.controls import ControlButton, ControlEmptyWidget
from .experiment import *
from .util.data import *
import yaml
import time

class Experiment(BaseWidget):
    """
    Base class for SRS/multiphoton experiment. Includes basic equipment control.

    Args:
        formset (dict/list): dictionary/list for GUI organization.
        calibfile (str): path to yaml file for calibration, e.g., time 0.
        logdir (str): path for working directory
    """

    def __init__(self, formset, calibfile, logdir):
        BaseWidget.__init__(self)
        self.set_margin(10)

        self._logdir = logdir

        self._calibfile = 'calibration/t0_calibration.yaml'
        self._calib_dict = {}

        self._data = Data(self._logdir)

        self._insight_panel = ControlEmptyWidget(margin=10)
        self._stage_panel = ControlEmptyWidget(margin=10, side='right')
        self._zidaq_panel = ControlEmptyWidget(margin=10)
        self._expmt_panel = ControlEmptyWidget(margin=10)

        self._insight = InsightController('COM6', 0.07, formset['insight'])
        self._insight.parent = self
        self._insight_panel.value = self.insight

        self._delaystage = StageController('COM7', 0.05, formset['stage'])
        self._delaystage.parent = self
        self._stage_panel.value = self.delaystage

        self._zidaq = ziDAQController(formset['zidaq'])
        self._zidaq.parent = self
        self._zidaq_panel.value = self.zidaq

        # Organization and parameter initialization
        self._expmt_widgets()
        self._load_calibration(self.calibfile)

        self.formset = formset['expmt']

    ############################################################################
    # GUI Widgets

    def _expmt_widgets(self):
        """Experiment specific GUI objects.  Separate from device GUI objects"""
        self._expmt_history = ControlTextArea('Experiment Log')
        self._expmt_history.readonly = True

        self._expmt_panel.value = [self._expmt_history]

    ############################################################################
    # Logging and calibration

    def _update_history(self, msg):
        """Write to the experiment history log."""
        t = time.asctime(time.localtime())
        self._expmt_history += '%s: %s' % (t, msg)

    def _load_calibration(self, calibfile):
        """Load calibration file into memory."""
        try:
            with open(calibfile) as f:
                tmp = ''
                for line in f:
                    tmp += line
                self._calib_dict = yaml.load(tmp)
            msg = 'Calibration found'
            self._update_history(msg)

        except FileNotFoundError as e:
            msg = 'No calibration found'
            self._update_history(msg)

    ############################################################################
    # Functions for optimizing signal vs delay stage position

    def _optimize(self, pos):
        """
        Optimize the lockin signal as a function of delay stage position.
        Requires laser, delay stage, and zidaq to be on, and an acquirable signal.

        Args:
            pos (float): a stage position around which to optimize
        """
        pos_range = np.linspace(pos - .1, pos + .1, 200)
        self._delaystage.gotopos_text.value = str(pos_range[0])
        self._delaystage.absmov_button.click()

        r = np.zeros([len(pos_range)])
        for i, p in enumerate(pos_range):
            print(i)
            self._delaystage.gotopos_text.value = str(p)
            self._delaystage.absmov_button.click()
            time.sleep(.2)
            x, y, frame, line = self._zidaq.poll()
            r[i] = np.mean((x**2 + y**2)**0.5)

        wl = str(self._insight.opo_wl)
        max_pos = pos_range[np.argmax(r)]
        self._calib_dict['stage'][wl] = max_pos
        self._calib_dict['dsmpos'][wl] = self._insight.dsmpos

        calib = yaml.dump(self._calib_dict)
        with open(self._calibfile, 'w') as f:
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
        """Called on window close.  Writes logs to data file and text files."""
        # data object stores its own copies of log files
        logs = {}
        logs['zidaq'] = self._zidaq.action_history
        logs['stage'] = self._stage.action_history
        logs['insight'] = self._insight.action_history
        logs['insight'] += '\n\n ----Beginning Code History----\n\n'
        logs['insight'] +=  self._insight.code_history
        logs['expmt'] = self._expmt_history
        self.data.close(logs)

        # Write out text logs as well
        with open('%s/log_zidaq.txt' % (self._logdir), 'w') as f:
            f.write(logs['zidaq'])

        with open('%s/log_insight.txt' % (self._logdir), 'w') as f:
            f.write(logs['insight'])

        with open('%s/log_stage.txt' % (self._logdir), 'w') as f:
            f.write(logs['stage'])

        with open('%s/log_expmt.txt' % (self._logdir), 'w') as f:
            f.write(logs['expmt'])

    def closeEvent(self, event):
        self.beforeClose()
        super().closeEvent(event)