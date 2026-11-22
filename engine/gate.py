"""The validator.  Runs before any drawing; the build refuses to
render a page whose accounting breaks:

- band geometry sums to exactly 1024 (and the hero/card/brief grids
  close exactly across the width);
- printed story counts equal the content file's declared counts;
- region counts are computed from the story list and sum to the total;
  the masthead tally line is built from that same computation, so an
  independent recount from the frame reproduces it;
- no place is counted twice across heroes, cards and briefs;
- sport stories are flagged in the data and capped;
- every illustrated story carries a map pin (lon/lat) inside the
  locator map's projection range, so the map can place all 12
  numbered pins it promises in its caption;
- every brief is a NUMBERED one-liner in PLACE — fact (Source) form,
  measured at the real font, with depth checked by ROW index;
- every DATE CHECK item carries a full date and a source tag, and no
  DATE CHECK fact leaks into the day's stories;
- every text block fits its box at the real fonts, including the
  full vertical stack of each hero and card.
"""

import re

from PIL import Image, ImageDraw

from . import layout as L
from . import words

_draw = ImageDraw.Draw(Image.new("RGB", (8, 8)))

SPORT_CAP = 8


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
    sport = 0
    for story in heroes + cards + index:
        regions[story["region"]] = regions.get(story["region"], 0) + 1
        if story.get("sport"):
            sport += 1
    return {
        "heroes": len(heroes),
        "cards": len(cards),
        "index": len(index),
        "total": len(heroes) + len(cards) + len(index),
        "illustrated": len(heroes) + len(cards),
        "regions": regions,
        "region_count": len(regions),
        "sport": sport,
    }


def scope_line(stats):
    return (f"{stats['total']} STORIES · {stats['region_count']} REGIONS · "
            f"{stats['illustrated']} ILLUSTRATED")


def tally_line(stats):
    parts = [f"{name.upper()} {stats['regions'][name]}"
             for name in L.REGION_ORDER if name in stats["regions"]]
    return "STORIES BY REGION — " + " · ".join(parts)


def brief_text(item):
    return f"{item['place']} — {item['fact']} ({item['source']})"


