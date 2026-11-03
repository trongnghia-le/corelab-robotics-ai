---
{
  "id": "cpp01-foundations",
  "module_id": "CPP01",
  "title": "C++ fundamentals: types, scope, and predictable values",
  "summary": "Write a small compiled program and understand its arithmetic.",
  "estimated_minutes": 310,
  "prerequisites": [],
  "source_refs": [
    {
      "title": "LearnCpp",
      "url": "https://www.learncpp.com/"
    }
  ],
  "objectives": [
    "Compile and run a C++17 program.",
    "Predict integer and floating-point arithmetic.",
    "Use vectors and const references safely."
  ],
  "core_theory": [
    "C++ fundamentals: types, scope, and predictable values"
  ],
  "labs": [
    "Create main.cpp, compile it with the command above, and add singleton, mixed-sign, and empty-input cases. Predict each result before execution. Change one operand in a division from int to double and explain the result."
  ],
  "assessment_refs": [
    "CPP01-diagnostic-v1"
  ],
  "review_prompts": [
    "Compute a moving average for sampled motor velocity. State your numeric type, input contract, boundary behavior, and one test that catches integer truncation."
  ],
  "extension_refs": [
    "https://www.learncpp.com/"
  ]
}
---

## Why this matters

Write a small compiled program and understand its arithmetic. This lesson develops the core calculation before asking you to apply it in a new setting. Start with the diagnostic if you think you already know it; prior tool use is not evidence of understanding.

## Intuition

C++ makes representation and lifetime visible. A type tells the compiler which operations are valid, but also controls arithmetic and memory layout. Compilation catches some mistakes before execution; tests must catch incorrect behavior that is still legal C++.

![A stack-like memory diagram: a double vector with size 3 and valid indices 0 to 2, plus integer versus floating division of 5 by 2.](/lesson-figures/CPP01.svg)

*Types decide arithmetic: integer 5/2 truncates to 2 while 5.0/2 keeps 2.5; valid vector indices stop at size minus one.*

## Theory and derivation

A variable declaration introduces a typed object: `int count{3};` stores an integer, while `double dt{0.01};` stores an approximate real value. Initialize every local scalar before reading it. Integer division truncates toward zero: `5/2` is 2, whereas `5.0/2` is 2.5. Converting the truncated result to double afterward does not recover the lost fraction.

Functions declare a return type and typed parameters. Passing a vector by value copies it; `const std::vector<double>&` lets a function inspect the existing vector without mutation. The referenced object must remain alive during the call. Local scope determines where names are visible and when ordinary automatic objects are destroyed.

Use `std::vector` for a runtime-sized sequence. Its `size()` is a count, while valid indices run from zero through size minus one. `operator[]` does not check bounds; `.at()` does. Prefer range-based loops when the index has no separate meaning. Compile with warnings enabled and treat a warning as a question to resolve, not decoration.

## Worked example

If int steps=5 and total=2, `double ratio=steps/total;` produces 2.0 because division happened as integers. `double ratio=static_cast<double>(steps)/total;` produces 2.5. For an empty vector, a mean function must reject input before division.

## Exercises

1. **(Easy)** An encoder reports `int ticks = 7;` in `int rev = 2;` revolutions. Predict the value of `double a = ticks / rev;` and of `double b = static_cast<double>(ticks) / rev;`. Where exactly was the fraction lost in `a`? *(Adapted from: LearnCpp, the chapter on arithmetic operators and integer division)*
2. **(Easy)** A control loop contains `double dt = 1 / 100;` intended as a 100 Hz period. What value does `dt` get, what does the controller then do, and what are two ways to write it correctly? *(Adapted from: C++ Core Guidelines, ES.20 and ES.46 on initialisation and narrowing)*
3. **(Medium)** **Find the bug.** This prints a vector backwards:
   ```cpp
   void print_reversed(const std::vector<double>& v) {
       for (std::size_t i = v.size() - 1; i >= 0; --i)
           std::cout << v[i] << ' ';
   }
   ```
   Explain two separate failures (non-empty and empty input) and give a correct loop. *(Adapted from: C++ Core Guidelines, ES.100 on mixing signed and unsigned)*
4. **(Medium)** **Predict the output** (reason about each statement before compiling):
   ```cpp
   std::vector<int> v{4, 8, 15};
   std::cout << v.size() - 1 << ' ';
   try { std::cout << v.at(3); }
   catch (const std::out_of_range&) { std::cout << "caught"; }
   ```
   What would `v[3]` have done instead, and why is that worse for a robot?
