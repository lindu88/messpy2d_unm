from functools import partial
from Config import config
from qtpy.QtCore import QTimer, Qt, QThread, QSettings
from qtpy.QtGui import QFont, QIntValidator
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget,
                            QPushButton, QLabel, QVBoxLayout, QSizePolicy, QFormLayout,
                            QToolBar, QCheckBox)
import qtawesome as qta
from Instruments.interfaces import IAOMPulseShaper
from Plans import *
from Plans.ShaperCalibPlan import CalibScanView, CalibPlan
from QtHelpers import dark_palette, ControlFactory, make_groupbox, \
    ObserverPlot, ValueLabels
from SampleMoveWidget import MoveWidget
from ControlClasses import Controller

START_QT_CONSOLE = False
if START_QT_CONSOLE:
    from qtconsole.inprocess import QtInProcessKernelManager
    from qtconsole.rich_jupyter_widget import RichJupyterWidget


class SelectPlan(QWidget):
    def __init__(self, parent=None):
        super(SelectPlan, self).__init__(parent=parent)


class MainWindow(QMainWindow):
    def __init__(self, controller: Controller):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Messpy-2D Edition")
        # self.setWindowFlags
        self.controller = controller # type: Controller
        self.setup_toolbar()
        self.view = None


        self.cm = CommandMenu(parent=self)
        self.timer = QTimer()
        self.timer.timeout.connect(controller.loop)

        self.toggle_run(True)
        self.xaxis = {}

        dock_wigdets = []
        for c in controller.cam_list:
            lf = controller.loop_finnished
            lr = c.last_read
            self.xaxis[c] = c.wavelengths.copy()

            obs = [lambda i=i, c=c: c.last_read.lines[i, :] for i in range(c.cam.lines)]
            op = ObserverPlot(obs,
                              lf, x=c.disp_axis)
            dw = QDockWidget('Readings', parent=self)
            dw.setWidget(op)
            dock_wigdets.append(dw)

            w = QWidget()
            w.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            form_layout = QFormLayout()
            w.setLayout(form_layout)

            for i, n in enumerate(c.cam.line_names):
                line = op.lines[op.observed[i]]
                col = line.opts['pen'].color()
                print(col.name())
                lb = QLabel('<font color="%s">%s</font>' % (col.name(), n))
                cb = QCheckBox()
                cb.setChecked(True)
                form_layout.addRow(lb, cb)
                cb.toggled.connect(line.setVisible)

            dw = QDockWidget("Line Plot Controls")
            dw.setWidget(w)
            dock_wigdets.append(dw)

            obs = [lambda i=i, c=c: c.last_read.stds[i, :] for i in range(c.cam.std_lines)]
            op2 = ObserverPlot(obs,
                               lf, x=c.disp_axis)
            op2.setYRange(0, 8)
            dw = QDockWidget('Readings - stddev', parent=self)
            dw.setWidget(op2)
            dock_wigdets.append(dw)
            w = QWidget()
            w.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            form_layout = QFormLayout()
            w.setLayout(form_layout)


            for i, n in enumerate(c.cam.std_names):
                line = op2.lines[op2.observed[i]]
                col = line.opts['pen'].color()
                print(col.name())
                lb = QLabel('<font color="%s">%s</font>' % (col.name(), n))
                cb = QCheckBox()
                cb.setChecked(True)
                form_layout.addRow(lb, cb)
                cb.toggled.connect(line.setVisible)

            dw = QDockWidget("Std Plot Controls")
            dw.setWidget(w)
            dock_wigdets.append(dw)



            obs = [lambda i=i, c=c: c.last_read.signals[i, :] for i in range(c.cam.sig_lines)]
            op3 = ObserverPlot(obs, lf, x=c.disp_axis)
            dw = QDockWidget('Pump-probe signal', parent=self)
            dw.setWidget(op3)
            dock_wigdets.append(dw)

            w = QWidget()
            w.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            form_layout = QFormLayout()
            w.setLayout(form_layout)
            for i, n in enumerate(c.cam.sig_names):
                line = op3.lines[op3.observed[i]]
                col = line.opts['pen'].color()
                print(col.name())
                lb = QLabel('<font color="%s">%s</font>' % (col.name(), n))
                cb = QCheckBox()
                cb.setChecked(True)

                form_layout.addRow(lb, cb)
                cb.toggled.connect(line.setVisible)
            dw = QDockWidget("Sig Plot Controls")
            dw.setWidget(w)
            dock_wigdets.append(dw)


        for dw in dock_wigdets:
            self.addDockWidget(Qt.LeftDockWidgetArea, dw)

        #self.splitDockWidget(dock_wigdets[2], dock_wigdets[3], Qt.Horizontal)
        if len(dock_wigdets) > 3:
            self.splitDockWidget(dock_wigdets[0], dock_wigdets[1], Qt.Horizontal)
            self.splitDockWidget(dock_wigdets[2], dock_wigdets[3], Qt.Horizontal)
            self.splitDockWidget(dock_wigdets[4], dock_wigdets[5], Qt.Horizontal)
        self.setCentralWidget(self.cm)
        #self.obs_plot = [i.getWidget() for i in dock_wigdets]
        self.controller.cam.sigRefCalibrationFinished.connect(self.plot_calib)
        self.readSettings()
    def plot_calib(self, k1, k2):
        import pyqtgraph as pg
        win = pg.PlotWindow()
        win.plotItem.plot(k1)
        win.plotItem.plot(k2)
        win.show()
        self._win = win

    def setup_toolbar(self):
        self.tb = self.addToolBar('Begin Plan')
        tb = self.tb

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

        #asl_icon = qta.icon('fa.percent', color='white')
        #pp = QPushButton('2D Experiment', icon=asl_icon)
        #pp.clicked.connect(plan_starter(TwoDStarter))
        #tb.addWidget(pp)

        asl_icon = qta.icon('ei.graph', color='white')
        pp = QPushButton('Pump Probe', icon=asl_icon)
        pp.clicked.connect(plan_starter(PumpProbeStarter))
        tb.addWidget(pp)

        asl_icon = qta.icon('ei.barcode', color='white')
        pp = QPushButton('Scan Spectrum', icon=asl_icon)
        pp.clicked.connect(plan_starter(ScanSpectrumStarter))
        tb.addWidget(pp)

        asl_icon = qta.icon('ei.download', color='white')
        pp = QPushButton('Save current Spec', icon=asl_icon)
        tb.addWidget(pp)

        asl_icon = qta.icon('ei.graph', color='white')
        pp = QPushButton('Focus Scan', icon=asl_icon)
        pp.clicked.connect(plan_starter(FocusScanStarter))
        tb.addWidget(pp)

        asl_icon = qta.icon('mdi.chart-line', color='white')
        pp = QPushButton('Shaper Calibration', icon=asl_icon)

        def start_calib():
            c = self.controller
            fs = CalibPlan(cam=c.cam.cam,
                       move_func=c.cam.set_wavelength,
                       points=range(5500, 6500, 5))
            self.cal_viewer = CalibScanView(fs)
            c.async_plan = True
            fs.sigPlanDone.connect(lambda: setattr(c, 'async_plan', False))
            self.cal_viewer.show()
        pp.clicked.connect(start_calib)
        tb.addWidget(pp)

        alg_icon = qta.icon('mdi.chart-line', color='white')
        pp = QPushButton('Show alignment helper')
        pp.clicked.connect(self.show_alignment_helper)
        tb.addWidget(pp)



    def toggle_run(self, bool):
        if bool:
            self.timer.start(30)
        else:
            self.timer.stop()

    def toggle_wl(self, c):
        print(c)
        self.xaxis[c][:] = 1e7/self.xaxis[c][:]

    def show_planview(self):
        if self.view is not None:
            self.view.show()
        else:
            self.view = self.plan_class.viewer(self.controller.plan)

    def show_alignment_helper(self):
        self._ah = AlignmentHelper(self.controller)
        self._ah.show()
        #dw = QDockWidget(self._ah)
        #self.addDockWidget(Qt.LeftDockWidgetArea, dw)


    def closeEvent(self, event):
        print('closing')

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
        c = parent.controller # type: Controller

        self.add_plan_controls()

        self.add_loop_control(parent)
        gb = self.add_cam(c)
        self._layout.addWidget(gb)

        dls = self.add_delaystages(c)
        gb = make_groupbox(dls, "Delay")
        self._layout.addWidget(gb)

        for cam in c.cam_list:
            if cam.cam.changeable_wavelength:
                gb = self.add_spec(cam)
                self._layout.addWidget(gb)

        if c.rot_stage:
            self.add_rot_stage(c.rot_stage)
        if c.sample_holder:
            self.add_sample_holder(c.sample_holder)
        #self.add_ext_view()

    def add_plan_controls(self):
        self.start_but = QPushButton('Start Plan')
        self._sp = SelectPlan(self)
        self.start_but.clicked.connect(lambda: self._sp.show())
        self.plan_label = QLabel('Default loop')
        self.plan_label.setAlignment(Qt.AlignHCenter)
        self.pause_plan_but = QPushButton("Pause plan")
        self.pause_plan_but.setCheckable(True)
        c = self.parent().controller  # type: Controller
        def switch_pause(ev):
            c.pause_plan = self.pause_plan_but.isChecked()
        self.pause_plan_but.clicked.connect(switch_pause)

        self.reopen_planview_but = QPushButton('Reopen Planview')
        self.reopen_planview_but.setEnabled(False)
        self.reopen_planview_but.clicked.connect(self.parent().show_planview)
        for w in (self.start_but, self.plan_label,
                  self.reopen_planview_but, self.pause_plan_but):
            self._layout.addWidget(w)

    def add_ext_view(self):
        def get_ext(i):
            lr = controller.last_read
            return lr.ext[:, ]

        vl = ValueLabels([('Ext 1', partial(get_ext, 1))])
        self._layout.addWidget(make_groupbox([vl], 'Ext.'))
        #self._layout.addStretch(10)

    def add_loop_control(self, parent):
        cb_running = QPushButton('Running',
                                 icon=qta.icon('fa.play', color='white'))
        cb_running.setCheckable(True)
        cb_running.setChecked(True)
        cb_running.toggled.connect(parent.toggle_run)
        gb = make_groupbox([self.start_but, cb_running, self.plan_label],
                           'Plans')
        self._layout.addWidget(gb)
        return gb

    def add_cam(self, c: Controller):
        bg_buttons = [('Record BG', c.cam.get_bg)]
        if hasattr(c.cam, 'calibrate_ref'):
            bg_buttons.append(('Record Ref. Calib.', c.cam.calibrate_ref))
        if c.cam2:
            bg_buttons.append(('Record BG2', c.cam2.get_bg))
        sc = ControlFactory('Shots', c.cam.set_shots, format_str='%d',
                            presets=[20, 100, 500, 1000], extra_buttons=bg_buttons)
        sc.edit_box.setValidator(QIntValidator(10, 50000))
        c.cam.sigShotsChanged.connect(sc.update_value)
        c.cam.set_shots(config.shots)

        gb = make_groupbox([sc], "ADC")
        return gb


    def add_delaystages(self, c):
        dl = controller.delay_line
        dl1c = ControlFactory('Delay 1', lambda x: c.delay_line.set_pos(x, do_wait=False), format_str='%.1f fs',
                              extra_buttons=[("Set Home", dl.set_home)],
                              presets=[-50000, -10000, -1001, -50,
                                       50000, 10000, 1001, 50],
                              preset_func=lambda x: dl.set_pos(dl.get_pos() + x, do_wait=False),
                              )
        c.delay_line.sigPosChanged.connect(dl1c.update_value)
        dl1c.update_value(c.delay_line.get_pos())
        dls = [dl1c]
        if c.delay_line_second:
            dl2 = controller.delay_line_second
            dl2c = ControlFactory('Delay 2', dl2.set_pos, format_str='%.1f fs',
                                  extra_buttons=[("Set Home", dl2.set_pos)],
                                  )
            dls.append(dl2c)
            dl2.sigPosChanged.connect(dl2c.update_value)
        return dls

    def add_rot_stage(self, rs ):
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

    def add_spec(self, cam):
        if not cam.cam.changeable_wavelength:
            return ''
        spec = cam
        pre_fcn = lambda x: spec.set_wavelength(spec.get_wavelength() + x)

        def calc_and_set_wl(s):
            s = s.strip()
            try:
                if s[-1] == 'c':
                    wl =  1e7/float(s[:-1])
                else:
                    wl =  float(s)
                spec.set_wavelength(wl)
            except ValueError:
                pass

        spec_control = ControlFactory('Wavelength', calc_and_set_wl,
                                      format_str='%.1f nm',
                                      presets=[-100, -50, 50, 100],
                                      preset_func=pre_fcn,)

        spec.sigWavelengthChanged.connect(spec_control.update_value)
        spec.sigWavelengthChanged.emit(spec.get_wavelength())

        l = [spec_control]
        if spec.cam.changeable_slit:
            pre_fcn = lambda x: spec.set_slit(spec.get_slit() + x)
            slit_control = ControlFactory('Slit (μm)', cam.set_slit, presets=[-10, 10], preset_func=pre_fcn)
            slit_control.update_value(spec.get_slit())
            spec.sigSlitChanged.connect(slit_control.update_value)
            l.append((slit_control))
        cb = QCheckBox('Use Wavenumbers')
        l[-1].layout().addRow( cb)
        gb = make_groupbox(l, f"Spec: {cam.cam.name}")
        cb.clicked.connect(cam.set_disp_wavelengths)
        return gb

    def add_shaper(self, sh : IAOMPulseShaper):
        l = []
        if sh.grating_1 is not None:
            cf1 = ControlFactory('Grating 1', sh.grating_1.set_degrees, sh.grating_2.sigDegreesChanged)
            cf2 = ControlFactory('Grating 2', sh.grating_2.set_degrees, sh.grating_2.sigDegreesChanged)
            l += [cf1, cf2]

        cb_chopped = QCheckBox('Chopped')
        cb_phase_cycled = QCheckBox('Phase Cycling')
        cb_running = QCheckBox('Active')

        def set_mode():
            sh.set_mode(cb_chopped.isChecked(), cb_phase_cycled.isChecked())
            sh.set_running(cb_running.isChecked())

        cb_chopped.stateChanged.connect(set_mode)
        cb_phase_cycled.stateChanged.connect(set_mode)
        cb_running.stateChanged.connect(set_mode)
        l += [cb_chopped, cb_phase_cycled, cb_running]
        gb = make_groupbox(l, 'Shaper')
        return gb


if __name__ == '__main__':
    import sys
    import qasync
    import asyncio as aio
    app = QApplication([])
    app.setOrganizationName("USD");
    app.setApplicationName("MessPy3");
    loop = qasync.QEventLoop()
    aio.set_event_loop(loop)
    sys._excepthook = sys.excepthook
    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)
    sys.excepthook = exception_hook


    controller = Controller()



    font = QFont()

    app.setStyle('Fusion')
    #app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setPalette(dark_palette)
    ss = """
        QMainWindow { font-size: 20pt;}
        QToolTip { color: #ffffff; background-color: #2a82da;
                       border: 1px solid white; }
    """
    app.setStyleSheet(ss)
    font.setPointSize(11)
    font.setStyleStrategy(QFont.PreferQuality)
    app.setFont(font)
    mw = MainWindow(controller=controller)

    mw.showMaximized()
    app.exec()

    #app.aboutToQuit = lambda x: controller.shutdown()




