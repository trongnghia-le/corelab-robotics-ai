---
{"title": "Debug và kiểm thử: sanitizer, debugger và test harness", "summary": "Tìm lỗi bộ nhớ và lỗi logic bằng sanitizer và debugger, rút gọn một lỗi thành ca tối thiểu, và khóa bản sửa lại bằng một regression test.", "objectives": ["Chọn đúng công cụ (AddressSanitizer, UBSan, ThreadSanitizer, Valgrind, GDB) cho từng loại bug.", "Đọc một báo cáo sanitizer và xác định dòng lỗi, kích thước truy cập và nơi cấp phát.", "Rút gọn một chương trình lỗi thành một reproducer tối thiểu.", "Viết một regression test bằng một harness nhỏ, fail trước khi sửa và pass sau khi sửa."]}
---
## Vì sao điều này quan trọng

C++ không ngăn bạn đọc quá cuối mảng, dùng một đối tượng sau khi nó bị move hoặc bị giải phóng, hay cộng hai số bị tràn. Những lỗi này là *undefined behavior*: chương trình có thể crash, in ra một con số sai nhẹ, hoặc có vẻ chạy tốt hàng tháng rồi hỏng trên một compiler khác hay vào một ngày khác. Trên robot, triệu chứng thường xa nguyên nhân: một ước lượng vận tốc lệch vài phần trăm, hoặc một node chết mỗi giờ một lần. Các công cụ trong bài này biến sự hỏng hóc thầm lặng thành một thông báo lỗi tức thì, có chỉ ra vị trí, và kỷ luật rút gọn lỗi rồi thêm regression test bảo đảm cùng một bug không bao giờ quay lại. Trên thực tế, hầu hết các đội C++ chuyên nghiệp chạy unit test dưới AddressSanitizer và UBSan ở mỗi commit.

## Trực giác

Debug là phương pháp khoa học áp dụng lên một chương trình: quan sát một thất bại, hình thành giả thuyết, thiết kế một thí nghiệm có thể bác bỏ nó, lặp lại. Các công cụ khác nhau ở thứ chúng cho bạn quan sát:

- **Sanitizer** gắn thêm mã (instrument) vào chương trình lúc biên dịch và kiểm tra mọi truy cập bộ nhớ hay phép tính số học khi chạy. Nó tìm thấy bug *khi thao tác sai được thực thi*, ngay cả khi chương trình lẽ ra có vẻ chạy tốt.
- **Debugger** (GDB) dừng một chương trình đang chạy tại điểm bạn chọn và cho bạn kiểm tra biến cùng call stack, từng bước một. Nó cho thấy trạng thái ở thời điểm crash.
- **Test harness** tự động hóa thí nghiệm: cho một đầu vào và kết quả mong đợi, nó nói pass hay fail, mọi lần, trong vài giây.

Rút gọn là bước người ta hay bỏ qua. Một thất bại trên 10,000 dòng và một log 1 GB rất khó suy luận; cùng thất bại đó trên một chương trình 6 dòng và ba con số thường hiển nhiên.

![Vòng lặp debug từ lần chạy lỗi tới reproducer tới sanitizer hoặc debugger tới sửa lỗi và regression test, cùng các loại bug mà mỗi công cụ bắt được](/lesson-figures/CPP08.svg)

*Tái hiện, rút gọn, xác định vị trí bằng công cụ, sửa, rồi thêm regression test và chạy lại dưới các sanitizer.*

## Lý thuyết và suy dẫn

### Công cụ nào tìm bug nào

| Công cụ và cờ | Tìm | Chi phí điển hình |
|---|---|---|
| AddressSanitizer `-fsanitize=address` | tràn buffer heap/stack/global, use-after-free, use-after-scope, double free, rò rỉ (LeakSanitizer, trên Linux) | chậm khoảng 2x, bộ nhớ 2-3x |
| UndefinedBehaviorSanitizer `-fsanitize=undefined` | tràn số nguyên có dấu, dịch bit sai, dùng con trỏ null/lệch căn, chuyển đổi ngoài khoảng | nhỏ |
| ThreadSanitizer `-fsanitize=thread` | data race (CPP10) | chậm 5-15x; không kết hợp được với ASan |
| MemorySanitizer (clang) / Valgrind | đọc bộ nhớ chưa khởi tạo; Valgrind không cần biên dịch lại | Valgrind chậm khoảng 20-50x |
| Bản build GDB `-g` | vị trí crash, call stack, giá trị biến, theo dõi một giá trị thay đổi | không có cho đến khi dùng |
| Cảnh báo compiler `-Wall -Wextra -Wconversion` | nhiều lỗi trước khi chạy | miễn phí |

Biên dịch với `-g` (thông tin debug) và `-fno-omit-frame-pointer` (stack trace sạch), ở `-O0` hoặc `-O1`. Tối ưu hóa có thể khiến một biến bị "optimized out" trong debugger.

### Đọc báo cáo AddressSanitizer

Vài dòng đầu mang toàn bộ chẩn đoán:

```
ERROR: AddressSanitizer: heap-buffer-overflow on address 0x504000000038 ...
READ of size 8 at 0x504000000038 thread T0
    #0 ... in moving_average(...) buggy.cpp:10
    #1 ... in main buggy.cpp:18
0x504000000038 is located 0 bytes to the right of 40-byte region [0x504000000010,0x504000000038)
allocated by thread T0 here: ...
```

- *loại bug*: heap-buffer-overflow (cũng có stack-buffer-overflow, heap-use-after-free, ...);
- *cái gì*: một lần READ kích thước 8 (một `double`);
- *ở đâu*: frame #0, `buggy.cpp` dòng 10; bên gọi là frame #1;
- *đối tượng nào*: địa chỉ nằm cách 0 byte bên phải một vùng 40 byte, tức năm double, vậy là phần tử chỉ số 5 của một vector 5 phần tử đã bị đọc, vượt quá cuối một vị trí.

Luôn đọc lỗi *đầu tiên*; các lỗi sau có thể là hệ quả.

### Những điều cốt yếu của debugger

`gdb ./prog`, rồi `run`, `bt` (backtrace), `frame N`, `info locals`, `print expr`, `break file:line`, `watch var`, `continue`, `next`, `step`. Chế độ batch: `gdb -batch -ex run -ex bt ./prog`. Với crash bên trong một library, `bt` vẫn cho thấy frame gọi của bạn. Một `std::unique_ptr` đã bị move hiện ra là `get() = 0x0` trong GDB, giải thích ngay một segmentation fault tại phép dereference đó.

### Test harness và regression test

Một test là một khẳng định có thể thực thi: *với đầu vào X, kết quả là Y*. Một harness cho nó cấu trúc: test có tên, trạng thái độc lập, thông báo lỗi hiện giá trị mong đợi và giá trị thực, một bản tóm tắt và mã thoát khác không khi thất bại để CI nhận ra. Test tốt

- dùng các giá trị mong đợi tính bằng tay (không phải hàm đang được kiểm thử, vì như vậy chỉ chứng minh nó bằng chính nó);
- bao phủ biên (rỗng, một phần tử, cửa sổ bằng độ dài, số không), ca điển hình và ca lỗi;
- kiểm tra bất biến và tính chất (cửa sổ 1 là phép đồng nhất; độ dài kết quả là $n-w+1$);
- mang tính xác định (seed cố định, đồng hồ cố định) và độc lập với nhau.

Một **regression test** ghi lại một bug đã tìm ra: nó fail trên code hỏng và pass trên code đã sửa. Viết nó *trước* khi sửa chứng minh rằng nó phát hiện được bug.

Với so sánh số thực dùng dung sai: `|a - b| <= tol` là sai khi một trong hai giá trị là NaN, đó là cách an toàn; `!(|a-b| > tol)` sẽ chấp nhận NaN.

### Rút gọn và chia đôi

Nếu một thất bại cần $N$ phần tử và một thủ phạm duy nhất, việc chia đôi đầu vào tìm ra nó trong $\lceil\log_2 N\rceil$ lần chạy. Khi thất bại cần nhiều phần tử, delta debugging loại bỏ từng khối và giữ lại mọi lần loại bỏ mà vẫn còn thất bại. Với lịch sử, `git bisect` tìm kiếm nhị phân trên các commit: 1000 commit cần tối đa $\lceil\log_2 1000\rceil=10$ lần build. Với thất bại hiếm, số lần lặp cần để thấy một thất bại có xác suất $p$ với độ tin cậy $1-\alpha$ là $n\ge\ln\alpha/\ln(1-p)$.

## Ví dụ có lời giải

**Bug.** `moving_average` lẽ ra trả về một giá trị trung bình cho mỗi cửa sổ đầy đủ. Chạy không có sanitizer:

```
$ g++ -std=c++17 -g buggy.cpp -o buggy && ./buggy
3 4.5 6 4.5
```
Output mong đợi cho `{1,2,3,4,5}` với cửa sổ 2 là `1.5 2.5 3.5 4.5`. Các con số sai, nhưng không có gì crash.

