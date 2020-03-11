from Instruments.interfaces import ILissajousScanner
import threading
import pipython
from pipython import pitools, fastaligntools
import typing, time
import json
import attr



mag = pipython.GCSDevice()
c843 = pipython.GCSDevice('C-843')

c843.dll.settimeout = lambda x: None
c843.ConnectPciBoard(1)


CONF_FILE = "sample_holder_conf.json"

try:
    with open(CONF_FILE, 'r') as f:
        conf = json.load(f)
        POS_LIST = conf['pos_list']

except IOError:
    POS_LIST = (0, 0)

@attr.s(auto_attribs=True)
class SampleHolder(ILissajousScanner):
    pos_home: tuple = POS_LIST

    def __attrs_post_init__(self):
        t = threading.Thread(target=self.init_m414)
        t.start()
        t2 = threading.Thread(target=self.init_mag)
        t2.start()
        t.join()
        t2.join()

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
            time.sleep(0.3)
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
        mag.SVO('1', True)
        mag.VEL('1', 700)
        mag.ACC('1', 5000)

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

    def set_home(self):
        p1,p2 = self.get_pos_mm()
        self.pos_home = (p1, p2)
        with open(CONF_FILE, 'w') as f:
            json.dump(dict(pos_list=(p1, p2)), f)


if __name__ == '__main__':
    sh = SampleHolder()
    print(sh.get_pos_mm())
    sh.is_moving()
    sh.set_pos_mm(-0, 80)
    print(sh.is_moving())
