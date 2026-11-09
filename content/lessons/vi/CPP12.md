---
{"title": "C++ nâng cao: thư viện generic, ABI và thiết kế hệ thống", "summary": "Thiết kế và kiểm toán interface của thư viện về quyền sở hữu, xử lý lỗi và tương thích nhị phân, với một ranh giới C ổn định và một wrapper C++ an toàn.", "objectives": ["Phân biệt API với ABI và phân loại các thay đổi là tương thích mã nguồn, tương thích nhị phân hay phá vỡ.", "Thiết kế một ranh giới C ổn định (opaque handle, mã lỗi, không có exception xuyên qua) và bọc nó bằng C++ RAII.", "Kiểm toán interface của một thư viện: ai sở hữu cái gì, trong bao lâu và trên thread nào.", "Chọn giữa code generic chỉ có header, thư viện đã biên dịch và pimpl cho một kiểu triển khai cho trước."]}
---
## Vì sao điều này quan trọng

Phần mềm robotics được lắp ghép từ các thư viện do các đội khác nhau viết, biên dịch vào các thời điểm khác nhau, và thường được phân phối dưới dạng binary: SDK của hãng camera, một thư viện lập kế hoạch chuyển động, các package ROS 2, một driver động cơ mã đóng. Các ranh giới giữa chúng là nơi bug cư trú. Một hàm nhận `Frame*` không cho biết ai giải phóng frame; một struct bị đổi bố cục ở phiên bản thư viện mới lặng lẽ đọc sai field trong một executable cũ; một exception ném bên trong một callback C làm sập cả process. Đây không phải lỗi cú pháp, compiler chấp nhận chúng, và chúng xuất hiện dưới dạng crash ngoài hiện trường. Bài này nói về đọc và viết interface sao cho quyền sở hữu, vòng đời, lỗi và tương thích nhị phân đều tường minh. Nó tổng hợp mọi thứ của chuỗi bài: RAII và move (CPP03), invariant và interface (CPP04), template (CPP06), hệ thống build và linking (CPP07), và hợp đồng đồng thời (CPP10).

## Trực giác

Hãy phân biệt hai loại tương thích. Tương thích **API** (application programming interface) nghĩa là *mã nguồn* từng dùng thư viện vẫn biên dịch được. Tương thích **ABI** (application binary interface) nghĩa là một chương trình *đã biên dịch* vẫn chạy khi binary của thư viện được thay bằng phiên bản mới, mà không biên dịch lại. ABI là mọi thứ mã máy dựa vào: tên symbol, calling convention (cách truyền đối số), kích thước và bố cục của các kiểu, bố cục vtable, xử lý exception.

Vì vậy một interface thư viện ổn định trông như một phích cắm: một bề mặt nhỏ, nhàm chán, tường minh (opaque handle, hàm thường, số nguyên và double thường, mã lỗi) với mọi thứ thú vị của C++ nằm phía sau. Bên trong code của riêng bạn thì bạn muốn ngược lại: kiểu phong phú, RAII và exception. Giải pháp chuẩn là hai tầng: một ranh giới kiểu C cho binary và một wrapper C++ mỏng chỉ có header để làm cho API C an toàn khi dùng.

![Các tầng: code người dùng, wrapper RAII C++, ABI C ổn định với opaque handle, phần bên trong thư viện; bên phải, bảng tương thích API/ABI của các thay đổi thông dụng](/lesson-figures/CPP12.svg)

*Một ranh giới C ổn định giữa wrapper (được biên dịch cùng code của người dùng) và phần bên trong thư viện; bảng phân loại các thay đổi điển hình.*

Hãy nghĩ binary của thư viện như một tòa nhà và chương trình của bạn như một vị khách đã thuộc lòng sơ đồ tầng từ một cuốn brochure in lúc biên dịch. Brochure (header) nói "thang máy là cửa thứ ba bên trái, và căn phòng bạn cần cách thang máy 24 byte". Nếu chủ sở hữu xây lại sảnh nhưng giữ nguyên địa chỉ đường phố (tên symbol), vị khách tự tin bước vào và mở nhầm cửa. Không gì báo hiệu sự không khớp: loader đã tìm thấy địa chỉ mà nó yêu cầu. Đó là lý do lỗi tương thích nhị phân khó chịu: chúng thầm lặng, xuất hiện sau một lần nâng cấp thư viện "vô hại", và hiện ra xa chỗ thay đổi dưới dạng giá trị hỏng, lời gọi nhầm hàm hoặc crash trong destructor.

Một ví dụ robotics: một nhà cung cấp giao `libcamera_sdk.so` và node perception của bạn link với nó. Một bản cập nhật distribution thay `.so` bằng phiên bản minor mới có thêm một trường vào struct public. Node của bạn, không biên dịch lại, vẫn là cùng mã máy, đọc trường `exposure` ở offset 16; thư viện giờ lưu `gain` ở đó. Ảnh sai nhẹ, node không crash, và một phép hiệu chuẩn trôi đi cả tuần. Đối lập với một API break, nơi compiler cho bạn biết lúc build chính xác dòng nào cần sửa.

**Hãy dự đoán trước khi tính.** Với mỗi thay đổi "thêm một member private vào class truyền theo giá trị", "thêm một hàm free mới", "đổi giá trị tham số mặc định" và "thêm một virtual function ở cuối class", hãy quyết định liệu *source* cũ còn biên dịch được không và *binary* cũ còn chạy đúng không. Viết ra bốn đáp án, rồi so với bảng phân loại trong phần lý thuyết; các trường hợp gây bất ngờ thường là tham số mặc định (được nhúng vào caller) và virtual function ở cuối.

**Trực giác sai thường gặp** là "nếu nó biên dịch và link được thì nó tương thích". Link chỉ kiểm tra rằng có một symbol với tên được yêu cầu; nó không kiểm tra bố cục, slot vtable, ý nghĩa của một hàm inline đã được sao chép vào caller, hay ABI thư viện chuẩn mà các kiểu được build cùng. Mô hình tư duy an toàn là: mọi thứ nhìn thấy trong header và được caller đã biên dịch dùng đều bị đóng băng, và tự do duy nhất nằm sau một con trỏ mờ hoặc một lời gọi hàm không inline.

## Lý thuyết và suy dẫn

### Symbol, name mangling và `extern "C"`

C++ cho phép overload, nên compiler mã hóa kiểu tham số và namespace vào tên symbol (*mangling*). Trong `.so` đã biên dịch:

```
c_add                                   <- extern "C" int c_add(int, int)
_Z7cxx_addii                            <- int cxx_add(int, int)
_ZN5robot8cxx_add2Eii                   <- robot::cxx_add2(int, int)
_Z12takes_vectorRKSt6vectorIiSaIiEE     <- takes_vector(const std::vector<int>&)
```
(`nm -D lib.so` liệt kê chúng; `nm -DC` giải mã tên.) Mangling khác nhau giữa các compiler và thậm chí giữa các phiên bản, nên một API C++ biên dịch bằng một toolchain nhìn chung không thể được gọi từ code biên dịch bằng toolchain khác. `extern "C"` tắt mangling và dùng calling convention của C, nên bất kỳ ngôn ngữ nào (C, Python `ctypes`, Rust FFI) cũng gọi được hàm.

### Cái gì thuộc về một ABI ổn định

An toàn qua ranh giới nhị phân: số nguyên độ rộng cố định, `double`, con trỏ, opaque handle, struct C thuần với *bố cục cố định, có tài liệu* (chỉ được thêm vào cuối nếu có phiên bản), con trỏ hàm với liên kết C, enum với kích thước nền tảng tường minh, `const char*` với chủ sở hữu có tài liệu. Rủi ro: `std::string`, `std::vector`, `std::shared_ptr`, `std::function` trong chữ ký (bố cục của chúng phụ thuộc phiên bản standard library và cờ: ví dụ dual ABI của GCC `_GLIBCXX_USE_CXX11_ABI` làm đổi `std::string`); hàm ảo (thêm hoặc sắp xếp lại làm đổi vtable); class có hàm thành viên inline chạm dữ liệu private (được inline vào phía gọi); template được khởi tạo ở cả hai phía; exception qua ranh giới; `new` trong thư viện và `delete` ở phía gọi nếu chúng dùng allocator hoặc runtime khác nhau.

**Thí nghiệm.** Phiên bản 1 của một thư viện phơi ra `struct Pose { double x; double y; }` và `get_pose(Pose*)`. Phiên bản 2 chèn `double z` vào giữa và viết lại hàm. Một ứng dụng biên dịch với header của phiên bản 1 nhưng chạy với phiên bản 2 in ra `x=1 y=9` thay vì `x=1 y=2`: nó đọc field `z` như `y`, và thư viện thậm chí ghi 24 byte vào đối tượng 16 byte của ứng dụng. Không có gì thất bại lúc link vì tên symbol `get_pose` không đổi.

### Phân loại thay đổi

