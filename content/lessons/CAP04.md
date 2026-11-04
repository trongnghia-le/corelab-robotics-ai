---
{
  "id": "cap04-capstone",
  "module_id": "CAP04",
  "title": "Capstone milestone 4: occupancy mapping, A* planning and path tracking for CoreBot",
  "summary": "Build a log-odds occupancy grid from lidar and the estimated pose, inflate it into a costmap, plan with A*, track the path within base limits, handle dynamic obstacles, and judge the whole pipeline with seeded benchmarks and Wilson bounds.",
  "estimated_minutes": 1560,
  "project_minutes": 1560,
  "prerequisites": [
    "CAP03",
    "E02",
    "C05",
    "S05"
  ],
  "source_refs": [
    {
      "title": "Occupancy grid mapping (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Occupancy_grid_mapping"
    },
    {
      "title": "A* search algorithm (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/A*_search_algorithm"
    },
    {
      "title": "Pure pursuit (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Pure_pursuit"
    },
    {
      "title": "Nav2 documentation",
      "url": "https://docs.nav2.org/index.html"
    },
    {
      "title": "CMU Robotic Motion Planning course notes",
      "url": "https://www.cs.cmu.edu/~motionplanning/"
    },
    {
      "title": "Binomial proportion confidence interval (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval"
    }
  ],
  "objectives": [
    "Build a log-odds occupancy grid from lidar scans and an estimated pose and score it against a ground-truth grid with IoU.",
    "Derive an inflation radius from the robot footprint, a safety margin and the pose uncertainty, and use it in a costmap.",
    "Implement 8-connected A* with an admissible octile heuristic and prove it optimal against a Dijkstra reference.",
    "Track a path with pure pursuit under velocity and acceleration limits and stop or replan when an obstacle appears.",
    "Judge a navigation benchmark with the lower Wilson bound, path efficiency and zero-collision gates, and defend the thresholds."
  ],
  "core_theory": [
    "Capstone integration: mapping, planning fundamentals, LQR/path tracking, ROS 2 runtime"
  ],
  "labs": [
    "Complete the CAP04 milestone brief in ~/corebot-capstone: pass tests/acceptance/test_cap04.py on a seeded 30-episode navigation benchmark."
  ],
  "assessment_refs": [
    "CAP04-diagnostic-v1"
  ],
  "review_prompts": [
    "Explain how the pose uncertainty from CAP03 changes the inflation radius your planner should use.",
    "Say why 27 successes out of 30 does not satisfy a gate of a 75 percent lower Wilson bound."
  ],
  "extension_refs": [
    "https://docs.nav2.org/index.html",
    "https://turtlebot.github.io/turtlebot4-user-manual/"
  ]
}
---

## Why this matters

After CAP03 the robot knows roughly where it is. CAP04 teaches it to **go somewhere**: turn lidar rays into a map, turn the map into a safe cost surface, find a short path, and follow that path without hitting anything or demanding more than the wheels can deliver. Every later milestone leans on it: CAP05 needs the base parked at the right place in front of the table, CAP07 sends navigation goals from a parsed sentence, and CAP08 counts a navigation timeout as a failure category (`NAV_TIMEOUT`) in its error budget.

This milestone is also where integration bugs become expensive. A planner that is correct but runs in the wrong frame, a tracker that ignores the angular limit, or a map built from the simulator's true pose instead of your EKF all produce a robot that looks fine in a demo and fails a seeded benchmark. The brief below therefore ships with an acceptance suite, including a test that your navigation code never imports simulator truth.

**Scoring.** CAP04 carries a weight of 11 out of 100 for graduation. Its gate checks (bold in the Tests section) are navigation success with the Wilson bound, and zero collisions.

## Intuition

CAP04 adds the "mind's eye" of the base: a grid that says where space is free, a cost surface that says where the robot body may go, a path through it and a controller that walks it. Think of a cautious person crossing a dark room with a torch: the torch beam is the lidar, what they remember is the grid, the "stay a hand away from the furniture" habit is the inflation, and the walking pace they pick depending on how sharp the next turn is, is the tracker.

![Architecture of the CoreBot Tidy capstone with firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation, task layer and a safety supervisor](/lesson-figures/CAP-architecture.svg)

*Where CAP04 sits: the "mapping/planning" band takes `ScanSample` and `Pose2DCov` and produces `/cmd_vel` for the firmware base built in CAP02.*

This milestone uses these earlier CoreLab topics, so go back to them when a step feels unfamiliar:

- [CAP03](/lessons/CAP03) supplies the pose and its covariance; the map is only as good as that pose.
- [E02 Planning fundamentals](/lessons/E02) gives A*, admissible heuristics and Dijkstra.
- [C05 LQR](/lessons/C05) is the optional tracker upgrade (LQR on cross-track and heading error).
- [S05 ROS 2 runtime](/lessons/S05) explains executors, callbacks and QoS for the optional ROS 2 wrappers and for the Nav2 track.
- Also useful: [C08 Sensor fusion](/lessons/C08) and [C12 Nonlinear state estimation](/lessons/C12) for how pose uncertainty arises, and [S07 Robot safety](/lessons/S07) for stop distances.

## Theory and derivation

These are the integration notes: the five formulas and interfaces that decide whether the milestone passes. Each links back to its source topic.

