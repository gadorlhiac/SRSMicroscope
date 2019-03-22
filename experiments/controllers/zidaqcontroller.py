#! /usr/bin/env python

import pyforms
import time
import threading
import matplotlib.pyplot as plt
import numpy as np
from .servers.zidaq import *
from .gui.ControlMatplotlib import *
from .gui.ControlCombo import *
from .controller import *
from pyforms import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlLabel
from pyforms.controls import ControlTextArea

class ziDAQController(ziDAQ, Controller):
    """
    Extended zidaq controller.  Inherits from controller and zidaq server for
    integration of gui elements and ziDAQ server lockin.

    Args:
        formset (dict/list): dictionary/list for GUI organization.
    """
    def __init__(self, formset):
        ziDAQ.__init__(self)
        Controller.__init__(self, formset, 'ZI HF2LI')
        self.set_margin(10)

        # Signal in/out selectors
        #self._sigin_sele = ControlCombo()
        #self._sigin_sele += ('Siginal Input 1', 0)
        #self._sigin_sele += ('Siginal Input 2', 1)

        #self._sigout_sele = ControlCombo()
        #self._sigout_sele += ('Siginal Output 1', 0)
        #self._sigout_sele += ('Siginal Output 2', 1)

        # Oscilloscope trace
        #self._scope_viewer = ControlMatplotlib(default=self.scope)

        #self.scopeThread = threading.Thread(target=self._plot_scope, args=[0])
        #self.scopeThread.start()

    ############################################################################
    # GUI Widgets

    def _widgets(self):
        """ziDAQ GUI items for demodulation parameters"""
        # Action and error log from parent Controller class
        Controller._widgets(self)

        # Lockin time constant
        self.tc_text = ControlText('Time Constant (s):')
        self.tc_text.value = str(self.tc)
        self.set_tc_button = ControlButton('Set')
        self.set_tc_button.value = self._set_tc

        # Oscillator frequency
        self.freq_text = ControlText('Oscillator Frequency (Hz):')
        self.freq_text.value = str(self.freq)
        self.set_freq_button = ControlButton('Set')
        self.set_freq_button.value = self._set_freq

        # Sampling rate from demodulated signal
        self.rate_text = ControlText('Sampling Rate (Hz):')
        self.rate_text.value = str(self.rate)
        self.set_rate_button = ControlButton('Set')
        self.set_rate_button.value = self._set_rate


    ############################################################################
    # TC, frequency and sampling rate setters

    def _set_tc(self):
        """Set the lockin demodulator time constant"""
        try:
            self.tc = float(self.tc_text.value.strip())
            self.tc_text.value = str(self.tc)
        except Exception as e:
            self.last_action = 'Error changing time constant: %s' % (str(e))
        finally:
            self._update_history()

    def _set_freq(self):
        """Set the lockin oscillator frequency"""
        try:
            self.freq = float(self.freq_text.value.strip())
            self.freq_text.value = str(self.freq)
        except Exception as e:
            self.last_action = 'Error changing oscillator frequency: %s' % (str(e))
        finally:
            self._update_history()

    def _set_rate(self):
        """Set the sampling rate of the demodulated signal"""
        try:
            self.rate = float(self.rate_text.value.strip())
            self.rate_text.value = str(self.rate)
        except Exception as e:
            self.last_action = 'Error changing sampling rate: %s' % (str(e))
        finally:
            self._update_history()

    ############################################################################
    # Polling functions

    def poll(self, poll_length=0.05, timeout=500, tc=1e-3):
        """
        Poll the demodulator for a set time.

        Args:
            poll_length (float): how long to poll. Units: (s)
            timeout (int): timeout period for response from server. Units (ms)
            tc (float): demodulator time constant with which to poll. Units (s)

        Returns:
            x (np array): demodulator x values over polling period.
            y (np array): demodulator y values over polling period.
            frame (np array): auxilary in 0 values.  Currently configured to olympus frame clock.
            line (np array): auxilary in 1 values. Currently configured to olympus line clock.
        """
        x, y, frame, line = self._poll(poll_length, timeout, tc)
        self._update_history()
        return x, y, frame, line

    def _plot_scope(self, channel):
        """Plot the oscilloscope trace of input.  Not in use."""
        while 1:
            time.sleep(0.05)
            self._poll_scope(channel)
            self._scope_viewer.value = self.scope

    ############################################################################
    # Overload Controller parent _status function

    #def _status(self):
        #while 1:
            #time.sleep(0.05)
            #si = self._sigin_sele.value
            #so = self._sigout_sele.value
            #if si != self.sigin:
            #    self.sigin = si
            #    self._update_history()
            #if so != self.sigout:
            #    self.sigout = so
            #    self._update_history