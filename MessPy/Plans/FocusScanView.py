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
                obs=[lambda: fs.scan_x.probe],
                signal=fsPlan.sigStepDone,
                x=fsPlan.scan_x.pos
            )

            self.x_ref_plot = ObserverPlot(
                obs=[lambda: fs.scan_x.ref],
                signal=fsPlan.sigStepDone,
                x=fsPlan.scan_x.pos
            )

            row = [self.x_probe_plot, self.x_ref_plot]
            if self.plan.power_meter:
                self.x_pw_plot = ObserverPlot(
                    obs=[lambda: fs.scan_x.extra],
                    signal=fsPlan.sigStepDone,
                    x=fsPlan.scan_x.pos
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
        fsPlan = self.plan
        if sx := fsPlan.scan_x:
            pr, ref, pw = sx.analyze()
            self.x_probe_plot.plot(sx.pos, pr.model, pen=pen)
            text = pg.TextItem(pr.make_text(), anchor=(0, 1.0))
            text.setPos(sx.pos[int(len(sx.pos) / 2)],
                        (np.max(sx.probe) + np.min(sx.probe)) / 2.)
            self.x_probe_plot.plotItem.addItem(text)

            self.x_ref_plot.plotItem.plot(sx.pos, ref.model, pen=pen)
            text = pg.TextItem(ref.make_text(), anchor=(0, 1.0))
            text.setPos(sx.pos[int(len(sx.pos) / 2)],
                        (np.max(sx.ref) + np.min(sx.ref)) / 2.)
            self.x_ref_plot.plotItem.addItem(text)

            if pw is not None:
                self.x_pw_plot.plotItem.plot(sx.pos, pw.model, pen=pen)
                text = pg.TextItem(pw.make_text(), anchor=(0, 1.0))
                text.setPos(sx.pos[int(len(sx.pos) / 2)],
                            (np.max(sx.extra) + np.min(sx.extra)) / 2.)
                self.x_pw_plot.plotItem.addItem(text)

        if sx := fsPlan.scan_y:
            pr, ref, pw = sx.analyze()
            self.y_probe_plot.plot(sx.pos, pr.model, pen=pen)
            text = pg.TextItem(pr.make_text(), anchor=(0, 1.0))
            text.setPos(sx.pos[int(len(sx.pos) / 2)],
                        (np.max(sx.probe) + np.min(sx.probe)) / 2.)
            self.y_probe_plot.plotItem.addItem(text)

            self.y_ref_plot.plotItem.plot(sx.pos, ref.model, pen=pen)
            text = pg.TextItem(ref.make_text(), anchor=(0, 1.0))
            text.setPos(sx.pos[int(len(sx.pos) / 2)],
                        (np.max(sx.ref) + np.min(sx.ref)) / 2.)
            self.y_ref_plot.plotItem.addItem(text)

            if pw is not None:
                self.y_pw_plot.plotItem.plot(sx.pos, pw.model, pen=pen)
                text = pg.TextItem(pw.make_text(), anchor=(0, 1.0))
                text.setPos(sx.pos[int(len(sx.pos) / 2)],
                            (np.max(sx.extra) + np.min(sx.extra)) / 2.)
                self.y_pw_plot.plotItem.addItem(text)


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
               {'name': 'steps', 'type': 'float', 'value': 0.02, 'step': 0.01}
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
        fs = FocusScan(
            name=p['Filename'],
            cam=self.candidate_cams[p['Cam']],
            meta=make_entry(p),
            shots=p['Shots'],
            x_parameters=x_stepper,
            y_parameters=y_stepper,
            fh=controller.sample_holder,
            power_meter=getattr(controller, 'power_meter', None),
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


