---
{
  "id": "cap02-capstone",
  "module_id": "CAP02",
  "title": "Capstone firmware-in-the-loop base: speed loop, CRC8 protocol, watchdog and odometry",
  "summary": "Build the CoreBot Tidy drive base as portable C run on the host through ctypes: a quadrature decoder, a PI wheel-speed loop with anti-windup, a CRC-8 framed serial protocol, a command watchdog, a motor model fitted from step data and calibrated odometry, verified by an offline acceptance suite.",
  "estimated_minutes": 1680,
  "project_minutes": 1680,
  "prerequisites": [
    "CAP01",
    "HW10",
    "HW11",
    "C09",
    "S06",
    "CPP08",
    "S08"
  ],
  "source_refs": [
    {
      "title": "PlatformIO native platform",
      "url": "https://docs.platformio.org/en/latest/platforms/native.html"
    },
    {
      "title": "Python ctypes documentation",
      "url": "https://docs.python.org/3/library/ctypes.html"
    },
    {
      "title": "CTest manual (CMake)",
      "url": "https://cmake.org/cmake/help/latest/manual/ctest.1.html"
    },
    {
      "title": "Cyclic redundancy check (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Cyclic_redundancy_check"
    },
    {
      "title": "Vulcanexus micro-ROS documentation",
      "url": "https://micro.vulcanexus.org/docs/"
    },
    {
      "title": "ros2_control (Jazzy)",
      "url": "https://control.ros.org/jazzy/index.html"
    }
  ],
  "objectives": [
    "Implement and unit-test embedded-style C (quadrature decoder, PI speed loop with anti-windup, CRC-8 framing, watchdog) and call it from the simulator through ctypes.",
    "Meet explicit step-response, protocol and watchdog specifications using the evalkit helpers and read the metrics from logged artefacts.",
    "Identify a first-order motor model from step data and report the fit honestly.",
    "Dead-reckon odometry from wheel counts and calibrate wheel radius and track width in the right order.",
    "Budget latency and link load for the 100 Hz host loop and choose a watchdog timeout with a stated rationale."
  ],
  "core_theory": [
    "Embedded motor speed control (HW10)",
    "MCU to ROS 2 link and framing (HW11)",
    "Digital control and anti-windup (C09)",
    "Hardware integration: drivers, timing, unit checks (S06)",
    "System identification (S08)"
  ],
  "labs": [
    "Build the firmware-in-the-loop base in ~/corebot-capstone and pass tests/acceptance/test_cap02.py, including the gate checks for step response, protocol and watchdog."
  ],
  "assessment_refs": [
    "CAP02-diagnostic-v1"
  ],
  "review_prompts": [
    "Explain what the firmware must do when the host sends no command for 120 ms, and show the log line that proves it.",
    "Justify the watchdog timeout, the PI gains and the frame format with numbers from your own artefacts."
  ],
  "extension_refs": [
    "https://docs.platformio.org/en/latest/platforms/native.html",
    "https://micro.vulcanexus.org/docs/"
  ]
}
---

## Why this matters

CoreBot Tidy can only drive where you tell it if its wheels do what the host asks, and tell the host honestly what they did. In CAP01 you built a robot that rests still in a seeded world. In this milestone you give it a **base controller** the way a real robot has one: a small piece of embedded C that closes the wheel-speed loop at 1 kHz, a framed and checksummed serial link to the host, a watchdog that stops the motors when the host goes silent, and an odometry layer on the host that turns encoder counts into a pose. Every later milestone (EKF in CAP03, navigation in CAP04, the safety supervisor in CAP07) stands on this layer. If its step response is sloppy, its protocol silently drops frames, or its watchdog never fires, the failures show up three milestones later as "the planner is flaky".

The approach is **firmware-in-the-loop** (FIL): the C sources are written as if for a microcontroller (fixed-width integers, no `malloc`, no floating-point surprises), but you compile them on your laptop into `libfw.so` and call them from the simulator at 1 kHz through `ctypes`. The same files build for an ESP32 with PlatformIO, so the optional hardware tier (see the extension challenge) is a re-flash, not a rewrite.

This is a project brief from a senior engineer to you: the lesson explains which earlier topics you are reusing, the Independent practice section is the actual brief, and the tests tell you when you are done.

## Intuition

![The CoreBot Tidy architecture: sensors and simulator, firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation, task layer and a safety supervisor that can stop every actuator path](/lesson-figures/CAP-architecture.svg)

*The whole system. This milestone is the orange band: it sits between the physics (MuJoCo plant) and everything the host does. Its two outputs are wheel counts with a status word, and a guarantee: no command for too long means zero PWM.*

Think of the firmware as a **very reliable, very boring employee** at the wheels. The host (a clever but sometimes late manager) sends "go 0.3 m/s". The employee converts that to wheel speeds, keeps each wheel at its speed using only local information (encoder counts, a clock), reports counts back, and has one rule written on the wall: *if the manager stops talking for 80 ms, stop the motors and wait*. The employee never trusts a message that fails its checksum and never lets a half-received message move a wheel.

![The CAP02 data path: commanded wheel speed enters a PI speed loop in C, PWM drives the simulated motor, the quadrature decoder produces 16-bit counts, a CRC-8 frame carries counts to the host driver, and a watchdog forces PWM to zero when commands stop](/lesson-figures/CAP02.svg)

This milestone reuses, and you should reread if rusty: [CAP01](/lessons/CAP01) (repo, `interfaces.py`, seeded env), [HW10](/lessons/HW10) (embedded speed control, PWM and encoder timing), [HW11](/lessons/HW11) (MCU to ROS 2 link, framing), [C09](/lessons/C09) (discrete PI, anti-windup), [S06](/lessons/S06) (counter unwrapping, freshness, command mapping), [CPP08](/lessons/CPP08) (testing C and C++ code) and [S08](/lessons/S08) (fitting a first-order motor model from step data).

## Theory and derivation

These are the **integration notes**: the few formulas and interfaces that matter here, each with the topic where it was derived.

### 1. Counts, speed and quantisation ([HW10](/lessons/HW10), [S06](/lessons/S06))

With $\text{PPR}$ pulses per motor revolution, $\times4$ decoding and gear ratio $g$, one wheel turn is $N=4\cdot\text{PPR}\cdot g$ counts. For the simulated N20 motor, $\text{PPR}=11$, $g=34$, so $N=1496$. A speed estimate from counts over a window $T$ has quantum
$$\Delta\omega=\frac{2\pi}{N\,T}.$$
At the 100 Hz control rate ($T=10$ ms) that is $0.42$ rad/s, **7 % of a 6 rad/s target**. This is why the PI loop uses a short filter or window, and why your logged speed (column `omega` in `step_left.csv`) is computed over 50 ms ($\Delta\omega=0.084$ rad/s, 1.4 %). Loop-rate aliasing against the encoder quantisation is one of the classic failure modes.

