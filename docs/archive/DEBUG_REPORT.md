# Stoxify — Debug Report

**Scope:** full application (FastAPI backend + vanilla-JS SPA + PWA service worker)
**Method:** manual audit of every source file, then reproduction with standalone probes *before* any fix was applied. Every defect below was observed failing (see §7), not inferred.

---

## 1. Summary

| # | Defect | Impact | Status |
|---|--------|--------|--------|
| C1 | Buy-side charges recorded but never debited | Every BUY overstates cash by the charge amount | Fixed |
| C2 | `restore` + `cancel` duplicated blocked margin | Repeats → free money | Fixed |
| C3 | Resting LIMIT / STOP orders were never triggered | Pending orders could never fill | Fixed |
| C4 | Stale cloud row resurrected sold inventory | User could sell shares they no longer owned | Fixed |
| C5 | SIP / IPO request bodies did not match the API | Both features always failed (HTTP 422) | Fixed |
| H1 | `delete_user` resurrected the account | Deleted accounts came back | Fixed |
| H2 | SIP day 29–31 raised `ValueError` | HTTP 500 on a valid request | Fixed |
| H3 | LTCG never detected for cloud rows | Tax report classified everything as STCG | Fixed |
| H4 | Unknown user id reported ₹10,00,000 | Phantom capital | Fixed |
| H5 | Pre-market window ended at 09:08 | 09:08–09:14 shown as "market closed" | Fixed |
| H6 | Four UI panels bound to non-existent element ids | Option chain, sector split, tax card, market pill never rendered | Fixed |
| H7 | Watchlist read/write used different owners | Guest stars never appeared | Fixed |
| H8 | Peer table read a key the quote never emits | Dividend yield always 0.80% | Fixed |
| H9 | Fallback price derived from salted `hash()` | Prices changed on every restart | Fixed |
| H10 | `cancel_gtt_order` / `cancel_sip` reported success on no-op | False success toasts | Fixed |
| H11 | Pending orders stored margin in `total_amount` | Order value mis-reported; refunds depended on it | Fixed |
| H12 | Existing DBs skipped `init_db()` migrations | A new column could be missing at runtime | Fixed |
| N1–N10 | Known issues left unchanged, with recommendations | See §5 | Reported |

---

## 2. Verification

```bash
python probe_bugs.py            # 12 defect probes (before -> after)   -> 0 defects
python probe_regressions.py     # 30 adversarial regression checks      -> 0 problems
python test_api_contract.py     # frontend payload <-> API contract     -> 0 failures
python test_app.py              # broker engine E2E                    -> ALL PASSED
python test_trade_lifecycle.py  # order lifecycle                      -> passed
python test_user_credentials.py # auth / profile                       -> passed
```

`probe_bugs.py`, `probe_regressions.py` and `test_api_contract.py` are new files added by this audit and are safe to keep in CI. `probe_bugs.py` and `probe_regressions.py` force Supabase off, and `test_api_contract.py` points it at a dead endpoint, so none of them touch the cloud project. Only `test_user_credentials.py` writes to the real Supabase project (it creates and removes its own test user).

---

## 3. Critical — money and order lifecycle

### C1. Buy-side charges were recorded but never debited
**Where** `database.py` `execute_trade()` BUY branch (fix at [database.py:2078](database.py:2078))

**Symptom.** The trade confirmation screen showed a full SEBI charge sheet on a BUY, but the wallet only ever lost the gross order value. Sells *did* deduct charges. The asymmetry meant every buy left the account overstated by its own brokerage + STT + stamp duty + exchange/SEBI fees + GST.

**Root cause.** In the BUY branch the cash mutation happened first:

```python
new_balance = round(balance - required_margin, 2)   # margin only
...
charges = calculate_trade_charges("BUY", ...)       # computed AFTER, used only for display
```

`charges["total"]` was written into the `orders` row for the contract note but never subtracted from `balance`. The SELL branch, by contrast, used `net_proceeds = total_amount - charges["total"]`, so only one leg of a round trip was charged.

