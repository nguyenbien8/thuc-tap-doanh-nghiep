# 1. Tổng quan đề tài

**Đề tài:** Học thói quen của con người trong ngôi nhà thông minh từ dữ liệu cảm biến
**Hướng tiếp cận:** Học máy không giám sát — phân cụm mật độ DBSCAN trên các phiên hoạt động

---

## 1.1. Bối cảnh

Một ngôi nhà thông minh ghi lại liên tục các sự kiện cảm biến: cảm biến chuyển động (PIR) ở từng phòng, công tắc cửa và tủ, cảm biến nhiệt độ, ánh sáng, công suất thiết bị. Mỗi dòng dữ liệu chỉ cho biết *"lúc t, ở phòng r, cảm biến s có giá trị v"*. Dữ liệu này có ba đặc điểm gây khó khăn:

1. **Không có nhãn.** Người ở trong nhà không ghi lại "tôi đang ăn sáng" hay "tôi đang uống thuốc". Việc gán nhãn thủ công tốn kém và xâm phạm riêng tư.
2. **Rời rạc và nhiễu.** Một hoạt động sinh ra hàng chục sự kiện; bên cạnh đó có nhiều sự kiện ngẫu nhiên (đi ngang hành lang, cảm biến kích hoạt nhầm).
3. **Mang tính cá nhân.** Mỗi người có lịch sinh hoạt khác nhau nên không thể dùng một bộ luật viết tay chung cho mọi người.

Tuy vậy, đời sống con người lại **lặp lại theo chu kỳ ngày**: thức dậy, nấu ăn, uống thuốc, đi ngủ... gần như cùng một khung giờ, ở cùng một nơi. Đề tài khai thác chính tính lặp lại này.

## 1.2. Mục tiêu và phạm vi

Mục tiêu là **tự động tìm ra các hành động thường xuyên / tuần hoàn của từng người** từ dữ liệu cảm biến không nhãn, và mô tả chúng dưới dạng con người đọc được, ví dụ:

> *"Cư dân 1 có thói quen ở **bếp** vào khoảng **20:32** (80% số lần rơi vào 20:20–20:40), mỗi lần khoảng 3 phút, lặp lại **25/28 ngày**, luôn kèm cảm biến hộp thuốc."* → đây chính là thói quen uống thuốc buổi tối.

Đề tài gồm đúng hai bước như yêu cầu:

| Bước | Nội dung | Kết quả đầu ra |
|---|---|---|
| **B1. Tiền xử lý** | Làm sạch, chuẩn hoá, gom sự kiện thành *phiên hoạt động*, trích đặc trưng | Bảng phiên (mỗi dòng một lần ở một phòng) |
| **B2. Định nghĩa mẫu & tìm mẫu** | Định nghĩa "thói quen" một cách đo được; dùng **một kỹ thuật: DBSCAN** để tìm | Danh sách thói quen: ai, ở đâu, lúc mấy giờ, bao lâu, bao nhiêu ngày |

**Ngoài phạm vi** (chỉ là hướng ứng dụng về sau): robot, hệ thống nhắc nhở khi quên uống thuốc, điều khiển thiết bị, dự đoán hành động tiếp theo, phân loại có giám sát.

## 1.3. Câu hỏi nghiên cứu

- **RQ1 – Biểu diễn:** Chuỗi sự kiện cảm biến rời rạc nên được gom thành đơn vị quan sát nào để phản ánh một lần hoạt động của con người?
- **RQ2 – Phát hiện:** Với định nghĩa thói quen đã chọn, DBSCAN có tìm lại được các thói quen mà không cần biết trước số lượng thói quen và không dùng nhãn hay không?
- **RQ3 – Nhiễu và độ tin cậy:** Phương pháp có tách được hành vi ngẫu nhiên khỏi thói quen, và kết quả có ổn định khi thay đổi tham số hay không?

## 1.4. Định nghĩa "thói quen" dùng trong đề tài

Đây là quyết định quan trọng nhất của bước B2 vì nó quyết định thuật toán phải tìm cái gì.

> **Thói quen** là một nhóm các phiên hoạt động của **cùng một người**, ở **cùng một phòng**, thoả mãn đồng thời:
> 1. **Cùng khung giờ:** giờ bắt đầu gần nhau (trong khoảng `eps` ≈ 30 phút) trên đồng hồ 24 giờ;
> 2. **Cùng kiểu:** thời lượng tương tự nhau;
> 3. **Lặp lại đủ nhiều:** xuất hiện ở ít nhất `min_support` = 50% số ngày quan sát.
>
> Nhóm thoả mãn (1) + (2) nhưng chưa đạt (3) được gọi là **mẫu lặp lại không thường xuyên** (ví dụ: tập thể dục 2–3 lần/tuần, dậy muộn vào cuối tuần). Phiên không thuộc nhóm nào là **nhiễu**.

Điều kiện (1)–(2) là điều kiện *mật độ* — rất nhiều phiên nằm sát nhau — nên chọn thuật toán phân cụm theo mật độ là tự nhiên. Điều kiện (3) được kiểm tra sau khi phân cụm, bằng cách đếm số ngày khác nhau mà cụm xuất hiện.

## 1.5. Vì sao chọn DBSCAN

