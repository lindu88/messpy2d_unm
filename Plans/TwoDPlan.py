import numpy as np
from scipy.stats import binned_statistic
from attr import attrs, attrib, Factory, make_class
from ControlClasses import Controller, Signal

speed_of_light = 299792458.0
HeNe_period_m = 632.816e-9
HeNe_period_fs = 632.816e-9 / speed_of_light * 1e15

def bins_and_borders(lower, upper, num_bins):
    both = np.linspace(lower, upper, 2*num_bins+1)
    bins = both[1::2]
    bin_borders = both[::2]
    return bins, bin_borders

def phase_correction(binned_pyro):
    """Find time-zero bin and constant phase from interferogram"""
    m_argmax = np.argmax(binned_pyro)
    last_m = np.inf
    x = np.arange(binned_pyro.size)
    out, trys = [], 0
    while True and trys < 150:
        mr = np.roll(binned_pyro, -m_argmax)
        mr_spec = np.fft.fft(mr)[1:mr.size // 2]
        pp = np.argmax(np.abs(mr_spec))
        xl = x[1:mr.size // 2] - x[pp]
        xl = xl[pp - 5:pp + 4]
        mr_phase = np.unwrap(np.angle(mr_spec))


        A = np.vstack([xl, np.ones(2 * 4 + 1)]).T
        deriv, const = np.linalg.lstsq(A, mr_phase[pp - 5:pp + 4])[0]
        out.append((deriv, const, -m_argmax))
        trys += 1
        if trys > 150:
            break

        if np.sign(deriv) != np.sign(last_m) and last_m is not np.inf:
            out = np.array(out)
            i = np.argmin(np.abs(out[:, 0]))
            deriv, const, k0 = out[i, :].T
            k0 = int(k0)

            break
        elif deriv > 0:
            m_argmax -= 1
        elif deriv < 0:
            m_argmax += 1
        last_m = deriv
    return k0, const%np.pi

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

def calc_necessary_shots(distance_fs, laser_freq_kHz=2,
                         shots_per_period=4):
    """Calculates maximal speed of the delayline and the necessary 
       shot number"""


    max_speed = HeNe_period_m / shots_per_period/ laser_freq_kHz
    min_shot_count = 2 * distance_fs / HeNe_period_fs

def estimated_distance(laser_freq_kHz, speed, shots):
    duration = 1000*shots / laser_freq_kHz
    return (duration * speed * 1000) / speed_of_light * 1e15



@attrs
class TwoDimMoving:
    name = attrib('')
    sample_info = attrib(Factory(dict))
    tau_range = attrib([-3, 3])
    shots = attrib(4000)
    bin_width = attrib(3)
    scans = attrib(0)
    wl = attrib(0)
    controller = attrib(Factory(Controller)) # type: Controller
    data = attrib(None)
    binned_data = attrib(None)

    sigScanFinished = attrib(Factory(Signal))
    sigTauMinChanged = attrib(Factory(Signal))
    sigTauMaxChanged = attrib(Factory(Signal))
    sigShotsChanged = attrib(Factory(Signal))

    def __attrs_post_init__(self):
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        N = self.controller.cam.num_ch
        self.bin_paras = calc_params(self.tau_range, self.num_bins)
        self.bin_counts = np.zeros(self.bin_paras.bins.size, dtype='int')
        self.bin_total = np.zeros((self.bin_paras.bins.size, N))
        self.bin_means = np.zeros_like(self.bin_total)
        self.controller.cam.set_shots(self.shots)

    def set_tau_min(self, tau_min):
        self.tau_range[0] = tau_min
        self.sigTauMinChanged.emit(tau_min)

    def set_tau_max(self, tau_max):
        self.tau_range[1] = tau_max
        self.sigTauMaxChanged.emit(tau_max)

    def set_shots(self, shots):
        self.shots = shots
        self.sigShotsChanged.emit(shots)

    def make_step_gen(self):
        c = self.controller

        while True:
            print('j')
            self.start_recording()
            self.save_raw()
            self.bin_scan()
            self.sigScanFinished.emit()
            #self.save_result()
            self.scans += 1
            yield

    def bin_scan(self):
        c = self.controller
        pd1, pd2, pyro = self.lr.ext[:, -3:].T

        # assuming monoton movement for now
        pd1_state =  (pd1 - pd1.mean()) > 0
        counts = np.hstack((0, np.diff(pd1_state).cumsum()))
        tau = counts * HeNe_period_fs / 2.

        #bin
        pre_bins = np.arange(-1, tau.max(), self.bin_width)
        m, _, _ = binned_statistic(tau, pyro, 'mean', bins=pre_bins)
        k0, const_phase = phase_correction(m)
        self.inferferogram = m[k0:k0+1024]
        self.pump_spec = np.abs(np.fft.fft(self.inferferogram))
        binned_probe = binned_statistic(tau, self.lr.probe, 'mean', bins=pre_bins)
        self.binned_probe = binned_probe[k0:k0+1024]






    def save_raw(self):
        "Save raw data, the format is 16xprobe, 16xref, chopper, fringe"
        lr = self.lr
        print(lr.ext.shape)
        out = np.column_stack((lr.det_a, lr.det_b,  lr.ext))
        np.save("%s_%d.npy"%(self.name, self.scans), out)

    def start_recording(self):
        c = self.controller
        c.delay_line_second.set_speed(1.)


        c.delay_line.set_pos(self.t_range[0]*1000)
        print('pos bevor', c.delay_line.get_pos())
        c.delay_line_second.set_speed(0.25)
        c.delay_line.set_pos(self.t_range[1]*1000, do_wait=False)
        self. lr = c.cam.read_cam()
        print('pos after',  c.delay_line.get_pos())



    def save_result(self):
        pass

