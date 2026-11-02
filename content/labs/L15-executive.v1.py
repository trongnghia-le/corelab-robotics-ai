"""CoreLab Executive and Watchdog lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
MOCK / SIMULATION MODE ONLY. This is a plain state machine for a made-up
pick-and-deliver task. It is NOT a safety function, NOT safety certification
and NOT a hazard analysis, and it must never be connected to a real robot,
gripper or emergency stop on the strength of this kit.
Implement the four functions below, then run your edited file locally:
  Windows: py -3 L15-executive.v1.py
  macOS/Linux: python3 L15-executive.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared machine. States (str):
  IDLE, APPROACH, GRASP, TRANSPORT, RELEASE, DONE, FAULT, and one hold state
  per active phase: HOLD_APPROACH, HOLD_GRASP, HOLD_TRANSPORT, HOLD_RELEASE.
  The four ACTIVE phases are APPROACH, GRASP, TRANSPORT, RELEASE. Each has an
  entry command: APPROACH move_pick, GRASP close_gripper, TRANSPORT move_drop,
  RELEASE open_gripper. These four are the MOTION commands; "stop" is the only
  other command. A HOLD_x state remembers the phase x it interrupted.
Events (str): start, reached, grasped, released, grasp_failed, obs, tick,
  cancel, fault, resume, reset. An event is a pair (t, name) with t an integer
  time in milliseconds. "obs" means a fresh observation arrived at time t;
  "tick" only lets time pass. Nothing is checked between events: a real
  watchdog needs its own timer, here the watchdog runs only when an event
  arrives.
Observation age at an event = t minus the time of the latest "obs" event
  (this event included, so an "obs" event has age 0); age is None when no obs
  has happened yet. An observation is STALE when age is None or age > max_age.
  Age exactly equal to max_age is still fresh.

transition(state, event, age, retries, max_age, max_retries)
    -> (next_state, commands, retries_next)
  One event, applied in this priority order (the first rule that applies wins):
  1. fault: every state except FAULT goes to FAULT. commands = ("stop",) only
     when the old state was an active phase (a HOLD_x or IDLE/DONE is modelled
     as not moving), else (). In FAULT it stays FAULT with (). retries unchanged.
  2. cancel: an active phase goes to IDLE with ("stop",) and retries 0; a
     HOLD_x goes to IDLE with () and retries 0; IDLE, DONE and FAULT ignore it.
  3. watchdog: if the state is an active phase and the observation is stale,
     go to HOLD_x with ("stop",); the event itself is discarded (retries
     unchanged). This applies to every event name, including "tick".
  4. otherwise the guarded table (anything not listed changes nothing, emits
     () and keeps retries - this includes obs, tick, and any event that does
     not belong to the current state):
       IDLE + start            -> APPROACH, ("move_pick",), retries 0, but only
                                  if the observation is fresh (else no change).
       APPROACH + reached      -> GRASP, ("close_gripper",)
       GRASP + grasped         -> TRANSPORT, ("move_drop",)
       GRASP + grasp_failed    -> if retries < max_retries: APPROACH,
                                  ("move_pick",), retries + 1; else FAULT,
                                  ("stop",), retries unchanged.
       TRANSPORT + reached     -> RELEASE, ("open_gripper",)
       RELEASE + released      -> DONE, ()
       HOLD_x + resume         -> only if the observation is fresh AND
                                  retries < max_retries: back to x, the entry
                                  command of x, retries + 1. Otherwise it stays
                                  in HOLD_x with () (no blind re-entry; recovery
                                  never happens by itself, only on "resume").
       FAULT + reset, DONE + reset -> IDLE, (), retries 0.
  Retry counter summary: start (accepted), reset and cancel set it to 0; fault,
  reaching DONE, the watchdog and ignored events keep it; only a grasp retry and
  a resume add 1.
  Bounds: state in the 11 names; event in the 11 names; age None or an int with
  0 <= age <= 1000000; max_age an int with 1 <= max_age <= 100000; max_retries
  an int with 0 <= max_retries <= 5; retries an int with 0 <= retries <=
  max_retries. Never bool or float. Anything else raises ValueError. Return a
  3-tuple (str, list/tuple of command str, int).

is_stale(age, max_age) -> bool
  True when age is None or age > max_age (see above); same bounds for age and
  max_age as transition. Return an actual bool.

replay(events, max_age, max_retries) -> (states, commands)
  Start in IDLE with no observation and retries 0. events is a list/tuple of 0
  to 200 pairs (t, name) with t an int, 0 <= t <= 1000000, times
  non-decreasing, name one of the 11 event names (a pair is a list or tuple of
  length 2). Apply transition() once per event, in order, tracking the latest
  obs time and the retry counter. states[i] is the state AFTER event i;
  commands[i] is the list/tuple of command names emitted while processing
  event i (maybe empty). Both have exactly len(events) entries; an empty trace
  gives ([], []). Decreasing times, bool/float/negative t, unknown names or
  more than 200 events raise ValueError. max_age and max_retries have the
  bounds above. Never mutate the inputs. The result must be a pair of
  list/tuple values.

unsafe_motion_indices(events, commands, max_age) -> list of int
  A trace monitor, independent of any state machine: it sees only the events
  and the commands that were emitted for each of them (commands[i] is a
  list/tuple of command names for event i, same length as events, at most 10 names per event, every name
  one of move_pick, close_gripper, move_drop, open_gripper, stop). Return, in
  increasing order, every index i such that commands[i] contains a MOTION
  command AND at least one of these holds at event i:
    * stale: the observation age at event i (obs at i included) is None or
      greater than max_age;
    * the event itself is "cancel" or "fault";
    * latched fault: a "fault" event occurred at or before i and no "reset"
      event has occurred since (a "reset" at i itself clears it);
    * cancelled: a "cancel" event occurred at or before i and no "start"
      event has occurred since (a "start" at i itself counts as since).
  "stop" is never unsafe. Same event and max_age bounds as replay; invalid
  events, commands of the wrong shape or length, unknown command names raise
  ValueError. Never mutate the inputs. This is the invariant "no motion
  command while stale, cancelled or faulted".

Pause before coding - write your predictions down first:
  1. The newest obs is exactly max_age old when an event arrives. Is the
     machine allowed to move? What changes at max_age + 1?
  2. A "reached" event arrives while the observation is stale and the state is
     TRANSPORT. Does the machine go to RELEASE? What is emitted, how many times?
  3. A cancel arrives in HOLD_GRASP, then a fault in FAULT. Which of them must
     emit "stop", and why is a second "stop" not needed?
  4. The machine is in HOLD_APPROACH and a fresh obs arrives. Should it go back
     to APPROACH by itself? Which event and which guards decide the recovery?
  5. With max_retries = 1, how many times can a failed grasp be retried, and
     does a resume from a hold use the same budget? What happens at the limit?
  6. Which unsafe traces would the monitor miss if it looked only at staleness
     (not at cancel and fault)?
Self-check tolerances: exact equality for names, commands and counters. Failure
messages name the case and the kind of mismatch, never the expected values.
"your code raised X" means your function raised on a VALID input; "invalid
f(name=...)" lines are the opposite: that input must raise ValueError. A
function still raising NotImplementedError is reported once. Sweeps report one
line with a count and the first failing input.
This kit covers a deterministic, timestamped, plain state machine only: no
behaviour-tree library, no ROS or real-time timing, no hardware, no real
emergency stop, no certification, no automatic hazard analysis.
Reflection: why does passing this toy NOT make a robot safe? (Think about who
reviews the hazards, failures of the watchdog or clock itself, a stop command
that is sent but not obeyed, sensors that lie while looking fresh, timing
between events, hardware safety functions and standards, and recovering from a
hold with the gripper holding an object.)
"""

