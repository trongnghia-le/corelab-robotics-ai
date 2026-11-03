---
{"title": "Độ phức tạp và hiệu năng: tiệm cận, cache locality và profiling", "summary": "Kết hợp lập luận big-O với mô hình chi phí của hệ thống phân cấp bộ nhớ, đo đạc trung thực, và profile trước khi tối ưu.", "objectives": ["Suy ra và so sánh chi phí tiệm cận, và ước lượng số mũ thực nghiệm từ các phép đo thời gian.", "Giải thích cache line, spatial locality và vì sao vector thắng danh sách liên kết bằng con trỏ khi big-O bằng nhau.", "Thiết kế một benchmark tránh được những cái bẫy đo đạc thường gặp.", "Dùng profiler và định luật Amdahl để quyết định cái gì đáng tối ưu."]}
---
## Vì sao điều này quan trọng

Robot có deadline: một vòng điều khiển 1 kHz chỉ còn 1 ms cho mỗi lần lặp, một pipeline camera 30 Hz khoảng 33 ms mỗi frame, và trễ deadline nghĩa là lag, jitter hoặc mất ổn định. Vì vậy công việc hiệu năng đặt ra hai câu hỏi: *chi phí tăng thế nào theo kích thước bài toán* (độ phức tạp) và *một bước thực sự tốn bao nhiêu trên phần cứng thật* (hành vi bộ nhớ). Chỉ riêng big-O là gây hiểu lầm: danh sách liên kết và vector đều duyệt $n$ phần tử trong $O(n)$, vậy mà trên benchmark của bài này, danh sách chậm hơn khoảng 150 lần mỗi phần tử khi dữ liệu không còn vừa trong cache. Và tối ưu sai hàm là sự lãng phí công sức phổ biến nhất: nếu một hàm chiếm 5% thời gian chạy, ngay cả tăng tốc vô hạn cũng chỉ lợi tối đa 5%. Bài này cho bạn mô hình chi phí, kỷ luật đo đạc và quy trình profiling để đưa ra quyết định hiệu năng dựa trên bằng chứng.

## Trực giác

Tính toán thì rẻ, lấy dữ liệu thì đắt. Một CPU hiện đại làm được vài phép tính số học mỗi nano giây, nhưng một lần đọc trượt mọi cache sẽ đi đến bộ nhớ chính và tốn cỡ 100 ns, tương đương hàng trăm phép tính. Bộ nhớ vì vậy là một hệ phân cấp: thanh ghi, các cache nhỏ và nhanh (L1, L2, L3), rồi DRAM. Dữ liệu di chuyển giữa các tầng theo từng khối gọi là **cache line** (thường 64 byte). Nếu bạn đọc một `double` tại địa chỉ $a$, phần cứng nạp cả line 64 byte, nên 7 double tiếp theo là miễn phí. Duyệt một vector dùng mọi byte của mọi line nó nạp và để **prefetcher** của phần cứng đoán line tiếp theo. Theo con trỏ tới các node rải rác trên heap nạp một line chỉ để dùng 16 byte và địa chỉ kế tiếp không biết cho đến khi lần nạp hiện tại xong.

Vậy có hai thang đo: **tiệm cận** (bao nhiêu bước, khi $n$ tăng) và **hệ số hằng** (mỗi bước đắt thế nào, phụ thuộc vào locality). Một kỹ sư giỏi lập luận về cả hai, rồi đo.

![Nạp cache line: truy cập tuần tự dùng cả 8 double trong một line 64 byte, đuổi theo con trỏ chạm một node mỗi line; bên dưới, đồ thị log của ns mỗi phần tử theo n cho vector và danh sách đã xáo trộn](/lesson-figures/CPP09.svg)

*Truy cập tuần tự chia đều mỗi lần nạp cache line cho tám double; đuổi theo con trỏ trả trọn độ trễ bộ nhớ cho mỗi node một khi dữ liệu vượt quá các cache.*

## Lý thuyết và suy dẫn

### Chi phí tiệm cận

$f(n)=O(g(n))$ nghĩa là $f(n)\le c\,g(n)$ với một hằng số $c$ nào đó và mọi $n$ đủ lớn. Các tốc độ tăng thông dụng, theo thứ tự: $1,\ \log n,\ n,\ n\log n,\ n^2,\ n^3,\ 2^n$. Với $n=10^5$ điểm scan: so sánh từng cặp thực hiện $n^2=10^{10}$ phép toán, một lần sắp xếp hay dựng k-d tree thực hiện $n\log_2n\approx1.66\times10^6$, tỉ số khoảng 6000. Quy tắc: bỏ hằng số và các số hạng bậc thấp; vòng lặp lồng nhau nhân với nhau; các bước tuần tự cộng với nhau; vòng lặp giảm nửa phạm vi là $\log n$. Amortized $O(1)$ (`push_back` của vector) nghĩa là trung bình trên một chuỗi là hằng số dù từng bước đơn lẻ có thể tốn $O(n)$.

**Số mũ thực nghiệm.** Nếu $t(n)\approx c\,n^p$, thì $\ln t=\ln c+p\ln n$, một đường thẳng trên đồ thị log-log với độ dốc $p$. Khớp độ dốc bằng bình phương tối thiểu:
$$p=\frac{\sum_i(\ln n_i-\overline{\ln n})(\ln t_i-\overline{\ln t})}{\sum_i(\ln n_i-\overline{\ln n})^2}.$$
Nhân đôi $n$ nhân thời gian với $2^p$: khoảng $2$ cho tuyến tính, $4$ cho bậc hai. Dùng ít nhất bốn kích thước trải rộng hệ số 8 trở lên, và nhớ rằng hiệu ứng cache làm cong đường thẳng khi dữ liệu vượt qua một kích thước cache.

### Mô hình chi phí của hệ phân cấp bộ nhớ

