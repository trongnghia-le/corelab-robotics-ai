"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different formulations) that must
pass, and named injected bugs that must be rejected. Plain checks only, so
the fixture also works under python -O.
"""
import ast
import importlib.util
import itertools
import json
import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('rl_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L20-rl.v1.py'
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
NAMES = ('q_learning_update', 'sarsa_update', 'epsilon_greedy_probs',
         'discounted_returns', 'value_iteration', 'seed_report',
         'find_reward_loophole')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name) < spoiler for name in NAMES),
        'starter functions must sit above the spoiler banner')
require(text.index('def _oracle_vi') > spoiler, 'oracle must sit below the spoiler banner')
require(text.index('_Q_CASES = ') > spoiler, 'case tables must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('rl_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter, 'unimplemented starter must report failure')
require(len(starter) == len(NAMES) and all(line.startswith('not implemented: ') for line in starter),
        'starter must collapse NotImplementedError to one line per function: ' + str(starter))


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if value is None:
        raise SystemExit('None has no sample form')
    if type(value) is bool:
        return value
    if isinstance(value, (list, tuple)):
        return [dec(v) for v in value]
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def entry(structure, names, args):
    return {'structure': structure,
            'inputs': {name: dec(value) for name, value in zip(names, args)}}


expected_samples = (
    [entry('rl.q-update@1', ('q_sa', 'r', 'q_next', 'alpha', 'gamma', 'terminated', 'truncated'), args)
     for args, _ in kit._Q_CASES]
    + [entry('rl.sarsa-update@1', ('q_sa', 'r', 'q_next', 'a_next', 'alpha', 'gamma', 'terminated', 'truncated'), args)
       for args, _ in kit._SARSA_CASES]
    + [entry('rl.epsilon-greedy@1', ('q_values', 'epsilon'), args) for args, _ in kit._EPS_CASES]
    + [entry('rl.discounted-returns@1', ('rewards', 'gamma', 'bootstrap'),
             args if len(args) == 3 else args + (0,)) for args, _ in kit._RET_CASES]
    + [entry('rl.value-iteration@1', ('next_state', 'reward', 'terminal', 'gamma', 'sweeps'), args)
       for args, _ in kit._VI_CASES]
    + [entry('rl.seed-report@1', ('seeds', 'returns'), args) for args, _ in kit._REPORT_CASES]
    + [entry('rl.reward-loophole@1', ('next_state', 'reward', 'terminal', 'start', 'horizon'), args)
       for args, _ in kit._LOOP_CASES]
    + [entry('rl.update-chain@1', ('q_table', 'transitions', 'alpha', 'gamma'), case[:4])
       for case in kit._CHAINS])
samples = json.loads((root / 'content/labs/L20-rl.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L20-rl'], 'samples must hold only L20-rl')
require(samples['kits']['L20-rl'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')


# ---- validation shared by the references ----
def real(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError


def unit(value):
    real(value, 0, 1)


def flag(value):
    if type(value) is not bool:
        raise ValueError


def seq(value, low, high, bound):
    if not isinstance(value, (list, tuple)) or not low <= len(value) <= high:
        raise ValueError
    for v in value:
        real(v, -bound, bound)


def table_check(next_state, reward, terminal):
    if not isinstance(next_state, (list, tuple)) or not 1 <= len(next_state) <= 8:
        raise ValueError
    n = len(next_state)
    if not isinstance(next_state[0], (list, tuple)) or not 1 <= len(next_state[0]) <= 4:
        raise ValueError
    m = len(next_state[0])
    if not isinstance(reward, (list, tuple)) or len(reward) != n:
        raise ValueError
    if not isinstance(terminal, (list, tuple)) or len(terminal) != n:
        raise ValueError
    for s in range(n):
        if (not isinstance(next_state[s], (list, tuple)) or len(next_state[s]) != m
                or not isinstance(reward[s], (list, tuple)) or len(reward[s]) != m):
            raise ValueError
        for a in range(m):
            t = next_state[s][a]
            if type(t) is not int or not 0 <= t < n:
                raise ValueError
            real(reward[s][a], -1000, 1000)
        flag(terminal[s])


def q_check(q_sa, r, q_next, alpha, gamma, terminated, truncated):
    real(q_sa, -1e6, 1e6)
    real(r, -1e6, 1e6)
    seq(q_next, 1, 8, 1e6)
    unit(alpha)
    unit(gamma)
    flag(terminated)
    flag(truncated)


def aidx(a_next, q_next):
    if type(a_next) is not int or not 0 <= a_next < len(q_next):
        raise ValueError


def with_checks(check, body):
    def run(*args):
        check(*args)
        return body(*args)
    return run


# ---- author reference ----
def q_body(q_sa, r, q_next, alpha, gamma, terminated, truncated=False):
    target = r if terminated else r + gamma*max(q_next)
    return (target, q_sa + alpha*(target - q_sa))


def sarsa_body(q_sa, r, q_next, a_next, alpha, gamma, terminated, truncated=False):
    target = r if terminated else r + gamma*q_next[a_next]
    return (target, q_sa + alpha*(target - q_sa))


def eps_body(q_values, epsilon):
    n, best = len(q_values), max(q_values)
    k = sum(1 for q in q_values if q == best)
    return [epsilon/n + ((1 - epsilon)/k if q == best else 0.0) for q in q_values]


def ret_body(rewards, gamma, bootstrap=0):
    out, g = [], bootstrap
    for r in reversed(rewards):
        g = r + gamma*g
        out.append(g)
    return out[::-1]


def vi_body(next_state, reward, terminal, gamma, sweeps):
    n, m = len(next_state), len(next_state[0])
    v = [0.0]*n
    for _ in range(sweeps):
        old = v
        v = [0.0 if terminal[s] else max(
            reward[s][a] + (0.0 if terminal[next_state[s][a]] else gamma*old[next_state[s][a]])
            for a in range(m)) for s in range(n)]
    return v


def report_body(seeds, returns):
    n = len(returns)
    mean = sum(returns)/n
    if n == 1:
        return (1, mean, None, None, mean, mean)
    std = math.sqrt(sum((x - mean)**2 for x in returns)/(n - 1))
    return (n, mean, std, std/math.sqrt(n), min(returns), max(returns))


_loop_cache = {}


def loop_body(next_state, reward, terminal, start, horizon):
    """Reference by exhaustive enumeration of every action sequence (memoised)."""
    key = repr((next_state, reward, terminal, start, horizon))
    if key not in _loop_cache:
        _loop_cache[key] = loop_enumerate(next_state, reward, terminal, start, horizon)
    return _loop_cache[key]


def loop_enumerate(next_state, reward, terminal, start, horizon):
    m = len(next_state[0])
    goal, farm = None, None
    for steps in range(1, horizon + 1):
        for seq_ in itertools.product(range(m), repeat=steps):
            s, total, ended = start, 0, False
            for k, a in enumerate(seq_):
                total += reward[s][a]
                s = next_state[s][a]
                if terminal[s]:
                    ended = k + 1 == steps
                    if not ended:
                        total = None
                    break
            else:
                if steps == horizon and (farm is None or total > farm):
                    farm = total
                continue
            if total is not None and ended and (goal is None or total > goal):
                goal = total
    loophole = farm is not None and farm > (0 if goal is None else goal)
    return (goal, farm, loophole)


def q_ref(q_sa, r, q_next, alpha, gamma, terminated, truncated=False):
    q_check(q_sa, r, q_next, alpha, gamma, terminated, truncated)
    return q_body(q_sa, r, q_next, alpha, gamma, terminated, truncated)


def sarsa_check(q_sa, r, q_next, a_next, alpha, gamma, terminated, truncated=False):
    q_check(q_sa, r, q_next, alpha, gamma, terminated, truncated)
    aidx(a_next, q_next)


def eps_check(q_values, epsilon):
    seq(q_values, 1, 8, 1e6)
    unit(epsilon)


def ret_check(rewards, gamma, bootstrap=0):
    seq(rewards, 1, 200, 1e6)
    unit(gamma)
    real(bootstrap, -1e6, 1e6)


def vi_check(next_state, reward, terminal, gamma, sweeps):
    table_check(next_state, reward, terminal)
    unit(gamma)
    if type(sweeps) is not int or not 1 <= sweeps <= 1000:
        raise ValueError


def report_check(seeds, returns):
    seq(seeds, 1, 100, 10**9)
    if any(type(s) is not int or s < 0 for s in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError
    seq(returns, 1, 100, 1e6)
    if len(returns) != len(seeds):
        raise ValueError


def loop_check(next_state, reward, terminal, start, horizon):
    table_check(next_state, reward, terminal)
    if type(start) is not int or not 0 <= start < len(next_state) or terminal[start]:
        raise ValueError
    if type(horizon) is not int or not 1 <= horizon <= 8:
        raise ValueError


CHECKS = {'q_learning_update': q_check, 'sarsa_update': sarsa_check,
          'epsilon_greedy_probs': eps_check, 'discounted_returns': ret_check,
          'value_iteration': vi_check, 'seed_report': report_check,
          'find_reward_loophole': loop_check}
BODIES = {'q_learning_update': q_body, 'sarsa_update': sarsa_body,
          'epsilon_greedy_probs': eps_body, 'discounted_returns': ret_body,
          'value_iteration': vi_body, 'seed_report': report_body,
          'find_reward_loophole': loop_body}
refs = {name: with_checks(CHECKS[name], BODIES[name]) for name in NAMES}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


def body_mutant(name, body):
    """Full validation of the named function, replaced body."""
    return {name: with_checks(CHECKS[name], body)}


# ---- valid alternatives ----
def q_blend(q_sa, r, q_next, alpha, gamma, terminated, truncated=False):
    q_check(q_sa, r, q_next, alpha, gamma, terminated, truncated)
    alive = 0 if terminated else 1
    target = r + alive*gamma*max(q_next)
    return [target, (1 - alpha)*q_sa + alpha*target]


def sarsa_blend(q_sa, r, q_next, a_next, alpha, gamma, terminated, truncated=False):
    sarsa_check(q_sa, r, q_next, a_next, alpha, gamma, terminated, truncated)
    alive = 0 if terminated else 1
    target = r + alive*gamma*q_next[a_next]
    return [target, (1 - alpha)*q_sa + alpha*target]


def eps_vector(q_values, epsilon):
    eps_check(q_values, epsilon)
    n = len(q_values)
    best = max(q_values)
    greedy = [1.0 if q == best else 0.0 for q in q_values]
    total = sum(greedy)
    return tuple(epsilon*(1.0/n) + (1 - epsilon)*g/total for g in greedy)


def ret_forward(rewards, gamma, bootstrap=0):
    ret_check(rewards, gamma, bootstrap)
    n = len(rewards)
    return [sum(gamma**(k - t)*rewards[k] for k in range(t, n)) + gamma**(n - t)*bootstrap
            for t in range(n)]


def ret_recursive(rewards, gamma, bootstrap=0):
    ret_check(rewards, gamma, bootstrap)
    rewards = list(rewards)

    def g(t):
        return bootstrap if t == len(rewards) else rewards[t] + gamma*g(t + 1)
    return tuple(g(t) for t in range(len(rewards)))


def vi_dict(next_state, reward, terminal, gamma, sweeps):
    vi_check(next_state, reward, terminal, gamma, sweeps)
    n, m = len(next_state), len(next_state[0])
    value = {s: 0 for s in range(n)}
    for _ in range(sweeps):
        fresh = {}
        for s in range(n):
            if terminal[s]:
                fresh[s] = 0
                continue
            best = None
            for a in range(m):
                t = next_state[s][a]
                q = reward[s][a] + (0 if terminal[t] else gamma*value[t])
                if best is None or q > best:
                    best = q
            fresh[s] = best
        value = fresh
    return tuple(value[s] for s in range(n))


def report_two_pass(seeds, returns):
    report_check(seeds, returns)
    n = len(returns)
    mean = math.fsum(returns)/n
    if n < 2:
        return [n, mean, None, None, min(returns), max(returns)]
    var = math.fsum((x - mean)*(x - mean) for x in returns)/(n - 1)
    std = var**0.5
    return [n, mean, std, math.sqrt(var/n), sorted(returns)[0], sorted(returns)[-1]]


def report_welford(seeds, returns):
    report_check(seeds, returns)
    count, mean, m2 = 0, 0.0, 0.0
    for x in returns:
        count += 1
        delta = x - mean
        mean += delta/count
        m2 += delta*(x - mean)
    if count == 1:
        return (1, mean, None, None, returns[0], returns[0])
    std = math.sqrt(m2/(count - 1))
    return (count, mean, std, std/math.sqrt(count), min(returns), max(returns))


def loop_dp(next_state, reward, terminal, start, horizon):
    loop_check(next_state, reward, terminal, start, horizon)
    n, m = len(next_state), len(next_state[0])
    from_cache = {}

    def farm(s, steps):
        if steps == 0:
            return 0
        key = ('f', s, steps)
        if key not in from_cache:
            options = [reward[s][a] + farm(next_state[s][a], steps - 1)
                       for a in range(m) if not terminal[next_state[s][a]]
                       and farm(next_state[s][a], steps - 1) is not None]
            from_cache[key] = max(options) if options else None
        return from_cache[key]

    def goal(s, steps):
        if steps == 0:
            return None
        key = ('g', s, steps)
        if key not in from_cache:
            options = []
            for a in range(m):
                t = next_state[s][a]
                if terminal[t]:
                    options.append(reward[s][a])
                else:
                    rest = goal(t, steps - 1)
                    if rest is not None:
                        options.append(reward[s][a] + rest)
            from_cache[key] = max(options) if options else None
        return from_cache[key]

    g, f = goal(start, horizon), farm(start, horizon)
    flagged = f is not None and (f > g if g is not None else f > 0)
    return [g, f, flagged]


def q_fraction(q_sa, r, q_next, alpha, gamma, terminated, truncated=False):
    q_check(q_sa, r, q_next, alpha, gamma, terminated, truncated)
    F = Fraction
    target = F(r) if terminated else F(r) + F(gamma)*max(F(v) for v in q_next)
    return (float(target), float(F(q_sa) + F(alpha)*(target - F(q_sa))))


def eps_fraction(q_values, epsilon):
    eps_check(q_values, epsilon)
    F = Fraction
    n, best = len(q_values), max(F(q) for q in q_values)
    ties = [i for i, q in enumerate(q_values) if F(q) == best]
    return [float(F(epsilon)/n + ((1 - F(epsilon))/len(ties) if i in ties else 0))
            for i in range(n)]


alternatives = [
    ('author reference with exhaustive-enumeration loophole search', {}),
    ('blend form (1-alpha)q + alpha*target, alive mask, vector probabilities, forward/recursive returns',
     {'q_learning_update': q_blend, 'sarsa_update': sarsa_blend,
      'epsilon_greedy_probs': eps_vector, 'discounted_returns': ret_forward}),
    ('dict value iteration, two-pass report, memoised DP loophole, recursive returns',
     {'value_iteration': vi_dict, 'seed_report': report_two_pass,
      'find_reward_loophole': loop_dp, 'discounted_returns': ret_recursive}),
    ('Welford report with tuple results, exact Fraction update and probabilities',
     {'seed_report': report_welford, 'q_learning_update': q_fraction,
      'epsilon_greedy_probs': eps_fraction}),
    ('mixed: list outputs everywhere, DP loophole, forward returns',
     {'find_reward_loophole': loop_dp, 'discounted_returns': ret_forward,
      'seed_report': report_two_pass, 'sarsa_update': sarsa_blend}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result))


# ---- injected bugs ----
def accepts_when(check, name, fallback):
    """Full validation except one named gap: returns a plausible value instead."""
    def run(*args):
        if check(*args):
            return fallback
        return refs[name](*args)
    return run


def is_real(v):
    return type(v) in (int, float) and math.isfinite(v)


def q_variant(rule, new=None):
    def body(q_sa, r, q_next, alpha, gamma, terminated, truncated=False):
        target = rule(q_sa, r, q_next, alpha, gamma, terminated, truncated)
        return (target, new(q_sa, target, alpha) if new else q_sa + alpha*(target - q_sa))
    return body_mutant('q_learning_update', body)


def sarsa_variant(rule):
    def body(q_sa, r, q_next, a_next, alpha, gamma, terminated, truncated=False):
        target = rule(q_sa, r, q_next, a_next, gamma, terminated, truncated)
        return (target, q_sa + alpha*(target - q_sa))
    return body_mutant('sarsa_update', body)


def q_mutates(q_sa, r, q_next, alpha, gamma, terminated, truncated=False):
    q_check(q_sa, r, q_next, alpha, gamma, terminated, truncated)
    if isinstance(q_next, list):
        q_next.sort()
    return q_body(q_sa, r, q_next, alpha, gamma, terminated, truncated)


def eps_variant(rule):
    return body_mutant('epsilon_greedy_probs', rule)


def ret_variant(rule):
    return body_mutant('discounted_returns', rule)


def vi_variant(rule):
    return body_mutant('value_iteration', rule)


def vi_inplace(next_state, reward, terminal, gamma, sweeps):
    n, m = len(next_state), len(next_state[0])
    v = [0.0]*n
    for _ in range(sweeps):
        for s in range(n):
            v[s] = 0.0 if terminal[s] else max(
                reward[s][a] + (0.0 if terminal[next_state[s][a]] else gamma*v[next_state[s][a]])
                for a in range(m))
    return v


def vi_general(next_state, reward, terminal, gamma, sweeps, *, bootstrap_terminal=False,
               drop_terminal_reward=False, force_terminal_zero=True, pick=max,
               use_gamma=True, extra=0):
    n, m = len(next_state), len(next_state[0])
    v = [0.0]*n
    for _ in range(sweeps + extra):
        old = v
        new = []
        for s in range(n):
            if terminal[s] and force_terminal_zero:
                new.append(0.0)
                continue
            options = []
            for a in range(m):
                t = next_state[s][a]
                r = 0.0 if (drop_terminal_reward and terminal[t]) else reward[s][a]
                future = old[t] if (bootstrap_terminal or not terminal[t]) else 0.0
                options.append(r + (gamma if use_gamma else 1)*future)
            new.append(pick(options))
        v = new
    return v


def vi_skip_last(next_state, reward, terminal, gamma, sweeps):
    n, m = len(next_state), len(next_state[0])
    v = [0.0]*n
    for _ in range(sweeps):
        old = v
        v = [0.0 if terminal[s] else max(
            reward[s][a] + (0.0 if terminal[next_state[s][a]] else gamma*old[next_state[s][a]])
            for a in range(max(m - 1, 1))) for s in range(n)]
    return v


def report_variant(rule):
    return body_mutant('seed_report', rule)


def pop_std(seeds, returns):
    n = len(returns)
    mean = sum(returns)/n
    std = math.sqrt(sum((x - mean)**2 for x in returns)/n)
    return (n, mean, None if n == 1 else std, None if n == 1 else std/math.sqrt(n),
            min(returns), max(returns))


def report_tweak(change):
    def body(seeds, returns):
        n, mean, std, sem, worst, best = report_body(seeds, returns)
        return change(n, mean, std, sem, worst, best, returns)
    return report_variant(body)


def loop_variant(rule):
    return body_mutant('find_reward_loophole', rule)


def loop_dp_tweak(farm_steps=0, strict=True, goal_exact=False, farm_may_end=False,
                  drop_entry_reward=False, farm_any_length=False, none_as_minus_inf=False,
                  as_int=False):
    def body(next_state, reward, terminal, start, horizon):
        n, m = len(next_state), len(next_state[0])
        h = horizon + farm_steps
        farm_best = None
        # farm: all sequences of length h (or any length up to h) avoiding terminals
        level = {start: 0}
        candidates = []
        for t in range(h):
            fresh = {}
            for s, total in level.items():
                for a in range(m):
                    nxt = next_state[s][a]
                    if terminal[nxt] and not farm_may_end:
                        continue
                    value = total + reward[s][a]
                    if nxt not in fresh or value > fresh[nxt]:
                        fresh[nxt] = value
            level = fresh
            if level:
                candidates.append(max(level.values()))
        if farm_any_length:
            farm_best = max([0] + candidates)
        elif len(candidates) == h and h > 0:
            farm_best = candidates[-1]
        # goal: first terminal entry within the horizon
        level, goal_best = {start: 0}, None
        for t in range(horizon):
            fresh = {}
            for s, total in level.items():
                for a in range(m):
                    nxt = next_state[s][a]
                    value = total + (0 if (drop_entry_reward and terminal[nxt]) else reward[s][a])
                    if terminal[nxt]:
                        if not goal_exact or t == horizon - 1:
                            if goal_best is None or value > goal_best:
                                goal_best = value
                    elif nxt not in fresh or value > fresh[nxt]:
                        fresh[nxt] = value
            level = fresh
        base = goal_best if goal_best is not None else (float('-inf') if none_as_minus_inf else 0)
        if farm_best is None:
            flagged = False
        else:
            flagged = farm_best > base if strict else farm_best >= base
        return (goal_best, farm_best, int(flagged) if as_int else flagged)
    return loop_variant(body)


def only_where(check, rule, fallback_name):
    return lambda *args: rule(*args) if check(*args) else refs[fallback_name](*args)


mutants = [
    # --- terminal vs time limit ---
    ('done flag: truncation also cuts the bootstrap (Q-learning)',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if (term or trunc) else r + g*max(qn))),
    ('done flag: truncation also cuts the bootstrap (SARSA)',
     sarsa_variant(lambda q, r, qn, an, g, term, trunc: r if (term or trunc) else r + g*qn[an])),
    ('termination ignored: always bootstraps',
     q_variant(lambda q, r, qn, a, g, term, trunc: r + g*max(qn))),
    ('flags swapped: only truncation cuts the bootstrap',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if trunc else r + g*max(qn))),
    ('terminal target is 0 instead of r',
     q_variant(lambda q, r, qn, a, g, term, trunc: 0.0 if term else r + g*max(qn))),
    ('SARSA ignores termination',
     sarsa_variant(lambda q, r, qn, an, g, term, trunc: r + g*qn[an])),
    # --- Q-learning / SARSA arithmetic ---
    ('Q-learning bootstraps from the mean of q_next',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else r + g*sum(qn)/len(qn))),
    ('Q-learning bootstraps from q_next[0]',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else r + g*qn[0])),
    ('Q-learning bootstraps from min(q_next)',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else r + g*min(qn))),
    ('Q-learning forgets gamma',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else r + max(qn))),
    ('gamma also applied to r',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else g*(r + max(qn)))),
    ('target without the reward',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else g*max(qn))),
    ('q_new = target (alpha ignored)',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else r + g*max(qn),
               lambda q, t, al: t)),
    ('q_new = q + alpha*target (forgot to subtract q)',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else r + g*max(qn),
               lambda q, t, al: q + al*t)),
    ('step size 1 - alpha',
     q_variant(lambda q, r, qn, a, g, term, trunc: r if term else r + g*max(qn),
               lambda q, t, al: q + (1 - al)*(t - q))),
    ('returns (q_new, target) in swapped order', body_mutant('q_learning_update', lambda *a: tuple(reversed(q_body(*a))))),
    ('Q-learning mutates q_next', {'q_learning_update': q_mutates}),
    ('SARSA uses the greedy value (Q-learning)',
     sarsa_variant(lambda q, r, qn, an, g, term, trunc: r if term else r + g*max(qn))),
    ('SARSA index shifted by one',
     sarsa_variant(lambda q, r, qn, an, g, term, trunc: r if term else r + g*qn[(an + 1) % len(qn)])),
    ('SARSA uses the mean value (uniform expected)',
     sarsa_variant(lambda q, r, qn, an, g, term, trunc: r if term else r + g*sum(qn)/len(qn))),
    # --- epsilon greedy ---
    ('epsilon spread over the other actions only',
     eps_variant(lambda qv, e: [(1 - e) if q == max(qv) else e/max(len(qv) - 1, 1) if len(qv) > 1 else 1.0
                                for q in qv])),
    ('epsilon/n on the non-greedy only (probabilities sum below 1)',
     eps_variant(lambda qv, e: [(1 - e) if q == max(qv) else e/len(qv) for q in qv])),
    ('ties go to the first maximiser only',
     eps_variant(lambda qv, e: [e/len(qv) + ((1 - e) if i == qv.index(max(qv)) else 0.0)
                                for i in range(len(qv))])),
    ('every tied action gets the full greedy mass',
     eps_variant(lambda qv, e: [e/len(qv) + ((1 - e) if q == max(qv) else 0.0) for q in qv])),
    ('epsilon and 1 - epsilon swapped',
     eps_variant(lambda qv, e: eps_body(qv, 1 - e))),
    ('greedy action is the minimum',
     eps_variant(lambda qv, e: eps_body([-q for q in qv], e))),
    ('greedy action chosen by absolute value',
     eps_variant(lambda qv, e: eps_body([abs(q) for q in qv], e))),
    ('near-equal values treated as ties',
     eps_variant(lambda qv, e: (lambda b: [e/len(qv) + ((1 - e)/sum(1 for v in qv if abs(v - b) < 1e-6)
                                                       if abs(q - b) < 1e-6 else 0.0) for q in qv])(max(qv)))),
    ('tie detection skips the last action',
     eps_variant(lambda qv, e: (lambda ties: [e/len(qv) + ((1 - e)/len(ties) if i in ties else 0.0)
                                              for i in range(len(qv))])(
         [i for i in range(len(qv) - 1) if qv[i] == max(qv)] or [len(qv) - 1]))),
    ('value iteration never looks at the last action',
     vi_variant(lambda n, r, t, g, sw: vi_body(n, [row[:-1] for row in r], t, g, sw)
                if False else vi_skip_last(n, r, t, g, sw))),
    ('standard deviation via E[x^2] - mean^2',
     report_tweak(lambda n, mean, std, sem, w, b, rs: (
         lambda sd: (n, mean, sd, None if sd is None else sd/math.sqrt(n), w, b))(
         None if n == 1 else math.sqrt(max(0.0, (sum(x*x for x in rs)/n - mean*mean)*n/(n - 1)))))),
    # --- returns ---
    ('returns listed latest first',
     ret_variant(lambda rw, g, b=0: ret_body(rw, g, b)[::-1])),
    ('bootstrap added undiscounted',
     ret_variant(lambda rw, g, b=0: [x + (1 - g**(len(rw) - t))*b
                                     for t, x in enumerate(ret_body(rw, g, b))])),
    ('discount exponent starts at 1',
     ret_variant(lambda rw, g, b=0: [g*x for x in ret_body(rw, g, b)])),
    ('bootstrap ignored',
     ret_variant(lambda rw, g, b=0: ret_body(rw, g, 0))),
    ('prefix sums instead of returns-to-go',
     ret_variant(lambda rw, g, b=0: [sum(g**k*rw[k] for k in range(t + 1)) for t in range(len(rw))])),
    ('undiscounted return-to-go (gamma ignored)',
     ret_variant(lambda rw, g, b=0: ret_body(rw, 1, b))),
    ('bootstrap not scaled by gamma at the last step',
     ret_variant(lambda rw, g, b=0: [ret_body(rw, g, 0)[t] + b*g**(len(rw) - t - 1) for t in range(len(rw))])),
    # --- value iteration ---
    ('in-place (Gauss-Seidel) sweeps',
     vi_variant(vi_inplace)),
    ('terminal states bootstrapped through their own row',
     vi_variant(lambda *a: vi_general(*a, force_terminal_zero=False))),
    ('reward into the terminal state dropped',
     vi_variant(lambda *a: vi_general(*a, drop_terminal_reward=True))),
    ('one extra sweep',
     vi_variant(lambda *a: vi_general(*a, extra=1))),
    ('min instead of max',
     vi_variant(lambda *a: vi_general(*a, pick=min))),
    ('gamma forgotten',
     vi_variant(lambda *a: vi_general(*a, use_gamma=False))),
    ('runs 1000 sweeps whatever sweeps says',
     vi_variant(lambda n, r, t, g, sw: vi_body(n, r, t, g, 1000))),
    # --- seed report ---
    ('population standard deviation (divides by n)',
     report_variant(pop_std)),
    ('standard error equals the standard deviation',
     report_tweak(lambda n, mean, std, sem, w, b, rs: (n, mean, std, std, w, b))),
    ('standard error divides by n',
     report_tweak(lambda n, mean, std, sem, w, b, rs: (n, mean, std, None if std is None else std/n, w, b))),
    ('best seed reported as the mean',
     report_tweak(lambda n, mean, std, sem, w, b, rs: (n, b, std, sem, w, b))),
    ('single seed gets std 0 instead of None',
     report_tweak(lambda n, mean, std, sem, w, b, rs: (n, mean, 0.0 if std is None else std,
                                                       0.0 if sem is None else sem, w, b))),
    ('worst and best swapped',
     report_tweak(lambda n, mean, std, sem, w, b, rs: (n, mean, std, sem, b, w))),
    ('median reported as the mean',
     report_tweak(lambda n, mean, std, sem, w, b, rs: (n, sorted(rs)[n//2], std, sem, w, b))),
    ('report sorts the returns in place',
     {'seed_report': lambda seeds, returns: (report_check(seeds, returns), returns.sort(),
                                             report_body(seeds, returns))[2]
      if isinstance(returns, list) else refs['seed_report'](seeds, returns)}),
    # --- loophole ---
    ('farm path one step too short',
     loop_dp_tweak(farm_steps=-1)),
    ('loophole when farm ties the goal (>=)',
     loop_dp_tweak(strict=False)),
    ('goal only counted when reached at the last step',
     loop_dp_tweak(goal_exact=True)),
    ('farm path allowed to end in a terminal state',
     loop_dp_tweak(farm_may_end=True)),
    ('reward of the entering transition dropped',
     loop_dp_tweak(drop_entry_reward=True)),
    ('farm allowed to stop early (any length)',
     loop_dp_tweak(farm_any_length=True)),
    ('unreachable goal treated as minus infinity',
     loop_dp_tweak(none_as_minus_inf=True)),
    ('loophole returned as an int, not a bool',
     loop_dp_tweak(as_int=True)),
    # --- validation gaps ---
    ('terminated=1 (int) accepted as a flag',
     {'q_learning_update': accepts_when(lambda *a: type(a[5]) is int, 'q_learning_update', (0.0, 0.0))}),
    ('truncated flag string accepted',
     {'q_learning_update': accepts_when(lambda *a: len(a) > 6 and isinstance(a[6], str),
                                        'q_learning_update', (0.0, 0.0))}),
    ('alpha above 1 accepted',
     {'q_learning_update': accepts_when(lambda *a: is_real(a[3]) and a[3] > 1, 'q_learning_update', (0.0, 0.0))}),
    ('negative gamma accepted',
     {'sarsa_update': accepts_when(lambda *a: is_real(a[5]) and a[5] < 0, 'sarsa_update', (0.0, 0.0))}),
    ('negative a_next wraps around',
     {'sarsa_update': accepts_when(lambda *a: type(a[3]) is int and a[3] < 0, 'sarsa_update', (0.0, 0.0))}),
    ('a_next out of range accepted when terminated',
     {'sarsa_update': lambda q, r, qn, an, al, g, term, trunc=False: refs['sarsa_update'](
         q, r, qn, 0 if (term is True and type(an) is int) else an, al, g, term, trunc)}),
    ('empty q_next accepted',
     {'q_learning_update': accepts_when(lambda *a: isinstance(a[2], (list, tuple)) and not a[2],
                                        'q_learning_update', (0.0, 0.0))}),
    ('q_next not validated when terminated',
     {'q_learning_update': lambda q, r, qn, al, g, term, trunc=False:
      (r, q + al*(r - q)) if term is True and is_real(q) and is_real(r) and is_real(al) and 0 <= al <= 1
      else refs['q_learning_update'](q, r, qn, al, g, term, trunc)}),
    ('bool in q_values accepted',
     {'epsilon_greedy_probs': accepts_when(lambda *a: isinstance(a[0], list) and any(type(v) is bool for v in a[0]),
                                           'epsilon_greedy_probs', [1.0])}),
    ('epsilon above 1 accepted',
     {'epsilon_greedy_probs': accepts_when(lambda *a: is_real(a[1]) and a[1] > 1, 'epsilon_greedy_probs', [1.0])}),
    ('more than 8 actions rejected (over-strict)',
     {'epsilon_greedy_probs': lambda qv, e: refs['epsilon_greedy_probs'](qv, e)
      if not (isinstance(qv, list) and len(qv) == 8) else (_ for _ in ()).throw(ValueError())}),
    ('|q| above 100 rejected (over-strict)',
     {'q_learning_update': lambda q, *a: (_ for _ in ()).throw(ValueError())
      if is_real(q) and abs(q) > 100 else refs['q_learning_update'](q, *a)}),
    ('empty rewards accepted',
     {'discounted_returns': accepts_when(lambda *a: isinstance(a[0], (list, tuple)) and not a[0],
                                         'discounted_returns', [])}),
    ('bootstrap bound unchecked',
     {'discounted_returns': accepts_when(lambda *a: len(a) > 2 and is_real(a[2]) and abs(a[2]) > 1e6,
                                         'discounted_returns', [0.0])}),
    ('tuple rewards rejected (over-strict)',
     {'discounted_returns': lambda rw, *a: refs['discounted_returns'](rw, *a)
      if isinstance(rw, list) else (_ for _ in ()).throw(ValueError())}),
    ('ragged next_state accepted',
     {'value_iteration': accepts_when(lambda *a: isinstance(a[0], list) and len(set(map(len, a[0]))) > 1
                                      if all(isinstance(r, (list, tuple)) for r in a[0]) else False,
                                      'value_iteration', [0.0])}),
    ('successor out of range wraps around',
     {'value_iteration': accepts_when(lambda *a: isinstance(a[0], list) and any(
         isinstance(r, list) and any(type(t) is int and t < 0 for t in r) for r in a[0]),
         'value_iteration', [0.0])}),
    ('terminal entries 0/1 accepted',
     {'value_iteration': accepts_when(lambda *a: isinstance(a[2], list) and any(type(t) is int for t in a[2]),
                                      'value_iteration', [0.0])}),
    ('reward table shape mismatch accepted',
     {'value_iteration': accepts_when(lambda *a: isinstance(a[1], list) and isinstance(a[0], list)
                                      and len(a[1]) != len(a[0]), 'value_iteration', [0.0])}),
    ('float sweeps accepted',
     {'value_iteration': lambda n, r, t, g, sw: refs['value_iteration'](n, r, t, g, int(sw))
      if type(sw) is float and math.isfinite(sw) and sw >= 1 else refs['value_iteration'](n, r, t, g, sw)}),
    ('sweeps above 1000 rejected (over-strict)',
     {'value_iteration': lambda n, r, t, g, sw: refs['value_iteration'](n, r, t, g, sw)
      if sw != 1000 else (_ for _ in ()).throw(ValueError())}),
    ('duplicate seeds accepted',
     {'seed_report': accepts_when(lambda s, r: isinstance(s, list) and len(set(s)) < len(s)
                                  and all(type(v) is int for v in s) and len(s) == len(r) if isinstance(r, list) else False,
                                  'seed_report', (1, 0.0, None, None, 0.0, 0.0))}),
    ('seeds and returns of different length accepted',
     {'seed_report': accepts_when(lambda s, r: isinstance(s, list) and isinstance(r, list)
                                  and len(s) != len(r) and len(s) > 0 and len(r) > 0,
                                  'seed_report', (1, 0.0, None, None, 0.0, 0.0))}),
    ('float seed accepted',
     {'seed_report': accepts_when(lambda s, r: isinstance(s, list) and any(type(v) is float for v in s),
                                  'seed_report', (1, 0.0, None, None, 0.0, 0.0))}),
    ('NaN return accepted',
     {'seed_report': accepts_when(lambda s, r: isinstance(r, list) and any(type(v) is float and v != v for v in r),
                                  'seed_report', (1, 0.0, None, None, 0.0, 0.0))}),
    ('empty seed list accepted',
     {'seed_report': accepts_when(lambda s, r: isinstance(s, list) and not s,
                                  'seed_report', (1, 0.0, None, None, 0.0, 0.0))}),
    ('terminal start state accepted',
     {'find_reward_loophole': accepts_when(
         lambda n, r, t, s, h: isinstance(t, list) and type(s) is int and 0 <= s < len(t) and t[s] is True,
         'find_reward_loophole', (None, None, False))}),
    ('horizon above 8 accepted',
     {'find_reward_loophole': accepts_when(lambda *a: type(a[4]) is int and a[4] > 8,
                                           'find_reward_loophole', (None, None, False))}),
    ('bool start accepted',
     {'find_reward_loophole': accepts_when(lambda *a: type(a[3]) is bool,
                                           'find_reward_loophole', (None, None, False))}),
    ('loophole mutates the reward table',
     {'find_reward_loophole': lambda n, r, t, s, h: (r.reverse() if isinstance(r, list) else None,
                                                     refs['find_reward_loophole'](n, r, t, s, h))[1]}),
    ('rejects int rewards (over-strict)',
     {'value_iteration': lambda n, r, t, g, sw: (_ for _ in ()).throw(ValueError())
      if any(type(x) is int for row in r for x in row) else refs['value_iteration'](n, r, t, g, sw)}),
]
for label, over in mutants:
    require(run_with(over), 'false accept: ' + label)
print('RL kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
