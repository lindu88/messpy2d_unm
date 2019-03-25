from xmlrpc.client import ServerProxy
from Config import config
from Instruments.interfaces import IDelayLine



if config.dl_server is None:
    config.dl_server = 'http://130.133.30.146:8000'

dlproxy = ServerProxy(config.dl_server)

class DelayLine(IDelayLine)
    def __init__(self):
        self.name = f"Remote DelayLine xmlrpc {config.dl_server}"

    def move_mm(self, mm, *args, **kwargs):
        dlproxy.move_mm(mm)

    def get_pos_mm(self):
        return dlproxy.get_mm()

    def is_moving(self):
        return dlproxy.is_moving()


dl = DelayLine()
dl.is_moving()