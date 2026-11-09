---
{"title": "Cột mốc capstone 4: lập bản đồ lưới chiếm dụng, lập kế hoạch A* và bám đường đi cho CoreBot", "summary": "Xây lưới chiếm dụng (occupancy grid) log-odds từ lidar và pose ước lượng, làm phồng (inflate) thành costmap, lập kế hoạch bằng A*, bám đường đi trong giới hạn của đế robot, xử lý vật cản động và đánh giá toàn bộ pipeline bằng benchmark có seed cố định và cận Wilson.", "objectives": ["Xây lưới chiếm dụng log-odds từ scan lidar và pose ước lượng, rồi chấm điểm với lưới ground truth bằng IoU.", "Suy ra bán kính inflate từ footprint của robot, biên an toàn và độ bất định của pose, rồi dùng nó trong costmap.", "Cài đặt A* 8 hướng với heuristic octile chấp nhận được (admissible) và chứng minh tối ưu so với Dijkstra.", "Bám đường đi bằng pure pursuit dưới giới hạn vận tốc và gia tốc, dừng hoặc lập kế hoạch lại khi gặp vật cản.", "Đánh giá benchmark điều hướng bằng cận dưới Wilson, hiệu quả đường đi và cổng không va chạm, và bảo vệ các ngưỡng đã chọn."]}
---

## Vì sao điều này quan trọng

Sau CAP03, robot biết đại khái mình đang ở đâu. CAP04 dạy nó **đi đến một nơi**: biến tia lidar thành bản đồ, biến bản đồ thành bề mặt chi phí an toàn, tìm đường ngắn, rồi đi theo đường đó mà không đâm vào gì và không đòi hỏi bánh xe nhiều hơn khả năng. Mọi cột mốc sau đều dựa vào nó: CAP05 cần đế robot đỗ đúng chỗ trước bàn, CAP07 gửi goal điều hướng từ một câu đã được phân tích, và CAP08 đếm timeout điều hướng là một loại lỗi (`NAV_TIMEOUT`) trong ngân sách sai số.

Đây cũng là nơi lỗi tích hợp trở nên đắt đỏ. Một planner đúng nhưng chạy sai frame, một tracker bỏ qua giới hạn góc, hay một bản đồ dựng từ pose thật của simulator thay vì EKF của bạn đều tạo ra robot trông ổn khi demo nhưng trượt benchmark có seed cố định. Vì vậy brief bên dưới đi kèm bộ kiểm thử nghiệm thu, gồm một test bảo đảm code điều hướng không bao giờ import dữ liệu thật của simulator.

**Điểm số.** CAP04 có trọng số 11 trên 100 điểm tốt nghiệp. Các cổng (gate) của nó (in đậm trong phần Kiểm thử) là thành công điều hướng với cận Wilson và không va chạm.

## Trực giác

CAP04 thêm "con mắt trong đầu" cho đế robot: một lưới cho biết chỗ nào trống, một bề mặt chi phí cho biết thân robot được đi đâu, một đường đi xuyên qua nó và một bộ điều khiển bước theo. Hãy hình dung một người thận trọng băng qua căn phòng tối với đèn pin: chùm đèn là lidar, thứ họ nhớ là lưới, thói quen "tránh xa đồ đạc một gang tay" là inflation, và nhịp bước chọn tùy theo khúc cua phía trước gắt đến đâu là tracker.

![Kiến trúc capstone CoreBot Tidy gồm đế firmware-in-the-loop, ước lượng, lập bản đồ và kế hoạch, nhận thức, thao tác, lớp tác vụ và bộ giám sát an toàn](/lesson-figures/CAP-architecture.svg)

*Vị trí của CAP04: dải "mapping/planning" nhận `ScanSample` và `Pose2DCov` rồi tạo `/cmd_vel` cho đế firmware xây ở CAP02.*

Cột mốc này dùng các chủ đề CoreLab trước đó; hãy quay lại khi một bước thấy lạ:

- [CAP03](/lessons/CAP03) cung cấp pose và hiệp phương sai của nó; bản đồ chỉ tốt bằng pose.
- [E02 Planning fundamentals](/lessons/E02) cho A*, heuristic admissible và Dijkstra.
- [C05 LQR](/lessons/C05) là bản nâng cấp tracker tùy chọn (LQR trên sai số cross-track và heading).
- [S05 ROS 2 runtime](/lessons/S05) giải thích executor, callback và QoS cho các wrapper ROS 2 tùy chọn và cho nhánh Nav2.
- Cũng hữu ích: [C08 Sensor fusion](/lessons/C08) và [C12 Nonlinear state estimation](/lessons/C12) để hiểu độ bất định của pose đến từ đâu, và [S07 Robot safety](/lessons/S07) cho khoảng cách dừng.

## Lý thuyết và suy dẫn

Đây là các ghi chú tích hợp: năm công thức và giao diện quyết định cột mốc đạt hay không. Mỗi mục có liên kết về chủ đề gốc.

![Pipeline từ scan lidar và pose EKF qua lưới chiếm dụng, costmap, A star và pure pursuit đến lệnh bánh xe, cùng bộ giám sát dừng và lập kế hoạch lại và hồ sơ chi phí quanh vật cản](/lesson-figures/CAP04.svg)

### 1. Cập nhật log-odds của lưới chiếm dụng (nguồn: CAP03 cho pose, Probabilistic Robotics cho mô hình)

Mỗi ô lưu log-odds $l=\ln\frac{p}{1-p}$ rằng nó bị chiếm. Tia **kết thúc** trong một ô cộng $l_\text{occ}=\ln\frac{0.7}{0.3}=0.847$; mọi ô tia **đi xuyên qua** cộng $l_\text{free}=\ln\frac{0.4}{0.6}=-0.405$. Cập nhật chỉ là phép cộng, đó là lý do dùng log-odds: bằng chứng từ các scan độc lập cứ thế cộng dồn. Kẹp (clamp) về $[-4,4]$ để một ô bị đánh dấu sai có thể đổi ý sau vài scan. Đổi ngược bằng $p=1/(1+e^{-l})$. Giá trị đo ở tầm tối đa là "không có phản hồi", không phải vật cản: bỏ qua cập nhật occupied cho nó.

Điểm cuối trong frame bản đồ là $(x+r\cos(\theta+\alpha),\,y+r\sin(\theta+\alpha))$ với pose **ước lượng** $(x,y,\theta)$. Sai số heading $\delta\theta$ làm lệch điểm cuối ở tầm $r$ sang bên khoảng $r\,\delta\theta$: ở 3 m, 2 độ là 10 cm, tức hai ô. Vì thế điểm bản đồ phụ thuộc vào CAP03.

