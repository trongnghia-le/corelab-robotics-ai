"""CoreLab Belief and task-reasoning lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I, cognition certification
or robot permission. SYMBOLIC TOY: exact enumeration of a few possible worlds.
Implement the six functions below, then run your edited file locally:
  Windows: py -3 L22-reasoning.v1.py
  macOS/Linux: python3 L22-reasoning.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared toy (numerical/symbolic practice, not perception, language or a robot):
a robot must fetch a hidden key from one of a few boxes. Everything is a finite
set of text facts, so you can enumerate every possible world and check a plan
against all of them.
  fact   a str of the form name(arg) or name(arg,arg,...): lowercase ASCII,
         the name and every argument start with a letter and use letters,
         digits and "_", no spaces, at most 40 characters in all. Examples: at(home), in(key,box_a). The
         arguments are the OBJECTS the fact talks about (home, key, box_a).
  world  (or state) a list/tuple of 0 to 20 distinct facts that are TRUE; every
         other fact is false (closed world). Order carries no meaning.
  belief a list/tuple of 1 to 16 worlds that are pairwise DIFFERENT as sets of
         facts. The robot believes the real world is one of them and cannot tell
         which; each is a possible hidden state. weights (when given) is a
         parallel list/tuple of finite positive int/float (never bool), each
         at most 1e6, one per world; probability = weight / sum of weights.
  actions a dict: action name (a str: a lowercase letter then lowercase letters,
         digits or "_", at most 40 characters; at most 24 actions) ->
         a spec dict. Every entry is validated, including entries the plan never uses. An ordinary action has exactly the keys "pre", "add" and
         "del" (each a list/tuple of 0 to 6 distinct facts): it needs every pre
         fact true, then deletes the "del" facts and THEN adds the "add" facts
         (a fact in both ends up true). A sensing action has exactly the keys
         "pre" and "sense" (one fact): it needs every pre fact true, changes
         nothing, and tells the robot whether the sense fact is true.
  plan   a finite tree of nested lists/tuples (at most 64 nodes in total):
           ["stop"]                                 end of the plan
           ["do", name, rest]                       ordinary action, then rest
           ["sense", name, if_true, if_false]       sensing action; continue in
                                                    if_true when its sense fact
                                                    is true in the CURRENT world,
                                                    else in if_false
         "do" must name an ordinary action and "sense" a sensing action.
  goal   a list/tuple of 1 to 6 distinct facts that must all be true at "stop".
Running a plan in one world: start at the root and track the current world. At a
"do" or "sense" node, if any pre fact is false in the current world the plan
FAILS there with reason "precondition" (nothing after it runs); otherwise a "do"
applies its effects, a "sense" branches. At ["stop"] the plan succeeds when every
goal fact is true, else FAILS with reason "goal". A plan is correct for a belief
only if it succeeds in EVERY world of the belief; a world where it fails is a
COUNTEREXAMPLE: a hidden state the plan did not account for.

Contracts (any wrong type, shape, bound or fact syntax raises ValueError; a plan
or table that is shaped right but names an action missing from the table also
raises ValueError, except in ungrounded; never mutate arguments):
  apply_action(state, pre, add, dele) -> tuple of str, or None
      One STRIPS step on one state (state, pre, add and dele are lists/tuples of
      facts as above; dele is the "del" list). None when some pre fact is false
      in state; otherwise the tuple of facts (state minus dele) plus add, sorted
      in ordinary string order, with no duplicates. EXACT.
  update_belief(belief, fact, observed) -> list of tuples of str
      The robot senses whether `fact` is true; observed is a bool (the True and
      False objects only). Keep exactly the worlds where (fact in world) equals
      observed, in their ORIGINAL order, each returned as a sorted tuple of
      facts. The result is [] when the observation contradicts every world
      (the model is falsified, which is a report, not an error). EXACT.
  posterior(belief, weights, fact, observed) -> list of float
      The same filtering, but return the probability of each surviving world, in
      belief order: weight / sum of the surviving weights, so the list sums to 1.
      [] when no world survives. Tolerance 1e-9.
  plan_failures(belief, plan, actions, goal) -> list of (index, reason)
      One pair per world where the plan fails, in belief order: index is the int
      position of the world in belief and reason is "precondition" or "goal"
      (see above). [] means the plan achieves the goal in every possible world.
      EXACT.
  success_probability(belief, weights, plan, actions, goal) -> float
      The total weight of the worlds where the plan succeeds divided by the
      total weight of all worlds, in [0, 1]. Tolerance 1e-9. (Only 1.0 means
      the plan is correct; a high number is not a guarantee.)
  ungrounded(belief, plan, actions) -> (missing_actions, missing_objects)
      Groundedness. Both are sorted tuples of unique str.
        missing_actions: every action name used in some node of the plan (all
          branches, reachable or not) that is not a key of actions. For this
          function only, a missing name is not an error; the other checks above
          (shape, kinds of the known names) still apply.
        missing_objects: every object (fact argument) that occurs in a pre, add,
          del or sense fact of a USED action that exists in actions, and that
          occurs in no fact of any world of belief. Actions in the table that
          the plan never uses are ignored. The goal is not examined here.
      A plan can be perfectly "logical" and still talk about a cabinet that is
      not there; grounding is a separate check from feasibility.
Bounds: lists/tuples must contain only the types stated; bool, float and other
ints are never accepted where an int or str is required; NaN and infinity are
invalid. Return exactly the types named (lists or tuples are both fine for the
sequences). Never mutate inputs.

Pause before coding - write your predictions down first:
  1. Three equally likely boxes, you look in the first and it is empty: which
     worlds remain, what are their probabilities, and does the answer depend on
     whether you say "not found" or "empty"?
  2. A plan that opens box_a and grabs from it: in how many of three worlds does
     it succeed, and why is "it works if the key is in box_a" not enough?
  3. A box turns out to be locked in one world and the plan opens it: which of
     the two failure reasons do you get, and which hidden state is the
     counterexample you would hand to the planner?
  4. A plan proposes open_cabinet but no fact mentions a cabinet: is it
     infeasible, ungrounded, or both, and what does your check report?
  5. After a sensing action in a world where the fact is true, is the world
     itself changed? What changes about the robot's belief?
Self-check tolerances are exact except where stated. Failure messages name the
case and the kind of mismatch, never the expected values. "your code raised X"
means your function raised on a VALID input.
This does not implement perception, natural-language understanding, an LLM or
VLM, probabilistic sensor noise, continuous motion or task planning, a
simulator, or any cognition or robot-safety certification. Reflection: why does
passing this toy NOT show that a real robot reasons correctly about its task?
(Think about noisy and wrong perception, objects that are named but not really
there, hidden states too numerous to list, actions that fail unpredictably,
geometry and timing, plans written in free text that a human must interpret,
and who reviews an unfamiliar plan before it moves anything.)
"""
import math


