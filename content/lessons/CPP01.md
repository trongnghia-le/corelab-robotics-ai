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
    },
    {
      "title": "C++ Core Guidelines (ES.46, ES.100-ES.107)",
      "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"
    },
    {
      "title": "cppreference: Arithmetic operators and usual arithmetic conversions",
      "url": "https://en.cppreference.com/w/cpp/language/usual_arithmetic_conversions"
    },
    {
      "title": "Goldberg: What Every Computer Scientist Should Know About Floating-Point Arithmetic",
      "url": "https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html"
    },
    {
      "title": "cppreference: List-initialization (narrowing conversions)",
      "url": "https://en.cppreference.com/w/cpp/language/list_initialization"
    },
    {
      "title": "cppreference: Default-initialization",
      "url": "https://en.cppreference.com/w/cpp/language/default_initialization"
    },
    {
      "title": "cppreference: Reference declaration (dangling references)",
      "url": "https://en.cppreference.com/w/cpp/language/reference"
    },
    {
      "title": "cppreference: Storage duration",
      "url": "https://en.cppreference.com/w/cpp/language/storage_duration"
    },
    {
      "title": "cppreference: std::vector::operator[]",
      "url": "https://en.cppreference.com/w/cpp/container/vector/operator_at"
    },
    {
      "title": "C++ working draft: [basic.fundamental], [expr.pre], [conv.integral], [dcl.init.list]",
      "url": "https://eel.is/c++draft/"
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

Picture memory as one long row of numbered bytes, and every variable as a stretch of that row with a type stamped on it. The type decides three things at once: how many bytes the object covers, how the bits in those bytes are read (a two's-complement integer, an IEEE 754 binary floating-point number, an address), and which operations the compiler accepts. The four bytes `00 00 80 3f` are the integer 1065353216 when read as an `int` and the number 1.0 when read as a `float`; nothing in the bytes says which, only the declaration does. This is the central difference from Python, where each object carries its type at run time and integers never overflow. In C++ the type is fixed at compile time and the arithmetic is carried out in the type the compiler derives from the operands, not in the type the programmer had in mind.

A concrete case. A robot travelled 9 m in 4 s. The program below stores the average speed in two ways, then subtracts 4 from the size of a vector of three readings. It was compiled with g++ 11.4.0 (`-std=c++20 -Wall -Wextra`) without any warning. Predict the three numbers it prints before reading on.

```cpp
#include <iostream>
#include <vector>

int main() {
    int meters{9};
    int seconds{4};
    double v1 = meters / seconds;
    double v2 = static_cast<double>(meters) / seconds;
    std::vector<int> w{10, 20, 30};
    std::cout << v1 << ' ' << v2 << ' ' << w.size() - 4 << '\n';
}
```

![A stack-like memory diagram: a double vector with size 3 and valid indices 0 to 2, plus integer versus floating division of 5 by 2.](/lesson-figures/CPP01.svg)

*Figure: types decide arithmetic. Integer `5 / 2` truncates to 2 while `5.0 / 2` keeps 2.5, and the valid indices of a vector stop at `size() - 1`; the cell after the last element exists in memory but is not part of the vector.*

**Check the prediction.** The program prints `2 2.25 18446744073709551615`. The first number is `2`, not `2.25`: both operands of `meters / seconds` are `int`, so the division is an integer division that returns 2, and only afterwards is that 2 converted to `2.0` for the `double` on the left of `=`. The second line casts one operand first, so the division is done in floating point and gives 2.25. The third number is not negative and not an error: `w.size()` has the unsigned type `std::size_t` (64 bits on this machine), so `3 - 4` wraps modulo $2^{64}$ to $2^{64}-1 = 18446744073709551615$.

Two wrong intuitions are behind most first-year C++ bugs. The first is "the type on the left of `=` decides the arithmetic": the result type follows the operands, and the destination only receives the finished value. The second is "if it compiles without warnings it has been checked": the compiler verified that the operations are legal for the types, not that the numbers mean what the author intended. The remaining sections turn these two pictures into rules: which type each expression has (conversions), how much error a floating-point result carries, how long an object lives, and what the program is allowed to do at the edge of a vector.

## Theory and derivation

A variable declaration introduces a typed object: `int count{3};` stores an integer, while `double dt{0.01};` stores an approximate real value. Initialize every local scalar before reading it. Integer division truncates toward zero: `5/2` is 2, whereas `5.0/2` is 2.5. Converting the truncated result to double afterward does not recover the lost fraction.

Functions declare a return type and typed parameters. Passing a vector by value copies it; `const std::vector<double>&` lets a function inspect the existing vector without mutation. The referenced object must remain alive during the call. Local scope determines where names are visible and when ordinary automatic objects are destroyed.

Use `std::vector` for a runtime-sized sequence. Its `size()` is a count, while valid indices run from zero through size minus one. `operator[]` does not check bounds; `.at()` does. Prefer range-based loops when the index has no separate meaning. Compile with warnings enabled and treat a warning as a question to resolve, not decoration.

### Objects, types and list-initialization

An *object* is a region of storage with a type; a declaration such as `T x{init};` creates it and fixes how its bits are read. Three forms of initialization matter in practice. *Default* initialization of a local scalar (`int n;`) leaves an indeterminate value, and reading it is undefined behaviour (cppreference, "Default-initialization", section "Indeterminate and erroneous values"). *Value* initialization (`int n{};`, `double d{};`) gives zero. *List* (brace) initialization `T x{v};` behaves like direct initialization with one extra rule: narrowing conversions are ill-formed (cppreference, "List-initialization", section "Narrowing conversions"; standard [dcl.init.list], paragraph 7 in the current working draft at eel.is/c++draft). A conversion is narrowing when it can change the value: floating point to integer, integer to floating point (unless the source is a constant that is stored exactly), or integer to an integer type that cannot hold every value of the source (unless a constant that fits). The equals form `int c = 9.99;` performs the same conversion silently; `-Wconversion` warns about it, `-Wall -Wextra` do not.

The working rule is to brace-initialize every object (C++ Core Guidelines ES.20 and ES.23) and to write `static_cast` wherever a narrowing is intended (ES.46), so that the lossy step is visible to the reader and to the compiler. Braces also remove one classic trap: in `int count{3.0 * 2}` the compiler rejects the initializer instead of storing 6 after silently converting a `double`.

**Example.** Compiled with g++ 11.4.0, `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>

int main() {
    int a{};
    double b{};
    int c = 9.99;
    std::cout << a << ' ' << b << ' ' << c << '\n';
}
```

The output is `0 0 9`: `{}` value-initializes both to zero, and `int c = 9.99;` keeps only the integer part, with no diagnostic. Replacing the last initialization by `int d{9.99};` stops the build with `error: narrowing conversion of '9.9900000000000002e+0' from 'double' to 'int' [-Wnarrowing]`. Adding `-Wconversion` to the first program produces `warning: conversion from 'double' to 'int' changes value from '9.9900000000000002e+0' to '9'`. The trailing digits are the stored binary value of 9.99.

### References, `const` and how arguments are passed

A reference is another name for an existing object. In `double mean(const std::vector<double>& v)` the name `v` is bound to the caller's vector and no copy is made (cppreference, "Reference declaration"). A reference must be initialized where it is declared and cannot be reseated afterwards; a reference to `const` refuses writes through that name, which turns "this function only reads" into a compiler-checked statement (Core Guidelines Con.1, F.16). Passing by value copy-initializes the parameter from the argument, so a vector with $n$ elements of $s$ bytes costs one allocation and $ns$ bytes of copying, $O(n)$ per call, whereas a reference costs one address (8 bytes on a 64-bit platform) whatever $n$ is. Guideline F.16 turns this into a rule of thumb: pass cheap-to-copy types such as `int`, `double` or `std::string_view` by value and everything larger by `const&`; F.17 uses a non-const reference for in-out parameters, and F.20 prefers a return value to an output parameter.

The price of a reference is lifetime. It does not own the object it names; if that object ends first, the reference *dangles* and using it is undefined behaviour (cppreference, "Reference declaration", section "Dangling references"; Core Guidelines F.43 forbids returning a reference to a local object). Inside a call the argument always outlives the parameter, so a `const&` parameter is safe; the danger begins when a reference is stored or returned.

**Example.** A point cloud of 250 000 `double` values is read by a function five times, once by value and once by `const&` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). The type counts its copies:

```cpp
#include <iostream>
#include <vector>

struct Cloud {
    std::vector<double> p;
    static inline int copies = 0;
    explicit Cloud(std::size_t n) : p(n, 1.0) {}
    Cloud(const Cloud& o) : p(o.p) { ++copies; }
};

double first_by_value(Cloud c) { return c.p[0]; }
double first_by_ref(const Cloud& c) { return c.p[0]; }

int main() {
    Cloud cloud(250000);
    for (int i = 0; i < 5; ++i) first_by_value(cloud);
    std::cout << "after 5 by-value calls: copies = " << Cloud::copies << '\n';
    Cloud::copies = 0;
    for (int i = 0; i < 5; ++i) first_by_ref(cloud);
    std::cout << "after 5 by-reference calls: copies = " << Cloud::copies << '\n';
    std::cout << "bytes per by-value call: " << cloud.p.size() * sizeof(double) << '\n';
}
```

Output: `after 5 by-value calls: copies = 5`, `after 5 by-reference calls: copies = 0`, `bytes per by-value call: 2000000`. Each by-value call allocates and fills 2 MB ($250\,000\times8$ B); at a rate of 60 Hz that is $2\times10^6\times60=120$ MB/s of traffic that the `const&` version does not generate.

### Scope and the lifetime of automatic objects

The *scope* of a name is the part of the program where it can be used; for a variable declared in a block it runs from the declaration to the closing brace (cppreference, "Scope"). The *lifetime* of an object is a run-time notion. An object with automatic storage duration, that is a local variable that is not `static`, is created when execution passes its definition and destroyed when execution leaves the block, in the reverse order of construction (cppreference, "Storage duration", section "Automatic storage duration"; standard [basic.stc.auto]). The storage comes from the call stack, so creating and destroying such an object costs a pointer adjustment and no allocation. This reverse-order guarantee is what the resource-management rules of the next lesson build on.

For locals, scope and lifetime coincide, but they are different ideas: a reference or pointer extends *access to* an object, never its *lifetime*. Reusing a name in a nested scope hides the outer one and is discouraged (Core Guidelines ES.12). A second consequence is that a function must not hand out the address of its own local variable, since the variable is gone when the function returns.

**Example.** A type that prints when it is created and destroyed makes the order visible (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <iostream>

struct Probe {
    const char* name;
    explicit Probe(const char* n) : name(n) { std::cout << "make " << name << '\n'; }
    ~Probe() { std::cout << "drop " << name << '\n'; }
};

int main() {
    Probe a("a");
    {
        Probe b("b");
        Probe c("c");
        std::cout << "inner block ends\n";
    }
    Probe d("d");
    std::cout << "main ends\n";
}
```

Output, in order: `make a`, `make b`, `make c`, `inner block ends`, `drop c`, `drop b`, `make d`, `main ends`, `drop d`, `drop a`. `c` was created last in the inner block and is destroyed first; `a` is created first and destroyed last.

### `std::vector`, `size()` and bounds

A `std::vector<T>` owns a contiguous array of `size()` elements. `size()` returns `std::size_t`, an unsigned type, and the valid indices are $0\le i<\texttt{size()}$. `v[i]` has the precondition $i<\texttt{size()}$ and performs no check: if the precondition is false, "the behavior is undefined" (cppreference, "std::vector::operator[]"). `v.at(i)` checks and throws `std::out_of_range` (cppreference, "std::vector::at"). The unchecked form is the default because it costs nothing, so the discipline has to come from elsewhere: a range-based `for` when the index has no meaning of its own (Core Guidelines ES.71), a checked access in tests, and a build with sanitizers (SL.con.3 asks to avoid bounds errors).

Undefined behaviour means that the standard places no requirement on the program, not that it crashes. A read one past the end may return stale data, return a neighbour's data, crash later or appear to work, and a different compiler flag can change which one happens. AddressSanitizer (`-fsanitize=address`) instruments heap and stack accesses and aborts at the first out-of-bounds access with a report that names the offending line and the size of the block; UndefinedBehaviorSanitizer (`-fsanitize=undefined`) reports other violations such as signed overflow. Both examine only the paths that actually run, so a clean run is evidence for those inputs and not a proof.

**Example.** A vector of three `int` values is read at index 3 (g++ 11.4.0, `-std=c++20 -Wall -Wextra -g -fsanitize=address,undefined`):

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{10, 20, 30};
    int i = 3;
    std::cout << v[i] << '\n';
}
```

The program compiles without a warning, and the run aborts with `AddressSanitizer: heap-buffer-overflow ... READ of size 4 ... t4.cpp:7` and `located 0 bytes to the right of 12-byte region`. The numbers agree with the layout: $3\times4=12$ bytes are allocated, and index 3 starts at byte offset 12, the first byte after the block. Without the sanitizer the same program would simply print whatever follows the array.

### Integer conversions, modular arithmetic and undefined overflow

Integer division is only one place where types change the numbers. The other is *conversion before arithmetic*. For a built-in binary operator, the operands are first promoted and then brought to a common type $C$ by the usual arithmetic conversions (cppreference, "Usual arithmetic conversions", Stage 5). If both are signed or both unsigned, $C$ is the one with the greater rank. If one is signed ($S$) and one unsigned ($U$): when the rank of $U$ is at least that of $S$, $C$ is $U$; otherwise, if $S$ can represent every value of $U$, $C$ is $S$; otherwise $C$ is the unsigned type matching $S$. So on a platform with 32-bit `int` and `unsigned int` of equal rank, `-3 < 7u` converts $-3$ to $2^{32}-3$ and is false.

Two different rules then apply to the result. *Unsigned* arithmetic is defined modulo $2^n$ for $n$ bits (cppreference, "Arithmetic operators", Overflows), so for `int x = -3; unsigned y = 7;`
$$x-y \equiv (2^{32}-3)-7 = 2^{32}-10 = 4294967286 \pmod{2^{32}},$$
exactly the value in the C++ Core Guidelines example (ES.100). *Signed* overflow is not wraparound: the behaviour is undefined, and a compiler may assume it never happens (ES.103; cppreference lists wrapping, trapping, saturating or being optimised out as possible manifestations). This is why "use `unsigned` so that a count can never be negative" (a tempting fix for `v.size() - 1`) is rejected by the guidelines (ES.106): the value is not prevented from being negative, it silently becomes a huge positive number, and it opens the door to the signed/unsigned mixes above. The guideline summary is: do arithmetic in signed types (ES.102), subscript with a signed index type or convert once at the boundary (ES.107), and make narrowing explicit (ES.46).

![A ring of the 2^32 unsigned values with 0 at the top, the signed reading of the upper half, and the arrows for -20 converted to unsigned and for subtracting 30.](/lesson-figures/CPP01-2.svg)

*Figure: unsigned 32-bit values live on a ring. Converting $-20$ to `unsigned` lands at $2^{32}-20$, the 20th step back from 0, and subtracting 30 moves 30 further steps back to $2^{32}-50 = 4294967246$.*

```explore
{
  "title": "Wrap-around of an n-bit unsigned type",
  "title_vi": "Tràn vòng của kiểu unsigned n bit",
  "prompt": "Predict first: with a 6-bit type (modulus 64) what unsigned value does a true difference of -50 become, and what does the same bit pattern mean when read as a signed number? Then move d across 0 and across the modulus.",
  "prompt_vi": "Dự đoán trước: với kiểu 6 bit (modulo 64), hiệu thật bằng -50 trở thành giá trị unsigned nào, và cùng dãy bit đó có nghĩa gì khi đọc như số có dấu? Sau đó kéo d qua 0 và qua giá trị modulo.",
  "params": [
    { "name": "n", "label": "bits n", "label_vi": "số bit n", "min": 3, "max": 8, "step": 1, "value": 6, "unit": "" },
    { "name": "d", "label": "true value x - y", "label_vi": "giá trị thật x - y", "min": -100, "max": 100, "step": 1, "value": -50, "unit": "" }
  ],
  "let": [
    { "name": "m", "expr": "2^n" },
    { "name": "w", "expr": "d - m*floor(d/m)" },
    { "name": "s", "expr": "w - m*step(w - m/2)" }
  ],
  "plot": {
    "x": { "name": "t", "min": -100, "max": 100, "label": "true value t = x - y", "label_vi": "giá trị thật t = x - y" },
    "y": { "label": "stored value", "label_vi": "giá trị lưu", "min": -110, "max": 260 },
    "series": [
      { "expr": "t", "label": "true value", "label_vi": "giá trị thật", "color": "grey" },
      { "expr": "t - m*floor(t/m)", "label": "unsigned result (t mod 2^n)", "label_vi": "kết quả unsigned (t mod 2^n)", "color": "orange" }
    ],
    "points": [
      { "x": "d", "y": "w", "label": "unsigned result", "label_vi": "kết quả unsigned", "color": "orange" }
    ]
  },
  "readouts": [
    { "label": "modulus 2^n", "label_vi": "modulo 2^n", "expr": "m", "unit": "", "digits": 0 },
    { "label": "unsigned result", "label_vi": "kết quả unsigned", "expr": "w", "unit": "", "digits": 0 },
    { "label": "same bits read as signed", "label_vi": "cùng dãy bit đọc như số có dấu", "expr": "s", "unit": "", "digits": 0 }
  ]
}
```

*The slider uses a few bits so that the pattern is visible; for the 32-bit `unsigned` of the text the modulus is 4294967296 and the sawtooth has the same shape.* Predict-first answer: $-50\bmod 64=14$, and the pattern 14 has a clear top bit of zero, so it reads as $+14$ in a signed type too; moving $d$ to $-20$ gives $44$, which reads as $-20$ because $44\ge32$.

**Example.** On a 64-bit Linux machine with g++ 11.4.0 (`int` 32 bits), a signed value $-20$ meets an unsigned value 30:

```cpp
#include <iostream>

int main() {
    int a = -20;
    unsigned b = 30;
    std::cout << a - b << '\n';
    std::cout << (a < b) << '\n';
    long long c = -20;
    std::cout << (c < b) << '\n';
    std::cout << static_cast<int>(a - b) << '\n';
}
```

Output: `4294967246`, `0`, `1`, `-50`. `int` and `unsigned int` have equal rank, so $a$ becomes $2^{32}-20=4294967276$ and the difference is $4294967276-30=4294967246=2^{32}-50$. The comparison `a < b` is therefore $4294967276<30$, false, and `-Wall -Wextra` reports it (`-Wsign-compare`). With `long long c` the common type is `long long`, which holds every `unsigned int`, so the comparison is $-20<30$ and is true. Casting the unsigned result back to `int` returns $-50$, because the conversion yields the value congruent modulo $2^{32}$ ([conv.integral], paragraph 3). A related program, `int square(int x) { return x * x; }` called with `square(50000)`, is undefined behaviour because $2\,500\,000\,000>2^{31}-1$: GCC with `-fsanitize=undefined` reports `signed integer overflow: 50000 * 50000 cannot be represented in type 'int'`, and without it prints the wrapped value $-1794967296=2\,500\,000\,000-2^{32}$, which is only one of the permitted outcomes.

### A floating-point error model and the price of a sum

Binary floating point rounds every operation. For IEEE double with round-to-nearest, each basic operation returns $\mathrm{fl}(a\circ b)=(a\circ b)(1+\delta)$ with $|\delta|\le u=2^{-53}\approx1.1\times10^{-16}$ (for `float`, $u=2^{-24}\approx6\times10^{-8}$). This is Goldberg's relative-error model (Goldberg, *What Every Computer Scientist Should Know About Floating-Point Arithmetic*, section "Errors In Summation").

Apply it to the recursive sum $s_1=x_1$, $s_i=\mathrm{fl}(s_{i-1}+x_i)=(s_{i-1}+x_i)(1+\delta_i)$. Unrolling and dropping second-order terms gives
$$s_n=\sum_{j=1}^{n}x_j\,(1+\theta_j),\qquad |\theta_j|\lesssim (n-j+1)\,u,$$
because $x_j$ passes through the additions $j,\dots,n$ and each one perturbs it by a factor $(1+\delta_i)$ (the first term is perturbed by about $nu$, the last by $u$). Hence
$$\Bigl|s_n-\sum x_j\Bigr|\;\lesssim\;u\sum_{j}(n-j+1)|x_j|\;\le\;\frac{n(n+1)}{2}\,u\,\max_j|x_j|.$$
The worst case grows like $n^2u$, and typical random rounding errors grow more like $\sqrt n\,u$, but a systematic bias (adding $0.1$ over and over) can approach the worst case. Kahan's compensated summation carries the lost low-order bits in a correction $c$ and, by Goldberg's Theorem 8 (section "Optimizers"), perturbs each summand by only about $2u+O(nu^2)$ instead of $(n-j+1)u$. The proof relies on $(t-s)-y$ being non-zero: an optimiser that treats floating point like real algebra rewrites it to $0$ and destroys the algorithm, which is why `-ffast-math` must not be used on such code.

![Two staircase curves of the spacing between neighbouring floating-point numbers against magnitude, for float and double, with the points 1e8 and 1e14 marked.](/lesson-figures/CPP01-3.svg)

*Figure: the gap between adjacent numbers ($\mathrm{ulp}$) doubles each time the magnitude doubles. A double near $10^8$ resolves $1.5\times10^{-8}$, a double near $10^{14}$ only $1.6\times10^{-2}$; a `float` near $1.7\times10^{7}$ already steps by 2.*

**Example.** The rounding model predicts three things that can be seen in 8 lines (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <cmath>
#include <iomanip>
#include <iostream>

int main() {
    float f = 16777216.0f;                       // 2^24
    double d = 1.0e16;
    std::cout << std::setprecision(17);
    std::cout << (f + 1.0f == f) << ' ' << (d + 1.0 == d) << '\n';
    std::cout << 0.1 + 0.2 << ' ' << (0.1 + 0.2 == 0.3) << '\n';
    std::cout << std::nextafter(f, 1e30f) - f << ' ' << std::nextafter(d, 1e30) - d << '\n';
}
```

Output: `1 1`, `0.30000000000000004 0`, `2 2`. Above $2^{24}=16\,777\,216$ a `float` can no longer represent every integer, so adding 1 changes nothing (the exact sum lies halfway between two floats and rounds back to the even neighbour); a `double` shows the same at $10^{16}$, where the spacing is 2. `0.1 + 0.2` is not `0.3` because each of the three decimal constants is stored with a relative error of up to $u=2^{-53}$, which is why equality of computed doubles must be tested with a tolerance chosen from the scale of the data.

### Three moving averages and where their errors come from

The lesson gives the direct window mean, the streaming update $S_{k+1}=S_k-x_k+x_{k+w}$ and the prefix-sum form $y_k=(P_{k+w}-P_k)/w$. Their floating-point errors scale differently.

- *Direct*: apply the bound above to the $w$ terms of one window and divide by $w$: the error of the mean is at most about $\tfrac{w+1}{2}\,u\max|x|$, whatever the length of the signal.
- *Streaming*: the error in $S_k$ accumulates over all earlier updates and is never removed, so after $k$ steps it can be about $k\,u\,\max|S|$ in the worst case and $\sqrt{k}\,u\,\max|S|$ typically (the drift of Exercise 9).
- *Prefix sums*: $P_n$ can be much larger than any window sum, so $P_{k+w}$ and $P_k$ are each rounded at the scale $\mathrm{ulp}(P_n)/2$, and their difference, which is small, is a *catastrophic cancellation* in Goldberg's sense (section "Cancellation": subtracting two quantities that are already subject to rounding error). The error in $y_k$ is therefore about $\mathrm{ulp}(P_n)/w$, however short the window.

The remedy that costs almost nothing is to subtract a reference value first, for example $x_0$ or a running mean estimate, accumulate $x_i-x_0$, and add it back at the end: the sums are then of the size of the *variation*, not of the *offset*. Exercise 14 measures this effect.

**Example.** A tiny signal that rides on a very large offset exposes the three variants (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). With $x=\{10^{16},1,1,1,1\}$ and $w=2$ the exact window means are $5\times10^{15}+0.5$, then 1, 1, 1:

```cpp
#include <iostream>
#include <vector>

int main() {
    const std::vector<double> x{1e16, 1, 1, 1, 1};
    const std::size_t w = 2;
    std::vector<double> p(x.size() + 1, 0.0);
    for (std::size_t i = 0; i < x.size(); ++i) p[i + 1] = p[i] + x[i];
    double s = x[0] + x[1];                       // streaming window sum
    for (std::size_t k = 0; k + w <= x.size(); ++k) {
        double direct = (x[k] + x[k + 1]) / 2.0;
        double prefix = (p[k + w] - p[k]) / 2.0;
        double stream = s / 2.0;
        std::cout << "k=" << k << " direct=" << direct << " streaming=" << stream
                  << " prefix=" << prefix << '\n';
        if (k + w < x.size()) s = s - x[k] + x[k + w];
    }
}
```

The output has four lines: `k=0 direct=5e+15 streaming=5e+15 prefix=5e+15`, then for $k=1,2,3$ the same triple `direct=1 streaming=0.5 prefix=0`. The direct mean is exact for the three small windows. The streaming sum started as $10^{16}+1$, which rounds to $10^{16}$ (the spacing there is 2), so after subtracting $x_0=10^{16}$ it holds 0 instead of 1 and stays wrong by 1 forever, giving 0.5. The prefix sums never see the 1's at all because each addition to $P\approx10^{16}$ rounds back to $P$, so $P_{k+w}-P_k=0$. The remedy of the text, subtracting $x_0$ first, makes the data $\{0,1,1,1,1\}$, for which all three variants are exact.

## Worked example

### Case 1: an integer division hides a fraction

**Problem.** A program declares `int steps{5};` and `int total{2};` and must store the ratio of the two as a `double`. The first version is `double ratio = steps / total;`. State the value it stores and say what has to change to obtain 2.5.

**Solution.**

1. *Find the operand types.* Both operands of `/` are `int` (declarations above).
2. *Apply the usual arithmetic conversions* (cppreference, "Usual arithmetic conversions"; [expr.arith.conv]). Both operands already have the same type, so no conversion happens, and the built-in `/` for `int` returns an `int` that is the quotient truncated toward zero: $5=2\cdot2+1$, so the result is 2 with remainder 1.
3. *Perform the assignment.* The `int` value 2 is converted to `double` and stored as 2.0 exactly. The type `double` on the left plays no role in step 2: it only receives the finished value.
4. *Convert before dividing.* Write `static_cast<double>(steps) / total`. Now the operands are `double` and `int`, the `int` is converted to `double` (usual arithmetic conversions again), and the division is $5.0/2.0=2.5$.
5. *Run it.* Compiled with g++ 11.4.0 (`-std=c++20 -Wall -Wextra`), the program

```cpp
#include <iostream>

int main() {
    int steps{5};
    int total{2};
    double ratio_int = steps / total;
    double ratio_fp = static_cast<double>(steps) / total;
    std::cout << ratio_int << ' ' << ratio_fp << '\n';
}
```

prints `2 2.5`.

**Check.** Python gives `5 // 2 = 2` with `5 % 2 = 1`, and `5 / 2 = 2.5`. The identity $\text{steps}=\text{total}\cdot q+r$ confirms the split: $2\cdot2+1=5$. A limiting case shows when the bug is invisible: with `steps = 4` both versions give 2, so a test whose inputs are all divisible would pass the broken code.

**Takeaway.** The operand types choose the arithmetic; the destination type only receives the result. The same care applies to a `mean` of an empty vector, which must be rejected before any division.

### Case 2: encoder speed across a timer wrap-around

**Problem.** An encoder with 4096 counts per revolution advances by 37 counts between two readings of a free-running 32-bit microsecond timer (`std::uint32_t`). The first reading is $t_0=4\,294\,967\,000$ µs, the second $t_1=1200$ µs: the timer wrapped once in between (it wraps every $2^{32}\,\mu s\approx71.6$ min). Compute the shaft speed in rad/s and in rpm, and show what two typical coding mistakes would return.

**Solution.**

1. *Elapsed time.* The two readings have type `std::uint32_t` (here `unsigned int`), so `t1 - t0` is unsigned arithmetic, defined modulo $2^{32}$ ([basic.fundamental], paragraph 2; cppreference, "Arithmetic operators", Overflows). Substituting: $\Delta t=(1200-4\,294\,967\,000)\bmod 2^{32}=1200+(4\,294\,967\,296-4\,294\,967\,000)=1200+296=1496\ \mu s$. This is valid as long as the true interval is shorter than $2^{32}$ µs.
2. *Angle turned.* One count is $2\pi/4096$ rad. In code the count and the number of counts per revolution are `int`, so the fraction must be formed in floating point: `static_cast<double>(37) / 4096`, then $\Delta\theta=37\cdot\frac{2\pi}{4096}=0.056757$ rad. Written as `37 / 4096 * 2.0 * pi` the integer division gives 0 first.
3. *Speed.* $\omega=\Delta\theta/\Delta t=0.056757\ \text{rad}/(1.496\times10^{-3}\ \text{s})=37.9394$ rad/s.
4. *Convert units.* $37.9394\ \text{rad/s}\times\dfrac{60}{2\pi}=362.29$ rpm.
5. *Run it.* The program below (g++ 11.4.0, `-std=c++20 -Wall -Wextra`) also computes the two wrong versions:

```cpp
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>

constexpr double kPi = 3.14159265358979323846;

int main() {
    const int counts_per_rev = 4096;
    const int delta_counts = 37;
    const std::uint32_t t0 = 4294967000u;   // microseconds, just before the 32-bit timer wraps
    const std::uint32_t t1 = 1200u;         // microseconds, just after

    const std::uint32_t dt_us = t1 - t0;    // modulo 2^32
    const double dt_wrong = static_cast<double>(t1) - static_cast<double>(t0);
    const double w_int = delta_counts / counts_per_rev * 2.0 * kPi / (dt_us * 1e-6);
    const double w = static_cast<double>(delta_counts) / counts_per_rev * 2.0 * kPi / (dt_us * 1e-6);

    std::cout << std::fixed << std::setprecision(4);
    std::cout << "dt_us = " << dt_us << "\n";
    std::cout << "dt from doubles = " << dt_wrong << "\n";
    std::cout << "w (int division) = " << w_int << " rad/s\n";
    std::cout << "w = " << w << " rad/s\n";
}
```

Output: `dt_us = 1496`, `dt from doubles = -4294965800.0000`, `w (int division) = 0.0000 rad/s`, `w = 37.9394 rad/s`.

![The 2^32 microsecond timer drawn as a ring with the reading t0 just before the wrap and t1 just after, the two arcs of 296 and 1200 microseconds, and the three computed results.](/lesson-figures/CPP01-4.svg)

*Figure: the interval is the arc from $t_0$ across the wrap to $t_1$: $296+1200=1496$ µs. Converting to `double` before subtracting gives a negative interval; integer division gives zero speed; the correct order gives 37.94 rad/s.*

**Check.** A second method unwraps by hand: $t_1+2^{32}=4\,294\,968\,496$, and $4\,294\,968\,496-4\,294\,967\,000=1496$ µs. An order-of-magnitude check: $37/4096=0.00903$ rev in 1.496 ms is 6.04 rev/s, i.e. 362 rpm, matching step 4. Python reproduces $\omega=37.93936$ rad/s.

**Takeaway.** Unsigned wrap-around is a feature when it is used deliberately for a timer difference (subtract first, in the unsigned type), and a bug when the same values are first widened or mixed with signed quantities.

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

11. **(Challenge)** **Conversions decide the comparison.** On a 64-bit Linux machine (`int` 32 bits, `long` and `std::size_t` 64 bits), predict each result and name the common type chosen by the usual arithmetic conversions: (a) `-3 - 7u` printed as an unsigned number; (b) `-3 < 7u`; (c) `int i = -1; std::vector<int> v{1,2,3}; i < v.size()`; (d) `-1LL < 3u`; (e) `short s = -1; unsigned short us = 1; s < us`; (f) `-1L < 1UL`. Derive (a) with modular arithmetic. Then rewrite (c) in two ways that cannot give a surprising answer, and say which the Core Guidelines prefer for subscripts. Compile with `-Wall -Wextra` and report which of the six lines the compiler warns about. (adapted from C++ Core Guidelines, ES.100 and ES.106; cppreference, "Usual arithmetic conversions", Stage 5)
12. **(Challenge)** **Overflow is not wraparound.** Consider `int area(int h, int w) { return h * w; }` called as `area(10'000'000, 100'000'000)`. (a) Compute the true product and its residue modulo $2^{32}$, and the `int` value a two's-complement machine would show if it wrapped. (b) State precisely what the C++ standard says about this call, in contrast to the same computation done on `unsigned`. (c) For `bool f(int x) { return x + 1 > x; }` and `f(INT_MAX)`, say what you expect from an optimiser, then compile with GCC at `-O0`, at `-O2`, at `-O2 -fsanitize=undefined` and at `-O2 -fwrapv` and report the four answers. (d) Give a version of `area` whose contract is checkable and that cannot overflow for the inputs you accept, and the largest square side that `int` can hold. (adapted from C++ Core Guidelines, ES.103; cppreference, "Arithmetic operators", Overflows)
13. **(Challenge)** **Summing $10^7$ copies of 0.1.** (a) Derive, to first order, the bound $\bigl|s_n-\sum x_j\bigr|\lesssim u\sum_j (n-j+1)|x_j|$ for recursive summation. (b) Evaluate it for $n=10^7$, $x_j=0.1$ in `float` ($u=2^{-24}$) and in `double` ($u=2^{-53}$). (c) Write the loops in `float`, in `double`, and a Kahan-compensated `float` version, and report the three results and their errors against $10^7\cdot$`0.1f` (the exact product of the stored value). (d) Rebuild with `-O2 -ffast-math` and explain what happens to the Kahan result, using the identity $C=((S+Y)-S)-Y$. (adapted from Goldberg, *What Every Computer Scientist Should Know About Floating-Point Arithmetic*, sections "Errors In Summation" and "Optimizers", Theorem 8)
14. **(Challenge)** **Prefix sums with an offset.** Let $x_i = 10^8 + k_i/100$ with $k_i=(37i)\bmod 101$ for $i<n=10^6$, and window $w=10$. (a) Predict, before running, the order of magnitude of the error of the prefix-sum moving average $y_k=(P_{k+w}-P_k)/w$ in `double`, using $\mathrm{ulp}(P_n)$, and explain it as catastrophic cancellation. (b) Compute an exact reference with 64-bit integers in units of $0.01$. (c) Measure the maximum absolute error of the prefix-sum, the streaming-sum and the direct-sum versions, and of a prefix-sum version that accumulates $x_i-x_0$. (d) Say which version you would ship for a 1 kHz velocity signal that rides on a large offset, and what test would have caught the problem. (adapted from Goldberg, section "Cancellation" (catastrophic versus benign cancellation); the signal is constructed for this exercise)

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

Check each numeric claim of this lesson twice, by two routes. For a conversion, predict the common type from the rules and then print `typeid(a + b).name()` or `static_assert(std::is_same_v<decltype(a + b), unsigned>)`. For a floating-point sum, compare against an exact reference computed in 64-bit integers (units of 0.01, say) or in Python's `fractions.Fraction`, and state the tolerance as a multiple of $u\cdot|x|$, not as a fixed number. For a moving average, test the four boundary cases (`w == 1`, `w == n`, `w == 0`, `w > n`) and the invariants from the lab: output length $n-w+1$, `w == 1` returns the input, `w == n` returns the mean, and adding a constant to the input adds the same constant to the output. Rebuild with `-Wall -Wextra -Wpedantic` and then with `-fsanitize=address,undefined -g`; deliberately change `<=` to `<` in a loop bound and confirm that a test fails. A sanitizer that stays silent proves only that the executed paths were clean.

## Failure modes

- **Integer division before conversion:** `double r = a / b;` with two `int` operands truncates; the symptom is a velocity or ratio that is exactly an integer, and tests whose inputs are all divisible do not show it.
- **Unsigned wrap in a loop condition:** `for (std::size_t i = n - 1; i >= 0; --i)` never ends, and `v.size() - 1` on an empty vector is $2^{64}-1$. With g++ 11.4.0, `-Wextra` flags the `>= 0` (`-Wtype-limits`) but says nothing about the wrapped subtraction.
- **Signed overflow treated as wrap-around:** `x + 1 > x` may be folded to `true` by the optimiser, so a "wrap-around check" disappears at `-O2` while it works at `-O0`; the sanitizer can stay silent when the comparison has already been folded.
- **Uninitialized local:** `int n;` followed by a read is undefined; `-Wall` warns only in simple cases.
- **Out-of-range `operator[]`:** undefined behaviour with no exception; use `.at()` in tests or run the sanitizer build.
- **Floating-point equality and drift:** `sum == 1.0` after repeated additions, a streaming window sum that never recovers from one rounding error, and prefix sums of data riding on a large offset.
- **A dangling reference:** a function that returns a `const&` to a local variable, or a reference stored longer than the object it names.

## Alternatives and trade-offs

- **Fixed-width integers or doubles.** Encoder counts, timestamps and sensor register values are integers with a known width: `std::int32_t` and `std::uint32_t` make the modulus explicit and keep the arithmetic exact; `double` is the right type for physical quantities after conversion. Mixing the two is where the bugs of this lesson live.
- **Signed sizes.** `std::ssize(v)` (C++20) or a `std::ptrdiff_t` index avoids the signed/unsigned mix at the price of a conversion at the library boundary (Core Guidelines ES.100 to ES.107).
- **`operator[]` versus `.at()` versus a range-based `for`.** Unchecked access is fastest, `.at()` reports the error as an exception, and a range-based `for` removes the index altogether.
- **Three moving averages.** Direct sums cost $O(nw)$ but are accurate; streaming costs $O(n)$ and accumulates drift; prefix sums cost $O(n)$ with a large-offset hazard. Kahan summation or subtracting a reference value restores accuracy at small cost, and `long double` or integer accumulators are the heavy-duty alternatives.
- **Python versus C++ for the same job.** Python integers never overflow and its floats are the same IEEE doubles; C++ gives control over types and memory at the cost of the undefined-behaviour rules of this lesson.

## Transfer and retention

Compute a moving average for sampled motor velocity. State your numeric type, input contract, boundary behavior, and one test that catches integer truncation.

Close the reference before trying. Without looking, write the type and value of each of these expressions on a 64-bit Linux machine: `7 / 2`, `7 / 2.0`, `-1 < 1u`, `std::vector<int>{}.size() - 1`, `1e16 + 1 == 1e16`. Explain one way each answer could change on another platform (for example, a 32-bit `std::size_t` or `long`). Return after at least a week and reconstruct the conversion rules, the rounding model and the three moving averages from a blank page, then check against the lesson.

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

11. (Results from a g++ 11.4.0 run on 64-bit Linux.) (a) The common type is `unsigned int` (equal rank, so $U$ wins): $-3\mapsto 2^{32}-3$, and $(2^{32}-3)-7=2^{32}-10=4294967286$. (b) `-3 < 7u` is **false** (0), because $-3$ becomes $4294967293$. (c) **false**: the common type is `unsigned long` (`std::size_t`), and $-1$ becomes $2^{64}-1$. (d) **true**: `long long` outranks `unsigned int` and can represent every `unsigned int`, so the common type is `long long` and $-1<3$. (e) **true**: both `short` types are promoted to `int` first, so the comparison is $-1<1$ in `int`. (f) **false**: `long` and `unsigned long` have equal rank, so the common type is `unsigned long` and $-1\mapsto 2^{64}-1$. Safe rewrites of (c): `i < static_cast<int>(v.size())` (convert once, at the boundary, acceptable while `size` fits in `int`), or use a signed index/size type such as `std::ptrdiff_t n = std::ssize(v)` (C++20) or `gsl::index`, which is what ES.107 recommends for subscripts. With g++ 11.4.0 and `-Wall -Wextra` (`-Wsign-compare`), the warnings fire for (b), (c) and (f) only; (a) is a plain unsigned subtraction, (d) mixes types where the signed one can hold every value, and in (e) both operands are promoted to `int`. So the compiler does not catch every surprise: (a) is silently wrong for a reader who expected $-10$.
12. (a) The true product is $10^{15}$. Modulo $2^{32}$ it is $2764472320$, which read as a two's-complement `int` is $2764472320-2^{32}=-1530494976$ (computed in Python, and the same bits were produced by a cast in C++). (b) For `int`, signed overflow is **undefined behaviour**: the standard imposes no requirement, and wrapping to $-1530494976$ is only one possible manifestation (cppreference lists wrapping, trapping, saturating and being optimised away). For `unsigned`, the same product is defined: it is the residue $2764472320$. (c) A conforming optimiser may assume `x + 1` does not overflow and fold the comparison to `true`. With GCC 11.4.0 on `f(INT_MAX)` the observed results were: `-O0` gives 1, `-O2` gives 1, `-O2 -fsanitize=undefined` gives 1 with no diagnostic (the comparison was already folded to `true`, so no overflow is executed), and `-O2 -fwrapv` gives 0 (wraparound is now the defined behaviour). The lesson: a sanitizer that stays silent does not prove that overflow is absent. (d) For example `std::int64_t area(std::int32_t h, std::int32_t w) { if (h < 0 || w < 0) throw std::invalid_argument("negative"); return static_cast<std::int64_t>(h) * w; }`: the widened product of two non-negative 32-bit values is below $2^{62}$, so it cannot overflow. If the result must remain an `int`, check `h <= INT_MAX / w` (for `w > 0`) before multiplying. The largest square side that fits is $\lfloor\sqrt{2^{31}-1}\rfloor=46340$ (Python `math.isqrt`).
13. (a) With $s_i=(s_{i-1}+x_i)(1+\delta_i)$, $|\delta_i|\le u$, induction gives $s_n=\sum_j x_j\prod_{i=\max(j,2)}^{n}(1+\delta_i)$. A product of $m$ factors $(1+\delta_i)$ equals $1+\theta$ with $|\theta|\le mu+O(u^2)$, and $x_j$ meets $n-j+1$ factors (for $j\ge2$; $x_1$ meets $n-1$), so $|\theta_j|\lesssim(n-j+1)u$; summing $|x_j\theta_j|$ gives the bound. (b) For equal terms $\sum_j(n-j+1)=n(n+1)/2$, so the bound is $0.1\cdot\frac{n(n+1)}{2}\,u$. For $n=10^7$ this is $298023.25$ for `float` and $5.55\times10^{-4}$ for `double` (Python). (c) Measured: `float` naive $=1087937.0$, an error of $+87936.99$ relative to $10^7\cdot$`0.1f` $=1000000.0149$ (within the bound of $2.98\times10^5$ but far from small); Kahan `float` $=1000000.0$, error $-0.0149$ (the `float` result is rounded to the nearest representable value); `double` naive $=999999.999839$, error $-1.61\times10^{-4}$ against $10^6$ (within $5.55\times10^{-4}$). So Kahan in `float` beats naive summation in `double` here, consistent with the $2u$ bound being better than $(n-j+1)u$. (d) With `-O2 -ffast-math` the Kahan loop returned $1087937.0$, the same as naive: the compiler may use real-number algebra, rewrite $C=((S+Y)-S)-Y$ to $0$, and the correction disappears (Goldberg, section "Optimizers"). Either keep compensated summation out of `-ffast-math` translation units, or add `-fno-associative-math` (with it, the same GCC 11.4.0 build gave Kahan $=1000000.0$ again).
14. (a) $P_n\approx10^{14}$ (measured $P_n=100000000499999.9$), whose ulp is $2^{46-52}=0.015625$. Each $P_k$ is rounded to within about half an ulp (and the errors accumulate over earlier additions), and $y_k$ subtracts two such values to obtain a window sum near $10^9$ and then divides by $w=10$, so the error is expected at about $\mathrm{ulp}(P_n)/w\approx1.6\times10^{-3}$, much larger than the $\mathrm{ulp}(10^8)=1.5\times10^{-8}$ resolution of the data. This is catastrophic cancellation: the operands already carry rounding error far larger than the difference's own resolution. (b) Store $c_i=10^{10}+k_i$ (units of $0.01$) in `std::int64_t`; the exact window sum is a sum of $w$ of them (below $10^{12}$), then $y_k=\text{sum}/(100w)$. (c) Measured maxima over all windows: prefix sums $2.41\times10^{-3}$, streaming sum $3.66\times10^{-3}$, direct sum (sampled every 1000th window) $2.98\times10^{-8}$, prefix sums of $x_i-x_0$ $1.49\times10^{-8}$. The last two are at the level of the representation error of the inputs themselves (half an ulp of $10^8$ is $7.5\times10^{-9}$). The streaming version suffers because $S_k\approx10^9$ and its rounding error never leaves; the prefix version because $P_n$ is $10^5$ times bigger than a window sum. (d) Ship the direct sum for small $w$ (cost $O(nw)$ is trivial at 1 kHz) or the shifted prefix sum when $w$ is large, and add a regression test with a large offset and a small variation (compare with an integer or `long double` reference to a tolerance proportional to $u\cdot|x|$, not to $\max|y|$); a test on zero-mean data would never have shown the problem.

## Further reading

[LearnCpp](https://www.learncpp.com/) — primary course, documentation, or the supplied reference collection. Follow the relevant subject heading; these are further reading links, not reproduced book chapters.

- [C++ Core Guidelines, arithmetic rules ES.100 to ES.107](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#es100-dont-mix-signed-and-unsigned-arithmetic) - signed/unsigned mixing, overflow and narrowing.
- [C++ working draft](https://eel.is/c++draft/) - [basic.fundamental], [expr.pre], [conv.integral], [expr.arith.conv], [dcl.init.list], [basic.stc.auto].
- [cppreference: List-initialization](https://en.cppreference.com/w/cpp/language/list_initialization), [Default-initialization](https://en.cppreference.com/w/cpp/language/default_initialization), [Reference declaration](https://en.cppreference.com/w/cpp/language/reference), [Storage duration](https://en.cppreference.com/w/cpp/language/storage_duration) and [std::vector::operator[]](https://en.cppreference.com/w/cpp/container/vector/operator_at).
- [cppreference: Arithmetic operators](https://en.cppreference.com/w/cpp/language/operator_arithmetic) and [usual arithmetic conversions](https://en.cppreference.com/w/cpp/language/usual_arithmetic_conversions).
- [Goldberg, What Every Computer Scientist Should Know About Floating-Point Arithmetic](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) - rounding error, cancellation and Kahan summation.

**More practice:** [LearnCpp chapter 4 quiz](https://www.learncpp.com/cpp-tutorial/chapter-4-summary-and-quiz/) (fundamental types and integer division), [LearnCpp chapter 12 quiz](https://www.learncpp.com/cpp-tutorial/chapter-12-summary-and-quiz/) (compound types and references), [LearnCpp on the std::vector unsigned subscript problem](https://www.learncpp.com/cpp-tutorial/stdvector-and-the-unsigned-length-and-subscript-problem/), and the [Exercism C++ track](https://exercism.org/tracks/cpp/exercises).