STATES = ("IDLE", "APPROACH", "GRASP", "TRANSPORT", "RELEASE", "DONE", "FAULT",
          "HOLD_APPROACH", "HOLD_GRASP", "HOLD_TRANSPORT", "HOLD_RELEASE")
EVENTS = ("start", "reached", "grasped", "released", "grasp_failed", "obs", "tick",
          "cancel", "fault", "resume", "reset")
MOTION = ("move_pick", "close_gripper", "move_drop", "open_gripper")


def is_stale(age, max_age):
    raise NotImplementedError("Stale means no observation yet, or older than max_age (equal is fresh)")


def transition(state, event, age, retries, max_age, max_retries):
    raise NotImplementedError("Apply fault, cancel, watchdog, then the guarded table, in that order")


def replay(events, max_age, max_retries):
    raise NotImplementedError("Track the latest obs time and the retry counter; apply transition per event")


def unsafe_motion_indices(events, commands, max_age):
    raise NotImplementedError("A monitor over events and commands only: stale, cancel/fault, latched fault, cancelled")


# ---- SPOILER BELOW: the _..._ref functions are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


_TMAX = 1000000
_ENTRY = {"APPROACH": "move_pick", "GRASP": "close_gripper",
          "TRANSPORT": "move_drop", "RELEASE": "open_gripper"}
_COMMANDS = MOTION + ("stop",)


def _int(value, low, high):
    return type(value) is int and low <= value <= high


def _check_age(age):
    if age is not None and not _int(age, 0, _TMAX):
        raise ValueError("age")


def _check_max_age(max_age):
    if not _int(max_age, 1, 100000):
        raise ValueError("max_age")


def _check_max_retries(max_retries):
    if not _int(max_retries, 0, 5):
        raise ValueError("max_retries")


def _stale_ref(age, max_age):
    _check_age(age)
    _check_max_age(max_age)
    return age is None or age > max_age


def _transition_ref(state, event, age, retries, max_age, max_retries):
    if type(state) is not str or state not in STATES:
        raise ValueError("state")
    if type(event) is not str or event not in EVENTS:
        raise ValueError("event")
    _check_age(age)
    _check_max_age(max_age)
    _check_max_retries(max_retries)
    if not _int(retries, 0, max_retries):
        raise ValueError("retries")
    active = state in _ENTRY
    stale = age is None or age > max_age
    if event == "fault":
        if state == "FAULT":
            return ("FAULT", (), retries)
        return ("FAULT", ("stop",) if active else (), retries)
    if event == "cancel":
        if active:
            return ("IDLE", ("stop",), 0)
        if state.startswith("HOLD_"):
            return ("IDLE", (), 0)
        return (state, (), retries)
    if active and stale:
        return ("HOLD_" + state, ("stop",), retries)
    if state == "IDLE" and event == "start":
        if stale:
            return (state, (), retries)
        return ("APPROACH", ("move_pick",), 0)
    if state == "APPROACH" and event == "reached":
        return ("GRASP", ("close_gripper",), retries)
    if state == "GRASP" and event == "grasped":
        return ("TRANSPORT", ("move_drop",), retries)
    if state == "GRASP" and event == "grasp_failed":
        if retries < max_retries:
            return ("APPROACH", ("move_pick",), retries + 1)
        return ("FAULT", ("stop",), retries)
    if state == "TRANSPORT" and event == "reached":
        return ("RELEASE", ("open_gripper",), retries)
    if state == "RELEASE" and event == "released":
        return ("DONE", (), retries)
    if state.startswith("HOLD_") and event == "resume":
        if not stale and retries < max_retries:
            phase = state[5:]
            return (phase, (_ENTRY[phase],), retries + 1)
        return (state, (), retries)
    if state in ("FAULT", "DONE") and event == "reset":
        return ("IDLE", (), 0)
    return (state, (), retries)


