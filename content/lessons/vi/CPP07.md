---
{"title": "Hệ thống build: CMake, linking và target", "summary": "Hiểu các giai đoạn compile và link, mô tả một dự án dưới dạng các target với usage requirement trong CMake, và kiểm thử ngoài cây source (out of source).", "objectives": ["Giải thích preprocessing, compiling, archiving và linking, và ánh xạ mỗi thông báo lỗi thường gặp về đúng giai đoạn.", "Viết CMakeLists.txt với một library, một application và một test executable bằng các lệnh target_*.", "Chọn PUBLIC, PRIVATE hoặc INTERFACE cho include directory và dependency link.", "Dự đoán những gì hệ thống build sẽ build lại sau một thay đổi ở source hoặc header."]}
---
## Vì sao điều này quan trọng

Một stack phần mềm robot gồm hàng chục library và executable: toán, driver, planning, perception, test. Gõ lệnh compiler bằng tay hết dùng được từ file thứ hai. Một hệ thống build ghi lại *cái gì phụ thuộc vào cái gì* và chỉ tính lại những gì đã thay đổi; nó cũng cho mọi lập trình viên và mọi máy continuous-integration cùng một bản build. ROS 2 build bằng `colcon`, vốn điều khiển CMake; Eigen, OpenCV, PCL và Gazebo đều đi kèm package CMake. Những vấn đề hằng ngày phổ biến nhất (một `undefined reference`, một header "không tìm thấy" ở target này nhưng không ở target kia, một test lặng lẽ chạy binary cũ) đều là vấn đề của hệ thống build, và chúng trở nên dễ khi bạn nói được giai đoạn nào của pipeline đã sinh ra thông báo.

## Trực giác

Biến source thành chương trình là một pipeline các bước nhỏ:

1. **Preprocess**: `#include` dán header vào, macro `#define` được khai triển. Output: một *translation unit* cho mỗi `.cpp`.
2. **Compile**: mỗi translation unit trở thành một *object file* (`.o`) chứa mã máy với các tham chiếu chưa được giải quyết tới các hàm định nghĩa ở nơi khác.
3. **Archive** (static library `.a`) hoặc link thành shared library (`.so`).
4. **Link**: linker nối các object file và library, giải quyết mỗi tham chiếu tới đúng một định nghĩa, và tạo ra executable.

Một hệ thống build là một *đồ thị*: mỗi output phụ thuộc vào các input của nó, và một output được build lại khi bất kỳ input nào mới hơn. Bản thân CMake không biên dịch gì cả. Nó *sinh ra* một bản build gốc (Makefile hoặc file Ninja) từ một mô tả gồm các **target**, và công cụ gốc thực thi nó. Một target (library hay executable) mang theo **usage requirement**: include directory, compile definition, và những gì nó link. Các requirement `PUBLIC` đi tới mọi thứ link target đó; các requirement `PRIVATE` ở lại bên trong.

![Pipeline từ source tới object tới library và executable, với đồ thị phụ thuộc cho thấy file nào được build lại khi một header thay đổi](/lesson-figures/CPP07.svg)

*Source biên dịch thành object, object được archive thành library, và executable link library; một header thay đổi sẽ kích hoạt mọi object phụ thuộc.*

## Lý thuyết và suy dẫn

### Lỗi theo giai đoạn

| Thông báo | Giai đoạn | Nguyên nhân điển hình |
|---|---|---|
| `fatal error: robotmath/vec2.hpp: No such file or directory` | preprocess | include directory chưa được cấp cho target này |
| `error: 'foo' was not declared in this scope` | compile | thiếu `#include`, gõ sai, sai namespace |
| `undefined reference to 'robotmath::rotate(...)'` | link | khai báo tồn tại nhưng object hoặc library chứa định nghĩa không được link |
| `multiple definition of 'twice(int)'` | link | hàm không inline được định nghĩa trong header được hai file `.cpp` include |

Khai báo có thể lặp lại; một định nghĩa phải tồn tại đúng một lần trong chương trình (one-definition rule, ODR). Các hàm định nghĩa trong header phải là `inline` (hoặc là template, hoặc `constexpr`).

### Quy tắc build lại kiểu Make

