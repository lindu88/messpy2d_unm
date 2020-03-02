import attr
import numpy as np
from Plans.common_meta import Plan
import typing as T
from Signal import Signal
from Config import config
from pathlib import Path
import os.path
import matplotlib.pyplot as plt
import threading

from ControlClasses import Cam, Controller



@attr.s(auto_attribs=True, cmp=False)
class ScanSpectrum:
    name: str
    meta: dict
    cam: Cam
    wl_list: np.ndarray = attr.ib()
    n_lines: int = 128
    wl_idx: int = 0
    timeout: float = 3
    sigPointRead: Signal = attr.Factory(Signal)

    def __attrs_post_init__(self):
        n_wl = len(self.wl_list)
        self.wls = np.zeros((n_wl, self.n_lines))
        self.probe = np.zeros((n_wl, self.n_lines))
        self.ref = np.zeros((n_wl, self.n_lines))
        self.signal = np.zeros((n_wl, self.n_lines))

        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        




    def make_step_gen(self):
        self.cam.set_wavelength(self.wl_list[0])
        for self.wl_idx, wl in enumerate(self.wl_list):

            t = threading.Thread(target=self.cam.set_wavelength, args=(wl, self.timeout))
            t.start()
            while t.is_alive():
                yield


            wls = self.cam.get_wavelengths(wl)
            t = threading.Thread(target=self.cam.read_cam)
            t.start()
            while t.is_alive():
                yield

            probe = self.cam.last_read.lines[0, :]
            ref = self.cam.last_read.lines[1, :]
            sig = self.cam.last_read.signals

            self.wls[self.wl_idx,:] = wls
            self.probe[self.wl_idx,:] = probe
            self.ref[self.wl_idx, :] = ref
            self.signal[self.wl_idx, :] = sig
            self.sigPointRead.emit()
            yield

        self.save()
        yield

    def get_name(self, data_path = False):
        if data_path:
            p = Path(data_path)
        else:
            p = r"C:\Users\2dir\messpy2d\data_temps"
        dname = p +f"\{self.name}_spectrumScan.npz"

        if os.path.exists(dname):
            name_exists = True
            i = 0
            while name_exists == True:
                dname = p + f"\{self.name}{i}_spectrumScan.npz"
                i += 1
                if os.path.exists(dname) ==  False:
                    name_exists = False
        self._name = dname
        return self._name

    def save(self):
        data = {'cam': self.cam.name}
        #data['meta'] = self.meta
        data['wl'] = self.wls
        data['probe'] = self.probe
        data['ref'] = self.ref
        data['signal'] = self.signal
        fig = plt.figure()
        plt.plot(self.wls[:,64],self.probe[:,64], label = 'Probe')
        plt.plot(self.wls[:,64],self.ref[:,64], label = 'Ref')
        plt.legend()
        fig.show()
        try:
            name =  self.get_name(data_path = config.data_directory)
            np.savez(name, **data)
            fig.savefig(name[:-4]+'.png')
            print('saved in results')
        except:
            name = self.get_name()
            np.savez(name, **data)
            fig.savefig(name[:-4]+'.png')
            print('saved in local temp')



