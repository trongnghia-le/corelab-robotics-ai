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

Hãy hình dung xây một ngôi nhà từ các căn phòng đúc sẵn. Biên dịch là chế tạo từng căn phòng trong xưởng; nó chỉ cần bản vẽ mặt bằng của các phòng bên cạnh (các header), chứ không cần chính các phòng đó. Link là ngày các căn phòng được giao tới và bắt vít vào nhau; đó là lần đầu tiên có người phát hiện một cánh cửa được vẽ trên một bản vẽ nhưng chưa từng được làm trong căn phòng nào. Vì vậy "undefined reference" là thông báo lúc link còn "No such file" là lúc biên dịch: đó là những người khác nhau nhìn những tài liệu khác nhau.

Một ví dụ phần mềm robot: thư viện `planner` dùng `Vec2` của `core` trong header công khai, và cũng dùng một bộ phân tích YAML bên trong một file `.cpp`. Bất kỳ ai include `planner.hpp` phải tìm được header của `core`, nhưng không ai cần biết YAML tồn tại. `PUBLIC` và `PRIVATE` là cách viết ra đúng câu đó, để build nói với mọi target khác đủ lượng thông tin và không hơn.

**Hãy dự đoán trước khi tính.** Hãy `touch` một file `.cpp` trong dự án 40 source và dự đoán có bao nhiêu tiến trình compiler chạy; rồi `touch` một header mà 25 file include và dự đoán lại. Một dự đoán tốt là 1 và 25, cộng thêm một bước archive hoặc link mỗi lần. Nếu dự đoán của bạn sau khi `touch` file `.cpp` là "tất cả", mô hình trong đầu bạn coi build là một script luôn chạy từ đầu, thay vì một đồ thị trong đó chỉ các nút lỗi thời mới chạy.

**Trực giác sai thường gặp** là thứ tự thư viện trên dòng link chỉ là chuyện phong cách và CMake "cứ link mọi thứ". Với archive tĩnh, thứ tự là ngữ nghĩa: linker quét mỗi archive một lần, theo thứ tự cho trước, rồi quên nó. `target_link_libraries` hoạt động vì nó ghi một đồ thị và CMake suy ra thứ tự hợp lệ (và lặp lại các thành phần vòng) cho bạn. Cùng trực giác sai ấy xuất hiện với header: "chạy được trên máy tôi" thường nghĩa là một `include_directories` toàn cục hay một đường dẫn tuyệt đối làm nó chạy ở đó và không nơi nào khác.

![Bốn giai đoạn preprocess, compile, archive và link, cùng thông tin mỗi giai đoạn đọc và thông báo lỗi điển hình](/lesson-figures/CPP07.svg)

*Hình: compiler chỉ thấy khai báo, nên một định nghĩa bị thiếu chỉ lộ ra ở giai đoạn link; một header bị thiếu lộ ra ngay ở giai đoạn đầu. Gọi tên giai đoạn là thu hẹp nguyên nhân trước khi mở bất kỳ file nào.*

## Lý thuyết và suy dẫn

### Lỗi theo giai đoạn

| Thông báo | Giai đoạn | Nguyên nhân điển hình |
|---|---|---|
| `fatal error: robotmath/vec2.hpp: No such file or directory` | preprocess | include directory chưa được cấp cho target này |
| `error: 'foo' was not declared in this scope` | compile | thiếu `#include`, gõ sai, sai namespace |
| `undefined reference to 'robotmath::rotate(...)'` | link | khai báo tồn tại nhưng object hoặc library chứa định nghĩa không được link |
| `multiple definition of 'twice(int)'` | link | hàm không inline được định nghĩa trong header được hai file `.cpp` include |

Khai báo có thể lặp lại; một định nghĩa phải tồn tại đúng một lần trong chương trình (one-definition rule, ODR). Các hàm định nghĩa trong header phải là `inline` (hoặc là template, hoặc `constexpr`).

**Ví dụ.** Một driver cho flight controller được tách thành `imu/filter.hpp` (khai báo `double lowpass(double prev, double sample, double alpha);`) và vài chương trình nhỏ, mỗi chương trình làm hỏng đúng một giai đoạn. Output thật của `g++ 11.4`:

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

Chương trình thứ ba biên dịch sạch: khai báo trong header là đủ cho compiler. Chỉ linker mới hỏi "thân hàm đâu?". Chương trình thứ tư hỏng theo chiều ngược lại: hai object cùng mang một bản `gain()`. Đọc giai đoạn trước (preprocess, compile, link) là đã gọi tên nguyên nhân trước khi mở bất kỳ file nào.

### Quy tắc build lại kiểu Make

Một rule có dạng `target: prerequisites` và một recipe. Target được build lại khi bất kỳ prerequisite nào mới hơn (hoặc thiếu). Compiler có thể ghi ra các phụ thuộc header thật sự (`-MMD`), mà các bản build do CMake sinh ra dùng tự động. Hệ quả: đổi một `.cpp` biên dịch lại một object và link lại; đổi một header được include rộng rãi biên dịch lại mọi object include nó. Nếu $k$ trong $N$ object include một header, chi phí của việc động vào nó là $k$ lần compile cộng các lần link; chi phí động vào một `.cpp` là 1 lần compile cộng các lần link. Đó là lý do header nên include càng ít càng tốt.

