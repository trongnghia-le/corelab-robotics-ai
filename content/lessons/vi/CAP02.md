---
{"title": "Capstone đế firmware-in-the-loop: vòng tốc độ, giao thức CRC8, watchdog và odometry", "summary": "Xây đế di chuyển của CoreBot Tidy bằng C portable chạy trên host qua ctypes: bộ giải mã cầu phương, vòng tốc độ bánh PI có anti-windup, giao thức nối tiếp đóng khung CRC-8, watchdog lệnh, mô hình động cơ khớp từ dữ liệu bước và odometry đã hiệu chuẩn, được kiểm chứng bằng bộ kiểm thử nghiệm thu offline.", "objectives": ["Cài đặt và kiểm thử đơn vị mã C kiểu nhúng (bộ giải mã cầu phương, vòng tốc độ PI có anti-windup, đóng khung CRC-8, watchdog) và gọi nó từ simulator qua ctypes.", "Đạt các đặc tả tường minh về đáp ứng bước, giao thức và watchdog bằng các hàm evalkit và đọc số đo từ các artefact đã ghi log.", "Nhận dạng mô hình động cơ bậc nhất từ dữ liệu bước và báo cáo độ khớp một cách trung thực.", "Tính odometry từ số đếm bánh và hiệu chuẩn bán kính bánh và track width theo đúng thứ tự.", "Lập ngân sách độ trễ và tải liên kết cho vòng host 100 Hz và chọn timeout watchdog với lý do được nêu rõ."]}
---

## Vì sao điều này quan trọng

CoreBot Tidy chỉ có thể đi tới nơi bạn muốn nếu bánh xe làm đúng điều host yêu cầu và báo lại trung thực điều chúng đã làm. Ở CAP01 bạn đã dựng một robot đứng yên trong một thế giới có seed. Ở milestone này bạn trang bị cho nó một **bộ điều khiển đế (base controller)** đúng như robot thật: một đoạn C nhúng nhỏ đóng vòng tốc độ bánh ở 1 kHz, một liên kết nối tiếp có đóng khung và checksum với host, một watchdog dừng động cơ khi host im lặng, và một lớp odometry trên host biến số đếm encoder thành tư thế (pose). Mọi milestone sau (EKF ở CAP03, điều hướng ở CAP04, bộ giám sát an toàn ở CAP07) đều đứng trên lớp này. Nếu đáp ứng bước của nó cẩu thả, giao thức âm thầm rớt frame, hoặc watchdog không bao giờ kích hoạt, lỗi sẽ hiện ra ba milestone sau dưới dạng "planner chập chờn".

Cách tiếp cận là **firmware-in-the-loop** (FIL): mã C được viết như cho vi điều khiển (số nguyên độ rộng cố định, không `malloc`, không bất ngờ về dấu phẩy động), nhưng bạn biên dịch nó trên laptop thành `libfw.so` và gọi từ simulator ở 1 kHz qua `ctypes`. Cùng các file nguồn đó build được cho ESP32 bằng PlatformIO, nên tầng phần cứng tùy chọn (xem thử thách mở rộng) chỉ là nạp lại firmware chứ không phải viết lại.

Đây là bản brief dự án từ một kỹ sư senior gửi bạn: bài học giải thích bạn đang dùng lại những chủ đề nào trước đó, phần Thực hành độc lập là bản brief thật sự, và các bài kiểm thử cho bạn biết khi nào xong.

## Trực giác

![Kiến trúc CoreBot Tidy: cảm biến và simulator, đế firmware-in-the-loop, ước lượng, lập bản đồ và lập kế hoạch, nhận thức, thao tác, lớp tác vụ và bộ giám sát an toàn có thể dừng mọi đường tới cơ cấu chấp hành](/lesson-figures/CAP-architecture.svg)

*Toàn bộ hệ thống. Milestone này là dải màu cam: nó nằm giữa vật lý (plant MuJoCo) và mọi thứ host làm. Hai đầu ra của nó là số đếm bánh kèm từ trạng thái, và một cam kết: không có lệnh quá lâu nghĩa là PWM bằng 0.*

Hãy hình dung firmware như một **nhân viên rất đáng tin và rất nhàm chán** ở bánh xe. Host (một quản lý thông minh nhưng đôi khi trễ) gửi "đi 0.3 m/s". Nhân viên đổi nó thành tốc độ bánh, giữ mỗi bánh ở tốc độ đó chỉ bằng thông tin cục bộ (số đếm encoder, một đồng hồ), báo lại số đếm, và có một quy tắc dán trên tường: *nếu quản lý ngừng nói 80 ms, dừng động cơ và chờ*. Nhân viên không bao giờ tin một thông điệp sai checksum và không bao giờ để một thông điệp nhận dở làm quay bánh.

![Đường dữ liệu CAP02: tốc độ bánh ra lệnh vào vòng tốc độ PI bằng C, PWM lái động cơ mô phỏng, bộ giải mã cầu phương cho số đếm 16 bit, một frame CRC-8 mang số đếm tới driver trên host, và watchdog ép PWM về 0 khi lệnh ngừng đến](/lesson-figures/CAP02.svg)

Milestone này dùng lại, và bạn nên đọc lại nếu đã mờ: [CAP01](/lessons/CAP01) (repo, `interfaces.py`, env có seed), [HW10](/lessons/HW10) (điều khiển tốc độ nhúng, định thời PWM và encoder), [HW11](/lessons/HW11) (liên kết MCU với ROS 2, đóng khung), [C09](/lessons/C09) (PI rời rạc, anti-windup), [S06](/lessons/S06) (mở bọc bộ đếm, độ mới, ánh xạ lệnh), [CPP08](/lessons/CPP08) (kiểm thử mã C và C++) và [S08](/lessons/S08) (khớp mô hình động cơ bậc nhất từ dữ liệu bước).

## Lý thuyết và suy dẫn

Đây là **ghi chú tích hợp (integration notes)**: vài công thức và giao diện quan trọng ở đây, mỗi cái kèm chủ đề đã suy dẫn nó.

### 1. Số đếm, tốc độ và lượng tử hóa ([HW10](/lessons/HW10), [S06](/lessons/S06))

Với $\text{PPR}$ xung mỗi vòng động cơ, giải mã $\times4$ và tỉ số hộp số $g$, một vòng bánh là $N=4\cdot\text{PPR}\cdot g$ số đếm. Với động cơ N20 mô phỏng, $\text{PPR}=11$, $g=34$, nên $N=1496$. Ước lượng tốc độ từ số đếm trong cửa sổ $T$ có bước lượng tử
$$\Delta\omega=\frac{2\pi}{N\,T}.$$
Ở tốc độ điều khiển 100 Hz ($T=10$ ms) đó là $0.42$ rad/s, **7 % của mục tiêu 6 rad/s**. Vì vậy vòng PI dùng một bộ lọc hoặc cửa sổ ngắn, và vì vậy tốc độ bạn ghi log (cột `omega` trong `step_left.csv`) được tính trên 50 ms ($\Delta\omega=0.084$ rad/s, 1.4 %). Hiện tượng răng cưa (aliasing) giữa tốc độ vòng lặp và lượng tử hóa encoder là một lỗi kinh điển.

### 2. PI rời rạc với anti-windup ([C09](/lessons/C09))

Với sai số $e_k=\omega^*-\omega_k$ và chu kỳ lấy mẫu $T_s$:
$$u_k=\operatorname{sat}\bigl(K_p e_k + I_k\bigr),\qquad I_{k}=I_{k-1}+K_i e_k T_s\ \text{(chỉ khi không bão hòa, hoặc khi } e_k \text{ kéo } u \text{ trở lại)}.$$
Đây là *tích phân có điều kiện (conditional integration)*. Không có nó, một bánh bị kẹt làm $I$ tăng không giới hạn: trong ví dụ có lời giải $K_i e t=1.5\cdot6\cdot1=9$ sau một giây, gấp chín lần toàn thang, và bánh lao tới 20 rad/s khi được thả.

