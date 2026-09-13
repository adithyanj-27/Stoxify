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

console.log();
console.log('='.repeat(72));
console.log(failures === 0 ? ' WIZARD CHECKS PASSED' : ` ${failures} FAILURE(S)`);
console.log('='.repeat(72));
process.exit(failures === 0 ? 0 : 1);
