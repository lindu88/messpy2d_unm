# -*- coding: utf-8 -*-
"""
Created on Mon Sep 02 15:25:40 2013

@author: tillsten
"""


import zmq
import numpy
import subprocess



def send_array(socket, A, flags=0, copy=True, track=False):
    """send a numpy array with metadata"""
    md = dict(
        dtype = str(A.dtype),
        shape = A.shape,
    )
    socket.send_json(md, flags|zmq.SNDMORE)
    return socket.send(A, flags, copy=copy, track=track)


def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = buffer(msg)
    A = numpy.frombuffer(buf, dtype=md['dtype'])
    return A.reshape(md['shape'])


import os
import threading
class zmq_cam(object):
    shots = 140
    has_external = True

    def __init__(self):
#        server_fname ='"' +  os.path.dirname(__file__) + r'"\zmq_server.py"'
#
#        self.server = subprocess.Popen("python " + server_fname)

        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://127.0.0.1:5555")

    def read_cam(self):
        self.socket.send ("read")
        a = recv_array(self.socket, copy=True, track=False)
        print "recv"
        d = a /3276.7
        return d[:, :32].T, d[:, 32:64].T, a[:, -1] > 5000., d[:, [64, 64+8]]

    def set_shots(self, shots):
        self.socket.send("set_shots"+str(shots))
        print self.socket.recv()
        zmq_cam.shots = shots

    def __del__(self):
        pass
        #self.socket.send('quit')
#        print self.socket.recv()
#        print self.server.poll()

cam = zmq_cam()
if __name__ == "__main__":
#    import matplotlib.pyplot as plt
#    cam.set_shots(300)
    import time
    t = time.time()
    for i in range(10):
        cam.read_cam()[0].shape

    print (time.time() - t) / 10.