| Tiêu chí | K-Means | GMM | **DBSCAN** |
|---|---|---|---|
| Phải biết trước số thói quen *k* | Có | Có | **Không** |
| Xử lý hành vi ngẫu nhiên | Ép vào cụm gần nhất | Gán xác suất | **Gán nhãn nhiễu −1** |
| Tham số có ý nghĩa thực tế | *k* khó đoán | *k*, dạng hiệp phương sai | **`eps` = "lệch nhau bao nhiêu phút", `min_samples` = "lặp lại bao nhiêu lần"** |
| Dễ giải thích | Trung bình | Khó | **Dễ** |

Điểm then chốt: nhờ thiết kế không gian đặc trưng có đơn vị **giờ** (xem [03_phuong_phap.md](03_phuong_phap.md)), hai tham số của DBSCAN mang đúng ý nghĩa của định nghĩa thói quen, nên phương pháp vừa trình bày được bằng lời, vừa chạy thực nghiệm được.

## 1.6. Liên hệ với tài liệu tham khảo

**Duckworth, Hogg & Cohn (2019)** — *Unsupervised human activity analysis for intelligent mobile robots*, Artificial Intelligence 270:67–92 — nghiên cứu cách một robot di động (dự án STRANDS) tự học các hoạt động của con người qua quan sát dài hạn. Bài báo: (i) biến quan sát khung xương người thành biểu diễn **không gian–thời gian định tính** (quan hệ giữa tay/đầu với các đồ vật quan trọng); (ii) coi mỗi quan sát như một "văn bản" gồm các "từ mã"; (iii) dùng mô hình chủ đề **LDA** để tìm ra các khái niệm ẩn và coi chúng là các lớp hoạt động — hoàn toàn không giám sát; (iv) cập nhật mô hình liên tục bằng suy luận biến phân.

Đề tài này kế thừa **tư tưởng** của bài báo, không sao chép kỹ thuật:

| Khía cạnh | Duckworth et al. (2019) | Đề tài này |
|---|---|---|
| Nguồn dữ liệu | Camera trên robot, khung xương người | Cảm biến môi trường / vị trí trong nhà |
| Đơn vị quan sát | Một đoạn quan sát người | Một **phiên**: một lần ở liên tục trong một phòng |
| Biểu diễn | Quan hệ định tính (không phụ thuộc toạ độ chính xác) | Giờ trên vòng tròn 24h + thời lượng, **nhóm theo phòng** (vị trí định tính) |
| Kỹ thuật học | LDA (mô hình sinh xác suất) | DBSCAN (phân cụm mật độ) |
| Điểm chung | Không dùng nhãn khi học; nhãn chỉ dùng để đánh giá; tìm các mẫu lặp lại trong quan sát dài hạn | |

Lý do không dùng LDA: dữ liệu nhà thông minh có cấu trúc thời gian rõ ràng (giờ trong ngày), và câu hỏi của đề tài là *"khi nào, ở đâu, bao lâu"* — DBSCAN trên không gian thời gian trả lời trực tiếp câu hỏi đó và dễ trình bày hơn.

**Bộ dữ liệu STRANDS** (*Long-term person activity datasets*, LCAS – Đại học Lincoln) được công bố kèm bài **Coppola, Krajník, Bellotto & Duckett (ECAI 2016)**; tập con Aruba trích từ dữ liệu **CASAS** (Cook, 2010). Đề tài dùng tập Aruba (16 tuần, một người sống một mình) làm dữ liệu thật — xem [02_du_lieu.md](02_du_lieu.md).

## 1.7. Tóm tắt kết quả

| | Dữ liệu mô phỏng (có đáp án) | STRANDS Aruba (dữ liệu thật) |
|---|---|---|
| Quy mô | 2 người, 28 ngày, 3.397 sự kiện | 1 người, 112 ngày, 161.280 phút |
| Thói quen tìm được | **12/12** thói quen cài sẵn, kể cả **uống thuốc 20:32** | **5** thói quen (ngủ ~00:18, nấu ăn sáng ~09:04, ...) |
| Khớp với nhãn thật | ARI 0,96 · độ thuần 100% | độ thuần 79% (ngủ 100%, nấu ăn 92%) |
| So với cách làm ban đầu | độ lệch giờ trong cụm 182 → **10 phút** | 289 → **115 phút** |

Chi tiết và thảo luận: [04_ket_qua_thuc_nghiem.md](04_ket_qua_thuc_nghiem.md).

## Tài liệu tham khảo

1. P. Duckworth, D. C. Hogg, A. G. Cohn. *Unsupervised human activity analysis for intelligent mobile robots.* Artificial Intelligence, 270:67–92, 2019. doi:10.1016/j.artint.2018.12.005
2. C. Coppola, T. Krajník, N. Bellotto, T. Duckett. *Learning temporal context for activity recognition.* European Conference on Artificial Intelligence (ECAI), 2016. — bài mô tả bộ dữ liệu STRANDS long-term person activity.
3. D. J. Cook. *Learning setting-generalized activity models for smart spaces.* IEEE Intelligent Systems, 2010. — nguồn gốc dữ liệu CASAS Aruba.
4. M. Ester, H.-P. Kriegel, J. Sander, X. Xu. *A density-based algorithm for discovering clusters in large spatial databases with noise.* KDD, 1996. — thuật toán DBSCAN.
5. Trang dữ liệu STRANDS: <https://lcas.lincoln.ac.uk/nextcloud/shared/datasets/activity.html>