Một rule có dạng `target: prerequisites` và một recipe. Target được build lại khi bất kỳ prerequisite nào mới hơn (hoặc thiếu). Compiler có thể ghi ra các phụ thuộc header thật sự (`-MMD`), mà các bản build do CMake sinh ra dùng tự động. Hệ quả: đổi một `.cpp` biên dịch lại một object và link lại; đổi một header được include rộng rãi biên dịch lại mọi object include nó. Nếu $k$ trong $N$ object include một header, chi phí của việc động vào nó là $k$ lần compile cộng các lần link; chi phí động vào một `.cpp` là 1 lần compile cộng các lần link. Đó là lý do header nên include càng ít càng tốt.

### Những điều cốt yếu của CMake

```cmake
add_library(robotmath src/vec2.cpp)                      # a target
target_include_directories(robotmath PUBLIC include)     # usage requirement
add_executable(demo src/main.cpp)
target_link_libraries(demo PRIVATE robotmath)            # links AND inherits PUBLIC requirements
```

- Dùng **lệnh hướng target** (`target_include_directories`, `target_compile_options`, `target_link_libraries`), không dùng `include_directories` hay `link_libraries` toàn cục theo thư mục.
- **PUBLIC** = cần để build target *và* cần cho người dùng của nó (header của library nhắc tới dependency); **PRIVATE** = chỉ cần để build chính target (chỉ dùng trong file `.cpp`); **INTERFACE** = chỉ cần cho người dùng (library chỉ có header).
- Build ngoài cây source (out-of-source): `cmake -S . -B build` giữ các file sinh ra ngoài cây; xóa `build/` là cách dọn dẹp an toàn.
- Kiểu build: `Debug` (`-O0 -g`), `Release` (`-O3 -DNDEBUG`), `RelWithDebInfo`. Luôn benchmark ở Release. `-DNDEBUG` vô hiệu hóa `assert`, nên một test viết bằng `assert` pass một cách vô nghĩa ở Release.
- `enable_testing()` và `add_test(NAME x COMMAND exe)` đăng ký test; `ctest` chạy chúng và báo phần trăm pass/fail.
- Liệt kê source tường minh trong `add_library`/`add_executable` an toàn hơn `file(GLOB ...)`, thứ chỉ được đánh giá lúc configure (một file mới không được thấy cho đến khi bạn chạy lại `cmake`; `CONFIGURE_DEPENDS` giảm nhẹ điều này).

### Thứ tự link và static library

Linker GNU xử lý archive từ trái sang phải và chỉ trích xuất các member cần để thỏa các symbol đang *chưa được định nghĩa tại thời điểm đó*. Nếu `main.o` cần `a_fn` từ `libA.a` và `a_fn` cần `b_fn` từ `libB.a`, thì `g++ main.o -lA -lB` chạy được, nhưng `g++ main.o -lB -lA` thất bại với `undefined reference to b_fn()`: khi `libB.a` được quét thì chưa có gì cần nó. Với CMake bạn không bao giờ viết tay chuyện này: `target_link_libraries` ghi lại dependency và sắp xếp dòng link.

### Đồ thị phụ thuộc

Cho đồ thị build là một đồ thị có hướng không chu trình (DAG). Một thứ tự build hợp lệ là một thứ tự topo (topological order): mỗi node đứng sau tất cả prerequisite của nó. Tập cần build lại sau khi đổi node $c$ là $c$ cùng mọi node đến được từ $c$ theo các cạnh "được dùng bởi". Một chu trình (library A link B, B link A) không có thứ tự topo và CMake/Make sẽ báo nó.

## Ví dụ có lời giải

Dự án trong phần cài đặt tham khảo có một library `robotmath` (`src/vec2.cpp`, header public trong `include/`), một executable `demo`, và một test executable `test_vec2`.

