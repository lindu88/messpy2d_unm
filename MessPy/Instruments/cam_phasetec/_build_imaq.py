# _build_foo.py
from nicelib import build_lib

header_info = {
    'win*': {
        'path': (
            r"C:/Program Files (x86)/National Instruments/Shared/ExternalCompilerSupport/C/Include",
            
        ),
        'header': 'niimaq.h'
    },
}

lib_names = {'win*': 'imaq'}
preamble = """

#define __GNUC__ 

"""

def build():
    build_lib(header_info, lib_names, '_imaqlib', __file__, 
                ignored_headers=['vcruntime.h', 'stdio.h', 'corecrt.h', 'stddef.h'],
                preamble=preamble,  )


if __name__ == "__main__":
    build()