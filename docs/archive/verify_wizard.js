/**
 * Non-browser verification of the rebuilt registration wizard.
 *
 * 1. Exercises the REAL prefill generator extracted from static/app.js
 *    (deterministic seeding, adult DOB, complete address).
 * 2. Cross-references every element id the wizard JS touches against the ids
 *    that actually exist in static/index.html — the id-drift class of bug that
 *    silently disabled four panels before.
 *
 * Run:  node verify_wizard.js
 */
const fs = require('fs');
const path = require('path');

const APP = fs.readFileSync(path.join(__dirname, 'static', 'app.js'), 'utf8');
const HTML = fs.readFileSync(path.join(__dirname, 'static', 'index.html'), 'utf8');

let failures = 0;
function check(name, ok, detail = '') {
  console.log(`[${ok ? 'OK ' : 'FAIL'}] ${name}${detail ? '  ' + detail : ''}`);
  if (!ok) failures++;
}

/* ---------------------------------------------------------------- 1. prefill */
console.log('='.repeat(72));
console.log(' 1. Prefill generator (real code sliced out of static/app.js)');
console.log('='.repeat(72));

const start = APP.indexOf('const OB_FIRST_NAMES');
const end = APP.indexOf('function applyObPrefill');
if (start < 0 || end < 0 || end <= start) {
  check('generator block found in app.js', false, `start=${start} end=${end}`);
  process.exit(1);
}
const generatorSource = APP.slice(start, end);

// eslint-disable-next-line no-new-func
const makeGenerator = new Function(`${generatorSource}; return prefilledIdentityFor;`);
const prefilledIdentityFor = makeGenerator();

const PAN_A = 'ABCDE1234F';
const first = prefilledIdentityFor(PAN_A);
const second = prefilledIdentityFor(PAN_A);
const other = prefilledIdentityFor('ZYXWV9876Q');

check('same PAN yields an identical identity (seeded, not random)',
  JSON.stringify(first) === JSON.stringify(second));
check('a different PAN yields a different name', first.name !== other.name,
  `"${first.name}" vs "${other.name}"`);

const nameOk = /^[A-Za-z]+ [A-Za-z]+$/.test(first.name);
check('name is a plausible two-word Indian name', nameOk, `"${first.name}"`);

const dob = new Date(first.dob);
const now = new Date();
let age = now.getFullYear() - dob.getFullYear();
const m = now.getMonth() - dob.getMonth();
if (m < 0 || (m === 0 && now.getDate() < dob.getDate())) age--;
check('generated DOB always implies an adult (>=18)', age >= 18, `age ${age} from ${first.dob}`);
check('generated DOB is a real date', !isNaN(dob.getTime()), first.dob);

check('address line 1 is populated', !!first.address_line1, first.address_line1);
check('address line 2 is populated', !!first.address_line2, first.address_line2);
check('city is populated', !!first.city, first.city);
check('state is populated', !!first.state, first.state);
check('pincode is a 6-digit code', /^\d{6}$/.test(first.pincode), first.pincode);

// Every PAN in a spread should produce a complete, adult identity.
let spreadOk = true;
let spreadDetail = '';
const names = new Set();
for (let i = 0; i < 400; i++) {
  const pan = 'AAAPL' + String(1000 + i) + String.fromCharCode(65 + (i % 26));
  const id = prefilledIdentityFor(pan);
  names.add(id.name);
  const d = new Date(id.dob);
  let a = now.getFullYear() - d.getFullYear();
  const mm = now.getMonth() - d.getMonth();
  if (mm < 0 || (mm === 0 && now.getDate() < d.getDate())) a--;
  if (isNaN(d.getTime()) || a < 18 || !id.address_line1 || !/^\d{6}$/.test(id.pincode)) {
    spreadOk = false;
    spreadDetail = `broke on ${pan}: age ${a}, ${id.pincode}`;
    break;
  }
}
check('400 PANs all yield complete adult identities', spreadOk, spreadDetail);
check('the name pool produces variety', names.size > 100, `${names.size} distinct names`);
check('odd input does not crash the generator', (() => {
  try {
    const id = prefilledIdentityFor('');
    return !!id.name && /^\d{6}$/.test(id.pincode);
  } catch (e) {
    return false;
  }
})());

/* ------------------------------------------------------------- 2. id wiring */
console.log();
console.log('='.repeat(72));
console.log(' 2. Wizard element ids: referenced by JS vs present in HTML');
console.log('='.repeat(72));

