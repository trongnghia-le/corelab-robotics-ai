---
{
  "id": "cap09-capstone",
  "module_id": "CAP09",
  "title": "Capstone milestone 9: reproducible release, technical report, demo and the graduation check",
  "summary": "Package CoreBot Tidy so a stranger can rerun it (Docker and make reproduce-smoke), write a short scientific report whose every number is generated from your logs, record a 3-minute demo, and run the final graduation check against the capstone rubric.",
  "estimated_minutes": 960,
  "project_minutes": 960,
  "prerequisites": [
    "CAP08",
    "RS07",
    "RS04",
    "RS09",
    "T06",
    "HW12"
  ],
  "source_refs": [
    {
      "title": "Releasing research code (Papers with Code checklist)",
      "url": "https://github.com/paperswithcode/releasing-research-code"
    },
    {
      "title": "Henderson et al., Deep Reinforcement Learning that Matters",
      "url": "https://arxiv.org/abs/1709.06560"
    },
    {
      "title": "Docker documentation: building best practices",
      "url": "https://docs.docker.com/build/building/best-practices/"
    },
    {
      "title": "GNU Make manual",
      "url": "https://www.gnu.org/software/make/manual/make.html"
    },
    {
      "title": "pytest documentation",
      "url": "https://docs.pytest.org/en/stable/"
    }
  ],
  "objectives": [
    "Package a project so that make reproduce-smoke reruns seeded episodes and matches stored outcomes in a clean environment.",
    "Generate every number in a report from a metrics file with placeholders that fail on unknown keys.",
    "Write a report with the standard sections, calibrated claims, limitations and a reproducibility statement.",
    "Plan and record a 3-minute demo that shows the instruction, the robot's internal state and the result.",
    "Compute the weighted graduation score and decide Pass, Merit or Distinction against the rules."
  ],
  "core_theory": [
    "CAP08",
    "RS07",
    "RS04",
    "RS09",
    "T06",
    "HW12"
  ],
  "labs": [
    "Build the release (Dockerfile, Makefile, README, checklist), render the report from metrics.json, pass the CAP09 acceptance suite and run the graduation calculator on your own scores."
  ],
  "assessment_refs": [
    "CAP09-diagnostic-v1"
  ],
  "review_prompts": [
    "Find one sentence in your draft report that claims more than the evidence supports and rewrite it.",
    "Explain why a report number typed by hand is a defect even when it is correct today."
  ],
  "extension_refs": [
    "https://arxiv.org/abs/2305.05658"
  ]
}
---

## Why this matters

You have a working system and a set of honest numbers from [CAP08](/lessons/CAP08). Most of the value of a project is lost at this last step: the code runs only on your laptop, the report quotes numbers from an older run, the demo shows the one lucky episode. This milestone turns the project into something other people can trust and reuse: a release that a stranger can rerun, a report where every figure traces to a log, and a demo that tells the truth in three minutes.

It is also the end of the course, so it closes with a graduation check. The rule is deliberately plain: pass the gates, reach 60 in every milestone, reach 70 in total. The check is a small program you run on your own scores, so you can see exactly what stands between you and a Merit or Distinction.

## Intuition

![System architecture of CoreBot Tidy: sensors and MuJoCo world, firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation and learned skills, language task layer, safety supervisor and evaluation harness](/lesson-figures/CAP-architecture.svg)

*Release means freezing this whole picture: code, models, configs, seeds and logs, under one tag.*

Think of the release as a sealed box with a label. Inside: the source at tag `v1.0`, pinned dependencies, the firmware, small summary logs, trained weights. On the label: the commands that rebuild the headline numbers. A reader does not need to believe you; they run `make reproduce-smoke`, see six seeded episodes end exactly as your stored file says, and only then read the report.

The report is the box's instruction manual written in prose. The rule is simple: **no number in the Results section is typed by a human**. Placeholders such as `{{metric:nominal.wilson_lo|pct1}}` are replaced from `metrics.json`; if the key does not exist the build fails. The demo is the trailer. It must show the full chain (typed instruction, parser, pose estimate, detections, grasp, placement) and must not hide the safety supervisor.

This milestone draws on [CAP08](/lessons/CAP08) (the `metrics.json` and logs), [RS07 Scientific Writing](/lessons/RS07) (report structure and calibrated claims), [RS04 Experimental Reproducibility](/lessons/RS04) (seeds, environments, hashes), [RS09 Research Software](/lessons/RS09) (tests, packaging, lint), [T06 Docker](/lessons/T06) (the image) and [HW12 Bring-up & Debugging](/lessons/HW12) (the debug log appendix and the hardware appendix if you built the optional tier).

## Theory and derivation

These are the integration notes: the specifications that the acceptance tests enforce, each with the topic where it is taught.