1. **Giả thuyết từ các con số**: giá trị đầu tiên 3 bằng $(1+2+3)/2$: ba phần tử được cộng nhưng chia cho 2. Vòng lặp có thừa một lần lặp.
2. **Xác nhận bằng ASan**: `g++ -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer buggy.cpp && ./a.out` báo `heap-buffer-overflow`, `READ of size 8`, `buggy.cpp:10`, và "0 bytes to the right of 40-byte region": vector chứa 5 double, và cửa sổ cuối đã đọc chỉ số 5. Với cửa sổ cuối, $i=3$, $k=2$ cho chỉ số $3+2=5$, nằm ngoài phạm vi. Các output trước đó cũng sai, nhưng chỉ lần đọc này là lỗi bộ nhớ.
3. **Rút gọn**: với `{1,2,3}` và cửa sổ 2, output lẽ ra là `1.5 2.5` và ASan vẫn kích hoạt ở cửa sổ thứ hai (chỉ số $1+2=3$). Nhỏ hơn nữa: `{1,2}` và cửa sổ 1 lẽ ra cho `1 2`; chương trình in `3` rồi `2` cộng với bất cứ thứ gì nằm ở chỉ số 2 (mỗi cửa sổ đọc thừa một phần tử). Reproducer tối thiểu là một phần tử và cửa sổ 1: cửa sổ duy nhất đọc chỉ số 1 của một vector 1 phần tử.
4. **Sửa**: đổi `k <= w` thành `k < w`.
5. **Regression test** (tính bằng tay): `moving_average({1,2,3,4,5}, 2)` bằng `{1.5, 2.5, 3.5, 4.5}`; cửa sổ 1 trả về chính đầu vào; cửa sổ 5 trả về `{3}`; cửa sổ 6 và 0 trả về rỗng.
6. **Xác nhận**: test fail trên code cũ (giá trị đầu 3 chứ không phải 1.5, có hoặc không có sanitizer) và pass trên code mới dưới ASan và UBSan, không có báo cáo nào.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: AddressSanitizer wiki, list of detected errors)* Ghép mỗi bug với công cụ tốt nhất: (a) ghi một phần tử vượt quá mảng heap; (b) đọc một phần tử vector sau khi `push_back` đã cấp phát lại nó; (c) phép cộng `int` bị tràn; (d) hai thread cùng tăng một `int` thường; (e) một `new` không bao giờ được delete; (f) đọc một `double` cục bộ trước khi nó được gán.
2. **(Dễ)** Đọc đoạn trích báo cáo này và nêu loại bug, kích thước truy cập, dòng source, kích thước cấp phát và lỗi lệch bao nhiêu có khả năng nhất: `heap-buffer-overflow ... READ of size 8 ... in moving_average buggy.cpp:10 ... 0x...38 is located 0 bytes to the right of 40-byte region`.
3. **(Dễ)** *(Adapted from: Pro Git, Debugging with Git - binary search)* Một regression xuất hiện đâu đó trong 1000 commit. `git bisect` cần tối đa bao nhiêu lần build? Một tìm kiếm tuyến tính trên các commit cần bao nhiêu trong trường hợp xấu nhất?
4. **(Trung bình)** Giải thích vì sao chương trình không dùng sanitizer in ra `3 4.5 6 4.5` mà vẫn "chạy được". Tự suy ra bằng tay bốn con số mà vòng lặp lỗi tính (coi lần đọc ngoài phạm vi là 0) và chỉ ra vì sao con số cuối vô tình bằng giá trị đúng.
5. **(Trung bình)** Tìm bug trong chương trình sau từ output GDB của nó (`frame = std::unique_ptr<Frame> = {get() = 0x0}`, SIGSEGV tại dòng 11) và viết cách sửa tối thiểu. Hai lệnh GDB nào cho thấy bằng chứng?
   ```cpp
   int use(std::unique_ptr<Frame> f) { return f->id; }
   int main() {
     auto frame = std::make_unique<Frame>(Frame{7});
     int a = use(std::move(frame));
     int b = frame->id;
     std::cout << a + b << "\n";
   }
   ```
6. **(Trung bình)** Viết một regression test cho bug moving-average dùng harness `Checker` của bài này. Nó phải fail trên phiên bản lỗi ngay cả khi không dùng sanitizer. Giải thích vì sao khẳng định trên giá trị mạnh hơn việc chờ một crash.
7. **(Trung bình)** *(Adapted from: C++ Core Guidelines, section on testing/assertions, and common unit-test practice)* Thiết kế các ca test cho `wrap_to_pi(a)`, ánh xạ một góc vào $[-\pi,\pi)$. Liệt kê ít nhất tám ca với giá trị mong đợi (đến 5 chữ số thập phân) gồm biên, đầu vào âm, bội của $2\pi$, một đầu vào lớn và NaN.
8. **(Khó)** Một test thất bại trung bình 2 trên mỗi 100 lần chạy. Cần bao nhiêu lần chạy lặp để có 95% khả năng thấy ít nhất một thất bại? Liệt kê bốn nguyên nhân gây flaky trong các test robotics và một công cụ hoặc kỹ thuật cho mỗi nguyên nhân.
9. **(Khó)** Cài đặt `minimize(items, fails)` loại bỏ tham lam các khối (giảm nửa kích thước khối) trong khi bug vẫn còn xuất hiện. Chạy nó trên `list(range(64))` mà bug cần cả 17 và 42 cùng có mặt, và báo cáo danh sách tối thiểu cùng số lần gọi `fails`.
10. **(Khó)** *(Adapted from: GCC documentation, Instrumentation Options)* Thiết kế các job CI cho một repository C++ robotics: những bản build nào (cờ, kiểu build), những test nào dưới sanitizer nào, và vì sao ASan và TSan cần các job riêng. Nêu mỗi job sẽ bắt được gì trong bài tập 1 và 8.
11. **(Mini-project)** Lấy `buggy.cpp`. Chạy nó dưới ASan, Valgrind và GDB; điền một bảng (công cụ, lệnh, dòng output then chốt, điều nó dạy bạn); rút gọn đầu vào tới ca lỗi nhỏ nhất bằng tay; viết regression test bằng harness; sửa; cho thấy lần chạy xanh dưới ASan+UBSan.