### 2. Footprint, inflation và costmap (nguồn: S07 cho biên an toàn, CAP03 cho $\sigma$)

Coi robot là một đĩa và planner di chuyển một điểm. Ba bán kính quan trọng: bán kính ngoại tiếp (circumscribed) $r_c$ của footprint (giới hạn cứng: tâm gần ô bị chiếm hơn giá trị này là va chạm), **biên an toàn** $m$, và phần dự phòng cho bất định định vị $2\sigma_\text{pos}$ lấy từ hiệp phương sai EKF:
$$r_\text{inflate}=r_c+m+2\sigma_\text{pos}.$$
Costmap là *lethal* (254) khi gần hơn $r_c$, rồi giảm dần, ví dụ $c(d)=253\,e^{-k(d-r_c)}$ đến $r_\text{inflate}$ và bằng 0 ở ngoài. Với ô kích thước $\Delta$: $n=\lceil r_\text{inflate}/\Delta\rceil$. Goal nằm trong ô lethal là không thể đến theo định nghĩa: hãy đưa nó về ô trống gần nhất hoặc báo `no_path`, đừng bao giờ lập kế hoạch đến đó.

### 3. A* với heuristic octile (nguồn: E02)

Trên lưới 8 hướng, một bước tốn 1 (theo trục) hoặc $\sqrt2$ (chéo). Chi phí chính xác trong không gian trống cho độ lệch $dx,dy$ là $(\max-\min)+\sqrt2\min$, đúng bằng heuristic **octile**:
$$h(dx,dy)=(dx+dy)+(\sqrt2-2)\min(dx,dy).$$
Nó không bao giờ vượt chi phí thật (admissible) và nhất quán (consistent), nên A* với closed set trả về đường tối ưu. Khoảng cách Manhattan đánh giá quá cao các bước chéo và **không** admissible ở đây; khoảng cách Euclid admissible nhưng yếu hơn (mở rộng nhiều nút hơn). Với bước nhận biết chi phí, nhân một bước với $1+w\,c/254$; $w=0$ phải tái tạo đúng Dijkstra, đó chính là test nghiệm thu. Cấm các bước cắt góc ô bị chặn.

### 4. Pure pursuit có giới hạn (nguồn: C05 cho phương án LQR)

Chọn điểm trên đường cách robot khoảng $L$ phía trước, biểu diễn trong frame robot là $(x_r,y_r)$ với $x_r^2+y_r^2=L^2$, và lái theo cung đi qua nó:
$$\kappa=\frac{2y_r}{L^2},\qquad \omega=v\,\kappa.$$
$L$ dài hơn thì mượt hơn nhưng cắt góc; lựa chọn thường gặp là $L=\max(L_\min,\,g\,v)$. Sau đó áp giới hạn đế của CAP02: giảm tốc để $|\omega|\le\omega_\max$ (tức $v\le\omega_\max/|\kappa|$), kẹp $v$ về $v_\max$ và giới hạn $|\Delta v|\le a_\max\,\Delta t$. Nếu thích tracker dựa trên mô hình, LQR trên sai số cross-track và heading ([C05](/lessons/C05)) cho cùng giao diện với hệ số khuếch đại đã chỉnh thay cho quy tắc hình học.

### 5. Khoảng cách dừng và thống kê benchmark (nguồn: S07, RS02)

Quãng đường cần để dừng từ vận tốc $v$ với gia tốc hãm $a$ và tổng độ trễ $t_\ell$ (cảm biến, lập kế hoạch, lệnh, firmware) là
$$d_\text{stop}=\frac{v^2}{2a}+v\,t_\ell.$$
Biên inflation và giới hạn tốc độ phải giữ $d_\text{stop}$ nhỏ hơn khoảng cách mà lidar nhìn thấy vật cản. Với benchmark, đánh giá thành công bằng **cận dưới Wilson 95 %**, không phải ước lượng điểm (công thức trong `evalkit.wilson_interval`, [RS02](/lessons/RS02)): với 30 episode, ước lượng điểm 90 % ứng với cận dưới chỉ 74 %. Hiệu quả đường đi là độ dài đã đi chia cho độ dài đường ngắn nhất trong bản đồ ground truth.

## Ví dụ có lời giải

Đây là vết tham chiếu của một lần chạy đạt. **Giá trị minh họa**: chúng cho thấy con số khỏe mạnh trông thế nào, được tính tay và bằng script nhỏ ở phần Kiểm chứng, không lấy từ lần chạy thật trên robot của bạn.

### Lập bản đồ, inflation, heuristic, tracker, quãng dừng và bảng nghiệm thu

**Đề bài.** Lưới chiếm dụng dùng $p_\text{occ}=0.7$ và $p_\text{free}=0.4$ cho mỗi tia, ngưỡng xuất 0.65 và kích thước ô 0.05 m. Trả lời các câu sau với đủ các bước.

- (a) Log-odds và xác suất của một ô bị ba tia đánh trúng, của một ô bị năm tia trống đi qua, và của một ô bị đánh trúng hai lần và đi qua một lần; ô cuối có được xuất là bị chiếm không?
- (b) Inflation: bán kính ngoại tiếp $r_c=0.20$ m, biên $m=0.05$ m, độ lệch chuẩn vị trí EKF $\sigma=0.03$ m. Tìm $r_\text{inflate}$, số ô inflation $n$ và bán kính lethal tính bằng ô.
- (c) Heuristic A* cho độ lệch xuất phát đến đích $dx=30$, $dy=12$ ô: giá trị octile bằng ô và mét, so với đường thẳng, và có sát (tight) không.
- (d) Pure pursuit với điểm lookahead tại $(0.42,\,0.16)$ m trong frame robot và $v=0.4$ m/s: độ cong và tốc độ góc so với giới hạn 1.5 rad/s.
- (e) Quãng dừng ở $v=0.5$ m/s, $a=1$ m/s$^2$ và tổng trễ 150 ms.
- (f) Quyết định bảng nghiệm thu dưới đây, gồm vì sao 27 trên 30 lần thành công trượt cổng còn 28 trên 30 thì đạt.

**Lời giải.**

