---
{"title": "Capstone ước lượng trạng thái và định vị: hiệu chuẩn, EKF và tính nhất quán", "summary": "Định vị CoreBot Tidy: hiệu chuẩn camera mô phỏng, phát hiện marker trên tường bằng PnP, hợp nhất odometry bánh, gyro và phát hiện landmark trong một EKF với cập nhật dạng Joseph và gating, rồi kiểm toán bộ lọc bằng NEES và NIS trên năm quỹ đạo có seed.", "objectives": ["Hiệu chuẩn một camera mô phỏng từ các ảnh bàn cờ và đánh giá kết quả bằng RMS sai số chiếu lại và sai số tiêu cự.", "Biến các phát hiện marker thành phép đo khoảng cách-góc phương vị với ngoại tham số đã biết và các góc được wrap.", "Cài đặt một EKF trên odometry, gyro và landmark với cập nhật dạng Joseph và cổng Mahalanobis.", "Kiểm toán một bộ lọc bằng NEES và NIS, và chẩn đoán quá tự tin hay thiếu tự tin từ các con số.", "Giải thích tính quan sát được khi không có landmark trong tầm nhìn và giữ seed hiệu chỉnh tách khỏi seed kiểm thử."]}
---

## Vì sao điều này quan trọng

Sau CAP02, đế báo số đếm bánh và odometry của bạn bị trôi: sai tỉ lệ 1.5 % là 15 cm trên 10 m, sai hướng 2 % làm cong mọi đường dài. Điều hướng (CAP04) cần biết robot ở đâu với sai số vài centimet, và thao tác (CAP05) cần biết camera ở đâu. Milestone này làm cho robot **tự định vị**: bạn hiệu chuẩn camera mô phỏng, phát hiện các marker trên tường, hợp nhất odometry bánh, gyro và các phát hiện marker trong một Extended Kalman Filter, và quan trọng nhất, bạn **kiểm tra xem bộ lọc có trung thực không**. Một bộ lọc báo bất định 2 cm trong khi sai 15 cm còn tệ hơn không có bộ lọc, vì mọi module sau đều tin ma trận hiệp phương sai của nó.

Sản phẩm không phải là "một EKF"; mà là một EKF cộng với bằng chứng: phần dư hiệu chuẩn, đồ thị sai số theo thời gian với dải 2-sigma, thống kê nhất quán NEES/NIS, một bài kiểm thử outlier và một thảo luận về điều xảy ra khi không có landmark nào trong tầm nhìn. Cách tiếp cận và các con số theo thông lệ trong *Probabilistic Robotics* và trong gói `robot_localization`; bạn tự cài bộ lọc trước và có thể so sánh với thư viện sau.

## Trực giác

![Kiến trúc CoreBot Tidy: cảm biến và simulator, đế firmware-in-the-loop, ước lượng, lập bản đồ và lập kế hoạch, nhận thức, thao tác, lớp tác vụ và bộ giám sát an toàn có thể dừng mọi đường tới cơ cấu chấp hành](/lesson-figures/CAP-architecture.svg)

*Toàn bộ hệ thống. Milestone này là dải ước lượng màu xanh: odometry từ CAP02 cộng gyro cộng các phát hiện landmark đi vào, một tư thế kèm hiệp phương sai (`Pose2DCov`) đi ra.*

Một EKF là **một người ghi sổ có hai nguồn thu**. Giữa các lần thấy landmark, nó cộng dồn những chuyển động nhỏ có nhiễu (bánh và gyro) và ghi lại, trung thực, bất định của nó đã tăng bao nhiêu. Khi thấy một marker, nó so sánh điều nó thấy với điều nó kỳ vọng thấy, và hiệu chỉnh tư thế một phần tỉ lệ với mức nó tin phép đo so với bất định của chính nó (độ lợi Kalman). Nếu người ghi sổ quá tự tin (ghi bất định quá nhỏ) nó sẽ phớt lờ các phép đo tốt; nếu thiếu tự tin nó sẽ rung giật. Các bài kiểm tra NEES và NIS chính là cuộc kiểm toán.

![Đường ống CAP03: odometry bánh và gyro cấp cho bước dự đoán của EKF, các góc marker đi qua hiệu chuẩn camera và PnP thành phép đo khoảng cách-góc phương vị, bước cập nhật EKF với cổng Mahalanobis hiệu chỉnh tư thế, và NEES cùng NIS kiểm toán hiệp phương sai](/lesson-figures/CAP03.svg)

Milestone này dùng lại: [CAP02](/lessons/CAP02) (odometry đã hiệu chuẩn và dữ liệu `WheelState`/`OdomSample`), [C08](/lessons/C08) (hợp nhất cảm biến, cách nhìn bù và Kalman), [C12](/lessons/C12) (ước lượng trạng thái phi tuyến: EKF, Jacobian, tính nhất quán), [V04](/lessons/V04) (mô hình camera và hiệu chuẩn) và [V11](/lessons/V11) (hình học nhiều góc nhìn, PnP, ma trận cốt yếu). Kiến thức Kalman cơ bản ở [C07](/lessons/C07).

## Lý thuyết và suy dẫn

Đây là **ghi chú tích hợp (integration notes)**: các công thức và giao diện quan trọng, mỗi cái kèm chủ đề đã suy dẫn nó.

### 1. Trạng thái, dự đoán và các hệ quy chiếu ([C12](/lessons/C12), [C08](/lessons/C08))

Trạng thái $\mathbf{x}=[x,\,y,\,\theta,\,b_g]^\top$ trong hệ `map` (mét, radian), độ lệch gyro (bias) $b_g$ tính bằng rad/s. Đầu vào từ đế: tốc độ tiến $v$ (từ odometry bánh) và tốc độ gyro $\omega_g$. Với bước $\Delta t$:
$$x_{k+1}=x_k+v\cos\theta_k\,\Delta t,\quad y_{k+1}=y_k+v\sin\theta_k\,\Delta t,\quad \theta_{k+1}=\operatorname{wrap}\bigl(\theta_k+(\omega_g-b_g)\Delta t\bigr),\quad b_{g,k+1}=b_{g,k}.$$
Hiệp phương sai: $P^-=FPF^\top+GQG^\top$, với $F_{13}=-v\sin\theta\,\Delta t$, $F_{23}=v\cos\theta\,\Delta t$, $F_{34}=-\Delta t$. Dùng gyro cho hướng (và bánh chỉ cho tốc độ) là có chủ ý: tốc độ quay suy từ bánh phụ thuộc vào track width, hằng số kém được biết nhất của đế.

### 2. Phép đo landmark ([C12](/lessons/C12), [V11](/lessons/V11))

