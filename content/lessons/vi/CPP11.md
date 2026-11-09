---
{"title": "C++ số học: Eigen, bộ giải tuyến tính và ổn định số", "summary": "Dùng ma trận và các phép phân rã của Eigen để giải bài toán bình phương tối thiểu, đồng thời dự đoán và đo xem điều kiện số (conditioning) giới hạn độ chính xác ra sao.", "objectives": ["Tạo và thao tác ma trận, vector Eigen và tránh các cạm bẫy phổ biến về expression template và aliasing.", "Chọn phép phân rã (LU, Cholesky, QR, SVD) cho một hệ tuyến tính cho trước.", "Giải bài toán bình phương tối thiểu bằng QR và bằng phương trình chuẩn (normal equations) và giải thích vì sao độ chính xác khác nhau.", "Liên hệ condition number với số chữ số bị mất, và kiểm chứng kết quả C++ với một oracle Python độc lập."]}
---
## Vì sao điều này quan trọng

Gần như mọi bài toán ước lượng và điều khiển trong robotics cuối cùng đều trở thành một hệ tuyến tính hoặc một phép khớp bình phương tối thiểu: hiệu chuẩn camera hay độ lệch (bias) IMU, khớp một mặt phẳng vào đám mây điểm, giải một bước cập nhật Kalman, tính giả nghịch đảo Jacobian cho động học ngược, tối ưu một pose graph. Trong C++ công cụ chuẩn là Eigen, một thư viện chỉ có header mà các ma trận của nó biên dịch thành những vòng lặp gọn. Nhưng có hai điều khác với đại số trong sách giáo khoa. Thứ nhất, số học dấu phẩy động chỉ có khoảng 16 chữ số có nghĩa, và một bài toán điều kiện xấu (ill-conditioned) có thể vứt đi phần lớn chúng. Thứ hai, *cách* bạn giải rất quan trọng: giải bài toán bình phương tối thiểu bằng cách lập $A^\top A$ làm bình phương condition number và có thể mất nhiều gấp đôi số chữ số so với phân rã QR. Trong thí nghiệm của bài này, cùng một phép khớp đa thức bậc 9 mất 5 chữ số với QR (sai số $2.5\times10^{-11}$) và 12 chữ số với phương trình chuẩn (sai số $4.9\times10^{-4}$). Biết gọi bộ giải nào, và cách kiểm tra đáp án với một oracle độc lập, là điều phân biệt một kết quả bạn có thể tin cậy trên robot với một kết quả chỉ biên dịch được.

## Trực giác

Hãy coi condition number $\kappa(A)$ như một kính lúp: nếu đầu vào có sai số tương đối $\epsilon$, đáp án có thể có sai số tương đối tới $\kappa\epsilon$. Việc làm tròn ở mỗi phép tính thêm vào một sai số cỡ $\epsilon_{\text{mach}}\approx1.1\times10^{-16}$, nên ngay cả một thuật toán hoàn hảo áp dụng cho bài toán có $\kappa=10^{8}$ cũng chỉ tin được tới khoảng $10^{-8}$. Một thuật toán *ổn định (stable)* không thêm sai số nào hơn mức không thể tránh đó; một thuật toán *không ổn định* thêm nhiều hơn.

Bình phương tối thiểu có một hình học đẹp. Khớp tốt nhất $A\hat x$ là hình chiếu của $b$ lên không gian cột của $A$; phần dư $r=b-A\hat x$ vuông góc với mọi cột: $A^\top r=0$. QR làm việc trực tiếp với một cơ sở trực chuẩn của không gian đó (các phép biến đổi trực giao không khuếch đại sai số). Phương trình chuẩn $A^\top A\hat x=A^\top b$ tương đương về mặt đại số nhưng bắt đầu bằng việc nhân $A^\top A$, mà condition number của nó là $\kappa(A)^2$.

![Hình chiếu của b lên không gian cột của A với phần dư vuông góc, và một biểu đồ cột về sai số của QR so với phương trình chuẩn cho đa thức bậc 3, 6, 9 và 12](/lesson-figures/CPP11.svg)

*Hình: Trái: phần dư trực giao với không gian cột. Phải: sai số hệ số đo được của QR (khoảng kappa nhân 1e-16, nét đứt) và của phương trình chuẩn (khoảng kappa bình phương nhân 1e-16, nét đứt), bậc 3, 6, 9, 12.*

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

**Hãy dự đoán trước khi tính.** Bạn khớp một đường thẳng với bốn điểm rồi khớp một đa thức bậc 12 với 50 điểm, cả hai bằng đúng cùng một đoạn code, với dữ liệu hoàn toàn không có nhiễu, nên đáp án đúng đã biết. Trước khi đọc tiếp, hãy dự đoán mỗi phép khớp trả về bao nhiêu chữ số đúng với phương pháp tốt và với phương pháp cẩu thả. Thanh trượt ở trên cho thấy quy luật quyết định điều đó.

**Một hình ảnh để nhớ.** Bình phương tối thiểu là một cái bóng. Vector $b$ là một điểm trong không gian; các cột của $A$ span một mặt phẳng; các giá trị khớp là bóng của $b$ trên mặt phẳng đó, và phần dư là đoạn từ $b$ xuống bóng, gặp mặt phẳng ở góc vuông. Nếu hai cột của $A$ chỉ các hướng khác nhau rõ rệt, mặt phẳng được xác định tốt và một cú rung nhẹ của $b$ chỉ dịch bóng nhẹ. Nếu hai cột gần song song, mặt phẳng là một dải mỏng; mô tả bóng là "bấy nhiêu cột 1 cộng bấy nhiêu cột 2" giờ cần các hệ số khổng lồ trái dấu, và sai số nhỏ của bóng biến thành sai số lớn của các hệ số. Độ nhạy đó chính là điều kiện số, và nó là tính chất của bài toán, không phải của code.

**Đáp án của dự đoán.** Đường thẳng trả về khoảng 15 chữ số đúng; đa thức bậc 12 khoảng 8 với QR và không chữ số nào với phương trình chuẩn (sai số 3.8, bảng bên dưới). Dữ liệu hoàn hảo ở cả hai trường hợp: cái thay đổi là độ nhạy của đáp án với sai số làm tròn.

**Các trực giác sai.** "Nhiều chữ số ở đầu ra nghĩa là đáp án chính xác hơn": bộ giải in 16 chữ số dù 3 trong số đó có đúng hay không. "Nếu đường cong khớp trông đúng thì các hệ số đúng": hai vector hệ số rất khác nhau có thể cho các đường cong không phân biệt được khi bài toán điều kiện xấu, vì vậy oracle của bài so sánh phần dư và giá trị khớp. "Lập $A^\top A$ chỉ là đại số": nó bình phương điều kiện số, nên lặng lẽ vứt đi một nửa số chữ số của bạn. Và "Eigen sẽ tự lo": thư viện đúng, nhưng `auto` và aliasing có thể khiến một biểu thức đúng tính ra thứ khác.

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

