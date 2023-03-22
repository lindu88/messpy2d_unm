import numpy as np
import pyqtgraph as pg
import pyqtgraph.parametertree as pt
from qtpy.QtWidgets import QWidget, QPushButton

from .FocusScan import FocusScan

from qtpy.QtWidgets import QVBoxLayout, QMessageBox
from qtpy.QtCore import QTimer
from MessPy.ControlClasses import Controller
from MessPy.QtHelpers import vlay, hlay, PlanStartDialog, ObserverPlot, make_entry
from .PlanBase import sample_parameters


class FocusScanView(QWidget):
    def __init__(self, fsPlan: FocusScan, *args, **kwargs):
        super(FocusScanView, self).__init__(*args, **kwargs)
        self.plan = fsPlan
        fs = fsPlan
        lay = []
        if fsPlan.scan_x:
            self.x_probe_plot = ObserverPlot(
                obs=[lambda: fs.scan_x.get_data()[1]],
                signal=fsPlan.sigStepDone,
                x=lambda: fsPlan.scan_x.get_data()[0]
            )

            self.x_ref_plot = ObserverPlot(
                obs=[lambda: fs.scan_x.get_data()[2]],
                signal=fsPlan.sigStepDone,
                x=lambda: fsPlan.scan_x.get_data()[0]
            )

            row = [self.x_probe_plot, self.x_ref_plot]
            if self.plan.power_meter:
                self.x_pw_plot = ObserverPlot(
                    obs=[lambda: fs.scan_x.get_data()[3]],
                    signal=fsPlan.sigStepDone,
                    x=lambda: fsPlan.scan_x.get_data()[0]
                )
                row.append(self.x_pw_plot)
            lay.append(hlay(row))
        if fsPlan.scan_y:
            self.y_probe_plot = ObserverPlot(
                obs=[lambda: fs.scan_y.probe],
                signal=fsPlan.sigStepDone,
                x=fsPlan.scan_y.pos
            )

            self.y_ref_plot = ObserverPlot(
                obs=[lambda: fs.scan_y.ref],
                signal=fsPlan.sigStepDone,
                x=fsPlan.scan_y.pos
            )
            row = [self.y_probe_plot, self.y_ref_plot]
            if self.plan.power_meter:
                self.y_pw_plot = ObserverPlot(
                    obs=[lambda: fs.scan_y.extra],
                    signal=fsPlan.sigStepDone,
                    x=fsPlan.scan_y.pos
                )
                row.append(self.y_pw_plot)
            lay.append(hlay(row))

        self.plot_layout = vlay(lay)
        fsPlan.sigFitDone.connect(lambda: self.button.setEnabled(True))
        fsPlan.sigFitDone.connect(self.plot_fit)
        self.button = QPushButton('Save Scan', self)
        self.button.setEnabled(False)
        self.button.clicked.connect(fsPlan.save)
        fname = fsPlan.get_file_name()[0]
        self.button.clicked.connect(lambda: QMessageBox.information(
            self, 'Results Saved', 'At %s' % str(fname)))

        layout = QVBoxLayout(self)
        layout.addLayout(self.plot_layout)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def plot_fit(self):
        pen = pg.mkPen(color='#e377c2', width=2)

        for axis in ('x', 'y'):
            scan = getattr(self.plan, f'scan_{axis}', None)
            if scan is not None:
                pr, ref, pw = scan.analyze()
                probe_plot, ref_plot = getattr(self, f'{axis}_probe_plot'), getattr(self, f'{axis}_ref_plot')
                probe_plot.plot(pr.pos, pr.model, pen=pen)
                ref_plot.plot(ref.pos, ref.model, pen=pen)
                if pw is not None:
                    pw_plot = getattr(self, f'{axis}_pw_plot')
                    pw_plot.plot(pw.pos, pw.model, pen=pen)
                else:
                    pw_plot = None
                for plot, data, fit in [(probe_plot, scan.probe, pr), (ref_plot, scan.ref, ref), (pw_plot, scan.extra if pw is not None else None, pw)]:
                    if data is not None:
                        text = pg.TextItem(fit.make_text(), anchor=(0, 1.0))
                        text.setPos(scan.pos[int(len(scan.pos) / 2)], (np.max(data) + np.min(data)) / 2.)
                        plot.plotItem.addItem(text)


class FocusScanStarter(PlanStartDialog):
    experiment_type = 'FocusScan'
    title = "Focus Scan"
    viewer = FocusScanView

    def setup_paras(self):
        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp_focus'},
               {'name': 'Operator', 'type': 'str', 'value': ''},
               {'name': 'Shots', 'type': 'int', 'max': 2000, 'value': 100},
               {'name': 'Scan x', 'type': 'bool', 'value': True},
               {'name': 'Scan y', 'type': 'bool', 'value': True},
               {'name': 'Start x', 'type': 'float', 'value': 0, 'step': 0.1},
               {'name': 'End x', 'type': 'float', 'value': 1, 'step': 0.1},
               {'name': 'Start y', 'type': 'float', 'value': 0, 'step': 0.1},
               {'name': 'End y', 'type': 'float', 'value': 1, 'step': 0.1},
               {'name': 'steps', 'type': 'float', 'value': 0.02, 'step': 0.01},
               {'name': 'Power', 'type': 'bool', 'value': True},
               ]

        self.candidate_cams = {c.cam.name: c for c in self.controller.cam_list}
        tmp.append(dict(name='Cam', type='list',
                   values=self.candidate_cams.keys()))
        self.p = pt.Parameter.create(
            name='Exp. Settings', type='group', children=tmp)
        params = [sample_parameters, self.p]
        self.paras = pt.Parameter.create(
            name='Focus Scan', type='group', children=params)
        # config.last_pump_probe = self.paras.saveState()

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')
        s = self.paras.child('Sample')
        x_stepper = []
        y_stepper = []

        if p['Scan x']:
            x_stepper = [p['Start x'], p['End x'], p['steps']]
        if p['Scan y']:
            y_stepper = [p['Start y'], p['End y'], p['steps']]

        self.save_defaults()
        if p['Power']:
            power = getattr(controller, 'power_meter', None)
        else:
            power = None
        fs = FocusScan(
            name=p['Filename'],
            cam=self.candidate_cams[p['Cam']],
            meta=make_entry(p),
            shots=p['Shots'],
            x_parameters=x_stepper,
            y_parameters=y_stepper,
            z_points=None,
            fh=controller.sample_holder,
            power_meter=power,
        )
        return fs


if __name__ == '__main__':
    import sys

    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook

    app = QApplication([])
    con = Controller()
    timer = QTimer()
    timer.timeout.connect(con.loop)

    fs = FocusScan()
    con.plan = fs
    ppi = FocusScanViewViewer(fs)
    ppi.show()
    # formlayout.fedit(start_form)
    timer.start(50)
    try:
        app.exec_()
    except:
        print('fds')


