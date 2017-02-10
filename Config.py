import yamlcfg
import yaml
import os
p = os.path.dirname(__file__) + '/messpy_config.yml'
if not os.path.exists(p):
    with open(p, 'x') as f:
        f.write('{}')

config = yamlcfg.YamlConfig(path=p)