![Diagram: source tag v1.0, Dockerfile and Makefile feed make reproduce-smoke which compares six seeded outcomes with the stored file; metrics.json feeds report.md.tmpl through render.py into report.md; scores.json feeds graduate.py which prints the verdict](/lesson-figures/CAP09.svg)

### 1. Reproducibility smoke test ([RS04](/lessons/RS04))

You cannot rerun 320 episodes in a test, so you rerun a **smoke set**: 6 seeds, stored with their outcomes in `runs/smoke/expected.json`. The test passes when a fresh run (in the container, or in a fresh virtual environment) gives **exactly** the same outcome for each seed and finishes within 20 minutes. Determinism rests on four habits: fixed seeds (`numpy.random.default_rng(seed)`), single-threaded numerical code in tests (`OMP_NUM_THREADS=1`), pinned versions, and no dependence on wall-clock time. Floating-point results may differ between CPU types, so the smoke test compares **outcomes** (success flag, failure cause, number of steps within a tolerance you document), not raw floats.

### 2. Container and make targets ([T06](/lessons/T06), [RS09](/lessons/RS09))

Build the image from a pinned base (`python:3.11.9-slim-bookworm`), install dependencies from a lock file during `docker build`, and run with `--network none` so nothing can be downloaded at run time. `make` gives the reader short commands: `make doctor` (tools present?), `make test`, `make reproduce-smoke`, `make report`. The README quickstart must stay at 10 commands or fewer because a long quickstart is a quickstart nobody finishes.

### 3. Numbers from logs: placeholders ([RS07](/lessons/RS07), [RS09](/lessons/RS09))

Write `report/report.md.tmpl` with placeholders `{{metric:path|format}}`. `render.py` looks the dotted path up in `metrics.json`, formats it (`pct1`, `f3`, `int`) and refuses unknown keys, unknown formats and anything left unresolved. A second guard is a test that scans the Results section of the template for bare numbers (two or more digits, or decimals) outside placeholders. The effect is that when you rerun the benchmark the report updates itself, and a stale number is impossible.

### 4. Report structure and calibrated claims ([RS07](/lessons/RS07))

Required sections: Abstract, Introduction, Related work (at least 8 references with a URL or DOI), Method, Experiments, Results, Limitations, Safety, Ethics, Reproducibility statement, References; 3000 to 6000 words. Calibrate verbs to evidence: "we measured" for what the logs show, "suggests" for a result with a wide interval, "we did not test" for what is missing. In this project the most important calibrated sentence is: everything here is **simulation only**; the sealed twin estimates sensitivity to one family of perturbations and is not evidence about a real robot. The safety supervisor protects a simulation and is not a certified safety function (see [CAP07](/lessons/CAP07)). Link `docs/model_card.md` for the learned parts and `docs/hazard_table.md` for the hazards.

### 5. Release checklist ([RS09](/lessons/RS09), [HW12](/lessons/HW12))

`docs/RELEASE_CHECKLIST.md` follows the Papers with Code checklist (dependencies, training scripts, evaluation scripts, pretrained models, a results table with the commands that produce it). The acceptance test counts the boxes: all must be ticked. Add a bring-up and debug log as an appendix in the style of HW12: symptom, hypothesis, test, result, so a reader can see how you found problems.

### 6. The graduation rule

A milestone score is $100\,(0.6\,a+0.4\,r/(4m))$ where $a$ is the weighted fraction of automated checks passed, $r$ the sum of your rubric points (0 to 4 for each of $m$ criteria). The total is $\sum_i w_i s_i/100$ with weights CAP01 8, CAP02 12, CAP03 12, CAP04 11, CAP05 13, CAP06 12, CAP07 10, CAP08 14, CAP09 8 (sum 100). **Graduated** means all of: every gate of every milestone passes; every milestone score is at least 60; the weighted total is at least 70; CAP08 reports zero safety violations; `make reproduce-smoke` passes on a clean checkout. **Merit**: total at least 80. **Distinction**: total at least 90 and at least one stretch (visual odometry, ACT or LeRobot sim policy, LLM or CLIP parser variant, Nav2 baseline comparison, or the hardware tier with a real-versus-sim table). The hardware tier alone never replaces a failing gate. A failed gate does not lock anything in the app: it keeps the milestone in progress.

## Worked example

Illustrative values, not from a real run.

A learner's final scores (automated fraction $a$ and rubric points out of 16, four criteria) give these milestone scores and the weighted total:

| Milestone | Weight | $a$ | Rubric /16 | Score |
|---|---|---|---|---|
| CAP01 | 8 | 1.00 | 14 | 95.0 |
| CAP02 | 12 | 0.90 | 13 | 86.5 |
| CAP03 | 12 | 0.85 | 12 | 81.0 |
| CAP04 | 11 | 0.90 | 12 | 84.0 |
| CAP05 | 13 | 0.80 | 11 | 75.5 |
| CAP06 | 12 | 0.75 | 10 | 70.0 |
| CAP07 | 10 | 0.90 | 12 | 84.0 |
| CAP08 | 14 | 0.90 | 13 | 86.5 |
| CAP09 | 8 | 1.00 | 13 | 92.5 |

