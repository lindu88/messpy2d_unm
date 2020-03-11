# from Config import config
from qtpy.QtCore import QTimer, Qt, QThread
from qtpy.QtGui import QFont, QIntValidator, QKeyEvent
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QLineEdit, QDockWidget,
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
        self.scanner = sh
        self.setFocusPolicy(Qt.StrongFocus)
        home_button = QPushButton('Set Home')
        home_button.clicked.connect(lambda: self.scanner.set_home())
        self.move_button = QPushButton('Moving')
        self.move_button.setCheckable(True)
        self.move_button.setChecked(False)
        self.move_button.toggled.connect(self.mover)
        buttons = hlay([home_button,self.move_button])
        pos_str = str(self.scanner.pos_home)
        self.home_label= QLabel(pos_str)
        self.setLayout(vlay([self.home_label,buttons]))
        self.timer = QTimer()
        self.K = 0.025
        self.x_settings = 3
        self.y_settings = [2,0.2]

<<<<<<< HEAD
    def mover(self):
        if self.move_button.isChecked():
            if self.x_settings == None and self.y_settings == None:
                setwid = SettingsMoveWidget(mw=self)
                setwid.show()
            else:
                self.scanner.start_contimove(self.x_settings,self.y_settings)
        if self.move_button.isChecked() == False:
            self.scanner.stop_contimove()
            #self.x_settings = None
            #self.y_settings = None
=======
        self.pos_label = QLabel()
        self.home_button = QPushButton("Set Home")
        self.home_button.clicked.connect(sh.set_home)
        self.update_label()

    def update_label(self):
        x, y = self.scanner.get_pos_mm()
        self.pos_label.setText(f"x: {x:2.3f} mm  y: {y:2.3f} ")
>>>>>>> fbd6e834f4f51de77757a6b5c38dfe4de9551e1a

    def keyPressEvent(self, a0 : QKeyEvent) -> None:
        key = a0.key()
        pos = list(self.scanner.get_pos_mm())
        move = True
        K =  self.K
        if key == Qt.Key_Left:
            pos[0] += K
        elif key == Qt.Key_Right:
            pos[0] -= K
        elif key == Qt.Key_Up:
            pos[1] += K
        elif key == Qt.Key_Down:
            pos[1] -= K
        elif key == Qt.Key_W:
            self.K *= 1.5
        elif key == Qt.Key_S:
            self.K /= 1.5
        elif key == Qt.Key_Escape:
            move = False
            self.close()

        if move:
            self.scanner.set_pos_mm(*pos)
<<<<<<< HEAD
            self.label_updater(pos)

    def label_updater(self,new_pos):
        self.home_label.setText(f' x: {new_pos[0]:.3f}, y: {new_pos[1]:.3f}')

class SettingsMoveWidget(QWidget):
    def __init__(self, mw: MoveWidget, *args, **kwargs):
        super(SettingsMoveWidget, self).__init__(*args, **kwargs)
        self.mw = mw
        self.x_button = QPushButton('Set x:')
        self.x_button.clicked.connect(self.x_click)
        self.xlim_label = QLabel('x limit')
        self.edit_box_x = QLineEdit()
        self.edit_box_x.setMaxLength(3)
        self.edit_box_x.setMaximumWidth(100)
        self.x_limbox = vlay([self.xlim_label, self.edit_box_x])
        self.xsteps_label = QLabel('x steps')
        self.edit_box_xstep = QLineEdit()
        self.edit_box_xstep.setMaxLength(3)
        self.edit_box_xstep.setMaximumWidth(100)
        self.x_stepbox = vlay([self.xsteps_label, self.edit_box_xstep])
        self.x_setter = hlay([self.x_button,self.x_limbox,self.x_stepbox])

        self.y_button = QPushButton('Set y:')
        self.y_button.clicked.connect(self.y_click)
        self.ylim_label = QLabel('y limit')
        self.edit_box_y = QLineEdit()
        self.edit_box_y.setMaxLength(3)
        self.edit_box_y.setMaximumWidth(100)
        self.y_limbox = vlay([self.ylim_label, self.edit_box_y])
        self.ysteps_label = QLabel('y steps')
        self.edit_box_ystep = QLineEdit()
        self.edit_box_ystep.setMaxLength(3)
        self.edit_box_ystep.setMaximumWidth(100)
        self.y_stepbox = vlay([self.ysteps_label, self.edit_box_ystep])
        self.y_setter = hlay([self.y_button,self.y_limbox,self.y_stepbox])
        self.start_button = QPushButton('Start Movement:')
        self.start_button.clicked.connect(self.start_move)
        self.setLayout(vlay([self.x_setter,self.y_setter,self.start_button]))
=======
            self.update_label()
>>>>>>> fbd6e834f4f51de77757a6b5c38dfe4de9551e1a

    def x_click(self):
        self.mw.x_settings = [self.edit_box_x.text(),self.edit_box_xstep.text()]
    def y_click(self):
        self.mw.y_settings = [self.edit_box_y.text(),self.edit_box_ystep.text()]
    def start_move(self):
        self.mw.scanner.start_contimove(self.mw.x_settings, self.mw.y_settings)
        print(self.mw.x_settings, self.mw.y_settings)
        self.close()

if __name__ == '__main__':
    from Instruments.sample_holder_PI import SampleHolder
    sh = SampleHolder()
    app = QApplication([])
    mwid = MoveWidget(sh)
    mwid.show()
    app.exec_()