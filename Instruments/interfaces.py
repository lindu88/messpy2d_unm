import typing
import abc
import attr


# Defining a minimal interface for each hardware
@attr.s
class ICam(abc.ABC):
    shots: int = attr.ib()
    channels: int = attr.ib()
    background: attr.ib((0, 0))

    @abc.abstractmethod
    def read_cam(self):
        pass

    @abc.abstractmethod
    def set_shots(self, shots):
        pass

    def get_background(self):
        return self.background

    def set_background(self, back_a, back_b):
        self.background = (back_a, back_b)

    def record_background(self):
        for i in range(5):
            a, b, *_ = self.read_cam()
        back_a, back_b = a.mean(1), b.mean(1)
        self.set_background(back_a, back_b)



def mm_to_fs(pos_in_mm):
    "converts mm to femtoseconds"
    speed_of_light = 299792458.
    pos_in_meters = pos_in_mm / 1000.
    pos_sec = pos_in_meters / speed_of_light
    return pos_sec * 1e15

def fs_to_mm(t_fs):
    speed_of_light = 299792458.
    pos_m = speed_of_light * t_fs * 1e-15
    return pos_m * 1000.


@attr.s
class IDelayLine(abc.ABC):
    home_pos: float = attr.ib(0.)

    @abc.abstractmethod
    def move_mm(self, mm, *args, **kwargs):
        pass

    @abc.abstractmethod
    def get_pos_mm(self):
        pass

    def get_pos_fs(self):
        return mm_to_fs((self.get_pos_mm()-self.home_pos)*2.)

    def move_fs(self, fs, *args, **kwargs):
        mm = fs_to_mm(fs)
        print('mm', mm+self.home_pos)
        self.move_mm(mm/2.+self.home_pos, *args, **kwargs)






