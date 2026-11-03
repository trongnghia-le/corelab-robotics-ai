---
{"title": "C++ số học: Eigen, bộ giải tuyến tính và ổn định số", "summary": "Dùng ma trận và các phép phân rã của Eigen để giải bài toán bình phương tối thiểu, đồng thời dự đoán và đo xem điều kiện số (conditioning) giới hạn độ chính xác ra sao.", "objectives": ["Tạo và thao tác ma trận, vector Eigen và tránh các cạm bẫy phổ biến về expression template và aliasing.", "Chọn phép phân rã (LU, Cholesky, QR, SVD) cho một hệ tuyến tính cho trước.", "Giải bài toán bình phương tối thiểu bằng QR và bằng phương trình chuẩn (normal equations) và giải thích vì sao độ chính xác khác nhau.", "Liên hệ condition number với số chữ số bị mất, và kiểm chứng kết quả C++ với một oracle Python độc lập."]}
---
## Vì sao điều này quan trọng

Gần như mọi bài toán ước lượng và điều khiển trong robotics cuối cùng đều trở thành một hệ tuyến tính hoặc một phép khớp bình phương tối thiểu: hiệu chuẩn camera hay độ lệch (bias) IMU, khớp một mặt phẳng vào đám mây điểm, giải một bước cập nhật Kalman, tính giả nghịch đảo Jacobian cho động học ngược, tối ưu một pose graph. Trong C++ công cụ chuẩn là Eigen, một thư viện chỉ có header mà các ma trận của nó biên dịch thành những vòng lặp gọn. Nhưng có hai điều khác với đại số trong sách giáo khoa. Thứ nhất, số học dấu phẩy động chỉ có khoảng 16 chữ số có nghĩa, và một bài toán điều kiện xấu (ill-conditioned) có thể vứt đi phần lớn chúng. Thứ hai, *cách* bạn giải rất quan trọng: giải bài toán bình phương tối thiểu bằng cách lập $A^\top A$ làm bình phương condition number và có thể mất nhiều gấp đôi số chữ số so với phân rã QR. Trong thí nghiệm của bài này, cùng một phép khớp đa thức bậc 9 mất 5 chữ số với QR (sai số $2.5\times10^{-11}$) và 12 chữ số với phương trình chuẩn (sai số $4.9\times10^{-4}$). Biết gọi bộ giải nào, và cách kiểm tra đáp án với một oracle độc lập, là điều phân biệt một kết quả bạn có thể tin cậy trên robot với một kết quả chỉ biên dịch được.

## Trực giác

Hãy coi condition number $\kappa(A)$ như một kính lúp: nếu đầu vào có sai số tương đối $\epsilon$, đáp án có thể có sai số tương đối tới $\kappa\epsilon$. Việc làm tròn ở mỗi phép tính thêm vào một sai số cỡ $\epsilon_{\text{mach}}\approx1.1\times10^{-16}$, nên ngay cả một thuật toán hoàn hảo áp dụng cho bài toán có $\kappa=10^{8}$ cũng chỉ tin được tới khoảng $10^{-8}$. Một thuật toán *ổn định (stable)* không thêm sai số nào hơn mức không thể tránh đó; một thuật toán *không ổn định* thêm nhiều hơn.

Bình phương tối thiểu có một hình học đẹp. Khớp tốt nhất $A\hat x$ là hình chiếu của $b$ lên không gian cột của $A$; phần dư $r=b-A\hat x$ vuông góc với mọi cột: $A^\top r=0$. QR làm việc trực tiếp với một cơ sở trực chuẩn của không gian đó (các phép biến đổi trực giao không khuếch đại sai số). Phương trình chuẩn $A^\top A\hat x=A^\top b$ tương đương về mặt đại số nhưng bắt đầu bằng việc nhân $A^\top A$, mà condition number của nó là $\kappa(A)^2$.

![Hình chiếu của b lên không gian cột của A với phần dư vuông góc, và một biểu đồ cột về sai số của QR so với phương trình chuẩn cho đa thức bậc 3, 6, 9 và 12](/lesson-figures/CPP11.svg)

*Trái: phần dư trực giao với không gian cột. Phải: sai số hệ số đo được của QR (khoảng cond nhân 1e-16) và của phương trình chuẩn (khoảng cond bình phương nhân 1e-16).*

## Lý thuyết và suy dẫn

