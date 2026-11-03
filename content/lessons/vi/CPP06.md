---
{"title": "C++ hiện đại: template, constexpr và các idiom", "summary": "Viết code generic với các giả định được nêu rõ, đẩy công việc sang thời điểm biên dịch bằng constexpr, và dùng các idiom C++17 để ý định có thể kiểm chứng được.", "objectives": ["Viết function template và class template, giải thích deduction (suy luận kiểu), instantiation (khởi tạo template) và vì sao template nằm trong header.", "Nêu và thực thi các giả định của code generic bằng static_assert và if constexpr.", "Dùng constexpr để tính và kiểm tra giá trị lúc biên dịch, và phân biệt nó với const.", "Áp dụng auto, structured binding, optional và range-for mà không làm mất sự rõ ràng của kiểu."]}
---
## Vì sao điều này quan trọng

Các thư viện robotics buộc phải generic: ma trận Eigen trên `float` hoặc `double`, `std::vector` của mọi kiểu message, bộ lọc chạy cho trạng thái 2D lẫn 3D, các wrapper an toàn về đơn vị mà không tốn chi phí lúc chạy. Template cho phép bạn viết một thuật toán một lần và nhận được một phiên bản chuyên biệt, được inline, cho mỗi kiểu, không có lời gọi ảo. `constexpr` cho phép compiler tính các bảng calibration, phép đổi đơn vị và phép tính kích thước trước khi chương trình chạy, và biến nhiều bug thành lỗi biên dịch. Cái giá của sức mạnh này là thông báo lỗi và các giả định ngầm: một template lặng lẽ giả định "T là kiểu dấu phẩy động" sẽ cho đáp án sai, hoặc một trang lỗi, khi ai đó khởi tạo nó với `int`. Thói quen C++ hiện đại là nêu và kiểm tra từng giả định ở chỗ nó được đặt ra, như Core Guidelines nói: làm cho interface có kiểu chính xác và chặt chẽ.

## Trực giác

Template là một *khuôn tô* (stencil), không phải một hàm: không có gì tồn tại cho đến khi bạn dùng nó với các kiểu cụ thể. Khi bạn gọi `clamp_to(5, 0, 3)`, compiler suy ra `T = int`, đóng dấu ra một hàm thật `clamp_to<int>`, và biên dịch nó. Một lời gọi với `double` đóng dấu ra một hàm khác. Mỗi phiên bản nhanh như code viết tay, nhưng kích thước code tăng theo số kiểu khác nhau.

`constexpr` nghĩa là "có thể được tính lúc biên dịch". Nếu mọi đối số đều là hằng, compiler tính kết quả ngay khi biên dịch và có thể đặt nó vào binary, hoặc dùng nó ở nơi cần hằng (kích thước mảng, `static_assert`, đối số template). Nếu một đối số là giá trị lúc chạy, cùng hàm đó chỉ đơn giản chạy bình thường.

![Khởi tạo template và đánh giá constexpr: một khuôn tạo ra các hàm int và double, và đánh giá lúc biên dịch so với lúc chạy](/lesson-figures/CPP06.svg)

*Một khuôn template cho ra một hàm thật cho mỗi kiểu; code constexpr có thể chạy lúc biên dịch hoặc lúc chạy.*

## Lý thuyết và suy dẫn

### Function template và class template

```cpp
template <class T>
constexpr T clamp_to(T x, T lo, T hi) { return x < lo ? lo : (x > hi ? hi : x); }
```

- **Deduction**: mọi chỗ dùng `T` trong các tham số phải suy ra cùng một kiểu. `clamp_to(5, 0.0, 3.0)` thất bại: `int` so với `double`. Sửa bằng `clamp_to<double>(5, 0.0, 3.0)` tường minh hoặc dùng hai tham số template.
- **Instantiation** xảy ra khi template được dùng với đối số cụ thể; lỗi trong thân hàm được báo lúc đó, không phải khi template được định nghĩa. Do đó có những thông báo dài khét tiếng.
- **Định nghĩa trong header**: compiler phải thấy toàn bộ thân hàm tại mỗi điểm instantiation, nên template được định nghĩa trong header. Định nghĩa template trong `.cpp` và dùng nó từ file khác sẽ cho lỗi *linker* (undefined reference) trừ khi bạn khởi tạo tường minh (explicit instantiation).
- **Class template** hoạt động tương tự: `RunningStats<double>` và `RunningStats<float>` là hai kiểu không liên quan. Từ C++17, đối số constructor có thể suy ra đối số template (CTAD): `std::pair p{1, 2.5};`.
- **Tham số non-type**: `template <std::size_t N>` nhận một giá trị; `std::array<int, N>` là ví dụ chuẩn.

### Nêu các giả định

Một template nên khai báo những gì nó yêu cầu.

