import os
import threading, json
from typing import Optional, List, Iterable, TYPE_CHECKING, Generator, ClassVar

from loguru import logger
import numpy as np
from attr import Factory, attrib, attrs
from numpy._typing import NDArray
import h5py
import pandas as pd

from PyQt5.QtCore import QObject, pyqtSignal
from .PlanBase import Plan

if TYPE_CHECKING:
    from MessPy.ControlClasses import Controller, Cam
    from MessPy.Instruments.interfaces import ICam, IRotationStage, IShutter


@attrs(auto_attribs=True)
class PumpProbePlan(Plan):
    """Plan used for pump-probe experiments"""

    controller: "Controller"
    t_list: np.ndarray
    shots: int = 1000
    num_scans: int = 0
    t_idx: int = 0
    rot_idx: int = 0

    plan_shorthand: str = "PumpProbe"
    center_wl_list: List[List[float]] = [[0]]
    pump_shutter: Optional["IShutter"] = None
    cam_data: List["PumpProbeData"] = attrib(init=False)
    use_rot_stage: bool = False
    rot_stage_angles: Optional[list] = None
    rot_at_scan: List[float] = Factory(list)
    time_per_scan: str = ""
    do_ref_calib: bool = True
    probe_shutter: Optional["IShutter"] = None
    save_full_data: bool = False

    sigStepDone: ClassVar[pyqtSignal] = pyqtSignal()

    @property
    def common_mulitple_cwls(self):
        if len(self.center_wl_list) == 1:
            return 1
        else:
            return np.lcm(*map(len, self.center_wl_list))

    def __attrs_post_init__(self):
        super(PumpProbePlan, self).__attrs_post_init__()
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        self.angle_cycle = []
        self.cam_data = []
        self.pre_state = dict(
            shots=self.controller.cam.shots, delay=self.controller.delay_line.get_pos()
        )

        for c, cwl in zip(self.controller.cam_list, self.center_wl_list):
            self.cam_data.append(
                PumpProbeData(
                    cam=c,
                    cwl=cwl,
                    plan=self,
                    t_list=self.t_list,
                    save_full_data=self.save_full_data,
                )
            )

            c.set_shots(self.shots)

    def move_rot_stage(self, angle):
        if self.use_rot_stage:
            rs = self.controller.rot_stage
            if rs:
                rs.set_degrees(angle)
                while rs.is_moving():
                    rs.sigDegreesChanged.emit(rs.get_degrees())
                    yield

    def move_delay_line(self, t):
        self.controller.delay_line.set_pos(t, do_wait=False)
        while self.controller.delay_line.moving:
            yield

    def pre_scan(self) -> Generator:
        rs = self.controller.rot_stage
        if rs is not None:
            assert self.rot_stage_angles is not None
            yield from self.move_rot_stage(self.rot_stage_angles[self.rot_idx])
            self.rot_at_scan.append(rs.get_degrees())
        if self.probe_shutter:
            self.probe_shutter.close()
            for pp in self.cam_data:
                pp.cam.cam.get_background()
            self.probe_shutter.open()

        yield from self.move_delay_line(self.t_list[0] - 200)

    def scan(self) -> Generator:
        c = self.controller
        self.time_tracker.scan_starting()
        # -- scan
        if self.do_ref_calib and False:
            print("Calibrating Ref")
            print(f"At t={self.controller.delay_line.get_pos()}")
            self.cam_data[0].cam.cam.calibrate_ref()
        for self.t_idx, t in enumerate(self.t_list):
            yield from self.move_delay_line(t * 1000)
            if self.pump_shutter:
                self.pump_shutter.open()
            threads = []
            self.time_tracker.point_starting()
            for pp in self.cam_data:
                t = threading.Thread(target=pp.read_point, args=(self.t_idx,))
                t.start()
                threads.append(t)
            while any([t.is_alive() for t in threads]):
                yield
            for pp in self.cam_data:
                pp.sigStepDone.emit()

            if self.pump_shutter:
                self.pump_shutter.close()
            self.sigStepDone.emit()
            self.time_tracker.point_ending()
            yield
        self.time_tracker.scan_ending()

    def make_step_gen(self):
        c = self.controller
        rs = self.controller.rot_stage

        while True:
            yield from self.pre_scan()
            yield from self.scan()
            delta_t = self.time_tracker.scan_duration
            assert delta_t is not None
            self.time_per_scan = "%d:%02d" % (delta_t // 60, delta_t % 60)

            # --- post scans
            self.num_scans += 1
            self.controller.delay_line.set_pos(self.t_list[0], do_wait=False)
            for pp in self.cam_data:
                pp.post_scan()

            if self.use_rot_stage and (self.num_scans % self.common_mulitple_cwls == 0):
                assert self.rot_stage_angles is not None
                assert rs is not None
                self.rot_idx = (self.rot_idx + 1) % len(self.rot_stage_angles)
                rs.set_degrees(self.rot_stage_angles[self.rot_idx])

    def create_file(self):
        with self.data_file as f:
            for ppd in self.cam_data:
                f.create_dataset("wl_" + ppd.cam.name, data=ppd.wavelengths)
            f.create_dataset("t", data=self.t_list)
            f.create_dataset("rot", data=self.rot_at_scan)

    def save(self):
        logger.info(f"Saving to {self.data_file}")
        self.save_meta()

        with self.data_file as f:
            for ppd in self.cam_data:
                if (name := "data_" + ppd.cam.name) in f:
                    del f[name]
                    del f["rot"]
                f[name] = ppd.completed_scans
                f.create_dataset("rot", data=self.rot_at_scan)
            f.attrs["meta"] = json.dumps(self.meta)

    def restore_state(self):
        super().restore_state()
        # TODO: cam_list
        self.controller.cam.set_shots(self.pre_state["shots"])
        self.controller.delay_line.set_pos(self.pre_state["delay"], do_wait=False)

@attrs(auto_attribs=True)
class PumpProbeTasPlan(Plan):
    """Plan used for pump-probe experiments"""

    controller: "Controller"
    t_list: np.ndarray
    shots: int = 1000
    num_scans: int = 0
    t_idx: int = 0
    rot_idx: int = 0

    plan_shorthand: str = "PumpProbeTas"
    center_wl_list: List[List[float]] = [[0]]
    pump_shutter: Optional["IShutter"] = None
    cam_data: List["PumpProbeData"] = attrib(init=False)
    use_rot_stage: bool = False
    rot_stage_angles: Optional[list] = None
    rot_at_scan: List[float] = Factory(list)
    time_per_scan: str = ""
    do_ref_calib: bool = True
    probe_shutter: Optional["IShutter"] = None
    save_full_data: bool = False

    sigStepDone: ClassVar[pyqtSignal] = pyqtSignal()

    @property
    def common_mulitple_cwls(self):
        if len(self.center_wl_list) == 1:
            return 1
        else:
            return np.lcm(*map(len, self.center_wl_list))

    def __attrs_post_init__(self):
        super(PumpProbeTasPlan, self).__attrs_post_init__()
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        self.angle_cycle = []
        self.cam_data = []
        self.pre_state = dict(
            shots=self.controller.cam.shots, delay=self.controller.delay_line.get_pos()
        )
        for c, cwl in zip(self.controller.cam_list, self.center_wl_list):
            self.cam_data.append(
                PumpProbeData(
                    cam=c,
                    cwl=cwl,
                    plan=self,
                    t_list=self.t_list,
                    save_full_data=self.save_full_data,
                )
            )
            c.set_shots(self.shots)

    #no delay line for test
    def move_delay_line(self, t):
        #self.controller.delay_line.set_pos(t, do_wait=False)
        #while self.controller.delay_line.moving:
            #yield
        yield

    def pre_scan(self) -> Generator:
        rs = self.controller.rot_stage
        if rs is not None:
            assert self.rot_stage_angles is not None
            yield from self.move_rot_stage(self.rot_stage_angles[self.rot_idx])
            self.rot_at_scan.append(rs.get_degrees())
        if self.probe_shutter:
            self.probe_shutter.close()
            for pp in self.cam_data:
                pp.cam.cam.get_background()
            self.probe_shutter.open()

        yield from self.move_delay_line(self.t_list[0])

    def scan(self) -> Generator:
        c = self.controller
        self.time_tracker.scan_starting()
        # -- scan
        if self.do_ref_calib and False:
            print("Calibrating Ref")
            print(f"At t={self.controller.delay_line.get_pos()}")
            self.cam_data[0].cam.cam.calibrate_ref()
        for self.t_idx, t in enumerate(self.t_list):
            yield from self.move_delay_line(t * 1000)
            if self.pump_shutter:
                self.pump_shutter.open()
            threads = []
            self.time_tracker.point_starting()
            for pp in self.cam_data:
                t = threading.Thread(target=pp.read_point, args=(self.t_idx,))
                t.start()
                threads.append(t)
            while any([t.is_alive() for t in threads]):
                yield
            for pp in self.cam_data:
                pp.sigStepDone.emit()

            if self.pump_shutter:
                self.pump_shutter.close()
            self.sigStepDone.emit()
            self.time_tracker.point_ending()
            yield
        self.time_tracker.scan_ending()

    def make_step_gen(self):
        c = self.controller
        rs = self.controller.rot_stage

        while True:
            yield from self.pre_scan()
            yield from self.scan()
            delta_t = self.time_tracker.scan_duration
            assert delta_t is not None
            self.time_per_scan = "%d:%02d" % (delta_t // 60, delta_t % 60)

            # --- post scans
            self.num_scans += 1
            self.controller.delay_line.set_pos(self.t_list[0], do_wait=False)
            for pp in self.cam_data:
                pp.post_scan()

            if self.use_rot_stage and (self.num_scans % self.common_mulitple_cwls == 0):
                assert self.rot_stage_angles is not None
                assert rs is not None
                self.rot_idx = (self.rot_idx + 1) % len(self.rot_stage_angles)
                rs.set_degrees(self.rot_stage_angles[self.rot_idx])

    def create_file(self):
        with self.data_file as f:
            for ppd in self.cam_data:
                f.create_dataset("wl_" + ppd.cam.name, data=ppd.wavelengths)
            f.create_dataset("t", data=self.t_list)
            f.create_dataset("rot", data=self.rot_at_scan)

    def save(self):
        logger.info(f"Saving to {self.data_file}")
        self.save_meta()

        with self.data_file as f:
            for ppd in self.cam_data:
                if (name := "data_" + ppd.cam.name) in f:
                    del f[name]
                    del f["rot"]
                f[name] = ppd.completed_scans
                f.create_dataset("rot", data=self.rot_at_scan)
            f.attrs["meta"] = json.dumps(self.meta)

        #save csv -- avg of all scans as a wavelength / y data pair
        for idx, ppd in enumerate(self.cam_data):
            try:
                wavelengths = np.array(ppd.wavelengths).flatten()
                scans = np.array(ppd.completed_scans)  # shape: (scans, 1, times, 1, pixels)

                # Just averages all intensities for all results at pixel/wavelength even though for this test plan there is no time delay change
                avg_signal = scans.mean(axis=(0, 1, 2, 3)).flatten()

                if wavelengths.shape != avg_signal.shape:
                    raise ValueError("Wavelength/signal shape mismatch.")

                # Save with Pandas
                df = pd.DataFrame({
                    "Wavelength (nm)": wavelengths,
                    "Averaged Signal": avg_signal
                })

                base = os.path.splitext(self.data_file.filename)[0]
                csv_filename = f"{base}_cam{idx}_{ppd.cam.name.replace(' ', '_')}_avg.csv"

                df.to_csv(csv_filename, index=False)
                logger.info(f"Saved averaged signal CSV to {csv_filename}")

            except Exception as e:
                logger.error(f"Error saving averaged signal CSV for cam[{idx}]: {e}")

    def restore_state(self):
        super().restore_state()
        # TODO: cam_list
        self.controller.cam.set_shots(self.pre_state["shots"])
        self.controller.delay_line.set_pos(self.pre_state["delay"], do_wait=False)

@attrs(auto_attribs=True, cmp=False)
class PumpProbeData(QObject):
    """Class holding the pump-probe data for a single cam"""

    cam: "Cam"
    plan: PumpProbePlan
    cwl: List[float] = attrib()
    t_list: np.ndarray
    scan: int = 0
    delay_scans: int = 0
    wl_idx: int = 0
    t_idx: int = 0

    last_signal: Optional[np.ndarray] = None
    mean_signal: Optional[np.ndarray] = None
    current_scan: NDArray = attrib(init=False)
    mean_scans: Optional[np.ndarray] = None
    completed_scans: Optional[np.ndarray] = None
    wavelengths: np.ndarray = attrib(init=False)
    save_full_data: bool = False

    sigWavelengthChanged = pyqtSignal()
    sigStepDone = pyqtSignal()

    def __attrs_post_init__(self):
        super(PumpProbeData, self).__init__()
        num_sig = self.cam.sig_lines
        num_wl = len(self.cwl)
        num_t = len(self.t_list)
        num_ch = self.cam.channels
        self.wavelengths = np.zeros((num_wl, num_ch))
        for i, wl in enumerate(self.cwl):
            self.wavelengths[i, :] = self.cam.get_wavelengths(wl)
        self.current_scan = np.zeros((num_wl, num_t, num_sig, num_ch))
        self.mean_scans = None
        if self.cam.changeable_wavelength:
            self.cam.set_wavelength(self.cwl[0])

    def post_scan(self):
        "Called when a scan through the delay-line has finished"
        self.delay_scans += 1
        self.wl_idx = self.delay_scans % len(self.cwl)
        if self.delay_scans % len(self.cwl) == 0:
            self.scan += 1
            if self.completed_scans is None:
                self.completed_scans = self.current_scan[None, ...].copy()
                self.mean_scans = self.completed_scans[0, ...]
            else:
                self.completed_scans = np.concatenate(
                    (self.completed_scans, self.current_scan[None, ...])
                )
                self.mean_scans = self.completed_scans.mean(0)
            self.plan.save()
        next_wl = self.cwl[self.wl_idx]
        if len(self.cwl) > 1:
            self.cam.set_wavelength(next_wl)
        self.sigWavelengthChanged.emit()

    def read_point(self, t_idx):
        self.t_idx = t_idx
        self.cam.read_cam()
        lr = self.cam.last_read
        assert lr is not None
        if self.save_full_data:
            with self.plan.data_file as f:
                ds = f.create_dataset(
                    f"full_data/{self.cam.name}/scan_{self.scan}/t_{t_idx: 05d}",
                    data=lr.full_data.astype(np.float64),
                    compression="lzf",
                    chunks=(1, lr.full_data.shape[1], 20),
                    shuffle=True,
                    scaleoffset=2,
                )
        if np.shape(lr.signals)[0] == 1:
            self.current_scan[self.wl_idx, t_idx, :, :] = lr.signals[...]
        elif np.shape(lr.signals)[0] == 2:
            self.current_scan[self.wl_idx, t_idx, :, :] = lr.signals[0, :]
        else:
            print("Shape of lr.signal not matching current scan shape\n")
        if self.mean_scans is not None:
            self.mean_signal = self.mean_scans[self.wl_idx, t_idx, :, :]
        self.last_signal = lr.signals[:, :]
