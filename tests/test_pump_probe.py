from Config import config
config.testing = True
config.data_directory
from ControlClasses import Controller
from Plans import PumpProbePlan
import pathlib, os, pytest
import os.path as osp

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
    while pp.num_scans < 2:          
        c.loop()                     
    print(pp.cam_data[0].completed_scans.shape)
    assert(pp.cam_data[0].completed_scans.shape[0] == pp.cam_data[0].scan)


def test_overwrite_protection_pump_probe():
    c = Controller()
    t_list = range(0, 10)
    cwls = [[0,]]
    pp = PumpProbePlan(controller=c, t_list=t_list, name='test')
    c.plan = pp
    while pp.num_scans < 2:
        c.loop()
    name1 = pp.get_name().with_suffix('.npz')
    assert(pathlib.Path(name1).is_file())

    pp2 = PumpProbePlan(controller=c, t_list=t_list, name='test')
    c.plan = pp2
    while pp2.num_scans < 2:
        c.loop()
    name2 = pp2.get_name().with_suffix('.npz')
    assert(name1 != name2)
    assert(pathlib.Path(name2).is_file())
