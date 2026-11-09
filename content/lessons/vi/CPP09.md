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

**Hãy dự đoán trước khi tính.** Hai chương trình cộng cùng 4 triệu số; một chương trình đọc mảng từ đầu đến cuối, chương trình kia đi theo một chuỗi tham chiếu thăm cùng các số đó theo thứ tự ngẫu nhiên. Cả hai đều làm 4 triệu phép cộng. Trước khi đọc tiếp, hãy ghi ra bạn kỳ vọng chương trình thứ hai chậm hơn bao nhiêu lần. Đa số đoán 2 đến 5; kết quả đo trong bài này là khoảng 150.

**Một hình ảnh để nhớ.** Hãy nghĩ đến một thư viện với một cái bàn nhỏ (cache), một phòng đọc (tầng cache kế tiếp) và một nhà kho bên kia thành phố (DRAM). Lấy một cuốn sách từ nhà kho mất một giờ; chiếc xe tải luôn chở cả một thùng 64 cuốn nằm cạnh nhau. Nếu bạn đọc sách theo thứ tự trên kệ, một chuyến phục vụ 8 hoặc 16 yêu cầu và tài xế có thể bắt đầu chuyến sau trước khi bạn đọc xong thùng (prefetching). Nếu bạn xin sách theo thứ tự ngẫu nhiên, mỗi yêu cầu là một chuyến một giờ mới và các cuốn khác trong thùng bị bỏ phí. Cùng số sách, chi phí hoàn toàn khác.

**Trực giác sai** là "một thao tác tốn như nhau dù dữ liệu ở đâu, nên đếm thao tác là đủ". Đếm thao tác cho biết chi phí *tăng* thế nào; nó không nói gì về *đơn vị* của chi phí đó, thứ thay đổi tới 100 lần tùy dữ liệu nằm ở đâu và bạn chạm vào theo thứ tự nào. Trực giác sai thứ hai là tin vào một lần đo duy nhất: con số đo một lần, trong bản debug, khi công việc có thể bị optimizer xóa, không phải là bằng chứng.

## Lý thuyết và suy dẫn

### Chi phí tiệm cận

$f(n)=O(g(n))$ nghĩa là $f(n)\le c\,g(n)$ với một hằng số $c$ nào đó và mọi $n$ đủ lớn. Các tốc độ tăng thông dụng, theo thứ tự: $1,\ \log n,\ n,\ n\log n,\ n^2,\ n^3,\ 2^n$. Với $n=10^5$ điểm scan: so sánh từng cặp thực hiện $n^2=10^{10}$ phép toán, một lần sắp xếp hay dựng k-d tree thực hiện $n\log_2n\approx1.66\times10^6$, tỉ số khoảng 6000. Quy tắc: bỏ hằng số và các số hạng bậc thấp; vòng lặp lồng nhau nhân với nhau; các bước tuần tự cộng với nhau; vòng lặp giảm nửa phạm vi là $\log n$. Amortized $O(1)$ (`push_back` của vector) nghĩa là trung bình trên một chuỗi là hằng số dù từng bước đơn lẻ có thể tốn $O(n)$.

**Số mũ thực nghiệm.** Nếu $t(n)\approx c\,n^p$, thì $\ln t=\ln c+p\ln n$, một đường thẳng trên đồ thị log-log với độ dốc $p$. Khớp độ dốc bằng bình phương tối thiểu:
$$p=\frac{\sum_i(\ln n_i-\overline{\ln n})(\ln t_i-\overline{\ln t})}{\sum_i(\ln n_i-\overline{\ln n})^2}.$$
Nhân đôi $n$ nhân thời gian với $2^p$: khoảng $2$ cho tuyến tính, $4$ cho bậc hai. Dùng ít nhất bốn kích thước trải rộng hệ số 8 trở lên, và nhớ rằng hiệu ứng cache làm cong đường thẳng khi dữ liệu vượt qua một kích thước cache.

**Ví dụ.** Tìm cặp điểm gần nhất bằng brute force trên $n$ điểm lidar 2D so sánh mọi cặp, tức $n(n-1)/2$ phép tính khoảng cách. Chương trình đo thời gian cho $n=3000,6000,12000,24000$ (tốt nhất trong 5 lần) rồi khớp số mũ $p$ của $t\propto n^p$ bằng công thức bình phương tối thiểu ở trên (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, một lõi hiệu năng của Intel Core i5-12500H, ghim bằng `taskset`; thời gian thuộc về máy đó). Phép khớp cho thấy tốc độ tăng nào, và dự đoán thời gian bao nhiêu ở $n=48{,}000$?

```cpp
#include <chrono>
#include <cmath>
#include <cstdio>
#include <random>
#include <vector>
// Brute-force closest pair: O(n^2). Time it for four sizes and fit ln t = ln c + p ln n.
double closest_sq(const std::vector<double>& x, const std::vector<double>& y) {
  double best = 1e300;
  for (std::size_t i = 0; i < x.size(); ++i)
    for (std::size_t j = i + 1; j < x.size(); ++j) {
      double dx = x[i] - x[j], dy = y[i] - y[j];
      best = std::fmin(best, dx * dx + dy * dy);
    }
  return best;
}
int main() {
  std::mt19937 g(7);
  std::uniform_real_distribution<double> u(0.0, 10.0);
  std::vector<double> ln, lt;
  for (std::size_t n : {3000u, 6000u, 12000u, 24000u}) {
    std::vector<double> x(n), y(n);
    for (auto& v : x) v = u(g);
    for (auto& v : y) v = u(g);
    double best = 1e300, d = 0;
    for (int r = 0; r < 5; ++r) {
      auto a = std::chrono::steady_clock::now();
      d = closest_sq(x, y);
      auto b = std::chrono::steady_clock::now();
      best = std::fmin(best, std::chrono::duration<double, std::milli>(b - a).count());
    }
    std::printf("n = %5zu  best of 5 = %8.2f ms  (min d^2 = %.2e)\n", n, best, d);
    ln.push_back(std::log(double(n)));
    lt.push_back(std::log(best));
  }
  double mx = 0, my = 0;
  for (std::size_t i = 0; i < ln.size(); ++i) { mx += ln[i] / 4; my += lt[i] / 4; }
  double sxy = 0, sxx = 0;
  for (std::size_t i = 0; i < ln.size(); ++i) { sxy += (ln[i] - mx) * (lt[i] - my); sxx += (ln[i] - mx) * (ln[i] - mx); }
  std::printf("fitted exponent p = %.3f\n", sxy / sxx);
}
```

**Lời giải.** Thời gian tăng $21.34/5.11=4.18$, $87.54/21.34=4.10$ và $349.94/87.54=4.00$ lần mỗi lần gấp đôi, gần $2^2$, và độ dốc bình phương tối thiểu của $\ln t$ theo $\ln n$ là $p=2.033$: bậc hai, đúng như vòng lặp lồng nhau cho biết. Ở $n=48{,}000$ phép khớp dự đoán khoảng $4\times350\approx1400$ ms. Lần chạy ngắn nhất (5 ms) kém chính xác nhất, nên tỉ số đầu hơi lớn hơn 4. Thời gian phụ thuộc máy và giữ nguyên như đã đo; chạy lại trên máy khác sẽ đổi chúng và đổi số mũ ở chữ số cuối, không đổi dạng bậc hai. Chương trình in ra:

```text
n =  3000  best of 5 =     5.11 ms  (min d^2 = 1.45e-06)
n =  6000  best of 5 =    21.34 ms  (min d^2 = 1.84e-06)
n = 12000  best of 5 =    87.54 ms  (min d^2 = 5.76e-08)
n = 24000  best of 5 =   349.94 ms  (min d^2 = 1.22e-07)
fitted exponent p = 2.033
```

### Mô hình chi phí của hệ phân cấp bộ nhớ

Bậc độ lớn sơ bộ (thay đổi theo CPU): L1 hit khoảng 1 ns (4 chu kỳ), L2 khoảng 4 ns, L3 khoảng 15-40 ns, DRAM khoảng 80-100 ns. Băng thông tuần tự khoảng 10-30 GB/s, tức $\approx0.3$-$0.8$ ns mỗi phần tử 8 byte, tốc độ mà phép cộng vector đạt được. Một vòng lặp đuổi theo con trỏ bị *giới hạn bởi độ trễ*: mỗi lần nạp phụ thuộc vào lần trước, nên một cache miss phải trả đủ: 140 ns mỗi node trong benchmark của ta ở 4 triệu node, phù hợp với độ trễ DRAM cộng TLB miss.

**Cache line.** Với một mảng phần tử $b$ byte đọc theo bước nhảy (stride) $s$ (tính theo phần tử), phần tử $i$ nằm trong line $\lfloor ib/64\rfloor$. Đọc tuần tự $n$ phần tử chạm $\lceil nb/64\rceil$ line. Một stride từ $64/b$ phần tử trở lên chạm một line mới ở *mỗi* lần đọc. Ví dụ: 1000 float ($b=4$) đọc tuần tự chạm $\lceil4000/64\rceil=63$ line; đọc với stride 16 cũng chạm 63 line, với số phần tử ít hơn 16 lần. Thời gian đi theo số line, không theo số phần tử, một khi dữ liệu nằm ngoài cache.