Một marker ở vị trí map đã biết $(m_x,m_y)$ được phát hiện bằng PnP và biểu diễn dưới dạng khoảng cách và góc phương vị trong `base_link`:
$$h(\mathbf{x})=\begin{bmatrix}\sqrt{\Delta_x^2+\Delta_y^2}\\ \operatorname{wrap}\bigl(\operatorname{atan2}(\Delta_y,\Delta_x)-\theta\bigr)\end{bmatrix},\qquad \Delta_x=m_x-x,\ \Delta_y=m_y-y.$$
Với $q=\Delta_x^2+\Delta_y^2$, $r=\sqrt q$ Jacobian là
$$H=\begin{bmatrix}-\Delta_x/r&-\Delta_y/r&0&0\\ \Delta_y/q&-\Delta_x/q&-1&0\end{bmatrix}.$$
**Innovation của góc phương vị phải được wrap**, nếu không một marker gần $\pm\pi$ sẽ gây bước nhảy $2\pi$.

### 3. Cập nhật, dạng Joseph và cổng ([C07](/lessons/C07), [C12](/lessons/C12))

$$\nu=z-h(\hat{\mathbf x}),\quad S=HPH^\top+R,\quad K=PH^\top S^{-1},\quad \hat{\mathbf x}\leftarrow\hat{\mathbf x}+K\nu,\quad P\leftarrow(I-KH)P(I-KH)^\top+KRK^\top.$$
Dạng Joseph là tổng của hai số hạng nửa xác định dương, nên $P$ giữ được tính đối xứng xác định dương ngay cả khi có sai số làm tròn hoặc $K$ không tối ưu; dạng đơn giản $(I-KH)P$ không đảm bảo điều đó. **Cổng (gate)** trước khi cập nhật: chỉ chấp nhận nếu $d^2=\nu^\top S^{-1}\nu\le\chi^2_{2,0.99}=9.21$. Một marker sai ID cho $d^2$ lớn và bị từ chối; cái giá là 1 % các phát hiện tốt cũng bị từ chối.

### 4. Tính nhất quán: NEES và NIS ([C12](/lessons/C12), [RS03](/lessons/RS03))

Khi có sự thật nền (ground truth) trong mô phỏng, **bình phương sai số ước lượng chuẩn hóa (NEES)** của khối tư thế là
$$\text{NEES}_k=(\mathbf{x}_k-\hat{\mathbf x}_k)^\top P_k^{-1}(\mathbf{x}_k-\hat{\mathbf x}_k)\ \sim\ \chi^2_3\quad(\text{3 bậc tự do, cho }x,y,\theta).$$
Với một bộ lọc nhất quán, giá trị trung bình khoảng 3 và khoảng 95 % mẫu rơi trong khoảng hai phía 95 % $[0.216,\,9.348]$ ($\texttt{evalkit.chi2\_ppf}$ dùng xấp xỉ Wilson-Hilferty: 0.181 và 9.324). **Bình phương innovation chuẩn hóa (NIS)** $\text{NIS}=\nu^\top S^{-1}\nu\sim\chi^2_2$ không cần sự thật nền; trung bình của nó khoảng 2. Cách diễn giải:

| Quan sát | Ý nghĩa | Nguyên nhân thường gặp |
|---|---|---|
| NEES trung bình cao hơn nhiều so với 3 | quá tự tin: $P$ quá nhỏ | $Q$ quá nhỏ, thiếu trạng thái bias, lỗi hệ quy chiếu |
| NEES trung bình thấp hơn nhiều so với 3 | thiếu tự tin: $P$ quá lớn | $Q$ hoặc $R$ bị thổi phồng "cho an toàn" |
| NIS trung bình trên 2, NEES ổn | $R$ quá nhỏ hoặc có outlier | nhiễu của bộ phát hiện bị đánh giá thấp |
| NIS trung bình dưới 2 | $R$ quá lớn | $R$ bị thổi phồng để che một lỗi |

`evalkit.nees_consistency(errors, covs, dof)` trả về `(fraction_inside, mean_nees)`. Các mẫu liên tiếp tương quan mạnh, nên hãy lấy mẫu thưa (ở đây 10 Hz) và coi con số 95 % chỉ là xấp xỉ; vì thế bài kiểm thử chấp nhận từ 85 % đến 99.5 %.

### 5. Mô hình camera và hiệu chuẩn ([V04](/lessons/V04))

Pinhole: $u=f_x X/Z+c_x$, $v=f_y Y/Z+c_y$. Với camera mô phỏng có góc nhìn dọc $\text{fovy}$ và chiều cao ảnh $H$ pixel, tiêu cự lý tưởng là $f=\dfrac{H/2}{\tan(\text{fovy}/2)}$ và $(c_x,c_y)$ là tâm ảnh (sai khác quy ước nửa pixel; bài kiểm thử chấp nhận 3 px). Hiệu chuẩn bàn cờ (Zhang) cần khoảng 20 góc nhìn trở lên với độ nghiêng khác nhau; con số chất lượng là RMS sai số chiếu lại tính bằng pixel, và một con số tốt trên ảnh render sạch là dưới 0.5 px. Nhiễu pixel biến thành sai số mét theo $\sigma_Z\approx Z\,\sigma_w/w$ với $w=f\,s/Z$ là bề rộng pixel của marker ($s$ là cạnh của nó): sai số khoảng cách tăng theo $Z^2$.

### 6. Điều bộ lọc không làm được ([C08](/lessons/C08))

Khi không có landmark nào trong tầm nhìn, tư thế chỉ được dự đoán: sai số vị trí và hướng tăng lên và không có gì chặn chúng (hệ không quan sát được tư thế tuyệt đối). Hiệp phương sai cũng phải tăng; nếu không, bộ lọc đang nói dối. Hãy lên kế hoạch độ phủ landmark (marker trên tường thấy được từ phần lớn căn phòng) và ghi log khoảng dài nhất không có cập nhật được chấp nhận; nó giải thích hầu hết các đỉnh sai số.

## Ví dụ có lời giải

Mọi con số là **minh họa (illustrative)**, từ một mô phỏng độc lập nhỏ (xe một bánh lái vi sai trên quỹ đạo hình số tám 60 s, odometry sai tỉ lệ 1.5 % và sai tỉ lệ tốc độ quay 2 %, bias gyro 0.01 rad/s, tám marker trên tường), không phải từ một lần chạy repository của bạn.

