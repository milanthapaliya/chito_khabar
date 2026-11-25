# छिटो खबर — daily rashifal

Images and captions for the छिटो खबर Facebook page's daily rashifal post.
Every day a scheduled task writes new readings in our own words, renders the
image here and schedules a 6:00 AM (Nepal time) photo post through Windsor.ai.

This repo is **public** so Facebook can fetch each day's image from its
raw.githubusercontent.com link. Keep nothing private in it.

## Layout

- `rashifal/content/YYYY-MM-DD.json` — the day's 12 readings (`{"signs": {...}}`)
- `rashifal/images/YYYY-MM-DD.png` — the rendered 1080×1350 image
- `rashifal/captions/YYYY-MM-DD.txt` — the post caption
- `rashifal/render.py` — draws the image (same design as the canvas template)
- `rashifal/daily.py` — `info` gives the day's Nepali date and paths; `build` validates, renders and writes the caption

## Run by hand

```
cd rashifal
npm install
pip install nepali-datetime playwright
python3 daily.py info                 # today in Nepal time
python3 daily.py build content/2026-11-26.json
```

## Rules for the readings

- Write all 12 in fresh Nepali words. Never copy from a website or another page.
- One or two short sentences each, at most 90 characters, positive and general.
- No health, money or legal claims that someone might act on in a harmful way.
- Don't repeat the previous days' lines: read the last few files in `content/` first.

# Daily gold & silver rate

- `gold/rates.json` — every day's official rate (NPR per tola), used for the change, month low/high and the 7-day chart
- `gold/gold.py` — `info`, `add DAY GOLD SILVER`, `build DAY` (image + caption)
- `gold/images/`, `gold/captions/` — the day's card and caption

Rates come only from the Federation of Nepal Gold & Silver Dealers' Association (FENEGOSIDA),
as reported by at least two Nepali news portals that agree. No rate is published on Saturdays.
Fonts come from `rashifal/node_modules` (run `npm install` in `rashifal/`).
