import sys

import numpy as np
import pyqtgraph.parametertree as pt
from pyqtgraph import PlotWidget, ImageItem, PlotCurveItem, LinearRegionItem, mkBrush
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import (QApplication, QWidget)
from matplotlib import cm
import typing as T

from imaq_nicelib import Cam

from QtHelpers import hlay, vlay



row_paras = {'type': 'int', 'step': 1, 'min': 0, 'max': 128,
             'readonly': True}
params = [
    #{'name': 'Gain', 'type': 'int', 'value': 8, 'min': 1, 'max': 8},
    #{'name': 'Offset', 'type': 'int', 'value': 128, 'step': 1, 'min': 0, 'max': 255},
    {'name': 'Shots', 'type': 'int', 'value': 30, 'min': 10, 'max': 5000 },
    {'name': 'Top Probe', 'value': 35, **row_paras},
    {'name': 'Bot. Probe', 'value': 30, **row_paras},
    {'name': 'Top Ref', 'value': 103, **row_paras},
    {'name': 'Bot. Ref', 'value': 93, **row_paras},
    {'name': 'Top Probe2', 'value': 60, **row_paras},
    {'name': 'Bot. Probe2', 'value': 50, **row_paras},
    {'name': 'Record BG', 'type': 'action'},
    {'name': 'Delete BG', 'type': 'action'},
    {'name': 'Temp', 'type': 'float', 'readonly': True},
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

        self.pr_reg = LinearRegionItem(orientation=LinearRegionItem.Horizontal,
                                       values=(p['Bot. Probe'], p['Top Probe']))
        self.pr2_reg = LinearRegionItem(orientation=LinearRegionItem.Horizontal,
                                       values=(p['Bot. Probe2'], p['Top Probe2']))

        self.ref_reg = LinearRegionItem(orientation=LinearRegionItem.Horizontal, values=(p['Bot. Ref'], p['Top Ref']))
        self.pr_reg.setBrush(mkBrush([0, 0, 0, 0]))
        self.ref_reg.setBrush(mkBrush([0, 0, 0, 0]))
        self.pr2_reg.setBrush(mkBrush([0, 0, 0, 0]))
        self.pr_mean = PlotCurveItem(pen="r")
        self.pr2_mean = PlotCurveItem(pen="y")
        self.ref_mean = PlotCurveItem(pen="g")

        self.pr_reg.setZValue(10)

        self.left_line = PlotCurveItem(pen='r')
        self.right_line = PlotCurveItem(pen='b')

        for item in self.left_line, self.right_line, self.image, self.pr_reg, \
                    self.ref_reg, self.pr_mean, self.ref_mean, self.pr2_mean, self.pr2_reg:
            self.plotWidget.plotItem.addItem(item)

        self.pr_std = PlotCurveItem(pen='r')
        self.pr2_std = PlotCurveItem(pen='y')
        self.ref_std = PlotCurveItem(pen='b')
        self.norm_std = PlotCurveItem(pen='g')
        for i in self.pr_std, self.ref_std, self.norm_std, self.pr2_std:
            self.stdPlotWidget.plotItem.addItem(i)

        self.setLayout(hlay([self.paratree, vlay([self.plotWidget, self.stdPlotWidget])]))
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        self.params = p
        self.setup_connections()

    def setup_connections(self):
        p = self.params
        pm = self.cam
        #f = lambda val: pm._cam.set_gain(val.value())
        #p.child('Gain').sigValueChanged.connect(f)
        #f = lambda val: pm._cam.set_offset(val.value())
        #p.child('Offset').sigValueChanged.connect(f)
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

        # p.child('Temp').setValue(self.cam._cam.get_tempK())

        # def update_temp():
        #    p.child('Temp').setValue(self.cam._cam.get_tempK())
        # self.temp_timer = QTimer()
        # self.temp_timer.timeout.connect(update_temp)
        # self.temp_timer.start(10000)
        p.child('Record BG').sigActivated.connect(lambda: self.cam.set_background())
        p.child('Delete BG').sigActivated.connect(self.cam.remove_background)

    def update(self):
        pm = self.cam
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

        # print(img.shape)
        self.image.setImage(img.T, levels=levels)
        # print(np.median(img))
        # self.pr_reg.setRegion((0, 10))
        self.left_line.setData(x=-(img[:, 0] / MAX_VAL * 100), y=y)
        self.right_line.setData(x=-(img[:, -1] / MAX_VAL * 100), y=y)

        a, b = int(self.params['Top Probe']), int(self.params['Bot. Probe'])
        probe = data[b:a, :, :].sum(0)
        self.pr_mean.setData(x=x, y=img[b:a, :].mean(0) / MAX_VAL * 100 + 128)
        self.pr_std.setData(x=x, y=100 * probe.std(1) / probe.mean(1))

        a, b = int(self.params['Top Probe2']), int(self.params['Bot. Probe2'])
        probe = data[b:a, :, :].sum(0)
        self.pr2_mean.setData(x=x, y=img[b:a, :].mean(0) / MAX_VAL * 100 + 128)
        self.pr2_std.setData(x=x, y=100 * probe.std(1) / probe.mean(1))

        a, b = self.params['Top Ref'], self.params['Bot. Ref']
        a, b = int(a), int(b)
        ref = data[b:a, :, :].sum(0)
        self.ref_mean.setData(x=x, y=img[b:a, :].mean(0) / MAX_VAL * 100 + 128)
        self.ref_std.setData(x=x, y=100 * ref.std(1) / ref.mean(1))
        norm = probe / ref
        self.norm_std.setData(x=x, y=100 * norm.std(1) / norm.mean(1))
        # np.save('ref', ref)
        # np.save('probe', probe)

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