| Thay đổi | API (mã nguồn) | ABI (nhị phân) |
|---|---|---|
| Thêm một hàm tự do mới | tương thích | tương thích |
| Thêm một giá trị enum | tương thích (switch có thể cảnh báo) | tương thích nếu kích thước không đổi; code cũ có thể không xử lý nó |
| Đổi kiểu tham số hoặc thêm tham số | phá vỡ | phá vỡ (symbol/chữ ký mới) |
| Sắp xếp lại hoặc thêm data member public | thường tương thích | phá vỡ (bố cục) |
| Thêm một hàm ảo | tương thích | phá vỡ (bố cục vtable) |
| Thêm data member private vào class dùng theo giá trị | tương thích | phá vỡ (`sizeof` đổi) |
| Đổi hành vi nhưng không đổi chữ ký | tương thích | tương thích (nhưng có thể vi phạm hợp đồng) |
| Thêm data member vào class dùng pimpl | tương thích | tương thích (ẩn sau một con trỏ) |

### Opaque handle, pimpl và quyền sở hữu

**Opaque handle** (C): `typedef struct rc_arm rc_arm;` cùng `rc_arm* rc_arm_create(...)` và `rc_arm_destroy(rc_arm*)`. Phía gọi không bao giờ thấy bố cục, nên thư viện có thể đổi nó tự do. Hợp đồng nêu rằng bên tạo sở hữu vùng cấp phát: create/destroy đi thành cặp.

**Pimpl idiom** (C++): class giữ `std::unique_ptr<Impl>` tới một kiểu cài đặt ẩn được định nghĩa trong `.cpp`. Header public giữ cùng kích thước mãi mãi. Cạm bẫy: destructor (và các phép move) phải được định nghĩa trong `.cpp`, nơi `Impl` đầy đủ; nếu không compiler sinh chúng inline ở nơi `Impl` chưa đầy đủ, và thất bại với "invalid application of 'sizeof' to incomplete type".

**Từ vựng về quyền sở hữu** cần tìm trong bất kỳ interface nào (Core Guidelines I.11, F.26): con trỏ thô do hàm trả về (ai giải phóng?), tham số con trỏ thô (mượn hay nhận?), `const char*` trả về (tĩnh, hay hợp lệ đến lời gọi tiếp theo?), callback với `void* user_data` (vòng đời dữ liệu, thread của lời gọi), handle chia sẻ (các bản copy `cv::Mat` chia sẻ buffer pixel: phép gán là nông, `clone()` là sâu), view (`std::string_view`, `Eigen::Map`, `std::span`) không sở hữu.

### Lỗi qua ranh giới

Một exception không được lan truyền ra khỏi một hàm `extern "C"`: nếu bên gọi là C, Python hay một runtime khác không thể unwind các frame C++, hành vi là undefined và thường là `std::terminate`. Thí nghiệm: `risky(-3)` trong một shared library có throw, được gọi qua Python `ctypes`, làm process abort với `terminate called after throwing an instance of 'std::invalid_argument'`. Ranh giới C bắt mọi thứ và trả về một mã lỗi; wrapper C++ dịch mã đó trở lại thành exception (hoặc `std::expected`/`optional` nơi exception bị cấm). Cũng cung cấp `rc_strerror(code)` trả về một chuỗi tĩnh.

### Thư viện generic và ABI

Template được khởi tạo trong translation unit dùng chúng, nên một thư viện chỉ có header (Eigen, phần lớn standard library) không có ABI của riêng nó: compiler của người dùng sinh code, và các phiên bản compiler khác nhau trong một chương trình cùng tồn tại miễn là không có đối tượng kiểu template nào đi qua ranh giới nhị phân. Một thư viện đã biên dịch có template trong interface có thể giảm thời gian biên dịch bằng explicit instantiation (`extern template class Filter<double>;` trong header và `template class Filter<double>;` trong một `.cpp`), nhưng khi đó chỉ những instantiation đó có sẵn, và bố cục của `Filter<double>` là một phần của ABI.

### Checklist thiết kế hệ thống

Với mỗi hàm public hãy ghi ra: **Ai sở hữu** từng con trỏ/handle làm đối số và kết quả; **hợp lệ trong bao lâu**; **thread nào** được gọi nó và nó có reentrant không (CPP10); **những lỗi nào** nó báo và bằng cách nào; **cái gì có thể đổi** trong một phiên bản minor. Giao những điều này dưới dạng comment hoặc tài liệu cạnh khai báo, và mã hóa chúng vào kiểu khi có thể (`unique_ptr` cho chuyển giao, reference cho mượn, `const` cho chỉ đọc).

### Bố cục object theo Itanium ABI: `dsize`, `nvsize` và tail padding được tái sử dụng

Bảng trên nói "thêm một data member private: phá ABI". Itanium C++ ABI, mà GCC và Clang theo trên Linux, làm điều đó chính xác hơn (Itanium C++ ABI, §2.4 "Non-POD Class Types"; §2.1 "General" định nghĩa các thuật ngữ). Mỗi kiểu có bốn cỡ: `sizeof(T)` (gồm tail padding), `dsize(T)` (*data size*, cỡ không tính tail padding), `nvsize(T)` (cỡ không tính virtual base) và một alignment. Member và base được đặt lần lượt, mỗi cái ở offset kế tiếp thỏa alignment của nó, xuất phát từ `dsize(C)` hiện tại. Với một base **không phải POD theo nghĩa bố cục**, subobject kế tiếp có thể bắt đầu tại `offset(D)+dsize(D)`, tức tái sử dụng tail padding của base; với base POD thì bắt đầu tại `offset(D)+sizeof(D)`.

Hệ quả: với `struct A { int a; char b; ~A(); }` ta có $\mathrm{dsize}=5$, $\mathrm{sizeof}=8$, và trong `struct B : A { char c; }` member `c` nằm ở offset 5, nên `sizeof(B)==8`. Nếu `A` là POD (không có destructor do người dùng khai báo, không có member private), `c` sẽ nằm ở offset 8 và `sizeof(B)==12`. Có hai bài học thực tế. Thứ nhất, `memcpy` một `A` lên phần `A` của một `B` cũng sao chép luôn padding và có thể ghi đè `B::c`; đó là lý do `memcpy` lên subobject base hoặc kiểu không trivially-copyable là undefined và thực sự gây lỗi. Thứ hai, kiểm tra ABI chỉ dựa trên `sizeof` là **không đủ**: một thay đổi ở `A` có thể dời `B::c` mà không đổi cỡ nào (bài tập 13). Hãy kiểm tra bố cục bằng công cụ (`-fdump-lang-class` của GCC, `-Xclang -fdump-record-layouts` của Clang) trong CI.

### Mangling chi tiết: substitution và kiểu trả về

Một tên đã mangle được dựng từ `<nested-name>` (`N ... E`), các source name có tiền tố độ dài, và `<bare-function-type>`, danh sách kiểu tham số (Itanium C++ ABI, §5.1). Hai quy tắc quan trọng cho công việc ABI. **Nén (compression)** (§5.1.10): mỗi thành phần có thể thay thế (một tiền tố namespace hay class, một template-id, một tên template, một kiểu có qualifier, con trỏ hay tham chiếu; kiểu builtin và các viết tắt định sẵn `St`, `Sa`, `Ss` thì không) được đánh số từ trái sang phải là `S_`, `S0_`, `S1_`, ... và các lần xuất hiện sau được thay bằng chỉ số đó. Một thành phần được đánh số trước cấu trúc lớn hơn chứa nó. Thứ hai, **kiểu trả về** chỉ được mã hóa với hàm template (§5.1.5.3): `void f(P*)` và `bool f(P*)` không phải template đều mangle thành `_Z1fP1P`. Vì vậy đổi kiểu trả về của một hàm thường được export **không** gây lỗi link và là một phá ABI thầm lặng (và vi phạm ODR nếu cả hai phiên bản cùng có trong một chương trình), trong khi cùng thay đổi đó với một function template sẽ đổi tên symbol.

### Dual ABI: cái gì đổi trong symbol và cái gì không

Từ GCC 5, libstdc++ đưa hai cài đặt vào một thư viện: `std::string` copy-on-write đếm tham chiếu cũ và `std::list` có `size()` là $O(n)$, và các bản tuân thủ C++11 trong inline namespace `std::__cxx11`. Macro `_GLIBCXX_USE_CXX11_ABI` chọn bản mà header của một translation unit dùng (libstdc++ manual, "Dual ABI"). Vì hai kiểu có tên mangle khác nhau, sự không khớp ở *chữ ký* sẽ bị linker bắt: `void f(const std::string&)` thành `...RKSs` (cũ) so với `...RKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE` (mới), và hàm *trả về* `std::string` nhận tag `B5cxx11`, khi demangle hiện là `[abi:cxx11]`. Trường hợp nguy hiểm là một **member** `std::string` của một struct được truyền bằng tham chiếu: struct vẫn tên `Config`, hàm vẫn mangle thành `_Z6get_idRK6Config`, linker hài lòng, nhưng `sizeof(std::string)` là 8 byte ở ABI cũ và 32 byte ở ABI mới, nên mọi member sau đó nằm ở offset khác (bài tập 14).

### Virtual table: vì sao "thêm một virtual function ở cuối" cũng là phá

