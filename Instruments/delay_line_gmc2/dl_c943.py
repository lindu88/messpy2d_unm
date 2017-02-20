# -*- coding: utf-8 -*-
"""
Created on Tue Sep 03 14:24:02 2013

@author: tillsten
"""

#import cffi

#ffi = cffi.FFI()
#ffi.cdef(
from ctypes import *
import time
cstr = """

/////////////////////////////////////////////////////////////////////////////
// DLL initialization and comm functions
int		C843_FUNC_DECL	C843_Connect(const int iBoardNumber);
BOOL	C843_FUNC_DECL	C843_IsConnected(const int iId);
void	C843_FUNC_DECL	C843_CloseConnection(const int iId);
int		C843_FUNC_DECL	C843_GetError(const int iId);
BOOL	C843_FUNC_DECL	C843_SetErrorCheck(const int iId, BOOL bErrorCheck);
BOOL	C843_FUNC_DECL	C843_TranslateError(int errNr, char* szBuffer, const int maxlen);
int		C843_FUNC_DECL	C843_GetCurrentBoardId(const int iBoardNumber);


/////////////////////////////////////////////////////////////////////////////
// general
BOOL C843_FUNC_DECL C843_qERR(const int iId, int* pnError);
BOOL C843_FUNC_DECL C843_qIDN(const int iId, char* buffer, const int maxlen);
BOOL C843_FUNC_DECL C843_INI(const int iId, char* const szAxes);
BOOL Cdll.C843_CloseConnection843_FUNC_DECL C843_CLR(const int ID, char* const szAxes);

BOOL C843_FUNC_DECL C843_MOV(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_qMOV(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_MVR(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_IsMoving(const int iId, char* const szAxes, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_qONT(const int iId, char* const szAxes, BOOL* pbValarray);

BOOL C843_FUNC_DECL C843_DFF(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_qDFF(const int iId, char* const szAxes, double* pdValarray);

BOOL C843_FUNC_DECL C843_DFH(const int iId, char* const szAxes);
BOOL C843_FUNC_DECL C843_qDFH(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_GOH(const int iId, char* const szAxes);

BOOL C843_FUNC_DECL C843_qPOS(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_POS(const int iId, char* const szAxes, double* pdValarray);

BOOL C843_FUNC_DECL C843_HLT(const int iId, char* const szAxes);
BOOL C843_FUNC_DECL C843_STP(const int iId);

BOOL C843_FUNC_DECL C843_qCST(const int iId, char* const szAxes, char* names, const int maxlen);
BOOL C843_FUNC_DECL C843_CST(const int iId, char* const szAxes, char* names);
BOOL C843_FUNC_DECL C843_qVST(const int iId, char* buffer, const int maxlen);
BOOL C843_FUNC_DECL C843_qTVI(const int iId, char* axes, const int maxlen);
BOOL C843_FUNC_DECL C843_SAI(const int iId, char* const szOldAxes, char* const szNewAxes);
BOOL C843_FUNC_DECL C843_qSAI(const int iId, char* axes, const int maxlen);
BOOL C843_FUNC_DECL C843_qSAI_ALL(const int iId, char* axes, const int maxlen);

BOOL C843_FUNC_DECL C843_SVO(const int iId, char* const szAxes, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_qSVO(const int iId, char* const szAxes, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_SMO(const int iId, char* const szAxes, int* pnValarray);
BOOL C843_FUNC_DECL C843_qSMO(const int iId, char* const szAxes, int* pnValarray);

BOOL C843_FUNC_DECL C843_VEL(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_qVEL(const int iId, char* const szAxes, double* pdValarray);

BOOL C843_FUNC_DECL C843_SPA(const int iId, char* const szAxes, int* iCmdarray, double* dValarray, char* szStageNames);
BOOL C843_FUNC_DECL C843_qSPA(const int iId, char* const szAxes, int* iCmdarray, double* dValarray, char* szStageNames, int iMaxNameSize);

BOOL C843_FUNC_DECL C843_GetInputChannelNames(const int iId, char* szBuffer, const int maxlen);
BOOL C843_FUNC_DECL C843_GetOutputChannelNames(const int iId, char* szBuffer, const int maxlen);
BOOL C843_FUNC_DECL C843_DIO(const int iId, char* const szChannels, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_qDIO(const int iId, char* const szChannels, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_qTIO(const int iId, int* pINr, int* pONr);

BOOL C843_FUNC_DECL C843_STE(const int iId, char const  cAxis, double dOffset);
BOOL C843_FUNC_DECL C843_qSTE(const int iId, const char cAxis, const int iOffset, const int nrValues, double* pdValarray);

BOOL C843_FUNC_DECL C843_BRA(const int iId, char* const szAxes, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_qBRA(const int iId, char* szBuffer, const int maxlen);

BOOL C843_FUNC_DECL C843_qHLP(const int ID, char* buffer, const int maxlen);

/////////////////////////////////////////////////////////////////////////////
// String commands
BOOL C843_FUNC_DECL C843_C843Commandset(const int iId, char* const szCommand, char* szAwnser, int iMaxSize);
BOOL C843_FUNC_DECL C843_GcsCommandset(const int iIC843_GCS_DLLd, char* const szCommand);
BOOL C843_FUNC_DECL C843_GcsGetAnswer(const int ID, char* szAnswer, const int bufsize);
BOOL C843_FUNC_DECL C843_GcsGetAnswerSize(const int ID, int* iAnswerSize);



/////////////////////////////////////////////////////////////////////////////
// QMC commands.
BOOL C843_FUNC_DECL C843_SetQMC(const int iId, BYTE bCmd, BYTE bAxis, int Param);
BOOL C843_FUNC_DECL C843_GetQMC(const int iId, BYTE bCmd, BYTE bAxis, int* pResult);
BOOL C843_FUNC_DECL C843_SetQMCA(const int iId, BYTE bCmd, BYTE bAxis, WORD Param1, int lParam2);
BOOL C843_FUNC_DECL C843_GetQMCA(const int iId, BYTE bCmd, BYTE bAxis, WORD lParam, int* pResult);



/////////////////////////////////////////////////////////////////////////////
// limits
BOOL C843_FUNC_DECL C843_MNL(const int iId,  char* const szAxes);
BOOL C843_FUNC_DECL C843_MPL(const int iId,  char* const szAxes);
BOOL C843_FUNC_DECL C843_REF(const int iId, char* const szAxes);
BOOL C843_FUNC_DECL C843_qREF(const int iId, char* const szAxes, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_qLIM(const int iId, char* const szAxes, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_IsReferencing(const int iId, char* const szAxes, BOOL* pbIsReferencing);
BOOL C843_FUNC_DECL C843_GetRefResult(const int iId, char* const szAxes, int* pnResult);
BOOL C843_FUNC_DECL C843_IsReferenceOK(const int iId, char* const szAxes, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_qTMN(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_qTMX(const int iId, char* const szAxes, double* pdValarray);
BOOL C843_FUNC_DECL C843_RON(const int iId, char* const szAxes, BOOL* pbValarray);
BOOL C843_FUNC_DECL C843_qRON(const int iId, char* const szAxes, BOOL* pbValarray);


/////////////////////////////////////////////////////////////////////////////
// Spezial
BOOL	C843_FUNC_DECL	C843_AddStage(const int iId, char* const szAxes);
BOOL	C843_FUNC_DECL	C843_RemoveStage(const int iId, char* szStageName);
BOOL	C843_FUNC_DECL C843_OpenUserStagesEditDialog(const int iId);
BOOL	C843_FUNC_DECL C843_OpenPiStagesEditDialog(const int iId);
""".replace("BOOL", "bool").replace("C843_FUNC_DECL", "")

