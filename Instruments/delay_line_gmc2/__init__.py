# -*- coding: utf-8 -*-
"""
Created on Tue Sep 03 14:24:02 2013

@author: tillsten
"""

#import cffi

#ffi = cffi.FFI()
#ffi.cdef(
from ctypes import *
old_csb = create_string_buffer
def create_string_buffer(s, size=None):
    if isinstance(s, str):
        s = s.encode()
    return old_csb(s, size)
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
import os, platform
os.environ['PATH'] = os.path.dirname(__file__) + ';' + os.environ['PATH']
if platform.architecture()[0] == '64bit':
    dll = WinDLL('C843_GCS_DLL_x64')
else:
    dll = WinDLL('C843_GCS_DLL')


def Connect(board_num=1):
    dll.C843_Connect.restype = int
    bid = dll.C843_Connect(c_int(board_num))
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
    return dll.C843_CST(bid, pointer(ax), pointer(in_names))


def INI(bid, szAxes=""):
    ax = create_string_buffer(szAxes)
    dll.C843_INI.restype = bool
    dll.C843_INI(bid, pointer(ax))

def MNL(bid, szAxes=""):
    ax = create_string_buffer(szAxes)
    dll.C843_MNL.restype = bool
    print dll.C843_MNL(bid, pointer(ax))

def MPL(bid, szAxes=""):
    ax = create_string_buffer(szAxes)
    dll.C843_MPL.restype = bool
    dll.C843_MPL(bid, pointer(ax))

def REF(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_REF.restype = bool
    dll.C843_REF(bid, pointer(ax))

def RON(bid, vals, szAxes="1"):
    ax = create_string_buffer(szAxes)
    in_vals = (c_bool*max(len(szAxes), 1))(*vals)
    return dll.C843_RON(bid, pointer(ax), pointer(in_vals))

def qRON(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_IsReferencing.restype = bool
    out = (c_bool*max(len(szAxes), 1))()
    dll.C843_IsReferencing(bid, pointer(ax), pointer(out))
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
    dll.C843_POS(bid, pointer(ax), pointer(pin))


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
    dll.C843_VEL(bid, pointer(ax), pointer(pin))


def MOV(bid, pos, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_MOV.restype = bool
    pin = (c_double*len(pos))(*pos)
    return dll.C843_MOV(bid, pointer(ax), pointer(pin))

def MVR(bid, pos, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_MVR.restype = bool
    pin = (c_double*len(pos))(*pos)
    dll.C843_MVR(bid, pointer(ax), pointer(pin))

def DFH(bid, szAxes="1"):
    "Define current position as home for szAxes."
    ax = create_string_buffer(szAxes)
    dll.C843_DFH.restype = bool
    dll.C843_DFH(bid, szAxes)

def GOH(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_GOH.restype = bool
    dll.C843_GOH(bid, szAxes)

def IsMoving(bid, szAxes="1"):
    ax = create_string_buffer(szAxes)
    dll.C843_IsMoving.restype = bool
    out = (c_bool*max(len(szAxes), 1))()
    dll.C843_IsMoving(bid, pointer(ax), pointer(out))
    return out

def qACC(bid, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_qVEL.restype = bool
    out = (c_double*max(len(szAxes), 1))()
    dll.C843_qACC(bid, pointer(ax), pointer(out))
    return out

def ACC(bid, pos, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_VEL.restype = bool
    pin = (c_double*len(pos))(*pos)
    dll.C843_ACC(bid, pointer(ax), pointer(pin))

def qDEC(bid, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_qVEL.restype = bool
    out = (c_double*max(len(szAxes), 1))()
    dll.C843_qDEC(bid, pointer(ax), pointer(out))
    return out

def DEC(bid, pos, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_VEL.restype = bool
    pin = (c_double*len(pos))(*pos)
    dll.C843_DEC(bid, pointer(ax), pointer(pin))


#BOOL C843_FUNC_DECL C843_SPA(const int iId, char* const szAxes, int* iCmdarray, double* dValarray, char* szStageNames);
def SPA(bid, para, val, szAxes="1"):
    "C843_qPOS(const int iId, char* const szAxes, double* pdValarray);"
    ax = create_string_buffer(szAxes)
    dll.C843_VEL.restype = bool
    pin0 = (c_int*len(pos))(*para)
    pin = (c_double*len(pos))(*val)
    dll.C843_DEC(bid, pointer(ax), pointer(pin))

import os.path as osp

print "Init Delayline..."
LAST_ZERO_FILE = osp.dirname(__file__) + r'\last_pos.json'
import json
try:
    bid
except NameError:
    bid = Connect()
    print bid
    if bid != 0:
        raise IOError('DL faied')

    #GOH(bid)

    print qPOS(bid)[0]
    print "vel", qVEL(bid)[0]
#    print qPOS(bid)[0]
    print GetRefRes(bid)
#    MOV(bid, [150.])

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
        print CST(bid, "1", "M-505.6PD")
        print INI(bid)
        print 'acc', qACC(bid)[0], 'de acc', qDEC(bid)[0], qRON(bid)[0]
        DEC(bid, [5.])
        ACC(bid, [100.])
        print 'acc', qACC(bid)[0], 'de acc', qDEC(bid)[0], qRON(bid)[0]
        try:
            paras = json.load(open(LAST_ZERO_FILE, 'r'))
            lastmove, pos = paras['lastmove'], paras['current_pos']
            self.zero = paras['zero_pos']
        except IOError:
            lastmove = None
            pos = 0
            self.zero = 75
        print('lm ', lastmove)
        if not lastmove:
            self.reference()
        else:
            RON(bid, [False])
            POS(bid, [pos])

    def reference(self):
        REF(bid)
        print "Doing ref..."
        while IsReferencing(bid)[0]:
            time.sleep(0.1)
        print "Ref finnished, moving to last zero."
        MOV(bid, [self.zero])

    def get_fs(self):
        pos_mm = qPOS(bid)[0]
        print(pos_mm)
        t_fs = mm_to_fs((pos_mm-self.zero)*2)
        return -t_fs

    def move_fs(self, fs):
        json.dump(dict(lastmove=False, current_pos=0,
                       zero_pos=self.zero), file(LAST_ZERO_FILE, 'w'))
        mm = - fs_to_mm(fs) / 2.
        trys = 0
#
#        while abs(self.get_fs() - fs) > 10. and trys < 10:
#            print(MOV(bid, [mm+self.zero]))
#            print(IsMoving(bid)[0])
#            while IsMoving(bid)[0]:
#                print(qPos(bid)[0])
#                time.sleep(0.05)
#            trys += 1

        print(MOV(bid, [mm+self.zero]))
        while IsMoving(bid)[0]:
             qPOS(bid)[0]
        print(qPOS(bid)[0]), [mm+self.zero], mm_to_fs(-(qPOS(bid)[0]) + mm+self.zero)*2
        self.save_pos()

    def save_pos(self):
        pos = qPOS(bid)[0]
        json.dump(dict(lastmove=True, current_pos=pos,
                       zero_pos=self.zero), file(LAST_ZERO_FILE, 'w'))


    def def_home(self):
        self.zero = qPOS(bid)[0]
        self.save_pos()

#

dl = DelayLine()

if __name__ == "__main__":
    #dl.move_fs(200000)
    dl.move_fs(-1000)
    dl.move_fs(0)
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

