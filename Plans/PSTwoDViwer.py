class PumpProbeStarter(PlanStartDialog):
    title = "New Pump-probe Experiment"
    viewer = PumpProbeViewer
    experiment_type = 'Pump-Probe'

    def setup_paras(self):
        has_rot = self.controller.rot_stage is not None
        has_shutter = self.controller.shutter is not None

        tmp = [{'name': 'Filename', 'type': 'str', 'value': 'temp'},
               {'name': 'Operator', 'type': 'str', 'value': ''},
               {'name': 'Shots', 'type': 'int', 'max': 4000, 'decimals': 5,
                'step': 500, 'value': 100},
               {'name': 'Linear Range (-)', 'suffix': 'ps', 'type': 'float', 'value': -1},
               {'name': 'Linear Range (+)', 'suffix': 'ps', 'type': 'float', 'value': 1},
               {'name': 'Linear Range (step)', 'suffix': 'ps', 'type': 'float', 'min': 0.01},
               {'name': 'Logarithmic Scan', 'type': 'bool'},
               {'name': 'Logarithmic End', 'type': 'float', 'suffix': 'ps',
                'min': 0.},
               {'name': 'Logarithmic Points', 'type': 'int', 'min': 0},
               dict(name="Add pre-zero times", type='bool', value=False),
               dict(name="Num pre-zero points", type='int', value=10, min=0, max=20),
               dict(name="Pre-Zero pos", type='float', value=-60., suffix='ps'),
               dict(name='Use Shutter', type='bool', value=True, enabled=has_shutter, visible=has_shutter),
               dict(name='Use Rotation Stage', type='bool', value=True, enabled=has_rot, visible=has_rot),
               dict(name='Angles in deg.', type='str', value='0, 45', enabled=has_rot, visible=has_rot)]

        for c in self.controller.cam_list:
            if c.cam.changeable_wavelength:
                name = c.cam.name
                tmp.append(dict(name=f'{name} center wls', type='str', value='0'))

        two_d = {'name': 'Exp. Settings', 'type': 'group', 'children': tmp}

        params = [samp, two_d]
        self.paras = Parameter.create(name='Pump Probe', type='group', children=params)
        config.last_pump_probe = self.paras.saveState()

    def create_plan(self, controller: Controller):
        p = self.paras.child('Exp. Settings')
        s = self.paras.child('Sample')
        t_list = np.arange(p['Linear Range (-)'],
                           p['Linear Range (+)'],
                           p['Linear Range (step)']).tolist()
        if p['Logarithmic Scan']:
            t_list += (np.geomspace(p['Linear Range (+)'], p['Logarithmic End'], p['Logarithmic Points']).tolist())

        if p['Add pre-zero times']:
            n = p['Num pre-zero points']
            pos = p['Pre-Zero pos']
            times = np.linspace(pos - 1, pos, n).tolist()
            t_list = times + t_list

        if p['Use Rotation Stage'] and self.controller.rot_stage:
            s = p['Angles in deg.'].split(',')
            angles = list(map(float, s))
        else:
            angles = None

        cwls = []
        for c in self.controller.cam_list:
            if c.cam.changeable_wavelength:
                name = c.name
                l = p[f'{name} center wls'].split(',')
                cam_cwls = []
                for s in l:
                    if s[-1] == 'c':
                        cam_cwls.append(1e7/float(s[:-1]))
                    else:
                        cam_cwls.append(float(s))
                cwls.append(cam_cwls)
            else:
                cwls.append([0.])
        print(cwls)
        self.save_defaults()
        p = PumpProbePlan(
            name=p['Filename'],
            meta=self.paras.saveState(),
            t_list=np.asarray(t_list),
            shots=p['Shots'],
            controller=controller,
            center_wl_list=cwls,
            use_shutter=p['Use Shutter'] and self.controller.shutter,
            use_rot_stage=p['Use Rotation Stage'],
            rot_stage_angles=angles
        )
        return p