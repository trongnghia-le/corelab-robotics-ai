---
{"title": "Đồng thời: thread, đồng bộ hóa và data race", "summary": "Chia sẻ dữ liệu giữa các thread mà không có data race, xây một hàng đợi producer-consumer chặn (blocking) và nêu rõ hợp đồng khóa của nó.", "objectives": ["Định nghĩa data race, nhận ra một data race, và giải thích vì sao nó là undefined behavior.", "Bảo vệ trạng thái dùng chung bằng mutex theo RAII, và tránh deadlock do thứ tự khóa.", "Dùng condition variable đúng cách (luôn kèm predicate) để chặn và đánh thức thread.", "Viết và kiểm thử một hàng đợi producer-consumer có giới hạn và ghi tài liệu hợp đồng khóa của nó."]}
---
## Vì sao điều này quan trọng

Robot vốn đồng thời: driver camera giao frame ở 30 Hz, IMU ở 400 Hz, bộ điều khiển chạy ở 1 kHz và planner lấy bao nhiêu thời gian tùy cần. Dùng thread cho phép các hoạt động này chồng lên nhau, nhưng thread chia sẻ bộ nhớ, và chia sẻ không đồng bộ không chỉ là "thỉnh thoảng sai": đọc và ghi cùng một biến từ hai thread mà không đồng bộ là một **data race**, và đó là undefined behavior trong C++. Triệu chứng thuộc loại tệ nhất: mất cập nhật, giá trị bị xé (torn), treo máy mỗi tuần một lần, và bug biến mất khi bạn thêm một `printf`. Bài này cho bạn từ vựng (thread, mutex, condition variable, atomic), các bất biến cần giữ (không race, không deadlock, không mất wake-up), và một ví dụ hoàn chỉnh, hàng đợi chặn có giới hạn, thứ keo dán giữa callback cảm biến và các thread xử lý trong gần như mọi stack robotics, kể cả các executor và hàng đợi message của ROS 2.

## Trực giác

Thread là một luồng thực thi độc lập bên trong một process; mọi thread nhìn thấy cùng một bộ nhớ. Hãy tưởng tượng hai người cùng sửa một tờ phiếu. Nếu họ lần lượt thay phiên nhau (loại trừ tương hỗ, mutual exclusion), tờ phiếu giữ được nhất quán. Nếu cả hai viết cùng lúc, kết quả có thể là hỗn hợp của cả hai. Lock là cây bút mà mỗi lúc chỉ một người được cầm.

Ngay cả một dòng như `++counter` cũng là ba bước (nạp, cộng, lưu). Hai thread có thể cùng nạp 5, cùng cộng 1, và cùng lưu 6: mất một lần tăng. Mutex biến ba bước thành một *vùng găng (critical section)* không thể chia cắt; atomic làm cho một thao tác đơn không thể chia cắt ở mức phần cứng.

Chờ đợi là một vấn đề khác với khóa. Một consumer thấy hàng đợi rỗng không nên quay vòng (spin) đốt một lõi, cũng không nên giữ lock khi ngủ. **Condition variable** cho phép nó nhả lock và ngủ cho đến khi một thread khác báo rằng trạng thái có thể đã đổi, rồi lấy lại lock và kiểm tra lại.

![Producer, hàng đợi có giới hạn được bảo vệ bởi một mutex với hai condition variable, và consumer; một dòng thời gian cho thấy mất cập nhật từ hai phép tăng không đồng bộ](/lesson-figures/CPP10.svg)

*Trái: producer, hàng đợi và consumer được đồng bộ bởi một mutex và hai condition variable. Phải: hai phép tăng đan xen làm mất một cập nhật.*

**Hãy dự đoán trước khi tính.** Hai thread, mỗi thread cộng 1 vào cùng một số nguyên dùng chung một triệu lần. Trước khi chạy gì, hãy ghi ra giá trị cuối bạn kỳ vọng, và liệu nó có giống nhau ở mọi lần chạy không. Đa số nói 2.000.000. Kết quả đo trong bài này là "ít hơn, và khác nhau mỗi lần", với 11.654 lần cập nhật bị mất trong một lần chạy, và chuẩn C++ nói chương trình hoàn toàn không có nghĩa xác định.

**Một hình ảnh để nhớ.** Hãy tưởng tượng hai nhân viên cập nhật cùng một dòng sổ cái bằng giấy. Mỗi người đọc con số, đi đến máy tính, cộng một rồi quay lại ghi kết quả. Nếu cả hai cùng đọc 7 trước khi ai ghi, cả hai ghi 8 và một lần bán biến mất. Khóa là quy tắc chỉ nhân viên đang cầm bút mới được nhìn vào dòng đó; condition variable là phòng chờ nơi nhân viên ngủ cho đến khi ai đó rung chuông báo "giờ có việc để làm". Deadlock là hai nhân viên mỗi người giữ một cây bút và từ chối bỏ xuống cho đến khi có cây của người kia.

**Các trực giác sai.** "Tôi chạy thử thì in đúng, nên nó đúng": race phụ thuộc thời điểm, và debugger, một `printf` hoặc CPU khác làm thay đổi thời điểm. "Đọc một `int` dùng chung không khóa là vô hại": data race là undefined behavior kể cả với lần đọc, vì compiler được phép giả định nó không xảy ra. "Hàng đợi to hơn sửa được quá tải": nó chỉ trì hoãn lúc producer phải chờ và tăng latency. Hãy giữ quy tắc ngược lại: dữ liệu thay đổi dùng chung cần một chủ sở hữu có tên (một mutex), mọi lần chờ cần một predicate, và chương trình đa luồng được đánh giá theo các xen kẽ *có thể* xảy ra, không phải những cái bạn đã thấy.

## Lý thuyết và suy dẫn

### Data race và memory model

Hai truy cập bộ nhớ *xung đột (conflict)* nếu chúng chạm cùng một vị trí và ít nhất một là ghi. **Data race** xảy ra khi hai truy cập xung đột ở các thread khác nhau không được sắp thứ tự bởi quan hệ happens-before (tạo bởi mutex, atomic với thứ tự phù hợp, thread start và join). Một chương trình có data race là undefined behavior, ngay cả khi mỗi biến "chỉ là một int": compiler có thể giả định không có race và sắp xếp lại thứ tự, cache giá trị trong thanh ghi, hoặc tách các truy cập.

Không phải data race: đọc đồng thời dữ liệu không ai ghi; ghi vào các đối tượng khác nhau (các phần tử khác nhau của vector; dù các phần tử lân cận dùng chung một cache line, đó là vấn đề hiệu năng gọi là false sharing); các truy cập được bảo vệ bởi cùng một mutex; các thao tác trên `std::atomic`.

Mất cập nhật, từng bước: counter $=0$. Thread A nạp 0; thread B nạp 0; A lưu 1; B lưu 1. Hai lần tăng, giá trị cuối là 1. Trong một thí nghiệm với hai thread mỗi thread làm $10^6$ phép tăng thường, tổng quan sát được là 1,988,346 thay vì 2,000,000, mất $11{,}654$ cập nhật ($0.58\%$) trong một lần chạy. Một counter được mutex bảo vệ hoặc atomic luôn cho 2,000,000.

**Ví dụ.** Hai thread, mỗi thread cộng 1 vào một bộ đếm dùng chung 400,000 lần, trước hết trên `int` thường rồi trên `std::atomic<int>` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O0 -pthread`; `-O0` giữ cho nạp, cộng và lưu hiện ra thành ba bước):

```cpp
#include <atomic>
#include <cstdio>
#include <thread>
// Two threads each add 1 to a shared counter 400,000 times: plain int (a data race) versus atomic.
int plain = 0;
std::atomic<int> safe{0};
int main() {
  for (int run = 1; run <= 3; ++run) {
    plain = 0;
    {
      std::jthread a([] { for (int i = 0; i < 400000; ++i) ++plain; });
      std::jthread b([] { for (int i = 0; i < 400000; ++i) ++plain; });
    }
    std::printf("run %d: plain int  = %d (expected 800000, lost %d)\n", run, plain, 800000 - plain);
  }
  {
    std::jthread a([] { for (int i = 0; i < 400000; ++i) safe.fetch_add(1); });
    std::jthread b([] { for (int i = 0; i < 400000; ++i) safe.fetch_add(1); });
  }
  std::printf("atomic counter = %d\n", safe.load());
}
```

```text
run 1: plain int  = 421010 (expected 800000, lost 378990)
run 2: plain int  = 481171 (expected 800000, lost 318829)
run 3: plain int  = 481774 (expected 800000, lost 318226)
atomic counter = 800000
```

Bộ đếm thường kết thúc ở 421,010, 481,171 và 481,774, không bao giờ là 800,000 và khác nhau ở mỗi lần chạy, còn bộ đếm atomic luôn đúng 800,000. Mức mất ở đây (40 đến 47 %) lớn hơn nhiều so với 0.58 % nêu ở trên cho một bản build khác trên máy khác: độ lớn của nó phụ thuộc vào thời điểm, và đó chính là điều cần thấy, vì chương trình không có kết quả xác định. Biên dịch với ThreadSanitizer (`-fsanitize=thread`, chạy bằng `setarch -R ./a.out` trên kernel này), vòng lặp thường đó bị báo cáo (trích đoạn):

```text
WARNING: ThreadSanitizer: data race
  Read of size 4 by thread T2:
    #0 operator() e10_1.cpp:12
  Previous write of size 4 by thread T1:
    #0 operator() e10_1.cpp:11
SUMMARY: ThreadSanitizer: data race e10_1.cpp:12 in operator()
```

### Thread, mutex và RAII

```cpp
std::thread t(work, arg);   // starts immediately
t.join();                    // wait for it to finish
```
Một `std::thread` bị hủy khi vẫn còn joinable sẽ gọi `std::terminate` ("terminate called without an active exception"). Luôn `join()` (hoặc `detach()` có chủ ý, hiếm khi); với C++20 hãy ưu tiên `std::jthread`, tự join trong destructor.

Bảo vệ trạng thái dùng chung bằng mutex và khóa nó bằng RAII (CP.20): `std::lock_guard<std::mutex> lk(m);` hoặc `std::unique_lock` khi bạn cần mở khóa sớm hoặc chờ. Đừng bao giờ gọi `m.lock()`/`m.unlock()` bằng tay: một exception hay `return` sớm sẽ để nó bị khóa. Giữ các vùng găng ngắn và đừng gọi code không rõ (callback, I/O) khi đang giữ lock.

**Deadlock** cần một chu trình: thread 1 giữ $A$ và chờ $B$, thread 2 giữ $B$ và chờ $A$. Tránh nó bằng thứ tự khóa hoặc bằng cách lấy nhiều mutex cùng lúc với `std::scoped_lock lk(a.m, b.m);` (CP.21), dùng một thuật toán tránh deadlock.

**Ví dụ.** Một critical section ném exception (đọc cảm biến thất bại). Sau khi exception bị bắt, một thread thứ hai thử lấy cùng mutex bằng `try_lock`; một phiên bản khóa bằng `lock_guard`, phiên bản kia bằng `m.lock()` và `m.unlock()` viết tay (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`):