Với một class có virtual function, primary vtable bắt đầu bằng *offset-to-top* và một con trỏ RTTI, tiếp theo là các con trỏ virtual function theo thứ tự khai báo, với hai mục destructor (complete và deleting) ở vị trí của destructor (Itanium C++ ABI, §2.5.2 và §2.5.3). Lời gọi `b->g()` được biên dịch thành "nạp vptr, nạp slot $k$, gọi" với $k$ cố định lúc biên dịch từ *header*. Một override hoặc một virtual function thêm vào ở class dẫn xuất được đặt ở các slot sau slot của base. Nếu base class được thêm một virtual function ở phiên bản thư viện sau, mọi slot sau nó dịch đi một trong code đã biên dịch của thư viện, nhưng các vtable đã phát sinh trong binary của client (cho các class dẫn xuất từ `Base`) vẫn giữ cách sắp xếp cũ. Code client biên dịch và link được, và thư viện gọi nhầm hàm (bài tập 15). Thêm virtual function vào *giữa* là phá với mọi class dẫn xuất đã biên dịch trước; thêm vào cuối chỉ phá với các class dẫn xuất tự đưa vào virtual riêng; và một class không có virtual function nào (Category 0 trong §2.5.3) không có vtable nên không có vấn đề này, thêm một lý do để ưu tiên opaque handle.

## Ví dụ có lời giải

### Trường hợp cơ bản

**Đề bài.** Kiểm toán header SDK camera giả định này, rồi thiết kế một wrapper C++ an toàn. Với mỗi khai báo, nêu ai sở hữu bộ nhớ, thread nào có thể chạy code và điều gì có thể hỏng.

```c
typedef struct cam cam;
cam* cam_open(const char* device);
void cam_close(cam* c);
const char* cam_error(void);
unsigned char* cam_grab(cam* c, int* size);
void cam_on_frame(cam* c, void (*cb)(unsigned char*, int, void*), void* user);
```

**Lời giải.**

1. `cam_open` trả về một con trỏ: **do bên gọi sở hữu**, được giải phóng bằng `cam_close` (theo quy ước đặt tên; header không nói). `NULL` khi thất bại; lý do nằm trong `cam_error()`, một biến toàn cục, nên nó **không thread-safe**.
2. `cam_error()` trả về `const char*`: chủ sở hữu không rõ; có lẽ là một buffer tĩnh bị lời gọi tiếp theo ghi đè, nên phải copy ngay lập tức.
3. `cam_grab` trả về `unsigned char*` và kích thước qua một tham số out: **ai giải phóng buffer?** Hoặc camera tái sử dụng một buffer nội bộ (hợp lệ đến lần grab tiếp theo) hoặc bên gọi phải free. Header im lặng: một *rủi ro*. Wrapper an toàn phải copy vào một `std::vector<unsigned char>` ngay lập tức.
4. `cam_on_frame` đăng ký một callback với `void* user`: callback chạy trên một **thread không rõ** (có lẽ là thread của driver); `user` phải sống lâu hơn thời gian đăng ký; con trỏ buffer chỉ hợp lệ trong lúc callback. Một exception ném trong callback sẽ xuyên qua các frame C.
5. Thiết kế wrapper, mỗi quy tắc đối ứng một rủi ro ở trên: `class Camera` giữ `unique_ptr<cam, decltype(&cam_close)>` (trả lời bước 1: destructor đóng camera), throw `Error` từ constructor khi `cam_open` trả null, với thông báo được copy ngay từ `cam_error()` (bước 2), `grab()` trả `std::vector<unsigned char>` (bước 3), trampoline của callback là một hàm static bắt mọi exception và lưu chúng lại (bước 4), và `~Camera` hủy đăng ký callback rồi đóng camera, theo đúng thứ tự đó, để callback không thể chạy trên một `Camera` đã bị hủy.

**Kiểm tra.** Đối chiếu các sự kiện về con trỏ thô trong header với wrapper: có 4 câu hỏi về quyền sở hữu hoặc thread (bước 1 đến 4) và mỗi câu có đúng một cơ chế trong wrapper ở bước 5, nên interface public không còn con trỏ thô hay truy cập từ thread lạ. Thứ tự hủy kiểm tra được bằng cách đọc destructor: hủy đăng ký trước, đóng sau; thứ tự ngược lại để hở một khoảng thread của driver gọi vào thiết bị đã đóng.

**Rút ra.** Kết quả là một interface trong đó quyền sở hữu nằm trong kiểu: người dùng không bao giờ thấy một con trỏ thô hay một thread do thư viện tạo.

### Trường hợp khó hơn: tiến hóa một struct public mà không phá binary cũ

**Đề bài.** Một thư viện chuyển động export `get_pose(Pose*)` và muốn thêm tọa độ `z` mà không phá các binary build với phiên bản 1. Struct bố cục cố định của thí nghiệm trước không làm được, nên dùng mẫu *struct có tiền tố kích thước*. Header phiên bản 1: `struct Pose { uint32_t size; double x, y; };` và caller đặt `p.size = sizeof(Pose)` trước khi gọi. Phiên bản 2 thêm `z` ở cuối: `struct Pose { uint32_t size; double x, y, z; };`, và thư viện chỉ sao chép `min(caller_size, sizeof(Pose))` byte. Tính bố cục trên x86-64, chỉ ra điều xảy ra với caller cũ gọi thư viện mới và caller mới gọi thư viện cũ, và nêu cái giá của mẫu này.

**Lời giải.**

1. *Bố cục.* Trên x86-64, `size` chiếm byte 0-3. `double` cần alignment 8, nên theo sau là 4 byte padding, `x` ở offset 8, `y` ở offset 16; thành viên cuối kết thúc tại 16 + 8 = 24, là bội của 8, vậy `sizeof(Pose1)=24`. Phiên bản 2 thêm `z` ở offset 24, kết thúc ở 32, nên `sizeof(Pose2)=32`.
2. *Caller cũ, thư viện mới.* Caller truyền một object 24 byte với `size=24`. Thư viện dựng kết quả 32 byte bên trong và sao chép `min(24, 32) = 24` byte, nên `x=1`, `y=2` đúng, `size=24` được báo lại, và các byte canh gác đặt sau object của caller không bị đụng tới. Biên dịch trong hai translation unit, chương trình in `sizeof Pose1=24 Pose2=32 x=1 y=2 size=24 canary=127` (127 là byte canh gác không đổi).
3. *Caller mới, thư viện cũ.* Caller đặt `size=32`. Thư viện cũ chỉ biết 24 byte và phải báo đã ghi bao nhiêu bằng cách đặt `size=24`, để caller mới biết `z` không được cung cấp và không được đọc. Nếu thiếu quy tắc này caller sẽ đọc bộ nhớ chưa khởi tạo.
4. *Mẫu này tốn gì và không làm được gì.* Trường mới chỉ được thêm vào cuối, thư viện không bao giờ được đọc vượt quá `caller_size`, và ý nghĩa của mỗi trường phải cố định mãi mãi. Nó không giúp được với trường ở giữa, với kiểu của trường hiện có bị đổi, hay với class có virtual function. Với các trường hợp đó, lựa chọn thay thế là opaque handle với hàm accessor (`pose_get_z`) hoặc một hàm mới với struct mới (`get_pose_v2`).

**Kiểm tra.** Biên dịch bằng `g++ -std=c++20` trong hai translation unit (thư viện dùng struct 32 byte, caller dùng struct 24 byte): `offsetof` cho x=8, y=16, z=24, kích thước 24 và 32, và byte canh gác vẫn là 127, nên không có lần ghi nào vượt quá 24 byte. Quy tắc `min` là toàn bộ sự đảm bảo: với `size=24` nó không bao giờ ghi byte 24 trở đi.

**Rút ra.** Đánh đổi quyết định: struct có tiền tố kích thước giữ một C struct phẳng, copy được, rẻ và đơn giản để dùng từ Python `ctypes`, còn opaque handle tốn một lời gọi hàm cho mỗi trường nhưng cho phép thư viện đổi mọi thứ.

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** Với danh sách `nm -D` ở trên, các symbol nào có thể gọi từ Python bằng `ctypes` theo tên thường, và vì sao? `_Z7cxx_addii` mang thông tin gì?
2. **(Dễ)** *(Adapted from: KDE, Binary Compatibility Issues With C++)* Phân loại là phá vỡ API, chỉ phá vỡ ABI, hay không cái nào: (a) thêm một member private vào một class dùng theo giá trị; (b) thêm một hàm tự do mới; (c) thêm một hàm ảo vào một class có subclass ở các thư viện khác; (d) đổi giá trị đối số mặc định của một hàm; (e) đổi tên một tham số; (f) đổi `int` thành `long` trong một tham số.
3. **(Dễ)** *(Adapted from: C++ Core Guidelines, I.11 and F.26)* Với mỗi khai báo nêu chữ ký nói gì về quyền sở hữu và để lại điều gì không nói: `Frame* grab();`, `void put(Frame*);`, `const char* name() const;`, `void set_cb(Callback, void*);`, `std::unique_ptr<Map> load(const std::string&);`.
4. **(Trung bình)** Tìm hai bug trong hàm giao diện C này và sửa chúng:
   ```cpp
   extern "C" const char* describe(int code) {
     if (code < 0) throw std::invalid_argument("negative");
     std::string s = "code " + std::to_string(code);
     return s.c_str();
   }
   ```
