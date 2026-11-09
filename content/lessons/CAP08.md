---
{
  "id": "cap08-capstone",
  "module_id": "CAP08",
  "title": "Capstone milestone 8: full-system integration, sim-to-real gap and honest evaluation",
  "summary": "Run the whole CoreBot Tidy stack on hundreds of seeded episodes, measure it against a sealed perturbed twin of your own simulator, and report success rates with Wilson bounds, paired tests, bootstrap intervals and a failure taxonomy.",
  "estimated_minutes": 2040,
  "project_minutes": 2040,
  "prerequisites": [
    "CAP02",
    "CAP06",
    "CAP07",
    "S09",
    "RS03",
    "RS05"
  ],
  "source_refs": [
    {
      "title": "Henderson et al., Deep Reinforcement Learning that Matters",
      "url": "https://arxiv.org/abs/1709.06560"
    },
    {
      "title": "Tobin et al., Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World",
      "url": "https://arxiv.org/abs/1703.06907"
    },
    {
      "title": "Binomial proportion confidence interval (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval"
    },
    {
      "title": "McNemar's test (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/McNemar%27s_test"
    },
    {
      "title": "Bootstrapping (statistics) (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Bootstrapping_(statistics)"
    },
    {
      "title": "MuJoCo documentation: the simulation loop",
      "url": "https://mujoco.readthedocs.io/en/stable/programming/simulation.html"
    }
  ],
  "objectives": [
    "Run a full-system benchmark on seeded episodes and log every outcome with its root cause.",
    "Report success rates with Wilson bounds and compare two conditions with a paired exact test and a bootstrap interval.",
    "Estimate a sim-to-real gap against a sealed perturbed twin and attempt to close part of it by system identification.",
    "Keep tuning seeds disjoint from evaluation seeds and state hypotheses before running experiments.",
    "Build an error budget from a failure taxonomy and decide what to fix first."
  ],
  "core_theory": [
    "CAP02",
    "CAP06",
    "CAP07",
    "S09",
    "RS03",
    "RS05"
  ],
  "labs": [
    "Run 120 nominal, 80 twin and 4 x 30 ablation episodes, recompute every metric from the logs, recalibrate against the sealed twin, and pass the CAP08 acceptance suite."
  ],
  "assessment_refs": [
    "CAP08-diagnostic-v1"
  ],
  "review_prompts": [
    "State, before running anything, which ablation you expect to hurt most and by how much, then compare with the result.",
    "Explain why a 90 % success rate on 10 episodes is weaker evidence than 78 % on 120."
  ],
  "extension_refs": [
    "https://arxiv.org/abs/2305.05658"
  ]
}
---

## Why this matters

Up to now every milestone had a unit you could test in isolation: a wheel loop, a filter, a planner, a grasp. CAP08 is where the pieces meet, and where the most common research mistake appears: a number that looks good because of how it was measured. A robot that "works" on the seeds you tuned on, reported as a single percentage, proves very little. A robot evaluated on fresh seeds, with an interval, a paired comparison against its own ablations and a table of why it fails, tells a stranger (and the future you) what to trust.

This milestone also asks the question every robotics project eventually faces: how far is the simulator from reality? You do not have the real robot (the hardware tier is optional), so you build the next best thing: a **sealed twin**, a copy of your world with hidden perturbations. You may run experiments on it, but you may not read its parameters. How much success you lose on the twin, and how much you win back with system identification, is a small, honest model of sim-to-real transfer. It reuses ideas from [S09 Sim2Real](/lessons/S09), the statistics of [RS03 Statistical Inference](/lessons/RS03) and the failure analysis of [RS05 Error Analysis](/lessons/RS05).

## Intuition

![System architecture of CoreBot Tidy: sensors and MuJoCo world, firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation and learned skills, language task layer, safety supervisor and evaluation harness](/lesson-figures/CAP-architecture.svg)

*The shaded strip at the bottom of the architecture is the evaluation harness. CAP08 is the first milestone that mostly lives there.*

Think of the harness as a laboratory, not a demo. In a demo you pick the good run. In a laboratory you fix the protocol first, run it, and report what happened including the embarrassing part. Three habits make the difference:

- **Seeds are the experimental unit.** Each episode is one seed (scene layout, object poses, instruction). Seeds used for tuning never appear in evaluation.
- **Every number has an interval.** A success rate is an estimate from a finite sample; the interval says how much it could move if you reran with new seeds.
- **Every failure has a cause.** "It failed" is not data. `GRASP_SLIP` versus `LOCALISATION` tells you where the next ten hours go.

This milestone uses your work from [CAP02](/lessons/CAP02) (the firmware link and odometry calibration, which you will redo against the twin), [CAP06](/lessons/CAP06) (the learned skill and domain randomisation that you ablate) and [CAP07](/lessons/CAP07) (the parser and the safety supervisor whose violations must be zero). Earlier milestones ([CAP03](/lessons/CAP03) to [CAP05](/lessons/CAP05)) supply the estimator, planner and grasp pipeline that you now run end to end.

## Theory and derivation

These are the integration notes: the few formulas and interfaces that CAP08 depends on, each with the topic where it is taught.

![Diagram: the same stack runs on the nominal world and on a sealed twin with hidden perturbations; episodes are written to episodes.jsonl, metrics.py recomputes Wilson bounds, paired tests and a failure table, and tuning seeds stay separate from evaluation seeds](/lesson-figures/CAP08.svg)

### 1. Success rate with a Wilson interval ([RS03](/lessons/RS03))

