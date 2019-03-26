#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__      = "Ricardo Ribeiro"
__credits__     = ["Ricardo Ribeiro"]
__license__     = "MIT"
__version__     = "0.0"
__maintainer__  = "Ricardo Ribeiro"
__email__       = "ricardojvr@gmail.com"
__status__      = "Development"

import numpy as np
from pyforms.utils.settings_manager import conf

from AnyQt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from pyforms.gui.controls.ControlBase import ControlBase


from AnyQt import _api

if _api.USED_API == _api.QT_API_PYQT5:
	from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
	from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
elif _api.USED_API == _api.QT_API_PYQT4:
	from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
	from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.figure import Figure
import matplotlib.pyplot as plt



class ControlMatplotlib(ControlBase, QWidget):
    def __init__(self, *args, **kwargs):
        self._value = kwargs.get('value')
        QWidget.__init__(self)
        ControlBase.__init__(self, *args, **kwargs)

    def init_form(self):
        plt.ion()
        self._fig = Figure()
        self._ax = self._fig.add_subplot(111)
        self._img = self._ax.imshow(np.zeros([512,512]))
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setParent(self)
        self._mpl_toolbar = NavigationToolbar(self._canvas, self)
        self._cb = self._fig.colorbar(self._img)
        self._cb.formatter.set_useOffset(False)
        self._cb.update_ticks()

        vbox = QVBoxLayout()
        vbox.addWidget(self._canvas)
        vbox.addWidget(self._mpl_toolbar)
        self.setLayout(vbox)
        self.on_draw()

    def on_draw(self):
        self._img.set_data(self._value)
        self._img.autoscale()
        self._canvas.draw()
        self.repaint()

    def read_daq(self, newData):
        self._value = newData
        self.on_draw()

    ############################################################################
    ############ Properties ####################################################
    ############################################################################

    @property
    def form(self):
        return self


    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        if self._value.any():
            self.on_draw()