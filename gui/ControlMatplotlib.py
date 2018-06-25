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
from mpl_toolkits.mplot3d import Axes3D



class ControlMatplotlib(ControlBase, QWidget):
    def __init__(self, *args, **kwargs):
        #self._value = kwargs.get('value')
        QWidget.__init__(self)
        ControlBase.__init__(self, *args, **kwargs)

    def init_form(self):
        plt.ion()
        print(self._value)
        self._fig = Figure()
        self.axes = self._fig.add_subplot(111)
        self.canvas = FigureCanvas(self._fig)
        self.canvas.setParent(self)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        self.setLayout(vbox)
        self.on_draw()

    def draw(self):
        self.on_draw()
        self.canvas.draw()

    def on_draw(self):
        self.axes.cla()
        self.axes.plot(self._value)
        self.canvas.draw()


    ############################################################################
    ############ Properties ####################################################
    ############################################################################

    @property
    def form(self): return self


    @property
    def value(self): return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.draw()