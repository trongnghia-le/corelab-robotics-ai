---
{"title": "C++ nâng cao: thư viện generic, ABI và thiết kế hệ thống", "summary": "Thiết kế và kiểm toán interface của thư viện về quyền sở hữu, xử lý lỗi và tương thích nhị phân, với một ranh giới C ổn định và một wrapper C++ an toàn.", "objectives": ["Phân biệt API với ABI và phân loại các thay đổi là tương thích mã nguồn, tương thích nhị phân hay phá vỡ.", "Thiết kế một ranh giới C ổn định (opaque handle, mã lỗi, không có exception xuyên qua) và bọc nó bằng C++ RAII.", "Kiểm toán interface của một thư viện: ai sở hữu cái gì, trong bao lâu và trên thread nào.", "Chọn giữa code generic chỉ có header, thư viện đã biên dịch và pimpl cho một kiểu triển khai cho trước."]}
---
## Vì sao điều này quan trọng

Phần mềm robotics được lắp ghép từ các thư viện do các đội khác nhau viết, biên dịch vào các thời điểm khác nhau, và thường được phân phối dưới dạng binary: SDK của hãng camera, một thư viện lập kế hoạch chuyển động, các package ROS 2, một driver động cơ mã đóng. Các ranh giới giữa chúng là nơi bug cư trú. Một hàm nhận `Frame*` không cho biết ai giải phóng frame; một struct bị đổi bố cục ở phiên bản thư viện mới lặng lẽ đọc sai field trong một executable cũ; một exception ném bên trong một callback C làm sập cả process. Đây không phải lỗi cú pháp, compiler chấp nhận chúng, và chúng xuất hiện dưới dạng crash ngoài hiện trường. Bài này nói về đọc và viết interface sao cho quyền sở hữu, vòng đời, lỗi và tương thích nhị phân đều tường minh. Nó tổng hợp mọi thứ của chuỗi bài: RAII và move (CPP03), invariant và interface (CPP04), template (CPP06), hệ thống build và linking (CPP07), và hợp đồng đồng thời (CPP10).

## Trực giác

Hãy phân biệt hai loại tương thích. Tương thích **API** (application programming interface) nghĩa là *mã nguồn* từng dùng thư viện vẫn biên dịch được. Tương thích **ABI** (application binary interface) nghĩa là một chương trình *đã biên dịch* vẫn chạy khi binary của thư viện được thay bằng phiên bản mới, mà không biên dịch lại. ABI là mọi thứ mã máy dựa vào: tên symbol, calling convention (cách truyền đối số), kích thước và bố cục của các kiểu, bố cục vtable, xử lý exception.

Vì vậy một interface thư viện ổn định trông như một phích cắm: một bề mặt nhỏ, nhàm chán, tường minh (opaque handle, hàm thường, số nguyên và double thường, mã lỗi) với mọi thứ thú vị của C++ nằm phía sau. Bên trong code của riêng bạn thì bạn muốn ngược lại: kiểu phong phú, RAII và exception. Giải pháp chuẩn là hai tầng: một ranh giới kiểu C cho binary và một wrapper C++ mỏng chỉ có header để làm cho API C an toàn khi dùng.

![Các tầng: code người dùng, wrapper RAII C++, ABI C ổn định với opaque handle, phần bên trong thư viện; bên phải, bảng tương thích API/ABI của các thay đổi thông dụng](/lesson-figures/CPP12.svg)

*Một ranh giới C ổn định giữa wrapper (được biên dịch cùng code của người dùng) và phần bên trong thư viện; bảng phân loại các thay đổi điển hình.*

## Lý thuyết và suy dẫn

### Symbol, name mangling và `extern "C"`

C++ cho phép overload, nên compiler mã hóa kiểu tham số và namespace vào tên symbol (*mangling*). Trong `.so` đã biên dịch:

```
c_add                                   <- extern "C" int c_add(int, int)
_Z7cxx_addii                            <- int cxx_add(int, int)
_ZN5robot8cxx_add2Eii                   <- robot::cxx_add2(int, int)
_Z12takes_vectorRKSt6vectorIiSaIiEE     <- takes_vector(const std::vector<int>&)
```
(`nm -D lib.so` liệt kê chúng; `nm -DC` giải mã tên.) Mangling khác nhau giữa các compiler và thậm chí giữa các phiên bản, nên một API C++ biên dịch bằng một toolchain nhìn chung không thể được gọi từ code biên dịch bằng toolchain khác. `extern "C"` tắt mangling và dùng calling convention của C, nên bất kỳ ngôn ngữ nào (C, Python `ctypes`, Rust FFI) cũng gọi được hàm.

