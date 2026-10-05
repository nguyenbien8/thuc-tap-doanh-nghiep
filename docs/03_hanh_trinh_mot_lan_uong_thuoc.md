# 03 · Hành trình của một lần uống thuốc: từ 6 dòng log đến một thói quen

Tài liệu này theo chân **một lần uống thuốc thật** (tối 03/06/2025, resident_01) qua từng bước của pipeline. Mọi con số đều lấy từ file thật trong repo. Đọc xong bạn sẽ thấy cụ thể mỗi bước làm gì với dữ liệu.

```text
 Bước 0: 6 dòng lẫn trong 3.397 dòng thô
   │  B1.1 làm sạch
   ▼
 Bước 1: 6 dòng sạch, đúng thứ tự
   │  B1.2 gom phiên
   ▼
 Bước 2: 1 phiên "resident_01_17"
   │  B1.3 trích đặc trưng
   ▼
 Bước 3: 1 dòng trong sessions.csv
   │  B2.1 đổi sang không gian "giờ"
   ▼
 Bước 4: 1 điểm (2,305; −3,046; 0,994)
   │  B2.2 DBSCAN
   ▼
 Bước 5: thuộc cụm 5 cùng 24 phiên khác
   │  B2.3 mô tả + đếm ngày
   ▼
 Bước 6: "resident_01 · bếp · 20:32 · 25/28 ngày" → thói quen
```

---

## Bước 0 – Dữ liệu thô

Trong `data/raw/smart_home_events.csv` có 6 dòng thuộc lần uống thuốc này, **nằm rải rác** trong file vì toàn bộ file đã bị xáo trộn (giống log gom từ nhiều thiết bị). Khi lọc ra và sắp xếp lại:

```csv
timestamp,resident_id,room,sensor_type,sensor_id,value,event_type,activity_label
2025-06-03 20:28:26,resident_01,kitchen,motion,kitchen_motion,1.00,motion,take_medicine
2025-06-03 20:28:56,resident_01,kitchen,door,kitchen_door,1.00,open,take_medicine
2025-06-03 20:29:26,resident_01,kitchen,temperature,kitchen_temperature,22.48,reading,take_medicine
2025-06-03 20:29:56,resident_01,kitchen,light,kitchen_light,333.38,reading,take_medicine
2025-06-03 20:30:26,resident_01,kitchen,pillbox,kitchen_pillbox,1.00,open,take_medicine
2025-06-03 20:31:24,resident_01,kitchen,motion,kitchen_motion,1.00,motion,take_medicine
```

Thuật toán **không được nhìn** cột cuối `take_medicine`. Với nó, đây chỉ là "6 lần cảm biến kêu ở bếp lúc hơn 20:28".

## Bước 1 – Làm sạch (`clean_events`)

Các dòng này vốn "sạch", nên bước làm sạch chỉ **sắp xếp** chúng về đúng thứ tự theo `resident_id` → `timestamp`. Nếu một trong 6 dòng có tên phòng là `" Kitchen "`, nó sẽ được chuẩn hoá thành `kitchen` và vẫn thuộc cùng phiên. Nếu dòng `temperature` bị thiếu giá trị, nó được điền median nhiệt độ của toàn bộ dữ liệu.

## Bước 2 – Gom phiên (`create_sessions`)

Xét các sự kiện của resident_01 theo thứ tự thời gian:

| Phiên | Bắt đầu → kết thúc | Phòng | Vì sao tách |
|---|---|---|---|
| resident_01_16 | 18:25:00 → 18:52:37 | kitchen | bữa tối |
| **resident_01_17** | **20:28:26 → 20:31:24** | **kitchen** | cách sự kiện trước (18:52:37) **96 phút > 30 phút** → phiên mới |
| resident_01_18 | 21:26:33 → 21:30:33 | living_room | cách 55 phút **và** khác phòng → phiên mới |

Dù bữa tối và uống thuốc đều ở bếp, chúng **thành hai phiên riêng** nhờ khoảng lặng 96 phút. Cả 6 dòng được gán `session_id = 17`, `session_key = resident_01_17` trong `clean_events.csv`.

## Bước 3 – Trích đặc trưng (`build_session_features`)

6 dòng gộp thành **1 dòng** trong `data/processed/demo/sessions.csv`:

| Cột | Giá trị | Tính thế nào |
|---|---|---|
| `start_time` → `end_time` | 20:28:26 → 20:31:24 | sự kiện đầu, sự kiện cuối |
| `duration_minutes` | 2,97 | 20:31:24 − 20:28:26 |
| `event_count` | 6 | số dòng |
| `dominant_room` | kitchen | phòng xuất hiện nhiều nhất |
| `sensor_types` | door\|light\|motion\|**pillbox**\|temperature | các loại cảm biến, sắp theo abc |
| `start_hour` | 20,4739 | 20 + 28/60 + 26/3600 |
| `date` | 2025-06-03 | để sau này đếm số ngày |
| `activity_label` | take_medicine | chỉ để chấm điểm |

