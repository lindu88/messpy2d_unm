from xmlrpc.client import ServerProxy
from Config import config
from Instruments.interfaces import IDelayLine
import wrapt



config.dl_server = 'http://130.133.30.146:8000'

dlproxy = ServerProxy(config.dl_server)


class DelayLine(IDelayLine):

    def __init__(self):
        self.name = f"Remote DelayLine xmlrpc {config.dl_server}"
        super().__init__(name=self.name, pos_sign=-1)


    @wrapt.synchronized
    def move_mm(self, mm, *args, **kwargs):
        dlproxy.move_mm(mm)

    @wrapt.synchronized
    def get_pos_mm(self):
        return dlproxy.get_mm()

    @wrapt.synchronized
    def is_moving(self):
        return dlproxy.is_moving()


dl = DelayLine()
dl.is_moving()