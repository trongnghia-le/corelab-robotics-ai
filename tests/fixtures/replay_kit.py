"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative solutions (different formulations of replay_node,
different search orders for minimal_reproducer, different test-suite styles for
node_tests) that must pass, and named injected bugs (buggy nodes, buggy
shrinkers, weak or wrong test suites) that must be rejected for the intended
reason. Plain checks only, so the fixture also works under python -O.
"""
import ast
import importlib.util
import itertools
import json
import math
from decimal import Decimal
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('replay_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L05-replay.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree)
            if isinstance(node, ast.Import) for alias in node.names}
imported |= {node.module.split('.')[0] for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom) and node.module}
require(imported <= {'math', 'decimal'}, 'kit imports beyond math/decimal: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
require('rclpy' not in text.replace('Do not import rclpy', ''), 'kit must not use rclpy')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name) < spoiler
            for name in ('exact_arc', 'replay_node', 'minimal_reproducer', 'node_tests')),
        'starter functions must sit above the spoiler banner')
require(all(text.index(name) > spoiler for name in ('def _run', 'class _NodeB', '_MUTANTS = [')),
        'reference and mutants must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('replay_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter and sum(1 for line in starter if 'not implemented yet' in line) == 3
        and len(starter) == 3, 'starter must report exactly three NotImplementedError lines')


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def encode_messages(messages):
    out = []
    for m in messages:
        if m['kind'] == 'odom':
            out.append(['odom', str(m['stamp']), m['frame_id'], m['child_frame_id'],
                        dec(m['vl']), dec(m['vr'])])
        else:
            out.append(['reset', str(m['stamp']), dec(m['x']), dec(m['y']), dec(m['theta'])])
    return out


def encode_config(config):
    return {'frame_id': config['frame_id'], 'child_frame_id': config['child_frame_id'],
            'track': dec(config['track']), 'max_gap_ns': str(config['max_gap_ns']),
            'gap_policy': config['gap_policy'],
            'initial_pose': [dec(v) for v in config['initial_pose']]}


expected_samples = (
    [{'structure': 'replay.node@1', 'inputs': {**encode_config(c), 'messages': encode_messages(m)}}
     for _, c, m, _, _ in kit._ANCHORS]
    + [{'structure': 'replay.node@1', 'inputs': {**encode_config(c), 'messages': encode_messages(m)}}
       for _, c, m in kit._ORACLE]
    + [{'structure': 'replay.reproducer@1',
        'inputs': {'fault': flaw or 'none', **encode_config(c), 'messages': encode_messages(m)}}
       for _, flaw, c, m in kit._REPRO])
samples = json.loads((root / 'content/labs/L05-replay.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L05-replay'], 'samples must hold only L05-replay')
require(samples['kits']['L05-replay'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')


# ---- helpers ----
def deep(value):
    return kit._deep(value)


_REF_CACHE = {}


def ref_decimal(config, messages):
    key = repr((config, messages))
    if key not in _REF_CACHE:
        _REF_CACHE[key] = kit._run(config, messages, arc=kit._decimal_arc)
    return _REF_CACHE[key]


def close(got, want, tol=1e-9):
    try:
        return kit._same(got, want) is None if tol == 1e-9 else exact_equal(got, want)
    except Exception:
        return False


def exact_equal(got, want):
    if len(got[0]) != len(want[0]):
        return False
    for a, b in zip(got[0], want[0]):
        if dict(a) != dict(b):
            return False
    return [tuple(d) for d in got[1]] == [tuple(d) for d in want[1]]


# ---- author replay_node (own formulation, rotation-matrix arc) ----
def author_replay(config, messages):
    kit._validate(config, messages)
    frame, child = config['frame_id'], config['child_frame_id']
    gap_limit, policy, track = config['max_gap_ns'], config['gap_policy'], config['track']
    start = (float(config['initial_pose'][0]), float(config['initial_pose'][1]),
             math.atan2(math.sin(config['initial_pose'][2]), math.cos(config['initial_pose'][2])))
    state = {'pose': None, 'clock': None}
    poses, drops = [], []

    def publish(stamp, flag):
        x, y, theta = state['pose']
        poses.append({'stamp': stamp, 'frame_id': frame, 'child_frame_id': child,
                      'x': x, 'y': y, 'theta': theta, 'flag': flag})

    def advance(vl, vr, dt):
        x, y, theta = state['pose']
        dl, dr = vl * dt, vr * dt
        turn = (dr - dl) / track
        mid = (dl + dr) / 2
        if abs(turn) < 1e-7:
            forward, side = mid * (1 - turn * turn / 24), mid * turn / 2
        else:
            forward, side = mid * math.sin(turn) / turn, mid * (1 - math.cos(turn)) / turn
        c, s = math.cos(theta), math.sin(theta)
        theta = theta + turn
        state['pose'] = (x + c * forward - s * side, y + s * forward + c * side,
                         math.atan2(math.sin(theta), math.cos(theta)))

    for i, m in enumerate(messages):
        if m['kind'] == 'reset':
            theta = m['theta']
            state['pose'] = (float(m['x']), float(m['y']), math.atan2(math.sin(theta), math.cos(theta)))
            state['clock'] = m['stamp']
            publish(m['stamp'], 'reset')
            continue
        clock = state['clock']
        if m['frame_id'] != frame:
            drops.append((i, 'frame'))
        elif m['child_frame_id'] != child:
            drops.append((i, 'child_frame'))
        elif clock is not None and m['stamp'] == clock:
            drops.append((i, 'duplicate'))
        elif clock is not None and m['stamp'] < clock:
            drops.append((i, 'out_of_order'))
        else:
            flag = 'init'
            if clock is None:
                state['pose'] = start
            else:
                span = m['stamp'] - clock
                flag = 'gap' if span > gap_limit else 'ok'
                if flag == 'gap' and policy == 'reset':
                    state['pose'] = start
                else:
                    advance(m['vl'], m['vr'], span / 1e9)
            state['clock'] = m['stamp']
            publish(m['stamp'], flag)
    return (poses, drops)


# ---- alternative 2: two passes (classify, then integrate) with Decimal arc, own validation ----
def declarative_validate(config, messages):
    def ok_num(v, bound):
        return type(v) in (int, float) and v == v and abs(v) <= bound
    rules = {'frame_id': lambda v: type(v) is str and 1 <= len(v) <= 32,
             'child_frame_id': lambda v: type(v) is str and 1 <= len(v) <= 32,
             'track': lambda v: ok_num(v, 2) and v >= 0.1,
             'max_gap_ns': lambda v: type(v) is int and 1 <= v <= 10 ** 12,
             'gap_policy': lambda v: v in ('reset', 'flag') and type(v) is str,
             'initial_pose': lambda v: isinstance(v, (list, tuple)) and len(v) == 3
             and ok_num(v[0], 1000) and ok_num(v[1], 1000) and ok_num(v[2], 2 * math.pi)}
    if not isinstance(config, dict) or set(config) != set(rules):
        raise ValueError
    if not all(rule(config[key]) for key, rule in rules.items()):
        raise ValueError
    if not isinstance(messages, (list, tuple)) or len(messages) > 200:
        raise ValueError
    layouts = {'odom': {'stamp': lambda v: True, 'frame_id': lambda v: type(v) is str and len(v) <= 32,
                        'child_frame_id': lambda v: type(v) is str and len(v) <= 32,
                        'vl': lambda v: ok_num(v, 2), 'vr': lambda v: ok_num(v, 2)},
               'reset': {'stamp': lambda v: True, 'x': lambda v: ok_num(v, 1000),
                         'y': lambda v: ok_num(v, 1000), 'theta': lambda v: ok_num(v, 2 * math.pi)}}
    for m in messages:
        if not isinstance(m, dict) or m.get('kind') not in layouts:
            raise ValueError
        layout = layouts[m['kind']]
        if set(m) != set(layout) | {'kind'}:
            raise ValueError
        stamp = m['stamp']
        if type(stamp) is not int or stamp < 0 or stamp > 10 ** 13:
            raise ValueError
        if not all(rule(m[key]) for key, rule in layout.items()):
            raise ValueError


def two_pass_replay(config, messages):
    declarative_validate(config, messages)
    labels, clock = [], None
    for m in messages:
        if m['kind'] == 'reset':
            labels.append('reset')
            clock = m['stamp']
        elif m['frame_id'] != config['frame_id']:
            labels.append('frame')
        elif m['child_frame_id'] != config['child_frame_id']:
            labels.append('child_frame')
        elif clock is not None and m['stamp'] <= clock:
            labels.append('duplicate' if m['stamp'] == clock else 'out_of_order')
        else:
            labels.append('use')
            clock = m['stamp']
    drops = tuple((i, lab) for i, lab in enumerate(labels) if lab not in ('use', 'reset'))
    wrap = lambda a: math.atan2(math.sin(a), math.cos(a))
    pose, clock, out = None, None, []
    for m, lab in zip(messages, labels):
        if lab == 'reset':
            pose, clock = (float(m['x']), float(m['y']), wrap(m['theta'])), m['stamp']
            flag = 'reset'
        elif lab == 'use':
            if clock is None:
                p = config['initial_pose']
                pose, flag = (float(p[0]), float(p[1]), wrap(p[2])), 'init'
            else:
                span = m['stamp'] - clock
                late = span > config['max_gap_ns']
                flag = 'gap' if late else 'ok'
                if late and config['gap_policy'] == 'reset':
                    p = config['initial_pose']
                    pose = (float(p[0]), float(p[1]), wrap(p[2]))
                else:
                    pose = kit._decimal_arc(pose, m['vl'] * span / 1e9, m['vr'] * span / 1e9,
                                            config['track'])
            clock = m['stamp']
        else:
            continue
        out.append({'stamp': m['stamp'], 'frame_id': config['frame_id'],
                    'child_frame_id': config['child_frame_id'], 'x': pose[0], 'y': pose[1],
                    'theta': pose[2], 'flag': flag})
    return (tuple(out), drops)


# ---- alternative 3: object with an incrementally consumed generator ----
class Integrator(object):
    def __init__(self, config):
        self.config = config
        self.z = None
        self.heading = 0.0
        self.stamp = None

    def place(self, x, y, theta, stamp):
        self.z, self.heading, self.stamp = complex(x, y), math.remainder(theta, 2 * math.pi), stamp

    def move(self, vl, vr, dt):
        omega = (vr - vl) / self.config['track']
        speed = (vl + vr) / 2
        total = omega * dt
        direction = complex(math.cos(self.heading), math.sin(self.heading))
        if abs(total) < 1e-8:
            self.z += direction * speed * dt * complex(1, total / 2)
        else:
            self.z += direction * speed / omega * (complex(math.cos(total), math.sin(total)) - 1) / 1j
        self.heading = math.remainder(self.heading + total, 2 * math.pi)


def streaming_replay(config, messages):
    kit._validate(config, messages)

    def stream():
        node = Integrator(config)
        p = config['initial_pose']
        for i, m in enumerate(messages):
            if m['kind'] == 'reset':
                node.place(m['x'], m['y'], m['theta'], m['stamp'])
                yield ('pose', m['stamp'], node, 'reset')
                continue
            expected = (config['frame_id'], config['child_frame_id'])
            if (m['frame_id'], m['child_frame_id']) != expected:
                yield ('drop', i, 'frame' if m['frame_id'] != expected[0] else 'child_frame')
            elif node.stamp is not None and m['stamp'] <= node.stamp:
                yield ('drop', i, 'duplicate' if m['stamp'] == node.stamp else 'out_of_order')
            elif node.stamp is None:
                node.place(p[0], p[1], p[2], m['stamp'])
                yield ('pose', m['stamp'], node, 'init')
            else:
                span = m['stamp'] - node.stamp
                if span <= config['max_gap_ns']:
                    node.move(m['vl'], m['vr'], span / 1e9)
                    flag = 'ok'
                else:
                    flag = 'gap'
                    if config['gap_policy'] == 'flag':
                        node.move(m['vl'], m['vr'], span / 1e9)
                    else:
                        node.place(p[0], p[1], p[2], m['stamp'])
                node.stamp = m['stamp']
                yield ('pose', m['stamp'], node, flag)
    poses, drops = [], []
    for kind, a, b, *rest in stream():
        if kind == 'drop':
            drops.append([a, b])
        else:
            poses.append({'stamp': a, 'frame_id': config['frame_id'],
                          'child_frame_id': config['child_frame_id'], 'x': b.z.real,
                          'y': b.z.imag, 'theta': b.heading, 'flag': rest[0]})
    return (tuple(poses), tuple(drops))


# ---- minimal_reproducer implementations ----
def fault_differs(node, config, messages, reference):
    try:
        got = node(deep(config), [dict(m) for m in messages])
    except Exception:
        return True
    try:
        want = reference(config, messages)
    except Exception:
        return True
    return kit._same(got, want) is not None


def repro_combinations(node, config, messages):
    if not callable(node) or len(messages) > 12:
        raise ValueError
    if not fault_differs(node, config, messages, author_replay):
        return None
    for size in range(len(messages) + 1):
        for combo in itertools.combinations(range(len(messages)), size):
            if fault_differs(node, config, [messages[i] for i in combo], author_replay):
                return list(combo)


def repro_bitmask(node, config, messages):
    if not callable(node) or len(messages) > 12:
        raise ValueError
    n = len(messages)
    if not fault_differs(node, config, messages, two_pass_replay):
        return None
    ranked = sorted(range(1 << n), key=lambda mask: bin(mask).count('1'))
    for mask in ranked:
        keep = [i for i in range(n) if mask >> i & 1]
        if fault_differs(node, config, [messages[i] for i in keep], two_pass_replay):
            return tuple(keep)


def repro_grow(node, config, messages):
    """Breadth-first growth of index tuples (a third search order)."""
    if not callable(node) or len(messages) > 12:
        raise ValueError
    if not fault_differs(node, config, messages, streaming_replay):
        return None
    level = [()]
    while True:
        for combo in level:
            if fault_differs(node, config, [messages[i] for i in combo], streaming_replay):
                return list(combo)
        level = [c + (j,) for c in level for j in range(c[-1] + 1 if c else 0, len(messages))]


# ---- node_tests suites ----
INVALID = kit._invalid_cases()
SWEEP = [kit._sweep_log(seed) for seed in range(kit._SWEEPS)]
SCENARIOS = ([(t, c, m) for t, c, m, _, _ in kit._ANCHORS] + list(kit._ORACLE)
             + [('sweep', c, m) for c, m in SWEEP])


def make_suite(reference, scenarios=SCENARIOS, invalid=True, repeat=True, mutation=True,
               exact=False, catch=True, skip=(), result='bool'):
    def suite(node):
        try:
            for tag, config, messages in scenarios:
                if tag in skip:
                    continue
                c, m = deep(config), deep(messages)
                first = node(c, m)
                if mutation and (c != config or m != messages):
                    return False
                if repeat:
                    second = node(deep(config), deep(messages))
                    if not (exact_equal(first, second) if exact else close(first, second)):
                        return False
                want = reference(config, messages)
                if not (exact_equal(first, want) if exact else close(first, want)):
                    return False
            if invalid:
                for _, config, messages in INVALID:
                    try:
                        node(deep(config), deep(messages))
                    except ValueError:
                        continue
                    except Exception:
                        return False
                    return False
        except Exception:
            if catch:
                return False
            raise
        return True if result == 'bool' else (1 if result == 'int' else None)
    return suite


def suite_random(node):
    """Second style: own generated logs and a few literal expectations."""
    ref = two_pass_replay
    try:
        cfg = kit._cfg(gap_policy='flag', initial_pose=[0.5, -0.5, 3.0])
        for seed in range(100, 220):
            draw = kit._lcg(seed)
            log = []
            ms = 100 * draw(10)
            for _ in range(1 + draw(9)):
                kind = draw(14)
                if kind == 0:
                    log.append(kit._r(ms, draw(3) * .5, 0., draw(9) - 4.))
                else:
                    log.append(kit._o(ms, (draw(9) - 4) * .1, (draw(9) - 4) * .1,
                                      {1: 'map', 3: 'Odom', 6: 'odom2'}.get(kind, 'odom'),
                                      {2: 'x', 4: 'base_link2', 5: 'Base_link'}.get(kind, 'base_link')))
                ms = max(0, ms + (-250, 0, 300, 500, 1000, 1001, 1700)[draw(7)])
            for config in (kit._cfg(track=.2 + .1 * draw(5), gap_policy=('reset', 'flag')[seed % 2]),
                           cfg):
                c, m = deep(config), deep(log)
                got = node(c, m)
                if c != config or m != log or not close(got, ref(config, log)):
                    return False
                if not close(node(deep(config), deep(log)), got):
                    return False
        for config, messages in ((kit._cfg(), [kit._o(0, 0., 0.), kit._o(0, 1., 1.)]),
                                 (kit._cfg(max_gap_ns=0), [])):
            try:
                node(config, messages)
                if config['max_gap_ns'] == 0:
                    return False
            except ValueError:
                if config['max_gap_ns'] != 0:
                    return False
        for _, config, messages in INVALID:
            try:
                node(deep(config), deep(messages))
            except ValueError:
                continue
            except Exception:
                return False
            return False
        return True
    except Exception:
        return False


# ---- running the kit against implementations ----
def run_with(replay=None, repro=None, tests=None):
    saved = (kit.replay_node, kit.minimal_reproducer, kit.node_tests)
    kit.replay_node = replay or author_replay
    kit.minimal_reproducer = repro or repro_combinations
    kit.node_tests = tests or make_suite(ref_decimal)
    try:
        return kit.self_check()
    finally:
        kit.replay_node, kit.minimal_reproducer, kit.node_tests = saved


def cross_check():
    """Alternatives must agree with the kit reference on many random logs."""
    impls = (author_replay, two_pass_replay, streaming_replay)
    logs = SWEEP + [kit._sweep_log(s) for s in range(1000, 1400)]
    logs += [(c, m) for _, c, m in kit._ORACLE] + [(c, m) for _, c, m, _, _ in kit._ANCHORS]
    for index, (config, messages) in enumerate(logs):
        want = ref_decimal(config, messages)
        for impl in impls:
            require(kit._same(impl(deep(config), deep(messages)), want) is None,
                    impl.__name__ + ' disagrees with the reference on log ' + str(index))
    for label, config, messages in INVALID:
        for impl in impls:
            try:
                impl(deep(config), deep(messages))
            except ValueError:
                continue
            except Exception as error:
                require(False, impl.__name__ + ' raised ' + type(error).__name__
                        + ' on invalid ' + label)
            require(False, impl.__name__ + ' accepted invalid ' + label)


cross_check()

alternatives = [
    ('author: rotation-matrix replay, combinations search, scenario suite', {}),
    ('two-pass classify/integrate replay with Decimal arc and declarative validation, '
     'tuple outputs, bitmask search',
     {'replay': two_pass_replay, 'repro': repro_bitmask}),
    ('streaming generator replay with a complex-number integrator, breadth-first search',
     {'replay': streaming_replay, 'repro': repro_grow}),
    ('generated-log differential suite against a two-pass reference',
     {'tests': suite_random}),
    ('scenario suite built on the streaming implementation as its own reference',
     {'replay': streaming_replay, 'tests': make_suite(streaming_replay)}),
    ('scenario suite with only the anchors plus sweeps in a different order',
     {'tests': make_suite(ref_decimal, scenarios=list(reversed(SCENARIOS)))}),
]
for label, parts in alternatives:
    result = run_with(**parts)
    require(result == [], 'false reject (' + label + '): ' + str(result))


# ---- injected bugs: replay_node ----
def flawed(flaw):
    memory = {'pose': None, 'last': None}
    return lambda config, messages: kit._run(config, messages, flaw, memory=memory)


FLAW_TAGS = {
    'frame-ignored': 'frame', 'child-ignored': 'frame', 'dup-accepted': 'stamp',
    'ooo-accepted': 'stamp', 'ooo-rewinds-clock': 'stamp', 'frame-drop-rewinds-clock': 'frame',
    'stamp-before-frame': 'frame', 'dup-reason-wrong': 'stamp', 'gap-inclusive': 'gap',
    'gap-never': 'gap', 'gap-reset-keeps-pose': 'gap', 'gap-reset-integrates': 'gap',
    'gap-flag-missing': 'gap', 'gap-flag-skips': 'gap', 'reset-ignored': 'reset',
    'reset-clock-kept': 'reset', 'reset-no-output': 'reset', 'first-integrates': 'start',
    'euler': 'pose', 'theta-unwrapped': 'pose', 'dt-units': 'pose', 'swapped-wheels': 'pose',
    'only-final': 'pose', 'stamp-previous': 'pose', 'frames-swapped': 'start',
    'mutates-input': 'start', 'state-leak': 'repeat', 'no-validation': 'invalid',
    'bool-stamp': 'invalid', 'loose-track': 'invalid', 'crash-empty': 'start',
    'frame-casefold': 'frame', 'frame-prefix': 'frame', 'child-prefix': 'frame', 'child-casefold': 'frame',
}
require(set(FLAW_TAGS) == {f for _, _, f in kit._MUTANTS}, 'every mutant flaw needs an expected tag')
rejected = 0


def expect_rejected(label, result, tag):
    global rejected
    require(result, 'false accept (' + label + ')')
    require(any(line.startswith('[' + tag + ']') or line.startswith(tag) for line in result),
            'wrong reason for ' + label + ' (wanted ' + tag + '): ' + str(result[:3]))
    rejected += 1


for flaw, tag in FLAW_TAGS.items():
    expect_rejected('replay_node ' + flaw, run_with(replay=flawed(flaw)), tag)


def wrap_core(post):
    return lambda config, messages: post(author_replay(config, messages))


def sort_first(config, messages):
    messages.sort(key=lambda m: m['stamp'])
    return author_replay(config, messages)


def config_mutating(config, messages):
    config['initial_pose'] = tuple(config['initial_pose'])
    return author_replay(config, messages)


def float_stamp(result):
    return ([dict(p, stamp=p['stamp'] / 1e9) for p in result[0]], result[1])


def drop_flag(result):
    return ([{k: v for k, v in p.items() if k != 'flag'} for p in result[0]], result[1])


def bare_drops(result):
    return (result[0], [i for i, _ in result[1]])


def list_not_pair(result):
    return result[0]


def theta_degrees(result):
    return ([dict(p, theta=math.degrees(p['theta'])) for p in result[0]], result[1])


def nan_pose(result):
    return ([dict(p, x=float('nan')) if p['flag'] == 'gap' else p for p in result[0]], result[1])


def numpy_like(result):
    return ([dict(p, x=Decimal(str(p['x']))) for p in result[0]], result[1])


def one_based(result):
    return (result[0], [(i + 1, r) for i, r in result[1]])


def reset_unwrapped(config, messages):
    base = author_replay(config, messages)
    poses = [dict(p) for p in base[0]]
    resets = [m for m in messages if m['kind'] == 'reset']
    for p in poses:
        if p['flag'] == 'reset':
            match = [m for m in resets if m['stamp'] == p['stamp']][0]
            p['theta'] = float(match['theta'])
    return (poses, base[1])


def stamp_seconds(config, messages):
    base = author_replay(config, messages)
    return ([dict(p, stamp=float(p['stamp'])) for p in base[0]], base[1])


def init_ignores_pose(config, messages):
    base = author_replay(config, messages)
    shift = config['initial_pose']
    poses = []
    for p in base[0]:
        poses.append(dict(p, x=p['x'] - shift[0], y=p['y'] - shift[1]) if p['flag'] == 'init' else p)
    return (poses, base[1])


def gap_off_by_one_ns(config, messages):
    config = dict(config, max_gap_ns=config['max_gap_ns'] + 1)
    return author_replay(config, messages)


extra_nodes = [
    ('sorts the messages by stamp in place', sort_first, 'stamp'),
    ('replaces config initial_pose by a tuple', config_mutating, 'start'),
    ('stamp converted to float seconds', wrap_core(float_stamp), 'start'),
    ('stamp converted to float seconds (reset path)', stamp_seconds, 'start'),
    ('pose without flag key', wrap_core(drop_flag), 'start'),
    ('drops as bare indices', wrap_core(bare_drops), 'start'),
    ('returns only the poses', wrap_core(list_not_pair), 'start'),
    ('heading reported in degrees', wrap_core(theta_degrees), 'pose'),
    ('NaN pose on gap', wrap_core(nan_pose), 'gap'),
    ('Decimal positions', wrap_core(numpy_like), 'pose'),
    ('one-based drop indices', wrap_core(one_based), 'stamp'),
    ('reset heading not wrapped', reset_unwrapped, 'reset'),
    ('initial pose subtracted from init', init_ignores_pose, 'start'),
    ('gap limit shifted by 1 ns', gap_off_by_one_ns, 'gap'),
]
for label, node, tag in extra_nodes:
    expect_rejected('replay_node ' + label, run_with(replay=node), tag)


# ---- injected bugs: minimal_reproducer ----
def repro_full(node, config, messages):
    return list(range(len(messages))) if fault_differs(node, config, messages, author_replay) else None


def repro_prefix(node, config, messages):
    """Shortest exposing PREFIX (not subsequence)."""
    if not fault_differs(node, config, messages, author_replay):
        return None
    for size in range(len(messages) + 1):
        if fault_differs(node, config, messages[:size], author_replay):
            return list(range(size))


def repro_window(node, config, messages):
    """Shortest exposing CONTIGUOUS window; a decoy between two messages inflates it."""
    n = len(messages)
    if not fault_differs(node, config, messages, author_replay):
        return None
    for size in range(n + 1):
        for start in range(n - size + 1):
            if fault_differs(node, config, messages[start:start + size], author_replay):
                return list(range(start, start + size))


def repro_last_only(node, config, messages):
    return [len(messages) - 1] if fault_differs(node, config, messages, author_replay) else None


def repro_reversed(node, config, messages):
    found = repro_combinations(node, config, messages)
    return None if found is None else list(reversed(found))


def repro_never_none(node, config, messages):
    found = repro_combinations(node, config, messages)
    return [0] if found is None else found


def repro_always_none(node, config, messages):
    return None


def repro_messages_not_indices(node, config, messages):
    found = repro_combinations(node, config, messages)
    return None if found is None else [messages[i] for i in found]


def repro_mutating(node, config, messages):
    found = repro_combinations(node, config, messages)
    messages.reverse()
    return found


def repro_no_validation(node, config, messages):
    n = len(messages)
    best = None
    for size in range(n + 1):
        for combo in itertools.combinations(range(n), size):
            if best is None and fault_differs(node, config, [messages[i] for i in combo], author_replay):
                best = list(combo)
    return best if fault_differs(node, config, messages, author_replay) else None


def repro_same_as_reference(node, config, messages):
    """Compares with the node's own output, so it never sees a difference."""
    return None


