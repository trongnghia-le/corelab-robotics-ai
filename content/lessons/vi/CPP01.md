---
{"title": "Cơ bản C++: kiểu dữ liệu, phạm vi và giá trị có thể dự đoán", "summary": "Viết một chương trình biên dịch nhỏ và hiểu phép tính số học của nó.", "objectives": ["Biên dịch và chạy một chương trình C++17.", "Dự đoán phép tính số nguyên và số thực dấu phẩy động.", "Dùng vector và tham chiếu const một cách an toàn."]}
---

## Vì sao điều này quan trọng

Viết một chương trình biên dịch nhỏ và hiểu phép tính số học của nó. Bài học này phát triển phép tính cốt lõi trước khi yêu cầu bạn áp dụng nó vào một bối cảnh mới. Hãy làm bài chẩn đoán trước nếu bạn nghĩ mình đã biết rồi; việc từng dùng công cụ không phải là bằng chứng của sự hiểu.

## Trực giác

C++ làm cho cách biểu diễn dữ liệu và vòng đời đối tượng (lifetime) trở nên hiển hiện. Một kiểu (type) cho trình biên dịch biết phép toán nào hợp lệ, nhưng cũng quyết định số học và bố cục bộ nhớ. Biên dịch bắt được một số lỗi trước khi chạy; các bài kiểm thử phải bắt những hành vi sai mà vẫn là C++ hợp lệ.

![Sơ đồ bộ nhớ kiểu stack: một vector double có kích thước 3 với chỉ số hợp lệ từ 0 đến 2, cùng phép chia số nguyên so với số thực của 5 cho 2.](/lesson-figures/CPP01.svg)

*Kiểu quyết định số học: phép chia nguyên 5/2 bị cắt cụt thành 2 trong khi 5.0/2 giữ 2.5; chỉ số hợp lệ của vector dừng ở kích thước trừ một.*

## Lý thuyết và suy dẫn

Một khai báo biến đưa vào một đối tượng có kiểu: `int count{3};` lưu một số nguyên, còn `double dt{0.01};` lưu một giá trị thực xấp xỉ. Hãy khởi tạo mọi biến vô hướng cục bộ trước khi đọc. Phép chia nguyên cắt cụt về phía không: `5/2` là 2, trong khi `5.0/2` là 2.5. Chuyển kết quả đã bị cắt cụt sang double sau đó không khôi phục được phần thập phân đã mất.

Hàm khai báo kiểu trả về và các tham số có kiểu. Truyền vector theo giá trị (by value) sẽ sao chép nó; `const std::vector<double>&` cho phép hàm xem vector hiện có mà không sửa. Đối tượng được tham chiếu phải còn sống trong suốt lời gọi. Phạm vi cục bộ (scope) quyết định tên nào nhìn thấy được ở đâu và khi nào các đối tượng tự động thông thường bị hủy.

Dùng `std::vector` cho một dãy có kích thước xác định lúc chạy. `size()` của nó là một số đếm, còn chỉ số hợp lệ chạy từ không đến kích thước trừ một. `operator[]` không kiểm tra biên; `.at()` thì có. Ưu tiên vòng lặp range-based khi chỉ số không có ý nghĩa riêng. Biên dịch với cảnh báo được bật và coi mỗi cảnh báo là một câu hỏi cần giải quyết, không phải đồ trang trí.

## Ví dụ có lời giải

Nếu int steps=5 và total=2, thì `double ratio=steps/total;` cho 2.0 vì phép chia xảy ra dưới dạng số nguyên. `double ratio=static_cast<double>(steps)/total;` cho 2.5. Với một vector rỗng, hàm tính trung bình phải từ chối đầu vào trước khi chia.

## Bài tập

