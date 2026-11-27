"""Daily NEPSE update post for छिटो खबर (English poster).

  python3 nepse.py info [YYYY-MM-DD]
      Nepal date info and paths. NEPSE trades Sunday to Thursday.
  python3 nepse.py build YYYY-MM-DD
      Validates data/YYYY-MM-DD.json, renders images/YYYY-MM-DD.png
      and writes captions/YYYY-MM-DD.txt.

data/YYYY-MM-DD.json: see data/2026-11-26.json for the shape (index close/change/pct,
turnover in rupees, shares, transactions, 5 gainers, 5 losers, 13 sector indices).
Needs: pip install nepali-datetime playwright; fonts from ../rashifal (npm install there).
"""
import datetime, json, pathlib, sys

import nepali_datetime as nd
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE.parent / "rashifal/node_modules/@fontsource/inter/files"
NPT = datetime.timezone(datetime.timedelta(hours=5, minutes=45))
BS_MONTHS = ["Baisakh", "Jestha", "Asar", "Shrawan", "Bhadra", "Asoj", "Kartik",
             "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"]
NE_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
NE_WEEKDAYS = ["सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार", "आइतबार"]
NE_MONTHS = ["बैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज", "कात्तिक",
             "मंसिर", "पुस", "माघ", "फागुन", "चैत"]
RED, BLUE, INK = "#C8102E", "#003893", "#16181D"
UP, DOWN, FLAT = "#147A3D", "#C21E2F", "#5B5F66"


def info(day=None):
    g = datetime.date.fromisoformat(day) if day else datetime.datetime.now(NPT).date()
    b = nd.date.from_datetime_date(g)
    return {
        "gregorian": g.isoformat(),
        "trading_day": g.weekday() in (6, 0, 1, 2, 3),  # Sun-Thu
        "date_en": g.strftime("%a, %d %b %Y").replace(" 0", " "),
        "date_bs": f"{BS_MONTHS[b.month-1]} {b.day}, {b.year}",
        "date_ne": f"{NE_WEEKDAYS[g.weekday()]}, {NE_MONTHS[b.month-1]} {str(b.day).translate(NE_DIGITS)}, {str(b.year).translate(NE_DIGITS)}",
        "data_file": f"data/{g.isoformat()}.json",
        "image_file": f"images/{g.isoformat()}.png",
        "caption_file": f"captions/{g.isoformat()}.txt",
    }


def validate(d):
    errs = []
    ix = d.get("index", {})
    for k in ("close", "change", "pct"):
        if not isinstance(ix.get(k), (int, float)): errs.append(f"index.{k}")
    if isinstance(ix.get("close"), (int, float)) and isinstance(ix.get("change"), (int, float)) and isinstance(ix.get("pct"), (int, float)):
        prev = ix["close"] - ix["change"]
        if prev and abs(ix["change"] / prev * 100 - ix["pct"]) > 0.02:
            errs.append("index pct does not match change/close")
    for k in ("turnover", "shares", "transactions"):
        if not isinstance(d.get(k), (int, float)): errs.append(k)
    if len(d.get("gainers", [])) != 5: errs.append("need 5 gainers")
    if len(d.get("losers", [])) != 5: errs.append("need 5 losers")
    if any(x["pct"] <= 0 for x in d.get("gainers", [])): errs.append("gainer with pct <= 0")
    if any(x["pct"] >= 0 for x in d.get("losers", [])): errs.append("loser with pct >= 0")
    if len(d.get("sectors", [])) < 10: errs.append("need the sector indices")
    if errs: sys.exit("data problems: " + "; ".join(errs))


def col(v): return UP if v > 0 else (DOWN if v < 0 else FLAT)
def sign(v, nd_=2): return ("+" if v > 0 else ("−" if v < 0 else "")) + f"{abs(v):,.{nd_}f}"
def arrow(v): return "▲" if v > 0 else ("▼" if v < 0 else "■")


def faces():
    return "\n".join(
        f"@font-face{{font-family:Inter;font-weight:{w};src:url('{(FONTS / f'inter-latin-{w}-normal.woff2').as_uri()}') format('woff2');}}"
        for w in (500, 600, 700, 800))


