from collections import defaultdict
from Config import config
from qtpy.QtWidgets import QWidget, QSizePolicy, QLabel, QVBoxLayout, QHBoxLayout
from qtpy.QtGui import QPalette, QFont
from qtpy.QtCore import Qt, QTimer
from ControlClasses import Controller
from Plans.PumpProbe import PumpProbePlan
from pyqtgraph.parametertree import Parameter, ParameterTree

import pyqtgraph as pg
from QtHelpers import ObserverPlot, PlanStartDialog
import numpy as np

np.seterr('ignore')
import attr
import os

os.environ['QT_API'] = 'pyqt5'
import formlayout
from typing import List

from .common_meta import samp

@attr.s
class IndicatorLine:
    wl_idx = attr.ib()  # type: int
    wl = attr.ib()
    pos = attr.ib()
    line = attr.ib()
    entry_label = attr.ib()
    trans_line = attr.ib()  # type: pg.PlotCurveItem
    hist_trans_line = attr.ib()  # type: pg.PlotCurveItem
    channel = attr.ib(0)   # type: int

    def __attrs_post_init__(self):
        print('init')
        self.line.sigPositionChangeFinished.connect(self.update_pos)
        self.update_pos()

    def update_pos(self):
        self.pos = self.line.pos().x()
        self.channel = np.argmin(abs(self.pos - self.wl[self.wl_idx, :]))

    def hide_hist(self):
        self.hist_trans_line.parentItem().removeItem(self.hist_trans_line)

    def hide_trans(self):
        self.hist_trans_line.parentItem().removeItem(self.trans_line)

    def update_trans(self):
        pass

class LineLabel(QLabel):
    def __init__(self, line, parent=None):
        super(LineLabel, self).__init__(parent=parent)
        assert (isinstance(line, pg.InfiniteLine))
        line.sigPositionChangeFinished.connect(self.update_label)
        self.line = line
        p = QPalette()
        p.setColor(QPalette.Foreground, line.pen.color())
        self.setPalette(p)

        f = QFont()
        f.setPointSize(15)
        f.bold()
        self.setFont(f)
        self.update_label()
        self.setFrameStyle(3)
        self.setAlignment(Qt.AlignHCenter)

    def update_label(self, ev=None):
        x = self.line.pos().x()
        self.setText('%.1f' % x)