bad_repros = [
    ('returns the whole list', repro_full, 'reproducer', 'not shortest'),
    ('shortest prefix instead of subsequence', repro_prefix, 'reproducer', 'not shortest'),
    ('contiguous windows only', repro_window, 'reproducer', 'not shortest'),
    ('only the last index', repro_last_only, 'reproducer', 'does not expose'),
    ('indices in descending order', repro_reversed, 'reproducer', 'increasing'),
    ('returns an index for a node that agrees', repro_never_none, 'reproducer', 'expected None'),
    ('always None', repro_always_none, 'reproducer', 'returned None'),
    ('returns messages instead of indices', repro_messages_not_indices, 'reproducer', 'increasing'),
    ('mutates the message list', repro_mutating, 'reproducer', 'mutated'),
    ('no validation of node or size', repro_no_validation, 'invalid', 'returned instead'),
]
for label, repro, tag, reason in bad_repros:
    result = run_with(repro=repro)
    require(result, 'false accept (minimal_reproducer ' + label + ')')
    require(any(line.startswith('[' + tag + ']') and (reason is None or reason in line)
                for line in result),
            'wrong reason for minimal_reproducer ' + label + ': ' + str(result[:3]))
    rejected += 1


# ---- injected bugs: node_tests (weak, wrong or ill-formed suites) ----
def always_true(node):
    return True


