import matplotlib.pyplot as plt
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
from scipy.ndimage import uniform_filter1d, gaussian_filter1d
from typing import Optional
from qtawesome import icon


rcParams['font.family'] = 'Segoe UI'
style.use('dark_background')

@attr.s(auto_attribs=True)
class CalibView(QWidget):
    x: np.ndarray
    y_train: np.ndarray
    y_single: np.ndarray
    y_full: Optional[np.ndarray] = None

    single: int = 15*500
    width: int = 150
    dist: int = 350

    prominence: float = 50
    distance: int = 3
    filter: float = 1
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
        self.sb_dist.setMinimum(1)

        self.row.addWidget(QLabel('Peak distance'))
        self.row.addWidget(self.sb_dist)

        self.sb_prom = QSpinBox()
        self.sb_prom.setMaximum(20000)
        self.sb_prom.setValue(self.prominence)
        self.sb_prom.valueChanged.connect(self.analyze)
        self.row.addWidget(QLabel('Peak prominance'))
        self.row.addWidget(self.sb_prom)

        self.use_norm = QCheckBox("Normalize")
        self.use_norm.toggled.connect(self.analyze)
        self.row.addWidget(self.use_norm)

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

        self.gvd_slider = QSlider()
        self.gvd_slider.setMinimum(-300)
        self.gvd_slider.setMaximum(300)
        self.layout().addWidget(self.gvd_slider)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.analyze()
        self.fig.canvas.draw()

    def analyze(self):
        self.prominence = self.sb_prom.value()
        self.distance = self.sb_dist.value()
        self.filter = self.sb_filter.value()
        if self.filter > 0:

            y_train = gaussian_filter1d(self.y_train, self.filter)
            y_single = gaussian_filter1d(self.y_single, self.filter)
        else:
            y_train, y_single = self.y_train, self.y_single
        if self.use_norm.isChecked():
            y_train = 500*(y_train/(y_full+50))
            y_single = 500*(y_single/(y_full+50))

        p0, _ = find_peaks(y_train, prominence=self.prominence, distance=self.distance)
        p1, _ = find_peaks(y_single, prominence=self.prominence, distance=self.distance)

        self.ax.cla()
        self.ax1.cla()
        self.ax.plot(self.x, y_train)
        self.ax.plot(self.x, y_single)
        if self.y_full is not None and not self.use_norm.isChecked():
            self.ax.plot(self.x, y_full)
        ax1 = self.ax1
        x = self.x
        self.ax.plot(self.x[p0], y_train[p0], '|', ms=7, c='r')
        self.ax.plot(self.x[p1], y_single[p1], '^', ms=7, c='r')
        if len(p0) > 1 and len(p1) == 1:
            a = np.arange(0, 4096 * 3, self.width + self.dist)
            align = np.argmin(abs(x[p0] - x[p1]))
            pix0 = self.single + self.width / 2
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

            self.fig.canvas.draw_idle()

if __name__ == '__main__':
    from Instruments.dac_px.pxdac import AOM
    aom = AOM()
    app = QApplication([])
    #from qt_material import apply_stylesheet
    #apply_stylesheet(app, 'light_blue.xml')
    x, y_train, y_single, y_full = np.load('calib.npy').T
    y_single -= y_single.min()
    y_train -= y_train.min()
    y_full -= y_full.min()
    view = CalibView(x=x, y_single=y_single, y_train=y_train, y_full=y_full)
    view.show()
    view.sigCalibrationAccepted.connect(aom.set_calib)
    view.sigCalibrationAccepted.connect(lambda x: aom.generate_waveform(np.ones_like(aom.nu), np.ones_like(aom.nu)))
    def set_gvd(x):
        print(x)
        aom.set_dispersion_correct(x, 0, 0)
    view.gvd_slider.valueChanged.connect(set_gvd)

    app.exec_()
