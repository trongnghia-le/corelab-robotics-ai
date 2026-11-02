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
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('dynamics_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L08-dynamics.v1.py'
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
require(not any(isinstance(node, ast.Attribute) and node.attr in ('system', 'popen', 'urlopen')
                for node in ast.walk(tree)), 'kit touches the system')
NAMES = ('acceleration', 'energy', 'small_angle_period', 'step', 'energy_trace',
         'energy_drift', 'computed_torque', 'regulate', 'best_model')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in NAMES),
        'starter functions must sit above the spoiler banner')
require(text.index('def _oracle_step') > spoiler and text.index('_ACC_CASES = ') > spoiler,
        'oracle and case tables must sit below the spoiler banner')
for name in NAMES:
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    require(isinstance(node.body[0], ast.Raise), 'starter ' + name + ' must raise')
spec = importlib.util.spec_from_file_location('dynamics_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(len(starter) == 9 and all('not implemented yet' in line for line in starter),
        'unimplemented starter must report each function once: ' + str(starter))


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return [dec(v) for v in value]
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def entry(structure, names, args):
    return {'structure': structure, 'inputs': {n: dec(v) for n, v in zip(names, args)}}


expected_samples = (
    [entry('dynamics.acceleration@1', ('q', 'qd', 'tau', 'model'), a) for a, _ in kit._ACC_CASES]
    + [entry('dynamics.energy@1', ('q', 'qd', 'model'), a) for a, _ in kit._ENERGY_CASES]
    + [entry('dynamics.period@1', ('model',), a) for a, _ in kit._PERIOD_CASES]
    + [entry('dynamics.step@1', ('method', 'q', 'qd', 'tau', 'h', 'model'), a)
       for a, _ in kit._STEP_CASES]
    + [entry('dynamics.energy-trace@1', ('method', 'q0', 'qd0', 'h', 'steps', 'model'), a)
       for a, _ in kit._TRACE_CASES]
    + [entry('dynamics.energy-drift@1', ('energies',), a) for a, _ in kit._DRIFT_CASES]
    + [entry('dynamics.computed-torque@1',
             ('q', 'qd', 'ref', 'kp', 'kd', 'tau_max', 'model'), a) for a, _ in kit._CT_CASES]
    + [entry('dynamics.regulate@1',
             ('q0', 'qd0', 'q_ref', 'kp', 'kd', 'tau_max', 'h', 'steps', 'method', 'plant',
              'controller'), a) for _, a in kit._REG_CASES]
    + [entry('dynamics.best-model@1', ('qs', 'qds', 'candidates'), a) for a in kit._BEST_CASES])
