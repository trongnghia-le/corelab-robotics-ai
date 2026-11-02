---
{
  "id": "cpp07-foundations",
  "module_id": "CPP07",
  "title": "Build systems: CMake, linking, and targets",
  "summary": "Understand compile and link stages, describe a project as targets with usage requirements in CMake, and test it out of source.",
  "estimated_minutes": 80,
  "prerequisites": [
    "CPP01",
    "T01"
  ],
  "source_refs": [
    {
      "title": "CMake Tutorial",
      "url": "https://cmake.org/cmake/help/latest/guide/tutorial/index.html"
    },
    {
      "title": "CMake: cmake-buildsystem(7)",
      "url": "https://cmake.org/cmake/help/latest/manual/cmake-buildsystem.7.html"
    },
    {
      "title": "GNU Make Manual",
      "url": "https://www.gnu.org/software/make/manual/make.html"
    }
  ],
  "objectives": [
    "Explain preprocessing, compiling, archiving and linking, and map each common error message to its stage.",
    "Write a CMakeLists.txt with a library, an application and a test executable using target_* commands.",
    "Choose PUBLIC, PRIVATE or INTERFACE for include directories and link dependencies.",
    "Predict what a build system rebuilds after a source or header change."
  ],
  "core_theory": [
    "CMake",
    "linking",
    "build targets"
  ],
  "labs": [
    "Build the robotmath library, a demo application and a test executable with CMake out of source, run ctest, observe incremental rebuilds, and implement a Python model of build order, rebuild sets and include propagation."
  ],
  "assessment_refs": [
    "CPP07-diagnostic-v1"
  ],
  "review_prompts": [
    "After you add a new .cpp file to a library the build does not see it until you re-run cmake. Explain why when file(GLOB) is used and describe two ways to avoid the problem."
  ],
  "extension_refs": [
    "https://cmake.org/cmake/help/latest/guide/tutorial/index.html",
    "https://cmake.org/cmake/help/latest/manual/cmake-buildsystem.7.html"
  ]
}
---

## Why this matters

A robot software stack is dozens of libraries and executables: math, drivers, planning, perception, tests. Typing compiler commands by hand stops working at the second file. A build system records *what depends on what* and recomputes only what changed; it also gives every developer and every continuous-integration machine the same build. ROS 2 builds with `colcon`, which drives CMake; Eigen, OpenCV, PCL and Gazebo all ship CMake packages. The commonest daily problems (an `undefined reference`, a header that is "not found" in one target but not another, a test that silently runs an old binary) are all build-system problems, and they become easy once you can say which stage of the pipeline produced the message.

## Intuition

Turning source into a program is a pipeline of small steps:

1. **Preprocess**: `#include` pastes headers, `#define` macros expand. Output: one *translation unit* per `.cpp`.
2. **Compile**: each translation unit becomes an *object file* (`.o`) containing machine code with unresolved references to functions defined elsewhere.
3. **Archive** (static library `.a`) or link into a shared library (`.so`).
4. **Link**: the linker joins object files and libraries, resolving every reference to exactly one definition, and produces an executable.

A build system is a *graph*: each output depends on its inputs, and an output is rebuilt when any input is newer. CMake does not compile anything itself. It *generates* a native build (Makefiles or Ninja files) from a description made of **targets**, and the native tool executes it. A target (library or executable) carries **usage requirements**: include directories, compile definitions, and what it links. `PUBLIC` requirements travel to everyone who links the target; `PRIVATE` ones stay inside.

![Pipeline from sources to objects to a library and executables, with a dependency graph showing which files rebuild when a header changes](/lesson-figures/CPP07.svg)

*Sources compile to objects, objects archive into a library, and executables link the library; a changed header triggers every dependent object.*

## Theory and derivation

### Errors by stage

| Message | Stage | Typical cause |
|---|---|---|
| `fatal error: robotmath/vec2.hpp: No such file or directory` | preprocess | include directory not given to this target |
| `error: 'foo' was not declared in this scope` | compile | missing `#include`, typo, wrong namespace |
| `undefined reference to 'robotmath::rotate(...)'` | link | declaration exists but definition's object or library is not linked |
| `multiple definition of 'twice(int)'` | link | non-inline function defined in a header included by two `.cpp` files |