**Một lần cập nhật bằng tay.** Prior $\hat{\mathbf x}=(1.0,\,0.5,\,0.3,\,0)$, $P=\operatorname{diag}(0.0025,\,0.0025,\,0.0009,\,0.0004)$ (độ lệch chuẩn 5 cm, 5 cm, 1.7 độ, 0.02 rad/s). Marker ở $(1.9,\,1.0)$: $\Delta_x=0.9$, $\Delta_y=0.5$, $q=1.06$, $r=1.0296$ m, góc phương vị dự đoán $\operatorname{atan2}(0.5,0.9)-0.3=0.2071$ rad. Các hàng Jacobian: $[-0.874,\,-0.486,\,0,\,0]$ và $[0.472,\,-0.849,\,-1,\,0]$. Với $R=\operatorname{diag}(0.03^2,0.012^2)$: $S\approx\operatorname{diag}(0.0034,\,0.0034)$. Phát hiện cho khoảng cách 1.09 m, góc phương vị 0.25 rad: $\nu=(0.0604,\,0.0429)$, $d^2=1.62<9.21$, nên nó được chấp nhận (và 1.62 là một mẫu hợp lý từ $\chi^2_2$, trung bình 2). Hiệu chỉnh là $K\nu=(-0.024,\,-0.048,\,-0.011,\,0)$: marker xa hơn dự đoán, nên robot dịch ra xa nó. Hậu nghiệm $\hat{\mathbf x}=(0.976,\,0.452,\,0.289,\,0)$; độ lệch chuẩn giảm từ (5.0, 5.0 cm, 1.7 độ) xuống (2.6, 2.7 cm, 1.5 độ); phần tử bias không đổi vì prior này không có tương quan với nó.

**Năm quỹ đạo 60 s** (seed 1000 đến 1004), sau khi chỉnh ($q_v=0.08$, $q_w=0.02$, $q_b=2\times10^{-4}$ trong mã của bài này):

| seed | RMSE vị trí (cm) | RMSE hướng (độ) | sai số cuối (cm) | sai số cuối của dead reckoning (cm) | NEES trong 95 % | NEES trung bình | NIS trung bình | bị gate |
|---|---|---|---|---|---|---|---|---|
| 1000 | 4.1 | 0.73 | 1.0 | 30.6 | 0.903 | 4.74 | 1.83 | 8 |
| 1001 | 3.1 | 0.29 | 0.2 | 24.0 | 0.958 | 3.62 | 1.85 | 7 |
| 1002 | 2.7 | 0.32 | 0.4 | 27.8 | 0.958 | 3.76 | 1.86 | 6 |
| 1003 | 4.7 | 1.07 | 0.2 | 29.0 | 0.980 | 4.15 | 1.86 | 8 |
| 1004 | 2.9 | 0.48 | 0.2 | 21.9 | 0.963 | 3.17 | 1.78 | 8 |

Cả năm đều qua các giới hạn độ chính xác (5 cm, 2 độ, sai số cuối nhỏ hơn dead reckoning ít nhất 3 lần) và dải nhất quán. Lần chỉnh đầu tiên ($q_v=0.05$, $q_w=0.01$) có **RMSE tương tự nhưng NEES trung bình 5 đến 10 và chỉ 43 % đến 87 % mẫu nằm trong khoảng**: chính xác nhưng quá tự tin, đúng điều cuộc kiểm toán sinh ra để bắt. Trong 771 lần thử phát hiện ở seed 1000, 8 lần bị gate (1 % của 771 là 7.7: đúng kỳ vọng với một cổng ở mức 99 %).

**Outlier.** Thay 10 % phát hiện bằng các phát hiện sai ID, sai tư thế (seed 1000): 61 bị gate, RMSE vị trí 5.4 cm so với 4.1 cm sạch (+31 %, giới hạn +50 %). Khoảng 77 outlier được chèn; khoảng 8 trong 61 phát hiện bị gate là phát hiện tốt, nên khoảng 53 outlier bị bắt và khoảng 24 cái trông đủ hợp lý để lọt qua cổng, và đó là lý do sai số tăng.

**Hiệu chuẩn** (minh họa): 24 góc nhìn, RMS 0.31 px, $f_x=581.2$ so với giá trị thật 579.4 (0.3 %), điểm chính lệch 0.6 px và 0.9 px. Với camera 640 nhân 480 và fovy 45 độ: $f=240/\tan22.5^\circ=579.4$ px.

## Bài tập

1. **(Easy)** Một camera mô phỏng 640 nhân 480 pixel với góc nhìn dọc 45 độ. Tính $f$ theo pixel, góc nhìn ngang và điểm chính lý tưởng. *(Quan hệ pinhole từ bài V04 và bài viết hiệu chuẩn của LearnOpenCV.)*
2. **(Easy)** Cho hai cận hai phía 95 % của NEES 3 bậc tự do và nói NEES trung bình 9.1 trong cả một lần chạy nghĩa là gì cho một bộ lọc tư thế 3 bậc tự do. Hai núm nào bạn kiểm tra trước?
3. **(Easy)** Một góc phương vị được dự đoán là $-3.10$ rad và đo được $+3.10$ rad. Tính innovation khi không wrap và khi có wrap.
4. **(Medium)** Một marker có cạnh 0.15 m. Ở 2 m với $f=579$ px, bề rộng pixel của nó là bao nhiêu, và nhiễu bề rộng 0.7 px gây sai số khoảng cách bao nhiêu? Điều gì xảy ra ở 1 m và 4 m? Sai số ngang do sai số góc 0.5 px ở 2 m là bao nhiêu?
5. **(Medium)** Với robot ở $(1.0,\,0.5)$ hướng 0.3 rad và một landmark ở $(1.9,\,1.0)$, tính hai hàng của $H$ cho $x$, $y$, $\theta$ và $b_g$.
6. **(Medium)** Giải thích vì sao dùng dạng Joseph và bài kiểm thử sức khỏe số học kiểm tra gì. Khi nào $(I-KH)P$ hỏng trong thực tế?
7. **(Medium)** Cổng là $\chi^2_{2,0.99}=9.21$. Trong khoảng 770 phát hiện tốt, bạn kỳ vọng bao nhiêu bị gate? Bạn thấy 61 khi chèn 10 % outlier: có hợp lý không? Nếu thấy 61 mà không có outlier thì sao?
8. **(Medium)** *Tính quan sát được.* Không marker nào thấy được trong 20 s trong khi robot chạy 0.3 m/s. Với sai số bias gyro còn lại 0.002 rad/s, ước lượng sai số hướng ở cuối và sai số vị trí kéo theo. Hiệp phương sai nên làm gì trong lúc này?
9. **(Hard)** *Chẩn đoán.* Lần chạy A: NEES trung bình 9.0, NIS trung bình 2.0. Lần chạy B: NEES trung bình 1.1, NIS trung bình 0.4. Lần chạy C: NEES trung bình 3.1, NIS trung bình 3.4. Nêu vấn đề có khả năng nhất ở mỗi lần và cách sửa đầu tiên.
10. **(Hard)** *Vệ sinh kiểm thử.* Bạn chỉnh $Q$ và $R$ trên chính năm quỹ đạo kiểm thử để qua các ngưỡng. Vì sao đó là vấn đề, sửa quy trình thế nào, và bạn báo cáo gì?
11. **(Hard, mini-project)** Cài EKF và chạy bốn biến thể trên năm quỹ đạo: bộ lọc đầy đủ; không gyro (dùng tốc độ quay từ bánh); không landmark; 10 % outlier có và không có cổng. Báo cáo RMSE, tỉ lệ NEES trong khoảng và khoảng dài nhất không có cập nhật; nêu các giả định, baseline (bộ lọc đầy đủ), một ca biên (marker ở góc phương vị $\pm\pi$ phía sau robot) và quan sát nào sẽ bác bỏ bộ lọc của bạn.

