import cffi
import logging
import attr
import numpy as np
from pathlib import Path
from imaq_cffi import IMAQ_Reader

p = Path(__file__).parent
PT_DLL = cffi.FFI()

with open(p / 'pt_2dmct.h') as f:
    cdefs = f.readlines()[4:51]
    PT_DLL.cdef(''.join(cdefs))
""" Binning Modes
  Index	Columns x Rows 	Max. Frame Rate
  0	128 x 128	(1.610 kHz)
  1	128 x 64	(2.899 kHz)
  2	128 x 56	(3.220 kHz)
  3	128 x 32	(4.830 kHz)
  4	128 x 16	(7.246 kHz)
  5	96 x 64	(3.773 kHz)
  6	96 x 32	(6.289 kHz)
"""

BINNING_MODES = [(128, 128), (128, 64), (128, 56), (128, 32), (128, 16),
                 (96, 64), (96, 32)]


@attr.s(auto_attribs=True)
class PT_MCT:
    shots: int = attr.ib(40)
    int_time_us: int = attr.ib(700)
    binning_mode: int = attr.ib(0)
    gain: int = attr.ib(9)
    offset: int = attr.ib(164)
    use_trigger: int = attr.ib(True)

    def __attrs_post_init__(self):
        self.load_dll()
        self.setup_cam()
        self.reader = IMAQ_Reader()

    def _errchk(self, err):
        if err != 0:
            errStr = PT_DLL.new('char[500]')
            self._dll.LVDLLStatus(errStr, 500, PT_DLL.NULL)
            print(PT_DLL.string(errStr))

    def load_dll(self):
        self._dll = PT_DLL.dlopen(str(p / 'pt_2dmct.dll'))

    def setup_cam(self):
        ec = self._errchk
        ec(self._dll.PT_2DMCT_Initialize())
        out = PT_DLL.new('double*')
        ec(self._dll.PT_2DMCT_IntegrationTime(self.int_time_us, out))
        ec(self._dll.PT_2DMCT_SetGainOffset(self.gain, self.offset))
        ec(self._dll.PT_2DMCT_SetWindowSize(self.binning_mode))

    def set_gain(self, gain):
        ec = self._errchk
        self.gain = gain
        ec(self._dll.PT_2DMCT_SetGainOffset(self.gain, self.offset))

    def set_offset(self, offset):
        ec = self._errchk
        self.offset = offset
        ec(self._dll.PT_2DMCT_SetGainOffset(self.gain, self.offset))

    def get_tempK(self):
        text = PT_DLL.new('char[100]')
        TempK = PT_DLL.new('double*')
        err = self._dll.PT_2DMCT_GetFPATemp(text, TempK, 100)
        self._errchk(err)
        return TempK[0]

    def read_cam(self):
        self.reader.shots = self.shots
        return self.reader.read_cam(self.shots)

    def read_cam2(self):
        rows, cols = BINNING_MODES[self.binning_mode]
        # p = PT_DLL.new('Uint16Array***', init=self._data)
        self.arr = np.zeros((rows, cols, self.shots), dtype=np.uint16)
        p = PT_DLL.from_buffer(self.arr)
        # t = time.time()
        self.offset = 16384 * np.ones_like(self.arr)
        self._errchk(self._dll.PT_2DMCT_GetFrames(self.shots, cols, rows, self.use_trigger, p, self.arr.size))
        # print("DLL CALL", time.time()-t)
        # self.arr += self.arr
        self.offset -= self.arr
        # self.arr *= -1
        return self.offset.T


if __name__ == '__main__':
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore
    import time

    app = pg.mkQApp()
    timer = QtCore.QTimer()
    wid = pg.ImageView()
    wid2 = pg.ImageView()
    pt = PT_MCT()
    # print(pt.get_tempK())
    pt.read_cam()
    import numpy as np


    def update():
        t = time.time()
        a = pt.read_cam()
        print(time.time() - t)
        wid.setImage(a.std(0).T, autoLevels=False)
        wid2.setImage(a.mean(0).T, autoLevels=False)


    timer.timeout.connect(update)
    timer.start(30)
    wid.show()
    wid2.show()
    app.exec_()
