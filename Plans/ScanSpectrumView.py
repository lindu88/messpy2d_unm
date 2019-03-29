import numpy as np
import pyqtgraph.parametertree as pt
import typing as T
from Signal import Signal
from .ScanSpectrum import ScanSpectrum
from .common_meta import samp
from Config import config
from qtpy.QtWidgets import QWidget, QSizePolicy, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QApplication, QTabWidget
from qtpy.QtGui import QPalette, QFont
from qtpy.QtCore import Qt, QTimer
from ControlClasses import Controller, Cam
from QtHelpers import vlay, hlay, PlanStartDialog, ObserverPlot


class ScanSpectrumView(QWidget):
    def __init__(self, ss_plan: ScanSpectrum, *args, **kwargs):
        super(ScanSpectrumView, self).__init__(*args, **kwargs)
        cam = ss_plan.cam

        def amp_getter(i):
            pixel = ss_plan.cam.channels // 2
            return ss_plan.amplitudes[i, :ss_plan.wl_idx, pixel]

        obs = [lambda: amp_getter(i) for i in range(cam.lines)]
        x = lambda: ss_plan.wl_list[:ss_plan.wl_idx]
        self.top_plot = ObserverPlot(
                obs=obs,
                signal=ss_plan.sigPointRead,
                x=x,
        )

        x = lambda: 1e7/ss_plan.wl_list[:ss_plan.wl_idx]
        self.bot_plot = ObserverPlot(
                obs=obs,
                signal=ss_plan.sigPointRead,
                x=x,
        )
        self.top_plot.plotItem.setLabel('bottom', 'Wavelength / nm')
        self.bot_plot.plotItem.setLabel('bottom', 'Wavenumber / cm-1')
        self.setLayout(vlay([self.top_plot, self.bot_plot]))

import pyqtgraph.parametertree.parameterTypes as pTypes


class WavelengthParameter(pTypes.GroupParameter):
    def __init__(self, **opts):
        opts['type'] = 'bool'
        opts['value'] = True
        pTypes.GroupParameter.__init__(self, **opts)

        self.addChild({'name': 'Wavelength (nm)', 'type': 'float', 'value': 700,
                       'decimals': 5,})
        self.addChild({'name': 'Wavenumber (cm-1)', 'type': 'float', 'value': 1e7 / 700.,
                       'decimals': 5,})
        self.a = self.param('Wavelength (nm)')
        self.b = self.param('Wavenumber (cm-1)')
        self.a.sigValueChanged.connect(self.aChanged)
        self.b.sigValueChanged.connect(self.bChanged)

    def aChanged(self):
        self.b.setValue(1e7 / self.a.value(), blockSignal=self.bChanged)

    def bChanged(self):
        self.a.setValue(1e7 / self.b.value(), blockSignal=self.aChanged)


class ScanSpectrumStarter(PlanStartDialog):
    experiment_type = 'ScanSpec'
    viewer = ScanSpectrumView
    title = "Scan Spectrum"

    def setup_paras(self):
        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp'},
               {'name': 'Operator', 'type': 'str', 'value': ''},
               {'name': 'Shots', 'type': 'int', 'max': 4000, 'decimals': 5,
                'step': 100, 'value': 100},
               WavelengthParameter(name='Min.'),
               WavelengthParameter(name='Max.'),
               dict(name='Steps', type='int', min=2, value=30),
               dict(name='Linear Axis', type='list', values=['nm', 'cm-1']),
               ]

        self.candidate_cams = {c.cam.name: c for c in self.controller.cam_list if c.cam.changeable_wavelength}

        tmp.append(dict(name='Cam', type='list', values=self.candidate_cams.keys()))
        p = pt.Parameter(name='Exp. Settings', type='group',
                         children=tmp)
        params = [samp, p]
        self.paras = pt.Parameter.create(name='Scan Spectrum', type='group', children=params)
        self.save_defaults()

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')
        s = self.paras.child('Sample')
        mapper = {'nm': 'Wavelength (nm)', 'cm-1': 'Wavenumber (cm-1)'}
        unit = mapper[p['Linear Axis']]
        wl_list = np.linspace(p.child('Min.')[unit],
                            p.child('Max.')[unit],
                            p['Steps'])

        if len(wl_list) == 0 or wl_list.min()-wl_list.max()==0:
            raise ValueError('Zero Steps')
        ss = ScanSpectrum(
                name=p['Filename'],
                cam=self.candidate_cams[p['Cam']],
                meta=s,
                wl_list=wl_list,
        )

        return ss
