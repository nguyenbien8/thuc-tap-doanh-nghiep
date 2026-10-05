# 5. Kịch bản thuyết trình và chuẩn bị phản biện

**Slide:** [slide_thuyet_trinh.html](slide_thuyet_trinh.html) — mở bằng trình duyệt.

| Phím | Tác dụng |
|---|---|
| → / Space / Enter / click nửa phải | Slide sau |
| ← / Backspace / click nửa trái | Slide trước |
| `N` | Bật/tắt ghi chú thuyết trình |
| `F` | Toàn màn hình |
| `Ctrl + P` → *Save as PDF* | Xuất PDF, mỗi slide một trang (khổ ngang, lề 0, bật *Background graphics*) |

File slide dùng ảnh trong `reports/results/`, nên khi nộp hoặc chép sang máy khác cần giữ nguyên thư mục `reports/`. Trước khi trình bày, điền họ tên, người hướng dẫn và đơn vị thực tập vào slide 1 (tìm chuỗi `[Họ và tên]` trong file HTML).

**Thời lượng mục tiêu:** 12–15 phút · 16 slide · khoảng 50–60 giây mỗi slide.

---

## Mạch trình bày

| Phần | Slide | Thời gian | Thông điệp cần chốt |
|---|---|---|---|
| Mở đầu | 1–3 | 2' | Dữ liệu cảm biến không nhãn → cần tìm thói quen *ai · ở đâu · mấy giờ* |
| Nền tảng | 4–5 | 2' | Kế thừa tư tưởng Duckworth et al.; hai bộ dữ liệu, một bộ có đáp án |
| Phương pháp | 6–8 | 4' | Phiên = một lần ở một phòng; thói quen = cùng giờ + cùng kiểu + ≥ 50% ngày; DBSCAN trong không gian "giờ" |
| Kết quả | 9–12 | 4' | 12/12 thói quen, có uống thuốc 20:32; dữ liệu thật: ngủ 100%, bữa sáng 92% |
| Đánh giá | 13–14 | 2' | Tốt hơn hẳn baseline; tham số ổn định |
| Kết thúc | 15–16 | 1' | Nêu thẳng hạn chế; kết luận |

## Lời thoại từng slide

Lời thoại đầy đủ có sẵn trong slide (nhấn `N`). Tóm tắt ý chính:

1. **Tiêu đề.** Giới thiệu đề tài và mục tiêu trong một câu.
2. **Bài toán.** Chỉ vào đoạn log: "máy chỉ thấy các dòng này". Chỉ sang ô xanh: "cái chúng ta muốn là câu này". Nêu 3 khó khăn: không nhãn, nhiễu, cá nhân.
3. **Phạm vi.** B1 và B2; **nói rõ không làm robot, không làm nhắc nhở** — chủ động nói trước để tránh bị hỏi.
4. **Tài liệu tham khảo.** Nêu đúng tên bài, tác giả, năm. Nhấn mạnh: *kế thừa tư tưởng học không nhãn, nhãn chỉ để đánh giá*; khác dữ liệu nên khác kỹ thuật.
5. **Dữ liệu.** Mô phỏng = đề thi có đáp án; Aruba = dữ liệu thật. Kể ngắn việc tự kiểm định mã phòng (mã 1 đi kèm Sleeping → phòng ngủ) — cho thấy đã làm việc thật với dữ liệu.
6. **B1.** Đọc dãy số 3.397 → 3.339 → 501. Giải thích hai quy tắc tách phiên và vì sao Aruba bắt buộc phải tách theo phòng.
7. **Định nghĩa thói quen.** Slide quan trọng nhất về tư duy. Đọc chậm ba điều kiện. Nói: "điều kiện 1–2 là mật độ, nên em chọn thuật toán mật độ".
8. **DBSCAN.** Giải thích vòng tròn 24 giờ bằng ví dụ 23:50 và 00:10. Nhấn mạnh eps = 0,5 **nghĩa đen là 30 phút**. So sánh nhanh với K-Means.
9. **Kết quả mô phỏng.** Hướng dẫn cách đọc hình: mỗi hàng một người ở một phòng, mỗi chấm một phiên. Đọc 4 con số.
10. **Uống thuốc.** Dừng lại ở slide này — đây là ví dụ của chính đề bài.
11. **Aruba.** Thuật toán chỉ thấy phòng và giờ. Đọc 2 dòng đầu bảng (ngủ, bữa sáng).
12. **Đối chiếu nhãn.** Hai điểm: khớp tốt với thói quen có giờ rõ; phát hiện thói quen phòng tắm mà nhãn gốc bỏ sót. Tự nêu giới hạn phòng khách.
13. **Baseline.** Độ lệch giờ 182 → 10 phút. Kể chuyện baseline biến nhiễu thành "thói quen giả".
14. **Độ nhạy.** "Tham số chọn theo ý nghĩa, không tinh chỉnh theo nhãn."
15. **Hạn chế.** Đọc thẳng, không né.
16. **Kết luận.** Một câu tổng kết, cảm ơn.

