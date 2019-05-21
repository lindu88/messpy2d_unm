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


class FocusInfo(a.Atom):
    "All units are given in μm"
    pump_x = a.Int(0)
    pump_y = a.Int(0)
    probe_x = a.Int(0)
    probe_y = a.Int(0)
    ref_x = a.Int(0)
    ref_y = a.Int(0)


class SetupInfo(a.Atom):
    excitation_wavelength = a.Float()
    excitation_energy_mw = a.Float()
    focus = a.Typed(FocusInfo)
    shots = a.Int()

class ScanSpectrumSettings(a.Atom):
    wl_min = a.Float(400)
    wl_max = a.Float(2000)
    steps = a.Int(100)
    shots = a.Int(50)
    linear_in = a.Enum('wl', 'wn')
    path = a.Str('')


class PumpProbeSettings(a.Atom):
    switch_pol = a.Bool(False)
    center_wls = a.List(a.Float)
    delay_times = a.List(a.Float)


if __name__ == '__main__':
    from enaml.qt.qt_application import QtApplication
    from qtpy import QtWidgets

    app = QtApplication()
    with imports():
        from scan_spectrum import ScanSettingsView
    w = QtWidgets.QMainWindow()

    fv = ScanSettingsView(ss=ScanSpectrumSettings(), si=SampleInfo(), focus=FocusInfo())
    fv.initialize()
    fv.activate_proxy()
    w.setCentralWidget(fv.proxy.widget)
    w.show()
    app.start()


