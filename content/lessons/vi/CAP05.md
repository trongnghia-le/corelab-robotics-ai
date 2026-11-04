---
{"title": "Cột mốc capstone 5: gắp vật theo nhận thức với phân đoạn, tư thế 3D và IK dùng Jacobian", "summary": "Tìm các khối màu trong ảnh RGB-D, biến pixel thành tư thế 3D trong frame gốc cánh tay bằng hiệu chuẩn hand-eye, rồi gắp bằng IK damped least squares, quỹ đạo quintic và bảng phân loại lỗi, đánh giá bằng benchmark 50 lượt có seed cố định.", "objectives": ["Deproject một pixel và độ sâu theo mét thành điểm trong frame camera rồi đưa về frame gốc cánh tay bằng phép biến đổi hand-eye.", "Phân đoạn khối màu bằng baseline HSV và một CNN nhỏ, báo mean IoU trên các seed giữ lại.", "Giải bài gắp từ trên xuống cho cánh tay 5 bậc tự do bằng IK damped least squares, tôn trọng giới hạn khớp và tránh nhảy nhánh.", "Tạo quỹ đạo quintic trong giới hạn vận tốc, gia tốc và mô-men, và kiểm tra tính khả thi bằng động lực học ngược.", "Chạy benchmark pick-and-place có seed cố định, đánh giá bằng cận Wilson và phân loại mọi thất bại trong một taxonomy."]}
---

## Vì sao điều này quan trọng

CoreBot Tidy tồn tại để chuyển một khối từ bàn vào thùng. CAP05 là phần chạm vào vật: nó quyết định **khối ở đâu** (nhận thức), **tiếp cận thế nào** (lập kế hoạch gắp) và **cánh tay đến đó ra sao** (động học, quỹ đạo, mô-men). Đây cũng là nơi đầu tiên các sai số nhân lên: sai một pixel phân đoạn, lệch 5 mm độ sâu, sai 1 độ trong phép quay hand-eye và thiếu một giới hạn khớp cộng lại thành một gripper khép vào không khí.

Cột mốc này độc lập với CAP04 (bạn có thể chạy song song), nhưng cả hai đều xuất phát từ CAP03: cánh tay cần đế được định vị để frame camera, frame đế và frame cánh tay khớp nhau. CAP06 sau này sẽ thay gắp có kịch bản của bạn bằng gắp học được sau cùng giao diện `GraspSkill`, và CAP08 đếm mọi thất bại của cột mốc này trong ngân sách sai số (`DETECTION`, `GRASP_SLIP`, `PLACE_MISS`).

**Điểm số.** CAP05 có trọng số 13 trên 100 điểm tốt nghiệp. Các cổng (in đậm trong phần Kiểm thử) là động học ngược và benchmark pick-and-place. Tầng SO-101 thật tùy chọn không bao giờ thay thế một cổng đang trượt.

## Trực giác

Nhìn, quyết định, với tới. Camera cho màu và khoảng cách của từng pixel; phân đoạn nói pixel nào là "khối đỏ"; deprojection biến các pixel đó thành điểm 3D; một phép biến đổi cố định, **hiệu chuẩn hand-eye**, biểu diễn điểm đó trong frame riêng của cánh tay; động học ngược tìm góc khớp đưa đầu ngón tay đến đó với gripper chúc xuống; một quỹ đạo mượt đưa cánh tay đến các góc đó mà không vượt giới hạn của động cơ. Mỗi bước có một phép kiểm tra số rẻ, và đó chính là ý nghĩa của cột mốc: bạn gỡ lỗi nó như một chuỗi, không phải một bí ẩn.

![Kiến trúc capstone CoreBot Tidy gồm đế firmware-in-the-loop, ước lượng, lập bản đồ và kế hoạch, nhận thức, thao tác, lớp tác vụ và bộ giám sát an toàn](/lesson-figures/CAP-architecture.svg)

*Vị trí của CAP05: khối nhận thức tạo tư thế vật trong frame đế, khối thao tác biến chúng thành quỹ đạo khớp sau giao diện `GraspSkill`.*

Các chủ đề CoreLab trước đó được dùng ở đây:

- [CAP03](/lessons/CAP03): hiệu chuẩn camera (nội tại $K$) và frame đế bạn định vị trong đó.
- [R05 Inverse kinematics](/lessons/R05): nhánh nghiệm, tầm với và các bộ giải số.
- [R06 Robot Jacobian](/lessons/R06): ma trận bên trong bước damped least squares.
- [R07 Rigid-body dynamics](/lessons/R07): động lực học ngược cho kiểm tra khả thi mô-men.
- [V10 Segmentation](/lessons/V10): IoU, mIoU và vệ sinh huấn luyện.
- [V13 3D perception](/lessons/V13): độ sâu, point cloud và căn chỉnh cứng.
- Cũng có: [V04 Camera calibration](/lessons/V04), [R03 Rigid-body transformations](/lessons/R03) và [R04 Forward kinematics](/lessons/R04) (FK của CAP01 là mô hình mà bộ giải dùng).

## Lý thuyết và suy dẫn

Các ghi chú tích hợp: công thức và giao diện quyết định cột mốc đạt hay không.

![Pipeline từ ảnh RGB-D qua phân đoạn, deprojection và phép biến đổi hand-eye thành một detection, rồi lập kế hoạch gắp, động học ngược, quỹ đạo quintic và cánh tay, cùng khối taxonomy lỗi](/lesson-figures/CAP05.svg)

### 1. Deprojection (nguồn: V04, V13)

Với camera pinhole có nội tại $f_x,f_y,c_x,c_y$, một pixel $(u,v)$ có độ sâu $z$ theo mét (khoảng cách dọc trục quang) ánh xạ thành
$$p_\text{cam}=\Big(\tfrac{u-c_x}{f_x}\,z,\ \tfrac{v-c_y}{f_y}\,z,\ z\Big)$$
trong frame quang học (x phải, y xuống, z phía trước). MuJoCo cho góc nhìn dọc, nên $f_y=\frac{H/2}{\tan(\text{fovy}/2)}$ và $f_x=f_y$ với pixel vuông. Bộ đệm độ sâu của MuJoCo đã **chuẩn hóa**, không phải mét: đổi bằng mặt phẳng near và far trước khi dùng, và loại giá trị không dương. Dùng **median** của các điểm theo từng pixel trong mask, không dùng mean, vì viền mask trộn độ sâu của khối và nền.

### 2. Hiệu chuẩn hand-eye (nguồn: R03, V13)

