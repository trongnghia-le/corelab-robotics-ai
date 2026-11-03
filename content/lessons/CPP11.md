---
{
  "id": "cpp11-foundations",
  "module_id": "CPP11",
  "title": "Numerical C++: Eigen, linear solvers, and numerical stability",
  "summary": "Use Eigen matrices and decompositions to solve least-squares problems, and predict and measure how conditioning limits accuracy.",
  "estimated_minutes": 400,
  "prerequisites": [
    "CPP05",
    "M03"
  ],
  "source_refs": [
    {
      "title": "Eigen: Getting started",
      "url": "https://eigen.tuxfamily.org/dox/GettingStarted.html"
    },
    {
      "title": "Eigen: Linear algebra and decompositions",
      "url": "https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html"
    },
    {
      "title": "MIT 18.06 Linear Algebra (OpenCourseWare)",
      "url": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/"
    }
  ],
  "objectives": [
    "Create and manipulate Eigen matrices and vectors and avoid the common expression-template and aliasing pitfalls.",
    "Choose a decomposition (LU, Cholesky, QR, SVD) for a given linear system.",
    "Solve least-squares problems with QR and with the normal equations and explain why they differ in accuracy.",
    "Relate the condition number to digits lost, and verify C++ results against an independent Python oracle."
  ],
  "core_theory": [
    "Eigen",
    "linear solvers",
    "numerical stability"
  ],
  "labs": [
    "Implement least squares by QR and by normal equations with Eigen, a Vandermonde design matrix, residual and condition-number helpers; compare the error growth with degree and check results against NumPy."
  ],
  "assessment_refs": [
    "CPP11-diagnostic-v1"
  ],
  "review_prompts": [
    "A calibration routine fits a degree-9 polynomial to sensor data using the normal equations and returns unstable coefficients between runs. Explain the likely cause with numbers and propose two changes."
  ],
  "extension_refs": [
    "https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html",
    "https://eigen.tuxfamily.org/dox/group__LeastSquares.html"
  ]
}
---

## Why this matters

Almost every estimation and control problem in robotics eventually becomes a linear system or a least-squares fit: calibrating a camera or an IMU bias, fitting a plane to a point cloud, solving a Kalman update, computing a Jacobian pseudo-inverse for inverse kinematics, optimizing a pose graph. In C++ the standard tool is Eigen, a header-only library whose matrices compile to tight loops. But two things differ from textbook algebra. First, floating point arithmetic has about 16 significant digits, and an ill-conditioned problem can throw most of them away. Second, *how* you solve matters: solving the least-squares problem by forming $A^\top A$ squares the condition number and can lose twice as many digits as a QR factorization. In the experiment of this lesson, the same degree-9 polynomial fit loses 5 digits with QR (error $2.5\times10^{-11}$) and 12 digits with the normal equations (error $4.9\times10^{-4}$). Knowing which solver to call, and how to check the answer against an independent oracle, is what separates a result you can trust on a robot from one that merely compiles.

## Intuition

Think of the condition number $\kappa(A)$ as a magnifier: if the input has relative error $\epsilon$, the answer may have relative error up to $\kappa\epsilon$. Rounding in each arithmetic operation adds an error of size $\epsilon_{\text{mach}}\approx1.1\times10^{-16}$, so even a perfect algorithm applied to a problem with $\kappa=10^{8}$ can only be trusted to about $10^{-8}$. A *stable* algorithm adds no more error than that unavoidable amount; an *unstable* one adds more.

Least squares has a nice geometry. The best fit $A\hat x$ is the projection of $b$ onto the column space of $A$; the leftover $r=b-A\hat x$ is perpendicular to every column: $A^\top r=0$. QR works directly with an orthonormal basis of that space (orthogonal transformations do not amplify errors). The normal equations $A^\top A\hat x=A^\top b$ are algebraically equivalent but start by multiplying $A^\top A$, whose condition number is $\kappa(A)^2$.

![Projection of b onto the column space of A with perpendicular residual, and a bar chart of the error of QR versus normal equations for polynomial degrees 3, 6, 9 and 12](/lesson-figures/CPP11.svg)

*Left: the residual is orthogonal to the column space. Right: measured coefficient error of QR (about cond times 1e-16) and of the normal equations (about cond squared times 1e-16).*

## Theory and derivation

### Eigen basics

```cpp
#include <Eigen/Dense>
Eigen::MatrixXd A(3, 2);      // dynamic size, column-major by default
A << 1, 0,
     1, 1,
     1, 2;
Eigen::VectorXd b(3);  b << 1, 2, 2;
Eigen::Vector3d v(1, 2, 3);   // fixed size: no heap allocation, preferred for small vectors
double n = (A * x - b).norm();
```
Indices are zero-based and `A(i, j)` is row $i$, column $j$. `Eigen::Map<VectorXd>(ptr, n)` views existing memory without copying. Compile with `-I/usr/include/eigen3` (or `find_package(Eigen3)` and `Eigen3::Eigen` in CMake) and `-O2`; Eigen is very slow without optimization.

**Expression templates.** `A * x + b` does not compute anything: it builds a lightweight expression object that is evaluated when assigned to a matrix. Two traps follow.