### 3. Mô hình động cơ từ dữ liệu bước ([S08](/lessons/S08))

Khớp $\omega(t)=K_u\,u\,(1-e^{-t/\tau})$ với một bước vòng hở. Động cơ mô phỏng có $K_u=20$ rad/s mỗi đơn vị duty và $\tau=80$ ms; `sysid/motor_fit.py` phải khôi phục cả hai trong vài phần trăm và ghi vào `configs/motor_params.json`. Quy tắc ngón tay cái cho plant bậc nhất: thời gian xác lập 2 % của vòng hở là $\approx 4\tau=0.32$ s; vòng kín phải thắng nó, và đó là điều đặc tả settle < 0.35 s mã hóa.

### 4. Định dạng frame và CRC ([HW11](/lessons/HW11), [S06](/lessons/S06))

Frame logic (12 byte, little-endian): `type, seq, left(u16), right(u16), status, tick_ms(u16), vbat_dV, reserved, crc8`. Dạng trên dây: `0x7E` + frame với mỗi `0x7E`/`0x7D` thay bằng `0x7D, b ^ 0x20` + `0x7E`. CRC-8 dùng đa thức $x^8+x^2+x+1$ (`0x07`), giá trị đầu 0, không đảo bit; giá trị kiểm tra chuẩn là `crc8(b"123456789") == 0xF4`. Tải liên kết, như ở S06:
$$\text{load}=\frac{B_{\text{wire}}\cdot10\cdot f}{\text{baud}},\qquad \frac{26\cdot10\cdot100}{115200}=22.6\%\ \text{(trường hợp xấu nhất, mọi byte đều bị escape)}.$$
Frame điển hình là 14 byte trên dây: 12.2 %. CRC-8 phát hiện mọi lỗi một bit trong frame ngắn thế này, và bạn không phải tin suông: bài kiểm thử lật từng bit của frame 12 byte (96 lần lật).

### 5. Watchdog ([S07](/lessons/S07), [HW10](/lessons/HW10))

Firmware giữ `last_cmd_ms`. Mỗi tick: `expired = !armed || (uint32_t)(now - last) >= timeout`. Khi hết hạn: PWM = 0 **và bộ tích phân PI được reset**, nếu không việc phục hồi sẽ bắt đầu từ một tích phân cũ. Phép trừ không dấu chịu được việc bộ đếm mili giây 32 bit quay vòng. Lúc khởi động `armed = 0`, nên đầu ra giữ bằng 0 cho tới lệnh hợp lệ đầu tiên. Quy tắc timeout: khoảng 3 chu kỳ host (ở đây 30 ms) là mức sàn; đặc tả của milestone là "về 0 trong 100 ms", nên ta dùng 80 ms. Quãng đường đi được trong lúc timeout chạy là một con số thiết kế: $0.5\,\text{m/s}\times0.08\,\text{s}=4$ cm.

### 6. Odometry vi sai và hai hằng số hiệu chuẩn ([CAP01](/lessons/CAP01), [S06](/lessons/S06))

$$\Delta s=\frac{r(\Delta\phi_R+\Delta\phi_L)}{2},\qquad \Delta\theta=\frac{r(\Delta\phi_R-\Delta\phi_L)}{b},\qquad x\mathrel{+}=\Delta s\cos\theta,\ y\mathrel{+}=\Delta s\sin\theta,$$
với bán kính bánh $r$ và khoảng cách hai bánh (track width) $b$. Hiệu chuẩn theo thứ tự này: chạy một đường thẳng đã đo để có $r_{\text{true}}=r_{\text{est}}\cdot d_{\text{true}}/d_{\text{reported}}$; rồi quay tại chỗ một góc thật đã biết để có $b_{\text{true}}=b_{\text{est}}\cdot\theta_{\text{reported}}/\theta_{\text{true}}$. Sai $r$ làm co giãn quãng đường; sai $b$ làm co giãn hướng, và sai hướng chi phối sai số vị trí sau vài mét.

## Ví dụ có lời giải

Mọi giá trị dưới đây là **minh họa (illustrative)** (sinh ra từ một mô phỏng độc lập nhỏ của plant và bộ điều khiển trên, không phải từ một lần chạy repository của bạn); số của bạn sẽ khác, và không sao miễn là các bài kiểm thử qua.

Plant: $K_u=20$ rad/s, $\tau=80$ ms, $N=1496$, PI ở 100 Hz với $K_p=0.12$, $K_i=1.5$, bộ đếm bắt đầu ở 65000 để việc quay vòng 16 bit xảy ra trong log.

| t (s) | omega (rad/s, cửa sổ 50 ms) | counts (uint16) |
|---|---|---|
| 0.001 | 0.00 | 65000 |
| 0.051 | 3.70 | 65044 |
| 0.101 | 5.80 | 65113 |
| 0.151 | 5.88 | 65183 |
| 0.201 | 5.96 | 65254 |
| 0.301 | 6.05 | 65397 |

`step_metrics(t, y, target=6.0)` cho thời gian xác lập 0.19 s, vọt lố 0.8 %, sai số xác lập 0.01 %: tất cả trong giới hạn (0.35 s, 10 %, 2 %). Số đếm mỗi 10 ms ở 6 rad/s: $6/(2\pi)\cdot1496/100=14.3$, nên số đếm nguyên trong CSV tăng 14 hoặc 15 mỗi dòng.

Kiểm thử windup (bánh bị chặn 1 s rồi thả): với tích phân có điều kiện, đỉnh sau khi thả là 6.79 rad/s, vọt lố 13.2 % (giới hạn 15 %); với bộ tích phân luôn bật, tích phân là 9.0 lúc thả và bánh đạt 19.9 rad/s, vọt lố 232 %.

Kiểm thử watchdog: host gửi ở 100 Hz tới $t=500$ ms và im lặng tới 620 ms. PWM ghi log là 0.31 tới 579 ms và 0 từ 581 ms, nên nó về 0 khoảng 80 ms sau lệnh cuối (giới hạn 100 ms). Bánh trôi xuống khoảng 3.9 rad/s, lệnh tiếp tục lúc 620 ms, và bộ tích phân bắt đầu lại từ 0: tốc độ leo về 6 rad/s với đỉnh 6.07 rad/s (giới hạn $1.2\times6=7.2$).

Giao thức: frame cho seq 7, số đếm 65530 và 4 là `7e 01 07 fa ff 04 00 00 d2 04 4c 00 d6 7e` (14 byte, không byte nào cần escape). Chèn thêm 50 byte rác ngẫu nhiên phía trước không ngăn nó được phân tích, vì `0x7E` đứng đầu xả hết những gì đã gom.

Odometry (bán kính bánh thật 0.0335 m, danh định 0.0330 m; track width thật 0.163 m, danh định 0.160 m): đường thẳng 10 m đọc ra 9.85 m, trôi 1.5 %, nên $r=0.0330\cdot10/9.85=0.0335$. Hình vuông 2 m với hằng số danh định kết thúc cách sự thật 3.1 cm và 1.3 độ; với hằng số đã hiệu chuẩn $(0.03345, 0.1625)$ nó kết thúc cách 1.4 cm.

Một `runs/cap02/metrics.json` mẫu được cho ở phần Kết quả mong đợi.

## Bài tập