**Bố cục.** Mảng các cấu trúc (AoS) xen kẽ các field, nên đọc một field kéo theo các field khác qua cache; cấu trúc của các mảng (SoA) lưu mỗi field liên tục. Với $N=10^6$ điểm 16 byte (x, y, z, intensity), cộng chỉ `z` truyền 16 MB với AoS nhưng 4 MB với SoA.

**Duyệt hai chiều.** Một ma trận $N\times N$ double theo hàng (row-major) được duyệt từng hàng với một miss mỗi 8 phần tử; duyệt từng cột thì mỗi truy cập là một line mới (stride $8N$ byte).

**Ví dụ.** Một chu trình ngẫu nhiên gồm các chỉ số 8 byte được đuổi theo trong các mảng 16 KiB, 256 KiB, 4 MiB và 64 MiB. Mỗi bước nhảy phụ thuộc vào lần nạp trước, nên thời gian mỗi bước là độ trễ của tầng đang chứa mảng (cùng bản build và máy như trên: L1d 48 KiB và L2 1.25 MiB mỗi lõi, L3 18 MiB dùng chung). Mỗi kích thước rơi vào tầng nào, mỗi tầng cho độ trễ bao nhiêu, và tỉ số giữa dòng đầu và dòng cuối là bao nhiêu?

```cpp
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <numeric>
#include <random>
#include <vector>
// Dependent loads through one random cycle of 8-byte indices: time per hop vs working-set size.
int main() {
  std::mt19937_64 g(3);
  std::printf("%10s %12s\n", "bytes", "ns per hop");
  for (std::size_t kb : {16u, 256u, 4096u, 65536u}) {
    std::size_t n = kb * 1024 / sizeof(std::size_t);
    std::vector<std::size_t> perm(n), next(n);
    std::iota(perm.begin(), perm.end(), 0);
    std::shuffle(perm.begin(), perm.end(), g);
    for (std::size_t i = 0; i < n; ++i) next[perm[i]] = perm[(i + 1) % n];  // one cycle of length n
    std::size_t hops = 20'000'000, p = 0;
    auto a = std::chrono::steady_clock::now();
    for (std::size_t i = 0; i < hops; ++i) p = next[p];
    auto b = std::chrono::steady_clock::now();
    volatile std::size_t sink = p; (void)sink;
    std::printf("%7zu KiB %12.2f\n", kb, std::chrono::duration<double, std::nano>(b - a).count() / hops);
  }
}
```

**Lời giải.** Bốn kích thước rơi vào bốn tầng: 16 KiB vừa L1d (khoảng 1.1 ns mỗi bước), 256 KiB vượt L1d nhưng vừa L2 (3.0 ns), 4 MiB vượt L2 nhưng vừa L3 (11.9 ns) và 64 MiB vượt L3 nên mỗi bước đi tới DRAM (khoảng 110 ns). Tỉ số giữa dòng đầu và dòng cuối là $109.71/1.13=97$, với cùng một chuỗi lệnh. 110 ns gần với 140 ns mỗi node của danh sách xáo trộn trong bảng của bài; phần chênh còn lại chưa được tách riêng ở đây. Các thời gian phụ thuộc máy và giữ nguyên như đã đo. Chương trình in ra:

```text
     bytes   ns per hop
     16 KiB         1.13
    256 KiB         2.99
   4096 KiB        11.91
  65536 KiB       109.71
```

### Đo đạc trung thực

1. Bản build tối ưu hóa (`-O2` hoặc `-O3`), không có sanitizer, assertion của bản release như trong production.
2. Làm cho kết quả quan sát được (lưu vào một `volatile` hoặc in ra) để optimizer không thể loại bỏ công việc.
3. Warm up, lặp nhiều lần, báo cáo **median** và độ phân tán; giá trị nhỏ nhất cũng hữu ích như cận dưới. Không bao giờ dùng một lần chạy.
4. Chỉ đo thao tác: cấp phát và khởi tạo bên ngoài vùng được đo.
5. Cố định tần số CPU và đóng các chương trình khác nếu có thể; ghi rõ máy.
6. Thay đổi $n$ qua các kích thước cache (vài KB, hàng trăm KB, hàng chục MB) và báo cáo ns mỗi phần tử, không phải tổng thời gian.
7. Kiểm tra tính đúng của kết quả (tổng bằng tham chiếu) để bạn không đo một bug.

**Ví dụ.** Quy tắc 2 trong thực tế: cùng một vòng lặp cộng (mảng $10^6$ double, lặp 100 lần) được đo một lần với kết quả bị bỏ đi và một lần với kết quả lưu vào `volatile` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, một lõi hiệu năng của Intel Core i5-12500H, ghim bằng `taskset`). Mỗi biến thể báo thời gian mỗi phần tử bao nhiêu, và biến thể nào đáng tin?

```cpp
#include <chrono>
#include <cstdio>
#include <vector>
// The same loop timed with its result discarded and with its result stored in a volatile.
static double work(const std::vector<double>& v) { double s = 0; for (double x : v) s += x * 1.0000001; return s; }
int main() {
  std::vector<double> v(1'000'000, 1.0);
  auto t = [] { return std::chrono::steady_clock::now(); };
  auto ns = [](auto a, auto b) { return std::chrono::duration<double, std::nano>(b - a).count(); };
  auto a = t();
  for (int r = 0; r < 100; ++r) (void)work(v);          // result unused: the compiler may drop the calls
  auto b = t();
  std::printf("result discarded : %9.3f ns per element\n", ns(a, b) / 100 / v.size());
  volatile double sink = 0;
  (void)sink;
  a = t();
  for (int r = 0; r < 100; ++r) sink = work(v);          // result observable
  b = t();
  std::printf("result stored    : %9.3f ns per element\n", ns(a, b) / 100 / v.size());
}
```

**Lời giải.** Biến thể đầu báo 0.000 ns mỗi phần tử: compiler thấy `work` không có tác dụng phụ và xóa các lời gọi. Một kết quả dưới một chu kỳ clock mỗi phần tử (khoảng 0.25 ns ở 4 GHz) là dấu hiệu nên nghi ngờ dead-code elimination. Biến thể thứ hai, 0.469 ns mỗi phần tử, truyền 8 B mỗi phần tử với $8/0.469\approx17$ GB/s, một tốc độ hợp lý cho mảng 8 MB, nên đó là biến thể đáng tin. Giá trị 0.469 ns phụ thuộc máy và giữ nguyên như đã đo. Chương trình in ra:

```text
result discarded :     0.000 ns per element
result stored    :     0.469 ns per element
```

### Profiling và định luật Amdahl

Profiler lấy mẫu xem chương trình tốn thời gian ở đâu: `perf record -g ./prog` rồi `perf report`, hoặc `gprof`. Tối ưu phần đóng góp lớn nhất trước. Nếu một phần chiếm tỉ lệ $f$ tổng thời gian và được làm nhanh hơn $s$ lần, mức tăng tốc tổng thể là
$$S=\frac{1}{(1-f)+f/s}.$$
Với $f=0.3$ và $s=10$: $S=1/(0.7+0.03)=1.37$. Ngay cả $s\to\infty$ cũng chỉ cho $1/0.7=1.43$. Hãy profile trước; nút thắt cổ chai hiếm khi ở chỗ trực giác bảo.

![Tốc độ tăng chung theo tốc độ tăng cục bộ cho f = 0.3, 0.5 và 0.749, mỗi đường phẳng dần về 1/(1-f)](/lesson-figures/CPP09-5.svg)

*Hình: định luật Amdahl. Mỗi đường là $S=1/((1-f)+f/s)$ và phẳng dần về $1/(1-f)$; hai chấm là $f=0.3,\ s=10$ của bài và công đoạn đo được với $f=0.749,\ s=8$.*

**Ví dụ.** Một frame có hai công đoạn. Công đoạn A (một căn bậc hai mỗi phần tử) và công đoạn B (một phép nhân cộng mỗi phần tử) được đo riêng, định luật Amdahl dự đoán mức lợi khi làm A nhanh hơn tám lần, rồi A thật sự làm một phần tám khối lượng (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, một lõi hiệu năng của Intel Core i5-12500H, ghim bằng `taskset`; tốt nhất trong 9 lần chạy). Phân số $f$ của frame thuộc A là bao nhiêu, công thức dự đoán mức tăng tốc nào cho $s=8$, đo được bao nhiêu, và sau đó profile chỉ vào công đoạn nào?

