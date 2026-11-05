# Groww vs. Stoxify — Registration Flow Plan

**Status:** plan only. No application code was modified for this document.
**Revision 2** — scoped to **flow fidelity without real verification**. Supersedes the phase structure in revision 1.
**Date:** 13 Sep 2026

---

## 1. Goal

The registration should **feel** close to Groww. Verification is not the point — the sequence, the gates and the states are.

Groww's "feel" decomposes into five things, and none of them require a single real integration:

1. **Order** — mobile, then email, then PAN, then auto-filled personal details, then bank, then consent, then a pause.
2. **Gates** — each identity step is confirmed before the next appears. You cannot skip ahead.
3. **Prefill** — the system "already knows" your name, date of birth and address. You confirm; you do not type. This is Groww's most distinctive move, and it is free to fake.
4. **The pause** — you submit, and you are told the documents are being processed. The anti-climax is part of the experience.
5. **Reveal** — the client ID and login credentials arrive at the end, when the account is ready.

Explicitly *not* required: real PAN/Aadhaar/NPCI checks, document uploads, video verification, e-signatures, or regulatory artefacts. Those add build cost and zero felt difference.

### What currently breaks the feel

- **Username + password in step 1.** Groww has neither (§3).
- **The OTP gate is not a gate.** It is bypassable with a hard-coded `4321` ([app.js:6086](static/app.js:6086)).
- **Nothing is prefilled.** The user types their own name, DOB and age by hand, contradicting the "we already know you" effect.
- **Five steps then instant success.** There is no pause, so the single most recognisable moment of Groww's flow is absent.

---

## 2. What Groww actually does

Verified against current public documentation (§12).

| # | Groww step | Detail |
|---|---|---|
| 1 | Mobile + email | Both entered; **OTPs are sent to both** during the flow |
| 2 | PAN verification | PAN checked against the income-tax database; name must match |
| 3 | Aadhaar e-KYC | Aadhaar fetched via OTP; **address is pulled from the UIDAI record**, not typed |
| 4 | Bank linking | Account number + IFSC + **cancelled cheque or bank statement upload**; name on the bank account must match PAN exactly |
| 5 | KYC details | Occupation, income, **father's and mother's names**, trading experience |
| 6 | IPV | In-person verification: a short selfie **video** proving a real person |
| 7 | Signature | Signature photographed on white paper and uploaded |
| 8 | e-Sign | Account-opening agreement e-signed with **Aadhaar OTP** (legally equivalent to a physical signature under the IT Act, 2000) |
| 9 | Consent | Read applicable charges and tick to agree; open the stocks account |
| 10 | **Pending** | Account activates in **a few hours to 1–3 working days** after verification; client ID + login credentials arrive by email |
| 11 | Post-activation | Log in with user ID + password + OTP, then **set a 4- or 6-digit PIN** and optionally enable biometric login |
| 12 | Segment gating | F&O needs **separate activation with income proof** (or instant activation if holdings exceed a threshold) |

Also relevant:
- Groww is a **standalone** trading + demat account funded by UPI, not a 3-in-1 bundle. Demat is CDSL-only.
- **Minor and joint accounts are separate flows** — the main flow is for adults.
- Nominee details are a distinct step.
- Account closure is offline (physical form), unlike opening.

---

## 3. What Stoxify does today

The wizard is a 6-container / 5-indicator flow at [index.html:1456](static/index.html:1456)–1733, driven by [app.js:5944](static/app.js:5944)–6296.

