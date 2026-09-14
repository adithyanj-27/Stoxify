import os
import numpy as np
from PIL import Image, ImageDraw

D = r"C:\Users\adith\Documents\Stoxify\_glitch_frames"
files = sorted(f for f in os.listdir(D) if f.startswith("f_") and f.endswith(".png"))
color = [np.asarray(Image.open(os.path.join(D, f)).convert("RGB")) for f in files]
gray = [np.asarray(Image.open(os.path.join(D, f)).convert("L")).astype(np.int16) for f in files]
H, W = gray[0].shape
FPS = 12.55

CT, CB = 1120, 1440            # the churning band (chips + margin rows)
print(f"crop rows {CT}-{CB} of {H}")


def strip(idx_list, crop=(CT, CB), name="s.png", tile_w=360, cols=4, label=True):
    a, b = crop
    ch = b - a
    th = int(tile_w * ch / W)
    rowsn = (len(idx_list) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, rowsn * (th + 15)), (25, 25, 30))
    d = ImageDraw.Draw(sheet)
    for k, idx in enumerate(idx_list):
        tile = Image.fromarray(color[idx][a:b]).resize((tile_w, th), Image.LANCZOS)
        x, y = (k % cols) * tile_w, (k // cols) * (th + 15)
        sheet.paste(tile, (x, y))
        if label:
            d.text((x + 3, y + th + 2), f"f{idx} t={idx/FPS:.2f}s", fill=(240, 240, 240))
    p = os.path.join(D, name)
    sheet.save(p)
    print("saved", p, sheet.size)


# the suspected glitch window
strip(list(range(78, 98, 2)), name="tight_glitch_window.png", cols=4)
# a normal tap for comparison (qty 10 -> 5 early in the clip)
strip(list(range(6, 20, 2)), name="tight_early_tap.png", cols=4)
# every frame across the churn, extra magnification
strip(list(range(86, 97)), crop=(1150, 1400), name="tight_glitch_frames.png", tile_w=420, cols=3)

# numeric trace of the churn band
print("\n== per-frame change inside crop band ==")
for i in range(1, len(gray)):
    d = float(np.abs(gray[i][CT:CB] - gray[i - 1][CT:CB]).mean())
    if d > 4:
        print(f"  f{i:3d}->{i+1:3d} t={i/FPS:5.2f}s  band12band change={d:6.2f}")

# exact row profile of the churn at its peak, to locate the element
peak = 89
prof = np.abs(gray[peak][CT:CB] - gray[peak - 1][CT:CB]).mean(axis=1)
print(f"\n== row profile of change at f{peak-1}->f{peak} (top 8 rows) ==")
for r in np.argsort(prof)[::-1][:8]:
    print(f"  y={CT + int(r)}  change={prof[r]:.1f}")
