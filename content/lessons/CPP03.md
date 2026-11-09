---
{
  "id": "cpp03-foundations",
  "module_id": "CPP03",
  "title": "Resource management: RAII, unique ownership, and move semantics",
  "summary": "Tie every resource to an owning object, make ownership visible in types, and transfer it with moves instead of copies.",
  "estimated_minutes": 390,
  "prerequisites": [
    "CPP02"
  ],
  "source_refs": [
    {
      "title": "C++ standard draft: [except.ctor], [class.dtor], [class.copy.elision]",
      "url": "https://eel.is/c++draft/except.ctor"
    },
    {
      "title": "C++ Core Guidelines: R. Resource management",
      "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"
    },
    {
      "title": "cppreference: std::unique_ptr",
      "url": "https://en.cppreference.com/w/cpp/memory/unique_ptr"
    },
    {
      "title": "LearnCpp: move semantics and smart pointers",
      "url": "https://www.learncpp.com/"
    },
    {
      "title": "cppreference: std::shared_ptr",
      "url": "https://en.cppreference.com/w/cpp/memory/shared_ptr"
    },
    {
      "title": "cppreference: std::move_if_noexcept",
      "url": "https://en.cppreference.com/w/cpp/utility/move_if_noexcept"
    },
    {
      "title": "cppreference: std::vector::emplace_back",
      "url": "https://en.cppreference.com/w/cpp/container/vector/emplace_back"
    }
  ],
  "objectives": [
    "State the RAII rule and explain why it gives exception safety.",
    "Express exclusive ownership with value members, std::vector and std::unique_ptr instead of new/delete.",
    "Implement a move-only resource class that follows the rule of five and leaves a valid moved-from state.",
    "Choose function signatures that show whether ownership is borrowed, transferred or shared."
  ],
  "core_theory": [
    "RAII",
    "unique ownership",
    "move semantics"
  ],
  "labs": [
    "Implement a move-only Buffer and a ScopeGuard, then run the tests under AddressSanitizer to prove there is no leak, double free or use after move."
  ],
  "assessment_refs": [
    "CPP03-diagnostic-v1"
  ],
  "review_prompts": [
    "A callback receives a raw pointer to a camera frame and stores it for later. Redesign the signature so that ownership and lifetime are explicit, and justify your choice among unique_ptr, shared_ptr to const, and copying."
  ],
  "extension_refs": [
    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines",
    "https://en.cppreference.com/w/cpp/memory/unique_ptr"
  ]
}
---

## Why this matters

A robot process opens cameras, serial ports, GPU buffers, file logs and mutexes, and it runs for hours. Every one of those is a *resource* that must be released exactly once, even when an exception, an early `return`, or a failed sensor read leaves the function in the middle. Hand-written `new`/`delete` or `open`/`close` pairs fail on exactly those paths: a leak of one 2 KB scratch buffer per control cycle at 100 Hz is 20 MB per minute, and a double free can crash a vehicle controller. C++ solves this without a garbage collector: the object that owns a resource releases it in its destructor, and the language guarantees destructors run when scope ends, normally or by exception. This is RAII (resource acquisition is initialization). Move semantics then lets ownership travel (returned from factories, stored in containers) without copying large buffers.

## Intuition

Think of a library book with exactly one borrower card. RAII says the card is the object: whoever holds it is responsible for returning the book, and the card cannot be lost without the book being returned automatically. `std::unique_ptr` is a card that cannot be photocopied but can be handed to someone else. A raw pointer is a sticky note with a shelf number on it: it says where the book is, but not who must return it.

In code, the questions to ask of every pointer or handle are: *who owns it, who may only look at it, and until when is it valid?* RAII turns the answer into types: a value member or `std::vector` owns its elements; `std::unique_ptr<T>` owns one `T` exclusively; `T&` and `T*` (when raw) only borrow.

A concrete case: the vision node of a mobile robot receives a 1280 × 720 RGB frame, 2,764,800 bytes, 15 times per second. One copy costs 41.5 MB/s of memory traffic; a pipeline that copies the frame at three stages (decode, undistort, detect) pushes 124.4 MB/s through the memory bus, and every copy is a fresh allocation that can fail. If the frame is one heap block with exactly one owner at a time, the three stages pass a handle instead: a hand-over is a pointer assignment, and whichever stage holds the handle when something goes wrong releases the block while the stack unwinds.

Predict before reading on. A function opens a serial-port object and then calls a routine that throws; a caller three frames up catches the exception. In which order do the port's close and the first line of the catch block run, and how many lines of cleanup code does the function itself need? Write the prediction down; the answer follows the figure.

Two wrong intuitions are worth naming. The first is that `std::move` moves something: it only casts, and the data moves (if at all) inside the constructor or assignment that the cast selects. A moved-from object is still alive and is destroyed later, which is why it must be left in a state its destructor can handle. The second is that smart pointers make ownership problems disappear: `unique_ptr` removes leaks and double frees only when ownership really forms a tree, `shared_ptr` cycles leak silently (see the last theory subsection), and a raw pointer taken from a smart pointer can still dangle (Core Guidelines R.37).

![Lifetime diagram: Buffer a owns storage, a move transfers the pointer to b and leaves a empty, then both destructors run safely](/lesson-figures/CPP03.svg)

*A move transfers the owning pointer and nulls the source, so exactly one destructor frees the storage.*

Answer to the prediction: the port closes first, while the exception is still travelling up the stack, and only then does the first line of the catch block run; the function needs no cleanup code at all, because the destructor of the port is the cleanup. The first theory subsection shows this with compiled code.

## Theory and derivation

### RAII and destruction order

A local object is destroyed when its scope ends, in reverse order of construction. The destructor runs during **stack unwinding** if an exception propagates. Therefore a resource owned by a local object is released on every exit path with no `finally`. Members are destroyed in reverse declaration order, after the destructor body. A destructor must not throw (it is implicitly `noexcept`).

**Example.** A telemetry routine opens an IMU port, then a GPS port, then meets a corrupt packet and throws (compiled and run with g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). In what order are the ports closed, and before or after the handler prints?

```cpp
#include <cstdio>
#include <stdexcept>
struct Port { const char* n; explicit Port(const char* s) : n(s) { std::printf("open  %s\n", n); }
              ~Port() { std::printf("close %s\n", n); } };
void run() {
  Port imu("imu0");
  Port gps("gps1");
  throw std::runtime_error("bad checksum");
}
int main() {
  try { run(); } catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); }
}
```

**Solution.** A local object is destroyed when its scope ends, in reverse order of construction, also during stack unwinding. The ports are therefore closed in the order `gps1`, `imu0`, the reverse of opening, and both closes happen before the handler prints; `run` contains no cleanup statement. This is [except.ctor] ¶2 of the C++ standard: each automatic object that has been constructed is destroyed, in reverse order of the completion of its construction, as control passes to the handler (see also Core Guidelines E.6). The program prints:

```text
open  imu0
open  gps1
close gps1
close imu0
caught: bad checksum
```

![Timeline of run(): imu0 and gps1 open, an exception is thrown, gps1 then imu0 close during stack unwinding, main catches](/lesson-figures/CPP03-2.svg)

*Figure: the lifelines are nested like parentheses, so the last resource opened is the first closed; the shaded interval is the unwinding between the throw (3) and the end of the scope of `run` (5).*

### The rule of zero, three, five

- **Rule of zero**: if your class owns resources only through members that already manage them (`std::vector`, `std::string`, `std::unique_ptr`), write *no* special member functions. The compiler-generated ones are correct. Prefer this.
- **Rule of three/five**: if you must manage a raw resource, define or delete all of: destructor, copy constructor, copy assignment, move constructor, move assignment. A class with a destructor that frees memory but a default copy has two objects owning the same pointer: a double free.