1. **(Easy)** Một encoder có 11 xung mỗi vòng ở động cơ, giải mã $\times4$ và hộp số 34:1. Tính số đếm mỗi vòng bánh, số đếm mỗi 10 ms ở 6 rad/s, và bước lượng tử tốc độ ở 100 Hz. *(Số của động cơ N20 mô phỏng; công thức từ bài HW10 và S06.)*
2. **(Easy)** Frame dài 14 byte trên dây (xấu nhất 26), gửi ở 100 Hz qua UART 115200 baud 8N1. Tải liên kết, điển hình và xấu nhất. Bạn có thể gửi ở 1 kHz không? *(Công thức: S06 và bài Wikipedia về đóng khung truyền nối tiếp.)*
3. **(Easy)** Tính tay `crc8` của hai byte `0x01 0x02` với đa thức `0x07`, giá trị đầu 0. Rồi nêu CRC của `b"123456789"` phải là bao nhiêu và vì sao một giá trị kiểm tra đã biết hữu ích.
4. **(Medium)** Host gửi lệnh ở 100 Hz. Chọn timeout cho watchdog và biện minh bằng ba lập luận (jitter của host, quãng phanh ở 0.5 m/s, dừng nhầm). Robot đi được bao xa sau lệnh cuối?
5. **(Medium)** *Ngân sách độ trễ.* Đặc tả nói thời gian chết từ lệnh đến phản hồi đầu tiên $\le20$ ms. Firmware chạy vòng tốc độ ở 100 Hz, liên kết là 14 byte ở 115200 baud, và số đếm encoder đầu tiên cần khoảng 6.8 ms chuyển động của động cơ. Cộng trường hợp xấu nhất và quyết định đặc tả có đạt được không. Suy ra 6.8 ms từ $K_u=20$ rad/s, $\tau=80$ ms, duty đầu tiên $K_p\cdot6=0.72$.
6. **(Medium)** *Tìm lỗi.* Bộ giải mã giữ `int delta = cur - prev;` với giá trị `uint16_t` và log hiện $-65\,526$ số đếm cho bước từ 65530 sang 4. Giải thích lỗi thăng cấp số nguyên (integer promotion) trong C và đưa ra dòng đã sửa. Rồi cho delta của 65500 sang 40.
7. **(Medium)** Giải thích bằng số vì sao bộ tích phân PI đạt 9.0 sau một lần kẹt 1 s ở mục tiêu 6 rad/s ($K_i=1.5$), và vì sao tích phân có điều kiện giữ nó gần 0.3. Còn phương pháp anti-windup nào khác và nó đánh đổi điều gì?
8. **(Medium)** *Hiệu chuẩn.* Sau khi chạy 10 m, odometry báo 9.85 m với $r_{\text{est}}=0.0330$ m. Cho $r$ mới. Sau khi quay 10 vòng thật (odometry đã sửa $r$) báo tổng cộng 3667.5 độ với $b_{\text{est}}=0.160$ m. Cho $b$ mới. Cái nào ảnh hưởng hình vuông 2 m nhiều hơn và vì sao?
9. **(Hard)** *Thiết kế.* Ở tốc độ bánh tối đa 20 rad/s, một bánh tạo bao nhiêu cạnh encoder mỗi mili giây? Một tick 1 kHz có thể lấy mẫu trực tiếp các đường A/B để giải mã không? Đề xuất firmware thật làm gì và simulator nên bắt chước thế nào.
10. **(Hard)** *Dấu phẩy cố định.* Cập nhật tích phân là $K_i e T_s$ với $K_i=1.5$, $T_s=0.01$. Nếu $I$ lưu ở Q15 (giá trị trong $[-1,1)$ với độ phân giải $2^{-15}$), sai số $e$ nào cho gia số nhỏ hơn một LSB, và điều gì xảy ra với sai số xác lập nếu bạn cắt cụt (truncate)? Dấu phẩy động có hợp lý trên ESP32 không?
11. **(Hard, mini-project)** Dựng vòng FIL và các artefact đáp ứng bước, rồi chèn lỗi liên kết (rớt 1 % frame, lật 1 bit mỗi 1000 frame, thêm 5 ms độ trễ) và báo cáo thời gian xác lập, vọt lố và bài kiểm thử watchdog thay đổi ra sao. Nêu các giả định, baseline (không lỗi), một ca biên (timeout watchdog đúng bằng chu kỳ lệnh) và quan sát nào sẽ bác bỏ thiết kế của bạn.

## Cài đặt tham khảo

Module dưới đây là `corebot/driver.py`, phía host của liên kết: codec frame, mở bọc bộ đếm và độ mới. Nó là một bộ khung: mỗi hàm có hợp đồng trong docstring và ném `NotImplementedError`. Hãy điền vào ở Nhiệm vụ 4 (các mảnh đều nhỏ; kỷ luật nằm ở các bài kiểm thử). Bản song sinh C của codec nằm ở `firmware/core/frame.c` và hai bên được kiểm chéo ở Nhiệm vụ 3.

```python
"""corebot/driver.py (skeleton): frames <-> SI units, counter unwrapping, freshness.

Contract (see interfaces.py): WheelState carries uint16 wrapped counts; this module turns them
into signed deltas and rad/s, and refuses to hand out stale data.
Units: SI. Time: seconds from one clock (the host monotonic clock). Counts: 4 * PPR * gear per wheel turn.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

SOF, ESC, FRAME_LEN = 0x7E, 0x7D, 12      # delimiter, escape byte, logical frame length incl. CRC
STATE_FMT = "<BBHHBHBB"                    # type, seq, left, right, status, tick_ms, vbat_dV, reserved


def crc8(data: bytes, poly: int = 0x07, init: int = 0x00) -> int:
    """CRC-8 (poly 0x07, no reflection). Check value: crc8(b"123456789") == 0xF4."""
    raise NotImplementedError


def pack_state(seq: int, left: int, right: int, status: int, tick_ms: int, vbat_dv: int) -> bytes:
    """Build the 12-byte logical frame: 11 body bytes (STATE_FMT, type 0x01) + CRC-8 of the body."""
    raise NotImplementedError


def stuff(frame: bytes) -> bytes:
    """Wire form: SOF + frame with every SOF/ESC byte replaced by ESC, byte ^ 0x20 + SOF."""
    raise NotImplementedError


class FrameParser:
    """Byte-at-a-time parser. feed() returns the list of valid 12-byte logical frames completed by
    these bytes. Bad CRC, wrong length or a dangling escape drop the frame and count it in
    `rejected`; the next SOF always resynchronises."""

    def __init__(self) -> None:
        self.rejected = 0

    def feed(self, data: bytes) -> list[bytes]:
        raise NotImplementedError


def unwrap_delta(prev: int, cur: int, bits: int = 16) -> int:
    """Signed difference of a free-running counter (modular arithmetic, see /lessons/S06)."""
    raise NotImplementedError


@dataclass(frozen=True)
class WheelSample:
    stamp: float          # s, host clock when the frame was received
    omega_left: float     # rad/s, positive = forward
    omega_right: float    # rad/s
    fresh: bool           # False when the newest frame is older than max_age


class Driver:
    """Owns the previous counts, the wheel geometry and the freshness rule."""

    def __init__(self, counts_per_rev: int, max_age: float = 0.03) -> None:
        self.counts_per_rev = counts_per_rev
        self.max_age = max_age

    def on_frame(self, stamp: float, frame: bytes) -> WheelSample:
        """Decode one valid frame; the first frame only primes the counters (omega = 0, fresh = False)."""
        raise NotImplementedError

    def poll(self, now: float) -> WheelSample:
        """Called every control tick; returns the last sample with fresh=False once older than max_age."""
        raise NotImplementedError
```

## Thực hành độc lập

### Mục tiêu

Thêm một đế drive firmware-in-the-loop vào `~/corebot-capstone`: C portable cho vòng tốc độ bánh, bộ giải mã cầu phương, giao thức đóng khung CRC-8 và watchdog; một driver và odometry trên host; một mô hình động cơ đã nhận dạng hệ thống; và các artefact dưới `runs/cap02/` làm `tests/acceptance/test_cap02.py` qua. Đây là milestone CAP02 của capstone và nó xây trên repository CAP01 của bạn.

