---
{"title": "C++ hiện đại: template, constexpr và các idiom", "summary": "Viết code generic với các giả định được nêu rõ, đẩy công việc sang thời điểm biên dịch bằng constexpr, và dùng các idiom C++17 để ý định có thể kiểm chứng được.", "objectives": ["Viết function template và class template, giải thích deduction (suy luận kiểu), instantiation (khởi tạo template) và vì sao template nằm trong header.", "Nêu và thực thi các giả định của code generic bằng static_assert và if constexpr.", "Dùng constexpr để tính và kiểm tra giá trị lúc biên dịch, và phân biệt nó với const.", "Áp dụng auto, structured binding, optional và range-for mà không làm mất sự rõ ràng của kiểu."]}
---
## Vì sao điều này quan trọng

Các thư viện robotics buộc phải generic: ma trận Eigen trên `float` hoặc `double`, `std::vector` của mọi kiểu message, bộ lọc chạy cho trạng thái 2D lẫn 3D, các wrapper an toàn về đơn vị mà không tốn chi phí lúc chạy. Template cho phép bạn viết một thuật toán một lần và nhận được một phiên bản chuyên biệt, được inline, cho mỗi kiểu, không có lời gọi ảo. `constexpr` cho phép compiler tính các bảng calibration, phép đổi đơn vị và phép tính kích thước trước khi chương trình chạy, và biến nhiều bug thành lỗi biên dịch. Cái giá của sức mạnh này là thông báo lỗi và các giả định ngầm: một template lặng lẽ giả định "T là kiểu dấu phẩy động" sẽ cho đáp án sai, hoặc một trang lỗi, khi ai đó khởi tạo nó với `int`. Thói quen C++ hiện đại là nêu và kiểm tra từng giả định ở chỗ nó được đặt ra, như Core Guidelines nói: làm cho interface có kiểu chính xác và chặt chẽ.

## Trực giác

Template là một *khuôn tô* (stencil), không phải một hàm: không có gì tồn tại cho đến khi bạn dùng nó với các kiểu cụ thể. Khi bạn gọi `clamp_to(5, 0, 3)`, compiler suy ra `T = int`, đóng dấu ra một hàm thật `clamp_to<int>`, và biên dịch nó. Một lời gọi với `double` đóng dấu ra một hàm khác. Mỗi phiên bản nhanh như code viết tay, nhưng kích thước code tăng theo số kiểu khác nhau.

`constexpr` nghĩa là "có thể được tính lúc biên dịch". Nếu mọi đối số đều là hằng, compiler tính kết quả ngay khi biên dịch và có thể đặt nó vào binary, hoặc dùng nó ở nơi cần hằng (kích thước mảng, `static_assert`, đối số template). Nếu một đối số là giá trị lúc chạy, cùng hàm đó chỉ đơn giản chạy bình thường.

Hãy hình dung template như một con dấu cao su có chỗ trống cho kiểu. Bản thân con dấu không in ra gì; mỗi lần bạn đóng nó với một kiểu mới, bạn nhận được một trang mới, độc lập. Điều này giải thích ba điều người mới thấy bất ngờ: toàn bộ thân hàm phải nhìn thấy được lúc đóng dấu (nên template nằm trong header), lỗi bên trong thân chỉ xuất hiện khi một trang được in (nên thông báo lỗi dài và trỏ vào nơi instantiation chứ không phải nơi định nghĩa), và hai trang in từ cùng một con dấu là hai kiểu không liên quan (`RunningStats<float>` không phải lớp cha hay lớp anh em của `RunningStats<double>`). Compiler không "chạy" template; nó viết code thông thường cho bạn rồi biên dịch code đó.

Ví dụ robot đời thường: một bộ lọc kẹp góc khớp theo radian, dòng động cơ theo ampere và số pixel phải hành xử giống nhau, nhưng bạn không muốn số pixel vô tình bị kẹp bởi các cận dấu phẩy động. Hệ thống kiểu là nơi rẻ nhất để nói "ba đại lượng này dùng chung thuật toán nhưng không chung đơn vị hay giả định", và `static_assert` cùng `constexpr` là cách bảo compiler kiểm tra điều đó trước khi robot di chuyển.

**Hãy dự đoán trước khi tính.** Không chạy gì cả, hãy quyết định `clamp_to(3, 0.5, 2.5)` nên trả về gì nếu đọc nó như toán học, rồi nó trả về gì trong phiên bản mà các cận bị ép về kiểu của đối số đầu. Đoạn sau hình sẽ cho đáp án.

**Trực giác sai thường gặp** là một phép chuyển kiểu "rõ ràng vừa khít" thì vô hại, và một tổng dấu phẩy động cứ là một tổng. Cả hai đều không đúng. Chuyển kiểu làm đổi giá trị khi kiểu đích không biểu diễn được nó, và phép cộng dấu phẩy động không có tính kết hợp, nên một fold hay một phương sai streaming trông vô tội có thể mất toàn bộ chữ số có nghĩa khi các giá trị lớn triệt tiêu nhau. Cách chữa trong cả hai trường hợp là cùng một thói quen: viết giả định (kiểu, miền giá trị, thứ tự phép tính) ở nơi compiler hoặc một test có thể kiểm tra, thay vì giữ trong đầu.

![Trái: template clamp_to như một khuôn tạo ra clamp_to<int> và clamp_to<double> và bị static_assert chặn với std::string; phải: những gì trình biên dịch tính (giá trị constexpr, static_assert) so với những gì chương trình đang chạy tính](/lesson-figures/CPP06.svg)

*Hình: một khuôn template cho ra một hàm thật cho mỗi kiểu, và `static_assert` biến một kiểu không được hỗ trợ thành lỗi build. Bên phải, giá trị `constexpr` và `static_assert` do trình biên dịch tính, còn một giá trị đọc từ cảm biến chỉ có thể do chương trình đang chạy tính; cùng một hàm `constexpr` phục vụ cả hai.*

**Đáp án của dự đoán.** Đọc như toán học thì kết quả là $2.5$. Phiên bản ép các cận về kiểu của đối số đầu âm thầm biến $2.5$ thành $2$ và trả về $2$: nó biên dịch được, chạy được, và sai $0.5$. Phần lý thuyết bên dưới quay lại khoảng cách này (deduction, non-deduced context) và bài tập 14 làm việc với nó.

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

**Ví dụ.** Ba lời gọi của cùng một template `twice` được biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`: `twice(21)`, `twice(1.25)` và `twice<float>(2)`. Mỗi lời gọi in ra chữ ký mà compiler đã đóng dấu (`__PRETTY_FUNCTION__` của GCC). Mỗi lời gọi suy ra hay nhận `T` là gì, và có bao nhiêu hàm được tạo ra?

```cpp
#include <iostream>

template <class T>
T twice(T x) {
  std::cout << __PRETTY_FUNCTION__ << '\n';
  return x + x;
}

int main() {
  twice(21);          // T deduced as int
  twice(1.25);        // T deduced as double
  twice<float>(2);    // T given explicitly; the int argument converts to float
}
```

**Lời giải.** `twice(21)` suy ra `T = int` từ đối số, `twice(1.25)` suy ra `T = double`, và `twice<float>(2)` chỉ định `T` tường minh, nên đối số 2 được chuyển thành `float`. Ba lời gọi tạo ba hàm độc lập, mỗi hàm được biên dịch cho kiểu riêng của nó (cppreference, *Templates*). Chương trình in ra:

```text
T twice(T) [with T = int]
T twice(T) [with T = double]
T twice(T) [with T = float]
```

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

**Ví dụ.** `half` chỉ dành cho kiểu dấu phẩy động và tự bảo vệ bằng `static_assert`. `half(7.0f)` in ra gì, và compiler làm gì khi chương trình được build với `-DTRY_INT`, tức thêm lời gọi `half(7)`? Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <type_traits>

template <class T>
T half(T x) {
  static_assert(std::is_floating_point_v<T>, "half needs a floating-point type");
  return x / 2;
}

int main() {
  std::cout << half(7.0f) << '\n';
#ifdef TRY_INT
  std::cout << half(7) << '\n';
#endif
}
```

