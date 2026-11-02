"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative controllers (different anti-windup methods and
formulations) that must pass, and named injected bugs that must be rejected.
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
        raise SystemExit('pid_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L04-pid.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names}
imported |= {node.module.split('.')[0] for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom) and node.module}
require(imported <= {'math'}, 'kit imports beyond math: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name) < spoiler
            for name in ('p_step', 'pi_step', 'simulate', 'step_metrics')),
        'starter functions must sit above the spoiler banner')
require(text.index('def _oracle_pi') > spoiler, 'oracle must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('pid_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
require(kit.self_check(), 'unimplemented starter must report failure')


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def entry(structure, names, args):
    return {'structure': structure,
            'inputs': {name: [dec(v) for v in value] if isinstance(value, (list, tuple))
                       else dec(value) for name, value in zip(names, args)}}


expected_samples = (
    [entry('pid.p-step@1', ('y', 'r', 'kp', 'limit', 'h', 'd'), args)
     for args, _ in kit._P_CASES]
    + [entry('pid.pi-step@1', ('y', 'r', 'integral', 'kp', 'ki', 'limit', 'h', 'd'), args)
       for args, _ in kit._PI_CASES]
    + [entry('pid.simulate@1', ('y0', 'r', 'kp', 'ki', 'limit', 'h', 'steps', 'd'), case[1])
       for case in kit._SIM_CASES]
    + [entry('pid.step-metrics@1', ('outputs', 'y0', 'r', 'band'), args)
       for args, _ in kit._METRIC_CASES]
    + [entry('pid.unreachable-recovery@1',
             ('y0', 'r', 'kp', 'ki', 'limit', 'h', 'd_unreachable', 'steps_unreachable',
              'd_reachable', 'steps_reachable'), case[:10]) for case in kit._CHAINS])
samples = json.loads((root / 'content/labs/L04-pid.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L04-pid'], 'samples must hold only L04-pid')
require(samples['kits']['L04-pid'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')


# ---- author reference implementation (conditional integration) ----
def finite(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError


def positive(value, high):
    finite(value, 0, high)
    if value <= 0:
        raise ValueError


def common(y, r, kp, limit, h, d):
    finite(y, -100, 100)
    finite(r, -100, 100)
    finite(kp, 0, 100)
    positive(limit, 100)
    positive(h, 1)
    finite(d, -100, 100)


def clip(v, limit):
    return max(-limit, min(limit, v))


def p_step(y, r, kp, limit, h, d=0):
    common(y, r, kp, limit, h, d)
    u = clip(kp*(r - y), limit)
    return (u, y + h*(u + d))


def pi_validate(y, r, integral, kp, ki, limit, h, d):
    common(y, r, kp, limit, h, d)
    finite(integral, -1e9, 1e9)
    finite(ki, 0, 100)


def core_hold(y, r, integral, kp, ki, limit, h, d):
    """Unvalidated update shared by pi_step and simulate (conditional integration)."""
    e = r - y
    v = kp*e + ki*integral
    u = clip(v, limit)
    pushing = (v > limit and e > 0) or (v < -limit and e < 0)
    return (u, y + h*(u + d), integral if pushing else integral + h*e)


def make_pi(core):
    def pi(y, r, integral, kp, ki, limit, h, d=0):
        pi_validate(y, r, integral, kp, ki, limit, h, d)
        return core(y, r, integral, kp, ki, limit, h, d)
    return pi


def sim_validate(y0, r, kp, ki, limit, h, steps, d):
    pi_validate(y0, r, 0, kp, ki, limit, h, d)
    if type(steps) is not int or not 1 <= steps <= 1000:
        raise ValueError


def make_sim(core):
    def run(y0, r, kp, ki, limit, h, steps, d=0):
        sim_validate(y0, r, kp, ki, limit, h, steps, d)
        y, integral, trace = y0, 0, []
        for _ in range(steps):
            u, y, integral = core(y, r, integral, kp, ki, limit, h, d)
            trace.append((y, u))
        return trace
    return run


pi_step = make_pi(core_hold)
simulate = make_sim(core_hold)


def metrics_validate(outputs, y0, r, band):
    if not isinstance(outputs, (list, tuple)) or not 1 <= len(outputs) <= 1000:
        raise ValueError
    for value in outputs:
        finite(value, -1e6, 1e6)
    finite(y0, -100, 100)
    finite(r, -100, 100)
    positive(band, 100)


def step_metrics(outputs, y0, r, band):
    metrics_validate(outputs, y0, r, band)
    ys = [y0, *outputs]
    settle = None
    for k in range(len(ys) - 1, -1, -1):
        if abs(ys[k] - r) > band:
            break
        settle = k
    s = (r > y0) - (r < y0)
    overshoot = max([0] + [s*(y - r) for y in outputs]) if s else 0
    return (settle, overshoot)


refs = {'p_step': p_step, 'pi_step': pi_step, 'simulate': simulate,
        'step_metrics': step_metrics}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


# ---- valid alternatives ----
def pi_mathworks_clamp(y, r, integral, kp, ki, limit, h, d=0):
    """Integrate first, then undo it when saturated and sign(e) == sign(u)."""
    pi_validate(y, r, integral, kp, ki, limit, h, d)
    e = r - y
    v = kp*e + ki*integral
    u = clip(v, limit)
    candidate = integral + h*e
    if u != v and e != 0 and math.copysign(1, e) == math.copysign(1, u):
        candidate = integral
    return [u, y + h*u + h*d, candidate]


def simulate_inline(y0, r, kp, ki, limit, h, steps, d=0):
    """Own loop with the same clamping rule, never calling pi_step."""
    sim_validate(y0, r, kp, ki, limit, h, steps, d)
    y, integral, trace = y0, 0, []
    for _ in range(steps):
        e = r - y
        v = kp*e + ki*integral
        u = clip(v, limit)
        if not (u != v and e*u > 0):
            integral += h*e
        y += h*(u + d)
        trace.append([y, u])
    return trace


def core_tracking(y, r, integral, kp, ki, limit, h, d):
    """Back-calculation with full tracking: the integral jumps to I_t."""
    e = r - y
    v = kp*e + ki*integral
    u = clip(v, limit)
    if u == v:
        nxt = integral + h*e
    else:
        tracked = integral if ki == 0 else (u - kp*e)/ki
        nxt = tracked if u*e > 0 else tracked + h*e
    return (u, y + h*(u + d), nxt)


def core_backcalc(y, r, integral, kp, ki, limit, h, d):
    """Back-calculation dI = h*e + c*(u - v)/ki with c = 0.5, guarded while pushing."""
    e = r - y
    v = kp*e + ki*integral
    u = clip(v, limit)
    if u == v:
        return (u, y + h*(u + d), integral + h*e)
    if ki == 0:
        return (u, y + h*(u + d), integral)
    nxt = integral + h*e + 0.5*(u - v)/ki
    if e*u > 0:
        nxt = min(integral, nxt) if u > 0 else max(integral, nxt)
    return (u, y + h*(u + d), nxt)


def simulate_tuple(y0, r, kp, ki, limit, h, steps, d=0):
    return tuple(tuple(pair) for pair in make_sim(core_backcalc)(y0, r, kp, ki, limit, h, steps, d))


def metrics_forward(outputs, y0, r, band):
    """Forward scan: one past the last out-of-band sample; list result."""
    metrics_validate(outputs, y0, r, band)
    ys = list((y0,) + tuple(outputs))
    last_out = max([k for k, y in enumerate(ys) if abs(y - r) > band], default=-1)
    settle = None if last_out == len(ys) - 1 else last_out + 1
    if r > y0:
        overshoot = max(0.0, max(outputs) - r)
    elif r < y0:
        overshoot = max(0.0, r - min(outputs))
    else:
        overshoot = 0.0
    return [settle, overshoot]


def p_fraction(y, r, kp, limit, h, d=0):
    """Exact rational arithmetic, converted back to float at the end."""
    common(y, r, kp, limit, h, d)
    F = Fraction
    u = max(-F(limit), min(F(limit), F(kp)*(F(r) - F(y))))
    return (float(u), float(F(y) + F(h)*(u + F(d))))


def pi_fraction(y, r, integral, kp, ki, limit, h, d=0):
    pi_validate(y, r, integral, kp, ki, limit, h, d)
    F = Fraction
    e = F(r) - F(y)
    v = F(kp)*e + F(ki)*F(integral)
    u = max(-F(limit), min(F(limit), v))
    hold = v != u and v*e > 0
    nxt = F(integral) if hold else F(integral) + F(h)*e
    return (float(u), float(F(y) + F(h)*(u + F(d))), float(nxt))


alternatives = [
    ('author conditional integration', {}),
    ('MathWorks-style clamping, list outputs, inline simulate',
     {'pi_step': pi_mathworks_clamp, 'simulate': simulate_inline}),
    ('full-tracking back-calculation, shared core in simulate',
     {'pi_step': make_pi(core_tracking), 'simulate': make_sim(core_tracking)}),
    ('guarded back-calculation, tuple trace, forward-scan metrics',
     {'pi_step': make_pi(core_backcalc), 'simulate': simulate_tuple,
      'step_metrics': metrics_forward}),
    ('exact Fraction arithmetic', {'p_step': p_fraction, 'pi_step': pi_fraction}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result))


# ---- injected bugs ----
def raw_pi(rule):
    """pi_step with full validation and a replaceable (u, y_next, integral_next) rule."""
    def step(y, r, integral, kp, ki, limit, h, d=0):
        pi_validate(y, r, integral, kp, ki, limit, h, d)
        e = r - y
        v = kp*e + ki*integral
        return rule(y, e, v, clip(v, limit), integral, kp, ki, limit, h, d)
    return step


def raw_p(rule):
    def step(y, r, kp, limit, h, d=0):
        common(y, r, kp, limit, h, d)
        return rule(y, r, kp, limit, h, d)
    return step


def raw_sim(body):
    def run(y0, r, kp, ki, limit, h, steps, d=0):
        sim_validate(y0, r, kp, ki, limit, h, steps, d)
        return body(y0, r, kp, ki, limit, h, steps, d)
    return run


def sim_no_feedback(y0, r, kp, ki, limit, h, steps, d):
    y, trace = y0, []
    for _ in range(steps):
        u, y, _ = core_hold(y, r, 0, kp, ki, limit, h, d)
        trace.append((y, u))
    return trace


def sim_pre_step(y0, r, kp, ki, limit, h, steps, d):
    y, integral, trace = y0, 0, []
    for _ in range(steps):
        before = y
        u, y, integral = core_hold(y, r, integral, kp, ki, limit, h, d)
        trace.append((before, u))
    return trace


def sim_naive(y0, r, kp, ki, limit, h, steps, d):
    y, integral, trace = y0, 0, []
    for _ in range(steps):
        e = r - y
        u = clip(kp*e + ki*integral, limit)
        integral += h*e
        y += h*(u + d)
        trace.append((y, u))
    return trace


def sim_p_only(y0, r, kp, ki, limit, h, steps, d):
    return simulate(y0, r, kp, 0, limit, h, steps, d)


def sim_integral_starts_at_error(y0, r, kp, ki, limit, h, steps, d):
    y, integral, trace = y0, r - y0, []
    for _ in range(steps):
        u, y, integral = core_hold(y, r, integral, kp, ki, limit, h, d)
        trace.append((y, u))
    return trace


def metrics_rule(rule):
    def run(outputs, y0, r, band):
        settle, overshoot = step_metrics(outputs, y0, r, band)
        return rule(outputs, y0, r, band, settle, overshoot)
    return run


def first_entry(outputs, y0, r, band, settle, overshoot):
    ys = [y0, *outputs]
    if settle is None:
        return (None, overshoot)
    return (next(k for k, y in enumerate(ys) if abs(y - r) <= band), overshoot)


def strict_band(outputs, y0, r, band):
    return step_metrics(outputs, y0, r, band*(1 - 1e-12))


def sorting(outputs, y0, r, band):
    result = step_metrics(outputs, y0, r, band)
    if isinstance(outputs, list):
        outputs.sort()
    return result


def accepts_when(check, function):
    """Full validation except one named gap: returns a plausible value instead."""
    def run(*args):
        if check(*args):
            return (0.0, 0.0, 0.0)[:2 if function in (p_step, step_metrics) else 3]
        return function(*args)
    return run


def floats_only(function):
    def run(*args):
        if not all(type(v) is float for v in args if not isinstance(v, (list, tuple))):
            raise ValueError
        return function(*args)
    return run


def is_real(v):
    return type(v) in (int, float) and math.isfinite(v)


def sim_revalidating(y0, r, kp, ki, limit, h, steps, d=0):
    """Calls the validating pi_step on every state, so intermediate |y| > 100 raises."""
    sim_validate(y0, r, kp, ki, limit, h, steps, d)
    y, integral, trace = y0, 0, []
    for _ in range(steps):
        u, y, integral = pi_step(y, r, integral, kp, ki, limit, h, d)
        trace.append((y, u))
    return trace


def strict_bound(position, bound):
    """Over-strict validation: also rejects a valid value beyond `bound`."""
    def wrap(function):
        def run(*args):
            value = args[position]
            if isinstance(value, (list, tuple)):
                if any(is_real(v) and abs(v) > bound for v in value):
                    raise ValueError
            elif is_real(value) and abs(value) > bound:
                raise ValueError
            return function(*args)
        return run
    return wrap


mutants = [
    ('error sign flipped (y - r)', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        clip(kp*(y - r), L), y + h*(clip(kp*(y - r), L) + d)))}),
    ('p_step forgot h', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        clip(kp*(r - y), L), y + clip(kp*(r - y), L) + d))}),
    ('p_step h applied twice', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        clip(kp*(r - y), L), y + h*h*(clip(kp*(r - y), L) + d)))}),
    ('clip the state instead of the command', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        kp*(r - y), clip(y + h*(kp*(r - y) + d), L)))}),
    ('no clip', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        kp*(r - y), y + h*(kp*(r - y) + d)))}),
    ('clip to [0, limit]', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        max(0, min(L, kp*(r - y))), y + h*(max(0, min(L, kp*(r - y))) + d)))}),
    ('clip only the upper limit', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        min(L, kp*(r - y)), y + h*(min(L, kp*(r - y)) + d)))}),
    ('disturbance ignored', {'p_step': raw_p(lambda y, r, kp, L, h, d: p_step(y, r, kp, L, h))}),
    ('disturbance inside the clip', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        clip(kp*(r - y) + d, L), y + h*clip(kp*(r - y) + d, L)))}),
    ('output speed clipped to +-100', {'p_step': raw_p(lambda y, r, kp, L, h, d: (
        p_step(y, r, kp, L, h, d)[0], max(-100, min(100, p_step(y, r, kp, L, h, d)[1]))))}),
    ('integral without h', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + h*(u + d), I if v != u and v*e > 0 else I + e))}),
    ('integral with h twice', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + h*(u + d), I if v != u and v*e > 0 else I + h*h*e))}),
    ('integral sign flipped', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + h*(u + d), I if v != u and v*e > 0 else I - h*e))}),
    ('command uses the updated integral', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        clip(v + ki*h*e, L), y + h*(clip(v + ki*h*e, L) + d), I + h*e))}),
    ('naive clamp with runaway integrator', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + h*(u + d), I + h*e))}),
    ('integral frozen whenever saturated', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + h*(u + d), I if v != u else I + h*e))}),
    ('integral reset to 0 when saturated', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + h*(u + d), 0.0 if v != u else I + h*e))}),
    ('anti-windup only at the upper limit', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + h*(u + d), I if v > L and e > 0 else I + h*e))}),
    ('back-calculation unwinds past the tracking value', {'pi_step': raw_pi(
        lambda y, e, v, u, I, kp, ki, L, h, d: (
            u, y + h*(u + d), I + h*e if u == v or ki == 0 else I + h*e + 2*(u - v)/ki))}),
    ('integral of the next error', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + h*(u + d), I if v != u and v*e > 0 else I + h*(e - h*(u + d))))}),
    ('pi_step forgot h in the plant', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        u, y + u + d, I if v != u and v*e > 0 else I + h*e))}),
    ('review F1: saturation decided from kp*e only', {'pi_step': raw_pi(
        lambda y, e, v, u, I, kp, ki, L, h, d: (
            u, y + h*(u + d), I if (kp*e > L and e > 0) or (kp*e < -L and e < 0) else I + h*e))}),
    ('review F2: unguarded fixed-gain back-calculation (Kt = 1)', {'pi_step': raw_pi(
        lambda y, e, v, u, I, kp, ki, L, h, d: (
            u, y + h*(u + d), I + h*e if ki == 0 else I + h*(e + (u - v)/ki)))}),
    ('review F3: |v| >= limit treated as saturated', {'pi_step': raw_pi(
        lambda y, e, v, u, I, kp, ki, L, h, d: (
            u, y + h*(u + d), I if abs(v) >= L and v*e > 0 else I + h*e))}),
    ('review F3: |u| == limit treated as saturated', {'pi_step': raw_pi(
        lambda y, e, v, u, I, kp, ki, L, h, d: (
            u, y + h*(u + d), I if abs(u) == L and u*e > 0 else I + h*e))}),
    ('review F4: simulate re-validates intermediate states via pi_step',
     {'simulate': sim_revalidating}),
    ('review F5: |integral| > 100 rejected', {'pi_step': strict_bound(2, 100)(pi_step)}),
    ('review F5: |outputs| > 100 rejected', {'step_metrics': strict_bound(0, 100)(step_metrics)}),
    ('review F5: steps == 1000 rejected', {'simulate': lambda *a: (_ for _ in ()).throw(ValueError())
                                           if a[6] == 1000 else simulate(*a)}),
    ('review F5: string limit accepted', {'pi_step': accepts_when(
        lambda *a: isinstance(a[5], str), pi_step)}),
    ('pi_step ignores ki', {'pi_step': raw_pi(lambda y, e, v, u, I, kp, ki, L, h, d: (
        clip(kp*e, L), y + h*(clip(kp*e, L) + d), I + h*e))}),
    ('simulate does not feed back the integral', {'simulate': raw_sim(sim_no_feedback)}),
    ('simulate records the pre-step output', {'simulate': raw_sim(sim_pre_step)}),
    ('simulate includes y0 (steps + 1 entries)', {'simulate': raw_sim(
        lambda y0, r, kp, ki, L, h, n, d: [(y0, 0.0)] + simulate(y0, r, kp, ki, L, h, n, d))}),
    ('simulate pair order (u, y)', {'simulate': raw_sim(
        lambda y0, r, kp, ki, L, h, n, d: [(u, y) for y, u in simulate(y0, r, kp, ki, L, h, n, d)])}),
    ('simulate forgot the disturbance', {'simulate': raw_sim(
        lambda y0, r, kp, ki, L, h, n, d: simulate(y0, r, kp, ki, L, h, n, 0))}),
    ('simulate own loop with runaway integrator', {'simulate': raw_sim(sim_naive)}),
    ('simulate P-only', {'simulate': raw_sim(sim_p_only)}),
    ('simulate integral starts at the error', {'simulate': raw_sim(sim_integral_starts_at_error)}),
    ('settle off by one (list index)', {'step_metrics': metrics_rule(
        lambda o, y0, r, b, s, ov: (None if s is None else max(s - 1, 0), ov))}),
    ('settle at the first entry into the band', {'step_metrics': metrics_rule(first_entry)}),
    ('strict band edge', {'step_metrics': strict_band}),
    ('settle never 0 (ignores y0)', {'step_metrics': metrics_rule(
        lambda o, y0, r, b, s, ov: (None if s is None else max(s, 1), ov))}),
    ('not settled reported as N', {'step_metrics': metrics_rule(
        lambda o, y0, r, b, s, ov: (len(o) if s is None else s, ov))}),
    ('overshoot sign ignores step direction', {'step_metrics': metrics_rule(
        lambda o, y0, r, b, s, ov: (s, max(0, max(y - r for y in o))))}),
    ('overshoot may be negative', {'step_metrics': metrics_rule(
        lambda o, y0, r, b, s, ov: (s, 0 if r == y0 else max(((r > y0) - (r < y0))*(y - r) for y in o)))}),
    ('overshoot as a fraction of the step', {'step_metrics': metrics_rule(
        lambda o, y0, r, b, s, ov: (s, ov if r == y0 else ov/abs(r - y0)))}),
    ('step_metrics sorts the input', {'step_metrics': sorting}),
    ('bool kp accepted', {'p_step': accepts_when(lambda *a: type(a[2]) is bool, p_step)}),
    ('NaN limit accepted', {'pi_step': accepts_when(
        lambda *a: type(a[5]) is float and a[5] != a[5], pi_step)}),
    ('NaN band accepted', {'step_metrics': accepts_when(
        lambda *a: type(a[3]) is float and a[3] != a[3], step_metrics)}),
    ('float steps accepted', {'simulate': lambda *a: simulate(*a[:6], int(a[6]), *a[7:])
                              if type(a[6]) is float and math.isfinite(a[6]) and a[6] >= 1
                              else simulate(*a)}),
    ('bool steps accepted', {'simulate': lambda *a: simulate(*a[:6], int(a[6]), *a[7:])
                             if type(a[6]) is bool and a[6] else simulate(*a)}),
    ('h = 0 accepted', {'p_step': accepts_when(lambda *a: a[4] == 0 and type(a[4]) is float, p_step)}),
    ('negative ki accepted', {'pi_step': accepts_when(lambda *a: is_real(a[4]) and a[4] < 0, pi_step)}),
    ('integral bound unchecked', {'pi_step': accepts_when(
        lambda *a: is_real(a[2]) and abs(a[2]) > 1e9, pi_step)}),
    ('disturbance bound unchecked', {'simulate': lambda *a: [(0.0, 0.0)] * 5
                                     if len(a) > 7 and is_real(a[7]) and abs(a[7]) > 100
                                     else simulate(*a)}),
    ('empty outputs accepted', {'step_metrics': accepts_when(
        lambda *a: isinstance(a[0], (list, tuple)) and not a[0], step_metrics)}),
    ('bool sample in outputs accepted', {'step_metrics': accepts_when(
        lambda *a: isinstance(a[0], list) and any(type(v) is bool for v in a[0]), step_metrics)}),
    ('rejects int inputs', {'p_step': floats_only(p_step)}),
    ('rejects tuple outputs', {'step_metrics': lambda o, *a: step_metrics(o, *a)
                               if isinstance(o, list) else (_ for _ in ()).throw(ValueError())}),
    ('NaN u returned', {'p_step': raw_p(lambda y, r, kp, L, h, d: (float('nan'), y))}),
    ('bool settle returned', {'step_metrics': metrics_rule(
        lambda o, y0, r, b, s, ov: (bool(s) if s in (0, 1) else s, ov))}),
]
for label, over in mutants:
    require(run_with(over), 'false accept: ' + label)
print('PID kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
