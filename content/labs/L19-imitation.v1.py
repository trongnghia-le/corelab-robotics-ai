"""CoreLab Episode QA and imitation baseline lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the seven functions below, then run your edited file locally:
  Windows: py -3 L19-imitation.v1.py
  macOS/Linux: python3 L19-imitation.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared toy world (numerical practice on tiny lists, not a robot dataset):
a demonstration dataset is a list of episodes. An episode is a triple
(times, obs, acts): times in seconds, one scalar observation and one scalar
action per time step (any consistent units). An episode has no field for a
session or an id; sessions and ids are separate parallel lists of non-empty
str, one entry per episode. A behaviour-cloning (BC) baseline is the least
squares line  a = w*o + b  fitted on the TRAINING episodes only, judged on
held-out episodes against a mean-action baseline. That is a data-hygiene
exercise: no neural network, no LeRobot or real robot data, no closed-loop
rollout and no claim about generalisation.

Contracts (numbers are int or float, never bool; lists may be lists or
tuples; bounds inclusive; invalid input raises ValueError; never mutate):
  qa_episode(times, obs, acts, max_gap, obs_range, act_range) -> list of str
      times: 0..1000 FINITE numbers with |t| <= 1e6. obs, acts: 0..1000 numbers
      each; unlike times they may be NaN or +-inf, because that is exactly what
      the check must report. max_gap: finite, 0 < max_gap <= 1e6 seconds.
      obs_range = (lo, hi) and act_range = (lo, hi): two finite numbers with
      |value| <= 1e6 and lo <= hi, the allowed closed interval.
      Returns the names of the defects found, each at most once, in this fixed
      order (the list is empty for a clean episode):
        "empty"               times, obs and acts are all empty (nothing else is
                              reported then);
        "length-mismatch"     len(times), len(obs), len(acts) are not all equal;
        "time-not-increasing" some consecutive pair has times[i+1] <= times[i]
                              (a repeated timestamp counts);
        "time-gap"            some consecutive pair has
                              times[i+1] - times[i] > max_gap + 1e-9 (the 1e-9
                              absorbs float noise, so a gap equal to max_gap such
                              as 0.1 built from k*0.1 is NOT a defect);
        "non-finite-value"    any NaN or +-inf in obs or acts;
        "obs-out-of-range"    some FINITE obs value outside obs_range;
        "act-out-of-range"    some FINITE act value outside act_range.
      The checks are independent: a length mismatch does not hide a time gap, and
      a NaN is "non-finite-value" only, never out of range.
  qa_dataset(episodes, max_gap, obs_range, act_range) -> list of (index, names)
      episodes: 1..200 triples (times, obs, acts), each satisfying the qa_episode
      argument contract. For every episode with at least one defect return a pair
      (index, list of str), ascending by index: its qa_episode names, then
      "duplicate" last when the episode has exactly the same times, obs and acts
      (compared element by element with ==, so a tuple equals a list and 1 equals
      1.0) as an EARLIER episode. The first copy is never flagged "duplicate";
      episodes without defects are left out. Duplicate detection on episodes that
      contain NaN is not graded.
  split_by_session(sessions, test_sessions) -> (train_indices, test_indices)
      sessions: 2..1000 non-empty str, the session of each episode.
      test_sessions: a list/tuple of non-empty str (not a single str), each equal
      to some entry of sessions; repeats are ignored; at least one session must
      remain for training and at least one is held out, else ValueError. Every
      episode of a held-out session goes to the test side, all others to the train
      side. Return two lists of ascending episode indices.
  leaked_ids(train_ids, test_ids) -> list of str
      Two lists/tuples of 0..1000 non-empty str. Return the DISTINCT ids that
      occur on both sides, in plain string order (sorted(); "ep-10" before
      "ep-2"). Empty list when nothing leaks.
  fit_linear(obs, acts) -> (w, b)
      obs, acts: equal-length lists of 2..1000 finite numbers, |value| <= 1e6.
      The least-squares line a = w*o + b through the points (obs[i], acts[i]),
      i.e. the normal equations  w = Sxy/Sxx,  b = mean(acts) - w*mean(obs)  with
      Sxx = sum (o-mean o)^2, Sxy = sum (o-mean o)(a-mean a). ValueError when all
      obs are exactly equal (no slope is defined). Tolerance 1e-9 absolute.
  bc_baseline(episodes, fit_indices, eval_indices) -> (w, b, mse_bc, mse_mean)
      episodes: 1..200 triples (times, obs, acts); the three lists of each triple
      have equal length >= 1 (episodes may differ in length), finite numbers, |value| <= 1e6 (run qa_dataset first; this function does not repair
      data). fit_indices, eval_indices: non-empty lists/tuples of distinct valid
      episode indices (int, not bool, 0 <= i < len(episodes)); order is irrelevant.
      They MAY overlap - that is a leaky run, which you can then expose with
      leaked_ids; do not raise on overlap. Pool all steps of the fit episodes and
      fit (w, b) with fit_linear on them ONLY (the evaluation episodes must not
      influence w, b or the baseline). mse_bc is the mean over all pooled steps of
      the eval episodes (every step weighs equally, not every episode) of
      (act - (w*obs + b))^2. mse_mean uses the constant prediction mean of the FIT
      episodes' actions on the same eval steps. Units are action units squared.
      ValueError when the pooled fit observations are all equal. Tolerance 1e-9.
  best_lag(obs, acts, max_lag) -> int
      obs, acts: equal-length lists of 3..1000 finite numbers, |value| <= 1e6;
      max_lag: an int (not bool) with 0 <= max_lag <= len(obs) - 3. For a lag k in
      -max_lag..max_lag pair obs[i] with acts[i+k] for every i for which both
      indices exist (k > 0: the recorded action answers an observation k steps
      EARLIER; k < 0: the action is recorded k steps before its observation). The
      score of k is the mean squared residual of the least-squares line through
      those pairs (SSE divided by the number of pairs; if all paired obs are equal
      the line is the mean action). Return the lag with the smallest score. Ties
      are not graded; yours should prefer the smaller |k|, then the smaller k.
      Warning: the score is a mean over a different number of pairs for every lag,
      so on noisy data an extreme lag with only 3 or 4 pairs can fit by chance and
      win. Keep max_lag small (at most about len(obs)//3) when you use it for real
      checks; the self-check cases are chosen with clear margins.
      Pairs never wrap around: acts[(i+k) % n] is wrong.
Tolerances: all float results 1e-9 absolute. Return types: lists/tuples of the
documented shape holding finite int/float (str names for the defect lists),
indices and the lag are int.

Typical toy workflow (do each check on your own tiny data first): qa_dataset ->
remove or fix defective episodes -> split_by_session -> leaked_ids on the ids you
kept -> bc_baseline -> compare mse_bc with mse_mean on episodes the fit never saw.
When the comparison looks wrong, shrink to the smallest dataset that still shows
it, then collect fresh episodes before you trust a fix.

Pause before coding - write your predictions down first:
  1. times [0, 0.1, 0.1, 0.3]: which defect does the repeated 0.1 give, and does
     the 0.2 s jump also give a gap with max_gap = 0.15?
  2. Does a time axis built as k*0.1 pass max_gap = 0.1? Why is an epsilon needed?
  3. Why is one NaN not also "obs-out-of-range"? What would a sort-then-compare
     range check do with a NaN?
  4. Two sessions share a recording day and three episodes each. You split at the
     episode level, 2 train / 1 test per session. What leaks that a session split
     avoids?
  5. A BC line is fitted on episodes {0, 1} and judged on {1, 2}. Will the held-out
     MSE usually look better or worse than with {2} alone? Does that prove anything
     about a new session?
  6. Actions are logged 2 steps after the observation they answer. What does
     best_lag return, and what does lag 0 do to the fitted slope?
Self-check tolerances are per case, not physical accuracy. Failure messages name
the case and the kind of mismatch, never the expected values. "your code raised X"
means your function raised on a VALID input. A function still raising
NotImplementedError is reported once.
This does not implement a neural policy, LeRobot dataset loading, real robot
logs, multi-dimensional observations, closed-loop rollout, or any statistical
test of generalisation.
Reflection: why does passing this toy NOT validate a real imitation pipeline?
(Think about demonstrator quality and variance, compounding errors in closed-loop
rollout, covariate shift between sessions, hidden confounders such as operator or
day, multimodal actions that an average destroys, many-dimensional observations,
and a held-out set of a handful of episodes that cannot support any generalisation
claim.)

Background link only: LeRobot, https://github.com/huggingface/lerobot, is an
optional open-source robot-learning library; no code, data or text from it is
redistributed here and nothing in this kit needs it.
"""
import math
from fractions import Fraction


