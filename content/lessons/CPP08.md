---
{
  "id": "cpp08-foundations",
  "module_id": "CPP08",
  "title": "Debugging and testing: sanitizers, debuggers, and test harnesses",
  "summary": "Find memory and logic errors with sanitizers and a debugger, reduce a failure to a minimal case, and lock the fix in with a regression test.",
  "estimated_minutes": 405,
  "prerequisites": [
    "CPP07",
    "CPP02"
  ],
  "source_refs": [
    {
      "title": "AddressSanitizer (Google Sanitizers wiki)",
      "url": "https://github.com/google/sanitizers/wiki/AddressSanitizer"
    },
    {
      "title": "GCC: Program Instrumentation Options",
      "url": "https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html"
    },
    {
      "title": "GDB documentation",
      "url": "https://sourceware.org/gdb/documentation/"
    },
    {
      "title": "AddressSanitizerAlgorithm (Google Sanitizers wiki)",
      "url": "https://github.com/google/sanitizers/wiki/AddressSanitizerAlgorithm"
    },
    {
      "title": "GDB manual: Setting Watchpoints",
      "url": "https://sourceware.org/gdb/current/onlinedocs/gdb.html/Set-Watchpoints.html"
    },
    {
      "title": "Clang: UndefinedBehaviorSanitizer",
      "url": "https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html"
    },
    {
      "title": "git-bisect documentation",
      "url": "https://git-scm.com/docs/git-bisect"
    }
  ],
  "objectives": [
    "Choose the right tool (AddressSanitizer, UBSan, ThreadSanitizer, Valgrind, GDB) for a class of bug.",
    "Read a sanitizer report and locate the faulty line, access size and allocation site.",
    "Reduce a failing program to a minimal reproducer.",
    "Write a regression test with a small harness that fails before the fix and passes after."
  ],
  "core_theory": [
    "sanitizers",
    "debuggers",
    "test harnesses"
  ],
  "labs": [
    "Reproduce a heap buffer overflow in a moving average with AddressSanitizer, inspect a crash in GDB, reduce the input, fix the bug, and implement a small test harness that holds the regression test."
  ],
  "assessment_refs": [
    "CPP08-diagnostic-v1"
  ],
  "review_prompts": [
    "A test fails once in about fifty runs on CI but never locally. Describe how you would make it reproducible and which tools you would apply, in order."
  ],
  "extension_refs": [
    "https://github.com/google/sanitizers/wiki/AddressSanitizer",
    "https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html"
  ]
}
---

## Why this matters

C++ does not stop you from reading past the end of an array, using an object after it was moved or freed, or adding two numbers that overflow. These mistakes are *undefined behavior*: the program may crash, print a slightly wrong number, or appear to work for months, then fail on a different compiler or a different day. On a robot, the symptom is often far from the cause: a velocity estimate that is off by a few percent, or a node that dies once per hour. The tools in this lesson turn silent corruption into an immediate, located error message, and the discipline of reducing the failure and adding a regression test makes sure the same bug never returns. In practice, most professional C++ teams run their unit tests under AddressSanitizer and UBSan on every commit.

## Intuition

Debugging is the scientific method applied to a program: observe a failure, form a hypothesis, design an experiment that could disprove it, repeat. The tools differ in what they let you observe:

- A **sanitizer** instruments the program at compile time and checks every memory access or arithmetic operation while it runs. It finds a bug *when the bad operation executes*, even if the program would otherwise appear to work.
- A **debugger** (GDB) stops a running program at a chosen point and lets you inspect variables and the call stack, step by step. It shows the state at the moment of the crash.
- A **test harness** automates the experiment: given an input and an expected result, it says pass or fail, every time, in seconds.

Reduction is the step that people skip. A failure on 10,000 lines and a 1 GB log is hard to reason about; the same failure on a 6-line program and three numbers is usually obvious.

Think of a debugging session as a police investigation with three kinds of evidence. A sanitizer is a security camera installed in advance: it records only the specific crimes it was designed to watch (an out-of-bounds access, a use after free), but it records them at the exact moment they happen, with the address and the call stack. A debugger is a detective who walks through the scene after the event: it can show the state of everything, but only at the points where you told it to stop. A test is a standing order: "when this input arrives, this output must leave", checked automatically forever.

Everyday robot example: a velocity filter occasionally outputs a spike once an hour. The ring buffer is a plain array, the spike is the value that sat one slot past the end, and the robot "works" for months because the neighbouring memory is usually zero. No amount of staring at the spike plots finds that; an AddressSanitizer build of the same code names the line the first time the index goes out of range, and a regression test with a hand-computed window keeps it from returning.

**Predict before you compute.** The moving average of `{1,2,3,4,5}` with window 2 prints `3 4.5 6 4.5` instead of `1.5 2.5 3.5 4.5`. Before reading the sanitizer report, guess how many elements were summed per window. The first output 3 is $(1+2+3)/2$, so three elements were added and the divisor was still 2; only one number of the loop bound changed. Notice that you can reach this hypothesis from the output alone, and that the sanitizer's job is to confirm it, not to replace the thinking.

**The common wrong intuition** is that a program that did not crash is correct, and that "it works with a debugger or in Release" is evidence about the bug. Undefined behaviour has no obligation to crash: an out-of-range read returns whatever is there, and the last window of the example even prints the right number by accident. Likewise, a bug that disappears when you add a `printf` or switch on optimisation is not gone; it has moved. The cure is to make the failure deterministic and small first (reduce the input, fix the seeds), then use a tool that observes the bad operation directly.

![The six-step debugging loop from a failing run to a regression test, and the four tools with the bugs each one finds](/lesson-figures/CPP08.svg)

*Figure: reproduce, reduce, locate with the tool that matches the question, fix, then lock the fix in with a regression test and re-run under the sanitizers. Step 3 is the only place where the tool choice matters.*

## Theory and derivation

### Which tool finds which bug

| Tool and flag | Finds | Typical cost |
|---|---|---|
| AddressSanitizer `-fsanitize=address` | heap/stack/global buffer overflow, use-after-free, use-after-scope, double free, leaks (LeakSanitizer, on Linux) | about 2x slower, 2-3x memory |
| UndefinedBehaviorSanitizer `-fsanitize=undefined` | signed integer overflow, bad shifts, null/misaligned pointer use, out-of-range conversions | small |
| ThreadSanitizer `-fsanitize=thread` | data races (CPP10) | 5-15x slower; cannot be combined with ASan |
| MemorySanitizer (clang) / Valgrind | reads of uninitialized memory; Valgrind needs no recompilation | Valgrind about 20-50x slower |
| GDB `-g` build | crash location, call stack, variable values, watch a value change | none until used |
| Compiler warnings `-Wall -Wextra -Wconversion` | many mistakes before running | free |

Compile with `-g` (debug info) and `-fno-omit-frame-pointer` (clean stack traces), at `-O0` or `-O1`. Optimization can make a variable "optimized out" in the debugger.

**Example.** Three one-file programs of a robot controller, each with one silent bug, run under the tool that the table assigns to it (g++ 11.4, Valgrind 3.18): `ovf.cpp` adds `2000000000` twice to an `int` encoder counter, `uaf.cpp` deletes a gain and then prints `*gain`, and `uninit.cpp` tests an uninitialised `double offset` with `if (offset > 0.1)`. Which tool (AddressSanitizer, UndefinedBehaviorSanitizer or Valgrind) reports each bug?

**Solution.** The encoder counter wraps without any ASan report, because no memory is touched wrongly; UBSan names the line. The use-after-free is the reverse: UBSan sees nothing wrong with an integer or a pointer read, while ASan reports the freed address (and the printed value `1.17263e-313` shows the stale memory was already reused; this garbage value varies from run to run). The uninitialised `double` is found by Valgrind, not by either sanitizer. Matching the symptom to the tool is a table lookup, not a guess. The sessions are:

```
$ g++ -std=c++20 -g -fsanitize=address ovf.cpp -o ovf_a && ./ovf_a    # ticks += 2000000000 twice on an int
-294967296
$ g++ -std=c++20 -g -fsanitize=undefined ovf.cpp -o ovf_u && ./ovf_u
ovf.cpp:5:9: runtime error: signed integer overflow: 2000000000 + 2000000000 cannot be represented in type 'int'
-294967296
$ g++ -std=c++20 -g -fsanitize=address uaf.cpp -o uaf_a && ./uaf_a    # delete gain; then print *gain
==316859==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010 ...
$ g++ -std=c++20 -g -fsanitize=undefined uaf.cpp -o uaf_u && ./uaf_u
1.17263e-313
$ g++ -std=c++20 -g -O0 uninit.cpp -o uninit && valgrind -q ./uninit  # double offset; if (offset > 0.1)
==316884== Conditional jump or move depends on uninitialised value(s)
==316884==    at 0x1091A2: main (uninit.cpp:4)
```

### Reading an AddressSanitizer report

The first lines carry the whole diagnosis:

```
ERROR: AddressSanitizer: heap-buffer-overflow on address 0x504000000038 ...
READ of size 8 at 0x504000000038 thread T0
    #0 ... in moving_average(...) buggy.cpp:10
    #1 ... in main buggy.cpp:18
0x504000000038 is located 0 bytes to the right of 40-byte region [0x504000000010,0x504000000038)
allocated by thread T0 here: ...
```

