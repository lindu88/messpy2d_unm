import cffi

ffibuilder = cffi.FFI()
ffibuilder.set_source(
    "_imaqffi",
    '#include "read_loop.h"',
    sources=["read_loop.c"],
    include_dirs=[
        r"C:/Program Files (x86)/National Instruments/Shared/ExternalCompilerSupport/C/Include"
    ],
    library_dirs=[
        r"C:/Program Files (x86)/National Instruments/Shared/ExternalCompilerSupport/C/Lib64/MSVC/"
    ],
    libraries=["imaq"],
)

defs = ffibuilder.cdef("""
typedef int...   uInt32;
typedef int...   uInt16; 
typedef int...   Int32;
typedef int...   INTERFACE_ID;
typedef int...   SESSION_ID;
typedef int...   EVENT_ID;
typedef int...   PULSE_ID;
typedef int...   BUFLIST_ID;
typedef int...   IMG_ERR;
typedef int...   GUIHNDL;
typedef char     Int8;

typedef int USER_FUNC;

#define  IMG_TRIG_ACTION_CAPTURE             ...
#define  IMG_EXT_TRIG0                       ...
#define  IMG_LAST_BUFFER                     ...
#define  IMG_OLDEST_BUFFER                   ...
#define  IMG_CURRENT_BUFFER                  ...
#define  IMG_ATTR_FRAME_COUNT                ...

typedef enum {
    IMG_SIGNAL_NONE                 = 0xFFFFFFFF,
    IMG_SIGNAL_EXTERNAL             = 0,
    IMG_SIGNAL_RTSI                 = 1,
    IMG_SIGNAL_ISO_IN               = 2,
    IMG_SIGNAL_ISO_OUT              = 3,
    IMG_SIGNAL_STATUS               = 4,
    IMG_SIGNAL_SCALED_ENCODER       = 5,
    IMG_SIGNAL_SOFTWARE_TRIGGER     = 6
} IMG_SIGNAL_TYPE;


typedef enum {
    IMG_OVERWRITE_GET_OLDEST         = 0,
    IMG_OVERWRITE_GET_NEXT_ITERATION = 1,
    IMG_OVERWRITE_FAIL               = 2,
    IMG_OVERWRITE_GET_NEWEST         = 3
} IMG_OVERWRITE_MODE;

USER_FUNC imgInterfaceOpen(const Int8* interface_name, INTERFACE_ID* ifid);
USER_FUNC imgSessionOpen(INTERFACE_ID ifid, SESSION_ID* sid);
USER_FUNC imgSessionStatus(SESSION_ID sid, uInt32* boardStatus, uInt32* bufIndex);
USER_FUNC imgClose(uInt32 void_id, uInt32 freeResources);
USER_FUNC imgSnap(SESSION_ID sid, void **bufAddr);
USER_FUNC imgSnapArea(SESSION_ID sid, void **bufAddr,uInt32 top,uInt32 left, uInt32 height, uInt32 width,uInt32 rowBytes);
USER_FUNC imgGrabSetup(SESSION_ID sid, uInt32 startNow);
USER_FUNC imgGrab(SESSION_ID sid, void** bufPtr, uInt32 syncOnVB);
USER_FUNC imgGrabArea(SESSION_ID sid, void** bufPtr, uInt32 syncOnVB, uInt32 top, uInt32 left, uInt32 height, uInt32 width, uInt32 rowBytes);
USER_FUNC imgRingSetup(SESSION_ID sid,  uInt32 numberBuffer,void* bufferList[], uInt32 skipCount, uInt32 startnow);
USER_FUNC imgSequenceSetup(SESSION_ID sid,  uInt32 numberBuffer,void* bufferList[], uInt32 skipCount[], uInt32 startnow, uInt32 async);
USER_FUNC imgGetAttribute(uInt32 void_id, uInt32 attribute, void* value);
USER_FUNC imgSessionReleaseBuffer(SESSION_ID sid);
USER_FUNC imgSessionStopAcquisition(SESSION_ID sid);
USER_FUNC imgSessionStartAcquisition(SESSION_ID sid);
USER_FUNC imgSessionExamineBuffer2(SESSION_ID sid, uInt32 whichBuffer, uInt32 *bufferNumber, void** bufferAddr);
USER_FUNC imgSessionCopyBufferByNumber(SESSION_ID sid, uInt32 bufNumber, void* userBuffer, IMG_OVERWRITE_MODE overwriteMode,
                        uInt32* copiedNumber, uInt32* copiedIndex);
USER_FUNC imgShowError(int err, char* msg); 
USER_FUNC imgSessionTriggerConfigure2(SESSION_ID sid, IMG_SIGNAL_TYPE triggerType, 
    uInt32 triggerNumber, uInt32 polarity, uInt32 timeout, uInt32 action);
                       
int read_n_shots(int shots, uInt32 start_frame, SESSION_ID sid, uInt16 *buf,
                 int num_line_ranges, int *line_ranges, float *linebuffer, uInt16 *back);
""")
ffibuilder.compile(verbose=True)