The weighted total is 83.1: Merit, provided all gates passed, no milestone is below 60 (the lowest is 70.0), CAP08 has zero safety violations and the smoke test passed on a clean checkout. A Nav2 comparison stretch does not lift the grade to Distinction because 83.1 is below 90. The same arithmetic in code:

```python
# Standalone: the graduation arithmetic of plan section 7 with illustrative inputs (standard library only).
WEIGHTS = {"CAP01": 8, "CAP02": 12, "CAP03": 12, "CAP04": 11, "CAP05": 13,
           "CAP06": 12, "CAP07": 10, "CAP08": 14, "CAP09": 8}
# milestone: (fraction of weighted automated checks passed, rubric points out of 4 x 4 criteria)
inputs = {"CAP01": (1.00, 14), "CAP02": (0.90, 13), "CAP03": (0.85, 12), "CAP04": (0.90, 12),
          "CAP05": (0.80, 11), "CAP06": (0.75, 10), "CAP07": (0.90, 12), "CAP08": (0.90, 13), "CAP09": (1.00, 13)}
total = 0.0
for k, (auto, rubric) in inputs.items():
    score = 100 * (0.6 * auto + 0.4 * rubric / 16)
    total += WEIGHTS[k] * score / 100
    print(f"{k}  weight {WEIGHTS[k]:2d}  score {score:5.1f}")
print(f"weighted total {total:.1f}  ->", "Merit" if total >= 80 else "Pass" if total >= 70 else "not graduated")
print("Distinction needs total >= 90 AND a stretch; here the total is the limit, not the stretch.")
```

A smoke run, illustrative: six seeds 1000 to 1005, expected outcomes `[ok, ok, GRASP_SLIP, ok, ok, GRASP_SLIP]`, rerun in 734 s inside the container, identical outcomes: pass (the limit is 1200 s). A report template excerpt and how the placeholders resolve:

```markdown
### Results (excerpt of report.md.tmpl)

On {{metric:nominal.n|int}} held-out nominal episodes the system completed the task in
{{metric:nominal.rate|pct1}} of cases (Wilson 95 % interval {{metric:nominal.wilson_lo|pct1}} to
{{metric:nominal.wilson_hi|pct1}}). On the sealed twin the rate was {{metric:twin.rate|pct1}}; the estimated
gap is {{metric:gap.difference|f3}} (95 % CI {{metric:gap.ci_lo|f3}} to {{metric:gap.ci_hi|f3}}).
Removing landmark updates lowered success by {{metric:ablations.no_landmarks.effect_pp|f2}} points
(exact paired p = {{metric:ablations.no_landmarks.mcnemar_p|f3}}).
```

With the illustrative metrics of CAP08 this renders as "On 120 held-out nominal episodes the system completed the task in 78.3 % of cases (Wilson 95 % interval 70.1 % to 84.8 %)". Change the benchmark, rerun `make report`, and the sentence changes with it.

## Exercises

1. **(Easy)** *Placeholders.* `nominal.wilson_lo` is 0.7014. What does `{{metric:nominal.wilson_lo|pct1}}` render to, and `{{metric:nominal.n|int}}` for `n = 120.0`? What happens for `{{metric:nominal.p95}}` if the key does not exist?
2. **(Easy)** *Weighted total.* Milestone scores are CAP01 to CAP09 = 90, 85, 80, 70, 75, 65, 72, 78, 88 with the official weights. Compute the total and the grade if all gates passed.
3. **(Medium)** *Verdict.* Total 91, the Nav2 stretch done, zero safety violations, smoke test passed, but one CAP05 gate failed. What is the verdict and what do you do next?
4. **(Medium)** *Smoke mismatch.* Six seeds are rerun and seed 1003 is `success` in the stored file but `GRASP_SLIP` now. List four plausible causes of non-determinism and the order in which you would test them.
5. **(Medium)** *Image design.* A teammate's Dockerfile runs `pip install -r requirements.txt` at container start and the README says "needs internet for first run". Why does this break the reproducibility claim, and what do you change?
6. **(Medium)** *Calibrated claims.* Rewrite "Our robot achieves 78 % success in the real world and solves sim-to-real" so that it is true for this project.
7. **(Medium)** *Reference check.* Which of these entries counts toward the 8 references: (a) "Tobin et al. 2017, https://arxiv.org/abs/1703.06907", (b) "Henderson et al. 2018, Deep RL that matters", (c) "Doe 2020, doi 10.1000/xyz123", (d) "see Wikipedia"?
8. **(Hard)** *Demo storyboard.* Allocate 180 seconds for the demo video. Which shots are mandatory and what overlay must be visible? Give segment durations that sum to 180 s.
9. **(Hard)** *Merit or Distinction.* Total 88, hardware tier done with a real-versus-sim table, everything else passes. Another learner has total 92 and only did the hardware tier without the table. Decide both.
10. **(Hard, mini-project)** *Clean-checkout dry run.* Clone your repository into an empty directory, build the container, run `docker run --network none ... make reproduce-smoke`, and time it. Record every problem (missing file, network access, unpinned version, absolute path) and fix it. State what observation would show that your release is not reproducible.