def _events_ref(events):
    if not isinstance(events, (list, tuple)) or len(events) > 200:
        raise ValueError("events")
    out = []
    last = 0
    for pair in events:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("event pair")
        t, name = pair
        if not _int(t, 0, _TMAX) or type(name) is not str or name not in EVENTS:
            raise ValueError("event pair")
        if t < last:
            raise ValueError("times must not decrease")
        last = t
        out.append((t, name))
    return out


def _replay_ref(events, max_age, max_retries):
    pairs = _events_ref(events)
    _check_max_age(max_age)
    _check_max_retries(max_retries)
    state, retries, last_obs = "IDLE", 0, None
    states, commands = [], []
    for t, name in pairs:
        if name == "obs":
            last_obs = t
        age = None if last_obs is None else t - last_obs
        state, cmds, retries = _transition_ref(state, name, age, retries, max_age, max_retries)
        states.append(state)
        commands.append(list(cmds))
    return states, commands


def _unsafe_ref(events, commands, max_age):
    pairs = _events_ref(events)
    _check_max_age(max_age)
    if not isinstance(commands, (list, tuple)) or len(commands) != len(pairs):
        raise ValueError("commands")
    for cmds in commands:
        if not isinstance(cmds, (list, tuple)) or len(cmds) > 10:
            raise ValueError("commands")
        for c in cmds:
            if type(c) is not str or c not in _COMMANDS:
                raise ValueError("commands")
    last_obs, faulted, cancelled, out = None, False, False, []
    for i, (t, name) in enumerate(pairs):
        if name == "obs":
            last_obs = t
        elif name == "fault":
            faulted = True
        elif name == "reset":
            faulted = False
        elif name == "cancel":
            cancelled = True
        elif name == "start":
            cancelled = False
        stale = last_obs is None or t - last_obs > max_age
        if any(c in MOTION for c in commands[i]) and (stale or faulted or cancelled):
            out.append(i)
    return out


