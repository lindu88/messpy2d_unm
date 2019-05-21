from xmlrpc.client import ServerProxy
from Config import config
from Instruments.interfaces import IDelayLine
import wrapt



config.dl_server = 'http://130.133.30.235:8000'

dlproxy = ServerProxy(config.dl_server)


class DelayLine(IDelayLine):

    def __init__(self):
        self.name = f"Remote DelayLine xmlrpc {config.dl_server}"
        super().__init__(name=self.name, pos_sign=-1, home_pos=dlproxy.get_home())

    @wrapt.synchronized
    def move_mm(self, mm, *args, **kwargs):
        return dlproxy.move_mm(mm)

    @wrapt.synchronized
    def get_pos_mm(self):
        return dlproxy.get_mm()

    @wrapt.synchronized
    def is_moving(self):
        return dlproxy.is_moving()

    @wrapt.synchronized
    def def_home(self):
        self.home_pos = self.get_pos_mm()
        return dlproxy.def_home()


dl = DelayLine()
if __name__ == '__main__':

    dl.is_moving()
    print(dlproxy.get_home(), dl.home_pos)
#print(dl.def_home())