from qtpy import QtWidgets, QtCore
from serial import Serial

from MessPy.Instruments.interfaces import IPowerMeter
import attr


@attr.dataclass(kw_only=True)
class Starbright(IPowerMeter):
    name: str = 'Starbright'
    _serial: Serial = Serial("COM9", baudrate=19200)

    def read_power(self) -> float:
        self._serial.write(b"$SP\r\n")
        ans = self._serial.read_until(b'\r\n')
        print(ans)
        return float(ans[1:-2])


if __name__ == '__main__':
    s = Starbright()
    print(s.read_power())