- *bug class*: heap-buffer-overflow (also stack-buffer-overflow, heap-use-after-free, ...);
- *what*: a READ of size 8 (a `double`);
- *where*: frame #0, `buggy.cpp` line 10; the caller is frame #1;
- *which object*: the address is 0 bytes right of a 40-byte region, i.e. five doubles, so index 5 of a 5-element vector was read, one past the end.

Always read the *first* error; later ones can be consequences.

**Example.** A lidar driver clips 90 range readings (`std::vector<float> ranges(90, 12.0f)`) with a loop `for (i = 0; i <= ranges.size(); ++i)`. Read the first lines of the real AddressSanitizer report (addresses shortened) and give the class of the error, what was accessed, where, which object, and the fix.

**Solution.** Class: heap-buffer-overflow. What: a READ of size 4, one `float`. Where: `clip`, line 4, called from `main` line 8. Which object: 0 bytes to the right of a 360-byte region, that is $360/4=90$ floats, so index 90 was read, the first one past the end. The loop bound `<=` should be `<`. The report is:

```
==...==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5130000001a8 ...
READ of size 4 at 0x5130000001a8 thread T0
    #0 0x... in clip(std::vector<float, std::allocator<float> >&, float) lidar.cpp:4
    #1 0x... in main lidar.cpp:8
0x5130000001a8 is located 0 bytes to the right of 360-byte region [0x513000000040,0x5130000001a8)
```

### Debugger essentials

`gdb ./prog`, then `run`, `bt` (backtrace), `frame N`, `info locals`, `print expr`, `break file:line`, `watch var`, `continue`, `next`, `step`. Batch mode: `gdb -batch -ex run -ex bt ./prog`. For a crash inside a library, `bt` still shows your calling frame. A moved-from `std::unique_ptr` prints as `get() = 0x0` in GDB, which immediately explains a segmentation fault at that dereference.

**Example.** A lookup returns `nullptr` for an unknown sensor id and the caller dereferences it (`sensors = {{1, 100.0}, {2, 50.0}}`, `find(sensors, 3)`). Using batch GDB on the `-g -O0` build with `run`, `bt` and `info locals`, which line crashes, what is the value of `s`, and where does the fix belong?

```cpp
struct Sensor { int id; double rate_hz; };
const Sensor* find(const std::vector<Sensor>& v, int id) {
  for (const Sensor& s : v) if (s.id == id) return &s;
  return nullptr;
}
// main: sensors = {{1, 100.0}, {2, 50.0}};  const Sensor* s = find(sensors, 3);  std::cout << s->rate_hz;
```

**Solution.** `bt` gives the crash line (`nul.cpp:11`), `info locals` shows `s = 0x0`: `find(sensors, 3)` found no sensor 3, because only ids 1 and 2 exist. The fix belongs at the call site (check the pointer, or return `std::optional`), not at the dereference. The batch session prints:

```
$ g++ -std=c++20 -g -O0 nul.cpp -o nul && gdb -batch -ex run -ex bt -ex 'info locals' ./nul
Program received signal SIGSEGV, Segmentation fault.
0x0000555555555422 in main () at nul.cpp:11
11	  std::cout << s->rate_hz << "\n";
#0  0x0000555555555422 in main () at nul.cpp:11
sensors = std::vector of length 2, capacity 2 = {{id = 1, rate_hz = 100}, {id = 2, rate_hz = 50}}
s = 0x0
```

### Test harnesses and regression tests

A test is an executable claim: *given input X, the result is Y*. A harness gives it structure: named tests, independent state, failure messages that show expected and actual values, a summary and a non-zero exit code on failure so that CI notices. Good tests

- use hand-computed expected values (not the function under test, which would only prove it equals itself);
- cover boundaries (empty, one element, window equals length, zero), typical cases and error cases;
- check invariants and properties (window 1 is the identity; the result length is $n-w+1$);
- are deterministic (fixed seeds, fixed clocks) and independent of each other.

A **regression test** captures a bug that was found: it fails on the broken code and passes on the fixed code. Writing it *before* fixing proves that it detects the bug.

For floating-point comparisons use a tolerance: `|a - b| <= tol` is false when either value is NaN, which is the safe way round; `!(|a-b| > tol)` would accept NaN.

**Example.** A motor-command limiter `saturate(v, lo, hi)` returns `lo` instead of `hi` above the upper limit. Four hand-computed expectations are written in a 10-line macro harness, which prints expected and actual values and returns a non-zero exit code. Which expectation fails, what is the exit code, and what does the run after the one-line fix print?

```cpp
#include <cmath>
#include <cstdlib>
#include <iostream>
// saturate v into [lo, hi]  (BUG: the upper branch returns lo)
double saturate(double v, double lo, double hi) {
  if (v < lo) return lo;
  if (v > hi) return lo;
  return v;
}
static int failures = 0;
#define EXPECT_NEAR(got, want, tol)                                                    \
  do { const double g = (got), w = (want);                                             \
       if (!(std::fabs(g - w) <= (tol))) { ++failures;                                 \
         std::cerr << "FAIL line " << __LINE__ << ": " #got " = " << g                 \
                   << ", expected " << w << "\n"; } } while (0)
int main() {
  EXPECT_NEAR(saturate(0.4, -1.0, 1.0), 0.4, 1e-12);    // inside
  EXPECT_NEAR(saturate(-3.0, -1.0, 1.0), -1.0, 1e-12);  // below
  EXPECT_NEAR(saturate(2.5, -1.0, 1.0), 1.0, 1e-12);    // above
  EXPECT_NEAR(saturate(1.0, -1.0, 1.0), 1.0, 1e-12);    // exactly on the limit
  std::cout << (failures ? "FAILED" : "all passed") << "\n";
  return failures ? EXIT_FAILURE : EXIT_SUCCESS;
}
```

**Solution.** The expectations are inside (0.4 stays 0.4), below ($-3.0\to-1.0$), above ($2.5\to1.0$) and exactly on the limit ($1.0\to1.0$). With the bug only the third one fails: `saturate(2.5, -1.0, 1.0)` returns `lo = -1` instead of `1`, the harness counts one failure, prints `FAILED` and exits with 1. The failing run names the case (`2.5` should saturate to `1.0`), and after changing `return lo` to `return hi` in the upper branch all four pass and the exit code is 0. The test would fail without any sanitizer and in a Release build, because it asserts on values. The session is:

```
$ g++ -std=c++20 -Wall -Wextra sat.cpp -o sat && ./sat; echo "exit $?"
FAIL line 19: saturate(2.5, -1.0, 1.0) = -1, expected 1
FAILED
exit 1
$ sed 's/if (v > hi) return lo;/if (v > hi) return hi;/' sat.cpp > sat2.cpp     # the fix
$ g++ -std=c++20 -Wall -Wextra sat2.cpp -o sat2 && ./sat2; echo "exit $?"
all passed
exit 0
```

### Reduction and bisection

If a failure needs $N$ items and a single culprit, halving the input finds it in $\lceil\log_2 N\rceil$ runs. When the failure needs several items, delta debugging removes chunks and keeps any removal that still fails. For history, `git bisect` binary-searches commits: 1000 commits need at most $\lceil\log_2 1000\rceil=10$ builds. For rare failures, the number of repetitions needed to see a failure of probability $p$ with confidence $1-\alpha$ is $n\ge\ln\alpha/\ln(1-p)$.

**Example.** A configuration regression is somewhere in 48 commits: `cfg` holds `gain=1` until commit 31 changes it. `git bisect run` uses a script that tests the file (`grep -q 'gain=1' cfg`). How many test runs does it need, which commit does it report, and how does the number of revisions left evolve?

**Solution.** Each run halves the range, so $\lceil\log_2 48\rceil=6$ runs are enough: 23, 11, 5, 2, 0 and 0 revisions are left after the successive runs, and 48 commits cost 6 builds instead of up to 47. The last run leaves one commit, the first bad one, c31. The "roughly N steps" line is git's own estimate and counts the remaining ones. The session is:

```
$ git bisect start HEAD <first-commit>      # 48 commits; cfg holds "gain=1" until the bug lands
Bisecting: 23 revisions left to test after this (roughly 5 steps)
$ git bisect run ./test.sh                  # test.sh:  grep -q 'gain=1' cfg
running  './test.sh'
Bisecting: 11 revisions left to test after this (roughly 4 steps)
running  './test.sh'
Bisecting: 5 revisions left to test after this (roughly 3 steps)
running  './test.sh'
Bisecting: 2 revisions left to test after this (roughly 2 steps)
running  './test.sh'
Bisecting: 0 revisions left to test after this (roughly 1 step)
running  './test.sh'
Bisecting: 0 revisions left to test after this (roughly 0 steps)
running  './test.sh'
<hash> is the first bad commit              # commit c31
```

How many repeats expose a rare failure? The curve $1-(1-p)^n$ shows it (move the slider of $p$):

