#! /usr/bin/env python

import numpy as np
import time
import zhinst.ziPython as ziPython
import yaml

class APIError(Exception):
    def __init__(self, error):
        self.msg = error

    def __str__(self):
        return self.msg

class ziDAQ(object):
    """
    Facilitates control of the ZI HFL2I lockin amplifier.  Uses the server API.
    """
    def __init__(self):
        self._name = ''
        self._scope = []

        self._sigin = 0
        self._sigout = 0
        self._scope_time = 1

        self._tc = 0
        self._freq = 0
        self._rate = 0

        try:
            port, apilevel = self._discover()
            self.server = ziPython.ziDAQServer('localhost', port, apilevel)
            self.server.connect()

            settings, msg = self._load_settings()
            self.server.set(settings)
            self.server.sync()

            self._get_config()

            self.last_action = 'Lockin found, %s' % (msg)
        except Exception as e:
            self.last_action = str(e)

    ############################################################################
    # Lockin device discovery functions and settings initiliazation.

    def _discover(self):
        """Run API discovery routines, and return port and apilevel to allow connection"""
        try:
            disc = ziPython.ziDiscovery()
            device = disc.findAll()[0]
            dev_info = disc.get(device)
            port = dev_info['serverport']
            apilevel = dev_info['apilevel']
            self._name = dev_info['deviceid'].lower()
            self.last_action = 'Lock-in found'
            return port, apilevel

        except Exception as e:
            self.last_action = 'Lock-in not found. %s' % (str(e))
            return 8005, 1

    def _load_settings(self):
        """
        Try to load settings for oscillator/demodulator/server.
        Default settings hard coded if not found.
        """
        try:
            with open('calibration/lockin.yaml') as f:
                tmp = ''
                for line in f:
                    tmp += line
                settings = yaml.load(tmp)
            msg = 'settings loaded'
        except FileNotFoundError as e:
            msg = 'using default settings'

            settings = [['/%s/demods/*/enable' % (self._name), 0],
                        ['/%s/demods/*/trigger' % (self._name), 0],
                        ['/%s/sigouts/*/enables/*' % (self._name), 0],
                        ['/%s/scopes/*/enable' % (self._name), 0],

                        ['/%s/sigins/%d/ac' % (self._name, self._sigin), 1],
                        ['/%s/sigins/%d/imp50' % (self._name, self._sigin), 1],
                        ['/%s/sigins/%d/diff' % (self._name, self._sigin), 0],

                        ['/%s/demods/0/enable' % (self._name), 1],
                        ['/%s/demods/0/adcselect' % (self._name), self._sigin],
                        ['/%s/demods/0/order' % (self._name), 4],
                        ['/%s/demods/0/timeconstant' % (self._name), 2e-5],
                        ['/%s/demods/0/rate' % (self._name), 2e5],
                        ['/%s/demods/0/oscselect' % (self._name), 0],
                        ['/%s/demods/0/harmonic' % (self._name), 1],
                        ['/%s/oscs/0/freq' % (self._name), 10280000]]
        finally:
            return settings, msg

    def _get_config(self):
        """
        Get the current lockin oscillator frequency, demodulator time constant
        and sampling rate of the demodulated signal.
        """
        try:
            self._tc = self.server.getDouble('/%s/demods/0/timeconstant' % (self._name))
            self._rate = self.server.getDouble('/%s/demods/0/rate' % (self._name))
            self._freq = self.server.getDouble('/%s/oscs/0/freq' % (self._name))
        except Exception as e:
            self.last_action = str(e)

    ############################################################################
    # Polling functions for data retrieval.

    def _poll(self, poll_length=0.05, timeout=500, tc=1e-3):
        """
        Poll the demodulator and record the data.

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
        flat_dictionary_key = True
        path = '/%s/demods/0' % (self._name)

        self.server.setDouble('%s/timeconstant' % (path), tc)
        self.server.sync()

        self.server.subscribe(path)
        self.server.sync()

        try:
            data = self.server.poll(poll_length, timeout, 1, flat_dictionary_key)
            if '%s/sample' % (path) in data:
                x = np.array(data['%s/sample' % (path)]['x'])
                y = np.array(data['%s/sample' % (path)]['y'])
                frame = np.array(data['%s/sample' % (path)]['auxin0'])
                line = np.array(data['%s/sample' % (path)]['auxin1'])

            self.last_action = 'Polled for %f s and time constant %f s' \
                                                            % (poll_length, tc)
        except Exception as e:
            self.last_action = 'While polling, encountered error: %s' % (str(e))

        self.server.setDouble('%s/timeconstant' % (path), self._tc)
        self.server.sync()

        return x, y, frame, line

    def _poll_scope(self, channel):
        """Poll the oscilloscope.  Not currently in use."""
        try:
            path = '/%s/scopes/0/wave' % (self._name)
            self.server.subscribe(path)
            self.server.sync()
            poll_length = .05  # [s]
            poll_timeout = 500  # [ms]
            poll_flags = 0
            poll_return_flat_dict = True
            data = self.server.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
            self._scope = data['/%s/scopes/%i/wave' % (self._name, channel)][0]['wave']
        except Exception as e:
            self.last_action = str(e)

    ############################################################################
    # API errors

    def _check_api_errors(self):
        """Check if any API errors were found"""
        try:
            e = self.server.getLastError()
            if e != '':
                raise APIError(self._api_error)

        except APIError as e:
            self._api_error = str(msg)
            self.last_action = str(msg)

    ############################################################################
    # Property and setter functions for lockin time constant, modulation
    # frequency and sampling rate

    # Lockin time constant
    @property
    def tc(self):
        """Property to return current demodulator time constant."""
        return self._tc

    @tc.setter
    def tc(self, val):
        """
        Time constant setter.

        Args:
            val (float): demodulator time constant. Units (s)
        """
        self.server.setDouble('/%s/demods/0/timeconstant' % (self._name), val)
        self.server.sync()

        self._tc = self.server.getDouble('/%s/demods/0/timeconstant' % (self._name))
        self.last_action = 'Lockin time constant set to %i' % (self._tc)

    # Lockin oscillator frequency
    @property
    def freq(self):
        """Property to return current oscillator frequency."""
        return self._freq

    @freq.setter
    def freq(self, val):
        """
        Oscillator frequency setter.

        Args:
            val (float): oscillator frequency. Units (Hz)
        """
        self.server.setDouble('/%s/oscs/0/freq' % (self._name), val)
        self.server.sync()

        self._freq = self.server.getDouble('/%s/oscs/0/freq' % (self._name))
        self.last_action = 'Oscillator frequency set to %i' % (self._freq)

    # Lockin sampling rate
    @property
    def rate(self):
        """Property to return current sampling rate of demodulated signal."""
        return self._rate

    @rate.setter
    def rate(self, val):
        """
        Sampling rate setter.

        Args:
            val (float): sampling rate of demodulated signal. Units (Sa/s)
        """
        self.server.setDouble('/%s/demods/0/rate' % (self._name), val)
        self.server.sync()

        self._rate = self.server.getDouble('/%s/demods/0/rate' % (self._name))
        self.last_action = 'Lockin sampling rate set to %i' % (self._rate)

    ############################################################################
    # Property and setter functions for signal input/outputs

    @property
    def sigin(self):
        """Return current signal input channel.  Not in use."""
        return self._sigin

    @sigin.setter
    def sigin(self, val):
        """Set current signal input channel. Not in use."""
        self._sigin = val
        self.last_action = 'Signal input changed to channel %d.' % (val+1)

    @property
    def sigout(self):
        """Return current signal output channel.  Not in use."""
        return self._sigout

    @sigout.setter
    def sigout(self, val):
        """Set current signal output channel. Not in use."""
        self._sigout = val
        self.last_action = 'Signal output changed to channel %d.' % (val+1)

    ############################################################################
    # Oscilloscope properties

    @property
    def scope(self):
        """Return the oscilloscope trace."""
        return self._scope

    @property
    def scope_time(self):
        return self._scope_time

    @scope_time.setter
    def scope_time(self, val):
        try:
            if val > 15:
                scope_time = 15
            else:
                scope_time = val
            clockbase = float(self.server.getInt('/%s/clockbase' % (self._name)))
            self.server.set(['/%s/scopes/0/time' % (device), scope_time])
            self.last_action = 'Oscilloscope time set to %i' % (val)
            #desired_t_shot = 10./frequency
            #scope_time = np.ceil(np.max([0, np.log2(clockbase*desired_t_shot/2048.)]))
        except:
            self.last_action = ''

#self.server.subscribe('/%s/demods/0/sample' % (self._name))
#flat_dictionary_key = True
#data = daq.poll(0.1, 200, 1, flat_dictionary_key)
#if '/dev123/demods/0/sample' in data:
# access the demodulator data:
#x = data['/dev123/demods/0/sample']['x']
#y = data['/dev123/demods/0/sample']['y']
#frame = data['/dev123/demods/0/sample']['auxin0']
#line = data['/dev123/demods/0/sample']['auxin1']
#dataloss = '/dev123/status/demodsampleloss'
#clipping = '/dev123/status/adcclip/0'


    #desired_t_shot = 10./frequency
    #scope_time = np.ceil(np.max([0, np.log2(clockbase*desired_t_shot/2048.)]))
    #if scope_time > 15:
    #    scope_time = 15
    #    warnings.warn("Can't not obtain scope durations of %.3f s, scope shot duration will be %.3f."
    #                  % (desired_t_shot, 2048.*2**scope_time/clockbase))