## Cài đặt tham khảo

Bộ khung dưới đây là `corebot/estimation/ekf.py`. Hợp đồng (trạng thái, đơn vị, cái gì được wrap, cái gì được ghi log) nằm trong docstring; phần toán ở các mục Lý thuyết 1 đến 3. Hãy điền vào ở Nhiệm vụ 3.

```python
"""corebot/estimation/ekf.py (skeleton): planar EKF fusing odometry, gyro and landmark detections.

State  x = [x, y, theta, b_g]   x, y in metres (frame `map`), theta in rad wrapped to [-pi, pi),
                                 b_g = gyro bias in rad/s.
Inputs predict(): v (m/s) from wheel odometry, gyro_z (rad/s), dt (s). The heading rate is gyro_z - b_g.
Inputs update_landmark(): range (m) and bearing (rad) of a marker with a KNOWN map position,
                          measured in the base_link frame (bearing positive counter-clockwise from +x).
Everything is SI. All timestamps come from one clock; the caller guarantees dt > 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def wrap(angle: float) -> float:
    """Wrap an angle to [-pi, pi). Apply it to EVERY angle difference, including the bearing innovation."""
    raise NotImplementedError


@dataclass
class EkfConfig:
    q_v: float = 0.08          # m/s, std of the speed noise (document the units you chose)
    q_w: float = 0.02          # rad/s, std of the gyro noise (turns into a heading noise via dt)
    q_b: float = 2e-4          # rad/s per sqrt(s), random walk of the gyro bias
    r_range: float = 0.03      # m, landmark range noise
    r_bearing: float = 0.012   # rad, landmark bearing noise
    gate_chi2: float = 9.21    # 99 % quantile of chi-square with 2 dof
    p0_diag: tuple = (1e-4, 1e-4, 1e-4, 4e-4)


@dataclass
class Ekf:
    x: np.ndarray                                   # shape (4,)
    P: np.ndarray                                   # shape (4, 4), symmetric positive definite
    cfg: EkfConfig = field(default_factory=EkfConfig)
    nis: list = field(default_factory=list)         # one NIS value per ACCEPTED update (2 dof)
    gated: int = 0                                  # number of rejected detections

    def predict(self, v: float, gyro_z: float, dt: float) -> None:
        """Propagate the mean with the unicycle model and the covariance with F P F^T + G Q G^T.
        Re-symmetrise P at the end."""
        raise NotImplementedError

    def update_landmark(self, rng: float, bearing: float, landmark_xy: tuple) -> bool:
        """Range-bearing update with a Mahalanobis gate. Returns True if the detection was used.
        Steps: predicted measurement h(x); Jacobian H (2x4); innovation nu with wrapped bearing;
        S = H P H^T + R; d2 = nu^T S^-1 nu; reject if d2 > gate_chi2 (increment `gated`);
        K = P H^T S^-1; x += K nu (wrap theta); Joseph form P = (I-KH) P (I-KH)^T + K R K^T; log d2 in `nis`."""
        raise NotImplementedError
```

## Thực hành độc lập

### Mục tiêu

Định vị CoreBot Tidy trong phòng lab mô phỏng: hiệu chuẩn camera từ các ảnh bàn cờ, phát hiện marker trên tường và tính phép đo khoảng cách-góc phương vị, xây một EKF trên odometry, gyro và landmark, chạy năm quỹ đạo 60 s có seed và có sự thật nền, và chứng minh bằng NEES/NIS rằng bộ lọc vừa chính xác vừa trung thực. Đây là milestone CAP03; nó dùng odometry đã hiệu chuẩn của CAP02.

### Thiết lập

Làm việc trong `~/corebot-capstone`. Bạn cần NumPy và OpenCV (`opencv-python-headless`; ghim phiên bản bạn dùng trong `pyproject.toml`). Render cần MuJoCo với EGL hoặc OSMesa (xem CAP01 về `MUJOCO_GL`); OSMesa chậm (khoảng 5 đến 10 khung hình mỗi giây ở 320 nhân 240), nên hãy render 24 góc nhìn hiệu chuẩn và 100 khung marker một lần rồi lưu cache. Lệnh:

```bash
cd ~/corebot-capstone && source .venv/bin/activate
pip install "numpy>=1.26" "opencv-python-headless>=4.9" pytest   # pin the versions you actually use in pyproject.toml
mkdir -p runs/cap03 configs
python -m corebot.estimation.render_calib --views 24 --seed 1000 --out runs/cap03/calib_views   # your script, Task 1
python -m corebot.estimation.calibration --views runs/cap03/calib_views --out configs/camera.yaml
python -m bench.run_cap03 --seeds 1000 1001 1002 1003 1004 --out runs/cap03                    # your script, Task 6
pytest -q tests/acceptance/test_cap03.py
```

Lược đồ artefact mà các bài kiểm thử đọc là cố định:

```text
runs/cap03/traj_<i>.npz        (one per seeded 60 s trajectory, N samples at 100 Hz)
  t      (N,)       s            time
  truth  (N, 3)     m, m, rad    ground truth x, y, theta  (ONLY used by tests and plots, never by the filter)
  est    (N, 3)     m, m, rad    EKF estimate
  dr     (N, 3)     m, m, rad    dead reckoning from wheel odometry only
  P      (N, 4, 4)               EKF covariance of [x, y, theta, b_g]
  nis    (M,)                    NIS (2 dof) of every ACCEPTED landmark update
  gated  ()         count        detections rejected by the gate
  upd_median_ms ()  ms           median wall time of one update_landmark call
runs/cap03/outliers_0.npz      same keys, same seed as traj_0, with 10 % wrong-ID/wrong-pose detections
runs/cap03/calibration.json    n_images, rms_px, fx, fy, cx, cy, and "truth": {fx, fy, cx, cy} from the sim camera
runs/cap03/landmark_pose.npz   pos_err_m (K,), yaw_err_deg (K,), dist_m (K,) for >= 100 detections
```

