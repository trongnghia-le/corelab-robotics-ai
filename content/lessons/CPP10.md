---
{
  "id": "cpp10-foundations",
  "module_id": "CPP10",
  "title": "Concurrency: threads, synchronization, and data races",
  "summary": "Share data between threads without data races, build a blocking producer-consumer queue, and state its locking contract.",
  "estimated_minutes": 405,
  "prerequisites": [
    "CPP03",
    "CPP08"
  ],
  "source_refs": [
    {
      "title": "cppreference: Concurrency support library",
      "url": "https://en.cppreference.com/w/cpp/thread"
    },
    {
      "title": "C++ Core Guidelines: CP. Concurrency and parallelism",
      "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"
    },
    {
      "title": "cppreference: std::memory_order",
      "url": "https://en.cppreference.com/w/cpp/atomic/memory_order"
    }
  ],
  "objectives": [
    "Define a data race, recognize one, and explain why it is undefined behavior.",
    "Protect shared state with mutexes using RAII, and avoid lock-order deadlock.",
    "Use condition variables correctly (always with a predicate) to block and wake threads.",
    "Write and test a bounded producer-consumer queue and document its locking contract."
  ],
  "core_theory": [
    "threads",
    "synchronization",
    "data races"
  ],
  "labs": [
    "Implement a blocking bounded queue with close semantics, test it with blocked producers and consumers and a multi-thread stress test, and run it under ThreadSanitizer."
  ],
  "assessment_refs": [
    "CPP10-diagnostic-v1"
  ],
  "review_prompts": [
    "A control thread needs only the latest sensor reading, while a logging thread needs every reading. Choose a data structure and locking contract for each and explain why one queue design does not fit both."
  ],
  "extension_refs": [
    "https://en.cppreference.com/w/cpp/thread",
    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"
  ]
}
---

## Why this matters

A robot is concurrent by nature: a camera driver delivers frames at 30 Hz, an IMU at 400 Hz, a controller runs at 1 kHz and a planner takes whatever time it needs. Using threads lets these activities overlap, but threads share memory, and unsynchronized sharing is not merely "occasionally wrong": reading and writing the same variable from two threads without synchronization is a **data race**, which is undefined behavior in C++. The symptoms are the worst kind: lost updates, torn values, hangs that appear once a week, and bugs that vanish when you add a `printf`. This lesson gives you the vocabulary (thread, mutex, condition variable, atomic), the invariants to preserve (no race, no deadlock, no lost wake-up), and a complete example, the bounded blocking queue, which is the glue between sensor callbacks and processing threads in nearly every robotics stack, including the executors and message queues of ROS 2.

## Intuition

A thread is an independent flow of execution inside one process; all threads see the same memory. Imagine two people editing the same paper form. If they take turns (mutual exclusion), the form stays consistent. If both write at once, the result may be a mixture of both. The lock is the pen that only one person may hold.

Even a single line such as `++counter` is three steps (load, add, store). Two threads can both load 5, both add 1, and both store 6: one increment is lost. A mutex makes the three steps one indivisible *critical section*; an atomic makes the single operation indivisible in hardware.

Waiting is a different problem from locking. A consumer that finds the queue empty should not spin burning a core, nor hold the lock while sleeping. A **condition variable** lets it release the lock and sleep until another thread signals that the state may have changed, then re-acquire the lock and re-check.

![Producer, bounded queue protected by one mutex with two condition variables, and consumer; a timeline showing a lost update from two unsynchronized increments](/lesson-figures/CPP10.svg)

*Left: producer, queue and consumer synchronized by one mutex and two condition variables. Right: two interleaved increments lose an update.*

## Theory and derivation

### Data races and the memory model

Two memory accesses *conflict* if they touch the same location and at least one is a write. A **data race** occurs when two conflicting accesses in different threads are not ordered by a happens-before relation (created by mutexes, atomics with suitable ordering, thread start and join). A program with a data race has undefined behavior, even if each variable is "just an int": the compiler may assume no race and reorder, cache values in registers, or split accesses.

