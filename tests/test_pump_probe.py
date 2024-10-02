import pytest
import os
import pathlib
import os.path as osp
from MessPy.Plans import PumpProbePlan
from MessPy.ControlClasses import Controller
from MessPy.Config import config

config.testing = True
config.data_directory


def test_init():
    controller = Controller()
    controller.cam.set_shots(2)
    for i in range(2):
        controller.loop()


def test_functions():
    c = Controller()
    c.cam.get_bg()
    if c.shutter:
        c.shutter[0].open()
        assert c.shutter[0].is_open()
        c.shutter[0].close()
        assert not c.shutter[0].is_open()


def test_pump_probe():
    c = Controller()
    t_list = range(0, 10)
    cwls = [
        [
            0,
            300,
        ]
    ]
    c.cam.set_shots(2)
    pp = PumpProbePlan(
        controller=c, t_list=t_list, name="test", shots=2, center_wl_list=cwls
    )
    c.plan = pp

    while pp.num_scans < 2:
        c.loop()
    assert pp.cam_data[0].completed_scans.shape[0] == pp.cam_data[0].scan
