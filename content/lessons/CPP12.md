---
{
  "id": "cpp12-foundations",
  "module_id": "CPP12",
  "title": "Advanced C++: generic libraries, ABI, and systems design",
  "summary": "Design and audit library interfaces for ownership, error handling and binary compatibility, with a stable C boundary and a safe C++ wrapper.",
  "estimated_minutes": 420,
  "prerequisites": [
    "CPP06",
    "CPP09"
  ],
  "source_refs": [
    {
      "title": "C++ Core Guidelines: I. Interfaces",
      "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"
    },
    {
      "title": "KDE: Binary Compatibility Issues With C++",
      "url": "https://community.kde.org/Policies/Binary_Compatibility_Issues_With_C%2B%2B"
    },
    {
      "title": "Itanium C++ ABI",
      "url": "https://itanium-cxx-abi.github.io/cxx-abi/abi.html"
    }
  ],
  "objectives": [
    "Distinguish API from ABI and classify changes as source-compatible, binary-compatible or breaking.",
    "Design a stable C boundary (opaque handles, error codes, no exceptions across it) and wrap it in RAII C++.",
    "Audit a library interface for who owns what, for how long, and on which thread.",
    "Choose between header-only generic code, compiled libraries, and pimpl for a given deployment."
  ],
  "core_theory": [
    "generic libraries",
    "ABI",
    "systems design"
  ],
  "labs": [
    "Implement a C ABI for a robot arm with opaque handle and error codes, wrap it in a move-only RAII class, test ownership and error translation, and write an ownership audit of the interface."
  ],
  "assessment_refs": [
    "CPP12-diagnostic-v1"
  ],
  "review_prompts": [
    "A vendor ships a closed-source C++ driver library as a .so with std::string and std::vector in its public header. Your team uses a different compiler version. List the risks and propose an integration strategy."
  ],
  "extension_refs": [
    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines",
    "https://community.kde.org/Policies/Binary_Compatibility_Issues_With_C%2B%2B"
  ]
}
---

## Why this matters

Robotics software is assembled from libraries written by different teams, compiled at different times, and often distributed as binaries: a camera vendor's SDK, a motion planning library, ROS 2 packages, a closed-source motor driver. The boundaries between them are where bugs live. A function that takes `Frame*` does not say who frees the frame; a struct whose layout changed in a new library version silently reads the wrong field in an old executable; an exception thrown inside a C callback aborts the whole process. These are not syntax errors, the compiler accepts them, and they appear as crashes in the field. This lesson is about reading and writing interfaces so that ownership, lifetime, errors and binary compatibility are explicit. It combines everything from the track: RAII and moves (CPP03), invariants and interfaces (CPP04), templates (CPP06), build systems and linking (CPP07), and concurrency contracts (CPP10).

## Intuition

Distinguish two kinds of compatibility. **API** (application programming interface) compatibility means *source code* that used the library still compiles. **ABI** (application binary interface) compatibility means an *already compiled* program still runs when the library binary is replaced by a new version, without recompiling. The ABI is everything the machine code relies on: symbol names, calling convention (how arguments are passed), sizes and layouts of types, vtable layouts, exception handling.

A stable library interface therefore looks like a plug: a small, boring, explicit surface (opaque handles, plain functions, plain integers and doubles, error codes) with all the interesting C++ behind it. Inside your own code you want the opposite: rich types, RAII and exceptions. The standard solution is two layers: a C-style boundary for the binary and a thin header-only C++ wrapper that makes the C API safe to use.

![Layers: user code, C++ RAII wrapper, stable C ABI with opaque handle, library internals; right, table of API/ABI compatibility of common changes](/lesson-figures/CPP12.svg)

