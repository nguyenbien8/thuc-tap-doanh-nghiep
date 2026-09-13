# Research Story: Phát hiện mẫu hoạt động trong nhà thông minh

## 1. Câu chuyện một câu

Từ các sự kiện cảm biến rời rạc, project gom các sự kiện gần nhau thành một session, mô tả session bằng đặc trưng thời gian và cảm biến, rồi dùng DBSCAN để tìm các nhóm session lặp lại mà không cần gán nhãn hoạt động từ đầu.

## 2. Vấn đề nghiên cứu

Trong nhà thông minh, dữ liệu thường là log cảm biến chứ không phải nhãn có sẵn như `breakfast`, `sleep` hay `leave_home`. Nếu muốn tự động tìm thói quen, ta cần trả lời:

> Những session nào xuất hiện nhiều lần và có profile hành vi tương tự nhau?

Mục tiêu của project không phải khẳng định một session chắc chắn là một hoạt động có tên người dùng đặt trước. Mục tiêu đúng hơn là tìm **mẫu hành vi lặp lại** để con người có thể kiểm tra và đặt tên ở bước sau.

### Ranh giới phạm vi

Project dừng ở việc phát hiện và mô tả các mẫu hành động chung. Không triển khai robot, hệ thống nhắc nhở, điều khiển thiết bị, dự báo hành động tiếp theo hoặc quyết định thay cho người dùng. Những phần đó chỉ được nêu như ý tưởng ứng dụng sau khi mẫu đã được xác nhận.

## 3. Vì sao phải tiền xử lý trước?

Một dòng log cảm biến chỉ nói rằng một cảm biến đã phát sự kiện. Nó chưa phải là một hoạt động có ý nghĩa. Ví dụ bốn sự kiện trong tám phút ở bếp có thể cùng thuộc một lần chuẩn bị bữa ăn.

Vì vậy project dùng sessionization:

- Sắp xếp sự kiện theo cư dân và timestamp.
- Bắt đầu session mới khi không có sự kiện trong hơn 30 phút.
- Tóm tắt session bằng số sự kiện, thời lượng, số phòng, loại cảm biến, giá trị môi trường và thời điểm trong ngày.
- Mã hóa giờ bằng `sin/cos` để 23:59 và 00:01 gần nhau về mặt chu kỳ.

Nếu bỏ bước này và đưa từng dòng log vào clustering, mô hình sẽ gom các lần phát cảm biến thay vì gom hành vi của con người.

## 4. Định nghĩa mẫu hoạt động

Trong phạm vi bài thực tập, một mẫu hoạt động được định nghĩa là:

> Một nhóm session có đặc trưng hành vi tương tự và xuất hiện lặp lại trong dữ liệu.

Mỗi mẫu được mô tả bằng:

- Quy mô: số session và tỷ lệ trên toàn bộ dữ liệu.
- Bối cảnh: phòng thường gặp và loại sự kiện thường gặp.
- Cấu trúc: thời lượng, số sự kiện, số cảm biến.
- Nhịp thời gian: vị trí trong ngày và ngày trong tuần.

DBSCAN gán `-1` cho session không thuộc vùng mật độ cao. Đây là tín hiệu có thể dùng để tìm hành vi bất thường hoặc thay đổi thói quen, không nên tự động coi là lỗi dữ liệu.

## 5. Vì sao chọn DBSCAN?

### Lý do chọn

- Không cần biết trước có bao nhiêu mẫu hoạt động.
- Có thể tìm nhóm theo mật độ thay vì ép mọi session vào một nhóm.
- Có nhãn nhiễu cho hành vi hiếm hoặc bất thường.
- Dễ giải thích trong báo cáo: các session gần nhau trong không gian đặc trưng tạo thành một vùng hành vi lặp lại.

### Vì sao không chọn K-Means làm phương pháp chính?

K-Means cần chọn trước số cụm `k` và gán mọi điểm vào một cụm. Điều đó không phù hợp khi số thói quen chưa biết và khi có session bất thường. K-Means vẫn có thể là baseline mở rộng, nhưng không phải lựa chọn đầu tiên cho câu hỏi hiện tại.

### Vì sao chưa chọn HDBSCAN?

HDBSCAN mạnh hơn khi mật độ giữa các nhóm thay đổi và tự chọn ngưỡng ở nhiều mức. Tuy nhiên, DBSCAN có ít tham số hơn, dễ trình bày và đủ cho quy mô bài thực tập. Khi dữ liệu thật lớn hoặc có nhiều cư dân/mật độ khác nhau, HDBSCAN là hướng nâng cấp hợp lý.

## 6. Cách chọn tham số và đánh giá

