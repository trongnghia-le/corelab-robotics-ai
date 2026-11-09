---
{
  "id": "cpp09-foundations",
  "module_id": "CPP09",
  "title": "Complexity and performance: asymptotics, cache locality, and profiling",
  "summary": "Combine big-O reasoning with the memory-hierarchy cost model, measure honestly, and profile before optimizing.",
  "estimated_minutes": 410,
  "prerequisites": [
    "CPP05",
    "CPP08"
  ],
  "source_refs": [
    {
      "title": "Ulrich Drepper: What Every Programmer Should Know About Memory",
      "url": "https://lwn.net/Articles/250967/"
    },
    {
      "title": "Linux perf Tutorial",
      "url": "https://perf.wiki.kernel.org/index.php/Tutorial"
    },
    {
      "title": "MIT 6.006 Introduction to Algorithms (OpenCourseWare)",
      "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/"
    },
    {
      "title": "Drepper: What Every Programmer Should Know About Memory (PDF edition)",
      "url": "https://www.akkadia.org/drepper/cpumemory.pdf"
    }
  ],
  "objectives": [
    "Derive and compare asymptotic costs and estimate an empirical exponent from timings.",
    "Explain cache lines, spatial locality and why a vector beats a pointer-linked list at equal big-O.",
    "Design a benchmark that avoids the usual measurement traps.",
    "Use a profiler and Amdahl's law to decide what is worth optimizing."
  ],
  "core_theory": [
    "complexity",
    "cache locality",
    "profiling"
  ],
  "labs": [
    "Implement timing statistics, an empirical complexity estimator, a cache-line model and a pool-allocated linked list; then benchmark vector traversal against a shuffled list and report ns per element for three sizes."
  ],
  "assessment_refs": [
    "CPP09-diagnostic-v1"
  ],
  "review_prompts": [
    "A perception node spends 62% of its time in nearest-neighbour search. A teammate wants to rewrite the message serialization instead because it looks slow in the code. Explain what you would do first and what bound Amdahl's law gives for each option."
  ],
  "extension_refs": [
    "https://lwn.net/Articles/250967/",
    "https://perf.wiki.kernel.org/index.php/Tutorial"
  ]
}
---

## Why this matters

A robot has a deadline: a 1 kHz control loop leaves 1 ms per iteration, a 30 Hz camera pipeline about 33 ms per frame, and missing it means lag, jitter or instability. Performance work therefore asks two questions: *how does the cost grow with the problem size* (complexity) and *what does one step actually cost on real hardware* (memory behavior). Big-O alone is misleading: a linked list and a vector both traverse $n$ elements in $O(n)$, yet on this lesson's benchmark the list is about 150 times slower per element once the data no longer fits in cache. And optimizing the wrong function is the most common waste of effort: if a function takes 5% of the run time, even an infinite speedup gains at most 5%. This lesson gives you the cost model, the measurement discipline and the profiling workflow to make performance decisions from evidence.

## Intuition

Computing is cheap, fetching data is expensive. A modern CPU can do several arithmetic operations per nanosecond, but a read that misses every cache goes to main memory and costs on the order of 100 ns, hundreds of operations' worth. Memory is therefore a hierarchy: registers, small fast caches (L1, L2, L3), then DRAM. Data moves between levels in blocks called **cache lines** (typically 64 bytes). If you read a `double` at address $a$, the hardware loads the whole 64-byte line, so the next 7 doubles are free. Traversing a vector uses every byte of every line it loads and lets the hardware **prefetcher** guess the next line. Following pointers to nodes scattered around the heap loads a line to use 16 bytes and the next address is unknown until the current load finishes.

So there are two scales: **asymptotic** (how many steps, as $n$ grows) and **constant factor** (how expensive each step is, which depends on locality). A good engineer reasons about both, then measures.

![Cache line loads: sequential access uses all 8 doubles in a 64-byte line, pointer chasing touches one node per line; below, a log plot of ns per element vs n for vector and shuffled list](/lesson-figures/CPP09.svg)

*Sequential access amortizes each cache-line load over eight doubles; pointer chasing pays a full memory latency per node once the data exceeds the caches.*

**Predict before you compute.** Two programs add up the same 4 million numbers; one reads an array from start to end, the other follows a chain of references that visits the same numbers in random order. Both do 4 million additions. Before reading on, write down how many times slower you expect the second one to be. Most people guess 2 to 5; the measured answer in this lesson is about 150.

**A picture to hold on to.** Think of a library with a small desk (the cache), a reading room (the next cache level) and a warehouse across town (DRAM). Fetching one book from the warehouse takes an hour; a van always brings a whole crate of 64 neighbouring books. If you read the books in shelf order, one trip serves 8 or 16 requests and the driver can start the next trip before you finish the crate (prefetching). If you ask for books in random order, each request is a fresh one-hour trip and the other books in the crate are wasted. Same number of books, completely different cost.

**The wrong intuition** is "an operation costs the same wherever the data lives, so counting operations is enough". Counting operations tells you how the cost *grows*; it says nothing about the *unit* of that cost, which changes by a factor of 100 depending on where the data sits and in what order you touch it. The second wrong intuition is trusting a single timing: a number measured once, in a debug build, with the work possibly deleted by the optimizer, is not evidence.

## Theory and derivation

### Asymptotic cost

$f(n)=O(g(n))$ means $f(n)\le c\,g(n)$ for some constant $c$ and all large $n$. Common growth rates, ordered: $1,\ \log n,\ n,\ n\log n,\ n^2,\ n^3,\ 2^n$. For $n=10^5$ scan points: a pairwise comparison does $n^2=10^{10}$ operations, a sort or a k-d tree build does $n\log_2n\approx1.66\times10^6$, a ratio of about 6000. Rules: drop constants and lower-order terms; nested loops multiply; sequential steps add; a loop that halves its range is $\log n$. Amortized $O(1)$ (vector `push_back`) means the average over a sequence is constant even though single steps can cost $O(n)$.

**Empirical exponent.** If $t(n)\approx c\,n^p$, then $\ln t=\ln c+p\ln n$, a straight line on a log-log plot with slope $p$. Fit the slope by least squares:
$$p=\frac{\sum_i(\ln n_i-\overline{\ln n})(\ln t_i-\overline{\ln t})}{\sum_i(\ln n_i-\overline{\ln n})^2}.$$
Doubling $n$ multiplies the time by $2^p$: about $2$ for linear, $4$ for quadratic. Use at least four sizes spanning a factor of 8 or more, and remember that cache effects bend the line when the data crosses a cache size.

**Example.** A brute-force closest-pair search over $n$ 2D lidar returns compares every pair, $n(n-1)/2$ distance evaluations. The program times it for $n=3000,6000,12000,24000$ (best of 5) and fits the exponent $p$ of $t\propto n^p$ with the least-squares formula above (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, one performance core of an Intel Core i5-12500H pinned with `taskset`; the times belong to that machine). What growth does the fit show, and what time does it predict at $n=48{,}000$?

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