```cpp
#include <chrono>
#include <cmath>
#include <cstdio>
#include <vector>
// Two stages per frame; time each, apply Amdahl's formula, then really speed one stage up 8x.
static double stage_a(const std::vector<double>& v, int reps) { double s = 0; for (int r = 0; r < reps; ++r) for (double x : v) s += std::sqrt(x + r); return s; }
static double stage_b(const std::vector<double>& v, int reps) { double s = 0; for (int r = 0; r < reps; ++r) for (double x : v) s += x * 0.5 + r; return s; }
static double ms(std::chrono::steady_clock::time_point a, std::chrono::steady_clock::time_point b) { return std::chrono::duration<double, std::milli>(b - a).count(); }
int main() {
  std::vector<double> v(1 << 16, 2.0);
  volatile double sink = 0;
  (void)sink;
  double best[2][2];  // [config][stage]
  for (int cfg = 0; cfg < 2; ++cfg) {
    int ra = cfg == 0 ? 240 : 30;       // config 1: stage A does 1/8 of the work (8x faster)
    double ta = 1e9, tb = 1e9;
    for (int rep = 0; rep < 9; ++rep) {
      auto t0 = std::chrono::steady_clock::now(); sink = stage_a(v, ra);
      auto t1 = std::chrono::steady_clock::now(); sink = stage_b(v, 240);
      auto t2 = std::chrono::steady_clock::now();
      ta = std::fmin(ta, ms(t0, t1)); tb = std::fmin(tb, ms(t1, t2));
    }
    best[cfg][0] = ta; best[cfg][1] = tb;
  }
  double total0 = best[0][0] + best[0][1], total1 = best[1][0] + best[1][1];
  double f = best[0][0] / total0;
  std::printf("before: A = %.2f ms, B = %.2f ms, total = %.2f ms, f(A) = %.3f\n", best[0][0], best[0][1], total0, f);
  std::printf("Amdahl prediction for s = 8 : %.3f\n", 1.0 / ((1 - f) + f / 8));
  std::printf("after : A = %.2f ms, B = %.2f ms, total = %.2f ms, measured speedup = %.3f\n", best[1][0], best[1][1], total1, total0 / total1);
}
```

**Lời giải.** Công đoạn A chiếm $f=20.98/28.02=0.749$ thời gian. Với $s=8$, công thức $S=1/\bigl((1-f)+f/s\bigr)$ cho $S=1/(0.251+0.749/8)=2.90$ và phép đo cho $28.02/9.60=2.92$, lệch dưới 1 %. Sau thay đổi, B chiếm $7.01/9.60=73\%$ frame, và dù A nhanh vô hạn cũng không vượt $1/(1-0.749)=3.98$: profile giờ chỉ vào B. Các thời gian phụ thuộc máy và giữ nguyên như đã đo. Chương trình in ra:

```text
before: A = 20.98 ms, B = 7.04 ms, total = 28.02 ms, f(A) = 0.749
Amdahl prediction for s = 8 : 2.900
after : A = 2.59 ms, B = 7.01 ms, total = 9.60 ms, measured speedup = 2.919
```

Các thanh trượt dưới đây cho thấy cùng định luật với các giá trị $f$ và $s$ khác:

```explore
{
  "title": "How much does a faster part buy?",
  "title_vi": "Làm nhanh một phần mua được bao nhiêu?",
  "prompt": "Predict first: a part that takes 30% of the time is made 10 times faster. Will the whole program run more than 1.5 times faster? Then drag f and s: find the s that reaches 90% of the ceiling 1/(1-f), and see what raising f does to the ceiling.",
  "prompt_vi": "Dự đoán trước: một phần chiếm 30% thời gian được làm nhanh hơn 10 lần. Cả chương trình có chạy nhanh hơn hơn 1.5 lần không? Rồi kéo f và s: tìm s đạt 90% của trần 1/(1-f), và xem tăng f làm trần thay đổi thế nào.",
  "params": [
    { "name": "f", "label": "fraction of time f", "label_vi": "tỉ lệ thời gian f", "min": 0.05, "max": 0.95, "step": 0.01, "value": 0.3, "unit": "" },
    { "name": "s", "label": "local speedup s", "label_vi": "tốc độ tăng cục bộ s", "min": 1, "max": 100, "step": 1, "value": 10, "unit": "x" }
  ],
  "let": [
    { "name": "S", "expr": "1 / ((1 - f) + f / s)" },
    { "name": "ceil", "expr": "1 / (1 - f)" }
  ],
  "plot": {
    "x": { "name": "x", "min": 1, "max": 100, "label": "local speedup s", "label_vi": "tốc độ tăng cục bộ s" },
    "y": { "label": "overall speedup S", "label_vi": "tốc độ tăng chung S", "min": 1 },
    "series": [
      { "expr": "1 / ((1 - f) + f / x)", "label": "S(s)", "label_vi": "S(s)", "color": "orange" },
      { "expr": "ceil", "label": "ceiling 1/(1-f)", "label_vi": "trần 1/(1-f)", "color": "grey" }
    ],
    "points": [
      { "x": "s", "y": "S", "label": "your s", "label_vi": "s của bạn", "color": "blue" }
    ]
  },
  "readouts": [
    { "label": "overall speedup S", "label_vi": "tốc độ tăng chung S", "expr": "S", "unit": "x", "digits": 3 },
    { "label": "ceiling 1/(1-f)", "label_vi": "trần 1/(1-f)", "expr": "ceil", "unit": "x", "digits": 3 },
    { "label": "share of the ceiling reached", "label_vi": "phần trăm trần đã đạt", "expr": "100 * S / ceil", "unit": "%", "digits": 1 },
    { "label": "new time as a fraction of the old", "label_vi": "thời gian mới so với cũ", "expr": "(1 - f) + f / s", "unit": "", "digits": 3 }
  ]
}
```

### Tính kết hợp tập (set associativity) và conflict miss

Một cache có $C$ byte, kích thước line $L$ và độ kết hợp $W$ ("$W$-way") có $S=C/(WL)$ *tập* (set). Địa chỉ byte $a$ thuộc line $\lfloor a/L\rfloor$, line này chỉ được đặt trong tập $\lfloor a/L\rfloor \bmod S$, ở một trong $W$ ô của tập đó (cache kết hợp đầy đủ, $S=1$, phải so sánh mọi tag nên không thực tế với cache cỡ megabyte; cache ánh xạ trực tiếp có $W=1$) (Drepper, *What Every Programmer Should Know About Memory*, §3.3.1). Dung lượng không phải giới hạn duy nhất: nếu hơn $W$ line "nóng" cùng ánh xạ vào một tập thì chúng đẩy nhau ra ngay cả khi cache gần như trống. Đó là **conflict miss**.

*Trường hợp cụ thể.* L1d 32 KiB, 8-way, line 64 byte có $S=32768/(8\cdot64)=64$ tập. Đi xuống một cột của ma trận row-major có $N$ double mỗi hàng. Hàng $r$ bắt đầu ở byte $8Nr$, nên tập của nó là $\lfloor 8Nr/64\rfloor \bmod 64$. Khi $8N$ là bội của 64, chỉ số tập tăng một bước không đổi $d=(N/8)\bmod 64$ mỗi hàng, và cột chỉ ghé qua $S/\gcd(d,S)$ tập khác nhau, tức là tối đa $8\,S/\gcd(d,S)$ line có thể ở lại cache cùng lúc. Với $N=1024$ (hàng 8192 byte) $d=128\bmod64=0$: mọi hàng rơi vào cùng một tập và cả cột tranh nhau 8 ô. Với $N=1032$, $d=1$ và cả 64 tập (512 line) được dùng. Drepper đã đo đúng hiện tượng này (§6.2.1, Hình 6.5): các phần tử danh sách cách nhau một bội của 4096 byte (64 line, tức $S$ line) với hơn 8 phần tử tốn khoảng 10 chu kỳ mỗi phần tử thay vì 3, và phép đo này cũng cho biết L1d là 8-way, 32 kB. Vì vậy lũy thừa của hai là kích thước tệ nhất cho truy cập có stride; đệm (padding) mỗi hàng thêm một phần tử thường là đủ (Bài tập 12).

![Ba vòng tròn gồm 64 tập cache cho thấy lượt đi xuống cột chạm những tập nào với N = 1024, 1056 và 1032](/lesson-figures/CPP09-2.svg)

*Hình: cùng một cache 32 KiB, 8-way nhìn từ một lượt đi xuống cột. Bước $d=(N/8)\bmod64$ quyết định cột dùng 1, 16 hay cả 64 tập, và do đó bao nhiêu line có thể ở lại (theo Drepper, §3.3.1).*

**Ví dụ.** Mười sáu cache line được nối thành một chu trình, mỗi line giữ offset của line kế, và chu trình được đi $10^8$ bước. Ở bố cục đầu các line cách nhau 4096 byte, ở bố cục sau cách nhau 4160 byte. L1d của lõi này là 48 KiB, 12-way, nên $S=49152/(12\cdot64)=64$ tập, và 4096 byte đúng bằng 64 line (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, một lõi hiệu năng của Intel Core i5-12500H, ghim bằng `taskset`). Ở bố cục nào các line tranh nhau cùng một tập, và mỗi bố cục cho thời gian mỗi bước bao nhiêu?

```cpp
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
// 16 cache lines whose addresses differ by a stride; each line holds the offset of the next one.
// Stride 4096 B maps all 16 to ONE set of a 64-set L1d; stride 4160 B spreads them over 16 sets.
int main() {
  const std::size_t lines = 16, hops = 100'000'000;
  for (std::size_t stride : {4096u, 4160u}) {
    char* mem = static_cast<char*>(std::aligned_alloc(4096, (stride * lines + 8191) / 4096 * 4096));
    for (std::size_t i = 0; i < lines; ++i)
      *reinterpret_cast<std::size_t*>(mem + i * stride) = ((i + 5) % lines) * stride;  // 5 is coprime to 16: one cycle
    std::size_t off = 0;
    auto a = std::chrono::steady_clock::now();
    for (std::size_t i = 0; i < hops; ++i) off = *reinterpret_cast<std::size_t*>(mem + off);
    auto b = std::chrono::steady_clock::now();
    volatile std::size_t sink = off; (void)sink;
    std::printf("stride %5zu B: %.2f ns per hop\n", stride, std::chrono::duration<double, std::nano>(b - a).count() / hops);
    std::free(mem);
  }
}
```

