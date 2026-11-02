"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different formulations of the
triangular/trapezoidal time law) that must pass, and named injected bugs that
must be rejected for their intended reason. Plain checks only, so it also works
under python -O.
"""
import ast
import importlib.util
import json
import math
from decimal import Decimal
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('trajectory_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L07-trajectory.v1.py'
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
names = ('profile', 'min_duration', 'scaled_profile', 'sample', 'sync_duration')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _ref_profile') > spoiler and text.index('_PROFILE_CASES = ') > spoiler,
        'oracle and tables must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('trajectory_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check([])
require(starter, 'unimplemented starter must report failure')
require(all(failure.isascii() for failure in starter), 'starter failure messages must be ASCII')
require(len(starter) == 5 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented function into one line: ' + str(starter))


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def entry(structure, names_, args):
    return {'structure': structure,
            'inputs': {name: dec(value) for name, value in zip(names_, args)}}


expected_samples = (
    [entry('trajectory.profile@1', ('distance', 'vmax', 'amax'), a) for a, _ in kit._PROFILE_CASES]
    + [entry('trajectory.min-duration@1', ('distance', 'vmax', 'amax'), a)
       for a, _ in kit._DUR_CASES]
    + [entry('trajectory.scaled-profile@1', ('distance', 'vmax', 'amax', 'duration'), a)
       for a, _ in kit._SCALED_CASES]
    + [entry('trajectory.sample@1', ('distance', 'vmax', 'amax', 't', 'duration'), a)
       for a, _ in kit._SAMPLE_CASES]
    + [entry('trajectory.shape@1', ('distance', 'vmax', 'amax', 'duration'), a)
       for a in kit._SHAPE_CASES]
    + [entry('trajectory.sync@1', ('d1', 'v1', 'a1', 'd2', 'v2', 'a2'), a)
       for a, _ in kit._SYNC_CASES])
samples = json.loads((root / 'content/labs/L07-trajectory.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L07-trajectory'], 'samples must hold only L07-trajectory')
require(samples['kits']['L07-trajectory'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')


# ---- independent cross-checks of the hand-derived tables ----
def area(p):
    """Area under |v(t)|: two ramps of ta (average speed vp/2) plus the cruise."""
    return abs(p[3])*p[1] + abs(p[3])*p[2]


for args, hand in kit._PROFILE_CASES:
    ref = kit._ref_profile(*args)
    require(abs(area(ref) - abs(args[0])) <= 1e-9*max(1, abs(args[0])),
            'reference profile area differs from distance: ' + repr(args))
    require(ref[4] >= 0 and abs(ref[3]) <= args[1]*(1 + 1e-12)
            and abs(ref[3])/ref[1] <= args[2]*(1 + 1e-12) if ref[1] else True,
            'reference profile violates a limit: ' + repr(args))
    if hand is not None:
        require(all(abs(a - b) <= 1e-12 for a, b in zip(hand, ref[1:])),
                'hand profile table disagrees with the reference: ' + repr(args))
for args, hand in kit._DUR_CASES:
    if hand is not None:
        require(abs(kit._ref_profile(*args)[4] - hand) <= 1e-12, 'hand duration table: ' + repr(args))
for args, hand in kit._SCALED_CASES:
    ref = kit._ref_scaled(*args)
    if ref[0] != 'infeasible' and ref[0] != 'none':
        require(abs(area(ref) - abs(args[0])) <= 1e-9*max(1, abs(args[0])),
                'reference scaled area differs from distance: ' + repr(args))
        require(abs(ref[4] - args[3]) <= 1e-9 or args[3] < kit._ref_profile(*args[:3])[4],
                'scaled duration: ' + repr(args))
        require(abs(ref[3]) <= args[1]*(1 + 1e-9), 'scaled peak above vmax: ' + repr(args))
    if hand is not None:
        require(hand[0] == ref[0] and all(abs(a - b) <= 1e-12 for a, b in zip(hand[1:], ref[1:])),
                'hand scaled table disagrees with the reference: ' + repr(args))
for args, hand in kit._SAMPLE_CASES:
    if hand is not None:
        ref = kit._ref_sample(*args)
        require(abs(ref[0] - hand[0]) <= 1e-12 and abs(ref[1] - hand[1]) <= 1e-12
                and (hand[2] is None or abs(ref[2] - hand[2]) <= 1e-12),
                'hand sample table disagrees with the reference: ' + repr(args))
# the reference is continuous and symmetric: q(t) + q(T - t) = distance
for args in kit._SHAPE_CASES:
    p = kit._ref_profile(*args[:3]) if len(args) == 3 else kit._ref_scaled(*args)
    for k in range(1, 40):
        t = p[4]*k/40
        a = kit._ref_sample(*args[:3], t, args[3] if len(args) > 3 else None)
        b = kit._ref_sample(*args[:3], p[4] - t, args[3] if len(args) > 3 else None)
        require(abs(a[0] + b[0] - args[0]) <= 1e-9 and abs(a[1] - b[1]) <= 1e-9,
                'reference sample is not symmetric: ' + repr(args))
for args, hand in kit._SYNC_CASES:
    if hand is not None:
        require(abs(max(kit._ref_profile(*args[:3])[4], kit._ref_profile(*args[3:])[4]) - hand)
                <= 1e-12, 'hand sync table: ' + repr(args))


# ---- author reference implementation (validating) ----
def real(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError


def limits(distance, vmax, amax):
    real(distance, -1000, 1000)
    real(vmax, 0.01, 100)
    real(amax, 0.01, 1000)


def span(duration):
    real(duration, 0, 1e6)


def profile(distance, vmax, amax):
    limits(distance, vmax, amax)
    return kit._ref_profile(distance, vmax, amax)


def min_duration(distance, vmax, amax):
    limits(distance, vmax, amax)
    return kit._ref_profile(distance, vmax, amax)[4]


def scaled_profile(distance, vmax, amax, duration):
    limits(distance, vmax, amax)
    span(duration)
    return kit._ref_scaled(distance, vmax, amax, duration)


def sample(distance, vmax, amax, t, duration=None):
    limits(distance, vmax, amax)
    span(t)
    if duration is not None:
        span(duration)
        if kit._ref_scaled(distance, vmax, amax, duration)[0] == 'infeasible':
            raise ValueError
    return kit._ref_sample(distance, vmax, amax, t, duration)


def sync_duration(d1, v1, a1, d2, v2, a2):
    limits(d1, v1, a1)
    limits(d2, v2, a2)
    return max(kit._ref_profile(d1, v1, a1)[4], kit._ref_profile(d2, v2, a2)[4])


refs = {'profile': profile, 'min_duration': min_duration, 'scaled_profile': scaled_profile,
        'sample': sample, 'sync_duration': sync_duration}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


def sgn(x):
    return (x > 0) - (x < 0)


# ---- valid alternatives ----
def profile_ratio(distance, vmax, amax):
    """Compare d with vmax^2/amax (a distance); lists; ints survive where exact."""
    limits(distance, vmax, amax)
    d = abs(distance)
    if d == 0:
        return ['none', 0, 0, 0, 0]
    ramp_distance = vmax*vmax/amax
    if d <= ramp_distance:
        ta = math.sqrt(d/amax)
        return ['triangular', ta, 0.0, sgn(distance)*amax*ta, ta + ta]
    ta = vmax/amax
    tc = (d - ramp_distance)/vmax
    return ['trapezoidal', ta, tc, sgn(distance)*vmax, ta + tc + ta]


def scaled_naive(distance, vmax, amax, duration):
    """(aT - sqrt(a^2 T^2 - 4 a d))/2 form with a plain float guard; tuples."""
    limits(distance, vmax, amax)
    span(duration)
    d = abs(distance)
    tmin = profile_ratio(distance, vmax, amax)[4]
    if d == 0:
        return ('none', 0.0, 0.0, 0.0, duration)
    if duration < tmin - 1e-9*max(1.0, tmin):
        return ('infeasible', 0.0, 0.0, 0.0, tmin)
    disc = max(0.0, (amax*duration)**2 - 4*amax*d)
    v = min(vmax, (amax*duration - math.sqrt(disc))/2)
    ta = v/amax
    return ('trapezoidal', ta, duration - 2*ta, sgn(distance)*v, duration)


def scaled_bisection(distance, vmax, amax, duration):
    """Bisect on the peak speed v in v*(T - v/a) = d (increasing on [0, aT/2])."""
    limits(distance, vmax, amax)
    span(duration)
    d = abs(distance)
    tmin = profile_ratio(distance, vmax, amax)[4]
    if d == 0:
        return ['none', 0.0, 0.0, 0.0, float(duration)]
    if duration < tmin - 1e-10*max(1.0, tmin):
        return ['infeasible', 0.0, 0.0, 0.0, tmin]
    low, high = 0.0, min(vmax, amax*duration/2)
    for _ in range(200):
        mid = (low + high)/2
        if mid*(duration - mid/amax) < d:
            low = mid
        else:
            high = mid
    v = high
    return ['trapezoidal', v/amax, duration - 2*v/amax, sgn(distance)*v, duration]


def segments(distance, vmax, amax, duration):
    """Phase list [(length, acceleration)] from the scaled/min profile."""
    if duration is None:
        p = profile_ratio(distance, vmax, amax)
    else:
        p = scaled_bisection(distance, vmax, amax, duration)
    a = sgn(distance)*amax
    return [(p[1], a), (p[2], 0.0), (p[1], -a)], p


def sample_integrate(distance, vmax, amax, t, duration=None):
    """Integrate piecewise-constant acceleration segment by segment; then hold."""
    limits(distance, vmax, amax)
    span(t)
    if duration is not None:
        span(duration)
        if scaled_bisection(distance, vmax, amax, duration)[0] == 'infeasible':
            raise ValueError
    if distance == 0:
        return [0.0, 0.0, 0.0]
    parts, p = segments(distance, vmax, amax, duration)
    q = v = 0.0
    clock = 0.0
    for length, a in parts:
        if t <= clock + length:
            s = t - clock
            return [q + v*s + 0.5*a*s*s, v + a*s, a]
        q += v*length + 0.5*a*length*length
        v += a*length
        clock += length
    return [float(distance), 0.0, 0.0]


def sample_mirror(distance, vmax, amax, t, duration=None):
    """Second half by symmetry: q(t) = D - q(T - t), v(t) = v(T - t), a(t) = -a(T - t)."""
    limits(distance, vmax, amax)
    span(t)
    if duration is not None:
        span(duration)
        if kit._ref_scaled(distance, vmax, amax, duration)[0] == 'infeasible':
            raise ValueError
    kind, ta, tc, vp, total = (kit._ref_profile(distance, vmax, amax) if duration is None
                               else kit._ref_scaled(distance, vmax, amax, duration))
    if kind == 'none' or t >= total:
        return (float(distance), 0.0, 0.0)
    a = vp/ta

    def first_half(s):
        if s < ta:
            return (0.5*a*s*s, a*s, a)
        return (0.5*vp*ta + vp*(s - ta), vp, 0.0)
    if t <= total/2:
        return first_half(t)
    q, v, acc = first_half(total - t)
    return (distance - q, v, -acc)


def sample_unit(distance, vmax, amax, t, duration=None):
    """Unit profile (D = 1, v/d, a/d scaling) multiplied back by the distance."""
    limits(distance, vmax, amax)
    span(t)
    if duration is not None:
        span(duration)
        if kit._ref_scaled(distance, vmax, amax, duration)[0] == 'infeasible':
            raise ValueError
    if distance == 0:
        return [0, 0, 0]
    d = abs(distance)
    kind, ta, tc, vp, total = (kit._ref_profile(d, vmax, amax) if duration is None
                               else kit._ref_scaled(d, vmax, amax, duration))
    if t >= total:
        return [distance, 0, 0]
    if t < ta:
        q, v, a = 0.5*amax_eff(vp, ta)*t*t, amax_eff(vp, ta)*t, amax_eff(vp, ta)
    elif t < ta + tc:
        q, v, a = 0.5*vp*ta + vp*(t - ta), vp, 0.0
    else:
        s = total - t
        q, v, a = d - 0.5*amax_eff(vp, ta)*s*s, amax_eff(vp, ta)*s, -amax_eff(vp, ta)
    k = sgn(distance)
    return [k*q, k*v, k*a]


def amax_eff(vp, ta):
    return abs(vp)/ta


def profile_zero_unified(distance, vmax, amax):
    """Boundary goes to 'trapezoidal' (tc = 0 there); tuple; min of two durations form."""
    limits(distance, vmax, amax)
    d = abs(distance)
    if d == 0:
        return ('none', 0.0, 0.0, 0.0, 0.0)
    ta = min(vmax/amax, math.sqrt(d/amax))
    vp = amax*ta
    tc = max(0.0, (d - amax*ta*ta)/vp)
    return ('trapezoidal' if d*amax >= vmax*vmax else 'triangular', ta, tc,
            sgn(distance)*vp, 2*ta + tc)


def sync_via_scaled(d1, v1, a1, d2, v2, a2):
    limits(d1, v1, a1)
    limits(d2, v2, a2)
    times = sorted([profile_zero_unified(d1, v1, a1)[4], profile_zero_unified(d2, v2, a2)[4]])
    return times[-1]


alternatives = [
    ('author: closed-form reference with area-preserving scaling', {}),
    ('ratio test on vmax^2/amax, lists, naive quadratic scaling, mirrored second half',
     {'profile': profile_ratio, 'scaled_profile': scaled_naive, 'sample': sample_mirror,
      'min_duration': lambda *a: profile_ratio(*a)[4]}),
    ('min(vmax/amax, sqrt(d/amax)) ramp formula, bisection scaling, segment integration',
     {'profile': profile_zero_unified, 'scaled_profile': scaled_bisection,
      'sample': sample_integrate, 'min_duration': lambda *a: profile_zero_unified(*a)[4],
      'sync_duration': sync_via_scaled}),
    ('unit-distance profile multiplied back by the sign',
     {'sample': sample_unit, 'scaled_profile': scaled_naive}),
    ('integer-preserving ratio profile, bisection scaling, mirrored sample',
     {'profile': profile_ratio, 'scaled_profile': scaled_bisection, 'sample': sample_mirror}),
    ('boundary labelled trapezoidal, naive scaling, integrated sample, sync by sorting',
     {'profile': profile_zero_unified, 'scaled_profile': scaled_naive,
      'sample': sample_integrate, 'sync_duration': sync_via_scaled}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result[:4]))


# ---- injected bugs ----
def valid(rule, kind):
    """Run the author validation for a function kind, then the buggy rule."""
    def run(*a):
        if kind == 'profile':
            limits(*a[:3])
        elif kind == 'scaled':
            limits(*a[:3])
            span(a[3])
        elif kind == 'sample':
            limits(*a[:3])
            span(a[3])
            if len(a) > 4 and a[4] is not None:
                span(a[4])
        elif kind == 'sync':
            limits(*a[:3])
            limits(*a[3:])
        return rule(*a)
    return run


def profile_rule(rule):
    return valid(rule, 'profile')


def ref_with(index, change):
    """Reference profile with element `index` replaced by change(ref, d, vmax, amax)."""
    def rule(distance, vmax, amax):
        p = list(kit._ref_profile(distance, vmax, amax))
        p[index] = change(p, abs(distance), vmax, amax, distance)
        return tuple(p)
    return rule


def kind_by_distance(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if distance != 0:
        p[0] = 'triangular' if abs(distance) < vmax else 'trapezoidal'
    return tuple(p)


def always_trapezoid(distance, vmax, amax):
    d = abs(distance)
    if d == 0:
        return ('none', 0.0, 0.0, 0.0, 0.0)
    ta = vmax/amax
    tc = d/vmax - ta
    return ('trapezoidal', ta, tc, sgn(distance)*vmax, 2*ta + tc)


def no_ramp_time(distance, vmax, amax):
    p = kit._ref_profile(distance, vmax, amax)
    return (p[0], p[1], p[2], p[3], abs(distance)/vmax)


def half_tri_ramp(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if p[0] == 'triangular':
        p[1] = math.sqrt(abs(distance)/(2*amax))
        p[3] = sgn(distance)*amax*p[1]
        p[4] = 2*p[1]
    return tuple(p)


def tri_single_ramp(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if p[0] == 'triangular':
        p[4] = p[1]
    return tuple(p)


def tri_peak_vmax(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if p[0] == 'triangular':
        p[3] = sgn(distance)*vmax
    return tuple(p)


def peak_unsigned(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    p[3] = abs(p[3])
    return tuple(p)


def trapezoid_peak_unsigned(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if p[0] == 'trapezoidal':
        p[3] = abs(p[3])
    return tuple(p)


def divide_by_distance(distance, vmax, amax):
    p = kit._ref_profile(distance, vmax, amax)
    return p + (vmax*amax/abs(distance),)[:0] if abs(distance) > 0 else (1/abs(distance),)


def cruise_without_ramp_subtraction(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if p[0] == 'trapezoidal':
        p[2] = abs(distance)/vmax
        p[4] = 2*p[1] + p[2]
    return tuple(p)


def sqrt_of_signed(distance, vmax, amax):
    if distance < 0:
        math.sqrt(distance)
    return kit._ref_profile(distance, vmax, amax)


def ramp_vmax_times_amax(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if p[0] == 'trapezoidal':
        p[1] = vmax*amax
        p[4] = 2*p[1] + p[2]
    return tuple(p)


def misspelled_label(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if p[0] == 'triangular':
        p[0] = 'triangle'
    return tuple(p)


def zero_threshold(distance, vmax, amax):
    if abs(distance) < 1e-3:
        return ('none', 0.0, 0.0, 0.0, 0.0)
    return kit._ref_profile(distance, vmax, amax)


def swapped_limits(distance, vmax, amax):
    return kit._ref_profile(distance, min(amax, 100), min(vmax, 1000))


def cruise_first(distance, vmax, amax):
    p = list(kit._ref_profile(distance, vmax, amax))
    if p[0] == 'trapezoidal':
        p[1], p[2] = p[2], p[1]
    return tuple(p)


def dur_rule(rule):
    def run(distance, vmax, amax):
        limits(distance, vmax, amax)
        return rule(distance, vmax, amax)
    return run


def scaled_rule(rule):
    return valid(rule, 'scaled')


def uniform_stretch(distance, vmax, amax, duration):
    p = kit._ref_profile(distance, vmax, amax)
    if p[0] == 'none':
        return ('none', 0.0, 0.0, 0.0, float(duration))
    if duration < p[4] - 1e-9:
        return ('infeasible', 0.0, 0.0, 0.0, p[4])
    k = duration/p[4]
    return ('trapezoidal', p[1]*k, p[2]*k, p[3]/k, float(duration))


def average_speed_cruise(distance, vmax, amax, duration):
    p = kit._ref_scaled(distance, vmax, amax, duration)
    if p[0] in ('infeasible', 'none'):
        return p
    v = abs(distance)/duration
    return ('trapezoidal', v/amax, duration - 2*v/amax, sgn(distance)*v, float(duration))


def clamp_to_minimum(distance, vmax, amax, duration):
    p = kit._ref_scaled(distance, vmax, amax, duration)
    if p[0] == 'infeasible':
        return kit._ref_profile(distance, vmax, amax)
    return p


def raise_on_impossible(distance, vmax, amax, duration):
    p = kit._ref_scaled(distance, vmax, amax, duration)
    if p[0] == 'infeasible':
        raise ValueError('too short')
    return p


def exceed_limits(distance, vmax, amax, duration):
    p = kit._ref_scaled(distance, vmax, amax, duration)
    if p[0] == 'infeasible' and abs(distance) > 0:
        v = abs(distance)/duration
        return ('trapezoidal', 0.0, float(duration), sgn(distance)*v, float(duration))
    return p


def larger_root(distance, vmax, amax, duration):
    p = kit._ref_scaled(distance, vmax, amax, duration)
    if p[0] in ('infeasible', 'none'):
        return p
    disc = max(0.0, (amax*duration)**2 - 4*amax*abs(distance))
    v = (amax*duration + math.sqrt(disc))/2
    return ('trapezoidal', v/amax, duration - 2*v/amax, sgn(distance)*v, float(duration))


def keep_vmax_lower_amax(distance, vmax, amax, duration):
    p = kit._ref_scaled(distance, vmax, amax, duration)
    if p[0] in ('infeasible', 'none'):
        return p
    tmin = kit._ref_profile(distance, vmax, amax)[4]
    if duration > tmin:
        d = abs(distance)
        ta = duration - d/vmax
        return ('trapezoidal', ta, duration - 2*ta, sgn(distance)*vmax, float(duration))
    return p


def infeasible_reports_request(distance, vmax, amax, duration):
    p = kit._ref_scaled(distance, vmax, amax, duration)
    if p[0] == 'infeasible':
        return ('infeasible', 0.0, 0.0, 0.0, float(duration))
    return p


def strict_infeasible(distance, vmax, amax, duration):
    tmin = kit._ref_profile(distance, vmax, amax)[4]
    if abs(distance) > 0 and duration < tmin:
        return ('infeasible', 0.0, 0.0, 0.0, tmin)
    return kit._ref_scaled(distance, vmax, amax, max(duration, tmin))


def zero_distance_zero_duration(distance, vmax, amax, duration):
    if distance == 0:
        return ('none', 0.0, 0.0, 0.0, 0.0)
    return kit._ref_scaled(distance, vmax, amax, duration)


def scaled_sign_lost(distance, vmax, amax, duration):
    p = list(kit._ref_scaled(distance, vmax, amax, duration))
    p[3] = abs(p[3])
    return tuple(p)


def scaled_wide_band(distance, vmax, amax, duration):
    tmin = kit._ref_profile(distance, vmax, amax)[4]
    if abs(distance) > 0 and tmin - 0.6 <= duration < tmin:
        return kit._ref_profile(distance, vmax, amax)
    return kit._ref_scaled(distance, vmax, amax, duration)


def snap_to_minimum(distance, vmax, amax, duration):
    tmin = kit._ref_profile(distance, vmax, amax)[4]
    if abs(distance) > 0 and tmin <= duration < tmin + 1e-3:
        return kit._ref_profile(distance, vmax, amax)
    return kit._ref_scaled(distance, vmax, amax, duration)


def loose_feasibility(distance, vmax, amax, duration):
    tmin = kit._ref_profile(distance, vmax, amax)[4]
    if abs(distance) > 0 and tmin - 1e-3 <= duration < tmin:
        return kit._ref_profile(distance, vmax, amax)
    return kit._ref_scaled(distance, vmax, amax, duration)


def loose_type_band(distance, vmax, amax):
    d = abs(distance)
    if d > 0 and d*amax < vmax*vmax*1.001:
        ta = math.sqrt(d/amax)
        return ('triangular', ta, 0.0, sgn(distance)*amax*ta, 2*ta)
    return kit._ref_profile(distance, vmax, amax)


def sample_rule(rule):
    return valid(rule, 'sample')


def with_profile(distance, vmax, amax, duration):
    return (kit._ref_profile(distance, vmax, amax) if duration is None
            else kit._ref_scaled(distance, vmax, amax, duration))


def decel_after_ramp(distance, vmax, amax, t, duration=None):
    """Forgets the cruise: decelerates as soon as the ramp ends."""
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    if kind == 'none':
        return (0.0, 0.0, 0.0)
    a = vp/ta
    if t < ta:
        return (0.5*a*t*t, a*t, a)
    if t < 2*ta:
        s = t - ta
        return (0.5*vp*ta + vp*s - 0.5*a*s*s, vp - a*s, -a)
    return (float(distance), 0.0, 0.0)


def decel_sign_acceleration(distance, vmax, amax, t, duration=None):
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    return (q, v, abs(a)*sgn(distance) if a != 0 else 0.0)


def decel_position_plus(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    if kind != 'none' and ta + tc <= t < total:
        s = t - ta - tc
        return (0.5*vp*ta + vp*tc + vp*s + 0.5*(vp/ta)*s*s, v, a)
    return (q, v, a)


def decel_velocity_wrong_clock(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    if kind != 'none' and ta + tc <= t < total:
        return (q, vp - (vp/ta)*(t - ta), a)
    return (q, v, a)


def no_hold(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    if kind != 'none' and t >= total:
        s = t - total
        return (distance + 0.0*s, -(vp/ta)*s, -(vp/ta))
    return kit._ref_sample(distance, vmax, amax, t, duration)


def raises_after_end(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    if kind != 'none' and t > total:
        raise ValueError('t is beyond the move')
    return kit._ref_sample(distance, vmax, amax, t, duration)


def ignores_duration(distance, vmax, amax, t, duration=None):
    return kit._ref_sample(distance, vmax, amax, t, None)


def uniform_stretch_sample(distance, vmax, amax, t, duration=None):
    if duration is None or distance == 0:
        return kit._ref_sample(distance, vmax, amax, t, duration)
    p = kit._ref_profile(distance, vmax, amax)
    k = duration/p[4]
    q, v, a = kit._ref_sample(distance, vmax, amax, t/k, None)
    return (q, v/k, a/(k*k))


def cruise_without_accel_distance(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    if kind != 'none' and ta <= t < ta + tc:
        return (vp*(t - ta), v, a)
    return (q, v, a)


def glitch_near_boundary(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    if kind != 'none' and 0 < ta - t < 1e-4*max(1.0, total):
        return (q + 1e-3*sgn(distance), v, a)
    return (q, v, a)


def acceleration_spike(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    if kind != 'none' and t == ta:
        return (q, v, 10*amax*sgn(distance))
    return (q, v, a)


def overshoot_then_return(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    if kind != 'none' and total - ta/2 < t < total:
        return (distance + sgn(distance)*0.01*abs(distance), v, a)
    return (q, v, a)


def speed_over_limit_mid_cruise(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = with_profile(distance, vmax, amax, duration)
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    if kind != 'none' and tc > 0 and abs(t - (ta + tc/2)) < 1e-12:
        return (q, v*1.2, a)
    return (q, v, a)


def sample_sign_lost(distance, vmax, amax, t, duration=None):
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    return (abs(q), abs(v), abs(a))


def start_offset(distance, vmax, amax, t, duration=None):
    q, v, a = kit._ref_sample(distance, vmax, amax, t, duration)
    if t == 0 and distance != 0:
        return (q, 0.01, a)
    return (q, v, a)


def sync_rule(rule):
    return valid(rule, 'sync')


def accepts_when(predicate, function, value):
    def run(*a):
        if predicate(*a):
            return value
        return function(*a)
    return run


mutants = [
    # profile
    ('profile: triangular/trapezoidal chosen by distance < vmax', {'profile': profile_rule(kind_by_distance)}, ['kind label']),
    ('profile: always the trapezoid formula (negative cruise time)', {'profile': profile_rule(always_trapezoid)}, ['kind label', 't_cruise']),
    ('profile: duration = distance / vmax (ramps ignored)', {'profile': profile_rule(no_ramp_time)}, ['duration']),
    ('profile: triangular ramp sqrt(d/(2 amax))', {'profile': profile_rule(half_tri_ramp)}, ['t_acc']),
    ('profile: triangular duration is one ramp', {'profile': profile_rule(tri_single_ramp)}, ['duration']),
    ('profile: triangular peak reported as vmax', {'profile': profile_rule(tri_peak_vmax)}, ['v_peak']),
    ('profile: v_peak unsigned for reversed moves', {'profile': profile_rule(peak_unsigned)}, ['v_peak']),
    ('profile: v_peak unsigned only in trapezoids', {'profile': profile_rule(trapezoid_peak_unsigned)}, ['v_peak']),
    ('profile: division by zero for distance 0', {'profile': profile_rule(lambda d, v, a: kit._ref_profile(d, v, a) + (1/abs(d),)[:0] if d else (1/d,))}, ['raised']),
    ('profile: cruise time = d / vmax (ramp distance not subtracted)', {'profile': profile_rule(cruise_without_ramp_subtraction)}, ['t_cruise']),
    ('profile: sqrt of the signed distance fails for reversed moves', {'profile': profile_rule(sqrt_of_signed)}, ['raised']),
    ('profile: ramp time vmax*amax', {'profile': profile_rule(ramp_vmax_times_amax)}, ['t_acc']),
    ('profile: triangular label misspelled', {'profile': profile_rule(misspelled_label)}, ['kind label']),
    ('profile: distances below 1e-3 treated as no motion', {'profile': profile_rule(zero_threshold)}, ['kind label']),
    ('profile: vmax and amax swapped', {'profile': profile_rule(swapped_limits)}, ['t_acc', 'v_peak', 'duration', 'kind label']),
    ('profile: cruise and ramp times swapped', {'profile': profile_rule(cruise_first)}, ['t_acc']),
    # min_duration
    ('min_duration: distance / vmax', {'min_duration': dur_rule(lambda d, v, a: abs(d)/v if d else 0.0)}, ['min_duration']),
    ('min_duration: always the triangular formula', {'min_duration': dur_rule(lambda d, v, a: 2*math.sqrt(abs(d)/a))}, ['min_duration']),
    ('min_duration: signed for reversed moves', {'min_duration': dur_rule(lambda d, v, a: sgn(d)*kit._ref_profile(d, v, a)[4])}, ['min_duration']),
    ('min_duration: zero distance divides by zero', {'min_duration': dur_rule(lambda d, v, a: kit._ref_profile(d, v, a)[4] + 0*(1/d))}, ['raised']),
    # scaled_profile
    ('scaled: uniform time stretch (acceleration lowered)', {'scaled_profile': scaled_rule(uniform_stretch)}, ['t_acc', 'v_peak', 't_cruise']),
    ('scaled: cruise at distance / duration (ramps ignored)', {'scaled_profile': scaled_rule(average_speed_cruise)}, ['v_peak', 't_acc']),
    ('scaled: impossible request clamped to the minimum profile', {'scaled_profile': scaled_rule(clamp_to_minimum)}, ['impossible']),
    ('scaled: impossible request raises ValueError', {'scaled_profile': scaled_rule(raise_on_impossible)}, ['raised']),
    ('scaled: impossible request met by exceeding the limits', {'scaled_profile': scaled_rule(exceed_limits)}, ['impossible']),
    ('scaled: larger root of the quadratic', {'scaled_profile': scaled_rule(larger_root)}, ['v_peak', 't_acc']),
    ('scaled: keeps vmax and lowers amax instead', {'scaled_profile': scaled_rule(keep_vmax_lower_amax)}, ['t_acc', 'v_peak']),
    ('scaled: infeasible result reports the requested time', {'scaled_profile': scaled_rule(infeasible_reports_request)}, ['reported minimum duration']),
    ('scaled: no tolerance band at the minimum', {'scaled_profile': scaled_rule(strict_infeasible)}, ['kind label', 'impossible']),
    ('scaled: tolerance band 0.6 s accepts impossible requests', {'scaled_profile': scaled_rule(scaled_wide_band)}, ['impossible']),
    ('scaled: zero distance ignores the requested duration', {'scaled_profile': scaled_rule(zero_distance_zero_duration)}, ['duration']),
    ('scaled: v_peak unsigned', {'scaled_profile': scaled_rule(scaled_sign_lost)}, ['v_peak']),
    # sample
    ('sample: decelerates right after the ramp (no cruise)', {'sample': sample_rule(decel_after_ramp)}, ['q is wrong', 'v is wrong']),
    ('sample: deceleration reported with the wrong sign', {'sample': sample_rule(decel_sign_acceleration)}, ['a is wrong']),
    ('sample: deceleration distance added instead of subtracted', {'sample': sample_rule(decel_position_plus)}, ['q is wrong']),
    ('sample: deceleration clock starts at the ramp end', {'sample': sample_rule(decel_velocity_wrong_clock)}, ['v is wrong']),
    ('sample: keeps decelerating after the end', {'sample': sample_rule(no_hold)}, ['sample 3', 'after the end']),
    ('sample: raises after the end', {'sample': sample_rule(raises_after_end)}, ['raised']),
    ('sample: ignores the duration argument', {'sample': sample_rule(ignores_duration)}, ['q is wrong', 'v is wrong']),
    ('sample: scaled profile by uniform time stretch', {'sample': sample_rule(uniform_stretch_sample)}, ['q is wrong', 'v is wrong', 'a is wrong']),
    ('sample: cruise position forgets the ramp distance', {'sample': sample_rule(cruise_without_accel_distance)}, ['q is wrong', 'continuity']),
    ('sample: 1e-3 position glitch just before the ramp ends', {'sample': sample_rule(glitch_near_boundary)}, ['continuity']),
    ('sample: acceleration spike exactly at a phase boundary', {'sample': sample_rule(acceleration_spike)}, ['bound check: |a|']),
    ('sample: overshoot just before the end', {'sample': sample_rule(overshoot_then_return)}, ['bound check: q', 'monotone', 'continuity', 'endpoint']),
    ('sample: speed above vmax mid-cruise', {'sample': sample_rule(speed_over_limit_mid_cruise)}, ['bound check: |v|']),
    ('sample: signs lost for reversed moves', {'sample': sample_rule(sample_sign_lost)}, ['q is wrong', 'v is wrong']),
    ('sample: starts with a velocity', {'sample': sample_rule(start_offset)}, ['endpoint check']),
    ('scaled: snaps to the minimum profile within 1e-3 s above it', {'scaled_profile': scaled_rule(snap_to_minimum)}, ['t_acc', 'v_peak', 't_cruise']),
    ('scaled: feasibility tolerance 1e-3 s accepts a request just below the minimum', {'scaled_profile': scaled_rule(loose_feasibility)}, ['impossible']),
    ('profile: triangular label and numbers up to 0.1 % past the boundary', {'profile': profile_rule(loose_type_band)}, ['t_acc', 'kind label', 'duration']),
    ('sample: t upper bound exclusive', {'sample': lambda *a: (_ for _ in ()).throw(ValueError()) if a[3] >= 1e6 else sample(*a)}, ['raised']),
    ('scaled_profile: duration upper bound exclusive', {'scaled_profile': lambda *a: (_ for _ in ()).throw(ValueError()) if a[3] >= 1e6 else scaled_profile(*a)}, ['raised']),
    ('scaled_profile: duration 0 rejected', {'scaled_profile': lambda *a: (_ for _ in ()).throw(ValueError()) if a[3] == 0 else scaled_profile(*a)}, ['raised']),
    ('min_duration: amax upper bound exclusive', {'min_duration': lambda *a: (_ for _ in ()).throw(ValueError()) if a[2] >= 1000 else min_duration(*a)}, ['raised']),
    # sync
    ('sync: sum of the two durations', {'sync_duration': sync_rule(lambda d1, v1, a1, d2, v2, a2: kit._ref_profile(d1, v1, a1)[4] + kit._ref_profile(d2, v2, a2)[4])}, ['common duration']),
    ('sync: smaller of the two durations', {'sync_duration': sync_rule(lambda d1, v1, a1, d2, v2, a2: min(kit._ref_profile(d1, v1, a1)[4], kit._ref_profile(d2, v2, a2)[4]))}, ['common duration']),
    ('sync: duration of the longer distance', {'sync_duration': sync_rule(lambda d1, v1, a1, d2, v2, a2: kit._ref_profile(d1, v1, a1)[4] if abs(d1) >= abs(d2) else kit._ref_profile(d2, v2, a2)[4])}, ['common duration']),
    ('sync: zero-distance axis divides by zero', {'sync_duration': sync_rule(lambda d1, v1, a1, d2, v2, a2: max(kit._ref_profile(d1, v1, a1)[4], kit._ref_profile(d2, v2, a2)[4]) + 0*(1/(d1*d2)))}, ['raised']),
    ('sync: signed durations', {'sync_duration': sync_rule(lambda d1, v1, a1, d2, v2, a2: max(sgn(d1)*kit._ref_profile(d1, v1, a1)[4], sgn(d2)*kit._ref_profile(d2, v2, a2)[4]))}, ['common duration']),
    # validation
    ('bool distance accepted by profile', {'profile': accepts_when(lambda *a: type(a[0]) is bool, profile, ('none', 0.0, 0.0, 0.0, 0.0))}, ['invalid profile']),
    ('NaN distance accepted by profile', {'profile': accepts_when(lambda *a: type(a[0]) is float and a[0] != a[0], profile, ('none', 0.0, 0.0, 0.0, 0.0))}, ['invalid profile']),
    ('zero vmax accepted by min_duration', {'min_duration': accepts_when(lambda *a: a[1] == 0, min_duration, 0.0)}, ['invalid min_duration']),
    ('negative amax accepted by profile', {'profile': accepts_when(lambda *a: a[2] < 0, profile, ('none', 0.0, 0.0, 0.0, 0.0))}, ['invalid profile']),
    ('distance bound unchecked by min_duration', {'min_duration': accepts_when(lambda *a: abs(a[0]) > 1000, min_duration, 0.0)}, ['invalid min_duration']),
    ('negative duration accepted by scaled_profile', {'scaled_profile': accepts_when(lambda *a: a[3] < 0, scaled_profile, ('none', 0.0, 0.0, 0.0, 0.0))}, ['invalid scaled_profile']),
    ('negative t accepted by sample', {'sample': accepts_when(lambda *a: a[3] < 0, sample, (0.0, 0.0, 0.0))}, ['invalid sample']),
    ('infeasible duration sampled instead of rejected', {'sample': lambda *a: kit._ref_sample(*a[:4], None) if len(a) > 4 and a[4] == 5.0 else sample(*a)}, ['invalid sample']),
    ('bool duration accepted by sample', {'sample': accepts_when(lambda *a: len(a) > 4 and type(a[4]) is bool, sample, (0.0, 0.0, 0.0))}, ['invalid sample']),
    ('NaN second limit accepted by sync_duration', {'sync_duration': accepts_when(lambda *a: a[5] != a[5], sync_duration, 0.0)}, ['invalid sync_duration']),
    ('int inputs rejected', {'profile': lambda d, v, a: profile(d, v, a) if all(type(x) is float for x in (d, v, a)) else (_ for _ in ()).throw(ValueError())}, ['raised']),
    ('string t accepted by sample', {'sample': accepts_when(lambda *a: type(a[3]) is str, sample, (0.0, 0.0, 0.0))}, ['invalid sample']),
    ('profile raises NotImplementedError on some inputs only', {'profile': lambda d, v, a: (_ for _ in ()).throw(NotImplementedError()) if d < 0 else profile(d, v, a)}, ['NotImplementedError in']),
    ('NaN in the result at the boundary', {'profile': lambda d, v, a: ('trapezoidal', float('nan'), 0.0, 2.0, 4.0) if d == 4 and v == 2 else profile(d, v, a)}, ['profile']),
]
print_labels = []
for label, over, keywords in mutants:
    result = run_with(over)
    require(result, 'false accept: ' + label)
    require(any(k in f for f in result for k in keywords),
            'rejected for the wrong reason: ' + label + ' -> ' + str(result[:3]))
    print_labels.append(label)
require(len(mutants) >= 30 and len(set(print_labels)) == len(print_labels), 'need >= 30 distinct mutants')
print('Trajectory kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
