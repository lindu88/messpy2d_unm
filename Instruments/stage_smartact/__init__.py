import typing, attr

from smaract import ctl


from Instruments.interfaces import ILissajousScanner

@attr.define
class SmarActXYZ(ILissajousScanner):
    handle: int = attr.ib(init=False)
    channels: dict[str, int] = {"x": 0, "y": 1, "z": 2}

    def __attrs_post_init__(self):
        super(SmarActXYZ, self).__attrs_post_init__()
        buffer = ctl.FindDevices()
        if len(buffer) == 0:
            raise IOError("MCS2 no devices found.")
        locators = buffer.split("\n")
        self.handle = ctl.Open(locators[0])

        for c, idx in self.channels.items():
            ctl.SetProperty_i32(self.handle, idx, ctl.Property.MAX_CL_FREQUENCY, 6000)
            ctl.SetProperty_i32(self.handle, idx, ctl.Property.HOLD_TIME, 1000)

    def get_pos_mm(self) -> typing.Tuple[float, float]:
        pos = []
        for c, idx in self.channels.items():
            position = ctl.GetProperty_i64(self.handle, idx, ctl.Property.POSITION)
            pos.append(position)
        return tuple(pos)

    def set_pos_mm(self, x=None, y=None):
        move_mode = ctl.MoveMode.CL_ABSOLUTE
        ctl.SetProperty_i32(self.handle, self.channel, ctl.Property.MOVE_MODE, move_mode)
        ctl.Move(self.handle, self.channel, x, 0)

    def is_moving(self) -> typing.Tuple[bool, bool]:
        pass

    def set_home(self):
        pass

    def set_zpos_mm(self, mm: float):
        pass

    def get_zpos_mm(self) -> float:
        pass

    def is_zmoving(self) -> bool:
        pass


if __name__ == '__main__':
    stage = SmarActXYZ(name='SmartAct', pos_home=(0, 0, 0))
    print(stage.get_pos_mm())
