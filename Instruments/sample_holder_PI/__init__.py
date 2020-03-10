from Instruments.interfaces import ILissajousScanner
import threading
import pipython
from pipython import pitools, fastaligntools
import typing



mag = pipython.GCSDevice()
c843 = pipython.GCSDevice('C-843')

c843.dll.settimeout = lambda x: None
c843.ConnectPciBoard(1)


class SampleHolder(ILissajousScanner):
    def __init__(self):
        t = threading.Thread(target=self.init_m414)
        t.start()
        self.init_mag()
        t.join()

    def init_m414(self):
        c843.CST('2',  'M-414.1PD')
        c843.qCST(2)
        c843.INI("2")
        c843.qREF()
        is_referenced = c843.qFRF('2')['2']
        if not is_referenced:
            c843.FRF('2')
            c843.errcheck = False
            while True:
                if c843.qFRF('2')['2']:
                    break
            c843.errcheck = True
            c843.isavailable
        c843.ACC('2', 500)
        c843.DEC('2', 500)

    def init_mag(self):
        devs  = mag.EnumerateUSB("C-891")
        mag.ConnectUSB(devs[0])
        mag.EAX('1', True)
        mag.SVO('1', True)
        if not mag.qFRF('1'):
            mag.FRF('1')
            pitools.waitonreferencing(mag)
            mag.SVO()

    def set_pos_mm(self, x=None, y=None):
        if x is not None:
            mag.MOV('1', x)
        if y is not None:
            c843.MOV('2', y)

    def get_pos_mm(self) -> typing.Tuple[float, float]:
        y = c843.qPOS('2')['2']
        x = mag.qPOS('1')['1']
        return x, y

    def is_moving(self) -> typing.Tuple[bool, bool]:
        a = c843.qMOV('2')['2']
        b = mag.qMOV('1')['1']
        return a, b

    def start_wave
if __name__ == '__main__':
    sh = SampleHolder()
    print(sh.get_pos_mm())
    sh.is_moving()
    sh.set_pos_mm(-20, 50)
    print(sh.is_moving())
