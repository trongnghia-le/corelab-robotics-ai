---
{
  "id": "cpp04-foundations",
  "module_id": "CPP04",
  "title": "Classes and OOP: encapsulation, interfaces, and invariants",
  "summary": "Design classes whose public operations can never leave a valid state, and use abstract interfaces for behavior that varies.",
  "estimated_minutes": 75,
  "prerequisites": [
    "CPP01",
    "CPP02"
  ],
  "source_refs": [
    {
      "title": "C++ Core Guidelines: C. Classes and class hierarchies",
      "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"
    },
    {
      "title": "cppreference: Classes",
      "url": "https://en.cppreference.com/w/cpp/language/classes"
    },
    {
      "title": "LearnCpp",
      "url": "https://www.learncpp.com/"
    }
  ],
  "objectives": [
    "State a class invariant and show that a constructor establishes it and every public member preserves it.",
    "Decide between struct and class, public data and accessors, member and free function.",
    "Design an abstract interface with a virtual destructor and avoid slicing.",
    "Recognize when inheritance violates substitutability and choose composition or templates instead."
  ],
  "core_theory": [
    "encapsulation",
    "interfaces",
    "invariants"
  ],
  "labs": [
    "Implement a JointState that rejects invalid position updates, a PController behind an abstract interface, and a control step that cannot leave the joint's limits, then try to break the invariant with hostile inputs."
  ],
  "assessment_refs": [
    "CPP04-diagnostic-v1"
  ],
  "review_prompts": [
    "A FixedJoint class derives from Joint and overrides set_position to throw. Explain what substitutability rule this breaks, and redesign the hierarchy."
  ],
  "extension_refs": [
    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines",
    "https://en.cppreference.com/w/cpp/language/classes"
  ]
}
---

## Why this matters

Robot software is full of values that only make sense inside a range: a joint angle between its limits, a unit quaternion, a gain that must be non-negative, a time step greater than zero. If these are public fields in a `struct`, any line of code anywhere can store 99 radians into a joint that physically stops at 1.5, and the bug appears later, far from its cause, perhaps as a hardware fault. A class fixes this by making the *only* way to change the state a function that checks the rule. The second half of the lesson, interfaces, is how you swap behavior (a P controller for a PID, a simulated driver for the real one) without rewriting the callers. Together they are the basis of most C++ robotics libraries: ROS 2 hardware interfaces, MoveIt planners, and controller plugins all expose small abstract interfaces over classes that guard their invariants.

## Intuition

An *invariant* is a sentence that is true every time control is outside the class's member functions. "The position is within the limits and the speed does not exceed the maximum" is one. The class is a small fortress: the constructor builds the invariant, every public function may assume it on entry and must restore it on exit, and private data keeps outsiders from touching it. If a request would break the invariant, the function refuses (returns `false` or throws) and leaves the state unchanged.

An *interface* is a contract with no state: "give me an error, I give you a command". Callers depend on the contract; implementers are free to differ. Because callers hold a reference to the abstract base, the right override is chosen at run time through the virtual table.

![Class JointState with private state and public operations as a gate, and an abstract Controller interface with two implementations](/lesson-figures/CPP04.svg)

*The public functions are the only door to the private state; an abstract Controller lets callers use any implementation.*

## Theory and derivation

### Invariants and the proof pattern

Let $I(s)$ be the invariant over state $s$. A class is correct if

1. **Establish:** after every successful constructor, $I$ holds; a failing constructor throws, so no half-built object exists.
2. **Preserve:** for each public operation $f$, if $I(s)$ holds before the call then $I(s')$ holds after, whether $f$ returned normally, returned an error code, or threw.

By induction on the number of calls, $I$ holds for every reachable state. For `JointState` with limits $[l,h]$ and speed limit $v_{\max}$: $I(q,v) \equiv l\le q\le h \;\wedge\; |v|\le v_{\max}$ (all finite). `try_set_position(q', dt)` changes the state only if $l\le q'\le h$ and $|q'-q|/dt\le v_{\max}$; then $v'=(q'-q)/dt$ satisfies $I$. Otherwise it changes nothing, so $I$ holds trivially.