| Step | Screen | Fields collected | What actually happens |
|---|---|---|---|
| 1 | "Open Your Demat Account" | Mobile, email, **username**, **password** | Validates 10-digit phone, email regex, username 3–25 + charset, password ≥ 6. Calls `GET /api/user/check-username`, then probes `POST /api/user/login` with the email to detect an existing account. Generates a **4-digit OTP client-side** (`Math.random`), renders it in a fake SMS banner ([app.js:6012](static/app.js:6012)) |
| 2 | "Enter Verification Code" | 4-digit OTP | Accepts the generated code **or the literal `4321`**. `resendOtp()` reveals the new code in a toast ([app.js:6059](static/app.js:6059)) |
| 3 | "Personal Details" | PAN, full name, DOB, gender, occupation, income, **age (typed manually)**, experience | PAN: length 10 only. Name: non-empty. Age: from the manual field, must be ≥ 13. `cutoffDate` is computed from DOB and then **never used** ([app.js:6129](static/app.js:6129)) |
| 4 | "Link Bank Account" | Bank chip, account no., re-enter, IFSC | Chips prefill a canned IFSC. "Penny drop" is a **2.2 s CSS animation with no API call** ([app.js:6196](static/app.js:6196)) |
| 5 | "Set 4-Digit Trading PIN" | PIN, confirm | `POST /api/user/create`, stores the user id in `localStorage`, jumps straight to success |
| 6 | "Account Successfully Activated!" | — | Shows Demat ID, username, email, bank, and "Linked Bank Balance ₹10,00,000" |

Backend: `POST /api/user/create` ([main.py:225](main.py:225)) → `create_user()` ([database.py:772](database.py:772)) generates a `STOX-######` id, derives an avatar colour from the name length, **derives the IFSC from the bank name** (`f"{bank_name.split()[0].upper()[:4]}0001234"` at [database.py:794](database.py:794)), derives the UPI id from the username, sets wallet `balance = 0` with `bank_balance = 1,000,000`, seeds a watchlist, and mirrors the row into Supabase Auth + the cloud `users` table.

---

## 4. Gap analysis and how the gaps are triaged

The gap tables below are unchanged from revision 1; what changed is what we do about them. Each gap now falls into one of three buckets.

### Bucket A — flow gaps (these are the work)

| Gap | Why it is flow |
|---|---|
| G1 no username/password | Groww has none; step 1 is shaped wrong |
| G3 (partial) no address | The *prefilled address* is what makes the PAN step feel Groww-like |
| G5 no consent screen | A distinct screen with a tick is part of the rhythm |
| G6 instant activation | The pause is the most recognisable moment |
| G7 PIN during registration | Groww sets it after activation |
| G8 no charges consent | Same as G5 |
| G10 no nominee | Optional in Groww too — low priority |
| G26 indicator drift | The wizard miscounts its own steps |

### Bucket B — ceremony (deliberately not built)

| Gap | Why we skip it |
|---|---|
| G2 email + mobile *verified* | We keep the *gate* (an OTP step you must clear); we do not build real delivery |
| G4 signature + IPV video | Camera/canvas work with no felt benefit |
| G9 F&O income-proof activation | Post-activation flow, not registration |
| G17 bank name must match PAN | Invisible to the user when it passes |
| G28 penny drop really verifies | The animation already lands the feeling |

### Bucket C — real defects, fix regardless of the flow work

These are not flow issues. They are bugs found while comparing, and they should be fixed whatever we decide about Groww parity.

| Gap | Why it matters |
|---|---|
| G11 PAN length-only validation | `ABCDE1234F`-shaped nonsense passes |
| G12 gender/occupation/income collected then **silently discarded** | The user fills them in and they vanish ([app.js:6232](static/app.js:6232), [main.py:209](main.py:209)) |
| G13 father's/mother's name never asked | Two cheap fields, currently lost |
| G14 age typed manually, can contradict DOB; DOB check is dead code | Internal inconsistency |
| G15 age floor 13, and 10 on update | Inconsistent; wrong for an adult product |
| G16 IFSC overwritten server-side; weak bank validation | The user's real IFSC is thrown away |
| G18 PIN length unvalidated at creation | Only enforced on update ([main.py:367](main.py:367)) |
| G20 OTP bypass | A "gate" with a master key |
| G21 credentials stored in plaintext | **[database.py:173](database.py:173), [:166](database.py:166)** — see §10 |
| G22 account enumeration | Login returns the account holder's **name** for a bare identifier ([main.py:413](main.py:413)) |
| G24 no mobile uniqueness | Any 10-digit number is accepted; two accounts can share one |
| G25 Supabase RLS is `USING (true)` | Whoever holds the publishable key can read every user's bank account and PIN |
| G30 success screen shows a hard-coded ₹10,00,000 | Not read from the account |

