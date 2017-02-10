from functools import partial
from Config import config
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtpy.QtCore import QTimer, Qt
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget,
                            QPushButton, QLabel, QVBoxLayout, QSizePolicy,
                            QToolBar, QCheckBox)

import qtawesome as qta
from Plans import *
from QtHelpers import dark_palette, ControlFactory, make_groupbox, \
    ObserverPlot, ValueLabels
from ControlClasses import Controller

HAS_SECOND_DELAYLINE = config.has_second_delay
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

        cm = CommandMenu(parent=self)

        self.timer = QTimer(parent=self)
        self.timer.timeout.connect(controller.loop)
        self.timer.timeout.connect(QApplication.processEvents)
        self.timer.start(10)
        lr = controller.last_read
        op = ObserverPlot([(lr, 'probe_mean'), (lr, 'reference_mean')],
                          self.timer.timeout)
        dw = QDockWidget('Readings', parent=self)
        dw.setWidget(op)
        op2 = ObserverPlot([(lr, 'probe_std'), (lr, 'reference_std')],
                           self.timer.timeout)
        op2.setYRange(0, 20)
        dw2 = QDockWidget('Readings - stddev', parent=self)
        dw2.setWidget(op2)
        op3 = ObserverPlot([(lr, 'probe_signal')],
                           self.timer.timeout)
        dw3 = QDockWidget('Pump-probe signal', parent=self)
        dw3.setWidget(op3)

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
        dw4.close()

        self.addDockWidget(Qt.LeftDockWidgetArea, dw)
        self.addDockWidget(Qt.LeftDockWidgetArea, dw2)
        self.addDockWidget(Qt.LeftDockWidgetArea, dw3)
        self.addDockWidget(Qt.LeftDockWidgetArea, dw4)
        self.setCentralWidget(cm)
        self.show()

    def setup_toolbar(self):
        self.tb = self.addToolBar('Begin Plan')
        tb = self.tb

        def start_pp():
            plan, ok = TwoDStarter.start_plan(self.controller)
            if ok:
                self.toggle_run(False)
                controller.plan = plan
                self.toggle_run(True)

        asl_icon = qta.icon('ei.graph', color='white')
        pp = QPushButton('Pump-probe', icon=asl_icon)
        pp.clicked.connect(start_pp)

        tb.addWidget(pp)
        asl_icon = qta.icon('ei.barcode', color='white')
        pp = QPushButton('Scan Spectrum', icon=asl_icon)
        tb.addWidget(pp)
        asl_icon = qta.icon('ei.download', color='white')
        pp = QPushButton('Save current Spec', icon=asl_icon)
        tb.addWidget(pp)

    def toggle_run(self, bool):
        if bool:
            self.timer.start(20)
        else:
            self.timer.stop()

    def closeEvent(self, *args, **kwargs):
        config.write()
        super(MainWindow, self).closeEvent(*args, **kwargs)



class HardwareRegistry:
    pass


class CommandMenu(QWidget):
    def __init__(self, parent=None):
        super(CommandMenu, self).__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._layout = QVBoxLayout(self)
        c = parent.controller # type: Controller

        self.start_but = QPushButton('Start Plan')
        self._sp = SelectPlan(self)
        self.start_but.clicked.connect(lambda: self._sp.show())
        self.plan_label = QLabel('Default loop')
        self.plan_label.setAlignment(Qt.AlignHCenter)
        cb_running = QPushButton('Running',
                                 icon=qta.icon('fa.play', color='white'))
        cb_running.setCheckable(True)
        cb_running.setChecked(True)
        cb_running.toggled.connect(parent.toggle_run)

        gb = make_groupbox([self.start_but, cb_running, self.plan_label],
                           'Plans')
        self._layout.addWidget(gb)

        sc = ControlFactory('Shots', c.cam.set_shots, format_str='%d',
                            presets=[50, 200, 500, 1000])

        c.cam.sigShotsChanged.connect(sc.update_value)
        gb = make_groupbox([sc], "ADC")
        self._layout.addWidget(gb)

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
            dl2 = controller.delayline_2
            dl2c = ControlFactory('Delay 2', print, format_str='%.1f fs',
                                  extra_buttons=[("Set Home", dl2.set_pos)],
                                  )
            dls.append(dl2c)
        gb = make_groupbox(dls, "Delay")
        self._layout.addWidget(gb)

        spec = c.spectrometer
        pre_fcn = lambda x: spec.set_wavelength(spec.get_wavelength() + x)
        spec_control = ControlFactory('Wavelength', c.spectrometer.set_wavelength,
                                      format_str='%.1f nm',
                                      presets=[-100, -50, 50, 100],
                                      preset_func=pre_fcn)

        c.spectrometer.sigWavelengthChanged.connect(spec_control.update_value)
        gb = make_groupbox([spec_control], "Spectrometer")

        self._layout.addWidget(gb)

        if HAS_ROTATION_STAGE:
            rs = ControlFactory('Angle', print,
                                format_str='%.1f deg')
            gb = make_groupbox([rs], "Rotation Stage")
            self._layout.addWidget(gb)

        def get_ext(i):
            lr = controller.last_read
            return lr.ext_channel_mean[i]

        vl = ValueLabels([('Ext 1', partial(get_ext, 1))])
        self._layout.addWidget(make_groupbox([vl], 'Ext.'))
        self._layout.addStretch(10)


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
    app.setStyle('Fusion')
    app.setPalette(dark_palette)
    ss = """
        QToolTip { color: #ffffff; background-color: #2a82da;
                       border: 1px solid white; }
    """
    app.setStyleSheet(ss)

    mw = MainWindow(controller=controller)
    from Plans.PumpProbeViewer import PumpProbeViewer
    from Plans.PumpProbe import PumpProbePlan

    pp = PumpProbePlan(name='BlaBlub', controller=controller)
    controller.plan = None
    pp.t_list = np.arange(-2, 5, 0.1)
    pp.center_wl_list = [300, 600]
    #pi = PumpProbeViewer(pp)
    #ppi.show()
    mw.show()
    app.exec_()
