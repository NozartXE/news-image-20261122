"""Compose the 1024x1024 front page from the validated content file.

Draw order follows the band stack in layout.BANDS.  Every string drawn
here is one the gate has already measured, using the same fonts.
Stories are numbered in reading order: heroes 1-2, cards 3-12, then
the briefs wall 13-36.
"""

from PIL import Image, ImageDraw

from . import art, colours as C, gate, layout as L, words


def _f(name):
    fam, size, bold = L.TYPE[name]
    return words.font(fam, size, bold)


def _text(draw, xy, text, type_name, fill=C.INK, anchor="la"):
    draw.text(xy, text, font=_f(type_name), fill=fill, anchor=anchor)


def _wrap(draw, text, type_name, max_width):
    return words.wrap(draw, text, _f(type_name), max_width)


def _rule(draw, x0, x1, y, fill=C.RULE, width=2):
    draw.line([x0, y, x1, y], fill=fill, width=width)


def _pin_badge(draw, cx, cy, number, disc_r, num_type):
    draw.ellipse([cx - disc_r - 2, cy - disc_r - 2, cx + disc_r + 2,
                  cy + disc_r + 2], fill=C.WHITE)
    draw.ellipse([cx - disc_r, cy - disc_r, cx + disc_r, cy + disc_r],
                 fill=C.RED)
    _text(draw, (cx, cy), str(number), num_type, fill=C.WHITE, anchor="mm")


def render(content, stats):
    img = Image.new("RGB", (L.PAGE_W, L.PAGE_H), C.PAPER)
    draw = ImageDraw.Draw(img)
    mx = L.MARGIN
    right = L.PAGE_W - L.MARGIN

    # ---------------------------------------------------------- kicker
    y = L.band_y("kicker")
    _text(draw, (mx, y + 4), content["kicker"], "kicker", fill=C.INK_SOFT)
    _rule(draw, mx, right, y + L.band_h("kicker") - 1, width=1)

    # -------------------------------------------------------- masthead
    y = L.band_y("masthead")
    _text(draw, (mx, y + 2), content["day_line"], "day", fill=C.RED)
    _text(draw, (mx, y + 22), content["date_line"], "date", fill=C.INK)
    scope = gate.scope_line(stats)
    _text(draw, (right, y + 26), scope, "scope", fill=C.INK, anchor="ra")
    _text(draw, (right, y + 48), "EVERY ITEM SOURCED · EVERY STORY DATED TODAY",
          "scope_sub", fill=C.FAINT, anchor="ra")
    _text(draw, (mx, y + 74), gate.tally_line(stats), "tally",
          fill=C.TEAL_DARK)
    _rule(draw, mx, right, y + L.band_h("masthead") - 1, width=3)

    # ----------------------------------------------------------- strip
    y = L.band_y("strip")
    label_w = L.STRIP_LABEL_W
    _text(draw, (mx + 2, y + 7), "THE DAY", "strip_title", fill=C.RED)
    _text(draw, (mx + 2, y + 21), "IN FIGURES", "strip_title", fill=C.RED)
    cell_w = (L.FULL_TEXT_W - label_w) / len(content["strip"])
    for i, fig in enumerate(content["strip"]):
        cx = mx + label_w + cell_w * (i + 0.5)
        x0 = mx + label_w + cell_w * i
        if i:
            draw.line([x0, y + 6, x0, y + L.band_h("strip") - 6],
                      fill=(196, 188, 170), width=1)
        size = words.fit_size(draw, fig["display"], "heavy", True, 30,
                              cell_w - 8)
        draw.text((cx, y + 2), fig["display"],
                  font=words.font("heavy", size, True), fill=C.INK,
                  anchor="ma")
        _text(draw, (cx, y + 31), fig["caption"], "strip_cap",
              fill=C.INK_SOFT, anchor="ma")
    _rule(draw, mx, right, y + L.band_h("strip") - 1, width=1)

    # ---------------------------------------------------------- heroes
    y = L.band_y("heroes")
    big, small = content["heroes"]
    _hero(draw, big, mx, y, L.HERO_BIG_W, pin_no=1, big_hero=True)
    _hero(draw, small, mx + L.HERO_BIG_W + L.GUTTER, y, L.HERO_SMALL_W,
          pin_no=2, big_hero=False)
    _rule(draw, mx, right, y + L.band_h("heroes") - 1, width=2)

    # ----------------------------------------------------------- cards
    y = L.band_y("cards")
    for i, card in enumerate(content["cards"]):
        col, row = i % L.CARD_COLS, i // L.CARD_COLS
        cx = mx + col * (L.CARD_W + L.GUTTER)
        cy = y + row * (L.CARD_H + L.GUTTER)
        _card(draw, card, cx, cy, pin_no=i + 3)
    _rule(draw, mx, right, y + L.band_h("cards") - 1, width=2)

    # ----------------------------------------------------- briefs wall
    y = L.band_y("index")
    _text(draw, (mx, y + 2), content["index_title"], "index_title", fill=C.INK)
    _rule(draw, mx, right, y + L.INDEX_TITLE_H - 3, fill=(196, 188, 170),
          width=1)
    for i, item in enumerate(content["index"]):
        col, row = i % L.INDEX_COLS, i // L.INDEX_COLS  # row-major: the
        # numbers read left to right, top to bottom
        cx = mx + col * (L.INDEX_COL_W + L.GUTTER)
        cy = y + L.INDEX_TITLE_H + row * L.INDEX_ROW_H
        lead = f"{gate.brief_number(content, i)}. {item['place']} —"
        lines = words.wrap_rich(draw, lead,
                                item["fact"] + f" ({item['source']})",
                                _f("index_brief_b"), _f("index_brief"),
                                L.INDEX_TEXT_W)
        for line in lines:  # the gate guarantees exactly one
            lx = cx
            for text, bold in line:
                f = _f("index_brief_b") if bold else _f("index_brief")
                draw.text((lx, cy + 1), text, font=f, fill=C.INK)
                lx += words.width(draw, text, f) + words.width(
                    draw, " ", _f("index_brief"))
    _rule(draw, mx, right, y + L.band_h("index") - 1, width=1)

    # ------------------------------------------------------- datecheck
    y = L.band_y("datecheck")
    _text(draw, (mx, y + 1), content["datecheck_title"], "dc_title",
          fill=C.RED)
    body = "   ·   ".join(content["datecheck"])
    ly = y + L.DATECHECK_TITLE_H + 2
    for line in _wrap(draw, body, "dc_body", L.FULL_TEXT_W):
        _text(draw, (mx, ly), line, "dc_body", fill=C.INK_SOFT)
        ly += L.LEAD["dc_body"]
    _rule(draw, mx, right, y + L.band_h("datecheck") - 1, width=1)

    # ---------------------------------------------------------- footer
    y = L.band_y("footer")
    fw = words.width(draw, content["footer"], _f("footer"))
    _text(draw, ((L.PAGE_W - fw) / 2, y + 5), content["footer"], "footer",
          fill=C.FAINT)

    return img