**Lời giải.** Khi không có `-DTRY_INT` chỉ `half(7.0f)` được instantiate với `T = float`: assertion đúng và in ra $7.0/2=3.5$ (khối đầu). Với `-DTRY_INT` lời gọi `half(7)` instantiate `T = int`, `std::is_floating_point_v<int>` là false, và build dừng bằng thông báo của chính tác giả thay vì thực hiện một phép chia nguyên cho ra 3 (khối thứ hai, một dòng nêu đúng vấn đề):

```text
3.5
```

```text
half.cpp: In instantiation of ‘T half(T) [with T = int]’:
half.cpp:13:20:   required from here
half.cpp:6:22: error: static assertion failed: half needs a floating-point type
```

### constexpr

Biến `constexpr` là hằng và phải được khởi tạo bằng biểu thức hằng. Hàm `constexpr` (C++14/17: cho phép vòng lặp, biến cục bộ và điều kiện, không có `try`, hàm thư viện chuẩn bị giới hạn) được tính lúc biên dịch khi dùng trong ngữ cảnh biểu thức hằng và chạy bình thường trong các trường hợp khác. Điều này khác với `const`: `const int n = read();` là hằng lúc chạy và không thể làm kích thước mảng, còn `constexpr int n = 4;` thì được.

Một mẫu hữu ích: tính một bảng lúc biên dịch và kiểm tra nó bằng `static_assert`:

```cpp
constexpr auto sq = make_squares<6>();   // {0, 1, 4, 9, 16, 25}
static_assert(sq[5] == 25);
```
Hãy cẩn thận với tràn số trong biểu thức hằng: tràn số có dấu là lỗi biên dịch ở đó, và đây là một ưu điểm. Với bình phương `int`, chỉ số đầu tiên bị tràn là 46341, vì $46341^2=2{,}147{,}488{,}281>2^{31}-1$.

**Ví dụ.** Một ADC 12 bit với điện áp tham chiếu 3.3 V đổi số đếm sang milivolt bằng $\text{mv}=\lfloor 3300\,c/4095\rfloor$. Chương trình kiểm tra $c=0$ và $c=4095$ bằng `static_assert`, dựng một bảng ba phần tử cho $c=1024,2048,3072$ và còn gọi `mv(argc + 1000)`. Compiler tự tính những phần nào, và chương trình in ra gì? Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <array>
#include <iostream>

constexpr int mv(int counts) { return counts * 3300 / 4095; }   // 12-bit ADC, 3.3 V reference
static_assert(mv(0) == 0 && mv(4095) == 3300);
constexpr std::array<int, 3> table{mv(1024), mv(2048), mv(3072)};   // built by the compiler

int main(int argc, char**) {
  const int runtime = mv(argc + 1000);   // argc is a run-time value: same function, run-time evaluation
  std::cout << table[0] << ' ' << table[1] << ' ' << table[2] << ' ' << runtime << '\n';
}
```

**Lời giải.** Hai `static_assert` và bảng ba phần tử là ngữ cảnh biểu thức hằng, nên compiler tự tính (bảng nằm sẵn trong binary). Các assertion đúng: $\text{mv}(0)=0$ và $\text{mv}(4095)=3300\cdot4095/4095=3300$. Bảng là $\lfloor 3300\cdot1024/4095\rfloor=825$, $\lfloor 3300\cdot2048/4095\rfloor=1650$ và $\lfloor 3300\cdot3072/4095\rfloor=2475$. `mv(argc + 1000)` có đối số lúc chạy ($\text{argc}=1$ nên $c=1001$), nên cùng hàm đó chỉ đơn giản chạy: $\lfloor 3300\cdot1001/4095\rfloor=806$. Vậy một hàm `constexpr` phục vụ cả lúc biên dịch lẫn lúc chạy. Chương trình in ra:

```text
825 1650 2475 806
```

### Các idiom hiện đại

- `auto` suy ra theo giá trị và bỏ reference cùng `const` cấp cao nhất; `auto&` và `const auto&` giữ chúng; `decltype(auto)` giữ đúng kiểu của biểu thức. Dùng `auto` khi kiểu hiển nhiên từ vế phải, và viết ra kiểu khi nó làm rõ ý định.
- Structured binding: `auto [t, v] = sample;` đặt tên cho các member của một struct, pair hoặc tuple.
- `std::optional<T>` biểu diễn "có thể có giá trị" mà không cần giá trị canh gác như -1 hay NaN. `std::string_view` là một view không sở hữu của văn bản (một phép mượn theo nghĩa của CPP03).
- Range-for: `for (const auto& s : samples)`; biến vòng lặp là reference để tránh copy.
- Ưu tiên thuật toán và kiểu chuẩn hơn vòng lặp thô và con trỏ, và khởi tạo đồng nhất bằng ngoặc nhọn (cũng cấm narrowing: `int i{2.5}` là lỗi).

**Ví dụ.** Một log các mẫu (thời gian tính bằng s, dòng tính bằng A) $\{(0.1,2.0),(0.2,4.5),(0.3,6.0)\}$ được tìm mẫu đầu tiên vượt một giới hạn, một lần với 4 A và một lần với 9 A. `std::optional` thay cho một giá trị canh như $-1$, structured binding đặt tên `t` và `v`, và range-for dùng `const auto&` để không copy mẫu nào. Chương trình in ra gì cho mỗi giới hạn? Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <optional>
#include <vector>

struct Sample {
  double t;   // s
  double v;   // A
};

std::optional<Sample> first_above(const std::vector<Sample>& log, double limit) {
  for (const auto& s : log)
    if (s.v > limit) return s;
  return std::nullopt;
}

int main() {
  const std::vector<Sample> log{{0.1, 2.0}, {0.2, 4.5}, {0.3, 6.0}};
  for (double limit : {4.0, 9.0}) {
    if (auto s = first_above(log, limit)) {
      auto [t, v] = *s;
      std::cout << "limit " << limit << ": t=" << t << " v=" << v << '\n';
    } else {
      std::cout << "limit " << limit << ": none\n";
    }
  }
}
```

**Lời giải.** Với giới hạn 4 A, mẫu đầu tiên có $v>4$ là $(0.2,4.5)$, vì $2.0$ không vượt $4$; `first_above` trả về nó và binding cho `t=0.2 v=4.5`. Với giới hạn 9 A không mẫu nào thỏa ($6.0\le 9$), nên hàm trả về `std::nullopt` và chương trình nói thẳng điều đó, thay vì trả về một giá trị ma thuật. Chương trình in ra:

```text
limit 4: t=0.2 v=4.5
limit 9: none
```

### Một generic đúng về số học: Welford

Với trung bình và phương sai dạng streaming, việc duy trì tổng bình phương làm mất độ chính xác. Cập nhật Welford dùng trung bình trước đó, với $\delta=x_n-\bar x_{n-1}$:
$$\bar x_n=\bar x_{n-1}+\frac{\delta}{n},\qquad M_n=M_{n-1}+\delta\,(x_n-\bar x_n),\qquad s^2=\frac{M_n}{n-1}.$$
Công thức ngây thơ $(\sum x^2-n\bar x^2)/(n-1)$ trừ hai số rất lớn và gần bằng nhau (triệt tiêu thảm khốc, catastrophic cancellation).

**Ví dụ.** Bốn số đo $10^{10}+\{1,4,4,7\}$ có phương sai mẫu thật $18/3=6$ (các độ lệch $-3,0,0,3$ so với trung bình $10^{10}+4$). Cả công thức tổng ngây thơ lẫn cập nhật Welford chạy bằng `double` trên cùng dữ liệu. Mỗi công thức in ra gì? Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <vector>

