# 04 · Vì sao làm thế này mà không làm cách khác

Mỗi mục dưới đây là **một quyết định thiết kế**, trình bày theo cùng khuôn:

- **Quyết định:** đề tài chọn gì.
- **Các cách khác đã cân nhắc:** và vì sao không chọn.
- **Cái giá phải trả:** mọi lựa chọn đều đánh đổi một thứ gì đó. Biết điểm yếu của chính mình là cách tốt nhất để trả lời phản biện.

Các quyết định được sắp theo đúng thứ tự của pipeline.

---

## Phần A · Phạm vi

### A1. Chỉ làm 2 bước, chỉ dùng 1 kỹ thuật

- **Quyết định:** B1 tiền xử lý → B2 định nghĩa mẫu + tìm bằng DBSCAN. Không làm robot, nhắc nhở hay dự đoán.
- **Vì sao:** đúng yêu cầu đề bài: *"chọn 1 phương pháp tương ứng với 1 kĩ thuật hiểu được, trình bày được, thực nghiệm được là hoàn thành"*, và *"chỉ cần tìm ra các mẫu"*.
- **Lưu ý:** trong repo có một phương pháp thứ hai là *baseline* (`experiments.py`). Đó **không phải** kỹ thuật thứ hai của đề tài mà là thước đo để so sánh; nó cũng là DBSCAN, chỉ khác cách biểu diễn dữ liệu.

---

## Phần B · Bước 1: tiền xử lý

### B1. Đơn vị quan sát là "phiên", không phải từng dòng log

- **Quyết định:** gom các sự kiện thành **phiên** = một lần một người ở liên tục trong một phòng.
- **Các cách khác:**

| Cách | Vì sao không |
|---|---|
| Phân cụm từng dòng log | Một bữa tối sinh ~10 dòng; phân cụm từng dòng sẽ ra cụm "các lần cảm biến chuyển động ở bếp", không phải "bữa tối". Dòng log là *triệu chứng*, không phải *hành động* |
| Cửa sổ cố định (mỗi 15 phút, mỗi giờ) | Cắt ngang hoạt động: bữa trưa 11:45–12:30 bị chia vào hai cửa sổ. Hoạt động 3 phút (uống thuốc) chìm trong cửa sổ 1 giờ |
| Mỗi ngày là một quan sát | Chỉ trả lời được "ngày này giống ngày kia không", không trả lời được "lúc mấy giờ làm gì" |

- **Cái giá:** một hoạt động bị gián đoạn (ra hành lang rồi quay lại) sẽ bị cắt thành nhiều phiên nhỏ. Ví dụ: bữa sáng 08/06 của resident_01 bị cắt làm 3 mảnh và bị gán nhiễu; giấc ngủ Aruba bị tách làm 2 mẫu vì dậy đi vệ sinh.

### B2. Mở phiên mới khi lặng > 30 phút HOẶC đổi phòng

- **Quyết định:** dùng cả hai quy tắc (`inactivity_gap_minutes: 30`, `split_on_room_change: true`).
- **Vì sao cần quy tắc "lặng":** giữa hai hoạt động ở *cùng một phòng* (bữa tối 18:30 và uống thuốc 20:30 đều ở bếp) chỉ có khoảng lặng là ranh giới.
- **Vì sao cần quy tắc "đổi phòng":**
  1. Thói quen gắn với địa điểm (uống thuốc *ở bếp*). Không tách thì "ngủ dậy ở phòng ngủ → 10 phút sau ăn sáng ở bếp" thành một phiên lai.
  2. **Với Aruba đây là quy tắc duy nhất hoạt động được**: dữ liệu có mỗi phút một dòng nên không bao giờ có khoảng lặng 30 phút. Thí nghiệm *ablation* chứng minh: bỏ quy tắc này thì cả 112 ngày thành **1 phiên** và không tìm ra gì.
