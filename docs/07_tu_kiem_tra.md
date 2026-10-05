# 07 · Tự kiểm tra: bạn đã hiểu repo chưa?

Hai phần: **câu hỏi** (trả lời bằng lời, như khi bị hội đồng hỏi) và **bài tập thực hành** (sửa tham số, chạy lại, quan sát). Đáp án gợi ý nằm trong thẻ *Đáp án*, hãy tự nghĩ trước khi mở.

> Trước khi làm bài tập: các lệnh dưới đây sẽ **ghi đè** `reports/results/`. Làm xong, chạy lại 4 lệnh ở cuối tài liệu này để khôi phục kết quả chuẩn.

---

## Phần 1 · Câu hỏi

**Dữ liệu**

1. Dòng thứ 1.441 trong `location.min` của Aruba ứng với thời điểm nào?
   <details><summary>Đáp án</summary>Phút thứ 1.440 tính từ 00:00 ngày 1, tức 00:00 ngày 2.</details>

2. Vì sao đề tài kết luận mã vị trí Aruba đánh số từ 1, trái với ví dụ trên trang dataset?
   <details><summary>Đáp án</summary>Mã 0 không xuất hiện; khi đối chiếu với nhãn, mã 1 đi kèm Sleeping (phòng ngủ), 2 với Bed_to_Toilet (nhà tắm), 3 với Relax (phòng khách), 4 với Meal_Preparation (bếp), chỉ khớp khi đánh số từ 1.</details>

3. Vì sao mã 9 bị đổi thành `outside`? Nếu không đổi, kết quả chính có thay đổi không?
   <details><summary>Đáp án</summary>Ở đó trung vị 146 phút, không có hoạt động, và là nơi Leave/Enter_Home. Chỉ đổi <i>tên</i> của một nhóm; DBSCAN chạy theo nhóm nên các thói quen ở phòng ngủ, bếp, phòng khách, phòng tắm không đổi.</details>

4. Cột `activity_label` được dùng ở những chỗ nào trong code?
   <details><summary>Đáp án</summary>Chỉ trong <code>external_scores</code> và <code>build_profiles</code> (dominant_label, label_purity) của discovery.py, và hình <code>label_matrix.png</code>. <code>habit_feature_matrix</code> không đọc nó.</details>

5. Vì sao dữ liệu mô phỏng đặt `min_session_minutes: 0` còn Aruba đặt 5?

**Phương pháp**

6. Giải thích bằng một câu vì sao `eps = 0,5` nghĩa là "30 phút".
   <details><summary>Đáp án</summary>Giờ được đặt trên vòng tròn có chu vi 24, nên khoảng cách giữa hai điểm ≈ số giờ chênh lệch; 0,5 giờ = 30 phút.</details>

7. Bữa tối 18:30 và uống thuốc 20:30 đều ở bếp. Kể ra *hai* lý do chúng không chung cụm.
   <details><summary>Đáp án</summary>(1) Ở bước 1 chúng đã là hai phiên riêng vì cách nhau > 30 phút; (2) ở bước 2 chúng cách nhau ~2,5 "giờ" (2 giờ lệch giờ + thời lượng 3 so với 30 phút), lớn hơn eps 0,5.</details>

8. Vì sao không cho DBSCAN tự đảm nhiệm điều kiện "≥ 50% số ngày"?

9. Với Aruba (112 ngày), `min_samples` bằng bao nhiêu? Vì sao không để cố định là 5?

10. Baseline có tỷ lệ nhiễu 5%, phương pháp đề xuất 35%. Như vậy baseline tốt hơn không?
    <details><summary>Đáp án</summary>Không. Baseline gom 164 lần đi ngang ngẫu nhiên thành một cụm "thói quen" giả; nhiễu thấp vì nó không nhận ra nhiễu. Trong dữ liệu mô phỏng, 35% nhiễu phần lớn chính là các lần đi ngang ngẫu nhiên được cài sẵn.</details>