int main() {
  const std::vector<double> xs{1e10 + 1, 1e10 + 4, 1e10 + 4, 1e10 + 7};
  double s = 0, q = 0, mean = 0, m2 = 0;
  int n = 0;
  for (double x : xs) {
    s += x;
    q += x * x;                          // naive running sums
    ++n;
    const double delta = x - mean;       // Welford update
    mean += delta / n;
    m2 += delta * (x - mean);
  }
  const double naive = (q - n * (s / n) * (s / n)) / (n - 1);
  std::cout << "naive " << naive << ", Welford " << m2 / (n - 1) << '\n';
}
```

**Lời giải.** Công thức ngây thơ tính $(q-n\bar x^2)/(n-1)$ từ $q=\sum x^2\approx4\cdot10^{20}$ và $n\bar x^2$, hai số cỡ đó mà hiệu chỉ là $18$. Các double gần $4\cdot10^{20}$ (giữa $2^{68}$ và $2^{69}$) cách nhau $2^{68-52}=65\,536$, nên hiệu bị mất trong làm tròn và ra $-65\,536/3=-21\,845.3$, một phương sai âm. Cập nhật Welford chỉ làm việc với các độ lệch nhỏ: $\delta=1\cdot10^{10}+1$ cho trung bình $10^{10}+1$ và $M=0$; rồi $\delta=3$, trung bình $10^{10}+2.5$, $M=4.5$; $\delta=1.5$, trung bình $10^{10}+3$, $M=6$; $\delta=4$, trung bình $10^{10}+4$, $M=18$, nên phương sai là $18/3=6$. Chương trình in ra:

```text
naive -21845.3, Welford 6
```

Quy mô của vấn đề có thể đọc từ khoảng cách giữa các số `double`: các tổng $q=\sum x^2$ và $n\bar x^2$ có cỡ $n\cdot\text{offset}^2$, và một `double` ở cỡ đó không phân biệt được các hiệu nhỏ hơn khoảng cách $2^{\lfloor\log_2 q\rfloor-52}$ của nó. Thanh trượt cho thấy khoảng cách chia cho $n-1$ so với phương sai thật: tại nơi tỉ số đạt 1 thì không còn tin được công thức ngây thơ (đây là ước lượng quy mô, không phải cận chặt, vì các tổng tích lũy nhiều lần làm tròn).

```explore
{
  "title": "When does the naive variance break?",
  "title_vi": "Khi nào phương sai ngây thơ bị hỏng?",
  "prompt": "Predict first: for 4 readings with variance 30, at what offset (power of ten) does the rounding error scale of the naive formula become as large as the variance itself? Then move the offset slider and check against the lesson's case at 10^9.",
  "prompt_vi": "Dự đoán trước: với 4 số đo có phương sai 30, ở độ lệch nào (lũy thừa của 10) thì quy mô sai số làm tròn của công thức ngây thơ lớn bằng chính phương sai? Sau đó kéo thanh trượt độ lệch và đối chiếu với trường hợp 10^9 của bài.",
  "params": [
    {
      "name": "off",
      "label": "log10 of the offset",
      "label_vi": "log10 của độ lệch",
      "min": 0,
      "max": 11,
      "step": 0.25,
      "value": 9,
      "unit": ""
    },
    {
      "name": "n",
      "label": "readings n",
      "label_vi": "số đo n",
      "min": 2,
      "max": 1000,
      "step": 1,
      "value": 4,
      "unit": ""
    },
    {
      "name": "v",
      "label": "true variance",
      "label_vi": "phương sai thật",
      "min": 1,
      "max": 1000,
      "step": 1,
      "value": 30,
      "unit": ""
    }
  ],
  "let": [
    {
      "name": "sp",
      "expr": "2^(floor(log10(n*10^(2*off))/log10(2))-52)"
    }
  ],
  "plot": {
    "x": {
      "name": "h",
      "min": 0,
      "max": 11,
      "label": "log10 of the offset",
      "label_vi": "log10 của độ lệch"
    },
    "y": {
      "label": "log10 (error scale / true variance)",
      "label_vi": "log10 (quy mô sai số / phương sai thật)",
      "min": -12,
      "max": 8
    },
    "series": [
      {
        "expr": "log10(2^(floor(log10(n*10^(2*h))/log10(2))-52)/(n-1)/v)",
        "label": "naive error scale / variance",
        "label_vi": "quy mô sai số ngây thơ / phương sai",
        "color": "orange"
      },
      {
        "expr": "0",
        "label": "error = variance",
        "label_vi": "sai số = phương sai",
        "color": "grey"
      }
    ],
    "points": [
      {
        "x": "off",
        "y": "log10(sp/(n-1)/v)",
        "label": "your offset",
        "label_vi": "độ lệch của bạn",
        "color": "orange"
      }
    ]
  },
  "readouts": [
    {
      "label": "spacing of doubles at q = n·offset²",
      "label_vi": "khoảng cách double tại q = n·offset²",
      "expr": "sp",
      "unit": "",
      "digits": 0
    },
    {
      "label": "error scale of the variance (spacing / (n−1))",
      "label_vi": "quy mô sai số của phương sai (khoảng cách / (n−1))",
      "expr": "sp/(n-1)",
      "unit": "",
      "digits": 1
    },
    {
      "label": "error scale / true variance",
      "label_vi": "quy mô sai số / phương sai thật",
      "expr": "sp/(n-1)/v",
      "unit": "",
      "digits": 3
    }
  ]
}
```

### Deduction chuyên sâu: forwarding reference và non-deduced context

Xét `template <class T> void f(P)` được gọi như `f(e)` với đối số kiểu $A$. Các quy tắc deduction (cppreference, *Template argument deduction*, "Deduction from a function call") được áp dụng theo thứ tự: nếu `P` là kiểu reference thì dùng kiểu được tham chiếu; cv-qualifier cấp cao nhất của `P` bị bỏ qua; nếu `P` *không* phải reference thì `A` trước hết bị decay (mảng thành con trỏ, hàm thành con trỏ hàm, bỏ `const` cấp cao nhất). Sau đó compiler tìm `T` làm cho `P` trùng với `A`.

Có một quy tắc phá vỡ khuôn mẫu đó. Nếu `P` là `T&&` với `T` là tham số template trần, không có cv-qualifier (một **forwarding reference**) và đối số là lvalue kiểu $A$, thì $A\&$ được dùng để deduction, tức `T = A&`. Kiểu tham số `T&&` trở thành `A& &&`, và quy tắc reference collapsing rút gọn nó thành `A&` (chỉ `&& &&` mới thành `&&`). Do đó:

| lời gọi | `T` suy ra | kiểu tham số |
|---|---|---|
| `f(i)` với `int i` | `int&` | `int&` |
| `f(ci)` với `const int ci` | `const int&` | `const int&` |
| `f(0)` | `int` | `int&&` |

`std::forward<T>(x)` là `static_cast<T&&>(x)`: với `T = int&` nó cho lvalue, với `T = int` nó cho rvalue, nên value category của người gọi được khôi phục. Trường hợp đặc biệt này cần đúng dạng `T&&`: với `template <class T> void g(const T&&)` lời gọi `g(i)` là lỗi (rvalue reference không bind được lvalue), và bên trong một class template thì `T&&` của chính tham số lớp không bao giờ là forwarding reference.

**Non-deduced context.** Một tham số viết dạng `typename identity<T>::type` (mọi thứ bên trái `::`) hoặc danh sách braced `{1,2,3}` không tham gia deduction; `T` phải đến từ nơi khác hoặc được cho tường minh. Ví dụ của chính cppreference: `bad(x, 1.2)` với `std::vector<std::complex<double>> x` thất bại vì `T` được suy ra là `complex<double>` từ `x` và là `double` từ `1.2`, còn phiên bản dùng `typename identity<T>::type value` chỉ suy ra từ `x` và chuyển kiểu `1.2`. Đây là cách chuẩn để sửa bài tập 1, nhưng có giá phải trả: việc chuyển kiểu diễn ra âm thầm, nên `T` kiểu `int` có thể cắt cụt một cận `double` (xem bài tập 14).

![Ba lời gọi f(T&&): T được suy ra, kiểu tham số sau reference collapsing và value category được std::forward khôi phục, với bốn quy tắc collapsing bên dưới](/lesson-figures/CPP06-2.svg)

*Hình: bảng của mục này dưới dạng hình. Một lvalue làm `T` thành lvalue reference và collapsing giữ tham số là lvalue reference; một rvalue làm `T` thành kiểu thường và tham số `T&&` là rvalue reference. `std::forward<T>(x)` sau đó chuyển tiếp cùng category.*

**Ví dụ.** `sink` báo cáo value category mà người gọi đã truyền, dùng `std::is_lvalue_reference_v<T>` và kích thước chuỗi. Nó được gọi với một `std::string` có tên ("arm"), với giá trị tạm `std::string("hand")` và với `std::move(name)`. Mỗi lời gọi in ra gì, và `T` được suy ra thế nào? Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <string>
#include <type_traits>
#include <utility>

template <class T>
void sink(T&& x) {
  std::cout << (std::is_lvalue_reference_v<T> ? "lvalue" : "rvalue") << ' ' << x.size() << '\n';
}

int main() {
  std::string name = "arm";
  sink(name);                 // lvalue: T = std::string&
  sink(std::string("hand"));  // rvalue: T = std::string
  sink(std::move(name));      // std::move yields an rvalue again
}
```

