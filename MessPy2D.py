from functools import partial
from Config import config
from qtpy.QtCore import QTimer, Qt, QThread
from qtpy.QtGui import QFont, QGuiApplication
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget,
                            QPushButton, QLabel, QVBoxLayout, QSizePolicy,
                            QToolBar, QCheckBox)
import qtawesome as qta
from Plans import *
from QtHelpers import dark_palette, ControlFactory, make_groupbox, \
    ObserverPlot, ValueLabels
from ControlClasses import Controller, LastRead

START_QT_CONSOLE = False
if START_QT_CONSOLE:
    from qtconsole.inprocess import QtInProcessKernelManager
    from qtconsole.rich_jupyter_widget import RichJupyterWidget


HAS_SECOND_DELAYLINE = config.has_second_delaystage
HAS_ROTATION_STAGE = config.has_rot_stage


class SelectPlan(QWidget):
    def __init__(self, parent=None):
        super(SelectPlan, self).__init__(parent=parent)


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Messpy-2D Edition")
        # self.setWindowFlags
        self.controller = controller # type: Controller
        self.setup_toolbar()
        self.view = None

        cm = CommandMenu(parent=self)

        self.timer = QTimer(parent=self)
        self.timer.timeout.connect(controller.loop)
        self.timer.timeout.connect(QApplication.processEvents)
        self.toggle_run(True)

        dock_wigdets = []
        for c in [controller.cam, controller.cam2]:
            lr = c.last_read # type: LastRead
            op = ObserverPlot([(lr, 'probe_mean'), (lr, 'reference_mean')],
                              lr.sigProcessingCompleted)
            dw = QDockWidget('Readings', parent=self)
            dw.setWidget(op)
            dock_wigdets.append(dw)

            op2 = ObserverPlot([(lr, 'probe_std'), (lr, 'reference_std')],
                               lr.sigProcessingCompleted)
            op2.setYRange(0, 20)
            dw = QDockWidget('Readings - stddev', parent=self)
            dw.setWidget(op2)
            dock_wigdets.append(dw)

            op3 = ObserverPlot([(lr, 'probe_signal')],
                               lr.sigProcessingCompleted)
            dw = QDockWidget('Pump-probe signal', parent=self)
            dw.setWidget(op3)
            dock_wigdets.append(dw)

        if START_QT_CONSOLE:
            kernel_manager = QtInProcessKernelManager()
            kernel_manager.start_kernel(show_banner=False)
            kernel = kernel_manager.kernel

            kernel.gui = 'qt'
            kernel_client = kernel_manager.client()
            kernel_client.start_channels()
            kernel_client.namespace = self
            ipython_widget = RichJupyterWidget()
            ipython_widget.kernel_manager = kernel_manager
            ipython_widget.kernel_client = kernel_client
            kernel.shell.push({'controller': controller})

            dw4 = QDockWidget('Console', parent=self)
            dw4.setWidget(ipython_widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, dw4)
            dw4.close()
        for dw in dock_wigdets:
            self.addDockWidget(Qt.LeftDockWidgetArea, dw)

        self.splitDockWidget(dock_wigdets[0], dock_wigdets[3], Qt.Horizontal)
        self.splitDockWidget(dock_wigdets[1], dock_wigdets[4], Qt.Horizontal)
        self.splitDockWidget(dock_wigdets[2], dock_wigdets[5], Qt.Horizontal)
        self.setCentralWidget(cm)
        self.show()

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
                    self.viewer = PlanClass.viewer(plan)
                    self.viewer.show()

                    self.toggle_run(True)
            return f

        asl_icon = qta.icon('fa.percent', color='white')
        pp = QPushButton('2D Experiment', icon=asl_icon)
        pp.clicked.connect(plan_starter(TwoDStarter))
        tb.addWidget(pp)

        asl_icon = qta.icon('ei.graph', color='white')
        pp = QPushButton('Pump Probe', icon=asl_icon)
        pp.clicked.connect(plan_starter(PumpProbeStarter))
        tb.addWidget(pp)

        asl_icon = qta.icon('ei.barcode', color='white')
        pp = QPushButton('Scan Spectrum', icon=asl_icon)
        tb.addWidget(pp)

        asl_icon = qta.icon('ei.download', color='white')
        pp = QPushButton('Save current Spec', icon=asl_icon)
        tb.addWidget(pp)

    def toggle_run(self, bool):
        if bool:
            self.timer.start(10)
        else:
            self.timer.stop()

    def show_planview(self):
        if self.view is not None:
            self.view.show()

    def closeEvent(self, *args, **kwargs):
        config.write()
        super(MainWindow, self).closeEvent(*args, **kwargs)