With $k$ successes in $n$ independent episodes the point estimate is $\hat p=k/n$. The Wilson score interval at $z=1.96$ is
$$\frac{\hat p+\frac{z^2}{2n}\ \pm\ z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}.$$
It stays inside $[0,1]$ and behaves for small $n$ and for $\hat p$ near 0 or 1, unlike the textbook $\hat p\pm z\sqrt{\hat p(1-\hat p)/n}$. The gate of this milestone is written on the **lower** bound, because the lower bound is the claim you can defend. Rule of thumb for planning: the half-width at $\hat p=0.8$ is about $1.96\sqrt{0.16/n}$, so $n\approx 246$ episodes for $\pm0.05$ and $n\approx 61$ for $\pm0.10$.

### 2. Paired comparison of two conditions (McNemar, [RS03](/lessons/RS03))

Ablations reuse the same seeds as the nominal run, so outcomes are paired. Count the discordant seeds: $b$ = nominal succeeded and the ablation failed, $c$ = the reverse. Under the null hypothesis (no effect) each discordant seed is equally likely to fall either way, so $b\sim\text{Binomial}(b+c,\tfrac12)$ and the exact two-sided p-value is
$$p=\min\Bigl(1,\ 2\sum_{i=0}^{\min(b,c)}\binom{b+c}{i}2^{-(b+c)}\Bigr).$$
Seeds where both succeeded or both failed carry no information about the difference. Report the effect too, $(b-c)/n_{\text{pairs}}$ in percentage points, because a tiny effect can be significant and a large one non-significant at $n=30$.

### 3. Many comparisons (multiple testing, [RS03](/lessons/RS03))

Four ablations means four tests. At level 0.05 each, the chance of at least one false alarm under the null is $1-0.95^4\approx0.19$. The Holm step-down procedure compares the smallest p-value with $\alpha/4$, the next with $\alpha/3$, and so on, stopping at the first failure. State in the report how many comparisons you ran.

### 4. Bootstrap interval for a mean ([RS03](/lessons/RS03))

For a quantity without a neat formula (median duration, mean cross-track error) resample the episodes with replacement $B=2000$ times, compute the statistic each time, and take the 2.5 % and 97.5 % percentiles. It assumes the episodes are exchangeable draws, which is exactly why seeds must be independent.

### 5. Estimating the sim-to-real gap ([S09](/lessons/S09))

Let $p_{\text{nom}}$ and $p_{\text{twin}}$ be the success rates on the two worlds. The gap is $\Delta=p_{\text{nom}}-p_{\text{twin}}$. For independent samples use Newcombe's hybrid interval built from the two Wilson bounds $(\ell_i,u_i)$:
$$\Bigl[\Delta-\sqrt{(\hat p_1-\ell_1)^2+(u_2-\hat p_2)^2},\ \ \Delta+\sqrt{(u_1-\hat p_1)^2+(\hat p_2-\ell_2)^2}\Bigr].$$
If you run the same seeds on both worlds you may instead use McNemar. Remember what the twin is: one specific family of perturbations (wheel radius, track width, mass, friction, camera latency, lidar noise), not "reality". The estimate tells you how sensitive your stack is to errors of that kind and size.

### 6. Error budget and latency ([RS05](/lessons/RS05), [CAP02](/lessons/CAP02))

With failure counts $F_j$ per root cause and $N$ episodes, fixing cause $j$ completely would raise success to at most $(k+F_j)/N$. Sort causes by $F_j$ and attack the biggest bar first. For latency, per-stage medians do not add up exactly: the median of a sum is not the sum of the medians. Log each stage's time per episode and compute the median of the **total** perception-to-command time; the acceptance test limits it to 100 ms (at 0.5 m/s the robot moves 5 cm in that time).

## Worked example

All values below are illustrative, not from a real run.

### Gates, sim-to-twin gap, four paired ablations with Holm, failure budget and recalibration

**Problem.** A reference run produced 120 nominal episodes (seeds 1000 to 1119, 94 successes), 80 twin episodes (seeds 1120 to 1199, 46 successes before recalibration) and four ablations of 30 paired seeds (seeds 1000 to 1029); tuning used seeds 0 to 99 only. The ablations succeeded in 12, 18, 22 and 20 of 30 episodes (rates 0.40, 0.60, 0.73, 0.67) for "no landmark updates", "no DR policy", "scripted grasp instead of learned" and "safety supervisor off". The acceptance rules are: nominal rate at least 0.70 with Wilson lower bound at least 0.60, twin rate at least 0.50, median perception-to-command latency at most 100 ms, and recalibration with at least 25 % relative improvement.

- (a) Compute the Wilson intervals of the nominal and twin results and decide the nominal gate.
- (b) Compute the gap $\Delta$ between nominal and twin and its Newcombe interval.
- (c) Find the paired counts $b$ and $c$, the exact McNemar $p$-values and effects of the ablations, and apply Holm at 0.05 over the four tests; write the honest sentence.
- (d) Check that the failure counts (`GRASP_SLIP` 36, `DETECTION` 22, `PLACE_MISS` 14, `LOCALISATION` 13, `NAV_TIMEOUT` 9, `PARSE` 5, `OTHER` 5, `SAFETY_STOP` 3, `FIRMWARE_LINK` 1) match the failed episodes, and evaluate the recalibration (cross-track RMSE 0.112 m to 0.071 m) and the latency (median 71 ms).

**Solution.**