## Reference implementation

This is the skeleton of `report/render.py`, the module that resolves placeholders and fails on anything unknown. Implement it with the standard library. The acceptance test imports `render` from it.

```python
"""report/render.py: resolve {{metric:path|format}} placeholders from runs/final/metrics.json.

A number in the report that does not come from metrics.json is a bug, so unknown paths fail loudly.
"""
from __future__ import annotations

import re

PLACEHOLDER = re.compile(r"\{\{\s*metric:([A-Za-z0-9_.\-]+)(?:\|([a-z0-9]+))?\s*\}\}")
FORMATS = {                      # name -> formatter; add your own, keep them boring
    "int": lambda v: str(int(round(v))),
    "f2": lambda v: f"{v:.2f}",
    "f3": lambda v: f"{v:.3f}",
    "pct0": lambda v: f"{100 * v:.0f} %",
    "pct1": lambda v: f"{100 * v:.1f} %",
}


def lookup(metrics: dict, path: str) -> float:
    """Follow a dotted path such as 'nominal.wilson_lo'.

    Raises KeyError("unknown metric: <path>") if any part is missing, and
    KeyError("metric is not a number: <path>") for dicts, lists, booleans and None.
    """
    raise NotImplementedError


def render(template: str, metrics: dict) -> str:
    """Replace every placeholder (default format f3). Unknown formats raise KeyError.
    After substitution no '{{' may remain: raise ValueError otherwise."""
    raise NotImplementedError


def main() -> None:
    """Read runs/final/metrics.json and report/report.md.tmpl, write report/report.md."""
    raise NotImplementedError
```

## Independent practice

### Goal
Turn the finished project into a release a stranger can rerun, write the technical report from your own metrics with no hand-typed numbers, record the demo, complete the checklist and run the graduation calculator on your own scores. Weight in graduation: 8 points of 100.

### Setup
Work in `~/corebot-capstone`, tag candidate `v1.0` only when the tree is clean. You need Docker (optional but recommended), `make`, `git`, Python 3.11 or newer and `ruff` (`pip install ruff`). Allow about 16 hours: roughly 6 for the release, 7 for the report, 1 for the demo, 2 for the dry run and fixes. Keep the report at 3000 to 6000 words; shorter and clearer is better than long.

```bash
cd ~/corebot-capstone
mkdir -p report/figures tools runs/smoke docs
# report/render.py        <- the reference skeleton above, implemented
# tools/release_check.py  <- starter stubs below (headings, references, checklist, smoke_matches)
# tools/graduate.py       <- weights, gates, Merit/Distinction
python -m pytest -q tests/acceptance/test_cap09.py
python tools/graduate.py docs/scores.json
```

### Tasks
1. **Release.** Add the `Dockerfile` and `Makefile` below (adapt names to your repo), a `requirements.lock` with exact versions, a `LICENSE` and a `README.md` whose "Quickstart" block has 10 commands or fewer.
2. **Smoke set.** Choose 6 seeds, run them once, save outcomes to `runs/smoke/expected.json` (`{"episodes": [{"seed", "success", "reason", "steps"}], "elapsed_s": 0}`), and write `tools/compare_smoke.py`. `make reproduce-smoke` writes `runs/smoke/actual.json` with the measured `elapsed_s`.
3. **Renderer.** Implement `report/render.py` (reference skeleton) and `tools/release_check.py` (starter stubs).
4. **Report.** Write `report/report.md.tmpl` with the required sections and at least 8 references; at least three figures generated by `report/make_figures.py` from `runs/`; every number in Results via a placeholder.
5. **Model card and hazard table.** `docs/model_card.md` (intended use, data, metrics with CI, limits for the learned parts) and `docs/hazard_table.md` (from CAP07), both linked from the report.
6. **Demo.** A 3-minute video: typed instruction, parse result, estimator pose and detections overlaid, grasp, placement, and one safety stop. Add the link or file path to the README.
7. **Checklist.** Complete `docs/RELEASE_CHECKLIST.md` (every box ticked only after you verified the item).
8. **Graduation.** Fill `docs/scores.json` (automated fraction, rubric points with linked evidence for each, gates, stretches), run `python tools/graduate.py docs/scores.json`, commit, tag `v1.0`.