**Ví dụ.** Một dự án bộ điều khiển có $N=6$ source; ba trong số đó (`pid_a.cpp`, `pid_b.cpp`, `pid_c.cpp`) include `pid.hpp`. Một Makefile viết tay với `-MMD` (để compiler ghi lại phụ thuộc header) cho kết quả:

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

Chạm một `.cpp` tốn 1 compile cộng bước link; chạm header tốn $k=3$ compile cộng bước link, và lần `make` thứ hai không làm gì. Với 2 s mỗi compile, đó là 2 s so với 6 s, cộng thêm bước link mỗi lần.

Thử thay đổi $N$, $k$, thời gian compile và số job song song để thấy chi phí của header tăng nhanh thế nào (thời gian thực của $k$ lần compile lại xếp vào $j$ job là $\lceil k/j\rceil\,t$, thời gian CPU là $k\,t$):

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

**Ví dụ.** Một module odometry bánh xe: `odom` đổi số tick encoder thành quãng đường, $d = 2\pi r\,\text{ticks}/\text{ticks\_per\_rev}$. Mô tả CMake chỉ cần các dòng của phần này, còn tên target mang phần còn lại:

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

Kiểm tra: 1440 tick với 360 tick mỗi vòng là 4 vòng của bánh bán kính 0,05 m, nên $4\cdot 2\pi\cdot 0.05 = 1.2566$ m, đúng như in ra. `main.cpp` include `odom/wheel.hpp` mà không có dòng include riêng nào: `PUBLIC include` của `odom` đã tới `drive` và `test_wheel` qua `target_link_libraries`.

### Thứ tự link và static library

Linker GNU xử lý archive từ trái sang phải và chỉ trích xuất các member cần để thỏa các symbol đang *chưa được định nghĩa tại thời điểm đó*. Nếu `main.o` cần `a_fn` từ `libA.a` và `a_fn` cần `b_fn` từ `libB.a`, thì `g++ main.o -lA -lB` chạy được, nhưng `g++ main.o -lB -lA` thất bại với `undefined reference to b_fn()`: khi `libB.a` được quét thì chưa có gì cần nó. Với CMake bạn không bao giờ viết tay chuyện này: `target_link_libraries` ghi lại dependency và sắp xếp dòng link.

**Ví dụ.** Một thư viện planner `libplan.a` (`plan()` gọi `costmap_at()`) và một thư viện bản đồ `libmap.a` (định nghĩa `costmap_at()`); `main.o` gọi `plan()`. Chạy thật với gcc 11.4:

```
$ gcc -c main.c plan.c map.c && ar rcs libplan.a plan.o && ar rcs libmap.a map.o
$ gcc main.o -L. -lmap -lplan -o t1       # main needs plan(); plan() needs costmap_at()
./libplan.a(plan.o): in function `plan':
plan.c:(.text+0x9): undefined reference to `costmap_at'
$ gcc main.o -L. -lplan -lmap -o t2 && ./t2; echo "exit $?"
exit 0
```

Khi `-lmap` đứng trước, `libmap.a` được quét lúc chưa có gì cần `costmap_at` nên bị bỏ qua; sau đó `libplan.a` mới tạo ra nhu cầu và không còn archive nào. Thông báo nêu `plan.c`, object cần symbol, chứ không nêu thư viện đang thiếu trên dòng lệnh.

### Đồ thị phụ thuộc

Cho đồ thị build là một đồ thị có hướng không chu trình (DAG). Một thứ tự build hợp lệ là một thứ tự topo (topological order): mỗi node đứng sau tất cả prerequisite của nó. Tập cần build lại sau khi đổi node $c$ là $c$ cùng mọi node đến được từ $c$ theo các cạnh "được dùng bởi". Một chu trình (library A link B, B link A) không có thứ tự topo và CMake/Make sẽ báo nó.

**Ví dụ.** Một node SLAM: `scan.o` và `icp.o` đều include `scan.hpp`, `libslam.a` archive chúng, `slam_node` link thư viện và `viz.o`. Thứ tự topo và tập cần build lại chỉ là vài dòng Python:

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

```
['scan.hpp', 'scan.o', 'icp.o', 'libslam.a', 'slam_node']
['viz.cpp', 'viz.o', 'slam_node']
```

Chạm `scan.hpp` chạm tới 4 nút phía sau (hai object, archive và executable); chạm `viz.cpp` chỉ tới `viz.o` và executable. `order` là một thứ tự hợp lệ bất kỳ: `graphlib` chỉ đảm bảo điều kiện tiên quyết đứng trước.

### Phân giải archive như một điểm bất động

Mô hình trạng thái của linker là một tập $U$ các symbol hiện đang chưa định nghĩa. Các object file ghi trên dòng lệnh luôn được lấy, và các symbol chưa định nghĩa của chúng được thêm vào $U$. Một archive (`libX.a`) được quét *một lần*, tại vị trí của nó trên dòng lệnh: mọi member định nghĩa một symbol trong $U$ đều được trích ra, các symbol chưa định nghĩa của chính nó được thêm vào $U$, và việc quét archive đó tiếp tục cho đến khi không member nào còn lại định nghĩa symbol trong $U$. Sau đó archive không bao giờ được xét lại. Đó chính là lý do thứ tự quan trọng (GNU ld manual, `--start-group`: bình thường một archive chỉ được tìm một lần theo thứ tự ghi trên dòng lệnh).

