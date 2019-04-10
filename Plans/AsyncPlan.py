import asyncio as aio
import attr
#from PyQt5.QtWidgets import QWidget
import os

os.environ['QT_API'] = 'PyQt5'
from Instruments.interfaces import ILissajousScanner, ICam, IDelayLine
from typing import List, Callable, Tuple
from asyncqt import QEventLoop, asyncClose, asyncSlot
from qtpy.QtWidgets import *
from qtpy.QtCore import QObject, Signal

@attr.s(auto_attribs=True, cmp=False)
class FocusScan(QObject):
    cam: ICam
    sample_scanner: IDelayLine
    points: List[float]
    amps: List[List[float]] = attr.Factory(list)
    start_pos: Tuple[float, float] = 0

    sigStepDone = Signal()

    def __attrs_post_init__(self):
        super().__init__()

    async def step(self):
        await self.pre_scan()
        for p in self.points:
            await self.read_point(p)
            self.sigStepDone.emit()

        await self.post_scan()

    async def pre_scan(self):
        self.sample_scanner.move_mm(self.start_pos)

    async def post_scan(self):
        pass

    async def read_point(self, p):
        self.sample_scanner.move_mm(p)
        while self.sample_scanner.is_moving():
            await aio.sleep(0.01)

        reading = await loop.run_in_executor(None, self.cam.make_reading)
        self.amps.append(reading.lines.sum(1))



class FocusScanView(QWidget):
    def __init__(self, focus_scan: FocusScan, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.focus_scan = focus_scan
        self.info_label = QLabel('BLa')
        self.focus_scan.sigStepDone.connect(self.update_view)
        self.setLayout(QHBoxLayout())
        self.start_button = QPushButton('start')
        self.layout().addWidget(self.info_label)
        self.layout().addWidget(self.start_button)
        self.start_button.clicked.connect(self.start)


    def start(self):
        loop = aio.get_event_loop()
        loop.create_task(self.focus_scan.step())

    @asyncSlot()
    async def update_view(self):
        print('update')
        self.info_label.setText(str(self.focus_scan.amps[-1]))

if __name__ == '__main__':
    from Instruments.mocks import CamMock, DelayLineMock

    app = QApplication([])
    loop = QEventLoop(app)
    aio.set_event_loop(loop)
    cam = CamMock()
    cam.set_shots(10)
    fs = FocusScan(cam=cam, sample_scanner=DelayLineMock(),
                   points=range(0, 100))
    fv = FocusScanView(fs)
    fv.show()





    loop.run_forever()








