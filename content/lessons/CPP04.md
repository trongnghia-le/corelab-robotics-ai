---
{
  "id": "cpp04-foundations",
  "module_id": "CPP04",
  "title": "Classes and OOP: encapsulation, interfaces, and invariants",
  "summary": "Design classes whose public operations can never leave a valid state, and use abstract interfaces for behavior that varies.",
  "estimated_minutes": 395,
  "prerequisites": [
    "CPP01",
    "CPP02"
  ],
  "source_refs": [
    {
      "title": "C++ standard draft: [class.cdtor], [class.access.general]",
      "url": "https://eel.is/c++draft/class.cdtor"
    },
    {
      "title": "Itanium C++ ABI, 2.5 Virtual Table Layout",
      "url": "https://itanium-cxx-abi.github.io/cxx-abi/abi.html"
    },
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
    },
    {
      "title": "cppreference: Virtual function specifier",
      "url": "https://en.cppreference.com/w/cpp/language/virtual"
    },
    {
      "title": "MIT 6.031 Reading 7: Designing Specifications (stronger vs. weaker specs)",
      "url": "https://web.mit.edu/6.031/www/sp22/classes/07-designing-specs/"
    },
    {
      "title": "MIT 6.031 Reading 11: Abstraction Functions and Rep Invariants",
      "url": "https://web.mit.edu/6.031/www/sp22/classes/11-abstraction-functions-rep-invariants/"
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

In a six-joint arm driver running at 1 kHz, a command array arrives from the planner every millisecond. A wrist joint limited to $\pm2.9$ rad that receives 7.3 rad is more than 4 rad beyond its stop, and the fault shows up not at the line that stored the number but wherever the joint later hits the stop or the controller diverges. If the only way to write the joint's target is a function that tests the limits, the bad command is rejected at the line that issued it, with a name and a value in the log. That is the point of an invariant: faults surface where they are made.

Predict before reading on. A `Gripper` keeps its opening `width_` private, and its setter clamps every request to the range 0 to 80 mm. The class also has a public accessor `double& width() { return width_; }`. Can a caller still make the gripper hold 120 mm, and in how many lines of code? Decide, then read on; the answer follows the figure.

Three wrong intuitions recur. *Private means safe*: `private` is a compile-time check on names, and it protects the invariant only if no public function hands out a writable reference to the data. *Inheritance is for reuse*: a derived object is promised wherever the base is expected, so derive only when the derived type keeps every promise of the base; reuse of code belongs to composition. *Virtual calls are too slow for control loops*: an indirect call costs a few nanoseconds, about 0.0005 % of a 1 ms control period.

![Class JointState with private state and public operations as a gate, and an abstract Controller interface with two implementations](/lesson-figures/CPP04.svg)

*The public functions are the only door to the private state; an abstract Controller lets callers use any implementation.*

Answer to the prediction: yes, in one line, `g.width() = 120;`: the write goes through the returned reference and the clamp in the setter is never consulted. The invariant $0\le \text{width}\le 80$ holds only if every route to the data passes through a checked function, so the accessor must return a value or a `const` reference.

## Theory and derivation

### Invariants and the proof pattern

Let $I(s)$ be the invariant over state $s$. A class is correct if

1. **Establish:** after every successful constructor, $I$ holds; a failing constructor throws, so no half-built object exists.
2. **Preserve:** for each public operation $f$, if $I(s)$ holds before the call then $I(s')$ holds after, whether $f$ returned normally, returned an error code, or threw.

By induction on the number of calls, $I$ holds for every reachable state. For `JointState` with limits $[l,h]$ and speed limit $v_{\max}$: $I(q,v) \equiv l\le q\le h \;\wedge\; |v|\le v_{\max}$ (all finite). `try_set_position(q', dt)` changes the state only if $l\le q'\le h$ and $|q'-q|/dt\le v_{\max}$; then $v'=(q'-q)/dt$ satisfies $I$. Otherwise it changes nothing, so $I$ holds trivially.

Notice the implementation detail that matters: write the check as `!(lo <= q && q <= hi)` or test finiteness first. With `NaN`, every comparison is false, so `if (q < lo || q > hi) reject` would accept it.

**Example.** A motor driver accepts a duty cycle only in $[0, 0.85]$. The class below establishes that invariant in its constructor, and a second test written as `!(d < 0 || d > 0.85)` is compared with it on three inputs (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

```cpp
#include <cstdio>
#include <limits>
#include <stdexcept>
// Invariant: 0 <= duty <= 0.85 (the driver's limit), never NaN.
class DutyCycle {
  double d_;
 public:
  explicit DutyCycle(double d) : d_(d) {
    if (!(0.0 <= d && d <= 0.85)) throw std::invalid_argument("duty out of range");
  }
  double value() const { return d_; }
};
bool naive_ok(double d) { return !(d < 0.0 || d > 0.85); }   // wrong test
int main() {
  const double nan = std::numeric_limits<double>::quiet_NaN();
  double tests[] = {0.5, 0.9, nan};
  for (double d : tests) {
    bool ok = true;
    try { DutyCycle x(d); } catch (const std::invalid_argument&) { ok = false; }
    std::printf("duty %-5g  constructor accepts: %d   naive range test accepts: %d\n", d, ok, naive_ok(d));
  }
}
```

```text
duty 0.5    constructor accepts: 1   naive range test accepts: 1
duty 0.9    constructor accepts: 0   naive range test accepts: 0
duty nan    constructor accepts: 0   naive range test accepts: 1
```

The constructor uses the *positive* form `0 <= d && d <= 0.85` and negates it, so NaN (for which every comparison is false) is rejected, and the establish step of the proof holds for all inputs. The negated-comparison test accepts NaN: it would store a value outside the invariant, and the preserve step of every later call would be proved for a state that never satisfied $I$.
```explore
{
  "title": "Which updates does the gate accept?",
  "title_vi": "Cổng chấp nhận những cập nhật nào?",
  "prompt": "Predict first: from q = 0.15 with vmax = 2 rad/s, can the joint reach q' = 0.9 in dt = 0.1 s? What is the smallest dt that works? Then drag q' and dt to test your answer, and raise vmax to see the accepted region widen.",
  "prompt_vi": "Dự đoán trước: từ q = 0.15 với vmax = 2 rad/s, khớp có đạt tới q' = 0.9 trong dt = 0.1 s không? dt nhỏ nhất dùng được là bao nhiêu? Rồi kéo q' và dt để kiểm tra, và tăng vmax để thấy vùng chấp nhận rộng ra.",
  "params": [
    { "name": "q0", "label": "current q", "label_vi": "q hiện tại", "min": -1.5, "max": 1.5, "step": 0.05, "value": 0.15, "unit": "rad" },
    { "name": "qn", "label": "target q'", "label_vi": "đích q'", "min": -1.7, "max": 1.7, "step": 0.05, "value": 0.9, "unit": "rad" },
    { "name": "dt", "label": "time step dt", "label_vi": "bước thời gian dt", "min": 0.05, "max": 1, "step": 0.025, "value": 0.1, "unit": "s" },
    { "name": "vmax", "label": "speed limit vmax", "label_vi": "giới hạn tốc độ vmax", "min": 0.5, "max": 4, "step": 0.25, "value": 2, "unit": "rad/s" }
  ],
  "let": [
    { "name": "speed", "expr": "abs(qn - q0) / dt" },
    { "name": "dtmin", "expr": "abs(qn - q0) / vmax" },
    { "name": "ok", "expr": "ifpos(vmax - speed + 0.0000001, ifpos(1.5 - abs(qn) + 0.0000001, 1, 0), 0)" }
  ],
  "plot": {
    "x": { "name": "x", "min": -1.7, "max": 1.7, "label": "target q' (rad)", "label_vi": "đích q' (rad)" },
    "y": { "label": "dt (s)", "label_vi": "dt (s)", "min": 0, "max": 1 },
    "series": [
      { "expr": "abs(x - q0) / vmax", "label": "dt = |q' - q| / vmax (accepted above)", "label_vi": "dt = |q' - q| / vmax (chấp nhận phía trên)", "color": "orange" }
    ],
    "points": [
      { "x": "qn", "y": "dt", "label": "your call", "label_vi": "lời gọi của bạn", "color": "blue" }
    ]
  },
  "readouts": [
    { "label": "speed |q' - q| / dt", "label_vi": "tốc độ |q' - q| / dt", "expr": "speed", "unit": "rad/s", "digits": 3 },
    { "label": "smallest legal dt", "label_vi": "dt nhỏ nhất hợp lệ", "expr": "dtmin", "unit": "s", "digits": 3 },
    { "label": "accepted (1 yes, 0 no; limits +-1.5)", "label_vi": "được chấp nhận (1 có, 0 không; giới hạn +-1.5)", "expr": "ok", "unit": "", "digits": 0 }
  ]
}
```

*Figure: the orange line is the boundary $dt=|q'-q|/v_{\max}$; calls above it satisfy the speed test, and the position test $|q'|\le1.5$ is the second condition that the readout adds. The default reproduces step 2 of the worked example.*

### Design rules from the Core Guidelines

- Use `struct` when the data has *no* invariant (any combination of members is valid), e.g. `struct Pose2D { double x, y, theta; };`. Use `class` with private data when there is an invariant (C.2, C.8).
- A constructor should create a *fully initialized, valid* object or throw (C.41, C.42). Avoid two-phase `init()` functions, which allow invalid objects to exist.
- Do not return non-`const` references or pointers to private members; they bypass the gate. Return values or `const&`.
- Prefer non-member functions for operations that do not need private access, so the class stays small (C.4).
- Mark single-argument constructors `explicit` (C.46) to prevent silent conversions like `JointState j = 0.5;`.
- Each member function is `const` unless it changes the state.

**Example.** `Pose2D` has no invariant (any three numbers are a pose), so it stays a `struct`; `JointAngle` has the invariant $|a|\le\pi$, so it is a class with an `explicit` constructor (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

```cpp
#include <cstdio>
struct Pose2D { double x, y, theta; };                 // no invariant: a struct
class JointAngle {                                     // invariant: |a| <= pi, so a class
  double a_;
 public:
  explicit JointAngle(double a) : a_(a) {}
  double value() const { return a_; }
};
void report(JointAngle a) { std::printf("angle = %.2f rad\n", a.value()); }
int main() {
  Pose2D p{1.0, 2.0, 0.5};
  std::printf("pose = (%.1f, %.1f, %.1f)\n", p.x, p.y, p.theta);
  report(JointAngle{0.75});
}
```

```text
pose = (1.0, 2.0, 0.5)
angle = 0.75 rad
```

Writing `report(0.75)` instead of `report(JointAngle{0.75})` is rejected at build time: `could not convert ‘7.5e-1’ from ‘double’ to ‘JointAngle’`. Without `explicit` the bare number would convert silently, and a value in degrees or a plain `double` meant for another parameter would flow into the class unchecked (C.46).

### Access control and `const`: what the compiler enforces

Access control is a compile-time check on *names*. A private member can be named only by members and friends of its class ([class.access.general] ¶1); the check is per class, not per object, so a member function may read the private data of another object of the same class (as every copy constructor and `operator==` does), and nothing at run time prevents a debugger or a bad pointer from overwriting the bytes. What `private` buys is therefore a *finite list of places* to audit when the invariant breaks: the member functions and friends. Every public function that returns a non-`const` reference or pointer to private data, and every `friend`, extends that list, which is why the guidelines avoid them (C.9, C.133).

A `const` member function promises not to change the observable state of the object, and the compiler enforces it for data members that are not `mutable`: inside the function `this` has type `const T*`, so assignments to members are errors (cppreference: cv type qualifiers, `mutable` specifier). The distinction that matters is between *bitwise* and *logical* constness. A cache, a mutex or a read counter does not change the value that callers see, so it may be declared `mutable` and written from a `const` function; a member that is part of the abstract value must not be. Overloads on `const` let one name serve both read-only and writable callers (`T& at(i)` and `const T& at(i) const`), and `const` references are the cheapest way to hand out read access (F.16, Con.2).

**Example.** An odometer counts how often its total is read, through a `mutable` counter, and is viewed through a `const` reference (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

```cpp
#include <cstdio>
class Odometer {
  double total_ = 12.5;
  mutable int reads_ = 0;                // bookkeeping, not part of the observable value
 public:
  double total() const { ++reads_; return total_; }
  void add(double d) { total_ += d; }
  int reads() const { return reads_; }
};
int main() {
  Odometer o;
  const Odometer& view = o;
  double a = view.total() + view.total();
  std::printf("sum of two reads = %.1f, reads counted = %d\n", a, view.reads());
}
```

```text
sum of two reads = 25.0, reads counted = 2
```

Both calls compile because `total()` is `const` and the counter is `mutable`; the sum is 25.0 and 2 reads are counted. Calling the mutating `add()` through the same reference is rejected: `passing ‘const Odometer’ as ‘this’ argument discards qualifiers [-fpermissive]`.

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

**Example.** A PID controller with three gains is deleted through a base pointer. First a base without a virtual destructor, built with g++ 11.4.0 and `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`:

```cpp
#include <cstdio>
struct Controller { virtual double compute(double e) const = 0; ~Controller() {} };       // no virtual destructor
struct PID : Controller { double gains[3] = {1, 0.1, 0.01}; double compute(double e) const override { return gains[0] * e; } };
int main() { Controller* c = new PID; std::printf("%g\n", c->compute(2.0)); delete c; }
```

```text
warning: deleting object of abstract class type ‘Controller’ which has non-virtual destructor will cause undefined behavior [-Wdelete-non-virtual-dtor]
==PID==ERROR: AddressSanitizer: new-delete-type-mismatch on 0x... in thread T0:
object passed to delete has wrong type:
size of the allocated type:   32 bytes;
size of the deallocated type: 8 bytes.
SUMMARY: AddressSanitizer: new-delete-type-mismatch ../../../../src/libsanitizer/asan/asan_new_delete.cpp:172 in operator delete(void*, unsigned long)
```

The compiler warns at build time and AddressSanitizer reports at run time that an object of 32 bytes was released as one of 8 bytes: `~PID` and the derived part were never handled. With `virtual ~Controller()` (C.35) the same deletion through a `std::unique_ptr<Controller>` runs both destructors, as the second program shows (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

```cpp
#include <cstdio>
#include <memory>
struct Controller { virtual ~Controller() { std::puts("~Controller"); } virtual double compute(double e) const = 0; };
struct PID : Controller { double gains[3] = {1, 0.1, 0.01}; ~PID() override { std::puts("~PID"); } double compute(double e) const override { return gains[0] * e; } };
int main() { std::unique_ptr<Controller> c = std::make_unique<PID>(); std::printf("%g\n", c->compute(2.0)); }
```

```text
2
~PID
~Controller
```

### Substitutability

If code works with a `Base&`, it must also work with any `Derived`. A `FixedJoint : Joint` whose `set_position` throws breaks this (the Liskov substitution principle): callers cannot tell from the type whether the call is legal. Derive only when the derived class *is a* substitutable kind of the base, otherwise use composition (a member) or separate interfaces (`Positionable` is implemented only by movable joints).

**Example.** A planner sends `set_position` to every joint of a mixed arm; the second joint is a `FixedJoint` derived from `Joint` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

```cpp
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <vector>
struct Joint { virtual ~Joint() = default; virtual void set_position(double q) { std::printf("moved to %.2f\n", q); } };
struct FixedJoint : Joint { void set_position(double) override { throw std::logic_error("fixed joint cannot move"); } };
int main() {
  std::vector<std::unique_ptr<Joint>> arm;
  arm.push_back(std::make_unique<Joint>()); arm.push_back(std::make_unique<FixedJoint>()); arm.push_back(std::make_unique<Joint>());
  int i = 0;
  for (auto& j : arm) {
    try { j->set_position(0.25 * ++i); } catch (const std::logic_error& e) { std::printf("joint %d: %s\n", i - 1, e.what()); }
  }
}
```

```text
moved to 0.25
joint 1: fixed joint cannot move
moved to 0.75
```

The code compiles without a warning and the planner, written against `Joint&`, cannot tell from the types that joint 1 will refuse: it must catch `std::logic_error` or test the dynamic type, and every new caller has to remember to do the same. A type whose operation is sometimes illegal does not satisfy the contract of its base (Core Guidelines C.120, and the Liskov substitution principle), so `FixedJoint` should not derive from a `Joint` that promises movement.

### Virtual calls during construction and destruction

While a base-class constructor runs, the object's dynamic type *is* the base. The rule is that a virtual call made directly or indirectly from a constructor or destructor selects the final overrider of the class whose constructor or destructor is currently running, never an override in a more-derived class (cppreference: virtual function specifier, "During construction and destruction"; C++ Core Guidelines, C.82). The reason is a safety argument, not an accident: when `Sensor()` runs, the members of `Lidar` have not been constructed yet, so dispatching to `Lidar::name()` would read an object that does not exist. Destruction mirrors this: by the time `~Sensor()` runs, `~Lidar()` has finished and the `Lidar` members are gone.

```cpp
struct Sensor {
  Sensor() { std::cout << "Sensor() sees " << name() << "\n"; }
  virtual ~Sensor() { std::cout << "~Sensor() sees " << name() << "\n"; }
  virtual std::string name() const { return "generic"; }
};
struct Lidar : Sensor {
  std::string label = "lidar";
  Lidar() { std::cout << "Lidar() sees " << name() << "\n"; }
  ~Lidar() override { std::cout << "~Lidar() sees " << name() << "\n"; }
  std::string name() const override { return label; }
};
```

Constructing and destroying a `Lidar` prints `Sensor() sees generic`, `Lidar() sees lidar`, `~Lidar() sees lidar`, `~Sensor() sees generic`. If `name()` were pure virtual in `Sensor` and not implemented, the call from `Sensor()` has undefined behavior (C.82). What to do instead: pass the needed data to the base constructor as an argument (`Sensor(std::string n)`), use a named factory that constructs the object completely and then calls `init()` (the object is valid from the moment the factory returns it, so the invariant is not weakened), or use a non-virtual helper in the base. This is the dynamic-dispatch version of the invariant proof pattern: a virtual call inside a constructor happens *before* the establish step is finished, so the preserve step may not be assumed.

**Example.** A sensor driver computes its sampling period in the base constructor from a virtual `rate()`; the derived driver overrides `rate()` to 100 Hz. The second design passes the rate down (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

```cpp
#include <cstdio>
struct Driver {
  double period;
  Driver() : period(1.0 / rate()) {}           // virtual call inside the constructor
  virtual double rate() const { return 10.0; } // Hz, base default
  virtual ~Driver() = default;
};
struct FastDriver : Driver { double rate() const override { return 100.0; } };
struct Fixed {
  double period;
  explicit Fixed(double hz) : period(1.0 / hz) {}   // data passed down instead
  virtual ~Fixed() = default;
};
struct FastFixed : Fixed { FastFixed() : Fixed(100.0) {} };
int main() {
  FastDriver a; FastFixed b;
  std::printf("virtual call in constructor: period = %.2f s\n", a.period);
  std::printf("rate passed to base       : period = %.2f s\n", b.period);
}
```

```text
virtual call in constructor: period = 0.10 s
rate passed to base       : period = 0.01 s
```

In `Driver()` the dynamic type is `Driver`, so `rate()` resolves to the base value 10 Hz ([class.cdtor]) and the period is 0.10 s although the object is meant to run at 100 Hz: the fault is silent and the invariant "period = 1 / rate" is false from the first instant. Passing the rate as a constructor argument makes the period 0.01 s and needs no virtual call before the object is complete (C.82).

![Four columns for constructing and destroying a Lidar: Sensor() sees generic, Lidar() sees lidar, ~Lidar() sees lidar, ~Sensor() sees generic; the member label is alive only in the middle](/lesson-figures/CPP04-2.svg)

*Figure: the same virtual call `name()` selects a different function in each of the four phases; in the outer two the member `Lidar::label` does not exist, which is why the language does not dispatch to the derived override.*

### Substitutability as a contract: weaker preconditions, stronger postconditions

The Liskov paragraph above can be made precise with the vocabulary of specifications. A specification $S_2$ is *stronger* than $S_1$ if its precondition is weaker or equal (it accepts at least all inputs $S_1$ accepts) and, on every input $S_1$ accepts, its postcondition is stronger or equal; a stronger specification can replace a weaker one in any client (MIT 6.031, Reading 7, "Stronger vs. weaker specs"). Apply it to an overriding function `Derived::f` of `Base::f`:

$$\text{pre}_{\text{Base}}(x) \Rightarrow \text{pre}_{\text{Derived}}(x), \qquad \text{pre}_{\text{Base}}(x)\wedge \text{post}_{\text{Derived}}(x,y) \Rightarrow \text{post}_{\text{Base}}(x,y).$$

*Why this is the right condition.* A client written against `Base&` only knows $\text{pre}_{\text{Base}}$ and relies on $\text{post}_{\text{Base}}$. If $\text{pre}_{\text{Derived}}$ were stricter, there would be an input $x$ the client may legally pass, with $\text{pre}_{\text{Base}}(x)$ true and $\text{pre}_{\text{Derived}}(x)$ false: the override rejects or misbehaves on a legal call. If $\text{post}_{\text{Derived}}$ were weaker, the client would see a result its proof cannot handle. Class invariants add one more clause: since the invariant must hold after every public call, $I_{\text{Derived}}\Rightarrow I_{\text{Base}}$ (a derived object may have *more* constraints, never fewer). For `JointState`, the base promises $|v|\le v_{\max}$; a derived class that accepts faster moves (a weaker precondition) must still clamp so that the stored speed obeys the base bound, or it breaks the base invariant clients rely on (MIT 6.031, Reading 11, "Rep invariant").

*Mechanising it: the non-virtual interface.* To make the contract hold for every override automatically, put the gate in a public non-virtual function of the base that checks the base precondition, calls a private virtual `do_set(q, dt)`, and checks the base invariant on the way out; derived classes customise only the private step. Then even a careless override cannot publish a state that violates $I_{\text{Base}}$. This also explains why the guidelines discourage `protected` data (C.133): a derived class that can write base members bypasses the gate, so the base can no longer prove its invariant by looking at its own member functions alone.

**Example.** Base joints accept a move when $|\Delta q|/dt\le2$ rad/s; `SlowJoint` overrides the test with 1.25 rad/s. Four calls from $q=0$ are replayed against both (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

```cpp
#include <cmath>
#include <cstdio>
struct Joint {
  virtual ~Joint() = default;
  virtual bool accepts(double dq, double dt) const { return std::fabs(dq) / dt <= 2.0; }   // base: vmax = 2 rad/s
};
struct SlowJoint : Joint {
  bool accepts(double dq, double dt) const override { return std::fabs(dq) / dt <= 1.25; } // stricter precondition
};
int main() {
  const double calls[][2] = {{0.3, 0.2}, {0.5, 0.5}, {0.6, 0.4}, {0.8, 0.5}};
  Joint base; SlowJoint slow;
  std::printf("dq    dt    speed  base  slow\n");
  for (auto& c : calls)
    std::printf("%.1f   %.1f   %.2f   %-5d %d\n", c[0], c[1], c[0] / c[1], base.accepts(c[0], c[1]), slow.accepts(c[0], c[1]));
}
```

```text
dq    dt    speed  base  slow
0.3   0.2   1.50   1     0
0.5   0.5   1.00   1     1
0.6   0.4   1.50   1     0
0.8   0.5   1.60   1     0
```

All four calls satisfy the base precondition, but `SlowJoint` rejects three of them (1.50, 1.50 and 1.60 rad/s are above 1.25): its precondition is stricter, so $\text{pre}_{\text{Base}}\Rightarrow\text{pre}_{\text{Derived}}$ fails, and a client that legally passed those arguments now gets a refusal. The figure draws the same situation as regions in the plane of target and time step.

![Accepted regions above the lines dt = |q'|/vmax for vmax 2.75, 2 and 1.25 with limits plus or minus 1.5, and two marked calls A and B](/lesson-figures/CPP04-3.svg)

*Figure: each override's accepted calls lie above its line; the slow override accepts a subset (point A is lost), the fast one a superset (point B is accepted but its stored speed 2.4 rad/s breaks the base invariant).*

### Copying polymorphic objects: slicing, `clone`, and covariant returns

Copying through a base reference copies only the base subobject (slicing), which is why polymorphic bases suppress public copy and move operations (C.67). When a deep copy of the most-derived type is genuinely needed, the guidelines prescribe a virtual `clone` that returns an owning pointer and, in derived classes, a covariant return type (C.130; cppreference: virtual function specifier, "Covariant return types"):

```cpp
struct Shape  { virtual ~Shape() = default; virtual Shape* clone() const { return new Shape(*this); } };
struct Circle : Shape { Circle* clone() const override { return new Circle(*this); } };
struct Ring   : Circle { double r2 = 2; };   // forgot to override clone()
```

The failure mode is silent: `Ring` inherits `Circle::clone`, so `Shape* p = new Ring; p->clone()` produces a `Circle`, a slice with no compiler diagnostic. Covariant return types cannot be smart pointers, so the safe form is again an NVI: a public non-virtual `std::unique_ptr<Shape> clone() const` that wraps a private pure virtual `do_clone()` and compares `typeid(*result)` with `typeid(*this)`; a forgotten override is then caught at the first clone in a debug build instead of producing a wrong object later. Making `do_clone` pure also forces every concrete class to supply it, though it cannot force an intermediate class's subclasses to do so, which is why the runtime check remains useful.

**Example.** A filter chain clones its nodes through a public non-virtual `clone()` that wraps a private pure virtual `do_clone()` and compares dynamic types. `Gain` overrides it; `AutoGain` derives from `Gain` and forgets (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

```cpp
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <typeinfo>
class Node {
 public:
  virtual ~Node() = default;
  std::unique_ptr<Node> clone() const {
    auto p = do_clone();
    if (typeid(*p) != typeid(*this)) throw std::logic_error("do_clone() not overridden");
    return p;
  }
 private:
  virtual std::unique_ptr<Node> do_clone() const = 0;
};
struct Gain : Node {
  double k = 2.5;
 private:
  std::unique_ptr<Node> do_clone() const override { return std::make_unique<Gain>(*this); }
};
struct AutoGain : Gain { double target = 1.0; };      // forgot to override do_clone
int main() {
  Gain g; AutoGain a;
  try { g.clone();  std::puts("Gain: clone ok"); } catch (const std::logic_error& e) { std::printf("Gain: %s\n", e.what()); }
  try { a.clone();  std::puts("AutoGain: clone ok"); } catch (const std::logic_error& e) { std::printf("AutoGain: %s\n", e.what()); }
}
```

```text
Gain: clone ok
AutoGain: do_clone() not overridden
```

`Gain` clones correctly. For `AutoGain`, the inherited `Gain::do_clone` would build a `Gain` (a slice: the field `target` is lost), but the `typeid` comparison in `clone()` turns that silent loss into an exception at the first clone, in the test run rather than in the field (C.130, C.67). The check costs one RTTI comparison per clone.

## Worked example


### Case 1: accepting and rejecting joint updates

**Problem.** `JointState(lo=-1.5, hi=1.5, vmax=2.0)` starts at $q=0$, $v=0$. Apply, in order, `try_set_position(0.15, 0.1)`, `try_set_position(0.9, 0.1)`, the same target with the smallest legal `dt`, and `try_set_position(1.6, 10.0)`. Give the result and the state after each call. Then close the loop with `PController(kp=2)`, `dt=0.1`, target $1.0$ and no limits, and give $q_{10}$.

**Solution.** The acceptance test is the one of the theory: $l\le q'\le h$ and $|q'-q|/dt\le v_{\max}$, and a rejection changes nothing (preserve step).

1. *Call `(0.15, 0.1)`.* Range: $-1.5\le0.15\le1.5$ holds. Speed: $|0.15-0|/0.1=1.5$ rad/s $\le2$. Accept: $q=0.15$, $v=1.5$.
2. *Call `(0.9, 0.1)`.* Range holds. Speed: $|0.9-0.15|/0.1=0.75/0.1=7.5$ rad/s $>2$. Reject; the state stays $q=0.15$, $v=1.5$.
3. *Smallest `dt` for the target $0.9$.* Require $0.75/dt\le2$, so $dt\ge0.75/2=0.375$ s. With `dt = 0.375` the speed is exactly $0.75/0.375=2.0\le2$: accept, $q=0.9$, $v=2.0$. (Equality at the boundary is fragile in floating point; production code leaves a margin or compares with a tolerance.)
4. *Call `(1.6, 10.0)`.* Range: $1.6>1.5$, so the call is rejected whatever `dt` is; the speed $|1.6-0.9|/10=0.07$ is irrelevant.
5. *Closed loop.* With $v_{\max}$ and the limits not active, one step is $q_{k+1}=q_k+k_p(1-q_k)\,dt=q_k+0.2(1-q_k)$, so the error $1-q_k$ is multiplied by $0.8$ each step and $q_k=1-0.8^k$. For $k=10$: $0.8^{10}=0.107374$, so $q_{10}=0.892626$.

![Plot of the accepted region of target position and dt from q = 0.15 with vmax 2 and limits plus or minus 1.5, with the rejected step 2, the boundary point of step 3 and the out-of-range step 4](/lesson-figures/CPP04-4.svg)

*Figure: the numbers of steps 2 to 4 drawn in the plane of target and `dt`; step 2 lies below the boundary line, step 3 on it, step 4 beyond the dashed limit.*

**Check.** The reference `JointState` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`) gives

```text
try_set_position(0.15, 0.1) -> accept, q=0.15, v=1.5
try_set_position(0.9, 0.1) -> reject, q=0.15, v=1.5
try_set_position(0.9, 0.375) -> accept, q=0.9, v=2
try_set_position(1.6, 10.0) -> reject, q=0.9, v=2
q10 = 0.892626
```

which matches steps 1 to 5; the closed-form value $1-0.8^{10}=0.8926258\ldots$ agrees with the loop.

**Takeaway.** The class accepts a call only when both conditions hold, and the same two inequalities give the smallest legal `dt` directly.

### Case 2: layout, dispatch and slicing of a `PID` object

**Problem.** Controllers carry an `id` and a vptr; `PID` adds two gains. Predict `sizeof(Controller)`, `sizeof(PID)`, the offset of each member of `PID` on x86-64 with the Itanium ABI, the value of `r.compute(2.0)` for a `Controller& r` bound to a `PID`, and of `c.compute(2.0)` for the sliced copy `Controller c = p`.

```cpp
#include <cstddef>
#include <cstdio>
#include <typeinfo>
struct Controller {
  virtual ~Controller() = default;
  virtual double compute(double) const { return 0.0; }
  int id = 7;
};
struct PID : Controller {
  double kp = 3.0, ki = 0.5;
  double compute(double e) const override { return kp * e + ki * e; }
};
int main() {
  PID p;
  Controller& r = p;
  Controller c = p;                                    // slicing: copies the Controller part only
  std::printf("sizeof(Controller) = %zu, sizeof(PID) = %zu\n", sizeof(Controller), sizeof(PID));
  std::printf("offsets in PID: id = %zu, kp = %zu, ki = %zu\n",
              (size_t)((char*)&p.id - (char*)&p), (size_t)((char*)&p.kp - (char*)&p), (size_t)((char*)&p.ki - (char*)&p));
  std::printf("r.compute(2.0) = %.1f, c.compute(2.0) = %.1f\n", r.compute(2.0), c.compute(2.0));
  void** vt_p = *reinterpret_cast<void***>(&p);        // the vptr (Itanium ABI)
  void** vt_c = *reinterpret_cast<void***>(&c);
  std::printf("vptr slot -1 is typeid: PID %d, sliced copy %d\n", vt_p[-1] == &typeid(PID), vt_c[-1] == &typeid(Controller));
  std::printf("vptr of p and c differ: %d\n", vt_p != vt_c);
}
```

**Solution.** Alignment rule: a member of size $s$ is placed at the next multiple of its alignment, and the object size is rounded up to the largest alignment (here 8).

1. *`Controller`.* A class with virtual functions starts with a vptr (8 bytes, Itanium ABI §2.5). `int id` (4 bytes, alignment 4) goes at offset 8, ending at 12; the size is rounded up to a multiple of 8: $\text{sizeof}(\text{Controller})=16$, with 4 bytes of padding.
2. *`PID`.* The base subobject comes first (offsets 0 to 15). `double kp` needs alignment 8, so it is at offset 16, `double ki` at 24: $\text{sizeof}(\text{PID})=16+8+8=32$.
3. *Dispatch through the reference.* `r` refers to the same 32-byte object, whose vptr points to the vtable of `PID` (slot $-1$ holds the `typeinfo`, slots 0 and 1 the two destructors, slot 2 `compute`). The call picks `PID::compute`: $3.0\cdot2.0+0.5\cdot2.0=6.0+1.0=7.0$.
4. *Slicing.* `Controller c = p` copy-constructs only the 16-byte `Controller` subobject: `kp` and `ki` are not copied, and the new object's vptr is the one of `Controller`, so `c.compute(2.0)` runs `Controller::compute` and returns $0.0$.

![Memory layout of PID p: vptr at 0, id at 8, padding 12 to 16, kp at 16, ki at 24; the vtable of PID with typeinfo, two destructors and compute; the sliced copy of 16 bytes whose vptr points to Controller](/lesson-figures/CPP04-5.svg)

*Figure: the 32-byte object with its Controller part (16 B) and the part added by `PID` (16 B), the vtable slots, and what the sliced copy keeps.*

**Check.** Compiled with g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`, the program prints

```text
sizeof(Controller) = 16, sizeof(PID) = 32
offsets in PID: id = 8, kp = 16, ki = 24
r.compute(2.0) = 7.0, c.compute(2.0) = 0.0
vptr slot -1 is typeid: PID 1, sliced copy 1
vptr of p and c differ: 1
```

(slot $-1$ equals `&typeid(PID)` for `p` and `&typeid(Controller)` for the copy, and calling slot 2 of each vtable through a function pointer gave $7.0$ and $0.0$ in a variant of the program). The sizes and offsets are properties of this ABI, not of the standard.

**Takeaway.** The vptr travels with the object and selects the override, so dispatch needs a reference or pointer; copying by value keeps only the base part and its vptr.

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

12. **(Challenge)** Dispatch during construction. For the `Sensor`/`Lidar` classes in the theory section, (a) write the exact output of `{ Lidar l; }`. (b) Explain why dispatching to `Lidar::name()` from inside `Sensor()` would be unsafe, naming which member is not yet alive. (c) If `Sensor::name()` were pure virtual with no definition, what does the standard say about the call in `Sensor()`, and what does g++ typically do at run time? (d) Give two redesigns that give each sensor its name without a virtual call in a constructor, and say which keeps the invariant "a `Sensor` always has a non-empty name" easiest to prove. (adapted from C++ Core Guidelines, C.82, and cppreference "Virtual function specifier", During construction and destruction)
13. **(Challenge)** Substitutability, counted. `JointState(lo=-1.5, hi=1.5, vmax=2)` starts at $q=0$. Consider the grid of calls `try_set_position(q', dt)` with $q'=0.1k$ for $k=-15,\dots,15$ and $dt=0.05j$ for $j=1,\dots,20$ (620 calls). (a) How many does the base accept? (b) A subclass `SlowJoint` with $v_{\max}=1$ overrides the check: how many does it accept, and how many calls does the base accept but `SlowJoint` rejects? Which of the two conditions of substitutability fails, and for which calls? (c) A subclass `FastJoint` with $v_{\max}=3$ accepts how many? Is it substitutable as written, and what extra behavior makes it so? (d) Show the arithmetic is exact by rewriting the speed test with integers. (adapted from MIT 6.031 Reading 7, "Stronger vs. weaker specs", and Reading 11, rep invariants)
14. **(Challenge)** The silent slice. With `Shape`, `Circle`, `Ring` as in the theory section, (a) what is `p->clone()`'s dynamic type for `Shape* p = new Ring`? (b) Predict `sizeof(Shape)`, `sizeof(Circle)`, `sizeof(Ring)` on GCC for x86-64 (a vptr is 8 bytes; `Circle` adds a `double r = 1` and `Ring` adds `double r2`). (c) Rewrite the hierarchy with a public non-virtual `std::unique_ptr<Shape> clone() const` and a private pure virtual `do_clone()`, add a `typeid` check, and say what happens when a `Ring` is cloned without its own `do_clone`. (d) Why can the runtime check not be replaced by a compile-time error in the language, and what does `final` on `Circle::do_clone` change? (adapted from C++ Core Guidelines, C.67 and C.130)
15. **(Challenge)** All-or-nothing invariants. `JointArray` holds six `JointState`s (limits $[-1.5,1.5]$, $v_{\max}=2$, all at $q=0$) and `try_set_all(t, dt)` with a logging hook `hook(i)` that may throw. Use $t=(0.1,0.1,0.1,2.0,0.1,0.1)$, $dt=0.1$. (a) For a naive loop (check joint $i$, commit it, call `hook(i)`), give the final positions and the return value. (b) Same for a two-phase version (validate all, run all hooks, then commit all). (c) Now $t=(0.1,\dots,0.1)$ and `hook(2)` throws: give the positions after the exception for both versions. (d) State the group invariant, and why the commit phase must be `noexcept` for the two-phase version to be correct. (source: MIT 6.031 Reading 11, rep invariants and "how to establish invariants"; C++ Core Guidelines, C.41)

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

### Library track

Use only the standard library: `<random>` for the fuzz test of the extension project, and `<functional>`/`<variant>` for the two alternatives to virtual dispatch from exercise 8. Paste the code below *after* your finished `JointState`, `Controller`, `PController` and `step` (it has its own `main`, so drop the one from the tests). Compile with `g++ -std=c++17 -Wall -Wextra -fsanitize=address,undefined`.

```cpp
#include <cassert>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <random>
#include <variant>
#include <vector>

// step() again, but taking ANY callable error -> command (lambda, std::function, functor).
template <class F>
void step_with(JointState& j, F&& compute, double target, double dt) {
  const double cmd = std::clamp(compute(target - j.position()), -j.vmax(), j.vmax());
  j.set_position(std::clamp(j.position() + cmd * dt, j.lo(), j.hi()), dt);
}

struct PGain  { double kp; double operator()(double e) const { return kp * e; } };
struct PDGain { double kp, kd, prev = 0; double operator()(double e) { double d = e - prev; prev = e; return kp * e + kd * d; } };

int main() {
  // 1. fuzz with <random>: the invariant must hold after every call, accepted or not
  std::mt19937 rng(42);
  std::normal_distribution<double> nd(0.0, 3.0);
  const double inf = std::numeric_limits<double>::infinity();
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const std::vector<double> special = {0.0, -0.0, nan, inf, -inf, 1e308, 5e-324, 1.5, -1.5};
  JointState j(-1.5, 1.5, 2.0);
  int accepted = 0;
  for (int i = 0; i < 100000; ++i) {
    double q  = (i % 4 == 0) ? special[rng() % special.size()] : nd(rng);
    double dt = (i % 5 == 0) ? special[rng() % special.size()] : std::fabs(nd(rng)) * 0.1;
    const double q0 = j.position(), v0 = j.velocity();
    const bool ok = j.try_set_position(q, dt);
    accepted += ok;
    if (!ok) assert(j.position() == q0 && j.velocity() == v0);      // a rejection is a no-op
    assert(std::isfinite(j.position()) && j.position() >= -1.5 && j.position() <= 1.5);
    assert(std::fabs(j.velocity()) <= 2.0);
  }
  std::cout << "accepted " << accepted << " of 100000\n";

  // 2. three ways to swap the controller must agree with the virtual PController
  const double expect = 1.0 - std::pow(0.8, 10);
  PController virt(2.0);
  std::function<double(double)> fn = PGain{2.0};
  std::variant<PGain, PDGain> var = PGain{2.0};            // run-time switch without virtual
  JointState a(-10, 10, 100), b(-10, 10, 100), c(-10, 10, 100), d(-10, 10, 100);
  for (int i = 0; i < 10; ++i) {
    step(a, virt, 1.0, 0.1);                                           // virtual
    step_with(b, fn, 1.0, 0.1);                                        // std::function
    step_with(c, [&](double e) { return std::visit([e](auto& g) { return g(e); }, var); }, 1.0, 0.1);
    step_with(d, PGain{2.0}, 1.0, 0.1);                                // template, inlinable
  }
  for (const JointState* s : {&a, &b, &c, &d}) assert(std::fabs(s->position() - expect) < 1e-12);
  std::cout << "four controllers agree: " << a.position() << "\n";
}
```

Expected output: `accepted ...` (about 11 800 of 100 000 with this seed; the exact count depends on your standard library's `normal_distribution`) and `four controllers agree: 0.892626`. Every assert must hold, which is the induction proof of exercise 7 checked on 100 000 hostile calls. Then measure: how much slower is the `std::function` loop than the template version for $10^8$ calls (use `-O2` and `std::chrono`)?

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

12. (a) `Sensor() sees generic`, `Lidar() sees lidar`, `~Lidar() sees lidar`, `~Sensor() sees generic` (measured with g++ 11.4). (b) When `Sensor()` runs, the `Lidar` part has not been constructed: `label` (a `std::string` member of `Lidar`) is not yet alive, so `Lidar::name()` would return a reference to an unconstructed string. The language therefore resolves the call to `Sensor::name()`. In `~Sensor()` the `Lidar` members are already destroyed, for the same reason in reverse. (c) A call to an unimplemented pure virtual function from a constructor or destructor, direct or indirect, is undefined behavior (C.82); g++ typically links the vtable slot to `__cxa_pure_virtual` and the program aborts with "pure virtual method called" (when the call is direct in the constructor the compiler may also reject or warn at build time). (d) Redesign 1: pass the name down, `Sensor(std::string n) : name_(std::move(n))` with a non-virtual `name() const`; the derived constructor writes `Sensor("lidar")`. Redesign 2: a static factory `create_lidar()` that constructs completely and then calls a virtual `init()`. Redesign 1 keeps the invariant easiest to prove: the base constructor can check `!n.empty()` and throw, establishing the invariant once, before any derived code runs, and `name()` is a plain getter that cannot break it.
13. Use integers: $|q'|/dt = 0.1|k|/(0.05j) = 2|k|/j$, so the test $|q'|/dt\le v_{\max}$ is $2|k|\le v_{\max}\,j$ (all $q'$ lie in $[-1.5,1.5]$, so the range check always passes). (a) $v_{\max}=2$: **410** of 620 accepted (computed by enumeration). (b) $v_{\max}=1$: **220** accepted. Every call accepted by `SlowJoint` is accepted by the base (220 in both, 0 only in the derived), so 410 - 220 = **190** calls are accepted by the base and rejected by `SlowJoint`: the precondition of the override is *stricter* than the base's, the first substitutability condition fails ($\text{pre}_{\text{Base}}\Rightarrow\text{pre}_{\text{Derived}}$ is false). A client that legally asked for $k=15$, $j=15$ ($1.5$ rad in $0.75$ s, speed 2) is rejected. Its postcondition ($|v|\le1\le2$) is fine. (c) $v_{\max}=3$: **480** accepted, a superset of the 410 (weaker precondition: allowed). But as written it stores speeds up to 3, violating the base invariant $|v|\le2$ that clients may rely on, so the postcondition/invariant condition fails. It becomes substitutable if it also keeps the stored speed bounded, for instance by clamping the commanded speed or the step so that $|v'|\le2$, or by declaring a weaker base invariant, which then changes what clients may assume. (d) Done above: no floating-point boundary issue appears in the counts because the comparison uses exact integers.
14. (a) `Circle`: `Ring` inherits `Circle::clone`, which copy-constructs a `Circle`; measured: original `Ring`, clone `Circle`, with no diagnostic. (b) Measured on g++ 11.4 x86-64: `sizeof(Shape)=8` (the vptr), `sizeof(Circle)=16`, `sizeof(Ring)=24`. These are ABI-dependent numbers, not guaranteed by the standard. (c) Public non-virtual `clone()`: `std::unique_ptr<Shape> p(do_clone()); if (typeid(*p) != typeid(*this)) abort();`. Cloning a `Ring` that did not override `do_clone` runs `Circle::do_clone`, returns a `Circle`, the check sees `Circle != Ring` and aborts with a message (measured: "clone() override missing in 4Ring"). The check also gives an owning `unique_ptr` from the start, which a covariant raw-pointer `clone` cannot. (d) The language has no way to say "every class derived from this one, at any depth, must override"; pure virtual only forces the first concrete class. A debug-time `typeid` check is therefore the cheapest net. Putting `final` on `Circle::do_clone` forbids further overrides, so `Ring` could not override it either: it turns a forgotten override into a design where `Ring` must not exist as a subclass of `Circle`, forcing a better design (for example `Ring` derived from `Shape` directly).
15. (a) Naive loop: joints 0, 1, 2 pass validation and commit (positions $0.1$), joint 3 fails ($2.0>1.5$) and the function returns `false`: final positions $(0.1,0.1,0.1,0,0,0)$, a state nobody requested (measured). (b) Two-phase: validation fails before anything is changed: return `false`, positions $(0,0,0,0,0,0)$. (c) Naive: `hook(2)` throws after joint 2 has committed, so positions $(0.1,0.1,0.1,0,0,0)$ after the exception. Two-phase: the hooks run before any commit and the throw leaves all six at $0$ (strong guarantee). (d) Group invariant: every joint satisfies its own invariant *and* the vector of positions equals the last vector that passed validation as a whole (so the group never exposes a mix of old and new). The commit phase must be `noexcept`: if a commit could throw after joint 2, the earlier commits could not be undone (an undo would also be a commit), and the group would again be in a mixed state. Therefore everything that can fail (validation, logging, allocation) is done in phase 1, and phase 2 only assigns doubles.

## Further reading

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - section C on classes, invariants (C.2, C.40-C.42), and hierarchies (C.120-C.153).
- [cppreference: Classes](https://en.cppreference.com/w/cpp/language/classes) - precise rules for access control, constructors, virtual functions and abstract classes.
- [LearnCpp](https://www.learncpp.com/) - classes, constructors, inheritance and virtual functions with graded quizzes.
- [C++ standard draft, [class.cdtor]](https://eel.is/c++draft/class.cdtor) and [[class.access.general]](https://eel.is/c++draft/class.access.general) - virtual calls during construction and destruction, and the definition of private access; [Itanium C++ ABI, §2.5](https://itanium-cxx-abi.github.io/cxx-abi/abi.html) - the vtable layout used in the second worked case.
- [cppreference: Virtual function specifier](https://en.cppreference.com/w/cpp/language/virtual) - behavior during construction and destruction, covariant return types, pure virtual functions.
- [MIT 6.031 Reading 7: Designing Specifications](https://web.mit.edu/6.031/www/sp22/classes/07-designing-specs/) and [Reading 11: Abstraction Functions and Rep Invariants](https://web.mit.edu/6.031/www/sp22/classes/11-abstraction-functions-rep-invariants/) - stronger vs. weaker specifications and how to establish and preserve a representation invariant.

**More practice:** the quizzes on [LearnCpp: introduction to classes](https://www.learncpp.com/cpp-tutorial/introduction-to-classes/), [pure virtual functions and interface classes](https://www.learncpp.com/cpp-tutorial/pure-virtual-functions-abstract-base-classes-and-interface-classes/), [virtual destructors and override](https://www.learncpp.com/cpp-tutorial/virtual-destructors-virtual-assignment-and-overriding-virtualization/) and [object slicing](https://www.learncpp.com/cpp-tutorial/object-slicing/) (answers shown on each page), and the Core Guidelines [classes and class hierarchies](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#c-classes-and-class-hierarchies) section as a review checklist for your own `JointState`.