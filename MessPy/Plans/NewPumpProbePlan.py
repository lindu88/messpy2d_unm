from typing import Generator, Any, ClassVar
from attr import attrs, attrib
import numpy as np
from itertools import cycle
from functools import cached_property
from numpy.typing import NDArray

from .PlanBase import ScanPlan
from MessPy.Instruments.interfaces import ICam, IShutter, IRotationStage, IDelayLine
from PySide6.QtCore import Signal, QThread  # type: ignore
from typing import Optional


@attrs(kw_only=True, auto_attribs=True)
class NewPumpProbePlan(ScanPlan):
    shots: int
    t_points: NDArray[np.float64]
    cam: ICam

    delay_line: IDelayLine

    cur_t_idx: int = 0
    cur_wl_idx: int = 0
    rot_stage: Optional[IRotationStage] = None
    shutter_probe: Optional[IShutter] = None
    shutter_pump: Optional[IShutter] = None

    center_wavelengths: NDArray[np.float64] = np.array([0.0])
    reader_thread: Optional[QThread] = None
    sigStepDone: ClassVar[Signal] = Signal()

    @cached_property
    def angle_cycle(self) -> cycle:
        return cycle(self.center_wavelengths)

    @property
    def cur_t(self) -> float:
        return self.t_points[self.cur_t_idx]

    @property
    def cur_wl(self) -> float:
        return self.center_wavelengths[self.cur_wl_idx]

    def setup_plan(self) -> Generator:
        yield from super().setup_plan()
        if self.shutter_probe:
            self.shutter_probe.close()
        self.cam

    def move_rot_stage(self, angle: float) -> Generator[None, Any, None]:
        if self.rot_stage and len(self.center_wavelengths) > 1:
            self.rot_stage.set_degrees(angle)
            while self.rot_stage.is_moving():
                yield

    def move_delay_line(self, t: float) -> Generator[None, Any, None]:
        self.delay_line.set_pos(t, do_wait=False)
        while self.delay_line.moving:
            yield

    def pre_scan(self) -> Generator:
        yield from super().pre_scan()
        if self.rot_stage and len(self.center_wavelengths) > 1:
            self.rot_stage.set_degrees(self.center_wavelengths[self.cur_wl_idx])
            while self.rot_stage.is_moving():
                yield

    def scan(self) -> Generator:
        assert isinstance(self.cam, ICam)
        for self.cur_t_idx, t in enumerate(self.t_points):
            yield from self.move_delay_line(t)

            self.time_tracker.point_ending()
            self.sigStepDone.emit()

    def read_point(self):
        assert isinstance(self.cam, ICam)
        self.reader_thread = QThread(targ)
