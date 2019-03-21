import threading
from typing import Callable, List

from attr import attrs, attrib, Factory


@attrs
class CallBack:
    cb_func: Callable = attrib()
    call_in_thread: bool = attrib(True)
    join_thread: bool = attrib(True)


@attrs
class Signal:
    callbacks: List[CallBack] = attrib(Factory(list))

    def emit(self, *args):
        thr_to_join = []
        for cb in self.callbacks:
            try:
                if not cb.call_in_thread:
                    cb.cb_func(*args)
                else:
                    t = threading.Thread(target=cb.cb_func, args=args)
                    t.run()
                    if cb.join_thread:
                        thr_to_join.append(t)
            except:
                raise
        for t in thr_to_join:
            if t.is_alive():
                t.join()

    def connect(self, cb, do_threaded=True):
        self.callbacks.append(CallBack(cb, do_threaded))

    def disconnect(self, cb):
        cbs = [cb.cb_func for cb in self.callbacks]
        if cb in cbs:
            idx = cbs.find(cb)
            self.callbacks.pop(idx)
        else:
            raise ValueError("Can't disconnect %s from signal. Not found." % cb)