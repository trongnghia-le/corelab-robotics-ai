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

## Theory and derivation

### Asymptotic cost

$f(n)=O(g(n))$ means $f(n)\le c\,g(n)$ for some constant $c$ and all large $n$. Common growth rates, ordered: $1,\ \log n,\ n,\ n\log n,\ n^2,\ n^3,\ 2^n$. For $n=10^5$ scan points: a pairwise comparison does $n^2=10^{10}$ operations, a sort or a k-d tree build does $n\log_2n\approx1.66\times10^6$, a ratio of about 6000. Rules: drop constants and lower-order terms; nested loops multiply; sequential steps add; a loop that halves its range is $\log n$. Amortized $O(1)$ (vector `push_back`) means the average over a sequence is constant even though single steps can cost $O(n)$.

**Empirical exponent.** If $t(n)\approx c\,n^p$, then $\ln t=\ln c+p\ln n$, a straight line on a log-log plot with slope $p$. Fit the slope by least squares:
$$p=\frac{\sum_i(\ln n_i-\overline{\ln n})(\ln t_i-\overline{\ln t})}{\sum_i(\ln n_i-\overline{\ln n})^2}.$$
Doubling $n$ multiplies the time by $2^p$: about $2$ for linear, $4$ for quadratic. Use at least four sizes spanning a factor of 8 or more, and remember that cache effects bend the line when the data crosses a cache size.

### The memory hierarchy cost model

Rough orders of magnitude (they vary by CPU): L1 hit about 1 ns (4 cycles), L2 about 4 ns, L3 about 15-40 ns, DRAM about 80-100 ns. Sequential bandwidth is about 10-30 GB/s, i.e. $\approx0.3$-$0.8$ ns per 8-byte element, the speed the vector sum reaches. A pointer-chasing loop is *latency bound*: each load depends on the previous one, so a cache miss is paid in full: 140 ns per node in our benchmark at 4 million nodes, consistent with DRAM latency plus TLB misses.

**Cache lines.** For an array of elements of $b$ bytes read with stride $s$ (in elements), element $i$ lives in line $\lfloor ib/64\rfloor$. Sequential reads of $n$ elements touch $\lceil nb/64\rceil$ lines. A stride of $64/b$ elements or more touches a new line on *every* read. Example: 1000 floats ($b=4$) read sequentially touch $\lceil4000/64\rceil=63$ lines; read with stride 16 they touch 63 lines too, with 16 times fewer elements. Time follows lines, not elements, once the data is out of cache.

**Layout.** Array of structures (AoS) interleaves fields, so reading one field drags the others through the cache; structure of arrays (SoA) stores each field contiguously. For $N=10^6$ points of 16 bytes (x, y, z, intensity), summing only `z` streams 16 MB as AoS but 4 MB as SoA.

**Two-dimensional traversal.** A row-major $N\times N$ matrix of doubles is traversed row by row with one miss per 8 elements; column by column each access is a new line (stride $8N$ bytes).

### Measuring honestly

1. Optimized build (`-O2` or `-O3`), no sanitizers, release assertions as in production.
2. Make the result observable (store into a `volatile` or print) so the optimizer cannot remove the work.
3. Warm up, repeat many times, report the **median** and the spread; the minimum is also useful as a lower bound. Never use a single run.
4. Time only the operation: allocate and initialize outside the timed region.
5. Fix the CPU frequency and close other programs if you can; report the machine.
6. Vary $n$ across cache sizes (a few KB, hundreds of KB, tens of MB) and report ns per element, not total time.
7. Check correctness of the result (sum equals the reference) so you are not timing a bug.

### Profiling and Amdahl's law

A profiler samples where the program spends time: `perf record -g ./prog` then `perf report`, or `gprof`. Optimize the largest contributor first. If a part takes fraction $f$ of the total time and is made $s$ times faster, the overall speedup is
$$S=\frac{1}{(1-f)+f/s}.$$
With $f=0.3$ and $s=10$: $S=1/(0.7+0.03)=1.37$. Even $s\to\infty$ gives $1/0.7=1.43$. Profile first; the bottleneck is rarely where intuition says.

## Worked example

**Task.** Estimate the cost of summing $n=4\times10^6$ doubles stored (a) in a `std::vector` and (b) in a linked list whose nodes are visited in shuffled order, using the measured table (this machine, `-O2`):

| $n$ | vector (ns/element) | shuffled list (ns/element) |
|---|---|---|
| 1,000 | 0.76 | 1.88 |
| 100,000 | 0.77 | 14.4 |
| 4,000,000 | 0.92 | 140 |

