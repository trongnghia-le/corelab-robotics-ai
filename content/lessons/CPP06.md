---
{
  "id": "cpp06-foundations",
  "module_id": "CPP06",
  "title": "Modern C++: templates, constexpr, and idioms",
  "summary": "Write generic code with stated assumptions, move work to compile time with constexpr, and use C++17 idioms that make intent checkable.",
  "estimated_minutes": 390,
  "prerequisites": [
    "CPP03",
    "CPP05"
  ],
  "source_refs": [
    {
      "title": "cppreference: Templates",
      "url": "https://en.cppreference.com/w/cpp/language/templates"
    },
    {
      "title": "cppreference: constexpr specifier",
      "url": "https://en.cppreference.com/w/cpp/language/constexpr"
    },
    {
      "title": "C++ Core Guidelines: T. Templates and generic programming",
      "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"
    }
  ],
  "objectives": [
    "Write function and class templates and explain deduction, instantiation and why templates live in headers.",
    "State and enforce the assumptions of generic code with static_assert and if constexpr.",
    "Use constexpr to compute and check values at compile time, and distinguish it from const.",
    "Apply auto, structured bindings, optional and range-for without losing type clarity."
  ],
  "core_theory": [
    "templates",
    "constexpr",
    "modern idioms"
  ],
  "labs": [
    "Implement constrained generic numerical utilities (clamp, deg2rad, a compile-time table, Welford statistics, a container mean) and verify them with compile-time and run-time checks."
  ],
  "assessment_refs": [
    "CPP06-diagnostic-v1"
  ],
  "review_prompts": [
    "A teammate writes mean(const std::vector<std::string>&) by accident and gets a 40-line compiler error. Show how to turn that into a one-line message and explain what a C++20 concept would add."
  ],
  "extension_refs": [
    "https://en.cppreference.com/w/cpp/language/templates",
    "https://en.cppreference.com/w/cpp/language/constexpr"
  ]
}
---

## Why this matters

Robotics libraries are generic by necessity: Eigen matrices over `float` or `double`, `std::vector` of any message type, filters that work for 2D and 3D states, unit-safe wrappers that cost nothing at run time. Templates let you write an algorithm once and get a specialized, inlined version for each type, with no virtual calls. `constexpr` lets the compiler evaluate calibration tables, unit conversions and size computations before the program runs, and turns many bugs into compile errors. The cost of this power is error messages and hidden assumptions: a template that silently assumes "T is a floating-point type" will produce a wrong answer, or a page of errors, when someone instantiates it with `int`. The modern C++ habit is to state and check each assumption where it is made, as the Core Guidelines put it: make interfaces precisely and strongly typed.

## Intuition

A template is a *stencil*, not a function: nothing exists until you use it with concrete types. When you call `clamp_to(5, 0, 3)` the compiler deduces `T = int`, stamps out a real function `clamp_to<int>`, and compiles that. A call with `double` stamps out another one. Each version is as fast as hand-written code, but the code size grows with the number of distinct types.

`constexpr` means "may be evaluated at compile time". If every argument is a constant, the compiler computes the result while compiling and can place it into the binary, or use it where a constant is required (array sizes, `static_assert`, template arguments). If an argument is a run-time value, the same function simply runs normally.

![Template instantiation and constexpr evaluation: one stencil producing int and double functions, and compile time versus run time evaluation](/lesson-figures/CPP06.svg)

*One template stencil yields one real function per type; constexpr code may run at compile time or at run time.*

## Theory and derivation

### Function and class templates

```cpp
template <class T>
constexpr T clamp_to(T x, T lo, T hi) { return x < lo ? lo : (x > hi ? hi : x); }
```

- **Deduction**: all uses of `T` in the parameters must deduce the same type. `clamp_to(5, 0.0, 3.0)` fails: `int` versus `double`. Fix with an explicit `clamp_to<double>(5, 0.0, 3.0)` or two template parameters.
- **Instantiation** happens when the template is used with concrete arguments; errors in the body are reported then, not when the template is defined. Hence the infamous long messages.
- **Definition in headers**: the compiler must see the whole body at each point of instantiation, so templates are defined in headers. Defining a template in a `.cpp` and using it from another file gives a *linker* error (undefined reference) unless you explicitly instantiate it.
- **Class templates** work the same way: `RunningStats<double>` and `RunningStats<float>` are unrelated types. Since C++17, constructor arguments can deduce the template arguments (CTAD): `std::pair p{1, 2.5};`.
- **Non-type parameters**: `template <std::size_t N>` takes a value; `std::array<int, N>` is the standard example.

