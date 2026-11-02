"""CoreLab Replay Node lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
REPLAY OF A RECORDED LIST OF PLAIN PYTHON DICTS ONLY. This kit is the ROS-free
logic core that a ROS 2 odometry node could wrap. It uses no ROS, no DDS and
no rosbag. There are no QoS profiles, no TF2 broadcasting, no ROS or
simulated clock, no executor, no launch file, no message serialisation and no
real robot. Do not import rclpy here; this kit cannot show that a real node
works. It teaches the policies a node needs: which messages are used, in what
order, and what is published after each one.
Implement the three functions below, then run your edited file locally:
  Windows: py -3 L05-replay.v1.py
  macOS/Linux: python3 L05-replay.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Model. Wheel-odometry messages arrive as dicts; the node emits pose dicts.
Pose (x, y, theta) is the axle midpoint in the odom frame, metres and radians,
+theta counter-clockwise, ideal differential drive with no slip (same model
as the L03 odometry kit). Times are INTEGER NANOSECONDS (never float).

config (dict with exactly these keys; anything else raises ValueError):
  frame_id        str, 1 to 32 chars: the frame_id messages must carry
  child_frame_id  str, 1 to 32 chars: the child_frame_id messages must carry
  track           finite int/float (not bool), 0.1 <= track <= 2 (metres)
  max_gap_ns      int (not bool), 1 <= max_gap_ns <= 10**12
  gap_policy      "reset" or "flag"
  initial_pose    list/tuple of 3 finite int/float, |x|,|y| <= 1000,
                  |theta| <= 2*pi

messages: a list or tuple of 0 to 200 dicts. Two kinds, exact key sets:
  odom : {"kind": "odom", "stamp": int, "frame_id": str, "child_frame_id":
          str, "vl": number, "vr": number}
         stamp int (not bool) 0 <= stamp <= 10**13 ns; frame ids are any str
         of 0 to 32 chars (a wrong frame is VALID input, see policy); vl, vr
         are LINEAR rim speeds in m/s, finite int/float, |v| <= 2.
  reset: {"kind": "reset", "stamp": int, "x": number, "y": number,
          "theta": number} with the same stamp bounds, |x|,|y| <= 1000 and
          |theta| <= 2*pi.
Stamps need NOT be increasing (out-of-order data is the point of the lab).
Invalid config or message (wrong type or shape, bool, NaN, infinity, out of
bounds, unknown kind, missing or extra key, more than 200 messages) raises
ValueError before anything is produced. Never mutate config or messages.

replay_node(config, messages) -> (poses, drops)
  Process the messages in list order with this declared policy. State: the
  current pose and the "clock" last (the stamp of the last accepted odom
  message or of the last reset); both start as None.
  1. reset message: never dropped, whatever its stamp. pose = its (x, y,
     wrapped theta); last = its stamp; emit a pose with flag "reset".
  2. odom message, checked in this order, the first failing check drops it:
       frame_id != config frame_id            -> drop reason "frame"
       child_frame_id != config child         -> drop reason "child_frame"
       last is not None and stamp == last     -> drop reason "duplicate"
       last is not None and stamp < last      -> drop reason "out_of_order"
     A dropped message emits nothing and changes NO state (the clock too).
  3. an accepted odom message always emits exactly one pose (the intermediate
     pose) with the message's stamp:
       last is None: pose = initial_pose (theta wrapped), flag "init"; no
         integration (this message only starts the clock).
       otherwise dt_ns = stamp - last. The speeds in the message apply over
         the interval (last, stamp] (they were measured over the PREVIOUS
         interval). It is a GAP when dt_ns > max_gap_ns (equal is not a gap).
         No gap: integrate, flag "ok". Gap with policy "reset": pose =
         initial_pose, no integration, flag "gap". Gap with policy "flag":
         integrate over the whole gap anyway, flag "gap".
       Integration: dl = vl*dt, dr = vr*dt with dt = dt_ns/10**9 seconds, then
         the exact constant-curvature arc step (provided: exact_arc).
       Afterwards last = stamp.
  The pose message is a dict with exactly the keys stamp (int ns), frame_id
  and child_frame_id (the CONFIG values), x, y, theta (finite floats, theta in
  [-pi, pi], either endpoint allowed) and flag ("init", "ok", "gap", "reset").
  poses is a list/tuple of such dicts, one per emitted pose, in order. drops is
  a list/tuple of pairs (index, reason) with the 0-based message index and the
  reason string, in order. Return a pair (poses, drops). Empty input gives
  ([], []). Pose tolerance in checks: 1e-9 m and 1e-9 rad (wrapped), exact
  equality for stamp, frames, flag, indices and reasons. Several arc
  formulations are legitimate; do not compare floats with == in your own tests.

minimal_reproducer(node, config, messages) -> list of int, or None
  node is a function node(config, messages) -> (poses, drops) like
  replay_node, possibly faulty. Use YOUR replay_node as the reference. A
  subsequence (a selection of indices in increasing order, keeping the
  original messages and their stamps) EXPOSES a fault when node and
  replay_node give different results on it (poses outside the tolerances
  above, or different drops) or node raises on it while replay_node does not.
  Return the increasing list of indices of a SHORTEST exposing subsequence (any
  one if several; the empty subsequence counts), or None when node agrees with
  replay_node on the full list. The kit only supplies lists where this is
  unambiguous: either node differs on the full list, or it agrees on every
  subsequence. messages has 0 to 12 entries; more raise ValueError, and a
  node that is not callable raises ValueError. Never mutate the inputs.

node_tests(node) -> bool
  Your independent test suite. It receives a candidate node core (a function
  node(config, messages) -> (poses, drops)) and returns True to ACCEPT it or
  False to REJECT it. The kit runs it on two valid cores (written in different
  styles, so floats differ in the last digits) which it must accept, and on a
  set of cores with realistic bugs which it must reject. Build your own
  configs and message lists; compare floats with a tolerance; an exception from
  the node (including ValueError on a valid input) means reject. Check that a
  node raises ValueError on invalid input, does not mutate its arguments and
  gives the same answer when called twice. Return a real bool. A suite that
  agrees with your own replay_node is allowed, but then replay_node itself must
  be right: this kit also checks it.

exact_arc(pose, dl, dr, track) -> (x, y, theta)   (PROVIDED, already working)
  The exact planar arc of the L03 odometry kit: dl, dr are wheel travels in
  metres, heading wrapped to [-pi, pi]. No validation; use it as is.

Predict before coding:
  1. Two messages carry the same stamp. Which one counts, and does the second
     still emit a pose?
  2. A message with the wrong frame_id arrives between two good ones. Does the
     clock advance? What happens to the time step of the next good message?
  3. A reset message has an EARLIER stamp than the last accepted message. What
     is the next dt, and why is this not a "duplicate" or "out_of_order" case?
  4. Exactly max_gap_ns passes. Is it a gap? How does your answer change at
     max_gap_ns + 1? Which policy keeps the pose and which discards it?
  5. A one-message log: what is emitted? What does the first message do to the
     clock?
  6. Which small log shows that a node ignores child_frame_id? Which shows
     that it rewinds its clock on a dropped message? What is the shortest
     message list for each?
Self-check tolerances are per-case metres and radians, not physical accuracy.
Failure messages start with a tag such as [stamp] or [gap] and name the kind of
mismatch, never the expected numbers. "your code raised X" means your function
raised on a VALID input. A function still raising NotImplementedError is
reported once. For node_tests the kit names the mutant (M01...) and its area.
Honest limits of this self-check: it is a fixed practice fixture and can be
gamed. The candidate cores are anonymous closures with the same name, shuffled,
but nothing stops you from detecting them by behaviour or reading the spoiler
section, and passing proves nothing about your suite on other bugs. Treat it as
feedback on what to test, not as a measurement.
Reflection: even a perfect replay node only proves its logic on this recorded
list. It says nothing about DDS delivery, QoS history or reliability, clock
sources and time jumps, TF2 buffering and lookup, wheel slip, calibration, or
whether the robot actually went where the poses say.
"""
import math
from decimal import Decimal, localcontext

