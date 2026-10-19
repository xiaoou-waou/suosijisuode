#!/usr/bin/env python3
"""Draw 所得's mark and write every icon the apps and the docs use.

The mark is an open cool-white arc (a thought) with a warm ivory pearl in the
gap (what arrived), on a midnight squircle. The menu-bar and tray art use a
thicker stroke so the same mark still reads at 18 px. Indexing uses a dimmed
metal version of that art; the shell and the Mac status item sweep the bright
art back in clockwise. Paused art puts two bars where the pearl sits. The
update dot is drawn by the apps, not baked into these pictures.

    python3 scripts/make-icon.py
"""

import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "Resources" / "AppIcon"

# Midnight squircle, cool-white metal, warm ivory pearl.
MIDNIGHT_TOP = (28, 42, 74)
MIDNIGHT = (16, 22, 42)
MIDNIGHT_BOTTOM = (10, 14, 28)
ARC_LIGHT = (247, 249, 252)
ARC_MID = (228, 235, 244)
ARC_SHADE = (188, 200, 216)
PEARL_HI = (255, 250, 242)
PEARL = (246, 230, 200)
PEARL_EDGE = (196, 160, 104)
PEARL_SHADOW = (120, 90, 52)
DIM_ARC = (108, 120, 140)
DIM_ARC_SHADE = (72, 82, 100)
DIM_PEARL = (108, 100, 90)
DIM_BG = (8, 10, 18)

# Gap sits just below the right-hand point of the ring: the thought opens, the pearl arrives.
GAP_CENTER = 32.0


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def squircle_mask(size, pad, n=5.0):
    """Alpha for a macOS-style superellipse, antialiased."""
    yy, xx = np.ogrid[0:size, 0:size]
    center = (size - 1) / 2.0
    radius = center * (1.0 - pad)
    x = (xx - center) / radius
    y = (yy - center) / radius
    distance = (np.abs(x) ** n + np.abs(y) ** n) ** (1.0 / n)
    aa = 1.25 / radius
    return np.clip((1.0 - distance) / aa + 0.5, 0.0, 1.0).astype(np.float32)


def vertical_gradient(size, top, bottom):
    t = np.linspace(0.0, 1.0, size, dtype=np.float32)[:, None]
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    for i in range(3):
        rgb[:, :, i] = top[i] + (bottom[i] - top[i]) * t
    return rgb


def angle_point(cx, cy, radius, degrees):
    rad = math.radians(degrees)
    return cx + radius * math.cos(rad), cy + radius * math.sin(rad)


