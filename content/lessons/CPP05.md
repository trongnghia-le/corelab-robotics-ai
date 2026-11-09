---
{
  "id": "cpp05-foundations",
  "module_id": "CPP05",
  "title": "STL containers, iterators, and algorithms",
  "summary": "Choose a container from its access pattern, use iterator ranges and standard algorithms correctly, and measure the trade-off.",
  "estimated_minutes": 395,
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
    },
    {
      "title": "cppreference: std::lower_bound",
      "url": "https://en.cppreference.com/w/cpp/algorithm/lower_bound"
    },
    {
      "title": "cppreference: Compare (named requirement)",
      "url": "https://en.cppreference.com/w/cpp/named_req/Compare"
    },
    {
      "title": "cppreference: std::unordered_map::insert",
      "url": "https://en.cppreference.com/w/cpp/container/unordered_map/insert"
    },
    {
      "title": "cppreference: std::inplace_merge",
      "url": "https://en.cppreference.com/w/cpp/algorithm/inplace_merge"
    },
    {
      "title": "cppreference: std::vector::push_back",
      "url": "https://en.cppreference.com/w/cpp/container/vector/push_back"
    },
    {
      "title": "cppreference: std::vector::insert",
      "url": "https://en.cppreference.com/w/cpp/container/vector/insert"
    },
    {
      "title": "cppreference: std::remove, std::remove_if",
      "url": "https://en.cppreference.com/w/cpp/algorithm/remove"
    },
    {
      "title": "cppreference: std::deque",
      "url": "https://en.cppreference.com/w/cpp/container/deque"
    },
    {
      "title": "cppreference: std::unordered_map",
      "url": "https://en.cppreference.com/w/cpp/container/unordered_map"
    },
    {
      "title": "cppreference: std::map::lower_bound",
      "url": "https://en.cppreference.com/w/cpp/container/map/lower_bound"
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

An everyday picture helps. A sorted `vector` is a corridor of numbered lockers: locker 5000 is reached by walking straight to it, and a binary search is the game "higher or lower" played on the numbers on the doors. A `list` is a treasure hunt in which every note says where the next one is hidden, so the 5000th note costs 4999 steps and nothing is stored in order. A `map` is a tree of signposts ("smaller keys to the left, larger keys to the right"), and an `unordered_map` is a wall of mailboxes where a hash function turns the key into a mailbox number.

A robot example: a lidar driver appends a pose every 100 ms, and the controller needs the pose at the exact time $t=12.34$ s, which falls between two stored poses. The container that keeps the poses in time order and finds the two neighbours quickly is the right one; the container that finds an exact key fastest (the hash table) cannot answer this question at all.

*Predict before reading on.* A log holds 1,000,000 sorted timestamps. How many timestamps must be inspected, in the worst case, to find the position of a given time, and would a tree and a vector inspect the same number? The figures and the theory below settle both questions.

The common wrong intuition is that the complexity table decides everything: "both are $O(\log n)$, so they are equally fast". The table counts steps, not the cost of one step. A step in a sorted vector reads memory next to the previous read; a step in a tree follows a pointer to a node allocated somewhere else, and when the data no longer fits in the cache each hop can wait for main memory. The measurements near the end of the lesson show a factor of about 4 between the two for the same logarithmic step count. A second wrong intuition is that `remove` removes: it only moves elements, and the container still has its old size until `erase` is called.

![Five containers drawn as memory: vector cells with spare capacity, deque blocks behind an index, list nodes, a red-black tree and hash buckets with chains](/lesson-figures/CPP05.svg)

*Figure: where the elements live. Only the vector keeps its elements side by side, which is why a search touches few cache lines; the other containers reach elements through pointers. The tree shows a valid red-black colouring (every path from the root to a missing child passes two black nodes); the buckets use $\text{key}\bmod 5$, as libstdc++ does for `int` keys. Layouts after the container descriptions in cppreference (Containers library).*

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

**Example.** A robot keeps the latest 4 range readings (in m) and a table from frame id to a label. The readings $2.4, 2.5, 2.7, 2.6, 2.8, 3.1$ arrive one by one, and the frames are $\{100\to\text{a}, 130\to\text{b}, 160\to\text{c}\}$. Which container suits the window, which one answers "which stored frame is the first at or after id 140?", and what do the window and that frame look like at the end? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <deque>
#include <iostream>
#include <map>

int main() {
  std::deque<double> window;                       // latest 4 range readings (m)
  for (double r : {2.4, 2.5, 2.7, 2.6, 2.8, 3.1}) {
    window.push_back(r);
    if (window.size() > 4) window.pop_front();
  }
  for (std::size_t i = 0; i < window.size(); ++i) std::cout << (i ? " " : "") << window[i];
  std::cout << '\n';

  std::map<int, const char*> frames{{100, "a"}, {130, "b"}, {160, "c"}};
  auto it = frames.lower_bound(140);               // first key not less than 140
  std::cout << it->first << ' ' << it->second << '\n';
}
```

**Solution.** The window is a `std::deque`: `push_back` and `pop_front` are constant time (cppreference, `std::deque`, Complexity), so dropping the oldest reading once the size exceeds 4 is cheap, and after six readings it holds the last four, $2.7, 2.6, 2.8, 3.1$. The question "which stored frame is the first at or after id 140?" is `std::map::lower_bound(140)`, logarithmic in the size (cppreference, `std::map::lower_bound`): the first key not less than 140 is 160, with label `c`. A hash map cannot answer it, because it has no order. The program prints:

```text
2.7 2.6 2.8 3.1
160 c
```

### Iterators and invalidation

Categories, from weakest to strongest: input, forward, bidirectional, random access (and contiguous). `std::sort` needs random access, so it cannot sort a `std::list` (use `list::sort`). `std::lower_bound` works on forward iterators but is only $O(\log n)$ comparisons *and* steps for random-access ones.

**Invalidation rules** (the most common source of undefined behavior): `vector::push_back` may reallocate, invalidating all iterators, pointers and references; `vector::erase(it)` invalidates `it` and everything after it; `map`/`list` erase invalidates only the erased element; `unordered_map` rehash invalidates iterators but not references.

**Example.** The vector `{10, 20, 30}` has size 3 and capacity 3. An iterator to its first element is taken, then `push_back(40)` is called, and the iterator is dereferenced. Is the iterator still valid, and what does AddressSanitizer report? Compiled with `g++ -std=c++20 -g -fsanitize=address,undefined` (g++ 11.4.0):

```cpp
#include <iostream>
#include <vector>

int main() {
  std::vector<int> v{10, 20, 30};   // size 3, capacity 3
  auto it = v.begin();
  v.push_back(40);                  // full: reallocates, `it` now dangles
  std::cout << *it << '\n';
}
```

**Solution.** The vector is full, so the next `push_back` allocates a new block and frees the old one: when the new size exceeds the old capacity a reallocation takes place, and then all iterators and all references to the elements are invalidated (cppreference, `std::vector::push_back`). The iterator taken before it dangles, and reading `*it` is a heap-use-after-free; the report names the freed block and the `_M_realloc_insert` call that freed it. The report starts as follows (addresses and the rest of the report omitted):

```text
ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010 at pc ...
READ of size 4 at 0x502000000010 thread T0
    #0 ... in main e2.cpp:8
freed by thread T0 here:
    ... in std::vector<int, std::allocator<int> >::_M_realloc_insert<int>(...)
    ... in main e2.cpp:7
```

### Binary search

For a sorted range, `lower_bound(first, last, x)` returns the first element not less than $x$; `upper_bound` returns the first element greater than $x$. After $k$ halvings the window has $\lceil n/2^k\rceil$ elements, so the number of comparisons is at most $\lceil\log_2(n+1)\rceil$. For $n=360{,}000$ this is 19; for $n=10^6$ it is 20. The precondition is that the range is sorted by the same ordering used by the comparator; otherwise the result is meaningless.

Linear interpolation between neighbours $(t_a,v_a)$ and $(t_b,v_b)$ with $t_a\le t\le t_b$:
$$v(t)=v_a+(v_b-v_a)\frac{t-t_a}{t_b-t_a}.$$

**Example.** On the sorted vector $\{1,2,2,2,5,8\}$, what are `lower_bound(2)` and `upper_bound(2)` as indices, how many copies of 2 are there, and what do `lower_bound(3)` and `lower_bound(9)` give? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
  std::vector<int> v{1, 2, 2, 2, 5, 8};
  auto lo = std::lower_bound(v.begin(), v.end(), 2);
  auto hi = std::upper_bound(v.begin(), v.end(), 2);
  std::cout << (lo - v.begin()) << ' ' << (hi - v.begin()) << ' ' << (hi - lo) << '\n';
  std::cout << (std::lower_bound(v.begin(), v.end(), 3) - v.begin()) << ' '
            << (std::lower_bound(v.begin(), v.end(), 9) == v.end()) << '\n';
}
```

**Solution.** `lower_bound(2)` is the first element not less than 2 (index 1) and `upper_bound(2)` the first element greater than 2 (index 4), so the three copies of 2 occupy $[1,4)$ and the count is the difference of the two iterators, $4-1=3$. A value that is absent gives the insertion point: `lower_bound(3)` is index 4 (the element 5). A value above everything gives `end()`: `lower_bound(9) == end()` is true (printed as 1). Each call makes a logarithmic number of comparisons (cppreference, `std::lower_bound`, Complexity). The program prints:

```text
1 4 3
4 1
```

### Erase-remove and common algorithms

`std::remove_if(first, last, pred)` moves the kept elements to the front and returns the new logical end; the tail holds unspecified values. Follow it with `container.erase(new_end, container.end())`. `std::accumulate(first, last, init)` folds with `+` (the type of `init` decides the arithmetic: `0` accumulates in `int`, `0.0` in `double`). `std::nth_element(first, nth, last)` places the element that would be at position `nth` in sorted order there, in expected $O(n)$, which suffices for a median (sorting costs $O(n\log n)$).

**Example.** Six temperature readings (in degrees Celsius), $21.5, 22.0, 85.5, 23.5, 90.0, 22.5$, contain two sensor glitches above 60. After `remove_if` with the predicate $t>60$, what are the logical and physical sizes, and after `erase`, what is the sum of the kept values when `accumulate` starts from `0` and from `0.0`? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <algorithm>
#include <iostream>
#include <numeric>
#include <vector>

int main() {
  std::vector<double> temp{21.5, 22.0, 85.5, 23.5, 90.0, 22.5};
  auto new_end = std::remove_if(temp.begin(), temp.end(), [](double t) { return t > 60.0; });
  std::cout << "logical size " << (new_end - temp.begin()) << ", physical size " << temp.size() << '\n';
  temp.erase(new_end, temp.end());
  std::cout << "after erase " << temp.size() << ", sum with 0: " << std::accumulate(temp.begin(), temp.end(), 0)
            << ", with 0.0: " << std::accumulate(temp.begin(), temp.end(), 0.0) << '\n';
}
```

**Solution.** `remove_if` makes exactly one pass and applies the predicate once per element (cppreference, `std::remove`, Complexity); it keeps $21.5, 22.0, 23.5, 22.5$ and returns the new logical end, so the logical size is 4, but the physical size stays 6 until `erase`. The sum with an `int` initial value truncates every partial sum: $21.5\to21$, $21+22.0=43$, $43+23.5=66.5\to66$, $66+22.5=88.5\to88$. With `0.0` it is the true sum of the kept values, $21.5+22.0+23.5+22.5=89.5$. The program prints:

```text
logical size 4, physical size 6
after erase 4, sum with 0: 88, with 0.0: 89.5
```

### Amortized growth

If a vector doubles its capacity when full, pushing $n$ elements copies at most $1+2+4+\dots+2^{k}<2n$ elements in reallocations, so the amortized cost per `push_back` is $O(1)$. With growth factor $g>1$ the total is at most $\frac{g}{g-1}n$.

![Left: capacity staircase 1, 2, 4, ..., 128 against the number of push_back calls for 100 pushes with seven reallocations; right: schematic of an iterator pointing into the freed old block after a reallocation](/lesson-figures/CPP05-2.svg)

*Figure: left, the measured capacity (libstdc++, g++ 11.4.0) after $n$ calls of `push_back`; each step up is a reallocation and copies as many elements as there are before it (1, 2, 4, ..., 64), 127 in total, below $2n=200$. Right, why the reallocation matters: an iterator taken earlier still points into the old block, which has been freed.*

```explore
{
  "title": "Growth factor: copying work against wasted memory",
  "title_vi": "Hệ số tăng trưởng: công copy so với bộ nhớ lãng phí",
  "prompt": "Predict first: if the growth factor is lowered towards 1, what happens to the worst-case number of copies per push_back, and what does the vector gain in return? Then move the slider.",
  "prompt_vi": "Dự đoán trước: nếu hạ hệ số tăng trưởng xuống gần 1, số lần copy tối đa cho mỗi push_back thay đổi thế nào, và vector được lợi gì? Sau đó kéo thanh trượt.",
  "params": [
    {
      "name": "g",
      "label": "growth factor g",
      "label_vi": "hệ số tăng trưởng g",
      "min": 1.1,
      "max": 4,
      "step": 0.05,
      "value": 2,
      "unit": ""
    },
    {
      "name": "n",
      "label": "pushes n",
      "label_vi": "số lần push n",
      "min": 100,
      "max": 10000,
      "step": 100,
      "value": 1000,
      "unit": ""
    }
  ],
  "let": [
    {
      "name": "per",
      "expr": "g/(g-1)"
    },
    {
      "name": "waste",
      "expr": "(g-1)/g"
    }
  ],
  "plot": {
    "x": {
      "name": "h",
      "min": 1.1,
      "max": 4,
      "label": "growth factor g",
      "label_vi": "hệ số tăng trưởng g"
    },
    "y": {
      "label": "copies per push (bound), capacity per element",
      "label_vi": "copy mỗi push (cận), dung lượng mỗi phần tử",
      "min": 0,
      "max": 12
    },
    "series": [
      {
        "expr": "h/(h-1)",
        "label": "copies per push, at most g/(g-1)",
        "label_vi": "copy mỗi push, tối đa g/(g-1)",
        "color": "orange"
      },
      {
        "expr": "h",
        "label": "capacity / size, at most g",
        "label_vi": "dung lượng / size, tối đa g",
        "color": "blue"
      }
    ],
    "points": [
      {
        "x": "g",
        "y": "per",
        "label": "copies",
        "label_vi": "copy",
        "color": "orange"
      },
      {
        "x": "g",
        "y": "g",
        "label": "capacity",
        "label_vi": "dung lượng",
        "color": "blue"
      }
    ]
  },
  "readouts": [
    {
      "label": "element copies in reallocations, at most",
      "label_vi": "số phần tử bị copy khi cấp phát lại, tối đa",
      "expr": "per*n",
      "unit": "elements",
      "digits": 0
    },
    {
      "label": "copies per push, at most",
      "label_vi": "copy mỗi push, tối đa",
      "expr": "per",
      "unit": "",
      "digits": 2
    },
    {
      "label": "unused capacity, at most",
      "label_vi": "dung lượng chưa dùng, tối đa",
      "expr": "waste*100",
      "unit": "%",
      "digits": 0
    }
  ]
}
```

**Example.** 100 `push_back`s are made into an empty `vector<int>` (libstdc++, which doubles the capacity). How many times does the capacity change, which values does it take, how many elements are relocated in total, and how does that compare with the bound $\frac{g}{g-1}n$ for $g=2$? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <vector>

int main() {
  std::vector<int> v;
  std::vector<std::size_t> caps;
  std::size_t moved = 0;
  for (int i = 0; i < 100; ++i) {
    std::size_t before = v.size(), cap = v.capacity();
    v.push_back(i);
    if (v.capacity() != cap) {            // a (re)allocation happened
      caps.push_back(v.capacity());
      moved += before;                    // `before` elements were relocated (0 on the first)
    }
  }
  for (std::size_t i = 0; i < caps.size(); ++i) std::cout << (i ? " " : "") << caps[i];
  std::cout << "\nreallocations after the first: " << caps.size() - 1 << ", elements relocated: " << moved << '\n';
}
```

**Solution.** The capacity takes the values $1,2,4,\dots,128$, that is 8 values, so it changes 8 times (once at the first allocation and 7 reallocations after it). The reallocations at sizes $1,2,4,\dots,64$ relocate $1+2+4+\dots+64=127$ elements, below the bound $\frac{g}{g-1}n=2\cdot100=200$ for $g=2$. The program prints:

```text
1 2 4 8 16 32 64 128
reallocations after the first: 7, elements relocated: 127
```

### Why iterators are invalidated: reading the rule off the data structure

Each invalidation rule is a consequence of what the container does to its memory, so you can re-derive it instead of memorising a table (cppreference: Containers library, "Iterator invalidation"; `std::unordered_map::insert`).

- **`vector`** stores elements in one block. If $\text{size}<\text{capacity}$, `push_back` writes into spare storage: elements do not move, only `end()` changes. If $\text{size}=\text{capacity}$, a new block is allocated, the $n$ elements are relocated and the old block is freed: *every* iterator, pointer and reference dangles. `insert`/`erase` in the middle shift the tail by one slot, so everything at or after the position is invalidated (the lesson's rule), though elements before it keep their addresses.
- **`deque`** keeps fixed-size blocks plus an index of block pointers. Growing at either end may reallocate the *index* (invalidating iterators) but never moves elements, so references and pointers to elements stay valid (measured with libstdc++ for `push_back` and `push_front`).
- **`list` and `map`/`set`** allocate each element in its own node and only relink pointers, so only the erased element is invalidated.
- **`unordered_map`** is an array of buckets of nodes. Nodes never move, so references and pointers stay valid. But when an insertion would push the load factor $\text{size}/\text{bucket\_count}$ above `max_load_factor` (default 1.0), the table is rebuilt with more buckets, and the iterators (which encode the bucket traversal order) are all invalidated: "If rehashing occurs (due to the insertion), all iterators are invalidated. Otherwise iterators are not invalidated."

Measured with libstdc++ (g++ 11.4): inserting the keys $0,\dots,999$ into an empty `unordered_map<int,int>` changes the bucket count through $1\to13\to29\to59\to127\to257\to541\to1109$ (7 rehashes), with the first rehash on the first insertion and then on the 14th and 30th (sizes just above $13$ and $29$); the address of `m[0]` never changed, and the final load factor is $1000/1109\approx0.9017$. These bucket counts are implementation specific (primes in libstdc++), only the rule is standard. The same measurement for a `vector<int>` filled by 1000 `push_back`s shows capacities $1,2,4,\dots,1024$: ten reallocations after the first allocation, relocating $1+2+\dots+512=1023$ elements, below the $2n$ bound of the amortized-growth argument.

**What the load-factor rule costs.** If keys are spread evenly over the $m$ buckets (the model of "simple uniform hashing"), a table with $n$ keys has load factor $\alpha=n/m$ and a bucket holds $\alpha$ nodes on average, so a failed lookup walks $\alpha$ nodes and a successful one about $1+\alpha/2$. The library promises only average constant-time search (cppreference, `std::unordered_map`), because a bucket that collects many keys makes the search walk a long chain; keeping $\alpha\le$ `max_load_factor` is what makes the average constant, and it is the reason for the rehash. Measured with libstdc++ (g++ 11.4.0, `-O2`, 64-bit random keys, 1031 buckets): $\alpha=0.95$ gave 1.465 nodes per successful lookup (model 1.475) and $\alpha=3.80$ gave 2.921 (model 2.900). Raising `max_load_factor` therefore trades fewer buckets and fewer rehashes for longer chains.

```explore
{
  "title": "Hash table: load factor against nodes visited",
  "title_vi": "Bảng băm: load factor và số node phải duyệt",
  "prompt": "Predict first: if max_load_factor is raised from 1 to 4, how many nodes does a failed lookup walk on average, and what does the table save in return? Then move the slider.",
  "prompt_vi": "Dự đoán trước: nếu nâng max_load_factor từ 1 lên 4, một lần tra cứu thất bại duyệt trung bình bao nhiêu node, và bảng tiết kiệm được gì? Sau đó kéo thanh trượt.",
  "params": [
    {
      "name": "lf",
      "label": "max_load_factor",
      "label_vi": "max_load_factor",
      "min": 0.25,
      "max": 4,
      "step": 0.25,
      "value": 1,
      "unit": ""
    },
    {
      "name": "n",
      "label": "keys n",
      "label_vi": "số key n",
      "min": 100,
      "max": 10000,
      "step": 100,
      "value": 1000,
      "unit": ""
    }
  ],
  "let": [
    {
      "name": "buckets",
      "expr": "ceil(n/lf)"
    }
  ],
  "plot": {
    "x": {
      "name": "a",
      "min": 0.1,
      "max": 4,
      "label": "load factor = size / bucket_count",
      "label_vi": "load factor = size / bucket_count"
    },
    "y": {
      "label": "nodes visited per lookup",
      "label_vi": "số node duyệt mỗi lần tra cứu",
      "min": 0,
      "max": 4
    },
    "series": [
      {
        "expr": "a",
        "label": "failed lookup: a",
        "label_vi": "tra cứu thất bại: a",
        "color": "blue"
      },
      {
        "expr": "1+a/2",
        "label": "successful lookup: 1 + a/2",
        "label_vi": "tra cứu thành công: 1 + a/2",
        "color": "orange"
      }
    ],
    "points": [
      {
        "x": "lf",
        "y": "lf",
        "label": "failed",
        "label_vi": "thất bại",
        "color": "blue"
      },
      {
        "x": "lf",
        "y": "1+lf/2",
        "label": "successful",
        "label_vi": "thành công",
        "color": "orange"
      }
    ]
  },
  "readouts": [
    {
      "label": "nodes walked, failed lookup",
      "label_vi": "node duyệt, tra cứu thất bại",
      "expr": "lf",
      "unit": "",
      "digits": 2
    },
    {
      "label": "nodes walked, successful lookup",
      "label_vi": "node duyệt, tra cứu thành công",
      "expr": "1+lf/2",
      "unit": "",
      "digits": 2
    },
    {
      "label": "buckets needed for n keys (at least)",
      "label_vi": "số bucket cần cho n key (tối thiểu)",
      "expr": "buckets",
      "unit": "",
      "digits": 0
    }
  ]
}
```

**Example.** Fifty more elements are appended to a `vector`, a `deque`, a `list` and, with keys 100 to 149, to an `unordered_map` that held one element. Comparing the address of the first element before and after shows what each layout does with its memory. Which of the four moves its first element, and how many buckets does the map have at the end? (Comparing addresses is shown here for observation only; the standard allows the library to behave differently, see exercise 14.) Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <cstdint>
#include <deque>
#include <iostream>
#include <list>
#include <unordered_map>
#include <vector>

template <class C> void probe(const char* name, C& c) {
  auto before = reinterpret_cast<std::uintptr_t>(&*c.begin());
  for (int i = 0; i < 50; ++i) c.push_back(i);
  std::cout << name << ": first element moved? " << (before != reinterpret_cast<std::uintptr_t>(&*c.begin()) ? "yes" : "no") << '\n';
}

int main() {
  std::vector<int> v{7};  std::deque<int> d{7};  std::list<int> l{7};
  probe("vector", v); probe("deque", d); probe("list", l);
  std::unordered_map<int, int> m{{7, 0}};
  auto before = reinterpret_cast<std::uintptr_t>(&m[7]);
  for (int i = 100; i < 150; ++i) m[i] = i;
  std::cout << "unordered_map: value moved? " << (before != reinterpret_cast<std::uintptr_t>(&m[7]) ? "yes" : "no") << ", buckets " << m.bucket_count() << '\n';
}
```

**Solution.** Only the contiguous block of the `vector` moves, because growing past capacity relocates it to a new block. The `deque` and the `list` keep their elements in place (chunks and nodes are not relocated), and the `unordered_map` keeps its nodes in place even though it rehashes, so the value at key 7 does not move. The last line also prints the number of buckets (59 for 51 elements here). The program prints:

```text
vector: first element moved? yes
deque: first element moved? no
list: first element moved? no
unordered_map: value moved? no, buckets 59
```

### Binary search: loop invariant, exact comparison count, and what `lower_bound` requires

Let `p(e)` be the predicate "$e<x$" under the comparator. `lower_bound` finds the first element for which `p` is false, and it requires only that the range be **partitioned** by `p` (all `true` elements before all `false` ones); a sorted range is the usual way to guarantee that (cppreference: `std::lower_bound`, Notes). The standard loop is

```cpp
auto count = std::distance(first, last);
while (count > 0) {
  auto it = first; auto step = count / 2; std::advance(it, step);
  if (comp(*it, value)) { first = ++it; count -= step + 1; }
  else                    count = step;
}
return first;
```

*Invariant.* Writing the original range as $[a,b)$, at the top of every iteration all elements in $[a,\text{first})$ satisfy `p`, and the first element not satisfying `p` (or $b$) lies in $[\text{first},\text{first}+\text{count}]$. *Initialisation:* $\text{first}=a$, $\text{count}=b-a$ holds trivially. *Maintenance:* with $\text{step}=\lfloor \text{count}/2\rfloor$, if `p(*it)` is true then, by partitioning, everything up to and including `it` satisfies `p`, so we move `first` past `it` and drop $\text{step}+1$ from the count; otherwise `*it` is a candidate answer and the answer lies in $[\text{first},\,\text{first}+\text{step}]$, so `count = step`. *Termination:* `count` strictly decreases and the loop ends at $0$ where the invariant says the answer is `first`. Because the proof uses only the partition property, `lower_bound` does not need a total order on all elements.

*Exact worst case.* Each iteration spends one comparison and leaves $\text{count}'\le\max(\lfloor n/2\rfloor,\,n-\lfloor n/2\rfloor-1)=\lfloor n/2\rfloor$. Hence $W(n)=1+W(\lfloor n/2\rfloor)$ with $W(0)=0$, so $W(n)=\lfloor\log_2 n\rfloor+1=\lceil\log_2(n+1)\rceil$: $19$ for $n=360{,}000$ and $20$ for $n=10^6$. Measured over every possible target: $n=2^{20}$ gives $21$, $n=1000$ gives $10$ (worst) and $9$ (best), and for $n=2^k-1$ every search costs exactly $k$ comparisons.

*A classic bug that this form avoids.* Binary searches written as `mid = (lo + hi) / 2` on `int` overflow when `lo + hi` exceeds $2^{31}-1$: for `lo = 2000000000` and `hi = 2100000000` the sum is $4.1\cdot10^9$, which wraps to $-194{,}967{,}296$ in 32-bit two's complement. The loop above never adds two positions; it halves a *count*, so no sum of indices appears.

![Left: worst-case comparisons floor(log2 n) + 1 against n on a log axis with 10, 14, 17 and 20 marked at 10^3 to 10^6; right: window sizes after each comparison for n = 45 and targets 0 and 44](/lesson-figures/CPP05-3.svg)

*Figure: left, the worst case grows by one comparison each time $n$ doubles, so a million samples cost 20 and a linear scan would cost up to a million. Right, the loop of this section on $n=45$: the window $45\to22\to11\to5\to2\to1$ for target 0 (never less than an element, 6 comparisons, the worst case) and $45\to22\to10\to4\to1$ for target 44 (always less, 5 comparisons).*

**Example.** A comparator that counts its calls gives the exact cost of binary search. On the sorted vector $0,1,\dots,44$ ($n=45$), what are the fewest and the most comparisons over every possible target, and how does the maximum compare with $\lfloor\log_2 45\rfloor+1$ derived above (the traces in the figure)? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <algorithm>
#include <iostream>
#include <numeric>
#include <vector>

int main() {
  std::vector<int> v(45);
  std::iota(v.begin(), v.end(), 0);                // 0, 1, ..., 44
  int worst = 0, best = 99;
  for (int x = 0; x < 45; ++x) {
    int count = 0;
    auto it = std::lower_bound(v.begin(), v.end(), x, [&](int e, int value) { ++count; return e < value; });
    if (it - v.begin() != x) return 1;
    worst = std::max(worst, count);
    best = std::min(best, count);
  }
  std::cout << "n=45 best=" << best << " worst=" << worst << '\n';
}
```

**Solution.** Searching every possible target costs at least 5 and at most 6 comparisons. The worst case is $\lfloor\log_2 45\rfloor+1=5+1=6$, as derived above: the window shrinks $45\to22\to11\to5\to2\to1$ for target 0, which is never less than an element (6 comparisons), and $45\to22\to10\to4\to1$ for target 44 (5 comparisons), the traces in the figure. The program prints:

```text
n=45 best=5 worst=6
```

### Strict weak ordering: why a single NaN can break `set`, `sort` and `lower_bound`

Ordered containers and `std::sort` require the comparator `comp` to be a **strict weak ordering**: irreflexive ($\text{comp}(a,a)$ false), asymmetric, transitive, and with transitive *equivalence* where $a\sim b$ means $\neg\text{comp}(a,b)\wedge\neg\text{comp}(b,a)$ (cppreference: Compare requirements). The built-in `<` on `double` satisfies all of this except when a NaN appears. Take $a=1$, $b=\text{NaN}$, $c=2$: every comparison with NaN is false, so $a\sim b$ and $b\sim c$, but $a<c$ means $a\not\sim c$. Equivalence is not transitive, so `<` is not a strict weak ordering on a set that contains NaN, and the behavior of `std::sort` and `std::set` is undefined. In practice (libstdc++) inserting $1,2,\text{NaN},3$ into a `std::set<double>` leaves 3 elements, while inserting $\text{NaN},1,2,3$ leaves only 1 element: the outcome depends on insertion order, a symptom of undefined behavior. `std::is_sorted` returns `true` on $\{1,2,3,\text{NaN},5,6,7\}$ and `lower_bound` returns index 3 for the targets $4$, $5$ and $6.5$: for $4$ and $5$ that is the correct answer *by the definition* "first element not less than $x$" (the NaN is "not less than" anything), while for $6.5$ the predicate $e<6.5$ is true, false, true after the NaN, so the range is not partitioned and the precondition is violated. The fix is either to reject NaN at the boundary (the lesson's validation habit) or to use a comparator that is a genuine strict weak ordering, such as "NaN sorts after every number": `comp(a,b) = !isnan(a) && (isnan(b) || a < b)`, which is the lexicographic order on the pairs $(\text{isnan}(x),x)$.

**Example.** With $a=4$, $b=\text{NaN}$, $c=5$, are the equivalences $a\sim b$, $b\sim c$ and $a\sim c$ true, is `<` then a strict weak ordering on a set containing NaN, and what does sorting $\{9.5,\text{NaN},7.25,8\}$ with the comparator "NaN last" give? Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <algorithm>
#include <cmath>
#include <iostream>
#include <vector>

int main() {
  const double nan = std::nan("");
  std::cout << "4~NaN " << (!(4 < nan) && !(nan < 4)) << ", NaN~5 " << (!(nan < 5) && !(5 < nan)) << ", 4~5 " << (!(4 < 5) && !(5 < 4)) << '\n';
  std::vector<double> v{9.5, nan, 7.25, 8.0};
  std::sort(v.begin(), v.end(), [](double a, double b) { return !std::isnan(a) && (std::isnan(b) || a < b); });
  for (double x : v) std::cout << x << ' ';
  std::cout << '\n';
}
```

**Solution.** Every comparison with NaN is false, so both $a\sim b$ and $b\sim c$ hold, while $4<5$ gives $a\not\sim c$. Equivalence is not transitive, so `<` is not a strict weak ordering on a set containing NaN. The comparator "NaN last", `comp(a,b) = !isnan(a) && (isnan(b) || a < b)`, repairs this: it sorts $\{9.5,\text{NaN},7.25,8\}$ into $7.25,\;8,\;9.5,\;\text{NaN}$. The program prints (1 stands for true):

```text
4~NaN 1, NaN~5 1, 4~5 0
7.25 8 9.5 nan 
```

## Worked example

Two cases use the tools of the theory above: `lower_bound` and `upper_bound` (Binary search), linear interpolation, `accumulate` and erase-remove (Erase-remove and common algorithms) and `vector::insert` (Iterators and invalidation).

### Case 1: interpolating between neighbours and cleaning a series

**Problem.** A time series is stored as a sorted vector of $(t_i,v_i)$ pairs, $t$ in seconds: $(0,0)$, $(1,10)$, $(2,20)$, $(4,60)$. Find $v(3)$ by linear interpolation, the number of samples with $1\le t\le2$, and the result of removing every sample with $|v|>50$; also say what happens for the queries $t=4.1$, $t=-0.1$ and $t=1$.

**Solution.**

1. *Locate the neighbours (Binary search).* `lower_bound` for $t=3$ starts with a window of $n=4$ elements. The probe is index $\lfloor4/2\rfloor=2$, where $t_2=2<3$, so the window becomes the single element at index 3. The probe there has $t_3=4\ge3$, so the window is empty and the result is index 3, the pair $(4,60)$. Two comparisons were used, within the bound $\lceil\log_2(4+1)\rceil=3$.
2. *Decide which case applies.* The result is neither `end()` nor `begin()`, and $t_3=4\ne3$ is not an exact hit, so the value lies strictly between the previous element $(2,20)$ and $(4,60)$.
3. *Interpolate.* $v(3)=v_a+(v_b-v_a)\dfrac{t-t_a}{t_b-t_a}=20+(60-20)\dfrac{3-2}{4-2}=20+40\cdot0.5=40$.
4. *Boundary queries.* For $t=4.1$ the window ends at `end()`, so the answer is "no value". For $t=-0.1$ the result is `begin()` with $t_0=0>-0.1$, so again "no value". For $t=1$ the result is index 1 with $t_1=1$ equal to the query, an exact hit: return 10 without interpolating.
5. *Count a closed range.* `lower_bound(1)` is index 1 and `upper_bound(2)` is index 3, so the number of samples with $1\le t\le2$ is $3-1=2$.
6. *Erase-remove with limit 50.* `remove_if(|v|>50)` keeps $(0,0)$, $(1,10)$, $(2,20)$ and returns the iterator at index 3; `erase(index 3, end)` shrinks the size from 4 to 3, so the removed count is $4-3=1$.

**Check.** The point $t=3$ is the midpoint of $[2,4]$, so $v(3)$ must be the midpoint of $20$ and $60$, which is 40. The reference implementation below returns the same results for every step (its self-test passes under `-fsanitize=address,undefined`).

**Takeaway.** A sorted vector answers "value at time $t$" with two cheap decisions, a binary search and a case split on `end()`, `begin()` and exact hits, before any arithmetic is done.

### Case 2: a late sample, a spike and a range mean

**Problem.** A current sensor log (milliseconds, amperes) holds the sorted samples $(10,3.0)$, $(20,3.2)$, $(30,3.1)$, $(50,9.8)$, $(60,3.4)$, $(80,3.5)$. (a) A late sample $(40,3.3)$ arrives: find its insertion index and how many elements `vector::insert` shifts. (b) Compute the mean of the samples with $20\le t\le60$ ms. (c) The value 9.8 A is a spike: remove every sample above 5 A and recompute the mean over the same range. (d) Interpolate the current at $t=45$ ms in the cleaned series.

**Solution.**

1. *Insertion index (Binary search).* `upper_bound(40)` is the first element with $t>40$, that is $(50,9.8)$ at index 3. Inserting there keeps the series sorted, also when equal timestamps exist.
2. *Cost of the insertion (Iterators and invalidation).* `vector::insert` shifts the elements from the insertion point to the end: $6-3=3$ elements move one slot (cppreference, `std::vector::insert`, Complexity: linear in the distance from the position to the end). The size becomes 7, and the iterators at or after index 3 are invalidated (every iterator if the capacity was exhausted).
3. *Range of the mean.* In the new series $t=\{10,20,30,40,50,60,80\}$, `lower_bound(20)` is index 1 and `upper_bound(60)` is index 6, so the range holds $6-1=5$ samples: $3.2$, $3.1$, $3.3$, $9.8$, $3.4$.
4. *Mean with the spike.* `accumulate(lo, hi, 0.0, ...)` adds the values: $3.2+3.1+3.3+9.8+3.4=22.8$ A, and the mean is $22.8/5=4.56$ A. The initial value must be `0.0`: an `int` would truncate every partial sum.
5. *Clean with erase-remove.* `remove_if(v>5)` keeps 6 samples and `erase` removes the one sample above the limit, so the size goes from 7 to 6. The samples in $20\le t\le60$ are now $3.2$, $3.1$, $3.3$, $3.4$ (4 samples), with sum $13.0$ A and mean $13.0/4=3.25$ A.
6. *Interpolate after cleaning.* In the cleaned series `lower_bound(45)` finds $(60,3.4)$ and its predecessor is the late sample $(40,3.3)$, so $v(45)=3.3+(3.4-3.3)\dfrac{45-40}{60-40}=3.3+0.1\cdot0.25=3.325$ A.

**Check.** A Python run gives $22.8/5=4.56$, $13.0/4=3.25$ and $3.325$ (floating-point output $4.5600000000000005$, $3.2500000000000004$, $3.3249999999999997$). A C++ program with the same calls prints `insert index 3, tail elements moved 3`, `range [1,6) count 5 mean 4.56`, `removed 1`, `count 4 mean 3.25`, `v(45) = 3.325` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). A sanity check on meaning: one 9.8 A outlier among four values near 3.25 A raises the mean by 1.31 A, which is why the cleaning step precedes the statistics.

**Takeaway.** The order of operations matters: insert late data in sorted position, clean the outliers, and only then compute means and interpolations, because each step changes the indices and values the next one sees.

![Left: the sorted series after the insertion with the 9.8 A spike, the range 20 to 60 ms and the two means 4.56 A and 3.25 A; right: the elements before and after vector::insert at index 3 with three shifted elements](/lesson-figures/CPP05-4.svg)

*Figure: the numbers of Case 2. The shaded band is the range $[20,60]$ ms; the dashed lines are the means over that range with and without the spike. The table shows the three elements (amber) that `vector::insert` shifts to make room for the late sample (green).*

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
3. **(Easy)** A 200 Hz log of 90 minutes has 1,080,000 samples. How many comparisons does a linear scan need in the worst case and how many does `lower_bound` need? What is the ratio?
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
10. **(Hard)** Derive the amortized cost bound: for growth factor $g$, show that $n$ pushes cause at most $\frac{g}{g-1}n$ element moves in reallocations, and compute it for $g=1.25$ and $g=3$. Why do implementations not choose a very large $g$?
11. **(Mini-project)** Write the benchmark of exercise 8 as a program, report nanoseconds per query for $N\in\{10^3,10^5,10^6\}$ in a table, state the ratios, and explain with one paragraph about cache locality why the gap widens with $N$.

12. **(Challenge)** Binary search, exactly. Using the `lower_bound` loop in the theory section, (a) prove that the invariant is maintained when `comp(*it, value)` is false, and that termination returns the first element that is not less than `value`. (b) Prove that the worst case is $\lfloor\log_2 n\rfloor+1$ comparisons and evaluate it for $n=1$, $5000$ and $2^{16}$. (c) For which $n\le40$ is the best case equal to the worst case? State the pattern, and give the best and worst case for $n=5000$. (d) A teammate writes `mid = (lo + hi) / 2` with 32-bit `int` indices on a log of $2.0\cdot10^9$ entries searched in the upper half, with `lo = 1900000000` and `hi = 2000000000`: compute `lo + hi` as a 32-bit two's-complement value and give the safe formula. (adapted from cppreference, `std::lower_bound`, Complexity and Possible implementation)
13. **(Challenge)** NaN in a sorted container. (a) Prove that `a < b` on `double` is not a strict weak ordering on a set containing NaN by exhibiting three values whose equivalence relation is not transitive. (b) For the vector $\{1.5,3.5,\text{NaN},7.5,9.5\}$ give `lower_bound(x)`'s index for $x=1,\,3.5,\,5,\,7.5,\,8.5,\,10$ with the default `<` (libstdc++, g++ 11.4), and say for which of them the result is correct by the definition and for which the precondition is violated. (c) Predict the size of a `std::set<double>` after inserting $4,6,\text{NaN},8$ and after inserting $\text{NaN},4,6,8$. (d) Give a comparator that is a strict weak ordering with NaN sorted last, argue why, and state what `std::sort` returns for $\{8,\text{NaN},5,\text{NaN},6\}$. (adapted from cppreference, Compare named requirement and `std::lower_bound` Notes)
14. **(Challenge)** Predict, then measure, invalidation and growth. (a) Push 300 `int`s one at a time into an empty `std::vector<int>`: with doubling, list the capacities, count the reallocations after the first allocation and the total number of relocated elements; compare with the bound $\frac{g}{g-1}n$. (b) Call `max_load_factor(0.5)` on an empty `std::unordered_map<int,int>` and insert the keys $0,\dots,99$: state the exact rule that triggers a rehash, say which of {iterators, references to `m[0]`} survive a rehash, and use the rule to find the sizes at which rehashes occur when the observed bucket counts are $1,23,47,97,199,409$. (c) After `std::deque<int> d{5,6,7,8}; int* p = &d[2]; d.push_front(4); d.push_front(3); d.push_back(9);` is `p` still valid, and what does it point to? (d) Which of your answers are guaranteed by the standard and which are properties of libstdc++? (adapted from cppreference, Containers library "Iterator invalidation" and `std::unordered_map::insert`)
15. **(Challenge)** Batch late data. A sorted `vector` holds $n=100{,}000$ samples; $k=1000$ late samples with uniformly random timestamps must be merged in. (a) Using the `std::vector::insert` complexity (linear in the distance from the position to the end), estimate the total element moves of inserting them one by one with `lower_bound`. (b) Estimate the cost of: sort the $k$ late samples, append them, `std::inplace_merge`. (c) Measured with a counting element type (seed 42, g++ 11.4 `-O2`): report the two counts and their ratio. (d) For which regime is one-by-one insertion actually better, and what quantity would you measure first? (adapted from cppreference, `std::inplace_merge` Complexity and `std::vector::insert` Complexity)

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
  CHECK(s.append(0.5, 4) && s.append(1.5, 10) && s.append(2, 7) && s.append(5, 19));
  CHECK(s.size() == 4);
  // hand-computed interpolation: between (2,7) and (5,19) at t=3.5 -> 13; between (0.5,4) and (1.5,10) at t=1 -> 7
  CHECK(s.at(3.5).value() == 13.0);
  CHECK(std::fabs(s.at(1.0).value() - 7.0) < 1e-12);
  // exact timestamps and ends
  CHECK(s.at(0.5).value() == 4.0 && s.at(1.5).value() == 10.0 && s.at(5.0).value() == 19.0);
  CHECK(!s.at(0.4) && !s.at(5.1));
  // append rules
  CHECK(!s.append(5.0, 1.0) && !s.append(3.0, 1.0) && !s.append(NAN, 1.0) && s.size() == 4);
  // ranges (inclusive)
  CHECK(s.count_in(1.5, 2.0) == 2 && s.count_in(1.0, 4.9) == 2 && s.count_in(6, 7) == 0 && s.count_in(2, 1) == 0);
  CHECK(s.mean_in(0.5, 2.0).value() == 7.0 && !s.mean_in(2.5, 4.5));
  // erase-remove
  CHECK(s.drop_above(15.0) == 1 && s.size() == 3 && !s.at(5.0));
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

### Library track

Use only the standard library (`<map>`, `<chrono>`, `<random>`) for task 5 and 6. Paste this *after* your finished `TimeSeries` (it has its own `main`, so drop the one from the tests) and compile it separately with `g++ -std=c++17 -O2 -Wall -Wextra` (no sanitizers when timing).

```cpp
#include <cassert>
#include <chrono>
#include <iostream>
#include <map>
#include <random>

// Same interface on std::map, for the cross-check and the benchmark (task 5).
class MapSeries {
 public:
  bool append(double t, double v) {
    if (!std::isfinite(t) || (!m_.empty() && !(t > m_.rbegin()->first))) return false;
    m_.emplace_hint(m_.end(), t, v);
    return true;
  }
  std::optional<double> at(double t) const {
    auto it = m_.lower_bound(t);
    if (it == m_.end()) return std::nullopt;
    if (it->first == t) return it->second;
    if (it == m_.begin()) return std::nullopt;
    auto a = std::prev(it);
    return a->second + (it->second - a->second) * (t - a->first) / (it->first - a->first);
  }
 private:
  std::map<double, double> m_;
};

template <class S>
double ns_per_query(const S& s, const std::vector<double>& q, double& sink) {
  using clk = std::chrono::steady_clock;
  double best = 1e300;
  for (int rep = 0; rep < 5; ++rep) {                         // repeats: keep the best (least noisy)
    auto t0 = clk::now();
    for (double x : q) sink += s.at(x).value_or(0.0);         // consume results
    best = std::min(best, std::chrono::duration<double, std::nano>(clk::now() - t0).count() / q.size());
  }
  return best;
}

int main() {
  std::mt19937 g(1);
  for (std::size_t n : {1000u, 100000u, 1000000u}) {
    TimeSeries vs; MapSeries ms;
    for (std::size_t i = 0; i < n; ++i) { vs.append(0.01 * i, std::sin(0.01 * i)); ms.append(0.01 * i, std::sin(0.01 * i)); }
    std::uniform_real_distribution<double> u(0.0, 0.01 * (n - 1));
    std::vector<double> q(2000000); for (double& x : q) x = u(g);
    for (int i = 0; i < 1000; ++i) assert(std::fabs(vs.at(q[i]).value() - ms.at(q[i]).value()) < 1e-12);  // same answers
    double sink = 0;
    double a = ns_per_query(vs, q, sink), b = ns_per_query(ms, q, sink);
    std::cout << "N=" << n << "  vector " << a << " ns  map " << b << " ns  ratio " << b / a << "  check " << sink << "\n";
  }
}
```

On one test machine the output was ratios of about 1.5, 2.3 and 4.2 for $N=10^3, 10^5, 10^6$ (vector 64, 162, 248 ns per query; map 94, 374, 1032 ns); yours will differ, but the ratio should grow with $N$. The `assert` checks that both structures return the same interpolated values. Questions: why does the vector's time still grow with $N$? What happens to the ratio if the queries are sorted instead of random?

![Left: median of three runs of the time per query for a sorted vector and a map at N = 10^3, 10^5 and 10^6; right: the data size of 16 bytes per sample and 48 bytes per tree node against the L2 and L3 cache sizes](/lesson-figures/CPP05-5.svg)

*Figure: time per query is machine-dependent. Median of three runs of the program above on an Intel Core i5-12500H (L2 1.5 MiB per core, L3 18 MiB), g++ 11.4.0, `-O2`: vector 53, 104 and 180 ns, map 59, 208 and 691 ns for $N=10^3,10^5,10^6$. The gap opens when the tree (48 B per node, 48 MB at $N=10^6$) no longer fits in the caches while the vector (16 B per sample) is traversed with fewer and more predictable memory reads.*

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
3. Linear: 1,080,000 comparisons. Binary: $\lceil\log_2 1{,}080{,}001\rceil=21$, since $2^{20}=1{,}048{,}576<1{,}080{,}001\le2^{21}$. Ratio $\approx 51{,}400$.
4. Bug 1: if `it == v.begin()` (query before the first sample) `it - 1` is before the beginning. Bug 2: if `it == v.end()` (query after the last sample) `*it` dereferences `end()`. Also a division by zero cannot happen if timestamps are strictly increasing, but an exact hit with $t=t_b$ should return directly. Fix: check `it == end` first, then exact equality, then `it == begin`, and only then interpolate (see the reference `at`).
5. `erase(it)` invalidates `it` (and all later iterators), so `++it` on the next loop turn is undefined behavior; even when it appears to work it skips the element that slid into the erased slot. Fix 1: `for (auto it = v.begin(); it != v.end();) { if (it->v > 50) it = v.erase(it); else ++it; }`. Fix 2: `v.erase(std::remove_if(v.begin(), v.end(), [](const Sample& s){ return s.v > 50; }), v.end());` which is also $O(n)$ instead of $O(n^2)$.
6. Output `0 1`. `operator[]` default-constructs and inserts the missing key `"kp"`, so a typo in a parameter name silently becomes a gain of 0 and the map grows. Use `find`/`at` (which throws) for reads, and `[]` only when insertion is intended.
7. `std::sort` is $O(n\log n)$ (about $1001\cdot10\approx10^4$ comparisons), `nth_element` is expected $O(n)$ (a few thousand). The median of `{7,1,5,3,9}` is at index 2 and equals 5. After `nth_element` the elements before are all $\le5$ and the ones after all $\ge5$, in unspecified order; the vector is *not* sorted.
8. Control: `-O2` for all; one warm-up pass (page-in, branch predictors, caches); the same pre-generated random queries for each structure; accumulate results into a variable that is printed so the loop is not eliminated; several repeats with the median. Expected ordering for nearest-time queries: `vector` fastest, `map` slower (pointer chasing, cache misses); `unordered_map` cannot answer nearest-time queries at all, only exact keys, so comparing it is only valid for exact index lookups, where it is fast but answers a different question.
9. 1% of 1000 per second is 10 late inserts per second. A middle insertion shifts on average $n/2=50{,}000$ elements $\times16$ B $=800$ kB; 10 per second is 8 MB/s, trivial. A `map` is not justified; measure the real distribution of lateness (late samples are mostly near the end, so shifts are even smaller) and the query latency budget before changing anything.
10. Reallocations happen when the size reaches $c, gc, g^2c,\dots$ and each copies the current size, so the total is $c+gc+\dots+g^{k}c$ with $g^{k}c\le n$. The geometric sum is at most $n\cdot\frac{1}{1-1/g}=\frac{g}{g-1}n$. For $g=1.25$: $5n$; for $g=3$: $1.5n$. A very large $g$ wastes memory (up to $(g-1)/g$ of capacity is unused) and the allocator may be unable to find a block; typical values are 1.5 to 2.
11. A good answer has: a table with the three sizes; vector faster than map by a ratio that grows (in one run 1.0, 1.7, 3.6); explanation: the vector's binary search touches a few cache lines and prefetching works, whereas a tree visits nodes scattered over the heap; at $10^6$ elements the tree (about 48 B/node) exceeds the cache and each hop can be a cache miss; and a caveat about the machine and one run.

12. (a) Suppose the invariant holds at the top of an iteration with `it = first + step` and `comp(*it, value)` false. Then `*it` does not satisfy `p`, so the first non-`p` element is at or before `it`, i.e. in $[\text{first},\text{first}+\text{step}]$, and `count = step` restores the claim (the elements before `first` are unchanged and still satisfy `p`). At termination `count = 0`, so the answer lies in $[\text{first},\text{first}]$: it is `first` itself, the first element that is not less than `value` (or `last`). (b) One comparison per iteration and $\text{count}'\in\{\lfloor n/2\rfloor,\; n-\lfloor n/2\rfloor-1\}$; the second is at most the first, so the worst case follows $W(n)=1+W(\lfloor n/2\rfloor)$, $W(0)=0$. Writing $n$ in binary, each step drops the last bit, so $W(n)$ is the bit length of $n$: $\lfloor\log_2 n\rfloor+1$. Values: $W(1)=1$, $W(5000)=\lfloor12.29\rfloor+1=13$, $W(2^{16})=17$ (measured by exhaustive search over all targets: $n=5000$ gives best 12 and worst 13, $n=65536$ gives best 16 and worst 17). (c) Measured for $n\le40$: best equals worst exactly for $n=1,3,7,15,31$, that is $n=2^k-1$, since then both branches leave $2^{k-1}-1$ elements; the smallest $n>1$ is $3$. For $n=5000$ the best case is 12 and the worst 13. (d) $1\,900\,000\,000+2\,000\,000\,000=3\,900\,000\,000$ exceeds $2^{31}-1=2\,147\,483\,647$ and wraps to $3\,900\,000\,000-2^{32}=-394\,967\,296$, a negative index. Safe forms: `mid = lo + (hi - lo) / 2`, or halve a count as the standard loop does.
13. (a) Take $a=3$, $b=\text{NaN}$, $c=9$. `3 < NaN`, `NaN < 3`, `NaN < 9`, `9 < NaN` are all false, so $a\sim b$ and $b\sim c$ (equivalent), yet $3<9$ so $a\not\sim c$. Equivalence is required to be transitive, so the requirement fails. (b) Measured indices: $x=1\to0$, $x=3.5\to1$, $x=5\to2$, $x=7.5\to2$, $x=8.5\to2$, $x=10\to2$. The predicate $e<x$ along the vector is F F F F F for $x=1$, T F F F F for $x=3.5$ and T T F F F for $x=5$ and $x=7.5$: all partitioned, so the answer is correct by the definition "first element not less than $x$" (for $x=5$ and $x=7.5$ it is index 2, the NaN, although the number 7.5 at index 3 is what one probably wanted). For $x=8.5$ the predicate is T T F T F and for $x=10$ it is T T F T T: the range is not partitioned, the precondition is violated and the returned 2 is meaningless (for $x=10$ the position after all numbers, index 5, would be wanted). (c) Measured (libstdc++): $\{4,6,\text{NaN},8\}$ gives size 3 and $\{\text{NaN},4,6,8\}$ gives size 1; the exact numbers are implementation dependent because the behavior is undefined, which is the point. (d) `comp(a,b) = !isnan(a) && (isnan(b) || a < b)`. It is the lexicographic order on $(\text{isnan}(x),x)$ with `false < true`: on non-NaN values `<` is a strict total order and all NaNs form one equivalence class, and a lexicographic combination of strict weak orderings is a strict weak ordering. Measured result of `std::sort` on $\{8,\text{NaN},5,\text{NaN},6\}$: `5 6 8 nan nan`.
14. (a) Measured with libstdc++: capacities $1,2,4,8,\dots,512$ (10 allocations, so 9 reallocations after the first), relocated elements $1+2+4+\dots+256=511$. Bound for $g=2$: $\frac{g}{g-1}n=600$; the actual 511 is below it because the last block of 512 is not full. (b) Rule: an insertion that would make $\text{size}>\text{bucket\_count}\cdot\text{max\_load\_factor}$ triggers a rehash to a larger bucket count (a rehash takes place when the new number of elements is greater than the old `max_load_factor()*bucket_count()`, cppreference: `unordered_map::insert`). Iterators are all invalidated by a rehash while references and pointers to elements (`&m[0]`) stay valid (same page). With the factor 0.5: the first insertion makes the size 1 and $1>1\cdot0.5$, so the table grows to 23 buckets; then $12>23\cdot0.5=11.5$ gives 47, $24>47\cdot0.5=23.5$ gives 97, $49>97\cdot0.5=48.5$ gives 199 and $100>199\cdot0.5=99.5$ gives 409 (measured: rehashes at sizes 1, 12, 24, 49 and 100, final load factor $100/409\approx0.245$). The bucket counts are primes chosen by the library; the standard fixes only the rule. (c) Yes: `p` is still valid and points to `7` (`d[4]` after the three insertions). Growth at either end of a `deque` never moves elements; iterators are invalidated but references are not (measured: `p == &d[4]`). (d) Standard guarantees: the invalidation rules above (vector reallocation, rehash invalidates iterators but not references, deque end insertions keep references). Library-specific: the capacities $1,2,4,\dots$ (growth factor 2 in libstdc++; other libraries use other factors, e.g. 1.5) and the prime bucket counts.
15. (a) A random position in a vector of current size $m$ shifts on average $m/2$ elements, so about $k\cdot n/2=1000\cdot50{,}000=5\cdot10^7$ element moves (the average is $m/2$ with $m$ growing from $10^5$ to $1.01\cdot10^5$, and the measured value varies with the random draw). (b) Sorting $k$ items costs $O(k\log k)\approx1000\cdot10=10^4$ moves; appending is $k$ copies; `inplace_merge` performs exactly $N-1$ comparisons when it has a temporary buffer and $O(N\log N)$ otherwise, with $N=n+k=101{,}000$, and moves about $N$ elements, so roughly $10^5$ in total. (c) Measured with a move-counting element type: one-by-one `lower_bound` + `insert`: **49,671,028** element moves; sort + append + `inplace_merge`: **113,561** moves (10,612 in the sort); ratio $\approx437$. The first matches the $5\cdot10^7$ estimate. (d) One-by-one wins when $k$ is tiny (for $k=1$ the merge touches all $n$ elements anyway, while the insert touches $n/2$ on average), or when late samples are always near the end (the shift length is then the lateness, not $n$): measure the distribution of lateness, i.e. the distance of each insertion point from the end, before choosing. If the lateness is bounded by $L$ samples, inserting from the back costs $O(kL)$.

## Further reading

- [cppreference: Containers library](https://en.cppreference.com/w/cpp/container) - the complete container table with complexity guarantees and invalidation rules.
- [cppreference: Algorithms library](https://en.cppreference.com/w/cpp/algorithm) - every algorithm with preconditions, complexity and examples.
- [LearnCpp](https://www.learncpp.com/) - the chapters on containers, iterators and algorithms with quizzes.
- [cppreference: std::lower_bound](https://en.cppreference.com/w/cpp/algorithm/lower_bound), [Compare requirements](https://en.cppreference.com/w/cpp/named_req/Compare) and [`std::inplace_merge`](https://en.cppreference.com/w/cpp/algorithm/inplace_merge) - the partition precondition, strict weak ordering, and merge complexity used in the proofs.
- [cppreference: `std::unordered_map::insert`](https://en.cppreference.com/w/cpp/container/unordered_map/insert) - when rehashing invalidates iterators.
- cppreference pages used for the complexity and invalidation statements in the examples: [`std::vector::push_back`](https://en.cppreference.com/w/cpp/container/vector/push_back), [`std::vector::insert`](https://en.cppreference.com/w/cpp/container/vector/insert), [`std::remove`](https://en.cppreference.com/w/cpp/algorithm/remove), [`std::deque`](https://en.cppreference.com/w/cpp/container/deque), [`std::unordered_map`](https://en.cppreference.com/w/cpp/container/unordered_map) and [`std::map::lower_bound`](https://en.cppreference.com/w/cpp/container/map/lower_bound).

**More practice:** the quizzes on [LearnCpp: STL containers overview](https://www.learncpp.com/cpp-tutorial/stl-containers-overview/), [iterators overview](https://www.learncpp.com/cpp-tutorial/stl-iterators-overview/) and [algorithms overview](https://www.learncpp.com/cpp-tutorial/stl-algorithms-overview/) (answers shown on each page), and the runnable examples on cppreference for [`std::lower_bound`](https://en.cppreference.com/w/cpp/algorithm/lower_bound) and [`std::remove`/`remove_if`](https://en.cppreference.com/w/cpp/algorithm/remove) (modify them to predict outputs), plus the [iterator invalidation table](https://en.cppreference.com/w/cpp/container#Iterator_invalidation).