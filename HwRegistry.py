import platform
from Config import config
from Instruments.mocks import CamMock, DelayLineMock
TESTING = config.testing
_cam = CamMock()
_cam2 = CamMock(name="Mock2")
_dl = DelayLineMock()
_dl2 = None
_rot_stage = None
_shutter = None

pc_name = platform.node()

if pc_name == '2dir-PC':
    from Instruments.ircam_16 import irdaq
    _cam = irdaq.cam

    #from Instruments.spec_triax import spec
    #_spec = spec

    from Instruments.delay_line_mercury import dl
    _dl = dl
    hp = config.__dict__.get('Delay 1 Home Pos.', 8.80)
    _dl.home_pos = hp

    from Instruments.delay_line_gmc2 import dl
    _dl2 = dl
    #hp = config.__dict__.get('Delay 2 Home Pos.', 8.80)
    #_dl2.home_pos = hp
    #_dl2 = None

    #from Instruments.FringeCounter import fc
    #_fc = fc

elif pc_name == 'helmholm' and not TESTING:
    from Instruments.stresing_cam.ESLS import Cam
    #from Instruments.delay_line_serial import dl as _dl
    from Instruments.delay_line_xmlrpc import dl as _dl
    #from Instruments.delay_line_mercury import dl as _dl
    _cam = Cam()
    from Instruments.ircam_64_remote import cam
    _cam2 = cam
    from Instruments.remotes import RotationStage, Shutter
    _rot_stage = RotationStage()
    _shutter = Shutter()
