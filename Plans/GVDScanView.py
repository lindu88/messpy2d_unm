from QtHelpers import ObserverPlot, PlanStartDialog, QPushButton, QVBoxLayout
from qtpy.QtWidgets import QWidget
import pyqtgraph.parametertree as pt
from .GVDScan import GVDScan
from .common_meta import samp

class GVDScanView(QWidget):
    def __init__(self, fsPlan: GVDScan, *args, **kwargs):
        super(GVDScanView, self).__init__(*args, **kwargs)

        self.gvd_amp = ObserverPlot(
            obs=(fsPlan, "probe[:, 2]"),
            signal=fsPlan.sigStepDone,
            x=fsPlan.gvd_list)

        self.gvd_sig = ObserverPlot(
            obs=(fsPlan, "signal[:, 2]"),
            signal=fsPlan.sigStepDone,
            x=fsPlan.gvd_list)

        layout = QVBoxLayout(self)
        layout.addLayout(self.gvd)

        self.setLayout(layout)


class GVDScanStarter(PlanStartDialog):
    experiment_type = 'FocusScan'
    title = "Focus Scan"
    viewer = GVDScanView

    def setup_paras(self):
        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp_focus'},
               {'name': 'Operator', 'type': 'str', 'value': ''},
               {'name': 'Shots', 'type': 'int', 'max': 2000, 'value': 100},
               {'name': 'Start Val', 'type': 'float', 'value': -300_000, 'step': 1000},
               {'name': 'End Val', 'type': 'float', 'value': -100_000, 'step': 1000},
               {'name': 'Scan Mode', 'type': 'list', 'values': ['GVD', 'TOD', 'FOD']}

               ]


        self.p = pt.Parameter.create(name='Exp. Settings', type='group', children=tmp)
        params = [self.p]
        self.paras = pt.Parameter.create(name='Focus Scan', type='group', children=params)
        #config.last_pump_probe = self.paras.saveState()

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')



        self.save_defaults()
        fs = GVDScan(
            name=p['Filename'],
            meta=None,
            cam=controller.cam,



        )
        return fs