Bậc độ lớn sơ bộ (thay đổi theo CPU): L1 hit khoảng 1 ns (4 chu kỳ), L2 khoảng 4 ns, L3 khoảng 15-40 ns, DRAM khoảng 80-100 ns. Băng thông tuần tự khoảng 10-30 GB/s, tức $\approx0.3$-$0.8$ ns mỗi phần tử 8 byte, tốc độ mà phép cộng vector đạt được. Một vòng lặp đuổi theo con trỏ bị *giới hạn bởi độ trễ*: mỗi lần nạp phụ thuộc vào lần trước, nên một cache miss phải trả đủ: 140 ns mỗi node trong benchmark của ta ở 4 triệu node, phù hợp với độ trễ DRAM cộng TLB miss.

**Cache line.** Với một mảng phần tử $b$ byte đọc theo bước nhảy (stride) $s$ (tính theo phần tử), phần tử $i$ nằm trong line $\lfloor ib/64\rfloor$. Đọc tuần tự $n$ phần tử chạm $\lceil nb/64\rceil$ line. Một stride từ $64/b$ phần tử trở lên chạm một line mới ở *mỗi* lần đọc. Ví dụ: 1000 float ($b=4$) đọc tuần tự chạm $\lceil4000/64\rceil=63$ line; đọc với stride 16 cũng chạm 63 line, với số phần tử ít hơn 16 lần. Thời gian đi theo số line, không theo số phần tử, một khi dữ liệu nằm ngoài cache.

**Bố cục.** Mảng các cấu trúc (AoS) xen kẽ các field, nên đọc một field kéo theo các field khác qua cache; cấu trúc của các mảng (SoA) lưu mỗi field liên tục. Với $N=10^6$ điểm 16 byte (x, y, z, intensity), cộng chỉ `z` truyền 16 MB với AoS nhưng 4 MB với SoA.

**Duyệt hai chiều.** Một ma trận $N\times N$ double theo hàng (row-major) được duyệt từng hàng với một miss mỗi 8 phần tử; duyệt từng cột thì mỗi truy cập là một line mới (stride $8N$ byte).

### Đo đạc trung thực

1. Bản build tối ưu hóa (`-O2` hoặc `-O3`), không có sanitizer, assertion của bản release như trong production.
2. Làm cho kết quả quan sát được (lưu vào một `volatile` hoặc in ra) để optimizer không thể loại bỏ công việc.
3. Warm up, lặp nhiều lần, báo cáo **median** và độ phân tán; giá trị nhỏ nhất cũng hữu ích như cận dưới. Không bao giờ dùng một lần chạy.
4. Chỉ đo thao tác: cấp phát và khởi tạo bên ngoài vùng được đo.
5. Cố định tần số CPU và đóng các chương trình khác nếu có thể; ghi rõ máy.
6. Thay đổi $n$ qua các kích thước cache (vài KB, hàng trăm KB, hàng chục MB) và báo cáo ns mỗi phần tử, không phải tổng thời gian.
7. Kiểm tra tính đúng của kết quả (tổng bằng tham chiếu) để bạn không đo một bug.

### Profiling và định luật Amdahl

Profiler lấy mẫu xem chương trình tốn thời gian ở đâu: `perf record -g ./prog` rồi `perf report`, hoặc `gprof`. Tối ưu phần đóng góp lớn nhất trước. Nếu một phần chiếm tỉ lệ $f$ tổng thời gian và được làm nhanh hơn $s$ lần, mức tăng tốc tổng thể là
$$S=\frac{1}{(1-f)+f/s}.$$
Với $f=0.3$ và $s=10$: $S=1/(0.7+0.03)=1.37$. Ngay cả $s\to\infty$ cũng chỉ cho $1/0.7=1.43$. Hãy profile trước; nút thắt cổ chai hiếm khi ở chỗ trực giác bảo.

## Ví dụ có lời giải

**Bài toán.** Ước lượng chi phí cộng $n=4\times10^6$ double lưu (a) trong một `std::vector` và (b) trong một danh sách liên kết có các node được thăm theo thứ tự xáo trộn, dùng bảng đo được (máy này, `-O2`):

| $n$ | vector (ns/phần tử) | danh sách xáo trộn (ns/phần tử) |
|---|---|---|
| 1,000 | 0.76 | 1.88 |
| 100,000 | 0.77 | 14.4 |
| 4,000,000 | 0.92 | 140 |