Tư thế camera trong frame đế là phép biến đổi cứng $T_\text{base,cam}=(R,t)$. Cho các cặp điểm $p_i^\text{cam}$ và $p_i^\text{base}$ (thu bằng cách chạm hoặc đọc truth của simulator, chỉ trong lúc hiệu chuẩn), phép biến đổi bình phương tối thiểu đến từ phương pháp Kabsch: trừ trọng tâm, lấy SVD của $H=\sum \tilde p^\text{cam}_i\,(\tilde p_i^\text{base})^\top=U\Sigma V^\top$, rồi $R=V\,\mathrm{diag}(1,1,\det(VU^\top))\,U^\top$ và $t=\bar p^\text{base}-R\bar p^\text{cam}$. Dùng ít nhất 10 điểm phân tán tốt, không thẳng hàng, và **đánh giá trên các điểm giữ lại**. Sai một pixel tương đương $z/f_y\approx1$ mm ở 0.42 m, nên mục tiêu RMS 5 mm là khoảng năm pixel sai số tổng.

### 3. IK damped least squares cho cánh tay 5 bậc tự do (nguồn: R05, R06)

Cánh tay SO-101 có năm khớp trước gripper, nên bạn không thể ra lệnh đầy đủ tư thế 6D. Gắp từ trên xuống cần vị trí đầu công cụ (3 số) và pitch tiếp cận (1 số); cổ tay xoay (roll) được đặt sau từ yaw của vật. Với sai số tác vụ $e=[\Delta p;\ \Delta\text{pitch}]$ và Jacobian tác vụ $J\in\mathbb R^{4\times5}$:
$$\Delta q=J^\top\big(JJ^\top+\lambda^2I\big)^{-1}e,$$
kẹp mỗi bước khớp ở $0.2$ rad, kẹp $q$ về giới hạn sau mỗi bước, và **bắt đầu từ các khớp hiện tại** để nghiệm ở yên trên một nhánh. Gần điểm kỳ dị, giả nghịch đảo bùng nổ ($1/\sigma$); bản damped bị chặn bởi $\sigma/(\sigma^2+\lambda^2)\le1/(2\lambda)$. Một cánh tay phẳng có hai nghiệm (khuỷu lên/xuống); chọn nghiệm có góc khớp nằm trong giới hạn và gần $q_\text{now}$ nhất.

### 4. Quỹ đạo và khả thi mô-men (nguồn: R07)

Một quintic với $s=t/T$ và hàm trộn $10s^3-15s^4+6s^5$ bắt đầu và kết thúc với vận tốc và gia tốc bằng không. Với một chuyển động khớp $|\Delta q|$ các đỉnh là
$$\dot q_\max=\tfrac{15}{8}\tfrac{|\Delta q|}{T}=1.875\tfrac{|\Delta q|}{T},\qquad \ddot q_\max=\tfrac{10}{\sqrt3}\tfrac{|\Delta q|}{T^2}=5.7735\tfrac{|\Delta q|}{T^2},$$
nên thời lượng khả thi ngắn nhất là $T=\max_j\big(\tfrac{1.875|\Delta q_j|}{v_j},\sqrt{\tfrac{5.7735|\Delta q_j|}{a_j}}\big)$. Sau đó kiểm tra mô-men bằng động lực học ngược $\tau=M(q)\ddot q+C(q,\dot q)\dot q+g(q)$ dọc quỹ đạo đã lấy mẫu so với `forcerange` của actuator trong MJCF. Giữ cánh tay duỗi dài chống trọng lực thường đã dùng phần lớn mô-men vai trước khi cộng gia tốc.

### 5. Chỉ số phân đoạn và thống kê benchmark (nguồn: V10, RS02)

Với mỗi lớp, $\text{IoU}=\frac{TP}{TP+FP+FN}$ và mIoU là trung bình trên các lớp có trong truth. Chia train, validation và test theo **seed cảnh**, không theo frame: các frame của một episode gần như trùng nhau, nên chia theo frame làm rò rỉ tập test và thổi phồng mIoU. Với benchmark dùng cận dưới Wilson 95 % (`evalkit.wilson_interval`) và một taxonomy lỗi có tổng số đếm đúng bằng số thất bại.

## Ví dụ có lời giải

Vết tham chiếu của một lần chạy đạt. **Giá trị minh họa**, tính bằng script thư viện chuẩn trong phần Kiểm chứng (dùng các link minh họa $L_1=0.116$, $L_2=0.135$, $L_3=0.10$ m; hãy đọc giá trị của bạn từ MJCF), không lấy từ lần chạy thật.

**Từ pixel đến đế.** Ảnh 640 x 480, fovy 60 độ: $f_y=240/\tan30^\circ=415.7$ px. Pixel $(352,236)$ ở độ sâu 0.42 m cho $p_\text{cam}=(0.0323,\,-0.0040,\,0.420)$ m. Camera đặt ở $(0.10,0,0.35)$ m trong `base_link`, chúc xuống 50 độ, nên $p_\text{base}=(0.3731,\,-0.0323,\,0.0309)$ m. Trụ cánh tay nằm trước `base_link` 0.17 m, nên trong `arm_base`: $(0.2031,\,-0.0323,\,0.0309)$ m, bán kính $r=0.2056$ m.

**IK.** Pan $=\operatorname{atan2}(-0.0323,0.2031)=-9.0^\circ$. Bài toán phẳng với công cụ chúc xuống có hai nhánh: (vai $-9.3^\circ$, khuỷu $+56.8^\circ$) cần cổ tay $-137.5^\circ$, ngoài giới hạn minh họa $\pm110^\circ$; (vai $52.2^\circ$, khuỷu $-56.8^\circ$) cần $-85.4^\circ$ và được chấp nhận. FK của nghiệm được chọn trả về đích với sai số $10^{-9}$ m.

**Quỹ đạo.** Một chuyển động khớp 0.8 rad trong 1.2 s: tốc độ đỉnh $1.875\cdot0.8/1.2=1.25$ rad/s, gia tốc đỉnh $5.7735\cdot0.8/1.44=3.21$ rad/s$^2$.

| Kiểm tra (test) | Ngưỡng | Kết quả minh họa |
|---|---|---|
| IK, 200 đích với tới được | >= 98 %, sai số < 2 mm | 199/200, tệ nhất 0.9 mm, bước khớp lớn nhất 0.07 rad |
| RMS hand-eye (giữ lại) | < 5 mm | 2.7 mm trên 24 điểm |
| mIoU phân đoạn (300 frame) | >= 0.85 | CNN 0.912, baseline HSV 0.874 |
| Sai số tâm, 0.3-0.6 m | trung vị < 1.5 cm | 0.83 cm |
| Vận tốc / gia tốc / mô-men | <= giới hạn, >= 99 % | 82 % / 91 % giới hạn, 99.6 % |
| Gắp thành công, 50 lượt | >= 80 %, cận dưới >= 68 % | 43/50 = 86 %, cận 73.8 % |
| Đặt vào thùng | >= 75 % | 40/50 = 80 % |
| Thời gian chu kỳ trung bình | < 25 s | 19.7 s |
| Taxonomy lỗi | tổng = số lỗi (10) | slip 4, knocked 3, place_miss 3 |