### Cơ bản về Eigen

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
Chỉ số bắt đầu từ không và `A(i, j)` là hàng $i$, cột $j$. `Eigen::Map<VectorXd>(ptr, n)` xem vùng nhớ có sẵn mà không copy. Biên dịch với `-I/usr/include/eigen3` (hoặc `find_package(Eigen3)` và `Eigen3::Eigen` trong CMake) và `-O2`; Eigen rất chậm khi không tối ưu hóa.

**Expression template.** `A * x + b` không tính gì cả: nó dựng một đối tượng biểu thức nhẹ và chỉ được đánh giá khi gán cho một ma trận. Hai cái bẫy theo sau.

1. `auto` bắt lấy biểu thức, không phải kết quả. `auto s = M.colPivHouseholderQr().solve(b);` giữ một reference tới phép phân rã tạm, thứ bị hủy ở cuối câu lệnh: đọc `s` về sau là use-after-scope (AddressSanitizer báo `stack-use-after-scope`). Hãy viết `Eigen::VectorXd s = ...;`.
2. **Aliasing.** `A = A.transpose();` đọc và ghi cùng một vùng nhớ khi đang đánh giá. Ở bản build debug Eigen assert "aliasing detected during transposition"; với `-O2 -DNDEBUG` nó lặng lẽ tạo ra một ma trận sai (với $\begin{pmatrix}1&2\\3&4\end{pmatrix}$ nó in ra $\begin{pmatrix}1&2\\2&4\end{pmatrix}$ thay vì $\begin{pmatrix}1&3\\2&4\end{pmatrix}$). Dùng `A.transposeInPlace()` hoặc `A = A.transpose().eval();`.

### Giải hệ tuyến tính

Đừng bao giờ lập nghịch đảo tường minh để giải $Ax=b$; hãy phân rã rồi giải. Chọn theo cấu trúc:

| Ma trận | Phân rã (Eigen) | Chi phí (flop, $n\times n$) | Ghi chú |
|---|---|---|---|
| vuông tổng quát | `partialPivLu()` | $\tfrac23n^3$ | nhanh, ổn định trong thực tế |
| đối xứng xác định dương (hiệp phương sai, phương trình chuẩn) | `llt()` / `ldlt()` | $\tfrac13n^3$ | Cholesky; thất bại/báo cờ nếu không SPD |
| cao, hạng đầy đủ, bình phương tối thiểu | `householderQr()` / `colPivHouseholderQr()` | $2mn^2-\tfrac23n^3$ | ổn định, phát hiện hạng nhờ pivoting |
| thiếu hạng, hoặc cần $\sigma$ | `jacobiSvd()` / `bdcSvd()` | lớn hơn | vững chắc nhất; cho condition number |

Ở $n=1000$, Cholesky là $\approx3.3\times10^{8}$ flop, khoảng 33 ms ở 10 GFLOP/s; ở $n=6$ khoảng 72 flop, không đáng kể.

### Bình phương tối thiểu

Cho $A\in\mathbb R^{m\times n}$, $m\ge n$, tìm $\hat x=\arg\min\|Ax-b\|_2$. Đặt gradient bằng không cho ta phương trình chuẩn $A^\top A\hat x=A^\top b$, tương đương $A^\top(A\hat x-b)=0$. Với phân rã QR mỏng $A=QR$ ($Q^\top Q=I$, $R$ tam giác trên) bài toán trở thành $R\hat x=Q^\top b$, giải bằng thế ngược; chuẩn của phần dư là $\|(I-QQ^\top)b\|$.

**Vì sao phương trình chuẩn mất độ chính xác.** Với SVD $A=U\Sigma V^\top$, $A^\top A=V\Sigma^2V^\top$ nên $\kappa(A^\top A)=\sigma_{\max}^2/\sigma_{\min}^2=\kappa(A)^2$. Một bộ giải có sai số $\approx\kappa\,\epsilon_{\text{mach}}$ áp dụng cho ma trận này cho $\kappa(A)^2\epsilon_{\text{mach}}$, trong khi QR đạt khoảng $\kappa(A)\epsilon_{\text{mach}}$ (với các bài toán phần dư nhỏ).

**Số chữ số.** Số chữ số mất $\approx\log_{10}\kappa$. Với $\kappa=3.6\times10^{6}$: QR giữ khoảng $16-6.6\approx9$ chữ số; phương trình chuẩn giữ khoảng $16-13.1\approx3$.

