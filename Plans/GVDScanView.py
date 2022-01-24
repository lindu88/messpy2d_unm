import numpy as np
import pyqtgraph.parametertree as pt
from qtpy.QtWidgets import QWidget, QLabel, QVBoxLayout
from qtawesome import icon

from ControlClasses import Controller
from QtHelpers import ObserverPlot, PlanStartDialog, vlay, make_entry
from .GVDScan import GVDScan


class GVDScanView(QWidget):
    def __init__(self, gvd_plan: GVDScan, *args, **kwargs):
        super(GVDScanView, self).__init__(*args, **kwargs)
        self.plan = gvd_plan

        self.gvd_amp = ObserverPlot(
            obs=[lambda: self.plan.probe2.mean(1)],
            signal=gvd_plan.sigPointRead,
            x=gvd_plan.gvd_list)

        self.gvd_sig = ObserverPlot(
            obs=[lambda: self.plan.signal[:, :, 0].mean(1), lambda: self.plan.signal[:, :, 2].mean(1)],
            signal=gvd_plan.sigPointRead,
            x=gvd_plan.gvd_list)

        self.info_label = QLabel("Info")
        self.setLayout(vlay(self.gvd_sig, self.gvd_amp, self.info_label))
        self.plan.sigPointRead.connect(self.update_label)
        self.setWindowTitle("GVD Scan")
        self.setWindowIcon(icon('fa5s.tired'))

    def update_label(self):
        p = self.plan
        s = f"Point {p.gvd_idx}/ {len(p.gvd_list)}"
        self.info_label.setText(s)


class GVDScanStarter(PlanStartDialog):
    experiment_type = 'FocusScan'
    title = "Focus Scan"
    viewer = GVDScanView

    def setup_paras(self):
        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp_focus'},
               {'name': 'Shots', 'type': 'int', 'max': 2000, 'value': 100},
               {'name': 'Start Val', 'type': 'float', 'value': -300, 'step': 1},
               {'name': 'End Val', 'type': 'float', 'value': -100, 'step': 1},
               {'name': 'Step', 'type': 'float', 'value': 1, 'step': 0.1},
               {'name': 'Scan Mode', 'type': 'list', 'values': ['GVD', 'TOD', 'FOD']},
               {'name': 'Waiting time (s)', 'type': 'float', 'value': 0.1, 'step': 0.05},
               {'name': 'GVD', 'type': 'float', 'value': 0, 'step': 1},
               {'name': 'TOD', 'type': 'float', 'value': 0, 'step': 1},
               {'name': 'FOD', 'type': 'float', 'value': 0, 'step': 1},

               ]
        self.p = pt.Parameter.create(name='Exp. Settings', type='group', children=tmp)
        params = [self.p]
        self.paras = pt.Parameter.create(name='Focus Scan', type='group', children=params)
        # config.last_pump_probe = self.paras.saveState()

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')

        self.save_defaults()
        start = min(p['Start Val'], p['End Val'])
        end = max(p['Start Val'], p['End Val'])
        gvd_list = np.arange(start, end, p['Step'])
        fs = GVDScan(
            aom = controller.shaper,
            meta=make_entry(self.paras),
            gvd=p['GVD'],
            tod=p['TOD'],
            fod=p['FOD'],
            name=p['Filename'],
            cam=controller.cam,
            gvd_list=gvd_list,
            scan_mode=p['Scan Mode'],
            waiting_time=p['Waiting time (s)'],
            shots=p['Shots']
        )
        return fs
