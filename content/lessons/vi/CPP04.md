---
{"title": "Class và OOP: đóng gói, interface và invariant", "summary": "Thiết kế các class mà các thao tác public không bao giờ để lại trạng thái không hợp lệ, và dùng abstract interface cho những hành vi thay đổi được.", "objectives": ["Phát biểu một class invariant và chỉ ra rằng constructor thiết lập nó còn mọi hàm thành viên public đều bảo toàn nó.", "Quyết định giữa struct và class, dữ liệu public và accessor, hàm thành viên và hàm tự do (free function).", "Thiết kế một abstract interface với virtual destructor và tránh slicing.", "Nhận ra khi nào kế thừa vi phạm tính thay thế được (substitutability) và chọn composition hoặc template thay thế."]}
---
## Vì sao điều này quan trọng

Phần mềm robot đầy những giá trị chỉ có nghĩa trong một khoảng: góc khớp nằm giữa các giới hạn của nó, một quaternion đơn vị, một hệ số khuếch đại phải không âm, một bước thời gian lớn hơn không. Nếu chúng là các field public trong một `struct`, bất kỳ dòng code nào ở đâu cũng có thể lưu 99 radian vào một khớp mà về mặt vật lý dừng ở 1.5, và bug xuất hiện muộn hơn, xa nguyên nhân, có thể là một lỗi phần cứng. Class sửa chuyện này bằng cách biến cách *duy nhất* để đổi trạng thái thành một hàm kiểm tra quy tắc. Nửa sau của bài, interface, là cách bạn đổi hành vi (bộ điều khiển P sang PID, driver giả lập sang driver thật) mà không phải viết lại phía gọi. Cùng nhau chúng là nền tảng của hầu hết thư viện robotics C++: hardware interface của ROS 2, planner của MoveIt, và plugin controller đều phơi ra những abstract interface nhỏ trên các class bảo vệ invariant của chúng.

## Trực giác

*Invariant* là một mệnh đề đúng mỗi khi quyền điều khiển nằm ngoài các hàm thành viên của class. "Vị trí nằm trong giới hạn và tốc độ không vượt quá mức tối đa" là một invariant. Class là một pháo đài nhỏ: constructor xây dựng invariant, mọi hàm public được phép giả định nó đúng khi vào và phải khôi phục nó khi ra, và dữ liệu private ngăn người ngoài chạm vào nó. Nếu một yêu cầu sẽ phá invariant, hàm từ chối (trả `false` hoặc throw) và để trạng thái không đổi.

*Interface* là một hợp đồng không có trạng thái: "đưa tôi một sai số, tôi đưa bạn một lệnh". Phía gọi phụ thuộc vào hợp đồng; phía cài đặt được tự do khác nhau. Vì phía gọi giữ một reference tới abstract base, override đúng được chọn lúc chạy thông qua bảng ảo (virtual table).

![Class JointState với trạng thái private và các thao tác public như một cánh cổng, và một abstract interface Controller với hai cài đặt](/lesson-figures/CPP04.svg)

*Các hàm public là cánh cửa duy nhất vào trạng thái private; một Controller trừu tượng cho phép phía gọi dùng bất kỳ cài đặt nào.*

## Lý thuyết và suy dẫn

### Invariant và mẫu chứng minh

Gọi $I(s)$ là invariant trên trạng thái $s$. Một class là đúng nếu

1. **Thiết lập (Establish):** sau mọi constructor thành công, $I$ đúng; một constructor thất bại sẽ throw, nên không có đối tượng dựng dở nào tồn tại.
2. **Bảo toàn (Preserve):** với mỗi thao tác public $f$, nếu $I(s)$ đúng trước lời gọi thì $I(s')$ đúng sau đó, dù $f$ trả về bình thường, trả về mã lỗi, hay throw.

Bằng quy nạp theo số lời gọi, $I$ đúng với mọi trạng thái có thể đạt tới. Với `JointState` có giới hạn $[l,h]$ và giới hạn tốc độ $v_{\max}$: $I(q,v) \equiv l\le q\le h \;\wedge\; |v|\le v_{\max}$ (đều hữu hạn). `try_set_position(q', dt)` chỉ đổi trạng thái nếu $l\le q'\le h$ và $|q'-q|/dt\le v_{\max}$; khi đó $v'=(q'-q)/dt$ thỏa $I$. Nếu không, nó không đổi gì, nên $I$ đúng hiển nhiên.

Hãy chú ý chi tiết cài đặt quan trọng: viết phép kiểm tra là `!(lo <= q && q <= hi)` hoặc kiểm tra tính hữu hạn trước. Với `NaN`, mọi phép so sánh đều sai, nên `if (q < lo || q > hi) reject` sẽ chấp nhận nó.

