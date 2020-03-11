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

        self.pos_label = QLabel()
        self.home_button = QPushButton("Set Home")
        self.home_button.clicked.connect(sh.set_home)
        self.update_label()

    def update_label(self):
        x, y = self.scanner.get_pos_mm()
        self.pos_label.setText(f"x: {x:2.3f} mm  y: {y:2.3f} ")

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
            self.update_label()


if __name__ == '__main__':
    from Instruments.sample_holder_PI import SampleHolder
    sh = SampleHolder()
    app = QApplication([])
    mwid = MoveWidget(sh)
    mwid.show()
    app.exec_()