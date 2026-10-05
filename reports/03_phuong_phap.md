# 3. Phương pháp

```text
 Sự kiện thô ──B1.1 Làm sạch──► Sự kiện sạch ──B1.2 Gom phiên──► Phiên ──B1.3 Đặc trưng──► Bảng phiên
                                                                                              │
     Báo cáo thói quen ◄──B2.3 Mô tả & lọc tần suất── Cụm ◄──B2.2 DBSCAN theo (người, phòng)──┘
                                                                  ▲
                                                   B2.1 Không gian "giờ"
```

| Bước | Mã nguồn | Hàm chính |
|---|---|---|
| B1 – Tiền xử lý | [preprocessing.py](../src/smart_home_patterns/preprocessing.py) | `clean_events`, `create_sessions`, `build_session_features`, `preprocess` |
| B2 – Tìm thói quen | [discovery.py](../src/smart_home_patterns/discovery.py) | `habit_feature_matrix`, `discover_patterns`, `build_profiles` |
| Điều phối, báo cáo, hình | [pipeline.py](../src/smart_home_patterns/pipeline.py), [plots.py](../src/smart_home_patterns/plots.py) | `run_pipeline` |
| So sánh, độ nhạy | [experiments.py](../src/smart_home_patterns/experiments.py) | `run_experiments` |

---

## B1. Tiền xử lý dữ liệu

### B1.1. Làm sạch (`clean_events`)

| # | Thao tác | Lý do |
|---|---|---|
| 1 | Kiểm tra đủ 7 cột bắt buộc, thiếu thì báo lỗi ngay | Lỗi schema phải lộ ra sớm thay vì sinh kết quả sai âm thầm |
| 2 | Ép `timestamp` → datetime, `value` → số; giá trị hỏng thành NaT/NaN | Không để một dòng hỏng làm dừng cả pipeline |
| 3 | Bỏ dòng thiếu quá 40% số ô | Dòng quá hỏng không còn thông tin |
| 4 | Bỏ dòng thiếu thời gian, người, phòng, cảm biến hoặc loại sự kiện | Không xác định được *ai – ở đâu – lúc nào* thì không dùng được |
| 5 | Cắt khoảng trắng, đưa về chữ thường | `" Kitchen "` và `kitchen` phải là một phòng |
| 6 | Điền `value` thiếu bằng median **theo loại cảm biến** | Không lấy median chung, vì nhiệt độ (≈23) và ánh sáng (≈300) khác thang đo |
| 7 | Bỏ dòng trùng, sắp xếp theo người → thời gian | Gói tin gửi lặp là lỗi phổ biến của IoT; gom phiên cần đúng thứ tự |

### B1.2. Gom sự kiện thành phiên (`create_sessions`)

Một dòng log không phải là một hành động. Đơn vị quan sát được chọn là **phiên**: *một lần một người ở liên tục trong một phòng*. Với mỗi người, sự kiện thứ *i* mở phiên mới khi:

$$\Delta t_i = t_i - t_{i-1} > G \quad\text{hoặc}\quad \text{room}_i \neq \text{room}_{i-1}$$

với $G$ = `inactivity_gap_minutes` = 30 phút.

- **Tách theo khoảng lặng** thay vì cắt cửa sổ cố định (ví dụ mỗi giờ): cửa sổ cố định sẽ cắt đôi bữa trưa 11:45–12:30.
- **Tách khi đổi phòng**: thói quen gắn với địa điểm (uống thuốc *ở bếp*); không tách thì "ngủ dậy ở phòng ngủ rồi sang bếp ăn sáng" bị gộp thành một phiên lai. Với dữ liệu theo phút như Aruba (không bao giờ có khoảng lặng), đây là cách tách **duy nhất** — thí nghiệm ablation ở [04](04_ket_qua_thuc_nghiem.md) cho thấy bỏ quy tắc này thì cả 112 ngày thành một phiên.
- **Lọc phiên quá ngắn** (`min_session_minutes`): với Aruba đặt 5 phút để bỏ các lần đi ngang hành lang; với dữ liệu mô phỏng đặt 0 để các lần đi ngang ngẫu nhiên đi tiếp vào B2 và bị đánh dấu nhiễu (kiểm tra khả năng lọc nhiễu).

### B1.3. Đặc trưng của phiên (`build_session_features`)

