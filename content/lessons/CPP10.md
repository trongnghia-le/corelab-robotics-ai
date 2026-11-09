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

**Predict before you compute.** Two threads each add 1 to the same shared integer one million times. Before running anything, write down the final value you expect, and whether it is the same on every run. Most people say 2,000,000. The measured answer in this lesson is "less, and different each time", with 11,654 updates lost in one run, and the C++ standard says the program has no defined meaning at all.

**A picture to hold on to.** Imagine two clerks updating one paper ledger line. Each reads the number, walks to a calculator, adds one and walks back to write the result. If both read 7 before either writes, both write 8 and one sale vanishes. A lock is a rule that only the clerk holding the pen may even look at the line; a condition variable is the waiting room where a clerk sleeps until someone rings a bell saying "there is now something to do". Deadlock is two clerks each holding one pen and refusing to put it down until they get the other's.

**The wrong intuitions.** "It printed the right answer when I tried, so it is correct": races depend on timing, and a debugger, a `printf` or a different CPU changes the timing. "Reading a shared `int` without a lock is harmless": a data race is undefined behavior even for a read, because the compiler is allowed to assume it cannot happen. "A bigger queue fixes overload": it only delays the moment the producer has to wait and increases latency. Hold the opposite rule: shared mutable data needs one named owner (a mutex), every wait needs a predicate, and a threaded program is judged by the interleavings that *can* happen, not by the ones you saw.

## Theory and derivation

### Data races and the memory model

Two memory accesses *conflict* if they touch the same location and at least one is a write. A **data race** occurs when two conflicting accesses in different threads are not ordered by a happens-before relation (created by mutexes, atomics with suitable ordering, thread start and join). A program with a data race has undefined behavior, even if each variable is "just an int": the compiler may assume no race and reorder, cache values in registers, or split accesses.

Not data races: concurrent reads of data nobody writes; writes to different objects (distinct vector elements; though neighbouring elements share a cache line, which is a performance issue called false sharing); accesses protected by the same mutex; operations on `std::atomic`.

Lost update, step by step: counter $=0$. Thread A loads 0; thread B loads 0; A stores 1; B stores 1. Two increments, final value 1. In an experiment with two threads each doing $10^6$ plain increments, the observed total was 1,988,346 instead of 2,000,000, losing $11{,}654$ updates ($0.58\%$) in one run. A mutex-protected or atomic counter always gives 2,000,000.

**Example.** Two threads each add 1 to a shared counter 400,000 times, first on a plain `int` and then on a `std::atomic<int>` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O0 -pthread`; `-O0` keeps the load, add and store visible as three steps):

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

The plain counter ends at 421,010, 481,171 and 481,774, never 800,000 and different on every run, while the atomic counter is always exactly 800,000. The loss here (40 to 47 %) is far larger than the 0.58 % quoted above for another build on another machine: its size depends on timing, which is the point, because the program has no defined result. Built with ThreadSanitizer (`-fsanitize=thread`, run as `setarch -R ./a.out` on this kernel), the same plain loop is reported (excerpt):

```text
WARNING: ThreadSanitizer: data race
  Read of size 4 by thread T2:
    #0 operator() e10_1.cpp:12
  Previous write of size 4 by thread T1:
    #0 operator() e10_1.cpp:11
SUMMARY: ThreadSanitizer: data race e10_1.cpp:12 in operator()
```

### Threads, mutexes and RAII

```cpp
std::thread t(work, arg);   // starts immediately
t.join();                    // wait for it to finish
```
A `std::thread` that is destroyed while still joinable calls `std::terminate` ("terminate called without an active exception"). Always `join()` (or `detach()` deliberately, rarely); with C++20 prefer `std::jthread`, which joins in its destructor.

Protect shared state with a mutex and lock it with RAII (CP.20): `std::lock_guard<std::mutex> lk(m);` or `std::unique_lock` when you need to unlock early or wait. Never call `m.lock()`/`m.unlock()` by hand: an exception or early `return` would leave it locked. Keep critical sections short and do not call unknown code (callbacks, I/O) while holding a lock.

**Deadlock** needs a cycle: thread 1 holds $A$ and waits for $B$, thread 2 holds $B$ and waits for $A$. Avoid it by lock ordering or by acquiring several mutexes at once with `std::scoped_lock lk(a.m, b.m);` (CP.21), which uses a deadlock-avoidance algorithm.

**Example.** A critical section throws an exception (a failed sensor read). After the exception is caught, a second thread tries to take the same mutex with `try_lock`; one version locks with `lock_guard`, the other with `m.lock()` and `m.unlock()` by hand (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`):

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

The guard's destructor runs while the exception unwinds the stack, so the mutex is free afterwards (`1`). The hand-written version never reaches `m.unlock()`, so the mutex stays locked for good (`0`): every other thread that asked for it would block forever. The final `m.unlock()` in `main` only cleans up the demonstration.

