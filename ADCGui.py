# from Config import config
from qtpy.QtCore import QTimer, Qt, QThread
from qtpy.QtGui import QFont, QIntValidator
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget,
                            QPushButton, QLabel, QVBoxLayout, QSizePolicy, QFormLayout,
                            QToolBar, QCheckBox)
import qtawesome as qta

from QtHelpers import dark_palette, ControlFactory, make_groupbox, \
    ObserverPlot, ValueLabels, vlay, hlay
# from ControlClasses import Controller
from pyqtgraph import PlotWidget, ImageItem, PlotCurveItem, LinearRegionItem, mkBrush, mkPen
import pyqtgraph.parametertree as pt
import numpy as np

row_paras = {'type': 'int', 'step': 1, 'min': 0, 'max': 128,
             'readonly': True}

params = [

    {'name': 'Gain', 'type': 'int', 'value': 8, 'min': 1, 'max': 8},
    {'name': 'Background', 'type': 'int', 'value': 128, 'step': 1, 'min': 0, 'max': 255},
    {'name': 'Top Probe', 'value': 30, **row_paras},
    {'name': 'Bot. Probe', 'value': 35, **row_paras},
    {'name': 'Top Ref', 'value': 93, **row_paras},
    {'name': 'Bot. Ref', 'value': 103, **row_paras},
]


x = np.arange(128)
y = np.arange(128)
Y, X = np.meshgrid(y, x, indexing='ij')

from matplotlib import cm

colormap = cm.get_cmap('viridis')  # cm.get_cmap("CMRmap")
colormap._init()

lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt


# Apply the colormap


class PTMock:
    def __init__(self):
        self.gain = 8
        self.background = 128

    def set_gain(self, gain: int):
        self.gain = gain

    def set_background(self, bg):
        print(bg)
        self.background = bg

    def read_all(self):
        out = np.zeros((y.size, x.size), dtype=np.uint16)
        # print(out.shape, Y.shape, X.shape)
        ref_sig = np.exp(-(Y - (X - 64) * 0.03 - 83) ** 2 / 50) * 4000 * self.gain / 8
        out += np.uint16(ref_sig)
        pr_sig = np.exp(-(Y - (X - 64) * 0.03 - 33) ** 2 / 50) * self.gain / 8 * 4000
        out += np.uint16(pr_sig)

        out += np.uint16(np.random.poisson(lam=1500, size=out.shape))
        out -= self.background * 1000 + 128000

        np.clip(out, 0, MAX_VAL - 1, out)
        return out


pm = PTMock()

MAX_VAL = 1 << 14


class GuiOptionsWindow(QWidget):
    def __init__(self, parent=None):
        super(GuiOptionsWindow, self).__init__(parent=parent)
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

        f = lambda val: pm.set_gain(val.value())
        p.child('Gain').sigValueChanged.connect(f)

        f = lambda val: pm.set_background(val.value())
        p.child('Background').sigValueChanged.connect(f)

        def update_pr_regions(reg: LinearRegionItem):
            mi, ma = sorted(reg.getRegion())
            p.child('Top Probe').setValue(ma)
            p.child('Bot. Probe').setValue(mi)

        self.pr_reg.sigRegionChangeFinished.connect(update_pr_regions)

        def update_ref_regions(reg: LinearRegionItem):
            mi, ma = sorted(reg.getRegion())
            p.child('Top Ref').setValue(ma)
            p.child('Bot. Ref').setValue(mi)

        self.ref_reg.sigRegionChangeFinished.connect(update_ref_regions)
        self.params = p

    def update(self):
        img = pm.read_all()
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

    def gen_mask(self):
        pass

if __name__ == '__main__':
    app = QApplication([])
    go = GuiOptionsWindow()

    go.show()
    app.exec_()
