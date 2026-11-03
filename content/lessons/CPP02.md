---
{
  "id": "cpp02-foundations",
  "module_id": "CPP02",
  "title": "Memory, references, and lifetime",
  "summary": "Explain who owns an object and how long a reference stays valid.",
  "estimated_minutes": 280,
  "prerequisites": [
    "CPP01"
  ],
  "source_refs": [
    {
      "title": "LearnCpp",
      "url": "https://www.learncpp.com/"
    }
  ],
  "objectives": [
    "Distinguish values, addresses, pointers, and references.",
    "Identify dangling references and invalidated storage.",
    "Use RAII and standard containers for ownership."
  ],
  "core_theory": [
    "Memory, references, and lifetime"
  ],
  "labs": [
    "Draw lifetimes for a value, reference, and unique_ptr across nested scopes. Write a safe function returning a vector by value. In a separate intentional experiment, use a sanitizer to identify a dangling reference; do not run undefined behavior in robot control code."
  ],
  "assessment_refs": [
    "CPP02-diagnostic-v1"
  ],
  "review_prompts": [
    "A callback stores a pointer to a temporary sensor buffer. Describe a failure scenario and redesign the ownership contract so the callback can safely outlive the producer call."
  ],
  "extension_refs": [
    "https://www.learncpp.com/"
  ]
}
---

## Why this matters

Explain who owns an object and how long a reference stays valid. This lesson develops the core calculation before asking you to apply it in a new setting. Start with the diagnostic if you think you already know it; prior tool use is not evidence of understanding.

## Intuition

A pointer is a value that can refer to an object in memory; it is not ownership by itself. A reference is an alias. Correctness depends on whether the object still exists and whether an operation moved its storage. Drawing object lifetimes is often more useful than staring at addresses.

![Timeline of a vector reallocation: a pointer to element 0 in the old block becomes dangling after the elements move to a larger block, while a unique_ptr transfers a single ownership arrow.](/lesson-figures/CPP02.svg)

*A pointer is only as valid as the object it points to; reallocation and scope exit both end lifetimes.*

## Theory and derivation

An automatic local object is destroyed when its scope ends. Returning a pointer or reference to it leaves a dangling handle. Copying a value creates another object with its own lifetime; copying a pointer only creates another address value.

`std::vector` owns contiguous element storage. Growing beyond capacity can allocate a new block, move elements, and invalidate pointers, references, and iterators to the old storage. A vector object can remain alive while a pointer to one of its former elements becomes invalid. Do not rely on observed address stability from one run.

RAII associates resource release with object destruction. `std::unique_ptr<T>` owns one dynamically allocated object and cannot be copied; moving transfers ownership. `std::shared_ptr<T>` shares ownership with a reference count and additional cost. Neither automatically makes access thread-safe. Prefer values and containers until dynamic ownership is actually needed.

To inspect suspected memory errors, compile your own code with `-fsanitize=address,undefined -g`. Sanitizers detect many executed invalid operations; passing one run is not proof that every lifetime is correct.

## Worked example

A function `const int& bad(){ int x=3; return x; }` returns a reference after x has been destroyed. In contrast, `int good(){ int x=3; return x; }` returns a value. With vector v, taking &v[0] and then causing a reallocation can invalidate that pointer even though v still exists.

## Exercises

1. **(Easy)** For each snippet say whether the returned handle is valid, and why: (a) `int f() { int x = 3; return x; }`; (b) `const int& g() { int x = 3; return x; }`; (c) `int* h() { static int x = 3; return &x; }`. For the invalid one, name the C++ term for what the caller now holds. *(Adapted from: C++ Core Guidelines, F.43 on returning pointers or references to locals)*
2. **(Easy)** Predict the output and say how many `int` objects exist at the end:
   ```cpp
   auto a = std::make_unique<int>(7);
   auto b = std::move(a);
   std::cout << (a == nullptr) << ' ' << *b;
   ```
   Why does the line `auto c = b;` not compile, and why is that a feature for a robot driver that owns a device handle? *(Adapted from: cppreference, std::unique_ptr)*
