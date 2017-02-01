import numpy as np
from attr import attrs, attrib, Factory, make_class
from ControlClasses import Controller, Signal

speed_of_light = 299792458.0

def calc_params(t_range, num_bins, shots=4000, shots_per_sec=2000):
    total_range = (t_range[1] - t_range[0])
    speed = total_range / (shots/shots_per_sec)
    bins = np.linspace(t_range[0], t_range[1], 2*num_bins+1)[1::2]
    bin_borders = np.linspace(t_range[0], t_range[1], 2 * num_bins + 1)[::2]

    out = make_class('Params', ['speed', 'bin_borders', 'bins',
                                'freqs_cm'])
    out(speed=speed, bins=bins, bin_borders=bin_borders)




@attrs
class TwoDimMoving:
    name = attrib('')
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
        self.data = np.zeros((N, self.num_bins))
        self.shots_per_bin = np.zeros_like(self.wl)
        dt = self.num_bins / (self.t_range[1]-self.t_range[0])
        self.freqs_ps = np.fft.fftfreq(self.num_bins, dt)
        self.freq_cm = speed_of_light / self.freqs_ps * 1000
        self.t_bins = 0

    def make_step_gen(self):
        while True:
            self.start_recording()
            self.save_raw()
            self.bin_scan()
            self.save_result()
            self.return_position()
            self.scans += 1
            yield

    def bin_scan(self):
        idx = np.searchsorted(self.t_bins,
                              self.tc.last_read.fringe_count)

    def save_raw(self):
        "Save raw data, the format is 16xprobe, 16xref, chopper, fringe"
        lr = self.controller.last_read
        out = np.column_stack((lr.probe, lr.ref, lr.chopper, lr.fringe))
        np.savetxt("%s_%d.txt"%(self.name, self.scans))

    def start_recording(self):
        c = self.controller
        c.delay_line_second.set_speed()
        c.fringe_counter.clear()
        c.cam.read_cam()
        self.last_read = c.last_read
        
    def save_result(self):
        pass