### Thiết lập

Làm việc trong `~/corebot-capstone` (tạo ở CAP01). Bạn cần Python 3.10+, `gcc` và `cmake` (các bài kiểm thử bỏ qua kèm thông báo rõ nếu thiếu, và một lần bỏ qua tính là **không đạt** cho gate). Các phiên bản cần ghim trong `pyproject.toml`: `numpy`, `pytest`, `pyserial` (tùy chọn). Lệnh:

```bash
cd ~/corebot-capstone
source .venv/bin/activate                    # created in CAP01
sudo apt install -y build-essential cmake    # gcc + CMake + ctest; `make doctor` checks these
mkdir -p runs/cap02 firmware/core firmware/tests
cmake -S firmware -B firmware/build && cmake --build firmware/build   # builds libfw.so and test_core
ctest --test-dir firmware/build --output-on-failure
python -m corebot.sysid.motor_fit --out configs/motor_params.json     # your script, Task 5
pytest -q tests/acceptance/test_cap02.py
```

Thời gian chạy: các kịch bản bước, windup và watchdog mất vài giây trên laptop (vật lý 1 ms, 1 s đến 3 s thời gian mô phỏng mỗi kịch bản). Giữ file evalkit từ CAP01 ở `src/corebot/evalkit.py` (tải `/practice/capstone/evalkit.py` nếu bạn chưa có).

### Nhiệm vụ

1. **Bộ giải mã cầu phương** (`firmware/core/quad_decode.c`): giải mã x4 từ mẫu A/B 2 bit bằng bảng chuyển trạng thái, số đếm `uint16_t` quay vòng. Kiểm thử đơn vị: 12 chu kỳ thuận, ngược, quay qua 65535.
2. **Vòng tốc độ PI** (`pi_speed.c`): PI dấu phẩy động với anti-windup tích phân có điều kiện, đầu ra kẹp trong $[-1,1]$. Chỉnh $K_p,K_i$ cho đặc tả; ghi giá trị và lập luận vào `docs/tuning.md`.
3. **Codec frame và watchdog** (`frame.c`, `watchdog.c`): CRC-8, byte stuffing, một bộ giải mã không bao giờ tràn buffer và đồng bộ lại ở mỗi `0x7E`; một watchdog bắt đầu ở trạng thái đã hết hạn và dùng phép trừ thời gian không dấu. Kiểm chéo bằng Python rằng `FwLib.crc8` bằng `driver.crc8` trên 1000 đầu vào ngẫu nhiên.
4. **Phía host** (`src/corebot/driver.py`, `fw_sim.py`): hoàn thiện bộ khung tham khảo ở trên; `fw_sim.py` chạy tick 1 kHz (plant, bộ giải mã, mỗi tick thứ mười chạy PI và một frame) với một `LinkModel` có thể thêm độ trễ, rớt và lật bit từ bộ sinh có seed.
5. **Nhận dạng hệ thống** (`sysid/motor_fit.py`): ghi log một bước duty vòng hở, khớp $K_u$ và $\tau$, ghi `configs/motor_params.json`, báo cáo phần dư của khớp một cách trung thực (đừng giấu một khớp tệ bằng cách nới dung sai).
6. **Artefact** dưới `runs/cap02/`: `step_left.csv`, `step_right.csv` (cột `t,omega,counts`, mục tiêu 6 rad/s, bộ đếm bắt đầu gần 65535), `windup.csv` (bánh bị chặn tới $t=1$ s), `watchdog.csv` (cột `t_ms,cmd_rx,pwm,omega`), `latency.csv` (`cmd_id,dead_time_ms`), `loop_periods.csv` (`tick,period_ms`), `summary.json` (số liệu liên kết), `odometry.json`.
7. **Odometry và hiệu chuẩn** (`estimation/odometry.py`; `estimation/calibration.py` dành cho CAP03, ở đây là một script `calibrate_odometry.py`): ba lần chạy có seed của đường thẳng 10 m và hình vuông 2 m trước và sau hiệu chuẩn; ghi số trước/sau.
8. **Tùy chọn**: `firmware/platformio.ini` biên dịch cùng `core/` (xem phần Thực hành với thư viện). Không bắt buộc chạy.
9. Viết `docs/cap02_notes.md`: định thời và đơn vị của mọi giao diện, mặc định an toàn, bạn sẽ đổi gì cho ESP32 thật, và một trang bài học rút ra (nó đưa vào báo cáo CAP09).

### Code khởi đầu

Các stub C biên dịch được và thất bại rõ ràng (`firmware/core/fw_api.h` là hợp đồng; giữ nguyên nó):

```c
/* fw_api.h : the public surface of the portable firmware core (no malloc, fixed-width ints). */
#ifndef FW_API_H
#define FW_API_H
#include <stddef.h>
#include <stdint.h>

#define FR_SOF 0x7E
#define FR_ESC 0x7D
#define FR_LEN 12               /* logical frame: 11 bytes + CRC8 */
#define FR_MAX_WIRE (2 + 2 * FR_LEN)

/* quadrature decoder (x4) ------------------------------------------------ */
typedef struct { uint8_t prev_ab; uint16_t count; } qd_t;
void     qd_init(qd_t *q, uint8_t ab);
void     qd_update(qd_t *q, uint8_t ab);       /* ab = (A << 1) | B, call at >= 4x the max edge rate */

/* PI speed loop with conditional-integration anti-windup ----------------- */
typedef struct { float kp, ki, integ; } pi_t;
void     pi_init(pi_t *p, float kp, float ki);
float    pi_step(pi_t *p, float target, float measured, float dt);   /* returns duty in [-1, 1] */

/* frame codec: SOF + stuffed(frame) + SOF, CRC-8 (poly 0x07) ------------ */
uint8_t  crc8(const uint8_t *data, size_t n);
size_t   fr_encode(const uint8_t *logical, size_t n, uint8_t *wire);    /* returns wire length */
typedef struct { uint8_t buf[FR_LEN + 1]; uint8_t n; uint8_t esc; uint8_t overflow; } fr_dec_t;
void     fr_dec_init(fr_dec_t *d);
int      fr_dec_push(fr_dec_t *d, uint8_t byte, uint8_t *logical);      /* 1 = valid frame in logical[FR_LEN], 0 = nothing yet */

/* command watchdog ------------------------------------------------------- */
typedef struct { uint32_t last_ms; uint32_t timeout_ms; uint8_t armed; } wd_t;
void     wd_init(wd_t *w, uint32_t timeout_ms);   /* starts EXPIRED: outputs stay zero until the first feed */
void     wd_feed(wd_t *w, uint32_t now_ms);
int      wd_expired(const wd_t *w, uint32_t now_ms);

#endif
```

```c
/* firmware/core starter: every function compiles and every test fails clearly until you fill it in.
   Rules: no malloc, fixed-width integers, no printf in the control path, outputs ZERO at boot. */
#include "fw_api.h"

void qd_init(qd_t *q, uint8_t ab) { (void)q; (void)ab; /* TODO: store the first AB state, count = 0 */ }
void qd_update(qd_t *q, uint8_t ab) { (void)q; (void)ab; /* TODO: 16-entry transition table, +1/-1/0 */ }

void pi_init(pi_t *p, float kp, float ki) { (void)p; (void)kp; (void)ki; /* TODO */ }
float pi_step(pi_t *p, float target, float measured, float dt) {
    (void)p; (void)target; (void)measured; (void)dt;
    return 0.0f; /* TODO: PI, clamp to [-1, 1], integrate only when not saturated (or when the error pulls back) */
}

uint8_t crc8(const uint8_t *data, size_t n) { (void)data; (void)n; return 0; /* TODO: poly 0x07, init 0 */ }
size_t fr_encode(const uint8_t *logical, size_t n, uint8_t *wire) {
    (void)logical; (void)n; (void)wire;
    return 0; /* TODO: SOF, stuffed payload, stuffed CRC, SOF */
}
void fr_dec_init(fr_dec_t *d) { (void)d; /* TODO */ }
int fr_dec_push(fr_dec_t *d, uint8_t byte, uint8_t *logical) {
    (void)d; (void)byte; (void)logical;
    return 0; /* TODO: on SOF validate length + CRC; unstuff ESC; never overflow buf */
}

void wd_init(wd_t *w, uint32_t timeout_ms) { (void)w; (void)timeout_ms; /* TODO: start EXPIRED */ }
void wd_feed(wd_t *w, uint32_t now_ms) { (void)w; (void)now_ms; /* TODO */ }
int wd_expired(const wd_t *w, uint32_t now_ms) { (void)w; (void)now_ms; return 0; /* TODO: unsigned subtraction */ }
```

