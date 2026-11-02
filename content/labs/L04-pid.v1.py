"""CoreLab Bounded feedback lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the four functions below, then run your edited file locally:
  Windows: py -3 L04-pid.v1.py
  macOS/Linux: python3 L04-pid.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared toy plant (numerical practice, not a motor, torque or hardware model):
a wheel speed y in m/s follows the discrete-time integrator
    y[k+1] = y[k] + h*(u[k] + d)
u[k] is the applied acceleration command in m/s^2, h the step in seconds and d
a constant, known disturbance acceleration in m/s^2 (d = 0 is the X13 model).
Error sign: e = r - y (reference minus output); a positive u raises y.
Only the command is bounded: u = clip(v, -limit, limit) for the raw command v.
Nothing else is clipped: y_next, the raw command v and integral_next are never
clipped, and outputs may exceed the input bounds below. The bounds only decide
which INPUTS are valid (for example an input integral beyond 1e9 is invalid).

Contracts (all numbers finite int/float, never bool; bounds inclusive):
  p_step(y, r, kp, limit, h, d=0) -> (u, y_next)                       EXACT
      v = kp*e,  u = clip(v, -limit, limit),  y_next = y + h*(u + d).
  pi_step(y, r, integral, kp, ki, limit, h, d=0) -> (u, y_next, integral_next)
      integral is the STORED sum of past error*time (m/s * s = m).
      v = kp*e + ki*integral (the stored value, before this step's update),
      u = clip(v, -limit, limit), y_next = y + h*(u + d).             EXACT
      Not saturated (-limit <= v <= limit; exactly +-limit is not saturated):
          integral_next = integral + h*e                              EXACT
      Saturated (|v| > limit, whether kp*e or ki*integral caused it) -
      anti-windup BAND, checked on every single step. Let
      s = +1 if v > limit else -1 and the tracking value
          I_t = (s*limit - kp*e) / ki    (I_t = integral when ki == 0),
      the integral at which v would sit exactly on the limit for this error.
      * Pushing (s*e > 0, the error drives further into the limit): the
        integral must not grow in that direction or unwind past I_t:
          s = +1:  I_t <= integral_next <= integral
          s = -1:  integral <= integral_next <= I_t
      * Otherwise (s*e <= 0, the error already asks to come back): integrate
        at least normally, but do not unwind past I_t + h*e:
          s = +1:  I_t + h*e <= integral_next <= integral + h*e
          s = -1:  integral + h*e <= integral_next <= I_t + h*e
      Accepted: conditional integration / clamping (hold while pushing,
      integrate normally otherwise), and tracking or back-calculation ONLY
      when guarded so that, on each step, the integral never moves toward the
      limit while pushing and never unwinds past I_t. NOT accepted:
      - a naive clamp of u that still does integral + h*e on every step (a
        runaway integrator);
      - deciding saturation from kp*e alone (the integral can saturate u);
      - treating v exactly equal to +-limit as saturated;
      - freezing the integral whenever saturated, whatever the error sign (it
        stays stuck after the error has changed sign);
      - an unguarded fixed-gain back-calculation
        integral += h*(e + Kt*(u - v)/ki): for small Kt it still grows while
        pushing, for large Kt it overshoots I_t, so it fails this per-step
        band even where its closed-loop response looks acceptable.
  simulate(y0, r, kp, ki, limit, h, steps, d=0) -> list of `steps` pairs
      Start at y[0] = y0 with integral 0 and apply the pi_step update once
      per step, in order, feeding back y_next and integral_next. Entry k is
      the pair (y[k+1], u[k]): the output after step k and the command
      applied in it. Validate simulate's own arguments once. The pi_step
      bounds on y and integral apply to caller inputs only: intermediate
      states may leave them (y can pass 100), and simulate must not raise for
      any valid simulate arguments. Share an unvalidated update with pi_step
      rather than calling the validating pi_step on every state.
  step_metrics(outputs, y0, r, band) -> (settle, overshoot)
      outputs = [y[1], ..., y[N]] (e.g. the y values of a simulate trace) and
      y[0] = y0. "Within band" means |y[k] - r| <= band (inclusive).
      settle = the smallest k in 0..N such that y[j] is within band for EVERY
      j with k <= j <= N. It is a step count (time = settle*h; y0 itself is
      k = 0), not a list index. settle = None when y[N] is outside the band:
      "not settled within this horizon" is a report, not an error.
      overshoot = max(0, max over k = 1..N of s*(y[k] - r)) with s = +1 if
      r > y0 and s = -1 if r < y0; overshoot = 0 if r == y0. Absolute m/s,
      never negative, not a percentage.
Bounds: |y|, |y0|, |r| <= 100; 0 <= kp <= 100 (1/s); 0 <= ki <= 100 (1/s^2);
0 < limit <= 100; 0 < h <= 1; |d| <= 100; |integral| <= 1e9; steps is an int
(not bool or float) with 1 <= steps <= 1000; outputs is a list/tuple of 1 to
1000 numbers with |value| <= 1e6; 0 < band <= 100. Invalid inputs (wrong type
or shape, bool, NaN, infinity, out of bounds) raise ValueError. Return exactly
a list/tuple of finite int/float (non-bool) values; settle is an int or None.
Never mutate inputs.
Unreachable references: if d works against the command (for example d = -0.8
with limit = 0.5 and r above y) y can never reach r. u then stays on the
limit, the integral must stay bounded by the band above and step_metrics
reports None. No case here demands zero error in finite time.

Pause before coding - write your predictions down first:
  1. y == r with integral 0: what u does P control give, and does y stay at r
     when d != 0?  What steady error do you expect for P-only with d?
  2. Unsaturated P-only: the error is multiplied by what each step? What
     happens for h*kp = 0.2, 1, 1.5 and 2.5?
  3. pi_step at equilibrium y == r with d = -1: what integral keeps u = -d?
  4. A long saturated rise: what does a naive integral do, and how does that
     change the overshoot once y reaches r?
  5. d = -0.8 and limit = 0.5 with r above y: can y ever reach r? What should
     the integral do while it cannot?
  6. Can u saturate while kp*e is small? What then decides "pushing"?
Self-check tolerances are per-case m/s, m/s^2 and m, not physical accuracy.
Failure messages name the case and the kind of mismatch, never the expected
numbers. "your code raised X" means your function raised on a VALID input.
This does not implement motor control, torque control, tuning, delay,
filtering, a derivative term or any hardware interface.
Reflection: why does passing this toy integrator NOT validate a real
actuator? (Think about motor and current dynamics, delay, friction, sensor
noise and quantisation, sampling jitter, unknown or changing loads, limits
that are not symmetric, and safety stops.)

Background link only: MathWorks, Anti-Windup Control Using a PID Controller,
https://www.mathworks.com/help/simulink/slref/anti-windup-control-using-a-pid-controller.html
It describes clamping and fixed-gain back-calculation; this kit accepts the
latter only in the guarded form above. No source code, text, diagrams or
model from that page is redistributed here, and no MATLAB is needed.
"""
import math


