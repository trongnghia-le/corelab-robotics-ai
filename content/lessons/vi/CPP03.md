---
{"title": "Quản lý tài nguyên: RAII, sở hữu duy nhất và move semantics", "summary": "Gắn mọi tài nguyên với một đối tượng sở hữu, làm cho quyền sở hữu hiện rõ trong kiểu dữ liệu, và chuyển nó bằng move thay vì copy.", "objectives": ["Phát biểu quy tắc RAII và giải thích vì sao nó đem lại exception safety.", "Biểu diễn quyền sở hữu độc quyền bằng value member, std::vector và std::unique_ptr thay cho new/delete.", "Cài đặt một class tài nguyên chỉ-move theo rule of five và để lại trạng thái moved-from hợp lệ.", "Chọn chữ ký hàm cho thấy quyền sở hữu là mượn, chuyển giao hay chia sẻ."]}
---
## Vì sao điều này quan trọng

Một tiến trình robot mở camera, cổng serial, buffer GPU, file log và mutex, và chạy hàng giờ liền. Mỗi thứ đó là một *tài nguyên* phải được giải phóng đúng một lần, ngay cả khi một exception, một `return` sớm, hoặc một lần đọc cảm biến thất bại khiến hàm dừng giữa chừng. Các cặp `new`/`delete` hay `open`/`close` viết tay đều hỏng đúng ở những đường đi này: rò rỉ một buffer nháp 2 KB mỗi chu kỳ điều khiển ở 100 Hz là 20 MB mỗi phút, và một double free có thể làm sập bộ điều khiển xe. C++ giải quyết chuyện này mà không cần garbage collector: đối tượng sở hữu tài nguyên giải phóng nó trong destructor, và ngôn ngữ đảm bảo destructor chạy khi scope kết thúc, dù bình thường hay do exception. Đây là RAII (resource acquisition is initialization, tức "chiếm tài nguyên là khởi tạo"). Move semantics sau đó cho phép quyền sở hữu di chuyển (được trả về từ factory, lưu vào container) mà không phải copy các buffer lớn.

## Trực giác

Hãy nghĩ đến một cuốn sách thư viện chỉ có đúng một thẻ mượn. RAII nói rằng cái thẻ chính là đối tượng: ai giữ thẻ thì có trách nhiệm trả sách, và thẻ không thể bị mất mà sách không được trả tự động. `std::unique_ptr` là một cái thẻ không thể photocopy nhưng có thể trao cho người khác. Con trỏ thô (raw pointer) là một tờ giấy nhớ ghi số kệ: nó cho biết cuốn sách ở đâu, nhưng không cho biết ai phải trả nó.

Trong code, các câu hỏi cần đặt ra với mọi con trỏ hay handle là: *ai sở hữu nó, ai chỉ được nhìn, và nó còn hợp lệ cho đến khi nào?* RAII biến câu trả lời thành kiểu dữ liệu: một value member hay `std::vector` sở hữu các phần tử của nó; `std::unique_ptr<T>` sở hữu độc quyền một `T`; `T&` và `T*` (khi là con trỏ thô) chỉ mượn.

![Sơ đồ vòng đời: Buffer a sở hữu vùng nhớ, một phép move chuyển con trỏ sang b và để a rỗng, rồi cả hai destructor chạy an toàn](/lesson-figures/CPP03.svg)

*Một phép move chuyển con trỏ sở hữu và đặt nguồn về null, nên chỉ đúng một destructor giải phóng vùng nhớ.*

## Lý thuyết và suy dẫn

### RAII và thứ tự hủy

Một đối tượng cục bộ bị hủy khi scope của nó kết thúc, theo thứ tự ngược với thứ tự khởi tạo. Destructor chạy trong quá trình **stack unwinding** (tháo ngăn xếp) nếu có exception lan truyền. Vì vậy tài nguyên do một đối tượng cục bộ sở hữu được giải phóng trên mọi đường thoát mà không cần `finally`. Các member bị hủy theo thứ tự ngược với thứ tự khai báo, sau phần thân destructor. Destructor không được throw (nó mặc định là `noexcept`).

### Rule of zero, three, five

- **Rule of zero**: nếu class của bạn chỉ sở hữu tài nguyên thông qua các member vốn đã tự quản lý chúng (`std::vector`, `std::string`, `std::unique_ptr`), hãy viết *không* hàm thành viên đặc biệt nào. Những hàm do compiler sinh ra là đúng. Hãy ưu tiên cách này.
- **Rule of three/five**: nếu bạn buộc phải quản lý một tài nguyên thô, hãy định nghĩa hoặc xóa (delete) tất cả: destructor, copy constructor, copy assignment, move constructor, move assignment. Một class có destructor giải phóng bộ nhớ nhưng copy mặc định sẽ có hai đối tượng cùng sở hữu một con trỏ: double free.

### Value category và move

