import cffi
import threading
import numba
import numpy as np


ffi = cffi.FFI()
defs = ffi.cdef("""
typedef unsigned long       uInt32;
typedef long       Int32;

typedef  uInt32   INTERFACE_ID;
typedef  uInt32   SESSION_ID;
typedef  uInt32   EVENT_ID;
typedef  uInt32   PULSE_ID;
typedef  uInt32   BUFLIST_ID;
typedef  Int32    IMG_ERR;
typedef  uInt32   GUIHNDL;
typedef  char Int8;

typedef int USER_FUNC;

#define  IMG_TRIG_ACTION_CAPTURE             1
#define  IMG_EXT_TRIG0                       0
#define  IMG_LAST_BUFFER                     0xFFFFFFFE
#define  IMG_OLDEST_BUFFER                   0xFFFFFFFD
#define  IMG_CURRENT_BUFFER                  0xFFFFFFFC
#define  IMG_TRIG_DRIVE_FRAME_START          8
#define  IMG_TRIG_DRIVE_FRAME_DONE           9
#define  IMG_TRIG_POLAR_ACTIVEH              0
#define  IMG_TRIG_POLAR_ACTIVEL              1

typedef enum {
    IMG_SIGNAL_NONE                 = 0xFFFFFFFF,
    IMG_SIGNAL_EXTERNAL             = 0,
    IMG_SIGNAL_RTSI                 = 1,
    IMG_SIGNAL_ISO_IN               = 2,
    IMG_SIGNAL_ISO_OUT              = 3,
    IMG_SIGNAL_STATUS               = 4,
    IMG_SIGNAL_SCALED_ENCODER       = 5,
    IMG_SIGNAL_SOFTWARE_TRIGGER     = 6
} IMG_SIGNAL_TYPE;


typedef enum {
    IMG_OVERWRITE_GET_OLDEST         = 0,
    IMG_OVERWRITE_GET_NEXT_ITERATION = 1,
    IMG_OVERWRITE_FAIL               = 2,
    IMG_OVERWRITE_GET_NEWEST         = 3
} IMG_OVERWRITE_MODE;

USER_FUNC imgInterfaceOpen(const Int8* interface_name, INTERFACE_ID* ifid);
USER_FUNC imgSessionOpen(INTERFACE_ID ifid, SESSION_ID* sid);
USER_FUNC imgSessionStatus(SESSION_ID sid, uInt32* boardStatus, uInt32* bufIndex);
USER_FUNC imgClose(uInt32 void_id, uInt32 freeResources);
USER_FUNC imgSnap(SESSION_ID sid, void **bufAddr);
USER_FUNC imgSnapArea(SESSION_ID sid, void **bufAddr,uInt32 top,uInt32 left, uInt32 height, uInt32 width,uInt32 rowBytes);
USER_FUNC imgGrabSetup(SESSION_ID sid, uInt32 startNow);
USER_FUNC imgGrab(SESSION_ID sid, void** bufPtr, uInt32 syncOnVB);
USER_FUNC imgGrabArea(SESSION_ID sid, void** bufPtr, uInt32 syncOnVB, uInt32 top, uInt32 left, uInt32 height, uInt32 width, uInt32 rowBytes);
USER_FUNC imgRingSetup(SESSION_ID sid,  uInt32 numberBuffer,void* bufferList[], uInt32 skipCount, uInt32 startnow);
USER_FUNC imgSequenceSetup(SESSION_ID sid,  uInt32 numberBuffer,void* bufferList[], uInt32 skipCount[], uInt32 startnow, uInt32 async);
USER_FUNC imgGetAttribute(uInt32 void_id, uInt32 attribute, void* value);
USER_FUNC imgSessionReleaseBuffer(SESSION_ID sid);
USER_FUNC imgSessionStopAcquisition(SESSION_ID sid);
USER_FUNC imgSessionStartAcquisition(SESSION_ID sid);
USER_FUNC imgSessionExamineBuffer2(SESSION_ID sid, uInt32 whichBuffer, uInt32 *bufferNumber, void** bufferAddr);
USER_FUNC imgSessionCopyArea (SESSION_ID boardid, uInt32 bufNumber, void* userBuffer, IMG_OVERWRITE_MODE overwriteMode, 
                               uInt32* copiedNumber, uInt32* copiedIndex);
USER_FUNC imgSessionCopyBufferByNumber(SESSION_ID sid, uInt32 bufNumber, void* userBuffer, IMG_OVERWRITE_MODE overwriteMode, uInt32* copiedNumber, uInt32* copiedIndex);

int imgShowError(int err, char* msg); 

USER_FUNC imgSessionTriggerConfigure2(SESSION_ID sid, IMG_SIGNAL_TYPE triggerType, 
    uInt32 triggerNumber, uInt32 polarity, uInt32 timeout, uInt32 action);
USER_FUNC imgSessionTriggerDrive2(SESSION_ID sid, IMG_SIGNAL_TYPE triggerType,
    uInt32 triggerNumber, uInt32 polarity, uInt32 source);

""")