The `Makefile` and `Dockerfile` below are the reference layout.

```make
.PHONY: doctor test reproduce reproduce-smoke report docker

doctor:                      ## tools present?
	@for t in python3 gcc cmake git; do command -v $$t >/dev/null || echo "missing: $$t"; done

test:
	python -m pytest -q tests/unit tests/acceptance

reproduce-smoke:             ## 6 seeded episodes, compare with runs/smoke/expected.json
	python bench/run_bench.py --split smoke --seeds 1000-1005 --out runs/smoke/actual.json
	python tools/compare_smoke.py runs/smoke/expected.json runs/smoke/actual.json

report:                      ## metrics.json -> report/report.md (fails on unknown keys)
	python bench/metrics.py && python report/render.py

reproduce: reproduce-smoke report

docker:
	docker build -t corebot:v1.0 .
	docker run --rm --network none corebot:v1.0 make reproduce-smoke
```

```dockerfile
FROM python:3.11.9-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git make \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
# Dependencies are baked into the image: nothing is downloaded when the container runs.
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY . .
RUN pip install --no-cache-dir -e . && cmake -S firmware -B firmware/build && cmake --build firmware/build
ENV MUJOCO_GL=osmesa OMP_NUM_THREADS=1 PYTHONHASHSEED=0
CMD ["make", "reproduce-smoke"]
```

The checklist (ticked here only as an example of the format; tick yours when each item is verified):

```markdown
# Release checklist (after the ML Code Completeness Checklist of paperswithcode/releasing-research-code)

- [x] Dependencies pinned in pyproject.toml and requirements.lock
- [x] Dockerfile builds; `docker run --network none` passes reproduce-smoke
- [x] Training scripts (train_ppo.py, bc.py) with seeds and CPU config documented
- [x] Evaluation scripts (bench/run_bench.py, bench/metrics.py) regenerate metrics.json from logs
- [x] Trained weights (< 20 MB) committed or linked, with checksums
- [x] README quickstart has 10 commands or fewer
- [x] README results table lists each headline number with the command that produces it
- [x] LICENSE present; third-party assets (Menagerie SO-101) keep their licences
- [x] docs/model_card.md and docs/hazard_table.md exist and are linked from the report
- [x] Report: every number in Results comes from a placeholder; limitations and "simulation only" stated
- [x] Git tag v1.0 created on a clean working tree
- [x] Dry run on a fresh clone in a fresh venv or container completed and timed
```

### Starter code
Interface stubs for the release checks and the graduation calculator:

```python
"""tools/release_check.py and tools/graduate.py: interface stubs."""
from __future__ import annotations

REQUIRED_HEADINGS = ["Abstract", "Introduction", "Related work", "Method", "Experiments", "Results",
                     "Limitations", "Safety", "Ethics", "Reproducibility statement", "References"]
WEIGHTS = {"CAP01": 8, "CAP02": 12, "CAP03": 12, "CAP04": 11, "CAP05": 13,
           "CAP06": 12, "CAP07": 10, "CAP08": 14, "CAP09": 8}
STRETCHES = {"visual_odometry", "act_sim_policy", "llm_or_clip_parser", "nav2_baseline", "hardware_real_vs_sim"}


def missing_headings(markdown: str) -> list[str]:
    """Required level-2 headings (case-insensitive) that the report lacks."""
    raise NotImplementedError


def word_count(markdown: str) -> int:
    """Words outside fenced code blocks."""
    raise NotImplementedError


def references(markdown: str) -> list[str]:
    """List items under '## References' that contain a well-formed http(s) URL or a DOI (10.xxxx/...)."""
    raise NotImplementedError


def missing_figures(markdown: str, root: str = ".") -> list[str]:
    """Image paths in ![alt](path) that do not exist under root (http links are skipped)."""
    raise NotImplementedError


def checklist(markdown: str) -> tuple[int, int]:
    """(done, total) for '- [x]' and '- [ ]' items."""
    raise NotImplementedError


def quickstart_commands(readme: str) -> int | None:
    """Command lines (no blanks, no # comments) in the first code block under a Quickstart heading; None if absent."""
    raise NotImplementedError


def smoke_matches(expected: dict, actual: dict, max_seconds: float = 1200) -> bool:
    """Stored outcomes of >= 6 smoke seeds equal a fresh rerun exactly, and the rerun took <= max_seconds."""
    raise NotImplementedError


def milestone_score(automated_fraction: float, rubric_points: float, criteria: int) -> float:
    """100 * (0.6 * automated + 0.4 * rubric_points / (4 * criteria)). ValueError for out-of-range input."""
    raise NotImplementedError


def evaluate(data: dict) -> dict:
    """Graduation verdict: keys total, scores, graduated, grade ('not graduated'|'Pass'|'Merit'|'Distinction'), reasons.
    Graduated needs: every gate passed, every milestone >= 60, weighted total >= 70, zero CAP08 safety violations,
    reproduce-smoke passed on a clean checkout. Merit: total >= 80. Distinction: total >= 90 and a known stretch."""
    raise NotImplementedError
```

