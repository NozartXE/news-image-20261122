"""The validator.  Runs before any drawing; the build refuses to
render a page whose accounting breaks:

- band geometry sums to exactly 1024 (and the hero/card/index grids
  close exactly across the width);
- printed story counts equal the content file's declared counts;
- region counts are computed from the story list and sum to the total;
- every figure-strip token is printed exactly twice on the whole
  page: once in the strip, once inside its anchor story — and never
  in the DATE CHECK;
- every index brief carries a per-item source tag and fits its cell
  in at most two lines, with depth measured by ROW index;
- every DATE CHECK item carries a full date and a source tag, and no
  DATE CHECK fact leaks into the day's stories;
- every text block fits its box at the real fonts.
"""

import re

from PIL import Image, ImageDraw

from . import layout as L
from . import words

_draw = ImageDraw.Draw(Image.new("RGB", (8, 8)))


class GateError(Exception):
    pass


def fnt(name):
    fam, size, bold = L.TYPE[name]
    return words.font(fam, size, bold)


def compute_stats(content):
    heroes = content["heroes"]
    cards = content["cards"]
    index = content["index"]
    regions = {}
    for story in heroes + cards + index:
        regions[story["region"]] = regions.get(story["region"], 0) + 1
    return {
        "heroes": len(heroes),
        "cards": len(cards),
        "index": len(index),
        "total": len(heroes) + len(cards) + len(index),
        "illustrated": len(heroes) + len(cards),
        "regions": regions,
        "region_count": len(regions),
    }


def scope_line(stats):
    return (f"{stats['total']} STORIES · {stats['region_count']} REGIONS · "
            f"{stats['illustrated']} ILLUSTRATED")


def chip_texts(stats):
    return [f"{name.upper()} {stats['regions'][name]}"
            for name in L.REGION_ORDER if name in stats["regions"]]


def brief_text(item):
    return f"{item['place']} — {item['fact']} ({item['source']})"


def story_strings(story):
    out = []
    for key in ("kicker", "headline", "dek", "body"):
        if key in story:
            out.append(story[key])
    return out


def printed_strings(content, stats):
    """Every string the page will print, grouped by area."""
    groups = {
        "masthead": [content["kicker"], content["day_line"],
                     content["date_line"], scope_line(stats),
                     "EVERY ITEM SOURCED · EVERY STORY DATED TODAY"],
        "strip": [content["strip_title"]]
                 + [f["display"] for f in content["strip"]]
                 + [f["caption"] for f in content["strip"]],
        "chips": chip_texts(stats),
        "index": [content["index_title"]]
                 + [brief_text(i) for i in content["index"]],
        "map": ["THE ILLUSTRATED STORIES, MAPPED"],
        "datecheck": [content["datecheck_title"]] + list(content["datecheck"]),
        "footer": [content["footer"]],
    }
    for hero in content["heroes"]:
        groups[f"story:{hero['id']}"] = story_strings(hero)
    for card in content["cards"]:
        groups[f"story:{card['id']}"] = story_strings(card)
    return groups


def _wrap_lines(text, type_name, max_width):
    return words.wrap(_draw, text, fnt(type_name), max_width)


def _check_fit(errors, label, text, type_name, max_width, max_lines):
    lines = _wrap_lines(text, type_name, max_width)
    if len(lines) > max_lines:
        errors.append(f"{label}: {len(lines)} lines > {max_lines} allowed "
                      f"at {type_name}: {text[:60]!r}")
    return lines


