---
{"title": "STL container, iterator và algorithm", "summary": "Chọn container từ mẫu truy cập dữ liệu, dùng đúng iterator range và các thuật toán chuẩn, rồi đo để thấy sự đánh đổi.", "objectives": ["Chọn giữa vector, deque, list, map, unordered_map và set dựa trên các thao tác mà chương trình thực hiện.", "Mô tả các iterator category, khoảng nửa mở (half-open range) và sự vô hiệu hóa iterator (iterator invalidation).", "Dùng đúng lower_bound, accumulate, remove_if/erase và nth_element.", "Thiết kế một micro-benchmark công bằng và diễn giải kết quả."]}
---
## Vì sao điều này quan trọng

Phần lớn code robot dành thời gian di chuyển các chuỗi số: scan, quỹ đạo, các giá trị cảm biến có timestamp, các detection. Standard library cung cấp container và thuật toán đã được kiểm thử cho những việc này, và chọn khôn ngoan thay đổi chi phí theo nhiều bậc độ lớn. Tìm mẫu gần nhất theo timestamp bằng cách quét 360,000 mẫu của một giờ dữ liệu 100 Hz tốn 360,000 phép so sánh; bằng binary search chỉ tốn 19. Chọn sai container cũng là nguồn bug: erase trong vòng lặp làm vô hiệu hóa iterator, và `map::operator[]` lặng lẽ chèn một key còn thiếu. Bài này dạy mô hình đằng sau STL (container giữ phần tử, iterator trỏ vào chúng, thuật toán làm việc trên các iterator range) để bạn có thể chọn, kết hợp và kiểm thử chúng một cách tự tin.

## Trực giác

Hãy nghĩ đến ba tầng. **Container** sở hữu các phần tử và quyết định bố cục của chúng: `vector` là một khối liên tục, `list` là các node cấp phát riêng lẻ, `map` là một cây cân bằng. **Iterator** là con trỏ tổng quát hóa: chúng nói "ở đây" và "tiếp theo". **Thuật toán** (`sort`, `find`, `lower_bound`, `accumulate`) được viết một lần dựa trên iterator, nên chúng chạy trên mọi container cung cấp đúng iterator category. Một thuật toán không bao giờ thay đổi *kích thước* của container, vì nó chỉ thấy iterator; muốn thu nhỏ phải gọi `erase` của container.

Các range là **nửa mở**: `[first, last)` chứa `first` nhưng không chứa `last`. Một range rỗng có `first == last`. Quy ước này là lý do `v.end()` hợp lệ để so sánh nhưng không bao giờ để dereference, và là lý do `lower_bound` có thể trả về `end()` với nghĩa "không tìm thấy".

Một hình ảnh đời thường sẽ giúp ích. Một `vector` đã sắp xếp giống một hành lang có các tủ khóa đánh số: muốn đến tủ 5000 chỉ cần đi thẳng tới đó, và binary search là trò chơi "cao hơn hay thấp hơn" chơi trên các con số ghi ở cửa tủ. Một `list` là trò săn kho báu trong đó mỗi mảnh giấy cho biết mảnh tiếp theo giấu ở đâu, nên mảnh thứ 5000 tốn 4999 bước và không có gì được lưu theo thứ tự. Một `map` là cây các biển chỉ đường ("key nhỏ hơn đi sang trái, lớn hơn đi sang phải"), còn `unordered_map` là một bức tường hộp thư mà hàm băm biến key thành số hộp thư.

Một ví dụ robot: driver lidar thêm một pose mỗi 100 ms, và bộ điều khiển cần pose đúng tại thời điểm $t=12.34$ s, nằm giữa hai pose đã lưu. Container giữ các pose theo thứ tự thời gian và tìm nhanh hai lân cận là lựa chọn đúng; container tìm một key chính xác nhanh nhất (bảng băm) hoàn toàn không trả lời được câu hỏi này.

*Dự đoán trước khi đọc tiếp.* Một log chứa 1,000,000 timestamp đã sắp xếp. Trong trường hợp xấu nhất phải xem bao nhiêu timestamp để tìm vị trí của một thời điểm cho trước, và cây với vector có xem cùng một số lượng không? Các hình và phần lý thuyết bên dưới sẽ trả lời cả hai câu hỏi.

Trực giác sai phổ biến là bảng độ phức tạp quyết định tất cả: "cả hai đều là $O(\log n)$ nên nhanh như nhau". Bảng đếm số bước, không đếm chi phí của một bước. Một bước trong vector đã sắp xếp đọc vùng nhớ nằm cạnh lần đọc trước; một bước trong cây theo một con trỏ tới node được cấp phát ở nơi khác, và khi dữ liệu không còn vừa trong cache thì mỗi bước nhảy có thể phải chờ bộ nhớ chính. Các phép đo gần cuối bài cho thấy chênh lệch khoảng 4 lần giữa hai bên dù số bước logarit như nhau. Trực giác sai thứ hai là `remove` thì xóa: nó chỉ dịch chuyển phần tử, và container vẫn giữ kích thước cũ cho đến khi gọi `erase`.

![Năm container vẽ dưới dạng bộ nhớ: các ô của vector có dung lượng dự trữ, các khối deque sau một chỉ mục, node của list, cây đỏ-đen và các bucket băm có chuỗi](/lesson-figures/CPP05.svg)

*Hình: các phần tử nằm ở đâu. Chỉ vector giữ các phần tử cạnh nhau, vì vậy một lần tìm kiếm chạm vào ít cache line; các container còn lại tới phần tử qua con trỏ. Cây là một cách tô màu đỏ-đen hợp lệ (mọi đường từ gốc tới một con trống đi qua hai node đen); các bucket dùng $\text{key}\bmod 5$, như libstdc++ làm với key kiểu `int`. Bố cục theo mô tả container trong cppreference (Containers library).*

## Lý thuyết và suy dẫn

### Chọn container

| Container | Bố cục | Truy cập chỉ số / tìm | Chèn / xóa | Ghi chú |
|---|---|---|---|---|
| `vector<T>` | liên tục | chỉ số $O(1)$; tìm $O(n)$, $O(\log n)$ nếu đã sắp xếp | cuối: amortized $O(1)$; giữa: $O(n)$ | lựa chọn mặc định; thân thiện với cache |
| `deque<T>` | các khối | chỉ số $O(1)$ | cả hai đầu $O(1)$ | hàng đợi FIFO, cửa sổ trượt |
| `list<T>` | các node | $O(n)$ | $O(1)$ tại một iterator đã biết | hiếm khi đáng dùng; locality kém |
| `map<K,V>` | cây cân bằng | $O(\log n)$ | $O(\log n)$ | sắp theo key, iterator ổn định |
| `unordered_map<K,V>` | bảng băm | kỳ vọng $O(1)$ | kỳ vọng $O(1)$ | không có thứ tự, không có truy vấn khoảng |
| `set<K>` | cây | $O(\log n)$ | $O(\log n)$ | key duy nhất và có thứ tự |

Hãy chọn từ các *thao tác*: bạn tra cứu theo key chính xác, theo key gần nhất, hay theo khoảng? Chỉ chèn ở cuối, hay ở giữa? Có cần thứ tự không? Một hash map không thể trả lời "mẫu ngay trước thời điểm $t$"; một vector đã sắp xếp hoặc một `map` thì có thể.

**Ví dụ.** Một robot giữ 4 số đo khoảng cách mới nhất (đơn vị m) và một bảng từ id khung hình đến nhãn. Cửa sổ là một `std::deque`: `push_back` và `pop_front` có thời gian hằng số (cppreference, `std::deque`, Complexity). Câu hỏi "khung đã lưu đầu tiên có id từ 140 trở lên là khung nào?" là `std::map::lower_bound`, logarit theo kích thước (cppreference, `std::map::lower_bound`), và một hash map không trả lời được. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <deque>
#include <iostream>
#include <map>

int main() {
  std::deque<double> window;                       // latest 4 range readings (m)
  for (double r : {2.4, 2.5, 2.7, 2.6, 2.8, 3.1}) {
    window.push_back(r);
    if (window.size() > 4) window.pop_front();
  }
  for (std::size_t i = 0; i < window.size(); ++i) std::cout << (i ? " " : "") << window[i];
  std::cout << '\n';

  std::map<int, const char*> frames{{100, "a"}, {130, "b"}, {160, "c"}};
  auto it = frames.lower_bound(140);               // first key not less than 140
  std::cout << it->first << ' ' << it->second << '\n';
}
```

```text
2.7 2.6 2.8 3.1
160 c
```

### Iterator và sự vô hiệu hóa

Các category, từ yếu nhất đến mạnh nhất: input, forward, bidirectional, random access (và contiguous). `std::sort` cần random access, nên nó không sắp xếp được một `std::list` (hãy dùng `list::sort`). `std::lower_bound` chạy được trên forward iterator nhưng chỉ có $O(\log n)$ phép so sánh *và* số bước với random-access iterator.

**Quy tắc vô hiệu hóa** (nguồn gốc phổ biến nhất của undefined behavior): `vector::push_back` có thể cấp phát lại, vô hiệu hóa mọi iterator, con trỏ và reference; `vector::erase(it)` vô hiệu hóa `it` và mọi thứ sau nó; erase của `map`/`list` chỉ vô hiệu hóa phần tử bị xóa; rehash của `unordered_map` vô hiệu hóa iterator nhưng không vô hiệu hóa reference.

**Ví dụ.** Vector `{10, 20, 30}` có size 3 và capacity 3, nên lần `push_back` kế tiếp cấp phát một khối mới và giải phóng khối cũ: khi size mới vượt capacity cũ thì xảy ra cấp phát lại, và khi đó mọi iterator cùng mọi reference tới phần tử đều bị vô hiệu hóa (cppreference, `std::vector::push_back`). Iterator lấy trước đó bị treo. Biên dịch bằng `g++ -std=c++20 -g -fsanitize=address,undefined` (g++ 11.4.0), báo cáo bắt đầu như sau (địa chỉ và phần còn lại của báo cáo được lược bỏ):

```cpp
#include <iostream>
#include <vector>

int main() {
  std::vector<int> v{10, 20, 30};   // size 3, capacity 3
  auto it = v.begin();
  v.push_back(40);                  // full: reallocates, `it` now dangles
  std::cout << *it << '\n';
}
```

```text
ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010 at pc ...
READ of size 4 at 0x502000000010 thread T0
    #0 ... in main e2.cpp:8
freed by thread T0 here:
    ... in std::vector<int, std::allocator<int> >::_M_realloc_insert<int>(...)
    ... in main e2.cpp:7