Notice the implementation detail that matters: write the check as `!(lo <= q && q <= hi)` or test finiteness first. With `NaN`, every comparison is false, so `if (q < lo || q > hi) reject` would accept it.

### Design rules from the Core Guidelines

- Use `struct` when the data has *no* invariant (any combination of members is valid), e.g. `struct Pose2D { double x, y, theta; };`. Use `class` with private data when there is an invariant (C.2, C.8).
- A constructor should create a *fully initialized, valid* object or throw (C.41, C.42). Avoid two-phase `init()` functions, which allow invalid objects to exist.
- Do not return non-`const` references or pointers to private members; they bypass the gate. Return values or `const&`.
- Prefer non-member functions for operations that do not need private access, so the class stays small (C.4).
- Mark single-argument constructors `explicit` (C.46) to prevent silent conversions like `JointState j = 0.5;`.
- Each member function is `const` unless it changes the state.

### Interfaces and virtual dispatch

An abstract base class declares pure virtual functions (`= 0`) and a virtual destructor:

```cpp
struct Controller {
  virtual ~Controller() = default;
  virtual double compute(double error) const = 0;
};
```

- **Virtual destructor**: deleting a derived object through a base pointer without it is undefined behavior (C.35).
- **`override`**: lets the compiler check that you really override something.
- **Slicing**: passing `Controller c` by value copies only the base subobject, which here is not even constructible because it is abstract; for a concrete base it silently loses the derived behavior. Pass by reference or pointer (C.145) and delete the copy operations of polymorphic bases (C.67).
- **Cost**: a virtual call is an indirect call through the vtable, typically a few nanoseconds and not inlinable. It is irrelevant at 1 kHz control and relevant inside a loop over $10^8$ elements.

### Substitutability

If code works with a `Base&`, it must also work with any `Derived`. A `FixedJoint : Joint` whose `set_position` throws breaks this (the Liskov substitution principle): callers cannot tell from the type whether the call is legal. Derive only when the derived class *is a* substitutable kind of the base, otherwise use composition (a member) or separate interfaces (`Positionable` is implemented only by movable joints).

## Worked example

Design `JointState(lo=-1.5, hi=1.5, vmax=2.0)` and check one update sequence by hand. Start $q=0$, $v=0$.

1. Update `try_set_position(0.15, 0.1)`: in range ($-1.5\le0.15\le1.5$). Speed $=|0.15-0|/0.1=1.5\le2$. Accept: $q=0.15$, $v=1.5$.
2. Update `try_set_position(0.9, 0.1)`: in range. Speed $=|0.9-0.15|/0.1=7.5>2$. Reject; $q=0.15$, $v=1.5$ unchanged.
3. What is the minimum `dt` that makes the move to 0.9 legal? Need $0.75/dt\le2\Rightarrow dt\ge0.375$ s. `try_set_position(0.9, 0.375)` has speed exactly $0.75/0.375=2.0\le2$. Accept. (In floating point equality at the boundary is fragile; production code often uses a small tolerance or a slightly smaller step.)
4. `try_set_position(1.6, 10.0)`: out of range ($1.6>1.5$), reject whatever `dt` is.
5. Closed-loop check with `PController(kp=2)`, `dt=0.1`, target $1.0$, huge limits: $q_{k+1}=q_k+2(1-q_k)(0.1)=q_k+0.2(1-q_k)$, so the error shrinks by 0.8 each step: $q_k=1-0.8^k$. After 10 steps $q_{10}=1-0.107374=0.892626$.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: C++ Core Guidelines, C.2 and C.8)* For each type decide `struct` with public members or `class` with private members, and state the invariant if any: (a) `Vec3 {x, y, z}`; (b) `JointState`; (c) `UnitQuaternion`; (d) `LogConfig {path, level}` where level must be one of five names; (e) `RingBuffer` holding head, tail and storage.
2. **(Easy)** Predict the output, then explain what would be wrong if `~Base` were not virtual:
   ```cpp
   struct Base { Base() { std::cout << "B "; } virtual ~Base() { std::cout << "~B "; } };
   struct Der : Base { Der() { std::cout << "D "; } ~Der() override { std::cout << "~D "; } };
   int main() { Base* p = new Der; delete p; }
   ```
