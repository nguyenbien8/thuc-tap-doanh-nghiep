# Ý tưởng thuyết trình dự án

## Thông điệp trung tâm

> Làm thế nào biến log cảm biến rời rạc thành các session hành vi, rồi phát hiện những mẫu lặp lại mà không cần biết trước tên hoạt động?

Không trình bày project như một danh sách thư viện. Hãy trình bày như một cuộc điều tra dữ liệu: vấn đề là gì, vì sao dữ liệu thô chưa trả lời được, quyết định kỹ thuật nào được chọn, bằng chứng cho thấy điều gì, và giới hạn nằm ở đâu.

**Ranh giới cần nói ngay:** project chỉ tìm và mô tả mẫu hành động chung. Robot, hệ thống nhắc thuốc, điều khiển thiết bị và dự báo hành động tiếp theo chỉ là ý tưởng ứng dụng, không phải phần code hay kết quả thực nghiệm.

## Mạch kể đề xuất

### Phần 1: Vấn đề thực tế

Mở đầu bằng một chuỗi sự kiện đơn giản:

```text
07:10 motion kitchen
07:12 door kitchen
07:15 temperature kitchen
07:18 light kitchen
```

Đặt câu hỏi: đây là bốn dòng log hay là một lần hoạt động của con người? Máy không thể tìm thói quen nếu chỉ nhìn từng dòng độc lập.

**Thông điệp cần chốt:** cần tạo đơn vị quan sát có ý nghĩa hơn raw event.

### Phần 2: Mục tiêu và phạm vi

Nêu rõ project chỉ giải quyết hai bước:

1. Tiền xử lý và tạo session.
2. Tìm các mẫu session lặp lại bằng một kỹ thuật unsupervised.

Không hứa hẹn nhận diện hoàn hảo mọi hoạt động. Mục tiêu là chứng minh một quy trình có thể giải thích, chạy lại và mở rộng.

### Phần 3: Dữ liệu và khó khăn

Giới thiệu schema gồm timestamp, cư dân, phòng, sensor, value và event type.

Nêu các vấn đề của raw data:

- Sự kiện rời rạc.
- Missing và duplicate.
- Các sensor có scale khác nhau.
- Chưa có nhãn hoạt động.
- Hành vi lặp lại nhưng không hoàn toàn giống nhau.

Đây là lý do không thể đưa CSV thẳng vào một thuật toán clustering rồi gọi kết quả là thói quen.

### Phần 4: Bước tiền xử lý

Trình bày bằng flow một chiều:

```text
Validate schema
-> parse timestamp/value
-> normalize category
-> handle missing
-> remove duplicates
-> sort by resident/time
-> sessionize
-> aggregate features
```

Giải thích kỹ nhất hai quyết định:

- `inactivity_gap = 30 phút`: khoảng im lặng lớn mở session mới.
- `sin/cos` cho giờ và ngày trong tuần: bảo toàn tính chu kỳ.

Kết thúc phần này bằng câu: sau preprocessing, mỗi session trở thành một dòng mô tả một lần hành vi thay vì một tín hiệu thiết bị đơn lẻ.

### Phần 5: Định nghĩa “mẫu hoạt động”

Định nghĩa chính thức:

> Một mẫu hoạt động là nhóm session có vector đặc trưng tương tự và xuất hiện lặp lại trong dữ liệu.

Nhấn mạnh cluster không tự có tên. Tên nghiệp vụ chỉ được đặt sau khi xem profile và timeline.

Ví dụ “một người thường uống thuốc lúc 8h” chỉ dùng để minh họa lớp ứng dụng phía sau: project hiện tại chỉ tìm được mẫu lặp lại quanh thời điểm đó, chưa tự nhắc thuốc và chưa đánh giá việc quên thuốc.

### Phần 6: Vì sao chọn DBSCAN?

Trình bày bảng so sánh ngắn:

| Phương pháp | Điểm mạnh | Vì sao không làm chính |
|---|---|---|
| K-Means | Dễ dùng, nhanh | Phải biết trước số cluster, ép noise vào cluster |
| Hierarchical | Có dendrogram | Cần quyết định cut tree, khó xử lý noise rõ ràng |
| DBSCAN | Không cần số cluster, có noise | Nhạy với eps, cần scale và kiểm tra sensitivity |
| HDBSCAN | Linh hoạt với mật độ | Mạnh hơn nhưng phức tạp hơn phạm vi bài thực tập |

Kết luận: DBSCAN là lựa chọn cân bằng giữa khả năng giải thích, phạm vi đề tài và nhu cầu chưa có nhãn.

### Phần 7: Cách chạy DBSCAN có trách nhiệm

Nêu tuần tự:

1. Chọn feature số có ý nghĩa.
2. StandardScaler.
3. Dùng k-distance để ước lượng `eps`.
4. Chạy DBSCAN với `min_samples = 5`.
5. Ghi lại cluster và noise.
6. Sinh metrics, profile và biểu đồ.

Cho thấy hình `k_distance_diagnostic.png` ở đây. Câu giải thích mẫu:

> `eps` được chọn bằng một heuristic tái lập dựa trên khoảng cách đến láng giềng thứ 5; biểu đồ này giúp kiểm tra xem ngưỡng có hợp lý hay không. Đây không phải một giá trị tối ưu tuyệt đối.

### Phần 8: Kết quả demo

Trình bày số liệu:

- 102 session.
- 3 cluster.
- Noise khoảng 6.86%.
- Silhouette khoảng 0.325.

Sau đó trình bày profile:

- Cluster 0: khoảng 33.33%, liên quan nhiều đến bedroom.
- Cluster 1: khoảng 18.63%, liên quan nhiều đến kitchen.
- Cluster 2: khoảng 41.18%, liên quan nhiều đến bedroom.

Cách diễn giải nên dùng:

> Dữ liệu demo cho thấy pipeline phát hiện ba vùng session lặp lại, chủ yếu khác nhau theo thời điểm và bối cảnh phòng.

Không nói quá thành “mô hình đã nhận diện chính xác ăn sáng, ăn tối và đi ngủ”.

### Phần 9: Đánh giá và giới hạn

Nói rõ metrics hiện tại là internal clustering metrics, không phải accuracy. Silhouette khoảng 0.325 cho thấy cấu trúc có phân tách ở mức vừa phải nhưng chưa đủ để khẳng định nhận diện hoạt động nghiệp vụ.

Các giới hạn cần tự nêu trước khi giảng viên hỏi:

- Demo chỉ có một cư dân và dữ liệu sạch.
- Sessionization phụ thuộc ngưỡng 30 phút.
- DBSCAN nhạy với `eps` và scale.
- Chưa có ground truth hoạt động.
- Cluster có thể phản ánh phòng/giờ thay vì hoạt động.
- Chưa đánh giá tổng quát hóa theo thời gian.

Việc chủ động nêu giới hạn làm kết luận đáng tin hơn.

### Phần 10: Ý tưởng ứng dụng sau này, không thuộc phạm vi code

Chỉ trình bày ngắn như hướng phát triển:

- Nếu phát hiện một mẫu thường lặp lại lúc 8h, một hệ thống khác có thể đề xuất nhắc nhở khi mẫu vắng mặt.
- Mẫu bất thường có thể là đầu vào cho một module cảnh báo.
- Profile mẫu có thể hỗ trợ cá nhân hóa smart home.

Nhấn mạnh: các module này không được xây dựng trong project; project chỉ cung cấp mẫu và profile làm đầu vào tiềm năng. Mọi ứng dụng sau này cần kiểm tra false positive, quyền riêng tư và xác nhận của người dùng.

### Phần 11: Bước phát triển tiếp theo

Đây là phần chứng minh project có hướng nghiên cứu tiếp:

1. Ánh xạ dữ liệu STRANDS.
2. Gán nhãn thủ công 30-50 session.
3. So sánh cluster với nhãn chuyên gia.
4. Chạy K-Means làm baseline.
5. Thử sensitivity của inactivity gap, eps và min_samples.
6. Cân nhắc HDBSCAN khi có nhiều cư dân hoặc mật độ khác nhau.

### Phần 12: Kết luận

Câu kết luận đề xuất:

> Dự án đã xây dựng được một pipeline không giám sát có thể tái lập: từ log cảm biến, hệ thống tạo session, biểu diễn session bằng đặc trưng thời gian và cảm biến, sau đó dùng DBSCAN để phát hiện các vùng hành vi lặp lại và session bất thường. Kết quả demo chứng minh quy trình hoạt động, nhưng để đặt tên hoạt động nghiệp vụ cần kiểm chứng thêm trên dữ liệu STRANDS và nhãn thủ công.

## Câu hỏi phản biện dự kiến

### Vì sao không dùng deep learning?

Dữ liệu trong phạm vi thực tập chưa có nhãn đủ lớn, còn mục tiêu là hiểu và giải thích pipeline. DBSCAN phù hợp hơn để chứng minh nguyên lý. Deep learning là hướng mở rộng khi có dữ liệu lớn và ground truth.

### Tại sao cluster chỉ có ba nhóm?

Số cluster là kết quả của mật độ dữ liệu và tham số DBSCAN, không đặt trước. Demo hiện tại có cấu trúc đơn giản nên chủ yếu tách theo phòng/thời điểm. Dữ liệu thật có thể cho kết quả khác.

### Silhouette 0.325 có tốt không?

Đây chưa phải điểm số cao. Nó cho thấy phân tách nội bộ có nhưng chưa mạnh, vì vậy không nên tuyên bố nhận diện hoạt động chính xác. Cần so sánh baseline và kiểm chứng bằng nhãn thủ công.

### Noise có phải lỗi không?

Không nhất thiết. Noise có thể là hoạt động hiếm hoặc bất thường, vốn là điểm mạnh của DBSCAN. Tuy nhiên cũng có thể do eps chưa phù hợp, nên phải phân tích các session noise.

### Làm sao biết cluster là hoạt động thật?

Xem timeline và profile của cluster, sau đó đối chiếu với nhãn chuyên gia trên một mẫu session. Không được suy ra tên hoạt động chỉ từ màu cluster trên PCA.

## Nguyên tắc khi làm slide sau này

- Mỗi slide chỉ có một thông điệp chính.
- Dùng một flow pipeline xuyên suốt, không thay đổi tên gọi giữa các slide.
- Hiển thị một ví dụ raw event trước và sau sessionization.
- Hiển thị một bảng profile cluster và k-distance plot.
- Metrics luôn đi kèm diễn giải, không chỉ liệt kê số.
- Kết luận phải phân biệt rõ: “pipeline chứng minh được” và “cần dữ liệu thật để xác nhận”.