```explore
{
  "title": "How many repeats to see a rare failure?",
  "title_vi": "Cần lặp bao nhiêu lần để thấy một lỗi hiếm?",
  "prompt": "Predict first: if a test fails 6 times in 100 runs, is 50 runs enough to be 95% sure of seeing a failure? Then check with the slider and find the failure rate for which 20 runs are enough.",
  "prompt_vi": "Dự đoán trước: nếu một test lỗi 6 lần trong 100 lần chạy, 50 lần chạy có đủ để chắc chắn 95% thấy một lỗi không? Sau đó kiểm tra bằng thanh trượt và tìm tỉ lệ lỗi mà 20 lần chạy là đủ.",
  "params": [
    { "name": "pp", "label": "failure probability per run p", "label_vi": "xác suất lỗi mỗi lần chạy p", "min": 0.5, "max": 50, "step": 0.5, "value": 6, "unit": "%" }
  ],
  "let": [
    { "name": "q", "expr": "pp/100" },
    { "name": "n95", "expr": "ceil(ln(0.05)/ln(1-q))" },
    { "name": "n99", "expr": "ceil(ln(0.01)/ln(1-q))" }
  ],
  "plot": {
    "x": { "name": "n", "min": 0, "max": 200, "label": "repeated runs n", "label_vi": "số lần chạy lặp n" },
    "y": { "label": "P(at least one failure) (%)", "label_vi": "P(thấy ít nhất một lỗi) (%)", "min": 0, "max": 100 },
    "series": [
      { "expr": "100*(1-(1-q)^n)", "label": "1 - (1-p)^n", "label_vi": "1 - (1-p)^n", "color": "blue" },
      { "expr": "95", "label": "95 % target", "label_vi": "mục tiêu 95 %", "color": "grey" }
    ],
    "points": [
      { "x": "n95", "y": "100*(1-(1-q)^n95)", "label": "runs for 95 %", "label_vi": "số lần cho 95 %", "color": "green" }
    ]
  },
  "readouts": [
    { "label": "runs for 95 % confidence", "label_vi": "số lần chạy cho độ tin cậy 95 %", "expr": "n95", "unit": "", "digits": 0 },
    { "label": "runs for 99 % confidence", "label_vi": "số lần chạy cho độ tin cậy 99 %", "expr": "n99", "unit": "", "digits": 0 }
  ]
}
```

### How AddressSanitizer decides: shadow memory and the access check

Reading a report is easier once you know what produced it. AddressSanitizer replaces `malloc` and `free`, surrounds every allocation with poisoned **redzones**, puts freed memory in a **quarantine** (also poisoned) so that stale pointers are caught for a while, and the compiler rewrites every load and store into "check, then access" (AddressSanitizer wiki, *AddressSanitizerAlgorithm*, "Short version"). The data structure that makes the check cheap is **shadow memory**: every aligned 8-byte word of application memory has one shadow byte.

The mapping on 64-bit Linux is $\text{Shadow}=(\text{Mem}\gg3)+\texttt{0x7fff8000}$ (same wiki, "Mapping"). Because `malloc` returns 8-byte aligned blocks, only the tail of an allocation can have a word that is partly valid, so a shadow byte takes one of a small set of values: $0$ if all 8 bytes are addressable, a negative value if none are (different negative codes name the reason, such as a heap redzone), and $k\in\{1,\dots,7\}$ if only the first $k$ bytes are addressable. For `malloc(13)` at an aligned address the two words get shadow $0$ and $5$, since $13=8+5$. A real run confirms it: the report of a bad read next to a 13-byte block showed the shadow row `fa fa 00 [05] fa fa ...`, with `fa` marking the heap redzone.

The instrumented access of size $s$ at address $a$ is:

1. load $v=\text{shadow}(a)$;
2. if $v=0$, the access is fine (fast path, one load and one compare);
3. otherwise do the *slow path*: let $\ell=(a\bmod 8)+s-1$ be the offset of the last byte touched inside the word; the access is an error iff $\ell\ge v$ (for $v>0$), and always an error for negative $v$.

The wiki's slow-path function is exactly this test, and it assumes the access stays within one 8-byte word. Worked case with the 13-byte block above: a 4-byte read at offset 9 has $\ell=1+3=4<5$ and passes; at offset 10 it has $\ell=2+3=5\ge5$ and fails. A real run confirms both (offset 9 silent, offset 10 reported as `heap-buffer-overflow ... READ of size 4`). Two practical consequences follow: the check costs one extra load for correct accesses, which explains the "about 2x slower" figure in the table; and the shadow region costs one eighth of the address space it covers, part of the memory overhead.

![The 13-byte block as two 8-byte words with shadow values 0 and 5, and two 4-byte reads at offsets 9 and 10](/lesson-figures/CPP08-2.svg)

*Figure: the theory case drawn; the same test $\ell\ge v$ that passes the read at offset 9 fails the one at offset 10, because byte 13 is poisoned.*

**Example.** A 10-byte heap block is allocated with `malloc(10)` and read with a 2-byte access at offset 8 or at offset 9 (run for real under `-fsanitize=address`). Using the shadow-memory rule, for which offset is a report expected, and what do the shadow bytes of the block look like?

```cpp
#include <cstdlib>
#include <cstdio>
#include <cstring>
int main(int argc, char** argv) {
  volatile char* p = static_cast<volatile char*>(std::malloc(10));
  int off = std::atoi(argv[1]);
  volatile short x = *reinterpret_cast<volatile short*>(p + off);   // 2-byte read at offset off
  (void)x;
  std::puts("no report"); std::free((void*)p);
}
```

**Solution.** $10=8+2$, so the shadow bytes are $0$ (the first 8 bytes fully addressable) and $2$ (only the first 2 bytes of the next group). An access of size $s$ at position $a$ in a group is allowed if $a+s-1<$ shadow value $\ell$. Offset 8: $\ell=(0)+2-1=1<2$, silent. Offset 9: $\ell=1+2-1=2\ge2$, reported with "0 bytes to the right of 10-byte region". The printed row `00[02]` is exactly the pair of shadow values; with the block at $0\mathrm{x}502000000010$ the shadow address is $(\texttt{0x502000000010}\gg3)+\texttt{0x7fff8000}=\texttt{0xa047fff8002}$, which is the `00`, and the next byte is the `02`. The runs print:

```
$ g++ -std=c++20 -g -fsanitize=address shadow.cpp -o shadow && ./shadow 8
no report
$ ./shadow 9
==...==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x502000000019 ...
READ of size 2 at 0x502000000019 thread T0
0x50200000001a is located 0 bytes to the right of 10-byte region [0x502000000010,0x50200000001a)
=>0x0a047fff8000: fa fa 00[02]fa fa fa fa fa fa fa fa fa fa fa fa
```

### What AddressSanitizer cannot see, and which tool covers the gap

The scheme only detects an access if the *target byte itself* is poisoned. Three families of bugs escape for that reason.

- **Jumping over the redzone.** If an index is so wrong that the access lands inside a different, valid object, the shadow byte is $0$ and nothing is reported. Tested: two `malloc(32)` blocks `p` and `q` were 48 bytes apart (the 32 usable bytes plus 16 bytes of poisoned padding), so `p[48]` read `q[0]` without any report, while `p[32]` was caught.
- **Overflow inside one object.** Fields of a struct, or elements of a struct's array member, are contiguous with no redzone between them. Writing `s.buf[4]` on `int buf[4]` clobbers the neighbouring field `limit` silently under ASan. In a test the program printed `limit=5` with no report. UndefinedBehaviorSanitizer's `-fsanitize=bounds` ("out of bounds array indexing in cases where the array bound can be statically determined") did report it. This is the reason the lesson combines `address,undefined` rather than choosing one.
- **Logic errors with valid memory.** A wrong index that stays inside the object, a stale but still-allocated pointer, or a race are not memory errors; only tests and other sanitizers address them.

The general lesson: a sanitizer is a *dynamic* check of specific bug classes along the executed path. A silent run is evidence, not proof, so the tool choice table of this lesson is a coverage statement, and a regression test that asserts on values still has to exist.

![Two heap blocks with poisoned padding and a struct with no padding: where ASan reports and where it stays silent](/lesson-figures/CPP08-3.svg)

*Figure: ASan checks the byte it is about to touch. `p[32]` lands in poison; `p[48]` lands in valid memory of another object; `buf[4]` lands in a valid member of the same object.*

**Example.** A `std::vector<int>` grown by five `push_back` calls holds 5 elements in a buffer for 8 (capacity 8, 32 bytes). The program reads `v[6]` and then `v[8]` under `-fsanitize=address`, and once more under `-D_GLIBCXX_ASSERTIONS` (library bounds checks). Which reads does ASan report, what does the silent one print, and what does the assertion build do?

```cpp
std::vector<int> v;
for (int i = 1; i <= 5; ++i) v.push_back(10 * i);              // size 5, capacity 8
std::cout << "size " << v.size() << ", capacity " << v.capacity() << std::endl;
std::cout << "v[6] = " << v[6] << std::endl;                   // past the end, inside the allocation
std::cout << "v[8] = " << v[8] << std::endl;                   // past the allocation
```

**Solution.** Reading `v[6]` is past the end of the vector but inside the allocation (index 6 of 8 slots, $6\cdot4=24<32$ bytes), so ASan stays silent and the program prints the allocator's fill pattern; `v[8]` starts at byte $8\cdot4=32$, past the allocation, and is reported ("0 bytes to the right of 32-byte region"). Compiling with `-D_GLIBCXX_ASSERTIONS` catches the first one as well: the program aborts (exit status 134) before printing `v[6]`. The garbage `-1094795586` is `0xBEBEBEBE`, ASan's fill value for fresh heap memory. The lesson is the same as above: the sanitizer knows the allocation, not the container's `size()`, so a checked `at()` or the assertion mode of the standard library must complement it. The two sessions are:

```
$ g++ -std=c++20 -g -fsanitize=address cap.cpp -o cap && ./cap
size 5, capacity 8
v[6] = -1094795586
==317745==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x503000000060 ...
READ of size 4 at 0x503000000060 thread T0
0x503000000060 is located 0 bytes to the right of 32-byte region [0x503000000040,0x503000000060)
$ g++ -std=c++20 -g -D_GLIBCXX_ASSERTIONS cap.cpp -o cap2 && ./cap2; echo "exit $?"
size 5, capacity 8
exit 134
```

### Watchpoints: finding who wrote a value

When a variable has the wrong value and you do not know which line wrote it, a **watchpoint** asks the debugger to stop when it changes. `watch expr` stops when the expression is written and its value changes; `rwatch` stops on reads and `awatch` on either (GDB manual, *Setting Watchpoints*). Two details matter in practice. Ordinarily a watchpoint respects variable scope, so for a global or a heap object reached through a pointer use `watch -location expr` (`-l`), which takes the address once and watches that memory. And there are two implementations: with hardware support, watchpoints "do not slow down the running of your program"; otherwise GDB single-steps and tests the value each time, which the manual describes as "hundreds of times slower than normal execution". Hardware watchpoints are the first thing to try, software ones the last resort for a bug whose culprit you cannot guess.

A worked case, run with GDB: a struct has `int buf[4]; int limit = 100;` and a loop `for (i = 0; i <= n; ++i) buf[i] = i + 1;` with `n = 4`. With `watch -l s.limit` GDB stops with `Old value = 100`, `New value = 5`, in the loop line of `fill (n=4)`, and `bt` shows the call from `main`. The value 5 is the last value written ($i+1$ with $i=4$), which immediately identifies the off-by-one in the loop bound, even though no sanitizer needed to be involved.

**Example.** A global `g_mode` should stay 1 (run) after `arm()`, but the program ends with the wrong mode. Which GDB command stops at the first write that makes it greater than 1, without knowing which function writes it, and what do the old value, the new value and the frame show?

```cpp
int g_mode = 0;                          // 0 = idle, 1 = run
void arm()           { g_mode = 1; }
void set_gain(int k) { g_mode = k * 2; } // BUG: clobbers the mode
int main() { arm(); set_gain(3); std::cout << "mode " << g_mode << "\n"; }
```

**Solution.** The conditional watchpoint `watch g_mode if g_mode > 1` stops at the first write that satisfies the condition. `Old value = 1`, `New value = 6` and the frame `set_gain (k=3)` identify the writer: $6=3\cdot2$ is `k * 2`, so the bug is the formula in `set_gain`, which was written for another variable. A global needs no `-l`; the condition keeps the stop to the interesting write. The batch session prints:

```
$ g++ -std=c++20 -g -O0 glob.cpp -o glob && gdb -batch -ex 'watch g_mode if g_mode > 1' -ex run -ex bt ./glob
Hardware watchpoint 1: g_mode
Old value = 1
New value = 6
set_gain (k=3) at glob.cpp:4
4	void set_gain(int k) { g_mode = k * 2; }   // BUG: clobbers the mode
#0  set_gain (k=3) at glob.cpp:4
#1  0x00005555555551ee in main () at glob.cpp:7
```

### Bisecting when the failure is probabilistic

Bisection assumes a deterministic test: if the test says "good" at commit $c$ then the bug is later, otherwise earlier. For $N$ commits this takes $\lceil\log_2N\rceil$ steps (the `git bisect` documentation shows an example saying "roughly 10 steps" for a few hundred to a thousand revisions). If the failure appears only with probability $p$ per run on a bad commit, a single "pass" is not evidence of a good commit. Run each tested commit $r$ times and call it good only if all $r$ runs pass. A good commit never fails, so errors can happen only on bad commits, each with probability $(1-p)^r$ of being misjudged as good. If at most $k=\lceil\log_2N\rceil$ steps test a bad commit, the probability of an entirely correct search is at least $\bigl(1-(1-p)^r\bigr)^k$. To reach confidence $1-\alpha$ it suffices that $(1-p)^r\le1-(1-\alpha)^{1/k}$, i.e. $r\ge\ln\!\bigl(1-(1-\alpha)^{1/k}\bigr)/\ln(1-p)$. The worst-case cost is $k\,r$ runs, because good commits need all $r$ runs but bad ones stop at the first failure. The bound is conservative (it unions the per-step errors) but it shows the shape of the trade-off: a rarer failure multiplies the cost of every one of the $k$ steps, so first raise $p$ by stressing the test (more threads, fixed seeds, sanitizer builds) before bisecting.

**Example.** Search 64 commits for a bug that shows with probability $p=0.5$ per run, with confidence $1-\alpha=0.95$. What number of repeats $r$ per commit is needed, what is the worst-case number of runs, and what does a simulation of 20000 searches (each tested commit repeated up to $r$ times, a bad commit stopping at its first failure) give for $r=1$ and $r=7$?

**Solution.** Here $k=\lceil\log_2 64\rceil=6$ and $r\ge\ln(1-0.95^{1/6})/\ln0.5=6.88$, so $r=7$ and the worst case is $kr=42$ runs. With $r=1$ the bound is $0.5^6=0.0156$ and the simulation succeeds in 18 % of the searches; with $r=7$ the bound $\bigl(1-0.5^7\bigr)^6=0.954$ holds (97.7 % observed, since the bound adds up errors that rarely coincide) at a mean of 26.9 runs. The simulation is random, so the figures below are as measured and a rerun differs in the last digit. The script prints:

```
$ python3 prob.py        # N = 64 commits, p = 0.5, 1 - alpha = 0.95; 20000 simulated searches per row
r=1: bound=0.0156  simulated success=0.1792  mean runs=6.0
r=7: bound=0.9540  simulated success=0.9765  mean runs=26.9
k = 6  r = 7  worst-case runs k*r = 42
```

Move the sliders to see the repeats needed for other sizes:

```explore
{
  "title": "Bisecting a flaky bug: repeats per commit",
  "title_vi": "Bisect một lỗi chập chờn: số lần lặp mỗi commit",
  "prompt": "Predict first: with p = 50 % per run and 64 commits, is r = 3 repeats per commit enough for 95 % confidence? Then raise N or lower p and watch the repeats needed.",
  "prompt_vi": "Dự đoán trước: với p = 50 % mỗi lần chạy và 64 commit, r = 3 lần lặp mỗi commit có đủ cho độ tin cậy 95 % không? Sau đó tăng N hoặc giảm p và xem số lần lặp cần thiết thay đổi ra sao.",
  "params": [
    { "name": "N", "label": "commits to search N", "label_vi": "số commit cần tìm N", "min": 8, "max": 4096, "step": 1, "value": 64, "unit": "" },
    { "name": "pp", "label": "failure probability per run on a bad commit p", "label_vi": "xác suất lỗi mỗi lần chạy trên commit xấu p", "min": 5, "max": 100, "step": 1, "value": 50, "unit": "%" },
    { "name": "al", "label": "allowed error alpha", "label_vi": "sai số cho phép alpha", "min": 1, "max": 20, "step": 1, "value": 5, "unit": "%" },
    { "name": "r", "label": "repeats per tested commit r", "label_vi": "số lần lặp mỗi commit r", "min": 1, "max": 60, "step": 1, "value": 7, "unit": "" }
  ],
  "let": [
    { "name": "q", "expr": "pp/100" },
    { "name": "a", "expr": "al/100" },
    { "name": "k", "expr": "ceil(ln(N)/ln(2) - 0.000001)" },
    { "name": "rneed", "expr": "ceil(ln(1-(1-a)^(1/k))/ln(1-q))" },
    { "name": "bound", "expr": "(1-(1-q)^r)^k" }
  ],
  "plot": {
    "x": { "name": "m", "min": 1, "max": 60, "label": "repeats per commit r", "label_vi": "số lần lặp mỗi commit r" },
    "y": { "label": "lower bound on P(correct search)", "label_vi": "cận dưới của P(tìm đúng)", "min": 0, "max": 1 },
    "series": [
      { "expr": "(1-(1-q)^m)^k", "label": "(1-(1-p)^r)^k", "label_vi": "(1-(1-p)^r)^k", "color": "blue" },
      { "expr": "1-a", "label": "target 1-alpha", "label_vi": "mục tiêu 1-alpha", "color": "grey" }
    ],
    "points": [
      { "x": "r", "y": "bound", "label": "your r", "label_vi": "r của bạn", "color": "green" }
    ]
  },
  "readouts": [
    { "label": "bisection steps k", "label_vi": "số bước bisect k", "expr": "k", "unit": "", "digits": 0 },
    { "label": "smallest r for 1-alpha", "label_vi": "r nhỏ nhất cho 1-alpha", "expr": "rneed", "unit": "", "digits": 0 },
    { "label": "worst-case runs k*r", "label_vi": "số lần chạy tối đa k*r", "expr": "k*rneed", "unit": "", "digits": 0 },
    { "label": "bound with your r", "label_vi": "cận với r của bạn", "expr": "bound", "unit": "", "digits": 3 }
  ]
}
```

## Worked example

### Case 1: an off-by-one in a moving average

