---
{
  "id": "cpp05-foundations",
  "module_id": "CPP05",
  "title": "STL containers, iterators, and algorithms",
  "summary": "Choose a container from its access pattern, use iterator ranges and standard algorithms correctly, and measure the trade-off.",
  "estimated_minutes": 80,
  "prerequisites": [
    "CPP01"
  ],
  "source_refs": [
    {
      "title": "cppreference: Containers library",
      "url": "https://en.cppreference.com/w/cpp/container"
    },
    {
      "title": "cppreference: Algorithms library",
      "url": "https://en.cppreference.com/w/cpp/algorithm"
    },
    {
      "title": "LearnCpp",
      "url": "https://www.learncpp.com/"
    }
  ],
  "objectives": [
    "Pick between vector, deque, list, map, unordered_map and set from the operations a program performs.",
    "Describe iterator categories, half-open ranges and iterator invalidation.",
    "Use lower_bound, accumulate, remove_if/erase and nth_element correctly.",
    "Design a fair micro-benchmark and interpret the result."
  ],
  "core_theory": [
    "containers",
    "iterators",
    "algorithms"
  ],
  "labs": [
    "Implement a timestamped series on a sorted vector with interpolation, range counts and erase-remove, then benchmark it against std::map and unordered_map for several sizes."
  ],
  "assessment_refs": [
    "CPP05-diagnostic-v1"
  ],
  "review_prompts": [
    "A log analyser loops 'for (auto it = v.begin(); it != v.end(); ++it) if (bad(*it)) v.erase(it);'. Explain why this is undefined behavior and give two corrected versions."
  ],
  "extension_refs": [
    "https://en.cppreference.com/w/cpp/container",
    "https://en.cppreference.com/w/cpp/algorithm"
  ]
}
---

## Why this matters

Most robot code spends its time moving sequences of numbers around: scans, trajectories, timestamped sensor readings, detections. The standard library gives you tested containers and algorithms for these, and choosing wisely changes the cost by orders of magnitude. A nearest-timestamp lookup done by scanning a 360,000-sample hour of 100 Hz data costs 360,000 comparisons; done with a binary search it costs 19. The wrong container is also a source of bugs: erasing in a loop invalidates iterators, and `map::operator[]` silently inserts a missing key. This lesson teaches the model behind the STL (containers hold elements, iterators point into them, algorithms work on iterator ranges) so that you can choose, combine and test them with confidence.

## Intuition

Think of three layers. **Containers** own elements and fix their layout: `vector` is one contiguous block, `list` is separately allocated nodes, `map` is a balanced tree. **Iterators** are generalized pointers: they say "here" and "next". **Algorithms** (`sort`, `find`, `lower_bound`, `accumulate`) are written once against iterators, so they work on any container that offers the right iterator category. An algorithm never changes the *size* of a container, because it only sees iterators; to shrink it you must call the container's `erase`.

Ranges are **half-open**: `[first, last)` contains `first` but not `last`. An empty range has `first == last`. This convention is why `v.end()` is valid to compare with but never to dereference, and why `lower_bound` can return `end()` meaning "not found".

![Contiguous vector with binary search narrowing a window, compared with a tree of nodes, with typical costs](/lesson-figures/CPP05.svg)

*Binary search on a sorted contiguous vector halves the window each step; a tree needs pointer hops for the same logarithmic count.*

## Theory and derivation

### Container choice

| Container | Layout | Index / find | Insert / erase | Notes |
|---|---|---|---|---|
| `vector<T>` | contiguous | $O(1)$ index; $O(n)$ find, $O(\log n)$ if sorted | end: amortized $O(1)$; middle: $O(n)$ | default choice; cache friendly |
| `deque<T>` | blocks | $O(1)$ index | both ends $O(1)$ | FIFO queues, sliding windows |
| `list<T>` | nodes | $O(n)$ | $O(1)$ at a known iterator | rarely worth it; poor locality |
| `map<K,V>` | balanced tree | $O(\log n)$ | $O(\log n)$ | sorted by key, stable iterators |
| `unordered_map<K,V>` | hash table | expected $O(1)$ | expected $O(1)$ | no order, no range queries |
| `set<K>` | tree | $O(\log n)$ | $O(\log n)$ | unique sorted keys |

