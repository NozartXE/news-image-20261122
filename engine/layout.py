"""Page geometry.  The gate asserts these numbers sum to the canvas;
the page module draws by them.  One source of truth for both.
"""

PAGE_W = 1024
PAGE_H = 1024
MARGIN = 10
GUTTER = 8

# (name, height) top to bottom — must sum to PAGE_H (gate-checked)
BANDS = [
    ("kicker", 24),
    ("masthead", 90),
    ("strip", 48),
    ("heroes", 300),
    ("map", 68),
    ("cards", 296),
    ("index", 100),
    ("datecheck", 78),
    ("footer", 20),
]


def band_y(name):
    y = 0
    for n, h in BANDS:
        if n == name:
            return y
        y += h
    raise KeyError(name)


def band_h(name):
    return dict(BANDS)[name]


# heroes
HERO_BIG_W = 660
HERO_SMALL_W = 336
HERO_SCENE_H = 120

# cards
CARD_COLS = 5
CARD_ROWS = 2
CARD_W = (PAGE_W - 2 * MARGIN - (CARD_COLS - 1) * GUTTER) / CARD_COLS
CARD_H = (band_h("cards") - (CARD_ROWS - 1) * GUTTER) / CARD_ROWS
CARD_SCENE_H = 52

# index
INDEX_COLS = 3
INDEX_ROWS = 2
INDEX_TITLE_H = 24
INDEX_COL_W = (PAGE_W - 2 * MARGIN - (INDEX_COLS - 1) * GUTTER) / INDEX_COLS
INDEX_ROW_H = (band_h("index") - INDEX_TITLE_H) / INDEX_ROWS

# strip
STRIP_LABEL_W = 84

# date check
DATECHECK_TITLE_H = 15

REGION_ORDER = ["Europe", "Asia-Pacific", "Middle East", "North America"]

# typographic scale shared by gate (measurement) and page (drawing)
TYPE = {
    "kicker": ("sans", 11, True),
    "day": ("sans", 15, True),
    "date": ("serif", 56, True),
    "scope": ("sans", 13, True),
    "scope_sub": ("sans", 10, False),
    "strip_title": ("sans", 10, True),
    "strip_cap": ("sans", 9, True),
    "hero_kicker": ("sans", 12, True),
    "hero_kicker_s": ("sans", 11, True),
    "hero_big_head": ("sans", 32, True),
    "hero_big_dek": ("sans", 16, True),
    "hero_body": ("sans", 13, False),
    "chip": ("sans", 10, True),
    "hero_small_head": ("sans", 25, True),
    "hero_small_dek": ("sans", 13, True),
    "hero_small_body": ("sans", 12, False),
    "card_kicker": ("sans", 10, True),
    "card_head": ("sans", 15, True),
    "card_body": ("sans", 11, False),
    "index_title": ("sans", 13, True),
    "index_brief": ("sans", 12, False),
    "index_brief_b": ("sans", 12, True),
    "map_cap": ("sans", 9, True),
    "pin_num": ("sans", 11, True),
    "badge_num": ("sans", 9, True),
    "dc_title": ("sans", 11, True),
    "dc_body": ("sans", 10, False),
    "footer": ("sans", 9, False),
}

LEAD = {
    "hero_big_head": 36,
    "hero_body": 16,
    "hero_small_head": 29,
    "hero_small_dek": 16,
    "hero_small_body": 15,
    "card_head": 17,
    "card_body": 13,
    "index_brief": 15,
    "dc_body": 12,
}

HERO_BIG_TEXT_W = HERO_BIG_W - 28
HERO_SMALL_TEXT_W = HERO_SMALL_W - 24
CARD_TEXT_W = CARD_W - 16
INDEX_TEXT_W = INDEX_COL_W - 16
FULL_TEXT_W = PAGE_W - 2 * MARGIN