**Example.** `RawLog` owns 5 doubles through a raw pointer and defines no copy operations; `Log` holds a `std::vector` and a `std::string` and defines no special member at all. Each is copied once (the diagnostics go to `stderr`; g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Does each copy share storage with the original, and what happens when both objects are destroyed?

```cpp
#include <cstdio>
#include <string>
#include <vector>
class RawLog {                       // raw owner, copy operations not written
  double* p_;
 public:
  explicit RawLog(int n) : p_(new double[n]()) {}
  ~RawLog() { delete[] p_; }
  const double* data() const { return p_; }
};
struct Log { std::vector<double> t; std::string name; };   // rule of zero
int main() {
  Log a{std::vector<double>(5), "run"};
  Log b = a;
  std::fprintf(stderr, "Log copy shares storage:    %d\n", a.t.data() == b.t.data());
  RawLog r(5);
  RawLog s = r;                      // implicit copy constructor
  std::fprintf(stderr, "RawLog copy shares storage: %d\n", r.data() == s.data());
}
```

**Solution.** The copy of `Log` has storage of its own, because the members know how to copy themselves: the rule of zero (Core Guidelines C.20) costs nothing. The copy of `RawLog` is made by the implicit copy constructor, which copies the pointer, so it shares the 40-byte block with the original; when both go out of scope AddressSanitizer reports the second `delete[]` of the same address as a double free, which is what C.21 (define or delete all five together) prevents. The program prints (the sanitizer report is shortened):

```text
Log copy shares storage:    0
RawLog copy shares storage: 1
==PID==ERROR: AddressSanitizer: attempting double-free on 0x... in thread T0:   (shortened)
```

### Value categories and moves

An **lvalue** has a name and identity; an **rvalue** is a temporary or something you promise not to use again. `std::move(x)` does not move anything: it is a cast to an rvalue reference, which allows an overload `T(T&&)` to be selected. A move constructor should (1) steal the resource, (2) leave the source in a **valid but unspecified** state, usually empty, so that its destructor and assignment still work, and (3) be `noexcept`.

For the owning buffer used in this lesson:

$$\text{move: } \underbrace{\texttt{data\_}}_{\text{dst}} \leftarrow \texttt{src.data\_}, \quad \texttt{src.data\_} \leftarrow \texttt{nullptr}$$

Cost: a copy of $n$ doubles is $O(n)$ time and $8n$ bytes; a move is $O(1)$ (two assignments).

Why `noexcept` matters: when `std::vector` must grow, it relocates its elements. To keep its strong exception guarantee it uses `std::move_if_noexcept`: if the move constructor can throw and the type is also copyable, it *copies* instead. A forgotten `noexcept` silently turns $O(1)$ relocations into $O(n)$ copies.

**Example.** A logger holds 6000 samples (48,000 bytes) in a `std::vector<double>` and hands the whole record to an uploader. `std::move` is only a cast; the vector's move constructor does the work (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Does the new vector reuse the old block, what are the sizes afterwards, and can the moved-from vector still be used?

```cpp
#include <cstdio>
#include <utility>
#include <vector>
int main() {
  std::vector<double> v(6000, 1.5);
  const double* before = v.data();
  std::vector<double> w = std::move(v);
  std::printf("w.data() == old v.data(): %d\n", w.data() == before);
  std::printf("v.size() = %zu, w.size() = %zu\n", v.size(), w.size());
  v.push_back(2.0);                      // moved-from vector is still usable
  std::printf("after push_back: v.size() = %zu\n", v.size());
}
```

**Solution.** The move constructor steals the data pointer and nulls the source (two pointer-sized writes, $O(1)$), so `w` has the very same block (the data pointers compare equal) and no copy of 48,000 bytes happens. `v` is empty with this library (`v.size() = 0`, `w.size() = 6000`) and still accepts `push_back`: the standard guarantees only a valid but unspecified state for the moved-from object, so portable code should assign or destroy it, not read from it. The program prints:

```text
w.data() == old v.data(): 1
v.size() = 0, w.size() = 6000
after push_back: v.size() = 1
```

### Return values and `std::move`

`return local;` already treats `local` as an rvalue and allows copy elision (NRVO). Writing `return std::move(local);` defeats NRVO and forces a move, and compilers warn (`-Wpessimizing-move`). Use `std::move` only when passing an lvalue you will not use again.

**Example.** A small pose type counts its copies and moves. Three functions return a local in different ways: one of two named locals chosen by `if`, a conditional expression `f ? a : b`, and `std::move(a)` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`, no optimisation). How many copies and moves does each return cost?

```cpp
#include <utility>
#include <cstdio>
struct T { int c = 0, m = 0;
  T() = default;
  T(const T& o) : c(o.c + 1), m(o.m) {}
  T(T&& o) noexcept : c(o.c), m(o.m + 1) {} };
T by_if(bool f) { T a, b; if (f) return a; return b; }
T by_cond(bool f) { T a, b; return f ? a : b; }
T by_move() { T a; return std::move(a); }
int main() {
  T x = by_if(true), y = by_cond(true), z = by_move();
  std::printf("two named returns : copies=%d moves=%d\n", x.c, x.m);
  std::printf("conditional expr  : copies=%d moves=%d\n", y.c, y.m);
  std::printf("return std::move  : copies=%d moves=%d\n", z.c, z.m);
}
```

**Solution.** Two named returns still cost one move: when a function returns different locals, no single object can be built in the caller's storage, so the compiler falls back to the implicit move of [class.copy.elision] ¶3 (the returned name is first treated as an rvalue). The conditional expression `f ? a : b` is not a plain name, so that rule does not apply and the type is *copied*. `return std::move(a)` costs a move and draws the warning shown. The rule of thumb stays: return the local by name. The build emits the warning shown first, and the program prints:

```text
warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
two named returns : copies=0 moves=1
conditional expr  : copies=1 moves=0
return std::move  : copies=0 moves=1
```

### Ownership in signatures

| Intent | Signature | Meaning |
|---|---|---|
| Use, do not keep | `const Frame&`, `Frame&` | borrower, caller keeps ownership |
| Optional borrow | `const Frame*` | may be null, still not owned |
| Take ownership | `std::unique_ptr<Frame>` by value | caller must `std::move` in |
| Give ownership | return `std::unique_ptr<Frame>` | caller owns result |
| Shared lifetime | `std::shared_ptr<const Frame>` | reference counted, use sparingly |

Use `std::make_unique<T>(args...)`; it is exception safe and avoids a naked `new`. For C APIs, give `unique_ptr` a custom deleter: `std::unique_ptr<FILE, int(*)(FILE*)> f(fopen(p, "r"), &fclose);`.

**Example.** A pipeline keeps its video source for its whole life, while `show` only looks at it (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). After `show(*s)` and after `set_source(std::move(s))`, who owns the source, and does `set_source(s)` compile?

```cpp
#include <cstdio>
#include <memory>
#include <utility>
struct Source { int id; };
struct Pipeline {
  std::unique_ptr<Source> src_;
  void set_source(std::unique_ptr<Source> s) { src_ = std::move(s); }
};
void show(const Source& s) { std::printf("show(%d)\n", s.id); }
int main() {
  auto s = std::make_unique<Source>(Source{42});
  show(*s);                                  // borrow: s keeps ownership
  Pipeline p;
  p.set_source(std::move(s));                // transfer: explicit at the call site
  std::printf("caller's pointer is null: %d, pipeline holds id %d\n", s == nullptr, p.src_->id);
}
```

**Solution.** `show(const Source&)` borrows, so the caller keeps `s`; `set_source(std::unique_ptr<Source>)` takes ownership, and the call site must say `std::move(s)`, so the hand-over is visible and afterwards `s` is null (guaranteed for `unique_ptr`) while the pipeline holds id 42. Writing `set_source(s)` does not compile: g++ reports `use of deleted function 'std::unique_ptr<...>::unique_ptr(const std::unique_ptr<...>&)'`. These are the rules F.7, R.32 and R.33 of the Core Guidelines made executable. The program prints:

```text
show(42)
caller's pointer is null: 1, pipeline holds id 42
```

### RAII wrappers for C handles: custom deleters and a scope guard

Not every resource is memory. A C library hands out a `FILE*`, a file descriptor or an opaque handle together with a release function (`fclose`, `close`, a vendor `dev_close`). Two wrappers cover the cases, and the choice depends on what the cleanup is. If it is *the release of one handle*, give `std::unique_ptr<T, D>` a deleter type `D`; its destructor calls `D` on the stored pointer when that pointer is not null (cppreference: `std::unique_ptr`; C++ standard [unique.ptr]). A stateless function object as deleter takes no space in the smart pointer, whereas a function pointer is stored and doubles its size. If the cleanup is *an arbitrary action*, such as undoing a half-finished step, a scope guard stores a callable and runs it in its destructor unless it was dismissed: this is `ScopeGuard` in the reference implementation, and Core Guidelines E.19 recommends exactly this (`gsl::finally`) when no suitable resource-handle class exists.

The commit/rollback pattern is the important use: arm the guard first, do the work that may throw, call `dismiss()` last. Two cautions apply. The callable runs inside a destructor, so it must not throw (E.16, C.36). And a lambda that captures by reference must not outlive what it refers to, so the guard is declared after the objects its lambda touches. Prefer a real class with a destructor (E.6) whenever the resource deserves a name.

**Example.** A calibration step must roll back its partial result when a sensor times out, and a `FILE*` needs a deleter (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). What do stages 1 and 2 print with the scope guard, and how large is a `unique_ptr<FILE>` with a function-pointer deleter, with an empty deleter class, and `unique_ptr<int>`?

```cpp
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <utility>
template <class F> struct Guard {
  F f; bool on = true;
  explicit Guard(F fn) : f(std::move(fn)) {}
  Guard(Guard&&) = delete;
  ~Guard() { if (on) f(); }
};
struct FileCloser { void operator()(std::FILE* p) const { std::fclose(p); } };
void stage(int k) {
  Guard g([&] { std::printf("rollback %d\n", k); });
  if (k == 2) throw std::runtime_error("sensor timeout");
  g.on = false;                                       // commit: nothing to undo
  std::printf("commit %d\n", k);
}
int main() {
  for (int k : {1, 2}) { try { stage(k); } catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); } }
  std::printf("unique_ptr<FILE, int(*)(FILE*)>: %zu bytes\n", sizeof(std::unique_ptr<std::FILE, int (*)(std::FILE*)>));
  std::printf("unique_ptr<FILE, FileCloser>:    %zu bytes\n", sizeof(std::unique_ptr<std::FILE, FileCloser>));
  std::printf("unique_ptr<int>:                 %zu bytes\n", sizeof(std::unique_ptr<int>));
}
```

**Solution.** Stage 1 reaches `g.on = false`, so only the commit message appears. In stage 2 the throw skips that line and the destructor of the guard prints the rollback before the handler runs. The size lines show the cost of the deleter choice: the function-pointer deleter is stored and makes the smart pointer 16 bytes, while the empty `FileCloser` class keeps it at 8, the same as a plain pointer. The program prints:

```text
commit 1
rollback 2
caught: sensor timeout
unique_ptr<FILE, int(*)(FILE*)>: 16 bytes
unique_ptr<FILE, FileCloser>:    8 bytes
unique_ptr<int>:                 8 bytes
```

### Exception safety levels, copy-and-swap, and why vectors check `noexcept`

An operation offers one of three guarantees: **basic** (no leak, every invariant holds, but the value may have changed), **strong** (if it throws, the observable state is exactly as before: commit-or-rollback), and **nothrow** (it cannot throw). The naive copy assignment

```cpp
Buffer& operator=(const Buffer& o) {   // WRONG even for the basic guarantee
  delete[] data_;
  data_ = new double[o.size_];          // may throw: data_ now dangles
  std::copy(o.data_, o.data_ + o.size_, data_); size_ = o.size_; return *this;
}
```

fails twice: `new` can throw after the old storage is already gone (a dangling `data_` that the destructor will delete again), and `b = b` copies from freed memory. The repair is an ordering rule: **do everything that can throw first, on a temporary; commit with operations that cannot throw.** Copy-and-swap packages that rule:

```cpp
friend void swap(Buffer& a, Buffer& b) noexcept { std::swap(a.data_, b.data_); std::swap(a.size_, b.size_); }
Buffer& operator=(Buffer o) noexcept { swap(*this, o); return *this; }   // o is taken by value
```

*Proof of the strong guarantee.* The parameter `o` is initialised before the function body runs: by the copy constructor if the argument is an lvalue, by the move constructor if it is an rvalue. If that copy throws, the body never executes, so `*this` is untouched. If it succeeds, `swap` only exchanges a pointer and an integer, so it cannot throw; afterwards `o` holds the old contents and its destructor releases them. Self-assignment is correct without a test because `o` is an independent copy. The same single function therefore serves as copy- and move-assignment (the argument's value category selects the constructor), which collapses the copy and move assignments of the rule of five into one function (compare C++ Core Guidelines, C.21, C.65 and C.66).

Costs and limits: an assignment `a = b` always allocates, even if `a` already has enough capacity, whereas `std::vector::operator=` reuses its storage; the unified operator is also *ambiguous* if you additionally declare `operator=(const Buffer&)`, because `a = b` matches both equally well. Use copy-and-swap when clarity and the strong guarantee matter more than the last allocation.

**Example.** A calibration table of 7 doubles is overwritten by a table of 4 doubles while an injected fault makes the copy constructor throw once (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). What are the size and first value of `a` after the failed assignment, and after the successful one?

```cpp
#include <cstdio>
#include <algorithm>
#include <stdexcept>
#include <utility>
class Table {
  double* d_; std::size_t n_;
  static inline bool fail_ = false;
 public:
  static void fail_next_copy() { fail_ = true; }
  explicit Table(std::size_t n, double v) : d_(new double[n]), n_(n) { std::fill(d_, d_ + n, v); }
  Table(const Table& o) : d_(nullptr), n_(0) {
    if (fail_) { fail_ = false; throw std::runtime_error("copy failed"); }
    d_ = new double[o.n_]; std::copy(o.d_, o.d_ + o.n_, d_); n_ = o.n_; }
  ~Table() { delete[] d_; }
  friend void swap(Table& a, Table& b) noexcept { std::swap(a.d_, b.d_); std::swap(a.n_, b.n_); }
  Table& operator=(Table o) noexcept { swap(*this, o); return *this; }
  std::size_t size() const { return n_; }
  double operator[](std::size_t i) const { return d_[i]; }
};
int main() {
  Table a(7, 1.5), b(4, 9.0);
  Table::fail_next_copy();
  try { a = b; } catch (const std::exception& e) { std::printf("threw: %s\n", e.what()); }
  std::printf("a after failed a = b: size=%zu a[0]=%.1f\n", a.size(), a[0]);
  a = b;
  std::printf("a after a = b       : size=%zu a[0]=%.1f\n", a.size(), a[0]);
}
```

**Solution.** The first assignment fails inside the construction of the by-value parameter, before `swap` runs, so `a` keeps its 7 elements and its first value 1.5: the strong guarantee, observed. The second assignment succeeds and the table is the new one (4 elements, first value 9.0), all at once. The program prints:

```text
threw: copy failed
a after failed a = b: size=7 a[0]=1.5
a after a = b       : size=4 a[0]=9.0
```

*Why `std::vector` asks about `noexcept`.* To grow, a vector must relocate $n$ elements into new storage and promise that, if anything throws, the old vector is still intact. Suppose it moves and the $k$-th move throws: elements $1,\dots,k-1$ have already been pillaged, and putting them back needs $k-1$ more moves, which may throw too, so no rollback exists. Copying leaves the sources untouched, so after a throw at the $k$-th copy the vector only destroys the $k-1$ new copies and frees the new block. Hence `std::move_if_noexcept` returns an rvalue only if the move cannot throw *or* the type cannot be copied at all; in the latter case the guarantee is waived (cppreference: `std::move_if_noexcept`; `std::vector::emplace_back`, "Exceptions").

```explore
{
  "title": "Cost of relocation when the move can throw",
  "title_vi": "Chi phí di dời khi move có thể throw",
  "prompt": "Predict first: a vector of a copyable type whose move is not noexcept receives n push_back calls and doubles its capacity from 1. For n = 20, how many element copies happen in relocations alone: about n, about 2n, or about n²? Then move the sliders.",
  "prompt_vi": "Dự đoán trước: một vector của kiểu copy được mà move không noexcept nhận n lần push_back và nhân đôi dung lượng từ 1. Với n = 20, có bao nhiêu phép copy phần tử chỉ riêng trong lúc di dời: cỡ n, cỡ 2n hay cỡ n²? Rồi kéo thanh trượt.",
  "params": [
    { "name": "n", "label": "push_back calls n", "label_vi": "số lần push_back n", "min": 1, "max": 64, "step": 1, "value": 20, "unit": "" },
    { "name": "s", "label": "element size", "label_vi": "kích thước phần tử", "min": 8, "max": 4096, "step": 8, "value": 64, "unit": "B" }
  ],
  "let": [
    { "name": "copies", "expr": "2^ceil(log(n)/log(2) - 0.000001) - 1" }
  ],
  "plot": {
    "x": { "name": "m", "min": 1, "max": 64, "label": "pushes m", "label_vi": "số lần push m" },
    "y": { "label": "relocation copies", "label_vi": "số copy khi di dời", "min": 0 },
    "series": [
      { "expr": "2^ceil(log(m)/log(2) - 0.000001) - 1", "label": "move not noexcept: copies", "label_vi": "move không noexcept: số copy", "color": "orange" },
      { "expr": "0", "label": "move noexcept: copies", "label_vi": "move noexcept: số copy", "color": "green" },
      { "expr": "m", "label": "m (one copy per push)", "label_vi": "m (một copy mỗi lần push)", "color": "grey" }
    ],
    "points": [
      { "x": "n", "y": "copies", "label": "your n", "label_vi": "n của bạn", "color": "orange" }
    ]
  },
  "readouts": [
    { "label": "relocation copies", "label_vi": "số copy khi di dời", "expr": "copies", "unit": "", "digits": 0 },
    { "label": "bytes copied (relocation only)", "label_vi": "byte được copy (chỉ khi di dời)", "expr": "copies*s", "unit": "B", "digits": 0 },
    { "label": "copies per push", "label_vi": "số copy trên mỗi push", "expr": "copies/n", "unit": "", "digits": 2 }
  ]
}
```

*Figure: the orange staircase is $2^{\lceil\log_2 m\rceil}-1$ (relocations at sizes 1, 2, 4, ..., each copying that many elements; measured 31 copies for 20 pushes with the libstdc++ of g++ 11.4.0). With a `noexcept` move the copy count stays at zero and each relocation is a cheap move.*

### What a throwing constructor cleans up: the half-built object

If a constructor exits by exception, the destructor of that object does **not** run, because the object never finished existing. What the language does destroy are the *fully constructed* base subobjects and members, in reverse order. So for

```cpp
struct Raw { double* a; double* b;
  Raw() : a(new double[100]), b(new double[200]) { risky(); }   // risky() throws
  ~Raw() { delete[] a; delete[] b; } };