5. **(Medium)** A perception node passes a point cloud (`std::vector<double>` of $10^6$ elements) to a filter at 30 Hz. Estimate the memory traffic caused by passing it by value versus by `const&`. Give a signature that avoids the copy and prevents modification.
6. **(Medium)** A student writes `double s = 0; for (int i = 0; i < 10; ++i) s += 0.1; if (s == 1.0) arm_motor();`. Predict whether the motor arms, give the approximate error $1-s$, and write a safe comparison. Explain why `double` still beats `float` here.
7. **(Hard)** **Find the bug.** A moving average of window `w` over `x`:
   ```cpp
   std::vector<double> y;
   for (std::size_t i = 0; i + w < x.size(); ++i) {
       double s = 0;
       for (std::size_t j = i; j < i + w; ++j) s += x[j];
       y.push_back(s / w);
   }
   ```
   For `x = {1,2,3,4}`, `w = 2` list what it returns and what it should return. State the fix and two further inputs the function must reject.
8. **(Hard)** You smooth a motor velocity measured at 1 kHz with an 11-sample moving average. Specify the function contract (types, preconditions, output length, what the first outputs mean). Compute the delay the filter adds for a ramp input, and say when that delay is unacceptable inside a control loop.
9. **(Hard)** **Derivation.** Show that the streaming update $y_{k+1}=y_k+(x_{k+w}-x_k)/w$ equals recomputing the window sum. Then explain why repeated use over millions of samples can drift in floating point, and suggest a remedy.
10. **(Project)** Write `stats.hpp`/`main.cpp` with `mean`, `variance` and `moving_average`, a test `main` that checks hand-computed cases and error paths, compile with `-std=c++17 -Wall -Wextra -Wpedantic`, then rebuild with `-fsanitize=address,undefined -g` and report the output of both builds.

## Reference implementation

Read the contract first. Predict the output before running the code locally. This reference is for studying; a submission copied from it is assisted practice, not independent evidence.

```cpp
#include <vector>
#include <stdexcept>
#include <cassert>
double mean(const std::vector<double>& x) {
    if (x.empty()) throw std::invalid_argument("empty");
    double sum{0.0};
    for (double v : x) sum += v;
    return sum / static_cast<double>(x.size());
}
int main() { assert(mean({2.,4.,6.}) == 4.); }
// g++ -std=c++17 -Wall -Wextra -Wpedantic main.cpp -o demo
```

## Independent practice

### Goal
Write a small, tested numeric library in C++17: mean, variance, a moving average with a strict contract, and a division that cannot silently truncate. See each error path fire and each invariant hold.

### Setup
A C++17 compiler (`g++` or `clang++`). Save the starter and the tests together as `lab.cpp`, then compile with `g++ -std=c++17 -Wall -Wextra -Wpedantic lab.cpp -o lab && ./lab`. Later, rebuild with `-fsanitize=address,undefined -g`.

### Tasks
1. Implement `mean` and `safe_ratio`. Predict by hand what `safe_ratio(5, 2)` returns and why `5 / 2` alone would not.
2. Implement `variance` using `mean` (two passes). Compute `{2, 4, 6}` by hand first.
3. Implement `moving_average` with the exact output length $n-w+1$ and the two precondition checks.
4. Compile with warnings on. Fix every warning (typically signed/unsigned) rather than silencing it.
5. Rebuild with the sanitizers, then temporarily change one loop bound to `<` instead of `<=` and see which test catches it.

### Starter code
```cpp
#include <cassert>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <stdexcept>
#include <vector>

// Mean of x. Throw std::invalid_argument if x is empty.
double mean(const std::vector<double>& x) { throw std::logic_error("not implemented"); }

// Population variance (divide by n) using mean(); throw on empty input.
double variance(const std::vector<double>& x) { throw std::logic_error("not implemented"); }

// Window means: output length n-w+1, y[k] = mean of x[k..k+w-1].
// Throw std::invalid_argument if w == 0 or w > x.size().
std::vector<double> moving_average(const std::vector<double>& x, std::size_t w) { throw std::logic_error("not implemented"); }

// Return a/b as a double (no truncation). Throw std::domain_error if b == 0.
double safe_ratio(int a, int b) { throw std::logic_error("not implemented"); }
```

### Tests
Paste this below the starter code (same file) and run it. Every check is a plain `assert`; the first failure stops the run.