### 2. Discrete PI with anti-windup ([C09](/lessons/C09))

With error $e_k=\omega^*-\omega_k$ and sample time $T_s$:
$$u_k=\operatorname{sat}\bigl(K_p e_k + I_k\bigr),\qquad I_{k}=I_{k-1}+K_i e_k T_s\ \text{(only if not saturating, or if } e_k \text{ pulls } u \text{ back)}.$$
This is *conditional integration*. Without it, a blocked wheel makes $I$ grow without bound: in the worked example $K_i e t=1.5\cdot6\cdot1=9$ after one second, nine times full scale, and the wheel races to 20 rad/s on release.

### 3. Motor model from step data ([S08](/lessons/S08))

Fit $\omega(t)=K_u\,u\,(1-e^{-t/\tau})$ to an open-loop step. The simulated motor has $K_u=20$ rad/s per unit duty and $\tau=80$ ms; `sysid/motor_fit.py` must recover both within a few percent and write them to `configs/motor_params.json`. Rule of thumb for the first-order plant: 2 % settling of the open loop is $\approx 4\tau=0.32$ s; closed loop must beat that, which is what the settle < 0.35 s spec encodes.

### 4. Frame format and CRC ([HW11](/lessons/HW11), [S06](/lessons/S06))

Logical frame (12 bytes, little-endian): `type, seq, left(u16), right(u16), status, tick_ms(u16), vbat_dV, reserved, crc8`. Wire form: `0x7E` + frame with every `0x7E`/`0x7D` replaced by `0x7D, b ^ 0x20` + `0x7E`. CRC-8 uses polynomial $x^8+x^2+x+1$ (`0x07`), initial value 0, no reflection; the standard check value is `crc8(b"123456789") == 0xF4`. Link load, as in S06:
$$\text{load}=\frac{B_{\text{wire}}\cdot10\cdot f}{\text{baud}},\qquad \frac{26\cdot10\cdot100}{115200}=22.6\%\ \text{(worst case, every byte escaped)}.$$
Typical frames are 14 wire bytes: 12.2 %. A CRC-8 detects all single-bit errors in frames this short, and you do not have to take that on trust: the test flips every bit of the 12-byte frame (96 flips).

### 5. Watchdog ([S07](/lessons/S07), [HW10](/lessons/HW10))

Firmware keeps `last_cmd_ms`. Each tick: `expired = !armed || (uint32_t)(now - last) >= timeout`. When expired: PWM = 0 **and the PI integrator is reset**, otherwise recovery restarts from a stale integral. The unsigned subtraction survives the 32-bit millisecond counter wrapping. At boot `armed = 0`, so outputs stay zero until the first valid command. Timeout rule of thumb: about 3 host periods (here 30 ms) is the floor; the milestone's spec is "zero within 100 ms", so we use 80 ms. The distance covered while the timeout runs is a design number: $0.5\,\text{m/s}\times0.08\,\text{s}=4$ cm.

### 6. Differential-drive odometry and its two calibration constants ([CAP01](/lessons/CAP01), [S06](/lessons/S06))

$$\Delta s=\frac{r(\Delta\phi_R+\Delta\phi_L)}{2},\qquad \Delta\theta=\frac{r(\Delta\phi_R-\Delta\phi_L)}{b},\qquad x\mathrel{+}=\Delta s\cos\theta,\ y\mathrel{+}=\Delta s\sin\theta,$$
with wheel radius $r$ and track width $b$. Calibrate in this order: drive a measured straight line to get $r_{\text{true}}=r_{\text{est}}\cdot d_{\text{true}}/d_{\text{reported}}$; then spin in place a known true angle to get $b_{\text{true}}=b_{\text{est}}\cdot\theta_{\text{reported}}/\theta_{\text{true}}$. An error in $r$ scales distance; an error in $b$ scales heading, and heading errors dominate position error after a few metres.

## Worked example

All values below are **illustrative** (produced by a small stand-alone simulation of the plant and controller above, not from a run of your repository); your numbers will differ, and that is fine as long as the tests pass.

Plant: $K_u=20$ rad/s, $\tau=80$ ms, $N=1496$, PI at 100 Hz with $K_p=0.12$, $K_i=1.5$, counter starting at 65000 so that the 16-bit wrap occurs inside the log.

| t (s) | omega (rad/s, 50 ms window) | counts (uint16) |
|---|---|---|
| 0.001 | 0.00 | 65000 |
| 0.051 | 3.70 | 65044 |
| 0.101 | 5.80 | 65113 |
| 0.151 | 5.88 | 65183 |
| 0.201 | 5.96 | 65254 |
| 0.301 | 6.05 | 65397 |

`step_metrics(t, y, target=6.0)` gives settling 0.19 s, overshoot 0.8 %, steady-state error 0.01 %: all inside the limits (0.35 s, 10 %, 2 %). Counts per 10 ms at 6 rad/s: $6/(2\pi)\cdot1496/100=14.3$, so the integer counts in the CSV advance by 14 or 15 per row.

Windup test (wheel blocked for 1 s, then released): with conditional integration the peak after release is 6.79 rad/s, an overshoot of 13.2 % (limit 15 %); with the integrator always on, the integral is 9.0 at release and the wheel reaches 19.9 rad/s, an overshoot of 232 %.

Watchdog test: the host sends at 100 Hz until $t=500$ ms and is silent until 620 ms. The logged PWM is 0.31 up to 579 ms and 0 from 581 ms, so it reaches zero about 80 ms after the last command (limit 100 ms). The wheel coasts down to about 3.9 rad/s, commands resume at 620 ms, and the integrator restarts from 0: the speed climbs back to 6 rad/s with a peak of 6.07 rad/s (limit $1.2\times6=7.2$).

Protocol: the frame for sequence 7, counts 65530 and 4 is `7e 01 07 fa ff 04 00 00 d2 04 4c 00 d6 7e` (14 bytes, no byte needed escaping). Prepending 50 random garbage bytes does not stop it from being parsed, because the leading `0x7E` flushes whatever was collected.

Odometry (wheel radius true 0.0335 m, nominal 0.0330 m; track width true 0.163 m, nominal 0.160 m): a straight 10 m reads 9.85 m, a drift of 1.5 %, so $r=0.0330\cdot10/9.85=0.0335$. The 2 m square with nominal constants ends 3.1 cm and 1.3 degrees away from the truth; with calibrated constants $(0.03345, 0.1625)$ it ends 1.4 cm away.

