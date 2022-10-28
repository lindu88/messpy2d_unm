from Instruments.interfaces import IDelayLine
from .delay_gen import DG535
import attr


@attr.s(auto_attribs=True, keyword_only=True)
class GeneratorDelayline(IDelayLine):
    name: str = 'GeneratorDelayline'
    generator: DG535 = attr.Factory(DG535)
    last_set: float = 0

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.last_set = 0

    def move_mm(self, x: float):
        self.pos = x

    def is_moving(self):
        return False

    def get_pos_mm(self):
        return self.pos

    def get_pos_fs(self) -> float:
        return self.last_set*1000

    def def_home(self):
        self.home_pos = self.last_set + self.home_pos

    def move_fs(self, fs, do_wait=False, *args, **kwargs):
        """
        For the delay generator we use ns seconds as base unit for the ScanSetting
        instead of ps. Hence we also have a factor 1000 here since DG gen takes
        ns.


        """
        self.last_set = fs/1000.
        self.generator.set_delay('A', fs/1000. + self.home_pos)