### Tests
`tests/acceptance/test_cap09.py` reads your report template, `runs/final/metrics.json`, `runs/smoke/*.json`, the repository state and `docs/`. Checks marked G are gates. Thresholds are provisional starting values (see the plan rationale); tighten them once your own reference run exists.

- Report numbers resolve (G): the template renders with no `{{` left, all required headings exist, 3000 to 6000 words (a short paper is readable and a long one rarely is), all figures exist, and Results has no hand-typed number.
- References: at least 8 entries with a URL or DOI (the minimum for a credible related-work section).
- Reproduce smoke (G): stored and fresh outcomes for the 6 seeds are identical and the rerun took at most 1200 s (a reader will not wait longer).
- Repository state: tag `v1.0` exists, clean working tree, `LICENSE` present, quickstart of at most 10 commands, `ruff check .` passes (skipped with a message if `ruff` is not installed, which counts as not passed for the gate).
- Model card and hazard table exist and the report links them.
- Release checklist: at least 10 items, all ticked.
- Graduation calculator: Merit for 89.0, no Distinction below 90, a failed gate means not graduated.
- Your scores file is complete for all nine milestones.

```python
"""CAP09 acceptance tests. Gates (G): test_report_numbers_resolve, test_reproduce_smoke_matches."""
import json
import pathlib
import re
import shutil
import subprocess

import pytest

from report.render import render
from tools.graduate import WEIGHTS, evaluate
from tools.release_check import (checklist, missing_figures, missing_headings, quickstart_commands,
                                 references, smoke_matches, word_count)

TEMPLATE = pathlib.Path("report/report.md.tmpl")


def _metrics():
    return json.loads(pathlib.Path("runs/final/metrics.json").read_text())


def _report():
    return render(TEMPLATE.read_text(), _metrics())      # raises on an unknown metric or an unresolved {{...}}


def test_report_numbers_resolve():                                # G
    text = _report()
    assert "{{" not in text and "}}" not in text
    assert missing_headings(text) == []
    assert 3000 <= word_count(text) <= 6000
    assert missing_figures(text) == []
    results = TEMPLATE.read_text().split("## Results")[1].split("\n## ")[0]
    bare = re.sub(r"\{\{[^}]*\}\}", "", results)
    assert re.findall(r"\d+\.\d+|\d{2,}", bare) == [], "a number in Results is typed by hand"


def test_references():
    assert len(references(_report())) >= 8


def test_reproduce_smoke_matches():                               # G
    expected = json.loads(pathlib.Path("runs/smoke/expected.json").read_text())
    actual = json.loads(pathlib.Path("runs/smoke/actual.json").read_text())
    assert smoke_matches(expected, actual, max_seconds=1200)


def test_repository_state():
    git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
    assert "v1.0" in git("tag").split()
    assert git("status", "--porcelain") == ""
    assert pathlib.Path("LICENSE").exists()
    n = quickstart_commands(pathlib.Path("README.md").read_text())
    assert n is not None and n <= 10
    if shutil.which("ruff"):
        assert subprocess.run(["ruff", "check", "."]).returncode == 0
    else:
        pytest.skip("ruff not installed: install it, this check counts as not passed for the gate")


def test_model_card_and_hazard_table_cross_referenced():
    for f in ("docs/model_card.md", "docs/hazard_table.md"):
        assert pathlib.Path(f).exists(), f
    text = TEMPLATE.read_text()
    assert "model_card.md" in text and "hazard_table.md" in text


def test_release_checklist_complete():
    done, total = checklist(pathlib.Path("docs/RELEASE_CHECKLIST.md").read_text())
    assert total >= 10 and done == total


def test_graduation_calculator():
    ok = {"milestones": {k: {"automated": 0.9, "rubric": 14, "criteria": 4, "gates_passed": True} for k in WEIGHTS},
          "cap08_safety_violations": 0, "reproduce_smoke_clean_checkout": True, "stretches": []}
    v = evaluate(ok)
    assert v["graduated"] and v["grade"] == "Merit" and abs(v["total"] - 89.0) < 0.1
    assert evaluate({**ok, "stretches": ["nav2_baseline"]})["grade"] == "Merit"        # 89 < 90: no Distinction
    bad = json.loads(json.dumps(ok)); bad["milestones"]["CAP05"]["gates_passed"] = False
    assert not evaluate(bad)["graduated"]


def test_my_scores_file_is_complete():
    v = evaluate(json.loads(pathlib.Path("docs/scores.json").read_text()))
    assert set(v["scores"]) == set(WEIGHTS)
```

