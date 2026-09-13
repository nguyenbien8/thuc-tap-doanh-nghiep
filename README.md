# Smart Home Activity Pattern Discovery

Dự án thực tập phát hiện các hoạt động thường xuyên/tuần hoàn của con người trong ngôi nhà thông minh từ dữ liệu cảm biến, theo hướng **unsupervised learning**.

## 1. Mục tiêu và phạm vi

Bài toán được giới hạn ở hai bước có thể giải thích và thực nghiệm rõ ràng:

1. **Tiền xử lý dữ liệu:** kiểm tra schema, chuẩn hóa kiểu dữ liệu, xử lý giá trị thiếu, loại bản ghi trùng, sắp xếp theo thời gian, gom các sự kiện thành session theo khoảng không hoạt động và tạo đặc trưng.
2. **Tìm mẫu hoạt động:** xem mỗi session là một quan sát; dùng DBSCAN để gom các session có hành vi tương tự mà không cần nhãn hoạt động ban đầu.

Một cụm DBSCAN được diễn giải là một mẫu hoạt động lặp lại, dựa trên thời lượng, số sự kiện, loại cảm biến, phòng, thời điểm trong ngày và ngày trong tuần. Nhãn `-1` là nhiễu hoặc hành vi bất thường.

**Phạm vi chính thức:** project chỉ thực nghiệm việc tìm các mẫu hành động chung từ dữ liệu cảm biến. Project không xây dựng robot, hệ thống nhắc nhở, bộ điều khiển thiết bị hay mô-đun dự báo hành động tiếp theo. Các ứng dụng như “phát hiện người thường uống thuốc lúc 8h để đề xuất nhắc nhở khi bỏ lỡ” chỉ là hướng phát triển sau này.

## 2. Dữ liệu đầu vào

CSV cần có các cột:

`timestamp, resident_id, room, sensor_type, sensor_id, value, event_type`

Ví dụ:

```csv
timestamp,resident_id,room,sensor_type,sensor_id,value,event_type
2025-01-01 07:10:00,resident_01,kitchen,motion,kitchen_motion,1,motion
2025-01-01 07:12:00,resident_01,kitchen,temperature,kitchen_temp,22.1,reading
```

Project có dữ liệu demo được sinh tái lập, không chứa thông tin cá nhân và không phụ thuộc internet. Có thể thay file demo bằng dữ liệu STRANDS sau khi ánh xạ tên cột về schema trên.

## 3. Cài đặt

Khuyến nghị Python 3.10+:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 4. Chạy nhanh

```powershell
python -m smart_home_patterns.cli generate-demo
python -m smart_home_patterns.cli run
```

Kết quả chính:

- `data/processed/clean_events.csv`: sự kiện đã làm sạch và có `session_key`.
- `data/processed/session_features.csv`: một dòng cho mỗi session, gồm đặc trưng dùng cho clustering và nhãn cụm.
- `reports/metrics.json`: `eps`, số cụm, tỷ lệ nhiễu, Silhouette, Davies-Bouldin và Calinski-Harabasz.
- `reports/activity_profiles.csv`: profile trung bình của từng mẫu hoạt động.
- `reports/figures/activity_clusters_pca.png`: biểu đồ PCA màu theo cụm.
- `reports/figures/k_distance_diagnostic.png`: chẩn đoán khoảng cách dùng để kiểm tra lựa chọn `eps`.

Có thể chạy từng bước:

```powershell
python -m smart_home_patterns.cli preprocess --input data/raw/smart_home_events.csv
python -m smart_home_patterns.cli run --input data/raw/smart_home_events.csv
```

## 5. Phương pháp và quyết định thiết kế

### Tiền xử lý