- **Vì sao 30 phút?** Đủ dài để một hoạt động có những quãng yên lặng bên trong (ngồi ăn không cử động mạnh) mà không bị cắt; đủ ngắn để hai hoạt động cách nhau hơn nửa tiếng được tách riêng. Đây là giá trị hay gặp trong các nghiên cứu nhà thông minh, và nó là tham số trong config, đổi được.
- **Cái giá:** với cảm biến chỉ kêu khi có chuyển động, người ngồi đọc sách bất động hơn 30 phút sẽ bị cắt phiên.

### B3. Bỏ phiên ngắn hơn 5 phút (chỉ với Aruba)

- **Quyết định:** `min_session_minutes: 5` cho Aruba, `0` cho dữ liệu mô phỏng.
- **Vì sao khác nhau:** Aruba có 80% phiên dưới 5 phút, phần lớn là đi ngang hành lang; giữ lại chúng chỉ làm loãng dữ liệu. Với dữ liệu mô phỏng, đề tài *cố ý* giữ lại các lần đi ngang ngẫu nhiên để kiểm tra DBSCAN có tự đánh dấu chúng là nhiễu không (kết quả: 164/164).
- **Cái giá:** mất các thói quen rất ngắn trên Aruba (ví dụ uống một cốc nước ở bếp trong 2 phút).

### B4. Điền giá trị thiếu bằng median *theo loại cảm biến*

- **Các cách khác:** bỏ dòng (mất dữ liệu); điền 0 (0 °C là nhiệt độ có thật); điền median toàn bộ (trộn nhiệt độ ≈ 23 với ánh sáng ≈ 300 → ra con số vô nghĩa).
- **Cái giá:** không có đáng kể; phương pháp chính cũng không dùng giá trị `value`.

---

## Phần C · Bước 2: định nghĩa mẫu

### C1. Thói quen = cùng người · cùng phòng · cùng giờ · cùng thời lượng · ≥ 50% số ngày

- **Vì sao định nghĩa như vậy:** đề bài yêu cầu tìm *"hành động thường xuyên hay tuần hoàn"*, ví dụ *"khoảng thời gian này người ta hay uống thuốc"*. Mỗi thành phần của định nghĩa tương ứng một ý:
  - *cùng giờ* → **tuần hoàn** theo ngày;
  - *≥ 50% số ngày* → **thường xuyên**;
  - *cùng phòng, cùng thời lượng* → **cùng một hành động**;
  - *cùng người* → thói quen là **cá nhân**.
- **Các định nghĩa khác:**

| Định nghĩa khác | Vì sao không chọn |
|---|---|
| Chuỗi hành động hay lặp lại (A → B → C) | Là bài toán khai phá chuỗi (sequence mining), trả lời "sau khi làm A thì làm gì", không trả lời được "lúc mấy giờ". Là hướng mở rộng |
| Tập cảm biến hay kích hoạt cùng nhau (itemset) | Không có trục thời gian; không đọc được thành câu dễ hiểu |
| Cụm phiên bất kỳ | Không phân biệt được "thỉnh thoảng" với "thường xuyên": tập thể dục 30% số ngày cũng sẽ thành thói quen |

- **Cái giá:** chưa bắt được thói quen theo tuần ("thứ Bảy nào cũng đi chợ"); các mẫu như vậy chỉ hiện ra dưới dạng *mẫu không thường xuyên*.

### C2. Ngưỡng 50% số ngày được kiểm tra *sau* DBSCAN

- **Vì sao không để DBSCAN tự lo?** DBSCAN đếm *số phiên* gần nhau, không đếm *số ngày*. Nếu một người vào bếp 5 lần lúc 15:00 chỉ trong một ngày, DBSCAN có thể coi đó là "dày", nhưng đó không phải thói quen. Đếm số ngày khác nhau (`date.nunique()`) mới đúng nghĩa "lặp lại".
- **Lợi ích phụ:** cụm không đạt ngưỡng vẫn được giữ lại và báo cáo là **mẫu không thường xuyên** (tập thể dục, lịch cuối tuần), vốn là thông tin có giá trị.

