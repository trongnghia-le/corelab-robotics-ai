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

Hãy xem một phiên debug như một cuộc điều tra của cảnh sát với ba loại bằng chứng. Sanitizer là camera an ninh lắp sẵn: nó chỉ ghi những tội cụ thể mà nó được thiết kế để theo dõi (truy cập ngoài phạm vi, dùng sau khi giải phóng), nhưng ghi đúng thời điểm chúng xảy ra, kèm địa chỉ và call stack. Debugger là thám tử đi qua hiện trường sau sự việc: nó cho thấy trạng thái của mọi thứ, nhưng chỉ tại những điểm bạn bảo nó dừng. Test là mệnh lệnh thường trực: "khi đầu vào này đến, đầu ra này phải đi ra", được kiểm tra tự động mãi mãi.

Ví dụ robot đời thường: một bộ lọc vận tốc thỉnh thoảng cho ra một gai nhọn mỗi giờ. Ring buffer là một mảng thường, cái gai là giá trị nằm ở ô sau ô cuối, và robot "chạy được" hàng tháng vì vùng nhớ kế bên thường bằng 0. Nhìn chằm chằm vào đồ thị gai không tìm ra điều đó; một bản build AddressSanitizer của cùng code chỉ ra đúng dòng ngay lần đầu chỉ số vượt phạm vi, và một regression test với cửa sổ tính tay giữ cho nó không quay lại.

**Hãy dự đoán trước khi tính.** Trung bình trượt của `{1,2,3,4,5}` với cửa sổ 2 in `3 4.5 6 4.5` thay vì `1.5 2.5 3.5 4.5`. Trước khi đọc báo cáo sanitizer, hãy đoán mỗi cửa sổ cộng bao nhiêu phần tử. Giá trị đầu 3 là $(1+2+3)/2$, nên ba phần tử đã được cộng và ước số vẫn là 2; chỉ một con số của cận vòng lặp đã đổi. Hãy để ý rằng bạn đến được giả thuyết này chỉ từ đầu ra, và việc của sanitizer là xác nhận nó, không phải thay thế việc suy nghĩ.

**Trực giác sai thường gặp** là chương trình không crash thì đúng, và "nó chạy với debugger hoặc ở Release" là bằng chứng về lỗi. Hành vi không xác định không có nghĩa vụ phải crash: một lần đọc ngoài phạm vi trả về bất cứ thứ gì đang ở đó, và cửa sổ cuối của ví dụ thậm chí in đúng số một cách tình cờ. Tương tự, lỗi biến mất khi bạn thêm `printf` hoặc bật tối ưu hóa không hề mất; nó chỉ chuyển chỗ. Cách chữa là làm cho lỗi tất định và nhỏ trước (rút gọn đầu vào, cố định seed), rồi dùng công cụ quan sát trực tiếp thao tác sai.

![Vòng debug sáu bước từ lần chạy lỗi tới regression test, và bốn công cụ cùng loại lỗi mỗi công cụ tìm ra](/lesson-figures/CPP08.svg)

*Hình: tái hiện, thu nhỏ, định vị bằng công cụ khớp với câu hỏi, sửa, rồi khóa bản sửa bằng regression test và chạy lại dưới các sanitizer. Bước 3 là nơi duy nhất việc chọn công cụ có ý nghĩa.*

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

**Ví dụ.** Ba chương trình một file của một bộ điều khiển robot, mỗi chương trình có một lỗi im lặng, chạy dưới công cụ mà bảng gán cho nó (g++ 11.4, Valgrind 3.18):

```
$ g++ -std=c++20 -g -fsanitize=address ovf.cpp -o ovf_a && ./ovf_a    # ticks += 2000000000 twice on an int
-294967296
$ g++ -std=c++20 -g -fsanitize=undefined ovf.cpp -o ovf_u && ./ovf_u
ovf.cpp:5:9: runtime error: signed integer overflow: 2000000000 + 2000000000 cannot be represented in type 'int'
-294967296
$ g++ -std=c++20 -g -fsanitize=address uaf.cpp -o uaf_a && ./uaf_a    # delete gain; then print *gain
==316859==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010 ...
$ g++ -std=c++20 -g -fsanitize=undefined uaf.cpp -o uaf_u && ./uaf_u
1.17263e-313
$ g++ -std=c++20 -g -O0 uninit.cpp -o uninit && valgrind -q ./uninit  # double offset; if (offset > 0.1)
==316884== Conditional jump or move depends on uninitialised value(s)
==316884==    at 0x1091A2: main (uninit.cpp:4)
```

Bộ đếm encoder tràn mà ASan không báo gì, vì không có vùng nhớ nào bị chạm sai; UBSan nêu đúng dòng. Use-after-free thì ngược lại: UBSan không thấy gì sai với một lần đọc số nguyên hay con trỏ, còn ASan báo địa chỉ đã giải phóng (và giá trị in ra `1.17263e-313` cho thấy vùng nhớ cũ đã được dùng lại). `double` chưa khởi tạo được Valgrind tìm ra, không sanitizer nào thấy. Ghép triệu chứng với công cụ là tra bảng, không phải đoán mò.

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

**Ví dụ.** Một driver lidar cắt 90 giá trị khoảng cách (`std::vector<float> ranges(90, 12.0f)`) bằng vòng lặp `for (i = 0; i <= ranges.size(); ++i)`. Những dòng đầu của báo cáo thật (địa chỉ được rút gọn):

```
==...==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5130000001a8 ...
READ of size 4 at 0x5130000001a8 thread T0
    #0 0x... in clip(std::vector<float, std::allocator<float> >&, float) lidar.cpp:4
    #1 0x... in main lidar.cpp:8
0x5130000001a8 is located 0 bytes to the right of 360-byte region [0x513000000040,0x5130000001a8)
```

Loại lỗi: heap-buffer-overflow. Cái gì: một lần READ cỡ 4, một `float`. Ở đâu: `clip`, dòng 4, được gọi từ `main` dòng 8. Đối tượng nào: cách 0 byte về bên phải một vùng 360 byte, tức $360/4=90$ float, nên chỉ số 90 đã được đọc, phần tử đầu tiên sau cuối. Cận vòng lặp `<=` phải là `<`.

### Những điều cốt yếu của debugger

`gdb ./prog`, rồi `run`, `bt` (backtrace), `frame N`, `info locals`, `print expr`, `break file:line`, `watch var`, `continue`, `next`, `step`. Chế độ batch: `gdb -batch -ex run -ex bt ./prog`. Với crash bên trong một library, `bt` vẫn cho thấy frame gọi của bạn. Một `std::unique_ptr` đã bị move hiện ra là `get() = 0x0` trong GDB, giải thích ngay một segmentation fault tại phép dereference đó.

**Ví dụ.** Một hàm tra cứu trả `nullptr` cho một sensor id không biết và nơi gọi dereference nó. GDB chế độ batch trên bản build `-g -O0`:

```cpp
struct Sensor { int id; double rate_hz; };
const Sensor* find(const std::vector<Sensor>& v, int id) {
  for (const Sensor& s : v) if (s.id == id) return &s;
  return nullptr;
}
// main: sensors = {{1, 100.0}, {2, 50.0}};  const Sensor* s = find(sensors, 3);  std::cout << s->rate_hz;
```

```
$ g++ -std=c++20 -g -O0 nul.cpp -o nul && gdb -batch -ex run -ex bt -ex 'info locals' ./nul
Program received signal SIGSEGV, Segmentation fault.
0x0000555555555422 in main () at nul.cpp:11
11	  std::cout << s->rate_hz << "\n";
#0  0x0000555555555422 in main () at nul.cpp:11
sensors = std::vector of length 2, capacity 2 = {{id = 1, rate_hz = 100}, {id = 2, rate_hz = 50}}
s = 0x0
```

