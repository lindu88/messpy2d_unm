from collections import defaultdict
from qtpy.QtWidgets import *
from qtpy.QtGui import QPalette, QFont
from qtpy.QtCore import Qt, QTimer
from ControlClasses import Controller
from Plans.PumpProbe import PumpProbePlan
import pyqtgraph as pg
from QtHelpers import ObserverPlot, vlay, hlay
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
        
    

if __name__ == '__main__':
    app = QApplication([])
    tdp = TwoDimMoving('TestPlan')
    tw = TwoDViewer(tdp)
    tw.show()
    app.exec_()