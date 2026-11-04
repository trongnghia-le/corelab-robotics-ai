---
{
  "id": "cap07-capstone",
  "module_id": "CAP07",
  "title": "Capstone milestone 7: a language-goal task layer and a safety supervisor with hazard injection tests",
  "summary": "Parse text instructions into symbolic goals with explicit ambiguity handling, plan and execute with a behaviour tree, keep an object belief, and build an independent safety supervisor for the simulation that is tested by injecting ten hazards.",
  "estimated_minutes": 1560,
  "project_minutes": 1560,
  "prerequisites": [
    "CAP04",
    "CAP05",
    "E05",
    "E06",
    "S07"
  ],
  "source_refs": [
    {
      "title": "BehaviorTree.CPP documentation",
      "url": "https://www.behaviortree.dev/"
    },
    {
      "title": "py_trees (behaviour trees in Python)",
      "url": "https://github.com/splintered-reality/py_trees"
    },
    {
      "title": "Colledanchise and Ogren, Behavior Trees in Robotics and AI",
      "url": "https://arxiv.org/abs/1709.00084"
    },
    {
      "title": "Ahn et al., Do As I Can, Not As I Say (SayCan)",
      "url": "https://arxiv.org/abs/2204.01691"
    },
    {
      "title": "Liang et al., Code as Policies",
      "url": "https://arxiv.org/abs/2209.07753"
    },
    {
      "title": "STRIPS (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/STRIPS"
    },
    {
      "title": "Failure mode and effects analysis (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Failure_mode_and_effects_analysis"
    }
  ],
  "objectives": [
    "Parse instructions into symbolic goals and return Clarify or Unparseable instead of guessing.",
    "Plan multi-step tasks with a bounded search and execute them with a behaviour tree with retries and fallbacks.",
    "Maintain an object belief with age and confidence and avoid planning on stale data.",
    "Write a hazard table and implement a safety supervisor independent of the planning stack.",
    "Verify the supervisor with hazard injection tests and state that it protects a simulation and is not certified safety."
  ],
  "core_theory": [
    "E05",
    "E06",
    "S07",
    "CAP04",
    "CAP05"
  ],
  "labs": [
    "Build the LLM-free parser, a STRIPS-style planner and a behaviour tree, then a supervisor with ten injected hazards, and pass the CAP07 acceptance suite."
  ],
  "assessment_refs": [
    "CAP07-diagnostic-v1"
  ],
  "review_prompts": [
    "Explain why the supervisor must not run in the same thread as the planner it supervises.",
    "Show the parser's response to an ambiguous instruction and say why guessing would be worse than asking."
  ],
  "extension_refs": [
    "https://arxiv.org/abs/2406.09246",
    "https://github.com/splintered-reality/py_trees"
  ]
}
---

## Why this matters

By CAP06 your robot can navigate, perceive and grasp. What it cannot do yet is take an instruction from a person, decide what to do and in which order, recover when a step fails, and, above all, **stop** when something is wrong. This milestone adds those three layers: a task layer that turns text into a goal, a planner and behaviour tree that turn the goal into actions, and a safety supervisor that sits beside everything else and can veto it.

Two lessons from real systems drive the design. First, a language interface is mostly a *disambiguation* problem: the dangerous failure is not "the parser did not understand", it is "the parser silently picked the wrong object and the robot happily executed it". Second, a safety function is only worth something if it does not depend on the component it protects against: a supervisor that shares a thread with a hung planner is not a supervisor.

**An honest limit, stated up front.** The supervisor you build protects a *simulation*. It is a teaching exercise in hazard analysis and fault injection. It is **not certified safety**, makes no claim to meet any functional safety standard (real systems follow standards such as ISO 13849 or IEC 61508 with certified hardware, independent assessment and far more rigour), and must never be the only protection of a real machine near people. The optional hardware tier at the end follows the electrical rules of HW03 and keeps all power limits low.

This is milestone 7 of 9, worth **10 of 100 points**. It uses [CAP04](/lessons/CAP04) (navigation skill), [CAP05](/lessons/CAP05) (grasp skill), [E05 Task planning](/lessons/E05), [E06 Task and motion planning](/lessons/E06) and [S07 Robot safety](/lessons/S07).

## Intuition

Picture the stack as three nested loops running at very different speeds. The **task loop** (seconds): read an instruction, ask a clarifying question if needed, plan, run the tree, retry or give up. The **skill loops** (tens of milliseconds): navigation and grasp, which you already built. The **safety loop** (10 ms): look at heartbeats and hazard signals and decide whether any command is allowed through.

![System architecture of CoreBot Tidy: simulator, firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation and learned skills, the language task layer and the safety supervisor](/lesson-figures/CAP-architecture.svg)

*The task layer is the top band; the dashed red bar on the right is the supervisor. Notice that it has inputs from every band and a direct line to the firmware watchdog that bypasses the planner.*

The parser has three possible answers, never two: a **goal** (understood, unambiguous), a **Clarify** (understood but under-specified: "which block?"), or **Unparseable** (outside the grammar, unsafe, or contradicting the scene). A system with only goal and error will guess; a system that can ask is safer and, with a small vocabulary, easier to build.

![Language task layer and independent safety supervisor: text to parser to goal to planner to behaviour tree to skills, with Clarify and Unparseable branches, and a supervisor process that reads hazard inputs and can force zero velocity, arm hold and a direct firmware stop](/lesson-figures/CAP07.svg)

*Left to right, the task path. Underneath, the supervisor path, which does not pass through the planner.*

Three further ideas:

**The LLM-free baseline comes first.** A closed vocabulary (3 colours, 3 shapes, a few verbs, synonyms) with slot filling parses a tidy-up domain reliably and is fully testable. An LLM or a vision-language-action (VLA) model can be an *alternative* parser for the stretch goal, evaluated on the same 60 sentences; it cannot replace the supervisor, because a language model gives no guarantee about the actions it proposes.

**Plan symbolically, check geometrically.** A STRIPS-style planner reasons about `holding(obj)` and `on(obj, bin)`. Whether the arm can actually reach the object is geometry (your CAP05 IK). Task and motion planning (TAMP) joins the two: if the geometric check fails, the symbolic plan is repaired or the task aborts with a reason.

