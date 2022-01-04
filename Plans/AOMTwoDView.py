import attr
import numpy as np
import pyqtgraph.parametertree as pt
from pyqtgraph import PlotWidget, ImageItem, PlotItem, colormap, GraphicsLayoutWidget, HistogramLUTItem, InfiniteLine, \
    mkPen, PlotDataItem
from qtpy.QtWidgets import QWidget, QLabel

from ControlClasses import Controller
from QtHelpers import vlay, PlanStartDialog, hlay
from .AOMTwoPlan import AOMTwoDPlan
from .PlanBase import sample_parameters


class AOMTwoDViewer(GraphicsLayoutWidget):
    def __init__(self, plan: AOMTwoDPlan, parent=None):
        super().__init__(parent=parent)
        self.pump_freq = plan.last_freq
        self.probe_freq = plan.probe_freq

        pw = self.addPlot()
        pw: PlotItem
        pw.setLabels(bottom='Probe Freq', left='Time')
        cmap = colormap.get("CET-D1")
        self.ifr_img = ImageItem()
        self.ift_img.setImage(np.zeros(128, 128), rect=(self.probe_freq.min(), 0, self.probe_freq.ptp(), plan.max_t2))
        pw.addItem(self.ifr_img)
        self.spec_image_view = pw
        self.ifr_img.mouseClickEvent = self.ifr_clicked
        hist = HistogramLUTItem()
        hist.setImageItem(self.ifr_img)
        hist.gradient.setColorMap(cmap)
        self.addItem(hist)
        self.ifr_lines: dict[InfiniteLine, PlotDataItem] = {}
        self.ifr_free_colors = list(range(9))

        pw = self.addPlot()
        pw: PlotItem
        pw.setLabels(bottom='Probe Freq', left='Pump Freq')
        cmap = colormap.get("CET-D1")
        self.spec_img = ImageItem()
        self.spec_img.setImage(np.zeros(128, 128),
                               rect=(self.probe_freq.min(), self.pump_freqs.min(), self.probe_freq.ptp(),
                                     self.pump_freqs.ptp()))
        pw.addItem(self.spec_img)
        self.spec_line = InfiniteLine(pos=self.pump_freqs[64], angle=0,
                                      bounds=(self.pump_freqs.min(), self.pump_freqs.max()),
                                      movable=True)
        pw.addItem(self.spec_line)
        hist = HistogramLUTItem()
        hist.setImageItem(self.spec_img)
        hist.gradient.setColorMap(cmap)

        self.addItem(hist)
        self.ci.nextRow()
        self.trans_plot = self.ci.addPlot(colspan=2)
        self.trans_plot.setLabels(bottom="Time", left='Signal')
        self.spec_plot = self.ci.addPlot(colspan=2)
        self.spec_plot.setLabels(bottom="Probe Freq", left='Signal')
        self.spec_cut_line = self.spec_plot.plot()
        self.ci.nextRow()
        self.info_label = self.ci.addLabel("Hallo", colspan=4)
        self.update_plots()
        self.spec_line.sigPositionChanged.connect(self.update_spec_lines)
        self.plan.sigStepDone.connect(self.update_images)
        self.plan.sigStepDone.connect(self.update_plots)
        self.plan.sigStepDone.connect(self.update_label)

    def update_images(self):
        self.ifr_img.setImage(self.plan.last_ir)
        self.spec_img.setImage(self.plan.last_2d)

    def ifr_clicked(self, ev):
        x, y = ev.pos()
        if len(self.ifr_free_colors) == 0:
            return
        _int_color = self.ifr_free_colors.pop(0)
        line = self.spec_image_view.addLine(x=self.probe_freq[round(x)], movable=True,
                                            bounds=(self.probe_freq.min(), self.probe_freq.max()),
                                            pen=mkPen(_int_color, width=1))
        line._int_color = _int_color
        self.ifr_lines[line] = self.trans_plot.plot(self.t, self.plan.last_ir[round(x), :], pen=line.pen)

        def update(line: InfiniteLine):
            idx = np.argmin(abs(self.probe_freq - line.pos()[0]))
            self.ifr_lines[line].setData(self.t, self.plan.last_ir[round(idx), :])

        def delete(line: InfiniteLine, ev):
            ev.accept()
            trans_line = self.ifr_lines.pop(line)
            self.trans_plot.removeItem(trans_line)
            self.spec_image_view.removeItem(line)
            self.ifr_free_colors.append(line._int_color)

        line.sigClicked.connect(delete)
        line.sigPositionChanged.connect(update)


    def update_plots(self):
        self.spec_plot.plot(self.probe_freq, self.plan.last_2d.mean(1))
        for line in self.ifr_lines:
            line.sigPositionChanged.emit(line) # Causes an update

    def update_spec_lines(self, line: InfiniteLine):
        print("update", line.pos()[1])
        idx = np.argmin(abs(self.pump_freqs - line.pos()[1]))
        self.spec_cut_line.setData(self.probe_freq, self.plan.last_2d[:, idx])

    def update_label(self):
        p = self.plan
        s = f'''
            <h3>Current Experiment</h3>
            <big>
            <dl>
            <dt>Name:<dd>{p.name}
            <dt>Shots:<dd>{p.t}
            <dt>Scan:<dd>{p.cur_scan} / {p.max_scan}                     
            </dl>
            </big>
            '''
        s = s + p.time_tracker.as_string()
        self.label.setText(s)


