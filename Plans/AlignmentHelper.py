import pyqtgraph as pg
import time
from qtpy.QtGui import QFont, QGuiApplication
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget,
                            QPushButton, QLabel, QVBoxLayout, QSizePolicy,
                            QToolBar, QCheckBox)
import QtHelpers as qh
from ControlClasses import Controller

class AlignmentHelper(QWidget):
    def __init__(self, controller: Controller, **kwargs):
        super().__init__(**kwargs)
        self.times = []
        self.time_max = 20
        self.controller = controller
        cam1_obs = (controller.cam.last_read)

        self.left_plots = qh.ObserverPlot(parent=self, x=self.times)