`bt` cho dòng crash (`nul.cpp:11`), `info locals` cho thấy `s = 0x0`: `find(sensors, 3)` không tìm thấy sensor 3, vì chỉ có id 1 và 2. Chỗ sửa nằm ở nơi gọi (kiểm tra con trỏ, hoặc trả `std::optional`), không phải ở chỗ dereference.

### Test harness và regression test

Một test là một khẳng định có thể thực thi: *với đầu vào X, kết quả là Y*. Một harness cho nó cấu trúc: test có tên, trạng thái độc lập, thông báo lỗi hiện giá trị mong đợi và giá trị thực, một bản tóm tắt và mã thoát khác không khi thất bại để CI nhận ra. Test tốt

- dùng các giá trị mong đợi tính bằng tay (không phải hàm đang được kiểm thử, vì như vậy chỉ chứng minh nó bằng chính nó);
- bao phủ biên (rỗng, một phần tử, cửa sổ bằng độ dài, số không), ca điển hình và ca lỗi;
- kiểm tra bất biến và tính chất (cửa sổ 1 là phép đồng nhất; độ dài kết quả là $n-w+1$);
- mang tính xác định (seed cố định, đồng hồ cố định) và độc lập với nhau.

Một **regression test** ghi lại một bug đã tìm ra: nó fail trên code hỏng và pass trên code đã sửa. Viết nó *trước* khi sửa chứng minh rằng nó phát hiện được bug.

Với so sánh số thực dùng dung sai: `|a - b| <= tol` là sai khi một trong hai giá trị là NaN, đó là cách an toàn; `!(|a-b| > tol)` sẽ chấp nhận NaN.

**Ví dụ.** Một bộ giới hạn lệnh động cơ `saturate(v, lo, hi)` trả `lo` thay vì `hi` khi vượt giới hạn trên. Bốn kỳ vọng tính tay trong một harness macro 10 dòng, in giá trị mong đợi và giá trị thực rồi trả mã thoát khác 0:

```cpp
#include <cmath>
#include <cstdlib>
#include <iostream>
// saturate v into [lo, hi]  (BUG: the upper branch returns lo)
double saturate(double v, double lo, double hi) {
  if (v < lo) return lo;
  if (v > hi) return lo;
  return v;
}
static int failures = 0;
#define EXPECT_NEAR(got, want, tol)                                                    \
  do { const double g = (got), w = (want);                                             \
       if (!(std::fabs(g - w) <= (tol))) { ++failures;                                 \
         std::cerr << "FAIL line " << __LINE__ << ": " #got " = " << g                 \
                   << ", expected " << w << "\n"; } } while (0)
int main() {
  EXPECT_NEAR(saturate(0.4, -1.0, 1.0), 0.4, 1e-12);    // inside
  EXPECT_NEAR(saturate(-3.0, -1.0, 1.0), -1.0, 1e-12);  // below
  EXPECT_NEAR(saturate(2.5, -1.0, 1.0), 1.0, 1e-12);    // above
  EXPECT_NEAR(saturate(1.0, -1.0, 1.0), 1.0, 1e-12);    // exactly on the limit
  std::cout << (failures ? "FAILED" : "all passed") << "\n";
  return failures ? EXIT_FAILURE : EXIT_SUCCESS;
}
```

```
$ g++ -std=c++20 -Wall -Wextra sat.cpp -o sat && ./sat; echo "exit $?"
FAIL line 19: saturate(2.5, -1.0, 1.0) = -1, expected 1
FAILED
exit 1
$ sed 's/if (v > hi) return lo;/if (v > hi) return hi;/' sat.cpp > sat2.cpp     # the fix
$ g++ -std=c++20 -Wall -Wextra sat2.cpp -o sat2 && ./sat2; echo "exit $?"
all passed
exit 0
```

Lần chạy lỗi nêu đúng ca (`2.5` phải bị chặn về `1.0`), và bản đã sửa thì qua. Test này sẽ lỗi mà không cần sanitizer nào và cả trong build Release, vì nó kiểm tra giá trị.

### Rút gọn và chia đôi

Nếu một thất bại cần $N$ phần tử và một thủ phạm duy nhất, việc chia đôi đầu vào tìm ra nó trong $\lceil\log_2 N\rceil$ lần chạy. Khi thất bại cần nhiều phần tử, delta debugging loại bỏ từng khối và giữ lại mọi lần loại bỏ mà vẫn còn thất bại. Với lịch sử, `git bisect` tìm kiếm nhị phân trên các commit: 1000 commit cần tối đa $\lceil\log_2 1000\rceil=10$ lần build. Với thất bại hiếm, số lần lặp cần để thấy một thất bại có xác suất $p$ với độ tin cậy $1-\alpha$ là $n\ge\ln\alpha/\ln(1-p)$.

**Ví dụ.** Một regression cấu hình nằm đâu đó trong 48 commit: `cfg` giữ `gain=1` cho đến commit 31 thì đổi. `git bisect run` với một script kiểm tra file tìm ra nó sau 6 lần chạy test, $\lceil\log_2 48\rceil=6$:

```
$ git bisect start HEAD <first-commit>      # 48 commits; cfg holds "gain=1" until the bug lands
Bisecting: 23 revisions left to test after this (roughly 5 steps)
$ git bisect run ./test.sh                  # test.sh:  grep -q 'gain=1' cfg
running  './test.sh'
Bisecting: 11 revisions left to test after this (roughly 4 steps)
running  './test.sh'
Bisecting: 5 revisions left to test after this (roughly 3 steps)
running  './test.sh'
Bisecting: 2 revisions left to test after this (roughly 2 steps)
running  './test.sh'
Bisecting: 0 revisions left to test after this (roughly 1 step)
running  './test.sh'
Bisecting: 0 revisions left to test after this (roughly 0 steps)
running  './test.sh'
<hash> is the first bad commit              # commit c31
```

Mỗi lần chạy giảm đôi khoảng tìm (còn 23, 11, 5, 2, 0 revision), nên 48 commit tốn 6 lần build thay vì tới 47. Dòng "roughly N steps" là ước lượng của chính git và đếm số bước còn lại.

Cần lặp bao nhiêu lần để lộ một lỗi hiếm? Đường cong $1-(1-p)^n$ cho thấy (kéo thanh trượt của $p$):