*A stable C boundary between the wrapper (compiled with the user's code) and the library internals; the table classifies typical changes.*

## Theory and derivation

### Symbols, name mangling and `extern "C"`

C++ allows overloading, so the compiler encodes the parameter types and namespaces into the symbol name (*mangling*). In the compiled `.so`:

```
c_add                                   <- extern "C" int c_add(int, int)
_Z7cxx_addii                            <- int cxx_add(int, int)
_ZN5robot8cxx_add2Eii                   <- robot::cxx_add2(int, int)
_Z12takes_vectorRKSt6vectorIiSaIiEE     <- takes_vector(const std::vector<int>&)
```
(`nm -D lib.so` lists them; `nm -DC` demangles.) Mangling differs between compilers and even between versions, so a C++ API compiled with one toolchain generally cannot be called from code compiled with another. `extern "C"` turns off mangling and uses the C calling convention, so any language (C, Python `ctypes`, Rust FFI) can call the function.

### What belongs in a stable ABI

Safe across a binary boundary: fixed-width integers, `double`, pointers, opaque handles, plain C structs with *fixed, documented layout* (append-only if versioned), function pointers with C linkage, enums with an explicit underlying size, `const char*` with a documented owner. Risky: `std::string`, `std::vector`, `std::shared_ptr`, `std::function` in a signature (their layout depends on the standard library version and flags: for example GCC's dual ABI `_GLIBCXX_USE_CXX11_ABI` changes `std::string`); virtual functions (adding or reordering changes the vtable); classes with inline member functions that touch private data (inlined into the caller); templates instantiated in both sides; exceptions across the boundary; `new` in the library and `delete` in the caller if they use different allocators or runtimes.

**Experiment.** Version 1 of a library exposes `struct Pose { double x; double y; }` and `get_pose(Pose*)`. Version 2 inserts `double z` between them and rewrites the function. An application compiled against version 1 headers but run against version 2 prints `x=1 y=9` instead of `x=1 y=2`: it reads the `z` field as `y`, and the library even writes 24 bytes into the application's 16-byte object. Nothing failed at link time because the symbol name `get_pose` is unchanged.

### Classifying changes

| Change | API (source) | ABI (binary) |
|---|---|---|
| Add a new free function | compatible | compatible |
| Add an enum value | compatible (switches may warn) | compatible if the size does not change; old code may not handle it |
| Change a parameter type or add a parameter | breaks | breaks (new symbol/signature) |
| Reorder or add a public data member | usually compatible | breaks (layout) |
| Add a virtual function | compatible | breaks (vtable layout) |
| Add a private data member to a class used by value | compatible | breaks (`sizeof` changes) |
| Change behavior but not the signature | compatible | compatible (but may violate the contract) |
| Add a data member to a pimpl'd class | compatible | compatible (hidden behind a pointer) |

### Opaque handles, pimpl and ownership

**Opaque handle** (C): `typedef struct rc_arm rc_arm;` plus `rc_arm* rc_arm_create(...)` and `rc_arm_destroy(rc_arm*)`. The caller never sees the layout, so the library can change it freely. The contract states that the creator owns the allocation: create/destroy are paired.

**Pimpl idiom** (C++): the class holds `std::unique_ptr<Impl>` to a hidden implementation type defined in the `.cpp`. The public header keeps the same size forever. Pitfall: the destructor (and move operations) must be defined in the `.cpp`, where `Impl` is complete; otherwise the compiler generates them inline where `Impl` is incomplete, and fails with "invalid application of 'sizeof' to incomplete type".

**Ownership vocabulary** to look for in any interface (Core Guidelines I.11, F.26): raw pointer returned by a function (who frees it?), raw pointer parameter (borrowed or taken?), `const char*` returned (static, or valid until the next call?), callbacks with `void* user_data` (lifetime of the data, thread of the call), shared handles (`cv::Mat` copies share the pixel buffer: assignment is shallow, `clone()` is deep), views (`std::string_view`, `Eigen::Map`, `std::span`) that do not own.

### Errors across the boundary

An exception must not propagate out of an `extern "C"` function: if the caller is C, Python or another runtime that cannot unwind C++ frames, the behavior is undefined and typically `std::terminate`. Experiment: `risky(-3)` in a shared library that throws, called through Python `ctypes`, aborts the process with `terminate called after throwing an instance of 'std::invalid_argument'`. The C boundary catches everything and returns an error code; the C++ wrapper translates the code back into an exception (or `std::expected`/`optional` where exceptions are disallowed). Also provide `rc_strerror(code)` returning a static string.

### Generic libraries and ABI

Templates are instantiated in the translation unit that uses them, so a header-only library (Eigen, most of the standard library) has no ABI of its own: the user's compiler generates the code, and different compiler versions in one program coexist as long as no template-typed objects cross a binary boundary. A compiled library with templates in its interface can reduce compile time by explicit instantiation (`extern template class Filter<double>;` in the header and `template class Filter<double>;` in one `.cpp`), but then only those instantiations are available, and the layout of `Filter<double>` is part of the ABI.

### Systems design checklist

For every public function write down: **Who owns** each pointer/handle argument and result; **how long** it is valid; **which thread(s)** may call it and whether it is reentrant (CPP10); **what errors** it reports and how; **what can change** in a minor version. Deliver these as comments or documentation next to the declaration, and encode them in types where possible (`unique_ptr` for transfer, references for borrow, `const` for read-only).

## Worked example

Audit this hypothetical camera SDK header, then wrap it.

```c
typedef struct cam cam;
cam* cam_open(const char* device);
void cam_close(cam* c);
const char* cam_error(void);
unsigned char* cam_grab(cam* c, int* size);
void cam_on_frame(cam* c, void (*cb)(unsigned char*, int, void*), void* user);
```
1. `cam_open` returns a pointer: **owned by the caller**, released with `cam_close` (by naming convention; the header does not say). `NULL` on failure; the reason is in `cam_error()`, a global, so it is **not thread-safe**.
2. `cam_error()` returns `const char*`: owner unclear; probably a static buffer overwritten by the next call, so it must be copied immediately.
3. `cam_grab` returns `unsigned char*` and the size through an out parameter: **who frees the buffer?** Either the camera reuses an internal buffer (valid until the next grab) or the caller must free it. The header is silent: a *risk*. The safe wrapper must copy into a `std::vector<unsigned char>` immediately.
4. `cam_on_frame` registers a callback with `void* user`: the callback runs on an **unknown thread** (probably a driver thread); `user` must outlive the registration; the buffer pointer is valid only during the callback. An exception thrown in the callback would cross C frames.
5. Wrapper design: `class Camera` holds `unique_ptr<cam, decltype(&cam_close)>`, throws `Error` from the constructor when `cam_open` returns null (with the message copied from `cam_error()`), `grab()` returns `std::vector<unsigned char>`, the callback trampoline is a static function that catches all exceptions and stores them, and `~Camera` unregisters the callback and closes the camera (in that order, so the callback cannot run on a destroyed `Camera`).

The result is an interface where ownership is in the types: the user never sees a raw pointer or a thread the library created.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** Given the `nm -D` listing above, which symbols can be called from Python with `ctypes` by their plain name, and why? What is the information carried in `_Z7cxx_addii`?
2. **(Easy)** *(Adapted from: KDE, Binary Compatibility Issues With C++)* Classify as API-breaking, ABI-breaking only, or neither: (a) add a private member to a class used by value; (b) add a new free function; (c) add a virtual function to a class with subclasses in other libraries; (d) change a function's default argument value; (e) rename a parameter; (f) change `int` to `long` in a parameter.
3. **(Easy)** *(Adapted from: C++ Core Guidelines, I.11 and F.26)* For each declaration state what the signature says about ownership and what it leaves unsaid: `Frame* grab();`, `void put(Frame*);`, `const char* name() const;`, `void set_cb(Callback, void*);`, `std::unique_ptr<Map> load(const std::string&);`.
4. **(Medium)** Find the two bugs in this C-interface function and fix them:
   ```cpp
   extern "C" const char* describe(int code) {
     if (code < 0) throw std::invalid_argument("negative");
     std::string s = "code " + std::to_string(code);
     return s.c_str();
   }
   ```
5. **(Medium)** *(Adapted from: OpenCV documentation, "Mat - the basic image container")* A class holds a `std::shared_ptr<std::vector<int>>` like `cv::Mat` headers share pixels. What do `a.at(0)`, `b.at(0)` and `c.at(0)` print after `Image a(3,1); Image b = a; Image c = a.clone(); b.fill(7);`? What robotics bug does this cause when a callback stores a copy of the frame?
6. **(Medium)** Write the header and the `.cpp` of `Planner` with a pimpl. A user translation unit that only includes the header and creates a `Planner` fails with "invalid application of 'sizeof' to incomplete type". Why, and what is the one-line fix?
7. **(Medium)** Interpret the experiment: the application printed `x=1 y=9` after the library was swapped. Explain exactly what happened in terms of offsets, and give three ways to evolve the struct without breaking old binaries.
8. **(Hard)** *(Adapted from: libstdc++ manual, dual ABI)* A prebuilt `.so` was compiled with `_GLIBCXX_USE_CXX11_ABI=0` and exports `void f(const std::string&)`. Your code uses the default. What happens at link time and why? List three strategies for a vendor delivering a binary SDK.
9. **(Hard)** Review this hypothetical header and list at least six ownership, lifetime, thread or ABI risks, then rewrite it:
   ```cpp
   // libgrip.h (hypothetical)
   struct GripperState { double width; double force; int status; };
   class Gripper {
    public:
     Gripper(const std::string& port);
     GripperState* poll();                 // returns internal state
     void on_contact(std::function<void(GripperState)> cb);
     virtual void close(double width);
     std::vector<double> history;
   };
   ```
10. **(Hard)** You maintain a generic `Filter<T>` for `float` and `double`. Compare (i) header-only, (ii) compiled library with explicit instantiation, (iii) a C API with two sets of functions. Evaluate compile time, ABI stability, extensibility to `long double`, and binary size.
11. **(Mini-project)** Pick a real robotics library interface you use (for example an `rclcpp` subscription callback, `cv::Mat`, `Eigen::Map`, or a `tf2::Buffer`) and write a one-page ownership audit (function, owner, lifetime, thread, error reporting, ABI risk) plus a 30-line wrapper or test that demonstrates one risk.

## Reference implementation

A complete single-file model of a library with a C ABI (opaque handle, error codes, no exceptions across the boundary, a test hook) and the C++ RAII wrapper. In a real project the middle section is compiled into `libarm.so` and the wrapper lives in the installed header. Compile with `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

```cpp
// CPP12 reference: a C ABI around a C++ implementation (opaque handle, error codes, no exceptions
// across the boundary) and a safe C++ RAII wrapper on top of it.
#include <cmath>
#include <cstddef>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

// ---------------- the C interface (what a header robot_c_api.h would declare) ----------------
extern "C" {
typedef struct rc_arm rc_arm;  // opaque: callers never see the layout
enum { RC_OK = 0, RC_ERR_NULL = -1, RC_ERR_RANGE = -2, RC_ERR_VALUE = -3 };

rc_arm* rc_arm_create(int dof);  // caller owns the result; release with rc_arm_destroy; NULL on failure
void rc_arm_destroy(rc_arm* arm);  // accepts NULL
int rc_arm_set_joint(rc_arm* arm, int index, double angle);
int rc_arm_get_joint(const rc_arm* arm, int index, double* out);
int rc_arm_dof(const rc_arm* arm);                // number of joints, or a negative error code
const char* rc_strerror(int code);                // static storage: do not free
int rc_live_arms(void);                           // test hook: number of arms not yet destroyed
}

// ---------------- implementation (compiled into the shared library) ----------------
struct rc_arm {
  std::vector<double> q;
};
static int g_live = 0;

extern "C" {
rc_arm* rc_arm_create(int dof) {
  try {  // an exception must never cross the C boundary
    if (dof <= 0 || dof > 32) return nullptr;
    rc_arm* a = new rc_arm{std::vector<double>(static_cast<std::size_t>(dof), 0.0)};
    ++g_live;
    return a;
  } catch (...) {
    return nullptr;
  }
}
void rc_arm_destroy(rc_arm* arm) {
  if (!arm) return;
  delete arm;
  --g_live;
}
int rc_arm_set_joint(rc_arm* arm, int index, double angle) {
  if (!arm) return RC_ERR_NULL;
  if (index < 0 || static_cast<std::size_t>(index) >= arm->q.size()) return RC_ERR_RANGE;
  if (!std::isfinite(angle)) return RC_ERR_VALUE;
  arm->q[static_cast<std::size_t>(index)] = angle;
  return RC_OK;
}
int rc_arm_get_joint(const rc_arm* arm, int index, double* out) {
  if (!arm || !out) return RC_ERR_NULL;
  if (index < 0 || static_cast<std::size_t>(index) >= arm->q.size()) return RC_ERR_RANGE;
  *out = arm->q[static_cast<std::size_t>(index)];
  return RC_OK;
}
int rc_arm_dof(const rc_arm* arm) { return arm ? static_cast<int>(arm->q.size()) : RC_ERR_NULL; }
const char* rc_strerror(int code) {
  switch (code) {
    case RC_OK: return "ok";
    case RC_ERR_NULL: return "null handle or pointer";
    case RC_ERR_RANGE: return "joint index out of range";
    case RC_ERR_VALUE: return "angle is not finite";
    default: return "unknown error";
  }
}
int rc_live_arms(void) { return g_live; }
}

// ---------------- the C++ wrapper (header-only, ships with the user's code) ----------------
class Error : public std::runtime_error {
 public:
  explicit Error(int code) : std::runtime_error(rc_strerror(code)), code_(code) {}
  int code() const { return code_; }

 private:
  int code_;
};

inline void check(int code) {
  if (code != RC_OK) throw Error(code);
}

// Owns an rc_arm. Move-only; a moved-from Arm is empty and every operation on it throws Error(RC_ERR_NULL).
class Arm {
 public:
  explicit Arm(int dof) : h_(rc_arm_create(dof), &rc_arm_destroy) {
    if (!h_) throw std::invalid_argument("rc_arm_create failed (dof must be in 1..32)");
  }
  Arm(Arm&&) noexcept = default;
  Arm& operator=(Arm&&) noexcept = default;

  void set(int index, double angle) { check(rc_arm_set_joint(h_.get(), index, angle)); }
  double get(int index) const {
    double out = 0.0;
    check(rc_arm_get_joint(h_.get(), index, &out));
    return out;
  }
  int dof() const {
    const int n = rc_arm_dof(h_.get());
    check(n < 0 ? n : RC_OK);
    return n;
  }

 private:
  std::unique_ptr<rc_arm, void (*)(rc_arm*)> h_;
};

// ---- self-test
int main() {
  static_assert(!std::is_copy_constructible_v<Arm>);
  static_assert(std::is_nothrow_move_constructible_v<Arm>);
  {
    Arm a(3);
    a.set(1, 0.5);
    Arm b = std::move(a);
    if (b.get(1) != 0.5 || b.dof() != 3 || rc_live_arms() != 1) return 1;
    try { a.get(0); return 2; } catch (const Error& e) { if (e.code() != RC_ERR_NULL) return 3; }
    try { b.set(3, 1.0); return 4; } catch (const Error& e) { if (e.code() != RC_ERR_RANGE) return 5; }
  }
  if (rc_live_arms() != 0) return 6;
  std::cout << "CPP12 reference self-test passed\n";
}
```

Commands used to inspect and break binary compatibility:

```
g++ -std=c++17 -shared -fPIC mylib.cpp -o libmy.so
nm -D libmy.so | grep ' T '          # exported symbols; add -C to demangle
ldd ./app                            # which shared libraries are resolved
g++ -shared -fPIC pose_v1.cpp -o libpose.so && g++ app.cpp -L. -lpose -Wl,-rpath,'$ORIGIN' -o app && ./app   # x=1 y=2
g++ -shared -fPIC pose_v2.cpp -o libpose.so && ./app                                                        # x=1 y=9
```

## Independent practice

### Goal

Implement a C interface with an opaque handle and error codes, wrap it in a move-only RAII class, prove with tests that ownership and errors are handled, and write the ownership audit that documents the interface.

### Setup

`g++` with C++17 (`nm`, `ldd` for the optional shared-library step). Save the starter and then the tests below it as `lab.cpp`; build with `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab`.

### Tasks

1. Define `struct rc_arm`, the live-count bookkeeping and implement `rc_arm_create`, `rc_arm_destroy`, `rc_arm_dof`, `rc_strerror`, `rc_live_arms`. Wrap bodies in `try/catch(...)`.
2. Implement `rc_arm_set_joint` and `rc_arm_get_joint` with all error codes, making sure a rejected call changes nothing.
3. Implement `check`, `Error`'s message and `Arm` (constructor, `set`, `get`, `dof`); the defaulted move operations must leave a moved-from `Arm` throwing `Error(RC_ERR_NULL)`.
4. Run the tests under ASan and confirm that `rc_live_arms()` returns to 0 after every scope (including when an exception is thrown).
5. Split the file: compile the C-API part into `libarm.so` and check `nm -D libarm.so | grep rc_` shows unmangled names; link a tiny `main` against it.
6. Write the ownership audit (a table of 7 functions with owner, lifetime, thread safety, error, ABI risk) and one paragraph on how you would extend the struct in version 2 without breaking old binaries.

### Starter code

```cpp
#include <cmath>
#include <cstddef>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

// ---------------- C interface: DO NOT change these declarations ----------------
extern "C" {
typedef struct rc_arm rc_arm;  // opaque handle
enum { RC_OK = 0, RC_ERR_NULL = -1, RC_ERR_RANGE = -2, RC_ERR_VALUE = -3 };

rc_arm* rc_arm_create(int dof);      // 1..32 joints, all angles 0.0; NULL if dof is out of range or allocation fails
void rc_arm_destroy(rc_arm* arm);    // accepts NULL (no-op)
int rc_arm_set_joint(rc_arm* arm, int index, double angle);       // RC_ERR_NULL / RC_ERR_RANGE / RC_ERR_VALUE (non-finite angle)
int rc_arm_get_joint(const rc_arm* arm, int index, double* out);  // RC_ERR_NULL for null arm OR null out; RC_ERR_RANGE
int rc_arm_dof(const rc_arm* arm);   // number of joints, or RC_ERR_NULL
const char* rc_strerror(int code);   // static strings: "ok", "null handle or pointer", "joint index out of range",
                                     // "angle is not finite", and "unknown error" for anything else
int rc_live_arms(void);              // test hook: number of arms created and not yet destroyed
}

// ---------------- implementation of the interface ----------------
// TODO: define struct rc_arm (hold the joint angles) and the bookkeeping behind rc_live_arms.
// Rules: no C++ exception may escape any extern "C" function (catch everything, return an error).
extern "C" {
rc_arm* rc_arm_create(int dof) { throw std::logic_error("NotImplemented"); }
void rc_arm_destroy(rc_arm* arm) { throw std::logic_error("NotImplemented"); }
int rc_arm_set_joint(rc_arm* arm, int index, double angle) { throw std::logic_error("NotImplemented"); }
int rc_arm_get_joint(const rc_arm* arm, int index, double* out) { throw std::logic_error("NotImplemented"); }
int rc_arm_dof(const rc_arm* arm) { throw std::logic_error("NotImplemented"); }
const char* rc_strerror(int code) { throw std::logic_error("NotImplemented"); }
int rc_live_arms(void) { throw std::logic_error("NotImplemented"); }
}

// ---------------- C++ wrapper ----------------
// Error(code): std::runtime_error whose what() is rc_strerror(code); code() returns the code.
class Error : public std::runtime_error {
 public:
  explicit Error(int code) : std::runtime_error("TODO"), code_(code) {}
  int code() const { return code_; }

 private:
  int code_;
};

// throws Error(code) unless code == RC_OK
inline void check(int code) { throw std::logic_error("NotImplemented"); }

// Owns an rc_arm through std::unique_ptr<rc_arm, void (*)(rc_arm*)>. Move-only. The constructor throws
// std::invalid_argument if rc_arm_create fails. A moved-from Arm is empty: every operation on it throws
// Error(RC_ERR_NULL). set/get translate error codes with check().
class Arm {
 public:
  explicit Arm(int dof) { throw std::logic_error("NotImplemented"); }
  Arm(Arm&&) noexcept = default;
  Arm& operator=(Arm&&) noexcept = default;
  void set(int index, double angle) { throw std::logic_error("NotImplemented"); }
  double get(int index) const { throw std::logic_error("NotImplemented"); }
  int dof() const { throw std::logic_error("NotImplemented"); }

 private:
  std::unique_ptr<rc_arm, void (*)(rc_arm*)> h_{nullptr, &rc_arm_destroy};
};
```

### Tests

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#include <cstring>
#include <iostream>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)
template <class E, class F> bool throws(F f) { try { f(); } catch (const E&) { return true; } return false; }
template <class F> int code_of(F f) { try { f(); } catch (const Error& e) { return e.code(); } return RC_OK; }

int main() {
  static_assert(!std::is_copy_constructible_v<Arm>, "Arm must be move-only");
  static_assert(std::is_nothrow_move_constructible_v<Arm>, "moves must be noexcept");
  CHECK(rc_live_arms() == 0);
  // 1. the C API directly: codes, not exceptions
  rc_arm* raw = rc_arm_create(2);
  CHECK(raw != nullptr && rc_arm_dof(raw) == 2 && rc_live_arms() == 1);
  CHECK(rc_arm_set_joint(raw, 1, 0.25) == RC_OK);
  double out = -1.0;
  CHECK(rc_arm_get_joint(raw, 1, &out) == RC_OK && out == 0.25);
  CHECK(rc_arm_get_joint(raw, 0, &out) == RC_OK && out == 0.0);
  CHECK(rc_arm_set_joint(raw, 2, 0.0) == RC_ERR_RANGE && rc_arm_set_joint(raw, -1, 0.0) == RC_ERR_RANGE);
  CHECK(rc_arm_set_joint(raw, 0, NAN) == RC_ERR_VALUE && rc_arm_set_joint(raw, 0, INFINITY) == RC_ERR_VALUE);
  CHECK(rc_arm_get_joint(raw, 0, &out) == RC_OK && out == 0.0);  // rejected writes changed nothing
  CHECK(rc_arm_get_joint(raw, 0, nullptr) == RC_ERR_NULL);
  CHECK(rc_arm_set_joint(nullptr, 0, 1.0) == RC_ERR_NULL && rc_arm_dof(nullptr) == RC_ERR_NULL);
  rc_arm_destroy(raw);
  rc_arm_destroy(nullptr);  // allowed
  CHECK(rc_live_arms() == 0);
  CHECK(rc_arm_create(0) == nullptr && rc_arm_create(33) == nullptr && rc_arm_create(-5) == nullptr);
  CHECK(rc_live_arms() == 0);
  // 2. error strings
  CHECK(std::strcmp(rc_strerror(RC_OK), "ok") == 0);
  CHECK(std::strcmp(rc_strerror(RC_ERR_RANGE), "joint index out of range") == 0);
  CHECK(std::strcmp(rc_strerror(-99), "unknown error") == 0);
  // 3. the C++ wrapper: RAII, exceptions, moves
  {
    Arm a(3);
    CHECK(a.dof() == 3 && rc_live_arms() == 1);
    a.set(2, 1.5);
    CHECK(a.get(2) == 1.5 && a.get(0) == 0.0);
    CHECK(code_of([&] { a.set(3, 0.0); }) == RC_ERR_RANGE);
    CHECK(code_of([&] { a.set(0, NAN); }) == RC_ERR_VALUE);
    try { a.get(9); } catch (const Error& e) { CHECK(std::strcmp(e.what(), "joint index out of range") == 0); }
    Arm b = std::move(a);                                   // ownership moves, no new arm is created
    CHECK(rc_live_arms() == 1 && b.get(2) == 1.5);
    CHECK(code_of([&] { a.get(0); }) == RC_ERR_NULL);       // moved-from is empty
    CHECK(code_of([&] { a.dof(); }) == RC_ERR_NULL);
    Arm c(1);
    CHECK(rc_live_arms() == 2);
    c = std::move(b);                                       // c's old arm must be destroyed
    CHECK(rc_live_arms() == 1 && c.dof() == 3);
  }
  CHECK(rc_live_arms() == 0);                               // everything released at scope exit
  CHECK(throws<std::invalid_argument>([] { Arm bad(0); }));
  CHECK(rc_live_arms() == 0);
  // 4. exception safety: an exception thrown mid-scope still destroys the arm
  try { Arm t(2); t.set(5, 0.0); } catch (const Error&) {}
  CHECK(rc_live_arms() == 0);
  std::cout << "all tests passed\n";
}
```

### Expected output

```
all tests passed
```

With the stubs the first call terminates with `NotImplemented`. For the shared-library step `nm -D libarm.so` should list `rc_arm_create`, `rc_arm_destroy`, `rc_arm_set_joint`, `rc_arm_get_joint`, `rc_arm_dof`, `rc_strerror` and `rc_live_arms` exactly as written, with no `_Z` prefixes.

### Extension challenge

Add `rc_version()` and a `size` field to a public options struct so that the library can detect which version of the struct the caller compiled against; or call the shared library from Python with `ctypes` and write a Python context manager with the same ownership semantics as `Arm`.

### Library track

Python's standard-library `ctypes` is the real-world consumer of a C ABI, and the best test that your boundary is clean. Put the interface declarations and the implementation (everything above the "C++ wrapper" comment, with its includes, no `main`) into `arm.cpp`, build the shared library, and call it from Python:

```
g++ -std=c++17 -Wall -Wextra -shared -fPIC arm.cpp -o libarm.so
nm -D libarm.so | grep ' T '        # seven unmangled rc_* symbols, no _Z prefixes
python3 lib_arm.py                   # the script below
```

```python
import ctypes, math

lib = ctypes.CDLL("./libarm.so")                      # the C ABI: plain symbol names, no mangling
lib.rc_arm_create.restype = ctypes.c_void_p           # opaque handle = an address; we never look inside
lib.rc_arm_create.argtypes = [ctypes.c_int]
lib.rc_arm_destroy.argtypes = [ctypes.c_void_p]
lib.rc_arm_set_joint.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
lib.rc_arm_get_joint.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
lib.rc_arm_dof.argtypes = [ctypes.c_void_p]
lib.rc_strerror.restype = ctypes.c_char_p             # static storage: ctypes copies it, we never free it
lib.rc_strerror.argtypes = [ctypes.c_int]
RC_OK, RC_ERR_NULL, RC_ERR_RANGE, RC_ERR_VALUE = 0, -1, -2, -3


class Arm:
    """The Python twin of the C++ wrapper: RAII through a context manager."""
    def __init__(self, dof):
        self.h = lib.rc_arm_create(dof)
        if not self.h:
            raise ValueError("rc_arm_create failed (dof must be in 1..32)")
    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
    def close(self):
        if self.h:
            lib.rc_arm_destroy(self.h)
            self.h = None
    def set(self, i, angle):
        code = lib.rc_arm_set_joint(self.h, i, angle)
        if code != RC_OK:
            raise RuntimeError(lib.rc_strerror(code).decode())
    def get(self, i):
        out = ctypes.c_double()
        code = lib.rc_arm_get_joint(self.h, i, ctypes.byref(out))
        if code != RC_OK:
            raise RuntimeError(lib.rc_strerror(code).decode())
        return out.value

assert lib.rc_live_arms() == 0
with Arm(3) as a:
    a.set(1, 0.5)
    assert a.get(1) == 0.5 and lib.rc_arm_dof(a.h) == 3 and lib.rc_live_arms() == 1
    for bad, msg in ((lambda: a.set(3, 1.0), "joint index out of range"), (lambda: a.set(0, math.nan), "angle is not finite")):
        try:
            bad(); raise AssertionError("should have failed")
        except RuntimeError as e:
            assert str(e) == msg
assert lib.rc_live_arms() == 0                        # released on scope exit, the same invariant as the C++ tests
assert lib.rc_arm_create(0) is None and lib.rc_arm_create(33) is None
lib.rc_arm_destroy(None)                              # NULL is accepted: no-op
print("library track ok")
```

Expected: `library track ok`. The script shows what the C++ `Arm` wrapper does in another language: the handle is an opaque address, the error codes become exceptions, and `rc_live_arms()` proves the arm is released when the `with` block ends. Try calling a `cxx_`-style function (a mangled C++ function) through `ctypes` by its plain name: it fails with `AttributeError`. If you compile with an exception-throwing function exported as `extern "C"` and call it from here, the process aborts, as in the theory section.

## Verification

- `nm -D` on every release: the exported symbol list is the ABI. Diff it between versions (tools such as `abidiff` from libabigail automate the comparison of types and symbols).
- Write a test that builds the application against version N headers and runs it against version N+1 library binaries.
- Count live resources with a test hook (here `rc_live_arms`) and assert it is 0 at the end of every test and after thrown exceptions.
- Run under ASan/UBSan and, for threads, TSan (CPP08, CPP10); try the C API from a second language (Python `ctypes`) to prove it is really C.
- Review checklist per function: owner, lifetime, thread, error path, nullability; reviewers should be able to answer without reading the implementation.
- Check `sizeof` and `offsetof` of public structs with `static_assert` so layout changes fail the build.

## Failure modes

| Mistake | Consequence |
|---|---|
| Exception escaping an `extern "C"` function | `terminate` or undefined behavior in the caller (shown with `ctypes`) |
| Returning `s.c_str()` of a local `std::string` | dangling pointer; garbage text or crash |
| Inserting a field in the middle of a public struct | old binaries read the wrong field (`y=9` instead of `y=2`), possible memory corruption |
| `std::string` in the signature of a prebuilt `.so` with a different libstdc++ ABI flag | link error `undefined reference to f(std::__cxx11::basic_string...)` |
| Allocating in the library and `delete`-ing in the caller | heap corruption when allocators differ |
| Adding a virtual function to a public class | vtable layout changes; old subclasses crash |
| Callback with `void*` user data that outlives its object | use after free on the driver thread |
| Defining the destructor of a pimpl class inline in the header | `incomplete type` error |
| Shallow copy of a `cv::Mat`-like handle assumed to be deep | two owners modify one buffer; data race or corruption |
| Global `cam_error()` string with several threads | race; wrong message for the wrong thread |

## Alternatives and trade-offs

- **C API + C++ wrapper vs C++ API.** The C boundary survives compiler changes, works from Python/Rust and can be versioned, but is verbose and loses type safety until wrapped. A pure C++ API is nicer but ties all users to one toolchain; it is acceptable when everything is built together (for example inside one ROS 2 workspace).
- **Pimpl vs opaque C handle.** Pimpl keeps a C++ class syntax and allows exceptions behind it, but still has a C++ ABI (mangled names, standard types); a C handle is stricter and portable.
- **Header-only vs compiled.** Header-only is easy to distribute and generic but lengthens compile times and has no ABI contract; compiled libraries give faster builds and hide internals but require ABI discipline and a build system.
- **Virtual interfaces vs function-pointer tables.** Abstract classes are idiomatic but fragile across binaries; a struct of function pointers (as in C plugin APIs) has a fixed layout that can be extended by appending.
- **Exceptions vs error codes vs `std::expected`.** Exceptions give clean code inside one binary; codes cross language boundaries; `std::expected` (C++23, or `tl::expected`) gives explicit errors without exceptions in hard real-time code.
- **Semantic versioning.** Encode the contract: patch releases keep ABI; minor releases only add; major releases may break and change the SONAME (`libfoo.so.2`).

## Transfer and retention

This is the same problem in every ecosystem: Python extension modules and `ctypes` need a C ABI; ROS 2 messages are defined in IDL precisely so that layouts are generated, not hand-written; Rust FFI and `cxx` crates enforce an explicit boundary; Linux distributions track the SONAME of every library. To retain: after a week, write from memory the two-layer pattern (opaque handle, create/destroy, error codes, wrapper with `unique_ptr` and a deleter) and list the six categories of ABI-breaking change; review one dependency in your own project with the audit table.

## Exercise answers

1. `c_add` can be called by its plain name from `ctypes`: it has C linkage, so its symbol is just `c_add`. The others are mangled by the C++ compiler: `_Z7cxx_addii` encodes `_Z` (a C++ symbol), `7cxx_add` (a 7-character name), and `ii` (two `int` parameters); `_ZN5robot8cxx_add2Eii` adds the namespace `robot`; the vector function encodes template and allocator arguments. Mangled names are compiler-specific, and a standard type such as `std::vector` in the signature also makes the layout part of the ABI.
2. (a) ABI-breaking only (`sizeof` changes, source still compiles). (b) neither (compatible both ways). (c) ABI-breaking only (vtable layout) and the source of subclasses still compiles. (d) API-compatible but the default value is baked into callers at compile time, so old binaries keep the old default: a silent behavior mismatch (treat as ABI-relevant). (e) neither. (f) both: source usually still compiles (implicit conversion) but the symbol/signature changes (`long` vs `int` is a different mangled name and calling convention width), so old binaries fail to link or pass wrong-width data.
3. `Frame* grab();` says a pointer comes back; unsaid: owner, lifetime, null meaning. `void put(Frame*);` says a pointer goes in; unsaid: does the callee take ownership, can it be null, is it stored? `const char* name() const;` read-only text; unsaid: valid until when (object lifetime, next call?). `void set_cb(Callback, void*);` unsaid: thread of the call, lifetime of the user data, whether it is called after unregistering. `std::unique_ptr<Map> load(const std::string&);` says: the caller receives exclusive ownership; the argument is borrowed for the call; it can still throw or return null unless documented.
4. Bug 1: an exception escapes the `extern "C"` function (UB or terminate when the caller is C); fix by catching and returning an error value (for example `nullptr` or a status). Bug 2: `s.c_str()` points into a local string destroyed at return: dangling. Fix: return a pointer to static storage (a `static thread_local std::string` buffer, documenting "valid until the next call on this thread") or write into a caller-provided buffer `int describe(int code, char* buf, size_t n)`.
5. Output `7 7 1`: `b = a` copies the handle but shares the buffer, so `fill(7)` changes both `a` and `b`; `clone()` copied the data, so `c` still has 1. Robotics bug: a callback that stores `msg_image` (a shallow copy) while the driver reuses the buffer for the next frame silently sees the data change (or a race with another thread); the fix is `clone()` or storing an immutable shared message (`shared_ptr<const Msg>`).
6. In the header declare `~Planner();` and the move operations (`Planner(Planner&&) noexcept; Planner& operator=(Planner&&) noexcept;`), and define them in the `.cpp` where `struct Planner::Impl { ... };` is complete (`Planner::~Planner() = default;`). Otherwise the implicit inline destructor instantiates `std::default_delete<Impl>` where `Impl` is incomplete, giving "invalid application of 'sizeof' to incomplete type".
7. The application's header says `y` is at offset 8, but version 2 placed `z` at offset 8 and `y` at offset 16; the library wrote `z=9` at offset 8, which the application reads as `y`, and the library also wrote 8 bytes beyond the application's 16-byte struct (undefined behavior, a stack overflow in the application). The symbol name did not change, so the linker did not complain. Ways to evolve safely: append new fields at the end of a struct that carries its own `size` (or version) field as the first member and let the library fill only the fields the caller's size covers; hide the struct behind an opaque handle with accessor functions (`pose_get_y`); add a new function and a new struct (`get_pose_v2`) and keep the old one.
8. At link time you get `undefined reference to f(std::string const&)` because with the default (new) ABI the parameter's type is `std::__cxx11::basic_string<...>` and mangles differently from the old `std::basic_string<...>`; the symbol in the `.so` does not match. Strategies: a C interface (`const char*` and lengths); ship builds for both values of `_GLIBCXX_USE_CXX11_ABI` (and pin one compiler version); ship the library as source or as a static library built with the user's toolchain; or provide a header-only wrapper that converts to the C interface.
9. Risks: `Gripper(const std::string&)` puts `std::string` in the ABI; `poll()` returns a raw pointer to internal state (who owns it, lifetime, thread safety? is it overwritten by the next poll?); `std::function` in `on_contact` (ABI and which thread calls it; exceptions across the call; lifetime of captures); `virtual close` in an exported class (vtable and subclass compatibility; also missing virtual destructor); public `std::vector<double> history` data member (layout and thread safety, anyone can mutate it); `GripperState` is a public struct that cannot grow; no error reporting for `close` and the constructor (exceptions or codes?). Redesign: opaque handle `grip*` with `grip_open/close`, `grip_poll(grip*, GripperState* out, uint32_t size)` copying into caller memory, `grip_set_contact_callback(grip*, void(*)(const GripperState*, void*), void*)` with a documented thread and a catch-all, functions returning codes, plus a C++ wrapper with RAII.
10. (i) Header-only: no ABI problem, any type works (`long double`), but every translation unit recompiles the code (longer builds, larger binaries). (ii) Compiled with explicit instantiation (`extern template class Filter<float>; extern template class Filter<double>;`): faster builds, smaller objects; the layout of `Filter<float>` and `Filter<double>` becomes ABI, and `long double` needs a new instantiation (a library change). (iii) A C API with `filter_f32_*` and `filter_f64_*` function sets: most stable, usable from other languages, verbose, and every new type needs new functions. Choose (i) for a generic header library used inside one build; (ii) for a library with a handful of supported types; (iii) when the library is delivered as binary to unknown toolchains.
11. A good answer includes: a table with at least six functions; for each: owner, lifetime, thread/callback context, error mechanism and ABI risk; at least one risk demonstrated with a short program (for example shallow copy, dangling view, or callback lifetime) and the fix (clone, owner type, or unregister in the destructor); and a recommendation on how to wrap it.

## Further reading

- [C++ Core Guidelines: Interfaces](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - rules I.1-I.27 on explicit, typed, stable interfaces; I.11 (ownership) and I.26-I.27 (ABI) are central here.
- [KDE: Binary Compatibility Issues With C++](https://community.kde.org/Policies/Binary_Compatibility_Issues_With_C%2B%2B) - the practical list of source-, binary- and breaking changes.
- [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html) - the specification of name mangling, object layout and vtables used by GCC and Clang on Linux.

**More practice:** the [KDE binary compatibility guide](https://community.kde.org/Policies/Binary_Compatibility_Issues_With_C%2B%2B) (a do-and-don't list to classify, as in exercise 2), the libstdc++ manual on the [dual ABI](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html) (reproduce exercise 8 with `-D_GLIBCXX_USE_CXX11_ABI=0`), the [`ctypes` documentation](https://docs.python.org/3/library/ctypes.html) (call your `libarm.so`), cppreference on [language linkage](https://en.cppreference.com/w/cpp/language/language_linkage) and the [pimpl idiom](https://en.cppreference.com/w/cpp/language/pimpl), and the Core Guidelines [interfaces section (I)](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#i-interfaces) for the audit of exercise 11.