class PumpProbeViewer(QWidget):
    def __init__(self, pp_plan, parent=None):
        super(PumpProbeViewer, self).__init__(parent=parent)
        self.pp_plan = pp_plan  # type: PumpProbePlan
        self._layout = QHBoxLayout(self)
        self.info_label = QLabel()
        self.info_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.update_info()
        lw = QVBoxLayout(self)

        vlay = QVBoxLayout(self)

        self.do_show_cur = QCheckBox('Current Scan', self)
        self.do_show_cur.setChecked(True)
        self.do_show_cur.stateChanged.connect(self.hide_current)
        self.do_show_mean = QCheckBox('Mean of all scans', self)
        self.do_show_mean.setChecked(True)
        self.do_show_mean.stateChanged.connect(self.hide_hist)
        vlay.addWidget(self.info_label)

        vlay.addWidget(self.do_show_cur)
        vlay.addWidget(self.do_show_mean)
        self.line_area = QVBoxLayout(self)
        vlay.addLayout(self.line_area)
        vlay.addStretch(1)
        self._layout.addLayout(vlay)
        self._layout.addLayout(lw)

        self.sig_plot = ObserverPlot([], pp_plan.sigStepDone)
        self.sig_plot.add_observed((pp_plan, 'signal_data'))
        self.sig_plot.click_func = self.handle_sig_click
        self.trans_plot = ObserverPlot([], pp_plan.sigStepDone)

        lw.addWidget(self.sig_plot)
        lw.addWidget(self.trans_plot)
        self.inf_lines = [list() for i in pp_plan.center_wl_list]  # type: List[List[IndicatorLine]]

        for i in [self.update_info, self.update_trans]:
            self.pp_plan.sigStepDone.connect(i)
        pp_plan.sigWavelengthChanged.connect(self.handle_wl_change)

    def handle_sig_click(self, coords):
        x = coords.x()
        c = next(self.sig_plot.color_cycle)
        l = self.sig_plot.plotItem.addLine(x=x, pen=pg.mkPen(c, width=6))
        l.setMovable(True)
        lbl = LineLabel(l, self)
        self.line_area.addWidget(lbl)
        tl = self.trans_plot.plot(pen=pg.mkPen(c, width=2))
        tlh = self.trans_plot.plot(pen=pg.mkPen(c, width=4))

        il = IndicatorLine(wl_idx=self.pp_plan.wl_idx,
                           wl=self.pp_plan.wl,
                           pos=x,
                           line=l,
                           trans_line=tl,
                           hist_trans_line=tlh,
                           entry_label=lbl
                           )
        self.inf_lines[self.pp_plan.wl_idx].append(il)

        def remove_line(ev):
            lbl.deleteLater()
            self.sig_plot.plotItem.removeItem(l)
            self.trans_plot.plotItem.removeItem(tl)
            self.trans_plot.plotItem.removeItem(tlh)
            self.inf_lines[il.wl_idx].remove(il)

        lbl.mouseReleaseEvent = remove_line

    def update_info(self):
        pp_plan = self.pp_plan
        s = '''
        <h3>Current plan</h3>
        <big>
        <dl>
        <dt>Name:<dd>{s.name}
        <dt>Shots:<dd>{s.shots}
        <dt>Scan:<dd>{s.num_scans}
        <dt>Wl pos:<dd>{s.wl_idx}/{nwl}
        <dt>t pos:<dd>{s.t_idx}/{nt}
        <dt>Time per scan<dd>{s.time_per_scan}
        </dl>
        </big>
        '''.format(s=pp_plan, nt=len(pp_plan.t_list),
                   nwl=len(pp_plan.center_wl_list))
        self.info_label.setText(s)

    def handle_wl_change(self):
        last_idx = self.pp_plan.wl_idx - 1

        for i in self.inf_lines[last_idx]:
            self.trans_plot.removeItem(i.trans_line)
            i.line.hide()
        for i in self.inf_lines[self.pp_plan.wl_idx]:
            self.trans_plot.addItem(i.trans_line)

            i.line.show()

    def hide_hist(self, i):
        all_lines = []
        for i in range(len(self.pp_plan.center_wl_list)):
            all_lines += self.inf_lines[i]
        chk = self.do_show_mean.checkState()
        if not chk:
            for i in all_lines:
                self.trans_plot.removeItem(i.hist_trans_line)

        else:
            for i in all_lines:
                self.trans_plot.addItem(i.hist_trans_line)


    def hide_current(self, i):
        all_lines = []
        for i in range(len(self.pp_plan.center_wl_list)):
            all_lines += self.inf_lines[i]
        chk = self.do_show_cur.checkState()
        if not chk:
            for i in all_lines:
                self.trans_plot.removeItem(i.trans_line)
        else:
            for i in all_lines:
                self.trans_plot.addItem(i.trans_line)
            self.handle_wl_change()

    def update_spec(self):
        pass

    def update_trans(self):
        pp = self.pp_plan
        if pp.t_idx == 0:
            return

        if self.do_show_cur.checkState():
            for i in self.inf_lines[pp.wl_idx]:
                i.trans_line.setData(x=pp.t_list[:pp.t_idx],
                                     y=pp.cur_scan[pp.wl_idx, :pp.t_idx, i.channel])

        if pp.old_scans.shape[3] > 0 and self.do_show_mean.checkState():
            for j in self.inf_lines:
                for i in j:
                    if i.hist_trans_line not in self.trans_plot.plotItem.dataItems:
                        continue
                    ym = np.nanmean(pp.old_scans[pp.wl_idx, :, i.channel, :], 1)
                    i.hist_trans_line.setData(x=pp.t_list, y=ym)