```explore
{
  "title": "How many repeats to see a rare failure?",
  "title_vi": "Cần lặp bao nhiêu lần để thấy một lỗi hiếm?",
  "prompt": "Predict first: if a test fails 6 times in 100 runs, is 50 runs enough to be 95% sure of seeing a failure? Then check with the slider and find the failure rate for which 20 runs are enough.",
  "prompt_vi": "Dự đoán trước: nếu một test lỗi 6 lần trong 100 lần chạy, 50 lần chạy có đủ để chắc chắn 95% thấy một lỗi không? Sau đó kiểm tra bằng thanh trượt và tìm tỉ lệ lỗi mà 20 lần chạy là đủ.",
  "params": [
    { "name": "pp", "label": "failure probability per run p", "label_vi": "xác suất lỗi mỗi lần chạy p", "min": 0.5, "max": 50, "step": 0.5, "value": 6, "unit": "%" }
  ],
  "let": [
    { "name": "q", "expr": "pp/100" },
    { "name": "n95", "expr": "ceil(ln(0.05)/ln(1-q))" },
    { "name": "n99", "expr": "ceil(ln(0.01)/ln(1-q))" }
  ],
  "plot": {
    "x": { "name": "n", "min": 0, "max": 200, "label": "repeated runs n", "label_vi": "số lần chạy lặp n" },
    "y": { "label": "P(at least one failure) (%)", "label_vi": "P(thấy ít nhất một lỗi) (%)", "min": 0, "max": 100 },
    "series": [
      { "expr": "100*(1-(1-q)^n)", "label": "1 - (1-p)^n", "label_vi": "1 - (1-p)^n", "color": "blue" },
      { "expr": "95", "label": "95 % target", "label_vi": "mục tiêu 95 %", "color": "grey" }
    ],
    "points": [
      { "x": "n95", "y": "100*(1-(1-q)^n95)", "label": "runs for 95 %", "label_vi": "số lần cho 95 %", "color": "green" }
    ]
  },
  "readouts": [
    { "label": "runs for 95 % confidence", "label_vi": "số lần chạy cho độ tin cậy 95 %", "expr": "n95", "unit": "", "digits": 0 },
    { "label": "runs for 99 % confidence", "label_vi": "số lần chạy cho độ tin cậy 99 %", "expr": "n99", "unit": "", "digits": 0 }
  ]
}
```

### AddressSanitizer quyết định thế nào: shadow memory và phép kiểm tra truy cập

Đọc báo cáo dễ hơn khi bạn biết cái gì tạo ra nó. AddressSanitizer thay `malloc` và `free`, bao quanh mỗi allocation bằng các **redzone** bị poison, đặt bộ nhớ đã giải phóng vào một **quarantine** (cũng bị poison) để con trỏ cũ vẫn bị bắt trong một thời gian, và compiler viết lại mọi load và store thành "kiểm tra rồi truy cập" (AddressSanitizer wiki, *AddressSanitizerAlgorithm*, "Short version"). Cấu trúc dữ liệu làm phép kiểm tra rẻ là **shadow memory**: mỗi từ 8 byte căn hàng của bộ nhớ ứng dụng có một byte shadow.

Ánh xạ trên Linux 64-bit là $\text{Shadow}=(\text{Mem}\gg3)+\texttt{0x7fff8000}$ (cùng wiki, "Mapping"). Vì `malloc` trả về khối căn hàng 8 byte, chỉ phần đuôi của một allocation mới có từ hợp lệ một phần, nên một byte shadow nhận một trong ít giá trị: $0$ nếu cả 8 byte đều truy cập được, một giá trị âm nếu không byte nào truy cập được (các mã âm khác nhau nêu lý do, ví dụ redzone của heap), và $k\in\{1,\dots,7\}$ nếu chỉ $k$ byte đầu truy cập được. Với `malloc(13)` ở địa chỉ căn hàng, hai từ có shadow $0$ và $5$, vì $13=8+5$. Một lần chạy thật xác nhận điều này: báo cáo của một lần đọc sai cạnh khối 13 byte hiện hàng shadow `fa fa 00 [05] fa fa ...`, trong đó `fa` đánh dấu redzone của heap.

Truy cập kích thước $s$ tại địa chỉ $a$ được instrument như sau:

1. nạp $v=\text{shadow}(a)$;
2. nếu $v=0$, truy cập hợp lệ (đường nhanh, một load và một phép so sánh);
3. nếu không thì chạy *đường chậm*: đặt $\ell=(a\bmod 8)+s-1$ là offset của byte cuối cùng bị chạm trong từ; truy cập là lỗi khi và chỉ khi $\ell\ge v$ (với $v>0$), và luôn là lỗi với $v$ âm.

Hàm đường chậm của wiki chính là phép kiểm tra này, và nó giả định truy cập nằm gọn trong một từ 8 byte. Trường hợp có lời giải với khối 13 byte ở trên: đọc 4 byte tại offset 9 có $\ell=1+3=4<5$ nên qua; tại offset 10 có $\ell=2+3=5\ge5$ nên lỗi. Một lần chạy thật xác nhận cả hai (offset 9 im lặng, offset 10 được báo `heap-buffer-overflow ... READ of size 4`). Hai hệ quả thực tế: phép kiểm tra tốn thêm một load cho truy cập đúng, giải thích con số "chậm khoảng 2x" trong bảng; và vùng shadow tốn một phần tám không gian địa chỉ nó bao phủ, một phần của chi phí bộ nhớ.

![Khối 13 byte như hai từ 8 byte với giá trị shadow 0 và 5, và hai lần đọc 4 byte tại offset 9 và 10](/lesson-figures/CPP08-2.svg)

*Hình: ca của phần lý thuyết được vẽ ra; cùng phép thử $\ell\ge v$ cho qua lần đọc ở offset 9 nhưng chặn lần đọc ở offset 10, vì byte 13 bị poison.*

**Ví dụ.** Một khối 10 byte cho $10=8+2$, nên các shadow byte là $0$ và $2$. Đọc 2 byte tại offset 8 và 9, chạy thật:

```cpp
#include <cstdlib>
#include <cstdio>
#include <cstring>
int main(int argc, char** argv) {
  volatile char* p = static_cast<volatile char*>(std::malloc(10));
  int off = std::atoi(argv[1]);
  volatile short x = *reinterpret_cast<volatile short*>(p + off);   // 2-byte read at offset off
  (void)x;
  std::puts("no report"); std::free((void*)p);
}
```

```
$ g++ -std=c++20 -g -fsanitize=address shadow.cpp -o shadow && ./shadow 8
no report
$ ./shadow 9
==...==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x502000000019 ...
READ of size 2 at 0x502000000019 thread T0
0x50200000001a is located 0 bytes to the right of 10-byte region [0x502000000010,0x50200000001a)
=>0x0a047fff8000: fa fa 00[02]fa fa fa fa fa fa fa fa fa fa fa fa
```

Offset 8: $\ell=(0)+2-1=1<2$, im lặng. Offset 9: $\ell=1+2-1=2\ge2$, bị báo với "0 bytes to the right of 10-byte region". Dòng `00[02]` in ra chính là cặp giá trị shadow; với khối ở $0\mathrm{x}502000000010$ thì địa chỉ shadow là $(\texttt{0x502000000010}\gg3)+\texttt{0x7fff8000}=\texttt{0xa047fff8002}$, đó là byte `00`, và byte kế tiếp là `02`.

### AddressSanitizer không thấy gì, và công cụ nào lấp khoảng trống

Cơ chế chỉ phát hiện một truy cập nếu *chính byte đích* bị poison. Ba họ lỗi thoát vì lý do đó.

- **Nhảy qua redzone.** Nếu chỉ số sai đến mức truy cập rơi vào một đối tượng khác còn hợp lệ, byte shadow là $0$ và không có gì được báo. Thử nghiệm: hai khối `malloc(32)` là `p` và `q` cách nhau 48 byte (32 byte dùng được cộng 16 byte đệm bị poison), nên `p[48]` đọc `q[0]` mà không báo gì, trong khi `p[32]` bị bắt.
- **Tràn bên trong một đối tượng.** Các trường của một struct, hay phần tử của mảng thành viên của struct, liền kề nhau không có redzone giữa chúng. Ghi `s.buf[4]` trên `int buf[4]` làm hỏng trường kế bên `limit` một cách im lặng dưới ASan. Trong một thử nghiệm chương trình in `limit=5` mà không có báo cáo. `-fsanitize=bounds` của UndefinedBehaviorSanitizer ("truy cập mảng ngoài phạm vi trong các trường hợp cận mảng xác định được tĩnh") đã báo nó. Đó là lý do bài học kết hợp `address,undefined` thay vì chọn một.
- **Lỗi logic với bộ nhớ hợp lệ.** Một chỉ số sai nhưng vẫn nằm trong đối tượng, một con trỏ cũ nhưng vẫn được cấp phát, hay một race không phải lỗi bộ nhớ; chỉ test và các sanitizer khác xử lý chúng.