1. *Gia số log-odds.* $l_\text{occ}=\ln(0.7/0.3)=0.847$ và $l_\text{free}=\ln(0.4/0.6)=-0.405$; cập nhật là phép cộng thuần túy và ngưỡng chặn $[-4,4]$ không bị chạm trong các ví dụ dưới.
2. *Ba lần trúng.* $l=3\cdot0.847=2.54$, $p=1/(1+e^{-2.54})=0.927$.
3. *Năm lần đi qua ô trống.* $l=5\cdot(-0.405)=-2.03$, $p=1/(1+e^{2.03})=0.116$.
4. *Hai lần trúng và một lần đi qua.* $l=2\cdot0.847-0.405=1.289$, $p=1/(1+e^{-1.289})=0.784>0.65$, nên ô vẫn được xuất là bị chiếm.
5. *Bán kính inflation.* $r_\text{inflate}=r_c+m+2\sigma=0.20+0.05+2\cdot0.03=0.31$ m. Tính bằng ô $n=\lceil0.31/0.05\rceil=\lceil6.2\rceil=7$. Bán kính lethal là $r_c/\Delta=0.20/0.05=4$ ô.
6. *Heuristic octile.* Với bước 8 hướng chi phí 1 và $\sqrt2$, đường rẻ nhất đi $\min(dx,dy)=12$ bước chéo và $dx-12=18$ bước thẳng: $h=(dx+dy)+(\sqrt2-2)\min(dx,dy)=42-0.586\cdot12=34.97$ ô, tức $34.97\cdot0.05=1.749$ m. Đường thẳng là $\sqrt{30^2+12^2}=32.31$ ô, không đạt được trên lưới này. Không có đường thật nào trong không gian trống ngắn hơn 34.97 ô, nên heuristic không bao giờ đánh giá quá cao và, bằng chi phí thật trong không gian trống, nó sát (tight).
7. *Độ cong của tracker.* $L^2=0.42^2+0.16^2=0.1764+0.0256=0.202$, $L=0.449$ m. Pure pursuit cho $\kappa=2y/L^2=2\cdot0.16/0.202=1.584\ \text{m}^{-1}$.
8. *Tốc độ góc.* $\omega=v\kappa=0.4\cdot1.584=0.634$ rad/s, nằm trong giới hạn 1.5 rad/s (không cần giảm tốc).
9. *Quãng dừng.* $d_\text{stop}=v\,t_r+v^2/(2a)=0.5\cdot0.15+0.5^2/(2\cdot1)=0.075+0.125=0.20$ m.
10. *Quy tắc nghiệm thu.* IoU $=\text{TP}/(\text{TP}+\text{FP}+\text{FN})=1900/(1900+120+160)=1900/2180=0.872\ge0.85$. Thành công $28/30=93.3\ \%$ có cận dưới Wilson 95 % là 78.7 %, không nhỏ hơn 75 %, nên cổng đạt. Với $27/30=90.0\ \%$ ước lượng điểm đạt quy tắc 90 % nhưng cận dưới là 74.4 %, dưới 75 %: cổng đòi bằng chứng, không đòi may mắn. Các hàng còn lại so một giá trị đo với một ngưỡng, như trong bảng.

| Kiểm tra (test) | Ngưỡng | Kết quả minh họa |
|---|---|---|
| IoU ô bị chiếm | >= 0.85 | 0.872 (TP 1900, FP 120, FN 160) |
| A* so với Dijkstra, 20 fixture | chính xác | 0 sai khác |
| Thời gian lập kế hoạch trung vị 200 x 200 | < 50 ms | 11.4 ms |
| Cross-track trung bình / lớn nhất | < 0.08 / < 0.20 m | 0.041 / 0.118 m |
| Thành công, 30 episode | >= 90 %, cận dưới >= 75 % | 28/30 = 93.3 %, cận 78.7 % |
| Va chạm | 0 | 0 |
| Hiệu quả đường đi trung vị | <= 1.3 | 1.12 |
| Vật cản động, khoảng hở nhỏ nhất | >= 0.15 m | 0.21 m (1 trong 10 lượt `blocked`) |

**Kiểm tra.** Heuristic: tìm kiếm Dijkstra trên lưới trống 8 hướng từ $(0,0)$ đến $(30,12)$ trả về 34.97 ô, bằng $12\sqrt2+18$ và bằng $h$, đồng thời xác nhận đường thẳng 32.31 không đạt được. Tracker: đường tròn đi qua gốc và $(0.42,\,0.16)$, tiếp xúc với hướng robot, có bán kính $L^2/(2y)=0.631$ m, nghịch đảo là 1.584 m$^{-1}$. Quãng dừng: cả hai số hạng đều bằng mét ($0.5\ \text{m/s}\cdot0.15\ \text{s}$ và $\text{m}^2/\text{s}^2$ chia cho $\text{m/s}^2$) và cộng lại 0.20 m, thoải mái dưới bán kính inflation 0.31 m. Các giá trị bản đồ tính lại được bằng cách cộng các gia số trong một vòng lặp và bằng script ở phần Kiểm chứng.

**Rút ra.** Mọi con số trong vết nghiệm thu đến từ một công thức ngắn (tổng log-odds, $r_c+m+2\sigma$, chi phí octile, $2y/L^2$, $vt_r+v^2/2a$); cổng thành công dùng một cận tin cậy, nên ước lượng điểm vừa chạm 90 % là chưa đủ.

## Bài tập

1. **(Easy)** Một ô bị hai tia đánh trúng và một tia trống đi qua, với $p_\text{occ}=0.7$ và $p_\text{free}=0.4$. Cho log-odds và xác suất của nó. Nó có được xuất là bị chiếm ở ngưỡng 0.65 không?
2. **(Easy)** Robot có bán kính ngoại tiếp 0.22 m, bạn muốn biên 0.05 m và EKF báo $\sigma_\text{pos}=0.04$ m. Cho bán kính inflate theo mét và theo ô 5 cm.
3. **(Easy)** *Thống kê.* Một benchmark điều hướng có 27 thành công trên 30 episode. Tính khoảng Wilson 95 %, cho biết nó có đạt cổng "ước lượng điểm ít nhất 90 % và cận dưới ít nhất 75 %" không, và cần bao nhiêu thành công để đạt.
4. **(Medium)** Với $dx=24$ và $dy=10$ ô, tính giá trị heuristic Manhattan, Euclid và octile và chi phí thật trong không gian trống trên lưới 8 hướng. Heuristic nào admissible?
5. **(Medium)** *Tính toán.* Điểm lookahead là $(0.30,\,-0.12)$ m trong frame robot và robot chạy 0.5 m/s với $\omega_\max=1.5$ rad/s. Tính $\kappa$, $\omega$ và xem tracker có phải giảm tốc không.
6. **(Medium)** *Tích hợp.* Thấy vật cản ở xa 1.5 m phía trước, robot hãm 1 m/s$^2$ với độ trễ 150 ms và cần khoảng hở 0.15 m. Ở tốc độ nào khoảng cách dừng dùng hết toàn bộ khoảng trống? Đáp án nói gì về việc vì sao test vật cản động chủ yếu kiểm tra logic chứ không phải vật lý?
7. **(Medium)** Có sai số heading 2 độ khi dựng bản đồ một bức tường cách 3 m. Ước lượng sai số ngang của các ô tường và cho biết nó ảnh hưởng thế nào đến IoU ô bị chiếm ở độ phân giải 5 cm.
8. **(Hard)** *Thiết kế.* Một hành lang rộng 0.9 m. Với $r_c=0.22$, $m=0.05$ và $\sigma=0.03$ m, rồi $\sigma=0.08$ m, hành lang có đi được trong costmap đã inflate không? Planner nên làm gì khi hiệp phương sai tăng?
9. **(Hard)** *Chống gian lận.* Test AST cấm import `corebot.sim.world` trong các module điều hướng. Nêu ba cách học viên vẫn có thể đưa ground truth vào pipeline và một test bổ sung cho mỗi cách.
10. **(Hard, mini-project)** Chạy benchmark 30 episode trên năm bố cục, rồi phân loại mọi thất bại vào `timeout`, `blocked`, `no_path`, `collision` với nguyên nhân một dòng. Nêu giả định, baseline (phòng trống, goal thẳng), trường hợp biên (goal nằm trong vùng inflation một ô) và quan sát nào khiến bạn bác bỏ planner của mình.

