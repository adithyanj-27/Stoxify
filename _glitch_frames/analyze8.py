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

BLANK = [21, 22, 25, 26, 27, 29, 31, 35, 36, 38, 43, 44, 48, 54, 55, 56, 57, 71, 73, 87, 88, 90, 91, 93, 97]
BLANK = [i for i in BLANK if i < N]

# ---- 1. blue-ish (tap highlight / hover ring) detection per frame ----
print("== blue-ish px in the chips row (y1055-1100) and in the whole drawer body (y850-1300) ==")
blue_rows, blue_body = [], []
for i in range(N):
    c = color[i].astype(np.int16)
    R, G, B = c[:, :, 0], c[:, :, 1], c[:, :, 2]
    blue = (B - R > 25) & (B > 60)
    r = int(blue[1055:1100].sum())
    b = int(blue[850:1300].sum())
    blue_rows.append(r); blue_body.append(b)

base_r = int(np.median([v for i, v in enumerate(blue_rows) if i not in set(BLANK)]))
base_b = int(np.median([v for i, v in enumerate(blue_body) if i not in set(BLANK)]))
print(f"  baseline (non-blank frames): chips-row={base_r}, body={base_b}")
hot = [i for i in range(N) if blue_rows[i] > base_r * 1.6 + 30 or blue_body[i] > base_b * 1.6 + 60]
print(f"  hover/highlight frames ({len(hot)}): {hot}")

# ---- 2. correlation: tap-ish frames vs blank frames ----
print("\n== correlation ==")
prev_hot = set()
for h in hot:
    for d in (0, 1, 2):
        prev_hot.add(h + d)
both = sorted(prev_hot & set(BLANK))
print(f"  blank frames that are within 0-2 frames after a highlight change: {len(both)}/{len(BLANK)} -> {both}")

# ---- 3. do the chip boxes / card borders survive on blank frames? ----
print("\n== pixels by luminance class: chips row (y1070-1096) ==")
def counts(i, a, b):
    g = gray[i][a:b]
    return (int((g >= 90).sum()), int(((g >= 25) & (g < 85)).sum()), round(float(g.mean()), 2))
grp = [i for i in range(N) if i not in set(BLANK)]
print(f"  normal frames : text(>=90)={np.mean([counts(i,1070,1096)[0] for i in grp]):7.0f}  box(25-85)={np.mean([counts(i,1070,1096)[1] for i in grp]):7.0f}  mean={np.mean([counts(i,1070,1096)[2] for i in grp]):6.2f}")
print(f"  blank frames  : text(>=90)={np.mean([counts(i,1070,1096)[0] for i in BLANK]):7.0f}  box(25-85)={np.mean([counts(i,1070,1096)[1] for i in BLANK]):7.0f}  mean={np.mean([counts(i,1070,1096)[2] for i in BLANK]):6.2f}")

print("\n== pixels by luminance class: margin row (y1201-1226) ==")
print(f"  normal frames : text(>=90)={np.mean([counts(i,1201,1226)[0] for i in grp]):7.0f}  box(25-85)={np.mean([counts(i,1201,1226)[1] for i in grp]):7.0f}  mean={np.mean([counts(i,1201,1226)[2] for i in grp]):6.2f}")
print(f"  blank frames  : text(>=90)={np.mean([counts(i,1201,1226)[0] for i in BLANK]):7.0f}  box(25-85)={np.mean([counts(i,1201,1226)[1] for i in BLANK]):7.0f}  mean={np.mean([counts(i,1201,1226)[2] for i in BLANK]):6.2f}")

# ---- 4. does the stable region above (product/variety) ever drop? ----
print("\n== ink in the stable upper drawer region (y560-830) across all frames ==")
ink = [(i, int((gray[i][560:830] > 140).sum())) for i in range(N)]
vals = np.array([v for _, v in ink], float)
med = np.median(vals)
dev = [(i, v) for i, v in ink if abs(v - med) / med > 0.2]
print(f"  median={med:.0f}  frames deviating >20%: {dev if dev else 'NONE'}")

# ---- 5. per-frame ink of each blanking row, to see the on/off pattern ----
print("\n== on/off pattern of the 5 blanking rows (1=text present, 0=blank) ==")
rows = [(900, 916), (979, 1003), (1075, 1090), (1201, 1225), (1249, 1267)]
pat = []
for a, b in rows:
    v = [int((gray[i][a:b + 1] > 140).sum()) for i in range(N)]
    m = np.median([v[i] for i in grp])
    pat.append([1 if v[i] > m * 0.3 else 0 for i in range(N)])
for k, (a, b) in enumerate(rows, 1):
    print(f"  row{k} y{a}-{b}: " + "".join(str(x) for x in pat[k - 1]))
print("  frame idx    : " + "".join(str(i % 10) for i in range(N)))