def p_step(y, r, kp, limit, h, d=0):
    raise NotImplementedError("Clip the command, not the speed; then step the integrator")


def pi_step(y, r, integral, kp, ki, limit, h, d=0):
    raise NotImplementedError("Use the stored integral; stop it winding up while pushing a limit")


def simulate(y0, r, kp, ki, limit, h, steps, d=0):
    raise NotImplementedError("Share an unvalidated update with pi_step; feed back y and the integral, intermediate y may exceed 100")


def step_metrics(outputs, y0, r, band):
    raise NotImplementedError("Settle is a step count that must hold to the end of the horizon")


# ---- SPOILER BELOW: _oracle_pi and _oracle_metrics are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _oracle_pi(y, r, integral, kp, ki, limit, h, d=0):
    """Author reference: conditional integration (hold while pushing a limit)."""
    e = r - y
    v = kp*e + ki*integral
    u = max(-limit, min(limit, v))
    s = 1 if v > limit else -1 if v < -limit else 0
    return u, y + h*(u + d), integral if s*e > 0 else integral + h*e


def _oracle_trace(y0, r, kp, ki, limit, h, steps, d=0):
    y, integral, trace = y0, 0, []
    for _ in range(steps):
        u, y, integral = _oracle_pi(y, r, integral, kp, ki, limit, h, d)
        trace.append((y, u))
    return trace


