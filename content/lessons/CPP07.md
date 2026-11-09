---
{
  "id": "cpp07-foundations",
  "module_id": "CPP07",
  "title": "Build systems: CMake, linking, and targets",
  "summary": "Understand compile and link stages, describe a project as targets with usage requirements in CMake, and test it out of source.",
  "estimated_minutes": 405,
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
    },
    {
      "title": "GNU ld: command-line options",
      "url": "https://sourceware.org/binutils/docs/ld/Options.html"
    },
    {
      "title": "CMake: target_link_libraries",
      "url": "https://cmake.org/cmake/help/latest/command/target_link_libraries.html"
    },
    {
      "title": "CMake: generator expressions",
      "url": "https://cmake.org/cmake/help/latest/manual/cmake-generator-expressions.7.html"
    },
    {
      "title": "The Ninja build system manual",
      "url": "https://ninja-build.org/manual.html"
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

Picture building a house from prefabricated rooms. Compiling is making each room in a workshop; it only needs the floor plan of its neighbours (the headers), not the neighbours themselves. Linking is the day the rooms are delivered and bolted together; that is the first time anyone finds out that a door was drawn on one plan but never built in any room. This is why "undefined reference" is a link-time message and "No such file" a compile-time one: they are different people looking at different documents.

A robot-software example: the `planner` library uses `Vec2` from `core` in its public header, and also uses a YAML parser inside one `.cpp` file. Anybody who includes `planner.hpp` must be able to find `core`'s headers, but nobody should need to know YAML exists. `PUBLIC` and `PRIVATE` are the way to write down exactly that sentence, so the build tells every other target the right amount and no more.

**Predict before you compute.** Touch one `.cpp` file in a project of 40 sources and predict how many compiler processes will run; then touch a header that 25 of them include and predict again. A good prediction is 1 and 25, plus one archive or link step each time. If your prediction after touching the `.cpp` is "everything", your mental model treats the build as a script that always runs from the top, instead of a graph in which only the stale nodes run.

**The common wrong intuition** is that the order of libraries on a link line is a style choice and that CMake "just links things". For static archives the order is semantics: the linker scans each archive once, in the order given, and forgets it. `target_link_libraries` works because it records a graph and CMake derives a valid order (and repeats cyclic components) for you. The same wrong intuition shows up with headers: "it compiled on my machine" often means a global `include_directories` or an absolute path made it work there and nowhere else.

![The four stages preprocess, compile, archive and link, with what each reads and the typical error message of each](/lesson-figures/CPP07.svg)

*Figure: the compiler sees only declarations, so a missing definition surfaces first in the link stage; a missing header surfaces in the very first stage. Naming the stage narrows the cause before any file is opened.*

## Theory and derivation

### Errors by stage

| Message | Stage | Typical cause |
|---|---|---|
| `fatal error: robotmath/vec2.hpp: No such file or directory` | preprocess | include directory not given to this target |
| `error: 'foo' was not declared in this scope` | compile | missing `#include`, typo, wrong namespace |
| `undefined reference to 'robotmath::rotate(...)'` | link | declaration exists but definition's object or library is not linked |
| `multiple definition of 'twice(int)'` | link | non-inline function defined in a header included by two `.cpp` files |

Declarations may repeat; a definition must exist exactly once in the program (the one-definition rule, ODR). Header functions that are defined in the header must be `inline` (or templates, or `constexpr`).

**Example.** A flight-controller driver is split into `imu/filter.hpp` (declares `double lowpass(double prev, double sample, double alpha);`) and small test programs that each break exactly one stage: `a_pre.cpp` includes `imu/filtr.hpp` (typo in the file name), `b_comp.cpp` calls `lowpas(0.0, 1.0, 0.5)`, `c_link.cpp` calls `lowpass(...)` with the header correct but no definition linked, and `d1.cpp` and `d2.cpp` both include `gain.hpp`, which defines `gain()`. Which stage (preprocess, compile, link) reports each failure, and what does each message look like?

**Solution.** The first program stops in the preprocessor (`No such file or directory`), the second in the compiler (`not declared in this scope`, with a hint at `lowpass`), the third and fourth in the linker. The third program compiles cleanly: the declaration in the header is all the compiler needs. Only the linker asks "where is the body?" and answers `undefined reference`. The fourth fails the other way round: two objects each carry a copy of `gain()`, hence `multiple definition`. Reading the stage first (preprocess, compile, link) names the cause before any file is opened. Real output of `g++ 11.4` (the column numbers depend on how the test file is laid out):

```
$ g++ -std=c++20 -Wall -Wextra -I. -c a_pre.cpp      # #include "imu/filtr.hpp"  (typo in the file name)
a_pre.cpp:1:10: fatal error: imu/filtr.hpp: No such file or directory
$ g++ -std=c++20 -Wall -Wextra -I. -c b_comp.cpp     # calls lowpas(0.0, 1.0, 0.5)
b_comp.cpp:2:21: error: ‘lowpas’ was not declared in this scope; did you mean ‘lowpass’?
$ g++ -std=c++20 -Wall -Wextra -I. -c c_link.cpp     # calls lowpass(...), declared in imu/filter.hpp
$ g++ c_link.o -o c_link
c_link.cpp:(.text+0x2d): undefined reference to `lowpass(double, double, double)'
$ g++ d1.o d2.o -o d                                 # gain.hpp defines gain(); d1.cpp and d2.cpp include it
d2.cpp:(.text+0x0): multiple definition of `gain()'; d1.o:d1.cpp:(.text+0x0): first defined here
```

### Make-style rebuild rules

A rule has the form `target: prerequisites` and a recipe. The target is rebuilt when any prerequisite is newer (or missing). Compilers can write the true header dependencies (`-MMD`), which CMake's generated builds use automatically. Consequence: changing one `.cpp` recompiles one object and relinks; changing a widely included header recompiles every object that includes it. If $k$ of $N$ objects include a header, the cost of touching it is $k$ compiles plus the links; the cost of touching a `.cpp` is 1 compile plus the links. This is why headers should include as little as possible.

**Example.** A controller project has $N=6$ sources; three of them (`pid_a.cpp`, `pid_b.cpp`, `pid_c.cpp`) include `pid.hpp`. A hand-written Makefile with `-MMD` (so the compiler records the header dependencies) is run after `touch pid_b.cpp`, then after `touch pid.hpp`, then once more. How many compiles does each step cost, and what does the last `make` do? At 2 s per compile, how long are the first two rebuilds, link excluded?

**Solution.** Touching one `.cpp` costs 1 compile plus the link; touching the header costs $k=3$ compiles (every file that includes it) plus the link, and a second `make` does nothing because every timestamp is up to date. At 2 s per compile that is $1\cdot2=2$ s against $k\cdot2=6$ s, plus the link each time. The session is:

```
$ make                       # 6 sources; pid_a.cpp, pid_b.cpp, pid_c.cpp include pid.hpp
$ touch pid_b.cpp && make
g++ -std=c++20 -c pid_b.cpp -o pid_b.o
g++ main.o pid_a.o pid_b.o pid_c.o log_a.o log_b.o -o app
$ touch pid.hpp && make
g++ -std=c++20 -c pid_a.cpp -o pid_a.o
g++ -std=c++20 -c pid_b.cpp -o pid_b.o
g++ -std=c++20 -c pid_c.cpp -o pid_c.o
g++ main.o pid_a.o pid_b.o pid_c.o log_a.o log_b.o -o app
$ make
make: 'app' is up to date.
```

Playing with $N$, $k$, the compile time and the number of parallel jobs shows how fast the header cost grows (wall-clock time of the $k$ recompiles packed onto $j$ jobs is $\lceil k/j\rceil\,t$, the CPU time is $k\,t$):

```explore
{
  "title": "Touching a header: how much rebuilds?",
  "title_vi": "Chạm vào một header: build lại bao nhiêu?",
  "prompt": "Predict first: with the defaults, does doubling the number of parallel jobs halve the wall-clock time of a header change? Then check with the sliders, and find the value of k at which the wall-clock time jumps.",
  "prompt_vi": "Dự đoán trước: với giá trị mặc định, tăng gấp đôi số job song song có làm thời gian thực giảm một nửa khi đổi một header không? Sau đó kiểm tra bằng thanh trượt, và tìm giá trị k mà tại đó thời gian thực nhảy bậc.",
  "params": [
    { "name": "n", "label": "sources in the project N", "label_vi": "số source của dự án N", "min": 10, "max": 100, "step": 1, "value": 60, "unit": "" },
    { "name": "kh", "label": "sources that include the header k", "label_vi": "số source include header k", "min": 1, "max": 100, "step": 1, "value": 18, "unit": "" },
    { "name": "t", "label": "compile time per source", "label_vi": "thời gian compile mỗi source", "min": 0.5, "max": 10, "step": 0.5, "value": 2, "unit": "s" },
    { "name": "j", "label": "parallel jobs", "label_vi": "số job song song", "min": 1, "max": 16, "step": 1, "value": 4, "unit": "" },
    { "name": "lk", "label": "link time", "label_vi": "thời gian link", "min": 0, "max": 10, "step": 0.5, "value": 3, "unit": "s" }
  ],
  "let": [
    { "name": "kk", "expr": "min(kh, n)" },
    { "name": "wall", "expr": "ceil(kk/j)*t + lk" },
    { "name": "cpu", "expr": "kk*t + lk" }
  ],
  "plot": {
    "x": { "name": "m", "min": 0, "max": 100, "label": "sources recompiled m", "label_vi": "số source phải compile lại m" },
    "y": { "label": "time (s)", "label_vi": "thời gian (s)", "min": 0 },
    "series": [
      { "expr": "ceil(min(m, n)/j)*t + lk", "label": "wall-clock time", "label_vi": "thời gian thực", "color": "blue" },
      { "expr": "min(m, n)*t + lk", "label": "CPU time", "label_vi": "thời gian CPU", "color": "orange" }
    ],
    "points": [
      { "x": "kk", "y": "wall", "label": "your header", "label_vi": "header của bạn", "color": "green" }
    ]
  },
  "readouts": [
    { "label": "compiles after touching a .cpp", "label_vi": "số compile khi chạm một .cpp", "expr": "1", "unit": "", "digits": 0 },
    { "label": "compiles after touching the header", "label_vi": "số compile khi chạm header", "expr": "kk", "unit": "", "digits": 0 },
    { "label": "wall-clock time", "label_vi": "thời gian thực", "expr": "wall", "unit": "s", "digits": 1 },
    { "label": "CPU time", "label_vi": "thời gian CPU", "expr": "cpu", "unit": "s", "digits": 1 }
  ]
}
```

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

**Example.** A wheel-odometry module: `odom` converts encoder ticks to distance, $d = 2\pi r\,\text{ticks}/\text{ticks\_per\_rev}$. `drive` prints the distance for 1440 ticks at 360 ticks per revolution on a wheel of radius 0.05 m, and `test_wheel` is registered as a test. What are the CMake lines needed (only those of this section), what does the build print, and why does `main.cpp` need no include line of its own for `odom`?

```cmake
add_library(odom src/wheel.cpp)
target_include_directories(odom PUBLIC include)
add_executable(drive src/main.cpp)
target_link_libraries(drive PRIVATE odom)
enable_testing()
add_executable(test_wheel tests/test_wheel.cpp)
target_link_libraries(test_wheel PRIVATE odom)
add_test(NAME wheel COMMAND test_wheel)
```

**Solution.** The CMake description needs only the lines of the block above, and the target names carry everything else: `odom` is a library with a public include directory, `drive` and `test_wheel` link it. 1440 ticks at 360 ticks per revolution is 4 revolutions of a wheel of radius 0.05 m, so $4\cdot 2\pi\cdot 0.05 = 1.2566$ m, as printed. `main.cpp` includes `odom/wheel.hpp` without any include line of its own: the `PUBLIC include` of `odom` reached `drive` and `test_wheel` through `target_link_libraries`. The configure, build, test and run steps print:

```
$ cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build
[ 16%] Building CXX object CMakeFiles/odom.dir/src/wheel.cpp.o
[ 33%] Linking CXX static library libodom.a
[ 50%] Building CXX object CMakeFiles/drive.dir/src/main.cpp.o
[ 66%] Linking CXX executable drive
[ 83%] Building CXX object CMakeFiles/test_wheel.dir/tests/test_wheel.cpp.o
[100%] Linking CXX executable test_wheel
$ ctest --test-dir build
1/1 Test #1: wheel ............................   Passed    0.00 sec
100% tests passed, 0 tests failed out of 1
$ ./build/drive
1.25664 m
```

### Linking order and static libraries

A GNU linker processes archives left to right and extracts only the members needed to satisfy symbols that are *currently* undefined. If `main.o` needs `a_fn` from `libA.a` and `a_fn` needs `b_fn` from `libB.a`, then `g++ main.o -lA -lB` works, but `g++ main.o -lB -lA` fails with `undefined reference to b_fn()`: when `libB.a` was scanned nothing needed it yet. With CMake you never write this by hand: `target_link_libraries` records dependencies and orders the link line.

**Example.** A planner library `libplan.a` (`plan()` calls `costmap_at()`) and a map library `libmap.a` (defines `costmap_at()`); `main.o` calls `plan()`. Does the link succeed with `-lmap -lplan`, and with `-lplan -lmap`? Real run with gcc 11.4:

**Solution.** With `-lmap` first, `libmap.a` is scanned when nothing needs `costmap_at` yet and is dropped; `libplan.a` then creates the need and no archive is left, so the link fails. With `-lplan -lmap`, `libplan.a` supplies `plan` and creates the need for `costmap_at`, which `libmap.a` then satisfies, so the link succeeds and the program exits with 0. The message names `plan.c`, the object that needed the symbol, not the library that is missing from the line. The session is:

```
$ gcc -c main.c plan.c map.c && ar rcs libplan.a plan.o && ar rcs libmap.a map.o
$ gcc main.o -L. -lmap -lplan -o t1       # main needs plan(); plan() needs costmap_at()
./libplan.a(plan.o): in function `plan':
plan.c:(.text+0x9): undefined reference to `costmap_at'
$ gcc main.o -L. -lplan -lmap -o t2 && ./t2; echo "exit $?"
exit 0
```

### The dependency graph

Let the build graph be a directed acyclic graph (DAG). A valid build order is a topological order: every node after all of its prerequisites. The set to rebuild after changing node $c$ is $c$ together with all nodes reachable from $c$ along "is-used-by" edges. A cycle (library A links B, B links A) has no topological order and CMake/Make report it.

**Example.** A SLAM node: `scan.o` and `icp.o` both include `scan.hpp`, `libslam.a` archives them, `slam_node` links the library and `viz.o`. Using the few lines of Python below to compute the topological order and the rebuild set, which nodes are rebuilt when `scan.hpp` changes, and which when `viz.cpp` changes?

```python
from graphlib import TopologicalSorter
deps = {"scan.o": ["scan.cpp", "scan.hpp"], "icp.o": ["icp.cpp", "scan.hpp"], "viz.o": ["viz.cpp"],
        "libslam.a": ["scan.o", "icp.o"], "slam_node": ["libslam.a", "viz.o"]}
order = list(TopologicalSorter(deps).static_order())
def rebuild(changed):
    out = {changed}
    while True:
        more = {n for n, ds in deps.items() if n not in out and out & set(ds)}
        if not more: return [n for n in order if n in out]
        out |= more
print(rebuild("scan.hpp")); print(rebuild("viz.cpp"))
```

**Solution.** `rebuild(changed)` starts from the changed file and repeatedly adds every node that lists a node already in the set as a prerequisite, until nothing is added; the result is listed in topological order. Touching `scan.hpp` reaches 4 downstream nodes (two objects, the archive and the executable); touching `viz.cpp` reaches only `viz.o` and the executable. The first line of `order` is any valid order: `graphlib` guarantees only that prerequisites come first. The program prints:

```
['scan.hpp', 'scan.o', 'icp.o', 'libslam.a', 'slam_node']
['viz.cpp', 'viz.o', 'slam_node']
```

### Archive resolution as a fixed point

Model the linker's state as a set $U$ of currently undefined symbols. Object files named on the command line are always taken, and their undefined symbols are added to $U$. An archive (`libX.a`) is scanned *once*, at its position in the command line: every member that defines some symbol in $U$ is extracted, its own undefined symbols are added to $U$, and scanning of that archive continues until no remaining member defines a symbol in $U$. The archive is then never revisited. This is exactly why order matters (GNU ld manual, `--start-group`: "normally, an archive is searched only once in the order that it is specified").

A concrete case with two cross-referencing archives. `libA.a` has members `a1.o` (defines `fa1`, needs `fb1`) and `a2.o` (defines `fa2`); `libB.a` has `b1.o` (defines `fb1`, needs `fa2`); `main.o` needs `fa1`.

| command | scan trace | result |
|---|---|---|
| `main.o -lA -lB` | $U=\{fa1\}$; `a1.o` extracted, $U=\{fb1\}$; `libB`: `b1.o` extracted, $U=\{fa2\}$; no more archives | `undefined reference to fa2` |
| `main.o -lB -lA` | $U=\{fa1\}$; `libB` has nothing for $U$; `libA`: `a1.o`, $U=\{fb1\}$ | `undefined reference to fb1` |
| `main.o -lA -lB -lA` | as the first row, then `libA` again: `a2.o` defines `fa2` | links |
| `main.o --start-group -lA -lB --end-group` | the group is rescanned until $U$ stops changing | links |

Termination of a group: every extra pass that does not stop the process extracts at least one new member, and a member is extracted at most once, so a group of archives with $M$ members in total needs at most $M+1$ passes. The ld manual warns that this "has a significant performance cost" and recommends it only for unavoidable circular references. CMake does the same for mutually dependent static libraries: it repeats the whole strongly connected component, so `A <-> B` linked from `main` produces `A B A B` (CMake docs, `target_link_libraries`, "Cyclic Dependencies of Static Libraries"). Its advice: if two archives are that interdependent, merge them (for example as an object library).

**Example.** Three archives: `libX.a` = {`x1.o`: defines `f1`, needs `g1`; `x2.o`: defines `f2`}, `libY.a` = {`y1.o`: defines `g1`, needs `h1`}, `libZ.a` = {`z1.o`: defines `h1`, needs `f2`}; `main.o` needs `f1`. Applying the archive-resolution rule of this section, what is left undefined for `-lX -lY -lZ`, for `-lZ -lY -lX`, and for `-lX -lY -lZ -lX`? What does the linker say (gcc 11.4)?

**Solution.** Keep the set $U$ of undefined symbols, initially $U=\{f1\}$ from `main.o`; each archive is scanned once, left to right, and extracts the members that define a symbol of $U$. For `-lX -lY -lZ`: `libX` extracts `x1.o`, $U=\{g1\}$; `libY` extracts `y1.o`, $U=\{h1\}$; `libZ` extracts `z1.o`, $U=\{f2\}$; no archive is left, so `f2` stays undefined. In the order `-lZ -lY -lX` nothing matches until `libX`, which extracts `x1.o` and gives $U=\{g1\}$ and stops, so `g1` stays undefined. A fourth scan of `libX` (`-lX -lY -lZ -lX`) extracts `x2.o` for `f2` and ends with $U=\emptyset$. The chain $f1\to g1\to h1\to f2$ runs "backwards" through the archives, so the one line that works repeats `libX` at the end. The linker agrees:

```
$ gcc main.o -L. -lX -lY -lZ -o t
undefined reference to `f2'
$ gcc main.o -L. -lZ -lY -lX -o t
undefined reference to `g1'
$ gcc main.o -L. -lX -lY -lZ -lX -o t && echo linked
linked
```

The chain $f1\to g1\to h1\to f2$ runs "backwards" through the archives, so the one line that works repeats `libX` at the end.

### Transitive usage requirements, precisely

`target_link_libraries(A <scope> B)` writes the dependency into two places. `PRIVATE` puts `B` only in `A`'s own `LINK_LIBRARIES`; `INTERFACE` puts it only in `INTERFACE_LINK_LIBRARIES`; `PUBLIC` puts it in both (CMake docs, `target_link_libraries`, "Libraries for a Target and/or its Dependents"). A consumer `main` of `A` inherits `A`'s `INTERFACE_INCLUDE_DIRECTORIES`, `INTERFACE_COMPILE_DEFINITIONS`, and so on, and recursively those of everything in `A`'s `INTERFACE_LINK_LIBRARIES`.

Static libraries need one exception. If `A` is static and links `B` `PRIVATE`, the final executable still needs `B`'s object code, because `libA.a` contains unresolved references into `B`. CMake therefore records the private dependency in the interface as `$<LINK_ONLY:B>`, which means "link `B`, but do not propagate its include directories, definitions or options" (CMake docs, generator expressions, `$<LINK_ONLY:...>`). Checked with CMake 3.22: for a static `A` with `PRIVATE B`, `INTERFACE_LINK_LIBRARIES` of `A` was `$<LINK_ONLY:B>`; the link line of `main` contained `libA.a libB.a` but its compile flags did not contain `B`'s include directory. For a shared `A` the property was empty, because the shared library already resolved `B` at its own link.

![Table-diagram: for a static library A that links B, the three scopes and whether A, and main, see B's include directory and link B](/lesson-figures/CPP07-2.svg)

*Figure: the scope written in `target_link_libraries(A <scope> B)` decides who sees B's include directory; for a static A, B is linked into `main` in all three cases.*

**Example.** A sensor-fusion library `fusion` (static) uses a matrix library `matlib` only inside `fusion.c`, and `slam` links `fusion` (CMake lines below). What are the `LINK_LIBRARIES` and `INTERFACE_LINK_LIBRARIES` of `fusion`, and does the compile line of `slam.c` contain `-Imatinc`? What does the link line of `slam` contain? CMake 3.22:

```cmake
add_library(matlib STATIC mat.c)
target_include_directories(matlib PUBLIC matinc)
add_library(fusion STATIC fusion.c)
target_include_directories(fusion PUBLIC fusioninc)
target_link_libraries(fusion PRIVATE matlib)
add_executable(slam slam.c)
target_link_libraries(slam PRIVATE fusion)
```

**Solution.** `fusion` keeps `matlib` in its own `LINK_LIBRARIES`, and publishes it to consumers only as `$<LINK_ONLY:matlib>`. Hence `libmatlib.a` is on the link line of `slam` while `-Imatinc` is absent from its compile line (only `-Ifusioninc` is there): the private dependency is linked but not compiled against. CMake reports the two properties and the generated lines:

```
-- fusion LINK_LIBRARIES           = matlib
-- fusion INTERFACE_LINK_LIBRARIES = $<LINK_ONLY:matlib>
compile line of slam.c:  cc -Ifusioninc -o CMakeFiles/slam.dir/slam.c.o -c slam.c
link line of slam:       cc CMakeFiles/slam.dir/slam.c.o -o slam  libfusion.a libmatlib.a
```

### Exporting a target: BUILD_INTERFACE and INSTALL_INTERFACE

A usage requirement such as `target_include_directories(core PUBLIC /abs/path/include)` is valid while building inside the same tree, but if `core` is installed and exported the path would be baked into a file used on a different machine. CMake therefore rejects an absolute path inside the source or build directory in `INTERFACE_INCLUDE_DIRECTORIES` of an exported target. The fix separates the two worlds: `$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>` is used when consuming from the same build system, and `$<INSTALL_INTERFACE:include>` (a path relative to the install prefix) is used after installation (CMake docs, cmake-buildsystem(7), "Include Directories and Usage Requirements" and "Build Specification and Usage Requirements").

**Example.** A transform library `tf` is exported with `install(TARGETS tf EXPORT tfTargets ...)` and `install(EXPORT tfTargets ...)`. What does CMake 3.22 do when the include directory is given as `${CMAKE_CURRENT_SOURCE_DIR}/include`, and what with `$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>` plus `$<INSTALL_INTERFACE:include>`?

**Solution.** With the absolute source path in the usage requirement CMake stops at generate time; with the two generator expressions it passes. The failed path would have been baked into the exported file and be wrong on any other machine, whereas `include` after `INSTALL_INTERFACE` is read relative to the install prefix. The two runs print:

```
$ cmake -S . -B build        # target_include_directories(tf PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
CMake Error in CMakeLists.txt:
  Target "tf" INTERFACE_INCLUDE_DIRECTORIES property contains path:
    "<scratch>/include"
  which is prefixed in the source directory.
CMake Generate step failed.  Build files cannot be regenerated correctly.
$ cmake -S . -B build        # $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include> $<INSTALL_INTERFACE:include>
-- Generating done
```

### Library kinds and the cost model: static, shared, object, interface

`add_library` creates one of several kinds of target, and the kind decides what the build produces and when its code is compiled (CMake docs, cmake-buildsystem(7), "Binary Targets", "Object Libraries" and "Interface Libraries"). A **static** library is an archive of object files; the final link copies the needed members into every executable that uses it. A **shared** library is linked once and resolved again when the program loads, so the executable contains a reference rather than the code. An **object** library is a collection of object files "created by compiling source files without any archiving or linking"; other targets reuse those objects through `$<TARGET_OBJECTS:name>` or by linking the object library. An **interface** library compiles nothing and produces no file: it only carries usage requirements, which makes it the right kind for header-only code.

The practical consequence is a cost model. A source file listed in $k$ different targets is compiled $k$ times, once per target, because each target has its own object directory. Verified with CMake 3.22: two executables each listing `f.cpp` triggered 4 compile steps in total (two for `main` files, two for `f.cpp`), while putting `f.cpp` in an `OBJECT` library linked by both triggered 3. For a project in which a library is also compiled into its test executable, an object library (or linking the test against the library) avoids compiling twice. Linking against a static library instead of listing sources has the extra benefit that its usage requirements travel with it.

Which kind should a module choose? A rule of thumb that follows from the definitions: use a static library as the default for code owned by the project (simple deployment, the link line is deterministic); use a shared library when several executables must share one copy of the code or when the code must be replaced without relinking the application; use an object library to compile once and then archive or link the same objects into several different targets; use an interface library for header-only code and for bundles of flags that many targets should inherit. Two limits to remember: object libraries cannot be the `TARGET` of `add_custom_command(TARGET)`, and interface libraries accept only the `INTERFACE` form of `target_include_directories`, `target_compile_definitions` and friends.

**Example.** Two executables `m1` and `m2` need the same `f.c`. How many `Building C object` lines does CMake 3.22 (Makefile generator) print when `f.c` is listed in both executables, and when it is built once as an object library used through `$<TARGET_OBJECTS:fobj>`?

**Solution.** Listing `f.c` in both executables compiles it twice (2 `main` files plus 2 copies of `f.c` = 4); an object library compiles it once (2 `main` files plus 1 copy = 3). The saving is one compile here; for a 5-minute translation unit shared by ten tools it is nine compiles. The two builds give:

```
$ cmake -S . -B b -DMODE=listed      # add_executable(m1 m1.c f.c) and add_executable(m2 m2.c f.c)
$ cmake --build b | grep -c 'Building C object'
4
$ cmake -S . -B b -DMODE=object      # add_library(fobj OBJECT f.c); m1, m2 use $<TARGET_OBJECTS:fobj>
$ cmake --build b | grep -c 'Building C object'
3
```

## Worked example

### Case 1: configure, build, test, rebuild

**Problem.** The project of the reference implementation has a library `robotmath` (`src/vec2.cpp`, public header `include/robotmath/vec2.hpp`), an executable `demo` (`src/main.cpp`) and a test executable `test_vec2` (`tests/test_vec2.cpp`). Configure it out of source in Release mode, build it, run the test, and then predict and check how many compile, archive and link steps run after touching (a) `src/main.cpp`, (b) `src/vec2.cpp`, (c) `include/robotmath/vec2.hpp`.

**Solution.**

1. *Write the graph* (theory, "The dependency graph"). Edges point from a prerequisite to what it feeds: `vec2.cpp`, `vec2.hpp` $\to$ `vec2.o`; `main.cpp`, `vec2.hpp` $\to$ `main.o`; `test_vec2.cpp`, `vec2.hpp` $\to$ `test_vec2.o`; `vec2.o` $\to$ `librobotmath.a`; `main.o`, `librobotmath.a` $\to$ `demo`; `test_vec2.o`, `librobotmath.a` $\to$ `test_vec2`. Every `.o` includes the header, which is the whole point of step 5.
2. *Configure*: `cmake -S proj -B build -DCMAKE_BUILD_TYPE=Release` reads `CMakeLists.txt`, finds the compiler and generates Makefiles in `build/`. Nothing is compiled yet.
3. *Build*: `cmake --build build`. A first build runs every non-source node once: 3 objects (compile), 1 archive, 2 executables (link), 6 steps. The log shows exactly that: `Building CXX object` for `vec2.cpp`, `main.cpp`, `test_vec2.cpp`; `Linking CXX static library librobotmath.a`; `Linking CXX executable demo` and `test_vec2` (progress 16% to 100%).
4. *Test*: `ctest --test-dir build --output-on-failure` prints `100% tests passed, 0 tests failed out of 1`.
5. *Predict the rebuild sets*: the set to rebuild after changing a node is that node plus everything reachable from it. (a) `main.cpp` reaches `main.o` and `demo`: 1 compile, 1 link. (b) `vec2.cpp` reaches `vec2.o`, `librobotmath.a`, `demo`, `test_vec2`: 1 compile, 1 archive, 2 links. (c) `vec2.hpp` reaches all three objects, the archive and both executables: 3 compiles, 1 archive, 2 links.
6. *Run and compare*: after `touch` and `cmake --build build` the log shows (a) 1 `Building CXX object` and 1 `Linking CXX executable`; (b) 1 `Building`, 1 `Linking CXX static library` and 2 `Linking CXX executable`; (c) 3 `Building`, 1 archive, 2 executables. These are the predictions.
7. *Include propagation* (theory, "CMake essentials"): `demo` never mentions `include/`, yet `#include "robotmath/vec2.hpp"` works, because `target_include_directories(robotmath PUBLIC include)` is inherited by anything linking `robotmath`. Removing the `target_link_libraries(demo ...)` line makes `demo` fail in the preprocessing stage with `fatal error: robotmath/vec2.hpp: No such file or directory`.
8. *Symbols*: `nm -C build/librobotmath.a | grep ' T '` lists `robotmath::norm`, `robotmath::rotate` and `robotmath::operator+` as defined (`T`) in the archive.

![Stacked bars of compile, archive and link steps run after touching main.cpp (2 steps), vec2.cpp (4 steps) and vec2.hpp (6 steps)](/lesson-figures/CPP07-3.svg)

*Figure: the measured steps of Case 1; the header touch costs three times the `.cpp` touch because three objects include it.*

**Check.** The number of steps after a touch equals the size of the reachable set minus the touched source: $2$, $4$ and $6$ steps for (a), (b), (c), as in the figure. A limiting case: a second `cmake --build build` with no change runs 0 steps ("up to date").

**Takeaway.** A header included by $k$ objects costs $k$ compiles, a private `.cpp` costs one: the build is a graph, and only the nodes reachable from the change run.

### Case 2: a link failure traced from first principles

**Problem.** Four C files: `main.c` calls `fa1`; `a1.c` defines `fa1`, which calls `fb1`; `a2.c` defines `fa2`; `b1.c` defines `fb1`, which calls `fa2`. Archive `libA.a` from `a1.o a2.o` and `libB.a` from `b1.o`. Predict which of `main.o -lA -lB`, `main.o -lB -lA`, `main.o -lA -lB -lA` links, using the rule of "Archive resolution as a fixed point", then check with gcc 11.4 and binutils 2.47.

**Solution.**

1. *Rule*: keep the set $U$ of undefined symbols. Start with $U=\{fa1\}$ from `main.o`. Each archive is scanned once, at its position; it contributes every member that defines a symbol in $U$, and the member's own undefined symbols enter $U$.
2. *`-lA -lB`*: `libA.a` defines `fa1`, so `a1.o` is extracted and $U=\{fb1\}$. `a2.o` defines `fa2`, which is not in $U$ yet, so it stays in the archive. `libB.a`: `b1.o` defines `fb1`, so it is extracted and $U=\{fa2\}$. No archive remains: `fa2` is undefined. Observed: `b1.c:(.text+0x9): undefined reference to 'fa2'`.
3. *`-lB -lA`*: $U=\{fa1\}$ and `libB.a` defines nothing in it, so it is skipped. `libA.a` extracts `a1.o`, $U=\{fb1\}$, and nothing remains. Observed: `a1.c:(.text+0x9): undefined reference to 'fb1'`.
4. *`-lA -lB -lA`*: as in step 2 until $U=\{fa2\}$; the second scan of `libA.a` finds `a2.o` defining `fa2`, so $U=\emptyset$ and the link succeeds. The group form `-Wl,--start-group -lA -lB -Wl,--end-group` also links, at the price of repeated scanning.
5. *In CMake* the fix is a dependency, not an order: `target_link_libraries(A PRIVATE B)` and `target_link_libraries(B PRIVATE A)` make a cyclic static component, and the executable that links `A` gets `A B A B` (CMake docs, `target_link_libraries`, "Cyclic Dependencies of Static Libraries"). The better design removes the cycle by merging `A` and `B`, or by moving `fa2` into a library that does not depend on `A`.

![Trace of the set U for three link lines over libA.a and libB.a](/lesson-figures/CPP07-4.svg)

*Figure: the set $U$ after every scan; the first two lines end with an undefined symbol, the third with $U=\emptyset$.*

**Check.** `nm libA.a libB.a` confirms the model: `a1.o` has `T fa1` and `U fb1`, `a2.o` has `T fa2`, `b1.o` has `T fb1` and `U fa2`. The three real link commands give the outcomes of steps 2, 3 and 4: two failures and one success.

**Takeaway.** The error is reported against the last object that needed the symbol (`b1.c`, then `a1.c`), not against the missing library: read "undefined reference" as "no archive scanned after this point defined it".

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
12. **(Challenge)** Reproduce the table of the "Archive resolution as a fixed point" section for a different system: `libP.a` has `p1.o` (defines `fp1`, needs `fq1`) and `p2.o` (defines `fp2`, needs `fq2`); `libQ.a` has `q1.o` (defines `fq1`, needs `fp2`) and `q2.o` (defines `fq2`); `main.o` needs `fp1`. For each of `main.o -lP -lQ`, `main.o -lQ -lP`, `main.o -lP -lQ -lP` and `main.o -lP -lQ -lP -lQ`, trace $U$ and say whether it links. Then prove that a `--start-group` over archives with $M$ members in total needs at most $M+1$ scans, and say what CMake emits for `main -> P`, `P <-> Q`. (adapted from the GNU ld manual, option `--start-group`, and CMake docs, `target_link_libraries`, "Cyclic Dependencies of Static Libraries")
13. **(Challenge)** Static library `A` has `target_link_libraries(A PRIVATE B)` and `B` has `target_include_directories(B PUBLIC inc_b)`. The executable `m` links `A` `PRIVATE` and its `main.c` calls only `A`'s API. (a) Is `inc_b` on the compile line of `m`? (b) Is `libB.a` on the link line of `m`? (c) Explain what property of `A` makes (b) true although (a) is false, and what changes if `A` is a shared library instead. (d) `m.c` now needs a header from `inc_b`: give the minimal correct change and say which alternative would be wrong design. (source: CMake docs, `target_link_libraries`, "Libraries for a Target and/or its Dependents", and generator expressions, `$<LINK_ONLY:...>`)
14. **(Challenge)** A teammate writes `target_include_directories(core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)` and adds `install(TARGETS core EXPORT coreTargets)` followed by `install(EXPORT coreTargets DESTINATION lib/cmake/core)`. Predict what CMake reports at generate time and why. Rewrite the include line so that both an in-tree consumer and an installed consumer work, state what path each consumer receives, and say why this cannot be solved by "just use a relative path". (source: CMake docs, cmake-buildsystem(7), "Include Directories and Usage Requirements", and the `BUILD_INTERFACE`/`INSTALL_INTERFACE` generator expressions)
15. **(Challenge)** A project has 40 sources of 3 s each. A script `gen_config.py` creates `config.h` from `config.in`; 25 sources include `config.h`. The build tool is Ninja with 8 parallel jobs and the compile rule uses a depfile. (a) You touch `config.in` but the script rewrites `config.h` byte-for-byte unchanged. How many compiles run if the generating rule has no `restat`, and how many with `restat = 1`? Give wall-clock times under ideal packing. (b) Why should a target that merely needs `config.h` to exist before any compile starts use an order-only dependency (`||`) instead of an ordinary one, and what is the risk of that choice? (c) Suppose the script instead writes a new timestamp and a changed `config.h`: how many compiles now? (source: Ninja manual, rule variable `restat`, and "Order-only dependencies")

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

### Library track

Python's standard library already has the algorithm you wrote: `graphlib.TopologicalSorter` (3.9+). Cross-check your `topo_order` against it, then let the real build system confirm your `rebuild_set` model. Append this to your finished Python file and run it from the directory that contains `proj/` (the CMake part needs `cmake` and `make`; delete part 3 otherwise).

```python
import json, random, subprocess
from graphlib import CycleError, TopologicalSorter   # standard library, Python 3.9+

# 1. your topo_order against graphlib on 200 random DAGs: both must be valid orders
rng = random.Random(0)
for _ in range(200):
    n = rng.randint(1, 12)
    deps = {f"n{i}": [f"n{j}" for j in range(i) if rng.random() < 0.3] for i in range(n)}
    mine = topo_order(deps)
    ref = list(TopologicalSorter(deps).static_order())
    assert sorted(mine) == sorted(ref)
    pos = {x: i for i, x in enumerate(mine)}
    assert all(pos[d] < pos[x] for x, ds in deps.items() for d in ds)

# 2. cycle detection agrees with graphlib
try:
    TopologicalSorter({"a": ["b"], "b": ["a"]}).prepare()
    raise AssertionError
except CycleError:
    pass

# 3. let the REAL build system rebuild after a `touch` and compare its compile count with the model (needs cmake + make
#    and the proj/ project from the lab; skip this part otherwise). Run from the directory containing proj/.
import pathlib, time
subprocess.run(["cmake", "-S", "proj", "-B", "build"], check=True, capture_output=True)
subprocess.run(["cmake", "--build", "build"], check=True, capture_output=True)
graph = {"vec2.o": ["vec2.cpp", "vec2.hpp"], "main.o": ["main.cpp", "vec2.hpp"], "test.o": ["test_vec2.cpp", "vec2.hpp"],
         "librobotmath.a": ["vec2.o"], "demo": ["main.o", "librobotmath.a"], "test_vec2": ["test.o", "librobotmath.a"]}
real_path = {"vec2.hpp": "proj/include/robotmath/vec2.hpp", "vec2.cpp": "proj/src/vec2.cpp", "main.cpp": "proj/src/main.cpp"}
for changed in ("vec2.hpp", "vec2.cpp", "main.cpp"):
    time.sleep(1.1)
    pathlib.Path(real_path[changed]).touch()
    out = subprocess.run(["cmake", "--build", "build"], check=True, capture_output=True, text=True).stdout
    real_compiles = out.count("Building CXX")
    model = rebuild_set(graph, {changed})
    model_compiles = sum(1 for n in model if n.endswith(".o"))
    print(changed, "real compiles:", real_compiles, "model:", model_compiles)
    assert real_compiles == model_compiles
print("library track ok")
```

Expected: three lines such as `vec2.hpp real compiles: 3 model: 3`, `vec2.cpp ... 1 ... 1`, `main.cpp ... 1 ... 1`, then `library track ok`. The model counts only `.o` nodes, which is what the build prints as `Building CXX object`.

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
10. `core`: `add_library(core ...)`, `target_include_directories(core PUBLIC include)`. `planning`: `target_link_libraries(planning PUBLIC core)` (its headers use core types) and `PRIVATE Eigen3::Eigen`. `drivers`: `PRIVATE core`. `planner_node`: `PRIVATE planning`; `driver_node`: `PRIVATE drivers`; tests: `test_core -> core`, `test_planning -> planning`, `test_drivers -> drivers`. A change to `core/types.hpp` rebuilds the objects of `core`, `planning`, `drivers` and the nodes and tests that include it: all 3 libraries, 2 applications and 3 tests are affected (8 targets). Strictly, only targets whose sources include the header (directly or through a public header) recompile: `core`, `planning`, `drivers`, `planner_node`, `test_core`, `test_planning`; `driver_node` and `test_drivers` only relink, because `drivers` links `core` PRIVATE and its headers hide the types. A cycle would have no valid build order: A needs B built first and B needs A built first.
11. A good answer: (a) `vec2.cpp`: 1 compile, archive, relink `demo`, `test_vec2` and the `robotplan` test; (b) `vec2.hpp`: every object that includes it, including `robotplan.cpp`; (c) `robotplan.cpp`: 1 compile, archive and relink of its own test, not `demo`. The `compile_commands.json` line shows `-I` flags inherited through `PUBLIC`; the ASAN build is in its own directory so the two configurations do not mix.
12. Trace for `main.o -lP -lQ`: $U=\{fp1\}$; `libP`: `p1.o` extracted (defines `fp1`), $U=\{fq1\}$; `p2.o` defines only `fp2`, not in $U$, skipped. `libQ`: `q1.o` extracted, $U=\{fp2\}$ (`q2.o` not needed). Done with `fp2` undefined: **fails** (`undefined reference to fp2`). `main.o -lQ -lP`: $U=\{fp1\}$; `libQ` has nothing for $U$; `libP`: `p1.o`, $U=\{fq1\}$; fails (`fq1`). `main.o -lP -lQ -lP`: as the first, then second `libP` pass: `p2.o` defines `fp2`, extracted, $U=\{fq2\}$; no archive left: **fails** (`undefined reference to fq2`). `main.o -lP -lQ -lP -lQ`: the second `libQ` pass extracts `q2.o`, $U=\emptyset$: **links**. So this chain needs $P\,Q\,P\,Q$ although the dependency graph $p1\to q1\to p2\to q2$ alternates four times; so the two-archive pattern `A B A` does not generalise to "repeat once". Proof for the group bound: a pass over the group either extracts at least one member not extracted before, or extracts none and then $U$ does not change, so the linker stops. Each of the $M$ members is extracted at most once, so at most $M$ passes extract something, and one final pass extracts nothing: at most $M+1$ scans. For `P <-> Q` CMake repeats the strongly connected component, so `main -> P` links `P Q P Q` (as in the CMake documentation example for `A`, `B`), which happens to be enough here, but the documentation says pathological arrangements can need more and offers `LINK_INTERFACE_MULTIPLICITY` or merging the archives. (The earlier `A`/`B` table was reproduced with gcc and `ar`: `-lA -lB` and `-lB -lA` failed, `-lA -lB -lA` and the group linked.)
13. (a) No: `PRIVATE` keeps `B`'s usage requirements (including its include directory) away from `A`'s consumers. (b) Yes: the link line of `m` contained `libA.a libB.a`. (c) For a static `A`, CMake stores the private dependency in `A`'s `INTERFACE_LINK_LIBRARIES` as `$<LINK_ONLY:B>`: link `B`, but propagate none of its compile-time usage requirements, because `libA.a` still has unresolved references into `B` when `m` is linked. For a shared `A` the property is empty (checked with CMake 3.22), because `B` was already linked into the shared library. (d) Minimal correct change: `target_link_libraries(m PRIVATE B)` in `m`'s own CMake code, which states the real dependency of `m.c` on `B`'s header and gives it `inc_b`. The wrong design is to change `A` to `PUBLIC B` just to make the include path visible: every consumer of `A` would then depend on `B`, and the interface of `A` would leak an implementation detail.
14. At generate time CMake stops with an error that the target's `INTERFACE_INCLUDE_DIRECTORIES` property contains a path that is "prefixed in the source directory" (reproduced with CMake 3.22, "Generate step failed"). The exported file would contain an absolute path from the build machine, wrong on any other machine. Rewrite: `target_include_directories(core PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include> $<INSTALL_INTERFACE:include>)`. An in-tree consumer receives the absolute source path; an installed consumer receives a path under the install prefix, `<prefix>/include` (the equivalent `INCLUDES DESTINATION include` option is documented in cmake-buildsystem(7) as appending `${CMAKE_INSTALL_PREFIX}/include`; the rewritten line was checked to configure without error). A relative path cannot work because "relative to what?" differs: relative to the source tree for the build, relative to the install prefix afterwards. Absolute paths are valid only for one of the two cases.
15. (a) Without `restat`, Ninja considers `config.h` newer than the old objects (the script ran), so all 25 dependent sources recompile: $\lceil25/8\rceil=4$ rounds of 3 s each, about 12 s of wall-clock time (75 s of CPU time). With `restat = 1`, Ninja re-stats `config.h` after the command; its modification time did not change, so it is treated as not needing to be built and the reverse dependencies are removed from the pending list: 0 compiles, only the script itself runs. (b) An order-only dependency says "build this first, but changes to it alone do not rebuild the output". It is the right tool to make sure `config.h` exists before the first compile starts (the compile's real dependency on header contents comes from the depfile discovered by the compiler). The risk: if the order-only edge is the only link and no depfile records the include, a change to `config.h` never triggers recompilation. (c) A genuinely changed header gets a new modification time; `restat` cannot help, and all 25 compiles run again (about 12 s). (This is derived from the Ninja manual's definitions of `restat` and order-only dependencies; Ninja was not run, because it is not installed here.)

## Further reading

- [CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/index.html) - step-by-step guide: libraries, usage requirements, testing and installing.
- [cmake-buildsystem(7)](https://cmake.org/cmake/help/latest/manual/cmake-buildsystem.7.html) - the precise semantics of targets, PUBLIC/PRIVATE/INTERFACE and transitive usage requirements.
- [GNU Make Manual](https://www.gnu.org/software/make/manual/make.html) - rules, prerequisites and how rebuilds are decided.
- [GNU ld: command-line options](https://sourceware.org/binutils/docs/ld/Options.html) - `--start-group`, and how archives are searched.
- [`target_link_libraries`](https://cmake.org/cmake/help/latest/command/target_link_libraries.html) - link interface, PRIVATE/PUBLIC/INTERFACE, and cyclic static libraries.
- [cmake-generator-expressions(7)](https://cmake.org/cmake/help/latest/manual/cmake-generator-expressions.7.html) - `$<LINK_ONLY:...>`, `$<BUILD_INTERFACE:...>` and `$<INSTALL_INTERFACE:...>`.
- [The Ninja build system manual](https://ninja-build.org/manual.html) - `restat`, depfiles and order-only dependencies.

**More practice:** the [CMake Tutorial step "Adding a Library"](https://cmake.org/cmake/help/latest/guide/tutorial/Adding%20a%20Library.html) and the following steps (usage requirements, testing), the reference page for [`target_link_libraries`](https://cmake.org/cmake/help/latest/command/target_link_libraries.html) (PUBLIC/PRIVATE/INTERFACE semantics, then re-do exercise 10), the [`file(GLOB)`](https://cmake.org/cmake/help/latest/command/file.html) warning, the [CTest manual](https://cmake.org/cmake/help/latest/manual/ctest.1.html), and the [graphlib docs](https://docs.python.org/3/library/graphlib.html) for the build-order model.