Khởi đầu cho wrapper `ctypes` (khai báo `argtypes` và `restype` cho mọi hàm bạn gọi; `ctypes` âm thầm giả định `int`):

```python
"""corebot/fw_sim.py (starter): the C core inside the simulator loop via ctypes."""
from __future__ import annotations

import ctypes
import pathlib
from dataclasses import dataclass

LIB = pathlib.Path("firmware/build/libfw.so")


@dataclass
class LinkModel:
    """Serial link between firmware and host. Seeded: same seed, same faults."""
    latency_s: float = 0.0012      # 14 bytes at 115200 baud
    drop_prob: float = 0.0
    bitflip_prob: float = 0.0
    seed: int = 0


class FwLib:
    """Thin ctypes wrapper. Declare argtypes/restype for EVERY function you call: ctypes guesses int."""

    def __init__(self, path: pathlib.Path = LIB) -> None:
        self.lib = ctypes.CDLL(str(path))
        self.lib.crc8.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        self.lib.crc8.restype = ctypes.c_uint8
        # TODO: pi_init/pi_step (c_float), fr_encode, wd_* ...

    def crc8(self, data: bytes) -> int:
        return int(self.lib.crc8(data, len(data)))


class FirmwareInTheLoop:
    """1 kHz tick: plant -> encoder counts -> PI -> PWM -> plant; 100 Hz frames to the host."""

    def __init__(self, fw: FwLib, link: LinkModel) -> None:
        self.fw, self.link = fw, link

    def tick(self, t_ms: int) -> None:
        raise NotImplementedError("TODO: advance plant by 1 ms, run decoder, every 10th tick run pi_step and emit a frame")

    def receive_command(self, t_ms: int, v: float, w: float) -> None:
        raise NotImplementedError("TODO: feed the watchdog and set the wheel targets")
```

### Kiểm thử

`firmware/tests/test_core.c` (`assert` thuần, chạy bởi `ctest`; nó qua `-Wall -Wextra -Werror`, nên tham số không dùng trong stub của bạn cần ép kiểu `(void)` như trên):

```c
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../core/fw_api.h"

static void test_crc(void) { assert(crc8((const uint8_t *)"123456789", 9) == 0xF4); }
static void test_qd(void) {
    qd_t q; qd_init(&q, 0);
    const uint8_t fwd[] = {1, 3, 2, 0};          /* 00 -> 01 -> 11 -> 10 -> 00 : one full cycle = +4 */
    for (int r = 0; r < 3; r++) for (int i = 0; i < 4; i++) qd_update(&q, fwd[i]);
    assert(q.count == 12);
    const uint8_t rev[] = {2, 3, 1, 0};
    for (int i = 0; i < 4; i++) qd_update(&q, rev[i]);
    assert(q.count == 8);
    qd_init(&q, 0); q.count = 65534; for (int i = 0; i < 4; i++) qd_update(&q, fwd[i]);
    assert(q.count == 2);                        /* 16-bit wrap */
}
static void test_pi(void) {
    pi_t p; pi_init(&p, 0.12f, 1.5f);
    for (int i = 0; i < 1000; i++) assert(pi_step(&p, 100.0f, 0.0f, 0.01f) == 1.0f);
    assert(p.integ < 1.0f);                      /* no windup */
    pi_init(&p, 0.12f, 1.5f);
    float u = pi_step(&p, 1.0f, 0.0f, 0.01f);
    assert(u > 0.0f && u < 1.0f);
}
static void test_frame(void) {
    uint8_t payload[FR_LEN - 1]; for (int i = 0; i < FR_LEN - 1; i++) payload[i] = (uint8_t)(i * 23);
    payload[3] = FR_SOF; payload[4] = FR_ESC;   /* force stuffing */
    uint8_t wire[FR_MAX_WIRE]; size_t n = fr_encode(payload, FR_LEN - 1, wire);
    assert(n > FR_LEN + 2);
    fr_dec_t d; fr_dec_init(&d); uint8_t out[FR_LEN]; int got = 0;
    for (size_t i = 0; i < n; i++) got += fr_dec_push(&d, wire[i], out);
    assert(got == 1 && memcmp(out, payload, FR_LEN - 1) == 0);
    /* every single-bit flip of the 12-byte logical frame is rejected */
    uint8_t full[FR_LEN]; memcpy(full, payload, FR_LEN - 1); full[FR_LEN - 1] = crc8(payload, FR_LEN - 1);
    for (int i = 0; i < FR_LEN; i++) for (int b = 0; b < 8; b++) {
        uint8_t bad[FR_LEN]; memcpy(bad, full, FR_LEN); bad[i] ^= (uint8_t)(1u << b);
        assert(crc8(bad, FR_LEN - 1) != bad[FR_LEN - 1]);
    }
}
static void test_wd(void) {
    wd_t w; wd_init(&w, 100);
    assert(wd_expired(&w, 0));                   /* zero outputs at boot */
    wd_feed(&w, 1000); assert(!wd_expired(&w, 1099)); assert(wd_expired(&w, 1100));
    wd_feed(&w, 0xFFFFFFF0u); assert(!wd_expired(&w, 5));   /* wrap of the ms counter */
}
int main(void) { test_crc(); test_qd(); test_pi(); test_frame(); test_wd(); puts("firmware core: all tests passed"); return 0; }
```

`tests/acceptance/test_cap02.py` ở dưới. Các kiểm tra gate (những cái phải qua để tốt nghiệp) là `test_step_response`, `test_single_bit_flips_rejected`, `test_resync_and_no_loss` và `test_watchdog`. **Các ngưỡng là giá trị khởi đầu tạm thời (provisional; xem lý do trong comment); hãy siết chặt chúng khi bạn đã có lần chạy tham chiếu của riêng mình.** Lý do một dòng: thời gian xác lập < 0.35 s (khoảng $4\tau$ của động cơ vòng hở, vòng kín phải thắng); vọt lố < 10 % (0.6 rad/s trên 6); sai số xác lập < 2 % (độ chính xác cỡ hiệu chuẩn); vọt lố hồi phục < 15 % (log windup của một vòng tệ trên 200 %); về 0 trong 100 ms (đặc tả an toàn CAP07 là 300 ms cần dư địa cho phần còn lại của stack); thời gian chết $\le20$ ms (một chu kỳ vòng 10 ms cộng liên kết cộng số đếm đầu tiên); jitter p99 $\le5$ ms (nửa chu kỳ vòng); tải liên kết < 50 % (S06: không còn chỗ cho gửi lại ở trên mức đó); trôi odometry < 2 % và sai số hình vuông < 8 cm (CAP03 cần một điểm xuất phát mà EKF có thể hiệu chỉnh).

