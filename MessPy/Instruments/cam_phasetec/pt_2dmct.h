#include "extcode.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef struct {
	int32_t dimSizes[3];
	uint16_t elt[1];
	} Uint16ArrayBase;
typedef Uint16ArrayBase **Uint16Array;

/*!
 * PT_2DMCT_GetFPATemp
 */
int32_t __cdecl PT_2DMCT_GetFPATemp(char TempKStr[], double *TempK,
	int32_t len);
/*!
 * PT_2DMCT_GetFrames
 */
int32_t __cdecl PT_2DMCT_GetFrames(int32_t Frames, int32_t Cols,
	int32_t Rows, int32_t Trigger, uint16_t FrameData[], int32_t len);
/*!
 * PT_2DMCT_Initialize
 */
int32_t __cdecl PT_2DMCT_Initialize(void);
/*!
 * PT_2DMCT_IntegrationTime
 */
int32_t __cdecl PT_2DMCT_IntegrationTime(double IntUs, double *MaxFrameRate);
/*!
 * PT_2DMCT_SetGainOffset
 */
int32_t __cdecl PT_2DMCT_SetGainOffset(int32_t Gain, int32_t Offset);
/*!
 * PT_2DMCT_SetWindowSize
 */
int32_t __cdecl PT_2DMCT_SetWindowSize(uint32_t WindowSize);
/*!
 * PT_2DMCT_GetFrames_3D_WRAPPED
 */
int32_t __cdecl PT_2DMCT_GetFrames_3D_WRAPPED(int32_t Frames, int32_t Cols,
	int32_t Rows, int32_t Trigger, Uint16Array *Data);

long __cdecl LVDLLStatus(char *errStr, int errStrLen, void *module);

/*
* Memory Allocation/Resize/Deallocation APIs for type 'Uint16Array'
*/
Uint16Array __cdecl AllocateUint16Array (int32_t *dimSizeArr);
int32_t __cdecl ResizeUint16Array (Uint16Array *hdlPtr, int32_t *dimSizeArr);
int32_t __cdecl DeAllocateUint16Array (Uint16Array *hdlPtr);

#ifdef __cplusplus
} // extern "C"
#endif