### Quy tắc thiết kế từ Core Guidelines

- Dùng `struct` khi dữ liệu *không* có invariant (mọi tổ hợp member đều hợp lệ), ví dụ `struct Pose2D { double x, y, theta; };`. Dùng `class` với dữ liệu private khi có invariant (C.2, C.8).
- Một constructor nên tạo một đối tượng *được khởi tạo đầy đủ và hợp lệ* hoặc throw (C.41, C.42). Tránh các hàm `init()` hai pha, vì chúng cho phép đối tượng không hợp lệ tồn tại.
- Đừng trả về reference hoặc con trỏ không-`const` tới member private; chúng vượt qua cánh cổng. Trả về giá trị hoặc `const&`.
- Ưu tiên hàm không phải thành viên cho các thao tác không cần truy cập private, để class nhỏ gọn (C.4).
- Đánh dấu constructor một đối số là `explicit` (C.46) để ngăn các chuyển đổi ngầm như `JointState j = 0.5;`.
- Mỗi hàm thành viên là `const` trừ khi nó thay đổi trạng thái.

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

### Tính thay thế (Substitutability)

Nếu code hoạt động với `Base&`, nó cũng phải hoạt động với bất kỳ `Derived` nào. Một `FixedJoint : Joint` có `set_position` throw sẽ phá điều này (nguyên lý thay thế Liskov): phía gọi không thể biết từ kiểu rằng lời gọi có hợp lệ hay không. Chỉ kế thừa khi class dẫn xuất *là một* loại thay thế được của base, nếu không hãy dùng composition (một member) hoặc các interface tách riêng (`Positionable` chỉ được cài đặt bởi các khớp di chuyển được).

## Ví dụ có lời giải

Thiết kế `JointState(lo=-1.5, hi=1.5, vmax=2.0)` và kiểm tra bằng tay một chuỗi cập nhật. Bắt đầu $q=0$, $v=0$.

1. Cập nhật `try_set_position(0.15, 0.1)`: trong khoảng ($-1.5\le0.15\le1.5$). Tốc độ $=|0.15-0|/0.1=1.5\le2$. Chấp nhận: $q=0.15$, $v=1.5$.
2. Cập nhật `try_set_position(0.9, 0.1)`: trong khoảng. Tốc độ $=|0.9-0.15|/0.1=7.5>2$. Từ chối; $q=0.15$, $v=1.5$ không đổi.
3. `dt` tối thiểu để bước tới 0.9 hợp lệ là bao nhiêu? Cần $0.75/dt\le2\Rightarrow dt\ge0.375$ s. `try_set_position(0.9, 0.375)` có tốc độ đúng bằng $0.75/0.375=2.0\le2$. Chấp nhận. (Trong dấu phẩy động, phép bằng nhau ở biên rất mong manh; code production thường dùng một dung sai nhỏ hoặc một bước nhỏ hơn chút.)
4. `try_set_position(1.6, 10.0)`: ngoài khoảng ($1.6>1.5$), từ chối bất kể `dt`.
5. Kiểm tra vòng kín với `PController(kp=2)`, `dt=0.1`, mục tiêu $1.0$, giới hạn rất lớn: $q_{k+1}=q_k+2(1-q_k)(0.1)=q_k+0.2(1-q_k)$, nên sai số co lại 0.8 lần mỗi bước: $q_k=1-0.8^k$. Sau 10 bước $q_{10}=1-0.107374=0.892626$.

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

## Đọc thêm

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - phần C về class, invariant (C.2, C.40-C.42), và hệ phân cấp (C.120-C.153).
- [cppreference: Classes](https://en.cppreference.com/w/cpp/language/classes) - các quy tắc chính xác về kiểm soát truy cập, constructor, hàm ảo và abstract class.
- [LearnCpp](https://www.learncpp.com/) - class, constructor, kế thừa và hàm ảo với các quiz có chấm điểm.

**Thực hành thêm:** các quiz ở [LearnCpp: introduction to classes](https://www.learncpp.com/cpp-tutorial/introduction-to-classes/), [pure virtual functions and interface classes](https://www.learncpp.com/cpp-tutorial/pure-virtual-functions-abstract-base-classes-and-interface-classes/), [virtual destructors and override](https://www.learncpp.com/cpp-tutorial/virtual-destructors-virtual-assignment-and-overriding-virtualization/) và [object slicing](https://www.learncpp.com/cpp-tutorial/object-slicing/) (đáp án hiện trên mỗi trang), và phần [classes and class hierarchies](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#c-classes-and-class-hierarchies) của Core Guidelines làm checklist ôn tập cho `JointState` của riêng bạn.
