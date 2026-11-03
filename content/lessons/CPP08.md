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

![Debugging loop from failing run to reproducer to sanitizer or debugger to fix and regression test, with the bug classes each tool catches](/lesson-figures/CPP08.svg)

*Reproduce, reduce, locate with a tool, fix, then add a regression test and re-run under the sanitizers.*

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

### Debugger essentials

`gdb ./prog`, then `run`, `bt` (backtrace), `frame N`, `info locals`, `print expr`, `break file:line`, `watch var`, `continue`, `next`, `step`. Batch mode: `gdb -batch -ex run -ex bt ./prog`. For a crash inside a library, `bt` still shows your calling frame. A moved-from `std::unique_ptr` prints as `get() = 0x0` in GDB, which immediately explains a segmentation fault at that dereference.

### Test harnesses and regression tests

A test is an executable claim: *given input X, the result is Y*. A harness gives it structure: named tests, independent state, failure messages that show expected and actual values, a summary and a non-zero exit code on failure so that CI notices. Good tests

- use hand-computed expected values (not the function under test, which would only prove it equals itself);
- cover boundaries (empty, one element, window equals length, zero), typical cases and error cases;
- check invariants and properties (window 1 is the identity; the result length is $n-w+1$);
- are deterministic (fixed seeds, fixed clocks) and independent of each other.

A **regression test** captures a bug that was found: it fails on the broken code and passes on the fixed code. Writing it *before* fixing proves that it detects the bug.

For floating-point comparisons use a tolerance: `|a - b| <= tol` is false when either value is NaN, which is the safe way round; `!(|a-b| > tol)` would accept NaN.

### Reduction and bisection

If a failure needs $N$ items and a single culprit, halving the input finds it in $\lceil\log_2 N\rceil$ runs. When the failure needs several items, delta debugging removes chunks and keeps any removal that still fails. For history, `git bisect` binary-searches commits: 1000 commits need at most $\lceil\log_2 1000\rceil=10$ builds. For rare failures, the number of repetitions needed to see a failure of probability $p$ with confidence $1-\alpha$ is $n\ge\ln\alpha/\ln(1-p)$.

## Worked example

**The bug.** `moving_average` should return one mean per full window. Run without sanitizers:

```
$ g++ -std=c++17 -g buggy.cpp -o buggy && ./buggy
3 4.5 6 4.5
```
The expected output for `{1,2,3,4,5}` with window 2 is `1.5 2.5 3.5 4.5`. The numbers are wrong, but nothing crashed.