1. **Dung lượng chiếm.** Một `Node` là 16 byte (một `double` và một con trỏ), nên 4 triệu node chiếm 64 MB; vector giữ 32 MB. Cả hai đều vượt quá cache L2 điển hình (hàng trăm KB đến vài MB) và có lẽ cả L3.
2. **Vector.** Thời gian mỗi phần tử hầu như không đổi: 0.76 đến 0.92 ns. Vòng lặp truyền 8 byte mỗi phần tử, nên $0.92\ \text{ns}$ mỗi phần tử khoảng $8.7$ GB/s, một tốc độ streaming điển hình, và prefetcher che giấu độ trễ.
3. **Danh sách.** Ở $n=1000$, 16 KB vừa trong L1, nên ngay cả truy cập xáo trộn cũng rẻ (1.88 ns, bị giới hạn bởi các lần nạp phụ thuộc). Ở $10^5$ (1.6 MB) nó tràn khỏi L1/L2 và tốn 14.4 ns. Ở $4\times10^6$ gần như mọi bước nhảy đều miss xuống DRAM: 140 ns, gần với độ trễ DRAM. Mỗi node là một lần nạp line riêng: trong 64 byte nạp vào chỉ 16 được dùng.
4. **Tỉ số.** $140/0.92\approx152$ lần chậm hơn mỗi phần tử, với cùng $O(n)$.
5. **Số mũ thực nghiệm.** Tổng thời gian $t=n\cdot(\text{ns mỗi phần tử})$. Giữa $n=10^5$ và $4\times10^6$ thời gian của danh sách tăng $\frac{4\times10^6\cdot140}{10^5\cdot14.4}\approx389$ khi kích thước tăng 40 lần, số mũ $\ln389/\ln40\approx1.62$: không phải hành vi $O(n)$ với hệ số hằng, vì chế độ cache đã đổi. Vector cho $\ln\frac{4\times10^6\cdot0.92}{10^5\cdot0.77}/\ln40\approx1.05$, về cơ bản là tuyến tính.
6. **Kiểm tra Amdahl.** Nếu việc duyệt danh sách chiếm 30% một frame và vector làm nó nhanh hơn 100 lần: $S=1/(0.7+0.003)=1.42$, nên những thứ khác trong frame mới là điều quan trọng.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: MIT 6.006, asymptotic analysis problems)* Cho lớp tăng trưởng của từng trường hợp: (a) so sánh mọi cặp trong $n$ điểm lidar; (b) binary search trong một mảng $n$ timestamp đã sắp xếp; (c) `push_back` $n$ phần tử vào một `vector`; (d) sắp xếp $n$ điểm bằng `std::sort`. Với $n=10^5$ hãy so sánh bằng số số phép toán của (a) và (d).
2. **(Dễ)** *(Adapted from: Drepper, What Every Programmer Should Know About Memory, cache line discussion)* Một mảng 1000 `float` được đọc tuần tự, rồi với stride 16 phần tử. Mỗi lượt chạm bao nhiêu cache line 64 byte? Điều đó có nghĩa gì cho thời gian chạy khi mảng không nằm trong cache?
3. **(Dễ)** *(Adapted from: Bryant and O'Hallaron, CS:APP, Amdahl's law)* 30% thời gian của một frame là resize ảnh. Bạn làm nó nhanh hơn 10 lần. Mức tăng tốc tổng thể là bao nhiêu, và mức tốt nhất có thể nếu resize là miễn phí?
4. **(Trung bình)** Từ bảng trong ví dụ có lời giải, giải thích trong bốn câu vì sao danh sách xáo trộn chậm hơn 152 lần ở $n=4\times10^6$ dù cả hai cách duyệt đều là $O(n)$. Nhắc đến cache line, prefetching và độ trễ, và nói số liệu nào ủng hộ từng nhận định.
5. **(Trung bình)** Tìm ít nhất bốn khiếm khuyết trong benchmark này và sửa chúng.
   ```cpp
   auto t0 = std::chrono::steady_clock::now();
   std::vector<double> v(1000000, 1.0);
   double s = 0;
   for (double x : v) s += x;
   auto t1 = std::chrono::steady_clock::now();
   std::cout << std::chrono::duration<double>(t1 - t0).count() << " s\n";
   ```
   (biên dịch bằng `g++ -O0`; chạy một lần.)
6. **(Trung bình)** *(Adapted from: CS:APP, matrix traversal and locality)* Một ma trận double $4096\times4096$ theo hàng được cộng theo từng hàng và theo từng cột. Nó chứa bao nhiêu cache line, mỗi thứ tự gây ra bao nhiêu lần nạp line (giả sử ma trận lớn hơn nhiều so với cache và một line bị loại bỏ trước khi được dùng lại), và tỉ số nạp là bao nhiêu?
7. **(Trung bình)** Một đám mây điểm có $10^6$ điểm `{float x, y, z, intensity}`. Bạn chỉ cần trung bình của `z`. So sánh số byte được truyền từ bộ nhớ với một `std::vector<Point>` AoS và với SoA `std::vector<float> z`. Khi nào sự khác biệt thôi quan trọng?
8. **(Khó)** Bạn đo một hàm tại $n=1000, 2000, 4000, 8000$: $2.0, 8.1, 32.5, 129$ ms. Ước lượng số mũ (bằng tay với các tỉ số, rồi với công thức bình phương tối thiểu), nêu độ phức tạp có khả năng, và dự đoán thời gian tại $n=10^5$. Nêu hai lý do dự đoán có thể sai.
9. **(Khó)** Một profile của một perception node cho thấy (số liệu minh họa): tìm kiếm láng giềng gần nhất 62%, serialization point cloud 18%, voxel filter 12%, còn lại 8%. Tính mức tăng tốc tổng thể tối đa cho (i) làm tìm kiếm nhanh hơn 5 lần, (ii) làm serialization nhanh hơn 100 lần. Làm cái nào trước? Bạn sẽ kiểm tra gì trước khi viết code?
10. **(Khó)** Một particle filter có 5000 hạt `{x, y, theta, weight}` mỗi hạt 32 byte (có đệm). Chuẩn hóa trọng số chỉ đọc `weight`. SoA có đáng không? Tính dung lượng chiếm, bàn về kích thước cache, và mô tả benchmark sẽ quyết định, kể cả cách bạn thay đổi $N$.
11. **(Mini-project)** Chạy benchmark của bài này trên máy bạn cho $n=10^3,10^5,4\times10^6$; thêm một phép cộng có stride (stride 8 double) làm cột thứ tư; khớp `loglog_slope` giữa hai kích thước lớn nhất cho từng cột; báo cáo kích thước cache của bạn (`lscpu`) và giải thích mỗi đường cong bị bẻ cong ở đâu.

## Cài đặt tham khảo

Phần 1 là thư viện mà lab yêu cầu bạn viết (thống kê, khớp số mũ, mô hình cache-line, danh sách cấp phát theo pool). Phần 2 là chương trình benchmark; biên dịch riêng với `-O2` và không có sanitizer.