### Nhiệm vụ

1. **Hiệu chuẩn** (`estimation/calibration.py`, `configs/camera.yaml`): render ít nhất 20 góc nhìn bàn cờ với tư thế đa dạng, phát hiện góc, hiệu chuẩn, và báo cáo RMS, tiêu cự và điểm chính so với sự thật của simulator (từ `fovy`).
2. **Landmark** (`estimation/landmarks.py`): phát hiện các marker trên tường, chạy PnP, đổi sang khoảng cách và góc phương vị trong `base_link` bằng ngoại tham số camera; 100 khung ở khoảng cách tới 2 m, sai số vị trí và hướng trung vị ghi vào `landmark_pose.npz`.
3. **EKF** (`estimation/ekf.py`): trạng thái $[x,y,\theta,b_g]$, dự đoán, cập nhật khoảng cách-góc phương vị với innovation đã wrap, cổng Mahalanobis, dạng Joseph.
4. **Mô hình nhiễu từ dữ liệu**: ước lượng nhiễu odometry và gyro từ một lần chạy đứng yên và một lần chạy vận tốc không đổi, và nhiễu bộ phát hiện từ Nhiệm vụ 2; viết một suy dẫn ngắn trong `docs/noise_models.md` (liệt kê mọi quy ước đơn vị và hệ quy chiếu).
5. **Quỹ đạo**: năm lần chạy 60 s có seed (`seeds 1000..1004`) ghi sự thật nền, ước lượng, dead reckoning, $P$, NIS và số phát hiện bị gate. Vẽ sai số theo thời gian với dải 2-sigma.
6. **Lần chạy outlier**: cùng seed với quỹ đạo 0 với 10 % phát hiện sai ID hoặc sai tư thế; lưu `outliers_0.npz`.
7. **Báo cáo tính trung thực** (`docs/consistency.md`): bảng NEES/NIS, một đoạn về tính quan sát được (điều gì xảy ra khi không có landmark trong tầm nhìn), một đoạn về cái bạn đã chỉnh và trên seed nào.
8. **Tùy chọn**: notebook visual odometry (ma trận cốt yếu, tỉ lệ từ odometry bánh); xem thử thách mở rộng.

### Code khởi đầu

Chữ ký cho phía nhận thức (bộ khung EKF nằm ở phần Cài đặt tham khảo):

```python
"""estimation/calibration.py and estimation/landmarks.py (starter signatures)."""
from __future__ import annotations

import numpy as np


def calibrate_camera(images: list, board: tuple = (9, 6), square_m: float = 0.03) -> dict:
    """Checkerboard calibration (Zhang). Return {"fx","fy","cx","cy","dist","rms_px","n_images"}.
    Use at least 20 views with varied tilt and distance; reject views where corners are not found.
    Hint: keep the corner detection and the optimisation separate so each can be tested alone."""
    raise NotImplementedError


def marker_pose_camera(corners_px: np.ndarray, K: np.ndarray, side_m: float) -> np.ndarray:
    """PnP for one square marker: 4x2 pixel corners -> 4x4 transform T_cam_marker."""
    raise NotImplementedError


def to_range_bearing(T_base_cam: np.ndarray, T_cam_marker: np.ndarray) -> tuple:
    """Marker position in the base frame -> (range_m, bearing_rad). T_base_cam comes from configs/camera.yaml."""
    raise NotImplementedError
```

### Kiểm thử

`tests/acceptance/test_cap03.py` ở dưới. Các kiểm tra gate là `test_camera_calibration`, `test_ekf_accuracy` và `test_consistency`. Các bài kiểm thử dùng `evalkit.nees_consistency` từ CAP01. **Các ngưỡng là giá trị khởi đầu tạm thời (provisional); hãy siết chặt chúng khi bạn đã có lần chạy tham chiếu của riêng mình.** Lý do một dòng: ít nhất 20 góc nhìn và RMS dưới 0.5 px (mức sàn thường dùng để hiệu chuẩn Zhang ổn định trên ảnh render sạch); sai số tiêu cự dưới 2 % và điểm chính dưới 3 px (cái mà độ chính xác khoảng cách PnP cần); sai số trung vị của landmark dưới 5 cm và 3 độ ở tới 2 m (xấp xỉ ô bản đồ 5 cm của CAP04); RMSE vị trí dưới 5 cm và RMSE hướng dưới 2 độ (sai số ngang 7 cm sau 2 m ở 2 độ); sai số cuối tốt hơn dead reckoning 3 lần (nếu không landmark chẳng thêm gì); tỉ lệ NEES trong khoảng 85 % đến 99.5 % (mẫu tương quan khiến đúng 95 % khó xảy ra, và 100 % nghĩa là thiếu tự tin); NIS trung bình trong 0.5 đến 1.5 lần giá trị kỳ vọng; 10 % outlier làm RMSE tăng tối đa 50 %; $P$ đối xứng tới $10^{-9}$ và xác định dương (vệ sinh số học); cập nhật dưới 2 ms (một vòng 100 Hz không được bị bộ lọc chi phối).