3. **(Easy)** A joint has limits $[-1.5, 1.5]$ rad and $v_{\max}=2$ rad/s. Starting at $q=1.0$, what is the smallest control period `dt` for which a move to $1.4$ is accepted? Is a move to $1.6$ ever accepted?
4. **(Medium)** Find the bug(s) that let a caller break the invariant, and fix the class.
   ```cpp
   class Joint {
     double q_ = 0, lo_, hi_;
    public:
     Joint(double lo, double hi) : lo_(lo), hi_(hi) {}
     double& position() { return q_; }
     void set(double q) { if (q < lo_ || q > hi_) return; q_ = q; }
   };
   // caller: Joint j(-1, 1); j.position() = 99;  j.set(NAN);
   ```
5. **(Medium)** *(Adapted from: C++ Core Guidelines, C.41)* A teammate writes `Camera c; c.init(path);` with a default constructor that leaves `fd_ = -1`. List two concrete bugs this design allows and show how to restructure it so an invalid `Camera` cannot exist, including what to do when opening can fail.
6. **(Medium)** Predict the output and explain:
   ```cpp
   struct Controller { virtual ~Controller() = default; virtual double compute(double) const { return 0; } };
   struct P : Controller { double compute(double e) const override { return 2 * e; } };
   double run(Controller c) { return c.compute(1); }
   double run2(const Controller& c) { return c.compute(1); }
   int main() { P p; std::cout << run(p) << " " << run2(p); }
   ```
7. **(Medium)** Prove by induction that a `JointState` with the constructor and `try_set_position` from this lesson keeps $l\le q\le h$ for any sequence of calls, including calls with `NaN`, negative `dt`, and exceptions. State precisely which line handles each case.
8. **(Hard)** *(Adapted from: C++ Core Guidelines, C.120 and T.1)* Three ways to let a robot swap controllers: an abstract `Controller` base with virtual calls, `std::function<double(double)>`, and a template parameter `template <class C> void run(C&)`. Compare them on run-time cost, binary size, ability to change at run time, and testability. Which would you use for a 1 kHz joint loop that must switch between P and PID at run time?
9. **(Hard)** A hierarchy has `Joint` with `virtual void set_position(double)` and `FixedJoint : Joint` that throws `std::logic_error`. A planner calls `set_position` on every joint of a mixed list. Explain the defect, then redesign twice: once with separate interfaces and once with composition, and say which keeps call sites simplest.
10. **(Hard)** `JointArray` holds six `JointState`s and offers `try_set_all(std::array<double,6> q, double dt)`. Specify a semantic where either all joints move or none do, show why a naive loop calling `try_set_position` joint by joint breaks it, and give an implementation plan (two-phase: validate all, then commit). What invariant ties the joints together?
11. **(Mini-project)** Extend the lab's `JointState` with a `Limits` value type (a validated `struct`-like class) and a `JointGroup` of named joints. Add a fuzz test that applies 100,000 random `(q, dt)` pairs (including NaN, infinities, zeros) and checks the invariant after every call; report the acceptance rate.

## Reference implementation

`JointState` enforces its invariant, `Controller` is the abstract interface, `PController` implements it, and `step` is a free function that uses only the public interface. Build with `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

```cpp
// CPP04 reference: a joint state that can never leave its invariant, plus a small interface hierarchy.
#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <stdexcept>

// Invariant: lo <= q <= hi, |v| <= vmax, all values finite.
class JointState {
 public:
  JointState(double lo, double hi, double vmax, double q0 = 0.0)
      : lo_(lo), hi_(hi), vmax_(vmax), q_(q0) {
    if (!std::isfinite(lo) || !std::isfinite(hi) || !(lo < hi)) throw std::invalid_argument("bad limits");
    if (!std::isfinite(vmax) || !(vmax > 0.0)) throw std::invalid_argument("bad vmax");
    if (!(lo <= q0 && q0 <= hi)) throw std::invalid_argument("q0 outside limits");
  }