1. **Configure**: `cmake -S proj -B build -DCMAKE_BUILD_TYPE=Release` đọc `CMakeLists.txt`, tìm compiler, và sinh Makefile trong `build/`. Chưa có gì được biên dịch.
2. **Build**: `cmake --build build` biên dịch `vec2.cpp` thành một object, archive nó thành `librobotmath.a`, biên dịch `main.cpp` và `test_vec2.cpp`, và link hai executable với library. Log build cho thấy 3 bước compile, 1 archive và 2 link (phần trăm từ 16% đến 100%).
3. **Test**: `ctest --test-dir build --output-on-failure` chạy `test_vec2`; kết quả `100% tests passed, 0 tests failed out of 1`.
4. **Incremental**: `touch src/main.cpp && cmake --build build` chỉ biên dịch lại `main.cpp` (1 compile, 1 link). `touch src/vec2.cpp` sẽ biên dịch lại nó, tạo lại archive và link lại cả hai executable (1 compile, 1 archive, 2 link). `touch include/robotmath/vec2.hpp` sẽ biên dịch lại cả ba object, vì cả ba đều include nó.
5. **Include**: `demo` không bao giờ nhắc tới `include/`, vậy mà `#include "robotmath/vec2.hpp"` vẫn chạy, vì `target_include_directories(robotmath PUBLIC include)` được thừa kế bởi bất cứ thứ gì link `robotmath`. Bỏ dòng `target_link_libraries(demo ...)` và `demo` thất bại ở giai đoạn preprocessing với `fatal error: robotmath/vec2.hpp: No such file or directory`.
6. **Symbol**: `nm -C build/librobotmath.a | grep ' T '` liệt kê `robotmath::norm`, `robotmath::rotate` và `robotmath::operator+` là đã được định nghĩa (`T`) trong archive.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** Phân loại mỗi thông báo theo giai đoạn pipeline và nêu cách sửa nhiều khả năng nhất: (a) `fatal error: planner/path.hpp: No such file or directory`; (b) `error: 'Path' does not name a type`; (c) `undefined reference to 'plan(Path const&)'`; (d) `multiple definition of 'clamp01(double)'`.
2. **(Dễ)** Một dự án có 40 file `.cpp` mỗi file mất 3 s để biên dịch. Một header `types.hpp` được include (trực tiếp hoặc gián tiếp) bởi 25 file trong số đó. Ước lượng thời gian biên dịch sau khi động vào `types.hpp` so với động vào một `.cpp` (bỏ qua link). Nêu một kỹ thuật để giảm con số thứ nhất.
3. **(Dễ)** *(Adapted from: GNU Make Manual, introduction to rules)* Trong đồ thị của lab (`app` cần `libplan` và `main.o`; `main.o` cần `main.cpp` và `plan.hpp`) Make build lại những node nào nếu chỉ `plan.hpp` thay đổi, và theo thứ tự nào?
4. **(Trung bình)** Tìm các vấn đề trong `CMakeLists.txt` này và viết lại theo phong cách hiện đại hướng target.
   ```cmake
   add_library(robotmath src/vec2.cpp)
   include_directories(/home/me/proj/include)
   add_executable(demo src/main.cpp)
   ```
   Dự án build được trên máy của tác giả, nhưng `demo` thất bại khi link với `undefined reference to robotmath::rotate(...)`.
5. **(Trung bình)** *(Adapted from: CMake Tutorial, usage requirements)* Library `sensors` có `sensors.hpp` include `util/units.hpp` (các kiểu nằm trong public API của nó) và `sensors.cpp` include `<yaml/parser.hpp>` để đọc cấu hình. Application `driver` link `sensors`. Chọn PUBLIC/PRIVATE cho việc `sensors` link `util` và `yaml`, và nói lựa chọn sai gây ra lỗi gì cho `driver`.
6. **(Trung bình)** *(Adapted from: CMake documentation, `file(GLOB)`)* Một đồng nghiệp dùng `file(GLOB SRC src/*.cpp)` và thêm `src/filter.cpp`, nhưng linker báo `undefined reference to Filter::update`. Giải thích chuỗi sự kiện và nêu hai cách sửa.
7. **(Trung bình)** Một test dùng `assert(norm({3,4}) == 5)`. Target test pass ở build Debug, nhưng một cài đặt sai cũng "pass" ở Release. Giải thích vì sao, và cách làm cho test độc lập với kiểu build.
8. **(Khó)** *(Adapted from: CMake documentation, cmake-buildsystem(7), static libraries)* Cho `main.o` -> `libA.a` -> `libB.a` (A dùng B), nêu lệnh nào trong `g++ main.o -lA -lB` và `g++ main.o -lB -lA` link được và vì sao. Bạn viết gì trong CMake để thứ tự đúng một cách tự động, và điều gì thay đổi nếu A link B `PRIVATE` so với `PUBLIC` khi chính `main` cũng dùng một header của B?
9. **(Khó)** Một header định nghĩa `int twice(int x) { return 2 * x; }` và được `u1.cpp` và `u2.cpp` include. Dự đoán giai đoạn thất bại và thông báo. Nêu ba cách sửa khác nhau và đánh đổi của mỗi cách (inline, `static`, chuyển sang `.cpp`).
10. **(Khó)** Thiết kế đồ thị target cho một repository có các library `core` (kiểu dữ liệu), `planning` (dùng kiểu của `core` trong header và `Eigen` chỉ ở nội bộ), `drivers` (chỉ dùng kiểu của `core` ở nội bộ), các application `planner_node` và `driver_node`, và một test cho mỗi library. Nêu từng dòng `target_link_libraries` kèm loại của nó, vẽ đồ thị và nói điều gì được build lại khi `core/include/core/types.hpp` thay đổi (đếm số target). Vì sao đồ thị phải không có chu trình?
11. **(Mini-project)** Mở rộng dự án lab với một library thứ hai `robotplan` (một hàm dùng `robotmath::Vec2` trong header public của nó) link `robotmath` PUBLIC, cùng test riêng của nó. Ghi lại, trong một bảng, những bước build nào chạy sau `touch` trên (a) `vec2.cpp`, (b) `vec2.hpp`, (c) `robotplan.cpp`; thêm `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` và cho thấy dòng lệnh compile của một source; build một lần với `-DENABLE_ASAN=ON` trong một thư mục build khác.