```python
"""tests/acceptance/test_cap02.py : reads runs/cap02/ and tests the firmware core.
Gate checks are marked GATE. Thresholds are provisional starting values; tighten them once your own reference run exists."""
import csv, json, pathlib, random, shutil, statistics, subprocess
import pytest
from corebot.evalkit import step_metrics, all_single_bit_flips_detected
from corebot.driver import FrameParser, pack_state, stuff, FRAME_LEN

RUNS = pathlib.Path("runs/cap02")

def _csv(name):
    with open(RUNS / name) as f:
        return list(csv.DictReader(f))

def _series(name, col):
    rows = _csv(name)
    return [float(r["t"]) for r in rows], [float(r[col]) for r in rows]

def test_ctest_passes():                                     # GATE-adjacent; skip counts as not passed
    if not (shutil.which("gcc") and shutil.which("cmake")):
        pytest.skip("gcc/cmake missing: install them (make doctor); counts as NOT passed for the gate")
    subprocess.run(["cmake", "-S", "firmware", "-B", "firmware/build"], check=True)
    subprocess.run(["cmake", "--build", "firmware/build"], check=True)
    assert subprocess.run(["ctest", "--test-dir", "firmware/build"]).returncode == 0

@pytest.mark.parametrize("side", ["left", "right"])
def test_step_response(side):                                # GATE
    t, y = _series(f"step_{side}.csv", "omega")
    settle, over, sse = step_metrics(t, y, target=6.0, band=0.02)
    assert settle < 0.35     # a base that needs >0.35 s to reach speed feels sluggish to the tracker (CAP04)
    assert over < 0.10       # 10 % of 6 rad/s is 0.6 rad/s, about 2 cm/s at the wheel: tolerable
    assert sse < 0.02        # 2 % steady-state error: calibration-level accuracy
    counts = [int(r["counts"]) for r in _csv(f"step_{side}.csv")]
    assert any(b < a for a, b in zip(counts, counts[1:])), "16-bit wrap never exercised: start the counter near 65535"

def test_anti_windup():
    t, y = _series("windup.csv", "omega")
    after = [v for tt, v in zip(t, y) if tt > 1.0]            # wheel blocked until t = 1.0 s, then released
    assert (max(after) - 6.0) / 6.0 < 0.15                    # without anti-windup the same log shows >200 %

def test_single_bit_flips_rejected():                        # GATE
    frame = pack_state(7, 65530, 4, 0, 1234, 76)
    assert len(frame) == FRAME_LEN and all_single_bit_flips_detected(frame[:-1])
    for i in range(FRAME_LEN):
        for bit in range(8):
            bad = bytearray(frame); bad[i] ^= 1 << bit
            assert FrameParser().feed(bytes([0x7E]) + bytes(bad) + bytes([0x7E])) == []

def test_resync_and_no_loss():                               # GATE
    rng = random.Random(1000)
    garbage = bytes(rng.randrange(256) for _ in range(50))
    p = FrameParser()
    assert len(p.feed(garbage + stuff(pack_state(1, 1, 2, 0, 10, 76)))) == 1
    p, got = FrameParser(), 0
    for s in range(10_000):
        got += len(p.feed(stuff(pack_state(s, s * 37, s * 91, 0, s, 76))))
    assert got == 10_000
    link = RUNS / "summary.json"
    s = json.loads(link.read_text())["link"]
    assert s["frame_bytes_worst"] * 10 * s["rate_hz"] / s["baud"] < 0.5

def test_watchdog():                                         # GATE
    rows = _csv("watchdog.csv")
    t = [float(r["t_ms"]) for r in rows]; rx = [int(r["cmd_rx"]) for r in rows]
    pwm = [float(r["pwm"]) for r in rows]; w = [float(r["omega"]) for r in rows]
    last = max(tt for tt, r in zip(t, rx) if r and tt < 560)  # last command before the silence
    first_zero = min(tt for tt, p in zip(t, pwm) if tt > last and p == 0.0)
    assert first_zero - last <= 100
    resume = min(tt for tt, r in zip(t, rx) if r and tt > last + 50)
    assert max(v for tt, v in zip(t, w) if tt > resume) <= 1.2 * 6.0

def test_latency_and_jitter():
    dead = [float(r["dead_time_ms"]) for r in _csv("latency.csv")]
    assert max(dead) <= 20.0                                  # one 100 Hz period of wait + link + first count
    dev = sorted(abs(float(r["period_ms"]) - 10.0) for r in _csv("loop_periods.csv"))
    assert dev[int(0.99 * len(dev))] <= 5.0                   # p99 jitter

def test_odometry_calibration():
    o = json.loads((RUNS / "odometry.json").read_text())
    assert o["after"]["straight_drift_pct"] < 2.0
    assert o["after"]["square_err_m"] < 0.08
    assert o["after"]["square_err_m"] < o["before"]["square_err_m"]
    assert len(o["seeds"]) == 3
```

### Kết quả mong đợi

Khi có đủ artefact và firmware đã build, `pytest -q tests/acceptance/test_cap02.py` in ra (thời gian minh họa):

```text
.........                                                                [100%]
9 passed in 3.4s
```

và `runs/cap02/metrics.json` của bạn (do script của chính bạn ghi) nên trông như sau (giá trị minh họa):

```json
{
  "milestone": "CAP02",
  "step": {"left": {"settle_s": 0.19, "overshoot": 0.008, "sse": 0.0001},
           "right": {"settle_s": 0.19, "overshoot": 0.008, "sse": 0.0001}},
  "windup_overshoot": 0.132,
  "protocol": {"bit_flips_rejected": "96/96", "frames_lost_of_10000": 0, "link_load_worst": 0.226},
  "watchdog": {"zero_after_ms": 80, "peak_after_resume_rad_s": 6.07},
  "latency_ms": {"max": 18.4, "jitter_p99": 1.7},
  "odometry": {"before": {"straight_drift_pct": 1.49, "square_err_m": 0.031},
               "after": {"straight_drift_pct": 0.20, "square_err_m": 0.014}}
}
```

Nếu thiếu gcc hoặc cmake bạn sẽ thấy `s` cho bài kiểm thử ctest thay vì dấu chấm: hãy cài chúng, bỏ qua không phải là qua.

### Thử thách mở rộng

**Mở rộng:** thay float bằng số học Q15 trong vòng PI và chứng minh bằng một bài kiểm thử rằng các số đo bước vẫn trong giới hạn và bộ tích phân không bị kẹt ở sai số nhỏ (Bài tập 10). Thêm kế toán số thứ tự (sequence number) để driver báo số frame bị mất.

**Tầng phần cứng tùy chọn (OPTIONAL, không điểm nào phụ thuộc vào nó):** ESP32 + hai động cơ giảm tốc có encoder N20 hoặc JGA25-370 + driver TB6612FNG hoặc DRV8833 + pin Li-ion 2S có cầu chì nối tiếp (danh sách linh kiện theo HW05 và HW03). Build cùng `core/` bằng `pio run -e esp32`, phát lại bài kiểm thử bước qua serial bằng pySerial (script ở phần Thực hành với thư viện), và so sánh số đo bước thật với mô phỏng; chờ đợi khác biệt do ma sát, sụt áp pin và PPR encoder thật. An toàn trước hết: cầu chì, giới hạn dòng của nguồn bàn, **bánh nhấc khỏi mặt đất ở các lần chạy đầu**, giữ ở mức 12 V hoặc thấp hơn, và theo các quy tắc điện của [HW03](/lessons/HW03). Chỉ phần cứng không bao giờ thay thế một gate bị trượt.

### Thực hành với thư viện

Biên dịch cùng core bằng nền tảng `native` của PlatformIO (host, kiểm thử Unity) và một môi trường `esp32`. Rồi nối đế với ROS 2 bằng micro-ROS hoặc `ros2_control` thay vì liên kết của bạn (nghiên cứu cách hardware interface của chúng bọc `read()`/`write()`; lý do bạn tự viết trước là để hiểu chúng giấu gì).