def brief_number(content, i):
    """Briefs are numbered after the illustrated stories."""
    return len(content["heroes"]) + len(content["cards"]) + i + 1


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
                     "EVERY ITEM SOURCED · EVERY STORY DATED TODAY",
                     tally_line(stats)],
        "map": [content["map_title"], content["map_caption"]],
        "index": [content["index_title"]]
                 + [f"{brief_number(content, i)}. {brief_text(item)}"
                    for i, item in enumerate(content["index"])],
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
        errors.append(f"geometry: brief grid spans {idx_span}, not {L.PAGE_W}")
    if len(content["index"]) != L.INDEX_COLS * L.INDEX_ROWS:
        errors.append(f"geometry: {len(content['index'])} briefs do not fill "
                      f"the {L.INDEX_COLS}x{L.INDEX_ROWS} brief wall")

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
    if stats["sport"] > SPORT_CAP:
        errors.append(f"sport: {stats['sport']} sport stories over the "
                      f"cap of {SPORT_CAP}")
    for story in content["heroes"] + content["cards"] + content["index"]:
        if story["region"] not in L.REGION_ORDER:
            errors.append(f"regions: story {story.get('id', story['place'])} "
                          f"has unknown region {story['region']!r}")
        if not story.get("verify"):
            errors.append(f"verify: story {story.get('id', story['place'])} "
                          f"has no verification note")

    # ---- no place counted twice ------------------------------------
    places = {}
    for story in content["heroes"] + content["cards"]:
        places.setdefault(story["place"].upper(), []).append(story["id"])
    for item in content["index"]:
        places.setdefault(item["place"].upper(), []).append(item["place"])
    for place, owners in places.items():
        if len(owners) > 1:
            errors.append(f"duplicates: place {place} counted "
                          f"{len(owners)} times ({', '.join(owners)})")

    groups = printed_strings(content, stats)
    all_text = "\n".join(s for g in groups.values() for s in g).lower()

    # ---- locator map pins -------------------------------------------
    for story in content["heroes"] + content["cards"]:
        pin = story.get("pin")
        if (not isinstance(pin, list) or len(pin) != 2
                or not all(isinstance(v, (int, float)) for v in pin)):
            errors.append(f"map: story {story['id']} has no [lon, lat] pin")
            continue
        lon, lat = pin
        if not -180.0 <= lon <= 180.0 or not -56.0 <= lat <= 84.0:
            errors.append(f"map: story {story['id']} pin ({lon}, {lat}) "
                          f"outside the projection range")

    # ---- briefs wall --------------------------------------------------
    brief_re = re.compile(r"^[A-Z ]+ — .+ \([A-Za-z ]+\)$")
    for i, item in enumerate(content["index"]):
        brief = brief_text(item)
        if not brief_re.match(brief):
            errors.append(f"index: brief lacks PLACE — fact (Source) form: "
                          f"{brief[:60]!r}")
        lead = f"{brief_number(content, i)}. {item['place']} —"
        lines = words.wrap_rich(_draw, lead,
                                item["fact"] + f" ({item['source']})",
                                fnt("index_brief_b"), fnt("index_brief"),
                                L.INDEX_TEXT_W)
        if len(lines) != 1:
            errors.append(f"index: brief {i} wraps to {len(lines)} lines "
                          f"(numbered wall is one line each): {brief[:60]!r}")
        row = i // L.INDEX_COLS  # depth is a ROW property, never the column
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
    dc_max = (L.band_h("datecheck") - L.DATECHECK_TITLE_H - 2) // L.LEAD["dc_body"]
    if len(dc_lines) > dc_max:
        errors.append(f"datecheck: flows to {len(dc_lines)} lines "
                      f"(max {dc_max})")

    # ---- heroes -------------------------------------------------------
    big, small = content["heroes"][0], content["heroes"][1]
    _check_fit(errors, "hero-big kicker", big["kicker"], "hero_kicker",
               L.HERO_BIG_TEXT_W, 1)
    bh = _check_fit(errors, "hero-big headline", big["headline"],
                    "hero_big_head", L.HERO_BIG_TEXT_W, 2)
    _check_fit(errors, "hero-big dek", big["dek"], "hero_big_dek",
               L.HERO_BIG_TEXT_W, 1)
    bb = _check_fit(errors, "hero-big body", big["body"], "hero_body",
                    L.HERO_BIG_TEXT_W, 2)
    big_stack = (L.HERO_SCENE_H + 6 + 19 + len(bh) * L.LEAD["hero_big_head"]
                 + 3 + 23 + len(bb) * L.LEAD["hero_body"])
    if big_stack > L.band_h("heroes"):
        errors.append(f"hero-big: stack is {big_stack}px > band "
                      f"{L.band_h('heroes')}px")
    _check_fit(errors, "hero-small kicker", small["kicker"], "hero_kicker_s",
               L.HERO_SMALL_TEXT_W, 1)
    sh = _check_fit(errors, "hero-small headline", small["headline"],
                    "hero_small_head", L.HERO_SMALL_TEXT_W, 2)
    sd = _check_fit(errors, "hero-small dek", small["dek"], "hero_small_dek",
                    L.HERO_SMALL_TEXT_W, 2)
    sb = _check_fit(errors, "hero-small body", small["body"],
                    "hero_small_body", L.HERO_SMALL_TEXT_W, 3)
    small_stack = (L.HERO_SCENE_H + 6 + 17 + len(sh) * L.LEAD["hero_small_head"]
                   + 3 + len(sd) * L.LEAD["hero_small_dek"] + 3
                   + len(sb) * L.LEAD["hero_small_body"])
    if small_stack > L.band_h("heroes"):
        errors.append(f"hero-small: stack is {small_stack}px > band "
                      f"{L.band_h('heroes')}px")

    # ---- cards ---------------------------------------------------------
    for card in content["cards"]:
        _check_fit(errors, f"card {card['id']} kicker", card["kicker"],
                   "card_kicker", L.CARD_TEXT_W, 1)
        ch = _check_fit(errors, f"card {card['id']} headline",
                        card["headline"], "card_head", L.CARD_TEXT_W, 2)
        cb = _check_fit(errors, f"card {card['id']} body", card["body"],
                        "card_body", L.CARD_TEXT_W, 3)
        stack = (L.CARD_SCENE_H + 4 + 14 + len(ch) * L.LEAD["card_head"]
                 + 2 + len(cb) * L.LEAD["card_body"])
        if stack > L.CARD_H:
            errors.append(f"card {card['id']}: stack is {stack}px > card "
                          f"{L.CARD_H:.0f}px")

    # ---- masthead / map / footer ---------------------------------------
    _check_fit(errors, "kicker", content["kicker"], "kicker",
               L.FULL_TEXT_W, 1)
    _check_fit(errors, "footer", content["footer"], "footer",
               L.FULL_TEXT_W, 1)
    _check_fit(errors, "scope line", scope_line(stats), "scope", 320, 1)
    _check_fit(errors, "tally line", tally_line(stats), "tally",
               L.FULL_TEXT_W, 1)
    if words.width(_draw, content["date_line"], fnt("date")) > 700:
        errors.append("masthead: date line too wide at 56pt serif")
    _check_fit(errors, "map title", content["map_title"], "map_title",
               190, 1)
    _check_fit(errors, "map caption", content["map_caption"], "map_cap",
               220, 1)

    if errors:
        raise GateError("GATE FAILED:\n- " + "\n- ".join(errors))
    return stats


def report_lines(content, stats):
    lines = [
        f"stories={stats['total']} heroes={stats['heroes']} "
        f"cards={stats['cards']} briefs={stats['index']}",
        f"illustrated={stats['illustrated']} regions={stats['region_count']} "
        + " ".join(f"{k}={v}" for k, v in stats["regions"].items()),
        f"sport={stats['sport']} (cap {SPORT_CAP})",
        f"scope line printed: {scope_line(stats)!r}",
        f"tally line printed: {tally_line(stats)!r}",
        f"map pins={stats['illustrated']} "
        f"datecheck items={len(content['datecheck'])}",
        "geometry: bands sum to 1024; hero/card/brief grids close exactly",
    ]
    return lines
