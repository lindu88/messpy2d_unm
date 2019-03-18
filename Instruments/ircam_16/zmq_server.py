# -*- coding: utf-8 -*-
"""
Created on Mon Sep 02 15:08:57 2013

@author: Owner
"""

import zmq, time
import numpy as np
from irdaq import InfraAD

cam = InfraAD()
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://127.0.0.1:5555")

def send_array(socket, A, flags=0, copy=False, track=False):
    """send a numpy array with metadata"""
    md = dict(
        dtype = str(A.dtype),
        shape = A.shape,
    )
    socket.send_json(md, flags|zmq.SNDMORE)
    return socket.send(A, flags, copy=copy, track=track)



while True:
    #  Wait for next request from client
    msg = socket.recv()
    print "Received request: ", msg

    if msg == 'read':
        send_array(socket, cam.transfer_data(), copy=False)
#        send_array(socket, np.zeros((800, 600), dtype=np.int16), copy=False, track=False)
        print "send"
    if msg[:9] == 'set_shots':
        print "set_shots " + str(int(msg[9:]))
        cam.set_shots(int(msg[9:]))
        socket.send("setting shots")

    if msg == 'quit':
        socket.send("quitting")
        quit()