```cpp
// CPP09 reference: measurement helpers and a pointer-chasing list for locality experiments.
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <numeric>
#include <set>
#include <stdexcept>
#include <vector>

// Median of the samples (mean of the two middle values when the count is even).
double median(std::vector<double> v) {
  if (v.empty()) throw std::invalid_argument("median of empty sample");
  std::sort(v.begin(), v.end());
  const std::size_t n = v.size();
  return n % 2 ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]);
}

// Least-squares slope of ln(y) against ln(x): the empirical exponent p in y ~ x^p.
double loglog_slope(const std::vector<double>& x, const std::vector<double>& y) {
  if (x.size() != y.size() || x.size() < 2) throw std::invalid_argument("need >= 2 matching points");
  std::vector<double> lx, ly;
  for (std::size_t i = 0; i < x.size(); ++i) {
    if (!(x[i] > 0.0) || !(y[i] > 0.0)) throw std::invalid_argument("values must be positive");
    lx.push_back(std::log(x[i]));
    ly.push_back(std::log(y[i]));
  }
  const double n = static_cast<double>(lx.size());
  const double mx = std::accumulate(lx.begin(), lx.end(), 0.0) / n;
  const double my = std::accumulate(ly.begin(), ly.end(), 0.0) / n;
  double sxy = 0.0, sxx = 0.0;
  for (std::size_t i = 0; i < lx.size(); ++i) {
    sxy += (lx[i] - mx) * (ly[i] - my);
    sxx += (lx[i] - mx) * (lx[i] - mx);
  }
  if (sxx == 0.0) throw std::invalid_argument("x values must differ");
  return sxy / sxx;
}

// Number of distinct cache lines touched when reading elements 0, s, 2s, ... (< n) of an array of
// n elements of elem_bytes each, stored from a line-aligned address.
std::size_t lines_touched(std::size_t n, std::size_t elem_bytes, std::size_t stride_elems,
                          std::size_t line_bytes = 64) {
  if (elem_bytes == 0 || stride_elems == 0 || line_bytes == 0) throw std::invalid_argument("zero argument");
  std::set<std::size_t> lines;
  for (std::size_t i = 0; i < n; i += stride_elems) lines.insert(i * elem_bytes / line_bytes);
  return lines.size();
}

struct Node {
  double value = 0.0;
  Node* next = nullptr;
};

// A singly linked list whose nodes live in one pool, linked in the order given by `order`
// (order[k] is the pool index of the k-th node in traversal order). order must be a permutation.
class PoolList {
 public:
  PoolList(const std::vector<double>& values, const std::vector<std::size_t>& order)
      : pool_(values.size()) {
    if (order.size() != values.size()) throw std::invalid_argument("order size mismatch");
    std::vector<bool> seen(values.size(), false);
    for (std::size_t idx : order) {
      if (idx >= values.size() || seen[idx]) throw std::invalid_argument("order is not a permutation");
      seen[idx] = true;
    }
    for (std::size_t i = 0; i < values.size(); ++i) pool_[i].value = values[i];
    for (std::size_t k = 0; k + 1 < order.size(); ++k) pool_[order[k]].next = &pool_[order[k + 1]];
    head_ = order.empty() ? nullptr : &pool_[order[0]];
  }
  PoolList(const PoolList&) = delete;
  PoolList& operator=(const PoolList&) = delete;

  double sum() const {
    double s = 0.0;
    for (const Node* p = head_; p; p = p->next) s += p->value;
    return s;
  }

 private:
  std::vector<Node> pool_;
  Node* head_ = nullptr;
};

double sum_vector(const std::vector<double>& v) {
  double s = 0.0;
  for (double x : v) s += x;
  return s;
}

// ---- self-test
int main() {
  if (median({3, 1, 2}) != 2.0 || median({4, 1, 3, 2}) != 2.5) return 1;
  if (std::fabs(loglog_slope({10, 100, 1000}, {5, 500, 50000}) - 2.0) > 1e-9) return 2;
  if (lines_touched(16, 8, 1) != 2 || lines_touched(1000, 4, 16) != 63) return 3;
  PoolList l({1, 2, 3, 4}, {2, 0, 3, 1});
  if (l.sum() != 10.0) return 4;
  std::cout << "CPP09 reference self-test passed\n";
}
```

Benchmark (`g++ -O2 -std=c++17 bench.cpp && ./a.out`):

```cpp
// Locality benchmark: sum a vector vs follow a linked list whose nodes are visited in shuffled order.
#include <algorithm>
#include <chrono>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

struct Node { double value; Node* next; };

template <class F>
double median_ns(F f, int repeats, double per) {
  std::vector<double> t;
  for (int r = 0; r < repeats; ++r) {
    auto a = std::chrono::steady_clock::now();
    volatile double sink = f();
    (void)sink;
    auto b = std::chrono::steady_clock::now();
    t.push_back(std::chrono::duration<double, std::nano>(b - a).count() / per);
  }
  std::sort(t.begin(), t.end());
  return t[t.size() / 2];
}

int main() {
  std::mt19937 g(1);
  std::cout << "n, vector ns/elem, sequential-list ns/elem, shuffled-list ns/elem\n";
  for (std::size_t n : {1000u, 100000u, 4000000u}) {
    std::vector<double> v(n, 1.0);
    std::vector<Node> pool(n);
    std::vector<std::size_t> seq(n), shuf(n);
    std::iota(seq.begin(), seq.end(), 0);
    shuf = seq;
    std::shuffle(shuf.begin(), shuf.end(), g);
    auto link = [&](const std::vector<std::size_t>& o) {
      for (std::size_t i = 0; i < n; ++i) { pool[o[i]].value = 1.0; pool[o[i]].next = (i + 1 < n) ? &pool[o[i + 1]] : nullptr; }
      return &pool[o[0]];
    };
    int reps = n < 100000 ? 2000 : 7;
    double tv = median_ns([&] { double s = 0; for (double x : v) s += x; return s; }, reps, n);
    Node* hs = link(seq);
    double ts = median_ns([&] { double s = 0; for (Node* p = hs; p; p = p->next) s += p->value; return s; }, reps, n);
    Node* hr = link(shuf);
    double tr = median_ns([&] { double s = 0; for (Node* p = hr; p; p = p->next) s += p->value; return s; }, reps, n);
    std::cout << n << ", " << tv << ", " << ts << ", " << tr << "\n";
  }
}
```

Output trên máy dùng cho bài này (của bạn sẽ khác về số tuyệt đối nhưng không khác về hình dạng):

```
n, vector ns/elem, sequential-list ns/elem, shuffled-list ns/elem
1000, 0.76, 1.883, 1.883
100000, 0.76523, 1.89211, 14.388
4000000, 0.923664, 2.37656, 140.04
```

Lưu ý rằng danh sách có các node được liên kết theo thứ tự bộ nhớ (tuần tự) chỉ chậm hơn vector khoảng 2.5 lần ở mọi kích thước, nên chi phí của danh sách xáo trộn do mẫu truy cập gây ra, không phải do trường con trỏ thừa.