A sample `runs/cap02/metrics.json` is shown in Expected output.

## Exercises

1. **(Easy)** An encoder has 11 pulses per revolution at the motor, $\times4$ decoding and a 34:1 gearbox. Counts per wheel turn, counts per 10 ms at 6 rad/s, and the speed quantum at 100 Hz. *(Numbers of the simulated N20 motor; formulas from the HW10 and S06 lessons.)*
2. **(Easy)** The frame is 14 bytes on the wire (26 worst case), sent at 100 Hz over a 115200-baud UART with 8N1. Link load, typical and worst case. Could you send it at 1 kHz? *(Formula: S06 and the Wikipedia article on serial communication framing.)*
3. **(Easy)** Compute by hand `crc8` of the two bytes `0x01 0x02` with polynomial `0x07`, init 0. Then say what the CRC of `b"123456789"` must be and why a known check value is useful.
4. **(Medium)** The host sends commands at 100 Hz. Choose a watchdog timeout and justify it with three arguments (host jitter, braking distance at 0.5 m/s, nuisance stops). How far does the robot travel after the last command?
5. **(Medium)** *Latency budget.* The spec says command-to-first-response dead time $\le20$ ms. Firmware runs its speed loop at 100 Hz, the link is 14 bytes at 115200 baud, and the first encoder count needs about 6.8 ms of motor motion. Add up the worst case and decide if the spec is reachable. Derive the 6.8 ms from $K_u=20$ rad/s, $\tau=80$ ms, first duty $K_p\cdot6=0.72$.
6. **(Medium)** *Find the bug.* The decoder keeps `int delta = cur - prev;` with `uint16_t` values and the log shows $-65\,526$ counts for a step from 65530 to 4. Explain the C integer promotion mistake and give the corrected line. Then give the delta for 65500 to 40.
7. **(Medium)** Explain in numbers why the PI integrator reaches 9.0 after a 1 s stall at target 6 rad/s ($K_i=1.5$), and why conditional integration keeps it near 0.3. What other anti-windup method exists and what trade-off does it bring?
8. **(Medium)** *Calibration.* After driving 10 m the odometry reports 9.85 m with $r_{\text{est}}=0.0330$ m. Give the new $r$. After spinning 10 true turns the (r-corrected) odometry reports a total of 3667.5 degrees with $b_{\text{est}}=0.160$ m. Give the new $b$. Which one affects a 2 m square more and why?
9. **(Hard)** *Design.* At the maximum wheel speed 20 rad/s, how many encoder edges per millisecond does one wheel produce? Can a 1 kHz tick sample the A/B lines directly to decode them? Propose what the real firmware does and how the simulator should mimic it.
10. **(Hard)** *Fixed-point.* The integrator update is $K_i e T_s$ with $K_i=1.5$, $T_s=0.01$. If $I$ is stored in Q15 (a value in $[-1,1)$ with $2^{-15}$ resolution), what error $e$ produces an increment smaller than one LSB, and what happens to the steady-state error if you truncate? Is floating point justified on an ESP32?
11. **(Hard, mini-project)** Build the FIL loop and the step-response artefacts, then inject link faults (1 % dropped frames, 1 flipped bit per 1000 frames, 5 ms extra latency) and report how settling time, overshoot and the watchdog test change. State assumptions, a baseline (no faults), a boundary case (watchdog timeout exactly equal to the command period) and what observation would reject your design.

## Reference implementation

The module below is `corebot/driver.py`, the host side of the link: frame codec, counter unwrap and freshness. It is a skeleton: every function has its contract in the docstring and raises `NotImplementedError`. Fill it in during Task 4 (the pieces are small; the discipline is in the tests). The C twin of the codec lives in `firmware/core/frame.c` and the two are cross-checked in Task 3.

```python
"""corebot/driver.py (skeleton): frames <-> SI units, counter unwrapping, freshness.

Contract (see interfaces.py): WheelState carries uint16 wrapped counts; this module turns them
into signed deltas and rad/s, and refuses to hand out stale data.
Units: SI. Time: seconds from one clock (the host monotonic clock). Counts: 4 * PPR * gear per wheel turn.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

SOF, ESC, FRAME_LEN = 0x7E, 0x7D, 12      # delimiter, escape byte, logical frame length incl. CRC
STATE_FMT = "<BBHHBHBB"                    # type, seq, left, right, status, tick_ms, vbat_dV, reserved


def crc8(data: bytes, poly: int = 0x07, init: int = 0x00) -> int:
    """CRC-8 (poly 0x07, no reflection). Check value: crc8(b"123456789") == 0xF4."""
    raise NotImplementedError


def pack_state(seq: int, left: int, right: int, status: int, tick_ms: int, vbat_dv: int) -> bytes:
    """Build the 12-byte logical frame: 11 body bytes (STATE_FMT, type 0x01) + CRC-8 of the body."""
    raise NotImplementedError


def stuff(frame: bytes) -> bytes:
    """Wire form: SOF + frame with every SOF/ESC byte replaced by ESC, byte ^ 0x20 + SOF."""
    raise NotImplementedError


class FrameParser:
    """Byte-at-a-time parser. feed() returns the list of valid 12-byte logical frames completed by
    these bytes. Bad CRC, wrong length or a dangling escape drop the frame and count it in
    `rejected`; the next SOF always resynchronises."""

    def __init__(self) -> None:
        self.rejected = 0

    def feed(self, data: bytes) -> list[bytes]:
        raise NotImplementedError


def unwrap_delta(prev: int, cur: int, bits: int = 16) -> int:
    """Signed difference of a free-running counter (modular arithmetic, see /lessons/S06)."""
    raise NotImplementedError


@dataclass(frozen=True)
class WheelSample:
    stamp: float          # s, host clock when the frame was received
    omega_left: float     # rad/s, positive = forward
    omega_right: float    # rad/s
    fresh: bool           # False when the newest frame is older than max_age


class Driver:
    """Owns the previous counts, the wheel geometry and the freshness rule."""

    def __init__(self, counts_per_rev: int, max_age: float = 0.03) -> None:
        self.counts_per_rev = counts_per_rev
        self.max_age = max_age

    def on_frame(self, stamp: float, frame: bytes) -> WheelSample:
        """Decode one valid frame; the first frame only primes the counters (omega = 0, fresh = False)."""
        raise NotImplementedError

    def poll(self, now: float) -> WheelSample:
        """Called every control tick; returns the last sample with fresh=False once older than max_age."""
        raise NotImplementedError
```

## Independent practice

### Goal

