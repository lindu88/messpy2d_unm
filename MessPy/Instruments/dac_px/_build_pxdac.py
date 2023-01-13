# _build_foo.py
from nicelib import build_lib

header_info = {
    'win*': {
        'path': (
            r"C:\Program Files (x86)\Signatec\PXDAC4800\Include",
            
        ),
        'header': 'pxdac4800_wrap.h'
    },
}

lib_names = {'win*': 'PXDAC4800_64'}


def build():
    build_lib(header_info, lib_names, '_pxdaclib', __file__, ignored_headers=['vcruntime.h', 'stdio.h'] )


if __name__ == "__main__":
    build()