## Cài đặt tham khảo

Dự án (các lệnh shell chạy từ thư mục chứa `proj/`), rồi một mô hình Python nhỏ của những gì hệ thống build tính toán.

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

Các lệnh và kết quả quan sát được:

```
cmake -S proj -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure      # 100% tests passed, 0 tests failed out of 1
./build/demo                                    # rotated: 6.12323e-17 1
cmake -S proj -B build-asan -DENABLE_ASAN=ON && cmake --build build-asan && ctest --test-dir build-asan
```

Cùng library đó được build bằng tay, đó là thứ CMake tự động hóa:

```
g++ -std=c++17 -Iproj/include -c proj/src/vec2.cpp -o vec2.o      # compile
ar rcs librobotmath.a vec2.o                                         # archive
g++ -std=c++17 -Iproj/include proj/src/main.cpp librobotmath.a -o demo   # compile + link
```

Mô hình Python (phần bạn cài đặt trong lab):

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

## Thực hành độc lập

### Mục tiêu

Build, kiểm thử và khảo sát một dự án C++ nhỏ nhiều target bằng CMake, rồi cài đặt ba phép tính nằm ở lõi của một hệ thống build (thứ tự build, tập build lại, lan truyền include) và đối chiếu chúng với những gì CMake làm.

### Chuẩn bị

Cài `cmake` (3.16+), một compiler C++17 và `make` (ví dụ `sudo apt install cmake g++ make`). Chỉ dùng standard library của Python 3 cho mô hình. Tạo `proj/` với năm file từ phần cài đặt tham khảo.

### Nhiệm vụ

1. Configure và build ngoài cây source; chạy `ctest`. Xác nhận `100% tests passed`.
2. Chạy `touch proj/src/main.cpp`, build lại và đếm số bước compile và link; lặp lại với `touch proj/include/robotmath/vec2.hpp` và với `proj/src/vec2.cpp`. Ghi ra ba con số đếm.
3. Xóa dòng `target_link_libraries(demo ...)` và build lại; sao chép thông báo lỗi và nêu giai đoạn của nó. Khôi phục dòng đó.
4. Trong một file Python, cài đặt `topo_order` (thuật toán Kahn với tie-breaking theo thứ tự bảng chữ cái) và phát hiện chu trình.
5. Cài đặt `rebuild_set` dùng `topo_order`, và so sánh dự đoán của nó với các số đếm ở Nhiệm vụ 2 bằng cách mã hóa đồ thị lab thành một dict.
6. Cài đặt `interface_dirs` và `visible_dirs` (lan truyền PUBLIC/PRIVATE) và các test bên dưới.

### Code khởi đầu

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

### Kiểm thử

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

### Kết quả mong đợi

```
all tests passed
```

và, với phần CMake, `100% tests passed, 0 tests failed out of 1` từ `ctest`, với ba số đếm build lại của Nhiệm vụ 2 bằng 1 compile và 1 link (`main.cpp`), 1 compile, 1 archive và 2 link (`vec2.cpp`), và 3 compile, 1 archive và 2 link (`vec2.hpp`).