1. **(Dễ)** Một encoder báo `int ticks = 7;` trong `int rev = 2;` vòng quay. Hãy dự đoán giá trị của `double a = ticks / rev;` và của `double b = static_cast<double>(ticks) / rev;`. Phần thập phân bị mất chính xác ở đâu trong `a`? *(Phỏng theo: LearnCpp, the chapter on arithmetic operators and integer division)*
2. **(Dễ)** Một vòng điều khiển chứa `double dt = 1 / 100;` với ý định là chu kỳ 100 Hz. `dt` nhận giá trị nào, bộ điều khiển sau đó làm gì, và có hai cách nào để viết đúng? *(Phỏng theo: C++ Core Guidelines, ES.20 and ES.46 on initialisation and narrowing)*
3. **(Vừa)** **Tìm lỗi.** Đoạn này in một vector theo thứ tự ngược:
   ```cpp
   void print_reversed(const std::vector<double>& v) {
       for (std::size_t i = v.size() - 1; i >= 0; --i)
           std::cout << v[i] << ' ';
   }
   ```
   Hãy giải thích hai thất bại riêng biệt (đầu vào không rỗng và rỗng) và đưa ra một vòng lặp đúng. *(Phỏng theo: C++ Core Guidelines, ES.100 on mixing signed and unsigned)*
4. **(Vừa)** **Dự đoán đầu ra** (suy luận từng câu lệnh trước khi biên dịch):
   ```cpp
   std::vector<int> v{4, 8, 15};
   std::cout << v.size() - 1 << ' ';
   try { std::cout << v.at(3); }
   catch (const std::out_of_range&) { std::cout << "caught"; }
   ```
   `v[3]` sẽ làm gì thay vào đó, và vì sao điều đó tệ hơn đối với robot?
5. **(Vừa)** Một node perception truyền một point cloud (`std::vector<double>` gồm $10^6$ phần tử) tới một bộ lọc ở 30 Hz. Hãy ước lượng lưu lượng bộ nhớ gây ra khi truyền theo giá trị so với `const&`. Đưa ra một signature tránh việc sao chép và ngăn việc sửa đổi.
6. **(Vừa)** Một sinh viên viết `double s = 0; for (int i = 0; i < 10; ++i) s += 0.1; if (s == 1.0) arm_motor();`. Hãy dự đoán motor có được kích hoạt hay không, cho sai số xấp xỉ $1-s$, và viết một phép so sánh an toàn. Giải thích vì sao `double` vẫn tốt hơn `float` ở đây.
7. **(Khó)** **Tìm lỗi.** Một trung bình trượt (moving average) cửa sổ `w` trên `x`:
   ```cpp
   std::vector<double> y;
   for (std::size_t i = 0; i + w < x.size(); ++i) {
       double s = 0;
       for (std::size_t j = i; j < i + w; ++j) s += x[j];
       y.push_back(s / w);
   }
   ```
   Với `x = {1,2,3,4}`, `w = 2` hãy liệt kê nó trả về gì và đáng ra phải trả về gì. Nêu cách sửa và hai đầu vào khác mà hàm phải từ chối.
8. **(Khó)** Bạn làm mượt vận tốc motor đo ở 1 kHz bằng trung bình trượt 11 mẫu. Hãy đặc tả hợp đồng của hàm (kiểu, tiền điều kiện, độ dài đầu ra, ý nghĩa của các đầu ra đầu tiên). Tính độ trễ mà bộ lọc thêm vào cho đầu vào dốc (ramp), và nói khi nào độ trễ đó không chấp nhận được trong một vòng điều khiển.
9. **(Khó)** **Suy dẫn.** Chứng minh rằng cập nhật streaming $y_{k+1}=y_k+(x_{k+w}-x_k)/w$ bằng việc tính lại tổng cửa sổ. Sau đó giải thích vì sao việc dùng lặp lại qua hàng triệu mẫu có thể gây trôi (drift) trong dấu phẩy động, và gợi ý một biện pháp khắc phục.
10. **(Dự án)** Viết `stats.hpp`/`main.cpp` với `mean`, `variance` và `moving_average`, một `main` kiểm thử để kiểm tra các trường hợp tính tay và các đường lỗi, biên dịch với `-std=c++17 -Wall -Wextra -Wpedantic`, rồi dựng lại với `-fsanitize=address,undefined -g` và báo cáo đầu ra của cả hai bản build.

