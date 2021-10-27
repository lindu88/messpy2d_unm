import os.path
import threading
import typing as T
from pathlib import Path

import attr
import matplotlib.pyplot as plt
import numpy as np
from qtpy.QtCore import QObject, Signal

from Config import config
from ControlClasses import Cam
from Instruments.dac_px.pxdac import AOM
import hdf


@attr.s(auto_attribs=True, cmp=False)
class GVDScan(QObject):
    name: str
    meta: dict
    cam: Cam
    aom: AOM
    gvd_list: T.Sized[float]
    gvd_idx: int = 0
    timeout: float = 3
    scan_mode: T.Literal['GVD', 'FOD', 'TOD'] = 'GVD'

    observed_channel: T.Optional[int] = None

    sigPointRead = Signal()

    def __attrs_post_init__(self):
        QObject.__init__(self)
        n_wl = len(self.gvd_list)
        n_pix = self.cam.channels
        if self.aom.calib is None:
            raise ValueError("Shaper must have an calibration")
        self.wls = np.zeros((n_wl, n_pix))
        self.probe = np.zeros((n_wl, n_pix))
        self.probe2 = np.zeros((n_wl, n_pix))
        self.ref = np.zeros((n_wl, n_pix))
        self.signal = np.zeros((n_wl,  n_pix, self.cam.sig_lines))

        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)

    def make_step_gen(self):

        for self.gvd_idx, value in enumerate(self.gvd_list):
            d = {self.scan_mode: value}
            t = threading.Thread(target=self.aom.set_dispersion_correct, kwargs=d)
            t.start()
            while t.is_alive():
                yield
            t = threading.Thread(target=self.cam.read_cam)
            t.start()
            while t.is_alive():
                yield

            probe = self.cam.last_read.lines[0, :]
            probe2 = self.cam.last_read.lines[1, :]
            ref = self.cam.last_read.lines[2, :]
            sig = self.cam.last_read.signals

            self.probe[self.gvd_idx, :] = probe
            self.probe2[self.gvd_idx, :] = probe2
            self.ref[self.gvd_idx, :] = ref
            self.signal[self.gvd_idx, ...] = sig
            self.shown_signal = sig[:, :, 1].sum(1)
            self.sigPointRead.emit()
            yield

        self.save()
        yield

    def get_name(self, data_path=False):
        if data_path:
            p = Path(data_path)
        else:
            p = r"C:\Users\2dir\messpy2d\data_temps"
        dname = p + f"\{self.name}_spectrumScan.npz"

        if os.path.exists(dname):
            name_exists = True
            i = 0
            while name_exists == True:
                dname = p + f"\{self.name}{i}_spectrumScan.npz"
                i += 1
                if os.path.exists(dname) == False:
                    name_exists = False
        self._name = dname
        return self._name

    def save(self):
        return
        data = {'cam': self.cam.name}
        # data['meta'] = self.meta
        data['wl'] = self.wls
        data['probe'] = self.probe
        data['ref'] = self.ref
        data['signal'] = self.signal
        fig = plt.figure()
        plt.plot(self.wls[:, 64], self.probe[:, 64], label='Probe')
        plt.plot(self.wls[:, 64], self.ref[:, 64], label='Ref')
        plt.legend()
        fig.show()
        try:
            name = self.get_name(data_path=config.data_directory)
            np.savez(name, **data)
            fig.savefig(name[:-4] + '.png')
            print('saved in results')
        except:
            name = self.get_name()
            np.savez(name, **data)
            fig.savefig(name[:-4] + '.png')
            print('saved in local temp')