**Solution.** The times grow by $21.34/5.11=4.18$, $87.54/21.34=4.10$ and $349.94/87.54=4.00$ per doubling, close to $2^2$, and the least-squares slope of $\ln t$ against $\ln n$ is $p=2.033$: quadratic, as the nested loop says. At $n=48{,}000$ the fit predicts about $4\times350\approx1400$ ms. The shortest run (5 ms) is the least precise, which is why the first ratio is a little above 4. The times are machine dependent and kept as measured; a rerun on another machine changes them and the exponent in the last digit, not the quadratic shape. The program prints:

```text
n =  3000  best of 5 =     5.11 ms  (min d^2 = 1.45e-06)
n =  6000  best of 5 =    21.34 ms  (min d^2 = 1.84e-06)
n = 12000  best of 5 =    87.54 ms  (min d^2 = 5.76e-08)
n = 24000  best of 5 =   349.94 ms  (min d^2 = 1.22e-07)
fitted exponent p = 2.033
```

### The memory hierarchy cost model

Rough orders of magnitude (they vary by CPU): L1 hit about 1 ns (4 cycles), L2 about 4 ns, L3 about 15-40 ns, DRAM about 80-100 ns. Sequential bandwidth is about 10-30 GB/s, i.e. $\approx0.3$-$0.8$ ns per 8-byte element, the speed the vector sum reaches. A pointer-chasing loop is *latency bound*: each load depends on the previous one, so a cache miss is paid in full: 140 ns per node in our benchmark at 4 million nodes, consistent with DRAM latency plus TLB misses.

**Cache lines.** For an array of elements of $b$ bytes read with stride $s$ (in elements), element $i$ lives in line $\lfloor ib/64\rfloor$. Sequential reads of $n$ elements touch $\lceil nb/64\rceil$ lines. A stride of $64/b$ elements or more touches a new line on *every* read. Example: 1000 floats ($b=4$) read sequentially touch $\lceil4000/64\rceil=63$ lines; read with stride 16 they touch 63 lines too, with 16 times fewer elements. Time follows lines, not elements, once the data is out of cache.

**Layout.** Array of structures (AoS) interleaves fields, so reading one field drags the others through the cache; structure of arrays (SoA) stores each field contiguously. For $N=10^6$ points of 16 bytes (x, y, z, intensity), summing only `z` streams 16 MB as AoS but 4 MB as SoA.

**Two-dimensional traversal.** A row-major $N\times N$ matrix of doubles is traversed row by row with one miss per 8 elements; column by column each access is a new line (stride $8N$ bytes).

**Example.** One random cycle of 8-byte indices is chased through arrays of 16 KiB, 256 KiB, 4 MiB and 64 MiB. Each hop depends on the previous load, so the time per hop is the latency of the level that holds the array (same build and machine as above: 48 KiB L1d and 1.25 MiB L2 per core, 18 MiB shared L3). Which level does each size land in, what latency does each give, and how large is the ratio between the first and last row?

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

**Solution.** The four sizes land in four levels: 16 KiB fits L1d (about 1.1 ns per hop), 256 KiB exceeds L1d but fits L2 (3.0 ns), 4 MiB exceeds L2 but fits L3 (11.9 ns) and 64 MiB exceeds L3, so every hop goes to DRAM (about 110 ns). The ratio between the first and last row is $109.71/1.13=97$, for the same instruction sequence. The 110 ns is close to the 140 ns per node of the shuffled list in the lesson's table; the remaining difference is not isolated here. The timings are machine dependent and kept as measured. The program prints:

```text
     bytes   ns per hop
     16 KiB         1.13
    256 KiB         2.99
   4096 KiB        11.91
  65536 KiB       109.71
```

### Measuring honestly

1. Optimized build (`-O2` or `-O3`), no sanitizers, release assertions as in production.
2. Make the result observable (store into a `volatile` or print) so the optimizer cannot remove the work.
3. Warm up, repeat many times, report the **median** and the spread; the minimum is also useful as a lower bound. Never use a single run.
4. Time only the operation: allocate and initialize outside the timed region.
5. Fix the CPU frequency and close other programs if you can; report the machine.
6. Vary $n$ across cache sizes (a few KB, hundreds of KB, tens of MB) and report ns per element, not total time.
7. Check correctness of the result (sum equals the reference) so you are not timing a bug.

**Example.** Rule 2 in action: the same summing loop (an array of $10^6$ doubles, 100 repetitions) is timed once with its result thrown away and once with the result stored into a `volatile` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, one performance core of an Intel Core i5-12500H pinned with `taskset`). What time per element does each variant report, and which one is trustworthy?

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

**Solution.** The first variant claims 0.000 ns per element: the compiler saw that `work` has no side effects and deleted the calls. A result below one clock cycle per element (about 0.25 ns at 4 GHz) is the signal to suspect dead-code elimination. The second variant, 0.469 ns per element, streams 8 B per element at $8/0.469\approx17$ GB/s, a plausible rate for an 8 MB array, so it is the trustworthy one. The 0.469 ns is machine dependent and kept as measured. The program prints:

```text
result discarded :     0.000 ns per element
result stored    :     0.469 ns per element
```

### Profiling and Amdahl's law

A profiler samples where the program spends time: `perf record -g ./prog` then `perf report`, or `gprof`. Optimize the largest contributor first. If a part takes fraction $f$ of the total time and is made $s$ times faster, the overall speedup is
$$S=\frac{1}{(1-f)+f/s}.$$
With $f=0.3$ and $s=10$: $S=1/(0.7+0.03)=1.37$. Even $s\to\infty$ gives $1/0.7=1.43$. Profile first; the bottleneck is rarely where intuition says.

![Overall speedup against local speedup for f = 0.3, 0.5 and 0.749, each flattening at 1/(1-f)](/lesson-figures/CPP09-5.svg)

*Figure: Amdahl's law. Each curve is $S=1/((1-f)+f/s)$ and flattens at $1/(1-f)$; the two dots are the lesson's $f=0.3,\ s=10$ and the measured stage with $f=0.749,\ s=8$.*

**Example.** A frame has two stages. Stage A (a square root per element) and stage B (a multiply-add per element) are timed separately, Amdahl's law predicts the gain from making A eight times faster, and then A really does one eighth of the work (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, one performance core of an Intel Core i5-12500H pinned with `taskset`; best of 9 runs). What fraction $f$ of the frame is A, what speedup does the formula predict for $s=8$, what is measured, and which stage does the profile point to afterwards?

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