1. `auto` captures the expression, not the result. `auto s = M.colPivHouseholderQr().solve(b);` keeps a reference to the temporary decomposition, which is destroyed at the end of the statement: reading `s` later is a use-after-scope (AddressSanitizer reports `stack-use-after-scope`). Write `Eigen::VectorXd s = ...;`.
2. **Aliasing.** `A = A.transpose();` reads and writes the same memory while evaluating. In a debug build Eigen asserts "aliasing detected during transposition"; with `-O2 -DNDEBUG` it silently produces a wrong matrix (for $\begin{pmatrix}1&2\\3&4\end{pmatrix}$ it printed $\begin{pmatrix}1&2\\2&4\end{pmatrix}$ instead of $\begin{pmatrix}1&3\\2&4\end{pmatrix}$). Use `A.transposeInPlace()` or `A = A.transpose().eval();`.

### Solving linear systems

Never form an explicit inverse to solve $Ax=b$; factorize and solve. Choose by structure:

| Matrix | Decomposition (Eigen) | Cost (flops, $n\times n$) | Notes |
|---|---|---|---|
| general square | `partialPivLu()` | $\tfrac23n^3$ | fast, stable in practice |
| symmetric positive definite (covariances, normal equations) | `llt()` / `ldlt()` | $\tfrac13n^3$ | Cholesky; fails/flags if not SPD |
| tall, full rank, least squares | `householderQr()` / `colPivHouseholderQr()` | $2mn^2-\tfrac23n^3$ | stable, detects rank with pivoting |
| rank-deficient, or you need $\sigma$ | `jacobiSvd()` / `bdcSvd()` | larger | most robust; gives the condition number |

At $n=1000$, Cholesky is $\approx3.3\times10^{8}$ flops, about 33 ms at 10 GFLOP/s; at $n=6$ it is about 72 flops, negligible.

### Least squares

Given $A\in\mathbb R^{m\times n}$, $m\ge n$, find $\hat x=\arg\min\|Ax-b\|_2$. Setting the gradient to zero gives the normal equations $A^\top A\hat x=A^\top b$, equivalently $A^\top(A\hat x-b)=0$. With the thin QR factorization $A=QR$ ($Q^\top Q=I$, $R$ upper triangular) the problem becomes $R\hat x=Q^\top b$, solved by back substitution; the residual norm is $\|(I-QQ^\top)b\|$.

**Why normal equations lose accuracy.** With the SVD $A=U\Sigma V^\top$, $A^\top A=V\Sigma^2V^\top$ so $\kappa(A^\top A)=\sigma_{\max}^2/\sigma_{\min}^2=\kappa(A)^2$. A solver with error $\approx\kappa\,\epsilon_{\text{mach}}$ applied to this matrix gives $\kappa(A)^2\epsilon_{\text{mach}}$, whereas QR achieves about $\kappa(A)\epsilon_{\text{mach}}$ (for small residual problems).

**Digits.** Digits lost $\approx\log_{10}\kappa$. For $\kappa=3.6\times10^{6}$: QR keeps about $16-6.6\approx9$ digits; the normal equations keep about $16-13.1\approx3$.

### Conditioning of polynomial fits

The Vandermonde matrix with columns $1,t,t^2,\dots,t^d$ on $[0,1]$ becomes nearly rank-deficient as $d$ grows, because high powers look alike. Measured with 50 equally spaced points:

| degree | $\kappa(A)$ | QR error | normal-equation error |
|---|---|---|---|
| 3 | 1.2e2 | 4.0e-15 | 1.2e-12 |
| 6 | 2.0e4 | 4.6e-13 | 2.1e-08 |
| 9 | 3.6e6 | 2.5e-11 | 4.9e-04 |
| 12 | 6.8e8 | 3.4e-08 | 3.8e+00 |

(errors are $\|\hat c-c_{\text{true}}\|$ for noise-free data $y=Ac_{\text{true}}$ with $c_{\text{true},j}=(-1)^j(1+0.1j)$, the same coefficients as the lab test; other coefficients give errors of the same order, and the last digits depend on the platform.) Centering and scaling $t$ to $[-1,1]$ reduces the degree-12 condition number to $1.6\times10^{4}$; orthogonal polynomial bases (Chebyshev) are better still. Remedies for near-singular problems: scale the columns, use SVD with truncation, or add Tikhonov (ridge) regularization $(A^\top A+\lambda I)x=A^\top b$.

### Verifying with an oracle

An independent implementation catches wiring mistakes (wrong index, transposed matrix). Compare *residual norms* and *fitted values*, not only coefficients, when the problem is ill-conditioned, since coefficients can differ in the last digits while the fit is identical. Choose tolerances from $\kappa\,\epsilon_{\text{mach}}$, not arbitrary $10^{-6}$.

## Worked example

Fit $y=a+bt$ to the points $(0,1),(1,3),(2,4),(3,8)$.