const htmlIds = new Set(
  [...HTML.matchAll(/id="([^"]+)"/g)].map(match => match[1])
);

// Every id the onboarding code looks up.
const obStart = APP.indexOf('let obUserData = {');
const obEnd = APP.indexOf('/* =======================================================\n   ORDER CONFIRMATION MODAL HELPERS');
const wizardSource = APP.slice(obStart, obEnd > 0 ? obEnd : APP.length);

const referenced = new Set(
  [...wizardSource.matchAll(/getElementById\(\s*['"]([^'"]+)['"]\s*\)/g)].map(m => m[1])
);
// Dynamic lookups written as template strings, e.g. `obStep-${i}`.
for (let i = 1; i <= 6; i++) {
  referenced.add(`obStep-${i}`);
  referenced.add(`obStepIndicator-${i}`);
}
// Connectors sit BETWEEN steps, so the last step correctly has none.
for (let i = 1; i <= 5; i++) {
  referenced.add(`obConnector-${i}`);
}

const missing = [...referenced].filter(id => !htmlIds.has(id)).sort();
check('every wizard id referenced by JS exists in index.html',
  missing.length === 0,
  missing.length ? `missing: ${missing.join(', ')}` : `${referenced.size} ids checked`);

// Ids that must no longer exist anywhere (removed OTP / username / password / age).
const shouldBeGone = ['obInputUsername', 'obInputPassword', 'obInputAge', 'obUsernameStatus',
  'smsPushBanner', 'smsOtpCode', 'obDisplayPhone', 'otp-1', 'otp-2', 'otp-3', 'otp-4'];
const stillThere = shouldBeGone.filter(id => htmlIds.has(id));
check('removed fields are gone from the markup', stillThere.length === 0,
  stillThere.length ? `still present: ${stillThere.join(', ')}` : 'checked ' + shouldBeGone.length);

// The new surfaces must exist.
const mustExist = ['obReviewName', 'obReviewPhone', 'obReviewEmail', 'obReviewPan', 'obReviewBank',
  'obPendingView', 'obPendingText', 'obPendingRef', 'obPendingName', 'obPendingEmail',
  'obActiveView', 'obPinView', 'obConsentTick', 'obCreatedBankBalance',
  'obInputAddress1', 'obInputAddress2', 'obInputCity', 'obInputState', 'obInputPincode',
  'obInputPin', 'obInputPinConfirm'];
const absent = mustExist.filter(id => !htmlIds.has(id));
check('all new wizard surfaces exist', absent.length === 0,
  absent.length ? `missing: ${absent.join(', ')}` : 'checked ' + mustExist.length);

// Functions the markup calls by name must be defined in app.js.
const JS_KEYWORDS = new Set(['if', 'for', 'while', 'return', 'switch', 'typeof', 'catch',
  'function', 'new', 'delete', 'void', 'do', 'else', 'try', 'throw', 'case', 'var', 'let',
  'const', 'this', 'event', 'window', 'document']);