**Solution.** Stage A is $f=20.98/28.02=0.749$ of the time. With $s=8$ the formula $S=1/\bigl((1-f)+f/s\bigr)$ gives $S=1/(0.251+0.749/8)=2.90$ and the measurement gives $28.02/9.60=2.92$, within 1 %. After the change stage B is $7.01/9.60=73\%$ of the frame, and even an infinitely fast A could not beat $1/(1-0.749)=3.98$: the profile now points at B. The times are machine dependent and kept as measured. The program prints:

```text
before: A = 20.98 ms, B = 7.04 ms, total = 28.02 ms, f(A) = 0.749
Amdahl prediction for s = 8 : 2.900
after : A = 2.59 ms, B = 7.01 ms, total = 9.60 ms, measured speedup = 2.919
```

The sliders below show the same law for other values of $f$ and $s$:

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

### Set associativity and conflict misses

A cache of $C$ bytes with line size $L$ and associativity $W$ ("$W$-way") has $S=C/(WL)$ *sets*. A byte address $a$ belongs to line $\lfloor a/L\rfloor$, which can live only in set $\lfloor a/L\rfloor \bmod S$, in any of the $W$ slots of that set (a fully associative cache, $S=1$, would have to compare every tag, which is impractical for megabyte caches; a direct-mapped one has $W=1$) (Drepper, *What Every Programmer Should Know About Memory*, §3.3.1). Capacity is not the only limit: more than $W$ hot lines that map to the same set evict each other even when the cache is mostly empty. These are **conflict misses**.

*Worked case.* An L1d of 32 KiB, 8-way, 64-byte lines has $S=32768/(8\cdot64)=64$ sets. Walk down one column of a row-major matrix with $N$ doubles per row. Row $r$ starts at byte $8Nr$, so its set is $\lfloor 8Nr/64\rfloor \bmod 64$. When $8N$ is a multiple of 64 the set index advances by a constant step $d=(N/8)\bmod 64$ per row, and the column visits only $S/\gcd(d,S)$ distinct sets, i.e. at most $8\,S/\gcd(d,S)$ lines can stay resident. For $N=1024$ (rows of 8192 bytes) $d=128\bmod64=0$: every row falls in the same set and the whole column competes for 8 slots. For $N=1032$, $d=1$ and all 64 sets (512 lines) are used. Drepper measured exactly this (§6.2.1, Figure 6.5): list elements spaced by a multiple of 4096 bytes (64 lines, i.e. $S$ lines) with more than 8 elements cost about 10 cycles per element instead of 3, which also reveals an 8-way, 32 kB L1d. Powers of two are therefore the worst sizes for strided access; padding a row by one element is often enough (Exercise 12).

![Three rings of 64 cache sets showing which sets a column walk visits for N = 1024, 1056 and 1032](/lesson-figures/CPP09-2.svg)

*Figure: the same 32 KiB, 8-way cache seen from a column walk. The step $d=(N/8)\bmod64$ decides whether the column uses 1, 16 or all 64 sets, and with it how many lines can stay resident (after Drepper, §3.3.1).*

**Example.** Sixteen cache lines are linked into one cycle, each holding the offset of the next, and the cycle is walked $10^8$ times. In the first layout the lines are 4096 bytes apart, in the second 4160 bytes. The L1d of this core is 48 KiB, 12-way, so $S=49152/(12\cdot64)=64$ sets, and 4096 bytes is exactly 64 lines (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, one performance core of an Intel Core i5-12500H pinned with `taskset`). In which layout do the lines compete for the same set, and what time per hop does each layout give?

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

**Solution.** With 4096 B spacing all 16 lines map to one set (the set index advances by $64 \bmod 64=0$ per line), and that set has only 12 ways, so under LRU every hop misses L1 and is served by L2 at 3.16 ns (the L2 latency of the previous example was 2.99 ns). With 4160 B $=65$ lines the set index advances by $65\bmod64=1$ per line, so the lines fall in 16 different sets and every hop hits L1: 1.12 ns. The 16 lines occupy only 1 KiB, so capacity is irrelevant; the ratio is $3.16/1.12=2.8$. The timings are machine dependent and kept as measured. The program prints:

```text
stride  4096 B: 3.16 ns per hop
stride  4160 B: 1.12 ns per hop
```

### False sharing and the coherence protocol

The cache line is also the unit of *coherence*. For a core to write a line it must hold it exclusively; if another core's L1d holds a copy, the write sends a request-for-ownership (RFO) that invalidates the other copy, and the line moves between caches. Two threads that increment *different* `int`s which happen to share one 64-byte line are race-free but pay this transfer for almost every write: **false sharing**. Drepper (§3.3.4 and §6.4.1, Figure 6.10) measured a workload in which each thread only increments its own memory location and the run time still grows with the number of threads. Remedies: give each thread its own line (`alignas(64)`, or `std::hardware_destructive_interference_size`), accumulate into a thread-local variable and combine at the end, or use per-thread structures. The price of padding $T$ counters is $64T$ bytes instead of $4T$. Padding must be checked against the alignment of the *base address*: a misaligned array can still let neighbours share a line (Exercise 13).

**Example.** Two threads each increment their own `std::atomic<long>` counter $5\times10^7$ times. In `Shared` the two counters are neighbours in one 16-byte object (one line); in `Padded` each is aligned to 64 bytes. Atomics are used so that neither version has a data race (same build, the two threads pinned to two performance cores with `taskset -c 2,4`; the same program under ThreadSanitizer reports nothing). How much slower is the shared version, and what does the fix cost?

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

**Solution.** The only difference is the line: $1105.6/204.1=5.4$ times slower when the counters share it, because every increment has to take the line away from the other core. The price of the fix is memory, $128$ bytes instead of $16$ (`sizeof(Padded) = 128`). The times are machine dependent and kept as measured. The program prints:

```text
sizeof(Shared) = 16, sizeof(Padded) = 128
same line   :  1105.6 ms
own lines   :   204.1 ms
```

### Latency-bound and bandwidth-bound loops: a throughput model

Let $L$ be the DRAM latency, $k$ the number of cache-line fetches in flight at once (limited by the hardware miss-handling slots), and $\beta$ the peak bandwidth in bytes per ns. A line fetch takes $L$, and at most $k$ overlap, so the line throughput is
$$\text{lines/ns}\le\min\!\left(\frac{k}{L},\ \frac{\beta}{64}\right),\qquad t_{\text{per line}}\ge\max\!\left(\frac{L}{k},\ \frac{64}{\beta}\right).$$
A pointer-chasing loop has $k=1$ because the next address is the content of the current load, so it pays $L$ per node: the 140 ns of our list. A sequential loop is recognized by the hardware prefetcher, which after two or more misses in a pattern fetches ahead (a constant stride is recognized too, but prefetching does not cross a page boundary) (Drepper, §6.3.1), so it behaves as if $k$ were large and reaches $64/\beta$. The two regimes meet at $k^\*=L\beta/64$ lines in flight. With the illustrative values $L=90$ ns and $\beta=12$ GB/s $=12$ bytes/ns, $64/\beta=5.33$ ns per line and $k^\*=90/5.33=16.9$, so more than 16 overlapping fetches are needed to saturate the bus; a core with only 10 slots is limited to $L/10=9$ ns per line. This simplified model (it ignores TLB misses, which add to the shuffled-list cost) explains why interleaving several *independent* traversals speeds up a list walk (Exercise 14).