Add a firmware-in-the-loop drive base to `~/corebot-capstone`: portable C for the wheel speed loop, quadrature decoder, CRC-8 framed protocol and watchdog; a host driver and odometry; a system-identified motor model; and the artefacts under `runs/cap02/` that make `tests/acceptance/test_cap02.py` pass. This is milestone CAP02 of the capstone and it builds on your CAP01 repository.

### Setup

Work in `~/corebot-capstone` (created in CAP01). You need Python 3.10+, `gcc` and `cmake` (the tests skip with a clear message if they are missing, and a skip counts as **not passed** for the gate). Pinned versions to record in `pyproject.toml`: `numpy`, `pytest`, `pyserial` (optional). Commands:

```bash
cd ~/corebot-capstone
source .venv/bin/activate                    # created in CAP01
sudo apt install -y build-essential cmake    # gcc + CMake + ctest; `make doctor` checks these
mkdir -p runs/cap02 firmware/core firmware/tests
cmake -S firmware -B firmware/build && cmake --build firmware/build   # builds libfw.so and test_core
ctest --test-dir firmware/build --output-on-failure
python -m corebot.sysid.motor_fit --out configs/motor_params.json     # your script, Task 5
pytest -q tests/acceptance/test_cap02.py
```

Runtime: the whole step, windup and watchdog scenarios take seconds on a laptop (1 ms physics, 1 s to 3 s of simulated time each). Keep the evalkit file from CAP01 at `src/corebot/evalkit.py` (download `/practice/capstone/evalkit.py` if you have not).

### Tasks

1. **Quadrature decoder** (`firmware/core/quad_decode.c`): x4 decoding from 2-bit A/B samples with a transition table, `uint16_t` count that wraps. Unit tests: 12 forward cycles, reverse, wrap through 65535.
2. **PI speed loop** (`pi_speed.c`): float PI with conditional-integration anti-windup, output clamped to $[-1,1]$. Tune $K_p,K_i$ for the specs; record the values and your reasoning in `docs/tuning.md`.
3. **Frame codec and watchdog** (`frame.c`, `watchdog.c`): CRC-8, byte stuffing, a decoder that never overflows its buffer and resynchronises on every `0x7E`; a watchdog that starts expired and uses unsigned time subtraction. Cross-check in Python that `FwLib.crc8` equals `driver.crc8` on 1000 random inputs.
4. **Host side** (`src/corebot/driver.py`, `fw_sim.py`): finish the reference skeleton above; `fw_sim.py` runs the 1 kHz tick (plant, decoder, every tenth tick PI and a frame) with a `LinkModel` that can add latency, drops and bit flips from a seeded generator.
5. **System identification** (`sysid/motor_fit.py`): log an open-loop duty step, fit $K_u$ and $\tau$, write `configs/motor_params.json`, report the fit residual honestly (do not hide a bad fit by widening the tolerance).
6. **Artefacts** under `runs/cap02/`: `step_left.csv`, `step_right.csv` (columns `t,omega,counts`, target 6 rad/s, counter started near 65535), `windup.csv` (wheel blocked until $t=1$ s), `watchdog.csv` (columns `t_ms,cmd_rx,pwm,omega`), `latency.csv` (`cmd_id,dead_time_ms`), `loop_periods.csv` (`tick,period_ms`), `summary.json` (link figures), `odometry.json`.
7. **Odometry and calibration** (`estimation/odometry.py`, `estimation/calibration.py` is for CAP03; here a `calibrate_odometry.py` script): three seeded runs of a straight 10 m and a 2 m square before and after calibration; write the before/after numbers.
8. **Optional**: `firmware/platformio.ini` that compiles the same `core/` (see Library track). Not required to run.
9. Write `docs/cap02_notes.md`: timing and units of every interface, safe defaults, what you would change for a real ESP32, and one page of lessons learned (it feeds the CAP09 report).

### Starter code

C stubs that compile and fail clearly (`firmware/core/fw_api.h` is the contract; keep it as it is):

```c
/* fw_api.h : the public surface of the portable firmware core (no malloc, fixed-width ints). */
#ifndef FW_API_H
#define FW_API_H
#include <stddef.h>
#include <stdint.h>

#define FR_SOF 0x7E
#define FR_ESC 0x7D
#define FR_LEN 12               /* logical frame: 11 bytes + CRC8 */
#define FR_MAX_WIRE (2 + 2 * FR_LEN)

/* quadrature decoder (x4) ------------------------------------------------ */
typedef struct { uint8_t prev_ab; uint16_t count; } qd_t;
void     qd_init(qd_t *q, uint8_t ab);
void     qd_update(qd_t *q, uint8_t ab);       /* ab = (A << 1) | B, call at >= 4x the max edge rate */

/* PI speed loop with conditional-integration anti-windup ----------------- */
typedef struct { float kp, ki, integ; } pi_t;
void     pi_init(pi_t *p, float kp, float ki);
float    pi_step(pi_t *p, float target, float measured, float dt);   /* returns duty in [-1, 1] */

/* frame codec: SOF + stuffed(frame) + SOF, CRC-8 (poly 0x07) ------------ */
uint8_t  crc8(const uint8_t *data, size_t n);
size_t   fr_encode(const uint8_t *logical, size_t n, uint8_t *wire);    /* returns wire length */
typedef struct { uint8_t buf[FR_LEN + 1]; uint8_t n; uint8_t esc; uint8_t overflow; } fr_dec_t;
void     fr_dec_init(fr_dec_t *d);
int      fr_dec_push(fr_dec_t *d, uint8_t byte, uint8_t *logical);      /* 1 = valid frame in logical[FR_LEN], 0 = nothing yet */

/* command watchdog ------------------------------------------------------- */
typedef struct { uint32_t last_ms; uint32_t timeout_ms; uint8_t armed; } wd_t;
void     wd_init(wd_t *w, uint32_t timeout_ms);   /* starts EXPIRED: outputs stay zero until the first feed */
void     wd_feed(wd_t *w, uint32_t now_ms);
int      wd_expired(const wd_t *w, uint32_t now_ms);

#endif
```