1. Design matrix $A=\begin{pmatrix}1&0\\1&1\\1&2\\1&3\end{pmatrix}$, $b=(1,3,4,8)^\top$.
2. $A^\top A=\begin{pmatrix}4&6\\6&14\end{pmatrix}$ (column sums: $4$, $0+1+2+3=6$, $0+1+4+9=14$). $A^\top b=(1+3+4+8,\ 0\cdot1+1\cdot3+2\cdot4+3\cdot8)^\top=(16,\ 35)^\top$.
3. Determinant $4\cdot14-6\cdot6=20$. Then $a=\dfrac{14\cdot16-6\cdot35}{20}=\dfrac{224-210}{20}=0.7$ and $b=\dfrac{4\cdot35-6\cdot16}{20}=\dfrac{140-96}{20}=2.2$.
4. Fitted values $0.7+2.2t=(0.7,\ 2.9,\ 5.1,\ 7.3)$; residual $r=A\hat x-b=(-0.3,\ -0.1,\ 1.1,\ -0.7)$.
5. Check orthogonality: $\sum r_i=-0.3-0.1+1.1-0.7=0$ and $\sum t_ir_i=0-0.1+2.2-2.1=0$. Both zero, as $A^\top r=0$ requires.
6. Residual norm $\sqrt{0.09+0.01+1.21+0.49}=\sqrt{1.8}=1.3416$.
7. Conditioning: $\sigma$'s of $A$ give $\kappa(A)\approx3.76$ (so no digits are at risk), and either method works; in the degree-12 case above they would not.

## Exercises

Problems marked *Adapted* restate a standard exercise type from the cited source in new words and numbers.

1. **(Easy)** *(Adapted from: MIT 18.06, least squares and projections)* Fit $y=a+bt$ by least squares to $(0,2),(1,3),(2,7)$. Give $\hat x$, the residual vector, and verify $A^\top r=0$.
2. **(Easy)** *(Adapted from: Eigen, Linear algebra and decompositions)* Name the Eigen decomposition you would use for: (a) a 6x6 symmetric positive definite stiffness matrix; (b) a general 4x4 Jacobian system; (c) a tall 1000x5 full-rank design matrix; (d) a possibly rank-deficient 1000x5 design matrix where you want the rank and the pseudo-inverse.
3. **(Easy)** A problem has $\kappa(A)=3.6\times10^{6}$. Estimate the accurate digits of a double-precision solution for a stable method on $A$ and for the normal equations.
4. **(Medium)** Find the bug (two lines are wrong in different ways) and say how each would show up:
   ```cpp
   Eigen::MatrixXd M(2, 2); M << 1, 2, 3, 4;
   M = M.transpose();
   auto x = M.colPivHouseholderQr().solve(b);
   ```
5. **(Medium)** *(Adapted from: Eigen documentation, aliasing)* Predict what `M = M.transpose();` does in a Debug build and in `-O2 -DNDEBUG`, and give two correct alternatives. Why does `C = A * B;` have no such problem for matrix products by default?
6. **(Medium)** For a design matrix with $\kappa=10^{6}$, estimate the relative error of QR and of the normal equations with $\epsilon_{\text{mach}}=1.1\times10^{-16}$. Compare with the measured degree-9 row of the table ($\kappa=3.6\times10^{6}$) and comment on the agreement.
7. **(Medium)** Write a NumPy snippet that checks the lab's C++ result for the data $t=0..9$, $y=(1.1, 2.9, 5.2, 7.1, 8.8, 11.2, 13.1, 14.8, 17.1, 19.0)$ and decide which quantities to compare and with which tolerance.
8. **(Hard)** *(Adapted from: Trefethen and Bau, Numerical Linear Algebra, lectures on least squares and conditioning)* Prove that $\kappa_2(A^\top A)=\kappa_2(A)^2$ for full-column-rank $A$, and derive the least-squares solution through QR: show that $\hat x=R^{-1}Q^\top b$.
9. **(Hard)** The columns of a calibration matrix are nearly collinear: $\sigma_{\max}=1$, $\sigma_{\min}=10^{-4}$. Compute $\kappa(A)$ and $\kappa(A^\top A)$. With ridge parameter $\lambda=10^{-6}$ compute the condition number of $A^\top A+\lambda I$ and discuss the bias-variance trade-off of choosing $\lambda$.
10. **(Hard)** Cost model: a visual-inertial optimizer solves a dense SPD system of size $n=300$ every 33 ms. Estimate flops for Cholesky versus LU versus QR, the time at 5 GFLOP/s, and say what changes if the matrix is sparse.
11. **(Mini-project)** Reproduce the table of this lesson for degrees 3 to 12 on your machine, add a column for `jacobiSvd().solve` and one for fitting on $t\in[-1,1]$, and write down the degree at which each method's error first exceeds $10^{-6}$.

## Reference implementation

The code below is the library of the lab: Vandermonde design matrix, QR and normal-equation solvers, residual, condition number and a polynomial fit. Compile with `g++ -std=c++17 -O2 -Wall -Wextra -I/usr/include/eigen3 ref.cpp` (install with `sudo apt install libeigen3-dev`).