Lưu ý 40 trên 50 lượt gắp (80 %) đạt ước lượng điểm nhưng cận dưới là 67.0 % và trượt cổng một phần trăm.

## Bài tập

1. **(Easy)** Camera 640 x 480 có góc nhìn dọc 60 độ. Tính $f_y$ và kích thước một pixel ở độ sâu 0.42 m.
2. **(Easy)** Với $f_x=f_y=415.7$, $c=(320,240)$, deproject pixel $(400,200)$ ở độ sâu 0.5 m vào frame quang học.
3. **(Easy)** *Thống kê.* Một benchmark gắp có 43 thành công trên 50 lượt và một lần chạy khác có 40 trên 50. Tính cả hai khoảng Wilson và cho biết lần nào đạt "ít nhất 80 % và cận dưới ít nhất 68 %".
4. **(Medium)** Một khớp phải di chuyển 0.6 rad với giới hạn $v_\max=1.5$ rad/s và $a_\max=4$ rad/s$^2$. Tính thời lượng quintic ngắn nhất và cho biết giới hạn nào ràng buộc.
5. **(Medium)** *Vì sao cần damping.* Một Jacobian tác vụ có các giá trị suy biến 1 và 0.01 và sai số là 0.1 m theo mỗi hướng suy biến. So sánh bước giả nghịch đảo với bước damped ở $\lambda=0.1$.
6. **(Medium)** *Phân đoạn.* Số đếm lớp trên tập test: nền TP 9400, FP 250, FN 150; đỏ TP 320, FP 40, FN 60; xanh dương TP 280, FP 20, FN 40. Tính ba IoU và mIoU, và cho biết có đạt 0.85 không.
7. **(Medium)** *Mô-men.* Khối lượng và tay đòn quanh vai: link 0.15 kg tại 0.07 m, cẳng tay 0.12 kg tại 0.19 m, gripper cộng khối 0.08 kg tại 0.28 m, quán tính hiệu dụng 0.012 kg m$^2$, gia tốc đỉnh 3.2 rad/s$^2$. Ước lượng mô-men vai và so với giới hạn actuator 1.0 N m (minh họa).
8. **(Medium)** *Gỡ lỗi.* Gắp chỉ thất bại khi khối nằm xa về bên trái bàn, và gripper luôn khép lệch khoảng 3 cm sang phải của khối. Liệt kê ba nguyên nhân có khả năng theo thứ tự bạn sẽ kiểm tra.
9. **(Hard)** *Thiết kế.* Yaw của khối là 100 độ trong bản đồ, pan của cánh tay là $-9^\circ$ và gripper đối xứng khi quay 180 độ. Chọn roll cổ tay trong $[-90^\circ,90^\circ)$ để gripper khép qua cạnh ngắn của khối, và giải thích vì sao bạn rút gọn theo modulo 180.
10. **(Hard, mini-project)** Dựng benchmark 50 lượt với tư thế và yaw ngẫu nhiên của khối (seed 1000 đến 1049), ghi `reason` cho mọi thất bại và viết `docs/failure_taxonomy.md` kèm cách sửa cho loại lớn nhất. Nêu giả định, baseline (khối ở giữa bàn, yaw 0), trường hợp biên (khối ở mép không gian làm việc) và quan sát nào khiến bạn bác bỏ pipeline của mình.

## Cài đặt tham khảo

Khung của module trung tâm, `manipulation/ik.py`. Nó không chạy được ở đây (cần NumPy và `ArmModel` của CAP01) nhưng hợp lệ về cú pháp và nhất quán với các giao diện của `interfaces.py`.

```python
"""src/corebot/manipulation/ik.py -- damped least-squares IK for the 5-DOF SO-101 arm (skeleton).

Task space: tool-tip position (3) + approach pitch (1) = 4 constraints. The 5th joint
(wrist_roll) is set afterwards from the object yaw, so it never enters the Jacobian.
Frames: targets are expressed in `arm_base`; angles in rad; lengths in m.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from corebot.manipulation.kinematics import ArmModel   # wraps your CAP01 fk (see Setup)


@dataclass(frozen=True)
class IKResult:
    q: np.ndarray            # (5,) joint angles, always inside the limits
    success: bool            # position error < tol and pitch error < pitch_tol
    pos_err: float           # metres
    pitch_err: float         # rad
    iterations: int


def task_error(arm: ArmModel, q: np.ndarray, target_xyz: np.ndarray, target_pitch: float) -> np.ndarray:
    """(4,) = [target_xyz - tip_xyz, wrap(target_pitch - tip_pitch)]."""
    raise NotImplementedError


def task_jacobian(arm: ArmModel, q: np.ndarray) -> np.ndarray:
    """(4, 5) = [linear tip Jacobian rows; pitch row]. Check it against finite differences."""
    raise NotImplementedError


def solve_ik(arm: ArmModel, target_xyz: np.ndarray, target_pitch: float, q0: np.ndarray,
             damping: float = 0.05, tol: float = 1e-3, pitch_tol: float = 0.02,
             max_iter: int = 100, max_step: float = 0.2) -> IKResult:
    """dq = J^T (J J^T + damping^2 I)^-1 e, step clipped to max_step per joint, q clipped to the
    limits after every step. Start from q0 (the current joints) so the solution stays on one
    branch. Never raise on 'unreachable': return success=False with the best q found."""
    raise NotImplementedError


def wrist_roll_for_yaw(object_yaw: float, pan: float) -> float:
    """Roll that aligns the jaws across the object's short side, reduced to the nearest
    equivalent of a symmetric (180-degree) gripper, inside the roll limits."""
    raise NotImplementedError
```

Hãy kiểm tra `task_jacobian` bằng sai phân hữu hạn của FK trước khi tin bộ giải: một sai dấu ở một cột khiến vòng lặp đi lang thang mà không bao giờ báo lỗi.

## Thực hành độc lập

### Mục tiêu
Giao chuỗi thao tác của CoreBot: deprojection và hiệu chuẩn hand-eye, baseline màu và một CNN nhỏ cho phân đoạn, gắp từ trên xuống bằng damped least squares với quỹ đạo quintic, và benchmark pick-and-place 50 lượt có seed cố định kèm taxonomy lỗi, tất cả vượt bộ nghiệm thu và chỉ dùng dữ liệu camera (không bao giờ dùng truth của simulator) khi chạy.