```

### Binary search

Với một range đã sắp xếp, `lower_bound(first, last, x)` trả về phần tử đầu tiên không nhỏ hơn $x$; `upper_bound` trả về phần tử đầu tiên lớn hơn $x$. Sau $k$ lần giảm nửa, cửa sổ còn $\lceil n/2^k\rceil$ phần tử, nên số phép so sánh tối đa là $\lceil\log_2(n+1)\rceil$. Với $n=360{,}000$ là 19; với $n=10^6$ là 20. Điều kiện tiên quyết là range được sắp xếp theo cùng thứ tự mà comparator dùng; nếu không, kết quả vô nghĩa.

Nội suy tuyến tính giữa các lân cận $(t_a,v_a)$ và $(t_b,v_b)$ với $t_a\le t\le t_b$:
$$v(t)=v_a+(v_b-v_a)\frac{t-t_a}{t_b-t_a}.$$

**Ví dụ.** Trên vector đã sắp xếp $\{1,2,2,2,5,8\}$, `lower_bound(2)` là phần tử đầu tiên không nhỏ hơn 2 (chỉ số 1) và `upper_bound(2)` là phần tử đầu tiên lớn hơn 2 (chỉ số 4), nên ba bản sao của số 2 nằm trong $[1,4)$ và số lượng là hiệu của hai iterator. Một giá trị không có mặt cho ra điểm chèn, còn giá trị lớn hơn mọi phần tử cho ra `end()`. Mỗi lời gọi tốn số phép so sánh logarit (cppreference, `std::lower_bound`, Complexity). Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
  std::vector<int> v{1, 2, 2, 2, 5, 8};
  auto lo = std::lower_bound(v.begin(), v.end(), 2);
  auto hi = std::upper_bound(v.begin(), v.end(), 2);
  std::cout << (lo - v.begin()) << ' ' << (hi - v.begin()) << ' ' << (hi - lo) << '\n';
  std::cout << (std::lower_bound(v.begin(), v.end(), 3) - v.begin()) << ' '
            << (std::lower_bound(v.begin(), v.end(), 9) == v.end()) << '\n';
}
```

```text
1 4 3
4 1
```

### Erase-remove và các thuật toán thông dụng

`std::remove_if(first, last, pred)` dồn các phần tử được giữ lên đầu và trả về điểm cuối logic mới; phần đuôi chứa các giá trị không xác định. Theo sau nó bằng `container.erase(new_end, container.end())`. `std::accumulate(first, last, init)` gộp bằng `+` (kiểu của `init` quyết định phép tính: `0` tích lũy bằng `int`, `0.0` bằng `double`). `std::nth_element(first, nth, last)` đặt vào vị trí `nth` phần tử sẽ nằm ở đó nếu sắp xếp, trong kỳ vọng $O(n)$, đủ cho trung vị (median) (sắp xếp tốn $O(n\log n)$).

**Ví dụ.** Sáu số đo nhiệt độ (độ C) có hai lần cảm biến nhiễu trên 60. `remove_if` chỉ duyệt một lượt và áp dụng predicate đúng một lần cho mỗi phần tử (cppreference, `std::remove`, Complexity); nó trả về điểm cuối logic mới, nhưng size vẫn là 6 cho đến khi `erase`. Tổng với giá trị đầu là `int` làm cắt cụt mọi tổng riêng; với `0.0` đó là tổng thật của các giá trị được giữ. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <algorithm>
#include <iostream>
#include <numeric>
#include <vector>

int main() {
  std::vector<double> temp{21.5, 22.0, 85.5, 23.5, 90.0, 22.5};
  auto new_end = std::remove_if(temp.begin(), temp.end(), [](double t) { return t > 60.0; });
  std::cout << "logical size " << (new_end - temp.begin()) << ", physical size " << temp.size() << '\n';
  temp.erase(new_end, temp.end());
  std::cout << "after erase " << temp.size() << ", sum with 0: " << std::accumulate(temp.begin(), temp.end(), 0)
            << ", with 0.0: " << std::accumulate(temp.begin(), temp.end(), 0.0) << '\n';
}
```

```text
logical size 4, physical size 6
after erase 4, sum with 0: 88, with 0.0: 89.5
```

### Tăng trưởng amortized

Nếu một vector nhân đôi dung lượng khi đầy, việc push $n$ phần tử copy tối đa $1+2+4+\dots+2^{k}<2n$ phần tử trong các lần cấp phát lại, nên chi phí amortized mỗi `push_back` là $O(1)$. Với hệ số tăng trưởng $g>1$ tổng tối đa là $\frac{g}{g-1}n$.

![Trái: bậc thang dung lượng 1, 2, 4, ..., 128 theo số lần gọi push_back cho 100 lần push với bảy lần cấp phát lại; phải: sơ đồ iterator trỏ vào khối cũ đã được giải phóng sau khi cấp phát lại](/lesson-figures/CPP05-2.svg)

*Hình: bên trái, dung lượng đo được (libstdc++, g++ 11.4.0) sau $n$ lần gọi `push_back`; mỗi bậc đi lên là một lần cấp phát lại và copy đúng số phần tử đang có (1, 2, 4, ..., 64), tổng cộng 127, thấp hơn $2n=200$. Bên phải, vì sao cấp phát lại quan trọng: một iterator lấy từ trước vẫn trỏ vào khối cũ, và khối đó đã được giải phóng.*

```explore
{
  "title": "Growth factor: copying work against wasted memory",
  "title_vi": "Hệ số tăng trưởng: công copy so với bộ nhớ lãng phí",
  "prompt": "Predict first: if the growth factor is lowered towards 1, what happens to the worst-case number of copies per push_back, and what does the vector gain in return? Then move the slider.",
  "prompt_vi": "Dự đoán trước: nếu hạ hệ số tăng trưởng xuống gần 1, số lần copy tối đa cho mỗi push_back thay đổi thế nào, và vector được lợi gì? Sau đó kéo thanh trượt.",
  "params": [
    {
      "name": "g",
      "label": "growth factor g",
      "label_vi": "hệ số tăng trưởng g",
      "min": 1.1,
      "max": 4,
      "step": 0.05,
      "value": 2,
      "unit": ""
    },
    {
      "name": "n",
      "label": "pushes n",
      "label_vi": "số lần push n",
      "min": 100,
      "max": 10000,
      "step": 100,
      "value": 1000,
      "unit": ""
    }
  ],
  "let": [
    {
      "name": "per",
      "expr": "g/(g-1)"
    },
    {
      "name": "waste",
      "expr": "(g-1)/g"
    }
  ],
  "plot": {
    "x": {
      "name": "h",
      "min": 1.1,
      "max": 4,
      "label": "growth factor g",
      "label_vi": "hệ số tăng trưởng g"
    },
    "y": {
      "label": "copies per push (bound), capacity per element",
      "label_vi": "copy mỗi push (cận), dung lượng mỗi phần tử",
      "min": 0,
      "max": 12
    },
    "series": [
      {
        "expr": "h/(h-1)",
        "label": "copies per push, at most g/(g-1)",
        "label_vi": "copy mỗi push, tối đa g/(g-1)",
        "color": "orange"
      },
      {
        "expr": "h",
        "label": "capacity / size, at most g",
        "label_vi": "dung lượng / size, tối đa g",
        "color": "blue"
      }
    ],
    "points": [
      {
        "x": "g",
        "y": "per",
        "label": "copies",
        "label_vi": "copy",
        "color": "orange"
      },
      {
        "x": "g",
        "y": "g",
        "label": "capacity",
        "label_vi": "dung lượng",
        "color": "blue"
      }
    ]
  },
  "readouts": [
    {
      "label": "element copies in reallocations, at most",
      "label_vi": "số phần tử bị copy khi cấp phát lại, tối đa",
      "expr": "per*n",
      "unit": "elements",
      "digits": 0
    },
    {
      "label": "copies per push, at most",
      "label_vi": "copy mỗi push, tối đa",
      "expr": "per",
      "unit": "",
      "digits": 2
    },
    {
      "label": "unused capacity, at most",
      "label_vi": "dung lượng chưa dùng, tối đa",
      "expr": "waste*100",
      "unit": "%",
      "digits": 0
    }
  ]
}
```

**Ví dụ.** 100 lần `push_back` vào một `vector<int>` rỗng làm capacity đổi 8 lần (libstdc++ nhân đôi): 7 lần cấp phát lại sau lần cấp phát đầu relocate $1+2+4+\dots+64=127$ phần tử, thấp hơn cận $\frac{g}{g-1}n=2\cdot100=200$ với $g=2$. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <iostream>
#include <vector>

int main() {
  std::vector<int> v;
  std::vector<std::size_t> caps;
  std::size_t moved = 0;
  for (int i = 0; i < 100; ++i) {
    std::size_t before = v.size(), cap = v.capacity();
    v.push_back(i);
    if (v.capacity() != cap) {            // a (re)allocation happened
      caps.push_back(v.capacity());
      moved += before;                    // `before` elements were relocated (0 on the first)
    }
  }
  for (std::size_t i = 0; i < caps.size(); ++i) std::cout << (i ? " " : "") << caps[i];
  std::cout << "\nreallocations after the first: " << caps.size() - 1 << ", elements relocated: " << moved << '\n';
}
```

```text
1 2 4 8 16 32 64 128
reallocations after the first: 7, elements relocated: 127
```

### Vì sao iterator bị vô hiệu hóa: đọc quy tắc từ cấu trúc dữ liệu

Mỗi quy tắc vô hiệu hóa là hệ quả của việc container làm gì với bộ nhớ của nó, nên bạn có thể suy lại thay vì học thuộc bảng (cppreference: Containers library, "Iterator invalidation"; `std::unordered_map::insert`).

- **`vector`** lưu phần tử trong một khối. Nếu $\text{size}<\text{capacity}$, `push_back` ghi vào chỗ trống: phần tử không di chuyển, chỉ `end()` đổi. Nếu $\text{size}=\text{capacity}$, một khối mới được cấp phát, $n$ phần tử được relocate và khối cũ được giải phóng: *mọi* iterator, pointer và reference đều treo. `insert`/`erase` ở giữa dịch phần đuôi một ô, nên mọi thứ tại hoặc sau vị trí đó bị vô hiệu hóa (quy tắc của bài), còn phần tử trước đó giữ nguyên địa chỉ.
- **`deque`** giữ các khối kích thước cố định cùng một chỉ mục các con trỏ khối. Tăng ở hai đầu có thể cấp phát lại *chỉ mục* (làm mất hiệu lực iterator) nhưng không bao giờ di chuyển phần tử, nên reference và pointer tới phần tử vẫn hợp lệ (đo được với libstdc++ cho `push_back` và `push_front`).
- **`list` và `map`/`set`** cấp phát mỗi phần tử thành một node riêng và chỉ nối lại con trỏ, nên chỉ phần tử bị xóa bị vô hiệu hóa.
- **`unordered_map`** là một mảng các bucket chứa node. Node không bao giờ di chuyển nên reference và pointer vẫn hợp lệ. Nhưng khi một lần chèn làm load factor $\text{size}/\text{bucket\_count}$ vượt `max_load_factor` (mặc định 1.0), bảng được xây lại với nhiều bucket hơn, và các iterator (mã hóa thứ tự duyệt bucket) đều bị vô hiệu hóa: "If rehashing occurs (due to the insertion), all iterators are invalidated. Otherwise iterators are not invalidated."