```c
/* firmware/core starter: every function compiles and every test fails clearly until you fill it in.
   Rules: no malloc, fixed-width integers, no printf in the control path, outputs ZERO at boot. */
#include "fw_api.h"

void qd_init(qd_t *q, uint8_t ab) { (void)q; (void)ab; /* TODO: store the first AB state, count = 0 */ }
void qd_update(qd_t *q, uint8_t ab) { (void)q; (void)ab; /* TODO: 16-entry transition table, +1/-1/0 */ }

void pi_init(pi_t *p, float kp, float ki) { (void)p; (void)kp; (void)ki; /* TODO */ }
float pi_step(pi_t *p, float target, float measured, float dt) {
    (void)p; (void)target; (void)measured; (void)dt;
    return 0.0f; /* TODO: PI, clamp to [-1, 1], integrate only when not saturated (or when the error pulls back) */
}

uint8_t crc8(const uint8_t *data, size_t n) { (void)data; (void)n; return 0; /* TODO: poly 0x07, init 0 */ }
size_t fr_encode(const uint8_t *logical, size_t n, uint8_t *wire) {
    (void)logical; (void)n; (void)wire;
    return 0; /* TODO: SOF, stuffed payload, stuffed CRC, SOF */
}
void fr_dec_init(fr_dec_t *d) { (void)d; /* TODO */ }
int fr_dec_push(fr_dec_t *d, uint8_t byte, uint8_t *logical) {
    (void)d; (void)byte; (void)logical;
    return 0; /* TODO: on SOF validate length + CRC; unstuff ESC; never overflow buf */
}

void wd_init(wd_t *w, uint32_t timeout_ms) { (void)w; (void)timeout_ms; /* TODO: start EXPIRED */ }
void wd_feed(wd_t *w, uint32_t now_ms) { (void)w; (void)now_ms; /* TODO */ }
int wd_expired(const wd_t *w, uint32_t now_ms) { (void)w; (void)now_ms; return 0; /* TODO: unsigned subtraction */ }
```

The `ctypes` wrapper starter (declare `argtypes` and `restype` for every function you call; `ctypes` silently assumes `int`):

```python
"""corebot/fw_sim.py (starter): the C core inside the simulator loop via ctypes."""
from __future__ import annotations

import ctypes
import pathlib
from dataclasses import dataclass

LIB = pathlib.Path("firmware/build/libfw.so")


@dataclass
class LinkModel:
    """Serial link between firmware and host. Seeded: same seed, same faults."""
    latency_s: float = 0.0012      # 14 bytes at 115200 baud
    drop_prob: float = 0.0
    bitflip_prob: float = 0.0
    seed: int = 0


class FwLib:
    """Thin ctypes wrapper. Declare argtypes/restype for EVERY function you call: ctypes guesses int."""

    def __init__(self, path: pathlib.Path = LIB) -> None:
        self.lib = ctypes.CDLL(str(path))
        self.lib.crc8.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        self.lib.crc8.restype = ctypes.c_uint8
        # TODO: pi_init/pi_step (c_float), fr_encode, wd_* ...

    def crc8(self, data: bytes) -> int:
        return int(self.lib.crc8(data, len(data)))


class FirmwareInTheLoop:
    """1 kHz tick: plant -> encoder counts -> PI -> PWM -> plant; 100 Hz frames to the host."""

    def __init__(self, fw: FwLib, link: LinkModel) -> None:
        self.fw, self.link = fw, link

    def tick(self, t_ms: int) -> None:
        raise NotImplementedError("TODO: advance plant by 1 ms, run decoder, every 10th tick run pi_step and emit a frame")

    def receive_command(self, t_ms: int, v: float, w: float) -> None:
        raise NotImplementedError("TODO: feed the watchdog and set the wheel targets")
```

### Tests

`firmware/tests/test_core.c` (plain `assert`, run by `ctest`; it passes `-Wall -Wextra -Werror`, so unused parameters in your stubs need the `(void)` casts shown above):

```c
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../core/fw_api.h"

static void test_crc(void) { assert(crc8((const uint8_t *)"123456789", 9) == 0xF4); }
static void test_qd(void) {
    qd_t q; qd_init(&q, 0);
    const uint8_t fwd[] = {1, 3, 2, 0};          /* 00 -> 01 -> 11 -> 10 -> 00 : one full cycle = +4 */
    for (int r = 0; r < 3; r++) for (int i = 0; i < 4; i++) qd_update(&q, fwd[i]);
    assert(q.count == 12);
    const uint8_t rev[] = {2, 3, 1, 0};
    for (int i = 0; i < 4; i++) qd_update(&q, rev[i]);
    assert(q.count == 8);
    qd_init(&q, 0); q.count = 65534; for (int i = 0; i < 4; i++) qd_update(&q, fwd[i]);
    assert(q.count == 2);                        /* 16-bit wrap */
}
static void test_pi(void) {
    pi_t p; pi_init(&p, 0.12f, 1.5f);
    for (int i = 0; i < 1000; i++) assert(pi_step(&p, 100.0f, 0.0f, 0.01f) == 1.0f);
    assert(p.integ < 1.0f);                      /* no windup */
    pi_init(&p, 0.12f, 1.5f);
    float u = pi_step(&p, 1.0f, 0.0f, 0.01f);
    assert(u > 0.0f && u < 1.0f);
}
static void test_frame(void) {
    uint8_t payload[FR_LEN - 1]; for (int i = 0; i < FR_LEN - 1; i++) payload[i] = (uint8_t)(i * 23);
    payload[3] = FR_SOF; payload[4] = FR_ESC;   /* force stuffing */
    uint8_t wire[FR_MAX_WIRE]; size_t n = fr_encode(payload, FR_LEN - 1, wire);
    assert(n > FR_LEN + 2);
    fr_dec_t d; fr_dec_init(&d); uint8_t out[FR_LEN]; int got = 0;
    for (size_t i = 0; i < n; i++) got += fr_dec_push(&d, wire[i], out);
    assert(got == 1 && memcmp(out, payload, FR_LEN - 1) == 0);
    /* every single-bit flip of the 12-byte logical frame is rejected */
    uint8_t full[FR_LEN]; memcpy(full, payload, FR_LEN - 1); full[FR_LEN - 1] = crc8(payload, FR_LEN - 1);
    for (int i = 0; i < FR_LEN; i++) for (int b = 0; b < 8; b++) {
        uint8_t bad[FR_LEN]; memcpy(bad, full, FR_LEN); bad[i] ^= (uint8_t)(1u << b);
        assert(crc8(bad, FR_LEN - 1) != bad[FR_LEN - 1]);
    }
}
static void test_wd(void) {
    wd_t w; wd_init(&w, 100);
    assert(wd_expired(&w, 0));                   /* zero outputs at boot */
    wd_feed(&w, 1000); assert(!wd_expired(&w, 1099)); assert(wd_expired(&w, 1100));
    wd_feed(&w, 0xFFFFFFF0u); assert(!wd_expired(&w, 5));   /* wrap of the ms counter */
}
int main(void) { test_crc(); test_qd(); test_pi(); test_frame(); test_wd(); puts("firmware core: all tests passed"); return 0; }
```