### Thiết lập
- Repository: `~/corebot-capstone`, nhánh `cap05`. `models/corebot.xml` và FK của CAP01 phải qua các test riêng của chúng. CAP05 bọc `fk`/`fk_pose` của CAP01 trong lớp `ArmModel` mà bạn thêm vào `manipulation/kinematics.py`: `ArmModel.from_mjcf(path)`, `limits` (5 x 2, rad), `home` (5,) và `fk(q) -> (xyz, pitch)` trong `arm_base`.
- File mới: `perception/depth.py`, `perception/hand_eye.py`, `perception/segmentation.py` (+ `perception/make_dataset.py`), `manipulation/ik.py`, `grasp.py`, `trajectory.py`, `tests/acceptance/test_cap05.py`, `docs/failure_taxonomy.md`.
- Artefact trong `runs/cap05/`: `ik_path.json`, `hand_eye.npz`, `segmentation.json`, `localisation.npz`, `trajectory.json`, `picks.jsonl`, `failure_taxonomy.json`, `metrics.json`. Trọng số đã huấn luyện trong `models/segnet.npz` (dưới 20 MB).
- Lệnh: `python -m corebot.perception.make_dataset --seeds 0:600` (render RGB cùng bộ đệm `segmentation` của MuJoCo làm nhãn), `python -m corebot.perception.segmentation --train`, `python bench/run_bench.py --milestone cap05 --seeds 1000:1050`, `pytest -q tests/acceptance/test_cap05.py`.
- Phiên bản ghim: Python 3.11 trở lên, `mujoco` 3.x, `numpy` 1.26 trở lên, `pytest` 8; CNN có thể chỉ dùng NumPy hoặc `torch` (CPU) nếu bạn ghim nó. Render: `MUJOCO_GL=egl`, với `osmesa` là phương án chậm (khoảng 5 đến 10 khung hình mỗi giây ở 320 x 240). Sinh dataset mất khoảng 10 đến 20 phút, huấn luyện 5 đến 30 phút trên CPU laptop, benchmark khoảng 15 phút.
- Huấn luyện trên seed cảnh 0 đến 599, chỉnh trên 600 đến 699, test trên 700 đến 999 (300 frame, mỗi seed một frame) với texture và ánh sáng khác; không bao giờ dùng seed từ 1000 trở lên cho thứ gì ngoài benchmark.

### Nhiệm vụ
1. `deproject` và `mask_to_xyz_cam` kèm đổi độ sâu; kiểm thử đơn vị với các số tính tay của ví dụ có lời giải.
2. `fit_rigid_transform` (Kabsch) và script hiệu chuẩn thu 24 cặp điểm, lưu `hand_eye.npz` cùng `configs/hand_eye.yaml`; đánh giá trên các điểm giữ lại.
3. `hsv_baseline`, `miou`, bộ sinh dataset và một `SegNet` nhỏ; lưu `segmentation.json` với cả hai mIoU.
4. `task_error`, `task_jacobian` (kiểm tra sai phân hữu hạn), `solve_ik` và `wrist_roll_for_yaw`.
5. `plan_grasp` (pre-grasp, grasp, lift) và `quintic`, `min_duration`, cộng kiểm tra mô-men bằng động lực học ngược với MuJoCo (`mj_inverse`).
6. `ScriptedGraspSkill.execute` với các lý do lỗi của taxonomy và bước xác minh (độ mở gripper và độ cao vật sau khi nhấc).
7. Chạy 50 lượt có seed, viết `picks.jsonl`, `failure_taxonomy.json` và `docs/failure_taxonomy.md` kèm một cách sửa cho mỗi loại.

### Code khởi đầu
```python
"""Interface stubs for CAP05. Keep the signatures: tests/acceptance/test_cap05.py imports them."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from corebot.interfaces import Detection, GraspGoal, GraspResult, ImageFrame


# ---- src/corebot/perception/depth.py --------------------------------------------------------
def deproject(u: float, v: float, depth_m: float, K: np.ndarray) -> np.ndarray:
    """Pixel + metric depth (z along the optical axis) -> (3,) point in the OpenCV optical frame
    (x right, y down, z forward). MuJoCo renders depth as a normalised buffer: convert to metres
    first (document the formula you use) and reject depth <= 0 or non-finite."""
    raise NotImplementedError


def mask_to_xyz_cam(depth_m: np.ndarray, mask: np.ndarray, K: np.ndarray) -> np.ndarray | None:
    """Robust 3D centroid of a binary mask: drop invalid depths, use the median of the
    per-pixel points (not the mean: mask edges bleed into the background). None if < 30 pixels."""
    raise NotImplementedError


# ---- src/corebot/perception/hand_eye.py -----------------------------------------------------
def fit_rigid_transform(points_cam: np.ndarray, points_base: np.ndarray) -> np.ndarray:
    """4x4 T_base_cam minimising sum |R p_cam + t - p_base|^2 (Kabsch/SVD, det(R) = +1)."""
    raise NotImplementedError


def transform_points(T: np.ndarray, pts: np.ndarray) -> np.ndarray:
    raise NotImplementedError


# ---- src/corebot/perception/segmentation.py -------------------------------------------------
CLASSES = ("background", "red", "green", "blue", "bin", "table")


def hsv_baseline(rgb: np.ndarray) -> np.ndarray:
    """(H, W) uint8 class map from fixed colour thresholds. Record its mIoU too."""
    raise NotImplementedError


def miou(pred: np.ndarray, truth: np.ndarray, n_classes: int = len(CLASSES)) -> float:
    """Mean over classes present in `truth` of TP / (TP + FP + FN)."""
    raise NotImplementedError


class SegNet:
    """Small CNN (about 100-300 k parameters, < 20 MB on disk), 128x96 input, CPU friendly."""

    def predict(self, rgb: np.ndarray) -> np.ndarray:
        raise NotImplementedError


# ---- src/corebot/manipulation/grasp.py ------------------------------------------------------
@dataclass(frozen=True)
class GraspPlan:
    pregrasp_q: np.ndarray
    grasp_q: np.ndarray
    lift_q: np.ndarray
    gripper_open: float
    gripper_closed: float


def plan_grasp(det: Detection, T_arm_base: np.ndarray, arm, q_now: np.ndarray) -> GraspPlan | None:
    """Top-down grasp: pre-grasp 0.08 m above the object, grasp at its centre height, lift 0.10 m.
    Returns None when any of the three IK solves fails or violates a limit (reason -> taxonomy)."""
    raise NotImplementedError


# ---- src/corebot/manipulation/trajectory.py -------------------------------------------------
def quintic(q0: np.ndarray, q1: np.ndarray, duration: float, dt: float) -> np.ndarray:
    """(N, 5) samples with zero velocity and acceleration at both ends:
    q(s) = q0 + (q1 - q0) (10 s^3 - 15 s^4 + 6 s^5), s = t / duration."""
    raise NotImplementedError


def min_duration(dq: np.ndarray, v_max: np.ndarray, a_max: np.ndarray) -> float:
    """Smallest T for which the quintic keeps |v| <= v_max and |a| <= a_max on every joint
    (peak v = 1.875 |dq| / T, peak a = 5.7735 |dq| / T^2)."""
    raise NotImplementedError


# ---- the skill interface (CAP06 swaps the implementation behind it) --------------------------
class ScriptedGraspSkill:
    def execute(self, goal: GraspGoal, env) -> GraspResult:
        """Perceive -> plan -> move -> close -> lift -> verify (gripper width and object height).
        GraspResult.reason is one of: 'ok', 'no_detection', 'ik_fail', 'joint_limit', 'slip',
        'knocked', 'place_miss', 'timeout' (the failure taxonomy keys)."""
        raise NotImplementedError
```

