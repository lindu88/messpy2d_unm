from ControlClasses import Controller
from Config import config
from qtpy.QtCore import QTimer, Qt, QSettings
from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget, QPushButton, QLabel, QSizePolicy,
                            QFormLayout, QMessageBox,
                            QCheckBox)
import qtawesome as qta
from Instruments.interfaces import IAOMPulseShaper, ICam
from Plans import *
from Plans.ShaperCalibPlan import CalibScanView, CalibPlan
from QtHelpers import ControlFactory, make_groupbox, \
    ValueLabels, ObserverPlotWithControls, hlay
from SampleMoveWidget import MoveWidget

from functools import partial

import qtawesome as qta
from qtpy.QtCore import QTimer, Qt, QSettings
from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget, QPushButton, QLabel, QSizePolicy,
                            QFormLayout, QMessageBox,
                            QCheckBox)

from Config import config
from ControlClasses import Controller
from Instruments.interfaces import IAOMPulseShaper, ICam
from Plans import *
from Plans.ShaperCalibPlan import CalibScanView, CalibPlan
from QtHelpers import ControlFactory, make_groupbox, \
    ValueLabels, ObserverPlotWithControls, hlay
from SampleMoveWidget import MoveWidget


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Messpy-2D Edition")
        self.setWindowIcon(qta.icon('fa.play'))
        self.controller = controller  # controller

        self.setup_toolbar()

        self.cm = CommandMenu(parent=self)
        self.timer = QTimer()
        self.timer.timeout.connect(controller.loop)

        self.toggle_run(True)
        self.xaxis = {}

        dock_wigdets = []
        for c in controller.cam_list:
            lf = controller.loop_finished
            lr = c.last_read
            self.xaxis[c] = c.wavelengths.copy()

            obs = [lambda i=i, c=c: c.last_read.lines[i, :] for i in range(c.cam.lines)]
            op = ObserverPlotWithControls(c.cam.line_names, obs, lf, x=c.disp_axis)
            dw = QDockWidget('Readings', parent=self)
            dw.setWidget(op)
            dock_wigdets.append(dw)

            obs = [lambda i=i, c=c: c.last_read.stds[i, :] for i in range(c.cam.std_lines)]
            op2 = ObserverPlotWithControls(c.cam.std_names, obs, lf, x=c.disp_axis)
            op2.obs_plot.setYRange(0, 8)
            dw = QDockWidget('Readings - stddev', parent=self)
            dw.setWidget(op2)
            dock_wigdets.append(dw)

            obs = [lambda i=i, c=c: c.last_read.signals[i, :] for i in range(c.cam.sig_lines)]
            op3 = ObserverPlotWithControls(c.cam.sig_names, obs, lf, x=c.disp_axis)
            dw = QDockWidget('Pump-probe signal', parent=self)
            dw.setWidget(op3)
            dock_wigdets.append(dw)

        for dw in dock_wigdets:
            self.addDockWidget(Qt.LeftDockWidgetArea, dw)

        if len(dock_wigdets) > 3:
            self.splitDockWidget(dock_wigdets[0], dock_wigdets[3], Qt.Horizontal)
            self.splitDockWidget(dock_wigdets[1], dock_wigdets[4], Qt.Horizontal)
            self.splitDockWidget(dock_wigdets[2], dock_wigdets[5], Qt.Horizontal)
        self.setCentralWidget(self.cm)

        self.controller.cam.sigRefCalibrationFinished.connect(self.plot_calib)
        self.readSettings()

    def plot_calib(self, k1, k2):
        import pyqtgraph as pg
        win = pg.PlotWidget()
        win.plotItem.plot(k1)
        win.plotItem.plot(k2)
        win.show()
        self._win = win

    def setup_toolbar(self):
        self.toolbar = self.addToolBar('Begin Plan')
        tb = self.toolbar

        def plan_starter(PlanClass):
            def f():
                plan, ok = PlanClass.start_plan(self.controller)
                if ok:
                    print('ok')
                    self.toggle_run(False)
                    self.controller.plan = plan
                    self.plan_class = PlanClass
                    self.viewer = PlanClass.viewer(plan)
                    self.viewer.show()
                    self.cm.reopen_planview_but.setEnabled(True)
                    self.controller.pause_plan = False
                    self.toggle_run(True)

            return f

        plans = [
            ('Pump Probe', 'ei.graph', PumpProbeStarter),
            ('Scan Spectrum', 'ei.barcode', ScanSpectrumStarter),
        ]
        if self.controller.shaper is not None:
            plans += [('GVD Scan', 'ei.graph', GVDScanStarter)]
            plans += [('2D Measurement', 'ei.graph', AOMTwoDStarter)]

        for text, icon, starter in plans:
            asl_icon = qta.icon(icon, color='white')
            pp = QPushButton(text, icon=asl_icon)
            pp.clicked.connect(plan_starter(starter))
            tb.addWidget(pp)

        asl_icon = qta.icon('mdi.chart-line', color='white')
        pp = QPushButton('Shaper Calibration', icon=asl_icon)

        def start_calib():
            c = self.controller
            fs = CalibPlan(cam=c.cam,
                           dac=c.shaper,
                           move_func=c.cam.set_wavelength,
                           points=range(5500, 6500, 5))
            self.cal_viewer = CalibScanView(fs)
            fs.sigTaskReady.connect(lambda x: c.async_tasks.append(x))
            c.async_plan = True
            # c.async_tasks = self.cal_viewer.task
            fs.sigPlanDone.connect(lambda: setattr(c, 'async_plan', False))
            self.cal_viewer.show()

        pp.clicked.connect(start_calib)
        tb.addWidget(pp)

        alg_icon = qta.icon('mdi.chart-line', color='white')
        pp = QPushButton('Show alignment helper', icon=asl_icon)
        pp.clicked.connect(self.show_alignment_helper)
        tb.addWidget(pp)

    def toggle_run(self, bool):
        if bool:
            self.timer.start(5)
        else:
            self.timer.stop()

    def toggle_wl(self, c):
        self.xaxis[c][:] = 1e7 / self.xaxis[c][:]

    def show_planview(self):
        if self.view is not None:
            self.view.show()
        else:
            self.view = self.plan_class.viewer(self.controller.plan)

    def show_alignment_helper(self):
        self._ah = AlignmentHelper(self.controller)
        self._ah.show()
        # dw = QDockWidget(self._ah)
        # self.addDockWidget(Qt.LeftDockWidgetArea, dw)

    def closeEvent(self, *args, **kwargs):
        config.save()
        settings = QSettings()
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('windowState', self.saveState())
        super(MainWindow, self).closeEvent(*args, **kwargs)

    def readSettings(self):
        settings = QSettings()
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
            self.restoreState(settings.value("windowState"))