```ini
; firmware/platformio.ini : the SAME core/ for the host (native) and an optional ESP32
[platformio]
src_dir = core

[env:native]
platform = native
build_flags = -Wall -Wextra -DFW_HOST=1
test_framework = unity

[env:esp32]
platform = espressif32
board = esp32dev
framework = arduino
build_flags = -Wall -Wextra
```

Kiểm tra vòng lặp (loopback) của việc đóng khung qua một cổng nối tiếp thật hoặc ảo bằng pySerial (Linux, `socat` tạo cặp cổng):

```python
# Needs: pip install pyserial ; socat for the virtual pair (Linux): socat -d -d pty,raw,echo=0 pty,raw,echo=0
# Replays the CAP02 state frames over a (virtual or real) serial port and checks the parser end to end.
import sys

import serial  # pyserial

from corebot.driver import FrameParser, pack_state, stuff

tx = serial.Serial(sys.argv[1], 115200, timeout=0.1)   # e.g. /dev/pts/3
rx = serial.Serial(sys.argv[2], 115200, timeout=0.1)   # e.g. /dev/pts/4 (or the ESP32: /dev/ttyUSB0)
parser, seen = FrameParser(), 0
for seq in range(200):
    tx.write(stuff(pack_state(seq, seq * 14, seq * 14, 0, seq * 10, 76)))
    seen += len(parser.feed(rx.read(64)))
print("frames seen:", seen, "rejected:", parser.rejected)
assert seen >= 195, "link lost frames: check cabling, baud rate and the stuffing of 0x7E/0x7D"
```

## Kiểm chứng

Kiểm tra số bằng tay trước khi tin các đồ thị: số đếm mỗi vòng (1496), bước lượng tử (0.42 rad/s ở 100 Hz), giá trị kiểm tra CRC (`0xF4`), tải liên kết (12.2 % điển hình). Kiểm chứng firmware như firmware: `ctest` phải qua trên bản build sạch với `-Wall -Wextra -Werror`; mỗi bài kiểm thử phải thất bại trước khi bạn làm hỏng mã (đảo một dấu trong bảng chuyển trạng thái và thấy bài kiểm thử bộ giải mã thất bại). Kiểm chứng tuyên bố "an toàn lúc khởi động" bằng cách đọc log: PWM bằng 0 cho tới lệnh đầu tiên. Kiểm chứng tuyên bố "sống sót qua rác" bằng các bài kiểm thử vét cạn và ngẫu nhiên trong `test_cap02.py`.

**Chấm điểm và tốt nghiệp.** CAP02 có giá trị **12 trên 100** điểm. Điểm gồm 60 % tự động (tỉ lệ có trọng số của các kiểm tra, gate đánh dấu ở trên) và 40 % rubric của người (0 đến 4 mỗi tiêu chí): chất lượng mã C (không cấp phát động trong đường điều khiển, số nguyên độ rộng cố định, mọi float đều có lý do), mặc định an toàn (đầu ra bằng 0 lúc khởi động và khi lệnh cũ), tài liệu về định thời và đơn vị, nhận dạng hệ thống trung thực. Tốt nghiệp đòi hỏi mọi kiểm tra gate của mọi milestone qua, mọi milestone từ 60 trở lên và tổng có trọng số từ 70 trở lên. Một gate trượt giữ CAP02 ở trạng thái "đang làm" trong ứng dụng nhưng không khóa các chủ đề sau. Một prompt tự xem xét bạn có thể đưa cho một LLM cùng với `firmware/core/*` và `runs/cap02/metrics.json` (không phải nhận xét của chính bạn): *"Review this embedded C for a wheel speed controller. List any dynamic allocation, integer promotion or wrap bugs, missing zero-at-boot behaviour and any place a stale command could move a motor. Score 0 to 4 against: code quality, safety defaults, documentation of timing and units, honest sysid, and cite lines."*

## Lỗi thường gặp

- Encoder của một bánh bị đảo dấu: robot quay tại chỗ thay vì đi thẳng; bài kiểm thử bước từng bánh qua, đường thẳng 10 m thì không.
- Số học `uint16_t` làm trong `int`: việc quay vòng tạo ra một đỉnh nhọn $\pm65\,5xx$ số đếm và một tốc độ khổng lồ (Bài tập 6).
- Windup bộ tích phân sau khi kẹt hoặc một lệnh bão hòa (Bài tập 7).
- ISR (hoặc tick 1 kHz) làm quá nhiều: in ra, định dạng dấu phẩy động hoặc chặn trong đường điều khiển.
- `float` trên MCU và `double` trên host: khác biệt số nhỏ làm hỏng so sánh khớp từng bit; hãy so sánh bằng dung sai.
- Byte stuffing lệch một: frame có `0x7E` bên trong là frame hỏng, một trong 256 frame, nên các bài kiểm thử ngẫu nhiên phải đủ dài để chạm vào nó.
- Tràn buffer của parser với rác, hoặc parser không bao giờ đồng bộ lại sau khi mất một dấu phân cách.
- Tốc độ vòng lặp gây aliasing với lượng tử hóa encoder: ước lượng tốc độ 1 kHz từ số đếm hầu như luôn là 0 hoặc một số đếm (Bài tập 1).
- Quên PWM = 0 lúc khởi động và khi dữ liệu cũ; quên reset bộ tích phân khi watchdog kích hoạt.
- Hiệu chuẩn track width trước bán kính bánh, khiến hiệu chuẩn hướng hấp thụ sai số bán kính.

## Phương án khác và đánh đổi

Bạn có thể bỏ C và viết vòng tốc độ bằng Python: viết nhanh hơn, nhưng nó giấu đúng những vấn đề milestone này dạy (độ rộng số nguyên, quay vòng, định thời, giới hạn buffer) và không nạp được vào MCU. Bạn có thể dùng đóng khung COBS (chi phí cố định một byte mỗi 254, độ dài dự đoán được) thay vì byte stuffing kiểu HDLC (độ dài thay đổi, đơn giản hơn); bạn có thể dùng CRC 16 bit cho frame dài hơn. Odometry có thể được tinh chỉnh bằng gyro ở CAP03; ở đây odometry chỉ dùng bánh là baseline bạn phải vượt. micro-ROS cho bạn một node ROS 2 trên MCU với giá là toolchain nặng hơn; `ros2_control` cho một hardware interface chuẩn trên host. Gazebo hay một robot thật sẽ cho bạn ma sát và trượt mà bạn không có trong MuJoCo với bánh lý tưởng; tầng phần cứng tồn tại để cho thấy khoảng cách đó.

## Vận dụng và ghi nhớ

**Milestone này chuẩn bị cho:** CAP03 (odometry bạn hiệu chuẩn là đầu vào dự đoán của EKF), CAP04 (bộ bám đường ra lệnh `v`, `w` qua liên kết này), CAP07 (bộ giám sát an toàn gửi frame dừng trực tiếp tới watchdog này), CAP08 (bản twin đổi bán kính bánh và track width của bạn; script hiệu chuẩn của bạn được dùng lại cho khoảng cách mô phỏng với thực).

Câu hỏi ôn cho tuần sau, không xem ghi chú:

1. Viết delta bộ đếm an toàn khi quay vòng bằng C với đúng các kiểu số nguyên.
2. Nêu ba lý do một frame có thể bị từ chối, và parser làm gì sau mỗi lý do.
3. Vì sao bộ tích phân phải reset khi watchdog kích hoạt?
4. Suy ra bước lượng tử tốc độ cho một tốc độ vòng lặp cho trước và giải thích vì sao cửa sổ dài hơn giúp ích.
5. Thứ tự hiệu chuẩn bán kính bánh và track width là gì, và vì sao?

## Đáp án bài tập