**Ví dụ.** Ma trận $M=\begin{pmatrix}1&2\\3&4\end{pmatrix}$ được chuyển vị ba cách trong một bản build đã tắt assertion: phép gán có aliasing `A = A.transpose();`, `transposeInPlace()` và `.eval()`. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -O2 -DNDEBUG -Wall -Wextra -I/usr/include/eigen3`. Kết quả nào đúng, và có thông báo nào được in cho kết quả sai không?

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

**Lời giải.** Chuyển vị đúng là $\begin{pmatrix}1&3\\2&4\end{pmatrix}$. Phép gán có aliasing ghi phần tử $(1,0)$ từ $(0,1)$ rồi đọc phần tử $(0,1)$ đã bị ghi đè, nên số 3 mất và ma trận in ra $\begin{pmatrix}1&2\\2&4\end{pmatrix}$ đối xứng một cách tình cờ; `transposeInPlace()` và `.eval()` (một temporary tường minh) cho kết quả đúng $\begin{pmatrix}1&3\\2&4\end{pmatrix}$. Không có thông báo nào được in cho kết quả sai, vì assertion có thể bắt lỗi đã bị loại khỏi bản biên dịch bởi `-DNDEBUG`. Chương trình in ra:

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

### Giải hệ tuyến tính

Đừng bao giờ lập nghịch đảo tường minh để giải $Ax=b$; hãy phân rã rồi giải. Chọn theo cấu trúc:

| Ma trận | Phân rã (Eigen) | Chi phí (flop, $n\times n$) | Ghi chú |
|---|---|---|---|
| vuông tổng quát | `partialPivLu()` | $\tfrac23n^3$ | nhanh, ổn định trong thực tế |
| đối xứng xác định dương (hiệp phương sai, phương trình chuẩn) | `llt()` / `ldlt()` | $\tfrac13n^3$ | Cholesky; thất bại/báo cờ nếu không SPD |
| cao, hạng đầy đủ, bình phương tối thiểu | `householderQr()` / `colPivHouseholderQr()` | $2mn^2-\tfrac23n^3$ | ổn định, phát hiện hạng nhờ pivoting |
| thiếu hạng, hoặc cần $\sigma$ | `jacobiSvd()` / `bdcSvd()` | lớn hơn | vững chắc nhất; cho condition number |

Ở $n=1000$, Cholesky là $\approx3.3\times10^{8}$ flop, khoảng 33 ms ở 10 GFLOP/s; ở $n=6$ khoảng 72 flop, không đáng kể.

**Ví dụ.** Ba khối lượng nối bằng lò xo cho một ma trận độ cứng $K$ (N/m) đối xứng xác định dương với các trị riêng 54.6, 268.0 và 427.4. Với lực $f=(2,0,5)$ N, các độ dịch chuyển $x$ (m) được tính bằng Cholesky (`llt()`), bằng LU (`partialPivLu()`) và bằng ma trận nghịch đảo tường minh. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. $\kappa(K)$ là bao nhiêu, độ dịch chuyển và phần dư ra sao, và điều gì phân biệt ba phương pháp?

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

**Lời giải.** Số điều kiện là tỉ số của các trị riêng cực trị, $\kappa(K)=427.4/54.6=7.8$. Với $n=3$, Cholesky tốn $\tfrac13n^3=9$ flop và LU tốn $\tfrac23n^3=18$ flop. Các độ dịch chuyển $x$ (m) ra giống hệt nhau từ cả ba phương pháp, với phần dư gần $10^{-15}$ N. Ở $n=3$ và $\kappa=7.8$ chưa có gì phân biệt các phương pháp; bảng ở trên cho lý do nên ưu tiên phân rã (một nửa số flop với Cholesky, không phải lập nghịch đảo) khi $n$ hoặc $\kappa$ tăng. `info() == Success` xác nhận phân rã Cholesky thấy ma trận xác định dương. Chương trình in ra:

```text
llt  x = 0.0208 0.0424 0.0568  residual 1.98603e-15
lu   x = 0.0208 0.0424 0.0568  residual 1.77636e-15
inv  x = 0.0208 0.0424 0.0568  residual 1.25607e-15
llt info() == Success: 1
```

### Bình phương tối thiểu

Cho $A\in\mathbb R^{m\times n}$, $m\ge n$, tìm $\hat x=\arg\min\|Ax-b\|_2$. Đặt gradient bằng không cho ta phương trình chuẩn $A^\top A\hat x=A^\top b$, tương đương $A^\top(A\hat x-b)=0$. Với phân rã QR mỏng $A=QR$ ($Q^\top Q=I$, $R$ tam giác trên) bài toán trở thành $R\hat x=Q^\top b$, giải bằng thế ngược; chuẩn của phần dư là $\|(I-QQ^\top)b\|$.

**Vì sao phương trình chuẩn mất độ chính xác.** Với SVD $A=U\Sigma V^\top$, $A^\top A=V\Sigma^2V^\top$ nên $\kappa(A^\top A)=\sigma_{\max}^2/\sigma_{\min}^2=\kappa(A)^2$. Một bộ giải có sai số $\approx\kappa\,\epsilon_{\text{mach}}$ áp dụng cho ma trận này cho $\kappa(A)^2\epsilon_{\text{mach}}$, trong khi QR đạt khoảng $\kappa(A)\epsilon_{\text{mach}}$ (với các bài toán phần dư nhỏ).

**Số chữ số.** Số chữ số mất $\approx\log_{10}\kappa$. Với $\kappa=3.6\times10^{6}$: QR giữ khoảng $16-6.6\approx9$ chữ số; phương trình chuẩn giữ khoảng $16-13.1\approx3$.

**Ví dụ.** Một encoder bánh xe báo vị trí $p$ (m) tại $t=0,\dots,4$ s: $0.20,\,1.10,\,1.90,\,3.20,\,3.90$. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. Khớp $p=p_0+vt$ bằng QR và bằng phương trình chuẩn: tìm vị trí đầu $p_0$ và tốc độ $v$, kiểm tra bằng tay và kiểm tra phần dư trực giao với các cột.

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

**Lời giải.** Bằng tay: $A^\top A=\begin{pmatrix}5&10\\10&30\end{pmatrix}$, $A^\top p=(10.3,\,30.1)^\top$, $\det=5\cdot30-10\cdot10=50$, nên $p_0=(30\cdot10.3-10\cdot30.1)/50=0.16$ m và $v=(5\cdot30.1-10\cdot10.3)/50=0.95$ m/s. QR và phương trình chuẩn đều cho $p_0=0.16$ m và $v=0.95$ m/s. Vector phần dư trực giao với cả hai cột ($\|A^\top r\|\approx10^{-14}$), đó là tính chất định nghĩa của nghiệm cực tiểu. Chương trình in ra:

```text
QR      p0, v = 0.1600 0.9500
normal  p0, v = 0.1600 0.9500
residual      =  0.0400 -0.0100 -0.1600  0.1900 -0.0600
||r||         = 0.2588
||A^T r||     = 6.00e-15
```

### Điều kiện số của phép khớp đa thức

Ma trận Vandermonde với các cột $1,t,t^2,\dots,t^d$ trên $[0,1]$ trở nên gần như thiếu hạng khi $d$ tăng, vì các lũy thừa cao trông giống nhau. Đo với 50 điểm cách đều:

| bậc | $\kappa(A)$ | sai số QR | sai số phương trình chuẩn |
|---|---|---|---|
| 3 | 1.2e2 | 4.0e-15 | 1.2e-12 |
| 6 | 2.0e4 | 4.6e-13 | 2.1e-08 |
| 9 | 3.6e6 | 2.5e-11 | 4.9e-04 |
| 12 | 6.8e8 | 3.4e-08 | 3.8e+00 |

(sai số là $\|\hat c-c_{\text{true}}\|$ cho dữ liệu không nhiễu $y=Ac_{\text{true}}$ với $c_{\text{true},j}=(-1)^j(1+0.1j)$, cùng các hệ số với test của lab; các hệ số khác cho sai số cùng bậc, và các chữ số cuối phụ thuộc nền tảng.) Căn giữa và co giãn $t$ về $[-1,1]$ giảm condition number bậc 12 xuống $1.6\times10^{4}$; các cơ sở đa thức trực giao (Chebyshev) còn tốt hơn. Các biện pháp cho bài toán gần suy biến: co giãn các cột, dùng SVD có cắt cụt, hoặc thêm điều chuẩn Tikhonov (ridge) $(A^\top A+\lambda I)x=A^\top b$.

**Ví dụ.** Ma trận Vandermonde bậc $d$ được lập trên 21 thời điểm cách đều, một lần trên $[0,1]$ và một lần sau khi ánh xạ $t\mapsto2t-1$ lên $[-1,1]$. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. Số điều kiện tăng theo bậc như thế nào trong mỗi trường hợp?

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

**Lời giải.** Chương trình tính $\kappa=\sigma_{\max}/\sigma_{\min}$ từ các giá trị kỳ dị. Số điều kiện trên $[0,1]$ tăng khoảng 1000 lần cho mỗi 4 bậc thêm vào (593 ở bậc 4, $6.17\times10^{5}$ ở bậc 8, $1.49\times10^{8}$ ở bậc 11), và cùng dữ liệu đó trên $[-1,1]$ vẫn tốt hơn hơn bốn bậc độ lớn ở bậc 11 ($8.52\times10^{3}$, hệ số $1.49\times10^{8}/8.52\times10^{3}\approx1.7\times10^{4}$). Việc căn giữa là miễn phí và loại bỏ phần lớn vấn đề. Chương trình in ra:

```text
degree 4: cond on [0,1] = 593   cond on [-1,1] = 17.2
degree 8: cond on [0,1] = 6.17e+05   cond on [-1,1] = 529
degree 11: cond on [0,1] = 1.49e+08   cond on [-1,1] = 8.52e+03
```

### Kiểm chứng bằng một oracle

Một cài đặt độc lập bắt được các lỗi nối dây (sai chỉ số, ma trận bị chuyển vị). So sánh *chuẩn phần dư* và *giá trị khớp*, không chỉ các hệ số, khi bài toán điều kiện xấu, vì các hệ số có thể khác nhau ở những chữ số cuối trong khi phép khớp giống hệt. Chọn dung sai từ $\kappa\,\epsilon_{\text{mach}}$, không phải $10^{-6}$ tùy tiện.

**Ví dụ.** Tám số đọc hiệu chuẩn (số đếm ADC theo điện áp tham chiếu tính bằng V) được khớp bằng bộ giải QR trong C++ và bằng oracle NumPy `lstsq`. Chương trình C++ được biên dịch như các ví dụ trước, rồi chạy chương trình Python. Hai bộ giải khớp nhau, tới bao nhiêu chữ số, và dung sai $10\,\kappa\,\epsilon_{\text{mach}}\|b\|$ của mục này có được thỏa không?

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

**Lời giải.** Khối đầu là chương trình C++ và khối thứ hai là oracle Python. Các hệ số khớp nhau tới 11 chữ số, không phải 16: chúng khác nhau khoảng $10^{-12}$ ở các chữ số cuối được in, trong khi chuẩn phần dư khớp ở cả 12 chữ số được in. Với $\kappa(A)=6.28$ và $\|b\|\approx5.9\times10^{3}$, dung sai là $10\,\kappa\,\epsilon_{\text{mach}}\|b\|=10\cdot6.28\cdot2.2\times10^{-16}\cdot5.9\times10^{3}=8.3\times10^{-11}$, được thỏa với biên rộng bởi độ lệch khoảng $10^{-12}$. Chuẩn phần dư 9.72 lớn vì bộ chuyển đổi không tuyến tính; đó là tính chất của dữ liệu, và oracle cho cùng giá trị. Chương trình C++ in ra khối đầu và chương trình Python in ra khối thứ hai:

```text
x = [-2.642857142857, 831.619047619048]
residual norm = 9.719886340703
```

```text
x = [-2.642857142856, 831.619047619048]
residual norm = 9.719886340703
cond(A) = 6.2781, tolerance 10*cond*eps*||b|| = 8.27e-11
```

### Bình phương tối thiểu bằng phép chiếu, và một cái bẫy số học

Nghiệm bình phương tối thiểu $\hat x$ được đặc trưng bởi $A^\top(A\hat x-b)=0$: phần dư $r=b-A\hat x$ vuông góc với mọi cột của $A$ (Boyd và Vandenberghe, VMLS, §12.2, phương trình chuẩn (12.4)). Với $A=QR$, các cột của $Q$ span cùng không gian, nên $A\hat x=QQ^\top b$ (VMLS, Bài tập 12.8). Vì $r\perp A\hat x$, Pythagoras cho $\|b\|^2=\|A\hat x\|^2+\|r\|^2$, và $\|A\hat x\|^2=\|Q^\top b\|^2$ vì $Q$ có các cột trực chuẩn. Do đó
$$\|r\|^2=\|b\|^2-\|Q^\top b\|^2 .$$
Đẳng thức này chính xác nhưng nguy hiểm về số học. Cả hai số hạng được tính với sai số tuyệt đối cỡ $\epsilon_{\text{mach}}\|b\|^2$, nên khi phép khớp tốt ($\|r\|\ll\|b\|$) thì *hiệu* có sai số tương đối cỡ $\epsilon_{\text{mach}}\|b\|^2/\|r\|^2$: mọi chữ số có nghĩa mất hết khi $\|r\|/\|b\|\lesssim\sqrt{\epsilon_{\text{mach}}}\approx10^{-8}$. Hãy tính vector phần dư $b-A\hat x$ rồi lấy chuẩn của nó (Bài tập 12). Cùng mẫu "trừ hai số lớn gần bằng nhau" là điều làm phương trình chuẩn mong manh.

**Ví dụ.** Khớp một hằng số với ba số đọc $b=(2\cdot10^{8}+2,\ 2\cdot10^{8},\ 2\cdot10^{8}-2)$. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`. Bình phương phần dư $\|r\|^2$ tính bằng công thức Pythagoras $\|b\|^2-\|Q^\top b\|^2$ là bao nhiêu, và khi lập vector phần dư trước thì là bao nhiêu?

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