**Lời giải.** Với khoảng cách 4096 B, cả 16 line ánh xạ vào một tập (chỉ số tập tăng $64 \bmod 64=0$ mỗi line), và tập đó chỉ có 12 way, nên theo LRU mỗi bước đều miss L1 và được L2 phục vụ ở 3.16 ns (độ trễ L2 trong ví dụ trước là 2.99 ns). Với 4160 B $=65$ line, chỉ số tập tăng $65\bmod64=1$ mỗi line, nên các line rơi vào 16 tập khác nhau và mỗi bước hit L1: 1.12 ns. 16 line chỉ chiếm 1 KiB nên dung lượng không phải vấn đề; tỉ số là $3.16/1.12=2.8$. Các thời gian phụ thuộc máy và giữ nguyên như đã đo. Chương trình in ra:

```text
stride  4096 B: 3.16 ns per hop
stride  4160 B: 1.12 ns per hop
```

### False sharing và giao thức coherence

Cache line cũng là đơn vị của *coherence* (nhất quán bộ nhớ đệm). Để ghi vào một line, core phải giữ nó ở trạng thái độc quyền; nếu L1d của core khác đang giữ bản sao, lệnh ghi gửi một request-for-ownership (RFO) làm vô hiệu bản sao kia, và line di chuyển giữa các cache. Hai thread tăng hai `int` *khác nhau* nhưng cùng nằm trong một line 64 byte thì không có race, vậy mà gần như mỗi lần ghi đều trả giá chuyển line này: **false sharing**. Drepper (§3.3.4 và §6.4.1, Hình 6.10) đo một tải mà mỗi thread chỉ tăng vị trí nhớ riêng của nó, vậy mà thời gian chạy vẫn tăng theo số thread. Cách khắc phục: cho mỗi thread một line riêng (`alignas(64)`, hoặc `std::hardware_destructive_interference_size`), cộng dồn vào biến cục bộ của thread rồi gộp ở cuối, hoặc dùng cấu trúc riêng cho từng thread. Giá của padding là $64T$ byte cho $T$ bộ đếm thay vì $4T$. Phải kiểm tra padding theo độ căn chỉnh của *địa chỉ cơ sở*: một mảng bị lệch vẫn có thể để các thread lân cận dùng chung line (Bài tập 13).

**Ví dụ.** Hai thread, mỗi thread tăng `std::atomic<long>` của riêng mình $5\times10^7$ lần. Ở `Shared` hai bộ đếm nằm cạnh nhau trong một đối tượng 16 byte (một line); ở `Padded` mỗi bộ đếm được căn 64 byte. Dùng atomic để không bản nào có data race (cùng bản build, hai thread được ghim vào hai lõi hiệu năng bằng `taskset -c 2,4`; cùng chương trình dưới ThreadSanitizer không báo gì). Bản dùng chung chậm hơn bao nhiêu, và cách sửa tốn gì?

```cpp
#include <atomic>
#include <chrono>
#include <cstdio>
#include <functional>
#include <thread>
// Two threads, each incrementing ITS OWN counter 50 million times. No data race, but the counters
// either share a 64-byte line or sit in separate lines.
struct Shared { std::atomic<long> a{0}, b{0}; };
struct Padded { alignas(64) std::atomic<long> a{0}; alignas(64) std::atomic<long> b{0}; };
template <class T>
double run() {
  T c;
  auto bump = [](std::atomic<long>& x) { for (int i = 0; i < 50'000'000; ++i) x.fetch_add(1, std::memory_order_relaxed); };
  auto t0 = std::chrono::steady_clock::now();
  { std::jthread t1(bump, std::ref(c.a)); std::jthread t2(bump, std::ref(c.b)); }
  auto t1 = std::chrono::steady_clock::now();
  return std::chrono::duration<double, std::milli>(t1 - t0).count();
}
int main() {
  std::printf("sizeof(Shared) = %zu, sizeof(Padded) = %zu\n", sizeof(Shared), sizeof(Padded));
  std::printf("same line   : %7.1f ms\n", run<Shared>());
  std::printf("own lines   : %7.1f ms\n", run<Padded>());
}
```

**Lời giải.** Khác biệt duy nhất là line: chậm $1105.6/204.1=5.4$ lần khi hai bộ đếm dùng chung line, vì mỗi lần tăng phải giành line khỏi lõi kia. Cái giá của cách sửa là bộ nhớ, $128$ byte thay vì $16$ (`sizeof(Padded) = 128`). Các thời gian phụ thuộc máy và giữ nguyên như đã đo. Chương trình in ra:

```text
sizeof(Shared) = 16, sizeof(Padded) = 128
same line   :  1105.6 ms
own lines   :   204.1 ms
```

### Vòng lặp bị chặn bởi latency và bởi bandwidth: mô hình thông lượng

Gọi $L$ là latency DRAM, $k$ là số lần nạp cache line đang diễn ra đồng thời (bị giới hạn bởi số ô xử lý miss của phần cứng), và $\beta$ là bandwidth đỉnh tính bằng byte trên ns. Một lần nạp line tốn $L$ và tối đa $k$ lần chồng lên nhau, nên thông lượng line là
$$\text{lines/ns}\le\min\!\left(\frac{k}{L},\ \frac{\beta}{64}\right),\qquad t_{\text{per line}}\ge\max\!\left(\frac{L}{k},\ \frac{64}{\beta}\right).$$
Vòng lặp đuổi theo con trỏ có $k=1$ vì địa chỉ kế tiếp là nội dung của lần tải hiện tại, nên trả $L$ cho mỗi node: 140 ns của danh sách trong bài. Vòng lặp tuần tự được hardware prefetcher nhận ra, sau hai lần miss trở lên theo một mẫu nó nạp trước (stride không đổi cũng được nhận ra, nhưng prefetch không vượt qua ranh giới page) (Drepper, §6.3.1), nên hoạt động như thể $k$ lớn và đạt $64/\beta$. Hai chế độ gặp nhau ở $k^\*=L\beta/64$ line đang bay. Với các giá trị minh họa $L=90$ ns và $\beta=12$ GB/s $=12$ byte/ns, $64/\beta=5{,}33$ ns mỗi line và $k^\*=90/5{,}33=16{,}9$, nên cần hơn 16 lần nạp chồng nhau để bão hòa bus; một core chỉ có 10 ô bị giới hạn ở $L/10=9$ ns mỗi line. Mô hình đơn giản này (bỏ qua TLB miss, thứ cộng thêm vào chi phí danh sách xáo trộn) giải thích vì sao xen kẽ nhiều lần duyệt *độc lập* làm tăng tốc việc duyệt danh sách (Bài tập 14).

![Thời gian mỗi node theo số lần nạp độc lập đang bay, với đường dốc bị chặn bởi latency, giới hạn số ô và sàn bandwidth](/lesson-figures/CPP09-3.svg)

*Hình: mô hình thông lượng với $L=140$ ns, $\beta=16$ B/ns và $M=12$ ô (giá trị minh họa). Phép đuổi con trỏ nằm ở $k=1$ trên đường dốc latency; giới hạn số ô chặn mức giảm ở 11.7 ns, gấp ba lần sàn 4 ns vốn cần $k^\*=35$.*

**Ví dụ.** Mỗi chu trình trong $k$ chu trình xáo trộn 128 MiB được tiến một node mỗi vòng, đồng bộ từng bước; $k$ lần nạp của một vòng không phụ thuộc nhau, nên tối đa $k$ lần miss có thể chồng nhau (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, một lõi hiệu năng của Intel Core i5-12500H, ghim bằng `taskset`). Với $L=126$ ns mỗi node ở $k=1$, mô hình $L/k$ dự đoán gì cho $k=2,3,6$, và các thời gian đo so sánh thế nào?

```cpp
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <numeric>
#include <random>
#include <vector>
// k independent random cycles (128 MiB each) walked in lock-step: every hop reads a new line.
int main() {
  const std::size_t n = 1u << 24;
  std::mt19937_64 g(11);
  std::vector<std::vector<std::size_t>> chain;
  for (int c = 0; c < 6; ++c) {
    std::vector<std::size_t> perm(n), next(n);
    std::iota(perm.begin(), perm.end(), 0);
    std::shuffle(perm.begin(), perm.end(), g);
    for (std::size_t i = 0; i < n; ++i) next[perm[i]] = perm[(i + 1) % n];
    chain.push_back(std::move(next));
  }
  const std::size_t rounds = 3'000'000;
  std::printf("%2s %14s\n", "k", "ns per node");
  for (int k : {1, 2, 3, 6}) {
    std::size_t p[6] = {0, 1, 2, 3, 4, 5};
    auto a = std::chrono::steady_clock::now();
    for (std::size_t r = 0; r < rounds; ++r)
      for (int c = 0; c < k; ++c) p[c] = chain[c][p[c]];
    auto b = std::chrono::steady_clock::now();
    volatile std::size_t sink = p[0] + p[1]; (void)sink;
    std::printf("%2d %14.1f\n", k, std::chrono::duration<double, std::nano>(b - a).count() / (rounds * k));
  }
}
```

