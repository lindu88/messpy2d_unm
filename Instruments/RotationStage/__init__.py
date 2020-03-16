# -*- coding: utf-8 -*-
"""
Created on Wed Jun 04 19:06:42 2014

@author: tillsten
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jun 03 15:41:22 2014

@author: tillsten
"""

try:
    rs.s.close()
except NameError:
    pass

import serial
import json, os
from Instruments.interfaces import IRotationStage
import attr


CONF_FILE = "rot_stage_conf.json"

try:
    with open(CONF_FILE, 'r') as f:
        conf = json.load(f)
        pol_list = conf['pol_list']

except IOError:
    pol_list = (0, 45)

@attr.s(auto_attribs=True)
class RotationStage(IRotationStage):
    name: str = 'Rotation Stage'
    comport: str = 'COM11'
    rot: object = attr.ib()
    set_pol_list: pol_list = attr.ib()

    @rot.default
    def _default_rs(self):
        rot = serial.Serial(self.comport, baudrate = 115200 * 8, xonxoff = 1)
        rot.timeout = 3

        return rot

    def __attrs_post_init__(self):
        self.rot.write(b'1OR\r\n')

    def w(self,x):
        writer_str = f'{x}\r\n'
        self.rot.write(writer_str.encode('utf-8'))
        self.rot.timeout = 3

    def set_degrees(self, pos):
        """Set absolute position of the roatation stage"""
        setter_str = f'1PA{pos}\r\n'
        self.rot.write(setter_str.encode('utf-8'))
        self.rot.timeout = 3

    def get_degrees(self):
        """Returns the position"""
        self.w('1TP')
        self.rot.timeout = 0.5
        ans = self.rot.readall().decode()
        return float(ans[ans.find("TP")+2:-2])

    def is_moving(self):
        self.w('1MM?')
        ans = self.rot.readall().decode()
        return ans[ans.find("MM")+2:-2] == '28'

    def switch_pol(self):
        self.pol_idx = (self.pol_idx + 1)%len(self.pol_list)
        self.set_pos(self.pol_list[self.pol_idx])

    def set_pol_list(self, a1, a2):
        self.pol_list = (a1, a2)
        with open(CONF_FILE, 'w') as f:
            json.dump(dict(pol_list=(a1, a2)), f)




rs = RotationStage()

if __name__ == '__main__':
    import time
    print('change first')
    rs.set_degrees(0)
    time.sleep(8)
    deg = rs.get_degrees()
    print(f'first pol:{deg}')
    rs.set_degrees(80)
    time.sleep(8)
    deg = rs.get_degrees()
    print(f'second pol:{deg}')



#rs.set_pos(1)
