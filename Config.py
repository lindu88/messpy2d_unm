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

    from Instruments.delay_line_gmc2 import dl
    _dl2 = dl
    hp = config.__dict__.get('Delay 2 Home Pos.', 8.80)
    _dl2.home_pos = hp

    #from Instruments.FringeCounter import fc
    #_fc = fc
else:
    has_second_delaystage = False
    CamBase = object
    from Instruments.mocks import CamMock, DelayLineMock
    _cam = CamMock()
    _dl = DelayLineMock()
    DelayBase = object
    SpecBase = object


config.list_of_solvents = ['Toluene', 'THF', 'H20', 'D20', 'DMSO', 'None']
config.list_of_samples = ['Cyclohexanol', 'Phenylisocyanat', 'TDI']

