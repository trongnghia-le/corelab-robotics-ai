"""CoreLab Grid Bayes localization lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the nine functions below, then run your edited file locally:
  Windows: py -3 L09-localization.v1.py
  macOS/Linux: python3 L09-localization.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared model: a robot lives on a 1-D corridor of n cells numbered 0..n-1 (left to
right). The belief is a list of n probabilities, belief[i] = P(robot is in cell i).
The world is a list of n integers, world[i] = 1 if cell i has a door and 0 if it is
plain wall. A sensor reports z = 1 ("door") or z = 0 ("no door"); it is right with
probability p_correct and wrong with probability 1 - p_correct, independently at
every reading. Nothing is random here: every function is deterministic.

Numeric conventions (every argument): finite int or float, never bool. Cell indices,
offsets, world entries and z are int. cyclic is a real bool. Invalid input of any
kind raises ValueError. No function mutates its arguments. Every returned sequence is a
new list (type list, not a tuple, and never the same object as an input) of finite
floats or ints.
  belief: list/tuple of n = 2..64 numbers, each in [0, 1], sum within 1e-9 of 1.
  weights: list/tuple of 1..64 numbers, each in [0, 1e6]; they need not sum to 1.
  kernel: list/tuple of 1..8 numbers in [0, 1] summing within 1e-9 of 1.
  offset0: int in -8..8.   world: n ints in {0, 1}, same n as the belief.
  p_correct: number in [0, 1].   z: int 0 or 1.   u0: number with 0 <= u0 < 1.
Outputs are compared entry by entry with an absolute tolerance of 1e-9 (the
effective sample size: 1e-9*len(weights)); the resampling indices must match exactly.

Contracts:
  normalize(weights) -> list of len(weights) floats summing to 1: weights[i]/sum.
      If every weight is 0 the sum is 0 and nothing can be normalised: raise
      ValueError. Never invent a uniform belief silently.
  predict(belief, kernel, offset0, cyclic) -> new belief after one noisy move.
      kernel[k] is the probability that the robot's displacement is offset0 + k
      cells (positive = towards higher indices), so a kernel of length 3 with
      offset0 = 0 means "undershoot by 0, move 1, overshoot to 2" for kernel[0..2]
      at displacements 0, 1, 2. Exactly:
          new[j] = sum of belief[i]*kernel[k] over all (i, k) landing in j.
      cyclic == True: the corridor is a ring, a cell index is taken modulo n (even
      several times round when the kernel is longer than n).
      cyclic == False: the ends are walls. A displacement past a wall leaves the
      robot against it: its mass lands in cell 0 (or n-1). No mass is lost, so the
      output still sums to the input sum. predict does NOT renormalise.
  sensor_likelihood(world, z, p_correct) -> list of n floats:
      p_correct where world[i] == z, else 1 - p_correct. It is a likelihood
      P(z | robot in cell i), not a belief: it does not sum to 1.
  update(belief, likelihood) -> posterior: normalize(belief[i]*likelihood[i]).
      likelihood: list/tuple of n numbers in [0, 1e6], same n as the belief. If
      every product is 0 the evidence is impossible under the belief: raise
      ValueError (a model that said "impossible" cannot be conditioned on it).
  localize(belief, world, p_correct, kernel, offset0, cyclic, observations)
      -> belief after processing observations in order. For each z: update with
      sensor_likelihood(world, z, p_correct), THEN predict with the motion. So the
      sensor sees the cell the robot is in, then the robot moves. observations:
      list/tuple of 0..32 ints in {0, 1}; an empty list returns the belief as a
      new list. A zero posterior at any step raises ValueError.
  modes(belief) -> ascending list of the cell indices i with
      belief[i] >= max(belief) - 1e-9. More than one index = ambiguous belief.
  effective_sample_size(weights) -> (sum w)^2 / sum w^2, a float between 1 and
      len(weights). Scaling all weights leaves it unchanged. Raise ValueError when
      every weight is 0.
  particle_update(cells, weights, world, z, p_correct) -> list of len(cells) new
      weights. Particle k sits in cell cells[k] (int in 0..n-1, repeats allowed)
      and has prior weight weights[k] (len(cells) == len(weights) in 1..64, n =
      len(world) in 2..64). New weight = normalize(weights[k]*L[cells[k]]) with
      L = sensor_likelihood(world, z, p_correct). All-zero products: ValueError.
  systematic_resample(weights, u0) -> list of N = len(weights) particle indices.
      Weights are normalised first (all zero: ValueError). With cum[i] =
      w[0] + ... + w[i] (normalised), the N sample positions are
          p_k = (u0 + k)/N for k = 0..N-1
      and position p_k selects the SMALLEST index i with cum[i] > p_k, so a position
      that falls exactly on a boundary cum[i] goes to the next particle. The result
      is non-decreasing; a weight-0 particle is never chosen. u0 is the single
      explicit draw: u0 is divided by N together with k (u0 is NOT a position by
      itself). With u0 just below 1 the float position (N-1+u0)/N can round to
      1.0, and the last cumulative value can be a hair below 1: never index past
      the last particle with positive weight (clamp to it). Particle i then appears floor(N*w[i]) or
      ceil(N*w[i]) times; the self-check verifies this as well as the exact indices.
      Boundary ties are only tested where every number is exactly representable.
Self-check tolerances are per-case probabilities, not physical accuracy. Failure
messages name the case and the kind of mismatch, never the expected numbers.
"your code raised X on a VALID input" means the case is inside the contract and must
return; "invalid f(name=...)" lines are the opposite: that input must raise
ValueError. A function still raising NotImplementedError is reported once.

Pause before coding - write your predictions down first:
  1. Uniform belief over a ring of 4 cells with doors at cells 0 and 3, one z = 1
     reading with p_correct = 0.8: what is the posterior? Which cells tie?
  2. Why does a symmetric layout (the same door pattern shifted by half a ring)
     make some beliefs impossible to disambiguate, however many readings you take?
  3. A wall corridor, robot surely in the last cell, motion kernel [0.25,0.5,0.25]
     at displacements 0, 1, 2: where does the mass go? And on a ring?
  4. A sensor with p_correct = 1 reports z that contradicts the belief: what should
     happen, and why is p_correct = 0.999 safer than 1.0?
  5. Do update-then-predict and predict-then-update agree? Try the 4-cell case with
     a deterministic move.
  6. Weights [1,1,1,1] versus [4,0,0,0]: what is the effective sample size of each?
  7. Systematic resampling of four equal weights with u0 = 0.5: which indices?
     Why must u0 be divided by N?
This kit covers a 1-D discrete Bayes (histogram) filter and a few deterministic
particle-weight operations only: no SLAM, no continuous state, no random draws or
convergence statistics, no real sensors or simulators, no map learning.
Reflection: why does passing this toy NOT validate localization on a real robot?
(Think about odometry drift, a map that is itself wrong, unmodelled sensor errors and
correlated readings, dynamic obstacles, kidnapping, discretisation error, particle
depletion, tuning of the likelihood and motion noise, timing, and recovery behaviour.)
"""
import math
from fractions import Fraction


