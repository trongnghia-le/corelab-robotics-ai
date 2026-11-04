---
{"title": "Nền tảng capstone: spec, repository, mô hình robot và thế giới có seed", "summary": "Bắt đầu capstone CoreBot Tidy: viết spec đo lường được, tạo repository tái lập được, mô hình hóa base vi sai cùng tay SO-101 trong MuJoCo và URDF, và chứng minh bằng acceptance test rằng tính tất định, động học và độ ổn định khi nghỉ đều đạt.", "objectives": ["Viết một spec đo lường và bác bỏ được, trong đó mỗi yêu cầu có metric, ngưỡng kèm lý do và test kiểm tra nó.", "Tạo repository tái lập được (phiên bản được ghim, make test, API môi trường có seed) từ script skeleton dùng chung.", "Mô hình hóa base vi sai, tay SO-101 và các cảm biến trong MJCF, phản chiếu trong URDF và kiểm tra tên, giới hạn và khối lượng khớp nhau.", "Cho thấy forward kinematics của bạn, MuJoCo và URDF đặt tool trong phạm vi 1 mm của nhau.", "Đánh giá tỉ lệ thành công bằng cận dưới Wilson và giải thích rubric tốt nghiệp cùng timeline của capstone."]}
---

## Vì sao điều này quan trọng