| Nhóm | Đặc trưng | Dùng cho |
|---|---|---|
| **Thời gian** | `start_hour` (giờ thập phân), `duration_minutes`, `hour_sin`, `hour_cos` | **Phân cụm (B2)** |
| **Ngữ cảnh** | `resident_id`, `dominant_room` | **Chia nhóm trước khi phân cụm** |
| Mô tả | `event_count`, `unique_sensors`, `sensor_types`, `motion_count`, `door_count`, `temperature_mean`, `light_mean` | Diễn giải cụm, baseline |
| Lịch | `date`, `weekday` | Đếm số ngày xuất hiện (tần suất) |
| Đánh giá | `activity_label` (nhãn chiếm đa số trong phiên) | **Chỉ để chấm điểm** |

Phiên không có cảm biến nhiệt độ/ánh sáng được điền **giá trị trung bình của toàn bộ dữ liệu**, không điền 0 — vì 0 °C hay 0 lux là giá trị vật lý có thật và sẽ làm sai lệch khoảng cách.

---

## B2. Định nghĩa mẫu và tìm mẫu bằng DBSCAN

### B2.1. Không gian đặc trưng đo bằng "giờ" (`habit_feature_matrix`)

Mỗi phiên được biến thành một điểm 3 chiều:

$$
\mathbf{x} = \Big(\; R\cos\theta,\;\; R\sin\theta,\;\; w\cdot\log_2(1 + d)\;\Big),
\qquad \theta = \frac{2\pi h}{24},\quad R = \frac{24}{2\pi}
$$

với $h$ = giờ bắt đầu, $d$ = thời lượng (phút), $w$ = `duration_weight` = 0,5.

**Vì sao dạng này?**

1. **Giờ là đại lượng vòng tròn.** 23:50 và 00:10 chỉ cách nhau 20 phút, nhưng nếu dùng số thực 23,83 và 0,17 thì cách nhau 23,7 giờ. Đặt giờ lên vòng tròn giải quyết điều này (điều quan trọng với thói quen *đi ngủ* — Aruba ngủ lúc ~00:18).
2. **Chọn bán kính $R = 24/2\pi$** (chu vi đúng 24) khiến khoảng cách Euclid giữa hai điểm **xấp xỉ đúng số giờ** giữa hai thời điểm: lệch 30 phút → khoảng cách 0,4996. Mọi trục đều có đơn vị giờ, **không cần chuẩn hoá (StandardScaler)** và tham số `eps` đọc được bằng lời.
3. **Thời lượng dùng thang log.** 3 phút và 6 phút khác nhau nhiều về bản chất (uống thuốc vs. nấu nhanh), 300 và 306 phút thì không. Với $w = 0{,}5$: *thời lượng gấp đôi tương đương lệch 30 phút giờ bắt đầu*.

### B2.2. DBSCAN theo từng người × từng phòng (`discover_patterns`)

Phiên được chia nhóm theo `(resident_id, dominant_room)`, rồi chạy DBSCAN độc lập trong từng nhóm. Lý do: thói quen là **cá nhân** và **gắn với địa điểm**; hai người cùng ăn tối lúc 19:00 là hai thói quen khác nhau; ở bếp lúc 20:30 và ở phòng khách lúc 20:30 cũng vậy.

**Nhắc lại DBSCAN** (Ester et al., 1996). Với bán kính `eps` và ngưỡng `min_samples`:
- điểm **lõi**: có ≥ `min_samples` điểm (tính cả chính nó) trong bán kính `eps`;
- **cụm** = tập các điểm lõi nối với nhau qua các lân cận, cộng các điểm biên nằm trong lân cận của chúng;
- điểm không thuộc cụm nào = **nhiễu**, nhãn `−1`.

**Tham số và ý nghĩa**

| Tham số | Giá trị | Ý nghĩa bằng lời |
|---|---|---|
| `eps_hours` | 0,5 | Hai phiên "cùng khung giờ" nếu bắt đầu lệch nhau khoảng ≤ 30 phút |
| `min_samples` | $\max\big(5,\ \lceil 0{,}2 \times \text{số ngày}\rceil\big)$ | Một khung giờ chỉ "dày" nếu có phiên từ ít nhất ~20% số ngày; 28 ngày → 6, 112 ngày → 23 |
| `duration_weight` | 0,5 | Thời lượng gấp đôi = lệch 30 phút |
| `min_support` | 0,5 | Cụm là **thói quen** nếu xuất hiện ở ≥ 50% số ngày |