class IMAQ_Reader:
    def __init__(self):
        Sid = ffi.new("SESSION_ID[1]")
        Iid = ffi.new("INTERFACE_ID[1]")
        self.lib = ffi.dlopen("imaq.dll")
        self.ec(self.lib.imgInterfaceOpen(b"img0", Iid))
        self.ec(self.lib.imgSessionOpen(Iid[0], Sid))
        self.ec(self.lib.imgSessionTriggerConfigure2(Sid[0], self.lib.IMG_SIGNAL_EXTERNAL, 0, 0,
                                                     10000, self.lib.IMG_TRIG_ACTION_CAPTURE))
        self.ec(self.lib.imgSessionTriggerDrive2(Sid[0], self.lib.IMG_SIGNAL_RTSI, 1, self.lib.IMG_TRIG_POLAR_ACTIVEH,
                                                 self.lib.IMG_TRIG_DRIVE_FRAME_START                                                     ))
        self.read_lock = threading.Lock()
        s = Sid[0]
        self.s = s
        self.shots = 10
        self.last_valid = 0
        self.start_acq()

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
        N = 1000
        self.buflist = ffi.new("void *[]", [ffi.NULL] * N)
        self.ec(self.lib.imgRingSetup(self.s, N, ffi.cast("void **", self.buflist), 0, 0))
        #self

    def read_cam(self, shots=None):
        if shots is None:
            shots = self.shots

        self.read_lock.acquire()
        arr = np.zeros((shots, 128, 128), dtype=np.float64)
        imgSize = 128 * 128 * 2
        lib = self.lib
        sid = self.s
        self.start_acq()
        self.ec(lib.imgSessionStartAcquisition(sid))

        outptr = ffi.new("void **")

        ptr = ffi.new("unsigned long[1]")

        status = ffi.new("uInt32[1]")
        buf_idx = ffi.new("uInt32[1]")
        self.ec(lib.imgSessionStatus(sid, status, buf_idx))
        # print("buf",buf_idx[0], "status", status[0])
        # self.ec(lib.imgSessionExamineBuffer2(sid, lib.IMG_CURRENT_BUFFER, ptr, outptr))
        # self.ec(lib.imgSessionReleaseBuffer(sid, ))
        while self.get_fcount() == 0:
            pass
        fc = self.get_fcount()
        self.ec(lib.imgSessionStatus(sid, status, buf_idx))
        # print(fc, buf_idx[0])
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
                raise IOError(f"Req. {i + fc}, got {ptr[0]}")

            bi = np.frombuffer(ba).view('u2')
            a = np.swapaxes(bi.reshape(32, 128, 4), 0, 1).reshape(128, 128)
            arr[i, :, :] = (1 << 14) - a.T
            if self.get_fcount() > shots:
                self.ec(lib.imgSessionStopAcquisition(sid))
            # arr = np.swapaxes(arr, 1, 2)

            # self.ec(lib.imgSessionReleaseBuffer(sid))
        # print(arr.shape)
        #lost = self.get_lost()

        self.ec(lib.imgSessionStopAcquisition(sid))
        #self.last_valid = self.get_last_valid()
        # print(fc, "fc", self.get_last_valid(), "val", lost , "lost")
        self.read_lock.release()

        return arr

    def acq_running(self):
        fcount = ffi.new("long[1]")
        self.ec(self.lib.imgGetAttribute(self.s, 0x0074 + 0x3FF60000, fcount))
        # print(fcount[0])
        return fcount[0] > 0

@numba.njit
def read_loop(shots, lib, sid, ptr, buf_idx):
    for i in range(shots):
        ba = bytearray(128*128*2)
        #    print(self.get_last_valid())
        x = lib.imgSessionCopyBufferByNumber(sid, i, ffi.from_buffer(ba),
                                                 lib.IMG_OVERWRITE_FAIL, ptr, buf_idx)
        bi = np.frombuffer(ba).view('u2')
        a = np.swapaxes(bi.reshape(32, 128, 4), 0, 1).reshape(128, 128)
        arr[i, :, :] = (1 << 14) - a.T


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
    #pt = pg.PlotCurveItem([1, 2, 3])
    wid.addItem(it)

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
        # print(time.time()-t)
        it.setImage(arr.mean(0).T-back.T, autoLevels=True)
        #pt.setData(arr[:, 64, 64])
        # it.setLevels(0, 10000)

        # timer.stop()


    timer.timeout.connect(update)
    timer.start(30)
    wid.show()
    app.exec_()