Một trường hợp cụ thể với hai archive tham chiếu chéo. `libA.a` có các member `a1.o` (định nghĩa `fa1`, cần `fb1`) và `a2.o` (định nghĩa `fa2`); `libB.a` có `b1.o` (định nghĩa `fb1`, cần `fa2`); `main.o` cần `fa1`.

| lệnh | vết quét | kết quả |
|---|---|---|
| `main.o -lA -lB` | $U=\{fa1\}$; trích `a1.o`, $U=\{fb1\}$; `libB`: trích `b1.o`, $U=\{fa2\}$; hết archive | `undefined reference to fa2` |
| `main.o -lB -lA` | $U=\{fa1\}$; `libB` không có gì cho $U$; `libA`: `a1.o`, $U=\{fb1\}$ | `undefined reference to fb1` |
| `main.o -lA -lB -lA` | như dòng đầu, rồi `libA` lần nữa: `a2.o` định nghĩa `fa2` | link được |
| `main.o --start-group -lA -lB --end-group` | nhóm được quét lại cho đến khi $U$ không đổi | link được |

Tính dừng của một nhóm: mỗi lượt thêm mà chưa dừng đều trích ra ít nhất một member mới, và một member được trích nhiều nhất một lần, nên một nhóm archive có tổng $M$ member cần nhiều nhất $M+1$ lượt quét. ld manual cảnh báo rằng cách này "có chi phí hiệu năng đáng kể" và chỉ nên dùng khi có tham chiếu vòng không tránh được. CMake làm tương tự cho các static library phụ thuộc lẫn nhau: nó lặp lại toàn bộ thành phần liên thông mạnh, nên `A <-> B` được link từ `main` cho ra `A B A B` (CMake docs, `target_link_libraries`, "Cyclic Dependencies of Static Libraries"). Lời khuyên của nó: nếu hai archive phụ thuộc nhau đến mức đó, hãy gộp chúng (ví dụ thành một object library).

**Ví dụ.** Ba archive: `libX.a` = {`x1.o`: định nghĩa `f1`, cần `g1`; `x2.o`: định nghĩa `f2`}, `libY.a` = {`y1.o`: định nghĩa `g1`, cần `h1`}, `libZ.a` = {`z1.o`: định nghĩa `h1`, cần `f2`}; `main.o` cần `f1`. Áp dụng quy tắc của phần này cho `-lX -lY -lZ`: $U=\{f1\}$; `libX` trích `x1.o`, $U=\{g1\}$; `libY` trích `y1.o`, $U=\{h1\}$; `libZ` trích `z1.o`, $U=\{f2\}$; không còn archive nào nên `f2` vẫn chưa định nghĩa. Với thứ tự `-lZ -lY -lX` không gì khớp cho đến `libX`, cho $U=\{g1\}$ rồi dừng. Lượt quét thứ tư `libX` kết thúc với $U=\emptyset$. Linker đồng ý (gcc 11.4):

```
$ gcc main.o -L. -lX -lY -lZ -o t
undefined reference to `f2'
$ gcc main.o -L. -lZ -lY -lX -o t
undefined reference to `g1'
$ gcc main.o -L. -lX -lY -lZ -lX -o t && echo linked
linked
```

Chuỗi $f1\to g1\to h1\to f2$ chạy "ngược" qua các archive, nên dòng duy nhất chạy được lặp lại `libX` ở cuối.

### Usage requirement bắc cầu, một cách chính xác

`target_link_libraries(A <scope> B)` ghi phụ thuộc vào hai nơi. `PRIVATE` đặt `B` chỉ vào `LINK_LIBRARIES` của riêng `A`; `INTERFACE` đặt chỉ vào `INTERFACE_LINK_LIBRARIES`; `PUBLIC` đặt vào cả hai (CMake docs, `target_link_libraries`, "Libraries for a Target and/or its Dependents"). Một consumer `main` của `A` thừa hưởng `INTERFACE_INCLUDE_DIRECTORIES`, `INTERFACE_COMPILE_DEFINITIONS`, v.v. của `A`, và đệ quy của mọi thứ trong `INTERFACE_LINK_LIBRARIES` của `A`.

Static library cần một ngoại lệ. Nếu `A` là static và link `B` ở dạng `PRIVATE`, file thực thi cuối cùng vẫn cần object code của `B`, vì `libA.a` chứa các tham chiếu chưa phân giải vào `B`. Vì vậy CMake ghi phụ thuộc private vào interface dưới dạng `$<LINK_ONLY:B>`, nghĩa là "link `B`, nhưng đừng truyền include directory, definition hay option của nó" (CMake docs, generator expressions, `$<LINK_ONLY:...>`). Đã kiểm tra với CMake 3.22: với `A` static và `PRIVATE B`, `INTERFACE_LINK_LIBRARIES` của `A` là `$<LINK_ONLY:B>`; dòng link của `main` chứa `libA.a libB.a` nhưng cờ biên dịch của nó không chứa include directory của `B`. Với `A` shared thì property rỗng, vì thư viện shared đã phân giải `B` ngay lúc link của nó.

![Bảng-sơ đồ: với thư viện tĩnh A link B, ba scope và việc A, cũng như main, có thấy thư mục include của B và link B hay không](/lesson-figures/CPP07-2.svg)

