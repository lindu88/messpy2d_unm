from typing import Dict

import serial, attr,  logging, atexit
from Instruments.interfaces import ISpectrograph

@attr.s(auto_attribs=True)
class SP2500i(ISpectrograph):
    comport: str = 'COM4'
    pos_nm: float = 0
    port: serial.Serial = attr.ib()
    changeable_slit: bool = False
    changeable_wavelength: bool = True
    name: str = 'SP2500i'
    _last_grating: int = attr.ib()

    @port.default
    def serial_connect(self):
        logging.info(f'SP2500i: Connecting to {self.comport}')
        port = serial.Serial(self.comport, baudrate=9600*12)
        port.timeout = 2
        atexit.register(self.disconnect)
        return port

    @_last_grating.default
    def _read_grating(self):
        return self.get_grating()

    def _write(self, cmd: bytes, await_resp: bool = True,
               timeout: float = 2):
        logging.debug(f'SP2500i: Writing cmd: {cmd}')
        self.port.write(cmd + b'\r')
        if await_resp:
            logging.debug(f'SP2500i: Waiting for ok: {cmd}')
            resp = self._readline(timeout=timeout)
            if resp[-2:] != b'ok':
                raise IOError(f"Command not responded with OK, got '{resp}' instead")
            return resp
        else:
            return 

    def _readline(self, timeout=None) -> bytes:
        logging.debug(f'SP2500i: Reading line')
        old_timeout = self.port.timeout
        if timeout is None:
            timeout = old_timeout
        self.port.timeout = timeout
        resp = self.port.read_until(b'\r\n')
        logging.debug(f'SP2500i: Got {resp}')
        self.port.timeout = old_timeout
        return resp[:-2]

    def get_wavelength(self) -> float:
        resp = self._write(b'?NM')
        return float(resp.strip(b' ').split(b' ')[0])

    def set_wavelength(self, nm: float, timeout: float = 4):
        self._write(b'%.3f GOTO' % nm, timeout=timeout)
        self.sigWavelengthChanged.emit(nm)

    def get_installed_gratings(self) -> str:
        self._write(b'?GRATINGS', False)
        resp = self.port.read(1000)
        return resp.decode('utf-8')

    @property
    def gratings(self) -> Dict[int, str]:
        return {1: '75', 2: '30'}

    def get_grating(self) -> int:
        self._write(b'?GRATING', False)
        resp = self._readline()[:-2]
        self._last_grating = int(resp)
        return int(resp)

    def set_grating(self, grating: int):
        print("set_grating", grating)
        self._write(b'%d GRATING' % grating, timeout=35)
        self.sigGratingChanged.emit(grating)
        self._last_grating = grating
        print("set grating", grating)

    def reset(self):
        self._write(b'MONO-RESET')

    def disconnect(self):
        self.port.close()

if __name__ == "__main__":
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    spec = SP2500i()
    wl = spec.get_wavelength()
    print(spec.get_installed_gratings())
    #print(f'Current wavelength {spec.get_wavelength()}')
    print(f'Current grating {spec.get_grating()}')
    spec.set_wavelength(wl + 200)
    spec.set_grating(2)