samples = json.loads((root / 'content/labs/L08-dynamics.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L08-dynamics'], 'samples must hold only L08-dynamics')
require(samples['kits']['L08-dynamics'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')


# ---- author reference implementation (validated, parametrised for mutants) ----
METHODS = ('euler', 'symplectic', 'rk4')
BOUNDS = ((0.5, 10), (0.2, 1), (0, 1), (0, 0.5), (1, 20))


def num(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError


def positive(value, high):
    num(value, 0, high)
    if value <= 0:
        raise ValueError


def check_model(model):
    if not isinstance(model, (list, tuple)) or len(model) != 5:
        raise ValueError
    for value, (low, high) in zip(model, BOUNDS):
        num(value, low, high)


def check_method(method):
    if type(method) is not str or method not in METHODS:
        raise ValueError


def check_state(*values):
    for v in values:
        num(v, -100, 100)


def check_steps(steps):
    if type(steps) is not int or not 1 <= steps <= 1000:
        raise ValueError


def check_ref(ref):
    if not isinstance(ref, (list, tuple)) or len(ref) != 3:
        raise ValueError
    num(ref[0], -100, 100)
    num(ref[1], -100, 100)
    num(ref[2], -1000, 1000)


def std_acc(q, qd, tau, model):
    m, lc, ic, b, g = model
    return (tau - b*qd - m*g*lc*math.sin(q))/(ic + m*lc*lc)


def std_energy(q, qd, model):
    m, lc, ic, b, g = model
    return 0.5*(ic + m*lc*lc)*qd*qd + m*g*lc*(1 - math.cos(q))


def std_period(model):
    m, lc, ic, b, g = model
    return 2*math.pi*math.sqrt((ic + m*lc*lc)/(m*g*lc))


def std_step(method, q, qd, tau, h, model, acc):
    if method == 'euler':
        return (q + h*qd, qd + h*acc(q, qd, tau, model))
    if method == 'symplectic':
        qd_next = qd + h*acc(q, qd, tau, model)
        return (q + h*qd_next, qd_next)

    def f(s):
        return (s[1], acc(s[0], s[1], tau, model))
    k1 = f((q, qd))
    k2 = f((q + 0.5*h*k1[0], qd + 0.5*h*k1[1]))
    k3 = f((q + 0.5*h*k2[0], qd + 0.5*h*k2[1]))
    k4 = f((q + h*k3[0], qd + h*k3[1]))
    return (q + h/6*(k1[0] + 2*k2[0] + 2*k3[0] + k4[0]),
            qd + h/6*(k1[1] + 2*k2[1] + 2*k3[1] + k4[1]))


def std_trace(method, q0, qd0, h, steps, model, stepf, en):
    q, qd, out = q0, qd0, [en(q0, qd0, model)]
    for _ in range(steps):
        q, qd = stepf(method, q, qd, 0.0, h, model)
        out.append(en(q, qd, model))
    return out


def std_drift(es):
    return (es[-1] - es[0], max(abs(e - es[0]) for e in es))


def std_ct(q, qd, ref, kp, kd, tmax, model):
    m, lc, ic, b, g = model
    raw = ((ic + m*lc*lc)*(ref[2] + kd*(ref[1] - qd) + kp*(ref[0] - q))
           + b*qd + m*g*lc*math.sin(q))
    return (raw, max(-tmax, min(tmax, raw)))


def std_reg(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller, stepf, ctf):
    q, qd, out = q0, qd0, []
    for _ in range(steps):
        tau = ctf(q, qd, (q_ref, 0.0, 0.0), kp, kd, tmax, controller)[1]
        q, qd = stepf(method, q, qd, tau, h, plant)
        out.append((q, qd, tau))
    return out


def std_best(qs, qds, cands, en):
    spreads = []
    for c in cands:
        es = [en(q, v, c) for q, v in zip(qs, qds)]
        top = max(es)
        spreads.append(0.0 if top <= 0 else (top - min(es))/top)
    low = min(spreads)
    return (min(i for i, s in enumerate(spreads) if s <= low + 1e-9), spreads)


def make(**o):
    """Public validated functions; any piece may be replaced by a buggy variant."""
    acc, en, per = o.get('acc', std_acc), o.get('en', std_energy), o.get('per', std_period)
    if 'stepcore' in o:
        def stepf(method, q, qd, tau, h, model):
            return o['stepcore'](method, q, qd, tau, h, model, acc)
    else:
        def stepf(method, q, qd, tau, h, model):
            return std_step(method, q, qd, tau, h, model, acc)
    ctf = o.get('ct', std_ct)
    fns = {}

    def acceleration(q, qd, tau, model):
        check_state(q, qd, tau)
        check_model(model)
        return acc(q, qd, tau, model)

    def energy(q, qd, model):
        check_state(q, qd)
        check_model(model)
        return en(q, qd, model)

    def small_angle_period(model):
        check_model(model)
        return per(model)

    def step(method, q, qd, tau, h, model):
        check_method(method)
        check_state(q, qd, tau)
        positive(h, 0.05)
        check_model(model)
        return stepf(method, q, qd, tau, h, model)

    def energy_trace(method, q0, qd0, h, steps, model):
        check_method(method)
        check_state(q0, qd0)
        positive(h, 0.05)
        check_steps(steps)
        check_model(model)
        if 'trace' in o:
            return o['trace'](method, q0, qd0, h, steps, model, stepf, en)
        return std_trace(method, q0, qd0, h, steps, model, stepf, en)

    def energy_drift(energies):
        if not isinstance(energies, (list, tuple)) or not 2 <= len(energies) <= 1001:
            raise ValueError
        for e in energies:
            num(e, -1e200, 1e200)
        return o.get('drift', std_drift)(energies)

    def computed_torque(q, qd, ref, kp, kd, tau_max, model):
        check_state(q, qd)
        check_ref(ref)
        num(kp, 0, 1000)
        num(kd, 0, 200)
        positive(tau_max, 100)
        check_model(model)
        return ctf(q, qd, ref, kp, kd, tau_max, model)

    def regulate(q0, qd0, q_ref, kp, kd, tau_max, h, steps, method, plant, controller):
        check_state(q0, qd0, q_ref)
        num(kp, 0, 1000)
        num(kd, 0, 200)
        positive(tau_max, 100)
        positive(h, 0.05)
        check_steps(steps)
        check_method(method)
        check_model(plant)
        check_model(controller)
        if 'reg' in o:
            return o['reg'](q0, qd0, q_ref, kp, kd, tau_max, h, steps, method, plant,
                            controller, stepf, ctf)
        return std_reg(q0, qd0, q_ref, kp, kd, tau_max, h, steps, method, plant, controller,
                       stepf, ctf)

    def best_model(qs, qds, candidates):
        for seq in (qs, qds):
            if not isinstance(seq, (list, tuple)) or not 2 <= len(seq) <= 200:
                raise ValueError
            for v in seq:
                num(v, -100, 100)
        if len(qs) != len(qds):
            raise ValueError
        if not isinstance(candidates, (list, tuple)) or not 1 <= len(candidates) <= 10:
            raise ValueError
        for c in candidates:
            check_model(c)
        return o.get('best', std_best)(qs, qds, candidates, en)

    for f in (acceleration, energy, small_angle_period, step, energy_trace, energy_drift,
              computed_torque, regulate, best_model):
        fns[f.__name__] = f
    return fns


reference = make()


def run_with(over):
    for name, fn in reference.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in reference.items():
        setattr(kit, name, fn)
    return result


require(run_with({}) == [], 'author reference must pass: ' + str(run_with({})))


# ---- independent cross-checks of the oracle (not through the oracle code) ----
def lcg(seed):
    state = seed
    while True:
        state = (1103515245*state + 12345) % 2**31
        yield state/2**31


rand = lcg(7)


def uniform(low, high):
    return low + (high - low)*next(rand)


def rk4_ref(q, qd, tau, h, model):
    m, lc, ic, b, g = model
    inertia = ic + m*lc*lc

    def a(q_, qd_):
        return (tau - b*qd_ - m*g*lc*math.sin(q_))/inertia
    k1q, k1v = qd, a(q, qd)
    k2q, k2v = qd + h/2*k1v, a(q + h/2*k1q, qd + h/2*k1v)
    k3q, k3v = qd + h/2*k2v, a(q + h/2*k2q, qd + h/2*k2v)
    k4q, k4v = qd + h*k3v, a(q + h*k3q, qd + h*k3v)
    return (q + h/6*(k1q + 2*k2q + 2*k3q + k4q), qd + h/6*(k1v + 2*k2v + 2*k3v + k4v))


for _ in range(60):
    model = (uniform(0.5, 10), uniform(0.2, 1), uniform(0, 1), uniform(0, 0.5), uniform(1, 20))
    q, qd, tau, h = uniform(-6, 6), uniform(-8, 8), uniform(-10, 10), uniform(0.005, 0.05)
    one = kit._oracle_step('rk4', q, qd, tau, h, model)
    fine = (q, qd)
    for _k in range(64):
        fine = rk4_ref(fine[0], fine[1], tau, h/64, model)
    require(abs(one[0] - fine[0]) < 5e-6*max(1, abs(fine[0]))
            and abs(one[1] - fine[1]) < 5e-6*max(1, abs(fine[1])),
            'oracle RK4 step disagrees with a 64-substep solve')
    ours = rk4_ref(q, qd, tau, h, model)
    require(abs(one[0] - ours[0]) < 1e-12*max(1, abs(ours[0]))
            and abs(one[1] - ours[1]) < 1e-12*max(1, abs(ours[1])), 'oracle RK4 formula')
    # the oracle's other helpers against the reference functions
    require(abs(kit._oracle_acc(q, qd, tau, model) - reference['acceleration'](q, qd, tau, model)) < 1e-12,
            'oracle acceleration')
# linearised one-step formulas (tiny angle, so sin q = q to 1e-20)
w2 = 9.81
for h in (0.01, 0.03, 0.05):
    z = math.sqrt(w2)*h
    q, qd = 1e-7, 2e-7
    e = kit._oracle_step('euler', q, qd, 0.0, h, (1, 1, 0, 0, 9.81))
    require(abs(e[0] - (q + h*qd)) < 1e-18 and abs(e[1] - (qd - h*w2*q)) < 1e-15, 'euler linear')
    s = kit._oracle_step('symplectic', q, qd, 0.0, h, (1, 1, 0, 0, 9.81))
    require(abs(s[1] - (qd - h*w2*q)) < 1e-15 and abs(s[0] - (q + h*(qd - h*w2*q))) < 1e-15,
            'symplectic linear')
    r = kit._oracle_step('rk4', q, qd, 0.0, h, (1, 1, 0, 0, 9.81))
    taylor_q = q*(1 - z*z/2 + z**4/24) + qd*h*(1 - z*z/6)
    require(abs(r[0] - taylor_q) < 1e-15, 'rk4 linear Taylor formula')
    en0 = 0.5*qd*qd + 0.5*w2*q*q
    en1 = 0.5*e[1]**2 + 0.5*w2*e[0]**2
    require(abs(en1/en0 - (1 + z*z)) < 1e-9, 'explicit Euler multiplies E by 1 + (hw)^2')
# energy conservation with a fine RK4 (continuous-model invariant)
model = (1.5, 0.8, 0.05, 0.0, 9.81)
trace = kit._oracle_trace('rk4', 2.5, 0.0, 0.002, 2500, model)
require(max(abs(e - trace[0]) for e in trace) < 1e-9*trace[0], 'fine RK4 conserves E')
# measured period of a small swing against 2*pi*sqrt(I/(m g lc)) and the amplitude correction
q, qd, t, h = 0.05, 0.0, 0.0, 0.0005
crossing = None
while crossing is None:
    q_next, qd_next = rk4_ref(q, qd, 0.0, h, model)
    t += h
    if qd <= 0 < qd_next:
        crossing = t - h*qd_next/(qd_next - qd)
    q, qd = q_next, qd_next
period = kit._oracle_period(model)
require(abs(2*crossing - period*(1 + 0.05**2/16)) < 2e-4, 'small-angle period vs simulation')
# critically damped regulator against the closed form (perfect model, ZOH)
reg = kit._oracle_regulate(0.0, 0.0, 0.8, 25, 10, 100, 0.001, 1000, 'rk4', (1, 1, 0, 0, 9.81),
                           (1, 1, 0, 0, 9.81))
for k in (99, 499, 999):
    t = 0.001*(k + 1)
    require(abs((0.8 - reg[k][0]) - 0.8*(1 + 5*t)*math.exp(-5*t)) < 2e-3, 'critical damping')
# a wrong gravity shifts the steady angle: kp*I*e = (g_true - g_model) m lc sin q
plant = (1.0, 1.0, 0.0, 0.2, 9.81)
reg = kit._oracle_regulate(0.0, 0.0, 0.5, 100, 20, 100, 0.001, 4000, 'rk4', plant,
                           (1.0, 1.0, 0.0, 0.2, 5.0))
q_end = reg[-1][0]
require(abs(100*(0.5 - q_end) - (9.81 - 5.0)*math.sin(q_end)) < 5e-3, 'steady offset of a wrong g')
# flat-energy diagnosis on a fine independent solve
truth = (1.5, 0.8, 0.05, 0.0, 9.81)
q, qd, qs, qds = 1.2, 0.0, [], []
for k in range(1200):
    q, qd = rk4_ref(q, qd, 0.0, 0.001, truth)
    if k % 100 == 99:
        qs.append(q)
        qds.append(qd)
index, spreads = kit._oracle_best(qs, qds, [(1.5, 0.8, 0.05, 0, 7.0), truth, (1.5, 0.8, 0.6, 0, 9.81)])
require(index == 1 and spreads[1] < 1e-8 and spreads[0] > 0.05 and spreads[2] > 0.05, 'diagnosis')


# ---- valid alternatives (different formulations) ----
def acc_norm(q, qd, tau, model):
    m, lc, ic, b, g = model
    inertia = ic + m*lc**2
    return tau/inertia - (b/inertia)*qd - (m*g*lc/inertia)*math.sin(q)


def energy_half(q, qd, model):
    m, lc, ic, b, g = model
    return (ic + m*lc*lc)/2*qd**2 + 2*m*g*lc*math.sin(q/2)**2


def period_w(model):
    m, lc, ic, b, g = model
    w = math.sqrt(m*g*lc/(ic + m*lc*lc))
    return 2*math.pi/w


TABLEAU = ((0.5,), (0.0, 0.5), (0.0, 0.0, 1.0))
WEIGHTS = (1/6, 1/3, 1/3, 1/6)


def step_tableau(method, q, qd, tau, h, model, acc):
    """Generic explicit Runge-Kutta; euler and symplectic written as two sequential updates."""
    if method == 'euler':
        qdd = acc(q, qd, tau, model)
        return [q + h*qd, qd + h*qdd]
    if method == 'symplectic':
        qd2 = qd + acc(q, qd, tau, model)*h
        return [q + qd2*h, qd2]
    ks = []
    for row in ((),) + TABLEAU:
        sq = q + h*sum(c*k[0] for c, k in zip(row, ks))
        sv = qd + h*sum(c*k[1] for c, k in zip(row, ks))
        ks.append((sv, acc(sq, sv, tau, model)))
    return [q + h*sum(w*k[0] for w, k in zip(WEIGHTS, ks)),
            qd + h*sum(w*k[1] for w, k in zip(WEIGHTS, ks))]


def trace_listcomp(method, q0, qd0, h, steps, model, stepf, en):
    states = [(q0, qd0)]
    for _ in range(steps):
        states.append(tuple(stepf(method, states[-1][0], states[-1][1], 0.0, h, model)))
    return tuple(en(q, v, model) for q, v in states)


def drift_envelope(es):
    first = es[0]
    return [es[-1] - first, max(max(es) - first, first - min(es))]


def ct_inverse(q, qd, ref, kp, kd, tmax, model):
    """Commanded acceleration, then the torque that makes the model deliver it."""
    m, lc, ic, b, g = model
    command = ref[2] + kd*(ref[1] - qd) + kp*(ref[0] - q)
    raw = (ic + m*lc**2)*command + b*qd + m*g*lc*math.sin(q)
    return [raw, sorted((-tmax, raw, tmax))[1]]


def reg_inline(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller, stepf, ctf):
    """Own loop and own torque line; never calls the shared helpers."""
    cm, cl, ci, cb, cg = controller
    out = []
    state = (q0, qd0)
    for _ in range(steps):
        raw = (ci + cm*cl*cl)*(kd*(0 - state[1]) + kp*(q_ref - state[0])) + cb*state[1] \
            + cm*cg*cl*math.sin(state[0])
        tau = min(tmax, max(-tmax, raw))
        state = tuple(std_step(method, state[0], state[1], tau, h, plant, std_acc))
        out.append((state[0], state[1], tau))
    return tuple(out)


def best_ratio(qs, qds, cands, en):
    spreads = []
    for c in cands:
        es = [en(q, v, c) for q, v in zip(qs, qds)]
        spreads.append(0.0 if max(es) <= 0 else 1.0 - min(es)/max(es))
    best = 0
    for i, s in enumerate(spreads):
        if s < min(spreads) + 1e-9:
            best = i
            break
    return (best, tuple(spreads))


alternatives = [
    ('author reference', {}),
    ('normalised physics, half-angle energy, w-based period',
     {'acc': acc_norm, 'en': energy_half, 'per': period_w}),
    ('Butcher-tableau integrators with list results, tuple energy trace',
     {'stepcore': step_tableau, 'trace': trace_listcomp}),
    ('inverse-dynamics torque (list result), envelope drift, inline regulate loop',
     {'ct': ct_inverse, 'drift': drift_envelope, 'reg': reg_inline}),
    ('ratio spread with tuple result and first-minimum search',
     {'best': best_ratio}),
    ('everything alternative together',
     {'acc': acc_norm, 'en': energy_half, 'per': period_w, 'stepcore': step_tableau,
      'trace': trace_listcomp, 'drift': drift_envelope, 'ct': ct_inverse, 'reg': reg_inline,
      'best': best_ratio}),
]
for label, parts in alternatives:
    result = run_with(make(**parts))
    require(result == [], 'false reject (' + label + '): ' + str(result[:6]))


# ---- injected bugs ----
def sym_first(method, q, qd, tau, h, model, acc):
    return std_step('symplectic' if method == 'euler' else method, q, qd, tau, h, model, acc)


def euler_for_symplectic(method, q, qd, tau, h, model, acc):
    return std_step('euler' if method == 'symplectic' else method, q, qd, tau, h, model, acc)


def position_first(method, q, qd, tau, h, model, acc):
    if method != 'symplectic':
        return std_step(method, q, qd, tau, h, model, acc)
    q2 = q + h*qd
    return (q2, qd + h*acc(q2, qd, tau, model))


def implicit_damping(method, q, qd, tau, h, model, acc):
    if method != 'symplectic':
        return std_step(method, q, qd, tau, h, model, acc)
    m, lc, ic, b, g = model
    inertia = ic + m*lc*lc
    qd2 = (qd + h*(tau - m*g*lc*math.sin(q))/inertia)/(1 + h*b/inertia)
    return (q + h*qd2, qd2)


def rk4_custom(weights=(1, 2, 2, 1), half=0.5, tau_stages=True, divisor=6.0, hfinal=1.0):
    def run(method, q, qd, tau, h, model, acc):
        if method != 'rk4':
            return std_step(method, q, qd, tau, h, model, acc)
        t2 = tau if tau_stages else 0.0

        def f(s, t):
            return (s[1], acc(s[0], s[1], t, model))
        k1 = f((q, qd), tau)
        k2 = f((q + half*h*k1[0], qd + half*h*k1[1]), t2)
        k3 = f((q + half*h*k2[0], qd + half*h*k2[1]), t2)
        k4 = f((q + h*k3[0], qd + h*k3[1]), t2)
        w = weights
        return (q + hfinal*h/divisor*(w[0]*k1[0] + w[1]*k2[0] + w[2]*k3[0] + w[3]*k4[0]),
                qd + hfinal*h/divisor*(w[0]*k1[1] + w[1]*k2[1] + w[2]*k3[1] + w[3]*k4[1]))
    return run


def step_no_tau(method, q, qd, tau, h, model, acc):
    return std_step(method, q, qd, 0.0, h, model, acc)


def step_h_twice(method, q, qd, tau, h, model, acc):
    return std_step(method, q, qd, tau, h*h if method == 'euler' else h, model, acc)


def trace_no_initial(method, q0, qd0, h, steps, model, stepf, en):
    return std_trace(method, q0, qd0, h, steps, model, stepf, en)[1:]


def trace_always_symplectic(method, q0, qd0, h, steps, model, stepf, en):
    return std_trace('symplectic', q0, qd0, h, steps, model, stepf, en)


def trace_extra_step(method, q0, qd0, h, steps, model, stepf, en):
    return std_trace(method, q0, qd0, h, steps + 1, model, stepf, en)


def trace_flat(method, q0, qd0, h, steps, model, stepf, en):
    return [en(q0, qd0, model)]*(steps + 1)


def trace_revalidating(method, q0, qd0, h, steps, model, stepf, en):
    q, qd, out = q0, qd0, [en(q0, qd0, model)]
    for _ in range(steps):
        check_state(q, qd)
        q, qd = stepf(method, q, qd, 0.0, h, model)
        out.append(en(q, qd, model))
    return out


def trace_lagged(method, q0, qd0, h, steps, model, stepf, en):
    out = std_trace(method, q0, qd0, h, steps, model, stepf, en)
    return [out[0]] + out[:-1]


def trace_tau_one(method, q0, qd0, h, steps, model, stepf, en):
    q, qd, out = q0, qd0, [en(q0, qd0, model)]
    for _ in range(steps):
        q, qd = stepf(method, q, qd, 1.0, h, model)
        out.append(en(q, qd, model))
    return out


def ct_custom(gravity=1.0, inertia=True, perror=1.0, ff=True, damping=True, rate_ref=True,
              clip='sym', raw_clipped=False):
    def run(q, qd, ref, kp, kd, tmax, model):
        m, lc, ic, b, g = model
        command = (ref[2] if ff else 0.0) + kd*((ref[1] if rate_ref else 0.0) - qd) \
            + kp*perror*(ref[0] - q)
        raw = ((ic + m*lc*lc) if inertia else 1.0)*command + (b*qd if damping else 0.0) \
            + gravity*m*g*lc*math.sin(q)
        if clip == 'sym':
            tau = max(-tmax, min(tmax, raw))
        elif clip == 'positive':
            tau = max(0.0, min(tmax, raw))
        else:
            tau = min(tmax, raw)
        return (tau if raw_clipped else raw, tau)
    return run


def reg_plant_as_controller(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller,
                            stepf, ctf):
    return std_reg(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, plant, stepf, ctf)


def reg_controller_as_plant(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller,
                            stepf, ctf):
    return std_reg(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, controller, controller,
                   stepf, ctf)


def reg_unclipped_plant(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller,
                        stepf, ctf):
    q, qd, out = q0, qd0, []
    for _ in range(steps):
        raw, tau = ctf(q, qd, (q_ref, 0.0, 0.0), kp, kd, tmax, controller)
        q, qd = stepf(method, q, qd, raw, h, plant)
        out.append((q, qd, tau))
    return out


def reg_no_feedback(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller,
                    stepf, ctf):
    tau = ctf(q0, qd0, (q_ref, 0.0, 0.0), kp, kd, tmax, controller)[1]
    q, qd, out = q0, qd0, []
    for _ in range(steps):
        q, qd = stepf(method, q, qd, tau, h, plant)
        out.append((q, qd, tau))
    return out


def reg_pre_step(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller, stepf, ctf):
    q, qd, out = q0, qd0, []
    for _ in range(steps):
        tau = ctf(q, qd, (q_ref, 0.0, 0.0), kp, kd, tmax, controller)[1]
        out.append((q, qd, tau))
        q, qd = stepf(method, q, qd, tau, h, plant)
    return out


def reg_always_rk4(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller,
                   stepf, ctf):
    return std_reg(q0, qd0, q_ref, kp, kd, tmax, h, steps, 'rk4', plant, controller,
                   stepf, ctf)


def reg_revalidating(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller,
                     stepf, ctf):
    q, qd, out = q0, qd0, []
    for _ in range(steps):
        check_state(q, qd)
        tau = ctf(q, qd, (q_ref, 0.0, 0.0), kp, kd, tmax, controller)[1]
        q, qd = stepf(method, q, qd, tau, h, plant)
        out.append((q, qd, tau))
    return out


def reg_extra_entry(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller,
                    stepf, ctf):
    return [(q0, qd0, 0.0)] + std_reg(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant,
                                      controller, stepf, ctf)


def reg_ref_rate_error(q0, qd0, q_ref, kp, kd, tmax, h, steps, method, plant, controller,
                       stepf, ctf):
    """The controller is fed the negated rate."""
    q, qd, out = q0, qd0, []
    for _ in range(steps):
        tau = ctf(q, -qd, (q_ref, 0.0, 0.0), kp, kd, tmax, controller)[1]
        q, qd = stepf(method, q, qd, tau, h, plant)
        out.append((q, qd, tau))
    return out


def best_rule(pick):
    def run(qs, qds, cands, en):
        spreads = std_best(qs, qds, cands, en)[1]
        return pick(qs, qds, cands, en, spreads)
    return run


def spreads_of(qs, qds, cands, en, normalise):
    out = []
    for c in cands:
        es = [en(q, v, c) for q, v in zip(qs, qds)]
        out.append(normalise(es))
    return out


mutants = [
    ('gravity torque sign flipped', {'acc': lambda q, qd, tau, mo: (
        tau - mo[3]*qd + mo[0]*mo[4]*mo[1]*math.sin(q))/(mo[2] + mo[0]*mo[1]**2)}),
    ('cos instead of sin in the gravity torque', {'acc': lambda q, qd, tau, mo: (
        tau - mo[3]*qd - mo[0]*mo[4]*mo[1]*math.cos(q))/(mo[2] + mo[0]*mo[1]**2)}),
    ('inertia ignores ic', {'acc': lambda q, qd, tau, mo: (
        tau - mo[3]*qd - mo[0]*mo[4]*mo[1]*math.sin(q))/(mo[0]*mo[1]**2)}),
    ('inertia m*lc instead of m*lc^2', {'acc': lambda q, qd, tau, mo: (
        tau - mo[3]*qd - mo[0]*mo[4]*mo[1]*math.sin(q))/(mo[2] + mo[0]*mo[1])}),
    ('inertia uses ic only', {'acc': lambda q, qd, tau, mo: (
        tau - mo[3]*qd - mo[0]*mo[4]*mo[1]*math.sin(q))/(mo[2] if mo[2] else 1.0)}),
    ('gravity torque forgot lc', {'acc': lambda q, qd, tau, mo: (
        tau - mo[3]*qd - mo[0]*mo[4]*math.sin(q))/(mo[2] + mo[0]*mo[1]**2)}),
    ('damping omitted', {'acc': lambda q, qd, tau, mo: (
        tau - mo[0]*mo[4]*mo[1]*math.sin(q))/(mo[2] + mo[0]*mo[1]**2)}),
    ('damping sign flipped', {'acc': lambda q, qd, tau, mo: (
        tau + mo[3]*qd - mo[0]*mo[4]*mo[1]*math.sin(q))/(mo[2] + mo[0]*mo[1]**2)}),
    ('torque not divided by the inertia', {'acc': lambda q, qd, tau, mo: tau - (
        mo[3]*qd + mo[0]*mo[4]*mo[1]*math.sin(q))/(mo[2] + mo[0]*mo[1]**2)}),
    ('potential energy -m g lc cos q (no offset)', {'en': lambda q, qd, mo: 0.5*(
        mo[2] + mo[0]*mo[1]**2)*qd*qd - mo[0]*mo[4]*mo[1]*math.cos(q)}),
    ('potential energy m g lc (1 + cos q)', {'en': lambda q, qd, mo: 0.5*(
        mo[2] + mo[0]*mo[1]**2)*qd*qd + mo[0]*mo[4]*mo[1]*(1 + math.cos(q))}),
    ('kinetic energy without the half', {'en': lambda q, qd, mo: (
        mo[2] + mo[0]*mo[1]**2)*qd*qd + mo[0]*mo[4]*mo[1]*(1 - math.cos(q))}),
    ('kinetic energy ignores ic', {'en': lambda q, qd, mo: 0.5*(
        mo[0]*mo[1]**2)*qd*qd + mo[0]*mo[4]*mo[1]*(1 - math.cos(q))}),
    ('potential energy forgot lc', {'en': lambda q, qd, mo: 0.5*(
        mo[2] + mo[0]*mo[1]**2)*qd*qd + mo[0]*mo[4]*(1 - math.cos(q))}),
    ('period without the 2*pi', {'per': lambda mo: math.sqrt(
        (mo[2] + mo[0]*mo[1]**2)/(mo[0]*mo[4]*mo[1]))}),
    ('period ignores ic', {'per': lambda mo: 2*math.pi*math.sqrt(mo[1]/mo[4])}),
    ('damped period instead of the undamped one', {'per': lambda mo: 2*math.pi/math.sqrt(
        mo[0]*mo[4]*mo[1]/(mo[2] + mo[0]*mo[1]**2) - (mo[3]/(2*(mo[2] + mo[0]*mo[1]**2)))**2)}),
    ('euler written as semi-implicit', {'stepcore': sym_first}),
    ('symplectic written as explicit euler', {'stepcore': euler_for_symplectic}),
    ('symplectic updates the angle first', {'stepcore': position_first}),
    ('symplectic with implicit damping', {'stepcore': implicit_damping}),
    ('rk4 weights all equal', {'stepcore': rk4_custom(weights=(1, 1, 1, 1), divisor=4.0)}),
    ('rk4 stages advance by a full h', {'stepcore': rk4_custom(half=1.0)}),
    ('rk4 forgets tau in stages 2 to 4', {'stepcore': rk4_custom(tau_stages=False)}),
    ('rk4 final divisor 3', {'stepcore': rk4_custom(divisor=3.0)}),
    ('step ignores tau', {'stepcore': step_no_tau}),
    ('explicit euler uses h squared', {'stepcore': step_h_twice}),
    ('trace omits the initial energy', {'trace': trace_no_initial}),
    ('trace ignores the method', {'trace': trace_always_symplectic}),
    ('trace takes one step too many', {'trace': trace_extra_step}),
    ('trace is a flat line at E0', {'trace': trace_flat}),
    ('trace energies lag one step behind', {'trace': trace_lagged}),
    ('trace applies a unit torque', {'trace': trace_tau_one}),
    ('trace re-validates intermediate states', {'trace': trace_revalidating}),
    ('drift as a fraction of E0', {'drift': lambda es: (
        (es[-1] - es[0])/es[0], max(abs(e - es[0]) for e in es)/es[0])}),
    ('drift final change unsigned', {'drift': lambda es: (
        abs(es[-1] - es[0]), max(abs(e - es[0]) for e in es))}),
    ('drift max measured step to step', {'drift': lambda es: (
        es[-1] - es[0], max(abs(b - a) for a, b in zip(es, es[1:])))}),
    ('drift max change signed', {'drift': lambda es: (
        es[-1] - es[0], max(e - es[0] for e in es))}),
    ('drift measured against the last energy', {'drift': lambda es: (
        es[0] - es[-1], max(abs(e - es[-1]) for e in es))}),
    ('torque gravity sign flipped', {'ct': ct_custom(gravity=-1.0)}),
    ('torque without gravity compensation', {'ct': ct_custom(gravity=0.0)}),
    ('torque without the inertia factor', {'ct': ct_custom(inertia=False)}),
    ('torque position error sign flipped', {'ct': ct_custom(perror=-1.0)}),
    ('torque drops the acceleration feedforward', {'ct': ct_custom(ff=False)}),
    ('torque without damping compensation', {'ct': ct_custom(damping=False)}),
    ('torque ignores the reference rate', {'ct': ct_custom(rate_ref=False)}),
    ('torque clipped to [0, tau_max]', {'ct': ct_custom(clip='positive')}),
    ('torque clipped on the upper side only', {'ct': ct_custom(clip='upper')}),
    ('torque raw value returned clipped', {'ct': ct_custom(raw_clipped=True)}),
    ('regulate uses the plant model in the controller', {'reg': reg_plant_as_controller}),
    ('regulate integrates the controller model', {'reg': reg_controller_as_plant}),
    ('regulate sends the unclipped torque to the plant', {'reg': reg_unclipped_plant}),
    ('regulate has no feedback', {'reg': reg_no_feedback}),
    ('regulate records pre-step states', {'reg': reg_pre_step}),
    ('regulate always uses rk4', {'reg': reg_always_rk4}),
    ('regulate re-validates intermediate states', {'reg': reg_revalidating}),
    ('regulate returns an extra initial entry', {'reg': reg_extra_entry}),
    ('regulate feeds back the negated rate', {'reg': reg_ref_rate_error}),
    ('best_model picks the largest spread', {'best': best_rule(
        lambda qs, qds, cands, en, sp: (sp.index(max(sp)), sp))}),
    ('best_model uses the absolute energy range', {'best': best_rule(
        lambda qs, qds, cands, en, sp: (lambda a: (a.index(min(a)), a))(spreads_of(
            qs, qds, cands, en, lambda es: max(es) - min(es))))}),
    ('best_model ties go to the last index', {'best': best_rule(
        lambda qs, qds, cands, en, sp: (max(i for i, s in enumerate(sp) if s <= min(sp) + 1e-9), sp))}),
    ('best_model looks at the first and last sample only', {'best': best_rule(
        lambda qs, qds, cands, en, sp: (lambda a: (a.index(min(a)), a))(spreads_of(
            qs, qds, cands, en, lambda es: abs(es[-1] - es[0])/max(es[0], es[-1], 1e-300))))}),
    ('best_model spread relative to the mean', {'best': best_rule(
        lambda qs, qds, cands, en, sp: (lambda a: (a.index(min(a)), a))(spreads_of(
            qs, qds, cands, en, lambda es: (max(es) - min(es))/(sum(es)/len(es)))))}),
    ('best_model exact minimum without the 1e-9 tie rule', {'best': best_rule(
        lambda qs, qds, cands, en, sp: (sp.index(min(sp)), sp))}),
    ('best_model returns the spreads sorted', {'best': best_rule(
        lambda qs, qds, cands, en, sp: (sp.index(min(sp)), sorted(sp)))}),
    ('best_model standard deviation instead of range', {'best': best_rule(
        lambda qs, qds, cands, en, sp: (lambda a: (a.index(min(a)), a))(spreads_of(
            qs, qds, cands, en, lambda es: math.sqrt(sum((e - sum(es)/len(es))**2 for e in es)
                                                     /len(es))/max(es))))}),
]


def accepts_when(check, name, value):
    """Reference except one named validation gap: returns a plausible value instead."""
    def run(*args):
        if check(*args):
            return value
        return reference[name](*args)
    return run


def is_real(v):
    return type(v) in (int, float) and math.isfinite(v)


def model_gap(index, predicate):
    """`index` is the position of a model argument; the gap fires on predicate(model)."""
    def check(*args):
        mo = args[index]
        return isinstance(mo, (list, tuple)) and predicate(mo)
    return check


mutants += [
    ('bool q accepted', {'acceleration': accepts_when(lambda *a: type(a[0]) is bool, 'acceleration', 0.0)}),
    ('NaN model entry accepted', {'energy': accepts_when(
        model_gap(2, lambda mo: any(type(v) is float and v != v for v in mo)), 'energy', 0.0)}),
    ('six-entry model accepted', {'small_angle_period': accepts_when(
        model_gap(0, lambda mo: len(mo) == 6), 'small_angle_period', 1.0)}),
    ('model below the g bound accepted', {'acceleration': accepts_when(
        model_gap(3, lambda mo: len(mo) == 5 and is_real(mo[4]) and mo[4] < 1), 'acceleration', 0.0)}),
    ('negative damping accepted', {'energy': accepts_when(
        model_gap(2, lambda mo: len(mo) == 5 and is_real(mo[3]) and mo[3] < 0), 'energy', 0.0)}),
    ('method matched case-insensitively', {'step': lambda method, *a: reference['step'](
        method.lower() if type(method) is str else method, *a)}),
    ('unknown method falls back to rk4', {'step': lambda method, *a: reference['step'](
        'rk4' if type(method) is str and method not in METHODS else method, *a)}),
    ('float steps accepted', {'energy_trace': lambda *a: reference['energy_trace'](
        *a[:4], int(a[4]), *a[5:]) if type(a[4]) is float and math.isfinite(a[4]) and a[4] >= 1
        else reference['energy_trace'](*a)}),
    ('bool steps accepted', {'regulate': lambda *a: reference['regulate'](
        *a[:7], int(a[7]), *a[8:]) if type(a[7]) is bool and a[7] else reference['regulate'](*a)}),
    ('h = 0 accepted', {'step': accepts_when(lambda *a: len(a) > 4 and a[4] == 0 and type(a[4]) is float,
                                            'step', (0.0, 0.0))}),
    ('tau_max = 0 accepted', {'computed_torque': accepts_when(
        lambda *a: a[5] == 0 and type(a[5]) is float, 'computed_torque', (0.0, 0.0))}),
    ('negative kp accepted', {'regulate': accepts_when(
        lambda *a: is_real(a[3]) and a[3] < 0, 'regulate', [(0.0, 0.0, 0.0)])}),
    ('bad ref length accepted', {'computed_torque': accepts_when(
        lambda *a: isinstance(a[2], (list, tuple)) and len(a[2]) == 2, 'computed_torque', (0.0, 0.0))}),
    ('single-sample best_model accepted', {'best_model': accepts_when(
        lambda *a: isinstance(a[0], (list, tuple)) and len(a[0]) == 1, 'best_model', (0, [0.0]))}),
    ('mismatched qs/qds lengths accepted', {'best_model': accepts_when(
        lambda *a: isinstance(a[0], (list, tuple)) and isinstance(a[1], (list, tuple))
        and len(a[0]) != len(a[1]) and len(a[0]) > 1 and len(a[1]) > 1, 'best_model', (0, [0.0]))}),
    ('NaN energy accepted in drift', {'energy_drift': accepts_when(
        lambda *a: isinstance(a[0], list) and any(type(v) is float and v != v for v in a[0]),
        'energy_drift', (0.0, 0.0))}),
    ('single-energy list accepted', {'energy_drift': accepts_when(
        lambda *a: isinstance(a[0], list) and len(a[0]) == 1, 'energy_drift', (0.0, 0.0))}),
    ('over-strict: |q| above 10 rejected', {'acceleration': lambda q, *a: (_ for _ in ()).throw(
        ValueError()) if is_real(q) and abs(q) > 10 else reference['acceleration'](q, *a)}),
    ('over-strict: steps == 1000 rejected', {'energy_trace': lambda *a: (_ for _ in ()).throw(
        ValueError()) if a[4] == 1000 and type(a[4]) is int else reference['energy_trace'](*a)}),
    ('over-strict: lc == 1 rejected', {'energy': lambda q, qd, mo: (_ for _ in ()).throw(
        ValueError()) if isinstance(mo, (list, tuple)) and len(mo) == 5 and mo[1] == 1
        else reference['energy'](q, qd, mo)}),
    ('over-strict: b == 0.5 rejected', {'acceleration': lambda q, qd, tau, mo: (_ for _ in ()).throw(
        ValueError()) if isinstance(mo, (list, tuple)) and len(mo) == 5 and mo[3] == 0.5
        else reference['acceleration'](q, qd, tau, mo)}),
    ('over-strict: tuples rejected for models', {'small_angle_period': lambda mo: (_ for _ in ()).throw(
        ValueError()) if isinstance(mo, tuple) else reference['small_angle_period'](mo)}),
    ('over-strict: int model entries rejected', {'small_angle_period': lambda mo: (_ for _ in ()).throw(
        ValueError()) if isinstance(mo, (list, tuple)) and any(type(v) is int for v in mo)
        else reference['small_angle_period'](mo)}),
]


def mutates_model(function_name, index):
    def run(*args):
        result = reference[function_name](*args)
        if isinstance(args[index], list):
            args[index][3] = 0.0
        return result
    return run


def sorts_input(function_name, index):
    def run(*args):
        result = reference[function_name](*args)
        if isinstance(args[index], list):
            args[index].sort()
        return result
    return run


def returns_nan(function_name, shape):
    def run(*args):
        reference[function_name](*args)
        return shape
    return run


mutants += [
    ('model list mutated', {'small_angle_period': mutates_model('small_angle_period', 0)}),
    ('energy list sorted in place', {'energy_drift': sorts_input('energy_drift', 0)}),
    ('qs sorted in place', {'best_model': sorts_input('best_model', 0)}),
    ('NaN energy returned', {'energy': returns_nan('energy', float('nan'))}),
    ('bool index returned', {'best_model': lambda *a: (
        lambda r: (bool(r[0]) if r[0] in (0, 1) else r[0], r[1]))(reference['best_model'](*a))}),
    ('flat list of numbers returned for step', {'step': lambda *a: [reference['step'](*a)[0]]}),
]
for label, over in mutants:
    patched = make(**over) if not all(k in reference for k in over) else dict(over)
    require(run_with(patched), 'false accept: ' + label)
print('Dynamics kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