_NS = 1000000000


def exact_arc(pose, dl, dr, track):
    """Provided. Exact constant-curvature step in the world frame."""
    distance, angle = (dl + dr) / 2.0, (dr - dl) / track
    half = angle / 2.0
    if abs(half) < 1e-4:
        sinc = 1.0 - half * half / 6.0 + half ** 4 / 120.0
    else:
        sinc = math.sin(half) / half
    chord, heading = distance * sinc, pose[2] + half
    return (pose[0] + chord * math.cos(heading),
            pose[1] + chord * math.sin(heading),
            math.atan2(math.sin(pose[2] + angle), math.cos(pose[2] + angle)))


def replay_node(config, messages):
    raise NotImplementedError("Apply the declared frame, stamp, gap and reset policy")


def minimal_reproducer(node, config, messages):
    raise NotImplementedError("Find a shortest message subsequence on which node differs")


def node_tests(node):
    raise NotImplementedError("Accept valid node cores and reject the buggy ones")


# ---- SPOILER BELOW: the reference node and the buggy cores used to judge ----
# ---- node_tests. Do not read it before writing your own tests; the list of
# ---- mutants is exactly the list of bugs your suite must catch.


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


_STAMP_MAX = 10 ** 13
_CFG_KEYS = {'frame_id', 'child_frame_id', 'track', 'max_gap_ns', 'gap_policy',
             'initial_pose'}
_ODOM_KEYS = {'kind', 'stamp', 'frame_id', 'child_frame_id', 'vl', 'vr'}
_RESET_KEYS = {'kind', 'stamp', 'x', 'y', 'theta'}
_POSE_KEYS = {'stamp', 'frame_id', 'child_frame_id', 'x', 'y', 'theta', 'flag'}


def _wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def _num(value, bound):
    return type(value) in (int, float) and math.isfinite(value) and abs(value) <= bound


def _validate(config, messages, flaw=None):
    def bad():
        raise ValueError("invalid config or messages")
    int_ok = (lambda v: isinstance(v, int)) if flaw == 'bool-stamp' else (lambda v: type(v) is int)
    if type(config) is not dict or set(config) != _CFG_KEYS:
        bad()
    for key in ('frame_id', 'child_frame_id'):
        if type(config[key]) is not str or not 1 <= len(config[key]) <= 32:
            bad()
    low = 0.0 if flaw == 'loose-track' else 0.1
    if not _num(config['track'], 2) or config['track'] < low or config['track'] <= 0:
        bad()
    if type(config['max_gap_ns']) is not int or not 1 <= config['max_gap_ns'] <= 10 ** 12:
        bad()
    if type(config['gap_policy']) is not str or config['gap_policy'] not in ('reset', 'flag'):
        bad()
    pose = config['initial_pose']
    if (not isinstance(pose, (list, tuple)) or len(pose) != 3
            or not _num(pose[0], 1000) or not _num(pose[1], 1000)
            or not _num(pose[2], 2 * math.pi)):
        bad()
    if not isinstance(messages, (list, tuple)) or len(messages) > 200:
        bad()
    for m in messages:
        if type(m) is not dict or m.get('kind') not in ('odom', 'reset'):
            bad()
        if set(m) != (_ODOM_KEYS if m['kind'] == 'odom' else _RESET_KEYS):
            bad()
        if not int_ok(m['stamp']) or not 0 <= m['stamp'] <= _STAMP_MAX:
            bad()
        if m['kind'] == 'odom':
            for key in ('frame_id', 'child_frame_id'):
                if type(m[key]) is not str or len(m[key]) > 32:
                    bad()
            if not _num(m['vl'], 2) or not _num(m['vr'], 2):
                bad()
        elif not (_num(m['x'], 1000) and _num(m['y'], 1000) and _num(m['theta'], 2 * math.pi)):
            bad()