Đo với libstdc++ (g++ 11.4): chèn các khóa $0,\dots,999$ vào `unordered_map<int,int>` rỗng làm số bucket đi qua $1\to13\to29\to59\to127\to257\to541\to1109$ (7 lần rehash), lần đầu ở lần chèn đầu tiên rồi ở lần chèn thứ 14 và 30 (kích thước ngay trên $13$ và $29$); địa chỉ của `m[0]` không bao giờ đổi, và load factor cuối là $1000/1109\approx0.9017$. Các số bucket này phụ thuộc cài đặt (số nguyên tố trong libstdc++), chỉ có quy tắc là chuẩn. Cùng phép đo cho một `vector<int>` được điền bằng 1000 lần `push_back` cho thấy capacity $1,2,4,\dots,1024$: mười lần cấp phát lại sau lần đầu, relocate $1+2+\dots+512=1023$ phần tử, dưới cận $2n$ của lập luận amortized growth.

**Quy tắc load factor tốn gì.** Nếu các key trải đều trên $m$ bucket (mô hình "simple uniform hashing"), bảng có $n$ key có load factor $\alpha=n/m$ và một bucket chứa trung bình $\alpha$ node, nên một lần tra cứu thất bại duyệt $\alpha$ node còn một lần thành công duyệt khoảng $1+\alpha/2$. Thư viện chỉ hứa tìm kiếm hằng số trung bình (cppreference, `std::unordered_map`), vì một bucket gom nhiều key làm tìm kiếm phải đi qua một chuỗi dài; giữ $\alpha\le$ `max_load_factor` là điều làm cho mức trung bình là hằng số, và đó là lý do của việc rehash. Đo với libstdc++ (g++ 11.4.0, `-O2`, key ngẫu nhiên 64 bit, 1031 bucket): $\alpha=0.95$ cho 1.465 node mỗi lần tra cứu thành công (mô hình 1.475) và $\alpha=3.80$ cho 2.921 (mô hình 2.900). Vì vậy nâng `max_load_factor` đổi ít bucket hơn và ít lần rehash hơn lấy chuỗi dài hơn.

```explore
{
  "title": "Hash table: load factor against nodes visited",
  "title_vi": "Bảng băm: load factor và số node phải duyệt",
  "prompt": "Predict first: if max_load_factor is raised from 1 to 4, how many nodes does a failed lookup walk on average, and what does the table save in return? Then move the slider.",
  "prompt_vi": "Dự đoán trước: nếu nâng max_load_factor từ 1 lên 4, một lần tra cứu thất bại duyệt trung bình bao nhiêu node, và bảng tiết kiệm được gì? Sau đó kéo thanh trượt.",
  "params": [
    {
      "name": "lf",
      "label": "max_load_factor",
      "label_vi": "max_load_factor",
      "min": 0.25,
      "max": 4,
      "step": 0.25,
      "value": 1,
      "unit": ""
    },
    {
      "name": "n",
      "label": "keys n",
      "label_vi": "số key n",
      "min": 100,
      "max": 10000,
      "step": 100,
      "value": 1000,
      "unit": ""
    }
  ],
  "let": [
    {
      "name": "buckets",
      "expr": "ceil(n/lf)"
    }
  ],
  "plot": {
    "x": {
      "name": "a",
      "min": 0.1,
      "max": 4,
      "label": "load factor = size / bucket_count",
      "label_vi": "load factor = size / bucket_count"
    },
    "y": {
      "label": "nodes visited per lookup",
      "label_vi": "số node duyệt mỗi lần tra cứu",
      "min": 0,
      "max": 4
    },
    "series": [
      {
        "expr": "a",
        "label": "failed lookup: a",
        "label_vi": "tra cứu thất bại: a",
        "color": "blue"
      },
      {
        "expr": "1+a/2",
        "label": "successful lookup: 1 + a/2",
        "label_vi": "tra cứu thành công: 1 + a/2",
        "color": "orange"
      }
    ],
    "points": [
      {
        "x": "lf",
        "y": "lf",
        "label": "failed",
        "label_vi": "thất bại",
        "color": "blue"
      },
      {
        "x": "lf",
        "y": "1+lf/2",
        "label": "successful",
        "label_vi": "thành công",
        "color": "orange"
      }
    ]
  },
  "readouts": [
    {
      "label": "nodes walked, failed lookup",
      "label_vi": "node duyệt, tra cứu thất bại",
      "expr": "lf",
      "unit": "",
      "digits": 2
    },
    {
      "label": "nodes walked, successful lookup",
      "label_vi": "node duyệt, tra cứu thành công",
      "expr": "1+lf/2",
      "unit": "",
      "digits": 2
    },
    {
      "label": "buckets needed for n keys (at least)",
      "label_vi": "số bucket cần cho n key (tối thiểu)",
      "expr": "buckets",
      "unit": "",
      "digits": 0
    }
  ]
}
```

**Ví dụ.** Thêm 50 phần tử vào một `vector`, một `deque`, một `list` và, với key 100 đến 149, vào một `unordered_map` đang có một phần tử. So sánh địa chỉ của phần tử đầu trước và sau cho thấy mỗi bố cục làm gì với bộ nhớ của nó: chỉ khối liên tục của `vector` di chuyển. Dòng cuối còn in số bucket (59 cho 51 phần tử ở đây). (So sánh địa chỉ ở đây chỉ để quan sát; tiêu chuẩn cho phép thư viện hành xử khác, xem bài tập 14.) Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <cstdint>
#include <deque>
#include <iostream>
#include <list>
#include <unordered_map>
#include <vector>

template <class C> void probe(const char* name, C& c) {
  auto before = reinterpret_cast<std::uintptr_t>(&*c.begin());
  for (int i = 0; i < 50; ++i) c.push_back(i);
  std::cout << name << ": first element moved? " << (before != reinterpret_cast<std::uintptr_t>(&*c.begin()) ? "yes" : "no") << '\n';
}

int main() {
  std::vector<int> v{7};  std::deque<int> d{7};  std::list<int> l{7};
  probe("vector", v); probe("deque", d); probe("list", l);
  std::unordered_map<int, int> m{{7, 0}};
  auto before = reinterpret_cast<std::uintptr_t>(&m[7]);
  for (int i = 100; i < 150; ++i) m[i] = i;
  std::cout << "unordered_map: value moved? " << (before != reinterpret_cast<std::uintptr_t>(&m[7]) ? "yes" : "no") << ", buckets " << m.bucket_count() << '\n';
}
```

```text
vector: first element moved? yes
deque: first element moved? no
list: first element moved? no
unordered_map: value moved? no, buckets 59
```

### Tìm kiếm nhị phân: loop invariant, số phép so sánh chính xác, và `lower_bound` yêu cầu gì

Gọi `p(e)` là vị từ "$e<x$" theo comparator. `lower_bound` tìm phần tử đầu tiên mà `p` sai, và chỉ yêu cầu dãy được **partition** theo `p` (mọi phần tử `true` đứng trước mọi phần tử `false`); dãy đã sắp xếp là cách thường dùng để đảm bảo điều đó (cppreference: `std::lower_bound`, Notes). Vòng lặp chuẩn là

```cpp
auto count = std::distance(first, last);
while (count > 0) {
  auto it = first; auto step = count / 2; std::advance(it, step);
  if (comp(*it, value)) { first = ++it; count -= step + 1; }
  else                    count = step;
}
return first;
```

*Invariant.* Gọi dãy gốc là $[a,b)$, ở đầu mỗi vòng lặp mọi phần tử trong $[a,\text{first})$ thỏa `p`, và phần tử đầu tiên không thỏa `p` (hoặc $b$) nằm trong $[\text{first},\text{first}+\text{count}]$. *Khởi tạo:* $\text{first}=a$, $\text{count}=b-a$ đúng hiển nhiên. *Bảo toàn:* với $\text{step}=\lfloor \text{count}/2\rfloor$, nếu `p(*it)` đúng thì do partition, mọi thứ đến và gồm `it` đều thỏa `p`, nên ta đẩy `first` qua `it` và bớt $\text{step}+1$ khỏi count; ngược lại `*it` là ứng viên cho đáp án và đáp án nằm trong $[\text{first},\,\text{first}+\text{step}]$, nên `count = step`. *Kết thúc:* `count` giảm nghiêm ngặt và vòng lặp dừng ở $0$, khi invariant nói đáp án là `first`. Vì chứng minh chỉ dùng tính chất partition, `lower_bound` không cần thứ tự toàn phần trên mọi phần tử.

*Trường hợp xấu nhất chính xác.* Mỗi vòng lặp tốn một phép so sánh và để lại $\text{count}'\le\max(\lfloor n/2\rfloor,\,n-\lfloor n/2\rfloor-1)=\lfloor n/2\rfloor$. Do đó $W(n)=1+W(\lfloor n/2\rfloor)$ với $W(0)=0$, nên $W(n)=\lfloor\log_2 n\rfloor+1=\lceil\log_2(n+1)\rceil$: $19$ với $n=360{,}000$ và $20$ với $n=10^6$. Đo trên mọi mục tiêu có thể: $n=2^{20}$ cho $21$, $n=1000$ cho $10$ (xấu nhất) và $9$ (tốt nhất), và với $n=2^k-1$ mọi lần tìm đều tốn đúng $k$ phép so sánh.

*Một lỗi kinh điển mà dạng này tránh được.* Tìm kiếm nhị phân viết `mid = (lo + hi) / 2` trên `int` bị tràn khi `lo + hi` vượt $2^{31}-1$: với `lo = 2000000000` và `hi = 2100000000` tổng là $4.1\cdot10^9$, bị quấn thành $-194{,}967{,}296$ trong bù hai 32-bit. Vòng lặp trên không bao giờ cộng hai vị trí; nó chia đôi một *số lượng*, nên không có tổng chỉ số nào xuất hiện.

![Trái: số phép so sánh tệ nhất floor(log2 n) + 1 theo n trên trục log với 10, 14, 17 và 20 được đánh dấu tại 10^3 đến 10^6; phải: kích thước cửa sổ sau mỗi phép so sánh với n = 45 và đích 0 và 44](/lesson-figures/CPP05-3.svg)

*Hình: bên trái, trường hợp xấu nhất tăng thêm một phép so sánh mỗi khi $n$ gấp đôi, nên một triệu mẫu tốn 20 còn quét tuyến tính tốn tới một triệu. Bên phải, vòng lặp của mục này với $n=45$: cửa sổ $45\to22\to11\to5\to2\to1$ cho đích 0 (không bao giờ nhỏ hơn phần tử, 6 phép so sánh, trường hợp xấu nhất) và $45\to22\to10\to4\to1$ cho đích 44 (luôn nhỏ hơn, 5 phép so sánh).*

**Ví dụ.** Một comparator đếm số lần được gọi cho ra chi phí chính xác. Trên vector đã sắp xếp $0,1,\dots,44$ ($n=45$), tìm mọi đích có thể tốn ít nhất 5 và nhiều nhất 6 phép so sánh, và $\lfloor\log_2 45\rfloor+1=6$ là trường hợp xấu nhất suy ra ở trên (các vết trong hình). Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <algorithm>
#include <iostream>
#include <numeric>
#include <vector>

int main() {
  std::vector<int> v(45);
  std::iota(v.begin(), v.end(), 0);                // 0, 1, ..., 44
  int worst = 0, best = 99;
  for (int x = 0; x < 45; ++x) {
    int count = 0;
    auto it = std::lower_bound(v.begin(), v.end(), x, [&](int e, int value) { ++count; return e < value; });
    if (it - v.begin() != x) return 1;
    worst = std::max(worst, count);
    best = std::min(best, count);
  }
  std::cout << "n=45 best=" << best << " worst=" << worst << '\n';
}
```

