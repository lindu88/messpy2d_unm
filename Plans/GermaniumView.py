import numpy as np
import pyqtgraph.parametertree as pt
import typing as T
from Signal import Signal
from .GermaniumPlan import GermaniumPlan
from .common_meta import samp
from Config import config
from qtpy.QtWidgets import QWidget, QSizePolicy, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QApplication, QTabWidget
from qtpy.QtGui import QPalette, QFont
from qtpy.QtCore import Qt, QTimer
from ControlClasses import Controller, Cam
from QtHelpers import vlay, hlay, PlanStartDialog, ObserverPlot


class GermaniumView(QWidget):
    def __init__(self, germanium_plan: GermaniumPlan, *args, **kwargs):
        super(ScanSpectrumView, self).__init__(*args, **kwargs)

        get_signal = lambda: germanium_plan.germaniumSignal[:germanium_plan.t_idx]
        times = lambda: germanium_plan[:germanium_plan.t_idx]

        self.plot = ObserverPlot(
                obs= [get_signal],
                signal=germanium_plan.sigStepDone,
                x = times,
        )

        pen = pg.mkPen(color='#e377c2', width=2)
        plotGer = lambda: self.plot.plotItem.plot(germanium_plan.t, germanium_plan.fit.model, pen=pen)

        germanium_plan.sigGerDone.connect(lambda: plotGer())

        self.button = QPushButton('Set time zero', self)
        self.button.setEnabled(False)
        self.button.clicked.connect(lambda: print('not implemented yet'))
        germanium_plan.sigGerDone.connect(lambda: self.button.setEnabled(True))


        self.plot.plotItem.setLabel('bottom', 'time [ps]')
        layout = QVBoxLayout(self)
        layout.addLayout(self.plot)
        layout.addWidget(self.button)
        self.setLayout(layout)


import pyqtgraph.parametertree.parameterTypes as pTypes

class FocusScanStarter(PlanStartDialog):
    experiment_type = 'GermaniumScan'
    title = "Germanium Scan"
    viewer = GermaniumView

    def setup_paras(self):
        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'germanium'},
               {'name': 'Shots', 'type': 'int', 'max': 2000, 'value': 100},
               {'name': 'Start time', 'suffix': 'ps', 'type': 'float', 'value': -1},
               {'name': 'End time', 'suffix': 'ps', 'type': 'float', 'value': 1},
               {'name': 'Steps', 'suffix': 'ps', 'type': 'float', 'min': 0.1},
               ]


        self.p = pt.Parameter.create(name='Exp. Settings', type='group', children=tmp)
        params = [self.p]
        self.paras = pt.Parameter.create(name='Scan Spectrum', type='group', children=params)
        self.save_defaults()

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')
        t_List = np.arange([p['Start time'], p['End time'], p['Steps']])
        ger = GermaniumPlan(
            name=p['Filename'],
            cam=self.candidate_cams[p['Cam']],
            t_List = t_List,
            shots = p['Shots']
        )
        return ger