![Time per node against the number of independent fetches in flight, with the latency-bound slope, the slot limit and the bandwidth floor](/lesson-figures/CPP09-3.svg)

*Figure: the throughput model with $L=140$ ns, $\beta=16$ B/ns and $M=12$ slots (illustrative). The pointer chase sits at $k=1$ on the sloping latency line; the slot limit stops the fall at 11.7 ns, three times above the 4 ns floor that would need $k^\*=35$.*

**Example.** Each of $k$ shuffled cycles of 128 MiB is advanced one node per round, in lock-step; the $k$ loads of a round do not depend on each other, so up to $k$ misses can overlap (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, one performance core of an Intel Core i5-12500H pinned with `taskset`). With $L=126$ ns per node at $k=1$, what does the model $L/k$ predict for $k=2,3,6$, and how do the measured times compare?

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

**Solution.** At $k=1$ the loop pays the whole latency, 126 ns per node. The model predicts $L/k=126.2/2=63.1,\ 126.2/3=42.1,\ 126.2/6=21.0$ ns for $k=2,3,6$; the measured $47.3,\ 32.8,\ 17.6$ ns are 16-25 % lower (for example $1-47.3/63.1=25\%$ and $1-17.6/21.0=16\%$), so the shape (a hyperbola in $k$) is right and the constant is not: the model ignores effects such as address translation that are also overlapped, and their share was not isolated here. At $k=6$ the loop is $126.2/17.6=7.2$ times faster than at $k=1$ with the same total work. The times are machine dependent and kept as measured. The program prints:

```text
 k    ns per node
 1          126.2
 2           47.3
 3           32.8
 6           17.6
```

The plot below shows the time per cache line against the number of overlapped fetches:

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

### Amortized cost of `push_back`, and when constants beat exponents

The claim "amortized $O(1)$" has a short proof. Let a `vector` double its capacity whenever it is full, starting from capacity 1. Pushing $n$ elements triggers reallocations at sizes $1,2,4,\dots,2^j$ with $2^j<n$, each copying $2^i$ elements, so the total copy work is $\sum_{i=0}^{j}2^i=2^{j+1}-1<2n$. Adding the $n$ plain writes, the total is below $3n$ element operations, i.e. below 3 per push on average, which is $O(1)$. The assumption is the *geometric* growth factor: growing by a fixed increment $c$ gives $\sum_i ic=\Theta(n^2/c)$ total work and a quadratic loop. The price is memory: after a reallocation up to half of the capacity is unused, and the copy moves all elements at once, a latency spike that matters for real-time deadlines (use `reserve`). This is the standard argument of introductory algorithms courses such as MIT 6.006.

Asymptotics compare *shapes*, not *values*. Suppose algorithm A costs $a\,n^2$ ns and algorithm B costs $b\,n\log_2n$ ns. They cross at $n^\*$ with $a\,n^\*=b\log_2n^\*$; if B has a large constant, say $b/a=40$, the crossover is where $n=40\log_2n$, near $n\approx 340$, so for 100 points the "worse" algorithm A wins and for 10,000 points B wins by a factor of $10^{8}/(40\cdot10^4\cdot13.3)\approx19$. The memory model adds a second reason: $a$ and $b$ are not constants but step functions of the working set (the 0.8, 1.6, 3.0, 9.0 ns steps of Exercise 15), so the crossover moves when one of the algorithms leaves a cache level first. The practical rule that follows from these sections: choose by asymptotics when $n$ will be large and unknown; choose by a benchmark at the real size when $n$ is known and moderate (a few thousand elements) and the structures differ in locality. Connections: the same reasoning decides $k$-d tree versus brute-force nearest neighbours in perception code (CPP05 containers, M-track geometry), and why `std::sort` falls back to insertion sort on tiny ranges.

