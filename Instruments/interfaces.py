import typing, abc, time, attr, threading
import xmlrpc.server as rpc

class IDevice(abc.ABC):
    def init(self):
        pass

    def shutdown(self):
        pass

    @classmethod
    def create_remote(cls, *args, **kwargs):
        '''Creates an instance and puts it into a 
        xmlrpc server which is started in a seperated thread.
        
        Returns (obj, server, thread)'''
        obj = cls(*args, **kwargs)
        server = rpc.SimpleXMLRPCServer('')
        server.register_instance(obj)
        server.register_introspection_functions()
        thr = threading.Thread(target=server.serve_forever)
        return obj, server, thr

# Defining a minimal interface for each hardware
@attr.s
class ICam(IDevice):
    shots: int = attr.ib(50)
    lines: int = attr.ib(2)
    channels: int = attr.ib(100)
    background: tuple = attr.ib((0, 0))

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

    def shutdown(self):
        pass


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
class IDelayLine(IDevice):
    home_pos: float = attr.ib(0.)
    pos_sign: float = 1

    @abc.abstractmethod
    def move_mm(self, mm, *args, **kwargs):
        pass

    @abc.abstractmethod
    def get_pos_mm(self):
        pass

    def get_pos_fs(self):
        return self.pos_sign * mm_to_fs((self.get_pos_mm()-self.home_pos)*2.)

    def move_fs(self, fs, wait_for_move=False, *args, **kwargs):
        mm = self.pos_sign*fs_to_mm(fs)
        print('mm', mm+self.home_pos)
        self.move_mm(mm/2.+self.home_pos, *args, **kwargs)
        if wait_for_move:
            while self.is_moving():
                time.sleep(0.2)

    @abc.abstractmethod
    def is_moving(self):
        return False

    def def_home(self):
        self.home_pos = self.get_pos_mm()

    def shutdown(self):
        pass


class IShutter(abc.ABC):
    @abc.abstractmethod
    def toggle(self):
        pass

    @abc.abstractmethod
    def is_open(self) -> bool:
        pass

    def open(self):
        if self.is_open():
            return
        else:
            self.toggle()

    def close(self):
        if not self.is_open():
            return
        else:
            self.toggle()

    def shutdown(self):
        pass


class IRotationStage(abc.ABC):
    @abc.abstractmethod
    def set_degrees(self, deg: float):
        pass

    @abc.abstractmethod
    def get_degrees(self) -> float:
        pass

    @abc.abstractmethod
    def is_moving(self):
        pass

class LissajousScanner(abc.ABC):
    @abc.abstractmethod
    def set_pos_mm(self, x=None, y=None):
        pass

    def set_vel_mm(self):
        pass

    @abc.abstractmethod
    def is_moving(self) -> typing.Tuple[bool, bool]:
        pass

    def shutdown(self):
        pass