### Expected output
With a clean tagged repository and all artefacts:

```
........                                                                 [100%]
8 passed in 1.4s
```

A sample `docs/scores.json` (illustrative) and the verdict it produces, total 83.1 and grade Merit:

```json
{
  "milestones": {
    "CAP01": {"automated": 1.00, "rubric": 14, "criteria": 4, "gates_passed": true},
    "CAP02": {"automated": 0.90, "rubric": 13, "criteria": 4, "gates_passed": true},
    "CAP03": {"automated": 0.85, "rubric": 12, "criteria": 4, "gates_passed": true},
    "CAP04": {"automated": 0.90, "rubric": 12, "criteria": 4, "gates_passed": true},
    "CAP05": {"automated": 0.80, "rubric": 11, "criteria": 4, "gates_passed": true},
    "CAP06": {"automated": 0.75, "rubric": 10, "criteria": 4, "gates_passed": true},
    "CAP07": {"automated": 0.90, "rubric": 12, "criteria": 4, "gates_passed": true},
    "CAP08": {"automated": 0.90, "rubric": 13, "criteria": 4, "gates_passed": true},
    "CAP09": {"automated": 1.00, "rubric": 13, "criteria": 4, "gates_passed": true}
  },
  "cap08_safety_violations": 0,
  "reproduce_smoke_clean_checkout": true,
  "stretches": ["nav2_baseline"]
}
```

Before you have artefacts, the tests fail with `FileNotFoundError` or `NotImplementedError`; that is the intended starting state.

### Extension challenge
Add a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs `make test` and builds the image; publish the demo with captions; or write a two-page "lessons learned" note per milestone and fold it into the report's discussion. Optional hardware appendix: if you built the ESP32 base, add a real-versus-sim table (settling time, overshoot, steady-state error of the same step test) and a HW12-style bring-up log; mark the section "hardware, not part of the graded claims". Never present simulation numbers as real-world results.

### Library track
Use Jinja2 with `StrictUndefined` as a stricter template engine and let `ruff` enforce the lint gate; the output should match your own renderer for the same template.

```python
# Needs: pip install jinja2 ruff     (the same checks, with industrial-strength tools)
import json
import pathlib
import subprocess

from jinja2 import Environment, StrictUndefined

metrics = json.loads(pathlib.Path("runs/final/metrics.json").read_text())

# 1. A template engine that refuses unknown keys: StrictUndefined raises instead of printing a blank.
env = Environment(undefined=StrictUndefined)
tmpl = env.from_string("Nominal success was {{ '%.1f' % (100 * m.nominal.rate) }} % (n = {{ m.nominal.n }}).")
print(tmpl.render(m=metrics))      # dotted access works on dicts; a missing key raises UndefinedError

# 2. Lint gate exactly as the acceptance test expects it
result = subprocess.run(["ruff", "check", "."], capture_output=True, text=True)
print(result.stdout or "ruff: all checks passed")
assert result.returncode == 0
```

## Verification

Run the whole suite from a fresh clone, not from your working directory: `git clone . /tmp/check && cd /tmp/check && make test`. Change one number in `metrics.json` and confirm the report changes; delete a key and confirm `make report` fails. Change one expected smoke outcome and confirm `make reproduce-smoke` reports a mismatch. Read the report as a stranger: can you find the command that produces each headline number? Is "simulation only" stated in the abstract and the limitations? Scoring: CAP09 carries weight 8 of 100 (60 % automated, 40 % rubric: clarity and honesty of the report, demo comprehensibility, whether a reader could redo it, appropriate scope claims). Gates: the reproduce-smoke test and report numbers resolving. For graduation, `reproduce-smoke` must pass on a clean checkout and all other conditions of the rule must hold.

## Failure modes

- Numbers typed by hand that drift from the logs after a rerun.
- Figures without axis labels, units or intervals.
- A Docker image that needs the network at run time, or an unpinned base tag.
- Dependencies without exact versions; "works on my machine" with a global package.
- Undocumented hardware assumptions (GPU, display, EGL versus OSMesa).
- Claiming sim-to-real results from simulation, or implying the supervisor is certified safety.
- A dirty working tree at tag time, or a tag that points at a different commit than the report.
- The demo shows the best episode only; show a failure and how the system reacts.
- Hidden non-determinism: thread count, hash randomisation, time-based seeds; the smoke test flakes.
- The checklist ticked in bulk without verifying each item.

## Alternatives and trade-offs

Instead of Docker you can use a fresh virtual environment with a lock file (lighter, but system packages such as `cmake` are your problem) or Nix (strongest, steepest learning curve). Instead of a placeholder renderer you can use a notebook or Quarto/Jupyter Book (convenient, but easier to leave stale cells behind). A single `make` entry point is simple; `just` or `tox` give nicer ergonomics. A short paper is better than a long one: many readers only need the abstract, one figure and the limitations. For the demo, a screen recording with captions is enough; a polished edit is optional. If your machine cannot run the container, a documented venv path is acceptable, but the smoke test must still pass from a clean checkout.

