# Mobile buy drawer — text flicker on quantity tap

**Reported:** "in mobile view during the stock buy process, when I click +10 / +25 etc, that bottom portion glitches."

**Source video:** `C:\Users\adith\Documents\glitch.mp4` (720×1608, 11.95 s, 12.55 fps, ~150 frames).
Frame-by-frame analysis artefacts: `_glitch_frames/` (extracted PNGs, scripts, measurement output).

---

## Method

No device access, so the video was decoded and measured rather than eyeballed:

1. All 150 frames extracted with ffmpeg as PNGs.
2. Per-frame frame-to-frame difference, split into 16 horizontal bands.
3. Vertical displacement of the bottom strip by cross-correlation (is anything *moving*?).
4. Bright-pixel "ink" counting per row to detect whether text is actually present.
5. Comparison against a control region 40 px away that must not change.

## What the recording shows

The screen is the **mobile slide-up trading drawer** (`#mobileTradingDrawerOverlay` > `.mobile-drawer-card`),
confirmed by elements unique to it — the `Quantity` label with the `"N Delivery shares owned"` line
(from `#drawerHoldingQty` via `updatePageAvailableHolding`) and quick chips reading `1 5 10 25 50`
(the post-relabel labels), and the green `BUY <SYMBOL>` CTA from `#drawerOrderExecuteBtn`.

### Findings

| Measurement | Result |
|---|---|
| Green CTA top row | **identical on all 150 frames** (y=1374, spread 0 px) |
| Bottom-strip vertical displacement ≥3 px | **0 of 149 frame pairs** |
| Text rows that blank | y900-916, y979-1003, y1075-1090, y1201-1225, y1249-1267 |
| Frames that blank (whole-frame ink −25 %) | 19: f21, 22, 25, 26, 27, 29, 31, 35, 36, 38, 43, 44, 48, 54, 55, 56, 57, 71, 73 |
| Additional frames blanking the margin row only | f87, 88, 90, 91, 93, 97 |
| Ink in the control region y560-830 | **never deviates more than 20 %** — the upper form never flickers |

So **nothing shifts and nothing scrolls.** On the blanking frames the text simply is not painted:

* y900-916 → `Quantity` + `"50 Delivery shares owned"`
* y979-1003 → the stepper value (`− 25 +`)
* y1075-1090 → the quick chips (`1 5 10 25 50`)
* y1201-1225 → `Required Margin  ₹12,200.00`
* y1249-1267 → `Available Balance  ₹75,493.75`

Measured ink inside the margin row: 2819 bright px normally → **0** on blank frames. Chip-row text: 680 → **0**,
while the chip **borders and card backgrounds stay** (border-class pixels 1364 → 1122 on chips; card mean
luminance of the green button region unchanged at 111.58). That is the signature of a **composited layer being
re-rasterised: backgrounds survive, text is dropped for one frame**.

### Correlation with taps

Frames where a chip's hover/selection ring brightens (i.e. a tap happened):
f20, 26, 27, 34, 35, 36, 43, 44, 53, 61-63, 68-70, 86-88, 96-98.

**17 of the 25 blanking frames occur 0–2 frames after one of those taps.** Bursts match rapid chip tapping
(e.g. three blanks inside 250 ms). The blanking is scoped to the region `recalcPageMargin()` rewrites —
including text it never touches (`Available Balance`, the chips, `shares owned`) — which is consistent with
invalidation of whole raster tiles in that region, not with a layout or logic bug.

## Root cause

Text that is rewritten inside a **transform-composited, scrolling layer** gets dropped for a single frame
during re-rasterisation (Android Chrome). The drawer had every trigger in place at once:

1. `.mobile-drawer-overlay.active .mobile-drawer-card { transform: translateY(0) }` — a *settled* `translateY(0)`
   still keeps the sheet on its own compositor layer permanently.
2. `will-change: transform` + `backface-visibility: hidden` (added in the previous attempt) — forces that layer
   to be retained. **This likely made the flicker more likely, not less.**
3. `-webkit-overflow-scrolling: touch` — legacy scroller promotion.
4. `backdrop-filter: blur(8px)` on the parent overlay — forces backdrop re-compositing on child repaints
   (already removed for mobile in the previous attempt).
5. `recalcPageMargin()` used `innerText` on ~20 nodes per tap — every assignment swaps a text node and
   re-invalidates the element, including values that had not changed.

The previous attempt only addressed (4) plus a viewport-height instability, which is why the symptom survived.

## Changes made

`static/style.css`, `public/style.css`
* Removed `will-change: transform` + `backface-visibility` from `.mobile-drawer-card`.
* Removed `-webkit-overflow-scrolling: touch` from `.mobile-drawer-card`.
* Added `.mobile-drawer-card.anim-done` → `transform: none`, so once the slide-in finishes the sheet is no
  longer a permanent composited layer and text rasterises on the normal path.
* (Kept from the previous attempt: mobile `backdrop-filter: none`, `100svh` height.)

`static/app.js`, `public/app.js`
* `openMobileTradeDrawer()` — removes any stale `.anim-done`, then adds it on `transitionend` (400 ms fallback)
  so the slide-in still animates.
* `closeMobileTradeDrawer()` — clears `.anim-done` before `.active` so the slide-down still animates.
* New `setTextIfChanged(el, txt)` (uses `textContent`) and `recalcPageMargin()` rewritten to use it, with
  `className` writes guarded — a tap now dirties only the rows that actually changed.

Both `static/` and `public/` are byte-identical; `node --check` passes on both `app.js` files.

## How to verify

Reload on the phone (the service worker is network-first for `style.css`/`app.js`, so no cache bump is needed),
open a stock, tap the qty chips rapidly and watch the `Required Margin` / `Available Balance` / chip rows.
They should stay solid. If any flicker survives, the next lever is to take the scroll container off the animated
element (move `overflow-y: auto` to `.mobile-drawer-body` and let the sheet itself only transform), and to narrow
`transition: all` on `.qty-chip` / `.seg-btn` to specific properties.

## Not changed on purpose

* `#tradeModalOverlay` (`.trade-modal-card`) — uses a keyframe animation that ends without a lingering
  `transform`, so it is not affected the same way. Its chips (`+5 +10 +25 +50 +100`, `setQuickQty`) add to the
  quantity, while the drawer chips set it; the two conventions are still inconsistent.
* Wallet transactions view keeps `100dvh` — it is a full-screen panel, where `dvh` is correct.