### Điều kiện số của phép khớp đa thức

Ma trận Vandermonde với các cột $1,t,t^2,\dots,t^d$ trên $[0,1]$ trở nên gần như thiếu hạng khi $d$ tăng, vì các lũy thừa cao trông giống nhau. Đo với 50 điểm cách đều:

| bậc | $\kappa(A)$ | sai số QR | sai số phương trình chuẩn |
|---|---|---|---|
| 3 | 1.2e2 | 4.0e-15 | 1.2e-12 |
| 6 | 2.0e4 | 4.6e-13 | 2.1e-08 |
| 9 | 3.6e6 | 2.5e-11 | 4.9e-04 |
| 12 | 6.8e8 | 3.4e-08 | 3.8e+00 |

(sai số là $\|\hat c-c_{\text{true}}\|$ cho dữ liệu không nhiễu $y=Ac_{\text{true}}$ với $c_{\text{true},j}=(-1)^j(1+0.1j)$, cùng các hệ số với test của lab; các hệ số khác cho sai số cùng bậc, và các chữ số cuối phụ thuộc nền tảng.) Căn giữa và co giãn $t$ về $[-1,1]$ giảm condition number bậc 12 xuống $1.6\times10^{4}$; các cơ sở đa thức trực giao (Chebyshev) còn tốt hơn. Các biện pháp cho bài toán gần suy biến: co giãn các cột, dùng SVD có cắt cụt, hoặc thêm điều chuẩn Tikhonov (ridge) $(A^\top A+\lambda I)x=A^\top b$.

### Kiểm chứng bằng một oracle

Một cài đặt độc lập bắt được các lỗi nối dây (sai chỉ số, ma trận bị chuyển vị). So sánh *chuẩn phần dư* và *giá trị khớp*, không chỉ các hệ số, khi bài toán điều kiện xấu, vì các hệ số có thể khác nhau ở những chữ số cuối trong khi phép khớp giống hệt. Chọn dung sai từ $\kappa\,\epsilon_{\text{mach}}$, không phải $10^{-6}$ tùy tiện.

## Ví dụ có lời giải

Khớp $y=a+bt$ vào các điểm $(0,1),(1,3),(2,4),(3,8)$.

1. Ma trận thiết kế $A=\begin{pmatrix}1&0\\1&1\\1&2\\1&3\end{pmatrix}$, $b=(1,3,4,8)^\top$.
2. $A^\top A=\begin{pmatrix}4&6\\6&14\end{pmatrix}$ (tổng các cột: $4$, $0+1+2+3=6$, $0+1+4+9=14$). $A^\top b=(1+3+4+8,\ 0\cdot1+1\cdot3+2\cdot4+3\cdot8)^\top=(16,\ 35)^\top$.
3. Định thức $4\cdot14-6\cdot6=20$. Khi đó $a=\dfrac{14\cdot16-6\cdot35}{20}=\dfrac{224-210}{20}=0.7$ và $b=\dfrac{4\cdot35-6\cdot16}{20}=\dfrac{140-96}{20}=2.2$.
4. Giá trị khớp $0.7+2.2t=(0.7,\ 2.9,\ 5.1,\ 7.3)$; phần dư $r=A\hat x-b=(-0.3,\ -0.1,\ 1.1,\ -0.7)$.
5. Kiểm tra tính trực giao: $\sum r_i=-0.3-0.1+1.1-0.7=0$ và $\sum t_ir_i=0-0.1+2.2-2.1=0$. Cả hai bằng không, đúng như $A^\top r=0$ đòi hỏi.
6. Chuẩn phần dư $\sqrt{0.09+0.01+1.21+0.49}=\sqrt{1.8}=1.3416$.
7. Điều kiện số: các $\sigma$ của $A$ cho $\kappa(A)\approx3.76$ (nên không có chữ số nào gặp rủi ro), và cả hai phương pháp đều chạy được; ở ca bậc 12 phía trên thì không.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: MIT 18.06, least squares and projections)* Khớp $y=a+bt$ bằng bình phương tối thiểu cho $(0,2),(1,3),(2,7)$. Cho $\hat x$, vector phần dư, và kiểm tra $A^\top r=0$.
2. **(Dễ)** *(Adapted from: Eigen, Linear algebra and decompositions)* Nêu phép phân rã Eigen bạn sẽ dùng cho: (a) một ma trận độ cứng 6x6 đối xứng xác định dương; (b) một hệ Jacobian 4x4 tổng quát; (c) một ma trận thiết kế cao 1000x5 hạng đầy đủ; (d) một ma trận thiết kế 1000x5 có thể thiếu hạng mà bạn muốn biết hạng và giả nghịch đảo.
3. **(Dễ)** Một bài toán có $\kappa(A)=3.6\times10^{6}$. Ước lượng số chữ số chính xác của một nghiệm độ chính xác kép cho một phương pháp ổn định trên $A$ và cho phương trình chuẩn.
4. **(Trung bình)** Tìm bug (hai dòng sai theo hai kiểu khác nhau) và nói mỗi cái sẽ biểu hiện ra sao:
   ```cpp
   Eigen::MatrixXd M(2, 2); M << 1, 2, 3, 4;
   M = M.transpose();
   auto x = M.colPivHouseholderQr().solve(b);
   ```
