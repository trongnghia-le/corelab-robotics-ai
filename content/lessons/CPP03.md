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

![Lifetime diagram: Buffer a owns storage, a move transfers the pointer to b and leaves a empty, then both destructors run safely](/lesson-figures/CPP03.svg)

*A move transfers the owning pointer and nulls the source, so exactly one destructor frees the storage.*

## Theory and derivation

### RAII and destruction order

A local object is destroyed when its scope ends, in reverse order of construction. The destructor runs during **stack unwinding** if an exception propagates. Therefore a resource owned by a local object is released on every exit path with no `finally`. Members are destroyed in reverse declaration order, after the destructor body. A destructor must not throw (it is implicitly `noexcept`).

### The rule of zero, three, five

- **Rule of zero**: if your class owns resources only through members that already manage them (`std::vector`, `std::string`, `std::unique_ptr`), write *no* special member functions. The compiler-generated ones are correct. Prefer this.
- **Rule of three/five**: if you must manage a raw resource, define or delete all of: destructor, copy constructor, copy assignment, move constructor, move assignment. A class with a destructor that frees memory but a default copy has two objects owning the same pointer: a double free.

### Value categories and moves

An **lvalue** has a name and identity; an **rvalue** is a temporary or something you promise not to use again. `std::move(x)` does not move anything: it is a cast to an rvalue reference, which allows an overload `T(T&&)` to be selected. A move constructor should (1) steal the resource, (2) leave the source in a **valid but unspecified** state, usually empty, so that its destructor and assignment still work, and (3) be `noexcept`.

For the owning buffer used in this lesson:

$$\text{move: } \underbrace{\texttt{data\_}}_{\text{dst}} \leftarrow \texttt{src.data\_}, \quad \texttt{src.data\_} \leftarrow \texttt{nullptr}$$

Cost: a copy of $n$ doubles is $O(n)$ time and $8n$ bytes; a move is $O(1)$ (two assignments).

Why `noexcept` matters: when `std::vector` must grow, it relocates its elements. To keep its strong exception guarantee it uses `std::move_if_noexcept`: if the move constructor can throw and the type is also copyable, it *copies* instead. A forgotten `noexcept` silently turns $O(1)$ relocations into $O(n)$ copies.

### Return values and `std::move`

`return local;` already treats `local` as an rvalue and allows copy elision (NRVO). Writing `return std::move(local);` defeats NRVO and forces a move, and compilers warn (`-Wpessimizing-move`). Use `std::move` only when passing an lvalue you will not use again.

### Ownership in signatures

| Intent | Signature | Meaning |
|---|---|---|
| Use, do not keep | `const Frame&`, `Frame&` | borrower, caller keeps ownership |
| Optional borrow | `const Frame*` | may be null, still not owned |
| Take ownership | `std::unique_ptr<Frame>` by value | caller must `std::move` in |
| Give ownership | return `std::unique_ptr<Frame>` | caller owns result |
| Shared lifetime | `std::shared_ptr<const Frame>` | reference counted, use sparingly |

Use `std::make_unique<T>(args...)`; it is exception safe and avoids a naked `new`. For C APIs, give `unique_ptr` a custom deleter: `std::unique_ptr<FILE, int(*)(FILE*)> f(fopen(p, "r"), &fclose);`.

## Worked example

Trace this program, tracking `alive` (a counter incremented by every constructor and decremented by every destructor):

```cpp
Buffer a = make_ramp(3);   // (1)
Buffer b = std::move(a);   // (2)
{
  auto p = std::make_unique<Buffer>(2);  // (3)
}                          // (4)
```

1. `make_ramp(3)` builds `Buffer b(3)` inside the function; with elision the object is constructed directly into `a`. Storage `[0,1,2]` at address `A`. `alive = 1`.
2. `Buffer(Buffer&&)` runs: `b.data_ = A`, `b.size_ = 3`, then `a.data_ = nullptr`, `a.size_ = 0`. `alive = 2` (a moved-from object is still an object).
3. `make_unique<Buffer>(2)` allocates the `Buffer` object on the heap, whose constructor allocates 2 doubles. `alive = 3`.
4. At the closing brace `p` is destroyed: `unique_ptr` deletes the `Buffer`, whose destructor frees its 2 doubles. `alive = 2`.

At the end of the enclosing scope `b` is destroyed first (reverse order): `delete[] A`, `alive = 1`. Then `a`: `delete[] nullptr` is a defined no-op, `alive = 0`. Storage `A` was freed exactly once, which is the whole point. Without step 2's `a.data_ = nullptr`, both destructors would free `A`: a double free.

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

## Further reading

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - sections R (resource management), C.20-C.22 (rule of zero/five), F.15-F.26 (parameter passing).
- [cppreference: std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr) - complete interface, deleters, and the moved-from guarantee.
- [LearnCpp](https://www.learncpp.com/) - the chapters on smart pointers and move semantics, with step-by-step examples.

**More practice:** the quizzes on [LearnCpp: intro to smart pointers and move semantics](https://www.learncpp.com/cpp-tutorial/introduction-to-smart-pointers-move-semantics/) and [LearnCpp: std::unique_ptr](https://www.learncpp.com/cpp-tutorial/stdunique_ptr/) (answers are shown on the page), [LearnCpp: std::move](https://www.learncpp.com/cpp-tutorial/stdmove/), and the [Core Guidelines resource management section (R)](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management) as a review checklist for your own `Buffer`.