---

## Phần D · Bước 2: kỹ thuật

### D1. DBSCAN, không phải thuật toán khác

| Thuật toán | Vì sao không chọn |
|---|---|
| **K-Means** | Phải biết trước số thói quen *k*, điều không thể biết với một người lạ. Ép mọi phiên, kể cả đi ngang ngẫu nhiên, vào một cụm; không có khái niệm nhiễu |
| **GMM** (hỗn hợp Gauss) | Cũng cần *k*; giả định cụm hình elip; khó giải thích bằng lời hơn |
| **Phân cụm phân cấp** | Phải chọn ngưỡng cắt cây; không có nhiễu; chậm với 15.000 phiên |
| **HDBSCAN** | Rất phù hợp, thậm chí khắc phục được điểm yếu của DBSCAN (mục D6). Nhưng khó giải thích hơn (cây mật độ, độ bền cụm) và mất ý nghĩa trực quan của `eps`. Được ghi làm **hướng phát triển** |
| **LDA** (như bài báo tham khảo) | Hợp với dữ liệu dạng "túi từ" (quan hệ định tính, không có trục giờ rõ). Dữ liệu nhà thông minh có trục giờ tự nhiên; câu hỏi là "mấy giờ" nên phân cụm trên trục thời gian trả lời trực tiếp hơn |
| **HMM**, mạng nơ-ron | Mô hình hoá chuỗi hoặc cần nhiều dữ liệu và nhãn; vượt yêu cầu "hiểu được, trình bày được" |

**Vì sao chọn DBSCAN:** (1) không cần biết trước số thói quen; (2) tự đánh dấu nhiễu, đúng thứ cần để loại hành vi ngẫu nhiên; (3) **hai tham số của nó trùng với định nghĩa thói quen**: `eps` = "lệch bao nhiêu phút vẫn tính là cùng giờ", `min_samples` = "cần lặp lại bao nhiêu lần"; (4) thuật toán đơn giản, vẽ được trên bảng trắng.

### D2. Chỉ dùng giờ bắt đầu + thời lượng, không dùng mọi đặc trưng

- **Đây là bài học rút ra từ chính lịch sử của repo.** Phiên bản đầu tiên chuẩn hoá 10 đặc trưng (số sự kiện, số cảm biến, nhiệt độ, ánh sáng, giờ...) rồi đưa hết vào DBSCAN. Kết quả:
  - bữa sáng của **hai người** và bữa trưa bị gộp làm một cụm;
  - 164 lần đi ngang ngẫu nhiên bị gom thành một "thói quen" giả;
  - độ lệch giờ trong cụm là **3 giờ**, tức là không trả lời được "lúc mấy giờ".
- **Nguyên nhân:** 8/10 đặc trưng gần như giống nhau giữa các bữa ăn (cùng số cảm biến, cùng nhiệt độ bếp), còn giờ chỉ chiếm 2/10 chiều nên bị lấn át. Trong khoảng cách Euclid, **thêm đặc trưng không liên quan không vô hại, mà làm loãng đặc trưng quan trọng**.
- **Cách mới:** chỉ giữ thứ định nghĩa thói quen cần (giờ và thời lượng); còn phòng được dùng để **chia nhóm** (mục D5). Các đặc trưng khác vẫn được tính, nhưng chỉ để diễn giải (ví dụ `sensor_types` có `pillbox`).
- **Kết quả:** độ lệch giờ trong cụm giảm từ 182 xuống 10 phút; ARI tăng từ 0,55 lên 0,96.
- **Cái giá:** hai hoạt động khác nhau ở cùng phòng, cùng giờ, cùng thời lượng sẽ không phân biệt được.

### D3. Giờ đặt trên vòng tròn, bán kính R = 24/2π