---

## 5. Scope decision (settled)

Revision 1 left four decisions open. Your steer resolves all four:

> *Close to Groww, not identical. We don't need to verify everything. The flow is the important thing.*

- **D1 — how faithful should verification be?** → **UX-faithful only.** No mock KYC provider layer, no real integrations. Build the steps, the gates and the states; fake the results.
- **D2 — keep username + password?** → **Remove from registration**, keep as a legacy login path so existing accounts still work.
- **D3 — primary identifier?** → **Mobile**, verified by the OTP step. Email becomes a required second gate.
- **D4 — model the pending state?** → **Yes**, but with a short simulated wait rather than a locked account (see R2).

Two micro-decisions remain, and neither blocks starting.

**R1 — should the OTP gate be enforced server-side?**
The user experience is identical either way. Server-side costs ~1 day: one table plus two endpoints, no third-party anything.
- **(a) Yes, keep the gate real** *(recommended)*: the code is still displayed on screen as the simulated SMS, but the check happens in the backend. This is the one piece of "verification" that is load-bearing, because without it step 2 is a screen that always says yes.
- (b) Defer: keep it client-side for now. Faster, but the first gate remains decorative.
Either way, delete the `4321` master bypass — that is a one-line deletion, not a project.

**R2 — how long is the pending pause?**
Recommend a visible simulated wait (roughly 10–20 seconds) with the state persisted, so a page refresh during the wait still shows "processing". No locking of the trading UI — a locked demo is a broken demo.

---

## 6. Target flow

Replaces the current 5 steps. Seven steps, then the pause, then the reveal.

| # | Step | What the user does | What is faked |
|---|---|---|---|
| 1 | **Mobile** | Enters a 10-digit mobile → "OTP sent" → 4 boxes → verify | Delivery only: the code is shown on screen in a banner labelled *Simulated SMS (demo)* |
| 2 | **Email** | Same rhythm, one more gate | Same |
| 3 | **PAN** | Enters PAN → format validated → **next screen arrives prefilled** | The "records lookup" returns a canned name, DOB and address matching the PAN pattern |
| 4 | **Personal details** | Confirms name / DOB / **address** (read-only, "fetched from records"), then fills gender, occupation, income, trading experience, father's and mother's name | The lookup. Age is **derived from DOB** — the manual age field is deleted |
| 5 | **Bank** | Picks a bank → account number, re-enter, IFSC → penny-drop beat → verified | The penny drop: the existing animation, now returning a result |
| 6 | **Consent + submit** | Reads the charge schedule, ticks to agree, "Open my account" | Nothing |
| 7 | **Pending** | "Your documents are being processed. You'll receive your client ID by email." | The processing. State persists across a refresh |
| — | **Active + reveal** | Client ID shown, credentials confirmed | The activation. **Then** prompted to set a 4-digit app PIN |

Two notes on the design:

- **Step 3 is where the Aadhaar *feeling* is delivered without Aadhaar.** Groww's step 3 fetches your identity and address from the government record. Ours fakes the *result* — a prefilled, read-only block you confirm — which is the part the user actually experiences. No Aadhaar number is collected.
- **The PIN moves to the end** and out of the wizard, matching Groww's order.

---

## 7. Implementation plan

Three phases. No task longer than 1–2 days. Sizes: **S** ≈ under half a day, **M** ≈ 1–2 days.

### Phase 1 — Reshape the wizard (this is the deliverable)