- Timestamp lỗi bị loại; `value` được ép số và điền median theo loại cảm biến, sau đó dùng median toàn cục nếu cần.
- Chuẩn hóa category bằng trim/lowercase.
- Bản ghi trùng được loại bỏ.
- Session mới bắt đầu khi khoảng cách giữa hai sự kiện liên tiếp của cùng cư dân vượt `inactivity_gap_minutes` (mặc định 30 phút).
- Thời điểm trong ngày được mã hóa chu kỳ bằng `sin`/`cos`, tránh việc 23:59 và 00:01 bị xem là xa nhau.

### Phát hiện mẫu

DBSCAN phù hợp với bài toán vì không yêu cầu biết trước số hoạt động, tìm được vùng dữ liệu có mật độ cao và đánh dấu ngoại lệ. Trước DBSCAN, đặc trưng được chuẩn hóa để `event_count` không lấn át các biến khác. `eps` mặc định lấy phân vị 90% của khoảng cách đến láng giềng thứ `min_samples`; trong báo cáo cần ghi lại giá trị thực tế và giải thích nếu điều chỉnh thủ công.

PCA chỉ dùng cho trực quan hóa hai chiều, không phải mô hình phát hiện mẫu chính.

## 6. Bố cục báo cáo đề xuất

1. Đặt vấn đề và câu hỏi nghiên cứu.
2. Mô tả dữ liệu và schema.
3. Tiền xử lý: quy tắc làm sạch, sessionization, đặc trưng.
4. Định nghĩa mẫu: một mẫu là một nhóm session có profile cảm biến/thời gian tương tự.
5. DBSCAN: lý do chọn, `eps`, `min_samples`, chuẩn hóa.
6. Kết quả: số cụm, tỷ lệ nhiễu, các chỉ số, profile cụm và hình PCA.
7. Phân tích một mẫu tiêu biểu và kiểm tra tính lặp theo ngày/tuần.
8. Hạn chế: dữ liệu demo có cấu trúc đơn giản, session phụ thuộc ngưỡng 30 phút, DBSCAN nhạy với scale và `eps`, chưa có ground truth.
9. Hướng phát triển: đối chiếu nhãn chuyên gia, so sánh HDBSCAN, cập nhật theo mùa bằng cách chạy lại pipeline trên cửa sổ dữ liệu mới.

Phần lập luận đầy đủ, gồm câu hỏi nghiên cứu, ranh giới phạm vi, lý do chọn DBSCAN, cách đọc kết quả demo, ý tưởng ứng dụng ngoài phạm vi và câu kết luận mẫu, nằm trong [research_story.md](reports/research_story.md). Đây là tài liệu nên dùng làm khung chính khi viết báo cáo và slide bảo vệ.

[Trình tự xử lý chi tiết](reports/processing_pipeline.md) mô tả từng bước từ CSV đến cluster, còn [ý tưởng thuyết trình](reports/presentation_outline.md) là kịch bản nội dung và các câu hỏi phản biện dự kiến. Hai file này là nền trước khi thiết kế slide.

## 7. Bước tiếp theo để nâng chất lượng nghiên cứu

Ưu tiên tiếp theo không phải thêm nhiều thuật toán mà là kiểm chứng ý nghĩa của cluster trên dữ liệu thật:

1. Ánh xạ dữ liệu STRANDS về schema của project.
2. Chọn 30-50 session và gán nhãn thủ công ở mức đơn giản.
3. Đối chiếu nhãn thủ công với cluster để biết mô hình đang nhận ra hoạt động hay chỉ nhận ra phòng.
4. Chạy K-Means như baseline đối chứng, giữ DBSCAN làm phương pháp chính.
5. Chỉ diễn giải hoặc đặt tên nghiệp vụ cho cluster sau khi đã kiểm tra timeline và metrics; việc xây hệ thống hành động dựa trên cluster là phần mở rộng, không thuộc project này.

## 8. Kiểm thử

```powershell
python -m pytest
```

Các test hiện có kiểm tra chuẩn hóa dữ liệu, chia session và đầu ra discovery. Đây là project thực nghiệm nên cần bổ sung đánh giá thủ công trên một số session thật trước khi kết luận ý nghĩa nghiệp vụ.
