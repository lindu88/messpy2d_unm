import math
from functools import partial
from itertools import cycle

import pyqtgraph as pg
import pyqtgraph.parametertree as pt
import yaml
from qtpy.QtCore import Qt
from qtpy.QtGui import QPalette, QColor
from qtpy.QtWidgets import (QWidget, QLineEdit, QLabel, QPushButton, QHBoxLayout,
                            QFormLayout, QGroupBox, QVBoxLayout, QDialog, QStyleFactory)

from Config import config

VEGA_COLORS = {
    'blue': '#1f77b4',
    'orange': '#ff7f0e',
    'green': '#2ca02c',
    'red': '#d62728',
    'purple': '#9467bd',
    'brown': '#8c564b',
    'pink': '#e377c2',
    'gray': '#7f7f7f',
    'olive': '#bcbd22',
    'cyan': '#17becf'}

col = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
       '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
       '#bcbd22', '#17becf']


def make_default_cycle():
    return cycle(col[:])


def make_palette():
    """makes dark palette for use with qt fusion theme"""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(15, 15, 15))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor(242, 15, 97).lighter())
    palette.setColor(QPalette.HighlightedText, Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray)
    return palette


class ControlFactory(QWidget):
    """Simple widget build of Label, button and LineEdit

    Parameters
    ----------
    name: str,
        Shows up in the widget

    apply_fn: function,
        The function which gets called (with the the textlabel value)
        after pressing Set.

    update_signal: signal,
        The signal which is listened to update the label.

    parent: QWidget,
        Qt-parent widget

    format_str: str,
        Formatting of the value

    presets: list
        List of values for which a button is generated. When
        the button is clicked, call preset_func with the value.

    preset_func: function
        Gets called with the preset values, is required when using
        presets

    extra_buttons: list of (str, func)
        Creates button with the label given by the string
        and calling the function func.

    """
    def __init__(self, name, apply_fn, update_signal=None, parent=None,
                 format_str='%.1f', presets=None, preset_func=None,extra_buttons=None):
        super(ControlFactory, self).__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.apply_button = QPushButton('Set')
        self.apply_fn = apply_fn
        self.cur_value_label = QLabel()
        self.format_str = format_str
        self.update_value(0)
        self.edit_box = QLineEdit()
        self.edit_box.setMaxLength(7)
        self.edit_box.setMaximumWidth(100)
        self.apply_button.clicked.connect(lambda: apply_fn(self.edit_box.text()))

        self._layout = QFormLayout(self)
        self._layout.setLabelAlignment(Qt.AlignRight)

        for w in [(QLabel('<b>%s</b>'%name), self.cur_value_label),
                  (self.apply_button, self.edit_box)]:
            self._layout.addRow(*w)
        l = []
        if preset_func is None:
            self.preset_func = self.apply_fn
        else:
            self.preset_func = preset_func

        if presets is not None:
            self.setup_presets(presets)

        if extra_buttons is not None:
            self.setup_extra_buttons(extra_buttons)

        if update_signal is not None:
            update_signal.connect(self.update_value)

    def update_value(self, value):
        """updates value of the control widget"""
        if not isinstance(value, str):
            self.cur_value_label.setText(self.format_str % value)
        else:
            self.cur_value_label.setText(value)

    def setup_presets(self, presets):
        len_row = 0
        hlay = QHBoxLayout()
        for p in presets:
            s = partial_formatter(p)
            but = QPushButton(s)
            but.setStyleSheet('''
            QPushButton { color: lightblue;}''')
            but.setFlat(False)
            but.clicked.connect(partial(self.preset_func, p))
            but.setFixedWidth(200/min(len(presets), 4))
            hlay.addWidget(but)
            hlay.setSpacing(10)
            len_row += 1
            if len_row > 3:
                self._layout.addRow(hlay)
                hlay = QHBoxLayout()
                len_row = 0
            self._layout.addRow(hlay)

    def setup_extra_buttons(self, extra_buttons):
        hlay = QHBoxLayout()
        for (s, fn) in extra_buttons:
            but = QPushButton(s)
            but.clicked.connect(fn)
            hlay.addWidget(but)
        self._layout.addRow(hlay)


