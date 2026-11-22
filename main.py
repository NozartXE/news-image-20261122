"""Grader entry point (stdlib only).

Copies the committed entry.png into MAKEFUN_OUTPUT_DIR.  The picture
is drawn ahead of time by build.py; the grader image has no font or
imaging stack, so nothing is rendered here.
"""

import os
import shutil


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "output")
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    shutil.copyfile(src, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
