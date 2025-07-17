import platform
import sys
from MessPy.Config import config
from MessPy.Instruments.mocks import CamMock, DelayLineMock, StageMock, PowerMeterMock
from loguru import logger

logger.info("Init HwRegistry")
TESTING = config.testing
_cam = CamMock()
_cam2 = None  # CamMock(name="Mock2")
_dl = None
_dl2 = None
_rot_stage = None
_shutter = []
_sh = None
_shaper = None

pc_name = platform.node()

if len(sys.argv) > 1:
    arg = sys.argv[1]
else:
    arg = "vis"


logger.info(f"Running on {pc_name}")


#logger.info("Unknown PC, using mocks")
_cam = CamMock()
_dl = DelayLineMock()
_sh = StageMock()
_power_meter = PowerMeterMock()

logger.info("HwRegistry initialized")