```cpp
// CPP11 reference: least squares with Eigen, three ways to see numerical stability.
#include <Eigen/Dense>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

using Eigen::MatrixXd;
using Eigen::VectorXd;

// Design matrix with columns t^0, t^1, ..., t^degree.
MatrixXd vandermonde(const std::vector<double>& t, int degree) {
  if (degree < 0) throw std::invalid_argument("degree must be >= 0");
  MatrixXd A(static_cast<Eigen::Index>(t.size()), degree + 1);
  for (Eigen::Index i = 0; i < A.rows(); ++i) {
    double p = 1.0;
    for (int j = 0; j <= degree; ++j) {
      A(i, j) = p;
      p *= t[static_cast<std::size_t>(i)];
    }
  }
  return A;
}

static void check_shapes(const MatrixXd& A, const VectorXd& b) {
  if (A.rows() != b.size()) throw std::invalid_argument("A and b have different row counts");
  if (A.rows() < A.cols()) throw std::invalid_argument("underdetermined system");
}

// min ||Ax - b||_2 by column-pivoting Householder QR (stable).
VectorXd least_squares_qr(const MatrixXd& A, const VectorXd& b) {
  check_shapes(A, b);
  return A.colPivHouseholderQr().solve(b);
}

// Same problem through the normal equations A^T A x = A^T b (squares the condition number).
VectorXd least_squares_normal(const MatrixXd& A, const VectorXd& b) {
  check_shapes(A, b);
  return (A.transpose() * A).ldlt().solve(A.transpose() * b);
}

double residual_norm(const MatrixXd& A, const VectorXd& x, const VectorXd& b) {
  return (A * x - b).norm();
}

// sigma_max / sigma_min; +infinity if the smallest singular value is exactly 0.
double condition_number(const MatrixXd& A) {
  Eigen::JacobiSVD<MatrixXd> svd(A);
  const VectorXd s = svd.singularValues();
  const double smin = s(s.size() - 1);
  return smin == 0.0 ? std::numeric_limits<double>::infinity() : s(0) / smin;
}

// Coefficients c0..c_degree of the least-squares polynomial through (t, y).
std::vector<double> polyfit(const std::vector<double>& t, const std::vector<double>& y, int degree) {
  if (t.size() != y.size()) throw std::invalid_argument("t and y differ in length");
  const VectorXd b = Eigen::Map<const VectorXd>(y.data(), static_cast<Eigen::Index>(y.size()));
  const VectorXd x = least_squares_qr(vandermonde(t, degree), b);
  return std::vector<double>(x.data(), x.data() + x.size());
}

// ---- self-test
int main() {
  MatrixXd A(3, 2);
  A << 1, 0, 1, 1, 1, 2;
  VectorXd b(3);
  b << 1, 2, 2;
  const VectorXd x = least_squares_qr(A, b);
  if (std::fabs(x(0) - 7.0 / 6.0) > 1e-12 || std::fabs(x(1) - 0.5) > 1e-12) return 1;
  if (std::fabs(residual_norm(A, x, b) - std::sqrt(6.0) / 6.0) > 1e-12) return 2;
  if (std::fabs(condition_number(Eigen::Vector2d(1, 10).asDiagonal()) - 10.0) > 1e-12) return 3;
  std::cout << "CPP11 reference self-test passed\n";
}
```

The Python oracle for the noisy-line dataset of exercise 7:

```python
import numpy as np
t = np.arange(10.0)
y = np.array([1.1, 2.9, 5.2, 7.1, 8.8, 11.2, 13.1, 14.8, 17.1, 19.0])
A = np.vander(t, 2, increasing=True)           # columns 1, t
x, res, rank, sv = np.linalg.lstsq(A, y, rcond=None)
print("x =", x)
print("residual norm =", np.linalg.norm(A @ x - y))
print("cond(A) =", np.linalg.cond(A))
```

Output of the oracle, and of the C++ functions on the same data: `x = [1.06, 1.99333333]`, residual norm `0.4442221666`, `cond(A) = 10.1722753`.

## Independent practice

### Goal

Implement dense least squares with Eigen two ways, verify them against exact hand-computed cases and a Python oracle, and measure how conditioning controls accuracy.

### Setup

`g++` with C++17 and Eigen 3 (`sudo apt install libeigen3-dev`; header-only). Python 3 with NumPy for the oracle. Save the starter code and the tests below it as `lab.cpp`; build with `g++ -std=c++17 -O1 -g -Wall -Wextra -I/usr/include/eigen3 -fsanitize=address,undefined lab.cpp -o lab && ./lab`.

### Tasks

1. Implement `vandermonde` and check by hand the row for $t=3$, degree 2: $(1,3,9)$.
2. Implement `least_squares_qr`, `residual_norm` and the shape checks; verify the $[7/6, 1/2]$ example from the tests.
3. Implement `least_squares_normal`; confirm both give the same answer on a well-conditioned random problem.
4. Implement `condition_number` with `JacobiSVD` (singular values come sorted in decreasing order).
5. Implement `polyfit` and run it on the 10-point dataset of exercise 7; compare with `oracle.py`.
6. Reproduce the degree sweep (3, 6, 9, 12) in a small `main`, printing $\kappa$, the QR error and the normal-equation error; confirm the error ratio grows roughly like $\kappa$.

### Starter code

