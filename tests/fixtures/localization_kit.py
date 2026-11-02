"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different predict, update, resampling
and spread formulations) that must pass, and named injected bugs that must be
rejected for their intended reason. Plain checks only, so it also works under python -O.
"""
import ast
import bisect
import importlib.util
import json
import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('localization_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L09-localization.v1.py'
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
require(imported <= {'math', 'fractions', 'Fraction'}, 'kit imports beyond math/fractions: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
names = ('normalize', 'predict', 'sensor_likelihood', 'update', 'localize', 'modes',
         'effective_sample_size', 'particle_update', 'systematic_resample')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(all(text.index('def ' + ref) > spoiler for ref in
            ('_normalize_ref', '_predict_ref', '_resample_ref', '_localize_ref')),
        'oracle must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('localization_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter_notes = []
starter = kit.self_check(starter_notes)
require(starter, 'unimplemented starter must report failure')
require(all(failure.isascii() for failure in starter), 'starter failure messages must be ASCII')
require(len(starter) == 9 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented function into one line: ' + str(starter))
require(starter_notes == [], 'no optional parts in this kit')


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is bool:
        return 'cyclic' if value else 'walls'
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def encode(value):
    return [encode(v) for v in value] if isinstance(value, (list, tuple)) else dec(value)


def entry(structure, names_, args):
    return {'structure': structure,
            'inputs': {name: encode(value) for name, value in zip(names_, args)}}


expected_samples = (
    [entry('grid.normalize@1', ('weights',), (w,)) for w, _ in kit._NORM_CASES]
    + [entry('grid.predict@1', ('belief', 'kernel', 'offset0', 'motion'), a)
       for a, _ in kit._PRED_CASES]
    + [entry('grid.sensor-likelihood@1', ('world', 'z', 'p_correct'), a)
       for a, _ in kit._LIK_CASES]
    + [entry('grid.update@1', ('belief', 'likelihood'), a) for a, _ in kit._UPD_CASES]
    + [entry('grid.localize@1', ('belief', 'world', 'p_correct', 'kernel', 'offset0',
                                  'motion', 'observations'), a) for a, _ in kit._LOC_CASES]
    + [entry('grid.modes@1', ('belief',), (b,)) for b, _ in kit._MODE_CASES]
    + [entry('particles.ess@1', ('weights',), (w,)) for w, _ in kit._ESS_CASES]
    + [entry('particles.update@1', ('cells', 'weights', 'world', 'z', 'p_correct'), a)
       for a, _ in kit._PART_CASES]
    + [entry('particles.systematic-resample@1', ('weights', 'u0'), a)
       for a, _, _ in kit._RES_CASES])
SAMPLE_CAP = 50
# The manifest holds a representative subset (cap 50): every case of the smaller
# tables plus a spread of the longer ones. Build it with a deterministic stride.
def pick(items, count):
    if len(items) <= count:
        return list(items)
    step = (len(items) - 1) / (count - 1)
    return [items[round(i * step)] for i in range(count)]


groups = [
    ('grid.normalize@1', 3), ('grid.predict@1', 12), ('grid.sensor-likelihood@1', 3),
    ('grid.update@1', 4), ('grid.localize@1', 6), ('grid.modes@1', 3),
    ('particles.ess@1', 4), ('particles.update@1', 3), ('particles.systematic-resample@1', 8),
]
expected_manifest = []
for structure, count in groups:
    expected_manifest += pick([e for e in expected_samples if e['structure'] == structure], count)
require(len(expected_manifest) <= SAMPLE_CAP, 'kit sample cap is 50')
samples = json.loads((root / 'content/labs/L09-localization.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L09-localization'], 'samples must hold only L09-localization')
require(samples['kits']['L09-localization'] == expected_manifest,
        'samples manifest does not mirror the self-check cases')
require(all(e in expected_samples for e in samples['kits']['L09-localization']),
        'every sample must be a self-check case')


# ---- independent cross-check of the hand-derived tables ----
def total_ok(values, total=1.0):
    return abs(math.fsum(values) - total) <= 1e-12


for weights, hand in kit._NORM_CASES:
    if hand is not None:
        ref = kit._normalize_ref(weights)
        require(all(abs(float(a) - b) <= 1e-12 for a, b in zip(ref, hand)),
                'normalize hand table disagrees with the exact reference: ' + repr(weights))
for args, hand in kit._PRED_CASES:
    require(total_ok(args[0]) and total_ok(args[1]), 'predict case inputs must sum to 1: ' + repr(args))
    if hand is not None:
        ref = kit._predict_ref(*args)
        require(all(abs(float(a) - b) <= 1e-12 for a, b in zip(ref, hand)),
                'predict hand table disagrees with the exact reference: ' + repr(args))
for args, hand in kit._LIK_CASES:
    if hand is not None:
        ref = kit._likelihood_ref(*args)
        require(all(abs(float(a) - b) <= 1e-12 for a, b in zip(ref, hand)), 'likelihood hand table')
for args, hand in kit._UPD_CASES:
    require(total_ok(args[0]), 'update prior must sum to 1: ' + repr(args))
    if hand is not None:
        ref = kit._update_ref(*args)
        require(all(abs(float(a) - b) <= 1e-12 for a, b in zip(ref, hand)), 'update hand table')
for args, hand in kit._LOC_CASES:
    require(total_ok(args[0]), 'localize prior must sum to 1: ' + repr(args))
    if hand is not None:
        ref = kit._localize_ref(*args)
        require(all(abs(float(a) - b) <= 1e-12 for a, b in zip(ref, hand)), 'localize hand table')
for belief, hand in kit._MODE_CASES:
    require(abs(sum(belief) - 1) <= 1e-9, 'mode belief must be a distribution: ' + repr(belief))
    require(kit._modes_ref(belief) == hand, 'modes table disagrees with the reference')
for weights, hand in kit._ESS_CASES:
    if hand is not None:
        require(abs(float(kit._ess_ref(weights)) - hand) <= 1e-12, 'ESS hand table: ' + repr(weights))
for args, hand in kit._PART_CASES:
    if hand is not None:
        ref = kit._particle_ref(*args)
        require(all(abs(float(a) - b) <= 1e-12 for a, b in zip(ref, hand)), 'particle hand table')
for args, hand, kind in kit._RES_CASES:
    ref = kit._resample_ref(*args)
    if hand is not None:
        require(ref == hand, 'resample hand table disagrees with the exact reference: ' + repr(args))
    # Boundary margin: only the declared tie cases may put a position on a boundary.
    weights, u0 = args
    total = sum((Fraction(w) for w in weights), Fraction(0))
    n = len(weights)
    cum, running = [], Fraction(0)
    for w in weights:
        running += Fraction(w)
        cum.append(running / total)
    gaps = [abs((Fraction(u0) + k) / n - c) for k in range(n) for c in cum]
    if kind == 'tie':
        require(min(gaps) == 0, 'tie case has no exact boundary hit: ' + repr(args))
    elif kind in ('ref', 'hand'):
        require(min(gaps) > Fraction(1, 10 ** 6), 'non-tie case too close to a boundary: ' + repr(args))


# ---- author reference implementation ----
def check_number(value, low, high, open_high=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError
    if value < low or (value >= high if open_high else value > high):
        raise ValueError


def check_int(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError


def check_list(value, low, high, minimum, maximum):
    if not isinstance(value, (list, tuple)) or not minimum <= len(value) <= maximum:
        raise ValueError
    for v in value:
        check_number(v, low, high)
    return list(value)


def check_belief(belief, length=None):
    belief = check_list(belief, 0, 1, 2, 64)
    if abs(math.fsum(belief) - 1) > 1e-9 or (length is not None and len(belief) != length):
        raise ValueError
    return belief


def check_weights(weights):
    return check_list(weights, 0, 1e6, 1, 64)


def check_kernel(kernel):
    kernel = check_list(kernel, 0, 1, 1, 8)
    if abs(math.fsum(kernel) - 1) > 1e-9:
        raise ValueError
    return kernel


def check_world(world, length=None):
    if not isinstance(world, (list, tuple)) or not 2 <= len(world) <= 64:
        raise ValueError
    for w in world:
        check_int(w, 0, 1)
    if length is not None and len(world) != length:
        raise ValueError
    return list(world)


def check_cyclic(cyclic):
    if type(cyclic) is not bool:
        raise ValueError


def check_observations(observations):
    if not isinstance(observations, (list, tuple)) or len(observations) > 32:
        raise ValueError
    for z in observations:
        check_int(z, 0, 1)
    return list(observations)


def normalize(weights):
    weights = check_weights(weights)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    return [w / total for w in weights]


def predict_core(belief, kernel, offset0, cyclic):
    n = len(belief)
    out = [0.0] * n
    for i in range(n):
        for k in range(len(kernel)):
            j = i + offset0 + k
            j = j % n if cyclic else min(max(j, 0), n - 1)
            out[j] += belief[i] * kernel[k]
    return out


def predict(belief, kernel, offset0, cyclic):
    belief = check_belief(belief)
    kernel = check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    return predict_core(belief, kernel, offset0, cyclic)


def likelihood_core(world, z, p):
    return [p if w == z else 1 - p for w in world]


def sensor_likelihood(world, z, p_correct):
    world = check_world(world)
    check_int(z, 0, 1)
    check_number(p_correct, 0, 1)
    return likelihood_core(world, z, p_correct)


def update_core(belief, likelihood):
    products = [b * m for b, m in zip(belief, likelihood)]
    total = math.fsum(products)
    if total == 0:
        raise ValueError
    return [p / total for p in products]


def update(belief, likelihood):
    belief = check_belief(belief)
    likelihood = check_list(likelihood, 0, 1e6, 2, 64)
    if len(likelihood) != len(belief):
        raise ValueError
    return update_core(belief, likelihood)


def localize(belief, world, p_correct, kernel, offset0, cyclic, observations):
    belief = check_belief(belief)
    world = check_world(world, len(belief))
    check_number(p_correct, 0, 1)
    kernel = check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    observations = check_observations(observations)
    current = list(belief)
    for z in observations:
        current = update_core(current, likelihood_core(world, z, p_correct))
        current = predict_core(current, kernel, offset0, cyclic)
    return current


def modes(belief):
    belief = check_belief(belief)
    top = max(belief)
    return [i for i, b in enumerate(belief) if b >= top - 1e-9]


def effective_sample_size(weights):
    weights = check_weights(weights)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    return total * total / math.fsum(w * w for w in weights)


def particle_update(cells, weights, world, z, p_correct):
    weights = check_weights(weights)
    world = check_world(world)
    if not isinstance(cells, (list, tuple)) or len(cells) != len(weights):
        raise ValueError
    for c in cells:
        check_int(c, 0, len(world) - 1)
    check_int(z, 0, 1)
    check_number(p_correct, 0, 1)
    like = likelihood_core(world, z, p_correct)
    return update_core(weights, [like[c] for c in cells])


def resample_core(weights, u0):
    total = math.fsum(weights)
    n = len(weights)
    last = max(i for i, w in enumerate(weights) if w > 0)
    cum, running = [], 0.0
    for w in weights:
        running += w / total
        cum.append(running)
    out, i = [], 0
    for k in range(n):
        position = (u0 + k) / n
        while i < last and cum[i] <= position:
            i += 1
        out.append(i)
    return out


def systematic_resample(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    if math.fsum(weights) == 0:
        raise ValueError
    return resample_core(weights, u0)


refs = {name: globals()[name] for name in names}


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
def valid_dists(belief):
    return check_belief(belief)


def predict_matrix(belief, kernel, offset0, cyclic):
    """Build the full n x n transition matrix, then multiply."""
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    n = len(belief)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for k, pk in enumerate(kernel):
            j = (i + offset0 + k) % n if cyclic else min(max(i + offset0 + k, 0), n - 1)
            matrix[j][i] += pk
    return [math.fsum(matrix[j][i] * belief[i] for i in range(n)) for j in range(n)]


def predict_fold(belief, kernel, offset0, cyclic):
    """Full linear convolution on an extended index range, then fold the ends."""
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    n, m = len(belief), len(kernel)
    low = offset0
    wide = {}
    for i in range(n):
        for k in range(m):
            wide[i + low + k] = wide.get(i + low + k, 0.0) + belief[i] * kernel[k]
    out = [0.0] * n
    for position, mass in wide.items():
        target = position % n if cyclic else (0 if position < 0 else n - 1 if position > n - 1 else position)
        out[target] += mass
    return out


def predict_gather(belief, kernel, offset0, cyclic):
    """For each destination cell, gather from every source cell that can reach it."""
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    n = len(belief)
    out = []
    for j in range(n):
        acc = 0.0
        for i in range(n):
            for k in range(len(kernel)):
                d = offset0 + k
                landed = (i + d) % n if cyclic else min(max(i + d, 0), n - 1)
                if landed == j:
                    acc += belief[i] * kernel[k]
        out.append(acc)
    return out


def update_log(belief, likelihood):
    belief = check_belief(belief)
    likelihood = check_list(likelihood, 0, 1e6, 2, 64)
    if len(likelihood) != len(belief):
        raise ValueError
    logs = [math.log(b) + math.log(m) if b > 0 and m > 0 else None for b, m in zip(belief, likelihood)]
    live = [v for v in logs if v is not None]
    if not live:
        raise ValueError
    top = max(live)
    expd = [math.exp(v - top) if v is not None else 0.0 for v in logs]
    total = math.fsum(expd)
    return [v / total for v in expd]


def normalize_exact(weights):
    weights = check_weights(weights)
    total = sum((Fraction(w) for w in weights), Fraction(0))
    if total == 0:
        raise ValueError
    return [float(Fraction(w) / total) for w in weights]


def likelihood_branchless(world, z, p_correct):
    world = check_world(world)
    check_int(z, 0, 1)
    check_number(p_correct, 0, 1)
    return [(1 - abs(w - z)) * p_correct + abs(w - z) * (1 - p_correct) for w in world]


def localize_compose(belief, world, p_correct, kernel, offset0, cyclic, observations):
    check_belief(belief)
    check_observations(observations)
    current = list(belief)
    for z in observations:
        current = update(current, sensor_likelihood(world, z, p_correct))
        current = predict(current, kernel, offset0, cyclic)
    if not observations:
        # still validate everything the loop would have validated
        sensor_likelihood(world, 0, p_correct)
        predict(belief, kernel, offset0, cyclic)
    return list(current)


def modes_sorted(belief):
    belief = check_belief(belief)
    top = max(belief)
    order = sorted(range(len(belief)), key=lambda i: (-belief[i], i))
    return [i for i in sorted(order) if top - belief[i] <= 1e-9]


def ess_normalized(weights):
    weights = check_weights(weights)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    return 1.0 / math.fsum((w / total) ** 2 for w in weights)


def particle_via_grid(cells, weights, world, z, p_correct):
    weights = check_weights(weights)
    world = check_world(world)
    if not isinstance(cells, (list, tuple)) or len(cells) != len(weights):
        raise ValueError
    for c in cells:
        check_int(c, 0, len(world) - 1)
    check_int(z, 0, 1)
    check_number(p_correct, 0, 1)
    mass = [0.0] * len(world)
    for c, w in zip(cells, weights):
        mass[c] += w
    like = likelihood_core(world, z, p_correct)
    out = [w * like[c] for c, w in zip(cells, weights)]
    total = math.fsum(out)
    if total == 0:
        raise ValueError
    return [v / total for v in out]


def resample_bisect(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    n = len(weights)
    last = max(i for i, w in enumerate(weights) if w > 0)
    cum, running = [], 0.0
    for w in weights:
        running += w
        cum.append(running)
    return [min(bisect.bisect_right(cum, ((u0 + k) / n) * total), last) for k in range(n)]


def resample_exact(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    if math.fsum(weights) == 0:
        raise ValueError
    return kit._resample_ref(weights, u0)


def resample_counts(weights, u0):
    """Build the copy counts per particle, then expand them into the sorted index list."""
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    n = len(weights)
    last = max(i for i, w in enumerate(weights) if w > 0)
    counts = [0] * n
    edge, i = 0.0, 0
    for k in range(n):
        position = (u0 + k) / n
        while i < last and (edge + weights[i] / total) <= position:
            edge += weights[i] / total
            i += 1
        counts[i] += 1
    return [i for i, c in enumerate(counts) for _ in range(c)]


alternatives = [
    ('author: scatter predict, fsum, bisect-free two-pointer resample', {}),
    ('transition-matrix predict, log-space update, exact-Fraction normalize',
     {'predict': predict_matrix, 'update': update_log, 'normalize': normalize_exact}),
    ('convolve-then-fold predict, branch-free likelihood, composed localize, normalized ESS',
     {'predict': predict_fold, 'sensor_likelihood': likelihood_branchless,
      'localize': localize_compose, 'effective_sample_size': ess_normalized}),
    ('gather predict, sorted modes, particle update via cell masses, bisect resample',
     {'predict': predict_gather, 'modes': modes_sorted, 'particle_update': particle_via_grid,
      'systematic_resample': resample_bisect}),
    ('exact-Fraction resample, matrix predict, log update',
     {'systematic_resample': resample_exact, 'predict': predict_matrix, 'update': update_log}),
    ('count-based resample, fold predict, composed localize',
     {'systematic_resample': resample_counts, 'predict': predict_fold,
      'localize': localize_compose}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result))


# ---- injected bugs: (label, overrides, substring that must appear in a failure) ----
def lenient(function, condition, dummy):
    """Reference behaviour, except it returns `dummy` instead of rejecting when condition holds."""
    def run(*args):
        if condition(*args):
            return dummy
        return function(*args)
    return run


nan = float('nan')


def n_max(weights):
    weights = check_weights(weights)
    top = max(weights)
    if top == 0:
        raise ValueError
    return [w / top for w in weights]


def n_uniform_on_zero(weights):
    weights = check_weights(weights)
    total = math.fsum(weights)
    if total == 0:
        return [1 / len(weights)] * len(weights)
    return [w / total for w in weights]


def n_smoothed(weights):
    weights = check_weights(weights)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    return [(w + 1e-6) / (total + 1e-6 * len(weights)) for w in weights]


def p_lossy_walls(belief, kernel, offset0, cyclic):
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    n = len(belief)
    out = [0.0] * n
    for i in range(n):
        for k in range(len(kernel)):
            j = i + offset0 + k
            if cyclic:
                j %= n
            elif not 0 <= j < n:
                continue
            out[j] += belief[i] * kernel[k]
    return out


def p_blocked_walls(belief, kernel, offset0, cyclic):
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    n = len(belief)
    out = [0.0] * n
    for i in range(n):
        for k in range(len(kernel)):
            j = i + offset0 + k
            j = j % n if cyclic else (j if 0 <= j < n else i)
            out[j] += belief[i] * kernel[k]
    return out


def p_always_walls(belief, kernel, offset0, cyclic):
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    return predict_core(belief, kernel, offset0, False)


def p_reversed_direction(belief, kernel, offset0, cyclic):
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    return predict_core(belief, kernel[::-1], -(offset0 + len(kernel) - 1), cyclic)


def p_negated_offset(belief, kernel, offset0, cyclic):
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    return predict_core(belief, kernel, -offset0, cyclic)


def p_ignores_offset(belief, kernel, offset0, cyclic):
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    return predict_core(belief, kernel, -(len(kernel) // 2), cyclic)


def p_mutates(belief, kernel, offset0, cyclic):
    out = predict(belief, kernel, offset0, cyclic)
    if isinstance(belief, list):
        belief[:] = out
    return out


def p_normalizes_zero_mass(belief, kernel, offset0, cyclic):
    out = predict(belief, kernel, offset0, cyclic)
    return [v * 1.0000001 for v in out]


def l_swapped(world, z, p_correct):
    world = check_world(world)
    check_int(z, 0, 1)
    check_number(p_correct, 0, 1)
    return [1 - p_correct if w == z else p_correct for w in world]


def l_normalized(world, z, p_correct):
    values = sensor_likelihood(world, z, p_correct)
    total = math.fsum(values)
    return [v / total for v in values] if total else values


def l_ignores_z(world, z, p_correct):
    return sensor_likelihood(world, 1, p_correct) if z in (0, 1) and type(z) is int \
        else sensor_likelihood(world, z, p_correct)


def u_unnormalized(belief, likelihood):
    update(belief, likelihood)
    return [b * m for b, m in zip(belief, likelihood)]


def u_adds(belief, likelihood):
    update(belief, likelihood)
    s = [b + m for b, m in zip(belief, likelihood)]
    t = math.fsum(s)
    return [v / t for v in s]


def u_uniform_on_zero(belief, likelihood):
    try:
        return update(belief, likelihood)
    except ValueError:
        if (isinstance(belief, list) and isinstance(likelihood, list)
                and len(belief) == len(likelihood) and abs(math.fsum(belief) - 1) <= 1e-9):
            return [1 / len(belief)] * len(belief)
        raise


def u_prior_on_zero(belief, likelihood):
    try:
        return update(belief, likelihood)
    except ValueError:
        if (isinstance(belief, list) and isinstance(likelihood, list)
                and len(belief) == len(likelihood) and abs(math.fsum(belief) - 1) <= 1e-9):
            return list(belief)
        raise


def u_ignores_prior(belief, likelihood):
    belief = check_belief(belief)
    return normalize(likelihood) if len(likelihood) == len(belief) else update(belief, likelihood)


def u_max_normalized(belief, likelihood):
    update(belief, likelihood)
    products = [b * m for b, m in zip(belief, likelihood)]
    top = max(products)
    return [p / top for p in products]


def u_mutates(belief, likelihood):
    out = update(belief, likelihood)
    if isinstance(belief, list):
        belief[:] = out
    return out


def loc_predict_first(belief, world, p_correct, kernel, offset0, cyclic, observations):
    belief = check_belief(belief)
    world = check_world(world, len(belief))
    check_number(p_correct, 0, 1)
    kernel = check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    observations = check_observations(observations)
    current = list(belief)
    for z in observations:
        current = predict_core(current, kernel, offset0, cyclic)
        current = update_core(current, likelihood_core(world, z, p_correct))
    return current


def loc_no_final_move(belief, world, p_correct, kernel, offset0, cyclic, observations):
    belief = check_belief(belief)
    world = check_world(world, len(belief))
    check_number(p_correct, 0, 1)
    kernel = check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    observations = check_observations(observations)
    current = list(belief)
    for index, z in enumerate(observations):
        current = update_core(current, likelihood_core(world, z, p_correct))
        if index < len(observations) - 1:
            current = predict_core(current, kernel, offset0, cyclic)
    return current


def loc_always_walls(belief, world, p_correct, kernel, offset0, cyclic, observations):
    check_cyclic(cyclic)
    return localize(belief, world, p_correct, kernel, offset0, False, observations)


def loc_swallows_zero(belief, world, p_correct, kernel, offset0, cyclic, observations):
    try:
        return localize(belief, world, p_correct, kernel, offset0, cyclic, observations)
    except ValueError:
        if isinstance(belief, list) and abs(math.fsum(belief) - 1) <= 1e-9 and 'x' != observations:
            try:
                localize(belief, world, 0.5, kernel, offset0, cyclic, [])
                return list(belief)
            except ValueError:
                raise
        raise


def loc_flips_z(belief, world, p_correct, kernel, offset0, cyclic, observations):
    if isinstance(observations, list) and all(type(z) is int and z in (0, 1) for z in observations):
        observations = [1 - z for z in observations]
    return localize(belief, world, p_correct, kernel, offset0, cyclic, observations)


def loc_empty_uniform(belief, world, p_correct, kernel, offset0, cyclic, observations):
    out = localize(belief, world, p_correct, kernel, offset0, cyclic, observations)
    return [1 / len(out)] * len(out) if observations == [] else out


def m_first_only(belief):
    belief = check_belief(belief)
    return [belief.index(max(belief))]


def m_exact_ties(belief):
    belief = check_belief(belief)
    top = max(belief)
    return [i for i, b in enumerate(belief) if b == top]


def m_loose_ties(belief):
    belief = check_belief(belief)
    top = max(belief)
    return [i for i, b in enumerate(belief) if b >= top - 1e-6]


def m_descending(belief):
    return modes(belief)[::-1]


def m_returns_value(belief):
    check_belief(belief)
    return [max(belief)]


def e_unnormalized(weights):
    weights = check_weights(weights)
    if math.fsum(weights) == 0:
        raise ValueError
    return 1.0 / math.fsum(w * w for w in weights)


def e_inverse_max(weights):
    weights = check_weights(weights)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    return total / max(weights)


def e_sqrt(weights):
    return math.sqrt(effective_sample_size(weights))


def e_zero_on_zero(weights):
    try:
        return effective_sample_size(weights)
    except ValueError:
        if isinstance(weights, list) and all(type(w) in (int, float) and w == 0 for w in weights) and weights:
            return 0.0
        raise


def e_count_nonzero(weights):
    weights = check_weights(weights)
    if math.fsum(weights) == 0:
        raise ValueError
    return float(sum(1 for w in weights if w > 0))


def pu_forgets_prior(cells, weights, world, z, p_correct):
    particle_update(cells, weights, world, z, p_correct)
    like = likelihood_core(world, z, p_correct)
    return update_core([1.0] * len(cells), [like[c] for c in cells])


def pu_unnormalized(cells, weights, world, z, p_correct):
    particle_update(cells, weights, world, z, p_correct)
    like = likelihood_core(world, z, p_correct)
    return [w * like[c] for c, w in zip(cells, weights)]


def pu_shifted_cell(cells, weights, world, z, p_correct):
    particle_update(cells, weights, world, z, p_correct)
    like = likelihood_core(world, z, p_correct)
    return update_core(weights, [like[c - 1] for c in cells])


def pu_adds(cells, weights, world, z, p_correct):
    particle_update(cells, weights, world, z, p_correct)
    like = likelihood_core(world, z, p_correct)
    s = [w + like[c] for c, w in zip(cells, weights)]
    t = math.fsum(s)
    return [v / t for v in s]


def pu_uniform_on_zero(cells, weights, world, z, p_correct):
    try:
        return particle_update(cells, weights, world, z, p_correct)
    except ValueError:
        if (isinstance(cells, list) and isinstance(weights, list) and len(cells) == len(weights)
                and cells and all(type(c) is int and 0 <= c < len(world) for c in cells)
                and z in (0, 1) and p_correct == 1.0):
            return [1 / len(cells)] * len(cells)
        raise


def r_u0_not_scaled(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    n = len(weights)
    cum, running = [], 0.0
    for w in weights:
        running += w / total
        cum.append(running)
    return [min(next((i for i, c in enumerate(cum) if c > u0 + k / n), n - 1), n - 1)
            for k in range(n)]


def r_ignores_u0(weights, u0):
    return resample_core(check_weights(weights), 0.5) if check_number(u0, 0, 1, True) is None \
        and math.fsum(weights) > 0 else systematic_resample(weights, u0)


def r_same_position(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    n = len(weights)
    cum, running = [], 0.0
    for w in weights:
        running += w / total
        cum.append(running)
    index = next((i for i, c in enumerate(cum) if c > u0), n - 1)
    return [index] * n


def r_tie_to_left(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    n = len(weights)
    cum, running = [], 0.0
    for w in weights:
        running += w / total
        cum.append(running)
    return [min(next((i for i, c in enumerate(cum) if c >= (u0 + k) / n), n - 1), n - 1)
            for k in range(n)]


def r_no_clamp(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    n = len(weights)
    cum, running = [], 0.0
    for w in weights:
        running += w / total
        cum.append(running)
    return [[i for i, c in enumerate(cum) if c > (u0 + k) / n][0] for k in range(n)]


def r_clamp_to_last_index(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    total = math.fsum(weights)
    if total == 0:
        raise ValueError
    n = len(weights)
    cum, running = [], 0.0
    for w in weights:
        running += w / total
        cum.append(running)
    return [next((i for i, c in enumerate(cum) if c > (u0 + k) / n), n - 1) for k in range(n)]


def r_unnormalized_cum(weights, u0):
    weights = check_weights(weights)
    check_number(u0, 0, 1, open_high=True)
    if math.fsum(weights) == 0:
        raise ValueError
    n = len(weights)
    cum, running = [], 0.0
    for w in weights:
        running += w
        cum.append(running)
    return [min(next((i for i, c in enumerate(cum) if c > (u0 + k) / n), n - 1), n - 1)
            for k in range(n)]


def r_counts(weights, u0):
    out = systematic_resample(weights, u0)
    return [out.count(i) for i in range(len(weights))]


def r_off_by_one(weights, u0):
    out = systematic_resample(weights, u0)
    return [min(i + 1, len(weights) - 1) for i in out]


def r_unsorted(weights, u0):
    return systematic_resample(weights, u0)[::-1]


def r_stratified_midpoint(weights, u0):
    return systematic_resample(weights, 0.5)


def p_kernel_unchecked_sum():
    return lenient(predict, lambda b, k, o, c: isinstance(k, list) and len(k) == 2
                   and all(type(v) is float for v in k) and abs(math.fsum(k) - 1) > 0.3
                   and isinstance(b, list) and abs(math.fsum(b) - 1) <= 1e-9
                   and type(o) is int and type(c) is bool, [0.0, 0.0, 1.0])


def p_rev_kernel(belief, kernel, offset0, cyclic):
    belief, kernel = check_belief(belief), check_kernel(kernel)
    check_int(offset0, -8, 8)
    check_cyclic(cyclic)
    return predict_core(belief, kernel[::-1], offset0, cyclic)


def make_wrap_once(low_side):
    def run(belief, kernel, offset0, cyclic):
        belief, kernel = check_belief(belief), check_kernel(kernel)
        check_int(offset0, -8, 8)
        check_cyclic(cyclic)
        n = len(belief)
        out = [0.0] * n
        for i in range(n):
            for k in range(len(kernel)):
                j = i + offset0 + k
                if cyclic:
                    if j >= n and not low_side:
                        j -= n
                    elif j < 0 and low_side:
                        j += n
                if not 0 <= j < n:
                    if cyclic:
                        raise IndexError('wrapped index still out of range')
                    j = min(max(j, 0), n - 1)
                out[j] += belief[i] * kernel[k]
        return out
    return run


def loc_rev_kernel(belief, world, p_correct, kernel, offset0, cyclic, observations):
    check_kernel(kernel)
    return localize(belief, world, p_correct, list(kernel)[::-1], offset0, cyclic, observations)


def loc_aliases_empty(belief, world, p_correct, kernel, offset0, cyclic, observations):
    out = localize(belief, world, p_correct, kernel, offset0, cyclic, observations)
    return belief if observations == [] else out


def partial_predict(belief, kernel, offset0, cyclic):
    if cyclic is False:
        raise NotImplementedError('walls not done')
    return predict(belief, kernel, offset0, cyclic)


mutants = [
    ('predict uses the reversed kernel (correlation, not convolution)', {'predict': p_rev_kernel},
     'predict'),
    ('predict wraps a ring index only once on the high side', {'predict': make_wrap_once(False)},
     'predict'),
    ('predict wraps a ring index only once on the low side', {'predict': make_wrap_once(True)},
     'predict'),
    ('localize uses the reversed kernel', {'localize': loc_rev_kernel}, 'localize'),
    ('localize returns the input belief object for no readings', {'localize': loc_aliases_empty},
     'same list object'),
    ('normalize returns a tuple', {'normalize': lambda w: tuple(normalize(w))}, 'normalize'),
    ('update returns a tuple', {'update': lambda b, m: tuple(update(b, m))}, 'update'),
    ('modes returns a tuple', {'modes': lambda b: tuple(modes(b))}, 'modes'),
    ('normalize divides by the maximum', {'normalize': n_max}, 'normalize'),
    ('normalize returns a uniform belief for all-zero weights', {'normalize': n_uniform_on_zero},
     'normalize with all-zero weights'),
    ('normalize adds smoothing epsilon', {'normalize': n_smoothed}, 'normalize'),
    ('normalize accepts negative weights', {'normalize': lenient(
        normalize, lambda w: isinstance(w, list) and any(type(v) is float and v < 0 for v in w),
        [0.0])}, 'invalid normalize(weights='),
    ('normalize accepts NaN weight', {'normalize': lenient(
        normalize, lambda w: isinstance(w, list) and any(type(v) is float and v != v for v in w),
        [0.0])}, 'invalid normalize(weights='),
    ('predict drops mass past the walls', {'predict': p_lossy_walls}, 'predict'),
    ('predict blocks the move at the wall (mass stays in place)', {'predict': p_blocked_walls},
     'predict'),
    ('predict always wraps (cyclic flag ignored)',
     {'predict': lambda b, k, o, c: predict(b, k, o, False if c is False else c)
      and predict_core(check_belief(b), check_kernel(k), o, True)}, 'predict'),
    ('predict always uses walls (cyclic flag ignored)', {'predict': p_always_walls}, 'predict'),
    ('predict applies the kernel in the opposite direction', {'predict': p_reversed_direction},
     'predict'),
    ('predict negates offset0', {'predict': p_negated_offset}, 'predict'),
    ('predict ignores offset0 (centred kernel)', {'predict': p_ignores_offset}, 'predict'),
    ('predict mutates the input belief', {'predict': p_mutates}, 'mutated'),
    ('predict inflates the total mass', {'predict': p_normalizes_zero_mass}, 'predict'),
    ('predict accepts a kernel that does not sum to 1', {'predict': p_kernel_unchecked_sum()},
     'invalid predict(kernel='),
    ('predict raises NotImplementedError only for walls', {'predict': partial_predict},
     'predict: raised NotImplementedError in'),
    ('predict accepts cyclic as the int 1', {'predict': lenient(
        predict, lambda b, k, o, c: c == 1 and type(c) is int and not isinstance(c, bool),
        [0.0, 0.0, 1.0])}, 'invalid predict(cyclic='),
    ('predict accepts float offset0', {'predict': lambda b, k, o, c: predict(
        b, k, int(o) if type(o) is float and o == o and abs(o) < 9 else o, c)},
     'invalid predict(offset0='),
    ('likelihood swaps p_correct and 1 - p_correct', {'sensor_likelihood': l_swapped},
     'sensor_likelihood'),
    ('likelihood normalised to sum 1', {'sensor_likelihood': l_normalized}, 'sensor_likelihood'),
    ('likelihood ignores z', {'sensor_likelihood': l_ignores_z}, 'sensor_likelihood'),
    ('likelihood accepts p_correct > 1', {'sensor_likelihood': lenient(
        sensor_likelihood, lambda w, z, p: type(p) is float and p > 1 and p == p
        and isinstance(w, list) and type(z) is int, [0.0])}, 'invalid sensor_likelihood(p_correct='),
    ('likelihood accepts bool z', {'sensor_likelihood': lenient(
        sensor_likelihood, lambda w, z, p: type(z) is bool, [0.0])},
     'invalid sensor_likelihood(z='),
    ('update does not normalise', {'update': u_unnormalized}, 'update'),
    ('update adds instead of multiplying', {'update': u_adds}, 'update'),
    ('update returns a uniform belief on an impossible observation',
     {'update': u_uniform_on_zero}, 'update with'),
    ('update falls back to the prior on an impossible observation',
     {'update': u_prior_on_zero}, 'update with'),
    ('update ignores the prior', {'update': u_ignores_prior}, 'update'),
    ('update normalises by the maximum product', {'update': u_max_normalized}, 'update'),
    ('update mutates the input belief', {'update': u_mutates}, 'mutated'),
    ('update accepts a belief that does not sum to 1', {'update': lenient(
        update, lambda b, m: isinstance(b, list) and isinstance(m, list) and len(b) == len(m)
        and all(type(v) is float for v in b) and abs(math.fsum(b) - 1) > 0.05
        and all(0 <= v <= 1 for v in b) and all(type(v) is float and 0 <= v <= 1e6 for v in m),
        [0.0] * 3)}, 'invalid update(belief='),
    ('localize predicts before it senses', {'localize': loc_predict_first}, 'localize'),
    ('localize skips the move after the final reading', {'localize': loc_no_final_move},
     'localize'),
    ('localize ignores the cyclic flag', {'localize': loc_always_walls}, 'localize'),
    ('localize returns the prior when a reading is impossible', {'localize': loc_swallows_zero},
     'localize with'),
    ('localize flips every reading', {'localize': loc_flips_z}, 'localize'),
    ('localize returns uniform for no readings', {'localize': loc_empty_uniform}, 'localize 1'),
    ('localize accepts observation value 2', {'localize': lenient(
        localize, lambda b, w, p, k, o, c, obs: isinstance(obs, list) and obs == [2], [0.0] * 4)},
     'invalid localize(observations='),
    ('modes returns only the first maximum', {'modes': m_first_only}, 'modes'),
    ('modes uses exact equality for ties', {'modes': m_exact_ties}, 'modes'),
    ('modes uses a loose 1e-6 tie band', {'modes': m_loose_ties}, 'modes'),
    ('modes returns indices in descending order', {'modes': m_descending}, 'modes'),
    ('modes returns the maximum value, not its cell', {'modes': m_returns_value}, 'modes'),
    ('ESS forgets to normalise (1 / sum w^2)', {'effective_sample_size': e_unnormalized},
     'effective_sample_size'),
    ('ESS = total / max weight', {'effective_sample_size': e_inverse_max},
     'effective_sample_size'),
    ('ESS is the square root of the true value', {'effective_sample_size': e_sqrt},
     'effective_sample_size'),
    ('ESS returns 0 for all-zero weights', {'effective_sample_size': e_zero_on_zero},
     'effective_sample_size with all-zero'),
    ('ESS counts non-zero particles', {'effective_sample_size': e_count_nonzero},
     'effective_sample_size'),
    ('particle_update forgets the prior weights', {'particle_update': pu_forgets_prior},
     'particle_update'),
    ('particle_update does not normalise', {'particle_update': pu_unnormalized},
     'particle_update'),
    ('particle_update reads the likelihood of the neighbouring cell',
     {'particle_update': pu_shifted_cell}, 'particle_update'),
    ('particle_update adds likelihood to the weight', {'particle_update': pu_adds},
     'particle_update'),
    ('particle_update returns uniform when every particle is contradicted',
     {'particle_update': pu_uniform_on_zero}, 'particle_update with'),
    ('particle_update accepts a cell index past the world', {'particle_update': lenient(
        particle_update, lambda c, w, wd, z, p: isinstance(c, list) and any(
            type(v) is int and v >= len(wd) for v in c) if isinstance(wd, list) else False,
        [1.0])}, 'invalid particle_update(cells='),
    ('particle_update accepts a negative cell index (Python wraps it)', {'particle_update': lenient(
        particle_update, lambda c, w, wd, z, p: isinstance(c, list) and any(
            type(v) is int and v < 0 for v in c), [1.0])}, 'invalid particle_update(cells='),
    ('resample treats u0 as a position, not u0/N', {'systematic_resample': r_u0_not_scaled},
     'systematic_resample'),
    ('resample ignores u0', {'systematic_resample': r_ignores_u0}, 'systematic_resample'),
    ('resample uses one position (multinomial with one draw)',
     {'systematic_resample': r_same_position}, 'systematic_resample'),
    ('resample sends boundary positions to the left particle',
     {'systematic_resample': r_tie_to_left}, 'systematic_resample'),
    ('resample has no clamp (IndexError-style failure at the top)',
     {'systematic_resample': r_no_clamp}, 'systematic_resample'),
    ('resample clamps to N-1 even if that particle has zero weight',
     {'systematic_resample': r_clamp_to_last_index}, 'systematic_resample'),
    ('resample compares positions with unnormalised cumulative weights',
     {'systematic_resample': r_unnormalized_cum}, 'systematic_resample'),
    ('resample returns copy counts instead of indices', {'systematic_resample': r_counts},
     'systematic_resample'),
    ('resample indices off by one', {'systematic_resample': r_off_by_one},
     'systematic_resample'),
    ('resample returns indices in reverse order', {'systematic_resample': r_unsorted},
     'systematic_resample'),
    ('resample always uses u0 = 0.5', {'systematic_resample': r_stratified_midpoint},
     'systematic_resample'),
    ('resample accepts u0 = 1.0', {'systematic_resample': lenient(
        systematic_resample, lambda w, u: type(u) is float and u == 1.0, [0])},
     'invalid systematic_resample(u0='),
    ('resample accepts all-zero weights', {'systematic_resample': lenient(
        systematic_resample, lambda w, u: isinstance(w, list) and w and all(
            type(v) in (int, float) and v == 0 for v in w), [0])},
     'systematic_resample with all-zero'),
]
labels = set()
for label, over, expect in mutants:
    require(label not in labels, 'duplicate mutant label: ' + label)
    labels.add(label)
    result = run_with(over)
    require(result, 'false accept: ' + label)
    require(any(expect in line for line in result),
            'mutant rejected for the wrong reason: ' + label + ' -> ' + str(result[:3]))
print('Localization kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