**Lời giải.** Ở $k=1$ vòng lặp trả trọn độ trễ, 126 ns mỗi node. Mô hình dự đoán $L/k=126.2/2=63.1,\ 126.2/3=42.1,\ 126.2/6=21.0$ ns cho $k=2,3,6$; các giá trị đo $47.3,\ 32.8,\ 17.6$ ns thấp hơn 16-25 % (ví dụ $1-47.3/63.1=25\%$ và $1-17.6/21.0=16\%$), nên hình dạng (hyperbol theo $k$) đúng còn hằng số thì không: mô hình bỏ qua những hiệu ứng như dịch địa chỉ cũng được chồng lên nhau, và phần của chúng chưa được tách riêng ở đây. Ở $k=6$ vòng lặp nhanh gấp $126.2/17.6=7.2$ lần so với $k=1$ với cùng tổng khối lượng việc. Các thời gian phụ thuộc máy và giữ nguyên như đã đo. Chương trình in ra:

```text
 k    ns per node
 1          126.2
 2           47.3
 3           32.8
 6           17.6
```

Đồ thị dưới đây cho thấy thời gian mỗi cache line theo số lần nạp chồng nhau:

```explore
{
  "title": "Time per cache line against overlapped fetches",
  "title_vi": "Thời gian mỗi cache line theo số lần nạp chồng nhau",
  "prompt": "Predict first: with L = 140 ns, how many independent lists must be walked at once to cut the time per node to a tenth of the single-list time, and does the bandwidth floor matter before that? Then drag M and beta to see which limit binds.",
  "prompt_vi": "Dự đoán trước: với L = 140 ns, cần duyệt đồng thời bao nhiêu danh sách độc lập để thời gian mỗi node giảm còn một phần mười so với một danh sách, và sàn bandwidth có quan trọng trước đó không? Rồi kéo M và beta để xem giới hạn nào chặn.",
  "params": [
    { "name": "L", "label": "DRAM latency L", "label_vi": "độ trễ DRAM L", "min": 40, "max": 250, "step": 5, "value": 140, "unit": "ns" },
    { "name": "beta", "label": "bandwidth beta", "label_vi": "bandwidth beta", "min": 4, "max": 40, "step": 1, "value": 16, "unit": "B/ns" },
    { "name": "M", "label": "slots in flight M", "label_vi": "số ô đang bay M", "min": 1, "max": 32, "step": 1, "value": 12, "unit": "" },
    { "name": "k", "label": "independent lists k", "label_vi": "số danh sách độc lập k", "min": 1, "max": 40, "step": 1, "value": 1, "unit": "" }
  ],
  "let": [
    { "name": "floor", "expr": "64 / beta" },
    { "name": "t", "expr": "max(L / min(k, M), floor)" },
    { "name": "kstar", "expr": "L * beta / 64" }
  ],
  "plot": {
    "x": { "name": "x", "min": 1, "max": 40, "label": "independent lists k", "label_vi": "số danh sách độc lập k" },
    "y": { "label": "time per node (ns)", "label_vi": "thời gian mỗi node (ns)", "min": 0 },
    "series": [
      { "expr": "max(L / min(x, M), floor)", "label": "max(L/min(k,M), 64/beta)", "label_vi": "max(L/min(k,M), 64/beta)", "color": "orange" },
      { "expr": "L / x", "label": "L/k (no slot limit)", "label_vi": "L/k (không giới hạn ô)", "color": "blue" },
      { "expr": "floor", "label": "bandwidth floor", "label_vi": "sàn bandwidth", "color": "green" }
    ],
    "points": [
      { "x": "k", "y": "t", "label": "your k", "label_vi": "k của bạn", "color": "rose" }
    ]
  },
  "readouts": [
    { "label": "time per node", "label_vi": "thời gian mỗi node", "expr": "t", "unit": "ns", "digits": 2 },
    { "label": "bandwidth floor 64/beta", "label_vi": "sàn bandwidth 64/beta", "expr": "floor", "unit": "ns", "digits": 2 },
    { "label": "lists needed for the floor, k*", "label_vi": "số danh sách cần cho sàn, k*", "expr": "kstar", "unit": "", "digits": 1 },
    { "label": "best this hardware can do", "label_vi": "tốt nhất phần cứng này đạt", "expr": "max(L / M, floor)", "unit": "ns", "digits": 2 }
  ]
}
```

### Chi phí khấu hao của `push_back`, và khi hằng số thắng số mũ

Khẳng định "amortized $O(1)$" có một chứng minh ngắn. Cho `vector` nhân đôi dung lượng mỗi khi đầy, bắt đầu từ dung lượng 1. Đẩy $n$ phần tử gây các lần cấp phát lại ở kích thước $1,2,4,\dots,2^j$ với $2^j<n$, mỗi lần sao chép $2^i$ phần tử, nên tổng công việc sao chép là $\sum_{i=0}^{j}2^i=2^{j+1}-1<2n$. Cộng thêm $n$ lần ghi thường, tổng nhỏ hơn $3n$ thao tác phần tử, tức dưới 3 thao tác mỗi lần push trung bình, là $O(1)$. Giả thiết ở đây là hệ số tăng *nhân* (geometric): tăng theo bước cố định $c$ cho tổng công việc $\sum_i ic=\Theta(n^2/c)$ và một vòng lặp bậc hai. Cái giá là bộ nhớ: sau một lần cấp phát lại có thể một nửa dung lượng chưa dùng, và việc sao chép di chuyển mọi phần tử cùng lúc, một đột biến latency đáng kể với deadline thời gian thực (hãy dùng `reserve`). Đây là lập luận chuẩn của các môn nhập môn thuật toán như MIT 6.006.

Tiệm cận so sánh *hình dạng*, không so sánh *giá trị*. Giả sử thuật toán A tốn $a\,n^2$ ns và thuật toán B tốn $b\,n\log_2n$ ns. Chúng cắt nhau tại $n^\*$ với $a\,n^\*=b\log_2n^\*$; nếu B có hằng số lớn, chẳng hạn $b/a=40$, điểm cắt nằm ở chỗ $n=40\log_2n$, gần $n\approx 340$, nên với 100 điểm thuật toán A "tệ hơn" lại thắng, còn với 10.000 điểm B thắng khoảng $10^{8}/(40\cdot10^4\cdot13{,}3)\approx19$ lần. Mô hình bộ nhớ thêm một lý do thứ hai: $a$ và $b$ không phải hằng số mà là hàm bậc thang của working set (các bậc 0,8, 1,6, 3,0, 9,0 ns của Bài tập 15), nên điểm cắt dịch chuyển khi một trong hai thuật toán rời một tầng cache trước. Quy tắc thực hành rút ra: chọn theo tiệm cận khi $n$ sẽ lớn và chưa biết; chọn theo benchmark ở kích thước thật khi $n$ đã biết và vừa phải (vài nghìn phần tử) và các cấu trúc khác nhau về locality. Liên hệ: cùng lập luận này quyết định k-d tree hay nearest neighbour vét cạn trong code perception (container ở CPP05, hình học ở nhánh M), và vì sao `std::sort` chuyển sang insertion sort trên đoạn rất nhỏ.

**Ví dụ.** Chương trình in mỗi lần đổi capacity khi đẩy 1000 số nguyên, đếm số phần tử bị sao chép bởi các lần cấp phát lại, rồi lặp lại vòng lặp sau `reserve(1000)` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, một lõi hiệu năng của Intel Core i5-12500H, ghim bằng `taskset`). Có bao nhiêu lần cấp phát lại và sao chép phần tử, chi phí mỗi push là bao nhiêu so với cận 3, và `reserve` thay đổi gì?

```cpp
#include <cstdio>
#include <vector>
// Watch libstdc++'s growth policy for 1000 push_backs, and the same with reserve(1000).
int main() {
  std::vector<int> v;
  std::size_t cap = v.capacity(), copies = 0, reallocs = 0;
  std::printf("capacity changes:");
  for (int i = 0; i < 1000; ++i) {
    v.push_back(i);
    if (v.capacity() != cap) { copies += v.size() - 1; ++reallocs; cap = v.capacity(); std::printf(" %zu", cap); }
  }
  std::printf("\npush_back x1000: %zu reallocations, %zu element copies (%.2f operations per push, bound 3)\n", reallocs, copies, double(copies + 1000) / 1000);
  std::vector<int> w;
  w.reserve(1000);
  std::size_t c2 = w.capacity(); int changes = 0;
  for (int i = 0; i < 1000; ++i) { w.push_back(i); if (w.capacity() != c2) { ++changes; c2 = w.capacity(); } }
  std::printf("with reserve(1000): %d reallocations\n", changes);
}
```

**Lời giải.** Capacity nhân đôi, $1,2,4,\dots,1024$, qua 11 lần cấp phát lại sao chép $1+2+\dots+512=1023=2^{10}-1$ phần tử, khớp với tổng $2^{j+1}-1$ với $j=9$. Cộng 1000 lần ghi thường được $(1023+1000)/1000=2.02$ phép toán mỗi push, dưới cận 3. Với `reserve` không có lần cấp phát lại nào và không có đỉnh latency trong vòng lặp. Đầu ra mang tính tất định. Chương trình in ra:

