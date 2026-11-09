---
{
  "id": "cpp02-foundations",
  "module_id": "CPP02",
  "title": "Memory, references, and lifetime",
  "summary": "Explain who owns an object and how long a reference stays valid.",
  "estimated_minutes": 280,
  "prerequisites": [
    "CPP01"
  ],
  "source_refs": [
    {
      "title": "LearnCpp",
      "url": "https://www.learncpp.com/"
    },
    {
      "title": "C++ Core Guidelines (C.66, R.22-R.24, R.30-R.37)",
      "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"
    },
    {
      "title": "cppreference: std::vector (iterator invalidation)",
      "url": "https://en.cppreference.com/w/cpp/container/vector"
    },
    {
      "title": "cppreference: Reference initialization (lifetime of a temporary)",
      "url": "https://en.cppreference.com/w/cpp/language/reference_initialization"
    },
    {
      "title": "cppreference: std::shared_ptr",
      "url": "https://en.cppreference.com/w/cpp/memory/shared_ptr"
    },
    {
      "title": "cppreference: Range-based for loop (temporary range initializer)",
      "url": "https://en.cppreference.com/w/cpp/language/range-for"
    },
    {
      "title": "cppreference: Storage duration",
      "url": "https://en.cppreference.com/w/cpp/language/storage_duration"
    },
    {
      "title": "cppreference: Object (alignment, object representation)",
      "url": "https://en.cppreference.com/w/cpp/language/object"
    },
    {
      "title": "cppreference: sizeof operator",
      "url": "https://en.cppreference.com/w/cpp/language/sizeof"
    },
    {
      "title": "cppreference: offsetof",
      "url": "https://en.cppreference.com/w/cpp/types/offsetof"
    },
    {
      "title": "cppreference: std::unique_ptr",
      "url": "https://en.cppreference.com/w/cpp/memory/unique_ptr"
    },
    {
      "title": "cppreference: operator new (global replacements)",
      "url": "https://en.cppreference.com/w/cpp/memory/new/operator_new"
    },
    {
      "title": "C++ working draft: [basic.stc], [basic.align], [class.temporary]",
      "url": "https://eel.is/c++draft/"
    }
  ],
  "objectives": [
    "Distinguish values, addresses, pointers, and references.",
    "Identify dangling references and invalidated storage.",
    "Use RAII and standard containers for ownership."
  ],
  "core_theory": [
    "Memory, references, and lifetime"
  ],
  "labs": [
    "Draw lifetimes for a value, reference, and unique_ptr across nested scopes. Write a safe function returning a vector by value. In a separate intentional experiment, use a sanitizer to identify a dangling reference; do not run undefined behavior in robot control code."
  ],
  "assessment_refs": [
    "CPP02-diagnostic-v1"
  ],
  "review_prompts": [
    "A callback stores a pointer to a temporary sensor buffer. Describe a failure scenario and redesign the ownership contract so the callback can safely outlive the producer call."
  ],
  "extension_refs": [
    "https://www.learncpp.com/"
  ]
}
---

## Why this matters

Explain who owns an object and how long a reference stays valid. This lesson develops the core calculation before asking you to apply it in a new setting. Start with the diagnostic if you think you already know it; prior tool use is not evidence of understanding.

## Intuition

A pointer is a value that can refer to an object in memory; it is not ownership by itself. A reference is an alias. Correctness depends on whether the object still exists and whether an operation moved its storage. Drawing object lifetimes is often more useful than staring at addresses.

Think of memory as numbered lockers and of an object as the contents of one or more lockers. A *value* is the contents themselves: copying a value photocopies the contents into new lockers, and from then on the two copies are independent. A *pointer* is a slip of paper with a locker number written on it; copying the slip gives two slips that name the same locker, and nothing in the slip says whether the locker is still rented. A *reference* is a second label painted on the same locker: it cannot be blank and cannot be moved to another locker, but, like the slip, it says nothing about how long the locker stays rented. Who rents the locker, and when the rental ends, is the *ownership* and *lifetime* of the object, and it is a property of the program's structure (scopes, containers, smart pointers), not of the numbers in the slips.

A first case. Predict the output of the program below before reading on; it was compiled with g++ 11.4.0 (`-std=c++20 -Wall -Wextra`) without warnings.

```cpp
#include <iostream>

int main() {
    int x = 10;
    int y = x;
    int* p = &x;
    int& r = x;
    y = 20;
    *p = 30;
    r += 1;
    std::cout << "x=" << x << " y=" << y << " *p=" << *p << " r=" << r << '\n';
    std::cout << "&r == &x: " << (&r == &x) << ", &y == &x: " << (&y == &x) << '\n';
    std::cout << "sizeof(x)=" << sizeof(x) << " sizeof(p)=" << sizeof(p) << " sizeof(r)=" << sizeof(r) << '\n';
}
```

![A timeline of a vector reallocation: a pointer to element 0 of the old block of capacity 4 dangles after the fifth push_back moves the elements to a block of capacity 8, while a unique_ptr transfers a single ownership arrow.](/lesson-figures/CPP02.svg)

*Figure: two pictures of the same discipline. On the left a pointer into a vector survives until the vector reallocates; on the right ownership of one object is handed from `a` to `b`, so that exactly one name is responsible for destroying it.*

**Check the prediction.** The output is `x=31 y=20 *p=31 r=31`, then `&r == &x: 1, &y == &x: 0`, then `sizeof(x)=4 sizeof(p)=8 sizeof(r)=4`. `y` is a value copy, so assigning 20 to it never touches `x`; `p` and `r` both name the object `x`, so `*p = 30` and `r += 1` are two writes to one object (10, then 30, then 31). The reference has the same address as `x`, a copy has its own. The last number needs care: `sizeof(r)` reports the size of the referenced object (4), not of the reference itself, which the language does not specify further, while a pointer is an ordinary 8-byte object on this 64-bit machine.

The common wrong intuition is "a pointer or reference makes the object stay alive". It never does: only the owner decides, and the owner is a scope, a container or a smart pointer. The figure shows the two ways a handle goes bad that the rest of the lesson analyses: the storage is *moved* (a vector reallocates, the handle names a locker that has been emptied) or the object is *destroyed* (the scope ends, the owner is reset). A second wrong intuition is that a dangling handle announces itself: the old locker often still holds plausible numbers for a while, so a program can run correctly a thousand times and fail on the thousand-and-first, which is why this lesson relies on rules and on sanitizers rather than on observation.

## Theory and derivation

An automatic local object is destroyed when its scope ends. Returning a pointer or reference to it leaves a dangling handle. Copying a value creates another object with its own lifetime; copying a pointer only creates another address value.

`std::vector` owns contiguous element storage. Growing beyond capacity can allocate a new block, move elements, and invalidate pointers, references, and iterators to the old storage. A vector object can remain alive while a pointer to one of its former elements becomes invalid. Do not rely on observed address stability from one run.

RAII associates resource release with object destruction. `std::unique_ptr<T>` owns one dynamically allocated object and cannot be copied; moving transfers ownership. `std::shared_ptr<T>` shares ownership with a reference count and additional cost. Neither automatically makes access thread-safe. Prefer values and containers until dynamic ownership is actually needed.

To inspect suspected memory errors, compile your own code with `-fsanitize=address,undefined -g`. Sanitizers detect many executed invalid operations; passing one run is not proof that every lifetime is correct.

### Storage: static, automatic and dynamic

The standard distinguishes four storage durations: static, thread, automatic and dynamic ([basic.stc.general]; cppreference, "Storage duration"). Objects at namespace scope and `static` locals have *static* storage: they exist from program start or first use until the program ends. Local variables of a block have *automatic* storage: they are created when execution reaches the definition and destroyed at the end of the block ([basic.stc.auto]); implementations place them on the call stack, one frame per active function call, so creating and destroying them costs a pointer adjustment. *Dynamic* storage is obtained with `new` or an allocator and lasts until it is explicitly released ([basic.stc.dynamic]); implementations take it from the heap, which costs a search for a free block and a bookkeeping header, and a thread-safe allocator costs more. The practical consequences: automatic storage is fast but its lifetime is tied to the scope and its size to the frame (a megabyte-sized local array risks a stack overflow on a default 8 MB stack), while dynamic storage can outlive the function and be sized at run time but needs an owner that releases it exactly once.