- **Vấn đề:** giờ là đại lượng tuần hoàn. 23:50 và 00:10 cách nhau 20 phút, nhưng nếu dùng số thực (23,83 và 0,17) thì cách nhau 23,7 giờ. Thói quen đi ngủ quanh nửa đêm (Aruba ~00:18) sẽ bị xé làm hai cụm ở hai đầu trục.
- **Cách giải quyết phổ biến:** mã hoá `(sin, cos)` trên vòng tròn bán kính 1. Khi đó khoảng cách không có đơn vị dễ hiểu.
- **Cải tiến của đề tài:** chọn bán kính **R = 24/2π** để chu vi vòng tròn đúng bằng 24. Khi đó khoảng cách giữa hai điểm **xấp xỉ bằng số giờ chênh lệch** (lệch 30 phút → khoảng cách 0,4996). Nhờ vậy `eps = 0,5` có nghĩa đen là "30 phút".
- **Cái giá:** với chênh lệch rất lớn (vài giờ) thì khoảng cách dây cung hơi nhỏ hơn cung tròn (lệch 12 giờ → 7,6 thay vì 12), nhưng ở quy mô `eps` (30 phút) sai số không đáng kể.

### D4. Không dùng StandardScaler

- **Vì sao:** mọi trục đã cùng đơn vị "giờ". Chuẩn hoá sẽ co giãn mỗi trục theo độ phân tán của dữ liệu và phá mất ý nghĩa `eps = 30 phút`. StandardScaler cần khi các cột khác đơn vị (lux với phút), nhưng ở đây điều đó không xảy ra.

### D5. Thời lượng dùng thang log, trọng số 0,5

- **Vì sao log:** khác biệt 3 phút với 6 phút (uống thuốc với nấu nhanh) quan trọng hơn khác biệt 300 với 306 phút (hai đêm ngủ). Thang log đo *tỷ lệ* thay vì *hiệu số*.
- **Vì sao trọng số 0,5:** *thời lượng gấp đôi tương đương lệch 30 phút giờ bắt đầu*. Nó đủ để tách uống thuốc (3 phút) khỏi bữa tối (30 phút), nhưng không đến mức một bữa ăn dài hơn bình thường bị văng khỏi cụm.
- **Cái giá:** là một tham số chọn theo cảm nhận; bảng độ nhạy chưa quét tham số này.

### D6. Chạy DBSCAN riêng cho từng (người, phòng)

- **Cách khác:** đưa phòng vào như một đặc trưng one-hot trong cùng không gian. Nhưng khi đó phải chọn "khác phòng thì cách bao nhiêu giờ", một con số vô nghĩa.
- **Vì sao chia nhóm:** thói quen là cá nhân và gắn địa điểm; chia nhóm là cách nói thẳng điều đó, không cần con số tuỳ ý. Nó còn chạy nhanh hơn vì mỗi nhóm nhỏ.
- **Cái giá:** không tìm được thói quen trải qua nhiều phòng (ví dụ "đi vòng quanh nhà mỗi tối").

### D7. `min_samples` tăng theo số ngày

- **Quyết định:** `min_samples = max(5, ⌈0,2 × số ngày⌉)` → 28 ngày: 6; 112 ngày: 23.
- **Vì sao:** với 112 ngày, 5 phiên trùng giờ hoàn toàn có thể là ngẫu nhiên. Yêu cầu theo *tỷ lệ số ngày* giữ nguyên ý nghĩa "đủ thường xuyên để là một vùng dày", dù dữ liệu dài hay ngắn.
- **Cái giá:** với dữ liệu rất ngắn (vài ngày), sàn 5 là cứng; khi đó phương pháp thận trọng và dễ báo "không có thói quen".

### D8. eps = 0,5 giờ, chọn theo ý nghĩa, không tinh chỉnh theo nhãn

- **Vì sao không dò eps cho ARI cao nhất?** Vì như thế là **dùng nhãn để học**, biến bài toán thành có giám sát và kết quả tự đề cao chính nó. Trong thực tế không có nhãn để dò.
- **Kiểm tra lại lựa chọn** bằng hai công cụ không cần nhãn và một công cụ có nhãn:
  - biểu đồ k-distance: 0,5 nằm trước điểm gãy;
  - bảng độ nhạy: eps 0,25 → gần như tất cả thành nhiễu; eps ≥ 0,75 → cụm nối dài hơn 3 giờ;
  - độ thuần giữ ổn định 0,77–0,81 với mọi cấu hình, tức là lựa chọn không phải may mắn.
