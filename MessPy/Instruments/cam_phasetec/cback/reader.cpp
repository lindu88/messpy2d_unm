#include <cstdio>
#include <vector>
#include <stdexcept>
#include "imaq.h"

#define NUM_RING_BUFFERS 10000
constexpr int PIXEL_X = 128;
constexpr int PIXEL_Y = 128;
constexpr int bytes_per_pixel = 2;
constexpr int bytes_per_image = PIXEL_X * PIXEL_Y * bytes_per_pixel;


class ImaqCam
{
public:
    INTERFACE_ID iid = 0;
    BUFLIST_ID bid = 0;
    SESSION_ID sid = 0;
    int shots = 1000;
    char out[500];
    bool running = false;
    Int8 *ImaqBuffers[NUM_RING_BUFFERS];
    std::vector<uInt16> data;

    void errChk(int i)
    {
        if (i < 0)
        {
            imgShowError(i, out);
            printf("%s", out);
            throw std::runtime_error(out);
        }
    };

    int init()
    {
        errChk(imgInterfaceOpen("img0", &iid));
        errChk(imgSessionOpen(iid, &sid));
        errChk(imgCreateBufList(NUM_RING_BUFFERS, &bid));

        for (int i = 0; i < NUM_RING_BUFFERS; i++)
        {
            errChk(imgCreateBuffer(sid, IMG_HOST_FRAME, 0, (void **)&ImaqBuffers[i]));
            errChk(imgSetBufferElement2(bid, i, IMG_BUFF_ADDRESS, ImaqBuffers[i]));
            errChk(imgSetBufferElement2(bid, i, IMG_BUFF_SIZE, 128 * 128 * 2));
            errChk(imgSetBufferElement2(bid, i, IMG_BUFF_COMMAND, IMG_CMD_NEXT));
        }

        errChk(imgSetBufferElement2(bid, shots, IMG_BUFF_COMMAND, IMG_CMD_NEXT));
        return 1;
    }

    int set_shots(int s)
    {
        errChk(imgSetBufferElement2(bid, shots, IMG_BUFF_COMMAND, IMG_CMD_NEXT));
        printf("%s", "bla");
        errChk(imgSetBufferElement2(bid, s, IMG_BUFF_COMMAND, IMG_CMD_STOP));
        shots = s;
        data.resize(PIXEL_X*PIXEL_Y*shots);
        return 1;
    }

    int start()
    {
        errChk(imgSessionConfigure(sid, bid));
        errChk(imgSessionAcquire(sid, true, 0));
        return 1;
    }

    int info()
    {
        uInt32 status;
        uInt32 count;
        errChk(imgSessionStatus(sid, &status, &count));
        return count;
    }

    int read_cam() {
        if (!running) {
            start();
        }

        auto start_frame = last_valid_frame();
        for (int i = 0; i < shots; i++)
        {
            uInt32 buf_num;
            void* buf_addr;
            errChk(imgSessionExamineBuffer2(sid, start_frame+1, &buf_num, &buf_addr)); 
            memcpy(&data[i*PIXEL_X*PIXEL_Y], buf_addr, bytes_per_image);
            errChk(imgSessionReleaseBuffer(sid));
        }
        

    }

    inline uInt32 last_valid_frame() {
        uInt32 last_valid_frame;
        errChk(imgGetAttribute(sid, IMG_ATTR_LAST_VALID_FRAME, &last_valid_frame));
        return last_valid_frame;
    }

    uInt32 ImaqCallback(SESSION_ID sid, IMG_ERR err, IMG_SIGNAL_TYPE signalType, uInt32 signalIdentifier, void *userdata)
    {
        return 1;
    }
};