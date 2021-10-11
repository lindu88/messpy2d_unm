import attr
import numpy as np
from . import Plan

from typing import List, Dict, Optional
from Instruments.interfaces import ICam

@attr.s(auto_attribs=True)
class Parameter:
    name : str 
    upper_lim : float = np.inf
    lower_lim : float = -np.inf
    start_val : Optional[float] = None


class Manipulator:
    params = List[Parameter]

    def apply(self):
        raise NotImplementedError


class ObjectivDetector:
    """
    pass
    """
    
    @staticmethod
    def from_cam(cam: ICam, kind: str) -> 'ObjectivDetector':
        pass

    def eval(self):
        pass
    



    


@attr.s
class OptimizePlan:
    mani : Manipulator