def _decimal_arc(pose, dl, dr, track):
    """Independent high-precision arc (integrated sine/cosine power series)."""
    with localcontext() as ctx:
        ctx.prec = 140
        left, right, width = map(Decimal.from_float, map(float, (dl, dr, track)))
        distance, angle = (left + right) / 2, (right - left) / width
        even, odd = Decimal(1), angle / 2
        sx, sy = even, odd
        for k in range(1, 400):
            even *= -angle * angle / Decimal((2 * k) * (2 * k + 1))
            odd *= -angle * angle / Decimal((2 * k + 1) * (2 * k + 2))
            sx += even
            sy += odd
        bx, by = float(distance * sx), float(distance * sy)
        turn = float(angle)
    x, y, theta = pose
    return (x + math.cos(theta) * bx - math.sin(theta) * by,
            y + math.sin(theta) * bx + math.cos(theta) * by,
            _wrap(theta + turn))


def _euler_arc(pose, dl, dr, track):
    """Flawed: straight chord along the INITIAL heading."""
    return (pose[0] + (dl + dr) / 2 * math.cos(pose[2]),
            pose[1] + (dl + dr) / 2 * math.sin(pose[2]),
            _wrap(pose[2] + (dr - dl) / track))


def _unwrapped_arc(pose, dl, dr, track):
    """Flawed: correct position, heading never wrapped."""
    x, y, _ = exact_arc(pose, dl, dr, track)
    return (x, y, pose[2] + (dr - dl) / track)


def _run(config, messages, flaw=None, arc=exact_arc, memory=None):
    """Reference policy; `flaw` switches in one named bug (see _MUTANTS)."""
    if flaw == 'crash-empty' and not messages:
        raise IndexError("no first message")
    if flaw != 'no-validation':
        _validate(config, messages, flaw)
    if flaw == 'euler':
        arc = _euler_arc
    elif flaw == 'theta-unwrapped':
        arc = _unwrapped_arc
    frame, child = config['frame_id'], config['child_frame_id']
    initial = (float(config['initial_pose'][0]), float(config['initial_pose'][1]),
               _wrap(config['initial_pose'][2]))
    if flaw == 'theta-unwrapped':
        initial = tuple(map(float, config['initial_pose']))
    track, max_gap, policy = config['track'], config['max_gap_ns'], config['gap_policy']
    pose = last = None
    if flaw == 'state-leak':
        pose, last = memory['pose'], memory['last']
    poses, drops = [], []

    def emit(stamp, at, flag):
        a, b = (child, frame) if flaw == 'frames-swapped' else (frame, child)
        shown = stamp
        if flaw == 'stamp-previous' and last is not None and flag == 'ok':
            shown = last
        poses.append({'stamp': shown, 'frame_id': a, 'child_frame_id': b,
                      'x': float(at[0]), 'y': float(at[1]), 'theta': float(at[2]),
                      'flag': flag})

    for index, m in enumerate(messages):
        if flaw == 'mutates-input':
            m['seen'] = True
        stamp = m['stamp']
        if m['kind'] == 'reset':
            if flaw == 'reset-ignored':
                continue
            pose = (float(m['x']), float(m['y']), _wrap(m['theta']))
            if flaw != 'reset-clock-kept':
                last = stamp
            if flaw != 'reset-no-output':
                emit(stamp, pose, 'reset')
            continue
        frame_bad = m['frame_id'] != frame and flaw != 'frame-ignored'
        child_bad = m['child_frame_id'] != child and flaw != 'child-ignored'
        if flaw == 'frame-casefold':
            frame_bad = m['frame_id'].lower() != frame.lower()
        elif flaw == 'frame-prefix':
            frame_bad = not m['frame_id'].startswith(frame)
        elif flaw == 'child-prefix':
            child_bad = not m['child_frame_id'].startswith(child)
        elif flaw == 'child-casefold':
            child_bad = m['child_frame_id'].lower() != child.lower()
        stamp_reason = None
        if last is not None:
            if stamp == last and flaw != 'dup-accepted':
                stamp_reason = 'out_of_order' if flaw == 'dup-reason-wrong' else 'duplicate'
            elif stamp < last and flaw != 'ooo-accepted':
                stamp_reason = 'out_of_order'
        checks = [('frame', frame_bad), ('child_frame', child_bad),
                  (stamp_reason, stamp_reason is not None)]
        if flaw == 'stamp-before-frame':
            checks = [checks[2], checks[0], checks[1]]
        reason = next((name for name, failed in checks if failed), None)
        if reason is not None:
            drops.append((index, reason))
            if last is not None and ((flaw == 'ooo-rewinds-clock' and reason == 'out_of_order')
                                     or (flaw == 'frame-drop-rewinds-clock'
                                         and reason in ('frame', 'child_frame'))):
                last = stamp
            continue
        if last is None:
            pose, flag = initial, 'init'
            if flaw == 'first-integrates':
                dt = stamp / _NS
                pose = arc(pose, m['vl'] * dt, m['vr'] * dt, track)
        else:
            dt_ns = stamp - last
            gap = dt_ns >= max_gap if flaw == 'gap-inclusive' else dt_ns > max_gap
            if flaw == 'gap-never':
                gap = False
            flag = 'gap' if gap else 'ok'
            if gap and flaw == 'gap-flag-missing' and policy == 'flag':
                flag = 'ok'
            dt = dt_ns / (1e6 if flaw == 'dt-units' else _NS)
            dl, dr = m['vl'] * dt, m['vr'] * dt
            if flaw == 'swapped-wheels':
                dl, dr = dr, dl
            if gap and policy == 'reset':
                if flaw != 'gap-reset-keeps-pose':
                    pose = initial
                if flaw == 'gap-reset-integrates':
                    pose = arc(pose, dl, dr, track)
            elif not (gap and flaw == 'gap-flag-skips'):
                pose = arc(pose, dl, dr, track)
        emit(stamp, pose, flag)
        last = stamp
    if flaw == 'state-leak':
        memory['pose'], memory['last'] = pose, last
    if flaw == 'only-final':
        poses = poses[-1:]
    return (poses, drops)


