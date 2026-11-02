"""CoreLab RL experiment core lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the seven functions below, then run your edited file locally:
  Windows: py -3 L20-rl.v1.py
  macOS/Linux: python3 L20-rl.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared toy setting (numerical practice, not a simulator and not training):
tabular value tables, deterministic tiny environments and lists of finished
results. Nothing here samples an environment, draws random numbers or trains
anything; every answer is a closed-form or exact-enumeration number.

Common conventions. All numbers are finite int/float, never bool. Bounds are
inclusive. Invalid inputs (wrong type or shape, bool where a number is
expected, NaN, infinity, out of bounds, ragged tables) raise ValueError.
Inputs are never mutated. A "list" input may be a list or a tuple. Returned
sequences are lists or tuples of finite int/float (non-bool). Self-check
tolerance is 1e-9 times max(1, |value|); a returned bool must be a real bool.
The flags terminated and truncated must be real bool values (not 0/1).

  q_learning_update(q_sa, r, q_next, alpha, gamma, terminated, truncated=False)
      -> (target, q_new)
      One off-policy tabular step. q_sa is the current Q(s, a); r the reward
      received; q_next the list Q(s', .) over the actions of the next state s'.
      target = r + gamma*max(q_next) if the episode did NOT terminate in this
      transition, otherwise target = r.  q_new = q_sa + alpha*(target - q_sa).
      TERMINATED means the task itself ended (goal, fall, crash): there is no
      future, so no bootstrap. TRUNCATED means only the time limit or a
      recording cut stopped the episode while the task would go on: the next
      state still has a value, so the target STILL bootstraps. A replay
      buffer's single "done" flag mixes the two; only terminated cuts the
      bootstrap. If both flags are true the transition terminated (target =
      r). q_next is validated even when it is not used.
      Bounds: |q_sa| <= 1e6, |r| <= 1e6, 0 <= alpha <= 1, 0 <= gamma <= 1,
      q_next has 1 to 8 values with |value| <= 1e6.
  sarsa_update(q_sa, r, q_next, a_next, alpha, gamma, terminated, truncated=False)
      -> (target, q_new)
      On-policy step: the target uses the action a_next that was actually
      chosen in s' (an int index into q_next, 0 <= a_next < len(q_next), not
      bool): target = r + gamma*q_next[a_next] unless terminated, then r. The
      terminated/truncated rules and q_new are exactly as above. a_next is
      validated even when the step terminated.
  epsilon_greedy_probs(q_values, epsilon) -> list of probabilities
      With probability epsilon the behaviour picks uniformly among ALL n
      actions (including the greedy ones); otherwise it picks greedily. If
      several actions tie EXACTLY (==) for the maximum, the greedy mass 1 -
      epsilon is split equally among them. So p[a] = epsilon/n + (1 -
      epsilon)/k for each of the k maximising actions and epsilon/n for the
      others. The probabilities sum to 1 (tolerance 1e-9).
      Bounds: 1 to 8 values, |value| <= 1e6, 0 <= epsilon <= 1.
  discounted_returns(rewards, gamma, bootstrap=0) -> list [G_0, ..., G_{T-1}]
      rewards = [r_0, ..., r_{T-1}] of one episode (r_t is the reward after
      the action at step t). G_T = bootstrap and G_t = r_t + gamma*G_{t+1}, so
      G_0 = sum_t gamma^t r_t + gamma^T bootstrap. bootstrap is 0 for a
      terminated episode and the estimated value V(s_T) of the cut-off state
      for a time-limit truncation. gamma = 1 gives the undiscounted episode
      return in G_0. Entry t is the return FROM step t (not the reward).
      Bounds: 1 to 200 rewards with |r| <= 1e6, 0 <= gamma <= 1,
      |bootstrap| <= 1e6.
  value_iteration(next_state, reward, terminal, gamma, sweeps) -> list V
      Exact reference on a declared deterministic tiny MDP with n states
      (1 to 8) and m actions (1 to 4). next_state[s][a] is the int successor
      (0 <= . < n, not bool); reward[s][a] the finite reward (|.| <= 1000)
      received on that transition; terminal[s] a bool. Both tables are
      rectangular n x m. A terminal state ends the episode: its value is 0
      and its own row is never used, but the tables must still be valid. A
      reward on a transition INTO a terminal state is received and nothing
      bootstraps after it. Start from V = [0]*n and apply exactly `sweeps`
      SYNCHRONOUS sweeps, each computed from the previous sweep's table only
      (not updated in place):
          V_new[s] = max over a of reward[s][a] + gamma*V_old[next_state[s][a]]
      (the gamma*V term is 0 when the successor is terminal; V_new[s] = 0 for a
      terminal s). Return the list of n values after the last sweep.
      Bounds: 0 <= gamma <= 1; sweeps is an int, 1 <= sweeps <= 1000.
  seed_report(seeds, returns) -> (n, mean, std, sem, worst, best)
      The protocol reports EVERY declared seed. seeds are n distinct ints
      (0 <= seed <= 1e9, not bool; a repeated seed is a duplicated run and is
      invalid) and returns[i] is the raw final return of the run with seeds[i]
      (1 <= n <= 100, |value| <= 1e6, same length). Report n, mean, the SAMPLE
      standard deviation std = sqrt(sum (x - mean)^2 / (n - 1)), the standard
      error of the mean sem = std/sqrt(n), and the worst and best raw
      returns. For n = 1 std and sem do not exist: return None for both (a
      report, not an error). The seeds are only identity labels; the order of
      the lists does not change the numbers. Reporting only the best seed is
      a named mistake (it is the maximum of n draws, not a typical result);
      so is selecting the seeds after seeing the results.
  find_reward_loophole(next_state, reward, terminal, start, horizon)
      -> (best_goal, best_farm, loophole)
      Same table format as value_iteration (undiscounted here). start is an
      int state that is NOT terminal; horizon is an int, 1 <= horizon <= 8,
      the time limit in steps. An episode ends on entering a terminal state
      (that transition's reward counts) or after `horizon` steps.
      best_goal = the highest total reward over all action sequences that
      enter a terminal state within the horizon (the sum includes the entering
      reward); None if no sequence does.
      best_farm = the highest total reward over all action sequences of
      exactly `horizon` steps that NEVER enter a terminal state; None if
      none exists.
      loophole = True exactly when farming strictly beats finishing: best_farm
      is not None and best_farm > best_goal (when best_goal is None, compare
      with 0: positive reward available with no way to finish). It must be a
      real bool. A farmable reward can be a loophole at a long horizon and not
      at a short one.

Pause before coding - write your predictions down first:
  1. A transition is cut by the 200-step recording limit. Which flag is set,
     and does the target bootstrap? What if the robot actually reached the
     goal in that last step?
  2. Q-learning and SARSA share q_sa, r and q_next. When do their targets
     agree, and which one is larger when the behaviour picked a bad action?
  3. With ties in the greedy action, what probability does each tied action
     get, and why does epsilon/n appear on the greedy action too?
  4. Why does G_0 change when you add a bootstrap value, and by how much for
     gamma = 0.5 and T = 3?
  5. After one synchronous sweep from V = 0, what is V of a state whose best
     action pays 10 into the goal? How many sweeps until a 3-step path's
     value is exact?
  6. The goal pays +10 once; a pad you cannot leave pays +2 per step. Who
     wins at a horizon of 4? Of 10? Where is the tie, and what if the pad
     could be left again before finishing?
  7. Five seeds give 30, 5, 8, 7, 10. What do mean, sem and best say, and
     which one would you quote to a colleague?
Self-check cases are fixed author fixtures, per-case and exact; they are
practice only, not a performance claim. Failure messages name the case and
the kind of mismatch, never the expected numbers. "your code raised X" means
your function raised on a VALID input.
This does not implement an environment, a simulator, deep or continuous RL,
PPO or SAC, policy-gradient or function-approximation methods, stochastic
transitions, a significance test or confidence interval, or any human review
of an experiment protocol.
Reflection: why does passing this tabular toy NOT show that an RL experiment
is sound? (Think about the simulator you would train in, unequal seeds or
hyper-parameter budgets across methods, reward you did not intend, evaluation
episodes that overlap training, too few seeds for any uncertainty statement,
and a protocol that was written after seeing the results.)

Background link only: Sutton and Barto, Reinforcement Learning: An
Introduction (2nd ed.), http://incompleteideas.net/book/the-book-2nd.html, for
the update rules. No text or figures from it are redistributed here.
"""
import math