1. `static_assert(std::is_floating_point_v<T>, "message")` làm hỏng build với thông báo của *bạn* khi `T` sai.
2. `if constexpr (cond)` loại bỏ nhánh không được chọn lúc biên dịch, nên mỗi kiểu chỉ biên dịch phần code hợp lệ với nó:

```cpp
template <class T> auto describe(T) {
  if constexpr (std::is_integral_v<T>) return 1;
  else if constexpr (std::is_floating_point_v<T>) return 2;
  else return 3;
}
```
3. Trong C++20, **concept** (`template <std::floating_point T>`) biểu diễn ràng buộc ngay trong chữ ký và cho lỗi rõ ràng tại điểm gọi. Trong C++17 các tương đương là `static_assert` và `std::enable_if_t`.

Hãy ghi tài liệu cả các giả định về *ngữ nghĩa* (ví dụ "lo <= hi", "NaN đi qua không đổi"), vì hệ thống kiểu không kiểm tra được chúng.

### constexpr

Biến `constexpr` là hằng và phải được khởi tạo bằng biểu thức hằng. Hàm `constexpr` (C++14/17: cho phép vòng lặp, biến cục bộ và điều kiện, không có `try`, hàm thư viện chuẩn bị giới hạn) được tính lúc biên dịch khi dùng trong ngữ cảnh biểu thức hằng và chạy bình thường trong các trường hợp khác. Điều này khác với `const`: `const int n = read();` là hằng lúc chạy và không thể làm kích thước mảng, còn `constexpr int n = 4;` thì được.

Một mẫu hữu ích: tính một bảng lúc biên dịch và kiểm tra nó bằng `static_assert`:

```cpp
constexpr auto sq = make_squares<6>();   // {0, 1, 4, 9, 16, 25}
static_assert(sq[5] == 25);
```
Hãy cẩn thận với tràn số trong biểu thức hằng: tràn số có dấu là lỗi biên dịch ở đó, và đây là một ưu điểm. Với bình phương `int`, chỉ số đầu tiên bị tràn là 46341, vì $46341^2=2{,}147{,}488{,}281>2^{31}-1$.

### Các idiom hiện đại

- `auto` suy ra theo giá trị và bỏ reference cùng `const` cấp cao nhất; `auto&` và `const auto&` giữ chúng; `decltype(auto)` giữ đúng kiểu của biểu thức. Dùng `auto` khi kiểu hiển nhiên từ vế phải, và viết ra kiểu khi nó làm rõ ý định.
- Structured binding: `auto [t, v] = sample;` đặt tên cho các member của một struct, pair hoặc tuple.
- `std::optional<T>` biểu diễn "có thể có giá trị" mà không cần giá trị canh gác như -1 hay NaN. `std::string_view` là một view không sở hữu của văn bản (một phép mượn theo nghĩa của CPP03).
- Range-for: `for (const auto& s : samples)`; biến vòng lặp là reference để tránh copy.
- Ưu tiên thuật toán và kiểu chuẩn hơn vòng lặp thô và con trỏ, và khởi tạo đồng nhất bằng ngoặc nhọn (cũng cấm narrowing: `int i{2.5}` là lỗi).

### Một generic đúng về số học: Welford

Với trung bình và phương sai dạng streaming, việc duy trì tổng bình phương làm mất độ chính xác. Cập nhật Welford dùng trung bình trước đó, với $\delta=x_n-\bar x_{n-1}$:
$$\bar x_n=\bar x_{n-1}+\frac{\delta}{n},\qquad M_n=M_{n-1}+\delta\,(x_n-\bar x_n),\qquad s^2=\frac{M_n}{n-1}.$$
Công thức ngây thơ $(\sum x^2-n\bar x^2)/(n-1)$ trừ hai số rất lớn và gần bằng nhau (triệt tiêu thảm khốc, catastrophic cancellation).

## Ví dụ có lời giải

Cho các giá trị $2,4,4,4,5,5,7,9$ chảy qua cập nhật Welford, với $\bar x_0=0$, $M_0=0$.

| $n$ | $x$ | $\delta=x-\bar x_{n-1}$ | $\bar x_n$ | $M_n$ |
|---|---|---|---|---|
| 1 | 2 | 2 | 2 | 0 |
| 2 | 4 | 2 | 3 | 2 |
| 3 | 4 | 1 | 3.3333 | 2.6667 |
| 4 | 4 | 0.6667 | 3.5 | 3 |
| 5 | 5 | 1.5 | 3.8 | 4.8 |
| 6 | 5 | 1.2 | 4 | 6 |
| 7 | 7 | 3 | 4.4286 | 13.7143 |
| 8 | 9 | 4.5714 | 5 | 32 |

