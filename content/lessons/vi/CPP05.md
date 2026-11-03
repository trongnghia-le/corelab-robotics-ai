---
{"title": "STL container, iterator và algorithm", "summary": "Chọn container từ mẫu truy cập dữ liệu, dùng đúng iterator range và các thuật toán chuẩn, rồi đo để thấy sự đánh đổi.", "objectives": ["Chọn giữa vector, deque, list, map, unordered_map và set dựa trên các thao tác mà chương trình thực hiện.", "Mô tả các iterator category, khoảng nửa mở (half-open range) và sự vô hiệu hóa iterator (iterator invalidation).", "Dùng đúng lower_bound, accumulate, remove_if/erase và nth_element.", "Thiết kế một micro-benchmark công bằng và diễn giải kết quả."]}
---
## Vì sao điều này quan trọng

Phần lớn code robot dành thời gian di chuyển các chuỗi số: scan, quỹ đạo, các giá trị cảm biến có timestamp, các detection. Standard library cung cấp container và thuật toán đã được kiểm thử cho những việc này, và chọn khôn ngoan thay đổi chi phí theo nhiều bậc độ lớn. Tìm mẫu gần nhất theo timestamp bằng cách quét 360,000 mẫu của một giờ dữ liệu 100 Hz tốn 360,000 phép so sánh; bằng binary search chỉ tốn 19. Chọn sai container cũng là nguồn bug: erase trong vòng lặp làm vô hiệu hóa iterator, và `map::operator[]` lặng lẽ chèn một key còn thiếu. Bài này dạy mô hình đằng sau STL (container giữ phần tử, iterator trỏ vào chúng, thuật toán làm việc trên các iterator range) để bạn có thể chọn, kết hợp và kiểm thử chúng một cách tự tin.

## Trực giác

Hãy nghĩ đến ba tầng. **Container** sở hữu các phần tử và quyết định bố cục của chúng: `vector` là một khối liên tục, `list` là các node cấp phát riêng lẻ, `map` là một cây cân bằng. **Iterator** là con trỏ tổng quát hóa: chúng nói "ở đây" và "tiếp theo". **Thuật toán** (`sort`, `find`, `lower_bound`, `accumulate`) được viết một lần dựa trên iterator, nên chúng chạy trên mọi container cung cấp đúng iterator category. Một thuật toán không bao giờ thay đổi *kích thước* của container, vì nó chỉ thấy iterator; muốn thu nhỏ phải gọi `erase` của container.

Các range là **nửa mở**: `[first, last)` chứa `first` nhưng không chứa `last`. Một range rỗng có `first == last`. Quy ước này là lý do `v.end()` hợp lệ để so sánh nhưng không bao giờ để dereference, và là lý do `lower_bound` có thể trả về `end()` với nghĩa "không tìm thấy".

![Vector có thứ tự liên tục với lower_bound tìm t = 3, và số phép so sánh theo n cho binary search](/lesson-figures/CPP05.svg)

*Binary search trên một vector có thứ tự và liên tục giảm một nửa cửa sổ ở mỗi bước, nên số phép so sánh tăng như $\log_2 n$ (10, 14, 17, 20 cho $n=10^3,\dots,10^6$) trong khi quét tuyến tính cần tới $n$. Một cây cần cùng số phép so sánh logarit nhưng kèm các bước nhảy con trỏ.*

## Lý thuyết và suy dẫn

### Chọn container

| Container | Bố cục | Truy cập chỉ số / tìm | Chèn / xóa | Ghi chú |
|---|---|---|---|---|
| `vector<T>` | liên tục | chỉ số $O(1)$; tìm $O(n)$, $O(\log n)$ nếu đã sắp xếp | cuối: amortized $O(1)$; giữa: $O(n)$ | lựa chọn mặc định; thân thiện với cache |
| `deque<T>` | các khối | chỉ số $O(1)$ | cả hai đầu $O(1)$ | hàng đợi FIFO, cửa sổ trượt |
| `list<T>` | các node | $O(n)$ | $O(1)$ tại một iterator đã biết | hiếm khi đáng dùng; locality kém |
| `map<K,V>` | cây cân bằng | $O(\log n)$ | $O(\log n)$ | sắp theo key, iterator ổn định |
| `unordered_map<K,V>` | bảng băm | kỳ vọng $O(1)$ | kỳ vọng $O(1)$ | không có thứ tự, không có truy vấn khoảng |
| `set<K>` | cây | $O(\log n)$ | $O(\log n)$ | key duy nhất và có thứ tự |

Hãy chọn từ các *thao tác*: bạn tra cứu theo key chính xác, theo key gần nhất, hay theo khoảng? Chỉ chèn ở cuối, hay ở giữa? Có cần thứ tự không? Một hash map không thể trả lời "mẫu ngay trước thời điểm $t$"; một vector đã sắp xếp hoặc một `map` thì có thể.