**Lời giải.** Chuỗi có tên là lvalue, nên `T` được suy ra là `std::string&` và lời gọi in `lvalue 3`. Giá trị tạm là rvalue, nên `T` là `std::string` và lời gọi in `rvalue 4`. `std::move(name)` ép lvalue về lại rvalue, nên `T` lại là `std::string` và lời gọi in `rvalue 3` (`sink` chỉ đọc kích thước nên `name` vẫn giữ "arm"). Các kích thước in ra (3, 4, 3) cho thấy mỗi lời gọi nhận chuỗi riêng của nó. Chương trình in ra:

```text
lvalue 3
rvalue 4
rvalue 3
```

### Fold expression: trường hợp tổng quát đằng sau một phép cộng

Fold khai triển một parameter pack bằng một toán tử hai ngôi. Với các phần tử pack $E_1,\dots,E_N$ (cppreference, *Fold expressions*): right fold một ngôi `(E op ...)` là $E_1\,\mathrm{op}\,(\cdots\mathrm{op}\,(E_{N-1}\,\mathrm{op}\,E_N))$, left fold một ngôi `(... op E)` là $(((E_1\,\mathrm{op}\,E_2)\,\mathrm{op}\cdots)\,\mathrm{op}\,E_N)$, và các dạng hai ngôi thêm một giá trị khởi đầu $I$ ở đầu phải hoặc trái. Với pack rỗng, fold một ngôi chỉ hợp lệ cho `&&` (giá trị `true`), `||` (giá trị `false`) và `,` (giá trị `void()`); với `+` nó ill-formed, nên `(0.0 + ... + args)` là dạng an toàn của một phép tổng.

Chiều của fold quan trọng với dấu phẩy động vì `+` trên `double` không có tính kết hợp. Trong khoảng $2^{53}$ đến $2^{54}$ các số `double` cách nhau 2, nên $10^{16}+1$ rơi đúng điểm giữa và làm tròn về số chẵn, cho $10^{16}$. Khi đó với pack $(1,\,10^{16},\,-10^{16})$, left fold cho $((1+10^{16})-10^{16})=0$ còn right fold cho $1+(10^{16}-10^{16})=1$; với $(10^{16},-10^{16},1)$ hai kết quả đổi chỗ. Không có chiều fold cố định nào an toàn về số học; nếu cần chính xác hãy dùng cộng bù (Kahan) hoặc ghi rõ thứ tự.

![Fold trái và fold phải của pack (1, 1e16, -1e16) từng bước cho 0 và 1, và một trục số các double gần 1e16 cách nhau 2 với 1e16 + 1 được đánh dấu là điểm hòa](/lesson-figures/CPP06-3.svg)

*Hình: thứ tự tính của hai fold trên pack $(1,10^{16},-10^{16})$. Trong fold trái số 1 được cộng vào $10^{16}$ trước và bị mất theo quy tắc làm tròn về số chẵn khi hòa; trong fold phải các số lớn triệt tiêu trước và số 1 còn lại (khoảng cách giữa các double theo cppreference, Fold expressions, và quy tắc làm tròn về số chẵn của IEEE 754 dùng trong bài).*

**Ví dụ.** Phép trừ không có tính kết hợp, nên chiều của fold hiện rõ ngay cả với số nguyên. Với pack $(10,3,2)$ hãy tính fold trái `(... - args)` và fold phải `(args - ...)`, cùng fold hai ngôi `(0.0 + ... + args)` của một pack rỗng. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>

template <class... Ts> auto lsub(Ts... args) { return (... - args); }       // ((a - b) - c)
template <class... Ts> auto rsub(Ts... args) { return (args - ...); }       // (a - (b - c))
template <class... Ts> double total(Ts... args) { return (0.0 + ... + args); }

int main() {
  std::cout << lsub(10, 3, 2) << ' ' << rsub(10, 3, 2) << ' ' << total() << '\n';
}
```

**Lời giải.** Fold trái nhóm từ bên trái: $(10-3)-2=7-2=5$. Fold phải nhóm từ bên phải: $10-(3-2)=10-1=9$. Fold hai ngôi của một pack rỗng chỉ còn giá trị ban đầu `0.0`, in ra là `0`; fold một ngôi của pack rỗng sẽ là ill-formed với `+` (cppreference, *Fold expressions*), nên dạng hai ngôi là dạng an toàn. Chương trình in ra:

```text
5 9 0
```

### constexpr: khi một phép tính không phải biểu thức hằng

Một lời gọi chỉ được tính lúc biên dịch nếu mọi bước đều là *core constant expression*. Chia cho 0, đọc ngoài mảng, tràn số có dấu hoặc thực thi `throw` đều không phải, nên compiler từ chối bằng chẩn đoán trong `static_assert` hoặc trong initializer `constexpr`, trong khi lúc chạy cùng đoạn code đó là hành vi không xác định (hoặc ném exception). Ví dụ với GCC 11: `static_assert` gọi một hàm `constexpr` chia cho 0 báo `'(10 / 0)' is not a constant expression`. Hệ quả hữu ích là việc tính `constexpr` hoạt động như một bộ kiểm tra hành vi không xác định miễn phí cho các đầu vào bạn thử. Một hàm `constexpr` không phải template, không phải defaulted mà *không có* giá trị đối số nào cho ra biểu thức hằng là ill-formed, no diagnostic required (cppreference, *constexpr specifier*), nên đừng viết hàm như vậy rồi trông chờ compiler phát hiện.

**Ví dụ.** Một hàm giai thừa `constexpr` `fact(n)` dùng `int` 32 bit. `static_assert(fact(12) == 479001600)` có biên dịch được không, và `static_assert(fact(13) > 0)` xảy ra chuyện gì khi biên dịch chương trình với `-DTRY_13`? ($12!=479\,001\,600$ và $13!=6\,227\,020\,800$, giá trị lớn nhất của `int` là $2^{31}-1=2\,147\,483\,647$.)

```cpp
constexpr int fact(int n) { return n <= 1 ? 1 : n * fact(n - 1); }

static_assert(fact(12) == 479001600);   // 12! fits in a 32-bit int
#ifdef TRY_13
static_assert(fact(13) > 0);            // 13! = 6227020800 does not
#endif

