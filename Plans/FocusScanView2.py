import numpy as np
import pyqtgraph.parametertree as pt
import pyqtgraph as pg
import typing as T
from Signal import Signal
from .FocusScan import FocusScan
from Config import config
from qtpy.QtWidgets import QWidget, QPushButton,QLayout, QSizePolicy, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QApplication, QTabWidget
from qtpy.QtGui import QPalette, QFont
from qtpy.QtCore import Qt, QTimer
from ControlClasses import Controller, Cam
from QtHelpers import vlay, hlay, PlanStartDialog, ObserverPlot
from .common_meta import samp
from collections import namedtuple




class FocusScanView(QWidget):
    def __init__(self, fsPlan: FocusScan, *args, **kwargs):
        super(FocusScanView, self).__init__(*args, **kwargs)

        if fsPlan.scan_x:
            self.x_probe_plot = ObserverPlot(
                obs= (fsPlan, "probe_x"),
                signal=fsPlan.sigStepDone,
                x=fsPlan.pos_x
            )

            self.x_ref_plot = ObserverPlot(
                obs=(fsPlan, "ref_x"),
                signal=fsPlan.sigStepDone,
                x=fsPlan.pos_x
            )
        if fsPlan.scan_y:
            self.y_probe_plot = ObserverPlot(
                obs=(fsPlan, "probe_y"),
                signal=fsPlan.sigStepDone,
                x=fsPlan.pos_y
            )

            self.y_ref_plot = ObserverPlot(
                obs=(fsPlan, "ref_y"),
                signal=fsPlan.sigStepDone,
                x=fsPlan.pos_y
            )

        def plotFit():
            pen = pg.mkPen(color='#e377c2', width=2)
            if fsPlan.scan_x:
                self.x_probe_plot.plotItem.plot(fsPlan.pos_x, fsPlan.fit_xprobe.model, pen = pen)
                text_1 = pg.TextItem(fsPlan.xtext_probe, anchor=(0, 1.0))
                text_1.setPos(fsPlan.pos_x[int(len(fsPlan.pos_x) / 2)], (np.max(fsPlan.probe_x) + np.min(fsPlan.probe_x)) / 2.)
                self.x_probe_plot.plotItem.addItem(text_1)
                self.x_ref_plot.plotItem.plot(fsPlan.pos_x, fsPlan.fit_xref.model, pen = pen)
                text_2 = pg.TextItem(fsPlan.xtext_ref, anchor=(0, 1.0))
                text_2.setPos(fsPlan.pos_x[int(len(fsPlan.pos_x) / 2)], (np.max(fsPlan.ref_x) + np.min(fsPlan.ref_x)) / 2.)
                self.x_ref_plot.plotItem.addItem(text_2)

            if fsPlan.scan_y:
                self.y_probe_plot.plotItem.plot(fsPlan.pos_y, fsPlan.fit_yprobe.model, pen = pen)
                text_3 = pg.TextItem(fsPlan.ytext_probe, anchor=(0, 1.0))
                text_3.setPos(fsPlan.pos_y[int(len(fsPlan.pos_y) / 2)], (np.max(fsPlan.probe_y) + np.min(fsPlan.probe_y)) / 2.)
                self.y_probe_plot.plotItem.addItem(text_3)
                self.y_ref_plot.plotItem.plot(fsPlan.pos_y, fsPlan.fit_yref.model, pen = pen)
                text_4 = pg.TextItem(fsPlan.ytext_ref, anchor=(0, 1.0))
                text_4.setPos(fsPlan.pos_y[int(len(fsPlan.pos_y) / 2)], (np.max(fsPlan.ref_y) + np.min(fsPlan.ref_y)) / 2.)
                self.x_ref_plot.plotItem.addItem(text_4)

        fsPlan.sigFitDone.connect(lambda: plotFit())


        if fsPlan.scan_x and fsPlan.scan_y:
            self.plotlay =  hlay([vlay([self.x_probe_plot, self.x_ref_plot]),
                             vlay([self.y_probe_plot, self.y_ref_plot])])
        elif fsPlan.scan_x and not fsPlan.scan_y:
            self.plotlay = vlay([self.x_probe_plot, self.x_ref_plot])
        elif fsPlan.scan_y and not fsPlan.scan_x:
            self.plotlay = vlay([self.y_probe_plot, self.y_ref_plot])

        fsPlan.sigFitDone.connect(lambda: self.button.setEnabled(True))
        self.button = QPushButton('Redo Scan', self)
        self.button.setEnabled(False)
        self.button2 = QPushButton('Close', self)
        self.button2.setEnabled(False)
        self.button.clicked.connect(lambda: fsPlan.redo_trigggerd())
        self.button2.clicked.connect(lambda: fsPlan.stopper())
        layout=QVBoxLayout(self)
        layout.addLayout(self.plotlay)
        layout.addWidget(self.button)
        layout.addWidget(self.button2)
        self.setLayout(layout)


class FocusScanStarter(PlanStartDialog):
    experiment_type = 'FocusScan'
    title = "Focus Scan"
    viewer = FocusScanView

    def setup_paras(self):
        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp_focus'},
               {'name': 'Operator', 'type': 'str', 'value': ''},
               {'name': 'Shots', 'type': 'int', 'max': 2000, 'value': 100},
               {'name': 'Scan x', 'type': 'bool', 'value': True},
               {'name': 'Scan y', 'type': 'bool', 'value': True},
               {'name': 'Start x', 'type': 'float', 'value': 0},
               {'name': 'End x', 'type': 'float', 'value': 1},
               {'name': 'Start y', 'type': 'float', 'value': 0},
               {'name': 'End y', 'type': 'float', 'value': 1},
               {'name': 'steps', 'type': 'float', 'value': 0.1}
               ]

        self.candidate_cams = {c.cam.name: c for c in self.controller.cam_list}
        tmp.append(dict(name='Cam', type='list', values=self.candidate_cams.keys()))
        self.p = pt.Parameter.create(name='Exp. Settings', type='group', children=tmp)
        params = [samp, self.p]
        self.paras = pt.Parameter.create(name='Scan Spectrum', type='group', children=params)
        self.save_defaults()

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')
        s = self.paras.child('Sample')
        x_stepper = []
        y_stepper = []

        if p['Scan x']:
            x_stepper = [p['Start x'], p['End x'], p['steps']]
        if p['Scan y']:
            y_stepper = [p['Start y'], p['End y'], p['steps']]

        fs = FocusScan(
            name=p['Filename'],
            cam=self.candidate_cams[p['Cam']],
            meta=s,
            x_parameters=x_stepper,
            y_parameters=y_stepper
        )
        return fs




if __name__ == '__main__':
    import sys

    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook

    app = QApplication([])
    con = Controller()
    timer = QTimer()
    timer.timeout.connect(con.loop)

    fs = FocusScan()
    con.plan = fs
    ppi = FocusScanViewViewer(fs)
    ppi.show()
    # formlayout.fedit(start_form)
    timer.start(50)
    try:
        app.exec_()
    except:
        print('fds')