```text
n=45 best=5 worst=6
```

### Strict weak ordering: vì sao một NaN có thể làm hỏng `set`, `sort` và `lower_bound`

Container có thứ tự và `std::sort` yêu cầu comparator `comp` là một **strict weak ordering**: irreflexive ($\text{comp}(a,a)$ sai), asymmetric, transitive, và với *equivalence* bắc cầu, trong đó $a\sim b$ nghĩa là $\neg\text{comp}(a,b)\wedge\neg\text{comp}(b,a)$ (cppreference: yêu cầu Compare). Phép `<` có sẵn trên `double` thỏa tất cả trừ khi có NaN. Lấy $a=1$, $b=\text{NaN}$, $c=2$: mọi phép so sánh với NaN đều sai, nên $a\sim b$ và $b\sim c$, nhưng $a<c$ nghĩa là $a\not\sim c$. Equivalence không bắc cầu, nên `<` không phải strict weak ordering trên tập chứa NaN, và hành vi của `std::sort` và `std::set` là undefined. Trong thực tế (libstdc++) chèn $1,2,\text{NaN},3$ vào `std::set<double>` còn lại 3 phần tử, còn chèn $\text{NaN},1,2,3$ chỉ còn 1 phần tử: kết quả phụ thuộc thứ tự chèn, một triệu chứng của undefined behavior. `std::is_sorted` trả `true` trên $\{1,2,3,\text{NaN},5,6,7\}$ và `lower_bound` trả chỉ số 3 cho các mục tiêu $4$, $5$ và $6.5$: với $4$ và $5$ đó là đáp án đúng *theo định nghĩa* "phần tử đầu tiên không nhỏ hơn $x$" (NaN "không nhỏ hơn" bất cứ gì), còn với $6.5$ vị từ $e<6.5$ là đúng, sai, đúng sau NaN, nên dãy không được partition và điều kiện tiên quyết bị vi phạm. Cách sửa là từ chối NaN ở biên (thói quen validate của bài) hoặc dùng comparator thực sự là strict weak ordering, chẳng hạn "NaN xếp sau mọi số": `comp(a,b) = !isnan(a) && (isnan(b) || a < b)`, tức thứ tự từ điển trên các cặp $(\text{isnan}(x),x)$.

**Ví dụ.** Với $a=4$, $b=\text{NaN}$, $c=5$ cả hai tương đương $a\sim b$ và $b\sim c$ đều đúng trong khi $a\not\sim c$, nên tương đương không bắc cầu và `<` không phải strict weak ordering trên tập có NaN. Comparator "NaN đứng cuối" sửa điều đó: nó sắp $\{9.5,\text{NaN},7.25,8\}$ thành $7.25,\;8,\;9.5,\;\text{NaN}$. Biên dịch bằng g++ 11.4.0 (Ubuntu 22.04), `-std=c++20 -Wall -Wextra`:

```cpp
#include <algorithm>
#include <cmath>
#include <iostream>
#include <vector>

int main() {
  const double nan = std::nan("");
  std::cout << "4~NaN " << (!(4 < nan) && !(nan < 4)) << ", NaN~5 " << (!(nan < 5) && !(5 < nan)) << ", 4~5 " << (!(4 < 5) && !(5 < 4)) << '\n';
  std::vector<double> v{9.5, nan, 7.25, 8.0};
  std::sort(v.begin(), v.end(), [](double a, double b) { return !std::isnan(a) && (std::isnan(b) || a < b); });
  for (double x : v) std::cout << x << ' ';
  std::cout << '\n';
}
```

```text
4~NaN 1, NaN~5 1, 4~5 0
7.25 8 9.5 nan 
```

## Ví dụ có lời giải

Hai trường hợp dùng các công cụ của lý thuyết ở trên: `lower_bound` và `upper_bound` (Binary search), nội suy tuyến tính, `accumulate` và erase-remove (Erase-remove và các thuật toán thông dụng) và `vector::insert` (Iterator và sự vô hiệu hóa).

### Trường hợp 1: nội suy giữa các lân cận và làm sạch một chuỗi

**Đề bài.** Một chuỗi thời gian được lưu thành vector đã sắp xếp các cặp $(t_i,v_i)$, $t$ tính bằng giây: $(0,0)$, $(1,10)$, $(2,20)$, $(4,60)$. Tìm $v(3)$ bằng nội suy tuyến tính, số mẫu có $1\le t\le2$, và kết quả khi xóa mọi mẫu có $|v|>50$; đồng thời nói điều gì xảy ra với các truy vấn $t=4.1$, $t=-0.1$ và $t=1$.

**Lời giải.**

1. *Xác định các lân cận (Binary search).* `lower_bound` cho $t=3$ bắt đầu với cửa sổ $n=4$ phần tử. Điểm thăm là chỉ số $\lfloor4/2\rfloor=2$, nơi $t_2=2<3$, nên cửa sổ trở thành một phần tử duy nhất ở chỉ số 3. Tại đó $t_3=4\ge3$, nên cửa sổ rỗng và kết quả là chỉ số 3, cặp $(4,60)$. Đã dùng hai phép so sánh, nằm trong cận $\lceil\log_2(4+1)\rceil=3$.
2. *Xác định trường hợp.* Kết quả không phải `end()` cũng không phải `begin()`, và $t_3=4\ne3$ không phải trùng khớp chính xác, nên giá trị nằm nghiêm ngặt giữa phần tử trước $(2,20)$ và $(4,60)$.
3. *Nội suy.* $v(3)=v_a+(v_b-v_a)\dfrac{t-t_a}{t_b-t_a}=20+(60-20)\dfrac{3-2}{4-2}=20+40\cdot0.5=40$.
4. *Truy vấn biên.* Với $t=4.1$ cửa sổ kết thúc ở `end()`, nên đáp án là "không có giá trị". Với $t=-0.1$ kết quả là `begin()` có $t_0=0>-0.1$, lại "không có giá trị". Với $t=1$ kết quả là chỉ số 1 có $t_1=1$ bằng truy vấn, trùng khớp chính xác: trả về 10 mà không nội suy.
5. *Đếm một khoảng đóng.* `lower_bound(1)` là chỉ số 1 và `upper_bound(2)` là chỉ số 3, nên số mẫu có $1\le t\le2$ là $3-1=2$.
6. *Erase-remove với giới hạn 50.* `remove_if(|v|>50)` giữ $(0,0)$, $(1,10)$, $(2,20)$ và trả về iterator ở chỉ số 3; `erase(chỉ số 3, end)` thu size từ 4 xuống 3, nên số phần tử bị xóa là $4-3=1$.

**Kiểm tra.** Điểm $t=3$ là trung điểm của $[2,4]$, nên $v(3)$ phải là trung điểm của $20$ và $60$, tức 40. Cài đặt tham khảo bên dưới trả về đúng các kết quả này ở mọi bước (self-test của nó chạy qua với `-fsanitize=address,undefined`).

**Rút ra.** Một vector đã sắp xếp trả lời "giá trị tại thời điểm $t$" bằng hai quyết định rẻ, một lần binary search và một lần tách trường hợp theo `end()`, `begin()` và trùng khớp chính xác, trước khi làm bất kỳ phép tính nào.

### Trường hợp 2: một mẫu đến trễ, một đỉnh nhiễu và trung bình theo khoảng

**Đề bài.** Một log cảm biến dòng (mili giây, ampe) có các mẫu đã sắp xếp $(10,3.0)$, $(20,3.2)$, $(30,3.1)$, $(50,9.8)$, $(60,3.4)$, $(80,3.5)$. (a) Một mẫu đến trễ $(40,3.3)$: tìm chỉ số chèn và số phần tử `vector::insert` phải dịch. (b) Tính trung bình các mẫu có $20\le t\le60$ ms. (c) Giá trị 9.8 A là đỉnh nhiễu: xóa mọi mẫu trên 5 A và tính lại trung bình trên cùng khoảng. (d) Nội suy dòng tại $t=45$ ms trong chuỗi đã làm sạch.

**Lời giải.**

1. *Chỉ số chèn (Binary search).* `upper_bound(40)` là phần tử đầu tiên có $t>40$, tức $(50,9.8)$ ở chỉ số 3. Chèn tại đó giữ chuỗi được sắp xếp, kể cả khi có timestamp trùng.
2. *Chi phí chèn (Iterator và sự vô hiệu hóa).* `vector::insert` dịch các phần tử từ điểm chèn đến cuối: $6-3=3$ phần tử dịch một ô (cppreference, `std::vector::insert`, Complexity: tuyến tính theo khoảng cách từ vị trí đến cuối). Size thành 7, và các iterator từ chỉ số 3 trở đi bị vô hiệu hóa (mọi iterator nếu dung lượng đã hết).
3. *Khoảng của giá trị trung bình.* Trong chuỗi mới $t=\{10,20,30,40,50,60,80\}$, `lower_bound(20)` là chỉ số 1 và `upper_bound(60)` là chỉ số 6, nên khoảng chứa $6-1=5$ mẫu: $3.2$, $3.1$, $3.3$, $9.8$, $3.4$.
4. *Trung bình khi có đỉnh nhiễu.* `accumulate(lo, hi, 0.0, ...)` cộng các giá trị: $3.2+3.1+3.3+9.8+3.4=22.8$ A, và trung bình là $22.8/5=4.56$ A. Giá trị đầu phải là `0.0`: `int` sẽ cắt cụt mọi tổng riêng.
5. *Làm sạch bằng erase-remove.* `remove_if(v>5)` giữ 6 mẫu và `erase` xóa một mẫu vượt giới hạn, nên size từ 7 xuống 6. Các mẫu trong $20\le t\le60$ giờ là $3.2$, $3.1$, $3.3$, $3.4$ (4 mẫu), tổng $13.0$ A và trung bình $13.0/4=3.25$ A.
6. *Nội suy sau khi làm sạch.* Trong chuỗi đã làm sạch `lower_bound(45)` tìm $(60,3.4)$ và phần tử trước nó là mẫu đến trễ $(40,3.3)$, nên $v(45)=3.3+(3.4-3.3)\dfrac{45-40}{60-40}=3.3+0.1\cdot0.25=3.325$ A.

**Kiểm tra.** Chạy Python cho $22.8/5=4.56$, $13.0/4=3.25$ và $3.325$ (đầu ra số thực $4.5600000000000005$, $3.2500000000000004$, $3.3249999999999997$). Một chương trình C++ với cùng các lời gọi in `insert index 3, tail elements moved 3`, `range [1,6) count 5 mean 4.56`, `removed 1`, `count 4 mean 3.25`, `v(45) = 3.325` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). Kiểm tra ý nghĩa: một giá trị ngoại lai 9.8 A giữa bốn giá trị gần 3.25 A nâng trung bình lên 1.31 A, vì vậy bước làm sạch phải đứng trước bước thống kê.