(Kiểm tra, ví dụ dòng 2: $\delta=4-2=2$, $\bar x=2+2/2=3$, $M=0+2\cdot(4-3)=2$.) Trung bình cuối là $5$ và $M_8=32$, nên phương sai mẫu là $32/7\approx4.5714$ và phương sai tổng thể là $32/8=4$. Các giá trị khớp với định nghĩa trực tiếp: các độ lệch so với 5 là $-3,-1,-1,-1,0,0,2,4$ có bình phương cộng lại $9+1+1+1+0+0+4+16=32$.

Bây giờ là phần interface có ràng buộc: gọi `RunningStats<int>` chạm vào `static_assert(std::is_floating_point_v<T>)` và build dừng với thông báo "RunningStats needs a floating-point type" thay vì lặng lẽ thực hiện phép chia nguyên trong `delta / n`. Gọi `mean(std::vector<std::string>{})` dừng ở `static_assert(std::is_arithmetic_v<V>)`.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: cppreference, Templates - template argument deduction)* Vì sao `template <class T> T add(T a, T b); add(1, 2.5);` không biên dịch được? Nêu hai cách sửa khác nhau và cho biết kiểu kết quả khác nhau như thế nào.
2. **(Dễ)** Dòng nào trong số này biên dịch được? Giải thích mỗi dòng bằng một cụm từ.
   ```cpp
   int n = read_from_sensor();
   constexpr int a = 4 * 2;
   constexpr int b = n * 2;
   const int c = n * 2;
   std::array<int, a> arr1;
   std::array<int, c> arr2;
   ```
3. **(Dễ)** Một bảng lúc biên dịch `make_squares<N>()` lưu bình phương kiểu `int`. Nó chiếm bao nhiêu byte với $N=1000$ (giả sử `int` 4 byte) và chỉ số nhỏ nhất nào làm `i*i` tràn một số nguyên có dấu 32-bit?
4. **(Trung bình)** *(Adapted from: C++ Core Guidelines, T.62 - place template definitions where they are visible)* Một dự án định nghĩa `template <class T> T clamp_to(T, T, T);` trong `util.h` và thân hàm trong `util.cpp`; `main.cpp` gọi `clamp_to(3, 0, 5)` và bước link thất bại. Giải thích lỗi, và nêu hai cách sửa cùng đánh đổi của chúng.
5. **(Trung bình)** Tìm bug số học: đoạn code dưới tính phương sai của các giá trị gần $10^9$ (ví dụ một timestamp nano giây). Phương sai mẫu thật của $\{10^9+4, 10^9+7, 10^9+13, 10^9+16\}$ là 30. Dự đoán dấu của kết quả, giải thích, và thay bằng cập nhật Welford.
   ```cpp
   double s = 0, q = 0;
   for (double x : xs) { s += x; q += x * x; }
   double mean = s / xs.size();
   double var = (q - xs.size() * mean * mean) / (xs.size() - 1);
   ```
6. **(Trung bình)** Dự đoán output và giải thích vì sao lời gọi cuối biên dịch được dù nhánh `std::sqrt` không thể:
   ```cpp
   template <class T> std::string kind(T x) {
     if constexpr (std::is_integral_v<T>) return "int";
     else if constexpr (std::is_floating_point_v<T>) return std::to_string(std::sqrt(x)).substr(0, 3);
     else return "other";
   }
   std::cout << kind(3) << ' ' << kind(2.25) << ' ' << kind("x");
   ```
7. **(Trung bình)** *(Adapted from: C++ Core Guidelines, T.10 and T.150)* Viết `static_assert` làm cho `mean(const Container&)` thất bại với thông báo một dòng đối với container của `std::string`, và giải thích một mệnh đề `requires` của C++20 cải thiện gì cho *phía gọi*.
8. **(Trung bình)** Không chạy code, nêu các kiểu: `int i = 5; const int& r = i; auto a = r; auto& b = r; decltype(auto) c = r; auto d = std::move(i);`. Sau đó viết các `static_assert` chứng minh đáp án của bạn và biên dịch chúng.
9. **(Khó)** Một generic `template <class F, class T> T trapezoid(F f, T a, T b, int n)` tích phân `f` trên $[a,b]$. Liệt kê các giả định nó cần (về `F`, `T`, `n`, độ trơn) và cách thực thi từng cái. Với $f=\sin$ trên $[0,\pi/2]$, sai số của quy tắc hình thang tối đa là $\frac{(b-a)^3}{12n^2}\max|f''|$; tìm $n$ nhỏ nhất đảm bảo sai số $\le10^{-6}$.
10. **(Khó)** *(Adapted from: cppreference, constexpr specifier)* Giải thích vì sao `constexpr double s = std::sin(1.0);` có thể biên dịch hoặc không tùy compiler trong C++17, và viết một bản thay thế `constexpr` dùng chuỗi Taylor 12 số hạng. Bạn nên kiểm tra độ chính xác nào và trên khoảng nào?
11. **(Mini-project)** Xây một bảng tra cứu lúc biên dịch của $\sin$ với độ phân giải 1 độ ($0^\circ$-$90^\circ$) dùng hàm Taylor constexpr của bạn, `static_assert` các đầu mút (0 và gần 1), và đo sai số nội suy tối đa so với `std::sin` trên một lưới mịn. Báo cáo sai số và kích thước bảng tính bằng byte.