`tests/acceptance/test_cap02.py` is below. Gate checks (the ones that must pass to graduate) are `test_step_response`, `test_single_bit_flips_rejected`, `test_resync_and_no_loss` and `test_watchdog`. **Thresholds are provisional starting values (see rationale in the comments); tighten them once your own reference run exists.** One-line rationales: settling < 0.35 s (about $4\tau$ of the open-loop motor, closed loop must beat it); overshoot < 10 % (0.6 rad/s of 6); steady-state error < 2 % (calibration-level accuracy); recovery overshoot < 15 % (the windup log of a bad loop is above 200 %); zero within 100 ms (the CAP07 safety spec of 300 ms needs margin for the rest of the stack); dead time $\le20$ ms (one 10 ms loop period plus link plus first count); jitter p99 $\le5$ ms (half a loop period); link load < 50 % (S06: no room for retries above that); odometry drift < 2 % and square error < 8 cm (CAP03 needs a starting point the EKF can correct).

```python
"""tests/acceptance/test_cap02.py : reads runs/cap02/ and tests the firmware core.
Gate checks are marked GATE. Thresholds are provisional starting values; tighten them once your own reference run exists."""
import csv, json, pathlib, random, shutil, statistics, subprocess
import pytest
from corebot.evalkit import step_metrics, all_single_bit_flips_detected
from corebot.driver import FrameParser, pack_state, stuff, FRAME_LEN

RUNS = pathlib.Path("runs/cap02")

def _csv(name):
    with open(RUNS / name) as f:
        return list(csv.DictReader(f))

def _series(name, col):
    rows = _csv(name)
    return [float(r["t"]) for r in rows], [float(r[col]) for r in rows]

def test_ctest_passes():                                     # GATE-adjacent; skip counts as not passed
    if not (shutil.which("gcc") and shutil.which("cmake")):
        pytest.skip("gcc/cmake missing: install them (make doctor); counts as NOT passed for the gate")
    subprocess.run(["cmake", "-S", "firmware", "-B", "firmware/build"], check=True)
    subprocess.run(["cmake", "--build", "firmware/build"], check=True)
    assert subprocess.run(["ctest", "--test-dir", "firmware/build"]).returncode == 0

@pytest.mark.parametrize("side", ["left", "right"])
def test_step_response(side):                                # GATE
    t, y = _series(f"step_{side}.csv", "omega")
    settle, over, sse = step_metrics(t, y, target=6.0, band=0.02)
    assert settle < 0.35     # a base that needs >0.35 s to reach speed feels sluggish to the tracker (CAP04)
    assert over < 0.10       # 10 % of 6 rad/s is 0.6 rad/s, about 2 cm/s at the wheel: tolerable
    assert sse < 0.02        # 2 % steady-state error: calibration-level accuracy
    counts = [int(r["counts"]) for r in _csv(f"step_{side}.csv")]
    assert any(b < a for a, b in zip(counts, counts[1:])), "16-bit wrap never exercised: start the counter near 65535"

def test_anti_windup():
    t, y = _series("windup.csv", "omega")
    after = [v for tt, v in zip(t, y) if tt > 1.0]            # wheel blocked until t = 1.0 s, then released
    assert (max(after) - 6.0) / 6.0 < 0.15                    # without anti-windup the same log shows >200 %

def test_single_bit_flips_rejected():                        # GATE
    frame = pack_state(7, 65530, 4, 0, 1234, 76)
    assert len(frame) == FRAME_LEN and all_single_bit_flips_detected(frame[:-1])
    for i in range(FRAME_LEN):
        for bit in range(8):
            bad = bytearray(frame); bad[i] ^= 1 << bit
            assert FrameParser().feed(bytes([0x7E]) + bytes(bad) + bytes([0x7E])) == []

def test_resync_and_no_loss():                               # GATE
    rng = random.Random(1000)
    garbage = bytes(rng.randrange(256) for _ in range(50))
    p = FrameParser()
    assert len(p.feed(garbage + stuff(pack_state(1, 1, 2, 0, 10, 76)))) == 1
    p, got = FrameParser(), 0
    for s in range(10_000):
        got += len(p.feed(stuff(pack_state(s, s * 37, s * 91, 0, s, 76))))
    assert got == 10_000
    link = RUNS / "summary.json"
    s = json.loads(link.read_text())["link"]
    assert s["frame_bytes_worst"] * 10 * s["rate_hz"] / s["baud"] < 0.5

def test_watchdog():                                         # GATE
    rows = _csv("watchdog.csv")
    t = [float(r["t_ms"]) for r in rows]; rx = [int(r["cmd_rx"]) for r in rows]
    pwm = [float(r["pwm"]) for r in rows]; w = [float(r["omega"]) for r in rows]
    last = max(tt for tt, r in zip(t, rx) if r and tt < 560)  # last command before the silence
    first_zero = min(tt for tt, p in zip(t, pwm) if tt > last and p == 0.0)
    assert first_zero - last <= 100
    resume = min(tt for tt, r in zip(t, rx) if r and tt > last + 50)
    assert max(v for tt, v in zip(t, w) if tt > resume) <= 1.2 * 6.0

def test_latency_and_jitter():
    dead = [float(r["dead_time_ms"]) for r in _csv("latency.csv")]
    assert max(dead) <= 20.0                                  # one 100 Hz period of wait + link + first count
    dev = sorted(abs(float(r["period_ms"]) - 10.0) for r in _csv("loop_periods.csv"))
    assert dev[int(0.99 * len(dev))] <= 5.0                   # p99 jitter

def test_odometry_calibration():
    o = json.loads((RUNS / "odometry.json").read_text())
    assert o["after"]["straight_drift_pct"] < 2.0
    assert o["after"]["square_err_m"] < 0.08
    assert o["after"]["square_err_m"] < o["before"]["square_err_m"]
    assert len(o["seeds"]) == 3
```

### Expected output

With all artefacts present and the firmware built, `pytest -q tests/acceptance/test_cap02.py` prints (illustrative timing):

```text
.........                                                                [100%]
9 passed in 3.4s
```

and your `runs/cap02/metrics.json` (written by your own script) should look like this (illustrative values):

```json
{
  "milestone": "CAP02",
  "step": {"left": {"settle_s": 0.19, "overshoot": 0.008, "sse": 0.0001},
           "right": {"settle_s": 0.19, "overshoot": 0.008, "sse": 0.0001}},
  "windup_overshoot": 0.132,
  "protocol": {"bit_flips_rejected": "96/96", "frames_lost_of_10000": 0, "link_load_worst": 0.226},
  "watchdog": {"zero_after_ms": 80, "peak_after_resume_rad_s": 6.07},
  "latency_ms": {"max": 18.4, "jitter_p99": 1.7},
  "odometry": {"before": {"straight_drift_pct": 1.49, "square_err_m": 0.031},
               "after": {"straight_drift_pct": 0.20, "square_err_m": 0.014}}
}
```