## Thực hành độc lập

### Mục tiêu

Xây các công cụ đo và cấu trúc dữ liệu cho một thí nghiệm locality, kiểm tra chúng bằng các test chính xác, rồi chạy thí nghiệm trên máy của bạn và diễn giải.

### Chuẩn bị

`g++` với C++17. Tùy chọn `perf` (`sudo apt install linux-tools-generic`) và `lscpu`. Lưu starter và các test thành `lab.cpp`; chạy test bằng `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab`. Benchmark cần một cách build khác (`-O2`, không sanitizer).

### Nhiệm vụ

1. Cài đặt `median` và `loglog_slope`; kiểm tra bằng tay rằng các điểm trên $y=5x^2$ cho độ dốc 2.
2. Cài đặt `lines_touched` và xác nhận hai ca 63 line trong phần lý thuyết.
3. Cài đặt `PoolList` với kiểm tra hoán vị và `sum_vector`.
4. Xây benchmark từ phần cài đặt tham khảo (nó cần code liên kết kiểu `PoolList`) và ghi ns mỗi phần tử cho ba kích thước. Đặt ba con số của mỗi cột vào một bảng.
5. Dùng `loglog_slope` trên tổng thời gian đo được của danh sách xáo trộn giữa hai kích thước cuối và so sánh với vector.
6. Chạy `lscpu | grep -i cache` và chú thích bảng của bạn bằng kích thước cache; đánh dấu các dòng mà dữ liệu vượt quá L2 và L3.

### Code khởi đầu

```cpp
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <numeric>
#include <set>
#include <stdexcept>
#include <vector>

// Median of the samples (mean of the two middle values for an even count).
// Throws std::invalid_argument for an empty sample. Takes a copy: do not modify the caller's data.
double median(std::vector<double> v) { throw std::logic_error("NotImplemented"); }

// Least-squares slope of ln(y) against ln(x), i.e. the empirical exponent p in y ~ x^p.
// Throws std::invalid_argument if sizes differ, fewer than 2 points, any value <= 0 (or NaN),
// or all x are equal.
double loglog_slope(const std::vector<double>& x, const std::vector<double>& y) { throw std::logic_error("NotImplemented"); }

// Number of DISTINCT cache lines touched when reading elements 0, s, 2s, ... (< n) of an array
// of n elements of elem_bytes each, stored from a line-aligned address. Element i occupies the
// line (i * elem_bytes) / line_bytes. Throws std::invalid_argument if any size argument is 0.
std::size_t lines_touched(std::size_t n, std::size_t elem_bytes, std::size_t stride_elems,
                          std::size_t line_bytes = 64) { throw std::logic_error("NotImplemented"); }

struct Node {
  double value = 0.0;
  Node* next = nullptr;
};

// Singly linked list whose nodes live in ONE pool, linked in the order given by `order`
// (order[k] = pool index of the k-th node visited). Throws std::invalid_argument if `order` is
// not a permutation of 0..n-1 (wrong size, repeated or out-of-range index).
class PoolList {
 public:
  PoolList(const std::vector<double>& values, const std::vector<std::size_t>& order) { throw std::logic_error("NotImplemented"); }
  PoolList(const PoolList&) = delete;
  PoolList& operator=(const PoolList&) = delete;
  double sum() const { throw std::logic_error("NotImplemented"); }  // follows the next pointers
};

double sum_vector(const std::vector<double>& v) { throw std::logic_error("NotImplemented"); }
```

### Kiểm thử

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#include <iostream>
#include <random>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)
template <class E, class F> bool throws(F f) { try { f(); } catch (const E&) { return true; } return false; }

