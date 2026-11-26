"""Render the daily rashifal reel (1080x1920, silent MP4, ~31 s).

  python3 reel.py content/YYYY-MM-DD.json reels/YYYY-MM-DD.mp4

Uses the content file after `daily.py build` has filled in weekday/date.
The video is silent: the page owner adds music from Meta's library when posting.
Animation is drawn frame by frame in Chrome (Playwright) and encoded with ffmpeg.
"""
import html, json, pathlib, shutil, subprocess, sys, tempfile

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE / "node_modules/@fontsource/mukta/files"
ORDER = ["मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
         "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन"]
DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
FPS = 30
INTRO, PER, OUTRO = 2.5, 2.2, 2.5
RED, BLUE, INK = "#C8102E", "#003893", "#1C1C1C"


def faces():
    out = []
    for w in (500, 700, 800):
        for sub in ("devanagari", "latin"):
            f = FONTS / f"mukta-{sub}-{w}-normal.woff2"
            if f.exists():
                out.append(f"@font-face{{font-family:Mukta;font-weight:{w};src:url('{f.as_uri()}') format('woff2');}}")
    return "\n".join(out)


def page(c):
    signs = [{"name": n, "text": c["signs"][n], "num": f"{str(i+1).translate(DIGITS)} / १२"}
             for i, n in enumerate(ORDER)]
    seg = "".join('<div class="seg"><div class="fill"></div></div>' for _ in ORDER)
    return f"""<!doctype html><html lang="ne"><head><meta charset="utf-8"><style>
{faces()}
*{{box-sizing:border-box}} body{{margin:0;background:#F7F4EE}}
#root{{width:1080px;height:1920px;position:relative;overflow:hidden;background:#F7F4EE;font-family:Mukta,sans-serif;color:{INK}}}
.bars{{position:absolute;top:0;left:0;right:0}}
#prog{{position:absolute;top:250px;left:90px;right:90px;display:flex;gap:8px}}
.seg{{flex:1;height:8px;background:#E4DED3;border-radius:4px;overflow:hidden}} .fill{{height:100%;width:0;background:{RED}}}
.scene{{position:absolute;left:0;right:0;top:0;bottom:0;opacity:0}}
#card{{position:absolute;left:90px;right:90px;top:560px;background:#fff;border:2px solid #E4DED3;border-radius:16px;padding:70px 64px 80px}}
</style></head><body><div id="root">
<div class="bars"><div style="height:18px;background:{RED}"></div><div style="height:6px;background:{BLUE}"></div></div>
<div style="position:absolute;top:120px;left:90px;right:90px;display:flex;justify-content:space-between;align-items:baseline">
<div style="font-size:44px;font-weight:800;color:{RED}">छिटो खबर</div>
<div style="font-size:36px;font-weight:600;color:#555049">{html.escape(c['weekday'])}, {html.escape(c['date'])}</div></div>
<div id="prog">{seg}</div>
<div id="intro" class="scene"><div style="position:absolute;top:640px;left:90px;right:90px;text-align:center">
<div id="t1" style="font-size:150px;font-weight:800;line-height:1.1;letter-spacing:-2px">आजको<br>राशिफल</div>
<div id="t2" style="height:8px;width:160px;background:{RED};margin:48px auto 40px;border-radius:4px"></div>
<div id="t3" style="font-size:54px;font-weight:700">{html.escape(c['weekday'])}, {html.escape(c['date'])}</div>
<div id="t4" style="font-size:40px;font-weight:500;color:#555049;margin-top:28px">आफ्नो राशि आउँदासम्म हेर्नुहोस्</div></div></div>
<div id="sign" class="scene"><div id="card">
<div id="num" style="font-size:40px;font-weight:700;color:#8A847A"></div>
<div id="nm" style="font-size:190px;font-weight:800;color:{RED};line-height:1.1;margin-top:6px"></div>
<div style="height:6px;width:120px;background:{INK};margin:26px 0 40px;border-radius:3px"></div>
<div id="tx" style="font-size:60px;font-weight:600;line-height:1.5"></div></div></div>
<div id="outro" class="scene"><div style="position:absolute;top:700px;left:90px;right:90px;text-align:center">
<div style="font-size:120px;font-weight:800;color:{RED};line-height:1.1">छिटो खबर</div>
<div style="font-size:56px;font-weight:700;margin-top:40px;line-height:1.4">दिनहुँ राशिफलका लागि<br>फलो गर्नुहोस्</div>
<div style="font-size:42px;font-weight:500;color:#555049;margin-top:40px">तपाईंको राशि कुन हो? कमेन्टमा लेख्नुहोस्</div></div></div>
</div>
<script>
const S={json.dumps(signs, ensure_ascii=False)}, INTRO={INTRO}, PER={PER}, OUTRO={OUTRO};
const $=id=>document.getElementById(id), fills=[...document.querySelectorAll('.fill')];
const ease=x=>1-Math.pow(1-Math.min(Math.max(x,0),1),3);
function show(id){{for(const s of ['intro','sign','outro'])$(s).style.opacity=s===id?1:0;}}
window.renderAt=function(t){{
  const k=Math.floor((t-INTRO)/PER);
  fills.forEach((f,i)=>{{let w=0;if(t>=INTRO){{if(i<k)w=100;else if(i===k)w=100*((t-INTRO-i*PER)/PER);}}if(t>=INTRO+12*PER)w=100;f.style.width=Math.min(Math.max(w,0),100)+'%';}});
  if(t<INTRO){{show('intro');
    ['t1','t2','t3','t4'].forEach((id,i)=>{{const e=ease((t-0.15-i*0.25)/0.5);$(id).style.opacity=e;$(id).style.transform=`translateY(${{(1-e)*40}}px)`;}});
    const out=ease((t-(INTRO-0.3))/0.3);$('intro').style.opacity=1-out;return;}}
  if(k<12){{show('sign');const s=S[k],lt=t-INTRO-k*PER;
    if($('nm').textContent!==s.name){{$('nm').textContent=s.name;$('tx').textContent=s.text;$('num').textContent=s.num;}}
    const a=ease(lt/0.35),b=ease((lt-(PER-0.25))/0.25);
    $('card').style.transform=`translateX(${{(1-a)*140-b*140}}px)`;$('card').style.opacity=a*(1-b);
    $('tx').style.opacity=ease((lt-0.2)/0.35);return;}}
  show('outro');const e=ease((t-INTRO-12*PER)/0.5);$('outro').style.opacity=e;$('outro').style.transform=`scale(${{0.96+0.04*e}})`;
}};
</script></body></html>"""


