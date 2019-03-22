import numpy as np
import h5py

class Data(object):
    """
    Data object for handling io of data, metadata and logs.

    Args:
        logdir (str): Path to working directory

    Attributes:
        datafile (h5py.File): Opened hdf5 file for data storage
        count (int): Counter for dataset storage/naming
    """
    def __init__(self, logdir):
        self.datafile = h5py.File('%s/data.h5' % (logdir), 'w')
        self.data = h5py.create_group('data')

        self.logs = h5py.create_group('logs')
        self.count = 0

    def store_im(self, im, meta):
        """Stores data, increments count"""
        dataset = self.data.create_dataset('%i' % (self.count), data=im)
        dataset.attrs.update(meta)
        self.count += 1

    def close(self, logs):
        """To be called before exit.  Stores logs, and closes file."""
        self.logs.create_dataset('insight', data=logs['insight'])
        self.logs.create_dataset('stage', data=logs['stage'])
        self.logs.create_dataset('zidaq', data=logs['zidaq'])

        self.datafile.close()