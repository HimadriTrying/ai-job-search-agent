#!/usr/bin/env python3
"""
build_demo.py — render the Lucy product demo (GIF + MP4) frame by frame.

Why frames rather than a screen recording: a recording of a real session is at the mercy of
model latency and terminal reflow, and cannot be regenerated identically when the copy
changes. This builds each frame as HTML and composes them with explicit per-frame durations,
so the demo is deterministic, re-renderable, and diffable in review.

HONESTY NOTE — read before editing the SCENES below.
Every line of output in this demo is text the tools actually produced on 29 Jul 2026:
  * the digest block is the real output of
      python run.py --offline tests/fixtures/jobs.sample.json
  * the honesty-gate block is the real output of
      python honesty/verify.py <draft> --facts <facts> --target "Acme Corp"
    on a draft claiming 42% against a facts file recording 18%.
Output is reflowed and truncated to fit the frame; it is never invented. If you change a
line here, it must still be something the tool would print. This project's whole claim is
that it does not overstate, and the demo is the most-seen artefact it ships.

Usage:  python build_demo.py [--out DIR]
Needs:  chromium + ffmpeg (paths below), Pillow only for the poster frame.
"""

from __future__ import annotations
import argparse
import html
import shutil
import subprocess
from pathlib import Path

CHROME = "/opt/pw-browsers/chromium"
FFMPEG = "/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux"
W, H = 1000, 500

# ── The session ──────────────────────────────────────────────────────────────────
# Each scene is (kind, payload, seconds). Kinds:
#   "type"  — a user prompt, revealed character by character
#   "line"  — one output line appended, held for `seconds`
#   "hold"  — hold the current screen
#   "clear" — reset the screen
CMD1 = "what's out there for me?"
CMD2 = "tailor my CV for the first one"

