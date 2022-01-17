import asyncio
from typing import Literal, List, Dict, ClassVar

import numpy as np
import attr
from qtpy.QtCore import Signal

from ControlClasses import Cam, DelayLine

from Plans.PlanBase import AsyncPlan
from scipy.special import erf
import lmfit
from lmfit.model import ModelResult

@attr.s(auto_attribs=True)
class StepFitResult:
    success: bool
    params: object
    model: np.ndarray


def gaussian_step(x, x0, amp, back, sigma):
    return 0.5 * (1 + amp * erf((x - x0) / (sigma * 2))) - back


def fit_step_function(t, data) -> ModelResult:
    a = data[np.argmax(t)]
    b = data[np.argmin(t)]
    t0 = t[np.argmin(np.abs(data - (a - b) / 2))]
    sigma = 0.1
    step_amp = a-b
    back = b

    model = lmfit.Model(gaussian_step)
    fit_result = model.fit(data, x=t, amp=step_amp, back=back, sigma=sigma)
    return fit_result


@attr.s(auto_attribs=True, kw_only=True)
class AdaptiveTimeZeroPlan(AsyncPlan):
    cam: Cam
    delay_line: DelayLine
    mode: Literal['mean', 'max'] = 'mean'
    is_running: bool = True
    min_diff: float = 1
    max_diff: float = 4
    start: float = -5
    stop: float = 5
    current_step: float = 0.2
    shots: int = 100
    min_step: float = 0.05
    plan_shorthand: ClassVar[str] = 'AutoZero'
    is_async:  bool = True
    positions: list[float] = attr.Factory(list)
    values: list[float] = attr.Factory(list)

    sigStepDone: ClassVar[Signal] = Signal(object)

    async def plan(self):
        dl = self.delay_line
        await self.move_dl(self.start)
        cam = self.cam
        start_pos = dl.get_pos()/1000.
        self.cam.set_shots(self.shots)
        cur_signal = await self.read_point()
        self.sigPlanStarted.emit()

        while self.is_running:
            cur_pos = dl.get_pos()/1000.
            new_signal = await self.read_point()
            self.values.append(new_signal)
            self.positions.append(cur_pos)
            self.sigStepDone.emit(self.get_data())
            cam.sigReadCompleted.emit()
            sig_diff = abs(new_signal-cur_signal)
            cur_signal = new_signal
            if sig_diff > self.max_diff and self.current_step != self.min_step:
                self.current_step = max(0.5*self.current_step, self.min_step)
                next_pos = cur_pos - self.current_step
            elif sig_diff < self.min_diff:
                self.current_step = min(2 * self.current_step, 10)
                next_pos = cur_pos + self.current_step
            else:
                next_pos = cur_pos + self.current_step
            await self.move_dl(next_pos)
            if next_pos > self.stop:
                await self.check_pos(self.stop)
                while (new_x := self.check_for_holes()) and self.is_running:
                    await self.check_pos(new_x)
                self.is_running = False
        self.sigPlanFinished.emit()

    def check_for_holes(self):
        x, y = self.get_data()
        xd = np.diff(x)
        yd = np.diff(y)
        i = (np.abs(yd) > self.max_diff) #& (xd > self.min_step)
        if np.any(i):
            first = np.argmax(i)
            return (x[first+1]+x[first])/2
        else:
            return False

    async def read_point(self):
        loop = asyncio.get_running_loop()
        reading = await loop.run_in_executor(None, self.cam.cam.make_reading)
        return np.mean(reading.signals[0])

    async def check_pos(self, pos):
        await self.move_dl(pos)
        new_signal = await self.read_point()
        self.values.append(new_signal)
        self.positions.append(pos)
        self.sigStepDone.emit(self.get_data())

    async def move_dl(self, pos):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.delay_line.set_pos, 1000*pos, True)

    def get_data(self):
        x, y = self.positions, self.values
        xa, ya = np.array(x), np.array(y)
        i = np.argsort(xa)
        xa = xa[i]
        ya = ya[i]
        return xa, ya
