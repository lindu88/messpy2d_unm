from Instruments.RotationStage import RotationStage
from Instruments.dac_px import AOM

import attr
from qtpy import QtGui, QtWidgets, QtCore
from QtHelpers import ControlFactory, vlay, hlay

from pyqtgraph.parametertree import Parameter, ParameterTree

dispersion_params = [
    dict(name='GVD', type='float', value=0),
    dict(name='TOD', type='float', value=0),
    dict(name='FOD', type='float', value=0)
]


@attr.s
class ShaperControl(QtWidgets.QWidget):
    rs1: RotationStage = attr.ib()
    rs2: RotationStage = attr.ib()
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
                            update_signal=self.rs2.signals.sigDegreesChanged, format_str='%.2f',
                            presets=preset, preset_func=f, preset_rows=3)
        c1.update_value(self.rs1.get_degrees())
        c2.update_value(self.rs2.get_degrees())
        slider_lbl = QtWidgets.QLabel("bla")

        self.slider = QtWidgets.QSlider()
        self.slider.setOrientation(0x1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(lambda x: slider_lbl.setText('%0.1f' % (x / 1000)))
        self.slider.setValue(int(self.aom.amp_fac * 1000))
        self.slider.valueChanged.connect(lambda x: aom.set_wave_amp(x / 1000))

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

        self.pt = ParameterTree()
        self.disp_param = Parameter(dispersion_params)
        self.disp_param.sigValueChanged.connect(self.update_disp)
        self.pt.setParameters(self.disp_param)
        self.setLayout(vlay((hlay((slider_lbl, self.slider)),
                             vlay([c1, c2]),
                             self.chopped,
                             self.pc,
                             self.pt,
                             hlay((self.apply, self.cali)))))

        def update_disp(self):
            for i in ['gvd', 'tod', 'fod']:
                setattr(self.aom, i, self.disp_param[i])
            self.aom.update_dispersion_compensation()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    # from qt_material import apply_stylesheet
    # apply_stylesheet(app, 'light_blue.xml')
    aom = AOM()
    from Instruments.RotationStage import RotationStage

    r1 = RotationStage(name="Grating1", comport="COM5")
    r2 = RotationStage(name="Grating2", comport="COM6")

    sc = ShaperControl(rs1=r1, rs2=r2, aom=aom)
    sc.show()

    app.exec_()