*Hình: scope viết trong `target_link_libraries(A <scope> B)` quyết định ai thấy thư mục include của B; với A tĩnh, B được link vào `main` trong cả ba trường hợp.*

**Ví dụ.** Một thư viện sensor-fusion `fusion` (static) chỉ dùng thư viện ma trận `matlib` bên trong `fusion.c`, và `slam` link `fusion`. CMake 3.22 báo hai property và các dòng lệnh được sinh ra:

```cmake
add_library(matlib STATIC mat.c)
target_include_directories(matlib PUBLIC matinc)
add_library(fusion STATIC fusion.c)
target_include_directories(fusion PUBLIC fusioninc)
target_link_libraries(fusion PRIVATE matlib)
add_executable(slam slam.c)
target_link_libraries(slam PRIVATE fusion)
```

```
-- fusion LINK_LIBRARIES           = matlib
-- fusion INTERFACE_LINK_LIBRARIES = $<LINK_ONLY:matlib>
compile line of slam.c:  cc -Ifusioninc -o CMakeFiles/slam.dir/slam.c.o -c slam.c
link line of slam:       cc CMakeFiles/slam.dir/slam.c.o -o slam  libfusion.a libmatlib.a
```

`fusion` giữ `matlib` trong `LINK_LIBRARIES` của chính nó, và chỉ công bố cho consumer dưới dạng `$<LINK_ONLY:matlib>`. Vì vậy `libmatlib.a` có trên dòng link của `slam` trong khi `-Imatinc` vắng mặt trên dòng compile: dependency private được link nhưng không được compile cùng.

### Xuất một target: BUILD_INTERFACE và INSTALL_INTERFACE

Một usage requirement như `target_include_directories(core PUBLIC /abs/path/include)` hợp lệ khi build trong cùng cây thư mục, nhưng nếu `core` được cài đặt và export thì đường dẫn sẽ bị đóng cứng vào một file dùng trên máy khác. Vì vậy CMake từ chối đường dẫn tuyệt đối nằm trong thư mục source hoặc build trong `INTERFACE_INCLUDE_DIRECTORIES` của một target được export. Cách sửa tách hai thế giới: `$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>` dùng khi consume từ cùng build system, và `$<INSTALL_INTERFACE:include>` (đường dẫn tương đối so với install prefix) dùng sau khi cài đặt (CMake docs, cmake-buildsystem(7), "Include Directories and Usage Requirements" và "Build Specification and Usage Requirements").

**Ví dụ.** Một thư viện transform `tf` được export bằng `install(TARGETS tf EXPORT tfTargets ...)` và `install(EXPORT tfTargets ...)`. Với đường dẫn nguồn tuyệt đối trong usage requirement, CMake 3.22 dừng ở bước generate; với hai generator expression thì qua:

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

Đường dẫn bị từ chối sẽ bị đóng cứng vào file export và sai trên mọi máy khác, trong khi `include` sau `INSTALL_INTERFACE` được hiểu tương đối với install prefix.

### Các loại thư viện và mô hình chi phí: static, shared, object, interface

`add_library` tạo một trong nhiều loại target, và loại đó quyết định build tạo ra gì và code của nó được biên dịch khi nào (CMake docs, cmake-buildsystem(7), "Binary Targets", "Object Libraries" và "Interface Libraries"). Thư viện **static** là một archive các object file; lần link cuối sao chép các member cần thiết vào mọi file thực thi dùng nó. Thư viện **shared** được link một lần và phân giải lại lúc chương trình nạp, nên file thực thi chứa một tham chiếu chứ không phải code. Thư viện **object** là tập các object file "được tạo bằng cách biên dịch source mà không archive hay link"; các target khác tái dùng các object đó qua `$<TARGET_OBJECTS:name>` hoặc bằng cách link object library. Thư viện **interface** không biên dịch gì và không sinh file: nó chỉ mang usage requirement, nên là loại đúng cho code chỉ có header.

Hệ quả thực tế là một mô hình chi phí. Một file source nằm trong $k$ target khác nhau được biên dịch $k$ lần, mỗi target một lần, vì mỗi target có thư mục object riêng. Đã kiểm tra với CMake 3.22: hai file thực thi cùng liệt kê `f.cpp` kích hoạt tổng cộng 4 bước biên dịch (hai cho các file `main`, hai cho `f.cpp`), trong khi đặt `f.cpp` vào một thư viện `OBJECT` được cả hai link chỉ kích hoạt 3. Với một dự án mà thư viện cũng được biên dịch vào file thực thi test của nó, object library (hoặc link test với thư viện) tránh biên dịch hai lần. Link với static library thay vì liệt kê source còn có lợi ích thêm là usage requirement của nó đi theo.

Một module nên chọn loại nào? Một quy tắc ngón tay cái suy ra từ các định nghĩa: dùng static library làm mặc định cho code do dự án sở hữu (triển khai đơn giản, dòng link tất định); dùng shared library khi nhiều file thực thi phải chia sẻ một bản code hoặc khi code phải được thay mà không link lại ứng dụng; dùng object library để biên dịch một lần rồi archive hoặc link cùng các object vào nhiều target khác nhau; dùng interface library cho code chỉ có header và cho các gói cờ mà nhiều target nên thừa hưởng. Hai giới hạn cần nhớ: object library không thể là `TARGET` của `add_custom_command(TARGET)`, và interface library chỉ nhận dạng `INTERFACE` của `target_include_directories`, `target_compile_definitions` và các lệnh tương tự.