int main() {}
```

**Lời giải.** $12!=479\,001\,600<2\,147\,483\,647$, nên `static_assert` đầu biên dịch được. $13!=6\,227\,020\,800>2\,147\,483\,647$ làm tràn `int` 32 bit; tràn số có dấu không phải biểu thức hằng, nên với `-DTRY_13` compiler dừng ở `static_assert` thứ hai, trong khi cùng lời gọi đó lúc chạy sẽ âm thầm là undefined behaviour. Phản hồi của compiler với `g++ -std=c++20 -DTRY_13 -c fact.cpp` (g++ 11.4.0) là:

```text
fact.cpp:5:24: error: non-constant condition for static assertion
fact.cpp:5:19:   in ‘constexpr’ expansion of ‘fact(13)’
fact.cpp:5:24: error: overflow in constant expression [-fpermissive]
```

### Overload resolution và SFINAE: loại ứng viên thay vì báo lỗi

Khi bạn gọi một function template, compiler không dừng ở template đầu tiên không khớp. Với mỗi template ứng viên, nó thay các đối số được cho tường minh và được suy ra vào chữ ký (kiểu trả về, kiểu tham số, khai báo tham số template); nếu phép thay này tạo ra kiểu hay biểu thức không hợp lệ, ứng viên đó bị loại khỏi tập overload một cách im lặng thay vì bị báo lỗi. Đó là *Substitution Failure Is Not An Error* (cppreference, *SFINAE*). Hai điều kiện giới hạn quy tắc này. Thứ nhất, chỉ các lỗi trong **immediate context** của chữ ký mới là lỗi "mềm": nếu phép thay buộc phải instantiate một template khác (ví dụ một class template có thân chứa lỗi), lỗi đó là hard error. Thứ hai, khi đã biết các ứng viên còn sống, overload resolution thông thường chọn một cái; nếu không còn cái nào thì lời gọi là lỗi.

Một ví dụ nhỏ, được biên dịch bằng g++ 11.4: `template <class C> auto size_of(const C& c) -> decltype(c.size())` và `template <class T, std::size_t N> std::size_t size_of(const T (&)[N])`. Với `std::vector<int>` 3 phần tử, ứng viên thứ hai thất bại ở deduction và ứng viên đầu thắng (`3`); với `int a[5]` ứng viên đầu không có `a.size()` (một biểu thức không hợp lệ trong immediate context) và bị loại, còn ứng viên thứ hai trả về `5`. Viết ràng buộc trong kiểu trả về, trong `std::enable_if_t<...>` hay trong tham số template có giá trị mặc định đều khai thác cùng một cơ chế.

So sánh hai công cụ. SFINAE chọn *giữa các overload*: ứng viên thất bại biến mất và một hàm khác với chữ ký khác được gọi. `if constexpr` chọn *bên trong một thân hàm*: chữ ký giống nhau cho mọi kiểu và chỉ code trong nhánh được chọn mới được instantiate. Ưu tiên `if constexpr` khi các kiểu chỉ khác nhau ở chi tiết cài đặt và `static_assert` khi bạn muốn từ chối một kiểu kèm thông báo; dùng SFINAE (hoặc mệnh đề `requires` của C++20) khi cần các overload khác nhau cho các họ kiểu khác nhau và người gọi nên thấy các ứng viên không ràng buộc biến mất. Cái giá của SFINAE là chất lượng chẩn đoán: khi mọi overload bị loại, thông báo liệt kê tất cả ứng viên và lý do từng cái thất bại, đó là "lỗi 40 dòng" trong review prompt. Một ràng buộc viết bằng concept hay `static_assert` có thông báo biến cùng thông tin đó thành một dòng.

![Bốn lời gọi to_text so với hai overload: với mỗi lời gọi, mỗi ứng viên hoặc khả dụng hoặc bị loại, và kết quả là một giá trị hoặc lỗi biên dịch khi không còn ứng viên](/lesson-figures/CPP06-5.svg)

*Hình: overload resolution với SFINAE cho hai overload của ví dụ bên dưới. Một ứng viên có kiểu trả về là biểu thức không hợp lệ thì bị loại, nên mỗi lời gọi trong ba lời gọi đầu có đúng một ứng viên còn sống; lời gọi thứ tư mất cả hai ứng viên và là lỗi tại nơi gọi.*

**Ví dụ.** `to_text` có hai overload với kiểu trả về là `decltype(std::to_string(x))` và `decltype(x.name())`. Ứng viên nào khả dụng cho `to_text(42)`, `to_text(2.5)` và `to_text(Joint{"elbow"})`, chương trình in ra gì, và compiler báo gì nếu `main` còn in `to_text("x")`? Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <string>

struct Joint { std::string label; std::string name() const { return label; } };

template <class T> auto to_text(const T& x) -> decltype(std::to_string(x)) { return std::to_string(x); }
template <class T> auto to_text(const T& x) -> decltype(x.name()) { return x.name(); }

int main() {
  std::cout << to_text(42) << ' ' << to_text(2.5) << ' ' << to_text(Joint{"elbow"}) << '\n';
}
```

**Lời giải.** Với `42` và `2.5` ứng viên thứ hai có kiểu trả về không hợp lệ (`int` và `double` không có `.name()`), nên biến mất và ứng viên đầu trả về `std::to_string`: `42` và `2.500000`. Với một `Joint` ứng viên đầu biến mất (`std::to_string` không có overload cho nó) và ứng viên thứ hai trả về nhãn `elbow`; mỗi lời gọi này có đúng một ứng viên khả dụng. Với `to_text("x")` cả hai ứng viên bị loại, nên không hàm nào khả dụng và compiler báo khối thứ hai bên dưới, dòng hiển thị sau đầu ra. Chương trình in ra (khối đầu), còn lỗi đến từ lời gọi thêm (khối thứ hai):

```text
42 2.500000 elbow
```

```text
error: no matching function for call to ‘to_text(const char [2])’
```

## Ví dụ có lời giải

Cả hai trường hợp dùng cập nhật Welford và các kiểm tra interface của phần lý thuyết ở trên.

### Trường hợp 1: Welford trên một tập dữ liệu nhỏ

**Đề bài.** Cho các giá trị $2,4,4,4,5,5,7,9$ chảy qua cập nhật Welford (mục "Một generic đúng về số học: Welford"), bắt đầu từ $\bar x_0=0$ và $M_0=0$. Tìm trung bình, phương sai mẫu và phương sai tổng thể, và nói compiler làm gì khi `RunningStats<int>` hoặc `mean(std::vector<std::string>{})` được instantiate.

**Lời giải.**

1. *Nêu cập nhật.* Với giá trị thứ $n$ là $x_n$: $\delta=x_n-\bar x_{n-1}$, $\bar x_n=\bar x_{n-1}+\delta/n$, $M_n=M_{n-1}+\delta\,(x_n-\bar x_n)$ (mục Welford). Giá trị đầu cho $\delta=2-0=2$, $\bar x_1=0+2/1=2$, $M_1=0+2\cdot(2-2)=0$.
2. *Áp dụng cho từng giá trị.* Mỗi dòng của bảng dùng $\bar x$ và $M$ của dòng trước:

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

   Với dòng 2: $\delta=4-2=2$, $\bar x_2=2+2/2=3$, $M_2=0+2\cdot(4-3)=2$.
3. *Đọc trạng thái cuối.* Sau $n=8$ giá trị, trung bình là $\bar x_8=5$ và $M_8=32$.
4. *Đổi sang phương sai.* Phương sai mẫu chia cho $n-1$: $s^2=M_8/(n-1)=32/7\approx4.5714$. Phương sai tổng thể chia cho $n$: $32/8=4$.
5. *Kiểm tra interface.* Instantiate `RunningStats<int>` kích hoạt `static_assert(std::is_floating_point_v<T>)`, nên build dừng với thông báo "RunningStats needs a floating-point type" thay vì lặng lẽ thực hiện phép chia nguyên trong `delta / n`. `mean(std::vector<std::string>{})` dừng ở `static_assert(std::is_arithmetic_v<V>)` với thông báo của tác giả.

**Kiểm tra.** Định nghĩa trực tiếp cho cùng các số: các độ lệch so với 5 là $-3,-1,-1,-1,0,0,2,4$, bình phương cộng lại $9+1+1+1+0+0+4+16=32$, nên $s^2=32/7$. Cài đặt tham khảo bên dưới trả về trung bình 5 và phương sai $32/7$ trong self-test của nó.