def validate(content):
    errors = []
    stats = compute_stats(content)

    # ---- geometry -------------------------------------------------
    total_h = sum(h for _, h in L.BANDS)
    if total_h != L.PAGE_H:
        errors.append(f"geometry: bands sum to {total_h}, not {L.PAGE_H}")
    if L.MARGIN + L.HERO_BIG_W + L.GUTTER + L.HERO_SMALL_W + L.MARGIN != L.PAGE_W:
        errors.append("geometry: hero row does not close across the width")
    card_span = 2 * L.MARGIN + L.CARD_COLS * L.CARD_W + (L.CARD_COLS - 1) * L.GUTTER
    if abs(card_span - L.PAGE_W) > 0.01:
        errors.append(f"geometry: card grid spans {card_span}, not {L.PAGE_W}")
    idx_span = 2 * L.MARGIN + L.INDEX_COLS * L.INDEX_COL_W + (L.INDEX_COLS - 1) * L.GUTTER
    if abs(idx_span - L.PAGE_W) > 0.01:
        errors.append(f"geometry: index grid spans {idx_span}, not {L.PAGE_W}")

    # ---- declared counts ------------------------------------------
    exp = content["expected"]
    for key in ("heroes", "cards", "index", "total", "illustrated"):
        if exp[key] != stats[key]:
            errors.append(f"counts: declared {key}={exp[key]} but data has "
                          f"{stats[key]}")
    if exp["regions"] != stats["region_count"]:
        errors.append(f"counts: declared regions={exp['regions']} but data "
                      f"has {stats['region_count']}")
    if sum(stats["regions"].values()) != stats["total"]:
        errors.append("regions: region counts do not sum to the story total")
    for story in content["heroes"] + content["cards"] + content["index"]:
        if story["region"] not in L.REGION_ORDER:
            errors.append(f"regions: story {story['id']} has unknown region "
                          f"{story['region']!r}")
        if not story.get("verify"):
            errors.append(f"verify: story {story['id']} has no verification note")

    groups = printed_strings(content, stats)
    all_text = "\n".join(s for g in groups.values() for s in g).lower()

    # ---- figure strip ----------------------------------------------
    stories_by_id = {s["id"]: s for s in content["heroes"] + content["cards"]}
    for fig in content["strip"]:
        token = fig["token"].lower()
        if token not in fig["display"].lower():
            errors.append(f"strip: display {fig['display']!r} does not show "
                          f"token {fig['token']!r}")
        occurrences = all_text.count(token)
        if occurrences != 2:
            errors.append(f"strip: token {fig['token']!r} printed "
                          f"{occurrences} times, must be exactly 2 "
                          f"(strip + anchor)")
        anchor = stories_by_id.get(fig["anchor"])
        if anchor is None:
            errors.append(f"strip: anchor story {fig['anchor']!r} not found")
        elif token not in "\n".join(story_strings(anchor)).lower():
            errors.append(f"strip: token {fig['token']!r} not anchored in "
                          f"story {fig['anchor']!r}")
        for item in content["datecheck"]:
            if token in item.lower():
                errors.append(f"strip: token {fig['token']!r} leaks into "
                              f"DATE CHECK item {item[:40]!r}")

    # ---- index ------------------------------------------------------
    brief_re = re.compile(r"^[A-Z ]+ — .+ \([A-Za-z ]+\)$")
    for i, item in enumerate(content["index"]):
        brief = brief_text(item)
        if not brief_re.match(brief):
            errors.append(f"index: brief lacks PLACE — fact (Source) form: "
                          f"{brief[:60]!r}")
        lines = words.wrap_rich(_draw, f"{item['place']} —", item["fact"]
                                + f" ({item['source']})",
                                fnt("index_brief_b"), fnt("index_brief"),
                                L.INDEX_TEXT_W)
        if len(lines) > 2:
            errors.append(f"index: brief {i} wraps to {len(lines)} lines "
                          f"(max 2): {brief[:60]!r}")
        row = i % L.INDEX_ROWS  # depth is a ROW property, never the column
        depth = len(lines) * L.LEAD["index_brief"]
        cell_top = L.INDEX_TITLE_H + row * L.INDEX_ROW_H
        if cell_top + depth > L.band_h("index"):
            errors.append(f"index: brief {i} overflows the band at row {row}")

    # ---- date check ---------------------------------------------------
    date_re = re.compile(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d{1,2} Nov")
    story_blob = "\n".join(s for g, ss in groups.items()
                           if g.startswith("story:") for s in ss).lower()
    for item in content["datecheck"]:
        if not date_re.search(item):
            errors.append(f"datecheck: no full date in {item[:50]!r}")
        if not re.search(r"\([A-Za-z ]+\)$", item):
            errors.append(f"datecheck: no source tag in {item[:50]!r}")
        fact = item.split(" — ")[0].lower()
        if fact in story_blob:
            errors.append(f"datecheck: excluded fact leaks into stories: "
                          f"{item[:50]!r}")
    dc_text = "   ·   ".join(content["datecheck"])
    dc_lines = _wrap_lines(dc_text, "dc_body", L.FULL_TEXT_W)
    if len(dc_lines) > 5:
        errors.append(f"datecheck: flows to {len(dc_lines)} lines (max 5)")

    # ---- heroes -------------------------------------------------------
    big, small = content["heroes"][0], content["heroes"][1]
    _check_fit(errors, "hero-big kicker", big["kicker"], "hero_kicker",
               L.HERO_BIG_TEXT_W, 1)
    _check_fit(errors, "hero-big headline", big["headline"], "hero_big_head",
               L.HERO_BIG_TEXT_W, 2)
    _check_fit(errors, "hero-big dek", big["dek"], "hero_big_dek",
               L.HERO_BIG_TEXT_W, 1)
    _check_fit(errors, "hero-big body", big["body"], "hero_body",
               L.HERO_BIG_TEXT_W, 2)
    chip_w = sum(words.width(_draw, t, fnt("chip")) + 14
                 for t in chip_texts(stats)) + 6 * (len(chip_texts(stats)) - 1)
    if chip_w > L.HERO_BIG_TEXT_W:
        errors.append(f"chips: region chips need {chip_w:.0f}px > "
                      f"{L.HERO_BIG_TEXT_W}px")
    _check_fit(errors, "hero-small kicker", small["kicker"], "hero_kicker_s",
               L.HERO_SMALL_TEXT_W, 1)
    _check_fit(errors, "hero-small headline", small["headline"],
               "hero_small_head", L.HERO_SMALL_TEXT_W, 2)
    _check_fit(errors, "hero-small dek", small["dek"], "hero_small_dek",
               L.HERO_SMALL_TEXT_W, 2)
    _check_fit(errors, "hero-small body", small["body"], "hero_small_body",
               L.HERO_SMALL_TEXT_W, 4)

    # ---- cards ---------------------------------------------------------
    for card in content["cards"]:
        _check_fit(errors, f"card {card['id']} kicker", card["kicker"],
                   "card_kicker", L.CARD_TEXT_W, 1)
        _check_fit(errors, f"card {card['id']} headline", card["headline"],
                   "card_head", L.CARD_TEXT_W, 2)
        _check_fit(errors, f"card {card['id']} body", card["body"],
                   "card_body", L.CARD_TEXT_W, 3)

    # ---- masthead / strip / footer -------------------------------------
    _check_fit(errors, "kicker", content["kicker"], "kicker",
               L.FULL_TEXT_W, 1)
    _check_fit(errors, "footer", content["footer"], "footer",
               L.FULL_TEXT_W, 1)
    _check_fit(errors, "scope line", scope_line(stats), "scope", 320, 1)
    if words.width(_draw, content["date_line"], fnt("date")) > 700:
        errors.append("masthead: date line too wide at 56pt serif")
    cell_w = (L.FULL_TEXT_W - L.STRIP_LABEL_W) / len(content["strip"])
    for fig in content["strip"]:
        size = words.fit_size(_draw, fig["display"], "heavy", True, 30,
                              cell_w - 8)
        if size < 17:
            errors.append(f"strip: figure {fig['display']!r} shrinks to "
                          f"{size}pt in its cell")
        if words.width(_draw, fig["caption"], fnt("strip_cap")) > cell_w - 4:
            errors.append(f"strip: caption {fig['caption']!r} too wide")

    # ---- map pins --------------------------------------------------------
    illustrated = content["heroes"] + content["cards"]
    if len(illustrated) != stats["illustrated"]:
        errors.append("map: pin list does not match illustrated count")
    for story in illustrated:
        if "pin" not in story:
            errors.append(f"map: story {story['id']} has no pin")

    if errors:
        raise GateError("GATE FAILED:\n- " + "\n- ".join(errors))
    return stats


def report_lines(content, stats):
    lines = [
        f"stories={stats['total']} heroes={stats['heroes']} "
        f"cards={stats['cards']} index={stats['index']}",
        f"illustrated={stats['illustrated']} regions={stats['region_count']} "
        + " ".join(f"{k}={v}" for k, v in stats["regions"].items()),
        f"scope line printed: {scope_line(stats)!r}",
        f"strip figures={len(content['strip'])} "
        f"datecheck items={len(content['datecheck'])}",
        "geometry: bands sum to 1024; hero/card/index grids close exactly",
    ]
    return lines