SCENES: list[tuple[str, str, float]] = [
    ("hold", "", 0.7),
    ("type", CMD1, 1.4),
    ("hold", "", 0.4),
    ("line", '<span class="dim">Sweeping Greenhouse, Lever, Ashby, SmartRecruiters…</span>', 0.9),
    ("line", '<span class="dim">7 listings → 1 apply first · 1 worth a look · 2 skipped · 3 dropped</span>', 0.9),
    ("line", "", 0.15),
    ("line", '<span class="hd">APPLY FIRST</span>', 0.5),
    ("line", '<span class="ok">Senior Product Manager, AI Platform</span>  <span class="dim">Berlin</span>   <span class="score">+5</span>', 0.7),
    ("line", '  <span class="dim">+2 AI-forward · +2 staff-level altitude · +1 platform, 0 to 1, b2b</span>', 1.5),
    ("line", "", 0.15),
    ("line", '<span class="hd">DROPPED BEFORE SCORING</span> <span class="dim">so you never read them</span>', 0.5),
    ("line", '<span class="no">Junior Product Manager</span>          <span class="dim">below your seniority floor</span>', 0.6),
    ("line", '<span class="no">Director of Product, Payments</span>   <span class="dim">needs 12y, you have 5</span>', 1.8),
    ("clear", "", 0.3),
    ("type", CMD2, 1.6),
    ("hold", "", 0.4),
    ("line", '<span class="dim">Drafting, then checking every claim against career_facts.yaml…</span>', 1.3),
    ("line", "", 0.15),
    ("line", '<span class="fail">HONESTY GATE FAILED</span>', 0.8),
    ("line", '<span class="no">⚠ Metric \'42\' has no basis in career_facts.yaml</span>', 0.7),
    ("line", '  <span class="dim">near: "…grew activation 42% over two quarters…"</span>', 1.6),
    ("line", "", 0.15),
    ("line", '<span class="dim">Rewriting with the number you can actually defend…</span>', 1.3),
    ("line", '<span class="ok">✓ Honesty gate passed</span>  <span class="dim">activation 18%, from your own record</span>', 2.4),
    ("end", "", 2.6),
]

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="../../_card.css">
<style>
  body{{background:var(--paper)}}
  .card{{padding:0;display:flex;align-items:center;justify-content:center;background:var(--paper)}}
  .shell{{margin:auto}}
  .bloom-a{{width:520px;height:520px;right:-190px;top:-230px}}
  .bloom-b{{width:460px;height:460px;left:-200px;bottom:-240px}}
  .shell{{width:{sw}px;position:relative;z-index:1;margin:auto}}
  .bar{{display:flex;align-items:center;gap:8px;padding:12px 16px;
       background:#241f29;border-radius:14px 14px 0 0}}
  .bar i{{width:11px;height:11px;border-radius:50%;display:block}}
  .bar .t{{margin-left:10px;font-size:.8rem;color:#8b8494;font-family:var(--sans)}}
  .term{{border-radius:0 0 14px 14px;padding:22px 26px;font-size:15.5px;line-height:1.85;
        height:{th}px;overflow:hidden}}
  .row{{white-space:pre-wrap;word-break:break-word}}
  .hd{{color:#cbb8ff;letter-spacing:.09em;font-size:.82em}}
  .score{{color:#7ee0a8}}
  .fail{{color:#ff8f8f;font-weight:700;letter-spacing:.05em}}
  .cur{{display:inline-block;width:9px;height:1.05em;background:#f7b2d0;
       vertical-align:-2px;margin-left:2px}}
  .end{{position:absolute;inset:0;display:flex;flex-direction:column;
       align-items:center;justify-content:center;gap:14px;background:var(--paper);z-index:5}}
  .end .wordmark{{font-size:3.4rem}}
  .end .tag{{font-family:var(--display);font-size:1.5rem;color:var(--ink-2)}}
  .end .url{{font-size:1rem;color:var(--ink-3);letter-spacing:.02em}}
</style></head><body>
<div class="card">
  <div class="bloom bloom-a"></div><div class="bloom bloom-b"></div>
  {body}
</div></body></html>"""

SHELL = """<div class="shell">
    <div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i>
      <i style="background:#28c840"></i><span class="t">lucy — claude code</span></div>
    <div class="term">{rows}</div>
  </div>"""

END = """<div class="end">
    <div class="wordmark">Lucy</div>
    <div class="tag">One agent for the <em>whole</em> job search.</div>
    <div class="url">open source &middot; runs on your machine</div>
  </div>"""


def render_rows(rows: list[str], typing: str | None) -> str:
    out = list(rows)
    if typing is not None:
        out.append(f'<span class="you">&gt; </span>{html.escape(typing)}<span class="cur"></span>')
    return "".join(f'<div class="row">{r}</div>' for r in out)


def build_frames(outdir: Path) -> list[tuple[Path, float]]:
    frames: list[tuple[Path, float]] = []
    rows: list[str] = []
    n = 0

    def emit(body: str, secs: float):
        nonlocal n
        p = outdir / f"f{n:04d}.html"
        p.write_text(PAGE.format(body=body, sw=W - 150, th=H - 170))
        frames.append((p, secs))
        n += 1

    for kind, payload, secs in SCENES:
        if kind == "clear":
            rows = []
            emit(SHELL.format(rows=render_rows(rows, "")), secs)
        elif kind == "type":
            # Reveal the command a few characters at a time, then commit it as a row.
            step = max(1, len(payload) // 14)
            per = secs / max(1, (len(payload) // step) + 1)
            for i in range(step, len(payload) + step, step):
                emit(SHELL.format(rows=render_rows(rows, payload[:i])), per)
            rows.append(f'<span class="you">&gt; </span>{html.escape(payload)}')
            emit(SHELL.format(rows=render_rows(rows, None)), 0.25)
        elif kind == "line":
            rows.append(payload)
            emit(SHELL.format(rows=render_rows(rows, None)), secs)
        elif kind == "hold":
            emit(SHELL.format(rows=render_rows(rows, "" if not rows else None)), secs)
        elif kind == "end":
            emit(SHELL.format(rows=render_rows(rows, None)) + END, secs)
    return frames


def shoot(frames: list[tuple[Path, float]], outdir: Path, scale: int) -> list[tuple[Path, float]]:
    shots = []
    for i, (src, secs) in enumerate(frames):
        png = outdir / f"p{i:04d}.png"
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             f"--force-device-scale-factor={scale}", f"--window-size={W},{H}",
             f"--screenshot={png}", f"file://{src}"],
            check=True, capture_output=True)
        shots.append((png, secs))
    return shots


def encode(shots: list[tuple[Path, float]], outdir: Path, out: Path):
    """GIF via Pillow, WebM via ffmpeg.

    The bundled Playwright ffmpeg is a stripped build: VP8 is its only video encoder and
    WebM its only muxer, so there is no libx264 for MP4 and no GIF encoder. Pillow writes
    the animated GIF instead, which also gives exact per-frame durations without the
    concat-demuxer dance.
    """
    from PIL import Image

    imgs = [Image.open(p).convert("RGB") for p, _ in shots]
    gif_w = 680
    imgs = [im.resize((gif_w, round(im.height * gif_w / im.width)), Image.LANCZOS)
            for im in imgs]

    # Every frame must share ONE palette. Quantising each frame independently gives each its
    # own palette, and Pillow then silently collapsed 64 frames into 2. Build the palette from
    # a composite of frames spread across the run so late-scene colours are represented, then
    # map every frame onto it.
    sample = imgs[0].copy()
    picks = imgs[:: max(1, len(imgs) // 12)]
    strip = Image.new("RGB", (gif_w, sample.height * len(picks)))
    for i, im in enumerate(picks):
        strip.paste(im, (0, i * sample.height))
    base = strip.quantize(colors=112, method=Image.MEDIANCUT)

    frames = [im.quantize(palette=base, dither=Image.FLOYDSTEINBERG) for im in imgs]
    frames[0].save(out, save_all=True, append_images=frames[1:], loop=0, optimize=False,
                   duration=[max(20, int(s * 1000)) for _, s in shots], disposal=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent))
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()
    outdir = Path(args.out)
    work = outdir / "_frames"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    frames = build_frames(work)
    shots = shoot(frames, work, args.scale)
    gif = outdir / "lucy-demo.gif"
    encode(shots, work, gif)
    shutil.copy(shots[len(shots) // 3][0], outdir / "lucy-demo-poster.png")
    total = sum(s for _, s in frames)
    print(f"{len(frames)} frames, {total:.1f}s")
    print(f"GIF   {gif}  ({gif.stat().st_size/1024:.0f} KB)")

    shutil.rmtree(work)


if __name__ == "__main__":
    main()