```cpp
#include <Eigen/Dense>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>

using Eigen::MatrixXd;
using Eigen::VectorXd;

// Design matrix with columns t^0, t^1, ..., t^degree (one row per t). degree < 0 -> std::invalid_argument.
MatrixXd vandermonde(const std::vector<double>& t, int degree) { throw std::logic_error("NotImplemented"); }

// min ||Ax - b||_2 using Householder QR with column pivoting (A.colPivHouseholderQr().solve(b)).
// Throws std::invalid_argument if A.rows() != b.size() or A.rows() < A.cols().
VectorXd least_squares_qr(const MatrixXd& A, const VectorXd& b) { throw std::logic_error("NotImplemented"); }

// Same problem through the normal equations (A^T A) x = A^T b solved with .ldlt(). Same exceptions.
VectorXd least_squares_normal(const MatrixXd& A, const VectorXd& b) { throw std::logic_error("NotImplemented"); }

// Euclidean norm of the residual A x - b.
double residual_norm(const MatrixXd& A, const VectorXd& x, const VectorXd& b) { throw std::logic_error("NotImplemented"); }

// sigma_max / sigma_min from the singular values (Eigen::JacobiSVD); +infinity if sigma_min == 0.
double condition_number(const MatrixXd& A) { throw std::logic_error("NotImplemented"); }

// Coefficients c0..c_degree of the least-squares polynomial through the points (t[i], y[i]),
// computed with least_squares_qr. std::invalid_argument if t and y have different lengths.
std::vector<double> polyfit(const std::vector<double>& t, const std::vector<double>& y, int degree) {
  throw std::logic_error("NotImplemented");
}
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
  // 1. hand-computed least squares: A = [[1,0],[1,1],[1,2]], b = [1,2,2]
  //    normal equations [[3,3],[3,5]] x = [5,6] -> x = [7/6, 1/2], residual = [1/6, -1/3, 1/6], norm sqrt(6)/6
  MatrixXd A(3, 2);
  A << 1, 0, 1, 1, 1, 2;
  VectorXd b(3);
  b << 1, 2, 2;
  for (const VectorXd& x : {least_squares_qr(A, b), least_squares_normal(A, b)}) {
    CHECK(std::fabs(x(0) - 7.0 / 6.0) < 1e-12 && std::fabs(x(1) - 0.5) < 1e-12);
    CHECK(std::fabs(residual_norm(A, x, b) - std::sqrt(6.0) / 6.0) < 1e-12);
  }
  // 2. optimality: the residual is orthogonal to the columns of A
  VectorXd x = least_squares_qr(A, b);
  CHECK((A.transpose() * (A * x - b)).norm() < 1e-12);
  // 3. vandermonde and exact polynomial recovery: y = 1 + 2t exactly
  MatrixXd V = vandermonde({0.0, 1.0, 2.0, 3.0}, 2);
  CHECK(V.rows() == 4 && V.cols() == 3 && V(3, 0) == 1.0 && V(3, 1) == 3.0 && V(3, 2) == 9.0);
  std::vector<double> c = polyfit({0, 1, 2, 3}, {1, 3, 5, 7}, 1);
  CHECK(c.size() == 2 && std::fabs(c[0] - 1.0) < 1e-12 && std::fabs(c[1] - 2.0) < 1e-12);
  // 4. condition number: diagonal matrix, identity, singular matrix
  CHECK(std::fabs(condition_number(Eigen::Vector2d(1, 10).asDiagonal()) - 10.0) < 1e-12);
  CHECK(std::fabs(condition_number(MatrixXd::Identity(4, 4)) - 1.0) < 1e-12);
  MatrixXd S(2, 2);
  S << 1, 2, 2, 4;
  CHECK(condition_number(S) > 1e15);
  // 5. input validation
  CHECK(throws<std::invalid_argument>([&] { least_squares_qr(A, VectorXd::Zero(2)); }));
  CHECK(throws<std::invalid_argument>([&] { least_squares_qr(MatrixXd::Zero(2, 3), VectorXd::Zero(2)); }));
  CHECK(throws<std::invalid_argument>([] { polyfit({0, 1}, {1}, 1); }));
  CHECK(throws<std::invalid_argument>([] { vandermonde({0, 1}, -1); }));
  // 6. both solvers agree on a well-conditioned random problem
  std::mt19937 g(5);
  std::normal_distribution<double> n01(0.0, 1.0);
  MatrixXd R(30, 4);
  VectorXd rb(30);
  for (int i = 0; i < 30; ++i) { rb(i) = n01(g); for (int j = 0; j < 4; ++j) R(i, j) = n01(g); }
  CHECK((least_squares_qr(R, rb) - least_squares_normal(R, rb)).norm() < 1e-10);
  CHECK((R.transpose() * (R * least_squares_qr(R, rb) - rb)).norm() < 1e-10);
  // 7. stability: degree-9 polynomial on 50 points in [0,1]; cond(A) is about 3.6e6
  std::vector<double> t(50);
  for (int i = 0; i < 50; ++i) t[i] = i / 49.0;
  MatrixXd A9 = vandermonde(t, 9);
  VectorXd c9(10);
  for (int j = 0; j < 10; ++j) c9(j) = (j % 2 ? -1.0 : 1.0) * (1.0 + 0.1 * j);
  VectorXd y9 = A9 * c9;
  CHECK(condition_number(A9) > 1e6 && condition_number(A9) < 1e7);
  double err_qr = (least_squares_qr(A9, y9) - c9).norm();
  double err_ne = (least_squares_normal(A9, y9) - c9).norm();
  CHECK(err_qr < 1e-8);                 // error ~ cond * eps
  CHECK(err_ne > 100.0 * err_qr);       // error ~ cond^2 * eps: the normal equations lose digits
  std::cout << "all tests passed\n";
}
```

