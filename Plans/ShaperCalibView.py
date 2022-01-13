import asyncio
import matplotlib.pyplot as plt
from pyqtgraph.widgets.PlotWidget import PlotWidget
from qasync import asyncSlot
from qtpy.QtWidgets import (
    QWidget,
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QSpinBox,
    QLabel,
    QCheckBox,
    QDialogButtonBox,
    QSizePolicy,
    QSlider,
)
from qtpy.QtCore import Qt, Signal
from matplotlib.figure import Figure
from matplotlib import rcParams, style
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
import attr
import numpy as np
from scipy.constants import c
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d, gaussian_filter1d
from typing import Optional, ClassVar
from qtawesome import icon
from pyqtgraph.parametertree import Parameter, ParameterTree

import Instruments.interfaces
from Plans.ShaperCalibPlan import CalibPlan
from Config import config

rcParams["font.family"] = "Segoe UI"
style.use("dark_background")

@attr.s(auto_attribs=True)
class CalibScanView(QWidget):
    cam: Instruments.interfaces.ICam
    dac: Instruments.dac_px.AOM
    plan: Optional[CalibPlan] = None

    sigPlanCreated: ClassVar[Signal] = Signal(object)

    def __attrs_post_init__(self):
        super().__init__()
        self.setLayout(QHBoxLayout())

        self.children = [
            dict(name="Start Wavelength (nm)", type="int", value=5500, step=500),
            dict(name="End Wavelength (nm)", type="int", value=6500, step=500),
            dict(name="Step (nm)", type="float", value=10, step=2),
            dict(name="Shots", type="int", value=90, step=10),
            dict(name="Start Calibration", type="action"),
        ]
        param = Parameter.create(
            name="Calibration Scan", type="group", children=self.children
        )
        if (s := "CalibSettings") in config.exp_settings:
            param.restoreState(config.exp_settings[s],
                               addChildren=False, removeChildren=False)

        self.params: Parameter = param
        pt = ParameterTree()
        pt.setParameters(self.params)
        pt.setMaximumSize(300, 1000)

        self.layout().addWidget(pt)
        self.params.child("Start Calibration").sigActivated.connect(self.start)
        self.plot = PlotWidget(self)
        self.layout().addWidget(self.plot)
        self.info_label = QLabel()
        self.layout().addWidget(self.info_label)
        self.setMinimumSize(1200, 600)

    def start(self):
        s = self.params.saveState()
        config.exp_settings["CalibSettings"] = s
        start, stop, step = (
            self.params["Start Wavelength (nm)"],
            self.params["End Wavelength (nm)"],
            self.params["Step (nm)"],
        )
        config.save()

        self.plan = CalibPlan(
            cam=self.cam,
            dac=self.dac,
            points=np.arange(start, stop, step).tolist(),
            num_shots=self.params["Shots"],
        )
        self.sigPlanCreated.emit(self.plan)
        self.params.setReadonly(True)

        self.plan.sigPlanFinished.connect(self.analyse)
        self.plan.sigStepDone.connect(self.update_view)

    @asyncSlot()
    async def update_view(self):
        plan = self.plan

        self.plot.plotItem.clear()
        n = len(plan.amps)
        x = plan.points[:n]
        y = np.array(plan.amps)

        self.plot.plotItem.plot(x, y[:, 0], pen="r")
        self.plot.plotItem.plot(x, y[:, 1], pen="g")
        self.plot.plotItem.plot(x, y[:, 2], pen="y")

        self.info_label.setText(f'''
        Point {n}/{len(plan.points)}
        Channel {plan.channel}
        ''')

    def analyse(self):
        plan = self.plan
        x = np.array(plan.points)
        y_train = np.array(plan.amps)[:, 0]
        y_single = np.array(plan.amps)[:, 1]
        y_full = np.array(plan.amps)[:, 2]
        np.save("calib.npy", np.column_stack((x, y_train, y_single, y_full)))
        single_arr = np.column_stack((x[:, None], plan.single_spectra.T))
        np.save(f"wl_calib_{plan.channel}.npy", single_arr)
        self._view = CalibView(
            x=x,
            y_train=y_train - y_train.min(),
            y_single=y_single - y_single.min(),
            y_full=y_full - y_full.min(),
        )
        self._view.show()
        self._view.sigCalibrationAccepted.connect(plan.dac.set_calib)
        self._view.sigCalibrationAccepted.connect(
            lambda arg: plan.dac.generate_waveform()
        )