def qa_episode(times, obs, acts, max_gap, obs_range, act_range):
    raise NotImplementedError("Run each defect check on its own and list the names in the fixed order")


def qa_dataset(episodes, max_gap, obs_range, act_range):
    raise NotImplementedError("qa_episode per episode, then flag a copy of an EARLIER episode as duplicate")


def split_by_session(sessions, test_sessions):
    raise NotImplementedError("Whole sessions go to one side; return ascending indices for train and test")


def leaked_ids(train_ids, test_ids):
    raise NotImplementedError("Distinct ids present on both sides, sorted as plain strings")


def fit_linear(obs, acts):
    raise NotImplementedError("w = Sxy/Sxx and b = mean(acts) - w*mean(obs); no slope if obs are all equal")


def bc_baseline(episodes, fit_indices, eval_indices):
    raise NotImplementedError("Pool the fit episodes, fit the line there only, score every eval step")


def best_lag(obs, acts, max_lag):
    raise NotImplementedError("For each lag, pair obs[i] with acts[i+k], fit a line, keep the smallest mean residual")


# ---- SPOILER BELOW: _ref_* are complete exact references (Fraction normal ----
# ---- equations), and the case tables hold expected answers. Attempt first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


_NAMES = ("empty", "length-mismatch", "time-not-increasing", "time-gap",
          "non-finite-value", "obs-out-of-range", "act-out-of-range")


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _is_num(value):
    return type(value) in (int, float)