---

## Câu hỏi phản biện thường gặp

**1. Tại sao chọn DBSCAN mà không phải K-Means?**
K-Means phải biết trước số thói quen *k* — điều không thể biết với một người lạ — và ép mọi phiên, kể cả đi lại ngẫu nhiên, vào một cụm. DBSCAN tự xác định số cụm và gán nhãn −1 cho nhiễu. Quan trọng hơn, trong không gian đo bằng giờ, hai tham số của DBSCAN trùng với định nghĩa thói quen: `eps` = "lệch bao nhiêu phút vẫn tính là cùng giờ", `min_samples` = "lặp lại ở bao nhiêu phần trăm số ngày".

**2. Sao không dùng LDA như bài báo tham khảo?**
LDA phù hợp khi quan sát là "túi từ" các quan hệ định tính không có trục thời gian rõ ràng. Câu hỏi của đề tài là *khi nào, ở đâu, bao lâu*, dữ liệu có trục giờ tự nhiên, nên phân cụm mật độ trên trục thời gian trả lời trực tiếp và dễ giải thích hơn. Đề tài kế thừa tư tưởng (không nhãn, nhãn chỉ để đánh giá), không kế thừa kỹ thuật.

**3. Nếu đã có nhãn hoạt động, sao không dùng học có giám sát?**
Trong thực tế triển khai, nhà của người dùng **không có nhãn**. Nhãn trong Aruba và trong dữ liệu mô phỏng chỉ dùng để *chấm điểm* xem cụm tìm được có ý nghĩa không. Kết quả phòng tắm 10:22 còn cho thấy học không giám sát tìm được cả thói quen mà người gán nhãn bỏ sót.

**4. eps = 0,5 và 20% số ngày lấy từ đâu? Có phải chỉnh cho đẹp kết quả không?**
Chọn theo ý nghĩa trước khi chạy: 30 phút là độ lệch hợp lý của một thói quen hằng ngày; 20% số ngày để một khung giờ được coi là "dày". Không tinh chỉnh theo nhãn — làm vậy thì thành học có giám sát. Biểu đồ k-distance và bảng độ nhạy xác nhận đây là vùng hợp lý: trên mô phỏng, cả 12 cấu hình đều ra đúng 12 thói quen; trên Aruba, độ thuần giữ 0,77–0,81 với mọi cấu hình.

**5. Sao phải đặt giờ lên vòng tròn?**
Giờ là đại lượng tuần hoàn. 23:50 và 00:10 cách nhau 20 phút, nhưng nếu dùng số 23,83 và 0,17 thì cách nhau 23,7 giờ. Với thói quen đi ngủ quanh nửa đêm (Aruba ngủ lúc ~00:18), không dùng vòng tròn sẽ tách một thói quen thành hai cụm ở hai đầu trục.

**6. Tại sao không chuẩn hoá dữ liệu (StandardScaler)?**
Vì mọi trục đã cùng đơn vị giờ (bán kính 24/2π, thời lượng nhân trọng số 0,5). Chuẩn hoá sẽ phá mất ý nghĩa "eps = 30 phút". Phiên bản đầu của đề tài có chuẩn hoá 10 đặc trưng và thất bại vì trục giờ bị lấn át (slide 13).