```python
"""tests/acceptance/test_cap03.py : reads runs/cap03/.  GATE = counts toward the graduation gate.
Thresholds are provisional starting values; tighten them once your own reference run exists."""
import json, pathlib
import numpy as np
import pytest
from corebot.evalkit import nees_consistency

RUNS = pathlib.Path("runs/cap03")
TRAJ = sorted(RUNS.glob("traj_*.npz"))

def _wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi

def _err(z):                                   # estimate minus truth, heading wrapped
    e = z["est"] - z["truth"]
    e[:, 2] = _wrap(e[:, 2])
    return e

def test_five_trajectories_exist():
    assert len(TRAJ) >= 5

def test_camera_calibration():                  # GATE
    c = json.loads((RUNS / "calibration.json").read_text())
    assert c["n_images"] >= 20                  # Zhang's method needs varied views; 20 is the usual floor
    assert c["rms_px"] < 0.5                    # sub-pixel corners are achievable on clean renders
    assert abs(c["fx"] - c["truth"]["fx"]) / c["truth"]["fx"] < 0.02
    assert abs(c["cx"] - c["truth"]["cx"]) < 3.0 and abs(c["cy"] - c["truth"]["cy"]) < 3.0

def test_landmark_pose():
    z = np.load(RUNS / "landmark_pose.npz")
    near = z["dist_m"] <= 2.0
    assert len(z["pos_err_m"]) >= 100
    assert np.median(z["pos_err_m"][near]) < 0.05
    assert np.median(z["yaw_err_deg"][near]) < 3.0

@pytest.mark.parametrize("path", TRAJ)
def test_ekf_accuracy(path):                    # GATE
    z = np.load(path); e = _err(z)
    assert np.sqrt(np.mean(e[:, 0] ** 2 + e[:, 1] ** 2)) < 0.05          # 5 cm: one cell of the 5 cm map in CAP04
    assert np.degrees(np.sqrt(np.mean(e[:, 2] ** 2))) < 2.0              # 2 deg: 7 cm sideways error after 2 m
    dr = z["dr"] - z["truth"]
    assert np.hypot(*e[-1, :2]) * 3 <= np.hypot(*dr[-1, :2])             # fusion at least 3x better than dead reckoning

@pytest.mark.parametrize("path", TRAJ)
def test_consistency(path):                     # GATE
    z = np.load(path); e = _err(z)
    idx = range(0, len(e), 10)                  # 10 Hz subsample: neighbouring samples are strongly correlated
    inside, mean_nees = nees_consistency([e[i].tolist() for i in idx],
                                         [z["P"][i, :3, :3].tolist() for i in idx], dof=3)
    assert 0.85 <= inside <= 0.995              # a 95 % interval should hold ~95 %, not 100 % and not 60 %
    assert mean_nees < 3 * 2.0                  # mean NEES near dof = 3; 2x slack is the "overconfident" alarm
    assert 0.5 * 2 <= float(np.mean(z["nis"])) <= 1.5 * 2                # NIS of a 2-dof range-bearing update

def test_gating_with_outliers():
    clean = _err(np.load(RUNS / "traj_0.npz")); bad_z = np.load(RUNS / "outliers_0.npz"); bad = _err(bad_z)
    rm = lambda e: np.sqrt(np.mean(e[:, 0] ** 2 + e[:, 1] ** 2))
    assert rm(bad) < 1.5 * rm(clean)            # 10 % wrong detections may cost at most 50 % RMSE
    assert int(bad_z["gated"]) > 0              # the filter must say it rejected something

@pytest.mark.parametrize("path", TRAJ)
def test_numerical_health(path):
    z = np.load(path); P = z["P"]
    assert np.max(np.abs(P - np.swapaxes(P, 1, 2))) < 1e-9
    assert np.linalg.eigvalsh(P).min() > 0.0
    assert float(z["upd_median_ms"]) < 2.0      # leaves room for a 100 Hz loop on a laptop
```

### Kết quả mong đợi

Khi có đủ artefact, `pytest -q tests/acceptance/test_cap03.py` in ra (thời gian minh họa):

```text
...................                                                      [100%]
19 passed in 6.8s
```

Một `runs/cap03/metrics.json` mẫu mà script báo cáo của bạn có thể ghi (giá trị minh họa, hiển thị hai trong năm quỹ đạo):

```json
{
  "milestone": "CAP03",
  "calibration": {"n_images": 24, "rms_px": 0.31, "fx_err_pct": 0.31, "cx_err_px": 0.6, "cy_err_px": 0.9},
  "landmark_pose": {"median_pos_err_m": 0.018, "median_yaw_err_deg": 1.0, "n_frames": 100},
  "ekf": [
    {"seed": 1000, "pos_rmse_m": 0.041, "head_rmse_deg": 0.73, "final_err_m": 0.010, "dr_final_err_m": 0.306,
     "nees_inside": 0.903, "nees_mean": 4.74, "nis_mean": 1.83, "gated": 8},
    {"seed": 1001, "pos_rmse_m": 0.031, "head_rmse_deg": 0.29, "final_err_m": 0.002, "dr_final_err_m": 0.240,
     "nees_inside": 0.958, "nees_mean": 3.62, "nis_mean": 1.85, "gated": 7}
  ],
  "outliers_10pct": {"pos_rmse_m": 0.054, "rmse_increase_pct": 31, "gated": 61}
}
```

### Thử thách mở rộng

**Mở rộng (điểm thưởng, không phải gate):** visual odometry đơn mắt. Bám các đặc trưng giữa các khung hình, ước lượng ma trận cốt yếu, khôi phục phép quay và hướng tịnh tiến, và đặt tỉ lệ từ odometry bánh; mục tiêu độ trôi hướng dưới 3 độ mỗi 10 m. Cũng thử ước lượng tỉ lệ odometry như trạng thái thứ năm và chứng minh bằng NEES xem bộ lọc có tốt hơn không. Hãy trung thực: báo cáo cả khi nó không giúp ích.

**Ghi chú phần cứng tùy chọn:** nếu bạn đã dựng đế ESP32 của CAP02, hãy ghi log số đếm bánh thật và gyro của một IMU rẻ tiền (xem HW04) rồi chạy EKF của bạn offline không có landmark; so sánh độ trôi dead-reckoning với độ trôi mô phỏng. Không điểm nào phụ thuộc vào nó.

### Thực hành với thư viện

Thay EKF của bạn bằng `robot_localization` (ROS 2 Jazzy), hợp nhất `/odom` và `/imu`, và so sánh sai số của nó trên cùng một bag với của bạn. Rồi kiểm tra hiệu chuẩn của OpenCV với của bạn:

```yaml
# configs/rl_ekf.yaml : the same fusion with robot_localization (ROS 2 Jazzy) instead of your own ekf.py
ekf_filter_node:
  ros__parameters:
    frequency: 50.0
    two_d_mode: true
    publish_tf: true
    map_frame: map
    odom_frame: odom
    base_link_frame: base_link
    world_frame: odom
    odom0: /odom
    odom0_config: [false, false, false,  false, false, false,
                   true,  false, false,  false, false, true,
                   false, false, false]            # forward speed and yaw rate from wheels
    imu0: /imu
    imu0_config: [false, false, false,  false, false, false,
                  false, false, false,  false, false, true,
                  false, false, false]             # yaw rate from the gyro
    imu0_remove_gravitational_acceleration: false
```