```

both arrays leak ($100\cdot8+200\cdot8=2400$ bytes): the members are plain pointers, whose "destruction" does nothing, and `~Raw` is skipped. If the initialiser of `b` itself throws, `a` has been allocated and leaks ($800$ bytes). The principle behind "one resource, one owner" (E.6, R.13) is exactly this: when every resource is held by its own member object (`std::unique_ptr<double[]> a, b;`), the language's own cleanup of completed members releases whatever was acquired so far, in every exit path, with no code of yours. Never put two raw acquisitions in one constructor or one expression statement.

**Example.** Two members with visible constructors and destructors are held by a class whose constructor body throws (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Which destructors run, and in what order?

```cpp
#include <cstdio>
#include <stdexcept>
struct Res { const char* n; explicit Res(const char* s) : n(s) { std::printf("+%s ", n); }
             ~Res() { std::printf("-%s ", n); } };
struct Holder {
  Res a{"a"}; Res b{"b"};
  Holder() { std::printf("[body] "); throw std::runtime_error("x"); }
  ~Holder() { std::printf("~Holder "); }
};
int main() { try { Holder h; } catch (...) { std::printf("caught\n"); } }
```

**Solution.** Both members were completely constructed, so they are destroyed in reverse order (`-b -a`), and `~Holder` never runs, as [except.ctor] ¶3 specifies. The program prints:

```text
+a +b [body] -b -a caught
```

**Example.** The cost of raw owners is measured with a counting `operator new[]`; the first class acquires 5 and 7 doubles with `new` and throws, the second holds them in `unique_ptr<double[]>` and throws (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). How many bytes are still allocated after each failed construction?

```cpp
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>
#include <stdexcept>
static long live = 0;                                  // bytes allocated minus freed
void* operator new[](std::size_t n) { live += n; auto* p = static_cast<std::size_t*>(std::malloc(n + 16)); *p = n; return p + 2; }
void operator delete[](void* q) noexcept { if (q) { auto* p = static_cast<std::size_t*>(q) - 2; live -= *p; std::free(p); } }
void operator delete[](void* q, std::size_t) noexcept { operator delete[](q); }
struct Raw {
  double* a; double* b;
  Raw() : a(new double[5]), b(new double[7]) { throw std::runtime_error("x"); }
  ~Raw() { delete[] a; delete[] b; }
};
struct Safe {
  std::unique_ptr<double[]> a, b;
  Safe() : a(new double[5]), b(new double[7]) { throw std::runtime_error("x"); }
};
int main() {
  try { Raw r; } catch (...) {}
  std::printf("Raw : %ld bytes still allocated\n", live);
  live = 0;
  try { Safe s; } catch (...) {}
  std::printf("Safe: %ld bytes still allocated\n", live);
}
```

**Solution.** In `Raw` the members are plain pointers, so destroying them does nothing and `~Raw` is skipped: the two arrays leak $5\cdot8+7\cdot8=40+56=96$ bytes per failed construction. In `Safe` each array has its own owner member, and the language destroys the completed members itself, so nothing is left: 0 bytes. The program prints:

```text
Raw : 96 bytes still allocated
Safe: 0 bytes still allocated
```

![Left: sequence for Holder, b then a destroyed and ~Holder skipped. Right: bytes still allocated, 96 B for raw pointers (40 B + 56 B), 0 B for unique_ptr members](/lesson-figures/CPP03-3.svg)

*Figure: left, what the language destroys when a constructor throws; right, the bytes left allocated by the two classes of the example, with the contribution of each member.*

### Shared ownership: control block, cycles, aliasing

A `std::shared_ptr` is two pointers: one to the object and one to a **control block** that stores the strong count (owners), the weak count (observers), the type-erased deleter and, if created with `make_shared`, the object itself in the same allocation (cppreference: `std::shared_ptr`, "Implementation notes"). Copying increments the strong count with an atomic operation, destroying decrements it, and the object is destroyed when the strong count reaches 0; the control block is freed when the weak count reaches 0 as well. Consequences:

- *Cost.* Every by-value pass of a `shared_ptr` is an atomic read-modify-write, which is why the guidelines say to take smart pointers as parameters only to express lifetime semantics (R.30) and otherwise to pass a reference to the pointee (R.32, R.33); R.37 warns against giving a callee a raw pointer or reference taken from a smart pointer that something else might reset.
- *Cycles.* If `A` owns `B` through a `shared_ptr` and `B` owns `A`, then each object has strong count 2 while two locals refer to them; when the locals die the counts drop to 1, never to 0, and both objects leak with their destructors never run. A non-owning back-link must be a `std::weak_ptr` (R.24), turned into a temporary owner with `lock()` only while it is used.
- *Aliasing.* The aliasing constructor `shared_ptr<int>(p, &p->y)` shares `p`'s control block but points at a member: the member stays alive as long as any alias exists, even after `p` itself is reset.

**Example.** One pose estimate is shared by three consumers and watched by a diagnostics node that must not keep it alive (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). What are the use counts at each stage, what do `expired()` and `lock()` report at the end, and how large is a `shared_ptr`?

```cpp
#include <cstdio>
#include <memory>
struct Pose { double x = 1.0; };
int main() {
  auto sensor = std::make_shared<Pose>();
  std::weak_ptr<Pose> watcher = sensor;
  auto a = sensor, b = sensor;
  std::printf("use_count = %ld\n", sensor.use_count());
  a.reset(); b.reset();
  std::printf("after two resets: %ld\n", sensor.use_count());
  if (auto locked = watcher.lock()) std::printf("lock() ok, count = %ld\n", locked.use_count());
  sensor.reset();
  std::printf("expired = %d, lock() null = %d\n", watcher.expired(), watcher.lock() == nullptr);
  std::printf("sizeof(shared_ptr<Pose>) = %zu\n", sizeof(sensor));
}
```

**Solution.** Two copies raise the strong count from 1 to 3; the `weak_ptr` is not counted. After two resets it is back to 1. While a `lock()` result is held the count is 2 (the owner plus the temporary), and after the last owner resets, `expired()` is true and `lock()` returns null, so the observer learns that the object is gone instead of dangling. The 16 bytes are the two pointers (object and control block) described above. The program prints:

```text
use_count = 3
after two resets: 1
lock() ok, count = 2
expired = 1, lock() null = 1
sizeof(shared_ptr<Pose>) = 16
```

## Worked example



### Case 1: tracing a move and a heap `Buffer`

**Problem.** The `Buffer` of the reference implementation counts live objects in `Buffer::alive` (initially 0). Trace

```cpp
Buffer a = make_ramp(3);   // (1)
Buffer b = std::move(a);   // (2)
{
  auto p = std::make_unique<Buffer>(2);  // (3)
}                          // (4)
```

and give `alive` after each statement, the state of `a` after (2), and how many times the block of storage created in (1) is freed.

**Solution.**

1. *Statement (1).* `make_ramp(3)` builds `Buffer b(3)` inside the function; with elision the object is constructed directly into `a` (the constructor increments `alive`). Storage `[0,1,2]` at address `A`: `a.data_ = A`, `a.size_ = 3`, `alive = 1`.
2. *Statement (2).* `Buffer(Buffer&&)` is selected because `std::move(a)` is an rvalue (theory: value categories and moves). It performs the two assignments of the move formula: `b.data_ = a.data_ = A`, `b.size_ = 3`, then `a.data_ = nullptr`, `a.size_ = 0`. The constructor still increments `alive`, so `alive = 1 + 1 = 2`: a moved-from object is still an object.
3. *Statement (3).* `std::make_unique<Buffer>(2)` allocates the `Buffer` object on the heap, and its constructor allocates 2 doubles: `alive = 3`.
4. *Statement (4).* At the closing brace `p` is destroyed: `unique_ptr` deletes the `Buffer`, whose destructor frees its 2 doubles and decrements: `alive = 2`.
5. *End of the enclosing scope.* Destructors run in reverse order of construction ([except.ctor]; theory: RAII and destruction order). `b` first: `delete[] A`, `alive = 1`. Then `a`: `delete[] nullptr`, defined as a no-op by the language, `alive = 0`.

**Check.** Compiling the program with the reference `Buffer` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`) and printing `alive` after each statement gives `alive` = 1, 2, 3, 2 for (1) to (4) and `a.size()` = 0, `b.size()` = 3 after (2); AddressSanitizer reports no error, so `A` is freed exactly once. Without `a.data_ = nullptr` in step 2, step 5 would free `A` twice.