def apply_action(state, pre, add, dele):
    raise NotImplementedError("Check every pre fact, delete first, then add; return sorted facts or None")


def update_belief(belief, fact, observed):
    raise NotImplementedError("Keep the worlds that agree with the observation, in their original order")


def posterior(belief, weights, fact, observed):
    raise NotImplementedError("Filter, then divide each surviving weight by the surviving total")


def plan_failures(belief, plan, actions, goal):
    raise NotImplementedError("Run the plan tree in every world; sensing branches on the current world")


def success_probability(belief, weights, plan, actions, goal):
    raise NotImplementedError("Weight of the worlds where the plan succeeds over the total weight")


def ungrounded(belief, plan, actions):
    raise NotImplementedError("Collect used action names and objects that the belief does not contain")


# ---- SPOILER BELOW: the _o_* functions are complete references and the case ----
# ---- tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _o_apply(state, pre, add, dele):
    s = set(state)
    if not set(pre) <= s:
        return None
    return tuple(sorted((s - set(dele)) | set(add)))


def _o_update(belief, fact, observed):
    return [tuple(sorted(w)) for w in belief if (fact in w) == observed]


def _o_posterior(belief, weights, fact, observed):
    kept = [x for w, x in zip(belief, weights) if (fact in w) == observed]
    total = sum(kept)
    return [x/total for x in kept] if kept else []


def _o_run(world, plan, actions, goal):
    w, node = set(world), plan
    while True:
        if node[0] == "stop":
            return None if set(goal) <= w else "goal"
        spec = actions[node[1]]
        if not set(spec["pre"]) <= w:
            return "precondition"
        if node[0] == "do":
            w = (w - set(spec["del"])) | set(spec["add"])
            node = node[2]
        else:
            node = node[2] if spec["sense"] in w else node[3]


