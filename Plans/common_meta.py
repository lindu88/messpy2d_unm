from Config import config
import attr, time
from typing import Optional

sample_parameters = {'name': 'Sample', 'type': 'group', 'children': [
    dict(name='Sample', type='str', value=''),
    dict(name='Solvent', type='list', values=config.list_of_solvents),
    dict(name='Excitation', type='str'),
    dict(name='Thickness', type='str'),
    dict(name='Annotations', type='str'),
    dict(name='Users:', type='str'),
]}



@attr.s(auto_attribs=True)
class Plan:
    name: str = None
    meta: Optional[dict] = None
    status: str = ''
    creation_time: float = attr.Factory(time.time)

    