```python
# Needs: pip install numpy opencv-python-headless
# OpenCV reference for Task 1: compare its intrinsics and RMS with your own calibration.
import glob

import cv2
import numpy as np

BOARD, SQUARE = (9, 6), 0.03                       # inner corners, square size in metres
objp = np.zeros((BOARD[0] * BOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:BOARD[0], 0:BOARD[1]].T.reshape(-1, 2) * SQUARE
obj_pts, img_pts, size = [], [], None
for path in sorted(glob.glob("runs/cap03/calib_views/*.png")):
    gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    size = gray.shape[::-1]
    ok, corners = cv2.findChessboardCorners(gray, BOARD)
    if ok:
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                   (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3))
        obj_pts.append(objp)
        img_pts.append(corners)
rms, K, dist, _, _ = cv2.calibrateCamera(obj_pts, img_pts, size, None, None)
print("views used:", len(obj_pts), " RMS reprojection error (px):", round(rms, 3))
print("fx, fy, cx, cy =", K[0, 0], K[1, 1], K[0, 2], K[1, 2])
```

## Kiểm chứng

Làm phép tính trước khi viết mã: $f=579.4$ px, các cận $\chi^2$, một lần cập nhật bằng tay như trong ví dụ có lời giải. Kiểm chứng bộ lọc bằng các kiểm tra rẻ và quyết định: hiệp phương sai tăng khi không thấy landmark (in $\operatorname{tr}P$ trong 10 s dead reckoning); đổi dấu góc phương vị cố ý làm NIS bùng nổ; một bài kiểm thử innovation có wrap so với không wrap tại góc $\pm\pi$; chạy bộ lọc với tham số thật và không nhiễu trả về sự thật. Cũng kiểm chứng cách đánh giá: seed hiệu chỉnh phải khác seed kiểm thử, và đồ thị phải có dải 2-sigma.

**Chấm điểm và tốt nghiệp.** CAP03 có giá trị **12 trên 100** điểm: 60 % tự động (tỉ lệ có trọng số của các kiểm tra, gate ở trên) và 40 % rubric của người chấm 0 đến 4: mô hình nhiễu có lý do và được chỉnh từ dữ liệu, mọi quy ước đơn vị và hệ quy chiếu được giải thích, thảo luận trung thực về tính quan sát được, đồ thị rõ ràng. Tốt nghiệp cần mọi kiểm tra gate của mọi milestone, mọi milestone từ 60 trở lên và tổng có trọng số từ 70 trở lên. Một prompt tự xem xét cho LLM (đưa nó mã và artefact, không phải nhận xét của bạn): *"Audit this EKF. Check the heading wrap in every angle difference, the frame and sign of the camera extrinsics, whether R or Q are inflated to hide errors, whether tuning and test data overlap, and whether NEES/NIS support the claimed accuracy. Score 0 to 4 on noise models, conventions, observability and plots with line references."*

## Lỗi thường gặp

- Quên wrap innovation của góc phương vị (hoặc hướng sau cập nhật): các đỉnh nhọn $2\pi$ khi marker ở phía sau robot.
- Ngoại tham số hệ camera so với hệ robot sai dấu hoặc sai trục: bộ lọc hội tụ về một tư thế bị dịch hoặc xoay nhất quán; NIS lớn.
- Timestamp từ các đồng hồ khác nhau (thời gian sim so với thời gian thực): các phát hiện được áp vào sai trạng thái.
- Thổi phồng $R$ hoặc $Q$ để che lỗi: độ chính xác trông ổn, NEES và NIS thấp hơn nhiều so với kỳ vọng (bộ lọc thiếu tự tin).
- Quá tự tin: $Q$ quá nhỏ; bộ lọc thôi nghe landmark; NEES trung bình cao hơn nhiều so với 3.
- Nhập nhằng ID landmark: hai marker giống nhau bị đổi chỗ; cổng chỉ cứu bạn nếu sai số đủ lớn.
- Chỉnh và kiểm thử trên cùng các seed.
- Độ so với radian ở một chỗ nào đó (gyro tính bằng độ/s, bộ phát hiện tính bằng độ).
- Vô tình dùng sự thật nền trong bộ lọc: thêm bài kiểm thử AST hoặc grep rằng `estimation/` không bao giờ import tư thế thật của simulator (quy tắc CAP04 áp dụng từ đây).
- $P$ mất tính đối xứng và xác định dương vì cập nhật không phải dạng Joseph sau hàng nghìn bước.

## Phương án khác và đánh đổi

**EKF** đơn giản và nhanh nhưng tuyến tính hóa quanh ước lượng và có thể phân kỳ với prior xấu; bộ lọc **unscented** hoặc **error-state (ESKF)** xử lý tính phi tuyến của góc tốt hơn; **particle filter** (AMCL, như trong Nav2) xử lý tư thế đa đỉnh (phòng đối xứng, bị bế đi chỗ khác) với chi phí cao hơn; **factor graph** (GTSAM) làm mượt cả quỹ đạo và thắng về độ chính xác khi xử lý offline. Landmark có thể vào dưới dạng khoảng cách-góc phương vị (ở đây) hoặc phép đo pixel thô (chặt hơn, cần mô hình camera trong bộ lọc). Odometry bánh cộng gyro rẻ; visual odometry bỏ sự phụ thuộc vào tỉ lệ bánh nhưng cần kết cấu bề mặt và một nguồn tỉ lệ; so khớp quét lidar (lập bản đồ CAP04) là cảm biến bổ sung thường dùng. Lựa chọn thư viện, `robot_localization`, nặng về cấu hình nhưng đã được thử lửa; tự viết một lần là cách để học các tham số của nó nghĩa là gì.

## Vận dụng và ghi nhớ

**Milestone này chuẩn bị cho:** CAP04 (planner và bộ lập bản đồ dùng tư thế của bạn và có thể dùng hiệp phương sai của nó), CAP05 (phép biến đổi hand-eye và chuỗi tư thế đế phụ thuộc vào nó), CAP07 (cờ phân kỳ của bộ ước lượng cấp cho bộ giám sát an toàn) và CAP08 (ablation "không cập nhật landmark" và twin sim-to-real đều kiểm thử bộ lọc này).

Câu hỏi ôn cho tuần sau, không xem ghi chú:

1. Viết hàm đo khoảng cách-góc phương vị và Jacobian của nó.
2. Nêu giá trị kỳ vọng của NEES trung bình (3 bậc tự do) và NIS trung bình (2 bậc tự do) và bạn kết luận gì nếu chúng lớn gấp 3 lần.
3. Vì sao phải wrap innovation, và những góc nào cần wrap?
4. Vì sao dùng dạng Joseph, và nó bảo vệ hai tính chất nào của $P$?
5. Điều gì xảy ra với hiệp phương sai khi không có landmark trong tầm nhìn, và vì sao?

## Đáp án bài tập