def mover_rows(items):
    return "".join(
        f'<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-top:1px solid #ECE7DE">'
        f'<span style="font-weight:700;font-size:27px">{x["symbol"]}</span>'
        f'<span style="display:flex;gap:18px;align-items:baseline"><span style="font-size:22px;color:#5B5F66;font-weight:500">Rs {x["ltp"]:,.2f}</span>'
        f'<span style="font-size:25px;font-weight:700;color:{col(x["pct"])};min-width:92px;text-align:right">{sign(x["pct"])}%</span></span></div>'
        for x in items)


def page(d, i):
    ix = d["index"]
    c = col(ix["change"])
    chip_bg = "#E6F3EA" if ix["change"] > 0 else ("#FBE8EA" if ix["change"] < 0 else "#EEECE7")
    SHORT = {"Development Bank": "Dev. Bank", "Non-Life Insurance": "Non-Life Ins.", "Hotels & Tourism": "Hotels & Tourism"}
    sectors = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:9px 14px;background:#fff;border:1px solid #ECE7DE;border-radius:6px">'
        f'<span style="font-size:21px;font-weight:600">{SHORT.get(s["name"], s["name"])}</span>'
        f'<span style="font-size:21px;font-weight:700;color:{col(s["pct"])}">{sign(s["pct"])}%</span></div>'
        for s in sorted(d["sectors"], key=lambda s: -s["pct"]))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
{faces()}
body{{margin:0}} *{{box-sizing:border-box}}
#root{{width:1080px;height:1350px;background:#F7F4EE;font-family:Inter,sans-serif;color:{INK};display:flex;flex-direction:column;font-feature-settings:"tnum" 1}}
.card{{background:#fff;border:1px solid #E4DED3;border-radius:10px}}
.lbl{{font-size:20px;font-weight:700;letter-spacing:1.5px;color:#5B5F66;text-transform:uppercase}}
</style></head><body><div id="root">
<div style="height:12px;background:{RED}"></div><div style="height:4px;background:{BLUE}"></div>
<div style="padding:36px 56px 0;display:flex;justify-content:space-between;align-items:flex-end">
<div><div style="font-size:22px;font-weight:800;color:{RED};letter-spacing:3px">CHITO KHABAR</div>
<div style="font-size:66px;font-weight:800;letter-spacing:-1.5px;line-height:1.08;margin-top:6px">NEPSE Daily Update</div></div>
<div style="text-align:right;padding-bottom:6px"><div style="font-size:24px;font-weight:700">{i['date_en']}</div>
<div style="font-size:22px;font-weight:500;color:#5B5F66;margin-top:2px">{i['date_bs']}</div></div></div>
<div style="height:3px;background:{INK};margin:22px 56px 0"></div>
<div style="padding:24px 56px 0;display:flex;flex-direction:column;gap:16px">
<div class="card" style="padding:26px 34px;display:flex;justify-content:space-between;align-items:center">
<div><div class="lbl">NEPSE Index · Close</div>
<div style="font-size:104px;font-weight:800;letter-spacing:-3px;line-height:1.05;margin-top:6px">{ix['close']:,.2f}</div></div>
<div style="background:{chip_bg};color:{c};border-radius:8px;padding:16px 22px;text-align:right">
<div style="font-size:40px;font-weight:800;line-height:1.1">{arrow(ix['change'])} {abs(ix['change']):,.2f}</div>
<div style="font-size:30px;font-weight:700;margin-top:4px">{sign(ix['pct'])}%</div></div></div>
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px">
<div class="card" style="padding:18px 22px"><div class="lbl" style="font-size:17px">Turnover</div><div style="font-size:36px;font-weight:800;margin-top:6px">Rs {d['turnover']/1e9:,.2f} bn</div></div>
<div class="card" style="padding:18px 22px"><div class="lbl" style="font-size:17px">Shares traded</div><div style="font-size:36px;font-weight:800;margin-top:6px">{d['shares']/1e6:,.2f} mn</div></div>
<div class="card" style="padding:18px 22px"><div class="lbl" style="font-size:17px">Transactions</div><div style="font-size:36px;font-weight:800;margin-top:6px">{d['transactions']:,}</div></div></div>
<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px">
<div class="card" style="padding:18px 24px 6px"><div class="lbl" style="color:{UP};margin-bottom:6px">▲ Top Gainers</div>{mover_rows(d['gainers'])}</div>
<div class="card" style="padding:18px 24px 6px"><div class="lbl" style="color:{DOWN};margin-bottom:6px">▼ Top Losers</div>{mover_rows(d['losers'])}</div></div>
<div><div class="lbl" style="margin-bottom:10px">Sector Indices · % Change</div>
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px">{sectors}</div></div>
</div>
<div style="margin-top:auto;background:{RED};color:#fff;padding:20px 56px;display:flex;justify-content:space-between;align-items:center">
<div style="font-size:26px;font-weight:800;letter-spacing:2px">CHITO KHABAR</div>
<div style="font-size:19px;font-weight:500">Data: NEPSE via ShareSansar · Not investment advice</div></div>
</div></body></html>"""


def caption(d, i):
    ix = d["index"]
    move = "बढ्यो" if ix["change"] > 0 else ("घट्यो" if ix["change"] < 0 else "स्थिर रह्यो")
    head = (f"📈 NEPSE {abs(ix['change']):,.2f} अंकले बढ्यो" if ix["change"] > 0 else
            f"📉 NEPSE {abs(ix['change']):,.2f} अंकले घट्यो" if ix["change"] < 0 else "NEPSE स्थिर")
    best = max(d["sectors"], key=lambda s: s["pct"]); worst = min(d["sectors"], key=lambda s: s["pct"])
    g = d["gainers"][0]; l = d["losers"][0]
    lines = [head, "", f"🗓️ {i['date_ne']}", "",
             f"📊 NEPSE Index: {ix['close']:,.2f} ({sign(ix['change'])} | {sign(ix['pct'])}%)",
             f"💰 Turnover: रु {d['turnover']/1e7:,.2f} करोड",
             f"🔁 Shares traded: {d['shares']:,} | Transactions: {d['transactions']:,}", "",
             f"🟢 Top gainer: {g['symbol']} ({sign(g['pct'])}%)",
             f"🔴 Top loser: {l['symbol']} ({sign(l['pct'])}%)",
             f"🏆 Best sector: {best['name']} ({sign(best['pct'])}%)",
             f"⚠️ Weakest sector: {worst['name']} ({sign(worst['pct'])}%)", "",
             "👇 आज तपाईंको पोर्टफोलियो कस्तो रह्यो? कमेन्टमा भन्नुहोस्।", "",
             "📌 दिनहुँ सेयर बजारको अपडेटका लागि छिटो खबर लाई फलो गर्नुहोस्।",
             "ℹ️ यो जानकारी मात्र हो, लगानी सल्लाह होइन।", "",
             "#NEPSE #sharemarket #nepal #DailyUpdate"]
    return "\n".join(lines)


def build(day):
    i = info(day)
    d = json.loads((HERE / i["data_file"]).read_text(encoding="utf-8"))
    validate(d)
    (HERE / "images").mkdir(exist_ok=True); (HERE / "captions").mkdir(exist_ok=True)
    pf = HERE / "_page.html"; pf.write_text(page(d, i), encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(pf.as_uri()); pg.evaluate("document.fonts.ready")
        h = pg.evaluate("document.getElementById('root').scrollHeight")
        pg.screenshot(path=str(HERE / i["image_file"]), clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
        b.close()
    pf.unlink(missing_ok=True)
    if h > 1350: sys.exit(f"poster overflows ({h}px)")
    (HERE / i["caption_file"]).write_text(caption(d, i), encoding="utf-8")
    print(json.dumps(i, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "info": print(json.dumps(info(a[1] if len(a) > 1 else None), indent=1, ensure_ascii=False))
    elif len(a) == 2 and a[0] == "build": build(a[1])
    else: sys.exit(__doc__)