A standard container is a small automatic object that owns a dynamic block. A `std::vector<int>` object is three pointers (24 bytes on this 64-bit platform) living wherever the vector variable lives, and its elements live in a separate heap block. Moving or destroying the vector object acts on the 24 bytes; the block is released by the vector's destructor. This split between a *handle* and a *payload* explains most of the lesson: a pointer to the handle stays valid as long as the vector variable does, and a pointer to the payload does not.

**Example.** The global `operator new` can be replaced (cppreference, "operator new", section "Global replacements"), here only to count calls. Compiled with g++ 11.4.0 (`-std=c++20 -Wall -Wextra`):

```cpp
#include <cstdlib>
#include <iostream>
#include <memory>
#include <new>
#include <vector>

static int g_allocs = 0;
static std::size_t g_bytes = 0;

void* operator new(std::size_t n) {
    ++g_allocs;
    g_bytes += n;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

static void report(const char* what, int a0, std::size_t b0) {
    std::cout << what << ": " << g_allocs - a0 << " allocation(s), " << g_bytes - b0 << " bytes\n";
}

int main() {
    int a0 = g_allocs; std::size_t b0 = g_bytes;
    { int local[1000]; local[0] = 1; (void)local; }
    report("int local[1000]", a0, b0);

    a0 = g_allocs; b0 = g_bytes;
    { std::vector<int> v(1000); std::cout << "sizeof(v) = " << sizeof(v) << '\n'; }
    report("std::vector<int> v(1000)", a0, b0);

    a0 = g_allocs; b0 = g_bytes;
    { auto p = std::make_unique<int>(5); std::cout << "sizeof(p) = " << sizeof(p) << '\n'; }
    report("std::make_unique<int>(5)", a0, b0);
}
```

Output: `int local[1000]: 0 allocation(s), 0 bytes`; `sizeof(v) = 24`; `std::vector<int> v(1000): 1 allocation(s), 4000 bytes`; `sizeof(p) = 8`; `std::make_unique<int>(5): 1 allocation(s), 4 bytes`. The 4000 bytes are $1000\times4$; the 24-byte handle `v` itself is automatic and was not counted.

![Three storage areas side by side: static, the stack with frames, and the heap with the 4000-byte and 4-byte blocks, each handle on the stack pointing to its block, and the time at which each object ends.](/lesson-figures/CPP02-2.svg)

*Figure: the handle is on the stack and dies with its block; the payload is on the heap and dies when the owner's destructor releases it. The sizes are those of the example above.*

### Object layout: size, alignment and padding

Every object type has an *alignment requirement*, a power of two that says at which byte addresses objects of that type may be placed (cppreference, "Object", section "Alignment"; [basic.align]). For the common fundamental types the alignment equals the size (`int` 4, `double` 8 on this platform). The members of a class are laid out in declaration order, each at the next offset that satisfies its alignment, and the compiler inserts *padding* bytes to achieve this. The alignment of the class is the largest alignment of its members, and its size is rounded up to a multiple of that alignment, so that every element of an array of the class is itself aligned (cppreference, `sizeof`: "including any additional padding required to place such object in an array"). The rule gives a closed form. For members $m_1,\dots,m_k$ with sizes $s_i$ and alignments $a_i$, offsets are $o_1=0$ and $o_i=\lceil (o_{i-1}+s_{i-1})/a_i\rceil\,a_i$, the alignment is $A=\max a_i$ and $\mathrm{sizeof}=\lceil (o_k+s_k)/A\rceil\,A$. Different declaration orders of the same members can therefore give different sizes; putting larger-alignment members first usually removes the padding between them.

Layout matters for three reasons in robotics code: memory traffic (a padded struct in an array of $10^6$ points wastes cache and bandwidth), binary interfaces (a struct sent over a wire or a file must have a fixed, documented layout, not "whatever the compiler did"), and `memcpy`-style code that assumes there are no gaps. `offsetof` gives the offset of a member of a standard-layout class (cppreference, "offsetof").