Declarations may repeat; a definition must exist exactly once in the program (the one-definition rule, ODR). Header functions that are defined in the header must be `inline` (or templates, or `constexpr`).

### Make-style rebuild rules

A rule has the form `target: prerequisites` and a recipe. The target is rebuilt when any prerequisite is newer (or missing). Compilers can write the true header dependencies (`-MMD`), which CMake's generated builds use automatically. Consequence: changing one `.cpp` recompiles one object and relinks; changing a widely included header recompiles every object that includes it. If $k$ of $N$ objects include a header, the cost of touching it is $k$ compiles plus the links; the cost of touching a `.cpp` is 1 compile plus the links. This is why headers should include as little as possible.

### CMake essentials

```cmake
add_library(robotmath src/vec2.cpp)                      # a target
target_include_directories(robotmath PUBLIC include)     # usage requirement
add_executable(demo src/main.cpp)
target_link_libraries(demo PRIVATE robotmath)            # links AND inherits PUBLIC requirements
```

- Use **target-based commands** (`target_include_directories`, `target_compile_options`, `target_link_libraries`), not directory-global `include_directories` or `link_libraries`.
- **PUBLIC** = needed to build the target *and* by its users (the library's headers mention the dependency); **PRIVATE** = only needed to build the target itself (used only in `.cpp` files); **INTERFACE** = only needed by users (header-only libraries).
- Out-of-source builds: `cmake -S . -B build` keeps generated files out of the tree; deleting `build/` is a safe clean.
- Build types: `Debug` (`-O0 -g`), `Release` (`-O3 -DNDEBUG`), `RelWithDebInfo`. Always benchmark Release. `-DNDEBUG` disables `assert`, so a test written with `assert` passes vacuously in Release.
- `enable_testing()` and `add_test(NAME x COMMAND exe)` register tests; `ctest` runs them and reports a pass/fail percentage.
- Sources listed explicitly in `add_library`/`add_executable` are safer than `file(GLOB ...)`, which is evaluated only at configure time (a new file is not seen until you re-run `cmake`; `CONFIGURE_DEPENDS` mitigates this).

### Linking order and static libraries

A GNU linker processes archives left to right and extracts only the members needed to satisfy symbols that are *currently* undefined. If `main.o` needs `a_fn` from `libA.a` and `a_fn` needs `b_fn` from `libB.a`, then `g++ main.o -lA -lB` works, but `g++ main.o -lB -lA` fails with `undefined reference to b_fn()`: when `libB.a` was scanned nothing needed it yet. With CMake you never write this by hand: `target_link_libraries` records dependencies and orders the link line.

### The dependency graph

Let the build graph be a directed acyclic graph (DAG). A valid build order is a topological order: every node after all of its prerequisites. The set to rebuild after changing node $c$ is $c$ together with all nodes reachable from $c$ along "is-used-by" edges. A cycle (library A links B, B links A) has no topological order and CMake/Make report it.

## Worked example

The project in the reference implementation has a library `robotmath` (`src/vec2.cpp`, public header in `include/`), an executable `demo`, and a test executable `test_vec2`.

1. **Configure**: `cmake -S proj -B build -DCMAKE_BUILD_TYPE=Release` reads `CMakeLists.txt`, finds the compiler, and generates Makefiles in `build/`. Nothing is compiled yet.
2. **Build**: `cmake --build build` compiles `vec2.cpp` into an object, archives it to `librobotmath.a`, compiles `main.cpp` and `test_vec2.cpp`, and links two executables against the library. The build log shows 3 compile steps, 1 archive and 2 links (percentages 16% to 100%).
3. **Test**: `ctest --test-dir build --output-on-failure` runs `test_vec2`; the result `100% tests passed, 0 tests failed out of 1`.
4. **Incremental**: `touch src/main.cpp && cmake --build build` recompiles only `main.cpp` (1 compile, 1 link). `touch src/vec2.cpp` would recompile it, recreate the archive and relink both executables (1 compile, 1 archive, 2 links). `touch include/robotmath/vec2.hpp` would recompile all three objects, since all three include it.
5. **Includes**: `demo` never mentions `include/`, yet `#include "robotmath/vec2.hpp"` works, because `target_include_directories(robotmath PUBLIC include)` is inherited by anything linking `robotmath`. Remove the `target_link_libraries(demo ...)` line and `demo` fails at the preprocessing stage with `fatal error: robotmath/vec2.hpp: No such file or directory`.
6. **Symbols**: `nm -C build/librobotmath.a | grep ' T '` lists `robotmath::norm`, `robotmath::rotate` and `robotmath::operator+` as defined (`T`) in the archive.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** Classify each message by pipeline stage and give the most likely fix: (a) `fatal error: planner/path.hpp: No such file or directory`; (b) `error: 'Path' does not name a type`; (c) `undefined reference to 'plan(Path const&)'`; (d) `multiple definition of 'clamp01(double)'`.
2. **(Easy)** A project has 40 `.cpp` files that take 3 s each to compile. A header `types.hpp` is included (directly or indirectly) by 25 of them. Estimate the compile time after touching `types.hpp` versus touching one `.cpp` (ignore linking). Name one technique to reduce the first number.
3. **(Easy)** *(Adapted from: GNU Make Manual, introduction to rules)* In the lab graph (`app` needs `libplan` and `main.o`; `main.o` needs `main.cpp` and `plan.hpp`) which nodes does Make rebuild if only `plan.hpp` changes, and in which order?
4. **(Medium)** Find the problems in this `CMakeLists.txt` and rewrite it in modern target-based style.
   ```cmake
   add_library(robotmath src/vec2.cpp)
   include_directories(/home/me/proj/include)
   add_executable(demo src/main.cpp)
   ```
   The project builds on the author's machine, but `demo` fails to link with `undefined reference to robotmath::rotate(...)`.
5. **(Medium)** *(Adapted from: CMake Tutorial, usage requirements)* Library `sensors` has `sensors.hpp` that includes `util/units.hpp` (types in its public API) and `sensors.cpp` that includes `<yaml/parser.hpp>` for configuration. Application `driver` links `sensors`. Choose PUBLIC/PRIVATE for `sensors`'s link to `util` and to `yaml`, and say what error the wrong choice produces for `driver`.
6. **(Medium)** *(Adapted from: CMake documentation, `file(GLOB)`)* A teammate uses `file(GLOB SRC src/*.cpp)` and adds `src/filter.cpp`, but the linker reports `undefined reference to Filter::update`. Explain the sequence of events and give two fixes.
7. **(Medium)** A test uses `assert(norm({3,4}) == 5)`. The test target passes in a Debug build, but a wrong implementation also "passes" in Release. Explain why, and how to make tests independent of the build type.
8. **(Hard)** *(Adapted from: CMake documentation, cmake-buildsystem(7), static libraries)* Given `main.o` -> `libA.a` -> `libB.a` (A uses B), state which of `g++ main.o -lA -lB` and `g++ main.o -lB -lA` links and why. What do you write in CMake so the order is right automatically, and what changes if A links B `PRIVATE` versus `PUBLIC` when `main` itself also uses a B header?
9. **(Hard)** A header defines `int twice(int x) { return 2 * x; }` and is included by `u1.cpp` and `u2.cpp`. Predict the failing stage and message. Give three different corrections and the trade-off of each (inline, `static`, move to `.cpp`).
10. **(Hard)** Design the target graph for a repository with libraries `core` (types), `planning` (uses `core` types in its headers and `Eigen` only internally), `drivers` (uses `core` types only internally), applications `planner_node` and `driver_node`, and a test per library. State each `target_link_libraries` line with its kind, draw the graph and say what rebuilds when `core/include/core/types.hpp` changes (count targets). Why must the graph be acyclic?
11. **(Mini-project)** Extend the lab project with a second library `robotplan` (one function using `robotmath::Vec2` in its public header) that links `robotmath` PUBLIC, plus its own test. Record, in a table, which build steps run after `touch` on (a) `vec2.cpp`, (b) `vec2.hpp`, (c) `robotplan.cpp`; add `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` and show the compile command line of one source; build once with `-DENABLE_ASAN=ON` in a different build directory.

## Reference implementation

The project (shell commands run from the directory that contains `proj/`), then a small Python model of what the build system computes.

`proj/CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.16)
project(robotmath VERSION 0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
option(ENABLE_ASAN "Build with AddressSanitizer and UBSan" OFF)

# 1. the library: sources are private, the include/ directory is part of its public interface
add_library(robotmath src/vec2.cpp)
target_include_directories(robotmath PUBLIC include)
target_compile_options(robotmath PRIVATE -Wall -Wextra)

# 2. an application that uses the library
add_executable(demo src/main.cpp)
target_link_libraries(demo PRIVATE robotmath)

# 3. a separate test executable, registered with CTest
enable_testing()
add_executable(test_vec2 tests/test_vec2.cpp)
target_link_libraries(test_vec2 PRIVATE robotmath)
add_test(NAME vec2 COMMAND test_vec2)

# 4. an optional sanitizer build, switched on from the command line
if(ENABLE_ASAN)
  target_compile_options(robotmath PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(robotmath PUBLIC -fsanitize=address,undefined)
endif()
```

`proj/include/robotmath/vec2.hpp`:

```cpp
#pragma once
#include <cmath>

namespace robotmath {

struct Vec2 {
  double x = 0.0;
  double y = 0.0;
};

Vec2 operator+(Vec2 a, Vec2 b);
double norm(Vec2 v);
// Rotates v counter-clockwise by `angle` radians.
Vec2 rotate(Vec2 v, double angle);

}  // namespace robotmath
```

`proj/src/vec2.cpp`:

```cpp
#include "robotmath/vec2.hpp"

namespace robotmath {

Vec2 operator+(Vec2 a, Vec2 b) { return {a.x + b.x, a.y + b.y}; }

double norm(Vec2 v) { return std::hypot(v.x, v.y); }

Vec2 rotate(Vec2 v, double angle) {
  const double c = std::cos(angle), s = std::sin(angle);
  return {c * v.x - s * v.y, s * v.x + c * v.y};
}

}  // namespace robotmath
```

`proj/src/main.cpp`:

```cpp
#include <iostream>
#include "robotmath/vec2.hpp"

int main() {
  const robotmath::Vec2 p = robotmath::rotate({1.0, 0.0}, 3.14159265358979323846 / 2);
  std::cout << "rotated: " << p.x << " " << p.y << "\n";
}
```

`proj/tests/test_vec2.cpp`:

```cpp
#include <cmath>
#include <cstdlib>
#include <iostream>
#include "robotmath/vec2.hpp"

#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; return EXIT_FAILURE; } } while (0)

int main() {
  using namespace robotmath;
  CHECK(norm({3.0, 4.0}) == 5.0);
  const Vec2 s = Vec2{1.0, 2.0} + Vec2{0.5, -1.0};
  CHECK(s.x == 1.5 && s.y == 1.0);
  const Vec2 r = rotate({1.0, 0.0}, std::acos(-1.0) / 2);
  CHECK(std::fabs(r.x) < 1e-12 && std::fabs(r.y - 1.0) < 1e-12);
  // invariant: rotation preserves length
  CHECK(std::fabs(norm(rotate({2.0, -3.0}, 0.7)) - norm({2.0, -3.0})) < 1e-12);
  std::cout << "test_vec2 passed\n";
  return EXIT_SUCCESS;
}
```

Commands and the observed result:

```
cmake -S proj -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure      # 100% tests passed, 0 tests failed out of 1
./build/demo                                    # rotated: 6.12323e-17 1
cmake -S proj -B build-asan -DENABLE_ASAN=ON && cmake --build build-asan && ctest --test-dir build-asan
```

The same library built by hand, which is what CMake automates:

```
g++ -std=c++17 -Iproj/include -c proj/src/vec2.cpp -o vec2.o      # compile
ar rcs librobotmath.a vec2.o                                         # archive
g++ -std=c++17 -Iproj/include proj/src/main.cpp librobotmath.a -o demo   # compile + link
```

The Python model (the part you implement in the lab):

```python
"""CPP07 reference: a tiny model of what a build system computes (build order, rebuild set,
and CMake-style PUBLIC/PRIVATE include propagation)."""


def topo_order(deps):
    """deps: {node: [nodes it depends on]}. Return every node (also those only mentioned as
    dependencies) in an order where each node comes after all of its dependencies.
    Ties are broken alphabetically. Raises ValueError starting with 'cycle' on a cycle."""
    nodes = set(deps)
    for ds in deps.values():
        nodes.update(ds)
    remaining = {n: set(deps.get(n, ())) for n in nodes}
    order = []
    while remaining:
        ready = sorted(n for n, ds in remaining.items() if not ds)
        if not ready:
            raise ValueError("cycle among: " + ", ".join(sorted(remaining)))
        n = ready[0]
        order.append(n)
        del remaining[n]
        for ds in remaining.values():
            ds.discard(n)
    return order


def rebuild_set(deps, changed):
    """Nodes that must be rebuilt: the changed ones and everything that depends on them,
    directly or transitively. Returned in build (topological) order."""
    dirty = set(changed)
    grew = True
    while grew:
        grew = False
        for n, ds in deps.items():
            if n not in dirty and dirty.intersection(ds):
                dirty.add(n)
                grew = True
    return [n for n in topo_order(deps) if n in dirty]


def interface_dirs(edges, dirs, target):
    """Include directories a target exports to its users: its PUBLIC dirs plus the
    interface dirs of every library it links with PUBLIC."""
    out = set(dirs.get(target, {}).get("public", ()))
    for dep, kind in edges.get(target, ()):
        if kind == "PUBLIC":
            out |= interface_dirs(edges, dirs, dep)
    return out


def visible_dirs(edges, dirs, target):
    """Include directories used when compiling `target`: its own PUBLIC and PRIVATE dirs plus
    the interface dirs of everything it links with (PUBLIC or PRIVATE). Sorted list."""
    out = set(dirs.get(target, {}).get("public", ())) | set(dirs.get(target, {}).get("private", ()))
    for dep, _kind in edges.get(target, ()):
        out |= interface_dirs(edges, dirs, dep)
    return sorted(out)


# ---- self-test
if __name__ == "__main__":
    deps = {"app": ["libplan", "main.o"], "libplan": ["plan.o", "libmath"], "libmath": ["math.o"],
            "plan.o": ["plan.cpp", "math.hpp"], "math.o": ["math.cpp", "math.hpp"],
            "main.o": ["main.cpp", "plan.hpp"]}
    order = topo_order(deps)
    assert order.index("math.o") < order.index("libmath") < order.index("libplan") < order.index("app")
    assert rebuild_set(deps, {"main.cpp"}) == ["main.cpp", "main.o", "app"]
    try:
        topo_order({"a": ["b"], "b": ["a"]})
        raise SystemExit("cycle not detected")
    except ValueError as e:
        assert str(e).startswith("cycle")
    print("CPP07 reference self-test passed")
```

## Independent practice

### Goal

Build, test and inspect a small multi-target C++ project with CMake, then implement the three computations at the heart of a build system (build order, rebuild set, include propagation) and check them against what CMake does.

### Setup

Install `cmake` (3.16+), a C++17 compiler and `make` (for example `sudo apt install cmake g++ make`). Python 3 standard library only for the model. Create `proj/` with the five files from the reference implementation.

### Tasks

1. Configure and build out of source; run `ctest`. Confirm `100% tests passed`.
2. Run `touch proj/src/main.cpp`, rebuild and count the compile and link steps; repeat for `touch proj/include/robotmath/vec2.hpp` and for `proj/src/vec2.cpp`. Write down the three counts.
3. Delete the `target_link_libraries(demo ...)` line and rebuild; copy the error message and name its stage. Restore the line.
4. In a Python file implement `topo_order` (Kahn's algorithm with alphabetical tie-breaking) and cycle detection.
5. Implement `rebuild_set` using `topo_order`, and compare its prediction with the counts of Task 2 by encoding the lab graph as a dict.
6. Implement `interface_dirs` and `visible_dirs` (PUBLIC/PRIVATE propagation) and the tests below.

### Starter code

```python
def topo_order(deps):
    """deps: {node: [nodes it depends on]}. Return EVERY node (also nodes that only appear as
    dependencies) in an order where each node comes after all of its dependencies.
    Ties are broken alphabetically (always pick the alphabetically first ready node).
    Raise ValueError whose message starts with 'cycle' if the graph has a cycle."""
    raise NotImplementedError


def rebuild_set(deps, changed):
    """Nodes that must be rebuilt after the nodes in `changed` changed: the changed nodes and
    every node that depends on one of them, directly or transitively.
    Return them as a list in build (topological) order (use topo_order)."""
    raise NotImplementedError


def interface_dirs(edges, dirs, target):
    """Include dirs `target` exports to users (a set): its 'public' dirs plus the interface
    dirs of each library it links with kind 'PUBLIC'. edges: {t: [(dep, 'PUBLIC'|'PRIVATE')]},
    dirs: {t: {'public': [...], 'private': [...]}} (keys may be missing)."""
    raise NotImplementedError


def visible_dirs(edges, dirs, target):
    """Sorted list of include dirs used to compile `target`: its own public and private dirs
    plus interface_dirs of everything it links with (whatever the link kind)."""
    raise NotImplementedError
```

### Tests

```python


# ---- tests (paste below the starter code)
deps = {"app": ["libplan", "main.o"], "libplan": ["plan.o", "libmath"], "libmath": ["math.o"],
        "plan.o": ["plan.cpp", "math.hpp"], "math.o": ["math.cpp", "math.hpp"],
        "main.o": ["main.cpp", "plan.hpp"]}
# 1. topological order: hand-checked chain and the property "dependencies first"
order = topo_order(deps)
assert sorted(order) == sorted(set(deps) | {d for ds in deps.values() for d in ds})
pos = {n: i for i, n in enumerate(order)}
assert all(pos[d] < pos[n] for n, ds in deps.items() for d in ds)
assert topo_order({"b": ["a"], "c": ["a"]}) == ["a", "b", "c"]
assert topo_order({}) == []
# 2. rebuild sets
assert rebuild_set(deps, {"main.cpp"}) == ["main.cpp", "main.o", "app"]
assert rebuild_set(deps, {"math.hpp"}) == ["math.hpp", "math.o", "libmath", "plan.o", "libplan", "app"]
assert rebuild_set(deps, set()) == []
assert "main.o" not in rebuild_set(deps, {"math.cpp"})      # unrelated object is NOT rebuilt
# 3. cycle detection
try:
    topo_order({"a": ["b"], "b": ["c"], "c": ["a"]})
    raise AssertionError("cycle not detected")
except ValueError as e:
    assert str(e).startswith("cycle")
# 4. include propagation (the CMake PUBLIC / PRIVATE rule)
dirs = {"core": {"public": ["core/include"], "private": ["core/src"]},
        "util": {"public": ["util/include"]},
        "geom": {"public": ["geom/include"]}}
edges = {"core": [("util", "PUBLIC"), ("geom", "PRIVATE")], "app": [("core", "PRIVATE")]}
assert visible_dirs(edges, dirs, "app") == ["core/include", "util/include"]   # geom stays hidden
assert visible_dirs(edges, dirs, "core") == ["core/include", "core/src", "geom/include", "util/include"]
assert visible_dirs(edges, dirs, "util") == ["util/include"]
assert visible_dirs(edges, dirs, "unknown") == []
print("all tests passed")
```

### Expected output

```
all tests passed
```

and, for the CMake part, `100% tests passed, 0 tests failed out of 1` from `ctest`, with the three rebuild counts of Task 2 equal to 1 compile and 1 link (`main.cpp`), 1 compile, 1 archive and 2 links (`vec2.cpp`), and 3 compiles, 1 archive and 2 links (`vec2.hpp`).

### Extension challenge

Add `install(TARGETS robotmath ...)` plus a package config file so that another project can use `find_package(robotmath)` and `target_link_libraries(app PRIVATE robotmath::robotmath)`. Or extend the Python model with timestamps so that it reproduces Make's "is the target older than a prerequisite?" rule.

## Verification

- Run the build twice. The second `cmake --build build` must do nothing ("up to date"); if it rebuilds, a timestamp or a generated file is wrong.
- `cmake --build build --verbose` (or `make VERBOSE=1`) prints the real compile and link commands; check `-I`, `-std=` and `-O` flags there instead of guessing.
- `ctest -V` shows the test output; `ctest --output-on-failure` shows it only for failures.
- `nm -C file.a | grep ' T '` lists defined functions; `nm -C demo | grep ' U '` lists the unresolved ones; `ldd demo` lists shared libraries.
- Delete the build directory and rebuild from scratch in CI to catch hidden dependence on stale files; compare Debug and Release test results.
- For the model: assert the topological-order property on random DAGs.

## Failure modes

| Mistake | Observed |
|---|---|
| Forgetting `target_link_libraries(demo PRIVATE robotmath)` | `fatal error: robotmath/vec2.hpp: No such file or directory` (include propagation lost) or `undefined reference` |
| Library listed in the wrong order on a hand-written link line | `undefined reference` although the library exists |
| Function defined in a header without `inline` | `multiple definition of ...` at link |
| `file(GLOB)` and a new file | `undefined reference` until `cmake` is re-run |
| Global `include_directories(/abs/path)` | works on one machine only; leaks to all targets |
| `assert`-based tests in Release (`-DNDEBUG`) | broken code reported as passing |
| Editing a header but compiling with stale objects (no dependency scanning in a hand-written Makefile) | old behavior persists; mysterious crashes (ABI mismatch) |
| Circular library dependency | CMake: "dependency cycle" or linker errors; redesign the layering |
| Sanitizer flags on compile but not on link | `undefined reference to __asan_*` |

## Alternatives and trade-offs

- **CMake vs hand-written Make.** Make is transparent and fine for a handful of files; CMake handles portability, package discovery (`find_package`), IDE integration and install rules, at the cost of a second language.
- **Make vs Ninja generators.** Ninja (`-G Ninja`) is faster for incremental builds of large trees; Make generators are everywhere. The CMake description is the same.
- **Static vs shared libraries.** Static libraries produce one self-contained binary and let the linker drop unused code; shared libraries save disk and memory and can be updated separately but create run-time lookup and ABI issues (see CPP12). Set per target or with `BUILD_SHARED_LIBS`.
- **Many small targets vs one big one.** Fine-grained targets give precise rebuilds and enforce layering; too many make configuration slow and the graph hard to read.
- **Header-only libraries (`INTERFACE`).** No link step and easy to distribute, but every user recompiles the code; heavy templates inflate build times.
- **Other systems.** Bazel (hermetic, remote caching), Meson (simple syntax), `colcon`/`ament_cmake` for ROS 2, and Conan/vcpkg for dependencies. The ideas (targets, graph, usage requirements) carry over.

## Transfer and retention

`colcon build` is `cmake` for each package in dependency order, driven by the same graph logic you implemented. Python packaging (`pyproject.toml` build back ends), Docker layer caching (a layer is rebuilt when its inputs change) and `make`-style data pipelines (DVC, Snakemake) all use "rebuild what is downstream of a change". To retain: write the CMake lines for a library with one public and one private dependency from memory after a few days, and describe what each keyword does. When you meet any build error, first name the stage.

## Exercise answers

1. (a) preprocess: the include directory is not on this target's include path; fix with `target_include_directories` or link the library that exports it. (b) compile: missing `#include`/forward declaration or wrong namespace. (c) link: the definition is not in any linked object or library; add the source file or `target_link_libraries`. (d) link: a non-inline function is defined in a header included twice; make it `inline`.
2. After touching `types.hpp`: $25\times3=75$ s; after touching one `.cpp`: $3$ s. Reduce with forward declarations, splitting the header, the pimpl idiom, precompiled headers, or a compiler cache (`ccache`).
3. A change in `plan.hpp` makes `main.o` stale (it includes `plan.hpp`), hence `app`: order `main.o`, then `app` (in the lab graph `plan.hpp` is only a prerequisite of `main.o`). `libplan` is not rebuilt in that graph. In the model, `rebuild_set(deps, {"plan.hpp"})` returns `["plan.hpp", "main.o", "app"]`.
4. Problems: no `target_link_libraries(demo PRIVATE robotmath)`, so `demo` is compiled using the global include directory but never linked against the library: `undefined reference`; the absolute path is machine-specific; `include_directories` is global and applies to all targets. Fix: `add_library(robotmath src/vec2.cpp)`, `target_include_directories(robotmath PUBLIC include)`, `add_executable(demo src/main.cpp)`, `target_link_libraries(demo PRIVATE robotmath)`.
5. `util`: PUBLIC, because `sensors.hpp` (included by `driver`) includes `util/units.hpp`; PRIVATE would make `driver` fail with `fatal error: util/units.hpp: No such file or directory`. `yaml`: PRIVATE, because only `sensors.cpp` uses it; making it PUBLIC would leak the dependency and its include path to every user of `sensors` and force them to find it.
6. `file(GLOB)` is evaluated when CMake configures, so the generated build does not list `filter.cpp`; the build then compiles everything it knows but `Filter::update` is never compiled and linking fails. Fixes: re-run `cmake` (or touch `CMakeLists.txt`); list sources explicitly (recommended); or use `file(GLOB ... CONFIGURE_DEPENDS ...)`, which re-checks at build time at some cost.
7. In Release, `-DNDEBUG` turns `assert(...)` into nothing, so the wrong code is never checked and the test returns success. Use a test macro that does not depend on `NDEBUG` (a `CHECK` that prints and returns `EXIT_FAILURE`, as in the lab), or a framework such as GoogleTest/Catch2.
8. `main.o -lA -lB` links: after scanning `libA.a`, `b_fn` is undefined and `libB.a` is scanned next. `main.o -lB -lA` fails because `libB.a` is scanned when nothing needs it and `libA.a`'s later need is never satisfied. In CMake: `target_link_libraries(A PUBLIC B)` or `PRIVATE B`, and `target_link_libraries(main PRIVATE A)`; the link line is ordered automatically. With `PRIVATE`, B's include directories do not propagate to `main`, so if `main` uses a B header it needs its own `target_link_libraries(main PRIVATE B)`; with `PUBLIC`, `main` inherits B's include directories (and B on its link line).
9. Stage: link. `multiple definition of 'twice(int)'; ... first defined here`, because each translation unit has its own definition. Fixes: (1) `inline int twice(int x)` (idiomatic, definition stays in the header, the linker merges copies); (2) `static int twice(int)`, each file gets a private copy (wastes space, can duplicate state); (3) declare in the header and define in one `.cpp` (cleanest for non-trivial code, but prevents cross-file inlining without LTO).
10. `core`: `add_library(core ...)`, `target_include_directories(core PUBLIC include)`. `planning`: `target_link_libraries(planning PUBLIC core)` (its headers use core types) and `PRIVATE Eigen3::Eigen`. `drivers`: `PRIVATE core`. `planner_node`: `PRIVATE planning`; `driver_node`: `PRIVATE drivers`; tests: `test_core -> core`, `test_planning -> planning`, `test_drivers -> drivers`. A change to `core/types.hpp` rebuilds the objects of `core`, `planning`, `drivers` and the nodes and tests that include it: all 3 libraries, 2 applications and 3 tests are affected (8 targets), the worst case. A cycle would have no valid build order: A needs B built first and B needs A built first.
11. A good answer: (a) `vec2.cpp`: 1 compile, archive, relink `demo`, `test_vec2` and the `robotplan` test; (b) `vec2.hpp`: every object that includes it, including `robotplan.cpp`; (c) `robotplan.cpp`: 1 compile, archive and relink of its own test, not `demo`. The `compile_commands.json` line shows `-I` flags inherited through `PUBLIC`; the ASAN build is in its own directory so the two configurations do not mix.

## Further reading

- [CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/index.html) - step-by-step guide: libraries, usage requirements, testing and installing.
- [cmake-buildsystem(7)](https://cmake.org/cmake/help/latest/manual/cmake-buildsystem.7.html) - the precise semantics of targets, PUBLIC/PRIVATE/INTERFACE and transitive usage requirements.
- [GNU Make Manual](https://www.gnu.org/software/make/manual/make.html) - rules, prerequisites and how rebuilds are decided.

**More practice:** work through the later steps of the [CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/index.html) (each step ends with a build-and-run exercise), and the [CTest manual](https://cmake.org/cmake/help/latest/manual/ctest.1.html) for test options.