**Fix.** Compute the charge sheet before the mutation and debit it with the margin; a resting BUY now reserves margin + charges so the fill itself cannot fail on cash:

```python
charges = calculate_trade_charges("BUY", product_type, asset_type, total_amount)
required_cash = round(required_margin + charges["total"], 2)
if balance < required_cash: ...
new_balance = round(balance - required_cash, 2)
```

**Verification** (`probe_bugs.py` 1–2). Buy 10 × TCS @ ₹1,000 delivery:

| | Before | After |
|---|---|---|
| Cash debited | ₹10,000.00 | ₹10,017.77 (incl. ₹17.77 charges) |
| Flat round trip leaves | ₹9,99,967.80 | ₹9,99,950.03 |

`test_app.py` asserted `== 990000.0`, i.e. it **encoded the bug**; it is now charge-aware.

---

### C2. `restore` + `cancel` duplicated the blocked margin
**Where** `database.py` `restore_balance()` (fix at [database.py:2710](database.py:2710))

**Symptom.** Repeatable money creation: place a pending order, press **Restore Full ₹10,00,000**, then cancel the order — the wallet ended ₹10,000 *above* the restore target.

**Root cause.** `restore_balance()` reset the balance to ₹10,00,000 and deleted holdings/positions (its comment says it exists to "prevent balance duplication arbitrage"), but it left the `orders` rows in `OPEN`. Its implicit refund was therefore not matched by a state change, and `cancel_order()` — which refunds any `OPEN` BUY order — refunded the block a second time.

**Fix.** Retire resting orders as part of the restore, so the second refund is refused, while keeping the history auditable:

```sql
UPDATE orders SET status = 'CANCELLED'
WHERE user_id = ? AND status IN ('OPEN','TRIGGER_PENDING','CANCELLING')
```

**Verification** (`probe_bugs.py` 3): before → ₹10,10,000; after → ₹10,00,000 and the cancel returns `Cannot cancel order with status 'CANCELLED'`.

---

### C3. Resting LIMIT / STOP-LOSS orders were never triggered
**Where** `main.py` (fix at [main.py:855](main.py:855)); `database.py` `check_open_limit_orders()` (fix at [database.py:2502](database.py:2502))

**Symptom.** An order placed at a price away from the market stayed `OPEN` forever. The Orders tab, `GET /api/orders`, showed it unchanged no matter how the price moved.

**Root cause.** `check_open_limit_orders()` had exactly one caller — inside `place_order()`, restricted to the symbol just traded:

```python
check_open_limit_orders(order.symbol, exec_price, user_id=uid)
```

There was no poller, scheduler or read-path hook, so an order only ever re-evaluated when the user happened to submit *another* order for the *same* symbol. A secondary bug: the SQL matched `symbol = ?` exactly, while stored symbols are upper-cased with an exchange suffix (`RELIANCE.NS`) — so even that rare path missed whenever the caller passed a bare symbol.

**Fix.** Evaluate resting orders on the Orders poll (the natural heartbeat), using the 60s quote cache so it stays cheap, and match on symbol variants:

```python
def service_pending_orders(uid: str) -> int:
    pending = get_orders(status_filter="OPEN", ...) + get_orders(status_filter="TRIGGER_PENDING", ...)
    for symbol in {o["symbol"] for o in pending}:
        quote = market_service.get_stock_quote(symbol)
        check_open_limit_orders(symbol, quote["price"], user_id=uid)
```

**Verification** (`probe_bugs.py` 10–11, `test_api_contract.py` §4, `probe_regressions.py` C). A limit BUY at ₹550 rests while the feed is ₹600, then fills at ₹540 on the next poll; a stop-loss on `SBIN.NS` triggers when queried as `SBIN`; five consecutive servicing passes produce exactly one fill and one holding row.

