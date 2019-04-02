import atom.api as a
from enaml import imports, qt
from enaml.core.api import d_
import time

class Meta(a.Atom):
    creation_time = a.Float(factory=time.time)
    operator = a.Unicode()

class SampleInfo(a.Atom):
    sample_name = a.Unicode('')
    solvent_name = a.Unicode('')
    thickness = a.Unicode('')
    annotations = a.Unicode('')


class SetupInfo(a.Atom):
    excitation_wavelength = a.Float()
    excitation_energy_mw = a.Float()

class FocusInfo(a.Atom):
    "All units are given in μm"
    pump_x = a.Float(0)
    pump_y = a.Float(0)
    probe_x = a.Float(0)
    probe_y = a.Float(0)


class ScanSpectrumSettings(a.Atom):
    wl_min = a.Float(400)
    wl_max = a.Float(2000)
    steps = a.Int(100)
    shots = a.Int(50)
    linear_in = a.Enum('wl', 'wn')
    path = a.Str('')

    @a.observe('wl_min')
    def bla(self, ch):
        print(f'bla{self.wl_min}')


if __name__ == '__main__':
    from enaml.qt.qt_application import QtApplication
    from qtpy import QtWidgets

    app = QtApplication()
    with imports():
        from scan_spectrum import ScanSettingsView
    w = QtWidgets.QMainWindow()

    fv = ScanSettingsView(ss=ScanSpectrumSettings(), si=SampleInfo())
    fv.initialize()
    fv.activate_proxy()
    w.setCentralWidget(fv.proxy.widget)
    w.show()
    app.start()