def _oracle_metrics(outputs, y0, r, band):
    ys = [y0] + list(outputs)
    settle = None
    if abs(ys[-1] - r) <= band:
        settle = len(ys) - 1
        while settle > 0 and abs(ys[settle-1] - r) <= band:
            settle -= 1
    s = 1 if r > y0 else -1 if r < y0 else 0
    overshoot = 0 if s == 0 else max(0, max(s*(y - r) for y in outputs))
    return settle, overshoot


def _band(y, r, integral, kp, ki, limit, h):
    """Saturated step: (low, high, s, pushing) for integral_next, else None (exact)."""
    e = r - y
    v = kp*e + ki*integral
    if -limit <= v <= limit:
        return None
    s = 1 if v > limit else -1
    tracking = integral if ki == 0 else (s*limit - kp*e)/ki
    shift = 0 if s*e > 0 else h*e
    return (min(integral, tracking) + shift, max(integral, tracking) + shift,
            s, s*e > 0)


# p_step(y, r, kp, limit, h[, d]) -> (u, y_next): hand-derived answers.
_P_CASES = [
    ((0.5, 1.25, 2.0, 3.0, 0.1), (1.5, 0.65)),
    ((1.0, 0.4, 1.5, 2.0, 0.2), (-0.9, 0.82)),
    ((-0.5, 2.5, 3.0, 1.2, 0.25), (1.2, -0.2)),
    ((3.0, -2.0, 0.5, 0.75, 0.5), (-0.75, 2.625)),
    ((1.7, 1.7, 4.0, 1.0, 0.1), (0.0, 1.7)),
    ((1.0, 2.0, 0.0, 1.0, 0.5, -0.4), (0.0, 0.8)),
    ((0.2, 1.0, 1.0, 2.0, 0.1, 0.5), (0.8, 0.33)),
    ((0, 3, 2, 1, 1), (1, 1)),
    ((99.0, 100.0, 100.0, 100.0, 1.0, 100.0), (100.0, 299.0)),
    ((2.0, -1.0, 2.0, 0.5, 0.2, 1.5), (-0.5, 2.2)),
]
# pi_step(y, r, integral, kp, ki, limit, h[, d]) -> (u, y_next, integral_next);
# integral_next is None where the anti-windup band applies instead.
_PI_CASES = [
    ((0.5, 1.0, 0.0, 1.0, 2.0, 5.0, 0.1), (0.5, 0.55, 0.05)),
    ((1.0, 1.5, 0.2, 2.0, 0.5, 3.0, 0.2), (1.1, 1.22, 0.3)),
    ((2.0, 1.5, 0.8, 1.0, 1.0, 2.0, 0.5), (0.3, 2.15, 0.55)),
    ((1.0, 1.0, 0.4, 2.0, 2.5, 3.0, 0.1, -1.0), (1.0, 1.0, 0.4)),
    ((0.0, 2.0, 0.5, 2.0, 1.0, 1.5, 0.1), (1.5, 0.15, None)),
    ((1.0, -1.0, -0.3, 1.0, 2.0, 1.0, 0.2), (-1.0, 0.8, None)),
    ((1.2, 1.0, 3.0, 1.0, 1.0, 2.0, 0.5), (2.0, 2.2, None)),
    ((-1.2, -1.0, -3.0, 1.0, 1.0, 2.0, 0.5), (-2.0, -2.2, None)),
    ((0.0, 3.0, 0.7, 2.0, 0.0, 1.0, 0.25), (1.0, 0.25, None)),
    ((0, 1, 0, 2, 1, 10, 1), (2, 2, 1)),
    ((1.0, 1.0, 5.0, 1.0, 1.0, 2.0, 0.1), (2.0, 1.2, None)),
    ((0.0, 1.0, 0.0, 1.0, 1.0, 0.5, 0.1, -0.8), (0.5, -0.03, None)),
    ((-0.5, -1.0, -0.6, 0.5, 1.0, 1.0, 0.25), (-0.85, -0.7125, -0.725)),
    ((0.9, 1.0, 1.0, 1.0, 1.0, 0.5, 0.1), (0.5, 0.95, None)),
    ((-0.9, -1.0, -1.0, 1.0, 1.0, 0.5, 0.1), (-0.5, -0.95, None)),
    ((0.5, 1.0, 0.25, 1.0, 2.0, 1.0, 0.1), (1.0, 0.6, 0.3)),
    ((0.0, 0.5, -9e8, 1.0, 1e-9, 2.0, 0.5), (-0.4, -0.2, -899999999.75)),
]
# simulate(y0, r, kp, ki, limit, h, steps[, d]): "exact" cases never saturate
# with ki > 0, so every valid anti-windup method gives the same trace.
# "band" cases saturate first and are judged on behaviour: plant consistency,
# command bounds, settling and overshoot. "limit" stays saturated throughout.
_SIM_CASES = [
    ("exact", (0.0, 1.0, 2.0, 0.0, 10.0, 0.1, 20)),
    ("exact", (0.0, 1.0, 3.0, 0.0, 10.0, 0.5, 6)),
    ("exact", (0.0, 2.0, 1.0, 0.0, 0.5, 0.5, 8)),
    ("exact", (0.2, 1.0, 1.5, 0.5, 10.0, 0.1, 30, 0.3)),
    ("exact", (0, 1, 1, 0, 10, 1, 3)),
    ("band", (0.0, 2.0, 1.5, 1.0, 0.5, 0.1, 200), 0.05, 150, 0.2),
    ("band", (0.0, 1.0, 2.0, 1.0, 0.5, 0.1, 150, -0.2), 0.05, 120, 0.1),
    ("limit", (0.0, 1.0, 2.0, 1.0, 0.5, 0.1, 100, -0.8)),
    ("exact", (99.0, 100.0, 100.0, 0.0, 100.0, 1.0, 3, 100.0)),
    ("limit", (0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1000, -100.0)),
]
# step_metrics(outputs, y0, r, band) -> (settle, overshoot): hand-derived.
_METRIC_CASES = [
    (([0.5, 0.875, 1.125, 1.0625, 0.9375, 1.0], 0.5, 1.0, 0.125), (2, 0.125)),
    (([0.25, 0.5, 0.75], 0.0, 1.0, 0.125), (None, 0.0)),
    (([0.9375, 1.25, 1.0], 0.0, 1.0, 0.125), (3, 0.25)),
    (([1.5, 0.75, 0.9375, 1.0], 3.0, 1.0, 0.125), (3, 0.25)),
    (([1.0625, 0.9375], 1.0, 1.0, 0.125), (0, 0.0)),
    (([1.0], 0.0, 1.0, 0.125), (1, 0.0)),
    (([1.25, 1.0], 0.9375, 1.0, 0.125), (2, 0.25)),
    (((1, 2, 3, 3), 0, 3, 1), (2, 0)),
    (([-0.5, -1.25, -0.875, -1.0], 0.0, -1.0, 0.125), (3, 0.25)),
    (([1.5, 0.75, 1.125, 0.9375, 1.03125, 0.984375], 0.0, 1.0, 0.0625), (4, 0.5)),
    (([1e6, -1e6, 1.0], 0.0, 1.0, 100.0), (3, 999999.0)),
]
# Unreachable then reachable, through pi_step only, every step held to the
# contract: (y0, r, kp, ki, limit, h, d while unreachable, steps, d afterwards,
# steps, settle band, latest settle, max overshoot). The second has a small kp,
# so the integral term, not kp*e, is what saturates the command.
_CHAINS = [
    (0.0, 1.0, 2.0, 1.0, 0.5, 0.1, -0.8, 100, 0.0, 300, 0.05, 250, 0.2),
    (0.0, 1.0, 0.3, 1.0, 0.5, 0.1, -0.8, 100, 0.0, 500, 0.1, 400, 1.0),
]


