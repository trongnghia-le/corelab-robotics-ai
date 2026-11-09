---
{
  "id": "cap06-capstone",
  "module_id": "CAP06",
  "title": "Capstone milestone 6: a learned grasp skill with domain randomisation and honest statistics",
  "summary": "Wrap the grasp primitive as a Gymnasium environment, train PPO and a behaviour-cloning policy on CPU, randomise the physics, and evaluate on held-out seeds with Wilson and bootstrap bounds against the scripted skill.",
  "estimated_minutes": 1920,
  "project_minutes": 1920,
  "prerequisites": [
    "CAP05",
    "RL10",
    "RL12",
    "RL16",
    "RL17",
    "E07",
    "ML07"
  ],
  "source_refs": [
    {
      "title": "Spinning Up in Deep RL",
      "url": "https://spinningup.openai.com/en/latest/"
    },
    {
      "title": "Stable-Baselines3 documentation",
      "url": "https://stable-baselines3.readthedocs.io/en/master/"
    },
    {
      "title": "Gymnasium Env API",
      "url": "https://gymnasium.farama.org/api/env/"
    },
    {
      "title": "Tobin et al., Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World",
      "url": "https://arxiv.org/abs/1703.06907"
    },
    {
      "title": "Henderson et al., Deep Reinforcement Learning that Matters",
      "url": "https://arxiv.org/abs/1709.06560"
    },
    {
      "title": "Binomial proportion confidence interval (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval"
    }
  ],
  "objectives": [
    "Wrap the grasp primitive as a Gymnasium environment with a documented observation, action and reward.",
    "Train PPO and a behaviour-cloning policy on CPU within a stated step and wall-clock budget.",
    "Apply domain randomisation and evaluate on held-out seeds and perturbations.",
    "Report success rates with Wilson and bootstrap bounds and compare honestly with the scripted skill.",
    "Plug the learned skill into the GraspSkill interface behind a safety wrapper."
  ],
  "core_theory": [
    "RL10",
    "RL12",
    "RL16",
    "RL17",
    "E07",
    "ML07",
    "CAP05"
  ],
  "labs": [
    "Train and evaluate a state-based reach-and-grasp policy with and without domain randomisation, run the CAP06 acceptance suite and write the model card."
  ],
  "assessment_refs": [
    "CAP06-diagnostic-v1"
  ],
  "review_prompts": [
    "Explain why the reproducibility gate runs training twice on one CPU thread, and what you would check if it failed.",
    "State which seeds you trained on, which you evaluated on, and why reporting the best of five seeds would be wrong."
  ],
  "extension_refs": [
    "https://huggingface.co/docs/lerobot/il_sim",
    "https://arxiv.org/abs/2304.13705"
  ]
}
---

## Why this matters

Up to CAP05 your robot grasps with a scripted pipeline: perceive, compute inverse kinematics, close the gripper. That pipeline is readable and testable, but every object pose, friction value and delay it was tuned for is an assumption. This milestone asks a different question: can a **learned** skill do the reach-and-grasp primitive as well as the scripted one, and, more importantly, can you **prove it with numbers you would defend in front of a reviewer**?

The learning itself is the easy part: PPO on a small state-based task trains on a laptop CPU in well under an hour. The hard part is the engineering around it: a reward you can explain, a run you can repeat bit for bit, a randomisation range you can justify, evaluation on seeds the policy never saw, and confidence intervals instead of a single lucky number. Those habits are what separate a demo video from a result. You will also meet an uncomfortable truth early: a learned skill that is 90 % successful on the nominal simulator can drop to 60 % when friction changes by 40 %. Domain randomisation is the cheapest tool you have against that, and measuring its effect honestly (including when it does not help) is the real deliverable.

This is milestone 6 of 9, worth **12 of 100 points** in the graduation score. It builds directly on CAP05 (the scripted grasp is your baseline and your demo generator), and it reuses ideas from [RL10 PPO](/lessons/RL10), [RL12 RL experimental design](/lessons/RL12), [RL16 domain randomisation](/lessons/RL16), [RL17 imitation learning](/lessons/RL17), [E07 imitation-based robot policies](/lessons/E07) and [ML07 model evaluation](/lessons/ML07).

## Intuition

Think of the learned skill as a **new implementation of an interface you already have**. CAP05 defined the skill interface `ScriptedGraspSkill.execute(goal, env) -> GraspResult` (called the `GraspSkill` interface in this lesson). Everything above it (the task planner of CAP07, the full-system benchmark of CAP08) does not care whether the result came from inverse kinematics or from a neural network. Your job in CAP06 is to produce a second implementation, train it, and measure it against the first one under identical conditions.

![System architecture of CoreBot Tidy: simulator, firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation and learned skills, the language task layer and the safety supervisor](/lesson-figures/CAP-architecture.svg)

*In the architecture, the learned skill sits in band 4 next to the scripted manipulation block, behind the same `GraspSkill` interface. This milestone fills in the "Learned skill (PPO / BC policy)" box.*

Three ideas carry the whole milestone.

**1. Keep the learned part small.** You are not learning vision, navigation or the whole task. You learn a *primitive*: from a state vector (end-effector to object offset, object position in the arm base frame, joint state, gripper opening), output a small Cartesian step and a gripper command. A small problem trains in minutes, and failures are diagnosable. Vision-based policies (CNN in, action out) are a stretch goal, not the core.

**2. Two ways to learn the same primitive.** *Reinforcement learning* (PPO) discovers behaviour by trial and error against a reward you wrote. *Imitation learning* (behaviour cloning, BC) copies the scripted skill from demonstrations, so no reward is needed but errors compound when the policy drifts away from the states the demonstrations covered. Running both on the same environment and comparing is the educational core of the milestone.