1. *Nominal.* $\hat p=94/120=0.783$; the Wilson 95 % interval is $[0.701,\,0.848]$. The rate is at least 0.70 and the lower bound 0.701 is at least 0.60: the gate passes.
2. *Twin.* $\hat p=46/80=0.575$ with Wilson $[0.466,\,0.677]$; it meets the twin floor of 0.50.
3. *Gap.* $\Delta=0.783-0.575=0.208$. Newcombe: lower $=\Delta-\sqrt{(\hat p_1-\ell_1)^2+(u_2-\hat p_2)^2}=0.208-\sqrt{0.0818^2+0.1024^2}=0.208-0.131=0.077$; upper $=\Delta+\sqrt{(u_1-\hat p_1)^2+(\hat p_2-\ell_2)^2}=0.208+\sqrt{0.0643^2+0.1093^2}=0.208+0.127=0.335$. The gap is real (interval above 0) but its size is uncertain because the twin sample is small.
4. *Paired counts.* Each ablation rate plus its effect gives the same baseline on the 30 paired seeds: $0.40+0.433=0.60+0.233=0.733+0.10=0.833$, that is 25 baseline successes in 30. For an ablation with $k$ successes, $b-c=25-k$: 13, 7, 3 and 5. With the counts of the table, $15-2=13$, $11-4=7$, $7-4=3$ and $8-3=5$ agree, and the effect is $(b-c)/30$: $+43.3$, $+23.3$, $+10.0$, $+16.7$ points.
5. *Exact McNemar.* $p=2\,P(X\le\min(b,c))$ for $X\sim\text{Bin}(b+c,\tfrac12)$. For $b=15$, $c=2$: $2\,(1+17+136)/2^{17}=308/131072=0.00235$. The same formula gives 0.118 for (11, 4), 0.549 for (7, 4) and 0.227 for (8, 3).
6. *Holm.* Four tests at 0.05 have a chance of at least one false alarm of $1-0.95^4=0.185$ (about 0.19), so compare sorted $p$ with $0.05/4=0.0125$, $0.05/3=0.0167$, $0.05/2=0.025$, $0.05/1=0.05$. The smallest, $0.0023<0.0125$, survives (adjusted $4\times0.0023=0.0094$). The next, $0.118>0.0167$, fails, and Holm stops: the other three are not significant.
7. *Sentence.* "Removing landmark updates reduced success by about 43 points (paired exact p = 0.0023, Holm-adjusted 0.009); we found no reliable evidence for the other three effects at n = 30."
8. *Failure budget.* Failed episodes: nominal $120-94=26$, twin $80-46=34$, ablations $120-(12+18+22+20)=48$: total 108. The causes sum to $36+22+14+13+9+5+5+3+1=108$, so every failure carries a cause. The largest bar, `GRASP_SLIP` at 36 of 108 (33 %), is the first thing to fix.
9. *Recalibration.* Relative improvement $=(0.112-0.071)/0.112=0.366\approx37\ \%\ge25\ \%$: passes.
10. *Other rules.* Median latency $71\ \text{ms}\le100$ ms. Tuning seeds 0-99 do not overlap the evaluation seeds 1000-1199.

| Split | n | Successes | Rate | Wilson 95 % |
|---|---|---|---|---|
| nominal | 120 | 94 | 0.783 | [0.701, 0.848] |
| twin (before recalibration) | 80 | 46 | 0.575 | [0.466, 0.677] |

| Ablation (30 paired seeds) | Rate | $b$ | $c$ | exact p | effect (pp) |
|---|---|---|---|---|---|
| no landmark updates | 0.40 | 15 | 2 | 0.0023 | +43.3 |
| no DR policy | 0.60 | 11 | 4 | 0.118 | +23.3 |
| scripted grasp instead of learned | 0.73 | 7 | 4 | 0.549 | +10.0 |
| safety supervisor off | 0.67 | 8 | 3 | 0.227 | +16.7 |

The numbers above can be recomputed with this script (it runs with the standard library plus `evalkit.py`):

```python
# Stdlib only. Needs evalkit.py from CAP01 on the path (src/corebot/evalkit.py in your repo).
from corebot.evalkit import wilson_interval, paired_mcnemar

k, n = 94, 120                       # illustrative nominal result
lo, hi = wilson_interval(k, n)
print(f"nominal  {k}/{n} = {k / n:.3f}  Wilson95 [{lo:.3f}, {hi:.3f}]")
kt, nt = 46, 80                      # illustrative twin result
lot, hit = wilson_interval(kt, nt)
print(f"twin     {kt}/{nt} = {kt / nt:.3f}  Wilson95 [{lot:.3f}, {hit:.3f}]")
print(f"no_landmarks paired: b=15 c=2  p = {paired_mcnemar(15, 2):.4f}")
print(f"no_supervisor paired: b=8 c=3  p = {paired_mcnemar(8, 3):.4f}")
# Holm correction for the four ablation p-values, smallest first
ps = sorted([paired_mcnemar(15, 2), 0.118, 0.227, 0.549])
adj = [min(1.0, (len(ps) - i) * p) for i, p in enumerate(ps)]
print("Holm step-down thresholds 0.05/4, 0.05/3, 0.05/2, 0.05/1; first adjusted p =", round(adj[0], 4))
```



**Check.** The script prints the Wilson lines, the exact $p$ for (15, 2) and (8, 3), and the first Holm-adjusted $p$ (0.0094); an independent computation of the exact binomial sums and of the Newcombe formula gave the same values to three decimals. Sanity bounds: every $p$ is in $[0,1]$ and grows as the effect $(b-c)/30$ shrinks (0.0023, 0.118, 0.227, 0.549 for effects 43.3, 23.3, 16.7, 10.0 points), and the ablation failures $18+12+8+10=48$ match the failure budget of step 8.

**Takeaway.** With four ablations on 30 paired seeds only a large effect survives correction; report the effect, the exact paired $p$, the Holm-adjusted value and what could not be shown, and let the failure counts, summing to the number of failed episodes, direct the next fix.

## Exercises