5. **(Trung bình)** *(Adapted from: OpenCV documentation, "Mat - the basic image container")* Một class giữ một `std::shared_ptr<std::vector<int>>` giống như header `cv::Mat` chia sẻ pixel. `a.at(0)`, `b.at(0)` và `c.at(0)` in ra gì sau `Image a(3,1); Image b = a; Image c = a.clone(); b.fill(7);`? Bug robotics nào xảy ra khi một callback lưu một bản copy của frame?
6. **(Trung bình)** Viết header và `.cpp` của `Planner` với pimpl. Một translation unit của người dùng chỉ include header và tạo một `Planner` thất bại với "invalid application of 'sizeof' to incomplete type". Vì sao, và cách sửa một dòng là gì?
7. **(Trung bình)** Diễn giải thí nghiệm: ứng dụng in ra `x=1 y=9` sau khi thư viện bị hoán đổi. Giải thích chính xác điều gì đã xảy ra theo độ lệch (offset), và nêu ba cách để phát triển struct mà không phá các binary cũ.
8. **(Khó)** *(Adapted from: libstdc++ manual, dual ABI)* Một `.so` dựng sẵn được biên dịch với `_GLIBCXX_USE_CXX11_ABI=0` và xuất `void f(const std::string&)`. Code của bạn dùng mặc định. Điều gì xảy ra lúc link và vì sao? Liệt kê ba chiến lược cho một nhà cung cấp phân phối SDK dạng binary.
9. **(Khó)** Xem xét header giả định này và liệt kê ít nhất sáu rủi ro về quyền sở hữu, vòng đời, thread hoặc ABI, rồi viết lại nó:
   ```cpp
   // libgrip.h (hypothetical)
   struct GripperState { double width; double force; int status; };
   class Gripper {
    public:
     Gripper(const std::string& port);
     GripperState* poll();                 // returns internal state
     void on_contact(std::function<void(GripperState)> cb);
     virtual void close(double width);
     std::vector<double> history;
   };
   ```
10. **(Khó)** Bạn bảo trì một `Filter<T>` generic cho `float` và `double`. So sánh (i) chỉ có header, (ii) thư viện đã biên dịch với explicit instantiation, (iii) một API C với hai bộ hàm. Đánh giá thời gian biên dịch, tính ổn định ABI, khả năng mở rộng sang `long double`, và kích thước binary.
11. **(Mini-project)** Chọn một interface thư viện robotics thật mà bạn dùng (ví dụ callback subscription của `rclcpp`, `cv::Mat`, `Eigen::Map`, hay `tf2::Buffer`) và viết một bản kiểm toán quyền sở hữu một trang (hàm, chủ sở hữu, vòng đời, thread, báo lỗi, rủi ro ABI) cộng một wrapper hoặc test 30 dòng chứng minh một rủi ro.
12. **(Thử thách)** *Mangle bằng tay.* Dùng các quy tắc substitution, suy ra tên đã mangle của `void robot::Planner::replan(const std::vector<robot::Pose>& a, robot::Pose* b, const robot::Planner& c, std::vector<robot::Pose>& d)`. Liệt kê bảng substitution `S_`, `S0_`, ... mà bạn dựng, và giải thích vì sao các kiểu tham số lặp lại trong `a`, `c`, `d` trở thành substitution ngắn. Sau đó nêu việc đổi kiểu trả về từ `void` sang `bool` có đổi symbol không, và chuyện gì xảy ra lúc chạy khi một caller cũ gặp thư viện mới. Kiểm tra bằng `g++ -c` và `nm`. *(phỏng theo Itanium C++ ABI, §5.1.10 "Compression" và §5.1.5.3 "Function types")*
13. **(Thử thách)** *Padding dịch chuyển.* Cho `struct A { int a; char b; ~A(); }; struct B : A { char c; };` trên x86-64 Linux. (a) Cho `dsize(A)`, `sizeof(A)`, offset của `B::c` và `sizeof(B)`. (b) Lặp lại khi bỏ destructor khỏi `A` và thay `A` bằng một struct thường `PA` có cùng member (và `PB : PA`). (c) Chỉ ra bằng `memcpy` vì sao sao chép một `A` lên phần `A` của một `B` là nguy hiểm trong trường hợp (a). (d) Phiên bản 2 của thư viện thêm `char d;` vào `A` (sau `b`). Tính `sizeof(A)`, `sizeof(B)` mới và offset của `B::c`. Vì sao một bài test ABI chỉ so sánh `sizeof` có thể bỏ sót lỗi phá này? *(phỏng theo Itanium C++ ABI, §2.4 "Non-POD Class Types")*
14. **(Thử thách)** *Sai lệch mà linker chấp nhận.* Một thư viện được build với `-D_GLIBCXX_USE_CXX11_ABI=0` và export `int get_id(const Config&)` với `struct Config { std::string name; int id; };`. Ứng dụng dùng ABI mặc định, tạo `Config c{"arm", 42}` và gọi `get_id(c)`. (a) Cho tên đã mangle của `get_id` ở hai bản build và nói việc link có thành công không. (b) Dự đoán `sizeof(Config)` ở mỗi ABI và giá trị `get_id` trả về, giải thích từ hai bố cục. (c) Đề xuất hai thay đổi ở interface thư viện để biến lỗi thầm lặng này thành lỗi link hoặc thành chương trình đúng. Chạy thí nghiệm. *(phỏng theo libstdc++ manual, "Dual ABI")*
15. **(Thử thách)** *Hàm nào chạy?* Phiên bản 1 của header thư viện là `struct Base { virtual ~Base(); virtual int f(); virtual int g(); };`. Một ứng dụng định nghĩa `struct Derived : Base { int g() override { return 30; } virtual int extra() { return 99; } };` dựa trên phiên bản 1. Thư viện được nâng lên phiên bản 2, `struct Base { virtual ~Base(); virtual int f(); virtual int h(); virtual int g(); };` với `h()` trả về 2 và `g()` trả về 3, và export `int call_g(Base*)` và `int call_h(Base*)` chỉ chuyển tiếp tới `b->g()` và `b->h()`. Ứng dụng *không* được biên dịch lại. (a) Viết vtable của `Derived` như ứng dụng thấy, kèm số slot. (b) Hàm nào chạy với `call_g(&d)` và `call_h(&d)`? (c) Mô tả một thiết kế phía thư viện (vẫn giữ virtual function trong header) cho phép phiên bản 3 thêm hành vi mà không gặp lỗi này. *(phỏng theo Itanium C++ ABI, §2.5.2 và §2.5.3, và danh sách thay đổi không tương thích nhị phân trong KDE, Binary Compatibility Issues With C++)*

## Cài đặt tham khảo

Một mô hình đầy đủ trong một file của một thư viện với ABI C (opaque handle, mã lỗi, không có exception qua ranh giới, một hook kiểm thử) và wrapper RAII C++. Trong một dự án thật, phần giữa được biên dịch thành `libarm.so` và wrapper nằm trong header được cài đặt. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

```cpp
// CPP12 reference: a C ABI around a C++ implementation (opaque handle, error codes, no exceptions
// across the boundary) and a safe C++ RAII wrapper on top of it.
#include <cmath>
#include <cstddef>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

// ---------------- the C interface (what a header robot_c_api.h would declare) ----------------
extern "C" {
typedef struct rc_arm rc_arm;  // opaque: callers never see the layout
enum { RC_OK = 0, RC_ERR_NULL = -1, RC_ERR_RANGE = -2, RC_ERR_VALUE = -3 };

rc_arm* rc_arm_create(int dof);  // caller owns the result; release with rc_arm_destroy; NULL on failure
void rc_arm_destroy(rc_arm* arm);  // accepts NULL
int rc_arm_set_joint(rc_arm* arm, int index, double angle);
int rc_arm_get_joint(const rc_arm* arm, int index, double* out);
int rc_arm_dof(const rc_arm* arm);                // number of joints, or a negative error code
const char* rc_strerror(int code);                // static storage: do not free
int rc_live_arms(void);                           // test hook: number of arms not yet destroyed
}

// ---------------- implementation (compiled into the shared library) ----------------
struct rc_arm {
  std::vector<double> q;
};
static int g_live = 0;

extern "C" {
rc_arm* rc_arm_create(int dof) {
  try {  // an exception must never cross the C boundary
    if (dof <= 0 || dof > 32) return nullptr;
    rc_arm* a = new rc_arm{std::vector<double>(static_cast<std::size_t>(dof), 0.0)};
    ++g_live;
    return a;
  } catch (...) {
    return nullptr;
  }
}
void rc_arm_destroy(rc_arm* arm) {
  if (!arm) return;
  delete arm;
  --g_live;
}
int rc_arm_set_joint(rc_arm* arm, int index, double angle) {
  if (!arm) return RC_ERR_NULL;
  if (index < 0 || static_cast<std::size_t>(index) >= arm->q.size()) return RC_ERR_RANGE;
  if (!std::isfinite(angle)) return RC_ERR_VALUE;
  arm->q[static_cast<std::size_t>(index)] = angle;
  return RC_OK;
}
int rc_arm_get_joint(const rc_arm* arm, int index, double* out) {
  if (!arm || !out) return RC_ERR_NULL;
  if (index < 0 || static_cast<std::size_t>(index) >= arm->q.size()) return RC_ERR_RANGE;
  *out = arm->q[static_cast<std::size_t>(index)];
  return RC_OK;
}
int rc_arm_dof(const rc_arm* arm) { return arm ? static_cast<int>(arm->q.size()) : RC_ERR_NULL; }
const char* rc_strerror(int code) {
  switch (code) {
    case RC_OK: return "ok";
    case RC_ERR_NULL: return "null handle or pointer";
    case RC_ERR_RANGE: return "joint index out of range";
    case RC_ERR_VALUE: return "angle is not finite";
    default: return "unknown error";
  }
}
int rc_live_arms(void) { return g_live; }
}

// ---------------- the C++ wrapper (header-only, ships with the user's code) ----------------
class Error : public std::runtime_error {
 public:
  explicit Error(int code) : std::runtime_error(rc_strerror(code)), code_(code) {}
  int code() const { return code_; }

 private:
  int code_;
};

inline void check(int code) {
  if (code != RC_OK) throw Error(code);
}

// Owns an rc_arm. Move-only; a moved-from Arm is empty and every operation on it throws Error(RC_ERR_NULL).
class Arm {
 public:
  explicit Arm(int dof) : h_(rc_arm_create(dof), &rc_arm_destroy) {
    if (!h_) throw std::invalid_argument("rc_arm_create failed (dof must be in 1..32)");
  }
  Arm(Arm&&) noexcept = default;
  Arm& operator=(Arm&&) noexcept = default;

  void set(int index, double angle) { check(rc_arm_set_joint(h_.get(), index, angle)); }
  double get(int index) const {
    double out = 0.0;
    check(rc_arm_get_joint(h_.get(), index, &out));
    return out;
  }
  int dof() const {
    const int n = rc_arm_dof(h_.get());
    check(n < 0 ? n : RC_OK);
    return n;
  }

 private:
  std::unique_ptr<rc_arm, void (*)(rc_arm*)> h_;
};

// ---- self-test
int main() {
  static_assert(!std::is_copy_constructible_v<Arm>);
  static_assert(std::is_nothrow_move_constructible_v<Arm>);
  {
    Arm a(3);
    a.set(1, 0.5);
    Arm b = std::move(a);
    if (b.get(1) != 0.5 || b.dof() != 3 || rc_live_arms() != 1) return 1;
    try { a.get(0); return 2; } catch (const Error& e) { if (e.code() != RC_ERR_NULL) return 3; }
    try { b.set(3, 1.0); return 4; } catch (const Error& e) { if (e.code() != RC_ERR_RANGE) return 5; }
  }
  if (rc_live_arms() != 0) return 6;
  std::cout << "CPP12 reference self-test passed\n";
}
```

