---
{
  "id": "cpp02-foundations",
  "module_id": "CPP02",
  "title": "Memory, references, and lifetime",
  "summary": "Explain who owns an object and how long a reference stays valid.",
  "estimated_minutes": 55,
  "prerequisites": [
    "CPP01"
  ],
  "source_refs": [
    {
      "title": "LearnCpp",
      "url": "https://www.learncpp.com/"
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

## Theory and derivation

An automatic local object is destroyed when its scope ends. Returning a pointer or reference to it leaves a dangling handle. Copying a value creates another object with its own lifetime; copying a pointer only creates another address value.

`std::vector` owns contiguous element storage. Growing beyond capacity can allocate a new block, move elements, and invalidate pointers, references, and iterators to the old storage. A vector object can remain alive while a pointer to one of its former elements becomes invalid. Do not rely on observed address stability from one run.

RAII associates resource release with object destruction. `std::unique_ptr<T>` owns one dynamically allocated object and cannot be copied; moving transfers ownership. `std::shared_ptr<T>` shares ownership with a reference count and additional cost. Neither automatically makes access thread-safe. Prefer values and containers until dynamic ownership is actually needed.

To inspect suspected memory errors, compile your own code with `-fsanitize=address,undefined -g`. Sanitizers detect many executed invalid operations; passing one run is not proof that every lifetime is correct.

## Worked example

A function `const int& bad(){ int x=3; return x; }` returns a reference after x has been destroyed. In contrast, `int good(){ int x=3; return x; }` returns a value. With vector v, taking &v[0] and then causing a reallocation can invalidate that pointer even though v still exists.

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

Draw lifetimes for a value, reference, and unique_ptr across nested scopes. Write a safe function returning a vector by value. In a separate intentional experiment, use a sanitizer to identify a dangling reference; do not run undefined behavior in robot control code.

Record the problem, your derivation, implementation, exact command, and observed output. State assistance A0–A3 honestly. If you used a solution, repeat a new task without it before claiming independence.

## Verification

Check the worked numerical example independently, then test a boundary case and an invariant from the derivation. Keep the expected result separate from the implementation. Change a sign or remove one term deliberately: your tests should reject that broken version. Use the diagnostic to check concepts and numerical reasoning; short answers remain rubric-guided practice.

## Failure modes

“The address still contains 3” does not make a destroyed object valid. Shared ownership prevents some premature destruction but can introduce cycles and does not fix data races.

## Alternatives and trade-offs

Value semantics simplify lifetime reasoning. unique_ptr expresses exclusive ownership. shared_ptr is useful for genuinely shared lifetimes but adds coupling and overhead; nonowning references remain appropriate when lifetime is guaranteed elsewhere.

## Transfer and retention

A callback stores a pointer to a temporary sensor buffer. Describe a failure scenario and redesign the ownership contract so the callback can safely outlive the producer call.

Close the reference before trying. Explain your assumptions and one way your answer could fail. Return after at least a week and reconstruct the key argument from a blank page. A quiz alone does not verify unfamiliar transfer or research-level competence.

## Further reading

[LearnCpp](https://www.learncpp.com/) — primary course, documentation, or the supplied reference collection. Follow the relevant subject heading; these are further reading links, not reproduced book chapters.