**Problem.** `moving_average(v, w)` of the reference implementation should return one mean per full window of $w$ samples. For `v = {1, 2, 3, 4, 5}` and `w = 2` it should print `1.5 2.5 3.5 4.5`; the program prints `3 4.5 6 4.5` and does not crash. Find the cause with the tools of this lesson, reduce the failure, fix it and lock the fix in with a regression test.

**Solution.**

1. *Hypothesis from the numbers* (Intuition, "predict before you compute"). The first value 3 equals $(1+2+3)/2$: three elements were summed and the divisor stayed $w=2$. The window loop therefore runs one iteration too many. The other values fit: $(2+3+4)/2=4.5$, $(3+4+5)/2=6$, and the last window $(4+5+v[5])/2=4.5$ needs $v[5]=0$, an element that does not exist.
2. *Confirm with AddressSanitizer* (theory, "Reading an AddressSanitizer report"). `g++ -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer buggy.cpp` reports `heap-buffer-overflow`, `READ of size 8` at `buggy.cpp:10`, and "0 bytes to the right of 40-byte region". The vector holds $40/8=5$ doubles, so index 5 was read: for the last window $i=3$, $k=2$ gives $i+k=5$. The earlier outputs were wrong too, but only this read is a memory error.
3. *Reduce* (theory, "Reduction and bisection"). With `{1,2,3}` and `w=2` the program prints `3 2.5` and ASan reports a 24-byte region; with `{1,2}` and `w=1` it prints `3 2` (the correct answer is `1 2`) and a 16-byte region. The smallest reproducer is one element and `w=1`: it prints `7`, which is even correct, yet ASan still reports "0 bytes to the right of 8-byte region". Three numbers and a loop are now enough to reason about.
4. *Fix*: change `k <= w` to `k < w`.
5. *Regression test* with hand-computed values (theory, "Test harnesses and regression tests"): `moving_average({1,2,3,4,5}, 2)` equals `{1.5, 2.5, 3.5, 4.5}`; window 1 returns the input; window 5 returns `{3}`; windows 6 and 0 return empty.
6. *Confirm*: the test fails on the old code (the first value is 3, not 1.5, with or without a sanitizer) and passes on the fixed code under ASan and UBSan with no report.

![The elements each window reads in Case 1: three per window with k <= w, the last window reading index 5](/lesson-figures/CPP08-4.svg)

*Figure: Case 1 to scale. Each window reads one element too many (dashed); the last one is past the end of the 5-element vector.*

**Check.** An independent tool agrees: `valgrind ./buggy` prints `Invalid read of size 8` and "Address ... is 0 bytes after a block of size 40 alloc'd", the same 40-byte block. A units check: the sum of three elements divided by 2 cannot be a mean, since the mean of $\{1,2,3\}$ would be divided by 3.

**Takeaway.** The wrong numbers pointed to the hypothesis, ASan confirmed it at the exact line, and a test on values would have caught it without either tool.

### Case 2: a corrupted limit with no crash and no sanitizer report

**Problem.** A struct holds `int buf[4]` followed by `int limit = 100`, and a helper fills the buffer with `for (i = 0; i <= n; ++i) buf[i] = i + 1` for `n = 4`. The program prints `limit=5` instead of `limit=100`. Nothing crashed. Find the writer, explain why the first tool stays silent and fix it.

**Solution.**

1. *Hypothesis from the value.* 5 is not a plausible limit; it is $i+1$ for $i=4$, the last value the loop writes. So the loop wrote one element too far and `buf[4]` aliases `limit`. The `<=` where `<` was meant is the first suspect, not yet proved.
2. *Try AddressSanitizer.* Built with `-fsanitize=address` the program still prints `limit=5` and nothing else: `buf` and `limit` are addressable bytes of one object, with no redzone between members, so the access passes the shadow check (theory, "What AddressSanitizer cannot see").
3. *Try UBSan.* With `-fsanitize=undefined` it reports `wp.cpp:5:39: runtime error: index 4 out of bounds for type 'int [4]'`, because the array bound is a compile-time constant.
4. *Confirm with a watchpoint, independent of the sanitizers* (theory, "Watchpoints"). In GDB: `break main`, `run`, `watch -l s.limit`, `continue`. GDB stops with `Old value = 100`, `New value = 5` in `fill (n=4)` at the loop line, and `bt` names `main` as the caller (`Hardware watchpoint 2: -location s.limit`).
5. *Fix and lock in.* Change `<=` to `<` and add a regression test with a hand-computed expectation: after `fill(4)`, `limit == 100` and `buf == {1,2,3,4}`. It fails on the old code with or without sanitizers.

**Check.** Three different observers (UBSan's bounds check, the GDB watchpoint and the final value) agree on one index: 4. After the fix, `limit=100` is printed and the ASan and UBSan builds are silent.

**Takeaway.** The value pointed to the hypothesis, UBSan and GDB each confirmed it by a different route, and ASan alone would have missed it; a reduced reproducer (a struct, a loop, `n = 4`) keeps the watchpoint session short.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: AddressSanitizer wiki, list of detected errors)* Match each bug to the best tool: (a) writing one element past a heap array; (b) reading a vector element after `push_back` reallocated it; (c) `int` addition overflowing; (d) two threads incrementing a plain `int`; (e) a `new` that is never deleted; (f) reading a local `double` before it was assigned.
2. **(Easy)** Read this report excerpt and state the bug class, the access size, the source line, the name and size of the variable, and the index of the first bad access: `stack-buffer-overflow ... READ of size 4 ... #0 ... in main stk.cpp:4 ... This frame has 1 object(s): [32, 56) 'hist' (line 3) <== Memory access at offset 56 overflows this variable`.
3. **(Easy)** *(Adapted from: Pro Git, Debugging with Git - binary search)* A regression appeared somewhere in 1000 commits. How many builds does `git bisect` need at most? How many would a linear search over commits need in the worst case?
4. **(Medium)** Explain why an unsanitized program with the same off-by-one (`k <= w`) can print plausible numbers and still "work". For `v = {2, 4, 6, 8, 10, 12}` and `w = 3`, derive by hand the four numbers the buggy loop prints (treat the out-of-range read as 0) and the four correct means, and show why the last printed number happens to be right.
5. **(Medium)** Find the bug in the following program from its GDB output (`frame = std::unique_ptr<Frame> = {get() = 0x0}`, SIGSEGV at line 11) and write the minimal fix. Which two GDB commands show the evidence?
   ```cpp
   int use(std::unique_ptr<Frame> f) { return f->id; }
   int main() {
     auto frame = std::make_unique<Frame>(Frame{7});
     int a = use(std::move(frame));
     int b = frame->id;
     std::cout << a + b << "\n";
   }
   ```
6. **(Medium)** Write a regression test for the moving-average bug using the `Checker` harness of this lesson. It must fail on the buggy version even when no sanitizer is used. Explain why asserting on values is stronger than waiting for a crash.
7. **(Medium)** *(Adapted from: C++ Core Guidelines, section on testing/assertions, and common unit-test practice)* Design test cases for `wrap_to_pi(a)`, which maps an angle to $[-\pi,\pi)$. List at least eight cases with expected values (to 5 decimals) including boundaries, negative inputs, multiples of $2\pi$, a large input and NaN.
8. **(Hard)** A test fails on average 2 out of every 100 runs. How many repeated runs give a 95% chance of seeing at least one failure? List four causes of flakiness in robotics tests and one tool or technique for each.
9. **(Hard)** Implement `minimize(items, fails)` that greedily removes chunks (halving the chunk size) while the bug still shows. Run it on `list(range(64))` where the bug needs both 17 and 42 to be present, and report the minimal list and the number of calls of `fails`.
10. **(Hard)** *(Adapted from: GCC documentation, Instrumentation Options)* Design the CI jobs for a C++ robotics repository: which builds (flags, build type), which tests under which sanitizer, and why ASan and TSan need separate jobs. State what each job would catch from exercises 1 and 8.
11. **(Mini-project)** Take `buggy.cpp`. Run it under ASan, Valgrind and GDB; fill a table (tool, command, key line of output, what it taught you); reduce the input to the smallest failing case by hand; write the regression test with the harness; fix; show the green run under ASan+UBSan.
12. **(Challenge)** `char *p = malloc(21)` returns the 8-byte aligned address $A=\texttt{0x504000000010}$. (a) Using $\text{Shadow}=(\text{Mem}\gg3)+\texttt{0x7fff8000}$, compute the shadow addresses of the three words of the block and give their shadow values. (b) For 4-byte reads at offsets 16, 17, 18 and 20 from $A$, and an 8-byte read at offset 16, apply the slow-path test and say which are reported. (c) A 1-byte read at offset 20, and one at offset 21? (d) Which of (b) would also be missed by a scheme with only one bit per word ("word fully valid or not")? (adapted from the AddressSanitizer wiki, *AddressSanitizerAlgorithm*, "Mapping" and the `SlowPathCheck` function)
13. **(Challenge)** Two blocks `p = malloc(72)` and `q = malloc(72)` are allocated one after the other under ASan, and the program executes `volatile char v = p[d];` with $d=q-p$, then `volatile char w = p[72];`. Predict, with the shadow-memory model, which of the two reads is reported and why, and what $d$ would you expect to be (justify, then measure). Propose two different ways to make the first read detectable and discuss the cost of each. (adapted from the AddressSanitizer wiki, *AddressSanitizerAlgorithm*, "Short version" and "Memory mapping and Instrumentation")
14. **(Challenge)** `struct Ring { int slot[6]; int head; }; Ring r{{0,0,0,0,0,0},250}; void fill(int n){ for (int i = 0; i <= n; ++i) r.slot[i] = 2 * i; }` and `fill(6)`. (a) Predict what `head` holds afterwards and whether `-fsanitize=address` reports anything, and say why. (b) Which UBSan check can report it? (c) Write the GDB command that finds the line that corrupts `head` without knowing the loop, say what `Old value` and `New value` will show, and explain why a software watchpoint would be too slow for a program that runs for minutes. (adapted from the GDB manual, *Setting Watchpoints*, and the Clang UBSan manual, `-fsanitize=bounds`)
15. **(Challenge)** A test fails with probability $p=0.35$ on every run of a bad commit and never on a good commit. You bisect 4000 commits with $k=\lceil\log_2 4000\rceil$ steps, running each tested commit $r$ times and calling it good only if all $r$ runs pass. (a) Derive the probability that the whole search is correct, as a lower bound in $r$, $p$ and $k$. (b) Find the smallest $r$ giving at least 95% and the worst-case number of runs. (c) What is the success lower bound if $r=1$? (d) Name two ways to reduce the total cost, one that raises $p$ and one that shortens the search. (source: git-bisect documentation, the example session and "Bisect skip"; the probability bound is derived here)

