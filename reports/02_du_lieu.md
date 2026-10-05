# 2. Dữ liệu

Đề tài chạy trên **hai bộ dữ liệu** với cùng một pipeline:

| | Thí nghiệm 1 – Mô phỏng | Thí nghiệm 2 – STRANDS Aruba |
|---|---|---|
| Vai trò | Kiểm chứng phương pháp khi **biết trước đáp án** | Kiểm chứng trên **dữ liệu thật** |
| Nguồn | Sinh bằng `smart-home generate-demo` (seed 42) | Tải bằng `smart-home download-strands` |
| Nội dung | Sự kiện cảm biến (chuyển động, cửa, nhiệt độ, ánh sáng, công suất, hộp thuốc) | Vị trí (phòng) của người theo **từng phút** |
| Quy mô | 2 cư dân × 28 ngày, 3.397 sự kiện | 1 cư dân × 112 ngày, 161.280 phút |
| Cấu hình | [configs/config.yaml](../configs/config.yaml) | [configs/strands_aruba.yaml](../configs/strands_aruba.yaml) |

---

## 2.1. Schema chung

Mọi nguồn dữ liệu đều được đưa về một bảng sự kiện 7 cột. Nhờ vậy, bước tiền xử lý và tìm mẫu không phụ thuộc vào nguồn.

| Cột | Kiểu | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `timestamp` | datetime | Thời điểm sự kiện | `2025-06-02 07:31:12` |
| `resident_id` | chuỗi | Người gây ra sự kiện | `resident_01` |
| `room` | chuỗi | Phòng / vị trí | `kitchen` |
| `sensor_type` | chuỗi | Loại cảm biến | `motion`, `door`, `pillbox`, `presence` |
| `sensor_id` | chuỗi | Mã thiết bị | `kitchen_motion` |
| `value` | số | Giá trị đo (1/0 cho cảm biến nhị phân) | `1.0`, `23.4` |
| `event_type` | chuỗi | Loại sự kiện | `motion`, `open`, `reading` |
| `activity_label` | chuỗi, **tuỳ chọn** | Nhãn hoạt động thật | `take_medicine` |

**Nguyên tắc quan trọng:** cột `activity_label` (nếu có) **không bao giờ được dùng làm đặc trưng**. Nó chỉ được mang theo để sau khi phân cụm xong, đối chiếu xem cụm tìm được tương ứng với hoạt động thật nào. Phương pháp vì vậy vẫn hoàn toàn không giám sát.

**Giả định:** mỗi sự kiện biết được thuộc về cư dân nào (`resident_id`). Trong nhà nhiều người, điều này cần thẻ định vị hoặc vòng đeo tay; với nhà một người (như Aruba) thì hiển nhiên.

---

## 2.2. Thí nghiệm 1 – Dữ liệu mô phỏng có đáp án

Mã nguồn: [src/smart_home_patterns/demo.py](../src/smart_home_patterns/demo.py). Mục đích là tạo một "đề thi có đáp án": biết trước mỗi người có những thói quen nào để đo xem phương pháp tìm lại được bao nhiêu.

### Lịch sinh hoạt cài sẵn

| Cư dân | Hoạt động | Phòng | Giờ TB | Thời lượng TB | Xác suất/ngày | Ghi chú |
|---|---|---|---|---|---|---|
| resident_01 (hưu trí, rất đều) | wake_up | bedroom | 06:45 | 15' | 100% | |
| | breakfast | kitchen | 07:30 | 20' | 95% | |
| | lunch | kitchen | 12:00 | 30' | 90% | |
| | watch_tv | living_room | 14:00 | 60' | 70% | |
| | exercise | living_room | 17:00 | 30' | **30%** | *không phải thói quen* |
| | dinner | kitchen | 18:30 | 35' | 95% | |
| | **take_medicine** | kitchen | **20:30** | 3' | 85% | kích hoạt cảm biến `pillbox` |
| | go_to_bed | bedroom | 22:30 | 10' | 100% | |
| resident_02 (đi làm) | wake_up | bedroom | 07:45 | 12' | 100% | **cuối tuần +1,5 giờ** |
| | breakfast | kitchen | 08:15 | 15' | 85% | **cuối tuần +1,5 giờ** |
| | dinner | kitchen | 19:15 | 30' | 90% | |
| | watch_tv | living_room | 20:30 | 90' | 80% | |
| | go_to_bed | bedroom | 23:15 | 10' | 100% | |