### Stating assumptions

A template should declare what it requires.

1. `static_assert(std::is_floating_point_v<T>, "message")` fails the build with *your* message when `T` is wrong.
2. `if constexpr (cond)` discards the untaken branch at compile time, so each type only compiles the code that is valid for it:

```cpp
template <class T> auto describe(T) {
  if constexpr (std::is_integral_v<T>) return 1;
  else if constexpr (std::is_floating_point_v<T>) return 2;
  else return 3;
}
```
3. In C++20, **concepts** (`template <std::floating_point T>`) express the constraint in the signature and give a clear error at the call site. In C++17 the equivalents are `static_assert` and `std::enable_if_t`.

Document the *semantic* assumptions too (e.g., "lo <= hi", "NaN passes through unchanged"), because the type system cannot check them.

### constexpr

`constexpr` variables are constants and must be initialized by constant expressions. `constexpr` functions (C++14/17: loops, local variables and conditionals allowed, no `try`, limited standard-library functions) are evaluated at compile time when used in a constant-expression context and run normally otherwise. This differs from `const`: `const int n = read();` is a run-time constant that cannot size an array, while `constexpr int n = 4;` can.

A useful pattern: compute a table at compile time and validate it by `static_assert`:

```cpp
constexpr auto sq = make_squares<6>();   // {0, 1, 4, 9, 16, 25}
static_assert(sq[5] == 25);
```
Beware of overflow in constant expressions: signed overflow is a compile error there, which is a feature. For `int` squares the first overflowing index is 46341, since $46341^2=2{,}147{,}488{,}281>2^{31}-1$.

### Modern idioms

- `auto` deduces by value and drops references and top-level `const`; `auto&` and `const auto&` keep them; `decltype(auto)` keeps the exact expression type. Use `auto` where the type is obvious from the right-hand side, and write the type when it documents intent.
- Structured bindings: `auto [t, v] = sample;` names the members of a struct, pair or tuple.
- `std::optional<T>` expresses "maybe a value" without sentinels like -1 or NaN. `std::string_view` is a non-owning view of text (a borrow in the sense of CPP03).
- Range-for: `for (const auto& s : samples)`; the loop variable is a reference to avoid copies.
- Prefer algorithms and standard types over raw loops and pointers, and uniform initialization with braces (which also forbids narrowing: `int i{2.5}` is an error).

### A numerically sound generic: Welford

For streaming mean and variance, maintaining sums of squares loses precision. Welford's update uses the previous mean, with $\delta=x_n-\bar x_{n-1}$:
$$\bar x_n=\bar x_{n-1}+\frac{\delta}{n},\qquad M_n=M_{n-1}+\delta\,(x_n-\bar x_n),\qquad s^2=\frac{M_n}{n-1}.$$
The naive formula $(\sum x^2-n\bar x^2)/(n-1)$ subtracts two huge, nearly equal numbers (catastrophic cancellation).

## Worked example

Stream the values $2,4,4,4,5,5,7,9$ through Welford's update, with $\bar x_0=0$, $M_0=0$.

| $n$ | $x$ | $\delta=x-\bar x_{n-1}$ | $\bar x_n$ | $M_n$ |
|---|---|---|---|---|
| 1 | 2 | 2 | 2 | 0 |
| 2 | 4 | 2 | 3 | 2 |
| 3 | 4 | 1 | 3.3333 | 2.6667 |
| 4 | 4 | 0.6667 | 3.5 | 3 |
| 5 | 5 | 1.5 | 3.8 | 4.8 |
| 6 | 5 | 1.2 | 4 | 6 |
| 7 | 7 | 3 | 4.4286 | 13.7143 |
| 8 | 9 | 4.5714 | 5 | 32 |