| # | Task | Files | Size |
|---|---|---|---|
| 1.1 | Drive the step containers and the progress indicator from a single `STEPS` array so the count cannot drift again (fixes G26) | `static/index.html`, `static/app.js` | M |
| 1.2 | Step 1 → mobile only with the OTP gate; delete the username and password inputs (G1) | " | M |
| 1.3 | Step 2 → email with its own OTP gate | " | S |
| 1.4 | Step 3 → PAN format validation, then the prefilled read-only name/DOB/address block; **derive age from DOB and delete the manual age field** (G11, G14, G15) | " | M |
| 1.5 | Step 4 → personal details including father's and mother's name; **actually send gender, occupation and income to the API** (G12, G13) | " | S |
| 1.6 | Step 5 → bank validation, penny-drop feedback, and stop discarding the typed IFSC (G16, G28) | " | S |
| 1.7 | Step 6 → charges/consent screen with a required tick (G5, G8) | " | S |
| 1.8 | Step 7 → pending screen, persisted activation state, then the client-ID reveal (G6) | " | M |
| 1.9 | Move the PIN out of the wizard into a post-activation prompt (G7) | " | S |

### Phase 2 — Backend contract and persistence

| # | Task | Files | Size |
|---|---|---|---|
| 2.1 | Add the new columns (§8) with an idempotent migration; mirror them in `supabase_migration.sql` | `database.py`, `supabase_migration.sql` | M |
| 2.2 | Accept and persist gender, occupation, income, father's and mother's name in `CreateUserRequest` / `create_user` (G12, G13) | `main.py`, `database.py` | S |
| 2.3 | Make `username` and `password` optional for new accounts; keep legacy rows fully working (G1) | `main.py`, `database.py` | S |
| 2.4 | Enforce mobile-number uniqueness, and validate PIN length at creation, not only on update (G18, G24) | `database.py`, `main.py` | S |
| 2.5 | Store the IFSC as entered; remove the derived-IFSC overwrite (G16) | `database.py` | S |

### Phase 3 — Login, activation polish, tests

| # | Task | Files | Size |
|---|---|---|---|
| 3.1 | Login: mobile → OTP as the primary path; keep the username/email/password path for legacy accounts and label it as such | frontend, `main.py` | M |
| 3.2 | Post-activation app PIN (4-digit) with optional biometric later | frontend, `main.py` | S |
| 3.3 | Neutral login responses — no account name and no `exists` flag without a credential — and drop the step-1 existence probe (G22) | `main.py`, `static/app.js` | S |
| 3.4 | Success screen reads live values instead of the hard-coded ₹10,00,000 (G30) | frontend | S |
| 3.5 | Add `test_registration_flow.py`: step gates cannot be skipped, the OTP gate cannot be bypassed, PAN/IFSC/mobile validation, prefilled-detail integrity, duplicate mobile rejection, pending→active, PIN only after activation. Extend `test_api_contract.py` | tests | M |

### Optional, if you want it later

Not needed for the flow, listed so they are not mistaken for oversights:

- **R1:** server-side OTP enforcement (~1 day, one table + two endpoints).
- **Credential hashing** (G21) and **owner-scoped RLS** (G25). Both become necessary the moment this is used by anyone real; neither affects the flow. Note that Phase 1 adds address and parent names to the database, so the exposure grows — do these before real users, not before Phase 1 starts.
- **F&O activation with income proof** (G9), **nominee** (G10), demo credentials.

---

## 8. Data model changes

`users` — add: `phone_verified_at`, `email_verified_at`, `kyc_status` (`PENDING` | `ACTIVE` | `LEGACY`), `address_line1`, `address_line2`, `city`, `state`, `pincode`, `gender`, `occupation`, `income_range`, `father_name`, `mother_name`, `app_pin_hash`, `client_id`, `activated_at`.

New table — only if you take R1(a): `otp_challenges` (`identifier`, `purpose`, `code_hash`, `expires_at`, `attempts`, `consumed_at`, `created_at`).

Dropped from revision 1: `aadhaar_last4`, `kyc_reference`, `signature_captured_at`, `ipv_completed_at`, `esign_at`, `nominee_*`, `segments`, and the `kyc_applications` / `kyc_documents` / `kyc_events` tables.

Migration notes:
- Additive and idempotent, following the guarded-`ALTER` pattern already in `init_db` ([database.py:181](database.py:181)).
- Backfill every existing row to `kyc_status = 'LEGACY'` so nothing locks anyone out.
- `pin` / `password` stay as they are unless you take the optional hashing item.