def self_check():
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []

    def run(label, function, args, compare):
        try:
            compare(function(*args))
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": your code raised " + type(error).__name__
                            + " on a valid input")

    def close(got, want, name, tolerance=1e-9):
        if abs(got - want) > tolerance:
            raise _Mismatch(name + " is wrong (tolerance " + repr(tolerance) + ")")

    for i, (args, (u, y_next)) in enumerate(_P_CASES):
        def compare(got, u=u, y_next=y_next):
            if not _vector(got, 2):
                raise _Mismatch("output must be a length-2 list/tuple (u, y_next) of finite int/float")
            close(got[0], u, "command u")
            close(got[1], y_next, "y_next")
        run("p_step " + str(i), p_step, args, compare)

    def check_integral(got, state, exact):
        """state = (y, r, integral, kp, ki, limit, h); exact = unsaturated answer."""
        band = _band(*state)
        tolerance = 1e-9*max(1, abs(state[2]))
        if band is None:
            close(got, exact, "integral_next (unsaturated step)", tolerance)
            return
        low, high, s, pushing = band
        toward = got > high + tolerance if s > 0 else got < low - tolerance
        away = got < low - tolerance if s > 0 else got > high + tolerance
        if toward and pushing:
            raise _Mismatch("integral moved toward the limit while the saturated command"
                            " was pushing (windup)")
        if toward:
            raise _Mismatch("integral integrated less than normal although the error"
                            " points back from the limit (held or frozen?)")
        if away:
            raise _Mismatch("integral unwound past the tracking value"
                            + (" I_t" if pushing else " I_t + h*e"))

    for i, (args, (u, y_next, integral_next)) in enumerate(_PI_CASES):
        def compare(got, u=u, y_next=y_next, integral_next=integral_next, args=args):
            if not _vector(got, 3):
                raise _Mismatch("output must be a length-3 list/tuple"
                                " (u, y_next, integral_next) of finite int/float")
            close(got[0], u, "command u")
            close(got[1], y_next, "y_next")
            check_integral(got[2], args[:7], integral_next)
        run("pi_step " + str(i), pi_step, args, compare)

    def trace_shape(got, steps):
        if not isinstance(got, (list, tuple)) or len(got) != steps:
            raise _Mismatch("trace must be a list/tuple with exactly `steps` entries")
        for pair in got:
            if not _vector(pair, 2):
                raise _Mismatch("each entry must be a length-2 list/tuple (y_next, u)"
                                " of finite int/float")

    for i, (kind, args, *limits) in enumerate(_SIM_CASES):
        y0, r, limit, h, steps = args[0], args[1], args[4], args[5], args[6]
        d = args[7] if len(args) > 7 else 0
        reference = _oracle_trace(*args)

        def compare(got, kind=kind, reference=reference, limits=limits,
                    y0=y0, r=r, limit=limit, h=h, steps=steps, d=d):
            trace_shape(got, steps)
            if kind == "exact":
                for k, ((y, u), (want_y, want_u)) in enumerate(zip(got, reference)):
                    close(u, want_u, "u at step " + str(k))
                    close(y, want_y, "y after step " + str(k))
                return
            previous = y0
            for k, (y, u) in enumerate(got):
                if abs(u) > limit + 1e-12:
                    raise _Mismatch("command exceeds the limit at step " + str(k))
                close(y, previous + h*(u + d), "plant update y after step " + str(k),
                      1e-9*max(1, abs(y)))
                previous = y
            close(got[0][1], limit, "first (saturated) command")
            if kind == "limit":
                for k, (y, u) in enumerate(got):
                    close(u, limit, "u at step " + str(k) + " (reference unreachable)", 1e-12)
                return
            band, latest, worst = limits
            settle, overshoot = _oracle_metrics([y for y, u in got], y0, r, band)
            if settle is None or settle > latest:
                raise _Mismatch("does not settle within the stated band and horizon"
                                " (windup or wrong integral feedback?)")
            if overshoot > worst:
                raise _Mismatch("overshoot exceeds the behaviour band (integrator windup?)")
        run("simulate " + str(i) + " (" + kind + ")", simulate, args, compare)

    for i, (args, (settle, overshoot)) in enumerate(_METRIC_CASES):
        original = list(args[0])
        args = (type(args[0])(args[0]),) + args[1:]  # fresh copy: the table stays intact
        def compare(got, settle=settle, overshoot=overshoot, args=args, original=original):
            if list(args[0]) != original:
                raise _Mismatch("input outputs sequence was mutated")
            if (not isinstance(got, (list, tuple)) or len(got) != 2
                    or not (got[0] is None or type(got[0]) is int) or not _real(got[1])):
                raise _Mismatch("output must be a length-2 list/tuple (settle int or None,"
                                " finite overshoot)")
            if (got[0] is None) != (settle is None):
                raise _Mismatch("settled/not-settled decision is wrong")
            if got[0] != settle:
                raise _Mismatch("settle step count is wrong")
            close(got[1], overshoot, "overshoot", 1e-12)
        run("step_metrics " + str(i), step_metrics, args, compare)

    def chain(case):
        y, r, kp, ki, limit, h, d_far, n_far, d_near, n_near, band, latest, worst = case
        integral, outputs, y_start = 0, [], None
        for k in range(n_far + n_near):
            d = d_far if k < n_far else d_near
            if k == n_far:
                y_start = y
            got = pi_step(y, r, integral, kp, ki, limit, h, d)
            if not _vector(got, 3):
                raise _Mismatch("pi_step output must be a length-3 list/tuple of finite int/float")
            u, y_next, exact = _oracle_pi(y, r, integral, kp, ki, limit, h, d)
            where = (" while unreachable" if k < n_far else " after recovery starts")
            try:
                close(got[0], u, "command u")
                close(got[1], y_next, "y_next")
                check_integral(got[2], (y, r, integral, kp, ki, limit, h), exact)
            except _Mismatch as error:
                raise _Mismatch(str(error) + where + ", step " + str(k))
            y, integral = got[1], got[2]
            if k >= n_far:
                outputs.append(y)
        settle, overshoot = _oracle_metrics(outputs, y_start, r, band)
        if settle is None or settle > latest:
            raise _Mismatch("does not recover to the band in time once the reference is"
                            " reachable (integrator windup?)")
        if overshoot > worst:
            raise _Mismatch("recovery overshoot exceeds the behaviour band (integrator windup?)")
    for i, case in enumerate(_CHAINS):
        run("unreachable then reachable " + str(i), chain, (case,), lambda got: None)

    nan, inf = float('nan'), float('inf')
    signatures = [
        ("p_step", p_step, ("y", "r", "kp", "limit", "h", "d"),
         (0.5, 1.0, 1.0, 1.0, 0.1, 0.0)),
        ("pi_step", pi_step, ("y", "r", "integral", "kp", "ki", "limit", "h", "d"),
         (0.5, 1.0, 0.0, 1.0, 1.0, 1.0, 0.1, 0.0)),
        ("simulate", simulate, ("y0", "r", "kp", "ki", "limit", "h", "steps", "d"),
         (0.0, 1.0, 1.0, 1.0, 1.0, 0.1, 5, 0.0)),
        ("step_metrics", step_metrics, ("outputs", "y0", "r", "band"),
         ([0.5, 1.0], 0.0, 1.0, 0.1)),
    ]
    scalar = [nan, inf, -inf, True, 100.01, -100.01, "0", None]
    bad = {
        "y": scalar, "y0": scalar, "r": scalar,
        "kp": [nan, inf, -0.01, 100.01, True, "1", None],
        "ki": [nan, inf, -0.01, 100.01, False, "1", None],
        "limit": [0.0, -1.0, 100.01, nan, inf, True, "1", None],
        "h": [0.0, -0.1, 1.01, nan, inf, True, "0.1", None],
        "d": [nan, inf, 100.01, -100.01, True, "0", None],
        "integral": [nan, inf, 1.01e9, -1.01e9, True, "0", None],
        "steps": [0, -1, 1001, 5.0, True, nan, "5", None],
        "outputs": [[], (), [True], [nan], [inf], [1.0, nan], [1e6 + 1], [-1e6 - 1],
                    "abc", {0: 1.0}, [1.0, "x"], [0.5] * 1001, None, [[1.0]]],
        "band": [0.0, -0.1, 100.01, nan, inf, True, "0.1", None],
    }
    for title, function, names, args in signatures:
        for slot, name in enumerate(names):
            for value in bad[name]:
                trial = args[:slot] + (value,) + args[slot+1:]
                shown = repr(value)
                label = ("invalid " + title + "(" + name + "="
                         + (shown if len(shown) <= 24 else shown[:21] + "...") + ")")
                try:
                    function(*trial)
                except ValueError:
                    continue
                except Exception as error:
                    failures.append(label + ": raised " + type(error).__name__
                                    + " instead of ValueError")
                    continue
                failures.append(label + ": returned instead of raising ValueError")
    return failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual bounded-feedback self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