5. **(Trung bình)** *(Adapted from: Eigen documentation, aliasing)* Dự đoán `M = M.transpose();` làm gì ở bản build Debug và ở `-O2 -DNDEBUG`, và đưa ra hai lựa chọn đúng. Vì sao `C = A * B;` không có vấn đề như vậy với tích ma trận theo mặc định?
6. **(Trung bình)** Với một ma trận thiết kế có $\kappa=10^{6}$, ước lượng sai số tương đối của QR và của phương trình chuẩn với $\epsilon_{\text{mach}}=1.1\times10^{-16}$. So sánh với dòng bậc 9 đo được trong bảng ($\kappa=3.6\times10^{6}$) và nhận xét về mức khớp.
7. **(Trung bình)** Viết một đoạn NumPy kiểm tra kết quả C++ của lab cho dữ liệu $t=0..9$, $y=(1.1, 2.9, 5.2, 7.1, 8.8, 11.2, 13.1, 14.8, 17.1, 19.0)$ và quyết định so sánh những đại lượng nào với dung sai nào.
8. **(Khó)** *(Adapted from: Trefethen and Bau, Numerical Linear Algebra, lectures on least squares and conditioning)* Chứng minh $\kappa_2(A^\top A)=\kappa_2(A)^2$ cho $A$ hạng cột đầy đủ, và suy ra nghiệm bình phương tối thiểu qua QR: chứng minh $\hat x=R^{-1}Q^\top b$.
9. **(Khó)** Các cột của một ma trận hiệu chuẩn gần như cộng tuyến: $\sigma_{\max}=1$, $\sigma_{\min}=10^{-4}$. Tính $\kappa(A)$ và $\kappa(A^\top A)$. Với tham số ridge $\lambda=10^{-6}$ tính condition number của $A^\top A+\lambda I$ và bàn về đánh đổi bias-variance khi chọn $\lambda$.
10. **(Khó)** Mô hình chi phí: một bộ tối ưu visual-inertial giải một hệ SPD đặc kích thước $n=300$ mỗi 33 ms. Ước lượng flop cho Cholesky, LU và QR, thời gian ở 5 GFLOP/s, và nói điều gì thay đổi nếu ma trận thưa.
11. **(Mini-project)** Tái tạo bảng của bài này cho bậc 3 đến 12 trên máy của bạn, thêm một cột cho `jacobiSvd().solve` và một cột cho phép khớp trên $t\in[-1,1]$, và ghi lại bậc mà sai số của mỗi phương pháp lần đầu vượt quá $10^{-6}$.

## Cài đặt tham khảo

Đoạn code dưới là thư viện của lab: ma trận thiết kế Vandermonde, bộ giải QR và phương trình chuẩn, phần dư, condition number và một phép khớp đa thức. Biên dịch bằng `g++ -std=c++17 -O2 -Wall -Wextra -I/usr/include/eigen3 ref.cpp` (cài bằng `sudo apt install libeigen3-dev`).

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

Oracle Python cho tập dữ liệu đường thẳng có nhiễu của bài tập 7:

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

Output của oracle, và của các hàm C++ trên cùng dữ liệu: `x = [1.06, 1.99333333]`, chuẩn phần dư `0.4442221666`, `cond(A) = 10.1722753`.