Bài học tổng quát: sanitizer là phép kiểm tra *động* các lớp lỗi cụ thể dọc theo đường thực thi. Một lần chạy im lặng là bằng chứng, không phải chứng minh, nên bảng chọn công cụ của bài là một tuyên bố về độ phủ, và vẫn phải có một regression test khẳng định theo giá trị.

![Hai khối heap có phần đệm bị poison và một struct không có đệm: ASan báo lỗi ở đâu và im lặng ở đâu](/lesson-figures/CPP08-3.svg)

*Hình: ASan kiểm tra byte nó sắp chạm. `p[32]` rơi vào vùng poison; `p[48]` rơi vào vùng nhớ hợp lệ của đối tượng khác; `buf[4]` rơi vào một thành viên hợp lệ của cùng đối tượng.*

**Ví dụ.** Một `std::vector<int>` lớn lên bằng năm lần `push_back` chứa 5 phần tử trong buffer cho 8 (capacity 8, 32 byte). Đọc `v[6]` là quá cuối vector nhưng vẫn trong vùng cấp phát, nên ASan im lặng và chương trình in ra mẫu fill của allocator; `v[8]` quá vùng cấp phát và bị báo. Biên dịch với `-D_GLIBCXX_ASSERTIONS` (kiểm tra biên của thư viện) bắt được cả trường hợp đầu:

```cpp
std::vector<int> v;
for (int i = 1; i <= 5; ++i) v.push_back(10 * i);              // size 5, capacity 8
std::cout << "size " << v.size() << ", capacity " << v.capacity() << std::endl;
std::cout << "v[6] = " << v[6] << std::endl;                   // past the end, inside the allocation
std::cout << "v[8] = " << v[8] << std::endl;                   // past the allocation
```

```
$ g++ -std=c++20 -g -fsanitize=address cap.cpp -o cap && ./cap
size 5, capacity 8
v[6] = -1094795586
==317745==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x503000000060 ...
READ of size 4 at 0x503000000060 thread T0
0x503000000060 is located 0 bytes to the right of 32-byte region [0x503000000040,0x503000000060)
$ g++ -std=c++20 -g -D_GLIBCXX_ASSERTIONS cap.cpp -o cap2 && ./cap2; echo "exit $?"
size 5, capacity 8
exit 134
```

Giá trị rác `-1094795586` là `0xBEBEBEBE`, giá trị fill của ASan cho bộ nhớ heap mới. Bài học giống như trên: sanitizer biết vùng cấp phát, không biết `size()` của container, nên cần `at()` có kiểm tra hoặc chế độ assertion của thư viện chuẩn bổ sung.

### Watchpoint: tìm ai đã ghi một giá trị

Khi một biến có giá trị sai và bạn không biết dòng nào ghi nó, một **watchpoint** yêu cầu debugger dừng khi nó thay đổi. `watch expr` dừng khi biểu thức được ghi và giá trị đổi; `rwatch` dừng khi đọc và `awatch` khi đọc hoặc ghi (GDB manual, *Setting Watchpoints*). Hai chi tiết quan trọng trong thực tế. Thông thường một watchpoint tôn trọng phạm vi biến, nên với biến toàn cục hay đối tượng heap truy cập qua con trỏ hãy dùng `watch -location expr` (`-l`), lấy địa chỉ một lần và theo dõi vùng nhớ đó. Và có hai cách cài đặt: có hỗ trợ phần cứng, watchpoint "không làm chậm việc chạy chương trình"; nếu không GDB đi từng lệnh và kiểm tra giá trị mỗi lần, mà manual mô tả là "chậm hơn chạy bình thường hàng trăm lần". Watchpoint phần cứng là thứ đầu tiên nên thử, loại phần mềm là phương án cuối cho lỗi mà bạn không đoán ra thủ phạm.

Một trường hợp có lời giải, chạy với GDB: một struct có `int buf[4]; int limit = 100;` và vòng lặp `for (i = 0; i <= n; ++i) buf[i] = i + 1;` với `n = 4`. Với `watch -l s.limit`, GDB dừng với `Old value = 100`, `New value = 5`, ở dòng vòng lặp của `fill (n=4)`, và `bt` cho thấy lời gọi từ `main`. Giá trị 5 là giá trị cuối cùng được ghi ($i+1$ với $i=4$), nhận ra ngay lỗi lệch một ở cận vòng lặp, dù không cần sanitizer nào.

**Ví dụ.** Biến toàn cục `g_mode` phải giữ nguyên 1 (run) sau `arm()`, nhưng chương trình kết thúc với mode sai. Một watchpoint có điều kiện dừng ở lần ghi đầu tiên làm nó lớn hơn 1, mà không cần biết hàm nào ghi:

```cpp
int g_mode = 0;                          // 0 = idle, 1 = run
void arm()           { g_mode = 1; }
void set_gain(int k) { g_mode = k * 2; } // BUG: clobbers the mode
int main() { arm(); set_gain(3); std::cout << "mode " << g_mode << "\n"; }
```

```
$ g++ -std=c++20 -g -O0 glob.cpp -o glob && gdb -batch -ex 'watch g_mode if g_mode > 1' -ex run -ex bt ./glob
Hardware watchpoint 1: g_mode
Old value = 1
New value = 6
set_gain (k=3) at glob.cpp:4
4	void set_gain(int k) { g_mode = k * 2; }   // BUG: clobbers the mode
#0  set_gain (k=3) at glob.cpp:4
#1  0x00005555555551ee in main () at glob.cpp:7
```

`Old value = 1`, `New value = 6` và frame `set_gain (k=3)` chỉ ra thủ phạm: $6=3\cdot2$ là `k * 2`, nên lỗi là công thức trong `set_gain`, vốn được viết cho một biến khác. Biến toàn cục không cần `-l`; điều kiện giữ cho lần dừng chỉ ở lần ghi đáng quan tâm.

### Bisect khi lỗi có tính xác suất

Bisect giả định một test tất định: nếu test báo "tốt" ở commit $c$ thì lỗi nằm sau, nếu không thì nằm trước. Với $N$ commit cần $\lceil\log_2N\rceil$ bước (tài liệu `git bisect` có ví dụ nói "roughly 10 steps" cho vài trăm đến một nghìn revision). Nếu lỗi chỉ xuất hiện với xác suất $p$ mỗi lần chạy trên một commit xấu, một lần "pass" không phải bằng chứng về commit tốt. Chạy mỗi commit được thử $r$ lần và chỉ gọi nó là tốt nếu cả $r$ lần đều pass. Commit tốt không bao giờ lỗi, nên sai sót chỉ xảy ra ở commit xấu, mỗi lần với xác suất $(1-p)^r$ bị đánh giá nhầm là tốt. Nếu nhiều nhất $k=\lceil\log_2N\rceil$ bước thử một commit xấu, xác suất cả lượt tìm đúng hoàn toàn ít nhất là $\bigl(1-(1-p)^r\bigr)^k$. Để đạt độ tin cậy $1-\alpha$ chỉ cần $(1-p)^r\le1-(1-\alpha)^{1/k}$, tức $r\ge\ln\!\bigl(1-(1-\alpha)^{1/k}\bigr)/\ln(1-p)$. Chi phí xấu nhất là $k\,r$ lần chạy, vì commit tốt cần đủ $r$ lần còn commit xấu dừng ở lần lỗi đầu tiên. Cận này thận trọng (nó hợp các sai số từng bước) nhưng cho thấy hình dạng của sự đánh đổi: lỗi càng hiếm càng nhân chi phí của cả $k$ bước, nên trước hết hãy tăng $p$ bằng cách gây áp lực cho test (nhiều thread hơn, seed cố định, build có sanitizer) trước khi bisect.

