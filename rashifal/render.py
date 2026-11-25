"""Render the छिटो खबर daily rashifal image (1080x1350 PNG).

Usage: python3 render.py content.json out.png
content.json: {"weekday": "बुधबार", "date": "मंसिर ९, २०८३",
               "signs": {"मेष": "...", ... all 12 ...}}
Needs: npm install @fontsource/mukta (in this folder), playwright + google-chrome.
"""
import html, json, pathlib, sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE / "node_modules/@fontsource/mukta/files"
ORDER = ["मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
         "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"]
RED = "#C8102E"


def font_faces():
    out = []
    for w in (500, 700, 800):
        for sub in ("devanagari", "latin"):
            f = FONTS / f"mukta-{sub}-{w}-normal.woff2"
            if f.exists():
                out.append(f"@font-face{{font-family:Mukta;font-weight:{w};"
                           f"src:url('{f.as_uri()}') format('woff2');}}")
    return "\n".join(out)


def build_html(c):
    cards = []
    for name in ORDER:
        text = html.escape(c["signs"][name])
        cards.append(
            f'<div class="card"><div class="n">{name}</div><div class="t">{text}</div></div>')
    return f"""<!doctype html><html lang="ne"><head><meta charset="utf-8"><style>
{font_faces()}
body{{margin:0}}
.root{{width:1080px;height:1350px;box-sizing:border-box;background:#F7F4EE;font-family:Mukta,sans-serif;color:#1C1C1C;display:flex;flex-direction:column}}
.card{{background:#fff;border:1px solid #E4DED3;border-radius:6px;padding:16px 20px}}
.n{{font-size:30px;font-weight:800;color:{RED};line-height:1.2}}
.t{{font-size:21px;font-weight:500;line-height:1.5;margin-top:4px}}
</style></head><body><div class="root">
<div style="height:12px;background:{RED}"></div><div style="height:4px;background:#003893"></div>
<div style="padding:40px 56px 0;display:flex;justify-content:space-between;align-items:flex-end">
<div><div style="font-size:26px;font-weight:800;color:{RED};line-height:1.2">छिटो खबर</div>
<div style="font-size:92px;font-weight:800;line-height:1.05;letter-spacing:-1px;margin-top:6px">आजको राशिफल</div></div>
<div style="text-align:right;padding-bottom:14px">
<div style="font-size:30px;font-weight:700;line-height:1.3">{html.escape(c['weekday'])}</div>
<div style="font-size:30px;font-weight:500;line-height:1.3;color:#555049">{html.escape(c['date'])}</div></div></div>
<div style="height:3px;background:#1C1C1C;margin:24px 56px 0"></div>
<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 14px;padding:24px 56px 0">
{''.join(cards)}</div>
<div style="margin-top:auto;background:{RED};color:#fff;padding:22px 56px;display:flex;justify-content:space-between;align-items:center">
<div style="font-size:30px;font-weight:800">छिटो खबर</div>
<div style="font-size:24px;font-weight:500">दिनहुँ राशिफलका लागि फलो गर्नुहोस्</div></div>
</div></body></html>"""


def main(src, out):
    c = json.loads(pathlib.Path(src).read_text(encoding="utf-8"))
    missing = [n for n in ORDER if not c.get("signs", {}).get(n)]
    if missing:
        sys.exit(f"missing signs: {missing}")
    page_file = HERE / "_page.html"
    page_file.write_text(build_html(c), encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(page_file.as_uri())
        pg.evaluate("document.fonts.ready")
        overflow = pg.evaluate("document.querySelector('.root').scrollHeight")
        pg.screenshot(path=out, clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
        b.close()
    if overflow > 1350:
        sys.exit(f"content overflows: {overflow}px > 1350px; shorten the texts")
    print("rendered", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
