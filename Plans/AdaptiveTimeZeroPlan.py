import asyncio
from typing import Literal, List, Dict, ClassVar

import numpy as np
import attr
from qtpy.QtCore import Signal

from ControlClasses import Cam, DelayLine

from Plans.PlanBase import Plan
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


@attr.s(auto_attribs=True)
class AdaptiveTimeZeroPlan(Plan):
    cam: Cam
    delay_line: DelayLine
    mode: Literal['mean', 'max'] = 'mean'
    is_running: bool = True
    max_diff: float = 50
    stop: float = 10
    current_step: float = 1
    min_step: float = 0.05
    plan_shorthand: ClassVar[str] = 'AutoZero'
    is_async:  bool = True
    positions: Dict[float, float] = attr.Factory(dict)

    sigStepDone: ClassVar[Signal] = Signal()

    async def step(self):
        dl = self.delay_line
        cam = self.cam
        start_pos = dl.get_pos()
        cur_signal = await self.read_point()
        self.sigPlanStarted.emit()

        while self.is_running:
            cur_pos = dl.get_pos()
            new_signal = await self.read_point()
            self.positions[cur_pos] = new_signal
            self.sigStepDone.emit()

            if abs(new_signal-cur_signal) > self.max_diff:
                self.current_step = max(0.5*self.current_step, self.min_step)
                next_pos = cur_pos - self.current_step
            else:
                next_pos = cur_pos + self.current_step
            await self.move_dl(next_pos)
            if next_pos > self.stop:
                self.is_running = False
        self.sigPlanFinished.emit()

    async def read_point(self):
        loop = asyncio.get_running_loop()
        reading = await loop.run_in_executor(None, self.cam.make_reading)
        return np.mean(reading.signal[2])

    async def move_dl(self, pos):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.delay_line.set_pos, 1000*pos, True)

    def get_data(self):
        x, y = self.positions.items()
        xa, ya = np.array(x), np.array(y)
        i = np.argsort(xa)
        xa = xa[i]
        ya = ya[i]
        return xa, ya


