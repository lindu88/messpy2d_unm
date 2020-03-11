from Instruments.interfaces import ILissajousScanner
import threading
import pipython
from pipython import pitools, fastaligntools
import typing, time
import json
import attr
import  numpy as np
mag = pipython.GCSDevice()
c843 = pipython.GCSDevice('C-843')

c843.dll.settimeout = lambda x: None
c843.ConnectPciBoard(1)

from pathlib import Path
dir = Path(__file__).parent
CONF_FILE = dir / "sample_holder_conf.json"

try:
    with open(CONF_FILE, 'r') as f:
        conf = json.load(f)
        POS_LIST = conf['pos_list']
except FileNotFoundError:
    POS_LIST = (0, 0)

@attr.s(auto_attribs=True)
class SampleHolder(ILissajousScanner):
    name: str = 'Pi Instruments Sampleholder'
    pos_home: tuple = POS_LIST

    def __attrs_post_init__(self):
        t = threading.Thread(target=self.init_m414)
        t.start()
        t2 = threading.Thread(target=self.init_mag)
        t2.start()
        t.join()
        t2.join()
        self.set_pos_mm(*self.pos_home)

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
            time.sleep(0.5)
        c843.ACC('2', 500)
        c843.DEC('2', 500)

    def init_mag(self):
        devs  = mag.EnumerateUSB("C-891")
        mag.ConnectUSB(devs[0])
        mag.EAX('1', True)
        mag.SVO('1', True)
        if not mag.qFRF('1')['1']:
            mag.FRF('1')
            while not mag.qFRF('1')['1']:
                print( mag.qFRF('1')['1'])
                pass
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
        print(f'set_home: {self.pos_home[0]},{self.pos_home[1]}')
        with open(CONF_FILE, 'w') as f:
            json.dump(dict(pos_list=(p1, p2)), f)

    def start_contimove(self,x,y):
        self.do_move = True
        self.thread = threading.Thread(target=self.do_contimove,args=(x,y))
        self.thread.start()

    def do_contimove(self, x_settings, y_settings):
        x_stepper = np.arange(-x_settings,x_settings, 1)
        y_stepper = np.arange(-y_settings[0],y_settings[0], y_settings[1])
        idx = 1
        while self.do_move:
            if idx% 2 == 0:
                for jdx, j in enumerate(y_stepper):
                    self.set_pos_mm(None, self.pos_home[1] - j)
                    time.sleep(0.05)
                    if jdx % 2 == 0:
                        for i in x_stepper:
                            self.set_pos_mm(self.pos_home[0]+i,None)
                            time.sleep(0.05)
                    else:
                        for i in x_stepper:
                            self.set_pos_mm(self.pos_home[0]-i,None)
                            time.sleep(0.05)
                    idx +=1
            else:
                for jdx, j in enumerate(y_stepper):
                    self.set_pos_mm(None, self.pos_home[1] + j)
                    time.sleep(0.05)
                    if jdx % 2 == 0:
                        for i in x_stepper:
                            self.set_pos_mm(self.pos_home[0]+i,None)
                            time.sleep(0.05)
                    else:
                        for i in x_stepper:
                            self.set_pos_mm(self.pos_home[0]-i,None)
                            time.sleep(0.05)
                idx += 1


    def stop_contimove(self):
        self.do_move = False

if __name__ == '__main__':
    sh = SampleHolder()
    print(sh.get_pos_mm())
    sh.is_moving()
    sh.set_pos_mm(-0, 80)
    print(sh.is_moving())