class CommandMenu(QWidget):
    def __init__(self, parent=None):
        super(CommandMenu, self).__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._layout = QFormLayout(self)
        c = parent.controller  # type: Controller

        self.add_plan_controls()

        gb = self.add_cam(c)
        self._layout.addWidget(gb)

        dls = self.add_delaystages(c)
        gb = make_groupbox(dls, "Delay")
        self._layout.addWidget(gb)

        for cam in c.cam_list:
            if cam.changeable_wavelength:
                gb = self.add_spec(cam)
                self._layout.addWidget(gb)

        if c.rot_stage:
            self.add_rot_stage(c.rot_stage)
        if c.sample_holder:
            self.add_sample_holder(c.sample_holder)
        if c.shaper is not None:
            self.add_shaper(c.shaper)

    def add_plan_controls(self):
        # self.plan_label = QLabel('Default loop')
        # self.plan_label.setAlignment(Qt.AlignHCenter)
        self.pause_plan_but = QPushButton("Pause plan",
                                          icon=qta.icon('fa.pause', color="white"))
        self.pause_plan_but.setCheckable(True)
        c = self.parent().controller  # type: Controller

        def switch_pause(ev):
            c.pause_plan = self.pause_plan_but.isChecked()

        self.pause_plan_but.clicked.connect(switch_pause)

        self.reopen_planview_but = QPushButton('Reopen Planview')
        self.reopen_planview_but.setEnabled(False)
        self.reopen_planview_but.clicked.connect(self.parent().show_planview)
        cb_running = QPushButton('Running',
                                 icon=qta.icon('fa.play', color='white'))
        cb_running.setCheckable(True)
        cb_running.setChecked(True)
        cb_running.toggled.connect(self.parent().toggle_run)
        for w in (self.reopen_planview_but, self.pause_plan_but, cb_running):
            self._layout.addWidget(w)

    def add_ext_view(self):
        def get_ext(i):
            lr = controller.last_read
            return lr.ext[:, ]

        vl = ValueLabels([('Ext 1', partial(get_ext, 1))])
        self._layout.addWidget(make_groupbox([vl], 'Ext.'))
        # self._layout.addStretch(10)

    def add_cam(self, c: Controller):
        bg_buttons = [('Record BG', c.cam.get_bg)]
        if hasattr(c.cam, 'calibrate_ref'):
            bg_buttons.append(('Record Ref. Calib.', c.cam.calibrate_ref))
        if c.cam2:
            bg_buttons.append(('Record BG2', c.cam2.get_bg))
        if c.cam.cam.can_validate_pixel:
            bg_buttons.append(("Mark valid pix", c.cam.cam.mark_valid_pixel))
            bg_buttons.append(("Delete valid pix", c.cam.cam.delete_valid_pixel))
        sc = ControlFactory('Shots', c.cam.set_shots, format_str='%d',
                            presets=[20, 100, 500, 1000], extra_buttons=bg_buttons)
        sc.edit_box.setValidator(QIntValidator(10, 50000))
        c.cam.sigShotsChanged.connect(sc.update_value)
        c.cam.set_shots(config.shots)

        gb = make_groupbox([sc], "ADC")
        return gb

    def add_delaystages(self, c):
        dl = c.delay_line
        dl1c = ControlFactory('Delay 1', lambda x: c.delay_line.set_pos(x, do_wait=False), format_str='%.1f fs',
                              extra_buttons=[("Set Home", dl.set_home)],
                              presets=[-50000, -10000, -1000.0001, -50,
                                       50000, 10000, 1000.0001, 50],
                              preset_func=lambda x: dl.set_pos(dl.get_pos() + x, do_wait=False),
                              )
        c.delay_line.sigPosChanged.connect(dl1c.update_value)
        dl1c.update_value(c.delay_line.get_pos())
        dls = [dl1c]
        if c.delay_line_second:
            dl2 = c.delay_line_second
            dl2c = ControlFactory('Delay 2', dl2.set_pos, format_str='%.1f fs',
                                  extra_buttons=[("Set Home", dl2.set_pos)],
                                  )
            dls.append(dl2c)
            dl2.sigPosChanged.connect(dl2c.update_value)
        return dls

    def add_rot_stage(self, rs):
        rsi = ControlFactory('Angle', rs.set_degrees,
                             format_str='%.1f deg', presets=[0, 45])

        rsi.update_value(rs.get_degrees())
        rs.sigDegreesChanged.connect(rsi.update_value)
        gb = make_groupbox([rsi], "Rotation Stage")

        self._layout.addWidget(gb)

    def add_sample_holder(self, saho):
        move_wid = MoveWidget(saho)
        gb = make_groupbox([move_wid], "Sample Holder")
        self._layout.addWidget(gb)

    def add_spec(self, cam: ICam):
        if not cam.changeable_wavelength:
            return ''
        spec = cam.cam.spectrograph
        pre_fcn = lambda x: spec.set_wavelength(spec.get_wavelength() + x)

        def calc_and_set_wl(s):
            s = s.strip()
            try:
                if s[-1] == 'c':
                    wl = 1e7 / float(s[:-1])
                else:
                    wl = float(s)
                spec.set_wavelength(wl)
            except ValueError:
                pass

        spec_control = ControlFactory('Wavelength', calc_and_set_wl,
                                      format_str='%.1f nm',
                                      presets=[-100, -50, 50, 100],
                                      preset_func=pre_fcn, )

        spec.sigWavelengthChanged.connect(spec_control.update_value)
        spec.sigWavelengthChanged.emit(spec.get_wavelength())

        l = [spec_control]

        if spec.changeable_slit:
            pre_fcn = lambda x: spec.spectrograph.set_slit(spec.get_slit() + x)
            slit_control = ControlFactory('Slit (μm)', spec.set_slit, presets=[-10, 10], preset_func=pre_fcn)
            slit_control.update_value(spec.get_slit())
            spec.sigSlitChanged.connect(slit_control.update_value)
            l.append(slit_control)

        cb = QCheckBox('Use Wavenumbers')
        l[-1].layout().addRow(cb)
        if len(spec.gratings) > 1:
            gratings = spec.gratings
            cur_grating = spec.get_grating()
            lbl = QLabel('G: %s' % gratings[cur_grating])
            btns = [lbl]
            for idx, name in gratings.items():
                btn = QPushButton(name)
                btn.clicked.connect(lambda: partial(spec.set_grating, idx))
                btn.clicked.connect(lambda: lbl.setText('G: %s' % name))
                btn.setFixedWidth(70)
                btns.append(btn)

            l.append(hlay(btns, add_stretch=1))
        gb = make_groupbox(l, f"Spec: {cam.cam.name}")
        cb.clicked.connect(cam.set_disp_wavelengths)
        return gb

    def add_shaper(self, sh: IAOMPulseShaper):
        from ShaperRotStages import ShaperControl

        self.shaper_controls = ShaperControl(sh.rot1, sh.rot2, sh)
        but = QPushButton("Shaper Contorls")
        but.clicked.connect(self.shaper_controls.show)
        self._layout.addWidget(but)
        return


