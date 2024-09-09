import cffi

ffi = cffi.FFI()
ffi.cdef("""
int32_t imgInterfaceOpen(const char* interface_name, uint32_t* ifid);
int32_t imgSessionOpen(uint32_t ifid, uint32_t* sid);
int32_t imgSessionSerialWrite(uint32_t sid, char *buffer, uint32_t *bufSize, int32_t timeout);
int32_t imgSessionSerialReadBytes(uint32_t sid, char *buffer, uint32_t *bufSize, int32_t timeout);
int32_t imgSessionSerialFlush(uint32_t sid);
""")


dll = ffi.dlopen("imaq.dll")

l = ffi.new("uint32_t[1]")
sid = ffi.new("uint32_t[1]")
iid = ffi.new("uint32_t[1]")

dll.imgInterfaceOpen(b"img0", iid)
dll.imgSessionOpen(iid[0], sid)


def write(tup):
    print(tup)
    dll.imgSessionSerialFlush(sid[0])
    l[0] = 4
    buf = ffi.from_buffer(bytes((tup[0], tup[1], tup[2], tup[3])))    
    dll.imgSessionSerialWrite(sid[0], buf, l, 200)    

def read():
    out_buf = ffi.from_buffer(bytes([0, 0, 0, 0]))
    dll.imgSessionSerialReadBytes(sid[0], out_buf, l, 200)
    return ffi.buffer(out_buf)[:]

def send_cmd(tup):
    write(tup)
    ans = read()
    print(bytes(tup).hex(' '), '->', ans.hex(' '))


def init():
    import json
    with open("init_cmds.json") as f:
        cmd_list = json.load(f)

    import time

    for cmd in cmd_list[:2]:    
        write(cmd)
        time.sleep(0.3)

    for cmd in cmd_list[2:]:
        send_cmd(cmd)

def set_amplification(i: int, darklevel: int):
    assert (0 <= i < 8)
    assert ( 0 <= darklevel < 256)
    k = darklevel
    send_cmd((113, 0, 0, 0))
    send_cmd((112, 79-i, 0, 0))
    send_cmd((64, 1, k, 0))
    send_cmd((64, 2, k, 0))
    send_cmd((64, 64, k, 0))
    send_cmd((64, 128, k, 0))

init()
set_amplification(7, 167)
buf = ffi.new("char[4]")
quit()
out_buf = ffi.new("char[4]")
for i in range(4):
    dll.imgSessionSerialFlush(sid[0])
    l[0] = 4
    dll.imgSessionSerialWrite(sid[0], buf, l, 1000)

    l[0] = 4
    print(l[0])


    print(ffi.string(out_buf))