**7. Tỷ lệ nhiễu 34–35% có phải quá cao?**
Không. Trên dữ liệu mô phỏng, 164/177 phiên nhiễu là các lần đi ngang ngẫu nhiên được cài sẵn — nhiễu cao là *đúng*. Baseline có nhiễu chỉ 5% nhưng đó là vì nó gom nhiễu thành một "thói quen" giả. Trên Aruba, nhiễu là các lần ở phòng không theo giờ cố định, vốn không phải thói quen.

**8. ARI trên Aruba chỉ 0,36 — có thấp không?**
Thấp hơn mô phỏng là đúng kỳ vọng: (i) 34% thời gian mang nhãn `None`; (ii) vị trí không tương đương hoạt động (ăn và nghỉ đều ở phòng khách); (iii) người thật kém đều đặn. Chỉ số nên xem cùng là độ thuần 79% và độ thuần theo từng thói quen: ngủ 100%, nấu bữa sáng 92%. Baseline trên cùng dữ liệu chỉ đạt ARI 0,03.

**9. Vì sao phòng khách Aruba ra khung giờ rộng 14:19–22:20?**
Người này ngồi phòng khách gần như suốt chiều tối, các phiên phủ kín khoảng thời gian đó với mật độ cao liên tục, DBSCAN nối chúng thành một cụm (hiệu ứng *chaining*). Kết quả vẫn đúng về hành vi ("chiều tối thường ở phòng khách"). Hướng khắc phục: HDBSCAN, cho phép mật độ khác nhau giữa các vùng.

**10. Làm sao biết mã vị trí 9 là "ra ngoài"?**
File tên gọi nó là "Second Bathroom", nhưng: ở đó liên tục trung vị 146 phút, 100% không có hoạt động, và các hoạt động `Leave_Home`/`Enter_Home` xảy ra ở đó. Việc hiệu chỉnh được ghi minh bạch trong `configs/strands_aruba.yaml` và [02_du_lieu.md](02_du_lieu.md); các thói quen chính (ngủ, bếp, phòng khách, phòng tắm) không phụ thuộc vào mã này.

**11. Nhà có hai người thì sao?**
Đề tài giả định biết sự kiện do ai gây ra (`resident_id`). Dữ liệu mô phỏng có hai người và phương pháp tách được thói quen riêng của từng người vì DBSCAN chạy theo từng người. Trong thực tế cần thiết bị định danh (thẻ, vòng đeo tay); tách người từ cảm biến môi trường thuần tuý là một bài toán khác, ngoài phạm vi.

**12. Ứng dụng thực tế là gì?**
Kết quả là danh sách thói quen có khung giờ và tần suất — đầu vào cho các ứng dụng như nhắc uống thuốc khi 20:40 mà chưa thấy phiên bếp–hộp thuốc, hoặc cảnh báo khi giờ ngủ thay đổi đột ngột ở người cao tuổi. Các ứng dụng này nằm ngoài phạm vi đề tài.

**13. Dữ liệu mô phỏng có "dễ quá" không?**
Có chủ đích: nó là bài kiểm tra có đáp án để chứng minh phương pháp đúng khi biết chắc thói quen tồn tại. Dù vậy dữ liệu vẫn có dao động giờ, ngày bỏ lỡ, lịch cuối tuần khác, hoạt động thỉnh thoảng, nhiễu và lỗi dữ liệu. Độ khó thật được kiểm chứng bằng dữ liệu Aruba.

**14. Kết quả có tái lập được không?**
Có. Dữ liệu mô phỏng dùng seed cố định; dữ liệu Aruba tải từ nguồn gốc. Hai lệnh `smart-home run` và `smart-home experiments` tạo lại toàn bộ bảng và hình; 21 kiểm thử tự động (`python -m pytest`) bao phủ tiền xử lý, phân cụm, pipeline và bộ đọc STRANDS.
