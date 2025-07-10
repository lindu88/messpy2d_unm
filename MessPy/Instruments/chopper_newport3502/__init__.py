import os
import attr
import sys
import clr
from sympy import false

from MessPy.Instruments.interfaces import IChopper
sys.path.append(os.getcwd())
clr.AddReference("CmdLib3502")
from NewFocus.ChopperApp import *


@attr.s(auto_attribs=True)
class newport3502(IChopper):
    name: str = "Newport Chopper"
    comport: str = "com3"
    driver: CmdLib3502 = attr.ib(factory=lambda: CmdLib3502(False))
    devicekey: str = attr.ib(init=False, default=None)
    currentFreq: float = attr.ib(init=False, default=None)
    currentPhaseOffset: float = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        # Setup device key
        self.devicekey = self.driver.GetFirstDeviceKey()

        # Attempt to open device
        success = self.driver.Open(self.devicekey)
        if not success:
            print("chopper device not able to open\n")

    def close(self):
        suc = self.driver.close(self.devicekey)
        if (not suc):
            print("unable to close chopper device\n")
        return suc
    
    def get_phase(self) -> bool:
        return self.driver.getPhase(self.devicekey, self.currentPhaseOffset)

    def set_phase(self, pd):
        self.driver.setPhaseDelay(self.devicekey, pd)

    def set_sync(self, sync):
        # 1-3 for sync but
        self.driver.SetSync(self.devicekey, sync)

    def get_frequency(self) -> bool:
        return self.driver.getFrequency(self.devicekey, 1, self.currentFreq)

    def set_frequency(self, f: float):
        self.driver.setFrequency(self.devicekey, self.currentFreq)
if __name__ == '__main__':
    test = newport3502()