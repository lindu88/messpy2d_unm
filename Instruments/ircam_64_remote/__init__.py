"""Using the IR-ADC over network. Uses direct zmq messages."""
import numpy as np
from Instruments.interfaces import ICam, Reading
from Config import config
import zmq
import xmlrpc.client
config.ir_server_addr = 'tcp://130.133.30.146:5555'
if config.ir_server_addr is None:
    config.ir_server_addr = 'tcp://130.133.30.146:5555'

#config.ir_server_addr = 'tcp://localhost:8001'
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(config.ir_server_addr)
triax = xmlrpc.client.ServerProxy('http://130.133.30.146:8001', allow_none=True)

from typing import List
import attr

@attr.s(auto_attribs=True)
class Cam(ICam):
    name: str = 'Remote IR 32x2'
    shots: int = config.shots
    line_names: List = ['Probe', 'Ref']
    std_names: List = ['Probe', 'Ref', 'Probe/Ref']
    sig_names: List = ['Probe', 'Probe/Ref']
    channels: int = 32
    ext_channels: int = 3
    changeable_wavelength: bool = True
    changeable_slit: bool = True

    def read_cam(self):
        socket.send_json(('read', ''))
        #data = socket.recv()
        #data = np.frombuffer(b, dtype=args['dtype'], shape=args['shape'])
        shape, dtype = socket.recv_json()
        arr = socket.recv()
        arr = np.frombuffer(arr, dtype=dtype).reshape(shape)/3276.7
        ans = arr[:, :32], arr[:, 32:64], arr[:, -1] > 2, arr[:, [77]]
        return ans

    def make_reading(self) -> Reading:
        a, b, chopper, ext = self.read_cam()
        tmp = np.stack((a, b))
        if self.background is not None:
            tmp -= self.background[:, None, :]
        tm = tmp.mean(1)
        with np.errstate(invalid='ignore', divide='ignore'):
            ref = b/a
            ref_std = ref.std(0)/ref.mean(0)
            signal = -1000*np.log10(b[chopper, :].mean(0)/b[~chopper, :].mean(0))
            signal2 = -1000*np.log10(ref[chopper, :].mean(0) / ref[~chopper, :].mean(0))
        return Reading(
            lines=tm,
            stds=100*np.concatenate((tmp.std(1)/tm, ref_std[None, :])),
            signals=np.stack((signal, signal2)),
            valid=True,
        )

    def set_shots(self, shots: int):
        shots = int(shots)
        socket.send_json(('set_shots', shots))
        self.shots = shots
        b = socket.recv_json()

    def get_wavelength_array(self, center_wl):
        li = triax.get_arr(center_wl)
        return np.array(li)

    def set_wavelength(self, wl: float):
        try:
            wl = float(wl)
            triax.set_wl(wl)
        except ValueError:
            pass

    def get_wavelength(self):
        return triax.get_wl()

    def get_slit(self):
        return triax.get_slit()

    def set_slit(self, slit):
        try:
            slit = float(slit)
            triax.set_slit(slit)
        except ValueError:
            pass



cam = Cam()

if __name__  == '__main__':
    print(cam.get_wavelength())
    #cam.set_wavelength(1e7/1700)
    #print(cam.read_cam())
    print(cam.get_wavelength_array(5000), cam.get_wavelength_array(5500))