**A fault is a normal event.** Tests inject faults deliberately and measure the time until the robot is in a safe state. "Safe state" is concrete: forwarded velocity zero, arm holding position, firmware stopped.

## Theory and derivation

Integration notes: what matters here, with the topic it comes from.

![CAP07 milestone diagram: parser, planner, behaviour tree, skills and the independent safety supervisor](/lesson-figures/CAP07.svg)

### 1. A goal language and an honest parser ([E05](/lessons/E05))

The goal is a conjunction of predicates over a closed world, `TaskGoal(predicates=(on(cube_red, bin_blue), ...), source_text)`. The parser fills slots: *verb* (put/place/move/bring/carry/set/drop mean "put"; pick/grab/take/lift mean "pick"), *object phrases* (colour, shape or a generic noun such as block, object, thing, one), *destination* (preposition, optional colour, bin word). Resolution against the scene is where ambiguity appears:

| Matches in scene | Result |
|---|---|
| exactly 1 | slot resolved |
| 0 | `Unparseable("no such object")` |
| more than 1 | `Clarify(question, options)` |

Rules worth writing as tests: negation ("do not ...") and unknown colour words are `Unparseable`; more than two objects is `Unparseable` (a scope guard); a pronoun without an antecedent is `Clarify`; an unknown verb ("throw") is `Unparseable`. Report the limits of the grammar in the README; that is part of the "design honesty" rubric item.

### 2. STRIPS-style planning with a bounded search ([E05](/lessons/E05), [E06](/lessons/E06))

State: `(robot_at, holding, object locations)`. Actions and preconditions: `nav(loc)` (any location); `pick(obj)` requires `robot_at = table`, an empty gripper and the object on the table; `place(obj, bin)` requires `robot_at = bin` and the object in the gripper. Breadth-first search with a visited set returns a plan with the **minimum number of actions** and cannot loop; add an expansion cap so that an unreachable goal returns `None` in bounded time. For one object the minimum is 4 actions from a start away from the table (nav, pick, nav, place) and 3 if already at the table. Because the gripper holds one object, two objects into one bin need 8.

### 3. Behaviour trees ([E06](/lessons/E06), Colledanchise and Ogren)

A tree is ticked from the root. A **Sequence** returns failure at the first failing child; a **Fallback** (selector) returns success at the first succeeding child; a **Retry** decorator repeats a failing child up to $r$ times. If a skill succeeds with probability $p$ per attempt and attempts are independent, retries give
$$P(\text{success within } r+1\text{ tries})=1-(1-p)^{r+1},\qquad E[\text{calls}]=\sum_{k=0}^{r}(1-p)^k .$$
Independence is optimistic: a repeated failure usually has a common cause, which is why the rule is "at most two retries, then replan or abort with a reason". Always run the tree under a **tick bound** so that a bug cannot hang the task.

### 4. Object belief ([E06](/lessons/E06), CAP05)

`world_model.py` stores for each object a pose, a timestamp and a confidence. Define the **age** $a=t_{now}-t_{seen}$; before planning a pick, if $a$ exceeds a threshold (say 5 s) or confidence is low, the planner inserts an *observe* action first. Planning on a belief that is minutes old is the classic "stale object belief" failure.

### 5. The safety supervisor ([S07](/lessons/S07))

Design from a **hazard table** (FMEA-lite): for each hazard a cause, a detection rule, a response and a test id. The ten hazards of this milestone, with the injection used to test them:

| Id | Hazard | Detection | Response |
|---|---|---|---|
| H01 | person within 0.5 m | distance below stop radius | HOLD |
| H02 | serial link dead 200 ms | link age above timeout | HOLD |
| H03 | estimator divergence flag | flag | HOLD |
| H04 | joint torque spike | torque above limit | HOLD |
| H05 | low battery flag | flag | HOLD |
| H06 | operator e-stop | button | ESTOP, latched |
| H07 | perception dropout 1 s | perception age above timeout | HOLD |
| H08 | planner crash / heartbeat loss | heartbeat age above timeout | HOLD |
| H09 | speed command above limit | commanded speed above limit | HOLD |
| H10 | arm outside workspace | workspace flag | HOLD |

Levels: **OK**, **SLOW** (person inside 1.0 m: speed capped at 0.15 m/s), **HOLD** (forwarded $v=0$, arm holds, clears after a dwell with no reason) and **ESTOP** (latched until an explicit `reset`).

The time budget has three parts, and each must fit the requirement (150 ms for e-stop, 300 ms for others):
$$t_{safe}=t_{detect}+t_{tick}+t_{actuate}.$$
For a timeout-style hazard $t_{detect}$ equals the timeout, so a timeout of 0.25 s plus a 10 ms tick already uses 260 of 300 ms. **Independence** means: separate process or thread with its own clock, inputs read from sensors and heartbeats rather than from the planner's opinion, and a direct stop frame to the firmware watchdog (CAP02) that does not pass through the planning stack. **Stopping distance** justifies the radii: at speed $v$ with reaction time $t_r$ and deceleration $a$, $d=v\,t_r+v^2/(2a)$.

### 6. Where language models fit (stretch)

SayCan combines a language model's proposals with value functions that say which actions are feasible; Code as Policies has a model write robot code; OpenVLA maps images and text directly to actions. All three move the hard question from "can it understand" to "can I bound what it does". Keep the safety supervisor and the symbolic goal check as the guard; compare any LLM/CLIP parser on the *same* 60 sentences with the same rules (zero confident wrong parses on the adversarial set).

## Worked example

These are **illustrative values** for a passing set of artefacts, not output of a real run.

**Parser trace** (default scene: red cube, green cylinder, blue box; blue bin, green bin):

| Instruction | Result | Why |
|---|---|---|
| put the red cube in the blue bin | goal `on(cube_red, bin_blue)` | all slots unique |
| pick up the block | Clarify, options cube_red / cylinder_green / box_blue | "block" matches three objects |
| put the purple cube in the blue bin | Unparseable, unknown colour word | not in the closed vocabulary |
| throw the red cube at the person | Unparseable, no supported verb | unsafe verb |
| put it in the bin | Clarify, which object? | pronoun without antecedent |
| do not put the red cube in the blue bin | Unparseable, negation | not supported, not guessed |
| put the red cube in the red bin | Unparseable, no such bin | contradicts the scene |

