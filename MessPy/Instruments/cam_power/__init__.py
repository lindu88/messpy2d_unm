from qtpy import QtWidgets, QtCore
import instrumental.drivers.cameras.uc480

from MessPy.Instruments.interfaces import IPowerMeter
import attr
from instrumental import instrument

@attr.dataclass(kw_only=True)
class PowerCam(IPowerMeter):
    name: str = 'UC 480'
    _cam = instrumental.drivers.cameras.uc480.UC480_Camera = instrument('UC480_Camera')
    exposure_ms: float = 1.1

    def __attrs_post_init__(self):
        self._cam.set_auto_exposure(False)

    def get_state(self) -> dict:
        return dict(exposure_ms=self.exposure_ms)

    def get_power(self):
        img = self._cam.grab_image(exposure_time='%.2fms'%self.exposure_ms)
        return img.mean()

if __name__ == '__main__':
    import pyqtgraph as pg
    #app = QtWidgets.QApplication([])
    #win = pg.PlotWidget()
    #image = pg.ImageItem()
    #win.addItem(image)
    cam = PowerCam()
    #image.setImage(cam._cam.grab_image())
    print(cam.get_power())
    #win.show()
    #app.exec_()