Not data races: concurrent reads of data nobody writes; writes to different objects (distinct vector elements; though neighbouring elements share a cache line, which is a performance issue called false sharing); accesses protected by the same mutex; operations on `std::atomic`.

Lost update, step by step: counter $=0$. Thread A loads 0; thread B loads 0; A stores 1; B stores 1. Two increments, final value 1. In an experiment with two threads each doing $10^6$ plain increments, the observed total was 1,988,346 instead of 2,000,000, losing $11{,}654$ updates ($0.58\%$) in one run. A mutex-protected or atomic counter always gives 2,000,000.

### Threads, mutexes and RAII

```cpp
std::thread t(work, arg);   // starts immediately
t.join();                    // wait for it to finish
```
A `std::thread` that is destroyed while still joinable calls `std::terminate` ("terminate called without an active exception"). Always `join()` (or `detach()` deliberately, rarely); with C++20 prefer `std::jthread`, which joins in its destructor.

Protect shared state with a mutex and lock it with RAII (CP.20): `std::lock_guard<std::mutex> lk(m);` or `std::unique_lock` when you need to unlock early or wait. Never call `m.lock()`/`m.unlock()` by hand: an exception or early `return` would leave it locked. Keep critical sections short and do not call unknown code (callbacks, I/O) while holding a lock.

**Deadlock** needs a cycle: thread 1 holds $A$ and waits for $B$, thread 2 holds $B$ and waits for $A$. Avoid it by lock ordering or by acquiring several mutexes at once with `std::scoped_lock lk(a.m, b.m);` (CP.21), which uses a deadlock-avoidance algorithm.

### Condition variables

```cpp
std::unique_lock<std::mutex> lk(m);
cv.wait(lk, [&]{ return !q.empty() || closed; });   // predicate form
```
`wait` atomically releases the lock and sleeps; on wake-up it re-acquires the lock. The predicate is checked *with the lock held*, in a loop (the overload with a predicate does this for you), because of **spurious wake-ups** and because another consumer may have taken the item first. Notify after changing the state, either with the lock held or just after releasing it. A lost wake-up happens when a thread checks a condition without the lock, and the state changes between the check and the sleep.

### The bounded queue and its contract

A bounded queue with capacity $K$ separates producer and consumer rates: if the producer is faster, it blocks (back-pressure) instead of consuming unbounded memory. The state is `deque<T> q`, `bool closed` and one mutex. Two conditions: `not_full` (producers wait for `size < K`) and `not_empty` (consumers wait for items). The contract:

1. All state is protected by one mutex.
2. `push` blocks while full; `pop` blocks while empty and open.
3. `close()` marks the end of the stream and wakes everybody; after it `push` fails and `pop` drains the remaining items and then returns `nullopt`.
4. FIFO order; no item is lost or delivered twice.
5. No lock is held while running user code, so no lock-order cycle is possible.

*Sizing example.* A sensor bursts 50 items in 50 ms (1000 items/s); the consumer handles 200 items/s. During the burst the consumer removes $200\times0.05=10$ items, so the backlog is $50-10=40$ items and drains in $40/200=0.2$ s. Capacity $\ge40$ avoids blocking the producer; with capacity 8 the producer is slowed to the consumer's pace.

### Atomics and memory ordering

`std::atomic<T>` makes single operations indivisible and race-free. With `memory_order_seq_cst` (the default) all atomic operations appear in one global order. **Release/acquire** ordering gives a publication guarantee: everything written before a release store is visible after an acquire load that reads the stored value.

```cpp
int data; std::atomic<bool> ready{false};
// producer:  data = 42;  ready.store(true, std::memory_order_release);
// consumer:  while (!ready.load(std::memory_order_acquire)) {}  /* data == 42 here */
```
With `memory_order_relaxed` for both, the write to `data` is not ordered with the flag, and the read of `data` would be a data race. Use atomics for flags and counters; use mutexes for anything with an invariant across several variables.