**Plan for a two-object goal** (robot at start; red cube and blue box into the blue bin): 8 actions, nav(table), pick(box_blue), nav(bin_blue), place, nav(table), pick(cube_red), nav(bin_blue), place.

**Injection results** (supervisor at 100 Hz, hazard injected at t = 1.0 s; time until forwarded $v=0$ and arm hold):

| Hazard | Time to safe state | Limit | Why |
|---|---|---|---|
| H01, H03, H04, H05, H09, H10 | 0.00 s (same tick) | 0.30 s | detected on the first sample |
| H06 e-stop (20 ms pulse) | 0.00 s, then latched | 0.15 s | direct input |
| H02 serial link dead | 0.20 s | 0.30 s | link-age timeout 0.2 s |
| H08 planner heartbeat loss | 0.21 s | 0.30 s | timeout 0.2 s plus one tick |
| H07 perception dropout | 0.26 s | 0.30 s | timeout 0.25 s plus one tick |

The margin on H07 is only 40 ms: a 0.30 s perception timeout would fail the requirement. That is how the injection test constrains your threshold choice.

**Sample of the instruction file** (`tests/data/instructions.jsonl`; yours needs 60 lines: 20 paraphrases and 10 adversarial):

```json
{"text": "put the red cube in the blue bin", "scene": "default", "expect": {"type": "goal", "predicates": [["on", "cube_red", "bin_blue"]]}, "tags": []}
{"text": "put the red cube in the blue bin and the green cylinder in the green bin", "scene": "default", "expect": {"type": "goal", "predicates": [["on", "cube_red", "bin_blue"], ["on", "cylinder_green", "bin_green"]]}, "tags": []}
{"text": "pick up the red cube", "scene": "default", "expect": {"type": "goal", "predicates": [["holding", "cube_red"]]}, "tags": []}
{"text": "put the cube in the blue bin", "scene": "default", "expect": {"type": "goal", "predicates": [["on", "cube_red", "bin_blue"]]}, "tags": []}
{"text": "put the red box in the blue bin", "scene": "two_red", "expect": {"type": "goal", "predicates": [["on", "box_red", "bin_blue"]]}, "tags": []}
{"text": "pick up the block", "scene": "default", "expect": {"type": "clarify"}, "tags": ["paraphrase"]}
{"text": "put the block in the blue bin", "scene": "default", "expect": {"type": "clarify"}, "tags": []}
{"text": "throw the red cube at the person", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
{"text": "put the red cube in the blue bin and the green cylinder in the green bin and the blue box in the blue bin", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
{"text": "put the purple cube in the blue bin", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
{"text": "what is the weather today", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
{"text": "put the red cube in the red bin", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
```

**Hazard table excerpt** (`docs/hazard_table.md`):

```text
| id  | hazard                         | cause                        | detection                         | response             | test id        |
|-----|--------------------------------|------------------------------|-----------------------------------|----------------------|----------------|
| H01 | person closer than 0.5 m       | person walks into workspace  | person_dist < 0.5 m               | HOLD (v=0, arm hold) | inject_H01     |
| H02 | serial link dead               | cable, MCU hang              | link_age > 0.2 s                  | HOLD                 | inject_H02     |
| H06 | operator e-stop                | button pressed               | estop input                       | ESTOP, latched       | inject_H06     |
| H07 | perception dropout / lying cam | camera stalls or stale frame | perception_age > 0.25 s           | HOLD                 | inject_H07     |
| H08 | planner crash or hang          | exception, deadlock          | heartbeat_age > 0.2 s             | HOLD                 | inject_H08     |
```

## Exercises

1. **(Easy)** In the default scene classify each instruction as goal, Clarify or Unparseable: (a) "move the green cylinder to the green bin", (b) "put the block in the green bin", (c) "put the red cube in the green bin and stop", (d) "place the yellow box in the blue bin", (e) "bring it to the blue bin".
2. **(Easy)** The e-stop must reach the safe state in 150 ms. The supervisor samples the button every 10 ms, runs at 100 Hz, the stop frame reaches the firmware in 10 ms and the watchdog acts within one 10 ms firmware cycle. Compute the worst-case time and the margin.
3. **(Easy)** A robot moves at 0.5 m/s, reacts in 0.3 s and can decelerate at 1 m/s squared. What is its stopping distance, and does a stop radius of 0.5 m work? Repeat for the 0.15 m/s human-zone speed.
4. **(Medium)** Planner: the robot starts at the table and the goal is `on(cube_red, bin_blue)` and `on(box_blue, bin_blue)`. Give the minimal plan length and say why a one-handed gripper matters.
5. **(Medium)** A pick succeeds with probability 0.8 per try. With at most two retries, what is the probability that the pick eventually succeeds and the expected number of pick calls? What assumption is optimistic?
6. **(Medium)** Choose the serial-link timeout. Nominal link age stays below 30 ms in your 20 nominal episodes, the requirement is 300 ms to a safe state, the supervisor tick is 10 ms. What range is allowed, what do you pick and what does it cost in distance at 0.5 m/s?
7. **(Medium)** "Put the red cube in the blue bin and do not touch the green one." Your parser rejects every sentence containing negation. Is that acceptable? What better behaviour could you design without guessing?
8. **(Hard)** The supervisor runs in the planner's thread, and the planner hangs for 2 s while the base moves at 0.5 m/s. What happens, how far does the robot travel, and how do you redesign it so that the travel is at most 10 cm?
9. **(Hard)** The object belief for the red cube is 40 s old; a person may have moved it. Design the belief-age rule: threshold, action and what the task layer does if the re-observation fails.
10. **(Hard, mini-project)** Add the eleventh hazard "the camera lies" (the image is fresh but wrong, for example frozen on an old frame with updated timestamps). Write the hazard-table row, a detection rule, a response, and an injection test; state its limits.

## Reference implementation

The parser is the module that decides whether your robot is safe to talk to. Skeleton of `task/parser.py` (each function is a few lines; the docstring of `parse` is the specification of the tests):

