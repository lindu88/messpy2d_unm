from Config import config
import attr

samp = {'name': 'Sample', 'type': 'group', 'children': [
    dict(name='Sample', type='list', values=config.list_of_samples),
    dict(name='Solvent', type='list', values=config.list_of_solvents),
    dict(name='Excitation', type='str'),
    dict(name='Thickness', type='str'),
    dict(name='Annotations', type='str'),
    dict(name='Users:', type='str'),]}
    
    

@attr.s(auto_attribs=1)
class Plan:
    name: str
    meta: dict 
    status: str = ''

    