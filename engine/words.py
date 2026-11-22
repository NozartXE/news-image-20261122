"""Text measurement and wrapping helpers.

Everything the page prints is measured with the real fonts before it
is drawn; the gate uses the same functions, so a line that overflows
in the gate overflows on the page, and vice versa.
"""

import os

from PIL import ImageFont

_FONT_DIR = "/usr/share/fonts/truetype"
_PATHS = {
    # masthead serif
    ("serif", True): os.path.join(_FONT_DIR, "dejavu", "DejaVuSerif-Bold.ttf"),
    ("serif", False): os.path.join(_FONT_DIR, "dejavu", "DejaVuSerif.ttf"),
    # text sans (narrow, newspaper-like)
    ("sans", True): os.path.join(_FONT_DIR, "liberation", "LiberationSans-Bold.ttf"),
    ("sans", False): os.path.join(_FONT_DIR, "liberation", "LiberationSans-Regular.ttf"),
    # heavy display sans for the date and the figure strip
    ("heavy", True): os.path.join(_FONT_DIR, "dejavu", "DejaVuSans-Bold.ttf"),
    ("heavy", False): os.path.join(_FONT_DIR, "dejavu", "DejaVuSans.ttf"),
}

_cache = {}


def font(family, size, bold=False):
    key = (family, size, bold)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(_PATHS[(family, bold)], size)
    return _cache[key]


def width(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def wrap(draw, text, fnt, max_width):
    """Greedy word wrap; returns the list of lines (never drops words)."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if width(draw, trial, fnt) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_size(draw, text, family, bold, start_size, max_width, min_size=8):
    """Largest size <= start_size at which text fits on one line."""
    size = start_size
    while size > min_size:
        if width(draw, text, font(family, size, bold)) <= max_width:
            return size
        size -= 1
    return min_size


def wrap_rich(draw, bold_text, rest_text, fnt_bold, fnt, max_width):
    """Wrap a line that starts with a bold segment.

    Returns a list of lines; each line is a list of (text, is_bold)
    segments to draw left to right, words joined by single spaces.
    The bold segment only ever sits on the first line.
    """
    bold_w = width(draw, bold_text, fnt_bold) if bold_text else 0
    space_w = width(draw, " ", fnt)
    lines = []
    first = True
    current = []
    current_w = 0

    def flush():
        nonlocal first, current, current_w
        segs = ([(bold_text, True)] if (first and bold_text) else [])
        segs += current
        lines.append(segs)
        first = False
        current = []
        current_w = 0

    for word in rest_text.split():
        ww = width(draw, word, fnt)
        add = ww if not current else ww + space_w
        avail = max_width - (bold_w + space_w if (first and bold_text) else 0)
        if current and current_w + add > avail:
            flush()
            current = [(word, False)]
            current_w = ww
        else:
            current.append((word, False))
            current_w += add
    if current or (first and bold_text):
        flush()
    return lines