def q_learning_update(q_sa, r, q_next, alpha, gamma, terminated, truncated=False):
    raise NotImplementedError("Bootstrap with max(q_next) unless the task terminated; a time-limit cut still bootstraps")


def sarsa_update(q_sa, r, q_next, a_next, alpha, gamma, terminated, truncated=False):
    raise NotImplementedError("Use the action that was actually taken in the next state")


def epsilon_greedy_probs(q_values, epsilon):
    raise NotImplementedError("epsilon/n on every action plus the greedy mass shared among exact ties")


def discounted_returns(rewards, gamma, bootstrap=0):
    raise NotImplementedError("Work backwards from G_T = bootstrap")


def value_iteration(next_state, reward, terminal, gamma, sweeps):
    raise NotImplementedError("Synchronous sweeps from zeros; terminal states stay 0 and never bootstrap")


def seed_report(seeds, returns):
    raise NotImplementedError("Sample standard deviation divides by n - 1; report all seeds")


def find_reward_loophole(next_state, reward, terminal, start, horizon):
    raise NotImplementedError("Compare the best goal-reaching return with the best never-finishing return")


# ---- SPOILER BELOW: the _oracle_* functions are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _oracle_target(r, nxt, gamma, terminated):
    return r if terminated else r + gamma*nxt