### Cái gì thuộc về một ABI ổn định

An toàn qua ranh giới nhị phân: số nguyên độ rộng cố định, `double`, con trỏ, opaque handle, struct C thuần với *bố cục cố định, có tài liệu* (chỉ được thêm vào cuối nếu có phiên bản), con trỏ hàm với liên kết C, enum với kích thước nền tảng tường minh, `const char*` với chủ sở hữu có tài liệu. Rủi ro: `std::string`, `std::vector`, `std::shared_ptr`, `std::function` trong chữ ký (bố cục của chúng phụ thuộc phiên bản standard library và cờ: ví dụ dual ABI của GCC `_GLIBCXX_USE_CXX11_ABI` làm đổi `std::string`); hàm ảo (thêm hoặc sắp xếp lại làm đổi vtable); class có hàm thành viên inline chạm dữ liệu private (được inline vào phía gọi); template được khởi tạo ở cả hai phía; exception qua ranh giới; `new` trong thư viện và `delete` ở phía gọi nếu chúng dùng allocator hoặc runtime khác nhau.

**Thí nghiệm.** Phiên bản 1 của một thư viện phơi ra `struct Pose { double x; double y; }` và `get_pose(Pose*)`. Phiên bản 2 chèn `double z` vào giữa và viết lại hàm. Một ứng dụng biên dịch với header của phiên bản 1 nhưng chạy với phiên bản 2 in ra `x=1 y=9` thay vì `x=1 y=2`: nó đọc field `z` như `y`, và thư viện thậm chí ghi 24 byte vào đối tượng 16 byte của ứng dụng. Không có gì thất bại lúc link vì tên symbol `get_pose` không đổi.

### Phân loại thay đổi

| Thay đổi | API (mã nguồn) | ABI (nhị phân) |
|---|---|---|
| Thêm một hàm tự do mới | tương thích | tương thích |
| Thêm một giá trị enum | tương thích (switch có thể cảnh báo) | tương thích nếu kích thước không đổi; code cũ có thể không xử lý nó |
| Đổi kiểu tham số hoặc thêm tham số | phá vỡ | phá vỡ (symbol/chữ ký mới) |
| Sắp xếp lại hoặc thêm data member public | thường tương thích | phá vỡ (bố cục) |
| Thêm một hàm ảo | tương thích | phá vỡ (bố cục vtable) |
| Thêm data member private vào class dùng theo giá trị | tương thích | phá vỡ (`sizeof` đổi) |
| Đổi hành vi nhưng không đổi chữ ký | tương thích | tương thích (nhưng có thể vi phạm hợp đồng) |
| Thêm data member vào class dùng pimpl | tương thích | tương thích (ẩn sau một con trỏ) |

### Opaque handle, pimpl và quyền sở hữu

**Opaque handle** (C): `typedef struct rc_arm rc_arm;` cùng `rc_arm* rc_arm_create(...)` và `rc_arm_destroy(rc_arm*)`. Phía gọi không bao giờ thấy bố cục, nên thư viện có thể đổi nó tự do. Hợp đồng nêu rằng bên tạo sở hữu vùng cấp phát: create/destroy đi thành cặp.

**Pimpl idiom** (C++): class giữ `std::unique_ptr<Impl>` tới một kiểu cài đặt ẩn được định nghĩa trong `.cpp`. Header public giữ cùng kích thước mãi mãi. Cạm bẫy: destructor (và các phép move) phải được định nghĩa trong `.cpp`, nơi `Impl` đầy đủ; nếu không compiler sinh chúng inline ở nơi `Impl` chưa đầy đủ, và thất bại với "invalid application of 'sizeof' to incomplete type".

**Từ vựng về quyền sở hữu** cần tìm trong bất kỳ interface nào (Core Guidelines I.11, F.26): con trỏ thô do hàm trả về (ai giải phóng?), tham số con trỏ thô (mượn hay nhận?), `const char*` trả về (tĩnh, hay hợp lệ đến lời gọi tiếp theo?), callback với `void* user_data` (vòng đời dữ liệu, thread của lời gọi), handle chia sẻ (các bản copy `cv::Mat` chia sẻ buffer pixel: phép gán là nông, `clone()` là sâu), view (`std::string_view`, `Eigen::Map`, `std::span`) không sở hữu.

### Lỗi qua ranh giới