## Reference implementation

First, the buggy program and the exact steps used in the worked example. Then a small test harness (`Checker`, `Test`, `run_tests`) together with the fixed function, runnable as a single file.

`buggy.cpp`:

```cpp
#include <cstddef>
#include <iostream>
#include <vector>

// Moving average with window w over v; returns one value per full window.
std::vector<double> moving_average(const std::vector<double>& v, std::size_t w) {
  std::vector<double> out;
  for (std::size_t i = 0; i + w <= v.size(); ++i) {
    double sum = 0.0;
    for (std::size_t k = 0; k <= w; ++k) sum += v[i + k];  // BUG: should be k < w
    out.push_back(sum / static_cast<double>(w));
  }
  return out;
}

int main() {
  const std::vector<double> v{1.0, 2.0, 3.0, 4.0, 5.0};
  for (double x : moving_average(v, 2)) std::cout << x << ' ';
  std::cout << '\n';
}
```

Commands:

```
g++ -std=c++17 -g buggy.cpp -o buggy && ./buggy                       # wrong output, no crash
g++ -std=c++17 -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer buggy.cpp -o buggy_asan && ./buggy_asan
valgrind --error-exitcode=9 ./buggy                                    # "Invalid read of size 8"
gdb -batch -ex run -ex bt -ex "info locals" ./segv                     # crash site and variables
```

Harness and fixed function:

```cpp
// CPP08 reference: a tiny test harness (Checker + run_tests) and the fixed moving average.
#include <cmath>
#include <cstddef>
#include <exception>
#include <functional>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

class Checker {
 public:
  void check(bool ok, const std::string& what) {
    ++checks_;
    if (!ok) failures_.push_back(what);
  }
  // |a - b| <= tol. NaN never passes.
  void check_near(double a, double b, double tol, const std::string& what) {
    check(std::fabs(a - b) <= tol, what + " (got " + std::to_string(a) + ", expected " + std::to_string(b) + ")");
  }
  // Passes only if f() throws an exception of type E.
  template <class E, class F>
  void check_throws(F f, const std::string& what) {
    bool threw = false;
    try {
      f();
    } catch (const E&) {
      threw = true;
    } catch (...) {
    }
    check(threw, what + " (expected exception)");
  }
  void fail(const std::string& what) { check(false, what); }
  std::size_t checks() const { return checks_; }
  const std::vector<std::string>& failures() const { return failures_; }

 private:
  std::size_t checks_ = 0;
  std::vector<std::string> failures_;
};

struct Test {
  std::string name;
  std::function<void(Checker&)> fn;
};

// Runs every test, prints "PASS name" or "FAIL name: message" per failure, then a summary
// line "<p> passed, <f> failed". An exception escaping a test counts as a failure of that test
// and must not stop the remaining tests. Returns the number of failed tests.
int run_tests(const std::vector<Test>& tests, std::ostream& out) {
  int passed = 0, failed = 0;
  for (const Test& t : tests) {
    Checker c;
    try {
      t.fn(c);
    } catch (const std::exception& e) {
      c.fail(std::string("uncaught exception: ") + e.what());
    } catch (...) {
      c.fail("uncaught unknown exception");
    }
    if (c.failures().empty()) {
      ++passed;
      out << "PASS " << t.name << "\n";
    } else {
      ++failed;
      for (const std::string& f : c.failures()) out << "FAIL " << t.name << ": " << f << "\n";
    }
  }
  out << passed << " passed, " << failed << " failed\n";
  return failed;
}

// The fixed function from the debugging walk-through (window loop uses k < w).
std::vector<double> moving_average(const std::vector<double>& v, std::size_t w) {
  std::vector<double> out;
  if (w == 0) return out;
  for (std::size_t i = 0; i + w <= v.size(); ++i) {
    double sum = 0.0;
    for (std::size_t k = 0; k < w; ++k) sum += v[i + k];
    out.push_back(sum / static_cast<double>(w));
  }
  return out;
}

// ---- self-test
int main() {
  std::ostringstream os;
  int failed = run_tests(
      {{"ok", [](Checker& c) { c.check(true, "t"); }},
       {"bad", [](Checker& c) { c.check_near(1.0, 2.0, 0.1, "near"); }},
       {"boom", [](Checker&) { throw std::runtime_error("kaput"); }}},
      os);
  if (failed != 2) return 1;
  if (os.str().find("2 failed") == std::string::npos) return 2;
  const auto avg = moving_average({1, 2, 3, 4, 5}, 2);
  if (avg.size() != 4 || avg[3] != 4.5) return 3;
  std::cout << "CPP08 reference self-test passed\n";
}
```

## Independent practice

### Goal

Build a small test harness, use it to write a regression test for a real off-by-one bug, and prove the fixed code is clean under the sanitizers.

### Setup

`g++` with C++17. Optionally `gdb` and `valgrind` (`sudo apt install gdb valgrind`). Save the starter code and the tests below it as `lab.cpp`; build with `g++ -std=c++17 -Wall -Wextra -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer lab.cpp -o lab && ./lab`.

### Tasks

1. Save `buggy.cpp`, run it plain and under ASan; copy the first four lines of the report and decode them as in the theory section.
2. Reduce the input by hand to the smallest array that still triggers the ASan error.
3. Implement `Checker::check`, `check_near`, `fail`, `check_throws`, and the getters.
4. Implement `run_tests` with exact output formatting; make sure an exception escaping a test does not stop the others.
5. Implement the fixed `moving_average`, run the tests under ASan+UBSan.
6. Temporarily reintroduce the `k <= w` bug in your `moving_average` and confirm that the tests fail with a readable message (no crash needed), then restore the fix.

### Starter code

```cpp
#include <cmath>
#include <cstddef>
#include <exception>
#include <functional>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

class Checker {
 public:
  // Counts one check; records `what` as a failure message when ok is false.
  void check(bool ok, const std::string& what) { throw std::logic_error("NotImplemented"); }
  // Passes iff |a - b| <= tol. NaN must NOT pass. On failure the message is
  // what + " (got <a>, expected <b>)" using std::to_string.
  void check_near(double a, double b, double tol, const std::string& what) { throw std::logic_error("NotImplemented"); }
  // Passes only if f() throws an exception of type E (any other outcome fails, but must not escape).
  template <class E, class F>
  void check_throws(F f, const std::string& what) { throw std::logic_error("NotImplemented"); }
  // Records an unconditional failure.
  void fail(const std::string& what) { throw std::logic_error("NotImplemented"); }
  std::size_t checks() const { throw std::logic_error("NotImplemented"); }
  const std::vector<std::string>& failures() const { throw std::logic_error("NotImplemented"); }
};

struct Test {
  std::string name;
  std::function<void(Checker&)> fn;
};

// Runs every test with a fresh Checker. Per passing test print "PASS <name>\n"; per failure message
// print "FAIL <name>: <message>\n". An exception escaping a test (std::exception or anything else)
// counts as ONE failure of that test with a message starting "uncaught exception" and must not stop
// the other tests. Finally print "<passed> passed, <failed> failed\n". Return the number failed.
int run_tests(const std::vector<Test>& tests, std::ostream& out) { throw std::logic_error("NotImplemented"); }

// The fixed function from the debugging walk-through: one average per FULL window of w samples;
// w == 0 -> empty result. It must never read outside v.
std::vector<double> moving_average(const std::vector<double>& v, std::size_t w) { throw std::logic_error("NotImplemented"); }
```

### Tests

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)

