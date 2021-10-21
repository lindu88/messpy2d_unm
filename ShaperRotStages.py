from Instruments.RotationStage import RotationStage
from Instruments.dac_px.pxdac import AOM

import attr
from qtpy import QtGui, QtWidgets, QtCore
from QtHelpers import ControlFactory, vlay, hlay

@attr.s
class ShaperControl(QtWidgets.QWidget):
    rs1 : RotationStage = attr.ib()
    rs2 : RotationStage = attr.ib()
    aom: AOM = attr.ib()

    def __attrs_post_init__(self):
        super(ShaperControl, self).__init__()
        c1 = ControlFactory("Grating1", apply_fn=self.rs1.set_degrees, update_signal=self.rs1.signals.sigDegreesChanged)
        c2 = ControlFactory("Grating2", apply_fn=self.rs2.set_degrees, update_signal=self.rs2.signals.sigDegreesChanged)

        slider_lbl = QtWidgets.QLabel("bla")

        self.slider = QtWidgets.QSlider()
        self.slider.setOrientation(	0x1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(lambda x: slider_lbl.setText('%0.1f' % (x / 1000)))
        self.slider.setValue(int(self.aom.amp_fac * 1000))
        self.slider.valueChanged.connect(lambda x: aom.set_wave_amp(x/1000))


        self.setLayout(vlay((hlay((slider_lbl, self.slider)), vlay([c1, c2]))))



if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    aom = AOM()
    r1 = RotationStage(name="Grating1", comport="COM5")
    r2 = RotationStage(name="Grating2", comport="COM6")

    sc = ShaperControl(rs1=r1, rs2=r2, aom=aom)
    sc.show()

    app.exec_()