**Lời giải.** Phần dư chính xác là $r=(2,0,-2)$, nên $\|r\|^2=8$. Công thức Pythagoras trừ hai số gần $1.2\cdot10^{17}$, nơi các số double cách nhau 16, và trả về 0.0; lập vector phần dư trước trả về 8.0. Sai số tương đối dự đoán $\epsilon\|b\|^2/\|r\|^2=1.1\cdot10^{-16}\cdot1.2\cdot10^{17}/8\approx1.6$ đã vượt quá 100%, khớp với việc mất đáp số. Chương trình in ra:

```text
||b||^2 - ||Q^T b||^2 = 0.0
||b - A xhat||^2      = 8.0
```

### Phương pháp Gram (phương trình chuẩn) so với QR: chi phí và độ chính xác

Lập $G=A^\top A$ tận dụng đối xứng tốn khoảng $mn^2$ flop và phân rã Cholesky tốn $\tfrac13n^3$, nên phương pháp Gram tốn $mn^2+\tfrac13n^3$, trong khi Householder QR tốn $2mn^2-\tfrac23n^3$ (bảng của bài). Với $m\gg n$ phương pháp Gram nhanh gấp khoảng hai lần, với $m\approx n$ chỉ nhanh khoảng 1,1 đến 1,4 lần (VMLS, Bài tập 12.16, phần nhận xét nói mức chênh tốc độ quá nhỏ để có ý nghĩa thực tế). Độ chính xác mới quyết định. Một bộ giải backward-stable trên $G$ có sai số tương đối $\approx\kappa(G)\epsilon_{\text{mach}}=\kappa(A)^2\epsilon_{\text{mach}}$, so với $\kappa(A)\epsilon_{\text{mach}}$ của QR. Danh mục các phân rã dense của Eigen phản ánh điều này: `LLT` "very fast" nhưng độ chính xác "depends on condition number", còn `ColPivHouseholderQR` là "fast" với độ tin cậy "good" và làm lộ hạng (rank-revealing) (Eigen, *Catalogue of dense decompositions*). Một quy tắc dùng được: phương trình chuẩn chỉ chấp nhận được khi $\kappa(A)^2\epsilon_{\text{mach}}$ thấp hơn hẳn độ chính xác bạn cần, tức $\kappa(A)\lesssim10^{3}$ đến $10^{4}$ cho sáu chữ số đúng; điểm mạnh của chúng là khi $G$ rẻ để có (ví dụ cộng dồn trên dữ liệu streaming).