## Cài đặt tham khảo

Hãy đọc hợp đồng (contract) trước. Dự đoán đầu ra trước khi chạy code ở máy bạn. Phần này dùng để học; bài nộp sao chép từ đây là thực hành có hỗ trợ, không phải bằng chứng độc lập.

```cpp
#include <vector>
#include <stdexcept>
#include <cassert>
double mean(const std::vector<double>& x) {
    if (x.empty()) throw std::invalid_argument("empty");
    double sum{0.0};
    for (double v : x) sum += v;
    return sum / static_cast<double>(x.size());
}
int main() { assert(mean({2.,4.,6.}) == 4.); }
// g++ -std=c++17 -Wall -Wextra -Wpedantic main.cpp -o demo
```

## Thực hành độc lập

### Mục tiêu
Viết một thư viện số nhỏ có kiểm thử bằng C++17: mean, variance, một moving average với hợp đồng chặt chẽ, và một phép chia không thể cắt cụt một cách âm thầm. Quan sát từng đường lỗi được kích hoạt và từng bất biến được giữ.

### Chuẩn bị
Một trình biên dịch C++17 (`g++` hoặc `clang++`). Lưu code khởi đầu và các bài kiểm thử chung thành `lab.cpp`, rồi biên dịch bằng `g++ -std=c++17 -Wall -Wextra -Wpedantic lab.cpp -o lab && ./lab`. Sau đó, dựng lại với `-fsanitize=address,undefined -g`.

### Nhiệm vụ
1. Cài đặt `mean` và `safe_ratio`. Dự đoán bằng tay `safe_ratio(5, 2)` trả về gì và vì sao `5 / 2` đơn thuần sẽ không như vậy.
2. Cài đặt `variance` dùng `mean` (hai lượt). Hãy tính tay `{2, 4, 6}` trước.
3. Cài đặt `moving_average` với độ dài đầu ra chính xác $n-w+1$ và hai phép kiểm tra tiền điều kiện.
4. Biên dịch với cảnh báo bật. Sửa mọi cảnh báo (thường là signed/unsigned) thay vì dập tắt chúng.
5. Dựng lại với sanitizer, rồi tạm thời đổi một cận vòng lặp thành `<` thay vì `<=` và xem bài kiểm thử nào bắt được.

### Code khởi đầu
```cpp
#include <cassert>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <stdexcept>
#include <vector>

// Mean of x. Throw std::invalid_argument if x is empty.
double mean(const std::vector<double>& x) { throw std::logic_error("not implemented"); }

// Population variance (divide by n) using mean(); throw on empty input.
double variance(const std::vector<double>& x) { throw std::logic_error("not implemented"); }

// Window means: output length n-w+1, y[k] = mean of x[k..k+w-1].
// Throw std::invalid_argument if w == 0 or w > x.size().
std::vector<double> moving_average(const std::vector<double>& x, std::size_t w) { throw std::logic_error("not implemented"); }

// Return a/b as a double (no truncation). Throw std::domain_error if b == 0.
double safe_ratio(int a, int b) { throw std::logic_error("not implemented"); }
```

### Kiểm thử
Dán đoạn này bên dưới code khởi đầu (cùng một file) rồi chạy. Mọi kiểm tra đều là `assert` thuần; lần thất bại đầu tiên sẽ dừng chương trình.