@attr.s(auto_attribs=True)
class AOMTwoDViewerA(QWidget):
    plan: AOMTwoDPlan
    ifr_pw: PlotWidget = attr.ib(factory=PlotWidget)
    ifr_plot: PlotWidget = attr.ib(factory=PlotWidget)
    spec_pw: PlotWidget = attr.ib(factory=PlotWidget)
    spec_img_pw: PlotWidget = attr.ib(factory=PlotWidget)
    data_image: ImageItem = attr.ib(init=False)
    spec_image: ImageItem = attr.ib(init=False)
    label: QLabel = attr.Factory(QLabel)

    def __attrs_post_init__(self):
        super(AOMTwoDViewer, self).__init__()
        self.plan.sigStepDone.connect(self.update_image)
        self.data_image = ImageItem()
        self.spec_image = ImageItem()
        self.spec_img_pw.addItem(self.spec_image)
        self.spec_img_pw.plotItem.setTitle("2D Spectrum")
        self.ifr_pw.plotItem.addItem(self.data_image)
        self.ifr_pw.plotItem.setTitle("Inferogram")
        self.setLayout(vlay(hlay(self.ifr_pw, self.spec_img_pw),
                            hlay(self.ifr_plot, self.plot4),
                            self.label))
        self.l1 = self.spec_plot.plotItem.plot([1, 2, 3])
        self.l3 = self.plot4.plotItem.plot([1, 2, 3])

    def update_image(self):
        self.data_image.setImage(self.plan.last_ir)
        self.spec_image.setImage(self.plan.last_2d[:, :])
        # self.plot2.clear()
        # self.plot2.plot(self.plan.last_ir[64, :])
        # self.plot2.plot(self.plan.last_ir[0, :])
        # self.plot2.plot(self.plan.last_ir[-1, :])
        self.plot4.clear()
        self.plot4.plot(self.plan.last_freq[:], self.plan.last_2d[64, :])
        self.plot4.plot(self.plan.last_freq[:], self.plan.last_2d[0, :])
        self.plot4.plot(self.plan.last_freq[:], self.plan.last_2d[-1, :])
        self.plot4.plot(self.plan.last_freq[:], self.plan.last_2d.sum(0))
        # self.l3.setData(self.plan.last_ir[:, 50])

    def update_label(self):
        p = self.plan
        s = f'''
            <h3>Current Experiment</h3>
            <big>
            <dl>
            <dt>Name:<dd>{p.name}
            <dt>Shots:<dd>{p.t}
            <dt>Scan:<dd>{p.cur_scan} / {p.max_scan}                     
            </dl>
            </big>
            '''
        s = s + p.time_tracker.as_string()
        self.label.setText(s)


class AOMTwoDStarter(PlanStartDialog):
    title = "New 2D-experiment"
    viewer = AOMTwoDViewer
    experiment_type = '2D Time Domain'

    def setup_paras(self):
        has_rot = self.controller.rot_stage is not None
        has_shutter = self.controller.shutter is not None

        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp'},
               {'name': 'Operator', 'type': 'str', 'value': 'Till'},
               {'name': 't2 (+)', 'suffix': 'ps', 'type': 'float', 'value': 4},
               {'name': 't2 (step)', 'suffix': 'ps', 'type': 'float', 'value': 0.1},
               {'name': 'Phase Cycles', 'type': 'list', 'values': [1, 2, 4]},
               {'name': 'Rot. Frame', 'suffix': 'cm-1', 'type': 'float', 'value': 2000},
               {'name': 'Linear Range (-)', 'suffix': 'ps', 'type': 'float', 'value': 0},
               {'name': 'Linear Range (+)', 'suffix': 'ps', 'type': 'float', 'value': 1},
               {'name': 'Linear Range (step)', 'suffix': 'ps', 'type': 'float', 'min': 0.2},
               {'name': 'Logarithmic Scan', 'type': 'bool'},
               {'name': 'Logarithmic End', 'type': 'float', 'suffix': 'ps', 'min': 0.},
               {'name': 'Logarithmic Points', 'type': 'int', 'min': 0},
               dict(name="Add pre-zero times", type='bool', value=False),
               dict(name="Num pre-zero points", type='int', value=10, min=0, max=20),
               dict(name="Pre-Zero pos", type='float', value=-60., suffix='ps'),
               ]

        two_d = {'name': 'Exp. Settings', 'type': 'group', 'children': tmp}
        params = [sample_parameters, two_d]
        self.paras = pt.Parameter.create(name='Pump Probe', type='group', children=params)

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')
        s = self.paras.child('Sample')
        t_list = np.arange(p['Linear Range (-)'],
                           p['Linear Range (+)'],
                           p['Linear Range (step)']).tolist()
        if p['Logarithmic Scan']:
            t_list += (np.geomspace(p['Linear Range (+)'], p['Logarithmic End'], p['Logarithmic Points']).tolist())

        if p['Add pre-zero times']:
            n = p['Num pre-zero points']
            pos = p['Pre-Zero pos']
            times = np.linspace(pos - 1, pos, n).tolist()
            t_list = times + t_list

        self.save_defaults()
        p = AOMTwoDPlan(
            name=p['Filename'],
            meta=self.paras.getValues(),
            t3_list=np.asarray(t_list),
            controller=controller,
            max_t2=p['t2 (+)'],
            step_t2=p['t2 (step)'],
            rot_frame_freq=p['Rot. Frame'],
            shaper=controller.shaper,
            phase_frames=p['Phase Cycles'],
        )
        return p


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    from ControlClasses import Controller

    app = QApplication([])
    p = AOMTwoDPlan(controller=Controller(), shaper=None, t3_list=[1, 2])
    w = AOMTwoDViewer(plan=p)
    w.show()
    app.exec_()
