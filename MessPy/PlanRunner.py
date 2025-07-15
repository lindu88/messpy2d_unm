from typing import ClassVar, Literal, Optional

from attr import Factory, define
from loguru import logger
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from MessPy.Plans.PlanBase import Plan


@define
class PlanRunner(QObject):
    plan: Optional[Plan] = None
    state: Literal["running", "paused", "no_plan"] = "no_plan"

    sigPlanStopped: ClassVar[pyqtSignal] = pyqtSignal(bool)
    sigPlanStarted: ClassVar[pyqtSignal] = pyqtSignal(bool)
    sigPlanPaused: ClassVar[pyqtSignal] = pyqtSignal(bool)

    def __attr_post_init__(self):
        super().__attr_post_init__()

    @pyqtSlot(plan)
    def start_plan(self, plan: Plan):
        self.plan = plan
        self.state = "running"
        self.sigPlanStarted.emit(True)
        if not plan.is_async:
            pass

    @pyqtSlot()
    def pause_plan(self):
        if self.plan:
            self.state = "paused"
            self.sigPlanPaused.emit(True)

    @pyqtSlot()
    def resume_plan(self):
        if self.plan:
            self.state = "running"
            self.sigPlanPaused.emit(False)

    @pyqtSlot()
    def stop_plan(self):
        if self.plan:
            self.plan.stop_plan()
            self.sigPlanStopped.emit(True)
            self.state = "no_plan"