class _NodeB(object):
    """Valid core B: incremental object, complex-number arc, tuple outputs."""

    def __init__(self, config):
        self.cfg = config
        start = config['initial_pose']
        self.start = (complex(start[0], start[1]), _wrap(start[2]))
        self.z = self.theta = self.last = None

    def _step(self, vl, vr, dt):
        left, right = vl * dt, vr * dt
        phi = (right - left) / self.cfg['track']
        run = (left + right) / 2
        heading = complex(math.cos(self.theta), math.sin(self.theta))
        if abs(phi) < 1e-9:
            self.z += heading * run * (1 - phi * phi / 6) * complex(1, phi / 2)
        else:
            turn = complex(math.cos(phi), math.sin(phi))
            self.z += heading * run * (turn - 1) / complex(0, phi)
        self.theta = _wrap(self.theta + phi)

    def feed(self, index, m):
        cfg = self.cfg
        if m['kind'] == 'reset':
            self.z, self.theta = complex(m['x'], m['y']), _wrap(m['theta'])
            self.last = m['stamp']
            return self._pose(m['stamp'], 'reset'), None
        for reason, bad in (('frame', m['frame_id'] != cfg['frame_id']),
                            ('child_frame', m['child_frame_id'] != cfg['child_frame_id']),
                            ('duplicate', self.last == m['stamp']),
                            ('out_of_order', self.last is not None and m['stamp'] < self.last)):
            if bad:
                return None, [index, reason]
        flag = 'ok'
        if self.last is None:
            (self.z, self.theta), flag = self.start, 'init'
        elif m['stamp'] - self.last > cfg['max_gap_ns']:
            flag = 'gap'
            if cfg['gap_policy'] == 'reset':
                (self.z, self.theta) = self.start
            else:
                self._step(m['vl'], m['vr'], (m['stamp'] - self.last) / _NS)
        else:
            self._step(m['vl'], m['vr'], (m['stamp'] - self.last) / _NS)
        self.last = m['stamp']
        return self._pose(m['stamp'], flag), None

    def _pose(self, stamp, flag):
        return {'stamp': stamp, 'frame_id': self.cfg['frame_id'],
                'child_frame_id': self.cfg['child_frame_id'], 'x': self.z.real,
                'y': self.z.imag, 'theta': self.theta, 'flag': flag}


def _core_b(config, messages):
    _validate(config, messages)
    node, poses, drops = _NodeB(config), [], []
    for index, m in enumerate(messages):
        pose, drop = node.feed(index, m)
        if pose is not None:
            poses.append(pose)
        if drop is not None:
            drops.append(drop)
    return (tuple(poses), tuple(drops))


def _core_a(config, messages):
    return _run(config, messages)


_MUTANTS = [
    # (id, area, flaw)
    ('M01', 'frame', 'frame-ignored'), ('M02', 'frame', 'child-ignored'),
    ('M03', 'stamp', 'dup-accepted'), ('M04', 'stamp', 'ooo-accepted'),
    ('M05', 'stamp', 'ooo-rewinds-clock'), ('M06', 'frame', 'frame-drop-rewinds-clock'),
    ('M07', 'frame', 'stamp-before-frame'), ('M08', 'stamp', 'dup-reason-wrong'),
    ('M09', 'gap', 'gap-inclusive'), ('M10', 'gap', 'gap-never'),
    ('M11', 'gap', 'gap-reset-keeps-pose'), ('M12', 'gap', 'gap-reset-integrates'),
    ('M13', 'gap', 'gap-flag-missing'), ('M14', 'gap', 'gap-flag-skips'),
    ('M15', 'reset', 'reset-ignored'), ('M16', 'reset', 'reset-clock-kept'),
    ('M17', 'reset', 'reset-no-output'), ('M18', 'start', 'first-integrates'),
    ('M19', 'pose', 'euler'), ('M20', 'pose', 'theta-unwrapped'),
    ('M21', 'pose', 'dt-units'), ('M22', 'pose', 'swapped-wheels'),
    ('M23', 'output', 'only-final'), ('M24', 'output', 'stamp-previous'),
    ('M25', 'output', 'frames-swapped'), ('M26', 'mutation', 'mutates-input'),
    ('M27', 'repeat', 'state-leak'), ('M28', 'invalid', 'no-validation'),
    ('M29', 'invalid', 'bool-stamp'), ('M30', 'invalid', 'loose-track'),
    ('M31', 'start', 'crash-empty'), ('M32', 'frame', 'frame-casefold'),
    ('M33', 'frame', 'frame-prefix'), ('M34', 'frame', 'child-prefix'),
    ('M35', 'frame', 'child-casefold'),
]


def _anonymous(core):
    """Every candidate core goes through here so none can be told apart by name."""
    def node(config, messages):
        return core(config, messages)
    return node


def _mutant(flaw):
    memory = {'pose': None, 'last': None}
    return _anonymous(lambda config, messages: _run(config, messages, flaw, memory=memory))