3. **(Medium)** **Find the bug.** A logger keeps the latest lidar scan:
   ```cpp
   struct Logger {
       const std::vector<double>* last = nullptr;
       void on_scan(const std::vector<double>& s) { last = &s; }
   };
   void tick(Logger& log) {
       std::vector<double> scan = read_lidar();   // 360 ranges
       log.on_scan(scan);
   }
   ```
   When does `last` become invalid? Give two fixes (one copying, one sharing ownership) and estimate the copy cost at 10 Hz.
4. **(Medium)** Code takes `double* p = &v[0];` and then calls `v.push_back(x)` in a loop. Explain, using capacity, when `p` stops being valid. If capacity doubles starting from 1, how many allocations happen while pushing 100 elements, and what call removes them when you know the final size?
5. **(Medium)** A planner and a visualiser both read the same map built once at startup. Decide between a value copy, `unique_ptr`, `shared_ptr<const Map>`, and a raw pointer. Justify your choice and name one cost.
6. **(Medium)** **Find the bug.**
   ```cpp
   void load(const std::string& path) {
       Config* c = new Config();
       if (!c->read(path)) return;     // early return
       apply(*c);
       delete c;
   }
   ```
   Which path leaks? If a leaked `Config` is 2 MB and `load` fails 5 times per second, how much memory leaks in 10 minutes? Rewrite it so no path can leak. *(Adapted from: C++ Core Guidelines, R.11 and R.20 on owning resources)*
7. **(Hard)** Two nodes hold each other: `struct Node { std::shared_ptr<Node> peer; };` and `a->peer = b; b->peer = a;`. Track the reference counts as the last outside handles go away, explain why the nodes are never destroyed, and fix it with `weak_ptr`.
8. **(Hard)** **Read a sanitizer report.** AddressSanitizer reports `heap-use-after-free` on a read in `Controller::update`, with "freed by thread T0 here" pointing into `std::vector<Sample>::push_back` and "previously allocated" in `Controller::record`. Reconstruct the most likely bug, say how you would confirm it, and why a clean run elsewhere proves little. *(Adapted from: the AddressSanitizer documentation in the Clang manual)*
9. **(Hard)** Design the ownership of a camera pipeline: a driver produces frames, a detector and a recorder consume them at different rates. Choose types for frames and queues, who owns what, and how a slow recorder avoids keeping the driver's buffer alive indefinitely.
10. **(Project)** Write a `Tracked` class that counts live objects. Build three scenarios (move a `unique_ptr`, destroy an element of a vector, force a vector reallocation) and assert the live count after each. Run it under `-fsanitize=address,undefined`, then deliberately introduce a dangling reference and capture the report.

## Reference implementation

Read the contract first. Predict the output before running the code locally. This reference is for studying; a submission copied from it is assisted practice, not independent evidence.

```cpp
#include <memory>
#include <cassert>
int main() {
    auto a = std::make_unique<int>(7);
    auto b = std::move(a);
    assert(!a);
    assert(*b == 7);
} // b releases the object here
```

## Independent practice

### Goal
Make ownership observable: count live objects while moving, destroying and reallocating, and see a vector invalidate a stored address. Finish by running the program under the sanitizers.

### Setup
A C++17 compiler. Put the starter and tests in `lab.cpp` and build with `g++ -std=c++17 -Wall -Wextra -Wpedantic -g lab.cpp -o lab && ./lab`; then again with `-fsanitize=address,undefined`.

### Tasks
1. Implement `make_tracked` and `transfer`; before running, predict `Tracked::live` after each line of the first test block.
2. Implement `pick_larger`; check that the discarded object is destroyed without any explicit `delete`.
3. Implement `make_ramp` returning by value and explain why this is safe.
4. Implement `reallocation_moves_storage` and `weak_expires_after_reset`.
5. Rebuild with sanitizers. Then in a scratch file take `int* p = &v[0]`, push until reallocation, read `*p`, and record the sanitizer's report (do not keep this in the lab file).

