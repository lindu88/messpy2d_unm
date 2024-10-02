#include "niimaq.h"

int read_n_shots(int shots, uInt32 start_frame, SESSION_ID sid, uInt16 *buf,
                 int num_line_ranges, int line_ranges[], float linebuffer[],
                 uInt16 *back, uInt16 *dead_pixel_list, int num_dead_pixels);