import numpy as np
from attr import attrs, attrib, Factory, make_class
from ControlClasses import Controller
from Signal import Signal
import itertools
#from scipy.stats import binned_statistic
speed_of_light = 299792458.0
HeNe_periode = 611.802e-9 / speed_of_light
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
    start_end_tau = attrib([-3, 3])
    num_bins = attrib(2048)
    shots = attrib(4000)
    center_wl = attrib(1e7/2200) #used for interleaving
    pop_times = [0.2, 0.5, 2., 10.]
    n_interleave = 3
    scans = attrib(0)
    wl = attrib(0)
    controller = attrib(Factory(Controller)) # type: Controller
    data = attrib(None)
    binned_data = attrib(None)
    speed = attrib(0.1)

    sigScanFinished = attrib(Factory(Signal))
    sigTauStartChanged = attrib(Factory(Signal))
    sigTauEndChanged = attrib(Factory(Signal))
    sigShotsChanged = attrib(Factory(Signal))
    sigSpeedChanged = attrib(Factory(Signal))

    def __attrs_post_init__(self):
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        N = self.controller.cam.cam.channels

        self.bin_paras = calc_params(self.start_end_tau, self.num_bins)
        self.bin_counts = np.zeros(self.bin_paras.bins.size, dtype='int')
        self.bin_total = np.zeros((self.bin_paras.bins.size, N))
        self.bin_means = np.zeros_like(self.bin_total)
        self.controller.cam.set_shots(self.shots)



    def set_tau_min(self, tau_min):
        self.start_end_tau[0] = float(tau_min)
        self.sigTauStartChanged.emit(self.start_end_tau[0])

    def set_tau_max(self, tau_max):
        self.start_end_tau[1] = float(tau_max)
        self.sigTauEndChanged.emit(self.start_end_tau[1])

    def set_shots(self, shots):
        self.shots = int(shots)
        self.sigShotsChanged.emit(shots)

    def set_speed(self, speed):
        self.speed = float(speed)
        self.sigSpeedChanged.emit(self.speed)

    def make_step_gen(self):
        c = self.controller
        interleave_pos = np.linspace(-self.center_wl/2, self.center_wl/2, self.n_interleave)
        interleave_pos = interleave_pos*1e-9/speed_of_light*1e15
        c.delay_line.set_speed(0.1)
        while True:
            print('j')
            for self.pop_delay in self.pop_times:
                for self.interleave in interleave_pos:
                    print(self.interleave, interleave_pos, self.pop_delay)
                    self.controller.delay_line.set_pos(self.interleave+self.pop_delay*1000)
                    self.start_recording()
                    self.save_raw()

                    self.bin_scan()
                    self.sigScanFinished.emit()
                    yield
                #self.save_result()
            self.scans += 1
            yield

    def bin_scan(self):
        c = self.controller
        pd1 = self.lr.ext[:, -3]
        pd2 = self.lr.ext[:, -2]
        pyro = self.lr.ext[:, -1]
        counts1 = np.cumsum(np.diff(pd1 - pd1.mean() > 0))
        counts2 = np.cumsum(np.diff(pd2 - pd2.mean() > 0))

        taus = (counts1+counts2)/2. * HeNe_periode*1e15/2.
        self.current_t = np.hstack((0, taus))
        print(pyro.shape, taus.shape)
        self.bin_pre = np.arange(-0.1, taus.max(), HeNe_periode*1e15)
        self.cur_interferogram = binned_statistic(self.current_t, pyro, 'mean',  bins=self.bin_pre)[0]
        self.bin_probe = binned_statistic(self.current_t, self.lr.det_b.T, 'mean',  bins=self.bin_pre)[0].T


    def save_raw(self):
        "Save raw data, the format is 16xprobe, 16xref, chopper, fringe"
        lr = self.lr
        print(lr.ext.shape)

        out = np.column_stack((lr.det_a, lr.det_b,  lr.ext))
        np.save("data/%s_%d_popdelay_%.1f_%.1f.npy"%(self.name, self.scans,
                                                     self.pop_delay*1000, self.interleave), out)

    def start_recording(self):
        c = self.controller
        c.cam.set_shots(self.shots)
        c.delay_line_second.set_speed(.75)
        start = self.start_end_tau[0]
        end = self.start_end_tau[1]

        c.delay_line_second.set_pos(start * 1000)
        print('pos bevor', c.delay_line.get_pos())
        c.delay_line_second.set_speed(self.speed)
        c.delay_line_second.set_pos(end * 1000, do_wait=False)
        self. lr = c.cam.read_cam()
        c.delay_line_second.set_speed(1.)
        print('pos after',  c.delay_line.get_pos())



    def save_result(self):
        pass