```cpp
static bool near(double a, double b) { return std::abs(a - b) < 1e-12; }
template <class E, class F> static bool throws(F f) { try { f(); } catch (const E&) { return true; } catch (...) { return false; } return false; }

int main() {
    // hand-computed cases
    assert(near(mean({2., 4., 6.}), 4.));
    assert(near(mean({-3., 3.}), 0.));
    assert(near(mean({5.}), 5.));                       // singleton
    assert(near(variance({2., 4., 6.}), 8. / 3.));      // (4+0+4)/3
    assert(near(safe_ratio(5, 2), 2.5));
    auto y = moving_average({1, 2, 3, 4}, 2);
    assert(y.size() == 3 && near(y[0], 1.5) && near(y[1], 2.5) && near(y[2], 3.5));
    // error paths
    assert(throws<std::invalid_argument>([] { mean({}); }));
    assert(throws<std::invalid_argument>([] { moving_average({1, 2}, 0); }));
    assert(throws<std::invalid_argument>([] { moving_average({1, 2}, 3); }));
    assert(throws<std::domain_error>([] { safe_ratio(1, 0); }));
    // invariants: w == 1 returns the input; w == n returns the mean; shift invariance of variance
    std::vector<double> x{3, -1, 4, 1, -5, 9};
    auto id = moving_average(x, 1);
    for (std::size_t i = 0; i < x.size(); ++i) assert(near(id[i], x[i]));
    auto full = moving_average(x, x.size());
    assert(full.size() == 1 && near(full[0], mean(x)));
    std::vector<double> shifted;
    for (double v : x) shifted.push_back(v + 100.0);
    assert(std::abs(variance(shifted) - variance(x)) < 1e-9);
    std::cout << "mean = " << mean(x) << ", variance = " << variance(x) << ", ma size = " << moving_average(x, 3).size() << "\n";
    std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi
Một lời giải đúng sẽ in ra kết quả sau; một `assert` thất bại sẽ dừng cùng với tên file và dòng.

```text
mean = 1.83333, variance = 18.8056, ma size = 4
all tests passed
```

### Thử thách mở rộng
Thêm `class MovingAverage` với `double push(double v)` giữ một ring buffer và tổng chạy với độ phức tạp O(1) mỗi mẫu, và kiểm thử rằng nó khớp với `moving_average` trên dữ liệu ngẫu nhiên đến 1e-9. Giải thích cách bạn sẽ ngăn trôi dấu phẩy động.

### Thực hành với thư viện
Làm lại bài lab bằng thư viện chuẩn C++17 thay vì các vòng lặp tự viết: `std::accumulate` cho mean, `std::transform_reduce` cho variance, và `std::partial_sum` (tổng tiền tố) cho moving average, trong đó $y_k=(P_{k+w}-P_k)/w$. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra -Wpedantic lib.cpp -o lib && ./lib`. Sau đó chạy các bài kiểm thử của bạn trên các phiên bản này: chúng phải khớp đến $10^{-12}$.

```cpp
#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <vector>

double mean_std(const std::vector<double>& x) {
    if (x.empty()) throw std::invalid_argument("empty");
    return std::accumulate(x.begin(), x.end(), 0.0) / static_cast<double>(x.size());
}
double variance_std(const std::vector<double>& x) {
    const double m = mean_std(x);
    return std::transform_reduce(x.begin(), x.end(), 0.0, std::plus<>{},
                                 [m](double v) { return (v - m) * (v - m); }) / static_cast<double>(x.size());
}
// Moving average through prefix sums: y[k] = (P[k+w] - P[k]) / w
std::vector<double> moving_average_std(const std::vector<double>& x, std::size_t w) {
    if (w == 0 || w > x.size()) throw std::invalid_argument("window");
    std::vector<double> p(x.size() + 1, 0.0);
    std::partial_sum(x.begin(), x.end(), p.begin() + 1);
    std::vector<double> y(x.size() - w + 1);
    for (std::size_t k = 0; k < y.size(); ++k) y[k] = (p[k + w] - p[k]) / static_cast<double>(w);
    return y;
}

int main() {
    std::vector<double> x{3, -1, 4, 1, -5, 9};
    assert(std::abs(mean_std(x) - 11.0 / 6.0) < 1e-12);
    const auto y = moving_average_std(x, 3);
    const std::vector<double> want{2.0, 4.0 / 3.0, 0.0, 5.0 / 3.0};
    assert(y.size() == want.size() && std::equal(y.begin(), y.end(), want.begin(),
           [](double a, double b) { return std::abs(a - b) < 1e-12; }));
    std::cout << "variance = " << variance_std(x) << "\n";   // matches the hand-written lab
    std::cout << "library track ok\n";
}
```