## Cài đặt tham khảo

Khung của module đầu tiên, `mapping/occupancy.py`. Nó không chạy được ở đây (cần NumPy và package `corebot` của bạn) nhưng hợp lệ về cú pháp và khớp với các giao diện của `interfaces.py`.

```python
"""src/corebot/mapping/occupancy.py -- log-odds occupancy grid (skeleton).

Frames: `map` is fixed at the room corner; cell (i, j) covers
x in [x0 + i*res, x0 + (i+1)*res), y in [y0 + j*res, y0 + (j+1)*res).
The pose used here is the EKF estimate from CAP03, never the simulator truth.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from corebot.interfaces import Pose2DCov, ScanSample


@dataclass(frozen=True)
class GridSpec:
    width_m: float = 4.0
    height_m: float = 4.0
    resolution: float = 0.05          # metres per cell
    x0: float = 0.0
    y0: float = 0.0
    p_occ: float = 0.70               # inverse sensor model: cell at the beam end
    p_free: float = 0.40              # cells the beam passed through
    l_min: float = -4.0               # clamp so a cell can change its mind
    l_max: float = 4.0
    occupied_threshold: float = 0.65  # probability used to export a binary grid


class OccupancyGrid:
    def __init__(self, spec: GridSpec) -> None:
        """Allocate `log_odds` (float32, shape (ny, nx)) filled with 0.0 (p = 0.5)."""
        raise NotImplementedError

    def world_to_cell(self, x: float, y: float) -> tuple[int, int] | None:
        """(i, j) for a map-frame point, or None if outside the grid."""
        raise NotImplementedError

    def ray_cells(self, i0: int, j0: int, i1: int, j1: int) -> list[tuple[int, int]]:
        """Bresenham cells from (i0, j0) up to but excluding (i1, j1)."""
        raise NotImplementedError

    def integrate_scan(self, pose: Pose2DCov, scan: ScanSample, max_range: float) -> None:
        """For every finite beam: add l_free to the cells it crosses and l_occ to the end cell
        (only if range < max_range; a max-range reading is 'no hit', not an obstacle).
        Clamp to [l_min, l_max]. Beam angle in the map frame is pose.theta + angle_min + k * angle_inc."""
        raise NotImplementedError

    def probability(self) -> np.ndarray:
        """p = 1 / (1 + exp(-l)) for the whole grid."""
        raise NotImplementedError

    def occupied(self) -> np.ndarray:
        """Boolean grid: probability > spec.occupied_threshold."""
        raise NotImplementedError


def occupied_iou(estimate: np.ndarray, truth: np.ndarray) -> float:
    """|A and B| / |A or B| over occupied cells; 1.0 if both are empty."""
    raise NotImplementedError
```

Hãy điền nó theo công thức ở mục 1, rồi so lưới của bạn với lưới truth từ `bench/` bằng `occupied_iou`.

## Thực hành độc lập

### Mục tiêu
Giao stack điều hướng của CoreBot: một mapper log-odds, một costmap lethal/inscribed/inflated, một planner A* chính xác, một tracker pure pursuit có giới hạn và hành vi dừng/lập kế hoạch lại, và benchmark 30 episode có seed cố định vượt qua bộ nghiệm thu, chỉ dùng pose ước lượng.

### Thiết lập
- Repository: `~/corebot-capstone` (tạo ở CAP01). Làm trên nhánh `cap04`.
- File mới: `src/corebot/mapping/occupancy.py`, `mapping/costmap.py`, `planning/astar.py`, `planning/tracker.py`, `planning/navigator.py`, `configs/nav.yaml`, `tests/acceptance/test_cap04.py`.
- Artefact nằm trong `runs/cap04/`: `map_metrics.json`, `tracker_metrics.json`, `episodes.jsonl`, `dynamic.jsonl`, `hash_run1.json`, `hash_run2.json`, `metrics.json`.
- Lệnh: `make test` cho unit test, `python bench/run_bench.py --milestone cap04 --seeds 1000:1030` cho benchmark, `pytest -q tests/acceptance/test_cap04.py` cho cổng.
- Phiên bản ghim (đặt trong `pyproject.toml`): Python 3.11 trở lên, `numpy` 1.26 trở lên, `pytest` 8. Lidar dùng ray cast, không cần GPU. Benchmark 30 episode mất khoảng 5 đến 15 phút trên CPU laptop.
- Artefact tiên quyết: EKF của CAP03 phát `Pose2DCov` và năm quỹ đạo `traj_*.npz`.

