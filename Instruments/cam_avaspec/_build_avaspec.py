# _build_foo.py
from nicelib import build_lib

header_info = {
    'win*': {
        'path': (
            r"C:\AvaSpecX64-DLL_9.10.0.0\examples\Qtdemos\Qt5_demo_full",
        ),
        'header': 'avaspec.h'
    },
}

lib_names = {
    'win*': r'C:\AvaSpecX64-DLL_9.10.0.0\examples\Qtdemos\Qt5_demo_full\avaspecx64.dll'}
preamble = """
#define __linux
typedef signed char     int8;
typedef unsigned char   uint8;
typedef signed short    int16;
typedef unsigned short  uint16;
typedef unsigned int    uint32;
typedef signed int      int32;
"""


def build():
    build_lib(header_info, lib_names, '_avaspeclib', __file__,
              ignored_headers=['vcruntime.h',
                               'stdio.h', 'corecrt.h', 'stddef.h'],
              preamble=preamble, cffi_kwargs=dict(packed=True))


if __name__ == "__main__":
    build()
