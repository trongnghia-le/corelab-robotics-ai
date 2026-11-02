"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (rule chain, data table, per-state handlers,
inline replay, backward-scan monitor) that must pass, and named injected bugs that must
be rejected. Plain checks only, so it also works under python -O.
"""
import ast
import importlib.util
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('executive_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L15-executive.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names}
imported |= {node.module.split('.')[0] for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom) and node.module}
require(imported <= {'math'}, 'kit imports beyond math: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
names = ('is_stale', 'transition', 'replay', 'unsafe_motion_indices')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _transition_ref') > spoiler and text.index('def _unsafe_ref') > spoiler
        and text.index('_T_CASES =') > spoiler, 'oracle and tables must sit below the banner')
spec = importlib.util.spec_from_file_location('executive_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check([])
require(starter and len(starter) == 4 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented function into one line: ' + str(starter))
require(all(f.isascii() for f in starter), 'starter messages must be ASCII')

STATES, EVENTS, MOTION = kit.STATES, kit.EVENTS, kit.MOTION
ENTRY = {'APPROACH': 'move_pick', 'GRASP': 'close_gripper', 'TRANSPORT': 'move_drop',
         'RELEASE': 'open_gripper'}
ACTIVE = tuple(ENTRY)

# ---- samples manifest mirrors the selected positive cases ----


def enc(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [enc(v) for v in value]
    if type(value) is int:
        return str(value)
    return value


def entry(structure, keys, args):
    return {'structure': structure, 'inputs': {k: enc(v) for k, v in zip(keys, args)}}


STALE_PICK = (0, 3, 4, 5)
T_PICK = (0, 1, 2, 3, 4, 8, 10, 11, 12, 14, 15, 16, 17, 20, 21, 23, 25, 26, 28, 31, 32, 34, 36, 39, 41, 43)
R_PICK = (1, 2, 3, 4, 5, 6, 7, 8, 10, 13)
U_PICK = (1, 3, 4, 5, 7, 9, 10, 12, 13, 14)
expected = (
    [entry('executive.is-stale@1', ('age', 'max_age'), kit._STALE_CASES[i][0]) for i in STALE_PICK]
    + [entry('executive.transition@1', ('state', 'event', 'age', 'retries', 'max_age', 'max_retries'),
             kit._T_CASES[i][0]) for i in T_PICK]
    + [entry('executive.replay@1', ('events', 'max_age', 'max_retries'), kit._R_CASES[i][0]) for i in R_PICK]
    + [entry('executive.monitor@1', ('events', 'commands', 'max_age'), kit._U_CASES[i][0]) for i in U_PICK])
require(len(expected) <= 50, 'kit sample cap is 50: ' + str(len(expected)))
samples = json.loads((root / 'content/labs/L15-executive.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1', 'samples schema')
require(list(samples['kits']) == ['L15-executive'], 'samples must hold only L15-executive')
require(samples['kits']['L15-executive'] == expected, 'samples manifest does not mirror the self-check cases')

# ---- independent implementations ----


def is_int(v, lo, hi):
    return type(v) is int and lo <= v <= hi


def v_age(a):
    if a is not None and not is_int(a, 0, 1000000):
        raise ValueError


_SKIP = object()


def v_cfg(max_age, max_retries=_SKIP):
    if not is_int(max_age, 1, 100000):
        raise ValueError
    if max_retries is not _SKIP and not is_int(max_retries, 0, 5):
        raise ValueError


def v_trans_args(state, event, age, retries, max_age, max_retries):
    if type(state) is not str or state not in STATES or type(event) is not str or event not in EVENTS:
        raise ValueError
    v_age(age)
    v_cfg(max_age, max_retries)
    if not is_int(retries, 0, max_retries):
        raise ValueError


def v_events(events):
    if not isinstance(events, (list, tuple)) or len(events) > 200:
        raise ValueError
    prev = 0
    out = []
    for p in events:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise ValueError
        t, n = p
        if not is_int(t, 0, 1000000) or type(n) is not str or n not in EVENTS or t < prev:
            raise ValueError
        prev = t
        out.append((t, n))
    return out


def v_commands(commands, count):
    if not isinstance(commands, (list, tuple)) or len(commands) != count:
        raise ValueError
    for c in commands:
        if not isinstance(c, (list, tuple)) or len(c) > 10:
            raise ValueError
        for x in c:
            if type(x) is not str or x not in MOTION + ('stop',):
                raise ValueError


# --- rule chain with switchable bugs (also the default valid reference) ---
def make_transition(f=None):
    f = f or {}

    def transition(state, event, age, retries, max_age, max_retries):
        v_trans_args(state, event, age, retries, max_age, max_retries)
        active = state in ENTRY
        hold = state.startswith('HOLD_')
        if age is None:
            stale = not f.get('none_fresh')
        elif f.get('stale_ge'):
            stale = age >= max_age
        elif f.get('stale_plus1'):
            stale = age > max_age + 1
        else:
            stale = age > max_age
        wd_phases = f.get('wd_phases', ACTIVE)

        def fault():
            if event != 'fault':
                return None
            if state == 'FAULT':
                return (state, (), retries)
            if f.get('fault_hold_ignored') and hold:
                return (state, (), retries)
            stop = active or bool(f.get('fault_always_stop'))
            if f.get('fault_nostop'):
                stop = False
            return ('IDLE' if f.get('fault_idle') else 'FAULT', ('stop',) if stop else (),
                    0 if f.get('fault_clears_retries') else retries)

        def cancel():
            if event != 'cancel':
                return None
            if active:
                return ('IDLE', () if f.get('cancel_nostop') else ('stop',),
                        retries if f.get('cancel_keep_retries') else 0)
            if hold:
                if f.get('cancel_hold_ignored'):
                    return (state, (), retries)
                return ('IDLE', ('stop',) if f.get('cancel_hold_stop') else (), 0)
            if state == 'FAULT' and f.get('cancel_clears_fault'):
                return ('IDLE', (), 0)
            return (state, (), retries)

        def watchdog():
            if state in wd_phases and stale and not (f.get('wd_skip_tick') and event == 'tick') \
                    and not (f.get('wd_skip_obs') and event == 'obs'):
                return ('IDLE' if f.get('wd_idle') else 'HOLD_' + state, () if f.get('wd_nostop') else ('stop',),
                        0 if f.get('wd_clears_retries') else retries)
            return None

        def table():
            if state == 'IDLE' and event == 'start':
                if stale and not f.get('start_noguard'):
                    return (state, (), retries)
                return ('APPROACH', ('move_pick',), retries if f.get('start_keep_retries') else 0)
            if state == 'APPROACH' and event == 'reached':
                if f.get('skip_grasp'):
                    return ('TRANSPORT', ('move_drop',), retries)
                return ('GRASP', ('close_gripper',), retries)
            if state == 'GRASP' and event == 'grasped':
                return ('TRANSPORT', () if f.get('grasped_silent') else ('move_drop',), retries)
            if state == 'GRASP' and event == 'grasp_failed':
                limit = max_retries + (1 if f.get('retry_plus1') else 0) - (1 if f.get('retry_minus1') else 0)
                if f.get('retry_forever') or retries < limit:
                    again = 'GRASP' if f.get('retry_regrasp') else 'APPROACH'
                    return (again, (ENTRY[again],), retries if f.get('retry_nocount') else retries + 1)
                return ('FAULT', () if f.get('retry_fault_nostop') else ('stop',), retries)
            if state == 'TRANSPORT' and event == 'reached':
                return ('RELEASE', ('close_gripper',) if f.get('release_wrong') else ('open_gripper',), retries)
            if state == 'RELEASE' and event == 'released':
                return ('IDLE' if f.get('released_idle') else 'DONE', (), retries)
            if hold and event == 'resume':
                ok = (f.get('resume_nofresh') or not stale) and (f.get('resume_nobudget') or retries < max_retries)
                if ok:
                    phase = state[5:]
                    dest = 'APPROACH' if f.get('resume_approach') else phase
                    cmd = () if f.get('resume_nocmd') else (ENTRY[dest],)
                    return (dest, cmd, retries if f.get('resume_nocount') else retries + 1)
                return (state, (), retries)
            if hold and event == 'obs' and f.get('auto_resume') and not stale and retries < max_retries:
                phase = state[5:]
                return (phase, (ENTRY[phase],), retries + 1)
            if state in ('FAULT', 'DONE') and event == 'reset':
                if state == 'DONE' and f.get('reset_fault_only'):
                    return (state, (), retries)
                return ('IDLE', (), retries if f.get('reset_keep') else 0)
            if state == 'DONE' and event == 'start' and f.get('start_from_done'):
                return ('APPROACH', ('move_pick',), 0)
            return (state, (), retries)

        order = f.get('order', ('fault', 'cancel', 'wd'))
        out = None
        for stage in order:
            out = {'fault': fault, 'cancel': cancel, 'wd': watchdog}[stage]()
            if out is not None:
                break
        if out is None:
            out = table()
        if f.get('cmds_str'):
            return (out[0], ','.join(out[1]), out[2])
        if f.get('retries_float'):
            return (out[0], out[1], float(out[2]))
        if f.get('list_shape'):
            return [out[0], list(out[1]), out[2]]
        return out
    return transition


def make_stale(f=None):
    f = f or {}

    def is_stale(age, max_age):
        v_age(age)
        v_cfg(max_age)
        if age is None:
            return not f.get('none_fresh')
        if f.get('ge'):
            return age >= max_age
        if f.get('int_out'):
            return int(age > max_age)
        return age > max_age
    return is_stale


def make_replay(trans, f=None):
    f = f or {}

    def replay(events, max_age, max_retries):
        pairs = v_events(events)
        v_cfg(max_age, max_retries)
        if f.get('mutates'):
            events.sort() if isinstance(events, list) else None
        state, retries, last, prev = 'IDLE', 0, None, None
        states, commands = [], []
        for t, name in pairs:
            before = state
            old_last = last
            if name == 'obs' and not (f.get('obs_ignored_in_hold') and state.startswith('HOLD_')) \
                    and not (f.get('obs_ignored_in_fault') and state == 'FAULT'):
                if not (f.get('first_obs_only') and last is not None):
                    last = t
            use = old_last if f.get('age_before_obs') else last
            age = None if use is None else t - use
            if f.get('age_since_prev'):
                age = None if prev is None else t - prev
            prev = t
            state, cmds, retries = trans(state, name, age, retries, max_age, max_retries)
            if f.get('retries_lost'):
                retries = 0
            states.append(before if f.get('state_before') else state)
            commands.append(list(cmds))
        if f.get('drop_last') and states:
            states.pop()
            commands.pop()
        if f.get('flat'):
            commands = [c for cs in commands for c in cs]
        if f.get('tuples'):
            return tuple(states), tuple(tuple(c) for c in commands)
        return states, commands
    return replay


def make_monitor(f=None):
    f = f or {}

    def monitor(events, commands, max_age):
        pairs = v_events(events)
        v_cfg(max_age)
        v_commands(commands, len(pairs))
        motion = ('move_pick', 'move_drop') if f.get('two_motion') else MOTION
        if f.get('stop_counts'):
            motion = motion + ('stop',)
        last, faulted, cancelled, out = None, False, False, []
        for i, (t, name) in enumerate(pairs):
            if f.get('stale_before_obs'):
                age_last = last
            if name == 'obs':
                last = t
            if name == 'fault':
                faulted = True
            if name == 'reset' and not f.get('reset_after'):
                faulted = False
            if name == 'cancel':
                cancelled = True
            if name == 'start' and not f.get('start_after') and not f.get('never_uncancel'):
                cancelled = False
            use = age_last if f.get('stale_before_obs') else last
            if use is None:
                stale = not f.get('none_fresh')
            else:
                stale = (t - use >= max_age) if f.get('stale_ge') else (t - use > max_age)
            bad = stale
            if not f.get('only_stale'):
                if not f.get('no_event_rule') and name in ('cancel', 'fault'):
                    bad = True
                if faulted and not f.get('no_latch'):
                    bad = True
                if cancelled and not f.get('no_cancelled'):
                    bad = True
            if f.get('no_cancel_rule'):
                bad = stale or (faulted and not f.get('no_latch'))
            if f.get('any_command'):
                hit = len(commands[i]) > 0
            else:
                hit = any(c in motion for c in commands[i])
            if hit and bad:
                out.append(i)
            if name == 'reset' and f.get('reset_after'):
                faulted = False
            if name == 'start' and f.get('start_after') and not f.get('never_uncancel'):
                cancelled = False
        if f.get('first_only'):
            out = out[:1]
        if f.get('one_based'):
            out = [i + 1 for i in out]
        if f.get('descending'):
            out = out[::-1]
        if f.get('count'):
            return len(out)
        if f.get('none_when_empty') and not out:
            return None
        return out
    return monitor


# --- valid alternative formulations ---
# Alt 1: data-driven table of (state, event) -> function; rule priority as an ordered list.
def table_transition(state, event, age, retries, max_age, max_retries):
    v_trans_args(state, event, age, retries, max_age, max_retries)
    fresh = age is not None and age <= max_age
    t = {}
    for phase, cmd in ENTRY.items():
        t[(phase, 'cancel')] = lambda s, r: ('IDLE', ('stop',), 0)
        t[('HOLD_' + phase, 'cancel')] = lambda s, r: ('IDLE', (), 0)
    t[('IDLE', 'start')] = lambda s, r: ('APPROACH', ('move_pick',), 0) if fresh else (s, (), r)
    t[('APPROACH', 'reached')] = lambda s, r: ('GRASP', ('close_gripper',), r)
    t[('GRASP', 'grasped')] = lambda s, r: ('TRANSPORT', ('move_drop',), r)
    t[('GRASP', 'grasp_failed')] = lambda s, r: (('APPROACH', ('move_pick',), r + 1) if r < max_retries
                                                 else ('FAULT', ('stop',), r))
    t[('TRANSPORT', 'reached')] = lambda s, r: ('RELEASE', ('open_gripper',), r)
    t[('RELEASE', 'released')] = lambda s, r: ('DONE', (), r)
    for phase, cmd in ENTRY.items():
        t[('HOLD_' + phase, 'resume')] = (lambda p, c: lambda s, r: (p, (c,), r + 1)
                                          if (fresh and r < max_retries) else (s, (), r))(phase, cmd)
    t[('FAULT', 'reset')] = lambda s, r: ('IDLE', (), 0)
    t[('DONE', 'reset')] = lambda s, r: ('IDLE', (), 0)
    if event == 'fault':
        return ('FAULT', ('stop',) if state in ENTRY else (), retries) if state != 'FAULT' else (state, (), retries)
    if state in ENTRY and not fresh and event != 'cancel':
        return ('HOLD_' + state, ('stop',), retries)
    return t.get((state, event), lambda s, r: (s, (), r))(state, retries)


# Alt 2: one handler per state.
def handler_transition(state, event, age, retries, max_age, max_retries):
    v_trans_args(state, event, age, retries, max_age, max_retries)
    ok = age is not None and not age > max_age

    def stay():
        return [state, [], retries]

    def active(entry_event, nxt, cmd):
        if event == 'fault':
            return ['FAULT', ['stop'], retries]
        if event == 'cancel':
            return ['IDLE', ['stop'], 0]
        if not ok:
            return ['HOLD_' + state, ['stop'], retries]
        if event == entry_event:
            return [nxt, [cmd] if cmd else [], retries]
        return stay()

    def passive():
        if event == 'fault':
            return ['FAULT', [], retries]
        if event == 'cancel' and state.startswith('HOLD_'):
            return ['IDLE', [], 0]
        return stay()

    if state == 'IDLE':
        if event == 'start' and ok:
            return ['APPROACH', ['move_pick'], 0]
        return [state, [], retries] if event not in ('fault',) else ['FAULT', [], retries]
    if state == 'APPROACH':
        return active('reached', 'GRASP', 'close_gripper')
    if state == 'GRASP':
        if event == 'grasp_failed' and ok:
            if event == 'grasp_failed' and retries < max_retries:
                return ['APPROACH', ['move_pick'], retries + 1]
            return ['FAULT', ['stop'], retries]
        return active('grasped', 'TRANSPORT', 'move_drop')
    if state == 'TRANSPORT':
        return active('reached', 'RELEASE', 'open_gripper')
    if state == 'RELEASE':
        return active('released', 'DONE', None)
    if state == 'DONE':
        if event == 'reset':
            return ['IDLE', [], 0]
        return passive()
    if state == 'FAULT':
        if event == 'reset':
            return ['IDLE', [], 0]
        return stay()
    phase = state[5:]
    if event == 'resume' and ok and retries < max_retries:
        return [phase, [ENTRY[phase]], retries + 1]
    return passive()


rule_transition = make_transition()
order_transition = make_transition({'order': ('cancel', 'fault', 'wd')})
list_transition = make_transition({'list_shape': True})


def inline_replay(events, max_age, max_retries):
    """Replay without calling transition(): obs times kept in a list, a flat dispatch."""
    pairs = v_events(events)
    v_cfg(max_age, max_retries)
    obs_times = []
    state, retries = 'IDLE', 0
    states, commands = [], []
    for t, name in pairs:
        if name == 'obs':
            obs_times.append(t)
        fresh = bool(obs_times) and t - obs_times[-1] <= max_age
        out = []
        if name == 'fault' and state != 'FAULT':
            out = ['stop'] if state in ENTRY else []
            state = 'FAULT'
        elif name == 'cancel' and (state in ENTRY or state.startswith('HOLD_')):
            out = ['stop'] if state in ENTRY else []
            state, retries = 'IDLE', 0
        elif state in ENTRY and not fresh and name not in ('fault', 'cancel'):
            out = ['stop']
            state = 'HOLD_' + state
        elif (state, name) == ('IDLE', 'start') and fresh:
            state, retries, out = 'APPROACH', 0, ['move_pick']
        elif (state, name) == ('APPROACH', 'reached'):
            state, out = 'GRASP', ['close_gripper']
        elif (state, name) == ('GRASP', 'grasped'):
            state, out = 'TRANSPORT', ['move_drop']
        elif (state, name) == ('GRASP', 'grasp_failed'):
            if retries < max_retries:
                state, retries, out = 'APPROACH', retries + 1, ['move_pick']
            else:
                state, out = 'FAULT', ['stop']
        elif (state, name) == ('TRANSPORT', 'reached'):
            state, out = 'RELEASE', ['open_gripper']
        elif (state, name) == ('RELEASE', 'released'):
            state = 'DONE'
        elif state.startswith('HOLD_') and name == 'resume' and fresh and retries < max_retries:
            state = state[5:]
            retries += 1
            out = [ENTRY[state]]
        elif state in ('FAULT', 'DONE') and name == 'reset':
            state, retries = 'IDLE', 0
        states.append(state)
        commands.append(tuple(out))
    return tuple(states), tuple(commands)


def scan_monitor(events, commands, max_age):
    """Backward-scan monitor: looks for the latest relevant event at or before each index."""
    pairs = v_events(events)
    v_cfg(max_age)
    v_commands(commands, len(pairs))
    names = [n for _, n in pairs]
    out = []
    for i, (t, name) in enumerate(pairs):
        if not any(c in MOTION for c in commands[i]):
            continue
        obs = [pairs[j][0] for j in range(i + 1) if names[j] == 'obs']
        stale = (not obs) or t - obs[-1] > max_age

        def latest(label):
            for j in range(i, -1, -1):
                if names[j] == label:
                    return j
            return -1
        latched = latest('fault') > latest('reset') if latest('fault') >= 0 else False
        cancelled = latest('cancel') >= 0 and latest('cancel') > latest('start')
        if stale or name in ('cancel', 'fault') or latched or cancelled:
            out.append(i)
    return tuple(out)


def stale_not(age, max_age):
    v_age(age)
    v_cfg(max_age)
    return not (age is not None and age <= max_age)


require(rule_transition and True, 'unreachable')
default_stale, default_monitor = make_stale(), make_monitor()
refs = {'is_stale': default_stale, 'transition': rule_transition,
        'replay': kit._replay_ref, 'unsafe_motion_indices': default_monitor}


FULL = (1, 400, 300)
FAST = (16, 30, 30)


def run_with(over, size=FULL):
    kit._STRIDE, kit._RANDOM, kit._PAIRS = size
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


# ---- the oracle against independent implementations over the whole domain ----
for mr in (0, 2):
    for st in STATES:
        for ev in EVENTS:
            for ag in (None, 0, 1, 2, 3, 4, 5, 6, 9):
                for rt in range(mr + 1):
                    args = (st, ev, ag, rt, 4, mr)
                    want = kit._transition_ref(*args)
                    for fn in (rule_transition, table_transition, handler_transition, order_transition):
                        got = fn(*args)
                        require((got[0], tuple(got[1]), got[2]) == want, 'oracle disagrees with ' + fn.__name__
                                + ' on ' + repr(args))
for case, want in kit._T_CASES:
    require(table_transition(*case) == want, 'hand table disagrees with the data table: ' + repr(case))
traces = [t for _, t in kit._exhaustive_traces()][::4]
for trace in traces + [r[0] for r in kit._random_traces(100, 1515)]:
    for mx, mr in ((2, 1),) if trace in traces else ((2, 0), (3, 1), (2, 2)):
        want = kit._replay_ref(trace, mx, mr)
        got = inline_replay(trace, mx, mr)
        require((list(got[0]), [list(c) for c in got[1]]) == want, 'inline replay disagrees: ' + repr(trace))
        # the safety invariant holds for the reference machine on every trace
        require(kit._unsafe_ref(trace, want[1], mx) == [], 'reference machine violates the invariant: ' + repr(trace))
        require(list(scan_monitor(trace, want[1], mx)) == [], 'scan monitor flags the reference machine')
for args, want in kit._U_CASES:
    require(kit._unsafe_ref(*args) == want == list(scan_monitor(*args)), 'monitor hand table: ' + repr(args))
for args in kit._random_pairs(300, 777):
    require(kit._unsafe_ref(*args) == list(scan_monitor(*args)), 'scan monitor disagrees with the oracle')
for args, want in kit._R_CASES:
    require(kit._replay_ref(*args) == (want[0], want[1]), 'replay hand table: ' + repr(args))
for args, want in kit._STALE_CASES:
    require(kit._stale_ref(*args) == want == stale_not(*args), 'stale hand table: ' + repr(args))

alternatives = [
    ('author: rule chain, reference replay and monitor', {}),
    ('data-driven transition table, inline replay (no transition call), backward-scan monitor',
     {'transition': table_transition, 'replay': inline_replay, 'unsafe_motion_indices': scan_monitor}),
    ('per-state handlers returning lists, tuple-shaped replay output',
     {'transition': handler_transition, 'replay': make_replay(handler_transition, {'tuples': True}),
      'is_stale': stale_not}),
    ('cancel/fault/watchdog checked in another equivalent order, list-shaped transition result',
     {'transition': order_transition, 'replay': make_replay(list_transition)}),
    ('table transition used by a reference replay, scan monitor, negated stale test',
     {'transition': table_transition, 'replay': make_replay(table_transition),
      'unsafe_motion_indices': scan_monitor, 'is_stale': stale_not}),
    ('inline replay only; everything else reference',
     {'replay': inline_replay}),
    ('handler transition with tuple replay and scan monitor',
     {'transition': handler_transition, 'replay': make_replay(handler_transition, {'tuples': True}),
      'unsafe_motion_indices': scan_monitor}),
]
for number, (label, over) in enumerate(alternatives):
    result = run_with(over, FULL if number == 0 else (8, 100, 100))
    require(result == [], 'false reject (' + label + '): ' + str(result[:5]))


# ---- injected bugs ----
def accepts_when(pred, fn, value):
    def run(*a):
        return value if pred(*a) else fn(*a)
    return run


def T(flags):
    return {'transition': make_transition(flags)}


def R(flags=None, tflags=None):
    return {'replay': make_replay(make_transition(tflags), flags)}


def M(flags):
    return {'unsafe_motion_indices': make_monitor(flags)}


def ref(name):
    return refs[name]


mutants = [
    ('transition: age equal to max_age counted as stale', T({'stale_ge': True}), 'transition'),
    ('transition: one extra millisecond of staleness allowed', T({'stale_plus1': True}), 'transition'),
    ('transition: no observation yet counts as fresh', T({'none_fresh': True}), 'transition'),
    ('transition: start accepted without a fresh observation', T({'start_noguard': True}), 'transition'),
    ('transition: watchdog never fires on tick events', T({'wd_skip_tick': True}), 'transition'),
    ('transition: watchdog only guards APPROACH and TRANSPORT', T({'wd_phases': ('APPROACH', 'TRANSPORT')}),
     'transition'),
    ('transition: watchdog only guards motion phases, not RELEASE', T({'wd_phases': ('APPROACH', 'GRASP', 'TRANSPORT')}),
     'transition'),
    ('transition: stale watchdog forgets the stop command', T({'wd_nostop': True}), 'transition'),
    ('transition: stale watchdog drops to IDLE instead of HOLD', T({'wd_idle': True}), 'transition'),
    ('transition: watchdog runs after the normal table only', T({'order': ('fault', 'cancel')}), 'transition'),
    ('transition: watchdog has priority over cancel', T({'order': ('fault', 'wd', 'cancel')}), 'transition'),
    ('transition: watchdog has priority over fault', T({'order': ('wd', 'fault', 'cancel')}), 'transition'),
    ('transition: watchdog clears the retry counter', T({'wd_clears_retries': True}), 'transition'),
    ('transition: cancel emits no stop', T({'cancel_nostop': True}), 'transition'),
    ('transition: cancel keeps the retry counter', T({'cancel_keep_retries': True}), 'transition'),
    ('transition: cancel is ignored in a HOLD state', T({'cancel_hold_ignored': True}), 'transition'),
    ('transition: cancel in a HOLD state emits a second stop', T({'cancel_hold_stop': True}), 'transition'),
    ('transition: cancel clears a latched fault', T({'cancel_clears_fault': True}), 'transition'),
    ('transition: fault emits no stop', T({'fault_nostop': True}), 'transition'),
    ('transition: fault always emits stop, even when already stopped', T({'fault_always_stop': True}),
     'transition'),
    ('transition: fault is ignored in a HOLD state', T({'fault_hold_ignored': True}), 'transition'),
    ('transition: fault returns to IDLE (not latched)', T({'fault_idle': True}), 'transition'),
    ('transition: fault clears the retry counter', T({'fault_clears_retries': True}), 'transition'),
    ('transition: one retry too many', T({'retry_plus1': True}), 'transition'),
    ('transition: one retry too few', T({'retry_minus1': True}), 'transition'),
    ('transition: retries never exhausted', T({'retry_forever': True}), 'transition'),
    ('transition: retry does not count', T({'retry_nocount': True}), 'transition'),
    ('transition: retry skips the approach and closes the gripper again', T({'retry_regrasp': True}),
     'transition'),
    ('transition: exhausted retries fault without stop', T({'retry_fault_nostop': True}), 'transition'),
    ('transition: resume ignores the freshness guard', T({'resume_nofresh': True}), 'transition'),
    ('transition: resume ignores the retry budget', T({'resume_nobudget': True}), 'transition'),
    ('transition: resume does not re-issue the phase command', T({'resume_nocmd': True}), 'transition'),
    ('transition: resume does not count against the budget', T({'resume_nocount': True}), 'transition'),
    ('transition: resume always restarts at APPROACH', T({'resume_approach': True}), 'transition'),
    ('transition: fresh observation resumes a hold automatically', T({'auto_resume': True}), 'transition'),
    ('transition: reset keeps the retry counter', T({'reset_keep': True}), 'transition'),
    ('transition: reset accepted only from FAULT', T({'reset_fault_only': True}), 'transition'),
    ('transition: start accepted again from DONE', T({'start_from_done': True}), 'transition'),
    ('transition: start keeps the old retry counter', T({'start_keep_retries': True}), 'transition'),
    ('transition: approach skips the grasp', T({'skip_grasp': True}), 'transition'),
    ('transition: grasp success emits nothing', T({'grasped_silent': True}), 'transition'),
    ('transition: transport end emits close_gripper', T({'release_wrong': True}), 'transition'),
    ('transition: released goes to IDLE not DONE', T({'released_idle': True}), 'transition'),
    ('transition: commands returned as one string', T({'cmds_str': True}), 'transition'),
    ('transition: retries returned as float', T({'retries_float': True}), 'transition'),
    ('is_stale: age equal to max_age is stale', {'is_stale': make_stale({'ge': True})}, 'is_stale'),
    ('is_stale: no observation counts as fresh', {'is_stale': make_stale({'none_fresh': True})}, 'is_stale'),
    ('is_stale: returns an int, not a bool', {'is_stale': make_stale({'int_out': True})}, 'is_stale'),
    ('is_stale: inverted answer', {'is_stale': lambda a, m: not default_stale(a, m)}, 'is_stale'),
    ('replay: age counted from the first observation only', R({'first_obs_only': True}), 'replay'),
    ('replay: obs events ignored while in a HOLD state', R({'obs_ignored_in_hold': True}), 'replay'),
    ('replay: obs events ignored while in FAULT', R({'obs_ignored_in_fault': True}), 'replay'),
    ('replay: age taken before the obs event refreshes it', R({'age_before_obs': True}), 'replay'),
    ('replay: age measured since the previous event', R({'age_since_prev': True}), 'replay'),
    ('replay: retry counter reset on every event', R({'retries_lost': True}), 'replay'),
    ('replay: reports the state before each event', R({'state_before': True}), 'replay'),
    ('replay: last event dropped', R({'drop_last': True}), 'replay'),
    ('replay: commands flattened into one list', R({'flat': True}), 'replay'),
    ('replay: sorts the caller events in place', R({'mutates': True}), 'replay'),
    ('replay: built on a watchdog that fires one tick late', R(tflags={'stale_plus1': True}), 'replay'),
    ('replay: built on a transition without freshness guard on start', R(tflags={'start_noguard': True}), 'replay'),
    ('replay: built on a machine that auto-resumes', R(tflags={'auto_resume': True}), 'replay'),
    ('replay: empty trace returns None', {'replay': lambda e, a, r: None if len(e) == 0 else ref('replay')(e, a, r)},
     'replay'),
    ('replay: returns commands only', {'replay': lambda e, a, r: ref('replay')(e, a, r)[1]}, 'replay'),
    ('replay: states returned as one joined string', {'replay': lambda e, a, r: (
        ','.join(ref('replay')(e, a, r)[0]), ref('replay')(e, a, r)[1])}, 'replay'),
    ('replay: stop commands missing on watchdog', R(tflags={'wd_nostop': True}), 'replay'),
    ('monitor: only staleness is checked', M({'only_stale': True}), 'unsafe_motion_indices'),
    ('monitor: latched fault ignored', M({'no_latch': True}), 'unsafe_motion_indices'),
    ('monitor: cancelled state ignored after the cancel event', M({'no_cancelled': True}), 'unsafe_motion_indices'),
    ('monitor: cancelled never cleared by start', M({'never_uncancel': True}), 'unsafe_motion_indices'),
    ('monitor: a start at the same index does not clear cancelled', M({'start_after': True}),
     'unsafe_motion_indices'),
    ('monitor: reset at the same index does not clear the latch', M({'reset_after': True}),
     'unsafe_motion_indices'),
    ('monitor: stale test uses >=', M({'stale_ge': True}), 'unsafe_motion_indices'),
    ('monitor: no observation yet counts as fresh', M({'none_fresh': True}), 'unsafe_motion_indices'),
    ('monitor: staleness computed before the obs at this index', M({'stale_before_obs': True}),
     'unsafe_motion_indices'),
    ('monitor: stop counted as a motion command', M({'stop_counts': True}), 'unsafe_motion_indices'),
    ('monitor: only move_* commands count as motion', M({'two_motion': True}), 'unsafe_motion_indices'),
    ('monitor: any command counts as motion', M({'any_command': True}), 'unsafe_motion_indices'),
    ('monitor: only the first violation returned', M({'first_only': True}), 'unsafe_motion_indices'),
    ('monitor: indices are 1-based', M({'one_based': True}), 'unsafe_motion_indices'),
    ('monitor: indices in descending order', M({'descending': True}), 'unsafe_motion_indices'),
    ('monitor: returns the count instead of the indices', M({'count': True}), 'unsafe_motion_indices'),
    ('monitor: returns None when clear', M({'none_when_empty': True}), 'unsafe_motion_indices'),
    ('monitor: cancel rule missing entirely', M({'no_cancel_rule': True}), 'unsafe_motion_indices'),
    ('monitor: sorts the caller commands in place', {'unsafe_motion_indices': lambda e, c, m: (
        ref('unsafe_motion_indices')(e, c, m), c.sort() if isinstance(c, list) else None)[0]},
     'unsafe_motion_indices'),
    ('invalid: bool max_age accepted by is_stale', {'is_stale': accepts_when(
        lambda a, m: m is True, default_stale, False)}, 'is_stale'),
    ('invalid: max_age 0 accepted by is_stale', {'is_stale': accepts_when(
        lambda a, m: m == 0 and type(m) is int, default_stale, True)}, 'is_stale'),
    ('invalid: negative age accepted by is_stale', {'is_stale': accepts_when(
        lambda a, m: type(a) is int and a < 0, default_stale, False)}, 'is_stale'),
    ('invalid: float age accepted by is_stale', {'is_stale': accepts_when(
        lambda a, m: type(a) is float, default_stale, False)}, 'is_stale'),
    ('invalid: lower-case state accepted', {'transition': accepts_when(
        lambda s, *a: type(s) is str and s != s.upper(), rule_transition, ('IDLE', (), 0))}, 'transition'),
    ('invalid: unknown event accepted', {'transition': accepts_when(
        lambda s, e, *a: e == 'go', rule_transition, ('IDLE', (), 0))}, 'transition'),
    ('invalid: bool age accepted', {'transition': accepts_when(
        lambda s, e, a, *r: a is True, rule_transition, ('IDLE', (), 0))}, 'transition'),
    ('invalid: retries above max_retries accepted', {'transition': accepts_when(
        lambda s, e, a, r, m, mr: type(r) is int and r > mr, rule_transition, ('IDLE', (), 0))}, 'transition'),
    ('invalid: bool retries accepted', {'transition': accepts_when(
        lambda s, e, a, r, m, mr: type(r) is bool, rule_transition, ('IDLE', (), 0))}, 'transition'),
    ('invalid: max_retries 6 accepted', {'transition': accepts_when(
        lambda s, e, a, r, m, mr: mr == 6, rule_transition, ('IDLE', (), 0))}, 'transition'),
    ('invalid: max_age 0 accepted by transition', {'transition': accepts_when(
        lambda s, e, a, r, m, mr: m == 0, rule_transition, ('IDLE', (), 0))}, 'transition'),
    ('invalid: decreasing times accepted by replay', {'replay': accepts_when(
        lambda ev, m, r: isinstance(ev, (list, tuple)) and any(
            ev[i][0] > ev[i + 1][0] for i in range(len(ev) - 1)), refs['replay'], ([], []))}, 'replay'),
    ('invalid: unknown event name accepted by replay', {'replay': accepts_when(
        lambda ev, m, r: isinstance(ev, (list, tuple)) and any(
            isinstance(p, (list, tuple)) and len(p) == 2 and p[1] == 'go' for p in ev), refs['replay'], ([], []))},
     'replay'),
    ('invalid: bool time accepted by replay', {'replay': accepts_when(
        lambda ev, m, r: isinstance(ev, (list, tuple)) and any(
            isinstance(p, (list, tuple)) and len(p) == 2 and type(p[0]) is bool for p in ev),
        refs['replay'], ([], []))}, 'replay'),
    ('invalid: float time accepted by replay', {'replay': accepts_when(
        lambda ev, m, r: isinstance(ev, (list, tuple)) and any(
            isinstance(p, (list, tuple)) and len(p) == 2 and type(p[0]) is float for p in ev),
        refs['replay'], ([], []))}, 'replay'),
    ('invalid: 201 events accepted by replay', {'replay': accepts_when(
        lambda ev, m, r: isinstance(ev, (list, tuple)) and len(ev) > 200, refs['replay'], ([], []))}, 'replay'),
    ('invalid: max_retries above 5 accepted by replay', {'replay': accepts_when(
        lambda ev, m, r: r == 6, refs['replay'], ([], []))}, 'replay'),
    ('invalid: bool max_age accepted by replay', {'replay': accepts_when(
        lambda ev, m, r: m is True, refs['replay'], ([], []))}, 'replay'),
    ('invalid: mismatched command count accepted by monitor', {'unsafe_motion_indices': accepts_when(
        lambda e, c, m: isinstance(c, (list, tuple)) and isinstance(e, (list, tuple)) and len(c) != len(e),
        default_monitor, [])}, 'unsafe_motion_indices'),
    ('invalid: unknown command name accepted by monitor', {'unsafe_motion_indices': accepts_when(
        lambda e, c, m: isinstance(c, (list, tuple)) and any(isinstance(x, (list, tuple)) and 'fly' in x for x in c),
        default_monitor, [])}, 'unsafe_motion_indices'),
    ('invalid: command entry given as a string accepted by monitor', {'unsafe_motion_indices': accepts_when(
        lambda e, c, m: isinstance(c, (list, tuple)) and any(isinstance(x, str) for x in c),
        default_monitor, [])}, 'unsafe_motion_indices'),
    ('invalid: max_age 0 accepted by monitor', {'unsafe_motion_indices': accepts_when(
        lambda e, c, m: m == 0 and type(m) is int, default_monitor, [])}, 'unsafe_motion_indices'),
    ('starter-style: transition raises NotImplementedError on some inputs only', {'transition': (
        lambda *a: (_ for _ in ()).throw(NotImplementedError()) if a[0] == 'RELEASE' else rule_transition(*a))},
     'transition'),
]
unique = {m[0] for m in mutants}
require(len(unique) == len(mutants), 'duplicate mutant labels')
results = {}
for label, over, target in mutants:
    fast = run_with(over, FAST)
    # a mutant the reduced sweep misses, or rejects for another reason, is rerun at full strength
    ok = any(target in line for line in fast)
    results[label] = fast if ok else run_with(over)
accepted = [label for label, result in results.items() if not result]
require(not accepted, 'false accepts: ' + str(accepted))
for label, over, target in mutants:
    result = results[label]
    require(any(target in line for line in result),
            'mutant rejected for the wrong function (' + label + '): ' + str(result[:3]))
    require(all(line.isascii() for line in result), 'non-ASCII failure line for ' + label)
    leaked = [line for line in result if 'expected' in line.lower()]
    require(not leaked, 'failure line mentions expected values: ' + str(leaked[:1]))
require(len(mutants) >= 30, 'need at least 30 named mutants')
print('Executive kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