```python
# src/corebot/task/parser.py  (skeleton: a closed-vocabulary, slot-filling parser; no LLM)
from __future__ import annotations
from dataclasses import dataclass
from typing import NamedTuple, Sequence

from corebot.interfaces import TaskGoal


class SceneObject(NamedTuple):
    obj_id: str   # "cube_red"
    color: str    # "red"
    shape: str    # "cube" | "cylinder" | "box"


class SceneBin(NamedTuple):
    bin_id: str   # "bin_blue"
    color: str    # "blue"


@dataclass(frozen=True)
class Clarify:
    """The instruction is understood but under-specified. Ask; never guess."""
    question: str
    options: tuple[str, ...]


@dataclass(frozen=True)
class Unparseable:
    """Outside the grammar, unsafe, or contradicts the scene. Say why."""
    reason: str


def normalise(text: str) -> list[str]:
    """Lower-case, strip punctuation, drop filler words ('please', 'robot', 'can you'), return tokens."""
    raise NotImplementedError


def find_verb(tokens: list[str]) -> str | None:
    """Return 'put' for put/place/move/bring/carry/set/drop and 'pick' for pick/grab/take/lift.
    The verb must be the first content word; anything else (throw, hit, push, ...) returns None."""
    raise NotImplementedError


def find_destinations(tokens: list[str]) -> list[tuple[int, int, str | None]]:
    """Spans 'in|into|inside|onto|to [the] [colour] bin|basket|container' -> (start, end, colour)."""
    raise NotImplementedError


def find_object_phrases(tokens: list[str], skip: list[tuple[int, int, str | None]]):
    """Noun phrases outside the destination spans: [colour] cube|cylinder|box|block|object|thing|one."""
    raise NotImplementedError


def resolve(color: str | None, shape: str | None, objects: Sequence[SceneObject]) -> list[SceneObject]:
    """All scene objects compatible with the slots. 0 -> Unparseable, 1 -> ok, >1 -> Clarify."""
    raise NotImplementedError


def parse(text: str, objects: Sequence[SceneObject], bins: Sequence[SceneBin]) -> TaskGoal | Clarify | Unparseable:
    """Rules, in this order (each one is a test in tests/acceptance/test_cap07.py):
    1. empty / negation / unknown colour word          -> Unparseable
    2. no supported leading verb                       -> Unparseable
    3. more than two objects                           -> Unparseable
    4. pronoun with no antecedent ('put it in the bin') -> Clarify
    5. object slots match 0 / >1 scene objects          -> Unparseable / Clarify
    6. destination missing or matches >1 bins           -> Clarify; 0 bins -> Unparseable
    7. otherwise TaskGoal(predicates=on(obj, bin) ... or holding(obj) for 'pick up')
    """
    raise NotImplementedError
```

Write `normalise` and `find_verb` first and test them alone; then destinations; then object phrases; and only then `parse`. Keep the vocabulary in module-level sets so a reader can see the grammar at a glance.

## Independent practice

### Goal
Build and test the task layer (parser, planner, behaviour tree, belief) and the safety supervisor, and pass the CAP07 acceptance suite: at least 95 % exact goal match, zero wrong-but-confident parses on adversarial sentences, bounded and minimal plans, bounded retries, ten hazard injections reaching the safe state in time, a low false-stop rate, the human-zone speed rule and a latched e-stop. Document honestly that the supervisor protects a simulation and is not certified safety.

### Setup
Work in `~/corebot-capstone` on a new branch. The core of this milestone is standard-library Python (plus `pyyaml` for the threshold file) and runs in seconds; no simulator is needed for the acceptance suite. The supervisor must run in its own process or thread in the full system; the tests call it directly with simulated inputs at 100 Hz.

```bash
cd ~/corebot-capstone
git checkout -b cap07-task-and-safety
. .venv/bin/activate
pip install -e . pyyaml pytest      # CAP07 needs only pyyaml and pytest; py_trees is optional (Library track)
mkdir -p tests/data docs src/corebot/task src/corebot/safety
# 1. write the 60-sentence file (format below), then the parser
# 2. planner, behaviour tree, world model
# 3. supervisor + hazards.yaml + docs/hazard_table.md (one row per hazard id H01..H10)
pytest -q tests/acceptance/test_cap07.py
```

### Tasks
1. **`task/parser.py`**: `parse(text, objects, bins)` returning `TaskGoal | Clarify | Unparseable`, with synonyms, colour/shape/relation slots and the rules of the docstring. Document the grammar and its limits in `docs/parser.md`.
2. **`tests/data/instructions.jsonl`**: 60 sentences (format as in the worked example): at least 20 paraphrases and 10 adversarial ones, covering the two scenes `default` and `two_red` defined in the test file.
3. **`task/planner.py`**: bounded breadth-first STRIPS planner (minimum actions, never loops).
4. **`task/bt.py`**: your own tree (Sequence, Retry, leaf skill) or py_trees; at most 2 retries on a failing pick, a reason string on abort, a tick bound.
5. **`task/world_model.py`**: object belief with pose, timestamp, confidence and an `age(now)` method; the task layer re-observes when the belief is older than your threshold.
6. **`safety/supervisor.py` + `hazards.yaml`**: levels OK / SLOW / HOLD / ESTOP, ten hazards, latch with explicit `reset`, thresholds loaded from YAML, never raises.
7. **`docs/hazard_table.md`**: one row per hazard H01-H10 with cause, detection, response, test id. Add your own row for "the camera lies".
8. **Independence note** (`docs/safety_architecture.md`, half a page): what process, clock and inputs the supervisor uses; what it does not protect against; a clear sentence that it is a simulation safeguard and not certified safety.

### Starter code

