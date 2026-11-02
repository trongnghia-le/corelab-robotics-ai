"""CoreLab Pendulum dynamics lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the nine functions below, then run your edited file locally:
  Windows: py -3 L08-dynamics.v1.py
  macOS/Linux: python3 L08-dynamics.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared toy model (numerical practice, not a motor, gearbox or hardware model):
ONE rigid link on a frictionless pivot, moving in a vertical plane.
  q   joint angle in radians, measured from the DOWNWARD vertical,
      counter-clockwise positive (q = 0 hangs straight down; q = pi is upright).
  qd  joint rate in rad/s.  tau  joint torque in N*m, positive increases q.
  model = (m, lc, ic, b, g) with m the mass in kg, lc the distance in m from the
      pivot to the centre of mass, ic the inertia about the centre of mass in
      kg*m^2, b the viscous damping in N*m*s/rad and g gravity in m/s^2.
      I = ic + m*lc^2 is the inertia about the pivot (kg*m^2, parallel axis).
Equation of motion:   I*qdd + b*qd + m*g*lc*sin(q) = tau
so the gravity torque is m*g*lc*sin(q) (it pulls q back towards 0).
Total energy (zero at the hanging rest state; damping and tau are not in it):
      E = 0.5*I*qd^2 + m*g*lc*(1 - cos(q)).
For tau = 0 and b = 0, E is constant; with b > 0, dE/dt = -b*qd^2; with torque,
dE/dt = (tau - b*qd)*qd.

Integrators. step(method, q, qd, tau, h, model) advances one step of h seconds
with tau held constant over the step (zero-order hold). With a = acceleration at
the START state (q, qd) (damping uses the old qd as well):
  "euler"       q' = q + h*qd,   qd' = qd + h*a            (explicit Euler)
  "symplectic"  qd' = qd + h*a,  q' = q + h*qd'            (semi-implicit Euler:
                the NEW rate moves the angle)
  "rk4"         classical 4-stage Runge-Kutta on the state (q, qd) with
                f(q, qd) = (qd, acceleration(q, qd, tau)), tau constant:
                k1 = f(s), k2 = f(s + h/2 k1), k3 = f(s + h/2 k2), k4 = f(s + h k3),
                s' = s + h/6 (k1 + 2 k2 + 2 k3 + k4).
Results are EXACT definitions: each is compared with tolerance 1e-9 (relative to
max(1, |value|)); energy_trace and regulate results accumulate over many steps and use
1e-8 relative tolerance instead. Other formulations of the same method are accepted.

Contracts (all numbers finite int/float, never bool; bounds inclusive):
  acceleration(q, qd, tau, model) -> qdd           (rad/s^2) = (tau - b*qd - m*g*lc*sin(q))/I
  energy(q, qd, model) -> E                        (J) as above, no angle wrapping needed
  small_angle_period(model) -> T                   (s) 2*pi*sqrt(I/(m*g*lc)), the period of the
      linearised undamped model; b and tau are ignored.
  step(method, q, qd, tau, h, model) -> (q_next, qd_next)       as defined above
  energy_trace(method, q0, qd0, h, steps, model) -> list of steps + 1 energies
      E_0 .. E_steps along `steps` steps of step() with tau = 0 starting from
      (q0, qd0) (b in the model is used, so damped runs lose energy).
  energy_drift(energies) -> (final_change, max_change)
      final_change = E_last - E_0 (signed: positive means energy was GAINED),
      max_change = max over k of |E_k - E_0|, both in J, not relative.
  computed_torque(q, qd, ref, kp, kd, tau_max, model) -> (tau_raw, tau)
      ref = (q_d, qd_d, qdd_d) the desired angle, rate and acceleration.
      e = q_d - q, ed = qd_d - qd,
      tau_raw = I*(qdd_d + kd*ed + kp*e) + b*qd + m*g*lc*sin(q)
      (inertia times a commanded acceleration, plus damping and gravity
      compensation from the model, measured q and qd). tau = tau_raw clipped to
      [-tau_max, tau_max]; tau_raw is NOT clipped and a raw value exactly on a
      limit is not special. With a perfect model and no clipping the error obeys
      ed' + kd*ed + kp*e = 0 in continuous time.
  regulate(q0, qd0, q_ref, kp, kd, tau_max, h, steps, method, plant, controller)
      -> list of `steps` triples (q_next, qd_next, tau_applied).
      Hold the angle q_ref (qd_d = qdd_d = 0). Each step: tau = the clipped
      computed_torque of the CURRENT state using the `controller` model, then
      step(method, ..., tau, h, plant) with the `plant` model. plant and
      controller are models and may differ (a wrong model parameter). The
      controller sees the exact state; there is no noise, delay or estimator.
  best_model(qs, qds, candidates) -> (index, spreads)
      qs, qds: equally long lists of measured angles and rates (2 to 200 samples)
      from ONE free, undamped swing (tau = 0, b = 0). For each candidate model the
      energy of every sample is computed; spread = (Emax - Emin)/Emax, or 0.0 if
      Emax <= 0. A model that matches the real system keeps E flat, so its spread
      is near 0. spreads has one float per candidate. index = the smallest i whose
      spread is within 1e-9 of the smallest spread (ties go to the lowest index).
      Spreads are compared with absolute tolerance 1e-9.
Bounds (ValueError otherwise): a model is a list/tuple of exactly 5 numbers with
0.5 <= m <= 10, 0.2 <= lc <= 1, 0 <= ic <= 1, 0 <= b <= 0.5, 1 <= g <= 20;
|q|, |q0|, |q_ref|, |qd|, |qd0|, |tau| <= 100 and every entry of ref has
|q_d|, |qd_d| <= 100, |qdd_d| <= 1000; 0 < h <= 0.05; steps is an int (not bool
or float) with 1 <= steps <= 1000; 0 <= kp <= 1000; 0 <= kd <= 200;
0 < tau_max <= 100; method is exactly one of the strings "euler", "symplectic",
"rk4"; energies is a list/tuple of 2 to 1001 numbers with |E| <= 1e200; qs and
qds are lists/tuples of the same length 2..200 with |q|, |qd| <= 100; candidates
is a list/tuple of 1 to 10 models. Invalid inputs (wrong type or shape, bool,
NaN, infinity, out of bounds) raise ValueError. Intermediate states inside
energy_trace and regulate may leave the input bounds (explicit Euler can gain a
lot of energy) and must not raise; validate the caller's arguments once. Return
finite int/float values (non-bool) in the shapes above (lists or tuples both
accepted), the index as an int. Never mutate inputs.

Pause before coding - write your predictions down first:
  1. At q = 0 with qd = 0, tau = 0, what is qdd? At q = pi/2, tau = 0, with
     m = lc = 1, ic = 0, what is qdd?  What does ic do to the same torque?
  2. For small angles the model is q'' = -(m g lc / I) q: what period follows?
     Does changing m alone change it when ic = 0? When ic > 0?
  3. Undamped swing, small step h: which of the three methods gains energy every
     step, which keeps E within a small band around E_0, which barely moves E?
     By what factor does one explicit-Euler step scale a small-angle E?
  4. Halving h: what do you expect for the drift of each method (first order,
     first order but bounded, fourth order)?
  5. A computed-torque controller uses g_model = 5 while the real g is 9.81. What
     steady offset do you expect when holding a non-zero angle? What if tau_max
     is smaller than m g lc sin(q_ref)?
  6. A swing is recorded and you test two models with all masses doubled. Can the
     energy trace tell them apart? Which combination of parameters can it detect?
Self-check tolerances are per-case numerical, not physical accuracy. Failure
messages name the case and the kind of mismatch, never the expected numbers.
"your code raised X" means your function raised on a VALID input. A function that
raises NotImplementedError is reported once.
Analytic anchors used here: small-angle explicit Euler multiplies the energy by
(1 + (h*w)^2) per step with w^2 = m g lc/I; a critically damped regulator with
kp = (kd/2)^2 follows e(t) = e0 (1 + w t) exp(-w t) for a perfect model without
clipping (w = kd/2); RK4 energy drift is tiny for h*w well below 1.
This is a one-link, characterised toy. It has NO multi-link dynamics, contact,
friction beyond viscous damping, motor, gearbox or amplifier model, no physics
engine and no hardware or real torque control.
Reflection: why does passing this toy NOT validate a real arm? (Think about
unknown inertias and payloads, joint friction and backlash, motor and current
dynamics, flexible links, sample time and delay, sensor noise and quantisation,
torque limits that depend on speed, coupling between joints, and safety stops.)
"""
import math