int main() {
  // 1. Checker basics
  Checker c;
  c.check(true, "a");
  c.check(false, "b");
  c.check_near(1.0, 1.05, 0.1, "near-ok");
  c.check_near(1.0, 2.0, 0.1, "near-bad");
  c.check_near(NAN, 1.0, 1e9, "nan-must-fail");
  c.check_throws<std::out_of_range>([] { throw std::out_of_range("x"); }, "throws-ok");
  c.check_throws<std::out_of_range>([] {}, "throws-missing");
  c.check_throws<std::out_of_range>([] { throw std::logic_error("other"); }, "throws-wrong-type");
  CHECK(c.checks() == 8);
  CHECK(c.failures().size() == 5);
  CHECK(c.failures()[0] == "b");
  CHECK(c.failures()[1].find("near-bad (got 1.000000, expected 2.000000)") == 0);
  // 2. run_tests output and return value (hand-written expected text)
  std::ostringstream os;
  int failed = run_tests({{"good", [](Checker& k) { k.check(1 + 1 == 2, "math"); }},
                          {"bad", [](Checker& k) { k.check(false, "boom"); }},
                          {"throws", [](Checker&) { throw std::runtime_error("kaput"); }},
                          {"after", [](Checker& k) { k.check(true, "still runs"); }}},
                         os);
  CHECK(failed == 2);
  CHECK(os.str() == "PASS good\nFAIL bad: boom\nFAIL throws: uncaught exception: kaput\nPASS after\n2 passed, 2 failed\n");
  // 3. non-std exception does not escape
  std::ostringstream os2;
  CHECK(run_tests({{"weird", [](Checker&) { throw 42; }}}, os2) == 1);
  // 4. empty suite
  std::ostringstream os3;
  CHECK(run_tests({}, os3) == 0 && os3.str() == "0 passed, 0 failed\n");
  // 5. moving_average: hand computed and regression for the off-by-one
  std::vector<double> v{1, 2, 3, 4, 5};
  auto m = moving_average(v, 2);
  CHECK(m.size() == 4 && m[0] == 1.5 && m[1] == 2.5 && m[2] == 3.5 && m[3] == 4.5);
  CHECK(moving_average(v, 5).size() == 1 && moving_average(v, 5)[0] == 3.0);
  CHECK(moving_average(v, 6).empty() && moving_average(v, 0).empty() && moving_average({}, 3).empty());
  // 6. property: window 1 is the identity; the sum of window averages shifts correctly
  CHECK(moving_average(v, 1) == v);
  std::cout << "all tests passed\n";
}
```

### Expected output

```
all tests passed
```

With the stubs, the first test terminates with `NotImplemented`. With the bug reintroduced, the harness test 5 fails with the failing `CHECK` line; the sanitizer additionally reports `heap-buffer-overflow`.

### Extension challenge

Add a `TEST(name) { ... }` macro with static registration so that tests need not be listed by hand; add a `--filter` command-line option; or write `minimize` (exercise 9) in C++ and use it to shrink a failing input read from a file.

### Library track

The real-world version of your `Checker` is a test framework. GoogleTest (`sudo apt install libgtest-dev`) is the usual choice for C++ robotics code (ROS 2 `ament_cmake_gtest` wraps it). Save this as `gtest_ma.cpp` with your fixed `moving_average` above it.

```cpp
// gtest_ma.cpp : the regression tests of this lesson with GoogleTest instead of your Checker.
// Put the FIXED moving_average (and its includes) above this line, or #include a header that has it.
#include <gtest/gtest.h>
#include <cmath>
#include <vector>

TEST(MovingAverage, HandComputedWindow2) {
  const std::vector<double> v{1, 2, 3, 4, 5};
  const auto m = moving_average(v, 2);
  ASSERT_EQ(m.size(), 4u);                       // ASSERT_* stops this test, EXPECT_* continues
  EXPECT_DOUBLE_EQ(m[0], 1.5);                   // fails on the buggy code (it gives 3)
  EXPECT_DOUBLE_EQ(m[1], 2.5);
  EXPECT_DOUBLE_EQ(m[3], 4.5);
}

TEST(MovingAverage, Edges) {
  const std::vector<double> v{1, 2, 3, 4, 5};
  EXPECT_EQ(moving_average(v, 1), v);            // window 1 is the identity
  EXPECT_EQ(moving_average(v, 5), std::vector<double>{3.0});
  EXPECT_TRUE(moving_average(v, 6).empty());
  EXPECT_TRUE(moving_average(v, 0).empty());
}

TEST(Checker, NaNNeverPasses) { EXPECT_FALSE(std::fabs(NAN - 1.0) <= 1e9); }