Đầu ra kỳ vọng: `variance = 18.8056` rồi `library track ok`. Lưu ý rằng `std::accumulate(x.begin(), x.end(), 0)` với giá trị khởi đầu kiểu `int` sẽ cắt cụt âm thầm mọi tổng riêng; chữ `0.0` là quan trọng.

## Kiểm chứng

Hãy kiểm tra ví dụ số đã giải một cách độc lập, sau đó thử một trường hợp biên và một bất biến từ phần suy dẫn. Giữ kết quả mong đợi tách biệt với phần cài đặt. Cố ý đổi một dấu hoặc bỏ một số hạng: các bài kiểm thử của bạn phải loại bỏ phiên bản bị hỏng đó. Dùng bài chẩn đoán để kiểm tra khái niệm và lập luận bằng số; các câu trả lời ngắn vẫn là thực hành được hướng dẫn bằng rubric.

## Lỗi thường gặp

Một số nguyên cục bộ chưa khởi tạo không có giá trị hợp lệ nào dự đoán được để dựa vào. Truy cập vector ngoài phạm vi không phải là cách an toàn để phát hiện hết dữ liệu. Một tham chiếu không kéo dài vòng đời của một đối tượng bất kỳ.

## Phương án khác và đánh đổi

Python tiện cho việc khảo sát nhanh; C++ cung cấp kiểu tường minh và quyền kiểm soát tài nguyên. Hãy bắt đầu với các container chuẩn và quyền sở hữu (ownership) rõ ràng trước khi tối ưu hay đưa vào con trỏ thô.

## Vận dụng và ghi nhớ

Tính một moving average cho vận tốc motor được lấy mẫu. Nêu kiểu số của bạn, hợp đồng đầu vào, hành vi ở biên, và một bài kiểm thử bắt được lỗi cắt cụt số nguyên.

Hãy đóng tài liệu tham khảo trước khi thử. Giải thích các giả định của bạn và một cách mà câu trả lời của bạn có thể sai. Quay lại sau ít nhất một tuần và dựng lại lập luận chính từ một trang giấy trắng. Một bài quiz đơn thuần không kiểm chứng được khả năng vận dụng vào tình huống lạ hay năng lực ở mức nghiên cứu.

## Đáp án bài tập