- **Điểm yếu đã biết:** một `eps` chung cho mọi phòng. Phòng khách Aruba được dùng liên tục cả chiều tối nên các phiên nối nhau thành một cụm dài 14:19–22:20 (hiện tượng *chaining*). HDBSCAN là hướng khắc phục.

### D9. Giờ điển hình tính bằng *trung bình vòng tròn*

- **Vì sao:** trung bình thường của 23:30 và 00:30 là 12:00, sai hoàn toàn. Trung bình vòng tròn (`atan2` của trung bình sin và cos) cho 00:00, đúng. Khung giờ được báo bằng phân vị 10–90% của độ lệch quanh giờ điển hình, nên không bị méo bởi vài lần bất thường.

---

## Phần E · Đánh giá

### E1. Đánh giá bằng nhiều loại chỉ số

| Chỉ số | Trả lời câu hỏi | Vì sao cần |
|---|---|---|
| Silhouette **trong từng phòng** | Các cụm có tách biệt không? | Không cần nhãn. Tính trong từng phòng vì silhouette toàn cục sẽ bị thổi phồng: các phòng vốn đã bị chia riêng |
| **Độ lệch giờ trong cụm** | Cụm có trả lời được "mấy giờ" không? | Đây là chỉ số gắn trực tiếp với mục tiêu đề tài; chỉ số này làm lộ ra baseline thất bại |
| ARI, NMI, độ thuần | Cụm có trùng với hoạt động thật không? | Cần nhãn, nên chỉ dùng để chấm điểm |
| Số thói quen, tỷ lệ nhiễu | Kết quả có dùng được không? | Góc nhìn thực tế |

Tỷ lệ nhiễu thấp **không** tự động là tốt: baseline có nhiễu 5% vì nó gom nhiễu thành một cụm giả.

### E2. Baseline, ablation, độ nhạy

| Thí nghiệm | Mục đích |
|---|---|
| **Baseline** (cách làm ban đầu) | Chứng minh cách biểu diễn mới thực sự tốt hơn, không phải chỉ "trông hợp lý" |
| **Ablation** (bỏ tách phiên theo phòng) | Chứng minh từng thành phần đều cần thiết |
| **Độ nhạy** (lưới eps × tỷ lệ) | Chứng minh kết quả không phụ thuộc vào một tham số may mắn |

Bộ ba này là cách làm chuẩn khi viết báo cáo khoa học; hội đồng thường hỏi *"so với cái gì?"* và *"nếu đổi tham số thì sao?"*.

---

## Phần F · Kỹ thuật phần mềm

| Quyết định | Vì sao |
|---|---|
| Tham số nằm trong **YAML**, không viết cứng trong code | Đổi thí nghiệm không phải sửa code; một file config = một thí nghiệm có thể tái lập |
| Lệnh CLI `smart-home` | Mỗi bước chạy bằng một lệnh; người chấm tái lập được |
| **Seed cố định** cho dữ liệu mô phỏng | Chạy lại ra đúng từng con số trong báo cáo |
| **21 kiểm thử** | Bảo đảm sửa code không làm hỏng kết quả; có test cho các trường hợp khó (qua nửa đêm, không có cụm nào, mã phòng STRANDS) |
| Commit `reports/results/`, không commit `data/` | Người chấm xem được kết quả ngay; dữ liệu thì sinh lại hoặc tải lại được (và STRANDS có điều kiện sử dụng riêng) |
| Adapter riêng cho STRANDS | Thêm nguồn dữ liệu mới không phải sửa thuật toán |
| Báo cáo `habit_report.md` sinh tự động | Số liệu trong báo cáo không bao giờ lệch với số liệu thật |