1. **Hypothesis from the numbers**: the first value 3 equals $(1+2+3)/2$: three elements were summed but divided by 2. The loop has one iteration too many.
2. **Confirm with ASan**: `g++ -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer buggy.cpp && ./a.out` reports `heap-buffer-overflow`, `READ of size 8`, `buggy.cpp:10`, and "0 bytes to the right of 40-byte region": the vector holds 5 doubles, and the last window read index 5. For the last window, $i=3$, $k=2$ gives index $3+2=5$, which is out of range. The earlier outputs were wrong too, but only this read is a memory error.
3. **Reduce**: with `{1,2,3}` and window 2, the output should be `1.5 2.5` and ASan still fires at the second window (index $1+2=3$). Smaller still: `{1,2}` and window 1 should give `1 2`; the program prints `3` and then `2` plus whatever sits at index 2 (every window reads one element too many). The minimal reproducer is a single element and window 1: the only window reads index 1 of a 1-element vector.
4. **Fix**: change `k <= w` to `k < w`.
5. **Regression test** (hand-computed): `moving_average({1,2,3,4,5}, 2)` equals `{1.5, 2.5, 3.5, 4.5}`; window 1 returns the input; window 5 returns `{3}`; window 6 and 0 return empty.
6. **Confirm**: the test fails on the old code (first value 3 not 1.5, with or without the sanitizer) and passes on the new code under ASan and UBSan, with no report.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: AddressSanitizer wiki, list of detected errors)* Match each bug to the best tool: (a) writing one element past a heap array; (b) reading a vector element after `push_back` reallocated it; (c) `int` addition overflowing; (d) two threads incrementing a plain `int`; (e) a `new` that is never deleted; (f) reading a local `double` before it was assigned.
2. **(Easy)** Read this report excerpt and state the bug class, the access size, the source line, the allocation size and the likely off-by-how-many error: `heap-buffer-overflow ... READ of size 8 ... in moving_average buggy.cpp:10 ... 0x...38 is located 0 bytes to the right of 40-byte region`.
3. **(Easy)** *(Adapted from: Pro Git, Debugging with Git - binary search)* A regression appeared somewhere in 1000 commits. How many builds does `git bisect` need at most? How many would a linear search over commits need in the worst case?
4. **(Medium)** Explain why the unsanitized program printed `3 4.5 6 4.5` and still "worked". Derive by hand the four numbers the buggy loop computes (treat the out-of-range read as 0) and show why the last number happens to equal the correct one.
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
2. Bug class heap-buffer-overflow; a read of size 8 (one `double`); source line 10 of `buggy.cpp`; the allocation is 40 bytes, i.e. five doubles; the address is *0 bytes to the right* of the region, so the read was exactly one element past the end: an off-by-one (index 5 of 5).
3. At most $\lceil\log_2 1000\rceil=10$ builds; linear search needs up to 1000 (or 999).
4. Undefined behavior has no obligation to fail: the read one past the vector's buffer returned whatever was in that memory (allocator padding, often 0), so the code ran to completion. The buggy loop sums $w+1=3$ elements and divides by $w=2$: $(1+2+3)/2=3$, $(2+3+4)/2=4.5$, $(3+4+5)/2=6$, and for the last window $(4+5+v[5])/2$; with the garbage value 0 it is $4.5$, which coincidentally equals the correct $4.5$ for that window. A correct-looking last number hides the bug, which is why you must check all outputs.
5. `use` took the `unique_ptr` by value, and `std::move(frame)` transferred ownership into `f`, which is destroyed at the end of `use`; afterwards `frame` is null, and `frame->id` is a null dereference. GDB: `bt` (shows `main () at segv.cpp:11`) and `info locals` (shows `frame = ... {get() = 0x0}`). Fix: read `frame->id` before the move, or have `use` take `const Frame&` so ownership stays in `main`.
6. For instance: `Test{"moving_average window 2", [](Checker& c){ auto m = moving_average({1,2,3,4,5}, 2); c.check(m.size() == 4, "size"); c.check_near(m[0], 1.5, 1e-12, "m[0]"); ... }}`. On the buggy code `m[0]` is 3, so the test fails without a sanitizer. A value assertion states what correct means and fails deterministically; relying on a crash fails only when the undefined behavior happens to crash, and says nothing about wrong-but-silent results.
7. A good table: `wrap_to_pi(0)=0`; `wrap_to_pi(pi)=-3.14159` (upper end excluded); `wrap_to_pi(-pi)=-3.14159`; `wrap_to_pi(1.5*pi)=-1.5708`; `wrap_to_pi(2*pi)=0` (tolerance); `wrap_to_pi(7)=0.71681`; `wrap_to_pi(-7)=-0.71681`; `wrap_to_pi(1e6)` equals the direct computation with an independent oracle (precision loss for huge angles is expected); `wrap_to_pi(NAN)` is NaN (must not loop forever). Tolerance about $10^{-9}$.
8. $n\ge\ln0.05/\ln0.98=148.3$, so 149 runs. Causes and techniques: data races (ThreadSanitizer); timing/sleeps (use a fake clock or condition variables instead of `sleep`); uninitialized memory (Valgrind/MSan, `-ftrivial-auto-var-init=zero` to expose it); unseeded or time-seeded randomness (log and fix seeds); ordering of unordered containers (sort before comparing); resource leaks across tests (run each test in a fresh process).
9. The result is `[17, 42]` with 22 calls of `fails` for `range(64)` when you start at chunk 32 and halve down to 1 (the exact count depends on the strategy). A good answer shows that starting with chunk 32 removes 32 elements at a time (kept only if the bug persists), then halves down to 1, and that the result is "1-minimal": removing any single remaining element makes the bug disappear.
10. A good answer: job 1 Debug (`-O1 -g`) with `-fsanitize=address,undefined` running all tests (catches 1(a), 1(b), 1(c), 1(e)); job 2 Release with warnings as errors (`-Wall -Wextra -Werror`) and the same tests (catches optimization-dependent UB); job 3 ThreadSanitizer for the concurrency tests only (1(d), the race in exercise 8), separate because TSan and ASan instrument memory differently and cannot be combined; optionally a nightly Valgrind or MSan job for 1(f). Each job should upload the first sanitizer report as an artifact.
11. A good answer has a table with: ASan (first 4 lines: heap-buffer-overflow, READ of size 8, `buggy.cpp:10`, 0 bytes to the right of a 40-byte region), Valgrind (`Invalid read of size 8`, address 0 bytes after a block of size 40), GDB for the `segv.cpp` variant (`bt`, `get() = 0x0`); the reduced input (one element, window 1); a regression test that fails on the old code; and a final run with no sanitizer output.

## Further reading

- [AddressSanitizer (Google Sanitizers wiki)](https://github.com/google/sanitizers/wiki/AddressSanitizer) - what it detects, how to read reports, and its overhead.
- [GCC: Program Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) - every `-fsanitize=` option, and which can be combined.
- [GDB documentation](https://sourceware.org/gdb/documentation/) - the manual for breakpoints, stack inspection and watchpoints.

**More practice:** the [Pro Git chapter on debugging with Git](https://git-scm.com/book/en/v2/Git-Tools-Debugging-with-Git) (bisect and blame), the [UndefinedBehaviorSanitizer manual](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) and [AddressSanitizer manual](https://clang.llvm.org/docs/AddressSanitizer.html) (trigger each listed check deliberately and read the report), the [Valgrind quick start](https://valgrind.org/docs/manual/quick-start.html), the [GDB sample session](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Sample-Session.html), and the [GoogleTest primer](https://google.github.io/googletest/primer.html).