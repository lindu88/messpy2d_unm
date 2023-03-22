import threading
import typing as T

import attr
import numpy as np
import scipy.optimize as opt
import scipy.special as spec
from qtpy.QtCore import Signal

from MessPy.ControlClasses import Cam
from MessPy.Instruments.interfaces import ILissajousScanner, IPowerMeter
from MessPy.Plans.PlanBase import Plan


def gauss_int(x, x0, amp, back, w):
    return 0.5 * amp * (1 + spec.erf(np.sqrt(2) * (x - x0) / w)) + back


@attr.dataclass
class FitResult:
    name: str
    success: bool
    params: np.ndarray
    pos: np.ndarray
    data: np.ndarray
    model: np.ndarray

    def make_text(self):
        text = '%s\nBeamwaist: %2.3f mm \n 1/e: %2.3f mm \nFWHM %2.3f mm\nPOS %2.2f' % (
            self.name, self.params[-1], 0.59 * self.params[-1], 0.64 * self.params[-1], self.params[0])
        return text

    @classmethod
    def fit_curve(cls, pos, val, name):

        pos = np.array(pos)
        idx = np.argsort(pos)
        val = np.array(val)[idx]
        pos = pos[idx]
        a = val[np.argmax(pos)]
        b = val[np.argmin(pos)]
        x0 = [pos[np.argmin(np.abs(val - (a + b) / 2))], a - b, b, 0.1]


        def helper(p):
            return np.array(val) - gauss_int(pos, *p)

        res = opt.least_squares(helper, x0)
        fit = gauss_int(pos, *res.x)
        print(res.x)
        return cls(success=res.status > 0, params=res.x, model=fit, name=name, data=val, pos=pos)


@attr.define
class Scan:
    axis: str
    start: float
    end: float
    step: float
    pos: list[float] = attr.Factory(list)
    probe: list[float] = attr.Factory(list)
    ref: list[float] = attr.Factory(list)
    extra: list[float] = attr.Factory(list)
    full: list[np.ndarray] = attr.Factory(list)
    min_step: float = 0.005
    max_diff: float = 0.1

    def analyze(self):
        fit_probe = FitResult.fit_curve(self.pos, self.probe, f'{self.axis} probe')
        fit_ref = FitResult.fit_curve(self.pos, self.ref, f'{self.axis} ref')
        if len(self.extra) > 0:
            fit_extra = FitResult.fit_curve(self.pos, self.extra, f'{self.axis} PW')
        else:
            fit_extra = None
        return fit_probe, fit_ref, fit_extra

    def scan(self, mover, reader):
        sign = np.sign(self.end-self.start)
        for x0 in np.arange(self.start, self.end, sign*self.step):
            yield from self.check_point(x0, reader, mover)
        while (x0 := self.check_for_holes()):
            yield from self.check_point(x0, reader, mover)

    def check_point(self, x, reader, mover):
        yield from mover(x)
        for data, lines, pw in reader():
            yield
        self.pos.append(x)
        self.probe.append(data[0])
        if pw is not None:
            self.extra.append(pw)
        self.ref.append(data[1])
        self.full.append(lines)

    def get_data(self):
        idx = np.argsort(self.pos)
        p, pr, ref = np.array(self.pos)[idx], np.array(self.probe)[idx], np.array(self.ref)[idx]
        if self.extra:
            ex = np.array(self.extra)[idx]
        else:
            ex = None
        return p, pr, ref, ex

    def check_for_holes(self):
        x, y = self.get_data()[:2]
        xd = np.diff(x)
        yd = np.diff(y)/y.ptp()
        i = (np.abs(yd) > self.max_diff) & (xd > self.min_step)
        if np.any(i):
            first = np.argmax(i)
            return (x[first+1]+x[first])/2
        else:
            return False

@attr.s(auto_attribs=True, eq=False)
class FocusScan(Plan):
    """
    x_parameters and y_parameters are List [start, end, step];
    if list empty it is not measured
    """
    cam: Cam
    fh: ILissajousScanner
    plan_shorthand: T.ClassVar[str] = "FocusScan"
    x_parameters: T.Optional[list]
    y_parameters: T.Optional[list]
    z_points: T.Optional[list] = None
    shots: int = 100
    sigStepDone: T.ClassVar[Signal] = Signal()
    sigFitDone: T.ClassVar[Signal] = Signal()

    scan_x: T.Optional[Scan] = None
    scan_y: T.Optional[Scan] = None
    power_meter: T.Optional[IPowerMeter] = None

    def __attrs_post_init__(self):
        super(FocusScan, self).__attrs_post_init__()
        if self.x_parameters:
            self.scan_x = self.make_x_scan()
        if self.y_parameters:
            self.scan_y = self.make_y_scan()
        self.start_pos = (0, 0)  # self.fh.pos_home
        gen = self.make_scan_gen()
        self.make_step = lambda: next(gen)
        self.cam.set_shots(self.shots)
        if self.z_points is None:
            self.z_points = [self.fh.get_zpos_mm()]

    def make_x_scan(self):
        return Scan(axis='x',
                    start=self.x_parameters[0],
                    end=self.x_parameters[1],
                    step=self.x_parameters[2],
                    )

    def make_y_scan(self):
        return Scan(axis='y',
                    start=self.y_parameters[0],
                    end=self.y_parameters[1],
                    step=self.y_parameters[2],
                    )

    def make_scan_gen(self):
        for z_pos in self.z_points:
            self.fh.set_pos_mm(*self.start_pos)
            self.fh.set_zpos_mm(z_pos)
            while any(self.fh.is_moving()):
                yield
            if self.scan_x:
                for _ in self.scan_x.scan(lambda x: self.mover("x", x), self.reader):
                    self.sigStepDone.emit()
                    yield
            self.fh.set_pos_mm(*self.start_pos)
            if self.scan_y:
                for _ in self.scan_y.scan(lambda x: self.mover("y", x), self.reader):
                    self.sigStepDone.emit()
                    yield

            self.fh.set_pos_mm(*self.start_pos)
            self.sigFitDone.emit()
        self.sigPlanFinished.emit()
        yield

    def mover(self, axis, pos):
        if axis == 'x':
            self.fh.set_pos_mm(self.start_pos[0] + pos, None)
        if axis == 'y':
            self.fh.set_pos_mm(None, self.start_pos[1] + pos)
        while any(self.fh.is_moving()):
            yield
        yield

    def reader(self):
        t = threading.Thread(target=self.cam.read_cam)
        t.start()
        if self.power_meter is not None:
            f = self.power_meter.read_power()
        else:
            f = None
        while t.is_alive():
            yield False, None, None
        yield self.cam.last_read.lines.mean(1), self.cam.last_read.lines, f

    def save(self):
        name = self.get_file_name()[0]
        self.save_meta()
        data: dict[str, object] = {'cam': self.cam.name}

        if sx := self.scan_x:
            data['scan x'] = np.vstack((sx.pos, sx.probe, sx.ref))
            data['full x'] = np.array(sx.full)
            if len(sx.extra) > 0:
                data['extra x'] = sx.extra
        if sx := self.scan_y:
            data['scan y'] = np.vstack((sx.pos, sx.probe, sx.ref))
            data['full y'] = np.array(sx.full)
            if len(sx.extra) > 0:
                data['extra y'] = sx.extra

        np.savez(name, **data)