```cpp
#include <cstdio>
#include <mutex>
#include <stdexcept>
#include <thread>
// A critical section that throws. Can another thread take the mutex afterwards?
std::mutex m;
bool other_can_lock() {
  bool ok = false;
  std::jthread t([&] { ok = m.try_lock(); if (ok) m.unlock(); });
  t.join();
  return ok;
}
void with_guard() { std::lock_guard<std::mutex> lk(m); throw std::runtime_error("sensor read failed"); }
void by_hand() { m.lock(); throw std::runtime_error("sensor read failed"); m.unlock(); }
int main() {
  try { with_guard(); } catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); }
  std::printf("lock_guard : other thread can lock afterwards = %d\n", other_can_lock());
  try { by_hand(); } catch (const std::exception& e) { std::printf("caught: %s\n", e.what()); }
  std::printf("m.lock()   : other thread can lock afterwards = %d\n", other_can_lock());
  m.unlock();   // clean up the leaked lock (same thread that took it)
}
```

```text
caught: sensor read failed
lock_guard : other thread can lock afterwards = 1
caught: sensor read failed
m.lock()   : other thread can lock afterwards = 0
```

Destructor của guard chạy trong lúc exception tháo ngăn xếp, nên mutex được giải phóng (`1`). Phiên bản viết tay không bao giờ tới `m.unlock()`, nên mutex bị khóa mãi (`0`): mọi thread khác xin nó sẽ chặn vĩnh viễn. Lệnh `m.unlock()` cuối trong `main` chỉ để dọn phần minh họa.

### Condition variable

```cpp
std::unique_lock<std::mutex> lk(m);
cv.wait(lk, [&]{ return !q.empty() || closed; });   // predicate form
```
`wait` nhả lock một cách nguyên tử và ngủ; khi thức dậy nó lấy lại lock. Predicate được kiểm tra *khi đang giữ lock*, trong một vòng lặp (overload có predicate làm việc này cho bạn), vì có **spurious wake-up** (thức dậy giả) và vì consumer khác có thể đã lấy mất phần tử trước. Gọi notify sau khi đổi trạng thái, hoặc khi đang giữ lock hoặc ngay sau khi nhả nó. Mất wake-up xảy ra khi một thread kiểm tra điều kiện mà không có lock, và trạng thái thay đổi giữa lúc kiểm tra và lúc ngủ.

**Ví dụ.** Một notifier đặt `ready` và gọi `notify_one` *trước khi* waiter bắt đầu chờ. Waiter dùng `wait_for` không có predicate trước, rồi dùng overload có predicate, mỗi lần với timeout 200 ms để một lần mất wake-up hiện ra như timeout thay vì treo (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`):

```cpp
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <mutex>
#include <thread>
using namespace std::chrono_literals;
// The notification arrives BEFORE the waiter starts waiting. Without a predicate it is lost.
std::mutex m;
std::condition_variable cv;
bool ready = false;
int main() {
  {
    std::jthread notifier([] { { std::lock_guard<std::mutex> lk(m); ready = true; } cv.notify_one(); });
  }                                            // notifier has finished: ready == true, nobody was waiting
  auto t0 = std::chrono::steady_clock::now();
  std::unique_lock<std::mutex> lk(m);
  auto st = cv.wait_for(lk, 200ms);            // no predicate: waits for a notify that already happened
  auto t1 = std::chrono::steady_clock::now();
  std::printf("no predicate  : %s after %ld ms, ready = %d\n", st == std::cv_status::timeout ? "timed out" : "woken",
              (long)std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count(), ready);
  t0 = std::chrono::steady_clock::now();
  bool ok = cv.wait_for(lk, 200ms, [] { return ready; });   // predicate form tests the state first
  t1 = std::chrono::steady_clock::now();
  std::printf("with predicate: %s after %ld ms\n", ok ? "returned true" : "timed out",
              (long)std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count());
}
```

```text
no predicate  : timed out after 200 ms, ready = 1
with predicate: returned true after 0 ms
```

Trạng thái đã đúng từ trước, nhưng `wait_for` trần ngủ hết 200 ms vì thông báo duy nhất đến sớm hơn và đã mất: condition variable không nhớ gì. Overload có predicate kiểm `ready` dưới lock trước khi ngủ và trả về ngay (0 ms). Quy tắc là chờ một *trạng thái*, không bao giờ chờ một tín hiệu.

### Hàng đợi có giới hạn và hợp đồng của nó

Một hàng đợi có giới hạn dung lượng $K$ tách tốc độ của producer và consumer: nếu producer nhanh hơn, nó bị chặn (back-pressure) thay vì tiêu thụ bộ nhớ không giới hạn. Trạng thái gồm `deque<T> q`, `bool closed` và một mutex. Hai điều kiện: `not_full` (producer chờ `size < K`) và `not_empty` (consumer chờ có phần tử). Hợp đồng:

1. Mọi trạng thái được bảo vệ bởi một mutex.
2. `push` chặn khi đầy; `pop` chặn khi rỗng và còn mở.
3. `close()` đánh dấu kết thúc luồng và đánh thức mọi người; sau đó `push` thất bại và `pop` rút nốt các phần tử còn lại rồi trả `nullopt`.
4. Thứ tự FIFO; không phần tử nào bị mất hay giao hai lần.
5. Không giữ lock khi chạy code người dùng, nên không thể có chu trình thứ tự khóa.

*Ví dụ về kích thước.* Một cảm biến phát một đợt 50 phần tử trong 50 ms (1000 phần tử/s); consumer xử lý 200 phần tử/s. Trong đợt phát, consumer lấy đi $200\times0.05=10$ phần tử, nên tồn đọng là $50-10=40$ phần tử và được xả hết trong $40/200=0.2$ s. Dung lượng $\ge40$ tránh chặn producer; với dung lượng 8, producer bị làm chậm bằng nhịp của consumer.

**Ví dụ.** Quy tắc định cỡ của hợp đồng được thử trên một hàng đợi đang chạy. Một đợt 60 phần tử đến, cứ 0.5 ms một phần tử (2000 phần tử/s), và consumer cần 2.5 ms mỗi phần tử (400 phần tử/s). Đợt kéo dài $60\times0.5=30$ ms, trong đó consumer lấy đi khoảng $400\times0.030=12$ phần tử, nên backlog dự đoán là $60-12=48$ phần tử. Chương trình chạy dung lượng $K=64$ và $K=8$ và đếm số lần push phải chờ (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`):

```cpp
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <deque>
#include <mutex>
#include <thread>
using namespace std::chrono_literals;
// Bounded queue of capacity K. A burst of 60 items arrives every 0.5 ms (2000 items/s);
// the consumer needs 2.5 ms per item (400 items/s). Count the pushes that had to wait.
struct Queue {
  std::size_t K; std::deque<int> q; std::mutex m; std::condition_variable not_full, not_empty;
  std::size_t peak = 0; int waited = 0;
  explicit Queue(std::size_t k) : K(k) {}
  void push(int x) {
    std::unique_lock<std::mutex> lk(m);
    if (q.size() >= K) ++waited;
    not_full.wait(lk, [&] { return q.size() < K; });
    q.push_back(x); if (q.size() > peak) peak = q.size();
    not_empty.notify_one();
  }
  int pop() {
    std::unique_lock<std::mutex> lk(m);
    not_empty.wait(lk, [&] { return !q.empty(); });
    int x = q.front(); q.pop_front();
    not_full.notify_one();
    return x;
  }
};
int main() {
  for (std::size_t K : {64u, 8u}) {
    Queue q(K);
    auto t0 = std::chrono::steady_clock::now();
    double producer_ms = 0;
    {
      std::jthread consumer([&] { for (int i = 0; i < 60; ++i) { q.pop(); std::this_thread::sleep_for(2500us); } });
      std::jthread producer([&] {
        for (int i = 0; i < 60; ++i) { q.push(i); std::this_thread::sleep_for(500us); }
        producer_ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
      });
    }
    std::printf("K = %2zu: peak backlog = %2zu, pushes that blocked = %2d, producer done after %5.1f ms\n", K, q.peak, q.waited, producer_ms);
  }
}
```

```text
K = 64: peak backlog = 47, pushes that blocked =  0, producer done after  33.9 ms
K =  8: peak backlog =  8, pushes that blocked = 48, producer done after 137.1 ms
```

Với $K=64$, backlog đỉnh đo được là 47 (dự đoán 48; phần tử đầu được lấy ngay và các lần sleep không chính xác tuyệt đối), không push nào bị chặn và producer xong sau 33.9 ms. Với $K=8$ hàng đợi đầy sau 8 phần tử, 48 lần push phải chờ và producer bị kéo xuống nhịp của consumer: nó xong sau 137.1 ms, gần với $(60-8)\times2.5=130$ ms.

```explore
{
  "title": "How big must the queue be for a burst?",
  "title_vi": "Hàng đợi phải lớn bao nhiêu cho một đợt dồn dập?",
  "prompt": "Predict first: a burst of 50 items arrives at 1000 items/s and the consumer handles 200 items/s. How large is the backlog when the burst ends, and how long does it take to drain? Then drag the sliders: which single change shrinks the required capacity most?",
  "prompt_vi": "Dự đoán trước: một đợt 50 phần tử đến với tốc độ 1000 phần tử/s và consumer xử lý 200 phần tử/s. Backlog lúc đợt kết thúc là bao nhiêu, và mất bao lâu để xả hết? Rồi kéo các thanh trượt: thay đổi nào làm dung lượng cần thiết giảm nhiều nhất?",
  "params": [
    { "name": "n", "label": "burst size n", "label_vi": "cỡ đợt n", "min": 10, "max": 200, "step": 5, "value": 50, "unit": "items" },
    { "name": "rp", "label": "producer rate", "label_vi": "tốc độ producer", "min": 250, "max": 5000, "step": 50, "value": 1000, "unit": "items/s" },
    { "name": "rc", "label": "consumer rate", "label_vi": "tốc độ consumer", "min": 50, "max": 1000, "step": 10, "value": 200, "unit": "items/s" },
    { "name": "K", "label": "queue capacity K", "label_vi": "dung lượng hàng đợi K", "min": 1, "max": 100, "step": 1, "value": 8, "unit": "items" }
  ],
  "let": [
    { "name": "dur", "expr": "n / rp" },
    { "name": "backlog", "expr": "max(n - rc * dur, 0)" },
    { "name": "drain", "expr": "backlog / rc" },
    { "name": "late", "expr": "max(n / rc - dur, 0)" }
  ],
  "plot": {
    "x": { "name": "x", "min": 0, "max": 0.6, "label": "time since the burst starts (s)", "label_vi": "thời gian từ lúc đợt bắt đầu (s)" },
    "y": { "label": "items waiting", "label_vi": "số phần tử đang chờ", "min": 0 },
    "series": [
      { "expr": "max(min(rp * x, n) - min(rc * x, n), 0)", "label": "backlog with no limit", "label_vi": "backlog không giới hạn", "color": "orange" },
      { "expr": "K", "label": "capacity K", "label_vi": "dung lượng K", "color": "blue" }
    ],
    "points": [
      { "x": "dur", "y": "backlog", "label": "end of burst", "label_vi": "hết đợt", "color": "rose" }
    ]
  },
  "readouts": [
    { "label": "backlog at the end of the burst", "label_vi": "backlog lúc hết đợt", "expr": "backlog", "unit": "items", "digits": 1 },
    { "label": "time to drain", "label_vi": "thời gian xả hết", "expr": "drain", "unit": "s", "digits": 3 },
    { "label": "minimum capacity so the producer never blocks", "label_vi": "dung lượng tối thiểu để producer không bị chặn", "expr": "ceil(backlog)", "unit": "items", "digits": 0 },
    { "label": "last item waits", "label_vi": "phần tử cuối phải chờ", "expr": "late", "unit": "s", "digits": 3 },
    { "label": "producer blocks? (1 yes, 0 no)", "label_vi": "producer bị chặn? (1 có, 0 không)", "expr": "ifpos(backlog - K, 1, 0)", "unit": "", "digits": 0 }
  ]
}
```