## Worked example

Trace a producer-consumer run with capacity $K=2$, one producer $P$ pushing $1,2,3$ and one consumer $C$.

1. $P$ locks, `size=0<2`, pushes 1, `notify_one(not_empty)`, unlocks. Queue: $[1]$.
2. $P$ pushes 2. Queue: $[1,2]$, full.
3. $P$ tries `push(3)`: locks, the predicate `closed || size<2` is false, so `wait` releases the lock and blocks on `not_full`.
4. $C$ calls `pop`: locks, the queue is non-empty, takes 1, queue $[2]$, `notify_one(not_full)`, unlocks, returns 1.
5. $P$ wakes (it re-acquires the lock inside `wait`), the predicate `size<2` is true, pushes 3, queue $[2,3]$.
6. $C$ pops 2, then 3: queue empty. A fourth `pop` finds the queue empty and open, so it blocks on `not_empty`.
7. $P$ calls `close()`: sets `closed`, `notify_all` on both conditions. $C$ wakes, the predicate `closed || !empty` holds, the queue is empty, so `pop` returns `nullopt`, and the consumer loop `while (auto v = q.pop())` ends.

Every item was delivered once, in order, 1, 2, 3. Without step 7, $C$ would block forever (a hang): this is why `close()` exists. The checks: total delivered $=3$, sum $=6$; the same program with plain `int` and no lock for the count shows lost updates under load.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: C++ Core Guidelines, CP.2 and CP.3)* Which of these are data races? (a) two threads read the same `const int`; (b) one thread writes an `int`, another reads it, no synchronization; (c) two threads do `fetch_add` on one `std::atomic<int>`; (d) thread 1 writes `v[0]`, thread 2 writes `v[1]` of a pre-sized `std::vector<int>`. Which one may still be slow, and why?
2. **(Easy)** Two threads each execute `++counter` $10^6$ times on a plain `int`; one run printed 1,988,346. How many updates were lost and what percentage is that? Write an interleaving of a load/add/store sequence that loses one update, and name two fixes.
3. **(Easy)** Rewrite using RAII so the mutex is released on every path:
   ```cpp
   m.lock();
   if (queue.empty()) return false;
   x = queue.front(); queue.pop();
   m.unlock();
   return true;
   ```
4. **(Medium)** *(Adapted from: C++ Core Guidelines, CP.42)* Find the bugs in this consumer and fix it.
   ```cpp
   std::unique_lock<std::mutex> lk(m);
   if (q.empty()) cv.wait(lk);
   auto v = q.front();
   q.pop();
   ```
5. **(Medium)** *(Adapted from: C++ Core Guidelines, CP.21)* `transfer(a, b)` locks `a.m` then `b.m`; another thread calls `transfer(b, a)`. Explain the deadlock, show the interleaving, and fix it with `std::scoped_lock`.
6. **(Medium)** What does this program do and why? Give two fixes.
   ```cpp
   int main() { std::thread t([] { std::cout << "work\n"; }); }
   ```
7. **(Medium)** `BoundedQueue::size()` is `const` but locks a mutex; why must the mutex be `mutable`? A caller writes `if (q.size() < cap) q.push(x);`. Explain the check-then-act race and the correct call.
8. **(Hard)** *(Adapted from: cppreference, std::condition_variable example)* A sensor bursts 50 items in 50 ms; the consumer processes 200 items/s. Compute the backlog at the end of the burst, the time to drain it, and the minimum capacity so the producer never blocks. What is the latency of the last item of the burst?
9. **(Hard)** *(Adapted from: cppreference, std::memory_order)* Explain why the release/acquire flag pattern in the theory section is correct and what goes wrong with `memory_order_relaxed` on both operations. When would you use a mutex instead?
10. **(Hard)** Design. A control thread must always use the most recent sensor reading, ignoring older ones; a logger must see every reading. Specify (i) a `Latest<T>` mailbox, (ii) the queue for the logger, with their locking contracts, and what happens when the logger is slower than the sensor. Which is bounded, and what does "drop" mean for each?
11. **(Mini-project)** Measure throughput (items per second) of your queue with 1 producer and 1 consumer for capacities 1, 8 and 1024 and $10^6$ items; explain the trend; add `pop_for(std::chrono::milliseconds)` using `wait_for`; run everything under ThreadSanitizer.