**Takeaway.** A move is two pointer writes plus a nulling, and the nulling is what lets two destructors coexist.

### Case 2: counts and destruction order with `shared_ptr` and `weak_ptr`

**Problem.** An `Imu` is shared by a `Filter` and a `Logger`; the `Logger` also keeps a `weak_ptr` to the `Filter` for diagnostics. Each class prints its name in its destructor. Give every `use_count()` printed and the exact order of the destructor lines.

```cpp
#include <cstdio>
#include <memory>
struct Imu { ~Imu() { std::puts("~Imu"); } };
struct Filter { std::shared_ptr<Imu> imu; ~Filter() { std::puts("~Filter"); } };
struct Logger { std::shared_ptr<Imu> imu; std::weak_ptr<Filter> f; ~Logger() { std::puts("~Logger"); } };
int main() {
  auto imu = std::make_shared<Imu>();
  auto f = std::make_shared<Filter>();  f->imu = imu;
  std::printf("(1) imu=%ld f=%ld\n", imu.use_count(), f.use_count());
  {
    auto lg = std::make_shared<Logger>(); lg->imu = imu; lg->f = f;
    std::printf("(2) imu=%ld f=%ld lg=%ld\n", imu.use_count(), f.use_count(), lg.use_count());
    auto locked = lg->f.lock();
    std::printf("(3) f=%ld\n", f.use_count());
  }
  std::printf("(4) imu=%ld f=%ld\n", imu.use_count(), f.use_count());
  imu.reset();
  std::printf("(5) f->imu count=%ld\n", f->imu.use_count());
  f.reset();
  std::puts("(6) end");
}
```