def always_false(node):
    return False


def one_sided_nan(node):
    try:
        return node(kit._cfg(), [kit._o(0, .1, .1)]) is not None
    except Exception:
        return False


def make_scenarios(drop_tags):
    return [s for s in SCENARIOS if s[0] not in drop_tags]


bad_suites = [
    ('always accepts', always_true, 'accepted'),
    ('always rejects', always_false, 'valid core'),
    ('smoke test only', one_sided_nan, 'accepted'),
    ('exact float equality', make_suite(ref_decimal, exact=True), 'valid core'),
    ('no invalid-input checks', make_suite(ref_decimal, invalid=False), 'area invalid'),
    ('no mutation check', make_suite(ref_decimal, mutation=False), 'area mutation'),
    ('no gap scenarios', make_suite(ref_decimal, scenarios=make_scenarios(('gap', 'sweep', 'reset', 'start'))),
     'area gap'),
    ('no frame scenarios', make_suite(ref_decimal, scenarios=make_scenarios(('frame', 'sweep', 'output', 'start'))),
     'area frame'),
    ('no stamp scenarios', make_suite(ref_decimal, scenarios=[sc for sc in SCENARIOS if all(a['stamp'] < b['stamp'] for a, b in zip(sc[2], sc[2][1:]))]),
     'area stamp'),
    ('no reset scenarios', make_suite(ref_decimal, scenarios=make_scenarios(('reset', 'sweep'))),
     'area reset'),
    ('no long-turn pose scenarios', make_suite(ref_decimal, scenarios=[s for s in SCENARIOS if s[0] in ('start', 'stamp', 'frame', 'gap', 'reset')]),
     'area pose'),
    ('does not catch node exceptions', make_suite(ref_decimal, catch=False), 'raised'),
    ('returns 1 instead of True', make_suite(ref_decimal, result='int'), 'must return a bool'),
    ('returns None instead of True', make_suite(ref_decimal, result='none'), 'must return a bool'),
]
for label, suite, reason in bad_suites:
    result = run_with(tests=suite)
    require(result, 'false accept (node_tests ' + label + ')')
    require(all(line.startswith('[tests]') for line in result),
            'node_tests ' + label + ' disturbed other checks: ' + str(result[:3]))
    require(any(reason in line for line in result),
            'wrong reason for node_tests ' + label + ' (wanted ' + reason + '): ' + str(result[:3]))
    rejected += 1


# ---- a suite that agrees with a wrong replay_node is still caught by the kit ----
result = run_with(replay=flawed('gap-inclusive'), tests=make_suite(flawed('gap-inclusive')))
require(any(line.startswith('[gap]') for line in result) and any('[tests]' in line for line in result),
        'a self-consistent but wrong suite must fail twice')
rejected += 1

# NotImplementedError collapses to one line per function
kit.replay_node = lambda c, m: (_ for _ in ()).throw(NotImplementedError())
partial = kit.self_check()
require(sum('replay_node: not implemented' in line for line in partial) == 1, 'collapse failed')

print('Replay kit: %d valid alternatives accepted, %d injected bugs rejected; '
      'starter fails as intended' % (len(alternatives), rejected))
