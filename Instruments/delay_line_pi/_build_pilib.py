# _build_foo.py
from nicelib import build_lib
from pathlib import Path
from nicelib.process import declspec_hook

header_info = {
    "win*": {
        "path": (
            str(Path(__file__).parent),
            #r"{PROGRAMFILES}\IVI Foundation\VISA\Win64\Include",
            #r"{PROGRAMFILES(X86)}\IVI Foundation\VISA\WinNT64\Include",
        ),
        "header": "PI_GCS2_DLL.h",
    }
}


lib_names = {"win*": r""}

pre = """
"""

ignore_header = ["inttypes.h"]


def build():
    import sys

    build_lib(
        header_info,
        lib_names,
        "_pilib",
        __file__,
        logbuf=sys.stdout,
        ignored_headers=ignore_header,
        token_hooks=[declspec_hook],
        preamble=pre,
    )