def _o_failures(belief, plan, actions, goal):
    out = []
    for i, world in enumerate(belief):
        reason = _o_run(world, plan, actions, goal)
        if reason:
            out.append((i, reason))
    return out


def _o_success(belief, weights, plan, actions, goal):
    failed = {i for i, _ in _o_failures(belief, plan, actions, goal)}
    return sum(x for i, x in enumerate(weights) if i not in failed)/sum(weights)


def _o_objects(fact):
    return fact[fact.index("(") + 1:-1].split(",")


def _o_ungrounded(belief, plan, actions):
    known = {o for w in belief for f in w for o in _o_objects(f)}
    used, stack = [], [plan]
    while stack:
        node = stack.pop()
        if node[0] == "stop":
            continue
        used.append(node[1])
        stack.extend(node[2:])
    missing = sorted({n for n in used if n not in actions})
    objects = set()
    for name in set(used):
        spec = actions.get(name)
        if spec is None:
            continue
        for f in (list(spec["pre"]) + list(spec.get("add", ())) + list(spec.get("del", ()))
                  + ([spec["sense"]] if "sense" in spec else [])):
            objects.update(_o_objects(f))
    return (tuple(missing), tuple(sorted(objects - known)))


def _domain(boxes, lockable=()):
    """Box-fetch action table: goto_X, open_X, look_X (senses in(key,X)), grab_X, goto_home, deliver."""
    table = {
        "goto_home": {"pre": [], "add": ["at(home)"], "del": ["at(" + b + ")" for b in boxes]},
        "deliver": {"pre": ["at(home)", "holding(key)"], "add": ["delivered(key)"],
                    "del": ["holding(key)"]},
    }
    for b in boxes:
        table["goto_" + b] = {"pre": [], "add": ["at(" + b + ")"],
                              "del": ["at(home)"] + ["at(" + o + ")" for o in boxes if o != b]}
        table["open_" + b] = {"pre": ["at(" + b + ")", "closed(" + b + ")"]
                              + (["unlocked(" + b + ")"] if b in lockable else []),
                              "add": ["open(" + b + ")"], "del": ["closed(" + b + ")"]}
        table["look_" + b] = {"pre": ["at(" + b + ")", "open(" + b + ")"],
                              "sense": "in(key," + b + ")"}
        table["grab_" + b] = {"pre": ["at(" + b + ")", "open(" + b + ")", "in(key," + b + ")"],
                              "add": ["holding(key)"], "del": ["in(key," + b + ")"]}
    return table


def _belief(boxes, lockable=()):
    """Every (key box, lock state) world, key box varying slowest; sorted fact tuples."""
    worlds = []
    for where in boxes:
        for mask in range(2**len(lockable)):
            facts = ["at(home)", "in(key," + where + ")"] + ["closed(" + b + ")" for b in boxes]
            facts += ["unlocked(" + b + ")" for k, b in enumerate(lockable) if mask >> k & 1]
            worlds.append(tuple(sorted(facts)))
    return worlds


def _fetch(b):
    return ["do", "grab_" + b, ["do", "goto_home", ["do", "deliver", ["stop"]]]]


def _blind(b):
    return ["do", "goto_" + b, ["do", "open_" + b, _fetch(b)]]


def _search(order, last_look=False, swap=False):
    """Sensing search: go to a box, open it, look; fetch if found, else search the rest."""
    b, rest = order[0], order[1:]
    if not rest and not last_look:
        return _blind(b)
    if rest:
        no = _search(rest, last_look, swap)
    else:
        no = ["stop"]
    yes, no = (no, _fetch(b)) if swap else (_fetch(b), no)
    return ["do", "goto_" + b, ["do", "open_" + b, ["sense", "look_" + b, yes, no]]]


def _trunc(order):
    """Like _search but the last box is neither opened nor searched: the plan just stops."""
    b, rest = order[0], order[1:]
    if not rest:
        return ["stop"]
    return ["do", "goto_" + b, ["do", "open_" + b, ["sense", "look_" + b, _fetch(b), _trunc(rest)]]]


def seq_n(count):
    """A plan of exactly count + 1 nodes: count do-nodes then stop (64 nodes is the largest valid plan)."""
    node = ["stop"]
    for _ in range(count):
        node = ["do", "goto_box_a", node]
    return node


