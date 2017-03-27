import yamlcfg
import yaml
import os, platform
p = os.path.dirname(__file__) + '/messpy_config.yml'
if not os.path.exists(p):
    with open(p, 'x') as f:
        f.write('{}')

config = yamlcfg.YamlConfig(path=p)

if platform.node() == '2dir-PC':
    from Instruments.ircam_16 import irdaq
    _cam = irdaq.cam

    #from Instruments.spec_triax import spec
    #_spec = spec

    from Instruments.delay_line_mercury import dl
    _dl = dl
    hp = config.__dict__.get('Delay 1 Home Pos.', 8.80)
    _dl.home_pos = hp


    #from Instruments.FringeCounter import fc
    #_fc = fc

else:
    CamBase = object
    DelayBase = object
    SpecBase = object


