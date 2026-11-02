"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different formulations) that must
pass, and named injected bugs that must be rejected for the intended reason.
Plain checks only, so the fixture also works under python -O.
"""
import ast
import importlib.util
import json
import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('grasp_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L18-grasp.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names}
require(imported <= {'math'}, 'kit imports beyond math: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
require('_Mismatch' in text and 'SPOILER BELOW' in text, 'kit needs _Mismatch and a spoiler banner')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name) < spoiler for name in
            ('safety_factor', 'min_squeeze', 'max_lift_accel', 'in_friction_cone',
             'retention_events')), 'starter functions must sit above the spoiler banner')
require(text.index('def _ref_events') > spoiler and text.index('_EVENT_CASES = ') > spoiler,
        'references and case tables must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('grasp_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter, 'unimplemented starter must report failure')
require(sum('not implemented yet' in line for line in starter) == 5 and len(starter) == 5,
        'starter NotImplementedError must collapse to one line per function')


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def entry(structure, names, args):
    return {'structure': structure,
            'inputs': {name: [[dec(x) for x in row] for row in value]
                       if name == 'samples' else dec(value)
                       for name, value in zip(names, args)}}


expected_samples = (
    [entry('grasp.safety-factor@1', ('m', 'mu', 'n', 'a'), a) for a, _ in kit._FACTOR_CASES]
    + [entry('grasp.min-squeeze@1', ('m', 'mu', 'a'), a) for a, _ in kit._SQUEEZE_CASES]
    + [entry('grasp.max-lift-accel@1', ('m', 'mu', 'n'), a) for a, _ in kit._ACCEL_CASES]
    + [entry('grasp.friction-cone@1', ('fn', 'ft', 'mu'), a) for a, _ in kit._CONE_CASES]
    + [entry('grasp.retention-events@1', ('samples', 'mu', 'contact', 'window'), a)
       for a, _ in kit._EVENT_CASES])
samples = json.loads((root / 'content/labs/L18-grasp.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L18-grasp'], 'samples must hold only L18-grasp')
require(samples['kits']['L18-grasp'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')

# ---- independent exact-rational oracle agrees with the kit tables ----
G = Fraction(981, 100)
for (m, mu, n, a), want in kit._FACTOR_CASES:
    exact = 2*Fraction(repr(mu))*Fraction(repr(n))/(Fraction(repr(m))*(G + Fraction(repr(a))))
    require(abs(float(exact) - kit._ref_factor(m, mu, n, a)) < 1e-12, 'factor oracle')
for (m, mu, a), want in kit._SQUEEZE_CASES:
    exact = Fraction(repr(m))*(G + Fraction(repr(a)))/(2*Fraction(repr(mu)))
    require(abs(float(exact) - kit._ref_squeeze(m, mu, a)) < 1e-9, 'squeeze oracle')
for (m, mu, n), want in kit._ACCEL_CASES:
    exact = 2*Fraction(repr(mu))*Fraction(repr(n))/Fraction(repr(m)) - G
    require(abs(float(exact) - kit._ref_accel(m, mu, n)) < 1e-9, 'accel oracle')
for (fn, ft, mu), want in kit._CONE_CASES:
    exact = Fraction(repr(fn)) >= 0 and abs(Fraction(repr(ft))) <= Fraction(repr(mu))*Fraction(repr(fn))
    require(exact == want, 'cone oracle')
for args, want in kit._EVENT_CASES:
    require(kit._ref_events(*args) == want, 'event table disagrees with the reference')


# ---- author reference implementation ----
def finite(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError


def v_m(m): finite(m, 1e-300, 100)
def v_mu(mu): finite(mu, 0.01, 5)
def v_n(n): finite(n, 0, 10000)
def v_a(a): finite(a, -5, 50)


def v_trace(samples, mu, contact, window):
    if not isinstance(samples, (list, tuple)) or not 1 <= len(samples) <= 1000:
        raise ValueError
    for s in samples:
        if not isinstance(s, (list, tuple)) or len(s) != 3:
            raise ValueError
        if type(s[0]) is not int or s[0] not in (0, 1):
            raise ValueError
        finite(s[1], 0, 1000)
        finite(s[2], -1000, 1000)
    v_mu(mu)
    finite(contact, 1e-300, 1000)
    if type(window) is not int or not 1 <= window <= 1000:
        raise ValueError


def safety_factor(m, mu, n, a):
    v_m(m); v_mu(mu); v_n(n); v_a(a)
    return 2*mu*n/(m*(9.81 + a))


def min_squeeze(m, mu, a):
    v_m(m); v_mu(mu); v_a(a)
    return m*(9.81 + a)/(2*mu)


def max_lift_accel(m, mu, n):
    v_m(m); v_mu(mu); v_n(n)
    return 2*mu*n/m - 9.81


def in_friction_cone(fn, ft, mu):
    finite(fn, -1000, 1000); finite(ft, -1000, 1000); v_mu(mu)
    return fn >= 0 and abs(ft) <= mu*fn


FLAGS = dict(strict_contact=False, slip_ge=False, level_slip=False, no_rearm=False,
             empty_off=0, empty_before_contact=False, release_every_open=False,
             release_when_empty=False, no_lost=False, no_release=False, slip_on_lost=False,
             global_counter=False, slip_signed=False, slip_first=False, contact_in_open=False,
             names_only=False, one_based=False, mutate=False, count_window_from_zero=False,
             empty_ignores_run=False, keep_slip_on_release=False)


def machine(samples, mu, contact, window, **over):
    f = dict(FLAGS, **over)
    events, on, slipping, c, had, was_open, ever_slipped = [], False, False, 0, False, False, False
    for k, (cmd, fn, ft) in enumerate(samples):
        emitted = []
        if cmd == 1:
            first = not was_open
            if f['release_every_open'] or (first and (on or f['release_when_empty'])):
                if not f['no_release']:
                    emitted.append('release')
            if f['contact_in_open'] and not on and fn >= contact:
                emitted.insert(0, 'contact')
            on = had = False
            slipping = slipping if f['keep_slip_on_release'] else False
            if not f['global_counter']:
                c = 0
            was_open = True
            events.extend((k, name) for name in emitted)
            continue
        was_open = False
        if c == 0:
            had = False
        c += 1
        lost = False
        if f['empty_before_contact'] and not on and c == window + f['empty_off'] and not had:
            emitted.append('empty')
        hit = fn > contact if f['strict_contact'] else fn >= contact
        if not on and hit:
            emitted.append('contact')
            on, had = True, True
        elif on and fn < contact and not f['no_lost']:
            emitted.append('lost')
            on = slipping = False
            lost = True
        if (on and not lost) or (lost and f['slip_on_lost']):
            measure = ft if f['slip_signed'] else abs(ft)
            out = measure >= mu*fn if f['slip_ge'] else measure > mu*fn
            if out:
                if f['level_slip'] or (not slipping and not (f['no_rearm'] and ever_slipped)):
                    emitted.append('slip')
                slipping, ever_slipped = True, True
            else:
                slipping = False
        if not f['empty_before_contact'] and not on and (not had or f['empty_ignores_run']) \
                and c == window + f['empty_off']:
            emitted.append('empty')
        if f['slip_first'] and 'slip' in emitted and 'contact' in emitted:
            emitted.remove('slip')
            emitted.insert(0, 'slip')
        events.extend((k, name) for name in emitted)
    shift = 1 if f['one_based'] else 0
    if f['names_only']:
        return [name for _, name in events]
    return [(k + shift, name) for k, name in events]


def retention_events(samples, mu, contact, window):
    v_trace(samples, mu, contact, window)
    return machine(samples, mu, contact, window)


refs = {'safety_factor': safety_factor, 'min_squeeze': min_squeeze,
        'max_lift_accel': max_lift_accel, 'in_friction_cone': in_friction_cone,
        'retention_events': retention_events}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


require(run_with({}) == [], 'author reference must pass: ' + str(run_with({})[:3]))


def ev(**flags):
    def f(samples, mu, contact, window):
        v_trace(samples, mu, contact, window)
        return machine(samples, mu, contact, window, **flags)
    return f


# ---- valid alternatives (different formulations) ----
def factor_two_step(m, mu, n, a):
    v_m(m); v_mu(mu); v_n(n); v_a(a)
    capacity = mu*n + mu*n
    demand = m*9.81 + m*a
    return capacity/demand


def squeeze_via_total(m, mu, a):
    """Total squeeze 2n = m(g+a)/mu, then split between the pads."""
    v_m(m); v_mu(mu); v_a(a)
    return [(m*9.81 + m*a)/mu/2]


def accel_force_form(m, mu, n):
    v_m(m); v_mu(mu); v_n(n)
    return (2*mu*n - m*9.81)/m


def cone_tolerant(fn, ft, mu):
    finite(fn, -1000, 1000); finite(ft, -1000, 1000); v_mu(mu)
    if fn < 0:
        return False
    return -mu*fn*(1 + 1e-12) <= ft <= mu*fn*(1 + 1e-12)


def events_separate_passes(samples, mu, contact, window):
    """Contact/lost, slip, empty and release as four independent passes, merged by index."""
    v_trace(samples, mu, contact, window)
    n = len(samples)
    contact_state, rows = [False]*n, []
    on = False
    for k, (cmd, fn, ft) in enumerate(samples):
        if cmd == 1:
            if on and (k == 0 or samples[k-1][0] == 0):
                rows.append((k, 3, 'release'))
            on = False
        elif not on and fn >= contact:
            on = True
            rows.append((k, 0, 'contact'))
        elif on and fn < contact:
            on = False
            rows.append((k, 0, 'lost'))
        contact_state[k] = on
    armed = True
    for k, (cmd, fn, ft) in enumerate(samples):
        if cmd == 1 or not contact_state[k]:
            armed = True
            continue
        if abs(ft) > mu*fn:
            if armed:
                rows.append((k, 1, 'slip'))
            armed = False
        else:
            armed = True
    start, had = 0, False
    for k, (cmd, fn, ft) in enumerate(samples):
        if cmd == 1:
            start = k + 1
            had = False
            continue
        if contact_state[k] or any(r[0] == k and r[2] in ('contact', 'lost') for r in rows):
            had = had or contact_state[k]
            if any(r[0] == k and r[2] == 'contact' for r in rows):
                had = True
        if k - start + 1 == window and not had and not contact_state[k]:
            rows.append((k, 2, 'empty'))
    rows.sort()
    return tuple((k, name) for k, _, name in rows)


def events_dict_states(samples, mu, contact, window):
    """Same observer written as a string-state machine returning lists."""
    v_trace(samples, mu, contact, window)
    state, out, run_len, armed = 'idle', [], 0, True
    for k, row in enumerate(samples):
        cmd, fn, ft = row[0], row[1], row[2]
        if cmd == 1:
            if state in ('holding', 'slipping') and (k == 0 or samples[k-1][0] == 0):
                out.append([k, 'release'])
            state, run_len = 'open' if state == 'idle' and run_len == 0 and k > 0 and \
                samples[k-1][0] == 1 else 'idle', 0
            if k > 0 and samples[k-1][0] == 0:
                state = 'idle'
            continue
        run_len += 1
        if state == 'dropped':
            state = 'dropped'
        if state in ('idle', 'dropped', 'open'):
            if fn >= contact:
                out.append([k, 'contact'])
                state = 'holding'
            elif state == 'idle' and run_len == window:
                out.append([k, 'empty'])
        elif fn < contact:
            out.append([k, 'lost'])
            state = 'dropped'
            continue
        if state in ('holding', 'slipping'):
            if abs(ft) > mu*fn:
                if state == 'holding':
                    out.append([k, 'slip'])
                state = 'slipping'
            else:
                state = 'holding'
    return out


alternatives = [
    ('two-step capacity/demand factor, order of operations', {'safety_factor': factor_two_step}),
    ('squeeze via the total squeeze, returns a number', {'min_squeeze': lambda *a: squeeze_via_total(*a)[0]}),
    ('acceleration from the force form', {'max_lift_accel': accel_force_form}),
    ('closed cone with a 1e-12 relative tolerance', {'in_friction_cone': cone_tolerant}),
    ('events as four independent passes merged by index', {'retention_events': events_separate_passes}),
    ('events as a string-state machine returning lists', {'retention_events': events_dict_states}),
    ('squeeze as the reciprocal of force per newton', {'min_squeeze': lambda m, mu, a: (
        v_m(m), v_mu(mu), v_a(a), 1/(2*mu/(m*(9.81 + a))))[-1]}),
    ('events given tuple output', {'retention_events': lambda *a: tuple(
        tuple(e) for e in retention_events(*a))}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject of valid alternative: ' + label + ': ' + str(result[:2]))


# ---- injected bugs, each rejected by a failure line for the intended function ----
def is_real(x):
    return type(x) in (int, float) and math.isfinite(x)


def lenient(good, test, fallback):
    """Return `fallback` instead of ValueError when `test(args)` marks an invalid-input probe."""
    def wrapped(*args):
        if test(*args):
            return fallback
        return good(*args)
    return wrapped


mutants = [
    ('safety factor with one pad only', 'safety_factor', {'safety_factor': lambda m, mu, n, a: (
        v_m(m), v_mu(mu), v_n(n), v_a(a), mu*n/(m*(9.81 + a)))[-1]}),
    ('safety factor forgets the mass', 'safety_factor', {'safety_factor': lambda m, mu, n, a: (
        v_m(m), v_mu(mu), v_n(n), v_a(a), 2*mu*n/(9.81 + a))[-1]}),
    ('g = 9.8', 'safety_factor', {'safety_factor': lambda m, mu, n, a: (
        v_m(m), v_mu(mu), v_n(n), v_a(a), 2*mu*n/(m*(9.8 + a)))[-1]}),
    ('g = 10', 'min_squeeze', {'min_squeeze': lambda m, mu, a: (
        v_m(m), v_mu(mu), v_a(a), m*(10 + a)/(2*mu))[-1]}),
    ('acceleration ignored in the factor', 'safety_factor', {'safety_factor': lambda m, mu, n, a: (
        v_m(m), v_mu(mu), v_n(n), v_a(a), 2*mu*n/(m*9.81))[-1]}),
    ('acceleration subtracted (g - a)', 'safety_factor', {'safety_factor': lambda m, mu, n, a: (
        v_m(m), v_mu(mu), v_n(n), v_a(a), 2*mu*n/(m*(9.81 - a)))[-1]}),
    ('factor inverted (demand over capacity)', 'safety_factor', {'safety_factor': lambda m, mu, n, a: (
        v_m(m), v_mu(mu), v_n(n), v_a(a), (m*(9.81 + a)/(2*mu*n)) if n else 0.0)[-1]}),
    ('acceleration not multiplied by the mass', 'safety_factor', {'safety_factor': lambda m, mu, n, a: (
        v_m(m), v_mu(mu), v_n(n), v_a(a), 2*mu*n/(m*9.81 + a))[-1]}),
    ('squeeze forgets the two pads', 'min_squeeze', {'min_squeeze': lambda m, mu, a: (
        v_m(m), v_mu(mu), v_a(a), m*(9.81 + a)/mu)[-1]}),
    ('squeeze multiplies by mu', 'min_squeeze', {'min_squeeze': lambda m, mu, a: (
        v_m(m), v_mu(mu), v_a(a), m*(9.81 + a)*mu/2)[-1]}),
    ('squeeze forgets gravity', 'min_squeeze', {'min_squeeze': lambda m, mu, a: (
        v_m(m), v_mu(mu), v_a(a), m*a/(2*mu))[-1]}),
    ('squeeze with the acceleration sign flipped', 'min_squeeze', {'min_squeeze': lambda m, mu, a: (
        v_m(m), v_mu(mu), v_a(a), m*(9.81 - a)/(2*mu))[-1]}),
    ('max acceleration forgets gravity', 'max_lift_accel', {'max_lift_accel': lambda m, mu, n: (
        v_m(m), v_mu(mu), v_n(n), 2*mu*n/m)[-1]}),
    ('max acceleration as a ratio to g', 'max_lift_accel', {'max_lift_accel': lambda m, mu, n: (
        v_m(m), v_mu(mu), v_n(n), 2*mu*n/(m*9.81) - 1)[-1]}),
    ('max acceleration forgets the two pads', 'max_lift_accel', {'max_lift_accel': lambda m, mu, n: (
        v_m(m), v_mu(mu), v_n(n), mu*n/m - 9.81)[-1]}),
    ('max acceleration clamped at zero', 'max_lift_accel', {'max_lift_accel': lambda m, mu, n: (
        v_m(m), v_mu(mu), v_n(n), max(0.0, 2*mu*n/m - 9.81))[-1]}),
    ('cone edge treated as outside (strict)', 'in_friction_cone', {'in_friction_cone': lambda fn, ft, mu: (
        finite(fn, -1000, 1000), finite(ft, -1000, 1000), v_mu(mu), fn > 0 and abs(ft) < mu*fn)[-1]}),
    ('cone without abs on the tangential force', 'in_friction_cone', {'in_friction_cone': lambda fn, ft, mu: (
        finite(fn, -1000, 1000), finite(ft, -1000, 1000), v_mu(mu), fn >= 0 and ft <= mu*fn)[-1]}),
    ('cone accepts a pulling pad', 'in_friction_cone', {'in_friction_cone': lambda fn, ft, mu: (
        finite(fn, -1000, 1000), finite(ft, -1000, 1000), v_mu(mu), abs(ft) <= mu*abs(fn))[-1]}),
    ('cone with mu and fn swapped', 'in_friction_cone', {'in_friction_cone': lambda fn, ft, mu: (
        finite(fn, -1000, 1000), finite(ft, -1000, 1000), v_mu(mu), fn >= 0 and abs(ft) <= fn/mu)[-1]}),
    ('cone with the two-pad capacity', 'in_friction_cone', {'in_friction_cone': lambda fn, ft, mu: (
        finite(fn, -1000, 1000), finite(ft, -1000, 1000), v_mu(mu), fn >= 0 and abs(ft) <= 2*mu*fn)[-1]}),
    ('cone returns 1/0 instead of a bool', 'in_friction_cone', {'in_friction_cone': lambda fn, ft, mu: int(
        in_friction_cone(fn, ft, mu))}),
    ('contact needs fn strictly above threshold', 'retention_events', {'retention_events': ev(strict_contact=True)}),
    ('slip at the closed cone edge', 'retention_events', {'retention_events': ev(slip_ge=True)}),
    ('slip repeated on every outside sample', 'retention_events', {'retention_events': ev(level_slip=True)}),
    ('slip reported only once, never re-armed', 'retention_events', {'retention_events': ev(no_rearm=True)}),
    ('slip uses the signed tangential force', 'retention_events', {'retention_events': ev(slip_signed=True)}),
    ('slip evaluated on the lost sample', 'retention_events', {'retention_events': ev(slip_on_lost=True)}),
    ('empty one sample late', 'retention_events', {'retention_events': ev(empty_off=1)}),
    ('empty one sample early', 'retention_events', {'retention_events': ev(empty_off=-1)}),
    ('empty decided before contact (both reported)', 'retention_events', {'retention_events': ev(empty_before_contact=True)}),
    ('empty reported even after a contact in the run', 'retention_events', {'retention_events': ev(empty_ignores_run=True)}),
    ('closed-run counter never reset at open', 'retention_events', {'retention_events': ev(global_counter=True)}),
    ('release on every open sample', 'retention_events', {'retention_events': ev(release_every_open=True)}),
    ('release even when nothing is held', 'retention_events', {'retention_events': ev(release_when_empty=True)}),
    ('slip state not cleared on release', 'retention_events', {'retention_events': ev(keep_slip_on_release=True)}),
    ('release never reported', 'retention_events', {'retention_events': ev(no_release=True)}),
    ('lost never reported', 'retention_events', {'retention_events': ev(no_lost=True)}),
    ('contact reported while commanded open', 'retention_events', {'retention_events': ev(contact_in_open=True)}),
    ('slip listed before contact at one index', 'retention_events', {'retention_events': ev(slip_first=True)}),
    ('event names only, no index', 'retention_events', {'retention_events': ev(names_only=True)}),
    ('1-based event index', 'retention_events', {'retention_events': ev(one_based=True)}),
    ('observer sorts the caller samples', 'retention_events', {'retention_events': lambda s, mu, c, w: (
        v_trace(s, mu, c, w), s.sort(key=lambda r: r[1]) if isinstance(s, list) else None,
        machine(s, mu, c, w))[-1]}),
    ('bool m accepted', 'invalid safety_factor(m=True', {'safety_factor': lenient(
        safety_factor, lambda m, *a: type(m) is bool, 1.0)}),
    ('mu = 0 accepted', 'invalid min_squeeze(mu=0.0', {'min_squeeze': lenient(
        min_squeeze, lambda m, mu, a: mu == 0, 1.0)}),
    ('a below -g accepted', 'invalid safety_factor(a=-5.01', {'safety_factor': lenient(
        safety_factor, lambda m, mu, n, a: is_real(a) and a < -5, 1.0)}),
    ('negative n accepted', 'invalid max_lift_accel(n=-0.01', {'max_lift_accel': lenient(
        max_lift_accel, lambda m, mu, n: is_real(n) and n < 0, 1.0)}),
    ('NaN ft accepted by the cone', 'invalid in_friction_cone(ft=nan', {'in_friction_cone': lenient(
        in_friction_cone, lambda fn, ft, mu: type(ft) is float and ft != ft, True)}),
    ('float window accepted', 'invalid retention_events(window=2.0', {'retention_events': lenient(
        retention_events, lambda s, mu, c, w: type(w) is float, [])}),
    ('cmd = 2 accepted', 'invalid retention_events(samples=[(2', {'retention_events': lenient(
        retention_events, lambda s, *a: isinstance(s, list) and any(
            isinstance(r, tuple) and r[0] == 2 for r in s), [])}),
    ('bool cmd accepted', 'invalid retention_events(samples=[(True', {'retention_events': lenient(
        retention_events, lambda s, *a: isinstance(s, list) and any(
            isinstance(r, tuple) and type(r[0]) is bool for r in s), [])}),
    ('negative trace force accepted', 'invalid retention_events(samples=[(0, -0.1', {'retention_events': lenient(
        retention_events, lambda s, *a: isinstance(s, list) and any(
            isinstance(r, tuple) and len(r) == 3 and is_real(r[1]) and r[1] < 0 for r in s), [])}),
    ('empty trace accepted', 'invalid retention_events(samples=[]', {'retention_events': lenient(
        retention_events, lambda s, *a: isinstance(s, list) and not s, [])}),
    ('n = 0 rejected as over-strict', 'safety_factor 3', {'safety_factor': lambda m, mu, n, a: (
        (_ for _ in ()).throw(ValueError()) if n == 0 else safety_factor(m, mu, n, a))}),
    ('integer inputs rejected', 'min_squeeze', {'min_squeeze': lambda m, mu, a: (
        (_ for _ in ()).throw(ValueError()) if type(m) is int else min_squeeze(m, mu, a))}),
    ('mu = 0.01 rejected as over-strict', 'min_squeeze', {'min_squeeze': lambda m, mu, a: (
        (_ for _ in ()).throw(ValueError()) if mu == 0.01 else min_squeeze(m, mu, a))}),
]
require(len(mutants) >= 30, 'need at least 30 mutants')
for label, prefix, over in mutants:
    result = run_with(over)
    require(result, 'false accept: ' + label)
    require(any(line.startswith(prefix) for line in result),
            'mutant rejected for the wrong reason: ' + label + ' -> ' + result[0])
print('Grasp kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