### Nhiệm vụ
1. Cài `OccupancyGrid` (log-odds, tia Bresenham, kẹp, xử lý tầm tối đa) và `occupied_iou`; dựng bản đồ dọc một đường khảo sát có seed và lưu `map_metrics.json`.
2. Cài `inflate` (distance transform, lethal/inscribed/decay) và chọn `inflation_radius` trong `configs/nav.yaml` từ công thức $r_c+m+2\sigma$; ghi số liệu và lập luận vào `docs/nav_design.md`.
3. Cài `astar` (8 hướng, octile, không cắt góc, trọng số chi phí tùy chọn) và một `PlanResult`; chứng minh nó bằng Dijkstra trên 20 fixture.
4. Cài `PurePursuit` với lookahead, giảm tốc theo độ cong, giới hạn vận tốc, góc và gia tốc; lưu `tracker_metrics.json` từ 10 đường tham chiếu.
5. Cài `Navigator.navigate`: lập kế hoạch, bám, quét lại mỗi chu kỳ, dừng khi chi phí inflate phía trước là lethal, lập kế hoạch lại tối đa hai lần, rồi trả về `blocked`.
6. Chạy benchmark 30 episode (seed 1000 đến 1029, năm bố cục) và test vật cản động 10 lượt; lưu `episodes.jsonl` và `dynamic.jsonl`.
7. Chạy cùng một seed hai lần, băm (hash) trace và lưu cả hai hash.
8. Viết `docs/nav_failures.md`: mọi episode thất bại cùng lý do và điều bạn đã đổi (hoặc vì sao không đổi).

### Code khởi đầu
```python
"""Interface stubs for CAP04. Fill in the bodies; keep the signatures (the tests import them)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from corebot.interfaces import NavGoal, NavResult, Pose2DCov, WheelCmd


# ---- src/corebot/mapping/costmap.py ---------------------------------------------------------
def inflate(occupied: np.ndarray, resolution: float, inscribed_radius: float,
            inflation_radius: float, decay: float = 4.0) -> np.ndarray:
    """Return a float cost grid in [0, 254].
    255 is never produced here; 254 = 'lethal': occupied cells and every cell closer than
    inscribed_radius to one. Beyond that cost = 253 * exp(-decay * (d - inscribed_radius)),
    down to 0 at inflation_radius. d comes from a Euclidean distance transform (write your own
    two-pass or brushfire version; scipy is allowed only in the library track)."""
    raise NotImplementedError


# ---- src/corebot/planning/astar.py ----------------------------------------------------------
Cell = tuple[int, int]


@dataclass
class PlanResult:
    path: list[Cell] = field(default_factory=list)   # start..goal inclusive, empty if no path
    cost: float = float("inf")                        # sum of step lengths in cells (1 or sqrt 2)
    expanded: int = 0


def astar(cost_grid: np.ndarray, start: Cell, goal: Cell, lethal: float = 254.0,
          cost_weight: float = 0.0) -> PlanResult:
    """8-connected A* with the octile heuristic. Cells with cost >= lethal are blocked; moves
    that cut a blocked corner are not allowed. Step cost = length * (1 + cost_weight * cell_cost / 254).
    With cost_weight = 0 the result must equal Dijkstra's optimum exactly."""
    raise NotImplementedError


# ---- src/corebot/planning/tracker.py --------------------------------------------------------
@dataclass(frozen=True)
class TrackerLimits:
    v_max: float = 0.5        # m/s
    w_max: float = 1.5        # rad/s
    a_max: float = 1.0        # m/s^2 (linear), also used for braking
    lookahead_min: float = 0.25
    lookahead_gain: float = 0.8   # lookahead = max(lookahead_min, gain * |v|)


class PurePursuit:
    def __init__(self, path_xy: np.ndarray, limits: TrackerLimits = TrackerLimits()) -> None:
        """path_xy: (N, 2) map-frame waypoints."""
        raise NotImplementedError

    def command(self, pose: Pose2DCov, v_now: float, dt: float) -> tuple[WheelCmd, bool]:
        """(cmd, done). Choose the lookahead point, compute curvature kappa = 2*y_r / L^2 in the robot
        frame, slow down with curvature, then clip v and w to the limits and v-change to a_max*dt.
        done is True when the last waypoint is within 0.10 m."""
        raise NotImplementedError


# ---- src/corebot/planning/navigator.py ------------------------------------------------------
class Navigator:
    """Glue: grid -> costmap -> A* -> PurePursuit, with stop/replan/blocked logic."""

    def __init__(self, config_path: str = "configs/nav.yaml") -> None:
        raise NotImplementedError

    def navigate(self, goal: NavGoal, env) -> NavResult:
        """Run one navigation episode against `env` (only env.observe() outputs are allowed:
        ScanSample, WheelState -> your EKF pose). NavResult.reason is one of
        'reached', 'timeout', 'blocked', 'collision', 'no_path'."""
        raise NotImplementedError
```