def _hero(draw, hero, x, y, w, pin_no, big_hero):
    scene_rect = (x, y, w, L.HERO_SCENE_H)
    art.SCENES[hero["scene"]](draw, scene_rect)
    draw.rectangle([x, y, x + w - 1, y + L.HERO_SCENE_H - 1],
                   outline=C.INK, width=1)
    _pin_badge(draw, x + 16, y + 16, pin_no, 10, "badge_num")
    pad = 14 if big_hero else 12
    tx = x + pad
    tw = w - 2 * pad
    ty = y + L.HERO_SCENE_H + 6
    if big_hero:
        _text(draw, (tx, ty), hero["kicker"], "hero_kicker", fill=C.RED)
        ty += 19
        for line in _wrap(draw, hero["headline"], "hero_big_head", tw):
            _text(draw, (tx, ty), line, "hero_big_head", fill=C.INK)
            ty += L.LEAD["hero_big_head"]
        ty += 3
        _text(draw, (tx, ty), hero["dek"], "hero_big_dek", fill=C.TEAL_DARK)
        ty += 23
        for line in _wrap(draw, hero["body"], "hero_body", tw):
            _text(draw, (tx, ty), line, "hero_body", fill=C.INK_SOFT)
            ty += L.LEAD["hero_body"]
    else:
        _text(draw, (tx, ty), hero["kicker"], "hero_kicker_s", fill=C.RED)
        ty += 17
        for line in _wrap(draw, hero["headline"], "hero_small_head", tw):
            _text(draw, (tx, ty), line, "hero_small_head", fill=C.INK)
            ty += L.LEAD["hero_small_head"]
        ty += 3
        for line in _wrap(draw, hero["dek"], "hero_small_dek", tw):
            _text(draw, (tx, ty), line, "hero_small_dek", fill=C.TEAL_DARK)
            ty += L.LEAD["hero_small_dek"]
        ty += 3
        for line in _wrap(draw, hero["body"], "hero_small_body", tw):
            _text(draw, (tx, ty), line, "hero_small_body", fill=C.INK_SOFT)
            ty += L.LEAD["hero_small_body"]


def _card(draw, card, x, y, pin_no):
    scene_rect = (x, y, L.CARD_W, L.CARD_SCENE_H)
    art.SCENES[card["scene"]](draw, scene_rect)
    draw.rectangle([x, y, x + L.CARD_W - 1, y + L.CARD_H - 1],
                   outline=(196, 188, 170), width=1)
    _pin_badge(draw, x + 13, y + 13, pin_no, 9, "badge_num")
    tx = x + 8
    tw = L.CARD_W - 16
    ty = y + L.CARD_SCENE_H + 4
    _text(draw, (tx, ty), card["kicker"], "card_kicker", fill=C.RED)
    ty += 14
    for line in _wrap(draw, card["headline"], "card_head", tw):
        _text(draw, (tx, ty), line, "card_head", fill=C.INK)
        ty += L.LEAD["card_head"]
    ty += 2
    for line in _wrap(draw, card["body"], "card_body", tw):
        _text(draw, (tx, ty), line, "card_body", fill=C.INK_SOFT)
        ty += L.LEAD["card_body"]