def arc_mask(size, radius, stroke, gap, color_width=None):
    """Open ring with round caps. `gap` is the opening in degrees around GAP_CENTER."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    cx = cy = (size - 1) / 2.0
    box = [cx - radius, cy - radius, cx + radius, cy + radius]
    start = GAP_CENTER + gap / 2.0
    end = GAP_CENTER - gap / 2.0 + 360.0
    width = color_width or stroke
    draw.arc(box, start, end, fill=255, width=int(width))
    cap = stroke / 2.0
    for degrees in (start, GAP_CENTER - gap / 2.0):
        x, y = angle_point(cx, cy, radius, degrees)
        draw.ellipse([x - cap, y - cap, x + cap, y + cap], fill=255)
    return mask


def paint_arc(base, size, radius, stroke, gap, light, mid, shade):
    """Metal arc: a shaded ring with a cool highlight shifted up and left."""
    mask = arc_mask(size, radius, stroke, gap)
    shade_mask = arc_mask(size, radius, stroke, gap)
    # Highlight sits a couple of pixels up-left, clipped to the arc.
    shift = max(1, int(stroke * 0.08))
    highlight = Image.new("L", (size, size), 0)
    highlight.paste(arc_mask(size, radius, max(2, int(stroke * 0.72)), gap), (-shift, -shift))
    arc = np.array(mask, dtype=np.float32) / 255.0
    high = np.array(highlight, dtype=np.float32) / 255.0
    high = np.minimum(high, arc)
    shade_a = np.array(shade_mask, dtype=np.float32) / 255.0
    rgb = np.array(base.convert("RGBA"), dtype=np.float32)
    color = np.zeros_like(rgb[:, :, :3])
    for i in range(3):
        tone = np.full((size, size), mid[i], dtype=np.float32)
        tone = tone * (1.0 - shade_a * 0.0) 
        tone = np.where(high > 0.2, light[i], mid[i]).astype(np.float32)
        # A darker rim along the lower-right of the stroke.
        tone = tone * (1.0 - (arc - high) * 0.22) + shade[i] * (arc - high) * 0.22
        color[:, :, i] = tone
    a = arc[:, :, None]
    rgb[:, :, :3] = rgb[:, :, :3] * (1.0 - a) + color * a
    rgb[:, :, 3] = np.maximum(rgb[:, :, 3], arc * 255.0)
    return Image.fromarray(rgb.astype(np.uint8), "RGBA")


def paint_pearl(base, cx, cy, radius, bright=True):
    size = base.size[0]
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = overlay.load()
    hi = PEARL_HI if bright else DIM_PEARL
    body = PEARL if bright else DIM_PEARL
    edge = PEARL_EDGE if bright else DIM_PEARL
    shadow = PEARL_SHADOW if bright else DIM_BG
    # Soft contact shadow.
    shadow_img = Image.new("L", (size, size), 0)
    sd = ImageDraw.Draw(shadow_img)
    sd.ellipse([cx - radius, cy - radius * 0.92 + radius * 0.18, cx + radius, cy + radius * 1.05], fill=160)
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius * 0.18))
    sa = np.array(shadow_img, dtype=np.float32) / 255.0
    arr = np.array(base, dtype=np.float32)
    for i in range(3):
        arr[:, :, i] = arr[:, :, i] * (1.0 - sa * 0.45) + shadow[i] * sa * 0.45
    base = Image.fromarray(arr.astype(np.uint8), "RGBA")

    draw = ImageDraw.Draw(overlay)
    # Radial body, sampled in rings so the highlight sits up-left of center.
    steps = max(8, int(radius))
    hx, hy = cx - radius * 0.32, cy - radius * 0.36
    for step in range(steps, 0, -1):
        t = step / steps
        # Distance from the highlight, not the center, so the pearl turns toward the light.
        tone = t ** 0.85
        if tone < 0.25:
            color = lerp(hi, body, tone / 0.25)
        elif tone < 0.72:
            color = lerp(body, edge, (tone - 0.25) / 0.47)
        else:
            color = lerp(edge, shadow, (tone - 0.72) / 0.28)
        r = radius * t
        alpha = 255 if t < 0.98 else int(255 * (1.0 - t) / 0.02)
        draw.ellipse([hx - r, hy - r, hx + r, hy + r], fill=color + (alpha,))
    # Keep the disc centered on the pearl, not the highlight: clip to the true circle.
    clip = Image.new("L", (size, size), 0)
    ImageDraw.Draw(clip).ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=255)
    overlay.putalpha(Image.fromarray(np.minimum(np.array(overlay.getchannel("A")), np.array(clip))))
    # Specular pin.
    if bright:
        pr = radius * 0.16
        ImageDraw.Draw(overlay).ellipse(
            [cx - radius * 0.38 - pr, cy - radius * 0.42 - pr, cx - radius * 0.38 + pr, cy - radius * 0.42 + pr],
            fill=(255, 255, 255, 210),
        )
    return Image.alpha_composite(base, overlay)


def paint_bars(base, cx, cy, radius):
    """Two ivory bars in the pearl's place."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    bar_w = radius * 0.46
    bar_h = radius * 2.15
    gap = radius * 0.34
    for sign in (-1, 1):
        x = cx + sign * (gap / 2 + bar_w / 2)
        box = [x - bar_w / 2, cy - bar_h / 2, x + bar_w / 2, cy + bar_h / 2]
        draw.rounded_rectangle(box, radius=bar_w / 2, fill=PEARL_EDGE + (255,))
        inset = bar_w * 0.14
        inner = [box[0] + inset * 0.2, box[1] + inset, box[2] - inset, box[3] - inset * 0.4]
        draw.rounded_rectangle(inner, radius=bar_w / 2, fill=PEARL + (255,))
        draw.rounded_rectangle(
            [inner[0], inner[1], inner[2], inner[1] + bar_h * 0.28],
            radius=bar_w / 3,
            fill=PEARL_HI + (180,),
        )
    return Image.alpha_composite(base, overlay)