// Build and run (also under the sanitizers, as in the lab):
//   g++ -std=c++17 -g -O1 -fsanitize=address,undefined gtest_ma.cpp -lgtest -lgtest_main -pthread -o gt && ./gt
// Bounds checking without ASan: add -D_GLIBCXX_ASSERTIONS and use v.at(i) or v[i] on the buggy
// program; it aborts (SIGABRT, exit code 134) at the faulty index instead of printing wrong numbers.
```

Expected: `[  PASSED  ] 3 tests.` With the `k <= w` bug put back, `HandComputedWindow2` and `Edges` fail with a readable message (`Expected equality of these values ... 3 vs 1.5`) even without any sanitizer. Compare the output format with your `run_tests`.

## Verification

- Prove the test can fail: revert the fix (or mutate the code) and check that the test goes red. A test that never failed proves nothing.
- Run the whole suite under `-fsanitize=address,undefined`, and again in an optimized build; compare the results. Differences point to undefined behavior.
- Compare against a slow, obviously correct oracle (here, a direct sum over each window) on random inputs.
- Check the return code (`echo $?`) of the test program, since CI uses it.
- After reducing, re-check that the reduced program still shows the *same* error, not a different one.
- For flaky tests, repeat: `ctest --repeat until-fail:200` or a shell loop; log the seed.

## Failure modes

| Mistake | Consequence |
|---|---|
| Debugging without a reproducer | changes are guesses; the bug "disappears" and returns |
| Relying on a crash as the test | UB may not crash (here the program printed wrong numbers) |
| Expected values taken from the code under test | the test passes while the bug stays |
| `assert` in tests compiled with `-DNDEBUG` | tests do nothing in Release (CPP07) |
| Debugging an optimized build | variables "optimized out", lines jump around |
| Fixing the symptom (clamp the index) instead of the cause | a different wrong value appears later |
| Comparing doubles with `==` after computation | spurious failure; use a tolerance, and make NaN fail |
| Testing in one build type only | UB bugs hide at one optimization level |
| Mixing ASan and TSan in one binary | not supported; use separate builds |
| Ignoring the first sanitizer error and reading the last | the first one is the root cause |

## Alternatives and trade-offs

- **Sanitizers vs Valgrind.** Sanitizers need a rebuild but are fast enough to run the whole test suite; Valgrind works on any binary but is slow. Use Valgrind when you cannot rebuild.
- **Debugger vs print statements.** Prints are quick and work in production logs; a debugger gives stack and state without editing code. For timing-sensitive code, logging with timestamps may disturb less than breakpoints.
- **Hand-written harness vs a framework.** A 50-line harness is enough to learn; GoogleTest, Catch2 and doctest add fixtures, parameterized tests and mocking, and integrate with CTest.
- **Unit vs integration vs property-based tests.** Unit tests are fast and precise; integration tests catch interface mistakes; property-based tests (random inputs plus invariants) find unexpected cases.
- **Checked containers.** `-D_GLIBCXX_ASSERTIONS` or `.at()` give bounds checks cheaply in debug builds; keep them on in tests.
- **Static analysis** (`clang-tidy`, `cppcheck`) finds some bugs without running code, with false positives.

## Transfer and retention

The same loop applies in Python (`pytest`, `pdb`, `faulthandler`) and in ROS 2 (`ros2 bag` to replay a failing input, `launch_testing` for integration tests, `colcon test`). A recorded bag is the robotics version of a reproducer. For retention: keep a one-page checklist (reproduce, reduce, locate, fix, regression test, sanitizers) and apply it to the next bug you meet; after a week, redo exercise 9 without looking and explain why each removal step is safe.

## Exercise answers

1. (a) AddressSanitizer (heap-buffer-overflow). (b) AddressSanitizer (`heap-use-after-free`, because the old buffer was freed). (c) UBSan (`signed integer overflow`). (d) ThreadSanitizer (data race). (e) LeakSanitizer (part of ASan on Linux) or Valgrind. (f) Valgrind or MemorySanitizer ("conditional jump depends on uninitialised value"); compiler warnings `-Wuninitialized` catch simple cases.
2. Bug class stack-buffer-overflow; a read of size 4 (one `int`); line 4 of `stk.cpp`, in `main`; the variable is `hist`, occupying bytes $[32,56)$ of the frame, i.e. $24$ bytes $=6$ ints. The access is at offset 56, which is $56-32=24$ bytes from the start of `hist`, so the first bad access is index $24/4=6$, one past the end of a 6-element array (the loop `i < 8` then also reaches index 7, but the first error is the one to read).
3. At most $\lceil\log_2 1000\rceil=10$ builds; linear search needs up to 1000 (or 999).
4. The undefined read one past the vector's buffer returned whatever was in that memory (allocator padding, often 0), so the code ran to completion and printed numbers. The buggy loop sums $w+1=4$ elements and divides by $w=3$: $(2+4+6+8)/3=20/3=6.667$, $(4+6+8+10)/3=28/3=9.333$, $(6+8+10+12)/3=36/3=12$, and for the last window $(8+10+12+v[6])/3$ with $v[6]=0$ gives $30/3=10$. The correct means are $4$, $6$, $8$, $10$. The last number is right only because the extra element read as 0 and so added nothing; the first three are wrong. A correct-looking last number hides the bug, which is why every output must be checked (computed in Python).
5. `use` took the `unique_ptr` by value, and `std::move(frame)` transferred ownership into `f`, which is destroyed at the end of `use`; afterwards `frame` is null, and `frame->id` is a null dereference. GDB: `bt` (shows `main () at segv.cpp:11`) and `info locals` (shows `frame = ... {get() = 0x0}`). Fix: read `frame->id` before the move, or have `use` take `const Frame&` so ownership stays in `main`.
6. For instance: `Test{"moving_average window 2", [](Checker& c){ auto m = moving_average({1,2,3,4,5}, 2); c.check(m.size() == 4, "size"); c.check_near(m[0], 1.5, 1e-12, "m[0]"); ... }}`. On the buggy code `m[0]` is 3, so the test fails without a sanitizer. A value assertion states what correct means and fails deterministically; relying on a crash fails only when the undefined behavior happens to crash, and says nothing about wrong-but-silent results.
7. A good table: `wrap_to_pi(0)=0`; `wrap_to_pi(pi)=-3.14159` (upper end excluded); `wrap_to_pi(-pi)=-3.14159`; `wrap_to_pi(1.5*pi)=-1.5708`; `wrap_to_pi(2*pi)=0` (tolerance); `wrap_to_pi(7)=0.71681`; `wrap_to_pi(-7)=-0.71681`; `wrap_to_pi(1e6)` equals the direct computation with an independent oracle (precision loss for huge angles is expected); `wrap_to_pi(NAN)` is NaN (must not loop forever). Tolerance about $10^{-9}$.
8. $n\ge\ln0.05/\ln0.98=148.3$, so 149 runs. Causes and techniques: data races (ThreadSanitizer); timing/sleeps (use a fake clock or condition variables instead of `sleep`); uninitialized memory (Valgrind/MSan, `-ftrivial-auto-var-init=zero` to expose it); unseeded or time-seeded randomness (log and fix seeds); ordering of unordered containers (sort before comparing); resource leaks across tests (run each test in a fresh process).
9. The result is `[17, 42]` with 22 calls of `fails` for `range(64)` when you start at chunk 32 and halve down to 1 (the exact count depends on the strategy). A good answer shows that starting with chunk 32 removes 32 elements at a time (kept only if the bug persists), then halves down to 1, and that the result is "1-minimal": removing any single remaining element makes the bug disappear.
10. A good answer: job 1 Debug (`-O1 -g`) with `-fsanitize=address,undefined` running all tests (catches 1(a), 1(b), 1(c), 1(e)); job 2 Release with warnings as errors (`-Wall -Wextra -Werror`) and the same tests (catches optimization-dependent UB); job 3 ThreadSanitizer for the concurrency tests only (1(d), the race in exercise 8), separate because TSan and ASan instrument memory differently and cannot be combined; optionally a nightly Valgrind or MSan job for 1(f). Each job should upload the first sanitizer report as an artifact.
11. A good answer has a table with: ASan (first 4 lines: heap-buffer-overflow, READ of size 8, `buggy.cpp:10`, 0 bytes to the right of a 40-byte region), Valgrind (`Invalid read of size 8`, address 0 bytes after a block of size 40), GDB for the `segv.cpp` variant (`bt`, `get() = 0x0`); the reduced input (one element, window 1); a regression test that fails on the old code; and a final run with no sanitizer output.
12. (a) The first word's shadow address is $(\texttt{0x504000000010}\gg3)+\texttt{0x7fff8000}=\texttt{0xa087fff8002}$, the second word's is `0xa087fff8003`, the third's `0xa087fff8004` (computed in Python). Shadow values: $0$, $0$ and $5$, since $21=8+8+5$. (b) Slow path on the third word (shadow $5$): $\ell=(a\bmod8)+s-1$, error iff $\ell\ge5$. Offset 16, size 4: $\ell=0+3=3<5$, silent. Offset 17, size 4: $\ell=1+3=4<5$, silent. Offset 18, size 4: $\ell=2+3=5\ge5$, reported. Offset 20, size 4: $\ell=4+3=7\ge5$, reported. Offset 16, size 8: $\ell=7\ge5$, reported. A real run (gcc 11.4, `-fsanitize=address`) was silent for offsets 16 and 17 and reported `READ of size 4` for 18 and 20 and `READ of size 8` for 16. (c) Offset 20, size 1: $\ell=4+0=4<5$, silent. Offset 21, size 1: $\ell=5+0=5\ge5$, reported ("0 bytes to the right of 21-byte region"); both confirmed by a real run. (d) A one-bit-per-word scheme must treat the partly valid third word as valid (then the reads at offsets 18 and 20 and the byte at 21 are missed) or as invalid (then the valid reads at 16 and 17 give false alarms). The 8-to-1 mapping with values $0..7$ is what makes byte-exact tails possible.
13. The first read is *not* reported and the second is. `p[72]` lands in the right redzone of `p`: its shadow is a negative poison code, so the check fires ("0 bytes to the right of 72-byte region"). `p[d]` with $d=q-p$ is exactly the first byte of `q`; its shadow byte is $0$ (addressable), so the fast path accepts it: ASan checks the target byte, not whether the pointer's provenance is `p`. Expected $d$: the block plus the poisoned padding between consecutive allocations, so at least $72+$redzone; measured $d=112$ (40 bytes of redzone and allocator bookkeeping), and the read returned `q[0]` (9 in the run where `q` was filled with 9). Fixes: (1) larger redzones, which make a jump of a given size land in poison but cost memory per allocation and still do not stop an arbitrary index; (2) bounds-checked access in the code (`std::vector::at`, a checked span, or an explicit index check), which catches the bug independent of memory layout at the price of a branch per access; a third option is a bounds sanitizer such as `-fsanitize=bounds` for statically sized arrays, which does not help for heap arrays of dynamic size.
14. (a) `slot[6]` is the next int in the struct, i.e. `head`; after the loop `head` is $12$ (the last value written, $2i$ with $i=6$), and a run printed `head=12`. ASan reports nothing: the write lands in a valid, addressable word of the same global object, with no redzone between members. (b) `-fsanitize=bounds` (included in `-fsanitize=undefined`) reports `index 6 out of bounds for type 'int [6]'`, because the array bound is known statically (checked at `ring.cpp:4`). (c) `watch -l r.head` (or `watch -location r.head`) after `break main` and `run`, then `continue`: GDB stops with `Old value = 250`, `New value = 12` in `fill (n=6)` at the loop line, and `bt` shows `main` as the caller (checked with GDB). A software watchpoint single-steps and compares after every instruction, which the manual describes as hundreds of times slower than normal execution, so minutes become hours; hardware watchpoints avoid that cost.
15. (a) Errors can only occur at steps that test a bad commit, and at such a step the test wrongly says "good" with probability $(1-p)^r$ (all $r$ runs pass). With at most $k$ such steps, the probability that none errs is at least $\bigl(1-(1-p)^r\bigr)^k$. (b) Here $k=\lceil\log_2 4000\rceil=12$. Require $\bigl(1-0.65^{r}\bigr)^{12}\ge0.95$, i.e. $0.65^r\le1-0.95^{1/12}=0.004265$, so $r\ge\ln0.004265/\ln0.65=12.67$, so $r=13$ (computed: $(1-0.65^{13})^{12}=0.9565$; $r=12$ gives $0.9338<0.95$). Worst case $k\,r=12\cdot13=156$ runs, versus 12 for a deterministic test. (c) With $r=1$ the bound is $(1-0.65)^{12}=0.35^{12}=3.4\times10^{-6}$, essentially no guarantee: a single passing run of a bad commit is the common case. (d) Raise $p$: stress the test (loop it, add threads or sleeps, fix and vary seeds, use a TSan/ASan build) until it fails nearly always. Shorten the search: use `git bisect skip` for untestable commits, or narrow the range first with a cheaper deterministic indicator (a compile error, a changed file list).

## Further reading

- [AddressSanitizer (Google Sanitizers wiki)](https://github.com/google/sanitizers/wiki/AddressSanitizer) - what it detects, how to read reports, and its overhead.
- [GCC: Program Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) - every `-fsanitize=` option, and which can be combined.
- [GDB documentation](https://sourceware.org/gdb/documentation/) - the manual for breakpoints, stack inspection and watchpoints.
- [AddressSanitizerAlgorithm (Google Sanitizers wiki)](https://github.com/google/sanitizers/wiki/AddressSanitizerAlgorithm) - shadow memory, the mapping and the instrumented access check.
- [GDB manual: Setting Watchpoints](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Set-Watchpoints.html) - `watch`, `rwatch`, `awatch`, `-location`, hardware versus software watchpoints.
- [Clang: UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) - the list of `-fsanitize=` checks, including `bounds`.
- [git-bisect documentation](https://git-scm.com/docs/git-bisect) - the bisect procedure, step estimates and `skip`.

**More practice:** the [Pro Git chapter on debugging with Git](https://git-scm.com/book/en/v2/Git-Tools-Debugging-with-Git) (bisect and blame), the [UndefinedBehaviorSanitizer manual](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) and [AddressSanitizer manual](https://clang.llvm.org/docs/AddressSanitizer.html) (trigger each listed check deliberately and read the report), the [Valgrind quick start](https://valgrind.org/docs/manual/quick-start.html), the [GDB sample session](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Sample-Session.html), and the [GoogleTest primer](https://google.github.io/googletest/primer.html).