`min_samples` **tăng theo độ dài dữ liệu** vì với 112 ngày, 5 lần trùng giờ hoàn toàn có thể là ngẫu nhiên; yêu cầu tỷ lệ theo số ngày giữ nguyên nghĩa "lặp lại thường xuyên" dù dữ liệu dài hay ngắn.

Các tham số được chọn **theo ý nghĩa**, không tinh chỉnh theo nhãn thật (tinh chỉnh theo nhãn sẽ biến bài toán thành có giám sát). Biểu đồ k-distance (`figures/k_distance.png`) và bảng độ nhạy ở [04](04_ket_qua_thuc_nghiem.md) dùng để kiểm tra lựa chọn này.

**Giả mã**

```text
for mỗi nhóm (người p, phòng r):
    k ← max(min_samples, ceil(ratio × số_ngày(p)))
    if số phiên < k: mọi phiên của nhóm là nhiễu; continue
    X ← habit_feature_matrix(các phiên của nhóm)
    nhãn ← DBSCAN(eps, k).fit_predict(X)
    đánh số cụm toàn cục, sắp theo (người, phòng, giờ điển hình)
for mỗi cụm c:
    tần_suất(c) ← số ngày khác nhau có phiên thuộc c / số ngày quan sát của người đó
    c là thói quen ⇔ tần_suất(c) ≥ min_support
```

Độ phức tạp: DBSCAN của scikit-learn dùng cây lân cận, xấp xỉ $O(n \log n)$ mỗi nhóm; toàn bộ Aruba (161 nghìn phút, 3.015 phiên) chạy trong khoảng 10 giây kể cả vẽ hình.

### B2.3. Mô tả thói quen (`build_profiles`)

Với mỗi cụm, pipeline ghi vào `habits.csv` và `habit_report.md`:

| Trường | Cách tính |
|---|---|
| `typical_start` | **Trung bình vòng tròn** của giờ bắt đầu: $\bar\theta = \operatorname{atan2}\big(\overline{\sin\theta}, \overline{\cos\theta}\big)$ — trung bình thường của 23:30 và 00:30 sẽ ra 12:00, sai hoàn toàn |
| `window_start`–`window_end` | Phân vị 10% và 90% của độ lệch giờ so với trung bình vòng tròn (khung chứa 80% số lần) |
| `start_std_minutes` | Độ lệch chuẩn của giờ bắt đầu (phút) — thói quen càng "đúng giờ" càng nhỏ |
| `median_duration_minutes` | Trung vị thời lượng |
| `days_present`, `support` | Số ngày có mẫu; tỷ lệ trên số ngày quan sát |
| `is_habit` | `support ≥ min_support` |
| `sensor_types` | Tổ hợp cảm biến hay gặp nhất (ví dụ có `pillbox` → gợi ý uống thuốc) |
| `dominant_label`, `label_purity` | Nhãn thật chiếm đa số và tỷ lệ của nó — **chỉ để đánh giá** |

---

## 3.4. Đánh giá

| Loại | Chỉ số | Ý nghĩa |
|---|---|---|
| Nội tại | Silhouette tính **trong từng nhóm (người, phòng)** có ≥ 2 cụm, lấy trung bình theo kích thước | Cụm có tách biệt nhau không. Không tính silhouette toàn cục vì các phòng khác nhau vốn đã bị tách, sẽ làm điểm bị thổi phồng |
| Nội tại | `time_spread_min`: độ lệch chuẩn giờ bắt đầu trong cụm | Cụm có trả lời được *"lúc mấy giờ"* không |
| Ngoại tại | **ARI**, **NMI** giữa cụm và nhãn `người:hoạt_động`; **độ thuần** (purity) | Cụm có trùng với hoạt động thật không. Tính trên các phiên không phải nhiễu |
| Thực tiễn | Số thói quen, tỷ lệ nhiễu, tần suất | Kết quả có dùng được không |

**Baseline** để so sánh là phiên bản đầu tiên của đề tài: DBSCAN trên toàn bộ 10 đặc trưng số sau StandardScaler, `eps` = phân vị 90% của đường k-distance, không chia theo phòng.