### Starter code
```cpp
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

struct Tracked {                       // given: counts live objects
    static int live;
    int id;
    explicit Tracked(int i) : id(i) { ++live; }
    Tracked(const Tracked&) = delete;
    Tracked& operator=(const Tracked&) = delete;
    ~Tracked() { --live; }
};
int Tracked::live = 0;

// Create a Tracked with this id, owned by the returned unique_ptr.
std::unique_ptr<Tracked> make_tracked(int id) { throw std::logic_error("not implemented"); }

// Take ownership of p and give it back to the caller (move, never copy).
std::unique_ptr<Tracked> transfer(std::unique_ptr<Tracked> p) { throw std::logic_error("not implemented"); }

// Return the object with the larger id; the other one must be destroyed.
std::unique_ptr<Tracked> pick_larger(std::unique_ptr<Tracked> a, std::unique_ptr<Tracked> b) { throw std::logic_error("not implemented"); }

// Return n values 0.0, 1.0, ... by value (no pointers to locals).
std::vector<double> make_ramp(std::size_t n) { throw std::logic_error("not implemented"); }

// Fill a vector<int> to exactly its capacity, remember data() as an integer,
// push_back one more element, and return true if the storage moved.
bool reallocation_moves_storage() { throw std::logic_error("not implemented"); }

// Make a shared_ptr<Tracked>, take a weak_ptr to it, reset the shared_ptr,
// and return whether the weak_ptr is now expired.
bool weak_expires_after_reset() { throw std::logic_error("not implemented"); }
```

### Tests
Paste this below the starter code (same file) and run it. Every check is a plain `assert`; the first failure stops the run.

```cpp
int main() {
    assert(Tracked::live == 0);
    {   // moving ownership does not create or destroy objects
        auto a = make_tracked(5);
        assert(Tracked::live == 1);
        auto b = transfer(std::move(a));
        assert(a == nullptr && b != nullptr && b->id == 5 && Tracked::live == 1);
    }
    assert(Tracked::live == 0);                         // destroyed at scope end
    {   // the loser is destroyed inside pick_larger
        auto big = pick_larger(make_tracked(3), make_tracked(9));
        assert(big->id == 9 && Tracked::live == 1);
        auto tie = pick_larger(make_tracked(4), make_tracked(4));
        assert(Tracked::live == 2);
    }
    assert(Tracked::live == 0);
    {   // elements of a vector of unique_ptr are owned by the vector
        std::vector<std::unique_ptr<Tracked>> v;
        for (int i = 0; i < 3; ++i) v.push_back(make_tracked(i));
        assert(Tracked::live == 3);
        v.erase(v.begin());
        assert(Tracked::live == 2);
    }
    assert(Tracked::live == 0);
    auto r = make_ramp(4);
    assert(r.size() == 4 && r[0] == 0.0 && r[3] == 3.0 && make_ramp(0).empty());
    assert(reallocation_moves_storage());               // old pointers would dangle
    assert(weak_expires_after_reset() && Tracked::live == 0);
    std::cout << "ramp size " << r.size() << ", live objects at end " << Tracked::live << "\n";
    std::cout << "all tests passed\n";
}
```

### Expected output
A correct solution prints the following; with sanitizers the output is identical and no report appears.

```text
ramp size 4, live objects at end 0
all tests passed
```

### Extension challenge
Write `class SampleBuffer` that owns a `std::vector<double>`, exposes `const std::vector<double>& samples() const`, and provides `void push(double)`. Show with a test that a stored reference from `samples()` stays valid across `push` only if you `reserve` first, and document that contract in a comment.

## Verification

Check the worked numerical example independently, then test a boundary case and an invariant from the derivation. Keep the expected result separate from the implementation. Change a sign or remove one term deliberately: your tests should reject that broken version. Use the diagnostic to check concepts and numerical reasoning; short answers remain rubric-guided practice.

## Failure modes

“The address still contains 3” does not make a destroyed object valid. Shared ownership prevents some premature destruction but can introduce cycles and does not fix data races.

## Alternatives and trade-offs

Value semantics simplify lifetime reasoning. unique_ptr expresses exclusive ownership. shared_ptr is useful for genuinely shared lifetimes but adds coupling and overhead; nonowning references remain appropriate when lifetime is guaranteed elsewhere.