![Tỉ số flop của QR so với phương pháp Gram theo m chia n, và số chữ số đúng của cả hai cho phép khớp bậc 8](/lesson-figures/CPP11-2.svg)

*Hình: Trái: QR tốn nhiều nhất gấp đôi flop của phương pháp Gram (tỉ số 1 với ma trận vuông, 1.99 tại m = 2000, n = 8). Phải: hệ số 2 đó đổi lấy khoảng 5 chữ số đúng thêm ở kappa = 6.16e5.*

**Ví dụ.** Một phép khớp bậc 8 với 40 điểm trên $[0,1]$ có hệ số đã biết $c_j=(-1)^j(2+0.5j)$ ($\|c\|=12.6$) và dữ liệu không nhiễu. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. QR và phương pháp Gram (phương trình chuẩn) trả lại hệ số chính xác đến đâu, so với $\kappa\epsilon$ và $\kappa^2\epsilon$ thì sao, và QR tốn bao nhiêu flop cho bài toán $2000\times8$?

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

**Lời giải.** Ma trận có $\kappa(A)=6.16\times10^{5}$, nên $\kappa\epsilon=6.16\times10^{5}\cdot1.1\times10^{-16}=6.8\times10^{-11}$ và $\kappa^2\epsilon=4.2\times10^{-5}$. QR trả lại hệ số với sai số $1.3\times10^{-10}$ (khoảng $10^{-11}$ tương đối), phương pháp Gram với $1.2\times10^{-5}$ (khoảng $10^{-6}$ tương đối): sai số đo được bám theo $\kappa\epsilon$ và $\kappa^2\epsilon$ trong phạm vi hệ số 2 đến 4. Giá của QR tính bằng flop cho bài toán $2000\times8$ là hệ số 1.99, không đáng kể ở cỡ này. Chương trình in ra:

```text
cond(A) = 6.16e+05, kappa*eps = 6.8e-11, kappa^2*eps = 4.2e-05
QR error   1.3e-10
Gram error 1.2e-05
flops, m=2000, n=8: Gram 1.28e+05, QR 2.56e+05, ratio 1.99
```

### Bình phương tối thiểu lặp: phép lặp Richardson

Với $A$ rất lớn hoặc thưa, có thể bạn chỉ nhân được với $A$ và $A^\top$. Phép lặp $x_{k+1}=x_k-\mu A^\top(Ax_k-b)$ (VMLS, Bài tập 12.13) có $\hat x$ là điểm bất động. Trừ $\hat x$ và dùng $A^\top(A\hat x-b)=0$, sai số $e_k=x_k-\hat x$ thỏa $e_{k+1}=(I-\mu A^\top A)e_k$. Trong cơ sở singular phải của $A=U\Sigma V^\top$, thành phần $i$ của sai số được nhân với $1-\mu\sigma_i^2$ mỗi bước. Chọn $\mu=1/\sigma_{\max}^2$: các hệ số nằm trong $[0,\,1-1/\kappa^2]$ với $\kappa=\sigma_{\max}/\sigma_{\min}$, nên
$$\|e_k\|\le\Big(1-\frac1{\kappa^2}\Big)^k\|e_0\|,\qquad k\ge\frac{\ln(\text{tol})}{\ln(1-1/\kappa^2)}\approx\kappa^2\ln\frac1{\text{tol}}.$$
Bình phương của số điều kiện lại xuất hiện, lần này là số vòng lặp: giảm sai số $10^{-6}$ cần khoảng 1375 vòng với $\kappa=10$ và khoảng 138.000 với $\kappa=100$. Vì vậy người ta dùng tiền điều kiện (preconditioning), hoặc phương pháp Krylov như conjugate gradient trên cùng phương trình chuẩn; Richardson là thành viên đơn giản nhất của họ này và là mô hình đúng để hiểu vì sao điều kiện số chi phối mọi thứ trong bài.

![Cận sai số Richardson theo số bước lặp cho kappa bằng 2, 4 và 6](/lesson-figures/CPP11-3.svg)

*Hình: Gấp đôi kappa thì số bước lặp tăng khoảng 4 lần: 49, 215 và 491 bước để đạt 1e-6.*

**Ví dụ.** Một ma trận $40\times4$ được dựng với các giá trị kỳ dị $1,\ 0.75,\ 0.5,\ 1/6$, và gradient descent với bước $\mu=1/\sigma_{\max}^2=1$ chạy cho đến khi sai số giảm $10^{-6}$ lần. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. Cận dự đoán bao nhiêu bước, vòng lặp thực tế mất bao nhiêu bước, và cả lần chạy tốn bao nhiêu flop?

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

**Lời giải.** Số điều kiện là $\kappa=1/(1/6)=6$. Cận cho $k\ge\ln(10^{-6})/\ln(1-1/36)=490.4$ bước (đường tắt $\kappa^2\ln10^6=497.4$); vòng lặp dừng sau 488, nằm ngay trong cận, vì sai số ban đầu ngẫu nhiên có ít thành phần theo hướng kỳ dị chậm nhất. Mỗi bước tốn hai phép nhân ma trận-vector, $2\cdot2\cdot40\cdot4=640$ flop, nên cả lần chạy tốn khoảng $488\cdot640\approx3.1\times10^{5}$ flop. Chương trình in ra:

```text
iterations to reach 1e-6: 488
bound ln(1e-6)/ln(1-1/kappa^2) = 490.4
kappa^2 ln(1e6) = 497.4
```

### Điều kiện (conditioning) so với ổn định (stability): điều kiện số chặn cái gì