def _same(got, want):
    """Return None when results match, else a short description of the kind."""
    if not (isinstance(got, (list, tuple)) and len(got) == 2
            and isinstance(got[0], (list, tuple)) and isinstance(got[1], (list, tuple))):
        return 'result must be a pair (poses, drops) of lists/tuples'
    poses, drops = got
    if len(poses) != len(want[0]):
        return 'number of emitted pose messages is wrong'
    for pose, ref in zip(poses, want[0]):
        if type(pose) is not dict or set(pose) != _POSE_KEYS:
            return 'pose message must be a dict with exactly the documented keys'
        if type(pose['stamp']) is not int or pose['stamp'] != ref['stamp']:
            return 'pose stamp is wrong'
        if pose['frame_id'] != ref['frame_id'] or pose['child_frame_id'] != ref['child_frame_id']:
            return 'pose frame ids are wrong'
        if pose['flag'] != ref['flag']:
            return 'pose flag is wrong'
        for key in ('x', 'y', 'theta'):
            if type(pose[key]) not in (int, float) or not math.isfinite(pose[key]):
                return 'pose ' + key + ' must be a finite int/float'
        if abs(pose['x'] - ref['x']) > 1e-9 or abs(pose['y'] - ref['y']) > 1e-9:
            return 'pose position error exceeds 1e-9 m'
        if not -math.pi <= pose['theta'] <= math.pi:
            return 'heading not wrapped to [-pi, pi]'
        if abs(_wrap(pose['theta'] - ref['theta'])) > 1e-9:
            return 'pose heading error exceeds 1e-9 rad'
    shaped = []
    for item in drops:
        if not (isinstance(item, (list, tuple)) and len(item) == 2
                and type(item[0]) is int and type(item[1]) is str):
            return 'each drop must be a pair (index, reason)'
        shaped.append((item[0], item[1]))
    if shaped != [tuple(d) for d in want[1]]:
        return 'drop list (indices or reasons) is wrong'
    return None


def _o(ms, vl, vr, frame='odom', child='base_link'):
    return {'kind': 'odom', 'stamp': ms * 1000000, 'frame_id': frame,
            'child_frame_id': child, 'vl': vl, 'vr': vr}


def _on(ns, vl, vr, frame='odom', child='base_link'):
    message = _o(0, vl, vr, frame, child)
    message['stamp'] = ns
    return message


def _r(ms, x, y, theta):
    return {'kind': 'reset', 'stamp': ms * 1000000, 'x': x, 'y': y, 'theta': theta}


def _cfg(**over):
    base = {'frame_id': 'odom', 'child_frame_id': 'base_link', 'track': 0.5,
            'max_gap_ns': _NS, 'gap_policy': 'reset', 'initial_pose': [0.0, 0.0, 0.0]}
    base.update(over)
    return base


def _pose(ms, x, y, theta, flag, frame='odom', child='base_link'):
    return {'stamp': ms * 1000000, 'frame_id': frame, 'child_frame_id': child,
            'x': x, 'y': y, 'theta': theta, 'flag': flag}


_HALF_PI = math.pi / 2

# Hand-derived anchors: (tag, config, messages, expected poses, expected drops).
_ANCHORS = [
    ('start', _cfg(), [], [], []),
    ('start', _cfg(initial_pose=[1.0, -2.0, 0.5]), [_o(100, 0.3, 0.3)],
     [_pose(100, 1.0, -2.0, 0.5, 'init')], []),
    ('pose', _cfg(), [_o(0, .4, .4), _o(500, .4, .4), _o(1000, .4, .4)],
     [_pose(0, 0.0, 0.0, 0.0, 'init'), _pose(500, .2, 0.0, 0.0, 'ok'),
      _pose(1000, .4, 0.0, 0.0, 'ok')], []),
    ('pose', _cfg(initial_pose=[0.0, 0.0, _HALF_PI]),
     [_o(0, -.25, .25), _o(500, -.25, .25)],
     [_pose(0, 0.0, 0.0, _HALF_PI, 'init'), _pose(500, 0.0, 0.0, _HALF_PI + .5, 'ok')], []),
    ('pose', _cfg(track=1.0), [_o(0, 0., 0.), _o(1000, 0., _HALF_PI)],
     [_pose(0, 0.0, 0.0, 0.0, 'init'), _pose(1000, .5, .5, _HALF_PI, 'ok')], []),
    ('stamp', _cfg(),
     [_o(1000, 0., 0.), _o(1500, .4, .4), _o(1500, .8, .8),
      _o(2000, .9, .9, 'map'), _o(2500, .6, .6)],
     [_pose(1000, 0.0, 0.0, 0.0, 'init'), _pose(1500, .2, 0.0, 0.0, 'ok'),
      _pose(2500, .8, 0.0, 0.0, 'ok')], [(2, 'duplicate'), (3, 'frame')]),
    ('stamp', _cfg(),
     [_o(1000, 0., 0.), _o(1400, .5, .5), _o(1200, .9, .9),
      _o(1600, .5, .5, 'odom', 'tool0'), _o(1800, .5, .5)],
     [_pose(1000, 0.0, 0.0, 0.0, 'init'), _pose(1400, .2, 0.0, 0.0, 'ok'),
      _pose(1800, .4, 0.0, 0.0, 'ok')], [(2, 'out_of_order'), (3, 'child_frame')]),
    ('reset', _cfg(), [_o(0, .4, .4), _r(300, 1.0, 2.0, _HALF_PI), _o(800, .4, .4)],
     [_pose(0, 0.0, 0.0, 0.0, 'init'), _pose(300, 1.0, 2.0, _HALF_PI, 'reset'),
      _pose(800, 1.0, 2.2, _HALF_PI, 'ok')], []),
    ('gap', _cfg(), [_o(0, .4, .4), _o(500, .4, .4), _o(2000, .4, .4), _o(2500, .4, .4)],
     [_pose(0, 0.0, 0.0, 0.0, 'init'), _pose(500, .2, 0.0, 0.0, 'ok'),
      _pose(2000, 0.0, 0.0, 0.0, 'gap'), _pose(2500, .2, 0.0, 0.0, 'ok')], []),
    ('gap', _cfg(gap_policy='flag'),
     [_o(0, .4, .4), _o(500, .4, .4), _o(2000, .4, .4), _o(2500, .4, .4)],
     [_pose(0, 0.0, 0.0, 0.0, 'init'), _pose(500, .2, 0.0, 0.0, 'ok'),
      _pose(2000, .8, 0.0, 0.0, 'gap'), _pose(2500, 1.0, 0.0, 0.0, 'ok')], []),
]

