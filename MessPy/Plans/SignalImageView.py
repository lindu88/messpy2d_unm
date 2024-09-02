import numpy as np
import pyqtgraph.parametertree as pt
from pyqtgraph import ImageItem, PlotWidget, InfiniteLine

from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QCheckBox, QWidget, QLabel, QSpinBox
from qtawesome import icon

from MessPy.ControlClasses import Controller
from MessPy.QtHelpers import PlanStartDialog, vlay, hlay
from .SignalImagePlan import SignalImagePlan


class SignalImageView(QWidget):
    def __init__(self, si_plan: SignalImagePlan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = si_plan

        self.signal_index = 0
        self.signal_selector = QSpinBox()
        self.signal_selector.setRange(0, self.plan.cam.sig_lines - 1)
        self.signal_selector.valueChanged.connect(self.update_view)

        self.ch_index = 0
        self.ch_selector = QSpinBox()
        self.ch_selector.setRange(0, self.plan.cam.channels - 1)
        self.ch_selector.valueChanged.connect(self.update_view)

        

        self.cb_use_wavenumbers = QCheckBox("Use wavenumbers")

        self.line_plot = PlotWidget()
        self.ch_line = InfiniteLine(angle=0)
        self.line_plot.addItem(self.ch_line)
        self.ch_line.setPos(plan.)
        self.image = ImageItem()
        self.image_plot = PlotWidget()
        self.image_plot.setAspectLocked(True)
        self.image_plot.addItem(self.image)
        self.info_label = QLabel("Info")
        controls = hlay(self.signal_selector, self.ch_selector, self.cb_use_wavenumbers)
        self.setLayout(vlay(controls, self.line_plot, self.image_plot, self.info_label))
        self.plan.sigPointRead.connect(
            self.update_view, type=Qt.ConnectionType.QueuedConnection
        )
        self.setWindowTitle("image Scan")
        self.setWindowIcon(icon("fa5s.tired"))

    @Slot()
    def update_view(self):
        self.ch_index = self.ch_selector.value()
        self.signal_index = self.signal_selector.value()
        self.update_label()
        self.update_plot()
        self.update_image()

    def update_label(self):
        p = self.plan
        s = f"Scan {p.cur_scan}"
        self.info_label.setText(s)

    def update_plot(self):
        p = self.plan
        self.line_plot.clear()

        x = p.wavelengths
        if self.cb_use_wavenumbers.isChecked():
            x = 1e7 / x
        self.line_plot.plot(p.wavelengths, p.cur_signal.signals[self.signal_index, :])

    @Slot()
    def update_image(self):
        p = self.plan
        col = p.cur_image[..., self.signal_index, self.ch_index]
        self.image.setImage(col, autoLevels=True)
        self.image_plot.setXRange(0, p.positions.shape[1])
        self.image_plot.setYRange(0, p.positions.shape[0])


class SignalImageStarter(PlanStartDialog):
    experiment_type = "Signal Image Scan"
    title = "Signal Image Scan"
    viewer = SignalImageView

    def setup_paras(self):
        tmp = [
            {"name": "Filename", "type": "str", "value": "temp_signal_image"},
            {"name": "Shots", "type": "int", "max": 2000, "value": 100},
            {"name": "Resolution / mm", "type": "float", "value": 0.1, "step": 0.05},
            {"name": "Square width / mm", "type": "float", "value": 0.1, "step": 0.05},
        ]
        self.p = pt.Parameter.create(name="Exp. Settings", type="group", children=tmp)
        params = [self.p]
        self.paras = pt.Parameter.create(
            name="Focus Scan", type="group", children=params
        )

    def create_plan(self, controller: Controller):
        assert controller.sample_holder is not None
        p = self.paras.child("Exp. Settings")
        self.save_defaults()
        shots = p.child("Shots").value()
        res = p.child("Resolution / mm").value()
        width = p.child("Square width / mm").value()
        square_positions = np.arange(-width / 2, width / 2, res)
        starting_pos = controller.sample_holder.get_pos_mm()
        X, Y = np.meshgrid(square_positions, square_positions)
        X += starting_pos[0]
        Y += starting_pos[1]
        positions = np.dstack((X, Y))

        fs = SignalImagePlan(
            cam=controller.cam.cam,
            wavelengths=controller.cam.wavelengths,
            xy_stage=controller.sample_holder,
            positions=positions,
            shots=shots,
            name=p.child("Filename").value(),
        )

        return fs