![Pipeline from lidar scan and EKF pose through occupancy grid, costmap, A star and pure pursuit to the wheel command, with a stop and replan monitor and the cost profile around an obstacle](/lesson-figures/CAP04.svg)

### 1. Log-odds occupancy update (source: CAP03 for the pose, Probabilistic Robotics for the model)

Each cell stores the log-odds $l=\ln\frac{p}{1-p}$ of being occupied. A beam that **ends** in a cell adds $l_\text{occ}=\ln\frac{0.7}{0.3}=0.847$; every cell the beam **crosses** adds $l_\text{free}=\ln\frac{0.4}{0.6}=-0.405$. The update is a plain addition, which is why log-odds are used: evidence from independent scans simply accumulates. Clamp to $[-4,4]$ so a cell that was wrongly marked can change its mind within a few scans. Convert back with $p=1/(1+e^{-l})$. A reading at the maximum range is "no return", not an obstacle: skip the occupied update for it.

The endpoint in the map frame is $(x+r\cos(\theta+\alpha),\,y+r\sin(\theta+\alpha))$ with the **estimated** pose $(x,y,\theta)$. A heading error $\delta\theta$ moves an endpoint at range $r$ sideways by about $r\,\delta\theta$: at 3 m, 2 degrees is 10 cm, two cells. This is why the mapping score depends on CAP03.

### 2. Footprint, inflation and the costmap (source: S07 for margins, CAP03 for $\sigma$)

Treat the robot as a disc and the planner as moving a point. Three radii matter: the **circumscribed** radius $r_c$ of the footprint (a hard limit: any centre closer than this to an occupied cell is a collision), a **safety margin** $m$, and an allowance for localisation uncertainty $2\sigma_\text{pos}$ taken from the EKF covariance:
$$r_\text{inflate}=r_c+m+2\sigma_\text{pos}.$$
The costmap is *lethal* (254) closer than $r_c$, then decays, for example $c(d)=253\,e^{-k(d-r_c)}$ out to $r_\text{inflate}$ and 0 beyond. In cells of size $\Delta$: $n=\lceil r_\text{inflate}/\Delta\rceil$. A goal inside a lethal cell is unreachable by construction: snap it to the nearest free cell or report `no_path`, never plan to it.

### 3. A* with the octile heuristic (source: E02)

On an 8-connected grid a step costs 1 (axis) or $\sqrt2$ (diagonal). The exact free-space cost for offsets $dx,dy$ is $(\max-\min)+\sqrt2\min$, which the **octile** heuristic computes:
$$h(dx,dy)=(dx+dy)+(\sqrt2-2)\min(dx,dy).$$
It never exceeds the true cost (admissible) and is consistent, so A* with a closed set returns an optimal path. Manhattan distance overestimates diagonal moves and is **not** admissible here; Euclidean distance is admissible but weaker (more expansions). With cost-aware steps, multiply a step by $1+w\,c/254$; $w=0$ must reproduce Dijkstra exactly, which is the acceptance test. Forbid moves that cut a blocked corner.

### 4. Pure pursuit with limits (source: C05 for the LQR alternative)

Pick the path point at distance $L$ ahead of the robot, express it in the robot frame as $(x_r,y_r)$ with $x_r^2+y_r^2=L^2$, and drive the arc through it:
$$\kappa=\frac{2y_r}{L^2},\qquad \omega=v\,\kappa.$$
Longer $L$ is smoother but cuts corners; a typical choice is $L=\max(L_\min,\,g\,v)$. Then enforce the base limits of CAP02: slow down so $|\omega|\le\omega_\max$ (that is, $v\le\omega_\max/|\kappa|$), clip $v$ to $v_\max$ and limit $|\Delta v|\le a_\max\,\Delta t$. If you prefer a model-based tracker, LQR on the cross-track and heading error ([C05](/lessons/C05)) gives the same interface with a tuned gain instead of a geometric rule.

### 5. Stopping distance and benchmark statistics (source: S07, RS02)

The distance needed to stop from speed $v$ with deceleration $a$ and total latency $t_\ell$ (sensing, planning, command, firmware) is
$$d_\text{stop}=\frac{v^2}{2a}+v\,t_\ell.$$
Your inflation margin and your speed limit must keep $d_\text{stop}$ smaller than the distance at which the lidar can see an obstacle. For the benchmark, judge success with the **lower Wilson 95 % bound**, not the point estimate (formula in `evalkit.wilson_interval`, [RS02](/lessons/RS02)): with 30 episodes the point estimate of 90 % corresponds to a lower bound of only 74 %. Path efficiency is the travelled length divided by the shortest path length in the ground-truth map.

## Worked example

This is a reference trace of a passing run. **Illustrative values**: they show what healthy numbers look like and were computed by hand and with the small script in Verification, not taken from a real run of your robot.

**Map update.** A cell hit by three beams has $l=3\cdot0.847=2.54$, so $p=0.927$. A cell crossed by five free beams has $l=-2.03$, $p=0.116$. A cell hit twice and crossed once: $l=1.289$, $p=0.784$, still above the 0.65 export threshold.

**Inflation.** Circumscribed radius $r_c=0.20$ m, margin $m=0.05$ m, EKF position standard deviation $\sigma=0.03$ m: $r_\text{inflate}=0.20+0.05+0.06=0.31$ m, which is $\lceil 0.31/0.05\rceil=7$ cells; the lethal radius is 4 cells.

