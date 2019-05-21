from xmlrpc.client import ServerProxy
from Config import config
from Instruments.interfaces import IRotationStage, IShutter
from wrapt import synchronized
import attr
from Signal import Signal

config.rot_server = 'http://130.133.30.146:8003'
rot = ServerProxy(config.rot_server)

config.shutter_server = 'http://130.133.30.146:8002'
shutter = ServerProxy(config.shutter_server)

@attr.s
class RotationStage(IRotationStage):
    name = attr.ib('xmlrpc-RotStage')

    @synchronized
    def set_degrees(self, deg: float):
        deg = float(deg)
        rot.set_pos(deg)
        #self.sigDegreesChanged.emit(deg)


    @synchronized
    def get_degrees(self) -> float:
        pos = rot.get_pos()
        return pos

    @synchronized
    def is_moving(self):
        return rot.is_moving()

@attr.s
class Shutter(IShutter):
    name = attr.ib('xmlrpc-Shutter')

    @synchronized
    def is_open(self) -> bool:
        return shutter.is_open()

    @synchronized
    def toggle(self):
        shutter.toggle()
        self.sigShutterToggled.emit(self.is_open())


if __name__ == '__main__':
    sh = Shutter()
    sh.toggle()
    rs = RotationStage()
    print(rs.get_degrees())
    rs.set_degrees(30)
    print(rs.is_moving())

