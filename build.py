"""Dev build: validate, render twice, demand byte-identical output.

    python3 build.py

Writes entry.png (1024x1024) and entry-480.png (legibility audit
downscale) next to this file.  Refuses to finish if the gate fails,
if the two renders differ, or if entry.png exceeds 1 MiB.
"""

import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import gate, page  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BYTES = 1024 * 1024  # 1 MiB


def _png_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main():
    with open(os.path.join(HERE, "content", "content-20261122.json"),
              encoding="utf-8") as fh:
        content = json.load(fh)

    stats = gate.validate(content)
    print("GATE PASS")
    for line in gate.report_lines(content, stats):
        print(" ", line)

    img1 = page.render(content, stats)
    img2 = page.render(content, stats)
    b1, b2 = _png_bytes(img1), _png_bytes(img2)
    h1, h2 = hashlib.sha256(b1).hexdigest(), hashlib.sha256(b2).hexdigest()
    if h1 != h2:
        print("DETERMINISM FAILED: two renders differ", file=sys.stderr)
        return 1
    if len(b1) > MAX_BYTES:
        print(f"SIZE FAILED: entry.png is {len(b1)} bytes > {MAX_BYTES}",
              file=sys.stderr)
        return 1

    with open(os.path.join(HERE, "entry.png"), "wb") as fh:
        fh.write(b1)
    img1.resize((480, 480)).save(os.path.join(HERE, "entry-480.png"))
    print(f"entry.png {len(b1)} bytes sha256={h1}")
    print("determinism: two renders byte-identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