Hai ý niệm hay bị lẫn. **Conditioning** của một bài toán đo nghiệm chính xác thay đổi bao nhiêu khi đầu vào thay đổi nhẹ; nó thuộc về bài toán. **Stability** của một thuật toán đo xem đáp án tính được có phải là đáp án chính xác của một đầu vào bị nhiễu nhẹ hay không; nó thuộc về phương pháp. Với $Ax=b$, $A$ khả nghịch, giả sử vế phải bị nhiễu thành $b+\delta b$ và $A(x+\delta x)=b+\delta b$. Khi đó $\delta x=A^{-1}\delta b$, nên $\|\delta x\|\le\|A^{-1}\|\,\|\delta b\|$; và $\|b\|=\|Ax\|\le\|A\|\,\|x\|$ cho $1/\|x\|\le\|A\|/\|b\|$. Nhân lại,
$$\frac{\|\delta x\|}{\|x\|}\le\kappa(A)\,\frac{\|\delta b\|}{\|b\|},\qquad\kappa(A)=\|A\|\,\|A^{-1}\|.$$
Trong chuẩn 2, $\kappa=\sigma_{\max}/\sigma_{\min}$. Chặn này *đạt được*: lấy $b$ theo vector singular trái $u_{\max}$ (khi đó $\|x\|=\|b\|/\sigma_{\max}$ nhỏ nhất có thể) và $\delta b$ theo $u_{\min}$ (khi đó $\|\delta x\|=\|\delta b\|/\sigma_{\min}$ lớn nhất có thể); độ nhạy của một phần tử đơn lẻ là câu hỏi của VMLS Bài tập 11.26. Một thuật toán **backward-stable** trả về $\hat x$ giải $(A+E)\hat x=b$ với $\|E\|\approx\epsilon_{\text{mach}}\|A\|$. Kết hợp hai điều, bộ giải backward-stable có sai số tiến tối đa khoảng $\kappa(A)\,\epsilon_{\text{mach}}$: số chữ số mất là $\log_{10}\kappa$ không tránh được, và không thuật toán nào làm tốt hơn trên đầu vào đó, vì làm tròn dữ liệu về double đã là một nhiễu cỡ đó. Phương trình chuẩn *không* backward-stable cho bài toán bình phương tối thiểu: lập $A^\top A$ đã làm nhiễu dữ liệu ở mức tương đối $\epsilon_{\text{mach}}$ trong một ma trận có điều kiện số $\kappa^2$.

**Ví dụ.** Với $A=\mathrm{diag}(1,\,10^{-3})$ ($\kappa=1000$) và $b=(1,0)$, cùng một nhiễu tuyệt đối $|\delta b|=10^{-6}$ được áp theo hai hướng kỳ dị. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. Sai số tương đối của $x$ là bao nhiêu trong mỗi trường hợp?

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

**Lời giải.** Theo $u_{\max}$, sai số tương đối của $x$ bằng sai số tương đối của $b$ (tỉ số 1.0). Theo $u_{\min}$ nó lớn gấp 1000 lần: $10^{-6}$ thành $10^{-3}$, đúng là cận $\kappa\,\|\delta b\|/\|b\|=1000\cdot10^{-6}$ đạt chính xác. Cùng ma trận và cùng thuật toán cho cả hai kết quả; chỉ hướng của sai số khác nhau. Chương trình in ra:

```text
db along u_max: |db|/|b| = 1.0e-06, |dx|/|x| = 1.0e-06, ratio = 1.0
db along u_min: |db|/|b| = 1.0e-06, |dx|/|x| = 1.0e-03, ratio = 1000.0
```

### Khi phương trình chuẩn hỏng hoàn toàn: ma trận Läuchli

Lấy $A=\begin{pmatrix}1&1\\\delta&0\\0&\delta\end{pmatrix}$. Khi đó $A^\top A=\begin{pmatrix}1+\delta^2&1\\1&1+\delta^2\end{pmatrix}$ với $\det=\delta^2(2+\delta^2)$ và các giá trị singular $\sigma_{\max}=\sqrt{2+\delta^2}$, $\sigma_{\min}=\delta$, nên $\kappa(A)\approx\sqrt2/\delta$: với $\delta=10^{-8}$ khoảng $1{,}4\times10^{8}$, một bài toán mà độ chính xác kép giải được tới khoảng 8 chữ số. Nhưng $1+\delta^2=1+10^{-16}$ được làm tròn về $1$ trong độ chính xác kép (nửa đơn vị ở chữ số cuối của 1 là $1{,}1\times10^{-16}$, lớn hơn $10^{-16}$), ma trận Gram tính được đúng bằng $\begin{pmatrix}1&1\\1&1\end{pmatrix}$ và *suy biến*: phương trình chuẩn hỏng hẳn, không chỉ mất chữ số. Thông tin về $\delta^2$ đã bị hủy trong phép nhân, còn QR, không bao giờ lập $A^\top A$, không bị ảnh hưởng (Ví dụ có lời giải, trường hợp 2). Đây là phiên bản cực đoan của bảng trong bài: điều kiện số bình phương $2\times10^{16}$ vượt $1/\epsilon_{\text{mach}}$.

![Sai số tương đối của QR và phương trình chuẩn trên ma trận Läuchli theo delta](/lesson-figures/CPP11-5.svg)

*Hình: QR giữ ở mức sai số làm tròn trong khi phương trình chuẩn mất độ chính xác như 1/delta bình phương và thất bại khi delta bằng 1e-8 hoặc nhỏ hơn.*

**Ví dụ.** Lấy $\delta=10^{-7}$ và $b=(1,1,0)^\top$. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. Nghiệm bình phương tối thiểu chính xác là gì, và QR cùng phương trình chuẩn chính xác đến đâu?

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

**Lời giải.** Nghiệm chính xác suy ra từ $x_1-x_2=1/\delta$ và $x_1+x_2=(2+\delta)/(2+\delta^2)$ (trừ và cộng hai phương trình chuẩn): $(5000000.5,\,-4999999.5)$. $\kappa(A)=1.41\times10^{7}$, nên QR chính xác khoảng 9 chữ số (ở đây nó đạt $10^{-16}$); $\kappa(A^\top A)=2\times10^{14}$, và phần tử Gram tính được $G_{00}-1=9.99\times10^{-15}$ mang sai số 0.08% trong $\delta^2$, trở thành sai số tương đối $8\times10^{-4}$ trong $x$ (4000 theo giá trị tuyệt đối). Thêm một bậc mười nữa của $\delta$ làm ma trận Gram suy biến hoàn toàn, như hình cho thấy. Chương trình in ra:

```text
kappa(A) = 1.41e+07, kappa(G) = 2.00e+14
exact  x = 5000000.5000 -4999999.5000
QR     x = 5000000.5000 -4999999.5000   relative error 1.3e-16
normal x = 5004000.0889 -5003999.0889   relative error 8.0e-04
```

### Thiếu hạng và SVD cắt cụt

Nếu các cột của $A$ phụ thuộc (hoặc gần phụ thuộc), nghiệm cực tiểu bình phương không duy nhất. Với $A=U\Sigma V^\top$ và $r$ là số giá trị singular được giữ, nghiệm bình phương tối thiểu *chuẩn nhỏ nhất* là $\hat x=\sum_{i\le r}\frac{u_i^\top b}{\sigma_i}v_i=A^\dagger b$, $A^\dagger=V\Sigma^{+}U^\top$, trong đó $\Sigma^{+}$ nghịch đảo các giá trị singular khác không và đặt phần còn lại về không (giả nghịch đảo của VMLS §11.5 tổng quát hóa ra ngoài trường hợp cột độc lập). Mỗi số hạng nhân thành phần dữ liệu $u_i^\top b$ với $1/\sigma_i$, nên nhiễu theo hướng có $\sigma_i$ rất nhỏ bị khuếch đại rất mạnh; *cắt cụt* bỏ các số hạng đó và đánh đổi một độ chệch nhỏ lấy việc giảm lớn phương sai, cùng tinh thần với tham số ridge của Bài tập 9. `BDCSVD`/`JacobiSVD` của Eigen cho phép điều này qua một ngưỡng trên giá trị singular tương đối với giá trị lớn nhất, và `completeOrthogonalDecomposition` cho cùng nghiệm chuẩn nhỏ nhất với giá rẻ hơn (Eigen, *Catalogue of dense decompositions*). Ngưỡng là một quyết định mô hình hóa: chọn từ mức nhiễu của dữ liệu, không chỉ từ $\epsilon_{\text{mach}}$.