**Rút ra.** Một lượt, bộ nhớ $O(1)$ và không có phép trừ các số lớn: cập nhật theo dõi các độ lệch so với trung bình chạy, và template nêu giả định (kiểu dấu phẩy động) đúng ở nơi nó quan trọng.

### Trường hợp 2: vì sao phương sai ngây thơ trả về số âm

**Đề bài.** Bốn số đo $x=(10^9+4,\;10^9+7,\;10^9+13,\;10^9+16)$ có trung bình đúng $10^9+10$ và phương sai mẫu đúng $30$ (các độ lệch $-6,-3,3,6$, bình phương cộng lại $90$, $90/3=30$). Tính phương sai bằng `double` với công thức ngây thơ $(q-n\bar x^2)/(n-1)$, $q=\sum x^2$, giải thích kết quả, rồi tính lại bằng cập nhật Welford.

**Lời giải.**

1. *Các tổng.* $s=\sum x=4{,}000{,}000{,}040$ biểu diễn chính xác, nên $\bar x=s/4=1{,}000{,}000{,}010$ chính xác. $q$ đúng là $4\,000\,000\,080\,000\,000\,490$ và $n\bar x^2$ đúng là $4\,000\,000\,080\,000\,000\,400$.
2. *Khoảng cách giữa các double.* Cả hai số nằm trong $[2^{61},2^{62})$ ($2^{62}\approx4.61\times10^{18}$), nơi các `double` liên tiếp cách nhau $2^{61-52}=512$. Riêng lần làm tròn cuối đã dịch mỗi số tới $256$ (nửa khoảng cách), và $q$ còn tích lũy bốn phép cộng.
3. *Máy lưu gì.* Trong lần chạy thật $q$ được lưu là $4\,000\,000\,080\,000\,000\,000$ (sai số $-490$) và $n\bar x^2$ là $4\,000\,000\,080\,000\,000\,512$ (sai số $+112$). Hiệu của chúng là $q-n\bar x^2=-512$ (tính bằng Python), trong khi hiệu đúng là $490-400=90$. Hai số khổng lồ trùng nhau tới khoảng $17$ chữ số có nghĩa nhưng `double` chỉ giữ $15$-$16$, nên phép trừ phơi bày sai số làm tròn thay vì tín hiệu.
4. *Chia.* $-512/(n-1)=-512/3=-170.67$. Phương sai không thể âm; đó là triệu chứng nhìn thấy được, và trường hợp nguy hiểm là khi sai số tình cờ dương và đáp án chỉ đơn giản là sai.
5. *Dùng Welford.* Các giá trị chạy $(n,\delta,\bar x_n,M_n)$ là $(1,\,4,\,1000000004,\,0)$, $(2,\,3,\,1000000005.5,\,4.5)$, $(3,\,7.5,\,1000000008,\,42)$, $(4,\,8,\,1000000010,\,90)$ (ở đây $\delta$ đo từ trung bình chạy, mục Welford). Vậy $M_4=90$ và $s^2=90/3=30$ chính xác. Mỗi số hạng $\delta(x-\bar x)$ là tích của hai số cỡ 1 đến 10, không bao giờ là hiệu của hai số gần $10^{18}$.
6. *Dịch dữ liệu.* Phương sai không đổi nếu trừ một hằng khỏi mọi giá trị. Trừ giá trị đầu cho $(0,3,9,12)$ với $s=24$, $q=234$, $n\bar x^2=4\cdot36=144$, và công thức ngây thơ cho $(234-144)/3=30$ không gặp trở ngại.

**Kiểm tra.** Python với phân số chính xác cho $90/3=30$ với dữ liệu gốc và cùng giá trị với dữ liệu đã dịch; công thức ngây thơ bằng độ chính xác kép cho $-170.666\ldots$ (tử số in ra là $-512.0$). Tỉ số trong khối explore của mục Welford khớp: ở độ lệch $10^9$ khoảng cách chia cho $n-1$ là $512/3\approx171$, gấp khoảng $5.7$ lần phương sai thật.

**Rút ra.** Trừ trước khi bình phương, không phải sau. Welford không cần biết trước dữ liệu và chạy một lượt; phép dịch cần đoán tâm nhưng đơn giản hơn. Cả hai dựa trên cùng một nguyên tắc.

![Trái: trục số gần 4.00000008e18 với các double cách nhau 512, nơi q được lưu là 0 và n*mean^2 là 512, nên hiệu ngây thơ là -512 thay vì 90; phải: Welford M_n bằng 0, 4.5, 42 và 90 và phương sai 90/3 = 30](/lesson-figures/CPP06-4.svg)

*Hình: các số của Trường hợp 2. Bên trái, độ lệch so với $4\,000\,000\,080\,000\,000\,000$: vòng rỗng là giá trị đúng (490 và 400), vòng đặc là các double được lưu (0 và 512), nên hiệu lưu được là $0-512=-512$ so với hiệu đúng $490-400=90$. Bên phải, $M_n$ chạy của cập nhật Welford, mỗi bước cộng thêm một tích của các số nhỏ.*

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
3. **(Dễ)** Một bảng lúc biên dịch `make_cubes<N>()` lưu lập phương kiểu `int`, tức `i*i*i`. Nó chiếm bao nhiêu byte với $N=1200$ (giả sử `int` 4 byte), chỉ số nhỏ nhất nào làm `i*i*i` tràn một số nguyên có dấu 32-bit, và $N=1200$ có an toàn không?
4. **(Trung bình)** *(Adapted from: C++ Core Guidelines, T.62 - place template definitions where they are visible)* Một dự án định nghĩa `template <class T> T clamp_to(T, T, T);` trong `util.h` và thân hàm trong `util.cpp`; `main.cpp` gọi `clamp_to(3, 0, 5)` và bước link thất bại. Giải thích lỗi, và nêu hai cách sửa cùng đánh đổi của chúng.
5. **(Trung bình)** Tìm bug số học: đoạn code dưới tính phương sai của các giá trị gần $2\cdot10^9$ (ví dụ một timestamp nano giây). Phương sai mẫu thật của $\{2\cdot10^9+6,\ 2\cdot10^9+18,\ 2\cdot10^9+21,\ 2\cdot10^9+23\}$ là 58. Dự đoán dấu của kết quả, giải thích, và thay bằng cập nhật Welford.
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
12. **(Thử thách)** Cho `template <class T> void f(T&&); template <class T> void g(const T&&); template <class T> void h(T);` và `double d = 2.0; const double cd = 3.0; int b[4];`, với mỗi lời gọi hãy nêu `T` được suy ra và kiểu tham số, hoặc vì sao nó không biên dịch được: `f(d)`, `f(cd)`, `f(d + 1)`, `f(std::move(d))`, `g(2.5)`, `g(d)`, `h(b)`, `h(cd)`, `h("ab")`. Sau đó dùng reference collapsing để chỉ ra `std::forward<T>(x)` trả về gì trong `f` với `f(d)` và với `f(d + 1)`. *(phỏng theo cppreference, Template argument deduction, "Deduction from a function call")*
13. **(Thử thách)** Định nghĩa `lsum` là left fold một ngôi và `rsum` là right fold một ngôi của `+`. Tính cả hai trên `(2.0, 1e17, -1e17)` và trên `(1e17, -1e17, 2.0)` bằng `double` và giải thích từng kết quả từ khoảng cách giữa các số `double` gần $10^{17}$. Điều gì xảy ra với `lsum()` khi pack rỗng, và sửa chữ ký thế nào để tổng rỗng là `0.0`? Có thứ tự đối số nào làm cả hai fold chính xác với mọi đầu vào không? *(phỏng theo cppreference, Fold expressions)*
14. **(Thử thách)** Làm cho `clamp_to(T x, T lo, T hi)` chấp nhận `clamp_to(7, 0.0, 4.5)` bằng cách viết `lo` và `hi` là `typename id<T>::type`, với `template <class T> struct id { using type = T; };`. Dự đoán `clamp_to(7, 0.0, 4.5)`, `clamp_to(1, 1.5, 3.5)` và `clamp_to(0.75f, 1, 2)` (giá trị và `T` được suy ra). Giải thích vì sao cách sửa này nguy hiểm, và viết phiên bản thứ hai chấp nhận các kiểu đối số khác nhau nhưng từ chối mọi lời gọi mà một cận bị thu hẹp (narrowing). *(phỏng theo cppreference, Template argument deduction, "Non-deduced contexts")*
15. **(Thử thách)** `constexpr int arr[4] = {1,2,3,4};` và `constexpr int at(int i) { return arr[i]; }`. Nêu `static_assert(at(3) == 4);` và `static_assert(at(4) == 0);` cái nào biên dịch được và lời gọi lúc chạy `at(4)` làm gì. Sau đó viết `at` sao cho chỉ số ngoài phạm vi là lỗi biên dịch trong biểu thức hằng và là `std::out_of_range` bị ném lúc chạy, với cùng một thân hàm, và giải thích vì sao nó hoạt động. Cuối cùng, vì sao một hàm `constexpr` thất bại với mọi đối số là một vấn đề dù compiler im lặng? *(nguồn: cppreference, constexpr specifier, "Core constant expression" và quy tắc ill-formed NDR)*

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
3. Cài đặt `make_squares<N>()` và xác nhận compiler tính `make_squares<9>()[8]` lúc biên dịch.
4. Cài đặt `RunningStats<T>` với cập nhật Welford; kiểm tra các giá trị tính tay trong các test.
5. Cài đặt `mean` generic cho `vector<int>`, `list<float>` và một container rỗng; kiểm tra rằng một container chuỗi cho ra thông báo `static_assert` của bạn (thử riêng, rồi bỏ dòng đó).
6. Cố ý làm hỏng: tính phương sai bằng công thức ngây thơ và in giá trị cho dữ liệu `3e9 + x` của các test (x = 2, 5, 14, 15).

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
static_assert(clamp_to(9, 2, 6) == 6 && clamp_to(-4, 2, 6) == 2 && clamp_to(4, 2, 6) == 4);
static_assert(clamp_to(0.25, 0.0, 0.5) == 0.25);
static_assert(make_squares<9>()[8] == 64 && make_squares<9>()[0] == 0);
static_assert(deg2rad(180.0) > 3.14159 && deg2rad(180.0) < 3.1416);
static_assert(std::is_same_v<decltype(deg2rad(1.0f)), float>);