int main() {
  // 1. median: odd, even, unsorted, input untouched, empty
  CHECK(median({3, 1, 2}) == 2.0 && median({4, 1, 3, 2}) == 2.5 && median({7}) == 7.0);
  std::vector<double> keep{9, 1, 5};
  median(keep);
  CHECK(keep[0] == 9 && keep[1] == 1 && keep[2] == 5);
  CHECK(throws<std::invalid_argument>([] { median({}); }));
  // 2. loglog_slope: exact power laws (hand computed: y = 5 x^2 -> slope 2; y = 3 x -> 1; y = 7 -> 0)
  CHECK(std::fabs(loglog_slope({10, 100, 1000}, {500, 50000, 5000000}) - 2.0) < 1e-9);
  CHECK(std::fabs(loglog_slope({1, 2, 4, 8}, {3, 6, 12, 24}) - 1.0) < 1e-9);
  CHECK(std::fabs(loglog_slope({1, 10}, {7, 7})) < 1e-12);
  CHECK(throws<std::invalid_argument>([] { loglog_slope({1}, {1}); }));
  CHECK(throws<std::invalid_argument>([] { loglog_slope({1, 2}, {1, 0}); }));
  CHECK(throws<std::invalid_argument>([] { loglog_slope({2, 2}, {1, 3}); }));
  CHECK(throws<std::invalid_argument>([] { loglog_slope({1, 2, 3}, {1, 2}); }));
  // 3. lines_touched: sequential vs strided (hand computed)
  CHECK(lines_touched(16, 8, 1) == 2);       // 128 bytes
  CHECK(lines_touched(16, 8, 2) == 2);       // bytes 0..112
  CHECK(lines_touched(16, 8, 8) == 2);       // elements 0 and 8 -> bytes 0 and 64
  CHECK(lines_touched(16, 8, 16) == 1);      // element 0 only
  CHECK(lines_touched(1000, 4, 1) == 63);    // 4000 bytes / 64 = 62.5
  CHECK(lines_touched(1000, 4, 16) == 63);   // 63 elements, one per line: 16x fewer reads, same lines
  CHECK(lines_touched(0, 8, 1) == 0);
  CHECK(throws<std::invalid_argument>([] { lines_touched(10, 0, 1); }));
  // 4. PoolList: hand-computed traversal and properties
  PoolList a({1.0, 2.0, 3.0, 4.0}, {2, 0, 3, 1});
  CHECK(a.sum() == 10.0);
  PoolList empty({}, {});
  CHECK(empty.sum() == 0.0);
  CHECK(throws<std::invalid_argument>([] { PoolList({1.0, 2.0}, {0, 0}); }));
  CHECK(throws<std::invalid_argument>([] { PoolList({1.0, 2.0}, {0, 2}); }));
  CHECK(throws<std::invalid_argument>([] { PoolList({1.0, 2.0}, {0}); }));
  // 5. property: any traversal order of the same values gives the same sum as the vector
  std::mt19937 g(3);
  std::vector<double> vals(1000);
  for (std::size_t i = 0; i < vals.size(); ++i) vals[i] = static_cast<double>(i % 7) * 0.5;
  std::vector<std::size_t> order(vals.size());
  std::iota(order.begin(), order.end(), 0);
  const double ref = sum_vector(vals);
  CHECK(std::fabs(ref - 1498.5) < 1e-9);  // 142 full cycles of 10.5 plus 7.5
  for (int rep = 0; rep < 5; ++rep) {
    std::shuffle(order.begin(), order.end(), g);
    PoolList l(vals, order);
    CHECK(std::fabs(l.sum() - ref) < 1e-9);
  }
  CHECK(sum_vector({}) == 0.0);
  std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi

```
all tests passed
```

Với thí nghiệm, hãy kỳ vọng cột vector giữ trong khoảng 1.5x qua các kích thước, danh sách xáo trộn tăng ít nhất 20x từ kích thước nhỏ nhất đến lớn nhất, và tỉ số danh sách/vector ở kích thước lớn nhất nằm ở hàng chục hoặc hàng trăm.

### Thử thách mở rộng

Thay phép duyệt `PoolList` bằng một phiên bản "thân thiện với prefetch" xử lý tám danh sách độc lập cùng lúc và đo xem bạn che giấu được bao nhiêu độ trễ. Hoặc chạy `perf stat -e cache-misses,cache-references ./bench` và so sánh tỉ lệ miss của hai cách duyệt.

### Thực hành với thư viện

Google Benchmark (`sudo apt install libbenchmark-dev`) làm giúp bạn phần vệ sinh đo đạc của bài này: nó chọn số lần lặp, lặp lại, và cung cấp `DoNotOptimize`. Chạy lại thí nghiệm với nó, và đối chiếu `loglog_slope` của bạn với NumPy.

```cpp
// gbench.cpp : the vector / strided / shuffled-list experiment with Google Benchmark.
// g++ -std=c++17 -O2 gbench.cpp -lbenchmark -pthread -o gbench && ./gbench
#include <benchmark/benchmark.h>
#include <algorithm>
#include <numeric>
#include <random>
#include <vector>

static void BM_VectorSum(benchmark::State& st) {
  std::vector<double> v(st.range(0), 1.0);
  for (auto _ : st) {
    double s = 0;
    for (double x : v) s += x;
    benchmark::DoNotOptimize(s);                       // makes the result observable
  }
  st.SetItemsProcessed(st.iterations() * v.size());    // report items/second -> ns per element
}
static void BM_StrideSum(benchmark::State& st) {       // stride 8 doubles = one new cache line per read
  std::vector<double> v(st.range(0), 1.0);
  for (auto _ : st) {
    double s = 0;
    for (std::size_t i = 0; i < v.size(); i += 8) s += v[i];
    benchmark::DoNotOptimize(s);
  }
  st.SetItemsProcessed(st.iterations() * (v.size() / 8));
}
struct Node { double value; Node* next; };
static void BM_ShuffledList(benchmark::State& st) {
  const std::size_t n = st.range(0);
  std::vector<Node> pool(n);
  std::vector<std::size_t> order(n);
  std::iota(order.begin(), order.end(), 0);
  std::shuffle(order.begin(), order.end(), std::mt19937(1));
  for (std::size_t i = 0; i < n; ++i) { pool[order[i]].value = 1.0; pool[order[i]].next = i + 1 < n ? &pool[order[i + 1]] : nullptr; }
  for (auto _ : st) {
    double s = 0;
    for (Node* p = &pool[order[0]]; p; p = p->next) s += p->value;
    benchmark::DoNotOptimize(s);
  }
  st.SetItemsProcessed(st.iterations() * n);
}
BENCHMARK(BM_VectorSum)->Arg(1000)->Arg(100000)->Arg(4000000);
BENCHMARK(BM_StrideSum)->Arg(1000)->Arg(100000)->Arg(4000000);
BENCHMARK(BM_ShuffledList)->Arg(1000)->Arg(100000)->Arg(4000000);
BENCHMARK_MAIN();
```

Trên một máy thử, danh sách xáo trộn chạy khoảng 5.7 M item/s cho $4\times10^6$ node (khoảng 175 ns mỗi node) so với khoảng 450 M item/s cho vector (khoảng 2.2 ns), cùng hình dạng với bảng trong ví dụ có lời giải; item/s là nghịch đảo của ns mỗi phần tử. So sánh cột `Time` của `BM_StrideSum` với `BM_VectorSum` (bản stride đọc ít phần tử hơn 8 lần). Hãy kỳ vọng số của bạn khác. (Nếu link với `libbenchmark_main` thất bại do lỗi LTO, dùng `BENCHMARK_MAIN()` như ở trên.)

Với việc khớp, NumPy cho cùng số mũ với code bình phương tối thiểu của bạn:

```python
import numpy as np
n = np.array([1000, 2000, 4000, 8000.0]); t = np.array([2.0, 8.1, 32.5, 129])
p = np.polyfit(np.log(n), np.log(t), 1)[0]      # slope of ln t against ln n
print(round(p, 3))                              # 2.004, equal to loglog_slope({1000,...}, {2.0,...})
assert abs(p - 2.004) < 1e-3 and np.median([4, 1, 3, 2]) == 2.5
```

## Kiểm chứng

- Kiểm tra hàm được đo trả về đáp án đúng (so với tổng tham chiếu) ở mọi cấu hình.
- Lặp phép đo 5-10 lần; nếu độ phân tán trên khoảng 5% thì hoặc giảm nhiễu (đóng các chương trình) hoặc báo cáo độ phân tán.
- Một kết quả đúng `0 ns` hoặc không đổi theo $n$ nghĩa là optimizer đã loại bỏ vòng lặp.
- So sánh với mô hình: một phép cộng streaming gần 1 ns mỗi phần tử (hoặc ít hơn) là hợp lý; một phép cộng vector 20 ns mỗi phần tử báo hiệu bản build `-O0` hoặc một bug.
- Xác nhận số mũ thực nghiệm với ít nhất bốn kích thước; hai điểm luôn khớp một đường thẳng.
- Đối chiếu hàm đứng đầu của profiler với một bộ đếm giờ thủ công quanh nó.

## Lỗi thường gặp

| Sai lầm | Hậu quả |
|---|---|
| Đo bản build `-O0` hoặc có sanitizer | con số lệch 3-20x, với tỉ lệ khác nhau |
| Kết quả không được dùng | optimizer xóa vòng lặp; "0 ns" |
| Đo cấp phát cùng với vòng lặp | đo `malloc` và page fault, không phải thuật toán |
| Một lần chạy, không warm-up | nhiễu và cache lạnh chi phối |
| So sánh tại một kích thước vừa trong L1 | danh sách và vector trông bằng nhau (1.88 so với 0.76 ns ở đây); hiệu ứng chỉ xuất hiện khi ra khỏi cache |
| Chọn container chỉ theo big-O | chèn $O(1)$ trong danh sách thua dịch chuyển $O(n)$ trong vector khi $n$ vừa phải |
| Tối ưu một hàm dựa trên linh cảm | 5% thời gian chạy không thể cho nhiều hơn 5% |
| Dùng AoS `float` cho vòng lặp theo từng field | truyền nhiều gấp 4 lần dữ liệu cần thiết |
| Đọc profiler không có symbol (`-O2` không có `-g`) | tên và số dòng vô dụng |

## Phương án khác và đánh đổi

- **Phân tích tiệm cận so với benchmark.** Tiệm cận cho bạn biết cái gì mở rộng được; benchmark cho bạn biết cái gì nhanh ở kích thước của bạn. Dùng tiệm cận để loại các thiết kế $O(n^2)$, benchmark để chọn giữa các thiết kế $O(n)$.
- **`std::vector` so với `std::list`/`std::map`.** Ưu tiên vector, vector đã sắp xếp, hoặc flat map cho dữ liệu nhỏ và vừa; chỉ dùng container dựa trên node vì các đảm bảo đặc biệt của chúng (địa chỉ ổn định, nối splice rẻ).
- **AoS so với SoA so với AoSoA.** AoS tự nhiên cho "làm mọi thứ với một đối tượng"; SoA hợp với "làm một việc với mọi đối tượng" và vector hóa (SIMD); các khối AoSoA 8 hoặc 16 cân bằng cả hai.
- **Profiler lấy mẫu (`perf`, `gprof`) so với instrumentation (bộ đếm giờ, tracing).** Lấy mẫu có chi phí thấp và tìm hotspot; bộ đếm giờ/tracing thủ công cho thời lượng chính xác của các đoạn đã biết và dùng được cho độ trễ trong các vòng lặp real-time.
- **Tối ưu vi mô so với đổi thuật toán.** Cải thiện thuật toán hoặc bố cục dữ liệu trước (hệ số 10-100), rồi mới đến cờ compiler và tinh chỉnh vi mô (hệ số 1.1-2).
- **Song song (CPP10).** Nhiều lõi chỉ giúp khi công việc chia được và băng thông bộ nhớ chưa bão hòa; một vòng lặp bị giới hạn bởi băng thông không mở rộng tuyến tính.

## Vận dụng và ghi nhớ

Cùng mô hình chi phí này giải thích vì sao các phép toán vector hóa của NumPy thắng vòng lặp Python (liên tục, thân thiện với cache, không dispatch theo từng phần tử), vì sao PyTorch quan tâm bố cục tensor (contiguous so với strided), vì sao message ROS 2 truyền bằng con trỏ không copy, và vì sao kernel GPU thích truy cập bộ nhớ coalesced. Hãy luyện bằng cách đo một vòng lặp của chính bạn ở ba kích thước, và vẽ tay đồ thị log-log. Sau một tuần, tự suy lại định luật Amdahl từ định nghĩa (thời gian trước $=1$, thời gian sau $=(1-f)+f/s$) và nhớ lại bốn bậc độ lớn của độ trễ L1, L2, L3 và DRAM.

## Đáp án bài tập

1. (a) $O(n^2)$, (b) $O(\log n)$, (c) amortized $O(1)$ mỗi lần push, $O(n)$ cho $n$ lần push, (d) $O(n\log n)$. Với $n=10^5$: $n^2=10^{10}$ so với $n\log_2n\approx1.66\times10^6$, tỉ số khoảng 6000.
2. Tuần tự: $4000/64=62.5$, nên 63 line. Stride 16 (64 byte): phần tử 0, 16, ..., 992: 63 phần tử, mỗi phần tử một line, 63 line. Lượt có stride thực hiện ít lần đọc hơn 16 lần nhưng nạp cùng số line, nên khi dữ liệu không nằm trong cache thời gian chạy của nó xấp xỉ lượt tuần tự: thời gian bộ nhớ đi theo line, không theo phần tử.
3. $S=1/(0.7+0.3/10)=1/0.73=1.37$. Tốt nhất có thể khi resize miễn phí: $1/0.7=1.43$.
4. Một câu trả lời tốt: (1) cache line: mỗi lần nạp node của danh sách lấy một line 64 byte nhưng chỉ dùng 16 byte (giá trị 8 byte cộng con trỏ 8 byte), trong khi vector dùng cả 64 byte của mỗi line nó nạp; (2) prefetching: địa chỉ của vector dự đoán được, nên phần cứng nạp trước và vòng lặp chạy ở băng thông streaming (0.92 ns, khoảng 8.7 GB/s), nhưng địa chỉ kế tiếp của danh sách xáo trộn phụ thuộc vào lần nạp trước; (3) độ trễ: với 64 MB node, mọi bước nhảy đều miss xuống DRAM, tốn khoảng 140 ns, gần với độ trễ DRAM; (4) bằng chứng: ở $n=1000$ (16 KB trong cache) tỉ số chỉ là 2.5, và nó tăng lên 19 ở $10^5$ và 152 ở $4\times10^6$ khi dữ liệu rời khỏi các cache.
5. Khiếm khuyết: (1) bản build `-O0`, đo code chưa tối ưu; (2) việc cấp phát và khởi tạo vector nằm trong vùng được đo; (3) `s` không bao giờ được dùng, nên bản build tối ưu có thể xóa vòng lặp; (4) một lần chạy, không warm-up hay lặp lại; (5) tổng thời gian thay vì ns mỗi phần tử, nên không so sánh được qua các $n$; (6) chỉ một kích thước, nên không có thông tin về mở rộng hay cache. Cách sửa: build với `-O2`, cấp phát bên ngoài bộ đếm giờ, lưu kết quả vào một `volatile` hoặc in ra, lặp 10-1000 lần và báo cáo median theo ns/phần tử cho nhiều kích thước.
6. Ma trận có $4096^2\cdot8/64=2{,}097{,}152$ line. Theo từng hàng: mỗi line được nạp một lần: khoảng $2.1\times10^6$ lần nạp. Theo từng cột: mọi truy cập vào một line khác, và line bị loại bỏ trước khi các phần tử lân cận của nó được dùng: $4096^2=16{,}777{,}216$ lần nạp, nhiều hơn 8 lần (một lần mỗi phần tử thay vì một lần mỗi 8 phần tử).
7. AoS truyền mọi line: $10^6\cdot16=16$ MB (250,000 line). SoA chỉ đọc `z`: $10^6\cdot4=4$ MB (62,500 line), hệ số 4. Sự khác biệt quan trọng khi dữ liệu không vừa trong cache; khi cả mảng vừa trong L2/L3 (giả sử $10^4$ điểm = 160 KB), AoS và SoA chạy với tốc độ tương tự.
8. Các tỉ số: $8.1/2.0=4.05$, $32.5/8.1=4.01$, $129/32.5=3.97$, mỗi cái gần $4=2^2$, nên $p\approx2$. Bình phương tối thiểu cho $p\approx2.004$. Nhiều khả năng là thuật toán bậc hai (vòng lặp lồng nhau, khoảng cách từng cặp ngây thơ). Dự đoán tại $n=10^5$: $2.0\ \text{ms}\cdot(100)^2=20{,}000$ ms, khoảng 20 s. Có thể sai vì: dữ liệu rời khỏi cache ở $n$ lớn hơn (số mũ tăng), và một số hạng bậc hai có thể che các số hạng bậc thấp hơn hoặc có sự thay đổi chế độ thuật toán (ví dụ một ngưỡng hay hành vi cấp phát bộ nhớ).
9. (i) $S=1/(0.38+0.62/5)=1/0.504=1.98$. (ii) $S=1/(0.82+0.18/100)=1/0.8218=1.22$. Tối ưu tìm kiếm trước. Trước khi viết code: kiểm tra bằng một phép đo thứ hai (bộ đếm giờ thủ công hoặc `perf`) rằng profile là đại diện, rằng đó là bản build tối ưu, và liệu một thay đổi thuật toán (k-d tree hoặc voxel hash thay vì brute force) có thắng việc tinh chỉnh vi mô không.
10. Dung lượng chiếm: $5000\cdot32=160$ KB, vừa thoải mái trong L2 (thường 256 KB đến 2 MB), nên SoA nhiều khả năng cho lợi ích nhỏ. Benchmark: đo thời gian chuẩn hóa cho $N=10^3$ đến $10^7$ ở cả hai bố cục, báo cáo ns mỗi hạt, và tìm điểm gãy nơi AoS (32 B cho mỗi lần đọc weight) rời cache sớm hơn SoA (8 B cho mỗi weight); quyết định dựa trên kích thước bạn thực sự chạy, không phải kích thước lớn nhất. Một câu trả lời tốt kết luận "giữ AoS cho 5000 hạt trừ khi profiling cho thấy nó quan trọng, chuyển nếu $N$ tăng đến hàng triệu".
11. Một câu trả lời tốt gồm: một bảng bốn cột với ba kích thước; một cột stride gần với vector ở $n$ nhỏ nhưng tiến tới chi phí cache miss mỗi phần tử khi stride $\ge8$ double và dữ liệu lớn (mỗi lần đọc là một line mới); độ dốc gần 1 cho vector (1.0-1.1) và lớn hơn (khoảng 1.5-1.7 giữa hai kích thước cuối) cho danh sách xáo trộn trong vùng chuyển tiếp; và một nhận xét rằng mỗi chỗ bẻ cong khớp với dung lượng L1/L2/L3 từ `lscpu`.

## Đọc thêm

- [Drepper: What Every Programmer Should Know About Memory](https://lwn.net/Articles/250967/) - bản mô tả chi tiết kinh điển về cache, độ trễ và mẫu truy cập.
- [Linux perf Tutorial](https://perf.wiki.kernel.org/index.php/Tutorial) - `perf stat`, `perf record` và `perf report` kèm ví dụ.
- [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/) - phân tích độ phức tạp, cấu trúc dữ liệu, và bài tập.

**Thực hành thêm:** [hướng dẫn người dùng Google Benchmark](https://github.com/google/benchmark/blob/main/docs/user_guide.md) (viết một benchmark cho mỗi container), các bài tập về phân tích tiệm cận trong [MIT 6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/), [trang labs của CS:APP](https://csapp.cs.cmu.edu/3e/labs.html) (Cache Lab chính là bài tập locality của bài này), [What Every Programmer Should Know About Memory](https://www.akkadia.org/drepper/cpumemory.pdf) của Drepper, và [perf tutorial](https://perf.wiki.kernel.org/index.php/Tutorial) / [các ví dụ perf của Brendan Gregg](https://www.brendangregg.com/perf.html) để profile benchmark của bạn.