def _frac(value):
    return Fraction(value)


def _ref_qa(times, obs, acts, max_gap, obs_range, act_range):
    if not (times or obs or acts):
        return ["empty"]
    found = []
    if not len(times) == len(obs) == len(acts):
        found.append("length-mismatch")
    steps = [times[i+1] - times[i] for i in range(len(times) - 1)]
    if any(s <= 0 for s in steps):
        found.append("time-not-increasing")
    if any(s > max_gap + 1e-9 for s in steps):
        found.append("time-gap")
    if any(not math.isfinite(v) for v in list(obs) + list(acts)):
        found.append("non-finite-value")
    if any(math.isfinite(v) and not obs_range[0] <= v <= obs_range[1] for v in obs):
        found.append("obs-out-of-range")
    if any(math.isfinite(v) and not act_range[0] <= v <= act_range[1] for v in acts):
        found.append("act-out-of-range")
    return found


def _ref_dataset(episodes, max_gap, obs_range, act_range):
    out = []
    for i, (times, obs, acts) in enumerate(episodes):
        names = _ref_qa(times, obs, acts, max_gap, obs_range, act_range)
        copy = any(list(times) == list(t) and list(obs) == list(o) and list(acts) == list(a)
                   for t, o, a in episodes[:i])
        if copy:
            names.append("duplicate")
        if names:
            out.append((i, names))
    return out


def _ref_fit(obs, acts):
    """Exact rational normal equations: w = (nSxy - SxSy)/(nSxx - Sx^2)."""
    n = len(obs)
    xs = [_frac(v) for v in obs]
    ys = [_frac(v) for v in acts]
    sx, sy = sum(xs), sum(ys)
    denominator = n*sum(x*x for x in xs) - sx*sx
    if denominator == 0:
        raise ValueError("constant observations")
    w = (n*sum(x*y for x, y in zip(xs, ys)) - sx*sy)/denominator
    return w, (sy - w*sx)/n


def _ref_bc(episodes, fit_indices, eval_indices):
    fx = [v for i in fit_indices for v in episodes[i][1]]
    fy = [v for i in fit_indices for v in episodes[i][2]]
    w, b = _ref_fit(fx, fy)
    mean = sum(_frac(v) for v in fy)/len(fy)
    ex = [v for i in eval_indices for v in episodes[i][1]]
    ey = [v for i in eval_indices for v in episodes[i][2]]
    mse_bc = sum((_frac(y) - (w*_frac(x) + b))**2 for x, y in zip(ex, ey))/len(ex)
    mse_mean = sum((_frac(y) - mean)**2 for y in ey)/len(ey)
    return float(w), float(b), float(mse_bc), float(mse_mean)


def _ref_scores(obs, acts, max_lag):
    n = len(obs)
    scores = []
    for k in range(-max_lag, max_lag + 1):
        low, high = max(0, -k), min(n, n - k)
        xs = [_frac(obs[i]) for i in range(low, high)]
        ys = [_frac(acts[i + k]) for i in range(low, high)]
        m = len(xs)
        mx, my = sum(xs)/m, sum(ys)/m
        sxx = sum((x - mx)**2 for x in xs)
        syy = sum((y - my)**2 for y in ys)
        sxy = sum((x - mx)*(y - my) for x, y in zip(xs, ys))
        scores.append((((syy - sxy*sxy/sxx) if sxx else syy)/m, abs(k), k))
    return scores


