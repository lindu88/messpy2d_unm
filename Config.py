import json
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
        with open(fname, 'w') as f:
            json.dump(attr.asdict(self), f)

    def load(self, fname):
        with open(fname, 'r') as f:
            d = json.load(f)
            self.__dict__.update(d)

p = os.path.dirname(__file__) + '/messpy_config.json'
no_config = not os.path.exists(p)
config = Config()
if no_config:
    pass
else:
    config.load(p)