### Iterator và sự vô hiệu hóa

Các category, từ yếu nhất đến mạnh nhất: input, forward, bidirectional, random access (và contiguous). `std::sort` cần random access, nên nó không sắp xếp được một `std::list` (hãy dùng `list::sort`). `std::lower_bound` chạy được trên forward iterator nhưng chỉ có $O(\log n)$ phép so sánh *và* số bước với random-access iterator.

**Quy tắc vô hiệu hóa** (nguồn gốc phổ biến nhất của undefined behavior): `vector::push_back` có thể cấp phát lại, vô hiệu hóa mọi iterator, con trỏ và reference; `vector::erase(it)` vô hiệu hóa `it` và mọi thứ sau nó; erase của `map`/`list` chỉ vô hiệu hóa phần tử bị xóa; rehash của `unordered_map` vô hiệu hóa iterator nhưng không vô hiệu hóa reference.

### Binary search

Với một range đã sắp xếp, `lower_bound(first, last, x)` trả về phần tử đầu tiên không nhỏ hơn $x$; `upper_bound` trả về phần tử đầu tiên lớn hơn $x$. Sau $k$ lần giảm nửa, cửa sổ còn $\lceil n/2^k\rceil$ phần tử, nên số phép so sánh tối đa là $\lceil\log_2(n+1)\rceil$. Với $n=360{,}000$ là 19; với $n=10^6$ là 20. Điều kiện tiên quyết là range được sắp xếp theo cùng thứ tự mà comparator dùng; nếu không, kết quả vô nghĩa.

Nội suy tuyến tính giữa các lân cận $(t_a,v_a)$ và $(t_b,v_b)$ với $t_a\le t\le t_b$:
$$v(t)=v_a+(v_b-v_a)\frac{t-t_a}{t_b-t_a}.$$

### Erase-remove và các thuật toán thông dụng

`std::remove_if(first, last, pred)` dồn các phần tử được giữ lên đầu và trả về điểm cuối logic mới; phần đuôi chứa các giá trị không xác định. Theo sau nó bằng `container.erase(new_end, container.end())`. `std::accumulate(first, last, init)` gộp bằng `+` (kiểu của `init` quyết định phép tính: `0` tích lũy bằng `int`, `0.0` bằng `double`). `std::nth_element(first, nth, last)` đặt vào vị trí `nth` phần tử sẽ nằm ở đó nếu sắp xếp, trong kỳ vọng $O(n)$, đủ cho trung vị (median) (sắp xếp tốn $O(n\log n)$).

### Tăng trưởng amortized

Nếu một vector nhân đôi dung lượng khi đầy, việc push $n$ phần tử copy tối đa $1+2+4+\dots+2^{k}<2n$ phần tử trong các lần cấp phát lại, nên chi phí amortized mỗi `push_back` là $O(1)$. Với hệ số tăng trưởng $g>1$ tổng tối đa là $\frac{g}{g-1}n$.

## Ví dụ có lời giải

Chuỗi $t=\{0,1,2,4\}$, $v=\{0,10,20,60\}$ lưu trong một vector đã sắp xếp. Tính $v(3)$.

1. `lower_bound` cho $t=3$: phần tử đầu tiên có $t_i\ge3$. Các phép so sánh: cửa sổ là 4 phần tử; thăm phần tử giữa chỉ số 2 ($t=2<3$), nên sang phải; cửa sổ là chỉ số 3 ($t=4\ge3$). Kết quả: iterator tới $(4,60)$.
2. Nó không phải `end()` cũng không phải `begin()`, và `it->t != 3`, nên ta nội suy với phần tử trước đó $(2,20)$.
3. $v(3)=20+(60-20)\frac{3-2}{4-2}=20+40\cdot0.5=40$.
4. Kiểm tra biên: $t=4.1$ cho `lower_bound == end()`, trả về "không có giá trị"; $t=-0.1$ cho `begin()` với $t_0=0>-0.1$, trả về "không có giá trị"; $t=1$ là trúng chính xác và trả về 10 mà không nội suy.
5. Đếm số mẫu trong $[1,2]$: `lower_bound(1)` trỏ tới chỉ số 1, `upper_bound(2)` trỏ tới chỉ số 3, hiệu $3-1=2$.
6. Erase-remove với ngưỡng 50: `remove_if(|v|>50)` giữ $(0,0),(1,10),(2,20)$ và trả về iterator tại chỉ số 3; `erase(index3, end)` thu nhỏ kích thước từ 4 xuống 3, số phần tử bị xóa $=4-3=1$.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: cppreference, Containers library overview)* Chọn container tốt nhất và biện minh trong một câu: (a) 100 lần đọc range gần nhất, loại bỏ cái cũ nhất; (b) tra cứu từ id frame camera (số nguyên) sang metadata của nó; (c) kết quả detection phải duy nhất và sắp xếp theo id; (d) một log IMU 30 phút được truy vấn "mẫu gần nhất với thời điểm $t$".
2. **(Dễ)** Dự đoán output:
   ```cpp
   std::vector<int> v{3, 1, 4, 1, 5, 9, 2, 6};
   auto e = std::remove(v.begin(), v.end(), 1);
   std::cout << (e - v.begin()) << ' ' << v.size();
   v.erase(e, v.end());
   std::cout << ' ' << v.size();
   ```