**Ví dụ.** Hai executable `m1` và `m2` cần cùng `f.c`. Đếm các dòng `Building C object` (CMake 3.22, generator Makefile):

```
$ cmake -S . -B b -DMODE=listed      # add_executable(m1 m1.c f.c) and add_executable(m2 m2.c f.c)
$ cmake --build b | grep -c 'Building C object'
4
$ cmake -S . -B b -DMODE=object      # add_library(fobj OBJECT f.c); m1, m2 use $<TARGET_OBJECTS:fobj>
$ cmake --build b | grep -c 'Building C object'
3
```

Liệt kê `f.c` trong cả hai executable thì nó được compile hai lần (2 file `main` cộng 2 bản `f.c` = 4); object library compile nó một lần (3). Ở đây tiết kiệm một lần compile; với một translation unit 5 phút dùng chung cho mười công cụ thì là chín lần.

## Ví dụ có lời giải

### Trường hợp 1: configure, build, test, build lại

**Đề bài.** Dự án trong phần cài đặt tham khảo có library `robotmath` (`src/vec2.cpp`, header public `include/robotmath/vec2.hpp`), executable `demo` (`src/main.cpp`) và test executable `test_vec2` (`tests/test_vec2.cpp`). Hãy configure out-of-source ở chế độ Release, build, chạy test, rồi dự đoán và kiểm tra số bước compile, archive và link chạy sau khi `touch` (a) `src/main.cpp`, (b) `src/vec2.cpp`, (c) `include/robotmath/vec2.hpp`.

**Lời giải.**

1. *Viết đồ thị* (lý thuyết, "Đồ thị phụ thuộc"). Cạnh đi từ điều kiện tiên quyết tới thứ nó nuôi: `vec2.cpp`, `vec2.hpp` $\to$ `vec2.o`; `main.cpp`, `vec2.hpp` $\to$ `main.o`; `test_vec2.cpp`, `vec2.hpp` $\to$ `test_vec2.o`; `vec2.o` $\to$ `librobotmath.a`; `main.o`, `librobotmath.a` $\to$ `demo`; `test_vec2.o`, `librobotmath.a` $\to$ `test_vec2`. Mọi `.o` đều include header, đó là điểm mấu chốt của bước 5.
2. *Configure*: `cmake -S proj -B build -DCMAKE_BUILD_TYPE=Release` đọc `CMakeLists.txt`, tìm compiler và sinh Makefile trong `build/`. Chưa có gì được biên dịch.
3. *Build*: `cmake --build build`. Lần build đầu chạy mỗi nút không phải source đúng một lần: 3 object (compile), 1 archive, 2 executable (link), tổng 6 bước. Log đúng như vậy: `Building CXX object` cho `vec2.cpp`, `main.cpp`, `test_vec2.cpp`; `Linking CXX static library librobotmath.a`; `Linking CXX executable` cho `demo` và `test_vec2` (tiến độ 16% đến 100%).
4. *Test*: `ctest --test-dir build --output-on-failure` in `100% tests passed, 0 tests failed out of 1`.
5. *Dự đoán tập cần build lại*: tập cần build lại sau khi đổi một nút là nút đó cộng mọi thứ đi tới được từ nó. (a) `main.cpp` tới `main.o` và `demo`: 1 compile, 1 link. (b) `vec2.cpp` tới `vec2.o`, `librobotmath.a`, `demo`, `test_vec2`: 1 compile, 1 archive, 2 link. (c) `vec2.hpp` tới cả ba object, archive và cả hai executable: 3 compile, 1 archive, 2 link.
6. *Chạy và so sánh*: sau `touch` và `cmake --build build`, log cho thấy (a) 1 `Building CXX object` và 1 `Linking CXX executable`; (b) 1 `Building`, 1 `Linking CXX static library` và 2 `Linking CXX executable`; (c) 3 `Building`, 1 archive, 2 executable. Đúng như dự đoán.
7. *Lan truyền include* (lý thuyết, "Những điều cốt yếu của CMake"): `demo` không hề nhắc tới `include/`, vậy mà `#include "robotmath/vec2.hpp"` vẫn chạy, vì `target_include_directories(robotmath PUBLIC include)` được thừa kế bởi bất cứ thứ gì link `robotmath`. Bỏ dòng `target_link_libraries(demo ...)` thì `demo` thất bại ở giai đoạn preprocessing với `fatal error: robotmath/vec2.hpp: No such file or directory`.
8. *Symbol*: `nm -C build/librobotmath.a | grep ' T '` liệt kê `robotmath::norm`, `robotmath::rotate` và `robotmath::operator+` là đã được định nghĩa (`T`) trong archive.

![Cột chồng các bước compile, archive và link chạy sau khi touch main.cpp (2 bước), vec2.cpp (4 bước) và vec2.hpp (6 bước)](/lesson-figures/CPP07-3.svg)

*Hình: các bước đo được của Trường hợp 1; chạm header tốn gấp ba lần chạm `.cpp` vì ba object include nó.*