Một exception không được lan truyền ra khỏi một hàm `extern "C"`: nếu bên gọi là C, Python hay một runtime khác không thể unwind các frame C++, hành vi là undefined và thường là `std::terminate`. Thí nghiệm: `risky(-3)` trong một shared library có throw, được gọi qua Python `ctypes`, làm process abort với `terminate called after throwing an instance of 'std::invalid_argument'`. Ranh giới C bắt mọi thứ và trả về một mã lỗi; wrapper C++ dịch mã đó trở lại thành exception (hoặc `std::expected`/`optional` nơi exception bị cấm). Cũng cung cấp `rc_strerror(code)` trả về một chuỗi tĩnh.

### Thư viện generic và ABI

Template được khởi tạo trong translation unit dùng chúng, nên một thư viện chỉ có header (Eigen, phần lớn standard library) không có ABI của riêng nó: compiler của người dùng sinh code, và các phiên bản compiler khác nhau trong một chương trình cùng tồn tại miễn là không có đối tượng kiểu template nào đi qua ranh giới nhị phân. Một thư viện đã biên dịch có template trong interface có thể giảm thời gian biên dịch bằng explicit instantiation (`extern template class Filter<double>;` trong header và `template class Filter<double>;` trong một `.cpp`), nhưng khi đó chỉ những instantiation đó có sẵn, và bố cục của `Filter<double>` là một phần của ABI.

### Checklist thiết kế hệ thống

Với mỗi hàm public hãy ghi ra: **Ai sở hữu** từng con trỏ/handle làm đối số và kết quả; **hợp lệ trong bao lâu**; **thread nào** được gọi nó và nó có reentrant không (CPP10); **những lỗi nào** nó báo và bằng cách nào; **cái gì có thể đổi** trong một phiên bản minor. Giao những điều này dưới dạng comment hoặc tài liệu cạnh khai báo, và mã hóa chúng vào kiểu khi có thể (`unique_ptr` cho chuyển giao, reference cho mượn, `const` cho chỉ đọc).

## Ví dụ có lời giải

Kiểm toán header SDK camera giả định này, rồi bọc nó.

```c
typedef struct cam cam;
cam* cam_open(const char* device);
void cam_close(cam* c);
const char* cam_error(void);
unsigned char* cam_grab(cam* c, int* size);
void cam_on_frame(cam* c, void (*cb)(unsigned char*, int, void*), void* user);
```
1. `cam_open` trả về một con trỏ: **do bên gọi sở hữu**, được giải phóng bằng `cam_close` (theo quy ước đặt tên; header không nói). `NULL` khi thất bại; lý do nằm trong `cam_error()`, một biến toàn cục, nên nó **không thread-safe**.
2. `cam_error()` trả về `const char*`: chủ sở hữu không rõ; có lẽ là một buffer tĩnh bị lời gọi tiếp theo ghi đè, nên phải copy ngay lập tức.
3. `cam_grab` trả về `unsigned char*` và kích thước qua một tham số out: **ai giải phóng buffer?** Hoặc camera tái sử dụng một buffer nội bộ (hợp lệ đến lần grab tiếp theo) hoặc bên gọi phải free. Header im lặng: một *rủi ro*. Wrapper an toàn phải copy vào một `std::vector<unsigned char>` ngay lập tức.
4. `cam_on_frame` đăng ký một callback với `void* user`: callback chạy trên một **thread không rõ** (có lẽ là thread của driver); `user` phải sống lâu hơn thời gian đăng ký; con trỏ buffer chỉ hợp lệ trong lúc callback. Một exception ném trong callback sẽ xuyên qua các frame C.
5. Thiết kế wrapper: `class Camera` giữ `unique_ptr<cam, decltype(&cam_close)>`, throw `Error` từ constructor khi `cam_open` trả null (với thông báo được copy từ `cam_error()`), `grab()` trả `std::vector<unsigned char>`, trampoline của callback là một hàm static bắt mọi exception và lưu chúng lại, và `~Camera` hủy đăng ký callback rồi đóng camera (theo đúng thứ tự đó, để callback không thể chạy trên một `Camera` đã bị hủy).