## Cài đặt tham khảo

Các tiện ích generic với giả định tường minh: `clamp_to`, `deg2rad`, một `make_squares` lúc biên dịch, `RunningStats` của Welford và một `mean` cho container. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

```cpp
// CPP06 reference: small generic numerical utilities with explicit, checked assumptions.
#include <array>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <optional>
#include <type_traits>
#include <vector>

// clamp x into [lo, hi]. Precondition: lo <= hi. (NaN passes through unchanged.)
template <class T>
constexpr T clamp_to(T x, T lo, T hi) {
  static_assert(std::is_arithmetic_v<T>, "clamp_to needs an arithmetic type");
  return x < lo ? lo : (x > hi ? hi : x);
}

template <class T>
constexpr T deg2rad(T degrees) {
  static_assert(std::is_floating_point_v<T>, "deg2rad needs a floating-point type");
  return degrees * static_cast<T>(3.14159265358979323846L) / static_cast<T>(180);
}

// 0, 1, 4, 9, ... computed at compile time.
template <std::size_t N>
constexpr std::array<int, N> make_squares() {
  std::array<int, N> a{};
  for (std::size_t i = 0; i < N; ++i) a[i] = static_cast<int>(i * i);
  return a;
}

// Welford's online mean/variance: numerically stable, O(1) memory.
template <class T>
class RunningStats {
  static_assert(std::is_floating_point_v<T>, "RunningStats needs a floating-point type");

 public:
  void push(T x) {
    ++n_;
    const T delta = x - mean_;
    mean_ += delta / static_cast<T>(n_);
    m2_ += delta * (x - mean_);
  }
  std::size_t count() const { return n_; }
  std::optional<T> mean() const {
    if (n_ == 0) return std::nullopt;
    return mean_;
  }
  // Sample variance (divides by n-1); needs at least two values.
  std::optional<T> variance() const {
    if (n_ < 2) return std::nullopt;
    return m2_ / static_cast<T>(n_ - 1);
  }

 private:
  std::size_t n_ = 0;
  T mean_ = 0;
  T m2_ = 0;
};

// Mean of any container of arithmetic values, accumulated in double. Empty -> nullopt.
template <class Container>
std::optional<double> mean(const Container& c) {
  using V = typename Container::value_type;
  static_assert(std::is_arithmetic_v<V>, "mean needs a container of arithmetic values");
  if (c.empty()) return std::nullopt;
  double sum = 0.0;
  for (const V& x : c) sum += static_cast<double>(x);
  return sum / static_cast<double>(c.size());
}

// ---- self-test
int main() {
  static_assert(clamp_to(5, 0, 3) == 3);
  static_assert(make_squares<5>()[4] == 16);
  constexpr double h = deg2rad(90.0);
  static_assert(h > 1.5707 && h < 1.5708);
  RunningStats<double> s;
  for (double x : {2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0}) s.push(x);
  if (*s.mean() != 5.0) return 1;
  if (std::abs(*s.variance() - 32.0 / 7.0) > 1e-12) return 2;
  if (*mean(std::vector<int>{1, 2, 4}) < 2.33 || mean(std::vector<int>{})) return 3;
  std::cout << "CPP06 reference self-test passed\n";
}
```

## Thực hành độc lập

### Mục tiêu

Cài đặt năm tiện ích generic nhỏ mà giả định của chúng được kiểm tra bằng `static_assert`, và kiểm thử chúng bằng các phép kiểm tra lúc biên dịch và lúc chạy.

### Chuẩn bị

`g++` (phiên bản 9 trở lên) hoặc `clang++` với C++17. Lưu starter rồi đến các test thành `lab.cpp`; biên dịch bằng `g++ -std=c++17 -Wall -Wextra -g lab.cpp -o lab && ./lab`.

### Nhiệm vụ

1. Cài đặt `clamp_to` và xem bốn `static_assert` đầu tiên trong các test pass lúc biên dịch.
2. Cài đặt `deg2rad` với một `static_assert` trên `T` và kiểm tra rằng `deg2rad(1.0f)` vẫn là `float`.
3. Cài đặt `make_squares<N>()` và xác nhận compiler tính `make_squares<6>()[5]` lúc biên dịch.
4. Cài đặt `RunningStats<T>` với cập nhật Welford; kiểm tra bảng trong ví dụ có lời giải.
5. Cài đặt `mean` generic cho `vector<int>`, `list<float>` và một container rỗng; kiểm tra rằng một container chuỗi cho ra thông báo `static_assert` của bạn (thử riêng, rồi bỏ dòng đó).
6. Cố ý làm hỏng: tính phương sai bằng công thức ngây thơ và in giá trị cho dữ liệu `1e9 + x` của bài tập 5.

