"""Daily rashifal helper for छिटो खबर.

  python3 daily.py info [YYYY-MM-DD]
      Prints the Nepal-time date info for the post (defaults to today in Nepal):
      gregorian date, Bikram Sambat date, weekday, and the file paths to use.

  python3 daily.py build content/YYYY-MM-DD.json
      Validates the content file, fills in weekday/date, renders
      images/YYYY-MM-DD.png and writes captions/YYYY-MM-DD.txt.

content/YYYY-MM-DD.json only needs {"signs": {"मेष": "...", ... all 12}}.
Needs: pip install nepali-datetime playwright; npm install (in this folder).
"""
import datetime, json, pathlib, subprocess, sys

import nepali_datetime as nd

HERE = pathlib.Path(__file__).resolve().parent
NPT = datetime.timezone(datetime.timedelta(hours=5, minutes=45))
WEEKDAYS = ["सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार", "आइतबार"]
MONTHS = ["बैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज", "कात्तिक",
          "मंसिर", "पुस", "माघ", "फागुन", "चैत"]
ORDER = ["मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
         "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"]
EMOJI = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")


def info(day=None):
    g = datetime.date.fromisoformat(day) if day else datetime.datetime.now(NPT).date()
    b = nd.date.from_datetime_date(g)
    date_ne = f"{MONTHS[b.month - 1]} {str(b.day).translate(DIGITS)}, {str(b.year).translate(DIGITS)}"
    return {
        "gregorian": g.isoformat(),
        "bs": f"{b.year}-{b.month:02d}-{b.day:02d}",
        "weekday": WEEKDAYS[g.weekday()],
        "date": date_ne,
        "content_file": f"content/{g.isoformat()}.json",
        "image_file": f"images/{g.isoformat()}.png",
        "caption_file": f"captions/{g.isoformat()}.txt",
        "publish_at_utc": f"{g.isoformat()}T00:15:00Z",  # 06:00 Nepal time
    }


def caption(c):
    lines = [f"🔮 आजको राशिफल | {c['weekday']}, {c['date']}", "",
             "आज तपाईंको दिन कस्तो छ? आफ्नो राशि हेर्नुहोस् 👇", ""]
    for e, n in zip(EMOJI, ORDER):
        lines.append(f"{e} {n}: {c['signs'][n]}")
    lines += ["", "👇 तपाईंको राशि कुन हो? कमेन्टमा लेख्नुहोस्।", "",
              "📌 दिनहुँ राशिफलका लागि छिटो खबर लाई फलो गर्नुहोस्।", "",
              "#राशिफल #dailyhoroscope #छिटोखबर #नेपाल #reels #rashifal"]
    return "\n".join(lines)


def build(path):
    p = (HERE / path) if not pathlib.Path(path).is_absolute() else pathlib.Path(path)
    c = json.loads(p.read_text(encoding="utf-8"))
    missing = [n for n in ORDER if not str(c.get("signs", {}).get(n, "")).strip()]
    if missing:
        sys.exit(f"missing signs: {missing}")
    too_long = [n for n in ORDER if len(c["signs"][n]) > 90]
    if too_long:
        sys.exit(f"texts too long (max 90 characters): {too_long}")
    i = info(p.stem)
    c["weekday"], c["date"] = i["weekday"], i["date"]
    p.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "images").mkdir(exist_ok=True)
    (HERE / "captions").mkdir(exist_ok=True)
    subprocess.run([sys.executable, str(HERE / "render.py"), str(p),
                    str(HERE / i["image_file"])], check=True)
    (HERE / i["caption_file"]).write_text(caption(c), encoding="utf-8")
    print(json.dumps(i, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "info":
        print(json.dumps(info(sys.argv[2] if len(sys.argv) > 2 else None), ensure_ascii=False, indent=1))
    elif len(sys.argv) == 3 and sys.argv[1] == "build":
        build(sys.argv[2])
    else:
        sys.exit(__doc__)