### Atomic và memory ordering

`std::atomic<T>` làm cho các thao tác đơn không chia cắt được và không có race. Với `memory_order_seq_cst` (mặc định) mọi thao tác atomic xuất hiện theo một thứ tự toàn cục duy nhất. Thứ tự **release/acquire** cho một đảm bảo công bố: mọi thứ được ghi trước một release store đều nhìn thấy được sau một acquire load đọc giá trị đã lưu.

```cpp
int data; std::atomic<bool> ready{false};
// producer:  data = 42;  ready.store(true, std::memory_order_release);
// consumer:  while (!ready.load(std::memory_order_acquire)) {}  /* data == 42 here */
```
Với `memory_order_relaxed` cho cả hai, việc ghi `data` không được sắp thứ tự với cờ, và việc đọc `data` sẽ là một data race. Dùng atomic cho cờ và counter; dùng mutex cho bất cứ thứ gì có bất biến xuyên nhiều biến.

**Ví dụ.** Mẫu công bố của mục này được chạy 2000 lần, mỗi vòng dùng một cặp thread mới: producer ghi `data = 42` và đặt `ready` với release; consumer quay vòng với acquire rồi đọc `data` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`; cùng mã nguồn biên dịch với `-DRELAXED` dùng relaxed ở cả hai thao tác):

```cpp
#include <atomic>
#include <cstdio>
#include <thread>
// Publication: data is written, then a flag is set. Compile with -DRELAXED for the broken version.
#ifdef RELAXED
constexpr auto STORE = std::memory_order_relaxed, LOAD = std::memory_order_relaxed;
#else
constexpr auto STORE = std::memory_order_release, LOAD = std::memory_order_acquire;
#endif
int data = 0;
std::atomic<bool> ready{false};
int main() {
  int seen = 0;
  const int rounds = 2000;
  for (int r = 0; r < rounds; ++r) {
    data = 0; ready.store(false, std::memory_order_seq_cst);
    std::jthread producer([] { data = 42; ready.store(true, STORE); });
    std::jthread consumer([&] { while (!ready.load(LOAD)) {} if (data == 42) ++seen; });
  }
  std::printf("rounds where the consumer read 42: %d of %d\n", seen, rounds);
}
```

```text
rounds where the consumer read 42: 2000 of 2000
```

Cả 2000 vòng đều thấy 42, và ThreadSanitizer im lặng với phiên bản này. Trên x86-64, bản relaxed cũng in 2000 trên 2000, vì phần cứng giữ các store theo thứ tự, nên một bài test chạy qua không chứng minh gì cho phiên bản relaxed; ThreadSanitizer (`-fsanitize=thread`, chạy bằng `setarch -R ./a.out` trên kernel này) thì báo cáo nó (trích đoạn):

```text
WARNING: ThreadSanitizer: data race
  Read of size 4 by thread T2:
    #0 operator() e10_5.cpp:18
  Previous write of size 4 by thread T1:
    #0 operator() e10_5.cpp:17
SUMMARY: ThreadSanitizer: data race e10_5.cpp:18 in operator()
```

### Happens-before được định nghĩa chính xác

Định nghĩa data race ở trên dựa trên ba quan hệ của memory model C++ (cppreference, *std::memory_order*, "Formal description"). *Sequenced-before* sắp thứ tự các biểu thức trong cùng một thread. Một thao tác release trên atomic $M$ *synchronizes-with* một thao tác acquire trên $M$ đọc giá trị mà nó đã ghi (hoặc một giá trị trong release sequence của nó). *Inter-thread happens-before* là bao đóng của synchronizes-with kết hợp với sequenced-before; *happens-before* bao gồm sequenced-before. Khi đó một data race chính xác là hai truy cập không-atomic xung đột mà không cái nào happens-before cái kia.

*Chứng minh rằng mẫu flag là đúng.* Trong ví dụ producer/consumer, gọi $W$ là `data = 42`, $S$ là release store của `ready`, $L$ là acquire load trả về `true`, và $R$ là lần đọc `data`. $W$ sequenced-before $S$; $S$ synchronizes-with $L$ vì $L$ đọc giá trị $S$ ghi; $L$ sequenced-before $R$. Ghép lại, $W$ happens-before $R$, nên $R$ không phải race và đọc một visible side effect của $W$, tức 42. Nếu lần tải dùng `relaxed`, không có cạnh synchronizes-with nào, nên $W$ và $R$ là hai truy cập xung đột không có thứ tự: một data race và undefined behavior, không chỉ là "một giá trị cũ".

*Atomic relaxed thậm chí có thể tạo thành chu trình.* Với `x` và `y` ban đầu bằng 0, thread 1 chạy `r1 = y.load(relaxed); x.store(r1, relaxed)` và thread 2 chạy `r2 = x.load(relaxed); y.store(42, relaxed)`. Kết quả `r1 == r2 == 42` được phép: không gì buộc lần store 42 xảy ra sau lần load ở thread 2, và mô hình chỉ cấm các giá trị "out-of-thin-air" phụ thuộc vòng vào chính chúng (cppreference, *Relaxed ordering*). Bài tập 14 yêu cầu bạn chứng minh thứ tự nào cấm được kết quả này.

![Hai dòng thời gian của thread cho thấy chuỗi happens-before từ việc ghi data đến việc đọc nó với release/acquire, và cạnh bị thiếu với relaxed](/lesson-figures/CPP10-2.svg)

*Hình: chứng minh của mục này vẽ thành đồ thị. Cạnh synchronizes-with màu cam chỉ có với release/acquire; bỏ nó đi (relaxed) thì $W$ và $R$ là hai truy cập xung đột không có thứ tự, tức data race.*

**Ví dụ.** Việc tạo thread và `join` là các điểm đồng bộ, nên một giá trị có thể được chuyển vào thread rồi chuyển ra mà không cần atomic nào. Thread đọc `input` (được ghi trước khi nó được tạo) và ghi `output`; thread cha đọc `output` sau `join` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`; với `-DEARLY` thread cha đọc trước `join`):

```cpp
#include <cstdio>
#include <thread>
// Thread creation and join are synchronization points: no atomics needed here.
// Compile with -DEARLY to read the result before join(), which is a data race.
int main() {
  int input = 7, output = 0;                       // written before the thread starts
  std::thread t([&] { output = input * 6; });      // start of t happens-after everything above
#ifdef EARLY
  std::printf("output read before join = %d\n", output);
  t.join();
#else
  t.join();                                        // end of t happens-before join() returns
  std::printf("output read after join  = %d\n", output);
#endif
}
```

```text
output read after join  = 42
```

Việc ghi `input` happens-before lúc thread bắt đầu, và lúc thread kết thúc happens-before lúc `join` trả về, nên mọi truy cập đều có thứ tự: không có race, và kết quả là 42. Dưới ThreadSanitizer (`-fsanitize=thread`, chạy bằng `setarch -R ./a.out` trên kernel này) biến thể `-DEARLY`, đọc `output` trong lúc thread có thể còn đang ghi, bị báo cáo (trích đoạn):

```text
WARNING: ThreadSanitizer: data race
  Write of size 4 by thread T1:
    #0 operator() e10_6.cpp:7
  Previous read of size 4 by main thread:
    #0 main e10_6.cpp:9
SUMMARY: ThreadSanitizer: data race e10_6.cpp:7 in operator()
```

### Sequential consistency, store buffering và vì sao mặc định là `seq_cst`

Xét hai atomic `x`, `y` ban đầu bằng 0; thread 1 chạy `x.store(1); r1 = y.load();` và thread 2 chạy `y.store(1); r2 = x.load();`. Đây là dạng *store-buffering*. Khi cả bốn thao tác là `memory_order_seq_cst`, tất cả xuất hiện trong một thứ tự toàn phần phù hợp với thứ tự chương trình của từng thread (cppreference, *Sequentially-consistent ordering*). **Khẳng định:** $r1=r2=0$ là không thể. *Chứng minh.* Giả sử cả hai lần tải trả về 0. Lần tải $y$ trả về 0 nghĩa là nó đứng trước lần store $y$ của thread 2 trong thứ tự toàn phần $T$; lần tải $x$ trả về 0 nghĩa là nó đứng trước lần store $x$ của thread 1. Cùng với thứ tự chương trình, $T$ sẽ cần $\text{store}_x < \text{load}_y < \text{store}_y < \text{load}_x < \text{store}_x$, một chu trình. Mâu thuẫn. Với chỉ release store và acquire load thì không có thứ tự toàn phần: các lần store không cần hiển thị toàn cục trước khi các lần load chạy (mỗi core có thể giữ store trong store buffer trong khi lần load sau chạy) và $r1=r2=0$ được phép. Trên máy x86-64 với 200.000 vòng, chúng tôi quan sát $r1=r2=0$ ở 0 vòng với `seq_cst`, 630 với release/acquire và 564 với `relaxed`. Vì vậy giao thức loại trừ tương hỗ kiểu Dekker/Peterson viết bằng flag thường cần `seq_cst` (hoặc fence); mutex hoặc atomic `seq_cst` là mặc định an toàn và các thứ tự yếu hơn là tối ưu hóa cần được biện minh.

![Dòng thời gian của phép thử store buffering: cả hai store chờ trong buffer trong khi cả hai load đọc giá trị cũ, cho (0, 0)](/lesson-figures/CPP10-3.svg)

*Hình: vì sao $(r1,r2)=(0,0)$ có thể xảy ra khi không có một thứ tự toàn phần duy nhất. Các load chạy giữa lúc store được phát ra và lúc nó trở nên thấy được; các số đếm ở dưới là kết quả đo của ví dụ bên dưới.*