  double position() const { return q_; }
  double velocity() const { return v_; }
  double lo() const { return lo_; }
  double hi() const { return hi_; }
  double vmax() const { return vmax_; }

  // Moves to q over dt seconds. Returns false and changes nothing if the move would
  // violate the position limits or the speed limit (or if dt or q are not usable).
  bool try_set_position(double q, double dt) {
    if (!std::isfinite(q) || !(dt > 0.0) || !std::isfinite(dt)) return false;
    if (q < lo_ || q > hi_) return false;
    const double v = (q - q_) / dt;
    if (std::fabs(v) > vmax_) return false;
    q_ = q;
    v_ = v;
    return true;
  }

  // Same, but reports a rejection with an exception.
  void set_position(double q, double dt) {
    if (!try_set_position(q, dt)) throw std::domain_error("rejected joint update");
  }

 private:
  double lo_, hi_, vmax_;
  double q_;
  double v_ = 0.0;
};

// Interface: a controller maps an error to a velocity command.
struct Controller {
  virtual ~Controller() = default;
  virtual double compute(double error) const = 0;
};

class PController : public Controller {
 public:
  explicit PController(double kp) : kp_(kp) {
    if (!std::isfinite(kp) || kp < 0.0) throw std::invalid_argument("kp must be finite and >= 0");
  }
  double compute(double error) const override { return kp_ * error; }

 private:
  double kp_;
};

// One control step: command velocity, clamp it to vmax and the target to the limits, then apply.
void step(JointState& j, const Controller& c, double target, double dt) {
  const double cmd = std::clamp(c.compute(target - j.position()), -j.vmax(), j.vmax());
  const double q = std::clamp(j.position() + cmd * dt, j.lo(), j.hi());
  j.set_position(q, dt);
}

// ---- self-test
int main() {
  JointState j(-1.0, 1.0, 2.0);
  if (!j.try_set_position(0.15, 0.1) || j.position() != 0.15) return 1;
  if (j.try_set_position(0.9, 0.1) || j.position() != 0.15) return 2;  // 7.5 rad/s > 2
  bool threw = false;
  try { JointState bad(1.0, -1.0, 1.0); } catch (const std::invalid_argument&) { threw = true; }
  if (!threw) return 3;
  JointState k(-10.0, 10.0, 100.0);
  std::unique_ptr<Controller> c = std::make_unique<PController>(2.0);
  for (int i = 0; i < 10; ++i) step(k, *c, 1.0, 0.1);
  if (std::fabs(k.position() - (1.0 - std::pow(0.8, 10))) > 1e-12) return 4;
  std::cout << "CPP04 reference self-test passed\n";
}
```

## Independent practice

### Goal

Build a class that can be neither constructed nor updated into an invalid state, and prove it with a hostile-input test.

### Setup

`g++` or `clang++` with C++17. Save the starter code and the tests below as `lab.cpp`, then run

```
g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab
```

### Tasks

1. Implement the constructor with all four validations and the const getters.
2. Implement `try_set_position`: check finiteness first, then dt, then range, then speed; mutate only after all checks pass.
3. Implement `set_position` on top of `try_set_position`.
4. Implement `PController` and verify the closed form $q_k=1-0.8^k$ by hand with a calculator for $k=1,2,3$.
5. Implement `step` with the two clamps, then run the hostile test (gain $10^6$, alternating targets).
6. Add a fifth rejection case of your own to the tests (for example `+INFINITY`) and write down which line of your code handles it.

### Starter code

```cpp
#include <algorithm>
#include <cmath>
#include <memory>
#include <stdexcept>

// Invariant to enforce in EVERY public operation: lo <= q <= hi, |v| <= vmax, all finite.
class JointState {
 public:
  // Throws std::invalid_argument unless lo < hi (both finite), vmax finite and > 0, lo <= q0 <= hi.
  JointState(double lo, double hi, double vmax, double q0 = 0.0) {
    throw std::logic_error("NotImplemented");
  }
  double position() const { throw std::logic_error("NotImplemented"); }
  double velocity() const { throw std::logic_error("NotImplemented"); }  // (q_new - q_old) / dt of the last accepted move, 0 initially
  double lo() const { throw std::logic_error("NotImplemented"); }
  double hi() const { throw std::logic_error("NotImplemented"); }
  double vmax() const { throw std::logic_error("NotImplemented"); }