# Independent-method cases: (tag, config, messages) compared with the decimal oracle.
_ORACLE = [
    ('pose', _cfg(), [_o(0, .1, .3), _o(400, .1, .3), _o(800, -.3, .5), _o(1200, 1., 1.)]),
    ('pose', _cfg(initial_pose=[3., -4., 2.5], track=.3),
     [_o(0, 0., 0.), _o(900, -.9, .9), _o(1800, -.9, .9), _o(2700, .3, .3)]),
    ('pose', _cfg(track=.1), [_o(0, 0., 0.), _o(900, 2., -2.), _o(1800, 2., -2.),
                              _o(2700, 2., -2.), _o(3600, 1., 2.)]),
    ('pose', _cfg(), [_o(0, 0., 0.), _o(1000, .5, .500000000001), _o(2000, .2, .2000001)]),
    ('pose', _cfg(initial_pose=[999., -999., 6.28]), [_o(5, 1., 1.), _o(905, -2., 2.)]),
    ('stamp', _cfg(), [_o(100, .2, .2), _o(100, .5, .5), _o(100, .7, .7), _o(300, .2, .4)]),
    ('stamp', _cfg(), [_o(900, .2, .4), _o(700, .5, .1), _o(1100, .3, .3), _o(1000, .6, .6),
                       _o(1300, .3, .5)]),
    ('stamp', _cfg(), [_o(0, 0., 0.), _o(0, .2, .2), _o(400, .2, .2), _o(400, .4, .4),
                       _o(300, .1, .1), _o(900, .1, .1)]),
    ('frame', _cfg(), [_o(0, .2, .2), _o(300, .2, .2, 'map'), _o(500, .2, .4),
                       _o(600, .2, .2, 'odom', 'laser'), _o(800, .2, .4)]),
    ('frame', _cfg(), [_o(0, .2, .2), _o(200, .2, .2, 'Odom'), _o(400, .3, .3, 'odom2'),
                       _o(600, .3, .3, 'odom ', 'base_link'), _o(800, .3, .3, 'odom', 'Base_link'),
                       _o(900, .3, .3, 'odom', 'base_link2'), _o(1000, .2, .4, 'ODOM', 'BASE_LINK'),
                       _o(1100, .2, .4)]),
    ('frame', _cfg(), [_o(0, .2, .2), _o(300, .2, .2, 'odometry'), _o(500, .3, .3, 'odom', 'base_linked'),
                       _o(700, .3, .3, 'odom', 'base_lin'), _o(900, .2, .4, 'od', 'base_link'),
                       _o(1000, .2, .4)]),
    ('frame', _cfg(), [_o(500, .2, .2, 'map', 'laser'), _o(500, .3, .3), _o(500, .3, .3, 'map'),
                       _o(400, .1, .1, 'odom', 'other'), _o(900, .3, .1)]),
    ('frame', _cfg(), [_o(500, .2, .2), _o(500, .3, .3, 'map'), _o(400, .3, .3, 'odom', 'x'),
                       _o(500, .1, .1, 'odom', 'x'), _o(900, .3, .1)]),
    ('gap', _cfg(), [_o(0, .3, .3), _o(1000, .3, .3), _o(2000, .3, .5),
                     _on(3000000001, .3, .3)]),
    ('gap', _cfg(), [_o(0, .3, .3), _o(200, .3, .3), _on(1200000001, .3, .3),
                     _o(1900, .3, .3)]),
    ('gap', _cfg(gap_policy='flag'),
     [_o(0, .3, .4), _on(1000000000, .3, .4), _on(2000000001, .3, .5), _o(4000, .2, .2)]),
    ('gap', _cfg(initial_pose=[1., 1., 1.], max_gap_ns=250000000),
     [_o(0, .3, .3), _o(250, .3, .3), _o(501, .3, .5), _o(700, .1, .1)]),
    ('reset', _cfg(), [_r(100, 2., 1., 1.), _o(300, .2, .2), _o(700, .2, .4)]),
    ('reset', _cfg(), [_o(5000, .3, .3), _o(5300, .3, .3), _r(100, -1., 1., -3.), _o(400, .5, .5),
                       _o(300, .5, .5), _o(900, .2, .4)]),
    ('reset', _cfg(), [_o(0, .3, .3), _o(300, .3, .3), _r(300, 0., 0., 0.), _o(300, .3, .3),
                       _o(600, .3, .3), _r(600, 1., 1., 1.)]),
    ('reset', _cfg(gap_policy='flag'), [_o(0, .3, .3), _r(2500, 1., 0., 0.), _o(3000, .4, .6),
                                        _o(5000, .4, .6)]),
    ('reset', _cfg(), [_r(100, 0., 0., 5.0), _o(300, .2, .4), _r(500, 1., 1., -6.0)]),
    ('start', _cfg(initial_pose=[-5., 5., -1.]), [_o(7000, .4, .5)]),
    ('start', _cfg(), [_o(2000, .4, .4, 'map')]),
    ('output', _cfg(frame_id='world', child_frame_id='axle'),
     [_o(0, .2, .2, 'world', 'axle'), _o(500, .2, .2, 'world', 'axle'),
      _o(900, .4, .2, 'world', 'axle'), _o(1000, .4, .2, 'odom', 'base_link')]),
]


def _lcg(seed):
    state = [seed * 2654435761 % 2 ** 31 or 1]

    def draw(n):
        state[0] = (state[0] * 1103515245 + 12345) % 2 ** 31
        return (state[0] >> 8) % n
    return draw


def _sweep_log(seed):
    draw = _lcg(seed + 1)
    steps = (-300, 0, 100, 200, 400, 400, 900, 1000, 1001, 1500)
    speeds = (-.4, -.2, 0., .2, .3, .4, .5)
    ms = 500 + 100 * draw(5)
    log = []
    for _ in range(2 + draw(8)):
        pick = draw(12)
        if pick == 0:
            log.append(_r(ms, (draw(5) - 2) * .5, (draw(5) - 2) * .5, (draw(7) - 3) * .9))
        else:
            frame = 'map' if pick == 1 else 'odom'
            child = 'laser' if pick == 2 else 'base_link'
            log.append(_o(ms, speeds[draw(7)], speeds[draw(7)], frame, child))
        ms = max(0, ms + steps[draw(len(steps))])
    return (_cfg(gap_policy=('reset', 'flag')[draw(2)], track=(.3, .5, 1.)[draw(3)]), log)


