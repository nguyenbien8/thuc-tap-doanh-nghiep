# Kết quả thực nghiệm: `demo`

> File này được sinh tự động bởi `smart-home run`. Không sửa tay.

## Bước 1 – Tiền xử lý

- Sự kiện thô: **3,397** → sau làm sạch: **3,339** (loại 58).
- Phiên tạo được: **501**; giữ lại **501** (loại 0 phiên quá ngắn).

## Bước 2 – Tìm mẫu thói quen (DBSCAN theo cư dân × phòng)

- Tham số: `eps = 0.5 giờ`, `min_samples = max(5, ⌈0.2 × số ngày⌉)` = {'resident_01': 6, 'resident_02': 6}, `duration_weight = 0.5`, ngưỡng thói quen `min_support = 50%` số ngày.
- Số cụm: **15**, trong đó **12 thói quen**; tỷ lệ nhiễu: **35.3%** số phiên.
- Silhouette trong từng phòng: 0.908.
- Đối chiếu nhãn thật (không dùng khi huấn luyện): ARI = 0.959, NMI = 0.981, độ thuần = 1.000.

### Thói quen tìm được

| Cụm | Cư dân | Phòng | Giờ điển hình | Khung 80% | Thời lượng TV | Số ngày | Tần suất | Nhãn thật chiếm đa số (độ thuần) |
|---:|---|---|:---:|:---:|---:|---:|---:|---|
| C0 | resident_01 | bedroom | **06:42** | 06:31–06:57 | 15.4 phút | 28/28 | 100% | wake_up (100%) |
| C1 | resident_01 | bedroom | **22:31** | 22:18–22:45 | 10.1 phút | 28/28 | 100% | go_to_bed (100%) |
| C2 | resident_01 | kitchen | **07:33** | 07:23–07:49 | 20.2 phút | 27/28 | 96% | breakfast (100%) |
| C3 | resident_01 | kitchen | **12:03** | 11:52–12:12 | 28.4 phút | 27/28 | 96% | lunch (100%) |
| C4 | resident_01 | kitchen | **18:33** | 18:22–18:45 | 30.4 phút | 27/28 | 96% | dinner (100%) |
| C5 | resident_01 | kitchen | **20:32** | 20:20–20:40 | 2.6 phút | 25/28 | 89% | take_medicine (100%) |
| C6 | resident_01 | living_room | **14:03** | 13:46–14:13 | 57.6 phút | 20/28 | 71% | watch_tv (100%) |
| C8 | resident_02 | bedroom | **07:46** | 07:32–07:57 | 11.2 phút | 20/28 | 71% | wake_up (100%) |
| C10 | resident_02 | bedroom | **23:14** | 23:05–23:25 | 9.4 phút | 28/28 | 100% | go_to_bed (100%) |
| C11 | resident_02 | kitchen | **08:16** | 08:07–08:28 | 15.7 phút | 19/28 | 68% | breakfast (100%) |
| C13 | resident_02 | kitchen | **19:16** | 19:05–19:27 | 27.3 phút | 26/28 | 93% | dinner (100%) |
| C14 | resident_02 | living_room | **20:28** | 20:13–20:38 | 96.5 phút | 22/28 | 79% | watch_tv (100%) |

### Mẫu lặp lại nhưng chưa đủ thường xuyên

| Cụm | Cư dân | Phòng | Giờ điển hình | Khung 80% | Thời lượng TV | Số ngày | Tần suất | Nhãn thật chiếm đa số (độ thuần) |
|---:|---|---|:---:|:---:|---:|---:|---:|---|
| C7 | resident_01 | living_room | **16:55** | 16:37–17:07 | 29 phút | 10/28 | 36% | exercise (100%) |
| C9 | resident_02 | bedroom | **09:14** | 08:54–09:24 | 11.2 phút | 8/28 | 29% | wake_up (100%) |
| C12 | resident_02 | kitchen | **09:45** | 09:35–10:01 | 14 phút | 7/28 | 25% | breakfast (100%) |

Ghi chú: *Khung 80%* là khoảng giữa phân vị 10% và 90% của giờ bắt đầu; *Tần suất* = số ngày có mẫu / số ngày quan sát.