Các lệnh dùng để khảo sát và phá vỡ tương thích nhị phân:

```
g++ -std=c++17 -shared -fPIC mylib.cpp -o libmy.so
nm -D libmy.so | grep ' T '          # exported symbols; add -C to demangle
ldd ./app                            # which shared libraries are resolved
g++ -shared -fPIC pose_v1.cpp -o libpose.so && g++ app.cpp -L. -lpose -Wl,-rpath,'$ORIGIN' -o app && ./app   # x=1 y=2
g++ -shared -fPIC pose_v2.cpp -o libpose.so && ./app                                                        # x=1 y=9
```

## Thực hành độc lập

### Mục tiêu

Cài đặt một interface C với opaque handle và mã lỗi, bọc nó trong một class RAII chỉ-move, chứng minh bằng test rằng quyền sở hữu và lỗi được xử lý, và viết bản kiểm toán quyền sở hữu ghi tài liệu cho interface.

### Chuẩn bị

`g++` với C++17 (`nm`, `ldd` cho bước shared library tùy chọn). Lưu starter rồi các test bên dưới nó thành `lab.cpp`; build bằng `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab`.

### Nhiệm vụ

1. Định nghĩa `struct rc_arm`, phần ghi sổ live-count và cài đặt `rc_arm_create`, `rc_arm_destroy`, `rc_arm_dof`, `rc_strerror`, `rc_live_arms`. Bọc các thân hàm trong `try/catch(...)`.
2. Cài đặt `rc_arm_set_joint` và `rc_arm_get_joint` với mọi mã lỗi, đảm bảo một lời gọi bị từ chối không thay đổi gì.
3. Cài đặt `check`, thông báo của `Error` và `Arm` (constructor, `set`, `get`, `dof`); các phép move mặc định phải để một `Arm` đã bị move throw `Error(RC_ERR_NULL)`.
4. Chạy các test dưới ASan và xác nhận `rc_live_arms()` trở về 0 sau mỗi scope (kể cả khi một exception được throw).
5. Tách file: biên dịch phần C-API thành `libarm.so` và kiểm tra `nm -D libarm.so | grep rc_` cho thấy các tên không bị mangle; link một `main` nhỏ với nó.
6. Viết bản kiểm toán quyền sở hữu (một bảng 7 hàm với chủ sở hữu, vòng đời, an toàn thread, lỗi, rủi ro ABI) và một đoạn về cách bạn mở rộng struct ở phiên bản 2 mà không phá các binary cũ.

### Code khởi đầu

```cpp
#include <cmath>
#include <cstddef>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

// ---------------- C interface: DO NOT change these declarations ----------------
extern "C" {
typedef struct rc_arm rc_arm;  // opaque handle
enum { RC_OK = 0, RC_ERR_NULL = -1, RC_ERR_RANGE = -2, RC_ERR_VALUE = -3 };

rc_arm* rc_arm_create(int dof);      // 1..32 joints, all angles 0.0; NULL if dof is out of range or allocation fails
void rc_arm_destroy(rc_arm* arm);    // accepts NULL (no-op)
int rc_arm_set_joint(rc_arm* arm, int index, double angle);       // RC_ERR_NULL / RC_ERR_RANGE / RC_ERR_VALUE (non-finite angle)
int rc_arm_get_joint(const rc_arm* arm, int index, double* out);  // RC_ERR_NULL for null arm OR null out; RC_ERR_RANGE
int rc_arm_dof(const rc_arm* arm);   // number of joints, or RC_ERR_NULL
const char* rc_strerror(int code);   // static strings: "ok", "null handle or pointer", "joint index out of range",
                                     // "angle is not finite", and "unknown error" for anything else
int rc_live_arms(void);              // test hook: number of arms created and not yet destroyed
}

// ---------------- implementation of the interface ----------------
// TODO: define struct rc_arm (hold the joint angles) and the bookkeeping behind rc_live_arms.
// Rules: no C++ exception may escape any extern "C" function (catch everything, return an error).
extern "C" {
rc_arm* rc_arm_create(int dof) { throw std::logic_error("NotImplemented"); }
void rc_arm_destroy(rc_arm* arm) { throw std::logic_error("NotImplemented"); }
int rc_arm_set_joint(rc_arm* arm, int index, double angle) { throw std::logic_error("NotImplemented"); }
int rc_arm_get_joint(const rc_arm* arm, int index, double* out) { throw std::logic_error("NotImplemented"); }
int rc_arm_dof(const rc_arm* arm) { throw std::logic_error("NotImplemented"); }
const char* rc_strerror(int code) { throw std::logic_error("NotImplemented"); }
int rc_live_arms(void) { throw std::logic_error("NotImplemented"); }
}

// ---------------- C++ wrapper ----------------
// Error(code): std::runtime_error whose what() is rc_strerror(code); code() returns the code.
class Error : public std::runtime_error {
 public:
  explicit Error(int code) : std::runtime_error("TODO"), code_(code) {}
  int code() const { return code_; }

 private:
  int code_;
};

// throws Error(code) unless code == RC_OK
inline void check(int code) { throw std::logic_error("NotImplemented"); }

// Owns an rc_arm through std::unique_ptr<rc_arm, void (*)(rc_arm*)>. Move-only. The constructor throws
// std::invalid_argument if rc_arm_create fails. A moved-from Arm is empty: every operation on it throws
// Error(RC_ERR_NULL). set/get translate error codes with check().
class Arm {
 public:
  explicit Arm(int dof) { throw std::logic_error("NotImplemented"); }
  Arm(Arm&&) noexcept = default;
  Arm& operator=(Arm&&) noexcept = default;
  void set(int index, double angle) { throw std::logic_error("NotImplemented"); }
  double get(int index) const { throw std::logic_error("NotImplemented"); }
  int dof() const { throw std::logic_error("NotImplemented"); }

 private:
  std::unique_ptr<rc_arm, void (*)(rc_arm*)> h_{nullptr, &rc_arm_destroy};
};
```

### Kiểm thử

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#include <cstring>
#include <iostream>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)
template <class E, class F> bool throws(F f) { try { f(); } catch (const E&) { return true; } return false; }
template <class F> int code_of(F f) { try { f(); } catch (const Error& e) { return e.code(); } return RC_OK; }

