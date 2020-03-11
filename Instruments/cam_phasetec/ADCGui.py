from Config import config
import numpy as np
import pyqtgraph.parametertree as pt
from pyqtgraph import PlotWidget, ImageItem, PlotCurveItem, LinearRegionItem, mkBrush
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import (QApplication, QWidget)
from matplotlib import cm
import typing as T
from QtHelpers import hlay
if T.TYPE_CHECKING:
    from Instruments.cam_phasetec import PT_MCT, PhaseTecCam

row_paras = {'type': 'int', 'step': 1, 'min': 0, 'max': 128,
             'readonly': True}
params = [
    {'name': 'Gain', 'type': 'int', 'value': 8, 'min': 1, 'max': 8},
    {'name': 'Offset', 'type': 'int', 'value': 128, 'step': 1, 'min': 0, 'max': 255},
    {'name': 'Top Probe', 'value': 30, **row_paras},
    {'name': 'Bot. Probe', 'value': 35, **row_paras},
    {'name': 'Top Ref', 'value': 93, **row_paras},
    {'name': 'Bot. Ref', 'value': 103, **row_paras},
    {'name': 'Record BG', 'type': 'action'},
    {'name': 'Delete BG', 'type': 'action'},
]

x = np.arange(128)
y = np.arange(128)
colormap = cm.get_cmap('viridis')
colormap._init()
lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt
MAX_VAL = 1 << 14


class CamOptions(QWidget):
    def __init__(self, cam: PhaseTecCam, parent=None):
        super(CamOptions, self).__init__(parent=parent)
        self.cam = cam
        p = pt.Parameter.create(name='ADC Settings', type='group', children=params)
        self.paratree = pt.ParameterTree(self)
        self.paratree.setParameters(p)
        self.plotWidget = PlotWidget()
        self.image = ImageItem()
        self.image.setLookupTable(lut)

        self.pr_reg = LinearRegionItem(orientation="horizontal", pen="r")
        self.ref_reg = LinearRegionItem(orientation="horizontal", pen="g")
        self.pr_reg.setBrush(mkBrush([0, 0, 0, 0]))
        self.ref_reg.setBrush(mkBrush([0, 0, 0, 0]))
        self.pr_mean = PlotCurveItem(pen="r")
        self.ref_mean = PlotCurveItem(pen="g")

        self.pr_reg.setZValue(10)

        self.left_line = PlotCurveItem(pen='r')
        self.right_line = PlotCurveItem(pen='b')

        for item in self.left_line, self.right_line, self.image, self.pr_reg, \
                    self.ref_reg, self.pr_mean, self.ref_mean:
            self.plotWidget.plotItem.addItem(item)

        self.setLayout(hlay([self.paratree, self.plotWidget]))
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        self.image.setLevels([0, MAX_VAL])
        self.setup_connections()
        self.params = p

    def setup_connections(self):
        p = self.params
        pm = self.cam
        f = lambda val: pm._cam.set_gain(val.value())
        p.child('Gain').sigValueChanged.connect(f)
        f = lambda val: pm._cam.set_background_level(val.value())
        p.child('Offset').sigValueChanged.connect(f)

        def update_pr_regions(reg: LinearRegionItem):
            mi, ma = sorted(reg.getRegion())
            p.child('Top Probe').setValue(ma)
            p.child('Bot. Probe').setValue(mi)
        self.pr_reg.sigRegionChangeFinished.connect(update_pr_regions)

        def update_ref_regions(reg: LinearRegionItem):
            mi, ma = sorted(reg.getRegion())
            p.child('Top Ref').setValue(ma)
            p.child('Bot. Ref').setValue(mi)
            pm.ref_rows = p['Bot. Ref'], p['Top Ref']
            config.ref_rows = pm.ref_rows

        self.ref_reg.sigRegionChangeFinished.connect(update_ref_regions)

        p.child('Record BG').sigValueChanged.connect(self.cam.set_background)
        p.child('Delete BG').sigValueChanged.connect(self.cam.remove_background)

    def update(self):
        pm = self.cam
        img = pm.read_cam().mean(0)
        # print(img.shape)
        self.image.setImage(img.T, autoLevels=False)
        # print(np.median(img))
        # self.pr_reg.setRegion((0, 10))
        self.left_line.setData(x=-(img[:, 0] / MAX_VAL * 100), y=y)
        self.right_line.setData(x=-(img[:, -1] / MAX_VAL * 100), y=y)

        a, b = self.params['Top Probe'], self.params['Bot. Probe']
        self.pr_mean.setData(x=x, y=img[b:a, :].mean(0) / MAX_VAL * 100 + 128)

        a, b = self.params['Top Ref'], self.params['Bot. Ref']
        self.ref_mean.setData(x=x, y=img[b:a, :].mean(0) / MAX_VAL * 100 + 128)

    def get_best_pixel(self):
        pass


if __name__ == '__main__':
    app = QApplication([])
    go = CamOptions()

    go.show()
    app.exec_()