## Thực hành độc lập

### Mục tiêu

Cài đặt bình phương tối thiểu đặc bằng Eigen theo hai cách, kiểm chứng chúng với các ca tính tay chính xác và một oracle Python, và đo xem điều kiện số kiểm soát độ chính xác ra sao.

### Chuẩn bị

`g++` với C++17 và Eigen 3 (`sudo apt install libeigen3-dev`; chỉ có header). Python 3 với NumPy cho oracle. Lưu code khởi đầu và các test bên dưới nó thành `lab.cpp`; build bằng `g++ -std=c++17 -O1 -g -Wall -Wextra -I/usr/include/eigen3 -fsanitize=address,undefined lab.cpp -o lab && ./lab`.

### Nhiệm vụ

1. Cài đặt `vandermonde` và kiểm tra bằng tay hàng cho $t=3$, bậc 2: $(1,3,9)$.
2. Cài đặt `least_squares_qr`, `residual_norm` và các phép kiểm tra hình dạng; kiểm chứng ví dụ $[7/6, 1/2]$ từ các test.
3. Cài đặt `least_squares_normal`; xác nhận cả hai cho cùng đáp án trên một bài toán ngẫu nhiên điều kiện tốt.
4. Cài đặt `condition_number` với `JacobiSVD` (các giá trị kỳ dị được sắp giảm dần).
5. Cài đặt `polyfit` và chạy nó trên tập dữ liệu 10 điểm của bài tập 7; so sánh với `oracle.py`.
6. Tái tạo bước quét bậc (3, 6, 9, 12) trong một `main` nhỏ, in $\kappa$, sai số QR và sai số phương trình chuẩn; xác nhận tỉ số sai số tăng gần như theo $\kappa$.

### Code khởi đầu

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

### Kiểm thử

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

### Kết quả mong đợi

```
all tests passed
```

và với phép quét (3 chữ số có nghĩa; các chữ số cuối của bạn có thể khác): bậc 9 cho `cond 3.56e+06`, sai số QR cỡ `1e-11`, và sai số phương trình chuẩn cỡ `1e-4`.

### Thử thách mở rộng

Thêm hồi quy ridge `ridge(A, b, lambda)` qua QR mở rộng (xếp chồng $\sqrt\lambda I$ dưới $A$) và chứng tỏ nó ổn định hóa phép khớp bậc 12; hoặc tự cài đặt Householder QR và so sánh với Eigen trên các ca test.

### Thực hành với thư viện

Lab đã dùng Eigen. Thư viện độc lập là NumPy (`pip install numpy`), oracle thông thường: tái tạo toàn bộ bảng bậc trong Python với `np.vander`, `np.linalg.qr`, phương trình chuẩn và `np.linalg.lstsq`, và so sánh với phép quét C++ của bạn (cùng `c_true`, cùng 50 điểm). Khối cuối cho thấy các biện pháp từ phần lý thuyết với `numpy.polynomial.chebyshev`.

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

Kỳ vọng: các giá trị $\kappa$ 1.2e2, 2.0e4, 3.6e6, 6.8e8 (giống hệt lần chạy C++), sai số QR gần $\kappa\epsilon$ và sai số phương trình chuẩn gần $\kappa^2\epsilon$ (các chữ số cuối khác nhau giữa NumPy/LAPACK và Eigen), condition number khoảng 6.8e8, 1.6e4 và 2.5 cho cơ sở đơn thức trên $[0,1]$, cơ sở đơn thức trên $[-1,1]$ và cơ sở Chebyshev, rồi `library track ok`. So sánh số C++ của bạn với các dòng này và giải thích bất kỳ khác biệt nào lớn hơn hệ số 10.

## Kiểm chứng

- **Kiểm tra tối ưu:** $\|A^\top(A\hat x-b)\|$ phải cỡ $\epsilon\,\|A\|\,\|r\|$, không chỉ nhỏ theo nghĩa tuyệt đối. Luôn tính nó.
- **Kiểm tra oracle:** so sánh với `numpy.linalg.lstsq` trên cùng dữ liệu; so sánh chuẩn phần dư và giá trị khớp trước.
- **Ca chính xác:** các bài toán có nghiệm đã biết (dữ liệu sinh từ hệ số đã biết, như trong các test) biến độ chính xác thành một con số bạn có thể in ra.
- **Condition number:** tính `condition_number(A)` và đặt dung sai khoảng $10\,\kappa\,\epsilon_{\text{mach}}$; một phép so sánh thất bại với $\kappa$ rất lớn là điều được dự kiến, không phải bug.
- **Sanitizer:** build với ASan/UBSan để bắt các biểu thức `auto` treo, và chỉ biên dịch với `-DEIGEN_NO_DEBUG` cho benchmark.
- **Co giãn:** lặp lại với `t` được dịch và co giãn về $[-1,1]$ và kiểm tra condition number giảm.