Kết quả là một interface trong đó quyền sở hữu nằm trong kiểu: người dùng không bao giờ thấy một con trỏ thô hay một thread do thư viện tạo.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** Với danh sách `nm -D` ở trên, các symbol nào có thể gọi từ Python bằng `ctypes` theo tên thường, và vì sao? `_Z7cxx_addii` mang thông tin gì?
2. **(Dễ)** *(Adapted from: KDE, Binary Compatibility Issues With C++)* Phân loại là phá vỡ API, chỉ phá vỡ ABI, hay không cái nào: (a) thêm một member private vào một class dùng theo giá trị; (b) thêm một hàm tự do mới; (c) thêm một hàm ảo vào một class có subclass ở các thư viện khác; (d) đổi giá trị đối số mặc định của một hàm; (e) đổi tên một tham số; (f) đổi `int` thành `long` trong một tham số.
3. **(Dễ)** *(Adapted from: C++ Core Guidelines, I.11 and F.26)* Với mỗi khai báo nêu chữ ký nói gì về quyền sở hữu và để lại điều gì không nói: `Frame* grab();`, `void put(Frame*);`, `const char* name() const;`, `void set_cb(Callback, void*);`, `std::unique_ptr<Map> load(const std::string&);`.
4. **(Trung bình)** Tìm hai bug trong hàm giao diện C này và sửa chúng:
   ```cpp
   extern "C" const char* describe(int code) {
     if (code < 0) throw std::invalid_argument("negative");
     std::string s = "code " + std::to_string(code);
     return s.c_str();
   }
   ```
5. **(Trung bình)** *(Adapted from: OpenCV documentation, "Mat - the basic image container")* Một class giữ một `std::shared_ptr<std::vector<int>>` giống như header `cv::Mat` chia sẻ pixel. `a.at(0)`, `b.at(0)` và `c.at(0)` in ra gì sau `Image a(3,1); Image b = a; Image c = a.clone(); b.fill(7);`? Bug robotics nào xảy ra khi một callback lưu một bản copy của frame?
6. **(Trung bình)** Viết header và `.cpp` của `Planner` với pimpl. Một translation unit của người dùng chỉ include header và tạo một `Planner` thất bại với "invalid application of 'sizeof' to incomplete type". Vì sao, và cách sửa một dòng là gì?
7. **(Trung bình)** Diễn giải thí nghiệm: ứng dụng in ra `x=1 y=9` sau khi thư viện bị hoán đổi. Giải thích chính xác điều gì đã xảy ra theo độ lệch (offset), và nêu ba cách để phát triển struct mà không phá các binary cũ.
8. **(Khó)** *(Adapted from: libstdc++ manual, dual ABI)* Một `.so` dựng sẵn được biên dịch với `_GLIBCXX_USE_CXX11_ABI=0` và xuất `void f(const std::string&)`. Code của bạn dùng mặc định. Điều gì xảy ra lúc link và vì sao? Liệt kê ba chiến lược cho một nhà cung cấp phân phối SDK dạng binary.
9. **(Khó)** Xem xét header giả định này và liệt kê ít nhất sáu rủi ro về quyền sở hữu, vòng đời, thread hoặc ABI, rồi viết lại nó:
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
10. **(Khó)** Bạn bảo trì một `Filter<T>` generic cho `float` và `double`. So sánh (i) chỉ có header, (ii) thư viện đã biên dịch với explicit instantiation, (iii) một API C với hai bộ hàm. Đánh giá thời gian biên dịch, tính ổn định ABI, khả năng mở rộng sang `long double`, và kích thước binary.
11. **(Mini-project)** Chọn một interface thư viện robotics thật mà bạn dùng (ví dụ callback subscription của `rclcpp`, `cv::Mat`, `Eigen::Map`, hay `tf2::Buffer`) và viết một bản kiểm toán quyền sở hữu một trang (hàm, chủ sở hữu, vòng đời, thread, báo lỗi, rủi ro ABI) cộng một wrapper hoặc test 30 dòng chứng minh một rủi ro.

## Cài đặt tham khảo

Một mô hình đầy đủ trong một file của một thư viện với ABI C (opaque handle, mã lỗi, không có exception qua ranh giới, một hook kiểm thử) và wrapper RAII C++. Trong một dự án thật, phần giữa được biên dịch thành `libarm.so` và wrapper nằm trong header được cài đặt. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

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

Các lệnh dùng để khảo sát và phá vỡ tương thích nhị phân:

```
g++ -std=c++17 -shared -fPIC mylib.cpp -o libmy.so
nm -D libmy.so | grep ' T '          # exported symbols; add -C to demangle
ldd ./app                            # which shared libraries are resolved
g++ -shared -fPIC pose_v1.cpp -o libpose.so && g++ app.cpp -L. -lpose -Wl,-rpath,'$ORIGIN' -o app && ./app   # x=1 y=2
g++ -shared -fPIC pose_v2.cpp -o libpose.so && ./app                                                        # x=1 y=9
```

## Thực hành độc lập

### Mục tiêu

