"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different formulations) that must
pass, and named injected bugs that must be rejected. Plain checks only, so the
fixture also works under python -O.
"""
import ast
import importlib.util
import json
import math
import re
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('reasoning_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L22-reasoning.v1.py'
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
names = ('apply_action', 'update_belief', 'posterior', 'plan_failures',
         'success_probability', 'ungrounded')
require(all(text.index('def ' + name) < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _o_run') > spoiler, 'oracle must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('reasoning_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter, 'unimplemented starter must report failure')
require(len(starter) == 6 and all(line.endswith('not implemented yet') for line in starter),
        'starter failures must collapse to one line per function')


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def enc(value):
    if isinstance(value, bool) or isinstance(value, str) or value is None:
        return value
    if isinstance(value, (int, float)):
        return dec(value)
    if isinstance(value, dict):
        return {k: enc(v) for k, v in value.items()}
    return [enc(v) for v in value]


def entry(structure, keys, args):
    return {'structure': structure, 'inputs': {k: enc(v) for k, v in zip(keys, args)}}


def json_depth(value):
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        return 1 + max([json_depth(v) for v in value] or [0])
    return 0


SAMPLE_DEPTH_LIMIT = 40  # the app's strict JSON parser stops at nesting depth 48; deeper cases stay self-check-only


def shallow(entries):
    """Samples mirror every case except those whose JSON nesting (inputs object included) exceeds the limit."""
    return [e for e in entries if json_depth(e['inputs']) + 1 <= SAMPLE_DEPTH_LIMIT]


expected_samples = shallow(
    [entry('reasoning.apply-action@1', ('state', 'pre', 'add', 'del'), a) for a, _ in kit._APPLY_CASES]
    + [entry('reasoning.update-belief@1', ('belief', 'fact', 'observed'), a) for a, _ in kit._UPDATE_CASES]
    + [entry('reasoning.posterior@1', ('belief', 'weights', 'fact', 'observed'), a)
       for a, _ in kit._POSTERIOR_CASES]
    + [entry('reasoning.plan-failures@1', ('belief', 'plan', 'actions', 'goal'), a)
       for a, _ in kit._FAIL_CASES]
    + [entry('reasoning.success-probability@1', ('belief', 'weights', 'plan', 'actions', 'goal'), a)
       for a, _ in kit._SUCCESS_CASES]
    + [entry('reasoning.ungrounded@1', ('belief', 'plan', 'actions'), a)
       for a, _ in kit._UNGROUNDED_CASES])
samples = json.loads((root / 'content/labs/L22-reasoning.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L22-reasoning'], 'samples must hold only L22-reasoning')
require(samples['kits']['L22-reasoning'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')


# ---- author reference implementation (validating) ----
FACT = re.compile(r'[a-z][a-z0-9_]*\([a-z][a-z0-9_]*(,[a-z][a-z0-9_]*)*\)')
NAME = re.compile(r'[a-z][a-z0-9_]*')


def bad():
    raise ValueError


def is_fact(f):
    return type(f) is str and len(f) <= 40 and FACT.fullmatch(f) is not None and f.isascii()


def facts(value, low, high):
    if not isinstance(value, (list, tuple)) or not low <= len(value) <= high:
        bad()
    if not all(is_fact(f) for f in value) or len(set(value)) != len(value):
        bad()
    return frozenset(value)


def one_fact(f):
    if not is_fact(f):
        bad()
    return f


def boolean(b):
    if type(b) is not bool:
        bad()
    return b


def belief_of(belief):
    if not isinstance(belief, (list, tuple)) or not 1 <= len(belief) <= 16:
        bad()
    worlds = [facts(w, 0, 20) for w in belief]
    if len(set(worlds)) != len(worlds):
        bad()
    return worlds


def weights_of(weights, n):
    if not isinstance(weights, (list, tuple)) or len(weights) != n:
        bad()
    for x in weights:
        if type(x) not in (int, float) or not math.isfinite(x) or not 0 < x <= 1e6:
            bad()
    return list(weights)


def table_of(actions):
    if not isinstance(actions, dict) or len(actions) > 24:
        bad()
    out = {}
    for name, spec_ in actions.items():
        if type(name) is not str or len(name) > 40 or NAME.fullmatch(name) is None:
            bad()
        if not isinstance(spec_, dict):
            bad()
        if set(spec_) == {'pre', 'add', 'del'}:
            out[name] = ('do', facts(spec_['pre'], 0, 6), facts(spec_['add'], 0, 6),
                         facts(spec_['del'], 0, 6), None)
        elif set(spec_) == {'pre', 'sense'}:
            out[name] = ('sense', facts(spec_['pre'], 0, 6), frozenset(), frozenset(),
                         one_fact(spec_['sense']))
        else:
            bad()
    return out


def plan_of(plan, table, allow_missing=False):
    """Validate iteratively (cycles hit the node cap) and return plan as nested tuples."""
    count = 0
    stack = [plan]
    while stack:
        node = stack.pop()
        count += 1
        if count > 64 or not isinstance(node, (list, tuple)) or not node or type(node[0]) is not str:
            bad()
        kind, size = node[0], len(node)
        if kind == 'stop' and size == 1:
            continue
        if kind not in ('do', 'sense') or size != (3 if kind == 'do' else 4):
            bad()
        if type(node[1]) is not str:
            bad()
        if node[1] in table:
            if table[node[1]][0] != kind:
                bad()
        elif not allow_missing:
            bad()
        stack.extend(node[2:])

    def freeze(node):
        return ('stop',) if node[0] == 'stop' else (node[0], node[1]) + tuple(freeze(n) for n in node[2:])
    return freeze(plan)


def goal_of(goal):
    return facts(goal, 1, 6)


def core_apply(s, pre, add, dele):
    return None if not pre <= s else (s - dele) | add


def apply_action(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    out = core_apply(s, p, a, d)
    return None if out is None else tuple(sorted(out))


def update_belief(belief, fact, observed):
    worlds, f, o = belief_of(belief), one_fact(fact), boolean(observed)
    return [tuple(sorted(w)) for w in worlds if (f in w) == o]


def posterior(belief, weights, fact, observed):
    worlds = belief_of(belief)
    ws, f, o = weights_of(weights, len(worlds)), one_fact(fact), boolean(observed)
    kept = [x for w, x in zip(worlds, ws) if (f in w) == o]
    total = sum(kept)
    return [x/total for x in kept]


def run_world(world, node, table, goal):
    """Recursive reference: None on success, else the failure reason."""
    if node[0] == 'stop':
        return None if goal <= world else 'goal'
    kind, _, pre, add, dele, sense = table[node[1]][0], 0, *table[node[1]][1:]
    if not pre <= world:
        return 'precondition'
    if kind == 'do':
        return run_world((world - dele) | add, node[2], table, goal)
    return run_world(world, node[2] if sense in world else node[3], table, goal)


def failures_core(worlds, plan, table, goal):
    return [(i, r) for i, w in enumerate(worlds) for r in [run_world(w, plan, table, goal)] if r]


def plan_failures(belief, plan, actions, goal):
    worlds, table = belief_of(belief), table_of(actions)
    return failures_core(worlds, plan_of(plan, table), table, goal_of(goal))


def success_probability(belief, weights, plan, actions, goal):
    worlds = belief_of(belief)
    ws, table = weights_of(weights, len(worlds)), table_of(actions)
    failed = {i for i, _ in failures_core(worlds, plan_of(plan, table), table, goal_of(goal))}
    return sum(x for i, x in enumerate(ws) if i not in failed)/sum(ws)


def used_names(plan):
    out, stack = [], [plan]
    while stack:
        node = stack.pop()
        if node[0] != 'stop':
            out.append(node[1])
            stack.extend(node[2:])
    return out


def objects(fact):
    return fact[fact.index('(') + 1:-1].split(',')


def ungrounded(belief, plan, actions):
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    known = {o for w in worlds for f in w for o in objects(f)}
    used = used_names(tree)
    needed = set()
    for name in set(used) & set(table):
        _, pre, add, dele, sense = table[name]
        for f in set(pre) | set(add) | set(dele) | ({sense} if sense else set()):
            needed.update(objects(f))
    return (tuple(sorted({n for n in used if n not in table})), tuple(sorted(needed - known)))


refs = dict(apply_action=apply_action, update_belief=update_belief, posterior=posterior,
            plan_failures=plan_failures, success_probability=success_probability,
            ungrounded=ungrounded)


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


require(run_with({}) == [], 'reference implementation must pass: ' + str(run_with({})[:5]))


# ---- valid alternatives (different formulations) ----
def alt_bitmask(belief, plan, actions, goal):
    """Facts mapped to bits; worlds and effects are integers; iterative walk."""
    worlds, table, g = belief_of(belief), table_of(actions), goal_of(goal)
    tree = plan_of(plan, table)
    index = {}

    def bit(fs):
        mask = 0
        for f in fs:
            mask |= 1 << index.setdefault(f, len(index))
        return mask
    wm = [bit(w) for w in worlds]
    gm = bit(g)
    tm = {n: (k, bit(p), bit(a), bit(d), index.setdefault(s, len(index)) if s else None)
          for n, (k, p, a, d, s) in table.items()}
    out = []
    for i, w in enumerate(wm):
        node, reason = tree, None
        while True:
            if node[0] == 'stop':
                reason = None if gm & ~w == 0 else 'goal'
                break
            k, p, a, d, s = tm[node[1]]
            if p & ~w:
                reason = 'precondition'
                break
            if k == 'do':
                w = (w & ~d) | a
                node = node[2]
            else:
                node = node[2] if w >> s & 1 else node[3]
        if reason:
            out.append((i, reason))
    return out


def alt_paths(belief, plan, actions, goal):
    """Per-world path as a generator of events instead of a loop; sorted by index."""
    worlds, table, g = belief_of(belief), table_of(actions), goal_of(goal)
    tree = plan_of(plan, table)

    def verdict(w, node):
        while node[0] != 'stop':
            _, pre, add, dele, sense = table[node[1]]
            if not pre.issubset(w):
                return 'precondition'
            if sense is None:
                w, node = w.difference(dele).union(add), node[2]
            else:
                node = (node[3], node[2])[sense in w]
        return None if g.issubset(w) else 'goal'
    pairs = ((i, verdict(w, tree)) for i, w in enumerate(worlds))
    return [(i, r) for i, r in pairs if r is not None]


def alt_apply_list(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    if any(f not in s for f in p):
        return None
    kept = [f for f in s if f not in d]
    return tuple(sorted(set(kept + list(a))))


def alt_update_partition(belief, fact, observed):
    worlds, f, o = belief_of(belief), one_fact(fact), boolean(observed)
    yes = [w for w in worlds if f in w]
    no = [w for w in worlds if f not in w]
    pick = yes if o else no
    original = [tuple(sorted(w)) for w in worlds]
    return [t for t, w in zip(original, worlds) if w in pick]


def alt_posterior_fraction(belief, weights, fact, observed):
    worlds = belief_of(belief)
    ws, f, o = weights_of(weights, len(worlds)), one_fact(fact), boolean(observed)
    kept = [Fraction(x) for w, x in zip(worlds, ws) if (f in w) == o]
    total = sum(kept, Fraction(0))
    return [float(x/total) for x in kept]


def alt_success_complement(belief, weights, plan, actions, goal):
    worlds = belief_of(belief)
    ws, table = weights_of(weights, len(worlds)), table_of(actions)
    failed = failures_core(worlds, plan_of(plan, table), table, goal_of(goal))
    return 1 - sum(ws[i] for i, _ in failed)/sum(ws)


def alt_ungrounded_flat(belief, plan, actions):
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    known = {o for w in worlds for f in w for o in f[:-1].split('(')[1].split(',')}
    used = sorted(set(used_names(tree)))
    missing = tuple(n for n in used if n not in table)
    flat = [f for n in used if n in table
            for f in (*table[n][1], *table[n][2], *table[n][3], *([table[n][4]] if table[n][4] else []))]
    return (missing, tuple(sorted({o for f in flat for o in f[:-1].split('(')[1].split(',')} - known)))


alternatives = [
    ('bitmask worlds', {'plan_failures': alt_bitmask}),
    ('generator verdicts with set methods', {'plan_failures': alt_paths}),
    ('list-based apply_action', {'apply_action': alt_apply_list}),
    ('partition-based update_belief', {'update_belief': alt_update_partition}),
    ('Fraction posterior', {'posterior': alt_posterior_fraction}),
    ('complement success probability + flat ungrounded',
     {'success_probability': alt_success_complement, 'ungrounded': alt_ungrounded_flat}),
    ('tuple-returning variants', {
        'update_belief': lambda *a: tuple(update_belief(*a)),
        'plan_failures': lambda *a: tuple(list(p) for p in plan_failures(*a)),
        'ungrounded': lambda *a: [list(x) for x in ungrounded(*a)]}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'valid alternative rejected: ' + label + ' ' + str(result[:4]))


# ---- injected bugs: each must be rejected, and for its intended reason ----
def accepts_when(predicate, function):
    def run(*args):
        if predicate(*args):
            return function(*[a for a in kit_valid(function)])
        return function(*args)
    return run


valid_args = {
    'apply_action': (['at(home)'], ['at(home)'], ['b(x)'], []),
    'update_belief': ([['a(x)'], ['b(x)']], 'a(x)', True),
    'posterior': ([['a(x)'], ['b(x)']], [1, 1], 'a(x)', True),
    'plan_failures': ([['a(x)']], ['stop'], {}, ['a(x)']),
    'success_probability': ([['a(x)']], [1], ['stop'], {}, ['a(x)']),
    'ungrounded': ([['a(x)']], ['stop'], {}),
}


def lenient(name, predicate):
    """A buggy validator: accepts the invalid input selected by predicate."""
    function = refs[name]

    def run(*args):
        if predicate(*args):
            return function(*valid_args[name])
        return function(*args)
    return run


def pre_ignored(state, pre, add, dele):
    s, a, d = facts(state, 0, 20), facts(add, 0, 6), facts(dele, 0, 6)
    facts(pre, 0, 6)
    return tuple(sorted((s - d) | a))


def pre_reversed(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    return tuple(sorted((s - d) | a)) if s <= p else None


def add_then_delete(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    return tuple(sorted((s | a) - d)) if p <= s else None


def no_deletes(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    return tuple(sorted(s | a)) if p <= s else None


def no_adds(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    return tuple(sorted(s - d)) if p <= s else None


def unsorted_apply(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    if not p <= s:
        return None
    return tuple([f for f in state if f not in d] + [f for f in add if f not in state])


def empty_instead_of_none(state, pre, add, dele):
    out = apply_action(state, pre, add, dele)
    return () if out is None else out


def duplicates_apply(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    if not p <= s:
        return None
    return tuple(sorted([f for f in state if f not in d] + list(add)))


def mutates_state(state, pre, add, dele):
    out = apply_action(state, pre, add, dele)
    if out is not None and isinstance(state, list):
        state.append('zz(x)')
    return out


def pre_on_result(state, pre, add, dele):
    s, p, a, d = facts(state, 0, 20), facts(pre, 0, 6), facts(add, 0, 6), facts(dele, 0, 6)
    result = (s - d) | a
    return tuple(sorted(result)) if p <= result else None


def inverted_filter(belief, fact, observed):
    worlds, f, o = belief_of(belief), one_fact(fact), boolean(observed)
    return [tuple(sorted(w)) for w in worlds if (f in w) != o]


def ignores_observed(belief, fact, observed):
    worlds, f, o = belief_of(belief), one_fact(fact), boolean(observed)
    return [tuple(sorted(w)) for w in worlds if f in w]


def false_is_no_information(belief, fact, observed):
    worlds, f, o = belief_of(belief), one_fact(fact), boolean(observed)
    return [tuple(sorted(w)) for w in worlds if f in w or not o]


def sorted_belief(belief, fact, observed):
    return sorted(update_belief(belief, fact, observed), reverse=True)


def unsorted_worlds(belief, fact, observed):
    worlds, f, o = belief_of(belief), one_fact(fact), boolean(observed)
    return [tuple(w0) for w0, w in zip(belief, worlds) if (f in w) == o]


def none_when_empty(belief, fact, observed):
    return update_belief(belief, fact, observed) or None


def raises_when_empty(belief, fact, observed):
    out = update_belief(belief, fact, observed)
    if not out:
        raise ValueError('contradiction')
    return out


def update_mutates(belief, fact, observed):
    out = update_belief(belief, fact, observed)
    if isinstance(belief, list) and len(belief) > 1:
        belief[:] = out + belief[len(out):] if False else belief
        belief.reverse()
    return out


def unnormalised(belief, weights, fact, observed):
    worlds = belief_of(belief)
    ws, f, o = weights_of(weights, len(worlds)), one_fact(fact), boolean(observed)
    return [float(x) for w, x in zip(worlds, ws) if (f in w) == o]


def normalised_by_all(belief, weights, fact, observed):
    worlds = belief_of(belief)
    ws, f, o = weights_of(weights, len(worlds)), one_fact(fact), boolean(observed)
    return [x/sum(ws) for w, x in zip(worlds, ws) if (f in w) == o]


def uniform_posterior(belief, weights, fact, observed):
    kept = update_belief(belief, fact, observed)
    weights_of(weights, len(belief))
    return [1/len(kept)]*len(kept)


def zero_padded(belief, weights, fact, observed):
    worlds = belief_of(belief)
    ws, f, o = weights_of(weights, len(worlds)), one_fact(fact), boolean(observed)
    total = sum(x for w, x in zip(worlds, ws) if (f in w) == o)
    return [x/total if (f in w) == o else 0.0 for w, x in zip(worlds, ws)] if total else []


def none_posterior(belief, weights, fact, observed):
    return posterior(belief, weights, fact, observed) or None


def percent_posterior(belief, weights, fact, observed):
    return [100*x for x in posterior(belief, weights, fact, observed)]


def knobbed(belief, plan, actions, goal, swap=False, skip_do_pre=False, skip_sense_pre=False,
            add_first=False, goal_any=False, no_goal=False, first_branch=False, initial_sense=False,
            only_first_world=False, subset_reversed=False, missing_skip=False):
    """Reference plan runner with one realistic bug switched on; returns (index, reason) pairs."""
    worlds, table, g = belief_of(belief), table_of(actions), goal_of(goal)
    if missing_skip:
        tree = plan_of(plan, table, allow_missing=True)
    else:
        tree = plan_of(plan, table)
    out = []
    for i, w0 in enumerate(worlds):
        if only_first_world and i > 0:
            break
        w, node, reason = w0, tree, None
        while True:
            if node[0] == 'stop':
                ok = (not g) or (any(f in w for f in g) if goal_any else g <= w)
                if no_goal:
                    ok = True
                if subset_reversed:
                    ok = w <= g
                reason = None if ok else 'goal'
                break
            if node[1] not in table:
                node = node[2]
                continue
            kind, pre, add, dele, sense = table[node[1]]
            if not pre <= w and not (skip_do_pre if kind == 'do' else skip_sense_pre):
                reason = 'precondition'
                break
            if kind == 'do':
                w = ((w | add) - dele) if add_first else ((w - dele) | add)
                node = node[2]
            else:
                value = (sense in (w0 if initial_sense else w))
                if first_branch:
                    value = True
                if swap:
                    value = not value
                node = node[2] if value else node[3]
        if reason:
            out.append((i, reason))
    return out


def pf(**knobs):
    return lambda belief, plan, actions, goal: knobbed(belief, plan, actions, goal, **knobs)


def sp(**knobs):
    def run(belief, weights, plan, actions, goal):
        worlds = belief_of(belief)
        ws = weights_of(weights, len(worlds))
        failed = {i for i, _ in knobbed(belief, plan, actions, goal, **knobs)}
        return sum(x for i, x in enumerate(ws) if i not in failed)/sum(ws)
    return run


def first_failure_only(belief, plan, actions, goal):
    return plan_failures(belief, plan, actions, goal)[:1]


def one_reason(reason):
    return lambda belief, plan, actions, goal: [(i, reason) for i, _ in plan_failures(belief, plan, actions, goal)]


def world_index_missing(belief, plan, actions, goal):
    return [(i, r) for i, r in plan_failures(belief, plan, actions, goal) if r == 'goal'] or \
        [(i, r) for i, r in plan_failures(belief, plan, actions, goal)]


def worlds_instead_of_indices(belief, plan, actions, goal):
    worlds = belief_of(belief)
    return [(tuple(sorted(worlds[i])), r) for i, r in plan_failures(belief, plan, actions, goal)]


def failing_count(belief, weights, plan, actions, goal):
    worlds = belief_of(belief)
    ws = weights_of(weights, len(worlds))
    fails = plan_failures(belief, plan, actions, goal)
    return sum(ws[i] for i, _ in fails)/sum(ws)


def unweighted_success(belief, weights, plan, actions, goal):
    worlds = belief_of(belief)
    weights_of(weights, len(worlds))
    return 1 - len(plan_failures(belief, plan, actions, goal))/len(worlds)


def success_over_success(belief, weights, plan, actions, goal):
    worlds = belief_of(belief)
    ws = weights_of(weights, len(worlds))
    failed = {i for i, _ in plan_failures(belief, plan, actions, goal)}
    ok = sum(x for i, x in enumerate(ws) if i not in failed)
    return 1.0 if ok else 0.0


def percent_success(belief, weights, plan, actions, goal):
    return 100*success_probability(belief, weights, plan, actions, goal)


def ungrounded_whole_table(belief, plan, actions):
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    known = {o for w in worlds for f in w for o in objects(f)}
    needed = set()
    for _, pre, add, dele, sense in table.values():
        for f in set(pre) | set(add) | set(dele) | ({sense} if sense else set()):
            needed.update(objects(f))
    return (tuple(sorted({n for n in used_names(tree) if n not in table})),
            tuple(sorted(needed - known)))


def ungrounded_pre_only(belief, plan, actions):
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    known = {o for w in worlds for f in w for o in objects(f)}
    needed = set()
    for name in set(used_names(tree)) & set(table):
        for f in table[name][1]:
            needed.update(objects(f))
    return (tuple(sorted({n for n in used_names(tree) if n not in table})),
            tuple(sorted(needed - known)))


def ungrounded_no_sense(belief, plan, actions):
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    known = {o for w in worlds for f in w for o in objects(f)}
    needed = set()
    for name in set(used_names(tree)) & set(table):
        _, pre, add, dele, sense = table[name]
        for f in set(pre) | set(add) | set(dele):
            needed.update(objects(f))
    return (tuple(sorted({n for n in used_names(tree) if n not in table})),
            tuple(sorted(needed - known)))


def ungrounded_unsorted(belief, plan, actions):
    missing, objs = ungrounded(belief, plan, actions)
    return (missing[::-1], objs[::-1])


def ungrounded_duplicates(belief, plan, actions):
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    return (tuple(n for n in used_names(tree) if n not in table), ungrounded(belief, plan, actions)[1])


def ungrounded_first_world(belief, plan, actions):
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    known = {o for f in worlds[0] for o in objects(f)}
    needed = set()
    for name in set(used_names(tree)) & set(table):
        _, pre, add, dele, sense = table[name]
        for f in set(pre) | set(add) | set(dele) | ({sense} if sense else set()):
            needed.update(objects(f))
    return (ungrounded(belief, plan, actions)[0], tuple(sorted(needed - known)))


def ungrounded_predicates(belief, plan, actions):
    missing, objs = ungrounded(belief, plan, actions)
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    known = {f[:f.index('(')] for w in worlds for f in w}
    extra = {f[:f.index('(')] for name in set(used_names(tree)) & set(table)
             for f in set(table[name][1]) | set(table[name][2]) | set(table[name][3])}
    return (missing, tuple(sorted(set(objs) | (extra - known))))


def ungrounded_goal_too(belief, plan, actions):
    missing, objs = ungrounded(belief, plan, actions)
    return (missing, tuple(sorted(set(objs) | {'home'} - {'home'} | set(objects('delivered(cabinet)')) & {'cabinet'})))


def ungrounded_reachable_only(belief, plan, actions):
    """Inspects only the true branch of sensing nodes."""
    worlds, table = belief_of(belief), table_of(actions)
    tree = plan_of(plan, table, allow_missing=True)
    names, node = [], tree
    while node[0] != 'stop':
        names.append(node[1])
        node = node[2]
    known = {o for w in worlds for f in w for o in objects(f)}
    needed = set()
    for name in set(names) & set(table):
        _, pre, add, dele, sense = table[name]
        for f in set(pre) | set(add) | set(dele) | ({sense} if sense else set()):
            needed.update(objects(f))
    return (tuple(sorted({n for n in names if n not in table})), tuple(sorted(needed - known)))


def ungrounded_raises_on_missing(belief, plan, actions):
    table = table_of(actions)
    plan_of(plan, table)
    return ungrounded(belief, plan, actions)


def ungrounded_mutates(belief, plan, actions):
    out = ungrounded(belief, plan, actions)
    if isinstance(actions, dict) and actions:
        actions.pop(next(iter(actions)))
    return out


def plan_mutates(belief, plan, actions, goal):
    out = plan_failures(belief, plan, actions, goal)
    if isinstance(plan, list) and plan[0] == 'do':
        plan[0] = 'do'
        plan.append(None)
    return out


def too_big(plan):
    count, stack = 0, [plan]
    while stack and count <= 64:
        node = stack.pop()
        count += 1
        if isinstance(node, list) and node and node[0] in ('do', 'sense'):
            stack.extend(node[2:])
    return count > 64


def node_count(plan):
    count, stack = 0, [plan]
    while stack and count <= 100:
        node = stack.pop()
        count += 1
        if isinstance(node, list) and node and node[0] in ('do', 'sense'):
            stack.extend(node[2:])
    return count


mutants = [
    ('lenient: 65-node plan accepted (cap 65)', {'plan_failures': lenient(
        'plan_failures', lambda b, p, a, g: node_count(p) == 65)}),
    ('strict: 64-node plan rejected (cap 63)', {'plan_failures': (
        lambda b, p, a, g: bad() if node_count(p) >= 64 else plan_failures(b, p, a, g))}),
    ('ungrounded repeats a missing action used twice', {'ungrounded': (
        lambda b, p, a: (lambda r: (r[0] + r[0][:1], r[1]))(ungrounded(b, p, a)))}),
    ('lenient: unused action with bad fact accepted', {'plan_failures': lenient(
        'plan_failures', lambda b, p, a, g: isinstance(a, dict) and any(
            isinstance(s_, dict) and s_.get('pre') == ['bad'] for s_ in a.values()))}),

    ('apply_action ignores preconditions', {'apply_action': pre_ignored}),
    ('apply_action pre/state subset reversed', {'apply_action': pre_reversed}),
    ('apply_action adds then deletes', {'apply_action': add_then_delete}),
    ('apply_action forgets deletes', {'apply_action': no_deletes}),
    ('apply_action forgets adds', {'apply_action': no_adds}),
    ('apply_action result not sorted', {'apply_action': unsorted_apply}),
    ('apply_action returns () instead of None', {'apply_action': empty_instead_of_none}),
    ('apply_action returns duplicates', {'apply_action': duplicates_apply}),
    ('apply_action mutates the state', {'apply_action': mutates_state}),
    ('apply_action checks pre on the result', {'apply_action': pre_on_result}),
    ('update_belief keeps the opposite worlds', {'update_belief': inverted_filter}),
    ('update_belief ignores observed (keeps true)', {'update_belief': ignores_observed}),
    ('update_belief: a negative observation is no information', {'update_belief': false_is_no_information}),
    ('update_belief reorders the belief', {'update_belief': sorted_belief}),
    ('update_belief leaves worlds unsorted', {'update_belief': unsorted_worlds}),
    ('update_belief returns None when empty', {'update_belief': none_when_empty}),
    ('update_belief raises when empty', {'update_belief': raises_when_empty}),
    ('update_belief mutates the belief', {'update_belief': update_mutates}),
    ('posterior not normalised', {'posterior': unnormalised}),
    ('posterior normalised by all worlds', {'posterior': normalised_by_all}),
    ('posterior ignores weights', {'posterior': uniform_posterior}),
    ('posterior zero-pads eliminated worlds', {'posterior': zero_padded}),
    ('posterior returns None when empty', {'posterior': none_posterior}),
    ('posterior in percent', {'posterior': percent_posterior}),
    ('plan_failures: sensing branches swapped', {'plan_failures': pf(swap=True)}),
    ('plan_failures: sensing precondition skipped', {'plan_failures': pf(skip_sense_pre=True)}),
    ('plan_failures: action preconditions skipped', {'plan_failures': pf(skip_do_pre=True)}),
    ('plan_failures: effects add then delete', {'plan_failures': pf(add_first=True)}),
    ('plan_failures: goal needs only one fact', {'plan_failures': pf(goal_any=True)}),
    ('plan_failures: goal never checked', {'plan_failures': pf(no_goal=True)}),
    ('plan_failures: always the true branch', {'plan_failures': pf(first_branch=True)}),
    ('plan_failures: senses the initial world', {'plan_failures': pf(initial_sense=True)}),
    ('plan_failures: only the first world checked', {'plan_failures': pf(only_first_world=True)}),
    ('plan_failures: goal test reversed (world subset of goal)', {'plan_failures': pf(subset_reversed=True)}),
    ('plan_failures: unknown action silently skipped', {'plan_failures': pf(missing_skip=True)}),
    ('plan_failures reports only the first failure', {'plan_failures': first_failure_only}),
    ('plan_failures: every reason "precondition"', {'plan_failures': one_reason('precondition')}),
    ('plan_failures: every reason "goal"', {'plan_failures': one_reason('goal')}),
    ('plan_failures returns worlds, not indices', {'plan_failures': worlds_instead_of_indices}),
    ('plan_failures mutates the plan', {'plan_failures': plan_mutates}),
    ('success_probability counts the failing weight', {'success_probability': failing_count}),
    ('success_probability ignores weights', {'success_probability': unweighted_success}),
    ('success_probability is 1.0 when anything succeeds', {'success_probability': success_over_success}),
    ('success_probability in percent', {'success_probability': percent_success}),
    ('success_probability: sensing branches swapped', {'success_probability': sp(swap=True)}),
    ('success_probability: goal never checked', {'success_probability': sp(no_goal=True)}),
    ('ungrounded scans the whole action table', {'ungrounded': ungrounded_whole_table}),
    ('ungrounded looks at preconditions only', {'ungrounded': ungrounded_pre_only}),
    ('ungrounded ignores the sense fact', {'ungrounded': ungrounded_no_sense}),
    ('ungrounded not sorted', {'ungrounded': ungrounded_unsorted}),
    ('ungrounded reports duplicate action names', {'ungrounded': ungrounded_duplicates}),
    ('ungrounded knows only the first world', {'ungrounded': ungrounded_first_world}),
    ('ungrounded counts predicate names as objects', {'ungrounded': ungrounded_predicates}),
    ('ungrounded follows only the do-chain', {'ungrounded': ungrounded_reachable_only}),
    ('ungrounded raises on a missing action', {'ungrounded': ungrounded_raises_on_missing}),
    ('ungrounded mutates the action table', {'ungrounded': ungrounded_mutates}),
    # validation bugs
    ('lenient: uppercase fact accepted', {'update_belief': lenient(
        'update_belief', lambda b, f, o: type(f) is str and f != f.lower())}),
    ('lenient: fact without arguments accepted', {'posterior': lenient(
        'posterior', lambda b, w, f, o: type(f) is str and f.endswith('()'))}),
    ('lenient: truthy observed accepted', {'update_belief': lenient(
        'update_belief', lambda b, f, o: o in (0, 1) and type(o) is not bool)}),
    ('lenient: duplicate worlds accepted', {'posterior': lenient(
        'posterior', lambda b, w, f, o: isinstance(b, list) and len(b) > 1
        and all(isinstance(x, list) for x in b) and len({frozenset(x) for x in b}) < len(b))}),
    ('lenient: empty belief accepted', {'update_belief': lenient(
        'update_belief', lambda b, f, o: isinstance(b, (list, tuple)) and len(b) == 0)}),
    ('lenient: bool weight accepted', {'posterior': lenient(
        'posterior', lambda b, w, f, o: isinstance(w, (list, tuple)) and any(type(x) is bool for x in w))}),
    ('lenient: zero weight accepted', {'success_probability': lenient(
        'success_probability', lambda b, w, p, a, g: isinstance(w, (list, tuple))
        and any(type(x) in (int, float) and x == 0 for x in w))}),
    ('lenient: NaN weight accepted', {'posterior': lenient(
        'posterior', lambda b, w, f, o: isinstance(w, (list, tuple))
        and any(type(x) is float and x != x for x in w))}),
    ('lenient: weight length mismatch accepted', {'posterior': lenient(
        'posterior', lambda b, w, f, o: isinstance(w, (list, tuple)) and isinstance(b, (list, tuple))
        and len(w) != len(b))}),
    ('lenient: duplicate pre facts accepted', {'apply_action': lenient(
        'apply_action', lambda s, p, a, d: isinstance(p, (list, tuple)) and all(type(x) is str for x in p)
        and len(set(p)) < len(p))}),
    ('lenient: sensing action used in a do node accepted', {'plan_failures': lenient(
        'plan_failures', lambda b, p, a, g: isinstance(p, list) and p[:1] == ['do'] and len(p) > 1
        and isinstance(p[1], str) and isinstance(a, dict) and 'sense' in a.get(p[1], {}))}),
    ('lenient: unknown action in plan_failures accepted', {'plan_failures': lenient(
        'plan_failures', lambda b, p, a, g: isinstance(p, list) and len(p) > 1 and isinstance(a, dict)
        and isinstance(p[1], str) and p[1] == 'no_such_action')}),
    ('lenient: oversized plan accepted', {'plan_failures': lenient(
        'plan_failures', lambda b, p, a, g: too_big(p))}),
    ('lenient: action spec with extra key accepted', {'ungrounded': lenient(
        'ungrounded', lambda b, p, a: isinstance(a, dict) and any(
            isinstance(s, dict) and 'extra' in s for s in a.values()))}),
    ('lenient: empty goal accepted', {'plan_failures': lenient(
        'plan_failures', lambda b, p, a, g: isinstance(g, (list, tuple)) and len(g) == 0)}),
    ('lenient: world of 21 facts accepted', {'apply_action': lenient(
        'apply_action', lambda s, p, a, d: isinstance(s, (list, tuple)) and len(s) > 20)}),
    ('lenient: fact with trailing newline accepted', {'update_belief': lenient(
        'update_belief', lambda b, f, o: type(f) is str and f.endswith('\n'))}),
    ('strict: tuple belief rejected', {'update_belief': (
        lambda b, f, o: update_belief(b, f, o) if isinstance(b, list) else bad())}),
    ('strict: tuple plan rejected', {'plan_failures': (
        lambda b, p, a, g: plan_failures(b, p, a, g) if isinstance(p, list) else bad())}),
    ('strict: integer weights rejected', {'posterior': (
        lambda b, w, f, o: posterior(b, w, f, o) if all(type(x) is float for x in w) else bad())}),
]
require(len(mutants) >= 30, 'need at least 30 mutants')
for label, over in mutants:
    require(run_with(over), 'false accept: ' + label)
print('Reasoning kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
