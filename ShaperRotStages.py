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
        preset = [-1, -0.1, -0.01] + [0.01, 0.1, 1][::-1]
        f = self.rs1.move_relative
        c1 = ControlFactory("Grating1", apply_fn=self.rs1.set_degrees,
                            update_signal=self.rs1.signals.sigDegreesChanged, format_str='%.2f',
                            presets=preset, preset_func=f, preset_rows=3)

        f = self.rs2.move_relative
        c2 = ControlFactory("Grating2", apply_fn=self.rs2.set_degrees,
                            update_signal=self.rs2.signals.sigDegreesChanged,  format_str='%.2f',
                            presets=preset, preset_func=f, preset_rows=3)
        c1.update_value(self.rs1.get_degrees())
        c2.update_value(self.rs2.get_degrees())
        slider_lbl = QtWidgets.QLabel("bla")

        self.slider = QtWidgets.QSlider()
        self.slider.setOrientation(	0x1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(lambda x: slider_lbl.setText('%0.1f' % (x / 1000)))
        self.slider.setValue(int(self.aom.amp_fac * 1000))
        self.slider.valueChanged.connect(lambda x: aom.set_wave_amp(x/1000))

        self.chopped = QtWidgets.QCheckBox("Chopped")
        self.chopped.setChecked(self.aom.chopped)
        self.chopped.toggled.connect(lambda x: setattr(self.aom, 'chopped', x))

        self.pc = QtWidgets.QCheckBox("Phase Cycle")
        self.pc.setChecked(self.aom.phase_cycle)
        self.pc.toggled.connect(lambda x: setattr(self.aom, 'phase_cycle', x))

        self.apply = QtWidgets.QPushButton("Apply Waveform")
        self.apply.clicked.connect(lambda x: self.aom.generate_waveform())
        self.cali = QtWidgets.QPushButton("Full Mask")
        self.cali.clicked.connect(self.aom.load_full_mask)
        self.setLayout(vlay((hlay((slider_lbl, self.slider)),
                             vlay([c1, c2]),
                             self.chopped,
                             self.pc,
                             hlay((self.apply, self.cali)))))

    def disp_controls(self):

        d = {
            'GVD': ( -300, 300, 1),
            'TOD': ( -1000, 1000, 10),
            'FOD': ( -1000, 1000, 10),
        }

        for i in ['GVD', 'TOD', 'FOD']:
            slider = QtWidgets.QSlider()
            slider_lbl = QtWidgets.QLabel()
            slider.setOrientation(0x1)
            slider.setMinimum(d[i][0])
            slider.setMaximum(d[i][1])
            slider.setSingleStep(d[i][2])
            slider.valueChanged.connect(lambda x: slider_lbl.setText('%0.1f' % (x / 1000)))
            #slider.setValue(int(self.aom.amp_fac * 1000))
            def setter(val):
                aom.set_dispersion_correct()
            slider.valueChanged.connect(lambda x: aom.set_dispersion_correct())


if __name__ == '__main__':

    app = QtWidgets.QApplication([])
    #from qt_material import apply_stylesheet
    #apply_stylesheet(app, 'light_blue.xml')
    aom = AOM()

    r1 = RotationStage(name="Grating1", comport="COM5")
    r2 = RotationStage(name="Grating2", comport="COM6")

    sc = ShaperControl(rs1=r1, rs2=r2, aom=aom)
    sc.show()

    app.exec_()