## Transfer and retention

This is the last milestone, so the transfer is outward: the same release discipline (pinned environment, smoke test, generated numbers, calibrated claims, checklist) applies to any research or portfolio project, and the report and demo are the artefacts you can show others. Recall prompts:

1. What are the five conditions for "graduated", and which one is about the final milestone only?
2. Why does the smoke test compare outcomes and not raw floating-point numbers?
3. What does `render.py` do when a key is missing, and why?
4. Write a calibrated version of a claim from your own report.
5. What is the difference between Merit and Distinction in this course?

## Exercise answers

1. $0.7014\to$ "70.1 %" (0.7014 times 100 rounded to one decimal). `120.0` with `int` renders "120". A missing key raises `KeyError("unknown metric: nominal.p95")` and the build fails, which is the intended behaviour: a report must never print a blank or a guess.
2. Weighted sum: $8\cdot90+12\cdot85+12\cdot80+11\cdot70+13\cdot75+12\cdot65+10\cdot72+14\cdot78+8\cdot88=7741$, divided by 100: 77.4. At least 70 and below 80: "Pass" (graduated, no Merit), provided every milestone is at least 60 (the lowest is 65).
3. Not graduated: a failed gate blocks graduation whatever the total. The total and the stretch do not compensate. Next: fix the CAP05 gate (read its failing test, fix the cause, rerun the CAP05 acceptance suite), update the scores, rerun the graduation calculator. Distinction would then be possible: total 91 with a stretch.
4. Causes: (a) multithreaded numerical libraries (set `OMP_NUM_THREADS=1`), (b) a seed that is not fully used (random call outside `default_rng(seed)`), (c) different library versions or CPU between the two runs (compare lock file and `pip freeze`), (d) wall-clock dependence (timeouts, `time.time()` in logic). Test order: rerun the same seed twice on the same machine; if they differ it is (a), (b) or (d); if they agree but differ across environments, it is (c). Then bisect by disabling parts of the pipeline.
5. The claim "reproducible" now depends on a package index being available and on whatever versions it serves that day; the run also needs the internet. Bake the dependencies into the image at build time from a lock file with exact versions, copy the project in, and run with `--network none` in the test. Document the base image tag.
6. For example: "In simulation, our system completed the task in 78 % of 120 held-out episodes (Wilson 95 % interval 70 % to 85 %). On a sealed perturbed twin the rate was 58 %. We did not test a real robot, so we make no claim about sim-to-real transfer."
7. (a) counts (URL), (c) counts (DOI is well-formed). (b) has no URL or DOI and does not count for the automated test (add the arXiv URL). (d) is not a reference.
8. Mandatory shots: the typed instruction and the parse result (15 s), localisation with the pose and covariance overlay (20 s), navigation with the planned path (25 s), detections with labels overlaid and the grasp (40 s), placement into the bin (20 s), a safety stop with a person entering the zone (25 s), a metrics slide with interval and the limitations sentence (20 s), title and closing (15 s). Sum: 15 + 20 + 25 + 40 + 20 + 25 + 20 + 15 = 180 s. Overlay must show estimator pose, detections and the supervisor state.
9. Total 88 is below 90: Merit, even with a real-versus-sim table. The second learner has 92 but the hardware tier counts as a stretch only with a real-versus-sim table, so they do not meet the Distinction condition: Merit, and they can make the table (or do another stretch) to earn Distinction. The hardware tier never replaces a failing gate in either case.
10. A good dry-run log lists each defect with its fix (for example "asset path was absolute", "numpy not pinned", "needs network for weights download: weights now in the image"), the time of `make reproduce-smoke` (must be at most 20 min), and the rejecting observation: any mismatch of a stored outcome, any network access during the run, or a different result after a second identical run.

## Further reading

- [Releasing research code (Papers with Code checklist)](https://github.com/paperswithcode/releasing-research-code): the checklist behind `RELEASE_CHECKLIST.md`.
- [Henderson et al., Deep Reinforcement Learning that Matters](https://arxiv.org/abs/1709.06560): why seeds, variance and reporting practice decide whether results can be trusted.
- [Docker documentation: building best practices](https://docs.docker.com/build/building/best-practices/): pinned bases, layers and small images.
- [GNU Make manual](https://www.gnu.org/software/make/manual/make.html): targets and phony targets.
- [pytest documentation](https://docs.pytest.org/en/stable/): fixtures, skips and markers used by the acceptance suite.
- **More practice:** [TidyBot (arXiv 2305.05658)](https://arxiv.org/abs/2305.05658) is a good example of a system paper with a clear task, baselines and limitations; read it as a model for your own report.