**3. Randomise what you cannot know.** The simulator has one value for object mass and one for friction; the real world (and the held-out test set) has many. Training on a *distribution* of worlds makes the policy robust to the whole distribution, at the price of a harder learning problem. Randomise too little and nothing transfers; randomise too much and the task becomes infeasible and nothing is learned.

![Learned grasp skill: a domain randomiser feeds a Gymnasium grasp environment and a PPO or behaviour-cloning policy during training; a separate evaluation harness on held-out seeds and perturbations produces Wilson bounds and a comparison with the scripted skill](/lesson-figures/CAP06.svg)

*Training and evaluation are separate pipelines with separate seeds. Anything you tune after looking at evaluation results is training.*

## Theory and derivation

These are the integration notes: the few formulas, interfaces and rules that matter here, each tied to the topic where you learned it.

### 1. The environment is a contract ([RL09](/lessons/RL09), [RL10](/lessons/RL10), Gymnasium)

A Gymnasium environment has `reset(seed=...) -> (obs, info)` and `step(action) -> (obs, reward, terminated, truncated, info)`. Fix and document five things in `docs/reward_design.md`: observation vector (with units and scaling), action vector (what 1.0 means physically), episode length, termination versus truncation (a 60-step time limit is a *truncation*, not a failure of the task state; PPO's value bootstrap treats them differently), and the reward terms. All randomness must flow from the `seed` passed to `reset`, using one `numpy.random.Generator`; otherwise no result can be repeated.

### 2. Reward shaping and its traps ([RL10](/lessons/RL10), [RL12](/lessons/RL12))

A typical reach-and-grasp reward is a sum of terms:
$$r_t=-w_d\,\lVert x_{ee}-x_{obj}\rVert-w_a\lVert a_t\rVert^2-w_t+w_g\,\mathbb 1[\text{grasp}]+w_\ell\,\mathbb 1[\text{lift}].$$
The distance term makes learning *possible* (dense signal). The one-off bonuses define what *success* means. The step cost $w_t$ makes finishing early better than waiting. The classic failure is **reward hacking**: if every step pays a positive amount for being near the object (for example $e^{-10d}$), hovering for 60 steps can out-earn a real grasp. Write the reward as costs, add a small time penalty, and always inspect the *behaviour*, not only the return.

### 3. Discounting and time limits ([RL09](/lessons/RL09))

With discount $\gamma$ the effective horizon is about $1/(1-\gamma)$ steps. For a 60-step episode, $\gamma=0.98$ (horizon about 50) is a sensible start: the lift bonus is still visible from the first step. A $\gamma$ of 0.9 (horizon 10) would make the lift bonus almost invisible during approach.

### 4. Domain randomisation as a distribution ([RL16](/lessons/RL16), Tobin et al.)

Training samples a perturbation $\xi\sim p(\xi)$ at every `reset`: mass scale, friction scale, action delay, and for vision lighting and camera jitter. The policy maximises $\mathbb E_{\xi}[J(\pi,\xi)]$. Design rules: (a) the nominal world must be inside the range; (b) the range must be physically plausible; (c) record the sampled $\xi$ in every episode record; (d) evaluate on a *held-out* perturbation set and on the nominal set, and report both. Action delay of $d$ ms at a 10 Hz control rate means $\lceil d/100\rceil$ steps of buffering for the command, which you implement as a FIFO queue in `step`.

### 5. Imitation learning and compounding error ([RL17](/lessons/RL17), [E07](/lessons/E07))

Behaviour cloning minimises $\mathbb E_{(s,a)\sim d_{\text{expert}}}\lVert\pi(s)-a\rVert^2$. At test time the policy visits states from its *own* distribution. Ross, Gordon and Bagnell (the DAgger paper) show that with per-step error $\epsilon$ and horizon $T$ the worst-case cost grows like $\epsilon T^2$ for cloning versus $\epsilon T$ for methods that train on the learner's own state distribution. Practical consequences: split train and validation by **demonstration**, not by timestep (neighbouring timesteps leak); demos and policy must share the **same action space**; and held-out MSE alone is not enough, you must also run the policy in closed loop.

### 6. Statistics you must report ([ML07](/lessons/ML07), [RL12](/lessons/RL12))

For $k$ successes in $n$ independent episodes the 95 % **Wilson interval** is
$$\frac{\hat p+\frac{z^2}{2n}\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}},\qquad z=1.96.$$
It behaves sensibly near 0 and 1 and for small $n$ (the normal approximation does not). Rules used by every acceptance test in this capstone: seeds are `range(1000, 1000+N)` for evaluation and below 1000 for training; claims about a success rate use the **lower** bound; for a learning curve across training seeds you report each seed, the mean and a bootstrap interval, never the best seed ([Henderson et al.](https://arxiv.org/abs/1709.06560) show that this single habit changes many published conclusions). `evalkit.wilson_interval` and `evalkit.bootstrap_ci` (from CAP01) implement both.

### 7. Safety wrapper

A learned policy can output anything. Wrap it: clip the action to $[-1,1]$, convert to a Cartesian step of at most 1.5 cm, project the target into a **workspace box** (above the table, inside the reach of the SO-101), and count (never silently swallow) any violation that the guard had to correct. The acceptance test demands zero *uncorrected* violations; log corrections too, because a policy that needs the guard every step has not learned the task.

## Worked example

These are **illustrative values** for what a passing set of artefacts could look like, not output of a real run. Your own numbers will differ; the *shape* of the evidence is what matters.

### Budget, nominal and perturbed evaluation, behaviour cloning and a paired comparison

**Problem.** A PPO study uses 4 vectorised environments at about 366 environment steps per second (laptop CPU, one torch thread), with limits of 2 M steps and 2 h. Five PPO seeds are each evaluated on 100 episodes (seeds 1000-1499) with 93, 95, 92, 96 and 94 successes. A domain-randomised (DR) policy and a nominal-only policy are compared on 100 perturbed episodes (mass 0.7-1.3, friction 0.6-1.4, +40 ms delay, seeds 1500-1599): 81 and 58 successes. A behaviour-cloning (BC) policy has held-out MSE 0.011 against 0.093 for a constant-mean baseline (limit ratio 0.2) and 71/100 closed-loop successes; the demo sweep gives MSE 0.041, 0.026, 0.017, 0.011 for 50, 100, 200, 500 demonstrations. The scripted CAP05 skill scores 97/100 on the same 100 seeds.

- (a) Does a 1.5 M-step run of 4100 s fit the budget?
- (b) Summarise the nominal evaluation (mean, minimum, pooled rate and its 95 % Wilson interval).
- (c) Compute the Wilson intervals of 81/100 and 58/100 and a two-proportion $z$ for the difference; what may be claimed?
- (d) Check the BC ratio and the demo sweep, and give the Wilson interval of 71/100.
- (e) What does a paired comparison with the scripted skill (97/100) need, and what can already be said?

**Solution.**

1. *Throughput.* $1.5\times10^6/4100=365.9\approx366$ steps/s, consistent with the stated rate. $4100\ \text{s}/3600=1.14$ h. Both $1.5\,\text{M}\le2\,\text{M}$ steps and $1.14\,\text{h}\le2$ h hold; the same rate would need $2\times10^6/366=5465$ s $=1.52$ h for 2 M steps.
2. *Nominal evaluation.* Mean $=(93+95+92+96+94)/5=94\ \%$, minimum 92 %, pooled $470/500=0.940$.
3. *Wilson interval.* For $k/n$ with $z=1.96$: $\tilde p=(\hat p+z^2/2n)/(1+z^2/n)$, half-width $z\sqrt{\hat p(1-\hat p)/n+z^2/4n^2}/(1+z^2/n)$. For $470/500$ this gives $[0.916,\,0.958]$. For comparison $27/30$ gives $[0.744,\,0.965]$: about 17 times fewer episodes, an interval about five times wider (0.221 against 0.042).
4. *Perturbed intervals.* $81/100\to[0.722,\,0.875]$ and $58/100\to[0.482,\,0.672]$. The intervals do not overlap ($0.722>0.672$).
5. *Two-proportion $z$.* Pooled $\bar p=(81+58)/200=0.695$; $\text{SE}=\sqrt{\bar p(1-\bar p)\cdot2/100}=\sqrt{0.695\cdot0.305\cdot0.02}=0.0651$; $z=(0.81-0.58)/0.0651=3.53\approx3.5$. This supports "DR helped on this perturbation set", for **one** training seed per arm; a careful report says so and adds seeds if the claim matters.
6. *BC ratio.* $0.011/0.093=0.118\approx0.12\le0.2$: passes. The sweep 0.041, 0.026, 0.017, 0.011 decreases at every step, so it is monotone as expected.
7. *BC closed loop.* $71/100$ has Wilson interval $[0.615,\,0.790]$: lower than PPO (pooled 0.940) and lower than the scripted skill (0.97). This is a normal outcome of imitation without correction, and exactly what the comparison should show.
8. *Paired comparison.* Two separate rates ignore that both skills face the same seeds. Count $b$ = episodes where only the scripted skill succeeded and $c$ = episodes where only PPO succeeded; the exact test (`evalkit.paired_mcnemar`) uses only $b$ and $c$. Assumption added here (the original gives no pair counts): the PPO arm is training seed 0 (93/100) on the same 100 seeds. Then $b-c=97-93=4$. The smallest possible $b+c$ is 4 ($b=4$, $c=0$), giving $p=2\cdot(1/2)^4=0.125>0.05$; any larger $b+c$ with the same difference gives a larger $p$ (for example $b=6$, $c=2$: $p=0.289$). So a 4-point gap on 100 paired seeds can never be significant, and the report should say the two skills are not separated.

```python
from corebot.evalkit import wilson_interval        # CAP01: python3 evalkit.py also runs a self-test

for k, n in [(27, 30), (470, 500), (81, 100), (58, 100)]:
    lo, hi = wilson_interval(k, n)
    print(f"{k}/{n}: point {k / n:.3f}, 95% Wilson [{lo:.3f}, {hi:.3f}]")
```


Output (illustrative, computed from the formula above):

```text
27/30: point 0.900, 95% Wilson [0.744, 0.965]
470/500: point 0.940, 95% Wilson [0.916, 0.958]
81/100: point 0.810, 95% Wilson [0.722, 0.875]
58/100: point 0.580, 95% Wilson [0.482, 0.672]
```


| Training seed | Successes / 100 |
|---|---|
| 0 | 93 |
| 1 | 95 |
| 2 | 92 |
| 3 | 96 |
| 4 | 94 |

| Policy | Successes / 100 | Wilson 95 % |
|---|---|---|
| PPO with domain randomisation | 81 | [0.722, 0.875] |
| PPO without (nominal-only training) | 58 | [0.482, 0.672] |

**Check.** The four Wilson lines in the code output match the hand formula of step 3 (the script uses the same formula, and the values above were recomputed independently to three decimals). The $z$ test agrees with the interval test: the lower end 0.722 of the DR interval exceeds the upper end 0.672 of the other by 0.050, and $z=3.5$ corresponds to a two-sided $p\approx0.0004$. Sanity bound for (e): the exact paired test cannot return $p<0.05$ unless $b+c\ge6$ with $c=0$ (for example $b=6$, $c=0$ gives $p=0.031$), which needs a gap of at least 6 points.

**Takeaway.** Report every rate with its Wilson interval and compare policies on the same seeds; an interval, a test and an honest count of training seeds say what a point estimate cannot.

## Exercises

1. **(Easy)** A learner reports 27 successes in 30 held-out episodes. Compute the 95 % Wilson interval and decide whether the claim "success is at least 80 %" is supported.
2. **(Easy)** Training ran at 366 environment steps per second. How long do 2 M steps take, and does that fit the 2 h wall-clock limit with room for evaluation?
3. **(Easy)** A reward pays $e^{-10d}$ per step for the end-effector distance $d$ to the object, plus a one-off 12 for lifting. A policy hovers at $d=2$ cm for all 60 steps. Compute its return and explain why this may beat grasping.
4. **(Medium)** Training randomises mass in $[0.8,1.2]$, friction in $[0.7,1.3]$ and delay in $\{0,10,20,30\}$ ms. The held-out set uses mass $[0.7,1.3]$, friction $[0.6,1.4]$ and delay exactly 40 ms. What fraction of held-out episodes lie fully inside the training ranges? What would you change?
5. **(Medium)** DR policy: 81/100 on the perturbed set. Non-DR policy: 58/100. One training seed each. Which conclusion is justified and which is not?
6. **(Medium)** A BC policy has held-out MSE of 0.011 (excellent) but only 71 % closed-loop success. Give two explanations and one fix for each.
7. **(Medium)** Your demos store joint-position targets, but the PPO policy outputs end-effector deltas. Describe a cheap test that would catch the mismatch before any training.
8. **(Hard)** The reproducibility gate fails: two identical runs differ by $3\times10^{-3}$ in logged evaluation return. List the likely causes in the order you would check them.
9. **(Hard)** Five PPO seeds give 96, 61, 90, 88 and 20 successes out of 100. Compute the mean, decide whether the learning gate (mean at least 90 %, minimum at least 80 %) passes, and say what a responsible report contains.
10. **(Hard, mini-project)** Design and run the demo-count sweep (50, 100, 200, 500 demonstrations): which quantities do you log, which baseline and boundary case do you include, and what observation would make you reject "more demos always help"?

## Reference implementation

The module to write first is `learning/envs.py`: it is the contract everything else depends on. Below is the skeleton; the docstrings contain the decisions you must make and write down.

```python
# src/corebot/learning/envs.py  (skeleton: fill in the NotImplementedError bodies)
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np

from corebot.learning.randomize import DomainRandomizer, Perturbation


@dataclass(frozen=True)
class RewardWeights:
    """Every term is documented in docs/reward_design.md. Change them there first."""
    reach: float = 1.0        # -w * ||ee - obj||  (dense, bounded by workspace size)
    grasp: float = 2.0        # one-off bonus when both fingers touch the object
    lift: float = 10.0        # one-off bonus when the object is >= 5 cm above the table
    action: float = 0.01      # -w * ||a||^2  (discourages jitter)
    time: float = 0.005       # -w per step (discourages hovering near the object)


class GraspReachEnv(gym.Env):
    """State-based reach-and-grasp primitive for the SO-101 (the 'learned skill').

    Observation (float32, shape (17,), roughly normalised to [-1, 1]):
        ee_pos - obj_pos (3), obj_pos in arm_base frame (3), joint positions (5),
        joint velocities (5, scaled), gripper opening (1)
    Action (float32, shape (4,), in [-1, 1]): ee delta xyz (x 1.5 cm per step) and gripper command.
    Episode: 60 steps at 10 Hz control (10 physics substeps of 1 ms each), truncated at 60.
    Success: object >= 5 cm above the table and still held 10 steps later.
    """

    metadata = {"render_modes": []}

    def __init__(self, randomizer: DomainRandomizer | None = None,
                 weights: RewardWeights = RewardWeights(), max_steps: int = 60) -> None:
        super().__init__()
        raise NotImplementedError("load models/corebot.xml, build spaces, store the randomizer")

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        """Seed ALL randomness from `seed` (np.random.Generator), sample a Perturbation,
        apply it to the model, place the object, return (obs, info)."""
        raise NotImplementedError

    def step(self, action: np.ndarray):
        """Clip the action, pass it through the action-delay queue and the workspace guard
        (never leave the safe box, never command below the table), integrate physics,
        compute reward terms, return (obs, reward, terminated, truncated, info).
        info must contain: success, joint_limit_violations, table_collisions."""
        raise NotImplementedError

    def _obs(self) -> np.ndarray:
        raise NotImplementedError

    def _apply(self, p: Perturbation) -> None:
        """Write p into model.body_mass / model.geom_friction before the episode starts."""
        raise NotImplementedError
```

Fill it in this order: `_obs` (print one observation and check units by hand), `reset` (seed, perturbation, object placement; call twice with the same seed and assert equal observations), `step` without reward (scripted policy should reach the object), then the reward terms one at a time.

## Independent practice

### Goal
Produce a learned reach-and-grasp skill that meets the CAP06 acceptance suite: reproducible PPO training on CPU, at least 90 % mean nominal success, robust success on a held-out perturbation set, a behaviour-cloning policy compared with a constant baseline, zero guard violations, and a drop-in `GraspSkill`. Write down what the numbers do **not** show.

### Setup
Work in `~/corebot-capstone` (created in CAP01) on a new branch. Everything runs on CPU. The state-based environment needs no rendering; vision-based variants need `MUJOCO_GL=egl` (or `osmesa`, slower). Pin the versions you use in `pyproject.toml`; the lines below are examples to check against the current releases on the day.

```bash
cd ~/corebot-capstone
git checkout -b cap06-learned-skills
python3 -m venv .venv && . .venv/bin/activate
pip install -e .                             # then pip install the pins (example, check on the day):
#   mujoco>=3.2,<4  gymnasium>=0.29,<2  stable-baselines3>=2.3,<3  torch (CPU wheel)  numpy  pytest
export MUJOCO_GL=egl                         # osmesa if EGL is missing (state-based env needs no rendering)
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1   # single thread: needed for the reproducibility gate
mkdir -p runs/cap06 docs
python -m corebot.learning.train_ppo --seed 0 --steps 20000 --dr off --out runs/cap06/repro_a.json
python -m corebot.learning.train_ppo --seed 0 --steps 20000 --dr off --out runs/cap06/repro_b.json
pytest -q tests/acceptance/test_cap06.py
```

Runtime hints: PPO at 4 environments typically runs a few hundred steps per second on a laptop CPU, so budget 1 to 2 hours for the full 5-seed study (run seeds in sequence, not in parallel, if you want clean wall-clock numbers). If your first 20 k-step run shows no learning at all, debug the environment with the scripted policy before touching hyperparameters.

### Tasks
1. **`learning/envs.py`**: `GraspReachEnv` as above, with `docs/reward_design.md` (observation, action, each reward term and why, termination/truncation).
2. **`learning/randomize.py`**: `DomainRandomizer.sample(rng)` for mass, friction and delay (plus light and camera jitter for the vision variant). Log the sampled values in every episode.
3. **`learning/train_ppo.py`**: your own PPO from RL10 or Stable-Baselines3 (see Library track). CLI as specified, one thread, seeds < 1000 for training, evaluation on seeds >= 1000. Output `runs/cap06/ppo_seed{0..4}.json`, `repro_a.json`, `repro_b.json`, and a `--dr on|off` switch.
4. **`learning/bc.py`**: 500 scripted demonstrations, MLP, split by demonstration, demo-count sweep over 50/100/200/500, closed-loop evaluation on 100 seeds. Output `bc_summary.json`.
5. **Evaluation**: `eval_nominal.jsonl` and `eval_perturbed.jsonl` (one JSON per episode: policy, seed, success, perturbation values, violation counters), `summary.json` (counts and Wilson intervals), `meta.json` (steps, wall clock, device).
6. **`learning/skill.py`**: `LearnedGraspSkill` implementing the same `execute(goal, env)` signature as `ScriptedGraspSkill` (the CAP05 interface), wrapped by the safety guard.
7. **Model card** (`docs/model_card_cap06.md`, one page): intended use, training data/seeds, DR ranges, metrics with intervals, known failure cases, and what was *not* tested.
8. **Lessons learned** (one page) for the CAP09 report: the single biggest surprise and the first thing you would change.

### Starter code

```python
# src/corebot/learning/randomize.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Perturbation:
    mass_scale: float
    friction_scale: float
    delay_ms: int
    light_gain: float = 1.0       # vision only (CAP05 pipeline), unused by the state-based env
    cam_jitter_px: float = 0.0    # vision only


@dataclass(frozen=True)
class DomainRandomizer:
    """TRAIN ranges are deliberately narrower than the HELD-OUT evaluation ranges on some axes."""
    mass: tuple[float, float] = (0.8, 1.2)
    friction: tuple[float, float] = (0.7, 1.3)
    delay_ms: tuple[int, int] = (0, 30)

    def sample(self, rng: np.random.Generator) -> Perturbation:
        """Uniform draws inside the ranges; delay is an integer multiple of 10 ms."""
        raise NotImplementedError


# src/corebot/learning/train_ppo.py  (CLI contract used by the acceptance tests)
#   python -m corebot.learning.train_ppo --seed 0 --steps 20000 --dr off --out runs/cap06/repro_a.json
# The JSON it writes must contain: seed, steps, device, torch_threads, eval_return,
# eval_success, eval_n, total_env_steps, wall_clock_s.
def main(argv: list[str] | None = None) -> None:
    """Parse args, set torch.set_num_threads(1), seed python/numpy/torch/env, train, then evaluate
    on seeds >= 1000 (never on training seeds) and write the JSON."""
    raise NotImplementedError


# src/corebot/learning/bc.py
def collect_demos(n_demos: int, seed: int):
    """Run the scripted CAP05 grasp in GraspReachEnv-compatible action space and return
    (obs[N, 17], act[N, 4]). Demos must use the SAME action space as the policy."""
    raise NotImplementedError


def train_bc(obs, act, epochs: int = 200, seed: int = 0):
    """Small MLP (2 x 64), MSE loss, 80/20 split by DEMO (not by timestep), returns model and
    held-out MSE. Also return the constant-mean baseline MSE for the same split."""
    raise NotImplementedError
```

### Tests
Create `tests/acceptance/test_cap06.py`. Gates are the tests for reproducibility, learning and robustness.

```python
# tests/acceptance/test_cap06.py  (run from the repo root:  pytest -q tests/acceptance/test_cap06.py)
import inspect, json, pathlib
from corebot.evalkit import wilson_interval, bootstrap_ci

RUN = pathlib.Path("runs/cap06")
TRAIN_SEEDS_BELOW = 1000          # training uses seeds < 1000; evaluation uses seeds >= 1000

def _json(name):
    return json.loads((RUN / name).read_text())

def _episodes(name):
    return [json.loads(l) for l in (RUN / name).read_text().splitlines() if l.strip()]

def _rate(eps):
    return sum(e["success"] for e in eps) / len(eps)

# 1. reproducibility (GATE)
def test_ppo_is_reproducible_on_cpu():
    a, b = _json("repro_a.json"), _json("repro_b.json")
    assert a["seed"] == b["seed"] == 0 and a["steps"] == b["steps"] == 20000
    assert a["device"] == b["device"] == "cpu" and a["torch_threads"] == b["torch_threads"] == 1
    assert abs(a["eval_return"] - b["eval_return"]) < 1e-6

# 2. learning on the nominal environment (GATE)
def test_ppo_nominal_success():
    seeds = [_json(f"ppo_seed{s}.json") for s in range(5)]
    assert all(p["eval_n"] >= 100 for p in seeds)
    rates = [p["eval_success"] / p["eval_n"] for p in seeds]
    assert sum(rates) / 5 >= 0.90
    assert min(rates) >= 0.80                          # reporting the best of N seeds is not allowed
    eps = [e for e in _episodes("eval_nominal.jsonl") if e["policy"] == "ppo"]
    assert len(eps) >= 500 and min(e["seed"] for e in eps) >= TRAIN_SEEDS_BELOW
    lo, _ = bootstrap_ci([float(e["success"]) for e in eps], n=2000, seed=0)
    assert lo >= 0.80

# 3. robustness to held-out perturbations (GATE)
def test_domain_randomisation_robustness():
    eps = _episodes("eval_perturbed.jsonl")
    for e in eps:                                      # the held-out set really is the stated one
        assert 0.7 <= e["mass_scale"] <= 1.3 and 0.6 <= e["friction_scale"] <= 1.4 and e["delay_ms"] == 40
        assert e["seed"] >= TRAIN_SEEDS_BELOW
    dr = [e for e in eps if e["policy"] == "ppo_dr"]
    base = [e for e in eps if e["policy"] == "ppo_nodr"]
    assert len(dr) >= 100 and len(base) >= 100
    assert _rate(dr) >= 0.70 and _rate(dr) >= _rate(base)
    summary = _json("summary.json")["perturbed"]       # CIs reported, and they match the episodes
    for name, group in (("ppo_dr", dr), ("ppo_nodr", base)):
        lo, hi = wilson_interval(sum(e["success"] for e in group), len(group))
        assert abs(summary[name]["wilson"][0] - lo) < 1e-3 and abs(summary[name]["wilson"][1] - hi) < 1e-3

# 4. behaviour cloning
def test_bc_beats_constant_baseline_and_sweep_exists():
    bc = _json("bc_summary.json")
    assert bc["heldout_mse"] <= 0.2 * bc["const_baseline_mse"]
    assert bc["closed_loop_n"] >= 100 and bc["closed_loop_success"] / bc["closed_loop_n"] >= 0.60
    assert sorted(int(k) for k in bc["sweep"]) == [50, 100, 200, 500]
    vals = [bc["sweep"][k]["heldout_mse"] for k in sorted(bc["sweep"], key=int)]
    assert all(b <= a * 1.10 for a, b in zip(vals, vals[1:])) or bc.get("sweep_note")   # monotone or explained

# 5. compute budget
def test_budget_respected():
    m = _json("meta.json")
    assert m["total_env_steps"] <= 2_000_000 and m["wall_clock_s"] <= 7200 and m["device"] == "cpu"

# 6. safety wrapper
def test_no_limit_or_table_violations():
    for name in ("eval_nominal.jsonl", "eval_perturbed.jsonl"):
        assert sum(e["joint_limit_violations"] + e["table_collisions"] for e in _episodes(name)) == 0

# 7. integration: the learned skill is a drop-in replacement of ScriptedGraspSkill
def test_learned_skill_implements_grasp_skill():
    from corebot.manipulation.grasp import ScriptedGraspSkill
    from corebot.learning.skill import LearnedGraspSkill
    want = list(inspect.signature(ScriptedGraspSkill.execute).parameters)
    assert list(inspect.signature(LearnedGraspSkill.execute).parameters) == want
```

Thresholds are provisional starting values (see the plan rationale); tighten them once your own reference run exists. Rationale, one line each:

- Reproducibility `|diff| < 1e-6`: on one machine, one thread, identical seeds must agree to float precision; anything larger means hidden nondeterminism.
- Mean success >= 0.90, bootstrap lower bound >= 0.80, every seed >= 0.80: a state-based primitive on a 4 m room scale is easy enough that 90 % is reachable, and the per-seed floor blocks "best of N".
- Robustness >= 0.70 and at least the non-DR rate: a drop of 20 points under a 30-40 % physics change is acceptable; DR must not make things worse.
- BC held-out MSE <= 0.2 x constant baseline and closed-loop >= 0.60: cloning must clearly beat "predict the mean", and a weaker closed-loop number than PPO is expected.
- Budget 2 M steps / 2 h: keeps the milestone feasible on a laptop CPU and forces efficient experiments.
- Zero violations: the guard is a hard requirement, not a score.

### Expected output
When all artefacts exist, `pytest -q` prints:

```text
.......                                                                  [100%]
7 passed in 3.42s
```

A trimmed, illustrative `runs/cap06/metrics.json` (the summary you paste into the CAP09 report):

```json
{
  "milestone": "CAP06",
  "git_hash": "3fa91c2",
  "device": "cpu",
  "total_env_steps": 1500000,
  "wall_clock_s": 4100,
  "nominal": {"policy": "ppo", "seeds": 5, "episodes_per_seed": 100, "mean_success": 0.94, "bootstrap_lo": 0.92},
  "perturbed": {
    "ppo_dr":   {"k": 81, "n": 100, "wilson": [0.722, 0.875]},
    "ppo_nodr": {"k": 58, "n": 100, "wilson": [0.482, 0.672]}
  },
  "bc": {"heldout_mse": 0.011, "const_baseline_mse": 0.093, "closed_loop_success": 71, "closed_loop_n": 100},
  "violations": {"joint_limit": 0, "table_collision": 0}
}
```

### Extension challenge
Stretch (counts toward the Distinction criterion): train a **LeRobot ACT** policy on a simulated demonstration dataset following the [LeRobot imitation-learning-in-sim guide](https://huggingface.co/docs/lerobot/il_sim). It is slow on CPU; a free Colab GPU session is acceptable, and you should report the compute used. Compare against your BC policy on the same 100 seeds with Wilson bounds. A second stretch: vision-based PPO or BC with a small CNN at 64x64, with lighting and camera-jitter randomisation switched on and an ablation table.

Optional real-hardware tier: if you own an SO-101, teleoperate it with LeRobot, record a small dataset, and report a **real versus simulated** success table with the same statistics. Follow the electrical and power safety rules of HW03 (stay at or below 12 V, no unattended motion), keep a hand near the power switch, and remember that a hardware tier can never substitute for a failing gate.

### Library track
Replace your own PPO with Stable-Baselines3 and compare learning curves and wall-clock. The SB3 docs list tips on normalisation and evaluation ([RL tips](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html)). This snippet needs `pip install stable-baselines3 torch gymnasium` and your environment:

```python
# Needs: pip install "stable-baselines3>=2.3,<3" "gymnasium>=0.29,<2" torch (CPU build)
import json
import time

import torch
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize

from corebot.learning.envs import GraspReachEnv
from corebot.learning.randomize import DomainRandomizer

torch.set_num_threads(1)                      # needed for bit-for-bit repeatability on CPU
t0 = time.time()
seed = 0
venv = make_vec_env(lambda: GraspReachEnv(DomainRandomizer()), n_envs=4, seed=seed)
venv = VecNormalize(venv, norm_obs=True, norm_reward=True)       # unnormalised observations are a classic failure
model = PPO("MlpPolicy", venv, n_steps=512, batch_size=256, learning_rate=3e-4,
            gamma=0.98, gae_lambda=0.95, ent_coef=0.0, seed=seed, device="cpu", verbose=0)
model.learn(total_timesteps=20_000)

venv.training = False                         # freeze normalisation statistics for evaluation
venv.norm_reward = False
venv.seed(1000)                               # evaluation seeds start at 1000
obs, ok, n = venv.reset(), 0, 0
while n < 100:
    action, _ = model.predict(obs, deterministic=True)
    obs, _, done, info = venv.step(action)
    for i, d in enumerate(done):
        if d:
            n += 1
            ok += bool(info[i].get("success", False))
print(json.dumps({"seed": seed, "eval_success": ok, "eval_n": n, "wall_clock_s": round(time.time() - t0)}))
```

Expected: one JSON line with `eval_n` equal to 100 and a success count that, after 20 k steps, is usually far below the 300 k-step result in the worked example. That gap is normal; use this run only for the reproducibility check.

## Verification

Check each layer before trusting the next. **Environment:** the scripted policy succeeds at least 95 % of the time in `GraspReachEnv` (otherwise you are asking PPO to solve an infeasible task); `reset(seed=s)` twice gives identical observations; a random policy scores near zero. **Training:** run 20 k steps twice and compare the logged returns (the gate), then plot the learning curve per seed. **Evaluation:** evaluation seeds must not appear in any training log; recompute one Wilson interval by hand. **Behaviour:** watch ten evaluation episodes, including the failures, and write what the failure looks like (missed grasp, dropped object, guard clipping). A policy with a good return and a bad behaviour is a reward bug.

**Scoring.** CAP06 carries weight **12 of 100**. Its score is 60 % automated (weighted fraction of the seven checks; the gates are reproducibility, learning and robustness) and 40 % human rubric (four criteria scored 0-4 with linked evidence: reward design reasoning, no cherry-picked seeds, honest negative results, comparison with the scripted baseline). You may cross-check your self-scores with the review prompt below, which receives the code and artefacts and not your own verdict:

```text
You are reviewing a robotics student's CAP06 milestone. Below are the files envs.py, randomize.py,
train_ppo.py, bc.py, docs/reward_design.md and runs/cap06/summary.json. Do NOT use the student's own
verdict. For each criterion give a score 0-4 (0 missing, 2 works but unexplained, 4 justified, tested and
critiqued), quote the evidence (file and line or number) and name the single biggest weakness:
1. Reward design reasoning  2. Seeds and statistics honesty  3. Negative results and limits  4. Comparison with the scripted skill
```

Graduation needs every gate to pass, a milestone score of at least 60, and a weighted total of at least 70 across the capstone. A failed gate keeps the milestone "in progress"; it does not lock the app.

## Failure modes

- **Reward hacking:** the policy hovers near the object or exploits the lift bonus without holding. Cure: costs instead of positive per-step pay, time penalty, watch videos.
- **Sparse reward without shaping:** nothing is learned in 100 k steps. Cure: dense distance term and a curriculum from easy placements.
- **Unnormalised observations:** mixed scales (metres next to joint velocities) stall learning. Cure: normalise, and freeze the statistics at evaluation.
- **Evaluating on training seeds:** inflates success. Cure: disjoint seed ranges, checked by a test.
- **DR ranges that make the task infeasible:** the policy learns nothing or a timid average behaviour. Cure: widen gradually and check that the scripted policy still succeeds at the extremes.
- **BC compounding error and action-space mismatch** between demos and policy. Cure: replay-test the demos, add noise to demos, relabel on-policy states.
- **Reporting the best of N seeds,** or tuning on the evaluation set. Cure: report all seeds and freeze hyperparameters before evaluation.
- **Hidden nondeterminism:** multi-threaded torch, unseeded `numpy`, a dataloader shuffle. Cure: one thread, one `Generator`, seed everything.
- **Guard doing the work:** the policy depends on action clipping to succeed. Cure: log the correction counts.

## Alternatives and trade-offs

*Learned versus scripted.* The scripted skill is more predictable and needs no training; the learned skill can absorb effects you did not model, but only inside the distribution it saw. *PPO versus BC.* PPO needs a reward and many steps but can exceed the demonstrator; BC needs good demonstrations and a matching action space but is cheap and sample-efficient. *State-based versus vision-based.* State-based is fast and diagnosable; vision-based is the real target and multiplies compute by roughly an order of magnitude on CPU. *SAC or TD3 instead of PPO:* often more sample-efficient on continuous control, but PPO is the one you studied. *ACT/diffusion policies* handle multimodal demonstrations and action chunks better than a plain MLP but need more data and compute. *Own PPO versus Stable-Baselines3:* write your own once to understand it, use the library for experiments you want to trust.

## Transfer and retention

This milestone feeds CAP07 (the task layer calls a `GraspSkill` and must handle its failures with retries) and CAP08 (the full-system benchmark runs scripted and learned skills side by side, and the sim-to-real gap analysis reuses your perturbation sets and statistics). Outside the capstone the same habits apply to any learning result: seeds, held-out evaluation, intervals, baselines.

Recall prompts for a week from now: (1) Write the Wilson interval for 27/30 without notes and say what it implies. (2) Why does the BC bound grow like $\epsilon T^2$? (3) Which three things make a PPO run non-reproducible on a CPU? (4) What does "held-out" mean for seeds versus for perturbation ranges? (5) Why is the safety wrapper counted, not just applied?

## Exercise answers

1. $\hat p=0.90$. Wilson: $[0.744,0.965]$. The lower bound is below 0.80, so "at least 80 %" is **not** supported at 95 % confidence with 30 episodes, although the point estimate looks good. About 70 episodes (63 successes) would be needed for the lower bound to reach 0.80 if the true rate is 0.9.
2. $2\,000\,000/366\approx5\,465$ s $=1.52$ h. That leaves about 0.48 h (29 minutes) for evaluation, the BC study and overhead: tight but feasible; reduce steps or increase environments if evaluation is slow.
3. Hover return: $60\cdot e^{-0.2}=60\cdot0.819=49.1$. A grasp that takes 40 steps of approach (average per-step pay perhaps 0.5) plus 12 plus 20 steps at about 1.0 earns about $20+12+20=52$: nearly the same, so noise decides and hovering often wins early in training. The one-off bonus is only about 24 % of the hover return. Fix: costs ($-d$), a time penalty, and a larger or terminal-only success reward.
4. Mass: $0.4/0.6=67\,\%$ inside; friction: $0.6/0.8=75\,\%$; delay: 40 ms is outside $\{0..30\}$, so 0 %. Joint fraction is 0: every held-out episode needs extrapolation. Change: train delay up to 50 ms (so 40 ms is inside) and widen mass and friction to at least the held-out ranges, then say clearly that the held-out set is held out by **seeds and by episode draws**, not by range. Alternatively keep narrower training ranges on purpose to measure extrapolation, and report an in-range split too.
5. Justified: on this perturbed set with these training runs, the DR policy did better (non-overlapping Wilson intervals, $z\approx3.5$ (pooled variance)). Not justified: "DR always helps" or any effect size claim, because each arm is one training seed and training-seed variance is not measured; also the held-out set shares assumptions with the training distribution. Run 3 to 5 seeds per arm.
6. (a) Covariate shift: the policy's own small errors move it to states absent from the demos; fix with DAgger-style relabelling or noise-injected demos. (b) Action-space or timing mismatch between demos and policy (or an observation that leaks the timestep); fix by replaying demos through the env and by checking that the policy input matches. (Also: demos are multimodal, averaging two grasp approaches gives a failing mean; fix with more consistent scripted demos.)
7. Replay the demo actions open loop through the environment: the scripted episode should reproduce its success in at least 95 % of cases. If it does not, the action spaces differ. This test needs no training.
8. (1) torch threads greater than 1 or nondeterministic ops; (2) a seed not applied to one component (numpy global, env reset, action sampling); (3) VecNormalize statistics or dataloader shuffling; (4) wall-clock or time-dependent logic in the environment; (5) different package or BLAS versions between runs; (6) GPU kernels (not applicable to CPU). Bisect by logging the loss after each update and finding the first update that differs.
9. Mean $=355/5=71$ %, minimum 20 %. The gate fails on both mean and minimum. A responsible report shows all five seeds, the mean with a bootstrap interval, the curve of the failing seed, a hypothesis (exploration collapse or an unlucky initialisation), and an additional experiment (more seeds, a different learning rate). Do not drop seed 5 and do not report seed 1 (96) as "the result".
10. Log: held-out MSE, closed-loop successes out of 100 with Wilson interval, per demo count and for at least 3 training seeds; training seed and demo-split seed. Baseline: constant-mean policy (MSE) and the scripted skill (success). Boundary: 0 demos (the baseline) and 500. Reject "more demos always help" if success is non-monotone beyond overlapping intervals while MSE keeps falling: then the bottleneck is compounding error, not data volume.

## Further reading

- [Spinning Up in Deep RL](https://spinningup.openai.com/en/latest/) - PPO explained with experiment hygiene.
- [Stable-Baselines3 documentation](https://stable-baselines3.readthedocs.io/en/master/) and its [RL tips](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html).
- [Gymnasium Env API](https://gymnasium.farama.org/api/env/) - the `reset` and `step` contract, termination versus truncation.
- [Tobin et al., Domain Randomization](https://arxiv.org/abs/1703.06907) - the original sim-to-real argument.
- [Henderson et al., Deep RL that Matters](https://arxiv.org/abs/1709.06560) - why seeds and reporting matter.
- [Schulman et al., PPO](https://arxiv.org/abs/1707.06347).
- [Ross, Gordon and Bagnell, A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning](https://arxiv.org/abs/1011.0686) - compounding error and DAgger.
- [Zhao et al., ALOHA / ACT](https://arxiv.org/abs/2304.13705) and [LeRobot ACT docs](https://huggingface.co/docs/lerobot/act).
- [Binomial proportion confidence interval (Wikipedia)](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval) - Wilson and alternatives.
- **Video:** Pieter Abbeel, *Lecture 22 Sim2Real and Domain Randomization* (CS287, UC Berkeley); *ALOHA and ACT: LeRobot Research Presentation #1* (Hugging Face).
