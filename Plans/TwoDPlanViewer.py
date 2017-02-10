from collections import defaultdict
from qtpy.QtWidgets import *
from qtpy.QtGui import QPalette, QFont
from qtpy.QtCore import Qt, QTimer
from Config import config
from ControlClasses import Controller
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
from QtHelpers import ObserverPlot, vlay, hlay, PlanStartDialog
import numpy as np
from Plans.TwoDPlan import TwoDimMoving

class TwoDViewer(QWidget):
    def __init__(self, plan: TwoDimMoving, **kwargs):
        self.plan = plan
        super().__init__(**kwargs)
        self.setWindowTitle(plan.name)
        self.setMinimumSize(1200, 600)

        self.info_wid = QLabel()
        self.lines = {}
        self.setup_plots()
        self.setup_info()
        self.layout_widget()
        self.plan.sigScanFinished.connect(self.update)

    def setup_info(self):
        self.info_wid.setAlignment(Qt.AlignTop)
        self.info_wid.setText('2D Plan')

    def setup_plots(self):
        self.bin_plot = pg.PlotWidget(parent=self)
        self.trans_plot = pg.PlotWidget(parent=self)
        self.map_plot = pg.PlotWidget(parent=self)
        self.lines['bins'] = self.bin_plot.plotItem.plot()
        for i in range(16):
            self.lines[i] = self.trans_plot.plot()
        self.lines['pyro'] = self.trans_plot.plot()


    def layout_widget(self):
        lay = hlay([self.trans_plot,
                    vlay([self.bin_plot, self.map_plot]),
                    self.info_wid])
        self.setLayout(lay)

    def update(self):
        p = self.plan
        lr = p.last_read
        offsets = np.ptp(lr.probe, axis=1)
        mins = np.min(lr.probe, axis=1)
        x = lr.fringe
        for i in range(16):
            self.lines[i].setData(x, lr[i, :]+offsets)
        self.lines['bins'].setData(x, lr.ext[:, 3])


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
               {'name': 'Shots', 'type': 'int',  'max': 4000, 'decimals': 5,
                'step': 500},
               {'name': 'delay 1', 'type': 'float'},
               {'name': 'max. Tau 2', 'type': 'float', 'dec': True,
                'step': 0.1, 'siPrefix': False, 'suffix': ' ps'},
               {'name': 'min. Tau 2', 'type': 'float', 'dec': True,
                'step': 0.1, 'siPrefix': False, 'suffix': ' ps', 'default': -1},

               ]
        two_d = {'name': '2D Settings', 'type': 'group', 'children': tmp}

        params = [samp, two_d]
        self.paras = Parameter.create(name='2D plan', type='group', children=params)

    def create_plan(self, controller):
        p = self.paras.child('2D Settings')
        TwoDimMoving(
            name=p['Filename'],
            t_range=(p['min. Tau 2'], p['max. Tau 2']),
            shots=p['Shots'],
            controller=controller,
        )



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
    #tw.show()
    app.exec_()
