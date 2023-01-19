from serial import Serial

class SC10:

    def __init__(self, comport='COM12'):
        self.con = Serial(
            comport=comport,
            baudrate=9600,            
        )
        

    def open_shutter(self):
        pass

    def close_shutter(self):
        pass

    def toggle(self):
        pass

    def is_open(self) -> bool:
        pass