def acceleration(q, qd, tau, model):
    raise NotImplementedError("Gravity torque is m*g*lc*sin(q); divide by the pivot inertia ic + m*lc^2")


def energy(q, qd, model):
    raise NotImplementedError("Kinetic 0.5*I*qd^2 plus potential m*g*lc*(1 - cos q)")


def small_angle_period(model):
    raise NotImplementedError("Linearise sin(q) = q, read off w^2, then T = 2*pi/w")


def step(method, q, qd, tau, h, model):
    raise NotImplementedError("Three formulas; compute the acceleration at the start state, hold tau constant")


def energy_trace(method, q0, qd0, h, steps, model):
    raise NotImplementedError("Record the energy at k = 0 and after each step; do not validate inside the loop")


def energy_drift(energies):
    raise NotImplementedError("Signed last-minus-first and the largest absolute deviation from the first")


def computed_torque(q, qd, ref, kp, kd, tau_max, model):
    raise NotImplementedError("Inertia times the commanded acceleration, plus damping and gravity compensation, then clip")


def regulate(q0, qd0, q_ref, kp, kd, tau_max, h, steps, method, plant, controller):
    raise NotImplementedError("Controller model for the torque, plant model for the step; feed the new state back")


def best_model(qs, qds, candidates):
    raise NotImplementedError("Spread of the sample energies per candidate; the flattest wins")


