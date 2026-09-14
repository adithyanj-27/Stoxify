import numpy as np
from PIL import Image, ImageDraw

D = r"C:\Users\adith\Documents\Stoxify\_glitch_frames"
rows = [(900, 916), (979, 1003), (1075, 1090), (1201, 1225), (1249, 1267)]
TOP, BOT, SC = 830, 1470, 1.4

for idx, tag in ((20, "normal"), (21, "glitch")):
    c = np.asarray(Image.open(D + "\\f_%04d.png" % idx).convert("RGB"))
    H, W = c.shape[:2]
    im = Image.fromarray(c[TOP:BOT].copy()).resize((int(W * SC), int((BOT - TOP) * SC)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for n, (a, b) in enumerate(rows, 1):
        y0 = int((a - TOP) * SC) - 3
        y1 = int((b - TOP) * SC) + 3
        d.rectangle([0, y0, im.size[0] - 1, y1], outline=(255, 40, 40), width=3)
        d.text((8, max(0, y0 - 16)), "#" + str(n), fill=(255, 90, 90))
    p = D + "\\id_f%d_%s.png" % (idx, tag)
    im.save(p)
    print("saved", p, im.size)
