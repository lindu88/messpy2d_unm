import time
from typing import Literal
from Instruments.interfaces import IDelayLine
from serial import Serial
import attr


state_str = """
0A NOT INITIALIZED: after reset
0B NOT INITIALIZED: after CONFIG state
0C NOT INITIALIZED: after INITIALAZING state
0D NOT INITIALIZED: after NOT_REFERENCED state
0E NOT INITIALIZED: after HOMING state
0F NOT INITIALIZED: after MOVING state
10 NOT INITIALIZED: after READY state
11 NOT INITIALIZED: after DISABLE state
12 NOT INITIALIZED: after JOGGING state
13 NOT INITIALIZED: error, Stage type not valid
1E INITIALAZING: launch by USB
1F INITIALAZING: launch by Remote Control
28 NOT_REFERENCED
32 HOMING: launch by USB
33 HOMING: launch by Remote Control
3C MOVING
46 READY: after HOMING state
47 READY: after MOVING state
48 READY: after DISABLE state
49 READY: after JOGGING state
50 DISABLE: after READY state
51 DISABLE: after MOVING state
52 DISABLE: after JOGGING state
5A JOGGING: after READY state
5B JOGGING: after DISABLE state
"""

CONTROLLER_STATES = {s[:2]: s[3:] for s in state_str.splitlines() if s}
MAIN_STATES = {}
for k, v in CONTROLLER_STATES.items():
    i = v.find(':')
    if i != -1:
        v = v[:v.find(':')]
    MAIN_STATES[k] = v

SHORT_STATES = Literal['NOT_REFERENCED', 'READY', 'JOGGING', 'INITIALAZING', 'HOMING', 'NOT INITIALIZED', 'MOVING', 'DISABLE']

@attr.s(auto_attribs=True)
class NewportDLC(IDelayLine):
    name: str = 'Newport DLC'
    port: str = 'COM3'
    serial: Serial = attr.ib()

    @serial.default
    def _default_serial(self):
        return Serial(self.port, baudrate=115200 * 4)

    def __attrs_post_init__(self):
        super(NewportDLC, self).__attrs_post_init__()
        if self.controller_state() != 'READY':
            if self.controller_state() == 'NOT INITIALIZED':
                self.write('IE')
                while self.controller_state() == 'INITIALAZING':
                    time.sleep(0.1)
            if self.controller_state() == 'NOT_REFERENCED':
                self.write('OR')
                while self.controller_state() == 'HOMING':
                    time.sleep(0.1)
            if self.controller_state() == "DISABLE":
                self.write('MM1')
                
    def write(self, cmd: str):
        """
        Writes a command to the controller.
        """
        self.serial.write((cmd+'\r\n').encode())

    def read(self) -> str:
        return self.serial.read_until(b'\r\n').decode().strip()[:-2]

    def controller_state(self) -> SHORT_STATES:
        """
        Returns the current controller state.
        """
        self.write('TS')
        state = self.read()
        return MAIN_STATES[state[-2:]]

    def is_moving(self) -> bool:
        return self.controller_state() == 'MOVING'

    def get_pos_mm(self):
        self.write('TP?')
        return float(self.read())

    def set_pos_mm(self, pos_mm: float):
        self.write(f'TP{pos_mm:.3f}')
