# Hướng dẫn hiểu repo: bắt đầu từ đây

Thư mục `docs/` là **tài liệu học dành cho bạn**, người làm và bảo vệ đề tài. Nó giải thích repo từ gốc: dữ liệu lấy từ đâu, nằm ở đâu, mỗi bước làm gì, và **vì sao làm thế này mà không làm cách khác**.

| Thư mục | Viết cho ai | Mục đích |
|---|---|---|
| `docs/` | **Bạn** | Hiểu sâu để tự tin trả lời mọi câu hỏi |
| `reports/` | **Hội đồng** | Báo cáo nộp: ngắn gọn, trang trọng, trình bày kết quả |

Hai bộ tài liệu có phần trùng nhau, và đó là cố ý: `docs/` giải thích *cách* và *tại sao*, còn `reports/` trình bày *cái gì*.

---

## Lộ trình đọc đầy đủ (~4 giờ)

Đọc đúng thứ tự: mỗi tài liệu dùng kiến thức của tài liệu trước.

| # | Đọc | Thời gian | Sau khi đọc, bạn trả lời được |
|---|---|---|---|
| 1 | [../README.md](../README.md) | 10' | Đề tài làm gì, kết quả chính là gì |
| 2 | [../reports/01_tong_quan_de_tai.md](../reports/01_tong_quan_de_tai.md) | 20' | Bài toán, phạm vi, **định nghĩa thói quen**, liên hệ với bài báo tham khảo |
| 3 | [01_ban_do_repo.md](01_ban_do_repo.md) | 15' | File nào ở đâu, từ đâu ra, cái nào tự sinh, cái nào đưa lên git |
| 4 | **[02_du_lieu.md](02_du_lieu.md)** ★ | 60' | Hai bộ dữ liệu từ đâu ra, file gốc trông thế nào, được biến đổi qua từng giai đoạn ra sao, vì sao chọn bộ này |
| 5 | [03_hanh_trinh_mot_lan_uong_thuoc.md](03_hanh_trinh_mot_lan_uong_thuoc.md) | 20' | Theo chân một lần uống thuốc từ 6 dòng log đến dòng "thói quen", với con số thật ở mỗi bước |
| 6 | [../reports/03_phuong_phap.md](../reports/03_phuong_phap.md) | 30' | Công thức và tham số của B1, B2 |
| 7 | **[04_vi_sao_lam_the_nay.md](04_vi_sao_lam_the_nay.md)** ★ | 45' | Mỗi quyết định thiết kế: các cách khác, vì sao không chọn, cái giá phải trả |
| 8 | [05_doc_code.md](05_doc_code.md) + mở code bên cạnh | 60' | Hàm nào làm gì, các dòng then chốt, test bảo đảm điều gì |
| 9 | [../reports/04_ket_qua_thuc_nghiem.md](../reports/04_ket_qua_thuc_nghiem.md) | 30' | Kết quả, so sánh baseline, độ nhạy, hạn chế |
| 10 | [07_tu_kiem_tra.md](07_tu_kiem_tra.md) | 60' | Tự kiểm tra bằng câu hỏi và bài tập chạy code |
| — | [06_thuat_ngu.md](06_thuat_ngu.md) | tra cứu | Nghĩa của eps, điểm lõi, ARI, ablation... |

★ = hai tài liệu quan trọng nhất.

## Lộ trình nhanh (~1 giờ)

Khi cần nắm ý chính trước:

1. [../README.md](../README.md), phần *Kết quả chính*
2. [03_hanh_trinh_mot_lan_uong_thuoc.md](03_hanh_trinh_mot_lan_uong_thuoc.md): hiểu toàn bộ pipeline qua một ví dụ
3. [02_du_lieu.md](02_du_lieu.md), mục 1, 3.3–3.5 và 6
4. [04_vi_sao_lam_the_nay.md](04_vi_sao_lam_the_nay.md), mục C1, D1, D2, D3

## Trước buổi bảo vệ (~1,5 giờ)

1. [../reports/05_kich_ban_thuyet_trinh.md](../reports/05_kich_ban_thuyet_trinh.md): lời thoại + 14 câu hỏi phản biện
2. Mở [../reports/slide_thuyet_trinh.html](../reports/slide_thuyet_trinh.html), nhấn `N` để xem ghi chú, tập nói một lượt
3. [04_vi_sao_lam_the_nay.md](04_vi_sao_lam_the_nay.md): đọc lại phần *Cái giá phải trả* của từng mục (đây là chỗ hay bị hỏi)
4. [07_tu_kiem_tra.md](07_tu_kiem_tra.md), phần 1: trả lời thành tiếng không cần nhìn đáp án

---

## Nếu chỉ nhớ 5 điều

1. **Dữ liệu:** một bộ *mô phỏng có đáp án* (2 người, 28 ngày) để chứng minh phương pháp đúng, và một bộ *thật* STRANDS Aruba (1 người, 112 ngày, vị trí theo phút) để áp dụng. Nhãn chỉ dùng để chấm điểm.
2. **Bước 1:** gom log thành **phiên** = một lần ở liên tục trong một phòng (tách khi lặng > 30 phút hoặc đổi phòng).
3. **Thói quen** = cùng người, cùng phòng, cùng giờ (±30 phút), cùng thời lượng, lặp lại ≥ 50% số ngày.
4. **Bước 2:** DBSCAN trong không gian đo bằng **giờ** (giờ trên vòng tròn chu vi 24 + log thời lượng), chạy riêng từng người × phòng, nên `eps = 0,5` nghĩa đen là "30 phút".
5. **Kết quả:** mô phỏng 12/12 thói quen (có uống thuốc 20:32, 25/28 ngày); Aruba 5 thói quen (ngủ khớp nhãn 100%, bữa sáng 92%); tốt hơn hẳn cách làm ban đầu (độ lệch giờ 182 → 10 phút).