_ABC = ["box_a", "box_b", "box_c"]
_W3 = _belief(_ABC)
_GOAL = ["delivered(key)"]
_ACT3 = _domain(_ABC)
_AB = ["box_a", "box_b"]
_W4 = _belief(_AB, ("box_a",))
_ACT4 = _domain(_AB, ("box_a",))
_TOGGLE = {"toggle": {"pre": [], "add": ["lit(lamp)"], "del": ["lit(lamp)"]},
           "clear": {"pre": [], "add": [], "del": ["lit(lamp)"]},
           "on": {"pre": [], "add": ["lit(lamp)"], "del": []},
           "probe": {"pre": [], "sense": "lit(lamp)"}}

# apply_action(state, pre, add, dele) -> tuple or None: hand-derived.
_APPLY_CASES = [
    ((["at(home)", "holding(cup)"], ["at(home)", "holding(cup)"], ["placed(cup)"], ["holding(cup)"]),
     ("at(home)", "placed(cup)")),
    ((["at(home)"], ["at(home)", "holding(cup)"], ["placed(cup)"], []), None),
    ((["a(x)", "b(x)"], [], ["a(x)"], ["a(x)"]), ("a(x)", "b(x)")),
    ((["a(x)"], [], ["b(x)"], ["c(x)"]), ("a(x)", "b(x)")),
    ((["z(x)", "m(x)"], ["m(x)"], ["a(x)"], []), ("a(x)", "m(x)", "z(x)")),
    ((["a(x)"], ["a(x)"], ["a(x)"], []), ("a(x)",)),
    ((("at(home)",), (), ("at(shelf)",), ("at(home)",)), ("at(shelf)",)),
    ((["p(x)"], ["p(x)"], [], ["p(x)"]), ()),
]
# update_belief(belief, fact, observed) -> list of sorted tuples, original order.
_UPDATE_CASES = [
    ((_W3, "in(key,box_a)", False), [_W3[1], _W3[2]]),
    ((_W3, "in(key,box_a)", True), [_W3[0]]),
    ((_W3, "in(key,box_d)", True), []),
    ((tuple(_W3), "in(key,box_d)", False), _W3),
    ((_W3, "at(home)", False), []),
    (([_W3[2], _W3[0], _W3[1]], "in(key,box_b)", False), [_W3[2], _W3[0]]),
    (([["in(key,box_b)", "at(home)"], ["at(home)", "in(key,box_a)"]], "in(key,box_a)", False),
     [("at(home)", "in(key,box_b)")]),
    ((_W4, "unlocked(box_a)", True), [_W4[1], _W4[3]]),
]
# posterior(belief, weights, fact, observed) -> probabilities of the survivors.
_POSTERIOR_CASES = [
    ((_W3, [1, 1, 1], "in(key,box_a)", False), [0.5, 0.5]),
    ((_W3, [5, 3, 2], "in(key,box_c)", False), [0.625, 0.375]),
    ((_W3, [1, 1, 1], "in(key,box_d)", True), []),
    ((_W3, [0.5, 1.5, 2.0], "in(key,box_b)", False), [0.2, 0.8]),
    ((_W4, [1, 2, 3, 4], "in(key,box_a)", False), [3/7, 4/7]),
    ((_W4, [1, 2, 3, 4], "unlocked(box_a)", True), [1/3, 2/3]),
]
# plan_failures(belief, plan, actions, goal) -> [(index, reason)].
_FAIL_CASES = [
    ((_W3, _blind("box_a"), _ACT3, _GOAL), [(1, "precondition"), (2, "precondition")]),
    ((_W3, _search(_ABC), _ACT3, _GOAL), []),
    ((_W3, _trunc(_ABC), _ACT3, _GOAL), [(2, "goal")]),
    ((_W3, ("stop",), _ACT3, _GOAL), [(0, "goal"), (1, "goal"), (2, "goal")]),
    ((_W3, ["do", "goto_box_a", ["do", "grab_box_a", ["stop"]]], _ACT3, _GOAL),
     [(0, "precondition"), (1, "precondition"), (2, "precondition")]),
    ((_W4, ["do", "goto_box_a", ["do", "open_box_a", ["do", "grab_box_a", ["stop"]]]], _ACT4, _GOAL),
     [(0, "precondition"), (1, "goal"), (2, "precondition"), (3, "precondition")]),
    ((_W3, ["do", "goto_box_a", ["sense", "look_box_a", ["stop"], ["stop"]]], _ACT3, _GOAL),
     [(0, "precondition"), (1, "precondition"), (2, "precondition")]),
    ((_W3, _search(_ABC), _ACT3, ["delivered(key)", "open(box_c)"]), [(0, "goal"), (1, "goal")]),
    ((_W3[:2], _search(_AB, swap=True), _ACT3, _GOAL), [(0, "precondition"), (1, "precondition")]),
    ((_W4, _search(_AB), _ACT4, _GOAL), [(0, "precondition"), (2, "precondition")]),
    (([("a(x)",), ("b(x)",)], ["do", "toggle", ["stop"]], _TOGGLE, ["lit(lamp)"]), []),
    (([("a(x)",)], ["do", "toggle", ["do", "clear", ["stop"]]], _TOGGLE, ["lit(lamp)"]), [(0, "goal")]),
    ((_W3, seq_n(63), _ACT3, _GOAL), [(0, "goal"), (1, "goal"), (2, "goal")]),
    (([("a(x)",)], ["do", "on", ["sense", "probe", ["stop"], ["do", "clear", ["stop"]]]], _TOGGLE,
      ["lit(lamp)"]), []),
]
# success_probability(belief, weights, plan, actions, goal) -> float.
_SUCCESS_CASES = [
    ((_W3, [5, 3, 2], _blind("box_a"), _ACT3, _GOAL), 0.5),
    ((_W3, [5, 3, 2], _search(_ABC), _ACT3, _GOAL), 1.0),
    ((_W3, [1, 1, 2], _trunc(_ABC), _ACT3, _GOAL), 0.5),
    ((_W3, [1, 2, 3], ["stop"], _ACT3, _GOAL), 0.0),
    ((_W4, [1, 2, 3, 4], _blind("box_b"), _ACT4, _GOAL), 0.7),
    ((_W3, [0.5, 0.25, 0.25], _blind("box_b"), _ACT3, _GOAL), 0.25),
    ((_W4, [3, 1, 1, 3], _search(_AB), _ACT4, _GOAL), 0.5),
]
# ungrounded(belief, plan, actions) -> (missing actions, missing objects).
_GHOST = {
    "open_cabinet": {"pre": ["at(cabinet)", "closed(cabinet)"], "add": ["open(cabinet)"],
                     "del": ["closed(cabinet)"]},
    "look_tray": {"pre": ["at(box_a)"], "sense": "in(key,tray)"},
    "wipe": {"pre": ["holding(key)", "have(cloth)"], "add": ["clean(key)"], "del": []},
}
_UNGROUNDED_CASES = [
    ((_W3, _search(_ABC), _ACT3), ((), ())),
    ((_W3, ["do", "open_cabinet", ["stop"]], _ACT3), (("open_cabinet",), ())),
    ((_W3, ["do", "open_cabinet", ["stop"]], dict(_ACT3, **_GHOST)), ((), ("cabinet",))),
    ((_W3, _blind("box_a"), dict(_ACT3, **_GHOST)), ((), ())),
    ((_W3, ["do", "goto_box_a", ["sense", "look_tray", ["stop"], ["do", "wipe", ["stop"]]]],
      dict(_ACT3, **_GHOST)), ((), ("cloth", "tray"))),
    ((_W3, ["do", "zip", ["do", "alpha", ["do", "zip", ["do", "wipe", ["do", "open_cabinet", ["stop"]]]]]],
      dict(_ACT3, **_GHOST)), (("alpha", "zip"), ("cabinet", "cloth"))),
    (([("at(home)",), ("at(home)", "in(key,box_a)")], ["do", "goto_box_a", ["stop"]], _ACT3),
     ((), ("box_b", "box_c"))),
]


