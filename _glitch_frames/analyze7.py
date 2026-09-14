import os
import numpy as np
from PIL import Image, ImageDraw

D = r"C:\Users\adith\Documents\Stoxify\_glitch_frames"
files = sorted(f for f in os.listdir(D) if f.startswith("f_") and f.endswith(".png"))
color = [np.asarray(Image.open(os.path.join(D, f)).convert("RGB")) for f in files]
H, W = color[0].shape[:2]
FPS = 12.55

BLANK_ROWS = [(900, 916), (979, 1003), (1075, 1090), (1201, 1225), (1249, 1267)]
TOP, BOT = 830, 1470
SC = 1.5


def panel(idx, mark=False):
    im = Image.fromarray(color[idx][TOP:BOT].copy())
    im = im.resize((int(W * SC), int((BOT - TOP) * SC)), Image.LANCZOS)
    if mark:
        d = ImageDraw.Draw(im)
        for k, (a, b) in enumerate(BLANK_ROWS, 1):
            y0 = int((a - TOP) * SC) - 3
            y1 = int((b - TOP) * SC) + 3
            d.rectangle([0, y0, im.size[0] - 1, y1], outline=(255, 40, 40), width=3)
            d.text((8, max(0, y0 - 15)), f"#{k}", fill=(255, 90, 90))
    return im


p1 = panel(20, mark=True)
p2 = panel(21, mark=True)
sheet = Image.new("RGB", (p1.size[0], p1.size[1] * 2 + 60), (28, 28, 32))
d = ImageDraw.Draw(sheet)
sheet.paste(p1, (0, 0))
d.text((8, p1.size[1] + 4), "TOP = f20 (t=1.59s, normal)", fill=(140, 255, 160))
sheet.paste(p2, (0, p1.size[1] + 30))
d.text((8, p1.size[1] * 2 + 34), "BOTTOM = f21 (t=1.67s, glitch frame)", fill=(255, 160, 160))
sheet.save(os.path.join(D, "identify_blank_rows.png"))
print("saved identify_blank_rows.png", sheet.size)

# also a taller context crop of both frames, unmarked
ctx_top, ctx_bot = 520, 1470
c1 = Image.fromarray(color[20][ctx_top:ctx_bot]).resize((int(W * 1.2), int((ctx_bot - ctx_top) * 1.2)), Image.LANCZOS)
c1.save(os.path.join(D, "context_f20.png"))
print("saved context_f20.png", c1.size)