Cài đặt một interface C với opaque handle và mã lỗi, bọc nó trong một class RAII chỉ-move, chứng minh bằng test rằng quyền sở hữu và lỗi được xử lý, và viết bản kiểm toán quyền sở hữu ghi tài liệu cho interface.

### Chuẩn bị

`g++` với C++17 (`nm`, `ldd` cho bước shared library tùy chọn). Lưu starter rồi các test bên dưới nó thành `lab.cpp`; build bằng `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab`.

### Nhiệm vụ

1. Định nghĩa `struct rc_arm`, phần ghi sổ live-count và cài đặt `rc_arm_create`, `rc_arm_destroy`, `rc_arm_dof`, `rc_strerror`, `rc_live_arms`. Bọc các thân hàm trong `try/catch(...)`.
2. Cài đặt `rc_arm_set_joint` và `rc_arm_get_joint` với mọi mã lỗi, đảm bảo một lời gọi bị từ chối không thay đổi gì.
3. Cài đặt `check`, thông báo của `Error` và `Arm` (constructor, `set`, `get`, `dof`); các phép move mặc định phải để một `Arm` đã bị move throw `Error(RC_ERR_NULL)`.
4. Chạy các test dưới ASan và xác nhận `rc_live_arms()` trở về 0 sau mỗi scope (kể cả khi một exception được throw).
5. Tách file: biên dịch phần C-API thành `libarm.so` và kiểm tra `nm -D libarm.so | grep rc_` cho thấy các tên không bị mangle; link một `main` nhỏ với nó.
6. Viết bản kiểm toán quyền sở hữu (một bảng 7 hàm với chủ sở hữu, vòng đời, an toàn thread, lỗi, rủi ro ABI) và một đoạn về cách bạn mở rộng struct ở phiên bản 2 mà không phá các binary cũ.

### Code khởi đầu

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

### Kiểm thử

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

### Kết quả mong đợi

```
all tests passed
```

Với các stub, lời gọi đầu tiên kết thúc với `NotImplemented`. Với bước shared library, `nm -D libarm.so` nên liệt kê `rc_arm_create`, `rc_arm_destroy`, `rc_arm_set_joint`, `rc_arm_get_joint`, `rc_arm_dof`, `rc_strerror` và `rc_live_arms` đúng như đã viết, không có tiền tố `_Z`.

### Thử thách mở rộng

Thêm `rc_version()` và một field `size` vào một struct tùy chọn public để thư viện có thể phát hiện phiên bản struct nào mà bên gọi đã biên dịch; hoặc gọi shared library từ Python bằng `ctypes` và viết một context manager Python có cùng ngữ nghĩa sở hữu như `Arm`.

### Thực hành với thư viện

`ctypes` trong standard library của Python là người tiêu dùng thực tế của một ABI C, và là bài kiểm tra tốt nhất rằng ranh giới của bạn sạch. Đặt các khai báo interface và phần cài đặt (mọi thứ phía trên comment "C++ wrapper", cùng các include của nó, không có `main`) vào `arm.cpp`, build shared library, và gọi nó từ Python:

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

Kỳ vọng: `library track ok`. Script cho thấy wrapper C++ `Arm` làm gì trong một ngôn ngữ khác: handle là một địa chỉ mờ (opaque), mã lỗi trở thành exception, và `rc_live_arms()` chứng minh arm được giải phóng khi khối `with` kết thúc. Thử gọi một hàm kiểu `cxx_` (một hàm C++ bị mangle) qua `ctypes` bằng tên thường: nó thất bại với `AttributeError`. Nếu bạn biên dịch một hàm ném exception được xuất dưới dạng `extern "C"` và gọi nó từ đây, process sẽ abort, như trong phần lý thuyết.

## Kiểm chứng

- `nm -D` trên mọi bản release: danh sách symbol được xuất chính là ABI. So sánh nó giữa các phiên bản (các công cụ như `abidiff` của libabigail tự động hóa việc so sánh kiểu và symbol).
- Viết một test build ứng dụng với header phiên bản N và chạy nó với binary thư viện phiên bản N+1.
- Đếm tài nguyên sống bằng một hook kiểm thử (ở đây `rc_live_arms`) và assert nó bằng 0 ở cuối mỗi test và sau các exception được throw.
- Chạy dưới ASan/UBSan và, với thread, TSan (CPP08, CPP10); thử API C từ ngôn ngữ thứ hai (Python `ctypes`) để chứng minh nó thực sự là C.
- Checklist rà soát cho mỗi hàm: chủ sở hữu, vòng đời, thread, đường báo lỗi, khả năng null; người rà soát phải trả lời được mà không cần đọc phần cài đặt.
- Kiểm tra `sizeof` và `offsetof` của các struct public bằng `static_assert` để thay đổi bố cục làm hỏng build.