→ Đáp án: **12 thói quen** (≥ 50% số ngày) + **3 mẫu không thường xuyên** (exercise 30%, dậy muộn và ăn sáng muộn cuối tuần ≈ 8/28 ngày).

### Tính thực tế được đưa vào

- **Dao động giờ:** giờ bắt đầu lệch ngẫu nhiên theo phân phối chuẩn, độ lệch chuẩn 10 phút; thời lượng dao động ±20% (log-normal).
- **Chuỗi cảm biến:** khi vào phòng, mọi cảm biến của phòng kích hoạt; sau đó cảm biến chuyển động kích hoạt lại khoảng 5 phút/lần cho đến khi rời phòng.
- **Nhiễu hành vi:** mỗi người có 3 lần/ngày đi ngang ngẫu nhiên qua phòng tắm, hành lang hoặc phòng khách (1–3 sự kiện), nhãn `random_visit`.
- **Lỗi dữ liệu** (để bước làm sạch có việc thật để làm):

| Lỗi | Số dòng | Cách B1 xử lý |
|---|---:|---|
| Dòng trùng lặp | 50 | Loại bỏ |
| Timestamp hỏng (`not-a-timestamp`) | 8 | Ép kiểu → NaT → loại bỏ |
| Thiếu giá trị `value` | 33 | Điền median theo loại cảm biến |
| Tên phòng viết không thống nhất (`" Kitchen "`) | 67 | Cắt khoảng trắng, chữ thường |
| Log bị xáo trộn thứ tự | toàn bộ | Sắp xếp theo cư dân → thời gian |

---

## 2.3. Thí nghiệm 2 – STRANDS Long-term Person Activity (Aruba)

### Giới thiệu

Trang dữ liệu: <https://lcas.lincoln.ac.uk/nextcloud/shared/datasets/activity.html>. Bộ dữ liệu thuộc dự án STRANDS (LCAS, Đại học Lincoln), được dùng trong bài Coppola et al. (ECAI 2016) để đánh giá các mô hình thời gian cho nhận dạng hoạt động. Gồm hai thư mục:

- **aruba/** – một người cao tuổi sống một mình trong căn hộ thông minh, **16 tuần** (trích từ dữ liệu CASAS Aruba). **Đề tài dùng tập này.**
- **witham/** – một sinh viên trong văn phòng mở tại LCAS, 3 tuần. Không dùng vì không phải môi trường nhà ở.

### Định dạng thực tế

| File | Nội dung |
|---|---|
| `location.min` | Mỗi dòng một số nguyên = mã phòng người đang ở, **mỗi dòng là một phút** kể từ 00:00 ngày đầu tiên |
| `activity.min` | Tương tự, mã hoạt động mà chuyên gia đã gán nhãn |
| `location.names`, `activity.names` | Danh sách tên tương ứng với mã |

Aruba có 161.280 dòng = 112 ngày × 1.440 phút. 10 vị trí (Master Bedroom, Master Bathroom, Living Room, Kitchen, Junction, Corridor, Second Bedroom, Office, Second Bathroom, Outside) và 12 hoạt động (None, Bed_to_Toilet, Eating, Enter_Home, Housekeeping, Leave_Home, Meal_Preparation, Relax, Resperate, Sleeping, Wash_Dishes, Work).

File không chứa ngày tháng thật; đề tài gán ngày danh nghĩa bắt đầu `2010-11-04` và **không** rút ra kết luận nào về thứ trong tuần.

### Chuyển đổi sang schema

Mã nguồn: [src/smart_home_patterns/strands_adapter.py](../src/smart_home_patterns/strands_adapter.py). Mỗi phút trở thành một sự kiện `presence` — đúng loại tín hiệu mà một cảm biến định vị theo phòng tạo ra:

| Cột | Giá trị |
|---|---|
| `timestamp` | ngày bắt đầu + chỉ số dòng (phút) |
| `resident_id` | `aruba` |
| `room` | tên vị trí (chữ thường, `_` thay khoảng trắng) |
| `sensor_type` / `event_type` | `presence` |
| `sensor_id` | `loc_<mã>` (giữ mã gốc để truy vết) |
| `value` | `1.0` |
| `activity_label` | tên hoạt động — **chỉ để đánh giá** |

### Kiểm định cách đánh số mã (phát hiện khi làm đề tài)

Trang dữ liệu không nói rõ mã bắt đầu từ 0 hay 1. Mã vị trí 0 **không hề xuất hiện** trong `location.min` của Aruba, nên đề tài đối chiếu chéo mã vị trí với hoạt động đã gán nhãn (tính bằng số phút cùng xuất hiện):

| Mã vị trí | Hoạt động đi kèm nhiều nhất | Tên theo đánh số từ 1 | Tên theo đánh số từ 0 | Kết luận |
|---:|---|---|---|---|
| 1 | Sleeping (49.004 phút) | Master Bedroom | Master Bathroom | **từ 1** |
| 2 | Bed_to_Toilet (196) | Master Bathroom | Living Room | **từ 1** |
| 3 | Relax (44.216), Eating (1.563) | Living Room | Kitchen | **từ 1** |
| 4 | Meal_Preparation (4.911), Wash_Dishes (285) | Kitchen | Junction | **từ 1** |
| 9 | None (22.496); nơi xảy ra Leave_Home/Enter_Home; trung vị mỗi lần ở 146 phút | Second Bathroom | Outside | **ghi đè thành `outside`** |

- **Mã hoạt động** đánh số từ 0 (mã 0 = None) — khớp với toàn bộ bảng trên.
- **Mã vị trí** đánh số từ 1 (4 phòng chính khớp hoàn toàn với hoạt động).
- Riêng mã 9: ở "phòng tắm phụ" liên tục 2,5 giờ không làm gì, và là nơi người rời nhà/về nhà là vô lý; mã này gần như chắc chắn là **ra ngoài**. Cấu hình `location_overrides: {9: outside}` ghi lại việc hiệu chỉnh này một cách minh bạch.
- Có 53 phút mang mã hoạt động 13 (không có tên) → giữ dưới dạng `unknown_13`.

### Thống kê sau chuyển đổi (phút theo phòng)

| Phòng | Số phút | Tỷ lệ |
|---|---:|---:|
| living_room | 57.999 | 36,0% |
| master_bedroom | 55.645 | 34,5% |
| outside | 22.648 | 14,0% |
| kitchen | 8.847 | 5,5% |
| corridor | 6.147 | 3,8% |
| master_bathroom | 4.936 | 3,1% |
| second_bedroom | 3.309 | 2,1% |
| junction, office | 1.749 | 1,1% |

Hoạt động có nhãn chiếm phần nhỏ thời gian; 34% số phút mang nhãn `None` (không được gán). Điều này quan trọng khi đọc kết quả: một cụm có nhãn đa số là `None` **không có nghĩa là sai** — đó có thể là thói quen mà người gán nhãn không đặt tên (ví dụ vệ sinh buổi sáng).

### Điều kiện sử dụng

Khi dùng dữ liệu phải trích dẫn Coppola et al. (2016), và với tập Aruba phải trích dẫn thêm bài của CASAS (Cook, 2010). Dữ liệu thô **không được đưa vào repo**; lệnh `smart-home download-strands` tải bản gốc (~30 kB) từ trang của LCAS.