1. $f=240/\tan(22.5^\circ)=579.4$ px. Góc nhìn ngang $2\arctan(320/579.4)=57.8^\circ$. Điểm chính lý tưởng $(320,\,240)$ (hoặc $(319.5,\,239.5)$ khi tâm pixel ở nửa số nguyên; dung sai kiểm thử 3 px bao cả hai).
2. Cận chính xác $[0.216,\,9.348]$. Trung bình 9.1 so với kỳ vọng 3 nghĩa là sai số thực lớn hơn khoảng ba lần (theo đơn vị chuẩn hóa bình phương) so với điều $P$ thừa nhận: bộ lọc quá tự tin. Kiểm tra $Q$ trước (quá nhỏ, hoặc bias gyro không được mô hình hóa) rồi tới quy ước hệ quy chiếu và dấu của phép đo.
3. Không wrap: $3.10-(-3.10)=6.20$ rad, một innovation vô lý. Có wrap: $6.20-2\pi=-0.083$ rad.
4. Bề rộng pixel $w=579\cdot0.15/2=43.4$ px. $\sigma_Z=Z\,\sigma_w/w=2\cdot0.7/43.4=0.032$ m. Ở 1 m: $w=86.9$ px và $\sigma_Z=0.008$ m; ở 4 m: $w=21.7$ px và $\sigma_Z=0.129$ m (sai số tăng theo $Z^2$). Sai số ngang $Z\,\sigma_{px}/f=2\cdot0.5/579=1.7$ mm: khoảng cách chi phối, đó là lý do $R$ lớn hơn ở khoảng cách so với điều nhiễu pixel gợi ý và vì sao bài kiểm thử landmark chỉ tới 2 m.
5. $\Delta_x=0.9$, $\Delta_y=0.5$, $q=1.06$, $r=1.0296$. Hàng khoảng cách: $[-0.9/1.0296,\,-0.5/1.0296,\,0,\,0]=[-0.874,\,-0.486,\,0,\,0]$. Hàng góc phương vị: $[0.5/1.06,\,-0.9/1.06,\,-1,\,0]=[0.472,\,-0.849,\,-1,\,0]$.
6. Dạng Joseph là tổng của hai ma trận nửa xác định dương, nên $P$ giữ nửa xác định dương và đối xứng (sau một lần đối xứng hóa tường minh) với mọi độ lợi, kể cả độ lợi tính với sai số làm tròn hoặc $R$ chỉnh sai. $(I-KH)P$ chỉ bằng nó với $K$ tối ưu chính xác và trong dấu phẩy động trôi thành bất đối xứng; với $R$ rất nhỏ và hàng nghìn lần cập nhật nó có thể có trị riêng âm, sau đó cổng và phép tính NEES hỏng. Bài kiểm thử kiểm tra tính đối xứng tới $10^{-9}$ và trị riêng nhỏ nhất lớn hơn 0 trong cả lần chạy.
7. Khoảng 1 % của 770, tức 7 đến 8 (ví dụ thấy 8). Với 10 % outlier (khoảng 77 cái được chèn) 61 bị gate là hợp lý: hầu hết outlier bị bắt, một ít (khoảng 24) lọt qua. Với 61 mà không có outlier thì bộ lọc rất quá tự tin hoặc có lỗi hệ quy chiếu/dấu: các innovation lớn hơn nhiều so với $S$ dự đoán.
8. Sai số hướng $0.002\cdot20=0.04$ rad $=2.3^\circ$ ở cuối (tăng tuyến tính, trung bình $0.02$ rad). Sai số vị trí khoảng $0.3\cdot20\cdot0.02=0.12$ m. Hiệp phương sai cũng phải tăng: phương sai hướng tăng xấp xỉ theo $t^2$ (bất định bias nhân thời gian) cộng nhiễu gyro, và phương sai vị trí tăng nhanh hơn. Nếu $P$ in ra phẳng, bộ lọc đang nói dối.
9. A: bước dự đoán quá tự tin (Q quá nhỏ, không có trạng thái bias, lỗi hệ quy chiếu) với $R$ đúng; thổi $Q$ lên và kiểm tra bias gyro trước. B: thiếu tự tin, cả $Q$ và $R$ đều bị thổi phồng (có thể để che một lỗi); tính lại từ dữ liệu. C: NEES ổn nhưng NIS trên kỳ vọng 2: nhiễu bộ phát hiện $R$ quá nhỏ hoặc bộ phát hiện có outlier; tăng $R$ từ thống kê Nhiệm vụ 2 và kiểm tra cổng.
10. Chỉnh trên seed kiểm thử khiến các ngưỡng đo việc bạn khớp năm lần chạy đó tốt đến đâu, không phải bộ lọc tốt đến đâu. Sửa: chỉnh trên một tập riêng (seed 100 đến 119), đóng băng, rồi đánh giá một lần trên 1000 đến 1004. Báo cáo seed nào dùng cho cái nào, và các giá trị đã chỉnh.
11. Mong đợi: không có gyro thì sai số hướng bị chi phối bởi sai tỉ lệ bánh và RMSE tăng (bias trở nên không quan sát được); không landmark thì RMSE cỡ sai số dead-reckoning và NEES vượt xa dải trừ khi $P$ được phép tăng; với outlier và không có cổng RMSE bùng nổ vượt xa +50 %, có cổng thì nó ở trong giới hạn. Ca biên: marker ở $\pm\pi$: không wrap bạn thấy bước nhảy $2\pi$. Một quan sát bác bỏ: NEES trung bình trên 6 ở seed kiểm thử, hoặc $P$ không đổi trong lúc không thấy landmark nào.

## Đọc thêm

- [Camera calibration using OpenCV (LearnOpenCV)](https://learnopencv.com/camera-calibration-using-opencv/) - hiệu chuẩn bàn cờ từng bước.
- [robot_localization (Jazzy)](https://docs.ros.org/en/jazzy/p/robot_localization/) - EKF thư viện và cách cấu hình.
- [AprilTag library](https://github.com/AprilRobotics/apriltag) - phát hiện fiducial và tư thế.
- [Probabilistic Robotics (Thrun, Burgard, Fox)](https://mitpress.mit.edu/9780262201629/probabilistic-robotics/) - các chương định vị và SLAM bằng EKF.
- [Trang tác giả của Thrun](https://sites.google.com/site/thrunstuff) - tài liệu đi kèm sách.
- [Extended Kalman filter (Wikipedia)](https://en.wikipedia.org/wiki/Extended_Kalman_filter) - các phương trình dự đoán/cập nhật và Jacobian ở một chỗ.
- Video: Cyrill Stachniss, *EKF-SLAM*; *Intrinsic Camera Calibration - 5 Minutes with Cyrill*.