start_form = [('Name', ''),
              ('Shots', 1000),
              ('Center Wl.', ''),
              (None, 't list'),
              ('Linear min', -1.),
              ('Linear max', 1.),
              ('Linear Step', 0.1),
              ('Use Log.', True),
              ('Log Points', 70),
              ('Log End', 100)]


def pump_probe_starter(controller):
    out = formlayout.fedit(start_form, 'Pump-probe config')

    print(out)


class PumpProbeStarter(PlanStartDialog):
    title = "New Pump-probe Experiment"
    viewer = PumpProbeViewer

    def setup_paras(self):

        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp'},
               {'name': 'Operator', 'type': 'str', 'value': ''},
               {'name': 'Shots', 'type': 'int',  'max': 4000, 'decimals': 5,
                'step': 500, 'value': 100},
               {'name': 'Linear Range (-)', 'suffix': 'ps', 'type': 'float', 'value': -1},
               {'name': 'Linear Range (+)', 'suffix': 'ps', 'type': 'float', 'value': 1},
               {'name': 'Linear Range (step)', 'suffix': 'ps', 'type': 'float', 'min': 0.01},
               {'name': 'Logarithmic Scan', 'type': 'bool'},
               {'name': 'Logarithmic End', 'type': 'float', 'suffix': 'ps',
                'min': 0.},
               {'name': 'Logarithmic Points',  'type': 'int', 'min': 0},
               dict(name='Shutter', type='bool', value=True),
               dict(name='Use Rotation Stage', type='bool', value=True),
               dict(name='Angles in deg.', type='str'),
               dict(name="Add pre-zero times", type='bool', value=False),
               dict(name="Num pre-zero points", type='int', min=0, max=20),
               dict(name="Pre-Zero pos", type='float', value=-60., suffix='ps'),

               ]
        two_d = {'name': 'Pump Probe', 'type': 'group', 'children': tmp}
        
        params = [samp, two_d]
        self.paras = Parameter.create(name='Pump Probe', type='group', children=params)
        config.last_pump_probe = self.paras.saveState()

    def create_plan(self, controller):
        p = self.paras.child('Pump Probe')
        s = self.paras.child('Sample')
        t_list = np.arange(p['Linear Range (-)'],
                           p['Linear Range (+)'],
                           p['Linear Range (step)']).tolist()
        if p['Logarithmic Scan']:
            t_list.append(np.geomspace(p['Linear Range (+)'],
                                       p['Logarithmic End'],
                                       p['Logarithmic Points']).tolist())
        if p['Add pre-zero times']:
            n = p['Num pre-zero points']
            pos = p['Pre-Zero pos']
            times = np.linspace(pos-1, pos, n)
            t_list.append(times)

        if p['Use Rotation Stage']:
            s = p['Angles in deg.'].split(',')
            angles = map(float, s)
        else:
            angles = None

        p = PumpProbePlan(
            name=p['Filename'],
            meta=self.paras.saveState(),
            t_list=t_list,
            shots=p['Shots'],
            controller=controller,
            center_wl_list=[0.],
            use_shutter=p['Use Shutter'],
            rot_stage_angles=angles
        )
        return p


if __name__ == '__main__':
    import sys

    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)


    sys.excepthook = exception_hook

    app = QApplication([])
    con = Controller()
    timer = QTimer()
    timer.timeout.connect(con.loop)

    pp = PumpProbePlan(name='BlaBlub', controller=con)
    con.plan = pp
    pp.t_list = np.arange(-2, 2, 0.1)
    pp.center_wl_list = [300]
    ppi = PumpProbeViewer(pp)
    ppi.show()
    # formlayout.fedit(start_form)
    timer.start(50)
    try:
        app.exec_()
    except:
        print('fds')
