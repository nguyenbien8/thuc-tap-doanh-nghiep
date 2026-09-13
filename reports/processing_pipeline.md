# Trình tự xử lý chi tiết của dự án

## 1. Mục tiêu đầu vào và đầu ra

**Đầu vào:** log sự kiện cảm biến trong nhà thông minh, mỗi dòng là một sự kiện có timestamp, cư dân, phòng, cảm biến, giá trị và loại sự kiện.

**Đầu ra:**

- Bảng sự kiện đã làm sạch và có `session_key`.
- Bảng đặc trưng cấp session.
- Nhãn cluster của từng session.
- Profile trung bình của mỗi cluster.
- Metrics và hai biểu đồ chẩn đoán/diễn giải.

Pipeline kết thúc tại đây. Nó không có bước dự báo hành động tiếp theo, không gửi thông báo, không điều khiển robot/thiết bị và không tự động đặt tên nghiệp vụ cho cluster.

Luồng tổng quát:

```text
CSV cảm biến
   |
   v
Kiểm tra schema và ép kiểu
   |
   v
Lọc bản ghi thiếu/trùng + chuẩn hóa category
   |
   v
Sessionization theo inactivity gap
   |
   v
Tạo đặc trưng cấp session
   |
   v
StandardScaler
   |
   v
Ước lượng eps bằng k-distance
   |
   v
DBSCAN
   |
   +--> Metrics và noise analysis
   +--> Profile cluster
   +--> PCA visualization
   +--> K-distance diagnostic
```

## 2. Bước 0: kiểm tra dữ liệu đầu vào

File đầu vào phải có schema:

`timestamp, resident_id, room, sensor_type, sensor_id, value, event_type`

Hàm thực hiện: `validate_schema()` trong `src/smart_home_patterns/preprocessing.py`.

Nếu thiếu cột, pipeline dừng với lỗi rõ ràng thay vì âm thầm tạo kết quả không đầy đủ. Danh sách cột được đọc từ `configs/config.yaml` để schema được quản lý tập trung.

## 3. Bước 1: tiền xử lý sự kiện

Hàm thực hiện: `clean_events()`.

### 3.1 Chuẩn hóa kiểu dữ liệu

- `timestamp` được chuyển sang datetime; timestamp không hợp lệ bị loại.
- `value` được chuyển sang số; giá trị không chuyển được trở thành missing.
- Các trường category được trim khoảng trắng và chuyển lowercase: `room`, `sensor_type`, `event_type`.

### 3.2 Quy tắc missing

- Tính tỷ lệ missing của mỗi dòng trước khi điền giá trị.
- Loại dòng có tỷ lệ missing vượt `max_missing_fraction = 0.40`.
- Các trường cấu trúc bắt buộc như timestamp, resident, room, sensor và event type phải có giá trị; nếu thiếu thì loại.
- `value` được điền bằng median theo `sensor_type`; nếu nhóm không có median thì dùng median toàn cục; nếu toàn bộ thiếu thì dùng 0.

Quy tắc này chỉ là baseline. Khi dùng dữ liệu STRANDS, cần kiểm tra xem missing có nghĩa là “cảm biến không phát hiện” hay “bản ghi lỗi”; hai trường hợp đó không nên xử lý giống nhau.

### 3.3 Loại trùng và sắp xếp

- Loại bản ghi trùng hoàn toàn.
- Sắp xếp theo `resident_id` và `timestamp`.

Kết quả trung gian được ghi tại `data/processed/clean_events.csv`.

## 4. Bước 2: sessionization

Hàm thực hiện: `create_sessions()`.

Với từng cư dân:

1. Tính khoảng thời gian giữa sự kiện hiện tại và sự kiện trước đó.
2. Nếu khoảng cách lớn hơn `inactivity_gap_minutes = 30`, mở session mới.
3. Các sự kiện liên tiếp trong cùng vùng thời gian được gán cùng `session_id`.
4. Ghép `resident_id` và `session_id` thành `session_key`.

### Ý nghĩa

Một dòng sensor là hành động rất nhỏ của thiết bị; một session là đơn vị gần hơn với một lần hoạt động của con người. Đây là bước biến dữ liệu log thành đơn vị quan sát có thể đưa vào clustering.

### Giới hạn cần nói trong báo cáo

Sessionization bằng inactivity gap là một giả định. Nếu cư dân tạm dừng 31 phút, hai phần của cùng hoạt động có thể bị tách. Ngược lại, một chuỗi hoạt động khác nhau nhưng có sự kiện trung gian có thể bị nối. Vì vậy 30 phút cần được kiểm tra sensitivity trên dữ liệu thật.

## 5. Bước 3: tạo đặc trưng cấp session

Hàm thực hiện: `build_session_features()`.

Mỗi session được chuyển thành một vector số gồm:

| Nhóm | Đặc trưng | Ý nghĩa |
|---|---|---|
| Quy mô | `event_count` | Session có bao nhiêu sự kiện |
| Thời lượng | `duration_minutes` | Session kéo dài bao lâu |
| Không gian | `unique_rooms` | Có đi qua bao nhiêu phòng |
| Thiết bị | `unique_sensors` | Có bao nhiêu sensor tham gia |
| Hành vi sensor | `motion_count`, `door_count` | Mức độ chuyển động và cửa |
| Môi trường | `temperature_mean`, `light_mean` | Bối cảnh môi trường trung bình |
| Thời điểm ngày | `hour_sin`, `hour_cos` | Mã hóa chu kỳ 24 giờ |
| Thời điểm tuần | `weekday_sin`, `weekday_cos` | Mã hóa chu kỳ 7 ngày |

