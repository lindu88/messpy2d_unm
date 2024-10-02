#include "niimaq.h"
#include <stdio.h>
#include <stdint.h>

#define MAX_14BIT 16383
#define FRAME_SIZE (128 * 128)
#define ROW_SIZE 128

int16_t reorder_pixel(uInt16 single_frame[FRAME_SIZE], uInt16 reordered_frame[FRAME_SIZE])
{
    for (int index = 0; index < FRAME_SIZE; index++)
    {
        int k = ((index % ROW_SIZE) / 4) * 512 + index % 4 + index / ROW_SIZE * 4;
        reordered_frame[index] = MAX_14BIT - single_frame[k];
    }
    return 0;
}

int dead_pixel_replacement(uint16_t *frame, int *dead_pixel_list, int num_dead_pixels)
{
    for (int i = 0; i < num_dead_pixels; i++)
    {
        // Replace dead pixel by average of above and below
        // We have to check if the dead pixel is at the top or bottom of the frame
        uint16_t average;
        int dead_pixel = dead_pixel_list[i];
        if (dead_pixel < ROW_SIZE)
        {
            int below_pixel = dead_pixel + ROW_SIZE;
            average = frame[below_pixel];
        }
        else if (dead_pixel >= FRAME_SIZE - ROW_SIZE)
        {
            int above_pixel = dead_pixel - ROW_SIZE;
            average = frame[above_pixel];
        }
        else
        {
            int above_pixel = dead_pixel - ROW_SIZE;
            int below_pixel = dead_pixel + ROW_SIZE;
            average = (frame[above_pixel] / 2 + frame[below_pixel] / 2);
            frame[dead_pixel] = average;
        }
    }
    return 0;
}

int transpose(uInt16 *single_buf)
{
    uInt16 temp;
    for (int i = 0; i < ROW_SIZE; i++)
    {
        for (int j = i + 1; j < ROW_SIZE; j++)
        {
            temp = single_buf[i * ROW_SIZE + j];
            single_buf[i * ROW_SIZE + j] = single_buf[j * ROW_SIZE + i];
            single_buf[j * ROW_SIZE + i] = temp;
        }
    }
    return 0;
}

int subtract_frame(uInt16 *single_frame, uInt16 *back_frame)
{
    for (int index = 0; index < FRAME_SIZE; index++)
    {
        if (single_frame[index] > back_frame[index])
        {
            single_frame[index] = single_frame[index] - back_frame[index];
        }
        else
        {
            single_frame[index] = 0;
        }
    }
    return 0;
}

int read_n_shots(int shots, uInt32 start_frame, SESSION_ID sid, uInt16 *buf,
                 int num_line_ranges, int line_ranges[], float linebuffer[],
                 uInt16 *back, int *dead_pixel_list, int num_dead_pixels)
{
    uInt16 ba[FRAME_SIZE];
    uInt16 ba_reordered[FRAME_SIZE];
    uInt32 copiedNumber;
    uInt32 copiedIndex;
    for (int i_cur_shot = 0; i_cur_shot < shots; i_cur_shot++)
    {
        int err = imgSessionCopyBufferByNumber(sid, i_cur_shot + start_frame, ba,
                                               IMG_OVERWRITE_FAIL,
                                               &copiedNumber,
                                               &copiedIndex);
        if (err != 0)
        {
            return err;
        }
        reorder_pixel(ba, ba_reordered);
        transpose(ba_reordered);
        if (back != NULL)
        {
            subtract_frame(ba_reordered, back);
        }
        if (dead_pixel_list != NULL)
        {
            dead_pixel_replacement(ba_reordered, dead_pixel_list, num_dead_pixels);
        }
        memcpy(buf + i_cur_shot * FRAME_SIZE, ba_reordered, FRAME_SIZE * sizeof(uInt16));

        for (int j = 0; j < num_line_ranges; j++)
        {
            int bot_row = line_ranges[2 * j];
            int top_row = line_ranges[2 * j + 1];
            for (int n_chan = 0; n_chan < ROW_SIZE; n_chan++)
            {
                size_t idx = i_cur_shot * ROW_SIZE * num_line_ranges + j * ROW_SIZE + n_chan;
                for (int l = bot_row; l < top_row; l++)
                {
                    linebuffer[idx] += ba_reordered[l * ROW_SIZE + n_chan];
                }
                linebuffer[idx] /= 1.0 * (top_row - bot_row);
            }
        }
    }
    return 0;
}