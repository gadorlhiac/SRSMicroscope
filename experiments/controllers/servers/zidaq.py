#! /usr/bin/env python

import numpy as np
import time
import zhinst.ziPython as ziPython
import json

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

            self.last_action = 'Lockin found, %s' % (msg)
        except Exception as e:
            self.last_action = str(e)

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

    def _load_settings(self):
        try:
            with open('files/lockin.json') as f:
                tmp = ''
                for line in f:
                    tmp += line
                settings = json.loads(tmp)
            msg = 'settings loaded'
        except FileNotFoundError as e:
            msg = 'using default settings'

            settings = [['/%s/demods/*/enable' % (self._name), 0],
                        ['/%s/demods/*/trigger' % (self._name), 0],
                        ['/%s/sigouts/*/enables/*' % (self._name), 0],
                        ['/%s/scopes/*/enable' % (self._name), 0]],

                        ['/%s/sigins/%d/ac' % (self._name, self._sigin), 1],
                        ['/%s/sigins/%d/imp5' % (self._name, self._sigin), 1],
                        ['/%s/sigins/%d/diff' % (self._name, self._sigin), 0],

                        ['/%s/demods/0/enable' % (self._name), 1],
                        ['/%s/demods/0/adcselect' % (self._name), self._sigin],
                        ['/%s/demods/0/order' % (self._name), 4],
                        ['/%s/demods/0/timeconstant' % (self._name), 1],
                        ['/%s/demods/0/rate' % (self._name), 2e5],
                        ['/%s/demods/0/oscselect' % (self._name), 0],
                        ['/%s/demods/0/harmonic' % (self._name), 1],
                        ['/%s/oscs/0/frequency' % (self._name), 10280000]]
        finally:
            return settings, msg

    def _get_config(self):
        try:
            self._tc = self.server.getInt('/%s/demods/0/timeconstant' % (self._name))
            self._rate = self.server.getInt('/%s/demods/0/rate' % (self._name))
            self._freq = self.server.getInt('/%s/oscs/0/frequency' % (self._name))
        except Exception as e:
            self.last_action = str(e)

    def poll(self, poll_length=0.05, timeout=500):
        flat_dictionary_key = True
        path = '/%s/demods/0/sample'

        self.server.subscribe(path)
        self.server.sync()

        data = self.server.poll()
        if path in data:
            x = np.array(data[path]['x'])
            y = np.array(data[path]['y'])

        return x, y
        #flat_dictionary_key = True
#data = daq.poll(0.1, 200, 1, flat_dictionary_key)
#if '/dev123/demods/0/sample' in data:
# access the demodulator data:
#x = data['/dev123/demods/0/sample']['x']
#y = data['/dev123/demods/0/sample']['y']

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
            self.last_action = str(e)

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

#self.server.subscribe('/%s/demods/0/sample' % (self._name))
#flat_dictionary_key = True
#data = daq.poll(0.1, 200, 1, flat_dictionary_key)
#if '/dev123/demods/0/sample' in data:
# access the demodulator data:
#x = data['/dev123/demods/0/sample']['x']
#y = data['/dev123/demods/0/sample']['y']


    #desired_t_shot = 10./frequency
    #scope_time = np.ceil(np.max([0, np.log2(clockbase*desired_t_shot/2048.)]))
    #if scope_time > 15:
    #    scope_time = 15
    #    warnings.warn("Can't not obtain scope durations of %.3f s, scope shot duration will be %.3f."
    #                  % (desired_t_shot, 2048.*2**scope_time/clockbase))
