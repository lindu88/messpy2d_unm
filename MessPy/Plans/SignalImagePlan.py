import concurrent
import concurrent.futures

from attr import define, attrib
from PySide6.QtCore import Signal

from MessPy.Config import config
from MessPy.ControlClasses import Cam, Reading
from MessPy.Instruments.interfaces import ICam, ILissajousScanner
from MessPy.Plans.PlanBase import ScanPlan

import numpy as np
from typing import ClassVar


@define(auto_attribs=True, slots=False)
class SignalImagePlan(ScanPlan):
    cam: ICam
    xy_stage: ILissajousScanner
    positions: np.ndarray
    wavelengths: np.ndarray

    cur_image: np.ndarray = attrib(init=False)
    mean_image: np.ndarray = attrib(init=False)
    all_images: np.ndarray = attrib(init=False)

    cur_signal: Reading = attrib(init=False)
    shots: int = 150
    plan_shorthand: ClassVar[str] = "SignalImage"
    sigPointRead: ClassVar[Signal] = Signal()

    def setup_plan(self):
        image_shape = (
            self.positions.shape[0],
            self.positions.shape[1],
            self.cam.sig_lines,
            self.cam.channels,
        )
        self.cur_image = np.zeros(image_shape)
        self.cam.set_shots(self.shots)
        self.xy_stage.set_pos_mm(self.positions.flat[0])
        yield

    def scan(self):
        x_pos = self.positions[..., 0]
        y_pos = self.positions[..., 1]
        for ix, x in enumerate(x_pos[0, :]):
            for iy, y in enumerate(y_pos[:, 0]):
                self.time_tracker.point_starting()
                self.xy_stage.set_pos_mm(x, y)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self.cam.make_reading)
                while not future.done():
                    yield
                self.cur_signal = future.result()
                self.cur_image[iy, ix, :, :] = self.cur_signal.signals
                self.sigPointRead.emit()
                self.time_tracker.point_ending()
                yield

    def post_plan(self):
        if self.cur_scan == 0:
            self.all_images = self.cur_image[None, :, :]
        else:
            self.all_images = np.append(
                self.all_images, self.cur_image[None, :, :], axis=0
            )
        self.cur_image = np.zeros_like(self.cur_image)
        self.mean_image = np.mean(self.all_images, 0)

        fname = self.get_file_name()[0]
        np.savez(fname, data=self.all_images, positions=self.positions)

        yield