(Check, e.g. row 2: $\delta=4-2=2$, $\bar x=2+2/2=3$, $M=0+2\cdot(4-3)=2$.) The final mean is $5$ and $M_8=32$, so the sample variance is $32/7\approx4.5714$ and the population variance $32/8=4$. The values agree with the direct definition: deviations from 5 are $-3,-1,-1,-1,0,0,2,4$ whose squares sum to $9+1+1+1+0+0+4+16=32$.

Now the constrained-interface part: calling `RunningStats<int>` hits `static_assert(std::is_floating_point_v<T>)` and the build stops with the message "RunningStats needs a floating-point type" instead of silently doing integer division in `delta / n`. Calling `mean(std::vector<std::string>{})` stops at `static_assert(std::is_arithmetic_v<V>)`.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: cppreference, Templates - template argument deduction)* Why does `template <class T> T add(T a, T b); add(1, 2.5);` fail to compile? Give two different fixes and say how the result type differs.
2. **(Easy)** Which of these lines compile? Explain each in one phrase.
   ```cpp
   int n = read_from_sensor();
   constexpr int a = 4 * 2;
   constexpr int b = n * 2;
   const int c = n * 2;
   std::array<int, a> arr1;
   std::array<int, c> arr2;
   ```
3. **(Easy)** A compile-time table `make_squares<N>()` stores `int` squares. How many bytes does it occupy for $N=1000$ (assume 4-byte `int`) and for which smallest index does `i*i` overflow a 32-bit signed int?
4. **(Medium)** *(Adapted from: C++ Core Guidelines, T.62 - place template definitions where they are visible)* A project defines `template <class T> T clamp_to(T, T, T);` in `util.h` and its body in `util.cpp`; `main.cpp` calls `clamp_to(3, 0, 5)` and the link fails. Explain the error, and give two fixes with their trade-offs.
5. **(Medium)** Find the numerical bug: the code below computes the variance of readings near $10^9$ (for example a timestamp in nanoseconds). The true sample variance of $\{10^9+4, 10^9+7, 10^9+13, 10^9+16\}$ is 30. Predict the sign of the result, explain, and replace it with Welford's update.
   ```cpp
   double s = 0, q = 0;
   for (double x : xs) { s += x; q += x * x; }
   double mean = s / xs.size();
   double var = (q - xs.size() * mean * mean) / (xs.size() - 1);
   ```
6. **(Medium)** Predict the output and explain why the last call compiles even though the `std::sqrt` branch could not:
   ```cpp
   template <class T> std::string kind(T x) {
     if constexpr (std::is_integral_v<T>) return "int";
     else if constexpr (std::is_floating_point_v<T>) return std::to_string(std::sqrt(x)).substr(0, 3);
     else return "other";
   }
   std::cout << kind(3) << ' ' << kind(2.25) << ' ' << kind("x");
   ```
7. **(Medium)** *(Adapted from: C++ Core Guidelines, T.10 and T.150)* Write the `static_assert` that makes `mean(const Container&)` fail with a one-line message for a container of `std::string`, and explain what a C++20 `requires` clause would improve for the *caller*.
8. **(Medium)** Without running the code, state the types: `int i = 5; const int& r = i; auto a = r; auto& b = r; decltype(auto) c = r; auto d = std::move(i);`. Then write `static_assert`s that prove your answers and compile them.
9. **(Hard)** A generic `template <class F, class T> T trapezoid(F f, T a, T b, int n)` integrates `f` on $[a,b]$. List the assumptions it needs (about `F`, `T`, `n`, smoothness) and how to enforce each. For $f=\sin$ on $[0,\pi/2]$, the trapezoid error is at most $\frac{(b-a)^3}{12n^2}\max|f''|$; find the smallest $n$ guaranteeing error $\le10^{-6}$.
10. **(Hard)** *(Adapted from: cppreference, constexpr specifier)* Explain why `constexpr double s = std::sin(1.0);` may or may not compile in C++17 depending on the compiler, and write a `constexpr` replacement using a Taylor series with 12 terms. What accuracy should you verify and over which range?
11. **(Mini-project)** Build a compile-time lookup table of $\sin$ at 1-degree resolution ($0^\circ$-$90^\circ$) using your constexpr Taylor function, `static_assert` the endpoints (0 and nearly 1), and measure its maximum interpolation error against `std::sin` over a fine grid. Report the error and the table size in bytes.