**Ví dụ.** Cột thứ ba của ma trận $6\times3$ bằng cột 1 cộng cột 2 sai khác một dao động $10^{-9}$. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), Eigen 3.4.0, `-std=c++20 -Wall -Wextra -I/usr/include/eigen3`. Các giá trị kỳ dị là gì, và hệ số cùng phần dư khác nhau thế nào giữa nghiệm không cắt cụt và nghiệm cắt cụt ở $10^{-6}\sigma_{\max}$?

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

**Lời giải.** Các giá trị kỳ dị là 15.13, 2.243 và $1.7\times10^{-9}$. Giữ cả ba số hạng chia thành phần dữ liệu theo $v_3$ cho $1.7\times10^{-9}$: các hệ số lên tới $2.5\times10^{8}$ (chuẩn $4.3\times10^{8}$) với phần dư 3.4425. Cắt cụt ở $10^{-6}\sigma_{\max}$ (hạng 2) cho các hệ số có chuẩn 1.28 và phần dư 3.5183, chỉ cao hơn $3.5183/3.4425-1=2.2\%$: một độ chệch nhỏ đổi lấy mức giảm phương sai khổng lồ. Chương trình in ra:

```text
singular values: 1.513e+01 2.243e+00 1.704e-09
rank kept = 2
untruncated x = 2.462e+08 2.462e+08 -2.462e+08   |x| = 4.26e+08   |r| = 3.4425
truncated   x = 0.9443 -0.0917 0.8526   |x| = 1.2755   |r| = 3.5183
```

## Ví dụ có lời giải

### Trường hợp 1: trường hợp cơ bản

**Đề bài.** Khớp đường thẳng $y=c_0+c_1t$ bằng bình phương tối thiểu với bốn điểm $(0,1),(1,3),(2,4),(3,8)$, $t$ tính bằng s và $y$ bằng m. Cho $\hat c$, vector phần dư, và kiểm tra rằng phần dư trực giao với các cột.

**Lời giải.**

1. Viết dữ liệu dưới dạng $A c\approx y$ (thiết lập bình phương tối thiểu của phần lý thuyết). $A=\begin{pmatrix}1&0\\1&1\\1&2\\1&3\end{pmatrix}$, $y=(1,3,4,8)^\top$.
2. Phương trình chuẩn $A^\top A\hat c=A^\top y$. Các phần tử là tổng của các cột: $A^\top A=\begin{pmatrix}4&6\\6&14\end{pmatrix}$ ($4$; $0+1+2+3=6$; $0+1+4+9=14$) và $A^\top y=(1+3+4+8,\ 0\cdot1+1\cdot3+2\cdot4+3\cdot8)^\top=(16,\ 35)^\top$.
3. Định thức là $4\cdot14-6\cdot6=20$. Theo công thức nghịch đảo $2\times2$, $c_0=\dfrac{14\cdot16-6\cdot35}{20}=\dfrac{224-210}{20}=0.7$ m và $c_1=\dfrac{4\cdot35-6\cdot16}{20}=\dfrac{140-96}{20}=2.2$ m/s.
4. Giá trị khớp $0.7+2.2t=(0.7,\ 2.9,\ 5.1,\ 7.3)$ m, nên phần dư là $r=A\hat c-y=(-0.3,\ -0.1,\ 1.1,\ -0.7)$ m.
5. Tối ưu $A^\top r=0$: $\sum r_i=-0.3-0.1+1.1-0.7=0$ và $\sum t_ir_i=0-0.1+2.2-2.1=0$.
6. Chuẩn phần dư $\sqrt{0.09+0.01+1.21+0.49}=\sqrt{1.8}=1.3416$ m.
7. Điều kiện số: các giá trị kỳ dị của $A$ cho $\kappa(A)=3.76$, nên chỉ khoảng $\log_{10}3.76\approx0.6$ chữ số gặp rủi ro và cả hai phương pháp đều chạy được; ở ca bậc 12 của phần lý thuyết thì không.

**Kiểm tra.** `numpy.linalg.lstsq` trả về $(0.7,\ 2.2)$, chuẩn phần dư $1.3416$ và $\kappa=3.7589$, giống phép tính tay. Các tổng ở bước 5 triệt tiêu chính xác, như hình dưới cho thấy.

![Đường bình phương tối thiểu qua bốn điểm cùng các phần dư theo phương thẳng đứng](/lesson-figures/CPP11-4.svg)

*Hình: Bốn phần dư của trường hợp 1 vẽ đúng tỉ lệ; tổng và tổng có trọng số t của chúng triệt tiêu, đó chính là tính trực giao A^T r = 0.*

**Rút ra.** Cực tiểu là điểm mà phần dư vuông góc với mọi cột của $A$; hai tổng bằng không là toàn bộ phép thử.

### Trường hợp 2: bài toán Läuchli (phương trình chuẩn thất bại, QR thành công)

**Đề bài.** Giải $\min_x\|Ax-b\|$ với $A=\begin{pmatrix}1&1\\\delta&0\\0&\delta\end{pmatrix}$, $\delta=10^{-8}$, $b=A\,(1,1)^\top=(2,\delta,\delta)^\top$, nên nghiệm chính xác là $\hat x=(1,1)$ với phần dư bằng không. Dùng độ chính xác kép IEEE ($\epsilon_{\text{mach}}=1.1\times10^{-16}$).

**Lời giải.**

1. **Điều kiện số.** $A^\top A=\begin{pmatrix}1+\delta^2&1\\1&1+\delta^2\end{pmatrix}$; các trị riêng của nó là $2+\delta^2$ và $\delta^2$, nên $\sigma_{\max}=\sqrt{2+\delta^2}\approx1.414$, $\sigma_{\min}=\delta=10^{-8}$ và $\kappa(A)\approx1.41\times10^{8}$. Phương pháp ổn định giữ khoảng $16-8.15\approx8$ chữ số. Với phương trình chuẩn $\kappa^2\approx2\times10^{16}>1/\epsilon_{\text{mach}}$: không chữ số nào được đảm bảo.
2. **Phương trình chuẩn.** Trong dấu phẩy động $1+\delta^2=1+10^{-16}\to1$ (nửa đơn vị ở chữ số cuối của 1 là $1.1\times10^{-16}$), nên $A^\top A$ tính được là $\begin{pmatrix}1&1\\1&1\end{pmatrix}$ với định thức 0 (`numpy.linalg.det` cho $0.0$). Phép giải báo ma trận suy biến; không thể sửa gì sau đó, vì thông tin về $\delta^2$ đã mất trong phép nhân.
3. **QR.** QR Householder của $A$ rồi thế ngược (lý thuyết: $R\hat x=Q^\top b$) trả về $\hat x=(1.0,\,1.0)$ (`numpy.linalg.qr` và `solve(R, Q.T @ b)`, in ra `[1. 1.]`).
4. **Một trường hợp nhẹ hơn.** Với $\delta=10^{-4}$: $\kappa(A)=1.4\times10^{4}$ và $\kappa(A^\top A)=2.0\times10^{8}$. Phương trình chuẩn giờ chạy được và trả về $(1.0000000056,\,0.9999999944)$, sai số $7.9\times10^{-9}$, phù hợp với ước lượng $\kappa^2\epsilon_{\text{mach}}=2\times10^{8}\cdot1.1\times10^{-16}\approx2\times10^{-8}$; QR trả về sai số $3\times10^{-16}$, dưới chặn $\kappa\epsilon_{\text{mach}}\approx1.5\times10^{-12}$ của nó.
5. **Trong C++** điều này là `A.householderQr().solve(b)` so với `(A.transpose()*A).llt().solve(A.transpose()*b)`; lời gọi thứ hai thường báo `info() == NumericalIssue` (pivot bằng không) hoặc trả về rác.

