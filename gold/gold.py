"""Daily gold & silver rate post for छिटो खबर.

  python3 gold.py info [YYYY-MM-DD]
      Nepal date info, paths, and the previous recorded rate.
  python3 gold.py add YYYY-MM-DD GOLD_PER_TOLA SILVER_PER_TOLA
      Records the official rate in rates.json (overwrites that day).
  python3 gold.py build YYYY-MM-DD
      Renders images/YYYY-MM-DD.png and writes captions/YYYY-MM-DD.txt.

Per-10-gram prices are worked out from the tola price (1 tola = 11.6638 g),
the way the Federation lists them: gold rounded down to the nearest 10,
silver to the nearest rupee.
Needs: pip install nepali-datetime playwright; fonts from ../rashifal (npm install there).
"""
import datetime, html, json, math, pathlib, sys

import nepali_datetime as nd
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE.parent / "rashifal/node_modules/@fontsource/mukta/files"
RATES = HERE / "rates.json"
NPT = datetime.timezone(datetime.timedelta(hours=5, minutes=45))
WEEKDAYS = ["सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार", "आइतबार"]
MONTHS = ["बैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज", "कात्तिक",
          "मंसिर", "पुस", "माघ", "फागुन", "चैत"]
DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
TOLA_G = 11.6638
RED, BLUE, INK, GOLD = "#C8102E", "#003893", "#1C1C1C", "#B8860B"


