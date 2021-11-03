from typing import Dict

import numpy as np
import pyqtgraph.parametertree as pt
from matplotlib import cm
from pyqtgraph import PlotWidget, ImageItem, PlotCurveItem, LinearRegionItem, mkBrush
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import (QApplication, QWidget)

from QtHelpers import hlay, vlay
from imaq_nicelib import Cam

row_paras = {'type': 'int', 'step': 1, 'min': 0, 'max': 128,
             'readonly': True}
params = [
    {'name': 'Shots', 'type': 'int', 'value': 30, 'min': 10, 'max': 5000},
    {'name': 'Top Probe', 'value': 35, **row_paras},
    {'name': 'Bot. Probe', 'value': 30, **row_paras},
    {'name': 'Top Ref', 'value': 103, **row_paras},
    {'name': 'Bot. Ref', 'value': 93, **row_paras},
    {'name': 'Top Probe2', 'value': 60, **row_paras},
    {'name': 'Bot. Probe2', 'value': 50, **row_paras},
    {'name': 'Record BG', 'type': 'action'},
    {'name': 'Delete BG', 'type': 'action'},
    {'name': "Mode", "type": 'list', 'limits': ('norm', 'relstd', 'absstd')}
]

x = np.arange(128)
y = np.arange(128)
colormap = cm.get_cmap('viridis')
colormap._init()
lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
MAX_VAL = 1 << 14


class CamOptions(QWidget):
    def __init__(self, cam: Cam, parent=None):
        super(CamOptions, self).__init__(parent=parent)
        self.cam = cam
        p = pt.Parameter.create(name='ADC Settings', type='group', children=params)
        self.paratree = pt.ParameterTree(self)
        self.paratree.setParameters(p)

        self.plotWidget = PlotWidget()
        self.stdPlotWidget = PlotWidget()
        self.image = ImageItem()
        self.image.setLookupTable(lut)

        self.regions : Dict[str, LinearRegionItem] = {}
        self.mean_lines: Dict[str, PlotCurveItem] = {}
        self.std_lines: Dict[str, PlotCurveItem] = {}

        for i, line in enumerate(['Probe', 'Probe2', 'Ref']):
            region = LinearRegionItem(orientation=LinearRegionItem.Horizontal,
                                      values=(p[f'Bot. {line}'], p[f'Top {line}']))
            region.setZValue(10)
            region.setBrush(mkBrush([0, 0, 0, 0]))
            self.regions[line] = region
            self.plotWidget.addItem(region)

            mean_line = PlotCurveItem(pen="rby"[i])
            self.mean_lines[line] = mean_line
            self.plotWidget.addItem(mean_line)
            std_line = PlotCurveItem(pen="rby"[i])
            self.std_lines[line] = std_line
            self.stdPlotWidget.plotItem.addItem(std_line)


        self.left_line = PlotCurveItem(pen='r')
        self.right_line = PlotCurveItem(pen='b')

        self.plotWidget.plotItem.addItem(self.left_line)
        self.plotWidget.plotItem.addItem(self.right_line)

        self.std_lines['Norm'] = PlotCurveItem(pen='w')
        self.stdPlotWidget.plotItem.addItem(self.std_lines['Norm'])

        self.setLayout(hlay([self.paratree, vlay([self.plotWidget, self.stdPlotWidget])]))
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        self.params = p
        self.setup_connections()

    def setup_connections(self):
        p = self.params
        pm = self.cam

        p.child('Shots').sigValueChanged.connect(lambda val: pm.set_shots(val.value()))

        def update_pr_regions(reg: LinearRegionItem):
            mi, ma = sorted(reg.getRegion())
            p.child('Top Probe').setValue(ma)
            p.child('Bot. Probe').setValue(mi)

        self.pr_reg.sigRegionChangeFinished.connect(update_pr_regions)

        def update_pr2_regions(reg: LinearRegionItem):
            mi, ma = sorted(reg.getRegion())
            p.child('Top Probe2').setValue(ma)
            p.child('Bot. Probe2').setValue(mi)

        self.pr2_reg.sigRegionChangeFinished.connect(update_pr2_regions)

        def update_ref_regions(reg: LinearRegionItem):
            mi, ma = sorted(reg.getRegion())
            p.child('Top Ref').setValue(ma)
            p.child('Bot. Ref').setValue(mi)
            pm.ref_rows = p['Bot. Ref'], p['Top Ref']
            # config.ref_rows = pm.ref_rows

        self.ref_reg.sigRegionChangeFinished.connect(update_ref_regions)

        p.child('Record BG').sigActivated.connect(lambda: self.cam.set_background())
        p.child('Delete BG').sigActivated.connect(self.cam.remove_background)

    def update(self):
        pm = self.cam
        if self.standalone:
            import threading
            t = threading.Thread(target=pm.read_cam)
            t.start()
            while t.is_alive():
                QApplication.processEvents()

        data = pm.data.copy()
        if pm.background is not None:
            img = pm.data.mean(2) - pm.background
            data = data - pm.background[:, :, None]
            if self.params['Mode'] == 'relstd':
                img = 100 * data.std(2) / data.mean(2)
                levels = [0, 3]
            elif self.params['Mode'] == 'norm':
                img = pm.data.mean(2) - pm.background
                levels = [0, MAX_VAL]
            elif self.params["Mode"] == 'absstd':
                img = pm.data.std(2)
                levels = [0, 100]
        else:
            img = pm.data.mean(2)
            levels = [0, MAX_VAL]


        self.image.setImage(img.T, levels=levels)
        self.left_line.setData(x=-(img[:, 0] / MAX_VAL * 100), y=y)
        self.right_line.setData(x=-(img[:, -1] / MAX_VAL * 100), y=y)
        data = {}
        for i, line in enumerate(['Probe', 'Probe2', 'Ref']):
            a, b = int(self.params[f'Top {line}']), int(self.params[f'Bot. {line}'])
            probe = data[b:a, :, :].sum(0)
            self.mean_lines[line].setData(x=x, y=img[b:a, :].mean(0) / MAX_VAL * 100 + 128)
            self.std_lines.setData(x=x, y=100 * probe.std(1) / probe.mean(1))
            data = {line: probe}

        norm = data['probe'] / data['ref']
        self.norm_std.setData(x=x, y=100 * norm.std(1) / norm.mean(1))

    def get_best_pixel(self):
        pass


if __name__ == '__main__':
    import sys

    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)


    sys.excepthook = exception_hook
    app = QApplication([])
    go = CamOptions(cam=Cam())

    go.show()
    app.exec_()