1. **(Easy)** *Wilson bound.* Your pilot gives 27 successes in 30 episodes. Compute the Wilson 95 % interval and explain why the point estimate 0.90 alone is not what you report. Does it already satisfy the lower-bound gate of 0.60?
2. **(Easy)** *Planning n.* You expect a success rate near 0.8. How many episodes do you need for a Wilson half-width of about 0.10, and about 0.05? Why does the milestone ask for at least 100 nominal episodes?
3. **(Medium)** *Paired test.* In 10 discordant seeds, the nominal run won 9 and the ablated run won 1 ($b=9$, $c=1$). Compute the exact McNemar p-value. Repeat for $b=6$, $c=2$ and explain what the concordant seeds contribute.
4. **(Medium)** *Multiple comparisons.* Your four ablations give p-values 0.0023, 0.118, 0.227 and 0.549. Which survive Holm at 0.05? What would you write about the other three?
5. **(Medium)** *Seed hygiene.* You tuned thresholds on seeds 0-99 and report 84 successes out of those same 100 seeds. A colleague re-runs 100 fresh seeds and gets 72. What is wrong with the first number, and how would you set up the protocol so the problem cannot occur?
6. **(Medium)** *Gap interpretation.* Nominal 94/120 and twin 46/80. Using the Newcombe interval $[0.077,0.335]$, say what you can and cannot claim about the sim-to-real gap of your robot. Name one reason the real gap could be larger than the twin gap.
7. **(Medium)** *Latency budget.* Per-episode medians of the stages are perception 38 ms, planning 21 ms, command packing and link 9 ms. A colleague says the budget "adds up to 68 ms, so it passes the 100 ms limit". What is wrong with the argument, and what exactly should be logged and tested?
8. **(Hard)** *Error budget.* Among the 26 failed nominal episodes, 9 are `GRASP_SLIP`. Estimate the best-case success rate if you removed that cause completely, give a Wilson interval for the share of grasp failures, and decide whether another 10 hours on grasping or on detection (6 failures) is better.
9. **(Hard)** *Recalibration outcome.* After sysid on the twin the cross-track RMSE falls from 0.112 m to 0.095 m. Does the milestone's 25 % criterion pass? What must you deliver instead, and what is forbidden while trying to improve it?
10. **(Hard, mini-project)** *Design the ablation study.* Write `docs/experiments.md` before running the ablations: for each of the four ablations a hypothesis with a predicted direction and size, the seeds, the n, the test, the correction for multiple comparisons, and one outcome that would make you doubt your own pipeline (not the robot).

## Reference implementation

This is the skeleton of `bench/metrics.py`, the module that recomputes every reported number from the episode log. Implement it with the standard library and `evalkit.py` (see [CAP01](/lessons/CAP01) for how to download it). The acceptance test imports `CAUSES`, `compute_metrics` and `seed_overlap` from it.

```python
"""bench/metrics.py: recompute every reported number from runs/final/episodes.jsonl.

Nothing in the report or in metrics.json may come from anywhere else.
"""
from __future__ import annotations

from typing import Iterable, Sequence

CAUSES = ("NAV_TIMEOUT", "LOCALISATION", "DETECTION", "GRASP_SLIP", "PLACE_MISS",
          "PARSE", "SAFETY_STOP", "FIRMWARE_LINK", "OTHER")


def by_split(episodes: Iterable[dict], split: str) -> list[dict]:
    """Episodes whose "split" equals `split` (nominal, twin, twin_recal, abl:<name>), in file order."""
    raise NotImplementedError


def split_stats(eps: Sequence[dict]) -> dict:
    """n, successes, rate, wilson_lo, wilson_hi (95 %), median_duration_s of one split."""
    raise NotImplementedError


def failure_table(eps: Sequence[dict]) -> dict[str, int]:
    """Counts per failure_cause over the FAILED episodes only. A missing cause is counted under None."""
    raise NotImplementedError


def paired_counts(a_eps: Sequence[dict], b_eps: Sequence[dict]) -> tuple[int, int, int]:
    """(b, c, pairs) over the seeds present in both lists.
    b = A succeeded and B failed, c = A failed and B succeeded. Concordant pairs carry no information."""
    raise NotImplementedError


def newcombe_diff(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Newcombe hybrid-score 95 % CI for p1 - p2 from the two Wilson intervals (independent samples)."""
    raise NotImplementedError


def compute_metrics(episodes: Sequence[dict]) -> dict:
    """The dict stored as runs/final/metrics.json (see "Expected output" for the keys)."""
    raise NotImplementedError


def seed_overlap(tuning_seeds: Iterable[int], episodes: Sequence[dict]) -> list[int]:
    """Seeds used for tuning that also appear in a nominal or twin evaluation episode. Must be empty."""
    raise NotImplementedError
```

## Independent practice

### Goal
Run the complete CoreBot Tidy stack end to end on seeded episodes, evaluate it on a nominal world and on a sealed perturbed twin, ablate four design decisions with proper statistics, classify every failure, and pass the CAP08 acceptance suite. Weight in graduation: 14 points of 100.

### Setup
Work in `~/corebot-capstone` (created in [CAP01](/lessons/CAP01)). Python 3.11 or newer, the standard library plus the packages you already pinned in `pyproject.toml`; `corebot/evalkit.py` from CAP01 must be present. Budget your compute: 120 + 80 + 120 ablation episodes is about 320 episodes; if one takes 30 s of wall-clock you need about 3 hours, so run in the background and log to disk. The lean path (60 nominal + 40 twin) is for slow machines but then the gate on 100 and 60 episodes will fail; plan accordingly.

```bash
cd ~/corebot-capstone
mkdir -p bench runs/final tests/acceptance
# bench/metrics.py       <- the reference skeleton above, implemented
# bench/run_bench.py     <- your episode runner (starter stubs below)
python -m pytest -q tests/acceptance/test_cap08.py
python bench/metrics.py            # recomputes runs/final/metrics.json from episodes.jsonl
```

