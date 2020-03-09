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



class MoveWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setLayout(hlay([QLabel('Use Arrowkeys')]))
        self.timer = QTimer()


    #def start_move(self, direction):
    #    self.timer.connect

    def keyPressEvent(self, a0 : QKeyEvent) -> None:
        K = 0.5
        key = a0.key()
        pos = list(get_current_pos())
        move = True
        if key == Qt.LeftArrow:
            pos[0] += K
        elif key == Qt.RightArrow:
            pos[0] -= K
        elif key == Qt.UpArrow:
            pos[1] += K
        elif key == Qt.DownArrow:
            pos[1] -= K
        elif key == Qt.Key_Escape:
            move = False
            self.close()

        if move:
            move(*pos)



if __name__ == '__main__':
    app = QApplication([])
    mwid = MoveWidget()
    mwid.show()
    app.exec_()