int main() {
  // hand-computed Welford data {3, 5, 5, 7, 10}: mean 6, sum of squared deviations 28 -> sample variance 7
  RunningStats<double> s;
  CHECK(s.count() == 0 && !s.mean() && !s.variance());
  s.push(3);
  CHECK(s.mean().value() == 3.0 && !s.variance());
  for (double x : {5.0, 5.0, 7.0, 10.0}) s.push(x);
  CHECK(s.count() == 5 && std::fabs(s.mean().value() - 6.0) < 1e-12);
  CHECK(std::fabs(s.variance().value() - 7.0) < 1e-12);
  // numerical stability: large offset, true variance of {2,5,14,15} is 42
  RunningStats<double> big;
  for (double x : {2.0, 5.0, 14.0, 15.0}) big.push(3e9 + x);
  CHECK(std::fabs(big.variance().value() - 42.0) < 1e-6);
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
3. $1200\cdot4=4800$ byte. $1290^3=2{,}146{,}689{,}000$ vừa, $1291^3=2{,}151{,}685{,}171>2{,}147{,}483{,}647$ tràn, nên chỉ số đầu tiên bị tràn là 1291. Chỉ số lớn nhất dùng với $N=1200$ là 1199, nên bảng an toàn; với $N\ge1292$ tràn số sẽ là lỗi biên dịch trong biểu thức hằng.
4. Compiler biên dịch `main.cpp` mà không thấy thân hàm, nên nó phát ra một lời gọi tới `clamp_to<int>`, nhưng `util.cpp` không bao giờ khởi tạo chuyên biệt đó: undefined reference. Cách 1: chuyển thân hàm vào header (đơn giản; mỗi translation unit đều instantiation, thời gian biên dịch dài hơn). Cách 2: explicit instantiation trong `util.cpp` (`template int clamp_to<int>(int, int, int);`), giới hạn các kiểu được phép nhưng giữ thời gian biên dịch thấp.
5. Kết quả là số âm: $-2048/3\approx-682.7$ (tính bằng Python). Ở đây $q\approx1.6\times10^{19}$ nằm trong $[2^{63},2^{64})$, nơi các double cách nhau $2^{11}=2048$; $q$ và $n\bar x^2$ bằng nhau đến khoảng 17 chữ số trong khi một double chỉ mang khoảng 16, nên hiệu bị sai số làm tròn chi phối. Phương sai không thể âm. Cập nhật Welford trừ các đại lượng nhỏ (các độ lệch) ở mỗi bước, nên tránh được triệt tiêu; nó trả về 58.
6. Output: `int 1.5 other`. Ở các nhánh bị loại bỏ, `std::sqrt(x)` không bao giờ được khởi tạo cho `int` hay `const char*`, nhờ `if constexpr`; với `if` thường, lời gọi phải biên dịch được cho mọi `T`, và `std::sqrt(const char*)` thất bại. (`sqrt(2.25)=1.5`, `to_string` cho "1.500000", substr(0,3) là `1.5`.)
7. `static_assert(std::is_arithmetic_v<typename Container::value_type>, "mean needs a container of arithmetic values");` đặt ở đầu hàm: lỗi là một dòng với thông báo của bạn. Với `requires std::is_arithmetic_v<std::ranges::range_value_t<C>>` của C++20 trong chữ ký, lỗi được báo tại điểm gọi dưới dạng ràng buộc không thỏa, overload resolution có thể loại ứng viên đó và chọn overload khác, và ràng buộc hiện trong tài liệu.
8. `a` là `int` (auto bỏ reference và const), `b` là `const int&`, `c` là `const int&` (decltype(auto) giữ kiểu đã khai báo của biểu thức `r`), `d` là `int` (`std::move(i)` cho một rvalue, auto copy giá trị). Chứng minh: `static_assert(std::is_same_v<decltype(a), int>);` và tương tự.
9. Giả định: `F` gọi được với `T` và trả về thứ chuyển đổi được sang `T` (một `static_assert(std::is_invocable_r_v<T, F, T>)`); `T` là dấu phẩy động (`static_assert`); `n >= 1` (kiểm tra lúc chạy và throw/trả lỗi); $a\le b$ hữu hạn; $f$ có đạo hàm bậc hai bị chặn trên khoảng. Với cận, $\max|f''|=\max|\sin|=1$, nên $\frac{(\pi/2)^3}{12n^2}\le10^{-6}\Rightarrow n\ge\sqrt{3.8758/(12\cdot10^{-6})}=568.3$, vậy $n=569$ (sai số thực với $n=569$ khoảng $6.4\times10^{-7}$).
10. Trong C++17, `std::sin` không bắt buộc là `constexpr`; GCC tính gộp nó như một phần mở rộng của compiler trong khi các compiler khác từ chối. Một bản thay thế portable: `constexpr double taylor_sin(double x) { double term = x, sum = x; for (int k = 1; k < 12; ++k) { term *= -x * x / ((2 * k) * (2 * k + 1)); sum += term; } return sum; }`. Kiểm tra so với `std::sin` trên $[0,\pi/2]$ (và khoảng đã được gói lại mà bạn sẽ dùng): sai số tối đa ở đó khoảng $3\times10^{-16}$. Độ chính xác giảm với $|x|$ lớn, nên hãy rút gọn đối số trước.
11. Một câu trả lời tốt gồm: một `constexpr std::array<double, 91>` được dựng bởi hàm `constexpr`; `static_assert(table[0] == 0.0)` và một kiểm tra cận cho `table[90]` (nằm giữa 0.999999 và 1.000001); một vòng lặp theo bước 0.01 độ tính nội suy tuyến tính giữa các lân cận và sai số tuyệt đối tối đa so với `std::sin` (khoảng $\frac{h^2}{8}\max|f''|=\frac{(0.01745)^2}{8}\approx3.8\times10^{-5}$); kích thước bảng là $91\cdot8=728$ byte; và một nhận định về chi phí lúc biên dịch.
12. `f(d)`: `T = double&`, tham số `double&` (`double& &&` rút gọn thành `double&`). `f(cd)`: `T = const double&`, tham số `const double&`. `f(d + 1)`: tổng là prvalue, `T = double`, tham số `double&&`. `f(std::move(d))`: một xvalue, lại `T = double`, tham số `double&&`. `g(2.5)`: `T = double`, tham số `const double&&`. `g(d)`: lỗi, `const T&&` không phải forwarding reference, nên `T = double` và lvalue `d` không bind được `const double&&` (GCC: `cannot bind rvalue reference of type 'const double&&' to lvalue of type 'double'`). `h(b)`: `T = int*` (mảng decay). `h(cd)`: `T = double` (bỏ `const` cấp cao nhất). `h("ab")`: `T = const char*` (mảng `const char[3]` decay). `std::forward<T>(x)` là `static_cast<T&&>(x)`: với `f(d)` đó là `static_cast<double& &&>` = `double&`, một lvalue; với `f(d + 1)` đó là `static_cast<double&&>`, một rvalue, nên move semantics chỉ được bật khi người gọi truyền rvalue. (Đã kiểm tra bằng `static_assert(std::is_same_v<...>)` trên các kiểu được suy ra của mọi lời gọi trừ `g(d)`, có thông báo lỗi được đọc từ g++ 11.4, `-std=c++17`.)
13. `lsum(2.0,1e17,-1e17)`: các double trong $[2^{56},2^{57})$, khoảng chứa $10^{17}$, cách nhau $2^{56-52}=16$, nên $2+10^{17}$ chỉ cách $10^{17}$ là $2<8$ và làm tròn về nó; rồi trừ $10^{17}$ cho `0`. `rsum` của cùng pack: $2+(10^{17}-10^{17})=2$. Với `(1e17,-1e17,2.0)` kết quả đổi chỗ: `lsum` $=0+2=2$, `rsum` $=10^{17}+(-10^{17}+2)=10^{17}+(-10^{17})=0$, vì $-10^{17}+2$ cũng làm tròn về $-10^{17}$ (đã tính: `0` và `2` cho pack đầu, `2` và `0` cho pack sau). Pack rỗng: `(... + args)` là ill-formed (GCC: `fold of empty expansion over operator+`); dùng fold hai ngôi `(0.0 + ... + args)`, có giá trị `0.0` với pack rỗng. Không thứ tự nào chính xác cho mọi đầu vào: dù dùng chiều nào, cặp ví dụ trên chỉ ra một đầu vào mà tổng theo chiều đó sai; muốn chính xác cần cộng bù hoặc sắp xếp theo độ lớn, chứ không phải chọn fold.
14. Với `T` chỉ suy ra từ `x`: `clamp_to(7, 0.0, 4.5)` có `T = int`, `lo = 0`, `hi = 4` (4.5 bị cắt cụt), và trả về `4` (đã tính), dù kẹp 7 vào $[0,4.5]$ lẽ ra phải cho 4.5. `clamp_to(1, 1.5, 3.5)` cho `lo = 1`, `hi = 3` và trả về `1` (đã tính), không phải 1.5. `clamp_to(0.75f, 1, 2)` có `T = float`, các cận `int` chuyển chính xác, kết quả `1.0f`: vô hại. Nguy hiểm là các cận bị chuyển kiểu âm thầm sang kiểu của `x`. Phiên bản an toàn hơn nhận ba kiểu độc lập và từ chối narrowing: `template <class T, class L, class H> constexpr T clamp_to(T x, L lo, H hi) { static_assert(std::is_same_v<std::common_type_t<T, L, H>, T>, "bounds would be narrowed"); return x < lo ? T(lo) : (x > hi ? T(hi) : x); }`. Với nó `clamp_to(7, 0.0, 4.5)` thất bại với `bounds would be narrowed`, còn `clamp_to(0.75f, 1, 2)` và `clamp_to(7.0, 0, 4.5)` (trả về 4.5) vẫn biên dịch (đã kiểm tra bằng g++ 11.4). Đánh đổi: mẹo `identity` chỉ một dòng nhưng chuyển kiểu âm thầm; phiên bản ba tham số từ chối lời gọi sai lúc biên dịch nhưng cần `clamp_to<double>(7, 0, 4.5)` tường minh hoặc ép kiểu khi thật sự muốn thăng kiểu, và có ba tham số template cần ghi tài liệu.
15. `static_assert(at(3) == 4)` biên dịch được. `static_assert(at(4) == 0)` là lỗi (GCC: `array subscript value '4' is outside the bounds of array 'arr'`), còn lời gọi lúc chạy `at(4)` là hành vi không xác định mà không có chẩn đoán. Một thân hàm duy nhất: `constexpr int at(int i) { return (i >= 0 && i < 4) ? arr[i] : throw std::out_of_range("index"); }`. Trong biểu thức hằng, nhánh throw không bao giờ được chọn với chỉ số hợp lệ (nên lời gọi là hằng), nhưng với `at(4)` việc tính đi đến `throw`, không được phép trong biểu thức hằng, nên compiler báo `<throw-expression>` is not a constant expression; lúc chạy cùng nhánh đó ném `std::out_of_range` (đã kiểm tra bằng g++ 11.4: `at(2)` trong `static_assert` biên dịch được, `at(4)` trong `static_assert` bị từ chối, và lời gọi lúc chạy `at(argc+7)` ném exception). Một hàm `constexpr` mà không đối số nào cho biểu thức hằng là ill-formed, no diagnostic required: chương trình không hợp lệ nhưng compiler không bắt buộc báo, nên code có thể hỏng trên compiler hoặc phiên bản khác.

## Đọc thêm

- [cppreference: Templates](https://en.cppreference.com/w/cpp/language/templates) - các quy tắc về deduction, specialization và instantiation một cách chi tiết.
- [cppreference: constexpr specifier](https://en.cppreference.com/w/cpp/language/constexpr) - điều gì được phép trong biểu thức hằng ở mỗi tiêu chuẩn.
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - phần T về template và lập trình generic, và các quy tắc về hằng (Con) và `constexpr` (F.4).
- [cppreference: Template argument deduction](https://en.cppreference.com/w/cpp/language/template_argument_deduction) - forwarding reference, các điều chỉnh của `P` và `A`, và danh sách non-deduced context.
- [cppreference: Fold expressions](https://en.cppreference.com/w/cpp/language/fold) - bốn dạng fold và quy tắc cho pack rỗng.

**Thực hành thêm:** các quiz ở [LearnCpp: function templates](https://www.learncpp.com/cpp-tutorial/function-templates/), [templates in multiple files](https://www.learncpp.com/cpp-tutorial/using-function-templates-in-multiple-files/), [class templates](https://www.learncpp.com/cpp-tutorial/class-templates/), [constexpr functions](https://www.learncpp.com/cpp-tutorial/constexpr-functions/) và [constexpr if](https://www.learncpp.com/cpp-tutorial/constexpr-if-statements/) (đáp án hiện trên mỗi trang), phần [templates and generic programming](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#t-templates-and-generic-programming) của Core Guidelines, và trang Eigen về [viết hàm nhận kiểu Eigen](https://eigen.tuxfamily.org/dox/TopicFunctionTakingEigenTypes.html) (một bài toán ràng buộc template thực tế).
