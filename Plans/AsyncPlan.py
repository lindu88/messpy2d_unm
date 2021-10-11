import asyncio
import asyncio as aio
import attr
#from PyQt5.QtWidgets import QWidget
import os, sys

os.environ['QT_API'] = 'PyQt5'
sys.path.append('../')
from Instruments.interfaces import ILissajousScanner, ICam, IDelayLine
from typing import List, Callable, Tuple
from qasync import QEventLoop, asyncClose, asyncSlot
from qtpy.QtWidgets import *
from qtpy.QtCore import QObject, Signal
import pyqtgraph as pg
import numpy as np

@attr.s(auto_attribs=True, cmp=False)
class FocusScan(QObject):
    cam: ICam
    move_func: Callable
    points: List[float]
    amps: List[List[float]] = attr.Factory(list)
    start_pos: Tuple[float, float] = 0

    sigStepDone = Signal()
    sigPlanDone = Signal()

    def __attrs_post_init__(self):
        super().__init__()

    async def step(self):
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

        reading = await loop.run_in_executor(None, self.cam.make_reading)
        self.amps.append(reading.frame_data[:, 67])



class FocusScanView(QWidget):
    def __init__(self, focus_scan: FocusScan, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.info_label = QLabel('BLa')
        self.focus_scan = focus_scan        
        self.focus_scan.sigStepDone.connect(self.update_view)
        self.setLayout(QHBoxLayout())
        self.start_button = QPushButton('start')
        self.layout().addWidget(self.info_label)
        self.layout().addWidget(self.start_button)
        self.start_button.clicked.connect(self.start)
        self.plot = pg.PlotWidget(self)
        self.layout().addWidget(self.plot)
        self.focus_scan.sigPlanDone.connect(self.analyse)

    def start(self):
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
        self.plot.plotItem.plot(x, np.array(plan.amps)[:, 1], pen='r')
        self.plot.plotItem.plot(x, np.array(plan.amps)[:, 0], pen='g')

    def analyse(self):
        plan = self.focus_scan
        x = np.array(plan.points)
        y1 = np.array(plan.amps)[:, 1]
        y2 = np.array(plan.amps)[:, 0]
        np.save('calib.npy' ,np.column_stack((x, y1, y2)))
        from scipy.signal import find_peaks
        p1, _ = find_peaks(y1, height=4000, distance=5)
        p2, _ = find_peaks(y1, height=4000, distance=5)
        self.plot.plotItem.plot(x[p1], y1[p1])
        self.plot.plotItem.plot(x[p2], y2[p2])



if __name__ == '__main__':
    from Instruments.mocks import CamMock, DelayLineMock
    from Instruments.cam_phasetec import _ircam

    app = QApplication([])
    loop = QEventLoop(app)
    aio.set_event_loop(loop)
    cam = _ircam
    cam.set_shots(50)
    fs = FocusScan(cam=cam, move_func=cam.set_wavelength,
                   points=np.arange(5500, 6500, 5))
    fv = FocusScanView(fs)
    fv.show()





    loop.run_forever()








