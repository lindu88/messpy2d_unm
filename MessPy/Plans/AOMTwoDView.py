from typing import Callable

import attr
import numpy as np
import pyqtgraph.parametertree as pt
import qasync
from pyqtgraph import (
    GraphicsLayoutWidget,
    HistogramLUTItem,
    ImageItem,
    InfiniteLine,
    PlotDataItem,
    PlotItem,
    PlotWidget,
    colormap,
    mkPen,
)
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QLabel, QTabWidget, QWidget

from MessPy.ControlClasses import Controller
from MessPy.Plans.PlanParameters import DelayParameter
from MessPy.QtHelpers import PlanStartDialog, hlay, make_entry, remove_nodes, vlay

from .AOMTwoPlan import AOMTwoDPlan
from .PlanBase import sample_parameters


@attr.dataclass
class TwoDimPlotter(PlotWidget):
    plan: AOMTwoDPlan
    img_2dspec: ImageItem = attr.ib(factory=ImageItem)
    hist_item: HistogramLUTItem = attr.ib(factory=HistogramLUTItem)

    probe_freq: np.ndarray = attr.ib()
    pump_freqs: np.ndarray = attr.ib()

    @probe_freq.default
    def _read_freqs(self):
        self.plan.probe_freqs

    @pump_freqs.default
    def _read_freqs(self):
        self.plan.pump_freqs

    def __attrs_post_init__(self):
        self.img_2dspec.setImage(np.zeros((128, self.plan.t1.size)))
        self.img_2dspec.setRect((self.probe_freq.max(), self.pump_freqs[-1], -self.probe_freq.ptp(),
                                 self.pump_freqs[0] - self.pump_freqs[-1]))
        self.addItem(self.img_2dspec)
        self.hist_item.setImageItem(self.img_2dspec)
        self.addItem(self.hist_item)

    def update_image(self):
        self.img_2dspec.setImage(self.plan.last_2d[::, ::-1])


