#include "niimaq.h"
#include <stdio.h>
// self.ec(lib.imgSessionCopyBufferByNumber(sid, i, ffi.from_buffer(ba),
//                       lib.IMG_OVERWRITE_FAIL, ptr, buf_idx))
#include <stdint.h>
#define MAX_14BIT 16383


int16_t reorder_pixel(uInt16 *single_frame, uInt16 *reordered_frame)
{
    
    for (int index = 0; index < 128 * 128; index++)
    {
        int k = ((index % 128) / 4) * 512 + index % 4 + index / 128 * 4;
        reordered_frame[index] = MAX_14BIT - single_frame[k];
    }
    return 0;
}

int transpose(uInt16 *single_buf) {
    uInt16 temp;
    for (int i = 0; i < 128; i++) {
        for (int j = i + 1; j < 128; j++) {
            temp = single_buf[i * 128 + j];
            single_buf[i * 128 + j] = single_buf[j * 128 + i];
            single_buf[j * 128 + i] = temp;
        }
    }
    return 0;
}

int read_n_shots(int shots, uInt32 start_frame, SESSION_ID sid, uInt16 *buf,
                 int num_line_ranges, int line_ranges[], float linebuffer[],
                 uInt16* back)
{
    uInt16 ba[128 * 128];
    uInt16 ba_reordered[128 * 128];
    uInt32 copiedNumber;
    uInt32 copiedIndex;
    for (int i = 0; i < shots; i++)
    {
        //printf("Hey %i", i);
        int err = imgSessionCopyBufferByNumber(sid, i + start_frame, ba,
                                               IMG_OVERWRITE_FAIL,
                                               &copiedNumber,
                                               &copiedIndex);
        if (err != 0)
        {
            return err;
        }
        reorder_pixel(ba, ba_reordered);
        transpose(ba_reordered);
        // if (back != NULL) {
        //     for (int p = 0; p < 128*128; p++) {
        //         if (ba_reordered[p] > back[p]) {
        //             ba_reordered[p] = ba_reordered[p]-back[p];
        //         }
        //         else
        //         {
        //             ba_reordered[p] = 0;
        //         }
        //     }
        // }
        memcpy(buf + i * 128 * 128, ba_reordered, 128 * 128 * sizeof(uInt16));
        //printf("aftercopy %d", buf+i);        
        for (int j = 0; j < num_line_ranges; j++)
        {
            int bot_row = line_ranges[2*j];
            int top_row = line_ranges[2*j + 1];

            for (int k = 0; k < 128; k++)
            {
                for (int l = bot_row; l < top_row; l++)
                {
                    linebuffer[j * 128 * shots + k * shots + i] += ba_reordered[l * 128 + k];
                }
                linebuffer[j * 128 * shots + k * shots + i] /= (top_row - bot_row);
            }
        }
    }
    return 0;
}
