# Kết quả thực nghiệm: `strands_aruba`

> File này được sinh tự động bởi `smart-home run`. Không sửa tay.

## Bước 1 – Tiền xử lý

- Sự kiện thô: **161,280** → sau làm sạch: **161,280** (loại 0).
- Phiên tạo được: **15,176**; giữ lại **3,015** (loại 12,161 phiên quá ngắn).

## Bước 2 – Tìm mẫu thói quen (DBSCAN theo cư dân × phòng)

- Tham số: `eps = 0.5 giờ`, `min_samples = max(5, ⌈0.2 × số ngày⌉)` = {'aruba': 23}, `duration_weight = 0.5`, ngưỡng thói quen `min_support = 50%` số ngày.
- Số cụm: **11**, trong đó **5 thói quen**; tỷ lệ nhiễu: **34.3%** số phiên.
- Silhouette trong từng phòng: 0.600.
- Đối chiếu nhãn thật (không dùng khi huấn luyện): ARI = 0.361, NMI = 0.447, độ thuần = 0.792.

### Thói quen tìm được

| Cụm | Cư dân | Phòng | Giờ điển hình | Khung 80% | Thời lượng TV | Số ngày | Tần suất | Nhãn thật chiếm đa số (độ thuần) |
|---:|---|---|:---:|:---:|---:|---:|---:|---|
| C0 | aruba | kitchen | **09:04** | 08:01–10:18 | 8 phút | 60/112 | 54% | Meal_Preparation (92%) |
| C3 | aruba | living_room | **09:35** | 07:32–11:41 | 11 phút | 108/112 | 96% | Relax (63%) |
| C4 | aruba | living_room | **18:31** | 14:19–22:20 | 23 phút | 112/112 | 100% | Relax (79%) |
| C6 | aruba | master_bathroom | **10:22** | 09:25–11:11 | 12.5 phút | 58/112 | 52% | None (96%) |
| C7 | aruba | master_bedroom | **00:18** | 23:43–00:55 | 332.5 phút | 73/112 | 65% | Sleeping (100%) |

### Mẫu lặp lại nhưng chưa đủ thường xuyên

| Cụm | Cư dân | Phòng | Giờ điển hình | Khung 80% | Thời lượng TV | Số ngày | Tần suất | Nhãn thật chiếm đa số (độ thuần) |
|---:|---|---|:---:|:---:|---:|---:|---:|---|
| C1 | aruba | kitchen | **15:35** | 15:07–16:06 | 8 phút | 30/112 | 27% | None (49%) |
| C2 | aruba | kitchen | **17:50** | 17:14–18:33 | 7 phút | 33/112 | 30% | Meal_Preparation (80%) |
| C5 | aruba | master_bathroom | **07:39** | 07:01–08:17 | 12 phút | 35/112 | 31% | None (98%) |
| C8 | aruba | master_bedroom | **05:46** | 05:19–06:10 | 161 phút | 25/112 | 22% | Sleeping (100%) |
| C9 | aruba | master_bedroom | **11:05** | 10:36–11:30 | 7 phút | 40/112 | 36% | None (94%) |
| C10 | aruba | outside | **11:34** | 11:15–11:47 | 146 phút | 51/112 | 46% | None (100%) |

Ghi chú: *Khung 80%* là khoảng giữa phân vị 10% và 90% của giờ bắt đầu; *Tần suất* = số ngày có mẫu / số ngày quan sát.