@attr.s(auto_attribs=True)
class CalibView(QWidget):
    x: np.ndarray
    y_train: np.ndarray
    y_single: np.ndarray
    y_full: Optional[np.ndarray] = None

    single: int = 15 * 500
    width: int = 150
    dist: int = 350

    prominence: float = 50
    distance: int = 3
    filter: float = 0

    coeff: Optional[np.ndarray] = None

    sigCalibrationAccepted = Signal(object)
    sigCalibrationCanceled = Signal()

    def __attrs_post_init__(self):
        super().__init__()
        dpi = self.logicalDpiX()
        self.setWindowTitle("Calibration")
        self.setWindowIcon(icon("fa5s.ruler-horizontal"))
        self.fig = Figure(dpi=dpi, constrained_layout=True)
        self.ax0, self.ax2 = self.fig.subplots(2)
        self.canvas = FigureCanvas(self.fig)

        self.setLayout(QVBoxLayout())

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.setContentsMargins(0, 0, 0, 0)
        self.canvas.setContentsMargins(0, 0, 0, 0)

        self.row = QHBoxLayout()
        self.sb_filter = QSpinBox()
        self.sb_filter.setValue(self.filter)
        self.sb_filter.valueChanged.connect(self.analyze)
        self.row.addWidget(QLabel("Filter"))
        self.row.addWidget(self.sb_filter)

        self.sb_dist = QSpinBox()
        self.sb_dist.setValue(self.distance)
        self.sb_dist.valueChanged.connect(self.analyze)
        self.sb_dist.setMinimum(1)

        self.row.addWidget(QLabel("Peak distance"))
        self.row.addWidget(self.sb_dist)

        self.sb_prom = QSpinBox()
        self.sb_prom.setMaximum(20000)
        self.sb_prom.setValue(self.prominence)
        self.sb_prom.valueChanged.connect(self.analyze)
        self.row.addWidget(QLabel("Peak prominance"))
        self.row.addWidget(self.sb_prom)

        self.use_norm = QCheckBox("Normalize")
        self.use_norm.setChecked(True)
        self.use_norm.toggled.connect(self.analyze)
        self.row.addWidget(self.use_norm)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.row.addWidget(bb)
        # bb.setFixedWidth(400)
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

            y_train = gaussian_filter1d(self.y_train, self.filter)
            y_single = gaussian_filter1d(self.y_single, self.filter)
            y_full = gaussian_filter1d(self.y_full, self.filter)
        else:
            y_train, y_single, y_full = self.y_train, self.y_single, self.y_full
        if self.use_norm.isChecked():
            y_train = 500 * (y_train / (y_full + 50))
            y_single = 500 * (y_single / (y_full + 50))

        p0, _ = find_peaks(y_train, prominence=self.prominence, distance=self.distance)
        p1, _ = find_peaks(y_single, prominence=self.prominence, distance=self.distance)

        self.ax0.cla()
        self.ax2.cla()
        self.ax0.plot(self.x, y_train)
        self.ax0.plot(self.x, y_single)
        if self.y_full is not None and not self.use_norm.isChecked():
            self.ax0.plot(self.x, y_full)
        ax1 = self.ax2
        x = self.x
        self.ax0.plot(self.x[p0], y_train[p0], "|", ms=7, c="r")
        self.ax0.plot(self.x[p1], y_single[p1], "^", ms=7, c="r")

        if len(p0) > 1 and len(p1) == 1:
            a = np.arange(0, 4096 * 3, self.width + self.dist)
            align = np.argmin(abs(x[p0] - x[p1]))
            pix0 = self.single + self.width / 2
            pixel = a[: len(p0)] - a[align] + pix0

            freqs = c / x[p0] / 1e3
            freq0 = c / x[p1] / 1e3

            ax1.plot(pix0, freq0, marker="o", ms=10)
            ax1.set_xlabel("Pixel")
            ax1.set_ylabel("Freq / THz")
            self.ax0.set(xlabel="Wavelength / nm", ylabel="Counts")

            ax1.plot(pixel, freqs, marker="x", ms=10)
            all_pix = np.arange(pixel.min(), pixel.max())
            self.coeff = np.polyfit(pixel, freqs, 2)
            fit = np.polyval(self.coeff, all_pix)
            txt = "".join(["%.3e\n" % i for i in self.coeff])
            ax1.annotate(
                txt, (0.95, 0.93), xycoords="axes fraction", va="top", ha="right"
            )
            ax1.plot(all_pix, fit, color="xkcd:lime")

            self.fig.canvas.draw_idle()


if __name__ == "__main__":
    from Instruments.dac_px import AOM

    aom = AOM()
    app = QApplication([])
    # from qt_material import apply_stylesheet
    # apply_stylesheet(app, 'light_blue.xml')
    x, y_train, y_single, y_full = np.load("calib.npy").T
    y_single -= y_single.min()
    y_train -= y_train.min()
    y_full -= y_full.min()
    view = CalibView(x=x, y_single=y_single, y_train=y_train, y_full=y_full)
    view.show()
    view.sigCalibrationAccepted.connect(aom.set_calib)
    view.sigCalibrationAccepted.connect(
        lambda x: aom.generate_waveform(np.ones_like(aom.nu), np.ones_like(aom.nu))
    )

    def set_gvd(x):

        aom.gvd = x
        aom.update_dispersion_compensation()

    view.gvd_slider.valueChanged.connect(set_gvd)

    app.exec_()