If gcc or cmake is missing you will see `s` for the ctest test instead of a dot: install them, a skip is not a pass.

### Extension challenge

**Stretch:** replace float with Q15 arithmetic in the PI loop and show with a test that the step metrics stay inside the limits and that the integrator does not stall at small errors (Exercise 10). Add sequence-number accounting so the driver reports lost frames.

**Optional hardware tier (OPTIONAL, no grade depends on it):** ESP32 + two N20 or JGA25-370 encoder gearmotors + a TB6612FNG or DRV8833 driver + a 2S Li-ion pack with an inline fuse (parts list in HW05 and HW03 terms). Build the same `core/` with `pio run -e esp32`, replay the step test over serial with pySerial (script in the Library track), and compare real and simulated step metrics; expect differences from friction, battery sag and the real encoder PPR. Safety first: fuse, bench-supply current limit, **wheels off the ground for the first runs**, stay at or below 12 V, and follow the electrical rules of [HW03](/lessons/HW03). Hardware alone never substitutes for a failing gate.

### Library track

Compile the same core with PlatformIO's `native` platform (host, Unity tests) and an `esp32` environment. Then connect the base to ROS 2 with micro-ROS or `ros2_control` instead of your own link (study how their hardware interface wraps `read()`/`write()`; the reason you wrote your own first is to understand what they hide).

```ini
; firmware/platformio.ini : the SAME core/ for the host (native) and an optional ESP32
[platformio]
src_dir = core

[env:native]
platform = native
build_flags = -Wall -Wextra -DFW_HOST=1
test_framework = unity

[env:esp32]
platform = espressif32
board = esp32dev
framework = arduino
build_flags = -Wall -Wextra
```

A loopback check of the framing over a real or virtual serial port with pySerial (Linux, `socat` creates the pair):

```python
# Needs: pip install pyserial ; socat for the virtual pair (Linux): socat -d -d pty,raw,echo=0 pty,raw,echo=0
# Replays the CAP02 state frames over a (virtual or real) serial port and checks the parser end to end.
import sys

import serial  # pyserial

from corebot.driver import FrameParser, pack_state, stuff

tx = serial.Serial(sys.argv[1], 115200, timeout=0.1)   # e.g. /dev/pts/3
rx = serial.Serial(sys.argv[2], 115200, timeout=0.1)   # e.g. /dev/pts/4 (or the ESP32: /dev/ttyUSB0)
parser, seen = FrameParser(), 0
for seq in range(200):
    tx.write(stuff(pack_state(seq, seq * 14, seq * 14, 0, seq * 10, 76)))
    seen += len(parser.feed(rx.read(64)))
print("frames seen:", seen, "rejected:", parser.rejected)
assert seen >= 195, "link lost frames: check cabling, baud rate and the stuffing of 0x7E/0x7D"
```

## Verification

Check numbers by hand before trusting plots: counts per turn (1496), the quantum (0.42 rad/s at 100 Hz), the CRC check value (`0xF4`), the link load (12.2 % typical). Verify the firmware as firmware: `ctest` must pass on a clean build with `-Wall -Wextra -Werror`; every test must fail first when you break the code (flip a sign in the transition table and see the decoder test fail). Verify the claim "safe at boot" by reading the logs: PWM is 0 until the first command. Verify the claim "survives garbage" with the exhaustive and the random tests in `test_cap02.py`.

**Scoring and graduation.** CAP02 is worth **12 of 100** points. The score is 60 % automated (weighted fraction of checks, gates marked above) and 40 % human rubric (0 to 4 each): C code quality (no dynamic allocation in the control path, fixed-width integers, any float justified), safety defaults (outputs zero at boot and on stale commands), documentation of timing and units, honest system identification. Graduation requires every gate check of every milestone to pass, every milestone at 60 or above and a weighted total of at least 70. A failing gate keeps CAP02 "in progress" in the app but does not lock later topics. A self-review prompt you can give to an LLM together with `firmware/core/*` and `runs/cap02/metrics.json` (not your own verdict): *"Review this embedded C for a wheel speed controller. List any dynamic allocation, integer promotion or wrap bugs, missing zero-at-boot behaviour and any place a stale command could move a motor. Score 0 to 4 against: code quality, safety defaults, documentation of timing and units, honest sysid, and cite lines."*

## Failure modes

- One wheel's encoder sign inverted: the robot spins instead of driving straight; the step test passes per wheel, the 10 m straight does not.
- `uint16_t` arithmetic done in `int`: the wrap produces a $\pm65\,5xx$ count spike and a huge speed (Exercise 6).
- Integrator windup after a stall or a saturating command (Exercise 7).
- ISR (or the 1 kHz tick) doing too much: printing, floating-point formatting or blocking in the control path.
- `float` on the MCU and `double` on the host: tiny numeric differences that break bit-exact comparisons; compare with tolerances.
- Byte-stuffing off by one: the frame with a `0x7E` inside is the one that fails, once in 256 frames, so random tests must be long enough to hit it.
- Parser buffer overflow on garbage, or a parser that never resynchronises after a lost delimiter.
- Loop rate aliasing the encoder quantisation: a 1 kHz speed estimate from counts is almost always 0 or one count (Exercise 1).
- Forgetting PWM = 0 at boot and when the data is stale; forgetting to reset the integrator when the watchdog fires.
- Calibrating track width before wheel radius, so the heading calibration absorbs the radius error.

## Alternatives and trade-offs

You could skip the C and write the speed loop in Python: it is faster to write, but it hides exactly the problems this milestone teaches (integer widths, wrap, timing, buffer limits) and cannot be flashed. You could use COBS framing (constant overhead of one byte per 254, predictable length) instead of HDLC-style stuffing (variable length, simpler); you could use a 16-bit CRC for longer frames. Odometry can be refined with the gyro in CAP03; here wheel-only odometry is the baseline you must beat. micro-ROS gives you a ROS 2 node on the MCU at the price of a heavier toolchain; `ros2_control` gives a standard hardware interface on the host. Gazebo or a real robot would give you friction and slip you do not have in MuJoCo with ideal wheels; the hardware tier exists to show that gap.

## Transfer and retention

**This milestone prepares for:** CAP03 (the odometry you calibrate is the prediction input of the EKF), CAP04 (the tracker commands `v`, `w` through this link), CAP07 (the safety supervisor sends its direct stop frame to this watchdog), CAP08 (the twin changes your wheel radius and track width; your calibration script is reused for the sim-to-real gap).

