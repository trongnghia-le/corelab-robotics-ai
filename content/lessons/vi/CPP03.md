---
{"title": "Quản lý tài nguyên: RAII, sở hữu duy nhất và move semantics", "summary": "Gắn mọi tài nguyên với một đối tượng sở hữu, làm cho quyền sở hữu hiện rõ trong kiểu dữ liệu, và chuyển nó bằng move thay vì copy.", "objectives": ["Phát biểu quy tắc RAII và giải thích vì sao nó đem lại exception safety.", "Biểu diễn quyền sở hữu độc quyền bằng value member, std::vector và std::unique_ptr thay cho new/delete.", "Cài đặt một class tài nguyên chỉ-move theo rule of five và để lại trạng thái moved-from hợp lệ.", "Chọn chữ ký hàm cho thấy quyền sở hữu là mượn, chuyển giao hay chia sẻ."]}
---
## Vì sao điều này quan trọng

Một tiến trình robot mở camera, cổng serial, buffer GPU, file log và mutex, và chạy hàng giờ liền. Mỗi thứ đó là một *tài nguyên* phải được giải phóng đúng một lần, ngay cả khi một exception, một `return` sớm, hoặc một lần đọc cảm biến thất bại khiến hàm dừng giữa chừng. Các cặp `new`/`delete` hay `open`/`close` viết tay đều hỏng đúng ở những đường đi này: rò rỉ một buffer nháp 2 KB mỗi chu kỳ điều khiển ở 100 Hz là 20 MB mỗi phút, và một double free có thể làm sập bộ điều khiển xe. C++ giải quyết chuyện này mà không cần garbage collector: đối tượng sở hữu tài nguyên giải phóng nó trong destructor, và ngôn ngữ đảm bảo destructor chạy khi scope kết thúc, dù bình thường hay do exception. Đây là RAII (resource acquisition is initialization, tức "chiếm tài nguyên là khởi tạo"). Move semantics sau đó cho phép quyền sở hữu di chuyển (được trả về từ factory, lưu vào container) mà không phải copy các buffer lớn.

## Trực giác

Hãy nghĩ đến một cuốn sách thư viện chỉ có đúng một thẻ mượn. RAII nói rằng cái thẻ chính là đối tượng: ai giữ thẻ thì có trách nhiệm trả sách, và thẻ không thể bị mất mà sách không được trả tự động. `std::unique_ptr` là một cái thẻ không thể photocopy nhưng có thể trao cho người khác. Con trỏ thô (raw pointer) là một tờ giấy nhớ ghi số kệ: nó cho biết cuốn sách ở đâu, nhưng không cho biết ai phải trả nó.

Trong code, các câu hỏi cần đặt ra với mọi con trỏ hay handle là: *ai sở hữu nó, ai chỉ được nhìn, và nó còn hợp lệ cho đến khi nào?* RAII biến câu trả lời thành kiểu dữ liệu: một value member hay `std::vector` sở hữu các phần tử của nó; `std::unique_ptr<T>` sở hữu độc quyền một `T`; `T&` và `T*` (khi là con trỏ thô) chỉ mượn.

Một trường hợp cụ thể: node thị giác của một robot di động nhận một khung RGB 1280 × 720, 2.764.800 byte, 15 lần mỗi giây. Một bản copy tốn 41,5 MB/s lưu lượng bộ nhớ; một pipeline copy khung ở ba giai đoạn (giải mã, khử méo, nhận diện) đẩy 124,4 MB/s qua bus bộ nhớ, và mỗi bản copy là một lần cấp phát mới có thể thất bại. Nếu khung là một khối heap có đúng một chủ sở hữu tại mỗi thời điểm, ba giai đoạn chỉ chuyền một handle: mỗi lần bàn giao là một phép gán con trỏ, và giai đoạn nào đang giữ handle khi có sự cố sẽ giải phóng khối trong lúc stack unwinding.

Hãy dự đoán trước khi đọc tiếp. Một hàm mở một đối tượng cổng serial rồi gọi một routine throw; một hàm gọi cách đó ba tầng bắt exception. Việc đóng cổng và dòng đầu tiên của khối catch chạy theo thứ tự nào, và bản thân hàm cần bao nhiêu dòng code dọn dẹp? Hãy ghi dự đoán ra; đáp án nằm sau hình.

Có hai trực giác sai đáng gọi tên. Thứ nhất là cho rằng `std::move` di chuyển thứ gì đó: nó chỉ ép kiểu, còn dữ liệu (nếu có) chỉ chuyển bên trong constructor hay phép gán mà phép ép kiểu đã chọn. Một đối tượng moved-from vẫn còn sống và bị hủy sau đó, nên nó phải được để lại ở trạng thái mà destructor xử lý được. Thứ hai là cho rằng smart pointer làm vấn đề sở hữu biến mất: `unique_ptr` chỉ loại bỏ rò rỉ và double free khi quyền sở hữu thực sự tạo thành một cây, chu trình `shared_ptr` rò rỉ lặng lẽ (xem tiểu mục lý thuyết cuối), và con trỏ thô lấy từ một smart pointer vẫn có thể treo (Core Guidelines R.37).

![Sơ đồ vòng đời: Buffer a sở hữu vùng nhớ, một phép move chuyển con trỏ sang b và để a rỗng, rồi cả hai destructor chạy an toàn](/lesson-figures/CPP03.svg)

*Một phép move chuyển con trỏ sở hữu và đặt nguồn về null, nên chỉ đúng một destructor giải phóng vùng nhớ.*

Đáp án cho dự đoán: cổng được đóng trước, khi exception còn đang đi lên trên stack, rồi mới đến dòng đầu của khối catch; hàm không cần dòng code dọn dẹp nào, vì destructor của cổng chính là phần dọn dẹp. Tiểu mục lý thuyết đầu tiên minh họa điều này bằng code đã biên dịch.

## Lý thuyết và suy dẫn

### RAII và thứ tự hủy

Một đối tượng cục bộ bị hủy khi scope của nó kết thúc, theo thứ tự ngược với thứ tự khởi tạo. Destructor chạy trong quá trình **stack unwinding** (tháo ngăn xếp) nếu có exception lan truyền. Vì vậy tài nguyên do một đối tượng cục bộ sở hữu được giải phóng trên mọi đường thoát mà không cần `finally`. Các member bị hủy theo thứ tự ngược với thứ tự khai báo, sau phần thân destructor. Destructor không được throw (nó mặc định là `noexcept`).

