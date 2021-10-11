import logging
import multiprocessing as mp
import xmlrpc.server
import xmlrpc.client as c
import typing as T
import atexit

logger = logging.Logger("Supervisor")

class DelayLineServer:
    def nix(self):
        return "Hi"


def make_serv():
    dl = DelayLineServer()
    serv = xmlrpc.server.SimpleXMLRPCServer(('127.0.0.1', 80))
    serv.register_instance(dl)
    serv.serve_forever()

def get_req():
    prox = c.ServerProxy("http://127.0.0.1:80")
    while True:
        print(prox.nix())

#@attr.s(auto_attribs=True)
class ProcessHandler:
    def __init__(self, addr):
        self.processes: T.List[mp.Process] = []
        atexit.register(self.shutdown)

    def shutdown(self):
        for p in self.processes:
            p.kill()

    

if __name__ == "__main__":
    p1 = mp.Process(target=make_serv)
    p1.start()
    p2 = mp.Process(target=get_req)
    p2.start()