**Guard against double fills.** Fills remain claim-based — `check_open_limit_orders` must win a guarded `OPEN|TRIGGER_PENDING → CANCELLING` update (rowcount-checked) before it may execute — so the newly added polling cannot double-fill an order. The servicing loop reads pending symbols straight from the local ledger (`get_pending_order_symbols`) rather than pulling full order lists, so the Orders poll does not add cloud round trips.

---

### C4. A stale cloud row resurrected sold inventory
**Where** `database.py` `sync_holdings_from_supabase_into_cursor()` (fix at [database.py:1543](database.py:1543)), `sync_positions_from_supabase_into_cursor()` ([database.py:1634](database.py:1634))

**Symptom.** After selling an entire holding, the next cloud sync brought it back with its old quantity — sellable a second time. This was caught by the repo's own `test_trade_lifecycle.py`, which had never actually run (it failed at line 22 first, see §6).

**Root cause.** A full sale correctly wrote a tombstone *and* queued remote cleanup. The sync then did the opposite of what the tombstone was for:

```python
cursor.execute("DELETE FROM holding_tombstones WHERE user_id = ? AND UPPER(symbol) = ?", ...)
...
INSERT OR REPLACE INTO holdings (...)   # sold holding restored
```

It deleted the local evidence of the sale and trusted the remote quantity unconditionally.

**Fix.** Compare timestamps: if the local sale/close is newer than the cloud row's `updated_at`, the local ledger wins and the cloud row is reconciled to zero; otherwise the cloud row is a genuine later acquisition and the tombstone is cleared. This is what makes the tombstone "short-lived" as originally intended.

**Verification** (`test_trade_lifecycle.py` line 54 assertion): a fake remote returning quantity 10 after a full local sale now yields no holdings and issues a `PATCH ... quantity: 0`.

---

### C5. SIP and IPO submissions never reached the backend correctly
**Where** [static/app.js:6820](static/app.js:6820) (SIP), [static/app.js:6715](static/app.js:6715) (IPO)

**Symptom.** "Schedule SIP" and "Apply for IPO" always failed, with a generic `Failed to schedule SIP` / `IPO application failed` toast.

**Root cause.** The client sent field names the Pydantic models do not define, so FastAPI rejected every request with **HTTP 422** before any handler ran:

| Client sent | Model expects |
|---|---|
| `symbol`, `amount`, `installment_day` | `fund_id`, `fund_name`, `monthly_amount`, `sip_day` |
| `ipo_id`, `lots`, `bid_price`, `upi_id` | `ipo_id`, `ipo_name`, `lots`, `shares`, `bid_price` |

`shares` is the *lot size* (the backend multiplies `lots × shares`), and `ipo_name` is required.

**Fix.** Send the documented fields, deriving the fund display name from the current page asset or the modal input.

**Verification** (`test_api_contract.py` §2–3): the exact new payloads are accepted, the SIP appears in `GET /api/mf/sips`, and the IPO bid blocks ₹14,820 (1 lot × 38 × ₹390).

---

## 4. High — state, reporting and UI correctness

### H1. `delete_user` resurrected the account it had just deleted
**Where** [database.py:2744](database.py:2744) — *this was the cause of a failing test in the repo.*

**Root cause.** The remote cleanup block ran *after* the local `DELETE`, and its first statement was `u_row = get_user(user_id)`. `get_user()` falls back to Supabase when the local row is missing and **re-inserts what it finds** (`INSERT OR REPLACE INTO users`). So the delete re-created the account locally a microsecond after removing it.

**Fix.** Resolve the account and its `auth_id` *before* the local delete, and reuse that snapshot.

### H2. SIP instalment days 29–31 raised `ValueError`
**Where** [database.py:2868](database.py:2868), guarded at [main.py:1086](main.py:1086)

`datetime(year, month, day)` raises `ValueError: day is out of range for month`, e.g. a SIP on the 31st while today is in September → HTTP 500. The API accepted any integer. Now the next date rolls forward and clamps to the month's last valid day (`calendar.monthrange`), and out-of-range values are rejected with a 400.

### H3. LTCG was never detected for cloud-synced orders
**Where** [database.py:2972](database.py:2972)