**Rút ra.** Thứ tự các thao tác quan trọng: chèn dữ liệu đến trễ đúng vị trí đã sắp xếp, làm sạch giá trị ngoại lai, rồi mới tính trung bình và nội suy, vì mỗi bước đổi các chỉ số và giá trị mà bước sau nhìn thấy.

![Trái: chuỗi đã sắp xếp sau khi chèn với đỉnh nhiễu 9.8 A, khoảng 20 đến 60 ms và hai giá trị trung bình 4.56 A và 3.25 A; phải: các phần tử trước và sau vector::insert tại chỉ số 3 với ba phần tử bị dịch](/lesson-figures/CPP05-4.svg)

*Hình: các số của Trường hợp 2. Dải tô là khoảng $[20,60]$ ms; các đường nét đứt là trung bình trên khoảng đó khi có và không có đỉnh nhiễu. Bảng cho thấy ba phần tử (màu vàng) mà `vector::insert` dịch đi để nhường chỗ cho mẫu đến trễ (màu xanh lục).*

## Bài tập

Các bài đánh dấu *Adapted* diễn đạt lại một dạng bài tập chuẩn từ nguồn được trích dẫn, bằng lời và số liệu mới.

1. **(Dễ)** *(Adapted from: cppreference, Containers library overview)* Chọn container tốt nhất và biện minh trong một câu: (a) 100 lần đọc range gần nhất, loại bỏ cái cũ nhất; (b) tra cứu từ id frame camera (số nguyên) sang metadata của nó; (c) kết quả detection phải duy nhất và sắp xếp theo id; (d) một log IMU 30 phút được truy vấn "mẫu gần nhất với thời điểm $t$".
2. **(Dễ)** Dự đoán output:
   ```cpp
   std::vector<int> v{3, 1, 4, 1, 5, 9, 2, 6};
   auto e = std::remove(v.begin(), v.end(), 1);
   std::cout << (e - v.begin()) << ' ' << v.size();
   v.erase(e, v.end());
   std::cout << ' ' << v.size();
   ```
3. **(Dễ)** Một log 200 Hz dài 90 phút có 1,080,000 mẫu. Quét tuyến tính cần bao nhiêu phép so sánh trong trường hợp xấu nhất và `lower_bound` cần bao nhiêu? Tỉ số là bao nhiêu?
4. **(Trung bình)** Tìm hai bug undefined-behavior trong hàm trợ giúp nội suy này, và sửa chúng.
   ```cpp
   double interp(const std::vector<Sample>& v, double t) {
     auto it = std::lower_bound(v.begin(), v.end(), t, [](const Sample& s, double x) { return s.t < x; });
     const Sample& a = *(it - 1);
     const Sample& b = *it;
     return a.v + (b.v - a.v) * (t - a.t) / (b.t - a.t);
   }
   ```
5. **(Trung bình)** *(Adapted from: cppreference, `std::vector::erase` and iterator invalidation)* Vòng lặp này xóa các giá trị đọc trên 50. Giải thích chính xác điều gì sai, rồi viết cách sửa hai lần (một lần dùng giá trị trả về của erase, một lần dùng erase-remove).
   ```cpp
   for (auto it = v.begin(); it != v.end(); ++it)
     if (it->v > 50) v.erase(it);
   ```
6. **(Trung bình)** Dự đoán output và nêu bài học thiết kế:
   ```cpp
   std::map<std::string, double> gains;
   double kp = gains["kp"];
   std::cout << kp << ' ' << gains.size();
   ```
7. **(Trung bình)** Một cửa sổ 1001 mẫu cần trung vị mỗi 10 ms. So sánh `std::sort` với `std::nth_element` về chi phí, nêu kết quả của `nth_element` trên `{7,1,5,3,9}` tại vị trí 2, và nói điều gì xảy ra với các phần tử còn lại.
8. **(Khó)** *(Adapted from: cppreference, `std::lower_bound` and `std::map::lower_bound`)* Bạn phải trả lời "giá trị tại thời điểm $t$" cho $10^6$ mẫu đã lưu với $2\times10^6$ truy vấn ngẫu nhiên. Thiết kế một benchmark công bằng cho `vector`+`lower_bound`, `map::lower_bound` và một `unordered_map` khóa theo chỉ số mẫu nguyên. Liệt kê năm thứ bạn kiểm soát (mức tối ưu hóa, warm-up, sinh truy vấn, việc dùng kết quả, chạy lặp lại) và dự đoán thứ tự cùng lý do `unordered_map` không so sánh trực tiếp được.
9. **(Khó)** Các mẫu đến muộn không theo thứ tự (khoảng 1% của 1,000 lần chèn mỗi giây vào một chuỗi $10^5$ mẫu, mỗi mẫu 16 byte). Ước lượng lượng dữ liệu bị di chuyển cho mỗi lần chèn giữa vào một `vector` và mỗi giây. Dùng `map` có hợp lý không? Bạn sẽ đo gì trước tiên?
10. **(Khó)** Suy dẫn cận chi phí amortized: với hệ số tăng trưởng $g$, chứng minh $n$ lần push gây tối đa $\frac{g}{g-1}n$ lần di chuyển phần tử trong các lần cấp phát lại, và tính nó cho $g=1.25$ và $g=3$. Vì sao các implementation không chọn $g$ rất lớn?
11. **(Mini-project)** Viết benchmark của bài tập 8 thành một chương trình, báo cáo nano giây mỗi truy vấn cho $N\in\{10^3,10^5,10^6\}$ trong một bảng, nêu các tỉ số, và giải thích bằng một đoạn về cache locality vì sao khoảng cách tăng theo $N$.

12. **(Thử thách)** Tìm kiếm nhị phân, chính xác. Dùng vòng lặp `lower_bound` ở phần lý thuyết, (a) chứng minh invariant được bảo toàn khi `comp(*it, value)` sai, và khi kết thúc hàm trả về phần tử đầu tiên không nhỏ hơn `value`. (b) Chứng minh trường hợp xấu nhất là $\lfloor\log_2 n\rfloor+1$ phép so sánh và tính cho $n=1$, $5000$ và $2^{16}$. (c) Với $n\le40$ nào thì trường hợp tốt nhất bằng xấu nhất? Nêu quy luật, và cho trường hợp tốt nhất và xấu nhất với $n=5000$. (d) Một đồng đội viết `mid = (lo + hi) / 2` với chỉ số `int` 32-bit trên một log $2.0\cdot10^9$ phần tử đang tìm ở nửa trên, với `lo = 1900000000` và `hi = 2000000000`: tính `lo + hi` dưới dạng bù hai 32-bit và cho công thức an toàn. (phỏng theo cppreference, `std::lower_bound`, Complexity và Possible implementation)
13. **(Thử thách)** NaN trong container đã sắp xếp. (a) Chứng minh `a < b` trên `double` không phải strict weak ordering trên tập chứa NaN bằng cách chỉ ra ba giá trị mà quan hệ equivalence không bắc cầu. (b) Với vector $\{1.5,3.5,\text{NaN},7.5,9.5\}$ cho chỉ số `lower_bound(x)` với $x=1,\,3.5,\,5,\,7.5,\,8.5,\,10$ dùng `<` mặc định (libstdc++, g++ 11.4), và nói trường hợp nào kết quả đúng theo định nghĩa, trường hợp nào điều kiện tiên quyết bị vi phạm. (c) Dự đoán kích thước của `std::set<double>` sau khi chèn $4,6,\text{NaN},8$ và sau khi chèn $\text{NaN},4,6,8$. (d) Cho một comparator là strict weak ordering với NaN xếp cuối, lập luận vì sao, và nói `std::sort` trả về gì cho $\{8,\text{NaN},5,\text{NaN},6\}$. (phỏng theo cppreference, yêu cầu Compare và Notes của `std::lower_bound`)
14. **(Thử thách)** Dự đoán rồi đo vô hiệu hóa và tăng trưởng. (a) Push 300 `int` từng cái một vào `std::vector<int>` rỗng: với doubling, liệt kê các capacity, đếm số lần cấp phát lại sau lần đầu và tổng số phần tử được relocate; so với cận $\frac{g}{g-1}n$. (b) Gọi `max_load_factor(0.5)` trên `std::unordered_map<int,int>` rỗng rồi chèn các khóa $0,\dots,99$: nêu quy tắc chính xác kích hoạt rehash, nói cái nào trong {iterator, reference tới `m[0]`} sống sót sau rehash, và dùng quy tắc để tìm các kích thước tại đó rehash xảy ra khi các số bucket quan sát được là $1,23,47,97,199,409$. (c) Sau `std::deque<int> d{5,6,7,8}; int* p = &d[2]; d.push_front(4); d.push_front(3); d.push_back(9);` `p` còn hợp lệ không, và nó trỏ tới gì? (d) Câu trả lời nào được tiêu chuẩn đảm bảo và câu nào là thuộc tính của libstdc++? (phỏng theo cppreference, Containers library "Iterator invalidation" và `std::unordered_map::insert`)
15. **(Thử thách)** Gộp dữ liệu đến trễ. Một `vector` đã sắp xếp chứa $n=100{,}000$ mẫu; $k=1000$ mẫu đến trễ với timestamp ngẫu nhiên đều phải được gộp vào. (a) Dùng độ phức tạp của `std::vector::insert` (tuyến tính theo khoảng cách từ vị trí tới cuối), ước lượng tổng số phép move phần tử khi chèn từng cái bằng `lower_bound`. (b) Ước lượng chi phí của: sắp xếp $k$ mẫu trễ, nối vào cuối, `std::inplace_merge`. (c) Đo bằng kiểu phần tử có đếm (seed 42, g++ 11.4 `-O2`): báo cáo hai số đếm và tỉ lệ. (d) Chế độ nào thì chèn từng cái thực sự tốt hơn, và bạn sẽ đo đại lượng nào trước? (phỏng theo cppreference, Complexity của `std::inplace_merge` và Complexity của `std::vector::insert`)

## Cài đặt tham khảo

Một chuỗi thời gian dạng vector đã sắp xếp với nội suy, truy vấn khoảng bao gồm hai đầu và erase-remove. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra ref.cpp && ./a.out`.

```cpp
// CPP05 reference: a timestamped series on a sorted std::vector, queried with STL algorithms.
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <numeric>
#include <optional>
#include <vector>

struct Sample {
  double t;  // seconds
  double v;
};

class TimeSeries {
 public:
  // Appends only if t is finite and strictly later than the last sample.
  bool append(double t, double v) {
    if (!std::isfinite(t)) return false;
    if (!data_.empty() && !(t > data_.back().t)) return false;
    data_.push_back({t, v});
    return true;
  }
  std::size_t size() const { return data_.size(); }

  // Linearly interpolated value at time t, or nullopt outside [first.t, last.t].
  std::optional<double> at(double t) const {
    auto it = std::lower_bound(data_.begin(), data_.end(), t,
                               [](const Sample& s, double x) { return s.t < x; });
    if (it == data_.end()) return std::nullopt;       // after the last sample
    if (it->t == t) return it->v;                      // exact hit
    if (it == data_.begin()) return std::nullopt;     // before the first sample
    const Sample& a = *(it - 1);
    const Sample& b = *it;
    return a.v + (b.v - a.v) * (t - a.t) / (b.t - a.t);
  }