### Thử thách mở rộng

Thêm `install(TARGETS robotmath ...)` cùng một file package config để một dự án khác có thể dùng `find_package(robotmath)` và `target_link_libraries(app PRIVATE robotmath::robotmath)`. Hoặc mở rộng mô hình Python với timestamp để nó tái hiện quy tắc "target có cũ hơn một prerequisite không?" của Make.

### Thực hành với thư viện

Standard library của Python đã có thuật toán bạn vừa viết: `graphlib.TopologicalSorter` (3.9+). Đối chiếu `topo_order` của bạn với nó, rồi để hệ thống build thật xác nhận mô hình `rebuild_set` của bạn. Nối đoạn này vào cuối file Python đã hoàn thiện và chạy từ thư mục chứa `proj/` (phần CMake cần `cmake` và `make`; xóa phần 3 nếu không có).

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

Kỳ vọng: ba dòng như `vec2.hpp real compiles: 3 model: 3`, `vec2.cpp ... 1 ... 1`, `main.cpp ... 1 ... 1`, rồi `library track ok`. Mô hình chỉ đếm các node `.o`, đúng là thứ build in ra dưới dạng `Building CXX object`.

## Kiểm chứng

- Chạy build hai lần. Lần `cmake --build build` thứ hai không được làm gì ("up to date"); nếu nó build lại, một timestamp hoặc một file sinh ra đang sai.
- `cmake --build build --verbose` (hoặc `make VERBOSE=1`) in ra các lệnh compile và link thật; hãy kiểm tra các cờ `-I`, `-std=` và `-O` ở đó thay vì đoán.
- `ctest -V` hiển thị output của test; `ctest --output-on-failure` chỉ hiển thị cho các test thất bại.
- `nm -C file.a | grep ' T '` liệt kê các hàm đã định nghĩa; `nm -C demo | grep ' U '` liệt kê các hàm chưa được giải quyết; `ldd demo` liệt kê các shared library.
- Xóa thư mục build và build lại từ đầu trong CI để bắt các phụ thuộc ẩn vào file cũ; so sánh kết quả test Debug và Release.
- Với mô hình: assert tính chất của thứ tự topo trên các DAG ngẫu nhiên.

## Lỗi thường gặp

| Sai lầm | Quan sát được |
|---|---|
| Quên `target_link_libraries(demo PRIVATE robotmath)` | `fatal error: robotmath/vec2.hpp: No such file or directory` (mất lan truyền include) hoặc `undefined reference` |
| Library liệt kê sai thứ tự trên dòng link viết tay | `undefined reference` dù library tồn tại |
| Hàm định nghĩa trong header không có `inline` | `multiple definition of ...` lúc link |
| `file(GLOB)` và một file mới | `undefined reference` cho đến khi chạy lại `cmake` |
| `include_directories(/abs/path)` toàn cục | chỉ chạy trên một máy; rò rỉ sang mọi target |
| Test dựa trên `assert` ở Release (`-DNDEBUG`) | code hỏng được báo là pass |
| Sửa header nhưng biên dịch với object cũ (không quét dependency trong Makefile viết tay) | hành vi cũ vẫn còn; crash khó hiểu (ABI không khớp) |
| Phụ thuộc vòng giữa các library | CMake: "dependency cycle" hoặc lỗi linker; thiết kế lại tầng lớp |
| Cờ sanitizer ở compile nhưng không ở link | `undefined reference to __asan_*` |

## Phương án khác và đánh đổi

- **CMake so với Make viết tay.** Make minh bạch và ổn cho một nhúm file; CMake xử lý tính di động, tìm package (`find_package`), tích hợp IDE và quy tắc install, với cái giá là một ngôn ngữ thứ hai.
- **Generator Make so với Ninja.** Ninja (`-G Ninja`) nhanh hơn cho build incremental của các cây lớn; generator Make có ở khắp nơi. Mô tả CMake là như nhau.
- **Static so với shared library.** Static library tạo một binary khép kín và cho phép linker bỏ code không dùng; shared library tiết kiệm đĩa và bộ nhớ và có thể cập nhật riêng nhưng tạo ra vấn đề tra cứu lúc chạy và ABI (xem CPP12). Đặt theo từng target hoặc bằng `BUILD_SHARED_LIBS`.
- **Nhiều target nhỏ so với một target lớn.** Target mịn cho việc build lại chính xác và buộc phân tầng; quá nhiều làm configure chậm và đồ thị khó đọc.
- **Library chỉ có header (`INTERFACE`).** Không có bước link và dễ phân phối, nhưng mọi người dùng đều biên dịch lại code; template nặng làm tăng thời gian build.
- **Các hệ thống khác.** Bazel (hermetic, remote caching), Meson (cú pháp đơn giản), `colcon`/`ament_cmake` cho ROS 2, và Conan/vcpkg cho dependency. Các ý tưởng (target, đồ thị, usage requirement) vẫn áp dụng.