3. **(Dễ)** Một log 100 Hz dài một giờ có 360,000 mẫu. Quét tuyến tính cần bao nhiêu phép so sánh trong trường hợp xấu nhất và `lower_bound` cần bao nhiêu? Tỉ số là bao nhiêu?
4. **(Trung bình)** Tìm hai bug undefined-behavior trong hàm trợ giúp nội suy này, và sửa chúng.
   ```cpp
   double interp(const std::vector<Sample>& v, double t) {
     auto it = std::lower_bound(v.begin(), v.end(), t, [](const Sample& s, double x) { return s.t < x; });
     const Sample& a = *(it - 1);
     const Sample& b = *it;
     return a.v + (b.v - a.v) * (t - a.t) / (b.t - a.t);
   }
   ```
5. **(Trung bình)** *(Adapted from: cppreference, `std::vector::erase` and iterator invalidation)* Vòng lặp này xóa các giá trị đọc trên 50. Giải thích chính xác điều gì sai, rồi viết cách sửa hai lần (một lần dùng giá trị trả về của erase, một lần dùng erase-remove).
   ```cpp
   for (auto it = v.begin(); it != v.end(); ++it)
     if (it->v > 50) v.erase(it);
   ```
6. **(Trung bình)** Dự đoán output và nêu bài học thiết kế:
   ```cpp
   std::map<std::string, double> gains;
   double kp = gains["kp"];
   std::cout << kp << ' ' << gains.size();
   ```
7. **(Trung bình)** Một cửa sổ 1001 mẫu cần trung vị mỗi 10 ms. So sánh `std::sort` với `std::nth_element` về chi phí, nêu kết quả của `nth_element` trên `{7,1,5,3,9}` tại vị trí 2, và nói điều gì xảy ra với các phần tử còn lại.
8. **(Khó)** *(Adapted from: cppreference, `std::lower_bound` and `std::map::lower_bound`)* Bạn phải trả lời "giá trị tại thời điểm $t$" cho $10^6$ mẫu đã lưu với $2\times10^6$ truy vấn ngẫu nhiên. Thiết kế một benchmark công bằng cho `vector`+`lower_bound`, `map::lower_bound` và một `unordered_map` khóa theo chỉ số mẫu nguyên. Liệt kê năm thứ bạn kiểm soát (mức tối ưu hóa, warm-up, sinh truy vấn, việc dùng kết quả, chạy lặp lại) và dự đoán thứ tự cùng lý do `unordered_map` không so sánh trực tiếp được.
9. **(Khó)** Các mẫu đến muộn không theo thứ tự (khoảng 1% của 1,000 lần chèn mỗi giây vào một chuỗi $10^5$ mẫu, mỗi mẫu 16 byte). Ước lượng lượng dữ liệu bị di chuyển cho mỗi lần chèn giữa vào một `vector` và mỗi giây. Dùng `map` có hợp lý không? Bạn sẽ đo gì trước tiên?
10. **(Khó)** Suy dẫn cận chi phí amortized: với hệ số tăng trưởng $g$, chứng minh $n$ lần push gây tối đa $\frac{g}{g-1}n$ lần di chuyển phần tử trong các lần cấp phát lại, và tính nó cho $g=2$ và $g=1.5$. Vì sao các implementation không chọn $g$ rất lớn?
11. **(Mini-project)** Viết benchmark của bài tập 8 thành một chương trình, báo cáo nano giây mỗi truy vấn cho $N\in\{10^3,10^5,10^6\}$ trong một bảng, nêu các tỉ số, và giải thích bằng một đoạn về cache locality vì sao khoảng cách tăng theo $N$.

## Cài đặt tham khảo

Một chuỗi thời gian dạng vector đã sắp xếp với nội suy, truy vấn khoảng bao gồm hai đầu và erase-remove. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

