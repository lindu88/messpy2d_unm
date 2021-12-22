from typing import TYPE_CHECKING, ClassVar, Callable

import numpy as np
from attr import attrs, attrib

from ControlClasses import Controller
from .common_meta import Plan

if TYPE_CHECKING:
    pass
from Instruments.dac_px import AOM

# from qtpy.QtWidgets import QApplication
from Instruments.signal_processing import cm2THz
from qtpy.QtCore import Signal
import h5py

from typing import Optional

@attrs(auto_attribs=True, kw_only=True)
class AOMTwoDPlan(Plan):
    """Plan used for pump-probe experiments"""
    plan_shorthand: ClassVar[str] = "2D"
    controller: Controller
    shaper: AOM
    t3_list: np.ndarray
    max_t2: float = 4
    step_t2: float = 0.05
    t2: np.ndarray = attrib()
    rot_frame_freq: float = 0
    time_per_scan: float = 0
    data_file: h5py.File = attrib()
    inferogramm_data: np.ndarray = attrib()
    last_data: Optional[np.ndarray] = None
    sigStepDone: ClassVar[Signal] = Signal()
    make_step: Callable = attrib()

    @t2.default
    def _t2_default(self):
        return np.arange(0, self.max_t2 + 1e-3, self.step_t2)

    @data_file.default
    def _default_file(self):
        name = self.get_file_name()[0]
        f = h5py.File(name, mode='w')
        f.create_dataset("t2", data=self.t2)
        f.create_dataset("t3", data=self.t3_list)
        f.create_group("data")
        f['t2'].attrs['rot_frame'] = self.rot_frame_freq
        return f

    @inferogramm_data.default
    def _default_store(self):
        return np.zeros((self.controller.cam.channels, len(self.t2) * 2, len(self.t3_list)))

    @make_step.default
    def _tmp(self):
        return self.make_step_gen().__next__

    def make_step_gen(self):
        c = self.controller
        self.setup_shaper()
        for self.t3_idx, self.t3 in enumerate(self.t3_list):
            c.delay_line.set_pos(self.t3, do_wait=False)
            while c.delay_line.moving:
                yield
            yield from self.measure_point()
            self.sigStepDone.emit()

    def setup_shaper(self):
        print(cm2THz(self.rot_frame_freq))
        amp, phase = self.shaper.double_pulse(self.t2, cm2THz(self.rot_frame_freq))
        #amp[:, ::4] *= 0
        self.shaper.set_amp_and_phase(amp, phase)

        self.shaper.chopped = False
        self.shaper.phase_cycle = False
        self.shaper.do_dispersion_compensation = True
        self.shaper.generate_waveform()
        self.controller.cam.set_shots(amp.shape[1])

    def measure_point(self):
        # t = threading.Thread(target=self.controller.cam.cam.make_2D_reading,
        #                     args=(self.t2, self.rot_frame_freq))
        # t.start()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.controller.cam.cam.make_2D_reading, self.t2, self.rot_frame_freq)
            while not future.done():
                yield
            ret = future.result()
        for line, data in ret.items():
            self.data_file.create_dataset(f'if_data/{line}/{self.t3_idx}', data=data.interferogram)
            self.data_file.create_dataset(f'2d_data/{line}/{self.t3_idx}', data=data.signal_2D)

        self.last_2d = data.signal_2D
        self.last_ir = data.interferogram
        tmp = np.save(data.spectra.frame_data)
        self.last_freq = data.freqs