## Reference implementation

First the three-counter experiment (race, atomic, mutex), then the bounded queue.

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

Typical output on the lesson machine: `plain=1988346 atomic=2000000 locked=2000000` (the plain value differs at every run). Under ThreadSanitizer (`g++ -std=c++17 -g -O1 -pthread -fsanitize=thread race.cpp`; on some kernels run as `setarch $(uname -m) -R ./a.out` if you see "unexpected memory mapping") TSan reports `WARNING: ThreadSanitizer: data race` pointing at the `++plain` line, with the two conflicting threads.

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

## Independent practice

### Goal

Implement a blocking bounded queue with close semantics and show, with tests that block and wake threads, that it is correct and race-free.

### Setup

`g++` or `clang++` with C++17 and `-pthread`. Save the starter and the tests as `lab.cpp`. Build the tests with `g++ -std=c++17 -Wall -Wextra -g -pthread -fsanitize=address,undefined lab.cpp -o lab && ./lab`, and separately with `-fsanitize=thread` (not combinable with ASan).

### Tasks

1. Add the members and implement the constructor, `size` and `try_push`; run the single-thread part of the tests mentally first.
2. Implement `push` and `pop` with `wait` and a predicate; make sure each call notifies the right condition variable.
3. Implement `close()`; check the tests that release blocked threads (they fail after a 3-second timeout if you forget `notify_all`).
4. Run the stress test 20 times in a loop (`for i in $(seq 20); do ./lab; done`).
5. Build with ThreadSanitizer and confirm there is no warning.
6. Introduce one bug on purpose (for example read `closed_` without the lock in `size()` or use `if` instead of the predicate) and observe what TSan or the stress test reports; then restore.

### Starter code

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

### Tests

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

### Expected output

```
all tests passed
```

With the stubs the first test aborts with `NotImplemented`. A missing `notify_all` in `close()` shows up as `FAIL ... ready` after the timeout; with ThreadSanitizer a missing lock shows up as `data race`.

### Extension challenge

Add `pop_for(timeout)` and `push_for(timeout)`, then build a latest-value mailbox `Latest<T>` with `set`, `get` and a version counter so a consumer can tell whether a value is new.

### Library track

Standard-library building blocks beyond `mutex` and `condition_variable`: `std::async`/`std::future` (a thread that *returns* its result, so no shared accumulator is needed) and `std::shared_mutex` (many readers, one writer) for the `Latest<T>` mailbox of exercise 10. Paste this after your finished `BoundedQueue` (it has its own `main`, so drop the one from the tests) and build with `g++ -std=c++17 -Wall -Wextra -g -O1 -pthread`, then again with `-fsanitize=thread` (run as `setarch $(uname -m) -R ./a.out` if TSan complains about the memory mapping).

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

Expected output: `library track ok`, with no ThreadSanitizer warning. Questions: why does the future-returning consumer need no mutex around `s`? What would TSan say if `Latest::set` skipped its `unique_lock`?

## Verification

- Run under ThreadSanitizer: a clean run is strong evidence of no data race on the paths executed.
- Stress with more threads than cores and tiny capacities (1, 2): they maximize interleavings and blocking.
- Check the invariants at the end: items in = items out, sum matches, per-producer order is preserved, `size()==0`.
- Test the blocking behavior explicitly: a thread must be seen to be blocked (`wait_for(10ms) == timeout`), then released by the action under test, using a timeout to turn a hang into a failure.
- Repeat runs hundreds of times (`ctest --repeat until-fail:200`); a rare failure is still a failure.
- Review the contract: for every shared variable, write which mutex or atomic protects it.

