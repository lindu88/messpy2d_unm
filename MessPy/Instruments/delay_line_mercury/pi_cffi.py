import cffi
import os, sys
import ctypes as ct
import time
#ct.WinDLL('PI_GCS_DLL_x64')



#header = ''.join(open('PI_GCS2_DLL.h').readlines()[126:-3])
header = ''.join(open('PI_GCS2_DLL.h').readlines()[126:300])
header = header.replace('PI_FUNC_DECL', '')
header = header.replace('__int64', 'int64_t')
print(header)



ffi = cffi.FFI()
ax = b'1'

def on_target():
    bool_out = ffi.new('bool[1]')
    a.PI_qONT(i, ax, bool_out)
    return bool_out[0]

def qMov)

#ffi.cdef("int PI_ConnectUSB(const char* szDescription);")
ffi.cdef(header)
a = ffi.dlopen('PI_GCS2_DLL_x64.dll')
i = a.PI_ConnectUSB(b'0145500652')
print(i)
print(a.PI_INI(i, b'1'))
print(a.PI_FNL(i, b'1'))

print(a.PI_MOV(i, b'1', [7.5]))

#while not on_target():
#    time.sleep(0.1)
#print(a.PI_VCO(i, b'1', [True]))
#print(a.PI_VEL(i, b'1', [1.5]))
#time.sleep(0.5)
#print(a.PI_VEL(i, b'1', [0.]))