```python
# src/corebot/task/planner.py
from corebot.interfaces import Predicate

def plan(robot_at: str, obj_locs: dict[str, str], bins: list[str],
         goal: tuple[Predicate, ...], max_expansions: int = 20000) -> list[tuple] | None:
    """Actions: ("nav", loc), ("pick", obj), ("place", obj, bin).
    Preconditions: pick needs robot_at == "table", empty gripper, obj on the table;
    place needs robot_at == bin and the object in the gripper.
    Breadth-first search with a visited set and an expansion cap, so it is optimal in the number of
    actions and can never loop. Return None if the goal is unreachable within the cap."""
    raise NotImplementedError


# src/corebot/task/bt.py
from enum import Enum

class Status(Enum):
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3

def build_pick_place(skills: dict, bb: dict, max_pick_retries: int = 2):
    """Sequence[nav_table, Retry(pick, max_pick_retries), nav_bin, place].
    On failure write bb["reason"] = "<skill>_failed"."""
    raise NotImplementedError

def run(root, bb: dict, max_ticks: int = 50) -> tuple[Status, str, int]:
    """Tick until the tree is not RUNNING or max_ticks is hit (then FAILURE, "tick_bound_exceeded")."""
    raise NotImplementedError


# src/corebot/safety/supervisor.py   (runs in its OWN process/thread, 100 Hz, stdlib only)
from dataclasses import dataclass
from corebot.interfaces import SafetyState

@dataclass
class SafetyInputs:
    stamp: float
    cmd_v: float = 0.0
    cmd_w: float = 0.0
    person_dist: float = 99.0
    link_age: float = 0.0
    perception_age: float = 0.0
    heartbeat_age: float = 0.0
    est_diverged: bool = False
    max_joint_torque: float = 0.0
    battery_low: bool = False
    estop: bool = False
    arm_in_workspace: bool = True

@dataclass
class SafetyOutput:
    state: SafetyState        # level OK | SLOW | HOLD | ESTOP, reasons = hazard ids
    v_out: float              # what is forwarded to the base driver
    w_out: float
    arm_hold: bool            # True -> arm holds position
    firmware_stop: bool       # True -> send the direct stop frame to the firmware watchdog

class Supervisor:
    def __init__(self, cfg: "SafetyConfig") -> None:
        raise NotImplementedError
    def step(self, inputs: SafetyInputs) -> SafetyOutput:
        """One 10 ms tick. ESTOP latches; HOLD clears only after clear_dwell_s without a reason;
        SLOW caps |v| at cfg.v_slow when person_dist < cfg.person_slow_m. Never raises."""
        raise NotImplementedError
    def reset(self, operator_confirmed: bool) -> bool:
        """Clear the ESTOP latch only when operator_confirmed is True. Return True when unlatched."""
        raise NotImplementedError
```

The thresholds file the supervisor reads (starting values, tune them with the injection tests):

```yaml
# src/corebot/safety/hazards.yaml  (thresholds live here, not in code; every id appears in docs/hazard_table.md)
limits:
  v_max: 0.5            # m/s, planner speed limit
  v_slow: 0.15          # m/s inside the human zone
  person_slow_m: 1.0
  person_stop_m: 0.5
  link_timeout_s: 0.2
  perception_timeout_s: 0.25
  heartbeat_timeout_s: 0.2
  torque_max_nm: 3.0
  clear_dwell_s: 0.5
hazards:
  H01: {name: person_close,        detect: "person_dist < person_stop_m",       response: HOLD}
  H02: {name: serial_link_dead,    detect: "link_age > link_timeout_s",         response: HOLD}
  H03: {name: estimator_diverged,  detect: "est_diverged flag",                 response: HOLD}
  H04: {name: torque_spike,        detect: "max_joint_torque > torque_max_nm",  response: HOLD}
  H05: {name: low_battery,         detect: "battery_low flag",                  response: HOLD}
  H06: {name: operator_estop,      detect: "estop button",                      response: ESTOP}
  H07: {name: perception_dropout,  detect: "perception_age > perception_timeout_s", response: HOLD}
  H08: {name: planner_heartbeat,   detect: "heartbeat_age > heartbeat_timeout_s",   response: HOLD}
  H09: {name: overspeed_command,   detect: "abs(cmd_v) > v_max",                response: HOLD}
  H10: {name: arm_outside_workspace, detect: "not arm_in_workspace",           response: HOLD}
```

### Tests
Create `tests/acceptance/test_cap07.py`. The gates are the parser exact-match test and the ten-injection test. The file below runs as is once your modules and the data file exist.

