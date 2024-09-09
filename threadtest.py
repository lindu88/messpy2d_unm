from PySide6.QtCore import QObject, Signal, Slot, QThread


class TestWorker(QObject):
    sigWorkDone = Signal(int)

    @Slot(int)
    def work(self, n):
        print(QThread.currentThread())
        while n < 100:
            n += 1

        self.sigWorkDone.emit(n + 1)


class TestController(QObject):
    sigWorkDone = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.testthread = QThread()
        self.worker = TestWorker()
        self.worker.sigWorkDone.connect(self.sigWorkDone.emit)
        self.worker.moveToThread(self.testthread)
        self.testthread.start()

    @Slot(int)
    def start_work(self, n):
        self.worker.work(n)
        print(self.thread)
        print(QThread.currentThread())


if __name__ == "__main__":
    from PySide6.QtCore import QCoreApplication

    app = QCoreApplication([])
    controller = TestController()
    controller.sigWorkDone.connect(lambda n: print(f"Work done: {n}"))
    controller.start_work(0)
    app.exec()
