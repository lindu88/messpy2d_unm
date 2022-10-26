from Instruments.interfaces import IDelayLine
from .delay_gen import DG535
import attr


@attr.s(auto_attribs=True, keyword_only=True)
class GeneratorDelayline(IDelayLine):
    name: str = 'GeneratorDelayline'
    generator: object = attr.Factory(DG535)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.last_set = 0

    def move_mm(self, x: float):
        self.pos = x

    def is_moving(self):
        return False

    def get_pos_mm(self):
        return self.pos
