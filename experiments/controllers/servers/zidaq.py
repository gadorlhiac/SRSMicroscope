#! /usr/bin/env python

import numpy as np
import time
import zhinst.ziPython as ziPython

class APIError(Exception):
    def __init__(self, error):
        self.msg = error

    def __str__(self):
        return self.msg

class ziDAQ(object):
    def __init__(self):
        self._name = ''
        self._scope = []
        self._sigin = 0
        self._sigout = 0
        self._scope_time = 1

        port, apilevel = self._discover()
        try:
            self.server = ziPython.ziDAQServer('localhost', port, apilevel)
            self.server.connect()

            scope_time = 1
            scope_settings = [['/%s/scopes/%d/channel' % (self._name, self._sigin), 0],
                              ['/%s/scopes/%d/trigchannel' % (self._name, self._sigin), 2],
                              ['/%s/scopes/%d/triglevel' % (self._name, self._sigin), 0.0],
                              ['/%s/scopes/%d/trigholdoff' % (self._name, self._sigin), 0.1],
                      # Enable bandwidth limiting: avoid antialiasing effects due to
                      # sub-sampling when the scope sample rate is less than the input
                      # channel's sample rate.
                              ['/%s/scopes/%d/bwlimit' % (self._name, self._sigin), 1],
                      # Set the sampling rate.
                              ['/%s/scopes/%d/time' % (self._name, self._sigin), self._scope_time],
                      # Enable the scope
                              ['/%s/scopes/%d/enable' % (self._name, self._sigin), 1]]
            self.server.set(scope_settings)
            self.server.sync()
        except RuntimeError as e:
            self.last_action = e

    def _set(self, settings):
        self.server.set(scope_settings)
        self.server.sync()

    def _poll_scope(self, channel):
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
            self.last_action = e

    def _discover(self):
        try:
            disc = ziPython.ziDiscovery()
            device = disc.findAll()[0]
            dev_info = disc.get(device)
            port = dev_info['serverport']
            apilevel = dev_info['apilevel']
            self._name = dev_info['deviceid']
            self.last_action = 'Lock-in found'
            return port, apilevel

        except Exception as e:
            self.last_action = 'Lock-in not found'
            return 8005, 1

    def _check_api_errors(self):
        try:
            e = self.server.getLastError()
            if e != '':
                raise APIError(self._api_error)

        except APIError as e:
            self._api_error = e.msg
            self.last_action = e.msg

    @property
    def scope(self):
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


    #desired_t_shot = 10./frequency
    #scope_time = np.ceil(np.max([0, np.log2(clockbase*desired_t_shot/2048.)]))
    #if scope_time > 15:
    #    scope_time = 15
    #    warnings.warn("Can't not obtain scope durations of %.3f s, scope shot duration will be %.3f."
    #                  % (desired_t_shot, 2048.*2**scope_time/clockbase))

    @property
    def sigin(self):
        return self._sigin

    @sigin.setter
    def sigin(self, val):
        self._sigin = val
        self.last_action = 'Signal input changed to channel %d.' % (val+1)

    @property
    def sigout(self):
        return self._sigout

    @sigout.setter
    def sigout(self, val):
        self._sigout = val
        self.last_action = 'Signal output changed to channel %d.' % (val+1)