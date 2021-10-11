import atom.api as a
from .common import SampleInfo, SetupInfo, Meta

class PumpProbeCamSettings(a.Atom):
    center_wls = a.List(a.Float)
    cam = a.ForwardTyped('Cam')

class PumpProbeSettings(Meta):            
    setup_info = a.Typed(SetupInfo, factory=SetupInfo)
    sample_info = a.Typed(SampleInfo, factory=SampleInfo)
    cam_infos = a.List(PumpProbeCamSettings)
    delay_times = a.List(a.Float)    
    switch_pol = a.Bool(False)    
    pol_list = a.List(a.Float)
    use_shutter = a.Bool(False)
    use_rot_stage = a.Bool(False)
    rot_stage_angles = a.List(a.Float) 
    
    

class PumpProbePlan(Meta):
    cams = a.List()
    delay_line = a.Value()
    
    shutter = a.Value()
    rotation_stage = a.Value()

    settings = a.Typed(PumpProbeSettings)



class PumpProbeData(a.Atom):
    """
    Contains the collected data for a single camera.

    Parameters
    ----------
    a : [type]
        [description]
    """