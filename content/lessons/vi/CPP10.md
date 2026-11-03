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

## Lý thuyết và suy dẫn

### Data race và memory model

Hai truy cập bộ nhớ *xung đột (conflict)* nếu chúng chạm cùng một vị trí và ít nhất một là ghi. **Data race** xảy ra khi hai truy cập xung đột ở các thread khác nhau không được sắp thứ tự bởi quan hệ happens-before (tạo bởi mutex, atomic với thứ tự phù hợp, thread start và join). Một chương trình có data race là undefined behavior, ngay cả khi mỗi biến "chỉ là một int": compiler có thể giả định không có race và sắp xếp lại thứ tự, cache giá trị trong thanh ghi, hoặc tách các truy cập.

Không phải data race: đọc đồng thời dữ liệu không ai ghi; ghi vào các đối tượng khác nhau (các phần tử khác nhau của vector; dù các phần tử lân cận dùng chung một cache line, đó là vấn đề hiệu năng gọi là false sharing); các truy cập được bảo vệ bởi cùng một mutex; các thao tác trên `std::atomic`.

Mất cập nhật, từng bước: counter $=0$. Thread A nạp 0; thread B nạp 0; A lưu 1; B lưu 1. Hai lần tăng, giá trị cuối là 1. Trong một thí nghiệm với hai thread mỗi thread làm $10^6$ phép tăng thường, tổng quan sát được là 1,988,346 thay vì 2,000,000, mất $11{,}654$ cập nhật ($0.58\%$) trong một lần chạy. Một counter được mutex bảo vệ hoặc atomic luôn cho 2,000,000.

### Thread, mutex và RAII

```cpp
std::thread t(work, arg);   // starts immediately
t.join();                    // wait for it to finish
```
Một `std::thread` bị hủy khi vẫn còn joinable sẽ gọi `std::terminate` ("terminate called without an active exception"). Luôn `join()` (hoặc `detach()` có chủ ý, hiếm khi); với C++20 hãy ưu tiên `std::jthread`, tự join trong destructor.

Bảo vệ trạng thái dùng chung bằng mutex và khóa nó bằng RAII (CP.20): `std::lock_guard<std::mutex> lk(m);` hoặc `std::unique_lock` khi bạn cần mở khóa sớm hoặc chờ. Đừng bao giờ gọi `m.lock()`/`m.unlock()` bằng tay: một exception hay `return` sớm sẽ để nó bị khóa. Giữ các vùng găng ngắn và đừng gọi code không rõ (callback, I/O) khi đang giữ lock.

**Deadlock** cần một chu trình: thread 1 giữ $A$ và chờ $B$, thread 2 giữ $B$ và chờ $A$. Tránh nó bằng thứ tự khóa hoặc bằng cách lấy nhiều mutex cùng lúc với `std::scoped_lock lk(a.m, b.m);` (CP.21), dùng một thuật toán tránh deadlock.

### Condition variable

```cpp
std::unique_lock<std::mutex> lk(m);
cv.wait(lk, [&]{ return !q.empty() || closed; });   // predicate form
```
`wait` nhả lock một cách nguyên tử và ngủ; khi thức dậy nó lấy lại lock. Predicate được kiểm tra *khi đang giữ lock*, trong một vòng lặp (overload có predicate làm việc này cho bạn), vì có **spurious wake-up** (thức dậy giả) và vì consumer khác có thể đã lấy mất phần tử trước. Gọi notify sau khi đổi trạng thái, hoặc khi đang giữ lock hoặc ngay sau khi nhả nó. Mất wake-up xảy ra khi một thread kiểm tra điều kiện mà không có lock, và trạng thái thay đổi giữa lúc kiểm tra và lúc ngủ.

### Hàng đợi có giới hạn và hợp đồng của nó

Một hàng đợi có giới hạn dung lượng $K$ tách tốc độ của producer và consumer: nếu producer nhanh hơn, nó bị chặn (back-pressure) thay vì tiêu thụ bộ nhớ không giới hạn. Trạng thái gồm `deque<T> q`, `bool closed` và một mutex. Hai điều kiện: `not_full` (producer chờ `size < K`) và `not_empty` (consumer chờ có phần tử). Hợp đồng:

1. Mọi trạng thái được bảo vệ bởi một mutex.
2. `push` chặn khi đầy; `pop` chặn khi rỗng và còn mở.
3. `close()` đánh dấu kết thúc luồng và đánh thức mọi người; sau đó `push` thất bại và `pop` rút nốt các phần tử còn lại rồi trả `nullopt`.
4. Thứ tự FIFO; không phần tử nào bị mất hay giao hai lần.
5. Không giữ lock khi chạy code người dùng, nên không thể có chu trình thứ tự khóa.

*Ví dụ về kích thước.* Một cảm biến phát một đợt 50 phần tử trong 50 ms (1000 phần tử/s); consumer xử lý 200 phần tử/s. Trong đợt phát, consumer lấy đi $200\times0.05=10$ phần tử, nên tồn đọng là $50-10=40$ phần tử và được xả hết trong $40/200=0.2$ s. Dung lượng $\ge40$ tránh chặn producer; với dung lượng 8, producer bị làm chậm bằng nhịp của consumer.

### Atomic và memory ordering

`std::atomic<T>` làm cho các thao tác đơn không chia cắt được và không có race. Với `memory_order_seq_cst` (mặc định) mọi thao tác atomic xuất hiện theo một thứ tự toàn cục duy nhất. Thứ tự **release/acquire** cho một đảm bảo công bố: mọi thứ được ghi trước một release store đều nhìn thấy được sau một acquire load đọc giá trị đã lưu.

```cpp
int data; std::atomic<bool> ready{false};
// producer:  data = 42;  ready.store(true, std::memory_order_release);
// consumer:  while (!ready.load(std::memory_order_acquire)) {}  /* data == 42 here */
```
Với `memory_order_relaxed` cho cả hai, việc ghi `data` không được sắp thứ tự với cờ, và việc đọc `data` sẽ là một data race. Dùng atomic cho cờ và counter; dùng mutex cho bất cứ thứ gì có bất biến xuyên nhiều biến.

## Ví dụ có lời giải

Lần theo một lần chạy producer-consumer với dung lượng $K=2$, một producer $P$ push $1,2,3$ và một consumer $C$.

1. $P$ khóa, `size=0<2`, push 1, `notify_one(not_empty)`, mở khóa. Hàng đợi: $[1]$.
2. $P$ push 2. Hàng đợi: $[1,2]$, đầy.
3. $P$ thử `push(3)`: khóa, predicate `closed || size<2` sai, nên `wait` nhả lock và chặn trên `not_full`.
4. $C$ gọi `pop`: khóa, hàng đợi không rỗng, lấy 1, hàng đợi $[2]$, `notify_one(not_full)`, mở khóa, trả 1.
5. $P$ thức dậy (nó lấy lại lock bên trong `wait`), predicate `size<2` đúng, push 3, hàng đợi $[2,3]$.
6. $C$ pop 2, rồi 3: hàng đợi rỗng. Lần `pop` thứ tư thấy hàng đợi rỗng và còn mở, nên chặn trên `not_empty`.
7. $P$ gọi `close()`: đặt `closed`, `notify_all` trên cả hai điều kiện. $C$ thức dậy, predicate `closed || !empty` đúng, hàng đợi rỗng, nên `pop` trả `nullopt`, và vòng lặp consumer `while (auto v = q.pop())` kết thúc.

