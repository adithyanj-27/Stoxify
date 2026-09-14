import os
import numpy as np
from PIL import Image, ImageDraw

D = r"C:\Users\adith\Documents\Stoxify\_glitch_frames"
files = sorted(f for f in os.listdir(D) if f.startswith("f_") and f.endswith(".png"))
gray = [np.asarray(Image.open(os.path.join(D, f)).convert("L")).astype(np.int16) for f in files]
color = [np.asarray(Image.open(os.path.join(D, f)).convert("RGB")) for f in files]
H, W = gray[0].shape
FPS = 12.55
N = len(gray)

REG = {
    "top_status(y0-90)":        (0, 90),
    "control_static(y560-760)": (560, 760),
    "control_static2(y820-1000)": (820, 1000),
    "calc_card(y1150-1300)":    (1150, 1300),
    "text_line(y1196-1228)":    (1196, 1228),
    "green_btn(y1360-1440)":    (1360, 1440),
    "bottom(y1440-1608)":       (1440, 1608),
}

print("== bright-pixel count per region (text-ink proxy), every frame ==")
hdr = "frm   t   " + "".join(f"{k.split('(')[0][:9]:>11}" for k in REG)
print(hdr)
series = {k: [] for k in REG}
for i in range(N):
    row = f"{i:4d} {i/FPS:5.2f} "
    for k, (a, b) in REG.items():
        ink = int((gray[i][a:b] > 140).sum())
        series[k].append(ink)
        row += f"{ink:>11d}"
    if i % 1 == 0:
        print(row)

print("\n== flicker detection: ink count deviating >35% from region median ==")
for k, vals in series.items():
    v = np.array(vals, float)
    med = np.median(v)
    if med < 200:
        print(f"  {k}: median ink {med:.0f} (too little text to judge) - skipped")
        continue
    bad = np.where(np.abs(v - med) / med > 0.35)[0]
    if len(bad) == 0:
        print(f"  {k}: stable (median {med:.0f}, max dev {100*abs(v-med).max()/med:.0f}%)")
    else:
        print(f"  {k}: median {med:.0f} | {len(bad)} deviating frames -> " +
              ", ".join(f"f{i}({int(v[i])})" for i in bad[:25]))

print("\n== local churn: mean abs diff, churning band vs static control ==")
for i in range(1, N):
    d_txt = float(np.abs(gray[i][1196:1228] - gray[i - 1][1196:1228]).mean())
    d_ctl = float(np.abs(gray[i][560:760] - gray[i - 1][560:760]).mean())
    if d_txt > 8:
        print(f"  f{i:3d}->{i+1:3d} t={i/FPS:5.2f}s  textline={d_txt:6.2f}   control={d_ctl:5.2f}   ratio={d_txt/max(d_ctl,0.01):5.1f}x")

# horizontal profile of the churn to find WHICH x-range (left label vs right value)
print("\n== horizontal profile of change at f88->f89 in y1196-1228 ==")
d = np.abs(gray[89][1196:1228] - gray[88][1196:1228]).mean(axis=0)
for seg in range(0, W, 60):
    print(f"  x={seg:3d}-{seg+59:3d}  change={d[seg:seg+60].mean():6.2f}")

# save the blinking line magnified across the window for identification
idx = list(range(80, 96))
tl, tb = 1180, 1245
th = int(3.0 * (tb - tl))
sheet = Image.new("RGB", (W * 3, len(idx) * (th + 14)), (25, 25, 30))
dr = ImageDraw.Draw(sheet)
for k, i in enumerate(idx):
    tile = Image.fromarray(color[i][tl:tb]).resize((W * 3, th), Image.LANCZOS)
    sheet.paste(tile, (0, k * (th + 14)))
    dr.text((6, k * (th + 14) + th + 1), f"f{i} t={i/FPS:.2f}s", fill=(255, 220, 120))
p = os.path.join(D, "blink_line_stack.png")
sheet.save(p)
print("\nsaved", p, sheet.size, f"(crop y{tl}-{tb}, {len(idx)} frames stacked)")