### Expected output

```
all tests passed
```

and for the sweep (3 significant digits; your last digits can differ): degree 9 gives `cond 3.56e+06`, QR error of order `1e-11`, and normal-equation error of order `1e-4`.

### Extension challenge

Add ridge regression `ridge(A, b, lambda)` through an augmented QR (stack $\sqrt\lambda I$ under $A$) and show that it stabilizes the degree-12 fit; or implement a Householder QR yourself and compare with Eigen on the test cases.

### Library track

The lab already uses Eigen. The independent library is NumPy (`pip install numpy`), the usual oracle: reproduce the whole degree table in Python with `np.vander`, `np.linalg.qr`, the normal equations and `np.linalg.lstsq`, and compare it with your C++ sweep (same `c_true`, same 50 points). The last block shows the remedies from the theory section with `numpy.polynomial.chebyshev`.

```python
import numpy as np

t = np.linspace(0.0, 1.0, 50)                         # 50 equally spaced points in [0, 1]
print("deg   cond(A)   QR err    normal-eq err   lstsq(SVD) err")
for d in (3, 6, 9, 12):
    A = np.vander(t, d + 1, increasing=True)          # columns 1, t, ..., t^d  (same as vandermonde)
    c_true = np.array([(-1.0) ** j * (1.0 + 0.1 * j) for j in range(d + 1)])
    y = A @ c_true                                    # noise-free data
    Q, R = np.linalg.qr(A)                            # thin QR
    x_qr = np.linalg.solve(R, Q.T @ y)                # R x = Q^T y
    x_ne = np.linalg.solve(A.T @ A, A.T @ y)          # normal equations
    x_svd = np.linalg.lstsq(A, y, rcond=None)[0]      # SVD based (what numpy uses)
    err = lambda x: np.linalg.norm(x - c_true)
    print(f"{d:3d}  {np.linalg.cond(A):9.2e}  {err(x_qr):8.1e}  {err(x_ne):12.1e}  {err(x_svd):12.1e}")
    if d == 9:
        assert err(x_ne) > 100 * err(x_qr)            # the lab's stability test
        assert 1e6 < np.linalg.cond(A) < 1e7

# centering/scaling t to [-1, 1] and the Chebyshev basis (numpy.polynomial) remove the problem
s = 2 * t - 1
print("cond monomial [0,1]  :", f"{np.linalg.cond(np.vander(t, 13, increasing=True)):.1e}")
print("cond monomial [-1,1] :", f"{np.linalg.cond(np.vander(s, 13, increasing=True)):.1e}")
print("cond Chebyshev [-1,1]:", f"{np.linalg.cond(np.polynomial.chebyshev.chebvander(s, 12)):.1e}")

# the optimality check of the Verification section: A^T r must be ~ 0
A = np.vander(np.arange(10.0), 2, increasing=True)
y = np.array([1.1, 2.9, 5.2, 7.1, 8.8, 11.2, 13.1, 14.8, 17.1, 19.0])
x = np.linalg.lstsq(A, y, rcond=None)[0]
assert np.allclose(x, [1.06, 1.99333333333], atol=1e-9) and np.linalg.norm(A.T @ (A @ x - y)) < 1e-12
print("library track ok")
```

Expected: $\kappa$ values 1.2e2, 2.0e4, 3.6e6, 6.8e8 (identical to the C++ run), QR errors near $\kappa\epsilon$ and normal-equation errors near $\kappa^2\epsilon$ (the last digits differ between NumPy/LAPACK and Eigen), condition numbers about 6.8e8, 1.6e4 and 2.5 for the monomial basis on $[0,1]$, the monomial basis on $[-1,1]$ and the Chebyshev basis, then `library track ok`. Compare your C++ numbers with these rows and explain any difference larger than a factor of 10.

## Verification

- **Optimality check:** $\|A^\top(A\hat x-b)\|$ should be of order $\epsilon\,\|A\|\,\|r\|$, not just small in absolute terms. Always compute it.
- **Oracle check:** compare with `numpy.linalg.lstsq` on the same data; compare residual norms and fitted values first.
- **Exact cases:** problems with a known solution (data generated from known coefficients, as in the tests) turn accuracy into a number you can print.
- **Condition number:** compute `condition_number(A)` and set your tolerance as roughly $10\,\kappa\,\epsilon_{\text{mach}}$; a failing comparison with a huge $\kappa$ is expected, not a bug.
- **Sanitizers:** build with ASan/UBSan to catch the dangling `auto` expressions, and compile with `-DEIGEN_NO_DEBUG` only for benchmarks.
- **Scaling:** repeat with `t` shifted and scaled to $[-1,1]$ and check that the condition number drops.