### Kiểm thử
```python
# tests/acceptance/test_cap05.py
# Thresholds are provisional starting values; tighten them once your own reference run exists.
import json
import pathlib
from collections import Counter

import numpy as np

from corebot.evalkit import load_episodes, wilson_interval
from corebot.manipulation.ik import solve_ik
from corebot.manipulation.kinematics import ArmModel
from corebot.manipulation.trajectory import quintic
from corebot.perception.hand_eye import fit_rigid_transform, transform_points

RUNS = pathlib.Path("runs/cap05")
ARM = ArmModel.from_mjcf("models/corebot.xml")
TAXONOMY = {"no_detection", "ik_fail", "joint_limit", "slip", "knocked", "place_miss", "timeout"}


def _reachable_targets(n, seed):
    """Sample q inside the limits, take the FK tip: reachable by construction, pitch free."""
    rng = np.random.default_rng(seed)
    lo, hi = ARM.limits[:, 0], ARM.limits[:, 1]
    return [ARM.fk(rng.uniform(lo, hi)) for _ in range(n)]


# GATE: inverse kinematics --------------------------------------------------------------------------
def test_ik_200_reachable_targets():
    ok = 0
    for k, (xyz, pitch) in enumerate(_reachable_targets(200, seed=1000)):
        q0 = np.clip(ARM.home + 0.1 * np.random.default_rng(2000 + k).standard_normal(5),
                     ARM.limits[:, 0], ARM.limits[:, 1])
        r = solve_ik(ARM, xyz, pitch, q0)
        assert np.all(r.q >= ARM.limits[:, 0] - 1e-9) and np.all(r.q <= ARM.limits[:, 1] + 1e-9)
        ok += bool(r.success and r.pos_err < 2e-3)
    assert ok / 200 >= 0.98                 # reachable by construction, so only the solver can fail


def test_ik_path_has_no_branch_flip():
    q = json.load(open(RUNS / "ik_path.json"))["q"]       # waypoints along a straight tip line
    step = np.abs(np.diff(np.array(q), axis=0)).max()
    assert step < 0.2                       # rad: a larger jump between neighbours is a branch flip


def test_hand_eye_rms():
    d = np.load(RUNS / "hand_eye.npz")                      # held-out points not used for the fit
    T = fit_rigid_transform(d["fit_cam"], d["fit_base"])
    err = np.linalg.norm(transform_points(T, d["test_cam"]) - d["test_base"], axis=1)
    assert np.sqrt(np.mean(err ** 2)) < 0.005               # 5 mm: about five pixels of image error at 0.4 m


def test_segmentation_miou():
    m = json.load(open(RUNS / "segmentation.json"))
    assert m["n_eval_frames"] == 300 and m["eval_seeds_disjoint_from_train"] is True
    assert m["miou_cnn"] >= 0.85            # coloured blocks on a plain table: a solved problem
    assert "miou_hsv_baseline" in m         # the baseline must be recorded, whatever its value
    assert m["weights_mb"] < 20


def test_localisation_error():
    d = np.load(RUNS / "localisation.npz")                  # base-frame estimate vs truth, dist 0.3-0.6 m
    assert np.all((d["dist_m"] >= 0.3) & (d["dist_m"] <= 0.6))
    assert np.median(np.linalg.norm(d["est"] - d["truth"], axis=1)) < 0.015


def test_trajectory_limits_and_torque():
    t = json.load(open(RUNS / "trajectory.json"))
    assert t["max_vel_ratio"] <= 1.0 and t["max_acc_ratio"] <= 1.0   # fractions of the limits
    assert t["tracking_rms_m"] < 0.005
    assert t["torque_within_limit_fraction"] >= 0.99
    traj = quintic(np.zeros(5), np.full(5, 0.5), 1.0, 0.01)
    assert np.allclose(traj[0], 0) and np.allclose(traj[-1], 0.5)


# GATE: pick-and-place benchmark ------------------------------------------------------------------
def test_picks_benchmark():
    eps = load_episodes(RUNS / "picks.jsonl")
    n = len(eps)
    assert n == 50 and [e["seed"] for e in eps] == list(range(1000, 1050))
    picks = sum(e["pick_ok"] for e in eps)
    places = sum(e["place_ok"] for e in eps)
    lo, _ = wilson_interval(picks, n)
    assert picks / n >= 0.80 and lo >= 0.68
    assert places / n >= 0.75
    assert np.mean([e["cycle_s"] for e in eps]) < 25.0
    assert sum(e["joint_limit_violations"] for e in eps) == 0


def test_failure_taxonomy_adds_up():
    eps = load_episodes(RUNS / "picks.jsonl")
    failed = [e for e in eps if not (e["pick_ok"] and e["place_ok"])]
    tax = json.load(open(RUNS / "failure_taxonomy.json"))
    assert set(tax) <= TAXONOMY
    assert sum(tax.values()) == len(failed)
    assert Counter(e["reason"] for e in failed) == Counter(tax)
```