if __name__ == '__main__':
    import sys
    import qasync
    import asyncio as aio
    import traceback

    app = QApplication([])

    import qdarkstyle

    app.setOrganizationName("USD")
    app.setApplicationName("MessPy3")

    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, tb):
        emsg = QMessageBox()
        emsg.setWindowModality(Qt.WindowModal)
        traceback.print_tb(tb)
        tb = traceback.format_tb(tb)
        emsg.setText('Exception raised')
        emsg.setInformativeText(''.join(tb))
        emsg.setStandardButtons(QMessageBox.Abort | QMessageBox.Ok)
        result = emsg.exec_()
        print(result)
        if not result == QMessageBox.Ok:
            sys._excepthook(exctype, value, tb)
            sys.exit(1)
        else:
            pass


    sys.excepthook = exception_hook

    # font = QFont('Roboto')

    # app.setStyle('Fusion')
    # app.setAttribute(Qt.AA_EnableHighDpiScaling)
    # app.setPalette(dark_palette)
    ss = """
        QMainWindow { font-size: 20pt;}
        QToolTip { color: #ffffff; background-color: #2a82da;
                       border: 1px solid white; }
    """
    ss = qdarkstyle.load_stylesheet()
    app.setStyleSheet(ss)
    # font.setPointSize(9)
    # font.setStyleStrategy(QFont.PreferQuality)
    # app.setFont(font)

    mw = MainWindow(Controller())
    mw.showMaximized()
    loop = qasync.QEventLoop()

    aio.set_event_loop(loop)
    aio.get_event_loop().set_debug(True)
    app.exec()

    # app.aboutToQuit = lambda x: controller.shutdown()