  // Number of samples with t0 <= t <= t1.
  std::size_t count_in(double t0, double t1) const {
    auto [lo, hi] = range(t0, t1);
    return static_cast<std::size_t>(hi - lo);
  }

  // Mean of the values with t0 <= t <= t1, or nullopt if there are none.
  std::optional<double> mean_in(double t0, double t1) const {
    auto [lo, hi] = range(t0, t1);
    if (lo >= hi) return std::nullopt;
    double sum = std::accumulate(lo, hi, 0.0, [](double acc, const Sample& s) { return acc + s.v; });
    return sum / static_cast<double>(hi - lo);
  }

  // Erase-remove: drops every sample with |v| > limit, returns how many were removed.
  std::size_t drop_above(double limit) {
    auto new_end = std::remove_if(data_.begin(), data_.end(),
                                  [limit](const Sample& s) { return std::fabs(s.v) > limit; });
    std::size_t removed = static_cast<std::size_t>(data_.end() - new_end);
    data_.erase(new_end, data_.end());
    return removed;
  }

 private:
  using It = std::vector<Sample>::const_iterator;
  std::pair<It, It> range(double t0, double t1) const {
    auto lo = std::lower_bound(data_.begin(), data_.end(), t0,
                               [](const Sample& s, double x) { return s.t < x; });
    auto hi = std::upper_bound(data_.begin(), data_.end(), t1,
                               [](double x, const Sample& s) { return x < s.t; });
    if (hi < lo) hi = lo;  // t1 < t0
    return {lo, hi};
  }
  std::vector<Sample> data_;
};

// ---- self-test
int main() {
  TimeSeries s;
  for (auto [t, v] : std::vector<Sample>{{0, 0}, {1, 10}, {2, 20}, {4, 60}}) s.append(t, v);
  if (s.at(3.0).value() != 40.0) return 1;
  if (s.at(-0.1) || s.at(4.1)) return 2;
  if (s.count_in(1.0, 2.0) != 2) return 3;
  if (s.mean_in(0.0, 2.0).value() != 10.0) return 4;
  if (s.append(4.0, 1.0)) return 5;
  if (s.drop_above(50.0) != 1 || s.size() != 3) return 6;
  std::cout << "CPP05 reference self-test passed\n";
}
```

## Thực hành độc lập

### Mục tiêu

Xây cấu trúc tra cứu có timestamp trên một `std::vector` đã sắp xếp, kiểm thử các trường hợp biên của nó, và so sánh với `std::map` bằng một benchmark do bạn viết.

### Chuẩn bị

`g++` hoặc `clang++` với C++17. Lưu starter và các test bên dưới nó thành `lab.cpp`, biên dịch bằng `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined lab.cpp -o lab && ./lab`. Với benchmark ở nhiệm vụ cuối, biên dịch một file riêng với `-O2` và không có sanitizer.

### Nhiệm vụ

1. Cài đặt `append` và `size`. Làm cho timestamp bằng nhau và giảm dần thất bại.
2. Cài đặt `at` với `lower_bound`; xử lý trúng chính xác, `begin()` và `end()` trước khi nội suy.
3. Cài đặt `count_in` và `mean_in` với `lower_bound`/`upper_bound` và `accumulate`.
4. Cài đặt `drop_above` bằng erase-remove và trả về số phần tử đã xóa.
5. Viết một class thứ hai có cùng interface trên `std::map<double,double>` dùng `map::lower_bound`; chạy các test giống hệt trên nó.
6. Benchmark cả hai với $N=10^3,10^5,10^6$ và $2\times10^6$ truy vấn ngẫu nhiên ở `-O2`; in ns mỗi truy vấn và tỉ số.

### Code khởi đầu

```cpp
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <vector>

struct Sample {
  double t;  // seconds
  double v;
};

// Samples are kept sorted by strictly increasing t in a std::vector.
class TimeSeries {
 public:
  // Append only if t is finite and strictly later than the last sample; else return false, no change.
  bool append(double t, double v) { throw std::logic_error("NotImplemented"); }
  std::size_t size() const { throw std::logic_error("NotImplemented"); }

  // Linearly interpolated value at time t; nullopt if t < first.t or t > last.t.
  // Use std::lower_bound (O(log n)), not a linear scan. An exact timestamp returns its stored value.
  std::optional<double> at(double t) const { throw std::logic_error("NotImplemented"); }

  // Number of samples with t0 <= t <= t1 (inclusive both ends). 0 if t1 < t0.
  std::size_t count_in(double t0, double t1) const { throw std::logic_error("NotImplemented"); }

  // Mean of values with t0 <= t <= t1 (std::accumulate), nullopt if there are none.
  std::optional<double> mean_in(double t0, double t1) const { throw std::logic_error("NotImplemented"); }

  // Erase-remove idiom: delete every sample with |v| > limit; return the number removed.
  std::size_t drop_above(double limit) { throw std::logic_error("NotImplemented"); }
};
```

### Kiểm thử

```cpp

// ---- tests (paste below the starter code)
#include <cstdlib>
#include <iostream>
#include <random>
#define CHECK(c) do { if (!(c)) { std::cerr << "FAIL line " << __LINE__ << ": " #c "\n"; std::exit(1); } } while (0)

