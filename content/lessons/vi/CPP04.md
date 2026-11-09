---
{"title": "Class và OOP: đóng gói, interface và invariant", "summary": "Thiết kế các class mà các thao tác public không bao giờ để lại trạng thái không hợp lệ, và dùng abstract interface cho những hành vi thay đổi được.", "objectives": ["Phát biểu một class invariant và chỉ ra rằng constructor thiết lập nó còn mọi hàm thành viên public đều bảo toàn nó.", "Quyết định giữa struct và class, dữ liệu public và accessor, hàm thành viên và hàm tự do (free function).", "Thiết kế một abstract interface với virtual destructor và tránh slicing.", "Nhận ra khi nào kế thừa vi phạm tính thay thế được (substitutability) và chọn composition hoặc template thay thế."]}
---
## Vì sao điều này quan trọng

Phần mềm robot đầy những giá trị chỉ có nghĩa trong một khoảng: góc khớp nằm giữa các giới hạn của nó, một quaternion đơn vị, một hệ số khuếch đại phải không âm, một bước thời gian lớn hơn không. Nếu chúng là các field public trong một `struct`, bất kỳ dòng code nào ở đâu cũng có thể lưu 99 radian vào một khớp mà về mặt vật lý dừng ở 1.5, và bug xuất hiện muộn hơn, xa nguyên nhân, có thể là một lỗi phần cứng. Class sửa chuyện này bằng cách biến cách *duy nhất* để đổi trạng thái thành một hàm kiểm tra quy tắc. Nửa sau của bài, interface, là cách bạn đổi hành vi (bộ điều khiển P sang PID, driver giả lập sang driver thật) mà không phải viết lại phía gọi. Cùng nhau chúng là nền tảng của hầu hết thư viện robotics C++: hardware interface của ROS 2, planner của MoveIt, và plugin controller đều phơi ra những abstract interface nhỏ trên các class bảo vệ invariant của chúng.

## Trực giác

*Invariant* là một mệnh đề đúng mỗi khi quyền điều khiển nằm ngoài các hàm thành viên của class. "Vị trí nằm trong giới hạn và tốc độ không vượt quá mức tối đa" là một invariant. Class là một pháo đài nhỏ: constructor xây dựng invariant, mọi hàm public được phép giả định nó đúng khi vào và phải khôi phục nó khi ra, và dữ liệu private ngăn người ngoài chạm vào nó. Nếu một yêu cầu sẽ phá invariant, hàm từ chối (trả `false` hoặc throw) và để trạng thái không đổi.

*Interface* là một hợp đồng không có trạng thái: "đưa tôi một sai số, tôi đưa bạn một lệnh". Phía gọi phụ thuộc vào hợp đồng; phía cài đặt được tự do khác nhau. Vì phía gọi giữ một reference tới abstract base, override đúng được chọn lúc chạy thông qua bảng ảo (virtual table).

Trong một driver cánh tay sáu khớp chạy 1 kHz, một mảng lệnh từ planner đến mỗi mili giây. Một khớp cổ tay giới hạn $\pm2.9$ rad mà nhận 7,3 rad thì vượt điểm chặn hơn 4 rad, và lỗi không hiện ra ở dòng đã lưu con số đó mà ở chỗ khớp về sau đập vào điểm chặn hoặc bộ điều khiển phân kỳ. Nếu cách duy nhất để ghi mục tiêu của khớp là một hàm kiểm tra giới hạn, lệnh xấu bị từ chối ngay tại dòng đã phát ra nó, kèm tên và giá trị trong log. Đó là ý nghĩa của invariant: lỗi nổi lên tại nơi nó sinh ra.

Hãy dự đoán trước khi đọc tiếp. Một `Gripper` giữ độ mở `width_` ở dạng private, và setter của nó kẹp mọi yêu cầu vào khoảng 0 đến 80 mm. Lớp này còn có một accessor public `double& width() { return width_; }`. Bên gọi vẫn có thể làm gripper giữ 120 mm không, và bằng bao nhiêu dòng code? Hãy quyết định, rồi đọc tiếp; đáp án nằm sau hình.

Có ba trực giác sai hay gặp. *Private nghĩa là an toàn*: `private` là kiểm tra tên ở thời điểm biên dịch, và nó chỉ bảo vệ invariant nếu không có hàm public nào đưa ra tham chiếu ghi được vào dữ liệu. *Kế thừa là để tái sử dụng*: một đối tượng dẫn xuất được hứa hẹn ở mọi nơi cần base, nên chỉ kế thừa khi kiểu dẫn xuất giữ mọi lời hứa của base; tái sử dụng code thuộc về composition. *Lời gọi virtual quá chậm cho vòng điều khiển*: một lời gọi gián tiếp tốn vài nano giây, khoảng 0,0005 % của chu kỳ điều khiển 1 ms.

![Class JointState với trạng thái private và các thao tác public như một cánh cổng, và một abstract interface Controller với hai cài đặt](/lesson-figures/CPP04.svg)

*Các hàm public là cánh cửa duy nhất vào trạng thái private; một Controller trừu tượng cho phép phía gọi dùng bất kỳ cài đặt nào.*

Đáp án cho dự đoán: được, chỉ một dòng, `g.width() = 120;`: lệnh ghi đi qua tham chiếu được trả về và phép kẹp trong setter không bao giờ được hỏi tới. Invariant $0\le \text{width}\le 80$ chỉ đúng nếu mọi đường tới dữ liệu đều đi qua một hàm có kiểm tra, nên accessor phải trả về một giá trị hoặc một tham chiếu `const`.

## Lý thuyết và suy dẫn

### Invariant và mẫu chứng minh

Gọi $I(s)$ là invariant trên trạng thái $s$. Một class là đúng nếu

1. **Thiết lập (Establish):** sau mọi constructor thành công, $I$ đúng; một constructor thất bại sẽ throw, nên không có đối tượng dựng dở nào tồn tại.
2. **Bảo toàn (Preserve):** với mỗi thao tác public $f$, nếu $I(s)$ đúng trước lời gọi thì $I(s')$ đúng sau đó, dù $f$ trả về bình thường, trả về mã lỗi, hay throw.

Bằng quy nạp theo số lời gọi, $I$ đúng với mọi trạng thái có thể đạt tới. Với `JointState` có giới hạn $[l,h]$ và giới hạn tốc độ $v_{\max}$: $I(q,v) \equiv l\le q\le h \;\wedge\; |v|\le v_{\max}$ (đều hữu hạn). `try_set_position(q', dt)` chỉ đổi trạng thái nếu $l\le q'\le h$ và $|q'-q|/dt\le v_{\max}$; khi đó $v'=(q'-q)/dt$ thỏa $I$. Nếu không, nó không đổi gì, nên $I$ đúng hiển nhiên.

Hãy chú ý chi tiết cài đặt quan trọng: viết phép kiểm tra là `!(lo <= q && q <= hi)` hoặc kiểm tra tính hữu hạn trước. Với `NaN`, mọi phép so sánh đều sai, nên `if (q < lo || q > hi) reject` sẽ chấp nhận nó.