`_parse_order_dt` did `datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")`. Supabase returns `2026-01-01T10:00:00.123456+00:00`; slicing 19 characters keeps the literal `T`, the parse fails and returns `None` — so `days_held` was never computed and **every** sell was labelled STCG (20% instead of 12.5% + ₹1.25 L exemption). Now it uses `datetime.fromisoformat` with a `strptime` fallback.

### H4. An unknown user id was reported as holding ₹10,00,000
**Where** [database.py:1131](database.py:1131), [main.py:491](main.py:491)

`get_account()` returned a hard-coded ₹10,00,000 when no row matched, so a stale or arbitrary `x-user-id` looked fully funded. It now returns zeros plus `exists: False`, and `GET /api/account` reports the guest payload.

### H5. Pre-market session ended seven minutes early
**Where** [market_hours.py:51](market_hours.py:51)

The window was `540 <= total_minutes < 548` (09:00–09:08) while pre-open runs to 09:15. Everything from 09:08 to 09:14 fell through to the final `else` and was reported as **`AMO` / "Market CLOSED"**. Changed to `< 555`.

### H6. Four UI panels were bound to element ids that do not exist
**Where** [static/app.js:6304](static/app.js:6304), [:6924](static/app.js:6924), [:6955](static/app.js:6955), [static/index.html:89](static/index.html:89)

`getElementById` returns `null`, and every one of these call sites guarded with `if (element)`, so the panels silently stayed empty instead of throwing:

| app.js asked for | index.html actually has |
|---|---|
| `foTableBody` | `optionChainTableBody` → option chain never rendered |
| `sectorDiversificationBars` | `sectorAllocationContainer` → sector split never rendered |
| `taxStcgRealized` / `taxStcgPayable` / `taxLtcgRealized` / `taxLtcgPayable` | `taxStcgGain` / `taxStcgLiability` / `taxLtcgGain` / `taxLtcgLiability` → tax card stuck at ₹0.00 |
| `marketPulseDot` / `marketStatusText` | *(absent entirely)* → live market status never shown |

For the last one the CSS was already present in `style.css` (`.market-status-pill`, `.pulse-dot.green/.orange/.gray`); only the markup had been dropped, so it is restored in the header with those ids.

### H7. Guest watchlist read and wrote different owners
**Where** [main.py:895](main.py:895)

`read_watchlist` used `uid or "default"` while `add_watchlist` / `delete_watchlist` used `uid or "guest"`. A signed-out visitor read the seeded demo list and wrote to a different account, so a starred symbol never appeared. All three now use the same fallback.

### H8. Peer comparison read a key the quote never publishes
**Where** `market_service.py` `get_stock_peers()` (fix at [market_service.py:841](market_service.py:841))

Quotes publish `dividend_yield`; the code read `q.get("div_yield", 0.8)` — always the fallback, so every peer displayed a hard-coded **0.80%**. The same function also called `random.seed(...)`, reseeding the *shared module-level* RNG that also drives order-depth quantities and transaction references; it now uses a private `random.Random(seed)`.

### H9. Synthetic fallback prices changed on every restart
**Where** `market_service.py` `_get_default_stock_quote()` (fix at [market_service.py:347](market_service.py:347))

`abs(hash(symbol))` — Python salts string hashing per interpreter (`PYTHONHASHSEED`), so a symbol not in the master list got a different price after each restart. Replaced with `zlib.crc32`, which is stable. Verified by running two separate interpreters.

### H10. Cancelling a non-existent GTT / SIP reported success
**Where** [database.py:2860](database.py:2860), [database.py:2906](database.py:2906)

Both issued an unconditional `UPDATE` and returned `{"success": True}` regardless of whether a row matched, and without checking the current status. Both now filter on `status = 'ACTIVE'` and check `cursor.rowcount`.

### H11. Pending orders stored the blocked margin as the order value
**Where** [database.py:342](database.py:342)

