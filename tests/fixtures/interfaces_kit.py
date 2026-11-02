"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different formulations, including a float
slab test, a Cohen-Sutherland test and other subdivisions) that must pass, and named
injected bugs that must be rejected for their intended reason. Plain checks only, so it
also works under python -O.
"""
import ast
import importlib.util
import json
import math
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('interfaces_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L14-interfaces.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names}
imported |= {node.module.split('.')[0] for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom) and node.module}
require(imported <= {'math', 'fractions'}, 'kit imports beyond math/fractions: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
names = ('lifecycle_next', 'write_cycle', 'validate_trajectory', 'action_run', 'segment_free')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _write_ref') > spoiler and text.index('def _free_ref') > spoiler
        and text.index('_W_CASES =') > spoiler, 'oracle and tables must sit below the banner')
spec = importlib.util.spec_from_file_location('interfaces_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check([])
require(starter and len(starter) == 5 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented function into one line: ' + str(starter))
require(all(f.isascii() for f in starter), 'starter messages must be ASCII')
require('mock' in text[:900].lower() and 'MOCK' in text[:900], 'docstring must say MOCK up front')

LIFE, REQ, REASONS = kit.LIFECYCLES, kit.REQUESTS, kit.REASONS
EV = kit.ACTION_EVENTS

# ---- samples manifest mirrors the selected positive cases ----


def enc(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [enc(v) for v in value]
    if type(value) is int:
        return str(value)
    if type(value) is float:
        return repr(value)
    return value


def entry(structure, keys, args):
    return {'structure': structure, 'inputs': {k: enc(v) for k, v in zip(keys, args)}}


L_PICK = (0, 1, 2, 3, 7, 8, 11)
W_PICK = (0, 1, 2, 3, 5, 7, 10, 11, 14, 15, 16)
V_PICK = (0, 1, 2, 6, 7, 9, 11, 14, 18, 22, 23, 29)
A_PICK = (1, 2, 4, 5, 6, 11, 12, 13)
S_PICK = (0, 1, 4, 8, 9, 17, 18, 20, 21, 22, 24)
expected = (
    [entry('interfaces.lifecycle@1', ('state', 'request'), kit._L_CASES[i][0]) for i in L_PICK]
    + [entry('interfaces.write-cycle@1', ('lifecycle', 'position', 'command', 'dt', 'lower', 'upper',
                                          'max_velocity'), kit._W_CASES[i][0]) for i in W_PICK]
    + [entry('interfaces.trajectory@1', ('joint_names', 'points', 'interface_names', 'current', 'lower', 'upper',
                                         'max_velocity', 'start_tol'), kit._V_CASES[i][0]) for i in V_PICK]
    + [entry('interfaces.action@1', ('events', 'timeout'), kit._A_CASES[i][0]) for i in A_PICK]
    + [entry('interfaces.scene@1', ('q_start', 'q_end', 'l1', 'l2', 'box'), kit._S_CASES[i][0]) for i in S_PICK])
require(len(expected) <= 50, 'kit sample cap is 50: ' + str(len(expected)))
samples = json.loads((root / 'content/labs/L14-interfaces.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1', 'samples schema')
require(list(samples['kits']) == ['L14-interfaces'], 'samples must hold only L14-interfaces')
require(samples['kits']['L14-interfaces'] == expected, 'samples manifest does not mirror the self-check cases')

# ---- independent implementations (parametrised by bug flags) ----


def isnum(v, b):
    return type(v) in (int, float) and math.isfinite(v) and abs(v) <= b


def pair(v, b=100):
    return isinstance(v, (list, tuple)) and len(v) == 2 and all(isnum(x, b) for x in v)


def v_limits(lo, hi, vm):
    if not (pair(lo) and pair(hi) and pair(vm)):
        raise ValueError
    for j in range(2):
        if not (lo[j] < hi[j] and vm[j] > 0):
            raise ValueError


# --- lifecycle ---
def make_lifecycle(f=None):
    f = f or {}

    def fn(state, request):
        if type(state) is not str or state not in LIFE or type(request) is not str or request not in REQ:
            raise ValueError
        out = None
        if state == 'unconfigured' and request == 'configure':
            out = 'inactive'
        elif state == 'inactive' and request == 'activate':
            out = 'active'
        elif state == 'active' and request == 'deactivate':
            out = 'unconfigured' if f.get('deactivate_unconfig') else 'inactive'
        elif state == 'inactive' and request == 'cleanup':
            out = 'unconfigured'
        elif request == 'shutdown' and state != 'finalized':
            if not (f.get('no_shutdown_active') and state == 'active'):
                out = 'finalized'
        elif f.get('skip_configure') and state == 'unconfigured' and request == 'activate':
            out = 'active'
        elif f.get('reopen') and state == 'finalized' and request == 'configure':
            out = 'inactive'
        if out is None:
            ok = 1 if f.get('bad_ok') else bool(f.get('accept_refused'))
            return (state, ok)
        return (out, 1 if f.get('int_flag') else True)
    return fn


def table_lifecycle(state, request):
    if type(state) is not str or state not in LIFE or type(request) is not str or request not in REQ:
        raise ValueError
    allowed = {'unconfigured': {'configure': 'inactive', 'shutdown': 'finalized'},
               'inactive': {'activate': 'active', 'cleanup': 'unconfigured', 'shutdown': 'finalized'},
               'active': {'deactivate': 'inactive', 'shutdown': 'finalized'}, 'finalized': {}}
    nxt = allowed[state].get(request)
    return [nxt if nxt else state, nxt is not None]


# --- write_cycle ---
def make_write(f=None):
    f = f or {}

    def fn(lifecycle, position, command, dt, lower, upper, max_velocity):
        if type(lifecycle) is not str or lifecycle not in LIFE or not pair(position) or not pair(command):
            raise ValueError
        if not (isnum(dt, 1) and dt > 0):
            raise ValueError
        v_limits(lower, upper, max_velocity)
        if any(not (lower[j] <= position[j] <= upper[j]) for j in range(2)):
            raise ValueError
        hold = ([float(position[0]), float(position[1])], [0.0, 0.0])
        cmd = list(command)
        if f.get('limit_first') and any(not lower[j] <= cmd[j] <= upper[j] for j in range(2)):
            return hold + ('rejected-position-limit',)
        if lifecycle != 'active' and not f.get('inactive_moves'):
            return hold + ('rejected-not-active',)
        joints = (0,) if f.get('only_j0_limit') else (0, 1)
        if f.get('exclusive_limit'):
            bad = any(not lower[j] < cmd[j] < upper[j] for j in joints)
        else:
            bad = any(not lower[j] <= cmd[j] <= upper[j] for j in joints)
        if f.get('clamp'):
            cmd = [min(max(cmd[j], lower[j]), upper[j]) for j in range(2)]
            bad = False
        if f.get('partial') and any(not lower[j] <= cmd[j] <= upper[j] for j in range(2)):
            cmd = [cmd[j] if lower[j] <= cmd[j] <= upper[j] else position[j] for j in range(2)]
            bad = False
        if bad:
            if f.get('moving_velocity'):
                return hold[0], [(cmd[j] - position[j]) / dt for j in range(2)], 'rejected-position-limit'
            return hold + ('rejected-position-limit',)
        steps = [max_velocity[j] * (1 if f.get('no_dt') else dt) for j in range(2)]
        if f.get('same_vmax'):
            steps = [steps[0], steps[0]]
        gaps = [cmd[j] - position[j] for j in range(2)]
        new, limited = [], False
        scale = 1.0
        if f.get('vector_scale'):
            scale = min([1.0] + [steps[j] / abs(gaps[j]) for j in range(2) if abs(gaps[j]) > steps[j]])
        for j in range(2):
            tie = 0.0 if f.get('strict_tie') else (1e-3 if f.get('tie_big') else 1e-9)
            if f.get('vector_scale'):
                new.append(position[j] + gaps[j] * scale)
                limited = limited or scale < 1.0
            elif f.get('no_limit') or ((abs(gaps[j]) < steps[j] + tie) if f.get('strict_tie') else (abs(gaps[j]) <= steps[j] + tie)):
                new.append(float(cmd[j]))
            else:
                limited = True
                sign = 1.0 if (f.get('abs_sign') or gaps[j] > 0) else -1.0
                new.append(position[j] + sign * steps[j])
        if f.get('cmd_velocity'):
            vel = [(cmd[j] - position[j]) / dt for j in range(2)]
        else:
            vel = [(new[j] - position[j]) / dt for j in range(2)]
        if f.get('round_vel'):
            vel = [round(v, 6) for v in vel]
        status = 'rate-limited' if limited and not f.get('always_ok') else 'ok'
        return [float(v) for v in new], vel, status
    return fn


def vector_write(lifecycle, position, command, dt, lower, upper, max_velocity):
    """Alternative: clamp the gap with min/max, derive the status from the clamped gap."""
    if type(lifecycle) is not str or lifecycle not in LIFE or not pair(position) or not pair(command):
        raise ValueError
    if not (isnum(dt, 1) and dt > 0):
        raise ValueError
    v_limits(lower, upper, max_velocity)
    if any(not (lower[j] <= position[j] <= upper[j]) for j in range(2)):
        raise ValueError
    if lifecycle != 'active':
        return list(map(float, position)), [0.0, 0.0], 'rejected-not-active'
    if not all(lower[j] <= command[j] <= upper[j] for j in range(2)):
        return list(map(float, position)), [0.0, 0.0], 'rejected-position-limit'
    gap = [command[j] - position[j] for j in range(2)]
    cap = [max_velocity[j] * dt for j in range(2)]
    step = [max(-cap[j], min(cap[j], gap[j])) for j in range(2)]
    new = [command[j] if abs(gap[j]) <= cap[j] + 1e-9 else position[j] + step[j] for j in range(2)]
    cut = any(abs(gap[j]) > cap[j] + 1e-9 for j in range(2))
    return new, [(new[j] - position[j]) / dt for j in range(2)], ('rate-limited' if cut else 'ok')


# --- validate_trajectory ---
def make_traj(f=None):
    f = f or {}

    def fn(names, points, iface, current, lower, upper, vmax, tol):
        if not (isinstance(iface, (list, tuple)) and len(iface) == 2
                and all(type(n) is str and n and n.isascii() for n in iface) and iface[0] != iface[1]):
            raise ValueError
        if not (isinstance(names, (list, tuple)) and len(names) <= 6
                and all(type(n) is str and n for n in names)):
            raise ValueError
        if not (isinstance(points, (list, tuple)) and len(points) <= 50):
            raise ValueError
        for p in points:
            if not (isinstance(p, (list, tuple)) and len(p) == 2 and isnum(p[0], 1000) and p[0] >= 0
                    and isinstance(p[1], (list, tuple)) and len(p[1]) <= 6 and all(isnum(v, 100) for v in p[1])):
                raise ValueError
        if not pair(current):
            raise ValueError
        v_limits(lower, upper, vmax)
        if not (isnum(tol, 1) and tol >= 0):
            raise ValueError
        found = set()
        if not points:
            if not f.get('accept_empty'):
                found.add('empty-trajectory')
        if tuple(names) != tuple(iface):
            same = sorted(names) == sorted(iface) and len(names) == 2
            if f.get('set_names') and sorted(names) == sorted(iface):
                pass
            elif same and not f.get('order_as_names'):
                found.add('joint-order-mismatch')
            else:
                found.add('joint-names-mismatch')
        if points:
            if any(len(p[1]) != 2 for p in points):
                found.add('positions-length-mismatch')
            ts = [p[0] for p in points]
            rng = range(len(ts) - 1) if not f.get('first_pair_time') else range(min(1, len(ts) - 1))
            if any((ts[i + 1] < ts[i]) if f.get('equal_time_ok') else (ts[i + 1] <= ts[i]) for i in rng):
                found.add('time-not-increasing')
            if all(len(p[1]) == 2 for p in points):
                js = (0,) if f.get('pos_j0') else (0, 1)
                for p in points:
                    for j in js:
                        lo, hi = lower[j] - 1e-9, upper[j] + 1e-9
                        if f.get('pos_exclusive'):
                            outside = not (lower[j] < p[1][j] < upper[j])
                        else:
                            outside = not (lo <= p[1][j] <= hi)
                        if outside:
                            found.add('position-limit')
                last = len(points) - 1 if not f.get('skip_last_segment') else len(points) - 2
                for i in range(last):
                    dt = ts[i + 1] - ts[i]
                    if dt <= 0:
                        continue
                    for j in range(2):
                        dq = abs(points[i + 1][1][j] - points[i][1][j])
                        lim = (vmax[0] if f.get('same_vmax') else vmax[j]) * (1 if f.get('no_dt') else dt)
                        if dq > lim + 1e-9:
                            found.add('velocity-limit')
                ref = (0.0, 0.0) if f.get('start_zero') else current
                for j in (0,) if f.get('start_j0') else (0, 1):
                    d = abs(points[0][1][j] - ref[j])
                    if (d >= tol) if f.get('tol_strict') else (d > tol + 1e-9):
                        found.add('start-state-mismatch')
            elif f.get('crash_on_width'):
                points[0][1][1]
        out = [r for r in REASONS if r in found]
        if f.get('reverse'):
            out.reverse()
        if f.get('first_only'):
            out = out[:1]
        if f.get('duplicate') and 'velocity-limit' in out:
            out.append('velocity-limit')
        return out
    return fn


def check_list_traj(names, points, iface, current, lower, upper, vmax, tol):
    """Alternative: an ordered list of (reason, predicate) pairs on the validated inputs."""
    ref = kit._trajectory_ref
    ref(names, points, iface, current, lower, upper, vmax, tol)  # validation only, errors propagate
    pts = list(points)
    ok_width = all(len(p[1]) == 2 for p in pts)
    ts = [p[0] for p in pts]
    checks = [
        ('empty-trajectory', lambda: not pts),
        ('joint-names-mismatch', lambda: list(names) != list(iface) and not (
            len(names) == 2 and set(names) == set(iface) and names[0] != names[1])),
        ('joint-order-mismatch', lambda: list(names) != list(iface) and len(names) == 2
         and set(names) == set(iface) and names[0] != names[1]),
        ('positions-length-mismatch', lambda: bool(pts) and not ok_width),
        ('time-not-increasing', lambda: any(b <= a for a, b in zip(ts, ts[1:]))),
        ('position-limit', lambda: ok_width and any(
            q[j] < lower[j] - 1e-9 or q[j] > upper[j] + 1e-9 for _, q in pts for j in range(2))),
        ('velocity-limit', lambda: ok_width and any(
            abs(q2[j] - q1[j]) > vmax[j] * (t2 - t1) + 1e-9
            for (t1, q1), (t2, q2) in zip(pts, pts[1:]) if t2 > t1 for j in range(2))),
        ('start-state-mismatch', lambda: ok_width and bool(pts) and any(
            abs(pts[0][1][j] - current[j]) > tol + 1e-9 for j in range(2))),
    ]
    return [name for name, pred in checks if pred()]


# --- action client ---
def make_action(f=None):
    f = f or {}

    def fn(events, timeout):
        evs = kit._events_ref(events)
        if not (type(timeout) is int and 1 <= timeout <= 100000):
            raise ValueError
        state, progress, t_goal, prev_t = 'idle', 0.0, None, None
        states, progs = [], []
        first_t = evs[0][0] if evs else 0
        for t, name, value in evs:
            term = state in kit._TERMINAL
            if f.get('open_terminal') and term and name == 'result_ok' and state == 'aborted':
                state = 'succeeded'
                term = True
                states.append(state)
                progs.append(progress)
                prev_t = t
                continue
            if term:
                pass
            else:
                base = t_goal
                if f.get('from_prev') and prev_t is not None:
                    base = prev_t
                if f.get('from_first'):
                    base = first_t
                late = (state in ('pending', 'executing', 'canceling') and base is not None
                        and ((t - base >= timeout) if f.get('timeout_ge') else (t - base > timeout)))
                if late and not f.get('late_applies'):
                    state = 'timed-out'
                else:
                    if late:
                        pending_late = True
                    if state == 'idle' and name == 'send_goal':
                        state, t_goal = 'pending', t
                    elif state == 'idle' and name == 'accept' and f.get('accept_idle'):
                        state = 'executing'
                    elif state == 'pending' and name == 'send_goal' and f.get('resend'):
                        t_goal = t
                    elif state == 'pending' and name == 'accept':
                        state = 'executing'
                    elif state == 'pending' and name == 'reject':
                        state = 'aborted' if f.get('reject_aborted') else 'rejected'
                    elif name == 'cancel_request' and (state == 'executing' or (
                            state == 'pending' and not f.get('no_pending_cancel'))):
                        state = 'canceling'
                    elif state == 'canceling' and name == 'cancel_done':
                        state = 'canceled'
                    elif state in ('executing', 'canceling') and name == 'result_ok':
                        if f.get('cancel_wins') and state == 'canceling':
                            state = 'canceled'
                        else:
                            state = 'succeeded'
                            progress = progress if f.get('keep_progress') else 1.0
                    elif state in ('executing', 'canceling') and name == 'result_abort':
                        state = 'aborted'
                    elif name == 'feedback' and (state in ('executing', 'canceling')
                                                 or (state == 'pending' and f.get('fb_pending'))):
                        if f.get('fb_any') or value >= progress:
                            progress = float(value)
                        if f.get('fb_finishes') and value >= 1.0:
                            state = 'succeeded'
            if f.get('reset_progress') and name != 'feedback' and state == 'executing':
                progress = 0.0
            states.append(state)
            progs.append(progress)
            prev_t = t
        return states, progs
    return fn


def table_action(events, timeout):
    """Alternative: transition table keyed by (state, event), timeout checked first."""
    evs = kit._events_ref(events)
    if not (type(timeout) is int and 1 <= timeout <= 100000):
        raise ValueError
    table = {('idle', 'send_goal'): 'pending', ('pending', 'accept'): 'executing',
             ('pending', 'reject'): 'rejected', ('pending', 'cancel_request'): 'canceling',
             ('executing', 'cancel_request'): 'canceling', ('canceling', 'cancel_done'): 'canceled',
             ('executing', 'result_ok'): 'succeeded', ('canceling', 'result_ok'): 'succeeded',
             ('executing', 'result_abort'): 'aborted', ('canceling', 'result_abort'): 'aborted'}
    live = ('pending', 'executing', 'canceling')
    cur, prog, start = 'idle', 0.0, 0
    out_s, out_p = [], []
    for t, name, value in evs:
        if cur in live and t - start > timeout:
            cur = 'timed-out'
        elif (cur, name) in table:
            if (cur, name) == ('idle', 'send_goal'):
                start = t
            cur = table[(cur, name)]
            if name == 'result_ok':
                prog = 1.0
        elif name == 'feedback' and cur in ('executing', 'canceling'):
            prog = max(prog, float(value))
        out_s.append(cur)
        out_p.append(prog)
    return tuple(out_s), tuple(out_p)


# --- segment_free ---
def v_scene(qs, qe, l1, l2, box):
    if not (pair(qs, 10) and pair(qe, 10)):
        raise ValueError
    if not (isnum(l1, 10) and l1 > 0 and isnum(l2, 10) and l2 > 0):
        raise ValueError
    if not (isinstance(box, (list, tuple)) and len(box) == 4 and all(isnum(v, 100) for v in box)
            and box[0] <= box[2] and box[1] <= box[3]):
        raise ValueError


def slab(p, q, r, strict=False):
    t0, t1 = 0.0, 1.0
    for a, b, lo, hi in ((p[0], q[0], r[0], r[2]), (p[1], q[1], r[1], r[3])):
        d = b - a
        if d == 0.0:
            if a < lo or a > hi or (strict and (a <= lo or a >= hi)):
                return False
            continue
        ta, tb = (lo - a) / d, (hi - a) / d
        if ta > tb:
            ta, tb = tb, ta
        t0, t1 = max(t0, ta), min(t1, tb)
        if t0 > t1 or (strict and t0 >= t1):
            return False
    return True


def out_code(x, y, r):
    return (1 if x < r[0] else 2 if x > r[2] else 0) | (4 if y < r[1] else 8 if y > r[3] else 0)


def cohen(p, q, r):
    (x0, y0), (x1, y1) = p, q
    c0, c1 = out_code(x0, y0, r), out_code(x1, y1, r)
    for _ in range(12):
        if not (c0 | c1):
            return True
        if c0 & c1:
            return False
        c = c0 or c1
        if c & 8:
            x, y = x0 + (x1 - x0) * (r[3] - y0) / (y1 - y0), r[3]
        elif c & 4:
            x, y = x0 + (x1 - x0) * (r[1] - y0) / (y1 - y0), r[1]
        elif c & 2:
            x, y = r[2], y0 + (y1 - y0) * (r[2] - x0) / (x1 - x0)
        else:
            x, y = r[0], y0 + (y1 - y0) * (r[0] - x0) / (x1 - x0)
        if c == c0:
            x0, y0, c0 = x, y, out_code(x, y, r)
        else:
            x1, y1, c1 = x, y, out_code(x, y, r)
    return True


def make_scene(f=None, steps=200, hit=slab):
    f = f or {}

    def fn(qs, qe, l1, l2, box):
        v_scene(qs, qe, l1, l2, box)
        n = f.get('steps', steps)
        ks = [0, n] if f.get('ends_only') else range(n + 1)
        if f.get('skip_last'):
            ks = range(n)
        if f.get('skip_first'):
            ks = range(1, n + 1)
        if f.get('skip_both'):
            ks = range(1, n)
        b = (box[1], box[0], box[3], box[2]) if f.get('swap_xy') else tuple(box)
        if f.get('inflate'):
            b = (b[0] - 1e-3, b[1] - 1e-3, b[2] + 1e-3, b[3] + 1e-3)
        for k in ks:
            s = k / n
            if f.get('cartesian'):
                a0 = (l1 * math.cos(qs[0]) + l2 * math.cos(qs[0] + qs[1]), l1 * math.sin(qs[0]) + l2 * math.sin(qs[0] + qs[1]))
                a1 = (l1 * math.cos(qe[0]) + l2 * math.cos(qe[0] + qe[1]), l1 * math.sin(qe[0]) + l2 * math.sin(qe[0] + qe[1]))
                tx, ty = a0[0] + s * (a1[0] - a0[0]), a0[1] + s * (a1[1] - a0[1])
                if b[0] <= tx <= b[2] and b[1] <= ty <= b[3]:
                    return False
                continue
            a1_, a2_ = qs[0] + s * (qe[0] - qs[0]), qs[1] + s * (qe[1] - qs[1])
            if f.get('shortest'):
                d1 = (qe[0] - qs[0] + math.pi) % (2 * math.pi) - math.pi
                a1_ = qs[0] + s * d1
            ex, ey = l1 * math.cos(a1_), l1 * math.sin(a1_)
            ang = a2_ if f.get('absolute_q2') else a1_ + a2_
            tx, ty = ex + l2 * math.cos(ang), ey + l2 * math.sin(ang)
            if f.get('tip_only'):
                if b[0] <= tx <= b[2] and b[1] <= ty <= b[3]:
                    return False
                continue
            if f.get('points_only'):
                for x, y in ((ex, ey), (tx, ty)):
                    if b[0] <= x <= b[2] and b[1] <= y <= b[3]:
                        return False
                continue
            if f.get('elbow_only'):
                if b[0] <= ex <= b[2] and b[1] <= ey <= b[3]:
                    return False
                continue
            if f.get('bbox'):
                for p, q in (((0.0, 0.0), (ex, ey)), ((ex, ey), (tx, ty))):
                    if not (max(p[0], q[0]) < b[0] or min(p[0], q[0]) > b[2]
                            or max(p[1], q[1]) < b[1] or min(p[1], q[1]) > b[3]):
                        return False
                continue
            h = (lambda p, q, r: slab(p, q, r, True)) if f.get('open_box') else hit
            if (not f.get('skip_link1') and h((0.0, 0.0), (ex, ey), b)) or h((ex, ey), (tx, ty), b):
                return False
        return True
    return fn


def exact_scene(steps):
    def fn(qs, qe, l1, l2, box):
        v_scene(qs, qe, l1, l2, box)
        return kit._free_ref(qs, qe, l1, l2, box, steps)
    return fn


# ---- harness ----
refs = {'lifecycle_next': kit._lifecycle_ref, 'write_cycle': kit._write_ref,
        'validate_trajectory': kit._trajectory_ref, 'action_run': kit._action_ref,
        'segment_free': kit._free_ref}
FULL = [1, 300, 400, 150]
FAST = [1, 80, 120, 60]


def run_with(over, size=FULL):
    kit._FAST[:] = size
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


# ---- oracle against independent implementations ----
for a, w in kit._L_CASES:
    require(kit._lifecycle_ref(*a) == w == tuple(table_lifecycle(*a)), 'lifecycle hand table: ' + repr(a))
life_fn = make_lifecycle()
for s in LIFE:
    for r in REQ:
        require(tuple(life_fn(s, r)) == kit._lifecycle_ref(s, r) == tuple(table_lifecycle(s, r)),
                'lifecycle oracle disagreement ' + s + r)
write_fn = make_write()
for a, w in kit._W_CASES:
    for fn in (kit._write_ref, write_fn, vector_write):
        got = fn(*a)
        require(got[2] == w[2] and all(abs(x - y) < 1e-9 for x, y in zip(list(got[0]) + list(got[1]), w[0] + w[1])),
                'write hand table disagrees with ' + getattr(fn, '__name__', 'write') + ' on ' + repr(a))
for a in kit._write_cases(600, 99):
    want = kit._write_ref(*a)
    for fn in (write_fn, vector_write):
        got = fn(*a)
        require(got[2] == want[2] and all(abs(x - y) < 1e-9 for x, y in zip(list(got[0]) + list(got[1]),
                                                                           want[0] + want[1])),
                'write oracle disagreement on ' + repr(a))
traj_fn = make_traj()
for a, w in kit._V_CASES:
    for fn in (kit._trajectory_ref, traj_fn, check_list_traj):
        require(list(fn(*a)) == w, 'trajectory hand table disagrees with ' + fn.__name__ + ' on ' + repr(a))
for a in kit._trajectory_cases(800, 123):
    want = kit._trajectory_ref(*a)
    require(list(traj_fn(*a)) == want == list(check_list_traj(*a)), 'trajectory oracle disagreement on ' + repr(a))
act_fn = make_action()
for a, w in kit._A_CASES:
    for fn in (kit._action_ref, act_fn, table_action):
        got = fn(*a)
        require((list(got[0]), list(got[1])) == (w[0], w[1]), 'action hand table disagrees with '
                + getattr(fn, '__name__', 'action') + ' on ' + repr(a))
for a in kit._action_cases(300, 321):
    want = kit._action_ref(*a)
    for fn in (act_fn, table_action):
        got = fn(*a)
        require((list(got[0]), list(got[1])) == want, 'action oracle disagreement ' + repr(a))
cases_scene = kit._scene_cases(150, 7474)
require(len(cases_scene) == 150, 'scene case generator must yield 150 cases')
require(10 <= sum(1 for a in cases_scene if not kit._free_ref(*a)) <= 80, 'scene sweep must mix blocked and free')
for a, w in kit._S_CASES + [(c, kit._free_ref(*c)) for c in cases_scene]:
    require(kit._free_ref(*a) == w, 'exact reference disagrees with its table: ' + repr(a))
    for steps in (100, 137, 400, 1000):
        require(kit._free_ref(*a, steps=steps) == w if steps != 1000 or a in [c for c, _ in kit._S_CASES] else True,
                'subdivision band violated at ' + str(steps) + ' for ' + repr(a))
    for fn in (make_scene(steps=100), make_scene(steps=400, hit=cohen), make_scene(steps=200)):
        require(fn(*a) == w, 'float/cohen alternatives disagree with exact on ' + repr(a))

alternatives = [
    ('author: reference implementations', {}),
    ('if-chain lifecycle, vectorised clamp write_cycle, check-list validator, table action client, '
     'float slab scene at 100 steps',
     {'lifecycle_next': life_fn, 'write_cycle': vector_write, 'validate_trajectory': check_list_traj,
      'action_run': table_action, 'segment_free': make_scene(steps=100)}),
    ('dict lifecycle returning lists, per-joint write, flag validator, reference action, exact scene at 400 steps',
     {'lifecycle_next': table_lifecycle, 'write_cycle': write_fn, 'validate_trajectory': traj_fn,
      'segment_free': exact_scene(400)}),
    ('table action and Cohen-Sutherland scene at 200 steps, reference elsewhere',
     {'action_run': table_action, 'segment_free': make_scene(steps=200, hit=cohen)}),
    ('float slab scene at 1000 steps with flag-based action client',
     {'segment_free': make_scene(steps=1000), 'action_run': act_fn}),
    ('check-list validator and vectorised write_cycle only', {'validate_trajectory': check_list_traj,
                                                              'write_cycle': vector_write}),
    ('exact scene at 137 steps (odd subdivision) with table lifecycle',
     {'segment_free': exact_scene(137), 'lifecycle_next': table_lifecycle}),
]
for number, (label, over) in enumerate(alternatives):
    result = run_with(over, FULL if number == 0 else FAST)
    require(result == [], 'false reject (' + label + '): ' + str(result[:5]))


# ---- injected bugs ----
def L(flags):
    return {'lifecycle_next': make_lifecycle(flags)}


def W(flags):
    return {'write_cycle': make_write(flags)}


def V(flags):
    return {'validate_trajectory': make_traj(flags)}


def A(flags):
    return {'action_run': make_action(flags)}


def S(flags, **kw):
    return {'segment_free': make_scene(flags, **kw)}


def mutates_events(events, timeout):
    if isinstance(events, list):
        events.sort(key=lambda e: e[0])
        events.append(events[0] if events else None)
        events.pop()
        if events:
            events[0] = tuple(events[0])
    return kit._action_ref(events, timeout)


def mutates_points(*args):
    points = args[1]
    if isinstance(points, list):
        points.append(None)
        points.pop()
        points.sort(key=lambda p: p[0], reverse=True)
        points.sort(key=lambda p: p[0])
        points.insert(0, points[0] if points else None)
        points.pop(0)
        if points:
            points[0] = list(points[0])
    return kit._trajectory_ref(*args)


mutants = [
    ('lifecycle: activate allowed straight from unconfigured', L({'skip_configure': True}), 'lifecycle_next', ''),
    ('lifecycle: shutdown refused while active', L({'no_shutdown_active': True}), 'lifecycle_next', ''),
    ('lifecycle: finalized can be configured again', L({'reopen': True}), 'lifecycle_next', ''),
    ('lifecycle: deactivate goes back to unconfigured', L({'deactivate_unconfig': True}), 'lifecycle_next', ''),
    ('lifecycle: refused requests still report accepted', L({'accept_refused': True}), 'lifecycle_next', 'accepted'),
    ('lifecycle: accepted returned as int 1', L({'int_flag': True}), 'lifecycle_next', 'bool'),
    ('write: command executed while not active', W({'inactive_moves': True}), 'write_cycle', ''),
    ('write: out-of-limit command clamped instead of refused', W({'clamp': True}), 'write_cycle', ''),
    ('write: command exactly on the limit refused', W({'exclusive_limit': True}), 'write_cycle', ''),
    ('write: only joint 0 limit checked', W({'only_j0_limit': True}), 'write_cycle', ''),
    ('write: velocity limit ignores dt', W({'no_dt': True}), 'write_cycle', ''),
    ('write: joint 1 uses joint 0 velocity limit', W({'same_vmax': True}), 'write_cycle', ''),
    ('write: rate limit not applied at all', W({'no_limit': True}), 'write_cycle', ''),
    ('write: velocity read back from the command, not the motion', W({'cmd_velocity': True}), 'write_cycle', 'velocity'),
    ('write: rate-limited cycle reports ok', W({'always_ok': True}), 'write_cycle', 'status'),
    ('write: refused command reports the attempted velocity', W({'moving_velocity': True}), 'write_cycle', 'velocity'),
    ('write: a 1e-3 tie tolerance lets a slightly too far joint land on its command', W({'tie_big': True}), 'write_cycle', ''),
    ('write: velocity rounded to 6 digits', W({'round_vel': True}), 'write_cycle', 'velocity'),
    ('write: tie exactly at the step counts as rate-limited', W({'strict_tie': True}), 'write_cycle', ''),
    ('write: limiting scales the whole vector instead of each joint', W({'vector_scale': True}), 'write_cycle', ''),
    ('write: position limit judged before the lifecycle', W({'limit_first': True}), 'write_cycle', 'status'),
    ('write: limited step always moves in the positive direction', W({'abs_sign': True}), 'write_cycle', ''),
    ('write: in-limit joint moves while the other joint is refused', W({'partial': True}), 'write_cycle', ''),
    ('trajectory: order mismatch reported as a names mismatch', V({'order_as_names': True}), 'validate_trajectory', ''),
    ('trajectory: names compared as sets', V({'set_names': True}), 'validate_trajectory', ''),
    ('trajectory: equal waypoint times accepted', V({'equal_time_ok': True}), 'validate_trajectory', ''),
    ('trajectory: only the first pair of times checked', V({'first_pair_time': True}), 'validate_trajectory', ''),
    ('trajectory: position limit exclusive of the boundary', V({'pos_exclusive': True}), 'validate_trajectory', ''),
    ('trajectory: only joint 0 position limit checked', V({'pos_j0': True}), 'validate_trajectory', ''),
    ('trajectory: joint 1 judged by joint 0 velocity limit', V({'same_vmax': True}), 'validate_trajectory', ''),
    ('trajectory: velocity limit without the time difference', V({'no_dt': True}), 'validate_trajectory', ''),
    ('trajectory: last segment skipped in the velocity check', V({'skip_last_segment': True}), 'validate_trajectory', ''),
    ('trajectory: difference equal to the start tolerance rejected', V({'tol_strict': True}), 'validate_trajectory', ''),
    ('trajectory: start compared with zero, not the current state', V({'start_zero': True}), 'validate_trajectory', ''),
    ('trajectory: only joint 0 start compared', V({'start_j0': True}), 'validate_trajectory', ''),
    ('trajectory: only the first reason returned', V({'first_only': True}), 'validate_trajectory', ''),
    ('trajectory: reasons in reverse order', V({'reverse': True}), 'validate_trajectory', 'order'),
    ('trajectory: a repeated reason listed twice', V({'duplicate': True}), 'validate_trajectory', ''),
    ('trajectory: empty trajectory accepted', V({'accept_empty': True}), 'validate_trajectory', ''),
    ('trajectory: a wrong-width waypoint crashes', V({'crash_on_width': True}), 'validate_trajectory', 'raised'),
    ('trajectory: sorts the caller points in place', {'validate_trajectory': mutates_points}, 'validate_trajectory', 'modified'),
    ('action: timeout reached at exactly the limit', A({'timeout_ge': True}), 'action_run', ''),
    ('action: timeout measured from the previous event', A({'from_prev': True}), 'action_run', ''),
    ('action: timeout measured from the first event', A({'from_first': True}), 'action_run', ''),
    ('action: a result after aborted can change the outcome', A({'open_terminal': True}), 'action_run', ''),
    ('action: cancel ignored while the goal is pending', A({'no_pending_cancel': True}), 'action_run', ''),
    ('action: cancel wins over a result that arrives while canceling', A({'cancel_wins': True}), 'action_run', ''),
    ('action: lower feedback overwrites progress', A({'fb_any': True}), 'action_run', ''),
    ('action: feedback of 1.0 finishes the goal', A({'fb_finishes': True}), 'action_run', ''),
    ('action: succeeded keeps the last feedback instead of 1.0', A({'keep_progress': True}), 'action_run', ''),
    ('action: late event still applied, then timed out', A({'late_applies': True}), 'action_run', ''),
    ('action: a rejected goal reported as aborted', A({'reject_aborted': True}), 'action_run', ''),
    ('action: accept honoured before any send_goal', A({'accept_idle': True}), 'action_run', ''),
    ('action: progress reset by non-feedback events', A({'reset_progress': True}), 'action_run', ''),
    ('action: a second send_goal restarts the timeout', A({'resend': True}), 'action_run', ''),
    ('action: feedback honoured while still pending', A({'fb_pending': True}), 'action_run', ''),
    ('action: sorts the caller event list in place', {'action_run': mutates_events}, 'action_run', 'modified'),
    ('scene: last sample (k = 200) skipped', S({'skip_last': True}), 'segment_free', ''),
    ('scene: first sample (k = 0) skipped', S({'skip_first': True}), 'segment_free', ''),
    ('scene: both end samples skipped', S({'skip_both': True}), 'segment_free', ''),
    ('scene: 50 steps (every fourth sample)', S({'steps': 50}), 'segment_free', ''),
    ('scene: box inflated by 0.001 m', S({'inflate': True}), 'segment_free', ''),
    ('scene: only the end configurations checked', S({'ends_only': True}), 'segment_free', ''),
    ('scene: tip point only', S({'tip_only': True}), 'segment_free', ''),
    ('scene: elbow point only', S({'elbow_only': True}), 'segment_free', ''),
    ('scene: elbow and tip points, not the links', S({'points_only': True}), 'segment_free', ''),
    ('scene: link 1 ignored', S({'skip_link1': True}), 'segment_free', ''),
    ('scene: far too coarse a subdivision', S({'steps': 10}), 'segment_free', ''),
    ('scene: only 3 samples along the segment', S({'steps': 3}), 'segment_free', ''),
    ('scene: touching the box allowed (open box)', S({'open_box': True}), 'segment_free', ''),
    ('scene: link bounding boxes used instead of the links', S({'bbox': True}), 'segment_free', ''),
    ('scene: q2 treated as an absolute angle', S({'absolute_q2': True}), 'segment_free', ''),
    ('scene: box x and y swapped', S({'swap_xy': True}), 'segment_free', ''),
    ('scene: tip interpolated in Cartesian space instead of joint space', S({'cartesian': True}), 'segment_free', ''),
    ('scene: joint 1 interpolated along the shortest angular path', S({'shortest': True}), 'segment_free', ''),
]
require(len(mutants) >= 30, 'need at least 30 mutants')
for label, over, fname, needle in mutants:
    result = run_with(over, FAST)
    require(result, 'mutant not rejected: ' + label)
    require(all(f.startswith(fname) or f.startswith('invalid ' + fname) for f in result),
            'mutant failures should only concern ' + fname + ' (' + label + '): ' + str(result[:3]))
    if needle:
        require(any(needle in f for f in result), 'mutant rejected for the wrong reason (' + label + '): '
                + str(result[:3]))
    require(all(f.isascii() for f in result), 'messages must be ASCII (' + label + ')')

# ---- starter and message hygiene ----
partial = run_with({'lifecycle_next': lambda s, r: (_ for _ in ()).throw(NotImplementedError())}, FAST)
require(len(partial) == 1 and 'lifecycle_next' in partial[0] and 'not implemented yet' in partial[0],
        'a NotImplementedError function must collapse into one line: ' + str(partial))
leaky = run_with(W({'no_dt': True}), FAST)
require(all('rate-limited' not in f and 'ok' not in f.split(':', 1)[1] for f in leaky if f.startswith('write_cycle case')),
        'messages must not print expected values')
raiser = run_with({'segment_free': lambda *a: (_ for _ in ()).throw(KeyError('x'))}, FAST)
require(any('your code raised KeyError' in f for f in raiser), 'raised message missing')
lax = run_with({'action_run': lambda e, t: ([], [])}, FAST)
require(any('one entry per event' in f for f in lax), 'shape message missing')
no_validation = run_with({'lifecycle_next': lambda s, r: (s, False)}, FAST)
require(any(f.startswith('invalid lifecycle_next') for f in no_validation), 'invalid-input check missing')
print('Interfaces kit: ' + str(len(alternatives)) + ' valid alternatives accepted, ' + str(len(mutants))
      + ' injected bugs rejected; starter fails as intended')