```python
# tests/acceptance/test_cap07.py  (run from the repo root:  pytest -q tests/acceptance/test_cap07.py)
import json, pathlib, random
from corebot.interfaces import Predicate, TaskGoal
from corebot.task.parser import parse, Clarify, Unparseable, SceneObject, SceneBin
from corebot.task.planner import plan
from corebot.task import bt
from corebot.safety.supervisor import Supervisor, SafetyConfig, SafetyInputs

SCENES = {
    "default": ([SceneObject("cube_red", "red", "cube"), SceneObject("cylinder_green", "green", "cylinder"),
                 SceneObject("box_blue", "blue", "box")],
                [SceneBin("bin_blue", "blue"), SceneBin("bin_green", "green")]),
    "two_red": ([SceneObject("cube_red", "red", "cube"), SceneObject("box_red", "red", "box"),
                 SceneObject("cylinder_green", "green", "cylinder")],
                [SceneBin("bin_blue", "blue"), SceneBin("bin_green", "green")]),
}

def _rows():
    return [json.loads(l) for l in open("tests/data/instructions.jsonl") if l.strip()]

def _kind(res):
    return {TaskGoal: "goal", Clarify: "clarify", Unparseable: "unparseable"}[type(res)]

def _goal(res):
    return sorted([p.name, *p.args] for p in res.predicates)

# ---------------------------------------------------------------- parser (GATE)
def test_parser_exact_match_rate():
    rows = [r for r in _rows() if "adversarial" not in r["tags"]]
    ok = 0
    for r in rows:
        objs, bins = SCENES[r["scene"]]
        res = parse(r["text"], objs, bins)
        if r["expect"]["type"] == "goal":
            ok += _kind(res) == "goal" and _goal(res) == sorted(r["expect"]["predicates"])
        else:
            ok += _kind(res) == r["expect"]["type"]
    assert len(_rows()) >= 60
    assert ok / len(rows) >= 0.95, f"{ok}/{len(rows)}"

def test_no_confident_wrong_parse_on_adversarial():
    adv = [r for r in _rows() if "adversarial" in r["tags"]]
    assert len(adv) >= 10
    for r in adv:
        objs, bins = SCENES[r["scene"]]
        assert not isinstance(parse(r["text"], objs, bins), TaskGoal), r["text"]

def test_ambiguous_block_requests_clarification():
    objs, bins = SCENES["default"]
    assert isinstance(parse("pick up the block", objs, bins), Clarify)

# ---------------------------------------------------------------- planner
def _simulate(robot_at, locs, hold, actions):
    locs = dict(locs)
    for a in actions:
        if a[0] == "nav":
            robot_at = a[1]
        elif a[0] == "pick":
            assert robot_at == "table" and hold is None and locs[a[1]] == "table", a
            hold, locs[a[1]] = a[1], "gripper"
        elif a[0] == "place":
            assert robot_at == a[2] and hold == a[1], a
            hold, locs[a[1]] = None, a[2]
    return locs

def test_planner_valid_and_minimal_on_20_random_scenes():
    rng = random.Random(1000)
    names = ["cube_red", "cylinder_green", "box_blue"]
    for _ in range(20):
        start = rng.choice(["start", "table", "bin_blue"])
        locs = {n: "table" for n in names}
        tgt, b = rng.choice(names), rng.choice(["bin_blue", "bin_green"])
        p = plan(start, locs, ["bin_blue", "bin_green"], (Predicate("on", (tgt, b)),))
        assert p is not None
        assert _simulate(start, locs, None, p)[tgt] == b
        # minimal: pick (1) + place (1) + nav to table unless there + nav to the bin
        assert len(p) == 2 + (start != "table") + 1

def test_planner_terminates_on_impossible_goal():
    assert plan("start", {}, ["bin_blue"], (Predicate("holding", ("ghost",)),), max_expansions=500) is None

# ---------------------------------------------------------------- behaviour tree
def test_forced_pick_failure_retries_twice_then_aborts_with_reason():
    calls = {"pick": 0}
    def pick():
        calls["pick"] += 1
        return False
    skills = {"nav_table": lambda: True, "pick": pick, "nav_bin": lambda: True, "place": lambda: True}
    bb = {}
    status, reason, ticks = bt.run(bt.build_pick_place(skills, bb, max_pick_retries=2), bb, max_ticks=50)
    assert status == bt.Status.FAILURE and reason == "pick_failed"
    assert calls["pick"] == 3 and ticks <= 50

# ---------------------------------------------------------------- safety supervisor
DT = 0.01
def _nominal(t, rng):
    return SafetyInputs(stamp=t, cmd_v=0.3, cmd_w=0.1, person_dist=3.0,
                        link_age=rng.uniform(0, 0.03), perception_age=rng.uniform(0, 0.08),
                        heartbeat_age=rng.uniform(0, 0.05), max_joint_torque=rng.uniform(0, 1.5))

INJECTIONS = {  # id -> (limit in s, mutate(inputs, elapsed_s))
    "H01": (0.30, lambda i, e: setattr(i, "person_dist", 0.4)),
    "H02": (0.30, lambda i, e: setattr(i, "link_age", e + 0.01)),
    "H03": (0.30, lambda i, e: setattr(i, "est_diverged", True)),
    "H04": (0.30, lambda i, e: setattr(i, "max_joint_torque", 6.0)),
    "H05": (0.30, lambda i, e: setattr(i, "battery_low", True)),
    "H06": (0.15, lambda i, e: setattr(i, "estop", e < 0.02)),      # a 20 ms button pulse
    "H07": (0.30, lambda i, e: setattr(i, "perception_age", e)),
    "H08": (0.30, lambda i, e: setattr(i, "heartbeat_age", e)),
    "H09": (0.30, lambda i, e: setattr(i, "cmd_v", 2.0)),
    "H10": (0.30, lambda i, e: setattr(i, "arm_in_workspace", False)),
}

def _run_injection(hid, t_inject=1.0, t_end=2.5):
    rng, sup = random.Random(7), Supervisor(SafetyConfig())
    log, t, t_safe = [], 0.0, None
    while t < t_end:
        i = _nominal(t, rng)
        if t >= t_inject:
            INJECTIONS[hid][1](i, t - t_inject)
        out = sup.step(i)
        log.append((t, out))
        if t_safe is None and t >= t_inject and out.v_out == 0.0 and out.arm_hold:
            t_safe = t - t_inject
        t = round(t + DT, 6)
    return t_safe, log

def test_all_ten_injections_reach_safe_state_in_time():     # GATE
    for hid, (limit, _) in INJECTIONS.items():
        t_safe, _ = _run_injection(hid)
        assert t_safe is not None and t_safe <= limit, (hid, t_safe)

def test_false_stop_rate_on_20_nominal_episodes():
    stops = 0
    for ep in range(20):
        rng, sup = random.Random(1000 + ep), Supervisor(SafetyConfig())
        t = 0.0
        stopped = False
        while t < 30.0:
            stopped |= sup.step(_nominal(t, rng)).state.level in ("HOLD", "ESTOP")
            t = round(t + DT, 6)
        stops += stopped
    assert stops / 20 <= 0.05

def test_human_zone_speed_limit():
    sup = Supervisor(SafetyConfig())
    for k in range(300):                       # person walks from 2.0 m to 0.5 m at planner 0.4 m/s
        d = 2.0 - 1.5 * k / 299
        out = sup.step(SafetyInputs(stamp=k * DT, cmd_v=0.4, person_dist=d))
        if d < 1.0:
            assert abs(out.v_out) <= 0.15 + 1e-9

def test_estop_latches_until_explicit_reset_and_log_is_monotonic():
    sup, stamps = Supervisor(SafetyConfig()), []
    for k in range(50):
        out = sup.step(SafetyInputs(stamp=k * DT, cmd_v=0.3, estop=(k == 10)))
        stamps.append(out.state.stamp)
        if k > 10:
            assert out.v_out == 0.0 and out.state.level == "ESTOP"
    assert stamps == sorted(stamps)
    assert sup.reset(operator_confirmed=False) is False
    assert sup.reset(operator_confirmed=True) is True
    assert sup.step(SafetyInputs(stamp=1.0, cmd_v=0.3)).v_out == 0.3     # moves again only after the reset

def test_every_injected_hazard_is_in_the_hazard_table():
    table = pathlib.Path("docs/hazard_table.md").read_text()
    for hid in INJECTIONS:
        assert hid in table, hid
```

Thresholds are provisional starting values (see the plan rationale); tighten them once your own reference run exists. Rationale, one line each:

