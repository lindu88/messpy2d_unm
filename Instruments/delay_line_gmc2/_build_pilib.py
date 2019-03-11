# _build_foo.py
from nicelib import build_lib
from nicelib.process import cdecl_hook, declspec_hook

header_info = {
    'win*': {
        'path': (
            r".",
            r"{PROGRAMFILES}\Vendor\Product",
            r"{PROGRAMFILES(X86)}\Vendor\Product",
        ),
        'header': 'C843_GCS_DLL.h'
    },
}

lib_names = {'win*:64': 'C843_GCS_DLL_x64', 'win*:32': 'C843_GCS_DLL'}

pre = """
#define WIN32

"""

#re = 'typedef unsiged int'

th = [cdecl_hook, declspec_hook]
def build():
    build_lib(header_info, lib_names, '_gcslib', __file__,
              preamble=pre, token_hooks=[declspec_hook], debug_file='bla.h')

build()