### Condition variables

```cpp
std::unique_lock<std::mutex> lk(m);
cv.wait(lk, [&]{ return !q.empty() || closed; });   // predicate form
```
`wait` atomically releases the lock and sleeps; on wake-up it re-acquires the lock. The predicate is checked *with the lock held*, in a loop (the overload with a predicate does this for you), because of **spurious wake-ups** and because another consumer may have taken the item first. Notify after changing the state, either with the lock held or just after releasing it. A lost wake-up happens when a thread checks a condition without the lock, and the state changes between the check and the sleep.

**Example.** A notifier sets `ready` and calls `notify_one` *before* the waiter starts to wait. The waiter first uses `wait_for` without a predicate and then the predicate overload, each with a 200 ms timeout so that a lost wake-up shows as a timeout instead of a hang (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`):

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

The state was already true, but the bare `wait_for` sleeps through the whole 200 ms because the one notification came earlier and is gone: a condition variable remembers nothing. The predicate overload tests `ready` under the lock before sleeping and returns at once (0 ms). The rule is to wait for a *state*, never for a signal.

### The bounded queue and its contract

A bounded queue with capacity $K$ separates producer and consumer rates: if the producer is faster, it blocks (back-pressure) instead of consuming unbounded memory. The state is `deque<T> q`, `bool closed` and one mutex. Two conditions: `not_full` (producers wait for `size < K`) and `not_empty` (consumers wait for items). The contract:

1. All state is protected by one mutex.
2. `push` blocks while full; `pop` blocks while empty and open.
3. `close()` marks the end of the stream and wakes everybody; after it `push` fails and `pop` drains the remaining items and then returns `nullopt`.
4. FIFO order; no item is lost or delivered twice.
5. No lock is held while running user code, so no lock-order cycle is possible.

*Sizing example.* A sensor bursts 50 items in 50 ms (1000 items/s); the consumer handles 200 items/s. During the burst the consumer removes $200\times0.05=10$ items, so the backlog is $50-10=40$ items and drains in $40/200=0.2$ s. Capacity $\ge40$ avoids blocking the producer; with capacity 8 the producer is slowed to the consumer's pace.

**Example.** The sizing rule of the contract is tested on a running queue. A burst of 60 items arrives, one every 0.5 ms (2000 items/s), and the consumer needs 2.5 ms per item (400 items/s). The burst lasts $60\times0.5=30$ ms, in which the consumer removes about $400\times0.030=12$ items, so the predicted backlog is $60-12=48$ items. The program runs capacities $K=64$ and $K=8$ and counts the pushes that had to wait (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`):

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

With $K=64$ the measured peak backlog is 47 (prediction 48; the first item is taken at once and the sleeps are not exact), no push blocks and the producer is done after 33.9 ms. With $K=8$ the queue is full after 8 items, 48 pushes wait and the producer is slowed to the consumer's pace: it finishes after 137.1 ms, close to $(60-8)\times2.5=130$ ms.

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

### Atomics and memory ordering

`std::atomic<T>` makes single operations indivisible and race-free. With `memory_order_seq_cst` (the default) all atomic operations appear in one global order. **Release/acquire** ordering gives a publication guarantee: everything written before a release store is visible after an acquire load that reads the stored value.

```cpp
int data; std::atomic<bool> ready{false};
// producer:  data = 42;  ready.store(true, std::memory_order_release);
// consumer:  while (!ready.load(std::memory_order_acquire)) {}  /* data == 42 here */
```
With `memory_order_relaxed` for both, the write to `data` is not ordered with the flag, and the read of `data` would be a data race. Use atomics for flags and counters; use mutexes for anything with an invariant across several variables.

**Example.** The publication pattern of this section is run 2000 times, each round with a fresh pair of threads: the producer writes `data = 42` and sets `ready` with release; the consumer spins with acquire and then reads `data` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`; the same source compiled with `-DRELAXED` uses relaxed ordering on both operations):

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

All 2000 rounds see 42, and ThreadSanitizer is silent on this version. On x86-64 the relaxed build also prints 2000 of 2000, because the hardware keeps stores in order, so a passing test proves nothing about the relaxed version; ThreadSanitizer (`-fsanitize=thread`, run as `setarch -R ./a.out` on this kernel) does report it (excerpt):

```text
WARNING: ThreadSanitizer: data race
  Read of size 4 by thread T2:
    #0 operator() e10_5.cpp:18
  Previous write of size 4 by thread T1:
    #0 operator() e10_5.cpp:17