11. Chỉ ra một điểm yếu của phương pháp và cách khắc phục.

**Repo**

12. Xoá thư mục `data/`. Làm sao để có lại mọi thứ?
13. File nào quyết định lệnh `smart-home` tồn tại?
14. Vì sao `reports/results/` được đưa lên git còn `data/processed/` thì không?

---

## Phần 2 · Bài tập thực hành

Chạy từ thư mục gốc của repo, sau khi đã kích hoạt `.venv`.

### Bài 1 – Chứng minh phương pháp không dùng nhãn

```powershell
python -c "import pandas as pd; pd.read_csv('data/raw/smart_home_events.csv').drop(columns=['activity_label']).to_csv('data/raw/no_label.csv', index=False)"
smart-home run --input data/raw/no_label.csv
```

**Quan sát:** `reports/results/demo/habit_report.md` vẫn có **12 thói quen** giống hệt; chỉ mất dòng ARI/NMI và hình `label_matrix.png`.

### Bài 2 – Đổi eps

Sửa `configs/config.yaml`: `eps_hours: 0.5` → `0.25`, rồi chạy `smart-home run`. Làm lại với `1.5`.

**Câu hỏi:** số thói quen, tỷ lệ nhiễu và khung giờ thay đổi thế nào? Với 1,5 giờ, các thói quen gần nhau (resident_02: ngủ dậy 07:46 và ăn sáng 08:16 ở *khác phòng*; resident_01: bữa tối 18:33 và uống thuốc 20:32 ở *cùng phòng*) có bị gộp không? Vì sao?

### Bài 3 – Đổi ngưỡng thói quen

`min_support: 0.5` → `0.3`. **Dự đoán trước**: mẫu nào sẽ "được thăng hạng" thành thói quen? (Gợi ý: xem cột tần suất của các mẫu không thường xuyên.) Chạy và kiểm tra.

### Bài 4 – Tắt tách phiên theo phòng

`split_on_room_change: true` → `false`, chạy lại cho cả hai config. So sánh với bảng *ablation* trong [reports/04_ket_qua_thuc_nghiem.md](../reports/04_ket_qua_thuc_nghiem.md#43-so-sánh-với-cách-làm-ban-đầu-baseline-và-ablation). Vì sao Aruba mất hết cụm?

### Bài 5 – Thêm một thói quen vào dữ liệu mô phỏng

Trong `demo.py`, thêm vào lịch của resident_02 một dòng:

```python
Activity("take_medicine", "kitchen", 21.5, 3, 0.9),
```

Chạy `smart-home generate-demo` rồi `smart-home run`. Thói quen mới có xuất hiện với giờ ~21:30 không? Nó có bị gộp với `watch_tv` (20:30, phòng khách) không, và vì sao?

### Bài 6 – Theo dõi một phiên bất kỳ

Làm lại [03_hanh_trinh_mot_lan_uong_thuoc.md](03_hanh_trinh_mot_lan_uong_thuoc.md) cho **một phiên nhiễu** (`random_visit`): nó thuộc phiên nào, điểm 3D là gì, vì sao không đủ láng giềng?

---

## Khôi phục kết quả chuẩn sau khi làm bài tập

Hoàn tác bằng tay các thay đổi trong `configs/` và `demo.py`, xoá `data/raw/no_label.csv`, rồi chạy:

> Chỉ dùng `git checkout -- configs src` để hoàn tác **sau khi đã commit** bản chuẩn của repo. Nếu chưa commit, lệnh này sẽ đưa code về phiên bản cũ và làm mất toàn bộ thay đổi.

```powershell
smart-home generate-demo
smart-home run
smart-home run --config configs/strands_aruba.yaml
smart-home experiments
```

Kết quả phải khớp với số liệu trong báo cáo (demo: 15 cụm / 12 thói quen; Aruba: 11 cụm / 5 thói quen).