def reel_caption(c):
    """Copy-paste caption for posting the reel by hand."""
    from daily import EMOJI, ORDER
    lines = [f"🔮 आजको राशिफल | {c['weekday']}, {c['date']}", "",
             "रील हेर्नुहोस् र आफ्नो राशिको दिन कस्तो छ थाहा पाउनुहोस् 👇", ""]
    for e, n in zip(EMOJI, ORDER):
        lines.append(f"{e} {n}: {c['signs'][n]}")
    lines += ["", "👇 तपाईंको राशि कुन हो? कमेन्टमा लेख्नुहोस् र साथीलाई पनि सेयर गर्नुहोस्।", "",
              "📌 दिनहुँ राशिफलका लागि छिटो खबर लाई फलो गर्नुहोस्।", "",
              "#राशिफल #आजकोराशिफल #छिटोखबर #नेपाल #reels #rashifal"]
    return "\n".join(lines)


def write_caption(c, out):
    cap = pathlib.Path(out).with_suffix(".txt")
    cap.parent.mkdir(parents=True, exist_ok=True)
    cap.write_text(reel_caption(c), encoding="utf-8")
    print("caption", cap)


def main(src, out):
    c = json.loads(pathlib.Path(src).read_text(encoding="utf-8"))
    if not c.get("weekday") or not c.get("date"):
        sys.exit("run daily.py build first (weekday/date missing)")
    write_caption(c, out)
    total = INTRO + 12 * PER + OUTRO
    n = round(total * FPS)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="reel_"))
    pf = HERE / "_reel.html"
    pf.write_text(page(c), encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(pf.as_uri()); pg.evaluate("document.fonts.ready")
        h = pg.evaluate("Math.max(...[...document.querySelectorAll('#card')].map(e=>e.getBoundingClientRect().bottom))")
        for i in range(n):
            pg.evaluate(f"renderAt({i / FPS})")
            pg.screenshot(path=str(tmp / f"f{i:05d}.jpg"), type="jpeg", quality=92)
        # check the longest reading fits on its card above the reel caption area
        tallest = 0
        for k in range(12):
            pg.evaluate(f"renderAt({INTRO + k * PER + 1.0})")
            tallest = max(tallest, pg.evaluate("document.getElementById('card').getBoundingClientRect().bottom"))
        b.close()
    if tallest > 1560:
        sys.exit(f"a reading is too long for the reel (card ends at {tallest:.0f}px); shorten it")
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%05d.jpg"),
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-shortest",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(out)], check=True)
    shutil.rmtree(tmp)
    pf.unlink(missing_ok=True)
    print("reel", out, f"{total:.1f}s")


if __name__ == "__main__":
    # python3 reel.py content/DAY.json reels/DAY.mp4            -> reel + reels/DAY.txt caption
    # python3 reel.py --caption-only content/DAY.json reels/DAY.mp4 -> only the caption
    if sys.argv[1] == "--caption-only":
        c = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
        write_caption(c, sys.argv[3])
    else:
        main(sys.argv[1], sys.argv[2])
