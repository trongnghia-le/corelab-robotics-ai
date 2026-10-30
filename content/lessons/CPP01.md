---
{
  "id": "cpp01-foundations",
  "module_id": "CPP01",
  "title": "C++ fundamentals: types, scope, and predictable values",
  "summary": "Write a small compiled program and understand its arithmetic.",
  "estimated_minutes": 55,
  "prerequisites": [],
  "source_refs": [
    {
      "title": "LearnCpp",
      "url": "https://www.learncpp.com/"
    }
  ],
  "objectives": [
    "Compile and run a C++17 program.",
    "Predict integer and floating-point arithmetic.",
    "Use vectors and const references safely."
  ],
  "core_theory": [
    "C++ fundamentals: types, scope, and predictable values"
  ],
  "labs": [
    "Create main.cpp, compile it with the command above, and add singleton, mixed-sign, and empty-input cases. Predict each result before execution. Change one operand in a division from int to double and explain the result."
  ],
  "assessment_refs": [
    "CPP01-diagnostic-v1"
  ],
  "review_prompts": [
    "Compute a moving average for sampled motor velocity. State your numeric type, input contract, boundary behavior, and one test that catches integer truncation."
  ],
  "extension_refs": [
    "https://www.learncpp.com/"
  ]
}
---

## Why this matters

Write a small compiled program and understand its arithmetic. This lesson develops the core calculation before asking you to apply it in a new setting. Start with the diagnostic if you think you already know it; prior tool use is not evidence of understanding.

## Intuition

C++ makes representation and lifetime visible. A type tells the compiler which operations are valid, but also controls arithmetic and memory layout. Compilation catches some mistakes before execution; tests must catch incorrect behavior that is still legal C++.

## Theory and derivation

A variable declaration introduces a typed object: `int count{3};` stores an integer, while `double dt{0.01};` stores an approximate real value. Initialize every local scalar before reading it. Integer division truncates toward zero: `5/2` is 2, whereas `5.0/2` is 2.5. Converting the truncated result to double afterward does not recover the lost fraction.

Functions declare a return type and typed parameters. Passing a vector by value copies it; `const std::vector<double>&` lets a function inspect the existing vector without mutation. The referenced object must remain alive during the call. Local scope determines where names are visible and when ordinary automatic objects are destroyed.

Use `std::vector` for a runtime-sized sequence. Its `size()` is a count, while valid indices run from zero through size minus one. `operator[]` does not check bounds; `.at()` does. Prefer range-based loops when the index has no separate meaning. Compile with warnings enabled and treat a warning as a question to resolve, not decoration.

## Worked example

If int steps=5 and total=2, `double ratio=steps/total;` produces 2.0 because division happened as integers. `double ratio=static_cast<double>(steps)/total;` produces 2.5. For an empty vector, a mean function must reject input before division.

## Reference implementation

Read the contract first. Predict the output before running the code locally. This reference is for studying; a submission copied from it is assisted practice, not independent evidence.

```cpp
#include <vector>
#include <stdexcept>
#include <cassert>
double mean(const std::vector<double>& x) {
    if (x.empty()) throw std::invalid_argument("empty");
    double sum{0.0};
    for (double v : x) sum += v;
    return sum / static_cast<double>(x.size());
}
int main() { assert(mean({2.,4.,6.}) == 4.); }
// g++ -std=c++17 -Wall -Wextra -Wpedantic main.cpp -o demo
```

## Independent practice

Create main.cpp, compile it with the command above, and add singleton, mixed-sign, and empty-input cases. Predict each result before execution. Change one operand in a division from int to double and explain the result.

Record the problem, your derivation, implementation, exact command, and observed output. State assistance A0–A3 honestly. If you used a solution, repeat a new task without it before claiming independence.

## Verification

Check the worked numerical example independently, then test a boundary case and an invariant from the derivation. Keep the expected result separate from the implementation. Change a sign or remove one term deliberately: your tests should reject that broken version. Use the diagnostic to check concepts and numerical reasoning; short answers remain rubric-guided practice.

## Failure modes

An uninitialized local integer has no valid predictable value to rely on. An out-of-range vector access is not a safe way to detect the end of data. A reference does not extend an arbitrary object lifetime.

## Alternatives and trade-offs

Python is convenient for rapid inspection; C++ offers explicit types and control over resources. Start with standard containers and clear ownership before optimizing or introducing raw pointers.

## Transfer and retention

Compute a moving average for sampled motor velocity. State your numeric type, input contract, boundary behavior, and one test that catches integer truncation.

Close the reference before trying. Explain your assumptions and one way your answer could fail. Return after at least a week and reconstruct the key argument from a blank page. A quiz alone does not verify unfamiliar transfer or research-level competence.

## Further reading

[LearnCpp](https://www.learncpp.com/) — primary course, documentation, or the supplied reference collection. Follow the relevant subject heading; these are further reading links, not reproduced book chapters.