**Solution.** The `use_count()` of a `shared_ptr` is the number of strong owners (theory: shared ownership); `weak_ptr` and the control block do not count. Locals are destroyed in reverse order of declaration.

1. After `imu` is created its count is 1. Line `f->imu = imu;` adds the owner `Filter::imu`: `imu` count 2, `f` count 1 (printed `(1) imu=2 f=1`).
2. Inside the block `lg->imu = imu` adds the owner `Logger::imu`: count 3; `lg->f = f` stores a `weak_ptr`, so `f` stays at 1; `lg` itself has count 1 (printed `(2) imu=3 f=1 lg=1`).
3. `lg->f.lock()` creates the temporary owner `locked`: `f` count 2 (printed `(3) f=2`).
4. At the closing brace `locked` is destroyed first (declared last): `f` back to 1. Then `lg`: its count drops 1 to 0, `~Logger` runs and releases `Logger::imu`: `imu` count 2 (printed `(4) imu=2 f=1`, after the line `~Logger`).
5. `imu.reset()` releases the local owner: the only owner left is `Filter::imu`, so `f->imu.use_count()` is 1 (printed `(5)`).
6. `f.reset()` takes the count of `f` from 1 to 0: `~Filter` runs, its member `imu` is destroyed afterwards (members after the destructor body), taking the `Imu` count to 0: `~Imu`. Printed order `~Filter`, `~Imu`, then `(6) end`.

![Three ownership graphs at steps 3, 4 and 5: Imu strong count 3, 2, 1; Filter 2 then 1; Logger alive only at step 3, with a weak link to Filter](/lesson-figures/CPP03-4.svg)

*Figure: the strong counts of the program after steps (3), (4) and (5); the dashed arrow is the `weak_ptr`, which adds no count.*

**Check.** Compiled with g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`, the program prints exactly

```text
(1) imu=2 f=1
(2) imu=3 f=1 lg=1
(3) f=2
~Logger
(4) imu=2 f=1
(5) f->imu count=1
~Filter
~Imu
(6) end
```

which matches every number above; AddressSanitizer is silent. Independent argument: the sum of strong counts in the figure equals the number of solid arrows plus local variables, 3 at step 3 for `Imu` (`imu`, `Filter`, `Logger`).

**Takeaway.** Counts change only at copies, resets and destructions of owners, and `weak_ptr` observes without owning, so the graph of strong arrows must be acyclic for everything to be freed.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source, in new words and numbers.

1. **(Easy)** *(Adapted from: C++ Core Guidelines, R.1 and E.6)* Explain in three sentences why a function that locks a mutex through `std::lock_guard` is safe if the code after the lock throws, whereas `m.lock(); ...; m.unlock();` is not.
2. **(Easy)** Predict the output (each `Tag` prints `+name` when constructed and `-name` when destroyed):
   ```cpp
   struct Tag { std::string n; Tag(std::string s) : n(s) { std::cout << "+" << n << ' '; }
                ~Tag() { std::cout << "-" << n << ' '; } };
   int main() { Tag a("a"); { Tag b("b"); Tag c("c"); } Tag d("d"); }
   ```
3. **(Easy)** A 100 Hz control loop runs for 10 minutes. On an early-return path taken in one of every four cycles it forgets to `delete[]` a scratch buffer of 256 doubles. How many bytes leak? Why would a leak checker report it only at exit, and why is that still a bug on a robot?
4. **(Medium)** Find the bug and give three different fixes.
   ```cpp
   class Scan {
     double* d_;
    public:
     explicit Scan(size_t n) : d_(new double[n]) {}
     ~Scan() { delete[] d_; }
   };
   void f() { Scan a(10); Scan b = a; }
   ```
5. **(Medium)** Predict the output and say what the standard guarantees about `p` afterwards:
   ```cpp
   auto p = std::make_unique<int>(7);
   auto q = std::move(p);
   std::cout << (p == nullptr) << *q;
   ```
6. **(Medium)** *(Adapted from: C++ Core Guidelines, R.30-R.33 and F.7)* For each of these, choose the parameter type from the table above and justify it: (a) `draw(frame)` renders a camera frame and returns; (b) `Pipeline::set_source(...)` stores the frame source for its whole life; (c) `log_async(frame)` hands a frame to a thread that may outlive the caller; (d) a function that may or may not have a calibration to apply.
7. **(Medium)** *(Adapted from: LearnCpp, chapter on move semantics, returning by value)* Given `struct C { C(C&&) noexcept; ... };`, predict how many times the move constructor runs for `C a = f1();` with `C f1() { C c; return c; }` and for `C f2() { C c; return std::move(c); }` using GCC 11 at `-O0` in C++17. Explain the difference and which is preferred.
8. **(Hard)** Growth cost. Two types are identical except that `W(W&&) noexcept` and `V(V&&)` (not `noexcept`, but copyable). Both count their copies and moves. Predict the counts after `for (int i = 0; i < 4; ++i) v.push_back(W());` on a vector that starts empty and doubles capacity (1, 2, 4), then for `V`. Explain the mechanism.
9. **(Hard)** Derive why a move-assignment operator `Buffer& operator=(Buffer&& o) { delete[] data_; data_ = o.data_; size_ = o.size_; o.data_ = nullptr; o.size_ = 0; return *this; }` is wrong for `b = std::move(b)` and show the final state of `data_`. Then fix it two ways: with an identity check, and with the swap idiom (`std::swap(data_, o.data_)`); say what each leaves in `o`.
10. **(Hard)** Design. A ROS-style subscriber callback receives a 1 MB camera frame at 30 Hz. A planner thread needs the latest frame up to 200 ms after it arrives, while the driver reuses its buffer. Compare (i) copying into a member each time, (ii) `shared_ptr<const Frame>`, (iii) a pool of `unique_ptr<Frame>` handed over by `std::move`. Give the copy bandwidth of (i) and the main risk of each option.
11. **(Mini-project)** Wrap a fake C device API (`int dev_open(int id); void dev_close(int h);`, with a global counter of open handles) in a move-only `Device` class, plus a variant using `unique_ptr` with a custom deleter. Write tests showing the open-handle counter returns to 0 after normal exit, after a thrown exception, and after moving a device into a `std::vector`.

12. **(Challenge)** Copy-and-swap, quantitatively. Take `Buffer& operator=(Buffer o) noexcept { swap(*this, o); return *this; }` with a copy constructor that allocates, and a move constructor that steals. `a` holds 1000 doubles and `b` holds 500. (a) Prove that if the copy constructor throws during `a = b`, `a` is unchanged. (b) Give the number of copies, moves and heap allocations for `a = b`, then `a = std::move(b)`, then `a = a`. (c) State exactly what `b` and `a` hold afterwards in each case. (d) Why does adding a second overload `operator=(const Buffer&)` break `a = b`, and when would you still prefer it? (adapted from C++ Core Guidelines, C.65 and C.66, and cppreference "Rule of three/five")
13. **(Challenge)** Two nodes `A` and `B` of a graph hold each other through `std::shared_ptr<Cyc> other;`, both created with `make_shared` in an inner scope. (a) Give `use_count()` of each while both locals are alive, and the destructor output after the scope ends. (b) Change one link to `std::weak_ptr` and give the counts and the destructor order for `A` owning `B`. (c) For `struct P { int x, y; }; auto p = std::make_shared<P>(); std::shared_ptr<int> y(p, &p->y);` give `p.use_count()` and `y.use_count()`, then after `p.reset()`. Explain what is kept alive and why this is safe. (source: cppreference, std::shared_ptr, control block and aliasing constructor; C++ Core Guidelines, R.24)
14. **(Challenge)** Leak accounting in constructors. For `struct Raw { double *a, *b; Raw() : a(new double[30]), b(new double[90]) { risky(); } ~Raw() { delete[] a; delete[] b; } };` with `risky()` always throwing, how many bytes leak per attempted construction? Repeat when `b`'s initialiser is `throw std::runtime_error("x")` instead of `new double[90]`. Then rewrite the class with `std::unique_ptr<double[]>` members and show that the leak is zero in both cases, naming the language rule you rely on. Finally, a robot retries construction at 10 Hz for 5 minutes and fails every time with the first variant: how much memory is lost? (adapted from C++ Core Guidelines, E.6 and R.13)
15. **(Challenge)** Relocation under failure. A type `T` has a copy constructor that throws on its third invocation (counting from the start of the experiment) and a move constructor declared `noexcept(false)`. A `std::vector<T>` has size 4 and capacity 4, and you call `emplace_back(4)`. (a) Predict copies, moves, the vector size, capacity and element ids afterwards, and say what happens to the partly built new block. (b) Repeat with `noexcept` on the move constructor. (c) Prove why a relocation by moves cannot restore the old contents in general, and state what the standard waives when `T` is move-only with a throwing move. (adapted from cppreference, `std::vector::emplace_back` and `std::move_if_noexcept`, "Exceptions")

## Reference implementation

`Buffer` is the rule-of-five owner (raw storage, move only), `ScopeGuard` is a generic RAII helper for cleanup code, and `make_ramp` shows a factory returning by value. Compile with `g++ -std=c++17 -Wall -Wextra -fsanitize=address,undefined ref.cpp && ./a.out`.

```cpp
// CPP03 reference: an owning buffer (RAII, move-only), a scope guard, and a factory.
#include <cstddef>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <type_traits>
#include <utility>

