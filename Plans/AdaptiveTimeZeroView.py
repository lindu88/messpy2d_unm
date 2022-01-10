import numpy as np
import pyqtgraph.parametertree as pt
from qtpy.QtWidgets import QWidget, QPushButton
import attr
from ControlClasses import Controller
from QtHelpers import vlay, PlanStartDialog, ObserverPlot
from .AdaptiveTimeZeroPlan import AdaptiveTimeZeroPlan


@attr.s(auto_attribs=True)
class AdaptiveTZViewer(QWidget):
    plan: AdaptiveTimeZeroPlan
    plot_widget: ObserverPlot = attr.ib(init=False)
    stop_button: QPushButton = attr.Factory(lambda: QPushButton("Stop"))

    def __attrs_post_init__(self):
        super(AdaptiveTZViewer, self).__init__()
        #self.plan.sigStepDone.connect(self.update_view)
        self.plot_widget = ObserverPlot([self.plan.get_data], self.plan.sigStepDone)
        self.setLayout(vlay(self.plot_widget, self.stop_button))
        self.stop_button.clicked.connect(lambda: setattr(self.plan, 'is_running', False))


class AdaptiveTZStarter(PlanStartDialog):
    experiment_type = 'AdaptiveTZFinder'
    title = "Adaptive Time-zero finder"
    viewer = AdaptiveTZViewer

    def setup_paras(self):
        params = [dict(name='Filename', type='str', value='temp_tz'),
                  dict(name='MaxDiff', type='float', value=50),
                  dict(name='Stop', type='float', value=5),
                  dict(name='Initial Step', type='float', value=1),
                  dict(name='Min. Step', type='float', value=0.05),
                  dict(name='Mode', type='list', values=['mean', 'max'])
                  ]
        self.paras = pt.Parameter.create(name='Exp. Settings', type='group', children=params)

    def create_plan(self, controller: 'Controller'):
        p = self.paras.child('Exp. Settings')
        plan = AdaptiveTimeZeroPlan(
            cam=controller.cam,
            delay_line=controller.delay_line,
            max_diff=p["MaxDiff"],
            name=p["Filename"],
            meta={},
            stop=p["Stop"],
            current_step=p['Initial Step'],
            min_step=p['Min. Step'],
            mode=p['Mode']
        )
        return plan