# ---- SPOILER BELOW: the _oracle_* functions are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _oracle_acc(q, qd, tau, model):
    m, lc, ic, b, g = model
    return (tau - b*qd - m*g*lc*math.sin(q))/(ic + m*lc*lc)


def _oracle_energy(q, qd, model):
    m, lc, ic, b, g = model
    return 0.5*(ic + m*lc*lc)*qd*qd + m*g*lc*(1 - math.cos(q))


def _oracle_period(model):
    m, lc, ic, b, g = model
    return 2*math.pi*math.sqrt((ic + m*lc*lc)/(m*g*lc))


def _oracle_step(method, q, qd, tau, h, model):
    """Author reference for the three integrators."""
    if method == "euler":
        return (q + h*qd, qd + h*_oracle_acc(q, qd, tau, model))
    if method == "symplectic":
        qd_next = qd + h*_oracle_acc(q, qd, tau, model)
        return (q + h*qd_next, qd_next)

    def f(s):
        return (s[1], _oracle_acc(s[0], s[1], tau, model))
    k1 = f((q, qd))
    k2 = f((q + 0.5*h*k1[0], qd + 0.5*h*k1[1]))
    k3 = f((q + 0.5*h*k2[0], qd + 0.5*h*k2[1]))
    k4 = f((q + h*k3[0], qd + h*k3[1]))
    return (q + h/6*(k1[0] + 2*k2[0] + 2*k3[0] + k4[0]),
            qd + h/6*(k1[1] + 2*k2[1] + 2*k3[1] + k4[1]))


def _oracle_trace(method, q0, qd0, h, steps, model):
    q, qd, out = q0, qd0, [_oracle_energy(q0, qd0, model)]
    for _ in range(steps):
        q, qd = _oracle_step(method, q, qd, 0.0, h, model)
        out.append(_oracle_energy(q, qd, model))
    return out


def _oracle_drift(energies):
    return (energies[-1] - energies[0], max(abs(e - energies[0]) for e in energies))


def _oracle_ct(q, qd, ref, kp, kd, tau_max, model):
    m, lc, ic, b, g = model
    q_d, qd_d, qdd_d = ref
    raw = ((ic + m*lc*lc)*(qdd_d + kd*(qd_d - qd) + kp*(q_d - q))
           + b*qd + m*g*lc*math.sin(q))
    return (raw, max(-tau_max, min(tau_max, raw)))


def _oracle_regulate(q0, qd0, q_ref, kp, kd, tau_max, h, steps, method, plant, controller):
    q, qd, out = q0, qd0, []
    for _ in range(steps):
        tau = _oracle_ct(q, qd, (q_ref, 0.0, 0.0), kp, kd, tau_max, controller)[1]
        q, qd = _oracle_step(method, q, qd, tau, h, plant)
        out.append((q, qd, tau))
    return out