class PlanStartDialog(QDialog):
    title = ''

    def __init__(self, *args, **kwargs):
        super(PlanStartDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.title)
        self.treeview = pt.ParameterTree()
        start_button = QPushButton('Start Plan')
        start_button.clicked.connect(self.accept)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        self.setLayout(vlay([self.treeview,
                             hlay([start_button, cancel_button])]))
        self.setup_paras()
        self.load_defaults()
        self.treeview.setParameters(self.paras)
        self.treeview.setPalette(self.style().standardPalette())
        self.treeview.setStyle(QStyleFactory.create('Fusion'))
        self.treeview.setStyleSheet("")
        n = len(self.treeview.listAllItems())

        self.resize(350, n*40 + 100 )
        for i in self.treeview.listAllItems():
            if isinstance(i, pt.types.GroupParameterItem):
                i.updateDepth(0)

    def setup_paras(self):
        raise NotImplemented

    def create_plan(self):
        raise NotImplemented

    def load_defaults(self, fname=None):
        if fname is not None:
            f = open(fname, 'r')
            d = yaml.load(f)
        else:
            d = config._data
        for group in self.paras:
            for para in group:
                try:
                    para.setValue(d[group.name()][para.name()])
                except KeyError:
                    pass

    def save_defaults(self, fname=None):
        if fname is not None:
            d = {}
        else:
            d = config._data

        for group in self.paras:
            for para in group:
                d.setdefault(group.name(), {})[para.name()] = para.value()
        if fname is not None:
            f = open(fname, 'x')
            yaml.dump(d, f)
        else:
            config.write()

    def closeEvent(self, *args, **kwargs):
        self.save_defaults()
        super().closeEvent(*args, **kwargs)

    @classmethod
    def start_plan(cls, controller, parent=None):
        dialog = cls(parent=parent)
        result = dialog.exec_()
        plan = dialog.create_plan(controller)
        return plan, result == QDialog.Accepted


class ObserverPlot(pg.PlotWidget):
    def __init__(self, obs, signal, x=None, parent=None):
        super(ObserverPlot, self).__init__(parent=parent)
        signal.connect(self.update_data)
        self.color_cycle = make_default_cycle()
        self.plotItem.showGrid(x=True, y=True, alpha=1)
        self.lines = {}
        self.observed = []
        if isinstance(obs, tuple):
            obs = [obs]
        else:
            obs = obs
        for i in obs:
            self.add_observed(i)
        #self.enableMouse()
        self.sceneObj.sigMouseClicked.connect(self.click)
        self.click_func = None

    def add_observed(self, single_obs):
        self.observed.append(single_obs)
        pen = pg.mkPen(color=next(self.color_cycle), width=1)
        self.lines[single_obs[1]] = self.plotItem.plot([0], pen=pen)

    def update_data(self):
        for o in self.observed:
            self.lines[o[1]].setData(getattr(*o))

    def click(self, ev):
        print(ev.button())

        if self.click_func is not None and ev.button() == 1:
            coords = self.plotItem.vb.mapSceneToView(ev.pos())
            self.click_func(coords)
            ev.accept()




class ValueLabels(QWidget):
    def __init__(self, obs, parent=None):
        super(ValueLabels, self).__init__(parent=parent)
        lay = QFormLayout()
        self.setStyleSheet('''
        QLabel { font-size: 14pt;}''')
        self.setLayout(lay)
        self.obs = {}
        for name, getter in obs:
            self.obs[name] = QLabel('0'), getter
            lay.addRow(name + ':', self.obs[name][0])


def make_groupbox(widgets, title=''):
    """Puts given widgets into a groupbox"""
    gb = QGroupBox()
    gb.setContentsMargins(0, 0, 0, 0)
    gb.setSizeIncrement(0, 0)
    vl = QVBoxLayout(gb)
    vl.setContentsMargins(0, 0, 0, 0)
    for i in widgets:
        vl.addWidget(i)
    if title:
        gb.setTitle(title)

    return gb

dark_palette = make_palette()


def hlay(widgets, add_stretch=False):
    lay = QHBoxLayout()
    for w in widgets:
        try:
            lay.addWidget(w)
        except TypeError:
            lay.addLayout(w)

    if add_stretch:
        lay.addStretch(1)
    return lay


def vlay(widgets, add_stretch=False):
    lay = QVBoxLayout()
    for w in widgets:
        try:
            lay.addWidget(w)
        except TypeError:
            lay.addLayout(w)

    if add_stretch:
        lay.addStretch(1)
    return lay


def partial_formatter(val):
    sign = val/abs(val)
    if math.log10(abs(val)) > 3:
        return '%dk'%(sign*(abs(val)//1000))
    else:
        return str(val)