int main() {
  TimeSeries s;
  CHECK(s.size() == 0 && !s.at(0.0) && !s.mean_in(0, 1) && s.count_in(0, 1) == 0);  // empty series
  CHECK(s.append(0.5, 4) && s.append(1.5, 10) && s.append(2, 7) && s.append(5, 19));
  CHECK(s.size() == 4);
  // hand-computed interpolation: between (2,7) and (5,19) at t=3.5 -> 13; between (0.5,4) and (1.5,10) at t=1 -> 7
  CHECK(s.at(3.5).value() == 13.0);
  CHECK(std::fabs(s.at(1.0).value() - 7.0) < 1e-12);
  // exact timestamps and ends
  CHECK(s.at(0.5).value() == 4.0 && s.at(1.5).value() == 10.0 && s.at(5.0).value() == 19.0);
  CHECK(!s.at(0.4) && !s.at(5.1));
  // append rules
  CHECK(!s.append(5.0, 1.0) && !s.append(3.0, 1.0) && !s.append(NAN, 1.0) && s.size() == 4);
  // ranges (inclusive)
  CHECK(s.count_in(1.5, 2.0) == 2 && s.count_in(1.0, 4.9) == 2 && s.count_in(6, 7) == 0 && s.count_in(2, 1) == 0);
  CHECK(s.mean_in(0.5, 2.0).value() == 7.0 && !s.mean_in(2.5, 4.5));
  // erase-remove
  CHECK(s.drop_above(15.0) == 1 && s.size() == 3 && !s.at(5.0));
  CHECK(s.drop_above(1000.0) == 0);
  // property: interpolation at every stored time equals the stored value, and is monotone for monotone data
  TimeSeries r;
  std::mt19937 g(7);
  std::uniform_real_distribution<double> dt(0.01, 1.0);
  double t = 0, v = 0;
  std::vector<Sample> ref;
  for (int i = 0; i < 500; ++i) { t += dt(g); v += dt(g); CHECK(r.append(t, v)); ref.push_back({t, v}); }
  for (const Sample& p : ref) CHECK(r.at(p.t).value() == p.v);
  double prev = -1;
  for (double q = ref.front().t; q <= ref.back().t; q += 0.37) { double x = r.at(q).value(); CHECK(x >= prev); prev = x; }
  CHECK(r.count_in(ref.front().t, ref.back().t) == 500);
  std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi

```
all tests passed
```

Với benchmark, hãy kỳ vọng `vector` nhanh hơn `map` và khoảng cách tăng theo $N$ (trên một máy thử, các tỉ số khoảng 1.0 ở $10^3$, 1.7 ở $10^5$ và 3.6 ở $10^6$; số của bạn sẽ khác).

### Thử thách mở rộng

Thêm `insert_sorted(t, v)` chấp nhận các mẫu đến muộn bằng `upper_bound` và `vector::insert`, và đo chi phí như một hàm của khoảng cách từ vị trí chèn đến cuối. Sau đó so sánh với cài đặt `std::map` cho 1% mẫu đến muộn.

### Thực hành với thư viện

Chỉ dùng standard library (`<map>`, `<chrono>`, `<random>`) cho nhiệm vụ 5 và 6. Dán đoạn này *sau* `TimeSeries` đã hoàn thiện của bạn (nó có `main` riêng, nên bỏ `main` của phần test) và biên dịch riêng bằng `g++ -std=c++17 -O2 -Wall -Wextra` (không dùng sanitizer khi đo thời gian).

```cpp
#include <cassert>
#include <chrono>
#include <iostream>
#include <map>
#include <random>

// Same interface on std::map, for the cross-check and the benchmark (task 5).
class MapSeries {
 public:
  bool append(double t, double v) {
    if (!std::isfinite(t) || (!m_.empty() && !(t > m_.rbegin()->first))) return false;
    m_.emplace_hint(m_.end(), t, v);
    return true;
  }
  std::optional<double> at(double t) const {
    auto it = m_.lower_bound(t);
    if (it == m_.end()) return std::nullopt;
    if (it->first == t) return it->second;
    if (it == m_.begin()) return std::nullopt;
    auto a = std::prev(it);
    return a->second + (it->second - a->second) * (t - a->first) / (it->first - a->first);
  }
 private:
  std::map<double, double> m_;
};

template <class S>
double ns_per_query(const S& s, const std::vector<double>& q, double& sink) {
  using clk = std::chrono::steady_clock;
  double best = 1e300;
  for (int rep = 0; rep < 5; ++rep) {                         // repeats: keep the best (least noisy)
    auto t0 = clk::now();
    for (double x : q) sink += s.at(x).value_or(0.0);         // consume results
    best = std::min(best, std::chrono::duration<double, std::nano>(clk::now() - t0).count() / q.size());
  }
  return best;
}

int main() {
  std::mt19937 g(1);
  for (std::size_t n : {1000u, 100000u, 1000000u}) {
    TimeSeries vs; MapSeries ms;
    for (std::size_t i = 0; i < n; ++i) { vs.append(0.01 * i, std::sin(0.01 * i)); ms.append(0.01 * i, std::sin(0.01 * i)); }
    std::uniform_real_distribution<double> u(0.0, 0.01 * (n - 1));
    std::vector<double> q(2000000); for (double& x : q) x = u(g);
    for (int i = 0; i < 1000; ++i) assert(std::fabs(vs.at(q[i]).value() - ms.at(q[i]).value()) < 1e-12);  // same answers
    double sink = 0;
    double a = ns_per_query(vs, q, sink), b = ns_per_query(ms, q, sink);
    std::cout << "N=" << n << "  vector " << a << " ns  map " << b << " ns  ratio " << b / a << "  check " << sink << "\n";
  }
}
```

Trên một máy thử, output là các tỉ số khoảng 1.5, 2.3 và 4.2 cho $N=10^3, 10^5, 10^6$ (vector 64, 162, 248 ns mỗi truy vấn; map 94, 374, 1032 ns); của bạn sẽ khác, nhưng tỉ số nên tăng theo $N$. `assert` kiểm tra rằng cả hai cấu trúc trả về cùng giá trị nội suy. Câu hỏi: vì sao thời gian của vector vẫn tăng theo $N$? Điều gì xảy ra với tỉ số nếu các truy vấn được sắp xếp thay vì ngẫu nhiên?

![Trái: trung vị của ba lần chạy thời gian mỗi truy vấn cho vector đã sắp xếp và map tại N = 10^3, 10^5 và 10^6; phải: dung lượng dữ liệu 16 byte mỗi mẫu và 48 byte mỗi node cây so với kích thước cache L2 và L3](/lesson-figures/CPP05-5.svg)

*Hình: thời gian mỗi truy vấn phụ thuộc máy. Trung vị của ba lần chạy chương trình ở trên trên Intel Core i5-12500H (L2 1.5 MiB mỗi lõi, L3 18 MiB), g++ 11.4.0, `-O2`: vector 53, 104 và 180 ns, map 59, 208 và 691 ns cho $N=10^3,10^5,10^6$. Khoảng cách mở ra khi cây (48 B mỗi node, 48 MB ở $N=10^6$) không còn vừa trong cache trong khi vector (16 B mỗi mẫu) được duyệt bằng ít lần đọc bộ nhớ hơn và dễ đoán hơn.*

## Kiểm chứng

- Property test: với mọi $t_i$ đã lưu, `at(t_i)` phải bằng đúng $v_i$; với dữ liệu đơn điệu, phép nội suy phải đơn điệu.
- Đối chiếu với một oracle chậm: một cài đặt quét tuyến tính trên các truy vấn ngẫu nhiên phải cho đáp án y hệt.
- Các trường hợp biên cần test mọi lần: container rỗng, một phần tử, truy vấn trước phần tử đầu và sau phần tử cuối, key trùng, truy vấn đúng trên một key.
- Chạy dưới `-fsanitize=address,undefined` (và `-D_GLIBCXX_DEBUG` cho checked iterator) để bắt iterator ngoài phạm vi và iterator bị vô hiệu hóa.
- Vệ sinh benchmark: `-O2`, một lượt warm-up, truy vấn sinh trước khi đo, kết quả được dùng để optimizer không xóa mất vòng lặp, chạy lặp nhiều lần, báo cáo median.

## Lỗi thường gặp

| Sai lầm | Triệu chứng |
|---|---|
| `lower_bound` trên dữ liệu chưa sắp xếp | chỉ số sai một cách lặng lẽ, không có lỗi |
| Dereference `end()` hoặc `begin()-1` | crash hoặc giá trị rác (undefined behavior) |
| `erase` bên trong range-for hoặc vòng lặp iterator | bỏ sót phần tử hoặc crash; dùng `it = v.erase(it)` hoặc erase-remove |
| `remove_if` mà không có `erase` theo sau | container giữ kích thước cũ, phần đuôi chứa giá trị không xác định |
| `std::accumulate(first, last, 0)` trên double | tích lũy số nguyên: `{0.5, 0.5, 0.5}` có tổng 0 |
| `map::operator[]` trên key thiếu | chèn một giá trị mặc định (bài tập 6); dùng `find` hoặc `at` để đọc |
| Giữ một reference vào vector qua `push_back` | treo sau khi cấp phát lại |
| Benchmark bỏ kết quả | optimizer xóa công việc và báo khoảng 0 ns |
| Comparator không phải strict weak ordering (`<=`) | undefined behavior trong `sort`, `set` |

## Phương án khác và đánh đổi

- **Vector đã sắp xếp so với `map`.** Với dữ liệu xây một lần, truy vấn nhiều lần, vector đã sắp xếp thắng về tốc độ và bộ nhớ; nếu việc chèn giữa chiếm ưu thế, `map` tránh được việc dịch chuyển $O(n)$. Với vài trăm phần tử, cái nào cũng ổn và vector đơn giản hơn.
- **`unordered_map` so với các container có thứ tự.** Băm cho tra cứu chính xác kỳ vọng $O(1)$, nhưng không làm được truy vấn khoảng hoặc láng giềng gần nhất và có hành vi trường hợp xấu nhất tệ hơn với hàm băm kém.
- **`deque` so với `vector` cho FIFO.** `deque` pop từ đầu trong $O(1)$; với `vector`, pop phần tử đầu là $O(n)$ trừ khi bạn giữ một chỉ số head (một ring buffer).
- **Thuật toán so với vòng lặp viết tay.** Các thuật toán `std::` nêu rõ ý định (`count_if`, `any_of`) và đã được kiểm thử kỹ; vòng lặp viết tay vẫn ổn khi thoát sớm hoặc nhiều đầu ra làm dạng thuật toán trở nên khó hiểu.
- **Ranges và execution policy (C++20/17).** `std::ranges` cải thiện khả năng đọc và `std::execution::par` có thể song song hóa một số thuật toán, với cái giá là sự hỗ trợ của compiler và các quy tắc data race của CPP10.

## Vận dụng và ghi nhớ

Cùng các ý tưởng này xuất hiện trong NumPy (`np.searchsorted` là `lower_bound`, boolean mask là `remove_if`), trong buffer `tf2` của ROS 2 (cache có thứ tự thời gian với nội suy giữa các transform), và trong index của cơ sở dữ liệu (B-tree cho truy vấn khoảng, hash index cho so sánh bằng). Để ghi nhớ: viết lại từ trí nhớ bảng độ phức tạp của container sau ba ngày, rồi liệt kê cho dự án gần nhất của bạn container nào bạn đã dùng cho từng tập dữ liệu và thao tác chiếm ưu thế có khớp không. CPP09 tiếp nối bằng cách giải thích *vì sao* bố cục liên tục thắng trong thực tế.

## Đáp án bài tập

1. (a) `std::deque` (hoặc một ring buffer cố định): push back và pop front trong $O(1)$. (b) `std::unordered_map<int, Meta>`: tra cứu chính xác theo id nguyên, không cần thứ tự. (c) `std::set<int>` (hoặc `map` nếu có kèm payload): duy nhất và có thứ tự. (d) Một `std::vector` các mẫu sắp xếp theo thời gian với `lower_bound` (xây một lần, truy vấn nhiều); một `map` cũng được, nhưng chậm hơn và dùng nhiều bộ nhớ hơn.
2. `6 8 6`. `remove` dồn sáu phần tử được giữ `{3,4,5,9,2,6}` lên đầu và trả về iterator tại chỉ số 6, nhưng kích thước vẫn là 8 cho đến khi `erase` làm nó thành 6.
3. Tuyến tính: 1,080,000 phép so sánh. Nhị phân: $\lceil\log_2 1{,}080{,}001\rceil=21$, vì $2^{20}=1{,}048{,}576<1{,}080{,}001\le2^{21}$. Tỉ số $\approx 51{,}400$.
4. Bug 1: nếu `it == v.begin()` (truy vấn trước mẫu đầu) thì `it - 1` nằm trước phần đầu. Bug 2: nếu `it == v.end()` (truy vấn sau mẫu cuối) thì `*it` dereference `end()`. Ngoài ra, chia cho không không thể xảy ra nếu timestamp tăng nghiêm ngặt, nhưng một lần trúng chính xác với $t=t_b$ nên trả về trực tiếp. Cách sửa: kiểm tra `it == end` trước, rồi đẳng thức chính xác, rồi `it == begin`, và chỉ sau đó mới nội suy (xem `at` tham khảo).
5. `erase(it)` vô hiệu hóa `it` (và mọi iterator sau đó), nên `++it` ở lượt lặp kế là undefined behavior; ngay cả khi có vẻ chạy được, nó bỏ sót phần tử vừa trượt vào ô bị xóa. Cách sửa 1: `for (auto it = v.begin(); it != v.end();) { if (it->v > 50) it = v.erase(it); else ++it; }`. Cách sửa 2: `v.erase(std::remove_if(v.begin(), v.end(), [](const Sample& s){ return s.v > 50; }), v.end());` cũng là $O(n)$ thay vì $O(n^2)$.
6. Output `0 1`. `operator[]` default-construct và chèn key còn thiếu `"kp"`, nên một lỗi gõ tên tham số lặng lẽ trở thành gain 0 và map phình ra. Dùng `find`/`at` (sẽ throw) để đọc, và chỉ dùng `[]` khi thật sự muốn chèn.
7. `std::sort` là $O(n\log n)$ (khoảng $1001\cdot10\approx10^4$ phép so sánh), `nth_element` kỳ vọng $O(n)$ (vài nghìn). Trung vị của `{7,1,5,3,9}` nằm ở chỉ số 2 và bằng 5. Sau `nth_element` các phần tử trước đều $\le5$ và các phần tử sau đều $\ge5$, theo thứ tự không xác định; vector *không* được sắp xếp.
8. Kiểm soát: `-O2` cho tất cả; một lượt warm-up (page-in, branch predictor, cache); cùng các truy vấn ngẫu nhiên sinh sẵn cho mỗi cấu trúc; cộng dồn kết quả vào một biến được in ra để vòng lặp không bị loại bỏ; chạy lặp nhiều lần lấy median. Thứ tự kỳ vọng cho truy vấn thời gian gần nhất: `vector` nhanh nhất, `map` chậm hơn (đuổi theo con trỏ, cache miss); `unordered_map` hoàn toàn không trả lời được truy vấn thời gian gần nhất, chỉ trả lời key chính xác, nên so sánh nó chỉ hợp lệ cho tra cứu chỉ số chính xác, nơi nó nhanh nhưng trả lời một câu hỏi khác.
9. 1% của 1000 mỗi giây là 10 lần chèn muộn mỗi giây. Một lần chèn giữa dịch chuyển trung bình $n/2=50{,}000$ phần tử $\times16$ B $=800$ kB; 10 lần mỗi giây là 8 MB/s, không đáng kể. Dùng `map` là không hợp lý; hãy đo phân phối thực tế của độ trễ (các mẫu muộn chủ yếu gần cuối, nên việc dịch chuyển còn nhỏ hơn) và ngân sách độ trễ truy vấn trước khi thay đổi bất cứ thứ gì.
10. Việc cấp phát lại xảy ra khi kích thước đạt $c, gc, g^2c,\dots$ và mỗi lần copy kích thước hiện tại, nên tổng là $c+gc+\dots+g^{k}c$ với $g^{k}c\le n$. Tổng cấp số nhân tối đa là $n\cdot\frac{1}{1-1/g}=\frac{g}{g-1}n$. Với $g=1.25$: $5n$; với $g=3$: $1.5n$. $g$ rất lớn lãng phí bộ nhớ (tới $(g-1)/g$ dung lượng không dùng) và allocator có thể không tìm được khối đủ lớn; giá trị thường dùng là từ 1.5 đến 2.
11. Một câu trả lời tốt có: một bảng với ba kích thước; vector nhanh hơn map theo một tỉ số tăng dần (trong một lần chạy là 1.0, 1.7, 3.6); giải thích: binary search của vector chạm vài cache line và prefetch hoạt động, trong khi cây thăm các node rải rác trên heap; ở $10^6$ phần tử cây (khoảng 48 B/node) vượt quá cache và mỗi bước nhảy có thể là một cache miss; và một lưu ý về máy và về việc chỉ chạy một lần.

12. (a) Giả sử invariant đúng ở đầu một vòng lặp với `it = first + step` và `comp(*it, value)` sai. Khi đó `*it` không thỏa `p`, nên phần tử đầu tiên không thỏa `p` ở tại hoặc trước `it`, tức trong $[\text{first},\text{first}+\text{step}]$, và `count = step` khôi phục khẳng định (các phần tử trước `first` không đổi và vẫn thỏa `p`). Khi kết thúc `count = 0`, nên đáp án nằm trong $[\text{first},\text{first}]$: chính là `first`, phần tử đầu tiên không nhỏ hơn `value` (hoặc `last`). (b) Một phép so sánh mỗi vòng và $\text{count}'\in\{\lfloor n/2\rfloor,\; n-\lfloor n/2\rfloor-1\}$; giá trị thứ hai không lớn hơn giá trị thứ nhất, nên trường hợp xấu nhất theo $W(n)=1+W(\lfloor n/2\rfloor)$, $W(0)=0$. Viết $n$ ở dạng nhị phân, mỗi bước bỏ bit cuối, nên $W(n)$ là độ dài bit của $n$: $\lfloor\log_2 n\rfloor+1$. Giá trị: $W(1)=1$, $W(5000)=\lfloor12.29\rfloor+1=13$, $W(2^{16})=17$ (đo bằng tìm kiếm vét cạn trên mọi mục tiêu: $n=5000$ cho tốt nhất 12 và xấu nhất 13, $n=65536$ cho tốt nhất 16 và xấu nhất 17). (c) Đo được với $n\le40$: tốt nhất bằng xấu nhất đúng với $n=1,3,7,15,31$, tức $n=2^k-1$, vì khi đó cả hai nhánh để lại $2^{k-1}-1$ phần tử; $n>1$ nhỏ nhất là $3$. Với $n=5000$ trường hợp tốt nhất là 12 và xấu nhất là 13. (d) $1\,900\,000\,000+2\,000\,000\,000=3\,900\,000\,000$ vượt $2^{31}-1=2\,147\,483\,647$ và bị quấn thành $3\,900\,000\,000-2^{32}=-394\,967\,296$, một chỉ số âm. Dạng an toàn: `mid = lo + (hi - lo) / 2`, hoặc chia đôi một số lượng như vòng lặp chuẩn.
13. (a) Lấy $a=3$, $b=\text{NaN}$, $c=9$. `3 < NaN`, `NaN < 3`, `NaN < 9`, `9 < NaN` đều sai, nên $a\sim b$ và $b\sim c$ (tương đương), nhưng $3<9$ nên $a\not\sim c$. Equivalence phải bắc cầu, nên yêu cầu bị vi phạm. (b) Chỉ số đo được: $x=1\to0$, $x=3.5\to1$, $x=5\to2$, $x=7.5\to2$, $x=8.5\to2$, $x=10\to2$. Vị từ $e<x$ dọc theo vector là F F F F F với $x=1$, T F F F F với $x=3.5$ và T T F F F với $x=5$ và $x=7.5$: tất cả đều được partition, nên đáp án đúng theo định nghĩa "phần tử đầu tiên không nhỏ hơn $x$" (với $x=5$ và $x=7.5$ đó là chỉ số 2, tức NaN, dù số 7.5 ở chỉ số 3 mới là thứ bạn có thể muốn). Với $x=8.5$ vị từ là T T F T F và với $x=10$ là T T F T T: dãy không được partition, điều kiện tiên quyết bị vi phạm và giá trị 2 trả về vô nghĩa (với $x=10$ vị trí mong muốn là sau mọi số, chỉ số 5). (c) Đo được (libstdc++): $\{4,6,\text{NaN},8\}$ cho size 3 và $\{\text{NaN},4,6,8\}$ cho size 1; số chính xác phụ thuộc cài đặt vì hành vi là undefined, đó chính là điểm chính. (d) `comp(a,b) = !isnan(a) && (isnan(b) || a < b)`. Nó là thứ tự từ điển trên $(\text{isnan}(x),x)$ với `false < true`: trên các giá trị không phải NaN, `<` là thứ tự toàn phần chặt và mọi NaN tạo thành một lớp tương đương, và ghép từ điển các strict weak ordering là strict weak ordering. Kết quả đo của `std::sort` trên $\{8,\text{NaN},5,\text{NaN},6\}$: `5 6 8 nan nan`.
14. (a) Đo với libstdc++: capacity $1,2,4,8,\dots,512$ (10 lần cấp phát, tức 9 lần cấp phát lại sau lần đầu), số phần tử relocate $1+2+4+\dots+256=511$. Cận với $g=2$: $\frac{g}{g-1}n=600$; giá trị thực 511 nhỏ hơn vì khối cuối 512 chưa đầy. (b) Quy tắc: một lần chèn làm $\text{size}>\text{bucket\_count}\cdot\text{max\_load\_factor}$ kích hoạt rehash lên số bucket lớn hơn (rehash xảy ra khi số phần tử mới lớn hơn `max_load_factor()*bucket_count()` cũ, cppreference: `unordered_map::insert`). Mọi iterator bị vô hiệu hóa bởi rehash còn reference và pointer tới phần tử (`&m[0]`) vẫn hợp lệ (cùng trang). Với hệ số 0.5: lần chèn đầu làm size bằng 1 và $1>1\cdot0.5$, nên bảng tăng lên 23 bucket; rồi $12>23\cdot0.5=11.5$ cho 47, $24>47\cdot0.5=23.5$ cho 97, $49>97\cdot0.5=48.5$ cho 199 và $100>199\cdot0.5=99.5$ cho 409 (đo được: rehash ở các kích thước 1, 12, 24, 49 và 100, load factor cuối $100/409\approx0.245$). Các số bucket là số nguyên tố do thư viện chọn; tiêu chuẩn chỉ cố định quy tắc. (c) Có: `p` vẫn hợp lệ và trỏ tới `7` (`d[4]` sau ba lần chèn). Tăng ở hai đầu của `deque` không bao giờ di chuyển phần tử; iterator bị vô hiệu hóa nhưng reference thì không (đo được: `p == &d[4]`). (d) Tiêu chuẩn đảm bảo: các quy tắc vô hiệu hóa ở trên (vector cấp phát lại, rehash làm mất iterator nhưng không mất reference, chèn ở đầu deque giữ reference). Riêng thư viện: các capacity $1,2,4,\dots$ (hệ số tăng 2 trong libstdc++; thư viện khác dùng hệ số khác, ví dụ 1.5) và số bucket nguyên tố.
15. (a) Một vị trí ngẫu nhiên trong vector kích thước hiện tại $m$ dịch trung bình $m/2$ phần tử, nên khoảng $k\cdot n/2=1000\cdot50{,}000=5\cdot10^7$ phép move phần tử (trung bình là $m/2$ với $m$ tăng từ $10^5$ lên $1.01\cdot10^5$, và giá trị đo thay đổi theo lần bốc ngẫu nhiên). (b) Sắp xếp $k$ phần tử tốn $O(k\log k)\approx1000\cdot10=10^4$ phép move; nối vào cuối là $k$ phép copy; `inplace_merge` thực hiện đúng $N-1$ phép so sánh khi có buffer tạm và $O(N\log N)$ nếu không, với $N=n+k=101{,}000$, và move khoảng $N$ phần tử, nên tổng cỡ $10^5$. (c) Đo bằng kiểu phần tử đếm move: `lower_bound` + `insert` từng cái: **49,671,028** phép move phần tử; sắp xếp + nối + `inplace_merge`: **113,561** phép move (10,612 trong bước sort); tỉ lệ $\approx437$. Số đầu khớp ước lượng $5\cdot10^7$. (d) Chèn từng cái thắng khi $k$ rất nhỏ (với $k=1$ phép merge vẫn chạm tất cả $n$ phần tử, trong khi insert chạm trung bình $n/2$), hoặc khi mẫu trễ luôn ở gần cuối (độ dài dịch khi đó là độ trễ, không phải $n$): hãy đo phân bố độ trễ, tức khoảng cách từ mỗi điểm chèn tới cuối, trước khi chọn. Nếu độ trễ bị chặn bởi $L$ mẫu thì chèn từ phía sau tốn $O(kL)$.

## Đọc thêm

- [cppreference: Containers library](https://en.cppreference.com/w/cpp/container) - bảng container đầy đủ với đảm bảo độ phức tạp và quy tắc vô hiệu hóa.
- [cppreference: Algorithms library](https://en.cppreference.com/w/cpp/algorithm) - mọi thuật toán với điều kiện tiên quyết, độ phức tạp và ví dụ.
- [LearnCpp](https://www.learncpp.com/) - các chương về container, iterator và thuật toán kèm quiz.
- [cppreference: std::lower_bound](https://en.cppreference.com/w/cpp/algorithm/lower_bound), [yêu cầu Compare](https://en.cppreference.com/w/cpp/named_req/Compare) và [`std::inplace_merge`](https://en.cppreference.com/w/cpp/algorithm/inplace_merge) - điều kiện partition, strict weak ordering, và độ phức tạp của merge dùng trong các chứng minh.
- [cppreference: `std::unordered_map::insert`](https://en.cppreference.com/w/cpp/container/unordered_map/insert) - khi nào rehash làm mất hiệu lực iterator.
- Các trang cppreference dùng cho các phát biểu về độ phức tạp và vô hiệu hóa trong các ví dụ: [`std::vector::push_back`](https://en.cppreference.com/w/cpp/container/vector/push_back), [`std::vector::insert`](https://en.cppreference.com/w/cpp/container/vector/insert), [`std::remove`](https://en.cppreference.com/w/cpp/algorithm/remove), [`std::deque`](https://en.cppreference.com/w/cpp/container/deque), [`std::unordered_map`](https://en.cppreference.com/w/cpp/container/unordered_map) và [`std::map::lower_bound`](https://en.cppreference.com/w/cpp/container/map/lower_bound).

**Thực hành thêm:** các quiz ở [LearnCpp: STL containers overview](https://www.learncpp.com/cpp-tutorial/stl-containers-overview/), [iterators overview](https://www.learncpp.com/cpp-tutorial/stl-iterators-overview/) và [algorithms overview](https://www.learncpp.com/cpp-tutorial/stl-algorithms-overview/) (đáp án hiện trên mỗi trang), và các ví dụ chạy được trên cppreference cho [`std::lower_bound`](https://en.cppreference.com/w/cpp/algorithm/lower_bound) và [`std::remove`/`remove_if`](https://en.cppreference.com/w/cpp/algorithm/remove) (sửa chúng để dự đoán output), cùng [bảng vô hiệu hóa iterator](https://en.cppreference.com/w/cpp/container#Iterator_invalidation).