_MP, _CG, _MD, _OG, _ST = "move_pick", "close_gripper", "move_drop", "open_gripper", "stop"
# transition(state, event, age, retries, max_age, max_retries) -> (next, commands, retries_next)
_T_CASES = [
    (("IDLE", "start", 0, 0, 5, 2), ("APPROACH", (_MP,), 0)),
    (("IDLE", "start", 5, 0, 5, 2), ("APPROACH", (_MP,), 0)),
    (("IDLE", "start", 6, 0, 5, 2), ("IDLE", (), 0)),
    (("IDLE", "start", None, 0, 5, 2), ("IDLE", (), 0)),
    (("APPROACH", "reached", 2, 0, 5, 2), ("GRASP", (_CG,), 0)),
    (("GRASP", "grasped", 2, 1, 5, 2), ("TRANSPORT", (_MD,), 1)),
    (("TRANSPORT", "reached", 2, 2, 5, 2), ("RELEASE", (_OG,), 2)),
    (("RELEASE", "released", 0, 0, 5, 2), ("DONE", (), 0)),
    (("GRASP", "grasp_failed", 1, 0, 5, 2), ("APPROACH", (_MP,), 1)),
    (("GRASP", "grasp_failed", 1, 1, 5, 2), ("APPROACH", (_MP,), 2)),
    (("GRASP", "grasp_failed", 1, 2, 5, 2), ("FAULT", (_ST,), 2)),
    (("GRASP", "grasp_failed", 1, 0, 5, 0), ("FAULT", (_ST,), 0)),
    (("APPROACH", "reached", 6, 0, 5, 2), ("HOLD_APPROACH", (_ST,), 0)),
    (("TRANSPORT", "tick", 6, 1, 5, 2), ("HOLD_TRANSPORT", (_ST,), 1)),
    (("TRANSPORT", "tick", 5, 1, 5, 2), ("TRANSPORT", (), 1)),
    (("GRASP", "grasped", None, 0, 5, 2), ("HOLD_GRASP", (_ST,), 0)),
    (("RELEASE", "released", 9, 0, 5, 2), ("HOLD_RELEASE", (_ST,), 0)),
    (("APPROACH", "cancel", 0, 0, 5, 2), ("IDLE", (_ST,), 0)),
    (("GRASP", "cancel", 0, 2, 5, 2), ("IDLE", (_ST,), 0)),
    (("TRANSPORT", "cancel", 9, 1, 5, 2), ("IDLE", (_ST,), 0)),
    (("APPROACH", "cancel", None, 0, 5, 2), ("IDLE", (_ST,), 0)),
    (("HOLD_GRASP", "cancel", 9, 1, 5, 2), ("IDLE", (), 0)),
    (("IDLE", "cancel", 0, 0, 5, 2), ("IDLE", (), 0)),
    (("DONE", "cancel", 0, 1, 5, 2), ("DONE", (), 1)),
    (("FAULT", "cancel", 0, 2, 5, 2), ("FAULT", (), 2)),
    (("APPROACH", "fault", 0, 0, 5, 2), ("FAULT", (_ST,), 0)),
    (("GRASP", "fault", 9, 1, 5, 2), ("FAULT", (_ST,), 1)),
    (("HOLD_TRANSPORT", "fault", 0, 1, 5, 2), ("FAULT", (), 1)),
    (("IDLE", "fault", None, 0, 5, 2), ("FAULT", (), 0)),
    (("DONE", "fault", 0, 0, 5, 2), ("FAULT", (), 0)),
    (("FAULT", "fault", 0, 2, 5, 2), ("FAULT", (), 2)),
    (("HOLD_GRASP", "resume", 0, 0, 5, 2), ("GRASP", (_CG,), 1)),
    (("HOLD_APPROACH", "resume", 2, 1, 5, 2), ("APPROACH", (_MP,), 2)),
    (("HOLD_RELEASE", "resume", 5, 0, 5, 2), ("RELEASE", (_OG,), 1)),
    (("HOLD_TRANSPORT", "resume", 0, 0, 5, 2), ("TRANSPORT", (_MD,), 1)),
    (("HOLD_TRANSPORT", "resume", 0, 2, 5, 2), ("HOLD_TRANSPORT", (), 2)),
    (("HOLD_RELEASE", "resume", 6, 0, 5, 2), ("HOLD_RELEASE", (), 0)),
    (("HOLD_GRASP", "resume", None, 0, 5, 2), ("HOLD_GRASP", (), 0)),
    (("HOLD_GRASP", "resume", 0, 0, 5, 0), ("HOLD_GRASP", (), 0)),
    (("HOLD_GRASP", "obs", 0, 0, 5, 2), ("HOLD_GRASP", (), 0)),
    (("HOLD_TRANSPORT", "reached", 0, 0, 5, 2), ("HOLD_TRANSPORT", (), 0)),
    (("FAULT", "reset", 0, 2, 5, 2), ("IDLE", (), 0)),
    (("DONE", "reset", 9, 1, 5, 2), ("IDLE", (), 0)),
    (("IDLE", "reset", 0, 0, 5, 2), ("IDLE", (), 0)),
    (("FAULT", "start", 0, 0, 5, 2), ("FAULT", (), 0)),
    (("APPROACH", "start", 0, 1, 5, 2), ("APPROACH", (), 1)),
    (("APPROACH", "grasped", 1, 0, 5, 2), ("APPROACH", (), 0)),
    (("APPROACH", "resume", 1, 0, 5, 2), ("APPROACH", (), 0)),
    (("DONE", "start", 0, 0, 5, 2), ("DONE", (), 0)),
    (("IDLE", "tick", None, 0, 5, 2), ("IDLE", (), 0)),
    (("GRASP", "obs", 0, 1, 5, 2), ("GRASP", (), 1)),
]
_STALE_CASES = [
    ((None, 5), True), ((0, 5), False), ((4, 5), False), ((5, 5), False), ((6, 5), True),
    ((100, 5), True), ((0, 1), False), ((1, 1), False), ((2, 1), True), ((None, 1), True),
]
_O, _S = (0, "obs"), (0, "start")
# replay(events, max_age, max_retries) -> (states, commands)
_R_CASES = [
    (([], 5, 1), ([], [])),
    ((((0, "obs"), (1, "start"), (2, "reached"), (3, "grasped"), (4, "obs"), (5, "reached"), (6, "released")), 5, 1),
     (["IDLE", "APPROACH", "GRASP", "TRANSPORT", "TRANSPORT", "RELEASE", "DONE"],
      [[], [_MP], [_CG], [_MD], [], [_OG], []])),
    ((((0, "obs"), (1, "start"), (7, "tick"), (8, "reached")), 5, 1),
     (["IDLE", "APPROACH", "HOLD_APPROACH", "HOLD_APPROACH"], [[], [_MP], [_ST], []])),
    ((((0, "obs"), (0, "start"), (5, "tick"), (6, "tick")), 5, 1),
     (["IDLE", "APPROACH", "APPROACH", "HOLD_APPROACH"], [[], [_MP], [], [_ST]])),
    ((((0, "obs"), (0, "start"), (6, "tick"), (6, "resume"), (6, "obs"), (6, "resume"), (7, "reached")), 5, 1),
     (["IDLE", "APPROACH", "HOLD_APPROACH", "HOLD_APPROACH", "HOLD_APPROACH", "APPROACH", "GRASP"],
      [[], [_MP], [_ST], [], [], [_MP], [_CG]])),
    ((((0, "obs"), (0, "start"), (1, "reached"), (2, "grasp_failed"), (3, "reached"), (4, "grasp_failed")), 5, 1),
     (["IDLE", "APPROACH", "GRASP", "APPROACH", "GRASP", "FAULT"],
      [[], [_MP], [_CG], [_MP], [_CG], [_ST]])),
    ((((0, "obs"), (0, "start"), (6, "tick"), (6, "obs"), (6, "resume"), (7, "tick"), (13, "tick"), (13, "obs"), (13, "resume")), 5, 1),
     (["IDLE", "APPROACH", "HOLD_APPROACH", "HOLD_APPROACH", "APPROACH", "APPROACH", "HOLD_APPROACH",
       "HOLD_APPROACH", "HOLD_APPROACH"],
      [[], [_MP], [_ST], [], [_MP], [], [_ST], [], []])),
    ((((0, "obs"), (0, "start"), (1, "reached"), (2, "grasped"), (3, "cancel"), (4, "reached"), (5, "start")), 5, 1),
     (["IDLE", "APPROACH", "GRASP", "TRANSPORT", "IDLE", "IDLE", "APPROACH"],
      [[], [_MP], [_CG], [_MD], [_ST], [], [_MP]])),
    ((((0, "obs"), (0, "start"), (1, "fault"), (2, "obs"), (2, "start"), (3, "reset"), (3, "start")), 5, 1),
     (["IDLE", "APPROACH", "FAULT", "FAULT", "FAULT", "IDLE", "APPROACH"],
      [[], [_MP], [_ST], [], [], [], [_MP]])),
    ((((0, "start"), (1, "tick"), (2, "obs"), (2, "start")), 5, 1),
     (["IDLE", "IDLE", "IDLE", "APPROACH"], [[], [], [], [_MP]])),
    ((((0, "obs"), (0, "start"), (1, "reached"), (1, "grasped"), (2, "reached"), (9, "released")), 5, 1),
     (["IDLE", "APPROACH", "GRASP", "TRANSPORT", "RELEASE", "HOLD_RELEASE"],
      [[], [_MP], [_CG], [_MD], [_OG], [_ST]])),
    ((((0, "obs"), (0, "start"), (9, "fault")), 5, 1),
     (["IDLE", "APPROACH", "FAULT"], [[], [_MP], [_ST]])),
    ((((0, "obs"), (0, "start"), (9, "cancel")), 5, 1),
     (["IDLE", "APPROACH", "IDLE"], [[], [_MP], [_ST]])),
    ((((0, "obs"), (0, "start"), (0, "reached"), (0, "grasp_failed"), (0, "reached"), (0, "grasp_failed")), 5, 0),
     (["IDLE", "APPROACH", "GRASP", "FAULT", "FAULT", "FAULT"],
      [[], [_MP], [_CG], [_ST], [], []])),
]
_E1 = ((0, "obs"), (1, "start"), (2, "reached"), (3, "grasped"), (4, "reached"), (5, "released"))
_E2 = ((0, "obs"), (1, "start"), (9, "tick"))
_E3 = ((0, "obs"), (0, "start"), (1, "cancel"))
_E4 = ((0, "obs"), (0, "start"), (1, "cancel"), (1, "tick"))
_E5 = ((0, "obs"), (0, "start"), (1, "fault"), (2, "tick"))
# unsafe_motion_indices(events, commands, max_age) -> list of indices
_U_CASES = [
    ((_E1, ([], [_MP], [_CG], [_MD], [_OG], []), 5), []),
    ((_E2, ([], [_MP], [_MP]), 5), [2]),
    ((_E2, ([], [_MP], [_ST]), 5), []),
    ((((0, "obs"), (0, "start"), (5, "tick")), ([], [_MP], [_MP]), 5), []),
    ((((0, "obs"), (0, "start"), (6, "tick")), ([], [_MP], [_MP]), 5), [2]),
    ((_E3, ([], [_MP], [_MP]), 5), [2]),
    ((_E3, ([], [_MP], [_ST]), 5), []),
    ((_E4, ([], [_MP], [_ST], [_MD]), 5), [3]),
    ((_E4, ([], [_MP], [_ST], [_ST]), 5), []),
    ((((0, "obs"), (0, "start"), (1, "cancel"), (1, "start"), (1, "tick")), ([], [_MP], [_ST], [_MP], [_MP]), 5), []),
    ((_E5, ([], [_MP], [_ST], [_MP]), 5), [3]),
    ((((0, "obs"), (0, "start"), (1, "fault"), (2, "reset"), (2, "tick")), ([], [_MP], [_ST], [], [_MD]), 5), []),
    ((((0, "obs"), (0, "start"), (1, "fault"), (1, "obs"), (2, "tick")), ([], [_MP], [_ST], [], [_MD]), 5), [4]),
    ((((0, "start"),), ([_MP],), 5), [0]),
    ((((0, "obs"), (0, "start"), (9, "tick")), ([], [_MP], [_CG, _ST]), 5), [2]),
    ((((0, "obs"), (3, "tick"), (3, "start")), ([], [], [_MP]), 2), [2]),
    ((((0, "obs"), (2, "tick"), (2, "start")), ([], [], [_MP]), 2), []),
    ((((0, "obs"), (0, "start"), (1, "fault"), (1, "reset"), (1, "start")), ([], [_MP], [_ST], [], [_MP]), 5), []),
    (((), (), 5), []),
]