1. $N=4\cdot11\cdot34=1496$ số đếm mỗi vòng bánh. Ở 6 rad/s: $6/(2\pi)=0.955$ vòng/s, tức 1428 số đếm/s, nên 14.3 số đếm mỗi 10 ms. Bước lượng tử $2\pi/(1496\cdot0.01)=0.42$ rad/s, 7 % của 6 rad/s.
2. Điển hình: $14\cdot10\cdot100/115200=12.2\%$. Xấu nhất (26 byte): $22.6\%$. Ở 1 kHz: $121\%$ điển hình, bất khả thi; dữ liệu vòng tốc độ nên được tóm tắt ở 100 Hz.
3. Bắt đầu với $c=0$. Byte `0x01`: $c=0x01$; bảy lần dịch cho 0x80, lần dịch thứ tám có bit cao được đặt, nên $c=(0x80\ll1)\&0xFF\oplus0x07=0x07$. Byte `0x02`: $c=0x07\oplus0x02=0x05$; tám lần dịch cho 0x0A, 0x14, 0x28, 0x50, 0xA0, rồi (bit cao đặt) 0x40 xor 0x07 = 0x47, rồi 0x8E, rồi (bit cao đặt) 0x1C xor 0x07 = 0x1B. CRC là `0x1B`; hãy xác nhận bằng `crc8` của bạn. Giá trị kiểm tra của `b"123456789"` là `0xF4`; một giá trị đã công bố cho bạn biết quy ước đa thức, giá trị đầu và đảo bit có khớp với phía bên kia không.
4. Khoảng 80 ms. Jitter của host: timeout phải là vài chu kỳ (30 ms là 3 chu kỳ) để một lệnh trễ không làm robot dừng (dừng nhầm được kiểm thử ở CAP07: tối đa 5 % các episode danh định). Phanh: ở 0.5 m/s robot đi $0.5\cdot0.08=4$ cm trước khi PWM bị cắt, cộng quán tính. Giới hạn đặc tả (về 0 trong 100 ms) để lại 20 ms dư cho tick 1 ms và liên kết. Sau lệnh cuối: 4 cm.
5. Xấu nhất: chờ tick 10 ms kế tiếp của firmware (10 ms) + liên kết $14\cdot10/115200=1.2$ ms + số đếm đầu tiên 6.8 ms = 18.0 ms, dưới 20 ms với 2 ms dư; bất kỳ bộ đệm nào thêm vào (bộ định thời độ trễ 16 ms của USB-serial) sẽ phá nó. Số đếm đầu tiên: duty $0.12\cdot6=0.72$; gia tốc $K_u u/\tau=20\cdot0.72/0.08=180$ rad/s$^2$; một số đếm là $2\pi/1496=4.2\times10^{-3}$ rad; $t=\sqrt{2\cdot4.2\times10^{-3}/180}=6.8$ ms.
6. Các toán hạng `uint16_t` được thăng cấp lên `int` (32 bit) trước phép trừ, nên $4-65530=-65526$ chính xác và không có quay vòng. Sửa: `int16_t delta = (int16_t)(uint16_t)(cur - prev);` hoặc `(uint16_t)(cur - prev)` rồi kiểm tra nửa dải. 65500 sang 40: $(40-65500)\bmod65536=76$, nên $+76$.
7. Sai số 6 rad/s nhân $K_i=1.5$ nhân 1 s $=9.0$, gấp chín lần dải duty đầy đủ, nên sau khi thả đầu ra vẫn bão hòa cho tới khi bộ tích phân được gỡ bởi sai số âm: một cú vọt lố dài. Tích phân có điều kiện ngừng cộng khi đầu ra bão hòa, nên $I$ ở gần $1-K_p\cdot6\approx0.3$. Phương án khác: back-calculation, đưa hiệu giữa đầu ra đã bão hòa và đầu ra thô vào bộ tích phân với hệ số $1/T_t$; nó cần một hệ số theo dõi được chỉnh (trong một mô phỏng nháp với các hệ số này, các hệ số back-calculation từ 5 đến 40 để lại vọt lố 24 đến 121 %).
8. $r=0.0330\cdot10/9.85=0.03350$ m. $b=0.160\cdot3667.5/3600=0.16300$ m. Track width quan trọng hơn cho hình vuông: bốn khúc quay 90 độ của nó tích lũy sai hướng (1.9 phần trăm của 360 độ là khoảng 7 độ nếu không sửa), và sai hướng xoay mọi đoạn sau đó; sai bán kính chỉ co giãn mỗi cạnh 1.5 %.
9. $20/(2\pi)\cdot1496=4762$ số đếm/s, 4.8 cạnh mỗi ms mỗi bánh. Một tick 1 kHz thấy tối đa một mẫu mỗi ms, nên sẽ bỏ lỡ cạnh; firmware thật dùng ngắt cạnh hoặc một bộ đếm xung phần cứng (ESP32 có sẵn) và tick 1 kHz chỉ đọc số đếm đã tích lũy. Simulator nên tích lũy số đếm ở bước plant 1 ms (như trong mô phỏng mẫu) và chỉ đưa chuỗi A/B thô vào bộ giải mã trong các bài kiểm thử đơn vị.
10. Gia số $=K_ieT_s=0.015e$. Một LSB là $3.05\times10^{-5}$, nên $e<0.002$ rad/s cho ít hơn một LSB và phép cắt cụt làm tròn nó về 0: bộ tích phân bị kẹt và vòng giữ một sai số xác lập nhỏ (khoảng 0.002 rad/s, 0.03 % của 6 rad/s: vô hại ở đây, nhưng thấy được dưới dạng dao động); làm tròn tới số gần nhất hoặc một bộ cộng dồn rộng hơn (Q31) tránh được. ESP32 có FPU độ chính xác đơn, nên `float` trong vòng 100 Hz là hợp lý; nó sẽ không hợp lý trên Cortex-M0.
11. Mong đợi: với rớt 1 % cửa sổ 50 ms cho thấy các chỗ lõm nhỏ và thời gian xác lập tăng thêm một hai chu kỳ; một bit bị lật bị từ chối (CRC) và hành xử như một lần rớt; +5 ms độ trễ làm giảm dư địa của kiểm tra thời gian chết (18.0 + 5 = 23 ms trượt). Ca biên: với timeout bằng chu kỳ lệnh, mọi lệnh trễ đều làm robot dừng. Một quan sát bác bỏ: một frame được chấp nhận với giá trị bộ đếm sai, hoặc PWM khác 0 sau 100 ms kể từ lệnh cuối.

## Đọc thêm

- [PlatformIO native platform](https://docs.platformio.org/en/latest/platforms/native.html) - biên dịch và kiểm thử đơn vị lõi firmware trên host.
- [Python ctypes](https://docs.python.org/3/library/ctypes.html) - gọi một thư viện chia sẻ, argtypes và restype.
- [CTest manual](https://cmake.org/cmake/help/latest/manual/ctest.1.html) - đăng ký và chạy các bài kiểm thử C.
- [Cyclic redundancy check (Wikipedia)](https://en.wikipedia.org/wiki/Cyclic_redundancy_check) - đa thức, giá trị kiểm tra và phát hiện lỗi.
- [Vulcanexus micro-ROS documentation](https://micro.vulcanexus.org/docs/) - phần Thực hành với thư viện cho liên kết MCU với ROS 2.
- [ros2_control (Jazzy)](https://control.ros.org/jazzy/index.html) - hợp đồng hardware interface trên host.
- [pySerial documentation](https://pyserial.readthedocs.io/en/latest/) - cổng, timeout và miniterm.
- Video: Articulated Robotics, *The Ultimate Guide to using Motors in Robotics*; Texas Instruments, *Interfacing with Quadrature Encoders*; Articulated Robotics, *Could this button control your robot? (Beginner micro-ROS Tutorial)*.
