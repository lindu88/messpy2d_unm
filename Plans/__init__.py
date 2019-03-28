from .PumpProbe import PumpProbePlan
from .PumpProbeViewer import PumpProbeViewer, PumpProbeStarter
from .TwoDPlan import TwoDimMoving
from .TwoDPlanViewer import TwoDViewer, TwoDStarter
from .ScanSpectrum import ScanSpectrum
from .ScanSpectrumView import ScanSpectrumView, ScanSpectrumStarter
#__all__ = [PumpProbePlan, PumpProbeViewer, pump_probe_starter,  TwoDViewer, TwoDStarter]

import abc

import attr


class Plan(abc.ABC):


    @abc.abstractmethod
    def make_step(self):
        pass

