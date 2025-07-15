import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg


"""Test if graphics are working. pyside6 was not for two different windows computers"""


pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

app = QApplication(sys.argv)
w = pg.PlotWidget()
w.show()

x = np.linspace(200, 300, 100)
y = np.sin(np.linspace(0, 10, 100)) * 50

w.plot(x, y, pen=pg.mkPen('r', width=3))
sys.exit(app.exec())