def _oracle_probs(q_values, epsilon):
    n = len(q_values)
    best = max(q_values)
    ties = [i for i, q in enumerate(q_values) if q == best]
    return [epsilon/n + ((1 - epsilon)/len(ties) if i in ties else 0.0)
            for i in range(n)]


def _oracle_returns(rewards, gamma, bootstrap):
    out, g = [], bootstrap
    for r in reversed(rewards):
        g = r + gamma*g
        out.append(g)
    return out[::-1]


def _oracle_vi(next_state, reward, terminal, gamma, sweeps):
    n, m = len(next_state), len(next_state[0])
    v = [0.0]*n
    for _ in range(sweeps):
        old = v
        v = [0.0 if terminal[s] else max(
            reward[s][a] + (0.0 if terminal[next_state[s][a]]
                            else gamma*old[next_state[s][a]])
            for a in range(m)) for s in range(n)]
    return v


def _oracle_report(returns):
    n = len(returns)
    mean = sum(returns)/n
    if n == 1:
        return (1, mean, None, None, mean, mean)
    std = math.sqrt(sum((x - mean)**2 for x in returns)/(n - 1))
    return (n, mean, std, std/math.sqrt(n), min(returns), max(returns))


def _oracle_loophole(next_state, reward, terminal, start, horizon):
    n, m = len(next_state), len(next_state[0])
    # farm[t][s]: best total over t more steps that never enter a terminal state
    farm = [0.0]*n
    for _ in range(horizon):
        new = []
        for s in range(n):
            options = [reward[s][a] + farm[next_state[s][a]]
                       for a in range(m)
                       if not terminal[next_state[s][a]]
                       and farm[next_state[s][a]] is not None]
            new.append(max(options) if options else None)
        farm = new
    # goal[s]: best total from s that enters a terminal state within t steps
    goal = [None]*n
    for _ in range(horizon):
        new = []
        for s in range(n):
            options = []
            for a in range(m):
                t = next_state[s][a]
                if terminal[t]:
                    options.append(reward[s][a])
                elif goal[t] is not None:
                    options.append(reward[s][a] + goal[t])
            new.append(max(options) if options else None)
        goal = new
    best_goal, best_farm = goal[start], farm[start]
    loophole = best_farm is not None and best_farm > (
        0 if best_goal is None else best_goal)
    return best_goal, best_farm, loophole