## Failure modes

| Mistake | Observed |
|---|---|
| `auto x = A.colPivHouseholderQr().solve(b);` | `stack-use-after-scope` or garbage; use an explicit `VectorXd` |
| `A = A.transpose();` | assertion in Debug; silent wrong matrix in Release (`1 2 / 2 4`) |
| Solving by `A.inverse() * b` | slower and less accurate than `solve`; never needed |
| Normal equations on an ill-conditioned fit | error $\kappa^2\epsilon$: $4.9\times10^{-4}$ at degree 9 instead of $2.5\times10^{-11}$ |
| Monomial basis on $[0,1]$ for high degree | $\kappa$ explodes (6.8e8 at degree 12); center and scale $t$ |
| Building without `-O2` | Eigen is 10-100x slower, benchmark misleading |
| `LLT` on a matrix that is not positive definite | silently wrong unless you check `.info()` |
| Comparing coefficients with a fixed `1e-9` tolerance | false failures on ill-conditioned problems; compare residuals |
| Integer literals mixed into Eigen expressions of `double` | compile error or unexpected conversions; write `2.0` |
| Underdetermined system with QR | no unique solution; use the minimum-norm solution from SVD |

## Alternatives and trade-offs

- **QR vs normal equations vs SVD.** QR is the default for least squares (stable, fast). Normal equations are fastest ($\approx mn^2$ plus $\frac13n^3$) and fine when $\kappa$ is small, but lose accuracy. SVD is the most robust (rank-deficient, truncation, pseudo-inverse) and the slowest.
- **Dense vs sparse.** Large SLAM or bundle-adjustment problems are sparse; use `Eigen::SparseMatrix` with `SimplicialLDLT`, or specialised libraries (Ceres, g2o, GTSAM).
- **Fixed vs dynamic sizes.** `Matrix3d`, `Vector6d` avoid heap allocation and unroll loops; use dynamic sizes only when the dimension is unknown at compile time.
- **Float vs double.** `float` has about 7 digits (`1.2e-7`), which makes a condition number above $10^{4}$ already problematic; GPUs and embedded devices use it for speed, with care.
- **Eigen vs BLAS/LAPACK vs NumPy.** NumPy calls LAPACK and is the usual oracle; Eigen avoids the dependency and works with expression templates; linking to OpenBLAS/MKL helps for large matrices.
- **Direct vs iterative solvers.** Conjugate gradient and similar iterative methods avoid factorizing huge SPD systems but require a good preconditioner.

## Transfer and retention

The same ideas appear in Python (`numpy.linalg.lstsq` is SVD-based; `np.linalg.solve` is LU), in Kalman filters (use Cholesky or the Joseph form to keep covariances symmetric positive definite), in inverse kinematics (damped least squares is ridge regression, M12/R-series) and in machine learning (linear regression, ridge, and why feature scaling matters). To retain: after a week, derive the normal equations from "residual is perpendicular to the columns" and explain in two sentences why $\kappa(A^\top A)=\kappa(A)^2$; then recompute the digits-lost estimate for $\kappa=10^{8}$ for both methods.

## Exercise answers