- Chuẩn hóa toàn bộ đặc trưng số bằng `StandardScaler`.
- Chọn `min_samples = 5` để một mẫu phải có một vùng lân cận đủ ổn định.
- Ước lượng `eps` từ phân vị 90% của khoảng cách đến láng giềng thứ `min_samples`.
- Báo cáo đồng thời số cụm, tỷ lệ nhiễu, Silhouette, Davies-Bouldin và Calinski-Harabasz.

Không được kết luận chỉ từ một metric:

- Silhouette càng cao càng tốt.
- Davies-Bouldin càng thấp càng tốt.
- Calinski-Harabasz càng cao càng tốt.
- Tỷ lệ nhiễu cần được đọc cùng với mục tiêu: quá cao nghĩa là mô hình bỏ sót nhiều session; quá thấp có thể nghĩa là mô hình gom quá rộng.

## 7. Đọc kết quả demo hiện tại

Kết quả chạy tái lập hiện tại:

- 102 session.
- 3 cụm.
- Tỷ lệ nhiễu khoảng 6.86%.
- Silhouette khoảng 0.325.
- Cụm 0 chiếm khoảng 33.33%, profile chính là `bedroom`.
- Cụm 1 chiếm khoảng 18.63%, profile chính là `kitchen`.
- Cụm 2 chiếm khoảng 41.18%, profile chính là `bedroom`.

Diễn giải trung thực:

> Với dữ liệu demo hiện tại, DBSCAN phát hiện ba vùng session lặp lại, chủ yếu khác nhau theo thời điểm trong ngày và có tương quan với bối cảnh phòng. Đây là bằng chứng pipeline có thể tìm cấu trúc lặp lại, nhưng chưa đủ để gắn nhãn chi tiết như “ăn sáng”, “ăn tối” hay “đi ngủ”.

Điểm này rất quan trọng khi bảo vệ: không phóng đại kết quả vượt quá thông tin mà feature và dữ liệu đang cung cấp.

## 8. Ý tưởng ứng dụng ngoài phạm vi thực nghiệm

Nếu xác nhận các cụm trên dữ liệu thật bằng kiểm tra thủ công hoặc nhãn chuyên gia, profile mẫu có thể trở thành đầu vào cho một project khác, ví dụ:

- Nếu một người thường có một mẫu hành động vào khoảng 8h, hệ thống bên ngoài có thể đề xuất nhắc nhở khi mẫu đó vắng mặt.
- Một robot hoặc ứng dụng khác có thể dùng mẫu bất thường để đưa ra cảnh báo cần kiểm tra.
- Một hệ thống nhà thông minh có thể dùng mẫu đã xác nhận để cá nhân hóa thiết bị.
- Một module theo dõi dài hạn có thể so sánh profile theo mùa hoặc theo cửa sổ thời gian mới.

Các ví dụ này không được cài đặt trong project hiện tại. Chúng chỉ có thể triển khai sau khi kiểm tra false positive, quyền riêng tư và sự đồng ý của người dùng.

## 9. Bước tiếp theo có giá trị nhất

1. Thay dữ liệu demo bằng một phần dữ liệu STRANDS và lập bảng ánh xạ sensor/event về schema của project.
2. Chọn ngẫu nhiên 30-50 session, đọc timeline và ghi nhận diễn giải thủ công ở mức đơn giản.
3. So sánh diễn giải thủ công với cluster để kiểm tra cluster có ý nghĩa hành vi chung hay chỉ phản ánh phòng/thời điểm.
4. Thử một baseline K-Means với cùng feature, ghi rõ đây là đối chứng chứ không thay DBSCAN.
5. Điều chỉnh feature nếu cần, đặc biệt thêm đặc trưng thứ tự phòng/sensor hoặc cửa sổ thời gian, rồi chạy lại và so sánh metrics.
6. Chỉ sau bước này mới cân nhắc đặt tên nghiệp vụ cho từng cluster; không xây module nhắc nhở trong phạm vi bài này.

## 10. Câu kết luận mẫu cho báo cáo

Project chứng minh một quy trình không giám sát có thể chuyển log cảm biến thành các session hành vi và phát hiện các nhóm session lặp lại mà không cần số lượng hoạt động định trước. DBSCAN được chọn vì phù hợp với dữ liệu chưa có nhãn và có khả năng tách hành vi hiếm. Trên dữ liệu demo, kết quả đáng tin cậy nhất là phát hiện các profile theo bối cảnh phòng; để kết luận về hoạt động cụ thể của con người, cần xác nhận trên dữ liệu thật và bằng nhãn thủ công có kiểm soát.
