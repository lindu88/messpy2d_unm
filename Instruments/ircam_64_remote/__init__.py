"""Using the IR-ADC over network. Uses direct zmq messages."""
import numpy as np
from Instruments.interfaces import ICam
from Config import config
import zmq

if config.ir_server_addr is None:
    config.ir_server_addr = 'tcp://130.133.30.146:8001'

config.ir_server_addr = 'tcp://localhost:8001'
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(config.ir_server_addr)

import attr

@attr.s(auto_attribs=True)
class Cam(ICam):
    name: str = 'Remote IR 32x2'
    shots: int = config.shots
    lines: int = 2
    sig_lines: int = 1
    channels: int = 32
    ext_channels: int = 3
    changeable_wavelength: bool = False

    def read_cam(self):
        socket.send_pyobj(('read_cam', None))
        #data = socket.recv()
        #data = np.frombuffer(b, dtype=args['dtype'], shape=args['shape'])
        arr =  socket.recv_pyobj()
        ans = arr[:, :32], arr[:, 32:64], arr[:, 65] > 2, arr[:, [77]]
        return ans

    def set_shots(self, shots: int):

        shots = int(shots)
        socket.send_pyobj(('set_shots', shots))
        self.shots = shots
        b = socket.recv_pyobj()


cam = Cam()
print(cam.read_cam())