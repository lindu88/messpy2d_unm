import pickle
import os, platform
from collections import defaultdict
import attr
from pathlib import Path
p = Path(__file__).parent / 'messpy_config'


@attr.s(auto_attribs=True)
class Config:
    shots: int = 20
    list_of_solvents: list = ['Toluene', 'THF', 'H20', 'D20', 'DMSO', 'None']
    list_of_samples: list = ['Chlorophyll', 'AGP2', 'Cyclohexanol', 'Phenylisocyanat', 'TDI',
                             'Semi-Conductor', 'Cph1']
    exp_settings: dict = attr.Factory(lambda: defaultdict(dict))
    conf_path: str = p
    data_directory: Path = Path('D:') / 'results'
    testing = False

    def save(self, fname=p):
        with open(fname, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, fname) -> 'Config':
        with open(fname, 'rb') as f:
            d = pickle.load(f)
            return d

config = Config()
config_available = os.path.exists(p)
if config_available:
    f = attr.asdict(Config.load(p))
    for key, val in f.items():
        setattr(config, key, val)
config.data_directory = Path('D:\\') / 'results'