#dll = ffi.dlopen("C843_GCS_DLL.lib")

dll = WinDLL('C843_GCS_DLL')

def Connect(board_num=1):
    dll.C843_Connect.restype = int
    bid = dll.C843_Connect(c_int(board_num))
    print bid
    return bid

def isConnected(bid):
    if dll.C843_IsConnected(bid) == 1:
        return True
    else:
        return False
def CloseConnection(bid):
    dll.C843_CloseConnection.restype = None
    dll.C843_CloseConnection(c_int(bid))

def OpenPiStagesEditDialog(bid):
    print dll.C843_OpenPiStagesEditDialog(c_int(bid))

def qCST(bid, szAxes):
    "C843_qCST(const int iId, char* const szAxes, char* names, const int maxlen);"
    ax = create_string_buffer(szAxes)
    out = create_string_buffer("", 5000)

    dll.C843_qCST.restype = bool
    print dll.C843_qCST(bid, pointer(ax), pointer(out), 4999)
    print out.value
    print ax.value
    return out

def CST(bid, szAxes, names):
    "C843_qCST(const int iId, char* const szAxes, char* names, const int maxlen);"
    ax = create_string_buffer(szAxes)
    in_names = create_string_buffer(names)
    dll.C843_CST.restype = bool
    print dll.C843_CST(bid, pointer(ax), pointer(in_names))


def INI(bid, szAxes=""):
    ax = create_string_buffer(szAxes)
    dll.C843_INI.restype = bool
    print dll.C843_INI(bid, pointer(ax))

def MNL(bid, szAxes=""):
    ax = create_string_buffer(szAxes)
    dll.C843_MNL.restype = bool
    print dll.C843_MNL(bid, pointer(ax))

def MPL(bid, szAxes=""):
    ax = create_string_buffer(szAxes)
    dll.C843_MPL.restype = bool
    print dll.C843_MPL(bid, pointer(ax))