def _fresh(value):
    """Nested list copy of a tuple table entry, so mutation can be detected."""
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _frozen(value):
    if isinstance(value, (list, tuple)):
        return tuple(_frozen(v) for v in value)
    return value


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return text + ": over-strict validation?)"
    return text + ")"


def _names(value):
    """Normalise a returned command collection to a list of str, or raise _Mismatch."""
    if not isinstance(value, (list, tuple)) or any(type(c) is not str for c in value):
        raise _Mismatch("commands must be a list/tuple of command names (str)")
    return list(value)


def _norm_replay(got):
    if not isinstance(got, (list, tuple)) or len(got) != 2:
        raise _Mismatch("replay must return a pair (states, commands)")
    states, commands = got
    if not isinstance(states, (list, tuple)) or any(type(s) is not str for s in states):
        raise _Mismatch("states must be a list/tuple of state names (str)")
    if not isinstance(commands, (list, tuple)):
        raise _Mismatch("commands must be a list/tuple with one entry per event")
    return list(states), [_names(c) for c in commands]


def _norm_transition(got):
    if not isinstance(got, (list, tuple)) or len(got) != 3:
        raise _Mismatch("transition must return (next_state, commands, retries_next)")
    state, commands, retries = got
    if type(state) is not str:
        raise _Mismatch("next_state must be a state name (str)")
    if type(retries) is not int:
        raise _Mismatch("retries_next must be an int")
    return state, _names(commands), retries