```text
capacity changes: 1 2 4 8 16 32 64 128 256 512 1024
push_back x1000: 11 reallocations, 1023 element copies (2.02 operations per push, bound 3)
with reserve(1000): 0 reallocations
```

## Ví dụ có lời giải

### Trường hợp 1: trường hợp cơ bản

**Đề bài.** Cộng $n=4\times10^6$ double lưu (a) trong một `std::vector` và (b) trong một danh sách liên kết có các node được thăm theo thứ tự xáo trộn. Dùng bảng đo được dưới đây (máy này, `-O2`) để tìm chi phí mỗi phần tử của từng cấu trúc, mức chậm đi của danh sách, và số mũ thực nghiệm của mỗi cấu trúc giữa $n=10^5$ và $n=4\times10^6$.

| $n$ | vector (ns/phần tử) | danh sách xáo trộn (ns/phần tử) |
|---|---|---|
| 1,000 | 0.76 | 1.88 |
| 100,000 | 0.77 | 14.4 |
| 4,000,000 | 0.92 | 140 |

**Lời giải.**

1. **Dung lượng chiếm** (mô hình hệ phân cấp bộ nhớ). Một `Node` là 16 byte (một `double` và một con trỏ), nên $4\times10^6\cdot16\ \text{B}=64$ MB; vector giữ $4\times10^6\cdot8\ \text{B}=32$ MB. Cả hai đều vượt quá cache L2 điển hình (hàng trăm KB đến vài MB) và có lẽ cả L3.
2. **Vector.** Thời gian mỗi phần tử hầu như không đổi, 0.76 đến 0.92 ns. Vòng lặp truyền 8 byte mỗi phần tử, nên $8\ \text{B}/0.92\ \text{ns}\approx8.7$ GB/s, một tốc độ streaming điển hình; prefetcher che giấu độ trễ (mô hình thông lượng, $k$ lớn).
3. **Danh sách.** Ở $n=1000$, 16 KB vừa trong L1, nên ngay cả truy cập xáo trộn cũng rẻ (1.88 ns, bị giới hạn bởi các lần nạp phụ thuộc). Ở $10^5$ (1.6 MB) nó tràn khỏi L1/L2 và tốn 14.4 ns. Ở $4\times10^6$ gần như mọi bước nhảy đều miss xuống DRAM: 140 ns, gần với độ trễ DRAM $L$ (trường hợp $k=1$ của mô hình). Mỗi node là một lần nạp line riêng: trong 64 byte nạp vào chỉ 16 được dùng.
4. **Độ chậm.** $140/0.92=152$ lần chậm hơn mỗi phần tử, với cùng $O(n)$.
5. **Số mũ thực nghiệm** (phần chi phí tiệm cận). Tổng thời gian là $t=n\cdot(\text{ns mỗi phần tử})$. Với danh sách, giữa $n=10^5$ và $4\times10^6$: $\dfrac{4\times10^6\cdot140}{10^5\cdot14.4}=389$ khi kích thước tăng 40 lần, nên $p=\ln389/\ln40=1.62$. Với vector: $\dfrac{4\times10^6\cdot0.92}{10^5\cdot0.77}=47.8$, nên $p=\ln47.8/\ln40=1.05$.
6. **Đọc các số mũ.** Vector về cơ bản là tuyến tính. Danh sách ở đây không phải $O(n)$ với hệ số hằng, vì chế độ cache đã đổi giữa hai kích thước.
7. **Amdahl** (phần profiling). Nếu việc duyệt danh sách chiếm 30% một frame và vector làm nó nhanh hơn 100 lần: $S=1/(0.7+0.3/100)=1/0.703=1.42$, nên những thứ khác trong frame mới là điều quan trọng.

**Kiểm tra.** Mỗi line vector tốn $8\cdot0.92=7.4$ ns, tức $64\ \text{B}/7.4\ \text{ns}=8.7$ GB/s, cùng tốc độ như ở bước 2. Một lần chạy Python cho ba kết quả ra `152.2`, `1.617` và `1.048` cho tỉ số và hai số mũ. 140 ns của danh sách cũng khớp với độ trễ đuổi con trỏ $\approx110$ ns đo được cho mảng 64 MiB trong ví dụ về hệ phân cấp bộ nhớ, trong phạm vi khác biệt do TLB và kích thước node.

**Rút ra.** Hai lượt duyệt $O(n)$ chênh nhau 152 lần vì chi phí đơn vị phụ thuộc vào locality, và số mũ thực nghiệm cho thấy điều đó ngay khi dữ liệu rời một tầng cache.

### Trường hợp 2: độ rộng ma trận là lũy thừa của hai (conflict miss)

**Đề bài.** L1d 32 KiB, 8-way, line 64 byte (64 tập). Đọc 8 cột liền kề của ma trận double row-major có 256 hàng, hết cột này đến cột khác, mỗi lượt đi xuống 256 hàng. So sánh $N=1024$ và $N=1032$ double mỗi hàng. Dùng 4 ns cho một L2 hit và 1 ns cho một L1 hit, giả sử thay thế LRU và cache rỗng lúc đầu. Tìm số miss và tổng thời gian cho mỗi độ rộng.

**Lời giải.**

1. **Các line được chạm** (công thức cache line). Cột $c$ của hàng $r$ nằm ở byte $8(rN+c)$. 8 cột liền kề $c=0,\dots,7$ nằm trong cùng line 64 byte với cột 0 khi đầu hàng căn theo line, nên 8 lượt dùng cùng 256 line.
2. **Các tập** (phần set associativity). Tập của line là $\lfloor 8(rN+c)/64\rfloor\bmod64$. Với $N=1024$ bước hàng là $8\cdot1024=8192$ byte $=128$ line và $128\bmod64=0$, nên cả 256 line ánh xạ vào *một* tập có 8 way. Với $N=1032$ bước là $8256$ byte $=129$ line và $129\bmod64=1$: 256 line trải ra cả 64 tập, $256/64=4$ mỗi tập, vừa trong 8 way.
3. **Số miss.** $N=1024$: 256 line riêng biệt quay vòng qua 8 way theo LRU, nên mỗi line bị đẩy ra trước khi dùng lại và cả $8\cdot256=2048$ lần truy cập đều miss. $N=1032$: lượt 1 miss 256 line, lượt 2 đến 8 hit: 256 miss và $2048-256=1792$ hit.
4. **Thời gian.** $N=1024$: $2048\times4\ \text{ns}=8192$ ns. $N=1032$: $256\times4+1792\times1=2816$ ns. Tỉ lệ $8192/2816=2.9$.
5. **Đọc kết quả.** Hai chương trình làm cùng phép tính và chạm cùng số line riêng biệt; đệm mỗi hàng thêm 8 double (một line) loại bỏ độ chậm 2.9 lần. Duyệt các cột theo thứ tự sao cho xung đột tập không xảy ra cùng lúc (blocking hay tiling) loại bỏ vấn đề với mọi $N$.

![Biểu đồ cột của 64 tập cache: 256 line ở tập 0 với N = 1024, bốn line ở mỗi tập với N = 1032](/lesson-figures/CPP09-4.svg)

*Hình: các con số của Trường hợp 2. Biểu đồ bên phải dùng thang dọc khác (0 đến 10) để thấy bốn line mỗi tập so với sức chứa 8 way.*

**Kiểm tra.** Một mô phỏng LRU set-associative bằng Python (64 tập, 8 way, 2048 truy cập theo thứ tự trên) in `(2048, 0)` cho $N=1024$ và `(256, 1792)` cho $N=1032$ dưới dạng (miss, hit), và `8192/2816` là `2.909`. Kiểm tra độc lập bằng đếm: 256 line trong 64 tập là $256/64=4\le8$ với $N=1032$, còn $256>8$ trong một tập với $N=1024$.