def _copy(value, depth=0):
    if depth > 100:
        return value
    if isinstance(value, dict):
        return {k: _copy(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [_copy(v, depth + 1) for v in value]
    if isinstance(value, tuple):
        return tuple(_copy(v, depth + 1) for v in value)
    return value


def _sequence_of_str(got):
    return isinstance(got, (list, tuple)) and all(type(x) is str for x in got)


def self_check():
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    counts = {}
    unimplemented = set()

    def note(name, text):
        counts[name] = counts.get(name, 0) + 1
        if counts[name] <= 5:
            failures.append(text)

    def run(label, name, function, args, compare):
        before = repr(args)
        try:
            got = function(*args)
            if repr(args) != before:
                raise _Mismatch("an input argument was mutated")
            compare(got)
        except _Mismatch as error:
            note(name, label + ": " + str(error))
        except NotImplementedError:
            if name not in unimplemented:
                unimplemented.add(name)
                failures.append(name + ": not implemented yet")
        except Exception as error:
            note(name, label + ": your code raised " + type(error).__name__
                 + " on a valid input")

    def want_worlds(got, expected):
        if not isinstance(got, (list, tuple)) or not all(
                isinstance(w, (list, tuple)) and all(type(f) is str for f in w) for w in got):
            raise _Mismatch("output must be a list/tuple of worlds, each a list/tuple of str")
        if [tuple(w) for w in got] != [tuple(w) for w in expected]:
            raise _Mismatch("surviving worlds, their order or their sorted facts are wrong")

    def want_pairs(got, expected):
        if not isinstance(got, (list, tuple)) or not all(
                isinstance(p, (list, tuple)) and len(p) == 2 and type(p[0]) is int
                and type(p[1]) is str for p in got):
            raise _Mismatch("output must be a list/tuple of (int index, str reason) pairs")
        if [p[0] for p in got] != [p[0] for p in expected]:
            raise _Mismatch("the set of failing worlds (or its order) is wrong")
        if [p[1] for p in got] != [p[1] for p in expected]:
            raise _Mismatch("failure reasons (precondition versus goal) are wrong")

    def want_floats(got, expected):
        if not isinstance(got, (list, tuple)) or not all(_real(x) for x in got):
            raise _Mismatch("output must be a list/tuple of finite int/float")
        if len(got) != len(expected):
            raise _Mismatch("wrong number of probabilities (one per surviving world)")
        for a, b in zip(got, expected):
            if abs(a - b) > 1e-9:
                raise _Mismatch("a probability is wrong (tolerance 1e-9)")

    def want_float(got, expected):
        if not _real(got):
            raise _Mismatch("output must be a finite int/float")
        if abs(got - expected) > 1e-9:
            raise _Mismatch("probability is wrong (tolerance 1e-9)")

    def want_ungrounded(got, expected):
        if (not isinstance(got, (list, tuple)) or len(got) != 2
                or not all(_sequence_of_str(part) for part in got)):
            raise _Mismatch("output must be a pair (missing_actions, missing_objects) of str sequences")
        for part, want, what in ((got[0], expected[0], "missing_actions"),
                                 (got[1], expected[1], "missing_objects")):
            if tuple(part) != tuple(want):
                raise _Mismatch(what + " is wrong (sorted, unique, only what the plan uses?)")

    for i, (args, expected) in enumerate(_APPLY_CASES):
        def compare(got, expected=expected):
            if expected is None:
                if got is not None:
                    raise _Mismatch("should return None when a pre fact is false")
                return
            if got is None:
                raise _Mismatch("returned None although every pre fact holds")
            if not _sequence_of_str(got):
                raise _Mismatch("output must be a tuple of str")
            if tuple(got) != expected:
                raise _Mismatch("resulting facts are wrong (delete first then add; sorted, no duplicates)")
        run("apply_action " + str(i), "apply_action", apply_action, _copy(args), compare)

    for i, (args, expected) in enumerate(_UPDATE_CASES):
        run("update_belief " + str(i), "update_belief", update_belief, _copy(args),
            lambda got, expected=expected: want_worlds(got, expected))

    for i, (args, expected) in enumerate(_POSTERIOR_CASES):
        run("posterior " + str(i), "posterior", posterior, _copy(args),
            lambda got, expected=expected: want_floats(got, expected))

    for i, (args, expected) in enumerate(_FAIL_CASES):
        run("plan_failures " + str(i), "plan_failures", plan_failures, _copy(args),
            lambda got, expected=expected: want_pairs(got, expected))

    for i, (args, expected) in enumerate(_SUCCESS_CASES):
        run("success_probability " + str(i), "success_probability", success_probability,
            _copy(args), lambda got, expected=expected: want_float(got, expected))

    for i, (args, expected) in enumerate(_UNGROUNDED_CASES):
        run("ungrounded " + str(i), "ungrounded", ungrounded, _copy(args),
            lambda got, expected=expected: want_ungrounded(got, expected))

    # Sweep over generated box-fetch domains: every blind plan, search order and
    # a truncated or branch-swapped search, checked against the exact enumeration.
    n = 0
    for boxes, lockable in ((_AB, ()), (_AB, ("box_a",)), (_ABC, ()), (_ABC, ("box_b",))):
        belief = _belief(boxes, lockable)
        table = _domain(boxes, lockable)
        weights = [k + 1 for k in range(len(belief))]
        order_sets = [list(boxes), list(reversed(boxes)), boxes[1:] + boxes[:1]]
        plans = [_blind(b) for b in boxes]
        plans += [_search(o) for o in order_sets] + [_search(o, True) for o in order_sets[:2]]
        plans += [_trunc(o) for o in order_sets[:2]] + [_search(order_sets[0], False, True)]
        plans += [["do", "open_" + boxes[0], ["stop"]]]
        for plan in plans:
            n += 1
            args = (belief, plan, table, _GOAL)
            run("plan_failures sweep " + str(n), "plan_failures", plan_failures, _copy(args),
                lambda got, args=args: want_pairs(got, _o_failures(*args)))
            args2 = (belief, weights, plan, table, _GOAL)
            run("success_probability sweep " + str(n), "success_probability",
                success_probability, _copy(args2),
                lambda got, args2=args2: want_float(got, _o_success(*args2)))
        for b in boxes:
            for observed in (True, False):
                fact = "in(key," + b + ")"
                run("update_belief sweep " + str(n), "update_belief", update_belief,
                    _copy((belief, fact, observed)),
                    lambda got, a=(belief, fact, observed): want_worlds(got, _o_update(*a)))
                run("posterior sweep " + str(n), "posterior", posterior,
                    _copy((belief, weights, fact, observed)),
                    lambda got, a=(belief, weights, fact, observed): want_floats(got, _o_posterior(*a)))
        ghost_plan = ["do", "open_cabinet", ["do", "wipe", _search(boxes)]]
        for extra in (_GHOST, {}):
            full = dict(table, **extra)
            run("ungrounded sweep " + str(n), "ungrounded", ungrounded,
                _copy((belief, ghost_plan, full)),
                lambda got, a=(belief, ghost_plan, full): want_ungrounded(got, _o_ungrounded(*a)))

    # Invalid inputs: each must raise ValueError (never return, never another error).
    ok_belief = [list(_W3[0]), list(_W3[1])]
    ok_plan = ["do", "goto_box_a", ["stop"]]
    ok_actions = {"goto_box_a": {"pre": [], "add": ["at(box_a)"], "del": ["at(home)"]},
                  "look_box_a": {"pre": ["at(box_a)"], "sense": "in(key,box_a)"}}
    ok_goal = ["at(box_a)"]
    nan, inf = float("nan"), float("inf")
    def cyclic():
        loop = ["do", "goto_box_a", None]
        loop[2] = loop
        return loop
    deep = seq_n(65)
    deep65 = seq_n(64)

    def many(count):
        return ["f" + str(k) + "(x)" for k in range(count)]
    bad_facts = ["", "At(home)", "at()", "at(home", "home", "at(Home)", "at(h-1)",
                 "at( home)", "at(home)\n", "at(caf\u00e9)", "1at(x)", "a(x,)", "a(,x)",
                 "a(" + "x"*40 + ")", None, 5, True]
    bad_lists = [None, "at(home)", {"at(home)"}, [1], [True], [None], [["at(home)"]],
                 ["at(home)", "at(home)"]] + [[f] for f in bad_facts]
    bad_world_lists = bad_lists + [many(21)]
    bad_small_lists = bad_lists + [many(7)]
    bad_beliefs = [None, [], (), "abc", [None], ["at(home)"], [["bad"]], [["a(x)"], ["a(x)"]],
                   [["a(x)", "b(x)"], ["b(x)", "a(x)"]], [["a(x)", "a(x)"]],
                   [[f"w{k}(x)"] for k in range(17)], {"a(x)": 1}]
    bad_weights = [None, 5, "ab", [1], [1, 1, 1], [0, 1], [-1, 1], [nan, 1], [inf, 1],
                   [True, 1], ["1", 1], [None, 1], [1e6 + 1, 1], [1, -inf]]
    bad_observed = [1, 0, None, "True", "False", 2.0, [True]]
    bad_plans = [None, [], "stop", ["jump"], ["stop", "x"], ["do"], ["do", "goto_box_a"],
                 ["do", "goto_box_a", ["stop"], ["stop"]], ["do", 5, ["stop"]],
                 ["do", "goto_box_a", None], ["do", "look_box_a", ["stop"]],
                 ["sense", "goto_box_a", ["stop"], ["stop"]], ["sense", "look_box_a", ["stop"]],
                 ["sense", "look_box_a", ["stop"], ["stop"], ["stop"]], ["Stop"], 7,
                 {"stop": 1}, cyclic, deep, deep65, ["do", ["goto_box_a"], ["stop"]]]
    bad_actions = [None, [], "x", {"Go": {"pre": [], "add": [], "del": []}},
                   {"1go": {"pre": [], "add": [], "del": []}},
                   {"go": []}, {"go": {"pre": []}}, {"go": {"pre": [], "add": []}},
                   {"go": {"pre": [], "add": [], "del": [], "sense": "a(x)"}},
                   {"go": {"pre": [], "sense": "bad"}}, {"go": {"pre": [], "sense": ["a(x)"]}},
                   {"go": {"pre": ["bad"], "add": [], "del": []}},
                   {"go": {"pre": [], "add": [many(1)[0], many(1)[0]], "del": []}},
                   {"go": {"pre": [], "add": many(7), "del": []}},
                   {"go": {"pre": [], "add": [], "del": [], "extra": []}},
                   {"go": {"pre": [], "sense": "a(x)", "extra": 1}},
                   {5: {"pre": [], "add": [], "del": []}},
                   {("g" + str(k)): {"pre": [], "add": [], "del": []} for k in range(25)}]
    bad_goals = [None, [], (), "delivered(key)", ["bad"], ["a(x)", "a(x)"], many(7), [1], [None]]

    def cases(title, function, names, base, slots):
        for slot, values in slots:
            for value in values:
                trial = list(base)
                shown = "a self-referencing plan" if callable(value) else repr(value)
                trial[slot] = _copy(value() if callable(value) else value)
                label = ("invalid " + title + "(" + names[slot] + "="
                         + (shown if len(shown) <= 22 else shown[:19] + "...") + ")")
                try:
                    function(*_copy(trial))
                except ValueError:
                    continue
                except NotImplementedError:
                    if title not in unimplemented:
                        unimplemented.add(title)
                        failures.append(title + ": not implemented yet")
                    return
                except Exception as error:
                    note("invalid " + title, label + ": raised " + type(error).__name__
                         + " instead of ValueError")
                    continue
                note("invalid " + title, label + ": returned instead of raising ValueError")

    cases("apply_action", apply_action, ("state", "pre", "add", "dele"),
          (["at(home)"], ["at(home)"], ["b(x)"], []),
          [(0, bad_world_lists), (1, bad_small_lists), (2, bad_small_lists), (3, bad_small_lists)])
    cases("update_belief", update_belief, ("belief", "fact", "observed"),
          (ok_belief, "in(key,box_a)", True),
          [(0, bad_beliefs), (1, bad_facts), (2, bad_observed)])
    cases("posterior", posterior, ("belief", "weights", "fact", "observed"),
          (ok_belief, [1, 1], "in(key,box_a)", True),
          [(0, bad_beliefs), (1, bad_weights), (2, bad_facts), (3, bad_observed)])
    cases("plan_failures", plan_failures, ("belief", "plan", "actions", "goal"),
          (ok_belief, ok_plan, ok_actions, ok_goal),
          [(0, bad_beliefs), (1, bad_plans + [["do", "no_such_action", ["stop"]]]),
           (2, bad_actions), (3, bad_goals)])
    cases("success_probability", success_probability,
          ("belief", "weights", "plan", "actions", "goal"),
          (ok_belief, [1, 1], ok_plan, ok_actions, ok_goal),
          [(0, bad_beliefs), (1, bad_weights), (2, bad_plans + [["do", "no_such_action", ["stop"]]]),
           (3, bad_actions), (4, bad_goals)])
    cases("ungrounded", ungrounded, ("belief", "plan", "actions"),
          (ok_belief, ok_plan, ok_actions),
          [(0, bad_beliefs), (1, bad_plans), (2, bad_actions)])
    for name, seen in sorted(counts.items()):
        if seen > 5:
            failures.append(name + ": " + str(seen - 5) + " more failure(s) of this kind not listed")
    return failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual belief-and-reasoning self-check - practice only, no cognition certification")
    if failures:
        print(str(len(failures)) + " line(s) of failures:")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