`total_amount` received `required_margin`, so a resting intraday order displayed 20% of its true value, and `cancel_order` depended on that same overloaded field. A dedicated `blocked_amount` column now holds what was withheld (margin + estimated charges) and `cancel_order` refunds exactly that, falling back to `total_amount` for rows written before the column existed.

---

### H12. Hardening that came out of the fix review
- `ensure_db_initialized()` short-circuits whenever the `users` table exists, which means `init_db()`'s column migrations never run for an existing database. Since C1/H11 added a column that `cancel_order` now selects, the guard probes `SELECT blocked_amount FROM orders LIMIT 1` and re-runs `init_db()` if it is missing. `probe_regressions.py` D builds a pre-fix database and confirms it is migrated in place and that a legacy `OPEN` row still cancels via the `total_amount` fallback.
- `get_orders()` now also returns `blocked_amount`, so a client can display "margin blocked" separately from the order value (which H11 restored to meaning what it says).

---

## 5. Known issues left unchanged

These are real but need design decisions or carry a wider blast radius than a bug fix.

**N1 — GTT orders have no trigger engine.** `place_gtt_order` inserts a row; nothing anywhere evaluates `trigger_price`, so a GTT can never fire. `get_ipos`-style read paths confirm there is no evaluator. A GTT needs the same servicing hook as C3 plus target/stop-loss handling; recommend modelling it on `service_pending_orders`.

**N2 — Supabase-first reads shadow local state.** `get_orders`, `get_watchlist` and `list_users` return the remote list whenever it is non-empty and never merge the local ledger. A just-placed or just-cancelled order can therefore be missing or stale in the UI. Recommend making local SQLite the read source of truth with the cloud as a sync target.

**N3 — The deployed Supabase schema has drifted from the code.** Live errors observed during the test run:

```
column users.username does not exist
Could not find the 'password' column of 'users'
Could not find the table 'public.gtt_orders' / 'public.sips' / 'public.ipo_bids'
```

`supabase_schema.sql` never created `gtt_orders`, `sips`, `ipo_bids`, nor the `auth_id`, `age`, `experience`, `has_completed_tour`, `bank_*` columns, nor `orders.charges` / `net_amount`. Every write touching them fails and the failure is swallowed by `try/except` — the cloud is silently incomplete. **`supabase_migration.sql` has been extended** with all of the missing DDL (idempotent, safe to re-run); apply it to the project.

**N4 — There is no authentication.** Identity is a client-supplied `x-user-id` header or `?user_id=` query parameter, so any user can act as any other by changing a value. Inherent to the current design; needs real sessions (Supabase Auth is already wired up for storage) before this is exposed beyond a demo.

**N5 — `x-vercel-original-url` is trusted unvalidated.** The middleware rewrites the request path from a client-supplied header, which any caller can set. Constrain it to the Vercel-injected value (e.g. only when a platform header proves the request came through the proxy).

**N6 — Sector allocation uses cost basis.** `get_sector_allocation` weightings use `avg_price` while `/api/portfolio` uses market value, so the two disagree. Pass live quotes if the chart is meant to show current allocation.

**N7 — "Most bought" is not most bought.** `market_service.get_explore_data` sets `most_bought = all_stocks[:8]` — simply the first eight entries of the master list.

**N8 — Offline navigation always fails.** `sw.js` is deliberately network-only for the app shell and its fallback resolves `caches.match()` (which is `undefined` on a miss), so a cold offline navigation can never succeed. Add the shell to the precache with a stale-while-revalidate strategy if offline support is wanted.

**N9 — Intraday timing is never actually blocked.** `validate_order_timing` returns `(True, "INTRADAY", ...)` even when the market is closed; the returned `order_tag` is then discarded for non-AMO orders. This contradicts the README's "strict market hours enforcement". Either enforce it or correct the README.

**N10 — Messaging vs. funding model.** A new account's *bank* is credited ₹10,00,000 while the trading wallet starts at ₹0 (funded later via UPI). That is a coherent design, but `create_user`'s onboarding promise ("unlock ₹10,00,000 virtual balance") and the README's "₹10,00,000 available balance" are misleading. Recommend wording the copy as "₹10,00,000 in your linked bank account".