## Reference implementation

Generic utilities with explicit assumptions: `clamp_to`, `deg2rad`, a compile-time `make_squares`, Welford's `RunningStats` and a container `mean`. Compile with `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

```cpp
// CPP06 reference: small generic numerical utilities with explicit, checked assumptions.
#include <array>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <optional>
#include <type_traits>
#include <vector>

// clamp x into [lo, hi]. Precondition: lo <= hi. (NaN passes through unchanged.)
template <class T>
constexpr T clamp_to(T x, T lo, T hi) {
  static_assert(std::is_arithmetic_v<T>, "clamp_to needs an arithmetic type");
  return x < lo ? lo : (x > hi ? hi : x);
}

template <class T>
constexpr T deg2rad(T degrees) {
  static_assert(std::is_floating_point_v<T>, "deg2rad needs a floating-point type");
  return degrees * static_cast<T>(3.14159265358979323846L) / static_cast<T>(180);
}

// 0, 1, 4, 9, ... computed at compile time.
template <std::size_t N>
constexpr std::array<int, N> make_squares() {
  std::array<int, N> a{};
  for (std::size_t i = 0; i < N; ++i) a[i] = static_cast<int>(i * i);
  return a;
}

// Welford's online mean/variance: numerically stable, O(1) memory.
template <class T>
class RunningStats {
  static_assert(std::is_floating_point_v<T>, "RunningStats needs a floating-point type");

 public:
  void push(T x) {
    ++n_;
    const T delta = x - mean_;
    mean_ += delta / static_cast<T>(n_);
    m2_ += delta * (x - mean_);
  }
  std::size_t count() const { return n_; }
  std::optional<T> mean() const {
    if (n_ == 0) return std::nullopt;
    return mean_;
  }
  // Sample variance (divides by n-1); needs at least two values.
  std::optional<T> variance() const {
    if (n_ < 2) return std::nullopt;
    return m2_ / static_cast<T>(n_ - 1);
  }

 private:
  std::size_t n_ = 0;
  T mean_ = 0;
  T m2_ = 0;
};

// Mean of any container of arithmetic values, accumulated in double. Empty -> nullopt.
template <class Container>
std::optional<double> mean(const Container& c) {
  using V = typename Container::value_type;
  static_assert(std::is_arithmetic_v<V>, "mean needs a container of arithmetic values");
  if (c.empty()) return std::nullopt;
  double sum = 0.0;
  for (const V& x : c) sum += static_cast<double>(x);
  return sum / static_cast<double>(c.size());
}

// ---- self-test
int main() {
  static_assert(clamp_to(5, 0, 3) == 3);
  static_assert(make_squares<5>()[4] == 16);
  constexpr double h = deg2rad(90.0);
  static_assert(h > 1.5707 && h < 1.5708);
  RunningStats<double> s;
  for (double x : {2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0}) s.push(x);
  if (*s.mean() != 5.0) return 1;
  if (std::abs(*s.variance() - 32.0 / 7.0) > 1e-12) return 2;
  if (*mean(std::vector<int>{1, 2, 4}) < 2.33 || mean(std::vector<int>{})) return 3;
  std::cout << "CPP06 reference self-test passed\n";
}
```

## Independent practice

### Goal

Implement five small generic utilities whose assumptions are checked by `static_assert`, and test them with compile-time and run-time checks.

### Setup

`g++` (version 9 or later) or `clang++` with C++17. Save the starter and then the tests as `lab.cpp`; compile with `g++ -std=c++17 -Wall -Wextra -g lab.cpp -o lab && ./lab`.

### Tasks