def _oracle_spread(qs, qds, model):
    energies = [_oracle_energy(q, v, model) for q, v in zip(qs, qds)]
    top = max(energies)
    return 0.0 if top <= 0 else (top - min(energies))/top


def _oracle_best(qs, qds, candidates):
    spreads = [_oracle_spread(qs, qds, c) for c in candidates]
    low = min(spreads)
    return (min(i for i, s in enumerate(spreads) if s <= low + 1e-9), spreads)


_T = (1, 1, 0, 0, 9.81)
_M2 = (2, 0.5, 0.125, 0.1, 9.81)
_PI = math.pi
# acceleration(q, qd, tau, model) -> qdd; hand-derived (I = ic + m*lc^2).
_ACC_CASES = [
    ((0, 0, 2, _T), 2.0),
    ((_PI/2, 0, 0, _T), -9.81),
    ((_PI/6, 2, 3, _M2), -3.368),
    ((0.0, 3.0, 0.0, (1.0, 0.5, 0.0, 0.5, 9.81)), -6.0),
    ((_PI/2, 0, 0, (2, 1, 0.5, 0, 10)), -8.0),
    ((-_PI/2, 0, 0, _T), 9.81),
    ((2*_PI + _PI/2, 0, 0, (1, 1, 0, 0, 10)), -10.0),
    ((-100, 100, 100, (0.5, 0.2, 0.0, 0.5, 20.0)), 2449.363435889024),
]
# energy(q, qd, model) -> E (J); hand-derived.
_ENERGY_CASES = [
    ((_PI/2, 0, _T), 9.81),
    ((0, -2, (2, 0.5, 0.5, 0, 10)), 2.0),
    ((_PI/3, 2, _M2), 6.155),
    ((-_PI/2, 1, _T), 10.31),
    ((2*_PI, 0, _T), 0.0),
]
# small_angle_period(model) -> T (s).
_PERIOD_CASES = [
    ((_T,), 2.006066680711),
    (((1, 1, 1, 0, 2*_PI**2),), 2.0),
    (([2, 0.5, 0.125, 0.1, 9.81],), 1.585934962305),
]
# step(method, q, qd, tau, h, model) -> (q_next, qd_next). The euler and
# symplectic answers are hand-derived; the rk4 ones come from the four-stage formula.
_STEP_CASES = [
    (("euler", _PI/2, 0, 0, 0.05, (1, 1, 0, 0, 10)), (1.570796326795, -0.5)),
    (("euler", _PI/2, 2, 0, 0.05, (1, 1, 0, 0.5, 10)), (1.670796326795, 1.45)),
    (("euler", 0.3, -0.5, 1.5, 0.05, _M2), (0.275, -0.607924258188)),
    (("symplectic", _PI/2, 0, 0, 0.05, (1, 1, 0, 0, 10)), (1.545796326795, -0.5)),
    (("symplectic", _PI/2, 2, 0, 0.05, (1, 1, 0, 0.5, 10)), (1.643296326795, 1.45)),
    (("symplectic", 0, 0, 2, 0.05, (1, 1, 0, 0, 10)), (0.005, 0.1)),
    (("rk4", 0, 0, 0, 0.05, _M2), (0.0, 0.0)),
    (("rk4", 0.3, -0.5, 1.5, 0.05, _M2), (0.272473718912, -0.597477188738)),
    (("rk4", 2.5, 1.0, 0, 0.05, _T), (2.542814260113, 0.715424842517)),
    (("symplectic", 100, -100, 100, 0.05, (0.5, 0.2, 0.0, 0.5, 20.0)), (113.876591410277, 277.531828205549)),
]
# energy_trace(method, q0, qd0, h, steps, model); anchor names an analytic check.
_TRACE_CASES = [
    (("euler", 0.01, 0.0, 0.02, 200, _T), 'euler-growth'),
    (("symplectic", 0.5, 0.0, 0.02, 250, _T), 'symplectic-band'),
    (("rk4", 0.5, 0.0, 0.05, 200, _T), 'rk4-flat'),
    (("euler", 1.0, 0.0, 0.01, 200, (1, 1, 0, 0.2, 9.81)), None),
    (("symplectic", 1.0, 0.5, 0.02, 250, (2, 0.5, 0.125, 0, 9.81)), None),
    (("euler", 100.0, 100.0, 0.05, 1000, (0.5, 0.2, 0.0, 0.0, 20.0)), None),
]
# energy_drift(energies) -> (final_change, max_change); hand-derived.
_DRIFT_CASES = [
    (([1.0, 1.25, 0.5],), (-0.5, 0.5)),
    (([2.0, 2.0, 2.0],), (0.0, 0.0)),
    (((5.0, 4.0, 6.0, 5.5),), (0.5, 1.0)),
]
# computed_torque(q, qd, ref, kp, kd, tau_max, model) -> (tau_raw, tau); hand-derived.
_CT_CASES = [
    ((_PI/6, 0, (_PI/6, 0, 0), 100, 20, 50, (1, 1, 0, 0, 10)), (5.0, 5.0)),
    ((0, 1.0, (0.5, 0.0, 0.0), 20, 6, 50, _M2), (2.6, 2.6)),
    ((0, 0.5, (0.2, 0.4, 0.2), 20, 6, 50, _M2), (2.3, 2.3)),
    ((0, 0, (0, 0, 3.2), 10, 4, 50, _M2), (2.0, 2.0)),
    ((0, 0, (1.0, 0, 0), 100, 10, 5, (1, 1, 0, 0, 10)), (100.0, 5)),
    ((0, 0, (-1.0, 0, 0), 100, 10, 5, (1, 1, 0, 0, 10)), (-100.0, -5)),
    ((0, 0, (0.25, 0, 0), 20, 0, 5, (1, 1, 0, 0, 10)), (5.0, 5)),
]
# regulate(q0, qd0, q_ref, kp, kd, tau_max, h, steps, method, plant, controller);
# kind "exact" is compared with the reference, "analytic" also with the
# critically damped solution, "limit" never reaches q_ref (clip binds).
_REG_CASES = [
    ("analytic", (0.0, 0.0, 0.8, 25, 10, 100, 0.01, 300, "rk4", _T, _T)),
    ("exact", (0.0, 0.0, 0.8, 25, 10, 100, 0.01, 300, "symplectic", (1.2, 0.5, 0.05, 0.05, 9.81), (1.0, 0.5, 0.05, 0.0, 5.0))),
    ("limit", (-1.0, 0.0, 1.2, 60, 12, 6.0, 0.01, 400, "rk4", _M2, _M2)),
    ("exact", (0.0, 0.0, 10.0, 1000, 10, 100, 0.01, 300, "euler", (0.5, 0.2, 0.0, 0.0, 20.0), (0.5, 0.2, 0.0, 0.0, 20.0))),
]
# best_model(qs, qds, candidates) -> (index, spreads). Data: one undamped swing of
# the model (1.5, 0.8, 0.05, 0, 9.81), rounded to 6 decimals.
_BEST_CASES = [
    ([1.2, 1.14588, 0.986105, 0.730014, 0.397318, 0.020395, -0.358855, -0.697978, -0.963321, -1.133877, -1.199392, -1.156694, -1.007801],
     [0.0, -1.078386, -2.102232, -2.987236, -3.612221, -3.854758, -3.657745, -3.067996, -2.204287, -1.190435, -0.114929, 0.965756, 1.998663],
     [(1.5, 0.8, 0.05, 0, 7.0), (1.5, 0.8, 0.05, 0, 9.81), (1.5, 0.8, 0.6, 0, 9.81), (1.5, 0.6, 0.05, 0, 9.81)]),
    ([0.4, 0.504205, 0.57259, 0.600779, 0.587016, 0.532156, 0.439666, 0.315635, 0.16862, 0.009188, -0.150924],
     [1.5, 1.090553, 0.609965, 0.091098, -0.433386, -0.930914, -1.368625, -1.714226, -1.93895, -2.022166, -1.9558],
     [(1.5, 0.8, 0.6, 0, 9.81), (1.5, 0.6, 0.05, 0, 9.81), (1.5, 0.8, 0.05, 0, 9.81), (1.5, 0.8, 0.05, 0, 7.0)]),
    ([1.2, 1.14588, 0.986105, 0.730014, 0.397318, 0.020395, -0.358855, -0.697978, -0.963321, -1.133877, -1.199392, -1.156694, -1.007801],
     [0.0, -1.078386, -2.102232, -2.987236, -3.612221, -3.854758, -3.657745, -3.067996, -2.204287, -1.190435, -0.114929, 0.965756, 1.998663],
     [(3.0, 0.8, 0.1, 0, 9.81000002), (1.5, 0.8, 0.05, 0, 9.81), (1.5, 0.8, 0.6, 0, 9.81)]),
    ([0.0, 0.0, 0.0],
     [0.0, 0.0, 0.0],
     [(1.5, 0.8, 0.05, 0, 9.81), (1.5, 0.8, 0.05, 0, 7.0)]),
]


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return text + ": over-strict validation, or a bound that is too tight?)"
    return text + ")"


