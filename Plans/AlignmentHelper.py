import pyqtgraph as pg
import time
from qtpy.QtGui import QFont, QGuiApplication
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget,
                            QPushButton, QLabel, QVBoxLayout, QSizePolicy,
                            QToolBar, QCheckBox)
import QtHelpers as qh
from ControlClasses import Controller

class AlignmentHelper(QWidget):
    def __init__(self, controller: Controller, **kwargs):
        super().__init__(**kwargs)
        self.times = []
        self.time_max = 20
        self.t0 = time.time()
        self.controller = controller

        self.graph_layouter = pg.GraphicsLayoutWidget()
        self.setLayout(qh.hlay([self.graph_layouter]))
        self.plots = {}
        self.amp_lines = {}
        self.std_lines = {}

        for cam in controller.cam_list:
            amp_plot = self.graph_layouter.addPlot()
            for line_name in range(len(cam.cam.line_names)):
                c = pg.mkPen(color=qh.col[line_name])
                self.amp_lines[(cam, line_name)] = amp_plot.plot(pen=c), []

            std_plot = self.graph_layouter.addPlot()
            for std_name in range(len(cam.cam.std_names)):
                c = pg.mkPen(color=qh.col[std_name])
                self.std_lines[(cam, std_name)] = std_plot.plot(pen=c), []
            self.graph_layouter.nextRow()
        controller.loop_finished.connect(self.update_plots)

    def update_plots(self):

        t = time.time()
        self.times.append(t-self.t0)

        if self.times[-1] - self.times[0] > self.time_max:
            self.times = self.times[1:]
            do_pop = True
        else:
            do_pop = False

        for (cam, line), (p, data) in self.amp_lines.items():
            data.append(cam.last_read.lines[line].mean())
            if do_pop:
                data.pop(0)
            p.setData(self.times, data)

        for (cam, line), (p, data) in self.std_lines.items():
            data.append(cam.last_read.stds[line].mean())
            if do_pop:
                data.pop(0)
            p.setData(self.times, data)


if __name__ == '__main__':
    c = Controller()

    app = pg.mkQApp()
    a = AlignmentHelper(c)

    def looper():
        while True:
            c.loop()

    import threading
    t = threading.Thread(target=looper)
    t.start()
    app.aboutToQuit.conenct(t.s)
    a.show()
    app.exec_()





