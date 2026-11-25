"""Screens for the diorama monitors that the look-dev frames don't cover. Run with any Python that has Pillow:

    python video/v2/world/make_screens.py

Writes video/v2/world/screens/:
    shop-night-16x10.png, shop-tuesday-16x10.png
                         the shop PC at the 3D monitor's own 16:10 shape, rendered from the look-dev page
                         (render_shop_screens.js, node + the installed Chrome): Thursday 21:47's nine tabs, and
                         Tuesday 24 Nov 08:34's Jobs page with Priya's two wheel builds
    shop-tuesday.png     16:9 fallback if node/Chrome aren't there: frame 08 with its gadget and clock moved on a day
    shop-asleep.png      the shop PC asleep (scene 9): a black panel, Barnaby's bell glowing small in the corner
    lisbon-*.png         placeholders for Theo's Lisbon desk, used only when look/frames/lisbon-*.png don't exist yet
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.normpath(os.path.join(HERE, "..", "look", "frames"))
OUT = os.path.join(HERE, "screens")
FONTS = r"C:\Windows\Fonts"
GOLD = (201, 160, 74)          # Livery: lining gold #C9A04A
GREEN = (23, 64, 47)           # Livery: Hartley green #17402F


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def shop_tuesday():
    """Frame 08 says Monday 23, 11:31. Repaint the gadget (24 / Tuesday) and the clock (08:34, 24/11/2026)."""
    im = Image.open(os.path.join(FRAMES, "shop-pc-08-shop-jobs-after.png")).convert("RGB")
    px = im.load()
    d = ImageDraw.Draw(im)
    # calendar gadget: the paper is a vertical gradient, so refill each row with the colour at its left margin
    for y in range(476, 574):
        c = px[1712, y]
        d.line([(1722, y), (1842, y)], fill=c)
    d.text((1785, 509), "24", font=font("segoeuil.ttf", 76), fill=(30, 33, 40), anchor="mm")
    d.text((1785, 559), "Tuesday", font=font("segoeui.ttf", 20), fill=(52, 58, 68), anchor="mm")
    # taskbar clock: same trick, the bar is a vertical gradient
    for y in range(1028, 1078):
        c = px[1774, y]
        d.line([(1780, y), (1902, y)], fill=c)
    d.text((1834, 1040), "08:34", font=font("segoeui.ttf", 17), fill=(255, 255, 255), anchor="mm")
    d.text((1834, 1063), "24/11/2026", font=font("segoeui.ttf", 17), fill=(255, 255, 255), anchor="mm")
    im.save(os.path.join(OUT, "shop-tuesday.png"))


def bell_glyph(size, colour, width=None):
    """Barnaby's bell as a filled silhouette drawn to survive being 20 px tall on a monitor across the room: a full
    hemisphere dome standing clear of a wider, thicker base, a thin plunger, a ball knob, a pale highlight. Drawn in a
    64-unit box; the bell is 46 units tall."""
    s = size / 64.0
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4 * s, 51 * s, 60 * s, 59 * s], radius=3 * s, fill=colour)              # base
    d.pieslice([12 * s, 27 * s, 52 * s, 67 * s], 180, 360, fill=colour)                        # dome
    d.rectangle([12 * s, 46.2 * s, 52 * s, 47.6 * s], fill=colour)                             # dome's rim
    d.rectangle([30.6 * s, 17 * s, 33.4 * s, 28 * s], fill=colour)                             # plunger
    d.ellipse([26.5 * s, 11 * s, 37.5 * s, 20 * s], fill=colour)                               # knob
    d.arc([17 * s, 32 * s, 43 * s, 58 * s], 200, 250, fill=(255, 240, 205, 255), width=max(1, int(2.4 * s)))
    return im


def asleep(w, h, corner="br", scale=1.0, path=None, base=(0, 0, 0), frac=0.105):
    """A sleeping panel: black, Barnaby's bell glowing softly in one corner, about `frac` of the screen's height."""
    im = Image.new("RGB", (w, h), base)
    g = int(h * frac * 64 / 46)                               # glyph box so the bell itself is frac * h tall
    bell = bell_glyph(g, GOLD + (255,))
    m = int(h * 0.045)
    x = w - g - m if "r" in corner else m
    y = h - g - m if "b" in corner else m
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(glow)
    cx, cy, r = x + g // 2, y + int(g * 0.6), int(g * 0.95)
    hd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(g * 0.45))
    soft = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    soft.alpha_composite(bell, (x, y))
    glow.alpha_composite(soft.filter(ImageFilter.GaussianBlur(max(2, g // 30))))
    glow.alpha_composite(soft)
    out = im.convert("RGBA")
    out.alpha_composite(glow)
    out.convert("RGB").save(path)


def lisbon_main(path, w=2560, h=1440):
    """Placeholder: a dark tiling desktop (Linux): a terminal with Synapse's output, an editor, and a browser tile with
    the real Barnaby app (look/lisbon-pc/realapp/probe-1440.png if present)."""
    bg = (17, 19, 24)
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    bar = 30
    d.rectangle([0, 0, w, bar], fill=(11, 12, 15))
    for i, ws in enumerate("12345"):
        col = (201, 160, 74) if i == 0 else (120, 124, 132)
        d.text((14 + i * 26, 6), ws, font=font("CascadiaMono.ttf", 16), fill=col)
    d.text((w - 210, 6), "Tue 24 Nov  10:12", font=font("CascadiaMono.ttf", 16), fill=(180, 184, 190))
    gap = 10
    tiles = [(gap, bar + gap, int(w * 0.36), h - gap), (int(w * 0.36) + gap, bar + gap, w - gap, h - gap)]
    # terminal (left)
    x0, y0, x1, y1 = tiles[0]
    d.rectangle(tiles[0], fill=(22, 24, 30), outline=(201, 160, 74), width=2)
    mono = font("CascadiaMono.ttf", 19)
    lines = [("theo@lisboa:~/crew-memory$ ", "synapse build --auto --local", (230, 232, 236)),
             ("", "Scanning repository ...", (150, 156, 166)),
             ("", "  routes      13", (150, 156, 166)), ("", "  handlers    13", (150, 156, 166)),
             ("", "  tests       41 passed", (120, 190, 120)),
             ("", "Extracted 13 endpoint(s) in 0.4 s", (201, 160, 74)), ("", "", (0, 0, 0)),
             ("theo@lisboa:~/crew-memory$ ", "synapse build comfyui", (230, 232, 236)),
             ("", "Extracted 28 endpoint(s) in 0.6 s", (201, 160, 74)), ("", "", (0, 0, 0)),
             ("theo@lisboa:~/crew-memory$ ", "_", (230, 232, 236))]
    y = y0 + 18
    for pre, txt, col in lines:
        if pre:
            d.text((x0 + 18, y), pre, font=mono, fill=(110, 170, 130))
            d.text((x0 + 18 + d.textlength(pre, font=mono), y), txt, font=mono, fill=col)
        else:
            d.text((x0 + 18, y), txt, font=mono, fill=col)
        y += 30
    # browser tile with the real app
    x0, y0, x1, y1 = tiles[1]
    d.rectangle(tiles[1], fill=(28, 30, 36), outline=(60, 64, 72), width=2)
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y0 + 44], fill=(36, 38, 46))
    d.rounded_rectangle([x0 + 120, y0 + 9, x1 - 120, y0 + 36], 12, fill=(22, 24, 30))
    d.text((x0 + 140, y0 + 12), "localhost:8000  ·  Barnaby", font=font("segoeui.ttf", 17), fill=(170, 174, 182))
    app = os.path.normpath(os.path.join(HERE, "..", "look", "lisbon-pc", "realapp", "probe-1440.png"))
    if os.path.exists(app):
        a = Image.open(app).convert("RGB")
        tw, th = x1 - x0 - 4, y1 - y0 - 48
        a = a.resize((tw, int(a.height * tw / a.width)))
        im.paste(a.crop((0, 0, tw, min(th, a.height))), (x0 + 2, y0 + 46))
    im.save(path)


def lisbon_second(path, w=2560, h=1440):
    """Placeholder: a node graph (dark canvas, nodes and bezier links) with a render queue."""
    im = Image.new("RGB", (w, h), (30, 31, 35))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 40):
        d.line([(x, 0), (x, h)], fill=(36, 37, 42))
    for y in range(0, h, 40):
        d.line([(0, y), (w, y)], fill=(36, 37, 42))
    nodes = [(160, 240, "Load Checkpoint", (80, 110, 160)), (160, 640, "Load LoRA", (80, 110, 160)),
             (760, 200, "Prompt", (150, 120, 70)), (760, 560, "Negative", (150, 90, 80)),
             (1340, 360, "Sampler", (90, 140, 110)), (1880, 360, "Decode", (110, 100, 150)),
             (1880, 760, "Save Image", (90, 140, 110))]
    f = font("segoeui.ttf", 26)
    for i, (x, y, name, col) in enumerate(nodes):
        d.rounded_rectangle([x, y, x + 420, y + 300], 14, fill=(46, 48, 54), outline=(70, 72, 80), width=2)
        d.rounded_rectangle([x, y, x + 420, y + 46], 14, fill=col)
        d.text((x + 18, y + 8), name, font=f, fill=(240, 240, 240))
        for k in range(4):
            d.rounded_rectangle([x + 20, y + 70 + k * 52, x + 400, y + 106 + k * 52], 8, fill=(34, 36, 40))
    links = [(0, 2), (0, 3), (1, 4), (2, 4), (3, 4), (4, 5), (5, 6)]
    for a, b in links:
        ax, ay = nodes[a][0] + 420, nodes[a][1] + 120
        bx, by = nodes[b][0], nodes[b][1] + 120
        pts = []
        for i in range(41):
            t = i / 40
            c1x, c2x = ax + 200, bx - 200
            x = (1 - t) ** 3 * ax + 3 * (1 - t) ** 2 * t * c1x + 3 * (1 - t) * t ** 2 * c2x + t ** 3 * bx
            y = (1 - t) ** 3 * ay + 3 * (1 - t) ** 2 * t * ay + 3 * (1 - t) * t ** 2 * by + t ** 3 * by
            pts.append((x, y))
        d.line(pts, fill=(201, 160, 74), width=4)
    d.rounded_rectangle([w - 520, h - 420, w - 40, h - 40], 14, fill=(40, 42, 48), outline=(70, 72, 80), width=2)
    d.text((w - 500, h - 405), "Queue  ·  3 jobs", font=f, fill=(230, 230, 230))
    for k in range(3):
        d.rounded_rectangle([w - 500, h - 350 + k * 90, w - 60, h - 280 + k * 90], 8, fill=(54, 56, 62))
        d.rectangle([w - 500, h - 290 + k * 90, w - 500 + int(440 * (0.7 - 0.3 * k)), h - 284 + k * 90],
                    fill=(201, 160, 74))
    im.save(path)


def lisbon_laptop(path, w=2560, h=1600):
    """Placeholder: a light app (Quorum, the crew's memory): a sidebar, a list of notes, two flagged deadlines."""
    im = Image.new("RGB", (w, h), (247, 246, 242))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 420, h], fill=(236, 234, 228))
    f, fb = font("segoeui.ttf", 34), font("seguisb.ttf", 40)
    d.text((40, 40), "Quorum", font=fb, fill=(40, 44, 52))
    for k, t in enumerate(("Inbox", "Shots", "Deadlines", "Reviews", "Crew")):
        d.text((40, 140 + k * 70), t, font=f, fill=(70, 74, 82))
    d.rounded_rectangle([20, 270, 400, 330], 10, outline=(201, 160, 74), width=3)
    for k in range(9):
        y = 60 + k * 150
        d.rounded_rectangle([480, y, w - 60, y + 120], 14, fill=(255, 255, 255), outline=(225, 222, 214), width=2)
        d.rectangle([510, y + 30, 1200 + (k % 3) * 200, y + 52], fill=(70, 74, 82))
        d.rectangle([510, y + 72, 1700 - (k % 4) * 180, y + 88], fill=(180, 182, 186))
        if k in (1, 4):
            d.rounded_rectangle([w - 420, y + 34, w - 100, y + 86], 26, fill=(196, 72, 56))
            d.text((w - 380, y + 38), "in dispute", font=f, fill=(255, 255, 255))
    im.save(path)


def shop_16x10():
    """The shop PC's own 16:10 screens (1920x1200), rendered from the look-dev page by render_shop_screens.js."""
    js = os.path.join(HERE, "render_shop_screens.js")
    try:
        subprocess.run(["node", js], check=True)
        return True
    except (OSError, subprocess.CalledProcessError) as e:
        print("16:10 shop screens not rendered (node/Chrome?):", e, "- desk.py falls back to the 16:9 frames")
        return False


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    shop_16x10()
    shop_tuesday()                                            # 16:9 fallback, used only without the 16:10 render
    asleep(1920, 1200, "br", path=os.path.join(OUT, "shop-asleep.png"))
    lisbon_main(os.path.join(OUT, "lisbon-main-placeholder.png"))
    lisbon_second(os.path.join(OUT, "lisbon-second-placeholder.png"))
    lisbon_laptop(os.path.join(OUT, "lisbon-laptop-placeholder.png"))
    asleep(2560, 1440, "br", path=os.path.join(OUT, "lisbon-main-asleep.png"), frac=0.08)
    Image.new("RGB", (2560, 1440), (0, 0, 0)).save(os.path.join(OUT, "lisbon-black.png"))
    print("wrote", sorted(os.listdir(OUT)))
