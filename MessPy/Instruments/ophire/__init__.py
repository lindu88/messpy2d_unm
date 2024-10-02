"Class implemting the IPowerMeter interface for the Starbright power meter"
import attr
from serial import Serial

from MessPy.Instruments.interfaces import IPowerMeter


@attr.dataclass(kw_only=True)
class Starbright(IPowerMeter):
    """Class for the Starbright power meter

    Only read out is implemented. The power meter is connected via RS232.
    """
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