### Tasks
1. **Seed plan.** Write `configs/bench.yaml` and `runs/final/tuning_seeds.txt` (seeds 0-99). Evaluation seeds: nominal 1000-1119, twin 1120-1199; ablations reuse the first 30 nominal seeds. Instruction classes: single fetch, two-object, with distractors, spread over 5 scenes.
2. **Runner.** `bench/run_bench.py` runs one seeded episode per call, writes one JSON line with the fields of `EpisodeRecord`, and classifies each failure with one of the nine causes from logged events.
3. **Metrics.** Implement `bench/metrics.py`; `python bench/metrics.py` writes `runs/final/metrics.json` and must reproduce it exactly when re-run.
4. **Sealed twin.** Create `models/corebot_real.xml` with a generator that perturbs wheel radius (about +3 %), track width (about -2 %), mass (+15 %), friction (-25 %), camera latency (+30 ms) and lidar noise (x2). Use `--secret-seed $RANDOM` once; do not print, log or commit the seed; never open the produced XML.
5. **Twin experiments and recalibration.** Run step tests and square drives on the twin, re-identify wheel radius, track width and friction (the method of [CAP02](/lessons/CAP02)), update your nominal parameters, and re-run the twin split as `twin_recal`. Write `runs/final/twin_recal.json`.
6. **Ablations.** Four ablations on 30 paired seeds each: no landmark updates, no DR policy, scripted instead of learned grasp, supervisor off.
7. **Pre-registration.** Commit `docs/experiments.md` (hypotheses, predictions, tests) before the first ablation run; later edits only through new commits that say why.
8. **Error analysis.** Write `docs/error_budget.md`: the failure table, the best-case gain for the top two causes, your decision and the evidence for it.

### Starter code
`make_real_twin.py` is given because the point of the exercise is the evaluation, not the generator. It prints nothing about the perturbation; adapt the attribute patterns in `apply` to your MJCF (friction is a triple in MuJoCo, so scale its first number).

```python
"""Sealed twin generator: writes models/corebot_real.xml and prints NOTHING about the perturbation.

Usage: python make_real_twin.py --secret-seed $RANDOM     (do not log, print or commit the seed)
"""
import argparse
import json
import random
import re

# nominal size of each perturbation (the lesson tells you these); the actual factor is jittered
# by +-30 % so that you can identify the twin but not read it off.
NOMINAL = {"wheel_radius": +0.03, "track_width": -0.02, "mass": +0.15, "friction": -0.25,
           "camera_latency_s": 0.030, "lidar_noise_scale": 2.0}


def draw(secret_seed: int) -> dict:
    """Perturbation factors for one twin; deterministic in the secret seed."""
    rng = random.Random(secret_seed)
    out = {}
    for key, nominal in NOMINAL.items():
        jitter = rng.uniform(0.7, 1.3)
        out[key] = nominal * jitter if key != "lidar_noise_scale" else 1 + (nominal - 1) * jitter
    return out


def apply(xml_text: str, p: dict) -> str:
    """Scale the attributes your MJCF uses. Adapt the patterns to your own model file."""
    def scale(attr, factor, text):
        pattern = re.compile(rf'({attr}=")([-0-9.eE]+)(")')
        return pattern.sub(lambda m: f"{m.group(1)}{float(m.group(2)) * factor:.6g}{m.group(3)}", text)
    xml_text = scale("wheel_radius", 1 + p["wheel_radius"], xml_text)
    xml_text = scale("track_width", 1 + p["track_width"], xml_text)
    xml_text = scale("mass", 1 + p["mass"], xml_text)
    xml_text = scale("friction", 1 + p["friction"], xml_text)
    return xml_text


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--secret-seed", type=int, required=True)
    ap.add_argument("--src", default="models/corebot.xml")
    ap.add_argument("--dst", default="models/corebot_real.xml")
    a = ap.parse_args()
    params = draw(a.secret_seed)
    with open(a.src) as f:
        text = apply(f.read(), params)
    with open(a.dst, "w") as f:
        f.write(text)
    # Runtime knobs (latency, lidar noise) are read from a file that only the bench loads:
    with open(a.dst + ".runtime.json", "w") as f:
        json.dump({"camera_latency_s": params["camera_latency_s"],
                   "lidar_noise_scale": params["lidar_noise_scale"]}, f)
```

The runner and the sysid step are interface stubs for you to fill with your own stack.

```python
"""bench/run_bench.py and bench/sysid_twin.py: interface stubs (fill in with your own stack)."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict


@dataclass
class EpisodeRecord:
    seed: int
    split: str                      # "nominal" | "twin" | "twin_recal" | "abl:<name>"
    instruction_class: str          # "single" | "two_object" | "distractor"
    success: bool
    failure_cause: str | None       # one of metrics.CAUSES when success is False, else None
    duration_s: float               # simulated time
    safety_violations: int
    latency_ms: dict                # {"perception": .., "plan": .., "perception_to_command": ..}
    git_hash: str


def run_episode(seed: int, split: str, config: dict) -> EpisodeRecord:
    """Run ONE seeded end-to-end episode (parse -> navigate -> grasp -> place) and classify its outcome.

    Rules: no wall-clock randomness; the failure cause is decided from logged events, not guessed;
    a twin split loads models/corebot_real.xml but never reads its parameters.
    """
    raise NotImplementedError


def run_split(seeds: range, split: str, config: dict, out_path: str) -> None:
    """Append one JSON line per episode to out_path (create parent dirs, never overwrite old lines)."""
    raise NotImplementedError


def recalibrate(twin_episodes: list[dict], nominal_params: dict) -> dict:
    """System identification on EXPERIMENTS run on the twin (step tests, square drives).
    Returns new wheel_radius, track_width and friction estimates. May not read the twin's XML."""
    raise NotImplementedError


if __name__ == "__main__":
    print(json.dumps(asdict(EpisodeRecord(0, "nominal", "single", True, None, 91.2, 0,
                                          {"perception": 38.0, "plan": 21.0, "perception_to_command": 70.0}, "a1b2c3d"))))
```

