# news-image-20261122

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/NozartXE/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/NozartXE/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

One image that sums up the world news of Sunday 22 November 2026: a
date-as-masthead front page whose dominant hero is the wait at COP31
in Antalya — the final text is out, objections were due at 03:00 GMT
and the approval vote is set for 06:00 GMT, so the hero draws the
clock and the waiting delegates rather than a deal that has not
happened. A second hero covers Hong Kong's Election Committee polls
(856 candidates, 723 seats, 5,757 voters). Ten more stories are drawn
scene-cards, a dotted world map pins all twelve illustrated stories,
and six further Sunday briefs carry a source tag each: 18 stories,
4 regions, 12 illustrated. A figure strip prints the day's eight key
numbers, each appearing exactly once more on the page, inside its own
story. A DATE CHECK panel lists the widely shared items that turned
out to be 17–21 November news, each with its real date — nothing
misdated is illustrated. Every story was verified against its source
before it entered the content file; the verification note travels
with each story in `content/content-20261122.json`.

The picture is drawn by a deterministic engine (`engine/`, Pillow): a
validated content file goes in, a byte-identical 1024×1024 PNG comes
out. The validator refuses to draw a page whose accounting breaks —
story counts, scene counts, region counts, a figure repeated outside
its one allowed place, a brief without a source tag, or a line that
overflows its box.

## Run it

```sh
python3 build.py                # validates, draws entry.png + entry-480.png
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`main.py` is stdlib-only: it copies the committed `entry.png` to
`MAKEFUN_OUTPUT_DIR`, which is all the grader needs.