def normalize(weights):
    raise NotImplementedError("Divide by the sum; decide what an all-zero sum means")


def predict(belief, kernel, offset0, cyclic):
    raise NotImplementedError("Scatter each belief[i]*kernel[k] to cell i+offset0+k (wrap or clamp)")


def sensor_likelihood(world, z, p_correct):
    raise NotImplementedError("p_correct where the world agrees with z, else 1 - p_correct")


def update(belief, likelihood):
    raise NotImplementedError("Multiply cell by cell, then normalise")


def localize(belief, world, p_correct, kernel, offset0, cyclic, observations):
    raise NotImplementedError("For each z: sense (update), then move (predict)")


def modes(belief):
    raise NotImplementedError("All cells within 1e-9 of the largest belief")


def effective_sample_size(weights):
    raise NotImplementedError("(sum w)^2 / sum of w squared")


def particle_update(cells, weights, world, z, p_correct):
    raise NotImplementedError("Weight each particle by the likelihood of its cell, normalise")


def systematic_resample(weights, u0):
    raise NotImplementedError("Positions (u0 + k)/N against the cumulative weights")


# ---- SPOILER BELOW: the _..._ref functions are complete exact references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length=None):
    return (isinstance(value, (list, tuple)) and (length is None or len(value) == length)
            and all(_real(v) for v in value))