```cpp
// CPP05 reference: a timestamped series on a sorted std::vector, queried with STL algorithms.
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <numeric>
#include <optional>
#include <vector>

struct Sample {
  double t;  // seconds
  double v;
};

class TimeSeries {
 public:
  // Appends only if t is finite and strictly later than the last sample.
  bool append(double t, double v) {
    if (!std::isfinite(t)) return false;
    if (!data_.empty() && !(t > data_.back().t)) return false;
    data_.push_back({t, v});
    return true;
  }
  std::size_t size() const { return data_.size(); }

  // Linearly interpolated value at time t, or nullopt outside [first.t, last.t].
  std::optional<double> at(double t) const {
    auto it = std::lower_bound(data_.begin(), data_.end(), t,
                               [](const Sample& s, double x) { return s.t < x; });
    if (it == data_.end()) return std::nullopt;       // after the last sample
    if (it->t == t) return it->v;                      // exact hit
    if (it == data_.begin()) return std::nullopt;     // before the first sample
    const Sample& a = *(it - 1);
    const Sample& b = *it;
    return a.v + (b.v - a.v) * (t - a.t) / (b.t - a.t);
  }

  // Number of samples with t0 <= t <= t1.
  std::size_t count_in(double t0, double t1) const {
    auto [lo, hi] = range(t0, t1);
    return static_cast<std::size_t>(hi - lo);
  }

  // Mean of the values with t0 <= t <= t1, or nullopt if there are none.
  std::optional<double> mean_in(double t0, double t1) const {
    auto [lo, hi] = range(t0, t1);
    if (lo >= hi) return std::nullopt;
    double sum = std::accumulate(lo, hi, 0.0, [](double acc, const Sample& s) { return acc + s.v; });
    return sum / static_cast<double>(hi - lo);
  }

  // Erase-remove: drops every sample with |v| > limit, returns how many were removed.
  std::size_t drop_above(double limit) {
    auto new_end = std::remove_if(data_.begin(), data_.end(),
                                  [limit](const Sample& s) { return std::fabs(s.v) > limit; });
    std::size_t removed = static_cast<std::size_t>(data_.end() - new_end);
    data_.erase(new_end, data_.end());
    return removed;
  }

 private:
  using It = std::vector<Sample>::const_iterator;
  std::pair<It, It> range(double t0, double t1) const {
    auto lo = std::lower_bound(data_.begin(), data_.end(), t0,
                               [](const Sample& s, double x) { return s.t < x; });
    auto hi = std::upper_bound(data_.begin(), data_.end(), t1,
                               [](double x, const Sample& s) { return x < s.t; });
    if (hi < lo) hi = lo;  // t1 < t0
    return {lo, hi};
  }
  std::vector<Sample> data_;
};

// ---- self-test
int main() {
  TimeSeries s;
  for (auto [t, v] : std::vector<Sample>{{0, 0}, {1, 10}, {2, 20}, {4, 60}}) s.append(t, v);
  if (s.at(3.0).value() != 40.0) return 1;
  if (s.at(-0.1) || s.at(4.1)) return 2;
  if (s.count_in(1.0, 2.0) != 2) return 3;
  if (s.mean_in(0.0, 2.0).value() != 10.0) return 4;
  if (s.append(4.0, 1.0)) return 5;
  if (s.drop_above(50.0) != 1 || s.size() != 3) return 6;
  std::cout << "CPP05 reference self-test passed\n";
}
```

## Thực hành độc lập

### Mục tiêu

Xây cấu trúc tra cứu có timestamp trên một `std::vector` đã sắp xếp, kiểm thử các trường hợp biên của nó, và so sánh với `std::map` bằng một benchmark do bạn viết.

### Chuẩn bị

`g++` hoặc `clang++` với C++17. Lưu starter và các test bên dưới nó thành `lab.cpp`, biên dịch bằng `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab`. Với benchmark ở nhiệm vụ cuối, biên dịch một file riêng với `-O2` và không có sanitizer.

### Nhiệm vụ

1. Cài đặt `append` và `size`. Làm cho timestamp bằng nhau và giảm dần thất bại.
2. Cài đặt `at` với `lower_bound`; xử lý trúng chính xác, `begin()` và `end()` trước khi nội suy.
3. Cài đặt `count_in` và `mean_in` với `lower_bound`/`upper_bound` và `accumulate`.
4. Cài đặt `drop_above` bằng erase-remove và trả về số phần tử đã xóa.
5. Viết một class thứ hai có cùng interface trên `std::map<double,double>` dùng `map::lower_bound`; chạy các test giống hệt trên nó.
6. Benchmark cả hai với $N=10^3,10^5,10^6$ và $2\times10^6$ truy vấn ngẫu nhiên ở `-O2`; in ns mỗi truy vấn và tỉ số.

### Code khởi đầu