def _show(args):
    shown = "(" + ", ".join(repr(a) for a in args) + ")"
    return shown if len(shown) <= 60 else shown[:57] + "..."


def _clone(value):
    if isinstance(value, (list, tuple)):
        return type(value)(_clone(v) for v in value)
    return value


def _bad_models():
    base = (1.0, 0.5, 0.1, 0.1, 9.81)
    out = [(1.0, 0.5, 0.1, 0.1), base + (1.0,), (), "abc", None, 5, {0: 1.0},
           [1.0, 0.5, 0.1, 0.1, [9.81]]]
    outside = ((0.49, 10.01), (0.19, 1.01), (-0.01, 1.01), (-0.01, 0.51), (0.99, 20.01))
    for slot in range(5):
        for value in outside[slot] + (float('nan'), float('inf'), -float('inf'), True, "1", None):
            out.append(base[:slot] + (value,) + base[slot+1:])
    return out


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    `notes` is accepted for symmetry with the other kits and is not used.
    """
    failures = []
    calls, missing = {}, {}
    functions = {"acceleration": acceleration, "energy": energy,
                 "small_angle_period": small_angle_period, "step": step,
                 "energy_trace": energy_trace, "energy_drift": energy_drift,
                 "computed_torque": computed_torque, "regulate": regulate,
                 "best_model": best_model}

    def run(label, function, args, compare):
        name = label.split(" ")[0]
        calls[name] = calls.get(name, 0) + 1
        live = _clone(args)
        try:
            got = function(*live)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            return
        except Exception as error:
            failures.append(label + ": " + _raised(error))
            return
        try:
            if live != args:
                raise _Mismatch("an input argument was mutated")
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def close(got, want, name, tolerance=1e-9):
        if not abs(got - want) <= tolerance*max(1.0, abs(want)):
            raise _Mismatch(name + " is wrong (relative tolerance " + repr(tolerance) + ")")

    def scalar(got):
        if not _real(got):
            raise _Mismatch("output must be one finite int/float")

    def pair(got, text):
        if not _vector(got, 2):
            raise _Mismatch("output must be a length-2 list/tuple " + text + " of finite int/float")

    for i, (args, want) in enumerate(_ACC_CASES):
        def compare(got, want=want):
            scalar(got)
            close(got, want, "qdd")
        run("acceleration " + str(i) + " " + _show(args), acceleration, args, compare)

    for i, (args, want) in enumerate(_ENERGY_CASES):
        def compare(got, want=want):
            scalar(got)
            close(got, want, "energy")
        run("energy " + str(i) + " " + _show(args), energy, args, compare)

    for i, (args, want) in enumerate(_PERIOD_CASES):
        def compare(got, want=want):
            scalar(got)
            close(got, want, "period")
        run("small_angle_period " + str(i) + " " + _show(args), small_angle_period, args, compare)

    for i, (args, want) in enumerate(_STEP_CASES):
        def compare(got, want=want):
            pair(got, "(q_next, qd_next)")
            close(got[0], want[0], "q_next")
            close(got[1], want[1], "qd_next")
        run("step " + str(i) + " " + _show(args), step, args, compare)

    for i, (args, anchor) in enumerate(_TRACE_CASES):
        method, q0, qd0, h, steps, model = args

        def compare(got, args=args, anchor=anchor):
            if not isinstance(got, (list, tuple)) or len(got) != args[4] + 1:
                raise _Mismatch("trace must be a list/tuple with exactly steps + 1 energies")
            if not all(_real(v) for v in got):
                raise _Mismatch("every energy must be a finite int/float")
            want = _oracle_trace(*args)
            for k, (a, b) in enumerate(zip(got, want)):
                close(a, b, "energy at index " + str(k), 1e-8)
            if anchor == "euler-growth":
                m, lc, ic, damping, g = args[5]
                w2 = m*g*lc/(ic + m*lc*lc)
                factor = (1 + args[3]**2*w2)**args[4]
                if not abs(got[-1]/got[0] - factor) <= 2e-3*factor:
                    raise _Mismatch("small-angle check: explicit Euler should multiply the energy"
                                    " by (1 + (h*w)^2) every step")
            elif anchor == "rk4-flat":
                if not max(abs(e - got[0]) for e in got) <= 1e-4*got[0]:
                    raise _Mismatch("RK4 should keep this undamped energy flat to 0.01 percent")
            elif anchor == "symplectic-band":
                top = max(got)
                if not (top - min(got) <= 0.2*top and abs(got[-1] - got[0]) <= 0.2*got[0]):
                    raise _Mismatch("semi-implicit Euler should keep the energy in a small band")
        run("energy_trace " + str(i) + " " + _show(args), energy_trace, args, compare)

    for i, (args, want) in enumerate(_DRIFT_CASES):
        def compare(got, want=want):
            pair(got, "(final_change, max_change)")
            close(got[0], want[0], "final_change")
            close(got[1], want[1], "max_change")
        run("energy_drift " + str(i) + " " + _show(args), energy_drift, args, compare)

    for i, (args, want) in enumerate(_CT_CASES):
        def compare(got, want=want):
            pair(got, "(tau_raw, tau)")
            close(got[0], want[0], "tau_raw")
            close(got[1], want[1], "tau (after clipping)")
        run("computed_torque " + str(i) + " " + _show(args), computed_torque, args, compare)

    for i, (kind, args) in enumerate(_REG_CASES):
        def compare(got, kind=kind, args=args):
            q0, qd0, q_ref, kp, kd, tau_max, h, steps, method, plant, controller = args
            if not isinstance(got, (list, tuple)) or len(got) != steps:
                raise _Mismatch("trace must be a list/tuple with exactly `steps` entries")
            for entry in got:
                if not _vector(entry, 3):
                    raise _Mismatch("each entry must be a length-3 list/tuple"
                                    " (q_next, qd_next, tau) of finite int/float")
            want = _oracle_regulate(*args)
            for k, (a, b) in enumerate(zip(got, want)):
                if abs(a[2]) > tau_max + 1e-12:
                    raise _Mismatch("applied torque exceeds tau_max at step " + str(k))
                close(a[2], b[2], "applied torque at step " + str(k), 1e-8)
                close(a[0], b[0], "q after step " + str(k), 1e-8)
                close(a[1], b[1], "qd after step " + str(k), 1e-8)
            if kind == "analytic":
                w = kd/2.0
                k = steps // 2
                t = h*(k + 1)
                analytic = (q_ref - q0)*(1 + w*t)*math.exp(-w*t)
                if not abs((q_ref - got[k][0]) - analytic) <= 1e-2*abs(q_ref - q0):
                    raise _Mismatch("critically damped check: the error should follow"
                                    " e0 (1 + w t) exp(-w t) with a perfect model")
            if kind == "limit":
                if not all(abs(abs(e[2]) - tau_max) <= 1e-12 for e in got[len(got)//2:]):
                    raise _Mismatch("the torque limit should bind in the second half of this run")
        run("regulate " + str(i) + " (" + kind + ") " + _show(args), regulate, args, compare)

    for i, args in enumerate(_BEST_CASES):
        def compare(got, args=args):
            if (not isinstance(got, (list, tuple)) or len(got) != 2 or type(got[0]) is not int
                    or not isinstance(got[1], (list, tuple)) or len(got[1]) != len(args[2])
                    or not all(_real(v) for v in got[1])):
                raise _Mismatch("output must be (index int, list of one spread per candidate)")
            want_index, spreads = _oracle_best(*args)
            for j, (a, b) in enumerate(zip(got[1], spreads)):
                if not abs(a - b) <= 1e-9:
                    raise _Mismatch("spread of candidate " + str(j) + " is wrong (tolerance 1e-9)")
            if got[0] != want_index:
                raise _Mismatch("chosen candidate is wrong (ties go to the lowest index)")
        run("best_model " + str(i) + " " + _show(args), best_model, args, compare)

    nan, inf = float('nan'), float('inf')
    model = (1.0, 0.5, 0.1, 0.1, 9.81)
    ref = (0.5, 0.0, 0.0)
    energies = [1.0, 1.1, 1.2]
    methods = ["Euler", "rk", "RK4", "", None, 1, True, ["euler"], "semi", "symplectic "]
    angle = [nan, inf, -inf, True, 100.01, -100.01, "0", None]
    signatures = [
        ("acceleration", ("q", "qd", "tau", "model"), (0.5, 0.0, 0.0, model)),
        ("energy", ("q", "qd", "model"), (0.5, 0.0, model)),
        ("small_angle_period", ("model",), (model,)),
        ("step", ("method", "q", "qd", "tau", "h", "model"), ("rk4", 0.5, 0.0, 0.0, 0.01, model)),
        ("energy_trace", ("method", "q0", "qd0", "h", "steps", "model"),
         ("rk4", 0.5, 0.0, 0.01, 5, model)),
        ("energy_drift", ("energies",), (energies,)),
        ("computed_torque", ("q", "qd", "ref", "kp", "kd", "tau_max", "model"),
         (0.0, 0.0, ref, 20.0, 8.0, 5.0, model)),
        ("regulate", ("q0", "qd0", "q_ref", "kp", "kd", "tau_max", "h", "steps", "method",
                      "plant", "controller"),
         (0.0, 0.0, 0.5, 20.0, 8.0, 5.0, 0.01, 5, "rk4", model, model)),
        ("best_model", ("qs", "qds", "candidates"), ([0.1, 0.2, 0.3], [0.0, 0.1, 0.2], [model])),
    ]
    bad = {
        "method": methods,
        "q": angle, "q0": angle, "q_ref": angle,
        "qd": angle, "qd0": angle, "tau": angle,
        "h": [0.0, -0.01, 0.051, nan, inf, True, "0.01", None],
        "steps": [0, -1, 1001, 5.0, True, nan, "5", None],
        "kp": [nan, inf, -0.01, 1000.01, True, "1", None],
        "kd": [nan, inf, -0.01, 200.01, False, "1", None],
        "tau_max": [0.0, -1.0, 100.01, nan, inf, True, "1", None],
        "model": _bad_models(), "plant": _bad_models(), "controller": _bad_models(),
        "ref": [(0.5, 0.0), (0.5, 0.0, 0.0, 0.0), (100.01, 0.0, 0.0), (0.5, 100.01, 0.0),
                (0.5, 0.0, 1000.01), (nan, 0.0, 0.0), (0.5, inf, 0.0), (True, 0.0, 0.0),
                ("0.5", 0.0, 0.0), 0.5, None, [[0.5], 0.0, 0.0]],
        "energies": [[], (), [1.0], [1.0] * 1002, [1.0, nan], [1.0, inf], [1.0, True],
                     [1.0, "x"], [1.0, 2e200], [-2e200, 1.0], "abc", {0: 1.0}, None, 5],
        "qs": [[], [0.1], [0.1] * 201, [0.1, nan], [0.1, 100.01], [0.1, True], [0.1, "x"],
               [0.1, 0.2, 0.3, 0.4], "abc", None, 5],
        "qds": [[], [0.1], [0.1] * 201, [0.1, nan], [0.1, 100.01], [0.1, True], [0.1, "x"],
                [0.1], "abc", None, 5],
        "candidates": [[], (), [model] * 11, [model, (1.0,)], [model, None], "abc", None, 5,
                       [(1.0, 0.5, 0.1, 0.1, nan)], model],
    }
    for title, names_args, args in [(s[0], s[1], s[2]) for s in signatures]:
        function = functions[title]
        for slot, name in enumerate(names_args):
            for value in bad[name]:
                trial = args[:slot] + (value,) + args[slot+1:]
                shown = repr(value)
                label = ("invalid " + title + "(" + name + "="
                         + (shown if len(shown) <= 24 else shown[:21] + "...") + ")")
                calls[title] = calls.get(title, 0) + 1
                try:
                    function(*trial)
                except ValueError:
                    continue
                except NotImplementedError:
                    missing.setdefault(title, []).append(label)
                    continue
                except Exception as error:
                    failures.append(label + ": raised " + type(error).__name__
                                    + " instead of ValueError")
                    continue
                failures.append(label + ": returned instead of raising ValueError")

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
    print("CoreLab manual pendulum dynamics self-check - practice only, no signed evidence")
    for note in notes:
        print("Note: " + note)
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
