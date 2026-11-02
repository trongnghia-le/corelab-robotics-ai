"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different formulations) that must
pass, and named injected bugs that must be rejected. Plain checks only, so the
fixture also works under python -O.
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
        raise SystemExit('imitation_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L19-imitation.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree)
            if isinstance(node, ast.Import) for alias in node.names}
imported |= {node.module.split('.')[0] for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom) and node.module}
require(imported <= {'math', 'fractions'}, 'kit imports beyond math/fractions: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
FUNCTIONS = ('qa_episode', 'qa_dataset', 'split_by_session', 'leaked_ids', 'fit_linear',
             'bc_baseline', 'best_lag')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name) < spoiler for name in FUNCTIONS),
        'starter functions must sit above the spoiler banner')
require(text.index('def _ref_qa') > spoiler, 'oracle must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('imitation_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter, 'unimplemented starter must report failure')
require(len(starter) == len(FUNCTIONS) and all('not implemented' in line for line in starter),
        'starter must collapse NotImplementedError to one line per function: ' + str(starter))


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    if value != value or value in (float('inf'), float('-inf')):
        return repr(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def conv(value):
    if isinstance(value, (list, tuple)):
        return [conv(v) for v in value]
    return value if isinstance(value, str) else dec(value)


def entry(structure, names, args):
    return {'structure': structure,
            'inputs': {name: conv(value) for name, value in zip(names, args)}}


expected_samples = (
    [entry('imitation.qa-episode@1',
           ('times', 'obs', 'acts', 'max_gap', 'obs_range', 'act_range'), args)
     for args, _ in [c for c in kit._QA_CASES
                     if all(math.isfinite(v) for v in c[0][1] + c[0][2])][:12]]
    + [entry('imitation.qa-dataset@1', ('episodes', 'max_gap', 'obs_range', 'act_range'), args)
       for args, _ in kit._DATASET_CASES[:6]]
    + [entry('imitation.session-split@1', ('sessions', 'test_sessions'), args)
       for args, _ in kit._SPLIT_CASES[:4]]
    + [entry('imitation.leaked-ids@1', ('train_ids', 'test_ids'), args)
       for args, _ in kit._LEAK_CASES[:4]]
    + [entry('imitation.fit-linear@1', ('obs', 'acts'), args) for args, _ in kit._FIT_CASES[:5]]
    + [entry('imitation.bc-baseline@1', ('episodes', 'fit_indices', 'eval_indices'), args)
       for args, _ in kit._BC_CASES]
    + [entry('imitation.best-lag@1', ('obs', 'acts', 'max_lag'), args)
       for args, _ in kit._LAG_CASES])
samples = json.loads((root / 'content/labs/L19-imitation.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L19-imitation'], 'samples must hold only L19-imitation')
require(samples['kits']['L19-imitation'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50: ' + str(len(expected_samples)))


# ---- author reference implementation ----
def real(v):
    return type(v) in (int, float) and math.isfinite(v)


def lst(v, low, high):
    if not isinstance(v, (list, tuple)) or not low <= len(v) <= high:
        raise ValueError


def fin_list(v, low, high):
    lst(v, low, high)
    if not all(real(x) and abs(x) <= 1e6 for x in v):
        raise ValueError


def any_list(v, low, high):
    lst(v, low, high)
    if not all(type(x) in (int, float) for x in v):
        raise ValueError


def check_gap(g):
    if not real(g) or not 0 < g <= 1e6:
        raise ValueError


def check_range(r):
    lst(r, 2, 2)
    if not all(real(x) and abs(x) <= 1e6 for x in r) or r[0] > r[1]:
        raise ValueError


def check_ids(v, low=0, high=1000):
    lst(v, low, high)
    if not all(type(x) is str and x for x in v):
        raise ValueError


def check_qa_args(times, obs, acts, max_gap, obs_range, act_range):
    fin_list(times, 0, 1000)
    any_list(obs, 0, 1000)
    any_list(acts, 0, 1000)
    check_gap(max_gap)
    check_range(obs_range)
    check_range(act_range)


def check_episodes(episodes, max_gap, obs_range, act_range):
    lst(episodes, 1, 200)
    for ep in episodes:
        lst(ep, 3, 3)
        check_qa_args(ep[0], ep[1], ep[2], max_gap, obs_range, act_range)


def core_qa(times, obs, acts, max_gap, obs_range, act_range):
    if not (times or obs or acts):
        return ['empty']
    out = []
    if not len(times) == len(obs) == len(acts):
        out.append('length-mismatch')
    steps = [b - a for a, b in zip(times, times[1:])]
    if any(s <= 0 for s in steps):
        out.append('time-not-increasing')
    if any(s > max_gap + 1e-9 for s in steps):
        out.append('time-gap')
    if any(not math.isfinite(v) for v in [*obs, *acts]):
        out.append('non-finite-value')
    if any(math.isfinite(v) and not obs_range[0] <= v <= obs_range[1] for v in obs):
        out.append('obs-out-of-range')
    if any(math.isfinite(v) and not act_range[0] <= v <= act_range[1] for v in acts):
        out.append('act-out-of-range')
    return out


def qa_episode_with(core):
    def run(times, obs, acts, max_gap, obs_range, act_range):
        check_qa_args(times, obs, acts, max_gap, obs_range, act_range)
        return core(times, obs, acts, max_gap, obs_range, act_range)
    return run


def core_dataset(episodes, max_gap, obs_range, act_range, qa=core_qa, dup=None):
    dup = dup or (lambda i, ep, eps: any(
        list(ep[0]) == list(e[0]) and list(ep[1]) == list(e[1]) and list(ep[2]) == list(e[2])
        for e in eps[:i]))
    out = []
    for i, ep in enumerate(episodes):
        names = list(qa(ep[0], ep[1], ep[2], max_gap, obs_range, act_range))
        if dup(i, ep, episodes):
            names.append('duplicate')
        if names:
            out.append((i, names))
    return out


def dataset_with(core):
    def run(episodes, max_gap, obs_range, act_range):
        check_episodes(episodes, max_gap, obs_range, act_range)
        return core(episodes, max_gap, obs_range, act_range)
    return run


def core_split(sessions, test_sessions):
    held = set(test_sessions)
    return ([i for i, s in enumerate(sessions) if s not in held],
            [i for i, s in enumerate(sessions) if s in held])


def split_with(core):
    def run(sessions, test_sessions):
        check_ids(sessions, 2, 1000)
        check_ids(test_sessions, 1, 1000)
        held = set(test_sessions)
        if not held <= set(sessions) or set(sessions) <= held:
            raise ValueError
        return core(sessions, test_sessions)
    return run


def core_leak(train_ids, test_ids):
    return sorted(set(train_ids) & set(test_ids))


def leak_with(core):
    def run(train_ids, test_ids):
        check_ids(train_ids)
        check_ids(test_ids)
        return core(train_ids, test_ids)
    return run


def check_fit(obs, acts):
    fin_list(obs, 2, 1000)
    fin_list(acts, 2, 1000)
    if len(obs) != len(acts) or max(obs) == min(obs):
        raise ValueError


def core_fit(obs, acts):
    n = len(obs)
    mo, ma = sum(obs)/n, sum(acts)/n
    sxx = sum((o - mo)**2 for o in obs)
    sxy = sum((o - mo)*(a - ma) for o, a in zip(obs, acts))
    w = sxy/sxx
    return (w, ma - w*mo)


def fit_with(core):
    def run(obs, acts):
        check_fit(obs, acts)
        return core(obs, acts)
    return run


def check_bc(episodes, fit_indices, eval_indices):
    lst(episodes, 1, 200)
    for ep in episodes:
        lst(ep, 3, 3)
        for part in ep:
            fin_list(part, 1, 1000)
        if not len(ep[0]) == len(ep[1]) == len(ep[2]):
            raise ValueError
    for idx in (fit_indices, eval_indices):
        lst(idx, 1, 200)
        if (not all(type(i) is int and 0 <= i < len(episodes) for i in idx)
                or len(set(idx)) != len(idx)):
            raise ValueError
    fx = [o for i in fit_indices for o in episodes[i][1]]
    if max(fx) == min(fx):
        raise ValueError


def pooled(episodes, indices, slot):
    return [v for i in indices for v in episodes[i][slot]]


def core_bc(episodes, fit_indices, eval_indices, fit=core_fit):
    w, b = fit(pooled(episodes, fit_indices, 1), pooled(episodes, fit_indices, 2))
    fy = pooled(episodes, fit_indices, 2)
    mean = sum(fy)/len(fy)
    ex, ey = pooled(episodes, eval_indices, 1), pooled(episodes, eval_indices, 2)
    n = len(ex)
    return (w, b, sum((y - (w*x + b))**2 for x, y in zip(ex, ey))/n,
            sum((y - mean)**2 for y in ey)/n)


def bc_with(core):
    def run(episodes, fit_indices, eval_indices):
        check_bc(episodes, fit_indices, eval_indices)
        return core(episodes, fit_indices, eval_indices)
    return run


def check_lag(obs, acts, max_lag):
    fin_list(obs, 3, 1000)
    fin_list(acts, 3, 1000)
    if (len(obs) != len(acts) or type(max_lag) is not int
            or not 0 <= max_lag <= len(obs) - 3):
        raise ValueError


def lag_score(obs, acts, k):
    n = len(obs)
    low, high = max(0, -k), min(n, n - k)
    xs = [obs[i] for i in range(low, high)]
    ys = [acts[i + k] for i in range(low, high)]
    m = len(xs)
    mx, my = sum(xs)/m, sum(ys)/m
    sxx = sum((x - mx)**2 for x in xs)
    syy = sum((y - my)**2 for y in ys)
    sxy = sum((x - mx)*(y - my) for x, y in zip(xs, ys))
    return ((syy - sxy*sxy/sxx) if sxx else syy)/m


def core_lag(obs, acts, max_lag, score=lag_score, lags=None):
    lags = lags if lags is not None else range(-max_lag, max_lag + 1)
    return min(lags, key=lambda k: (score(obs, acts, k), abs(k), k))


def lag_with(core):
    def run(obs, acts, max_lag):
        check_lag(obs, acts, max_lag)
        return core(obs, acts, max_lag)
    return run


refs = {'qa_episode': qa_episode_with(core_qa),
        'qa_dataset': dataset_with(core_dataset),
        'split_by_session': split_with(core_split),
        'leaked_ids': leak_with(core_leak),
        'fit_linear': fit_with(core_fit),
        'bc_baseline': bc_with(core_bc),
        'best_lag': lag_with(core_lag)}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


# ---- valid alternatives (different formulations) ----
def qa_pairs(times, obs, acts, max_gap, obs_range, act_range):
    """Tuple result, zip-based, each defect a named predicate."""
    if len(times) + len(obs) + len(acts) == 0:
        return ('empty',)
    lo, hi = obs_range
    alo, ahi = act_range
    tests = [
        ('length-mismatch', len({len(times), len(obs), len(acts)}) > 1),
        ('time-not-increasing', any(not b > a for a, b in zip(times, times[1:]))),
        ('time-gap', any(b - a - 1e-9 > max_gap for a, b in zip(times, times[1:]))),
        ('non-finite-value', not all(math.isfinite(v) for v in obs) or
         not all(math.isfinite(v) for v in acts)),
        ('obs-out-of-range', any(v < lo or v > hi for v in obs if v == v and abs(v) != math.inf)),
        ('act-out-of-range', any(v < alo or v > ahi for v in acts if v - v == 0)),
    ]
    return tuple(name for name, hit in tests if hit)


def dataset_seen(episodes, max_gap, obs_range, act_range):
    """Hash-based duplicate detection, tuple entries."""
    seen, out = set(), []
    for i, ep in enumerate(episodes):
        key = (tuple(ep[0]), tuple(ep[1]), tuple(ep[2]))
        names = list(qa_pairs(*ep, max_gap, obs_range, act_range))
        if key in seen:
            names.append('duplicate')
        seen.add(key)
        if names:
            out.append((i, tuple(names)))
    return tuple(out)


def split_dict(sessions, test_sessions):
    """Per-session buckets, then tuple outputs."""
    side = {s: s in set(test_sessions) for s in sessions}
    train, test = [], []
    for i, s in enumerate(sessions):
        (test if side[s] else train).append(i)
    return (tuple(train), tuple(test))


def leak_loop(train_ids, test_ids):
    out = []
    for item in sorted(train_ids):
        if item in test_ids and item not in out:
            out.append(item)
    return tuple(out)


def fit_cramer(obs, acts):
    """2x2 normal equations [[Sxx, Sx], [Sx, n]] (w, b) = (Sxa, Sa) by Cramer's rule."""
    n = len(obs)
    sx, sa = sum(obs), sum(acts)
    sxx = sum(o*o for o in obs)
    sxa = sum(o*a for o, a in zip(obs, acts))
    det = sxx*n - sx*sx
    return [(sxa*n - sx*sa)/det, (sxx*sa - sx*sxa)/det]


def fit_fraction(obs, acts):
    n = len(obs)
    xs, ys = [Fraction(v) for v in obs], [Fraction(v) for v in acts]
    sx, sy = sum(xs), sum(ys)
    w = (n*sum(x*y for x, y in zip(xs, ys)) - sx*sy)/(n*sum(x*x for x in xs) - sx*sx)
    return (float(w), float((sy - w*sx)/n))


def bc_fraction(episodes, fit_indices, eval_indices):
    fx, fy = pooled(episodes, fit_indices, 1), pooled(episodes, fit_indices, 2)
    w, b = (Fraction(v) for v in fit_fraction(fx, fy))
    n = len(fy)
    xs, ys = [Fraction(v) for v in fx], [Fraction(v) for v in fy]
    sx, sy = sum(xs), sum(ys)
    w = (n*sum(x*y for x, y in zip(xs, ys)) - sx*sy)/(n*sum(x*x for x in xs) - sx*sx)
    b = (sy - w*sx)/n
    mean = sy/n
    ex = [Fraction(v) for v in pooled(episodes, eval_indices, 1)]
    ey = [Fraction(v) for v in pooled(episodes, eval_indices, 2)]
    return [float(w), float(b), float(sum((y - w*x - b)**2 for x, y in zip(ex, ey))/len(ex)),
            float(sum((y - mean)**2 for y in ey)/len(ey))]


def bc_stepwise(episodes, fit_indices, eval_indices):
    """Cramer's-rule fit, then accumulate squared error per eval step in a generator."""
    fx, fy = pooled(episodes, fit_indices, 1), pooled(episodes, fit_indices, 2)
    w, b = fit_cramer(fx, fy)
    mean = sum(fy)/len(fy)
    count = total_bc = total_mean = 0
    for i in eval_indices:
        for x, y in zip(episodes[i][1], episodes[i][2]):
            count += 1
            total_bc += (w*x + b - y)**2
            total_mean += (y - mean)**2
    return (w, b, total_bc/count, total_mean/count)


def lag_residual_direct(obs, acts, max_lag):
    """Fit the line with fit_cramer-free closed form, then sum residuals directly."""
    n = len(obs)
    best = None
    for k in sorted(range(-max_lag, max_lag + 1), key=lambda k: (abs(k), k)):
        pairs = [(obs[i], acts[i + k]) for i in range(n) if 0 <= i + k < n]
        m = len(pairs)
        mx = sum(p[0] for p in pairs)/m
        my = sum(p[1] for p in pairs)/m
        sxx = sum((p[0] - mx)**2 for p in pairs)
        w = sum((p[0] - mx)*(p[1] - my) for p in pairs)/sxx if sxx else 0.0
        score = sum((p[1] - my - w*(p[0] - mx))**2 for p in pairs)/m
        if best is None or score < best[0] - 1e-12:
            best = (score, k)
    return best[1]


alternatives = [
    ('author reference', {}),
    ('zip-based tuple results, hash duplicates, bucket split, loop leak',
     {'qa_episode': qa_episode_with(qa_pairs), 'qa_dataset': dataset_with(dataset_seen),
      'split_by_session': split_with(split_dict), 'leaked_ids': leak_with(leak_loop)}),
    ('Cramer 2x2 normal equations with list results, stepwise BC',
     {'fit_linear': fit_with(fit_cramer), 'bc_baseline': bc_with(bc_stepwise)}),
    ('exact Fraction fit and BC, residual-direct lag search',
     {'fit_linear': fit_with(fit_fraction), 'bc_baseline': bc_with(bc_fraction),
      'best_lag': lag_with(lag_residual_direct)}),
    ('tuple qa results with dataset built on them, Cramer-based BC through fit_cramer',
     {'qa_episode': qa_episode_with(lambda *a: tuple(core_qa(*a))),
      'qa_dataset': dataset_with(lambda e, g, o, a: core_dataset(e, g, o, a, qa=qa_pairs)),
      'bc_baseline': bc_with(lambda e, f, v: core_bc(e, f, v, fit=fit_cramer))}),
    ('episode-level dedupe via any-prior comparison on tuples',
     {'qa_dataset': dataset_with(lambda e, g, o, a: core_dataset(
         e, g, o, a, dup=lambda i, ep, eps: tuple(map(tuple, ep)) in
         [tuple(map(tuple, x)) for x in eps[:i]]))}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result))


# ---- injected bugs ----
def over_qa(core):
    return {'qa_episode': qa_episode_with(core)}


def over_dataset(core):
    return {'qa_dataset': dataset_with(core)}


def over_split(core):
    return {'split_by_session': split_with(core)}


def over_leak(core):
    return {'leaked_ids': leak_with(core)}


def over_fit(core):
    return {'fit_linear': fit_with(core)}


def over_bc(core):
    return {'bc_baseline': bc_with(core)}


def over_lag(core):
    return {'best_lag': lag_with(core)}


def qa_variant(**flags):
    """Reference qa_episode with named deviations."""
    def core(times, obs, acts, max_gap, obs_range, act_range):
        if not (times or obs or acts):
            return [] if flags.get('empty_clean') else ['empty']
        out = []
        n3 = len(times) == len(obs) == len(acts)
        mism = (len(obs) != len(acts)) if flags.get('mismatch_obs_acts') else not n3
        if mism:
            out.append('length-mismatch')
            if flags.get('early_return'):
                return out
        steps = [b - a for a, b in zip(times, times[1:])]
        if any((s < 0) if flags.get('strict_time') else (s <= 0) for s in steps):
            out.append('time-not-increasing')
        eps = 0.0 if flags.get('no_eps') else 1e-3 if flags.get('big_eps') else 1e-9
        if flags.get('gap_ge'):
            gap = any(s >= max_gap for s in steps)
        elif flags.get('gap_abs'):
            gap = any(abs(s) > max_gap + eps for s in steps)
        else:
            gap = any(s > max_gap + eps for s in steps)
        if gap:
            out.append('time-gap')
        values = [*obs, *acts] if not flags.get('nonfinite_obs_only') else list(obs)
        if flags.get('nan_only'):
            nonfinite = any(v != v for v in values)
        else:
            nonfinite = any(not math.isfinite(v) for v in values)
        if nonfinite:
            out.append('non-finite-value')
        keep = (lambda v: True) if flags.get('nan_range') else math.isfinite
        if flags.get('nan_only') or flags.get('inf_range'):
            keep = lambda v: v == v
        lo, hi = obs_range
        alo, ahi = act_range
        if flags.get('swap_ranges'):
            lo, hi, alo, ahi = alo, ahi, lo, hi
        if flags.get('exclusive'):
            def inside(v, a, b):
                return a < v < b
        else:
            def inside(v, a, b):
                return a <= v <= b
        if any(keep(v) and not inside(v, lo, hi) for v in obs):
            out.append('obs-out-of-range')
        if not flags.get('obs_only') and any(keep(v) and not inside(v, alo, ahi) for v in acts):
            out.append('act-out-of-range')
        if flags.get('sorted_names'):
            out.sort()
        return out
    return core


def qa_sorts_input(times, obs, acts, max_gap, obs_range, act_range):
    if isinstance(times, list):
        times.sort()
    return core_qa(times, obs, acts, max_gap, obs_range, act_range)


def dataset_variant(**flags):
    def core(episodes, max_gap, obs_range, act_range):
        out = []
        for i, ep in enumerate(episodes):
            names = core_qa(ep[0], ep[1], ep[2], max_gap, obs_range, act_range)
            if flags.get('only_obs'):
                copy = any(list(ep[1]) == list(e[1]) for e in episodes[:i])
            elif flags.get('adjacent'):
                copy = i > 0 and tuple(map(tuple, ep)) == tuple(map(tuple, episodes[i-1]))
            elif flags.get('first_too'):
                copy = sum(tuple(map(tuple, ep)) == tuple(map(tuple, e)) for e in episodes) > 1
            elif flags.get('acts_only'):
                copy = any(list(ep[2]) == list(e[2]) for e in episodes[:i])
            elif flags.get('skip_times'):
                copy = any(list(ep[1]) == list(e[1]) and list(ep[2]) == list(e[2])
                           for e in episodes[:i])
            else:
                copy = any(tuple(map(tuple, ep)) == tuple(map(tuple, e)) for e in episodes[:i])
            if flags.get('clean_only') and names:
                copy = False
            if copy and flags.get('dup_first'):
                names = ['duplicate'] + names
            elif copy:
                names = names + ['duplicate']
            if names or flags.get('all_entries'):
                out.append((i, names))
        return out
    return core


def fit_variant(kind):
    def core(obs, acts):
        n = len(obs)
        mo, ma = sum(obs)/n, sum(acts)/n
        sxx = sum((o - mo)**2 for o in obs)
        syy = sum((a - ma)**2 for a in acts)
        sxy = sum((o - mo)*(a - ma) for o, a in zip(obs, acts))
        if kind == 'through-origin':
            w = sum(o*a for o, a in zip(obs, acts))/sum(o*o for o in obs)
            return (w, 0.0)
        if kind == 'inverse-regression':
            if sxy == 0:
                return (0.0, ma)
            w = syy/sxy
            return (w, ma - w*mo)
        if kind == 'swapped-intercept':
            w = sxy/sxx
            return (w, mo - w*ma)
        if kind == 'sample-var':
            w = (sxy/n)/(sxx/(n - 1))
            return (w, ma - w*mo)
        if kind == 'first-two':
            w = (acts[1] - acts[0])/(obs[1] - obs[0]) if obs[1] != obs[0] else 0.0
            return (w, acts[0] - w*obs[0])
        if kind == 'no-n':
            sx, sa = sum(obs), sum(acts)
            w = (sum(o*a for o, a in zip(obs, acts)) - sx*sa)/(sum(o*o for o in obs) - sx*sx)
            return (w, (sa - w*sx)/n)
        if kind == 'ratio':
            w = sum(acts)/sum(obs) if sum(obs) else 0.0
            return (w, 0.0)
        if kind == 'median-intercept':
            w = sxy/sxx
            ordered = sorted(a - w*o for o, a in zip(obs, acts))
            return (w, ordered[n//2])
        if kind == 'slope-sign':
            return (-sxy/sxx, ma + sxy/sxx*mo)
        if kind == 'mean-only':
            return (0.0, ma)
        raise ValueError
    return core


def fit_zero_division(obs, acts):
    """Divides by Sxx unguarded: raises ZeroDivisionError, not ValueError, on constant obs."""
    fin_list(obs, 2, 1000)
    fin_list(acts, 2, 1000)
    if len(obs) != len(acts):
        raise ValueError
    if max(obs) == min(obs):
        return 1/0
    return core_fit(obs, acts)


def bc_variant(kind):
    def core(episodes, fit_indices, eval_indices):
        everything = list(range(len(episodes)))
        fit_ids = list(fit_indices)
        eval_ids = list(eval_indices)
        if kind == 'fit-all':
            fit_ids = everything
        elif kind == 'fit-union':
            fit_ids = sorted(set(fit_ids) | set(eval_ids))
        elif kind == 'fit-on-eval':
            fit_ids = eval_ids
        elif kind == 'first-fit-only':
            fit_ids = fit_ids[:1]
        elif kind == 'overlap-guard':
            if set(fit_ids) & set(eval_ids):
                raise ValueError
        w, b, mse_bc, mse_mean = core_bc(episodes, fit_ids, eval_ids)
        if kind == 'episode-mean':
            per = []
            for i in eval_ids:
                xs, ys = episodes[i][1], episodes[i][2]
                per.append(sum((y - (w*x + b))**2 for x, y in zip(xs, ys))/len(xs))
            mse_bc = sum(per)/len(per)
        fy = pooled(episodes, fit_ids, 2)
        ey = pooled(episodes, eval_ids, 2)
        ex = pooled(episodes, eval_ids, 1)
        if kind == 'eval-mean-baseline':
            m = sum(ey)/len(ey)
            mse_mean = sum((y - m)**2 for y in ey)/len(ey)
        elif kind == 'all-mean-baseline':
            allm = sum(v for e in episodes for v in e[2])/sum(len(e[2]) for e in episodes)
            mse_mean = sum((y - allm)**2 for y in ey)/len(ey)
        elif kind == 'zero-baseline':
            mse_mean = sum(y*y for y in ey)/len(ey)
        elif kind == 'rmse':
            mse_bc, mse_mean = math.sqrt(mse_bc), math.sqrt(mse_mean)
        elif kind == 'mae':
            mse_bc = sum(abs(y - (w*x + b)) for x, y in zip(ex, ey))/len(ex)
        elif kind == 'sum':
            mse_bc, mse_mean = mse_bc*len(ex), mse_mean*len(ex)
        elif kind == 'train-mse':
            mse_bc = sum((y - (w*x + b))**2 for x, y in zip(pooled(episodes, fit_ids, 1), fy))/len(fy)
        elif kind == 'swap-order':
            return (mse_bc, mse_mean, w, b)
        elif kind == 'unbiased':
            mse_bc = mse_bc*len(ex)/max(len(ex) - 1, 1)
        elif kind == 'mean-of-last-fit':
            m = sum(episodes[fit_ids[-1]][2])/len(episodes[fit_ids[-1]][2])
            mse_mean = sum((y - m)**2 for y in ey)/len(ey)
        return (w, b, mse_bc, mse_mean)
    return core


def lag_variant(kind):
    def score_sign(obs, acts, k):
        return lag_score(obs, acts, -k)

    def score_sum(obs, acts, k):
        n = len(obs)
        return lag_score(obs, acts, k)*(n - abs(k))

    def score_corr(obs, acts, k):
        n = len(obs)
        low, high = max(0, -k), min(n, n - k)
        xs = [obs[i] for i in range(low, high)]
        ys = [acts[i + k] for i in range(low, high)]
        m = len(xs)
        mx, my = sum(xs)/m, sum(ys)/m
        sxx = sum((x - mx)**2 for x in xs)
        syy = sum((y - my)**2 for y in ys)
        sxy = sum((x - mx)*(y - my) for x, y in zip(xs, ys))
        return -(sxy*sxy/(sxx*syy)) if sxx and syy else 0.0

    def score_raw(obs, acts, k):
        n = len(obs)
        low, high = max(0, -k), min(n, n - k)
        return sum((acts[i + k] - obs[i])**2 for i in range(low, high))/(high - low)

    def score_cyclic(obs, acts, k):
        n = len(obs)
        xs = list(obs)
        ys = [acts[(i + k) % n] for i in range(n)]
        mx, my = sum(xs)/n, sum(ys)/n
        sxx = sum((x - mx)**2 for x in xs)
        syy = sum((y - my)**2 for y in ys)
        sxy = sum((x - mx)*(y - my) for x, y in zip(xs, ys))
        return ((syy - sxy*sxy/sxx) if sxx else syy)/n

    def score_truncated(obs, acts, k):
        n = len(obs)
        a = obs[:n - abs(k)]
        b = acts[:n - abs(k)]
        return lag_score(a, b, 0) if a else 0.0

    def core(obs, acts, max_lag):
        if kind == 'nonneg':
            return core_lag(obs, acts, max_lag, lags=range(0, max_lag + 1))
        if kind == 'sign':
            return core_lag(obs, acts, max_lag, score=score_sign)
        if kind == 'sum':
            return core_lag(obs, acts, max_lag, score=score_sum)
        if kind == 'corr':
            return core_lag(obs, acts, max_lag, score=score_corr)
        if kind == 'raw':
            return core_lag(obs, acts, max_lag, score=score_raw)
        if kind == 'cyclic':
            return core_lag(obs, acts, max_lag, score=score_cyclic)
        if kind == 'truncate':
            return core_lag(obs, acts, max_lag, score=score_truncated)
        if kind == 'offset':
            return core_lag(obs, acts, max_lag) + max_lag
        if kind == 'zero-guard':
            if max_lag == 0:
                raise ValueError
        if kind == 'float':
            return float(core_lag(obs, acts, max_lag))
        if kind == 'bool':
            return bool(core_lag(obs, acts, max_lag)) if core_lag(obs, acts, max_lag) in (0, 1) \
                else core_lag(obs, acts, max_lag)
        if kind == 'score':
            k = core_lag(obs, acts, max_lag)
            return lag_score(obs, acts, k)
        return core_lag(obs, acts, max_lag)
    return core


def split_variant(kind):
    def core(sessions, test_sessions):
        held = list(test_sessions)
        if kind == 'dup':
            test = [i for t in held for i, s in enumerate(sessions) if s == t]
            return ([i for i, s in enumerate(sessions) if s not in held], test)
        if kind == 'swap':
            return ([i for i, s in enumerate(sessions) if s in held],
                    [i for i, s in enumerate(sessions) if s not in held])
        if kind == 'prefix':
            test = [i for i, s in enumerate(sessions) if any(s.startswith(t) for t in held)]
            return ([i for i in range(len(sessions)) if i not in test], test)
        if kind == 'grouped-order':
            train = sorted((i for i, s in enumerate(sessions) if s not in held),
                           key=lambda i: (sessions[i], i))
            return (train, [i for i, s in enumerate(sessions) if s in held])
        if kind == 'session-index':
            names = sorted(set(sessions))
            return ([names.index(s) for s in sessions if s not in held],
                    [names.index(s) for s in sessions if s in held])
        if kind == 'first-of-session':
            seen, test = set(), []
            for i, s in enumerate(sessions):
                if s in held and s not in seen:
                    seen.add(s)
                    test.append(i)
            return ([i for i in range(len(sessions)) if i not in test], test)
        if kind == 'episode-level':
            test = [i for i, s in enumerate(sessions) if s in held][::2]
            return ([i for i in range(len(sessions)) if i not in test], test)
        raise ValueError
    return core


def leak_variant(kind):
    def core(train_ids, test_ids):
        if kind == 'dups':
            return sorted(i for i in train_ids if i in test_ids)
        if kind == 'natural':
            def key(s):
                head, _, tail = s.rpartition('-')
                return (head, int(tail)) if tail.isdigit() else (s, 0)
            return sorted(set(train_ids) & set(test_ids), key=key)
        if kind == 'casefold':
            tests = {s.lower() for s in test_ids}
            return sorted({s for s in train_ids if s.lower() in tests})
        if kind == 'train-only':
            return sorted(set(train_ids) - set(test_ids))
        if kind == 'union':
            return sorted(set(train_ids) | set(test_ids))
        if kind == 'unsorted':
            return list(dict.fromkeys(i for i in test_ids if i in train_ids))
        if kind == 'count':
            return len(set(train_ids) & set(test_ids))
        raise ValueError
    return core


def accepts_when(check, name):
    """Reference validation except one named gap: returns a plausible value instead."""
    plausible = {'qa_episode': [], 'qa_dataset': [], 'split_by_session': ([0], [1]),
                 'leaked_ids': [], 'fit_linear': (0.0, 0.0), 'bc_baseline': (0.0, 0.0, 0.0, 0.0),
                 'best_lag': 0}[name]

    def run(*args):
        if check(*args):
            return plausible
        return refs[name](*args)
    return {name: run}


def is_num(v):
    return type(v) in (int, float)


def contains(seq, test):
    return isinstance(seq, (list, tuple)) and any(test(v) for v in seq)


mutants = [
    ('qa: time-gap tolerance 1e-3', over_qa(qa_variant(big_eps=True))),
    ('qa: gap flagged at >= max_gap', over_qa(qa_variant(gap_ge=True))),
    ('qa: no float tolerance on the gap', over_qa(qa_variant(no_eps=True))),
    ('qa: repeated timestamp allowed (< instead of <=)', over_qa(qa_variant(strict_time=True))),
    ('qa: gap uses |step| so a backwards jump is a gap', over_qa(qa_variant(gap_abs=True))),
    ('qa: NaN counted out of range', over_qa(qa_variant(nan_range=True))),
    ('qa: inf counted out of range', over_qa(qa_variant(inf_range=True))),
    ('qa: only NaN is non-finite (inf missed)', over_qa(qa_variant(nan_only=True))),
    ('qa: non-finite checked in obs only', over_qa(qa_variant(nonfinite_obs_only=True))),
    ('qa: range edges exclusive', over_qa(qa_variant(exclusive=True))),
    ('qa: obs and act ranges swapped', over_qa(qa_variant(swap_ranges=True))),
    ('qa: act range never checked', over_qa(qa_variant(obs_only=True))),
    ('qa: length mismatch ignores times', over_qa(qa_variant(mismatch_obs_acts=True))),
    ('qa: mismatch returns early and hides other defects', over_qa(qa_variant(early_return=True))),
    ('qa: empty episode reported clean', over_qa(qa_variant(empty_clean=True))),
    ('qa: names sorted alphabetically', over_qa(qa_variant(sorted_names=True))),
    ('qa: out-of-range name repeated per sample', over_qa(
        lambda t, o, a, g, orr, arr: core_qa(t, o, a, g, orr, arr) + [
            'obs-out-of-range' for v in o if math.isfinite(v) and not orr[0] <= v <= orr[1]][1:])),
    ('qa: sorts the caller times in place', over_qa(qa_sorts_input)),
    ('qa: bool max_gap accepted', accepts_when(lambda *a: type(a[3]) is bool, 'qa_episode')),
    ('qa: NaN timestamp accepted', accepts_when(
        lambda *a: contains(a[0], lambda v: type(v) is float and v != v), 'qa_episode')),
    ('qa: reversed range accepted', accepts_when(
        lambda *a: isinstance(a[4], (list, tuple)) and len(a[4]) == 2 and all(map(is_num, a[4]))
        and a[4][0] > a[4][1], 'qa_episode')),
    ('dataset: first copy flagged too', over_dataset(dataset_variant(first_too=True))),
    ('dataset: duplicates compare observations only', over_dataset(dataset_variant(only_obs=True))),
    ('dataset: duplicates compare actions only', over_dataset(dataset_variant(acts_only=True))),
    ('dataset: duplicates ignore timestamps', over_dataset(dataset_variant(skip_times=True))),
    ('dataset: only adjacent copies found', over_dataset(dataset_variant(adjacent=True))),
    ('dataset: duplicate named first', over_dataset(dataset_variant(dup_first=True))),
    ('dataset: defective copies not flagged', over_dataset(dataset_variant(clean_only=True))),
    ('dataset: clean episodes listed with empty names', over_dataset(dataset_variant(all_entries=True))),
    ('split: repeated test session duplicates indices', over_split(split_variant('dup'))),
    ('split: sides swapped', over_split(split_variant('swap'))),
    ('split: session matched by prefix', over_split(split_variant('prefix'))),
    ('split: train sorted by session not by index', over_split(split_variant('grouped-order'))),
    ('split: returns session numbers not episode indices', over_split(split_variant('session-index'))),
    ('split: only the first episode of a session held out', over_split(split_variant('first-of-session'))),
    ('split: episode-level alternate hold-out (leaks sessions)', over_split(split_variant('episode-level'))),
    ('split: test_sessions given as one str accepted', accepts_when(
        lambda *a: type(a[1]) is str, 'split_by_session')),
    ('split: holding out every session accepted', {'split_by_session': lambda s, t: (
        ([], list(range(len(s)))) if isinstance(t, list) and isinstance(s, list)
        and t and set(t) == set(s) and all(type(x) is str for x in s) else refs['split_by_session'](s, t))}),
    ('leak: duplicates not removed', over_leak(leak_variant('dups'))),
    ('leak: numeric-aware sort', over_leak(leak_variant('natural'))),
    ('leak: case-insensitive match', over_leak(leak_variant('casefold'))),
    ('leak: train-only ids returned', over_leak(leak_variant('train-only'))),
    ('leak: union returned', over_leak(leak_variant('union'))),
    ('leak: test-side order kept', over_leak(leak_variant('unsorted'))),
    ('leak: count returned', over_leak(leak_variant('count'))),
    ('fit: line through the origin', over_fit(fit_variant('through-origin'))),
    ('fit: regress obs on acts and invert', over_fit(fit_variant('inverse-regression'))),
    ('fit: intercept mean(o) - w mean(a)', over_fit(fit_variant('swapped-intercept'))),
    ('fit: sample variance with population covariance', over_fit(fit_variant('sample-var'))),
    ('fit: only the first two points', over_fit(fit_variant('first-two'))),
    ('fit: normal equation without n', over_fit(fit_variant('no-n'))),
    ('fit: ratio sum(acts)/sum(obs)', over_fit(fit_variant('ratio'))),
    ('fit: median intercept', over_fit(fit_variant('median-intercept'))),
    ('fit: slope sign flipped', over_fit(fit_variant('slope-sign'))),
    ('fit: constant-obs ZeroDivisionError', {'fit_linear': fit_zero_division}),
    ('fit: constant observations accepted', accepts_when(
        lambda *a: isinstance(a[0], (list, tuple)) and len(a[0]) >= 2 and all(map(real, a[0]))
        and len(set(a[0])) == 1 and len(a[0]) == len(a[1]), 'fit_linear')),
    ('fit: NaN observation accepted', accepts_when(
        lambda *a: contains(a[0], lambda v: type(v) is float and v != v), 'fit_linear')),
    ('bc: fits on every episode (eval included)', over_bc(bc_variant('fit-all'))),
    ('bc: fits on fit plus eval episodes', over_bc(bc_variant('fit-union'))),
    ('bc: fits on the eval episodes', over_bc(bc_variant('fit-on-eval'))),
    ('bc: only the first fit episode used', over_bc(bc_variant('first-fit-only'))),
    ('bc: raises on overlapping indices', over_bc(bc_variant('overlap-guard'))),
    ('bc: episode-averaged MSE', over_bc(bc_variant('episode-mean'))),
    ('bc: baseline mean from the eval actions', over_bc(bc_variant('eval-mean-baseline'))),
    ('bc: baseline mean from the whole dataset', over_bc(bc_variant('all-mean-baseline'))),
    ('bc: zero-action baseline', over_bc(bc_variant('zero-baseline'))),
    ('bc: RMSE instead of MSE', over_bc(bc_variant('rmse'))),
    ('bc: MAE instead of MSE', over_bc(bc_variant('mae'))),
    ('bc: summed squared error', over_bc(bc_variant('sum'))),
    ('bc: training MSE reported', over_bc(bc_variant('train-mse'))),
    ('bc: result order (mse, mse, w, b)', over_bc(bc_variant('swap-order'))),
    ('bc: unbiased n-1 denominator', over_bc(bc_variant('unbiased'))),
    ('bc: baseline from the last fit episode only', over_bc(bc_variant('mean-of-last-fit'))),
    ('bc: negative index accepted', accepts_when(
        lambda *a: isinstance(a[1], (list, tuple)) and any(type(i) is int and i < 0 for i in a[1]),
        'bc_baseline')),
    ('bc: bool index accepted', accepts_when(
        lambda *a: isinstance(a[2], (list, tuple)) and any(type(i) is bool for i in a[2]),
        'bc_baseline')),
    ('bc: unequal episode lengths accepted', accepts_when(
        lambda *a: isinstance(a[0], (list, tuple)) and any(
            isinstance(e, (list, tuple)) and len(e) == 3 and len({len(x) for x in e if isinstance(x, (list, tuple))}) > 1
            for e in a[0]), 'bc_baseline')),
    ('lag: only non-negative lags searched', over_lag(lag_variant('nonneg'))),
    ('lag: pairing sign flipped', over_lag(lag_variant('sign'))),
    ('lag: summed instead of mean residual', over_lag(lag_variant('sum'))),
    ('lag: correlation score without line', over_lag(lag_variant('corr'))),
    ('lag: residual without fitting a line', over_lag(lag_variant('raw'))),
    ('lag: truncated head instead of shifted pairs', over_lag(lag_variant('truncate'))),
    ('lag: cyclic shift acts[(i+k) % n]', over_lag(lag_variant('cyclic'))),
    ('lag: index offset by max_lag returned', over_lag(lag_variant('offset'))),
    ('lag: max_lag = 0 rejected', over_lag(lag_variant('zero-guard'))),
    ('lag: float lag returned', over_lag(lag_variant('float'))),
    ('lag: score returned instead of lag', over_lag(lag_variant('score'))),
    ('lag: bool max_lag accepted', accepts_when(lambda *a: type(a[2]) is bool, 'best_lag')),
    ('lag: oversized max_lag accepted', accepts_when(
        lambda *a: isinstance(a[0], (list, tuple)) and type(a[2]) is int and a[2] > len(a[0]) - 3 >= 0
        and all(map(real, a[0])), 'best_lag')),
]
survivors = [label for label, over in mutants if not run_with(over)]
require(not survivors, 'false accept: ' + '; '.join(survivors))
print('Imitation kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
