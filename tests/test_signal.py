from Signal import Signal

class Test:
    def __init__(self):
        self.signal = Signal()

def test_signal():
    def print_bla(x):
        print(x)

    t = Test()
    t.signal.connect(print_bla)