**Heuristic.** Start-to-goal offset $dx=30$, $dy=12$ cells: octile $h=42-0.586\cdot12=34.97$ cells $=1.749$ m, while the straight line is 32.31 cells. A real path cannot be shorter than 34.97 cells in free space, so the heuristic is tight.

**Tracker.** Lookahead point at $(0.42,\,0.16)$ m in the robot frame: $L=0.449$ m, $\kappa=2\cdot0.16/0.202=1.584$ m$^{-1}$; at $v=0.4$ m/s, $\omega=0.634$ rad/s, inside the 1.5 rad/s limit.

**Stopping.** At $v=0.5$ m/s, $a=1$ m/s$^2$ and 150 ms total latency: $d_\text{stop}=0.125+0.075=0.20$ m.

| Check (test) | Threshold | Illustrative result |
|---|---|---|
| Occupied-cell IoU | >= 0.85 | 0.872 (TP 1900, FP 120, FN 160) |
| A* vs Dijkstra, 20 fixtures | exact | 0 mismatches |
| Median plan time 200 x 200 | < 50 ms | 11.4 ms |
| Mean / max cross-track | < 0.08 / < 0.20 m | 0.041 / 0.118 m |
| Success, 30 episodes | >= 90 %, lower bound >= 75 % | 28/30 = 93.3 %, bound 78.7 % |
| Collisions | 0 | 0 |
| Median path efficiency | <= 1.3 | 1.12 |
| Dynamic obstacle, min clearance | >= 0.15 m | 0.21 m (1 of 10 trials `blocked`) |

Notice that 27 of 30 (90.0 %) would have a lower bound of 74.4 % and fail the gate even though it meets 90 %: the gate asks for evidence, not luck.

## Exercises

1. **(Easy)** A cell is hit by two beams and crossed by one free beam, with $p_\text{occ}=0.7$ and $p_\text{free}=0.4$. Give its log-odds and probability. Would it be exported as occupied at a 0.65 threshold?
2. **(Easy)** A robot has circumscribed radius 0.22 m, you want a 0.05 m margin and the EKF reports $\sigma_\text{pos}=0.04$ m. Give the inflation radius in metres and in 5 cm cells.
3. **(Easy)** *Statistics.* A navigation benchmark has 27 successes in 30 episodes. Compute the Wilson 95 % interval, say whether it passes a gate "point estimate at least 90 % and lower bound at least 75 %", and how many successes would pass.
4. **(Medium)** For $dx=24$ and $dy=10$ cells compute the Manhattan, Euclidean and octile heuristic values and the true free-space cost on an 8-connected grid. Which heuristics are admissible?
5. **(Medium)** *Calculation.* The lookahead point is $(0.30,\,-0.12)$ m in the robot frame and the robot drives at 0.5 m/s with $\omega_\max=1.5$ rad/s. Compute $\kappa$, $\omega$ and whether the tracker must slow down.
6. **(Medium)** *Integration.* An obstacle can be seen 1.5 m ahead, the robot brakes at 1 m/s$^2$ with 150 ms of latency and you need 0.15 m clearance. At what speed does the stop distance consume the whole gap? What does your answer say about why the dynamic-obstacle test is mostly a test of logic, not physics?
7. **(Medium)** A heading error of 2 degrees is present while mapping a wall 3 m away. Estimate the sideways error of the wall cells and say what it does to the occupied-cell IoU at 5 cm resolution.
8. **(Hard)** *Design.* A corridor is 0.9 m wide. With $r_c=0.22$, $m=0.05$ and $\sigma=0.03$ m, then $\sigma=0.08$ m, is the corridor passable in the inflated costmap? What should the planner do when the covariance grows?
9. **(Hard)** *Anti-cheating.* The AST test forbids importing `corebot.sim.world` in the navigation modules. List three ways a learner could still feed ground truth into the pipeline and one extra test for each.
10. **(Hard, mini-project)** Run the 30-episode benchmark on five layouts, then classify every failure into `timeout`, `blocked`, `no_path`, `collision` with a one-line cause. State your assumptions, a baseline (empty room, straight goal), a boundary case (goal one cell inside the inflation zone) and which observation would make you reject your planner.

## Reference implementation

A skeleton of the first module, `mapping/occupancy.py`. It is not runnable here (NumPy and your `corebot` package are needed) but it is syntactically valid and matches the interfaces of `interfaces.py`.