Choose from the *operations*: do you look up by exact key, by nearest key, by range? Insert at the end only, or in the middle? Need order? A hash map cannot answer "the sample just before time $t$"; a sorted vector or a `map` can.

### Iterators and invalidation

Categories, from weakest to strongest: input, forward, bidirectional, random access (and contiguous). `std::sort` needs random access, so it cannot sort a `std::list` (use `list::sort`). `std::lower_bound` works on forward iterators but is only $O(\log n)$ comparisons *and* steps for random-access ones.

**Invalidation rules** (the most common source of undefined behavior): `vector::push_back` may reallocate, invalidating all iterators, pointers and references; `vector::erase(it)` invalidates `it` and everything after it; `map`/`list` erase invalidates only the erased element; `unordered_map` rehash invalidates iterators but not references.

### Binary search

For a sorted range, `lower_bound(first, last, x)` returns the first element not less than $x$; `upper_bound` returns the first element greater than $x$. After $k$ halvings the window has $\lceil n/2^k\rceil$ elements, so the number of comparisons is at most $\lceil\log_2(n+1)\rceil$. For $n=360{,}000$ this is 19; for $n=10^6$ it is 20. The precondition is that the range is sorted by the same ordering used by the comparator; otherwise the result is meaningless.

Linear interpolation between neighbours $(t_a,v_a)$ and $(t_b,v_b)$ with $t_a\le t\le t_b$:
$$v(t)=v_a+(v_b-v_a)\frac{t-t_a}{t_b-t_a}.$$

### Erase-remove and common algorithms

`std::remove_if(first, last, pred)` moves the kept elements to the front and returns the new logical end; the tail holds unspecified values. Follow it with `container.erase(new_end, container.end())`. `std::accumulate(first, last, init)` folds with `+` (the type of `init` decides the arithmetic: `0` accumulates in `int`, `0.0` in `double`). `std::nth_element(first, nth, last)` places the element that would be at position `nth` in sorted order there, in expected $O(n)$, which suffices for a median (sorting costs $O(n\log n)$).

### Amortized growth

If a vector doubles its capacity when full, pushing $n$ elements copies at most $1+2+4+\dots+2^{k}<2n$ elements in reallocations, so the amortized cost per `push_back` is $O(1)$. With growth factor $g>1$ the total is at most $\frac{g}{g-1}n$.

## Worked example

Series $t=\{0,1,2,4\}$, $v=\{0,10,20,60\}$ stored in a sorted vector. Evaluate $v(3)$.

1. `lower_bound` for $t=3$: first element with $t_i\ge3$. Comparisons: the window is the 4 elements; probe the middle element index 2 ($t=2<3$), so move right; the window is index 3 ($t=4\ge3$). Result: iterator to $(4,60)$.
2. It is not `end()` and not `begin()`, and `it->t != 3`, so we interpolate with the previous element $(2,20)$.
3. $v(3)=20+(60-20)\frac{3-2}{4-2}=20+40\cdot0.5=40$.
4. Boundary checks: $t=4.1$ gives `lower_bound == end()`, return "no value"; $t=-0.1$ gives `begin()` with $t_0=0>-0.1$, return "no value"; $t=1$ gives an exact hit and returns 10 without interpolation.
5. Count of samples in $[1,2]$: `lower_bound(1)` points to index 1, `upper_bound(2)` points to index 3, difference $3-1=2$.
6. Erase-remove with limit 50: `remove_if(|v|>50)` keeps $(0,0),(1,10),(2,20)$ and returns an iterator at index 3; `erase(index3, end)` shrinks the size from 4 to 3, removed count $=4-3=1$.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: cppreference, Containers library overview)* Pick the best container and justify in one sentence: (a) the latest 100 range readings, discarding the oldest; (b) a lookup from camera frame id (integer) to its metadata; (c) detection results that must be kept unique and sorted by id; (d) a 30-minute IMU log queried for "the sample nearest to time $t$".
2. **(Easy)** Predict the output:
   ```cpp
   std::vector<int> v{3, 1, 4, 1, 5, 9, 2, 6};
   auto e = std::remove(v.begin(), v.end(), 1);
   std::cout << (e - v.begin()) << ' ' << v.size();
   v.erase(e, v.end());
   std::cout << ' ' << v.size();
   ```