Các ngưỡng là giá trị khởi đầu tạm thời (xem lý giải trong kế hoạch); hãy siết chặt khi bạn đã có lần chạy tham chiếu của riêng mình. Lý do một dòng cho mỗi ngưỡng: IK 98 % trên 200 đích vì các đích với tới được theo cách dựng và chỉ bộ giải của bạn có thể thất bại; 2 mm vì một khối rộng 2 đến 3 cm và gripper chịu được khoảng 5 mm; bước khớp 0.2 rad vì bước nhảy lớn hơn giữa các waypoint lân cận là nhảy nhánh; hand-eye 5 mm vì một pixel khoảng 1 mm ở 0.42 m và việc gắp chịu được vài milimét; mIoU 0.85 vì khối màu trên bàn trơn là bài toán đã giải, và dưới mức đó viền mask bắt đầu làm lệch tâm; tâm 1.5 cm vì nó phải nằm trong nửa bề rộng khối; giới hạn 100 % và mô-men 99 % vì vi phạm giới hạn trong mô phỏng là mối nguy thật, còn phần trăm cuối dành cho nhiễu số; gắp 80 % với cận dưới 68 % vì 50 lượt không chứng minh được hơn thế; chu kỳ trung bình 25 s để CAP08 chạy 160 episode trong vài giờ.

Các cổng: **test_ik_200_reachable_targets** và **test_picks_benchmark**.

### Kết quả mong đợi
```
$ pytest -q tests/acceptance/test_cap05.py
........                                                                 [100%]
8 passed in 96.4s

$ cat runs/cap05/metrics.json
{
  "milestone": "CAP05",
  "ik": {"targets": 200, "success": 199, "max_pos_err_m": 0.0009, "max_joint_step_rad": 0.07},
  "hand_eye": {"rms_m": 0.0027, "points": 24},
  "segmentation": {"miou_cnn": 0.912, "miou_hsv_baseline": 0.874, "weights_mb": 1.1, "n_eval_frames": 300},
  "localisation": {"median_err_m": 0.0083},
  "trajectory": {"max_vel_ratio": 0.82, "max_acc_ratio": 0.91, "tracking_rms_m": 0.0021,
                 "torque_within_limit_fraction": 0.996},
  "picks": {"episodes": 50, "pick_ok": 43, "pick_wilson_lo": 0.738, "place_ok": 40,
            "mean_cycle_s": 19.7, "joint_limit_violations": 0},
  "failures": {"slip": 4, "knocked": 3, "place_miss": 3}
}
```

Khi một test thất bại, điều đầu tiên cần đọc là số đo được cạnh ngưỡng; với benchmark hãy mở `failure_taxonomy.json` trước khi đổi bất kỳ code nào.

### Thử thách mở rộng
Với ra ngoài mặt bàn: gắp một hình trụ nằm ngang (gắp bên, 5 DOF) và đo thành công đổi thế nào với 50 lượt có seed nữa; hoặc thêm trường hợp lộn xộn với hai khối chạm nhau và một kiểm tra khoảng hở. Tầng phần cứng thật (tùy chọn): với một SO-101 thật (thiết kế mở, khoảng 130 đến 250 đô la Mỹ mỗi cánh tay tùy bộ kit và khu vực, hãy kiểm tra giá hiện tại) điều khiển qua LeRobot, chép `ik.py` của bạn, ra lệnh đến năm điểm trên bàn và so độ lặp lại với thước trên lưới. Giữ nguồn có cầu chì và giới hạn dòng, giữ tay ngoài vùng làm việc, và không chạy khi không có người. Không điểm nào phụ thuộc vào nó.

### Thực hành với thư viện