_SWEEPS = 60


def _invalid_cases():
    good = [_o(0, .1, .1)]
    nan, inf = float('nan'), float('inf')
    cases = []
    for key, value in (('frame_id', ''), ('frame_id', 5), ('child_frame_id', 'x' * 33),
                       ('track', .099), ('track', 2.01), ('track', True), ('track', nan),
                       ('max_gap_ns', 0), ('max_gap_ns', 10 ** 12 + 1), ('max_gap_ns', True),
                       ('max_gap_ns', 1e9), ('gap_policy', 'skip'), ('gap_policy', None),
                       ('initial_pose', [0., 0.]), ('initial_pose', [0., 0., 0., 0.]),
                       ('initial_pose', [0., 0., True]), ('initial_pose', [1001., 0., 0.]),
                       ('initial_pose', [0., 0., 7.]), ('initial_pose', 'abc'),
                       ('initial_pose', [0., nan, 0.])):
        cases.append(('config ' + key + '=' + repr(value), _cfg(**{key: value}), good))
    missing = _cfg()
    del missing['track']
    cases.append(('config missing track', missing, good))
    cases.append(('config extra key', _cfg(extra=1), good))
    cases.append(('config not a dict', [1, 2], good))
    for label, message in (
            ('bool stamp', {**_o(0, 0., 0.), 'stamp': True}),
            ('float stamp', {**_o(0, 0., 0.), 'stamp': 1e9}),
            ('negative stamp', {**_o(0, 0., 0.), 'stamp': -1}),
            ('stamp too large', {**_o(0, 0., 0.), 'stamp': 10 ** 13 + 1}),
            ('speed bound', _o(0, 2.01, 0.)), ('speed nan', _o(0, nan, 0.)),
            ('speed inf', _o(0, 0., -inf)), ('speed bool', _o(0, False, 0.)),
            ('frame type', {**_o(0, 0., 0.), 'frame_id': None}),
            ('frame too long', _o(0, 0., 0., 'f' * 33)),
            ('unknown kind', {**_o(0, 0., 0.), 'kind': 'imu'}),
            ('missing key', {k: v for k, v in _o(0, 0., 0.).items() if k != 'vr'}),
            ('extra key', {**_o(0, 0., 0.), 'extra': 1}),
            ('reset theta bound', _r(0, 0., 0., 7.)), ('reset x bound', _r(0, 1001., 0., 0.)),
            ('reset bool', _r(0, 0., 0., True)),
            ('reset with odom keys', {**_r(0, 0., 0., 0.), 'vl': 0.}),
            ('message not a dict', [1, 2, 3])):
        cases.append(('message ' + label, _cfg(), [_o(0, .1, .1), message]))
    cases.append(('messages not a list', _cfg(), 'abc'))
    cases.append(('messages dict', _cfg(), {0: _o(0, 0., 0.)}))
    cases.append(('more than 200 messages', _cfg(), [_o(i, .1, .1) for i in range(201)]))
    return cases


