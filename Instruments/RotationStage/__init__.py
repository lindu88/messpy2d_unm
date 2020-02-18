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
        rot.timeout = 0.5
        return rot

    def w(self,x):
        writer_str = str(x) + '\r\n'
        self.rot.write(writer_str.encode())

    def set_degrees(self, pos):
        """Set absolute position of the roatation stage"""
        setter_str = '1PA' + str(pos) + '\r\n'
        self.rot.write(setter_str.encode())

    def get_degrees(self):
        """Returns the position"""
        self.w('1TP')
        self.rot.timeout = 0.1
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
    deg = rs.get_degrees()
    rs.set_degrees(20)



#rs.set_pos(1)