### Tests
`tests/acceptance/test_cap08.py` reads only the artefacts under `runs/final/`. Checks marked G are gates (a failing gate keeps the milestone "in progress"). Thresholds are provisional starting values (see the plan rationale); tighten them once your own reference run exists.

- Integrity (G): at least 100 nominal and 60 twin episodes, because $n\ge100$ makes the Wilson half-width about 0.08 at $p=0.8$; unique seeds per split; recomputation matches `metrics.json`.
- Nominal success (G): rate at least 0.70 and Wilson lower bound at least 0.60, because a stack that cannot do 70 % of single tidy tasks is not integrated; median duration at most 180 s.
- Zero safety violations (G): any person-zone speed breach or non-latching e-stop is a design bug, not a statistic. Remember what the number means: the supervisor protects a simulation, so zero violations here is a teaching result about your hazard analysis and fault injection, not a certification of safety.
- Twin success at least 0.50 and recalibration: the twin is deliberately harsh; either at least 25 % relative improvement (cross-track RMSE or success) or an explicit negative result with CI.
- Ablations: at least four with $n\ge30$ (enough pairs to detect a large effect of about 40 points) and at least one McNemar entry.
- Taxonomy: at least 90 % of failures carry a cause from the fixed list and the counts sum to the failures.
- Latency: median perception-to-command at most 100 ms.
- Seed hygiene: no tuning seed appears in nominal or twin evaluation.

```python
"""CAP08 acceptance tests. Gates (G) are the checks that must pass to graduate."""
import json
import pathlib
import re

from bench.metrics import CAUSES, compute_metrics, seed_overlap
from corebot.evalkit import load_episodes, wilson_interval

RUNS = pathlib.Path("runs/final")
REQUIRED = {"seed", "split", "success", "failure_cause", "duration_s",
            "safety_violations", "latency_ms", "git_hash"}


def _eps():
    return load_episodes(RUNS / "episodes.jsonl")


def _split(name):
    return [e for e in _eps() if e["split"] == name]


def test_artefact_integrity():                                    # G
    eps = _eps()
    nominal, twin = _split("nominal"), _split("twin")
    assert len(nominal) >= 100 and len(twin) >= 60
    for name in {e["split"] for e in eps}:
        seeds = [e["seed"] for e in eps if e["split"] == name]
        assert len(seeds) == len(set(seeds)), f"duplicate seeds in {name}"
    assert all(REQUIRED <= set(e) for e in eps)
    assert all(re.fullmatch(r"[0-9a-f]{7,40}", e["git_hash"]) for e in eps)
    stored = json.loads((RUNS / "metrics.json").read_text())
    fresh = json.loads(json.dumps(compute_metrics(eps)))      # same float formatting as the file

    def same(a, b):
        if isinstance(a, dict):
            return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
        if isinstance(a, list):
            return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        if isinstance(a, float) or isinstance(b, float):
            return abs(a - b) < 1e-9
        return a == b
    assert same(stored, fresh), "metrics.json does not match a recomputation from the logs"


def test_nominal_success():                                       # G
    nominal = _split("nominal")
    k = sum(e["success"] for e in nominal)
    lo, _ = wilson_interval(k, len(nominal))
    assert k / len(nominal) >= 0.70 and lo >= 0.60
    durations = sorted(e["duration_s"] for e in nominal)
    assert durations[len(durations) // 2] <= 180.0


def test_zero_safety_violations():                                # G
    assert sum(e["safety_violations"] for e in _eps()) == 0


def test_twin_success_and_recalibration():
    twin = _split("twin")
    assert sum(e["success"] for e in twin) / len(twin) >= 0.50
    r = json.loads((RUNS / "twin_recal.json").read_text())
    if r.get("negative_result"):
        assert {"ci_lo", "ci_hi"} <= set(r), "a negative result must carry its CI"
    else:
        before, after = r["before"]["cross_track_rmse_m"], r["after"]["cross_track_rmse_m"]
        better_rmse = (before - after) / before >= 0.25
        better_succ = (r["after"]["success"] - r["before"]["success"]) / r["before"]["success"] >= 0.25
        assert better_rmse or better_succ


def test_ablations():
    m = json.loads((RUNS / "metrics.json").read_text())["ablations"]
    assert len(m) >= 4
    for name, a in m.items():
        assert a["n"] >= 30, name
        assert 0.0 <= a["wilson_lo"] <= a["wilson_hi"] <= 1.0, name
    assert any("mcnemar_p" in a and "effect_pp" in a for a in m.values())
    assert {"no_landmarks", "no_dr_policy", "scripted_grasp", "no_supervisor"} <= set(m)


def test_failure_taxonomy():
    eps = _eps()
    fails = [e for e in eps if not e["success"]]
    labelled = [e for e in fails if e["failure_cause"] in CAUSES]
    assert len(labelled) / len(fails) >= 0.90
    m = json.loads((RUNS / "metrics.json").read_text())["failures"]
    assert sum(m["by_cause"].values()) == m["total"] == len(fails)


def test_latency_budget():
    nominal = sorted(e["latency_ms"]["perception_to_command"] for e in _split("nominal"))
    assert nominal[len(nominal) // 2] <= 100.0


def test_seed_hygiene():
    tuning = [int(x) for x in (RUNS / "tuning_seeds.txt").read_text().split()]
    assert seed_overlap(tuning, _eps()) == []
```