```cpp
static bool near(double a, double b) { return std::abs(a - b) < 1e-12; }
template <class E, class F> static bool throws(F f) { try { f(); } catch (const E&) { return true; } catch (...) { return false; } return false; }

int main() {
    // hand-computed cases
    assert(near(mean({2., 4., 6.}), 4.));
    assert(near(mean({-3., 3.}), 0.));
    assert(near(mean({5.}), 5.));                       // singleton
    assert(near(variance({2., 4., 6.}), 8. / 3.));      // (4+0+4)/3
    assert(near(safe_ratio(5, 2), 2.5));
    auto y = moving_average({1, 2, 3, 4}, 2);
    assert(y.size() == 3 && near(y[0], 1.5) && near(y[1], 2.5) && near(y[2], 3.5));
    // error paths
    assert(throws<std::invalid_argument>([] { mean({}); }));
    assert(throws<std::invalid_argument>([] { moving_average({1, 2}, 0); }));
    assert(throws<std::invalid_argument>([] { moving_average({1, 2}, 3); }));
    assert(throws<std::domain_error>([] { safe_ratio(1, 0); }));
    // invariants: w == 1 returns the input; w == n returns the mean; shift invariance of variance
    std::vector<double> x{3, -1, 4, 1, -5, 9};
    auto id = moving_average(x, 1);
    for (std::size_t i = 0; i < x.size(); ++i) assert(near(id[i], x[i]));
    auto full = moving_average(x, x.size());
    assert(full.size() == 1 && near(full[0], mean(x)));
    std::vector<double> shifted;
    for (double v : x) shifted.push_back(v + 100.0);
    assert(std::abs(variance(shifted) - variance(x)) < 1e-9);
    std::cout << "mean = " << mean(x) << ", variance = " << variance(x) << ", ma size = " << moving_average(x, 3).size() << "\n";
    std::cout << "all tests passed\n";
}
```

### Expected output
A correct solution prints the following; a failed `assert` aborts with the file and line.

```text
mean = 1.83333, variance = 18.8056, ma size = 4
all tests passed
```

### Extension challenge
Add `class MovingAverage` with `double push(double v)` that keeps a ring buffer and a running sum in O(1) per sample, and test that it agrees with `moving_average` on random data to 1e-9. Explain how you would stop floating-point drift.

### Library track
Redo the lab with the C++17 standard library instead of hand-written loops: `std::accumulate` for the mean, `std::transform_reduce` for the variance, and `std::partial_sum` (prefix sums) for the moving average, where $y_k=(P_{k+w}-P_k)/w$. Compile with `g++ -std=c++17 -Wall -Wextra -Wpedantic lib.cpp -o lib && ./lib`. Then run your lab tests against these versions: they must agree to $10^{-12}$.

```cpp
#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <vector>

double mean_std(const std::vector<double>& x) {
    if (x.empty()) throw std::invalid_argument("empty");
    return std::accumulate(x.begin(), x.end(), 0.0) / static_cast<double>(x.size());
}
double variance_std(const std::vector<double>& x) {
    const double m = mean_std(x);
    return std::transform_reduce(x.begin(), x.end(), 0.0, std::plus<>{},
                                 [m](double v) { return (v - m) * (v - m); }) / static_cast<double>(x.size());
}
// Moving average through prefix sums: y[k] = (P[k+w] - P[k]) / w
std::vector<double> moving_average_std(const std::vector<double>& x, std::size_t w) {
    if (w == 0 || w > x.size()) throw std::invalid_argument("window");
    std::vector<double> p(x.size() + 1, 0.0);
    std::partial_sum(x.begin(), x.end(), p.begin() + 1);
    std::vector<double> y(x.size() - w + 1);
    for (std::size_t k = 0; k < y.size(); ++k) y[k] = (p[k + w] - p[k]) / static_cast<double>(w);
    return y;
}

int main() {
    std::vector<double> x{3, -1, 4, 1, -5, 9};
    assert(std::abs(mean_std(x) - 11.0 / 6.0) < 1e-12);
    const auto y = moving_average_std(x, 3);
    const std::vector<double> want{2.0, 4.0 / 3.0, 0.0, 5.0 / 3.0};
    assert(y.size() == want.size() && std::equal(y.begin(), y.end(), want.begin(),
           [](double a, double b) { return std::abs(a - b) < 1e-12; }));
    std::cout << "variance = " << variance_std(x) << "\n";   // matches the hand-written lab
    std::cout << "library track ok\n";
}
```

Expected output: `variance = 18.8056` then `library track ok`. Note that `std::accumulate(x.begin(), x.end(), 0)` with an `int` initial value would silently truncate every partial sum; the `0.0` matters.

## Verification