def _deep(value):
    if isinstance(value, dict):
        return {k: _deep(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_deep(v) for v in value]
    return value


def _subsets_by_size(n):
    masks = sorted(range(1 << n), key=lambda m: (bin(m).count('1'), m))
    return [[i for i in range(n) if m >> i & 1] for m in masks]


_CACHE = {}


def _oracle(key, config, messages):
    """High-precision reference result, computed once per case."""
    if key not in _CACHE:
        _CACHE[key] = _run(config, messages, arc=_decimal_arc)
    return _CACHE[key]


def _differs(node, config, messages):
    try:
        got = node(_deep(config), [dict(m) for m in messages])
    except Exception:
        return True
    return _same(got, _run(config, messages)) is not None


def _shortest(node, config, messages):
    """(length, set of index tuples) of shortest exposing subsequences, or None."""
    if not _differs(node, config, messages):
        return None
    best, found = None, set()
    for indices in _subsets_by_size(len(messages)):
        if best is not None and len(indices) > best:
            break
        if _differs(node, config, [messages[i] for i in indices]):
            best = len(indices)
            found.add(tuple(indices))
    return best, found


# Reproducer cases: (name, flaw or None for a valid core, config, messages).
_REPRO = [
    ('child frame ignored', 'child-ignored', _cfg(),
     [_o(0, .2, .2), _o(300, .2, .2, 'map'), _o(500, .3, .3), _o(700, .1, .1, 'odom', 'laser'),
      _o(900, .2, .2), _o(1100, .3, .3)]),
    ('dropped stale message rewinds the clock', 'ooo-rewinds-clock', _cfg(),
     [_o(1000, .2, .2), _o(800, .4, .4), _o(1500, .3, .3), _o(1900, .3, .3), _o(2300, .2, .2)]),
    ('gap test inclusive', 'gap-inclusive', _cfg(),
     [_o(0, .2, .2), _o(300, .2, .2), _o(700, .3, .3, 'map'), _o(1300, .2, .4),
      _o(1600, .2, .2)]),
    ('reset does not move the clock', 'reset-clock-kept', _cfg(),
     [_o(0, .2, .2), _o(400, .3, .3), _r(700, 1., 1., 1.), _o(900, .3, .5)]),
    ('duplicate stamp accepted', 'dup-accepted', _cfg(),
     [_o(0, .2, .2), _o(400, .3, .3), _o(400, .5, .5), _o(800, .3, .3)]),
    ('frame-dropped message rewinds the clock', 'frame-drop-rewinds-clock', _cfg(),
     [_o(0, .2, .2), _o(500, .3, .4), _o(300, .3, .3, 'map'), _o(700, .2, .4),
      _o(800, .2, .2)]),
    ('valid core', None, _cfg(),
     [_o(0, .2, .2), _o(300, .3, .3), _o(300, .1, .1), _o(900, .2, .4, 'map'),
      _o(2500, .2, .2)]),
]


def _repro_node(flaw):
    return _anonymous(_core_b) if flaw is None else _mutant(flaw)


def self_check():
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    unimplemented = set()

    def call(name, label, function, *args):
        """Run a learner function; None means it failed (already reported)."""
        if name in unimplemented:
            return None
        try:
            return (function(*args),)
        except NotImplementedError:
            unimplemented.add(name)
            failures.append(name + ": not implemented yet")
        except Exception as error:
            failures.append(label + ": your code raised " + type(error).__name__
                            + " on a valid input")
        return None

    # ---- replay_node ----
    def node_case(label, config, messages, want):
        c, m = _deep(config), _deep(messages)
        got = call('replay_node', label, replay_node, c, m)
        if got is None:
            return
        if (c, m) != (config, messages):
            failures.append(label + ": input was mutated")
            return
        problem = _same(got[0], want)
        if problem:
            failures.append(label + ": " + problem)

    for i, (tag, config, messages, poses, drops) in enumerate(_ANCHORS):
        node_case('[' + tag + '] hand anchor ' + str(i), config, messages, (poses, drops))
    for i, (tag, config, messages) in enumerate(_ORACLE):
        node_case('[' + tag + '] independent-arc case ' + str(i), config, messages,
                  _oracle(('case', i), config, messages))
    swept = []
    for seed in range(_SWEEPS):
        config, messages = _sweep_log(seed)
        got = call('replay_node', '[sweep] log ' + str(seed), replay_node,
                   _deep(config), _deep(messages))
        if got is None:
            break
        if _same(got[0], _oracle(('sweep', seed), config, messages)) is not None:
            swept.append(seed)
    if swept:
        failures.append('[sweep] ' + str(len(swept)) + ' of ' + str(_SWEEPS)
                        + ' generated mixed logs differ (first: log ' + str(swept[0]) + ')')
    config, messages, poses, drops = _ANCHORS[5][1:]
    for _ in range(2):
        got = call('replay_node', '[repeat] same log twice', replay_node,
                   _deep(config), _deep(messages))
        if got is not None and _same(got[0], (poses, drops)) is not None:
            failures.append('[repeat] calling replay_node twice on the same log '
                            'gives a different result')
            break
    for label, config, messages in _invalid_cases():
        if 'replay_node' in unimplemented:
            break
        try:
            replay_node(_deep(config), _deep(messages))
        except ValueError:
            continue
        except NotImplementedError:
            unimplemented.add('replay_node')
            failures.append('replay_node: not implemented yet')
            break
        except Exception as error:
            failures.append('[invalid] ' + label + ': raised ' + type(error).__name__
                            + ' instead of ValueError')
            continue
        failures.append('[invalid] ' + label + ': returned instead of raising ValueError')

    # ---- minimal_reproducer ----
    for i, (name, flaw, config, messages) in enumerate(_REPRO):
        label = '[reproducer] case ' + str(i)
        node = _repro_node(flaw)
        want = _shortest(node, config, messages)
        kept = _deep(messages)
        got = call('minimal_reproducer', label, minimal_reproducer, node, _deep(config), kept)
        if got is None:
            continue
        got = got[0]
        if kept != messages:
            failures.append(label + ': input was mutated')
        elif want is None:
            if got is not None:
                failures.append(label + ': node agrees with the reference; expected None')
        elif got is None:
            failures.append(label + ': returned None but the node differs')
        elif (not isinstance(got, (list, tuple))
              or any(type(v) is not int for v in got)
              or list(got) != sorted(set(got))
              or any(not 0 <= v < len(messages) for v in got)):
            failures.append(label + ': must be an increasing list of valid message indices')
        elif not _differs(node, config, [messages[v] for v in got]):
            failures.append(label + ': that subsequence does not expose the fault')
        elif len(got) != want[0]:
            failures.append(label + ': the subsequence exposes the fault but is not shortest')
    if 'minimal_reproducer' not in unimplemented:
        for label, args in (('non-callable node', (5, _cfg(), [_o(0, 0., 0.)])),
                            ('13 messages', (_anonymous(_core_b), _cfg(), [_o(i, 0., 0.) for i in range(13)]))):
            try:
                minimal_reproducer(*args)
            except ValueError:
                continue
            except Exception as error:
                failures.append('[invalid] reproducer ' + label + ': raised '
                                + type(error).__name__ + ' instead of ValueError')
                continue
            failures.append('[invalid] reproducer ' + label + ': returned instead of ValueError')

    # ---- node_tests ----
    def judge(label, core, accept):
        if 'node_tests' in unimplemented:
            return
        try:
            got = node_tests(core)
        except NotImplementedError:
            unimplemented.add('node_tests')
            failures.append('node_tests: not implemented yet')
            return
        except Exception as error:
            failures.append(label + ': your node_tests raised ' + type(error).__name__
                            + ' (catch errors from the node under test and reject it)')
            return
        if type(got) is not bool:
            failures.append(label + ': node_tests must return a bool')
        elif got != accept:
            failures.append(label + (': a valid core was rejected' if accept
                                     else ': a buggy core was accepted'))

    plan = [('[tests] valid core 1', _anonymous(_core_a), True),
            ('[tests] valid core 2', _anonymous(_core_b), True)]
    for ident, area, flaw in _MUTANTS:
        plan.append(('[tests] mutant ' + ident + ' (area ' + area + ')', _mutant(flaw), False))
    draw = _lcg(20240)
    for label, core, accept in sorted(plan, key=lambda item: draw(1000003)):
        judge(label, core, accept)
    return failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual replay-node self-check - practice only, no signed evidence")
    if failures:
        print("Failures (" + str(len(failures)) + "):")
        for line in failures:
            print("  " + line)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