**Ví dụ.** Tìm trong 64 commit một lỗi hiện ra với xác suất $p=0.5$ mỗi lần chạy, với $1-\alpha=0.95$. Ở đây $k=\lceil\log_2 64\rceil=6$ và $r\ge\ln(1-0.95^{1/6})/\ln0.5=6.88$, nên $r=7$ và trường hợp xấu nhất là $kr=42$ lần chạy. Mô phỏng 20000 lần tìm (mỗi commit được thử lặp tối đa $r$ lần, một commit xấu dừng ở lần lỗi đầu tiên):

```
$ python3 prob.py        # N = 64 commits, p = 0.5, 1 - alpha = 0.95; 20000 simulated searches per row
r=1: bound=0.0156  simulated success=0.1792  mean runs=6.0
r=7: bound=0.9540  simulated success=0.9765  mean runs=26.9
k = 6  r = 7  worst-case runs k*r = 42
```

Với $r=1$ cận là $0.5^6=0.0156$ và mô phỏng thành công 18 % số lần tìm; với $r=7$ cận $0.954$ đúng (quan sát được 97.7 %, vì cận cộng các sai số hiếm khi trùng nhau) với trung bình 26.9 lần chạy. Kéo các thanh trượt để xem số lần lặp cần cho các cỡ khác:

```explore
{
  "title": "Bisecting a flaky bug: repeats per commit",
  "title_vi": "Bisect một lỗi chập chờn: số lần lặp mỗi commit",
  "prompt": "Predict first: with p = 50 % per run and 64 commits, is r = 3 repeats per commit enough for 95 % confidence? Then raise N or lower p and watch the repeats needed.",
  "prompt_vi": "Dự đoán trước: với p = 50 % mỗi lần chạy và 64 commit, r = 3 lần lặp mỗi commit có đủ cho độ tin cậy 95 % không? Sau đó tăng N hoặc giảm p và xem số lần lặp cần thiết thay đổi ra sao.",
  "params": [
    { "name": "N", "label": "commits to search N", "label_vi": "số commit cần tìm N", "min": 8, "max": 4096, "step": 1, "value": 64, "unit": "" },
    { "name": "pp", "label": "failure probability per run on a bad commit p", "label_vi": "xác suất lỗi mỗi lần chạy trên commit xấu p", "min": 5, "max": 100, "step": 1, "value": 50, "unit": "%" },
    { "name": "al", "label": "allowed error alpha", "label_vi": "sai số cho phép alpha", "min": 1, "max": 20, "step": 1, "value": 5, "unit": "%" },
    { "name": "r", "label": "repeats per tested commit r", "label_vi": "số lần lặp mỗi commit r", "min": 1, "max": 60, "step": 1, "value": 7, "unit": "" }
  ],
  "let": [
    { "name": "q", "expr": "pp/100" },
    { "name": "a", "expr": "al/100" },
    { "name": "k", "expr": "ceil(ln(N)/ln(2) - 0.000001)" },
    { "name": "rneed", "expr": "ceil(ln(1-(1-a)^(1/k))/ln(1-q))" },
    { "name": "bound", "expr": "(1-(1-q)^r)^k" }
  ],
  "plot": {
    "x": { "name": "m", "min": 1, "max": 60, "label": "repeats per commit r", "label_vi": "số lần lặp mỗi commit r" },
    "y": { "label": "lower bound on P(correct search)", "label_vi": "cận dưới của P(tìm đúng)", "min": 0, "max": 1 },
    "series": [
      { "expr": "(1-(1-q)^m)^k", "label": "(1-(1-p)^r)^k", "label_vi": "(1-(1-p)^r)^k", "color": "blue" },
      { "expr": "1-a", "label": "target 1-alpha", "label_vi": "mục tiêu 1-alpha", "color": "grey" }
    ],
    "points": [
      { "x": "r", "y": "bound", "label": "your r", "label_vi": "r của bạn", "color": "green" }
    ]
  },
  "readouts": [
    { "label": "bisection steps k", "label_vi": "số bước bisect k", "expr": "k", "unit": "", "digits": 0 },
    { "label": "smallest r for 1-alpha", "label_vi": "r nhỏ nhất cho 1-alpha", "expr": "rneed", "unit": "", "digits": 0 },
    { "label": "worst-case runs k*r", "label_vi": "số lần chạy tối đa k*r", "expr": "k*rneed", "unit": "", "digits": 0 },
    { "label": "bound with your r", "label_vi": "cận với r của bạn", "expr": "bound", "unit": "", "digits": 3 }
  ]
}
```

## Ví dụ có lời giải

### Trường hợp 1: một lỗi off-by-one trong moving average

**Đề bài.** `moving_average(v, w)` của phần cài đặt tham khảo phải trả một giá trị trung bình cho mỗi cửa sổ đầy đủ $w$ mẫu. Với `v = {1, 2, 3, 4, 5}` và `w = 2` nó phải in `1.5 2.5 3.5 4.5`; chương trình in `3 4.5 6 4.5` và không crash. Hãy tìm nguyên nhân bằng các công cụ của bài học, thu nhỏ ca lỗi, sửa và khóa bản sửa bằng một regression test.

**Lời giải.**

1. *Giả thuyết từ các con số* (Trực giác, "dự đoán trước khi tính"). Giá trị đầu 3 bằng $(1+2+3)/2$: ba phần tử được cộng và số chia vẫn là $w=2$. Vậy vòng lặp cửa sổ chạy thừa một lần. Các giá trị khác khớp: $(2+3+4)/2=4.5$, $(3+4+5)/2=6$, và cửa sổ cuối $(4+5+v[5])/2=4.5$ cần $v[5]=0$, một phần tử không tồn tại.
2. *Xác nhận bằng AddressSanitizer* (lý thuyết, "Đọc báo cáo AddressSanitizer"). `g++ -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer buggy.cpp` báo `heap-buffer-overflow`, `READ of size 8` tại `buggy.cpp:10`, và "0 bytes to the right of 40-byte region". Vector chứa $40/8=5$ double, nên chỉ số 5 đã được đọc: với cửa sổ cuối $i=3$, $k=2$ cho $i+k=5$. Các output trước cũng sai, nhưng chỉ lần đọc này là lỗi bộ nhớ.
3. *Thu nhỏ* (lý thuyết, "Rút gọn và chia đôi"). Với `{1,2,3}` và `w=2` chương trình in `3 2.5` và ASan báo vùng 24 byte; với `{1,2}` và `w=1` nó in `3 2` (đáp án đúng là `1 2`) và vùng 16 byte. Ca tái hiện nhỏ nhất là một phần tử và `w=1`: nó in `7`, thậm chí đúng, vậy mà ASan vẫn báo "0 bytes to the right of 8-byte region". Ba con số và một vòng lặp đã đủ để suy luận.
4. *Sửa*: đổi `k <= w` thành `k < w`.
5. *Regression test* với giá trị tính tay (lý thuyết, "Test harness và regression test"): `moving_average({1,2,3,4,5}, 2)` bằng `{1.5, 2.5, 3.5, 4.5}`; cửa sổ 1 trả lại input; cửa sổ 5 trả `{3}`; cửa sổ 6 và 0 trả rỗng.
6. *Xác nhận*: test lỗi trên code cũ (giá trị đầu là 3, không phải 1.5, có hoặc không có sanitizer) và qua trên code đã sửa dưới ASan và UBSan mà không có báo cáo nào.