```python
"""src/corebot/mapping/occupancy.py -- log-odds occupancy grid (skeleton).

Frames: `map` is fixed at the room corner; cell (i, j) covers
x in [x0 + i*res, x0 + (i+1)*res), y in [y0 + j*res, y0 + (j+1)*res).
The pose used here is the EKF estimate from CAP03, never the simulator truth.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from corebot.interfaces import Pose2DCov, ScanSample


@dataclass(frozen=True)
class GridSpec:
    width_m: float = 4.0
    height_m: float = 4.0
    resolution: float = 0.05          # metres per cell
    x0: float = 0.0
    y0: float = 0.0
    p_occ: float = 0.70               # inverse sensor model: cell at the beam end
    p_free: float = 0.40              # cells the beam passed through
    l_min: float = -4.0               # clamp so a cell can change its mind
    l_max: float = 4.0
    occupied_threshold: float = 0.65  # probability used to export a binary grid


class OccupancyGrid:
    def __init__(self, spec: GridSpec) -> None:
        """Allocate `log_odds` (float32, shape (ny, nx)) filled with 0.0 (p = 0.5)."""
        raise NotImplementedError

    def world_to_cell(self, x: float, y: float) -> tuple[int, int] | None:
        """(i, j) for a map-frame point, or None if outside the grid."""
        raise NotImplementedError

    def ray_cells(self, i0: int, j0: int, i1: int, j1: int) -> list[tuple[int, int]]:
        """Bresenham cells from (i0, j0) up to but excluding (i1, j1)."""
        raise NotImplementedError

    def integrate_scan(self, pose: Pose2DCov, scan: ScanSample, max_range: float) -> None:
        """For every finite beam: add l_free to the cells it crosses and l_occ to the end cell
        (only if range < max_range; a max-range reading is 'no hit', not an obstacle).
        Clamp to [l_min, l_max]. Beam angle in the map frame is pose.theta + angle_min + k * angle_inc."""
        raise NotImplementedError

    def probability(self) -> np.ndarray:
        """p = 1 / (1 + exp(-l)) for the whole grid."""
        raise NotImplementedError

    def occupied(self) -> np.ndarray:
        """Boolean grid: probability > spec.occupied_threshold."""
        raise NotImplementedError


def occupied_iou(estimate: np.ndarray, truth: np.ndarray) -> float:
    """|A and B| / |A or B| over occupied cells; 1.0 if both are empty."""
    raise NotImplementedError
```

Fill it in with the formulas of note 1, then compare your grid with the truth grid from `bench/` using `occupied_iou`.

## Independent practice

### Goal
Deliver the navigation stack of CoreBot: a log-odds occupancy mapper, a lethal/inscribed/inflated costmap, an exact A* planner, a pure-pursuit tracker with limits and stop/replan behaviour, and a 30-episode seeded benchmark that passes the acceptance suite, using only the estimated pose.

### Setup
- Repository: `~/corebot-capstone` (created in CAP01). Work on a branch `cap04`.
- New files: `src/corebot/mapping/occupancy.py`, `mapping/costmap.py`, `planning/astar.py`, `planning/tracker.py`, `planning/navigator.py`, `configs/nav.yaml`, `tests/acceptance/test_cap04.py`.
- Artefacts go in `runs/cap04/`: `map_metrics.json`, `tracker_metrics.json`, `episodes.jsonl`, `dynamic.jsonl`, `hash_run1.json`, `hash_run2.json`, `metrics.json`.
- Commands: `make test` for the unit tests, `python bench/run_bench.py --milestone cap04 --seeds 1000:1030` for the benchmark, `pytest -q tests/acceptance/test_cap04.py` for the gate.
- Pinned versions (put them in `pyproject.toml`): Python 3.11 or newer, `numpy` 1.26 or newer, `pytest` 8. Rendering for the lidar uses ray casts, no GPU needed. Expect the 30-episode benchmark to take 5 to 15 minutes on a laptop CPU.
- Prerequisite artefacts: a CAP03 EKF that publishes `Pose2DCov` and the five `traj_*.npz` trajectories.

### Tasks
1. Implement `OccupancyGrid` (log-odds, Bresenham rays, clamping, max-range handling) and `occupied_iou`; build the map along a seeded survey path and save `map_metrics.json`.
2. Implement `inflate` (distance transform, lethal/inscribed/decay) and choose `inflation_radius` in `configs/nav.yaml` from the formula $r_c+m+2\sigma$; write the numbers and your reasoning in `docs/nav_design.md`.
3. Implement `astar` (8-connected, octile, no corner cutting, optional cost weight) and a `PlanResult`; prove it equal to Dijkstra on 20 fixtures.
4. Implement `PurePursuit` with lookahead, curvature slow-down, velocity, angular and acceleration limits; save `tracker_metrics.json` from 10 reference paths.
5. Implement `Navigator.navigate`: plan, track, rescan every cycle, stop when the inflated cost ahead is lethal, replan up to twice, then return `blocked`.
6. Run the 30-episode benchmark (seeds 1000 to 1029, five layouts) and the 10-trial dynamic-obstacle test; save `episodes.jsonl` and `dynamic.jsonl`.
7. Run the same seed twice, hash the trace, and save both hashes.
8. Write `docs/nav_failures.md`: every failed episode with its reason and what you changed (or why you did not).