1. Implement `clamp_to` and see the first four `static_assert`s in the tests pass at compile time.
2. Implement `deg2rad` with a `static_assert` on `T` and check that `deg2rad(1.0f)` stays `float`.
3. Implement `make_squares<N>()` and confirm that the compiler evaluates `make_squares<6>()[5]` at compile time.
4. Implement `RunningStats<T>` with Welford's update; check the table in the worked example.
5. Implement the generic `mean` for `vector<int>`, `list<float>` and an empty container; test that a container of strings gives your `static_assert` message (try it separately, then remove the line).
6. Break it on purpose: compute variance with the naive formula and print the value for the `1e9 + x` data of exercise 5.

### Starter code

```cpp
#include <array>
#include <cmath>
#include <cstddef>
#include <optional>
#include <stdexcept>
#include <type_traits>
#include <vector>

// Clamp x into [lo, hi] (precondition lo <= hi). Must be usable in constant expressions.
// static_assert that T is arithmetic.
template <class T>
constexpr T clamp_to(T x, T lo, T hi) { throw std::logic_error("NotImplemented"); }

// degrees -> radians for floating-point T only (static_assert it). constexpr.
template <class T>
constexpr T deg2rad(T degrees) { throw std::logic_error("NotImplemented"); }

// Array {0, 1, 4, 9, ..., (N-1)^2}, computed at compile time.
template <std::size_t N>
constexpr std::array<int, N> make_squares() { throw std::logic_error("NotImplemented"); }

// Welford online statistics for floating-point T (static_assert it).
//   push(x): update count, mean, M2 with delta = x - mean; mean += delta/n; M2 += delta*(x - mean)
//   count(), mean() -> nullopt if empty, variance() -> sample variance (n-1), nullopt if n < 2
template <class T>
class RunningStats {
 public:
  void push(T x) { throw std::logic_error("NotImplemented"); }
  std::size_t count() const { throw std::logic_error("NotImplemented"); }
  std::optional<T> mean() const { throw std::logic_error("NotImplemented"); }
  std::optional<T> variance() const { throw std::logic_error("NotImplemented"); }
};

// Mean of any container with an arithmetic value_type (static_assert), accumulated in double.
// Empty container -> std::nullopt.
template <class Container>
std::optional<double> mean(const Container& c) { throw std::logic_error("NotImplemented"); }
```

### Tests

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#include <iostream>
#include <list>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)

// compile-time checks: these fail to COMPILE until your constexpr code is right
static_assert(clamp_to(5, 0, 3) == 3 && clamp_to(-1, 0, 3) == 0 && clamp_to(2, 0, 3) == 2);
static_assert(clamp_to(0.5, 0.0, 1.0) == 0.5);
static_assert(make_squares<6>()[5] == 25 && make_squares<6>()[0] == 0);
static_assert(deg2rad(180.0) > 3.14159 && deg2rad(180.0) < 3.1416);
static_assert(std::is_same_v<decltype(deg2rad(1.0f)), float>);

int main() {
  // hand-computed Welford data: mean 5, sum of squared deviations 32 -> sample variance 32/7
  RunningStats<double> s;
  CHECK(s.count() == 0 && !s.mean() && !s.variance());
  s.push(2);
  CHECK(s.mean().value() == 2.0 && !s.variance());
  for (double x : {4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0}) s.push(x);
  CHECK(s.count() == 8 && std::fabs(s.mean().value() - 5.0) < 1e-12);
  CHECK(std::fabs(s.variance().value() - 32.0 / 7.0) < 1e-12);
  // numerical stability: large offset, true variance of {4,7,13,16} is 30
  RunningStats<double> big;
  for (double x : {4.0, 7.0, 13.0, 16.0}) big.push(1e9 + x);
  CHECK(std::fabs(big.variance().value() - 30.0) < 1e-6);
  // invariant: shifting every value by c shifts the mean by c and leaves the variance unchanged
  RunningStats<double> a, b;
  for (double x : {0.3, -1.2, 5.5, 2.0, 2.0}) { a.push(x); b.push(x + 100.0); }
  CHECK(std::fabs(b.mean().value() - a.mean().value() - 100.0) < 1e-9);
  CHECK(std::fabs(b.variance().value() - a.variance().value()) < 1e-9);
  // generic mean over different containers and element types
  CHECK(std::fabs(mean(std::vector<int>{1, 2, 4}).value() - 7.0 / 3.0) < 1e-12);
  CHECK(mean(std::list<float>{1.5f, 2.5f}).value() == 2.0);
  CHECK(!mean(std::vector<double>{}));
  // wide integers do not overflow because the sum is a double
  CHECK(mean(std::vector<int>{2000000000, 2000000000}).value() == 2000000000.0);
  std::cout << "all tests passed\n";
}
```

### Expected output

```
all tests passed
```

With the unimplemented starter the build itself fails at the first `static_assert` in the tests, which is the intended signal: compile-time failures are tests too.

### Extension challenge

Add `RunningStats::merge(const RunningStats&)` using the parallel (Chan) formula so partial statistics from two threads can be combined, and test it against a single pass. Then rewrite the constraints using C++20 `concept`s if your compiler supports `-std=c++20`.

### Library track

Use `<numeric>`/`<algorithm>` as references and, if installed, Eigen (`sudo apt install libeigen3-dev`; header-only, itself a template library over the scalar type). If Eigen is missing, delete the two Eigen parts and keep the rest. Paste this *after* your finished utilities (it has its own `main`, so drop the one from the tests) and compile with `g++ -std=c++17 -Wall -Wextra -I/usr/include/eigen3`.

```cpp
#include <algorithm>
#include <cassert>
#include <iostream>
#include <numeric>
#include <random>
#include <Eigen/Dense>   // Eigen 3: apt install libeigen3-dev; compile with -I/usr/include/eigen3