![Các phần tử mỗi cửa sổ đọc trong Trường hợp 1: ba phần tử mỗi cửa sổ với k <= w, cửa sổ cuối đọc chỉ số 5](/lesson-figures/CPP08-4.svg)

*Hình: Trường hợp 1 đúng tỉ lệ. Mỗi cửa sổ đọc thừa một phần tử (nét đứt); cửa sổ cuối nằm quá cuối vector 5 phần tử.*

**Kiểm tra.** Một công cụ độc lập đồng ý: `valgrind ./buggy` in `Invalid read of size 8` và "Address ... is 0 bytes after a block of size 40 alloc'd", cùng khối 40 byte. Kiểm tra ý nghĩa: tổng ba phần tử chia cho 2 không thể là trung bình, vì trung bình của $\{1,2,3\}$ phải chia cho 3.

**Rút ra.** Các con số sai chỉ tới giả thuyết, ASan xác nhận nó tại đúng dòng, và một test kiểm tra giá trị sẽ bắt được lỗi mà không cần cả hai công cụ.

### Trường hợp 2: một giới hạn bị hỏng, không crash và không có báo cáo sanitizer

**Đề bài.** Một struct chứa `int buf[4]` rồi `int limit = 100`, và một hàm phụ điền buffer bằng `for (i = 0; i <= n; ++i) buf[i] = i + 1` với `n = 4`. Chương trình in `limit=5` thay vì `limit=100`. Không có gì crash. Hãy tìm nơi ghi, giải thích vì sao công cụ đầu tiên im lặng và sửa lỗi.

**Lời giải.**

1. *Giả thuyết từ giá trị.* 5 không phải một giới hạn hợp lý; nó là $i+1$ với $i=4$, giá trị cuối cùng vòng lặp ghi. Vậy vòng lặp đã ghi thừa một phần tử và `buf[4]` trùng với `limit`. `<=` thay vì `<` là nghi phạm đầu tiên, chưa được chứng minh.
2. *Thử AddressSanitizer.* Build với `-fsanitize=address` chương trình vẫn in `limit=5` và không có gì khác: `buf` và `limit` là các byte hợp lệ của cùng một đối tượng, không có redzone giữa các thành viên, nên lần truy cập qua được phép kiểm tra shadow (lý thuyết, "AddressSanitizer không thấy gì").
3. *Thử UBSan.* Với `-fsanitize=undefined` nó báo `wp.cpp:5:39: runtime error: index 4 out of bounds for type 'int [4]'`, vì cận của mảng là hằng số lúc biên dịch.
4. *Xác nhận bằng watchpoint, độc lập với sanitizer* (lý thuyết, "Watchpoint"). Trong GDB: `break main`, `run`, `watch -l s.limit`, `continue`. GDB dừng với `Old value = 100`, `New value = 5` trong `fill (n=4)` tại dòng của vòng lặp, và `bt` nêu `main` là nơi gọi (`Hardware watchpoint 2: -location s.limit`).
5. *Sửa và khóa lại.* Đổi `<=` thành `<` và thêm một regression test với kỳ vọng tính tay: sau `fill(4)`, `limit == 100` và `buf == {1,2,3,4}`. Nó lỗi trên code cũ dù có hay không có sanitizer.

**Kiểm tra.** Ba người quan sát khác nhau (kiểm tra biên của UBSan, watchpoint của GDB và giá trị cuối) đồng ý về một chỉ số: 4. Sau khi sửa, `limit=100` được in ra và các bản build ASan và UBSan im lặng.

