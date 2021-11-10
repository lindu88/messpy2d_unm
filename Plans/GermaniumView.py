import numpy as np
import pyqtgraph.parametertree as pt
import pyqtgraph as pg
import typing as T
from .GermaniumPlan import GermaniumPlan

from qtpy.QtWidgets import (QWidget, QPushButton, QVBoxLayout)

from ControlClasses import Controller
from QtHelpers import vlay, hlay, PlanStartDialog, ObserverPlot


class GermaniumView(QWidget):
    def __init__(self, germanium_plan: GermaniumPlan, *args, **kwargs):
        super(GermaniumView, self).__init__(*args, **kwargs)

        get_signal = lambda: germanium_plan.germaniumSignal[:germanium_plan.t_idx]
        times = lambda: germanium_plan.t[:germanium_plan.t_idx]
        self.plan = germanium_plan
        self.plot = ObserverPlot(
            obs=[get_signal],
            signal=germanium_plan.sigStepDone,
            x=times,
        )

        pen = pg.mkPen(color='#e377c2', width=2)
        self.button = QPushButton('Set time zero', self)

        def plotGer():
            if germanium_plan.fit.success > 0:
                self.plot.plotItem.plot(germanium_plan.t, germanium_plan.fit.model, pen=pen)
                text = pg.TextItem(f'Zero_pos:{int(germanium_plan.fit.params[0])}', anchor=(0, 1.0))
                self.plot.plotItem.addItem(text)
                self.button.setEnabled(False)
                self.button.clicked.connect(lambda: germanium_plan.make_zero())
                self.button.setEnabled(True)
        germanium_plan.sigGerDone.connect(lambda: plotGer())
        self.plot.plotItem.setLabel('bottom', 'time [fs]')
        layout = QVBoxLayout(self)
        layout.addWidget(self.plot)
        layout.addWidget(self.button)
        self.setLayout(layout)


class GermaniumStarter(PlanStartDialog):
    experiment_type = 'GermaniumScan'
    title = "Germanium Scan"
    viewer = GermaniumView

    def setup_paras(self):
        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'germanium'},
               {'name': 'Start time', 'suffix': 'ps', 'type': 'float', 'value': -1, 'step': 0.1},
               {'name': 'End time', 'suffix': 'ps', 'type': 'float', 'value': 1, 'step': 0.1},
               {'name': 'Steps', 'suffix': 'ps', 'type': 'float', 'min': 0.01, 'step': 0.05},
               ]
        self.candidate_cams = {c.cam.name: c for c in self.controller.cam_list}
        tmp.append(dict(name='Cam', type='list', values=self.candidate_cams.keys()))

        self.p = pt.Parameter.create(name='Exp. Settings', type='group', children=tmp)
        params = [self.p]
        self.paras = pt.Parameter.create(name='Scan Spectrum', type='group', children=params)

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')
        t_list = np.arange(p['Start time'], p['End time'], p['Steps'])
        self.save_defaults()
        ger = GermaniumPlan(
            controller=controller,
            name=p['Filename'],
            cam=self.candidate_cams[p['Cam']],
            t_list=t_list
        )
        return ger