## Lỗi thường gặp

| Sai lầm | Quan sát được |
|---|---|
| `auto x = A.colPivHouseholderQr().solve(b);` | `stack-use-after-scope` hoặc rác; dùng `VectorXd` tường minh |
| `A = A.transpose();` | assertion ở Debug; ma trận sai lặng lẽ ở Release (`1 2 / 2 4`) |
| Giải bằng `A.inverse() * b` | chậm hơn và kém chính xác hơn `solve`; không bao giờ cần |
| Phương trình chuẩn trên phép khớp điều kiện xấu | sai số $\kappa^2\epsilon$: $4.9\times10^{-4}$ ở bậc 9 thay vì $2.5\times10^{-11}$ |
| Cơ sở đơn thức trên $[0,1]$ cho bậc cao | $\kappa$ bùng nổ (6.8e8 ở bậc 12); căn giữa và co giãn $t$ |
| Build không có `-O2` | Eigen chậm hơn 10-100 lần, benchmark gây hiểu lầm |
| `LLT` trên ma trận không xác định dương | sai lặng lẽ trừ khi bạn kiểm tra `.info()` |
| So sánh hệ số với dung sai cố định `1e-9` | thất bại giả trên bài toán điều kiện xấu; hãy so sánh phần dư |
| Hằng số nguyên trộn vào biểu thức Eigen của `double` | lỗi biên dịch hoặc chuyển đổi không mong muốn; viết `2.0` |
| Hệ thiếu ràng buộc (underdetermined) với QR | không có nghiệm duy nhất; dùng nghiệm chuẩn nhỏ nhất từ SVD |

## Phương án khác và đánh đổi

- **QR so với phương trình chuẩn so với SVD.** QR là mặc định cho bình phương tối thiểu (ổn định, nhanh). Phương trình chuẩn nhanh nhất ($\approx mn^2$ cộng $\frac13n^3$) và ổn khi $\kappa$ nhỏ, nhưng mất độ chính xác. SVD vững chắc nhất (thiếu hạng, cắt cụt, giả nghịch đảo) và chậm nhất.
- **Đặc so với thưa.** Các bài toán SLAM hay bundle-adjustment lớn là thưa; dùng `Eigen::SparseMatrix` với `SimplicialLDLT`, hoặc các thư viện chuyên dụng (Ceres, g2o, GTSAM).
- **Kích thước cố định so với động.** `Matrix3d`, `Vector6d` tránh cấp phát heap và mở vòng lặp; chỉ dùng kích thước động khi chiều không biết lúc biên dịch.
- **Float so với double.** `float` có khoảng 7 chữ số (`1.2e-7`), khiến condition number trên $10^{4}$ đã có vấn đề; GPU và thiết bị nhúng dùng nó cho tốc độ, với sự cẩn trọng.
- **Eigen so với BLAS/LAPACK so với NumPy.** NumPy gọi LAPACK và là oracle thông thường; Eigen tránh phụ thuộc và làm việc với expression template; link với OpenBLAS/MKL giúp ích cho ma trận lớn.
- **Bộ giải trực tiếp so với lặp.** Conjugate gradient và các phương pháp lặp tương tự tránh phân rã các hệ SPD khổng lồ nhưng cần một preconditioner tốt.

## Vận dụng và ghi nhớ

Cùng các ý tưởng xuất hiện trong Python (`numpy.linalg.lstsq` dựa trên SVD; `np.linalg.solve` là LU), trong bộ lọc Kalman (dùng Cholesky hoặc dạng Joseph để giữ hiệp phương sai đối xứng xác định dương), trong động học ngược (bình phương tối thiểu có giảm chấn chính là hồi quy ridge, M12/chuỗi R) và trong học máy (hồi quy tuyến tính, ridge, và vì sao co giãn đặc trưng quan trọng). Để ghi nhớ: sau một tuần, suy ra phương trình chuẩn từ "phần dư vuông góc với các cột" và giải thích trong hai câu vì sao $\kappa(A^\top A)=\kappa(A)^2$; rồi tính lại ước lượng số chữ số mất cho $\kappa=10^{8}$ ở cả hai phương pháp.

