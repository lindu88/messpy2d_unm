import atom.api as a
from enaml import imports, qt
from enaml.core.api import d_

class Freq(a.Atom):
    wl = a.Float()
    wn = a.Property()

    @wn.setter
    def _set_wn(self, wn):
        if wn != 0:
            self.wl = 1e7/wn

    @wn.getter
    def _get_wn(self, wn):
        return 1e7/self.wl

class ScanSpectrumSettings(a.Atom):
    wl_min = a.Float(400)
    wl_max = a.Float(2000)
    steps = a.Int(100)
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

    fv = ScanSettingsView(ss=ScanSpectrumSettings())
    fv.initialize()
    fv.activate_proxy()
    w.setCentralWidget(fv.proxy.widget)
    w.show()
    app.start()