**Kiểm tra.** Số bước sau mỗi lần touch bằng kích thước tập đi tới được trừ đi source đã chạm: $2$, $4$ và $6$ bước cho (a), (b), (c), như trong hình. Trường hợp giới hạn: lần `cmake --build build` thứ hai không đổi gì chạy 0 bước ("up to date").

**Rút ra.** Một header được $k$ object include tốn $k$ lần compile, một `.cpp` private tốn một lần: build là một đồ thị, và chỉ các nút đi tới được từ thay đổi mới chạy.

### Trường hợp 2: một lỗi link được lần vết từ nguyên lý đầu tiên

**Đề bài.** Bốn file C: `main.c` gọi `fa1`; `a1.c` định nghĩa `fa1`, gọi `fb1`; `a2.c` định nghĩa `fa2`; `b1.c` định nghĩa `fb1`, gọi `fa2`. Tạo archive `libA.a` từ `a1.o a2.o` và `libB.a` từ `b1.o`. Hãy dự đoán dòng nào trong `main.o -lA -lB`, `main.o -lB -lA`, `main.o -lA -lB -lA` link được, dùng quy tắc của "Phân giải archive như một điểm bất động", rồi kiểm tra bằng gcc 11.4 và binutils 2.47.

**Lời giải.**

1. *Quy tắc*: giữ tập $U$ các symbol chưa định nghĩa. Bắt đầu với $U=\{fa1\}$ từ `main.o`. Mỗi archive được quét một lần, tại vị trí của nó; nó đóng góp mọi member định nghĩa một symbol trong $U$, và các symbol chưa định nghĩa của member đó đi vào $U$.
2. *`-lA -lB`*: `libA.a` định nghĩa `fa1`, nên `a1.o` được trích và $U=\{fb1\}$. `a2.o` định nghĩa `fa2`, chưa nằm trong $U$, nên ở lại archive. `libB.a`: `b1.o` định nghĩa `fb1`, nên được trích và $U=\{fa2\}$. Không còn archive nào: `fa2` chưa định nghĩa. Quan sát: `b1.c:(.text+0x9): undefined reference to 'fa2'`.
3. *`-lB -lA`*: $U=\{fa1\}$ và `libB.a` không định nghĩa gì trong đó, nên bị bỏ qua. `libA.a` trích `a1.o`, $U=\{fb1\}$, và không còn gì. Quan sát: `a1.c:(.text+0x9): undefined reference to 'fb1'`.
4. *`-lA -lB -lA`*: như bước 2 cho đến $U=\{fa2\}$; lượt quét thứ hai `libA.a` thấy `a2.o` định nghĩa `fa2`, nên $U=\emptyset$ và link thành công. Dạng nhóm `-Wl,--start-group -lA -lB -Wl,--end-group` cũng link được, với giá là quét lặp.
5. *Trong CMake* cách sửa là một phụ thuộc, không phải một thứ tự: `target_link_libraries(A PRIVATE B)` và `target_link_libraries(B PRIVATE A)` tạo một thành phần static vòng, và file thực thi link `A` nhận `A B A B` (tài liệu CMake, `target_link_libraries`, "Cyclic Dependencies of Static Libraries"). Thiết kế tốt hơn là loại bỏ vòng bằng cách gộp `A` và `B`, hoặc chuyển `fa2` sang một thư viện không phụ thuộc `A`.

![Vết của tập U cho ba dòng link với libA.a và libB.a](/lesson-figures/CPP07-4.svg)

*Hình: tập $U$ sau mỗi lượt quét; hai dòng đầu kết thúc với một symbol chưa định nghĩa, dòng thứ ba kết thúc với $U=\emptyset$.*

**Kiểm tra.** `nm libA.a libB.a` xác nhận mô hình: `a1.o` có `T fa1` và `U fb1`, `a2.o` có `T fa2`, `b1.o` có `T fb1` và `U fa2`. Ba lệnh link thật cho kết quả của bước 2, 3 và 4: hai thất bại và một thành công.