### Code khởi đầu

```cpp
#include <array>
#include <cmath>
#include <cstddef>
#include <optional>
#include <stdexcept>
#include <type_traits>
#include <vector>

// Clamp x into [lo, hi] (precondition lo <= hi). Must be usable in constant expressions.
// static_assert that T is arithmetic.
template <class T>
constexpr T clamp_to(T x, T lo, T hi) { throw std::logic_error("NotImplemented"); }

// degrees -> radians for floating-point T only (static_assert it). constexpr.
template <class T>
constexpr T deg2rad(T degrees) { throw std::logic_error("NotImplemented"); }

// Array {0, 1, 4, 9, ..., (N-1)^2}, computed at compile time.
template <std::size_t N>
constexpr std::array<int, N> make_squares() { throw std::logic_error("NotImplemented"); }

// Welford online statistics for floating-point T (static_assert it).
//   push(x): update count, mean, M2 with delta = x - mean; mean += delta/n; M2 += delta*(x - mean)
//   count(), mean() -> nullopt if empty, variance() -> sample variance (n-1), nullopt if n < 2
template <class T>
class RunningStats {
 public:
  void push(T x) { throw std::logic_error("NotImplemented"); }
  std::size_t count() const { throw std::logic_error("NotImplemented"); }
  std::optional<T> mean() const { throw std::logic_error("NotImplemented"); }
  std::optional<T> variance() const { throw std::logic_error("NotImplemented"); }
};

// Mean of any container with an arithmetic value_type (static_assert), accumulated in double.
// Empty container -> std::nullopt.
template <class Container>
std::optional<double> mean(const Container& c) { throw std::logic_error("NotImplemented"); }
```

### Kiểm thử

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#include <iostream>
#include <list>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)

// compile-time checks: these fail to COMPILE until your constexpr code is right
static_assert(clamp_to(5, 0, 3) == 3 && clamp_to(-1, 0, 3) == 0 && clamp_to(2, 0, 3) == 2);
static_assert(clamp_to(0.5, 0.0, 1.0) == 0.5);
static_assert(make_squares<6>()[5] == 25 && make_squares<6>()[0] == 0);
static_assert(deg2rad(180.0) > 3.14159 && deg2rad(180.0) < 3.1416);
static_assert(std::is_same_v<decltype(deg2rad(1.0f)), float>);