## Cài đặt tham khảo

Trước hết là chương trình lỗi và các bước chính xác dùng trong ví dụ có lời giải. Sau đó là một test harness nhỏ (`Checker`, `Test`, `run_tests`) cùng hàm đã sửa, chạy được như một file duy nhất.

`buggy.cpp`:

```cpp
#include <cstddef>
#include <iostream>
#include <vector>

// Moving average with window w over v; returns one value per full window.
std::vector<double> moving_average(const std::vector<double>& v, std::size_t w) {
  std::vector<double> out;
  for (std::size_t i = 0; i + w <= v.size(); ++i) {
    double sum = 0.0;
    for (std::size_t k = 0; k <= w; ++k) sum += v[i + k];  // BUG: should be k < w
    out.push_back(sum / static_cast<double>(w));
  }
  return out;
}

int main() {
  const std::vector<double> v{1.0, 2.0, 3.0, 4.0, 5.0};
  for (double x : moving_average(v, 2)) std::cout << x << ' ';
  std::cout << '\n';
}
```

Các lệnh:

```
g++ -std=c++17 -g buggy.cpp -o buggy && ./buggy                       # wrong output, no crash
g++ -std=c++17 -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer buggy.cpp -o buggy_asan && ./buggy_asan
valgrind --error-exitcode=9 ./buggy                                    # "Invalid read of size 8"
gdb -batch -ex run -ex bt -ex "info locals" ./segv                     # crash site and variables
```

Harness và hàm đã sửa:

```cpp
// CPP08 reference: a tiny test harness (Checker + run_tests) and the fixed moving average.
#include <cmath>
#include <cstddef>
#include <exception>
#include <functional>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

class Checker {
 public:
  void check(bool ok, const std::string& what) {
    ++checks_;
    if (!ok) failures_.push_back(what);
  }
  // |a - b| <= tol. NaN never passes.
  void check_near(double a, double b, double tol, const std::string& what) {
    check(std::fabs(a - b) <= tol, what + " (got " + std::to_string(a) + ", expected " + std::to_string(b) + ")");
  }
  // Passes only if f() throws an exception of type E.
  template <class E, class F>
  void check_throws(F f, const std::string& what) {
    bool threw = false;
    try {
      f();
    } catch (const E&) {
      threw = true;
    } catch (...) {
    }
    check(threw, what + " (expected exception)");
  }
  void fail(const std::string& what) { check(false, what); }
  std::size_t checks() const { return checks_; }
  const std::vector<std::string>& failures() const { return failures_; }

 private:
  std::size_t checks_ = 0;
  std::vector<std::string> failures_;
};

struct Test {
  std::string name;
  std::function<void(Checker&)> fn;
};

// Runs every test, prints "PASS name" or "FAIL name: message" per failure, then a summary
// line "<p> passed, <f> failed". An exception escaping a test counts as a failure of that test
// and must not stop the remaining tests. Returns the number of failed tests.
int run_tests(const std::vector<Test>& tests, std::ostream& out) {
  int passed = 0, failed = 0;
  for (const Test& t : tests) {
    Checker c;
    try {
      t.fn(c);
    } catch (const std::exception& e) {
      c.fail(std::string("uncaught exception: ") + e.what());
    } catch (...) {
      c.fail("uncaught unknown exception");
    }
    if (c.failures().empty()) {
      ++passed;
      out << "PASS " << t.name << "\n";
    } else {
      ++failed;
      for (const std::string& f : c.failures()) out << "FAIL " << t.name << ": " << f << "\n";
    }
  }
  out << passed << " passed, " << failed << " failed\n";
  return failed;
}

// The fixed function from the debugging walk-through (window loop uses k < w).
std::vector<double> moving_average(const std::vector<double>& v, std::size_t w) {
  std::vector<double> out;
  if (w == 0) return out;
  for (std::size_t i = 0; i + w <= v.size(); ++i) {
    double sum = 0.0;
    for (std::size_t k = 0; k < w; ++k) sum += v[i + k];
    out.push_back(sum / static_cast<double>(w));
  }
  return out;
}

// ---- self-test
int main() {
  std::ostringstream os;
  int failed = run_tests(
      {{"ok", [](Checker& c) { c.check(true, "t"); }},
       {"bad", [](Checker& c) { c.check_near(1.0, 2.0, 0.1, "near"); }},
       {"boom", [](Checker&) { throw std::runtime_error("kaput"); }}},
      os);
  if (failed != 2) return 1;
  if (os.str().find("2 failed") == std::string::npos) return 2;
  const auto avg = moving_average({1, 2, 3, 4, 5}, 2);
  if (avg.size() != 4 || avg[3] != 4.5) return 3;
  std::cout << "CPP08 reference self-test passed\n";
}
```

## Thực hành độc lập

### Mục tiêu