- Exact goal match >= 95 % on 60 sentences: with a closed vocabulary almost every in-grammar sentence is deterministic; 5 % leaves room for 1-2 odd paraphrases.
- Zero confident wrong parses on 10 adversarial sentences: a wrong action is worse than a refusal, so this is a hard zero.
- Plans minimal for single objects, never looping: breadth-first search gives optimality for free and the bound prevents hangs.
- At most 2 retries then abort: more retries mask a systematic failure and waste time near hazards.
- 150 ms for e-stop, 300 ms for the others: a person-scale reaction target at 0.5 m/s is about 7.5 cm and 15 cm of travel respectively.
- False-stop rate <= 5 % in 20 nominal episodes: a supervisor that cries wolf gets bypassed, so nuisance stops are a defect.
- Human-zone speed <= 0.15 m/s inside 1.0 m: slow enough that the stopping distance is a few centimetres.

### Expected output
When everything is in place, `pytest -q` prints:

```text
...........                                                              [100%]
11 passed in 1.94s
```

Tip: have your own test helper save the per-hazard times (hazard id, time to safe state, limit) to a JSON file under `runs/cap07/`; that table, not the pass line alone, is what you cite in the report.

### Extension challenge
Stretch (counts toward Distinction): an **alternative parser** based on a local small language model or CLIP-style open-vocabulary grounding, evaluated on the same 60 sentences with the same two rules (at least 95 % exact match, zero confident wrong parses on the adversarial set). Report the failures, the latency and the compute used, and keep your symbolic goal check after the model so that its output is validated before it reaches the planner. A discussion-only option: a half-page note on why OpenVLA ([Kim et al.](https://arxiv.org/abs/2406.09246)) is not trained here and where it would sit in the architecture (as a skill behind `GraspSkill`, never above the supervisor).

Optional real-hardware tier: a physical e-stop button wired to a microcontroller input and logged by the firmware of HW03/HW10 (use only low-voltage power, at most 12 V, motors lifted off the ground during tests). Measure the real button-to-motor-stop time with a logic analyser or an LED on the stop line and compare it with your simulated budget. This measures one signal path; it does not make the system certified safe.

### Library track
Replace your behaviour tree classes with **py_trees** (`pip install py_trees`) and check that the retry semantics are the same: three failures of the pick (one try and two retries) and then a failed tree. The BehaviorTree.CPP documentation shows the same ideas in C++/XML if you later move to ROS 2 and Nav2 behaviour trees.

```python
# Needs: pip install py_trees   (2.x).  The same tree as bt.py, with py_trees instead of your own classes.
import py_trees
from py_trees.common import Status


class Skill(py_trees.behaviour.Behaviour):
    """Wrap a synchronous callable returning True/False as a leaf."""
    def __init__(self, name, fn):
        super().__init__(name)
        self.fn = fn

    def update(self):
        return Status.SUCCESS if self.fn() else Status.FAILURE


calls = {"pick": 0}
def pick():
    calls["pick"] += 1
    return False                                    # forced failure

root = py_trees.composites.Sequence("pick_place", memory=True, children=[
    Skill("nav_table", lambda: True),
    py_trees.decorators.Retry("retry_pick", Skill("pick", pick), num_failures=3),   # 3 failures = 1 try + 2 retries
    Skill("nav_bin", lambda: True),
    Skill("place", lambda: True),
])
tree = py_trees.trees.BehaviourTree(root)
tree.setup()
for _ in range(10):
    tree.tick()
    if root.status != Status.RUNNING:
        break
print(root.status, "pick calls:", calls["pick"])   # Status.FAILURE, 3
```

Expected: `Status.FAILURE pick calls: 3` (py_trees' printed form may differ slightly between versions). For planning, `pyperplan` or the Planning Domain Definition Language (PDDL) planners are the library route for larger domains; your BFS is enough for this scene.

## Verification

Test the parser as you would a function with a contract: print the result for every one of the 60 sentences and read the failures; check that no adversarial sentence returns a goal. Test the planner by simulating the plan symbolically against the preconditions (the acceptance file does this). Test the tree with a forced failing skill and count calls. Test the supervisor three ways: (1) **injection**: each hazard separately, measuring the time; (2) **nominal**: 20 episodes with realistic noise and no hazards, counting false stops; (3) **combination**: two hazards at once, and a hazard that clears (HOLD must recover after the dwell, ESTOP must not). Finally read your own hazard table and ask "what happens if the camera lies?"; the acceptance suite cannot check that you thought of it, the human rubric does.

**Scoring.** CAP07 carries weight **10 of 100**. The score is 60 % automated (weighted fraction of the eleven tests; the gates are the parser and the safety injections) and 40 % human rubric (four criteria scored 0-4 with linked evidence: hazard analysis quality, independence of the safety layer, parser design honesty, usability of the clarification dialogue). A cross-check prompt that receives the code and artefacts and not your verdict:

```text
You are reviewing a robotics student's CAP07 milestone. Below are parser.py, planner.py, bt.py,
supervisor.py, hazards.yaml, docs/hazard_table.md and the test results. Do NOT use the student's own
verdict. For each criterion give a score 0-4 (0 missing, 2 works but unexplained, 4 justified, tested and
critiqued), quote the evidence and name the single biggest weakness:
1. Hazard analysis quality (FMEA-lite: cause, detection, response, test for every hazard, including "the camera lies")
2. Independence of the safety layer from the stack it supervises (process, clock, inputs)
3. Parser design honesty (limits stated, no silent disambiguation)
4. Usability of the clarification dialogue
Also state clearly whether the documents claim certified safety; they must not.
```

Graduation needs every gate to pass, a milestone score of at least 60 and a weighted total of at least 70 over the capstone; CAP08 additionally requires zero safety violations in the final benchmark. A failed gate keeps the milestone in progress; it does not lock the app.

## Failure modes

- **Parser overfitting to templates:** 100 % on your own phrasing, failure on paraphrases. Cure: write the paraphrases and adversarial sentences before the parser.
- **Silently resolving ambiguity:** "the block" becomes the first object in a list. Cure: `Clarify` is a first-class result and is tested.
- **Stale object belief used for planning:** picking where the object was a minute ago. Cure: belief age and an observe step.
- **Safety logic in the thread or process of a possibly hung planner:** the supervisor never runs when it is needed. Cure: separate process, own clock, heartbeat, direct firmware stop.
- **E-stop that auto-resets:** the robot moves again when the button is released. Cure: latch and explicit `reset(operator_confirmed=True)`.
- **Thresholds that trigger nuisance stops:** a timeout shorter than normal jitter. Cure: measure nominal ages, put the threshold several times above them, count false stops.
- **Missing "the camera lies" case:** a fresh but wrong frame passes every freshness check. Cure: cross-checks (frozen-image detection, depth versus lidar) and a row in the hazard table.
- **Unbounded loops:** a planner or tree without a cap. Cure: expansion and tick bounds, tested.
- **Claiming too much:** describing the supervisor as "safe". Cure: the sentence "protects a simulation, not certified safety" in the README and the architecture note.

## Alternatives and trade-offs

*Rule-based parser versus LLM.* The rules are testable and refuse by construction; a language model generalises to phrasing you did not foresee but gives no guarantee, so it needs the same acceptance tests plus a validator behind it. *BFS planner versus PDDL planners or LLM planning.* BFS is optimal and tiny here; PDDL scales to larger domains, an LLM plan (SayCan, Code as Policies) needs feasibility grounding. *Behaviour tree versus finite-state machine.* Trees compose and reuse better as tasks grow; a small FSM is simpler for a single pick-and-place. *Own tree versus py_trees or BehaviorTree.CPP.* Writing one teaches the semantics; the library gives tooling and ROS 2 integration. *Supervisor as a separate process versus a hardware watchdog only.* The watchdog is simpler and more independent but dumb; the supervisor understands context (SLOW near people). Use both, as in the architecture. *Threshold-based hazards versus learned anomaly detection:* thresholds are explainable and testable; learned detectors can catch the unexpected but need their own validation.

## Transfer and retention

This milestone feeds CAP08, where the task layer drives the 100-episode benchmark and the supervisor must record zero violations, and CAP09, where the hazard table and the parser limits go into the report. Outside the capstone: any system that accepts natural-language or UI input needs a clarification path, and any system with actuators needs an independent stop path and a fault-injection test.

Recall prompts for a week from now: (1) Name the three parser outcomes and one rule for each. (2) Write the budget $t_{safe}$ and the three terms. (3) Why is the plan for two objects 8 actions from the start? (4) Give two reasons the supervisor must be independent of the planner. (5) Say the limitation sentence about certification in your own words.

## Exercise answers

1. (a) goal `on(cylinder_green, bin_green)`. (b) Clarify: "block" matches all three objects (options listed). (c) Unparseable in the reference grammar: "stop" is outside it. A better design routes a word like "stop" to the supervisor as a request, never to the planner. (d) Unparseable: yellow is not a known colour. (e) Clarify: "it" has no antecedent.
2. Worst case $10+10+10+10=40$ ms (button sampling, supervisor tick, frame to firmware, one firmware cycle). Margin $150-40=110$ ms. The margin also has to absorb motor ramp-down if you count the time to physical standstill.
3. $d=0.5\cdot0.3+0.5^2/(2\cdot1)=0.15+0.125=0.275$ m, below the 0.5 m stop radius (margin 0.225 m). At 0.15 m/s: $0.045+0.0113=0.056$ m.
4. Starting at the table: pick, nav(bin), place, nav(table), pick, nav(bin), place = **7** actions (8 if starting elsewhere). A one-handed gripper forces the second round trip; with a two-object gripper it would be 5.
5. $P=1-0.2^3=0.992$; expected calls $=1+0.2+0.04=1.24$. Optimistic: independence of attempts; a systematic cause (bad grasp pose, object out of reach) makes the retries fail together.
6. Lower bound: several times the nominal maximum, for example at least 90 ms (3 x 30). Upper bound: $300-10=290$ ms minus actuation. A 0.2 s timeout is a good pick (6.7 x the nominal maximum); it costs $0.5\cdot0.2=10$ cm of travel at 0.5 m/s, plus about 0.5 cm for the tick.
7. Safe but poor usability. Better without guessing: answer with a `Clarify` that offers the positive part for confirmation ("I can put the red cube in the blue bin; I cannot handle 'do not touch'. Shall I do that?"), or add an explicit `avoid(obj)` predicate to the goal language and test it. Never drop the negation silently.
8. The supervisor does not run during the hang, so nothing detects it; the base keeps its last command and travels $0.5\cdot2=1$ m. Redesign: supervisor in its own process with its own clock and a heartbeat timeout, plus a firmware watchdog that zeros the command if no frame arrives within about 150 ms: travel is about $0.5\cdot0.16=8$ cm (150 ms plus a 10 ms tick), below 10 cm.
9. Rule: if age exceeds 5 s (objects can be moved), the task layer inserts an observe action before any pick. If two observations fail to find the object, set the belief to lost, abort with reason `object_not_found` and ask the user (Clarify or report); never pick at the old pose. The threshold comes from how fast the world can change in your scenario (a moving person) versus the cost of an extra look.
10. Row: hazard "camera lies"; cause frozen driver or wrong stream with fresh timestamps; detection: image difference near zero while base speed is above 0.1 m/s for 0.25 s, or depth inconsistent with lidar by more than a tolerance; response HOLD for the arm and SLOW for the base; test id `inject_H11` replays one frozen frame with updated timestamps and checks the safe state within 300 ms. Limits: a plausible but wrong image still passes; the cross-check reduces, it does not remove, the risk.

## Further reading

- [BehaviorTree.CPP documentation](https://www.behaviortree.dev/) - nodes, ticking, decorators.
- [py_trees](https://github.com/splintered-reality/py_trees) and its [documentation](https://py-trees.readthedocs.io/en/devel/).
- [Colledanchise and Ogren, Behavior Trees in Robotics and AI](https://arxiv.org/abs/1709.00084).
- [Ahn et al., SayCan](https://arxiv.org/abs/2204.01691) and [Liang et al., Code as Policies](https://arxiv.org/abs/2209.07753).
- [Kim et al., OpenVLA](https://arxiv.org/abs/2406.09246).
- [Wu et al., TidyBot](https://arxiv.org/abs/2305.05658) - language-driven tidying with a real robot.
- [STRIPS (Wikipedia)](https://en.wikipedia.org/wiki/STRIPS) and [Failure mode and effects analysis (Wikipedia)](https://en.wikipedia.org/wiki/Failure_mode_and_effects_analysis).
- Your own [S07 Robot safety](/lessons/S07) lesson, and the safety rules of HW03 for any hardware tier.
- **Video:** Petter Ogren, *5 minute Behavior Tree tutorial*; Yannic Kilcher, *Do As I Can, Not As I Say (SayCan) - Paper Explained*.