Recall prompts for next week, without notes:

1. Write the wrap-safe counter delta in C with the exact integer types.
2. State the three reasons a frame can be rejected, and what the parser does after each.
3. Why must the integrator reset when the watchdog fires?
4. Derive the velocity quantum for a given loop rate and explain why a longer window helps.
5. What is the calibration order for wheel radius and track width, and why?

## Exercise answers

1. $N=4\cdot11\cdot34=1496$ counts per wheel turn. At 6 rad/s: $6/(2\pi)=0.955$ turns/s, i.e. 1428 counts/s, so 14.3 counts per 10 ms. Quantum $2\pi/(1496\cdot0.01)=0.42$ rad/s, 7 % of 6 rad/s.
2. Typical: $14\cdot10\cdot100/115200=12.2\%$. Worst case (26 bytes): $22.6\%$. At 1 kHz: $121\%$ typical, impossible; speed-loop data should be summarised at 100 Hz.
3. Start with $c=0$. Byte `0x01`: $c=0x01$; seven shifts give 0x80, the eighth shift has the top bit set, so $c=(0x80\ll1)\&0xFF\oplus0x07=0x07$. Byte `0x02`: $c=0x07\oplus0x02=0x05$; the eight shifts give 0x0A, 0x14, 0x28, 0x50, 0xA0, then (top bit set) 0x40 xor 0x07 = 0x47, then 0x8E, then (top bit set) 0x1C xor 0x07 = 0x1B. The CRC is `0x1B`; confirm it with your own `crc8`. The check value of `b"123456789"` is `0xF4`; a published value tells you whether polynomial, init and reflection conventions match the other side.
4. Around 80 ms. Host jitter: the timeout must be several periods (30 ms is 3 periods) so one late command does not stop the robot (nuisance stops are tested in CAP07: at most 5 % of nominal episodes). Braking: at 0.5 m/s the robot travels $0.5\cdot0.08=4$ cm before the PWM is cut, plus coasting. The spec bound (zero within 100 ms) leaves 20 ms of slack for the 1 ms tick and the link. After the last command: 4 cm.
5. Worst case: wait for the next firmware 10 ms tick (10 ms) + link $14\cdot10/115200=1.2$ ms + first count 6.8 ms = 18.0 ms, under 20 ms with 2 ms of margin; any added buffering (USB-serial latency timers of 16 ms) breaks it. First count: duty $0.12\cdot6=0.72$; acceleration $K_u u/\tau=20\cdot0.72/0.08=180$ rad/s$^2$; one count is $2\pi/1496=4.2\times10^{-3}$ rad; $t=\sqrt{2\cdot4.2\times10^{-3}/180}=6.8$ ms.
6. `uint16_t` operands are promoted to `int` (32-bit) before the subtraction, so $4-65530=-65526$ is exact and no wrap happens. Fix: `int16_t delta = (int16_t)(uint16_t)(cur - prev);` or `(uint16_t)(cur - prev)` followed by the half-range test. 65500 to 40: $(40-65500)\bmod65536=76$, so $+76$.
7. Error 6 rad/s times $K_i=1.5$ times 1 s $=9.0$, nine times the full duty range, so after release the output stays saturated until the integrator has been unwound by negative error: a long overshoot. Conditional integration stops adding when the output saturates, so $I$ stays near $1-K_p\cdot6\approx0.3$. Alternative: back-calculation, which feeds the difference between the saturated and the raw output into the integrator with gain $1/T_t$; it needs a tuned tracking gain (in a scratch simulation with these gains, back-calculation gains between 5 and 40 left 24 to 121 % overshoot).
8. $r=0.0330\cdot10/9.85=0.03350$ m. $b=0.160\cdot3667.5/3600=0.16300$ m. Track width matters more for the square: its four 90 degree turns accumulate heading error (1.9 percent of 360 degrees is about 7 degrees if uncorrected), and a heading error rotates every later segment; the radius error only scales each side by 1.5 %.
9. $20/(2\pi)\cdot1496=4762$ counts/s, 4.8 edges per ms per wheel. A 1 kHz tick can see at most one sample per ms, so it would miss edges; the real firmware uses edge interrupts or a hardware pulse counter (the ESP32 has one) and the 1 kHz tick only reads the accumulated count. The simulator should accumulate counts at the 1 ms plant step (as in the sample sim) and only feed raw A/B sequences to the decoder in the unit tests.
10. Increment $=K_ieT_s=0.015e$. One LSB is $3.05\times10^{-5}$, so $e<0.002$ rad/s gives less than one LSB and truncation rounds it to 0: the integrator stalls and the loop keeps a small steady-state error (about 0.002 rad/s, 0.03 % of 6 rad/s: harmless here, but visible as hunting); rounding to nearest or a wider accumulator (Q31) avoids it. The ESP32 has a single-precision FPU, so `float` in a 100 Hz loop is justified; it would not be on a Cortex-M0.
11. Expected: with 1 % drops the 50 ms window shows small dips and the settling time grows by one or two periods; a flipped bit is rejected (CRC) and behaves as a drop; +5 ms latency lowers the margin of the dead-time check (18.0 + 5 = 23 ms fails). The boundary case: with the timeout equal to the command period, every late command stops the robot. A rejecting observation: a frame accepted with a wrong counter value, or PWM nonzero 100 ms after the last command.

## Further reading

- [PlatformIO native platform](https://docs.platformio.org/en/latest/platforms/native.html) - compile and unit-test the firmware core on the host.
- [Python ctypes](https://docs.python.org/3/library/ctypes.html) - calling a shared library, argtypes and restype.
- [CTest manual](https://cmake.org/cmake/help/latest/manual/ctest.1.html) - registering and running C tests.
- [Cyclic redundancy check (Wikipedia)](https://en.wikipedia.org/wiki/Cyclic_redundancy_check) - polynomials, check values and error detection.
- [Vulcanexus micro-ROS documentation](https://micro.vulcanexus.org/docs/) - the Library track for the MCU to ROS 2 link.
- [ros2_control (Jazzy)](https://control.ros.org/jazzy/index.html) - hardware interface contract on the host.
- [pySerial documentation](https://pyserial.readthedocs.io/en/latest/) - ports, timeouts and miniterm.
- Videos: Articulated Robotics, *The Ultimate Guide to using Motors in Robotics*; Texas Instruments, *Interfacing with Quadrature Encoders*; Articulated Robotics, *Could this button control your robot? (Beginner micro-ROS Tutorial)*.