Kiểm tra chéo code của bạn với hai thư viện: **Pinocchio** (động học và Jacobian từ URDF của bạn; xem [trang dự án](https://github.com/stack-of-tasks/pinocchio)) và **OpenCV** (mask HSV và thành phần liên thông). Khối dưới đây chỉ chạy được sau `pip install pin opencv-python-headless numpy` và khi `models/corebot.urdf` đã tồn tại.

```python
# Needs: pip install pin opencv-python-headless numpy   (Pinocchio is published on PyPI as "pin")
import cv2
import numpy as np
import pinocchio as pin

# 1. Cross-check your Jacobian and FK against Pinocchio on the URDF you wrote in CAP01.
model = pin.buildModelFromUrdf("models/corebot.urdf")
data = model.createData()
tool = model.getFrameId("tool0")


def pin_tip_and_jacobian(q: np.ndarray):
    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)
    pin.computeJointJacobians(model, data, q)
    J = pin.getFrameJacobian(model, data, tool, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
    return data.oMf[tool].translation.copy(), J[:3, :]          # tip position, 3 x nv linear rows


# 2. A classical colour baseline with OpenCV: HSV threshold plus connected components.
def red_blocks(rgb: np.ndarray, min_pixels: int = 30):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    low = cv2.inRange(hsv, (0, 120, 70), (10, 255, 255))          # red wraps around hue 0
    high = cv2.inRange(hsv, (170, 120, 70), (180, 255, 255))
    mask = cv2.bitwise_or(low, high)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    return [(centroids[i], stats[i, cv2.CC_STAT_AREA]) for i in range(1, n)
            if stats[i, cv2.CC_STAT_AREA] >= min_pixels]


if __name__ == "__main__":
    q = np.zeros(model.nq)
    tip, J = pin_tip_and_jacobian(q)
    print("tip at q = 0:", np.round(tip, 4), "Jacobian shape", J.shape)
    # Compare with your own solver: the tip positions must agree to < 1 mm for 20 random q.
```

So vị trí đầu công cụ và các hàng Jacobian với FK của bạn cho 20 cấu hình ngẫu nhiên (phải khớp dưới 1 mm), và so mIoU baseline HSV của bạn với bản OpenCV. Với đường dẫn cánh tay thật xem [hướng dẫn SO-101 của LeRobot](https://huggingface.co/docs/lerobot/so101).

## Kiểm chứng

Hãy kiểm tra pipeline bằng tay trước khi tin một benchmark. Script thư viện chuẩn dưới đây tái tạo ví dụ có lời giải từ pixel đến góc khớp và các đỉnh quintic; chạy nó và so các hàm của bạn với kết quả.

```python
import math

# 1. pixel + depth -> camera frame (OpenCV optical convention: x right, y down, z forward)
H, W, FOVY = 480, 640, math.radians(60)
fy = (H / 2) / math.tan(FOVY / 2)          # MuJoCo gives fovy; fx = fy for square pixels
fx, cx, cy = fy, W / 2, H / 2
u, v, depth = 352, 236, 0.42
p_cam = ((u - cx) / fx * depth, (v - cy) / fy * depth, depth)

# 2. camera -> base_link with a hand-eye pose: camera at (0.10, 0, 0.35), pitched down 50 deg
th = math.radians(50)
x_ax, y_ax, z_ax = (0, -1, 0), (-math.sin(th), 0, -math.cos(th)), (math.cos(th), 0, -math.sin(th))
t = (0.10, 0.0, 0.35)
p_base = tuple(t[k] + p_cam[0] * x_ax[k] + p_cam[1] * y_ax[k] + p_cam[2] * z_ax[k] for k in range(3))

# 3. base_link -> arm_base (arm pillar 0.17 m ahead of base_link), then pan + planar IK
p_arm = (p_base[0] - 0.17, p_base[1], p_base[2])
pan = math.atan2(p_arm[1], p_arm[0])
r = math.hypot(p_arm[0], p_arm[1])
L1, L2, L3, ZS = 0.116, 0.135, 0.10, 0.05  # illustrative links; read yours from the MJCF


def planar_ik(r, z, sign):
    """Tip at (r, z) pointing straight down; sign = +1 / -1 picks the elbow branch."""
    wr, wz = r, z + L3 - ZS
    c = (wr * wr + wz * wz - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if abs(c) > 1:
        raise ValueError("unreachable")
    q3 = sign * math.acos(c)
    q2 = math.atan2(wz, wr) - math.atan2(L2 * math.sin(q3), L1 + L2 * math.cos(q3))
    return q2, q3


def planar_fk(q2, q3):
    return (L1 * math.cos(q2) + L2 * math.cos(q2 + q3),
            ZS + L1 * math.sin(q2) + L2 * math.sin(q2 + q3) - L3)


LIMIT = math.radians(110)                   # illustrative |wrist_flex| limit; use your MJCF value
for sign in (+1, -1):
    q2, q3 = planar_ik(r, p_arm[2], sign)
    wrist = -math.pi / 2 - (q2 + q3)        # keeps the tool pointing straight down
    ok = abs(wrist) <= LIMIT
    print("branch %+d: shoulder %6.1f elbow %6.1f wrist %7.1f deg  %s" %
          (sign, *(math.degrees(a) for a in (q2, q3, wrist)), "ok" if ok else "wrist limit"))
    if ok:
        best = (q2, q3, wrist)
q2, q3, wrist = best
fk_r, fk_z = planar_fk(q2, q3)

print("p_cam  = (%.4f, %.4f, %.4f) m" % p_cam)
print("p_base = (%.4f, %.4f, %.4f) m" % p_base)
print("p_arm  = (%.4f, %.4f, %.4f) m, r = %.4f m" % (*p_arm, r))
print("chosen: pan %.1f, shoulder %.1f, elbow %.1f, wrist %.1f deg" %
      tuple(math.degrees(a) for a in (pan, q2, q3, wrist)))
print("FK check: r %.5f z %.5f" % (fk_r, fk_z))
assert abs(fk_r - r) < 1e-9 and abs(fk_z - p_arm[2]) < 1e-9

# 4. quintic time scaling: peak speed and acceleration for a move dq in time T
dq, T = 0.8, 1.2
print("quintic peak v %.3f rad/s, peak a %.3f rad/s^2" % (1.875 * dq / T, 5.7735 * dq / T ** 2))
print("one pixel at 0.42 m is %.2f mm" % (depth / fy * 1000))
```

Kỳ vọng: $p_\text{cam}=(0.0323,-0.0040,0.4200)$, $p_\text{base}=(0.3731,-0.0323,0.0309)$, pan $-9.0^\circ$, nhánh $+1$ bị loại vì giới hạn cổ tay, nhánh $-1$ được chấp nhận với vai $52.2^\circ$, khuỷu $-56.8^\circ$, cổ tay $-85.4^\circ$, các đỉnh 1.250 rad/s và 3.208 rad/s$^2$, và một pixel $=1.01$ mm.

Sau đó kiểm chứng hành vi: vẽ tâm đã phát hiện ngược lên ảnh để xem nó có nằm trên khối không; đưa cánh tay đến tư thế pre-grasp với gripper mở và xem một ảnh render; phát lại chậm một lượt thất bại và gán nhãn lý do; xác nhận code nhận thức không bao giờ import truth của simulator (cùng kiểm tra AST như CAP04, áp dụng cho `perception/`).

**Điểm số.** Trọng số CAP05 là 13 trên 100 điểm tốt nghiệp. 60 % điểm cột mốc là tự động (phân số có trọng số của các kiểm tra, cổng: IK và gắp), 40 % là rubric tự đánh giá chấm 0 đến 4: lập luận chiến lược gắp, sơ đồ frame rõ ràng, chất lượng phân tích lỗi (nguyên nhân có dẫn đến cách sửa không?) và vệ sinh huấn luyện CNN (chia theo seed cảnh). Tốt nghiệp cần mọi cổng đạt, mọi cột mốc từ 60 trở lên và tổng có trọng số từ 70 trở lên.

## Lỗi thường gặp

- Dùng bộ đệm độ sâu như mét, hoặc sai dấu một trục trong deprojection: mọi vật nằm ở chỗ có vẻ hợp lý nhưng sai.
- Nội tại sai (dùng fovx cho $f_y$, hoặc bỏ qua tỉ lệ khung hình): sai số vị trí tăng dần về phía mép ảnh.
- Hand-eye được fit và kiểm tra trên cùng các điểm: RMS rất đẹp và robot rất tệ.
- Cánh tay che camera hoặc khối khi tiếp cận: phát hiện mất giữa lúc gắp; hãy phát hiện trước khi di chuyển và giữ lại tư thế.
- Cánh tay 5 bậc bị yêu cầu yaw và pitch tùy ý: hạn chế về từ trên xuống cộng roll, nếu không bộ giải dao động.
- Nhảy nhánh giữa các waypoint: khớp nhảy dữ dội; bắt đầu mỗi lần giải từ waypoint trước.
- Ma sát gripper hoặc `solref` quá mềm hoặc bước thời gian tiếp xúc quá lớn: khối trượt hoặc lún; chỉnh ma sát và bước thời gian, đừng chỉnh bộ điều khiển.
- Đường tiếp cận đẩy khối: dùng pre-grasp cao 8 cm, mở gripper trước.
- Tập huấn luyện và test dùng chung seed: mIoU 0.99 trong log và 0.70 trong benchmark.
- Báo 40/50 là "80 %, đạt" mà không có khoảng tin cậy.

## Phương án khác và đánh đổi

Với nhận thức, **baseline HSV** gần như miễn phí và thường đủ ở đây; **CNN** xử lý thay đổi ánh sáng và texture, còn **detector** huấn luyện sẵn (kiểu YOLO) hoặc mô hình từ vựng mở mở rộng cho nhiều vật hơn, đổi lại tốn tính toán và dataset. Độ sâu có thể đến từ cảm biến RGB-D, cặp stereo hoặc mạng đơn mục tiêu học được; RGB-D trực tiếp nhất trong mô phỏng. Với IK, **giải tích** (dạng đóng cho cánh tay phẳng) nhanh và chính xác nhưng riêng cho từng cánh tay; **damped least squares** tổng quát; IK dựa trên tối ưu hóa (với Pinocchio hoặc các bộ giải dựa trên MuJoCo) xử lý va chạm và độ ưu tiên. Với gắp, gắp song song từ trên xuống đơn giản; **mạng học tư thế gắp** và imitation đầu-cuối (CAP06, ACT trong LeRobot) xử lý cảnh lộn xộn nhưng cần dữ liệu và khó chứng nhận hơn. Xem [chương pick-and-place](https://manipulation.mit.edu/pick.html) của MIT 6.4210 cho cùng pipeline ở quy mô lớn hơn.

## Vận dụng và ghi nhớ

CAP05 chuẩn bị cho CAP06 (kỹ năng học được thay `ScriptedGraspSkill`, cùng giao diện và cùng benchmark), CAP07 (lớp tác vụ truyền nhãn vật và nhận `GraspResult.reason`) và CAP08 (`DETECTION`, `GRASP_SLIP` và `PLACE_MISS` xuất hiện trong taxonomy lỗi của toàn hệ thống). Câu hỏi ôn, trả lời sau một tuần không nhìn ghi chú:

1. Viết phương trình deprojection và nói nó đáp xuống frame nào.
2. Vì sao giả nghịch đảo damped bị chặn gần điểm kỳ dị, và damping tốn gì?
3. Vì sao cánh tay 5 bậc cần pitch chứ không cần đầy đủ hướng, và cái gì đặt roll cổ tay?
4. Cho vận tốc và gia tốc đỉnh của một quintic có độ dài $\Delta q$ và thời lượng $T$.
5. Vì sao tập train và test của phân đoạn phải chia theo seed cảnh?

## Đáp án bài tập

1. $f_y=240/\tan30^\circ=415.7$ px; một pixel ở 0.42 m là $0.42/415.7=1.01$ mm.
2. $X=(400-320)/415.7\cdot0.5=0.0962$ m, $Y=(200-240)/415.7\cdot0.5=-0.0481$ m, $Z=0.5$ m: điểm nằm bên phải và phía trên trục quang.
3. 43/50: [0.738, 0.930]: điểm 86 % và cận dưới 73.8 %: đạt. 40/50: [0.670, 0.888]: điểm 80 % đạt nhưng cận dưới 67.0 % thấp hơn 68 %: trượt.
4. $T\ge1.875\cdot0.6/1.5=0.75$ s từ vận tốc và $T\ge\sqrt{5.7735\cdot0.6/4}=0.931$ s từ gia tốc. Giới hạn gia tốc ràng buộc: 0.931 s.
5. Giả nghịch đảo: hướng thứ hai cho $0.1/0.01=10$ rad, một bước vô lý. Damped: $0.01/(0.01^2+0.1^2)\cdot0.1=0.099$ rad, còn hướng điều kiện tốt cho $1/(1+0.01)\cdot0.1=0.099$ rad. Cái giá là hướng thứ hai không được sửa chính xác trong một bước (cần vài vòng lặp).
6. Nền $9400/9800=0.959$; đỏ $320/420=0.762$; xanh dương $280/340=0.824$; mIoU $=0.848$, chỉ dưới 0.85: trượt. Đỏ là lớp yếu; hãy xem các false negative của nó (bóng, vùng sáng chói).
7. $\tau_\text{static}=9.81\,(0.15\cdot0.07+0.12\cdot0.19+0.08\cdot0.28)=9.81\cdot0.0557=0.546$ N m; động $0.012\cdot3.2=0.038$ N m; tổng $\approx0.585$ N m, khoảng 58 % của giới hạn 1.0 N m. Duỗi cánh tay hoặc mang vật nặng hơn nhanh chóng ăn hết biên.
8. Một độ lệch ổn định tăng theo khoảng cách ngang chỉ đến (1) phép quay hand-eye hoặc yaw camera (sai quay nhỏ làm lệch vật xa nhiều hơn): fit lại với các điểm trải khắp bàn; (2) điểm chính (principal point) hoặc $f_x$ (kiểm tra deprojection ở mép ảnh); (3) offset không của khớp pan hoặc dấu của pan trong FK. Kiểm thử với điểm giữ lại ở mép trái, rồi deproject một điểm đã biết, rồi ra lệnh cánh tay đến một điểm đã biết trong frame đế mà không dùng camera.
9. Jaws khép qua cạnh ngắn nếu roll bù pan: $\text{roll}=\text{wrap}_{180}(100^\circ-(-9^\circ))=109^\circ-180^\circ=-71^\circ$, nằm trong $[-90^\circ,90^\circ)$. Gripper đối xứng nhìn như nhau sau 180 độ, nên rút gọn modulo 180 cho phép quay nhỏ nhất và giữ khớp xa giới hạn.
10. Một đáp án tốt liệt kê seed, số đếm theo loại taxonomy (cộng đúng bằng số thất bại), một cách sửa gắn với loại lớn nhất (ví dụ slip thì tăng ma sát hoặc khép chậm hơn), thành công baseline trên 95 % ở giữa bàn, một trường hợp biên thất bại với lý do `ik_fail` hoặc `joint_limit` thay vì sập, và một quan sát bác bỏ pipeline (thành công giảm khi đổi texture, chỉ ra phân đoạn bị overfit).

## Đọc thêm

- [MIT 6.4210 Robotic Manipulation: Basic pick and place](https://manipulation.mit.edu/pick.html) và [Kinematics and Jacobians](https://manipulation.mit.edu/robot.html): cùng pipeline ở bối cảnh lớn hơn.
- [Tài liệu MuJoCo: modeling](https://mujoco.readthedocs.io/en/stable/modeling.html) và [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie): camera, bộ đệm phân đoạn, mô hình SO-101 và các file giấy phép của nó.
- [CS231n](https://cs231n.github.io/): huấn luyện CNN nhỏ và tránh rò rỉ dữ liệu.
- [Pinhole camera model (Wikipedia)](https://en.wikipedia.org/wiki/Pinhole_camera_model) và [Inverse kinematics (Wikipedia)](https://en.wikipedia.org/wiki/Inverse_kinematics): công thức tham chiếu.
- [Pinocchio](https://github.com/stack-of-tasks/pinocchio) và [hướng dẫn SO-101 của LeRobot](https://huggingface.co/docs/lerobot/so101): nhánh thư viện và tầng phần cứng tùy chọn; [thiết kế mở SO-ARM100/101](https://github.com/TheRobotStudio/SO-ARM100).
- **Luyện thêm:** xem bài giảng MIT 6.4210 "Basic pick and place (Part 1)" và Modern Robotics Chương 6 về động học ngược số, rồi tái tạo sơ đồ frame gắp cho cánh tay của bạn.