const calledFromHtml = [...HTML.matchAll(/on(?:click|input|change)="([A-Za-z_][A-Za-z0-9_]*)\(/g)]
  .map(m => m[1])
  .filter(fn => !JS_KEYWORDS.has(fn));
const undefinedHandlers = [...new Set(calledFromHtml)]
  .filter(fn => !new RegExp(`(function\\s+${fn}\\b|${fn}\\s*=\\s*(async\\s*)?\\()`, 'm').test(APP))
  .sort();
check('every onclick/oninput handler in index.html is defined in app.js',
  undefinedHandlers.length === 0,
  undefinedHandlers.length ? `undefined: ${undefinedHandlers.join(', ')}` : `${new Set(calledFromHtml).size} handlers checked`);

// Step structure must be internally consistent.
let stepsOk = true;
let stepsDetail = '';
for (let i = 1; i <= 6; i++) {
  const containers = (HTML.match(new RegExp(`id="obStep-${i}"`, 'g')) || []).length;
  const indicators = (HTML.match(new RegExp(`id="obStepIndicator-${i}"`, 'g')) || []).length;
  if (containers !== 1 || indicators !== 1) {
    stepsOk = false;
    stepsDetail += `step${i}: containers=${containers} indicators=${indicators} `;
  }
}
check('step containers and indicators are 1:1', stepsOk, stepsDetail);
check('no 7th step indicator is referenced', !APP.includes('obStepIndicator-7'));

/* ------------------------------------------------------ 3. welcome screen */
console.log();
console.log('='.repeat(72));
console.log(' 3. First-run welcome screen');
console.log('='.repeat(72));

check('welcome pane exists in the markup', htmlIds.has('welcomePane'));
check('pane is visible by default (no inline display:none)',
  !/id="welcomePane"[^>]*style="[^"]*display:\s*none/.test(HTML));
check('head script can pre-dismiss it for returning users',
  HTML.includes('welcome-dismissed') && HTML.includes("classList.add('welcome-dismissed')"));
check('mobile app bar is hidden behind the takeover',
  /html:not\(\.welcome-dismissed\)\s*\.mobile-bottom-bar/.test(HTML));

const welcomeHandlers = ['startWelcomeOnboarding', 'skipWelcomeToGuest', 'openLoginModal', 'enterGuestMode'];
const missingHandlers = welcomeHandlers.filter(fn =>
  !new RegExp(`function\\s+${fn}\\b`).test(APP));
check('all welcome actions are defined', missingHandlers.length === 0,
  missingHandlers.length ? `missing: ${missingHandlers.join(', ')}` : welcomeHandlers.join(', '));

// Only enterGuestMode may SET the flag. Applying the class alone happens in the
// boot paths (fetchCurrentUser), which is display state, not a stored choice.
const flagWrites = (APP.match(/setItem\('stoxify_guest_mode'/g) || []).length;
check('guest mode flag is written in exactly one place (extracted, not duplicated)',
  flagWrites === 1, `${flagWrites} setItem('stoxify_guest_mode') occurrence(s)`);
const enterGuestBlock = APP.match(/function enterGuestMode\(\)\s*\{[\s\S]*?\n\}/);
check('enterGuestMode is that place',
  !!enterGuestBlock && enterGuestBlock[0].includes("setItem('stoxify_guest_mode'"));
check('logoutUser delegates to it', /function logoutUser\(\)\s*\{\s*enterGuestMode\(\);/.test(APP));

// Logging in from '/', the welcome screen's own path, does not navigate (the
// success handler only redirects from /onboarding or /login), so the login path
// must dismiss the takeover itself.
check('successful login dismisses the welcome takeover',
  /closeLoginModal\(\);[\s\S]{0,400}hideWelcomePane\(\)/.test(APP));
check('the delete path also delegates', /enterGuestMode\(\);\s*\n\s*state\.account/.test(APP));

// The gate must cover the landing routes only.
const GATE = "if ((path === '/' || path === '/explore') && !hasSessionOrGuest())";
check('gate covers the landing routes and requires no session/guest choice',
  APP.includes(GATE), APP.includes(GATE) ? '' : 'exact gate expression not found');
check('deep links are NOT gated',
  !APP.includes("'\\/onboarding' && !hasSessionOrGuest") &&
  !APP.includes("!hasSessionOrGuest() && path === '/onboarding'") &&
  !APP.includes("startsWith('/stock/') && !hasSessionOrGuest"));

// Exercise the REAL gate predicate against a stubbed localStorage.
const gateSrc = APP.match(/function hasSessionOrGuest\(\)\s*\{[\s\S]*?\n\}/);
check('hasSessionOrGuest found for behavioural test', !!gateSrc);
if (gateSrc) {
  const makeGate = new Function('localStorage', `${gateSrc[0]}; return hasSessionOrGuest;`);
  const cases = [
    // uid,            guest flag, expected "has a session/choice" => welcome hidden?
    [null,             null,       false, 'brand-new visitor sees the welcome screen'],
    ['STOX-123456',    null,       true,  'signed-in user skips it'],
    [null,             'true',     true,  'a guest who skipped never sees it again'],
    ['STOX-123456',    'true',     true,  'signed-in while flagged guest still skips it'],
    ['guest',          null,       false, 'the literal "guest" id is not a real session'],
    ['default',        null,       false, 'the legacy "default" id is not a real session'],
    [null,             'false',    false, 'an explicit "false" flag is not a choice']
  ];
  for (const [uid, flag, expected, label] of cases) {
    const store = {
      getItem: key => {
        if (key === 'stoxify_user_id') return uid;
        if (key === 'stoxify_guest_mode') return flag;
        return null;
      }
    };
    const actual = makeGate(store)();
    check(label, actual === expected, `hasSessionOrGuest=${actual}`);
  }
}

console.log();
console.log('='.repeat(72));
console.log(failures === 0 ? ' WIZARD CHECKS PASSED' : ` ${failures} FAILURE(S)`);
console.log('='.repeat(72));
process.exit(failures === 0 ? 0 : 1);