## Vận dụng và ghi nhớ

`colcon build` là `cmake` cho từng package theo thứ tự dependency, được điều khiển bởi cùng logic đồ thị bạn vừa cài đặt. Đóng gói Python (back end build của `pyproject.toml`), cache layer của Docker (một layer được build lại khi input của nó thay đổi) và các pipeline dữ liệu kiểu `make` (DVC, Snakemake) đều dùng "build lại những gì nằm phía sau một thay đổi". Để ghi nhớ: sau vài ngày, viết từ trí nhớ các dòng CMake cho một library có một dependency public và một private, và mô tả mỗi từ khóa làm gì. Khi gặp bất kỳ lỗi build nào, trước hết hãy gọi tên giai đoạn.

## Đáp án bài tập

1. (a) preprocess: include directory không nằm trong include path của target này; sửa bằng `target_include_directories` hoặc link library xuất nó. (b) compile: thiếu `#include`/forward declaration hoặc sai namespace. (c) link: định nghĩa không nằm trong object hay library nào được link; thêm file source hoặc `target_link_libraries`. (d) link: một hàm không inline được định nghĩa trong header được include hai lần; làm nó `inline`.
2. Sau khi động vào `types.hpp`: $25\times3=75$ s; sau khi động vào một `.cpp`: $3$ s. Giảm bằng forward declaration, tách header, pimpl idiom, precompiled header, hoặc cache của compiler (`ccache`).
3. Thay đổi ở `plan.hpp` làm `main.o` cũ đi (nó include `plan.hpp`), và do đó `app`: thứ tự `main.o`, rồi `app` (trong đồ thị lab `plan.hpp` chỉ là prerequisite của `main.o`). `libplan` không được build lại trong đồ thị đó. Trong mô hình, `rebuild_set(deps, {"plan.hpp"})` trả về `["plan.hpp", "main.o", "app"]`.
4. Các vấn đề: không có `target_link_libraries(demo PRIVATE robotmath)`, nên `demo` được biên dịch với include directory toàn cục nhưng không bao giờ được link với library: `undefined reference`; đường dẫn tuyệt đối chỉ đúng với một máy; `include_directories` là toàn cục và áp dụng cho mọi target. Cách sửa: `add_library(robotmath src/vec2.cpp)`, `target_include_directories(robotmath PUBLIC include)`, `add_executable(demo src/main.cpp)`, `target_link_libraries(demo PRIVATE robotmath)`.
5. `util`: PUBLIC, vì `sensors.hpp` (được `driver` include) include `util/units.hpp`; PRIVATE sẽ làm `driver` thất bại với `fatal error: util/units.hpp: No such file or directory`. `yaml`: PRIVATE, vì chỉ `sensors.cpp` dùng nó; để PUBLIC sẽ làm rò rỉ dependency và include path của nó sang mọi người dùng `sensors` và buộc họ phải tìm nó.
6. `file(GLOB)` được đánh giá khi CMake configure, nên bản build sinh ra không liệt kê `filter.cpp`; build sau đó biên dịch mọi thứ nó biết nhưng `Filter::update` không bao giờ được biên dịch và link thất bại. Cách sửa: chạy lại `cmake` (hoặc touch `CMakeLists.txt`); liệt kê source tường minh (khuyến nghị); hoặc dùng `file(GLOB ... CONFIGURE_DEPENDS ...)`, kiểm tra lại lúc build với một chút chi phí.
7. Ở Release, `-DNDEBUG` biến `assert(...)` thành không gì cả, nên code sai không bao giờ bị kiểm tra và test trả về thành công. Hãy dùng một macro test không phụ thuộc `NDEBUG` (một `CHECK` in ra và trả `EXIT_FAILURE`, như trong lab), hoặc một framework như GoogleTest/Catch2.
8. `main.o -lA -lB` link được: sau khi quét `libA.a`, `b_fn` chưa được định nghĩa và `libB.a` được quét tiếp theo. `main.o -lB -lA` thất bại vì `libB.a` được quét khi chưa có gì cần nó và nhu cầu về sau của `libA.a` không bao giờ được thỏa. Trong CMake: `target_link_libraries(A PUBLIC B)` hoặc `PRIVATE B`, và `target_link_libraries(main PRIVATE A)`; dòng link được sắp xếp tự động. Với `PRIVATE`, include directory của B không lan truyền sang `main`, nên nếu `main` dùng một header của B thì nó cần `target_link_libraries(main PRIVATE B)` riêng; với `PUBLIC`, `main` thừa kế include directory của B (và B trên dòng link của nó).
9. Giai đoạn: link. `multiple definition of 'twice(int)'; ... first defined here`, vì mỗi translation unit có định nghĩa riêng. Cách sửa: (1) `inline int twice(int x)` (đúng idiom, định nghĩa ở lại trong header, linker gộp các bản sao); (2) `static int twice(int)`, mỗi file có bản riêng (tốn chỗ, có thể nhân đôi trạng thái); (3) khai báo trong header và định nghĩa trong một `.cpp` (sạch nhất cho code không tầm thường, nhưng ngăn inline xuyên file nếu không có LTO).
10. `core`: `add_library(core ...)`, `target_include_directories(core PUBLIC include)`. `planning`: `target_link_libraries(planning PUBLIC core)` (header của nó dùng kiểu của core) và `PRIVATE Eigen3::Eigen`. `drivers`: `PRIVATE core`. `planner_node`: `PRIVATE planning`; `driver_node`: `PRIVATE drivers`; test: `test_core -> core`, `test_planning -> planning`, `test_drivers -> drivers`. Một thay đổi ở `core/types.hpp` build lại các object của `core`, `planning`, `drivers` và các node cùng test include nó: cả 3 library, 2 application và 3 test bị ảnh hưởng (8 target). Nói chặt chẽ, chỉ các target có source include header (trực tiếp hoặc qua một header public) mới biên dịch lại: `core`, `planning`, `drivers`, `planner_node`, `test_core`, `test_planning`; `driver_node` và `test_drivers` chỉ link lại, vì `drivers` link `core` PRIVATE và header của nó che giấu các kiểu. Một chu trình sẽ không có thứ tự build hợp lệ: A cần B được build trước và B cần A được build trước.
11. Một câu trả lời tốt: (a) `vec2.cpp`: 1 compile, archive, link lại `demo`, `test_vec2` và test của `robotplan`; (b) `vec2.hpp`: mọi object include nó, kể cả `robotplan.cpp`; (c) `robotplan.cpp`: 1 compile, archive và link lại test của chính nó, không phải `demo`. Dòng `compile_commands.json` cho thấy các cờ `-I` được thừa kế qua `PUBLIC`; bản build ASAN nằm trong thư mục riêng để hai cấu hình không lẫn vào nhau.

## Đọc thêm

- [CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/index.html) - hướng dẫn từng bước: library, usage requirement, kiểm thử và cài đặt.
- [cmake-buildsystem(7)](https://cmake.org/cmake/help/latest/manual/cmake-buildsystem.7.html) - ngữ nghĩa chính xác của target, PUBLIC/PRIVATE/INTERFACE và usage requirement bắc cầu.
- [GNU Make Manual](https://www.gnu.org/software/make/manual/make.html) - rule, prerequisite và cách quyết định build lại.

**Thực hành thêm:** [bước "Adding a Library" của CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/Adding%20a%20Library.html) và các bước tiếp theo (usage requirement, kiểm thử), trang tham chiếu [`target_link_libraries`](https://cmake.org/cmake/help/latest/command/target_link_libraries.html) (ngữ nghĩa PUBLIC/PRIVATE/INTERFACE, rồi làm lại bài tập 10), lời cảnh báo về [`file(GLOB)`](https://cmake.org/cmake/help/latest/command/file.html), [CTest manual](https://cmake.org/cmake/help/latest/manual/ctest.1.html), và [tài liệu graphlib](https://docs.python.org/3/library/graphlib.html) cho mô hình thứ tự build.