class Buffer {
 public:
  static inline int alive = 0;  // number of Buffer objects currently alive (for tests)

  explicit Buffer(std::size_t n) : data_(n ? new double[n]() : nullptr), size_(n) { ++alive; }
  Buffer(const Buffer&) = delete;
  Buffer& operator=(const Buffer&) = delete;
  Buffer(Buffer&& other) noexcept : data_(other.data_), size_(other.size_) {
    other.data_ = nullptr;
    other.size_ = 0;
    ++alive;
  }
  Buffer& operator=(Buffer&& other) noexcept {
    if (this != &other) {
      delete[] data_;
      data_ = other.data_;
      size_ = other.size_;
      other.data_ = nullptr;
      other.size_ = 0;
    }
    return *this;
  }
  ~Buffer() {
    delete[] data_;
    --alive;
  }

  std::size_t size() const { return size_; }
  bool empty() const { return size_ == 0; }
  double& at(std::size_t i) {
    if (i >= size_) throw std::out_of_range("Buffer::at");
    return data_[i];
  }
  double at(std::size_t i) const {
    if (i >= size_) throw std::out_of_range("Buffer::at");
    return data_[i];
  }

 private:
  double* data_;
  std::size_t size_;
};

// Runs a callable when it leaves scope unless dismissed.
template <class F>
class ScopeGuard {
 public:
  explicit ScopeGuard(F f) : f_(std::move(f)) {}
  ScopeGuard(const ScopeGuard&) = delete;
  ScopeGuard& operator=(const ScopeGuard&) = delete;
  ScopeGuard(ScopeGuard&& o) noexcept : f_(std::move(o.f_)), active_(o.active_) { o.active_ = false; }
  ~ScopeGuard() {
    if (active_) f_();
  }
  void dismiss() { active_ = false; }

 private:
  F f_;
  bool active_ = true;
};

// Returns a buffer 0, 1, ..., n-1 by value (moved or elided, never copied).
Buffer make_ramp(std::size_t n) {
  Buffer b(n);
  for (std::size_t i = 0; i < n; ++i) b.at(i) = static_cast<double>(i);
  return b;
}

// ---- self-test
int main() {
  {
    Buffer a = make_ramp(4);
    Buffer b = std::move(a);
    if (!a.empty() || b.size() != 4 || b.at(3) != 3.0) return 1;
    auto p = std::make_unique<Buffer>(2);
    if (Buffer::alive != 3) return 2;
  }
  if (Buffer::alive != 0) return 3;
  int ran = 0;
  {
    ScopeGuard g([&] { ++ran; });
    ScopeGuard h([&] { ran += 100; });
    h.dismiss();
  }
  if (ran != 1) return 4;
  static_assert(!std::is_copy_constructible_v<Buffer>);
  static_assert(std::is_nothrow_move_constructible_v<Buffer>);
  std::cout << "CPP03 reference self-test passed\n";
}
```

## Independent practice

### Goal

Write a move-only owning class and a scope guard from stubs, then show with tests and AddressSanitizer that every resource is released exactly once.

### Setup

Needs `g++` or `clang++` with C++17. Save the starter code and the tests below it as `lab.cpp`; build with

```
g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab
```

### Tasks

1. Implement `Buffer(std::size_t)`, `size`, `empty`, `at`, and the destructor; keep `alive` exact. Run the first tests.
2. Implement the move constructor; confirm that the moved-from object is empty and that the destructor of both objects is safe.
3. Implement move assignment, including self-move.
4. Implement `make_ramp` and verify no copies occur (the copy constructor is deleted, so it cannot compile if you cheat).
5. Implement `ScopeGuard` (store the callable, run once, honour `dismiss`, support moves).
6. Deliberately break one rule (e.g. forget to null the source) and read the AddressSanitizer report: note the words *double-free* and the two stack traces.

### Starter code

```cpp
#include <cstddef>
#include <memory>
#include <stdexcept>
#include <type_traits>
#include <utility>

class Buffer {
 public:
  static inline int alive = 0;  // MUST equal the number of Buffer objects currently alive

  // n doubles, zero-initialised; n == 0 owns nothing. Counts itself in `alive`.
  explicit Buffer(std::size_t n) { throw std::logic_error("NotImplemented"); }
  Buffer(const Buffer&) = delete;
  Buffer& operator=(const Buffer&) = delete;
  // Steals the storage; `other` must become empty (size 0, no storage). Counts itself in `alive`.
  Buffer(Buffer&& other) noexcept { throw std::logic_error("NotImplemented"); }
  // Releases current storage, steals other's; self-move must be harmless.
  Buffer& operator=(Buffer&& other) noexcept { throw std::logic_error("NotImplemented"); }
  ~Buffer() {}  // must free the storage and decrement `alive`

  std::size_t size() const { throw std::logic_error("NotImplemented"); }
  bool empty() const { throw std::logic_error("NotImplemented"); }
  // Bounds-checked element access; throws std::out_of_range when i >= size().
  double& at(std::size_t i) { throw std::logic_error("NotImplemented"); }
  double at(std::size_t i) const { throw std::logic_error("NotImplemented"); }
};

// Runs the callable exactly once when the guard leaves scope, unless dismiss() was called.
// Movable (moved-from guard does nothing), not copyable.
template <class F>
class ScopeGuard {
 public:
  explicit ScopeGuard(F f) { throw std::logic_error("NotImplemented"); }
  void dismiss() { throw std::logic_error("NotImplemented"); }
};

// Returns Buffer holding 0, 1, ..., n-1 by value.
Buffer make_ramp(std::size_t n) { throw std::logic_error("NotImplemented"); }
```

### Tests

```cpp