class CommandMenu(QWidget):
    def __init__(self, parent=None):
        super(CommandMenu, self).__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._layout = QVBoxLayout(self)
        c = parent.controller # type: Controller

        self.add_plan_controls()

        self.add_loop_control(parent)
        gb = self.add_cam(c)
        self._layout.addWidget(gb)

        dls = self.add_delaystages(c)
        gb = make_groupbox(dls, "Delay")
        self._layout.addWidget(gb)

        if c.cam.cam.changeable_wavelength:
            gb = self.add_spec(c)
            self._layout.addWidget(gb)

        if HAS_ROTATION_STAGE:
            self.add_rot_stage()

        self.add_ext_view()

    def add_plan_controls(self):
        self.start_but = QPushButton('Start Plan')
        self._sp = SelectPlan(self)
        self.start_but.clicked.connect(lambda: self._sp.show())
        self.plan_label = QLabel('Default loop')
        self.plan_label.setAlignment(Qt.AlignHCenter)
        self.reopen_planview_but = QPushButton('Reopen Planview')
        self.reopen_planview_but.clicked.connect(self.parent().show_planview)
        for w in (self.start_but, self.plan_label, self.reopen_planview_but):
            self._layout.addWidget(w)

    def add_ext_view(self):
        def get_ext(i):
            lr = controller.last_read
            return lr.ext[:, ]

        vl = ValueLabels([('Ext 1', partial(get_ext, 1))])
        self._layout.addWidget(make_groupbox([vl], 'Ext.'))
        self._layout.addStretch(10)

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
        if c.cam2:
            bg_buttons.append(('Record BG2', c.cam2.get_bg))
        sc = ControlFactory('Shots', c.cam.set_shots, format_str='%d',
                            presets=[50, 200, 500, 1000], extra_buttons=bg_buttons)
        get_bg_button = QPushButton('Record Background')
        get_bg_button.clicked.connect(c.cam.get_bg)
        if c.cam2:
            get_bg_button.clicked.connect(c.cam.get_bg)
        gb = make_groupbox([sc], "ADC")
        return gb

    def add_delaystages(self, c):
        dl = controller.delay_line
        dl1c = ControlFactory('Delay 1', c.delay_line.set_pos, format_str='%.1f fs',
                              extra_buttons=[("Set Home", dl.set_pos)],
                              presets=[-50000, -10000, -1001, -50,
                                       50000, 10000, 1001, 50],
                              preset_func=lambda x: dl.set_pos(dl.get_pos() + x),
                              )
        c.delay_line.sigPosChanged.connect(dl1c.update_value)
        dls = [dl1c]
        if HAS_SECOND_DELAYLINE:
            dl2 = controller.delay_line_second
            dl2c = ControlFactory('Delay 2', dl2.set_pos, format_str='%.1f fs',
                                  extra_buttons=[("Set Home", dl2.set_pos)],
                                  )
            dls.append(dl2c)
            dl2.sigPosChanged.connect(dl2c.update_value)
        return dls

    def add_rot_stage(self):
        rs = ControlFactory('Angle', print,
                            format_str='%.1f deg')
        gb = make_groupbox([rs], "Rotation Stage")
        self._layout.addWidget(gb)

    def add_spec(self, c):
        if not c.cam.cam.changeable_wavelength:
            return ''
        spec = c.cam

        pre_fcn = lambda x: spec.set_wavelength(spec.get_wavelength() + x)
        spec_control = ControlFactory('Wavelength', c.cam.set_wavelength,
                                      format_str='%.1f nm',
                                      presets=[-100, -50, 50, 100],
                                      preset_func=pre_fcn)
        spec.sigWavelengthChanged.connect(spec_control.update_value)
        gb = make_groupbox([spec_control], "Spectrometer")
        return gb


if __name__ == '__main__':
    import sys
    import numpy as np

    sys._excepthook = sys.excepthook
    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)
    sys.excepthook = exception_hook


    controller = Controller()

    app = QApplication([])
    #app = QGuiApplication([], platformName='minimalegl ')

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
    from Plans.PumpProbeViewer import PumpProbeViewer
    from Plans.PumpProbe import PumpProbePlan

    #pp = PumpProbePlan(name='BlaBlub', controller=controller)
    controller.plan = None
    #pp.t_list = np.arange(-2, 5, 0.1)
    #pp.center_wl_list = [300, 600]
    #pi = PumpProbeViewer(pp)
    #ppi.show()
    mw.show()
    app.exec_()