---

## 9. API changes at a glance

| Change | Endpoint |
|---|---|
| Changed | `POST /api/user/create` — called at submit (step 6); accepts the new personal fields; `username`/`password` become optional |
| Changed | `POST /api/user/login` — neutral response without a credential; mobile + OTP becomes the primary path |
| New | `GET /api/user/activation-status` |
| New | `POST /api/user/pin` — the post-activation app PIN |
| New (only if R1(a)) | `POST /api/otp/send`, `POST /api/otp/verify` |
| Retired | `GET /api/user/check-username` — there is no longer a username to check |

---

## 10. Deliberately not building

| Not building | Reason |
|---|---|
| Aadhaar number capture / DigiLocker / e-KYC OTP | Only its *felt* result is kept — the prefilled, read-only identity block in step 3 |
| Signature capture and upload | Canvas or camera work, invisible payoff |
| IPV selfie video | Camera permissions and moderate build cost, no felt benefit |
| Penny-drop name matching | Not visible to the user when it passes |
| Cancelled cheque / bank statement upload | File handling for a step whose feeling is already delivered by the penny-drop beat |
| Income proof and F&O activation | A post-activation flow, not registration |
| Nominee | Optional in Groww too |
| Aadhaar e-sign | We will not label a simulated signature as legally equivalent under the IT Act, because it is not |
| Mock KYC provider service layer | Revision 1 task 2.6. Under "flow over verification" there is nothing to abstract over |
| Resumable staged application | The biggest single item in revision 1 (L). The user never sees it — they see steps — so the account is still created in one call at submit |
| Append-only `kyc_events` audit trail | A regulatory artefact, not a flow feature |
| Groww's AMC/charges copy | Keep the existing charge schedule consistent with what the trading engine actually charges |

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| Seven steps feels longer than the current five | One decision per step, an honest progress bar, and step 3 is a *confirmation* rather than typing — a reward, not a chore |
| Existing accounts break when username/password become optional | Backfill to `LEGACY`, keep the legacy login path, never hard-fail |
| Showing the OTP on screen looks like a bug | Label the banner *Simulated SMS (demo)* so it reads as deliberate |
| Docs, tests or demo scripts assume a username/password signup | Grep for hard-coded logins before starting; `test_api_contract.py` already drives `/api/user/create` and will need updating |
| The removed ceremony is mistaken for an oversight | §10 lists every omission with its reason |
| Real users arrive later | The deferred security items (hashing, RLS, server OTP) are named in §7 rather than dropped |

---

## 12. Sources for the Groww facts

- Chittorgarh, *Groww Account Opening — Process, Documents and Charges* (register with email + mobile, OTP, PAN, bank details, occupation/income/parents' names, trading experience, signature upload, Aadhaar e-sign, activation in a few hours): https://www.chittorgarh.com/broker/groww/account-opening/173/
- KnowYourBrokerage, *Groww Account Opening — Documents, Online Process & Time* (mobile + email OTPs, PAN verification, Aadhaar address pull, bank + cancelled cheque with exact PAN name match, IPV video, Aadhaar-OTP e-sign, 1–3 working days, F&O activation with income proof, standalone account funded by UPI, minor/joint as separate flows): https://knowyourbrokerage.in/groww/account-opening
- KnowYourBrokerage, *Groww Login — Web & App Sign-in, Password Reset, 2FA* (user ID + password, OTP approval, then set a 4- or 6-digit PIN and optionally enable biometric): https://knowyourbrokerage.in/groww/login
- TradingCritique, *Groww Account Opening 2026* (signup with mobile and email; PAN, Aadhaar, bank proof, signature; Aadhaar-OTP e-sign; under 10 minutes to apply, approval within 24 hours): https://tradingcritique.com/broker-review/how-to-open-account-in-groww-online/

Not independently confirmed, and worth settling against a real Groww signup before locking the design: Groww's exact signup **OTP length**, and whether their signup currently requires a distinct password at all (older material implies email + password login; newer implies mobile + OTP first).