**Ví dụ.** Một routine telemetry mở cổng IMU, rồi cổng GPS, rồi gặp một gói dữ liệu hỏng và throw (biên dịch và chạy với g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

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

```text
open  imu0
open  gps1
close gps1
close imu0
caught: bad checksum
```

Các cổng đóng theo thứ tự `gps1`, `imu0`, ngược với thứ tự mở, và cả hai lần đóng diễn ra trước khi handler in ra; `run` không chứa câu lệnh dọn dẹp nào. Đây là [except.ctor] ¶2 của chuẩn C++: mỗi đối tượng automatic đã được xây xong bị hủy, theo thứ tự ngược với thứ tự hoàn tất việc xây, khi quyền điều khiển chuyển tới handler (xem thêm Core Guidelines E.6).

![Dòng thời gian của run(): imu0 và gps1 mở, một exception bị throw, gps1 rồi imu0 đóng trong lúc stack unwinding, main bắt lỗi](/lesson-figures/CPP03-2.svg)

*Hình: các vòng đời lồng nhau như dấu ngoặc, nên tài nguyên mở sau cùng được đóng đầu tiên; vùng tô bóng là đoạn unwinding giữa lúc throw (3) và lúc kết thúc scope của `run` (5).*

### Rule of zero, three, five

- **Rule of zero**: nếu class của bạn chỉ sở hữu tài nguyên thông qua các member vốn đã tự quản lý chúng (`std::vector`, `std::string`, `std::unique_ptr`), hãy viết *không* hàm thành viên đặc biệt nào. Những hàm do compiler sinh ra là đúng. Hãy ưu tiên cách này.
- **Rule of three/five**: nếu bạn buộc phải quản lý một tài nguyên thô, hãy định nghĩa hoặc xóa (delete) tất cả: destructor, copy constructor, copy assignment, move constructor, move assignment. Một class có destructor giải phóng bộ nhớ nhưng copy mặc định sẽ có hai đối tượng cùng sở hữu một con trỏ: double free.

**Ví dụ.** `RawLog` sở hữu 5 double qua một con trỏ thô và không định nghĩa phép copy nào; `Log` chứa một `std::vector` và một `std::string` và không định nghĩa special member nào cả. Mỗi loại được copy một lần (thông báo chẩn đoán đi vào `stderr`; g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

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

```text
Log copy shares storage:    0
RawLog copy shares storage: 1
==PID==ERROR: AddressSanitizer: attempting double-free on 0x... in thread T0:   (shortened)
```

Bản copy của `Log` có vùng nhớ riêng, vì các member biết tự copy: rule of zero (Core Guidelines C.20) không tốn gì. Bản copy của `RawLog` dùng chung khối 40 byte với bản gốc, và khi cả hai ra khỏi scope, AddressSanitizer báo lần `delete[]` thứ hai trên cùng địa chỉ là double free, đúng điều mà C.21 (định nghĩa hoặc xóa cả năm hàm cùng nhau) ngăn chặn.

### Value category và move

**Lvalue** có tên và danh tính; **rvalue** là một giá trị tạm hoặc thứ bạn hứa sẽ không dùng lại. `std::move(x)` không di chuyển gì cả: nó là một phép ép kiểu (cast) sang rvalue reference, cho phép overload `T(T&&)` được chọn. Một move constructor nên (1) lấy cắp tài nguyên, (2) để nguồn ở trạng thái **hợp lệ nhưng không xác định (valid but unspecified)**, thường là rỗng, để destructor và phép gán của nó vẫn hoạt động, và (3) là `noexcept`.

Với buffer sở hữu dùng trong bài này:

$$\text{move: } \underbrace{\texttt{data\_}}_{\text{dst}} \leftarrow \texttt{src.data\_}, \quad \texttt{src.data\_} \leftarrow \texttt{nullptr}$$

Chi phí: copy $n$ double tốn $O(n)$ thời gian và $8n$ byte; một move là $O(1)$ (hai phép gán).

Vì sao `noexcept` quan trọng: khi `std::vector` phải tăng dung lượng, nó di dời (relocate) các phần tử. Để giữ strong exception guarantee, nó dùng `std::move_if_noexcept`: nếu move constructor có thể throw và kiểu đó cũng copy được, nó sẽ *copy* thay vì move. Quên `noexcept` lặng lẽ biến các phép di dời $O(1)$ thành các phép copy $O(n)$.

**Ví dụ.** Một logger giữ 6000 mẫu (48.000 byte) trong một `std::vector<double>` và giao toàn bộ bản ghi cho một uploader. `std::move` chỉ là phép ép kiểu; constructor move của vector mới làm việc (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

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

```text
w.data() == old v.data(): 1
v.size() = 0, w.size() = 6000
after push_back: v.size() = 1
```

`w` có đúng khối nhớ đó (hai con trỏ data so sánh bằng nhau), nên phép move tốn hai phép ghi cỡ con trỏ và không copy 48.000 byte nào. `v` rỗng với thư viện này và vẫn nhận `push_back`: chuẩn chỉ bảo đảm trạng thái hợp lệ nhưng không xác định cho đối tượng moved-from, nên code portable chỉ nên gán lại hoặc hủy nó, không đọc từ nó.

### Giá trị trả về và `std::move`

`return local;` đã coi `local` là rvalue và cho phép copy elision (NRVO). Viết `return std::move(local);` phá NRVO và ép một phép move, và compiler sẽ cảnh báo (`-Wpessimizing-move`). Chỉ dùng `std::move` khi truyền một lvalue mà bạn sẽ không dùng lại.

**Ví dụ.** Một kiểu pose nhỏ đếm số lần copy và move. Ba hàm trả về một biến cục bộ theo các cách khác nhau (g++ 11.4.0, `-std=c++20 -Wall -Wextra`, không tối ưu hóa):

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

```text
warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
two named returns : copies=0 moves=1
conditional expr  : copies=1 moves=0
return std::move  : copies=0 moves=1
```

Hai return có tên vẫn tốn một phép move: khi hàm trả về các biến cục bộ khác nhau, không có đối tượng duy nhất nào được dựng thẳng vào vùng nhớ của bên gọi, nên compiler quay về phép implicit move của [class.copy.elision] ¶3 (tên được trả về trước hết được xử lý như một rvalue). Biểu thức điều kiện `f ? a : b` không phải một tên đơn thuần, nên quy tắc đó không áp dụng và kiểu bị *copy*. `return std::move(a)` tốn một phép move và gây ra cảnh báo ở trên. Nguyên tắc vẫn là: trả về biến cục bộ bằng tên của nó.

### Quyền sở hữu trong chữ ký hàm

| Ý định | Chữ ký | Ý nghĩa |
|---|---|---|
| Dùng, không giữ | `const Frame&`, `Frame&` | bên mượn, bên gọi giữ quyền sở hữu |
| Mượn tùy chọn | `const Frame*` | có thể null, vẫn không sở hữu |
| Nhận quyền sở hữu | `std::unique_ptr<Frame>` truyền theo giá trị | bên gọi phải `std::move` vào |
| Trao quyền sở hữu | trả về `std::unique_ptr<Frame>` | bên gọi sở hữu kết quả |
| Vòng đời chia sẻ | `std::shared_ptr<const Frame>` | đếm tham chiếu, dùng dè xẻn |

Dùng `std::make_unique<T>(args...)`; nó an toàn với exception và tránh `new` trần. Với các API của C, hãy cho `unique_ptr` một custom deleter: `std::unique_ptr<FILE, int(*)(FILE*)> f(fopen(p, "r"), &fclose);`.

**Ví dụ.** Một pipeline giữ nguồn video trong suốt đời của nó, còn `show` chỉ nhìn nó (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

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

```text
show(42)
caller's pointer is null: 1, pipeline holds id 42
```

`show(const Source&)` chỉ mượn, nên bên gọi vẫn giữ `s`; `set_source(std::unique_ptr<Source>)` nhận quyền sở hữu, và chỗ gọi phải viết `std::move(s)`, nên việc bàn giao hiện rõ và sau đó `s` là null (được bảo đảm với `unique_ptr`). Viết `set_source(s)` thì không biên dịch được: g++ báo `use of deleted function 'std::unique_ptr<...>::unique_ptr(const std::unique_ptr<...>&)'`. Đó là các quy tắc F.7, R.32 và R.33 của Core Guidelines được thực thi bởi compiler.

### Wrapper RAII cho handle của C: custom deleter và scope guard

Không phải tài nguyên nào cũng là bộ nhớ. Một thư viện C đưa ra `FILE*`, file descriptor hay một handle không trong suốt cùng một hàm giải phóng (`fclose`, `close`, một `dev_close` của nhà sản xuất). Hai wrapper đủ cho các trường hợp, và việc chọn phụ thuộc vào việc dọn dẹp là gì. Nếu đó là *giải phóng một handle*, hãy cho `std::unique_ptr<T, D>` một kiểu deleter `D`; destructor của nó gọi `D` trên con trỏ đang giữ khi con trỏ đó không null (cppreference: `std::unique_ptr`; chuẩn C++ [unique.ptr]). Deleter là một function object không có trạng thái thì không chiếm chỗ trong smart pointer, còn con trỏ hàm thì được lưu lại và làm kích thước tăng gấp đôi. Nếu việc dọn dẹp là *một hành động tùy ý*, chẳng hạn hoàn tác một bước làm dở, thì scope guard lưu một callable và chạy nó trong destructor trừ khi đã bị dismiss: đó là `ScopeGuard` trong cài đặt tham khảo, và Core Guidelines E.19 khuyến nghị đúng điều này (`gsl::finally`) khi không có lớp resource-handle phù hợp.

Mẫu commit/rollback là cách dùng quan trọng: kích hoạt guard trước, làm phần việc có thể throw, gọi `dismiss()` cuối cùng. Cần hai lưu ý. Callable chạy bên trong destructor nên không được throw (E.16, C.36). Và lambda capture theo tham chiếu không được sống lâu hơn thứ nó tham chiếu, nên guard được khai báo sau các đối tượng mà lambda của nó dùng. Hãy ưu tiên một lớp thật có destructor (E.6) mỗi khi tài nguyên xứng đáng có tên riêng.

**Ví dụ.** Một bước hiệu chuẩn phải rollback kết quả dở dang khi cảm biến quá thời gian, và một `FILE*` cần một deleter (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

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

```text
commit 1
rollback 2
caught: sensor timeout
unique_ptr<FILE, int(*)(FILE*)>: 16 bytes
unique_ptr<FILE, FileCloser>:    8 bytes
unique_ptr<int>:                 8 bytes
```

Giai đoạn 1 chạy tới `g.on = false`, nên chỉ có thông báo commit. Ở giai đoạn 2, lệnh throw bỏ qua dòng đó và destructor của guard in ra rollback trước khi handler chạy. Các dòng kích thước cho thấy giá của lựa chọn deleter: deleter dạng con trỏ hàm làm smart pointer thành 16 byte, lớp rỗng `FileCloser` giữ nó ở 8 byte, bằng một con trỏ thường.

### Các mức exception safety, copy-and-swap, và vì sao vector kiểm tra `noexcept`

Một thao tác có thể đưa ra một trong ba đảm bảo: **basic** (không rò rỉ, mọi invariant còn đúng, nhưng giá trị có thể đã đổi), **strong** (nếu throw thì trạng thái quan sát được y hệt trước đó: hoặc commit hoặc rollback) và **nothrow** (không thể throw). Copy assignment ngây thơ

```cpp
Buffer& operator=(const Buffer& o) {   // WRONG even for the basic guarantee
  delete[] data_;
  data_ = new double[o.size_];          // may throw: data_ now dangles
  std::copy(o.data_, o.data_ + o.size_, data_); size_ = o.size_; return *this;
}
```

hỏng hai lần: `new` có thể throw sau khi vùng nhớ cũ đã mất (`data_` treo mà destructor sẽ delete lần nữa), và `b = b` copy từ vùng nhớ đã giải phóng. Cách sửa là một quy tắc về thứ tự: **làm mọi việc có thể throw trước, trên một đối tượng tạm; rồi commit bằng những thao tác không thể throw.** Copy-and-swap đóng gói quy tắc đó:

```cpp
friend void swap(Buffer& a, Buffer& b) noexcept { std::swap(a.data_, b.data_); std::swap(a.size_, b.size_); }
Buffer& operator=(Buffer o) noexcept { swap(*this, o); return *this; }   // o is taken by value
```

*Chứng minh strong guarantee.* Tham số `o` được khởi tạo trước khi thân hàm chạy: bằng copy constructor nếu đối số là lvalue, bằng move constructor nếu là rvalue. Nếu phép copy throw thì thân hàm không bao giờ chạy, nên `*this` không bị đụng tới. Nếu thành công, `swap` chỉ đổi một con trỏ và một số nguyên nên không thể throw; sau đó `o` giữ nội dung cũ và destructor của nó giải phóng chúng. Self-assignment đúng mà không cần kiểm tra vì `o` là một bản sao độc lập. Vì vậy một hàm duy nhất phục vụ cả copy- lẫn move-assignment (value category của đối số chọn constructor), gộp hai phép gán của rule of five làm một (so sánh C++ Core Guidelines, C.21, C.65 và C.66).

Chi phí và giới hạn: `a = b` luôn cấp phát, kể cả khi `a` đã đủ dung lượng, trong khi `std::vector::operator=` tái sử dụng vùng nhớ; toán tử hợp nhất cũng bị *mơ hồ* (ambiguous) nếu bạn khai báo thêm `operator=(const Buffer&)`, vì `a = b` khớp cả hai như nhau. Dùng copy-and-swap khi sự rõ ràng và strong guarantee quan trọng hơn lần cấp phát cuối cùng.

**Ví dụ.** Một bảng hiệu chuẩn 7 double bị ghi đè bằng một bảng 4 double trong khi một lỗi được chèn vào làm copy constructor throw một lần (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

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

```text
threw: copy failed
a after failed a = b: size=7 a[0]=1.5
a after a = b       : size=4 a[0]=9.0
```

Phép gán đầu thất bại ngay trong lúc dựng tham số truyền theo giá trị, trước khi `swap` chạy, nên `a` giữ nguyên 7 phần tử và giá trị đầu của nó: strong guarantee, được quan sát trực tiếp. Phép gán thứ hai thành công và bảng trở thành bảng mới, trong một lần duy nhất.
*Vì sao `std::vector` hỏi về `noexcept`.* Để tăng dung lượng, vector phải relocate $n$ phần tử sang vùng nhớ mới và hứa rằng nếu có gì throw thì vector cũ vẫn nguyên vẹn. Giả sử nó move và lần move thứ $k$ throw: các phần tử $1,\dots,k-1$ đã bị "cướp" nội dung, và đặt chúng về chỗ cũ cần thêm $k-1$ phép move, mà chúng cũng có thể throw, nên không tồn tại rollback. Copy để nguồn nguyên vẹn, nên khi lần copy thứ $k$ throw, vector chỉ hủy $k-1$ bản sao mới và giải phóng khối mới. Do đó `std::move_if_noexcept` chỉ trả về rvalue nếu move không thể throw *hoặc* kiểu không copy được; trường hợp sau thì đảm bảo bị bỏ (cppreference: `std::move_if_noexcept`; `std::vector::emplace_back`, mục "Exceptions").

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

*Hình: đường bậc thang màu cam là $2^{\lceil\log_2 m\rceil}-1$ (di dời ở các kích thước 1, 2, 4, ..., mỗi lần copy bằng ấy phần tử; đo được 31 lần copy cho 20 lần push với libstdc++ của g++ 11.4.0). Với move `noexcept` số copy giữ ở 0 và mỗi lần di dời chỉ là một phép move rẻ.*

### Constructor throw thì dọn gì: đối tượng xây dở

Nếu một constructor thoát bằng exception thì destructor của đối tượng đó **không** chạy, vì đối tượng chưa bao giờ hoàn tất. Ngôn ngữ chỉ hủy các subobject cơ sở và member *đã xây xong*, theo thứ tự ngược. Vậy với

```cpp
struct Raw { double* a; double* b;
  Raw() : a(new double[100]), b(new double[200]) { risky(); }   // risky() throws
  ~Raw() { delete[] a; delete[] b; } };
```

cả hai mảng đều rò rỉ ($100\cdot8+200\cdot8=2400$ byte): member là con trỏ thô, "hủy" chúng không làm gì cả, còn `~Raw` bị bỏ qua. Nếu chính initializer của `b` throw thì `a` đã được cấp phát và rò rỉ ($800$ byte). Nguyên tắc "một tài nguyên, một chủ sở hữu" (E.6, R.13) chính là điều này: khi mỗi tài nguyên do một member object riêng giữ (`std::unique_ptr<double[]> a, b;`), việc dọn dẹp các member đã hoàn tất của ngôn ngữ sẽ giải phóng mọi thứ đã chiếm được, trên mọi đường thoát, mà bạn không phải viết code nào. Đừng bao giờ đặt hai lần chiếm tài nguyên thô trong một constructor hay một câu lệnh biểu thức.

**Ví dụ.** Hai member có constructor và destructor nhìn thấy được, và một thân constructor throw (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

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

```text
+a +b [body] -b -a caught
```

Cả hai member đã được xây xong hoàn toàn, nên chúng bị hủy theo thứ tự ngược (`-b -a`), còn `~Holder` không bao giờ chạy, đúng như [except.ctor] ¶3 quy định. Chi phí của owner thô được đo bằng một `operator new[]` có đếm; lớp thứ nhất lấy 5 và 7 double bằng `new`, lớp thứ hai giữ chúng trong `unique_ptr<double[]>` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

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

```text

=================================================================
==301332==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 72 byte(s) in 1 object(s) allocated from:
    #0 0x707eb18b4887 in __interceptor_malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:145
    #1 0x6264c3bc4420 in operator new[](unsigned long) (/tmp/claude-1000/-home-tronghia-corelab/59927611-c392-43c8-9f6b-6c609caf863b/scratchpad/pass/cpp0304/ex03/e7b.bin+0x4420)
    #2 0x6264c3bc4867 in Raw::Raw() (/tmp/claude-1000/-home-tronghia-corelab/59927611-c392-43c8-9f6b-6c609caf863b/scratchpad/pass/cpp0304/ex03/e7b.bin+0x4867)
    #3 0x6264c3bc4634 in main (/tmp/claude-1000/-home-tronghia-corelab/59927611-c392-43c8-9f6b-6c609caf863b/scratchpad/pass/cpp0304/ex03/e7b.bin+0x4634)
    #4 0x707eb0829d8f in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58

Direct leak of 56 byte(s) in 1 object(s) allocated from:
    #0 0x707eb18b4887 in __interceptor_malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:145
    #1 0x6264c3bc4420 in operator new[](unsigned long) (/tmp/claude-1000/-home-tronghia-corelab/59927611-c392-43c8-9f6b-6c609caf863b/scratchpad/pass/cpp0304/ex03/e7b.bin+0x4420)
    #2 0x6264c3bc480a in Raw::Raw() (/tmp/claude-1000/-home-tronghia-corelab/59927611-c392-43c8-9f6b-6c609caf863b/scratchpad/pass/cpp0304/ex03/e7b.bin+0x480a)
    #3 0x6264c3bc4634 in main (/tmp/claude-1000/-home-tronghia-corelab/59927611-c392-43c8-9f6b-6c609caf863b/scratchpad/pass/cpp0304/ex03/e7b.bin+0x4634)
    #4 0x707eb0829d8f in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58

SUMMARY: AddressSanitizer: 128 byte(s) leaked in 2 allocation(s).
```

Phiên bản thô mất $5\cdot8+7\cdot8=96$ byte mỗi lần xây dựng thất bại, phiên bản `unique_ptr` không mất byte nào.

![Trái: trình tự với Holder, b rồi a bị hủy và ~Holder bị bỏ qua. Phải: số byte còn cấp phát, 96 B với con trỏ thô (40 B + 56 B), 0 B với member unique_ptr](/lesson-figures/CPP03-3.svg)

*Hình: bên trái, những gì ngôn ngữ hủy khi constructor throw; bên phải, số byte còn cấp phát của hai lớp trong ví dụ, kèm phần đóng góp của từng member.*

### Sở hữu chia sẻ: control block, chu trình, aliasing

Một `std::shared_ptr` gồm hai con trỏ: một tới đối tượng và một tới **control block**, nơi lưu strong count (số chủ sở hữu), weak count (số người quan sát), deleter đã xóa kiểu (type-erased) và, nếu tạo bằng `make_shared`, chính đối tượng trong cùng một lần cấp phát (cppreference: `std::shared_ptr`, "Implementation notes"). Copy tăng strong count bằng một phép atomic, hủy thì giảm, và đối tượng bị hủy khi strong count về 0; control block được giải phóng khi weak count cũng về 0. Hệ quả:

- *Chi phí.* Mỗi lần truyền `shared_ptr` theo giá trị là một phép atomic đọc-sửa-ghi, nên guideline nói chỉ nhận smart pointer làm tham số khi muốn diễn đạt lifetime semantics (R.30), còn lại thì truyền reference tới đối tượng được trỏ (R.32, R.33); R.37 cảnh báo đừng đưa cho callee một con trỏ thô hay reference lấy từ một smart pointer mà thứ khác có thể reset.
- *Chu trình.* Nếu `A` sở hữu `B` qua `shared_ptr` và `B` sở hữu `A`, thì mỗi đối tượng có strong count 2 khi hai biến cục bộ còn tham chiếu; khi biến cục bộ chết, count giảm xuống 1, không bao giờ về 0, và cả hai rò rỉ mà destructor không bao giờ chạy. Liên kết ngược không sở hữu phải là `std::weak_ptr` (R.24), chỉ đổi thành chủ sở hữu tạm bằng `lock()` khi đang dùng.
- *Aliasing.* Aliasing constructor `shared_ptr<int>(p, &p->y)` dùng chung control block của `p` nhưng trỏ vào một member: member sống chừng nào còn alias, kể cả sau khi chính `p` bị reset.

**Ví dụ.** Một ước lượng pose được chia sẻ cho ba bên dùng và được một node chẩn đoán theo dõi mà không được giữ nó sống (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`):

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

```text
use_count = 3
after two resets: 1
lock() ok, count = 2
expired = 1, lock() null = 1
sizeof(shared_ptr<Pose>) = 16
```

Hai bản copy nâng strong count từ 1 lên 3; `weak_ptr` không được tính. Trong khi kết quả `lock()` còn được giữ, count là 2 (chủ sở hữu cộng bản tạm), và sau khi chủ sở hữu cuối cùng reset, `expired()` là true và `lock()` trả về null, nên bên quan sát biết đối tượng đã mất thay vì giữ con trỏ treo. 16 byte là hai con trỏ (tới đối tượng và tới control block) đã mô tả ở trên.

## Ví dụ có lời giải


### Ca 1: lần theo một phép move và một `Buffer` trên heap

**Đề bài.** `Buffer` của cài đặt tham khảo đếm các đối tượng còn sống trong `Buffer::alive` (ban đầu là 0). Hãy lần theo

```cpp
Buffer a = make_ramp(3);   // (1)
Buffer b = std::move(a);   // (2)
{
  auto p = std::make_unique<Buffer>(2);  // (3)
}                          // (4)
```

và cho biết `alive` sau mỗi câu lệnh, trạng thái của `a` sau (2), và khối vùng nhớ tạo ở (1) được giải phóng mấy lần.

**Lời giải.**

1. *Câu lệnh (1).* `make_ramp(3)` dựng `Buffer b(3)` bên trong hàm; nhờ elision đối tượng được dựng thẳng vào `a` (constructor tăng `alive`). Vùng nhớ `[0,1,2]` tại địa chỉ `A`: `a.data_ = A`, `a.size_ = 3`, `alive = 1`.
2. *Câu lệnh (2).* `Buffer(Buffer&&)` được chọn vì `std::move(a)` là một rvalue (lý thuyết: value category và move). Nó thực hiện hai phép gán của công thức move: `b.data_ = a.data_ = A`, `b.size_ = 3`, rồi `a.data_ = nullptr`, `a.size_ = 0`. Constructor vẫn tăng `alive`, nên `alive = 1 + 1 = 2`: một đối tượng moved-from vẫn là một đối tượng.
3. *Câu lệnh (3).* `std::make_unique<Buffer>(2)` cấp phát đối tượng `Buffer` trên heap, và constructor của nó cấp phát 2 double: `alive = 3`.
4. *Câu lệnh (4).* Ở dấu ngoặc đóng, `p` bị hủy: `unique_ptr` xóa `Buffer`, destructor của nó giải phóng 2 double và giảm bộ đếm: `alive = 2`.
5. *Cuối scope bao ngoài.* Destructor chạy theo thứ tự ngược với thứ tự khởi tạo ([except.ctor]; lý thuyết: RAII và thứ tự hủy). `b` trước: `delete[] A`, `alive = 1`. Rồi `a`: `delete[] nullptr`, ngôn ngữ định nghĩa là không làm gì, `alive = 0`.

**Kiểm tra.** Biên dịch chương trình với `Buffer` tham khảo (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`) và in `alive` sau mỗi câu lệnh cho `alive` = 1, 2, 3, 2 ở (1) đến (4), cùng `a.size()` = 0 và `b.size()` = 3 sau (2); AddressSanitizer không báo lỗi, nên `A` được giải phóng đúng một lần. Nếu thiếu `a.data_ = nullptr` ở bước 2, bước 5 sẽ giải phóng `A` hai lần.

**Rút ra.** Một phép move là hai phép ghi con trỏ cộng với việc đặt null, và chính việc đặt null cho phép hai destructor cùng tồn tại.

### Ca 2: số đếm và thứ tự hủy với `shared_ptr` và `weak_ptr`

**Đề bài.** Một `Imu` được `Filter` và `Logger` chia sẻ; `Logger` còn giữ một `weak_ptr` tới `Filter` để chẩn đoán. Mỗi lớp in tên của nó trong destructor. Hãy cho mọi giá trị `use_count()` được in và thứ tự chính xác của các dòng destructor.

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

**Lời giải.** `use_count()` của một `shared_ptr` là số chủ sở hữu strong (lý thuyết: sở hữu chia sẻ); `weak_ptr` và control block không được tính. Biến cục bộ bị hủy theo thứ tự ngược với khai báo.

1. Sau khi `imu` được tạo, count của nó là 1. Dòng `f->imu = imu;` thêm chủ sở hữu `Filter::imu`: `imu` count 2, `f` count 1 (in ra `(1) imu=2 f=1`).
2. Trong khối, `lg->imu = imu` thêm chủ sở hữu `Logger::imu`: count 3; `lg->f = f` lưu một `weak_ptr`, nên `f` vẫn là 1; bản thân `lg` có count 1 (in ra `(2) imu=3 f=1 lg=1`).
3. `lg->f.lock()` tạo chủ sở hữu tạm `locked`: `f` count 2 (in ra `(3) f=2`).
4. Ở dấu ngoặc đóng, `locked` bị hủy trước (khai báo sau cùng): `f` về 1. Rồi `lg`: count của nó giảm từ 1 xuống 0, `~Logger` chạy và giải phóng `Logger::imu`: `imu` count 2 (in ra `(4) imu=2 f=1`, sau dòng `~Logger`).
5. `imu.reset()` giải phóng chủ sở hữu cục bộ: chủ sở hữu duy nhất còn lại là `Filter::imu`, nên `f->imu.use_count()` là 1 (in ra `(5)`).
6. `f.reset()` đưa count của `f` từ 1 về 0: `~Filter` chạy, rồi member `imu` bị hủy (member bị hủy sau thân destructor), đưa count của `Imu` về 0: `~Imu`. Thứ tự in ra `~Filter`, `~Imu`, rồi `(6) end`.

![Ba đồ thị sở hữu ở bước 3, 4 và 5: strong count của Imu là 3, 2, 1; Filter 2 rồi 1; Logger chỉ sống ở bước 3, có liên kết weak tới Filter](/lesson-figures/CPP03-4.svg)

*Hình: strong count của chương trình sau các bước (3), (4) và (5); mũi tên nét đứt là `weak_ptr`, không thêm count.*

**Kiểm tra.** Biên dịch với g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`, chương trình in chính xác

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

khớp với mọi số ở trên; AddressSanitizer im lặng. Lập luận độc lập: tổng strong count trong hình bằng số mũi tên liền cộng số biến cục bộ, ở bước 3 là 3 cho `Imu` (`imu`, `Filter`, `Logger`).

**Rút ra.** Số đếm chỉ đổi khi chủ sở hữu được copy, reset hoặc bị hủy, và `weak_ptr` quan sát mà không sở hữu, nên đồ thị các mũi tên strong phải không có chu trình thì mọi thứ mới được giải phóng.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: C++ Core Guidelines, R.1 and E.6)* Giải thích trong ba câu vì sao một hàm khóa mutex qua `std::lock_guard` là an toàn nếu code sau lệnh khóa throw, trong khi `m.lock(); ...; m.unlock();` thì không.
2. **(Dễ)** Dự đoán output (mỗi `Tag` in `+name` khi được dựng và `-name` khi bị hủy):
   ```cpp
   struct Tag { std::string n; Tag(std::string s) : n(s) { std::cout << "+" << n << ' '; }
                ~Tag() { std::cout << "-" << n << ' '; } };
   int main() { Tag a("a"); { Tag b("b"); Tag c("c"); } Tag d("d"); }
   ```
3. **(Dễ)** Một vòng điều khiển 100 Hz chạy 10 phút. Ở một đường return sớm được đi qua trong một trên bốn chu kỳ, nó quên `delete[]` một buffer nháp 256 double. Bao nhiêu byte bị rò rỉ? Vì sao một leak checker chỉ báo ở lúc thoát, và vì sao đó vẫn là bug trên robot?
4. **(Trung bình)** Tìm lỗi và nêu ba cách sửa khác nhau.
   ```cpp
   class Scan {
     double* d_;
    public:
     explicit Scan(size_t n) : d_(new double[n]) {}
     ~Scan() { delete[] d_; }
   };
   void f() { Scan a(10); Scan b = a; }
   ```
5. **(Trung bình)** Dự đoán output và nói tiêu chuẩn đảm bảo điều gì về `p` sau đó:
   ```cpp
   auto p = std::make_unique<int>(7);
   auto q = std::move(p);
   std::cout << (p == nullptr) << *q;
   ```
6. **(Trung bình)** *(Adapted from: C++ Core Guidelines, R.30-R.33 and F.7)* Với mỗi trường hợp sau, chọn kiểu tham số từ bảng ở trên và biện minh: (a) `draw(frame)` vẽ một frame camera rồi trả về; (b) `Pipeline::set_source(...)` lưu nguồn frame trong suốt đời của nó; (c) `log_async(frame)` giao một frame cho một thread có thể sống lâu hơn bên gọi; (d) một hàm có thể có hoặc không có một calibration để áp dụng.
7. **(Trung bình)** *(Adapted from: LearnCpp, chapter on move semantics, returning by value)* Cho `struct C { C(C&&) noexcept; ... };`, dự đoán move constructor chạy bao nhiêu lần với `C a = f1();` trong đó `C f1() { C c; return c; }` và với `C f2() { C c; return std::move(c); }`, dùng GCC 11 ở `-O0` trong C++17. Giải thích sự khác biệt và cách nào được ưu tiên.
8. **(Khó)** Chi phí tăng trưởng. Hai kiểu giống hệt nhau trừ việc `W(W&&) noexcept` và `V(V&&)` (không `noexcept`, nhưng copy được). Cả hai đều đếm số lần copy và move. Dự đoán các số đếm sau `for (int i = 0; i < 4; ++i) v.push_back(W());` trên một vector bắt đầu rỗng và nhân đôi dung lượng (1, 2, 4), rồi với `V`. Giải thích cơ chế.
9. **(Khó)** Suy dẫn vì sao toán tử move-assignment `Buffer& operator=(Buffer&& o) { delete[] data_; data_ = o.data_; size_ = o.size_; o.data_ = nullptr; o.size_ = 0; return *this; }` sai với `b = std::move(b)` và chỉ ra trạng thái cuối của `data_`. Sau đó sửa theo hai cách: bằng kiểm tra danh tính (identity check), và bằng swap idiom (`std::swap(data_, o.data_)`); nói mỗi cách để lại gì trong `o`.
10. **(Khó)** Thiết kế. Một callback subscriber kiểu ROS nhận một frame camera 1 MB ở 30 Hz. Một thread planner cần frame mới nhất trong tối đa 200 ms sau khi nó đến, trong khi driver tái sử dụng buffer của nó. So sánh (i) copy vào một member mỗi lần, (ii) `shared_ptr<const Frame>`, (iii) một pool các `unique_ptr<Frame>` được bàn giao bằng `std::move`. Cho băng thông copy của (i) và rủi ro chính của từng phương án.
11. **(Mini-project)** Bọc một API thiết bị C giả (`int dev_open(int id); void dev_close(int h);`, với một bộ đếm toàn cục các handle đang mở) trong một class `Device` chỉ-move, cộng với một biến thể dùng `unique_ptr` với custom deleter. Viết các test cho thấy bộ đếm handle đang mở trở về 0 sau khi thoát bình thường, sau một exception được throw, và sau khi move một device vào `std::vector`.

12. **(Thử thách)** Copy-and-swap, định lượng. Lấy `Buffer& operator=(Buffer o) noexcept { swap(*this, o); return *this; }` với copy constructor có cấp phát và move constructor "cướp". `a` giữ 1000 double và `b` giữ 500. (a) Chứng minh rằng nếu copy constructor throw trong `a = b` thì `a` không đổi. (b) Cho số lần copy, move và cấp phát heap của `a = b`, rồi `a = std::move(b)`, rồi `a = a`. (c) Nói chính xác `b` và `a` giữ gì sau mỗi trường hợp. (d) Vì sao thêm overload thứ hai `operator=(const Buffer&)` làm hỏng `a = b`, và khi nào bạn vẫn ưu tiên nó? (phỏng theo C++ Core Guidelines, C.65 và C.66, và cppreference "Rule of three/five")
13. **(Thử thách)** Hai nút `A` và `B` của một đồ thị giữ nhau qua `std::shared_ptr<Cyc> other;`, cả hai tạo bằng `make_shared` trong một scope bên trong. (a) Cho `use_count()` của mỗi nút khi cả hai biến cục bộ còn sống, và output của destructor sau khi scope kết thúc. (b) Đổi một liên kết thành `std::weak_ptr` và cho các count và thứ tự destructor khi `A` sở hữu `B`. (c) Với `struct P { int x, y; }; auto p = std::make_shared<P>(); std::shared_ptr<int> y(p, &p->y);` cho `p.use_count()` và `y.use_count()`, rồi sau `p.reset()`. Giải thích cái gì được giữ sống và vì sao an toàn. (nguồn: cppreference, std::shared_ptr, control block và aliasing constructor; C++ Core Guidelines, R.24)
14. **(Thử thách)** Kế toán rò rỉ trong constructor. Với `struct Raw { double *a, *b; Raw() : a(new double[30]), b(new double[90]) { risky(); } ~Raw() { delete[] a; delete[] b; } };` trong đó `risky()` luôn throw, mỗi lần thử xây dựng rò rỉ bao nhiêu byte? Lặp lại khi initializer của `b` là `throw std::runtime_error("x")` thay vì `new double[90]`. Sau đó viết lại class bằng member `std::unique_ptr<double[]>` và chứng tỏ rò rỉ bằng 0 trong cả hai trường hợp, nêu tên quy tắc ngôn ngữ bạn dựa vào. Cuối cùng, một robot thử xây dựng lại ở 10 Hz trong 5 phút và lần nào cũng thất bại với biến thể đầu: mất bao nhiêu bộ nhớ? (phỏng theo C++ Core Guidelines, E.6 và R.13)
15. **(Thử thách)** Relocation khi có lỗi. Một kiểu `T` có copy constructor throw ở lần gọi thứ ba (đếm từ đầu thí nghiệm) và move constructor khai báo `noexcept(false)`. Một `std::vector<T>` có size 4 và capacity 4, và bạn gọi `emplace_back(4)`. (a) Dự đoán số copy, move, size, capacity và id các phần tử sau đó, và nói điều gì xảy ra với khối mới xây dở. (b) Lặp lại khi move constructor có `noexcept`. (c) Chứng minh vì sao relocation bằng move nói chung không thể khôi phục nội dung cũ, và nêu tiêu chuẩn bỏ đảm bảo nào khi `T` chỉ-move với move có thể throw. (phỏng theo cppreference, `std::vector::emplace_back` và `std::move_if_noexcept`, "Exceptions")

## Cài đặt tham khảo

`Buffer` là bộ sở hữu theo rule-of-five (bộ nhớ thô, chỉ-move), `ScopeGuard` là một helper RAII tổng quát cho code dọn dẹp, và `make_ramp` minh họa một factory trả về theo giá trị. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra -fsanitize=address,undefined ref.cpp && ./a.out`.

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

## Thực hành độc lập

### Mục tiêu

Viết từ các stub một class sở hữu chỉ-move và một scope guard, rồi chứng minh bằng test và AddressSanitizer rằng mọi tài nguyên được giải phóng đúng một lần.

### Chuẩn bị

Cần `g++` hoặc `clang++` với C++17. Lưu code khởi đầu và các test bên dưới nó thành `lab.cpp`; build bằng

```
g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab
```

### Nhiệm vụ

1. Cài đặt `Buffer(std::size_t)`, `size`, `empty`, `at` và destructor; giữ `alive` chính xác. Chạy các test đầu tiên.
2. Cài đặt move constructor; xác nhận đối tượng moved-from là rỗng và destructor của cả hai đối tượng đều an toàn.
3. Cài đặt move assignment, bao gồm cả self-move.
4. Cài đặt `make_ramp` và kiểm tra không có copy nào xảy ra (copy constructor bị xóa, nên nếu bạn gian lận thì sẽ không biên dịch được).
5. Cài đặt `ScopeGuard` (lưu callable, chạy một lần, tôn trọng `dismiss`, hỗ trợ move).
6. Cố ý phá một quy tắc (ví dụ quên đặt null cho nguồn) và đọc báo cáo của AddressSanitizer: ghi nhận các từ *double-free* và hai stack trace.

### Code khởi đầu

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

### Kiểm thử

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

### Kết quả mong đợi

```
all tests passed
```

Với starter chưa cài đặt, chương trình kết thúc với `NotImplemented`; với một move constructor có bug, AddressSanitizer in ra `attempting double-free`.

### Thử thách mở rộng

Làm cho `Buffer` copy được bằng deep copy (copy-and-swap) và chứng minh bằng một bộ đếm rằng sự tăng trưởng của `std::vector<Buffer>` dùng move vì chúng là `noexcept`. Sau đó thay `double*` thô bằng `std::unique_ptr<double[]>` và xóa destructor cùng các phép move của bạn (rule of zero).

### Thực hành với thư viện

Chỉ dùng standard library. Làm lại `Buffer` theo rule of zero và để các kiểu thư viện thật làm việc, rồi xác nhận các nhận định trong bài bằng các bộ đếm. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra -fsanitize=address,undefined`.

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

Output mong đợi: `Safe copies=0 Risky copies=7` rồi `library track ok`. Sau đó chạy các test lab của bạn trên một `Buffer` bọc `std::unique_ptr<double[]>` với cả năm hàm thành viên đặc biệt bị xóa khỏi source của bạn, và nhận xét rằng các test vẫn pass.

## Kiểm chứng

- Biên dịch với `-fsanitize=address,undefined`. Rò rỉ hiện ra lúc thoát dưới dạng `LeakSanitizer: detected memory leaks` kèm stack cấp phát; double free hiện dưới dạng `attempting double-free`.
- Giữ một bộ đếm tĩnh các đối tượng còn sống (như `alive` ở đây) và assert rằng nó trở về giá trị ban đầu ở cuối mỗi test.
- Dùng `static_assert(std::is_nothrow_move_constructible_v<T>)` để ghim hợp đồng `noexcept`.
- Để kiểm tra tính đúng của move, assert rằng đối tượng moved-from *dùng được*: hủy nó, gán cho nó, gọi `size()`.
- Valgrind (`valgrind --leak-check=full ./a.out`) là một ý kiến độc lập thứ hai trên Linux.

## Lỗi thường gặp

| Sai lầm | Điều bạn quan sát được |
|---|---|
| Copy mặc định của class sở hữu con trỏ thô | double free, crash ở cuối scope; ASan `attempting double-free` |
| Move constructor quên đặt null cho nguồn | cùng double free, nhưng chỉ khi có move xảy ra |
| `return std::move(local)` | thêm một move, cảnh báo `-Wpessimizing-move` |
| Phép move không có `noexcept` | `vector` khi tăng trưởng copy phần tử (3 copy thay vì 3 move ở bài tập 8) |
| Dùng `unique_ptr` moved-from mà không kiểm tra | dereference null; smart pointer moved-from được đảm bảo là null |
| Vòng `shared_ptr` (cha sở hữu con, con sở hữu cha) | bộ nhớ không bao giờ được giải phóng; dùng `weak_ptr` cho liên kết ngược |
| `new` trong danh sách đối số, `f(shared_ptr<A>(new A), g())` | rò rỉ nếu `g()` throw giữa lúc cấp phát và lúc dựng (thứ tự đánh giá trước C++17); dùng `make_shared`/`make_unique` |
| Throw từ destructor | `std::terminate` trong lúc unwinding |

## Phương án khác và đánh đổi

- **Value so với `unique_ptr`**: một member thường hoặc biến cục bộ là mặc định; dùng `unique_ptr` khi cần đa hình, một đối tượng tùy chọn, hoặc một địa chỉ phải ổn định.
- **`unique_ptr` so với `shared_ptr`**: sở hữu chia sẻ tốn một cập nhật đếm tham chiếu atomic cho mỗi lần copy và làm vòng đời khó suy luận. Chỉ dùng khi vòng đời thực sự được chia sẻ, tốt nhất với dữ liệu `const`.
- **Con trỏ thô và reference** vẫn ổn khi là các view *không sở hữu*. Nếu bạn có thể nêu vòng đời trong một comment thì có thể truyền chúng; nếu không, hãy thiết kế lại.
- **Move so với copy so với share cho dữ liệu lớn**: copy 1 MB ở 30 Hz là 30 MB/s lưu lượng bộ nhớ và một đỉnh trễ; một move hoặc một pool là $O(1)$.
- **Các ngôn ngữ có garbage collection** giải phóng bộ nhớ nhưng không giải phóng file, socket hay lock một cách kịp thời; RAII xử lý mọi loại tài nguyên một cách xác định.

## Vận dụng và ghi nhớ

Cùng nguyên tắc này là `with` trong Python, `defer` trong Go và `Drop` trong Rust (nơi move là mặc định). Trong ROS 2, callback của `rclcpp::Subscription` có thể nhận `std::unique_ptr<Msg>` để chuyển giao intra-process không copy, đúng là mẫu của bài tập 10. Ôn tập giãn cách: sau một tuần, viết lại từ trí nhớ move constructor và move assignment của `Buffer`, và giải thích vì sao mỗi dòng có mặt. Những câu hỏi nên luôn đặt khi code review: ai sở hữu nó, nó chết ở đâu, nó có thể throw khi đang dựng dở không?

## Đáp án bài tập

1. `lock_guard` khóa trong constructor và mở khóa trong destructor; destructor chạy trong lúc stack unwinding nếu code throw, nên mutex luôn được giải phóng. Với `lock()`/`unlock()` thủ công, một exception (hoặc một `return` sớm) bỏ qua `unlock()`, để mutex bị khóa mãi mãi và các thread khác bị chặn (deadlock).
2. `+a +b +c -c -b +d -d -a`: các đối tượng của scope trong bị hủy theo thứ tự ngược tại `}`, rồi đến `d`, rồi `a`.
3. Số chu kỳ: $100\cdot600=60{,}000$; đường đi sớm: $60{,}000/4=15{,}000$ lần rò rỉ; mỗi lần là $256\cdot8=2048$ byte, nên $30{,}720{,}000$ byte ($\approx30.7$ MB). Checker báo lúc thoát, nhưng robot không bao giờ thoát trong lúc làm nhiệm vụ: bộ nhớ tăng cho đến khi allocator thất bại hoặc OOM killer ra tay, nên đó là một lỗi thật, chỉ là muộn hơn.
4. `Scan b = a` dùng copy constructor ngầm định, copy con trỏ; cả hai destructor gọi `delete[]` trên cùng một địa chỉ: double free. Cách sửa: (1) xóa các phép copy và thêm move (rule of five); (2) giữ `std::unique_ptr<double[]>` (rule of zero, class thành chỉ-move); (3) dùng `std::vector<double>` (rule of zero, copy được, kiểm tra biên qua `.at()`). Cách tốt nhất là (3) trừ khi kích thước cố định và việc copy bị cấm.
5. In ra `17`. Một `unique_ptr` moved-from được đảm bảo là null (đó là một hậu điều kiện được chỉ định rõ, không như hầu hết kiểu chuẩn khác).
6. (a) `const Frame&` (mượn, không null, bên gọi giữ nó); (b) `std::unique_ptr<Source>` theo giá trị (nhận sở hữu độc quyền; pipeline sống lâu bằng nguồn); (c) `std::shared_ptr<const Frame>` hoặc `unique_ptr<Frame>` được move vào thread (bên được gọi sống lâu hơn bên gọi, nên mượn là bug dangling reference); (d) `const Calibration*` (mượn tùy chọn; reference không biểu diễn được "vắng mặt").
7. `f1`: 0 lần move (bị loại bỏ bởi NRVO / đối tượng được dựng tại chỗ). `f2`: 1 lần move, vì `std::move` vô hiệu hóa elision. Nên ưu tiên `return c;`; compiler vẫn coi nó là một move nếu không thể elision.
8. Với `W` (noexcept): 7 move, 0 copy: 4 cho các phần tử mới cộng 3 phép di dời (1, rồi 2 phần tử được move ở hai lần cấp phát lại). Với `V`: 4 move (phần tử mới) và 3 copy (di dời): `std::vector` dùng `move_if_noexcept` và copy để giữ strong guarantee. Con số chính xác phụ thuộc hệ số tăng trưởng của standard library (GCC nhân đôi); bài học là 0 so với 3 copy.
9. Với `b = std::move(b)`, `o` là alias của `*this`: `delete[] data_` giải phóng vùng nhớ, rồi `data_ = o.data_` gán địa chỉ đã treo, rồi `o.data_ = nullptr` đặt null cho cả hai (chúng là cùng một đối tượng), nên trạng thái cuối là `data_ == nullptr`, `size_ == 0`: dữ liệu bị hủy dù self-move lẽ ra phải để lại một đối tượng hợp lệ (mất dữ liệu một cách lặng lẽ). Cách sửa 1: `if (this != &o) {...}`. Cách sửa 2: `std::swap(data_, o.data_); std::swap(size_, o.size_);` an toàn với self, và để nội dung *cũ* của `*this` lại trong `o` (được giải phóng khi `o` chết); phiên bản kiểm tra danh tính để `o` rỗng ngay lập tức.
10. (i) Copy: $1\ \text{MB}\cdot30=30$ MB/s cộng một lần cấp phát hoặc lock; rủi ro: jitter độ trễ, nhưng đơn giản nhất và an toàn. (ii) `shared_ptr<const Frame>`: không copy, planner giữ frame sống bao lâu tùy nhu cầu; rủi ro: bộ nhớ không giới hạn nếu planner chậm (frame chồng chất), và tranh chấp refcount atomic. (iii) Pool với `unique_ptr`: không copy và bộ nhớ có giới hạn, planner nhận sở hữu duy nhất và trả lại; rủi ro: xử lý cạn pool và đường trả về phức tạp hơn. Một câu trả lời tốt chọn (ii) với hàng đợi có giới hạn hoặc (iii) khi bộ nhớ phải có giới hạn, và nêu quy tắc vòng đời trong interface.
11. Một câu trả lời tốt gồm: constructor gọi `dev_open` và throw khi thất bại; destructor gọi `dev_close` nếu handle hợp lệ (`-1` nghĩa là rỗng); copy bị xóa, các phép move `noexcept` vô hiệu hóa handle của nguồn; các test đếm số handle đang mở khi thoát một scope, sau `throw`/`catch`, và sau `vec.push_back(std::move(d))` rồi hủy vector; biến thể `unique_ptr` dùng một deleter gọi `dev_close` trên handle (với `std::unique_ptr<std::remove_pointer_t<Handle>, Deleter>` hoặc một wrapper handle nhỏ).

12. (a) Trong `a = b`, tham số theo giá trị `o` được dựng từ `b` bằng copy constructor *trước khi* thân hàm bắt đầu. Nếu nó throw, luồng điều khiển rời hàm trước `swap`, nên không có gì trong `*this` bị đụng tới và `a` vẫn giữ 1000 double. Nếu thành công, `swap` đổi hai giá trị vô hướng và không thể throw, nên phép gán là tất cả-hoặc-không. (b) Đo bằng một class có đếm (g++ 11.4, `-std=c++17`): `a = b`: 1 copy, 0 move, 1 cấp phát; `a = std::move(b)`: 0 copy, 1 move, 0 cấp phát; `a = a`: 1 copy, 1 cấp phát (nó copy chính mình vào `o`, swap rồi giải phóng khối cũ: vô hại nhưng lãng phí). (c) Sau `a = b`, `a` có 500 phần tử bằng của `b` và `b` không đổi; sau move, `a` có 500 phần tử và `b` có 0 (move constructor của nó đã làm rỗng); sau `a = a`, `a` vẫn giữ 500 phần tử. (d) Khi khai báo cả `operator=(const Buffer&)` lẫn `operator=(Buffer)`, `a = b` gắn một lvalue vào cả hai với chi phí chuyển đổi như nhau, nên g++ báo "ambiguous overload for operator=" và bạn phải chọn một. Giữ overload `const Buffer&` riêng khi phép gán nằm ở đường nóng và kích thước thường bằng nhau: nó tái sử dụng vùng nhớ sẵn có mà không cấp phát (như `std::vector`) và vẫn có thể đạt strong guarantee nếu kiểm tra capacity trước và copy trước khi đổi size.
13. (a) `use_count()` là 2 cho cả hai (biến cục bộ cộng liên kết của nút kia). Cuối scope mỗi count giảm từ 2 xuống 1, không cái nào về 0, nên **không có output destructor nào**: cả hai nút rò rỉ. (b) Với `A` giữ `shared_ptr` tới `B` và `B` giữ `weak_ptr` tới `A`: khi cả hai biến cục bộ còn sống, `A.use_count()=1` và `B.use_count()=2` (đã đo). Cuối scope `b` được giải phóng trước (2 xuống 1), rồi `a` (1 xuống 0), `A` bị hủy và nhả `next` của nó, nên `B` theo sau: output `~A ~B`. `weak_ptr` không tăng strong count; `lock()` cho một chủ sở hữu tạm (count 2 khi đang giữ). (c) `p.use_count()=2` và `y.use_count()=2`, vì cả hai dùng chung một control block; sau `p.reset()`, `y.use_count()=1`. Toàn bộ đối tượng `P` vẫn sống vì control block sở hữu nó, và `y` trỏ vào trong, nên đọc `*y` là hợp lệ. Trong aliasing constructor, quyền sở hữu (control block) và con trỏ được lưu là tách rời nhau.
14. Biến thể đầu: thân hàm throw sau cả hai `new`, destructor không bao giờ chạy, và các member là con trỏ thô, nên cả hai khối đều rò rỉ: $30\cdot8+90\cdot8=960$ byte mỗi lần thử (đo bằng `operator new` có đếm: 960). Biến thể thứ hai: `a` đã được cấp phát ($240$ byte) rồi initializer của `b` throw, nên chỉ rò rỉ $240$ byte (đo được: 240). Với `std::unique_ptr<double[]> a, b;` quy tắc là: khi constructor thoát bằng exception, các member và base *đã xây xong hoàn toàn* bị hủy theo thứ tự ngược. `a` là một `unique_ptr` hoàn chỉnh nên destructor của nó giải phóng khối; `b` chưa hoàn tất nên không có gì để giải phóng; đo được rò rỉ 0 ở cả hai trường hợp. Vòng thử lại: $10\ \text{Hz}\cdot300\ \text{s}=3000$ lần, $3000\cdot960=2{,}880{,}000$ byte (khoảng 2,9 MB) bị mất.
15. (a) Với move có thể throw và kiểu copy được, `vector` dùng `move_if_noexcept`, chọn copy. Nó cấp phát khối mới capacity 8, dựng phần tử mới, rồi copy từng phần tử cũ: copy 1 và 2 thành công, copy 3 throw. Đo được: copy = 3 (tính cả lần thất bại), move = 0, size 4, capacity 4, id `0 1 2 3`. Hai bản sao mới và phần tử mới bị hủy và khối mới được giải phóng, nên vector y hệt trước đó: strong guarantee. (b) Với `noexcept` trên move constructor, các phần tử được move: đo được copy = 0, move = 4, size 5, capacity 8, không có exception. (c) Giả sử relocation move các phần tử $1..k-1$ và lần move thứ $k$ throw. Các nguồn $1..k-1$ giờ giữ giá trị moved-from, và khôi phục chúng cần $k-1$ phép move ngược, mà chúng cũng được phép throw, nên một rollback được đảm bảo nói chung không tồn tại. Copy để nguồn nguyên vẹn, do đó có quy tắc này. Nếu `T` chỉ-move (không có copy để quay về) và move của nó throw, `vector` vẫn dùng move, và strong guarantee bị bỏ: tác dụng là unspecified, chỉ có thể hy vọng basic guarantee.

## Đọc thêm

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - phần R (quản lý tài nguyên), C.20-C.22 (rule of zero/five), F.15-F.26 (truyền tham số).
- [cppreference: std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr) - interface đầy đủ, deleter, và đảm bảo moved-from.
- [LearnCpp](https://www.learncpp.com/) - các chương về smart pointer và move semantics, với ví dụ từng bước.
- [cppreference: std::shared_ptr](https://en.cppreference.com/w/cpp/memory/shared_ptr) - control block, aliasing constructor, `weak_ptr` và ghi chú về thread-safety.
- [Bản nháp chuẩn C++, [except.ctor]](https://eel.is/c++draft/except.ctor), [[class.dtor]](https://eel.is/c++draft/class.dtor) và [[class.copy.elision]](https://eel.is/c++draft/class.copy.elision) - câu chữ chính xác đằng sau thứ tự unwinding, việc hủy member và implicit move khi return.
- [cppreference: std::move_if_noexcept](https://en.cppreference.com/w/cpp/utility/move_if_noexcept) và [`std::vector::emplace_back`](https://en.cppreference.com/w/cpp/container/vector/emplace_back) - phát biểu chính xác về exception safety dùng trong lập luận relocation.

**Thực hành thêm:** các bài quiz ở [LearnCpp: intro to smart pointers and move semantics](https://www.learncpp.com/cpp-tutorial/introduction-to-smart-pointers-move-semantics/) và [LearnCpp: std::unique_ptr](https://www.learncpp.com/cpp-tutorial/stdunique_ptr/) (đáp án hiện trên trang), [LearnCpp: std::move](https://www.learncpp.com/cpp-tutorial/stdmove/), và [phần quản lý tài nguyên (R) của Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management) làm checklist ôn tập cho `Buffer` của riêng bạn.
