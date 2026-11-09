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
    },
    {
      "title": "Boyd and Vandenberghe: Introduction to Applied Linear Algebra (VMLS)",
      "url": "https://web.stanford.edu/~boyd/vmls/vmls.pdf"
    },
    {
      "title": "Eigen: Catalogue of dense decompositions",
      "url": "https://eigen.tuxfamily.org/dox/group__TopicLinearAlgebraDecompositions.html"
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

*Figure: Left: the residual is orthogonal to the column space. Right: measured coefficient error of QR (about kappa times 1e-16, dashed) and of the normal equations (about kappa squared times 1e-16, dashed), degrees 3, 6, 9, 12.*

```explore
{
 "title": "Digits lost: QR against the normal equations",
 "title_vi": "Chữ số bị mất: QR so với phương trình chuẩn",
 "prompt": "Predict first: for which condition number does each method run out of correct digits? Then slide log10 κ and read the two curves and the point.",
 "prompt_vi": "Dự đoán trước: với số điều kiện nào thì mỗi phương pháp hết sạch chữ số đúng? Sau đó kéo log10 κ và đọc hai đường cong cùng điểm đánh dấu.",
 "params": [
  {
   "name": "lk",
   "label": "log10 κ(A)",
   "label_vi": "log10 κ(A)",
   "min": 0,
   "max": 12,
   "step": 0.1,
   "value": 6.5
  }
 ],
 "let": [
  {
   "name": "kappa",
   "expr": "10^lk"
  },
  {
   "name": "dq",
   "expr": "max(0, 16 - lk)"
  },
  {
   "name": "dn",
   "expr": "max(0, 16 - 2*lk)"
  }
 ],
 "plot": {
  "x": {
   "name": "x",
   "min": 0,
   "max": 12,
   "label": "log10 κ(A)",
   "label_vi": "log10 κ(A)"
  },
  "y": {
   "label": "correct digits (of 16)",
   "label_vi": "chữ số đúng (trên 16)",
   "min": 0,
   "max": 16
  },
  "series": [
   {
    "expr": "max(0, 16 - x)",
    "label": "QR: 16 - log10 κ",
    "label_vi": "QR: 16 - log10 κ",
    "color": "blue"
   },
   {
    "expr": "max(0, 16 - 2*x)",
    "label": "normal equations: 16 - 2 log10 κ",
    "label_vi": "phương trình chuẩn: 16 - 2 log10 κ",
    "color": "orange"
   }
  ],
  "points": [
   {
    "x": "lk",
    "y": "dq",
    "label": "QR",
    "label_vi": "QR",
    "color": "blue"
   },
   {
    "x": "lk",
    "y": "dn",
    "label": "normal eq.",
    "label_vi": "PT chuẩn",
    "color": "orange"
   }
  ]
 },
 "readouts": [
  {
   "label": "κ(A)",
   "expr": "kappa",
   "unit": "",
   "digits": 0
  },
  {
   "label": "digits kept by QR",
   "label_vi": "chữ số QR giữ lại",
   "expr": "dq",
   "unit": "",
   "digits": 1
  },
  {
   "label": "digits kept by the normal equations",
   "label_vi": "chữ số phương trình chuẩn giữ lại",
   "expr": "dn",
   "unit": "",
   "digits": 1
  }
 ]
}
```

**Predict before you compute.** You fit a straight line to four points and then a degree-12 polynomial to 50 points, both with exactly the same code, using data that contain no noise at all, so the right answer is known. Before reading on, predict how many correct digits each fit returns with a good method and with a careless one. The slider above shows the rule that decides it.

**A picture to hold on to.** Least squares is a shadow. The vector $b$ is a point in space; the columns of $A$ span a plane; the fitted values are the shadow of $b$ on that plane, and the residual is the line from $b$ down to the shadow, which meets the plane at a right angle. If the two columns of $A$ point in clearly different directions, the plane is well defined and a slight shake of $b$ moves the shadow slightly. If the two columns are almost parallel, the plane is a sliver; describing the shadow as "so much of column 1 plus so much of column 2" now needs huge opposite coefficients, and tiny errors in the shadow turn into large errors in the coefficients. That sensitivity is the condition number, and it is a property of the problem, not of the code.

**Answer to the prediction.** The straight line returns about 15 correct digits; the degree-12 polynomial about 8 with QR and none with the normal equations (error 3.8, table below). The data are perfect in both cases: what changed is how sensitive the answer is to rounding.

**The wrong intuitions.** "More digits in the output mean a more accurate answer": a solver prints 16 digits whether or not 3 of them are right. "If the fitted curve looks right, the coefficients are right": two very different coefficient vectors can give indistinguishable curves when the problem is ill-conditioned, which is why the oracle in this lesson compares residuals and fitted values. "Forming $A^\top A$ is just algebra": it squares the condition number, so it silently throws away half of your digits. And "Eigen will just do it": the library is correct, but `auto` and aliasing can make a correct expression compute something else.

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

**Example.** The matrix $M=\begin{pmatrix}1&2\\3&4\end{pmatrix}$ is transposed three ways in a build with assertions off: the aliased assignment `A = A.transpose();`, `transposeInPlace()` and `.eval()`. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -O2 -DNDEBUG -Wall -Wextra -I/usr/include/eigen3`. Which results are correct, and is any message printed for a wrong one?

```cpp
#include <Eigen/Dense>
#include <iostream>

int main() {
  Eigen::MatrixXd A(2, 2);
  A << 1, 2,
       3, 4;
  Eigen::MatrixXd B = A;
  Eigen::MatrixXd C = A;

  A = A.transpose();              // aliasing: reads and writes the same memory
  B.transposeInPlace();           // correct, in place
  C = C.transpose().eval();       // correct, through an explicit temporary

  std::cout << "aliased A:\n" << A << "\ntransposeInPlace B:\n" << B
            << "\neval() C:\n" << C << '\n';
}
```

**Solution.** The correct transpose is $\begin{pmatrix}1&3\\2&4\end{pmatrix}$. The aliased assignment writes entry $(1,0)$ from $(0,1)$ and then reads the already overwritten entry for $(0,1)$, so the 3 is lost and the printed matrix $\begin{pmatrix}1&2\\2&4\end{pmatrix}$ is symmetric by accident; `transposeInPlace()` and `.eval()` (an explicit temporary) give the correct $\begin{pmatrix}1&3\\2&4\end{pmatrix}$. No message is printed for the wrong one, because the assertion that would catch it is compiled out by `-DNDEBUG`. The program prints:

```text
aliased A:
1 2
2 4
transposeInPlace B:
1 3
2 4
eval() C:
1 3
2 4
```

### Solving linear systems

Never form an explicit inverse to solve $Ax=b$; factorize and solve. Choose by structure:

| Matrix | Decomposition (Eigen) | Cost (flops, $n\times n$) | Notes |
|---|---|---|---|
| general square | `partialPivLu()` | $\tfrac23n^3$ | fast, stable in practice |
| symmetric positive definite (covariances, normal equations) | `llt()` / `ldlt()` | $\tfrac13n^3$ | Cholesky; fails/flags if not SPD |
| tall, full rank, least squares | `householderQr()` / `colPivHouseholderQr()` | $2mn^2-\tfrac23n^3$ | stable, detects rank with pivoting |
| rank-deficient, or you need $\sigma$ | `jacobiSvd()` / `bdcSvd()` | larger | most robust; gives the condition number |

At $n=1000$, Cholesky is $\approx3.3\times10^{8}$ flops, about 33 ms at 10 GFLOP/s; at $n=6$ it is about 72 flops, negligible.

**Example.** Three masses joined by springs give a symmetric positive definite stiffness matrix $K$ (N/m) with eigenvalues 54.6, 268.0 and 427.4. For forces $f=(2,0,5)$ N the displacements $x$ (m) are computed by Cholesky (`llt()`), by LU (`partialPivLu()`) and by the explicit inverse. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. What is $\kappa(K)$, what are the displacements and residuals, and what separates the three methods?

```cpp
#include <Eigen/Dense>
#include <iomanip>
#include <iostream>

int main() {
  // Three masses on springs in a chain: symmetric positive definite stiffness matrix (N/m), forces (N).
  Eigen::Matrix3d K;
  K <<  300, -100,    0,
       -100,  250, -150,
          0, -150,  200;
  Eigen::Vector3d f(2.0, 0.0, 5.0);

  Eigen::Vector3d x_llt = K.llt().solve(f);                 // Cholesky, the SPD choice
  Eigen::Vector3d x_lu  = K.partialPivLu().solve(f);        // LU, the general choice
  Eigen::Vector3d x_inv = K.inverse() * f;                  // explicit inverse: avoid

  std::cout << std::setprecision(6);
  std::cout << "llt  x = " << x_llt.transpose() << "  residual " << (K * x_llt - f).norm() << '\n';
  std::cout << "lu   x = " << x_lu.transpose()  << "  residual " << (K * x_lu - f).norm() << '\n';
  std::cout << "inv  x = " << x_inv.transpose() << "  residual " << (K * x_inv - f).norm() << '\n';
  std::cout << "llt info() == Success: " << (K.llt().info() == Eigen::Success) << '\n';
}
```

**Solution.** The condition number is the ratio of the extreme eigenvalues, $\kappa(K)=427.4/54.6=7.8$. Cholesky costs $\tfrac13n^3=9$ flops and LU $\tfrac23n^3=18$ flops for $n=3$. The displacements $x$ (m) come out identical from all three methods, with residuals near $10^{-15}$ N. At $n=3$ and $\kappa=7.8$ nothing separates the methods; the table above gives the reasons to prefer factorizations (half the flops for Cholesky, no inverse to form) once $n$ or $\kappa$ grows. `info() == Success` confirms that the Cholesky factorization found the matrix positive definite. The program prints:

```text
llt  x = 0.0208 0.0424 0.0568  residual 1.98603e-15
lu   x = 0.0208 0.0424 0.0568  residual 1.77636e-15
inv  x = 0.0208 0.0424 0.0568  residual 1.25607e-15
llt info() == Success: 1
```

### Least squares

Given $A\in\mathbb R^{m\times n}$, $m\ge n$, find $\hat x=\arg\min\|Ax-b\|_2$. Setting the gradient to zero gives the normal equations $A^\top A\hat x=A^\top b$, equivalently $A^\top(A\hat x-b)=0$. With the thin QR factorization $A=QR$ ($Q^\top Q=I$, $R$ upper triangular) the problem becomes $R\hat x=Q^\top b$, solved by back substitution; the residual norm is $\|(I-QQ^\top)b\|$.

**Why normal equations lose accuracy.** With the SVD $A=U\Sigma V^\top$, $A^\top A=V\Sigma^2V^\top$ so $\kappa(A^\top A)=\sigma_{\max}^2/\sigma_{\min}^2=\kappa(A)^2$. A solver with error $\approx\kappa\,\epsilon_{\text{mach}}$ applied to this matrix gives $\kappa(A)^2\epsilon_{\text{mach}}$, whereas QR achieves about $\kappa(A)\epsilon_{\text{mach}}$ (for small residual problems).

**Digits.** Digits lost $\approx\log_{10}\kappa$. For $\kappa=3.6\times10^{6}$: QR keeps about $16-6.6\approx9$ digits; the normal equations keep about $16-13.1\approx3$.

**Example.** A wheel encoder reports its position $p$ (m) at $t=0,\dots,4$ s: $0.20,\,1.10,\,1.90,\,3.20,\,3.90$. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. Fit $p=p_0+vt$ by QR and by the normal equations: find the start position $p_0$ and the speed $v$, check them by hand and check that the residual is orthogonal to the columns.

```cpp
#include <Eigen/Dense>
#include <iomanip>
#include <iostream>

int main() {
  // Wheel encoder: position (m) at t = 0..4 s. Fit p = p0 + v t.
  Eigen::MatrixXd A(5, 2);
  Eigen::VectorXd p(5);
  const double t[5] = {0, 1, 2, 3, 4};
  const double y[5] = {0.20, 1.10, 1.90, 3.20, 3.90};
  for (int i = 0; i < 5; ++i) { A(i, 0) = 1.0; A(i, 1) = t[i]; p(i) = y[i]; }

  Eigen::VectorXd x_qr = A.colPivHouseholderQr().solve(p);
  Eigen::VectorXd x_ne = (A.transpose() * A).ldlt().solve(A.transpose() * p);
  Eigen::VectorXd r = p - A * x_qr;

  std::cout << std::fixed << std::setprecision(4);
  std::cout << "QR      p0, v = " << x_qr.transpose() << '\n';
  std::cout << "normal  p0, v = " << x_ne.transpose() << '\n';
  std::cout << "residual      = " << r.transpose() << '\n';
  std::cout << "||r||         = " << r.norm() << '\n';
  std::cout << std::scientific << std::setprecision(2);
  std::cout << "||A^T r||     = " << (A.transpose() * r).norm() << '\n';
}
```

**Solution.** By hand: $A^\top A=\begin{pmatrix}5&10\\10&30\end{pmatrix}$, $A^\top p=(10.3,\,30.1)^\top$, $\det=5\cdot30-10\cdot10=50$, so $p_0=(30\cdot10.3-10\cdot30.1)/50=0.16$ m and $v=(5\cdot30.1-10\cdot10.3)/50=0.95$ m/s. QR and the normal equations give $p_0=0.16$ m and $v=0.95$ m/s alike. The residual vector is orthogonal to both columns ($\|A^\top r\|\approx10^{-14}$), which is the defining property of the minimizer. The program prints:

```text
QR      p0, v = 0.1600 0.9500
normal  p0, v = 0.1600 0.9500
residual      =  0.0400 -0.0100 -0.1600  0.1900 -0.0600
||r||         = 0.2588
||A^T r||     = 6.00e-15
```

### Conditioning of polynomial fits

The Vandermonde matrix with columns $1,t,t^2,\dots,t^d$ on $[0,1]$ becomes nearly rank-deficient as $d$ grows, because high powers look alike. Measured with 50 equally spaced points:

| degree | $\kappa(A)$ | QR error | normal-equation error |
|---|---|---|---|
| 3 | 1.2e2 | 4.0e-15 | 1.2e-12 |
| 6 | 2.0e4 | 4.6e-13 | 2.1e-08 |
| 9 | 3.6e6 | 2.5e-11 | 4.9e-04 |
| 12 | 6.8e8 | 3.4e-08 | 3.8e+00 |

(errors are $\|\hat c-c_{\text{true}}\|$ for noise-free data $y=Ac_{\text{true}}$ with $c_{\text{true},j}=(-1)^j(1+0.1j)$, the same coefficients as the lab test; other coefficients give errors of the same order, and the last digits depend on the platform.) Centering and scaling $t$ to $[-1,1]$ reduces the degree-12 condition number to $1.6\times10^{4}$; orthogonal polynomial bases (Chebyshev) are better still. Remedies for near-singular problems: scale the columns, use SVD with truncation, or add Tikhonov (ridge) regularization $(A^\top A+\lambda I)x=A^\top b$.

**Example.** A degree-$d$ Vandermonde matrix is built on 21 equally spaced sample times, once on $[0,1]$ and once after mapping $t\mapsto2t-1$ onto $[-1,1]$. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. How does the condition number grow with the degree in each case?

```cpp
#include <Eigen/Dense>
#include <iostream>
#include <vector>

double cond(const Eigen::MatrixXd& A) {
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(A);
  const auto s = svd.singularValues();
  return s(0) / s(s.size() - 1);
}

Eigen::MatrixXd vander(const std::vector<double>& t, int degree) {
  Eigen::MatrixXd A(t.size(), degree + 1);
  for (std::size_t i = 0; i < t.size(); ++i) {
    double p = 1.0;
    for (int j = 0; j <= degree; ++j) { A(i, j) = p; p *= t[i]; }
  }
  return A;
}

int main() {
  std::vector<double> t01, tpm;      // 21 equally spaced sample times
  for (int i = 0; i <= 20; ++i) { t01.push_back(i / 20.0); tpm.push_back(2.0 * i / 20.0 - 1.0); }
  std::cout.precision(3);
  for (int d : {4, 8, 11})
    std::cout << "degree " << d << ": cond on [0,1] = " << cond(vander(t01, d))
              << "   cond on [-1,1] = " << cond(vander(tpm, d)) << '\n';
}
```

**Solution.** The program computes $\kappa=\sigma_{\max}/\sigma_{\min}$ from the singular values. The condition number on $[0,1]$ grows by about a factor 1000 for 4 added degrees (593 at degree 4, $6.17\times10^{5}$ at degree 8, $1.49\times10^{8}$ at degree 11), and the same data on $[-1,1]$ stay more than four orders of magnitude better at degree 11 ($8.52\times10^{3}$, a factor $1.49\times10^{8}/8.52\times10^{3}\approx1.7\times10^{4}$). Centering is free and removes most of the problem. The program prints:

```text
degree 4: cond on [0,1] = 593   cond on [-1,1] = 17.2
degree 8: cond on [0,1] = 6.17e+05   cond on [-1,1] = 529
degree 11: cond on [0,1] = 1.49e+08   cond on [-1,1] = 8.52e+03
```

### Verifying with an oracle

An independent implementation catches wiring mistakes (wrong index, transposed matrix). Compare *residual norms* and *fitted values*, not only coefficients, when the problem is ill-conditioned, since coefficients can differ in the last digits while the fit is identical. Choose tolerances from $\kappa\,\epsilon_{\text{mach}}$, not arbitrary $10^{-6}$.

**Example.** Eight calibration readings (ADC counts against a reference voltage in V) are fitted by the C++ QR solver and by the NumPy oracle `lstsq`. The C++ program is compiled as in the previous examples, then the Python program is run. Do the two solvers agree, to how many digits, and is the tolerance $10\,\kappa\,\epsilon_{\text{mach}}\|b\|$ of this section met?

```cpp
#include <Eigen/Dense>
#include <cstdio>

int main() {
  // 8 calibration readings (ADC counts) against a reference voltage.
  const double v[8] = {0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0};
  const double c[8] = {412, 830, 1241, 1668, 2074, 2490, 2911, 3322};
  Eigen::MatrixXd A(8, 2);
  Eigen::VectorXd b(8);
  for (int i = 0; i < 8; ++i) { A(i, 0) = 1.0; A(i, 1) = v[i]; b(i) = c[i]; }
  Eigen::VectorXd x = A.colPivHouseholderQr().solve(b);
  std::printf("x = [%.12f, %.12f]\n", x(0), x(1));
  std::printf("residual norm = %.12f\n", (A * x - b).norm());
}
```

```python
import numpy as np
v = np.arange(0.5, 4.01, 0.5)
c = np.array([412, 830, 1241, 1668, 2074, 2490, 2911, 3322.0])
A = np.vander(v, 2, increasing=True)
x = np.linalg.lstsq(A, c, rcond=None)[0]
print("x = [%.12f, %.12f]" % tuple(x))
print("residual norm = %.12f" % np.linalg.norm(A @ x - c))
print("cond(A) = %.4f, tolerance 10*cond*eps*||b|| = %.2e" % (np.linalg.cond(A), 10*np.linalg.cond(A)*np.finfo(float).eps*np.linalg.norm(c)))
```

**Solution.** The first block is the C++ program and the second the Python oracle. The coefficients agree to 11 digits, not 16: they differ by about $10^{-12}$ in the last printed digits, while the residual norm agrees to all 12 printed digits. With $\kappa(A)=6.28$ and $\|b\|\approx5.9\times10^{3}$ the tolerance is $10\,\kappa\,\epsilon_{\text{mach}}\|b\|=10\cdot6.28\cdot2.2\times10^{-16}\cdot5.9\times10^{3}=8.3\times10^{-11}$, met with a wide margin by the difference of about $10^{-12}$. The residual norm 9.72 is large because the converter is not linear; that is a property of the data, and the oracle shows the same value. The C++ program prints the first output block and the Python program the second:

```text
x = [-2.642857142857, 831.619047619048]
residual norm = 9.719886340703
```

```text
x = [-2.642857142856, 831.619047619048]
residual norm = 9.719886340703
cond(A) = 6.2781, tolerance 10*cond*eps*||b|| = 8.27e-11
```

### Least squares by projection, and a numerical trap

The least-squares solution $\hat x$ is characterized by $A^\top(A\hat x-b)=0$: the residual $r=b-A\hat x$ is orthogonal to every column of $A$ (Boyd and Vandenberghe, VMLS, §12.2, normal equations (12.4)). With $A=QR$ the columns of $Q$ span the same space, so $A\hat x=QQ^\top b$ (VMLS, Exercise 12.8). Since $r\perp A\hat x$, Pythagoras gives $\|b\|^2=\|A\hat x\|^2+\|r\|^2$, and $\|A\hat x\|^2=\|Q^\top b\|^2$ because $Q$ has orthonormal columns. Therefore
$$\|r\|^2=\|b\|^2-\|Q^\top b\|^2 .$$
This identity is exact, but numerically dangerous. Both terms are computed with absolute error about $\epsilon_{\text{mach}}\|b\|^2$, so when the fit is good ($\|r\|\ll\|b\|$) the *difference* has relative error about $\epsilon_{\text{mach}}\|b\|^2/\|r\|^2$: all significant digits are lost once $\|r\|/\|b\|\lesssim\sqrt{\epsilon_{\text{mach}}}\approx10^{-8}$. Compute the residual vector $b-A\hat x$ and take its norm instead (Exercise 12). The same pattern, "subtract two big nearly equal numbers", is what makes the normal equations fragile.

**Example.** Fit a constant to the three readings $b=(2\cdot10^{8}+2,\ 2\cdot10^{8},\ 2\cdot10^{8}-2)$. Compiled with g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`. What is the squared residual $\|r\|^2$ computed by the Pythagorean formula $\|b\|^2-\|Q^\top b\|^2$, and what by forming the residual vector first?

```cpp
#include <cmath>
#include <cstdio>

int main() {
  // Fit a constant to b: A = (1,1,1)^T, Q = A/sqrt(3), exact residual r = b - mean(b).
  const double b[3] = {2e8 + 2, 2e8, 2e8 - 2};
  double bb = 0.0, qb = 0.0, mean = 0.0;
  for (double x : b) { bb += x * x; qb += x / std::sqrt(3.0); mean += x / 3.0; }
  const double trap = bb - qb * qb;            // ||b||^2 - ||Q^T b||^2
  double direct = 0.0;
  for (double x : b) direct += (x - mean) * (x - mean);   // ||b - A xhat||^2
  std::printf("||b||^2 - ||Q^T b||^2 = %.1f\n", trap);
  std::printf("||b - A xhat||^2      = %.1f\n", direct);
}
```

**Solution.** The exact residual is $r=(2,0,-2)$, so $\|r\|^2=8$. The Pythagorean formula subtracts two numbers near $1.2\cdot10^{17}$, where doubles are spaced 16 apart, and returns 0.0; forming the residual vector first returns 8.0. The predicted relative error $\epsilon\|b\|^2/\|r\|^2=1.1\cdot10^{-16}\cdot1.2\cdot10^{17}/8\approx1.6$ already exceeds 100%, which matches the lost answer. The program prints:

```text
||b||^2 - ||Q^T b||^2 = 0.0
||b - A xhat||^2      = 8.0
```

### Gram (normal-equation) method versus QR: cost and accuracy

Forming $G=A^\top A$ exploiting symmetry costs about $mn^2$ flops and a Cholesky factorization $\tfrac13n^3$, so the Gram method costs $mn^2+\tfrac13n^3$, while Householder QR costs $2mn^2-\tfrac23n^3$ (the lesson's table). For $m\gg n$ the Gram method is about twice as fast, for $m\approx n$ only about 1.1 to 1.4 times faster (VMLS, Exercise 12.16, whose remark says the gain is too small to matter in practice). Accuracy decides. A backward-stable solver on $G$ has relative error $\approx\kappa(G)\epsilon_{\text{mach}}=\kappa(A)^2\epsilon_{\text{mach}}$, against $\kappa(A)\epsilon_{\text{mach}}$ for QR. Eigen's catalogue of dense decompositions reflects this: `LLT` is "very fast" but its accuracy "depends on condition number", while `ColPivHouseholderQR` is "fast" with "good" reliability and is rank-revealing (Eigen, *Catalogue of dense decompositions*). A usable rule: the normal equations are acceptable only when $\kappa(A)^2\epsilon_{\text{mach}}$ is well below the accuracy you need, that is $\kappa(A)\lesssim10^{3}$ to $10^{4}$ for six correct digits; their strength is when $G$ is cheap to obtain (for example accumulated over streaming data).

![Flop ratio of QR to the Gram method against m over n, and the correct digits of both for a degree-8 fit](/lesson-figures/CPP11-2.svg)

*Figure: Left: QR costs at most twice the flops of the Gram method (ratio 1 for square, 1.99 at m = 2000, n = 8). Right: that factor 2 buys about 5 more correct digits at kappa = 6.16e5.*

**Example.** A degree-8 fit to 40 points of $[0,1]$ has known coefficients $c_j=(-1)^j(2+0.5j)$ ($\|c\|=12.6$) and noise-free data. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. How accurately do QR and the Gram (normal equations) method return the coefficients, how does that compare with $\kappa\epsilon$ and $\kappa^2\epsilon$, and what does QR cost in flops for a $2000\times8$ problem?

```cpp
#include <Eigen/Dense>
#include <cstdio>
#include <vector>

int main() {
  // Fit degree 8 to 40 points of [0,1], noise-free data from known coefficients.
  const int m = 40, d = 8;
  Eigen::MatrixXd A(m, d + 1);
  for (int i = 0; i < m; ++i) {
    const double t = i / double(m - 1);
    double p = 1.0;
    for (int j = 0; j <= d; ++j) { A(i, j) = p; p *= t; }
  }
  Eigen::VectorXd c(d + 1);
  for (int j = 0; j <= d; ++j) c(j) = (j % 2 ? -1.0 : 1.0) * (2.0 + 0.5 * j);
  Eigen::VectorXd y = A * c;
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(A);
  const double k = svd.singularValues()(0) / svd.singularValues()(d);
  const double e_qr = (A.householderQr().solve(y) - c).norm();
  const double e_ne = ((A.transpose() * A).llt().solve(A.transpose() * y) - c).norm();
  std::printf("cond(A) = %.3g, kappa*eps = %.1e, kappa^2*eps = %.1e\n", k, k * 1.1e-16, k * k * 1.1e-16);
  std::printf("QR error   %.1e\nGram error %.1e\n", e_qr, e_ne);
  const double mm = 2000, nn = 8;     // flop model for a tall problem
  std::printf("flops, m=2000, n=8: Gram %.3g, QR %.3g, ratio %.2f\n",
              mm * nn * nn + nn * nn * nn / 3, 2 * mm * nn * nn - 2 * nn * nn * nn / 3,
              (2 * mm * nn * nn - 2 * nn * nn * nn / 3) / (mm * nn * nn + nn * nn * nn / 3));
}
```

**Solution.** The matrix has $\kappa(A)=6.16\times10^{5}$, so $\kappa\epsilon=6.16\times10^{5}\cdot1.1\times10^{-16}=6.8\times10^{-11}$ and $\kappa^2\epsilon=4.2\times10^{-5}$. QR returns the coefficients to $1.3\times10^{-10}$ (about $10^{-11}$ relative), the Gram method to $1.2\times10^{-5}$ (about $10^{-6}$ relative): the measured errors follow $\kappa\epsilon$ and $\kappa^2\epsilon$ to within a factor of 2 to 4. The price of QR in flops for a $2000\times8$ problem is a factor 1.99, which is irrelevant at this size. The program prints:

```text
cond(A) = 6.16e+05, kappa*eps = 6.8e-11, kappa^2*eps = 4.2e-05
QR error   1.3e-10
Gram error 1.2e-05
flops, m=2000, n=8: Gram 1.28e+05, QR 2.56e+05, ratio 1.99
```

### Iterative least squares: the Richardson iteration

For very large or sparse $A$ you may only be able to multiply by $A$ and $A^\top$. The iteration $x_{k+1}=x_k-\mu A^\top(Ax_k-b)$ (VMLS, Exercise 12.13) has $\hat x$ as its fixed point. Subtracting $\hat x$ and using $A^\top(A\hat x-b)=0$, the error $e_k=x_k-\hat x$ obeys $e_{k+1}=(I-\mu A^\top A)e_k$. In the right singular basis of $A=U\Sigma V^\top$ component $i$ of the error is multiplied by $1-\mu\sigma_i^2$ per step. Choose $\mu=1/\sigma_{\max}^2$: the factors lie in $[0,\,1-1/\kappa^2]$ with $\kappa=\sigma_{\max}/\sigma_{\min}$, so
$$\|e_k\|\le\Big(1-\frac1{\kappa^2}\Big)^k\|e_0\|,\qquad k\ge\frac{\ln(\text{tol})}{\ln(1-1/\kappa^2)}\approx\kappa^2\ln\frac1{\text{tol}}.$$
The square of the condition number appears again, now as an iteration count: reducing the error by $10^{-6}$ needs about 1375 iterations for $\kappa=10$ and about 138,000 for $\kappa=100$. This is why preconditioning, or a Krylov method such as conjugate gradients on the same normal equations, is used in practice; Richardson is the simplest member of the family and the right model for understanding why conditioning controls everything in this lesson.

![Richardson error bound against iteration count for kappa 2, 4 and 6](/lesson-figures/CPP11-3.svg)

*Figure: Doubling kappa multiplies the iteration count by about 4: 49, 215 and 491 steps reach 1e-6.*

**Example.** A $40\times4$ matrix is built with singular values $1,\ 0.75,\ 0.5,\ 1/6$, and gradient descent with step $\mu=1/\sigma_{\max}^2=1$ runs until the error has fallen by $10^{-6}$. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. How many steps does the bound predict, how many does the loop take, and how many flops does the run cost?

```cpp
#include <Eigen/Dense>
#include <cmath>
#include <cstdio>
#include <random>

int main() {
  // 40x4 matrix with singular values 1, 0.75, 0.5, 1/6 so that kappa = 6.
  std::mt19937 g(3);
  std::normal_distribution<double> n01;
  Eigen::MatrixXd G = Eigen::MatrixXd::NullaryExpr(40, 4, [&] { return n01(g); });
  Eigen::MatrixXd U = Eigen::HouseholderQR<Eigen::MatrixXd>(G).householderQ() * Eigen::MatrixXd::Identity(40, 4);
  Eigen::MatrixXd V = Eigen::HouseholderQR<Eigen::MatrixXd>(Eigen::MatrixXd::NullaryExpr(4, 4, [&] { return n01(g); })).householderQ();
  Eigen::Vector4d s(1.0, 0.75, 0.5, 1.0 / 6.0);
  Eigen::MatrixXd A = U * s.asDiagonal() * V.transpose();
  Eigen::VectorXd b = Eigen::VectorXd::NullaryExpr(40, [&] { return n01(g); });
  const Eigen::VectorXd xhat = A.colPivHouseholderQr().solve(b);

  const double kappa = 6.0, mu = 1.0;        // mu = 1/sigma_max^2 = 1
  Eigen::VectorXd x = Eigen::VectorXd::Zero(4);
  const double e0 = (x - xhat).norm();
  int k = 0;
  while ((x - xhat).norm() > 1e-6 * e0) { x -= mu * A.transpose() * (A * x - b); ++k; }
  std::printf("iterations to reach 1e-6: %d\n", k);
  std::printf("bound ln(1e-6)/ln(1-1/kappa^2) = %.1f\n", std::log(1e-6) / std::log(1 - 1 / (kappa * kappa)));
  std::printf("kappa^2 ln(1e6) = %.1f\n", kappa * kappa * std::log(1e6));
}
```

```explore
{
 "title": "Richardson iteration: error against step count",
 "title_vi": "Phép lặp Richardson: sai số theo số bước",
 "prompt": "Predict first: if κ doubles, by what factor does the number of steps to reach the same tolerance change? Then set κ = 3, then κ = 6, and compare the iteration counts.",
 "prompt_vi": "Dự đoán trước: nếu κ tăng gấp đôi thì số bước để đạt cùng dung sai đổi theo hệ số nào? Sau đó đặt κ = 3, rồi κ = 6, và so sánh số bước lặp.",
 "params": [
  {
   "name": "kappa",
   "label": "κ(A)",
   "label_vi": "κ(A)",
   "min": 1.5,
   "max": 12,
   "step": 0.5,
   "value": 6
  },
  {
   "name": "te",
   "label": "tolerance exponent (tol = 10^-n)",
   "label_vi": "số mũ dung sai (tol = 10^-n)",
   "min": 2,
   "max": 10,
   "step": 1,
   "value": 6
  }
 ],
 "let": [
  {
   "name": "lr",
   "expr": "log10(1 - 1/kappa^2)"
  },
  {
   "name": "kn",
   "expr": "ceil(-te/lr)"
  }
 ],
 "plot": {
  "x": {
   "name": "k",
   "min": 0,
   "max": 1600,
   "label": "iteration k",
   "label_vi": "bước lặp k"
  },
  "y": {
   "label": "log10 of the error bound ratio",
   "label_vi": "log10 của tỉ số cận sai số",
   "min": -10,
   "max": 0
  },
  "series": [
   {
    "expr": "k*lr",
    "label": "(1 - 1/κ²)^k",
    "label_vi": "(1 - 1/κ²)^k",
    "color": "blue"
   },
   {
    "expr": "-te",
    "label": "tolerance",
    "label_vi": "dung sai",
    "color": "amber"
   }
  ],
  "points": [
   {
    "x": "kn",
    "y": "-te",
    "label": "steps needed",
    "label_vi": "số bước cần",
    "color": "orange"
   }
  ]
 },
 "readouts": [
  {
   "label": "steps needed k",
   "label_vi": "số bước cần k",
   "expr": "kn",
   "unit": "",
   "digits": 0
  },
  {
   "label": "κ² · ln(10^n)",
   "label_vi": "κ² · ln(10^n)",
   "expr": "kappa^2*te*ln(10)",
   "unit": "",
   "digits": 0
  }
 ]
}
```

**Solution.** The condition number is $\kappa=1/(1/6)=6$. The bound gives $k\ge\ln(10^{-6})/\ln(1-1/36)=490.4$ steps (the shortcut $\kappa^2\ln10^6=497.4$); the loop stops after 488, just inside the bound, because the random initial error has little component along the slowest singular direction. Each step costs two matrix-vector products, $2\cdot2\cdot40\cdot4=640$ flops, so the whole run takes about $488\cdot640\approx3.1\times10^{5}$ flops. The program prints:

```text
iterations to reach 1e-6: 488
bound ln(1e-6)/ln(1-1/kappa^2) = 490.4
kappa^2 ln(1e6) = 497.4
```

### Conditioning versus stability: what a condition number bounds

Two ideas are often confused. The **conditioning** of a problem measures how much the exact answer changes when the input changes slightly; it belongs to the problem. The **stability** of an algorithm measures whether the computed answer is the exact answer to a slightly perturbed input; it belongs to the method. For $Ax=b$ with invertible $A$, suppose the right-hand side is perturbed to $b+\delta b$ and $A(x+\delta x)=b+\delta b$. Then $\delta x=A^{-1}\delta b$, so $\|\delta x\|\le\|A^{-1}\|\,\|\delta b\|$; and $\|b\|=\|Ax\|\le\|A\|\,\|x\|$ gives $1/\|x\|\le\|A\|/\|b\|$. Multiplying,
$$\frac{\|\delta x\|}{\|x\|}\le\kappa(A)\,\frac{\|\delta b\|}{\|b\|},\qquad\kappa(A)=\|A\|\,\|A^{-1}\|.$$
In the 2-norm $\kappa=\sigma_{\max}/\sigma_{\min}$. The bound is *attained*: take $b$ along the left singular vector $u_{\max}$ (so $\|x\|=\|b\|/\sigma_{\max}$ is as small as possible) and $\delta b$ along $u_{\min}$ (so $\|\delta x\|=\|\delta b\|/\sigma_{\min}$ is as large as possible); the sensitivity of a single entry is the question of VMLS Exercise 11.26. A **backward-stable** algorithm returns $\hat x$ that solves $(A+E)\hat x=b$ with $\|E\|\approx\epsilon_{\text{mach}}\|A\|$. Combining the two, a backward-stable solver has forward error at most about $\kappa(A)\,\epsilon_{\text{mach}}$: the digits lost are the unavoidable $\log_{10}\kappa$, and no algorithm can do better on that input, because rounding the data to double precision is already a perturbation of that size. Normal equations are *not* backward stable for the least-squares problem: forming $A^\top A$ already perturbs the data at relative size $\epsilon_{\text{mach}}$ in a matrix whose condition number is $\kappa^2$.

**Example.** For $A=\mathrm{diag}(1,\,10^{-3})$ ($\kappa=1000$) and $b=(1,0)$, the same absolute perturbation $|\delta b|=10^{-6}$ is applied along the two singular directions. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. How large is the relative error of $x$ in each case?

```cpp
#include <Eigen/Dense>
#include <cstdio>

int main() {
  // A = diag(1, 1e-3): kappa = 1000. Perturb b along u_max or along u_min.
  Eigen::Matrix2d A = Eigen::Vector2d(1.0, 1e-3).asDiagonal();
  Eigen::Vector2d b(1.0, 0.0), x = A.partialPivLu().solve(b);
  for (int axis = 0; axis < 2; ++axis) {
    Eigen::Vector2d db = Eigen::Vector2d::Zero();
    db(axis) = 1e-6;
    Eigen::Vector2d dx = A.partialPivLu().solve(b + db) - x;
    std::printf("db along u%s: |db|/|b| = %.1e, |dx|/|x| = %.1e, ratio = %.1f\n",
                axis == 0 ? "_max" : "_min", db.norm() / b.norm(), dx.norm() / x.norm(),
                (dx.norm() / x.norm()) / (db.norm() / b.norm()));
  }
}
```

**Solution.** Along $u_{\max}$ the relative error of $x$ equals the relative error of $b$ (ratio 1.0). Along $u_{\min}$ it is 1000 times larger: $10^{-6}$ becomes $10^{-3}$, which is the bound $\kappa\,\|\delta b\|/\|b\|=1000\cdot10^{-6}$ reached exactly. The same matrix and the same algorithm give both results; only the direction of the error differs. The program prints:

```text
db along u_max: |db|/|b| = 1.0e-06, |dx|/|x| = 1.0e-06, ratio = 1.0
db along u_min: |db|/|b| = 1.0e-06, |dx|/|x| = 1.0e-03, ratio = 1000.0
```

### When the normal equations break exactly: the Läuchli matrix

Take $A=\begin{pmatrix}1&1\\\delta&0\\0&\delta\end{pmatrix}$. Then $A^\top A=\begin{pmatrix}1+\delta^2&1\\1&1+\delta^2\end{pmatrix}$ with $\det=\delta^2(2+\delta^2)$ and singular values $\sigma_{\max}=\sqrt{2+\delta^2}$, $\sigma_{\min}=\delta$, so $\kappa(A)\approx\sqrt2/\delta$: for $\delta=10^{-8}$ about $1.4\times10^{8}$, a problem that double precision solves to about 8 digits. But $1+\delta^2=1+10^{-16}$ rounds to $1$ in double precision (half a unit in the last place of 1 is $1.1\times10^{-16}$, which is larger than $10^{-16}$), the computed Gram matrix is exactly $\begin{pmatrix}1&1\\1&1\end{pmatrix}$ and is *singular*: the normal equations fail outright, not just lose digits. The information about $\delta^2$ is destroyed in the product, and QR, which never forms $A^\top A$, is unaffected (Worked example, case 2). This is the extreme version of the table in this lesson: the squared condition number $2\times10^{16}$ exceeds $1/\epsilon_{\text{mach}}$.

![Relative error of QR and the normal equations on the Läuchli matrix against delta](/lesson-figures/CPP11-5.svg)

*Figure: QR stays at rounding level while the normal equations lose accuracy like 1/delta squared and fail for delta of 1e-8 or less.*

**Example.** Take $\delta=10^{-7}$ and $b=(1,1,0)^\top$. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. What is the exact least-squares solution, and how accurate are QR and the normal equations?

```cpp
#include <Eigen/Dense>
#include <cstdio>

int main() {
  const double delta = 1e-7;
  Eigen::MatrixXd A(3, 2);
  A << 1, 1, delta, 0, 0, delta;
  Eigen::Vector3d b(1, 1, 0);
  // Exact solution from the normal equations: x1 - x2 = 1/delta, x1 + x2 = (2+delta)/(2+delta^2).
  const double s = (2 + delta) / (2 + delta * delta), d = 1 / delta;
  const Eigen::Vector2d x_exact((s + d) / 2, (s - d) / 2);
  Eigen::Vector2d x_qr = A.householderQr().solve(b);
  Eigen::Matrix2d G = A.transpose() * A;
  Eigen::Vector2d x_ne = G.ldlt().solve(A.transpose() * b);
  std::printf("kappa(A) = %.2e, kappa(G) = %.2e\n", 1.4142135623730951 / delta, 2.0 / (delta * delta));
  std::printf("exact  x = %.4f %.4f\n", x_exact(0), x_exact(1));
  std::printf("QR     x = %.4f %.4f   relative error %.1e\n", x_qr(0), x_qr(1), (x_qr - x_exact).norm() / x_exact.norm());
  std::printf("normal x = %.4f %.4f   relative error %.1e\n", x_ne(0), x_ne(1), (x_ne - x_exact).norm() / x_exact.norm());
}
```

**Solution.** The exact solution follows from $x_1-x_2=1/\delta$ and $x_1+x_2=(2+\delta)/(2+\delta^2)$ (subtract and add the two normal equations): $(5000000.5,\,-4999999.5)$. $\kappa(A)=1.41\times10^{7}$, so QR is accurate to about 9 digits (it reaches $10^{-16}$ here); $\kappa(A^\top A)=2\times10^{14}$, and the computed Gram entry $G_{00}-1=9.99\times10^{-15}$ carries a 0.08% error in $\delta^2$, which becomes a relative error $8\times10^{-4}$ in $x$ (4000 in absolute terms). One more decade of $\delta$ makes the Gram matrix exactly singular, as the figure shows. The program prints:

```text
kappa(A) = 1.41e+07, kappa(G) = 2.00e+14
exact  x = 5000000.5000 -4999999.5000
QR     x = 5000000.5000 -4999999.5000   relative error 1.3e-16
normal x = 5004000.0889 -5003999.0889   relative error 8.0e-04
```

### Rank deficiency and the truncated SVD

If the columns of $A$ are dependent (or nearly so), the least-squares minimizer is not unique. With $A=U\Sigma V^\top$ and $r$ the number of singular values kept, the *minimum-norm* least-squares solution is $\hat x=\sum_{i\le r}\frac{u_i^\top b}{\sigma_i}v_i=A^\dagger b$, $A^\dagger=V\Sigma^{+}U^\top$, where $\Sigma^{+}$ inverts the nonzero singular values and sets the others to zero (the pseudo-inverse of VMLS §11.5 generalized beyond independent columns). Each term scales the data component $u_i^\top b$ by $1/\sigma_i$, so noise in a direction with tiny $\sigma_i$ is amplified enormously; *truncation* drops those terms and trades a small bias for a large variance reduction, in the same spirit as the ridge parameter of Exercise 9. Eigen's `BDCSVD`/`JacobiSVD` expose this through a threshold on singular values relative to the largest, and `completeOrthogonalDecomposition` gives the same minimum-norm solution more cheaply (Eigen, *Catalogue of dense decompositions*). The threshold is a modelling decision: choose it from the noise level of the data, not from $\epsilon_{\text{mach}}$ alone.

**Example.** The third column of a $6\times3$ matrix equals column 1 plus column 2 up to a $10^{-9}$ wobble. Compiled with g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. What are the singular values, and how do the coefficients and the residual differ between the untruncated solution and one truncated at $10^{-6}\sigma_{\max}$?

```cpp
#include <Eigen/Dense>
#include <cstdio>

int main() {
  // Third column = column 1 + column 2 up to a 1e-9 wobble: numerically rank 2.
  const int m = 6;
  Eigen::MatrixXd A(m, 3);
  const double w[m] = {1e-9, -1e-9, 2e-9, 0.0, -2e-9, 1e-9};
  for (int i = 0; i < m; ++i) { A(i, 0) = i; A(i, 1) = (i % 3) + 1.0; A(i, 2) = A(i, 0) + A(i, 1) + w[i]; }
  Eigen::VectorXd b(m);
  b << 3.1, 4.2, 4.8, 8.1, 8.9, 10.2;
  Eigen::JacobiSVD<Eigen::MatrixXd> svd(A, Eigen::ComputeThinU | Eigen::ComputeThinV);
  std::printf("singular values: %.3e %.3e %.3e\n", svd.singularValues()(0), svd.singularValues()(1), svd.singularValues()(2));
  Eigen::VectorXd x_full = svd.solve(b);                     // all three terms, no truncation
  svd.setThreshold(1e-6);                                    // drop sigma_i < 1e-6 sigma_max
  Eigen::VectorXd x_trunc = svd.solve(b);
  std::printf("rank kept = %d\n", int(svd.rank()));
  std::printf("untruncated x = %.3e %.3e %.3e   |x| = %.2e   |r| = %.4f\n", x_full(0), x_full(1), x_full(2), x_full.norm(), (A * x_full - b).norm());
  std::printf("truncated   x = %.4f %.4f %.4f   |x| = %.4f   |r| = %.4f\n", x_trunc(0), x_trunc(1), x_trunc(2), x_trunc.norm(), (A * x_trunc - b).norm());
}
```

**Solution.** The singular values are 15.13, 2.243 and $1.7\times10^{-9}$. Keeping all three terms divides the data component along $v_3$ by $1.7\times10^{-9}$: the coefficients reach $2.5\times10^{8}$ (norm $4.3\times10^{8}$) for a residual of 3.4425. Truncating at $10^{-6}\sigma_{\max}$ (rank 2) gives coefficients of norm 1.28 and a residual of 3.5183, only $3.5183/3.4425-1=2.2\%$ higher: a small bias bought for a gigantic reduction in variance. The program prints:

```text
singular values: 1.513e+01 2.243e+00 1.704e-09
rank kept = 2
untruncated x = 2.462e+08 2.462e+08 -2.462e+08   |x| = 4.26e+08   |r| = 3.4425
truncated   x = 0.9443 -0.0917 0.8526   |x| = 1.2755   |r| = 3.5183
```

## Worked example

### Case 1: the basic case

**Problem.** Fit the line $y=c_0+c_1t$ by least squares to the four points $(0,1),(1,3),(2,4),(3,8)$, with $t$ in s and $y$ in m. Give $\hat c$, the residual vector, and verify that the residual is orthogonal to the columns.

**Solution.**

1. Write the data as $A c\approx y$ (the least-squares setting of the theory). $A=\begin{pmatrix}1&0\\1&1\\1&2\\1&3\end{pmatrix}$, $y=(1,3,4,8)^\top$.
2. Normal equations $A^\top A\hat c=A^\top y$. The entries are column sums: $A^\top A=\begin{pmatrix}4&6\\6&14\end{pmatrix}$ ($4$; $0+1+2+3=6$; $0+1+4+9=14$) and $A^\top y=(1+3+4+8,\ 0\cdot1+1\cdot3+2\cdot4+3\cdot8)^\top=(16,\ 35)^\top$.
3. The determinant is $4\cdot14-6\cdot6=20$. By the $2\times2$ inverse formula, $c_0=\dfrac{14\cdot16-6\cdot35}{20}=\dfrac{224-210}{20}=0.7$ m and $c_1=\dfrac{4\cdot35-6\cdot16}{20}=\dfrac{140-96}{20}=2.2$ m/s.
4. Fitted values $0.7+2.2t=(0.7,\ 2.9,\ 5.1,\ 7.3)$ m, so the residual is $r=A\hat c-y=(-0.3,\ -0.1,\ 1.1,\ -0.7)$ m.
5. Optimality $A^\top r=0$: $\sum r_i=-0.3-0.1+1.1-0.7=0$ and $\sum t_ir_i=0-0.1+2.2-2.1=0$.
6. Residual norm $\sqrt{0.09+0.01+1.21+0.49}=\sqrt{1.8}=1.3416$ m.
7. Conditioning: the singular values of $A$ give $\kappa(A)=3.76$, so about $\log_{10}3.76\approx0.6$ digits are at risk and either method works; in the degree-12 case of the theory they would not.

**Check.** `numpy.linalg.lstsq` returns $(0.7,\ 2.2)$, residual norm $1.3416$ and $\kappa=3.7589$, the same as the hand computation. The sums in step 5 vanish exactly, as the figure below shows.

![The least-squares line through four points with its vertical residuals](/lesson-figures/CPP11-4.svg)

*Figure: The four residuals of case 1 drawn to scale; their sum and their t-weighted sum vanish, which is the orthogonality A^T r = 0.*

**Takeaway.** The minimizer is the point where the residual is perpendicular to every column of $A$; two sums being zero is the whole test.

### Case 2: the Läuchli problem (normal equations fail, QR succeeds)

**Problem.** Solve $\min_x\|Ax-b\|$ for $A=\begin{pmatrix}1&1\\\delta&0\\0&\delta\end{pmatrix}$, $\delta=10^{-8}$, $b=A\,(1,1)^\top=(2,\delta,\delta)^\top$, so the exact solution is $\hat x=(1,1)$ with zero residual. Use IEEE double precision ($\epsilon_{\text{mach}}=1.1\times10^{-16}$).

**Solution.**

1. **Condition numbers.** $A^\top A=\begin{pmatrix}1+\delta^2&1\\1&1+\delta^2\end{pmatrix}$; its eigenvalues are $2+\delta^2$ and $\delta^2$, so $\sigma_{\max}=\sqrt{2+\delta^2}\approx1.414$, $\sigma_{\min}=\delta=10^{-8}$ and $\kappa(A)\approx1.41\times10^{8}$. A stable method keeps about $16-8.15\approx8$ digits. For the normal equations $\kappa^2\approx2\times10^{16}>1/\epsilon_{\text{mach}}$: no digit is guaranteed.
2. **Normal equations.** In floating point $1+\delta^2=1+10^{-16}\to1$ (half a unit in the last place of 1 is $1.1\times10^{-16}$), so the computed $A^\top A=\begin{pmatrix}1&1\\1&1\end{pmatrix}$ has determinant 0 (`numpy.linalg.det` gives $0.0$). The solve reports a singular matrix; nothing can be repaired afterwards, because the information about $\delta^2$ was lost in the product.
3. **QR.** Householder QR of $A$ followed by back substitution (theory: $R\hat x=Q^\top b$) returns $\hat x=(1.0,\,1.0)$ (`numpy.linalg.qr` and `solve(R, Q.T @ b)`, printed as `[1. 1.]`).
4. **A milder case.** For $\delta=10^{-4}$: $\kappa(A)=1.4\times10^{4}$ and $\kappa(A^\top A)=2.0\times10^{8}$. The normal equations now run and return $(1.0000000056,\,0.9999999944)$, an error of $7.9\times10^{-9}$, in line with the estimate $\kappa^2\epsilon_{\text{mach}}=2\times10^{8}\cdot1.1\times10^{-16}\approx2\times10^{-8}$; QR returns an error of $3\times10^{-16}$, below its bound $\kappa\epsilon_{\text{mach}}\approx1.5\times10^{-12}$.
5. **In C++** this is `A.householderQr().solve(b)` against `(A.transpose()*A).llt().solve(A.transpose()*b)`; the second typically reports `info() == NumericalIssue` (a zero pivot) or returns garbage.

**Check.** The determinant of the computed Gram matrix ($0.0$), the QR result `[1. 1.]` and the $\delta=10^{-4}$ errors above were all computed with NumPy in double precision; the prediction $\kappa^2\epsilon_{\text{mach}}$ agrees in order of magnitude.

**Takeaway.** The same data give failure at $\delta=10^{-8}$ for the normal equations and 8 correct digits with QR: check $\kappa(A)$ before choosing the method.

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

12. **(Challenge)** Residual by the Pythagorean identity. (a) Prove $\|b-A\hat x\|^2=\|b\|^2-\|Q^\top b\|^2$ for $A=QR$ with linearly independent columns. (b) Take $A=(1,1,1)^\top$ and $b=(10^8+1,\,10^8,\,10^8-1)^\top$. Compute the exact residual norm squared by hand, then evaluate the right-hand side of the identity in IEEE double precision and compare. (c) Explain the failure quantitatively and give a robust formula. (d) At what ratio $\|r\|/\|b\|$ does the identity lose all digits in double precision? (adapted from Boyd and Vandenberghe, VMLS, Exercise 12.8(b); the numerical trap is added)
13. **(Challenge)** Richardson iteration. (a) Prove that $x_{k+1}=x_k-\mu A^\top(Ax_k-b)$ with $\mu=1/\sigma_{\max}(A)^2$ satisfies $\|x_k-\hat x\|\le(1-1/\kappa^2)^k\|x_0-\hat x\|$. (b) How many iterations reduce the error by $10^{-6}$ for $\kappa=10,100,1000$? (c) Test the prediction numerically on a $60\times5$ matrix with singular values linearly spaced between 1 and $1/\kappa$ for $\kappa=10$ and $100$. (d) Compare with a direct QR solve for $n=5$ and say when the iteration is nevertheless preferable. (adapted from Boyd and Vandenberghe, VMLS, Exercise 12.13)
14. **(Challenge)** Weighted least squares. (a) Show that $\sum_iw_i(\tilde a_i^\top x-b_i)^2=\|D(Ax-b)\|^2$ for a diagonal $D$, and that $DA$ has independent columns when $A$ does and all $w_i>0$. (b) Derive $\hat x=(A^\top WA)^{-1}A^\top Wb$ with $W=\mathrm{diag}(w)$. (c) For the cubic Vandermonde matrix on 50 equally spaced points of $[0,1]$ ($\kappa=117.9$) give weight $10^{-6}$ to the first 25 rows and $1$ to the other 25. Compute $\kappa(DA)$ and $\kappa((DA)^\top DA)$, and say what this means for solving the weighted problem with the normal equations. (adapted from Boyd and Vandenberghe, VMLS, Exercise 12.4)
15. **(Challenge)** Gram method against QR. (a) Count the flops of both methods as in this lesson's table. (b) Evaluate the ratio for $(m,n)=(10^4,10)$ and $(600,500)$. (c) For the noise-free fit $b=Ac_{\text{true}}$ on 50 equally spaced points of $[0,1]$ with $c_{\text{true},j}=(-1)^j(1+0.1j)$, measure $\|\hat c-c_{\text{true}}\|$ for degrees 5, 7, 9 with QR and with the Gram method, and compare with $\kappa^2\epsilon_{\text{mach}}$ and $\kappa\epsilon_{\text{mach}}$. (d) Give a decision rule. (adapted from Boyd and Vandenberghe, VMLS, Exercise 12.16; the accuracy study is added)

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
12. (a) $A\hat x=QQ^\top b$ is the orthogonal projection of $b$ onto $\mathrm{range}(A)=\mathrm{range}(Q)$, so $r=b-QQ^\top b$ is orthogonal to $QQ^\top b$: $Q^\top r=Q^\top b-Q^\top QQ^\top b=0$ and $(QQ^\top b)^\top r=(Q^\top b)^\top Q^\top r=0$. Then $\|b\|^2=\|QQ^\top b\|^2+\|r\|^2$ and $\|QQ^\top b\|^2=b^\top QQ^\top QQ^\top b=\|Q^\top b\|^2$, hence $\|r\|^2=\|b\|^2-\|Q^\top b\|^2$. (b) $Q=(1,1,1)^\top/\sqrt3$, $Q^\top b=3\cdot10^8/\sqrt3$, so $\|Q^\top b\|^2=3\cdot10^{16}$. $\|b\|^2=(10^8+1)^2+10^{16}+(10^8-1)^2=3\cdot10^{16}+2$. Exact $\|r\|^2=2$ (indeed $r=b-10^8\mathbf 1=(1,0,-1)$, $\|r\|^2=2$). In float64 (numpy) the right-hand side evaluated to $-12.0$: negative, which is impossible for a squared norm. (c) Doubles near $3\cdot10^{16}$ are spaced $4$ apart (since $2^{53}\approx9.0\cdot10^{15}$), so $3\cdot10^{16}+2$ cannot even be represented, and each of the two terms has absolute error of several units, larger than the true answer 2. The relative error estimate $\epsilon\|b\|^2/\|r\|^2=1.1\cdot10^{-16}\cdot3\cdot10^{16}/2\approx1.7$ already exceeds 100%. Robust formula: form $r=b-A\hat x$ (here $(1,0,-1)$ up to rounding of $\hat x$; better still compute $b-\bar b$ for this one-column case) and take $\|r\|^2$. (d) The relative error is about $\epsilon\|b\|^2/\|r\|^2$, which reaches 1 at $\|r\|/\|b\|\approx\sqrt\epsilon\approx10^{-8}$. In the example $\|r\|/\|b\|=\sqrt2/(\sqrt3\cdot10^8)\approx8\cdot10^{-9}$, just below that threshold.
13. (a) Since $A^\top(A\hat x-b)=0$, $e_{k+1}=x_{k+1}-\hat x=e_k-\mu A^\top Ae_k=(I-\mu A^\top A)e_k$. With $A=U\Sigma V^\top$ and $e_k=V c_k$, $c_{k+1,i}=(1-\mu\sigma_i^2)c_{k,i}$. For $\mu=1/\sigma_{\max}^2$, $0\le1-\mu\sigma_i^2\le1-\sigma_{\min}^2/\sigma_{\max}^2=1-1/\kappa^2$, so $\|c_k\|\le(1-1/\kappa^2)^k\|c_0\|$ and $\|e_k\|=\|c_k\|$ since $V$ is orthogonal. (b) $k\ge\ln10^{-6}/\ln(1-1/\kappa^2)$: $\kappa=10$: $1374.6\to1375$; $\kappa=100$: $138{,}148.2\to138{,}149$; $\kappa=1000$: $13{,}815{,}503.6\to13{,}815{,}504$ (about $\kappa^2\ln10^6=13.8\,\kappa^2$). (c) A run with random orthogonal factors (seed 0) stopped when the error fell below $10^{-6}$ of its start after 1374 iterations for $\kappa=10$ and 138,098 for $\kappa=100$, matching the predictions to within 0.04%. (The bound is attained when the initial error has a component along the smallest singular vector, which is generic.) (d) QR for $m=60$, $n=5$ costs about $2mn^2-\tfrac23n^3\approx2900$ flops, once; Richardson with $\kappa=10$ costs about $4mn\cdot1375\approx1.6\cdot10^{6}$. For small dense problems direct QR wins by orders of magnitude. The iteration is preferable when $A$ is huge and sparse (or only available as a matrix-vector product), where storing a factorization is impossible and each iteration costs only two products, and when $\kappa$ is moderate or a preconditioner makes it so.
14. (a) Put $D=\mathrm{diag}(\sqrt{w_1},\dots,\sqrt{w_m})$; then $\|D(Ax-b)\|^2=\sum_i w_i(\tilde a_i^\top x-b_i)^2$. If $DAx=0$ then $Ax=0$ because $D$ is invertible for $w_i>0$, so $x=0$ when $A$ has independent columns. (b) Apply (12.5) to $B=DA$, $d=Db$: $\hat x=(B^\top B)^{-1}B^\top d=(A^\top D^2A)^{-1}A^\top D^2b=(A^\top WA)^{-1}A^\top Wb$ with $W=D^2$. (c) Computed: $\kappa(A)=117.86$; $\kappa(DA)=1807.18$ (weights $10^{-3}$ and 1 in $D$); $\kappa((DA)^\top DA)=\kappa(DA)^2=3.27\cdot10^{6}$. Down-weighting half of the rows by $10^{-6}$ makes the problem about 15 times worse conditioned in $\kappa$, 235 times in $\kappa^2$: the data from the first half still pin down the cubic through the second half but only weakly. Solve it through QR of $DA$ (that is what "weighted least squares as a standard problem" in the exercise means), not through $A^\top WA$, which would have $\kappa^2\epsilon_{\text{mach}}\approx3.6\cdot10^{-10}$ and is avoidable.
15. (a) Gram: $mn^2$ (symmetric product) $+\tfrac13n^3$ (Cholesky) $+O(mn+n^2)$; Householder QR: $2mn^2-\tfrac23n^3$. (b) $(10^4,10)$: QR $1.9993\cdot10^{6}$, Gram $1.0003\cdot10^{6}$, ratio $2.00$. $(600,500)$: QR $2.17\cdot10^{8}$, Gram $1.92\cdot10^{8}$, ratio $1.13$. (c) Computed (float64, numpy; QR via `numpy.linalg.qr`, Gram via `solve(AᵀA, Aᵀb)`):

   | degree | $\kappa(A)$ | QR error | Gram error | $\kappa^2\epsilon$ |
   |---|---|---|---|---|
   | 5 | $3.55\cdot10^{3}$ | $1.7\cdot10^{-13}$ | $1.1\cdot10^{-9}$ | $1.4\cdot10^{-9}$ |
   | 7 | $1.11\cdot10^{5}$ | $9.8\cdot10^{-12}$ | $9.9\cdot10^{-7}$ | $1.4\cdot10^{-6}$ |
   | 9 | $3.56\cdot10^{6}$ | $3.7\cdot10^{-11}$ | $8.2\cdot10^{-4}$ | $1.4\cdot10^{-3}$ |

   The Gram errors follow $\kappa^2\epsilon_{\text{mach}}$ (within a factor 1.7), the QR errors follow $\kappa\epsilon_{\text{mach}}$ ($3.9\cdot10^{-13}$, $1.2\cdot10^{-11}$, $3.9\cdot10^{-10}$ for the three degrees, all upper bounds that the measured values stay below). (d) Use QR (or SVD) by default; the Gram/Cholesky route only when $\kappa(A)^2\epsilon_{\text{mach}}$ is clearly below the accuracy you need (at most $\kappa\approx10^{3}$ for six digits), when $m\gg n$ and speed matters, or when $G$ is available cheaply; always check $\kappa$ (from an SVD or a condition estimate) and keep a QR fallback when Cholesky reports a non-positive pivot.

## Further reading

- [Eigen: Getting started](https://eigen.tuxfamily.org/dox/GettingStarted.html) - installation, matrices, vectors and the first program.
- [Eigen: Linear algebra and decompositions](https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html) - solving systems, least squares, and the decomposition comparison table.
- [MIT 18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/) - projections, least squares, and the SVD, with lectures and problem sets.
- [Boyd and Vandenberghe: Introduction to Applied Linear Algebra (VMLS)](https://web.stanford.edu/~boyd/vmls/vmls.pdf) - free PDF; §12.2 and §12.3 (least squares and its solution), Exercises 12.4, 12.8, 12.13 and 12.16 are the basis of the added theory and challenges.
- [Eigen: Catalogue of dense decompositions](https://eigen.tuxfamily.org/dox/group__TopicLinearAlgebraDecompositions.html) - speed, accuracy and rank-revealing properties of each decomposition.

**More practice:** the [MIT 18.06 assignments](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/assignments/) (the projection and least-squares problem sets), the Eigen pages [Linear algebra and decompositions](https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html), [Solving linear least squares systems](https://eigen.tuxfamily.org/dox/group__LeastSquares.html), [Aliasing](https://eigen.tuxfamily.org/dox/group__TopicAliasing.html) and [Lazy evaluation and `auto`](https://eigen.tuxfamily.org/dox/TopicLazyEvaluation.html), and the NumPy docs for [`np.linalg.lstsq`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) and [Chebyshev polynomials](https://numpy.org/doc/stable/reference/routines.polynomials.chebyshev.html) (re-do the degree sweep in a better basis).