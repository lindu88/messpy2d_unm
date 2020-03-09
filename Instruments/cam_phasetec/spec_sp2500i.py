import serial, attr, time, logging, contextlib, atexit


@attr.s(auto_attribs=True)
class SP2500i:
    comport: str = 'COM4'
    pos_nm: float = 0
    port: object = attr.ib()

    @port.default
    def serial_connect(self):
        logging.info(f'SP2500i: Connecting to {self.comport}')
        port = serial.Serial(self.comport)
        port.timeout = 2
        return port

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

    def set_wavelength(self, nm: float, timeout: float):
        self._write(b'%.3f GOTO' % nm, timeout=timeout)

    def get_installed_gratings(self) -> str:
        self._write(b'GRATINGS?')
        resp = self.port.read(1000)
        return resp.decode('utf-8')

    def get_grating(self) -> int:
        self._write(b'GRATING?')
        resp = self._readline()
        return int(resp)

    def set_grating(self, grating: int):
        self._write(b'%d GRATING' % grating, timeout=5)

    def reset(self):
        self._write(b'MONO-RESET')




if __name__ == "__main__":
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    spec = SP2500i()
    wl = spec.get_wavelength()
    #print(spec.get_installed_gratings())
    #print(f'Current wavelength {spec.get_wavelength()}')
    #print(f'Current grating {spec.get_grating()}')
    spec.set_wavelength(wl + 200)
    atexit.register()