def _ref_lag(obs, acts, max_lag):
    return min(_ref_scores(obs, acts, max_lag))[2]


_GAP = 0.25
_R1 = (-1.0, 1.0)
# qa_episode(times, obs, acts, max_gap, obs_range, act_range) -> names (hand-derived).
_QA_CASES = [
    (([0.0, 0.1, 0.2, 0.3], [0.0, 0.5, 1.0, -1.0], [0.2, 0.4, -0.3, 0.0], 0.1, _R1, _R1), []),
    (([0.0, 0.1, 0.1, 0.3], [0.0, 0.1, 0.2, 0.3], [0.0, 0.1, 0.2, 0.3], _GAP, _R1, _R1),
     ["time-not-increasing"]),
    (([0.0, 0.2, 0.1, 0.3], [0.0, 0.1, 0.2, 0.3], [0.0, 0.1, 0.2, 0.3], _GAP, _R1, _R1),
     ["time-not-increasing"]),
    (([0.0, 0.1, 0.5, 0.6], [0.0, 0.1, 0.2, 0.3], [0.0, 0.1, 0.2, 0.3], _GAP, _R1, _R1),
     ["time-gap"]),
    (([0.0, 0.25, 0.5], [0.0, 0.1, 0.2], [0.0, 0.1, 0.2], _GAP, _R1, _R1), []),
    (([0.0, 0.1, 0.2, 0.3], [0.0, 0.1, 0.2, 0.3], [0.0, 0.1, 0.2], _GAP, _R1, _R1),
     ["length-mismatch"]),
    (([0.0, 0.1, 0.2], [0.0, float("nan"), 0.2], [0.0, 0.1, float("inf")], _GAP, _R1, _R1),
     ["non-finite-value"]),
    (([0.0, 0.1, 0.2], [0.0, 1.5, 0.2], [-1.2, 0.1, 0.2], _GAP, _R1, _R1),
     ["obs-out-of-range", "act-out-of-range"]),
    (([0.0, 1.0, 0.5], [0.0, 0.1, 0.2], [0.0, 0.1, -3.0], _GAP, _R1, _R1),
     ["time-not-increasing", "time-gap", "act-out-of-range"]),
    (([], [], [], _GAP, _R1, _R1), ["empty"]),
    (([0.0], [0.5], [0.5], _GAP, _R1, _R1), []),
    (([0.0, 0.1], [], [], _GAP, _R1, _R1), ["length-mismatch"]),
    (((0, 1, 2), (0, 1, 0), (1, -1, 0), 1, (0, 1), (-1, 1)), []),
    (([0.0, 0.5, 0.6], [0.0, 0.1], [0.0, 0.1, 0.2], _GAP, _R1, _R1),
     ["length-mismatch", "time-gap"]),
    (([k*0.1 for k in range(12)], [0.0]*12, [0.0]*12, 0.1, _R1, _R1), []),
    (([0.0, 0.1, 0.2], [1.0, -1.0, float("-inf")], [0.2, 0.1, 0.0], _GAP, _R1, _R1),
     ["non-finite-value"]),
    (([0.0, 0.1, 0.2], [1.0000001, 0.0, 0.0], [0.0, -1.0, 0.0], _GAP, _R1, _R1),
     ["obs-out-of-range"]),
    (([0.0, 0.2], [0.0, 0.0], [0.0, 0.0], 0.1, _R1, _R1), ["time-gap"]),
    (([0.0, 0.1, 0.2], [2.0, -5.0, 0.0], [0.0, 3.0, 0.0], _GAP, (-5.0, 2.0), (0.0, 3.0)), []),
    (([1.0, 0.0], [0.0, 0.0], [0.0, 0.0], _GAP, _R1, _R1), ["time-not-increasing"]),
    (([0.0, 0.1, 0.2], [2.0, 3.0, 0.0], [0.0, 0.0, 0.0], _GAP, _R1, _R1), ["obs-out-of-range"]),
    (([0.0, 0.1, 0.2], [0.0, 0.0, 0.0], [0.0, float("nan"), 0.1], _GAP, _R1, _R1),
     ["non-finite-value"]),
    (([0.0, 0.1, 0.2], [0.0, 0.5, 0.0], [0.0, 0.1, 0.1], _GAP, _R1, (0.1, 0.1)),
     ["act-out-of-range"]),
    (([0.0, 0.250001], [0.0, 0.0], [0.0, 0.0], _GAP, _R1, _R1), ["time-gap"]),
]
_EPA = ([0.0, 0.1, 0.2], [0.0, 0.5, 0.25], [0.1, 0.2, 0.3])
_EPB = ([0.0, 0.1, 0.2], [0.5, 0.0, -0.25], [0.3, 0.2, 0.1])
_EPGAP = ([0.0, 0.1, 0.9], [0.0, 0.5, 0.25], [0.1, 0.2, 0.3])
# qa_dataset(episodes, max_gap, obs_range, act_range) -> [(index, names)].
_DATASET_CASES = [
    (([_EPA, _EPA, _EPGAP], _GAP, _R1, _R1), [(1, ["duplicate"]), (2, ["time-gap"])]),
    (([_EPGAP, _EPGAP], _GAP, _R1, _R1), [(0, ["time-gap"]), (1, ["time-gap", "duplicate"])]),
    (([_EPA, _EPB], _GAP, _R1, _R1), []),
    (([(tuple(_EPA[0]), tuple(_EPA[1]), tuple(_EPA[2])), ([0, 0.1, 0.2], [0, 0.5, 0.25], _EPA[2])],
      _GAP, _R1, _R1), [(1, ["duplicate"])]),
    (([_EPA, _EPA, _EPA], _GAP, _R1, _R1), [(1, ["duplicate"]), (2, ["duplicate"])]),
    (([_EPB, _EPA, ([0.0, 0.1, 0.2], [0.0, 0.5, 0.26], _EPA[2]), _EPB], _GAP, _R1, _R1),
     [(3, ["duplicate"])]),
    (([_EPA], _GAP, _R1, _R1), []),
    (([_EPA, (_EPA[0], _EPA[1], _EPB[2])], _GAP, _R1, _R1), []),
    (([_EPA, ([0.0, 0.1, 0.3], _EPA[1], _EPA[2])], _GAP, _R1, _R1), []),
    (([([0.0, 0.1], [0.0, 0.0], [0.0]), _EPA, ([0.0, 0.1], [0.0, 0.0], [0.0])], _GAP, _R1, _R1),
     [(0, ["length-mismatch"]), (2, ["length-mismatch", "duplicate"])]),
]
_SESSIONS = ["s1", "s1", "s2", "s3", "s2", "s3"]
# split_by_session(sessions, test_sessions) -> (train, test).
_SPLIT_CASES = [
    ((_SESSIONS, ["s2"]), ([0, 1, 3, 5], [2, 4])),
    ((_SESSIONS, ["s3", "s1"]), ([2, 4], [0, 1, 3, 5])),
    ((_SESSIONS, ["s2", "s2"]), ([0, 1, 3, 5], [2, 4])),
    ((["a", "b"], ["b"]), ([0], [1])),
    ((("x", "y", "x", "y", "z"), ("z",)), ([0, 1, 2, 3], [4])),
    ((["day-1/a", "day-1/b", "day-2/a"], ["day-1/a"]), ([1, 2], [0])),
    ((["s1", "s10", "s2"], ["s1"]), ([1, 2], [0])),
]
# leaked_ids(train_ids, test_ids) -> sorted distinct overlap.
_LEAK_CASES = [
    ((["e1", "e2", "e3"], ["e3", "e4", "e2"]), ["e2", "e3"]),
    (([], []), []),
    (((["e1", "e1"]), ["e1", "e1"]), ["e1"]),
    ((["ep-10", "ep-2", "ep-1"], ["ep-2", "ep-10", "ep-3"]), ["ep-10", "ep-2"]),
    ((["E1", "e2"], ["e1", "E2"]), []),
    ((("e1", "e2"), ("e2",)), ["e2"]),
    ((["a"], []), []),
]
# fit_linear(obs, acts) -> (w, b).
_FIT_CASES = [
    (([0, 1, 2], [1, 3, 5]), (2.0, 1.0)),
    (([1, 2, 3, 4], [2, 2, 4, 4]), (0.8, 1.0)),
    (([0, 2], [1, -3]), (-2.0, 1.0)),
    (([1, 2, 3], [4, 4, 4]), (0.0, 4.0)),
    (([-2, -1, 1, 2], [1, 0, 0, -1]), (-0.4, 0.0)),
    (([1000, 1001, 1002], [3, 5, 7]), (2.0, -1997.0)),
    (((0.5, 1.5), (2.0, 2.5)), (0.5, 1.75)),
]
_E_FIT_A = ([0.0, 0.1, 0.2], [0, 1, 2], [1, 3, 5])
_E_TEST_B = ([0.0, 0.1], [3, 4], [8, 8])
_E_P = ([0.0, 0.1], [0, 1], [0, 1])
_E_Q = ([0.0, 0.1], [2, 3], [3, 3])
_E_T = ([0.0, 0.1], [1, 2], [2, 2])
_E_LONG = ([0.0, 0.1, 0.2, 0.3], [0, 1, 2, 3], [0, 1, 2, 3])
_E_ONE = ([0.0], [10], [10])
_E_THREE = ([0.0, 0.1, 0.2], [4, 5, 6], [5, 6, 7])
_E_C1 = ([0.0, 0.1], [0, 1], [1, 3])
_E_C2 = ([0.0, 0.1], [2, 3], [5, 7])
_E_C3 = ([0.0], [4], [10])
_E_FLAT = ([0.0, 0.1, 0.2], [0, 1, 2], [2, 2, 2])
_E_AT5 = ([0.0], [5], [2])
# bc_baseline(episodes, fit_indices, eval_indices) -> (w, b, mse_bc, mse_mean).
_BC_CASES = [
    (([_E_FIT_A, _E_TEST_B], [0], [1]), (2.0, 1.0, 1.0, 25.0)),
    (([_E_P, _E_Q, _E_T], [0, 1], [2]), (1.1, 0.1, 0.365, 0.0625)),
    (([_E_FIT_A, _E_TEST_B], [0, 1], [1]), (1.9, 1.2, 0.925, 9.0)),
    (([_E_LONG, _E_ONE, _E_THREE], [0], [1, 2]), (1.0, 0.0, 0.75, 33.75)),
    (([_E_C1, _E_C3, _E_C2], [2, 0], [1]), (2.0, 1.0, 1.0, 36.0)),
    (([_E_FLAT, _E_AT5], [0], [1]), (0.0, 2.0, 0.0, 0.0)),
    (([_E_TEST_B, _E_FIT_A], [1], [0]), (2.0, 1.0, 1.0, 25.0)),
]
_LAG_OBS = [0.0, 1.0, -1.0, 2.0, 0.0, -2.0, 1.0, 3.0]
# best_lag(obs, acts, max_lag) -> lag; acts[j] = 2*obs[j-2] + 1 (lag 2), etc.
_LAG_CASES = [
    ((_LAG_OBS, [1.0, 1.0, 1.0, 3.0, -1.0, 5.0, 1.0, -3.0], 3), 2),
    ((_LAG_OBS, [3.0, -1.0, 5.0, 1.0, -3.0, 3.0, 7.0, 0.5], 3), -1),
    ((_LAG_OBS, [1.0, 3.0, -1.0, 5.0, 1.0, -3.0, 3.0, 7.0], 3), 0),
    ((_LAG_OBS, [1.0, 1.0, 1.0, 3.0, -1.0, 5.0, 1.0, -3.0], 0), 0),
    ((_LAG_OBS, [1.0, 1.0, 1.0, 3.0, -1.0, 5.0, 1.0, -3.0], 4), 2),
    (([-2, -1, -2, -1, 0, -1, -2, -1, 2], [0, 1, -4, -2, -2, -1, 1, -1, -3], 6), 2),
    (([-2, 1, 2, 1, 3, -1, 3, -2, 1, 2], [1, 2, 0, 3, -1, 4, -1, 2, 3, 2], 3), -1),
    ((tuple(_LAG_OBS), tuple([-5.0, -5.0, -5.0, -4.5, -5.5, -4.0, -5.0, -6.0]), 3), 2),
]


