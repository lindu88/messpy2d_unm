# _build_foo.py
from nicelib import build_lib
from nicelib.process import cdecl_hook, declspec_hook
from pathlib import Path

dir = Path()
header_info = {
    'win*': {
        'path': (
            r".",
            r"C:\Users\Public\PI\C-843\PI_Programming_Files_C843_GCS_DLL",
        ),
        'header': 'C843_GCS_DLL.h'
    },
}

lib_names = {'win*:64': r'C:\Users\Public\PI\C-843\PI_Programming_Files_C843_GCS_DLL', 'win*:32': 'C843_GCS_DLL'}

pre = """
#define WIN32
#define 
"""

#re = 'typedef unsiged int'

th = [cdecl_hook, declspec_hook]
def build():
    build_lib(header_info, lib_names, '_gcslib', __file__,
              preamble=pre, token_hooks=[declspec_hook])#, debug_file='bla.h')

build()