# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import types
import time
import numpy
import serial

DEBUG = True
CRLF = '\r\n'.encode('ascii')

COMMAND_LIST = [    
    ('counter_value', 0, (0, 65535)),
    ('pd1_offset', 1, (0, 4095)),
    ('pd2_offset', 2, (0, 4095)),
    ('dac_flag', 3, (0, 1)),
    ('rs232_mode', 4, (0, 2)),
    ('target_counts', 5, (0, 4095)),
    ('output_mode', 6, (0, 1)),
    ('test_mode', 9, (0, 1)),
    ('pd_signal', 20, (0, 2)),
    ('pd1_polarity', 21, (0, 2)),
    ('pd2_polarity', 22, (0, 2)),
    ('pd1_score_list', 10, None, 'G', 'ASCII'),
    ('compilation_stamp', 99, None, 'G', 'ASCII'),
    ('counter_table', 12, None, 'G', True),
    ('start_offset_calc', 0, None, 'T'),
    ('stop_offset_calc', 1, None, 'T'),

]

class FringeCounter(object):
    '''
    FringeCounter, controling the HellDunkelZaehler from Hamm Group.
    '''
    def __init__(self, com_port="COM3"):
        for c in COMMAND_LIST:
            self.make_command(*c)


        self.port = serial.Serial(port=com_port, baudrate=115200*5)
        self.port.timeout = 4

    def send_cmd(self, cmd):
        '''
        Encodes cmd to ASCII, adds lineterminator, writes cmd to port
        and check the answer. If successful, return the answer.
        '''
        cmd = cmd.encode('ASCII') + CRLF
        if DEBUG:
            print('SEND: ', cmd)
        expected_answ = cmd[0:1].lower() + cmd[1:5]
        self.port.write(cmd)
        answ = self.port.read_until(terminator=CRLF)
        if DEBUG:
            print('ANSW: ', answ)
        if answ[0] == expected_answ[0]:
            return answ[:-2]
        else:
            raise IOError('Send: {0}, Answ: {1}'.format(cmd, answ))

    def make_command(self, name, addr, value_range=None, mode='SG', extra_output=False):
        'helper method to generate setter and getter functions'
        if 'S' in mode:
            def setter(value):
                if value_range is not None:
                    if not value_range[0] <= value <= value_range[1]:
                        err_msg = 'Value of {} outside allowed range of {}-{}'
                        raise ValueError(err_msg.format(value, *value_range))

                cmd = 'S {0: 02d} {1: d}'.format(addr, value)
                self.send_cmd(cmd)
            #setter = types.MethodType(setter, self, FringeCounter)
            setattr(self, "set_" + name, setter)
        if 'G' in mode:
            def getter():
                cmd = 'G {0: 02d} 0'.format(addr)
                ans = self.send_cmd(cmd)
                if extra_output == 'ASCII':
                    n = int(ans.split(b' ')[1])
                    ans = [ans]
                    for i in range(n):
                        ans.append(self.port.read_until(CRLF))
                    
                elif extra_output: 
                    ans = (ans, self.port.read_until(CRLF))
                    
                else:
                    ans = int(ans.split(b' ')[1])
                return ans
                
            #getter = types.MethodType(getter, self, FringeCounter)
            setattr(self, "get_" + name, getter)
        if 'T' in mode:
            def func():
                cmd = 'T {0: 02d} 0'.format(addr)
                ans = self.send_cmd(cmd)
                if extra_output:
                    ans = (ans, self.port.read_until(CRLF))
                else:
                    ans = ans
                return ans
                
            #getter = types.MethodType(getter, self, FringeCounter)
            setattr(self,   name, func)

    def prime_fc(self, shots):
        "primes the fringe counter to record shots-counter values"
        self.shots = shots
        self.port.flushInput()
        self.set_target_counts(shots)
        self.time = time.time()

    def get_ct(self):
        self.port.write('g12 0\r\n')
        ans = self.port.read_until(CRLF)
        ans[]

    def get_values(self):
        print('time:', time.time() - self.time)
        while True:
            tc = self.get_target_counts()
            #print(tc)
            time.sleep(0.1)
            if tc  ==  0:
                break


        b = self.get_counter_table()

        #print(b[0], len(b[1]))
        return numpy.frombuffer(b[1][:-2], 'h')

    def set_counter(self, value=0):
        self.set_counter_value(32000)




fc = FringeCounter()



if __name__ == '__main__':
    import time
    import struct
    a = fc
    print(dir(a))
#    print(a.get_pd1_offset())
#    print(a.get_pd2_offset())
#    print(a.get_counter_value())
    print(a.start_offset_calc())
    time.sleep(1)
    print(a.stop_offset_calc())
    #a.set_pd1_offset(150)
    #a.set_pd2_offset(150)
    print(a.get_pd1_offset())
    print(a.get_pd2_offset())
    print(a.get_pd1_score_list())
    time.sleep(0.01)
    #print(a.get_counter_value())
    time.sleep(0.01)
    
    a.set_target_counts(1000)
    
    for i in range(3):
        b = a.get_counter_table()
        print(a.get_target_counts())
        time.sleep(0.2)
    print(b[1][:])
    print(struct.unpack('1000h', b[1][:-2]))
    a.port.close()