**Rút ra.** Giá trị chỉ tới giả thuyết, UBSan và GDB mỗi bên xác nhận bằng một đường khác nhau, và riêng ASan sẽ bỏ sót; một ca tái hiện nhỏ (một struct, một vòng lặp, `n = 4`) giữ cho phiên watchpoint ngắn.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: AddressSanitizer wiki, list of detected errors)* Ghép mỗi bug với công cụ tốt nhất: (a) ghi một phần tử vượt quá mảng heap; (b) đọc một phần tử vector sau khi `push_back` đã cấp phát lại nó; (c) phép cộng `int` bị tràn; (d) hai thread cùng tăng một `int` thường; (e) một `new` không bao giờ được delete; (f) đọc một `double` cục bộ trước khi nó được gán.
2. **(Dễ)** Đọc đoạn báo cáo sau và nêu loại lỗi, cỡ truy cập, dòng source, tên và kích thước của biến, và chỉ số của lần truy cập sai đầu tiên: `stack-buffer-overflow ... READ of size 4 ... #0 ... in main stk.cpp:4 ... This frame has 1 object(s): [32, 56) 'hist' (line 3) <== Memory access at offset 56 overflows this variable`.
3. **(Dễ)** *(Adapted from: Pro Git, Debugging with Git - binary search)* Một regression xuất hiện đâu đó trong 1000 commit. `git bisect` cần tối đa bao nhiêu lần build? Một tìm kiếm tuyến tính trên các commit cần bao nhiêu trong trường hợp xấu nhất?
4. **(Vừa)** Giải thích vì sao một chương trình không sanitizer có cùng lỗi lệch một (`k <= w`) vẫn có thể in ra các số trông hợp lý và vẫn "chạy được". Với `v = {2, 4, 6, 8, 10, 12}` và `w = 3`, hãy tính tay bốn số mà vòng lặp lỗi in ra (coi lần đọc ngoài biên là 0) và bốn giá trị trung bình đúng, rồi chỉ ra vì sao số in ra cuối cùng lại đúng.
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
12. **(Thử thách)** `char *p = malloc(21)` trả về địa chỉ căn 8 byte $A=\texttt{0x504000000010}$. (a) Dùng $\text{Shadow}=(\text{Mem}\gg3)+\texttt{0x7fff8000}$, tính địa chỉ shadow của ba từ của khối và nêu các giá trị shadow. (b) Với các lần đọc 4 byte tại offset 16, 17, 18 và 20 tính từ $A$, và một lần đọc 8 byte tại offset 16, áp dụng phép thử slow-path và cho biết lần nào bị báo. (c) Một lần đọc 1 byte tại offset 20, và một lần tại offset 21? (d) Trong (b), lần nào cũng sẽ bị bỏ sót bởi một sơ đồ chỉ có một bit cho mỗi từ ("từ hợp lệ hoàn toàn hay không")? (phỏng theo AddressSanitizer wiki, *AddressSanitizerAlgorithm*, "Mapping" và hàm `SlowPathCheck`)
13. **(Thử thách)** Hai khối `p = malloc(72)` và `q = malloc(72)` được cấp phát liên tiếp dưới ASan, và chương trình thực thi `volatile char v = p[d];` với $d=q-p$, rồi `volatile char w = p[72];`. Hãy dự đoán, bằng mô hình shadow memory, lần đọc nào bị báo và vì sao, và bạn kỳ vọng $d$ bằng bao nhiêu (giải thích, rồi đo). Đề xuất hai cách khác nhau để lần đọc đầu bị phát hiện và bàn về chi phí của từng cách. (phỏng theo AddressSanitizer wiki, *AddressSanitizerAlgorithm*, "Short version" và "Memory mapping and Instrumentation")
14. **(Thử thách)** `struct Ring { int slot[6]; int head; }; Ring r{{0,0,0,0,0,0},250}; void fill(int n){ for (int i = 0; i <= n; ++i) r.slot[i] = 2 * i; }` và `fill(6)`. (a) Dự đoán `head` chứa gì sau đó và `-fsanitize=address` có báo gì không, và nêu lý do. (b) Kiểm tra nào của UBSan có thể báo nó? (c) Viết lệnh GDB tìm ra dòng làm hỏng `head` mà không cần biết vòng lặp, nêu `Old value` và `New value` sẽ hiện gì, và giải thích vì sao một software watchpoint quá chậm với chương trình chạy hàng phút. (phỏng theo GDB manual, *Setting Watchpoints*, và Clang UBSan manual, `-fsanitize=bounds`)
15. **(Thử thách)** Một test lỗi với xác suất $p=0.35$ ở mỗi lần chạy trên commit xấu và không bao giờ lỗi trên commit tốt. Bạn bisect 4000 commit với $k=\lceil\log_2 4000\rceil$ bước, chạy mỗi commit được thử $r$ lần và chỉ gọi nó là tốt nếu cả $r$ lần đều qua. (a) Suy ra xác suất cả cuộc tìm kiếm đúng, dưới dạng cận dưới theo $r$, $p$ và $k$. (b) Tìm $r$ nhỏ nhất cho ít nhất 95% và số lần chạy tối đa. (c) Cận dưới thành công là bao nhiêu nếu $r=1$? (d) Nêu hai cách giảm tổng chi phí, một cách tăng $p$ và một cách rút ngắn cuộc tìm. (nguồn: tài liệu git-bisect, phiên ví dụ và "Bisect skip"; cận xác suất được suy ra ở đây)

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
2. Loại lỗi stack-buffer-overflow; một lần đọc cỡ 4 (một `int`); dòng 4 của `stk.cpp`, trong `main`; biến là `hist`, chiếm các byte $[32,56)$ của frame, tức $24$ byte $=6$ int. Truy cập ở offset 56, cách đầu `hist` $56-32=24$ byte, nên lần truy cập sai đầu tiên là chỉ số $24/4=6$, vượt cuối một phần tử của mảng 6 phần tử (vòng lặp `i < 8` còn chạm chỉ số 7, nhưng lỗi đầu tiên mới là lỗi cần đọc).
3. Tối đa $\lceil\log_2 1000\rceil=10$ lần build; tìm kiếm tuyến tính cần tới 1000 (hoặc 999).
4. Lần đọc không xác định vượt một phần tử qua buffer của vector trả về bất cứ thứ gì có trong vùng nhớ đó (phần đệm của allocator, thường là 0), nên code chạy xong và in ra số. Vòng lặp lỗi cộng $w+1=4$ phần tử và chia cho $w=3$: $(2+4+6+8)/3=20/3=6.667$, $(4+6+8+10)/3=28/3=9.333$, $(6+8+10+12)/3=36/3=12$, và với cửa sổ cuối $(8+10+12+v[6])/3$ với $v[6]=0$ cho $30/3=10$. Các giá trị trung bình đúng là $4$, $6$, $8$, $10$. Số cuối đúng chỉ vì phần tử thừa đọc ra 0 nên không cộng thêm gì; ba số đầu sai. Một số cuối trông đúng che giấu lỗi, vì vậy phải kiểm tra mọi output (tính bằng Python).
5. `use` nhận `unique_ptr` theo giá trị, và `std::move(frame)` chuyển quyền sở hữu vào `f`, thứ bị hủy khi `use` kết thúc; sau đó `frame` là null, và `frame->id` là một phép dereference null. GDB: `bt` (cho thấy `main () at segv.cpp:11`) và `info locals` (cho thấy `frame = ... {get() = 0x0}`). Cách sửa: đọc `frame->id` trước khi move, hoặc để `use` nhận `const Frame&` để quyền sở hữu ở lại trong `main`.
6. Ví dụ: `Test{"moving_average window 2", [](Checker& c){ auto m = moving_average({1,2,3,4,5}, 2); c.check(m.size() == 4, "size"); c.check_near(m[0], 1.5, 1e-12, "m[0]"); ... }}`. Trên code lỗi `m[0]` là 3, nên test fail mà không cần sanitizer. Khẳng định trên giá trị nêu rõ thế nào là đúng và fail một cách xác định; dựa vào crash chỉ fail khi undefined behavior tình cờ crash, và không nói gì về kết quả sai nhưng thầm lặng.
7. Một bảng tốt: `wrap_to_pi(0)=0`; `wrap_to_pi(pi)=-3.14159` (đầu trên bị loại); `wrap_to_pi(-pi)=-3.14159`; `wrap_to_pi(1.5*pi)=-1.5708`; `wrap_to_pi(2*pi)=0` (có dung sai); `wrap_to_pi(7)=0.71681`; `wrap_to_pi(-7)=-0.71681`; `wrap_to_pi(1e6)` bằng phép tính trực tiếp với một oracle độc lập (mất độ chính xác với góc rất lớn là điều được dự kiến); `wrap_to_pi(NAN)` là NaN (không được lặp vô hạn). Dung sai khoảng $10^{-9}$.
8. $n\ge\ln0.05/\ln0.98=148.3$, vậy 149 lần chạy. Nguyên nhân và kỹ thuật: data race (ThreadSanitizer); thời gian/sleep (dùng đồng hồ giả hoặc condition variable thay vì `sleep`); bộ nhớ chưa khởi tạo (Valgrind/MSan, `-ftrivial-auto-var-init=zero` để lộ ra); ngẫu nhiên không seed hoặc seed theo thời gian (ghi và cố định seed); thứ tự của các container không có thứ tự (sắp xếp trước khi so sánh); rò rỉ tài nguyên giữa các test (chạy mỗi test trong một process mới).
9. Kết quả là `[17, 42]` với 22 lần gọi `fails` cho `range(64)` khi bạn bắt đầu ở khối 32 và giảm nửa xuống 1 (số chính xác phụ thuộc chiến lược). Một câu trả lời tốt cho thấy bắt đầu với khối 32 loại bỏ 32 phần tử mỗi lần (chỉ giữ nếu bug còn tồn tại), rồi giảm nửa xuống 1, và rằng kết quả là "1-minimal": loại bỏ bất kỳ phần tử còn lại nào cũng làm bug biến mất.
10. Một câu trả lời tốt: job 1 Debug (`-O1 -g`) với `-fsanitize=address,undefined` chạy mọi test (bắt 1(a), 1(b), 1(c), 1(e)); job 2 Release với cảnh báo là lỗi (`-Wall -Wextra -Werror`) và cùng các test (bắt UB phụ thuộc tối ưu hóa); job 3 ThreadSanitizer chỉ cho các test đồng thời (1(d), race ở bài tập 8), tách riêng vì TSan và ASan instrument bộ nhớ khác nhau và không kết hợp được; tùy chọn một job Valgrind hoặc MSan hằng đêm cho 1(f). Mỗi job nên tải báo cáo sanitizer đầu tiên lên làm artifact.
11. Một câu trả lời tốt có một bảng gồm: ASan (4 dòng đầu: heap-buffer-overflow, READ of size 8, `buggy.cpp:10`, 0 bytes to the right of a 40-byte region), Valgrind (`Invalid read of size 8`, địa chỉ cách 0 byte sau một khối kích thước 40), GDB cho biến thể `segv.cpp` (`bt`, `get() = 0x0`); đầu vào đã rút gọn (một phần tử, cửa sổ 1); một regression test fail trên code cũ; và lần chạy cuối không có output sanitizer.
12. (a) Địa chỉ shadow của từ đầu là $(\texttt{0x504000000010}\gg3)+\texttt{0x7fff8000}=\texttt{0xa087fff8002}$, của từ thứ hai là `0xa087fff8003`, của từ thứ ba là `0xa087fff8004` (tính bằng Python). Giá trị shadow: $0$, $0$ và $5$, vì $21=8+8+5$. (b) Slow path trên từ thứ ba (shadow $5$): $\ell=(a\bmod8)+s-1$, lỗi khi $\ell\ge5$. Offset 16, cỡ 4: $\ell=0+3=3<5$, im lặng. Offset 17, cỡ 4: $\ell=1+3=4<5$, im lặng. Offset 18, cỡ 4: $\ell=2+3=5\ge5$, bị báo. Offset 20, cỡ 4: $\ell=4+3=7\ge5$, bị báo. Offset 16, cỡ 8: $\ell=7\ge5$, bị báo. Một lần chạy thật (gcc 11.4, `-fsanitize=address`) im lặng ở offset 16 và 17 và báo `READ of size 4` ở 18 và 20, `READ of size 8` ở 16. (c) Offset 20, cỡ 1: $\ell=4+0=4<5$, im lặng. Offset 21, cỡ 1: $\ell=5+0=5\ge5$, bị báo ("0 bytes to the right of 21-byte region"); cả hai đã được xác nhận bằng chạy thật. (d) Một sơ đồ một bit cho mỗi từ phải coi từ thứ ba hợp lệ một phần là hợp lệ (khi đó các lần đọc ở offset 18 và 20 và byte ở 21 bị bỏ sót) hoặc là không hợp lệ (khi đó các lần đọc hợp lệ ở 16 và 17 báo nhầm). Ánh xạ 8-trên-1 với các giá trị $0..7$ là điều cho phép phần đuôi chính xác từng byte.
13. Lần đọc đầu *không* bị báo còn lần thứ hai thì có. `p[72]` rơi vào redzone phải của `p`: shadow của nó là một mã poison âm, nên phép kiểm tra kích hoạt ("0 bytes to the right of 72-byte region"). `p[d]` với $d=q-p$ đúng là byte đầu của `q`; byte shadow của nó là $0$ (hợp lệ), nên đường nhanh chấp nhận: ASan kiểm tra byte đích, không kiểm tra xuất xứ của con trỏ có phải `p` hay không. $d$ kỳ vọng: khối cộng phần đệm bị poison giữa hai lần cấp phát liên tiếp, nên ít nhất $72+$redzone; đo được $d=112$ (40 byte redzone và dữ liệu quản lý của allocator), và lần đọc trả về `q[0]` (9 trong lần chạy mà `q` được điền 9). Cách sửa: (1) redzone lớn hơn, làm một bước nhảy cỡ nhất định rơi vào vùng poison nhưng tốn thêm bộ nhớ cho mỗi lần cấp phát và vẫn không chặn được chỉ số tùy ý; (2) truy cập có kiểm tra biên trong code (`std::vector::at`, span có kiểm tra, hoặc kiểm tra chỉ số tường minh), bắt lỗi độc lập với bố cục bộ nhớ với giá là một nhánh cho mỗi truy cập; lựa chọn thứ ba là bounds sanitizer như `-fsanitize=bounds` cho mảng có kích thước tĩnh, không giúp được cho mảng heap kích thước động.
14. (a) `slot[6]` là int kế tiếp trong struct, tức `head`; sau vòng lặp `head` là $12$ (giá trị cuối cùng được ghi, $2i$ với $i=6$), và một lần chạy in `head=12`. ASan không báo gì: lần ghi rơi vào một từ hợp lệ của cùng đối tượng toàn cục, không có redzone giữa các thành viên. (b) `-fsanitize=bounds` (nằm trong `-fsanitize=undefined`) báo `index 6 out of bounds for type 'int [6]'`, vì cận mảng được biết tĩnh (kiểm tra tại `ring.cpp:4`). (c) `watch -l r.head` (hoặc `watch -location r.head`) sau `break main` và `run`, rồi `continue`: GDB dừng với `Old value = 250`, `New value = 12` trong `fill (n=6)` tại dòng vòng lặp, và `bt` cho thấy `main` là nơi gọi (đã kiểm tra với GDB). Software watchpoint chạy từng lệnh và so sánh sau mỗi lệnh, mà manual mô tả là chậm hơn hàng trăm lần so với chạy bình thường, nên vài phút thành vài giờ; hardware watchpoint tránh được chi phí đó.
15. (a) Sai sót chỉ xảy ra ở các bước thử một commit xấu, và ở bước như vậy test nói nhầm "tốt" với xác suất $(1-p)^r$ (cả $r$ lần đều qua). Với tối đa $k$ bước như vậy, xác suất không bước nào sai ít nhất là $\bigl(1-(1-p)^r\bigr)^k$. (b) Ở đây $k=\lceil\log_2 4000\rceil=12$. Yêu cầu $\bigl(1-0.65^{r}\bigr)^{12}\ge0.95$, tức $0.65^r\le1-0.95^{1/12}=0.004265$, nên $r\ge\ln0.004265/\ln0.65=12.67$, vậy $r=13$ (đã tính: $(1-0.65^{13})^{12}=0.9565$; $r=12$ cho $0.9338<0.95$). Trường hợp xấu nhất $k\,r=12\cdot13=156$ lần chạy, so với 12 cho test tất định. (c) Với $r=1$ cận là $(1-0.65)^{12}=0.35^{12}=3.4\times10^{-6}$, gần như không có bảo đảm: một lần chạy qua của commit xấu là chuyện thường. (d) Tăng $p$: gây áp lực lên test (lặp, thêm thread hoặc sleep, cố định và thay đổi seed, dùng bản build TSan/ASan) cho đến khi nó lỗi gần như luôn. Rút ngắn cuộc tìm: dùng `git bisect skip` cho các commit không thử được, hoặc thu hẹp khoảng trước bằng một chỉ báo tất định rẻ hơn (lỗi biên dịch, danh sách file đổi).