SUMMARY: ThreadSanitizer: data race e10_5.cpp:18 in operator()
```

### Happens-before made precise

The data-race definition above rests on three relations from the C++ memory model (cppreference, *std::memory_order*, "Formal description"). *Sequenced-before* orders evaluations within one thread. A release operation on an atomic $M$ *synchronizes-with* an acquire operation on $M$ that reads the value it wrote (or a value from its release sequence). *Inter-thread happens-before* is the closure of synchronizes-with composed with sequenced-before; *happens-before* includes sequenced-before. A data race is then exactly two conflicting non-atomic accesses with neither happening before the other.

*Proof that the flag pattern is correct.* In the producer/consumer example, let $W$ be `data = 42`, $S$ the release store of `ready`, $L$ the acquire load that returns `true`, and $R$ the read of `data`. $W$ is sequenced-before $S$; $S$ synchronizes-with $L$ because $L$ read the value $S$ wrote; $L$ is sequenced-before $R$. Composing, $W$ happens-before $R$, so $R$ is not a race and it reads a visible side effect of $W$, i.e. 42. If the load used `relaxed`, no synchronizes-with edge exists, so $W$ and $R$ are unordered conflicting accesses: a data race and undefined behavior, not merely "a stale value".

*Relaxed atomics can even form cycles.* With `x` and `y` initially 0, thread 1 runs `r1 = y.load(relaxed); x.store(r1, relaxed)` and thread 2 runs `r2 = x.load(relaxed); y.store(42, relaxed)`. The outcome `r1 == r2 == 42` is allowed: nothing orders the store of 42 after the load in thread 2, and the model only forbids "out-of-thin-air" values that depend circularly on themselves (cppreference, *Relaxed ordering*). Exercise 14 asks you to prove which orderings forbid it.

![Two thread timelines showing the happens-before chain from the write of data to its read with release/acquire, and the missing edge with relaxed](/lesson-figures/CPP10-2.svg)

*Figure: the proof of this section drawn as a graph. The orange synchronizes-with edge exists only for release/acquire; remove it (relaxed) and $W$ and $R$ are unordered conflicting accesses, a data race.*

**Example.** Thread creation and `join` are synchronization points, so a value can be handed to a thread and back without any atomic. The thread reads `input` (written before it was created) and writes `output`; the parent reads `output` after `join` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`; with `-DEARLY` the parent reads before `join`):

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

Writing `input` happens-before the start of the thread, and the end of the thread happens-before the return of `join`, so every access is ordered: no race, and the result is 42. Under ThreadSanitizer (`-fsanitize=thread`, run as `setarch -R ./a.out` on this kernel) the `-DEARLY` variant, which reads `output` while the thread may still write it, is reported (excerpt):

```text
WARNING: ThreadSanitizer: data race
  Write of size 4 by thread T1:
    #0 operator() e10_6.cpp:7
  Previous read of size 4 by main thread:
    #0 main e10_6.cpp:9
SUMMARY: ThreadSanitizer: data race e10_6.cpp:7 in operator()
```

### Sequential consistency, store buffering and why default is `seq_cst`

Consider two atomics `x`, `y` initially 0; thread 1 runs `x.store(1); r1 = y.load();` and thread 2 runs `y.store(1); r2 = x.load();`. This is the *store-buffering* shape. With all four operations `memory_order_seq_cst`, all of them appear in one total order consistent with each thread's program order (cppreference, *Sequentially-consistent ordering*). **Claim:** $r1=r2=0$ is impossible. *Proof.* Suppose both loads return 0. The load of $y$ returning 0 means it precedes thread 2's store of $y$ in the total order $T$; the load of $x$ returning 0 means it precedes thread 1's store of $x$. With program order, $T$ would need $\text{store}_x < \text{load}_y < \text{store}_y < \text{load}_x < \text{store}_x$, a cycle. Contradiction. With only release stores and acquire loads there is no total order: the stores need not be globally visible before the loads execute (each core can hold the store in a store buffer while the later load runs) and $r1=r2=0$ is allowed. On an x86-64 machine with 200,000 rounds we observed $r1=r2=0$ in 0 rounds with `seq_cst`, 630 with release/acquire and 564 with `relaxed`. Hence Dekker/Peterson style mutual exclusion written with plain flags needs `seq_cst` (or fences); a mutex or `seq_cst` atomics is the safe default and weaker orders are an optimization to be justified.

![Timeline of the store-buffering test: both stores wait in buffers while both loads read the old values, giving (0, 0)](/lesson-figures/CPP10-3.svg)

*Figure: why $(r1,r2)=(0,0)$ is possible without a single total order. The loads run between the stores being issued and becoming visible; the counts at the bottom are the measurements of the example below.*