# q_learning_update(q_sa, r, q_next, alpha, gamma, terminated[, truncated])
# -> (target, q_new): hand-derived answers.
_Q_CASES = [
    ((2.0, 1.0, [3.0, 5.0], 0.5, 0.5, False, False), (3.5, 2.75)),
    ((2.0, 1.0, [3.0, 5.0], 0.5, 0.5, True, False), (1.0, 1.5)),
    ((2.0, 1.0, [3.0, 5.0], 0.5, 0.5, False, True), (3.5, 2.75)),
    ((2.0, 1.0, [3.0, 5.0], 0.5, 0.5, True, True), (1.0, 1.5)),
    ((-1.0, -2.0, [-4.0, -1.0, -3.0], 0.25, 0.9, False, False), (-2.9, -1.475)),
    ((1, 3, [100, 200], 0.5, 0, False, False), (3, 2.0)),
]
# sarsa_update(q_sa, r, q_next, a_next, alpha, gamma, terminated[, truncated])
_SARSA_CASES = [
    ((2.0, 1.0, [3.0, 5.0], 0, 0.5, 0.5, False, False), (2.5, 2.25)),
    ((2.0, 1.0, [3.0, 5.0], 1, 0.5, 0.5, False, False), (3.5, 2.75)),
    ((2.0, 1.0, [3.0, 5.0], 0, 0.5, 0.5, True, False), (1.0, 1.5)),
    ((2.0, 1.0, [3.0, 5.0], 0, 0.5, 0.5, False, True), (2.5, 2.25)),
    ((-1.0, -2.0, [-4.0, -1.0, -3.0], 2, 0.25, 0.9, False, False), (-4.7, -1.925)),
    ((1, 3, [100, 200], 1, 0.5, 0, False, False), (3, 2.0)),
]
# epsilon_greedy_probs(q_values, epsilon) -> probabilities
_EPS_CASES = [
    (([1.0, 3.0, 2.0], 0.3), [0.1, 0.8, 0.1]),
    (([1.0, 3.0, 3.0, 0.0], 0.2), [0.05, 0.45, 0.45, 0.05]),
    (([2.0], 0.5), [1.0]),
    (([0.0, 0.0], 1.0), [0.5, 0.5]),
    (([-1.0, -3.0, -2.0], 0.3), [0.8, 0.1, 0.1]),
    (([0.0, 2.0, 2.0], 0.3), [0.1, 0.45, 0.45]),
    (([2.0, 2.0000001, 1.0], 0.2), [0.2/3, 0.2/3 + 0.8, 0.2/3]),
    (((1, 2), 0.0), [0.0, 1.0]),
]
# discounted_returns(rewards, gamma[, bootstrap]) -> [G_0, ..., G_{T-1}]
_RET_CASES = [
    (([1.0, 2.0, 3.0], 0.5), [2.75, 3.5, 3.0]),
    (([1.0, 2.0, 3.0], 0.5, 8.0), [3.75, 5.5, 7.0]),
    (([1, -1, 2], 1), [2, 1, 2]),
    (([5.0, 7.0, 9.0], 0.0, 100.0), [5.0, 7.0, 9.0]),
    (((1, 1, 1), 1, 10), [13, 12, 11]),
]
# value_iteration(next_state, reward, terminal, gamma, sweeps) -> V
_C1 = ([[1, 0], [2, 0], [2, 2]], [[-1, -1], [10, -1], [0, 0]], [False, False, True])
_C2 = ([[2, 0], [0, 1], [2, 2]], [[5, 0], [1, 0], [0, 0]], [False, False, True])
_C3 = ([[1, 0], [2, 0], [3, 1], [3, 3]],
       [[-1, -1], [-1, -1], [20, -1], [0, 0]], [False, False, False, True])
_C4 = ([[0]], [[1.0]], [False])
_C6 = ([[0, 0, 0, 1], [1, 1, 1, 1]], [[1, 2, 3, 10], [0, 0, 0, 0]], [False, True])
_C5 = ([[0, 0], [0, 2], [1, 2]], [[99, 99], [4, -1], [-1, -1]], [True, False, False])
_VI_CASES = [
    ((*_C1, 0.5, 1), [-1.0, 10.0, 0.0]),
    ((*_C2, 0.5, 2), [5.0, 3.5, 0.0]),
    ((*_C3, 1.0, 2), [-2.0, 19.0, 20.0, 0.0]),
    ((*_C3, 1.0, 5), [18.0, 19.0, 20.0, 0.0]),
    ((*_C4, 0.5, 3), [1.75]),
    ((*_C6, 0.5, 3), [10.0, 0.0]),
    ((*_C5, 0.9, 1), [0.0, 4.0, -1.0]),
    ((*_C5, 0.9, 3), [0.0, 4.0, 2.6]),
]
# seed_report(seeds, returns) -> (n, mean, std, sem, worst, best)
_REPORT_CASES = [
    (([0, 1, 2, 3, 4], [8.0, 10.0, 12.0, 14.0, 6.0]),
     (5, 10.0, math.sqrt(10), math.sqrt(2), 6.0, 14.0)),
    (([7], [3.5]), (1, 3.5, None, None, 3.5, 3.5)),
    (([0, 1, 2, 3], [-10.0, -6.0, -8.0, -4.0]),
     (4, -7.0, math.sqrt(20/3), math.sqrt(20/3)/2, -10.0, -4.0)),
    (([4, 5, 6, 7], [100.0, 0.0, 0.0, 0.0]), (4, 25.0, 50.0, 25.0, 0.0, 100.0)),
    (([5, 6], [1, 3]), (2, 2.0, math.sqrt(2), 1.0, 1, 3)),
    (([1, 2, 3, 4], [999999.999, 1000000.0, 999999.998, 999999.997]),
     (4, 999999.9985, 0.0012909944499381381, 0.0006454972249690691, 999999.997, 1000000.0)),
]
# find_reward_loophole(next_state, reward, terminal, start, horizon)
# _LA: from state 0 take the goal (+10, ends) or step onto a pad (state 1) that
# you cannot leave and that pays +2 per step (action 0) or 0 (action 1).
_LA = ([[2, 1], [1, 1], [2, 2]], [[10, 0], [2, 0], [0, 0]], [False, False, True])
_LB = ([[0], [1]], [[1.0], [0.0]], [False, True])
_LC = ([[0], [1]], [[-1.0], [0.0]], [False, True])
_LE = ([[1, 1], [1, 1]], [[3, 5], [0, 0]], [False, True])
_LF = ([[1, 3], [2, 0], [2, 2], [3, 3]],
       [[0, -5], [6, 1], [0, 0], [0, 0]], [False, False, True, True])