3. **(Easy)** A 100 Hz log of one hour has 360,000 samples. How many comparisons does a linear scan need in the worst case and how many does `lower_bound` need? What is the ratio?
4. **(Medium)** Find two undefined-behavior bugs in this interpolation helper, and fix them.
   ```cpp
   double interp(const std::vector<Sample>& v, double t) {
     auto it = std::lower_bound(v.begin(), v.end(), t, [](const Sample& s, double x) { return s.t < x; });
     const Sample& a = *(it - 1);
     const Sample& b = *it;
     return a.v + (b.v - a.v) * (t - a.t) / (b.t - a.t);
   }
   ```
5. **(Medium)** *(Adapted from: cppreference, `std::vector::erase` and iterator invalidation)* This loop removes readings above 50. Explain exactly what goes wrong, then write the fix twice (once with the erase return value, once with erase-remove).
   ```cpp
   for (auto it = v.begin(); it != v.end(); ++it)
     if (it->v > 50) v.erase(it);
   ```
6. **(Medium)** Predict the output and name the design lesson:
   ```cpp
   std::map<std::string, double> gains;
   double kp = gains["kp"];
   std::cout << kp << ' ' << gains.size();
   ```
7. **(Medium)** A 1001-sample window needs the median every 10 ms. Compare `std::sort` with `std::nth_element` in cost, state the result of `nth_element` on `{7,1,5,3,9}` at position 2, and say what happens to the other elements.
8. **(Hard)** *(Adapted from: cppreference, `std::lower_bound` and `std::map::lower_bound`)* You must answer "value at time $t$" for $10^6$ stored samples with $2\times10^6$ random queries. Design a fair benchmark of `vector`+`lower_bound`, `map::lower_bound` and an `unordered_map` keyed by the integer sample index. List five things you control (optimization level, warm-up, query generation, result use, repeated runs) and predict the ordering and why `unordered_map` is not directly comparable.
9. **(Hard)** Late samples arrive out of order (about 1% of 1,000 inserts per second into a series of $10^5$ samples of 16 bytes each). Estimate the data moved per middle insertion into a `vector` and per second. Is a `map` justified? What would you measure first?
10. **(Hard)** Derive the amortized cost bound: for growth factor $g$, show that $n$ pushes cause at most $\frac{g}{g-1}n$ element moves in reallocations, and compute it for $g=2$ and $g=1.5$. Why do implementations not choose a very large $g$?
11. **(Mini-project)** Write the benchmark of exercise 8 as a program, report nanoseconds per query for $N\in\{10^3,10^5,10^6\}$ in a table, state the ratios, and explain with one paragraph about cache locality why the gap widens with $N$.

## Reference implementation