### Kiểm thử
```python
# tests/acceptance/test_cap04.py
# Thresholds are provisional starting values; tighten them once your own reference run exists.
import ast
import heapq
import json
import math
import pathlib
import random

import numpy as np
import pytest

from corebot.evalkit import load_episodes, wilson_interval
from corebot.mapping.costmap import inflate
from corebot.planning.astar import astar

RUNS = pathlib.Path("runs/cap04")
SRC = pathlib.Path("src/corebot")


def _dijkstra_cost(free: np.ndarray, start, goal):
    """Reference optimum on an 8-connected grid (corner cutting forbidden), stdlib heap."""
    ny, nx = free.shape
    dist = {start: 0.0}
    heap = [(0.0, start)]
    while heap:
        d, (i, j) = heapq.heappop(heap)
        if (i, j) == goal:
            return d
        if d > dist.get((i, j), math.inf):
            continue
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == dj == 0:
                    continue
                a, b = i + di, j + dj
                if not (0 <= a < nx and 0 <= b < ny and free[b, a]):
                    continue
                if di and dj and not (free[j, a] and free[b, i]):
                    continue
                nd = d + (math.sqrt(2) if di and dj else 1.0)
                if nd < dist.get((a, b), math.inf):
                    dist[(a, b)] = nd
                    heapq.heappush(heap, (nd, (a, b)))
    return math.inf


def _fixture(seed, n=40, density=0.25):
    rng = random.Random(seed)
    free = np.array([[rng.random() > density for _ in range(n)] for _ in range(n)])
    free[0, 0] = free[n - 1, n - 1] = True
    return free


# Automated checks -------------------------------------------------------------------------------
def test_mapping_iou():
    m = json.load(open(RUNS / "map_metrics.json"))
    assert m["cell_size_m"] == 0.05
    assert m["occupied_iou"] >= 0.85        # ~85 % of a clean reference: walls are thin, 1 cell = 5 cm


def test_astar_matches_dijkstra_on_20_fixtures():
    for seed in range(1000, 1020):
        free = _fixture(seed)
        grid = np.where(free, 0.0, 254.0)
        want = _dijkstra_cost(free, (0, 0), (39, 39))
        got = astar(grid, (0, 0), (39, 39))
        if math.isinf(want):
            assert got.path == []
        else:
            assert abs(got.cost - want) < 1e-9          # optimal, hence admissible heuristic


def test_astar_median_time_200x200():
    import time
    free = _fixture(1, n=200, density=0.05)   # sparse clutter like the lab room
    grid = np.where(free, 0.0, 254.0)
    ts = []
    for _ in range(5):
        t = time.perf_counter()
        astar(grid, (0, 0), (199, 199))
        ts.append(time.perf_counter() - t)
    assert sorted(ts)[2] < 0.050             # 50 ms: well under one 10 Hz planning period


def test_tracker_limits_and_error():
    r = json.load(open(RUNS / "tracker_metrics.json"))
    assert r["mean_cross_track_m"] < 0.08 and r["max_cross_track_m"] < 0.20
    assert r["max_v"] <= 0.5 + 1e-9 and r["max_w"] <= 1.5 + 1e-9    # the base limits of CAP02
    assert r["max_accel"] <= 1.0 + 1e-9


# GATE: navigation success and zero collisions -----------------------------------------------------
def test_navigation_benchmark():
    eps = load_episodes(RUNS / "episodes.jsonl")
    assert len(eps) >= 30 and len({e["seed"] for e in eps}) == len(eps)
    assert all(e["seed"] in range(1000, 1000 + len(eps)) for e in eps)
    ok = sum(1 for e in eps if e["outcome"] == "success")
    lo, _ = wilson_interval(ok, len(eps))
    assert ok / len(eps) >= 0.90             # point estimate
    assert lo >= 0.75                        # honest bound: 30 episodes cannot prove more
    assert sum(e["collisions"] for e in eps) == 0
    eff = sorted(e["path_length"] / e["shortest_length"] for e in eps if e["outcome"] == "success")
    assert eff[len(eff) // 2] <= 1.3         # median path efficiency
    assert all(e["duration_s"] <= 90.0 for e in eps if e["outcome"] == "success")


def test_dynamic_obstacle():
    trials = load_episodes(RUNS / "dynamic.jsonl")
    assert len(trials) == 10
    assert all(t["min_clearance_m"] >= 0.15 for t in trials)
    assert all(t["outcome"] in ("success", "blocked") for t in trials)


def test_determinism():
    a = json.load(open(RUNS / "hash_run1.json"))
    b = json.load(open(RUNS / "hash_run2.json"))
    assert a["trace_hash"] == b["trace_hash"]


def test_pipeline_never_imports_simulator_truth():
    banned = {"corebot.sim.world", "corebot.sim.truth"}
    for path in list((SRC / "mapping").glob("*.py")) + list((SRC / "planning").glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not banned.intersection(names), f"{path} imports simulator truth"
            if isinstance(node, ast.Attribute):
                assert node.attr not in ("true_pose", "ground_truth"), f"{path} reads {node.attr}"
```

Các ngưỡng là giá trị khởi đầu tạm thời (xem lý giải trong kế hoạch); hãy siết chặt khi bạn đã có lần chạy tham chiếu của riêng mình. Lý do một dòng cho mỗi ngưỡng: IoU 0.85 vì tường dày một hoặc hai ô và lệch một ô đã mất khoảng 10 điểm; A* chính xác vì đã biết nghiệm tối ưu, không có dung sai để tranh cãi; 50 ms để một lần lập kế hoạch nằm gọn trong vòng 10 Hz; cross-track trung bình 0.08 m vì biên inflation là 0.05 m và tracker phải ở trong đó; 0.5 m/s và 1.5 rad/s vì đó là giới hạn đế của CAP02; thành công 90 % với cận dưới 75 % vì 30 episode không chứng minh được hơn thế; va chạm bằng 0 vì va chạm là lỗi an toàn, không phải nhiễu; khoảng hở 0.15 m vì vượt biên 0.05 m một khoảng rõ ràng và khớp với phép tính khoảng cách dừng ở trên; hiệu quả 1.3 vì đường 8 hướng đã inflate hiếm khi dưới 1.1.

Các cổng (phải đạt để giữ cột mốc ở trạng thái "xong"): **test_navigation_benchmark** và phép khẳng định không va chạm bên trong nó.

### Kết quả mong đợi
```
$ pytest -q tests/acceptance/test_cap04.py
........                                                                 [100%]
8 passed in 21.8s

$ cat runs/cap04/metrics.json
{
  "milestone": "CAP04",
  "map": {"occupied_iou": 0.872, "cell_size_m": 0.05},
  "astar": {"fixtures": 20, "mismatches": 0, "median_ms_200x200": 11.4},
  "tracker": {"mean_cross_track_m": 0.041, "max_cross_track_m": 0.118, "max_v": 0.5, "max_w": 1.31},
  "navigation": {"episodes": 30, "success": 28, "wilson_lo": 0.787, "collisions": 0,
                 "median_path_efficiency": 1.12},
  "dynamic": {"trials": 10, "min_clearance_m": 0.21, "blocked": 1}
}
```

Nếu `pytest` báo `1 failed`, hãy đọc thông báo assertion trước: các test in số đo được cạnh ngưỡng.

### Thử thách mở rộng
Làm planner nhận biết bất định của pose: tính lại bán kính inflation từ hiệp phương sai EKF mỗi giây và so thành công cùng hiệu quả đường đi với bán kính cố định trên cùng 30 seed (báo cả hai khoảng Wilson). Thêm chế độ khám phá biên (frontier) để dựng bản đồ không cần đường khảo sát. Tầng phần cứng thật (tùy chọn): nếu bạn đã làm đế ESP32 của CAP02, hãy lái một hình vuông 2 m trên sàn dán băng keo, chỉ cho bánh chạm đất sau khi thử trên bàn với bánh nhấc lên, giới hạn dòng và cầu chì ở đường pin, rồi so đường chỉ dùng odometry với lần chạy sim. Không điểm nào phụ thuộc vào nó.

### Thực hành với thư viện