```cpp
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <vector>

struct Sample {
  double t;  // seconds
  double v;
};

// Samples are kept sorted by strictly increasing t in a std::vector.
class TimeSeries {
 public:
  // Append only if t is finite and strictly later than the last sample; else return false, no change.
  bool append(double t, double v) { throw std::logic_error("NotImplemented"); }
  std::size_t size() const { throw std::logic_error("NotImplemented"); }

  // Linearly interpolated value at time t; nullopt if t < first.t or t > last.t.
  // Use std::lower_bound (O(log n)), not a linear scan. An exact timestamp returns its stored value.
  std::optional<double> at(double t) const { throw std::logic_error("NotImplemented"); }

  // Number of samples with t0 <= t <= t1 (inclusive both ends). 0 if t1 < t0.
  std::size_t count_in(double t0, double t1) const { throw std::logic_error("NotImplemented"); }

  // Mean of values with t0 <= t <= t1 (std::accumulate), nullopt if there are none.
  std::optional<double> mean_in(double t0, double t1) const { throw std::logic_error("NotImplemented"); }

  // Erase-remove idiom: delete every sample with |v| > limit; return the number removed.
  std::size_t drop_above(double limit) { throw std::logic_error("NotImplemented"); }
};
```

### Kiểm thử

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#include <iostream>
#include <random>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)