def REF(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_REF.restype = bool
    print dll.C843_REF(bid, pointer(ax))

def RON(bid, vals, szAxes="1"):
    ax = create_string_buffer(szAxes)
    in_vals = (c_bool*max(len(szAxes), 1))(*vals)
    return dll.C843_RON(bid, pointer(ax), pointer(in_vals))

def qRON(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_IsReferencing.restype = bool
    out = (c_bool*max(len(szAxes), 1))()
    dll.C843_IsReferencing(bid, pointer(ax), pointer(out))
    print out[0]
    return out

def IsReferencing(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_IsReferencing.restype = bool
    out = (c_bool*max(len(szAxes), 1))()
    dll.C843_IsReferencing(bid, pointer(ax), pointer(out))
    return out

def GetRefRes(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_GetRefResult.restype = bool
    out = c_int()
    dll.C843_GetRefResult(bid, pointer(ax), pointer(out))
    return out


def POS(bid, pos, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_POS.restype = bool
    pin = (c_double*len(pos))(*pos)
    print "pos", dll.C843_POS(bid, pointer(ax), pointer(pin))


def qPOS(bid, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_qPOS.restype = bool
    out = (c_double*max(len(szAxes), 1))()
    dll.C843_qPOS(bid, pointer(ax), pointer(out))
    return out

def qVEL(bid, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_qVEL.restype = bool
    out = (c_double*max(len(szAxes), 1))()
    dll.C843_qVEL(bid, pointer(ax), pointer(out))
    return out

def VEL(bid, pos, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_VEL.restype = bool
    pin = (c_double*len(pos))(*pos)
    print dll.C843_VEL(bid, pointer(ax), pointer(pin))


def MOV(bid, pos, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_MOV.restype = bool
    pin = (c_double*len(pos))(*pos)
    print 'mov', dll.C843_MOV(bid, pointer(ax), pointer(pin))

def MVR(bid, pos, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_MVR.restype = bool
    pin = (c_double*len(pos))(*pos)
    print "MVR", dll.C843_MVR(bid, pointer(ax), pointer(pin))

def DFH(bid, szAxes="1"):
    "Define current position as home for szAxes."
    ax = create_string_buffer(szAxes)
    dll.C843_DFH.restype = bool
    print "Define home", dll.C843_DFH(bid, szAxes)

def IsMoving(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_IsMoving.restype = bool
    out = (c_bool*max(len(szAxes), 1))()
    dll.C843_IsMoving(bid, pointer(ax), pointer(out))
    return out

try:
    bid
except NameError:
    bid = Connect()
    CST(bid, "1", "M-525.22")
    INI(bid)
#    MPL(bid)
#    while IsReferencing(bid)[0]:
#        time.sleep(0.1)
#        print "Doing ref"
#    print qPOS(bid)[0]
#    print DFH(bid)
#    print qPOS(bid)[0]
#    print GetRefRes(bid)
#    MOV(bid, [150.])wl_arrays

def mm_to_fs(pos_in_mm):
    speed_of_light = 299792458.
    pos_in_meters = pos_in_mm / 1000.
    pos_sec = pos_in_meters / speed_of_light
    return pos_sec * 1e15

def fs_to_mm(t_fs):
    speed_of_light = 299792458.
    pos_m = speed_of_light * t_fs * 1e-15
    return pos_m * 1000.


class DelayLine(object):
    def __init__(self):
        fhandle = open("last_pos", "r")
        last_pos = float(fhandle.read())
        fhandle.close()
        print "last_pos", last_pos
    ##        POS(bid, [last_pos])
        print RON(bid, [False])
        print 'ron', qRON(bid)[0]
        print 'pos', POS(bid, [0.])
        print 'qpos', qPOS(bid)[0]
        DFH(bid)

        self._cache = [bid, dll, qPOS]

    def get_fs(self):
        pos_mm = qPOS(bid)[0]
        t_fs = mm_to_fs(pos_mm)*2
        return t_fs

    def move_fs(self, fs):
        mm = fs_to_mm(fs) / 2.
        trys = 0
        while abs(self.get_fs() - fs) > 10. and trys < 5:
            MOV(bid, [mm])
            while IsMoving(bid)[0]:
                print self.get_fs()
                time.sleep(0.05)
            trys += 1

        self.save_pos()
        print "fin:",  self.get_fs()
    def save_pos(self):
        pos = qPOS(bid)[0]
        fhandle = open("last_pos", "w")
        fhandle.write(str(pos))
        fhandle.close()

dl = DelayLine()

#dl.move_fs(-30000)
##print isConnected(bid)
#qCST(bid, "")

#o = qCST(bid, "")

##REF(bid)
#import time
#ron = qRON(bid)
#if not ron[0]:
#    MNL(bid)
#    while IsReferencing(bid)[0]:
#        time.sleep(0.2)
#print GetRefRes(bid).value
#ron = qRON(bid)
#print "ron", ron[0]
#print qPOS(bid)[0]
#o = MOV(bid, [150.0])
##CloseConnection(bid)

#OpenPiStagesEditDialog(bid)