**Ví dụ.** Phép thử store buffering được chạy 200,000 lần, với một `std::barrier` thả cả hai thread cùng lúc mỗi lần, một lần với các thao tác relaxed và một lần với `seq_cst` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`, một máy có CPU x86-64):

```cpp
#include <atomic>
#include <barrier>
#include <cstdio>
#include <thread>
#include <vector>
// Store buffering: x.store(1); r1 = y.load()  ||  y.store(1); r2 = x.load().  Count r1 == 0 && r2 == 0.
template <std::memory_order MO>
int run(int n) {
  std::vector<std::atomic<int>> x(n), y(n);
  for (int i = 0; i < n; ++i) { x[i].store(0, std::memory_order_relaxed); y[i].store(0, std::memory_order_relaxed); }
  std::vector<int> r1(n), r2(n);
  std::barrier sync(2);
  {
    std::jthread t1([&] { for (int i = 0; i < n; ++i) { sync.arrive_and_wait(); x[i].store(1, MO); r1[i] = y[i].load(MO); } });
    std::jthread t2([&] { for (int i = 0; i < n; ++i) { sync.arrive_and_wait(); y[i].store(1, MO); r2[i] = x[i].load(MO); } });
  }
  int both_zero = 0;
  for (int i = 0; i < n; ++i) both_zero += (r1[i] == 0 && r2[i] == 0);
  return both_zero;
}
int main() {
  const int n = 200000;
  std::printf("relaxed: (0,0) seen in %d of %d runs\n", run<std::memory_order_relaxed>(n), n);
  std::printf("seq_cst: (0,0) seen in %d of %d runs\n", run<std::memory_order_seq_cst>(n), n);
}
```

```text
relaxed: (0,0) seen in 2 of 200000 runs
seq_cst: (0,0) seen in 0 of 200000 runs
```

Với các thao tác relaxed, kết quả mà sequential consistency cấm là $(r1,r2)=(0,0)$ xuất hiện trong 2 lần chạy; với `seq_cst` nó không xuất hiện lần nào trong 200,000. Số đếm nhỏ và thay đổi giữa các lần chạy vì cửa sổ chỉ rộng vài nano giây, nên một bài stress test có thể cho thấy kết quả đó nhưng không bao giờ loại trừ nó; chứng minh ở trên thì có.

### Tránh deadlock bằng thứ tự khóa: chứng minh và giới hạn

Deadlock cần một chu trình trong đồ thị chờ (wait-for graph) (định nghĩa của bài). **Định lý.** Nếu mọi thread chỉ lấy khóa theo thứ tự tăng dần của một rank cố định, deadlock không thể xảy ra. *Chứng minh.* Giả sử các thread $T_1,\dots,T_k$ tạo thành chu trình: $T_i$ giữ khóa $a_i$ và chờ $a_{i+1}$ (chỉ số theo mod $k$). Một thread chờ $a_{i+1}$ khi đang giữ $a_i$ đã lấy $a_i$ trước, nên $\text{rank}(a_i)<\text{rank}(a_{i+1})$. Đi hết vòng ta được $\text{rank}(a_1)<\text{rank}(a_2)<\dots<\text{rank}(a_1)$, không thể. $\square$ Chứng minh cần *mọi* đường lấy khóa đều theo thứ tự, kể cả trong callback: vì vậy CP.22 cấm gọi code không biết khi đang giữ khóa (C++ Core Guidelines, CP.21 và CP.22). `std::scoped_lock` bỏ nhu cầu rank toàn cục bằng một thuật toán tránh deadlock, nhưng cần mọi khóa trong cùng một câu lệnh; các khóa lấy ở những hàm khác nhau vẫn cần một quy ước. Hai cái bẫy: khóa *cùng một* `std::mutex` hai lần trong một thread (ví dụ `transfer(a, a)`) là undefined behavior với mutex không đệ quy, dù có hay không `scoped_lock`; và sắp thứ tự theo địa chỉ (`std::less<>{}(&a.m, &b.m)`) là một rank hợp lệ cho mutex của các đối tượng không liên quan.

**Ví dụ.** Hai tài khoản, $0$ và $1$, và hai lần chuyển tiền theo hai chiều ngược nhau. Phiên bản ngây thơ khóa nguồn trước; một barrier khiến cả hai thread đều giữ khóa đầu, và giới hạn 200 ms cho khóa thứ hai biến việc chờ vĩnh viễn thành một thất bại nhìn thấy được. Phiên bản có thứ tự luôn khóa chỉ số thấp trước, và chạy 200,000 lần chuyển (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`; cũng sạch dưới ThreadSanitizer (`-fsanitize=thread`, chạy bằng `setarch -R ./a.out` trên kernel này)):

```cpp
#include <barrier>
#include <chrono>
#include <cstdio>
#include <mutex>
#include <thread>
using namespace std::chrono_literals;
// Two accounts, two transfers in opposite directions.
struct Account { std::mutex m; int balance; };
Account acc[2] = {{{}, 500000}, {{}, 500000}};
// Lock m, giving up after d (a stand-in for "would wait forever").
bool lock_within(std::mutex& m, std::chrono::milliseconds d) {
  auto end = std::chrono::steady_clock::now() + d;
  while (!m.try_lock()) {
    if (std::chrono::steady_clock::now() > end) return false;
    std::this_thread::sleep_for(1ms);
  }
  return true;
}
// Naive: lock the source, then the destination. A barrier forces both threads to hold their first lock.
bool transfer_naive(int from, int to, int amount, std::barrier<>& both_hold_first) {
  std::lock_guard<std::mutex> a(acc[from].m);
  both_hold_first.arrive_and_wait();
  if (!lock_within(acc[to].m, 200ms)) return false;   // would wait forever: report the deadlock instead
  std::lock_guard<std::mutex> b(acc[to].m, std::adopt_lock);
  acc[from].balance -= amount; acc[to].balance += amount;
  return true;
}
// Ordered: always lock the lower index first.
void transfer_ordered(int from, int to, int amount) {
  int lo = from < to ? from : to, hi = from < to ? to : from;
  std::lock_guard<std::mutex> a(acc[lo].m);
  std::lock_guard<std::mutex> b(acc[hi].m);
  acc[from].balance -= amount; acc[to].balance += amount;
}
int main() {
  std::barrier<> sync(2);
  bool ok1 = true, ok2 = true;
  {
    std::jthread t1([&] { ok1 = transfer_naive(0, 1, 30, sync); });
    std::jthread t2([&] { ok2 = transfer_naive(1, 0, 20, sync); });
  }
  std::printf("naive  : transfer 0->1 completed = %d, transfer 1->0 completed = %d\n", ok1, ok2);
  {
    std::jthread t1([] { for (int i = 0; i < 100000; ++i) transfer_ordered(0, 1, 3); });
    std::jthread t2([] { for (int i = 0; i < 100000; ++i) transfer_ordered(1, 0, 2); });
  }
  std::printf("ordered: 200000 transfers done, balances = %d + %d = %d\n", acc[0].balance, acc[1].balance, acc[0].balance + acc[1].balance);
}
```

```text
naive  : transfer 0->1 completed = 0, transfer 1->0 completed = 1
ordered: 200000 transfers done, balances = 400020 + 599980 = 1000000
```

Ở lần chạy ngây thơ, một lần chuyển bỏ cuộc sau 200 ms (không có giới hạn thì cả hai chờ mãi; bên nào bỏ cuộc thay đổi theo lần chạy), rồi lần còn lại tiếp tục. Phiên bản có thứ tự hoàn tất cả 200,000 lần chuyển, và tổng số dư vẫn là $400{,}020+599{,}980=1{,}000{,}000$, đúng tổng ban đầu như kiểm tra bảo toàn yêu cầu. Chứng minh áp dụng được: cả hai thread khóa theo hạng tăng dần, nên không chu trình nào hình thành.

### Condition variable: bất biến và lập luận mất thông báo (missed notification)

Condition variable không phải một flag; nó là một *hàng đợi các thread đang ngủ* gắn với một predicate trên trạng thái được mutex bảo vệ. Tính đúng đắn gồm ba phần (C++ Core Guidelines, CP.42; cppreference, `std::condition_variable`). (1) Predicate được đọc và quyết định ngủ được thực hiện khi giữ mutex, và `wait` nhả mutex và xếp thread vào hàng đợi một cách nguyên tử; nếu không, một thay đổi trạng thái kèm thông báo có thể rơi vào giữa lúc kiểm tra và lúc ngủ, thông báo bị mất (thread ngủ khi predicate đã đúng). (2) Sau khi thức, predicate được kiểm tra lại dưới khóa được lấy lại, trong một vòng lặp, vì việc thức không chứng minh gì: nó có thể là spurious, hoặc thread khác đã lấy mất phần tử giữa lúc thông báo và lúc thread này lấy được khóa. (3) Mỗi thay đổi trạng thái có thể làm predicate của một waiter nào đó thành đúng phải kèm một thông báo đến được *loại* waiter đó.

Phần (3) là chỗ `notify_one` nguy hiểm. Với một condition variable dùng chung cho waiter "không đầy" và "không rỗng", `notify_one` có thể đánh thức một waiter mà predicate vẫn sai, lần thức bị tiêu tốn, và một waiter lẽ ra tiến được lại tiếp tục ngủ (Bài tập 15). Hai thiết kế an toàn là `notify_all` kèm predicate (đúng, nhưng $O(\text{waiters})$ lần thức mỗi thao tác) và một condition variable cho mỗi predicate với `notify_one`. Một bất biến hữu ích để nêu trong hợp đồng của hàng đợi là: *mỗi khi khóa rảnh, nếu hàng đợi không rỗng thì không có consumer nào đang ngủ có predicate đúng, và nếu không đầy thì không có producer nào đang ngủ có predicate đúng.* Mỗi thao tác phải khôi phục bất biến này trước khi mở khóa, đúng là quy tắc thông báo. Thông báo sau khi mở khóa là được và có thể tiết kiệm một lần chuyển ngữ cảnh, nhưng thông báo *trước* khi đổi trạng thái là lỗi.