_MEMO = {}
_STRIDE, _RANDOM, _PAIRS = 1, 400, 300  # the author fixture lowers these for its fast mutant pass


class _Lcg:
    def __init__(self, seed):
        self.state = seed

    def below(self, n):
        self.state = (self.state*1103515245 + 12345) % 2147483648
        return (self.state >> 8) % n


_FLOW = {"IDLE": ("obs", "start"), "APPROACH": ("reached",), "GRASP": ("grasped", "grasp_failed"),
         "TRANSPORT": ("reached",), "RELEASE": ("released",), "DONE": ("reset",), "FAULT": ("reset",)}


def _random_traces(count, seed):
    """Deterministic traces guided by the reference machine so deep states are reached."""
    rng = _Lcg(seed)
    out = []
    for _ in range(count):
        max_age = 2 + rng.below(2)
        max_retries = rng.below(3)
        events, t, state, retries, last = [], 0, "IDLE", 0, None
        for _ in range(14):
            t += (0, 0, 1, 1, 2, 3, 4)[rng.below(7)]
            if rng.below(100) < 65:
                if state.startswith("HOLD_"):
                    name = ("obs", "resume")[rng.below(2)]
                else:
                    pool = _FLOW[state]
                    name = pool[rng.below(len(pool))]
                    if rng.below(5) == 0:
                        name = "obs"
            else:
                name = EVENTS[rng.below(len(EVENTS))]
            events.append((t, name))
            if name == "obs":
                last = t
            age = None if last is None else t - last
            state, _, retries = _transition_ref(state, name, age, retries, max_age, max_retries)
        out.append((tuple(events), max_age, max_retries))
    return out


_PREFIXES = {
    "start": [],
    "obs": [(0, "obs")],
    "approach": [(0, "obs"), (0, "start")],
    "grasp": [(0, "obs"), (0, "start"), (0, "reached")],
    "transport": [(0, "obs"), (0, "start"), (0, "reached"), (0, "grasped")],
    "release": [(0, "obs"), (0, "start"), (0, "reached"), (0, "grasped"), (0, "reached")],
    "done": [(0, "obs"), (0, "start"), (0, "reached"), (0, "grasped"), (0, "reached"), (0, "released")],
    "fault": [(0, "obs"), (0, "fault")],
    "hold-approach": [(0, "obs"), (0, "start"), (3, "tick")],
    "hold-grasp": [(0, "obs"), (0, "start"), (0, "reached"), (3, "tick")],
    "hold-transport": [(0, "obs"), (0, "start"), (0, "reached"), (0, "grasped"), (3, "tick")],
    "hold-release": [(0, "obs"), (0, "start"), (0, "reached"), (0, "grasped"), (0, "reached"), (3, "tick")],
    "retried-grasp": [(0, "obs"), (0, "start"), (0, "reached"), (0, "grasp_failed"), (0, "reached")],
    "retried-hold": [(0, "obs"), (0, "start"), (0, "reached"), (0, "grasp_failed"), (3, "tick")],
}


def _exhaustive_traces():
    """Every prefix followed by every 1- or 2-event suffix; gaps 0, max_age, max_age + 1."""
    symbols = [(gap, name) for name in EVENTS for gap in (0, 2, 3)]
    for label, prefix in _PREFIXES.items():
        base = prefix[-1][0] if prefix else 0
        for first in symbols:
            yield label, tuple(prefix) + ((base + first[0], first[1]),)
            for second in symbols:
                yield label, (tuple(prefix) + ((base + first[0], first[1]),
                                               (base + first[0] + second[0], second[1])))


def _random_pairs(count, seed):
    """Random (events, commands, max_age) triples, some safe and some unsafe."""
    rng = _Lcg(seed)
    out = []
    for _ in range(count):
        events, commands, t = [], [], 0
        for _ in range(8):
            t += (0, 0, 1, 2, 3)[rng.below(5)]
            events.append((t, EVENTS[rng.below(len(EVENTS))]))
            kind = rng.below(5)
            commands.append([] if kind < 2 else [_COMMANDS[rng.below(len(_COMMANDS))]]
                            if kind < 4 else [_ST, MOTION[rng.below(4)]])
        out.append((tuple(events), tuple(tuple(c) for c in commands), 1 + rng.below(3)))
    return out