Mỗi phần tử được giao một lần, theo thứ tự, 1, 2, 3. Nếu không có bước 7, $C$ sẽ chặn mãi mãi (treo): đó là lý do `close()` tồn tại. Các phép kiểm tra: tổng số đã giao $=3$, tổng $=6$; cùng chương trình với `int` thường và không lock cho bộ đếm cho thấy mất cập nhật dưới tải.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: C++ Core Guidelines, CP.2 and CP.3)* Trường hợp nào trong số này là data race? (a) hai thread đọc cùng một `const int`; (b) một thread ghi một `int`, thread khác đọc nó, không đồng bộ; (c) hai thread làm `fetch_add` trên một `std::atomic<int>`; (d) thread 1 ghi `v[0]`, thread 2 ghi `v[1]` của một `std::vector<int>` đã định kích thước trước. Trường hợp nào vẫn có thể chậm, và vì sao?
2. **(Dễ)** Hai thread mỗi thread thực hiện `++counter` $10^6$ lần trên một `int` thường; một lần chạy in ra 1,988,346. Mất bao nhiêu cập nhật và đó là bao nhiêu phần trăm? Viết một đan xen của chuỗi nạp/cộng/lưu làm mất một cập nhật, và nêu hai cách sửa.
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
8. **(Khó)** *(Adapted from: cppreference, std::condition_variable example)* Một cảm biến phát đợt 50 phần tử trong 50 ms; consumer xử lý 200 phần tử/s. Tính lượng tồn đọng ở cuối đợt, thời gian xả, và dung lượng tối thiểu để producer không bao giờ bị chặn. Độ trễ của phần tử cuối đợt là bao nhiêu?
9. **(Khó)** *(Adapted from: cppreference, std::memory_order)* Giải thích vì sao mẫu cờ release/acquire trong phần lý thuyết là đúng và điều gì sai với `memory_order_relaxed` cho cả hai thao tác. Khi nào bạn dùng mutex thay vào đó?
10. **(Khó)** Thiết kế. Một control thread phải luôn dùng lần đọc cảm biến mới nhất, bỏ qua các lần cũ hơn; một logger phải thấy mọi lần đọc. Đặc tả (i) một mailbox `Latest<T>`, (ii) hàng đợi cho logger, cùng hợp đồng khóa của chúng, và chuyện gì xảy ra khi logger chậm hơn cảm biến. Cái nào có giới hạn, và "drop" nghĩa là gì với mỗi cái?
11. **(Mini-project)** Đo thông lượng (phần tử mỗi giây) của hàng đợi của bạn với 1 producer và 1 consumer cho dung lượng 1, 8 và 1024 và $10^6$ phần tử; giải thích xu hướng; thêm `pop_for(std::chrono::milliseconds)` dùng `wait_for`; chạy tất cả dưới ThreadSanitizer.

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
2. Mất: $2{,}000{,}000-1{,}988{,}346=11{,}654$, tức $0.58\%$. Đan xen: A nạp 5; B nạp 5; A cộng và lưu 6; B cộng và lưu 6; hai lần tăng, cuối cùng 6. Cách sửa: `std::atomic<int>` với `fetch_add`, hoặc một `std::mutex` với `lock_guard` quanh phép tăng, hoặc một counter riêng cho mỗi thread được cộng lại ở cuối (không chia sẻ).
3. `{ std::lock_guard<std::mutex> lk(m); if (queue.empty()) return false; x = queue.front(); queue.pop(); return true; }`: lock được nhả khi `lk` ra khỏi scope ở cả hai lệnh return (và khi có exception do `front`/`pop` hay phép copy ném ra).
4. Bug 1: `if` thay vì vòng lặp hoặc predicate: sau một spurious wake-up, hoặc nếu consumer khác đã lấy phần tử, `q.front()` bị gọi trên hàng đợi rỗng. Bug 2 (thiết kế): không có cách dừng chờ khi tắt. Cách sửa: `cv.wait(lk, [&]{ return closed || !q.empty(); }); if (q.empty()) return std::nullopt;`.
5. Thread 1 khóa `a.m`, thread 2 khóa `b.m`; rồi thread 1 chờ `b.m` do thread 2 giữ, và thread 2 chờ `a.m`: một chu trình, nên cả hai chờ mãi mãi. Cách sửa: `std::scoped_lock lk(from.m, to.m);` (lấy cả hai mà không deadlock bất kể thứ tự đối số); hoặc áp đặt thứ tự toàn cục, chẳng hạn theo địa chỉ.
6. Đối tượng thread bị hủy khi còn joinable, nên `std::terminate` được gọi: output `terminate called without an active exception` và mã thoát 134. Cách sửa: `t.join();` trước khi return, hoặc dùng `std::jthread` (C++20), hoặc một wrapper RAII nhỏ join trong destructor.
7. `size()` về mặt logic là `const` (không đổi hàng đợi) nhưng phải khóa mutex, thứ làm đổi trạng thái nội bộ của mutex; khai báo mutex là `mutable` cho phép điều đó. `if (q.size() < cap) q.push(x);` là một race check-then-act: một thread khác có thể làm đầy hàng đợi giữa hai lời gọi, nên `push` có thể chặn (hoặc vượt chính sách dự định). Dùng `try_push(x)`, thực hiện cả phép kiểm tra và phép chèn trong một vùng găng.
8. Đợt phát: consumer lấy đi $200\times0.05=10$ phần tử trong 50 ms, nên tồn đọng là $50-10=40$ phần tử. Thời gian xả $40/200=0.2$ s. Dung lượng tối thiểu để không chặn: 40 (cộng một phần tử đang được xử lý). Phần tử cuối của đợt phải chờ 40 phần tử phía trước được xử lý: độ trễ khoảng $40/200=0.2$ s cộng thời gian xử lý của chính nó $5$ ms.
9. Release store xảy ra sau `data = 42`; acquire load đọc `true` đồng bộ hóa với nó, tạo một cạnh happens-before từ việc ghi `data` tới việc đọc, nên đọc `data` không có race và thấy 42. Với các thao tác relaxed không có thứ tự giữa cờ và `data`: compiler hoặc CPU có thể sắp xếp lại, và việc đọc `data` là một data race (undefined behavior). Dùng mutex khi hơn một biến phải nhất quán hoặc logic phức tạp hơn một cờ.
10. `Latest<T>`: hợp đồng: một mutex bảo vệ một `T` và một bộ đếm phiên bản; `set` ghi đè, không bao giờ chặn quá lock ngắn; `get` trả về một bản copy và phiên bản; "drop" = giá trị cũ bị bỏ khi bị thay thế. Hàng đợi của logger: có giới hạn, FIFO, `push` chặn (back-pressure lên thread cảm biến, thường không chấp nhận được) hoặc `try_push` bỏ phần tử mới nhất và tăng bộ đếm drop. Nếu logger chậm hơn, mailbox che giấu điều đó (bộ điều khiển không bị ảnh hưởng); hàng đợi logger hoặc chặn producer hoặc drop; các hệ thống thật chọn drop-kèm-bộ-đếm cho cảm biến và dung lượng lớn hơn cùng một thread logging riêng.
11. Một câu trả lời tốt gồm: dung lượng 1 buộc một lần chuyển ngữ cảnh cho mỗi phần tử, nên thông lượng thấp nhất (hàng trăm nghìn đến khoảng một triệu phần tử/s tùy máy); dung lượng 8 và 1024 cho phép gom lô và thông lượng tăng rồi phẳng ra; `pop_for` trả về `std::optional<T>` và dùng `not_empty_.wait_for(lk, timeout, predicate)` trả false khi hết thời gian; TSan không báo cảnh báo nào.

## Đọc thêm

- [cppreference: Concurrency support library](https://en.cppreference.com/w/cpp/thread) - thread, mutex, condition variable, future và atomic, kèm ví dụ.
- [C++ Core Guidelines: CP](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - các quy tắc để tránh race và deadlock (CP.2, CP.20, CP.21, CP.42).
- [cppreference: std::memory_order](https://en.cppreference.com/w/cpp/atomic/memory_order) - ý nghĩa chính xác của relaxed, acquire, release và seq_cst.

**Thực hành thêm:** [ThreadSanitizer manual](https://clang.llvm.org/docs/ThreadSanitizer.html) (tái hiện từng báo cáo được liệt kê trên một chương trình đồ chơi), các [quy tắc concurrency và parallelism](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#cp-concurrency-and-parallelism) của Core Guidelines (CP.20 đến CP.42 ứng với bài tập 3 đến 7), và các ví dụ chạy được trên cppreference cho [`std::condition_variable`](https://en.cppreference.com/w/cpp/thread/condition_variable), [`std::shared_mutex`](https://en.cppreference.com/w/cpp/thread/shared_mutex) và [`std::async`](https://en.cppreference.com/w/cpp/thread/async), mà bạn có thể mở rộng và chạy dưới TSan.
