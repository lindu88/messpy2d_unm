from collections import defaultdict
from qtpy.QtWidgets import *
from qtpy.QtGui import QPalette, QFont
from qtpy.QtCore import Qt, QTimer
from Config import config
from ControlClasses import Controller
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
from QtHelpers import ObserverPlot, vlay, hlay, PlanStartDialog, ControlFactory
import numpy as np
from Plans.TwoDPlan import TwoDimMoving

class TwoDViewer(QWidget):
    """Viewer for the two D plan"""
    def __init__(self, plan: TwoDimMoving, **kwargs):
        self.plan = plan
        super().__init__(**kwargs)
        self.setWindowTitle(plan.name)
        self.setMinimumSize(1200, 600)
        self.info_wid = QLabel()

        self.shots = ControlFactory('Shots', plan.set_shots, plan.sigShotsChanged)
        self.max_tau = ControlFactory('end tau', plan.set_tau_max, plan.sigTauEndChanged)
        self.min_tau = ControlFactory('start tau', plan.set_tau_min, plan.sigTauStartChanged)
        self.speed = ControlFactory('speed', plan.set_speed, plan.sigSpeedChanged)

        self.lines = {}
        self.setup_plots()
        self.setup_info()
        self.layout_widget()
        self.plan.sigScanFinished.connect(self.refresh)

    def setup_info(self):
        self.info_wid.setAlignment(Qt.AlignTop)
        self.info_wid.setText('2D Plan')

    def setup_plots(self):
        self.bin_plot = pg.PlotWidget(parent=self)
        self.trans_plot = pg.PlotWidget(parent=self)
        self.map_plot = pg.PlotWidget(parent=self)
        self.lines['bins'] = self.bin_plot.plotItem.plot()
        for i in list(range(16)) + ['pyro']:
            self.lines[i] = self.trans_plot.plot()

        self.lines['pd1'] = self.bin_plot.plot(pen=pg.mkPen('r', width=1))
        self.lines['pd2'] = self.bin_plot.plot(pen=pg.mkPen('g', width=1))
        #self.lines['sum_sig'] = self.tra.plot(pen=pg.mkPen('g', width=1))

    def layout_widget(self):
        con = vlay([self.info_wid, self.speed, self.shots, self.max_tau, self.min_tau])

        lay = hlay([self.trans_plot,
                    vlay([self.bin_plot, self.map_plot]),
                    con])
        self.setLayout(lay)

    def refresh(self):
        p = self.plan
        lr = p.lr
        #offsets = np.ptp(lr.probe, axis=1)
        #mins = np.min(lr.probe, axis=1)

        #for i in range(16):
        #    self.lines[i].setData(x, lr[i, :]+offsets)

        self.lines['pyro'].setData(p.bin_pre[:-1], p.cur_interferogram)
        self.lines['pd1'].setData(lr.ext[:, -2])
        self.lines['pd2'].setData(lr.ext[:, -3])
        for i in range(1):
            self.lines[i].setData(p.bin_pre[:-1], -p.bin_probe.mean(1))


class TwoDStarter(PlanStartDialog):
    title = "New 2D-Plan"

    def setup_paras(self):
        samp = {'name': 'Sample', 'type': 'group', 'children': [
            dict(name='Sample', type='list', values=config.list_of_samples),
            dict(name='Solvent', type='list', values=config.list_of_solvents),
            dict(name='Excitation', type='str'),
            dict(name='Thickness', type='str'),
            dict(name='Annotations', type='str')]}

        tmp = [{'name': 'Filename', 'type': 'str'},
               {'name': 'Shots', 'type': 'int',  'max': 40000, 'decimals': 5,
                'step': 500},
               {'name': 'delay 1', 'type': 'float'},
               {'name': 'end Tau 2', 'type': 'float', 'dec': True,
                'step': 0.1, 'siPrefix': False, 'suffix': ' ps', 'default': 3},
               {'name': 'start Tau 2', 'type': 'float', 'dec': True,
                'step': 0.1, 'siPrefix': False, 'suffix': ' ps', 'default': -3},
               {'name': 'Speed', 'type': 'float', 'dec': True,
                'step': 0.05, 'siPrefix': False, 'suffix': ' mm/s', 'default': 0.2},
               ]
        two_d = {'name': '2D Settings', 'type': 'group', 'children': tmp}

        params = [samp, two_d]
        self.paras = Parameter.create(name='2D plan', type='group', children=params)

    def create_plan(self, controller):
        p = self.paras.child('2D Settings')
        s = self.paras.child('Sample')
        p = TwoDimMoving(
            name=p['Filename'],
            start_end_tau=[p['start Tau 2'], p['end Tau 2']],
            shots=p['Shots'],
            controller=controller,
            speed = p['Speed']
        )
        self.save_defaults()
        return p

if __name__ == '__main__':
    import sys
    sys._excepthook = sys.excepthook
    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)
    sys.excepthook = exception_hook

    config.list_of_solvents = ['Toluene', 'THF', 'H20', 'D20', 'DMSO', 'None']
    config.list_of_samples = ['Cyclohexanol', 'Phenylisocyanat']
    app = QApplication([])
    tdp = TwoDimMoving('TestPlan')
    #tw = TwoDViewer(tdp)
    twd = TwoDStarter()
    twd.show()

    controller = Controller()
    p = twd.create_plan(controller)
    #tw.show()
    controller.plan = p
    tw = TwoDViewer(p)
    tw.show()
    app.exec_()