def _bad_cases():
    ok_events = ((0, "obs"), (1, "start"))
    ok_cmds = ([], [_MP])
    cases = []
    for bad in (True, -1, 1.5, "3", 1000001, [3]):
        cases.append(("is_stale(age=" + repr(bad) + ")", "is_stale", (bad, 5)))
    for bad in (0, True, 3.0, 100001, None, -2, "5"):
        cases.append(("is_stale(max_age=" + repr(bad) + ")", "is_stale", (2, bad)))
    base = ["APPROACH", "reached", 1, 0, 5, 2]

    def with_(index, value):
        args = list(base)
        args[index] = value
        return tuple(args)
    for bad in ("idle", "Approach", 3, None, "HOLD", ["IDLE"]):
        cases.append(("transition(state=" + repr(bad) + ")", "transition", with_(0, bad)))
    for bad in ("Start", "go", None, 4, ["tick"], ""):
        cases.append(("transition(event=" + repr(bad) + ")", "transition", with_(1, bad)))
    for bad in (-1, True, 2.5, "1", 1000001, False):
        cases.append(("transition(age=" + repr(bad) + ")", "transition", with_(2, bad)))
    for bad in (-1, 3, True, 1.0, None, "0"):
        cases.append(("transition(retries=" + repr(bad) + ")", "transition", with_(3, bad)))
    for bad in (0, True, 5.0, 100001, None):
        cases.append(("transition(max_age=" + repr(bad) + ")", "transition", with_(4, bad)))
    for bad in (-1, 6, True, 1.5, None):
        cases.append(("transition(max_retries=" + repr(bad) + ")", "transition", with_(5, bad)))
    for label, bad in (("a string", "obs"), ("None", None), ("a dict", {}), ("a number", 3)):
        cases.append(("replay(events=" + label + ")", "replay", (bad, 5, 1)))
        cases.append(("unsafe_motion_indices(events=" + label + ")", "unsafe_motion_indices", (bad, [], 5)))
    pair_bad = [("triple", ((0, "obs", 1),)), ("single", ((0,),)), ("not a pair", ("obs",)),
                ("bool time", ((True, "obs"),)), ("float time", ((1.0, "obs"),)),
                ("negative time", ((-1, "obs"),)), ("huge time", ((1000001, "obs"),)),
                ("unknown name", ((0, "go"),)), ("name not str", ((0, 3),)), ("name is a list", ((0, ["obs"]),)),
                ("decreasing times", ((2, "obs"), (1, "tick"))), ("capital name", ((0, "Obs"),)),
                ("string time", (("0", "obs"),)), ("201 events", tuple((0, "tick") for _ in range(201)))]
    for label, bad in pair_bad:
        cases.append(("replay(" + label + ")", "replay", (bad, 5, 1)))
        cases.append(("unsafe_motion_indices(" + label + ")", "unsafe_motion_indices",
                      (bad, tuple([] for _ in bad), 5)))
    for bad in (0, True, 5.0, 100001, None):
        cases.append(("replay(max_age=" + repr(bad) + ")", "replay", (ok_events, bad, 1)))
        cases.append(("unsafe_motion_indices(max_age=" + repr(bad) + ")", "unsafe_motion_indices",
                      (ok_events, ok_cmds, bad)))
    for bad in (-1, 6, True, 1.5, None):
        cases.append(("replay(max_retries=" + repr(bad) + ")", "replay", (ok_events, 5, bad)))
    cmd_bad = [("too few command lists", ([],)), ("too many command lists", ([], [], [])),
               ("unknown command", ([], ["fly"])), ("command not str", ([], [3])),
               ("entry is a string", ([], "stop")), ("entry is None", ([], None)),
               ("commands is a string", "ab"), ("commands is None", None),
               ("capital command", ([], ["Stop"]))]
    for label, bad in cmd_bad:
        cases.append(("unsafe_motion_indices(" + label + ")", "unsafe_motion_indices", (ok_events, bad, 5)))
    return cases


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    calls, missing = {}, {}

    def attempt(name, label, args, frozen=False):
        calls[name] = calls.get(name, 0) + 1
        live = _frozen(args) if frozen else _fresh(args)
        snapshot = repr(live)
        try:
            got = globals()[name](*live)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            return False, None
        except Exception as error:
            failures.append(label + ": " + _raised(error))
            return False, None
        if repr(live) != snapshot:
            failures.append(label + ": modified its input (inputs must never be mutated)")
        return True, got

    def run(name, label, args, compare, frozen=False):
        ok, got = attempt(name, label, args, frozen)
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def cmp_bool(want):
        def compare(got):
            if type(got) is not bool:
                raise _Mismatch("must return a real bool")
            if got != want:
                raise _Mismatch("wrong answer")
        return compare

    def cmp_transition(want):
        def compare(got):
            state, commands, retries = _norm_transition(got)
            if state != want[0]:
                raise _Mismatch("next_state is wrong")
            if commands != list(want[1]):
                raise _Mismatch("emitted commands are wrong")
            if retries != want[2]:
                raise _Mismatch("retries_next is wrong")
        return compare

    def cmp_replay(want):
        def compare(got):
            states, commands = _norm_replay(got)
            if len(states) != len(want[0]) or len(commands) != len(want[1]):
                raise _Mismatch("states and commands need one entry per event")
            for i, (a, b) in enumerate(zip(states, want[0])):
                if a != b:
                    raise _Mismatch("state after event " + str(i) + " is wrong")
            for i, (a, b) in enumerate(zip(commands, want[1])):
                if a != b:
                    raise _Mismatch("commands emitted at event " + str(i) + " are wrong")
        return compare

    def cmp_indices(want):
        def compare(got):
            if not isinstance(got, (list, tuple)) or any(type(i) is not int for i in got):
                raise _Mismatch("must return a list of int indices")
            if list(got) != want:
                raise _Mismatch("wrong set of unsafe indices (or not in increasing order)")
        return compare

    for i, (args, want) in enumerate(_STALE_CASES):
        run("is_stale", "is_stale case " + str(i), args, cmp_bool(want))
    for i, (args, want) in enumerate(_T_CASES):
        run("transition", "transition case " + str(i) + " (" + args[0] + " + " + args[1] + ")", args,
            cmp_transition(want))
    for i, (args, want) in enumerate(_R_CASES):
        for frozen in (False, True):
            run("replay", "replay case " + str(i) + (" (tuples)" if frozen else ""), args,
                cmp_replay(want), frozen)
    for i, (args, want) in enumerate(_U_CASES):
        for frozen in (False, True):
            run("unsafe_motion_indices", "unsafe_motion_indices case " + str(i) + (" (tuples)" if frozen else ""),
                args, cmp_indices(want), frozen)

    def sweep(name, label, cases, call, compare):
        """One line with a count and the first failing input, never the expected value."""
        if name in missing:
            return
        total = bad = 0
        first = None
        raised = None
        for args in cases:
            total += 1
            calls[name] = calls.get(name, 0) + 1
            try:
                got = call(*args)
                compare(args, got)
            except NotImplementedError:
                missing.setdefault(name, []).append(label)
                return
            except _Mismatch as error:
                bad += 1
                if first is None:
                    first = (args, str(error))
            except Exception as error:
                bad += 1
                raised = raised or type(error).__name__
                if first is None:
                    first = (args, "your code raised " + type(error).__name__)
        if bad:
            failures.append(label + ": " + str(bad) + " of " + str(total) + " valid cases wrong; first: "
                            + first[1] + " for input " + repr(first[0]))

    ages = (None, 0, 3, 4, 5, 9)
    if "sweep_t" not in _MEMO:
        _MEMO["sweep_t"] = [(s, e, a, r, 4, mr) for mr in (0, 2) for s in STATES for e in EVENTS for a in ages
                            for r in range(mr + 1)]
    sweep_t = _MEMO["sweep_t"]
    sweep("transition", "transition sweep over every (state, event, age, retries)", sweep_t, transition,
          lambda args, got: cmp_transition(_transition_ref(*args))(got))
    sweep_s = [(a, m) for m in (1, 3, 5) for a in (None, 0, 1, 2, 3, 4, 5, 6, 7, 100)]
    sweep("is_stale", "is_stale sweep", sweep_s, is_stale, lambda args, got: cmp_bool(_stale_ref(*args))(got))

    if "traces" not in _MEMO:
        _MEMO["traces"] = [(tuple(trace), 2, 1) for _, trace in _exhaustive_traces()]
    traces = _MEMO["traces"][::_STRIDE]
    if ("random", _RANDOM) not in _MEMO:
        _MEMO[("random", _RANDOM)] = _random_traces(_RANDOM, 1515)
    random_traces = _MEMO[("random", _RANDOM)]
    def expected_replay(args):
        if args not in _MEMO:
            _MEMO[args] = _replay_ref(*args)
        return _MEMO[args]

    sweep("replay", "replay exhaustive sweep (every state, every 1-2 event suffix)", traces, replay,
          lambda args, got: cmp_replay(expected_replay(args))(got))
    sweep("replay", "replay random-trace sweep", random_traces, replay,
          lambda args, got: cmp_replay(expected_replay(args))(got))

    def invariant(args, got):
        states, commands = _norm_replay(got)
        if len(commands) == len(args[0]) and _unsafe_ref(args[0], commands, args[1]):
            raise _Mismatch("emitted a motion command while stale, cancelled or faulted")
    sweep("replay", "replay safety invariant over the same traces", traces[::6] + random_traces, replay, invariant)
    sweep("unsafe_motion_indices", "unsafe_motion_indices random-trace sweep", _random_pairs(_PAIRS, 777),
          unsafe_motion_indices, lambda args, got: cmp_indices(_unsafe_ref(*args))(got))

    for label, name, args in _bad_cases():
        calls[name] = calls.get(name, 0) + 1
        live = _fresh(args)
        try:
            globals()[name](*live)
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            continue
        except Exception as error:
            failures.append("invalid " + label + ": raised " + type(error).__name__ + " instead of ValueError")
            continue
        failures.append("invalid " + label + ": returned instead of raising ValueError")
    summary = []
    for name, labels in missing.items():
        if len(labels) < calls[name]:
            summary.append(name + ": raised NotImplementedError in " + str(len(labels)) + " of "
                           + str(calls[name]) + " checks (first: " + labels[0] + "); finish it")
        else:
            summary.append(name + ": not implemented yet (raises NotImplementedError; "
                           + str(calls[name]) + " checks skipped)")
    return summary + failures


if __name__ == "__main__":
    notes = []
    failures = self_check(notes)
    print("CoreLab manual executive / watchdog self-check - mock simulation practice only, no signed evidence")
    for note in notes:
        print("Note: " + note)
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