  // Move to q over dt seconds. Return false and change NOTHING if q is NaN/inf, dt is not
  // finite and > 0, q is outside [lo, hi], or |q - position| / dt > vmax. Otherwise apply, return true.
  bool try_set_position(double q, double dt) { throw std::logic_error("NotImplemented"); }
  // Like try_set_position but throws std::domain_error on rejection.
  void set_position(double q, double dt) { throw std::logic_error("NotImplemented"); }
};

struct Controller {  // given: an abstract interface
  virtual ~Controller() = default;
  virtual double compute(double error) const = 0;
};

// Proportional controller: compute(e) = kp * e. Throws std::invalid_argument if kp < 0 or not finite.
class PController : public Controller {
 public:
  explicit PController(double kp) { throw std::logic_error("NotImplemented"); }
  double compute(double error) const override { throw std::logic_error("NotImplemented"); }
};

// One control step: cmd = clamp(c.compute(target - position), -vmax, vmax);
// q = clamp(position + cmd * dt, lo, hi); then j.set_position(q, dt).
void step(JointState& j, const Controller& c, double target, double dt) {
  throw std::logic_error("NotImplemented");
}
```

### Tests

```cpp

// ---- tests (paste below the starter code)
#include <cmath>
#include <cstdlib>
#include <iostream>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)
template <class E, class F> bool throws(F f) { try { f(); } catch (const E&) { return true; } return false; }