## Đáp án bài tập

1. $A=\begin{pmatrix}1&0\\1&1\\1&2\end{pmatrix}$, $b=(2,3,7)^\top$. $A^\top A=\begin{pmatrix}3&3\\3&5\end{pmatrix}$, $A^\top b=(12,\ 17)^\top$ ($0+3+14=17$). Định thức $6$: $a=(5\cdot12-3\cdot17)/6=9/6=1.5$, $b=(3\cdot17-3\cdot12)/6=15/6=2.5$. Giá trị khớp $=(1.5,\ 4.0,\ 6.5)$; phần dư $A\hat x-b=(-0.5,\ 1.0,\ -0.5)$. Kiểm tra: tổng $=0$; $\sum t_ir_i=0+1.0-1.0=0$. Chuẩn phần dư $\sqrt{1.5}=1.2247$.
2. (a) `llt()` (Cholesky; `ldlt()` là biến thể vững chắc); (b) `partialPivLu()`; (c) `householderQr()` hoặc `colPivHouseholderQr()`; (d) `jacobiSvd()` hoặc `bdcSvd()` (các giá trị kỳ dị cho hạng; `solve` cho nghiệm chuẩn nhỏ nhất) hoặc `completeOrthogonalDecomposition()`.
3. Phương pháp ổn định (QR): $16-\log_{10}(3.6\times10^{6})=16-6.6\approx9$ chữ số. Phương trình chuẩn: $\kappa^2=1.3\times10^{13}$, nên $16-13.1\approx3$ chữ số. Các sai số đo được trong bảng ($2.5\times10^{-11}$ và $4.9\times10^{-4}$) nhất quán về bậc độ lớn.
4. Dòng 2: `M = M.transpose();` là bug aliasing: assertion Debug "aliasing detected during transposition", hoặc một ma trận sai lặng lẽ ở Release; sửa bằng `M.transposeInPlace()` hoặc `.eval()`. Dòng 3: `auto x = ...solve(b)` lưu một biểu thức giữ reference tới phép phân rã tạm: bị treo, biểu hiện là rác hoặc ASan `stack-use-after-scope`; sửa bằng `Eigen::VectorXd x = ...`.
5. Ở Debug, một assertion kích hoạt: "aliasing detected during transposition". Ở `-O2 -DNDEBUG`, phép đánh giá tại chỗ ghi đè các phần tử nó vẫn còn cần và in ra $\begin{pmatrix}1&2\\2&4\end{pmatrix}$ cho $\begin{pmatrix}1&2\\3&4\end{pmatrix}$. Lựa chọn thay thế: `M.transposeInPlace();` hoặc `M = M.transpose().eval();`. Với tích `C = A * B;` Eigen giả định aliasing có thể xảy ra và mặc định đánh giá vào một biến tạm (chỉ dùng `.noalias()` khi bạn biết chúng không alias).
6. QR: $\approx10^{6}\times1.1\times10^{-16}=1.1\times10^{-10}$ sai số tương đối; phương trình chuẩn: $10^{12}\times1.1\times10^{-16}=1.1\times10^{-4}$. Các sai số bậc 9 đo được ($\kappa=3.6\times10^{6}$) là $2.5\times10^{-11}$ (tuyệt đối, với hệ số cỡ 1; cận là $4\times10^{-10}$) và $4.9\times10^{-4}$ (cận $1.3\times10^{-3}$): cả hai dưới các cận trường hợp xấu nhất và đúng bậc. Các cận bi quan một hệ số nhỏ.
7. `A = np.vander(t, 2, increasing=True); x = np.linalg.lstsq(A, y, rcond=None)[0]`, so sánh `x` (kỳ vọng $1.06$, $1.99333$), chuẩn phần dư ($0.44422$), và `np.linalg.cond(A)` ($10.17$) với output C++. Vì $\kappa\approx10$, dùng dung sai chặt như $10^{-12}$ tương đối; với phép khớp điều kiện xấu so sánh phần dư và giá trị khớp với dung sai $\approx\kappa\epsilon_{\text{mach}}\|y\|$.
8. Với $A=U\Sigma V^\top$ (SVD mỏng, $V$ trực giao), $A^\top A=V\Sigma^2V^\top$, có trị riêng là $\sigma_i^2$; nên $\kappa_2(A^\top A)=\sigma_{\max}^2/\sigma_{\min}^2=\kappa_2(A)^2$. Với QR: cực tiểu hóa $\|QRx-b\|$; mở rộng $Q$ thành ma trận trực giao $[Q\ Q_\perp]$, bảo toàn chuẩn: $\|QRx-b\|^2=\|Rx-Q^\top b\|^2+\|Q_\perp^\top b\|^2$. Số hạng thứ hai không phụ thuộc $x$, và số hạng thứ nhất bằng không khi $Rx=Q^\top b$, nên $\hat x=R^{-1}Q^\top b$ (tồn tại vì $R$ khả nghịch với hạng cột đầy đủ), và phần dư cực tiểu là $\|Q_\perp^\top b\|$.
9. $\kappa(A)=1/10^{-4}=10^{4}$; $\kappa(A^\top A)=10^{8}$. Với ridge: các trị riêng $\sigma^2+\lambda$: $(1+10^{-6})/(10^{-8}+10^{-6})=1.000001/1.01\times10^{-6}\approx9.9\times10^{5}$: tốt hơn khoảng 100 lần. Đánh đổi: $\lambda$ lớn hơn giảm phương sai (nghiệm ổn định) nhưng làm lệch nghiệm về không theo hướng yếu; chọn $\lambda$ bằng cross-validation hoặc đường cong L, hoặc dùng SVD cắt cụt.
10. Cholesky $\tfrac13n^3=9\times10^{6}$ flop; LU $\tfrac23n^3=1.8\times10^{7}$; QR $\tfrac43n^3=3.6\times10^{7}$. Ở $5\times10^{9}$ flop/s: 1.8 ms, 3.6 ms, 7.2 ms; tất cả vừa trong ngân sách 33 ms, nhưng Cholesky để lại nhiều chỗ nhất. Nếu ma trận thưa (như trong pose graph), Cholesky thưa dùng ít flop hơn nhiều (phụ thuộc fill-in) và bộ nhớ: lưu trữ $O(n)$ thay vì $O(n^2)$.
11. Một câu trả lời tốt gồm: bảng cho bậc 3-12 với các cột sai số; sai số SVD tương đương QR (cùng bậc); trên $[-1,1]$ các condition number giảm (với bậc 12: $1.6\times10^{4}$ thay vì $6.8\times10^{8}$), nên mọi phương pháp chính xác hơn nhiều; trên máy của bài này (50 điểm, dữ liệu không nhiễu) bậc đầu tiên có sai số trên $10^{-6}$ trên $[0,1]$ là 8 cho phương trình chuẩn và 15 cho QR và SVD; trên $[-1,1]$ là 14 cho phương trình chuẩn trong khi QR và SVD vẫn dưới $10^{-6}$ đến bậc 16; và một nhận xét về máy được dùng.

## Đọc thêm

- [Eigen: Getting started](https://eigen.tuxfamily.org/dox/GettingStarted.html) - cài đặt, ma trận, vector và chương trình đầu tiên.
- [Eigen: Linear algebra and decompositions](https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html) - giải hệ, bình phương tối thiểu, và bảng so sánh các phép phân rã.
- [MIT 18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/) - phép chiếu, bình phương tối thiểu, và SVD, với bài giảng và bài tập.

**Thực hành thêm:** [các bài tập MIT 18.06](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/assignments/) (các bộ bài về phép chiếu và bình phương tối thiểu), các trang Eigen [Linear algebra and decompositions](https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html), [Solving linear least squares systems](https://eigen.tuxfamily.org/dox/group__LeastSquares.html), [Aliasing](https://eigen.tuxfamily.org/dox/group__TopicAliasing.html) và [Lazy evaluation and `auto`](https://eigen.tuxfamily.org/dox/TopicLazyEvaluation.html), và tài liệu NumPy cho [`np.linalg.lstsq`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) và [Chebyshev polynomials](https://numpy.org/doc/stable/reference/routines.polynomials.chebyshev.html) (làm lại phép quét bậc trong một cơ sở tốt hơn).
