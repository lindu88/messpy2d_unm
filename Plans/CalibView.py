from qtpy.QtWidgets import QWidget, QApplication, QHBoxLayout, QVBoxLayout, QSpinBox, QLabel, QPushButton, QDialogButtonBox, QSizePolicy
from qtpy.QtCore import Qt, Signal
from matplotlib.figure import Figure
from matplotlib import rcParams, style
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import attr
import numpy as np
from scipy.constants import c
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d
from typing import Optional
from qtawesome import icon


rcParams['font.family'] = 'Segoe UI'
style.use('dark_background')

@attr.s(auto_attribs=True)
class CalibView(QWidget):
    x: np.ndarray
    y0: np.ndarray
    y1: np.ndarray

    single: int = 6000
    width: int = 150
    dist: int = 350

    prominence: float = 100
    distance: int = 10
    filter: float = 3
    coeff: Optional[np.ndarray] = None

    sigCalibrationAccepted = Signal(object)
    sigCalibrationCanceled = Signal()

    def __attrs_post_init__(self):
        super().__init__()
        dpi = self.logicalDpiX()
        self.setWindowTitle("Calibration")
        self.setWindowIcon(icon('fa5s.ruler-horizontal'))
        self.fig = Figure(dpi=dpi, constrained_layout=True)
        self.ax, self.ax1 = self.fig.subplots(2)
        self.canvas = FigureCanvas(self.fig)

        self.setLayout(QVBoxLayout())

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.setContentsMargins(0, 0, 0, 0)
        self.canvas.setContentsMargins(0, 0, 0, 0)

        self.row = QHBoxLayout()
        self.sb_filter = QSpinBox()
        self.sb_filter.setValue(self.filter)
        self.sb_filter.valueChanged.connect(self.analyze)
        self.row.addWidget(QLabel('Filter'))
        self.row.addWidget(self.sb_filter)


        self.sb_dist = QSpinBox()
        self.sb_dist.setValue(self.distance)
        self.sb_dist.valueChanged.connect(self.analyze)
        self.row.addWidget(QLabel('Peak distance'))
        self.row.addWidget(self.sb_dist)

        self.sb_prom = QSpinBox()
        self.sb_prom.setMaximum(20000)
        self.sb_prom.setValue(self.prominence)
        self.sb_prom.valueChanged.connect(self.analyze)
        self.row.addWidget(QLabel('Peak prominance'))
        self.row.addWidget(self.sb_prom)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.row.addWidget(bb)
        #bb.setFixedWidth(400)
        bb.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.row.setContentsMargins(20, 20, 20, 20)
        self.row.setSpacing(10)
        bb.accepted.connect(lambda: self.sigCalibrationAccepted.emit(self.coeff))
        bb.rejected.connect(self.close)
        bb.rejected.connect(self.sigCalibrationCanceled.emit)
        bb.rejected.connect(self.close)

        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)
        self.layout().addLayout(self.row)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.analyze()
        self.fig.canvas.draw()

    def analyze(self):
        self.prominence = self.sb_prom.value()
        self.distance = self.sb_dist.value()
        self.filter = self.sb_filter.value()
        if self.filter > 0:
            y0 = uniform_filter1d(self.y0, self.filter)
            y1 = uniform_filter1d(self.y1, self.filter)
        else:
            y0, y1 = self.y0, self.y1
        p0, _ = find_peaks(y0, prominence=self.prominence, distance=self.distance)
        p1, _ = find_peaks(y1, prominence=self.prominence, distance=self.distance)

        self.ax.cla()
        self.ax1.cla()
        self.ax.plot(self.x, y0)
        self.ax.plot(self.x, y1)

        ax1 = self.ax1
        x = self.x
        self.ax.plot(self.x[p0], y0[p0], '|', ms=7, c='r')
        self.ax.plot(self.x[p1], y1[p1], '^', ms=7, c='r')
        try:
            a = np.arange(0, 4096 * 3, 500)
            align = np.argmin(abs(x[p0] - x[p1]))
            pix0 = 6000 + self.width / 2
            pixel = a[:len(p0)] - a[align] + pix0

            freqs = c / x[p0] / 1e3
            freq0 = c / x[p1] / 1e3

            ax1.plot(pix0, freq0, marker='o', ms=10)
            ax1.set_xlabel('Pixel')
            ax1.set_ylabel('Freq / THz')
            self.ax.set(xlabel='Wavelength / nm', ylabel='Counts')

            ax1.plot(pixel, freqs, marker='x', ms=10)
            all_pix = np.arange(pixel.min(), pixel.max())
            self.coeff = np.polyfit(pixel, freqs, 2)
            fit = np.polyval(self.coeff, all_pix)
            txt = ''.join(['%.3e\n' % i for i in self.coeff])
            ax1.annotate(txt, (0.95, 0.93), xycoords='axes fraction', va='top', ha='right')
            ax1.plot(all_pix, fit, color='xkcd:lime')
        except ValueError as e:
            print(e)

        finally:
            self.fig.canvas.draw_idle()

if __name__ == '__main__':

    app = QApplication([])
    from qt_material import apply_stylesheet
    apply_stylesheet(app, 'light_blue.xml')
    x, y2, y1 = np.load('calib.npy').T
    view = CalibView(x=x, y0=y1, y1=y2)
    view.show()
    app.exec_()