## Lỗi thường gặp

| Sai lầm | Hậu quả |
|---|---|
| Exception thoát khỏi một hàm `extern "C"` | `terminate` hoặc undefined behavior ở phía gọi (được minh họa bằng `ctypes`) |
| Trả về `s.c_str()` của một `std::string` cục bộ | con trỏ treo; văn bản rác hoặc crash |
| Chèn một field vào giữa struct public | binary cũ đọc sai field (`y=9` thay vì `y=2`), có thể hỏng bộ nhớ |
| `std::string` trong chữ ký của `.so` dựng sẵn với cờ ABI libstdc++ khác | lỗi link `undefined reference to f(std::__cxx11::basic_string...)` |
| Cấp phát trong thư viện và `delete` ở phía gọi | hỏng heap khi allocator khác nhau |
| Thêm một hàm ảo vào class public | bố cục vtable đổi; subclass cũ crash |
| Callback với dữ liệu người dùng `void*` sống lâu hơn đối tượng của nó | use after free trên thread của driver |
| Định nghĩa destructor của class pimpl inline trong header | lỗi `incomplete type` |
| Copy nông một handle kiểu `cv::Mat` được cho là copy sâu | hai chủ sửa một buffer; data race hoặc hỏng dữ liệu |
| Chuỗi `cam_error()` toàn cục với nhiều thread | race; sai thông báo cho sai thread |

## Phương án khác và đánh đổi

- **API C + wrapper C++ so với API C++.** Ranh giới C sống sót qua thay đổi compiler, dùng được từ Python/Rust và có thể đánh phiên bản, nhưng dài dòng và mất an toàn kiểu cho đến khi được bọc. Một API C++ thuần đẹp hơn nhưng buộc mọi người dùng vào một toolchain; chấp nhận được khi mọi thứ được build cùng nhau (ví dụ trong một workspace ROS 2).
- **Pimpl so với opaque handle C.** Pimpl giữ cú pháp class C++ và cho phép exception phía sau, nhưng vẫn có ABI C++ (tên bị mangle, kiểu chuẩn); handle C nghiêm ngặt hơn và di động.
- **Chỉ header so với đã biên dịch.** Chỉ header dễ phân phối và generic nhưng kéo dài thời gian biên dịch và không có hợp đồng ABI; thư viện đã biên dịch cho build nhanh hơn và che giấu phần bên trong nhưng đòi hỏi kỷ luật ABI và một hệ thống build.
- **Interface ảo so với bảng con trỏ hàm.** Class trừu tượng là idiom nhưng mong manh qua các binary; một struct các con trỏ hàm (như trong API plugin C) có bố cục cố định có thể mở rộng bằng cách thêm vào cuối.
- **Exception so với mã lỗi so với `std::expected`.** Exception cho code sạch trong một binary; mã lỗi đi qua ranh giới ngôn ngữ; `std::expected` (C++23, hoặc `tl::expected`) cho lỗi tường minh không có exception trong code real-time cứng.
- **Đánh phiên bản ngữ nghĩa (semantic versioning).** Mã hóa hợp đồng: bản patch giữ ABI; bản minor chỉ thêm; bản major có thể phá vỡ và đổi SONAME (`libfoo.so.2`).

## Vận dụng và ghi nhớ

Đây là cùng một vấn đề trong mọi hệ sinh thái: module mở rộng Python và `ctypes` cần một ABI C; message ROS 2 được định nghĩa bằng IDL chính là để bố cục được sinh ra chứ không viết tay; Rust FFI và các crate `cxx` thực thi một ranh giới tường minh; các bản phân phối Linux theo dõi SONAME của mọi thư viện. Để ghi nhớ: sau một tuần, viết từ trí nhớ mẫu hai tầng (opaque handle, create/destroy, mã lỗi, wrapper với `unique_ptr` và deleter) và liệt kê sáu loại thay đổi phá vỡ ABI; rà soát một dependency trong dự án của bạn bằng bảng kiểm toán.

## Đáp án bài tập