**Example.** Three members of sizes 1, 4 and 1 bytes (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <cstddef>
#include <iostream>

struct T1 { char a; int b; char c; };
struct T2 { int b; char a; char c; };

int main() {
    std::cout << "T1 size " << sizeof(T1) << " align " << alignof(T1) << " offsets "
              << offsetof(T1, a) << ' ' << offsetof(T1, b) << ' ' << offsetof(T1, c) << '\n';
    std::cout << "T2 size " << sizeof(T2) << " align " << alignof(T2) << " offsets "
              << offsetof(T2, b) << ' ' << offsetof(T2, a) << ' ' << offsetof(T2, c) << '\n';
}
```

Output: `T1 size 12 align 4 offsets 0 4 8` and `T2 size 8 align 4 offsets 0 4 5`. By the formula: `T1` has $o_a=0$, $o_b=\lceil1/4\rceil\cdot4=4$, $o_c=8$ and $\lceil9/4\rceil\cdot4=12$, so 6 of its 12 bytes are padding; `T2` has $o_b=0$, $o_a=4$, $o_c=5$ and $\lceil6/4\rceil\cdot4=8$, with 2 padding bytes.

![Byte maps of the structs T1 and T2 with 4-byte alignment marks, padding drawn hatched, sizes 12 and 8.](/lesson-figures/CPP02-3.svg)

*Figure: the same three members, two declaration orders. Grey blocks are padding inserted to satisfy the 4-byte alignment of `int` and to round the size up to a multiple of 4.*

```explore
{
  "title": "Struct size as the alignment of the middle member grows",
  "title_vi": "Kích thước struct khi alignment của thành viên giữa tăng",
  "prompt": "Predict first: for a struct { char a; T b; char c; } how does sizeof grow when the alignment A of T doubles, and what does reordering to { T b; char a; char c; } save? Then move the slider.",
  "prompt_vi": "Dự đoán trước: với struct { char a; T b; char c; } thì sizeof tăng thế nào khi alignment A của T tăng gấp đôi, và việc sắp xếp lại thành { T b; char a; char c; } tiết kiệm được bao nhiêu? Sau đó kéo thanh trượt.",
  "params": [
    { "name": "k", "label": "log2 of the alignment of T (A = 2^k; T has size A)", "label_vi": "log2 của alignment của T (A = 2^k; T có kích thước A)", "min": 0, "max": 4, "step": 1, "value": 2, "unit": "" }
  ],
  "let": [
    { "name": "A", "expr": "2^k" },
    { "name": "ob", "expr": "A" },
    { "name": "s1", "expr": "ceil((2*A + 1)/A)*A" },
    { "name": "s2", "expr": "ceil((A + 2)/A)*A" }
  ],
  "scene": {
    "xmin": -1, "xmax": 50, "ymin": 0, "ymax": 4,
    "items": [
      { "type": "label", "at": [0, 3.5], "text": "order a, b, c", "text_vi": "thứ tự a, b, c", "color": "grey" },
      { "type": "segment", "from": [0, 3], "to": [1, 3], "color": "blue", "width": 12 },
      { "type": "segment", "from": [1, 3], "to": ["ob", 3], "color": "grey", "width": 12, "dash": true },
      { "type": "segment", "from": ["ob", 3], "to": ["ob + A", 3], "color": "orange", "width": 12 },
      { "type": "segment", "from": ["ob + A", 3], "to": ["ob + A + 1", 3], "color": "blue", "width": 12 },
      { "type": "segment", "from": ["ob + A + 1", 3], "to": ["s1", 3], "color": "grey", "width": 12, "dash": true },
      { "type": "label", "at": [0, 1.5], "text": "order b, a, c", "text_vi": "thứ tự b, a, c", "color": "grey" },
      { "type": "segment", "from": [0, 1], "to": ["A", 1], "color": "orange", "width": 12 },
      { "type": "segment", "from": ["A", 1], "to": ["A + 1", 1], "color": "blue", "width": 12 },
      { "type": "segment", "from": ["A + 1", 1], "to": ["A + 2", 1], "color": "blue", "width": 12 },
      { "type": "segment", "from": ["A + 2", 1], "to": ["s2", 1], "color": "grey", "width": 12, "dash": true }
    ]
  },
  "readouts": [
    { "label": "alignment A of T", "label_vi": "alignment A của T", "expr": "A", "unit": "B", "digits": 0 },
    { "label": "sizeof, order a, b, c", "label_vi": "sizeof, thứ tự a, b, c", "expr": "s1", "unit": "B", "digits": 0 },
    { "label": "sizeof, order b, a, c", "label_vi": "sizeof, thứ tự b, a, c", "expr": "s2", "unit": "B", "digits": 0 },
    { "label": "bytes saved by reordering", "label_vi": "số byte tiết kiệm khi sắp xếp lại", "expr": "s1 - s2", "unit": "B", "digits": 0 }
  ]
}
```

*Blue is a `char`, orange is `T`, grey dashed is padding. The first order needs $3A$ bytes whenever $A\ge2$, the second $2A$; for $A=1$ there is nothing to pad.* Predict-first answer: both sizes grow in proportion to $A$, and the saving is $A$ bytes (4 bytes for `int`, 8 for `double`, 16 for a 16-byte-aligned type).

### Values, pointers and references

A *value* of a class or built-in type is copied by copy-initialization: the copy is a new object with its own storage and lifetime, and later changes to either do not affect the other. A *pointer* `T*` is itself an object that holds an address (or the null value `nullptr`); copying it copies the address, so both pointers refer to the same object. A *reference* `T&` is an alias fixed at initialization: it must be bound to an existing object, cannot be null and cannot be reseated (cppreference, "Reference declaration"). In generated code references are usually implemented as pointers, but the language guarantees less: no null, no arithmetic, no array of references.

The lesson's key observation is that none of these three says anything about lifetime. A pointer or reference is valid exactly when the object it names is within its lifetime and, for pointers into a container, the element has not been moved; the Core Guidelines state the first half as "don't dereference an invalid pointer" (ES.65) and "never return a pointer or reference to a local object" (F.43). Choosing among them is a design decision: pass by value when copying is cheap or the callee needs its own copy; by `const&` to read without copying (F.16); by pointer when "no object" is a legitimate state (R.2 reserves raw pointers for individual objects that are *not* owned); and never use a raw `T*` to express ownership (R.3).

**Example.** Two copies of a vector and two copies of a pointer (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> a{1, 2, 3};
    std::vector<int> b = a;
    int* p = &a[0];
    int* q = p;
    b[0] = 9;
    *q = 5;
    std::cout << "a[0]=" << a[0] << " b[0]=" << b[0] << '\n';
    std::cout << "p == q: " << (p == q) << ", &a[0] == &b[0]: " << (&a[0] == &b[0]) << '\n';
}
```

Output: `a[0]=5 b[0]=9`, then `p == q: 1, &a[0] == &b[0]: 0`. Copying the vector `a` into `b` copied the three elements into a new heap block, so writing `9` to `b[0]` left `a` alone; copying the pointer `p` into `q` copied only an address, so writing `5` through `q` changed `a[0]`.

### Ownership, RAII and moves

*Ownership* answers "who releases this object?". RAII (resource acquisition is initialization) makes the answer structural: an object that acquires a resource in its constructor releases it in its destructor, so the release happens on every exit path, including early `return` and exceptions (Core Guidelines R.1, R.5). `std::unique_ptr<T>` is the smallest such owner: it holds one pointer (8 bytes here), deletes the object in its destructor and cannot be copied, because two owners would release twice. Ownership is transferred by a *move*: after `auto b = std::move(a);` the object belongs to `b` and `a` holds `nullptr` (cppreference, `std::unique_ptr`). A move of a `unique_ptr` copies one pointer and nulls the source; it does not touch the object, which is why a pointer to the object stays valid across the move even though the owner changed.

The Core Guidelines turn this into rules: do not call `new` and `delete` explicitly (R.11), represent ownership with `unique_ptr` or `shared_ptr` (R.20), prefer `unique_ptr` unless ownership is really shared (R.21), and create them with `make_unique` and `make_shared` (R.22, R.23). A function that takes a `unique_ptr` by value is a *sink*: it advertises that it takes ownership; a function that merely uses the object takes `T&` or `T*` (R.30).

**Example.** Moves between owners, with a type that prints its construction and destruction (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <iostream>
#include <memory>
#include <utility>

struct Probe {
    int id;
    explicit Probe(int i) : id(i) { std::cout << "make " << id << '\n'; }
    ~Probe() { std::cout << "drop " << id << '\n'; }
};

std::unique_ptr<Probe> pass_on(std::unique_ptr<Probe> p) { return p; }

int main() {
    auto a = std::make_unique<Probe>(1);
    auto b = std::make_unique<Probe>(2);
    auto c = pass_on(std::move(a));
    std::cout << "a empty: " << (a == nullptr) << ", c->id = " << c->id << '\n';
    b = std::move(c);
    std::cout << "after b = move(c): b->id = " << b->id << '\n';
}
```

The output is `make 1`, `make 2`, `a empty: 1, c->id = 1`, `drop 2`, `after b = move(c): b->id = 1`, `drop 1`. Passing `a` through `pass_on` moved ownership twice without creating or destroying a `Probe`. The assignment `b = std::move(c)` had to release what `b` owned before taking over, so object 2 was destroyed at that line; object 1 is destroyed once, when `b` goes out of scope at the end of `main`.

### Vector growth, invalidation and the cost of moving elements

The lesson says that growing past capacity can invalidate pointers. The precise rules are in the reference table "Iterator invalidation" of `std::vector` (cppreference): `push_back` and `emplace_back` invalidate *all* iterators, pointers and references if the capacity changed, and otherwise only `end()`; `insert` invalidates everything if the capacity changed and otherwise everything at or after the insertion point; `erase` invalidates the erased elements and everything after them; `reserve` invalidates everything if it changed the capacity and nothing otherwise. A reference to element `i` is therefore safe across `push_back` only if you know `size() < capacity()` beforehand, which is a precondition you should write down or enforce with `reserve`.

Why do implementations grow geometrically? Suppose capacity multiplies by a factor $g>1$ on each reallocation, and a reallocation at size $c$ moves $c$ elements. Pushing $n$ elements triggers reallocations at sizes $1,g,g^2,\dots,g^{m-1}$ with $g^{m-1}<n$, so the total number of element moves is at most
$$\sum_{i=0}^{m-1}g^i\;<\;n\sum_{k\ge0}g^{-k}\;=\;\frac{g}{g-1}\,n .$$
For $g=2$ that is below $2n$ moves in total, i.e. amortised $O(1)$ per push; for $g=1.5$ it is below $3n$. A constant increment, by contrast, would cost $\Theta(n^2)$ moves.

Whether those moves are *moves* or *copies* depends on the element type. `push_back` has the strong exception guarantee (cppreference, `std::vector::push_back`): if allocation or an element operation throws, the vector must be unchanged. To keep that promise while relocating, the implementation uses `std::move_if_noexcept`, which yields an rvalue only if the move constructor is `noexcept` or the type cannot be copied (cppreference, `std::move_if_noexcept`). A type whose move constructor can throw but which is copyable is therefore *copied* on every reallocation. This is the performance reason behind "Make move operations `noexcept`" (C++ Core Guidelines, C.66).

**Example.** A vector is given capacity for 4 elements, a pointer to its first element is stored, and five elements are pushed (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    v.reserve(4);
    int* p = v.data();
    for (int i = 0; i < 5; ++i) {
        v.push_back(i);
        std::cout << "size " << v.size() << " capacity " << v.capacity()
                  << " p still data(): " << (p == v.data()) << '\n';
    }
}
```

The first four lines show capacity 4 and `p still data(): 1`; the fifth shows `size 5 capacity 8 p still data(): 0`. The first four pushes keep $\mathrm{size}\le\mathrm{capacity}$, so nothing moves and `p` stays valid; the fifth push needs a block of 8, the four elements are relocated, and `p` names a block that has been freed. The test `p == v.data()` is only a diagnostic here: after a reallocation the two can compare equal by accident when the allocator reuses an address (Case 2 below shows exactly that), and `p` is invalid anyway.

### Temporaries and lifetime extension

A reference is only as good as the object it names. For temporaries, the language has exactly one rescue rule (cppreference, "Reference initialization", section "Lifetime of a temporary"): when a reference is *bound directly* to a temporary (a prvalue, or a data member or array element selected from one), the temporary lives as long as the reference. `const std::string& r = make();` is therefore valid. The exceptions are the heart of the matter:

- a temporary bound to a reference *parameter* lives only until the end of the full expression containing the call; if the function returns that reference, the result dangles after the semicolon (`const auto& r = id(make());`);
- a temporary bound in a `return` statement is destroyed at the end of the return expression;
- extension is not transitive: a second reference initialised from the first does not extend anything, and a function call in between breaks the chain;
- a reference member of an aggregate extends the temporary when brace-initialised (`A a{make()}`), but not when initialised with parentheses (`A a(make())`, valid since C++20).

Range-based `for` is the classic trap: `for (auto x : f().items())` binds the range to the *result of* `items()`, a reference into a temporary that is destroyed before the loop starts if `items()` returns a reference. A view type such as `std::string_view` has the same property as a reference: `std::string_view sv = make();` leaves `sv` pointing into a destroyed string. In all these cases the compiler accepts the code, and only a sanitizer run that executes the line reports it.

**Example.** A type that announces its destruction shows when a temporary dies (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <iostream>
#include <string>

struct Noisy {
    std::string name;
    explicit Noisy(std::string n) : name(std::move(n)) { std::cout << "make " << name << '\n'; }
    ~Noisy() { std::cout << "drop " << name << '\n'; }
};
Noisy make(const char* n) { return Noisy(n); }
const Noisy& id(const Noisy& x) { return x; }

int main() {
    const Noisy& r = make("A");
    std::cout << "after A\n";
    const Noisy& s = id(make("B"));
    std::cout << "after B, s refers to a dead object\n";
    (void)r; (void)s;
}
```

Output: `make A`, `after A`, `make B`, `drop B`, `after B, s refers to a dead object`, `drop A`. `A` is bound directly to `r`, so it lives until `main` ends; `B` is bound to the parameter of `id`, so it is destroyed at the semicolon of that statement, before the next line runs, and `s` already dangles at that line. The compiler issued no warning, and any use of `s` would be undefined behaviour.

### Reference counts, `weak_ptr`, and who may call what

A `shared_ptr` points to a *control block* that holds, among other things, the number of shared owners and the number of `weak_ptr`s. When the shared-owner count reaches zero the managed object is destroyed, but the control block is not deallocated until the `weak_ptr` count reaches zero as well (cppreference, `std::shared_ptr`). With `std::make_shared`, the object and the control block live in a single allocation (the benefit named in R.22), so the *memory* of an expired object is released only when the last `weak_ptr` is gone, although its destructor has already run. `weak_ptr::lock()` returns a `shared_ptr` that is empty if the object has expired, so it is the safe way to observe an object you do not own. This also explains the cycle of Exercise 7: with `a->peer = b; b->peer = a;` the counts are two each, so after the outside handles are dropped each node is kept alive by the other (the C++ Core Guidelines state the rule as "use `std::weak_ptr` to break cycles of `shared_ptr`s", R.24). The aliasing constructor `shared_ptr<int>(owner, &owner->field)` shares the owner's control block, so it keeps the *whole* owner alive while pointing at a member.

Counts say who keeps the object alive; they say nothing about whether a *raw reference you already hold* is safe. The Core Guidelines isolate this in R.37: do not pass a pointer or reference obtained from an aliased smart pointer, because anything downstream may reset that pointer and destroy the object while you still use it. The fix is to take a local copy ("pin") at the top of the call tree: `auto pin = g_p; f(*pin);`. The parameter rules R.32 to R.36 then say what a signature promises: `unique_ptr<T>` by value takes ownership, `unique_ptr<T>&` may reseat, `shared_ptr<T>` by value shares ownership, `const shared_ptr<T>&` may retain a count, and a function that only uses the object should take `T&` or `T*` (R.30).

**Example.** The strong and weak counts of one shared integer (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <iostream>
#include <memory>

int main() {
    auto a = std::make_shared<int>(42);
    std::weak_ptr<int> w = a;
    auto b = a;
    std::cout << "use_count " << a.use_count() << ", expired " << w.expired() << '\n';
    a.reset();
    std::cout << "use_count " << b.use_count() << ", expired " << w.expired() << '\n';
    b.reset();
    std::cout << "use_count " << w.use_count() << ", expired " << w.expired()
              << ", lock empty " << (w.lock() == nullptr) << '\n';
}
```

Output: `use_count 2, expired 0`, then `use_count 1, expired 0`, then `use_count 0, expired 1, lock empty 1`. Two `shared_ptr`s own the integer (count 2); resetting one leaves count 1 and the object alive; resetting the last drops the count to 0, destroys the integer, and the `weak_ptr` observes the expiry and returns an empty `shared_ptr` from `lock()` instead of a dangling pointer.

## Worked example

### Case 1: a reference to a destroyed local

**Problem.** A function `const int& bad() { int x = 3; return x; }` is called as `const int& r = bad();` and then `r` is printed. Its sibling `int good() { int x = 3; return x; }` returns by value. Explain what each caller holds after the call and what a compiler and a sanitizer report.

**Solution.**

1. *Find the storage duration of `x`.* It is a block-scope variable, so it has automatic storage duration and is destroyed when the function body ends ([basic.stc.auto]).
2. *Trace `good`.* `return x;` copies the value 3 into the return object, a new `int` owned by the caller's expression; destroying `x` afterwards does not matter. The caller holds the value 3.
3. *Trace `bad`.* The return type is a reference, so `return x;` binds the result to `x` itself, and no copy is made. When the body ends, `x` is destroyed, so the reference `r` in the caller names an object whose lifetime has ended: a dangling reference (cppreference, "Reference declaration", section "Dangling references"; Core Guidelines F.43).
4. *Compile.* With g++ 11.4.0 and `-std=c++20 -Wall -Wextra -g` the compiler emits `warning: reference to local variable 'x' returned [-Wreturn-local-addr]` for `bad`. At run time the unoptimised program exited with status 139 (SIGSEGV): GCC 11 compiles such a return as a null reference. With `-fsanitize=address,undefined` the report is `runtime error: reference binding to null pointer of type 'const int'` followed by `AddressSanitizer: SEGV on unknown address 0x000000000000` at the line that prints `r`. The behaviour is undefined, so another compiler or optimisation level may print 3 instead, or garbage.
5. *Run `good`.* The program that only calls `good()` and prints the result (g++ 11.4.0, `-std=c++20 -Wall -Wextra`) prints `3` and produces no warning.

**Check.** The warning is the compiler's static check that the returned address is a local's; the sanitizer is the dynamic check. The two agree. An independent argument is the object count: after `good` returns there are zero `x` objects and one `int` value in the caller; after `bad` returns there are zero `x` objects and a reference to none.

**Takeaway.** Returning by value is always safe for a local; returning a reference is safe only when the referent outlives the call, and "it printed 3 once" is no evidence.

### Case 2: nine pushes into a fresh vector

**Problem.** A `std::vector<int> v` starts empty. After the first `push_back` a pointer `int* p = v.data();` is stored. Then eight more elements are pushed, one by one. With libstdc++ (growth factor 2), list the capacity after each push, which pushes allocate a new block, how many element relocations happen in total, and when `p` is valid. Compare with the bound $\frac{g}{g-1}n$ of the theory.

**Solution.**

1. *Capacity rule.* A push with $\mathrm{size}<\mathrm{capacity}$ stores the element in place; otherwise the vector allocates a block of $g\cdot\mathrm{capacity}$ (here $g=2$; the first allocation has capacity 1), relocates its $\mathrm{size}$ elements and releases the old block.
2. *Trace the pushes.* Push 1: capacity 1 (allocation). Push 2: size 1 equals capacity 1, so a new block of 2 is allocated and 1 element moves. Push 3: size 2 equals capacity 2, new block of 4, 2 elements move. Push 4: size 3 < 4, in place. Push 5: size 4 equals capacity, new block of 8, 4 elements move. Pushes 6, 7, 8: in place. Push 9: size 8 equals capacity, new block of 16, 8 elements move.
3. *Count.* Allocations at pushes 1, 2, 3, 5, 9: **5** allocations, capacities $1,2,4,8,16$. Relocations: $1+2+4+8=15$.
4. *Compare with the bound.* The bound is $\frac{g}{g-1}n=\frac{2}{1}\cdot9=18$ and $15<18$, as it must be.
5. *Validity of `p`.* The pointer was taken after push 1, from the block of capacity 1. Pushes 2, 3, 5 and 9 each replace the block, so `p` is invalid from push 2 onwards; it is *not* revalidated by later pushes that happen not to move anything.
6. *Run it.* The program below prints, for each push, the capacity, whether a reallocation happened and the value of `p == v.data()` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    v.push_back(0);
    int* p = v.data();
    std::size_t moves = 0;
    std::size_t allocs = 0;
    std::size_t cap = v.capacity();
    std::cout << "push 1: capacity " << cap << '\n';
    ++allocs;
    for (int i = 1; i < 9; ++i) {
        std::size_t old_size = v.size();
        v.push_back(i);
        bool moved = v.capacity() != cap;
        if (moved) { ++allocs; moves += old_size; cap = v.capacity(); }
        std::cout << "push " << i + 1 << ": capacity " << v.capacity()
                  << (moved ? ", reallocated" : "") << ", p == data(): " << (p == v.data()) << '\n';
    }
    std::cout << "allocations " << allocs << ", elements moved " << moves << '\n';
}
```

Output: `push 1: capacity 1`; `push 2: capacity 2, reallocated, p == data(): 0`; `push 3: capacity 4, reallocated, p == data(): 1`; `push 4: capacity 4, p == data(): 1`; `push 5: capacity 8, reallocated, p == data(): 0`; pushes 6 to 8 with `capacity 8` and `0`; `push 9: capacity 16, reallocated, p == data(): 0`; and `allocations 5, elements moved 15`.

![A timeline over nine pushes: capacity steps 1, 2, 4, 8, 16 drawn against the push number, reallocation pushes marked, the interval in which the pointer p still names a live block, and the moves 1, 2, 4, 8.](/lesson-figures/CPP02-4.svg)

*Figure: the capacity staircase of Case 2. The pointer `p` is valid only on push 1; the coincidence at push 3 (`p == data()` true) is the allocator reusing the freed block, not validity.*

**Check.** The counts match the closed form $\sum_{i<4}2^i=2^4-1=15$ for four reallocations after the first allocation, and $15<18$. The surprising line is push 3, where `p == data()` printed 1 although the block of capacity 1 had been released at push 2: the allocator handed the same address back for the new block. A pointer comparison therefore cannot be used to test validity; the standard says all pointers into the old block are invalid after any reallocation (cppreference, `std::vector`, "Iterator invalidation"), whatever their value.

**Takeaway.** Capacity doubling gives few allocations (5 for 9 elements) and fewer than $2n$ relocations, but every one of them invalidates every pointer, so a stored pointer needs `reserve` (and a size guarantee) or must be replaced by an index.

### Case 3: reordering members of a struct

**Problem.** A telemetry record has the members `char flag; double stamp; char kind; int count;`. Compute its `sizeof` and member offsets with the layout rule, then find a declaration order with a smaller size, and confirm both by compiling.

**Solution.**

1. *Sizes and alignments.* `char` 1/1, `double` 8/8, `int` 4/4 (size/alignment in bytes on this platform). The record's alignment is $A=\max(1,8,1,4)=8$.
2. *Offsets in the given order.* $o_{\text{flag}}=0$; $o_{\text{stamp}}=\lceil1/8\rceil\cdot8=8$; $o_{\text{kind}}=8+8=16$; $o_{\text{count}}=\lceil17/4\rceil\cdot4=20$. The end of the last member is $20+4=24$, which is already a multiple of 8, so $\mathrm{sizeof}=24$. Padding: 7 bytes after `flag`, 3 after `kind`, none at the end: 10 bytes.
3. *Reorder by decreasing alignment.* `double stamp; int count; char flag; char kind;` gives $o=0,8,12,13$; the end is 14, rounded up to a multiple of 8 gives $\mathrm{sizeof}=16$ with 2 padding bytes after `kind` (the tail padding).
4. *Saving.* $24-16=8$ bytes per record, a third; for an array of $10^6$ records that is 8 MB.
5. *Compile.* Output of the program below (g++ 11.4.0, `-std=c++20 -Wall -Wextra`): `S1 size 24 align 8 offsets 0 8 16 20` and `S2 size 16 align 8 offsets 0 8 12 13`.

```cpp
#include <cstddef>
#include <iostream>

struct S1 { char a; double b; char c; int d; };
struct S2 { double b; int d; char a; char c; };

int main() {
    std::cout << "S1 size " << sizeof(S1) << " align " << alignof(S1) << " offsets "
              << offsetof(S1, a) << ' ' << offsetof(S1, b) << ' ' << offsetof(S1, c) << ' ' << offsetof(S1, d) << '\n';
    std::cout << "S2 size " << sizeof(S2) << " align " << alignof(S2) << " offsets "
              << offsetof(S2, b) << ' ' << offsetof(S2, d) << ' ' << offsetof(S2, a) << ' ' << offsetof(S2, c) << '\n';
}
```

(In the program the members are named `a, b, c, d` in the order `flag, stamp, kind, count` of the record.)

**Check.** The payload is $1+8+1+4=14$ bytes, so 16 is the smallest multiple of the alignment that holds it, and no order can do better; the 24-byte order wastes 10 bytes. The compiled offsets equal the hand-computed ones.

**Takeaway.** `sizeof` is the layout rule applied to a particular order; sort members by decreasing alignment unless a fixed external layout forbids it.

## Exercises

1. **(Easy)** For each snippet say whether the returned handle is valid, and why: (a) `int f() { int x = 3; return x; }`; (b) `const int& g() { int x = 3; return x; }`; (c) `int* h() { static int x = 3; return &x; }`. For the invalid one, name the C++ term for what the caller now holds. *(Adapted from: C++ Core Guidelines, F.43 on returning pointers or references to locals)*
2. **(Easy)** Predict the output and say how many `int` objects exist at the end:
   ```cpp
   auto a = std::make_unique<int>(7);
   auto b = std::move(a);
   std::cout << (a == nullptr) << ' ' << *b;
   ```
   Why does the line `auto c = b;` not compile, and why is that a feature for a robot driver that owns a device handle? *(Adapted from: cppreference, std::unique_ptr)*
3. **(Medium)** **Find the bug.** A logger keeps the latest lidar scan:
   ```cpp
   struct Logger {
       const std::vector<double>* last = nullptr;
       void on_scan(const std::vector<double>& s) { last = &s; }
   };
   void tick(Logger& log) {
       std::vector<double> scan = read_lidar();   // 360 ranges
       log.on_scan(scan);
   }
   ```
   When does `last` become invalid? Give two fixes (one copying, one sharing ownership) and estimate the copy cost at 10 Hz.
4. **(Medium)** Code takes `double* p = &v[0];` and then calls `v.push_back(x)` in a loop. Explain, using capacity, when `p` stops being valid. If capacity doubles starting from 1, how many allocations happen while pushing 100 elements, and what call removes them when you know the final size?
5. **(Medium)** A planner and a visualiser both read the same map built once at startup. Decide between a value copy, `unique_ptr`, `shared_ptr<const Map>`, and a raw pointer. Justify your choice and name one cost.
6. **(Medium)** **Find the bug.**
   ```cpp
   void load(const std::string& path) {
       Config* c = new Config();
       if (!c->read(path)) return;     // early return
       apply(*c);
       delete c;
   }
   ```
   Which path leaks? If a leaked `Config` is 2 MB and `load` fails 5 times per second, how much memory leaks in 10 minutes? Rewrite it so no path can leak. *(Adapted from: C++ Core Guidelines, R.11 and R.20 on owning resources)*
7. **(Hard)** Two nodes hold each other: `struct Node { std::shared_ptr<Node> peer; };` and `a->peer = b; b->peer = a;`. Track the reference counts as the last outside handles go away, explain why the nodes are never destroyed, and fix it with `weak_ptr`.
8. **(Hard)** **Read a sanitizer report.** AddressSanitizer reports `heap-use-after-free` on a read in `Controller::update`, with "freed by thread T0 here" pointing into `std::vector<Sample>::push_back` and "previously allocated" in `Controller::record`. Reconstruct the most likely bug, say how you would confirm it, and why a clean run elsewhere proves little. *(Adapted from: the AddressSanitizer documentation in the Clang manual)*
9. **(Hard)** Design the ownership of a camera pipeline: a driver produces frames, a detector and a recorder consume them at different rates. Choose types for frames and queues, who owns what, and how a slow recorder avoids keeping the driver's buffer alive indefinitely.
10. **(Project)** Write a `Tracked` class that counts live objects. Build three scenarios (move a `unique_ptr`, destroy an element of a vector, force a vector reallocation) and assert the live count after each. Run it under `-fsanitize=address,undefined`, then deliberately introduce a dangling reference and capture the report.

11. **(Challenge)** **The real cost of `push_back`.** (a) Derive the bound $\frac{g}{g-1}n$ on the total number of element moves for $n$ pushes with growth factor $g$, and evaluate it for $g=2$ and $g=1.5$ at $n=1000$. (b) Write an element type that counts its copy and move constructions, and instantiate three versions: copyable with `noexcept` move, copyable with a non-`noexcept` move, and move-only with a non-`noexcept` move. For $n=1000$ `emplace_back` calls on a fresh vector, record the number of reallocations (watch `capacity()`), copies and moves for each, then repeat the first version after `reserve(1000)`. (c) Explain each row of your table with the strong exception guarantee and `std::move_if_noexcept`. (d) A colleague stores `T* p = &v[0]` and says "I call `reserve` first, so `p` is safe". State exactly which later operations keep `p` valid and which do not. (adapted from cppreference, `std::vector` (Iterator invalidation), `std::vector::push_back` and `std::move_if_noexcept`; C++ Core Guidelines, C.66)
12. **(Challenge)** **Which of these dangle?** Compile with `g++ -std=c++20 -g -fsanitize=address,undefined` and, before running, classify each as valid or dangling and name the rule:
    ```cpp
    std::string make() { return std::string(64, 'x'); }
    const std::string& id(const std::string& s) { return s; }
    struct H { std::vector<int> v{1, 2, 3}; const std::vector<int>& items() const { return v; } };
    H mk() { return H{}; }
    struct A { const std::string& r; };
    struct P { std::string s{std::string(64, 'y')}; };
    P mkp() { return P{}; }
    // (A)  const std::string& r = make();             use r[0]
    // (B)  const std::string& r = id(make());         use r[0]
    // (C)  std::string_view sv = make();              use sv[0]
    // (D1) A a{make()};                               use a.r[0]
    // (D2) A a(make());                               use a.r[0]
    // (E)  for (int x : mk().items()) sum += x;
    // (F)  const std::string& m = mkp().s;            use m[0]
    // (G)  const std::string& m = id(mkp().s);        use m[0]
    ```
    Report the sanitizer category for each failing case. Then state why (E) is valid again in C++23 but (B) and (G) never become valid. (adapted from cppreference, "Reference initialization", section "Lifetime of a temporary", and "Range-based for loop", section "Temporary range initializer")
13. **(Challenge)** **A list with strong `next` and weak `prev`.** Build `struct Node { int id; std::shared_ptr<Node> next; std::weak_ptr<Node> prev; };` and a list of $n=3$ nodes with a `head` and a `tail` handle. (a) Print the `use_count()` of each node's owners before anything is released, and explain each number. (b) Predict, then print, the order of the destructor calls after `tail.reset()` and then `head.reset()`, using the rule that a destructor body runs before the members are destroyed. (c) Repeat with $n=10^5$ and $n=10^6$ on a default 8 MB stack and report what happens; explain it from (b). (d) Write the iterative teardown that avoids the problem and show that $10^6$ nodes pass. (e) State what would change if `prev` were a `shared_ptr`. (adapted from cppreference, `std::shared_ptr` and `std::weak_ptr`; C++ Core Guidelines, R.24)
14. **(Challenge)** **A reference from an aliased smart pointer.** Take
    ```cpp
    std::shared_ptr<Widget> g_p;
    void g() { g_p = std::make_shared<Widget>(); }
    int f(Widget& w) { g(); return w.x; }
    // main: g_p = std::make_shared<Widget>(); std::cout << f(*g_p);
    ```
    (a) Say exactly which object is destroyed and when, and which sanitizer report you expect. (b) Give three fixes (pin a local copy, change the signature, restructure ownership) and the cost of each. (c) Assign to each of the signatures `void a(Widget&)`, `void b(Widget*)`, `void c(std::unique_ptr<Widget>)`, `void d(std::unique_ptr<Widget>&)`, `void e(std::shared_ptr<Widget>)`, `void h(const std::shared_ptr<Widget>&)` the contract it promises, using R.30 to R.36. (d) Does fix 1 help if `g()` reset a `unique_ptr<Widget>` global instead? Why or why not? (adapted from C++ Core Guidelines, R.30 to R.37, in particular R.37)

## Reference implementation

Read the contract first. Predict the output before running the code locally. This reference is for studying; a submission copied from it is assisted practice, not independent evidence.

```cpp
#include <memory>
#include <cassert>
int main() {
    auto a = std::make_unique<int>(7);
    auto b = std::move(a);
    assert(!a);
    assert(*b == 7);
} // b releases the object here
```

## Independent practice

### Goal
Make ownership observable: count live objects while moving, destroying and reallocating, and see a vector invalidate a stored address. Finish by running the program under the sanitizers.

### Setup
A C++17 compiler. Put the starter and tests in `lab.cpp` and build with `g++ -std=c++17 -Wall -Wextra -Wpedantic -g lab.cpp -o lab && ./lab`; then again with `-fsanitize=address,undefined`.

### Tasks
1. Implement `make_tracked` and `transfer`; before running, predict `Tracked::live` after each line of the first test block.
2. Implement `pick_larger`; check that the discarded object is destroyed without any explicit `delete`.
3. Implement `make_ramp` returning by value and explain why this is safe.
4. Implement `reallocation_moves_storage` and `weak_expires_after_reset`.
5. Rebuild with sanitizers. Then in a scratch file take `int* p = &v[0]`, push until reallocation, read `*p`, and record the sanitizer's report (do not keep this in the lab file).

### Starter code
```cpp
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

struct Tracked {                       // given: counts live objects
    static int live;
    int id;
    explicit Tracked(int i) : id(i) { ++live; }
    Tracked(const Tracked&) = delete;
    Tracked& operator=(const Tracked&) = delete;
    ~Tracked() { --live; }
};
int Tracked::live = 0;

// Create a Tracked with this id, owned by the returned unique_ptr.
std::unique_ptr<Tracked> make_tracked(int id) { throw std::logic_error("not implemented"); }

// Take ownership of p and give it back to the caller (move, never copy).
std::unique_ptr<Tracked> transfer(std::unique_ptr<Tracked> p) { throw std::logic_error("not implemented"); }

// Return the object with the larger id; the other one must be destroyed.
std::unique_ptr<Tracked> pick_larger(std::unique_ptr<Tracked> a, std::unique_ptr<Tracked> b) { throw std::logic_error("not implemented"); }

// Return n values 0.0, 1.0, ... by value (no pointers to locals).
std::vector<double> make_ramp(std::size_t n) { throw std::logic_error("not implemented"); }

// Fill a vector<int> to exactly its capacity, remember data() as an integer,
// push_back one more element, and return true if the storage moved.
bool reallocation_moves_storage() { throw std::logic_error("not implemented"); }

// Make a shared_ptr<Tracked>, take a weak_ptr to it, reset the shared_ptr,
// and return whether the weak_ptr is now expired.
bool weak_expires_after_reset() { throw std::logic_error("not implemented"); }
```

### Tests
Paste this below the starter code (same file) and run it. Every check is a plain `assert`; the first failure stops the run.

```cpp
int main() {
    assert(Tracked::live == 0);
    {   // moving ownership does not create or destroy objects
        auto a = make_tracked(5);
        assert(Tracked::live == 1);
        auto b = transfer(std::move(a));
        assert(a == nullptr && b != nullptr && b->id == 5 && Tracked::live == 1);
    }
    assert(Tracked::live == 0);                         // destroyed at scope end
    {   // the loser is destroyed inside pick_larger
        auto big = pick_larger(make_tracked(3), make_tracked(9));
        assert(big->id == 9 && Tracked::live == 1);
        auto tie = pick_larger(make_tracked(4), make_tracked(4));
        assert(Tracked::live == 2);
    }
    assert(Tracked::live == 0);
    {   // elements of a vector of unique_ptr are owned by the vector
        std::vector<std::unique_ptr<Tracked>> v;
        for (int i = 0; i < 3; ++i) v.push_back(make_tracked(i));
        assert(Tracked::live == 3);
        v.erase(v.begin());
        assert(Tracked::live == 2);
    }
    assert(Tracked::live == 0);
    auto r = make_ramp(4);
    assert(r.size() == 4 && r[0] == 0.0 && r[3] == 3.0 && make_ramp(0).empty());
    assert(reallocation_moves_storage());               // old pointers would dangle
    assert(weak_expires_after_reset() && Tracked::live == 0);
    std::cout << "ramp size " << r.size() << ", live objects at end " << Tracked::live << "\n";
    std::cout << "all tests passed\n";
}
```

### Expected output
A correct solution prints the following; with sanitizers the output is identical and no report appears.

```text
ramp size 4, live objects at end 0
all tests passed
```

### Extension challenge
Write `class SampleBuffer` that owns a `std::vector<double>`, exposes `const std::vector<double>& samples() const`, and provides `void push(double)`. Show with a test that a stored reference from `samples()` stays valid across `push` only if you `reserve` first, and document that contract in a comment.

## Verification

Check every claim about lifetime by two independent routes. Statically: build with `-Wall -Wextra` (warnings such as `-Wreturn-local-addr`) and read each reference or pointer that escapes a function. Dynamically: build with `-fsanitize=address,undefined -g` and run a test that executes the suspect path; report the sanitizer category (`heap-use-after-free`, `stack-use-after-scope`, `heap-buffer-overflow`) and compare it with the category you predicted. Check layout claims with `static_assert(sizeof(S) == 16)` and `offsetof`, so that a change in member order or in the platform fails the build instead of a wire protocol. Check ownership with a counting type like `Tracked` of the lab: assert the number of live objects after a move, after destroying a vector element and after a reallocation. Remember what each tool cannot show: a clean sanitizer run covers only the executed paths, and `p == v.data()` is not a validity test.

## Failure modes

- **Dangling reference to a local:** returning `const T&` to a block variable, or storing `&s` of a parameter that the caller destroys (the logger of Exercise 3). GCC may turn it into a null reference, so the symptom can be a crash far from the cause.
- **Invalidated pointer into a vector:** `push_back`, `insert` or `erase` after taking `&v[0]`; the old block is freed, and the stale address may still compare equal to a new one.
- **Temporary that dies at the semicolon:** `const auto& r = id(make());`, `std::string_view sv = make();`, or `for (auto x : f().items())` before C++23.
- **Leak on an early exit:** a raw `new` with `delete` at the end (Exercise 6), or a `shared_ptr` cycle (Exercise 7).
- **Reference taken from an aliased smart pointer:** a callee resets the global `shared_ptr` while the caller still uses `*g_p` (Exercise 14).
- **Layout assumptions:** `memcpy` of a struct to a wire format, or reading a padded struct byte by byte; padding bytes have no meaningful value, and the layout may differ between platforms and compilers.
- **Shared ownership is not thread safety:** the control block's count is atomic, the pointed-to object is not.

## Alternatives and trade-offs

- **Value semantics first.** Returning a `std::vector` by value is cheap (move or copy elision) and has no lifetime question; the cost is a copy where sharing was intended.
- **`unique_ptr` versus `shared_ptr` versus a raw non-owning pointer or reference.** `unique_ptr` has the size of a pointer and no run-time cost; `shared_ptr` adds a control block, an atomic count and coupling of lifetimes; a raw pointer or reference is right only when a longer-lived owner is guaranteed elsewhere (R.3, R.30).
- **Indices or handles instead of pointers.** An index into a vector survives reallocation (but not erase of earlier elements); a generational handle also detects use after removal, at the cost of a lookup.
- **`reserve` versus `std::deque` or `std::list`.** `reserve` keeps one contiguous block and works when the maximum size is known; `std::deque` never relocates existing elements on `push_back` (references stay valid, iterators do not) at the price of non-contiguity; `std::list` keeps every node address stable but costs an allocation per element.
- **Reordered members versus a documented layout.** Sorting members by decreasing alignment saves memory; an explicit wire format with fixed-width integers and serialisation functions is safer when the bytes leave the process.

## Transfer and retention

A callback stores a pointer to a temporary sensor buffer. Describe a failure scenario and redesign the ownership contract so the callback can safely outlive the producer call.

Close the reference before trying. Without looking, draw the picture of each of these on paper: a `std::vector<double>` of 6 elements with a pointer to element 2 before and after a `push_back` that reallocates; the byte map of `struct { char a; short b; int c; }` with its size; and the owner, the weak observers and the control block for a `shared_ptr` handed to two consumers. State for each which handle becomes invalid when. Return after at least a week and reconstruct the storage durations, the layout rule and the invalidation table from a blank page, then check against the lesson.

## Exercise answers

1. (a) valid: a copy of the value is returned. (b) invalid: the local `x` is destroyed on return, so the caller holds a **dangling reference**. (c) valid while the program runs because `x` has static storage (but it is shared global state, not thread-safe).
2. Output `1 7`: after the move `a` is null and `b` owns the value; one `int` exists. `unique_ptr` is not copyable because there must be exactly one owner; for a device handle this prevents two owners both closing it.
3. `last` points at the local `scan`, which is destroyed when `tick` returns, so any later use is undefined behaviour. Fix 1: `std::vector<double> last;` and `last = s;` (copy). Fix 2: pass `std::shared_ptr<const std::vector<double>>` and store it. The copy is $360\times8=2880$ B, at 10 Hz about $29$ kB/s: negligible.
4. `p` is invalid as soon as `push_back` exceeds the current capacity, because the elements move to a new block. Capacities $1,2,4,\dots,128$ give **8** allocations for 100 elements. `v.reserve(100)` before the loop makes it one allocation and keeps pointers valid up to that size.
5. Best: `std::shared_ptr<const Map>` (read-only, lifetime tied to the last user) or, if both consumers are in the same scope and outlive nothing, a `const Map&`. A value copy duplicates a large map; `unique_ptr` cannot be shared; a raw pointer says nothing about ownership. Cost: an atomic reference count and shared lifetime that is harder to reason about.
6. The early `return` leaks `c` (the `delete` is skipped; an exception from `apply` leaks too). $2\ \text{MB}\times5\times600=6000$ MB, 6 GB. Fix: `auto c = std::make_unique<Config>();` (or just `Config c;`), with no `delete`.
7. After `a->peer = b; b->peer = a;` each node has a count of 2 (the local handle plus the peer). Dropping the local handles leaves counts of 1, held by each other, so neither reaches zero: a leak. Make one direction `std::weak_ptr<Node> peer;` (non-owning) so the counts reach zero.
8. A pointer/reference/iterator into the vector (likely stored in `record`) was used in `update` after `push_back` reallocated and freed the old block. Confirm by running the failing scenario with ASan, finding the stored address, and checking `capacity()` before/after; fix by storing an index, using `reserve`, or copying. A clean run elsewhere proves little because sanitizers only report executed paths.
9. A good design: frames are `std::shared_ptr<const Frame>` from a pool; each consumer has a bounded queue (or "latest only" slot) so a slow recorder drops or skips frames instead of pinning memory; the driver owns the pool and reuses buffers whose use count has fallen to one. It states what happens at overflow and that consumers never mutate shared frames.
10. A good answer asserts: moving a `unique_ptr` leaves the live count unchanged; destroying a vector element decrements by one; reallocating a vector of movable objects keeps the live count equal to the element count after the move (copies, if any, are destroyed). The dangling-reference experiment shows `heap-use-after-free` with allocation and free stack traces. The experiment is kept out of control code.

11. (a) Reallocations happen at sizes $1,g,\dots,g^{m-1}$ with $g^{m-1}<n$, and each moves as many elements as the current size, so moves $\le\sum_{i<m}g^i<n(1+g^{-1}+g^{-2}+\cdots)=\frac{g}{g-1}n$. For $n=1000$: $2000$ for $g=2$ and $3000$ for $g=1.5$. (b) Results from g++ 11.4.0 (libstdc++, growth factor 2) with $n=1000$: noexcept move, copyable: 11 reallocations, 0 copies, **1023 moves**; throwing move, copyable: 11 reallocations, **1023 copies**, 0 moves; throwing move, move-only: 11 reallocations, 0 copies, 1023 moves; after `reserve(1000)`: 0 reallocations, 0 copies, 0 moves. The capacities are $1,2,4,\dots,1024$, so the moves are $1+2+\dots+512=1023<2n$, consistent with (a). (c) `push_back` and `emplace_back` must leave the vector unchanged if something throws (strong guarantee). Moving elements into the new block with a throwing move would leave the old block half-emptied, so `move_if_noexcept` selects the copy when the move may throw *and* a copy exists; when the type is move-only there is no safe alternative, so it moves anyway and the guarantee is waived (cppreference). `reserve` removes all relocation. (d) After `reserve(N)`, the pointer `p` to element 0 stays valid across any number of `push_back`/`emplace_back` calls as long as `size()` never exceeds $N$ (capacity then never changes), and across `pop_back` (it invalidates only the erased element and `end()`) as long as element 0 is not the one erased. It is invalidated by: `push_back` beyond $N$ (capacity changes, all invalidated); `insert` at the front (everything at or after the insertion point, including element 0, even without reallocation); `erase(begin())`; `clear()` and `operator=`/`assign` (always invalidate); `shrink_to_fit` (may reallocate); and `reserve` with a larger argument (capacity changes). "I call `reserve` first" is therefore a promise about *how many* elements will be added, which should be asserted (`assert(v.size() < v.capacity())` before each insertion) or encoded by using indices instead of pointers.
12. Verified with g++ 11.4.0, `-std=c++20`, ASan+UBSan. Valid: (A) the temporary is bound directly to the reference, so its lifetime is extended (the program printed `x`); (D1) brace-initialisation of an aggregate reference member extends it (printed `x`); (F) a data member of a temporary, bound directly, is covered by the extension rule (printed `y`). Dangling: (B) the temporary is bound to the *parameter* of `id`, so it dies at the end of the full expression and `r` refers to it (ASan: `stack-use-after-scope`); (C) the `std::string` temporary is destroyed, leaving the view pointing at freed heap storage (`heap-use-after-free`, because 64 characters exceed the small-string buffer); (D2) parenthesised aggregate initialisation, new in C++20, does not extend (`stack-use-after-scope`); (E) the range is bound to the reference returned by `items()`, the temporary `H` dies before the loop body (`stack-use-after-scope`); (G) as (B): the reference parameter ends the extension (`stack-use-after-scope`). (E) is fixed in C++23: the range-based `for` page states that, since C++23, the lifetimes of all temporaries in the range-initialiser are extended to the end of the loop (before that it is undefined behaviour); in C++20 the workaround is an init-statement, `for (H h = mk(); int x : h.items())`. (B) and (G) are not range-based `for` loops, so that rule does not apply: the temporary is bound to a reference *parameter*, and by the parameter rule it exists only until the end of the full expression containing the call. Fix any of them by copying the value: `std::string s = id(make());`.
13. (a) With `head`, `tail` and `n = 3`: node 1 has count $1$ (only `head`), node 2 has $1$ (only `node1.next`), node 3 has $2$ (`node2.next` and `tail`); the `prev` pointers are weak and add nothing to the strong count (checked by running: `use(head)=1 use(2nd)=1 use(tail)=2`). (b) `tail.reset()` only lowers node 3's count from 2 to 1; nothing is destroyed. `head.reset()` drops node 1's count to 0, so its destructor body runs (`~Node(1)`), then its members are destroyed, which releases `next` and destroys node 2 (`~Node(2)`), and so on: the output is `~Node(1) ~Node(2) ~Node(3)`. (c) The destruction is recursive: each node's `next` member destroys the next node inside the previous node's destructor. Measured with `ulimit -s` $=8192$ kB at `-O0`: $n=10^5$ completed, $n=10^6$ crashed with exit status 139 (SIGSEGV from stack overflow). The exact threshold depends on frame size and optimisation. (d) `while (head && head.use_count() == 1) head = std::move(head->next);` detaches the successor before the node is destroyed, so every node is destroyed at depth one; $n=10^6$ then completed with the same destructor order. (e) With a strong `prev` every adjacent pair would own each other: counts of 2 per interior node, none reaching zero after `head.reset()` (Exercise 7 cycle) and the whole list would leak.
14. (a) `f` receives a reference to the widget owned by `g_p`. `g()` assigns a new widget to `g_p`, which drops the only owner of the old one and destroys it; `w.x` in `f` then reads freed memory. ASan reports `heap-use-after-free` on a READ of size 4 in `f`, with the free stack trace under `g` (reproduced with g++ 11.4.0; it printed no error and `42` for the pinned version). (b) Fix 1: `auto pin = g_p; f(*pin);` in the caller, cost one reference-count increment (atomic) for the whole call tree (R.37). Fix 2: change `f` to take `std::shared_ptr<Widget>` by value (R.34), which keeps its own count at the same cost but makes the lifetime dependency visible in the signature. Fix 3: restructure so that nothing called from `f` can reset `g_p` (for example make the global immutable after start-up, or pass the widget down from an owner that outlives the call); zero run-time cost but it needs discipline and a design review. (c) `a`: uses the object, non-null, no lifetime role; `b`: uses it, may be null; `c`: takes ownership (a sink), the caller must `std::move`; `d`: may reseat or reset the caller's pointer (R.33); `e`: shares ownership (R.34); `h`: may or may not retain a count, so it is a weaker promise and the smart pointer is only there for lifetime (R.36). Functions that merely use the object should prefer `a` or `b` (R.30). (d) No: the pin cannot be copied because a `unique_ptr` is the only owner; if `g()` resets the global `unique_ptr`, the object is destroyed regardless. The remedy is structural: do not let callees reach the owning pointer, or move ownership into a local for the duration of the call tree.

## Further reading

[LearnCpp](https://www.learncpp.com/) — primary course, documentation, or the supplied reference collection. Follow the relevant subject heading; these are further reading links, not reproduced book chapters.

- [C++ working draft](https://eel.is/c++draft/) - [basic.stc.general], [basic.stc.auto], [basic.stc.dynamic], [basic.align], [class.temporary].
- [cppreference: Storage duration](https://en.cppreference.com/w/cpp/language/storage_duration), [Object](https://en.cppreference.com/w/cpp/language/object) (alignment), [sizeof](https://en.cppreference.com/w/cpp/language/sizeof), [offsetof](https://en.cppreference.com/w/cpp/types/offsetof), [std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr) and [operator new](https://en.cppreference.com/w/cpp/memory/new/operator_new).
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector) (iterator invalidation) and [std::move_if_noexcept](https://en.cppreference.com/w/cpp/utility/move_if_noexcept).
- [cppreference: Reference initialization](https://en.cppreference.com/w/cpp/language/reference_initialization) (lifetime of a temporary) and [Range-based for loop](https://en.cppreference.com/w/cpp/language/range-for).
- [cppreference: std::shared_ptr](https://en.cppreference.com/w/cpp/memory/shared_ptr) and the Core Guidelines rules C.66, R.22 to R.24 and R.30 to R.37.

**More practice:** [LearnCpp chapter 22 quiz](https://www.learncpp.com/cpp-tutorial/chapter-22-summary-and-quiz/) (move semantics and smart pointers), [LearnCpp std::unique_ptr](https://www.learncpp.com/cpp-tutorial/stdunique_ptr/) and [std::shared_ptr](https://www.learncpp.com/cpp-tutorial/stdshared_ptr/) lessons, the [C++ Core Guidelines resource-management rules](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management), and the [AddressSanitizer use-after-free example](https://github.com/google/sanitizers/wiki/AddressSanitizerExampleUseAfterFree).