1. $A=\begin{pmatrix}1&0\\1&1\\1&2\end{pmatrix}$, $b=(2,3,7)^\top$. $A^\top A=\begin{pmatrix}3&3\\3&5\end{pmatrix}$, $A^\top b=(12,\ 17)^\top$ ($0+3+14=17$). Determinant $6$: $a=(5\cdot12-3\cdot17)/6=9/6=1.5$, $b=(3\cdot17-3\cdot12)/6=15/6=2.5$. Fit $=(1.5,\ 4.0,\ 6.5)$; residual $A\hat x-b=(-0.5,\ 1.0,\ -0.5)$. Check: sum $=0$; $\sum t_ir_i=0+1.0-1.0=0$. Residual norm $\sqrt{1.5}=1.2247$.
2. (a) `llt()` (Cholesky; `ldlt()` is the robust variant); (b) `partialPivLu()`; (c) `householderQr()` or `colPivHouseholderQr()`; (d) `jacobiSvd()` or `bdcSvd()` (singular values give the rank; `solve` gives the minimum-norm solution) or `completeOrthogonalDecomposition()`.
3. Stable method (QR): $16-\log_{10}(3.6\times10^{6})=16-6.6\approx9$ digits. Normal equations: $\kappa^2=1.3\times10^{13}$, so $16-13.1\approx3$ digits. The measured errors in the table ($2.5\times10^{-11}$ and $4.9\times10^{-4}$) are consistent in order of magnitude.
4. Line 2: `M = M.transpose();` is an aliasing bug: Debug assertion "aliasing detected during transposition", or a silently wrong matrix in Release; fix with `M.transposeInPlace()` or `.eval()`. Line 3: `auto x = ...solve(b)` stores an expression holding a reference to the temporary decomposition: dangling, shows as garbage or ASan `stack-use-after-scope`; fix with `Eigen::VectorXd x = ...`.
5. In Debug, an assertion fires: "aliasing detected during transposition". In `-O2 -DNDEBUG`, the in-place evaluation overwrites entries it still needs and prints $\begin{pmatrix}1&2\\2&4\end{pmatrix}$ for $\begin{pmatrix}1&2\\3&4\end{pmatrix}$. Alternatives: `M.transposeInPlace();` or `M = M.transpose().eval();`. For products `C = A * B;` Eigen assumes aliasing is possible and evaluates into a temporary by default (use `.noalias()` only when you know they do not alias).
6. QR: $\approx10^{6}\times1.1\times10^{-16}=1.1\times10^{-10}$ relative error; normal equations: $10^{12}\times1.1\times10^{-16}=1.1\times10^{-4}$. The measured degree-9 errors ($\kappa=3.6\times10^{6}$) are $2.5\times10^{-11}$ (absolute, with coefficients of size about 1; the bound is $4\times10^{-10}$) and $4.9\times10^{-4}$ (bound $1.3\times10^{-3}$): both below the worst-case bounds and of the right order. The bounds are pessimistic by a small factor.
7. `A = np.vander(t, 2, increasing=True); x = np.linalg.lstsq(A, y, rcond=None)[0]`, compare `x` (expected $1.06$, $1.99333$), the residual norm ($0.44422$), and `np.linalg.cond(A)` ($10.17$) with the C++ output. Since $\kappa\approx10$, use a tight tolerance such as $10^{-12}$ relative; for ill-conditioned fits compare the residual and fitted values with tolerance $\approx\kappa\epsilon_{\text{mach}}\|y\|$.
8. With $A=U\Sigma V^\top$ (thin SVD, $V$ orthogonal), $A^\top A=V\Sigma^2V^\top$, whose eigenvalues are $\sigma_i^2$; so $\kappa_2(A^\top A)=\sigma_{\max}^2/\sigma_{\min}^2=\kappa_2(A)^2$. For QR: minimize $\|QRx-b\|$; extend $Q$ to an orthogonal matrix $[Q\ Q_\perp]$, which preserves norms: $\|QRx-b\|^2=\|Rx-Q^\top b\|^2+\|Q_\perp^\top b\|^2$. The second term does not depend on $x$, and the first is zero when $Rx=Q^\top b$, so $\hat x=R^{-1}Q^\top b$ (exists because $R$ is invertible for full column rank), and the minimal residual is $\|Q_\perp^\top b\|$.
9. $\kappa(A)=1/10^{-4}=10^{4}$; $\kappa(A^\top A)=10^{8}$. With ridge: eigenvalues $\sigma^2+\lambda$: $(1+10^{-6})/(10^{-8}+10^{-6})=1.000001/1.01\times10^{-6}\approx9.9\times10^{5}$: about 100 times better. Trade-off: larger $\lambda$ lowers variance (stable solution) but biases the solution toward zero along the weak direction; choose $\lambda$ by cross-validation or the L-curve, or use truncated SVD.
10. Cholesky $\tfrac13n^3=9\times10^{6}$ flops; LU $\tfrac23n^3=1.8\times10^{7}$; QR $\tfrac43n^3=3.6\times10^{7}$. At $5\times10^{9}$ flops/s: 1.8 ms, 3.6 ms, 7.2 ms; all fit in a 33 ms budget, but Cholesky leaves the most room. If the matrix is sparse (as in pose graphs), sparse Cholesky uses far fewer flops (depends on fill-in) and memory: $O(n)$ storage instead of $O(n^2)$.
11. A good answer includes: the table for degrees 3-12 with the error columns; SVD error comparable to QR (same order); on $[-1,1]$ the condition numbers fall (for degree 12: $1.6\times10^{4}$ instead of $6.8\times10^{8}$), so all methods are much more accurate; in the machine of this lesson (50 points, noise-free data) the first degree with error above $10^{-6}$ on $[0,1]$ is 8 for the normal equations and 15 for QR and for SVD; on $[-1,1]$ it is 14 for the normal equations while QR and SVD stay below $10^{-6}$ up to degree 16; and a remark on the machine used.

## Further reading

- [Eigen: Getting started](https://eigen.tuxfamily.org/dox/GettingStarted.html) - installation, matrices, vectors and the first program.
- [Eigen: Linear algebra and decompositions](https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html) - solving systems, least squares, and the decomposition comparison table.
- [MIT 18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/) - projections, least squares, and the SVD, with lectures and problem sets.

**More practice:** the [MIT 18.06 assignments](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/assignments/) (the projection and least-squares problem sets), the Eigen pages [Linear algebra and decompositions](https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html), [Solving linear least squares systems](https://eigen.tuxfamily.org/dox/group__LeastSquares.html), [Aliasing](https://eigen.tuxfamily.org/dox/group__TopicAliasing.html) and [Lazy evaluation and `auto`](https://eigen.tuxfamily.org/dox/TopicLazyEvaluation.html), and the NumPy docs for [`np.linalg.lstsq`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) and [Chebyshev polynomials](https://numpy.org/doc/stable/reference/routines.polynomials.chebyshev.html) (re-do the degree sweep in a better basis).