int main() {
  // hand-computed Welford data: mean 5, sum of squared deviations 32 -> sample variance 32/7
  RunningStats<double> s;
  CHECK(s.count() == 0 && !s.mean() && !s.variance());
  s.push(2);
  CHECK(s.mean().value() == 2.0 && !s.variance());
  for (double x : {4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0}) s.push(x);
  CHECK(s.count() == 8 && std::fabs(s.mean().value() - 5.0) < 1e-12);
  CHECK(std::fabs(s.variance().value() - 32.0 / 7.0) < 1e-12);
  // numerical stability: large offset, true variance of {4,7,13,16} is 30
  RunningStats<double> big;
  for (double x : {4.0, 7.0, 13.0, 16.0}) big.push(1e9 + x);
  CHECK(std::fabs(big.variance().value() - 30.0) < 1e-6);
  // invariant: shifting every value by c shifts the mean by c and leaves the variance unchanged
  RunningStats<double> a, b;
  for (double x : {0.3, -1.2, 5.5, 2.0, 2.0}) { a.push(x); b.push(x + 100.0); }
  CHECK(std::fabs(b.mean().value() - a.mean().value() - 100.0) < 1e-9);
  CHECK(std::fabs(b.variance().value() - a.variance().value()) < 1e-9);
  // generic mean over different containers and element types
  CHECK(std::fabs(mean(std::vector<int>{1, 2, 4}).value() - 7.0 / 3.0) < 1e-12);
  CHECK(mean(std::list<float>{1.5f, 2.5f}).value() == 2.0);
  CHECK(!mean(std::vector<double>{}));
  // wide integers do not overflow because the sum is a double
  CHECK(mean(std::vector<int>{2000000000, 2000000000}).value() == 2000000000.0);
  std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi

```
all tests passed
```

Với starter chưa cài đặt, chính bước build thất bại tại `static_assert` đầu tiên trong các test, đó là tín hiệu chủ ý: lỗi lúc biên dịch cũng là test.

### Thử thách mở rộng

Thêm `RunningStats::merge(const RunningStats&)` dùng công thức song song (Chan) để các thống kê từng phần từ hai thread có thể được gộp lại, và kiểm tra nó với một lượt duyệt duy nhất. Sau đó viết lại các ràng buộc bằng `concept` của C++20 nếu compiler của bạn hỗ trợ `-std=c++20`.

### Thực hành với thư viện

Dùng `<numeric>`/`<algorithm>` làm tham chiếu và, nếu đã cài, Eigen (`sudo apt install libeigen3-dev`; chỉ có header, bản thân nó là một thư viện template trên kiểu vô hướng). Nếu thiếu Eigen, xóa hai phần Eigen và giữ phần còn lại. Dán đoạn này *sau* các tiện ích đã hoàn thiện của bạn (nó có `main` riêng, nên bỏ `main` của phần test) và biên dịch bằng `g++ -std=c++17 -Wall -Wextra -I/usr/include/eigen3`.

```cpp
#include <algorithm>
#include <cassert>
#include <iostream>
#include <numeric>
#include <random>
#include <Eigen/Dense>   // Eigen 3: apt install libeigen3-dev; compile with -I/usr/include/eigen3

// Eigen is the "generic over the scalar type" library: Matrix<Scalar, Rows, Cols>.
// A generic function over ANY Eigen vector type, with the assumption stated:
template <class Derived>
double eigen_mean(const Eigen::MatrixBase<Derived>& v) {
  static_assert(Derived::ColsAtCompileTime == 1, "eigen_mean needs a column vector");
  return v.template cast<double>().mean();
}

int main() {
  std::mt19937 g(3);
  std::normal_distribution<double> nd(1e9, 5.0);       // large offset: the naive formula fails here
  std::vector<double> xs(10000);
  for (double& x : xs) x = nd(g);

  // 1. Welford against a two-pass reference computed with <numeric>
  RunningStats<double> w;
  for (double x : xs) w.push(x);
  const double m = std::accumulate(xs.begin(), xs.end(), 0.0) / xs.size();
  const double ss = std::accumulate(xs.begin(), xs.end(), 0.0, [m](double a, double x) { return a + (x - m) * (x - m); });
  const double v2 = ss / (xs.size() - 1);
  assert(std::fabs(*w.mean() - m) < 1e-4 && std::fabs(*w.variance() - v2) < 1e-6 * v2);   // relative 1e-6

  // 2. the same numbers through Eigen (a templated library): mean() and a centred dot product
  Eigen::Map<const Eigen::VectorXd> e(xs.data(), xs.size());
  const double evar = (e.array() - e.mean()).matrix().squaredNorm() / (xs.size() - 1);
  assert(std::fabs(e.mean() - *w.mean()) < 1e-4 && std::fabs(evar - *w.variance()) < 1e-6 * evar);
  assert(std::fabs(eigen_mean(Eigen::Vector3f(1, 2, 6)) - 3.0) < 1e-6);   // same template, float scalar
  // eigen_mean(Eigen::RowVector3d(1, 2, 3));   // uncomment: stops at YOUR static_assert message

  // 3. std::clamp (C++17) agrees with clamp_to, including at the ends
  for (int i = -5; i <= 5; ++i) assert(clamp_to(i, -2, 3) == std::clamp(i, -2, 3));
  std::cout << "Welford var " << *w.variance() << " == two-pass " << ss / (xs.size() - 1) << "\nlibrary track ok\n";
}
```

Output mong đợi: phương sai Welford và hai-lượt khớp nhau (khoảng 24.9 với seed này) rồi đến `library track ok`. Bỏ comment dòng `RowVector3d` phải làm build dừng tại thông báo `static_assert` của bạn, cùng thói quen như trong `RunningStats`. Các dung sai là tương đối (`1e-6 * var`) vì với giá trị gần $10^9$ ngay cả trung bình hai-lượt cũng chỉ chính xác khoảng $10^{-7}$.

## Kiểm chứng

- Các test lúc biên dịch bằng `static_assert` chạy ở mọi lần build; chúng không tốn gì lúc chạy.
- So sánh code nhạy cảm về số học với một oracle độc lập (NumPy `np.var(x, ddof=1)`) trên cả dữ liệu lành tính và dữ liệu có offset lớn.
- Khởi tạo mỗi template với từng kiểu được hỗ trợ (`float`, `double`) và một kiểu không được hỗ trợ; kiểu không được hỗ trợ phải cho thông báo của bạn, không phải 40 dòng.
- Kiểm tra tính bất biến theo dịch chuyển: cộng $c$ vào mọi giá trị làm trung bình dịch đi $c$ và không đổi phương sai.
- Biên dịch với `-Wall -Wextra -Wconversion` để bắt narrowing giữa các kiểu template, và chạy dưới `-fsanitize=undefined`.

## Lỗi thường gặp

| Sai lầm | Kết quả |
|---|---|
| Thân template trong file `.cpp` | lỗi linker `undefined reference to clamp_to<int>(...)` |
| Kiểu đối số lẫn lộn `add(1, 2.5)` | lỗi xung đột deduction |
| Phương sai ngây thơ trên dữ liệu có offset | phương sai âm (ở đây $-170.67$ thay vì $30$) |
| `std::accumulate(..., 0)` trên double | tích lũy số nguyên (CPP05) |
| Thiếu `static_assert` trên `T` | chia nguyên trong `delta / n` hoặc lỗi khó hiểu sâu trong template |
| `const` ở nơi cần `constexpr` | "not a constant expression" khi làm kích thước mảng |
| Tràn số có dấu trong constexpr | lỗi biên dịch (tốt) so với wraparound/UB lặng lẽ lúc chạy (xấu) |
| `auto` gây copy (`auto x = vec;` trong vòng lặp) | copy ẩn; dùng `const auto&` |
| Code quá generic | lỗi khó đọc và phình code; thêm ràng buộc, giữ số lần instantiation nhỏ |

## Phương án khác và đánh đổi

- **Template so với hàm ảo (CPP04).** Template cho static dispatch và inline nhưng cố định kiểu lúc biên dịch và làm code phình ra; hàm ảo cho phép hoán đổi lúc chạy với cái giá là một lời gọi gián tiếp.
- **Template so với overload.** Với hai hoặc ba kiểu, overload thường (`float`, `double`) rõ ràng hơn một template có ràng buộc.
- **`constexpr` so với bộ sinh code hay bảng lúc chạy.** `constexpr` giữ nguồn chân lý trong code C++; một bảng sinh bằng Python dễ hơn cho dữ liệu khổng lồ hoặc phức tạp. Công việc lúc biên dịch làm tăng thời gian build, nên tránh nó cho các vòng lặp lớn.
- **`static_assert` / `enable_if` / concept.** `static_assert` cho thông báo tốt nhất trong C++17 nhưng thất bại *bên trong* hàm; SFINAE (`enable_if`) cho phép overload resolution chọn hàm khác nhưng khó đọc; concept (C++20) làm tốt cả hai.
- **`optional` so với NaN so với exception** cho "không có kết quả": `optional` tường minh và rẻ; NaN có thể lọt qua phép tính mà không ai nhận ra; exception chỉ hợp với thất bại hiếm gặp.

## Vận dụng và ghi nhớ

Eigen, `std::chrono` (đơn vị là kiểu) và `rclcpp::Publisher<MessageT>` của ROS 2 đều là template; đọc lỗi của chúng trở nên dễ hơn nhiều khi bạn nhận ra được instantiation và giả định không được thỏa. `typing.Generic` của Python và việc dispatch theo dtype của NumPy đóng cùng vai trò ở một thời điểm khác (lúc chạy). Ôn tập giãn cách: sau vài ngày, viết từ trí nhớ một hàm template có `static_assert`, một `if constexpr` và một helper `constexpr`, rồi giải thích phần nào chạy lúc biên dịch. Cũng hãy tự suy lại cập nhật Welford từ định nghĩa của trung bình.

## Đáp án bài tập

1. `T` được suy ra là `int` từ đối số đầu và `double` từ đối số thứ hai, xung đột. Cách A: `add<double>(1, 2.5)` chuyển int một cách tường minh và trả về `double` (3.5). Cách B: `template <class T, class U> auto add(T a, U b) { return a + b; }` trả về kiểu chung, ở đây là `double`. Cách C: gọi `add(1.0, 2.5)`.
2. `a` biên dịch được (biểu thức hằng). `b` thất bại (`n` là giá trị lúc chạy). `c` biên dịch được như một `const` lúc chạy. `arr1` biên dịch được (`a` là hằng lúc biên dịch); `arr2` thất bại vì `c` không dùng được làm đối số template.
3. $1000\cdot4=4000$ byte. $46340^2=2{,}147{,}395{,}600$ vừa, $46341^2=2{,}147{,}488{,}281>2{,}147{,}483{,}647$ tràn; chỉ số đầu tiên bị tràn là 46341.
4. Compiler biên dịch `main.cpp` mà không thấy thân hàm, nên nó phát ra một lời gọi tới `clamp_to<int>`, nhưng `util.cpp` không bao giờ khởi tạo chuyên biệt đó: undefined reference. Cách 1: chuyển thân hàm vào header (đơn giản; mỗi translation unit đều instantiation, thời gian biên dịch dài hơn). Cách 2: explicit instantiation trong `util.cpp` (`template int clamp_to<int>(int, int, int);`), giới hạn các kiểu được phép nhưng giữ thời gian biên dịch thấp.
5. Kết quả là số âm (khoảng $-170.7$ trong phép kiểm tra của bài): $q\approx4\times10^{18}$ và $n\bar x^2$ bằng nhau đến khoảng 18 chữ số, nhưng double chỉ có khoảng 16, nên hiệu bị sai số làm tròn chi phối. Phương sai không thể âm. Cập nhật Welford trừ các đại lượng nhỏ (các độ lệch) ở mỗi bước, nên tránh được triệt tiêu; nó trả về 30.
6. Output: `int 1.5 other`. Ở các nhánh bị loại bỏ, `std::sqrt(x)` không bao giờ được khởi tạo cho `int` hay `const char*`, nhờ `if constexpr`; với `if` thường, lời gọi phải biên dịch được cho mọi `T`, và `std::sqrt(const char*)` thất bại. (`sqrt(2.25)=1.5`, `to_string` cho "1.500000", substr(0,3) là `1.5`.)
7. `static_assert(std::is_arithmetic_v<typename Container::value_type>, "mean needs a container of arithmetic values");` đặt ở đầu hàm: lỗi là một dòng với thông báo của bạn. Với `requires std::is_arithmetic_v<std::ranges::range_value_t<C>>` của C++20 trong chữ ký, lỗi được báo tại điểm gọi dưới dạng ràng buộc không thỏa, overload resolution có thể loại ứng viên đó và chọn overload khác, và ràng buộc hiện trong tài liệu.
8. `a` là `int` (auto bỏ reference và const), `b` là `const int&`, `c` là `const int&` (decltype(auto) giữ kiểu đã khai báo của biểu thức `r`), `d` là `int` (`std::move(i)` cho một rvalue, auto copy giá trị). Chứng minh: `static_assert(std::is_same_v<decltype(a), int>);` và tương tự.
9. Giả định: `F` gọi được với `T` và trả về thứ chuyển đổi được sang `T` (một `static_assert(std::is_invocable_r_v<T, F, T>)`); `T` là dấu phẩy động (`static_assert`); `n >= 1` (kiểm tra lúc chạy và throw/trả lỗi); $a\le b$ hữu hạn; $f$ có đạo hàm bậc hai bị chặn trên khoảng. Với cận, $\max|f''|=\max|\sin|=1$, nên $\frac{(\pi/2)^3}{12n^2}\le10^{-6}\Rightarrow n\ge\sqrt{3.8758/(12\cdot10^{-6})}=568.3$, vậy $n=569$ (sai số thực với $n=569$ khoảng $6.4\times10^{-7}$).
10. Trong C++17, `std::sin` không bắt buộc là `constexpr`; GCC tính gộp nó như một phần mở rộng của compiler trong khi các compiler khác từ chối. Một bản thay thế portable: `constexpr double taylor_sin(double x) { double term = x, sum = x; for (int k = 1; k < 12; ++k) { term *= -x * x / ((2 * k) * (2 * k + 1)); sum += term; } return sum; }`. Kiểm tra so với `std::sin` trên $[0,\pi/2]$ (và khoảng đã được gói lại mà bạn sẽ dùng): sai số tối đa ở đó khoảng $3\times10^{-16}$. Độ chính xác giảm với $|x|$ lớn, nên hãy rút gọn đối số trước.
11. Một câu trả lời tốt gồm: một `constexpr std::array<double, 91>` được dựng bởi hàm `constexpr`; `static_assert(table[0] == 0.0)` và một kiểm tra cận cho `table[90]` (nằm giữa 0.999999 và 1.000001); một vòng lặp theo bước 0.01 độ tính nội suy tuyến tính giữa các lân cận và sai số tuyệt đối tối đa so với `std::sin` (khoảng $\frac{h^2}{8}\max|f''|=\frac{(0.01745)^2}{8}\approx3.8\times10^{-5}$); kích thước bảng là $91\cdot8=728$ byte; và một nhận định về chi phí lúc biên dịch.

## Đọc thêm

- [cppreference: Templates](https://en.cppreference.com/w/cpp/language/templates) - các quy tắc về deduction, specialization và instantiation một cách chi tiết.
- [cppreference: constexpr specifier](https://en.cppreference.com/w/cpp/language/constexpr) - điều gì được phép trong biểu thức hằng ở mỗi tiêu chuẩn.
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - phần T về template và lập trình generic, và các quy tắc về hằng (Con) và `constexpr` (F.4).

**Thực hành thêm:** các quiz ở [LearnCpp: function templates](https://www.learncpp.com/cpp-tutorial/function-templates/), [templates in multiple files](https://www.learncpp.com/cpp-tutorial/using-function-templates-in-multiple-files/), [class templates](https://www.learncpp.com/cpp-tutorial/class-templates/), [constexpr functions](https://www.learncpp.com/cpp-tutorial/constexpr-functions/) và [constexpr if](https://www.learncpp.com/cpp-tutorial/constexpr-if-statements/) (đáp án hiện trên mỗi trang), phần [templates and generic programming](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#t-templates-and-generic-programming) của Core Guidelines, và trang Eigen về [viết hàm nhận kiểu Eigen](https://eigen.tuxfamily.org/dox/TopicFunctionTakingEigenTypes.html) (một bài toán ràng buộc template thực tế).