int main() {
  // 1. construction and invariants
  JointState j(-1.0, 1.0, 2.0);
  CHECK(j.position() == 0.0 && j.velocity() == 0.0 && j.lo() == -1.0 && j.hi() == 1.0 && j.vmax() == 2.0);
  CHECK(throws<std::invalid_argument>([] { JointState(1.0, -1.0, 1.0); }));
  CHECK(throws<std::invalid_argument>([] { JointState(-1.0, 1.0, 0.0); }));
  CHECK(throws<std::invalid_argument>([] { JointState(-1.0, 1.0, 1.0, 1.5); }));
  CHECK(throws<std::invalid_argument>([] { JointState(NAN, 1.0, 1.0); }));
  // 2. accepted move (hand computed: 0.15 / 0.1 = 1.5 rad/s <= 2)
  CHECK(j.try_set_position(0.15, 0.1));
  CHECK(j.position() == 0.15 && std::fabs(j.velocity() - 1.5) < 1e-12);
  // 3. rejections change nothing: too fast, outside limits, NaN, bad dt
  CHECK(!j.try_set_position(0.9, 0.1));   // 7.5 rad/s
  CHECK(!j.try_set_position(1.5, 10.0));  // outside [lo, hi]
  CHECK(!j.try_set_position(NAN, 0.1));
  CHECK(!j.try_set_position(0.2, 0.0));
  CHECK(!j.try_set_position(0.2, -1.0));
  CHECK(j.position() == 0.15 && std::fabs(j.velocity() - 1.5) < 1e-12);
  CHECK(throws<std::domain_error>([&] { j.set_position(5.0, 1.0); }));
  // 4. boundary value is allowed
  JointState b(-1.0, 1.0, 100.0);
  CHECK(b.try_set_position(1.0, 1.0) && b.position() == 1.0);
  // 5. controller: closed form q_k = 1 - 0.8^k for kp = 2, dt = 0.1, huge vmax
  JointState k(-10.0, 10.0, 100.0);
  std::unique_ptr<Controller> c = std::make_unique<PController>(2.0);
  for (int i = 0; i < 10; ++i) step(k, *c, 1.0, 0.1);
  CHECK(std::fabs(k.position() - (1.0 - std::pow(0.8, 10))) < 1e-12);
  CHECK(throws<std::invalid_argument>([] { PController(-1.0); }));
  // 6. invariant under a hostile controller: huge gain, limited joint never leaves its box
  JointState h(-0.5, 0.5, 1.0);
  PController wild(1e6);
  for (int i = 0; i < 100; ++i) {
    step(h, wild, (i % 2) ? 10.0 : -10.0, 0.05);
    CHECK(h.position() >= -0.5 && h.position() <= 0.5 && std::fabs(h.velocity()) <= 1.0 + 1e-12);
  }
  std::cout << "all tests passed\n";
}
```

### Expected output

```
all tests passed
```

### Extension challenge

Make `Limits` and `JointState` constexpr-friendly, or add a `Joint` template parameter for the unit (radians versus meters) so that passing a prismatic position to a revolute joint does not compile.

## Verification

- Write the invariant as an `assert`-style `bool invariant() const` private function and call it at the end of every mutating function in debug builds.
- Hostile-input (fuzz) testing: random values, plus the special set `{0, -0, NaN, +inf, -inf, DBL_MAX, DBL_MIN}`. The invariant must hold after each call.
- Test the *rejection* path as carefully as the accepted path: the state must be unchanged, which you check by reading all getters before and after.
- Run under `-fsanitize=undefined` to catch signed overflow or invalid casts; check `-Wall -Wextra -Wnon-virtual-dtor` for missing virtual destructors.
- Compare closed-loop output against a short Python simulation with the same constants.

## Failure modes

| Mistake | Effect |
|---|---|
| Public data members for a value with a range | any code can store an invalid value; fails far from the cause |
| `if (q < lo \|\| q > hi) reject` | NaN passes validation and poisons later arithmetic |
| Getter returning `double&` | `j.position() = 99` bypasses all checks |
| Updating state before the last check | rejected call leaves a half-modified object |
| Non-virtual destructor on a polymorphic base | undefined behavior on `delete base_ptr`; derived part not destroyed |
| Passing a polymorphic object by value | slicing: the base implementation runs (output `0` instead of `2` in exercise 6) |
| Override typo (`const` missing) | silently a new function, base version runs; use `override` |
| Inheriting to reuse code rather than to substitute | callers must know the concrete type |

## Alternatives and trade-offs

- **Reject by `bool` or by exception.** A `bool`/`std::optional` return is natural when rejection is routine (a planner proposing many candidate updates); exceptions suit programmer errors and constructor failures. Real-time loops often forbid exceptions, so offer `try_` variants.
- **Clamp or reject.** Clamping always yields a valid state but hides errors; rejection exposes them. Safety-relevant code usually rejects and logs, and a separate layer clamps.
- **Inheritance vs templates vs `std::function`**: virtual calls give run-time flexibility at an indirect-call cost; templates give zero-overhead static polymorphism but fix the type at compile time and grow code size; `std::function` is flexible and simple for callbacks but may allocate.
- **Strong types.** A wrapper like `Radians` removes unit mix-ups at compile time; it is a tiny class with an invariant.
- **Aggregates for plain data.** For messages and parameter bundles with no invariant, a plain `struct` is better: it is simpler, can be brace-initialized, and cannot be misused through accessors.

## Transfer and retention

The same pattern appears in ROS 2 `hardware_interface` (an abstract interface with `read` and `write`), in `std::mutex`/`lock_guard` (a class whose invariant is "locked iff owned"), and in `std::vector` (invariant: size ≤ capacity, storage valid). In Python the invariant is kept with properties or descriptors (PY10). To retain: pick one class from your own code, write its invariant as a sentence, and find the first function that could break it. After a week, re-derive the induction proof for a class of your own without notes.

## Exercise answers

1. (a) `struct`: any three doubles are a valid vector. (b) `class`: $l\le q\le h$, $|v|\le v_{\max}$. (c) `class`: $\|q\|=1$; operations must renormalize or reject. (d) `class`: level must be a member of the allowed set (or use an `enum class` and a struct). (e) `class`: head and tail indices lie in $[0,\text{capacity})$ and storage matches them. A good answer links each `class` to its invariant.
2. Output: `B D ~D ~B`. Without a virtual destructor, `delete p` through `Base*` is undefined behavior; in practice only `~Base` runs, so resources held by `Der` leak.
3. $|1.4-1.0|/dt\le2\Rightarrow dt\ge0.2$ s. A move to 1.6 is never accepted because it is outside $[-1.5,1.5]$ regardless of `dt`.
4. Bugs: `position()` returns a mutable reference, so `j.position() = 99` writes anywhere; the constructor does not check `lo < hi`, and the initial `q_ = 0` is outside the limits for `Joint(1, 2)`; `set(NAN)` passes because both comparisons are false; `set` fails silently (`return`) so the caller cannot know. Fix: `double position() const`; validate in the constructor (throw); write `if (!(lo_ <= q && q <= hi_)) return false;` and return a `bool`.
5. Bugs: using the camera before `init()` (fd -1 read); calling `init()` twice leaks the first descriptor; a failed `init` leaves a half object. Fix: `explicit Camera(const std::string& path)` that opens and throws on failure (or a static factory `std::optional<Camera> Camera::open(path)` when failure is routine), destructor closes, copy deleted and moves defined (CPP03).
6. Output `0 2`. `run(Controller c)` slices `p` to its `Controller` part, and the base `compute` returns 0; `run2` takes a reference, so virtual dispatch calls `P::compute` and gives $2\cdot1=2$.
7. Base: the constructor throws unless $l\le q_0\le h$ with finite limits, so $I$ holds after construction. Step: assume $l\le q\le h$. In `try_set_position`: NaN/inf `q` and bad `dt` return `false` before any write (finiteness line); `q` outside $[l,h]$ returns `false` (range line); a too-fast move returns `false` (speed line); only when all pass are `q_` and `v_` assigned, to values that satisfy $l\le q'\le h$ and $|v'|\le v_{\max}$. A `false` return leaves the state unchanged, so $I$ still holds. `set_position` throws only after `try_set_position` returned `false`, with no change. By induction $I$ holds forever.
8. A good answer: virtual call = one indirect call, no inlining, but a single compiled function and the type can change at run time (swap a `unique_ptr<Controller>`); `std::function` has similar indirect cost, may allocate on construction, simplest for lambdas and test doubles; templates are fully inlinable (fastest) but the type is fixed at compile time and each instantiation adds code. For a P/PID switch at run time, an abstract interface (or `std::variant<P, PID>` with `std::visit`) is right; the cost is negligible at 1 kHz.
9. The planner expects every `Joint` to move; `FixedJoint` breaks the contract, so the caller must check types or catch exceptions (LSP violation). Redesign A: `struct Joint` (read-only: `position`) and `struct Actuated : Joint` (adds `set_position`), with `FixedJoint : Joint` only. Redesign B: a single `Joint` class that has a `Limits` or a `Mobility` member (composition) where a fixed joint has `lo == hi`, so `set_position` rejects every move through the normal rule. A usually keeps type-safe call sites; B keeps one type and is simpler for a list of mixed joints.
10. Naive loop: joints 0-2 accept and move, joint 3 rejects, so the arm ends in a state that was never requested (a partial update). Plan: phase 1, for each joint compute the acceptance with a non-mutating `can_move(q, dt)` and collect failures; if any, return `false` without writes; phase 2, commit all (cannot fail because validated). The group invariant is "each joint satisfies its own invariant *and* the last commanded vector is consistent", i.e. the vector is always a state that passed validation as a whole.
11. A good answer includes: `Limits(lo, hi, vmax)` validating in its constructor; `JointGroup` holds `std::map<std::string, JointState>` or a vector with names; the fuzz test draws from a list of special values and from a random normal distribution; acceptance rate depends on the distribution (report it with the count of each rejection reason); the invariant check is a separate function that does not use the code under test.

## Further reading

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - section C on classes, invariants (C.2, C.40-C.42), and hierarchies (C.120-C.153).
- [cppreference: Classes](https://en.cppreference.com/w/cpp/language/classes) - precise rules for access control, constructors, virtual functions and abstract classes.
- [LearnCpp](https://www.learncpp.com/) - classes, constructors, inheritance and virtual functions with graded quizzes.

**More practice:** the chapter quizzes on classes and inheritance at [LearnCpp](https://www.learncpp.com/) (answers shown inline), and the per-rule "Enforcement" notes in the [Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines), which describe how to check each rule in real code.