**Kiểm tra.** Định thức của ma trận Gram tính được ($0.0$), kết quả QR `[1. 1.]` và các sai số ở $\delta=10^{-4}$ ở trên đều được tính bằng NumPy với độ chính xác kép; dự đoán $\kappa^2\epsilon_{\text{mach}}$ khớp về bậc độ lớn.

**Rút ra.** Cùng dữ liệu cho thất bại ở $\delta=10^{-8}$ với phương trình chuẩn và 8 chữ số đúng với QR: hãy kiểm tra $\kappa(A)$ trước khi chọn phương pháp.

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

12. **(Challenge)** Phần dư qua đẳng thức Pythagoras. (a) Chứng minh $\|b-A\hat x\|^2=\|b\|^2-\|Q^\top b\|^2$ cho $A=QR$ có các cột độc lập tuyến tính. (b) Lấy $A=(1,1,1)^\top$ và $b=(10^8+1,\,10^8,\,10^8-1)^\top$. Tính bằng tay chuẩn bình phương chính xác của phần dư, rồi tính vế phải của đẳng thức trong độ chính xác kép IEEE và so sánh. (c) Giải thích sự thất bại một cách định lượng và nêu công thức bền vững. (d) Ở tỉ lệ $\|r\|/\|b\|$ nào đẳng thức mất hết chữ số trong độ chính xác kép? (adapted from Boyd and Vandenberghe, VMLS, Exercise 12.8(b); the numerical trap is added)
13. **(Challenge)** Phép lặp Richardson. (a) Chứng minh $x_{k+1}=x_k-\mu A^\top(Ax_k-b)$ với $\mu=1/\sigma_{\max}(A)^2$ thỏa $\|x_k-\hat x\|\le(1-1/\kappa^2)^k\|x_0-\hat x\|$. (b) Cần bao nhiêu vòng lặp để giảm sai số $10^{-6}$ với $\kappa=10,100,1000$? (c) Kiểm tra dự đoán bằng số trên ma trận $60\times5$ có các giá trị singular cách đều tuyến tính từ 1 đến $1/\kappa$ với $\kappa=10$ và $100$. (d) So với giải QR trực tiếp cho $n=5$ và nói khi nào phép lặp vẫn được ưu tiên. (adapted from Boyd and Vandenberghe, VMLS, Exercise 12.13)
14. **(Challenge)** Bình phương tối thiểu có trọng số. (a) Chứng minh $\sum_iw_i(\tilde a_i^\top x-b_i)^2=\|D(Ax-b)\|^2$ với $D$ đường chéo, và $DA$ có các cột độc lập khi $A$ có và mọi $w_i>0$. (b) Suy ra $\hat x=(A^\top WA)^{-1}A^\top Wb$ với $W=\mathrm{diag}(w)$. (c) Với ma trận Vandermonde bậc ba trên 50 điểm cách đều của $[0,1]$ ($\kappa=117{,}9$) cho trọng số $10^{-6}$ cho 25 hàng đầu và $1$ cho 25 hàng còn lại. Tính $\kappa(DA)$ và $\kappa((DA)^\top DA)$, và nói điều này có nghĩa gì khi giải bài toán có trọng số bằng phương trình chuẩn. (adapted from Boyd and Vandenberghe, VMLS, Exercise 12.4)
15. **(Challenge)** Phương pháp Gram so với QR. (a) Đếm flop của cả hai phương pháp như trong bảng của bài. (b) Tính tỉ lệ cho $(m,n)=(10^4,10)$ và $(600,500)$. (c) Với phép khớp không nhiễu $b=Ac_{\text{true}}$ trên 50 điểm cách đều của $[0,1]$ với $c_{\text{true},j}=(-1)^j(1+0{,}1j)$, đo $\|\hat c-c_{\text{true}}\|$ cho bậc 5, 7, 9 bằng QR và bằng phương pháp Gram, và so với $\kappa^2\epsilon_{\text{mach}}$ và $\kappa\epsilon_{\text{mach}}$. (d) Nêu một quy tắc quyết định. (adapted from Boyd and Vandenberghe, VMLS, Exercise 12.16; the accuracy study is added)

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
12. (a) $A\hat x=QQ^\top b$ là hình chiếu trực giao của $b$ lên $\mathrm{range}(A)=\mathrm{range}(Q)$, nên $r=b-QQ^\top b$ vuông góc với $QQ^\top b$: $Q^\top r=Q^\top b-Q^\top QQ^\top b=0$ và $(QQ^\top b)^\top r=(Q^\top b)^\top Q^\top r=0$. Khi đó $\|b\|^2=\|QQ^\top b\|^2+\|r\|^2$ và $\|QQ^\top b\|^2=b^\top QQ^\top QQ^\top b=\|Q^\top b\|^2$, do đó $\|r\|^2=\|b\|^2-\|Q^\top b\|^2$. (b) $Q=(1,1,1)^\top/\sqrt3$, $Q^\top b=3\cdot10^8/\sqrt3$, nên $\|Q^\top b\|^2=3\cdot10^{16}$. $\|b\|^2=(10^8+1)^2+10^{16}+(10^8-1)^2=3\cdot10^{16}+2$. Chính xác $\|r\|^2=2$ (thật vậy $r=b-10^8\mathbf 1=(1,0,-1)$, $\|r\|^2=2$). Trong float64 (numpy) vế phải tính ra $-12.0$: âm, điều không thể với một chuẩn bình phương. (c) Các double gần $3\cdot10^{16}$ cách nhau $4$ (vì $2^{53}\approx9{,}0\cdot10^{15}$), nên $3\cdot10^{16}+2$ thậm chí không biểu diễn được, và mỗi số hạng có sai số tuyệt đối vài đơn vị, lớn hơn đáp án thật 2. Ước lượng sai số tương đối $\epsilon\|b\|^2/\|r\|^2=1{,}1\cdot10^{-16}\cdot3\cdot10^{16}/2\approx1{,}7$ đã vượt 100%. Công thức bền vững: lập $r=b-A\hat x$ (ở đây $(1,0,-1)$ sai khác làm tròn của $\hat x$; còn tốt hơn là tính $b-\bar b$ cho trường hợp một cột này) rồi lấy $\|r\|^2$. (d) Sai số tương đối khoảng $\epsilon\|b\|^2/\|r\|^2$, đạt 1 ở $\|r\|/\|b\|\approx\sqrt\epsilon\approx10^{-8}$. Trong ví dụ $\|r\|/\|b\|=\sqrt2/(\sqrt3\cdot10^8)\approx8\cdot10^{-9}$, ngay dưới ngưỡng đó.
13. (a) Vì $A^\top(A\hat x-b)=0$, $e_{k+1}=x_{k+1}-\hat x=e_k-\mu A^\top Ae_k=(I-\mu A^\top A)e_k$. Với $A=U\Sigma V^\top$ và $e_k=V c_k$, $c_{k+1,i}=(1-\mu\sigma_i^2)c_{k,i}$. Với $\mu=1/\sigma_{\max}^2$, $0\le1-\mu\sigma_i^2\le1-\sigma_{\min}^2/\sigma_{\max}^2=1-1/\kappa^2$, nên $\|c_k\|\le(1-1/\kappa^2)^k\|c_0\|$ và $\|e_k\|=\|c_k\|$ vì $V$ trực giao. (b) $k\ge\ln10^{-6}/\ln(1-1/\kappa^2)$: $\kappa=10$: $1374{,}6\to1375$; $\kappa=100$: $138.148{,}2\to138.149$; $\kappa=1000$: $13.815.503{,}6\to13.815.504$ (khoảng $\kappa^2\ln10^6=13{,}8\,\kappa^2$). (c) Một lần chạy với các thừa số trực giao ngẫu nhiên (seed 0), dừng khi sai số xuống dưới $10^{-6}$ giá trị đầu, sau 1374 vòng với $\kappa=10$ và 138.098 với $\kappa=100$, khớp dự đoán trong 0,04%. (Chặn đạt được khi sai số ban đầu có thành phần theo vector singular nhỏ nhất, điều thường gặp.) (d) QR cho $m=60$, $n=5$ tốn khoảng $2mn^2-\tfrac23n^3\approx2900$ flop, một lần; Richardson với $\kappa=10$ tốn khoảng $4mn\cdot1375\approx1{,}6\cdot10^{6}$. Với bài toán dense nhỏ, QR trực tiếp thắng hàng nhiều bậc độ lớn. Phép lặp được ưu tiên khi $A$ khổng lồ và thưa (hoặc chỉ có dưới dạng tích ma trận-vector), nơi không thể lưu phân rã và mỗi vòng chỉ tốn hai phép nhân, và khi $\kappa$ vừa phải hoặc tiền điều kiện làm nó vừa phải.
14. (a) Đặt $D=\mathrm{diag}(\sqrt{w_1},\dots,\sqrt{w_m})$; khi đó $\|D(Ax-b)\|^2=\sum_i w_i(\tilde a_i^\top x-b_i)^2$. Nếu $DAx=0$ thì $Ax=0$ vì $D$ khả nghịch với $w_i>0$, nên $x=0$ khi $A$ có các cột độc lập. (b) Áp dụng (12.5) cho $B=DA$, $d=Db$: $\hat x=(B^\top B)^{-1}B^\top d=(A^\top D^2A)^{-1}A^\top D^2b=(A^\top WA)^{-1}A^\top Wb$ với $W=D^2$. (c) Tính được: $\kappa(A)=117{,}86$; $\kappa(DA)=1807{,}18$ (trọng số $10^{-3}$ và 1 trong $D$); $\kappa((DA)^\top DA)=\kappa(DA)^2=3{,}27\cdot10^{6}$. Giảm trọng số một nửa số hàng xuống $10^{-6}$ làm bài toán xấu điều kiện hơn khoảng 15 lần theo $\kappa$, 235 lần theo $\kappa^2$: dữ liệu ở nửa đầu vẫn ghim đa thức bậc ba qua nửa sau nhưng chỉ yếu. Hãy giải qua QR của $DA$ (đó là ý nghĩa của "bình phương tối thiểu có trọng số như bài toán chuẩn" trong bài tập), không qua $A^\top WA$, thứ có $\kappa^2\epsilon_{\text{mach}}\approx3{,}6\cdot10^{-10}$ và hoàn toàn tránh được.
15. (a) Gram: $mn^2$ (tích đối xứng) $+\tfrac13n^3$ (Cholesky) $+O(mn+n^2)$; Householder QR: $2mn^2-\tfrac23n^3$. (b) $(10^4,10)$: QR $1{,}9993\cdot10^{6}$, Gram $1{,}0003\cdot10^{6}$, tỉ lệ $2{,}00$. $(600,500)$: QR $2{,}17\cdot10^{8}$, Gram $1{,}92\cdot10^{8}$, tỉ lệ $1{,}13$. (c) Tính được (float64, numpy; QR bằng `numpy.linalg.qr`, Gram bằng `solve(AᵀA, Aᵀb)`):

   | bậc | $\kappa(A)$ | sai số QR | sai số Gram | $\kappa^2\epsilon$ |
   |---|---|---|---|---|
   | 5 | $3{,}55\cdot10^{3}$ | $1{,}7\cdot10^{-13}$ | $1{,}1\cdot10^{-9}$ | $1{,}4\cdot10^{-9}$ |
   | 7 | $1{,}11\cdot10^{5}$ | $9{,}8\cdot10^{-12}$ | $9{,}9\cdot10^{-7}$ | $1{,}4\cdot10^{-6}$ |
   | 9 | $3{,}56\cdot10^{6}$ | $3{,}7\cdot10^{-11}$ | $8{,}2\cdot10^{-4}$ | $1{,}4\cdot10^{-3}$ |

   Sai số Gram bám theo $\kappa^2\epsilon_{\text{mach}}$ (trong hệ số 1,7), sai số QR bám theo $\kappa\epsilon_{\text{mach}}$ ($3{,}9\cdot10^{-13}$, $1{,}2\cdot10^{-11}$, $3{,}9\cdot10^{-10}$ cho ba bậc, đều là chặn trên mà giá trị đo nằm dưới). (d) Dùng QR (hoặc SVD) làm mặc định; chỉ dùng đường Gram/Cholesky khi $\kappa(A)^2\epsilon_{\text{mach}}$ thấp hơn hẳn độ chính xác cần (tối đa $\kappa\approx10^{3}$ cho sáu chữ số), khi $m\gg n$ và tốc độ quan trọng, hoặc khi $G$ có sẵn rẻ; luôn kiểm tra $\kappa$ (từ SVD hoặc ước lượng điều kiện) và giữ QR dự phòng khi Cholesky báo pivot không dương.