**Rút ra.** Lỗi được báo với object *cuối cùng* cần symbol (`b1.c`, rồi `a1.c`), không phải với thư viện đang thiếu: hãy đọc "undefined reference" như "không archive nào được quét sau điểm này định nghĩa nó".

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
12. **(Thử thách)** Lặp lại bảng của mục "Phân giải archive như một điểm bất động" cho một hệ khác: `libP.a` có `p1.o` (định nghĩa `fp1`, cần `fq1`) và `p2.o` (định nghĩa `fp2`, cần `fq2`); `libQ.a` có `q1.o` (định nghĩa `fq1`, cần `fp2`) và `q2.o` (định nghĩa `fq2`); `main.o` cần `fp1`. Với mỗi lệnh `main.o -lP -lQ`, `main.o -lQ -lP`, `main.o -lP -lQ -lP` và `main.o -lP -lQ -lP -lQ`, lần vết $U$ và cho biết có link được không. Sau đó chứng minh rằng một `--start-group` trên các archive có tổng $M$ member cần nhiều nhất $M+1$ lượt quét, và cho biết CMake sinh ra gì với `main -> P`, `P <-> Q`. *(phỏng theo GNU ld manual, tùy chọn `--start-group`, và CMake docs, `target_link_libraries`, "Cyclic Dependencies of Static Libraries")*
13. **(Thử thách)** Static library `A` có `target_link_libraries(A PRIVATE B)` và `B` có `target_include_directories(B PUBLIC inc_b)`. File thực thi `m` link `A` ở dạng `PRIVATE` và `main.c` của nó chỉ gọi API của `A`. (a) `inc_b` có nằm trên dòng biên dịch của `m` không? (b) `libB.a` có nằm trên dòng link của `m` không? (c) Giải thích property nào của `A` làm (b) đúng dù (a) sai, và điều gì thay đổi nếu `A` là shared library. (d) `m.c` giờ cần một header từ `inc_b`: nêu thay đổi tối thiểu đúng đắn và cho biết phương án nào là thiết kế sai. *(nguồn: CMake docs, `target_link_libraries`, "Libraries for a Target and/or its Dependents", và generator expressions, `$<LINK_ONLY:...>`)*
14. **(Thử thách)** Một đồng đội viết `target_include_directories(core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)` và thêm `install(TARGETS core EXPORT coreTargets)` rồi `install(EXPORT coreTargets DESTINATION lib/cmake/core)`. Dự đoán CMake báo gì lúc generate và vì sao. Viết lại dòng include để cả consumer trong cây lẫn consumer đã cài đặt đều hoạt động, nêu đường dẫn mà mỗi consumer nhận được, và giải thích vì sao không thể giải quyết bằng "cứ dùng đường dẫn tương đối". *(nguồn: CMake docs, cmake-buildsystem(7), "Include Directories and Usage Requirements", và các generator expression `BUILD_INTERFACE`/`INSTALL_INTERFACE`)*
15. **(Thử thách)** Một dự án có 40 source, mỗi file 3 s. Một script `gen_config.py` tạo `config.h` từ `config.in`; 25 source include `config.h`. Công cụ build là Ninja với 8 job song song và rule biên dịch dùng depfile. (a) Bạn `touch config.in` nhưng script ghi lại `config.h` giống hệt từng byte. Có bao nhiêu lượt biên dịch chạy nếu rule sinh file không có `restat`, và bao nhiêu với `restat = 1`? Cho thời gian thực trong điều kiện xếp việc lý tưởng. (b) Vì sao một target chỉ cần `config.h` tồn tại trước khi bất kỳ lượt biên dịch nào bắt đầu nên dùng order-only dependency (`||`) thay vì phụ thuộc thường, và rủi ro của lựa chọn đó là gì? (c) Giả sử script thay vào đó ghi một timestamp mới và `config.h` đã thay đổi: giờ có bao nhiêu lượt biên dịch? *(nguồn: Ninja manual, biến rule `restat`, và "Order-only dependencies")*

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
12. Vết cho `main.o -lP -lQ`: $U=\{fp1\}$; `libP`: trích `p1.o` (định nghĩa `fp1`), $U=\{fq1\}$; `p2.o` chỉ định nghĩa `fp2`, không có trong $U$, bỏ qua. `libQ`: trích `q1.o`, $U=\{fp2\}$ (`q2.o` không cần). Kết thúc với `fp2` chưa định nghĩa: **thất bại** (`undefined reference to fp2`). `main.o -lQ -lP`: $U=\{fp1\}$; `libQ` không có gì cho $U$; `libP`: `p1.o`, $U=\{fq1\}$; thất bại (`fq1`). `main.o -lP -lQ -lP`: như lệnh đầu, rồi lượt `libP` thứ hai: `p2.o` định nghĩa `fp2`, được trích, $U=\{fq2\}$; hết archive: **thất bại** (`undefined reference to fq2`). `main.o -lP -lQ -lP -lQ`: lượt `libQ` thứ hai trích `q2.o`, $U=\emptyset$: **link được**. Vậy chuỗi này cần $P\,Q\,P\,Q$ dù đồ thị phụ thuộc $p1\to q1\to p2\to q2$ đổi bên bốn lần; mẫu hai archive `A B A` không khái quát thành "lặp một lần". Chứng minh cận cho nhóm: một lượt quét nhóm hoặc trích ra ít nhất một member chưa từng được trích, hoặc không trích gì và khi đó $U$ không đổi nên linker dừng. Mỗi trong $M$ member được trích nhiều nhất một lần, nên nhiều nhất $M$ lượt trích được gì đó, và một lượt cuối không trích gì: nhiều nhất $M+1$ lượt quét. Với `P <-> Q` CMake lặp lại thành phần liên thông mạnh, nên `main -> P` link `P Q P Q` (như ví dụ `A`, `B` trong tài liệu CMake), vừa đủ ở đây, nhưng tài liệu nói các sắp xếp bệnh lý có thể cần nhiều hơn và đưa ra `LINK_INTERFACE_MULTIPLICITY` hoặc gộp các archive. (Bảng `A`/`B` trước đó đã được tái hiện bằng gcc và `ar`: `-lA -lB` và `-lB -lA` thất bại, `-lA -lB -lA` và nhóm thì link được; và bốn lệnh của bài này cho đúng kết quả nêu trên.)
13. (a) Không: `PRIVATE` giữ usage requirement của `B` (kể cả include directory) khỏi các consumer của `A`. (b) Có: dòng link của `m` chứa `libA.a libB.a`. (c) Với `A` static, CMake lưu phụ thuộc private trong `INTERFACE_LINK_LIBRARIES` của `A` dưới dạng `$<LINK_ONLY:B>`: link `B`, nhưng không truyền usage requirement lúc biên dịch nào của nó, vì `libA.a` vẫn còn các tham chiếu chưa phân giải vào `B` khi `m` được link. Với `A` shared, property rỗng (đã kiểm tra với CMake 3.22), vì `B` đã được link vào thư viện shared. (d) Thay đổi tối thiểu đúng đắn: `target_link_libraries(m PRIVATE B)` trong CMake của chính `m`, nêu đúng phụ thuộc thật của `m.c` vào header của `B` và cấp cho nó `inc_b`. Thiết kế sai là đổi `A` thành `PUBLIC B` chỉ để đường dẫn include nhìn thấy được: mọi consumer của `A` khi đó phụ thuộc `B`, và interface của `A` làm rò rỉ một chi tiết cài đặt.
14. Lúc generate CMake dừng với lỗi rằng property `INTERFACE_INCLUDE_DIRECTORIES` của target chứa một đường dẫn "prefixed in the source directory" (tái hiện với CMake 3.22, "Generate step failed"). File được export sẽ chứa một đường dẫn tuyệt đối của máy build, sai trên mọi máy khác. Viết lại: `target_include_directories(core PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include> $<INSTALL_INTERFACE:include>)`. Consumer trong cây nhận đường dẫn source tuyệt đối; consumer đã cài đặt nhận một đường dẫn dưới install prefix, `<prefix>/include` (tùy chọn tương đương `INCLUDES DESTINATION include` được cmake-buildsystem(7) mô tả là thêm `${CMAKE_INSTALL_PREFIX}/include`; dòng đã viết lại đã được kiểm tra là configure không lỗi). Đường dẫn tương đối không giải quyết được vì "tương đối so với cái gì?" khác nhau: so với cây source khi build, so với install prefix sau khi cài. Đường dẫn tuyệt đối chỉ hợp lệ cho một trong hai trường hợp.
15. (a) Không có `restat`, Ninja coi `config.h` mới hơn các object cũ (script đã chạy), nên cả 25 source phụ thuộc biên dịch lại: $\lceil25/8\rceil=4$ đợt, mỗi đợt 3 s, khoảng 12 s thời gian thực (75 s thời gian CPU). Với `restat = 1`, Ninja stat lại `config.h` sau khi lệnh chạy; thời gian sửa đổi của nó không đổi, nên nó được coi như không cần build và các phụ thuộc ngược bị gỡ khỏi danh sách chờ: 0 lượt biên dịch, chỉ script tự chạy. (b) Order-only dependency nói "build cái này trước, nhưng chỉ riêng thay đổi của nó không làm output build lại". Đó là công cụ đúng để đảm bảo `config.h` tồn tại trước khi lượt biên dịch đầu tiên bắt đầu (phụ thuộc thật của lượt biên dịch vào nội dung header đến từ depfile do compiler phát hiện). Rủi ro: nếu cạnh order-only là liên kết duy nhất và không depfile nào ghi nhận include, thay đổi `config.h` sẽ không bao giờ kích hoạt biên dịch lại. (c) Một header thật sự đổi có thời gian sửa đổi mới; `restat` không giúp được, và cả 25 lượt biên dịch chạy lại (khoảng 12 s). (Kết quả suy ra từ định nghĩa `restat` và order-only dependency trong Ninja manual; tôi không chạy Ninja vì nó không được cài ở đây.)