**Rút ra.** Dung lượng không phải giới hạn duy nhất: độ dài hàng là lũy thừa của hai có thể khiến một cột tranh nhau một tập duy nhất, và một line đệm là đủ để sửa.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: MIT 6.006, asymptotic analysis problems)* Cho lớp tăng trưởng của từng trường hợp: (a) so sánh mọi cặp trong $n$ điểm lidar; (b) binary search trong một mảng $n$ timestamp đã sắp xếp; (c) `push_back` $n$ phần tử vào một `vector`; (d) sắp xếp $n$ điểm bằng `std::sort`. Với $n=10^5$ hãy so sánh bằng số số phép toán của (a) và (d).
2. **(Dễ)** *(Adapted from: Drepper, What Every Programmer Should Know About Memory, cache line discussion)* Một mảng 2400 `float` được đọc tuần tự, rồi với stride 8 phần tử. Mỗi lượt chạm bao nhiêu cache line 64 byte? Điều đó có nghĩa gì cho thời gian chạy khi mảng không nằm trong cache?
3. **(Dễ)** *(Adapted from: Bryant and O'Hallaron, CS:APP, Amdahl's law)* 45% thời gian của một frame là resize ảnh. Bạn làm nó nhanh hơn 8 lần. Mức tăng tốc tổng thể là bao nhiêu, và mức tốt nhất có thể nếu resize là miễn phí?
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
7. **(Trung bình)** Một đám mây điểm có $4\times10^5$ điểm `{float x, y, z, intensity; uint16_t ring, flags; uint32_t time}` (24 byte). Bạn chỉ cần trung bình của `intensity`. So sánh số byte được truyền từ bộ nhớ với một `std::vector<Point>` AoS và với SoA `std::vector<float> z`. Khi nào sự khác biệt thôi quan trọng?
8. **(Khó)** Bạn đo một hàm tại $n=1000, 2000, 4000, 8000$: $2.0, 8.1, 32.5, 129$ ms. Ước lượng số mũ (bằng tay với các tỉ số, rồi với công thức bình phương tối thiểu), nêu độ phức tạp có khả năng, và dự đoán thời gian tại $n=10^5$. Nêu hai lý do dự đoán có thể sai.
9. **(Khó)** Một profile của một perception node cho thấy (số liệu minh họa): tìm kiếm láng giềng gần nhất 55%, serialization point cloud 20%, voxel filter 15%, còn lại 10%. Tính mức tăng tốc tổng thể tối đa cho (i) làm tìm kiếm nhanh hơn 5 lần, (ii) làm serialization nhanh hơn 100 lần. Làm cái nào trước? Bạn sẽ kiểm tra gì trước khi viết code?
10. **(Khó)** Một particle filter có 5000 hạt `{x, y, theta, weight}` mỗi hạt 32 byte (có đệm). Chuẩn hóa trọng số chỉ đọc `weight`. SoA có đáng không? Tính dung lượng chiếm, bàn về kích thước cache, và mô tả benchmark sẽ quyết định, kể cả cách bạn thay đổi $N$.
11. **(Mini-project)** Chạy benchmark của bài này trên máy bạn cho $n=10^3,10^5,4\times10^6$; thêm một phép cộng có stride (stride 8 double) làm cột thứ tư; khớp `loglog_slope` giữa hai kích thước lớn nhất cho từng cột; báo cáo kích thước cache của bạn (`lscpu`) và giải thích mỗi đường cong bị bẻ cong ở đâu.

