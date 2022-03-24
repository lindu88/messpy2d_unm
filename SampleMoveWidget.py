# from Config import config
import attr
from qtpy.QtCore import QTimer, Qt, QThread, QObject, Slot
from qtpy.QtGui import QFont, QIntValidator, QKeyEvent, QIcon, QPixmap
from qtpy.QtWidgets import (QMainWindow, QApplication, QWidget, QLineEdit, QDockWidget, QShortcut,
                            QPushButton, QLabel, QVBoxLayout, QSizePolicy, QFormLayout,
                            QToolBar, QCheckBox)
from qtpy.QtSvg import QSvgWidget
from QtHelpers import  vlay, hlay

from Instruments.interfaces import ILissajousScanner

@attr.define
class ScannerMover(QObject):
    @Slot()
    def move_left(self):
        pass

    @Slot()
    def move_right(self):
        pass

    @Slot()
    def move_up(self):
        pass

    @Slot()
    def move_down(self):
        pass

class MoveWidget(QWidget):
    def __init__(self, sh: ILissajousScanner):
        super().__init__()
        self.scanner = sh
        self.setFocusPolicy(Qt.StrongFocus)
        home_button = QPushButton('Set Home')
        home_button.clicked.connect(lambda: self.scanner.set_home())
        self.move_button = QPushButton('Cont. Move.')
        self.move_button.setCheckable(True)
        self.move_button.setChecked(False)
        self.move_button.toggled.connect(self.mover)
        buttons = hlay([home_button, self.move_button])
        pos_str = str(self.scanner.pos_home)
        self.home_label = QLabel()
        self.label_updater(self.scanner.get_pos_mm(), self.scanner.get_zpos_mm())
        self.help_button = QPushButton('Help')
        self.help_button.clicked.connect(self.show_help)
        self.setLayout(vlay([self.home_label, buttons, self.help_button]))
        self.timer = QTimer()
        self.K = 0.1
        self.x_settings = 3
        self.y_settings = [2, 0.2]


    def show_help(self):
        self.help_label = QLabel()
        self.help_label.setPixmap(QPixmap('MotorHelp.png'))
        self.help_label.setAutoFillBackground(False)
        self.help_label.show()

    def show_xy(self):
        pass

    def mover(self):
        if self.move_button.isChecked():
            self.setwid = SettingsMoveWidget(mw=self)
            self.setwid.show()

        if self.move_button.isChecked() == False:
            self.scanner.stop_contimove()
            # self.x_settings = None
            # self.y_settings = None

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        key = a0.key()
        pos = list(self.scanner.get_pos_mm())

        if self.scanner.has_zaxis:
            z_pos = self.scanner.get_zpos_mm()

        move = True
        K = self.K
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

        if self.scanner.has_zaxis:
            z_pos = self.scanner.get_zpos_mm()
            if key == Qt.Key_R:
                z_pos += 0.3
                move = False
            if key == Qt.Key_F:
                z_pos -= 0.3
                move = False

            self.scanner.set_zpos_mm(z_pos)

        if move:
            self.scanner.set_pos_mm(*pos)
        self.label_updater(pos, z_pos)

    def label_updater(self, new_pos, zpos):
        self.home_label.setText(f' x: {new_pos[0]:.3f}, y: {new_pos[1]:.3f}, z: {zpos: .1f}')


class SettingsMoveWidget(QWidget):
    def __init__(self, mw: MoveWidget, *args, **kwargs):
        super(SettingsMoveWidget, self).__init__(*args, **kwargs)
        self.mw = mw
        self.x_button = QPushButton('Set x:')
        self.x_button.clicked.connect(self.x_click)
        self.xlim_label = QLabel('X amp.')
        self.edit_box_x = QLineEdit()
        self.edit_box_x.setMaxLength(3)
        self.edit_box_x.setMaximumWidth(100)
        self.x_limbox = vlay([self.xlim_label, self.edit_box_x])
        #self.xsteps_label = QLabel('x steps')
        #self.edit_box_xstep = QLineEdit()
        #self.edit_box_xstep.setMaxLength(3)
        #self.edit_box_xstep.setMaximumWidth(100)
        self.x_setter = hlay([self.x_button, self.x_limbox])

        self.y_button = QPushButton('Set y:')
        self.y_button.clicked.connect(self.y_click)
        self.ylim_label = QLabel('y limit')
        self.edit_box_y = QLineEdit()
        self.edit_box_y.setMaxLength(3)
        self.edit_box_y.setMaximumWidth(100)
        self.y_limbox = vlay([self.ylim_label, self.edit_box_y])
        #self.ysteps_label = QLabel('y steps')
        #self.edit_box_ystep = QLineEdit()
        #self.edit_box_ystep.setMaxLength(3)
        #self.edit_box_ystep.setMaximumWidth(100)
        #self.y_stepbox = vlay([self.ysteps_label, self.edit_box_ystep])
        self.y_setter = hlay([self.y_button, self.y_limbox])
        self.start_button = QPushButton('Start Movement:')
        self.start_button.clicked.connect(self.start_move)
        self.setLayout(vlay([self.x_setter, self.y_setter, self.start_button]))

    def x_click(self):
        self.mw.x_settings = float(self.edit_box_x.text())

    def y_click(self):
        self.mw.y_settings = float(self.edit_box_y.text())

    def start_move(self):
        self.mw.x_settings = float(self.edit_box_x.text())
        self.mw.y_settings = float(self.edit_box_y.text())
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