**Lvalue** có tên và danh tính; **rvalue** là một giá trị tạm hoặc thứ bạn hứa sẽ không dùng lại. `std::move(x)` không di chuyển gì cả: nó là một phép ép kiểu (cast) sang rvalue reference, cho phép overload `T(T&&)` được chọn. Một move constructor nên (1) lấy cắp tài nguyên, (2) để nguồn ở trạng thái **hợp lệ nhưng không xác định (valid but unspecified)**, thường là rỗng, để destructor và phép gán của nó vẫn hoạt động, và (3) là `noexcept`.

Với buffer sở hữu dùng trong bài này:

$$\text{move: } \underbrace{\texttt{data\_}}_{\text{dst}} \leftarrow \texttt{src.data\_}, \quad \texttt{src.data\_} \leftarrow \texttt{nullptr}$$

Chi phí: copy $n$ double tốn $O(n)$ thời gian và $8n$ byte; một move là $O(1)$ (hai phép gán).

Vì sao `noexcept` quan trọng: khi `std::vector` phải tăng dung lượng, nó di dời (relocate) các phần tử. Để giữ strong exception guarantee, nó dùng `std::move_if_noexcept`: nếu move constructor có thể throw và kiểu đó cũng copy được, nó sẽ *copy* thay vì move. Quên `noexcept` lặng lẽ biến các phép di dời $O(1)$ thành các phép copy $O(n)$.

### Giá trị trả về và `std::move`

`return local;` đã coi `local` là rvalue và cho phép copy elision (NRVO). Viết `return std::move(local);` phá NRVO và ép một phép move, và compiler sẽ cảnh báo (`-Wpessimizing-move`). Chỉ dùng `std::move` khi truyền một lvalue mà bạn sẽ không dùng lại.

### Quyền sở hữu trong chữ ký hàm

| Ý định | Chữ ký | Ý nghĩa |
|---|---|---|
| Dùng, không giữ | `const Frame&`, `Frame&` | bên mượn, bên gọi giữ quyền sở hữu |
| Mượn tùy chọn | `const Frame*` | có thể null, vẫn không sở hữu |
| Nhận quyền sở hữu | `std::unique_ptr<Frame>` truyền theo giá trị | bên gọi phải `std::move` vào |
| Trao quyền sở hữu | trả về `std::unique_ptr<Frame>` | bên gọi sở hữu kết quả |
| Vòng đời chia sẻ | `std::shared_ptr<const Frame>` | đếm tham chiếu, dùng dè xẻn |

Dùng `std::make_unique<T>(args...)`; nó an toàn với exception và tránh `new` trần. Với các API của C, hãy cho `unique_ptr` một custom deleter: `std::unique_ptr<FILE, int(*)(FILE*)> f(fopen(p, "r"), &fclose);`.

## Ví dụ có lời giải

Lần theo chương trình này, theo dõi `alive` (một bộ đếm tăng ở mỗi constructor và giảm ở mỗi destructor):

```cpp
Buffer a = make_ramp(3);   // (1)
Buffer b = std::move(a);   // (2)
{
  auto p = std::make_unique<Buffer>(2);  // (3)
}                          // (4)
```

1. `make_ramp(3)` dựng `Buffer b(3)` bên trong hàm; nhờ elision đối tượng được dựng thẳng vào `a`. Vùng nhớ `[0,1,2]` tại địa chỉ `A`. `alive = 1`.
2. `Buffer(Buffer&&)` chạy: `b.data_ = A`, `b.size_ = 3`, rồi `a.data_ = nullptr`, `a.size_ = 0`. `alive = 2` (một đối tượng moved-from vẫn là một đối tượng).
3. `make_unique<Buffer>(2)` cấp phát đối tượng `Buffer` trên heap, mà constructor của nó cấp phát 2 double. `alive = 3`.
4. Ở dấu ngoặc đóng, `p` bị hủy: `unique_ptr` xóa `Buffer`, destructor của nó giải phóng 2 double. `alive = 2`.

Ở cuối scope bao ngoài, `b` bị hủy trước (thứ tự ngược): `delete[] A`, `alive = 1`. Rồi đến `a`: `delete[] nullptr` là phép không làm gì được định nghĩa rõ, `alive = 0`. Vùng nhớ `A` được giải phóng đúng một lần, đó chính là mục đích. Nếu không có `a.data_ = nullptr` ở bước 2, cả hai destructor sẽ cùng giải phóng `A`: double free.

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

## Đọc thêm

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - phần R (quản lý tài nguyên), C.20-C.22 (rule of zero/five), F.15-F.26 (truyền tham số).
- [cppreference: std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr) - interface đầy đủ, deleter, và đảm bảo moved-from.
- [LearnCpp](https://www.learncpp.com/) - các chương về smart pointer và move semantics, với ví dụ từng bước.

**Thực hành thêm:** các bài quiz ở [LearnCpp: intro to smart pointers and move semantics](https://www.learncpp.com/cpp-tutorial/introduction-to-smart-pointers-move-semantics/) và [LearnCpp: std::unique_ptr](https://www.learncpp.com/cpp-tutorial/stdunique_ptr/) (đáp án hiện trên trang), [LearnCpp: std::move](https://www.learncpp.com/cpp-tutorial/stdmove/), và [phần quản lý tài nguyên (R) của Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management) làm checklist ôn tập cho `Buffer` của riêng bạn.
