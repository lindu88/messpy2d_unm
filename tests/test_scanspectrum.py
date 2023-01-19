from pytest import fixture
from MessPy.Plans import ScanSpectrum
from MessPy.ControlClasses import Controller
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QTimer
from pytestqt import qtbot

from MessPy.Config import config


@fixture
def controller(qtbot):
    controller = Controller()
    #controller._timer = QTimer()
    # controller._timer.timeout.connect(controller.loop)
    # controller._timer.start(10)
    return controller


def test_scan_spectrum(controller, qtbot, tmp_path):
    config.data_directory = tmp_path
    ss = ScanSpectrum(
        name='test',
        meta={},
        cam=controller.cam,
        timeout=3,
        wl_list=[10, 50, 100],
    )

    # with qtbot.waitSignal(ss.sigPlanFinished):
    while not ss.make_step():
        pass
    assert len(list(tmp_path.glob('*.*'))) == 2
