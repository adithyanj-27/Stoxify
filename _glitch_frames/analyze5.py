import os
import numpy as np
from PIL import Image

D = r"C:\Users\adith\Documents\Stoxify\_glitch_frames"
files = sorted(f for f in os.listdir(D) if f.startswith("f_") and f.endswith(".png"))
color = [np.asarray(Image.open(os.path.join(D, f)).convert("RGB")) for f in files]
gray = [np.asarray(Image.open(os.path.join(D, f)).convert("L")).astype(np.int16) for f in files]
H, W = gray[0].shape
FPS = 12.55
N = len(gray)

ink = np.array([[int((g > 140).sum()) for g in [gray[i]] for _ in [0]] for i in range(N)]).ravel()
print("ink counts done")

# --- per-row ink over time, to find the exact blanking rows ---
hits = []
for i in range(N):
    row = gray[i]
    ink_rows = (row > 140).sum(axis=1)
    hits.append(ink_rows)
HITS = np.array(hits, dtype=np.int32)      # (N, H)

med = np.median(HITS, axis=0)
bad = np.where(np.abs(HITS - med) > 0)[0]
# frames whose whole-frame ink is much lower than the median frame
tot = HITS.sum(axis=1)
mtot = np.median(tot)
low = np.where(tot < mtot * 0.75)[0]
print(f"\nmedian bright px/frame = {mtot:.0f}")
print(f"frames with >25% of all bright px missing: {len(low)} -> {list(low)}")

print("\n== per-frame blanked-row ranges (rows where >80% of median ink vanished) ==")
for i in low:
    r = med > 6
    lost = r & (HITS[i] < np.maximum(1, med * 0.2))
    if lost.sum() == 0:
        print(f"  f{i:3d} t={i/FPS:5.2f}s  (no contiguous rows flagged)")
        continue
    idx = np.where(lost)[0]
    # group into contiguous runs
    runs, start = [], idx[0]
    for a, b in zip(idx, idx[1:]):
        if b != a + 1:
            runs.append((start, a)); start = b
    runs.append((start, idx[-1]))
    runs = [(a, b) for a, b in runs if b - a >= 2]
    print(f"  f{i:3d} t={i/FPS:5.2f}s  runs: " + ", ".join(f"y{a}-{b}" for a, b in runs))

# --- is the card background still there on blank frames? sample known rows ---
print("\n== mean luminance of sample bands: normal vs blank frames ==")
sample_rows = [(600, 640), (900, 940), (1160, 1200), (1240, 1280), (1300, 1340), (1380, 1420)]
ok = int(low[3]) if len(low) > 3 else 0
for a, b in sample_rows:
    n = [float(gray[i][a:b].mean()) for i in range(N) if i not in set(low)]
    bl = [float(gray[i][a:b].mean()) for i in low]
    print(f"  y{a}-{b}: normal {np.mean(n):6.2f}   blank-frames {np.mean(bl):6.2f}   delta {np.mean(bl)-np.mean(n):+6.2f}")

# --- green CTA button presence per frame ---
print("\n== green CTA pixels (y1340-1450) per frame: min/median/max ==")
gcount = []
for i in range(N):
    c = color[i].astype(np.int16)
    R, G, B = c[:, :, 0], c[:, :, 1], c[:, :, 2]
    m = (G > 110) & (G - R > 40) & (G - B > 20)
    m[:1340, :] = False
    m[1450:, :] = False
    gcount.append(int(m.sum()))
g = np.array(gcount)
print(f"  min={g.min()}  median={np.median(g):.0f}  max={g.max()}")
print(f"  frames with <70% of median green: {list(np.where(g < np.median(g)*0.7)[0])}")

# --- tap detection: value changes in the input / margin rows ---
print("\n== big content changes in y1000-1350 (value edits = taps) ==")
for i in range(1, N):
    d = float(np.abs(gray[i][1000:1350] - gray[i - 1][1000:1350]).mean())
    if d > 12:
        print(f"  f{i:3d}->{i+1:3d} t={i/FPS:5.2f}s  change={d:6.2f}")