// Eigen is the "generic over the scalar type" library: Matrix<Scalar, Rows, Cols>.
// A generic function over ANY Eigen vector type, with the assumption stated:
template <class Derived>
double eigen_mean(const Eigen::MatrixBase<Derived>& v) {
  static_assert(Derived::ColsAtCompileTime == 1, "eigen_mean needs a column vector");
  return v.template cast<double>().mean();
}

int main() {
  std::mt19937 g(3);
  std::normal_distribution<double> nd(1e9, 5.0);       // large offset: the naive formula fails here
  std::vector<double> xs(10000);
  for (double& x : xs) x = nd(g);

  // 1. Welford against a two-pass reference computed with <numeric>
  RunningStats<double> w;
  for (double x : xs) w.push(x);
  const double m = std::accumulate(xs.begin(), xs.end(), 0.0) / xs.size();
  const double ss = std::accumulate(xs.begin(), xs.end(), 0.0, [m](double a, double x) { return a + (x - m) * (x - m); });
  const double v2 = ss / (xs.size() - 1);
  assert(std::fabs(*w.mean() - m) < 1e-4 && std::fabs(*w.variance() - v2) < 1e-6 * v2);   // relative 1e-6

  // 2. the same numbers through Eigen (a templated library): mean() and a centred dot product
  Eigen::Map<const Eigen::VectorXd> e(xs.data(), xs.size());
  const double evar = (e.array() - e.mean()).matrix().squaredNorm() / (xs.size() - 1);
  assert(std::fabs(e.mean() - *w.mean()) < 1e-4 && std::fabs(evar - *w.variance()) < 1e-6 * evar);
  assert(std::fabs(eigen_mean(Eigen::Vector3f(1, 2, 6)) - 3.0) < 1e-6);   // same template, float scalar
  // eigen_mean(Eigen::RowVector3d(1, 2, 3));   // uncomment: stops at YOUR static_assert message

  // 3. std::clamp (C++17) agrees with clamp_to, including at the ends
  for (int i = -5; i <= 5; ++i) assert(clamp_to(i, -2, 3) == std::clamp(i, -2, 3));
  std::cout << "Welford var " << *w.variance() << " == two-pass " << ss / (xs.size() - 1) << "\nlibrary track ok\n";
}
```

Expected output: the Welford and two-pass variances agree (about 24.9 for this seed) followed by `library track ok`. Uncommenting the `RowVector3d` line must stop the build at your `static_assert` message, the same habit as in `RunningStats`. The tolerances are relative (`1e-6 * var`) because with values near $10^9$ even the two-pass mean is only good to about $10^{-7}$.

## Verification

- Compile-time tests with `static_assert` run on every build; they cost nothing at run time.
- Compare numerically sensitive code against an independent oracle (NumPy `np.var(x, ddof=1)`) on both benign data and data with a large offset.
- Instantiate each template with each supported type (`float`, `double`) and one unsupported type; the unsupported one must produce your message, not 40 lines.
- Check that the shift invariant holds: adding $c$ to every value shifts the mean by $c$ and does not change the variance.
- Compile with `-Wall -Wextra -Wconversion` to catch narrowing between template types, and run under `-fsanitize=undefined`.

## Failure modes

| Mistake | Result |
|---|---|
| Template body in a `.cpp` file | linker error `undefined reference to clamp_to<int>(...)` |
| Mixed argument types `add(1, 2.5)` | deduction conflict error |
| Naive variance on offset data | negative variance (here $-170.67$ instead of $30$) |
| `std::accumulate(..., 0)` over doubles | integer accumulation (CPP05) |
| Missing `static_assert` on `T` | integer division inside `delta / n` or confusing errors deep in the template |
| `const` where `constexpr` is needed | "not a constant expression" when sizing an array |
| Signed overflow in constexpr | compile error (good) versus silent wraparound/UB at run time (bad) |
| `auto` that copies (`auto x = vec;` in a loop) | hidden copies; use `const auto&` |
| Over-generic code | unreadable errors and bloat; add constraints, keep the number of instantiations small |

## Alternatives and trade-offs

- **Templates vs virtual functions (CPP04).** Templates give static dispatch and inlining but fix the type at compile time and grow code; virtual functions allow swapping at run time at the cost of an indirect call.
- **Templates vs overloads.** For two or three types, plain overloads (`float`, `double`) are clearer than a constrained template.
- **`constexpr` vs a code generator or a run-time table.** `constexpr` keeps the source of truth in the C++ code; a Python-generated table is easier for huge or complex data. Compile-time work increases build time, so avoid it for large loops.
- **`static_assert` / `enable_if` / concepts.** `static_assert` gives the best messages in C++17 but fails *inside* the function; SFINAE (`enable_if`) lets overload resolution pick another function but is hard to read; concepts (C++20) do both well.
- **`optional` vs NaN vs exceptions** for "no result": `optional` is explicit and cheap; NaN can slip through arithmetic unnoticed; exceptions suit rare failures only.

## Transfer and retention

Eigen, `std::chrono` (units as types) and ROS 2's `rclcpp::Publisher<MessageT>` are all templates; reading their errors becomes much easier once you can identify the instantiation and the unmet assumption. Python's `typing.Generic` and NumPy dtype dispatch play the same role at a different time (run time). Spaced review: after a few days, write from memory a templated function with a `static_assert`, an `if constexpr` and a `constexpr` helper, then explain which parts run at compile time. Also re-derive the Welford update from the definition of the mean.

## Exercise answers

1. `T` is deduced as `int` from the first argument and `double` from the second, a conflict. Fix A: `add<double>(1, 2.5)` converts the int explicitly and returns `double` (3.5). Fix B: `template <class T, class U> auto add(T a, U b) { return a + b; }` returns the common type, here `double`. Fix C: call `add(1.0, 2.5)`.
2. `a` compiles (constant expression). `b` fails (`n` is a run-time value). `c` compiles as a run-time `const`. `arr1` compiles (`a` is a compile-time constant); `arr2` fails because `c` is not usable as a template argument.
3. $1000\cdot4=4000$ bytes. $46340^2=2{,}147{,}395{,}600$ fits, $46341^2=2{,}147{,}488{,}281>2{,}147{,}483{,}647$ overflows; the first overflowing index is 46341.
4. The compiler compiled `main.cpp` without seeing the body, so it emitted a call to `clamp_to<int>`, but `util.cpp` never instantiated that specialization: undefined reference. Fix 1: move the body into the header (simple; every translation unit instantiates, longer compile times). Fix 2: explicit instantiation in `util.cpp` (`template int clamp_to<int>(int, int, int);`), which limits the allowed types but keeps compile times low.
5. The result is negative (about $-170.7$ in the lesson's check): $q\approx4\times10^{18}$ and $n\bar x^2$ are equal up to about 18 digits, but a double has about 16, so the difference is dominated by rounding error. A variance cannot be negative. The Welford update subtracts small quantities (the deviations) at every step, so cancellation is avoided; it returns 30.
6. Output: `int 1.5 other`. In the discarded branches `std::sqrt(x)` is never instantiated for `int` or `const char*`, thanks to `if constexpr`; with a plain `if` the call would have to compile for every `T`, and `std::sqrt(const char*)` fails. (`sqrt(2.25)=1.5`, `to_string` gives "1.500000", substr(0,3) is `1.5`.)
7. `static_assert(std::is_arithmetic_v<typename Container::value_type>, "mean needs a container of arithmetic values");` placed at the top of the function: the error is one line with your message. With C++20 `requires std::is_arithmetic_v<std::ranges::range_value_t<C>>` in the signature, the error is reported at the call site as an unsatisfied constraint, overload resolution can reject the candidate and pick another overload, and the constraint is visible in the documentation.
8. `a` is `int` (auto drops the reference and const), `b` is `const int&`, `c` is `const int&` (decltype(auto) keeps the declared type of the expression `r`), `d` is `int` (`std::move(i)` yields an rvalue, auto copies the value). Proofs: `static_assert(std::is_same_v<decltype(a), int>);` and so on.
9. Assumptions: `F` is callable with `T` and returns something convertible to `T` (a `static_assert(std::is_invocable_r_v<T, F, T>)`); `T` is floating point (`static_assert`); `n >= 1` (check at run time and throw/return an error); $a\le b$ finite; $f$ has a bounded second derivative on the interval. For the bound, $\max|f''|=\max|\sin|=1$, so $\frac{(\pi/2)^3}{12n^2}\le10^{-6}\Rightarrow n\ge\sqrt{3.8758/(12\cdot10^{-6})}=568.3$, so $n=569$ (the actual error with $n=569$ is about $6.4\times10^{-7}$).
10. In C++17 `std::sin` is not required to be `constexpr`; GCC folds it as a compiler extension while other compilers reject it. A portable replacement: `constexpr double taylor_sin(double x) { double term = x, sum = x; for (int k = 1; k < 12; ++k) { term *= -x * x / ((2 * k) * (2 * k + 1)); sum += term; } return sum; }`. Verify against `std::sin` on $[0,\pi/2]$ (and the wrapped range you will use): the maximum error there is about $3\times10^{-16}$. Accuracy degrades for large $|x|$, so reduce the argument first.
11. A good answer includes: a `constexpr std::array<double, 91>` built by a `constexpr` function; `static_assert(table[0] == 0.0)` and a bound check on `table[90]` (between 0.999999 and 1.000001); a loop over 0.01-degree steps computing linear interpolation between neighbours and the maximum absolute error against `std::sin` (about $\frac{h^2}{8}\max|f''|=\frac{(0.01745)^2}{8}\approx3.8\times10^{-5}$); the table size is $91\cdot8=728$ bytes; and a statement of the compile-time cost.

## Further reading

- [cppreference: Templates](https://en.cppreference.com/w/cpp/language/templates) - deduction, specialization, and instantiation rules in detail.
- [cppreference: constexpr specifier](https://en.cppreference.com/w/cpp/language/constexpr) - what is allowed in constant expressions in each standard.
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - section T on templates and generic programming, and the rules on constants (Con) and `constexpr` (F.4).

**More practice:** the quizzes on [LearnCpp: function templates](https://www.learncpp.com/cpp-tutorial/function-templates/), [templates in multiple files](https://www.learncpp.com/cpp-tutorial/using-function-templates-in-multiple-files/), [class templates](https://www.learncpp.com/cpp-tutorial/class-templates/), [constexpr functions](https://www.learncpp.com/cpp-tutorial/constexpr-functions/) and [constexpr if](https://www.learncpp.com/cpp-tutorial/constexpr-if-statements/) (answers shown on each page), the Core Guidelines [templates and generic programming](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#t-templates-and-generic-programming) section, and the Eigen page on [writing functions taking Eigen types](https://eigen.tuxfamily.org/dox/TopicFunctionTakingEigenTypes.html) (a real-world template-constraint problem).