1. `a` là `3` (in ra 3) vì `ticks / rev` được tính dưới dạng `int / int` (cắt cụt) trước khi kết quả được chuyển đổi; `b` là `3.5`. Phần thập phân mất ở phép chia, không phải ở phép gán.
2. `1 / 100` là phép chia nguyên, nên `dt` là `0`. Một bộ điều khiển với `dt = 0` không bao giờ tích phân (hoặc chia cho không trong đạo hàm). Hãy viết `1.0 / 100` hoặc `0.01` (hoặc `constexpr double dt{1.0/100.0};`).
3. `size_t` không dấu, nên `i >= 0` luôn đúng: sau khi `i == 0` phép giảm quay vòng thành một giá trị rất lớn và `v[i]` đọc ngoài biên (hành vi không xác định, undefined behaviour). Với vector rỗng, `v.size() - 1` đã quay vòng thành giá trị rất lớn. Đúng: `for (std::size_t i = v.size(); i-- > 0; ) std::cout << v[i] << ' ';`
4. `v.size() - 1` là `2`; `v.at(3)` ném `std::out_of_range`, nên đầu ra là `2 caught`. `v[3]` là hành vi không xác định không kiểm tra: nó có thể đọc rác, sập về sau, hoặc có vẻ chạy được, điều này tệ hơn đối với robot so với một exception rõ ràng.
5. Theo giá trị: $10^6\times8$ B $=8$ MB được sao chép mỗi lần gọi; ở 30 Hz là khoảng $240$ MB/s lưu lượng thêm cộng một lần cấp phát mỗi lần. Theo tham chiếu: không sao chép. Signature `void filter(const std::vector<double>& cloud);`.
6. Tổng là $0.9999999999999999$, nên `s == 1.0` sai và motor không được kích hoạt; $1-s\approx1.1\times10^{-16}$. Dùng `std::abs(s - 1.0) < 1e-9`. `double` có khoảng 16 chữ số so với khoảng 7 của `float`, nên sai số làm tròn tích lũy nhỏ hơn nhiều.
7. Nó trả về 2 giá trị `{1.5, 2.5}`; đáng ra phải trả về 3 giá trị `{1.5, 2.5, 3.5}`. Điều kiện vòng lặp nên là `i + w <= x.size()`. Cũng cần từ chối `w == 0` (chia cho không) và `w > x.size()` (không có cửa sổ đầy đủ; `i + w` sẽ không bao giờ hợp lệ).
8. Hợp đồng: `x` là một vector các double hữu hạn, `1 <= w <= x.size()`, độ dài đầu ra `x.size() - w + 1`, phần tử `k` là trung bình của `x[k..k+w-1]` (nên không có đầu ra cho `w-1` mẫu khởi động đầu tiên). Với đầu vào dốc, trung bình trễ $(w-1)/2=5$ mẫu $=5$ ms ở 1 kHz. Không chấp nhận được khi biên pha (phase margin) hoặc ngân sách độ trễ của vòng chặt hơn mức đó, hoặc khi dùng đạo hàm của giá trị đã lọc.
9. Tổng cửa sổ $S_{k+1}=S_k-x_k+x_{k+w}$ vì các cửa sổ chỉ khác nhau ở việc bỏ $x_k$ và thêm $x_{k+w}$; chia cho $w$ cho ra cập nhật. Mỗi lần cập nhật thêm một sai số làm tròn không bao giờ được sửa, nên sai số đi lang thang ngẫu nhiên (random walk). Cách khắc phục: tính lại tổng từ đầu mỗi N bước, dùng cộng bù (Kahan/compensated summation), hoặc bộ tích lũy số nguyên cho số đếm cảm biến nguyên.
10. Một câu trả lời tốt cho thấy cả hai bản build in cùng kết quả kiểm thử, có các bài kiểm thử đường lỗi (rỗng, `w == 0`, `w > n`), báo cáo rằng sanitizer không đưa ra chẩn đoán nào cho các đường đã chạy, và nêu rằng một lần chạy sạch không phải là bằng chứng của sự đúng đắn.

## Đọc thêm

[LearnCpp](https://www.learncpp.com/) — khóa học chính, tài liệu, hoặc bộ tham khảo được cung cấp. Hãy theo mục chủ đề liên quan; đây là các liên kết đọc thêm, không phải các chương sách được sao chép lại.

**Thực hành thêm:** [LearnCpp chapter 4 quiz](https://www.learncpp.com/cpp-tutorial/chapter-4-summary-and-quiz/) (kiểu cơ bản và phép chia nguyên), [LearnCpp chapter 12 quiz](https://www.learncpp.com/cpp-tutorial/chapter-12-summary-and-quiz/) (kiểu hợp thành và tham chiếu), [LearnCpp on the std::vector unsigned subscript problem](https://www.learncpp.com/cpp-tutorial/stdvector-and-the-unsigned-length-and-subscript-problem/), và [Exercism C++ track](https://exercism.org/tracks/cpp/exercises).
