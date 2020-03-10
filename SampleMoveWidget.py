# from Config import config
from qtpy.QtCore import QTimer, Qt, QThread
from qtpy.QtGui import QFont, QIntValidator, QKeyEvent
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QDockWidget,
                            QPushButton, QLabel, QVBoxLayout, QSizePolicy, QFormLayout,
                            QToolBar, QCheckBox)
import qtawesome as qta

from QtHelpers import dark_palette, ControlFactory, make_groupbox, \
    ObserverPlot, ValueLabels, vlay, hlay
# from ControlClasses import Controller
from Instruments.interfaces import ILissajousScanner


class MoveWidget(QWidget):
    def __init__(self, sh : ILissajousScanner):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setLayout(hlay([QLabel('Use Arrowkeys')]))
        self.scanner = sh
        self.timer = QTimer()

    #def start_move(self, direction):
    #    self.timer.connect

    def keyPressEvent(self, a0 : QKeyEvent) -> None:
        K = 0.5
        key = a0.key()
        pos = list(self.scanner.get_pos_mm())
        print(pos)
        move = True
        if key == Qt.Key_Left:
            print('a')
            pos[0] += K
        elif key == Qt.Key_Right:
            pos[0] -= K
        elif key == Qt.Key_Up:
            pos[1] += K
        elif key == Qt.Key_Down:
            pos[1] -= K
        elif key == Qt.Key_Escape:
            move = False
            self.close()

        if move:
            self.scanner.set_pos_mm(*pos)



if __name__ == '__main__':
    from Instruments.sample_holder_PI import SampleHolder
    sh = SampleHolder()
    app = QApplication([])
    mwid = MoveWidget(sh)
    mwid.show()
    app.exec_()