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
    },
    {
      "title": "cppreference: Template argument deduction",
      "url": "https://en.cppreference.com/w/cpp/language/template_argument_deduction"
    },
    {
      "title": "cppreference: Fold expressions",
      "url": "https://en.cppreference.com/w/cpp/language/fold"
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

Think of a template as a rubber stamp with a blank for the type. The stamp itself prints nothing; each time you press it with a new type you get a new, independent page. This explains three things beginners find surprising: the whole body must be visible when you press (so templates live in headers), mistakes inside the body appear only when a page is printed (so error messages are long and point at the instantiation, not the definition), and two pages printed from the same stamp are unrelated types (`RunningStats<float>` is not a base or a sibling of `RunningStats<double>`). The compiler is not "running" the template; it is writing ordinary code for you and then compiling that code.

Everyday robot example: a filter that clamps a joint angle in radians, a motor current in amperes and a pixel count must behave the same way, but you do not want a pixel count to be accidentally clamped by floating-point bounds. The type system is the cheapest place to say "these three quantities share an algorithm but not their units or their assumptions", and `static_assert` and `constexpr` are how the compiler is told to check it before the robot ever moves.

**Predict before you compute.** Without running anything, decide what `clamp_to(3, 0.5, 2.5)` should return if you read it as mathematics, and then what it returns in a version where the bounds are forced to the type of the first argument. The paragraph after the figure gives the answer.

**The common wrong intuition** is that a conversion that "obviously fits" is harmless, and that a floating-point sum is a sum. Neither is true. A conversion changes the value when the target type cannot represent it, and floating-point addition is not associative, so an innocent-looking fold or a streaming variance can lose all of its significant digits when large values cancel. The remedy in both cases is the same habit: write the assumption (type, range, order of operations) where the compiler or a test can check it, instead of in your head.

![Left: the template clamp_to as a stencil that yields clamp_to<int> and clamp_to<double> and is stopped by a static_assert for std::string; right: what the compiler evaluates (constexpr values, static_assert) against what the running program evaluates](/lesson-figures/CPP06.svg)

*Figure: one template stencil yields one real function per type, and a `static_assert` turns an unsupported type into a build error. On the right, `constexpr` values and `static_assert` are evaluated by the compiler, while a value read from a sensor can only be evaluated by the running program; the same `constexpr` function serves both.*

**The answer to the prediction.** Read as mathematics the result is $2.5$. The version that forces the bounds to the type of the first argument silently turns $2.5$ into $2$ and returns $2$: it compiles, runs, and is wrong by $0.5$. The theory below returns to this gap (deduction, non-deduced contexts) and exercise 14 works with it.

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

**Example.** Three calls of one template `twice` are compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`: `twice(21)`, `twice(1.25)` and `twice<float>(2)`. Each prints the signature that the compiler stamped out (GCC's `__PRETTY_FUNCTION__`). What does each call deduce or take as `T`, and how many functions result?

```cpp
#include <iostream>

template <class T>
T twice(T x) {
  std::cout << __PRETTY_FUNCTION__ << '\n';
  return x + x;
}

int main() {
  twice(21);          // T deduced as int
  twice(1.25);        // T deduced as double
  twice<float>(2);    // T given explicitly; the int argument converts to float
}
```

**Solution.** `twice(21)` deduces `T = int` from the argument, `twice(1.25)` deduces `T = double`, and `twice<float>(2)` names `T` explicitly, so the argument 2 converts to `float`. Three calls make three independent functions, each compiled for its own type (cppreference, *Templates*). The program prints:

```text
T twice(T) [with T = int]
T twice(T) [with T = double]
T twice(T) [with T = float]
```

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

**Example.** `half` is meant for floating-point types only and guards itself with `static_assert`. What does `half(7.0f)` print, and what does the compiler do when the program is built with `-DTRY_INT`, which adds the call `half(7)`? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <type_traits>

template <class T>
T half(T x) {
  static_assert(std::is_floating_point_v<T>, "half needs a floating-point type");
  return x / 2;
}

int main() {
  std::cout << half(7.0f) << '\n';
#ifdef TRY_INT
  std::cout << half(7) << '\n';
#endif
}
```

**Solution.** Without `-DTRY_INT` only `half(7.0f)` is instantiated with `T = float`: the assertion holds and $7.0/2=3.5$ is printed (first block). With `-DTRY_INT` the call `half(7)` instantiates `T = int`, `std::is_floating_point_v<int>` is false, and the build stops with the author's own message instead of performing an integer division that would give 3 (second block, one line that names the problem):

```text
3.5
```

```text
half.cpp: In instantiation of ‘T half(T) [with T = int]’:
half.cpp:13:20:   required from here
half.cpp:6:22: error: static assertion failed: half needs a floating-point type
```

### constexpr

`constexpr` variables are constants and must be initialized by constant expressions. `constexpr` functions (C++14/17: loops, local variables and conditionals allowed, no `try`, limited standard-library functions) are evaluated at compile time when used in a constant-expression context and run normally otherwise. This differs from `const`: `const int n = read();` is a run-time constant that cannot size an array, while `constexpr int n = 4;` can.

A useful pattern: compute a table at compile time and validate it by `static_assert`:

```cpp
constexpr auto sq = make_squares<6>();   // {0, 1, 4, 9, 16, 25}
static_assert(sq[5] == 25);
```
Beware of overflow in constant expressions: signed overflow is a compile error there, which is a feature. For `int` squares the first overflowing index is 46341, since $46341^2=2{,}147{,}488{,}281>2^{31}-1$.

**Example.** A 12-bit ADC with a 3.3 V reference converts counts to millivolts with $\text{mv}=\lfloor 3300\,c/4095\rfloor$. The program checks $c=0$ and $c=4095$ with `static_assert`, builds a three-entry table for $c=1024,2048,3072$ and also calls `mv(argc + 1000)`. Which parts does the compiler evaluate, and what does the program print? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <array>
#include <iostream>

constexpr int mv(int counts) { return counts * 3300 / 4095; }   // 12-bit ADC, 3.3 V reference
static_assert(mv(0) == 0 && mv(4095) == 3300);
constexpr std::array<int, 3> table{mv(1024), mv(2048), mv(3072)};   // built by the compiler

int main(int argc, char**) {
  const int runtime = mv(argc + 1000);   // argc is a run-time value: same function, run-time evaluation
  std::cout << table[0] << ' ' << table[1] << ' ' << table[2] << ' ' << runtime << '\n';
}
```

**Solution.** The two `static_assert`s and the three-entry table are constant-expression contexts, so the compiler evaluates them (the table sits in the binary). The assertions hold: $\text{mv}(0)=0$ and $\text{mv}(4095)=3300\cdot4095/4095=3300$. The table is $\lfloor 3300\cdot1024/4095\rfloor=825$, $\lfloor 3300\cdot2048/4095\rfloor=1650$ and $\lfloor 3300\cdot3072/4095\rfloor=2475$. `mv(argc + 1000)` has a run-time argument ($\text{argc}=1$, so $c=1001$), so the same function simply runs: $\lfloor 3300\cdot1001/4095\rfloor=806$. One `constexpr` function thus serves both compile time and run time. The program prints:

```text
825 1650 2475 806
```

### Modern idioms

- `auto` deduces by value and drops references and top-level `const`; `auto&` and `const auto&` keep them; `decltype(auto)` keeps the exact expression type. Use `auto` where the type is obvious from the right-hand side, and write the type when it documents intent.
- Structured bindings: `auto [t, v] = sample;` names the members of a struct, pair or tuple.
- `std::optional<T>` expresses "maybe a value" without sentinels like -1 or NaN. `std::string_view` is a non-owning view of text (a borrow in the sense of CPP03).
- Range-for: `for (const auto& s : samples)`; the loop variable is a reference to avoid copies.
- Prefer algorithms and standard types over raw loops and pointers, and uniform initialization with braces (which also forbids narrowing: `int i{2.5}` is an error).

**Example.** A log of (time in s, current in A) samples $\{(0.1,2.0),(0.2,4.5),(0.3,6.0)\}$ is searched for the first sample above a limit, once for 4 A and once for 9 A. `std::optional` replaces a sentinel such as $-1$, the structured binding names `t` and `v`, and the range-for takes `const auto&` so that no sample is copied. What does the program print for each limit? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <optional>
#include <vector>

struct Sample {
  double t;   // s
  double v;   // A
};

std::optional<Sample> first_above(const std::vector<Sample>& log, double limit) {
  for (const auto& s : log)
    if (s.v > limit) return s;
  return std::nullopt;
}

int main() {
  const std::vector<Sample> log{{0.1, 2.0}, {0.2, 4.5}, {0.3, 6.0}};
  for (double limit : {4.0, 9.0}) {
    if (auto s = first_above(log, limit)) {
      auto [t, v] = *s;
      std::cout << "limit " << limit << ": t=" << t << " v=" << v << '\n';
    } else {
      std::cout << "limit " << limit << ": none\n";
    }
  }
}
```

**Solution.** For the limit 4 A the first sample with $v>4$ is $(0.2,4.5)$, since $2.0$ is not above $4$; `first_above` returns it and the binding gives `t=0.2 v=4.5`. For the limit 9 A no sample qualifies ($6.0\le 9$), so the function returns `std::nullopt` and the program says so, instead of returning a magic value. The program prints:

```text
limit 4: t=0.2 v=4.5
limit 9: none
```

### A numerically sound generic: Welford

For streaming mean and variance, maintaining sums of squares loses precision. Welford's update uses the previous mean, with $\delta=x_n-\bar x_{n-1}$:
$$\bar x_n=\bar x_{n-1}+\frac{\delta}{n},\qquad M_n=M_{n-1}+\delta\,(x_n-\bar x_n),\qquad s^2=\frac{M_n}{n-1}.$$
The naive formula $(\sum x^2-n\bar x^2)/(n-1)$ subtracts two huge, nearly equal numbers (catastrophic cancellation).

**Example.** Four readings $10^{10}+\{1,4,4,7\}$ have true sample variance $18/3=6$ (deviations $-3,0,0,3$ from the mean $10^{10}+4$). Both the naive running-sums formula and the Welford update run in `double` on the same data. What does each print? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <vector>

int main() {
  const std::vector<double> xs{1e10 + 1, 1e10 + 4, 1e10 + 4, 1e10 + 7};
  double s = 0, q = 0, mean = 0, m2 = 0;
  int n = 0;
  for (double x : xs) {
    s += x;
    q += x * x;                          // naive running sums
    ++n;
    const double delta = x - mean;       // Welford update
    mean += delta / n;
    m2 += delta * (x - mean);
  }
  const double naive = (q - n * (s / n) * (s / n)) / (n - 1);
  std::cout << "naive " << naive << ", Welford " << m2 / (n - 1) << '\n';
}
```

**Solution.** The naive formula computes $(q-n\bar x^2)/(n-1)$ from $q=\sum x^2\approx4\cdot10^{20}$ and $n\bar x^2$, two numbers of that size whose difference is only $18$. Doubles near $4\cdot10^{20}$ (between $2^{68}$ and $2^{69}$) are spaced by $2^{68-52}=65\,536$, so the difference is lost in rounding and comes out as $-65\,536/3=-21\,845.3$, a negative variance. The Welford update only works with small deviations: $\delta=1\cdot10^{10}+1$ gives mean $10^{10}+1$ and $M=0$; then $\delta=3$, mean $10^{10}+2.5$, $M=4.5$; $\delta=1.5$, mean $10^{10}+3$, $M=6$; $\delta=4$, mean $10^{10}+4$, $M=18$, so the variance is $18/3=6$. The program prints:

```text
naive -21845.3, Welford 6
```

The scale of the problem can be read off the spacing of doubles: the sums $q=\sum x^2$ and $n\bar x^2$ are about $n\cdot\text{offset}^2$ in size, and a double near that size cannot resolve differences smaller than its spacing $2^{\lfloor\log_2 q\rfloor-52}$. The slider shows the spacing divided by $n-1$ against the true variance: where the ratio reaches 1 the naive formula can no longer be trusted (this is a scale estimate, not a rigorous bound, since the sums accumulate several roundings).

```explore
{
  "title": "When does the naive variance break?",
  "title_vi": "Khi nào phương sai ngây thơ bị hỏng?",
  "prompt": "Predict first: for 4 readings with variance 30, at what offset (power of ten) does the rounding error scale of the naive formula become as large as the variance itself? Then move the offset slider and check against the lesson's case at 10^9.",
  "prompt_vi": "Dự đoán trước: với 4 số đo có phương sai 30, ở độ lệch nào (lũy thừa của 10) thì quy mô sai số làm tròn của công thức ngây thơ lớn bằng chính phương sai? Sau đó kéo thanh trượt độ lệch và đối chiếu với trường hợp 10^9 của bài.",
  "params": [
    {
      "name": "off",
      "label": "log10 of the offset",
      "label_vi": "log10 của độ lệch",
      "min": 0,
      "max": 11,
      "step": 0.25,
      "value": 9,
      "unit": ""
    },
    {
      "name": "n",
      "label": "readings n",
      "label_vi": "số đo n",
      "min": 2,
      "max": 1000,
      "step": 1,
      "value": 4,
      "unit": ""
    },
    {
      "name": "v",
      "label": "true variance",
      "label_vi": "phương sai thật",
      "min": 1,
      "max": 1000,
      "step": 1,
      "value": 30,
      "unit": ""
    }
  ],
  "let": [
    {
      "name": "sp",
      "expr": "2^(floor(log10(n*10^(2*off))/log10(2))-52)"
    }
  ],
  "plot": {
    "x": {
      "name": "h",
      "min": 0,
      "max": 11,
      "label": "log10 of the offset",
      "label_vi": "log10 của độ lệch"
    },
    "y": {
      "label": "log10 (error scale / true variance)",
      "label_vi": "log10 (quy mô sai số / phương sai thật)",
      "min": -12,
      "max": 8
    },
    "series": [
      {
        "expr": "log10(2^(floor(log10(n*10^(2*h))/log10(2))-52)/(n-1)/v)",
        "label": "naive error scale / variance",
        "label_vi": "quy mô sai số ngây thơ / phương sai",
        "color": "orange"
      },
      {
        "expr": "0",
        "label": "error = variance",
        "label_vi": "sai số = phương sai",
        "color": "grey"
      }
    ],
    "points": [
      {
        "x": "off",
        "y": "log10(sp/(n-1)/v)",
        "label": "your offset",
        "label_vi": "độ lệch của bạn",
        "color": "orange"
      }
    ]
  },
  "readouts": [
    {
      "label": "spacing of doubles at q = n·offset²",
      "label_vi": "khoảng cách double tại q = n·offset²",
      "expr": "sp",
      "unit": "",
      "digits": 0
    },
    {
      "label": "error scale of the variance (spacing / (n−1))",
      "label_vi": "quy mô sai số của phương sai (khoảng cách / (n−1))",
      "expr": "sp/(n-1)",
      "unit": "",
      "digits": 1
    },
    {
      "label": "error scale / true variance",
      "label_vi": "quy mô sai số / phương sai thật",
      "expr": "sp/(n-1)/v",
      "unit": "",
      "digits": 3
    }
  ]
}
```

### Deduction in depth: forwarding references and non-deduced contexts

Take `template <class T> void f(P)` called as `f(e)` with an argument of type $A$. The deduction rules (cppreference, *Template argument deduction*, "Deduction from a function call") are applied in this order: if `P` is a reference type, the referenced type is used; top-level cv-qualifiers of `P` are ignored; if `P` is *not* a reference, `A` first decays (array to pointer, function to function pointer, top-level `const` dropped). Then the compiler looks for `T` that makes `P` identical to `A`.

One rule breaks the pattern. If `P` is `T&&` with `T` a bare, cv-unqualified template parameter (a **forwarding reference**) and the argument is an lvalue of type $A$, then $A\&$ is used for deduction, so `T = A&`. The parameter type `T&&` becomes `A& &&`, and the reference-collapsing rules turn it into `A&` (only `&& &&` collapses to `&&`). Consequently:

| call | deduced `T` | parameter type |
|---|---|---|
| `f(i)` with `int i` | `int&` | `int&` |
| `f(ci)` with `const int ci` | `const int&` | `const int&` |
| `f(0)` | `int` | `int&&` |

`std::forward<T>(x)` is `static_cast<T&&>(x)`: for `T = int&` it yields an lvalue, for `T = int` an rvalue, so the caller's value category is restored. The special case needs the exact form `T&&`: for `template <class T> void g(const T&&)` the call `g(i)` is an error (an rvalue reference cannot bind an lvalue), and inside a class template `T&&` of the class's own parameter is never a forwarding reference.

**Non-deduced contexts.** A parameter written as `typename identity<T>::type` (everything left of `::`) or a braced list `{1,2,3}` does not take part in deduction; `T` must come from elsewhere or be given explicitly. cppreference's own example: `bad(x, 1.2)` for `std::vector<std::complex<double>> x` fails because `T` is deduced as `complex<double>` from `x` and as `double` from `1.2`, while the version with `typename identity<T>::type value` deduces from `x` only and converts `1.2`. This is the standard way to fix exercise 1, with a price: the conversion is silent, so `int`-typed `T` can silently truncate a `double` bound (see exercise 14).

![Three calls of f(T&&): deduced T, parameter type after reference collapsing and the value category restored by std::forward, with the four collapsing rules below](/lesson-figures/CPP06-2.svg)

*Figure: the table of this section as a picture. An lvalue makes `T` an lvalue reference and collapsing keeps the parameter an lvalue reference; an rvalue makes `T` a plain type and the parameter `T&&` an rvalue reference. `std::forward<T>(x)` then hands on the same category.*

**Example.** `sink` reports the value category its caller passed, using `std::is_lvalue_reference_v<T>` and the size of the string. It is called with a named `std::string` ("arm"), with a temporary `std::string("hand")` and with `std::move(name)`. What does each call print, and how is `T` deduced? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <string>
#include <type_traits>
#include <utility>

template <class T>
void sink(T&& x) {
  std::cout << (std::is_lvalue_reference_v<T> ? "lvalue" : "rvalue") << ' ' << x.size() << '\n';
}

int main() {
  std::string name = "arm";
  sink(name);                 // lvalue: T = std::string&
  sink(std::string("hand"));  // rvalue: T = std::string
  sink(std::move(name));      // std::move yields an rvalue again
}
```

**Solution.** The named string is an lvalue, so `T` is deduced as `std::string&` and the call prints `lvalue 3`. The temporary is an rvalue, so `T` is `std::string` and the call prints `rvalue 4`. `std::move(name)` casts the lvalue back to an rvalue, so `T` is `std::string` again and the call prints `rvalue 3` (`sink` only reads the size, so `name` still holds "arm"). The printed sizes (3, 4, 3) show that each call received its own string. The program prints:

```text
lvalue 3
rvalue 4
rvalue 3
```

### Fold expressions: the general case behind a sum

A fold expands a parameter pack with a binary operator. With pack elements $E_1,\dots,E_N$ (cppreference, *Fold expressions*): the unary right fold `(E op ...)` is $E_1\,\mathrm{op}\,(\cdots\mathrm{op}\,(E_{N-1}\,\mathrm{op}\,E_N))$, the unary left fold `(... op E)` is $(((E_1\,\mathrm{op}\,E_2)\,\mathrm{op}\cdots)\,\mathrm{op}\,E_N)$, and the binary forms add an initial value $I$ at the right or left end. For an empty pack a unary fold is only valid for `&&` (value `true`), `||` (value `false`) and `,` (value `void()`); for `+` it is ill-formed, so `(0.0 + ... + args)` is the safe form of a sum.

The direction matters for floating point because `+` on `double` is not associative. Between $2^{53}$ and $2^{54}$ doubles are spaced by 2, so $10^{16}+1$ is a tie and rounds to even, giving $10^{16}$. Then for the pack $(1,\,10^{16},\,-10^{16})$ the left fold gives $((1+10^{16})-10^{16})=0$ while the right fold gives $1+(10^{16}-10^{16})=1$; for $(10^{16},-10^{16},1)$ the two results swap. No fixed fold direction is numerically safe; if accuracy matters use compensated (Kahan) summation, or document the order.

![Left fold and right fold of the pack (1, 1e16, -1e16) step by step giving 0 and 1, and a number line of doubles near 1e16 spaced by 2 with 1e16 + 1 marked as a tie](/lesson-figures/CPP06-3.svg)

*Figure: the evaluation order of the two folds on the pack $(1,10^{16},-10^{16})$. In the left fold the 1 is added to $10^{16}$ first and is lost to the tie-to-even rule; in the right fold the large terms cancel first and the 1 survives (spacing of doubles after cppreference, Fold expressions, and the IEEE 754 round-to-even rule used in the text).*

**Example.** Subtraction is not associative, so the direction of a fold is visible even with integers. For the pack $(10,3,2)$ compute the left fold `(... - args)` and the right fold `(args - ...)`, and the binary fold `(0.0 + ... + args)` of an empty pack. Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>

template <class... Ts> auto lsub(Ts... args) { return (... - args); }       // ((a - b) - c)
template <class... Ts> auto rsub(Ts... args) { return (args - ...); }       // (a - (b - c))
template <class... Ts> double total(Ts... args) { return (0.0 + ... + args); }

int main() {
  std::cout << lsub(10, 3, 2) << ' ' << rsub(10, 3, 2) << ' ' << total() << '\n';
}
```

**Solution.** The left fold groups from the left: $(10-3)-2=7-2=5$. The right fold groups from the right: $10-(3-2)=10-1=9$. The binary fold of an empty pack leaves only the initial value, `0.0`, printed as `0`; a unary fold of an empty pack would be ill-formed for `+` (cppreference, *Fold expressions*), so the binary form is the safe one. The program prints:

```text
5 9 0
```

### constexpr: when an evaluation is not a constant expression

A call is evaluated at compile time only if every step is a *core constant expression*. Division by zero, reading outside an array, signed overflow, or evaluating a `throw` are not, so the compiler rejects them with a diagnostic in a `static_assert` or `constexpr` initializer, whereas at run time the same code has undefined behaviour (or throws). For example with GCC 11: `static_assert(10 / 0 == 0)` via a `constexpr` function reports `'(10 / 0)' is not a constant expression`. A useful consequence is that `constexpr` evaluation behaves like a free undefined-behaviour checker for the inputs you test. A `constexpr` function that is neither a template nor defaulted and for which *no* argument values give a constant expression is ill-formed, no diagnostic required (cppreference, *constexpr specifier*), so never write such a function and rely on the compiler to notice.

**Example.** A `constexpr` factorial `fact(n)` uses a 32-bit `int`. Does `static_assert(fact(12) == 479001600)` compile, and what happens to `static_assert(fact(13) > 0)` when the program is compiled with `-DTRY_13`? ($12!=479\,001\,600$ and $13!=6\,227\,020\,800$, the `int` maximum being $2^{31}-1=2\,147\,483\,647$.)

```cpp
constexpr int fact(int n) { return n <= 1 ? 1 : n * fact(n - 1); }

static_assert(fact(12) == 479001600);   // 12! fits in a 32-bit int
#ifdef TRY_13
static_assert(fact(13) > 0);            // 13! = 6227020800 does not
#endif

int main() {}
```

**Solution.** $12!=479\,001\,600<2\,147\,483\,647$, so the first `static_assert` compiles. $13!=6\,227\,020\,800>2\,147\,483\,647$ overflows a 32-bit `int`; signed overflow is not a constant expression, so with `-DTRY_13` the compiler stops at the second `static_assert`, whereas the same call at run time would silently be undefined behaviour. The compiler's answer to `g++ -std=c++20 -DTRY_13 -c fact.cpp` (g++ 11.4.0) is:

```text
fact.cpp:5:24: error: non-constant condition for static assertion
fact.cpp:5:19:   in ‘constexpr’ expansion of ‘fact(13)’
fact.cpp:5:24: error: overflow in constant expression [-fpermissive]
```

### Overload resolution and SFINAE: removing candidates instead of failing

When you call a function template, the compiler does not stop at the first template that does not fit. For each candidate template it substitutes the explicitly given and deduced arguments into the signature (return type, parameter types, template parameter declarations); if that substitution produces an invalid type or expression, the candidate is silently dropped from the overload set rather than reported as an error. This is *Substitution Failure Is Not An Error* (cppreference, *SFINAE*). Two conditions limit the rule. First, only failures in the **immediate context** of the signature are soft: if the substitution forces the instantiation of some other template (for example a class template whose body contains an error), that error is a hard error. Second, once the surviving candidates are known, ordinary overload resolution picks one; if none survives the call is an error.

A tiny example, compiled with g++ 11.4: `template <class C> auto size_of(const C& c) -> decltype(c.size())` and `template <class T, std::size_t N> std::size_t size_of(const T (&)[N])`. For a `std::vector<int>` of 3 elements the second candidate fails deduction and the first wins (`3`); for `int a[5]` the first candidate has no `a.size()` (an invalid expression in the immediate context) and is removed, and the second returns `5`. Writing the constraint inside the return type, `std::enable_if_t<...>` or a defaulted template parameter all exploit the same mechanism.

Compare the two tools. SFINAE chooses *between overloads*: the failing candidate disappears, and a different function with a different signature is called. `if constexpr` chooses *within one function body*: the signature is the same for all types and only the code inside the taken branch is instantiated. Prefer `if constexpr` when the types differ only in an implementation detail and `static_assert` when you want a type to be rejected with a message; reach for SFINAE (or a C++20 `requires` clause) when different overloads must exist for different type families and the caller should see the unconstrained candidates disappear. The cost of SFINAE is diagnostic quality: when every overload is removed the message lists all candidates and why each failed, which is the "40-line error" of the review prompt. A constraint written as a concept or a `static_assert` with a message turns the same information into one line.

![Four calls of to_text against two overloads: for each call each candidate is viable or removed, and the outcome is a result or a compile error when no candidate is left](/lesson-figures/CPP06-5.svg)

*Figure: overload resolution with SFINAE for the two overloads of the example below. A candidate whose return type is an invalid expression is removed, so each of the first three calls has exactly one survivor; the fourth call loses both candidates and is an error at the call site.*

**Example.** `to_text` has two overloads whose return types are `decltype(std::to_string(x))` and `decltype(x.name())`. Which candidates are viable for `to_text(42)`, `to_text(2.5)` and `to_text(Joint{"elbow"})`, what does the program print, and what does the compiler report if `main` also prints `to_text("x")`? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <string>

struct Joint { std::string label; std::string name() const { return label; } };

template <class T> auto to_text(const T& x) -> decltype(std::to_string(x)) { return std::to_string(x); }
template <class T> auto to_text(const T& x) -> decltype(x.name()) { return x.name(); }

int main() {
  std::cout << to_text(42) << ' ' << to_text(2.5) << ' ' << to_text(Joint{"elbow"}) << '\n';
}
```

**Solution.** For `42` and `2.5` the second candidate has an invalid return type (`int` and `double` have no `.name()`), so it disappears and the first returns `std::to_string`: `42` and `2.500000`. For a `Joint` the first candidate disappears (`std::to_string` has no overload for it) and the second returns the label `elbow`; each of these calls has exactly one viable candidate. For `to_text("x")` both candidates are removed, so no function is viable and the compiler reports the second block below, the line shown after the output. The program prints (first block), and the error comes from the extra call (second block):

```text
42 2.500000 elbow
```

```text
error: no matching function for call to ‘to_text(const char [2])’
```

## Worked example

Both cases use Welford's update and the interface checks of the theory above.

### Case 1: Welford on a small data set

**Problem.** Stream the values $2,4,4,4,5,5,7,9$ through Welford's update (section "A numerically sound generic: Welford"), starting from $\bar x_0=0$ and $M_0=0$. Find the mean, the sample variance and the population variance, and say what the compiler does when `RunningStats<int>` or `mean(std::vector<std::string>{})` is instantiated.

**Solution.**

1. *State the update.* For the $n$-th value $x_n$: $\delta=x_n-\bar x_{n-1}$, $\bar x_n=\bar x_{n-1}+\delta/n$, $M_n=M_{n-1}+\delta\,(x_n-\bar x_n)$ (Welford section). The first value gives $\delta=2-0=2$, $\bar x_1=0+2/1=2$, $M_1=0+2\cdot(2-2)=0$.
2. *Apply it to every value.* Each row of the table uses the previous row's $\bar x$ and $M$:

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

   For row 2: $\delta=4-2=2$, $\bar x_2=2+2/2=3$, $M_2=0+2\cdot(4-3)=2$.
3. *Read the final state.* After $n=8$ values the mean is $\bar x_8=5$ and $M_8=32$.
4. *Convert to variances.* The sample variance divides by $n-1$: $s^2=M_8/(n-1)=32/7\approx4.5714$. The population variance divides by $n$: $32/8=4$.
5. *Check the interface.* Instantiating `RunningStats<int>` triggers `static_assert(std::is_floating_point_v<T>)`, so the build stops with "RunningStats needs a floating-point type" instead of silently doing integer division in `delta / n`. `mean(std::vector<std::string>{})` stops at `static_assert(std::is_arithmetic_v<V>)` with the message of the author.

**Check.** The direct definition gives the same numbers: the deviations from 5 are $-3,-1,-1,-1,0,0,2,4$, whose squares sum to $9+1+1+1+0+0+4+16=32$, so $s^2=32/7$. The reference implementation below returns the mean 5 and the variance $32/7$ in its self-test.

**Takeaway.** One pass, $O(1)$ memory and no subtraction of large numbers: the update tracks the deviations from the running mean, and the template states its assumption (floating-point type) in the one place where it matters.

### Case 2: why the naive variance returns a negative number

**Problem.** Four readings $x=(10^9+4,\;10^9+7,\;10^9+13,\;10^9+16)$ have the exact mean $10^9+10$ and the exact sample variance $30$ (deviations $-6,-3,3,6$, squares sum to $90$, $90/3=30$). Compute the variance in `double` with the naive formula $(q-n\bar x^2)/(n-1)$, $q=\sum x^2$, explain the result, and compute it again with Welford's update.

**Solution.**

1. *Sums.* $s=\sum x=4{,}000{,}000{,}040$ is exactly representable, so $\bar x=s/4=1{,}000{,}000{,}010$ exactly. The exact $q=4\,000\,000\,080\,000\,000\,490$ and the exact $n\bar x^2=4\,000\,000\,080\,000\,000\,400$.
2. *Spacing of doubles.* Both numbers lie in $[2^{61},2^{62})$ ($2^{62}\approx4.61\times10^{18}$), where consecutive doubles are $2^{61-52}=512$ apart. The final rounding alone moves each by up to $256$ (half a spacing), and $q$ also accumulates four additions.
3. *What the machine stores.* In the actual run $q$ is stored as $4\,000\,000\,080\,000\,000\,000$ (error $-490$) and $n\bar x^2$ as $4\,000\,000\,080\,000\,000\,512$ (error $+112$). Their difference is $q-n\bar x^2=-512$ (computed in Python), whereas the exact difference is $490-400=90$. The two huge numbers agree to about $17$ significant digits but a double carries only $15$-$16$, so the subtraction exposes the rounding error instead of the signal.
4. *Divide.* $-512/(n-1)=-512/3=-170.67$. A variance cannot be negative; this is the visible symptom, and the dangerous case is when the error happens to be positive and the answer is merely wrong.
5. *Welford instead.* The running values $(n,\delta,\bar x_n,M_n)$ are $(1,\,4,\,1000000004,\,0)$, $(2,\,3,\,1000000005.5,\,4.5)$, $(3,\,7.5,\,1000000008,\,42)$, $(4,\,8,\,1000000010,\,90)$ (here $\delta$ is measured from the running mean, Welford section). Hence $M_4=90$ and $s^2=90/3=30$ exactly. Each term $\delta(x-\bar x)$ is a product of two numbers of size 1 to 10, never a difference of two numbers near $10^{18}$.
6. *Shift instead.* The variance does not change if a constant is subtracted from every value. Subtracting the first value gives $(0,3,9,12)$ with $s=24$, $q=234$, $n\bar x^2=4\cdot36=144$, and the naive formula gives $(234-144)/3=30$ without trouble.

**Check.** Python with exact fractions gives $90/3=30$ for the original data and the same for the shifted data; the double-precision naive formula gives $-170.666\ldots$ (the numerator printed as $-512.0$). The ratio in the explore block of the Welford section agrees: at offset $10^9$ the spacing divided by $n-1$ is $512/3\approx171$, about $5.7$ times the true variance.

**Takeaway.** Do the subtraction before the squaring, not after. Welford needs no knowledge of the data and runs in one pass; the shift needs a guess of the centre but is simpler. Both rest on the same principle.

![Left: number line near 4.00000008e18 with doubles 512 apart where q is stored as 0 and n*mean^2 as 512, so the naive difference is -512 instead of 90; right: Welford M_n equal to 0, 4.5, 42 and 90 and the variance 90/3 = 30](/lesson-figures/CPP06-4.svg)

*Figure: the numbers of Case 2. Left, offsets from $4\,000\,000\,080\,000\,000\,000$: hollow circles are the exact values (490 and 400), filled circles the stored doubles (0 and 512), so the stored difference is $0-512=-512$ against the exact $490-400=90$. Right, the running $M_n$ of Welford's update, each step adding a product of small numbers.*

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
3. **(Easy)** A compile-time table `make_cubes<N>()` stores the `int` cubes `i*i*i`. How many bytes does it occupy for $N=1200$ (assume 4-byte `int`), for which smallest index does `i*i*i` overflow a 32-bit signed int, and is $N=1200$ safe?
4. **(Medium)** *(Adapted from: C++ Core Guidelines, T.62 - place template definitions where they are visible)* A project defines `template <class T> T clamp_to(T, T, T);` in `util.h` and its body in `util.cpp`; `main.cpp` calls `clamp_to(3, 0, 5)` and the link fails. Explain the error, and give two fixes with their trade-offs.
5. **(Medium)** Find the numerical bug: the code below computes the variance of readings near $2\cdot10^9$ (for example a timestamp in nanoseconds). The true sample variance of $\{2\cdot10^9+6,\ 2\cdot10^9+18,\ 2\cdot10^9+21,\ 2\cdot10^9+23\}$ is 58. Predict the sign of the result, explain, and replace it with Welford's update.
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
12. **(Challenge)** Given `template <class T> void f(T&&); template <class T> void g(const T&&); template <class T> void h(T);` and `double d = 2.0; const double cd = 3.0; int b[4];`, state for each call the deduced `T` and the parameter type, or why it does not compile: `f(d)`, `f(cd)`, `f(d + 1)`, `f(std::move(d))`, `g(2.5)`, `g(d)`, `h(b)`, `h(cd)`, `h("ab")`. Then show, using reference collapsing, what `std::forward<T>(x)` returns inside `f` for `f(d)` and for `f(d + 1)`. (adapted from cppreference, Template argument deduction, "Deduction from a function call")
13. **(Challenge)** Define `lsum` as a unary left fold and `rsum` as a unary right fold of `+`. Evaluate both on `(2.0, 1e17, -1e17)` and on `(1e17, -1e17, 2.0)` in `double` and explain each result from the spacing of doubles near $10^{17}$. What happens for `lsum()` with an empty pack, and how do you fix the signature so an empty sum is `0.0`? Is there an argument order that makes both folds exact for every input? (adapted from cppreference, Fold expressions)
14. **(Challenge)** Make `clamp_to(T x, T lo, T hi)` accept `clamp_to(7, 0.0, 4.5)` by writing `lo` and `hi` as `typename id<T>::type`, with `template <class T> struct id { using type = T; };`. Predict `clamp_to(7, 0.0, 4.5)`, `clamp_to(1, 1.5, 3.5)` and `clamp_to(0.75f, 1, 2)` (value and deduced `T`). Explain why the fix is dangerous, and write a second version that accepts mixed argument types but rejects any call where a bound would be narrowed. (adapted from cppreference, Template argument deduction, "Non-deduced contexts")
15. **(Challenge)** `constexpr int arr[4] = {1,2,3,4};` and `constexpr int at(int i) { return arr[i]; }`. State which of `static_assert(at(3) == 4);` and `static_assert(at(4) == 0);` compile and what the run-time call `at(4)` does. Then write `at` so that an out-of-range index is a compile error in a constant expression and a thrown `std::out_of_range` at run time, with one function body, and explain why that works. Finally, why is a `constexpr` function that fails for all arguments a problem even if the compiler is silent? (source: cppreference, constexpr specifier, "Core constant expression" and the ill-formed-NDR rule)

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
3. Implement `make_squares<N>()` and confirm that the compiler evaluates `make_squares<9>()[8]` at compile time.
4. Implement `RunningStats<T>` with Welford's update; check the hand-computed values in the tests.
5. Implement the generic `mean` for `vector<int>`, `list<float>` and an empty container; test that a container of strings gives your `static_assert` message (try it separately, then remove the line).
6. Break it on purpose: compute variance with the naive formula and print the value for the `3e9 + x` data of the tests (x = 2, 5, 14, 15).

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
static_assert(clamp_to(9, 2, 6) == 6 && clamp_to(-4, 2, 6) == 2 && clamp_to(4, 2, 6) == 4);
static_assert(clamp_to(0.25, 0.0, 0.5) == 0.25);
static_assert(make_squares<9>()[8] == 64 && make_squares<9>()[0] == 0);
static_assert(deg2rad(180.0) > 3.14159 && deg2rad(180.0) < 3.1416);
static_assert(std::is_same_v<decltype(deg2rad(1.0f)), float>);

int main() {
  // hand-computed Welford data {3, 5, 5, 7, 10}: mean 6, sum of squared deviations 28 -> sample variance 7
  RunningStats<double> s;
  CHECK(s.count() == 0 && !s.mean() && !s.variance());
  s.push(3);
  CHECK(s.mean().value() == 3.0 && !s.variance());
  for (double x : {5.0, 5.0, 7.0, 10.0}) s.push(x);
  CHECK(s.count() == 5 && std::fabs(s.mean().value() - 6.0) < 1e-12);
  CHECK(std::fabs(s.variance().value() - 7.0) < 1e-12);
  // numerical stability: large offset, true variance of {2,5,14,15} is 42
  RunningStats<double> big;
  for (double x : {2.0, 5.0, 14.0, 15.0}) big.push(3e9 + x);
  CHECK(std::fabs(big.variance().value() - 42.0) < 1e-6);
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
3. $1200\cdot4=4800$ bytes. $1290^3=2{,}146{,}689{,}000$ fits, $1291^3=2{,}151{,}685{,}171>2{,}147{,}483{,}647$ overflows, so the first overflowing index is 1291. The largest index used for $N=1200$ is 1199, so the table is safe; for $N\ge1292$ the overflow would be a compile error in a constant expression.
4. The compiler compiled `main.cpp` without seeing the body, so it emitted a call to `clamp_to<int>`, but `util.cpp` never instantiated that specialization: undefined reference. Fix 1: move the body into the header (simple; every translation unit instantiates, longer compile times). Fix 2: explicit instantiation in `util.cpp` (`template int clamp_to<int>(int, int, int);`), which limits the allowed types but keeps compile times low.
5. The result is negative: $-2048/3\approx-682.7$ (computed in Python). Here $q\approx1.6\times10^{19}$ lies in $[2^{63},2^{64})$, where doubles are $2^{11}=2048$ apart; $q$ and $n\bar x^2$ are equal up to about 17 digits while a double carries about 16, so the difference is dominated by rounding error. A variance cannot be negative. The Welford update subtracts small quantities (the deviations) at every step, so cancellation is avoided; it returns 58.
6. Output: `int 1.5 other`. In the discarded branches `std::sqrt(x)` is never instantiated for `int` or `const char*`, thanks to `if constexpr`; with a plain `if` the call would have to compile for every `T`, and `std::sqrt(const char*)` fails. (`sqrt(2.25)=1.5`, `to_string` gives "1.500000", substr(0,3) is `1.5`.)
7. `static_assert(std::is_arithmetic_v<typename Container::value_type>, "mean needs a container of arithmetic values");` placed at the top of the function: the error is one line with your message. With C++20 `requires std::is_arithmetic_v<std::ranges::range_value_t<C>>` in the signature, the error is reported at the call site as an unsatisfied constraint, overload resolution can reject the candidate and pick another overload, and the constraint is visible in the documentation.
8. `a` is `int` (auto drops the reference and const), `b` is `const int&`, `c` is `const int&` (decltype(auto) keeps the declared type of the expression `r`), `d` is `int` (`std::move(i)` yields an rvalue, auto copies the value). Proofs: `static_assert(std::is_same_v<decltype(a), int>);` and so on.
9. Assumptions: `F` is callable with `T` and returns something convertible to `T` (a `static_assert(std::is_invocable_r_v<T, F, T>)`); `T` is floating point (`static_assert`); `n >= 1` (check at run time and throw/return an error); $a\le b$ finite; $f$ has a bounded second derivative on the interval. For the bound, $\max|f''|=\max|\sin|=1$, so $\frac{(\pi/2)^3}{12n^2}\le10^{-6}\Rightarrow n\ge\sqrt{3.8758/(12\cdot10^{-6})}=568.3$, so $n=569$ (the actual error with $n=569$ is about $6.4\times10^{-7}$).
10. In C++17 `std::sin` is not required to be `constexpr`; GCC folds it as a compiler extension while other compilers reject it. A portable replacement: `constexpr double taylor_sin(double x) { double term = x, sum = x; for (int k = 1; k < 12; ++k) { term *= -x * x / ((2 * k) * (2 * k + 1)); sum += term; } return sum; }`. Verify against `std::sin` on $[0,\pi/2]$ (and the wrapped range you will use): the maximum error there is about $3\times10^{-16}$. Accuracy degrades for large $|x|$, so reduce the argument first.
11. A good answer includes: a `constexpr std::array<double, 91>` built by a `constexpr` function; `static_assert(table[0] == 0.0)` and a bound check on `table[90]` (between 0.999999 and 1.000001); a loop over 0.01-degree steps computing linear interpolation between neighbours and the maximum absolute error against `std::sin` (about $\frac{h^2}{8}\max|f''|=\frac{(0.01745)^2}{8}\approx3.8\times10^{-5}$); the table size is $91\cdot8=728$ bytes; and a statement of the compile-time cost.
12. `f(d)`: `T = double&`, parameter `double&` (`double& &&` collapses to `double&`). `f(cd)`: `T = const double&`, parameter `const double&`. `f(d + 1)`: the sum is a prvalue, `T = double`, parameter `double&&`. `f(std::move(d))`: an xvalue, again `T = double`, parameter `double&&`. `g(2.5)`: `T = double`, parameter `const double&&`. `g(d)`: error, `const T&&` is not a forwarding reference, so `T = double` and the lvalue `d` cannot bind `const double&&` (GCC: `cannot bind rvalue reference of type 'const double&&' to lvalue of type 'double'`). `h(b)`: `T = int*` (the array decays). `h(cd)`: `T = double` (top-level `const` dropped). `h("ab")`: `T = const char*` (the array `const char[3]` decays). `std::forward<T>(x)` is `static_cast<T&&>(x)`: for `f(d)` it is `static_cast<double& &&>` = `double&`, an lvalue; for `f(d + 1)` it is `static_cast<double&&>`, an rvalue, so move semantics are only enabled when the caller passed an rvalue. (Checked with `static_assert(std::is_same_v<...>)` on the deduced types of all calls except `g(d)`, whose error message was read from g++ 11.4, `-std=c++17`.)
13. `lsum(2.0,1e17,-1e17)`: doubles in $[2^{56},2^{57})$, which contains $10^{17}$, are $2^{56-52}=16$ apart, so $2+10^{17}$ is only $2<8$ away from $10^{17}$ and rounds to it; then minus $10^{17}$ gives `0`. `rsum` of the same pack: $2+(10^{17}-10^{17})=2$. For `(1e17,-1e17,2.0)` the results swap: `lsum` $=0+2=2$, `rsum` $=10^{17}+(-10^{17}+2)=10^{17}+(-10^{17})=0$, because $-10^{17}+2$ also rounds to $-10^{17}$ (computed: `0` and `2` for the first pack, `2` and `0` for the second). Empty pack: `(... + args)` is ill-formed (GCC: `fold of empty expansion over operator+`); use the binary fold `(0.0 + ... + args)`, whose value for an empty pack is `0.0`. No order is exact for all inputs: whichever direction is used, the pair above shows an input where the sum in that direction is wrong; accuracy needs compensated summation or sorting by magnitude, not a choice of fold.
14. With `T` deduced from `x` only: `clamp_to(7, 0.0, 4.5)` has `T = int`, `lo = 0`, `hi = 4` (4.5 truncated), and returns `4` (computed), although clamping 7 to $[0,4.5]$ should give 4.5. `clamp_to(1, 1.5, 3.5)` gives `lo = 1`, `hi = 3` and returns `1` (computed), not 1.5. `clamp_to(0.75f, 1, 2)` has `T = float`, the `int` bounds convert exactly, and the result is `1.0f`: harmless. The danger is that the bounds are silently converted to the type of `x`. A safer version takes three independent types and refuses narrowing: `template <class T, class L, class H> constexpr T clamp_to(T x, L lo, H hi) { static_assert(std::is_same_v<std::common_type_t<T, L, H>, T>, "bounds would be narrowed"); return x < lo ? T(lo) : (x > hi ? T(hi) : x); }`. With it `clamp_to(7, 0.0, 4.5)` fails with `bounds would be narrowed`, while `clamp_to(0.75f, 1, 2)` and `clamp_to(7.0, 0, 4.5)` (which returns 4.5) still compile (checked with g++ 11.4). Trade-off: the `identity` trick is one line but converts silently; the three-parameter version rejects bad calls at compile time but needs an explicit `clamp_to<double>(7, 0, 4.5)` or a cast when promotion is really intended, and gives three template parameters to document.
15. `static_assert(at(3) == 4)` compiles. `static_assert(at(4) == 0)` is an error (GCC: `array subscript value '4' is outside the bounds of array 'arr'`), while the run-time call `at(4)` is undefined behaviour with no diagnostic. A single body: `constexpr int at(int i) { return (i >= 0 && i < 4) ? arr[i] : throw std::out_of_range("index"); }`. In a constant expression the throw branch is never taken for valid indices (so the call is constant), but for `at(4)` evaluation reaches the `throw`, which is not allowed in a constant expression, so the compiler reports `<throw-expression>` is not a constant expression; at run time the same branch throws `std::out_of_range` (verified with g++ 11.4: `at(2)` in `static_assert` compiles, `at(4)` in `static_assert` is rejected, and a run-time `at(argc+7)` throws). A `constexpr` function for which no argument gives a constant expression is ill-formed, no diagnostic required: the program is invalid but the compiler is not obliged to tell you, so the code can break on a different compiler or version.

## Further reading

- [cppreference: Templates](https://en.cppreference.com/w/cpp/language/templates) - deduction, specialization, and instantiation rules in detail.
- [cppreference: constexpr specifier](https://en.cppreference.com/w/cpp/language/constexpr) - what is allowed in constant expressions in each standard.
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - section T on templates and generic programming, and the rules on constants (Con) and `constexpr` (F.4).
- [cppreference: Template argument deduction](https://en.cppreference.com/w/cpp/language/template_argument_deduction) - forwarding references, adjustments of `P` and `A`, and the list of non-deduced contexts.
- [cppreference: Fold expressions](https://en.cppreference.com/w/cpp/language/fold) - the four fold forms and the rules for empty packs.

**More practice:** the quizzes on [LearnCpp: function templates](https://www.learncpp.com/cpp-tutorial/function-templates/), [templates in multiple files](https://www.learncpp.com/cpp-tutorial/using-function-templates-in-multiple-files/), [class templates](https://www.learncpp.com/cpp-tutorial/class-templates/), [constexpr functions](https://www.learncpp.com/cpp-tutorial/constexpr-functions/) and [constexpr if](https://www.learncpp.com/cpp-tutorial/constexpr-if-statements/) (answers shown on each page), the Core Guidelines [templates and generic programming](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#t-templates-and-generic-programming) section, and the Eigen page on [writing functions taking Eigen types](https://eigen.tuxfamily.org/dox/TopicFunctionTakingEigenTypes.html) (a real-world template-constraint problem).