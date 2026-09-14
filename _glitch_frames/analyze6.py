import os
import numpy as np
from PIL import Image, ImageDraw

D = r"C:\Users\adith\Documents\Stoxify\_glitch_frames"
files = sorted(f for f in os.listdir(D) if f.startswith("f_") and f.endswith(".png"))
color = [np.asarray(Image.open(os.path.join(D, f)).convert("RGB")) for f in files]
gray = [np.asarray(Image.open(os.path.join(D, f)).convert("L")).astype(np.int16) for f in files]
H, W = gray[0].shape
FPS = 12.55
N = len(gray)

BLANK = [21, 22, 25, 26, 27, 29, 31, 35, 36, 38, 43, 44, 48, 54, 55, 56, 57, 71, 73, 87, 88, 90, 91, 93, 97]
BLANK = [i for i in BLANK if i < N]

HITS = np.array([(g > 140).sum(axis=1) for g in gray], dtype=np.int32)
med = np.median(HITS, axis=0)
blankmed = np.median(HITS[BLANK], axis=0)

runs = []
inrun = False
for y in range(H):
    if med[y] >= 6 and not inrun:
        start = y; inrun = True
    elif med[y] < 6 and inrun:
        runs.append((start, y - 1)); inrun = False
if inrun:
    runs.append((start, H - 1))

print(f"{'rows':>14} {'h':>3} {'ink_normal':>11} {'ink_blank':>10} {'lost%':>7}  verdict")
for a, b in runs:
    if b - a < 2:
        continue
    nrm = float(med[a:b + 1].sum())
    blk = float(blankmed[a:b + 1].sum())
    lost = 100.0 * (1 - blk / max(nrm, 1))
    v = "BLANKS" if lost > 70 else ("partial" if lost > 25 else "stable")
    print(f"  y{a:4d}-{b:4d} {b-a+1:3d} {nrm:11.0f} {blk:10.0f} {lost:6.1f}%  {v}")

# annotate a normal frame with the blanking runs
annot = color[20].copy()
d = ImageDraw.Draw(annot)
n = 0
for a, b in runs:
    if b - a < 2:
        continue
    nrm = float(med[a:b + 1].sum()); blk = float(blankmed[a:b + 1].sum())
    if nrm > 0 and 100 * (1 - blk / nrm) > 70:
        n += 1
        d.rectangle([0, a - 4, W - 1, b + 4], outline=(255, 0, 0), width=3)
        d.text((6, max(0, a - 18)), f"#{n}  y{a}-{b}", fill=(255, 80, 80))
annot.save(os.path.join(D, "annotated_normal_f20.png"))
blank = color[21].copy()
Image.fromarray(blank).save(os.path.join(D, "blank_f21.png"))
print(f"\nsaved annotated_normal_f20.png and blank_f21.png ; blanking runs = {n}")

# side-by-side of a blanking run: normal vs blank, magnified
a, b = 960, 1300
tiles = []
for idx in (20, 21, 25, 22):
    t = Image.fromarray(color[idx][a:b]).resize((W, (b - a)))
    tiles.append((idx, t))
sheet = Image.new("RGB", (2 * W, 2 * (b - a) + 40), (30, 30, 34))
dr = ImageDraw.Draw(sheet)
for k, (idx, t) in enumerate(tiles):
    x, y = (k % 2) * W, (k // 2) * ((b - a) + 20)
    sheet.paste(t, (x, y))
    dr.text((x + 6, y + (b - a) + 2), f"f{idx}  t={idx/FPS:.2f}s", fill=(255, 230, 120))
sheet.save(os.path.join(D, "sbs_normal_vs_blank.png"))
print("saved sbs_normal_vs_blank.png", sheet.size)