1. `c_add` có thể gọi bằng tên thường từ `ctypes`: nó có liên kết C, nên symbol của nó chỉ là `c_add`. Các hàm khác bị compiler C++ mangle: `_Z7cxx_addii` mã hóa `_Z` (một symbol C++), `7cxx_add` (một tên 7 ký tự), và `ii` (hai tham số `int`); `_ZN5robot8cxx_add2Eii` thêm namespace `robot`; hàm vector mã hóa các đối số template và allocator. Tên bị mangle phụ thuộc compiler, và một kiểu chuẩn như `std::vector` trong chữ ký cũng làm bố cục thành một phần của ABI.
2. (a) Chỉ phá vỡ ABI (`sizeof` đổi, mã nguồn vẫn biên dịch). (b) không cái nào (tương thích cả hai chiều). (c) Chỉ phá vỡ ABI (bố cục vtable) và mã nguồn của subclass vẫn biên dịch. (d) Tương thích API nhưng giá trị mặc định được nướng vào phía gọi lúc biên dịch, nên binary cũ giữ giá trị mặc định cũ: một sự không khớp hành vi lặng lẽ (coi như liên quan ABI). (e) không cái nào. (f) cả hai: mã nguồn thường vẫn biên dịch (chuyển đổi ngầm) nhưng symbol/chữ ký đổi (`long` so với `int` là một tên mangle khác và độ rộng calling convention khác), nên binary cũ lỗi link hoặc truyền dữ liệu sai độ rộng.
3. `Frame* grab();` nói rằng một con trỏ được trả về; không nói: chủ sở hữu, vòng đời, ý nghĩa của null. `void put(Frame*);` nói một con trỏ đi vào; không nói: bên được gọi có nhận sở hữu không, nó có thể null không, nó có được lưu không? `const char* name() const;` văn bản chỉ đọc; không nói: hợp lệ đến khi nào (vòng đời đối tượng, lời gọi tiếp theo?). `void set_cb(Callback, void*);` không nói: thread của lời gọi, vòng đời dữ liệu người dùng, liệu nó có được gọi sau khi hủy đăng ký không. `std::unique_ptr<Map> load(const std::string&);` nói: bên gọi nhận sở hữu độc quyền; đối số được mượn trong lúc gọi; nó vẫn có thể throw hoặc trả null trừ khi được ghi tài liệu.
4. Bug 1: một exception thoát khỏi hàm `extern "C"` (UB hoặc terminate khi bên gọi là C); sửa bằng cách bắt và trả về một giá trị lỗi (ví dụ `nullptr` hoặc một status). Bug 2: `s.c_str()` trỏ vào một string cục bộ bị hủy lúc return: treo. Cách sửa: trả về con trỏ tới vùng lưu trữ tĩnh (một buffer `static thread_local std::string`, ghi tài liệu "hợp lệ đến lời gọi tiếp theo trên thread này") hoặc ghi vào một buffer do bên gọi cung cấp `int describe(int code, char* buf, size_t n)`.
5. Output `7 7 1`: `b = a` copy handle nhưng chia sẻ buffer, nên `fill(7)` đổi cả `a` và `b`; `clone()` copy dữ liệu, nên `c` vẫn là 1. Bug robotics: một callback lưu `msg_image` (một bản copy nông) trong khi driver tái sử dụng buffer cho frame tiếp theo sẽ lặng lẽ thấy dữ liệu đổi (hoặc race với thread khác); cách sửa là `clone()` hoặc lưu một message chia sẻ bất biến (`shared_ptr<const Msg>`).
6. Trong header khai báo `~Planner();` và các phép move (`Planner(Planner&&) noexcept; Planner& operator=(Planner&&) noexcept;`), và định nghĩa chúng trong `.cpp` nơi `struct Planner::Impl { ... };` đã đầy đủ (`Planner::~Planner() = default;`). Nếu không, destructor inline ngầm định khởi tạo `std::default_delete<Impl>` ở nơi `Impl` chưa đầy đủ, gây ra "invalid application of 'sizeof' to incomplete type".
7. Header của ứng dụng nói `y` ở offset 8, nhưng phiên bản 2 đặt `z` ở offset 8 và `y` ở offset 16; thư viện ghi `z=9` tại offset 8, mà ứng dụng đọc như `y`, và thư viện cũng ghi 8 byte vượt quá struct 16 byte của ứng dụng (undefined behavior, một tràn stack trong ứng dụng). Tên symbol không đổi, nên linker không phàn nàn. Cách phát triển an toàn: thêm field mới ở cuối một struct mang field `size` (hoặc phiên bản) của riêng nó làm member đầu tiên và để thư viện chỉ điền các field mà size của bên gọi bao phủ; ẩn struct sau một opaque handle với các hàm accessor (`pose_get_y`); thêm một hàm và một struct mới (`get_pose_v2`) và giữ hàm cũ.
8. Lúc link bạn nhận `undefined reference to f(std::string const&)` vì với ABI mặc định (mới) kiểu của tham số là `std::__cxx11::basic_string<...>` và mangle khác với `std::basic_string<...>` cũ; symbol trong `.so` không khớp. Chiến lược: một interface C (`const char*` và độ dài); phát hành bản build cho cả hai giá trị của `_GLIBCXX_USE_CXX11_ABI` (và ghim một phiên bản compiler); phát hành thư viện dưới dạng mã nguồn hoặc static library build với toolchain của người dùng; hoặc cung cấp một wrapper chỉ có header chuyển sang interface C.
9. Rủi ro: `Gripper(const std::string&)` đặt `std::string` vào ABI; `poll()` trả một con trỏ thô tới trạng thái nội bộ (ai sở hữu, vòng đời, an toàn thread? nó có bị lần poll tiếp theo ghi đè không?); `std::function` trong `on_contact` (ABI và thread nào gọi nó; exception qua lời gọi; vòng đời của các capture); `virtual close` trong một class được xuất (vtable và tương thích subclass; cũng thiếu virtual destructor); data member public `std::vector<double> history` (bố cục và an toàn thread, ai cũng sửa được); `GripperState` là struct public không thể lớn thêm; không có báo lỗi cho `close` và constructor (exception hay mã?). Thiết kế lại: opaque handle `grip*` với `grip_open/close`, `grip_poll(grip*, GripperState* out, uint32_t size)` copy vào bộ nhớ của bên gọi, `grip_set_contact_callback(grip*, void(*)(const GripperState*, void*), void*)` với thread được ghi tài liệu và catch-all, các hàm trả mã, cộng một wrapper C++ với RAII.
10. (i) Chỉ header: không có vấn đề ABI, kiểu nào cũng được (`long double`), nhưng mọi translation unit biên dịch lại code (build lâu hơn, binary lớn hơn). (ii) Đã biên dịch với explicit instantiation (`extern template class Filter<float>; extern template class Filter<double>;`): build nhanh hơn, object nhỏ hơn; bố cục của `Filter<float>` và `Filter<double>` trở thành ABI, và `long double` cần một instantiation mới (một thay đổi của thư viện). (iii) Một API C với các bộ hàm `filter_f32_*` và `filter_f64_*`: ổn định nhất, dùng được từ các ngôn ngữ khác, dài dòng, và mỗi kiểu mới cần hàm mới. Chọn (i) cho thư viện header generic dùng trong một build; (ii) cho thư viện có một nhúm kiểu được hỗ trợ; (iii) khi thư viện được giao dưới dạng binary cho các toolchain không biết trước.
11. Một câu trả lời tốt gồm: một bảng với ít nhất sáu hàm; với mỗi hàm: chủ sở hữu, vòng đời, ngữ cảnh thread/callback, cơ chế báo lỗi và rủi ro ABI; ít nhất một rủi ro được chứng minh bằng một chương trình ngắn (ví dụ copy nông, view treo, hoặc vòng đời callback) và cách sửa (clone, kiểu chủ sở hữu, hoặc hủy đăng ký trong destructor); và một khuyến nghị về cách bọc nó.

