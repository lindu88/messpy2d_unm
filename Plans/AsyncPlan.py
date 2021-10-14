import asyncio
import asyncio as aio
import sys

import attr

sys.path.append('../')
from Instruments.interfaces import ICam

from typing import List, Callable, Tuple
from qasync import QEventLoop, asyncSlot
from qtpy.QtWidgets import *
from qtpy.QtCore import QObject, Signal
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
import numpy as np
from .CalibView import CalibView

@attr.s(auto_attribs=True, cmp=False)
class CalibPlan(QObject):
    cam: ICam
    move_func: Callable
    points: List[float]
    amps: List[List[float]] = attr.Factory(list)
    start_pos: Tuple[float, float] = 0
    check_zero_order: bool = True
    channel: int = 67
    sigStepDone = Signal()
    sigPlanDone = Signal()

    def __attrs_post_init__(self):
        super().__init__()

    async def step(self):
        loop = asyncio.get_running_loop()
        if self.check_zero_order:
            self.cam.set_wavelength(0, 10)  #
            reading = await loop.run_in_executor(None, self.cam.make_reading)

        await self.pre_scan()
        for p in self.points:
            await self.read_point(p)
            self.sigStepDone.emit()

        await self.post_scan()

    async def pre_scan(self):
        self.cam.set_wavelength(self.start_pos, 10)

    async def post_scan(self):
        self.sigPlanDone.emit()

    async def read_point(self, p):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.cam.set_wavelength, p, 10)

        #while self.sample_scanner.is_moving():
        #    await aio.sleep(0.01)

        spectra, ch = await loop.run_in_executor(None, self.cam.get_spectra, 3)
        print(spectra['Probe2'].frame_data.shape)
        self.amps.append(spectra['Probe2'].frame_data[67, :])




class FocusScanView(QWidget):
    def __init__(self, focus_scan: CalibPlan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info_label = QLabel('BLa')
        self.focus_scan = focus_scan
        self.focus_scan.sigStepDone.connect(self.update_view)

        self.setLayout(QHBoxLayout())
        self.start_button = QPushButton('start')
        self.layout().addWidget(self.info_label)
        self.layout().addWidget(self.start_button)


        self.children = [
            dict(name='start_wl', type='int', value=5000, step=500),
            dict(name='end_wl', type='int',  value=7000, step=500),
            dict(name='step', type='float',  value=20, step=2),
        ]
        param = Parameter.create(name='Calibration Scan',
                                type='group',
                                children=self.children)
        for c in param.children():
            c.setDefault(c.value())

        self.children2 = [
            dict(name='Height', type='float', value=100000),
            dict(name='Distance', type='float', value=5),

        ]
        param2 = Parameter.create(name='Calibration Scan',
                            type='group',
                            children=self.children2)
        self.params : Parameter = param
        self.pt = ParameterTree()
        self.pt.setParameters(self.params)
        self.layout().addWidget(self.pt)
        self.start_button.clicked.connect(self.start)
        self.plot = pg.PlotWidget(self)
        self.layout().addWidget(self.plot)
        self.focus_scan.sigPlanDone.connect(self.analyse)
        self.focus_scan.sigPlanDone.connect(
            lambda: self.start_button.setEnabled(True))

    def start(self):
        s = self.params.saveState()
        start, stop, step = self.params['start_wl'], self.params['end_wl'], self.params['step']
        self.focus_scan.points = np.arange(start, stop, step)
        self.params.setReadonly(True)

        self.start_button.setDisabled(True)
        loop = aio.get_event_loop()
        loop.create_task(self.focus_scan.step())

    @asyncSlot()
    async def update_view(self):
        print('update')
        plan = self.focus_scan
        #self.info_label.setText(str(plan.amps[-1]))
        self.plot.plotItem.clear()
        n = len(plan.amps)
        x = plan.points[:n]

        y = np.array(plan.amps)
        print(y.shape)
        self.plot.plotItem.plot(x, y[:, 1], pen='r')
        self.plot.plotItem.plot(x, y[:, 0], pen='g')
        self.plot.plotItem.plot(x, y[:, 2], pen='y')

    def analyse(self):
        plan = self.focus_scan
        x = np.array(plan.points)
        y0 = np.array(plan.amps)[:, 0]
        y1 = np.array(plan.amps)[:, 1]
        y2 = np.array(plan.amps)[:, 2]
        np.save('calib.npy', np.column_stack((x, y1, y2)))
        self._view = CalibView(x=x, y1=y2, y0=y1, y2=y2)
        self._view.show()

    from Instruments.cam_phasetec import _ircam

    app = QApplication([])
    loop = QEventLoop(app)
    aio.set_event_loop(loop)
    cam = _ircam
    cam.set_shots(60)
    fs = CalibPlan(cam=cam,
                   move_func=cam.set_wavelength,
                   points=np.arange(5500, 6500, 5))
    fv = FocusScanView(fs)
    fv.show()
    app.exec()