`dominant_room` và `dominant_event_type` được giữ lại để giải thích profile, nhưng không đưa trực tiếp vào khoảng cách clustering vì đây là category chưa được mã hóa. `weekday` nguyên bản cũng không dùng trực tiếp vì thứ Hai và Chủ Nhật phải gần nhau về mặt chu kỳ. `weekday_sin` và `weekday_cos` vẫn được tạo để phục vụ phân tích tuần, nhưng được loại khỏi feature set của demo nhỏ; khi có dữ liệu đủ dài, có thể bật lại sau sensitivity analysis.

## 6. Bước 4: chuẩn hóa đặc trưng

Hàm thực hiện: `discover_patterns()`.

Các feature số có scale khác nhau. Ví dụ `event_count` có thể lớn hơn nhiều so với `hour_sin`, khiến một nhóm feature lấn át khoảng cách. `StandardScaler` đưa các feature về cùng thang đo trước DBSCAN.

Đây là bước cần thiết để khoảng cách Euclidean có ý nghĩa tương đối giữa các feature.

## 7. Bước 5: chọn `eps` có thể giải thích

Hàm thực hiện: `estimate_eps()` và `k_distance_values()`.

- Dùng `min_samples = 5`.
- Tính khoảng cách từ mỗi session đến láng giềng thứ 5.
- Sắp xếp các khoảng cách.
- Chọn `eps` theo phân vị 90% như một heuristic tái lập.
- Sinh `reports/figures/k_distance_diagnostic.png` để kiểm tra trực quan vị trí ngưỡng.

Cách nói chính xác trong báo cáo là: đây là lựa chọn khởi đầu có thể tái lập, không phải giá trị tối ưu tuyệt đối. Cần thử một dải `eps` trên dữ liệu thật và kiểm tra độ ổn định cluster.

## 8. Bước 6: DBSCAN

DBSCAN nhận ma trận feature đã scale và trả về:

- `0, 1, 2, ...`: cluster phát hiện được.
- `-1`: noise hoặc session không đủ giống các vùng mật độ cao.

Lý do dùng DBSCAN làm kỹ thuật chính:

- Không cần biết trước số hoạt động.
- Có thể phát hiện noise.
- Phù hợp với giai đoạn khám phá khi chưa có nhãn.
- Dễ liên kết cluster với profile trung bình để con người kiểm tra.

DBSCAN không tự đặt tên “breakfast” hay “sleep”. Tên hoạt động chỉ được đặt sau khi xem timeline, profile và/hoặc nhãn thủ công.

## 9. Bước 7: đánh giá

Pipeline ghi các chỉ số:

- `n_sessions`: số session sau preprocessing.
- `n_clusters`: số cluster không tính noise.
- `noise_ratio`: tỷ lệ session có nhãn `-1`.
- `silhouette_score`: càng cao càng tốt.
- `davies_bouldin_score`: càng thấp càng tốt.
- `calinski_harabasz_score`: thường càng cao càng tốt.
- `eps`, `min_samples`, `feature_columns`: để tái lập quyết định.

Các chỉ số hiện là đánh giá nội bộ trên cùng tập dữ liệu dùng để tìm cluster. Vì vậy không được gọi chúng là accuracy hay khả năng dự báo. Trên dữ liệu thật cần bổ sung:

- Gán nhãn thủ công 30-50 session.
- So sánh cluster với nhãn chuyên gia.
- Kiểm tra theo khoảng thời gian giữ lại.
- Thử sensitivity với `eps`, `min_samples` và inactivity gap.

## 10. Bước 8: profile và trực quan hóa

`build_profiles()` tính trung bình feature của từng cluster, số session, tỷ lệ và phòng/event thường gặp. Đây là cầu nối từ kết quả toán học sang diễn giải con người.

Hai biểu đồ được sinh:

- `activity_clusters_pca.png`: PCA hai chiều để quan sát cấu trúc cluster; PCA chỉ dùng để vẽ, không phải mô hình chính.
- `k_distance_diagnostic.png`: hỗ trợ giải thích lựa chọn `eps`.

## 11. Bước 9: diễn giải kết quả demo

Với dữ liệu demo hiện tại, pipeline tạo 102 session, 3 cluster và khoảng 6.86% noise. Silhouette khoảng 0.325. Profile cho thấy ba vùng session liên quan đến thời điểm và bối cảnh phòng.

Kết luận đúng:

> Pipeline phát hiện được các nhóm session lặp lại trong dữ liệu demo; cấu trúc hiện tại chủ yếu phản ánh time-of-day và tương quan với phòng. Chưa đủ bằng chứng để gắn tên hoạt động nghiệp vụ cụ thể.

Đây là lý do bước tiếp theo phải là dữ liệu STRANDS và kiểm tra thủ công, không phải chỉ tối ưu thêm một metric.

## 12. Lệnh tái lập

```powershell
$env:PYTHONPATH="src"
python -m smart_home_patterns.cli generate-demo
python -m smart_home_patterns.cli run
python -m pytest
```

Các file chính sau khi chạy nằm ở `data/processed/` và `reports/`.
