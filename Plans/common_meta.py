from Config import config
import attr, time, json
from datetime import datetime
from typing import Optional, ClassVar, Tuple
from qtpy.QtCore import QObject, Signal
from pathlib import Path
from Instruments.interfaces import IDevice

sample_parameters = {'name': 'Sample', 'type': 'group', 'children': [
    dict(name='Sample', type='str', value=''),
    dict(name='Solvent', type='list', values=config.list_of_solvents),
    dict(name='Excitation', type='str'),
    dict(name='Thickness', type='str'),
    dict(name='Annotations', type='str'),
    dict(name='Users:', type='str'),
]}


@attr.s(auto_attribs=True)
class Plan(QObject):
    plan_shorthand: ClassVar[str]

    name: str = ''
    meta: Optional[dict] = None
    status: str = ''
    creation_dt: datetime = attr.Factory(datetime.now)

    sigPlanFinished: ClassVar[Signal] = Signal()
    sigPlanStarted: ClassVar[Signal] = Signal()

    def get_file_name(self) -> Tuple[Path, Path]:
        """Builds the filename and the metafilename"""
        date_str = self.creation_dt.strftime("%y-%m-%d %H:%M")
        name = f"{date_str} {self.name}.{self.plan_shorthand}.messpy"
        meta_name = f"{date_str} {self.name}.{self.plan_shorthand}.json"
        p = Path(config.data_directory)
        if not p.exists():
            raise IOError("Data path in config not existing")
        return p / name, p / meta_name

    def save_meta(self):
        """Saves the metadata in the metafile"""
        self.get_app_state()
        if self.meta is not None:
            _, meta_file = self.get_file_name()
            with meta_file.open('w') as f:
                json.dump(self.meta, f)

    def get_app_state(self):
        """Collects all devices states."""
        for i in IDevice.registered_devices:
            self.meta[i.name] = i.get_state()