Xây một test harness nhỏ, dùng nó để viết regression test cho một bug off-by-one thật, và chứng minh code đã sửa sạch dưới các sanitizer.

### Chuẩn bị

`g++` với C++17. Tùy chọn `gdb` và `valgrind` (`sudo apt install gdb valgrind`). Lưu code khởi đầu và các test bên dưới nó thành `lab.cpp`; build bằng `g++ -std=c++17 -Wall -Wextra -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer lab.cpp -o lab && ./lab`.

### Nhiệm vụ

1. Lưu `buggy.cpp`, chạy nó bình thường và dưới ASan; sao chép bốn dòng đầu của báo cáo và giải mã chúng như trong phần lý thuyết.
2. Rút gọn đầu vào bằng tay tới mảng nhỏ nhất vẫn kích hoạt lỗi ASan.
3. Cài đặt `Checker::check`, `check_near`, `fail`, `check_throws` và các getter.
4. Cài đặt `run_tests` với định dạng output chính xác; đảm bảo một exception thoát ra khỏi một test không làm dừng các test khác.
5. Cài đặt `moving_average` đã sửa, chạy các test dưới ASan+UBSan.
6. Tạm thời đưa lại bug `k <= w` vào `moving_average` của bạn và xác nhận các test thất bại với một thông báo dễ đọc (không cần crash), rồi khôi phục bản sửa.

### Code khởi đầu

```cpp
#include <cmath>
#include <cstddef>
#include <exception>
#include <functional>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

class Checker {
 public:
  // Counts one check; records `what` as a failure message when ok is false.
  void check(bool ok, const std::string& what) { throw std::logic_error("NotImplemented"); }
  // Passes iff |a - b| <= tol. NaN must NOT pass. On failure the message is
  // what + " (got <a>, expected <b>)" using std::to_string.
  void check_near(double a, double b, double tol, const std::string& what) { throw std::logic_error("NotImplemented"); }
  // Passes only if f() throws an exception of type E (any other outcome fails, but must not escape).
  template <class E, class F>
  void check_throws(F f, const std::string& what) { throw std::logic_error("NotImplemented"); }
  // Records an unconditional failure.
  void fail(const std::string& what) { throw std::logic_error("NotImplemented"); }
  std::size_t checks() const { throw std::logic_error("NotImplemented"); }
  const std::vector<std::string>& failures() const { throw std::logic_error("NotImplemented"); }
};

struct Test {
  std::string name;
  std::function<void(Checker&)> fn;
};

// Runs every test with a fresh Checker. Per passing test print "PASS <name>\n"; per failure message
// print "FAIL <name>: <message>\n". An exception escaping a test (std::exception or anything else)
// counts as ONE failure of that test with a message starting "uncaught exception" and must not stop
// the other tests. Finally print "<passed> passed, <failed> failed\n". Return the number failed.
int run_tests(const std::vector<Test>& tests, std::ostream& out) { throw std::logic_error("NotImplemented"); }

// The fixed function from the debugging walk-through: one average per FULL window of w samples;
// w == 0 -> empty result. It must never read outside v.
std::vector<double> moving_average(const std::vector<double>& v, std::size_t w) { throw std::logic_error("NotImplemented"); }
```

### Kiểm thử

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)

