import numpy as np
import h5py

class Data(object):
    def __init__(self, logdir):
        self.datafile = h5py.File('%s/data.h5', 'w')
        self.data = h5py.create_group('images')
        self.metadata = h5py.create_group('metadata')
        self.logs = h5py.create_group('logs')

        self.count = 0

    def store(self, im, meta):
        self.data.create_dataset('%i' % (self.count), data=im)
        self.metadata.create_dataset('%i' % (self.count), data=meta)

        self.count += 1

    def close(self, logs):
        self.logs.create_dataset('insight', data=logs['insight'])
        self.logs.create_dataset('stage', data=logs['stage'])
        self.logs.create_dataset('zidaq', data=logs['zidaq'])

        self.datafile.close()