def render(size, thick=False, dim=False, paused=False):
    stroke = size * (0.115 if thick else 0.074)
    radius = size * (0.255 if thick else 0.268)
    gap = 78.0 if thick else 70.0
    pearl_r = size * (0.102 if thick else 0.090)
    pad = 0.045 if thick else 0.055

    mask = squircle_mask(size, pad)
    if dim:
        gradient = vertical_gradient(size, (18, 22, 32), DIM_BG)
    else:
        gradient = vertical_gradient(size, MIDNIGHT_TOP, MIDNIGHT_BOTTOM)
    rgb = np.zeros((size, size, 4), dtype=np.float32)
    rgb[:, :, :3] = gradient
    rgb[:, :, 3] = mask * 255.0
    # A cool inner sheen along the top, so the squircle isn't a flat fill.
    if not dim:
        sheen = np.linspace(1.0, 0.0, size, dtype=np.float32)[:, None]
        sheen = np.clip((0.42 - (np.ogrid[0:size, 0:size][0] / size)) / 0.42, 0, 1) * mask
        for i in range(3):
            rgb[:, :, i] += sheen * (12 if i == 2 else 8)
    image = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGBA")

    if dim:
        image = paint_arc(image, size, radius, stroke, gap, DIM_ARC, DIM_ARC, DIM_ARC_SHADE)
    else:
        image = paint_arc(image, size, radius, stroke, gap, ARC_LIGHT, ARC_MID, ARC_SHADE)

    cx, cy = angle_point((size - 1) / 2.0, (size - 1) / 2.0, radius * 0.90, GAP_CENTER)
    if paused:
        image = paint_bars(image, cx, cy, pearl_r)
    else:
        image = paint_pearl(image, cx, cy, pearl_r, bright=not dim)
    return image


def resize(image, size):
    return image.resize((size, size), Image.Resampling.LANCZOS)


def png_bytes(image):
    from io import BytesIO
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def write_icns(path, master):
    """Modern icns: PNG chunks for the sizes iconutil would write."""
    mapping = [
        (b"icp4", 16),
        (b"icp5", 32),
        (b"icp6", 64),
        (b"ic07", 128),
        (b"ic08", 256),
        (b"ic09", 512),
        (b"ic10", 1024),
        (b"ic11", 32),
        (b"ic12", 64),
        (b"ic13", 256),
        (b"ic14", 512),
    ]
    chunks = []
    for ostype, side in mapping:
        data = png_bytes(resize(master, side))
        chunks.append(ostype + struct.pack(">I", 8 + len(data)) + data)
    body = b"".join(chunks)
    path.write_bytes(b"icns" + struct.pack(">I", 8 + len(body)) + body)


def write_svg(path, thick, dim=False, paused=False):
    """Same geometry as the bitmap, for Icon Composer and the icon notes."""
    stroke = 118 if thick else 76
    radius = 250
    gap = 78 if thick else 70
    pearl = 104 if thick else 92
    start = GAP_CENTER + gap / 2.0
    end = GAP_CENTER - gap / 2.0

    def svg_point(degrees, r):
        rad = math.radians(degrees)
        return 512 + r * math.cos(rad), 512 + r * math.sin(rad)

    x1, y1 = svg_point(start, radius)
    x2, y2 = svg_point(end, radius)
    px, py = svg_point(GAP_CENTER, radius * 0.90)
    path_d = f"M {x1:.1f} {y1:.1f} A {radius} {radius} 0 1 1 {x2:.1f} {y2:.1f}"
    if dim:
        night, metal, pearl_fill = "#12151c", "#6c7890", "#6c645a"
    else:
        night, metal, pearl_fill = "url(#night)", "url(#metal)", "url(#pearl)"
    if paused:
        bar_w, bar_h, gap_b = pearl * 0.46, pearl * 2.15, pearl * 0.34
        bars = ""
        for sign in (-1, 1):
            x = px + sign * (gap_b / 2 + bar_w / 2) - bar_w / 2
            y = py - bar_h / 2
            bars += f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="{bar_w/2:.1f}" fill="#f6e6c8"/>'
        center = bars
    else:
        center = f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{pearl}" fill="{pearl_fill}"/>'
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="night" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1c2a4a"/>
      <stop offset="1" stop-color="#0a0e1c"/>
    </linearGradient>
    <linearGradient id="metal" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f7f9fc"/>
      <stop offset="1" stop-color="#d5deea"/>
    </linearGradient>
    <radialGradient id="pearl" cx="38%" cy="36%" r="70%">
      <stop offset="0" stop-color="#fffaf2"/>
      <stop offset="0.45" stop-color="#f6e6c8"/>
      <stop offset="1" stop-color="#c4a068"/>
    </radialGradient>
  </defs>
  <rect x="56" y="56" width="912" height="912" rx="210" fill="{night}"/>
  <path d="{path_d}" fill="none" stroke="{metal}" stroke-width="{stroke}" stroke-linecap="round"/>
  {center}