**Example.** The store-buffering test is run 200,000 times with a `std::barrier` releasing both threads together each time, once with relaxed and once with `seq_cst` operations (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`, one machine with an x86-64 CPU):

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

With relaxed operations the outcome that sequential consistency forbids $(r1,r2)=(0,0)$ appeared in 2 runs; with `seq_cst` it never appeared in 200,000. The count is small and varies from run to run because the window is a few nanoseconds wide, so a stress test can show the outcome but never exclude it; the proof above does.

### Deadlock freedom by lock ordering: a proof and its limits

A deadlock requires a cycle in the wait-for graph (the lesson's definition). **Theorem.** If every thread acquires locks only in increasing order of a fixed rank, no deadlock is possible. *Proof.* Suppose threads $T_1,\dots,T_k$ form a cycle: $T_i$ holds lock $a_i$ and waits for $a_{i+1}$ (indices mod $k$). A thread waiting for $a_{i+1}$ while holding $a_i$ acquired $a_i$ first, so $\text{rank}(a_i)<\text{rank}(a_{i+1})$. Going round the cycle gives $\text{rank}(a_1)<\text{rank}(a_2)<\dots<\text{rank}(a_1)$, impossible. $\square$ The proof needs *every* acquisition path to obey the order, including those inside callbacks: this is why CP.22 forbids calling unknown code while holding a lock (C++ Core Guidelines, CP.21 and CP.22). `std::scoped_lock` removes the need for a global rank by using a deadlock-avoidance algorithm, but it needs all the locks in one statement; locks acquired in different functions still need a convention. Two traps: locking the *same* `std::mutex` twice in one thread (for example `transfer(a, a)`) is undefined behavior for a non-recursive mutex, with or without `scoped_lock`; and ordering by address (`std::less<>{}(&a.m, &b.m)`) is a valid rank for mutexes of unrelated objects.

**Example.** Two accounts, $0$ and $1$, and two transfers in opposite directions. The naive version locks the source first; a barrier makes both threads hold their first lock, and a 200 ms limit on the second lock turns the permanent wait into a visible failure. The ordered version always locks the lower index first, and runs 200,000 transfers (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`; also clean under ThreadSanitizer (`-fsanitize=thread`, run as `setarch -R ./a.out` on this kernel)):

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

In the naive run one transfer gave up after 200 ms (without the limit both would wait forever; which of the two gives up varies), and the other then proceeded. The ordered version completed all 200,000 transfers, and the balances still sum to $400{,}020+599{,}980=1{,}000{,}000$, the starting total, as the conservation check requires. The proof applies: both threads acquire in increasing rank, so no cycle can form.

### Condition variables: the invariant and the missed-notification argument

A condition variable is not a flag; it is a *queue of sleeping threads* attached to a predicate over state protected by a mutex. Correctness has three parts (C++ Core Guidelines, CP.42; cppreference, `std::condition_variable`). (1) The predicate is read and the decision to sleep is made while holding the mutex, and `wait` releases the mutex and enqueues the thread atomically; otherwise a state change plus notification could fall between the check and the sleep, and the notification would be lost (the thread sleeps with a true predicate). (2) After waking, the predicate is re-tested under the re-acquired lock, in a loop, because a wake-up proves nothing: it may be spurious, or another thread may have consumed the item between the notification and this thread acquiring the lock. (3) Every state change that can make some waiter's predicate true is followed by a notification that reaches *that kind* of waiter.

Part (3) is where `notify_one` is dangerous. With one condition variable shared by "not full" and "not empty" waiters, `notify_one` may wake a waiter whose predicate is still false, the wake-up is consumed, and a waiter who could have proceeded sleeps on (Exercise 15). The two safe designs are `notify_all` with predicates (correct, but $O(\text{waiters})$ wake-ups per operation) and one condition variable per predicate with `notify_one`. A useful invariant to state in the queue's contract is: *whenever the lock is free, if the queue is non-empty then no consumer that is asleep has a true predicate, and if it is not full then no producer asleep has a true predicate.* Each operation must restore this invariant before unlocking, which is exactly the notification rule. Notifying after unlocking is allowed and can save one context switch, but notifying *before* the state change is a bug.