Check the worked numerical example independently, then test a boundary case and an invariant from the derivation. Keep the expected result separate from the implementation. Change a sign or remove one term deliberately: your tests should reject that broken version. Use the diagnostic to check concepts and numerical reasoning; short answers remain rubric-guided practice.

## Failure modes

An uninitialized local integer has no valid predictable value to rely on. An out-of-range vector access is not a safe way to detect the end of data. A reference does not extend an arbitrary object lifetime.

## Alternatives and trade-offs

Python is convenient for rapid inspection; C++ offers explicit types and control over resources. Start with standard containers and clear ownership before optimizing or introducing raw pointers.

## Transfer and retention

Compute a moving average for sampled motor velocity. State your numeric type, input contract, boundary behavior, and one test that catches integer truncation.

Close the reference before trying. Explain your assumptions and one way your answer could fail. Return after at least a week and reconstruct the key argument from a blank page. A quiz alone does not verify unfamiliar transfer or research-level competence.

## Exercise answers

1. `a` is `3` (printed as 3) because `ticks / rev` is evaluated as `int / int` (truncation) before the result is converted; `b` is `3.5`. The fraction is lost at the division, not at the assignment.
2. `1 / 100` is integer division, so `dt` is `0`. A controller with `dt = 0` never integrates (or divides by zero in a derivative). Write `1.0 / 100` or `0.01` (or `constexpr double dt{1.0/100.0};`).
3. `size_t` is unsigned, so `i >= 0` is always true: after `i == 0` the decrement wraps to a huge value and `v[i]` reads out of bounds (undefined behaviour). For an empty vector `v.size() - 1` already wraps to a huge value. Correct: `for (std::size_t i = v.size(); i-- > 0; ) std::cout << v[i] << ' ';`
4. `v.size() - 1` is `2`; `v.at(3)` throws `std::out_of_range`, so the output is `2 caught`. `v[3]` is unchecked undefined behaviour: it can read garbage, crash later, or appear to work, which is worse for a robot than a clean exception.
5. By value: $10^6\times8$ B $=8$ MB copied per call; at 30 Hz about $240$ MB/s of extra traffic plus an allocation each time. By reference: no copy. Signature `void filter(const std::vector<double>& cloud);`.
6. The sum is $0.9999999999999999$, so `s == 1.0` is false and the motor does not arm; $1-s\approx1.1\times10^{-16}$. Use `std::abs(s - 1.0) < 1e-9`. `double` has about 16 digits against about 7 for `float`, so accumulated rounding error is much smaller.
7. It returns 2 values `{1.5, 2.5}`; it should return 3 values `{1.5, 2.5, 3.5}`. The loop condition should be `i + w <= x.size()`. Also reject `w == 0` (division by zero) and `w > x.size()` (no complete window; `i + w` would never be valid).
8. Contract: `x` is a vector of finite doubles, `1 <= w <= x.size()`, output length `x.size() - w + 1`, element `k` is the mean of `x[k..k+w-1]` (so there are no outputs for the first `w-1` start-up samples). For a ramp the average lags by $(w-1)/2=5$ samples $=5$ ms at 1 kHz. It is unacceptable when the loop's phase margin or latency budget is tighter than that, or when a derivative of the filtered value is used.
9. Window sum $S_{k+1}=S_k-x_k+x_{k+w}$ because the windows differ only by dropping $x_k$ and adding $x_{k+w}$; dividing by $w$ gives the update. Each update adds a rounding error that is never corrected, so the error random-walks. Remedies: recompute the sum from scratch every N steps, use Kahan/compensated summation, or integer accumulators for integer sensor counts.
10. A good answer shows both builds printing the same test results, includes error-path tests (empty, `w == 0`, `w > n`), reports that sanitizers produced no diagnostics for those executed paths, and states that a clean run is not proof of correctness.

## Further reading

[LearnCpp](https://www.learncpp.com/) — primary course, documentation, or the supplied reference collection. Follow the relevant subject heading; these are further reading links, not reproduced book chapters.

**More practice:** [LearnCpp chapter 4 quiz](https://www.learncpp.com/cpp-tutorial/chapter-4-summary-and-quiz/) (fundamental types and integer division), [LearnCpp chapter 12 quiz](https://www.learncpp.com/cpp-tutorial/chapter-12-summary-and-quiz/) (compound types and references), [LearnCpp on the std::vector unsigned subscript problem](https://www.learncpp.com/cpp-tutorial/stdvector-and-the-unsigned-length-and-subscript-problem/), and the [Exercism C++ track](https://exercism.org/tracks/cpp/exercises).