## Đọc thêm

- [Eigen: Getting started](https://eigen.tuxfamily.org/dox/GettingStarted.html) - cài đặt, ma trận, vector và chương trình đầu tiên.
- [Eigen: Linear algebra and decompositions](https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html) - giải hệ, bình phương tối thiểu, và bảng so sánh các phép phân rã.
- [MIT 18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/) - phép chiếu, bình phương tối thiểu, và SVD, với bài giảng và bài tập.
- [Boyd và Vandenberghe: Introduction to Applied Linear Algebra (VMLS)](https://web.stanford.edu/~boyd/vmls/vmls.pdf) - PDF miễn phí; §12.2 và §12.3 (bình phương tối thiểu và nghiệm của nó), các Bài tập 12.4, 12.8, 12.13 và 12.16 là cơ sở của phần lý thuyết và các thử thách được thêm.
- [Eigen: Catalogue of dense decompositions](https://eigen.tuxfamily.org/dox/group__TopicLinearAlgebraDecompositions.html) - tốc độ, độ chính xác và tính chất làm lộ hạng của từng phân rã.

**Thực hành thêm:** [các bài tập MIT 18.06](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/assignments/) (các bộ bài về phép chiếu và bình phương tối thiểu), các trang Eigen [Linear algebra and decompositions](https://eigen.tuxfamily.org/dox/group__TutorialLinearAlgebra.html), [Solving linear least squares systems](https://eigen.tuxfamily.org/dox/group__LeastSquares.html), [Aliasing](https://eigen.tuxfamily.org/dox/group__TopicAliasing.html) và [Lazy evaluation and `auto`](https://eigen.tuxfamily.org/dox/TopicLazyEvaluation.html), và tài liệu NumPy cho [`np.linalg.lstsq`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) và [Chebyshev polynomials](https://numpy.org/doc/stable/reference/routines.polynomials.chebyshev.html) (làm lại phép quét bậc trong một cơ sở tốt hơn).