## Transfer and retention

A callback stores a pointer to a temporary sensor buffer. Describe a failure scenario and redesign the ownership contract so the callback can safely outlive the producer call.

Close the reference before trying. Explain your assumptions and one way your answer could fail. Return after at least a week and reconstruct the key argument from a blank page. A quiz alone does not verify unfamiliar transfer or research-level competence.

## Exercise answers

1. (a) valid: a copy of the value is returned. (b) invalid: the local `x` is destroyed on return, so the caller holds a **dangling reference**. (c) valid while the program runs because `x` has static storage (but it is shared global state, not thread-safe).
2. Output `1 7`: after the move `a` is null and `b` owns the value; one `int` exists. `unique_ptr` is not copyable because there must be exactly one owner; for a device handle this prevents two owners both closing it.
3. `last` points at the local `scan`, which is destroyed when `tick` returns, so any later use is undefined behaviour. Fix 1: `std::vector<double> last;` and `last = s;` (copy). Fix 2: pass `std::shared_ptr<const std::vector<double>>` and store it. The copy is $360\times8=2880$ B, at 10 Hz about $29$ kB/s: negligible.
4. `p` is invalid as soon as `push_back` exceeds the current capacity, because the elements move to a new block. Capacities $1,2,4,\dots,128$ give **8** allocations for 100 elements. `v.reserve(100)` before the loop makes it one allocation and keeps pointers valid up to that size.
5. Best: `std::shared_ptr<const Map>` (read-only, lifetime tied to the last user) or, if both consumers are in the same scope and outlive nothing, a `const Map&`. A value copy duplicates a large map; `unique_ptr` cannot be shared; a raw pointer says nothing about ownership. Cost: an atomic reference count and shared lifetime that is harder to reason about.
6. The early `return` leaks `c` (the `delete` is skipped; an exception from `apply` leaks too). $2\ \text{MB}\times5\times600=6000$ MB, 6 GB. Fix: `auto c = std::make_unique<Config>();` (or just `Config c;`), with no `delete`.
7. After `a->peer = b; b->peer = a;` each node has a count of 2 (the local handle plus the peer). Dropping the local handles leaves counts of 1, held by each other, so neither reaches zero: a leak. Make one direction `std::weak_ptr<Node> peer;` (non-owning) so the counts reach zero.
8. A pointer/reference/iterator into the vector (likely stored in `record`) was used in `update` after `push_back` reallocated and freed the old block. Confirm by running the failing scenario with ASan, finding the stored address, and checking `capacity()` before/after; fix by storing an index, using `reserve`, or copying. A clean run elsewhere proves little because sanitizers only report executed paths.
9. A good design: frames are `std::shared_ptr<const Frame>` from a pool; each consumer has a bounded queue (or "latest only" slot) so a slow recorder drops or skips frames instead of pinning memory; the driver owns the pool and reuses buffers whose use count has fallen to one. It states what happens at overflow and that consumers never mutate shared frames.
10. A good answer asserts: moving a `unique_ptr` leaves the live count unchanged; destroying a vector element decrements by one; reallocating a vector of movable objects keeps the live count equal to the element count after the move (copies, if any, are destroyed). The dangling-reference experiment shows `heap-use-after-free` with allocation and free stack traces. The experiment is kept out of control code.

## Further reading

[LearnCpp](https://www.learncpp.com/) — primary course, documentation, or the supplied reference collection. Follow the relevant subject heading; these are further reading links, not reproduced book chapters.

**More practice:** [LearnCpp chapter 22 quiz](https://www.learncpp.com/cpp-tutorial/chapter-22-summary-and-quiz/) (move semantics and smart pointers), [LearnCpp std::unique_ptr](https://www.learncpp.com/cpp-tutorial/stdunique_ptr/) and [std::shared_ptr](https://www.learncpp.com/cpp-tutorial/stdshared_ptr/) lessons, the [C++ Core Guidelines resource-management rules](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management), and the [AddressSanitizer use-after-free example](https://github.com/google/sanitizers/wiki/AddressSanitizerExampleUseAfterFree).