def _normalize_ref(weights):
    total = sum((Fraction(w) for w in weights), Fraction(0))
    if total == 0:
        raise ValueError("all-zero weights")
    return [Fraction(w) / total for w in weights]


def _predict_ref(belief, kernel, offset0, cyclic):
    n = len(belief)
    out = [Fraction(0)] * n
    for i, b in enumerate(belief):
        for k, pk in enumerate(kernel):
            j = i + offset0 + k
            j = j % n if cyclic else min(max(j, 0), n - 1)
            out[j] += Fraction(b) * Fraction(pk)
    return out


def _likelihood_ref(world, z, p_correct):
    p = Fraction(p_correct)
    return [p if w == z else 1 - p for w in world]


def _update_ref(belief, likelihood):
    return _normalize_ref([Fraction(b) * Fraction(m) for b, m in zip(belief, likelihood)])


def _localize_ref(belief, world, p_correct, kernel, offset0, cyclic, observations):
    current = [Fraction(b) for b in belief]
    for z in observations:
        current = _update_ref(current, _likelihood_ref(world, z, p_correct))
        current = _predict_ref(current, kernel, offset0, cyclic)
    return current


def _modes_ref(belief):
    top = max(belief)
    return [i for i, b in enumerate(belief) if b >= top - 1e-9]


def _ess_ref(weights):
    total = sum((Fraction(w) for w in weights), Fraction(0))
    squares = sum((Fraction(w) ** 2 for w in weights), Fraction(0))
    if total == 0:
        raise ValueError("all-zero weights")
    return total * total / squares


def _particle_ref(cells, weights, world, z, p_correct):
    like = _likelihood_ref(world, z, p_correct)
    return _normalize_ref([Fraction(w) * like[c] for c, w in zip(cells, weights)])


def _resample_ref(weights, u0):
    total = sum((Fraction(w) for w in weights), Fraction(0))
    if total == 0:
        raise ValueError("all-zero weights")
    n = len(weights)
    cum, running = [], Fraction(0)
    for w in weights:
        running += Fraction(w)
        cum.append(running)
    chosen = []
    for k in range(n):
        position = (Fraction(u0) + k) / n * total
        chosen.append(next(i for i, c in enumerate(cum) if c > position))
    return chosen