## Failure modes

| Mistake | Symptom |
|---|---|
| Unsynchronized counter or flag | lost updates (here 11,654 of 2,000,000), stale reads, TSan `data race` |
| `if (q.empty()) cv.wait(lk);` | wrong with spurious wake-up or multiple consumers: pops from an empty queue |
| Notify without changing the state under the lock | lost wake-up, thread sleeps forever |
| Forgetting `notify_all` in `close()` | consumers or producers hang at shutdown |
| Locking two mutexes in different orders | deadlock, program freezes |
| `std::thread` destroyed without `join` | `terminate called without an active exception` |
| Holding a lock while calling a callback or doing I/O | latency spikes, deadlock when the callback locks again |
| Check-then-act (`if (size() < cap) push`) | race between the check and the act; use one atomic operation (`try_push`) |
| `volatile` used as synchronization | not a synchronization mechanism in C++; use `std::atomic` |
| Detached thread uses a reference to a local | use after the local is destroyed |

## Alternatives and trade-offs

- **Mutex vs atomic.** Atomics are best for one flag or counter; a mutex is simpler and safer when several variables must change together.
- **Blocking queue vs lock-free queue.** Lock-free ring buffers (single-producer single-consumer) have lower latency and no priority inversion, but are subtle to write and test; start with the mutex version and measure.
- **Queue vs latest-value mailbox.** Use a queue when every item matters (logging, commands); use a mailbox (overwrite) when only the freshest value matters (control inputs).
- **Bounded vs unbounded.** Unbounded queues hide overload as memory growth and latency; bounded queues make overload visible as back-pressure or drops.
- **Threads vs async tasks (`std::async`, thread pools) vs executors.** Pools reduce thread-creation cost; ROS 2 executors schedule callbacks on a fixed set of threads, with callback groups to control mutual exclusion.
- **Shared-memory threads vs processes.** Processes isolate faults and avoid races on memory, at the cost of copying or shared-memory IPC; ROS 2 nodes in separate processes use messages.
- **Real-time concerns.** Mutexes can cause priority inversion; real-time control loops use priority-inheritance mutexes, lock-free structures, or avoid sharing.

## Transfer and retention

Python has the same concepts under different names (`threading.Lock`, `queue.Queue` with `put/get`, `Condition`), plus the global interpreter lock that limits parallel CPU use but not races on compound operations. In ROS 2, callbacks run on executor threads and shared member variables need the same protection; `rclcpp` callback groups are mutual-exclusion groups. GPUs have their own memory-ordering rules. To retain: after a few days, write the `wait`-with-predicate pattern and the `scoped_lock` pattern from memory and explain why each exists; and state the three conditions for deadlock.

## Exercise answers

