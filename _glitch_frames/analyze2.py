import os
import numpy as np
from PIL import Image, ImageDraw

D = r"C:\Users\adith\Documents\Stoxify\_glitch_frames"
files = sorted(f for f in os.listdir(D) if f.startswith("f_") and f.endswith(".png"))

gray, color = [], []
for f in files:
    im = Image.open(os.path.join(D, f)).convert("RGB")
    color.append(np.asarray(im))
    gray.append(np.asarray(im.convert("L")).astype(np.int16))

H, W = gray[0].shape
N = len(gray)
FPS = 12.55

# ---- band-wise change: which vertical region of the screen is changing? ----
NB = 16
bands = [(int(H * i / NB), int(H * (i + 1) / NB)) for i in range(NB)]
rows = []
for i in range(1, N):
    d = np.abs(gray[i] - gray[i - 1])
    bv = [float(d[a:b].mean()) for a, b in bands]
    rows.append((i, bv))

print("== per frame-pair: total change + the two hottest bands ==")
for i, bv in sorted(rows, key=lambda r: -sum(r[1]))[:16]:
    top = sorted(range(NB), key=lambda k: -bv[k])[:2]
    desc = ", ".join(f"band{k}(y{bands[k][0]}-{bands[k][1]})={bv[k]:.1f}" for k in top)
    print(f"  f{i:3d}->{i+1:3d} t={i/FPS:5.2f}s sum={sum(bv):6.1f}  {desc}")

print("\n== change confined to the lower half (y>804) over time ==")
for i, bv in rows:
    low = sum(bv[8:])
    up = sum(bv[:8])
    if low > 60 and low > up * 1.5:
        print(f"  f{i:3d}->{i+1:3d} t={i/FPS:5.2f}s  lower={low:6.1f} upper={up:6.1f}")

# ---- blue artifact detector (bottom half) ----
print("\n== blue-ish pixel counts in lower half (strong blue, not part of dark UI) ==")
for i in range(N):
    c = color[i].astype(np.int16)
    R, G, B = c[:, :, 0], c[:, :, 1], c[:, :, 2]
    m = (B > 150) & (B - R > 60) & (B - G > 30) & (G > 80)
    m[: int(H * 0.5), :] = False
    n = int(m.sum())
    if n > 1500:
        ys, xs = np.where(m)
        print(f"  f{i:3d} t={i/FPS:5.2f}s  blue px={n:6d}  y={ys.min()}-{ys.max()} x={xs.min()}-{xs.max()}")


def strip(idx_list, crop_top_frac, name, tile_w=300, cols=4):
    ct = int(H * crop_top_frac)
    crop_h = H - ct
    tw = tile_w
    th = int(tile_w * crop_h / W)
    rowsn = (len(idx_list) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rowsn * (th + 15)), (25, 25, 30))
    d = ImageDraw.Draw(sheet)
    for k, idx in enumerate(idx_list):
        tile = Image.fromarray(color[idx][ct:]).resize((tw, th))
        x, y = (k % cols) * tw, (k // cols) * (th + 15)
        sheet.paste(tile, (x, y))
        d.text((x + 3, y + th + 2), f"f{idx} t={idx/FPS:.2f}s", fill=(240, 240, 240))
    p = os.path.join(D, name)
    sheet.save(p)
    print(f"saved {p}  {sheet.size}  ({len(idx_list)} tiles, crop y>={ct})")


strip(list(range(54, 74, 2)), 0.45, "strip_blue_moment.png")
strip(list(range(98, 114)), 0.45, "strip_big_motion.png")
strip(list(range(0, 150, 4)), 0.45, "strip_bottom_overview.png", tile_w=200, cols=5)
