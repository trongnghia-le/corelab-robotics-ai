#!/bin/sh
# make_skeleton.sh: create the CoreBot Tidy capstone repository skeleton (CoreLab plan, section 4).
#
# Usage:   sh make_skeleton.sh [TARGET_DIR] [PATH_TO_evalkit.py]
# Default: TARGET_DIR=$HOME/corebot-capstone
#
# Idempotent: existing directories are reused and existing files are NEVER overwritten
# (they are reported as "keep"). Run it twice and the second run changes nothing.
set -eu

TARGET=${1:-"$HOME/corebot-capstone"}
EVALKIT_SRC=${2:-}
created=0
kept=0

mkd() { mkdir -p "$TARGET/$1"; }

# put REL < stdin : write a file only if it does not exist yet.
put() {
  f="$TARGET/$1"
  if [ -e "$f" ]; then
    echo "keep   $1"; kept=$((kept + 1)); cat > /dev/null; return 0
  fi
  mkdir -p "$(dirname "$f")"
  cat > "$f"
  echo "create $1"; created=$((created + 1))
}

for d in configs models/meshes firmware/core firmware/tests src/corebot/sim src/corebot/estimation \
         src/corebot/perception src/corebot/mapping src/corebot/planning src/corebot/manipulation \
         src/corebot/learning src/corebot/task src/corebot/safety ros2_ws/src bench runs \
         tests/unit tests/acceptance report/figures docs sysid .github/workflows; do
  mkd "$d"
done

# Python packages: every source directory gets an __init__.py
for d in src/corebot src/corebot/sim src/corebot/estimation src/corebot/perception src/corebot/mapping \
         src/corebot/planning src/corebot/manipulation src/corebot/learning src/corebot/task src/corebot/safety; do
  put "$d/__init__.py" </dev/null
done

put README.md <<'X'
# CoreBot Tidy (CoreLab capstone)

A mobile manipulator in a MuJoCo room that follows "put the red block in the blue bin".
Start with SPEC.md, then `make test`. Milestones CAP01..CAP09 are described in CoreLab.
X

put SPEC.md <<'X'
# SPEC: CoreBot Tidy

Each requirement has an id, a metric, a threshold (with a one-line rationale) and the test that checks it.

| id  | requirement | metric | threshold | rationale | test |
|-----|-------------|--------|-----------|-----------|------|
| SR1 | (replace me) | | | | tests/acceptance/test_cap01.py::test_determinism |
X

put LICENSE <<'X'
Choose a license for your own code (for example MIT) and keep the Menagerie model licenses
next to any asset you copy into models/meshes/.
X

put pyproject.toml <<'X'
[project]
name = "corebot"
version = "0.1.0"
requires-python = ">=3.10"
# Pin exact versions once you have a working environment (pip freeze), for example:
# dependencies = ["mujoco==3.x.y", "numpy==x.y.z", "pytest==x.y.z"]
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
X

put Makefile <<'X'
.PHONY: test unit acceptance doctor
test: unit
unit:
	python3 -m pytest -q tests/unit
acceptance:
	python3 -m pytest -q tests/acceptance
doctor:
	@for t in python3 git gcc cmake; do command -v $$t >/dev/null && echo "ok   $$t" || echo "MISS $$t (install it before CAP02)"; done
X

put Dockerfile <<'X'
# Fill in during CAP09 (reproducible environment).
FROM python:3.11-slim
WORKDIR /work
X

put .gitignore <<'X'
__pycache__/
*.pyc
.venv/
runs/*
!runs/.gitkeep
!runs/*/summary.json
*.npz
X

put runs/.gitkeep </dev/null

put .github/workflows/ci.yml <<'X'
name: ci
on: [push]
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install pytest numpy && python -m pytest -q tests/unit
X

for f in robot world ekf nav safety bench; do
  put "configs/$f.yaml" <<X
# configs/$f.yaml: fill in during the matching milestone
X
done

put src/corebot/interfaces.py <<'X'
"""The contract between modules: frozen dataclasses, SI units, `stamp` in seconds."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WheelCmd:
    stamp: float
    v: float  # m/s, forward
    w: float  # rad/s, counter-clockwise


@dataclass(frozen=True)
class WheelState:
    stamp: float
    left_counts: int   # uint16, wraps
    right_counts: int  # uint16, wraps
    status: int = 0


@dataclass(frozen=True)
class OdomSample:
    stamp: float
    x: float
    y: float
    theta: float
    v: float
    w: float


@dataclass(frozen=True)
class SafetyState:
    stamp: float
    level: str  # "OK" | "SLOW" | "HOLD" | "ESTOP"
    reasons: tuple = ()
X

put src/corebot/sim/world.py <<'X'
"""Seeded scene generation (CAP01). Use np.random.default_rng(seed) only."""


def make_scene(seed: int) -> dict:
    raise NotImplementedError
X

put src/corebot/sim/env.py <<'X'
"""Env.reset(seed) / step(action) API (CAP01)."""


class Env:
    def reset(self, seed: int):
        raise NotImplementedError

    def step(self, action):
        raise NotImplementedError
X

put src/corebot/manipulation/kinematics.py <<'X'
"""Own forward kinematics of the arm (CAP01)."""


def fk(q):
    raise NotImplementedError
X

if [ -n "$EVALKIT_SRC" ] && [ -f "$EVALKIT_SRC" ]; then
  if [ -e "$TARGET/src/corebot/evalkit.py" ]; then
    echo "keep   src/corebot/evalkit.py"; kept=$((kept + 1))
  else
    cp "$EVALKIT_SRC" "$TARGET/src/corebot/evalkit.py"
    echo "create src/corebot/evalkit.py"; created=$((created + 1))
  fi
else
  put src/corebot/evalkit.py <<'X'
# Download https://<corelab>/practice/capstone/evalkit.py and replace this file.
X
fi

put tests/unit/test_smoke.py <<'X'
def test_package_imports():
    import corebot.interfaces as i
    assert i.WheelCmd(0.0, 0.1, 0.0).v == 0.1
X

put tests/acceptance/test_cap01.py <<'X'
# Replace with the CAP01 acceptance file from the CoreLab lesson.
X

put docs/decisions.md <<'X'
# Decisions log (one short entry per decision: context, choice, alternatives, date)
X

put report/report.md.tmpl <<'X'
# CoreBot Tidy report
Numbers appear as {{metric:name}} placeholders and are filled from runs/*/metrics.json.
X

put firmware/CMakeLists.txt <<'X'
cmake_minimum_required(VERSION 3.16)
project(corebot_fw C)
enable_testing()
# CAP02: add_library(fw SHARED core/*.c) and the ctest targets here.
X

echo "done: $created created, $kept kept, target $TARGET"