### Starter code
```python
"""Interface stubs for CAP04. Fill in the bodies; keep the signatures (the tests import them)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from corebot.interfaces import NavGoal, NavResult, Pose2DCov, WheelCmd


# ---- src/corebot/mapping/costmap.py ---------------------------------------------------------
def inflate(occupied: np.ndarray, resolution: float, inscribed_radius: float,
            inflation_radius: float, decay: float = 4.0) -> np.ndarray:
    """Return a float cost grid in [0, 254].
    255 is never produced here; 254 = 'lethal': occupied cells and every cell closer than
    inscribed_radius to one. Beyond that cost = 253 * exp(-decay * (d - inscribed_radius)),
    down to 0 at inflation_radius. d comes from a Euclidean distance transform (write your own
    two-pass or brushfire version; scipy is allowed only in the library track)."""
    raise NotImplementedError


# ---- src/corebot/planning/astar.py ----------------------------------------------------------
Cell = tuple[int, int]


@dataclass
class PlanResult:
    path: list[Cell] = field(default_factory=list)   # start..goal inclusive, empty if no path
    cost: float = float("inf")                        # sum of step lengths in cells (1 or sqrt 2)
    expanded: int = 0


def astar(cost_grid: np.ndarray, start: Cell, goal: Cell, lethal: float = 254.0,
          cost_weight: float = 0.0) -> PlanResult:
    """8-connected A* with the octile heuristic. Cells with cost >= lethal are blocked; moves
    that cut a blocked corner are not allowed. Step cost = length * (1 + cost_weight * cell_cost / 254).
    With cost_weight = 0 the result must equal Dijkstra's optimum exactly."""
    raise NotImplementedError


# ---- src/corebot/planning/tracker.py --------------------------------------------------------
@dataclass(frozen=True)
class TrackerLimits:
    v_max: float = 0.5        # m/s
    w_max: float = 1.5        # rad/s
    a_max: float = 1.0        # m/s^2 (linear), also used for braking
    lookahead_min: float = 0.25
    lookahead_gain: float = 0.8   # lookahead = max(lookahead_min, gain * |v|)


class PurePursuit:
    def __init__(self, path_xy: np.ndarray, limits: TrackerLimits = TrackerLimits()) -> None:
        """path_xy: (N, 2) map-frame waypoints."""
        raise NotImplementedError

    def command(self, pose: Pose2DCov, v_now: float, dt: float) -> tuple[WheelCmd, bool]:
        """(cmd, done). Choose the lookahead point, compute curvature kappa = 2*y_r / L^2 in the robot
        frame, slow down with curvature, then clip v and w to the limits and v-change to a_max*dt.
        done is True when the last waypoint is within 0.10 m."""
        raise NotImplementedError


# ---- src/corebot/planning/navigator.py ------------------------------------------------------
class Navigator:
    """Glue: grid -> costmap -> A* -> PurePursuit, with stop/replan/blocked logic."""

    def __init__(self, config_path: str = "configs/nav.yaml") -> None:
        raise NotImplementedError

    def navigate(self, goal: NavGoal, env) -> NavResult:
        """Run one navigation episode against `env` (only env.observe() outputs are allowed:
        ScanSample, WheelState -> your EKF pose). NavResult.reason is one of
        'reached', 'timeout', 'blocked', 'collision', 'no_path'."""
        raise NotImplementedError
```

### Tests
```python
# tests/acceptance/test_cap04.py
# Thresholds are provisional starting values; tighten them once your own reference run exists.
import ast
import heapq
import json
import math
import pathlib
import random

import numpy as np
import pytest

from corebot.evalkit import load_episodes, wilson_interval
from corebot.mapping.costmap import inflate
from corebot.planning.astar import astar

RUNS = pathlib.Path("runs/cap04")
SRC = pathlib.Path("src/corebot")


def _dijkstra_cost(free: np.ndarray, start, goal):
    """Reference optimum on an 8-connected grid (corner cutting forbidden), stdlib heap."""
    ny, nx = free.shape
    dist = {start: 0.0}
    heap = [(0.0, start)]
    while heap:
        d, (i, j) = heapq.heappop(heap)
        if (i, j) == goal:
            return d
        if d > dist.get((i, j), math.inf):
            continue
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == dj == 0:
                    continue
                a, b = i + di, j + dj
                if not (0 <= a < nx and 0 <= b < ny and free[b, a]):
                    continue
                if di and dj and not (free[j, a] and free[b, i]):
                    continue
                nd = d + (math.sqrt(2) if di and dj else 1.0)
                if nd < dist.get((a, b), math.inf):
                    dist[(a, b)] = nd
                    heapq.heappush(heap, (nd, (a, b)))
    return math.inf


def _fixture(seed, n=40, density=0.25):
    rng = random.Random(seed)
    free = np.array([[rng.random() > density for _ in range(n)] for _ in range(n)])
    free[0, 0] = free[n - 1, n - 1] = True
    return free


# Automated checks -------------------------------------------------------------------------------
def test_mapping_iou():
    m = json.load(open(RUNS / "map_metrics.json"))
    assert m["cell_size_m"] == 0.05
    assert m["occupied_iou"] >= 0.85        # ~85 % of a clean reference: walls are thin, 1 cell = 5 cm


def test_astar_matches_dijkstra_on_20_fixtures():
    for seed in range(1000, 1020):
        free = _fixture(seed)
        grid = np.where(free, 0.0, 254.0)
        want = _dijkstra_cost(free, (0, 0), (39, 39))
        got = astar(grid, (0, 0), (39, 39))
        if math.isinf(want):
            assert got.path == []
        else:
            assert abs(got.cost - want) < 1e-9          # optimal, hence admissible heuristic


def test_astar_median_time_200x200():
    import time
    free = _fixture(1, n=200, density=0.05)   # sparse clutter like the lab room
    grid = np.where(free, 0.0, 254.0)
    ts = []
    for _ in range(5):
        t = time.perf_counter()
        astar(grid, (0, 0), (199, 199))
        ts.append(time.perf_counter() - t)
    assert sorted(ts)[2] < 0.050             # 50 ms: well under one 10 Hz planning period


def test_tracker_limits_and_error():
    r = json.load(open(RUNS / "tracker_metrics.json"))
    assert r["mean_cross_track_m"] < 0.08 and r["max_cross_track_m"] < 0.20
    assert r["max_v"] <= 0.5 + 1e-9 and r["max_w"] <= 1.5 + 1e-9    # the base limits of CAP02
    assert r["max_accel"] <= 1.0 + 1e-9


# GATE: navigation success and zero collisions -----------------------------------------------------
def test_navigation_benchmark():
    eps = load_episodes(RUNS / "episodes.jsonl")
    assert len(eps) >= 30 and len({e["seed"] for e in eps}) == len(eps)
    assert all(e["seed"] in range(1000, 1000 + len(eps)) for e in eps)
    ok = sum(1 for e in eps if e["outcome"] == "success")
    lo, _ = wilson_interval(ok, len(eps))
    assert ok / len(eps) >= 0.90             # point estimate
    assert lo >= 0.75                        # honest bound: 30 episodes cannot prove more
    assert sum(e["collisions"] for e in eps) == 0
    eff = sorted(e["path_length"] / e["shortest_length"] for e in eps if e["outcome"] == "success")
    assert eff[len(eff) // 2] <= 1.3         # median path efficiency
    assert all(e["duration_s"] <= 90.0 for e in eps if e["outcome"] == "success")


def test_dynamic_obstacle():
    trials = load_episodes(RUNS / "dynamic.jsonl")
    assert len(trials) == 10
    assert all(t["min_clearance_m"] >= 0.15 for t in trials)
    assert all(t["outcome"] in ("success", "blocked") for t in trials)


def test_determinism():
    a = json.load(open(RUNS / "hash_run1.json"))
    b = json.load(open(RUNS / "hash_run2.json"))
    assert a["trace_hash"] == b["trace_hash"]


def test_pipeline_never_imports_simulator_truth():
    banned = {"corebot.sim.world", "corebot.sim.truth"}
    for path in list((SRC / "mapping").glob("*.py")) + list((SRC / "planning").glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not banned.intersection(names), f"{path} imports simulator truth"
            if isinstance(node, ast.Attribute):
                assert node.attr not in ("true_pose", "ground_truth"), f"{path} reads {node.attr}"
```