1. (a) no race (reads only). (b) race. (c) no race (atomic). (d) no race (distinct objects). (d) can still be slow because adjacent elements often share a 64-byte cache line (false sharing): the line bounces between cores.
2. Lost: $2{,}000{,}000-1{,}988{,}346=11{,}654$, which is $0.58\%$. Interleaving: A loads 5; B loads 5; A adds and stores 6; B adds and stores 6; two increments, final 6. Fixes: `std::atomic<int>` with `fetch_add`, or a `std::mutex` with `lock_guard` around the increment, or one counter per thread summed at the end (no sharing).
3. `{ std::lock_guard<std::mutex> lk(m); if (queue.empty()) return false; x = queue.front(); queue.pop(); return true; }`: the lock is released when `lk` goes out of scope on both returns (and on an exception thrown by `front`/`pop` or the copy).
4. Bug 1: `if` instead of a loop or predicate: after a spurious wake-up, or if another consumer took the item, `q.front()` is called on an empty queue. Bug 2 (design): there is no way to stop waiting at shutdown. Fix: `cv.wait(lk, [&]{ return closed || !q.empty(); }); if (q.empty()) return std::nullopt;`.
5. Thread 1 locks `a.m`, thread 2 locks `b.m`; then thread 1 waits for `b.m` held by thread 2, and thread 2 waits for `a.m`: a cycle, so both wait forever. Fix: `std::scoped_lock lk(from.m, to.m);` (acquires both without deadlock regardless of argument order); alternatively impose a global order, such as by address.
6. The thread object is destroyed while joinable, so `std::terminate` is called: output `terminate called without an active exception` and exit code 134. Fixes: `t.join();` before returning, or use `std::jthread` (C++20), or a small RAII wrapper that joins in its destructor.
7. `size()` is logically `const` (does not change the queue) but must lock the mutex, which changes the mutex's internal state; declaring the mutex `mutable` allows that. `if (q.size() < cap) q.push(x);` is a check-then-act race: another thread can fill the queue between the two calls, so `push` may block (or exceed an intended policy). Use `try_push(x)`, which does the test and the insertion in one critical section.
8. Burst: the consumer removes $200\times0.05=10$ items during the 50 ms, so the backlog is $50-10=40$ items. Drain time $40/200=0.2$ s. Minimum capacity without blocking: 40 (plus the one being processed). The last item of the burst waits for the 40 items ahead of it to be processed: latency about $40/200=0.2$ s plus its own processing time $5$ ms.
9. The release store happens after `data = 42`; the acquire load that reads `true` synchronizes with it, creating a happens-before edge from the write of `data` to the read, so reading `data` is race-free and sees 42. With relaxed operations there is no ordering between the flag and `data`: the compiler or CPU may reorder, and the read of `data` is a data race (undefined behavior). Use a mutex when more than one variable must be consistent or the logic is more complex than a flag.
10. `Latest<T>`: contract: one mutex protects one `T` and a version counter; `set` overwrites, never blocks beyond the short lock; `get` returns a copy and the version; "drop" = the old value is discarded when replaced. The logger queue: bounded, FIFO, `push` blocks (back-pressure on the sensor thread, usually unacceptable) or `try_push` drops the newest item and increments a drop counter. If the logger is slower, the mailbox hides it (the controller is unaffected); the logger queue either blocks the producer or drops; real systems choose drop-with-counter for sensors and bigger capacity plus a dedicated logging thread.
11. A good answer includes: capacity 1 forces a context switch per item, so throughput is lowest (hundreds of thousands to about a million items/s depending on the machine); capacities 8 and 1024 allow batching and the throughput increases then flattens; `pop_for` returns `std::optional<T>` and uses `not_empty_.wait_for(lk, timeout, predicate)` returning false on timeout; TSan reports no warnings.

## Further reading

- [cppreference: Concurrency support library](https://en.cppreference.com/w/cpp/thread) - threads, mutexes, condition variables, futures and atomics, with examples.
- [C++ Core Guidelines: CP](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - rules for avoiding races and deadlocks (CP.2, CP.20, CP.21, CP.42).
- [cppreference: std::memory_order](https://en.cppreference.com/w/cpp/atomic/memory_order) - the exact meaning of relaxed, acquire, release and seq_cst.

**More practice:** the [ThreadSanitizer manual](https://clang.llvm.org/docs/ThreadSanitizer.html) (reproduce each listed report on a toy program), the Core Guidelines [concurrency and parallelism rules](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#cp-concurrency-and-parallelism) (CP.20 to CP.42 map to exercises 3 to 7), and the runnable examples on cppreference for [`std::condition_variable`](https://en.cppreference.com/w/cpp/thread/condition_variable), [`std::shared_mutex`](https://en.cppreference.com/w/cpp/thread/shared_mutex) and [`std::async`](https://en.cppreference.com/w/cpp/thread/async), which you can extend and run under TSan.