## Bước 4 – Đổi sang không gian "giờ" (`habit_feature_matrix`)

Phiên được biến thành một điểm 3 chiều. Tính tay:

```text
θ = 2π × 20,4739 / 24  = 5,360 rad         (góc trên mặt đồng hồ 24h)
R = 24 / 2π            = 3,820             (bán kính để chu vi đúng 24 "giờ")

x = R · cos θ          = 3,820 × 0,603  =  2,305
y = R · sin θ          = 3,820 × (−0,797) = −3,046
z = 0,5 · log2(1 + 2,97) = 0,5 × 1,988   =  0,994
```

→ điểm **(2,305; −3,046; 0,994)**.

So sánh với bữa tối cùng ngày (18:25, 27,6 phút) → điểm (0,416; −3,797; 2,419). **Khoảng cách giữa hai điểm = 2,48** "giờ". Số này gồm khoảng 2,06 giờ chênh lệch giờ bắt đầu, cộng phần chênh lệch thời lượng (3 phút so với 28 phút, tức gấp khoảng 7 lần). Khoảng cách này lớn hơn rất nhiều so với `eps = 0,5`, nên hai phiên không thể chung cụm.

## Bước 5 – DBSCAN (`discover_patterns`)

DBSCAN chạy riêng trên **nhóm (resident_01, kitchen)**, gồm 109 phiên (các bữa ăn, các lần uống thuốc, vài phiên lẻ).

- `min_samples` = max(5, ⌈0,2 × 28 ngày⌉) = **6**.
- Trong bán kính 0,5 quanh phiên này có **25 phiên** (kể cả chính nó). Các phiên gần nhất cách chỉ 0,04; 0,05; 0,06; 0,07; 0,08.
- 25 ≥ 6 → đây là **điểm lõi**. Các lần uống thuốc của những ngày khác cũng là điểm lõi và nối với nhau thành một cụm.

Cụm này gồm 25 phiên, giờ bắt đầu trải từ 20,28 đến 20,77 (tức 20:17 → 20:46). Sau khi đánh số lại theo thứ tự (người → phòng → giờ), cụm mang số **5**:

| Số cụm | resident_01 · … |
|---:|---|
| 0 | bedroom 06:42 |
| 1 | bedroom 22:31 |
| 2 | kitchen 07:33 |
| 3 | kitchen 12:03 |
| 4 | kitchen 18:33 |
| **5** | **kitchen 20:32** |
| … | … |

**Một phiên bị gán nhiễu trông thế nào?** Cũng trong nhóm bếp của resident_01, có 3 phiên nhiễu, đều thuộc bữa sáng ngày 08/06 (07:29, 07:40, 07:45; dài 5, 0 và 3,5 phút). Bữa sáng hôm đó bị cắt vụn thành 3 mảnh ngắn, có lẽ vì một lần đi ngang ngẫu nhiên sang phòng khác xen vào giữa. Mỗi mảnh quá ngắn so với các bữa sáng bình thường (~20 phút), nên không có đủ 6 láng giềng và bị gán −1. Đây đúng là hành vi "khác thường" mà ta muốn tách ra.

## Bước 6 – Mô tả và kiểm tra tần suất (`build_profiles`)

25 phiên của cụm 5 rơi vào **25 ngày khác nhau** trong 28 ngày quan sát:

```text
support = 25 / 28 = 0,893 ≥ min_support 0,5  →  is_habit = True
```

Dòng kết quả trong `reports/results/demo/habits.csv`:

```text
cluster=5 · resident_01 · kitchen · typical_start 20:32 · window 20:20–20:40
start_std 7,7 phút · median_duration 2,6 phút · 25/28 ngày · support 0,893 · is_habit True
sensor_types door|light|motion|pillbox|temperature
dominant_label take_medicine · label_purity 1,0    ← chỉ để chấm điểm
```

Đọc thành câu: ***resident_01 có thói quen ở bếp khoảng 20:32 (thường trong 20:20–20:40), mỗi lần chừng 3 phút, 25/28 ngày, luôn kèm cảm biến hộp thuốc*** → thói quen uống thuốc buổi tối.

Cột nhãn xác nhận: 100% phiên trong cụm đúng là `take_medicine`, và 25/28 ≈ 89% khớp với xác suất 85% đã cài trong bộ sinh dữ liệu.

---

## Tự làm lại hành trình này

```powershell
python -c "import pandas as pd; s=pd.read_csv('data/processed/demo/sessions.csv'); print(s[s.session_key=='resident_01_17'].T)"
python -c "import pandas as pd; h=pd.read_csv('reports/results/demo/habits.csv'); print(h[h.cluster==5].T)"
```

Hãy thử lặp lại hành trình với một phiên khác, ví dụ bữa trưa hoặc một lần `random_visit`, để tự kiểm tra mình đã hiểu.