int main() {
  static_assert(!std::is_copy_constructible_v<Arm>, "Arm must be move-only");
  static_assert(std::is_nothrow_move_constructible_v<Arm>, "moves must be noexcept");
  CHECK(rc_live_arms() == 0);
  // 1. the C API directly: codes, not exceptions
  rc_arm* raw = rc_arm_create(2);
  CHECK(raw != nullptr && rc_arm_dof(raw) == 2 && rc_live_arms() == 1);
  CHECK(rc_arm_set_joint(raw, 1, 0.25) == RC_OK);
  double out = -1.0;
  CHECK(rc_arm_get_joint(raw, 1, &out) == RC_OK && out == 0.25);
  CHECK(rc_arm_get_joint(raw, 0, &out) == RC_OK && out == 0.0);
  CHECK(rc_arm_set_joint(raw, 2, 0.0) == RC_ERR_RANGE && rc_arm_set_joint(raw, -1, 0.0) == RC_ERR_RANGE);
  CHECK(rc_arm_set_joint(raw, 0, NAN) == RC_ERR_VALUE && rc_arm_set_joint(raw, 0, INFINITY) == RC_ERR_VALUE);
  CHECK(rc_arm_get_joint(raw, 0, &out) == RC_OK && out == 0.0);  // rejected writes changed nothing
  CHECK(rc_arm_get_joint(raw, 0, nullptr) == RC_ERR_NULL);
  CHECK(rc_arm_set_joint(nullptr, 0, 1.0) == RC_ERR_NULL && rc_arm_dof(nullptr) == RC_ERR_NULL);
  rc_arm_destroy(raw);
  rc_arm_destroy(nullptr);  // allowed
  CHECK(rc_live_arms() == 0);
  CHECK(rc_arm_create(0) == nullptr && rc_arm_create(33) == nullptr && rc_arm_create(-5) == nullptr);
  CHECK(rc_live_arms() == 0);
  // 2. error strings
  CHECK(std::strcmp(rc_strerror(RC_OK), "ok") == 0);
  CHECK(std::strcmp(rc_strerror(RC_ERR_RANGE), "joint index out of range") == 0);
  CHECK(std::strcmp(rc_strerror(-99), "unknown error") == 0);
  // 3. the C++ wrapper: RAII, exceptions, moves
  {
    Arm a(3);
    CHECK(a.dof() == 3 && rc_live_arms() == 1);
    a.set(2, 1.5);
    CHECK(a.get(2) == 1.5 && a.get(0) == 0.0);
    CHECK(code_of([&] { a.set(3, 0.0); }) == RC_ERR_RANGE);
    CHECK(code_of([&] { a.set(0, NAN); }) == RC_ERR_VALUE);
    try { a.get(9); } catch (const Error& e) { CHECK(std::strcmp(e.what(), "joint index out of range") == 0); }
    Arm b = std::move(a);                                   // ownership moves, no new arm is created
    CHECK(rc_live_arms() == 1 && b.get(2) == 1.5);
    CHECK(code_of([&] { a.get(0); }) == RC_ERR_NULL);       // moved-from is empty
    CHECK(code_of([&] { a.dof(); }) == RC_ERR_NULL);
    Arm c(1);
    CHECK(rc_live_arms() == 2);
    c = std::move(b);                                       // c's old arm must be destroyed
    CHECK(rc_live_arms() == 1 && c.dof() == 3);
  }
  CHECK(rc_live_arms() == 0);                               // everything released at scope exit
  CHECK(throws<std::invalid_argument>([] { Arm bad(0); }));
  CHECK(rc_live_arms() == 0);
  // 4. exception safety: an exception thrown mid-scope still destroys the arm
  try { Arm t(2); t.set(5, 0.0); } catch (const Error&) {}
  CHECK(rc_live_arms() == 0);
  std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi

```
all tests passed
```

Với các stub, lời gọi đầu tiên kết thúc với `NotImplemented`. Với bước shared library, `nm -D libarm.so` nên liệt kê `rc_arm_create`, `rc_arm_destroy`, `rc_arm_set_joint`, `rc_arm_get_joint`, `rc_arm_dof`, `rc_strerror` và `rc_live_arms` đúng như đã viết, không có tiền tố `_Z`.

### Thử thách mở rộng

Thêm `rc_version()` và một field `size` vào một struct tùy chọn public để thư viện có thể phát hiện phiên bản struct nào mà bên gọi đã biên dịch; hoặc gọi shared library từ Python bằng `ctypes` và viết một context manager Python có cùng ngữ nghĩa sở hữu như `Arm`.

### Thực hành với thư viện

`ctypes` trong standard library của Python là người tiêu dùng thực tế của một ABI C, và là bài kiểm tra tốt nhất rằng ranh giới của bạn sạch. Đặt các khai báo interface và phần cài đặt (mọi thứ phía trên comment "C++ wrapper", cùng các include của nó, không có `main`) vào `arm.cpp`, build shared library, và gọi nó từ Python:

```
g++ -std=c++17 -Wall -Wextra -shared -fPIC arm.cpp -o libarm.so
nm -D libarm.so | grep ' T '        # seven unmangled rc_* symbols, no _Z prefixes
python3 lib_arm.py                   # the script below
```

```python
import ctypes, math

lib = ctypes.CDLL("./libarm.so")                      # the C ABI: plain symbol names, no mangling
lib.rc_arm_create.restype = ctypes.c_void_p           # opaque handle = an address; we never look inside
lib.rc_arm_create.argtypes = [ctypes.c_int]
lib.rc_arm_destroy.argtypes = [ctypes.c_void_p]
lib.rc_arm_set_joint.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
lib.rc_arm_get_joint.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
lib.rc_arm_dof.argtypes = [ctypes.c_void_p]
lib.rc_strerror.restype = ctypes.c_char_p             # static storage: ctypes copies it, we never free it
lib.rc_strerror.argtypes = [ctypes.c_int]
RC_OK, RC_ERR_NULL, RC_ERR_RANGE, RC_ERR_VALUE = 0, -1, -2, -3


class Arm:
    """The Python twin of the C++ wrapper: RAII through a context manager."""
    def __init__(self, dof):
        self.h = lib.rc_arm_create(dof)
        if not self.h:
            raise ValueError("rc_arm_create failed (dof must be in 1..32)")
    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
    def close(self):
        if self.h:
            lib.rc_arm_destroy(self.h)
            self.h = None
    def set(self, i, angle):
        code = lib.rc_arm_set_joint(self.h, i, angle)
        if code != RC_OK:
            raise RuntimeError(lib.rc_strerror(code).decode())
    def get(self, i):
        out = ctypes.c_double()
        code = lib.rc_arm_get_joint(self.h, i, ctypes.byref(out))
        if code != RC_OK:
            raise RuntimeError(lib.rc_strerror(code).decode())
        return out.value

assert lib.rc_live_arms() == 0
with Arm(3) as a:
    a.set(1, 0.5)
    assert a.get(1) == 0.5 and lib.rc_arm_dof(a.h) == 3 and lib.rc_live_arms() == 1
    for bad, msg in ((lambda: a.set(3, 1.0), "joint index out of range"), (lambda: a.set(0, math.nan), "angle is not finite")):
        try:
            bad(); raise AssertionError("should have failed")
        except RuntimeError as e:
            assert str(e) == msg
assert lib.rc_live_arms() == 0                        # released on scope exit, the same invariant as the C++ tests
assert lib.rc_arm_create(0) is None and lib.rc_arm_create(33) is None
lib.rc_arm_destroy(None)                              # NULL is accepted: no-op
print("library track ok")
```

Kỳ vọng: `library track ok`. Script cho thấy wrapper C++ `Arm` làm gì trong một ngôn ngữ khác: handle là một địa chỉ mờ (opaque), mã lỗi trở thành exception, và `rc_live_arms()` chứng minh arm được giải phóng khi khối `with` kết thúc. Thử gọi một hàm kiểu `cxx_` (một hàm C++ bị mangle) qua `ctypes` bằng tên thường: nó thất bại với `AttributeError`. Nếu bạn biên dịch một hàm ném exception được xuất dưới dạng `extern "C"` và gọi nó từ đây, process sẽ abort, như trong phần lý thuyết.

## Kiểm chứng

- `nm -D` trên mọi bản release: danh sách symbol được xuất chính là ABI. So sánh nó giữa các phiên bản (các công cụ như `abidiff` của libabigail tự động hóa việc so sánh kiểu và symbol).
- Viết một test build ứng dụng với header phiên bản N và chạy nó với binary thư viện phiên bản N+1.
- Đếm tài nguyên sống bằng một hook kiểm thử (ở đây `rc_live_arms`) và assert nó bằng 0 ở cuối mỗi test và sau các exception được throw.
- Chạy dưới ASan/UBSan và, với thread, TSan (CPP08, CPP10); thử API C từ ngôn ngữ thứ hai (Python `ctypes`) để chứng minh nó thực sự là C.
- Checklist rà soát cho mỗi hàm: chủ sở hữu, vòng đời, thread, đường báo lỗi, khả năng null; người rà soát phải trả lời được mà không cần đọc phần cài đặt.
- Kiểm tra `sizeof` và `offsetof` của các struct public bằng `static_assert` để thay đổi bố cục làm hỏng build.

## Lỗi thường gặp

| Sai lầm | Hậu quả |
|---|---|
| Exception thoát khỏi một hàm `extern "C"` | `terminate` hoặc undefined behavior ở phía gọi (được minh họa bằng `ctypes`) |
| Trả về `s.c_str()` của một `std::string` cục bộ | con trỏ treo; văn bản rác hoặc crash |
| Chèn một field vào giữa struct public | binary cũ đọc sai field (`y=9` thay vì `y=2`), có thể hỏng bộ nhớ |
| `std::string` trong chữ ký của `.so` dựng sẵn với cờ ABI libstdc++ khác | lỗi link `undefined reference to f(std::__cxx11::basic_string...)` |
| Cấp phát trong thư viện và `delete` ở phía gọi | hỏng heap khi allocator khác nhau |
| Thêm một hàm ảo vào class public | bố cục vtable đổi; subclass cũ crash |
| Callback với dữ liệu người dùng `void*` sống lâu hơn đối tượng của nó | use after free trên thread của driver |
| Định nghĩa destructor của class pimpl inline trong header | lỗi `incomplete type` |
| Copy nông một handle kiểu `cv::Mat` được cho là copy sâu | hai chủ sửa một buffer; data race hoặc hỏng dữ liệu |
| Chuỗi `cam_error()` toàn cục với nhiều thread | race; sai thông báo cho sai thread |

## Phương án khác và đánh đổi

- **API C + wrapper C++ so với API C++.** Ranh giới C sống sót qua thay đổi compiler, dùng được từ Python/Rust và có thể đánh phiên bản, nhưng dài dòng và mất an toàn kiểu cho đến khi được bọc. Một API C++ thuần đẹp hơn nhưng buộc mọi người dùng vào một toolchain; chấp nhận được khi mọi thứ được build cùng nhau (ví dụ trong một workspace ROS 2).
- **Pimpl so với opaque handle C.** Pimpl giữ cú pháp class C++ và cho phép exception phía sau, nhưng vẫn có ABI C++ (tên bị mangle, kiểu chuẩn); handle C nghiêm ngặt hơn và di động.
- **Chỉ header so với đã biên dịch.** Chỉ header dễ phân phối và generic nhưng kéo dài thời gian biên dịch và không có hợp đồng ABI; thư viện đã biên dịch cho build nhanh hơn và che giấu phần bên trong nhưng đòi hỏi kỷ luật ABI và một hệ thống build.
- **Interface ảo so với bảng con trỏ hàm.** Class trừu tượng là idiom nhưng mong manh qua các binary; một struct các con trỏ hàm (như trong API plugin C) có bố cục cố định có thể mở rộng bằng cách thêm vào cuối.
- **Exception so với mã lỗi so với `std::expected`.** Exception cho code sạch trong một binary; mã lỗi đi qua ranh giới ngôn ngữ; `std::expected` (C++23, hoặc `tl::expected`) cho lỗi tường minh không có exception trong code real-time cứng.
- **Đánh phiên bản ngữ nghĩa (semantic versioning).** Mã hóa hợp đồng: bản patch giữ ABI; bản minor chỉ thêm; bản major có thể phá vỡ và đổi SONAME (`libfoo.so.2`).

## Vận dụng và ghi nhớ

Đây là cùng một vấn đề trong mọi hệ sinh thái: module mở rộng Python và `ctypes` cần một ABI C; message ROS 2 được định nghĩa bằng IDL chính là để bố cục được sinh ra chứ không viết tay; Rust FFI và các crate `cxx` thực thi một ranh giới tường minh; các bản phân phối Linux theo dõi SONAME của mọi thư viện. Để ghi nhớ: sau một tuần, viết từ trí nhớ mẫu hai tầng (opaque handle, create/destroy, mã lỗi, wrapper với `unique_ptr` và deleter) và liệt kê sáu loại thay đổi phá vỡ ABI; rà soát một dependency trong dự án của bạn bằng bảng kiểm toán.

## Đáp án bài tập

1. `c_add` có thể gọi bằng tên thường từ `ctypes`: nó có liên kết C, nên symbol của nó chỉ là `c_add`. Các hàm khác bị compiler C++ mangle: `_Z7cxx_addii` mã hóa `_Z` (một symbol C++), `7cxx_add` (một tên 7 ký tự), và `ii` (hai tham số `int`); `_ZN5robot8cxx_add2Eii` thêm namespace `robot`; hàm vector mã hóa các đối số template và allocator. Tên bị mangle phụ thuộc compiler, và một kiểu chuẩn như `std::vector` trong chữ ký cũng làm bố cục thành một phần của ABI.
2. (a) Chỉ phá vỡ ABI (`sizeof` đổi, mã nguồn vẫn biên dịch). (b) không cái nào (tương thích cả hai chiều). (c) Chỉ phá vỡ ABI (bố cục vtable) và mã nguồn của subclass vẫn biên dịch. (d) Tương thích API nhưng giá trị mặc định được nướng vào phía gọi lúc biên dịch, nên binary cũ giữ giá trị mặc định cũ: một sự không khớp hành vi lặng lẽ (coi như liên quan ABI). (e) không cái nào. (f) cả hai: mã nguồn thường vẫn biên dịch (chuyển đổi ngầm) nhưng symbol/chữ ký đổi (`long` so với `int` là một tên mangle khác và độ rộng calling convention khác), nên binary cũ lỗi link hoặc truyền dữ liệu sai độ rộng.
3. `Frame* grab();` nói rằng một con trỏ được trả về; không nói: chủ sở hữu, vòng đời, ý nghĩa của null. `void put(Frame*);` nói một con trỏ đi vào; không nói: bên được gọi có nhận sở hữu không, nó có thể null không, nó có được lưu không? `const char* name() const;` văn bản chỉ đọc; không nói: hợp lệ đến khi nào (vòng đời đối tượng, lời gọi tiếp theo?). `void set_cb(Callback, void*);` không nói: thread của lời gọi, vòng đời dữ liệu người dùng, liệu nó có được gọi sau khi hủy đăng ký không. `std::unique_ptr<Map> load(const std::string&);` nói: bên gọi nhận sở hữu độc quyền; đối số được mượn trong lúc gọi; nó vẫn có thể throw hoặc trả null trừ khi được ghi tài liệu.
4. Bug 1: một exception thoát khỏi hàm `extern "C"` (UB hoặc terminate khi bên gọi là C); sửa bằng cách bắt và trả về một giá trị lỗi (ví dụ `nullptr` hoặc một status). Bug 2: `s.c_str()` trỏ vào một string cục bộ bị hủy lúc return: treo. Cách sửa: trả về con trỏ tới vùng lưu trữ tĩnh (một buffer `static thread_local std::string`, ghi tài liệu "hợp lệ đến lời gọi tiếp theo trên thread này") hoặc ghi vào một buffer do bên gọi cung cấp `int describe(int code, char* buf, size_t n)`.
5. Output `7 7 1`: `b = a` copy handle nhưng chia sẻ buffer, nên `fill(7)` đổi cả `a` và `b`; `clone()` copy dữ liệu, nên `c` vẫn là 1. Bug robotics: một callback lưu `msg_image` (một bản copy nông) trong khi driver tái sử dụng buffer cho frame tiếp theo sẽ lặng lẽ thấy dữ liệu đổi (hoặc race với thread khác); cách sửa là `clone()` hoặc lưu một message chia sẻ bất biến (`shared_ptr<const Msg>`).
6. Trong header khai báo `~Planner();` và các phép move (`Planner(Planner&&) noexcept; Planner& operator=(Planner&&) noexcept;`), và định nghĩa chúng trong `.cpp` nơi `struct Planner::Impl { ... };` đã đầy đủ (`Planner::~Planner() = default;`). Nếu không, destructor inline ngầm định khởi tạo `std::default_delete<Impl>` ở nơi `Impl` chưa đầy đủ, gây ra "invalid application of 'sizeof' to incomplete type".
7. Header của ứng dụng nói `y` ở offset 8, nhưng phiên bản 2 đặt `z` ở offset 8 và `y` ở offset 16; thư viện ghi `z=9` tại offset 8, mà ứng dụng đọc như `y`, và thư viện cũng ghi 8 byte vượt quá struct 16 byte của ứng dụng (undefined behavior, một tràn stack trong ứng dụng). Tên symbol không đổi, nên linker không phàn nàn. Cách phát triển an toàn: thêm field mới ở cuối một struct mang field `size` (hoặc phiên bản) của riêng nó làm member đầu tiên và để thư viện chỉ điền các field mà size của bên gọi bao phủ; ẩn struct sau một opaque handle với các hàm accessor (`pose_get_y`); thêm một hàm và một struct mới (`get_pose_v2`) và giữ hàm cũ.
8. Lúc link bạn nhận `undefined reference to f(std::string const&)` vì với ABI mặc định (mới) kiểu của tham số là `std::__cxx11::basic_string<...>` và mangle khác với `std::basic_string<...>` cũ; symbol trong `.so` không khớp. Chiến lược: một interface C (`const char*` và độ dài); phát hành bản build cho cả hai giá trị của `_GLIBCXX_USE_CXX11_ABI` (và ghim một phiên bản compiler); phát hành thư viện dưới dạng mã nguồn hoặc static library build với toolchain của người dùng; hoặc cung cấp một wrapper chỉ có header chuyển sang interface C.
9. Rủi ro: `Gripper(const std::string&)` đặt `std::string` vào ABI; `poll()` trả một con trỏ thô tới trạng thái nội bộ (ai sở hữu, vòng đời, an toàn thread? nó có bị lần poll tiếp theo ghi đè không?); `std::function` trong `on_contact` (ABI và thread nào gọi nó; exception qua lời gọi; vòng đời của các capture); `virtual close` trong một class được xuất (vtable và tương thích subclass; cũng thiếu virtual destructor); data member public `std::vector<double> history` (bố cục và an toàn thread, ai cũng sửa được); `GripperState` là struct public không thể lớn thêm; không có báo lỗi cho `close` và constructor (exception hay mã?). Thiết kế lại: opaque handle `grip*` với `grip_open/close`, `grip_poll(grip*, GripperState* out, uint32_t size)` copy vào bộ nhớ của bên gọi, `grip_set_contact_callback(grip*, void(*)(const GripperState*, void*), void*)` với thread được ghi tài liệu và catch-all, các hàm trả mã, cộng một wrapper C++ với RAII.
10. (i) Chỉ header: không có vấn đề ABI, kiểu nào cũng được (`long double`), nhưng mọi translation unit biên dịch lại code (build lâu hơn, binary lớn hơn). (ii) Đã biên dịch với explicit instantiation (`extern template class Filter<float>; extern template class Filter<double>;`): build nhanh hơn, object nhỏ hơn; bố cục của `Filter<float>` và `Filter<double>` trở thành ABI, và `long double` cần một instantiation mới (một thay đổi của thư viện). (iii) Một API C với các bộ hàm `filter_f32_*` và `filter_f64_*`: ổn định nhất, dùng được từ các ngôn ngữ khác, dài dòng, và mỗi kiểu mới cần hàm mới. Chọn (i) cho thư viện header generic dùng trong một build; (ii) cho thư viện có một nhúm kiểu được hỗ trợ; (iii) khi thư viện được giao dưới dạng binary cho các toolchain không biết trước.
11. Một câu trả lời tốt gồm: một bảng với ít nhất sáu hàm; với mỗi hàm: chủ sở hữu, vòng đời, ngữ cảnh thread/callback, cơ chế báo lỗi và rủi ro ABI; ít nhất một rủi ro được chứng minh bằng một chương trình ngắn (ví dụ copy nông, view treo, hoặc vòng đời callback) và cách sửa (clone, kiểu chủ sở hữu, hoặc hủy đăng ký trong destructor); và một khuyến nghị về cách bọc nó.
12. Dựng tên: `_Z` rồi `N5robot7Planner6replanE` (nested name: namespace `robot`, class `Planner`, hàm `replan`; substitution `S_` = `robot`, `S0_` = `robot::Planner`), rồi các tham số. Tham số `a` là `const std::vector<robot::Pose, std::allocator<robot::Pose>>&`, viết `RKSt6vectorINS_4PoseESaIS2_EE`: `St6vector` là `std::vector` (`S1_`), `NS_4PoseE` là `robot::Pose` (dùng lại `S_`, mục mới `S2_`), `Sa` là viết tắt định sẵn của `std::allocator` (không đánh số), `SaIS2_E` là `allocator<Pose>` (`S3_`), template-id `vector<Pose, allocator<Pose>>` là `S4_`, bản `const` là `S5_`, tham chiếu là `S6_`. Tham số `b`, `robot::Pose*`, là `PS2_` và thành `S7_`. Tham số `c`, `const Planner&`, là `RKS0_` (`S8_` cho kiểu const, `S9_` cho tham chiếu). Tham số `d`, tham chiếu không const tới `vector<Pose>`, là `RS4_`. Kết quả (hai tham số cuối dùng lại `S0_` và `S4_`, và compiler đồng ý): `_ZN5robot7Planner6replanERKSt6vectorINS_4PoseESaIS2_EEPS2_RKS0_RS4_`, đúng như `g++ -c` rồi `nm` in ra. Kiểu trả về không nằm trong tên mangle của hàm không phải template (§5.1.5.3), nên `void` sang `bool` giữ nguyên symbol: binary cũ link được, gọi code mới, và đọc một giá trị rác trong thanh ghi `al` làm kết quả (hoặc bỏ qua kết quả không được tạo ra). Tôi đã kiểm chứng bằng hai translation unit: `void f(P*)` và `bool f(P*)` cùng cho `_Z1fP1P`, còn các bản template cho `_Z1hIiEvT_` và `_Z1kIiEbT_`.
13. (a) `a` ở offset 0 (4 byte), `b` ở 4, nên `dsize(A)=5`, `sizeof(A)=8` (alignment 4). `A` không phải POD theo bố cục (có destructor do người dùng cung cấp), nên `B::c` được đặt tại offset $\mathrm{dsize}(A)=5$ và `sizeof(B)=8`. (b) Với `PA` là POD, base chiếm đủ `sizeof(PA)=8`, nên `PB::c` ở offset 8 và `sizeof(PB)=12`. Đo được: `A 8 B 8 PA 8 PB 12` và offset của `c` trong `B` bằng 5. (c) `memcpy(static_cast<A*>(&x), &y, sizeof(A))` ghi 8 byte: 5 byte dữ liệu và 3 byte padding, nhưng byte 5 chính là `B::c`. Trong thí nghiệm `c` là `'Z'` (90) trước và `0` sau (padding của nguồn `y` được khởi tạo bằng 0); với trường hợp POD nó vẫn là 90. (d) Ở phiên bản 2, `A` có `d` ở offset 5 nên `dsize(A)=6`, `sizeof(A)=8`, `B::c` dời tới offset 6 và `sizeof(B)=8`. Đo được: `sizeof A=8 B=8 offc=6` so với `offc0=5` trước đó. Cả hai cỡ không đổi mà member đã dời, nên kiểm tra `sizeof` vẫn qua nhưng binary cũ ghi `c` vào offset 5 (nay là `d`). Hãy dùng dump bố cục hoặc `offsetof`/`static_assert` cho mọi member.
14. (a) Cả hai bản build đều mangle thành `_Z6get_idRK6Config` (`nm` hiện cùng symbol trong `lib0.o` và `app1.o`), vì *kiểu* `Config` là kiểu người dùng, và các member của nó không xuất hiện trong tên mangle. Link thành công. (b) Với ABI cũ `std::string` là một con trỏ 8 byte, nên `Config` là 16 byte và `id` ở offset 8; với ABI mới `std::string` là 32 byte (con trỏ, độ dài, buffer 16 byte), nên `Config` là 40 byte và `id` ở offset 32. Ứng dụng lưu 42 tại offset 32, còn thư viện đọc offset 8, nơi bố cục mới chứa *độ dài* chuỗi là 3. Kết quả đo: `sizeof=40 id=3` (khi cả hai phía biên dịch với ABI cũ: `sizeof=16 id=42`). (c) Đưa kiểu vào symbol: giấu string sau một opaque handle hoặc dùng `const char*` cộng độ dài, để không có kiểu libstdc++ nào nằm trong struct; hoặc cho thư viện một versioned namespace hay một type tag (ví dụ `inline namespace v1_abi0 { struct Config ...}` chọn theo `_GLIBCXX_USE_CXX11_ABI`), để hai bản build cho tên mangle khác nhau và sự sai lệch trở thành `undefined reference` lúc link.
15. (a) vtable của `Derived` trong ứng dụng (từ `g++ -fdump-lang-class`): slot 0 là offset-to-top 0, slot 1 là RTTI, rồi các mục hàm: [0] `Derived::~Derived` (complete), [1] `Derived::~Derived` (deleting), [2] `Base::f`, [3] `Derived::g` (override slot 3 của phiên bản 1), [4] `Derived::extra`. (b) `call_g` của phiên bản 2 được biên dịch từ header mới dùng function slot 4 (`~D1`, `~D0`, `f`, `h`, `g`) và `call_h` dùng slot 3. Vậy `call_g(&d)` chạy `Derived::extra` và trả về 99, còn `call_h(&d)` chạy `Derived::g` và trả về 30. Đo được: `g=99 h=30`; không có gì lỗi lúc link. (c) Giữ cố định interface virtual công khai: thêm hành vi mới dưới dạng non-virtual method chuyển tiếp tới một implementation ẩn, dưới dạng một interface class mới (`Base2`) mà client tự chọn dùng, hoặc một hàm C mới; nếu buộc thêm virtual thì chỉ thêm ở cuối khi không client class nào dẫn xuất từ kiểu đó, còn không thì tăng SONAME. Thiết kế mạnh nhất là không export class đa hình qua ranh giới: expose một handle và một bảng callback có trường `size`.

## Đọc thêm

- [C++ Core Guidelines: Interfaces](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) - các quy tắc I.1-I.27 về interface tường minh, có kiểu, ổn định; I.11 (quyền sở hữu) và I.26-I.27 (ABI) là trung tâm ở đây.
- [KDE: Binary Compatibility Issues With C++](https://community.kde.org/Policies/Binary_Compatibility_Issues_With_C%2B%2B) - danh sách thực tế các thay đổi tương thích mã nguồn, tương thích nhị phân và phá vỡ.
- [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html) - đặc tả về name mangling, bố cục đối tượng và vtable do GCC và Clang dùng trên Linux.
- [libstdc++ manual: Dual ABI](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html) - `_GLIBCXX_USE_CXX11_ABI` và namespace `std::__cxx11` thay đổi symbol như thế nào (bài tập 14).

**Thực hành thêm:** [hướng dẫn tương thích nhị phân của KDE](https://community.kde.org/Policies/Binary_Compatibility_Issues_With_C%2B%2B) (một danh sách nên và không nên để phân loại, như bài tập 2), sách hướng dẫn libstdc++ về [dual ABI](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html) (tái hiện bài tập 8 với `-D_GLIBCXX_USE_CXX11_ABI=0`), [tài liệu `ctypes`](https://docs.python.org/3/library/ctypes.html) (gọi `libarm.so` của bạn), cppreference về [language linkage](https://en.cppreference.com/w/cpp/language/language_linkage) và [pimpl idiom](https://en.cppreference.com/w/cpp/language/pimpl), và [phần interface (I)](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#i-interfaces) của Core Guidelines cho bản kiểm toán của bài tập 11.