def _fresh(value):
    if isinstance(value, (list, tuple)):
        return type(value)(_fresh(v) for v in value)
    return value


def _close(got, want, name, tolerance=1e-9):
    if abs(got - want) > tolerance:
        raise _Mismatch(name + " is wrong (tolerance " + repr(tolerance) + ")")


def _raised(error):
    return "your code raised " + type(error).__name__ + " on a valid input"


def self_check():
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    missing = {}
    calls = {}

    def run(name, label, function, args, compare):
        calls[name] = calls.get(name, 0) + 1
        keep = _fresh(args)
        try:
            got = function(*_fresh(args))
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            return
        except Exception as error:
            failures.append(label + ": " + _raised(error))
            return
        try:
            if repr(args) != repr(keep):
                raise _Mismatch("an input was changed")
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))

    def names_of(got):
        if not isinstance(got, (list, tuple)) or not all(type(v) is str for v in got):
            raise _Mismatch("result must be a list/tuple of str defect names")
        return list(got)

    for i, (args, want) in enumerate(_QA_CASES):
        def compare(got, want=want):
            if names_of(got) != want:
                raise _Mismatch("defect names are wrong (set, spelling or fixed order)")
        run("qa_episode", "qa_episode " + str(i), qa_episode, args, compare)

    for i, (args, want) in enumerate(_DATASET_CASES):
        def compare(got, want=want):
            if not isinstance(got, (list, tuple)):
                raise _Mismatch("result must be a list/tuple of (index, names) pairs")
            shown = []
            for pair in got:
                if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                        or type(pair[0]) is not int):
                    raise _Mismatch("each entry must be a pair (int index, names)")
                shown.append((pair[0], names_of(pair[1])))
            if shown != want:
                raise _Mismatch("flagged episodes or their names are wrong"
                                " (clean episodes omitted, ascending, duplicate last)")
        run("qa_dataset", "qa_dataset " + str(i), qa_dataset, args, compare)

    for i, (args, (train, test)) in enumerate(_SPLIT_CASES):
        def compare(got, train=train, test=test):
            if (not isinstance(got, (list, tuple)) or len(got) != 2
                    or not all(isinstance(side, (list, tuple))
                               and all(type(v) is int for v in side) for side in got)):
                raise _Mismatch("result must be a pair of index lists (train, test)")
            if list(got[0]) != train or list(got[1]) != test:
                raise _Mismatch("train/test index lists are wrong"
                                " (whole sessions, ascending order)")
        run("split_by_session", "split_by_session " + str(i), split_by_session, args, compare)

    for i, (args, want) in enumerate(_LEAK_CASES):
        def compare(got, want=want):
            if names_of(got) != want:
                raise _Mismatch("leaked ids are wrong (distinct, plain string order)")
        run("leaked_ids", "leaked_ids " + str(i), leaked_ids, args, compare)

    def pair_check(got, want, labels, size):
        if (not isinstance(got, (list, tuple)) or len(got) != size
                or not all(_real(v) for v in got)):
            raise _Mismatch("result must be a length-" + str(size)
                            + " list/tuple of finite int/float")
        for value, target, label in zip(got, want, labels):
            _close(value, target, label)

    for i, (args, want) in enumerate(_FIT_CASES):
        run("fit_linear", "fit_linear " + str(i), fit_linear, args,
            lambda got, want=want: pair_check(got, want, ("slope w", "intercept b"), 2))

    for i, (args, want) in enumerate(_BC_CASES):
        run("bc_baseline", "bc_baseline " + str(i), bc_baseline, args,
            lambda got, want=want: pair_check(
                got, want, ("slope w", "intercept b", "held-out BC mse",
                            "held-out mean-baseline mse"), 4))

    for i, (args, want) in enumerate(_LAG_CASES):
        def compare(got, want=want):
            if type(got) is not int:
                raise _Mismatch("lag must be an int")
            if got != want:
                raise _Mismatch("lag is wrong (sign convention or pairing)")
        run("best_lag", "best_lag " + str(i), best_lag, args, compare)

    nan, inf = float("nan"), float("inf")
    ep = ([0.0, 0.1], [0.0, 0.5], [0.1, 0.2])
    rng = (-1.0, 1.0)
    time_bad = [[nan, 0.1], [inf, 0.1], [True, 0.1], ["0", 0.1], [0.0, 1e6 + 1],
                [0.0] * 1001, [[0.0], 0.1], "ab", None, {0: 0.1}, [None]]
    value_bad = [[True, 0.5], ["0", 0.5], [None, 0.5], [[0.0], 0.5], [0.0] * 1001,
                 "ab", None, {0: 0.5}]
    gap_bad = [0, -0.1, nan, inf, True, "0.25", None, 1e6 + 1]
    range_bad = [(1.0, -1.0), (nan, 1.0), (0.0, inf), (0.0,), (0.0, 1.0, 2.0), "ab",
                 None, (True, 1.0), (0.0, "1"), (-1e6 - 1, 0.0), 0.5, [[0.0, 1.0], 1.0]]
    ep_bad = [[], None, "abc", [1], [([0.0], [0.0])], [([0.0], [0.0], [0.0], [0.0])],
              [(0.0, [0.0], [0.0])], [([True], [0.0], [0.0])], [([nan], [0.0], [0.0])],
              [ep] * 201, [{"t": [0.0]}]]
    sess = ["s1", "s2", "s2"]
    id_bad = [None, "ab", [1], [""], [None], [["a"]], ["a"] * 1001, {"a": 1}, [True]]
    nums_bad = [[1.0, nan], [1.0, inf], [True, 2.0], ["1", 2.0], [None, 2.0],
                [1e6 + 1, 2.0], [-1e6 - 1, 2.0], [1.0] * 1001, "ab", None, [[1.0], 2.0]]
    idx_bad = [[], None, [5], [-1], [0, 0], [True], [0.0], "0", [None], [[0]], 0]
    bc_eps = [([0.0, 0.1], [0.0, 1.0], [1.0, 2.0]), ([0.0, 0.1], [2.0, 3.0], [2.0, 3.0])]
    lag_obs = [0.0, 1.0, -1.0, 2.0, 0.0, 3.0]
    lag_acts = [1.0, 1.0, 3.0, -1.0, 5.0, 1.0]
    signatures = [
        ("qa_episode", qa_episode, ("times", "obs", "acts", "max_gap", "obs_range", "act_range"),
         ([0.0, 0.1], [0.0, 0.5], [0.1, 0.2], 0.25, rng, rng),
         {"times": time_bad, "obs": value_bad, "acts": value_bad, "max_gap": gap_bad,
          "obs_range": range_bad, "act_range": range_bad}),
        ("qa_dataset", qa_dataset, ("episodes", "max_gap", "obs_range", "act_range"),
         ([ep], 0.25, rng, rng),
         {"episodes": ep_bad, "max_gap": gap_bad, "obs_range": range_bad,
          "act_range": range_bad}),
        ("split_by_session", split_by_session, ("sessions", "test_sessions"),
         (sess, ["s1"]),
         {"sessions": [[], ["s1"], [1, 2], ["", "a"], None, "ab", [True, "a"],
                       ["a", "b"] * 501, ["a", None]],
          "test_sessions": [[], ["zz"], ["s1", "s2"], [1], None, "s1", [""], ["s1", "zz"],
                            [None], [["s1"]], 0]}),
        ("leaked_ids", leaked_ids, ("train_ids", "test_ids"), (["a", "b"], ["b"]),
         {"train_ids": id_bad, "test_ids": id_bad}),
        ("fit_linear", fit_linear, ("obs", "acts"), ([0.0, 1.0, 2.0], [1.0, 3.0, 5.0]),
         {"obs": nums_bad + [[1.0, 1.0, 1.0], [1.0], [], [2.0, 2.0]],
          "acts": nums_bad + [[1.0, 2.0], [1.0], []]}),
        ("bc_baseline", bc_baseline, ("episodes", "fit_indices", "eval_indices"),
         (bc_eps, [0], [1]),
         {"episodes": ep_bad + [[([0.0, 0.1], [0.0], [0.0, 1.0]), bc_eps[1]],
                                [([], [], []), bc_eps[1]],
                                [([0.0, 0.1], [nan, 1.0], [1.0, 2.0]), bc_eps[1]],
                                [([0.0, 0.1], [0.0, 1.0], [True, 2.0]), bc_eps[1]],
                                [([0.0, 0.1], [0.0, 1.0], [inf, 2.0]), bc_eps[1]],
                                [([0.0, 0.1], [2.0, 2.0], [1.0, 2.0]), bc_eps[1]],
                                [([0.0], [0.0], [1.0]), bc_eps[1]]],
          "fit_indices": idx_bad + [[2]], "eval_indices": idx_bad + [[2]]}),
        ("best_lag", best_lag, ("obs", "acts", "max_lag"), (lag_obs, lag_acts, 2),
         {"obs": nums_bad + [[1.0, 2.0]], "acts": nums_bad + [[1.0] * 5],
          "max_lag": [-1, 4, 1.0, True, "1", None, nan, 1001]}),
    ]
    for title, function, names, args, bad in signatures:
        for slot, name in enumerate(names):
            for value in bad[name]:
                trial = args[:slot] + (value,) + args[slot+1:]
                shown = repr(value)
                label = ("invalid " + title + "(" + name + "="
                         + (shown if len(shown) <= 24 else shown[:21] + "...") + ")")
                try:
                    function(*_fresh(trial))
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
        calls.setdefault(title, 0)
    summary = []
    for name, labels in missing.items():
        if calls.get(name, 0) and len(labels) < calls[name]:
            summary.append(name + ": raised NotImplementedError in " + str(len(labels))
                           + " valid checks (first: " + labels[0] + "); finish it")
        else:
            summary.append(name + ": not implemented yet (raises NotImplementedError)")
    return summary + failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual Episode QA and imitation baseline self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