**Example.** The program prints every capacity change while 1000 integers are pushed, counts the elements copied by reallocations, and repeats the loop after `reserve(1000)` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -O2`, one performance core of an Intel Core i5-12500H pinned with `taskset`). How many reallocations and element copies occur, what is the cost per push against the bound of 3, and what changes with `reserve`?

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

**Solution.** The capacities double, $1,2,4,\dots,1024$, in 11 reallocations that copy $1+2+\dots+512=1023=2^{10}-1$ elements, in agreement with the sum $2^{j+1}-1$ for $j=9$. Adding the 1000 plain writes gives $(1023+1000)/1000=2.02$ operations per push, below the bound of 3. With `reserve` there are no reallocations and no latency spike inside the loop. The output is deterministic. The program prints:

```text
capacity changes: 1 2 4 8 16 32 64 128 256 512 1024
push_back x1000: 11 reallocations, 1023 element copies (2.02 operations per push, bound 3)
with reserve(1000): 0 reallocations
```

## Worked example

### Case 1: the basic case

**Problem.** Sum $n=4\times10^6$ doubles stored (a) in a `std::vector` and (b) in a linked list whose nodes are visited in shuffled order. Use the measured table below (this machine, `-O2`) to find the cost per element of each, the slowdown of the list, and the empirical exponent of each between $n=10^5$ and $n=4\times10^6$.

| $n$ | vector (ns/element) | shuffled list (ns/element) |
|---|---|---|
| 1,000 | 0.76 | 1.88 |
| 100,000 | 0.77 | 14.4 |
| 4,000,000 | 0.92 | 140 |

**Solution.**

1. **Footprints** (memory hierarchy model). A `Node` is 16 bytes (a `double` and a pointer), so $4\times10^6\cdot16\ \text{B}=64$ MB; the vector holds $4\times10^6\cdot8\ \text{B}=32$ MB. Both exceed typical L2 caches (hundreds of KB to a few MB) and probably L3.
2. **Vector.** The time per element hardly changes, 0.76 to 0.92 ns. The loop streams 8 bytes per element, so $8\ \text{B}/0.92\ \text{ns}\approx8.7$ GB/s, a typical streaming rate; the prefetcher hides the latency (throughput model, $k$ large).
3. **List.** At $n=1000$ the 16 KB fits in L1, so even shuffled access is cheap (1.88 ns, limited by the dependent loads). At $10^5$ (1.6 MB) it spills out of L1/L2 and costs 14.4 ns. At $4\times10^6$ almost every hop misses to DRAM: 140 ns, close to the DRAM latency $L$ (the $k=1$ case of the model). Each node is a separate line fetch: of the 64 bytes loaded only 16 are used.
4. **Slowdown.** $140/0.92=152$ times slower per element, with identical $O(n)$.
5. **Empirical exponent** (asymptotic cost section). Total time is $t=n\cdot(\text{ns per element})$. For the list, between $n=10^5$ and $4\times10^6$: $\dfrac{4\times10^6\cdot140}{10^5\cdot14.4}=389$ for a size increase of 40, so $p=\ln389/\ln40=1.62$. For the vector: $\dfrac{4\times10^6\cdot0.92}{10^5\cdot0.77}=47.8$, so $p=\ln47.8/\ln40=1.05$.
6. **Reading the exponents.** The vector is essentially linear. The list is not constant-factor $O(n)$ here, because the cache regime changed between the two sizes.
7. **Amdahl** (profiling section). If the list traversal were 30 % of a frame and the vector made it 100 times faster: $S=1/(0.7+0.3/100)=1/0.703=1.42$, so what else is in the frame matters.

**Check.** Per line the vector costs $8\cdot0.92=7.4$ ns, which is $64\ \text{B}/7.4\ \text{ns}=8.7$ GB/s, the same rate as in step 2. A Python run of the three results gives `152.2`, `1.617` and `1.048` for the ratio and the two exponents. The list's 140 ns also matches the $\approx110$ ns pointer-chase latency measured for a 64 MiB array in the memory-hierarchy example, within the TLB and node-size differences.

**Takeaway.** Two $O(n)$ traversals differ by a factor of 152 because the unit cost depends on locality, and the empirical exponent shows it as soon as the data leaves a cache level.

### Case 2: a power-of-two matrix width (conflict misses)

**Problem.** An L1d is 32 KiB, 8-way, with 64-byte lines (64 sets). Read 8 adjacent columns of a row-major matrix of doubles with 256 rows, one column after another, each pass going down the 256 rows. Compare $N=1024$ and $N=1032$ doubles per row. Use 4 ns for an L2 hit and 1 ns for an L1 hit, assume LRU replacement and an empty cache at the start. Find the number of misses and the total time for each width.

**Solution.**

1. **Lines touched** (cache-line formula). Column $c$ of row $r$ is at byte $8(rN+c)$. The 8 adjacent columns $c=0,\dots,7$ lie in the same 64-byte line as column 0 when the row start is line-aligned, so the 8 passes use the same 256 lines.
2. **Sets** (set-associativity section). The set of the line is $\lfloor 8(rN+c)/64\rfloor\bmod64$. For $N=1024$ the row stride is $8\cdot1024=8192$ bytes $=128$ lines and $128\bmod64=0$, so all 256 lines map to *one* set with 8 ways. For $N=1032$ the stride is $8256$ bytes $=129$ lines and $129\bmod64=1$: the 256 lines spread over all 64 sets, $256/64=4$ per set, which fits in 8 ways.
3. **Misses.** $N=1024$: 256 distinct lines cycle through 8 ways under LRU, so each line is evicted before it is used again and all $8\cdot256=2048$ accesses miss. $N=1032$: pass 1 misses on 256 lines, passes 2 to 8 hit: 256 misses and $2048-256=1792$ hits.
4. **Time.** $N=1024$: $2048\times4\ \text{ns}=8192$ ns. $N=1032$: $256\times4+1792\times1=2816$ ns. Ratio $8192/2816=2.9$.
5. **Reading the result.** The two programs do identical arithmetic and touch the same number of distinct lines; padding each row by 8 doubles (one line) removes a 2.9-fold slowdown. Visiting the columns in an order where the set conflicts do not occur at the same time (blocking or tiling) removes the problem for all $N$.

![Bar charts of the 64 cache sets: 256 lines in set 0 for N = 1024, four lines in every set for N = 1032](/lesson-figures/CPP09-4.svg)

*Figure: the numbers of Case 2. The right chart uses a different vertical scale (0 to 10) so that the four lines per set are visible against the 8-way capacity.*

**Check.** A set-associative LRU simulation in Python (64 sets, 8 ways, the 2048 accesses in the order above) prints `(2048, 0)` for $N=1024$ and `(256, 1792)` for $N=1032$ as (misses, hits), and `8192/2816` is `2.909`. Independent check by counting: 256 lines in 64 sets is $256/64=4\le8$ for $N=1032$, and $256>8$ in one set for $N=1024$.

**Takeaway.** Capacity is not the only limit: a power-of-two row length can make a column compete for a single set, and one line of padding fixes it.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: MIT 6.006, asymptotic analysis problems)* Give the growth class of each: (a) comparing every pair of $n$ lidar points; (b) binary search in a sorted array of $n$ timestamps; (c) `push_back` $n$ elements into a `vector`; (d) sorting $n$ points with `std::sort`. For $n=10^5$ compare the operation counts of (a) and (d) numerically.
2. **(Easy)** *(Adapted from: Drepper, What Every Programmer Should Know About Memory, cache line discussion)* An array of 2400 `float`s is read sequentially, then with a stride of 8 elements. How many 64-byte cache lines does each pass touch? What does it mean for run time when the array is not in cache?
3. **(Easy)** *(Adapted from: Bryant and O'Hallaron, CS:APP, Amdahl's law)* 45% of a frame's time is image resizing. You make it 8 times faster. What overall speedup do you get, and what is the best possible if resizing were free?
4. **(Medium)** From the worked-example table, explain in four sentences why the shuffled list is 152 times slower at $n=4\times10^6$ although both traversals are $O(n)$. Mention cache lines, prefetching and latency, and say which numbers support each claim.
5. **(Medium)** Find at least four flaws in this benchmark and fix them.
   ```cpp
   auto t0 = std::chrono::steady_clock::now();
   std::vector<double> v(1000000, 1.0);
   double s = 0;
   for (double x : v) s += x;
   auto t1 = std::chrono::steady_clock::now();
   std::cout << std::chrono::duration<double>(t1 - t0).count() << " s\n";
   ```
   (compiled with `g++ -O0`; run once.)
6. **(Medium)** *(Adapted from: CS:APP, matrix traversal and locality)* A $4096\times4096$ row-major matrix of doubles is summed row-by-row and column-by-column. How many cache lines does it contain, how many line loads does each order cause (assume the matrix is far larger than the cache and a line is evicted before it is reused), and what ratio of loads results?
7. **(Medium)** A point cloud has $4\times10^5$ points `{float x, y, z, intensity; uint16_t ring, flags; uint32_t time}` (24 bytes). You only need the mean of `intensity`. Compare the bytes streamed from memory with an AoS `std::vector<Point>` and with SoA `std::vector<float> z`. When does the difference stop mattering?
8. **(Hard)** You measured a routine at $n=1000, 2000, 4000, 8000$: $2.0, 8.1, 32.5, 129$ ms. Estimate the exponent (by hand with ratios, then with the least-squares formula), name the likely complexity, and predict the time at $n=10^5$. State two reasons the prediction might be wrong.
9. **(Hard)** A profile of a perception node shows (illustrative numbers): nearest-neighbour search 55%, point-cloud serialization 20%, voxel filter 15%, other 10%. Compute the maximum overall speedup for (i) making search 5x faster, (ii) making serialization 100x faster. Which first? What would you check before writing code?
10. **(Hard)** A particle filter has 5000 particles `{x, y, theta, weight}` of 32 bytes (padded). Normalizing weights reads only `weight`. Is SoA worth it? Compute the footprint, discuss cache sizes, and describe the benchmark that would decide, including how you would vary $N$.
11. **(Mini-project)** Run the benchmark of this lesson on your machine for $n=10^3,10^5,4\times10^6$; add a strided sum (stride 8 doubles) as a fourth column; fit `loglog_slope` between the largest two sizes for each column; report your cache sizes (`lscpu`) and explain where each curve bends.

12. **(Challenge)** An L1d cache is 32 KiB, 8-way, with 64-byte lines. A $4096\times N$ row-major matrix of doubles is read down one column. (a) Derive the set index of the element in row $r$ and compute, for $N=2048$, $2056$ and $2080$, how many distinct sets the column touches and how many of its lines can stay resident at once. (b) Explain why the $N=2048$ column behaves like an 8-line cache although the column has 4096 lines. (c) What is the smallest padding $p$ (in doubles) added to $N=2048$ that makes the column use all 64 sets, and how evenly are the 4096 rows spread? (adapted from Drepper, *What Every Programmer Should Know About Memory*, §3.3.1 and §6.2.1, Figure 6.5)
13. **(Challenge)** Eight threads each increment their own 4-byte counter stored in one `int counters[]` with a stride of $s$ ints between neighbouring threads' counters. (a) For a 64-byte aligned base, give for $s=1,2,4,8,16$ the number of lines used and the largest number of threads sharing a line, and the memory used. (b) Repeat for a base address that is 36 bytes after a line boundary. (c) Which $s$ removes false sharing in both cases, and what does it cost? (d) Name one design that avoids padding entirely. (adapted from Drepper, §3.3.4 and §6.4.1, Figure 6.10)
14. **(Challenge)** Use the throughput model of this lesson with $L=90$ ns, $\beta=12$ bytes/ns, 64-byte lines and at most $M=10$ lines in flight. A program walks $k$ independent shuffled lists in lock-step (one node of each list per round). (a) Give the time per node for $k=1,2,4,8,10,16$. (b) What is the smallest $k$ that would reach the bandwidth bound if $M$ were unlimited, and why can this machine never reach it? (c) Name two effects the model ignores that would make a real measurement differ. (source: Drepper, §3.3.2 and §6.3.1; the numeric values are illustrative)
15. **(Challenge)** Synthetic timings: $t(n)=n\cdot c(n)$ for $n=2^{10},2^{11},\dots,2^{22}$ doubles, with a cost per element $c=0.8$ ns while the array is $\le32$ KiB, $1.6$ ns up to 1 MiB, $3.0$ ns up to 32 MiB and $9.0$ ns beyond. (a) Fit the exponent over all 13 sizes, over the first four, and over the last four. (b) What is the local exponent across the single step from $n=2^{12}$ to $2^{13}$? (c) Use the all-sizes fit to predict $t(2^{24})$ and compare with the model. (d) State the rule for choosing the fit range. (source: Drepper, §3.3.2, working-set measurements; the cost steps are illustrative)

## Reference implementation

Part 1 is the library the lab asks you to write (statistics, exponent fit, cache-line model, pool-allocated list). Part 2 is the benchmark program; compile it separately with `-O2` and without sanitizers.

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

Output on the machine used for this lesson (yours will differ in absolute numbers but not in shape):

```
n, vector ns/elem, sequential-list ns/elem, shuffled-list ns/elem
1000, 0.76, 1.883, 1.883
100000, 0.76523, 1.89211, 14.388
4000000, 0.923664, 2.37656, 140.04
```

Note that the list whose nodes are linked in memory order (sequential) is only about 2.5 times slower than the vector at every size, so the cost of the shuffled list is caused by the access pattern, not by the extra pointer field.

## Independent practice

### Goal

Build the measurement tools and the data structures for a locality experiment, check them with exact tests, then run the experiment on your own machine and interpret it.

### Setup

`g++` with C++17. Optionally `perf` (`sudo apt install linux-tools-generic`) and `lscpu`. Save the starter and the tests as `lab.cpp`; run the tests with `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab`. The benchmark needs a different build (`-O2`, no sanitizer).

### Tasks

1. Implement `median` and `loglog_slope`; check by hand that points on $y=5x^2$ give slope 2.
2. Implement `lines_touched` and confirm the two 63-line cases from the theory section.
3. Implement `PoolList` with permutation validation and `sum_vector`.
4. Build the benchmark from the reference implementation (it needs `PoolList`-like linking code) and record ns per element for three sizes. Put the three numbers for each column into a table.
5. Use `loglog_slope` on your measured totals for the shuffled list between the last two sizes and compare with the vector.
6. Run `lscpu | grep -i cache` and annotate your table with the cache sizes; mark the rows where the data exceeds L2 and L3.

### Starter code

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

### Tests

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

### Expected output

```
all tests passed
```

For the experiment, expect the vector column to stay within about 1.5x across sizes, the shuffled list to grow by at least 20x from the smallest to the largest size, and the ratio list/vector at the largest size to be in the tens or hundreds.

### Extension challenge

Replace the `PoolList` traversal by a "prefetch-friendly" version that processes eight independent lists at once and measure how much of the latency you can hide. Or run `perf stat -e cache-misses,cache-references ./bench` and compare the miss rates of the two traversals.

### Library track

Google Benchmark (`sudo apt install libbenchmark-dev`) does the measurement hygiene of this lesson for you: it picks the iteration count, repeats, and provides `DoNotOptimize`. Re-run the experiment with it, and cross-check your `loglog_slope` against NumPy.

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

On one test machine the shuffled list ran at about 5.7 M items/s for $4\times10^6$ nodes (about 175 ns per node) against about 450 M items/s for the vector (about 2.2 ns), the same shape as the table in the worked example; items/s is the inverse of ns per element. Compare the `Time` column of `BM_StrideSum` with `BM_VectorSum` (the stride version reads 8 times fewer elements). Expect your numbers to differ. (If linking against `libbenchmark_main` fails with an LTO error, use `BENCHMARK_MAIN()` as above.)

For the fit, NumPy gives the same exponent as your least-squares code:

```python
import numpy as np
n = np.array([1000, 2000, 4000, 8000.0]); t = np.array([2.0, 8.1, 32.5, 129])
p = np.polyfit(np.log(n), np.log(t), 1)[0]      # slope of ln t against ln n
print(round(p, 3))                              # 2.004, equal to loglog_slope({1000,...}, {2.0,...})
assert abs(p - 2.004) < 1e-3 and np.median([4, 1, 3, 2]) == 2.5
```

## Verification

- Check that the timed function returns the right answer (compare with the reference sum) in every configuration.
- Repeat the measurement 5-10 times; if the spread is above about 5% either lower the noise (close programs) or report the spread.
- A result that is exactly `0 ns` or does not change with $n$ means the optimizer removed the loop.
- Compare against the model: a streaming sum near 1 ns per element (or less) is plausible; a vector sum of 20 ns per element signals a `-O0` build or a bug.
- Confirm the empirical exponent with at least four sizes; two points always fit a line.
- Cross-check a profiler's top function with a manual timer around it.

## Failure modes

| Mistake | Effect |
|---|---|
| Timing a `-O0` or sanitizer build | numbers 3-20x off, with different proportions |
| Result unused | the optimizer deletes the loop; "0 ns" |
| Timing allocation with the loop | measures `malloc` and page faults, not the algorithm |
| One run, no warm-up | noise and cold caches dominate |
| Comparing at one size that fits in L1 | list and vector look equal (1.88 vs 0.76 ns here); the effect appears only out of cache |
| Choosing a container by big-O only | $O(1)$ insertion in a list loses to $O(n)$ shifting in a vector for modest $n$ |
| Optimizing a function from guesswork | 5% of runtime cannot give more than 5% |
| Using `float` AoS for a field-wise loop | streams 4x the necessary data |
| Reading the profiler without symbols (`-O2` without `-g`) | useless names and line numbers |

## Alternatives and trade-offs

- **Asymptotic analysis vs benchmarks.** Asymptotics tells you what scales; benchmarks tell you what is fast at your sizes. Use asymptotics to eliminate $O(n^2)$ designs, benchmarks to choose among $O(n)$ ones.
- **`std::vector` vs `std::list`/`std::map`.** Prefer vectors, sorted vectors, or flat maps for small and medium data; use node-based containers only for their special guarantees (stable addresses, cheap splicing).
- **AoS vs SoA vs AoSoA.** AoS is natural for "do everything to one object"; SoA suits "do one thing to every object" and vectorization (SIMD); AoSoA blocks of 8 or 16 balance both.
- **Sampling profiler (`perf`, `gprof`) vs instrumentation (timers, tracing).** Sampling has low overhead and finds hotspots; manual timers/tracing give exact durations of known sections and work for latency in real-time loops.
- **Micro-optimization vs algorithm change.** Improve the algorithm or data layout first (factors of 10-100), then compiler flags and micro-tuning (factors of 1.1-2).
- **Parallelism (CPP10).** More cores help only when the work divides and memory bandwidth is not already saturated; a bandwidth-bound loop does not scale linearly.

## Transfer and retention

The same cost model explains why NumPy vectorized operations beat Python loops (contiguous, cache-friendly, no per-element dispatch), why PyTorch cares about tensor layout (contiguous vs strided), why ROS 2 messages pass by pointer without copying, and why GPU kernels prefer coalesced memory access. Practise by timing one of your own loops at three sizes, and by drawing the log-log plot by hand. In a week, re-derive Amdahl's law from the definition (time before $=1$, time after $=(1-f)+f/s$) and recall the four orders of magnitude for L1, L2, L3 and DRAM latency.

## Exercise answers

1. (a) $O(n^2)$, (b) $O(\log n)$, (c) amortized $O(1)$ per push, $O(n)$ for $n$ pushes, (d) $O(n\log n)$. For $n=10^5$: $n^2=10^{10}$ versus $n\log_2n\approx1.66\times10^6$, a ratio of about 6000.
2. Sequential: $2400\cdot4/64=150$ lines (exactly, from a line-aligned base). Stride 8 floats (32 bytes): elements 0, 8, ..., 2392: 300 elements, two per line, so again 150 lines. The strided pass does half as many reads but loads the same number of lines, so when data is not in cache its run time is about the same as the sequential pass: memory time follows lines, not elements.
3. $S=1/(0.55+0.45/8)=1/0.60625=1.65$. Best possible with free resizing: $1/0.55=1.82$.
4. A good answer: (1) cache lines: each list node load fetches a 64-byte line but uses 16 bytes (8-byte value plus 8-byte pointer), while the vector uses all 64 bytes of each line it loads; (2) prefetching: the vector's addresses are predictable, so the hardware fetches ahead and the loop runs at streaming bandwidth (0.92 ns, about 8.7 GB/s), but the shuffled list's next address depends on the previous load; (3) latency: with 64 MB of nodes every hop misses to DRAM, costing about 140 ns, close to DRAM latency; (4) evidence: at $n=1000$ (16 KB in cache) the ratio is only 2.5, and it grows to 19 at $10^5$ and 152 at $4\times10^6$ as the data leaves the caches.
5. Flaws: (1) `-O0` build, which measures unoptimized code; (2) allocation and initialization of the vector are inside the timed region; (3) `s` is never used, so an optimized build may delete the loop; (4) single run, no warm-up or repetition; (5) total time rather than ns per element, so it cannot be compared across $n$; (6) only one size, so no scaling or cache information. Fix: build with `-O2`, allocate outside the timer, store the result in a `volatile` or print it, repeat 10-1000 times and report the median in ns/element for several sizes.
6. The matrix has $4096^2\cdot8/64=2{,}097{,}152$ lines. Row-by-row: each line is loaded once: about $2.1\times10^6$ loads. Column-by-column: every access is to a different line, and the line is evicted before its neighbours are used: $4096^2=16{,}777{,}216$ loads, 8 times more (one per element rather than one per 8 elements).
7. AoS streams every line: $4\times10^5\cdot24=9.6$ MB (150,000 lines). SoA reads only `intensity`: $4\times10^5\cdot4=1.6$ MB (25,000 lines), a factor of 6. The difference matters when the data does not fit in cache; when the whole array fits in L2/L3 (say $10^4$ points = 240 KB), AoS and SoA run at similar speed.
8. Ratios: $8.1/2.0=4.05$, $32.5/8.1=4.01$, $129/32.5=3.97$, each close to $4=2^2$, so $p\approx2$. Least squares gives $p\approx2.004$. Likely a quadratic algorithm (nested loops, naive pairwise distances). Prediction at $n=10^5$: $2.0\ \text{ms}\cdot(100)^2=20{,}000$ ms, about 20 s. It could be wrong because: the data leaves the cache at larger $n$ (the exponent increases), and a quadratic term may hide lower-order terms or there may be a change of algorithm regime (for example a threshold or memory allocation behavior).
9. (i) $S=1/(0.45+0.55/5)=1/0.56=1.79$. (ii) $S=1/(0.8+0.2/100)=1/0.802=1.25$. Optimize the search first. Before writing code: check with a second measurement (manual timers or `perf`) that the profile is representative, that it is an optimized build, and whether an algorithmic change (a k-d tree or voxel hash instead of brute force) beats micro-tuning.
10. Footprint: $5000\cdot32=160$ KB, which fits comfortably in L2 (typically 256 KB to 2 MB), so SoA will likely give little. Benchmark: time normalization for $N=10^3$ to $10^7$ in both layouts, report ns per particle, and look for the knee where AoS (32 B per weight read) leaves the cache earlier than SoA (8 B per weight); decide using the size you actually run, not the largest. A good answer concludes "keep AoS for 5000 particles unless profiling shows it matters, switch if $N$ grows into millions".
11. A good answer includes: a four-column table with three sizes; a strided column that stays near the vector at small $n$ but approaches a cache-miss cost per element when stride $\ge8$ doubles and the data is large (every read is a new line); slopes close to 1 for the vector (1.0-1.1) and larger (about 1.5-1.7 between the last two sizes) for the shuffled list in the transition region; and a comment that each bend lines up with the L1/L2/L3 capacity from `lscpu`.
12. (a) Row $r$ starts at byte $8Nr$, so the set is $\lfloor 8Nr/64\rfloor \bmod 64$. For $N=2048$: step $d=256\bmod64=0$, so 1 distinct set and at most $1\cdot8=8$ resident lines. For $N=2056$: $d=257\bmod64=1$, $\gcd(1,64)=1$, so 64 sets and $512$ lines. For $N=2080$: $d=260\bmod64=4$, $64/\gcd(4,64)=16$ sets and $128$ lines. (Computed by enumerating all 4096 rows: 1, 64 and 16 distinct sets.) (b) With $N=2048$ every row is exactly 256 lines after the previous one, and $256\equiv0\pmod{64}$, so all 4096 lines map to one set that has 8 ways. Walking the column evicts a line before the next column (whose elements lie in the same lines, 8 doubles per line) can reuse it, so every access misses to L2 even though the column's 256 KiB of lines would fit in many other layouts. (c) Row $r$ starts at byte $8(2048+p)r$. Enumeration for $p=0,\dots,9$: $p=0$ gives 1 set (all 4096 rows in it); every $p$ from 1 to 9 gives all 64 sets with exactly $4096/64=64$ rows in each. So the smallest padding is $p=1$ double (8 bytes); in practice use $p=8$ (one line), which also keeps each row 64-byte aligned.
13. (a) Counter $t$ is at byte $4st$; line $=\lfloor4st/64\rfloor$. Aligned base: $s=1$: 1 line, 8 threads share it, 32 bytes. $s=2$: 1 line, 8 sharers, 64 bytes. $s=4$: 2 lines, 4 sharers, 128 bytes. $s=8$: 4 lines, 2 sharers, 256 bytes. $s=16$: 8 lines, 1 sharer, 512 bytes. (b) With the offset 36: $s=1$: 2 lines, 7 sharers; $s=2$: 2 lines, 4 sharers; $s=4$: 3 lines, 4 sharers; $s=8$: 5 lines, 2 sharers; $s=16$: 8 lines, 1 sharer (all computed by script). (c) $s=16$ ints (64 bytes) is the smallest stride that removes sharing for both alignments, because counters 64 bytes apart can never lie in the same 64-byte line. Cost: $8\cdot64=512$ bytes instead of 32, a factor 16 (and the first/last counter may still share a line with unrelated data before or after the array unless the array itself is `alignas(64)` and padded). (d) Each thread accumulates in a local variable (a register or its own stack, which is on its own lines) and writes the result once at the end (or a reduction after `join`), so there is no shared write during the loop.
14. (a) With $64/\beta=64/12=5.33$ ns, $t=\max(L/\min(k,M),\,5.33)$: $k=1$: 90 ns; $k=2$: 45; $k=4$: 22.5; $k=8$: 11.25; $k=10$: 9; $k=16$: 9 (the 10 slots are saturated). (b) $k^\*=L\beta/64=90/5.33=16.9$, so $k=17$ lists in flight would be needed; the machine has $M=10<17$, so it stays latency-limited at $9$ ns per node, 1.7 times the bandwidth bound of 5.33 ns, and an unlimited-$M$ machine would stop improving at $k=17$. (c) Examples: TLB misses (each node on a new page adds a page-walk), DRAM page/bank effects, the cost of the extra loop bookkeeping and register pressure for many lists, the limit of the prefetch units and shared bandwidth with other cores.
15. (a) The fit of $\ln t$ on $\ln n$ gives $p=1.182$ over all 13 sizes, $1.300$ over the first four ($2^{10}..2^{13}$, which includes the L1 to L2 step) and $1.000$ over the last four ($2^{19}..2^{22}$, all in the 3.0 ns regime). Within each constant-cost regime the slope is exactly 1.000. (b) From $2^{12}$ (0.8 ns, 32 KiB) to $2^{13}$ (1.6 ns, 64 KiB): $t$ grows by $2\cdot(1.6/0.8)=4$ for a size ratio of 2, so the local exponent is $\ln4/\ln2=2.0$. (c) Extrapolating the all-sizes fit to $n=2^{24}$ (128 MiB) predicts $0.53$ of the model value $2^{24}\cdot9.0$ ns, an underestimate by a factor $1.9$, because the data leave the last cache between $2^{22}$ and $2^{24}$ and the fit never saw that regime. (d) Fit only inside one regime (no cache boundary in the range), with at least four sizes, and extrapolate only within the same regime. Report the regime boundaries (from `lscpu`) next to the slope.

## Further reading

- [Drepper: What Every Programmer Should Know About Memory](https://lwn.net/Articles/250967/) - the classic, detailed account of caches, latency and access patterns.
- [Linux perf Tutorial](https://perf.wiki.kernel.org/index.php/Tutorial) - `perf stat`, `perf record` and `perf report` with examples.
- [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/) - complexity analysis, data structures, and problem sets.
- [Drepper (PDF edition): What Every Programmer Should Know About Memory](https://www.akkadia.org/drepper/cpumemory.pdf) - sections 3.3.1 (associativity), 6.2.1 (L1d conflict misses), 6.3.1 (hardware prefetching) and 6.4.1 (false sharing) are the basis of the added theory.

**More practice:** the [Google Benchmark user guide](https://github.com/google/benchmark/blob/main/docs/user_guide.md) (write one benchmark per container), the exercises on asymptotic analysis in [MIT 6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/), the CS:APP [labs page](https://csapp.cs.cmu.edu/3e/labs.html) (the Cache Lab is exactly the locality exercise of this lesson), Drepper's [What Every Programmer Should Know About Memory](https://www.akkadia.org/drepper/cpumemory.pdf), and the [perf tutorial](https://perf.wiki.kernel.org/index.php/Tutorial) / [Brendan Gregg's perf examples](https://www.brendangregg.com/perf.html) for profiling your benchmark.