---

## 6. Note on the existing test suite

`test_trade_lifecycle.py` could never pass in this repository: line 22 bought stock for an account whose wallet is intentionally ₹0 until funded. Because it aborted there, the later assertions — including the real C4 defect — never executed. Both are addressed: the test now funds the wallet via the documented bank→wallet transfer, and C4 is fixed. `test_app.py` asserted `990000.0` after a buy and so **locked in C1**; it is now charge-aware. `test_user_credentials.py` was failing because of H1 and passes unchanged.

---

## 7. Verification results

Every figure below is real output from the probes.

| Probe | Expectation | Before | After |
|---|---|---|---|
| 1 | cash out = value + charges | ₹10,000.00 | ₹10,017.77 |
| 2 | flat round trip = start − both charge sheets | ₹9,99,967.80 | ₹9,99,950.03 |
| 3 | restore then cancel creates no cash | ₹10,10,000.00 | ₹10,00,000.00 |
| 4 | deleted user stays deleted | user came back | `None` |
| 5 | SIP on the 31st schedules | `ValueError` | 30 Sep 2026 |
| 6 | 09:10 IST is pre-market | `AMO` | `PRE_MARKET` |
| 7 | ISO timestamp parses | `None` | 2026-01-01 10:00:00 |
| 8 | peer dividend yield is real | 0.80% (hard-coded) | matches the quote |
| 9 | fallback price stable across processes | differed | identical |
| 10 | resting limit order fills | never | fills at ₹540 |
| 11 | bare symbol matches `.NS` row | missed | matches |
| 12 | unknown user balance | ₹10,00,000 | ₹0.00 + `exists: False` |

Final state: `probe_bugs.py` 12/12 · `test_api_contract.py` 0 failures · `test_app.py` ALL PASSED · `test_trade_lifecycle.py` passed · `test_user_credentials.py` passed.

---

## 8. Limits of this verification

Stated plainly so the results are not over-read:

- **Author-run verification.** This is self-verification through purpose-built probe suites plus the repository's own tests. An independent adversarial verification pass was attempted but the verification sub-agent rejected both packet formats (`verification_packet_validation_failed_twice`) and is now blocked for this request, so it could not be re-run. Treat §7 as strong but not independent evidence.
- **Probes test behaviour, not the browser.** The frontend fixes in H6 and C5 were verified by reading the shipped DOM (ids exist), by `node --check` for syntax, and by driving the same request bodies through the real Pydantic models. No browser rendering or click-through was performed.
- **LTCG boundary.** `_parse_order_dt` deliberately drops timezone info. Every timestamp in play (`orders.timestamp` via SQLite `CURRENT_TIMESTAMP`, Supabase `updated_at`/`deleted_at`, and the UTC ISO strings this code writes) is UTC, so the comparison is consistent — but a holding period landing within hours of the 365-day line can still fall on either side by a day.
- **The cloud schema is fixed in the migration file, not in the live project.** N3 is only resolved once `supabase_migration.sql` is applied to Supabase. Until then the cloud sync for GTT/SIP/IPO and the new columns continues to fail silently.
- **The simulated order book has no price feed of its own.** Resting orders are evaluated when the Orders tab polls. A user who never opens the app will not see a fill until they do.

---

## 9. Files changed

**Backend** — `database.py` (C1 C2 C4 H1 H2 H3 H4 H10 H11 H12), `main.py` (C3 H2 H4 H7 H12), `market_service.py` (H8 H9), `market_hours.py` (H5)
**Frontend** — `static/app.js` (C5 H6), `static/index.html` (H6); the byte-identical `public/` and `public/static/` copies were re-synced
**Cloud schema** — `supabase_migration.sql` (N3)
**Tests** — `test_app.py` and `test_trade_lifecycle.py` corrected (both had encoded defects); `probe_bugs.py`, `probe_regressions.py` and `test_api_contract.py` added