# _LG: a +2 pad you can leave again, so farming first and finishing later pays.
_LG = ([[1, 0], [2, 1], [2, 2]], [[-1, 0], [10, 2], [0, 0]], [False, False, True])
_LOOP_CASES = [
    ((*_LA, 0, 1), (10, 0, False)),
    ((*_LA, 0, 6), (10, 10, False)),
    ((*_LA, 0, 7), (10, 12, True)),
    ((*_LA, 1, 3), (None, 6, True)),
    ((*_LB, 0, 5), (None, 5.0, True)),
    ((*_LC, 0, 5), (None, -5.0, False)),
    ((*_LE, 0, 3), (5, None, False)),
    ((*_LF, 0, 4), (7, 2, False)),
    ((*_LG, 0, 6), (17, 9, False)),
]
# One Q table updated over a short episode, in order (the third transition is a
# time-limit cut that still bootstraps, the last one ends the task).
# (q table as rows, transitions (s, a, r, s_next, terminated, truncated),
# alpha, gamma, expected final table); every update is judged on its own.
_CHAINS = [
    ([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
     [(0, 1, 1.0, 1, False, False), (1, 0, 2.0, 2, False, False),
      (2, 1, 4.0, 1, False, True), (2, 1, 4.0, 2, True, False)],
     0.5, 0.5, [[0.0, 0.5], [1.0, 0.0], [0.0, 3.125]]),
]


def self_check():
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []

    def run(label, function, args, compare):
        name = "q_learning_update" if function.__name__ == "chain" else function.__name__
        try:
            compare(function(*args))
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except NotImplementedError:
            if "not implemented: " + name not in failures:
                failures.append("not implemented: " + name)
        except Exception as error:
            failures.append(label + ": your code raised " + type(error).__name__
                            + " on a valid input")

    def close(got, want, name, tolerance=1e-9):
        if abs(got - want) > tolerance*max(1.0, abs(want)):
            raise _Mismatch(name + " is wrong (relative tolerance " + repr(tolerance) + ")")

    def pair(got, want, what):
        if not _vector(got, 2):
            raise _Mismatch("output must be a length-2 list/tuple " + what
                            + " of finite int/float")
        close(got[0], want[0], "target")
        close(got[1], want[1], "q_new")

    for i, (args, want) in enumerate(_Q_CASES):
        copy = [list(a) if isinstance(a, list) else a for a in args]
        def compare(got, want=want, copy=copy, args=args):
            pair(got, want, "(target, q_new)")
            if any(isinstance(a, list) and a != c for a, c in zip(args, copy)):
                raise _Mismatch("input q_next was mutated")
        run("q_learning_update " + str(i), q_learning_update, copy, compare)
    for i, (args, want) in enumerate(_SARSA_CASES):
        copy = [list(a) if isinstance(a, list) else a for a in args]
        def compare(got, want=want, copy=copy, args=args):
            pair(got, want, "(target, q_new)")
            if any(isinstance(a, list) and a != c for a, c in zip(args, copy)):
                raise _Mismatch("input q_next was mutated")
        run("sarsa_update " + str(i), sarsa_update, copy, compare)

    for i, (args, want) in enumerate(_EPS_CASES):
        original = list(args[0])
        probe = type(args[0])(args[0])
        def compare(got, want=want, original=original, probe=probe):
            if (not isinstance(got, (list, tuple)) or len(got) != len(want)
                    or not all(_real(p) for p in got)):
                raise _Mismatch("output must be a list/tuple with one finite probability per action")
            for k, (p, w) in enumerate(zip(got, want)):
                close(p, w, "probability of action " + str(k), 1e-9)
            if abs(sum(got) - 1.0) > 1e-9:
                raise _Mismatch("probabilities do not sum to 1")
            if list(probe) != original:
                raise _Mismatch("input q_values was mutated")
        run("epsilon_greedy_probs " + str(i), epsilon_greedy_probs, (probe, args[1]), compare)

    for i, (args, want) in enumerate(_RET_CASES):
        original = list(args[0])
        probe = type(args[0])(args[0])
        def compare(got, want=want, original=original, probe=probe):
            if (not isinstance(got, (list, tuple)) or len(got) != len(want)
                    or not all(_real(g) for g in got)):
                raise _Mismatch("output must be a list/tuple with one return G_t per step")
            for k, (g, w) in enumerate(zip(got, want)):
                close(g, w, "G_" + str(k))
            if list(probe) != original:
                raise _Mismatch("input rewards was mutated")
        run("discounted_returns " + str(i), discounted_returns, (probe,) + args[1:], compare)

    def tables(args):
        return [[list(row) for row in args[0]], [list(row) for row in args[1]], list(args[2])]

    for i, (args, want) in enumerate(_VI_CASES):
        copy = tables(args)
        def compare(got, want=want, copy=copy, args=args):
            if (not isinstance(got, (list, tuple)) or len(got) != len(want)
                    or not all(_real(v) for v in got)):
                raise _Mismatch("output must be a list/tuple with one value per state")
            for k, (v, w) in enumerate(zip(got, want)):
                close(v, w, "V of state " + str(k))
            if copy != tables(args):
                raise _Mismatch("an input table was mutated")
        run("value_iteration " + str(i), value_iteration, (*copy, args[3], args[4]), compare)

    for i, (args, want) in enumerate(_REPORT_CASES):
        seeds, returns = list(args[0]), list(args[1])
        probe = (list(seeds), list(returns))
        def compare(got, want=want, seeds=seeds, returns=returns, probe=probe):
            if (not isinstance(got, (list, tuple)) or len(got) != 6
                    or type(got[0]) is not int):
                raise _Mismatch("output must be a length-6 list/tuple (n int, mean, std, sem, worst, best)")
            if got[0] != want[0]:
                raise _Mismatch("n is wrong")
            if want[2] is None:
                if got[2] is not None or got[3] is not None:
                    raise _Mismatch("std and sem must be None for a single seed")
            else:
                if not _real(got[2]) or not _real(got[3]):
                    raise _Mismatch("std and sem must be finite numbers")
                close(got[2], want[2], "sample standard deviation")
                close(got[3], want[3], "standard error")
            if not _real(got[1]) or not _real(got[4]) or not _real(got[5]):
                raise _Mismatch("mean, worst and best must be finite numbers")
            close(got[1], want[1], "mean")
            close(got[4], want[4], "worst return")
            close(got[5], want[5], "best return")
            if probe[0] != seeds or probe[1] != returns:
                raise _Mismatch("an input list was mutated")
        run("seed_report " + str(i), seed_report, probe, compare)

    for i, (args, want) in enumerate(_LOOP_CASES):
        copy = tables(args)
        def compare(got, want=want, copy=copy, args=args):
            if not isinstance(got, (list, tuple)) or len(got) != 3:
                raise _Mismatch("output must be a length-3 list/tuple (best_goal, best_farm, loophole)")
            for k, name in ((0, "best_goal"), (1, "best_farm")):
                if (got[k] is None) != (want[k] is None):
                    raise _Mismatch(name + ": None / not-None decision is wrong")
                if got[k] is not None:
                    if not _real(got[k]):
                        raise _Mismatch(name + " must be a finite number or None")
                    close(got[k], want[k], name)
            if type(got[2]) is not bool:
                raise _Mismatch("loophole must be a real bool")
            if got[2] != want[2]:
                raise _Mismatch("loophole decision is wrong")
            if copy != tables(args):
                raise _Mismatch("an input table was mutated")
        run("find_reward_loophole " + str(i), find_reward_loophole,
            (*copy, args[3], args[4]), compare)

    def chain(case):
        table, transitions, alpha, gamma, final = case
        table = [list(row) for row in table]
        for k, (s, a, r, s2, term, trunc) in enumerate(transitions):
            before = table[s][a]
            got = q_learning_update(before, r, list(table[s2]), alpha, gamma, term, trunc)
            if not _vector(got, 2):
                raise _Mismatch("update output must be a length-2 list/tuple of finite int/float")
            target = _oracle_target(r, max(table[s2]), gamma, term)
            try:
                close(got[0], target, "target")
                close(got[1], before + alpha*(target - before), "q_new")
            except _Mismatch as error:
                raise _Mismatch(str(error) + " at transition " + str(k)
                                + " of the episode")
            table[s][a] = got[1]
        for s, row in enumerate(final):
            for a, want in enumerate(row):
                close(table[s][a], want, "final Q(" + str(s) + "," + str(a) + ")")
    for i, case in enumerate(_CHAINS):
        run("update chain " + str(i), chain, (case,), lambda got: None)

    # extreme but valid sizes and magnitudes, judged against the reference
    big = [[(3*s + 5*a + 1) % 8 for a in range(4)] for s in range(8)]
    pay = [[((7*s + 3*a) % 11) - 5 for a in range(4)] for s in range(8)]
    done = [False]*7 + [True]
    ramp = [1e6, -1e6, 0.0, 5e5, -5e5, 1.0, 1e6, -1e6]
    long_rewards = [((7*t) % 13) - 6.0 for t in range(200)]
    seeds = list(range(10**9 - 99, 10**9 + 1))
    spread = [((17*i) % 23) - 11.5 for i in range(100)]

    def vector(want):
        def compare(got):
            if (not isinstance(got, (list, tuple)) or len(got) != len(want)
                    or not all(_real(g) for g in got)):
                raise _Mismatch("output must be a list/tuple of finite int/float of the right length")
            for k, (g, w) in enumerate(zip(got, want)):
                close(g, w, "entry " + str(k))
        return compare

    def report_compare(got):
        want = _oracle_report(spread)
        if not isinstance(got, (list, tuple)) or len(got) != 6:
            raise _Mismatch("output must be a length-6 list/tuple")
        for k in range(6):
            if want[k] is None:
                continue
            close(got[k], want[k], "entry " + str(k))

    def loop_compare(got):
        want = _oracle_loophole(big, pay, done, 0, 8)
        if not isinstance(got, (list, tuple)) or len(got) != 3 or type(got[2]) is not bool:
            raise _Mismatch("output must be a length-3 list/tuple with a real bool")
        for k in (0, 1):
            if (got[k] is None) != (want[k] is None):
                raise _Mismatch("None / not-None decision is wrong")
            if got[k] is not None:
                close(got[k], want[k], "entry " + str(k))
        if got[2] != want[2]:
            raise _Mismatch("loophole decision is wrong")

    def pair_compare(want):
        return lambda got: pair(got, want, "(target, q_new)")

    run("boundary q_learning_update (8 actions, 1e6 values)", q_learning_update,
        (1e6, -1e6, list(ramp), 1.0, 0.9, False, False),
        pair_compare((-1e6 + 0.9*1e6, -1e6 + 0.9*1e6)))
    run("boundary sarsa_update (last of 8 actions)", sarsa_update,
        (-1e6, 1e6, list(ramp), 7, 0.5, 1.0, False, False),
        pair_compare((1e6 - 1e6, (-1e6 + 0.0)/2)))
    run("boundary epsilon_greedy_probs (8 actions, 1e6 values, ties)", epsilon_greedy_probs,
        (list(ramp), 0.5), vector(_oracle_probs(ramp, 0.5)))
    run("boundary discounted_returns (200 rewards)", discounted_returns,
        (list(long_rewards), 0.999, 1e6), vector(_oracle_returns(long_rewards, 0.999, 1e6)))
    run("boundary value_iteration (8 states, 4 actions, 1000 sweeps)", value_iteration,
        (big, pay, done, 1.0, 1000), vector(_oracle_vi(big, pay, done, 1.0, 1000)))
    run("boundary seed_report (100 seeds up to 1e9)", seed_report,
        (list(seeds), list(spread)), report_compare)
    run("boundary find_reward_loophole (8 states, 4 actions, horizon 8)", find_reward_loophole,
        (big, pay, done, 0, 8), loop_compare)

    nan, inf = float('nan'), float('inf')
    num = [nan, inf, -inf, True, "1", None, 1e6 + 1, -1e6 - 1]
    unit = [nan, inf, -0.01, 1.01, True, "0.5", None]
    flag = [0, 1, "True", None, 2.0]
    good_table = ([[1, 0], [2, 0], [2, 2]], [[-1, -1], [10, -1], [0, 0]],
                  [False, False, True])
    tables_bad = {
        "next_state": [[], [[1, 0], [2, 0]], [[1, 0], [2, 0], [2]], [[1, 0], [2, 0], [2, 3]],
                       [[1, 0], [2, 0], [2, -1]], [[1, 0], [2, 0], [2, True]],
                       [[1, 0], [2, 0], [2, 1.0]], [[1, 0], [2, 0], [2, "2"]],
                       [[0]]*9, "abc", None, [[1, 0], [2, 0], 2],
                       [[0, 0, 0, 0, 0]]*3],
        "reward": [[], [[-1, -1], [10, -1]], [[-1, -1], [10, -1], [0]],
                   [[-1, -1], [10, -1], [0, nan]], [[-1, -1], [10, -1], [0, inf]],
                   [[-1, -1], [10, -1], [0, True]], [[-1, -1], [10, -1], [0, 1001]],
                   [[-1, -1], [10, -1], [0, -1001]], [[-1, -1], [10, -1], [0, "0"]],
                   None, "abc"],
        "terminal": [[], [False, False], [False, False, True, True], [False, 0, True],
                     [0, 0, 1], ["no", False, True], None, "abc", [None, False, True]],
    }
    signatures = [
        ("q_learning_update", q_learning_update,
         ("q_sa", "r", "q_next", "alpha", "gamma", "terminated", "truncated"),
         (1.0, 1.0, [1.0, 2.0], 0.5, 0.5, False, False)),
        ("sarsa_update", sarsa_update,
         ("q_sa", "r", "q_next", "a_next", "alpha", "gamma", "terminated", "truncated"),
         (1.0, 1.0, [1.0, 2.0], 1, 0.5, 0.5, False, False)),
        ("epsilon_greedy_probs", epsilon_greedy_probs, ("q_values", "epsilon"),
         ([1.0, 2.0], 0.1)),
        ("discounted_returns", discounted_returns, ("rewards", "gamma", "bootstrap"),
         ([1.0, 2.0], 0.9, 0.0)),
        ("value_iteration", value_iteration,
         ("next_state", "reward", "terminal", "gamma", "sweeps"), (*good_table, 0.9, 5)),
        ("seed_report", seed_report, ("seeds", "returns"), ([1, 2, 3], [1.0, 2.0, 3.0])),
        ("find_reward_loophole", find_reward_loophole,
         ("next_state", "reward", "terminal", "start", "horizon"), (*good_table, 0, 5)),
    ]
    bad = {
        "q_sa": num, "r": num, "alpha": unit, "gamma": unit, "epsilon": unit,
        "terminated": flag, "truncated": flag,
        "q_next": [[], [nan], [inf], [True], [1.0, "x"], [1e6 + 1], [0.0]*9, "ab",
                   None, 3.0, [[1.0]]],
        "a_next": [-1, 2, 5, True, 1.0, "1", None, nan],
        "q_values": [[], [nan], [inf], [True], [1.0, None], [1e6 + 1], [0.0]*9,
                     "ab", None, 3.0],
        "rewards": [[], [nan], [inf], [True], [1.0, "x"], [1e6 + 1], [-1e6 - 1],
                    [0.0]*201, "ab", None, 3.0],
        "bootstrap": num,
        "sweeps": [0, -1, 1001, 5.0, True, nan, "5", None],
        "seeds": [[], [1, 1, 3], [1, 2], [1, 2, 3, 4], [1, 2, 3.0], [1, 2, True],
                  [-1, 2, 3], [1, 2, 10**9 + 1], [1, 2, "3"], None, "abc", 5],
        "returns": [[], [1.0, 2.0], [1.0, 2.0, 3.0, 4.0], [1.0, 2.0, nan], [1.0, 2.0, inf],
                    [1.0, 2.0, True], [1.0, 2.0, 1e6 + 1], [1.0, 2.0, "3"], None, "abc", 5,
                    [1.0]*101],
        "start": [-1, 3, 2, True, 0.0, "0", None, nan],
        "horizon": [0, -1, 9, 5.0, True, nan, "5", None],
        **tables_bad,
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
                except NotImplementedError:
                    break
                except Exception as error:
                    failures.append(label + ": raised " + type(error).__name__
                                    + " instead of ValueError")
                    continue
                failures.append(label + ": returned instead of raising ValueError")
    # validated even where the value is not used (terminated steps)
    unused = [
        ("q_learning_update", q_learning_update, (1.0, 1.0, [], 0.5, 0.5, True, False)),
        ("q_learning_update", q_learning_update, (1.0, 1.0, [nan], 0.5, 0.5, True, True)),
        ("sarsa_update", sarsa_update, (1.0, 1.0, [1.0, 2.0], 5, 0.5, 0.5, True, False)),
        ("sarsa_update", sarsa_update, (1.0, 1.0, [1.0, 2.0], -1, 0.5, 0.5, True, True)),
    ]
    for title, function, args in unused:
        label = "invalid " + title + " (terminated step) " + repr(args)[:40]
        try:
            function(*args)
        except ValueError:
            continue
        except NotImplementedError:
            break
        except Exception as error:
            failures.append(label + ": raised " + type(error).__name__
                            + " instead of ValueError")
            continue
        failures.append(label + ": returned instead of raising ValueError")
    return failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual RL experiment-core self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
