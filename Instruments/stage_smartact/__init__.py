import attr
import sys
import typing

from smaract import ctl

from Instruments.interfaces import ILissajousScanner


@attr.define
class SmarActXYZ(ILissajousScanner):
    name: str = 'SmarAct XYZ'
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
            move_mode = ctl.MoveMode.CL_ABSOLUTE
            ctl.SetProperty_i32(self.handle, idx, ctl.Property.MOVE_MODE, move_mode)

    def get_pos_mm(self) -> typing.Tuple[float, float]:
        pos = []
        for c in ['x', 'y']:
            position = ctl.GetProperty_i64(self.handle, self.channels[c], ctl.Property.POSITION)
            pos.append(position * 1e-9)
        return tuple(pos)

    def set_pos_mm(self, x=None, y=None):
        if x is not None:
            ctl.Move(self.handle, self.channel['x'], round(x/1e-9), 0)
        if y is not None:
            ctl.Move(self.handle, self.channel['z'], round(y/1e-9), 0)

    def is_moving(self) -> typing.Tuple[bool, bool]:
        state = ctl.GetProperty_i32(self.handle, self.channels['x'], ctl.Property.CHANNEL_STATE)
        x_moving = state & ctl.ChannelState.ACTIVELY_MOVING
        state = ctl.GetProperty_i32(self.handle, self.channels['y'], ctl.Property.CHANNEL_STATE)
        y_moving = state & ctl.ChannelState.ACTIVELY_MOVING
        return bool(x_moving), bool(y_moving)

    def set_home(self):
        pass

    def set_zpos_mm(self, mm: float):
        ctl.Move(self.handle, self.channels['z'], round(mm/1e-9), 0)

    def get_zpos_mm(self) -> float:
        position = ctl.GetProperty_i64(self.handle, self.channels['z'], ctl.Property.POSITION)
        return position*1e-9

    def is_zmoving(self) -> bool:
        state = ctl.GetProperty_i32(self.handle, self.channels['z'], ctl.Property.CHANNEL_STATE)
        return state & ctl.ChannelState.ACTIVELY_MOVING

    def parse_error(self, e: ctl.Error):
        return "MCS2 {}: {}, error: {} (0x{:04X}) in line: {}.".format(e.func, ctl.GetResultInfo(e.code),
                                                                       ctl.ErrorCode(e.code).name, e.code,
                                                                       sys.exc_info()[-1].tb_lineno
                                                                       )


if __name__ == '__main__':
    stage = SmarActXYZ(name='SmartAct', pos_home=(0, 0, 0))
    print(stage.get_pos_mm())
    print(stage.is_moving())
    #stage.set_zpos_mm(-15)
    print(stage.is_zmoving())
    print(stage.get_zpos_mm())