12. **(Challenge)** Một cache L1d 32 KiB, 8-way, line 64 byte. Một ma trận double row-major $4096\times N$ được đọc xuống theo một cột. (a) Suy ra chỉ số tập của phần tử ở hàng $r$ và tính, với $N=2048$, $2056$ và $2080$, cột chạm bao nhiêu tập khác nhau và bao nhiêu line của nó có thể ở lại cùng lúc. (b) Giải thích vì sao cột $N=2048$ hành xử như một cache 8 line dù cột có 4096 line. (c) Padding $p$ nhỏ nhất (tính bằng double) cộng vào $N=2048$ để cột dùng cả 64 tập là bao nhiêu, và 4096 hàng được trải đều đến mức nào? (adapted from Drepper, *What Every Programmer Should Know About Memory*, §3.3.1 and §6.2.1, Figure 6.5)
13. **(Challenge)** Tám thread mỗi thread tăng bộ đếm 4 byte riêng, lưu trong một `int counters[]` với stride $s$ int giữa bộ đếm của các thread lân cận. (a) Với địa chỉ cơ sở căn 64 byte, hãy cho $s=1,2,4,8,16$ số line được dùng, số thread tối đa chung một line, và bộ nhớ dùng. (b) Lặp lại cho địa chỉ cơ sở nằm sau ranh giới line 36 byte. (c) $s$ nào loại bỏ false sharing ở cả hai trường hợp, và cái giá là gì? (d) Nêu một thiết kế tránh hoàn toàn padding. (adapted from Drepper, §3.3.4 and §6.4.1, Figure 6.10)
14. **(Challenge)** Dùng mô hình thông lượng của bài với $L=90$ ns, $\beta=12$ byte/ns, line 64 byte và tối đa $M=10$ line đang bay. Một chương trình duyệt $k$ danh sách xáo trộn độc lập đồng bộ từng bước (mỗi vòng một node của mỗi danh sách). (a) Cho thời gian mỗi node với $k=1,2,4,8,10,16$. (b) $k$ nhỏ nhất đạt tới giới hạn bandwidth nếu $M$ không giới hạn là bao nhiêu, và vì sao máy này không bao giờ đạt được? (c) Nêu hai hiệu ứng mô hình bỏ qua khiến phép đo thật khác đi. (source: Drepper, §3.3.2 and §6.3.1; the numeric values are illustrative)
15. **(Challenge)** Thời gian tổng hợp: $t(n)=n\cdot c(n)$ với $n=2^{10},2^{11},\dots,2^{22}$ double, với chi phí mỗi phần tử $c=0{,}8$ ns khi mảng $\le32$ KiB, $1{,}6$ ns đến 1 MiB, $3{,}0$ ns đến 32 MiB và $9{,}0$ ns vượt quá. (a) Khớp số mũ trên cả 13 kích thước, trên bốn kích thước đầu và trên bốn kích thước cuối. (b) Số mũ cục bộ qua riêng bước từ $n=2^{12}$ đến $2^{13}$ là bao nhiêu? (c) Dùng đường khớp toàn bộ để dự đoán $t(2^{24})$ và so với mô hình. (d) Nêu quy tắc chọn khoảng khớp. (source: Drepper, §3.3.2, working-set measurements; the cost steps are illustrative)

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
2. Tuần tự: $2400\cdot4/64=150$ line (chính xác, từ địa chỉ gốc căn theo line). Stride 8 float (32 byte): phần tử 0, 8, ..., 2392: 300 phần tử, hai phần tử mỗi line, nên lại là 150 line. Lượt có stride thực hiện ít lần đọc hơn một nửa nhưng nạp cùng số line, nên khi dữ liệu không nằm trong cache thời gian chạy của nó xấp xỉ lượt tuần tự: thời gian bộ nhớ đi theo line, không theo phần tử.
3. $S=1/(0.55+0.45/8)=1/0.60625=1.65$. Tốt nhất có thể khi resize miễn phí: $1/0.55=1.82$.
4. Một câu trả lời tốt: (1) cache line: mỗi lần nạp node của danh sách lấy một line 64 byte nhưng chỉ dùng 16 byte (giá trị 8 byte cộng con trỏ 8 byte), trong khi vector dùng cả 64 byte của mỗi line nó nạp; (2) prefetching: địa chỉ của vector dự đoán được, nên phần cứng nạp trước và vòng lặp chạy ở băng thông streaming (0.92 ns, khoảng 8.7 GB/s), nhưng địa chỉ kế tiếp của danh sách xáo trộn phụ thuộc vào lần nạp trước; (3) độ trễ: với 64 MB node, mọi bước nhảy đều miss xuống DRAM, tốn khoảng 140 ns, gần với độ trễ DRAM; (4) bằng chứng: ở $n=1000$ (16 KB trong cache) tỉ số chỉ là 2.5, và nó tăng lên 19 ở $10^5$ và 152 ở $4\times10^6$ khi dữ liệu rời khỏi các cache.
5. Khiếm khuyết: (1) bản build `-O0`, đo code chưa tối ưu; (2) việc cấp phát và khởi tạo vector nằm trong vùng được đo; (3) `s` không bao giờ được dùng, nên bản build tối ưu có thể xóa vòng lặp; (4) một lần chạy, không warm-up hay lặp lại; (5) tổng thời gian thay vì ns mỗi phần tử, nên không so sánh được qua các $n$; (6) chỉ một kích thước, nên không có thông tin về mở rộng hay cache. Cách sửa: build với `-O2`, cấp phát bên ngoài bộ đếm giờ, lưu kết quả vào một `volatile` hoặc in ra, lặp 10-1000 lần và báo cáo median theo ns/phần tử cho nhiều kích thước.
6. Ma trận có $4096^2\cdot8/64=2{,}097{,}152$ line. Theo từng hàng: mỗi line được nạp một lần: khoảng $2.1\times10^6$ lần nạp. Theo từng cột: mọi truy cập vào một line khác, và line bị loại bỏ trước khi các phần tử lân cận của nó được dùng: $4096^2=16{,}777{,}216$ lần nạp, nhiều hơn 8 lần (một lần mỗi phần tử thay vì một lần mỗi 8 phần tử).
7. AoS truyền mọi line: $4\times10^5\cdot24=9.6$ MB (150,000 line). SoA chỉ đọc `intensity`: $4\times10^5\cdot4=1.6$ MB (25,000 line), hệ số 6. Sự khác biệt quan trọng khi dữ liệu không vừa trong cache; khi cả mảng vừa trong L2/L3 (giả sử $10^4$ điểm = 240 KB), AoS và SoA chạy với tốc độ tương tự.
8. Các tỉ số: $8.1/2.0=4.05$, $32.5/8.1=4.01$, $129/32.5=3.97$, mỗi cái gần $4=2^2$, nên $p\approx2$. Bình phương tối thiểu cho $p\approx2.004$. Nhiều khả năng là thuật toán bậc hai (vòng lặp lồng nhau, khoảng cách từng cặp ngây thơ). Dự đoán tại $n=10^5$: $2.0\ \text{ms}\cdot(100)^2=20{,}000$ ms, khoảng 20 s. Có thể sai vì: dữ liệu rời khỏi cache ở $n$ lớn hơn (số mũ tăng), và một số hạng bậc hai có thể che các số hạng bậc thấp hơn hoặc có sự thay đổi chế độ thuật toán (ví dụ một ngưỡng hay hành vi cấp phát bộ nhớ).
9. (i) $S=1/(0.45+0.55/5)=1/0.56=1.79$. (ii) $S=1/(0.8+0.2/100)=1/0.802=1.25$. Tối ưu tìm kiếm trước. Trước khi viết code: kiểm tra bằng một phép đo thứ hai (bộ đếm giờ thủ công hoặc `perf`) rằng profile là đại diện, rằng đó là bản build tối ưu, và liệu một thay đổi thuật toán (k-d tree hoặc voxel hash thay vì brute force) có thắng việc tinh chỉnh vi mô không.
10. Dung lượng chiếm: $5000\cdot32=160$ KB, vừa thoải mái trong L2 (thường 256 KB đến 2 MB), nên SoA nhiều khả năng cho lợi ích nhỏ. Benchmark: đo thời gian chuẩn hóa cho $N=10^3$ đến $10^7$ ở cả hai bố cục, báo cáo ns mỗi hạt, và tìm điểm gãy nơi AoS (32 B cho mỗi lần đọc weight) rời cache sớm hơn SoA (8 B cho mỗi weight); quyết định dựa trên kích thước bạn thực sự chạy, không phải kích thước lớn nhất. Một câu trả lời tốt kết luận "giữ AoS cho 5000 hạt trừ khi profiling cho thấy nó quan trọng, chuyển nếu $N$ tăng đến hàng triệu".
11. Một câu trả lời tốt gồm: một bảng bốn cột với ba kích thước; một cột stride gần với vector ở $n$ nhỏ nhưng tiến tới chi phí cache miss mỗi phần tử khi stride $\ge8$ double và dữ liệu lớn (mỗi lần đọc là một line mới); độ dốc gần 1 cho vector (1.0-1.1) và lớn hơn (khoảng 1.5-1.7 giữa hai kích thước cuối) cho danh sách xáo trộn trong vùng chuyển tiếp; và một nhận xét rằng mỗi chỗ bẻ cong khớp với dung lượng L1/L2/L3 từ `lscpu`.
12. (a) Hàng $r$ bắt đầu ở byte $8Nr$, nên tập là $\lfloor 8Nr/64\rfloor \bmod 64$. Với $N=2048$: bước $d=256\bmod64=0$, nên 1 tập khác nhau và tối đa $1\cdot8=8$ line ở lại. Với $N=2056$: $d=257\bmod64=1$, $\gcd(1,64)=1$, nên 64 tập và $512$ line. Với $N=2080$: $d=260\bmod64=4$, $64/\gcd(4,64)=16$ tập và $128$ line. (Tính bằng cách liệt kê cả 4096 hàng: 1, 64 và 16 tập khác nhau.) (b) Với $N=2048$ mỗi hàng cách hàng trước đúng 256 line, và $256\equiv0\pmod{64}$, nên cả 4096 line ánh xạ vào một tập có 8 way. Đi xuống cột làm một line bị đẩy ra trước khi cột kế tiếp (các phần tử nằm trong cùng các line, 8 double mỗi line) dùng lại được, nên mọi truy cập đều miss xuống L2 dù 256 KiB line của cột sẽ vừa trong nhiều bố cục khác. (c) Hàng $r$ bắt đầu ở byte $8(2048+p)r$. Liệt kê $p=0,\dots,9$: $p=0$ cho 1 tập (cả 4096 hàng trong đó); mọi $p$ từ 1 đến 9 cho cả 64 tập với đúng $4096/64=64$ hàng mỗi tập. Vậy padding nhỏ nhất là $p=1$ double (8 byte); trong thực tế dùng $p=8$ (một line), cũng giữ mỗi hàng căn 64 byte.
13. (a) Bộ đếm $t$ ở byte $4st$; line $=\lfloor4st/64\rfloor$. Cơ sở căn: $s=1$: 1 line, 8 thread chung, 32 byte. $s=2$: 1 line, 8 thread chung, 64 byte. $s=4$: 2 line, 4 thread chung, 128 byte. $s=8$: 4 line, 2 thread chung, 256 byte. $s=16$: 8 line, 1 thread, 512 byte. (b) Với độ lệch 36: $s=1$: 2 line, 7 thread chung; $s=2$: 2 line, 4 thread chung; $s=4$: 3 line, 4 thread chung; $s=8$: 5 line, 2 thread chung; $s=16$: 8 line, 1 thread chung (tính bằng script). (c) $s=16$ int (64 byte) là stride nhỏ nhất loại bỏ chia sẻ ở cả hai độ căn chỉnh, vì các bộ đếm cách nhau 64 byte không bao giờ nằm trong cùng một line 64 byte. Giá: $8\cdot64=512$ byte thay vì 32, gấp 16 lần (và bộ đếm đầu/cuối vẫn có thể chung line với dữ liệu không liên quan ở trước hoặc sau mảng trừ khi bản thân mảng được `alignas(64)` và đệm). (d) Mỗi thread cộng dồn vào biến cục bộ (thanh ghi hoặc stack riêng, nằm trên line riêng) và ghi kết quả một lần ở cuối (hoặc reduction sau `join`), nên không có ghi chung trong vòng lặp.
14. (a) Với $64/\beta=64/12=5{,}33$ ns, $t=\max(L/\min(k,M),\,5{,}33)$: $k=1$: 90 ns; $k=2$: 45; $k=4$: 22,5; $k=8$: 11,25; $k=10$: 9; $k=16$: 9 (10 ô đã bão hòa). (b) $k^\*=L\beta/64=90/5{,}33=16{,}9$, nên cần $k=17$ danh sách đang bay; máy có $M=10<17$, nên vẫn bị giới hạn bởi latency ở $9$ ns mỗi node, gấp 1,7 lần giới hạn bandwidth 5,33 ns, và máy có $M$ không giới hạn sẽ ngừng cải thiện ở $k=17$. (c) Ví dụ: TLB miss (mỗi node ở page mới thêm một page-walk), hiệu ứng page/bank của DRAM, chi phí quản lý vòng lặp phụ và áp lực thanh ghi khi có nhiều danh sách, giới hạn của các đơn vị prefetch và bandwidth dùng chung với core khác.
15. (a) Khớp $\ln t$ theo $\ln n$ cho $p=1{,}182$ trên cả 13 kích thước, $1{,}300$ trên bốn kích thước đầu ($2^{10}..2^{13}$, gồm bước L1 sang L2) và $1{,}000$ trên bốn kích thước cuối ($2^{19}..2^{22}$, đều trong chế độ 3,0 ns). Trong mỗi chế độ chi phí không đổi độ dốc đúng bằng 1,000. (b) Từ $2^{12}$ (0,8 ns, 32 KiB) đến $2^{13}$ (1,6 ns, 64 KiB): $t$ tăng $2\cdot(1{,}6/0{,}8)=4$ lần với tỉ lệ kích thước 2, nên số mũ cục bộ là $\ln4/\ln2=2{,}0$. (c) Ngoại suy đường khớp toàn bộ đến $n=2^{24}$ (128 MiB) dự đoán $0{,}53$ giá trị mô hình $2^{24}\cdot9{,}0$ ns, đánh giá thấp hệ số $1{,}9$, vì dữ liệu rời tầng cache cuối giữa $2^{22}$ và $2^{24}$ và đường khớp chưa từng thấy chế độ đó. (d) Chỉ khớp trong một chế độ (không có ranh giới cache trong khoảng), với ít nhất bốn kích thước, và chỉ ngoại suy trong cùng chế độ. Ghi ranh giới các chế độ (từ `lscpu`) cạnh độ dốc.

## Đọc thêm

- [Drepper: What Every Programmer Should Know About Memory](https://lwn.net/Articles/250967/) - bản mô tả chi tiết kinh điển về cache, độ trễ và mẫu truy cập.
- [Linux perf Tutorial](https://perf.wiki.kernel.org/index.php/Tutorial) - `perf stat`, `perf record` và `perf report` kèm ví dụ.
- [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/) - phân tích độ phức tạp, cấu trúc dữ liệu, và bài tập.
- [Drepper (bản PDF): What Every Programmer Should Know About Memory](https://www.akkadia.org/drepper/cpumemory.pdf) - các mục 3.3.1 (associativity), 6.2.1 (conflict miss của L1d), 6.3.1 (hardware prefetching) và 6.4.1 (false sharing) là cơ sở của phần lý thuyết được thêm.

**Thực hành thêm:** [hướng dẫn người dùng Google Benchmark](https://github.com/google/benchmark/blob/main/docs/user_guide.md) (viết một benchmark cho mỗi container), các bài tập về phân tích tiệm cận trong [MIT 6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/), [trang labs của CS:APP](https://csapp.cs.cmu.edu/3e/labs.html) (Cache Lab chính là bài tập locality của bài này), [What Every Programmer Should Know About Memory](https://www.akkadia.org/drepper/cpumemory.pdf) của Drepper, và [perf tutorial](https://perf.wiki.kernel.org/index.php/Tutorial) / [các ví dụ perf của Brendan Gregg](https://www.brendangregg.com/perf.html) để profile benchmark của bạn.