### Expected output
With a complete set of artefacts:

```
........                                                                 [100%]
8 passed in 0.9s
```

The abbreviated `runs/final/metrics.json` of the illustrative run (keys you must produce; yours will differ):

```json
{
  "nominal": {
    "n": 120,
    "successes": 94,
    "rate": 0.783,
    "wilson_lo": 0.701,
    "wilson_hi": 0.848,
    "median_duration_s": 118.4
  },
  "twin": {
    "n": 80,
    "successes": 46,
    "rate": 0.575,
    "wilson_lo": 0.466,
    "wilson_hi": 0.677
  },
  "gap": {
    "difference": 0.208,
    "ci_lo": 0.077,
    "ci_hi": 0.335
  },
  "safety_violations": 0,
  "failures": {
    "total": 108,
    "by_cause": {
      "GRASP_SLIP": 36,
      "DETECTION": 22,
      "PLACE_MISS": 14,
      "LOCALISATION": 13,
      "NAV_TIMEOUT": 9,
      "PARSE": 5,
      "OTHER": 5,
      "SAFETY_STOP": 3,
      "FIRMWARE_LINK": 1
    }
  },
  "latency_perception_to_command_ms_median": 71.0,
  "ablations": {
    "no_landmarks": {
      "n": 30,
      "rate": 0.4,
      "wilson_lo": 0.246,
      "wilson_hi": 0.577,
      "b": 15,
      "c": 2,
      "mcnemar_p": 0.00235,
      "effect_pp": 43.3
    }
  }
}
```

Before you have artefacts the tests fail with `FileNotFoundError` or `NotImplementedError`; that is the intended starting state.

### Extension challenge
Add a fifth condition that targets your largest failure cause and show with a paired test whether it helps. Stretch: replace the scripted wait in the supervisor with a learned person-distance estimator and show the false-stop rate stays at or below 5 %. Optional hardware tier (no grade depends on it; with a real-versus-sim table it can serve as the Distinction stretch of CAP09, and it never replaces a failing gate): replay the CAP02 step-response test on your real ESP32 base against the simulated one and add a real-versus-sim table (settling time, overshoot, steady-state error); with a real SO-101, run 20 pick trials and report the Wilson interval next to the simulated one. Keep wheels off the ground for first runs, stay at or below 12 V, keep a fuse in the battery line and follow the battery and electrical rules of HW03 (never charge or leave a lithium pack unattended).

### Library track
Cross-check your own functions with SciPy and statsmodels. The Wilson bounds should agree to about $10^{-4}$ (you use $z=1.96$, SciPy uses the exact quantile), and the exact McNemar p-value should match to many digits.

```python
# Needs: pip install scipy statsmodels   (cross-check of your own bench/metrics.py)
import numpy as np
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar

# 1. Wilson interval: SciPy gives the same numbers as evalkit.wilson_interval (z = 1.96 vs 1.959964: 1e-4 apart)
ci = stats.binomtest(94, 120).proportion_ci(confidence_level=0.95, method="wilson")
print("wilson  :", round(ci.low, 3), round(ci.high, 3))           # about 0.701 0.848

# 2. Exact McNemar on the discordant counts b=15, c=2 (table rows: A ok/fail, columns: B ok/fail)
table = [[0, 15], [2, 0]]            # only the off-diagonal cells enter the exact test
print("mcnemar :", mcnemar(table, exact=True).pvalue)                # about 0.00235

# 3. Percentile bootstrap of the mean success over 30 paired seeds
outcomes = np.array([1] * 22 + [0] * 8)
res = stats.bootstrap((outcomes,), np.mean, confidence_level=0.95, n_resamples=5000,
                      method="percentile", random_state=0)
print("bootstrap:", res.confidence_interval)
```

## Verification

Check numbers by hand before trusting code: Wilson 94/120 is about [0.70, 0.85]; McNemar with $b=15$, $c=2$ is $2\sum_{i\le2}\binom{17}{i}/2^{17}=2\cdot154/131072=0.0023$. Re-run `python bench/metrics.py` twice and diff the output; change one episode line by hand and confirm the integrity test fails. Run the same seed twice and compare outcomes (determinism from [CAP01](/lessons/CAP01)). Confirm that `tuning_seeds.txt` and the evaluation seeds are disjoint with a one-line set intersection. Scoring: CAP08 carries weight 14 of 100 in the graduation score (60 % automated checks, 40 % human rubric: experiment design, statistical honesty, error analysis, insight on what simulation cannot show). Gates: artefact integrity, nominal success, zero safety violations. Graduation requires zero safety violations here, all gates passed, and every milestone at least 60.

## Failure modes

- Tuning on the evaluation seeds, so the reported rate is optimistic.
- Reporting a mean without an interval, or comparing 30 episodes with 120 as if equal.
- Choosing the best of several runs ("cherry-picked seed") and calling it the result.
- Unlogged non-determinism: wall-clock seeds, unordered set iteration, multi-threaded training changing the policy.
- Overfitting to the twin by reading its parameters or by tuning thresholds on twin seeds.
- A failure taxonomy where everything is `OTHER`, so the error budget says nothing.
- Exploiting a simulator bug (objects clipping through bin walls) and counting it as success; check a few successes by watching the video.
- Running many tests and reporting only the significant one (no correction, no count of tests).
- Treating the twin as reality: it estimates sensitivity to one family of perturbations, nothing more.

## Alternatives and trade-offs

