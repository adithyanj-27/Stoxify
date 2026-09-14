import os
import numpy as np
from PIL import Image, ImageDraw

D = r"C:\Users\adith\Documents\Stoxify\_glitch_frames"
files = sorted(f for f in os.listdir(D) if f.startswith("f_") and f.endswith(".png"))
FPS = 12.55

gray = []
color = []
for f in files:
    im = Image.open(os.path.join(D, f)).convert("RGB")
    color.append(np.asarray(im))
    gray.append(np.asarray(im.convert("L")).astype(np.int16))

COLOR = color
H, W = gray[0].shape
N = len(gray)
print(f"frames={N} size={W}x{H} fps={FPS}")

half = [np.asarray(Image.fromarray(c).resize((W // 2, H // 2))).astype(np.int16) for c in COLOR]

# ---- 1. global motion per frame pair ----
motion = []
for i in range(1, N):
    motion.append(float(np.abs(half[i] - half[i - 1]).mean()))

# ---- 2. green CTA block tracking (bottom half) ----
# Groww green buy button: solid #10b981-ish fill
def green_block(idx):
    c = COLOR[idx].astype(np.int16)
    R, G, B = c[:, :, 0], c[:, :, 1], c[:, :, 2]
    mask = (G > 120) & (G - R > 45) & (G - B > 25)
    mask[: int(H * 0.5), :] = False           # bottom half only
    rows = np.where(mask.sum(axis=1) > W * 0.45)[0]   # wide solid band = the button
    if len(rows) == 0:
        return None
    return int(rows.min()), int(rows.max()), int(mask.sum())

blocks = [green_block(i) for i in range(N)]

# ---- 3. vertical displacement of the bottom strip (cross-correlation) ----
STRIP_TOP = int(H * 0.52)
max_shift = 140

def shift_cost(a, b, dy):
    h = a.shape[0]
    if dy > 0:
        A, B = a[dy:], b[: h - dy]
    elif dy < 0:
        A, B = a[: h + dy], b[-dy:]
    else:
        A, B = a, b
    return float(np.abs(A - B).mean())

shifts = []
for i in range(1, N):
    a = gray[i - 1][STRIP_TOP:].astype(np.float32)
    b = gray[i][STRIP_TOP:].astype(np.float32)
    costs = [(shift_cost(a, b, dy), dy) for dy in range(-max_shift, max_shift + 1)]
    best_cost, best_dy = min(costs)
    zero_cost = shift_cost(a, b, 0)
    shifts.append((best_dy, zero_cost, best_cost))

# ---- report ----
print("\n== top motion events ==")
for i in sorted(np.argsort(motion)[::-1][:12]):
    print(f"  {i:3d}->{i+1:3d}  t={i/FPS:5.2f}s  motion={motion[i]:6.2f}")

print("\n== green CTA band (top,bottom,area) — only frames where it exists ==")
prev = None
for i, b in enumerate(blocks):
    if b is None:
        if prev is not None:
            print(f"  f{i:3d} t={i/FPS:5.2f}s  CTA GONE")
            prev = None
        continue
    if prev is not None and abs(b[0] - prev[0]) >= 3:
        print(f"  f{i:3d} t={i/FPS:5.2f}s  CTA top {prev[0]} -> {b[0]}  (dy={b[0]-prev[0]:+d})  h={b[1]-b[0]}")
    prev = b

tops = [b[0] for b in blocks if b]
if tops:
    print(f"  CTA top row range over whole clip: min={min(tops)} max={max(tops)} spread={max(tops)-min(tops)}")

print("\n== bottom-strip vertical displacement (|dy|>=3 px) ==")
for i, (dy, z, bc) in enumerate(shifts):
    if abs(dy) >= 3:
        print(f"  {i:3d}->{i+1:3d}  t={i/FPS:5.2f}s  dy={dy:+4d}px  cost@0={z:6.2f} cost@best={bc:6.2f}")

nz = sum(1 for s in shifts if abs(s[0]) >= 3)
print(f"\n  frames with >=3px bottom-strip displacement: {nz}/{len(shifts)}")

# ---- 4. contact sheet, every 8th frame ----
step = 8
sel = list(range(0, N, step))
tw, th = 216, int(216 * H / W)
cols, rows = 3, (len(sel) + 2) // 3
sheet = Image.new("RGB", (cols * tw, rows * (th + 16)), (20, 20, 24))
d = ImageDraw.Draw(sheet)
for k, idx in enumerate(sel):
    tile = Image.fromarray(COLOR[idx]).resize((tw, th))
    x, y = (k % cols) * tw, (k // cols) * (th + 16)
    sheet.paste(tile, (x, y))
    d.text((x + 3, y + th + 2), f"f{idx}  t={idx/FPS:.1f}s", fill=(230, 230, 230))
sheet.save(os.path.join(D, "contact_sheet.png"))
print(f"\ncontact sheet: {len(sel)} tiles -> {os.path.join(D, 'contact_sheet.png')} ({sheet.size})")