Thresholds are provisional starting values (see the plan rationale); tighten them once your own reference run exists. One-line rationale per threshold: IoU 0.85 because walls are one or two cells thick and a one-cell shift already costs about 10 points; A* exact because the optimum is known, there is no tolerance to argue about; 50 ms so one planning call fits well inside a 10 Hz loop; cross-track 0.08 m mean because the inflation margin is 0.05 m and the tracker must stay inside it; 0.5 m/s and 1.5 rad/s because those are the CAP02 base limits; 90 % success with a 75 % lower bound because 30 episodes cannot prove more; zero collisions because a collision is a safety failure, not noise; 0.15 m clearance because it exceeds the 0.05 m margin by a clear amount and matches the stopping calculation above; efficiency 1.3 because an inflated, 8-connected path is rarely under 1.1.

Gate checks (these must pass to keep the milestone "done"): **test_navigation_benchmark** and the zero-collision assertion inside it.

### Expected output
```
$ pytest -q tests/acceptance/test_cap04.py
........                                                                 [100%]
8 passed in 21.8s

$ cat runs/cap04/metrics.json
{
  "milestone": "CAP04",
  "map": {"occupied_iou": 0.872, "cell_size_m": 0.05},
  "astar": {"fixtures": 20, "mismatches": 0, "median_ms_200x200": 11.4},
  "tracker": {"mean_cross_track_m": 0.041, "max_cross_track_m": 0.118, "max_v": 0.5, "max_w": 1.31},
  "navigation": {"episodes": 30, "success": 28, "wilson_lo": 0.787, "collisions": 0,
                 "median_path_efficiency": 1.12},
  "dynamic": {"trials": 10, "min_clearance_m": 0.21, "blocked": 1}
}
```

If `pytest` reports `1 failed`, read the assertion message first: the tests print the measured number next to the threshold.

### Extension challenge
Make the planner pose-uncertainty aware: recompute the inflation radius from the live EKF covariance every second and compare success and path efficiency against the fixed radius on the same 30 seeds (report both Wilson intervals). Add a frontier-exploration mode that builds the map without a survey path. Optional real-hardware tier: if you built the CAP02 ESP32 base, drive a 2 m square on a taped floor with wheels on the ground only after a bench test with the wheels lifted, current limited and a fuse in the battery line, and compare the odometry-only path with the sim run. No grade depends on it.

### Library track