**Ví dụ.** Một driver động cơ chỉ nhận duty cycle trong $[0, 0.85]$. Lớp dưới đây thiết lập invariant đó ngay trong constructor, và một phép thử thứ hai viết là `!(d < 0 || d > 0.85)` được so sánh với nó trên các đầu vào 0.5, 0.9 và NaN (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Mỗi phép thử chấp nhận đầu vào nào?

```cpp
#include <cstdio>
#include <limits>
#include <stdexcept>
// Invariant: 0 <= duty <= 0.85 (the driver's limit), never NaN.
class DutyCycle {
  double d_;
 public:
  explicit DutyCycle(double d) : d_(d) {
    if (!(0.0 <= d && d <= 0.85)) throw std::invalid_argument("duty out of range");
  }
  double value() const { return d_; }
};
bool naive_ok(double d) { return !(d < 0.0 || d > 0.85); }   // wrong test
int main() {
  const double nan = std::numeric_limits<double>::quiet_NaN();
  double tests[] = {0.5, 0.9, nan};
  for (double d : tests) {
    bool ok = true;
    try { DutyCycle x(d); } catch (const std::invalid_argument&) { ok = false; }
    std::printf("duty %-5g  constructor accepts: %d   naive range test accepts: %d\n", d, ok, naive_ok(d));
  }
}
```

**Lời giải.** Constructor dùng dạng *khẳng định* `0 <= d && d <= 0.85` rồi phủ định nó, nên NaN (mọi phép so sánh với nó đều sai) bị từ chối, và bước establish của chứng minh đúng với mọi đầu vào: 0.5 được chấp nhận, 0.9 và NaN bị từ chối. Phép thử dùng so sánh phủ định `!(d < 0 || d > 0.85)` đồng ý trên 0.5 và 0.9, nhưng với NaN cả hai phép so sánh đều sai nên nó chấp nhận: nó sẽ lưu một giá trị ngoài invariant, và bước preserve của mọi lời gọi sau đó sẽ được chứng minh cho một trạng thái chưa từng thỏa $I$. Chương trình in ra:

```text
duty 0.5    constructor accepts: 1   naive range test accepts: 1
duty 0.9    constructor accepts: 0   naive range test accepts: 0
duty nan    constructor accepts: 0   naive range test accepts: 1
```

```explore
{
  "title": "Which updates does the gate accept?",
  "title_vi": "Cổng chấp nhận những cập nhật nào?",
  "prompt": "Predict first: from q = 0.15 with vmax = 2 rad/s, can the joint reach q' = 0.9 in dt = 0.1 s? What is the smallest dt that works? Then drag q' and dt to test your answer, and raise vmax to see the accepted region widen.",
  "prompt_vi": "Dự đoán trước: từ q = 0.15 với vmax = 2 rad/s, khớp có đạt tới q' = 0.9 trong dt = 0.1 s không? dt nhỏ nhất dùng được là bao nhiêu? Rồi kéo q' và dt để kiểm tra, và tăng vmax để thấy vùng chấp nhận rộng ra.",
  "params": [
    { "name": "q0", "label": "current q", "label_vi": "q hiện tại", "min": -1.5, "max": 1.5, "step": 0.05, "value": 0.15, "unit": "rad" },
    { "name": "qn", "label": "target q'", "label_vi": "đích q'", "min": -1.7, "max": 1.7, "step": 0.05, "value": 0.9, "unit": "rad" },
    { "name": "dt", "label": "time step dt", "label_vi": "bước thời gian dt", "min": 0.05, "max": 1, "step": 0.025, "value": 0.1, "unit": "s" },
    { "name": "vmax", "label": "speed limit vmax", "label_vi": "giới hạn tốc độ vmax", "min": 0.5, "max": 4, "step": 0.25, "value": 2, "unit": "rad/s" }
  ],
  "let": [
    { "name": "speed", "expr": "abs(qn - q0) / dt" },
    { "name": "dtmin", "expr": "abs(qn - q0) / vmax" },
    { "name": "ok", "expr": "ifpos(vmax - speed + 0.0000001, ifpos(1.5 - abs(qn) + 0.0000001, 1, 0), 0)" }
  ],
  "plot": {
    "x": { "name": "x", "min": -1.7, "max": 1.7, "label": "target q' (rad)", "label_vi": "đích q' (rad)" },
    "y": { "label": "dt (s)", "label_vi": "dt (s)", "min": 0, "max": 1 },
    "series": [
      { "expr": "abs(x - q0) / vmax", "label": "dt = |q' - q| / vmax (accepted above)", "label_vi": "dt = |q' - q| / vmax (chấp nhận phía trên)", "color": "orange" }
    ],
    "points": [
      { "x": "qn", "y": "dt", "label": "your call", "label_vi": "lời gọi của bạn", "color": "blue" }
    ]
  },
  "readouts": [
    { "label": "speed |q' - q| / dt", "label_vi": "tốc độ |q' - q| / dt", "expr": "speed", "unit": "rad/s", "digits": 3 },
    { "label": "smallest legal dt", "label_vi": "dt nhỏ nhất hợp lệ", "expr": "dtmin", "unit": "s", "digits": 3 },
    { "label": "accepted (1 yes, 0 no; limits +-1.5)", "label_vi": "được chấp nhận (1 có, 0 không; giới hạn +-1.5)", "expr": "ok", "unit": "", "digits": 0 }
  ]
}
```

*Hình: đường cam là biên $dt=|q'-q|/v_{\max}$; các lời gọi phía trên nó thỏa phép thử tốc độ, còn phép thử vị trí $|q'|\le1.5$ là điều kiện thứ hai mà ô số liệu cộng thêm. Giá trị mặc định tái hiện bước 2 của ví dụ có lời giải.*

### Quy tắc thiết kế từ Core Guidelines

- Dùng `struct` khi dữ liệu *không* có invariant (mọi tổ hợp member đều hợp lệ), ví dụ `struct Pose2D { double x, y, theta; };`. Dùng `class` với dữ liệu private khi có invariant (C.2, C.8).
- Một constructor nên tạo một đối tượng *được khởi tạo đầy đủ và hợp lệ* hoặc throw (C.41, C.42). Tránh các hàm `init()` hai pha, vì chúng cho phép đối tượng không hợp lệ tồn tại.
- Đừng trả về reference hoặc con trỏ không-`const` tới member private; chúng vượt qua cánh cổng. Trả về giá trị hoặc `const&`.
- Ưu tiên hàm không phải thành viên cho các thao tác không cần truy cập private, để class nhỏ gọn (C.4).
- Đánh dấu constructor một đối số là `explicit` (C.46) để ngăn các chuyển đổi ngầm như `JointState j = 0.5;`.
- Mỗi hàm thành viên là `const` trừ khi nó thay đổi trạng thái.

**Ví dụ.** `Pose2D` không có invariant (ba số bất kỳ đều là một pose), nên nó vẫn là `struct`; `JointAngle` có invariant $|a|\le\pi$, nên là một class với constructor `explicit` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Chương trình in ra gì, và `report(0.75)` có được chấp nhận thay cho `report(JointAngle{0.75})` không?

```cpp
#include <cstdio>
struct Pose2D { double x, y, theta; };                 // no invariant: a struct
class JointAngle {                                     // invariant: |a| <= pi, so a class
  double a_;
 public:
  explicit JointAngle(double a) : a_(a) {}
  double value() const { return a_; }
};
void report(JointAngle a) { std::printf("angle = %.2f rad\n", a.value()); }
int main() {
  Pose2D p{1.0, 2.0, 0.5};
  std::printf("pose = (%.1f, %.1f, %.1f)\n", p.x, p.y, p.theta);
  report(JointAngle{0.75});
}
```

**Lời giải.** Viết `report(0.75)` thay cho `report(JointAngle{0.75})` bị từ chối lúc biên dịch: `could not convert ‘7.5e-1’ from ‘double’ to ‘JointAngle’`. Nếu không có `explicit`, con số trần sẽ được chuyển đổi lặng lẽ, và một giá trị theo độ hay một `double` dành cho tham số khác sẽ chảy vào class mà không bị kiểm tra (C.46). Chương trình với lời gọi tường minh in ra:

```text
pose = (1.0, 2.0, 0.5)
angle = 0.75 rad
```

### Kiểm soát truy cập và `const`: compiler thực thi điều gì

Kiểm soát truy cập là một phép kiểm tra lúc biên dịch trên *tên*. Một member private chỉ có thể được gọi tên bởi member và friend của class chứa nó ([class.access.general] ¶1); phép kiểm tra là theo class chứ không theo đối tượng, nên một hàm thành viên có thể đọc dữ liệu private của một đối tượng khác cùng class (như mọi copy constructor và `operator==` vẫn làm), và không có gì lúc chạy ngăn một debugger hay một con trỏ xấu ghi đè các byte đó. Vì vậy `private` mang lại một *danh sách hữu hạn các chỗ* cần rà soát khi invariant bị phá: các hàm thành viên và friend. Mọi hàm public trả về con trỏ hay tham chiếu không `const` tới dữ liệu private, và mọi `friend`, đều kéo dài danh sách đó, nên guidelines tránh chúng (C.9, C.133).

Một hàm thành viên `const` hứa không đổi trạng thái quan sát được của đối tượng, và compiler thực thi điều đó với các data member không phải `mutable`: bên trong hàm, `this` có kiểu `const T*`, nên phép gán vào member là lỗi (cppreference: cv type qualifiers, `mutable` specifier). Điểm khác biệt quan trọng là giữa tính const *bitwise* và *logical*. Một cache, một mutex hay một bộ đếm số lần đọc không đổi giá trị mà bên gọi nhìn thấy, nên có thể khai báo `mutable` và được ghi từ hàm `const`; một member là một phần của giá trị trừu tượng thì không được như vậy. Overload theo `const` cho phép một tên phục vụ cả bên gọi chỉ đọc lẫn bên gọi ghi được (`T& at(i)` và `const T& at(i) const`), và tham chiếu `const` là cách rẻ nhất để trao quyền đọc (F.16, Con.2).

**Ví dụ.** Một odometer đếm số lần đọc tổng của nó bằng một bộ đếm `mutable`, và được nhìn qua một tham chiếu `const` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Hai lần đọc qua tham chiếu `const` có biên dịch được không, tổng và số lần đọc là bao nhiêu, và chuyện gì xảy ra nếu gọi `add()` qua cùng tham chiếu đó?

```cpp
#include <cstdio>
class Odometer {
  double total_ = 12.5;
  mutable int reads_ = 0;                // bookkeeping, not part of the observable value
 public:
  double total() const { ++reads_; return total_; }
  void add(double d) { total_ += d; }
  int reads() const { return reads_; }
};
int main() {
  Odometer o;
  const Odometer& view = o;
  double a = view.total() + view.total();
  std::printf("sum of two reads = %.1f, reads counted = %d\n", a, view.reads());
}
```

**Lời giải.** Cả hai lời gọi biên dịch được vì `total()` là `const` và bộ đếm là `mutable`; tổng là $12{,}5+12{,}5=25{,}0$ và có 2 lần đọc được đếm. Gọi hàm thay đổi `add()` qua cùng tham chiếu đó bị từ chối: `passing ‘const Odometer’ as ‘this’ argument discards qualifiers [-fpermissive]`. Chương trình in ra:

```text
sum of two reads = 25.0, reads counted = 2
```

### Interface và virtual dispatch

Một abstract base class khai báo các hàm thuần ảo (`= 0`) và một virtual destructor:

```cpp
struct Controller {
  virtual ~Controller() = default;
  virtual double compute(double error) const = 0;
};
```

- **Virtual destructor**: xóa một đối tượng dẫn xuất qua con trỏ base mà không có nó là undefined behavior (C.35).
- **`override`**: để compiler kiểm tra rằng bạn thực sự override một thứ gì đó.
- **Slicing**: truyền `Controller c` theo giá trị chỉ copy subobject base, ở đây còn không dựng được vì nó trừu tượng; với base cụ thể, nó lặng lẽ mất hành vi dẫn xuất. Truyền bằng reference hoặc con trỏ (C.145) và xóa các phép copy của các base đa hình (C.67).
- **Chi phí**: một lời gọi ảo là một lời gọi gián tiếp qua vtable, thường vài nano giây và không inline được. Nó không đáng kể ở điều khiển 1 kHz và đáng kể trong một vòng lặp qua $10^8$ phần tử.

**Ví dụ.** Một bộ điều khiển PID có ba hệ số bị xóa qua một con trỏ base. Trước hết là một base không có destructor virtual, dựng bằng g++ 11.4.0 và `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`. Compiler và AddressSanitizer báo gì, và điều gì đổi khi có `virtual ~Controller()`?

```cpp
#include <cstdio>
struct Controller { virtual double compute(double e) const = 0; ~Controller() {} };       // no virtual destructor
struct PID : Controller { double gains[3] = {1, 0.1, 0.01}; double compute(double e) const override { return gains[0] * e; } };
int main() { Controller* c = new PID; std::printf("%g\n", c->compute(2.0)); delete c; }
```

**Lời giải.** Compiler cảnh báo lúc biên dịch và AddressSanitizer báo lúc chạy rằng một đối tượng 32 byte bị giải phóng như một đối tượng 8 byte: `~PID` và phần dẫn xuất không bao giờ được xử lý. Bản build và lần chạy cho ra (báo cáo được rút gọn):

```text
warning: deleting object of abstract class type ‘Controller’ which has non-virtual destructor will cause undefined behavior [-Wdelete-non-virtual-dtor]
==PID==ERROR: AddressSanitizer: new-delete-type-mismatch on 0x... in thread T0:
object passed to delete has wrong type:
size of the allocated type:   32 bytes;
size of the deallocated type: 8 bytes.
SUMMARY: AddressSanitizer: new-delete-type-mismatch ../../../../src/libsanitizer/asan/asan_new_delete.cpp:172 in operator delete(void*, unsigned long)
```

**Ví dụ.** Với `virtual ~Controller()` (C.35), cùng phép xóa đi qua một `std::unique_ptr<Controller>` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Những destructor nào chạy, và theo thứ tự nào?

```cpp
#include <cstdio>
#include <memory>
struct Controller { virtual ~Controller() { std::puts("~Controller"); } virtual double compute(double e) const = 0; };
struct PID : Controller { double gains[3] = {1, 0.1, 0.01}; ~PID() override { std::puts("~PID"); } double compute(double e) const override { return gains[0] * e; } };
int main() { std::unique_ptr<Controller> c = std::make_unique<PID>(); std::printf("%g\n", c->compute(2.0)); }
```

**Lời giải.** Destructor virtual làm phép xóa được phân phối theo kiểu động, nên destructor của lớp dẫn xuất sâu nhất chạy trước rồi đến destructor của base, theo thứ tự ngược với thứ tự xây, và đối tượng được giải phóng với kích thước thật của nó. Chương trình in ra kết quả của `compute(2.0)` ($1\cdot2=2$) rồi:

```text
2
~PID
~Controller
```

### Tính thay thế (Substitutability)

Nếu code hoạt động với `Base&`, nó cũng phải hoạt động với bất kỳ `Derived` nào. Một `FixedJoint : Joint` có `set_position` throw sẽ phá điều này (nguyên lý thay thế Liskov): phía gọi không thể biết từ kiểu rằng lời gọi có hợp lệ hay không. Chỉ kế thừa khi class dẫn xuất *là một* loại thay thế được của base, nếu không hãy dùng composition (một member) hoặc các interface tách riêng (`Positionable` chỉ được cài đặt bởi các khớp di chuyển được).

**Ví dụ.** Một planner gửi `set_position` tới mọi khớp của một cánh tay hỗn hợp; khớp thứ hai là một `FixedJoint` dẫn xuất từ `Joint` (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Code có biên dịch sạch không, planner thấy gì ở mỗi khớp, và `FixedJoint` có thỏa hợp đồng của `Joint` không?

```cpp
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <vector>
struct Joint { virtual ~Joint() = default; virtual void set_position(double q) { std::printf("moved to %.2f\n", q); } };
struct FixedJoint : Joint { void set_position(double) override { throw std::logic_error("fixed joint cannot move"); } };
int main() {
  std::vector<std::unique_ptr<Joint>> arm;
  arm.push_back(std::make_unique<Joint>()); arm.push_back(std::make_unique<FixedJoint>()); arm.push_back(std::make_unique<Joint>());
  int i = 0;
  for (auto& j : arm) {
    try { j->set_position(0.25 * ++i); } catch (const std::logic_error& e) { std::printf("joint %d: %s\n", i - 1, e.what()); }
  }
}
```

**Lời giải.** Code biên dịch không cảnh báo và planner, viết theo `Joint&`, không thể biết qua kiểu rằng khớp 1 sẽ từ chối: nó phải bắt `std::logic_error` hoặc kiểm tra kiểu động, và mọi bên gọi mới đều phải nhớ làm như vậy. Một kiểu có thao tác đôi khi bất hợp lệ không thỏa hợp đồng của base (Core Guidelines C.120, và nguyên lý thay thế Liskov), nên `FixedJoint` không nên dẫn xuất từ một `Joint` hứa hẹn có chuyển động. Chương trình in ra:

```text
moved to 0.25
joint 1: fixed joint cannot move
moved to 0.75
```

### Lời gọi virtual trong lúc construction và destruction

Trong khi constructor của lớp cơ sở chạy, kiểu động (dynamic type) của đối tượng *chính là* lớp cơ sở. Quy tắc là: một lời gọi virtual thực hiện trực tiếp hay gián tiếp từ constructor hoặc destructor sẽ chọn final overrider của lớp mà constructor hay destructor đó đang chạy, không bao giờ chọn override ở lớp dẫn xuất sâu hơn (cppreference: virtual function specifier, "During construction and destruction"; C++ Core Guidelines, C.82). Lý do là một lập luận an toàn, không phải ngẫu nhiên: khi `Sensor()` chạy, các member của `Lidar` chưa được xây, nên dispatch tới `Lidar::name()` sẽ đọc một đối tượng chưa tồn tại. Destruction là hình ảnh phản chiếu: khi `~Sensor()` chạy thì `~Lidar()` đã xong và các member của `Lidar` đã mất.

```cpp
struct Sensor {
  Sensor() { std::cout << "Sensor() sees " << name() << "\n"; }
  virtual ~Sensor() { std::cout << "~Sensor() sees " << name() << "\n"; }
  virtual std::string name() const { return "generic"; }
};
struct Lidar : Sensor {
  std::string label = "lidar";
  Lidar() { std::cout << "Lidar() sees " << name() << "\n"; }
  ~Lidar() override { std::cout << "~Lidar() sees " << name() << "\n"; }
  std::string name() const override { return label; }
};
```

Xây và hủy một `Lidar` in ra `Sensor() sees generic`, `Lidar() sees lidar`, `~Lidar() sees lidar`, `~Sensor() sees generic`. Nếu `name()` là pure virtual trong `Sensor` và không được cài đặt thì lời gọi từ `Sensor()` là undefined behavior (C.82). Thay vào đó nên: truyền dữ liệu cần thiết cho constructor cơ sở làm đối số (`Sensor(std::string n)`), dùng một factory có tên xây đối tượng hoàn chỉnh rồi gọi `init()` (đối tượng hợp lệ ngay khi factory trả về nên invariant không bị làm yếu), hoặc dùng hàm helper non-virtual trong lớp cơ sở. Đây là phiên bản dynamic-dispatch của mẫu chứng minh invariant: một lời gọi virtual trong constructor xảy ra *trước khi* bước establish hoàn tất, nên không được giả định bước preserve.

**Ví dụ.** Một driver cảm biến tính chu kỳ lấy mẫu ngay trong constructor của base từ một `rate()` virtual; driver dẫn xuất override `rate()` thành 100 Hz. Thiết kế thứ hai truyền tần số xuống (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Mỗi thiết kế tính ra chu kỳ bao nhiêu?

```cpp
#include <cstdio>
struct Driver {
  double period;
  Driver() : period(1.0 / rate()) {}           // virtual call inside the constructor
  virtual double rate() const { return 10.0; } // Hz, base default
  virtual ~Driver() = default;
};
struct FastDriver : Driver { double rate() const override { return 100.0; } };
struct Fixed {
  double period;
  explicit Fixed(double hz) : period(1.0 / hz) {}   // data passed down instead
  virtual ~Fixed() = default;
};
struct FastFixed : Fixed { FastFixed() : Fixed(100.0) {} };
int main() {
  FastDriver a; FastFixed b;
  std::printf("virtual call in constructor: period = %.2f s\n", a.period);
  std::printf("rate passed to base       : period = %.2f s\n", b.period);
}
```

**Lời giải.** Trong `Driver()` kiểu động là `Driver`, nên `rate()` được phân giải thành giá trị của base là 10 Hz ([class.cdtor]) và chu kỳ là $1/10=0{,}10$ s dù đối tượng được định chạy ở 100 Hz: lỗi âm thầm và invariant "chu kỳ = 1 / rate" sai ngay từ khoảnh khắc đầu tiên. Truyền tần số làm đối số constructor cho chu kỳ $1/100=0{,}01$ s và không cần lời gọi virtual nào trước khi đối tượng hoàn chỉnh (C.82). Chương trình in ra:

```text
virtual call in constructor: period = 0.10 s
rate passed to base       : period = 0.01 s
```

![Bốn cột cho việc xây và hủy một Lidar: Sensor() thấy generic, Lidar() thấy lidar, ~Lidar() thấy lidar, ~Sensor() thấy generic; member label chỉ sống ở giữa](/lesson-figures/CPP04-2.svg)

*Hình: cùng một lời gọi virtual `name()` chọn hàm khác nhau trong mỗi pha trong bốn pha; ở hai pha ngoài, member `Lidar::label` không tồn tại, vì vậy ngôn ngữ không gọi override dẫn xuất.*

### Substitutability như một hợp đồng: precondition yếu hơn, postcondition mạnh hơn

Đoạn Liskov ở trên có thể làm chính xác bằng từ vựng của specification. Specification $S_2$ *mạnh hơn* $S_1$ nếu precondition của nó yếu hơn hoặc bằng (nó nhận ít nhất mọi đầu vào mà $S_1$ nhận) và, trên mọi đầu vào mà $S_1$ nhận, postcondition của nó mạnh hơn hoặc bằng; một specification mạnh hơn có thể thay một cái yếu hơn trong mọi client (MIT 6.031, Reading 7, "Stronger vs. weaker specs"). Áp dụng cho hàm override `Derived::f` của `Base::f`:

$$\text{pre}_{\text{Base}}(x) \Rightarrow \text{pre}_{\text{Derived}}(x), \qquad \text{pre}_{\text{Base}}(x)\wedge \text{post}_{\text{Derived}}(x,y) \Rightarrow \text{post}_{\text{Base}}(x,y).$$

*Vì sao đây là điều kiện đúng.* Một client viết theo `Base&` chỉ biết $\text{pre}_{\text{Base}}$ và dựa vào $\text{post}_{\text{Base}}$. Nếu $\text{pre}_{\text{Derived}}$ chặt hơn thì sẽ có đầu vào $x$ mà client được phép truyền, với $\text{pre}_{\text{Base}}(x)$ đúng và $\text{pre}_{\text{Derived}}(x)$ sai: override từ chối hoặc hoạt động sai trên một lời gọi hợp lệ. Nếu $\text{post}_{\text{Derived}}$ yếu hơn thì client sẽ thấy một kết quả mà chứng minh của nó không xử lý được. Class invariant thêm một mệnh đề nữa: vì invariant phải đúng sau mọi lời gọi public nên $I_{\text{Derived}}\Rightarrow I_{\text{Base}}$ (đối tượng dẫn xuất có thể có *nhiều* ràng buộc hơn, không bao giờ ít hơn). Với `JointState`, lớp cơ sở hứa $|v|\le v_{\max}$; một lớp dẫn xuất chấp nhận các bước nhanh hơn (precondition yếu hơn) vẫn phải clamp để tốc độ lưu trữ tuân theo cận của lớp cơ sở, nếu không nó phá invariant mà client dựa vào (MIT 6.031, Reading 11, "Rep invariant").

*Cơ giới hóa: non-virtual interface.* Để hợp đồng tự động đúng với mọi override, đặt cổng kiểm tra trong một hàm public non-virtual của lớp cơ sở: nó kiểm tra precondition của lớp cơ sở, gọi một hàm private virtual `do_set(q, dt)`, và kiểm tra invariant của lớp cơ sở khi ra; lớp dẫn xuất chỉ tùy biến bước private. Khi đó ngay cả một override cẩu thả cũng không thể công bố một trạng thái vi phạm $I_{\text{Base}}$. Điều này cũng giải thích vì sao guideline không khuyến khích dữ liệu `protected` (C.133): lớp dẫn xuất ghi được vào member của lớp cơ sở sẽ vượt qua cổng, nên lớp cơ sở không còn chứng minh được invariant chỉ bằng cách nhìn các member function của chính nó.

**Ví dụ.** Joint cơ sở chấp nhận một chuyển động khi $|\Delta q|/dt\le2$ rad/s; `SlowJoint` override phép thử bằng 1,25 rad/s. Bốn lời gọi từ $q=0$ được phát lại trên cả hai (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Mỗi lớp chấp nhận những lời gọi nào, và override có thay thế được cho base không?

```cpp
#include <cmath>
#include <cstdio>
struct Joint {
  virtual ~Joint() = default;
  virtual bool accepts(double dq, double dt) const { return std::fabs(dq) / dt <= 2.0; }   // base: vmax = 2 rad/s
};
struct SlowJoint : Joint {
  bool accepts(double dq, double dt) const override { return std::fabs(dq) / dt <= 1.25; } // stricter precondition
};
int main() {
  const double calls[][2] = {{0.3, 0.2}, {0.5, 0.5}, {0.6, 0.4}, {0.8, 0.5}};
  Joint base; SlowJoint slow;
  std::printf("dq    dt    speed  base  slow\n");
  for (auto& c : calls)
    std::printf("%.1f   %.1f   %.2f   %-5d %d\n", c[0], c[1], c[0] / c[1], base.accepts(c[0], c[1]), slow.accepts(c[0], c[1]));
}
```

**Lời giải.** Tốc độ của mỗi lời gọi là $|\Delta q|/dt$: $0{,}3/0{,}2=1{,}50$, $0{,}5/0{,}5=1{,}00$, $0{,}6/0{,}4=1{,}50$ và $0{,}8/0{,}5=1{,}60$ rad/s. Cả bốn đều thỏa precondition của base (không quá 2), nhưng `SlowJoint` từ chối ba lời gọi (1,50, 1,50 và 1,60 rad/s đều lớn hơn 1,25): precondition của nó chặt hơn, nên $\text{pre}_{\text{Base}}\Rightarrow\text{pre}_{\text{Derived}}$ không đúng, và một bên gọi đã truyền các đối số hợp lệ nay bị từ chối. Hình vẽ dưới đây thể hiện cùng tình huống đó dưới dạng các vùng trong mặt phẳng của vị trí đích và bước thời gian. Chương trình in ra:

```text
dq    dt    speed  base  slow
0.3   0.2   1.50   1     0
0.5   0.5   1.00   1     1
0.6   0.4   1.50   1     0
0.8   0.5   1.60   1     0
```

![Các vùng được chấp nhận phía trên đường dt = |q'|/vmax với vmax 2,75, 2 và 1,25 và giới hạn cộng trừ 1,5, cùng hai lời gọi A và B được đánh dấu](/lesson-figures/CPP04-3.svg)

*Hình: các lời gọi được chấp nhận của mỗi override nằm phía trên đường của nó; override chậm chấp nhận một tập con (điểm A bị mất), override nhanh chấp nhận một tập cha (điểm B được chấp nhận nhưng tốc độ lưu 2,4 rad/s phá invariant của base).*

### Sao chép đối tượng đa hình: slicing, `clone`, và kiểu trả về covariant

Copy qua một reference tới lớp cơ sở chỉ sao chép subobject cơ sở (slicing), đó là lý do lớp cơ sở đa hình chặn copy và move public (C.67). Khi thật sự cần một bản sao sâu của kiểu dẫn xuất nhất, guideline quy định một `clone` virtual trả về con trỏ sở hữu và, trong lớp dẫn xuất, một kiểu trả về covariant (C.130; cppreference: virtual function specifier, "Covariant return types"):

```cpp
struct Shape  { virtual ~Shape() = default; virtual Shape* clone() const { return new Shape(*this); } };
struct Circle : Shape { Circle* clone() const override { return new Circle(*this); } };
struct Ring   : Circle { double r2 = 2; };   // forgot to override clone()
```

Kiểu lỗi này âm thầm: `Ring` thừa kế `Circle::clone`, nên `Shape* p = new Ring; p->clone()` tạo ra một `Circle`, một bản bị slice mà compiler không báo gì. Kiểu trả về covariant không thể là smart pointer, nên dạng an toàn lại là một NVI: `std::unique_ptr<Shape> clone() const` public non-virtual bọc một `do_clone()` pure virtual private và so sánh `typeid(*result)` với `typeid(*this)`; một override bị quên sẽ bị bắt ở lần clone đầu tiên trong bản debug thay vì sinh ra đối tượng sai về sau. Làm `do_clone` thuần ảo cũng buộc mọi lớp cụ thể phải cung cấp nó, dù không thể buộc các lớp con của một lớp trung gian làm vậy, nên kiểm tra lúc chạy vẫn hữu ích.

**Ví dụ.** Một chuỗi bộ lọc clone các node của nó qua một `clone()` public không virtual bọc một `do_clone()` pure virtual private và so sánh kiểu động. `Gain` override nó; `AutoGain` dẫn xuất từ `Gain` và quên (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`). Chuyện gì xảy ra khi clone từng node?

```cpp
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <typeinfo>
class Node {
 public:
  virtual ~Node() = default;
  std::unique_ptr<Node> clone() const {
    auto p = do_clone();
    if (typeid(*p) != typeid(*this)) throw std::logic_error("do_clone() not overridden");
    return p;
  }
 private:
  virtual std::unique_ptr<Node> do_clone() const = 0;
};
struct Gain : Node {
  double k = 2.5;
 private:
  std::unique_ptr<Node> do_clone() const override { return std::make_unique<Gain>(*this); }
};
struct AutoGain : Gain { double target = 1.0; };      // forgot to override do_clone
int main() {
  Gain g; AutoGain a;
  try { g.clone();  std::puts("Gain: clone ok"); } catch (const std::logic_error& e) { std::printf("Gain: %s\n", e.what()); }
  try { a.clone();  std::puts("AutoGain: clone ok"); } catch (const std::logic_error& e) { std::printf("AutoGain: %s\n", e.what()); }
}
```

**Lời giải.** `Gain` clone đúng. Với `AutoGain`, `Gain::do_clone` được thừa kế sẽ dựng một `Gain` (một slice: trường `target` bị mất), nhưng phép so sánh `typeid` trong `clone()` thấy `Gain` khác `AutoGain` và biến sự mất mát âm thầm đó thành một exception ngay lần clone đầu tiên, trong lần chạy test thay vì ngoài hiện trường (C.130, C.67). Phép kiểm tra tốn một phép so sánh RTTI cho mỗi lần clone. Chương trình in ra:

```text
Gain: clone ok
AutoGain: do_clone() not overridden
```

## Ví dụ có lời giải



### Ca 1: chấp nhận và từ chối các cập nhật khớp

**Đề bài.** `JointState(lo=-1.5, hi=1.5, vmax=2.0)` bắt đầu ở $q=0$, $v=0$. Lần lượt áp dụng `try_set_position(0.15, 0.1)`, `try_set_position(0.9, 0.1)`, cùng đích đó với `dt` nhỏ nhất hợp lệ, và `try_set_position(1.6, 10.0)`. Cho kết quả và trạng thái sau mỗi lời gọi. Sau đó đóng vòng điều khiển với `PController(kp=2)`, `dt=0.1`, đích $1.0$ và không giới hạn, và cho $q_{10}$.

**Lời giải.** Phép thử chấp nhận là phép thử trong lý thuyết: $l\le q'\le h$ và $|q'-q|/dt\le v_{\max}$, và một lần từ chối không đổi gì (bước preserve).

1. *Lời gọi `(0.15, 0.1)`.* Vị trí: $-1.5\le0.15\le1.5$ đúng. Tốc độ: $|0.15-0|/0.1=1.5$ rad/s $\le2$. Chấp nhận: $q=0.15$, $v=1.5$.
2. *Lời gọi `(0.9, 0.1)`.* Vị trí đúng. Tốc độ: $|0.9-0.15|/0.1=0.75/0.1=7.5$ rad/s $>2$. Từ chối; trạng thái giữ nguyên $q=0.15$, $v=1.5$.
3. *`dt` nhỏ nhất cho đích $0.9$.* Cần $0.75/dt\le2$, nên $dt\ge0.75/2=0.375$ s. Với `dt = 0.375` tốc độ đúng bằng $0.75/0.375=2.0\le2$: chấp nhận, $q=0.9$, $v=2.0$. (Dấu bằng ở biên rất mong manh với số thực dấu phẩy động; code thật chừa một biên an toàn hoặc so sánh với một dung sai.)
4. *Lời gọi `(1.6, 10.0)`.* Vị trí: $1.6>1.5$, nên bị từ chối với mọi `dt`; tốc độ $|1.6-0.9|/10=0.07$ không liên quan.
5. *Vòng kín.* Khi $v_{\max}$ và giới hạn không tác dụng, một bước là $q_{k+1}=q_k+k_p(1-q_k)\,dt=q_k+0.2(1-q_k)$, nên sai số $1-q_k$ được nhân với $0.8$ mỗi bước và $q_k=1-0.8^k$. Với $k=10$: $0.8^{10}=0.107374$, nên $q_{10}=0.892626$.

![Đồ thị vùng được chấp nhận theo vị trí đích và dt từ q = 0,15 với vmax 2 và giới hạn cộng trừ 1,5, cùng bước 2 bị từ chối, điểm biên của bước 3 và bước 4 ngoài giới hạn](/lesson-figures/CPP04-4.svg)

*Hình: các số của bước 2 đến 4 được vẽ trong mặt phẳng của đích và `dt`; bước 2 nằm dưới đường biên, bước 3 nằm trên nó, bước 4 nằm ngoài giới hạn nét đứt.*

**Kiểm tra.** `JointState` tham khảo (g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`) cho

```text
try_set_position(0.15, 0.1) -> accept, q=0.15, v=1.5
try_set_position(0.9, 0.1) -> reject, q=0.15, v=1.5
try_set_position(0.9, 0.375) -> accept, q=0.9, v=2
try_set_position(1.6, 10.0) -> reject, q=0.9, v=2
q10 = 0.892626
```

khớp với các bước 1 đến 5; giá trị dạng đóng $1-0.8^{10}=0.8926258\ldots$ trùng với vòng lặp.

**Rút ra.** Lớp chỉ chấp nhận một lời gọi khi cả hai điều kiện cùng đúng, và chính hai bất đẳng thức đó cho `dt` nhỏ nhất hợp lệ một cách trực tiếp.

### Ca 2: bố cục, dispatch và slicing của một đối tượng `PID`

**Đề bài.** Các controller mang một `id` và một vptr; `PID` thêm hai hệ số. Hãy dự đoán `sizeof(Controller)`, `sizeof(PID)`, vị trí của từng member của `PID` trên x86-64 với Itanium ABI, giá trị của `r.compute(2.0)` với `Controller& r` gắn vào một `PID`, và của `c.compute(2.0)` với bản sao bị slicing `Controller c = p`.

```cpp
#include <cstddef>
#include <cstdio>
#include <typeinfo>
struct Controller {
  virtual ~Controller() = default;
  virtual double compute(double) const { return 0.0; }
  int id = 7;
};
struct PID : Controller {
  double kp = 3.0, ki = 0.5;
  double compute(double e) const override { return kp * e + ki * e; }
};
int main() {
  PID p;
  Controller& r = p;
  Controller c = p;                                    // slicing: copies the Controller part only
  std::printf("sizeof(Controller) = %zu, sizeof(PID) = %zu\n", sizeof(Controller), sizeof(PID));
  std::printf("offsets in PID: id = %zu, kp = %zu, ki = %zu\n",
              (size_t)((char*)&p.id - (char*)&p), (size_t)((char*)&p.kp - (char*)&p), (size_t)((char*)&p.ki - (char*)&p));
  std::printf("r.compute(2.0) = %.1f, c.compute(2.0) = %.1f\n", r.compute(2.0), c.compute(2.0));
  void** vt_p = *reinterpret_cast<void***>(&p);        // the vptr (Itanium ABI)
  void** vt_c = *reinterpret_cast<void***>(&c);
  std::printf("vptr slot -1 is typeid: PID %d, sliced copy %d\n", vt_p[-1] == &typeid(PID), vt_c[-1] == &typeid(Controller));
  std::printf("vptr of p and c differ: %d\n", vt_p != vt_c);
}
```

**Lời giải.** Quy tắc căn chỉnh: một member kích thước $s$ được đặt ở bội số kế tiếp của alignment của nó, và kích thước đối tượng được làm tròn lên theo alignment lớn nhất (ở đây là 8).

1. *`Controller`.* Một class có hàm virtual bắt đầu bằng một vptr (8 byte, Itanium ABI §2.5). `int id` (4 byte, alignment 4) nằm ở offset 8, kết thúc ở 12; kích thước được làm tròn lên bội của 8: $\text{sizeof}(\text{Controller})=16$, với 4 byte đệm.
2. *`PID`.* Subobject base đứng trước (offset 0 đến 15). `double kp` cần alignment 8 nên ở offset 16, `double ki` ở 24: $\text{sizeof}(\text{PID})=16+8+8=32$.
3. *Dispatch qua tham chiếu.* `r` tham chiếu tới cùng đối tượng 32 byte, mà vptr của nó trỏ tới vtable của `PID` (slot $-1$ chứa `typeinfo`, slot 0 và 1 là hai destructor, slot 2 là `compute`). Lời gọi chọn `PID::compute`: $3.0\cdot2.0+0.5\cdot2.0=6.0+1.0=7.0$.
4. *Slicing.* `Controller c = p` copy-construct chỉ subobject `Controller` 16 byte: `kp` và `ki` không được copy, và vptr của đối tượng mới là vptr của `Controller`, nên `c.compute(2.0)` chạy `Controller::compute` và trả về $0.0$.

![Bố cục bộ nhớ của PID p: vptr ở 0, id ở 8, đệm 12 đến 16, kp ở 16, ki ở 24; vtable của PID với typeinfo, hai destructor và compute; bản sao slicing 16 byte có vptr trỏ tới Controller](/lesson-figures/CPP04-5.svg)

*Hình: đối tượng 32 byte với phần Controller (16 B) và phần `PID` thêm vào (16 B), các slot của vtable, và những gì bản sao bị slicing giữ lại.*

**Kiểm tra.** Biên dịch với g++ 11.4.0, `-std=c++20 -Wall -Wextra -fsanitize=address,undefined`, chương trình in

```text
sizeof(Controller) = 16, sizeof(PID) = 32
offsets in PID: id = 8, kp = 16, ki = 24
r.compute(2.0) = 7.0, c.compute(2.0) = 0.0
vptr slot -1 is typeid: PID 1, sliced copy 1
vptr of p and c differ: 1
```

(slot $-1$ bằng `&typeid(PID)` với `p` và `&typeid(Controller)` với bản sao, và gọi slot 2 của mỗi vtable qua con trỏ hàm cho $7.0$ và $0.0$ trong một biến thể của chương trình). Kích thước và offset là tính chất của ABI này, không phải của chuẩn.

**Rút ra.** Vptr đi cùng đối tượng và chọn override, nên dispatch cần tham chiếu hoặc con trỏ; copy theo giá trị chỉ giữ phần base và vptr của nó.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: C++ Core Guidelines, C.2 and C.8)* Với mỗi kiểu, quyết định dùng `struct` với member public hay `class` với member private, và nêu invariant nếu có: (a) `Vec3 {x, y, z}`; (b) `JointState`; (c) `UnitQuaternion`; (d) `LogConfig {path, level}` trong đó level phải là một trong năm tên; (e) `RingBuffer` giữ head, tail và vùng lưu trữ.
2. **(Dễ)** Dự đoán output, rồi giải thích điều gì sẽ sai nếu `~Base` không phải virtual:
   ```cpp
   struct Base { Base() { std::cout << "B "; } virtual ~Base() { std::cout << "~B "; } };
   struct Der : Base { Der() { std::cout << "D "; } ~Der() override { std::cout << "~D "; } };
   int main() { Base* p = new Der; delete p; }
   ```
3. **(Dễ)** Một khớp có giới hạn $[-1.5, 1.5]$ rad và $v_{\max}=2$ rad/s. Bắt đầu tại $q=1.0$, chu kỳ điều khiển `dt` nhỏ nhất để một bước tới $1.4$ được chấp nhận là bao nhiêu? Một bước tới $1.6$ có bao giờ được chấp nhận không?
4. **(Trung bình)** Tìm (các) bug cho phép phía gọi phá invariant, và sửa class.
   ```cpp
   class Joint {
     double q_ = 0, lo_, hi_;
    public:
     Joint(double lo, double hi) : lo_(lo), hi_(hi) {}
     double& position() { return q_; }
     void set(double q) { if (q < lo_ || q > hi_) return; q_ = q; }
   };
   // caller: Joint j(-1, 1); j.position() = 99;  j.set(NAN);
   ```
5. **(Trung bình)** *(Adapted from: C++ Core Guidelines, C.41)* Một đồng nghiệp viết `Camera c; c.init(path);` với một default constructor để `fd_ = -1`. Nêu hai bug cụ thể mà thiết kế này cho phép và chỉ ra cách tái cấu trúc để không thể tồn tại một `Camera` không hợp lệ, bao gồm cách xử lý khi việc mở có thể thất bại.
6. **(Trung bình)** Dự đoán output và giải thích:
   ```cpp
   struct Controller { virtual ~Controller() = default; virtual double compute(double) const { return 0; } };
   struct P : Controller { double compute(double e) const override { return 2 * e; } };
   double run(Controller c) { return c.compute(1); }
   double run2(const Controller& c) { return c.compute(1); }
   int main() { P p; std::cout << run(p) << " " << run2(p); }
   ```
7. **(Trung bình)** Chứng minh bằng quy nạp rằng một `JointState` với constructor và `try_set_position` của bài này giữ $l\le q\le h$ với mọi chuỗi lời gọi, kể cả các lời gọi với `NaN`, `dt` âm, và exception. Nêu chính xác dòng nào xử lý từng trường hợp.
8. **(Khó)** *(Adapted from: C++ Core Guidelines, C.120 and T.1)* Ba cách để robot đổi controller: một base `Controller` trừu tượng với lời gọi ảo, `std::function<double(double)>`, và một tham số template `template <class C> void run(C&)`. So sánh chúng về chi phí lúc chạy, kích thước binary, khả năng đổi lúc chạy, và khả năng kiểm thử. Bạn sẽ dùng cái nào cho một vòng khớp 1 kHz phải chuyển giữa P và PID lúc chạy?
9. **(Khó)** Một hệ phân cấp có `Joint` với `virtual void set_position(double)` và `FixedJoint : Joint` throw `std::logic_error`. Một planner gọi `set_position` trên mọi khớp của một danh sách hỗn hợp. Giải thích khiếm khuyết, rồi thiết kế lại hai lần: một lần với các interface tách riêng và một lần với composition, và nói cách nào giữ call site đơn giản nhất.
10. **(Khó)** `JointArray` giữ sáu `JointState` và cung cấp `try_set_all(std::array<double,6> q, double dt)`. Đặc tả một ngữ nghĩa trong đó hoặc tất cả khớp di chuyển hoặc không khớp nào, chỉ ra vì sao một vòng lặp ngây thơ gọi `try_set_position` từng khớp một phá vỡ nó, và đưa ra kế hoạch cài đặt (hai pha: kiểm tra tất cả, rồi commit). Invariant nào ràng buộc các khớp với nhau?
11. **(Mini-project)** Mở rộng `JointState` của lab với một kiểu giá trị `Limits` (một class kiểu `struct` đã được kiểm tra hợp lệ) và một `JointGroup` gồm các khớp có tên. Thêm một fuzz test áp dụng 100,000 cặp `(q, dt)` ngẫu nhiên (gồm NaN, vô cực, số không) và kiểm tra invariant sau mỗi lời gọi; báo cáo tỉ lệ chấp nhận.

12. **(Thử thách)** Dispatch trong lúc construction. Với các class `Sensor`/`Lidar` ở phần lý thuyết, (a) viết output chính xác của `{ Lidar l; }`. (b) Giải thích vì sao dispatch tới `Lidar::name()` từ trong `Sensor()` là không an toàn, nêu member nào chưa sống. (c) Nếu `Sensor::name()` là pure virtual không có định nghĩa thì tiêu chuẩn nói gì về lời gọi trong `Sensor()`, và g++ thường làm gì lúc chạy? (d) Nêu hai thiết kế lại để mỗi sensor có tên mà không có lời gọi virtual trong constructor, và nói cái nào giữ invariant "một `Sensor` luôn có tên không rỗng" dễ chứng minh nhất. (phỏng theo C++ Core Guidelines, C.82, và cppreference "Virtual function specifier", During construction and destruction)
13. **(Thử thách)** Substitutability, đếm cụ thể. `JointState(lo=-1.5, hi=1.5, vmax=2)` bắt đầu ở $q=0$. Xét lưới các lời gọi `try_set_position(q', dt)` với $q'=0.1k$ cho $k=-15,\dots,15$ và $dt=0.05j$ cho $j=1,\dots,20$ (620 lời gọi). (a) Lớp cơ sở chấp nhận bao nhiêu? (b) Một lớp con `SlowJoint` với $v_{\max}=1$ override phép kiểm tra: nó chấp nhận bao nhiêu, và có bao nhiêu lời gọi mà lớp cơ sở chấp nhận nhưng `SlowJoint` từ chối? Điều kiện nào trong hai điều kiện của substitutability bị vi phạm, với những lời gọi nào? (c) Một lớp con `FastJoint` với $v_{\max}=3$ chấp nhận bao nhiêu? Nó có thay thế được như đã viết không, và hành vi bổ sung nào làm nó thay thế được? (d) Chứng tỏ phép tính là chính xác bằng cách viết lại phép kiểm tra tốc độ bằng số nguyên. (phỏng theo MIT 6.031 Reading 7, "Stronger vs. weaker specs", và Reading 11, rep invariants)
14. **(Thử thách)** Lát cắt âm thầm. Với `Shape`, `Circle`, `Ring` như trong phần lý thuyết, (a) kiểu động của `p->clone()` với `Shape* p = new Ring` là gì? (b) Dự đoán `sizeof(Shape)`, `sizeof(Circle)`, `sizeof(Ring)` trên GCC x86-64 (vptr là 8 byte; `Circle` thêm `double r = 1` và `Ring` thêm `double r2`). (c) Viết lại hệ phân cấp với `std::unique_ptr<Shape> clone() const` public non-virtual và `do_clone()` pure virtual private, thêm kiểm tra `typeid`, và nói điều gì xảy ra khi clone một `Ring` mà không có `do_clone` riêng. (d) Vì sao kiểm tra lúc chạy không thể thay bằng một lỗi lúc biên dịch trong ngôn ngữ, và `final` trên `Circle::do_clone` thay đổi điều gì? (phỏng theo C++ Core Guidelines, C.67 và C.130)
15. **(Thử thách)** Invariant tất-cả-hoặc-không. `JointArray` giữ sáu `JointState` (giới hạn $[-1.5,1.5]$, $v_{\max}=2$, tất cả ở $q=0$) và `try_set_all(t, dt)` có một hook ghi log `hook(i)` có thể throw. Dùng $t=(0.1,0.1,0.1,2.0,0.1,0.1)$, $dt=0.1$. (a) Với vòng lặp ngây thơ (kiểm tra khớp $i$, commit nó, gọi `hook(i)`), cho các vị trí cuối và giá trị trả về. (b) Tương tự cho phiên bản hai pha (kiểm tra tất cả, chạy mọi hook, rồi commit tất cả). (c) Giờ $t=(0.1,\dots,0.1)$ và `hook(2)` throw: cho các vị trí sau exception với cả hai phiên bản. (d) Phát biểu group invariant, và vì sao pha commit phải `noexcept` để phiên bản hai pha đúng. (nguồn: MIT 6.031 Reading 11, rep invariants và "how to establish invariants"; C++ Core Guidelines, C.41)

## Cài đặt tham khảo

`JointState` thực thi invariant của nó, `Controller` là abstract interface, `PController` cài đặt nó, và `step` là một free function chỉ dùng public interface. Build bằng `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

```cpp
// CPP04 reference: a joint state that can never leave its invariant, plus a small interface hierarchy.
#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <stdexcept>

// Invariant: lo <= q <= hi, |v| <= vmax, all values finite.
class JointState {
 public:
  JointState(double lo, double hi, double vmax, double q0 = 0.0)
      : lo_(lo), hi_(hi), vmax_(vmax), q_(q0) {
    if (!std::isfinite(lo) || !std::isfinite(hi) || !(lo < hi)) throw std::invalid_argument("bad limits");
    if (!std::isfinite(vmax) || !(vmax > 0.0)) throw std::invalid_argument("bad vmax");
    if (!(lo <= q0 && q0 <= hi)) throw std::invalid_argument("q0 outside limits");
  }

  double position() const { return q_; }
  double velocity() const { return v_; }
  double lo() const { return lo_; }
  double hi() const { return hi_; }
  double vmax() const { return vmax_; }

  // Moves to q over dt seconds. Returns false and changes nothing if the move would
  // violate the position limits or the speed limit (or if dt or q are not usable).
  bool try_set_position(double q, double dt) {
    if (!std::isfinite(q) || !(dt > 0.0) || !std::isfinite(dt)) return false;
    if (q < lo_ || q > hi_) return false;
    const double v = (q - q_) / dt;
    if (std::fabs(v) > vmax_) return false;
    q_ = q;
    v_ = v;
    return true;
  }

  // Same, but reports a rejection with an exception.
  void set_position(double q, double dt) {
    if (!try_set_position(q, dt)) throw std::domain_error("rejected joint update");
  }

 private:
  double lo_, hi_, vmax_;
  double q_;
  double v_ = 0.0;
};

// Interface: a controller maps an error to a velocity command.
struct Controller {
  virtual ~Controller() = default;
  virtual double compute(double error) const = 0;
};

class PController : public Controller {
 public:
  explicit PController(double kp) : kp_(kp) {
    if (!std::isfinite(kp) || kp < 0.0) throw std::invalid_argument("kp must be finite and >= 0");
  }
  double compute(double error) const override { return kp_ * error; }

 private:
  double kp_;
};

// One control step: command velocity, clamp it to vmax and the target to the limits, then apply.
void step(JointState& j, const Controller& c, double target, double dt) {
  const double cmd = std::clamp(c.compute(target - j.position()), -j.vmax(), j.vmax());
  const double q = std::clamp(j.position() + cmd * dt, j.lo(), j.hi());
  j.set_position(q, dt);
}

// ---- self-test
int main() {
  JointState j(-1.0, 1.0, 2.0);
  if (!j.try_set_position(0.15, 0.1) || j.position() != 0.15) return 1;
  if (j.try_set_position(0.9, 0.1) || j.position() != 0.15) return 2;  // 7.5 rad/s > 2
  bool threw = false;
  try { JointState bad(1.0, -1.0, 1.0); } catch (const std::invalid_argument&) { threw = true; }
  if (!threw) return 3;
  JointState k(-10.0, 10.0, 100.0);
  std::unique_ptr<Controller> c = std::make_unique<PController>(2.0);
  for (int i = 0; i < 10; ++i) step(k, *c, 1.0, 0.1);
  if (std::fabs(k.position() - (1.0 - std::pow(0.8, 10))) > 1e-12) return 4;
  std::cout << "CPP04 reference self-test passed\n";
}
```

## Thực hành độc lập

### Mục tiêu

Xây một class không thể bị dựng hoặc cập nhật vào trạng thái không hợp lệ, và chứng minh bằng một test với đầu vào thù địch (hostile).

### Chuẩn bị

`g++` hoặc `clang++` với C++17. Lưu code khởi đầu và các test bên dưới thành `lab.cpp`, rồi chạy

```
g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab
```

### Nhiệm vụ

1. Cài đặt constructor với cả bốn phép kiểm tra hợp lệ và các getter const.
2. Cài đặt `try_set_position`: kiểm tra tính hữu hạn trước, rồi dt, rồi khoảng, rồi tốc độ; chỉ thay đổi sau khi mọi kiểm tra đã qua.
3. Cài đặt `set_position` dựa trên `try_set_position`.
4. Cài đặt `PController` và xác minh bằng tay công thức đóng $q_k=1-0.8^k$ bằng máy tính cho $k=1,2,3$.
5. Cài đặt `step` với hai phép clamp, rồi chạy test thù địch (gain $10^6$, mục tiêu đổi luân phiên).
6. Thêm một trường hợp từ chối thứ năm của riêng bạn vào các test (ví dụ `+INFINITY`) và ghi lại dòng nào trong code của bạn xử lý nó.

### Code khởi đầu

```cpp
#include <algorithm>
#include <cmath>
#include <memory>
#include <stdexcept>

// Invariant to enforce in EVERY public operation: lo <= q <= hi, |v| <= vmax, all finite.
class JointState {
 public:
  // Throws std::invalid_argument unless lo < hi (both finite), vmax finite and > 0, lo <= q0 <= hi.
  JointState(double lo, double hi, double vmax, double q0 = 0.0) {
    throw std::logic_error("NotImplemented");
  }
  double position() const { throw std::logic_error("NotImplemented"); }
  double velocity() const { throw std::logic_error("NotImplemented"); }  // (q_new - q_old) / dt of the last accepted move, 0 initially
  double lo() const { throw std::logic_error("NotImplemented"); }
  double hi() const { throw std::logic_error("NotImplemented"); }
  double vmax() const { throw std::logic_error("NotImplemented"); }

  // Move to q over dt seconds. Return false and change NOTHING if q is NaN/inf, dt is not
  // finite and > 0, q is outside [lo, hi], or |q - position| / dt > vmax. Otherwise apply, return true.
  bool try_set_position(double q, double dt) { throw std::logic_error("NotImplemented"); }
  // Like try_set_position but throws std::domain_error on rejection.
  void set_position(double q, double dt) { throw std::logic_error("NotImplemented"); }
};

struct Controller {  // given: an abstract interface
  virtual ~Controller() = default;
  virtual double compute(double error) const = 0;
};

// Proportional controller: compute(e) = kp * e. Throws std::invalid_argument if kp < 0 or not finite.
class PController : public Controller {
 public:
  explicit PController(double kp) { throw std::logic_error("NotImplemented"); }
  double compute(double error) const override { throw std::logic_error("NotImplemented"); }
};

// One control step: cmd = clamp(c.compute(target - position), -vmax, vmax);
// q = clamp(position + cmd * dt, lo, hi); then j.set_position(q, dt).
void step(JointState& j, const Controller& c, double target, double dt) {
  throw std::logic_error("NotImplemented");
}
```

### Kiểm thử

```cpp

// ---- tests (paste below the starter code)
#include <cmath>
#include <cstdlib>
#include <iostream>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)
template <class E, class F> bool throws(F f) { try { f(); } catch (const E&) { return true; } return false; }

int main() {
  // 1. construction and invariants
  JointState j(-1.0, 1.0, 2.0);
  CHECK(j.position() == 0.0 && j.velocity() == 0.0 && j.lo() == -1.0 && j.hi() == 1.0 && j.vmax() == 2.0);
  CHECK(throws<std::invalid_argument>([] { JointState(1.0, -1.0, 1.0); }));
  CHECK(throws<std::invalid_argument>([] { JointState(-1.0, 1.0, 0.0); }));
  CHECK(throws<std::invalid_argument>([] { JointState(-1.0, 1.0, 1.0, 1.5); }));
  CHECK(throws<std::invalid_argument>([] { JointState(NAN, 1.0, 1.0); }));
  // 2. accepted move (hand computed: 0.15 / 0.1 = 1.5 rad/s <= 2)
  CHECK(j.try_set_position(0.15, 0.1));
  CHECK(j.position() == 0.15 && std::fabs(j.velocity() - 1.5) < 1e-12);
  // 3. rejections change nothing: too fast, outside limits, NaN, bad dt
  CHECK(!j.try_set_position(0.9, 0.1));   // 7.5 rad/s
  CHECK(!j.try_set_position(1.5, 10.0));  // outside [lo, hi]
  CHECK(!j.try_set_position(NAN, 0.1));
  CHECK(!j.try_set_position(0.2, 0.0));
  CHECK(!j.try_set_position(0.2, -1.0));
  CHECK(j.position() == 0.15 && std::fabs(j.velocity() - 1.5) < 1e-12);
  CHECK(throws<std::domain_error>([&] { j.set_position(5.0, 1.0); }));
  // 4. boundary value is allowed
  JointState b(-1.0, 1.0, 100.0);
  CHECK(b.try_set_position(1.0, 1.0) && b.position() == 1.0);
  // 5. controller: closed form q_k = 1 - 0.8^k for kp = 2, dt = 0.1, huge vmax
  JointState k(-10.0, 10.0, 100.0);
  std::unique_ptr<Controller> c = std::make_unique<PController>(2.0);
  for (int i = 0; i < 10; ++i) step(k, *c, 1.0, 0.1);
  CHECK(std::fabs(k.position() - (1.0 - std::pow(0.8, 10))) < 1e-12);
  CHECK(throws<std::invalid_argument>([] { PController(-1.0); }));
  // 6. invariant under a hostile controller: huge gain, limited joint never leaves its box
  JointState h(-0.5, 0.5, 1.0);
  PController wild(1e6);
  for (int i = 0; i < 100; ++i) {
    step(h, wild, (i % 2) ? 10.0 : -10.0, 0.05);
    CHECK(h.position() >= -0.5 && h.position() <= 0.5 && std::fabs(h.velocity()) <= 1.0 + 1e-12);
  }
  std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi

```
all tests passed
```

### Thử thách mở rộng

Làm cho `Limits` và `JointState` thân thiện với constexpr, hoặc thêm một tham số template `Joint` cho đơn vị (radian so với mét) để việc truyền một vị trí tịnh tiến cho một khớp quay không biên dịch được.

### Thực hành với thư viện

Chỉ dùng standard library: `<random>` cho fuzz test của dự án mở rộng, và `<functional>`/`<variant>` cho hai phương án thay thế virtual dispatch từ bài tập 8. Dán code bên dưới *sau* các `JointState`, `Controller`, `PController` và `step` đã hoàn thiện của bạn (nó có `main` riêng, nên bỏ `main` ở phần test). Biên dịch bằng `g++ -std=c++17 -Wall -Wextra -fsanitize=address,undefined`.

```cpp
#include <cassert>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <random>
#include <variant>
#include <vector>

// step() again, but taking ANY callable error -> command (lambda, std::function, functor).
template <class F>
void step_with(JointState& j, F&& compute, double target, double dt) {
  const double cmd = std::clamp(compute(target - j.position()), -j.vmax(), j.vmax());
  j.set_position(std::clamp(j.position() + cmd * dt, j.lo(), j.hi()), dt);
}

struct PGain  { double kp; double operator()(double e) const { return kp * e; } };
struct PDGain { double kp, kd, prev = 0; double operator()(double e) { double d = e - prev; prev = e; return kp * e + kd * d; } };

int main() {
  // 1. fuzz with <random>: the invariant must hold after every call, accepted or not
  std::mt19937 rng(42);
  std::normal_distribution<double> nd(0.0, 3.0);
  const double inf = std::numeric_limits<double>::infinity();
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const std::vector<double> special = {0.0, -0.0, nan, inf, -inf, 1e308, 5e-324, 1.5, -1.5};
  JointState j(-1.5, 1.5, 2.0);
  int accepted = 0;
  for (int i = 0; i < 100000; ++i) {
    double q  = (i % 4 == 0) ? special[rng() % special.size()] : nd(rng);
    double dt = (i % 5 == 0) ? special[rng() % special.size()] : std::fabs(nd(rng)) * 0.1;
    const double q0 = j.position(), v0 = j.velocity();
    const bool ok = j.try_set_position(q, dt);
    accepted += ok;
    if (!ok) assert(j.position() == q0 && j.velocity() == v0);      // a rejection is a no-op
    assert(std::isfinite(j.position()) && j.position() >= -1.5 && j.position() <= 1.5);
    assert(std::fabs(j.velocity()) <= 2.0);
  }
  std::cout << "accepted " << accepted << " of 100000\n";

  // 2. three ways to swap the controller must agree with the virtual PController
  const double expect = 1.0 - std::pow(0.8, 10);
  PController virt(2.0);
  std::function<double(double)> fn = PGain{2.0};
  std::variant<PGain, PDGain> var = PGain{2.0};            // run-time switch without virtual
  JointState a(-10, 10, 100), b(-10, 10, 100), c(-10, 10, 100), d(-10, 10, 100);
  for (int i = 0; i < 10; ++i) {
    step(a, virt, 1.0, 0.1);                                           // virtual
    step_with(b, fn, 1.0, 0.1);                                        // std::function
    step_with(c, [&](double e) { return std::visit([e](auto& g) { return g(e); }, var); }, 1.0, 0.1);
    step_with(d, PGain{2.0}, 1.0, 0.1);                                // template, inlinable
  }
  for (const JointState* s : {&a, &b, &c, &d}) assert(std::fabs(s->position() - expect) < 1e-12);
  std::cout << "four controllers agree: " << a.position() << "\n";
}
```

Output mong đợi: `accepted ...` (khoảng 11 800 trong 100 000 với seed này; con số chính xác phụ thuộc vào `normal_distribution` của standard library của bạn) và `four controllers agree: 0.892626`. Mọi assert phải đúng, đó là chứng minh quy nạp của bài tập 7 được kiểm tra trên 100 000 lời gọi thù địch. Sau đó hãy đo: vòng lặp `std::function` chậm hơn bản template bao nhiêu với $10^8$ lời gọi (dùng `-O2` và `std::chrono`)?

## Kiểm chứng

- Viết invariant thành một hàm private `bool invariant() const` kiểu `assert` và gọi nó ở cuối mọi hàm có thay đổi trạng thái trong bản debug.
- Kiểm thử đầu vào thù địch (fuzz): giá trị ngẫu nhiên, cộng thêm tập đặc biệt `{0, -0, NaN, +inf, -inf, DBL_MAX, DBL_MIN}`. Invariant phải đúng sau mỗi lời gọi.
- Kiểm thử đường *từ chối* cẩn thận như đường chấp nhận: trạng thái phải không đổi, bạn kiểm tra bằng cách đọc mọi getter trước và sau.
- Chạy dưới `-fsanitize=undefined` để bắt tràn số có dấu hoặc ép kiểu không hợp lệ; kiểm tra `-Wall -Wextra -Wnon-virtual-dtor` để phát hiện virtual destructor bị thiếu.
- So sánh output vòng kín với một mô phỏng Python ngắn dùng cùng hằng số.

## Lỗi thường gặp

| Sai lầm | Hậu quả |
|---|---|
| Data member public cho một giá trị có khoảng hợp lệ | code nào cũng có thể lưu giá trị không hợp lệ; lỗi xuất hiện xa nguyên nhân |
| `if (q < lo \|\| q > hi) reject` | NaN qua được bước kiểm tra và làm hỏng các phép tính sau |
| Getter trả về `double&` | `j.position() = 99` vượt qua mọi phép kiểm tra |
| Cập nhật trạng thái trước phép kiểm tra cuối | lời gọi bị từ chối để lại đối tượng bị sửa dở |
| Destructor không virtual trên base đa hình | undefined behavior khi `delete base_ptr`; phần dẫn xuất không được hủy |
| Truyền đối tượng đa hình theo giá trị | slicing: cài đặt của base chạy (output `0` thay vì `2` ở bài tập 6) |
| Gõ sai override (thiếu `const`) | lặng lẽ thành một hàm mới, bản của base chạy; hãy dùng `override` |
| Kế thừa để tái dùng code thay vì để thay thế | phía gọi phải biết kiểu cụ thể |

## Phương án khác và đánh đổi

- **Từ chối bằng `bool` hay bằng exception.** Trả về `bool`/`std::optional` tự nhiên khi việc từ chối là thường lệ (một planner đề xuất nhiều cập nhật ứng viên); exception phù hợp với lỗi của lập trình viên và thất bại trong constructor. Các vòng lặp real-time thường cấm exception, nên hãy cung cấp các biến thể `try_`.
- **Clamp hay từ chối.** Clamp luôn cho trạng thái hợp lệ nhưng che giấu lỗi; từ chối phơi bày chúng. Code liên quan đến an toàn thường từ chối và ghi log, còn một tầng riêng thực hiện clamp.
- **Kế thừa so với template so với `std::function`**: lời gọi ảo cho sự linh hoạt lúc chạy với cái giá là một lời gọi gián tiếp; template cho đa hình tĩnh không tốn chi phí nhưng cố định kiểu lúc biên dịch và làm code phình ra; `std::function` linh hoạt và đơn giản cho callback nhưng có thể cấp phát bộ nhớ.
- **Strong type.** Một wrapper như `Radians` loại bỏ nhầm lẫn đơn vị lúc biên dịch; nó là một class rất nhỏ có invariant.
- **Aggregate cho dữ liệu thuần.** Với message và gói tham số không có invariant, một `struct` thuần tốt hơn: đơn giản hơn, có thể khởi tạo bằng ngoặc nhọn, và không thể bị dùng sai qua accessor.

## Vận dụng và ghi nhớ

Cùng mẫu này xuất hiện trong `hardware_interface` của ROS 2 (một abstract interface với `read` và `write`), trong `std::mutex`/`lock_guard` (một class có invariant "bị khóa khi và chỉ khi được sở hữu"), và trong `std::vector` (invariant: size ≤ capacity, vùng lưu trữ hợp lệ). Trong Python, invariant được giữ bằng property hoặc descriptor (PY10). Để ghi nhớ: chọn một class từ code của chính bạn, viết invariant của nó thành một câu, và tìm hàm đầu tiên có thể phá nó. Sau một tuần, tự suy lại chứng minh quy nạp cho một class của bạn mà không xem ghi chú.

## Đáp án bài tập

1. (a) `struct`: ba double bất kỳ đều là một vector hợp lệ. (b) `class`: $l\le q\le h$, $|v|\le v_{\max}$. (c) `class`: $\|q\|=1$; các thao tác phải chuẩn hóa lại hoặc từ chối. (d) `class`: level phải thuộc tập cho phép (hoặc dùng `enum class` và một struct). (e) `class`: chỉ số head và tail nằm trong $[0,\text{capacity})$ và vùng lưu trữ khớp với chúng. Một câu trả lời tốt nối mỗi `class` với invariant của nó.
2. Output: `B D ~D ~B`. Không có virtual destructor, `delete p` qua `Base*` là undefined behavior; trên thực tế chỉ `~Base` chạy, nên tài nguyên do `Der` giữ bị rò rỉ.
3. $|1.4-1.0|/dt\le2\Rightarrow dt\ge0.2$ s. Một bước tới 1.6 không bao giờ được chấp nhận vì nó nằm ngoài $[-1.5,1.5]$ bất kể `dt`.
4. Các bug: `position()` trả về một reference có thể sửa, nên `j.position() = 99` ghi tùy ý; constructor không kiểm tra `lo < hi`, và `q_ = 0` ban đầu nằm ngoài giới hạn với `Joint(1, 2)`; `set(NAN)` qua được vì cả hai phép so sánh đều sai; `set` thất bại một cách lặng lẽ (`return`) nên phía gọi không biết. Cách sửa: `double position() const`; kiểm tra hợp lệ trong constructor (throw); viết `if (!(lo_ <= q && q <= hi_)) return false;` và trả về `bool`.
5. Các bug: dùng camera trước `init()` (đọc fd -1); gọi `init()` hai lần làm rò rỉ descriptor đầu tiên; một `init` thất bại để lại một đối tượng dở dang. Cách sửa: `explicit Camera(const std::string& path)` mở và throw khi thất bại (hoặc một static factory `std::optional<Camera> Camera::open(path)` khi thất bại là thường lệ), destructor đóng, copy bị xóa và định nghĩa các phép move (CPP03).
6. Output `0 2`. `run(Controller c)` cắt `p` còn phần `Controller` của nó, và `compute` của base trả 0; `run2` nhận một reference, nên virtual dispatch gọi `P::compute` và cho $2\cdot1=2$.
7. Cơ sở: constructor throw trừ khi $l\le q_0\le h$ với các giới hạn hữu hạn, nên $I$ đúng sau khi dựng. Bước quy nạp: giả sử $l\le q\le h$. Trong `try_set_position`: `q` NaN/inf và `dt` xấu trả `false` trước mọi phép ghi (dòng kiểm tra tính hữu hạn); `q` ngoài $[l,h]$ trả `false` (dòng kiểm tra khoảng); một bước quá nhanh trả `false` (dòng kiểm tra tốc độ); chỉ khi tất cả đều qua thì `q_` và `v_` mới được gán, với các giá trị thỏa $l\le q'\le h$ và $|v'|\le v_{\max}$. Một kết quả `false` để trạng thái không đổi, nên $I$ vẫn đúng. `set_position` chỉ throw sau khi `try_set_position` trả `false`, không có thay đổi nào. Theo quy nạp $I$ đúng mãi mãi.
8. Một câu trả lời tốt: lời gọi ảo = một lời gọi gián tiếp, không inline, nhưng chỉ có một hàm được biên dịch và kiểu có thể đổi lúc chạy (hoán đổi một `unique_ptr<Controller>`); `std::function` có chi phí gián tiếp tương tự, có thể cấp phát khi dựng, đơn giản nhất cho lambda và test double; template inline được hoàn toàn (nhanh nhất) nhưng kiểu cố định lúc biên dịch và mỗi instantiation thêm code. Với việc chuyển P/PID lúc chạy, một abstract interface (hoặc `std::variant<P, PID>` với `std::visit`) là đúng; chi phí là không đáng kể ở 1 kHz.
9. Planner kỳ vọng mọi `Joint` đều di chuyển; `FixedJoint` phá hợp đồng, nên phía gọi phải kiểm tra kiểu hoặc bắt exception (vi phạm LSP). Thiết kế lại A: `struct Joint` (chỉ đọc: `position`) và `struct Actuated : Joint` (thêm `set_position`), với `FixedJoint : Joint` mà thôi. Thiết kế lại B: một class `Joint` duy nhất có member `Limits` hoặc `Mobility` (composition) trong đó khớp cố định có `lo == hi`, nên `set_position` từ chối mọi bước di chuyển qua quy tắc thông thường. A thường giữ call site an toàn về kiểu; B giữ một kiểu duy nhất và đơn giản hơn cho danh sách khớp hỗn hợp.
10. Vòng lặp ngây thơ: khớp 0-2 chấp nhận và di chuyển, khớp 3 từ chối, nên cánh tay kết thúc ở một trạng thái chưa từng được yêu cầu (cập nhật một phần). Kế hoạch: pha 1, với mỗi khớp tính việc chấp nhận bằng một `can_move(q, dt)` không thay đổi trạng thái và thu thập các thất bại; nếu có, trả `false` mà không ghi gì; pha 2, commit tất cả (không thể thất bại vì đã được kiểm tra). Invariant của nhóm là "mỗi khớp thỏa invariant của riêng nó *và* vector được ra lệnh gần nhất là nhất quán", tức vector luôn là một trạng thái đã qua kiểm tra như một tổng thể.
11. Một câu trả lời tốt gồm: `Limits(lo, hi, vmax)` kiểm tra hợp lệ trong constructor; `JointGroup` giữ `std::map<std::string, JointState>` hoặc một vector kèm tên; fuzz test lấy từ một danh sách giá trị đặc biệt và từ một phân phối chuẩn ngẫu nhiên; tỉ lệ chấp nhận phụ thuộc vào phân phối (báo cáo nó cùng số lượng của từng lý do từ chối); việc kiểm tra invariant là một hàm riêng không dùng code đang được kiểm thử.

12. (a) `Sensor() sees generic`, `Lidar() sees lidar`, `~Lidar() sees lidar`, `~Sensor() sees generic` (đo bằng g++ 11.4). (b) Khi `Sensor()` chạy, phần `Lidar` chưa được xây: `label` (một member `std::string` của `Lidar`) chưa sống, nên `Lidar::name()` sẽ trả về một reference tới string chưa được xây. Vì thế ngôn ngữ giải quyết lời gọi thành `Sensor::name()`. Trong `~Sensor()` các member của `Lidar` đã bị hủy, cùng lý do theo chiều ngược. (c) Gọi một hàm pure virtual chưa cài đặt từ constructor hoặc destructor, trực tiếp hay gián tiếp, là undefined behavior (C.82); g++ thường nối slot vtable tới `__cxa_pure_virtual` và chương trình abort với "pure virtual method called" (khi lời gọi là trực tiếp trong constructor, compiler cũng có thể từ chối hoặc cảnh báo lúc build). (d) Thiết kế 1: truyền tên xuống, `Sensor(std::string n) : name_(std::move(n))` với `name() const` non-virtual; constructor dẫn xuất viết `Sensor("lidar")`. Thiết kế 2: một static factory `create_lidar()` xây hoàn chỉnh rồi gọi `init()` virtual. Thiết kế 1 giữ invariant dễ chứng minh nhất: constructor cơ sở có thể kiểm tra `!n.empty()` và throw, thiết lập invariant một lần, trước khi bất kỳ code dẫn xuất nào chạy, và `name()` là getter thường không thể phá nó.
13. Dùng số nguyên: $|q'|/dt = 0.1|k|/(0.05j) = 2|k|/j$, nên phép thử $|q'|/dt\le v_{\max}$ là $2|k|\le v_{\max}\,j$ (mọi $q'$ nằm trong $[-1.5,1.5]$ nên kiểm tra phạm vi luôn qua). (a) $v_{\max}=2$: **410** trên 620 được chấp nhận (tính bằng liệt kê). (b) $v_{\max}=1$: **220** được chấp nhận. Mọi lời gọi `SlowJoint` chấp nhận đều được lớp cơ sở chấp nhận (220 ở cả hai, 0 chỉ ở lớp dẫn xuất), nên 410 - 220 = **190** lời gọi được lớp cơ sở chấp nhận mà `SlowJoint` từ chối: precondition của override *chặt hơn* lớp cơ sở, điều kiện substitutability thứ nhất bị vi phạm ($\text{pre}_{\text{Base}}\Rightarrow\text{pre}_{\text{Derived}}$ là sai). Một client hỏi hợp lệ $k=15$, $j=15$ ($1.5$ rad trong $0.75$ s, tốc độ 2) bị từ chối. Postcondition của nó ($|v|\le1\le2$) thì ổn. (c) $v_{\max}=3$: **480** được chấp nhận, một tập cha của 410 (precondition yếu hơn: được phép). Nhưng như đã viết nó lưu tốc độ tới 3, vi phạm invariant $|v|\le2$ của lớp cơ sở mà client có thể dựa vào, nên điều kiện postcondition/invariant bị vi phạm. Nó trở nên thay thế được nếu đồng thời giữ tốc độ lưu trữ bị chặn, chẳng hạn clamp tốc độ lệnh hoặc bước để $|v'|\le2$, hoặc khai báo invariant lớp cơ sở yếu hơn, khi đó điều client được giả định thay đổi. (d) Đã làm ở trên: không có vấn đề biên dấu phẩy động trong các số đếm vì phép so sánh dùng số nguyên chính xác.
14. (a) `Circle`: `Ring` thừa kế `Circle::clone`, copy-construct một `Circle`; đo được: bản gốc `Ring`, bản clone `Circle`, không có chẩn đoán nào. (b) Đo trên g++ 11.4 x86-64: `sizeof(Shape)=8` (vptr), `sizeof(Circle)=16`, `sizeof(Ring)=24`. Đây là các số phụ thuộc ABI, tiêu chuẩn không đảm bảo. (c) `clone()` public non-virtual: `std::unique_ptr<Shape> p(do_clone()); if (typeid(*p) != typeid(*this)) abort();`. Clone một `Ring` không override `do_clone` sẽ chạy `Circle::do_clone`, trả về một `Circle`, kiểm tra thấy `Circle != Ring` và abort kèm thông báo (đo được: "clone() override missing in 4Ring"). Kiểm tra này cũng cho một `unique_ptr` sở hữu ngay từ đầu, điều mà `clone` covariant dùng con trỏ thô không làm được. (d) Ngôn ngữ không có cách nói "mọi lớp dẫn xuất từ đây, ở bất kỳ độ sâu nào, đều phải override"; pure virtual chỉ buộc lớp cụ thể đầu tiên. Kiểm tra `typeid` lúc debug vì vậy là tấm lưới rẻ nhất. Đặt `final` trên `Circle::do_clone` cấm override thêm, nên `Ring` cũng không thể override nó: quên override biến thành một thiết kế mà `Ring` không được tồn tại như lớp con của `Circle`, buộc phải thiết kế tốt hơn (ví dụ `Ring` dẫn xuất trực tiếp từ `Shape`).
15. (a) Vòng lặp ngây thơ: khớp 0, 1, 2 qua kiểm tra và commit (vị trí $0.1$), khớp 3 thất bại ($2.0>1.5$) và hàm trả về `false`: vị trí cuối $(0.1,0.1,0.1,0,0,0)$, một trạng thái không ai yêu cầu (đã đo). (b) Hai pha: kiểm tra thất bại trước khi đổi bất cứ thứ gì: trả về `false`, vị trí $(0,0,0,0,0,0)$. (c) Ngây thơ: `hook(2)` throw sau khi khớp 2 đã commit, nên vị trí sau exception là $(0.1,0.1,0.1,0,0,0)$. Hai pha: hook chạy trước mọi commit và throw để cả sáu khớp ở $0$ (strong guarantee). (d) Group invariant: mỗi khớp thỏa invariant của nó *và* vector vị trí bằng vector cuối cùng đã qua kiểm tra như một tổng thể (nên nhóm không bao giờ lộ ra một hỗn hợp cũ và mới). Pha commit phải `noexcept`: nếu một commit có thể throw sau khớp 2 thì các commit trước đó không hoàn tác được (hoàn tác cũng là một commit), và nhóm lại ở trạng thái hỗn hợp. Vì vậy mọi thứ có thể thất bại (kiểm tra, ghi log, cấp phát) làm ở pha 1, còn pha 2 chỉ gán các double.

## Đọc thêm

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - phần C về class, invariant (C.2, C.40-C.42), và hệ phân cấp (C.120-C.153).
- [cppreference: Classes](https://en.cppreference.com/w/cpp/language/classes) - các quy tắc chính xác về kiểm soát truy cập, constructor, hàm ảo và abstract class.
- [LearnCpp](https://www.learncpp.com/) - class, constructor, kế thừa và hàm ảo với các quiz có chấm điểm.
- [Bản nháp chuẩn C++, [class.cdtor]](https://eel.is/c++draft/class.cdtor) và [[class.access.general]](https://eel.is/c++draft/class.access.general) - lời gọi virtual trong lúc construction và destruction, và định nghĩa truy cập private; [Itanium C++ ABI, §2.5](https://itanium-cxx-abi.github.io/cxx-abi/abi.html) - bố cục vtable dùng trong ca có lời giải thứ hai.
- [cppreference: Virtual function specifier](https://en.cppreference.com/w/cpp/language/virtual) - hành vi trong lúc construction và destruction, kiểu trả về covariant, hàm thuần ảo.
- [MIT 6.031 Reading 7: Designing Specifications](https://web.mit.edu/6.031/www/sp22/classes/07-designing-specs/) và [Reading 11: Abstraction Functions and Rep Invariants](https://web.mit.edu/6.031/www/sp22/classes/11-abstraction-functions-rep-invariants/) - specification mạnh so với yếu, và cách thiết lập và bảo toàn representation invariant.

**Thực hành thêm:** các quiz ở [LearnCpp: introduction to classes](https://www.learncpp.com/cpp-tutorial/introduction-to-classes/), [pure virtual functions and interface classes](https://www.learncpp.com/cpp-tutorial/pure-virtual-functions-abstract-base-classes-and-interface-classes/), [virtual destructors and override](https://www.learncpp.com/cpp-tutorial/virtual-destructors-virtual-assignment-and-overriding-virtualization/) và [object slicing](https://www.learncpp.com/cpp-tutorial/object-slicing/) (đáp án hiện trên mỗi trang), và phần [classes and class hierarchies](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#c-classes-and-class-hierarchies) của Core Guidelines làm checklist ôn tập cho `JointState` của riêng bạn.