1. **Footprints.** A `Node` is 16 bytes (a `double` and a pointer), so 4 million nodes occupy 64 MB; the vector holds 32 MB. Both exceed typical L2 caches (hundreds of KB to a few MB) and probably L3.
2. **Vector.** Time per element hardly changes: 0.76 to 0.92 ns. The loop streams 8 bytes per element, so $0.92\ \text{ns}$ per element is about $8.7$ GB/s, a typical streaming rate, and the prefetcher hides the latency.
3. **List.** At $n=1000$ the 16 KB fits in L1, so even shuffled access is cheap (1.88 ns, limited by the dependent loads). At $10^5$ (1.6 MB) it spills out of L1/L2 and costs 14.4 ns. At $4\times10^6$ almost every hop misses to DRAM: 140 ns, close to the DRAM latency. Each node is a separate line fetch: of the 64 bytes loaded only 16 are used.
4. **Ratio.** $140/0.92\approx152$ times slower per element, with identical $O(n)$.
5. **Empirical exponent.** Total time $t=n\cdot(\text{ns per element})$. Between $n=10^5$ and $4\times10^6$ the list's time grows by $\frac{4\times10^6\cdot140}{10^5\cdot14.4}\approx389$ for a size increase of 40, an exponent $\ln389/\ln40\approx1.62$: not constant-factor $O(n)$ behavior, because the cache regime changed. The vector gives $\ln\frac{4\times10^6\cdot0.92}{10^5\cdot0.77}/\ln40\approx1.05$, essentially linear.
6. **Amdahl check.** If the list traversal were 30% of a frame and the vector made it 100 times faster: $S=1/(0.7+0.003)=1.42$, so what else is in the frame matters.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: MIT 6.006, asymptotic analysis problems)* Give the growth class of each: (a) comparing every pair of $n$ lidar points; (b) binary search in a sorted array of $n$ timestamps; (c) `push_back` $n$ elements into a `vector`; (d) sorting $n$ points with `std::sort`. For $n=10^5$ compare the operation counts of (a) and (d) numerically.
2. **(Easy)** *(Adapted from: Drepper, What Every Programmer Should Know About Memory, cache line discussion)* An array of 1000 `float`s is read sequentially, then with a stride of 16 elements. How many 64-byte cache lines does each pass touch? What does it mean for run time when the array is not in cache?
3. **(Easy)** *(Adapted from: Bryant and O'Hallaron, CS:APP, Amdahl's law)* 30% of a frame's time is image resizing. You make it 10 times faster. What overall speedup do you get, and what is the best possible if resizing were free?
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
7. **(Medium)** A point cloud has $10^6$ points `{float x, y, z, intensity}`. You only need the mean of `z`. Compare the bytes streamed from memory with an AoS `std::vector<Point>` and with SoA `std::vector<float> z`. When does the difference stop mattering?
8. **(Hard)** You measured a routine at $n=1000, 2000, 4000, 8000$: $2.0, 8.1, 32.5, 129$ ms. Estimate the exponent (by hand with ratios, then with the least-squares formula), name the likely complexity, and predict the time at $n=10^5$. State two reasons the prediction might be wrong.
9. **(Hard)** A profile of a perception node shows (illustrative numbers): nearest-neighbour search 62%, point-cloud serialization 18%, voxel filter 12%, other 8%. Compute the maximum overall speedup for (i) making search 5x faster, (ii) making serialization 100x faster. Which first? What would you check before writing code?
10. **(Hard)** A particle filter has 5000 particles `{x, y, theta, weight}` of 32 bytes (padded). Normalizing weights reads only `weight`. Is SoA worth it? Compute the footprint, discuss cache sizes, and describe the benchmark that would decide, including how you would vary $N$.
11. **(Mini-project)** Run the benchmark of this lesson on your machine for $n=10^3,10^5,4\times10^6$; add a strided sum (stride 8 doubles) as a fourth column; fit `loglog_slope` between the largest two sizes for each column; report your cache sizes (`lscpu`) and explain where each curve bends.

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
2. Sequential: $4000/64=62.5$, so 63 lines. Stride 16 (64 bytes): elements 0, 16, ..., 992: 63 elements, one per line, 63 lines. The strided pass does 16 times fewer reads but loads the same number of lines, so when data is not in cache its run time is about the same as the sequential pass: memory time follows lines, not elements.
3. $S=1/(0.7+0.3/10)=1/0.73=1.37$. Best possible with free resizing: $1/0.7=1.43$.
4. A good answer: (1) cache lines: each list node load fetches a 64-byte line but uses 16 bytes (8-byte value plus 8-byte pointer), while the vector uses all 64 bytes of each line it loads; (2) prefetching: the vector's addresses are predictable, so the hardware fetches ahead and the loop runs at streaming bandwidth (0.92 ns, about 8.7 GB/s), but the shuffled list's next address depends on the previous load; (3) latency: with 64 MB of nodes every hop misses to DRAM, costing about 140 ns, close to DRAM latency; (4) evidence: at $n=1000$ (16 KB in cache) the ratio is only 2.5, and it grows to 19 at $10^5$ and 152 at $4\times10^6$ as the data leaves the caches.
5. Flaws: (1) `-O0` build, which measures unoptimized code; (2) allocation and initialization of the vector are inside the timed region; (3) `s` is never used, so an optimized build may delete the loop; (4) single run, no warm-up or repetition; (5) total time rather than ns per element, so it cannot be compared across $n$; (6) only one size, so no scaling or cache information. Fix: build with `-O2`, allocate outside the timer, store the result in a `volatile` or print it, repeat 10-1000 times and report the median in ns/element for several sizes.
6. The matrix has $4096^2\cdot8/64=2{,}097{,}152$ lines. Row-by-row: each line is loaded once: about $2.1\times10^6$ loads. Column-by-column: every access is to a different line, and the line is evicted before its neighbours are used: $4096^2=16{,}777{,}216$ loads, 8 times more (one per element rather than one per 8 elements).
7. AoS streams every line: $10^6\cdot16=16$ MB (250,000 lines). SoA reads only `z`: $10^6\cdot4=4$ MB (62,500 lines), a factor of 4. The difference matters when the data does not fit in cache; when the whole array fits in L2/L3 (say $10^4$ points = 160 KB), AoS and SoA run at similar speed.
8. Ratios: $8.1/2.0=4.05$, $32.5/8.1=4.01$, $129/32.5=3.97$, each close to $4=2^2$, so $p\approx2$. Least squares gives $p\approx2.004$. Likely a quadratic algorithm (nested loops, naive pairwise distances). Prediction at $n=10^5$: $2.0\ \text{ms}\cdot(100)^2=20{,}000$ ms, about 20 s. It could be wrong because: the data leaves the cache at larger $n$ (the exponent increases), and a quadratic term may hide lower-order terms or there may be a change of algorithm regime (for example a threshold or memory allocation behavior).
9. (i) $S=1/(0.38+0.62/5)=1/0.504=1.98$. (ii) $S=1/(0.82+0.18/100)=1/0.8218=1.22$. Optimize the search first. Before writing code: check with a second measurement (manual timers or `perf`) that the profile is representative, that it is an optimized build, and whether an algorithmic change (a k-d tree or voxel hash instead of brute force) beats micro-tuning.
10. Footprint: $5000\cdot32=160$ KB, which fits comfortably in L2 (typically 256 KB to 2 MB), so SoA will likely give little. Benchmark: time normalization for $N=10^3$ to $10^7$ in both layouts, report ns per particle, and look for the knee where AoS (32 B per weight read) leaves the cache earlier than SoA (8 B per weight); decide using the size you actually run, not the largest. A good answer concludes "keep AoS for 5000 particles unless profiling shows it matters, switch if $N$ grows into millions".
11. A good answer includes: a four-column table with three sizes; a strided column that stays near the vector at small $n$ but approaches a cache-miss cost per element when stride $\ge8$ doubles and the data is large (every read is a new line); slopes close to 1 for the vector (1.0-1.1) and larger (about 1.5-1.7 between the last two sizes) for the shuffled list in the transition region; and a comment that each bend lines up with the L1/L2/L3 capacity from `lscpu`.

## Further reading

- [Drepper: What Every Programmer Should Know About Memory](https://lwn.net/Articles/250967/) - the classic, detailed account of caches, latency and access patterns.
- [Linux perf Tutorial](https://perf.wiki.kernel.org/index.php/Tutorial) - `perf stat`, `perf record` and `perf report` with examples.
- [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/) - complexity analysis, data structures, and problem sets.

**More practice:** the [Google Benchmark user guide](https://github.com/google/benchmark/blob/main/docs/user_guide.md) (write one benchmark per container), the exercises on asymptotic analysis in [MIT 6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/), the CS:APP [labs page](https://csapp.cs.cmu.edu/3e/labs.html) (the Cache Lab is exactly the locality exercise of this lesson), Drepper's [What Every Programmer Should Know About Memory](https://www.akkadia.org/drepper/cpumemory.pdf), and the [perf tutorial](https://perf.wiki.kernel.org/index.php/Tutorial) / [Brendan Gregg's perf examples](https://www.brendangregg.com/perf.html) for profiling your benchmark.