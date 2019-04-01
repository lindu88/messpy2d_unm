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
        cam1_obs = (controller.cam.last_read)


        self.graph_layouter = pg.GraphicsLayoutWidget()
        self.setLayout(qh.hlay([self.graph_layouter]))
        self.plots = {}
        self.amp_lines = {}
        self.std_lines = {}

        for cam in controller.cam_list:
            amp_plot = self.graph_layouter.addPlot()
            std_plot = self.graph_layouter.addPlot()
            self.graph_layouter.nextRow()
            for l in range(cam.lines):
                self.amp_lines[(cam, l)] = amp_plot.plot()
                self.std_lines[(cam, l)] = std_plot.plot()

            cam.sigReadCompleted.connect(self.update_plots)

    def update_plots(self):
        t = time.time()
        self.times.append(t-self.t0)
        if t-self.times[0] > 20:
            self.times.pop(0)

        for (cam, line), p in self.amp_lines.items():
            p.setData(cam.last_ )


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