A sorted-vector time series with interpolation, inclusive range queries and erase-remove. Compile with `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

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

## Independent practice

### Goal

Build the timestamped lookup structure on a sorted `std::vector`, test its edge cases, and compare it with `std::map` using a benchmark you write.

### Setup

`g++` or `clang++` with C++17. Save the starter and the tests below it as `lab.cpp`, compile with `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab`. For the benchmark in the last task compile a separate file with `-O2` and without sanitizers.

### Tasks

1. Implement `append` and `size`. Make equal and decreasing timestamps fail.
2. Implement `at` with `lower_bound`; handle exact hits, `begin()` and `end()` before interpolating.
3. Implement `count_in` and `mean_in` with `lower_bound`/`upper_bound` and `accumulate`.
4. Implement `drop_above` with erase-remove and return the removed count.
5. Write a second class with the same interface on `std::map<double,double>` using `map::lower_bound`; run the same tests on it.
6. Benchmark both for $N=10^3,10^5,10^6$ and $2\times10^6$ random queries at `-O2`; print ns per query and the ratio.

### Starter code

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

### Tests

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

### Expected output

```
all tests passed
```

For the benchmark, expect `vector` to be faster than `map` and the gap to grow with $N$ (on one test machine the ratios were about 1.0 at $10^3$, 1.7 at $10^5$ and 3.6 at $10^6$; your numbers will differ).

### Extension challenge

Add `insert_sorted(t, v)` that accepts late samples using `upper_bound` and `vector::insert`, and measure the cost as a function of how far from the end the insertion happens. Then compare with a `std::map` implementation for 1% late arrivals.

## Verification

- Property test: for every stored $t_i$, `at(t_i)` must equal $v_i$ exactly; for monotone data the interpolation must be monotone.
- Cross-check against a slow oracle: a linear scan implementation on random queries must give identical answers.
- Edge cases to test every time: empty container, one element, query before the first and after the last, duplicate keys, query exactly on a key.
- Run under `-fsanitize=address,undefined` (and `-D_GLIBCXX_DEBUG` for checked iterators) to catch out-of-range iterators and invalidated iterators.
- Benchmark hygiene: `-O2`, a warm-up pass, queries generated before timing, results consumed so the optimizer cannot delete the loop, several repeats, report the median.

## Failure modes

| Mistake | Symptom |
|---|---|
| `lower_bound` on unsorted data | silently wrong index, no error |
| Dereferencing `end()` or `begin()-1` | crash or garbage value (undefined behavior) |
| `erase` inside a range-for or an iterator loop | skipped elements or crash; use `it = v.erase(it)` or erase-remove |
| `remove_if` without the following `erase` | container keeps its old size, tail holds unspecified values |
| `std::accumulate(first, last, 0)` over doubles | integer accumulation: `{0.5, 0.5, 0.5}` sums to 0 |
| `map::operator[]` on a missing key | inserts a default value (exercise 6); use `find` or `at` for reads |
| Holding a reference into a vector across `push_back` | dangling after reallocation |
| Benchmark that discards the result | the optimizer removes the work and reports about 0 ns |
| Comparator that is not a strict weak ordering (`<=`) | undefined behavior in `sort`, `set` |

## Alternatives and trade-offs

- **Sorted vector vs `map`.** For build-once, query-many data the sorted vector wins on speed and memory; if inserts in the middle dominate, `map` avoids the $O(n)$ shifting. For a few hundred elements, either is fine and the vector is simpler.
- **`unordered_map` vs ordered containers.** Hashing gives expected $O(1)$ exact lookups, but cannot do range or nearest-neighbour queries and has worse worst-case behavior with bad hashes.
- **`deque` vs `vector` for FIFO.** `deque` pops from the front in $O(1)$; with a `vector`, popping the front is $O(n)$ unless you keep a head index (a ring buffer).
- **Algorithms vs hand-written loops.** `std::` algorithms name the intent (`count_if`, `any_of`) and are well tested; a hand loop is fine when early exits or multiple outputs make the algorithm form obscure.
- **Ranges and execution policies (C++20/17).** `std::ranges` improves readability and `std::execution::par` can parallelize some algorithms, at the price of compiler support and the data-race rules of CPP10.

## Transfer and retention

The same ideas appear in NumPy (`np.searchsorted` is `lower_bound`, boolean masks are `remove_if`), in ROS 2 `tf2` buffers (time-ordered caches with interpolation between transforms), and in database indexes (B-trees for range queries, hash indexes for equality). To retain: write the table of container complexities from memory in three days, then list for your last project which container you used for each data set and whether the dominant operation matched. CPP09 builds on this by explaining *why* the contiguous layout wins in practice.

## Exercise answers

1. (a) `std::deque` (or a fixed ring buffer): push back and pop front in $O(1)$. (b) `std::unordered_map<int, Meta>`: exact lookup by integer id, order not needed. (c) `std::set<int>` (or `map` if a payload is attached): unique and sorted. (d) A `std::vector` of samples sorted by time with `lower_bound` (built once, queried often); a `map` also works, but is slower and uses more memory.
2. `6 8 6`. `remove` shifts the six kept elements `{3,4,5,9,2,6}` to the front and returns an iterator at index 6, but the size stays 8 until `erase`, which makes it 6.
3. Linear: 360,000 comparisons. Binary: $\lceil\log_2 360{,}001\rceil=19$. Ratio $\approx 18{,}900$.
4. Bug 1: if `it == v.begin()` (query before the first sample) `it - 1` is before the beginning. Bug 2: if `it == v.end()` (query after the last sample) `*it` dereferences `end()`. Also a division by zero cannot happen if timestamps are strictly increasing, but an exact hit with $t=t_b$ should return directly. Fix: check `it == end` first, then exact equality, then `it == begin`, and only then interpolate (see the reference `at`).
5. `erase(it)` invalidates `it` (and all later iterators), so `++it` on the next loop turn is undefined behavior; even when it appears to work it skips the element that slid into the erased slot. Fix 1: `for (auto it = v.begin(); it != v.end();) { if (it->v > 50) it = v.erase(it); else ++it; }`. Fix 2: `v.erase(std::remove_if(v.begin(), v.end(), [](const Sample& s){ return s.v > 50; }), v.end());` which is also $O(n)$ instead of $O(n^2)$.
6. Output `0 1`. `operator[]` default-constructs and inserts the missing key `"kp"`, so a typo in a parameter name silently becomes a gain of 0 and the map grows. Use `find`/`at` (which throws) for reads, and `[]` only when insertion is intended.
7. `std::sort` is $O(n\log n)$ (about $1001\cdot10\approx10^4$ comparisons), `nth_element` is expected $O(n)$ (a few thousand). The median of `{7,1,5,3,9}` is at index 2 and equals 5. After `nth_element` the elements before are all $\le5$ and the ones after all $\ge5$, in unspecified order; the vector is *not* sorted.
8. Control: `-O2` for all; one warm-up pass (page-in, branch predictors, caches); the same pre-generated random queries for each structure; accumulate results into a variable that is printed so the loop is not eliminated; several repeats with the median. Expected ordering for nearest-time queries: `vector` fastest, `map` slower (pointer chasing, cache misses); `unordered_map` cannot answer nearest-time queries at all, only exact keys, so comparing it is only valid for exact index lookups, where it is fast but answers a different question.
9. 1% of 1000 per second is 10 late inserts per second. A middle insertion shifts on average $n/2=50{,}000$ elements $\times16$ B $=800$ kB; 10 per second is 8 MB/s, trivial. A `map` is not justified; measure the real distribution of lateness (late samples are mostly near the end, so shifts are even smaller) and the query latency budget before changing anything.
10. Reallocations happen when the size reaches $c, gc, g^2c,\dots$ and each copies the current size, so the total is $c+gc+\dots+g^{k}c$ with $g^{k}c\le n$. The geometric sum is at most $n\cdot\frac{1}{1-1/g}=\frac{g}{g-1}n$. For $g=2$: $2n$; for $g=1.5$: $3n$. A very large $g$ wastes memory (up to $(g-1)/g$ of capacity is unused) and the allocator may be unable to find a block; typical values are 1.5 to 2.
11. A good answer has: a table with the three sizes; vector faster than map by a ratio that grows (in one run 1.0, 1.7, 3.6); explanation: the vector's binary search touches a few cache lines and prefetching works, whereas a tree visits nodes scattered over the heap; at $10^6$ elements the tree (about 48 B/node) exceeds the cache and each hop can be a cache miss; and a caveat about the machine and one run.

## Further reading

- [cppreference: Containers library](https://en.cppreference.com/w/cpp/container) - the complete container table with complexity guarantees and invalidation rules.
- [cppreference: Algorithms library](https://en.cppreference.com/w/cpp/algorithm) - every algorithm with preconditions, complexity and examples.
- [LearnCpp](https://www.learncpp.com/) - the chapters on containers, iterators and algorithms with quizzes.

**More practice:** the quizzes at the end of the containers and algorithms chapters on [LearnCpp](https://www.learncpp.com/), and the worked examples attached to each algorithm page on [cppreference](https://en.cppreference.com/w/cpp/algorithm), which you can modify and run to confirm your predictions.