int main() {
  // 1. Checker basics
  Checker c;
  c.check(true, "a");
  c.check(false, "b");
  c.check_near(1.0, 1.05, 0.1, "near-ok");
  c.check_near(1.0, 2.0, 0.1, "near-bad");
  c.check_near(NAN, 1.0, 1e9, "nan-must-fail");
  c.check_throws<std::out_of_range>([] { throw std::out_of_range("x"); }, "throws-ok");
  c.check_throws<std::out_of_range>([] {}, "throws-missing");
  c.check_throws<std::out_of_range>([] { throw std::logic_error("other"); }, "throws-wrong-type");
  CHECK(c.checks() == 8);
  CHECK(c.failures().size() == 5);
  CHECK(c.failures()[0] == "b");
  CHECK(c.failures()[1].find("near-bad (got 1.000000, expected 2.000000)") == 0);
  // 2. run_tests output and return value (hand-written expected text)
  std::ostringstream os;
  int failed = run_tests({{"good", [](Checker& k) { k.check(1 + 1 == 2, "math"); }},
                          {"bad", [](Checker& k) { k.check(false, "boom"); }},
                          {"throws", [](Checker&) { throw std::runtime_error("kaput"); }},
                          {"after", [](Checker& k) { k.check(true, "still runs"); }}},
                         os);
  CHECK(failed == 2);
  CHECK(os.str() == "PASS good\nFAIL bad: boom\nFAIL throws: uncaught exception: kaput\nPASS after\n2 passed, 2 failed\n");
  // 3. non-std exception does not escape
  std::ostringstream os2;
  CHECK(run_tests({{"weird", [](Checker&) { throw 42; }}}, os2) == 1);
  // 4. empty suite
  std::ostringstream os3;
  CHECK(run_tests({}, os3) == 0 && os3.str() == "0 passed, 0 failed\n");
  // 5. moving_average: hand computed and regression for the off-by-one
  std::vector<double> v{1, 2, 3, 4, 5};
  auto m = moving_average(v, 2);
  CHECK(m.size() == 4 && m[0] == 1.5 && m[1] == 2.5 && m[2] == 3.5 && m[3] == 4.5);
  CHECK(moving_average(v, 5).size() == 1 && moving_average(v, 5)[0] == 3.0);
  CHECK(moving_average(v, 6).empty() && moving_average(v, 0).empty() && moving_average({}, 3).empty());
  // 6. property: window 1 is the identity; the sum of window averages shifts correctly
  CHECK(moving_average(v, 1) == v);
  std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi

```
all tests passed
```

Với các stub, test đầu tiên kết thúc với `NotImplemented`. Với bug được đưa lại, test 5 của harness thất bại kèm dòng `CHECK` lỗi; sanitizer ngoài ra còn báo `heap-buffer-overflow`.

### Thử thách mở rộng

Thêm một macro `TEST(name) { ... }` với đăng ký tĩnh để không phải liệt kê test bằng tay; thêm tùy chọn dòng lệnh `--filter`; hoặc viết `minimize` (bài tập 9) bằng C++ và dùng nó để thu nhỏ một đầu vào lỗi đọc từ file.

### Thực hành với thư viện

Phiên bản thực tế của `Checker` của bạn là một test framework. GoogleTest (`sudo apt install libgtest-dev`) là lựa chọn thông thường cho code robotics C++ (`ament_cmake_gtest` của ROS 2 bọc nó). Lưu đoạn này thành `gtest_ma.cpp` với `moving_average` đã sửa của bạn ở phía trên.

```cpp
// gtest_ma.cpp : the regression tests of this lesson with GoogleTest instead of your Checker.
// Put the FIXED moving_average (and its includes) above this line, or #include a header that has it.
#include <gtest/gtest.h>
#include <cmath>
#include <vector>

TEST(MovingAverage, HandComputedWindow2) {
  const std::vector<double> v{1, 2, 3, 4, 5};
  const auto m = moving_average(v, 2);
  ASSERT_EQ(m.size(), 4u);                       // ASSERT_* stops this test, EXPECT_* continues
  EXPECT_DOUBLE_EQ(m[0], 1.5);                   // fails on the buggy code (it gives 3)
  EXPECT_DOUBLE_EQ(m[1], 2.5);
  EXPECT_DOUBLE_EQ(m[3], 4.5);
}

TEST(MovingAverage, Edges) {
  const std::vector<double> v{1, 2, 3, 4, 5};
  EXPECT_EQ(moving_average(v, 1), v);            // window 1 is the identity
  EXPECT_EQ(moving_average(v, 5), std::vector<double>{3.0});
  EXPECT_TRUE(moving_average(v, 6).empty());
  EXPECT_TRUE(moving_average(v, 0).empty());
}

TEST(Checker, NaNNeverPasses) { EXPECT_FALSE(std::fabs(NAN - 1.0) <= 1e9); }

// Build and run (also under the sanitizers, as in the lab):
//   g++ -std=c++17 -g -O1 -fsanitize=address,undefined gtest_ma.cpp -lgtest -lgtest_main -pthread -o gt && ./gt
// Bounds checking without ASan: add -D_GLIBCXX_ASSERTIONS and use v.at(i) or v[i] on the buggy
// program; it aborts (SIGABRT, exit code 134) at the faulty index instead of printing wrong numbers.
```

Kỳ vọng: `[  PASSED  ] 3 tests.` Khi đặt lại bug `k <= w`, `HandComputedWindow2` và `Edges` thất bại với một thông báo dễ đọc (`Expected equality of these values ... 3 vs 1.5`) ngay cả khi không có sanitizer. So sánh định dạng output với `run_tests` của bạn.

## Kiểm chứng

- Chứng minh test có thể fail: hoàn nguyên bản sửa (hoặc đột biến code) và kiểm tra test chuyển sang đỏ. Một test chưa bao giờ fail không chứng minh gì.
- Chạy cả bộ test dưới `-fsanitize=address,undefined`, và lần nữa ở một bản build tối ưu hóa; so sánh kết quả. Khác biệt chỉ tới undefined behavior.
- So sánh với một oracle chậm nhưng hiển nhiên đúng (ở đây là tổng trực tiếp trên từng cửa sổ) trên các đầu vào ngẫu nhiên.
- Kiểm tra mã trả về (`echo $?`) của chương trình test, vì CI dùng nó.
- Sau khi rút gọn, kiểm tra lại rằng chương trình rút gọn vẫn cho thấy *cùng* lỗi, không phải lỗi khác.
- Với test flaky, lặp lại: `ctest --repeat until-fail:200` hoặc một vòng lặp shell; ghi lại seed.

## Lỗi thường gặp

| Sai lầm | Hậu quả |
|---|---|
| Debug mà không có reproducer | thay đổi chỉ là đoán mò; bug "biến mất" rồi quay lại |
| Dựa vào crash làm test | UB có thể không crash (ở đây chương trình in ra số sai) |
| Giá trị mong đợi lấy từ code đang được kiểm thử | test pass trong khi bug vẫn còn |
| `assert` trong test biên dịch với `-DNDEBUG` | test không làm gì ở Release (CPP07) |
| Debug một bản build đã tối ưu hóa | biến bị "optimized out", dòng nhảy lung tung |
| Sửa triệu chứng (clamp chỉ số) thay vì nguyên nhân | một giá trị sai khác xuất hiện sau đó |
| So sánh double bằng `==` sau khi tính toán | thất bại giả; dùng dung sai, và làm cho NaN fail |
| Chỉ kiểm thử một kiểu build | bug UB ẩn ở một mức tối ưu hóa |
| Trộn ASan và TSan trong một binary | không được hỗ trợ; dùng các bản build riêng |
| Bỏ qua lỗi sanitizer đầu tiên và đọc lỗi cuối | lỗi đầu tiên mới là nguyên nhân gốc |

## Phương án khác và đánh đổi

- **Sanitizer so với Valgrind.** Sanitizer cần build lại nhưng đủ nhanh để chạy cả bộ test; Valgrind chạy trên bất kỳ binary nào nhưng chậm. Dùng Valgrind khi bạn không thể build lại.
- **Debugger so với print.** Print nhanh và dùng được trong log production; debugger cho stack và trạng thái mà không phải sửa code. Với code nhạy cảm về thời gian, log kèm timestamp có thể gây nhiễu ít hơn breakpoint.
- **Harness viết tay so với framework.** Một harness 50 dòng đủ để học; GoogleTest, Catch2 và doctest thêm fixture, test tham số hóa và mocking, và tích hợp với CTest.
- **Unit so với integration so với property-based test.** Unit test nhanh và chính xác; integration test bắt lỗi interface; property-based test (đầu vào ngẫu nhiên cộng bất biến) tìm ra các ca không ngờ tới.
- **Container có kiểm tra.** `-D_GLIBCXX_ASSERTIONS` hoặc `.at()` cho kiểm tra biên rẻ trong bản build debug; hãy bật chúng trong test.
- **Phân tích tĩnh** (`clang-tidy`, `cppcheck`) tìm một số bug mà không chạy code, kèm các cảnh báo sai.

## Vận dụng và ghi nhớ

Cùng vòng lặp này áp dụng trong Python (`pytest`, `pdb`, `faulthandler`) và trong ROS 2 (`ros2 bag` để phát lại một đầu vào lỗi, `launch_testing` cho integration test, `colcon test`). Một bag đã ghi là phiên bản robotics của reproducer. Để ghi nhớ: giữ một checklist một trang (tái hiện, rút gọn, xác định vị trí, sửa, regression test, sanitizer) và áp dụng nó cho bug tiếp theo bạn gặp; sau một tuần, làm lại bài tập 9 mà không nhìn đáp án và giải thích vì sao mỗi bước loại bỏ là an toàn.

## Đáp án bài tập

1. (a) AddressSanitizer (heap-buffer-overflow). (b) AddressSanitizer (`heap-use-after-free`, vì buffer cũ đã được giải phóng). (c) UBSan (`signed integer overflow`). (d) ThreadSanitizer (data race). (e) LeakSanitizer (một phần của ASan trên Linux) hoặc Valgrind. (f) Valgrind hoặc MemorySanitizer ("conditional jump depends on uninitialised value"); cảnh báo compiler `-Wuninitialized` bắt được các ca đơn giản.
2. Loại bug heap-buffer-overflow; một lần đọc kích thước 8 (một `double`); dòng source 10 của `buggy.cpp`; vùng cấp phát là 40 byte, tức năm double; địa chỉ nằm *0 byte bên phải* vùng đó, nên lần đọc vượt đúng một phần tử: một lỗi off-by-one (chỉ số 5 của 5).
3. Tối đa $\lceil\log_2 1000\rceil=10$ lần build; tìm kiếm tuyến tính cần tới 1000 (hoặc 999).
4. Undefined behavior không có nghĩa vụ phải thất bại: lần đọc vượt quá buffer của vector trả về bất cứ thứ gì có trong bộ nhớ đó (phần đệm của allocator, thường là 0), nên code chạy xong. Vòng lặp lỗi cộng $w+1=3$ phần tử và chia cho $w=2$: $(1+2+3)/2=3$, $(2+3+4)/2=4.5$, $(3+4+5)/2=6$, và với cửa sổ cuối $(4+5+v[5])/2$; với giá trị rác 0 nó là $4.5$, vô tình bằng $4.5$ đúng cho cửa sổ đó. Một con số cuối trông đúng che giấu bug, đó là lý do bạn phải kiểm tra mọi output.
5. `use` nhận `unique_ptr` theo giá trị, và `std::move(frame)` chuyển quyền sở hữu vào `f`, thứ bị hủy khi `use` kết thúc; sau đó `frame` là null, và `frame->id` là một phép dereference null. GDB: `bt` (cho thấy `main () at segv.cpp:11`) và `info locals` (cho thấy `frame = ... {get() = 0x0}`). Cách sửa: đọc `frame->id` trước khi move, hoặc để `use` nhận `const Frame&` để quyền sở hữu ở lại trong `main`.
6. Ví dụ: `Test{"moving_average window 2", [](Checker& c){ auto m = moving_average({1,2,3,4,5}, 2); c.check(m.size() == 4, "size"); c.check_near(m[0], 1.5, 1e-12, "m[0]"); ... }}`. Trên code lỗi `m[0]` là 3, nên test fail mà không cần sanitizer. Khẳng định trên giá trị nêu rõ thế nào là đúng và fail một cách xác định; dựa vào crash chỉ fail khi undefined behavior tình cờ crash, và không nói gì về kết quả sai nhưng thầm lặng.
7. Một bảng tốt: `wrap_to_pi(0)=0`; `wrap_to_pi(pi)=-3.14159` (đầu trên bị loại); `wrap_to_pi(-pi)=-3.14159`; `wrap_to_pi(1.5*pi)=-1.5708`; `wrap_to_pi(2*pi)=0` (có dung sai); `wrap_to_pi(7)=0.71681`; `wrap_to_pi(-7)=-0.71681`; `wrap_to_pi(1e6)` bằng phép tính trực tiếp với một oracle độc lập (mất độ chính xác với góc rất lớn là điều được dự kiến); `wrap_to_pi(NAN)` là NaN (không được lặp vô hạn). Dung sai khoảng $10^{-9}$.
8. $n\ge\ln0.05/\ln0.98=148.3$, vậy 149 lần chạy. Nguyên nhân và kỹ thuật: data race (ThreadSanitizer); thời gian/sleep (dùng đồng hồ giả hoặc condition variable thay vì `sleep`); bộ nhớ chưa khởi tạo (Valgrind/MSan, `-ftrivial-auto-var-init=zero` để lộ ra); ngẫu nhiên không seed hoặc seed theo thời gian (ghi và cố định seed); thứ tự của các container không có thứ tự (sắp xếp trước khi so sánh); rò rỉ tài nguyên giữa các test (chạy mỗi test trong một process mới).
9. Kết quả là `[17, 42]` với 22 lần gọi `fails` cho `range(64)` khi bạn bắt đầu ở khối 32 và giảm nửa xuống 1 (số chính xác phụ thuộc chiến lược). Một câu trả lời tốt cho thấy bắt đầu với khối 32 loại bỏ 32 phần tử mỗi lần (chỉ giữ nếu bug còn tồn tại), rồi giảm nửa xuống 1, và rằng kết quả là "1-minimal": loại bỏ bất kỳ phần tử còn lại nào cũng làm bug biến mất.
10. Một câu trả lời tốt: job 1 Debug (`-O1 -g`) với `-fsanitize=address,undefined` chạy mọi test (bắt 1(a), 1(b), 1(c), 1(e)); job 2 Release với cảnh báo là lỗi (`-Wall -Wextra -Werror`) và cùng các test (bắt UB phụ thuộc tối ưu hóa); job 3 ThreadSanitizer chỉ cho các test đồng thời (1(d), race ở bài tập 8), tách riêng vì TSan và ASan instrument bộ nhớ khác nhau và không kết hợp được; tùy chọn một job Valgrind hoặc MSan hằng đêm cho 1(f). Mỗi job nên tải báo cáo sanitizer đầu tiên lên làm artifact.
11. Một câu trả lời tốt có một bảng gồm: ASan (4 dòng đầu: heap-buffer-overflow, READ of size 8, `buggy.cpp:10`, 0 bytes to the right of a 40-byte region), Valgrind (`Invalid read of size 8`, địa chỉ cách 0 byte sau một khối kích thước 40), GDB cho biến thể `segv.cpp` (`bt`, `get() = 0x0`); đầu vào đã rút gọn (một phần tử, cửa sổ 1); một regression test fail trên code cũ; và lần chạy cuối không có output sanitizer.

## Đọc thêm

- [AddressSanitizer (Google Sanitizers wiki)](https://github.com/google/sanitizers/wiki/AddressSanitizer) - nó phát hiện gì, cách đọc báo cáo, và chi phí của nó.
- [GCC: Program Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) - mọi tùy chọn `-fsanitize=`, và cái nào kết hợp được.
- [GDB documentation](https://sourceware.org/gdb/documentation/) - sách hướng dẫn về breakpoint, kiểm tra stack và watchpoint.

**Thực hành thêm:** [chương Pro Git về debug với Git](https://git-scm.com/book/en/v2/Git-Tools-Debugging-with-Git) (bisect và blame), [UndefinedBehaviorSanitizer manual](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) và [AddressSanitizer manual](https://clang.llvm.org/docs/AddressSanitizer.html) (cố ý kích hoạt từng kiểm tra được liệt kê và đọc báo cáo), [Valgrind quick start](https://valgrind.org/docs/manual/quick-start.html), [GDB sample session](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Sample-Session.html), và [GoogleTest primer](https://google.github.io/googletest/primer.html).