def ne(n):
    """Nepali-format number with Devanagari digits: 241400 -> २,४१,४००"""
    s = str(int(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        s = ",".join(parts + [tail])
    return s.translate(DIGITS)


def per10(gold, silver):
    g = math.floor(gold / TOLA_G * 10 / 10) * 10 if gold else None
    s = round(silver / TOLA_G * 10) if silver else None
    return g, s


def load():
    return json.loads(RATES.read_text(encoding="utf-8"))


def bs(g):
    return nd.date.from_datetime_date(g)


def info(day=None):
    g = datetime.date.fromisoformat(day) if day else datetime.datetime.now(NPT).date()
    b = bs(g)
    rates = load()["rates"]
    prev = sorted(d for d in rates if d < g.isoformat())
    return {
        "gregorian": g.isoformat(),
        "weekday": WEEKDAYS[g.weekday()],
        "date": f"{MONTHS[b.month-1]} {str(b.day).translate(DIGITS)}, {str(b.year).translate(DIGITS)}",
        "is_saturday": g.weekday() == 5,
        "already_recorded": g.isoformat() in rates,
        "previous_day": prev[-1] if prev else None,
        "previous_rate": rates[prev[-1]] if prev else None,
        "image_file": f"images/{g.isoformat()}.png",
        "caption_file": f"captions/{g.isoformat()}.txt",
    }


def add(day, gold, silver):
    data = load()
    data["rates"][day] = {"gold": int(gold), "silver": int(silver)}
    data["rates"] = dict(sorted(data["rates"].items()))
    RATES.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def stats(day):
    rates = load()["rates"]
    today = rates[day]
    prev = sorted(d for d in rates if d < day)
    p = rates[prev[-1]] if prev else None
    g = datetime.date.fromisoformat(day)
    b = bs(g)
    # days in the same Bikram Sambat month, up to today
    month = [d for d in rates if d <= day and (lambda x: (x.year, x.month))(bs(datetime.date.fromisoformat(d))) == (b.year, b.month)]
    mgold = [rates[d]["gold"] for d in month if rates[d]["gold"]]
    first = rates[min(month)]["gold"] if month else None
    last7 = sorted(d for d in rates if d <= day)[-7:]
    return {
        "today": today, "prev": p,
        "dg": today["gold"] - p["gold"] if p and p.get("gold") else None,
        "ds": today["silver"] - p["silver"] if p and p.get("silver") else None,
        "month_low": len(mgold) > 2 and today["gold"] == min(mgold),
        "month_high": len(mgold) > 2 and today["gold"] == max(mgold),
        "month_name": MONTHS[b.month - 1],
        "month_first": first, "month_first_day": min(month) if month else None,
        "trend": [(d, rates[d]["gold"]) for d in last7],
    }


def change_text(d, unit="रु"):
    if d is None: return ""
    if d > 0: return f"▲ {unit} {ne(d)} बढ्यो"
    if d < 0: return f"▼ {unit} {ne(-d)} घट्यो"
    return "हिजोकै भाउ"


def font_faces():
    out = []
    for w in (500, 700, 800):
        for sub in ("devanagari", "latin"):
            f = FONTS / f"mukta-{sub}-{w}-normal.woff2"
            if f.exists():
                out.append(f"@font-face{{font-family:Mukta;font-weight:{w};src:url('{f.as_uri()}') format('woff2');}}")
    return "\n".join(out)


def build_html(day, st, i):
    t = st["today"]
    g10, s10 = per10(t["gold"], t["silver"])
    up = st["dg"] is not None and st["dg"] > 0
    chip_bg = "#E7F4EC" if up else ("#FBE9EB" if st["dg"] else "#EEECE7")
    chip_fg = "#17663A" if up else ("#A50E25" if st["dg"] else "#555049")
    s_chip = change_text(st["ds"])
    lo = min(v for _, v in st["trend"]); hi = max(v for _, v in st["trend"])
    bars = []
    for d, v in st["trend"]:
        h = 40 + (0 if hi == lo else (v - lo) / (hi - lo) * 140)
        dd = bs(datetime.date.fromisoformat(d))
        label = f"{MONTHS[dd.month-1][:3]} {str(dd.day).translate(DIGITS)}" if False else f"{str(dd.day).translate(DIGITS)} गते"
        is_today = d == day
        bars.append(
            f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:8px">'
            f'<div style="font-size:19px;font-weight:700;color:{INK if is_today else "#6B665E"}">{ne(round(v/1000))}</div>'
            f'<div style="width:100%;height:{h:.0f}px;background:{GOLD if is_today else "#E2D3A8"};border-radius:4px 4px 0 0"></div>'
            f'<div style="font-size:19px;font-weight:{700 if is_today else 500};color:{INK if is_today else "#6B665E"}">{label}</div></div>')
    note = ""
    if st["month_low"]: note = f"{st['month_name']} महिनाकै सबैभन्दा कम भाउ"
    elif st["month_high"]: note = f"{st['month_name']} महिनाकै सबैभन्दा उच्च भाउ"
    note_html = (f'<div style="margin-top:18px;display:inline-block;background:{INK};color:#fff;font-size:24px;font-weight:700;padding:8px 16px;border-radius:4px">{note}</div>' if note else "")
    return f"""<!doctype html><html lang="ne"><head><meta charset="utf-8"><style>
{font_faces()}
body{{margin:0}}
</style></head><body>
<div style="width:1080px;height:1350px;box-sizing:border-box;background:#F7F4EE;font-family:Mukta,sans-serif;color:{INK};display:flex;flex-direction:column">
<div style="height:12px;background:{RED}"></div><div style="height:4px;background:{BLUE}"></div>
<div style="padding:40px 56px 0;display:flex;justify-content:space-between;align-items:flex-end">
<div><div style="font-size:26px;font-weight:800;color:{RED};line-height:1.2">छिटो खबर</div>
<div style="font-size:84px;font-weight:800;line-height:1.05;letter-spacing:-1px;margin-top:6px">आजको सुनचाँदी भाउ</div></div>
<div style="text-align:right;padding-bottom:12px"><div style="font-size:30px;font-weight:700;line-height:1.3">{i['weekday']}</div>
<div style="font-size:30px;font-weight:500;line-height:1.3;color:#555049">{i['date']}</div></div></div>
<div style="height:3px;background:{INK};margin:24px 56px 0"></div>
<div style="padding:34px 56px 0">
<div style="background:#fff;border:1px solid #E4DED3;border-radius:8px;padding:30px 36px">
<div style="display:flex;justify-content:space-between;align-items:center">
<div style="font-size:34px;font-weight:800">छापावाल सुन <span style="font-size:24px;font-weight:500;color:#6B665E">प्रतितोला</span></div>
<div style="font-size:26px;font-weight:700;background:{chip_bg};color:{chip_fg};padding:6px 14px;border-radius:4px">{change_text(st['dg'])}</div></div>
<div style="font-size:120px;font-weight:800;line-height:1.05;color:{RED};margin-top:4px">रु {ne(t['gold'])}</div>
<div style="font-size:28px;font-weight:500;color:#555049">प्रति १० ग्राम: रु {ne(g10)}</div>
{note_html}
</div>
<div style="background:#fff;border:1px solid #E4DED3;border-radius:8px;padding:24px 36px;margin-top:16px;display:flex;justify-content:space-between;align-items:center">
<div><div style="font-size:30px;font-weight:800">चाँदी <span style="font-size:22px;font-weight:500;color:#6B665E">प्रतितोला</span></div>
<div style="font-size:24px;font-weight:500;color:#555049">प्रति १० ग्राम: रु {ne(s10)}</div></div>
<div style="text-align:right"><div style="font-size:60px;font-weight:800;line-height:1.1">रु {ne(t['silver'])}</div>
<div style="font-size:22px;font-weight:700;color:#555049">{s_chip}</div></div></div>
<div style="margin-top:30px;font-size:26px;font-weight:700">पछिल्ला कारोबार दिनको सुनको भाउ <span style="font-weight:500;color:#6B665E">(हजार रुपैयाँ प्रतितोला)</span></div>
<div style="display:flex;gap:14px;height:250px;margin-top:14px;align-items:flex-end">{''.join(bars)}</div>
</div>
<div style="margin-top:auto;background:{RED};color:#fff;padding:22px 56px;display:flex;justify-content:space-between;align-items:center">
<div style="font-size:30px;font-weight:800">छिटो खबर</div>
<div style="font-size:22px;font-weight:500">स्रोत: नेपाल सुनचाँदी व्यवसायी महासंघ</div></div>
</div></body></html>"""


def caption(day, st, i):
    t = st["today"]; g10, s10 = per10(t["gold"], t["silver"])
    dg, ds = st["dg"], st["ds"]
    if dg is None: head = "आजको सुनचाँदीको भाउ 🟡"
    elif dg > 0: head = f"सुनको भाउ तोलामा रु {ne(dg)} ले बढ्यो 📈"
    elif dg < 0: head = f"सुनको भाउ तोलामा रु {ne(-dg)} ले घट्यो 📉"
    else: head = "सुनको भाउ आज स्थिर 🟡"
    def ch(d):
        if d is None: return ""
        return f" (हिजोभन्दा रु {ne(abs(d))} ले {'बढ्यो' if d > 0 else 'घट्यो'})" if d else " (हिजोकै भाउ)"
    lines = [head, "", f"{i['weekday']}, {i['date']}", "",
             "🟡 छापावाल सुन", f"रु {ne(t['gold'])} प्रतितोला{ch(dg)}", f"रु {ne(g10)} प्रति १० ग्राम", "",
             "⚪ चाँदी", f"रु {ne(t['silver'])} प्रतितोला{ch(ds)}", f"रु {ne(s10)} प्रति १० ग्राम", ""]
    if st["month_low"]:
        lines.append(f"📊 यो {st['month_name']} महिनाकै सबैभन्दा कम भाउ हो।")
    elif st["month_high"]:
        lines.append(f"📊 यो {st['month_name']} महिनाकै सबैभन्दा उच्च भाउ हो।")
    if st["month_first"] and st["month_first_day"] != day:
        diff = t["gold"] - st["month_first"]
        if diff:
            word = "सस्तो" if diff < 0 else "महँगो"
            lines.append(f"{st['month_name']} १ गतेको तुलनामा सुन तोलामा रु {ne(abs(diff))} ले {word} छ।")
    lines += ["", "👇 तपाईंलाई के लाग्छ, सुन अब बढ्छ कि घट्छ? कमेन्टमा भन्नुहोस्।", "",
              "📌 दिनहुँ सुनचाँदीको भाउ थाहा पाउन छिटो खबर लाई फलो गर्नुहोस्।", "",
              "स्रोत: नेपाल सुनचाँदी व्यवसायी महासंघ", "",
              "#सुनकोभाउ #सुनचाँदी #goldprice #GoldPriceToday #छिटोखबर"]
    return "\n".join(l for l in lines)


def build(day):
    i = info(day)
    st = stats(day)
    (HERE / "images").mkdir(exist_ok=True); (HERE / "captions").mkdir(exist_ok=True)
    page = HERE / "_page.html"
    page.write_text(build_html(day, st, i), encoding="utf-8")
    out = HERE / i["image_file"]
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(page.as_uri()); pg.evaluate("document.fonts.ready")
        h = pg.evaluate("document.body.firstElementChild.scrollHeight")
        pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
        b.close()
    if h > 1350: sys.exit(f"overflow {h}px")
    (HERE / i["caption_file"]).write_text(caption(day, st, i), encoding="utf-8")
    print(json.dumps({**i, "image": str(out)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "info": print(json.dumps(info(a[1] if len(a) > 1 else None), ensure_ascii=False, indent=1))
    elif len(a) == 4 and a[0] == "add": add(a[1], a[2], a[3]); print("recorded", a[1:])
    elif len(a) == 2 and a[0] == "build": build(a[1])
    else: sys.exit(__doc__)