Replace your stack with **Nav2** (ROS 2 Jazzy) and compare. Nav2 is a library of planners, controllers and costmaps driven by YAML; the same ideas appear under different names. Use the Nav2 [documentation index](https://docs.nav2.org/index.html) and the TurtleBot 4 configuration as the reference, and check parameter names against the version you install, because they change between releases.

```yaml
# nav2_params.yaml (excerpt, Jazzy; verify names against your installed version)
global_costmap:
  global_costmap:
    ros__parameters:
      resolution: 0.05
      robot_radius: 0.20            # your circumscribed radius r_c
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        inflation_radius: 0.31      # r_c + margin + 2 sigma, the number you derived
        cost_scaling_factor: 4.0    # the decay constant k
planner_server:
  ros__parameters:
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner::NavfnPlanner"
      use_astar: true               # A* instead of Dijkstra
      allow_unknown: false
controller_server:
  ros__parameters:
    controller_plugins: ["FollowPath"]
    FollowPath:
      plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
      desired_linear_vel: 0.5       # v_max of CAP02
      lookahead_dist: 0.45
      max_angular_accel: 3.2
# launch:  ros2 launch nav2_bringup navigation_launch.py params_file:=configs/nav2_params.yaml
# goal:    ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 1.5}}}}"
```

Run the same 30 seeded goals through Nav2 using the `corebot_bridge` package and fill a table: your success rate and Wilson bound, Nav2's, median path efficiency, planning time. Expected: both near 90 % on this simple room; Nav2 wins on recovery behaviours, yours wins on being fully inspectable. This comparison is the "Nav2 baseline" stretch goal for the Distinction grade.

## Verification

Check the numbers by hand before trusting code. The script below uses only the standard library and reproduces the worked example; run it and compare your own grid and planner against these values.

```python
import math

# 1. log-odds update: a cell hit 3 times, another crossed by 5 free beams
l_occ, l_free = math.log(0.7 / 0.3), math.log(0.4 / 0.6)
prob = lambda l: 1 / (1 + math.exp(-l))
print("hit x3   : l = %.3f  p = %.3f" % (3 * l_occ, prob(3 * l_occ)))
print("free x5  : l = %.3f  p = %.3f" % (5 * l_free, prob(5 * l_free)))
print("hit,hit,free: p = %.3f" % prob(2 * l_occ + l_free))

# 2. inflation radii in cells (5 cm cells)
res, r_circ, margin, sigma = 0.05, 0.20, 0.05, 0.03
print("lethal radius   = %d cells" % math.ceil(r_circ / res))
print("inflation radius= %d cells (circumscribed + margin + 2 sigma)" % math.ceil((r_circ + margin + 2 * sigma) / res))

# 3. octile heuristic vs straight-line distance, dx = 30, dy = 12 cells
dx, dy = 30, 12
octile = (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)
print("octile %.2f cells = %.3f m; euclid %.2f cells" % (octile, octile * res, math.hypot(dx, dy)))
assert octile <= (dx - dy) + math.sqrt(2) * dy + 1e-12      # equals the true free-space cost

# 4. pure pursuit: lookahead point (0.42, 0.16) in the robot frame, v = 0.4 m/s
x, y = 0.42, 0.16
L2 = x * x + y * y
kappa = 2 * y / L2
print("L = %.3f m, kappa = %.3f 1/m, w = %.3f rad/s" % (math.sqrt(L2), kappa, 0.4 * kappa))

# 5. stopping distance at v = 0.5 m/s, a = 1.0 m/s^2, 150 ms of latency
v, a, lat = 0.5, 1.0, 0.15
print("stop distance = %.3f + %.3f = %.3f m" % (v * v / (2 * a), v * lat, v * v / (2 * a) + v * lat))


# 6. Wilson lower bound for the success rate
def wilson(s, n, z=1.959964):
    p = s / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


for s in (27, 28, 29, 30):
    lo, hi = wilson(s, 30)
    print("%d/30: %.3f  Wilson 95%% [%.3f, %.3f]" % (s, s / 30, lo, hi))
```

Expected: hit three times gives $p=0.927$; seven-cell inflation; octile 34.97 cells; $\kappa=1.584$; stop distance 0.200 m; for 27/30 the Wilson interval is [0.744, 0.965].

Then verify behaviour: the A* result must equal the Dijkstra cost on every fixture; replay the same seed twice and compare the trace hash; look at the saved map image for doubled walls (a pose error) and for free space marked occupied around the robot (a sign or frame error). Run the AST test and confirm it fails when you deliberately import the truth.

**Scoring.** CAP04 weight is 11 of 100 graduation points. 60 % of the milestone score is automated (weighted fraction of checks, with the navigation benchmark as the gate), 40 % is a self-assessed rubric of four criteria scored 0 to 4: inflation radius justified from the footprint, handling of localisation uncertainty, clarity of failure reasons, and test quality. Graduation needs every gate passing, every milestone at or above 60 and the weighted total at or above 70.

## Failure modes

- Goal inside an inflated or lethal cell: the planner returns no path or loops; snap or report it.
- Plan computed in the wrong frame (odom versus map): the robot drives parallel to the right path.
- Oscillation at a local minimum or at a narrow door: lookahead too short, or replanning every cycle on noisy costs; add hysteresis.
- Control rate slower than the planner, or the reverse: the tracker follows a stale path. Log the age of the path.
- Tracker ignores the angular limit: the base saturates, and the cross-track error test fails only on sharp turns.
- Map drifts because pose errors are not corrected: walls appear doubled. Fix CAP03, do not blur the map.
- Max-range readings treated as obstacles: a wall of phantom cells at the sensor range.
- Ground-truth pose used by accident: the benchmark looks perfect and the AST test fails.
- Reporting 27/30 as "90 %, pass" without the interval.

## Alternatives and trade-offs

Occupancy grids are simple and dense, but memory grows with area; **sparse maps** or OctoMaps scale better. A* is optimal on a grid but paths hug obstacles and zig-zag; **Theta*** or post-smoothing gives straighter paths, **D* Lite** replans cheaply when the map changes, and **RRT\*** or lattice planners respect kinematics better ([E02](/lessons/E02), CMU motion planning notes). Pure pursuit is a two-line geometric rule; **LQR** or **MPC** use a model and handle limits explicitly at the cost of tuning ([C05](/lessons/C05)); the regulated pure-pursuit controller in Nav2 adds speed regulation near obstacles and curves. SLAM (for example slam_toolbox) builds the map and the pose together; this milestone assumes a known room and a separate EKF, which is simpler to test.

## Transfer and retention

CAP04 prepares CAP05 (the base parks where the arm can reach), CAP07 (navigation goals from parsed sentences, and the speed limit near people) and CAP08 (navigation is the largest source of failures to classify). Recall prompts, to answer after a week without notes:

1. Write the log-odds update for a hit and for a free cell and say why the clamp exists.
2. Give the inflation radius formula and the three things it protects against.
3. Why is the octile heuristic admissible and Manhattan not?
4. Derive $\kappa=2y_r/L^2$ from the circle through the origin and the lookahead point.
5. Compute the Wilson lower bound for 28/30 by formula, then explain what changes if you run 100 episodes.

## Exercise answers

1. $l=2\cdot0.847+(-0.405)=1.289$; $p=1/(1+e^{-1.289})=0.784>0.65$, so it is exported as occupied.
2. $r_\text{inflate}=0.22+0.05+2\cdot0.04=0.35$ m $=7.0$ cells (use 7; round up when in doubt).
3. Wilson interval for 27/30: [0.744, 0.965]. The point estimate 90.0 % passes, the lower bound 74.4 % is below 75 %: the gate fails. 28/30 gives [0.787, 0.982] and passes.
4. Manhattan $=34$; Euclid $=\sqrt{24^2+10^2}=26$; octile $=34+(\sqrt2-2)\cdot10=28.14$; true cost $=14+10\sqrt2=28.14$. Euclid and octile are admissible; Manhattan (34) overestimates 28.14 and is not.
5. $L^2=0.09+0.0144=0.1044$; $\kappa=2\cdot(-0.12)/0.1044=-2.30$ m$^{-1}$; $\omega=0.5\cdot(-2.30)=-1.15$ rad/s, inside 1.5. Slow-down speed $\omega_\max/|\kappa|=0.65$ m/s is above 0.5 m/s, so no slow-down is needed.
6. Solve $v^2/2+0.15\,v=1.35$: $v^2+0.3v-2.7=0$, $v=1.5$ m/s. At the 0.5 m/s base limit the robot needs only 0.2 m to stop, so physics is never the limiting factor; the test checks that your logic reacts (stops, replans or reports `blocked`) and that the costmap marks the obstacle in time.
7. Sideways error $\approx3\tan2^\circ=0.105$ m, about two cells. A wall one or two cells thick would be drawn displaced by about its thickness, so occupied overlap drops sharply (IoU can fall below 0.6); the map needs the pose to be good to a cell.
8. Inflation radius $0.22+0.05+0.06=0.33$ m gives free width $0.9-0.66=0.24$ m: passable. With $\sigma=0.08$: $0.22+0.05+0.16=0.43$ m, free width $0.04$ m, less than one 5 cm cell: effectively blocked. A good planner reports the reason (`localisation_uncertain`), slows, or relocalises with landmarks before entering, rather than silently inflating forever.
9. (a) Passing the truth through the `env` object's attributes: grep for `.true_pose`, `ground_truth` (already included), plus a runtime test that wraps `env` in an object exposing only `observe()`. (b) Reading the map from the world's occupancy grid instead of lidar: a test that blanks the lidar and expects the mapped IoU to collapse. (c) Using the true goal-clearance data: a test that perturbs the truth and checks results do not change when only the truth is changed.
10. A good answer lists the seeds, five layouts, failure counts that sum to the number of failures, a table of reasons with one cause each, baseline success of nearly 100 % in the empty room, the boundary case reporting `no_path` or snapping explicitly, and rejection evidence such as success dropping when lidar noise doubles in a way your design did not predict.

## Further reading

- [Occupancy grid mapping (Wikipedia)](https://en.wikipedia.org/wiki/Occupancy_grid_mapping): the log-odds model and inverse sensor models.
- [A* search algorithm (Wikipedia)](https://en.wikipedia.org/wiki/A*_search_algorithm) and [CMU Robotic Motion Planning notes](https://www.cs.cmu.edu/~motionplanning/): admissibility, consistency and planning on grids.
- [Pure pursuit (Wikipedia)](https://en.wikipedia.org/wiki/Pure_pursuit): geometry of the lookahead rule.
- [Nav2 documentation](https://docs.nav2.org/index.html) and the [TurtleBot 4 user manual](https://turtlebot.github.io/turtlebot4-user-manual/): the library track reference.
- [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox): mapping and localisation together.
- [Binomial proportion confidence interval (Wikipedia)](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval): the Wilson interval used by the gates.
- **More practice:** watch Articulated Robotics, "Making robot navigation easy with Nav2 and ROS!", then re-create its `nav2_params.yaml` choices in your own `configs/nav.yaml`.
