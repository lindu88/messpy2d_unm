from .pyPICommands import pyPICommands as gcs
import time, os
C = os.path.abspath(os.path.dirname(__file__))
CMDS = gcs(dllname=C+'\\PI_GCS2_DLL_x64.dll', funcprefix='PI_')

CONNECTED_AXES = ['1']

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

def init_axes(cmds):
    """references the axes"""
    ref_ok = cmds.qFRF(' '.join(CONNECTED_AXES))
    for axis_to_ref in CONNECTED_AXES:
        cmds.SVO({axis_to_ref:1})        # switch on servo
        if ref_ok[axis_to_ref] != 1:
            print('referencing axis ' + axis_to_ref)
            cmds.FNL(axis_to_ref)

    axes_are_referencing = True
    while axes_are_referencing:
        time.sleep(0.1)
        ref = cmds.IsMoving(' '.join(CONNECTED_AXES))
        axes_are_referencing = sum(ref.values()) > 0


class DelayLine:
    def __init__(self):
        USB_devs = CMDS.EnumerateUSB(b'')
        CMDS.ConnectUSB(USB_devs[0])
        init_axes(CMDS)
        print('connected to ', CMDS.qIDN())
    
    def get_pos_mm(self):
        return CMDS.qPOS(CONNECTED_AXES)[0]

    def move_mm(self, mm):
        CMDS.MOV({1: mm})
        #while CMDS.IsMoving(CONNECTED_AXES):
        #   time.sleep(0.2)
    
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
dl.move_mm(2.)
                      
        
        


