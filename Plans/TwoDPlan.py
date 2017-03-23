import numpy as np
from attr import attrs, attrib, Factory, make_class
from ControlClasses import Controller, Signal

speed_of_light = 299792458.0

def bins_and_borders(lower, upper, num_bins):
    both = np.linspace(lower, upper, 2*num_bins+1)
    bins = both[1::2]
    bin_borders = both[::2]
    return bins, bin_borders

@attrs
class BinParameters:
    speed = attrib(0)
    bins = attrib(0)
    bin_borders = attrib(0)

def calc_params(t_range, num_bins, shots=4000, shots_per_sec=2000):
    total_range = (t_range[1] - t_range[0])
    speed = total_range / (shots/shots_per_sec)
    bins, bin_borders = bins_and_borders(*t_range, num_bins=num_bins)
    out = BinParameters(speed=speed, bins=bins, bin_borders=bin_borders)
    return out

@attrs
class TwoDimMoving:
    name = attrib('')
    sample_info = attrib(Factory(dict))
    t_range = attrib((-3, 3))
    num_bins = attrib(2048)
    shots = attrib(4000)
    scans = attrib(0)
    wl = attrib(0)
    controller = attrib(Factory(Controller)) # type: Controller
    data = attrib(None)
    binned_data = attrib(None)
    sigScanFinished = attrib(Factory(Signal))

    def __attrs_post_init__(self):
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        N = self.controller.cam.num_ch
        self.bin_paras = calc_params(self.t_range, self.num_bins)
        self.bin_counts = np.zeros(self.bin_paras.bins.size, dtype='int')
        self.bin_total = np.zeros((self.bin_paras.bins.size, N))
        self.bin_means = np.zeros_like(self.bin_total)


    def make_step_gen(self):
        c = self.controller()

        while True:
            print('j')
            self.start_recording()
            self.save_raw()
            self.bin_scan()
            self.sigScanFinished.emit()
            self.save_result()
            self.scans += 1
            yield

    def bin_scan(self):
        c = self.controller()
        idx = np.searchsorted(self.bin_paras.bin_borders,
                              self.tc.last_read.fringe_count)
        self.bin_counts[idx] += 1
        self.bin_total[idx, :] += c.last_read.probe[idx, :]
        self.bin_means[:] = self.bin_total / self.bin_counts



    def save_raw(self):
        "Save raw data, the format is 16xprobe, 16xref, chopper, fringe"
        lr = self.controller.last_read
        out = np.column_stack((lr.probe, lr.ref, lr.chopper, lr.fringe))
        np.savetxt("%s_%d.txt"%(self.name, self.scans))

    def start_recording(self):
        c = self.controller
        c.delay_line_second
        c.delay_line_second.set_speed()
        c.fringe_counter.clear()
        c.cam.read_cam()
        self.last_read = c.last_read


    def save_result(self):
        pass