// ---- tests (paste below the starter code)
#include <iostream>
#include <cstdlib>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)

int main() {
  static_assert(!std::is_copy_constructible_v<Buffer>, "Buffer must not be copyable");
  static_assert(std::is_nothrow_move_constructible_v<Buffer>, "move must be noexcept");
  CHECK(Buffer::alive == 0);
  {
    // 1. hand-computed: ramp of 5
    Buffer r = make_ramp(5);
    CHECK(r.size() == 5 && r.at(0) == 0.0 && r.at(4) == 4.0);
    // 2. zero-initialised
    Buffer z(3);
    CHECK(z.at(0) == 0.0 && z.at(2) == 0.0);
    // 3. move constructor leaves the source empty
    Buffer m = std::move(r);
    CHECK(r.empty() && r.size() == 0 && m.size() == 5);
    // 4. move assignment frees the old storage and survives self-move
    z = std::move(m);
    CHECK(z.size() == 5 && m.empty());
    Buffer& alias = z;
    z = std::move(alias);
    CHECK(z.size() == 5 && z.at(4) == 4.0);
    // 5. edge cases
    Buffer none(0);
    CHECK(none.empty());
    bool threw = false;
    try { z.at(5); } catch (const std::out_of_range&) { threw = true; }
    CHECK(threw);
    // 6. invariant: alive equals the number of live objects (r, z, m, none)
    CHECK(Buffer::alive == 4);
    auto p = std::make_unique<Buffer>(2);
    CHECK(Buffer::alive == 5);
  }
  CHECK(Buffer::alive == 0);  // everything released
  // 7. ScopeGuard: runs once, not when dismissed, not twice when moved
  int ran = 0;
  {
    ScopeGuard g([&] { ++ran; });
    ScopeGuard moved(std::move(g));
    ScopeGuard d([&] { ran += 100; });
    d.dismiss();
    CHECK(ran == 0);
  }
  CHECK(ran == 1);
  std::cout << "all tests passed\n";
}
```

### Expected output

```
all tests passed
```

With the unimplemented starter the program terminates with `NotImplemented`; with a buggy move constructor, AddressSanitizer prints `attempting double-free`.

### Extension challenge

Make `Buffer` copyable with a deep copy (copy-and-swap) and show with a counter that `std::vector<Buffer>` growth uses moves because they are `noexcept`. Then replace the raw `double*` by `std::unique_ptr<double[]>` and delete your destructor and move operations (rule of zero).

### Library track

Use only the standard library. Redo `Buffer` under the rule of zero and let the real library types do the work, then confirm the claims from the lesson with counters. Compile with `g++ -std=c++17 -Wall -Wextra -fsanitize=address,undefined`.

```cpp
#include <cassert>
#include <cstdio>
#include <iostream>
#include <memory>
#include <type_traits>
#include <vector>

// Rule of zero: no destructor, no copy or move declared. The unique_ptr member does everything.
class Buffer0 {
 public:
  explicit Buffer0(std::size_t n) : data_(new double[n]()), size_(n) {}
  std::size_t size() const { return size_; }
  double& operator[](std::size_t i) { return data_[i]; }
 private:
  std::unique_ptr<double[]> data_;
  std::size_t size_;
};
static_assert(!std::is_copy_constructible_v<Buffer0>);          // unique_ptr makes it move-only
static_assert(std::is_nothrow_move_constructible_v<Buffer0>);   // generated, and noexcept

// Counting types to watch std::vector growth (same as exercise 8)
struct Safe  { Safe() = default;  Safe(const Safe&)  { ++c; } Safe(Safe&&) noexcept { ++m; } static inline int c = 0, m = 0; };
struct Risky { Risky() = default; Risky(const Risky&) { ++c; } Risky(Risky&&)          { ++m; } static inline int c = 0, m = 0; };