**Ví dụ.** Bốn consumer chờ trên *một* condition variable trong khi producer công bố 6 phần tử, cách nhau 20 ms. Mỗi consumer kiểm lại predicate trong vòng lặp, nên cả `notify_one` và `notify_all` đều đúng; chương trình đếm số lần `wait` trả về (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`):

```cpp
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <mutex>
#include <thread>
#include <vector>
using namespace std::chrono_literals;
// Four consumers wait on ONE condition variable; the producer publishes 6 items, 20 ms apart.
// Compare notify_one with notify_all (the predicates make both correct).
struct Run { int taken = 0, wakeups = 0; };
Run run(bool all) {
  std::mutex m; std::condition_variable cv; int items = 0; bool done = false; Run r;
  {
    std::vector<std::jthread> consumers;
    for (int c = 0; c < 4; ++c)
      consumers.emplace_back([&] {
        std::unique_lock<std::mutex> lk(m);
        for (;;) {
          while (items == 0 && !done) { cv.wait(lk); ++r.wakeups; }
          if (items == 0) return;
          --items; ++r.taken;
        }
      });
    std::this_thread::sleep_for(50ms);             // let all four go to sleep
    for (int i = 0; i < 6; ++i) {
      { std::lock_guard<std::mutex> lk(m); ++items; }
      if (all) cv.notify_all(); else cv.notify_one();
      std::this_thread::sleep_for(20ms);
    }
    { std::lock_guard<std::mutex> lk(m); done = true; }
    cv.notify_all();
  }
  return r;
}
int main() {
  Run a = run(false), b = run(true);
  std::printf("notify_one: items taken = %d, wake-ups = %d\n", a.taken, a.wakeups);
  std::printf("notify_all: items taken = %d, wake-ups = %d\n", b.taken, b.wakeups);
}
```

```text
notify_one: items taken = 6, wake-ups = 10
notify_all: items taken = 6, wake-ups = 28
```

Cả hai lần chạy đều giao đủ 6 phần tử. `notify_one` tốn $6+4=10$ lần thức dậy (một lần mỗi phần tử, cộng bốn consumer bị đánh thức bởi `notify_all` cuối cùng kết thúc lần chạy); `notify_all` tốn $6\cdot4+4=28$, vì mỗi phần tử đánh thức cả bốn consumer và ba trong số đó không thấy gì rồi ngủ lại. Đây là phần chi phí của thiết kế an toàn; một condition variable cho mỗi predicate cho phép `notify_one` vừa đúng vừa rẻ.

## Ví dụ có lời giải

### Trường hợp 1: trường hợp cơ bản

**Đề bài.** Một hàng đợi có giới hạn có dung lượng $K=2$. Một producer $P$ đẩy các phần tử $1,2,3$ rồi gọi `close()`; một consumer $C$ lặp `while (auto v = q.pop())`. Lần theo một lần chạy trong đó hàng đợi đầy, nói thread nào bị chặn ở đâu và vì sao, và xác định cái gì được giao.

**Lời giải.** (Hợp đồng ở mục hàng đợi có giới hạn; các quy tắc condition variable ở hai mục đầu.)

1. $P$ khóa, `size=0<2`, đẩy 1, gọi `notify_one(not_empty)`, mở khóa. Hàng đợi: $[1]$.
2. $P$ đẩy 2. Hàng đợi: $[1,2]$, đầy ($\text{size}=K$).
3. $P$ gọi `push(3)`: khóa, predicate `closed || size<2` sai, nên `wait` nguyên tử nhả lock và chặn trên `not_full`. Hàng đợi không đổi: $[1,2]$.
4. $C$ gọi `pop`: khóa, hàng đợi không rỗng, lấy 1, hàng đợi $[2]$, `notify_one(not_full)`, mở khóa, trả về 1.
5. $P$ thức dậy (trong `wait` nó giành lại lock trước), kiểm lại predicate `size<2`: $1<2$ đúng, nên đẩy 3. Hàng đợi $[2,3]$.
6. $C$ lấy 2, rồi 3: hàng đợi rỗng. Lần `pop` thứ tư thấy hàng đợi rỗng và còn mở, nên predicate `closed || !empty` sai và nó chặn trên `not_empty`.
7. $P$ gọi `close()`: đặt `closed` dưới lock, rồi `notify_all` trên cả hai điều kiện. $C$ thức dậy, predicate đúng, hàng đợi rỗng, nên `pop` trả `nullopt` và vòng lặp kết thúc.

![Lưới bảy bước của Trường hợp 1: các ô hàng đợi, trạng thái của P và C, và condition variable mỗi bên chờ](/lesson-figures/CPP10-4.svg)

*Hình: vết của Trường hợp 1 cho hàng đợi dung lượng 2. Đọc mỗi cột từ trên xuống: các ô, P làm gì, C làm gì, thread bị chặn chờ trên gì.*

**Kiểm tra.** Mọi phần tử được giao một lần, theo thứ tự $1,2,3$, nên tổng số được giao là $3$ và tổng giá trị là $6$. Không có bước 7, $C$ sẽ chặn mãi, đó là lý do `close()` tồn tại. Kiểm tra độc lập: bảy bước đó được chạy lại trên `BoundedQueue` của phần cài đặt tham khảo (producer của bước 3 là một thread, một lần sleep ngắn cho thấy nó đang bị chặn):

```cpp
#include <chrono>
#include <cstdio>
#include <thread>
// BoundedQueue<T> exactly as in the Reference implementation section above
using namespace std::chrono_literals;
int main() {
  BoundedQueue<int> q(2);
  bool a = q.try_push(1), b = q.try_push(2), c = q.try_push(3);
  std::printf("steps 1-3: push 1 -> %d, push 2 -> %d, try_push 3 -> %d (full), size = %zu\n", a, b, c, q.size());
  {
    std::jthread producer([&] { q.push(3); });    // blocks on not_full until a slot is free
    std::this_thread::sleep_for(50ms);
    std::printf("step 3  : producer blocked, size still %zu\n", q.size());
    std::printf("step 4  : pop -> %d\n", *q.pop());
  }                                               // producer woke, pushed 3, finished
  std::printf("step 5  : size = %zu\n", q.size());
  int x = *q.pop(), y = *q.pop();
  std::printf("step 6  : pop -> %d, pop -> %d, size = %zu\n", x, y, q.size());
  std::jthread consumer([&] {
    auto v = q.pop();                             // fourth pop: empty and open, so it blocks
    std::printf("step 7  : blocked pop returned %s\n", v ? "a value" : "nullopt");
  });
  std::this_thread::sleep_for(50ms);
  q.close();
}
```

```text
steps 1-3: push 1 -> 1, push 2 -> 1, try_push 3 -> 0 (full), size = 2
step 3  : producer blocked, size still 2
step 4  : pop -> 1
step 5  : size = 2
step 6  : pop -> 2, pop -> 3, size = 0
step 7  : blocked pop returned nullopt
```

**Rút ra.** Mỗi lần chờ gắn với một predicate trên trạng thái, và mỗi thay đổi trạng thái thông báo cho điều kiện mà nó có thể làm đúng; luồng chỉ kết thúc vì `close()` đánh thức mọi bên.

### Trường hợp 2: ba tài khoản và chu trình thứ tự khóa

**Đề bài.** Ba thread chuyển tiền giữa các tài khoản được bảo vệ bởi mutex $m_0,m_1,m_2$: $T_1$: `transfer(0→2)`, $T_2$: `transfer(2→1)`, $T_3$: `transfer(1→0)`. Một lần chuyển khóa mutex nguồn trước, rồi mutex đích. Chứng minh có thể xảy ra deadlock, rồi chứng minh khóa theo thứ tự chỉ số tăng dần loại bỏ nó, và đếm các trường hợp.

**Lời giải.** (Mục deadlock và định lý về hạng trong phần lý thuyết.)

1. **Thứ tự ngây thơ.** Các chuỗi khóa: $T_1:(0,2)$, $T_2:(2,1)$, $T_3:(1,0)$. Lịch: $T_1$ khóa $m_0$, $T_2$ khóa $m_2$, $T_3$ khóa $m_1$. Giờ $T_1$ chờ $m_2$ (do $T_2$ giữ), $T_2$ chờ $m_1$ (do $T_3$ giữ), $T_3$ chờ $m_0$ (do $T_1$ giữ): một chu trình độ dài 3 trong đồ thị wait-for. Không thread nào tiến được.
2. **Thứ tự theo hạng.** Sắp mỗi cặp theo chỉ số, hạng $=$ chỉ số: $T_1:(0,2)$, $T_2:(1,2)$, $T_3:(0,1)$. Giả sử có một chu trình, mỗi thành viên giữ một khóa và chờ một khóa hạng cao hơn; đi hết vòng thì hạng tăng nghiêm ngặt rồi quay về điểm đầu, điều này bất khả. Vậy không có deadlock, theo định lý.
3. **Kiểm tra vét cạn.** Trạng thái $=$ (tiến độ mỗi thread, chủ sở hữu mỗi mutex); thread nhả cả hai khóa khi xong khóa thứ hai. Duyệt mọi đan xen, phiên bản ngây thơ có 27 trạng thái đạt được và 1 trạng thái deadlock (cái ở bước 1); phiên bản theo hạng có 24 trạng thái đạt được và 0 trạng thái deadlock.
4. **Sửa trong code.** `std::scoped_lock lk(acct[from].m, acct[to].m);` tránh được thứ tự tường minh và cần tiền điều kiện `from != to`, vì khóa cùng một mutex không đệ quy hai lần là undefined behavior.
5. **Hợp đồng.** Tiền được bảo toàn: tổng số dư trước và sau bằng nhau, một test có thể khẳng định sau khi join các thread, cùng với ThreadSanitizer để loại trừ race trên các số dư.

![Trái: chu trình wait-for của ba thread với thứ tự khóa ngây thơ. Phải: thứ tự theo hạng, nơi mọi lần khóa đều đi lên](/lesson-figures/CPP10-5.svg)

*Hình: hai thứ tự khóa của Trường hợp 2. Các mũi tên đỏ nét đứt bên trái khép thành một chu trình; bên phải mọi mũi tên chỉ tới hạng cao hơn, nên lập luận chu trình của phần lý thuyết không thể hoàn tất.*

**Kiểm tra.** Một phép tìm kiếm bằng Python trên mọi đan xen của ba chuỗi hai bước tái tạo bước 3: `(27, 1)` cho thứ tự ngây thơ và `(24, 0)` cho thứ tự theo hạng. Thứ tự theo hạng có chuỗi dài nhất $0<1<2$, nên lập luận về hạng bao trùm cả ba lần chuyển.

**Rút ra.** Deadlock cần một chu trình; một thứ tự toàn cục của các khóa khiến chu trình bất khả, và tìm kiếm vét cạn trên mô hình nhỏ xác nhận điều đó.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: C++ Core Guidelines, CP.2 and CP.3)* Trường hợp nào trong số này là data race? (a) hai thread đọc cùng một `const int`; (b) một thread ghi một `int`, thread khác đọc nó, không đồng bộ; (c) hai thread làm `fetch_add` trên một `std::atomic<int>`; (d) thread 1 ghi `v[0]`, thread 2 ghi `v[1]` của một `std::vector<int>` đã định kích thước trước. Trường hợp nào vẫn có thể chậm, và vì sao?
2. **(Dễ)** Hai thread mỗi thread thực hiện `++counter` $3\times10^5$ lần trên một `int` thường; một lần chạy in ra 583,904. Mất bao nhiêu cập nhật và đó là bao nhiêu phần trăm? Viết một đan xen của chuỗi nạp/cộng/lưu làm mất một cập nhật, và nêu hai cách sửa.
3. **(Dễ)** Viết lại bằng RAII để mutex được nhả trên mọi đường đi:
   ```cpp
   m.lock();
   if (queue.empty()) return false;
   x = queue.front(); queue.pop();
   m.unlock();
   return true;
   ```
4. **(Trung bình)** *(Adapted from: C++ Core Guidelines, CP.42)* Tìm các bug trong consumer này và sửa nó.
   ```cpp
   std::unique_lock<std::mutex> lk(m);
   if (q.empty()) cv.wait(lk);
   auto v = q.front();
   q.pop();
   ```
5. **(Trung bình)** *(Adapted from: C++ Core Guidelines, CP.21)* `transfer(a, b)` khóa `a.m` rồi `b.m`; một thread khác gọi `transfer(b, a)`. Giải thích deadlock, chỉ ra đan xen, và sửa bằng `std::scoped_lock`.
6. **(Trung bình)** Chương trình này làm gì và vì sao? Nêu hai cách sửa.
   ```cpp
   int main() { std::thread t([] { std::cout << "work\n"; }); }
   ```
7. **(Trung bình)** `BoundedQueue::size()` là `const` nhưng khóa một mutex; vì sao mutex phải là `mutable`? Một caller viết `if (q.size() < cap) q.push(x);`. Giải thích race check-then-act và lời gọi đúng.
8. **(Khó)** *(Adapted from: cppreference, std::condition_variable example)* Một cảm biến phát đợt 90 phần tử trong 30 ms; consumer xử lý 500 phần tử/s. Tính lượng tồn đọng ở cuối đợt, thời gian xả, và dung lượng tối thiểu để producer không bao giờ bị chặn. Độ trễ của phần tử cuối đợt là bao nhiêu?
9. **(Khó)** *(Adapted from: cppreference, std::memory_order)* Giải thích vì sao mẫu cờ release/acquire trong phần lý thuyết là đúng và điều gì sai với `memory_order_relaxed` cho cả hai thao tác. Khi nào bạn dùng mutex thay vào đó?
10. **(Khó)** Thiết kế. Một control thread phải luôn dùng lần đọc cảm biến mới nhất, bỏ qua các lần cũ hơn; một logger phải thấy mọi lần đọc. Đặc tả (i) một mailbox `Latest<T>`, (ii) hàng đợi cho logger, cùng hợp đồng khóa của chúng, và chuyện gì xảy ra khi logger chậm hơn cảm biến. Cái nào có giới hạn, và "drop" nghĩa là gì với mỗi cái?
11. **(Mini-project)** Đo thông lượng (phần tử mỗi giây) của hàng đợi của bạn với 1 producer và 1 consumer cho dung lượng 1, 8 và 1024 và $10^6$ phần tử; giải thích xu hướng; thêm `pop_for(std::chrono::milliseconds)` dùng `wait_for`; chạy tất cả dưới ThreadSanitizer.

12. **(Challenge)** Store buffering. Thread 1: `x.store(1); r1 = y.load();` thread 2: `y.store(1); r2 = x.load();` với `x = y = 0`. (a) Liệt kê mọi xen kẽ giữ thứ tự chương trình (có $\binom42=6$) và $(r1,r2)$ kết quả; bao nhiêu cái cho $r1=r2=1$? (b) Chứng minh $(0,0)$ không thể xảy ra khi cả bốn thao tác là `seq_cst`. (c) Giải thích vì sao $(0,0)$ có thể xảy ra với release store và acquire load, và nêu một thay đổi tối thiểu cấm nó. (d) Bạn kết luận gì về một giao thức loại trừ tương hỗ dùng flag viết bằng release/acquire? (adapted from cppreference, *std::memory_order*, "Sequentially-consistent ordering" and "Release-Acquire ordering")
13. **(Challenge)** Thứ tự khóa. Năm triết gia ngồi quanh bàn với năm cái nĩa (mutex $f_0,\dots,f_4$); triết gia $i$ cần nĩa $i$ và $(i+1)\bmod5$. (a) Chỉ ra một xen kẽ mà quy tắc ngây thơ "nĩa trái rồi nĩa phải" bị deadlock. (b) Chứng minh quy tắc "luôn lấy nĩa số nhỏ hơn trước" không thể deadlock, dùng lập luận rank. Hành vi của triết gia nào thay đổi? (c) Vì sao `std::scoped_lock lk(f[i], f[(i+1)%5])` cũng hoạt động, và điều gì sai với bàn có một triết gia và một nĩa? (adapted from C++ Core Guidelines, CP.21 and CP.22)
14. **(Challenge)** Chu trình relaxed. Thread 1: `r1 = y.load(); x.store(r1);` thread 2: `r2 = x.load(); y.store(42);`, `x = y = 0`. (a) Chứng minh $r1=r2=42$ không thể nếu mọi thao tác là `seq_cst`. (b) Chứng minh nó cũng không thể nếu các load là `acquire` và các store là `release`, bằng cách tìm một chu trình trong happens-before. (c) Vì sao nó được phép khi mọi thứ là `relaxed`? (d) Vì sao nó không liên quan đến hàng đợi dùng mutex của bài? (adapted from cppreference, *std::memory_order*, "Relaxed ordering")
15. **(Challenge)** Một lỗi liveness. Một hàng đợi có giới hạn dung lượng 1 dùng *một* condition variable `cv` cho cả hai điều kiện (không đầy / không rỗng) và gọi `notify_one()` sau mỗi thay đổi. (a) Dựng một lịch với hai producer và hai consumer kết thúc bằng cả bốn thread bị chặn dù hàng đợi đang chứa một phần tử. (b) Nêu hai cách sửa khác nhau và so sánh chi phí. (c) Phiên bản `if` kiểu "kiểm tra rồi hành động" còn vi phạm quy tắc nào của CP.42? (adapted from C++ Core Guidelines, CP.42; the schedule is the standard missed-notification argument)

## Cài đặt tham khảo

Trước hết là thí nghiệm ba counter (race, atomic, mutex), rồi đến hàng đợi có giới hạn.

```cpp
// Three ways to count to 2,000,000 from two threads.
#include <atomic>
#include <iostream>
#include <mutex>
#include <thread>

int plain = 0;                 // data race: undefined behavior
std::atomic<int> atomic_count{0};
int locked = 0;
std::mutex m;

int main() {
  auto work = [] {
    for (int i = 0; i < 1000000; ++i) {
      ++plain;                               // (1) unsynchronized
      atomic_count.fetch_add(1);             // (2) atomic read-modify-write
      std::lock_guard<std::mutex> lk(m);     // (3) mutex-protected
      ++locked;
    }
  };
  std::thread a(work), b(work);
  a.join();
  b.join();
  std::cout << "plain=" << plain << " atomic=" << atomic_count << " locked=" << locked << "\n";
}
```

Output điển hình trên máy của bài: `plain=1988346 atomic=2000000 locked=2000000` (giá trị plain khác nhau mỗi lần chạy). Dưới ThreadSanitizer (`g++ -std=c++17 -g -O1 -pthread -fsanitize=thread race.cpp`; trên một số kernel chạy dưới dạng `setarch $(uname -m) -R ./a.out` nếu bạn thấy "unexpected memory mapping") TSan báo `WARNING: ThreadSanitizer: data race` chỉ vào dòng `++plain`, kèm hai thread xung đột.

```cpp
// CPP10 reference: a bounded blocking queue with an explicit locking contract.
#include <condition_variable>
#include <cstddef>
#include <deque>
#include <iostream>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>

// Locking contract:
//  * Every member function takes the single mutex m_ for its whole critical section.
//  * push blocks while full; pop blocks while empty; both are woken by close().
//  * After close(): push returns false (nothing enqueued); pop drains remaining items, then
//    returns std::nullopt. close() is idempotent.
//  * FIFO order is preserved. One mutex, no callbacks run under the lock => no deadlock.
template <class T>
class BoundedQueue {
 public:
  explicit BoundedQueue(std::size_t capacity) : cap_(capacity) {
    if (capacity == 0) throw std::invalid_argument("capacity must be > 0");
  }
  BoundedQueue(const BoundedQueue&) = delete;
  BoundedQueue& operator=(const BoundedQueue&) = delete;

  bool push(T v) {
    std::unique_lock<std::mutex> lk(m_);
    not_full_.wait(lk, [&] { return closed_ || q_.size() < cap_; });
    if (closed_) return false;
    q_.push_back(std::move(v));
    not_empty_.notify_one();
    return true;
  }

  bool try_push(T v) {
    std::lock_guard<std::mutex> lk(m_);
    if (closed_ || q_.size() >= cap_) return false;
    q_.push_back(std::move(v));
    not_empty_.notify_one();
    return true;
  }

  std::optional<T> pop() {
    std::unique_lock<std::mutex> lk(m_);
    not_empty_.wait(lk, [&] { return closed_ || !q_.empty(); });
    if (q_.empty()) return std::nullopt;  // closed and drained
    T v = std::move(q_.front());
    q_.pop_front();
    not_full_.notify_one();
    return v;
  }

  void close() {
    {
      std::lock_guard<std::mutex> lk(m_);
      closed_ = true;
    }
    not_full_.notify_all();
    not_empty_.notify_all();
  }

  std::size_t size() const {
    std::lock_guard<std::mutex> lk(m_);
    return q_.size();
  }

 private:
  mutable std::mutex m_;
  std::condition_variable not_full_, not_empty_;
  std::deque<T> q_;
  const std::size_t cap_;
  bool closed_ = false;
};

// ---- self-test
int main() {
  BoundedQueue<int> q(2);
  if (!q.try_push(1) || !q.try_push(2) || q.try_push(3)) return 1;
  if (*q.pop() != 1) return 2;
  long long sum = 0;
  std::thread consumer([&] {
    while (auto v = q.pop()) sum += *v;
  });
  for (int i = 10; i < 20; ++i) q.push(i);
  q.close();
  consumer.join();
  if (sum != 2 + 145) return 3;
  std::cout << "CPP10 reference self-test passed\n";
}
```

## Thực hành độc lập

### Mục tiêu

Cài đặt một hàng đợi chặn có giới hạn với ngữ nghĩa close và chứng minh, bằng các test chặn và đánh thức thread, rằng nó đúng và không có race.

### Chuẩn bị

`g++` hoặc `clang++` với C++17 và `-pthread`. Lưu starter và các test thành `lab.cpp`. Build các test bằng `g++ -std=c++17 -Wall -Wextra -g -pthread -fsanitize=address,undefined lab.cpp -o lab && ./lab`, và riêng với `-fsanitize=thread` (không kết hợp được với ASan).

### Nhiệm vụ

1. Thêm các member và cài đặt constructor, `size` và `try_push`; chạy phần đơn thread của các test trong đầu trước.
2. Cài đặt `push` và `pop` với `wait` và một predicate; đảm bảo mỗi lời gọi notify đúng condition variable.
3. Cài đặt `close()`; kiểm tra các test giải phóng thread bị chặn (chúng thất bại sau timeout 3 giây nếu bạn quên `notify_all`).
4. Chạy stress test 20 lần trong một vòng lặp (`for i in $(seq 20); do ./lab; done`).
5. Build với ThreadSanitizer và xác nhận không có cảnh báo.
6. Cố ý đưa vào một bug (ví dụ đọc `closed_` không có lock trong `size()` hoặc dùng `if` thay vì predicate) và quan sát TSan hay stress test báo gì; rồi khôi phục.

### Code khởi đầu

```cpp
#include <condition_variable>
#include <cstddef>
#include <deque>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <thread>
#include <utility>

// Locking contract to implement (write it in a comment above your class too):
//  * One mutex guards ALL state (the deque and the closed flag).
//  * push blocks while the queue is full; pop blocks while it is empty; close() wakes everyone.
//  * After close(): push returns false and enqueues nothing; pop still drains remaining items and
//    then returns std::nullopt. close() may be called more than once.
//  * FIFO order. Use condition_variable::wait WITH A PREDICATE (spurious wake-ups are allowed).
template <class T>
class BoundedQueue {
 public:
  explicit BoundedQueue(std::size_t capacity) { throw std::logic_error("NotImplemented"); }  // capacity 0 -> std::invalid_argument
  BoundedQueue(const BoundedQueue&) = delete;
  BoundedQueue& operator=(const BoundedQueue&) = delete;

  bool push(T v) { throw std::logic_error("NotImplemented"); }      // blocks while full; false if closed
  bool try_push(T v) { throw std::logic_error("NotImplemented"); }  // never blocks; false if full or closed
  std::optional<T> pop() { throw std::logic_error("NotImplemented"); }  // blocks while empty and open
  void close() { throw std::logic_error("NotImplemented"); }
  std::size_t size() const { throw std::logic_error("NotImplemented"); }

 private:
  // add your members here: mutex (mutable), two condition variables, deque, capacity, closed flag
};
```

### Kiểm thử

```cpp

// ---- tests (paste below the starter code)
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <future>
#include <iostream>
#include <vector>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)

int main() {
  using namespace std::chrono_literals;
  // 1. single-thread semantics
  bool threw = false;
  try { BoundedQueue<int> bad(0); } catch (const std::invalid_argument&) { threw = true; }
  CHECK(threw);
  BoundedQueue<int> q(2);
  CHECK(q.size() == 0 && q.try_push(1) && q.try_push(2) && !q.try_push(3) && q.size() == 2);
  CHECK(q.pop().value() == 1 && q.pop().value() == 2);   // FIFO
  CHECK(q.try_push(7));
  q.close();
  q.close();                                              // idempotent
  CHECK(!q.push(8) && !q.try_push(9));                    // closed: nothing enqueued
  CHECK(q.pop().value() == 7 && !q.pop());                // drains, then nullopt
  // 2. blocked consumer is released by close() (a hang here shows as a failure after 3 s)
  BoundedQueue<int> e(4);
  auto blocked = std::async(std::launch::async, [&] { return e.pop(); });
  std::this_thread::sleep_for(50ms);
  CHECK(blocked.wait_for(10ms) == std::future_status::timeout);   // really blocked
  e.close();
  CHECK(blocked.wait_for(3s) == std::future_status::ready && !blocked.get());
  // 3. blocked producer is released by close() and by a pop
  BoundedQueue<int> f(1);
  CHECK(f.push(1));
  auto prod = std::async(std::launch::async, [&] { return f.push(2); });
  std::this_thread::sleep_for(50ms);
  CHECK(prod.wait_for(10ms) == std::future_status::timeout);
  CHECK(f.pop().value() == 1);
  CHECK(prod.wait_for(3s) == std::future_status::ready && prod.get());
  CHECK(f.pop().value() == 2);
  auto prod2 = std::async(std::launch::async, [&] { return f.push(3) && f.push(4); });
  std::this_thread::sleep_for(50ms);
  f.close();
  CHECK(prod2.wait_for(3s) == std::future_status::ready && !prod2.get());
  // 4. stress: 4 producers x 2500 items, 3 consumers; nothing lost or duplicated, per-producer order kept
  const int P = 4, N = 2500, C = 3;
  BoundedQueue<long long> s(8);
  std::vector<std::thread> producers, consumers;
  std::atomic<long long> total{0}, count{0};
  std::vector<std::vector<long long>> seen(C);
  for (int p = 0; p < P; ++p)
    producers.emplace_back([&, p] { for (int i = 0; i < N; ++i) s.push(p * 1000000LL + i); });
  for (int c = 0; c < C; ++c)
    consumers.emplace_back([&, c] { while (auto v = s.pop()) { total += *v; ++count; seen[c].push_back(*v); } });
  for (auto& t : producers) t.join();
  s.close();
  for (auto& t : consumers) t.join();
  long long expected = 0;
  for (int p = 0; p < P; ++p) for (int i = 0; i < N; ++i) expected += p * 1000000LL + i;
  CHECK(count == P * N && total == expected);
  for (auto& v : seen) {                                  // order of each producer inside one consumer
    long long last[P];
    for (long long& l : last) l = -1;
    for (long long x : v) { int p = static_cast<int>(x / 1000000); long long i = x % 1000000; CHECK(i > last[p]); last[p] = i; }
  }
  CHECK(s.size() == 0);
  std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi

```
all tests passed
```

Với các stub, test đầu tiên abort với `NotImplemented`. Thiếu `notify_all` trong `close()` hiện ra dưới dạng `FAIL ... ready` sau timeout; với ThreadSanitizer, thiếu lock hiện ra dưới dạng `data race`.

### Thử thách mở rộng

Thêm `pop_for(timeout)` và `push_for(timeout)`, rồi xây một mailbox giá trị mới nhất `Latest<T>` với `set`, `get` và một bộ đếm phiên bản để consumer biết một giá trị có mới không.

### Thực hành với thư viện

Các khối xây dựng của standard library ngoài `mutex` và `condition_variable`: `std::async`/`std::future` (một thread *trả về* kết quả của nó, nên không cần bộ tích lũy dùng chung) và `std::shared_mutex` (nhiều reader, một writer) cho mailbox `Latest<T>` của bài tập 10. Dán đoạn này sau `BoundedQueue` đã hoàn thiện của bạn (nó có `main` riêng, nên bỏ `main` của phần test) và build bằng `g++ -std=c++17 -Wall -Wextra -g -O1 -pthread`, rồi lần nữa với `-fsanitize=thread` (chạy dưới dạng `setarch $(uname -m) -R ./a.out` nếu TSan phàn nàn về memory mapping).

```cpp
#include <atomic>
#include <cassert>
#include <chrono>
#include <future>
#include <iostream>
#include <numeric>
#include <shared_mutex>
#include <vector>

// A latest-value mailbox (exercise 10) with std::shared_mutex: many readers, one writer.
template <class T>
class Latest {
 public:
  void set(T v) { std::unique_lock<std::shared_mutex> lk(m_); v_ = std::move(v); ++version_; }
  std::pair<T, unsigned long> get() const { std::shared_lock<std::shared_mutex> lk(m_); return {v_, version_}; }
 private:
  mutable std::shared_mutex m_;
  T v_{};
  unsigned long version_ = 0;
};

int main() {
  // 1. std::async + std::future: threads that RETURN a result (no shared sum, no race on it)
  BoundedQueue<int> q(8);
  auto producer = std::async(std::launch::async, [&] { for (int i = 1; i <= 1000; ++i) q.push(i); q.close(); return 1000; });
  auto consumer = std::async(std::launch::async, [&] { long long s = 0; while (auto v = q.pop()) s += *v; return s; });
  assert(producer.get() == 1000);
  assert(consumer.get() == 500500);                      // 1 + 2 + ... + 1000

  // 2. the lost-update experiment, three ways, with the result checked
  std::atomic<int> a{0};
  int plain_but_locked = 0;
  std::mutex mu;
  auto work = [&] { for (int i = 0; i < 100000; ++i) { a.fetch_add(1, std::memory_order_relaxed); std::lock_guard<std::mutex> lk(mu); ++plain_but_locked; } };
  auto f1 = std::async(std::launch::async, work), f2 = std::async(std::launch::async, work);
  f1.get(); f2.get();
  assert(a == 200000 && plain_but_locked == 200000);

  // 3. mailbox: the reader always sees a value and a non-decreasing version, writers never block on readers
  Latest<int> box;
  std::atomic<bool> stop{false};
  auto reader = std::async(std::launch::async, [&] { unsigned long last = 0; while (!stop) { auto [v, ver] = box.get(); assert(ver >= last); last = ver; (void)v; } return last; });
  for (int i = 1; i <= 10000; ++i) box.set(i);
  stop = true;
  assert(reader.get() <= 10000 && box.get().first == 10000);
  std::cout << "library track ok\n";
}
```

Output mong đợi: `library track ok`, không có cảnh báo ThreadSanitizer. Câu hỏi: vì sao consumer trả về future không cần mutex quanh `s`? TSan sẽ nói gì nếu `Latest::set` bỏ qua `unique_lock` của nó?

## Kiểm chứng

- Chạy dưới ThreadSanitizer: một lần chạy sạch là bằng chứng mạnh về việc không có data race trên các đường đã được thực thi.
- Stress với nhiều thread hơn số lõi và dung lượng rất nhỏ (1, 2): chúng tối đa hóa số đan xen và việc chặn.
- Kiểm tra các bất biến ở cuối: số phần tử vào = số phần tử ra, tổng khớp, thứ tự theo từng producer được bảo toàn, `size()==0`.
- Kiểm thử hành vi chặn một cách tường minh: phải thấy một thread bị chặn (`wait_for(10ms) == timeout`), rồi được giải phóng bởi hành động đang được kiểm thử, dùng timeout để biến một lần treo thành thất bại.
- Lặp lại hàng trăm lần (`ctest --repeat until-fail:200`); một thất bại hiếm vẫn là thất bại.
- Rà soát hợp đồng: với mỗi biến dùng chung, ghi rõ mutex hay atomic nào bảo vệ nó.

## Lỗi thường gặp

| Sai lầm | Triệu chứng |
|---|---|
| Counter hoặc cờ không đồng bộ | mất cập nhật (ở đây 11,654 trên 2,000,000), đọc dữ liệu cũ, TSan `data race` |
| `if (q.empty()) cv.wait(lk);` | sai với spurious wake-up hoặc nhiều consumer: pop từ hàng đợi rỗng |
| Notify mà không đổi trạng thái dưới lock | mất wake-up, thread ngủ mãi |
| Quên `notify_all` trong `close()` | consumer hoặc producer treo khi tắt |
| Khóa hai mutex theo thứ tự khác nhau | deadlock, chương trình đóng băng |
| `std::thread` bị hủy mà không `join` | `terminate called without an active exception` |
| Giữ lock khi gọi callback hoặc làm I/O | đỉnh độ trễ, deadlock khi callback khóa lại |
| Check-then-act (`if (size() < cap) push`) | race giữa lúc kiểm tra và lúc hành động; dùng một thao tác nguyên tử (`try_push`) |
| `volatile` dùng làm đồng bộ hóa | không phải cơ chế đồng bộ trong C++; dùng `std::atomic` |
| Thread detach dùng reference tới biến cục bộ | dùng sau khi biến cục bộ bị hủy |

## Phương án khác và đánh đổi

- **Mutex so với atomic.** Atomic tốt nhất cho một cờ hay counter; mutex đơn giản và an toàn hơn khi nhiều biến phải đổi cùng nhau.
- **Hàng đợi chặn so với hàng đợi lock-free.** Ring buffer lock-free (một producer một consumer) có độ trễ thấp hơn và không có priority inversion, nhưng tinh vi khi viết và kiểm thử; hãy bắt đầu với phiên bản mutex và đo.
- **Hàng đợi so với mailbox giá trị mới nhất.** Dùng hàng đợi khi mọi phần tử đều quan trọng (logging, lệnh); dùng mailbox (ghi đè) khi chỉ giá trị mới nhất quan trọng (đầu vào điều khiển).
- **Có giới hạn so với không giới hạn.** Hàng đợi không giới hạn che giấu quá tải dưới dạng bộ nhớ tăng và độ trễ; hàng đợi có giới hạn làm quá tải hiện ra dưới dạng back-pressure hoặc drop.
- **Thread so với task bất đồng bộ (`std::async`, thread pool) so với executor.** Pool giảm chi phí tạo thread; executor của ROS 2 lập lịch callback trên một tập thread cố định, với callback group để kiểm soát loại trừ tương hỗ.
- **Thread dùng chung bộ nhớ so với process.** Process cô lập lỗi và tránh race trên bộ nhớ, với cái giá là copy hoặc IPC bộ nhớ chia sẻ; các node ROS 2 trong process riêng dùng message.
- **Mối quan tâm real-time.** Mutex có thể gây priority inversion; vòng điều khiển real-time dùng mutex thừa kế ưu tiên, cấu trúc lock-free, hoặc tránh chia sẻ.

## Vận dụng và ghi nhớ

Python có cùng các khái niệm dưới tên khác (`threading.Lock`, `queue.Queue` với `put/get`, `Condition`), cộng với global interpreter lock hạn chế việc dùng CPU song song nhưng không ngăn race trên các thao tác phức hợp. Trong ROS 2, callback chạy trên các thread của executor và các biến thành viên dùng chung cần cùng sự bảo vệ; callback group của `rclcpp` là các nhóm loại trừ tương hỗ. GPU có quy tắc memory ordering riêng. Để ghi nhớ: sau vài ngày, viết từ trí nhớ mẫu `wait`-có-predicate và mẫu `scoped_lock` và giải thích vì sao mỗi cái tồn tại; và nêu ba điều kiện của deadlock.

## Đáp án bài tập

1. (a) không race (chỉ đọc). (b) race. (c) không race (atomic). (d) không race (đối tượng khác nhau). (d) vẫn có thể chậm vì các phần tử liền kề thường dùng chung một cache line 64 byte (false sharing): line nảy qua lại giữa các lõi.
2. Mất: $600{,}000-583{,}904=16{,}096$, tức $2.68\%$. Đan xen: A nạp 5; B nạp 5; A cộng và lưu 6; B cộng và lưu 6; hai lần tăng, cuối cùng 6. Cách sửa: `std::atomic<int>` với `fetch_add`, hoặc một `std::mutex` với `lock_guard` quanh phép tăng, hoặc một counter riêng cho mỗi thread được cộng lại ở cuối (không chia sẻ).
3. `{ std::lock_guard<std::mutex> lk(m); if (queue.empty()) return false; x = queue.front(); queue.pop(); return true; }`: lock được nhả khi `lk` ra khỏi scope ở cả hai lệnh return (và khi có exception do `front`/`pop` hay phép copy ném ra).
4. Bug 1: `if` thay vì vòng lặp hoặc predicate: sau một spurious wake-up, hoặc nếu consumer khác đã lấy phần tử, `q.front()` bị gọi trên hàng đợi rỗng. Bug 2 (thiết kế): không có cách dừng chờ khi tắt. Cách sửa: `cv.wait(lk, [&]{ return closed || !q.empty(); }); if (q.empty()) return std::nullopt;`.
5. Thread 1 khóa `a.m`, thread 2 khóa `b.m`; rồi thread 1 chờ `b.m` do thread 2 giữ, và thread 2 chờ `a.m`: một chu trình, nên cả hai chờ mãi mãi. Cách sửa: `std::scoped_lock lk(from.m, to.m);` (lấy cả hai mà không deadlock bất kể thứ tự đối số); hoặc áp đặt thứ tự toàn cục, chẳng hạn theo địa chỉ.
6. Đối tượng thread bị hủy khi còn joinable, nên `std::terminate` được gọi: output `terminate called without an active exception` và mã thoát 134. Cách sửa: `t.join();` trước khi return, hoặc dùng `std::jthread` (C++20), hoặc một wrapper RAII nhỏ join trong destructor.
7. `size()` về mặt logic là `const` (không đổi hàng đợi) nhưng phải khóa mutex, thứ làm đổi trạng thái nội bộ của mutex; khai báo mutex là `mutable` cho phép điều đó. `if (q.size() < cap) q.push(x);` là một race check-then-act: một thread khác có thể làm đầy hàng đợi giữa hai lời gọi, nên `push` có thể chặn (hoặc vượt chính sách dự định). Dùng `try_push(x)`, thực hiện cả phép kiểm tra và phép chèn trong một vùng găng.
8. Đợt phát: consumer lấy đi $500\times0.03=15$ phần tử trong 30 ms, nên tồn đọng là $90-15=75$ phần tử. Thời gian xả $75/500=0.15$ s. Dung lượng tối thiểu để không chặn: 75 (cộng một phần tử đang được xử lý). Phần tử cuối của đợt là phần tử thứ 75 trong backlog, nên nó xong sau $75/500=0.15$ s, đó là độ trễ của nó (đã gồm $2$ ms xử lý của chính nó).
9. Release store xảy ra sau `data = 42`; acquire load đọc `true` đồng bộ hóa với nó, tạo một cạnh happens-before từ việc ghi `data` tới việc đọc, nên đọc `data` không có race và thấy 42. Với các thao tác relaxed không có thứ tự giữa cờ và `data`: compiler hoặc CPU có thể sắp xếp lại, và việc đọc `data` là một data race (undefined behavior). Dùng mutex khi hơn một biến phải nhất quán hoặc logic phức tạp hơn một cờ.
10. `Latest<T>`: hợp đồng: một mutex bảo vệ một `T` và một bộ đếm phiên bản; `set` ghi đè, không bao giờ chặn quá lock ngắn; `get` trả về một bản copy và phiên bản; "drop" = giá trị cũ bị bỏ khi bị thay thế. Hàng đợi của logger: có giới hạn, FIFO, `push` chặn (back-pressure lên thread cảm biến, thường không chấp nhận được) hoặc `try_push` bỏ phần tử mới nhất và tăng bộ đếm drop. Nếu logger chậm hơn, mailbox che giấu điều đó (bộ điều khiển không bị ảnh hưởng); hàng đợi logger hoặc chặn producer hoặc drop; các hệ thống thật chọn drop-kèm-bộ-đếm cho cảm biến và dung lượng lớn hơn cùng một thread logging riêng.
11. Một câu trả lời tốt gồm: dung lượng 1 buộc một lần chuyển ngữ cảnh cho mỗi phần tử, nên thông lượng thấp nhất (hàng trăm nghìn đến khoảng một triệu phần tử/s tùy máy); dung lượng 8 và 1024 cho phép gom lô và thông lượng tăng rồi phẳng ra; `pop_for` trả về `std::optional<T>` và dùng `not_empty_.wait_for(lk, timeout, predicate)` trả false khi hết thời gian; TSan không báo cảnh báo nào.
12. (a) Các thao tác: $a$ = `x.store(1)`, $b$ = `r1=y.load()` (thread 1, $a$ trước $b$), $c$ = `y.store(1)`, $d$ = `r2=x.load()` ($c$ trước $d$). Sáu thứ tự và kết quả: $abcd\to(0,1)$; $acbd\to(1,1)$; $acdb\to(1,1)$; $cabd\to(1,1)$; $cadb\to(1,1)$; $cdab\to(1,0)$. Vậy 4 trong 6 cho $(1,1)$, một cho $(0,1)$, một cho $(1,0)$, và $(0,0)$ không bao giờ xuất hiện (liệt kê bằng script). (b) Giả sử $r1=0$ và $r2=0$ với một thứ tự toàn phần $T$ phù hợp thứ tự chương trình. $b$ đọc 0, nên $b$ đứng trước $c$ trong $T$ (nếu không nó đã đọc 1). Tương tự $d$ đứng trước $a$. Thứ tự chương trình cho $a<b$ và $c<d$. Do đó $a<b<c<d<a$, một chu trình trong một thứ tự toàn phần: mâu thuẫn. (c) Với release/acquire không có thứ tự toàn phần giữa các biến atomic khác nhau; mô hình cho phép store vào `x` của thread 1 còn nằm trong store buffer trong khi lần load `y` sau đó chạy, và đối xứng cho thread 2, nên cả hai lần load thấy 0. Thí nghiệm (200.000 vòng, x86-64, `g++ -O2`): $(0,0)$ ở 0 vòng với `seq_cst`, 630 với release/acquire và 564 với relaxed. Thay đổi tối thiểu: làm các store và load thành `seq_cst`, hoặc đặt `std::atomic_thread_fence(std::memory_order_seq_cst)` giữa store và load ở mỗi thread. (d) Một giao thức như Dekker, nơi mỗi thread đặt flag rồi đọc flag của thread kia, đúng là dạng này, nên với release/acquire cả hai thread có thể vào vùng găng; nó cần `seq_cst` (hoặc dùng mutex).
13. (a) Triết gia $i$ khóa $f_i$ rồi $f_{(i+1)\bmod5}$. Nếu cả năm thực hiện lần khóa đầu trước bất kỳ lần khóa thứ hai nào, triết gia $i$ giữ $f_i$ và chờ $f_{i+1}$ do $i+1$ giữ: một chu trình độ dài 5. (b) Đặt rank của nĩa $j$ là $j$. Các triết gia $0,\dots,3$ đã khóa nĩa nhỏ trước ($i<i+1$). Triết gia 4 cần nĩa 4 và 0, và theo quy tắc mới khóa $f_0$ trước rồi $f_4$ (thay đổi hành vi duy nhất). Theo định lý mọi lần lấy khóa đều theo rank tăng, nên không có chu trình. Cụ thể chu trình bị phá vì triết gia 4 không thể giữ $f_4$ trong khi chờ $f_0$. (c) `scoped_lock` với nhiều mutex dùng thuật toán tránh deadlock, nên lập luận không phụ thuộc thứ tự các đối số (CP.21). Với một triết gia và một nĩa, hai đối số là cùng mutex `f[0]`, bị một thread khóa hai lần: undefined behavior với `std::mutex` không đệ quy (thường là tự deadlock), không thứ tự nào sửa được; hãy kiểm tra `i != j` hoặc dùng một khóa.
14. (a) Gọi thứ tự toàn phần là $T$. Thứ tự chương trình cho $A<B$ (thread 1: load $y$ = $A$, store $x$ = $B$) và $C<D$ (thread 2: load $x$ = $C$, store $y=42$ = $D$). $r1=42$ nghĩa là $A$ đọc giá trị của $D$, nên $D<A$ trong $T$ (store 42 duy nhất vào $y$; giá trị ban đầu là 0). $r2=42$ nghĩa là $C$ đọc giá trị của $B$, nên $B<C$. Khi đó $D<A<B<C<D$, một chu trình, không thể. (b) Giờ $A$ là acquire load đọc giá trị do release store $D$ ghi, nên $D$ synchronizes-with $A$ và $D$ happens-before $A$. Tương tự $B$ (release) happens-before $C$. Với $A$ sequenced-before $B$ và $C$ sequenced-before $D$: $D\to A\to B\to C\to D$ trong happens-before, một chu trình, nhưng happens-before phải irreflexive (không có chu trình), nên kết quả bị cấm. (c) Với các thao tác relaxed không có cạnh synchronizes-with, nên chỉ thứ tự sửa đổi của từng biến áp dụng; mô hình cho phép $D$ trước $A$ trong thứ tự của `y` và $B$ trước $C$ trong thứ tự của `x` mà không mâu thuẫn (cppreference nêu rõ điều này). (d) Hàng đợi dùng mutex, mà các cặp unlock/lock tạo cạnh synchronizes-with cho mọi dữ liệu, nên mọi truy cập được sắp thứ tự toàn phần bởi khóa và lập luận chu trình relaxed không nảy sinh.
15. (a) Dung lượng 1, một cv, `notify_one` sau mỗi thay đổi. Bắt đầu: hàng đợi chứa $x$; producer $P_1,P_2$ bị chặn trong `push` (predicate `size<1` sai) trên `cv`. $C_1$ pop $x$ (hàng đợi rỗng) và gọi `notify_one`, chọn $P_1$. Trước khi $P_1$ lấy lại khóa, $C_2$ gọi `pop`, thấy hàng đợi rỗng và chờ trên `cv`: các waiter là $\{P_2,C_2\}$. $P_1$ thức, push $y$ (hàng đợi đầy) và gọi `notify_one`; cài đặt có thể chọn $P_2$ (các waiter không phân biệt được). $P_2$ thức, thấy hàng đợi đầy, và chờ lại. Giờ $C_2$ chờ dù hàng đợi chứa $y$, $P_2$ chờ, $P_1$ và $C_1$ không còn việc: không ai gọi `notify`, cả bốn thread bị chặn hoặc nhàn rỗi mãi mãi. (b) Cách 1: `notify_all` trên một cv; đúng nhưng đánh thức mọi waiter (thundering herd, $O(\text{waiters})$ lần chuyển ngữ cảnh mỗi thao tác). Cách 2: hai condition variable, `not_full` và `not_empty`, với `notify_one` trên cái mà trạng thái thay đổi thỏa; mỗi thông báo đều hữu ích và chỉ đúng loại waiter được đánh thức (đây là thiết kế của hàng đợi trong bài). (c) Dạng `if (q.empty()) cv.wait(lk);` chờ mà không kiểm tra lại điều kiện trong vòng lặp, điều CP.42 khuyên tránh (dùng overload có predicate): với spurious wake-up hoặc một consumer cạnh tranh, code pop từ hàng đợi rỗng.

## Đọc thêm

- [cppreference: Concurrency support library](https://en.cppreference.com/w/cpp/thread) - thread, mutex, condition variable, future và atomic, kèm ví dụ.
- [C++ Core Guidelines: CP](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - các quy tắc để tránh race và deadlock (CP.2, CP.20, CP.21, CP.42).
- [cppreference: std::memory_order](https://en.cppreference.com/w/cpp/atomic/memory_order) - ý nghĩa chính xác của relaxed, acquire, release và seq_cst.

**Thực hành thêm:** [ThreadSanitizer manual](https://clang.llvm.org/docs/ThreadSanitizer.html) (tái hiện từng báo cáo được liệt kê trên một chương trình đồ chơi), các [quy tắc concurrency và parallelism](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#cp-concurrency-and-parallelism) của Core Guidelines (CP.20 đến CP.42 ứng với bài tập 3 đến 7), và các ví dụ chạy được trên cppreference cho [`std::condition_variable`](https://en.cppreference.com/w/cpp/thread/condition_variable), [`std::shared_mutex`](https://en.cppreference.com/w/cpp/thread/shared_mutex) và [`std::async`](https://en.cppreference.com/w/cpp/thread/async), mà bạn có thể mở rộng và chạy dưới TSan.