Wilson is a good default; the Clopper-Pearson interval is conservative (wider, guaranteed coverage), the Agresti-Coull interval is a simple approximation. A permutation test on paired outcomes gives the same answer as exact McNemar for binary results but also works for continuous metrics. A Bayesian Beta-Binomial posterior gives a credible interval and an intuitive "probability that A beats B"; use it if you can state the prior. Instead of a hidden twin you can use domain randomisation ranges as a stress test (CAP06), which is cheaper but lets you see the perturbations. A real robot is the true test; the hardware tier is the cheap way to get a taste of it. More episodes beat clever statistics: if two conditions overlap, run more seeds before arguing about methods.

## Transfer and retention

This milestone prepares [CAP09](/lessons/CAP09), where every number in the report must come from the `metrics.json` you build here, and it applies [S09](/lessons/S09), [RS03](/lessons/RS03) and [RS05](/lessons/RS05) to your own system. Outside the capstone, the same protocol (fixed seeds, held-out test set, interval, paired comparison, error taxonomy) evaluates any model or robot. Recall prompts:

1. Write the Wilson interval formula from memory and say why its lower bound is used as the gate.
2. Which seeds does a paired McNemar test use, and which seeds does it ignore?
3. Why does the median of a latency sum differ from the sum of medians?
4. What may you do with the sealed twin, and what may you not do?
5. List the nine failure causes and say which one you expect to dominate your own stack, before looking at the data.

## Exercise answers

1. Wilson for 27/30: $[0.744,0.965]$. The point estimate hides a lower end near 0.74; with $n=30$ the true rate could easily be 0.8. The lower bound 0.744 is above 0.60, but the gate needs at least 100 episodes, so a 30-episode pilot only tells you that you are on the right track.
2. Half-width $1.96\sqrt{0.16/n}$: $\pm0.10$ needs $n\approx61$ (1.96$^2\cdot0.16/0.01=61.5$), $\pm0.05$ needs $n\approx246$. At least 100 nominal episodes gives a half-width of about 0.08 at $p=0.8$, a compromise between precision and the compute budget.
3. $b=9$, $c=1$: $n=10$, $p=2\,(1+10)/1024=0.0215$: significant at 0.05. $b=6$, $c=2$: $n=8$, $p=2\,(1+8+28)/256=0.289$: no evidence. Concordant seeds (both succeed or both fail) tell nothing about which condition is better; they only show those seeds were easy or hard.
4. Sorted: 0.0023 vs $0.05/4=0.0125$: pass; 0.118 vs $0.05/3=0.0167$: fail, so stop. Only the first survives. Report the other three as "no reliable evidence at n = 30", not "no effect": with 30 pairs you can only detect large effects; give the effect size and CI.
5. The 84/100 was measured on seeds that shaped the thresholds, so it is biased upwards (the tuning absorbed the noise of those particular scenes). The fresh 72/100 (Wilson $[0.625,0.799]$) is the honest figure. Protocol: write the tuning seed list and the evaluation seed list to files at the start, forbid the evaluation seeds in tuning code, and add the `seed_overlap` test.
6. You can claim that, for this perturbation family and these n, success falls by about 21 points and the plausible range is 8 to 34 points. You cannot claim that the real robot loses 21 points. The real gap could be larger because unmodelled effects exist that the twin has no parameter for (backlash, cable drag, lighting, contact softness, a slipping gripper pad), and because the real world perturbs everything at once and not within ranges you expected.
7. The sum of per-stage medians is not the median of the sum, and the stages are correlated (a slow frame is slow everywhere). Also link or queueing delay may be missing. Log per-episode (or per-frame) timestamps for each stage and the total, test the median of the total at most 100 ms, and also look at the 95th percentile since occasional spikes matter for safety.
8. Best case $(94+9)/120=0.858$ (Wilson 95 % $[0.785,0.910]$ if it really happened). The grasp share is $9/26=0.35$, Wilson $[0.19,0.54]$, which is wide: the data say grasping is probably the biggest bar but not by a decisive margin over detection (6/26). Spend the next hours on grasping if the cause is understood (slip analysis from the taxonomy), but re-check after the fix with new seeds; the budget is a guide, not a proof.
9. Improvement $(0.112-0.095)/0.112=15\%<25\%$: it fails. Deliver the written negative result: `negative_result: true` with the CI of the RMSE difference (bootstrap over episodes) in `twin_recal.json`, and an explanation of what limits identification (for example friction poorly excited by your experiments). Forbidden: reading the twin XML or its parameters, or tuning on the twin evaluation seeds.
10. A good document names, per ablation, the expected direction and rough size (for example "no landmarks: 30 to 50 points lower, because heading drifts"), fixes n = 30 paired seeds from 1000-1029, the exact McNemar test with Holm over four, and the pipeline-doubt outcome: for example "if the supervisor-off ablation changes success by more than 20 points while no hazards occur, my supervisor is interfering with normal operation, or the ablation switch is broken".

## Further reading

- [Henderson et al., Deep Reinforcement Learning that Matters](https://arxiv.org/abs/1709.06560): seeds, variance and honest reporting.
- [Tobin et al., Domain Randomization](https://arxiv.org/abs/1703.06907): why perturbing the simulator helps transfer.
- [Binomial proportion confidence interval (Wikipedia)](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval): Wilson, Clopper-Pearson and others compared.
- [McNemar's test (Wikipedia)](https://en.wikipedia.org/wiki/McNemar%27s_test): the paired test for binary outcomes.
- [Bootstrapping (statistics) (Wikipedia)](https://en.wikipedia.org/wiki/Bootstrapping_(statistics)): percentile intervals.
- [MuJoCo documentation: the simulation loop](https://mujoco.readthedocs.io/en/stable/programming/simulation.html): determinism and stepping.
- **More practice:** [TidyBot (arXiv 2305.05658)](https://arxiv.org/abs/2305.05658) reports a household-tidying system evaluated over many trials.
