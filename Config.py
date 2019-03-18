import yamlcfg
import yaml
import os, platform
p = os.path.dirname(__file__) + '/messpy_config.yml'
if not os.path.exists(p):
    with open(p, 'x') as f:
        f.write('{}')

config = yamlcfg.YamlConfig(path=p)

config.list_of_solvents = ['Toluene', 'THF', 'H20', 'D20', 'DMSO', 'None']
config.list_of_samples = ['Cyclohexanol', 'Phenylisocyanat', 'TDI']