_RING4 = [1, 0, 0, 1]
_Q = [0.25, 0.5, 0.25]
# normalize(weights): "hand" answers worked on paper, None = exact reference.
_NORM_CASES = [
    ([1, 1, 2], [0.25, 0.25, 0.5]),
    ([0, 0, 5], [0.0, 0.0, 1.0]),
    ([0.2, 0.3, 0.5], [0.2, 0.3, 0.5]),
    ([1e-12, 3e-12], [0.25, 0.75]),
    ([7], [1.0]),
    ([3.0, 0.0, 1.0, 0.0, 4.0, 2.0, 6.0], None),
    ([1e6, 1e6, 1e-6, 5e5], None),
]
# predict(belief, kernel, offset0, cyclic)
_PRED_CASES = [
    (([0, 1, 0, 0, 0], _Q, 0, True), [0.0, 0.25, 0.5, 0.25, 0.0]),
    (([0, 0, 0, 0, 1], _Q, 0, True), [0.5, 0.25, 0.0, 0.0, 0.25]),
    (([0, 0, 0, 0, 1], _Q, 0, False), [0.0, 0.0, 0.0, 0.0, 1.0]),
    (([1, 0, 0, 0], [0.1, 0.8, 0.1], -1, False), [0.9, 0.1, 0.0, 0.0]),
    (([1, 0, 0, 0], [0.1, 0.8, 0.1], -1, True), [0.8, 0.1, 0.0, 0.1]),
    (([0.5, 0.3, 0.2], [1], 2, True), [0.3, 0.2, 0.5]),
    (([0.5, 0.3, 0.2], [1], 0, False), [0.5, 0.3, 0.2]),
    (([0.7, 0.3], [0.2, 0.2, 0.2, 0.2, 0.2], -2, True), [0.54, 0.46]),
    (([0.0, 0.0, 1.0, 0.0, 0.0], [0.5, 0.0, 0.5], -1, False), [0.0, 0.5, 0.0, 0.5, 0.0]),
    (([0.05, 0.15, 0.3, 0.1, 0.25, 0.05, 0.1], [0.1, 0.2, 0.4, 0.2, 0.1], -2, True), None),
    (([0.05, 0.15, 0.3, 0.1, 0.25, 0.05, 0.1], [0.1, 0.2, 0.4, 0.2, 0.1], -2, False), None),
    (([0.3, 0.7], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], 8, False), [0.0, 1.0]),
    (([0, 0, 1, 0, 0, 0], [0.7, 0.2, 0.1], 0, True), [0.0, 0.0, 0.7, 0.2, 0.1, 0.0]),
    (([0, 0, 0, 1, 0, 0], [0.7, 0.2, 0.1], -1, False), [0.0, 0.0, 0.7, 0.2, 0.1, 0.0]),
    (([0, 0, 0, 0, 0, 1], [0.6, 0.3, 0.1], -2, False), [0.0, 0.0, 0.0, 0.6, 0.3, 0.1]),
    (([0.6, 0.4], [0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], -8, True), [0.52, 0.48]),
    (([0.5, 0.3, 0.2], [0.05, 0.05, 0.1, 0.1, 0.1, 0.1, 0.2, 0.3], 1, True), None),
    (([0.5, 0.3, 0.2], [0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05], -8, True), None),
    (([1 / 64] * 64, [0.125, 0.75, 0.125], 0, True), [1 / 64] * 64),
    (([1.0] + [0.0] * 63, [0.0] * 7 + [1.0], -8, False), [1.0] + [0.0] * 63),
]
# sensor_likelihood(world, z, p_correct)
_LIK_CASES = [
    (([1, 0, 0, 1], 1, 0.8), [0.8, 0.2, 0.2, 0.8]),
    (([1, 0, 0, 1], 0, 0.8), [0.2, 0.8, 0.8, 0.2]),
    (([1, 0, 0, 1], 1, 1.0), [1.0, 0.0, 0.0, 1.0]),
    (([1, 0, 0, 1], 1, 0), [0.0, 1.0, 1.0, 0.0]),
    (([0, 0, 0], 1, 0.7), [0.3, 0.3, 0.3]),
    (([1, 0, 1, 1, 0], 0, 0.9), None),
]
# update(belief, likelihood)
_UPD_CASES = [
    (([0.25] * 4, [0.8, 0.2, 0.2, 0.8]), [0.4, 0.1, 0.1, 0.4]),
    (([0.5, 0.5, 0.0], [1, 3, 100]), [0.25, 0.75, 0.0]),
    (([0.1, 0.2, 0.7], [0.5, 0.5, 0.5]), [0.1, 0.2, 0.7]),
    (([0.1, 0.2, 0.7], [0.0, 1.0, 0.0]), [0.0, 1.0, 0.0]),
    (([0.2, 0.2, 0.2, 0.2, 0.2], [0.9, 0.1, 0.1, 0.9, 0.1]), None),
    (([0.6, 0.1, 0.1, 0.2], [1e6, 1e-6, 5.0, 0.0]), None),
]
# localize(belief, world, p_correct, kernel, offset0, cyclic, observations)
_LOC_CASES = [
    (([0.25] * 4, [1, 0, 0, 0], 1.0, [1], 1, True, [1, 0]), [0.0, 0.0, 1.0, 0.0]),
    (([0.4, 0.3, 0.2, 0.1], [1, 0, 0, 0], 0.5, [1], 1, True, []), [0.4, 0.3, 0.2, 0.1]),
    (([1.0 / 6] * 6, [1, 0, 1, 0, 0, 0], 0.9, [1], 2, True, [1, 1]), None),
    (([0.2] * 5, [1, 0, 0, 1, 0], 0.8, [0.1, 0.8, 0.1], 0, True, [1, 0, 0]), None),
    (([0.2] * 5, [1, 0, 0, 1, 0], 0.8, [0.1, 0.8, 0.1], 0, False, [1, 0, 0, 1]), None),
    (([0.125] * 8, [1, 0, 0, 1, 1, 0, 0, 1], 0.75, [0.25, 0.5, 0.25], -1, True,
      [1, 1, 0, 0, 1]), None),
    (([0.2] * 5, [1, 0, 0, 1, 0], 0.8, [0.7, 0.2, 0.1], 0, True, [1, 0]), None),
    (([0.2] * 5, [1, 0, 0, 1, 0], 0.8, [0.1, 0.2, 0.7], -1, False, [1, 1, 0]), None),
]
# modes(belief)
_MODE_CASES = [
    ([0.4, 0.1, 0.1, 0.4], [0, 3]),
    ([0.2, 0.5, 0.3], [1]),
    ([0.25, 0.25, 0.25, 0.25], [0, 1, 2, 3]),
    ([0.5, 0.5 - 5e-10, 5e-10], [0, 1]),
    ([0.5, 0.5 - 2e-9, 2e-9], [0]),
    ([0.0, 1.0], [1]),
]
# effective_sample_size(weights); tolerance 1e-9*len(weights).
_ESS_CASES = [
    ([1, 1, 1, 1], 4.0),
    ([1, 0, 0, 0], 1.0),
    ([1, 1, 0, 0], 2.0),
    ([0.5, 0.25, 0.25], 8 / 3),
    ([3, 1], 1.6),
    ([30, 10], 1.6),
    ([0.1, 0.9, 0.4, 0.2, 0.3, 0.05, 0.5], None),
    ([2.5], 1.0),
]
# particle_update(cells, weights, world, z, p_correct)
_PART_CASES = [
    (([0, 1, 2, 3], [0.25] * 4, _RING4, 1, 0.8), [0.4, 0.1, 0.1, 0.4]),
    (([0, 0, 1], [2, 1, 1], [1, 0], 1, 0.75), [0.6, 0.3, 0.1]),
    (([0, 1, 1], [0.0, 1.0, 1.0], [1, 0], 0, 0.9), [0.0, 0.5, 0.5]),
    (([2, 2, 4, 0, 1, 3], [0.1, 0.3, 0.2, 0.15, 0.05, 0.2], [0, 1, 1, 0, 1], 1, 0.85), None),
    (([0], [3.0], [1, 0], 0, 0.6), [1.0]),
]
# systematic_resample(weights, u0) -> indices. (hand, "tie" = a position falls
# exactly on a boundary, all numbers exactly representable; None = exact reference.)
_RES_CASES = [
    (([1, 1, 1, 1], 0.5), [0, 1, 2, 3], "hand"),
    (([1, 0, 0, 0], 0.3), [0, 0, 0, 0], "hand"),
    (([3, 1], 0.4), [0, 0], "hand"),
    (([3, 1], 0.9), [0, 1], "hand"),
    (([0.1, 0.2, 0.3, 0.4], 0.5), [1, 2, 3, 3], "hand"),
    (([0, 1, 0, 1], 0.2), [1, 1, 3, 3], "hand"),
    (([5], 0.7), [0], "hand"),
    (([1, 1, 1, 1], 0.0), [0, 1, 2, 3], "tie"),
    (([3, 1], 0.5), [0, 1], "tie"),
    (([0.5, 0.25, 0.125, 0.125], 0.5), [0, 0, 1, 3], "tie"),
    (([0.3, 0.1, 0.05, 0.25, 0.3, 0.0, 0.02, 0.08, 0.1, 0.3, 0.2, 0.05], 0.37), None, "ref"),
    (([5, 1, 1, 1, 1, 1, 7, 2, 2, 0, 0, 3, 4, 1, 1, 1], 0.81), None, "ref"),
    (([3, 1], 0.9999999999999999), [0, 1], "round"),
    (([1, 1, 2], 0.9999999999999999), [1, 2, 2], "round"),
    (([1, 0], 0.9999999999999999), [0, 0], "round"),
    (([2, 1, 0, 0], 0.9999999999999999), [0, 0, 1, 1], "round"),
    (([0.3, 0.7] * 32, 0.123), None, "ref"),
]