class AOMTwoDViewer(GraphicsLayoutWidget):
    def __init__(self, plan: AOMTwoDPlan, parent=None):
        super().__init__(parent=parent)
        self.plan = plan
        self.pump_freqs = plan.pump_freqs
        self.probe_freq = plan.probe_freqs

        pw = self.addPlot()
        pw: PlotItem
        pw.setLabels(bottom='Probe Freq', left='Time')
        cmap = colormap.get("CET-D1")
        self.ifr_img = ImageItem()
        rect = (self.probe_freq.max(), 0, -self.probe_freq.ptp(), plan.max_t1)
        self.ifr_img.setImage(np.zeros((128, plan.t1.size)), rect=rect)
        pw.addItem(self.ifr_img)
        self.spec_image_view = pw
        self.ifr_img.mouseClickEvent = self.ifr_clicked
        hist = HistogramLUTItem()
        hist.setImageItem(self.ifr_img)
        hist.gradient.setColorMap(cmap)
        self.addItem(hist)
        self.ifr_lines: dict[InfiniteLine, PlotDataItem] = {}
        self.ifr_free_colors = list(range(9))
        self.addPlot: Callable[[], PlotItem]

        pw = self.addPlot()
        pw.setLabels(bottom='Probe Freq', left='Pump Freq')
        cmap = colormap.get("CET-D1")

        self.spec_img = ImageItem()
        rect = (self.probe_freq.max(), self.pump_freqs[-1], -self.probe_freq.ptp(),
                self.pump_freqs[0]-self.pump_freqs[-1])
        self.spec_img.setImage(
            np.zeros((128, plan.pump_freqs.size)), rect=rect)

        pw.addItem(self.spec_img)
        self.spec_line = InfiniteLine(pos=self.pump_freqs[self.pump_freqs.size//2], angle=0,
                                      bounds=(self.pump_freqs.min(),
                                              self.pump_freqs.max()),
                                      movable=True)
        pw.addItem(self.spec_line)
        hist = HistogramLUTItem()
        hist.setImageItem(self.spec_img)
        hist.gradient.setColorMap(cmap)

        self.addItem(hist)
        self.ci.nextRow()

        self.spec_plot = self.ci.addPlot(colspan=2)
        self.spec_plot.setLabels(bottom="Probe Freq", left='Signal')
        self.spec_cut_line = self.spec_plot.plot()
        self.spec_mean_line = self.spec_plot.plot()
        self.spec_current_line = self.spec_plot.plot()
        self.ci.nextRow()
        self.info_label = self.ci.addLabel("Hallo", colspan=4)

        self.update_plots()
        self.spec_line.sigPositionChanged.connect(self.update_spec_lines)
        self.spec_line.sig
        self.plan.sigStepDone.connect(self.update_data)
        self.plan.sigStepDone.connect(self.update_plots)
        self.plan.sigStepDone.connect(self.update_label)
        self.time_str = ''
        self.plan.time_tracker.sigTimesUpdated.connect(self.set_time_str)

    @qasync.asyncSlot()
    async def update_data(self, al=True):
        if self.plan.last_2d is not None:
            self.ifr_img.setImage(self.plan.last_ir, autoLevels=al)
            self.spec_img.setImage(self.plan.last_2d[::, ::-1], autoLevels=al)

    def update_plots(self):
        # self.spec_current_line.setData(self.probe_freq, self.plan.)
        if self.plan.last_2d is not None:
            self.spec_mean_line.setData(
                self.probe_freq, self.plan.last_2d.mean(1))
            for line in self.ifr_lines.keys():
                line.sigPositionChanged.emit(line)  # Causes an update

    def update_spec_lines(self, *args):
        idx = np.argmin(abs(self.pump_freqs - self.spec_line.pos()[1]))
        self.spec_cut_line.setData(self.probe_freq, self.plan.last_2d[:, idx])

    def set_time_str(self, s):
        self.time_str = s

    def update_label(self):
        p = self.plan
        s = f'''
            <h3>Current Experiment</h3>
            <big>
            <dl>
            <dt>Name:<dd>{p.name}
            <dt>Scan:<dd>{p.cur_scan} / {p.max_scan}
            <dt>Time-point:<dd>{p.t2_idx} / {p.t2.size}: {p.cur_t2: .2f} ps
            </dl>
            </big>
            '''
        s = s + self.time_str
        self.info_label.setText(s)


class AOMTwoDStarter(PlanStartDialog):
    title = "New 2D-experiment"
    viewer = AOMTwoDViewer
    experiment_type = '2D Time Domain'

    def setup_paras(self):
        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp'},
               {'name': 'Operator', 'type': 'str', 'value': 'Till'},
               {'name': 't1 (+)', 'suffix': 'ps',
                'type': 'float', 'value': -4},
               {'name': 't1 (step)', 'suffix': 'ps',
                'type': 'float', 'value': 0.1},
               {'name': 'Phase Cycles', 'type': 'list', 'values': [1, 2, 4]},
               {'name': 'Rot. Frame', 'suffix': 'cm-1',
                   'type': 'int', 'value': 2000},
               {'name': 'Mode', 'type': 'list',
                   'values': ['classic', 'bragg']},
               {'name': 'AOM Amp.', 'type': 'float',
                   'value': 0.3, 'min': 0, 'max': 0.6},
               {'name': 'Repetitions', 'type': 'int', 'value': 1},
               DelayParameter(),
               {'name': 'Save Frames', 'type': 'bool', 'value': False},
               {'name': 'Save Ref. Frames', 'type': 'bool', 'value': False},
               ]

        two_d = {'name': 'Exp. Settings', 'type': 'group', 'children': tmp}
        params = [sample_parameters, two_d]
        self.paras = pt.Parameter.create(
            name='Pump Probe', type='group', children=params)

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')
        s = self.paras.child('Sample')
        t_list = p.child("Delay Times").generate_values()
        self.save_defaults()

        p = AOMTwoDPlan(
            name=p['Filename'],
            meta=make_entry(self.paras),
            t2=np.asarray(t_list),
            controller=controller,
            max_t1=p['t1 (+)'],
            step_t1=p['t1 (step)'],
            rot_frame_freq=p['Rot. Frame'],
            shaper=controller.shaper,
            aom_amplitude=p['AOM Amp.'],
            phase_frames=p['Phase Cycles'],
            mode=p['Mode'],
            repetitions=p['Repetitions'],
            save_frames_enabled=p['Save Frames'],
            save_ref=p['Save Ref. Frames'] and p['Save Frames']
        )
        return p


if __name__ == '__main__':
    from MessPy.ControlClasses import Controller
    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    p = AOMTwoDPlan(controller=Controller(), shaper=None, t3_list=[1, 2])
    w = AOMTwoDViewer(plan=p)
    w.show()
    app.exec_()
