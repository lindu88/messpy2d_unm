import pickle
import os, platform
from collections import defaultdict
import attr
p = os.path.dirname(__file__) + '/messpy_config.json'


@attr.s(auto_attribs=True)
class Config:
    shots: int = 20
    list_of_solvents: list = ['Toluene', 'THF', 'H20', 'D20', 'DMSO', 'None']
    list_of_samples: list = ['Cyclohexanol', 'Phenylisocyanat', 'TDI']
    exp_settings: dict = attr.Factory(lambda: defaultdict(dict))
    conf_path: str = p

    def save(self, fname=p):
        with open(fname, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, fname):
        with open(fname, 'rb') as f:
            d = pickle.load(f)
            return d

p = os.path.dirname(__file__) + '\\messpy_config'
no_config = not os.path.exists(p)
config = Config()
if no_config:
    pass
else:
    config.load(p)