## Đọc thêm

- [AddressSanitizer (Google Sanitizers wiki)](https://github.com/google/sanitizers/wiki/AddressSanitizer) - nó phát hiện gì, cách đọc báo cáo, và chi phí của nó.
- [GCC: Program Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html) - mọi tùy chọn `-fsanitize=`, và cái nào kết hợp được.
- [GDB documentation](https://sourceware.org/gdb/documentation/) - sách hướng dẫn về breakpoint, kiểm tra stack và watchpoint.
- [AddressSanitizerAlgorithm (Google Sanitizers wiki)](https://github.com/google/sanitizers/wiki/AddressSanitizerAlgorithm) - shadow memory, ánh xạ và phép kiểm tra truy cập được instrument.
- [GDB manual: Setting Watchpoints](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Set-Watchpoints.html) - `watch`, `rwatch`, `awatch`, `-location`, watchpoint phần cứng so với phần mềm.
- [Clang: UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) - danh sách các kiểm tra `-fsanitize=`, gồm cả `bounds`.
- [git-bisect documentation](https://git-scm.com/docs/git-bisect) - quy trình bisect, ước lượng số bước và `skip`.

**Thực hành thêm:** [chương Pro Git về debug với Git](https://git-scm.com/book/en/v2/Git-Tools-Debugging-with-Git) (bisect và blame), [UndefinedBehaviorSanitizer manual](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) và [AddressSanitizer manual](https://clang.llvm.org/docs/AddressSanitizer.html) (cố ý kích hoạt từng kiểm tra được liệt kê và đọc báo cáo), [Valgrind quick start](https://valgrind.org/docs/manual/quick-start.html), [GDB sample session](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Sample-Session.html), và [GoogleTest primer](https://google.github.io/googletest/primer.html).