## Đọc thêm

- [CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/index.html) - hướng dẫn từng bước: library, usage requirement, kiểm thử và cài đặt.
- [cmake-buildsystem(7)](https://cmake.org/cmake/help/latest/manual/cmake-buildsystem.7.html) - ngữ nghĩa chính xác của target, PUBLIC/PRIVATE/INTERFACE và usage requirement bắc cầu.
- [GNU Make Manual](https://www.gnu.org/software/make/manual/make.html) - rule, prerequisite và cách quyết định build lại.
- [GNU ld: command-line options](https://sourceware.org/binutils/docs/ld/Options.html) - `--start-group` và cách các archive được tìm.
- [`target_link_libraries`](https://cmake.org/cmake/help/latest/command/target_link_libraries.html) - link interface, PRIVATE/PUBLIC/INTERFACE, và các static library vòng.
- [cmake-generator-expressions(7)](https://cmake.org/cmake/help/latest/manual/cmake-generator-expressions.7.html) - `$<LINK_ONLY:...>`, `$<BUILD_INTERFACE:...>` và `$<INSTALL_INTERFACE:...>`.
- [The Ninja build system manual](https://ninja-build.org/manual.html) - `restat`, depfile và order-only dependency.

**Thực hành thêm:** [bước "Adding a Library" của CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/Adding%20a%20Library.html) và các bước tiếp theo (usage requirement, kiểm thử), trang tham chiếu [`target_link_libraries`](https://cmake.org/cmake/help/latest/command/target_link_libraries.html) (ngữ nghĩa PUBLIC/PRIVATE/INTERFACE, rồi làm lại bài tập 10), lời cảnh báo về [`file(GLOB)`](https://cmake.org/cmake/help/latest/command/file.html), [CTest manual](https://cmake.org/cmake/help/latest/manual/ctest.1.html), và [tài liệu graphlib](https://docs.python.org/3/library/graphlib.html) cho mô hình thứ tự build.