int main() {
  std::vector<Buffer0> v;
  for (int i = 0; i < 8; ++i) v.emplace_back(1000);   // growth relocates by moving
  assert(v.size() == 8 && v[7].size() == 1000);

  { std::vector<Safe> s;  for (int i = 0; i < 8; ++i) s.emplace_back(); }
  { std::vector<Risky> r; for (int i = 0; i < 8; ++i) r.emplace_back(); }
  std::cout << "Safe copies=" << Safe::c << " Risky copies=" << Risky::c << "\n";
  assert(Safe::c == 0 && Risky::c == 7);              // 1 + 2 + 4 relocations

  {  // a C resource with a custom deleter: closed exactly once, also on early exit
    std::unique_ptr<FILE, int (*)(FILE*)> f(std::tmpfile(), &std::fclose);
    assert(f != nullptr);
    std::fputs("hello", f.get());
  }  // fclose runs here
  std::cout << "library track ok\n";
}
```

Expected output: `Safe copies=0 Risky copies=7` then `library track ok`. Then run your lab tests on a `Buffer` that wraps `std::unique_ptr<double[]>` with all five special members deleted from your source, and note that the tests still pass.

## Verification

- Compile with `-fsanitize=address,undefined`. A leak shows at exit as `LeakSanitizer: detected memory leaks` with the allocation stack; a double free as `attempting double-free`.
- Keep a static counter of live objects (as `alive` here) and assert it returns to its start value at the end of each test.
- Use `static_assert(std::is_nothrow_move_constructible_v<T>)` to pin the `noexcept` contract.
- For move correctness, assert the moved-from object is *usable*: destroy it, assign to it, call `size()`.
- Valgrind (`valgrind --leak-check=full ./a.out`) is an independent second opinion on Linux.

## Failure modes

| Mistake | What you observe |
|---|---|
| Default copy of a class owning a raw pointer | double free, crash at scope exit; ASan `attempting double-free` |
| Move constructor forgets to null the source | same double free, but only when moves occur |
| `return std::move(local)` | extra move, warning `-Wpessimizing-move` |
| Move operations without `noexcept` | `vector` growth copies elements (3 copies instead of 3 moves in exercise 8) |
| Using a moved-from `unique_ptr` without checking | null dereference; the moved-from smart pointer is guaranteed null |
| `shared_ptr` cycles (parent owns child, child owns parent) | memory never freed; use `weak_ptr` for the back link |
| `new` in an argument list, `f(shared_ptr<A>(new A), g())` | leak if `g()` throws between the allocation and construction (pre-C++17 evaluation order); use `make_shared`/`make_unique` |
| Throwing from a destructor | `std::terminate` during unwinding |

## Alternatives and trade-offs

- **Value vs `unique_ptr`**: a plain member or a local is the default; use `unique_ptr` when you need polymorphism, an optional object, or an address that must stay stable.
- **`unique_ptr` vs `shared_ptr`**: shared ownership costs an atomic reference-count update per copy and makes lifetime hard to reason about. Use it only when the lifetime is genuinely shared, preferably of `const` data.
- **Raw pointers and references** are fine as *non-owning* views. If you can state the lifetime in a comment, you may pass them; if not, redesign.
- **Move vs copy vs share for large data**: copy 1 MB at 30 Hz is 30 MB/s of memory traffic and a latency spike; a move or a pool is $O(1)$.
- **Garbage-collected languages** release memory but not files, sockets or locks promptly; RAII handles all resource kinds deterministically.

## Transfer and retention

The same principle is `with` in Python, `defer` in Go and `Drop` in Rust (where moves are the default). In ROS 2, `rclcpp::Subscription` callbacks can receive `std::unique_ptr<Msg>` for zero-copy intra-process transfer, exactly the pattern of exercise 10. Spaced review: after one week, rewrite from memory the `Buffer` move constructor and move assignment, and explain why each line is there. Questions to keep asking in code review: who owns it, where does it die, can it throw while half-built?

## Exercise answers

1. `lock_guard` locks in its constructor and unlocks in its destructor; destructors run during stack unwinding if code throws, so the mutex is always released. With manual `lock()`/`unlock()` an exception (or an early `return`) skips `unlock()`, leaving the mutex locked forever and other threads blocked (deadlock).
2. `+a +b +c -c -b +d -d -a`: inner scope objects are destroyed in reverse order at `}`, then `d`, then `a`.
3. Cycles: $100\cdot600=60{,}000$; early path: $60{,}000/4=15{,}000$ leaks; each is $256\cdot8=2048$ bytes, so $30{,}720{,}000$ bytes ($\approx30.7$ MB). The checker reports at exit, but a robot never exits during the mission: memory grows until the allocator fails or the OOM killer acts, so it is a real fault, only later.
4. `Scan b = a` uses the implicit copy constructor, copying the pointer; both destructors call `delete[]` on the same address: double free. Fixes: (1) delete copy operations and add moves (rule of five); (2) keep `std::unique_ptr<double[]>` (rule of zero, class becomes move-only); (3) use `std::vector<double>` (rule of zero, copyable, bounds via `.at()`). The best is (3) unless the size is fixed and copying is forbidden.
5. It prints `17`. A moved-from `unique_ptr` is guaranteed to be null (that is a specified postcondition, unlike most standard types).
6. (a) `const Frame&` (borrow, non-null, caller keeps it); (b) `std::unique_ptr<Source>` by value (takes exclusive ownership; the pipeline lives as long as the source); (c) `std::shared_ptr<const Frame>` or `unique_ptr<Frame>` moved into the thread (the callee outlives the caller, so a borrow is a dangling-reference bug); (d) `const Calibration*` (optional borrow; a reference cannot express "absent").
7. `f1`: 0 moves (elided by NRVO / the object is constructed in place). `f2`: 1 move, because `std::move` disables elision. `return c;` is preferred; the compiler treats it as a move anyway if elision is not possible.
8. For `W` (noexcept): 7 moves, 0 copies: 4 for the new elements plus 3 relocations (1, then 2 elements moved on the two reallocations). For `V`: 4 moves (new elements) and 3 copies (relocations): `std::vector` uses `move_if_noexcept` and copies to keep the strong guarantee. Exact numbers depend on the growth factor of the standard library (GCC doubles); the lesson is the 0 versus 3 copies.
9. With `b = std::move(b)`, `o` aliases `*this`: `delete[] data_` frees the storage, then `data_ = o.data_` assigns the dangling address, then `o.data_ = nullptr` nulls both (they are the same object), so the final state is `data_ == nullptr`, `size_ == 0`: the data is destroyed although a self-move should leave a valid object (silently losing data). Fix 1: `if (this != &o) {...}`. Fix 2: `std::swap(data_, o.data_); std::swap(size_, o.size_);` which is self-safe, and leaves the *old* contents of `*this` in `o` (freed when `o` dies); the identity check version leaves `o` empty immediately.
10. (i) Copy: $1\ \text{MB}\cdot30=30$ MB/s plus an allocation or lock; risk: latency jitter, but simplest and safe. (ii) `shared_ptr<const Frame>`: no copy, the planner keeps the frame alive for as long as it needs; risk: unbounded memory if the planner is slow (frames pile up), and atomic refcount contention. (iii) Pool with `unique_ptr`: no copy and bounded memory, the planner gets sole ownership and returns it; risk: exhaustion handling and more complex return path. A good answer chooses (ii) with a bounded queue or (iii) when memory must be bounded, and states the lifetime rule in the interface.
11. A good answer contains: constructor calls `dev_open` and throws on failure; destructor calls `dev_close` if the handle is valid (`-1` means empty); deleted copy, `noexcept` moves that invalidate the source's handle; tests that count open handles at exit of a scope, after `throw`/`catch`, and after `vec.push_back(std::move(d))` followed by vector destruction; the `unique_ptr` variant uses a deleter calling `dev_close` on the handle (with `std::unique_ptr<std::remove_pointer_t<Handle>, Deleter>` or a small handle wrapper).

12. (a) In `a = b` the by-value parameter `o` is built from `b` by the copy constructor *before* the body starts. If it throws, control leaves the function before `swap`, so nothing in `*this` has been touched and `a` still holds its 1000 doubles. If it succeeds, `swap` exchanges two scalars and cannot throw, so the assignment is all-or-nothing. (b) Measured with an instrumented class (g++ 11.4, `-std=c++17`): `a = b`: 1 copy, 0 moves, 1 allocation; `a = std::move(b)`: 0 copies, 1 move, 0 allocations; `a = a`: 1 copy, 1 allocation (it copies itself into `o`, swaps, and frees the old block: harmless but wasteful). (c) After `a = b`, `a` has 500 elements equal to `b`'s and `b` is unchanged; after the move, `a` has 500 elements and `b` has 0 (its move constructor emptied it); after `a = a`, `a` keeps 500 elements. (d) With both `operator=(const Buffer&)` and `operator=(Buffer)` declared, `a = b` binds an lvalue to either with the same conversion cost, so g++ reports "ambiguous overload for operator=" and you must choose one. Keep a dedicated `const Buffer&` overload when assignment is hot and sizes are often equal: it can reuse existing storage with no allocation (as `std::vector` does) and can still give the strong guarantee if you check capacity first and copy before changing size.
13. (a) `use_count()` is 2 for both (the local plus the other node's link). At scope end each count drops from 2 to 1, neither reaches 0, so there is **no destructor output at all**: both nodes leak. (b) With `A` holding `shared_ptr` to `B` and `B` holding `weak_ptr` to `A`: while both locals live, `A.use_count()=1` and `B.use_count()=2` (measured). At scope end `b` is released first (2 to 1), then `a` (1 to 0), `A` is destroyed and releases its `next`, so `B` follows: output `~A ~B`. `weak_ptr` does not raise the strong count; `lock()` yields a temporary owner (count 2 while held). (c) `p.use_count()=2` and `y.use_count()=2`, since both share one control block; after `p.reset()`, `y.use_count()=1`. The entire `P` object stays alive because the control block owns it, and `y` points into it, so reading `*y` is valid. Ownership (the control block) and the stored pointer are decoupled in the aliasing constructor.
14. First variant: the body throws after both `new`s, the destructor never runs, and the members are raw pointers, so both blocks leak: $30\cdot8+90\cdot8=960$ bytes per attempt (measured with a counting `operator new`: 960). Second variant: `a` was allocated ($240$ bytes) and then `b`'s initialiser throws, so only $240$ bytes leak (measured: 240). With `std::unique_ptr<double[]> a, b;` the rule is: when a constructor exits by exception, the members and bases that were *completely* constructed are destroyed in reverse order. `a` is a complete `unique_ptr`, so its destructor frees the block; `b` never completed, so there is nothing to free; measured leak 0 in both cases. Retry loop: $10\ \text{Hz}\cdot300\ \text{s}=3000$ attempts, $3000\cdot960=2{,}880{,}000$ bytes (about 2.9 MB) lost.
15. (a) With the throwing move and a copyable type, `vector` uses `move_if_noexcept`, which selects the copy. It allocates a new block of capacity 8, constructs the new element, then copies the old elements one by one: copies 1 and 2 succeed, copy 3 throws. Measured: copies = 3 (the failing one counted), moves = 0, size 4, capacity 4, ids `0 1 2 3`. The two new copies and the new element are destroyed and the new block is freed, so the vector is exactly as before: the strong guarantee. (b) With `noexcept` on the move constructor the elements are moved: measured copies = 0, moves = 4, size 5, capacity 8, no exception. (c) Suppose relocation moves elements $1..k-1$ and the $k$-th move throws. The sources $1..k-1$ now hold moved-from values, and restoring them needs $k-1$ moves back, which are themselves allowed to throw, so a guaranteed rollback does not exist in general. A copy leaves the sources intact, hence the rule. If `T` is move-only (no copy to fall back on) and its move throws, `vector` still uses the move, and the strong guarantee is waived: the effects are unspecified, and only the basic guarantee can be hoped for.

## Further reading

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - sections R (resource management), C.20-C.22 (rule of zero/five), F.15-F.26 (parameter passing).
- [cppreference: std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr) - complete interface, deleters, and the moved-from guarantee.
- [LearnCpp](https://www.learncpp.com/) - the chapters on smart pointers and move semantics, with step-by-step examples.
- [cppreference: std::shared_ptr](https://en.cppreference.com/w/cpp/memory/shared_ptr) - control block, aliasing constructor, `weak_ptr` and thread-safety notes.
- [C++ standard draft, [except.ctor]](https://eel.is/c++draft/except.ctor), [[class.dtor]](https://eel.is/c++draft/class.dtor) and [[class.copy.elision]](https://eel.is/c++draft/class.copy.elision) - the exact wording behind unwinding order, member destruction and implicit move on return.
- [cppreference: std::move_if_noexcept](https://en.cppreference.com/w/cpp/utility/move_if_noexcept) and [`std::vector::emplace_back`](https://en.cppreference.com/w/cpp/container/vector/emplace_back) - the exact exception-safety wording used in the relocation argument.

**More practice:** the quizzes on [LearnCpp: intro to smart pointers and move semantics](https://www.learncpp.com/cpp-tutorial/introduction-to-smart-pointers-move-semantics/) and [LearnCpp: std::unique_ptr](https://www.learncpp.com/cpp-tutorial/stdunique_ptr/) (answers are shown on the page), [LearnCpp: std::move](https://www.learncpp.com/cpp-tutorial/stdmove/), and the [Core Guidelines resource management section (R)](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management) as a review checklist for your own `Buffer`.