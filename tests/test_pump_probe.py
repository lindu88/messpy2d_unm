import pytest
from ControlClasses import Controller
from Plans import PumpProbePlan

def test_init():
    controller = Controller()
    for i in range(10):
        controller.loop()

def test_functions():
    c = Controller()
    c.cam.get_bg()
    if c.shutter:
        c.shutter.open()
        assert(c.shutter.is_open())
        c.shutter.close()
        assert(not c.shutter.is_open())


def test_pump_probe():
    c = Controller()
    t_list = range(0, 10)
    cwls = [[0,]]
    pp = PumpProbePlan(controller=c, t_list=t_list, name='test')
    c.plan = pp
    for i in range(300):
        c.loop()
    print(pp.cam_data[0].completed_scans.shape)
    assert(pp.cam_data[0].completed_scans.shape[0] == pp.cam_data[0].scan)