**Example.** Four consumers wait on *one* condition variable while a producer publishes 6 items, 20 ms apart. Each consumer re-tests its predicate in a loop, so both `notify_one` and `notify_all` are correct; the program counts how often `wait` returned (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2 -pthread`):

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

Both runs deliver all 6 items. `notify_one` costs $6+4=10$ wake-ups (one per item, plus the four consumers woken by the final `notify_all` that ends the run); `notify_all` costs $6\cdot4+4=28$, because each item wakes all four consumers and three of them find nothing and go back to sleep. This is the cost side of the safe design; one condition variable per predicate lets `notify_one` be both correct and cheap.

## Worked example

### Case 1: the basic case

**Problem.** A bounded queue has capacity $K=2$. One producer $P$ pushes the items $1,2,3$ and then calls `close()`; one consumer $C$ loops `while (auto v = q.pop())`. Trace one run in which the queue fills up, say which thread blocks where and why, and decide what is delivered.

**Solution.** (Contract of the bounded-queue section; condition-variable rules of the first two sections.)

1. $P$ locks, `size=0<2`, pushes 1, calls `notify_one(not_empty)`, unlocks. Queue: $[1]$.
2. $P$ pushes 2. Queue: $[1,2]$, full ($\text{size}=K$).
3. $P$ calls `push(3)`: it locks, the predicate `closed || size<2` is false, so `wait` atomically releases the lock and blocks on `not_full`. Queue unchanged: $[1,2]$.
4. $C$ calls `pop`: it locks, the queue is non-empty, takes 1, queue $[2]$, `notify_one(not_full)`, unlocks, returns 1.
5. $P$ wakes (inside `wait` it re-acquires the lock first), re-tests the predicate `size<2`: $1<2$ is true, so it pushes 3. Queue $[2,3]$.
6. $C$ pops 2, then 3: queue empty. A fourth `pop` finds the queue empty and open, so its predicate `closed || !empty` is false and it blocks on `not_empty`.
7. $P$ calls `close()`: sets `closed` under the lock, then `notify_all` on both conditions. $C$ wakes, the predicate holds, the queue is empty, so `pop` returns `nullopt` and the loop ends.

![Grid of the seven steps of Case 1: queue slots, the state of P and C, and the condition variable each waits on](/lesson-figures/CPP10-4.svg)

*Figure: the trace of Case 1 for a queue of capacity 2. Read each column top to bottom: slots, what P does, what C does, what a blocked thread waits on.*

**Check.** Every item was delivered once, in order $1,2,3$, so the total delivered is $3$ and the sum is $6$. Without step 7, $C$ would block forever, which is why `close()` exists. Independent check: the same seven steps replayed against the `BoundedQueue` of the reference implementation (the producer of step 3 is a thread, a short sleep shows that it is blocked):

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

**Takeaway.** Each wait is tied to a predicate over the state, and each state change notifies the condition it may have made true; the stream ends only because `close()` wakes everybody.

### Case 2: three accounts and a lock-order cycle

**Problem.** Three threads transfer money between accounts guarded by mutexes $m_0,m_1,m_2$: $T_1$: `transfer(0→2)`, $T_2$: `transfer(2→1)`, $T_3$: `transfer(1→0)`. A transfer locks the source mutex first, then the destination. Show that a deadlock is reachable, then show that locking in increasing index order removes it, and count the cases.

**Solution.** (Deadlock section and the rank theorem of the theory.)

1. **Naive order.** Lock sequences: $T_1:(0,2)$, $T_2:(2,1)$, $T_3:(1,0)$. Schedule: $T_1$ locks $m_0$, $T_2$ locks $m_2$, $T_3$ locks $m_1$. Now $T_1$ waits for $m_2$ (held by $T_2$), $T_2$ waits for $m_1$ (held by $T_3$), $T_3$ waits for $m_0$ (held by $T_1$): a cycle of length 3 in the wait-for graph. None can proceed.
2. **Ranked order.** Sort each pair by index, rank $=$ index: $T_1:(0,2)$, $T_2:(1,2)$, $T_3:(0,1)$. Suppose a cycle existed, each member holding a lock and waiting for a higher-ranked one; going around it the ranks would strictly increase and return to the start, which is impossible. So no deadlock, by the theorem.
3. **Exhaustive check.** State $=$ (progress of each thread, owner of each mutex); a thread releases both locks when it finishes its second lock. Exploring every interleaving, the naive version has 27 reachable states and 1 deadlocked state (the one in step 1); the ranked version has 24 reachable states and 0 deadlocked states.
4. **Fix in code.** `std::scoped_lock lk(acct[from].m, acct[to].m);` avoids the explicit order and needs `from != to` as a precondition, since locking the same non-recursive mutex twice is undefined behavior.
5. **Contract.** Money is conserved: the sum of balances before and after is equal, which a test can assert after joining the threads, together with ThreadSanitizer to exclude races on the balances.

![Left: wait-for cycle of three threads with the naive lock order. Right: ranked order where every acquisition goes up](/lesson-figures/CPP10-5.svg)

*Figure: the two lock orders of Case 2. The dashed red arrows on the left close a cycle; on the right every arrow points to a higher rank, so the cycle argument of the theory section cannot be completed.*

**Check.** A Python search over all interleavings of the three two-step sequences reproduces step 3: `(27, 1)` for the naive order and `(24, 0)` for the ranked one. The ranked order has the longest chain $0<1<2$, so the rank argument covers all three transfers.

**Takeaway.** A deadlock needs a cycle; one global order of the locks makes a cycle impossible, and exhaustive search of a small model confirms it.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: C++ Core Guidelines, CP.2 and CP.3)* Which of these are data races? (a) two threads read the same `const int`; (b) one thread writes an `int`, another reads it, no synchronization; (c) two threads do `fetch_add` on one `std::atomic<int>`; (d) thread 1 writes `v[0]`, thread 2 writes `v[1]` of a pre-sized `std::vector<int>`. Which one may still be slow, and why?
2. **(Easy)** Two threads each execute `++counter` $3\times10^5$ times on a plain `int`; one run printed 583,904. How many updates were lost and what percentage is that? Write an interleaving of a load/add/store sequence that loses one update, and name two fixes.
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
8. **(Hard)** *(Adapted from: cppreference, std::condition_variable example)* A sensor bursts 90 items in 30 ms; the consumer processes 500 items/s. Compute the backlog at the end of the burst, the time to drain it, and the minimum capacity so the producer never blocks. What is the latency of the last item of the burst?
9. **(Hard)** *(Adapted from: cppreference, std::memory_order)* Explain why the release/acquire flag pattern in the theory section is correct and what goes wrong with `memory_order_relaxed` on both operations. When would you use a mutex instead?
10. **(Hard)** Design. A control thread must always use the most recent sensor reading, ignoring older ones; a logger must see every reading. Specify (i) a `Latest<T>` mailbox, (ii) the queue for the logger, with their locking contracts, and what happens when the logger is slower than the sensor. Which is bounded, and what does "drop" mean for each?
11. **(Mini-project)** Measure throughput (items per second) of your queue with 1 producer and 1 consumer for capacities 1, 8 and 1024 and $10^6$ items; explain the trend; add `pop_for(std::chrono::milliseconds)` using `wait_for`; run everything under ThreadSanitizer.

12. **(Challenge)** Store buffering. Thread 1: `x.store(1); r1 = y.load();` thread 2: `y.store(1); r2 = x.load();` with `x = y = 0`. (a) List all interleavings that preserve program order (there are $\binom42=6$) and the resulting $(r1,r2)$; how many give $r1=r2=1$? (b) Prove that $(0,0)$ cannot occur when all four operations are `seq_cst`. (c) Explain why $(0,0)$ can occur with release stores and acquire loads, and give a minimal change that forbids it. (d) What would you conclude about a flag-based mutual-exclusion protocol written with release/acquire? (adapted from cppreference, *std::memory_order*, "Sequentially-consistent ordering" and "Release-Acquire ordering")
13. **(Challenge)** Lock ordering. Five philosophers sit around a table with five forks (mutexes $f_0,\dots,f_4$); philosopher $i$ needs forks $i$ and $(i+1)\bmod5$. (a) Show an interleaving in which the naive rule "left fork then right fork" deadlocks. (b) Prove that the rule "always take the lower-numbered fork first" cannot deadlock, using the rank argument. Which philosopher's behavior changes? (c) Why does `std::scoped_lock lk(f[i], f[(i+1)%5])` also work, and what would go wrong for a table with one philosopher and one fork? (adapted from C++ Core Guidelines, CP.21 and CP.22)
14. **(Challenge)** The relaxed cycle. Thread 1: `r1 = y.load(); x.store(r1);` thread 2: `r2 = x.load(); y.store(42);`, `x = y = 0`. (a) Prove that $r1=r2=42$ is impossible if all operations are `seq_cst`. (b) Prove it is also impossible if the loads are `acquire` and the stores are `release`, by finding a cycle in happens-before. (c) Why is it allowed when everything is `relaxed`? (d) Why is it irrelevant for the mutex-based queue of this lesson? (adapted from cppreference, *std::memory_order*, "Relaxed ordering")
15. **(Challenge)** A liveness bug. A bounded queue of capacity 1 uses *one* condition variable `cv` for both conditions (not full / not empty) and calls `notify_one()` after every change. (a) Construct a schedule with two producers and two consumers that ends with all four threads blocked although the queue holds an item. (b) Give two different fixes and compare their costs. (c) Which of the CP.42 rules does the "check, then act" `if` version also violate? (adapted from C++ Core Guidelines, CP.42; the schedule is the standard missed-notification argument)

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
2. Lost: $600{,}000-583{,}904=16{,}096$, which is $2.68\%$. Interleaving: A loads 5; B loads 5; A adds and stores 6; B adds and stores 6; two increments, final 6. Fixes: `std::atomic<int>` with `fetch_add`, or a `std::mutex` with `lock_guard` around the increment, or one counter per thread summed at the end (no sharing).
3. `{ std::lock_guard<std::mutex> lk(m); if (queue.empty()) return false; x = queue.front(); queue.pop(); return true; }`: the lock is released when `lk` goes out of scope on both returns (and on an exception thrown by `front`/`pop` or the copy).
4. Bug 1: `if` instead of a loop or predicate: after a spurious wake-up, or if another consumer took the item, `q.front()` is called on an empty queue. Bug 2 (design): there is no way to stop waiting at shutdown. Fix: `cv.wait(lk, [&]{ return closed || !q.empty(); }); if (q.empty()) return std::nullopt;`.
5. Thread 1 locks `a.m`, thread 2 locks `b.m`; then thread 1 waits for `b.m` held by thread 2, and thread 2 waits for `a.m`: a cycle, so both wait forever. Fix: `std::scoped_lock lk(from.m, to.m);` (acquires both without deadlock regardless of argument order); alternatively impose a global order, such as by address.
6. The thread object is destroyed while joinable, so `std::terminate` is called: output `terminate called without an active exception` and exit code 134. Fixes: `t.join();` before returning, or use `std::jthread` (C++20), or a small RAII wrapper that joins in its destructor.
7. `size()` is logically `const` (does not change the queue) but must lock the mutex, which changes the mutex's internal state; declaring the mutex `mutable` allows that. `if (q.size() < cap) q.push(x);` is a check-then-act race: another thread can fill the queue between the two calls, so `push` may block (or exceed an intended policy). Use `try_push(x)`, which does the test and the insertion in one critical section.
8. Burst: the consumer removes $500\times0.03=15$ items during the 30 ms, so the backlog is $90-15=75$ items. Drain time $75/500=0.15$ s. Minimum capacity without blocking: 75 (plus the one being processed). The last item of the burst is the 75th in the backlog, so it is finished after $75/500=0.15$ s, which is its latency (its own $2$ ms of processing is included).
9. The release store happens after `data = 42`; the acquire load that reads `true` synchronizes with it, creating a happens-before edge from the write of `data` to the read, so reading `data` is race-free and sees 42. With relaxed operations there is no ordering between the flag and `data`: the compiler or CPU may reorder, and the read of `data` is a data race (undefined behavior). Use a mutex when more than one variable must be consistent or the logic is more complex than a flag.
10. `Latest<T>`: contract: one mutex protects one `T` and a version counter; `set` overwrites, never blocks beyond the short lock; `get` returns a copy and the version; "drop" = the old value is discarded when replaced. The logger queue: bounded, FIFO, `push` blocks (back-pressure on the sensor thread, usually unacceptable) or `try_push` drops the newest item and increments a drop counter. If the logger is slower, the mailbox hides it (the controller is unaffected); the logger queue either blocks the producer or drops; real systems choose drop-with-counter for sensors and bigger capacity plus a dedicated logging thread.
11. A good answer includes: capacity 1 forces a context switch per item, so throughput is lowest (hundreds of thousands to about a million items/s depending on the machine); capacities 8 and 1024 allow batching and the throughput increases then flattens; `pop_for` returns `std::optional<T>` and uses `not_empty_.wait_for(lk, timeout, predicate)` returning false on timeout; TSan reports no warnings.
12. (a) Operations: $a$ = `x.store(1)`, $b$ = `r1=y.load()` (thread 1, $a$ before $b$), $c$ = `y.store(1)`, $d$ = `r2=x.load()` ($c$ before $d$). The six orders and results: $abcd\to(0,1)$; $acbd\to(1,1)$; $acdb\to(1,1)$; $cabd\to(1,1)$; $cadb\to(1,1)$; $cdab\to(1,0)$. So 4 of the 6 give $(1,1)$, one gives $(0,1)$, one $(1,0)$, and $(0,0)$ never appears (enumerated by script). (b) Suppose $r1=0$ and $r2=0$ with a single total order $T$ consistent with program order. $b$ reads 0, so $b$ precedes $c$ in $T$ (otherwise it would read 1). Likewise $d$ precedes $a$. Program order gives $a<b$ and $c<d$. Hence $a<b<c<d<a$, a cycle in a total order: contradiction. (c) With release/acquire there is no single total order across different atomic variables; the model lets thread 1's store to `x` still sit in a store buffer while its later load of `y` executes, and symmetrically for thread 2, so both loads see 0. Experiment (200,000 rounds, x86-64, `g++ -O2`): $(0,0)$ in 0 rounds for `seq_cst`, 630 for release/acquire and 564 for relaxed. Minimal change: make the stores and loads `seq_cst`, or put a `std::atomic_thread_fence(std::memory_order_seq_cst)` between the store and the load in each thread. (d) A protocol such as Dekker's, where each thread sets its flag and then reads the other's, is exactly this shape, so with release/acquire both threads can enter the critical section; it needs `seq_cst` (or use a mutex).
13. (a) Philosopher $i$ locks $f_i$ and then $f_{(i+1)\bmod5}$. If all five execute their first lock before any second lock, philosopher $i$ holds $f_i$ and waits for $f_{i+1}$ held by $i+1$: a cycle of length 5. (b) Rank fork $j$ as $j$. Philosophers $0,\dots,3$ already lock the lower fork first ($i<i+1$). Philosopher 4 needs forks 4 and 0, and under the new rule locks $f_0$ first, then $f_4$ (the only behavior change). By the theorem every acquisition is in increasing rank, so no cycle exists. Concretely the cycle is broken because philosopher 4 cannot hold $f_4$ while waiting for $f_0$. (c) `scoped_lock` with several mutexes uses a deadlock-avoidance algorithm, so the argument does not depend on the order of arguments (CP.21). With one philosopher and one fork the two arguments are the same mutex `f[0]`, locked twice by one thread: undefined behavior for a non-recursive `std::mutex` (typically a self-deadlock), which no ordering can fix; guard `i != j` or use a single lock.
14. (a) Let the total order be $T$. Program order gives $A<B$ (thread 1: load $y$ = $A$, store $x$ = $B$) and $C<D$ (thread 2: load $x$ = $C$, store $y=42$ = $D$). $r1=42$ means $A$ read $D$'s value, so $D<A$ in $T$ (the only store of 42 to $y$; the initial value is 0). $r2=42$ means $C$ read $B$'s value, so $B<C$. Then $D<A<B<C<D$, a cycle, impossible. (b) Now $A$ is an acquire load that reads the value written by release store $D$, so $D$ synchronizes-with $A$ and $D$ happens-before $A$. Likewise $B$ (release) happens-before $C$. With $A$ sequenced-before $B$ and $C$ sequenced-before $D$: $D\to A\to B\to C\to D$ in happens-before, a cycle, but happens-before must be irreflexive (acyclic), so the outcome is forbidden. (c) With relaxed operations there are no synchronizes-with edges, so only per-variable modification order applies; the model permits $D$ before $A$ in `y`'s order and $B$ before $C$ in `x`'s order with no contradiction (cppreference states this explicitly). (d) The queue uses a mutex, whose unlock/lock pairs form synchronizes-with edges for all data, so all accesses are totally ordered by the lock and no relaxed-cycle reasoning arises.
15. (a) Capacity 1, one cv, `notify_one` after each change. Start: queue holds $x$; producers $P_1,P_2$ are blocked in `push` (predicate `size<1` false) on `cv`. $C_1$ pops $x$ (queue empty) and calls `notify_one`, which picks $P_1$. Before $P_1$ reacquires the lock, $C_2$ calls `pop`, sees an empty queue and waits on `cv`: waiters are $\{P_2,C_2\}$. $P_1$ wakes, pushes $y$ (queue full) and calls `notify_one`; the implementation may choose $P_2$ (waiters are indistinguishable). $P_2$ wakes, finds the queue full, and waits again. Now $C_2$ waits although the queue holds $y$, $P_2$ waits, $P_1$ and $C_1$ have no more work: nobody calls `notify`, all four threads are blocked or idle forever. (b) Fix 1: `notify_all` on the single cv; correct but wakes every waiter (thundering herd, $O(\text{waiters})$ context switches per operation). Fix 2: two condition variables, `not_full` and `not_empty`, with `notify_one` on the one the changed state satisfies; each notification is useful and only the right kind of waiter wakes (this is the design of the lesson's queue). (c) The `if (q.empty()) cv.wait(lk);` form waits without re-checking the condition in a loop, which CP.42 says to avoid (use the predicate overload): with spurious wake-ups or a competing consumer, the code pops from an empty queue. 

## Further reading

- [cppreference: Concurrency support library](https://en.cppreference.com/w/cpp/thread) - threads, mutexes, condition variables, futures and atomics, with examples.
- [C++ Core Guidelines: CP](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - rules for avoiding races and deadlocks (CP.2, CP.20, CP.21, CP.42).
- [cppreference: std::memory_order](https://en.cppreference.com/w/cpp/atomic/memory_order) - the exact meaning of relaxed, acquire, release and seq_cst.

**More practice:** the [ThreadSanitizer manual](https://clang.llvm.org/docs/ThreadSanitizer.html) (reproduce each listed report on a toy program), the Core Guidelines [concurrency and parallelism rules](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#cp-concurrency-and-parallelism) (CP.20 to CP.42 map to exercises 3 to 7), and the runnable examples on cppreference for [`std::condition_variable`](https://en.cppreference.com/w/cpp/thread/condition_variable), [`std::shared_mutex`](https://en.cppreference.com/w/cpp/thread/shared_mutex) and [`std::async`](https://en.cppreference.com/w/cpp/thread/async), which you can extend and run under TSan.