from _imaqffi import lib, ffi
import threading
import numpy as np

class IMAQ_Reader:
    def __init__(self):
        Sid = ffi.new("SESSION_ID[1]")
        Iid = ffi.new("INTERFACE_ID[1]")
        self.lib = lib
        self.ec(self.lib.imgInterfaceOpen(b"img0", Iid))
        self.ec(self.lib.imgSessionOpen(Iid[0], Sid))
        self.ec(self.lib.imgSessionTriggerConfigure2(Sid[0],
                                                     self.lib.IMG_SIGNAL_EXTERNAL, 
                                                     lib.IMG_EXT_TRIG0,
                                                     0,
                                                     1000, self.lib.IMG_TRIG_ACTION_CAPTURE))
        self.read_lock = threading.Lock()
        s = Sid[0]
        self.s = s
        self.shots = 10
        self.last_valid = 0
        

    def ec(self, err):
        if err < 0:
            out = ffi.new("char[255]")
            self.lib.imgShowError(err, out)
            print(ffi.string(out))
            raise ValueError

    def get_fcount(self):
        fcount = ffi.new("long[1]")
        self.ec(self.lib.imgGetAttribute(self.s, 0x0076 + 0x3FF60000, fcount))
        return fcount[0]

    def get_lost(self):
        fcount = ffi.new("long[1]")
        self.ec(self.lib.imgGetAttribute(self.s, 0x0088 + 0x3FF60000, fcount))
        return fcount[0]

    def get_last_valid(self):
        fcount = ffi.new("long[1]")
        self.ec(self.lib.imgGetAttribute(self.s, 0x00BA + 0x3FF60000, fcount))
        return fcount[0]

    def start_acq(self):
        N = 100
        self.buflist = ffi.new("void *[]", [ffi.NULL]*N)
        self.ec(self.lib.imgRingSetup(self.s, N, ffi.cast("void **", self.buflist), 0, 0))
        self

    def read_cam(self, shots=None):
        if shots is None:
            shots = self.shots

        self.read_lock.acquire()
        arr = np.zeros((shots, 128, 128), dtype=np.float64)
        imgSize = 128*128*2
        lib = self.lib
        sid = self.s
        self.start_acq()
        self.ec(lib.imgSessionStartAcquisition(sid))

        outptr = ffi.new("void **")

        ptr = ffi.new("unsigned long[1]")

        status = ffi.new("uInt32[1]")
        buf_idx = ffi.new("uInt32[1]")
        self.ec(lib.imgSessionStatus(sid, status, buf_idx))
        #print("buf",buf_idx[0], "status", status[0])
        #self.ec(lib.imgSessionExamineBuffer2(sid, lib.IMG_CURRENT_BUFFER, ptr, outptr))
        #self.ec(lib.imgSessionReleaseBuffer(sid, ))
        #while self.get_fcount() == 0:
        #    pass
        fc = self.get_fcount()
        self.ec(lib.imgSessionStatus(sid, status, buf_idx))
        #print(fc, buf_idx[0])
        for i in range(shots):
            """USER_FUNC            imgSessionCopyArea(SESSION_ID
            boardid, uInt32
            bufNumber, void * userBuffer, IMG_OVERWRITE_MODE
            overwriteMode,
            uInt32 * copiedNumber, uInt32 * copiedIndex);"""
            ba = bytearray(imgSize)
        #    print(self.get_last_valid())
            self.ec(lib.imgSessionCopyBufferByNumber(sid, i, ffi.from_buffer(ba),
                                   lib.IMG_OVERWRITE_FAIL, ptr, buf_idx))
        #    print("req", i + fc, "fc", self.get_fcount(), "buf idx", buf_idx[0],
         #         "ifc", fc, "lv", self.get_last_valid(), "ret", ptr[0])
            if ptr[0] != (i):
                print("req", i + fc, "fc", self.get_fcount(),
                      "ifc", fc, "lv", self.get_last_valid(), "ret", ptr[0])
                print(i + fc, self.get_fcount(), fc, self.get_last_valid(), ptr[0])
                raise IOError(f"Req. {i+fc}, got {ptr[0]}")


            bi = np.frombuffer(ba).view('u2')
            a = np.swapaxes(bi.reshape(32, 128, 4), 0, 1).reshape(128, 128)
            arr[i, :, :] =  (1<<14)-a.T
            #arr = np.swapaxes(arr, 1, 2)

            #self.ec(lib.imgSessionReleaseBuffer(sid))
        #print(arr.shape)
        lost = self.get_lost()

        self.ec(lib.imgSessionStopAcquisition(sid))
        self.last_valid = self.get_last_valid()
        #print(fc, "fc", self.get_last_valid(), "val", lost , "lost")
        self.read_lock.release()

        return arr

    def acq_running(self):
        fcount = ffi.new("long[1]")
        self.ec(self.lib.imgGetAttribute(self.s, 0x0074 + 0x3FF60000, fcount))
        #print(fcount[0])
        return fcount[0] > 0


if __name__ == '__main__':
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore
    import time
    app = pg.mkQApp()
    timer = QtCore.QTimer()
    wid = pg.PlotWidget()
    ir = IMAQ_Reader()
    arr = ir.read_cam()
    back = arr.mean(0)
    it = pg.ImageItem(back)
    pt = pg.PlotCurveItem([1,2,3])
    wid.addItem(pt)


    np.save("testread2", ir.read_cam())
    import sys
    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)


    sys.excepthook = exception_hook
    import numpy as np
    import time
    def update():
        t = time.time()
        arr = ir.read_cam(10)
        #print(time.time()-t)
        #it.setImage(arr.mean(0), autoLevels=False)
        pt.setData(arr[:, 64, 64])
        #it.setLevels(0, 10000)

        #timer.stop()
    timer.timeout.connect(update)
    timer.start(30)
    wid.show()
    app.exec_()