## Đọc thêm

- [C++ Core Guidelines: Interfaces](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - các quy tắc I.1-I.27 về interface tường minh, có kiểu, ổn định; I.11 (quyền sở hữu) và I.26-I.27 (ABI) là trung tâm ở đây.
- [KDE: Binary Compatibility Issues With C++](https://community.kde.org/Policies/Binary_Compatibility_Issues_With_C%2B%2B) - danh sách thực tế các thay đổi tương thích mã nguồn, tương thích nhị phân và phá vỡ.
- [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html) - đặc tả về name mangling, bố cục đối tượng và vtable do GCC và Clang dùng trên Linux.

**Thực hành thêm:** [hướng dẫn tương thích nhị phân của KDE](https://community.kde.org/Policies/Binary_Compatibility_Issues_With_C%2B%2B) (một danh sách nên và không nên để phân loại, như bài tập 2), sách hướng dẫn libstdc++ về [dual ABI](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html) (tái hiện bài tập 8 với `-D_GLIBCXX_USE_CXX11_ABI=0`), [tài liệu `ctypes`](https://docs.python.org/3/library/ctypes.html) (gọi `libarm.so` của bạn), cppreference về [language linkage](https://en.cppreference.com/w/cpp/language/language_linkage) và [pimpl idiom](https://en.cppreference.com/w/cpp/language/pimpl), và [phần interface (I)](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#i-interfaces) của Core Guidelines cho bản kiểm toán của bài tập 11.