Bạn đã học xong tài liệu của khóa; giờ bạn xây một robot dùng tất cả. **CoreBot Tidy** là một mobile manipulator nhỏ trong một "phòng lab" MuJoCo: bạn gõ "put the red block in the blue bin" và robot phân tích câu, tự định vị, lái tới bàn, tìm khối bằng camera, gắp bằng tay 5 bậc tự do, lái tới thùng và đặt vào, trong khi một safety supervisor có thể dừng mọi thứ. Ý tưởng theo các dự án tham chiếu như [TidyBot](https://arxiv.org/abs/2305.05658) của Stanford và pipeline pick-and-place của [MIT 6.4210](https://manipulation.mit.edu/).

Chín milestone (CAP01 đến CAP09, khoảng 240 giờ, khoảng 24 tuần với 10 giờ mỗi tuần) xây nó theo từng lớp. Milestone đầu là nền móng, và cố ý thiên về kỷ luật hơn là robotics: một spec đo lường được, một repository tái lập được, một mô hình mà ba mô tả của nó khớp nhau, và các test thất bại khi có gì đó trôi đi. Các dự án như thế này hiếm khi chết vì một thuật toán khó. Chúng chết vì không ai biết thay đổi hôm qua có làm hỏng gì không, hay "chạy được" có nghĩa gì không. CAP01 đưa cho bạn công cụ để biết.

Giọng điệu của capstone: hãy coi nó như bản brief dự án từ một kỹ sư senior luôn ủng hộ bạn. Mỗi milestone nói rõ nó dùng các topic CoreLab nào trước đó, để bạn quay lại đọc lại. Milestone này dùng [S02 MuJoCo](/lessons/S02), [S04 Robot Description](/lessons/S04), [R04 Forward Kinematics](/lessons/R04), [T04 Software Testing](/lessons/T04), [T05 Reproducible Environments](/lessons/T05) và [RS02 Experimental Design](/lessons/RS02).

## Trực giác

Hãy hình dung capstone là một chồng năm lớp cùng giao tiếp qua một tệp hợp đồng nhỏ. Dưới cùng là thế giới mô phỏng (vật lý 1 ms, có seed). Phía trên là firmware-in-the-loop cho base (CAP02), rồi ước lượng và nhận thức phía host (CAP03, CAP05), các kỹ năng như điều hướng, thao tác và policy học được (CAP04 đến CAP06), và lớp task với ngôn ngữ và an toàn (CAP07). CAP08 đánh giá mọi thứ trên các episode có seed; CAP09 biến bằng chứng thành báo cáo và bản phát hành.

![Kiến trúc hệ thống CoreBot Tidy: năm băng từ thế giới MuJoCo ở dưới qua firmware in the loop, ước lượng và nhận thức phía host, và các kỹ năng, tới lớp task, với safety supervisor bên phải và evaluation harness bên dưới](/lesson-figures/CAP-architecture.svg)

*Bản đồ chung cho cả chín milestone. CAP01 xây băng dưới cùng và bộ khung test mà mọi băng sau đó đều được kiểm tra bằng.*

Điều CAP01 thêm vào là phần dễ bị bỏ qua: **mô hình thế giới** (robot được mô tả trong MJCF và URDF, cảnh được sinh từ một seed) và **spec** (định nghĩa "chạy đúng" bằng con số). Hai ý tưởng mang cả milestone.

1. *Một khẳng định không có test chỉ là hy vọng.* Mỗi yêu cầu trong `SPEC.md` nêu một metric, một ngưỡng, lý do một dòng cho ngưỡng và hàm test có thể bác bỏ nó.
2. *Ba mô tả của một robot phải khớp nhau.* Forward kinematics của bạn, mô hình MuJoCo và URDF đều nói tool ở đâu. Nếu chúng lệch nhau hơn một milimet thì một trong số đó sai, và mọi milestone sau sẽ thừa hưởng lỗi một cách âm thầm.

## Lý thuyết và suy dẫn

Phần này là "ghi chú tích hợp" của milestone: vài công thức, interface và quy tắc quan trọng ở đây, mỗi cái kèm liên kết về topic gốc.

![Tổng quan CAP01: SPEC.md nuôi một môi trường có seed và các acceptance test; forward kinematics của bạn, MJCF trong MuJoCo và URDF phải khớp trong 1 mm; các gate check là tính tất định và forward kinematics](/lesson-figures/CAP01.svg)

### 1. Spec là bảng các khẳng định bác bỏ được (từ RS02, T04)

[RS02](/lessons/RS02) dạy rằng một khẳng định chỉ hữu ích nếu một quan sát có thể bác bỏ nó. Vì vậy một hàng yêu cầu có sáu ô: id, yêu cầu, metric, ngưỡng, lý do, test. "Robot chính xác" không có ô nào được điền. "Forward kinematics của bạn đặt `tool0` trong 1 mm so với MuJoCo cho 20 cấu hình khớp ngẫu nhiên" có đủ. Lý do quan trọng vì ngưỡng là các quyết định: chọn 1 mm vì một lần gắp sau này chịu được khoảng 5 mm, và ngân sách sai số 5 mm không nên bị mô hình ăn mất.

Với tỉ lệ thành công đo trên $n$ episode độc lập có $k$ lần thành công, hãy báo cáo **khoảng Wilson** thay vì $k/n$. Với $\hat p=k/n$ và $z=1.96$ cho 95 %:
$$\frac{\hat p+\frac{z^2}{2n}\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}.$$
Các acceptance test sau này trong capstone kiểm tra cận *dưới*. Hàm `evalkit.wilson_interval(k, n)` cài đặt nó, với `wilson_interval(78, 100)` cho khoảng (0.689, 0.850).

### 2. Tính tái lập là hàm của seed (từ T05, S02)

Một lần chạy có seed phải là hàm thuần của seed: cùng seed, cùng cảnh, cùng `qpos` sau cùng các hành động ([T05](/lessons/T05)). Quy tắc trong repository này là **mọi ngẫu nhiên đến từ `np.random.default_rng(seed)`**; không bao giờ `np.random.rand`, không bao giờ `random.random`, không bao giờ thời gian hay thứ tự của một set. Một scene hash (SHA-256 của các tư thế vật thể đã làm tròn) cho phép test nhận ra cảnh bị đổi mà không cần so từng số thực. Kết quả dấu phẩy động có thể khác giữa các CPU và bản BLAS, nên tính tất định được kiểm tra ở dung sai $10^{-9}$ trên một máy và được ghi lại; giữa các máy bạn so với dung sai, không so hash. Vòng lặp của MuJoCo là `mj_step` lặp lại trên cùng một `MjData` ([simulation loop](https://mujoco.readthedocs.io/en/stable/programming/simulation.html)); `mj_resetData` cộng với việc đặt vật thể có seed của bạn là một lần reset đầy đủ.

### 3. Một robot, hai tệp: MJCF và URDF (từ S04, S02)

MJCF là định dạng của MuJoCo và mang vật lý: quán tính, contact, actuator, camera. URDF ([hướng dẫn ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html)) là thứ ROS 2, `robot_state_publisher` và nhiều thư viện kinematics đọc. Bạn viết cả hai và kiểm tra chúng với nhau về **tên khớp, giới hạn khớp (dung sai $10^{-6}$ rad) và tổng khối lượng (trong 2 %)**. Hai cái bẫy làm người mới mất nhiều ngày:

- Góc trong MJCF **mặc định là độ** (`<compiler angle="degree"/>`), góc trong URDF luôn là radian. Giới hạn `range="-110 110"` là 1.92 rad.
- Quán tính suy từ mesh có thể vô nghĩa (ví dụ một vỏ rỗng bị coi là đặc); hãy dùng hình học nguyên thủy hoặc giá trị `<inertial>` tường minh và ghi nguồn.

Các frame cố định cho cả capstone: `map` (góc phòng), `odom`, `base_link`, `camera_link`, `arm_base`, `tool0`.

### 4. Forward kinematics và 1 mm nghĩa là gì (từ R04)

FK của bạn là tích các phép biến đổi đồng nhất từ `arm_base` tới `tool0`:
$$T_{\text{tool}}(q)=\prod_{i=1}^{n}\underbrace{T_i^{\text{fixed}}\,\mathrm{Rot}(\hat a_i,q_i)}_{\text{một khớp}},\qquad p=T_{\text{tool}}[0\!:\!3,\,3].$$
Mọi offset cố định và trục được chép từ MJCF của bạn. Sai số góc khớp hoặc offset $\Delta\theta$ làm tool lệch khoảng $L\,\Delta\theta$ với $L$ là khoảng cách từ khớp đó tới tool. Với $L=0.3$ m, 1 mm ứng với $\Delta\theta=0.0033$ rad $=0.19^\circ$, nên test 1 mm bắt được dấu trục bị đảo hay lỗi độ-thay-radian (gây ra hàng cm hoặc hơn) nhưng chấp nhận sai số làm tròn.

### 5. Tệp hợp đồng `interfaces.py` (phong cách S06)

Các module không bao giờ truyền tuple rời. Chúng trao đổi các dataclass bất biến (frozen) theo đơn vị SI với một `stamp` tính bằng giây:

| Dataclass | Ý nghĩa | Ánh xạ ROS 2 |
|---|---|---|
| `WheelCmd(stamp, v, w)` | tốc độ ra lệnh (m/s, rad/s) | `geometry_msgs/Twist` |
| `WheelState(stamp, left_counts, right_counts, status)` | số đếm encoder uint16, có wrap | frame firmware, rồi `/joint_states` |
| `OdomSample`, `ImuSample`, `ScanSample`, `ImageFrame` | cảm biến sau driver | `nav_msgs/Odometry`, `sensor_msgs/*` |
| `Pose2DCov(stamp, x, y, theta, P)` | ước lượng kèm hiệp phương sai | pose kèm covariance |
| `GraspGoal`, `NavGoal`, `TaskGoal`, `SafetyState` | message kỹ năng và task | action và topic |

Frozen nghĩa là module phía sau không thể sửa cái module phía trước đã phát, nên mọi thay đổi trạng thái đều tường minh. Đây là cùng kỷ luật với [S06](/lessons/S06) (đơn vị và độ mới ở interface).

### 6. Bước thời gian, trạng thái nghỉ và contact (từ S02)

Với bước vật lý 1 ms, 5 giây nghỉ là 5000 bước. Trong MuJoCo, một contact có `dist` âm là đang xuyên vào nhau; test nghỉ ghi lại giá trị $-\text{dist}$ lớn nhất và giới hạn nó ở 2 mm. Ma sát bánh xe quá cao hoặc quá thấp, hoặc bước thời gian quá lớn so với contact cứng, lộ ra ở đây dưới dạng trôi hoặc rung trước khi chúng kịp làm hỏng điều hướng.

### Chấm điểm, tốt nghiệp và timeline

Mỗi milestone được 0 đến 100 điểm: **60 % kiểm tra tự động** (tỉ lệ có trọng số các check đạt; hai hoặc ba check mỗi milestone là **gate**) cộng **40 % rubric của con người** (bốn hoặc năm tiêu chí chấm 0 đến 4 kèm bằng chứng liên kết: 0 thiếu, 2 chạy được nhưng chưa giải thích, 4 có biện minh, có test và có phê bình). Trọng số cộng lại bằng 100:

| CAP01 | CAP02 | CAP03 | CAP04 | CAP05 | CAP06 | CAP07 | CAP08 | CAP09 |
|---|---|---|---|---|---|---|---|---|
| 8 | 12 | 12 | 11 | 13 | 12 | 10 | 14 | 8 |

Bạn **tốt nghiệp** khi tất cả điều sau đúng: mọi gate của mọi milestone đạt; mọi milestone đạt ít nhất 60; tổng có trọng số ít nhất 70; CAP08 không có vi phạm an toàn nào; bài smoke test tái lập của CAP09 đạt trên một checkout sạch. Merit là tổng từ 80; Distinction là từ 90 cộng một stretch goal. Tầng phần cứng tùy chọn không bao giờ thay thế một gate đang thất bại. Mọi ngưỡng trong capstone là giá trị đầu tiên và sẽ được hiệu chỉnh lại theo các lần chạy tham chiếu.

| Tuần | Milestone | Giờ |
|---|---|---|
| 1-2 | CAP01 nền tảng | 22 |
| 3-5 | CAP02 base firmware-in-the-loop | 28 |
| 6-8 | CAP03 ước lượng và định vị | 26 |
| 9-11 | CAP04 lập bản đồ, lập kế hoạch, điều hướng | 26 |
| 12-14 | CAP05 thao tác (có thể chồng với CAP04) | 30 |
| 15-18 | CAP06 kỹ năng học được | 32 |
| 19-21 | CAP07 lớp task và an toàn | 26 |
| 22-24 | CAP08 tích hợp và đánh giá, CAP09 báo cáo | 34 + 16 |

## Ví dụ có lời giải

Đây là một vết tham chiếu cho thấy một CAP01 đạt trông như thế nào. Mọi con số đều là giá trị minh họa (illustrative values) được chọn cho nhất quán với các công thức, không phải đầu ra của một lần chạy thật; của bạn sẽ khác ở các chữ số cuối và bạn nên đối chiếu với ngưỡng, không phải với các chữ số này.

**1. Một spec kiểm tra được.** Mười yêu cầu, mỗi yêu cầu gắn với một test (SR8 đến SR10 nằm trong unit test của bạn):

```markdown
| id   | requirement                              | metric                          | threshold | rationale                                    | test |
|------|------------------------------------------|---------------------------------|-----------|----------------------------------------------|------|
| SR1  | A seeded run is reproducible             | max abs qpos difference         | < 1e-9    | same machine and binary: expect exactly 0    | tests/acceptance/test_cap01.py::test_determinism |
| SR2  | Own FK equals the simulator              | tool position error, 20 configs | < 1 mm    | grasp tolerance is about 5 mm                | tests/acceptance/test_cap01.py::test_fk_matches_mujoco |
| SR3  | URDF and MJCF describe one robot         | joint-limit diff, mass diff     | 1e-6, 2 % | float round-trip, inertia rounding           | tests/acceptance/test_cap01.py::test_urdf_mjcf_consistency |
| SR4  | The robot rests when told nothing        | drift in 5 s, penetration       | 2 mm, 0.5 deg, 2 mm | below one pixel of later camera noise | tests/acceptance/test_cap01.py::test_rest_stability |
| SR5  | The table is inside the arm workspace    | reachable fraction of 100 points| >= 95 %   | validates the scale decision of the model    | tests/acceptance/test_cap01.py::test_reachability |
| SR6  | Every requirement is traceable           | SR ids with an existing test    | >= 8      | a spec nobody can check is decoration        | tests/acceptance/test_cap01.py::test_spec_traceability |
| SR7  | The repo has fast tests and pinned deps  | unit tests, pins                | >= 15, yes| CAP02 onward needs a safety net              | tests/acceptance/test_cap01.py::test_repo_hygiene |
| SR8  | Scenes are a function of the seed        | equal scene hash for equal seed | equal     | later benchmarks compare seeds               | tests/unit/test_world.py::test_scene_is_seeded |
| SR9  | Messages are immutable                   | assignment raises               | raises    | no module may edit another module's data     | tests/unit/test_interfaces.py::test_frozen |
| SR10 | Units are SI and documented              | every field doc names its unit  | all       | CAP02 mixes counts, rad and m/s              | tests/unit/test_interfaces.py::test_units_documented |
```

**2. Forward kinematics bằng tay.** Một tay minh họa: đỉnh trụ cao 0.05 m so với mặt phẳng base, độ dài link 0.12, 0.14 và 0.10 m (duỗi thẳng, với tầm với ngang 0.36 m, đó là lý do bàn phải thấp và gần). Góc tính bằng radian, góc nâng vai đo từ phương thẳng đứng.

```python
import math

# Illustrative arm (not SO-101 data): pillar top 0.05 m above the base plane, link lengths in metres.
L1, L2, L3, Z0 = 0.12, 0.14, 0.10, 0.05

def fk(pan, lift, elbow, wrist):
    """Tool position (x, y, z) in arm_base. Angles in radians, lift measured from vertical."""
    a1, a2, a3 = lift, lift + elbow, lift + elbow + wrist
    r = L1 * math.sin(a1) + L2 * math.sin(a2) + L3 * math.sin(a3)   # horizontal reach
    z = Z0 + L1 * math.cos(a1) + L2 * math.cos(a2) + L3 * math.cos(a3)
    return r * math.cos(pan), r * math.sin(pan), z

p = fk(0.4, 0.6, 0.9, -1.5)
print("tool0 in arm_base: x=%.4f y=%.4f z=%.4f" % p)

# What a unit slip does: the same four numbers read as degrees instead of radians.
bad = fk(math.radians(0.4), math.radians(0.6), math.radians(0.9), math.radians(-1.5))
print("angles treated as degrees: error = %.1f mm" % (1000 * math.dist(p, bad)))

# Reach limit: fully stretched (all angles 0 means straight up, so use lift = 90 degrees).
print("max horizontal reach = %.2f m" % (L1 + L2 + L3))
```

Đầu ra:

```text
tool0 in arm_base: x=0.1910 y=0.0808 z=0.2589
angles treated as degrees: error = 252.9 mm
max horizontal reach = 0.36 m
```

Nếu sau đó trình mô phỏng đọc được $(0.1911, 0.0807, 0.2590)$ cho `tool0` thì sai số là $\sqrt{0.1^2+0.1^2+0.1^2}\ \text{mm}=0.17$ mm: đạt so với ngưỡng 1 mm. Coi cùng bốn số đó là độ làm tool lệch khoảng 253 mm, đúng là lỗi mà test được tạo ra để bắt.

**3. Tính tất định.** Hai lần chạy `reset(seed=7)` cộng 500 bước theo kịch bản (0.5 s thời gian mô phỏng với 1 ms) cho cùng scene hash và $|q_1-q_2|$ lớn nhất bằng 0.0 (ngưỡng $10^{-9}$).

**4. Khả năng với tới.** Lấy mẫu đều các điểm trên bàn và hỏi tool có đặt được ở đó không. Với mô hình hình vành khăn minh họa (khoảng cách ngang từ 0.12 đến 0.33 m tính từ đế tay), một bàn trải từ 0.18 đến 0.32 m phía trước và rộng 0.24 m là đạt; đẩy cùng bàn đó ra xa thêm 0.07 m thì thất bại nặng:

```python
import math
import random

# Illustrative annulus model of a top-down reach: the tool can be placed where the horizontal
# distance r from the arm base is between R_MIN and R_MAX (numbers are illustrative, not SO-101 data).
R_MIN, R_MAX = 0.12, 0.33
rng = random.Random(1)

def fraction(x_lo, x_hi, y_half, n=100_000):
    ok = 0
    for _ in range(n):
        x, y = rng.uniform(x_lo, x_hi), rng.uniform(-y_half, y_half)
        ok += R_MIN <= math.hypot(x, y) <= R_MAX
    return ok / n

print("table 0.18..0.32 m ahead, +-0.12 m wide:", round(fraction(0.18, 0.32, 0.12), 3))
print("table 0.25..0.45 m ahead, +-0.12 m wide:", round(fraction(0.25, 0.45, 0.12), 3))
```

```text
table 0.18..0.32 m ahead, +-0.12 m wide: 0.986
table 0.25..0.45 m ahead, +-0.12 m wide: 0.363
```

98.6 % vượt gate 95 %; 36.3 % cho biết tỉ lệ mô hình sai, không phải code. Đây là "kiểm tra kích thước" của milestone: SO-101 chỉ với tới khoảng 0.35 đến 0.4 m, nên bạn gắn nó trên một trụ ngắn và dùng bàn và thùng thấp.

**5. Truy vết.** Một yêu cầu không có tên test thì không truy vết được; bộ phân tích tìm ra nó:

```python
import re

SPEC = """| id | requirement | metric | threshold | rationale | test |
|----|-------------|--------|-----------|-----------|------|
| SR1 | Same seed gives same run | max abs qpos diff | < 1e-9 | same binary, same machine | tests/acceptance/test_cap01.py::test_determinism |
| SR2 | Own FK matches MuJoCo | tool position error | < 1 mm | grasp tolerance is ~5 mm | tests/acceptance/test_cap01.py::test_fk_matches_mujoco |
| SR3 | The robot is accurate | (vague) | (none) | | |
"""

def parse(text):
    """Return {id: [cited test names]} for every table row that starts with an SR id."""
    rows = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*(SR\d+)\s*\|", line)
        if m:
            rows[m.group(1)] = re.findall(r"::(test_\w+)", line)
    return rows

rows = parse(SPEC)
print(rows)
untraceable = sorted(k for k, v in rows.items() if not v)
print("untraceable:", untraceable)
assert untraceable == ["SR3"]
```

```text
{'SR1': ['test_determinism'], 'SR2': ['test_fk_matches_mujoco'], 'SR3': []}
untraceable: ['SR3']
```

**6. Tệp metrics** sau một lần chạy đạt (`runs/cap01/metrics.json`, giá trị minh họa):

```json
{
  "determinism_max_abs_diff": 0.0,
  "fk_max_error_m": 0.00012,
  "mass_rel_diff": 0.004,
  "reachable_fraction": 0.97,
  "rest_arm_drift_deg": 0.02,
  "rest_base_drift_m": 0.0003,
  "rest_max_penetration_m": 0.0005,
  "spec_requirements": 10,
  "unit_tests": 17
}
```

**7. Một tỉ lệ thành công, cho sau này.** Nếu một test sau này báo 27 thành công trong 30 episode, ước lượng điểm là 0.90 nhưng khoảng Wilson 95 % là (0.744, 0.965): một yêu cầu cận dưới 0.75 sẽ vừa đủ thất bại.

## Bài tập

1. **(Easy)** Một tập episode có 27 thành công trong 30. Tính khoảng Wilson 95 % bằng `evalkit.wilson_interval` và quyết định test "cận dưới ít nhất 0.75" có đạt không. *(Nguồn: Wikipedia, Binomial proportion confidence interval.)*
2. **(Easy)** Viết lại "robot nên chính xác và không lắc khi nghỉ" thành hai hàng SPEC.md, mỗi hàng có metric, ngưỡng, lý do một dòng và tên test. *(Nguồn: định dạng SR của bài này; RS02.)*
3. **(Easy)** Một khớp được viết `<joint name="elbow_flex" type="hinge" range="-110 110"/>` trong MJCF không có thẻ `<compiler>`. Dải đó theo radian là bao nhiêu? `lower` và `upper` của URDF phải là bao nhiêu? Điều gì xảy ra nếu bạn viết `range="0 1.57"` và mong đợi radian? *(Nguồn: tài liệu MuJoCo modeling, thuộc tính `angle` của compiler.)*
4. **(Medium)** Bước vật lý là 1 ms. 5 s nghỉ là bao nhiêu bước? 500 bước theo kịch bản của test tất định là bao nhiêu giây? Điều gì đổi nếu bạn đặt bước 2 ms và giữ 500 bước? *(Nguồn: MuJoCo simulation loop.)*
5. **(Medium)** Khoảng cách từ cổ tay tới tool là 0.1 m và từ vai tới tool là 0.36 m. Sai số góc khớp (độ) nào làm tool lệch 1 mm với mỗi khớp? Vì sao điều đó biện minh cho việc test FK trên các cấu hình ngẫu nhiên thay vì chỉ ở tư thế zero? *(Nguồn: công thức bài R04.)*
6. **(Medium)** `test_urdf_mjcf_consistency` báo tổng khối lượng 3.18 kg trong MJCF và 3.10 kg trong URDF. Tính chênh lệch tương đối, nói test có đạt ở mức 2 % không, và nêu hai nguyên nhân khả dĩ. *(Nguồn: bài S04, `<inertial>` của URDF.)*
7. **(Medium)** Trong `test_reachability`, 91 trong 100 điểm bàn với tới được. Tính khoảng Wilson, nói test ước lượng điểm 95 % có đạt không, và nêu hai thay đổi thiết kế làm tăng tỉ lệ mà không đụng vào test. Hãy chạy trước đoạn mã kiểm tra tầm với ở bước 4 của Ví dụ mẫu (lưu thành `reach_demo.py`) để thấy vị trí bàn quan trọng đến mức nào. *(Nguồn: bài này, mục 4 và tầm với của SO-101 được nêu ở trên.)*
8. **(Hard)** *Tìm lỗi.* Code cảnh làm `import random; random.shuffle(objs)` để đặt vật thể và `np.random.rand()` cho vị trí thùng, và `reset(seed)` gọi `np.random.seed(seed)`. Hai lần chạy giống hệt cho cùng qpos, nhưng cùng seed trên máy của đồng nghiệp cho cảnh khác. Giải thích mọi khiếm khuyết và viết bản sửa chỉ dùng `np.random.default_rng(seed)`. *(Nguồn: T05; hướng dẫn NumPy Generator.)*
9. **(Hard)** *Thiết kế.* Thiết kế test độ ổn định khi nghỉ sao cho nó không thể đạt do ngẫu nhiên. Bạn ghi những đại lượng nào, ở bước nào, với ngưỡng nào, và vì sao chỉ kiểm tra trạng thái cuối là chưa đủ? Bao gồm cách MuJoCo báo độ xuyên (`mjContact.dist`). *(Nguồn: tài liệu MuJoCo programming, contacts.)*
10. **(Hard, mini-project)** Viết SPEC.md hoàn chỉnh cho robot của riêng bạn: mười yêu cầu, lý do cho mỗi ngưỡng và một tên test cho mỗi yêu cầu. Sau đó viết một bộ kiểm tra mười dòng từ chối spec có metric thiếu, ngưỡng thiếu hoặc test không truy vết được, và cho thấy nó từ chối một hàng cố ý làm hỏng. Nêu quan sát nào sẽ khiến bạn đổi một ngưỡng.

## Cài đặt tham khảo

Module bạn viết đầu tiên là forward kinematics của riêng bạn. Dưới đây là skeleton: docstring, type hint và `NotImplementedError`. Hãy viết các phép biến đổi từ MJCF của bạn; không có lời giải ẩn nào ở đây vì các con số là của bạn.

```python
"""src/corebot/manipulation/kinematics.py: your own forward kinematics of the arm (CAP01).

Frames: positions are expressed in the `arm_base` frame, metres, radians, right-handed,
z up. `q` lists the arm joints in the order of ARM_JOINTS (gripper excluded).
"""
from typing import Sequence

import numpy as np

ARM_JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


def rot_x(a: float) -> np.ndarray:
    """4x4 homogeneous rotation about x by `a` radians."""
    raise NotImplementedError


def rot_z(a: float) -> np.ndarray:
    """4x4 homogeneous rotation about z by `a` radians."""
    raise NotImplementedError


def trans(x: float, y: float, z: float) -> np.ndarray:
    """4x4 homogeneous translation."""
    raise NotImplementedError


def fk_pose(q: Sequence[float]) -> np.ndarray:
    """4x4 pose of site `tool0` in `arm_base` for joint angles q (product of transforms).

    Every offset and axis here must be copied from your MJCF `<body pos=... >` and
    `<joint axis=... >` values; write the source line numbers in comments.
    """
    raise NotImplementedError


def fk(q: Sequence[float]) -> np.ndarray:
    """Position (3,) of `tool0` in `arm_base`: the last column of fk_pose."""
    return fk_pose(q)[:3, 3]


def top_down_reachable(p_base: Sequence[float]) -> bool:
    """True if a top-down gripper pose exists at position p_base (m) inside joint limits.

    Start with a sampled search over q using fk(); replace it by closed-form IK in CAP05.
    """
    raise NotImplementedError
```

Gợi ý cho thân hàm `fk_pose`: lặp qua các khớp, nhân `trans(offset)` rồi một phép quay quanh trục khớp theo `q[i]`, và kết thúc bằng phép biến đổi cố định từ link cuối tới site `tool0`. Ghi vào comment dòng MJCF mà bạn chép từng offset.

## Thực hành độc lập

### Mục tiêu
Giao nền móng của CoreBot Tidy: một repository từ script skeleton, một `SPEC.md` đo lường được, một mô hình MJCF và một URDF của cùng robot, một môi trường có seed với API `reset(seed)` và `step`, forward kinematics của riêng bạn, ít nhất 15 unit test nhanh, và một bộ acceptance đạt và ghi `runs/cap01/metrics.json`. Ngân sách: khoảng 22 giờ (bài này là bản brief).

### Thiết lập
Làm việc trong một **repository riêng**, `~/corebot-capstone`, không bao giờ bên trong `corelab/`. Cần Python 3.10 trở lên, `git`, và sau này `gcc` và `cmake` (CAP02). Gợi ý runtime: `MUJOCO_GL=egl` để render trên máy có GPU, `osmesa` làm phương án chậm (CAP05 cần, CAP01 không cần). Hãy ghim đúng các phiên bản bạn đã test (các lệnh in chúng bằng `pip freeze`; MuJoCo và công cụ của nó đổi nhanh, nên một bản ghim bằng văn bản là một phần của điểm).

Tải `evalkit.py` (các helper dùng chung: khoảng Wilson, step metrics, CRC-8, NEES consistency, McNemar, bootstrap) và `make_skeleton.sh` từ ứng dụng CoreLab tại `/practice/capstone/evalkit.py` và `/practice/capstone/make_skeleton.sh`, rồi:

```bash
mkdir -p ~/corelab-downloads && cd ~/corelab-downloads
# replace HOST:PORT with the address of your running CoreLab app
curl -O http://HOST:PORT/practice/capstone/evalkit.py
curl -O http://HOST:PORT/practice/capstone/make_skeleton.sh
python3 evalkit.py                                   # prints: evalkit self-test OK
sh make_skeleton.sh ~/corebot-capstone ./evalkit.py  # safe to run twice; never overwrites
cd ~/corebot-capstone && git init
python3 -m venv .venv && . .venv/bin/activate
pip install mujoco numpy pytest yourdfpy
pip freeze | grep -i -E "^(mujoco|numpy|pytest|yourdfpy)=="   # paste these lines into pyproject.toml
make doctor && make test
```

Script tạo bố cục của kế hoạch (`configs/`, `models/`, `firmware/`, `src/corebot/...`, `tests/unit`, `tests/acceptance`, `bench/`, `runs/`, `report/`, `docs/`) với các stub, và bỏ qua mọi tệp đã tồn tại. Với tay SO-101, hãy chép `robotstudio_so101` từ [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) vào `models/meshes/` **cùng với tệp license của nó**; ghi lại commit bạn đã chép.

### Nhiệm vụ
1. Viết `SPEC.md` với các id yêu cầu SR1 đến SR10 (cột id, yêu cầu, metric, ngưỡng, lý do, test). Ví dụ trong Ví dụ có lời giải là khuôn mẫu, không phải đáp án: hãy thêm các yêu cầu phản ánh thiết kế của riêng bạn (ví dụ chiều cao bàn bạn chọn).
2. Viết `models/corebot.xml`: base vi sai (hai bánh dẫn động cộng bánh phụ hoặc skid), một trụ ngắn, tay SO-101 kèm gripper, một bàn thấp, ba vật thể có màu, hai thùng, và các cảm biến (encoder bánh, IMU, tia lidar, RGB-D, encoder khớp). Các site `tool0`, body `base_link` và `arm_base`. Ghi chú mọi đơn vị và lựa chọn `angle` của compiler trong comment.
3. Viết `models/corebot.urdf` với cùng tên khớp và giới hạn cho base và tay.
4. Cài `corebot/sim/world.py` và `corebot/sim/env.py`: `Env.reset(seed)`, `Env.step(ctrl)`, `Env.scene_hash()`; nguồn ngẫu nhiên duy nhất là `np.random.default_rng(seed)`.
5. Cài `manipulation/kinematics.py` (`fk`, `top_down_reachable`).
6. Cài `interfaces.py` (dataclass frozen với đơn vị được ghi tài liệu) và viết ít nhất 15 unit test trong `tests/unit`, gồm ba test được SR8 đến SR10 trích dẫn.
7. Cho target Makefile `make test` chạy các unit test; thêm tệp acceptance bên dưới; làm `pytest -q tests/acceptance` đạt; commit `runs/cap01/metrics.json`.
8. Quay video hoặc GIF "robot nghỉ" dài 5 s và viết một trang bài học rút ra trong `docs/` (nó đưa vào báo cáo CAP09).

### Code khởi đầu
Các stub interface cho thế giới và môi trường (skeleton kinematics nằm trong phần Cài đặt tham khảo):

```python
# --- src/corebot/sim/world.py ---
import numpy as np


def sample_table_points(seed: int, n: int) -> np.ndarray:
    """(n, 3) points on the table top, in the arm_base frame, drawn with np.random.default_rng(seed)."""
    raise NotImplementedError


def make_scene(seed: int) -> dict:
    """Seeded scene description: object poses, bin poses, obstacle poses (plain dict of lists)."""
    raise NotImplementedError


# --- src/corebot/sim/env.py ---
class Env:
    """Seeded MuJoCo environment. Public attributes used by the acceptance tests: model, data."""

    def __init__(self, model_path: str):
        """Load the MJCF with mujoco.MjModel.from_xml_path; do not create randomness here."""
        raise NotImplementedError

    def reset(self, seed: int) -> None:
        """mj_resetData, then place objects from make_scene(seed). Same seed, same state."""
        raise NotImplementedError

    def step(self, ctrl) -> None:
        """Write ctrl into data.ctrl (clipped to ctrlrange) and call mujoco.mj_step once."""
        raise NotImplementedError

    def scene_hash(self) -> str:
        """sha256 hex of the scene description (object poses rounded to 1e-9)."""
        raise NotImplementedError
```

### Kiểm thử
Lưu thành `tests/acceptance/test_cap01.py`. Các gate check là `test_determinism` và `test_fk_matches_mujoco`. Test forward kinematics qua URDF là tùy chọn (nó bị bỏ qua nếu thiếu `yourdfpy`). Tệp cần numpy và mujoco nên không chạy được trong CoreLab, nhưng các phần spec-traceability và hygiene chỉ đọc repository của bạn.

```python
"""tests/acceptance/test_cap01.py: CAP01 acceptance suite (thresholds are provisional)."""
import ast
import json
import pathlib
import re
import xml.etree.ElementTree as ET

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
XML = ROOT / "models" / "corebot.xml"
URDF = ROOT / "models" / "corebot.urdf"
METRICS = ROOT / "runs" / "cap01" / "metrics.json"


def record(name, value):
    """Merge one number into runs/cap01/metrics.json (the report reads it later)."""
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(METRICS.read_text()) if METRICS.exists() else {}
    data[name] = value
    METRICS.write_text(json.dumps(data, indent=2, sort_keys=True))


def scripted(model, k):
    return 0.3 * np.sin(0.02 * k + np.arange(model.nu))


def run_scripted(seed, steps=500):
    from corebot.sim.env import Env
    env = Env(str(XML))
    env.reset(seed)
    for k in range(steps):
        env.step(scripted(env.model, k))
    return env.data.qpos.copy(), env.scene_hash()


def test_determinism():  # GATE: SR1
    q1, h1 = run_scripted(7)
    q2, h2 = run_scripted(7)
    diff = float(np.max(np.abs(q1 - q2)))
    record("determinism_max_abs_diff", diff)
    assert diff < 1e-9 and h1 == h2   # 1e-9: same machine, same binary, so expect exactly 0


def _tool_in_base(mujoco, model, data):
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "arm_base")
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "tool0")
    R = data.xmat[bid].reshape(3, 3)
    return R.T @ (data.site_xpos[sid] - data.xpos[bid])


def test_fk_matches_mujoco():  # GATE: SR2
    import mujoco
    from corebot.manipulation.kinematics import ARM_JOINTS, fk
    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    rng = np.random.default_rng(2024)
    adr = [model.joint(n).qposadr[0] for n in ARM_JOINTS]
    lo = np.array([model.joint(n).range[0] for n in ARM_JOINTS])
    hi = np.array([model.joint(n).range[1] for n in ARM_JOINTS])
    worst = 0.0
    for _ in range(20):
        q = rng.uniform(lo, hi)
        data.qpos[adr] = q
        mujoco.mj_forward(model, data)
        worst = max(worst, float(np.linalg.norm(fk(q) - _tool_in_base(mujoco, model, data))))
    record("fk_max_error_m", worst)
    assert worst < 1e-3   # 1 mm: a unit or axis mistake gives centimetres, rounding gives micrometres


def test_urdf_fk_matches_mjcf():  # optional library check
    yourdfpy = pytest.importorskip("yourdfpy")
    import mujoco
    from corebot.manipulation.kinematics import ARM_JOINTS
    robot = yourdfpy.URDF.load(str(URDF))
    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    rng = np.random.default_rng(5)
    worst = 0.0
    for _ in range(20):
        q = rng.uniform(-0.5, 0.5, len(ARM_JOINTS))
        robot.update_cfg(dict(zip(ARM_JOINTS, q)))
        T = robot.get_transform("tool0", "arm_base")
        data.qpos[[model.joint(n).qposadr[0] for n in ARM_JOINTS]] = q
        mujoco.mj_forward(model, data)
        worst = max(worst, float(np.linalg.norm(T[:3, 3] - _tool_in_base(mujoco, model, data))))
    assert worst < 1e-3


def test_urdf_mjcf_consistency():  # SR3
    import mujoco
    model = mujoco.MjModel.from_xml_path(str(XML))
    root = ET.parse(URDF).getroot()
    urdf_limits = {}
    for j in root.iter("joint"):
        lim = j.find("limit")
        if j.get("type") in ("revolute", "prismatic") and lim is not None:
            urdf_limits[j.get("name")] = (float(lim.get("lower")), float(lim.get("upper")))
    for name, (lo, hi) in urdf_limits.items():
        rng = model.joint(name).range     # raises if the joint name is missing in the MJCF
        assert abs(rng[0] - lo) < 1e-6 and abs(rng[1] - hi) < 1e-6, name
    urdf_mass = sum(float(m.get("value")) for m in root.iter("mass"))
    mj_mass = float(model.body_mass.sum())
    record("mass_rel_diff", abs(urdf_mass - mj_mass) / mj_mass)
    assert abs(urdf_mass - mj_mass) / mj_mass < 0.02


def test_rest_stability():  # SR4
    import mujoco
    from corebot.sim.env import Env
    env = Env(str(XML))
    env.reset(0)
    m, d = env.model, env.data
    base = m.body("base_link").id
    p0, q0 = d.xpos[base].copy(), d.qpos.copy()
    worst_pen = 0.0
    for _ in range(int(5.0 / m.opt.timestep)):
        env.step(np.zeros(m.nu))
        assert np.all(np.isfinite(d.qpos))
        for c in d.contact[: d.ncon]:
            worst_pen = max(worst_pen, -c.dist)
    drift = float(np.linalg.norm(d.xpos[base][:2] - p0[:2]))
    arm = [m.joint(n).qposadr[0] for n in
           ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")]
    arm_drift = float(np.degrees(np.max(np.abs(d.qpos[arm] - q0[arm]))))
    record("rest_base_drift_m", drift)
    record("rest_arm_drift_deg", arm_drift)
    record("rest_max_penetration_m", worst_pen)
    assert drift < 2e-3 and arm_drift < 0.5 and worst_pen < 2e-3


def test_reachability():  # SR5
    from corebot.manipulation.kinematics import top_down_reachable
    from corebot.sim.world import sample_table_points
    pts = sample_table_points(123, 100)
    frac = sum(bool(top_down_reachable(p)) for p in pts) / len(pts)
    record("reachable_fraction", frac)
    assert frac >= 0.95


def _test_functions():
    names = set()
    for f in (ROOT / "tests").rglob("test_*.py"):
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                names.add(node.name)
    return names


def test_spec_traceability():  # SR6
    text = (ROOT / "SPEC.md").read_text()
    existing = _test_functions()
    ids = set()
    for line in text.splitlines():
        m = re.match(r"\|\s*(SR\d+)\s*\|", line)
        if not m:
            continue
        cited = re.findall(r"::(test_\w+)", line)
        assert cited and all(c in existing for c in cited), f"{m.group(1)} cites a missing test"
        ids.add(m.group(1))
    record("spec_requirements", len(ids))
    assert len(ids) >= 8


def test_repo_hygiene():  # SR7
    n = sum(len([x for x in ast.walk(ast.parse(f.read_text()))
                 if isinstance(x, ast.FunctionDef) and x.name.startswith("test_")])
            for f in (ROOT / "tests" / "unit").glob("test_*.py"))
    record("unit_tests", n)
    assert n >= 15
    assert re.search(r"==\s*\d", (ROOT / "pyproject.toml").read_text()), "pin versions with =="
```

Các ngưỡng là giá trị khởi đầu tạm thời (provisional; xem lý do trong kế hoạch); hãy siết chặt chúng khi bạn có lần chạy tham chiếu của riêng mình. Lý do một dòng: tất định dưới $10^{-9}$ vì cùng binary trên cùng máy phải cho đúng 0; FK dưới 1 mm vì một lần gắp chịu được khoảng 5 mm; giới hạn trong $10^{-6}$ và khối lượng trong 2 % vì chỉ làm tròn float và quán tính mới nên khác; trôi nghỉ 2 mm và 0.5 độ vì một robot trôi sẽ làm hỏng test odometry ở CAP02; 95 % với tới được vì nó xác nhận quyết định về kích thước; 8 yêu cầu truy vết được và 15 unit test vì chúng chứng minh lưới an toàn tồn tại.

### Kết quả mong đợi
Một lần chạy đạt in ra đại loại như sau (thời gian sẽ khác):

```text
........                                                                 [100%]
8 passed in 6.41s
```

Nếu không cài `yourdfpy` bạn thấy `7 passed, 1 skipped`, vẫn tính là đạt:

```text
.s......                                                                 [100%]
7 passed, 1 skipped in 6.02s
```

và một `runs/cap01/metrics.json` như thế này (giá trị minh họa):

```json
{
  "determinism_max_abs_diff": 0.0,
  "fk_max_error_m": 0.00012,
  "mass_rel_diff": 0.004,
  "reachable_fraction": 0.97,
  "rest_arm_drift_deg": 0.02,
  "rest_base_drift_m": 0.0003,
  "rest_max_penetration_m": 0.0005,
  "spec_requirements": 10,
  "unit_tests": 17
}
```

### Thử thách mở rộng
Stretch: thêm một kiểm tra render rằng camera nhìn thấy cả ba vật thể từ tư thế home, và một test rằng một cảnh sinh ngẫu nhiên không bao giờ đặt vật thể bên trong thùng hay trụ (1000 seed). Tầng phần cứng tùy chọn: không có ở milestone này, nhưng hãy ghi trong `docs/` nơi SO-101 thật sẽ khác mô hình của bạn (backlash, độ mềm của gripper, độ trễ servo); CAP02 và CAP06 dùng ghi chú đó.

### Thực hành với thư viện
Kiểm chéo kinematics của bạn với URDF qua một thư viện thay vì parser của riêng bạn: `yourdfpy` (hoặc `pinocchio`) tính phía URDF và MuJoCo tính phía kia, nên một dòng thất bại chỉ ra một tệp mô hình, không phải FK của bạn:

```python
# Needs: pip install mujoco numpy yourdfpy   (pinocchio is an alternative for the URDF side)
import numpy as np
import mujoco
import yourdfpy

from corebot.manipulation.kinematics import ARM_JOINTS, fk

model = mujoco.MjModel.from_xml_path("models/corebot.xml")
data = mujoco.MjData(model)
robot = yourdfpy.URDF.load("models/corebot.urdf")
rng = np.random.default_rng(11)
bid = model.body("arm_base").id
sid = model.site("tool0").id
adr = [model.joint(n).qposadr[0] for n in ARM_JOINTS]

rows = []
for i in range(20):
    q = rng.uniform(-0.6, 0.6, len(ARM_JOINTS))
    data.qpos[adr] = q
    mujoco.mj_forward(model, data)
    p_mj = data.xmat[bid].reshape(3, 3).T @ (data.site_xpos[sid] - data.xpos[bid])
    robot.update_cfg(dict(zip(ARM_JOINTS, q)))
    p_urdf = robot.get_transform("tool0", "arm_base")[:3, 3]
    rows.append((np.linalg.norm(fk(q) - p_mj), np.linalg.norm(p_urdf - p_mj)))

err = np.array(rows)
print("max |FK - MuJoCo| = %.2e m, max |URDF - MuJoCo| = %.2e m" % tuple(err.max(axis=0)))
assert (err < 1e-3).all()
```

Mong đợi: một dòng `max |FK - MuJoCo| = ... m, max |URDF - MuJoCo| = ... m` với cả hai số dưới $10^{-3}$. Nếu số URDF lớn mà số FK của bạn nhỏ thì URDF sai (kiểm tra dấu trục và thứ tự `rpy`).

## Kiểm chứng

Kiểm chứng ở ba mức. Bằng tay: forward kinematics ở tư thế zero và một tư thế bạn đo được bằng thước trên mô hình; đơn vị của mọi con số trong MJCF. Bằng test: bộ acceptance ở trên; hãy kill-test nó bằng cách cố ý làm hỏng (đảo một trục khớp trong URDF, đổi một seed, xóa một tên test khỏi SPEC.md) và xác nhận đúng test thất bại. Bằng đọc: quét `git diff` của `models/` tìm giá trị nào không có comment đơn vị.

Milestone này đáng **8 trên 100 điểm**. Phần tự động (60 %) là tỉ lệ có trọng số bảy check đạt, trong đó hai gate (tất định, forward kinematics) là bắt buộc để tốt nghiệp. Phần con người (40 %) là bốn tiêu chí chấm 0 đến 4 kèm liên kết bằng chứng: chất lượng spec (đo lường được? bác bỏ được?), độ thực tế của mô hình và ghi tài liệu đơn vị, thiết kế test, độ rõ ràng của repository. Prompt review tùy chọn cho một LLM (đưa nó code và artefact, không đưa nhận định của chính bạn): "Here are SPEC.md, the models and the tests. For each requirement say whether the metric, threshold and test are consistent, and name the weakest one."

## Lỗi thường gặp

- **Độ so với radian**: mặc định của MJCF là độ; URDF là radian; một dải hinge `0 1.57` thành 1.57 độ.
- **Quán tính suy từ mesh vô nghĩa**: mesh hiển thị dùng làm quán tính cho giá trị âm hoặc phi lý; hãy dùng hình nguyên thủy hoặc inertial tường minh.
- **Ma sát bánh gây rung hoặc trượt**: base bò đi khi nghỉ hoặc dao động; chỉnh ma sát và damping và test lúc nghỉ.
- **Bước thời gian quá lớn cho contact**: độ xuyên tăng và vật thể nổ tung; giảm bước trước khi đổi bất cứ thứ gì khác.
- **Dấu trục URDF không khớp**: FK của bạn khớp MuJoCo nhưng không khớp URDF; test tùy chọn bắt được.
- **Chép asset Menagerie mà không có license**: giữ mỗi license bên cạnh asset của nó.
- **Ngẫu nhiên bị rò**: `np.random.rand`, `random`, thứ tự duyệt set hoặc đồng hồ làm một lần chạy không tái lập được; chỉ dùng `default_rng(seed)`.
- **Một spec không ai làm nó thất bại được**: ngưỡng không có lý do, test không khẳng định gì, hoặc yêu cầu được viết sau khi code đã đạt.

## Phương án khác và đánh đổi

MuJoCo là nguồn sự thật duy nhất ở đây; một thế giới dựa trên Gazebo cho bộ công cụ ROS 2 phong phú hơn nhưng thêm một vật lý thứ hai phải giữ khớp. Bạn có thể bỏ hẳn URDF và chỉ giữ MJCF, điều này loại bỏ một bài toán nhất quán nhưng cũng loại bỏ cầu nối tới ROS 2 và Nav2. FK dạng đóng so với thư viện (`pinocchio`, `yourdfpy`): tự viết một lần dạy bạn các frame; giữ thư viện làm kiểm chéo. Về kịch bản, các phương án như tác vụ tabletop SO-101 đứng yên hay rover kiểu F1TENTH đã được cân nhắc; mobile manipulator được chọn là cái vận dụng cùng lúc định vị, điều hướng, thao tác, firmware và lớp task trong phạm vi ngân sách.

## Vận dụng và ghi nhớ

Milestone này chuẩn bị cho CAP02 (base firmware-in-the-loop dùng Env và `WheelCmd`/`WheelState` của bạn), CAP03 (EKF dùng các frame của bạn và các kiểm tra nhất quán của `evalkit`) và CAP05 (FK của bạn trở thành IK). Câu hỏi nhớ lại: (1) viết sáu cột của một hàng yêu cầu theo trí nhớ và cho một ví dụ tốt; (2) nói vì sao góc MJCF và URDF có thể âm thầm không khớp; (3) giải thích cận dưới Wilson thêm gì so với một phần trăm thành công; (4) liệt kê ba cách ngẫu nhiên rò vào một lần chạy có seed. Sau một tuần, hãy làm lại lập luận 1 mm cho một độ dài link khác.

## Đáp án bài tập

1. `wilson_interval(27, 30)` xấp xỉ (0.744, 0.965), ước lượng điểm 0.90. Cận dưới 0.744 thấp hơn 0.75 nên test thất bại, sát nút: với 30 episode bạn chưa thể khẳng định 0.75. Cách sửa trung thực là thêm episode hoặc hạ yêu cầu; đổi seed thì không.
2. Ví dụ SR-a: "Base nghỉ không bò", metric: thay đổi vị trí base trong 5 s với lệnh bằng không, ngưỡng 2 mm, lý do: dưới độ phân giải odometry của CAP02, test `test_rest_stability`. SR-b: "Tay giữ tư thế", metric: độ trôi khớp lớn nhất trong 5 s, ngưỡng 0.5 độ, lý do: nhỏ hơn nhiều so với dung sai gắp ở 0.3 m (0.5 độ là 2.6 mm), test cùng hàm đó. Cả hai đều bác bỏ được bằng cùng dữ liệu ghi log.
3. Khi không có thẻ `<compiler>`, góc là độ: $110^\circ=1.920$ rad, nên dải là $\pm1.920$ rad và `lower`/`upper` của URDF phải là $\mp1.920$ (đến 6 chữ số thập phân). `range="0 1.57"` là 1.57 độ $=0.0274$ rad nên khớp hầu như không động. Hãy đặt `<compiler angle="radian"/>` hoặc chuyển đổi có chủ ý và ghi chú.
4. 5 s ở 1 ms là 5000 bước. 500 bước là 0.5 s. Ở bước 2 ms, 500 bước là 1.0 s và 5 s nghỉ là 2500 bước; test không còn so sánh được và contact có thể ứng xử khác, nên chỉ đổi bước kèm một ghi chú trong nhật ký quyết định.
5. $\Delta\theta=1\text{ mm}/L$: với 0.1 m, 0.0100 rad $=0.573^\circ$; với 0.36 m, 0.00278 rad $=0.159^\circ$. Sai số ở các khớp gần đế bị cánh tay đòn khuếch đại, và một lỗi dấu hay trục có thể biến mất ở tư thế zero (mọi góc bằng 0), nên cần các cấu hình ngẫu nhiên.
6. $|3.18-3.10|/3.18=2.52\%$: không đạt ở mức 2 %. Nguyên nhân khả dĩ: thiếu một body (hàm gripper, camera, pin) trong URDF, hoặc MJCF dùng mật độ mặc định còn URDF có khối lượng tường minh; cũng có thể là nhầm đơn vị (gram so với kilogram).
7. Khoảng Wilson của 91/100 xấp xỉ (0.838, 0.952). Ước lượng điểm 0.91 thấp hơn 0.95 nên test thất bại. Cách sửa: dời bàn gần hơn hoặc nâng trụ để nhiều điểm rơi vào hình vành khăn hơn; thu hẹp mép xa của bàn; chọn lại offset gắn tay. Trong đoạn mã bước 4 (`reach_demo.py`), cùng bàn rộng 0.24 m đạt 98.6 % với tới được ở 0.18 đến 0.32 m phía trước và chỉ 36.3 % ở 0.25 đến 0.45 m.
8. Khiếm khuyết: (a) `random.shuffle` dùng bộ sinh Python toàn cục mà `np.random.seed` không gieo; (b) `np.random.seed` gieo trạng thái NumPy toàn cục mà bất kỳ thư viện nào cũng có thể tiêu thụ nên chuỗi phụ thuộc thứ tự gọi; (c) các lần chạy giống hệt trong cùng tiến trình che giấu vấn đề vì trạng thái tiến trình lặp lại. Máy khác hoặc phiên bản thư viện khác đổi thứ tự tiêu thụ. Sửa: `rng = np.random.default_rng(seed)` trong `reset`, truyền `rng` vào mọi helper và dùng `rng.permutation(objs)` và `rng.uniform(...)`; không bao giờ đụng trạng thái toàn cục.
9. Ở mỗi bước ghi vị trí base, góc khớp tay, `np.isfinite` của `qpos`, và giá trị lớn nhất của $-\text{contact.dist}$ trên `data.contact[:data.ncon]`. Ngưỡng: trôi base 2 mm, trôi tay 0.5 độ, xuyên 2 mm. Kiểm tra trạng thái cuối có thể đạt trong khi robot đã lắc rồi quay lại, hoặc một contact đã nổ rồi lắng; giá trị lớn nhất theo thời gian bắt được các hiện tượng thoáng qua. Dùng cùng lệnh bằng không và seed cố định.
10. Một đáp án tốt có mười hàng, mỗi hàng có con số và đơn vị, ngưỡng được biện minh bằng một nhu cầu sau này (dung sai gắp, độ phân giải odometry, nhiễu benchmark), và một bộ kiểm tra phân tích bảng và báo hàng vi phạm. Code điển hình: một biểu thức chính quy cho mỗi hàng, `assert` rằng ô metric và ngưỡng không rỗng và mọi `::test_name` tồn tại. Một ngưỡng đổi khi lần chạy tham chiếu cho thấy nó luôn đạt với biên rộng (quá lỏng) hoặc chập chờn (quá chặt), ghi trong nhật ký quyết định.

## Đọc thêm

- [MuJoCo documentation: modeling](https://mujoco.readthedocs.io/en/stable/modeling.html) - các phần tử MJCF, thuộc tính `angle` của compiler, quán tính và contact.
- [MuJoCo documentation: simulation loop](https://mujoco.readthedocs.io/en/stable/programming/simulation.html) - `mj_step`, `mj_forward`, reset.
- [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) - mô hình `robotstudio_so101` và license của nó.
- [ROS 2 Jazzy URDF tutorial](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html) - khớp, link, giới hạn và inertial.
- [MIT 6.4210 Robotic Manipulation](https://manipulation.mit.edu/) - pipeline pick-and-place mà capstone mô phỏng; Lecture 1 bên dưới.
- [TidyBot (arXiv 2305.05658)](https://arxiv.org/abs/2305.05658) - dự án tham chiếu cho việc dọn dẹp bằng mobile manipulator.
- [Binomial proportion confidence interval (Wikipedia)](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval) - khoảng Wilson dùng trong các acceptance test.
- **Thực hành thêm:** [Tài liệu LeRobot SO-101](https://huggingface.co/docs/lerobot/so101), [Articulated Robotics: mô tả robot bằng URDF](https://www.youtube.com/watch?v=CwdbsvcpOHM).