</svg>
"""
    path.write_text(svg)


def main():
    app = render(1024, thick=False)
    tray = render(1024, thick=True)
    dim = render(1024, thick=True, dim=True)
    paused = render(1024, thick=True, paused=True)
    if list(app.getdata()) == list(tray.getdata()):
        raise SystemExit("menu-bar stroke should differ from the app icon")
    if list(tray.getdata()) == list(dim.getdata()) or list(dim.getdata()) == list(paused.getdata()):
        raise SystemExit("idle, indexing and paused art must differ")

    ICON.mkdir(parents=True, exist_ok=True)
    (ICON / "AppIcon.icon" / "Assets").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "shell" / "ui").mkdir(parents=True, exist_ok=True)
    icons = ROOT / "shell" / "src-tauri" / "icons"
    icons.mkdir(parents=True, exist_ok=True)

    app.save(ROOT / "docs" / "logo.png")
    resize(app, 512).save(ROOT / "shell" / "ui" / "icon.png")
    resize(tray, 128).save(ICON / "tray.png")
    resize(dim, 128).save(ICON / "tray-dim.png")
    resize(paused, 128).save(ICON / "tray-paused.png")
    write_icns(ROOT / "Resources" / "AppIcon.icns", app)
    write_icns(icons / "icon.icns", app)

    resize(app, 32).save(icons / "32x32.png")
    resize(app, 128).save(icons / "128x128.png")
    resize(app, 256).save(icons / "128x128@2x.png")
    resize(app, 512).save(icons / "icon.png")
    resize(app, 256).save(icons / "icon.ico", format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    write_svg(ICON / "appicon.svg", thick=False)
    write_svg(ICON / "appicon-small.svg", thick=True)
    write_svg(ICON / "tray.svg", thick=True)
    write_svg(ICON / "menubar.svg", thick=True)
    # Dim and paused SVGs are the sources the bitmaps come from; the apps draw the sweep and the dot themselves.
    write_svg(ICON / "tray-dim.svg", thick=True, dim=True)
    write_svg(ICON / "tray-paused.svg", thick=True, paused=True)
    write_svg(ICON / "AppIcon.icon" / "Assets" / "mark.svg", thick=False)
    for stale in ("d-mark.svg", "tiles.svg"):
        leftover = ICON / "AppIcon.icon" / "Assets" / stale
        if leftover.exists():
            leftover.unlink()

    (ICON / "AppIcon.icon" / "icon.json").write_text(
        """{
  "fill" : {
    "solid" : "srgb:0.06275,0.08627,0.16471,1.00000"
  },
  "groups" : [
    {
      "layers" : [
        {
          "image-name" : "mark.svg",
          "name" : "mark"
        }
      ],
      "name" : "Mark"
    }
  ],
  "supported-platforms" : {
    "squares" : "shared"
  }
}
"""
    )
    (ICON / "README.md").write_text(
        """# 所得的图标

开口的冷白弧是所想，弧口里的暖象牙珍珠是所得，底是午夜圆角方。

- `appicon.svg`：应用图标。`scripts/make-icon.py` 把它画成 `../AppIcon.icns`、`docs/logo.png`、`shell/ui/icon.png` 和 `shell/src-tauri/icons`。
- `menubar.svg` 与 `tray.svg`：菜单栏和托盘用的同一枚标记，笔画更粗，缩到很小仍看得清。
- `tray-dim.svg`：索引时金属弧变暗。Mac 的 `StatusIcon` 和 shell 的 `tray_icon.rs` 从顶部顺时针把亮色扫回来。
- `tray-paused.svg`：暂停时珍珠的位置换成两道竖条。
- 有更新时，右上角的圆点是程序画上去的，不在这些图里。
- `AppIcon.icon`：同一设计的 Icon Composer 稿（午夜底 + 弧与珍珠）。`build.sh` 用 `actool` 编进 `Assets.car`。

重新生成全部位图：

```sh
python3 scripts/make-icon.py
```

颜色：午夜 `#10162A`；冷白弧 `#F7F9FC`；暖象牙珍珠 `#F6E6C8`。不要用 DigUp 的四色块，也不要用它的绿和琥珀。
"""
    )
    print("wrote icons")


if __name__ == "__main__":
    main()