def _fresh(value):
    """Nested list copy of a tuple table entry, so mutation can be detected."""
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return text + ": over-strict validation, or a zero sum that is not actually zero?)"
    return text + ")"


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    calls, missing = {}, {}

    def attempt(name, label, function, args):
        calls[name] = calls.get(name, 0) + 1
        try:
            return True, function(*args)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
        except Exception as error:
            failures.append(label + ": " + _raised(error))
        return False, None

    def run(name, label, function, args, compare):
        ok, got = attempt(name, label, function, args)
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def distribution(got, length, want, name, total=1.0, given=()):
        if not (type(got) is list and _vector(got, length)):
            raise _Mismatch("output must be a new list of " + str(length)
                            + " finite int/float values")
        if any(got is g for g in given):
            raise _Mismatch("output is the same list object as an input; return a new list")
        for i in range(length):
            if got[i] < -1e-12:
                raise _Mismatch(name + " entry " + str(i) + " is negative")
        if not abs(sum(got) - total) <= 1e-9:
            raise _Mismatch(name + " has the wrong total mass")
        for i in range(length):
            if not abs(got[i] - float(want[i])) <= 1e-9:
                raise _Mismatch(name + " entry " + str(i) + " is wrong (tolerance 1e-09)")

    for i, (weights, hand) in enumerate(_NORM_CASES):
        want = _normalize_ref(weights) if hand is None else hand
        args = (_fresh(weights),)

        def compare(got, args=args, weights=weights, want=want):
            if _fresh(args[0]) != _fresh(weights):
                raise _Mismatch("input weights were mutated")
            distribution(got, len(weights), want, "normalized weight", 1.0, args)
        run("normalize", "normalize " + str(i), normalize, args, compare)

    for i, (args, hand) in enumerate(_PRED_CASES):
        belief, kernel, offset0, cyclic = args
        want = _predict_ref(*args) if hand is None else hand
        call = (_fresh(belief), _fresh(kernel), offset0, cyclic)

        def compare(got, call=call, args=args, want=want):
            if _fresh(call[0]) != _fresh(args[0]) or _fresh(call[1]) != _fresh(args[1]):
                raise _Mismatch("an input list was mutated")
            distribution(got, len(args[0]), want, "predicted belief", sum(args[0]), call)
        run("predict", "predict " + str(i), predict, call, compare)

    for i, (args, hand) in enumerate(_LIK_CASES):
        want = _likelihood_ref(*args) if hand is None else hand
        call = (_fresh(args[0]), args[1], args[2])

        def compare(got, call=call, args=args, want=want):
            if _fresh(call[0]) != _fresh(args[0]):
                raise _Mismatch("input world was mutated")
            if not (type(got) is list and _vector(got, len(args[0]))):
                raise _Mismatch("output must be a new list of finite int/float values")
            for k in range(len(want)):
                if not abs(got[k] - float(want[k])) <= 1e-12:
                    raise _Mismatch("likelihood entry " + str(k) + " is wrong")
        run("sensor_likelihood", "sensor_likelihood " + str(i), sensor_likelihood, call, compare)

    for i, (args, hand) in enumerate(_UPD_CASES):
        want = _update_ref(*args) if hand is None else hand
        call = (_fresh(args[0]), _fresh(args[1]))

        def compare(got, call=call, args=args, want=want):
            if _fresh(call[0]) != _fresh(args[0]) or _fresh(call[1]) != _fresh(args[1]):
                raise _Mismatch("an input list was mutated")
            distribution(got, len(args[0]), want, "posterior", 1.0, call)
        run("update", "update " + str(i), update, call, compare)

    for i, (args, hand) in enumerate(_LOC_CASES):
        want = _localize_ref(*args) if hand is None else hand
        call = (_fresh(args[0]), _fresh(args[1]), args[2], _fresh(args[3]), args[4], args[5],
                _fresh(args[6]))

        def compare(got, call=call, args=args, want=want):
            if _fresh(call[0]) != _fresh(args[0]) or _fresh(call[1]) != _fresh(args[1]) \
                    or _fresh(call[3]) != _fresh(args[3]) or _fresh(call[6]) != _fresh(args[6]):
                raise _Mismatch("an input list was mutated")
            distribution(got, len(args[0]), want, "final belief", 1.0, call)
        run("localize", "localize " + str(i), localize, call, compare)

    for i, (belief, want) in enumerate(_MODE_CASES):
        def compare(got, belief=belief, want=want):
            if not (type(got) is list and all(type(v) is int for v in got)):
                raise _Mismatch("output must be a list of int cell indices")
            if list(got) != want:
                raise _Mismatch("the set of tied most-probable cells is wrong")
        run("modes", "modes " + str(i), modes, (_fresh(belief),), compare)

    for i, (weights, hand) in enumerate(_ESS_CASES):
        want = float(_ess_ref(weights)) if hand is None else hand

        def compare(got, weights=weights, want=want):
            if not _real(got):
                raise _Mismatch("output must be one finite int/float")
            if not abs(got - want) <= 1e-9 * len(weights):
                raise _Mismatch("effective sample size is wrong")
        run("effective_sample_size", "effective_sample_size " + str(i),
            effective_sample_size, (_fresh(weights),), compare)

    for i, (args, hand) in enumerate(_PART_CASES):
        want = _particle_ref(*args) if hand is None else hand
        call = (_fresh(args[0]), _fresh(args[1]), _fresh(args[2]), args[3], args[4])

        def compare(got, call=call, args=args, want=want):
            if any(_fresh(call[k]) != _fresh(args[k]) for k in range(3)):
                raise _Mismatch("an input list was mutated")
            distribution(got, len(args[0]), want, "particle weight", 1.0, call)
        run("particle_update", "particle_update " + str(i), particle_update, call, compare)

    for i, (args, hand, kind) in enumerate(_RES_CASES):
        want = _resample_ref(*args) if hand is None else hand
        call = (_fresh(args[0]), args[1])

        def compare(got, call=call, args=args, want=want, kind=kind):
            if _fresh(call[0]) != _fresh(args[0]):
                raise _Mismatch("input weights were mutated")
            n = len(args[0])
            if not (type(got) is list and len(got) == n
                    and all(type(v) is int and 0 <= v < n for v in got)):
                raise _Mismatch("output must be " + str(n) + " int indices in 0.." + str(n - 1)
                                + " (never past the last particle)")
            if any(got[k] > got[k + 1] for k in range(n - 1)):
                raise _Mismatch("indices must be non-decreasing")
            total = sum((Fraction(w) for w in args[0]), Fraction(0))
            for j in range(n):
                share = Fraction(n) * Fraction(args[0][j]) / total
                copies = list(got).count(j)
                if not math.floor(share) <= copies <= math.ceil(share):
                    raise _Mismatch("particle " + str(j) + " is copied a number of times that"
                                    " systematic resampling cannot produce")
            if list(got) != want:
                raise _Mismatch("the selected indices are wrong"
                                + (" (a position exactly on a cumulative boundary goes to the"
                                   " next particle)" if kind == "tie" else ""))
        run("systematic_resample", "systematic_resample " + str(i) + " (" + kind + ")",
            systematic_resample, call, compare)

    nan, inf = float('nan'), float('inf')
    good_belief = [0.25, 0.25, 0.5]
    probs = [nan, inf, True, -0.1, 1.1, "0.5", None]
    bad = {
        "belief": [[0.5], [0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] + [0.0] * 60,
                   [0.5, 0.4], [0.6, 0.6], [-0.5, 1.5], [nan, 1.0], [inf, 0.0], [True, 0.0, 0.0],
                   [0.5, "0.5"], [0.5, None], "ab", None, 5, {0: 1.0}, [[0.5], [0.5]],
                   [0.25, 0.25, 0.5 + 2e-9], [0.5, 0.5, 0.5]],
        "weights": [[], [0.0], [-1.0, 2.0], [nan, 1.0], [inf, 1.0], [True, 1.0], [1.0, "1"],
                    [1e6 + 1, 1.0], [1.0] * 65, "ab", None, 3, [None, 1.0]],
        "kernel": [[], [0.5, 0.4], [0.7, 0.7], [-0.5, 1.5], [nan, 1.0], [True], [0.125] * 9,
                   [0.5, 0.5, "0"], "ab", None, 1.0, [1.0 + 2e-9]],
        "offset0": [-9, 9, 0.0, 1.0, True, nan, "0", None],
        "cyclic": [1, 0, "True", None, 1.0],
        "world": [[1], [1] * 65, [1, 0, 2], [1, 0, True], [1, 0, 0.0], [1, 0, -1],
                  [1, 0, "1"], [1, 0, None], "abc", None, [[1], [0], [1]]],
        "z": [2, -1, 0.0, 1.0, True, False, nan, "1", None],
        "p_correct": probs,
        "likelihood": [[1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [-0.1, 1.0, 1.0], [1e6 + 1, 1.0, 1.0],
                       [nan, 1.0, 1.0], [inf, 1.0, 1.0], [True, 1.0, 1.0], [1.0, "1", 1.0],
                       "abc", None, [None, 1.0, 1.0]],
        "observations": [[2], [-1], [0.0], [True], [1, 0, 1.5], ["1"], [None], [1] * 33, "10",
                         None, 1, [[1]]],
        "cells": [[], [-1, 0], [3, 0], [0.0, 1], [True, 1], [0], [nan, 1], ["0", 1],
                  [0] * 65, None, "01", 1],
        "u0": [-0.1, 1.0, 1.5, nan, inf, True, "0.5", None],
    }
    world3 = [1, 0, 1]
    signatures = [
        ("normalize", normalize, ("weights",), ([1.0, 2.0],)),
        ("predict", predict, ("belief", "kernel", "offset0", "cyclic"),
         (good_belief, [0.25, 0.5, 0.25], 0, True)),
        ("sensor_likelihood", sensor_likelihood, ("world", "z", "p_correct"), (world3, 1, 0.8)),
        ("update", update, ("belief", "likelihood"), (good_belief, [1.0, 2.0, 3.0])),
        ("localize", localize,
         ("belief", "world", "p_correct", "kernel", "offset0", "cyclic", "observations"),
         (good_belief, world3, 0.8, [0.25, 0.5, 0.25], 0, True, [1, 0])),
        ("modes", modes, ("belief",), (good_belief,)),
        ("effective_sample_size", effective_sample_size, ("weights",), ([1.0, 2.0],)),
        ("particle_update", particle_update, ("cells", "weights", "world", "z", "p_correct"),
         ([0, 1, 2], [1.0, 1.0, 1.0], world3, 1, 0.8)),
        ("systematic_resample", systematic_resample, ("weights", "u0"), ([1.0, 2.0], 0.5)),
    ]
    for title, function, names_, args in signatures:
        for slot, name in enumerate(names_):
            for value in bad[name]:
                trial = args[:slot] + (value,) + args[slot + 1:]
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
    zero_cases = (
        ("normalize", normalize, ([0, 0, 0],), "all-zero weights"),
        ("effective_sample_size", effective_sample_size, ([0.0, 0.0],), "all-zero weights"),
        ("systematic_resample", systematic_resample, ([0, 0, 0], 0.5), "all-zero weights"),
        ("update", update, ([0.5, 0.5, 0.0], [0.0, 0.0, 1.0]), "an impossible observation"),
        ("update", update, ([1.0, 0.0], [0.0, 1.0]), "a likelihood that kills the belief"),
        ("particle_update", particle_update, ([0, 0], [1.0, 1.0], [1, 0], 0, 1.0),
         "every particle contradicted by an exact sensor"),
        ("localize", localize, ([0.5, 0.25, 0.25], [1, 0], 0.8, [1], 0, True, [1]),
         "a world list shorter than the belief"),
        ("localize", localize, ([0.5, 0.5], [1, 0, 0], 0.8, [1], 0, True, [1]),
         "a world list longer than the belief"),
        ("update", update, ([0.5, 0.5], [1.0, 1.0, 1.0]), "a likelihood of the wrong length"),
        ("localize", localize, ([1.0, 0.0, 0.0, 0.0], [1, 0, 0, 0], 1.0, [1], 1, True, [0]),
         "a reading an exact sensor says is impossible"),
        ("localize", localize, ([0.5, 0.5, 0.0, 0.0], [1, 0, 0, 0], 1.0, [1], 1, True, [1, 1]),
         "the second reading contradicts the moved belief"),
    )
    for title, function, args, what in zero_cases:
        calls[title] = calls.get(title, 0) + 1
        try:
            function(*_fresh(args))
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault(title, []).append(title + " zero case")
            continue
        except Exception as error:
            failures.append(title + " with " + what + ": raised " + type(error).__name__
                            + " instead of ValueError")
            continue
        failures.append(title + " with " + what + ": returned instead of raising ValueError")
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
    print("CoreLab manual Grid Bayes localization self-check - practice only, no signed evidence")
    for note in notes:
        print("Note: " + note)
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
