from asyncio import *
import attr
from Instruments.interfaces import ILissajousScanner, ICam, IDelayLine
from typing import List, Callable, Tuple


@attr.s(auto_attribs=True, cmp=False)
class FocusScan:
    cam: ICam
    sample_scanner: IDelayLine
    points: List[float]
    amps: List[List[float]] = attr.Factory(list)
    start_pos: Tuple[float, float] = 0

    async def step(self):
        await self.pre_scan()
        for p in self.points:
            await self.read_point(p)
        await self.post_scan()

    async def pre_scan(self):
        self.sample_scanner.move_mm(self.start_pos)

    async def post_scan(self):
        pass

    async def read_point(self, p):
        self.sample_scanner.move_mm(p)
        print(p)
        while self.sample_scanner.is_moving():
            await sleep(0.01)
        reading = await self.cam.async_make_read()
        self.amps.append(reading.lines.sum(1))
        print(self.amps[-1])

if __name__ == '__main__':
    from Instruments.mocks import CamMock, DelayLineMock

    fs = FocusScan(cam=CamMock(), sample_scanner=DelayLineMock(),
                   points=range(0, 100))

    loop = new_event_loop()
    loop.run_until_complete(fs.step())