int main() {
  TimeSeries s;
  CHECK(s.size() == 0 && !s.at(0.0) && !s.mean_in(0, 1) && s.count_in(0, 1) == 0);  // empty series
  CHECK(s.append(0, 0) && s.append(1, 10) && s.append(2, 20) && s.append(4, 60));
  CHECK(s.size() == 4);
  // hand-computed interpolation: between (2,20) and (4,60) at t=3 -> 40; at t=2.5 -> 30
  CHECK(s.at(3.0).value() == 40.0);
  CHECK(std::fabs(s.at(2.5).value() - 30.0) < 1e-12);
  // exact timestamps and ends
  CHECK(s.at(0.0).value() == 0.0 && s.at(1.0).value() == 10.0 && s.at(4.0).value() == 60.0);
  CHECK(!s.at(-0.1) && !s.at(4.1));
  // append rules
  CHECK(!s.append(4.0, 1.0) && !s.append(3.0, 1.0) && !s.append(NAN, 1.0) && s.size() == 4);
  // ranges (inclusive)
  CHECK(s.count_in(1.0, 2.0) == 2 && s.count_in(1.5, 3.9) == 1 && s.count_in(5, 6) == 0 && s.count_in(2, 1) == 0);
  CHECK(s.mean_in(0.0, 2.0).value() == 10.0 && !s.mean_in(2.5, 3.5));
  // erase-remove
  CHECK(s.drop_above(50.0) == 1 && s.size() == 3 && !s.at(4.0));
  CHECK(s.drop_above(1000.0) == 0);
  // property: interpolation at every stored time equals the stored value, and is monotone for monotone data
  TimeSeries r;
  std::mt19937 g(7);
  std::uniform_real_distribution<double> dt(0.01, 1.0);
  double t = 0, v = 0;
  std::vector<Sample> ref;
  for (int i = 0; i < 500; ++i) { t += dt(g); v += dt(g); CHECK(r.append(t, v)); ref.push_back({t, v}); }
  for (const Sample& p : ref) CHECK(r.at(p.t).value() == p.v);
  double prev = -1;
  for (double q = ref.front().t; q <= ref.back().t; q += 0.37) { double x = r.at(q).value(); CHECK(x >= prev); prev = x; }
  CHECK(r.count_in(ref.front().t, ref.back().t) == 500);
  std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi

```
all tests passed
```

Với benchmark, hãy kỳ vọng `vector` nhanh hơn `map` và khoảng cách tăng theo $N$ (trên một máy thử, các tỉ số khoảng 1.0 ở $10^3$, 1.7 ở $10^5$ và 3.6 ở $10^6$; số của bạn sẽ khác).

### Thử thách mở rộng

Thêm `insert_sorted(t, v)` chấp nhận các mẫu đến muộn bằng `upper_bound` và `vector::insert`, và đo chi phí như một hàm của khoảng cách từ vị trí chèn đến cuối. Sau đó so sánh với cài đặt `std::map` cho 1% mẫu đến muộn.

### Thực hành với thư viện

Chỉ dùng standard library (`<map>`, `<chrono>`, `<random>`) cho nhiệm vụ 5 và 6. Dán đoạn này *sau* `TimeSeries` đã hoàn thiện của bạn (nó có `main` riêng, nên bỏ `main` của phần test) và biên dịch riêng bằng `g++ -std=c++17 -O2 -Wall -Wextra` (không dùng sanitizer khi đo thời gian).

```cpp
#include <cassert>
#include <chrono>
#include <iostream>
#include <map>
#include <random>

// Same interface on std::map, for the cross-check and the benchmark (task 5).
class MapSeries {
 public:
  bool append(double t, double v) {
    if (!std::isfinite(t) || (!m_.empty() && !(t > m_.rbegin()->first))) return false;
    m_.emplace_hint(m_.end(), t, v);
    return true;
  }
  std::optional<double> at(double t) const {
    auto it = m_.lower_bound(t);
    if (it == m_.end()) return std::nullopt;
    if (it->first == t) return it->second;
    if (it == m_.begin()) return std::nullopt;
    auto a = std::prev(it);
    return a->second + (it->second - a->second) * (t - a->first) / (it->first - a->first);
  }
 private:
  std::map<double, double> m_;
};

template <class S>
double ns_per_query(const S& s, const std::vector<double>& q, double& sink) {
  using clk = std::chrono::steady_clock;
  double best = 1e300;
  for (int rep = 0; rep < 5; ++rep) {                         // repeats: keep the best (least noisy)
    auto t0 = clk::now();
    for (double x : q) sink += s.at(x).value_or(0.0);         // consume results
    best = std::min(best, std::chrono::duration<double, std::nano>(clk::now() - t0).count() / q.size());
  }
  return best;
}

int main() {
  std::mt19937 g(1);
  for (std::size_t n : {1000u, 100000u, 1000000u}) {
    TimeSeries vs; MapSeries ms;
    for (std::size_t i = 0; i < n; ++i) { vs.append(0.01 * i, std::sin(0.01 * i)); ms.append(0.01 * i, std::sin(0.01 * i)); }
    std::uniform_real_distribution<double> u(0.0, 0.01 * (n - 1));
    std::vector<double> q(2000000); for (double& x : q) x = u(g);
    for (int i = 0; i < 1000; ++i) assert(std::fabs(vs.at(q[i]).value() - ms.at(q[i]).value()) < 1e-12);  // same answers
    double sink = 0;
    double a = ns_per_query(vs, q, sink), b = ns_per_query(ms, q, sink);
    std::cout << "N=" << n << "  vector " << a << " ns  map " << b << " ns  ratio " << b / a << "  check " << sink << "\n";
  }
}
```

Trên một máy thử, output là các tỉ số khoảng 1.5, 2.3 và 4.2 cho $N=10^3, 10^5, 10^6$ (vector 64, 162, 248 ns mỗi truy vấn; map 94, 374, 1032 ns); của bạn sẽ khác, nhưng tỉ số nên tăng theo $N$. `assert` kiểm tra rằng cả hai cấu trúc trả về cùng giá trị nội suy. Câu hỏi: vì sao thời gian của vector vẫn tăng theo $N$? Điều gì xảy ra với tỉ số nếu các truy vấn được sắp xếp thay vì ngẫu nhiên?

## Kiểm chứng

- Property test: với mọi $t_i$ đã lưu, `at(t_i)` phải bằng đúng $v_i$; với dữ liệu đơn điệu, phép nội suy phải đơn điệu.
- Đối chiếu với một oracle chậm: một cài đặt quét tuyến tính trên các truy vấn ngẫu nhiên phải cho đáp án y hệt.
- Các trường hợp biên cần test mọi lần: container rỗng, một phần tử, truy vấn trước phần tử đầu và sau phần tử cuối, key trùng, truy vấn đúng trên một key.
- Chạy dưới `-fsanitize=address,undefined` (và `-D_GLIBCXX_DEBUG` cho checked iterator) để bắt iterator ngoài phạm vi và iterator bị vô hiệu hóa.
- Vệ sinh benchmark: `-O2`, một lượt warm-up, truy vấn sinh trước khi đo, kết quả được dùng để optimizer không xóa mất vòng lặp, chạy lặp nhiều lần, báo cáo median.

## Lỗi thường gặp

| Sai lầm | Triệu chứng |
|---|---|
| `lower_bound` trên dữ liệu chưa sắp xếp | chỉ số sai một cách lặng lẽ, không có lỗi |
| Dereference `end()` hoặc `begin()-1` | crash hoặc giá trị rác (undefined behavior) |
| `erase` bên trong range-for hoặc vòng lặp iterator | bỏ sót phần tử hoặc crash; dùng `it = v.erase(it)` hoặc erase-remove |
| `remove_if` mà không có `erase` theo sau | container giữ kích thước cũ, phần đuôi chứa giá trị không xác định |
| `std::accumulate(first, last, 0)` trên double | tích lũy số nguyên: `{0.5, 0.5, 0.5}` có tổng 0 |
| `map::operator[]` trên key thiếu | chèn một giá trị mặc định (bài tập 6); dùng `find` hoặc `at` để đọc |
| Giữ một reference vào vector qua `push_back` | treo sau khi cấp phát lại |
| Benchmark bỏ kết quả | optimizer xóa công việc và báo khoảng 0 ns |
| Comparator không phải strict weak ordering (`<=`) | undefined behavior trong `sort`, `set` |

## Phương án khác và đánh đổi

- **Vector đã sắp xếp so với `map`.** Với dữ liệu xây một lần, truy vấn nhiều lần, vector đã sắp xếp thắng về tốc độ và bộ nhớ; nếu việc chèn giữa chiếm ưu thế, `map` tránh được việc dịch chuyển $O(n)$. Với vài trăm phần tử, cái nào cũng ổn và vector đơn giản hơn.
- **`unordered_map` so với các container có thứ tự.** Băm cho tra cứu chính xác kỳ vọng $O(1)$, nhưng không làm được truy vấn khoảng hoặc láng giềng gần nhất và có hành vi trường hợp xấu nhất tệ hơn với hàm băm kém.
- **`deque` so với `vector` cho FIFO.** `deque` pop từ đầu trong $O(1)$; với `vector`, pop phần tử đầu là $O(n)$ trừ khi bạn giữ một chỉ số head (một ring buffer).
- **Thuật toán so với vòng lặp viết tay.** Các thuật toán `std::` nêu rõ ý định (`count_if`, `any_of`) và đã được kiểm thử kỹ; vòng lặp viết tay vẫn ổn khi thoát sớm hoặc nhiều đầu ra làm dạng thuật toán trở nên khó hiểu.
- **Ranges và execution policy (C++20/17).** `std::ranges` cải thiện khả năng đọc và `std::execution::par` có thể song song hóa một số thuật toán, với cái giá là sự hỗ trợ của compiler và các quy tắc data race của CPP10.

## Vận dụng và ghi nhớ

Cùng các ý tưởng này xuất hiện trong NumPy (`np.searchsorted` là `lower_bound`, boolean mask là `remove_if`), trong buffer `tf2` của ROS 2 (cache có thứ tự thời gian với nội suy giữa các transform), và trong index của cơ sở dữ liệu (B-tree cho truy vấn khoảng, hash index cho so sánh bằng). Để ghi nhớ: viết lại từ trí nhớ bảng độ phức tạp của container sau ba ngày, rồi liệt kê cho dự án gần nhất của bạn container nào bạn đã dùng cho từng tập dữ liệu và thao tác chiếm ưu thế có khớp không. CPP09 tiếp nối bằng cách giải thích *vì sao* bố cục liên tục thắng trong thực tế.

## Đáp án bài tập

1. (a) `std::deque` (hoặc một ring buffer cố định): push back và pop front trong $O(1)$. (b) `std::unordered_map<int, Meta>`: tra cứu chính xác theo id nguyên, không cần thứ tự. (c) `std::set<int>` (hoặc `map` nếu có kèm payload): duy nhất và có thứ tự. (d) Một `std::vector` các mẫu sắp xếp theo thời gian với `lower_bound` (xây một lần, truy vấn nhiều); một `map` cũng được, nhưng chậm hơn và dùng nhiều bộ nhớ hơn.
2. `6 8 6`. `remove` dồn sáu phần tử được giữ `{3,4,5,9,2,6}` lên đầu và trả về iterator tại chỉ số 6, nhưng kích thước vẫn là 8 cho đến khi `erase` làm nó thành 6.
3. Tuyến tính: 360,000 phép so sánh. Nhị phân: $\lceil\log_2 360{,}001\rceil=19$. Tỉ số $\approx 18{,}900$.
4. Bug 1: nếu `it == v.begin()` (truy vấn trước mẫu đầu) thì `it - 1` nằm trước phần đầu. Bug 2: nếu `it == v.end()` (truy vấn sau mẫu cuối) thì `*it` dereference `end()`. Ngoài ra, chia cho không không thể xảy ra nếu timestamp tăng nghiêm ngặt, nhưng một lần trúng chính xác với $t=t_b$ nên trả về trực tiếp. Cách sửa: kiểm tra `it == end` trước, rồi đẳng thức chính xác, rồi `it == begin`, và chỉ sau đó mới nội suy (xem `at` tham khảo).
5. `erase(it)` vô hiệu hóa `it` (và mọi iterator sau đó), nên `++it` ở lượt lặp kế là undefined behavior; ngay cả khi có vẻ chạy được, nó bỏ sót phần tử vừa trượt vào ô bị xóa. Cách sửa 1: `for (auto it = v.begin(); it != v.end();) { if (it->v > 50) it = v.erase(it); else ++it; }`. Cách sửa 2: `v.erase(std::remove_if(v.begin(), v.end(), [](const Sample& s){ return s.v > 50; }), v.end());` cũng là $O(n)$ thay vì $O(n^2)$.
6. Output `0 1`. `operator[]` default-construct và chèn key còn thiếu `"kp"`, nên một lỗi gõ tên tham số lặng lẽ trở thành gain 0 và map phình ra. Dùng `find`/`at` (sẽ throw) để đọc, và chỉ dùng `[]` khi thật sự muốn chèn.
7. `std::sort` là $O(n\log n)$ (khoảng $1001\cdot10\approx10^4$ phép so sánh), `nth_element` kỳ vọng $O(n)$ (vài nghìn). Trung vị của `{7,1,5,3,9}` nằm ở chỉ số 2 và bằng 5. Sau `nth_element` các phần tử trước đều $\le5$ và các phần tử sau đều $\ge5$, theo thứ tự không xác định; vector *không* được sắp xếp.
8. Kiểm soát: `-O2` cho tất cả; một lượt warm-up (page-in, branch predictor, cache); cùng các truy vấn ngẫu nhiên sinh sẵn cho mỗi cấu trúc; cộng dồn kết quả vào một biến được in ra để vòng lặp không bị loại bỏ; chạy lặp nhiều lần lấy median. Thứ tự kỳ vọng cho truy vấn thời gian gần nhất: `vector` nhanh nhất, `map` chậm hơn (đuổi theo con trỏ, cache miss); `unordered_map` hoàn toàn không trả lời được truy vấn thời gian gần nhất, chỉ trả lời key chính xác, nên so sánh nó chỉ hợp lệ cho tra cứu chỉ số chính xác, nơi nó nhanh nhưng trả lời một câu hỏi khác.
9. 1% của 1000 mỗi giây là 10 lần chèn muộn mỗi giây. Một lần chèn giữa dịch chuyển trung bình $n/2=50{,}000$ phần tử $\times16$ B $=800$ kB; 10 lần mỗi giây là 8 MB/s, không đáng kể. Dùng `map` là không hợp lý; hãy đo phân phối thực tế của độ trễ (các mẫu muộn chủ yếu gần cuối, nên việc dịch chuyển còn nhỏ hơn) và ngân sách độ trễ truy vấn trước khi thay đổi bất cứ thứ gì.
10. Việc cấp phát lại xảy ra khi kích thước đạt $c, gc, g^2c,\dots$ và mỗi lần copy kích thước hiện tại, nên tổng là $c+gc+\dots+g^{k}c$ với $g^{k}c\le n$. Tổng cấp số nhân tối đa là $n\cdot\frac{1}{1-1/g}=\frac{g}{g-1}n$. Với $g=2$: $2n$; với $g=1.5$: $3n$. $g$ rất lớn lãng phí bộ nhớ (tới $(g-1)/g$ dung lượng không dùng) và allocator có thể không tìm được khối đủ lớn; giá trị thường dùng là từ 1.5 đến 2.
11. Một câu trả lời tốt có: một bảng với ba kích thước; vector nhanh hơn map theo một tỉ số tăng dần (trong một lần chạy là 1.0, 1.7, 3.6); giải thích: binary search của vector chạm vài cache line và prefetch hoạt động, trong khi cây thăm các node rải rác trên heap; ở $10^6$ phần tử cây (khoảng 48 B/node) vượt quá cache và mỗi bước nhảy có thể là một cache miss; và một lưu ý về máy và về việc chỉ chạy một lần.

## Đọc thêm

- [cppreference: Containers library](https://en.cppreference.com/w/cpp/container) - bảng container đầy đủ với đảm bảo độ phức tạp và quy tắc vô hiệu hóa.
- [cppreference: Algorithms library](https://en.cppreference.com/w/cpp/algorithm) - mọi thuật toán với điều kiện tiên quyết, độ phức tạp và ví dụ.
- [LearnCpp](https://www.learncpp.com/) - các chương về container, iterator và thuật toán kèm quiz.

**Thực hành thêm:** các quiz ở [LearnCpp: STL containers overview](https://www.learncpp.com/cpp-tutorial/stl-containers-overview/), [iterators overview](https://www.learncpp.com/cpp-tutorial/stl-iterators-overview/) và [algorithms overview](https://www.learncpp.com/cpp-tutorial/stl-algorithms-overview/) (đáp án hiện trên mỗi trang), và các ví dụ chạy được trên cppreference cho [`std::lower_bound`](https://en.cppreference.com/w/cpp/algorithm/lower_bound) và [`std::remove`/`remove_if`](https://en.cppreference.com/w/cpp/algorithm/remove) (sửa chúng để dự đoán output), cùng [bảng vô hiệu hóa iterator](https://en.cppreference.com/w/cpp/container#Iterator_invalidation).