Thay stack của bạn bằng **Nav2** (ROS 2 Jazzy) và so sánh. Nav2 là thư viện các planner, controller và costmap điều khiển bằng YAML; cùng ý tưởng xuất hiện dưới tên khác. Dùng [mục lục tài liệu Nav2](https://docs.nav2.org/index.html) và cấu hình TurtleBot 4 làm tham chiếu, và kiểm tra tên tham số theo phiên bản bạn cài, vì chúng thay đổi giữa các bản phát hành.

```yaml
# nav2_params.yaml (excerpt, Jazzy; verify names against your installed version)
global_costmap:
  global_costmap:
    ros__parameters:
      resolution: 0.05
      robot_radius: 0.20            # your circumscribed radius r_c
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        inflation_radius: 0.31      # r_c + margin + 2 sigma, the number you derived
        cost_scaling_factor: 4.0    # the decay constant k
planner_server:
  ros__parameters:
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner::NavfnPlanner"
      use_astar: true               # A* instead of Dijkstra
      allow_unknown: false
controller_server:
  ros__parameters:
    controller_plugins: ["FollowPath"]
    FollowPath:
      plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
      desired_linear_vel: 0.5       # v_max of CAP02
      lookahead_dist: 0.45
      max_angular_accel: 3.2
# launch:  ros2 launch nav2_bringup navigation_launch.py params_file:=configs/nav2_params.yaml
# goal:    ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: 1.5}}}}"
```

Chạy cùng 30 goal có seed qua Nav2 bằng package `corebot_bridge` và điền bảng: tỉ lệ thành công của bạn kèm cận Wilson, của Nav2, hiệu quả đường đi trung vị, thời gian lập kế hoạch. Kỳ vọng: cả hai gần 90 % trong căn phòng đơn giản này; Nav2 thắng ở các hành vi phục hồi, bản của bạn thắng ở chỗ kiểm tra được toàn bộ. So sánh này là mục tiêu mở rộng "Nav2 baseline" cho hạng Distinction.

## Kiểm chứng

Hãy kiểm tra các con số bằng tay trước khi tin code. Script dưới đây chỉ dùng thư viện chuẩn và tái tạo ví dụ có lời giải; chạy nó và so lưới cùng planner của bạn với các giá trị này.

```python
import math

# 1. log-odds update: a cell hit 3 times, another crossed by 5 free beams
l_occ, l_free = math.log(0.7 / 0.3), math.log(0.4 / 0.6)
prob = lambda l: 1 / (1 + math.exp(-l))
print("hit x3   : l = %.3f  p = %.3f" % (3 * l_occ, prob(3 * l_occ)))
print("free x5  : l = %.3f  p = %.3f" % (5 * l_free, prob(5 * l_free)))
print("hit,hit,free: p = %.3f" % prob(2 * l_occ + l_free))

# 2. inflation radii in cells (5 cm cells)
res, r_circ, margin, sigma = 0.05, 0.20, 0.05, 0.03
print("lethal radius   = %d cells" % math.ceil(r_circ / res))
print("inflation radius= %d cells (circumscribed + margin + 2 sigma)" % math.ceil((r_circ + margin + 2 * sigma) / res))

# 3. octile heuristic vs straight-line distance, dx = 30, dy = 12 cells
dx, dy = 30, 12
octile = (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)
print("octile %.2f cells = %.3f m; euclid %.2f cells" % (octile, octile * res, math.hypot(dx, dy)))
assert octile <= (dx - dy) + math.sqrt(2) * dy + 1e-12      # equals the true free-space cost

# 4. pure pursuit: lookahead point (0.42, 0.16) in the robot frame, v = 0.4 m/s
x, y = 0.42, 0.16
L2 = x * x + y * y
kappa = 2 * y / L2
print("L = %.3f m, kappa = %.3f 1/m, w = %.3f rad/s" % (math.sqrt(L2), kappa, 0.4 * kappa))

# 5. stopping distance at v = 0.5 m/s, a = 1.0 m/s^2, 150 ms of latency
v, a, lat = 0.5, 1.0, 0.15
print("stop distance = %.3f + %.3f = %.3f m" % (v * v / (2 * a), v * lat, v * v / (2 * a) + v * lat))


# 6. Wilson lower bound for the success rate
def wilson(s, n, z=1.959964):
    p = s / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


for s in (27, 28, 29, 30):
    lo, hi = wilson(s, 30)
    print("%d/30: %.3f  Wilson 95%% [%.3f, %.3f]" % (s, s / 30, lo, hi))
```

Kỳ vọng: đánh trúng ba lần cho $p=0.927$; inflate bảy ô; octile 34.97 ô; $\kappa=1.584$; khoảng cách dừng 0.200 m; với 27/30 khoảng Wilson là [0.744, 0.965].

Sau đó kiểm chứng hành vi: kết quả A* phải bằng chi phí Dijkstra trên mọi fixture; chạy lại cùng seed hai lần và so hash trace; xem ảnh bản đồ đã lưu để tìm tường bị nhân đôi (lỗi pose) và vùng trống quanh robot bị đánh dấu bị chiếm (lỗi dấu hoặc frame). Chạy test AST và xác nhận nó thất bại khi bạn cố ý import truth.

**Điểm số.** Trọng số CAP04 là 11 trên 100 điểm tốt nghiệp. 60 % điểm cột mốc là tự động (phân số có trọng số của các kiểm tra, cổng là benchmark điều hướng), 40 % là rubric tự đánh giá gồm bốn tiêu chí chấm 0 đến 4: bán kính inflation được lập luận từ footprint, xử lý bất định định vị, độ rõ ràng của lý do thất bại và chất lượng test. Tốt nghiệp cần mọi cổng đạt, mọi cột mốc từ 60 trở lên và tổng có trọng số từ 70 trở lên.

## Lỗi thường gặp

- Goal nằm trong ô đã inflate hoặc lethal: planner trả về không có đường hoặc lặp; hãy snap hoặc báo lỗi.
- Kế hoạch tính sai frame (odom thay vì map): robot chạy song song với đường đúng.
- Dao động ở cực tiểu cục bộ hoặc ở cửa hẹp: lookahead quá ngắn, hoặc lập kế hoạch lại mỗi chu kỳ trên chi phí nhiễu; thêm hysteresis.
- Tốc độ điều khiển chậm hơn planner, hoặc ngược lại: tracker bám đường cũ. Ghi lại tuổi của đường.
- Tracker bỏ qua giới hạn góc: đế bị bão hòa, và test cross-track chỉ thất bại ở khúc cua gắt.
- Bản đồ trôi vì sai số pose không được sửa: tường bị nhân đôi. Sửa CAP03, đừng làm mờ bản đồ.
- Giá trị đo ở tầm tối đa bị coi là vật cản: một bức tường ma ở đúng tầm cảm biến.
- Vô tình dùng pose ground truth: benchmark trông hoàn hảo và test AST thất bại.
- Báo 27/30 là "90 %, đạt" mà không có khoảng tin cậy.

## Phương án khác và đánh đổi

Lưới chiếm dụng đơn giản và dày đặc, nhưng bộ nhớ tăng theo diện tích; **bản đồ thưa** hoặc OctoMap mở rộng tốt hơn. A* tối ưu trên lưới nhưng đường bám sát vật cản và zig-zag; **Theta*** hoặc làm mượt sau cho đường thẳng hơn, **D* Lite** lập kế hoạch lại rẻ khi bản đồ đổi, và **RRT\*** hoặc planner dạng lưới (lattice) tôn trọng động học tốt hơn ([E02](/lessons/E02), ghi chú CMU về motion planning). Pure pursuit là quy tắc hình học hai dòng; **LQR** hoặc **MPC** dùng mô hình và xử lý giới hạn tường minh, đổi lại phải tinh chỉnh ([C05](/lessons/C05)); bộ điều khiển regulated pure pursuit của Nav2 thêm điều tiết tốc độ gần vật cản và ở khúc cua. SLAM (ví dụ slam_toolbox) dựng bản đồ và pose cùng lúc; cột mốc này giả định phòng đã biết và một EKF riêng, đơn giản hơn để kiểm thử.

## Vận dụng và ghi nhớ

CAP04 chuẩn bị cho CAP05 (đế đỗ ở nơi cánh tay với tới), CAP07 (goal điều hướng từ câu đã phân tích, và giới hạn tốc độ gần người) và CAP08 (điều hướng là nguồn thất bại lớn nhất cần phân loại). Câu hỏi ôn, trả lời sau một tuần không nhìn ghi chú:

1. Viết cập nhật log-odds cho ô bị đánh trúng và ô trống, và nói vì sao cần kẹp.
2. Cho công thức bán kính inflation và ba điều nó bảo vệ.
3. Vì sao heuristic octile admissible còn Manhattan thì không?
4. Suy ra $\kappa=2y_r/L^2$ từ đường tròn qua gốc và điểm lookahead.
5. Tính cận dưới Wilson cho 28/30 bằng công thức, rồi giải thích điều gì đổi nếu chạy 100 episode.

## Đáp án bài tập

1. $l=2\cdot0.847+(-0.405)=1.289$; $p=1/(1+e^{-1.289})=0.784>0.65$, nên nó được xuất là bị chiếm.
2. $r_\text{inflate}=0.22+0.05+2\cdot0.04=0.35$ m $=7.0$ ô (dùng 7; làm tròn lên khi còn nghi ngờ).
3. Khoảng Wilson cho 27/30: [0.744, 0.965]. Ước lượng điểm 90.0 % đạt, nhưng cận dưới 74.4 % thấp hơn 75 %: cổng trượt. 28/30 cho [0.787, 0.982] và đạt.
4. Manhattan $=34$; Euclid $=\sqrt{24^2+10^2}=26$; octile $=34+(\sqrt2-2)\cdot10=28.14$; chi phí thật $=14+10\sqrt2=28.14$. Euclid và octile admissible; Manhattan (34) đánh giá quá 28.14 nên không.
5. $L^2=0.09+0.0144=0.1044$; $\kappa=2\cdot(-0.12)/0.1044=-2.30$ m$^{-1}$; $\omega=0.5\cdot(-2.30)=-1.15$ rad/s, trong 1.5. Tốc độ giảm $\omega_\max/|\kappa|=0.65$ m/s cao hơn 0.5 m/s, nên không cần giảm tốc.
6. Giải $v^2/2+0.15\,v=1.35$: $v^2+0.3v-2.7=0$, $v=1.5$ m/s. Ở giới hạn đế 0.5 m/s robot chỉ cần 0.2 m để dừng, nên vật lý không bao giờ là yếu tố giới hạn; test kiểm tra rằng logic của bạn phản ứng (dừng, lập kế hoạch lại hoặc báo `blocked`) và costmap đánh dấu vật cản kịp lúc.
7. Sai số ngang $\approx3\tan2^\circ=0.105$ m, khoảng hai ô. Bức tường dày một hai ô sẽ bị vẽ lệch cỡ bề dày của nó, nên phần chồng lấn bị chiếm giảm mạnh (IoU có thể rơi dưới 0.6); bản đồ cần pose chính xác đến một ô.
8. Bán kính inflation $0.22+0.05+0.06=0.33$ m cho bề rộng trống $0.9-0.66=0.24$ m: đi được. Với $\sigma=0.08$: $0.22+0.05+0.16=0.43$ m, bề rộng trống $0.04$ m, nhỏ hơn một ô 5 cm: thực tế bị chặn. Planner tốt báo lý do (`localisation_uncertain`), giảm tốc, hoặc định vị lại bằng landmark trước khi vào, thay vì lặng lẽ inflate mãi.
9. (a) Truyền truth qua thuộc tính của đối tượng `env`: grep `.true_pose`, `ground_truth` (đã có), cộng một test runtime bọc `env` trong đối tượng chỉ lộ `observe()`. (b) Đọc bản đồ từ lưới chiếm dụng của world thay vì lidar: một test tắt lidar và kỳ vọng IoU bản đồ sụp đổ. (c) Dùng dữ liệu khoảng hở thật quanh goal: một test thay đổi truth và kiểm tra kết quả không đổi khi chỉ truth bị đổi.
10. Một đáp án tốt liệt kê seed, năm bố cục, số lỗi theo loại cộng đúng bằng số thất bại, bảng lý do với mỗi nguyên nhân một dòng, thành công baseline gần 100 % trong phòng trống, trường hợp biên báo `no_path` hoặc snap một cách tường minh, và bằng chứng bác bỏ như thành công giảm khi nhiễu lidar tăng gấp đôi theo cách thiết kế của bạn không dự đoán được.

## Đọc thêm

- [Occupancy grid mapping (Wikipedia)](https://en.wikipedia.org/wiki/Occupancy_grid_mapping): mô hình log-odds và mô hình cảm biến nghịch.
- [A* search algorithm (Wikipedia)](https://en.wikipedia.org/wiki/A*_search_algorithm) và [ghi chú CMU Robotic Motion Planning](https://www.cs.cmu.edu/~motionplanning/): tính admissible, consistent và lập kế hoạch trên lưới.
- [Pure pursuit (Wikipedia)](https://en.wikipedia.org/wiki/Pure_pursuit): hình học của quy tắc lookahead.
- [Tài liệu Nav2](https://docs.nav2.org/index.html) và [hướng dẫn TurtleBot 4](https://turtlebot.github.io/turtlebot4-user-manual/): tham chiếu cho nhánh thư viện.
- [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox): lập bản đồ và định vị cùng nhau.
- [Binomial proportion confidence interval (Wikipedia)](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval): khoảng Wilson dùng trong các cổng.
- **Luyện thêm:** xem video của Articulated Robotics, "Making robot navigation easy with Nav2 and ROS!", rồi tái tạo các lựa chọn trong `nav2_params.yaml` của họ vào `configs/nav.yaml` của bạn.
