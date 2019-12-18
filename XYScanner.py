
from Instruments.remotes import Faulhaber
from qtpy import QtCore, QtWidgets, QtGui

fh = Faulhaber()

class Mover(QtWidgets.QWidget):
    keyPressed = QtCore.Signal(int)

    def __init__(self, **kwargs):
        super(Mover, self).__init__(**kwargs)
        self.step_size = 0.01
        self.timer = QtCore.QTimer()
        self.timer.start(300)

        self.x_label = QtWidgets.QLabel()
        self.y_label = QtWidgets.QLabel()
        self.step_lineedit = QtWidgets.QDoubleSpinBox()

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.x_label)
        self.layout().addWidget(self.y_label)

        self.timer.timeout.connect(self.update_pos)



    def keyPressEvent(self, event):
        super(Mover, self).keyPressEvent(event)
        key = event.key()
        print(key)
        self.keyPressed.emit(event.key())
        if key == QtCore.Qt.Key_Up:
            self.step('y', 1)
        elif key == QtCore.Qt.Key_Down:
            self.step('y', -1)
        elif key == QtCore.Qt.Key_Left:
            self.step('x', 1)
        elif key == QtCore.Qt.Key_Right:
            self.step('x', -1)

    def step(self, axis, sign):
        i = 0 if axis == 'x' else 1
        current_pos = fh.get_pos_mm()[i]
        if axis == 'x':
            y = None
            x = current_pos + sign*self.step_size
        else:
            x = None
            y = current_pos + sign*self.step_size
        fh.set_pos_mm(x=x, y=y)

    def update_pos(self):
        pos = fh.get_pos_mm()
        self.x_label.setText('%.3f mm' % pos[0])
        self.y_label.setText('%.3f mm' % pos[1])


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    m = Mover()
    m.show()
    app.exec_()