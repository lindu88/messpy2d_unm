import time
import os.path as osp
import ctypes as ct
import cffi
import time
#ct.WinDLL('PI_GCS_DLL_x64')

#header = ''.join(open('PI_GCS2_DLL.h').readlines()[126:-3])
p = osp.dirname(__file__)
header = ''.join(open(p+'/PI_GCS2_DLL.h').readlines()[126:300])
header = header.replace('PI_FUNC_DECL', '')
header = header.replace('__int64', 'int64_t')



ffi = cffi.FFI()
ax = b'1'

bool_out = ffi.new('int[1]')
double_out = ffi.new('double[1]')

def on_target():
    a.PI_qONT(i, ax, bool_out)
    print(bool_out)
    return bool(bool_out[0])



def is_moving():
    a.PI_IsMoving(i, ax, bool_out)
    return bool(bool_out[0])

def qSVO():
    a.PI_qSVO(i, ax, bool_out)
    return bool(bool_out[0])

def qFRF():
    a.PI_qSVO(i, ax, bool_out)
    return bool(bool_out[0])

def qPos():
    a.PI_qPOS(i, ax, double_out)
    return double_out[0]


#ffi.cdef("int PI_ConnectUSB(const char* szDescription);")
ffi.cdef(header)
a = ffi.dlopen(p +'/PI_GCS2_DLL_x64.dll')
i = a.PI_ConnectUSB(b'0145500652')
print(i)





def mm_to_fs(pos_in_mm):
    "converts mm to femtoseconds"
    speed_of_light = 299792458.
    pos_in_meters = pos_in_mm / 1000.
    pos_sec = pos_in_meters / speed_of_light
    return pos_sec * 1e15

def fs_to_mm(t_fs):
    speed_of_light = 299792458.
    pos_m = speed_of_light * t_fs * 1e-15
    return pos_m * 1000.



class DelayLine:
    def __init__(self):
        print(a.PI_INI(i, ax))
        if not qSVO():
            print(a.PI_SVO(i, ax, [1]))
        if not qFRF():
            print(a.PI_FNL(i, ax))
            while is_moving():
                print('ref ing')
                time.sleep(0.1)
        self.homepos = 9.0
    
    def get_pos_mm(self):
        return qPos()

    def get_pos_fs(self):
        return mm_to_fs((self.get_pos_mm()-self.homepos)*2.)

    def move_mm(self, mm, do_wait=True):
        a.PI_MOV(i, ax, [mm])
        if do_wait:
            while is_moving():
                print('mov ing')
                time.sleep(0.1)

    def move_fs(self, fs, do_wait=True):
        mm = fs_to_mm(fs)
        print('mm', mm+self.homepos)
        self.move_mm(mm/2.+self.homepos, do_wait=do_wait)

    def set_speed(self, speed):
        speed = float(speed)
        a.PI_VEL(i, ax, [speed])
    
    def wait_unil(self, pos):
        start_pos  = self.get_pos_mm(self)
        diff = (pos - start_pos)
        if diff == 0:
            return
        sign = diff/abs(diff)
        while True:
            diff = (pos - start_pos)
            if sign*diff > 0:
                break

dl = DelayLine()
dl.set_speed(1.0)
