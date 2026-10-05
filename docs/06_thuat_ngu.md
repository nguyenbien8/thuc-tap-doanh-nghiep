# 06 · Thuật ngữ

Tra cứu khi gặp từ lạ. Sắp xếp theo chủ đề, không theo abc.

## Dữ liệu

| Thuật ngữ | Nghĩa trong đề tài |
|---|---|
| **Sự kiện (event)** | Một dòng log: lúc t, người p, ở phòng r, cảm biến s có giá trị v |
| **Schema** | Danh sách cột bắt buộc và ý nghĩa của chúng (7 cột, xem [02_du_lieu.md](02_du_lieu.md#4-schema-chung-7-cột--1-cột-nhãn)) |
| **PIR / motion** | Cảm biến hồng ngoại thụ động, kêu khi có người cử động trong phòng |
| **presence** | Loại "cảm biến" đề tài gán cho dữ liệu STRANDS: mỗi phút báo "người đang ở phòng này" |
| **Nhãn (label) / ground truth** | Tên hoạt động thật (`activity_label`). Là đáp án, **chỉ dùng để chấm điểm** |
| **Dữ liệu mô phỏng (synthetic)** | Dữ liệu sinh bằng code theo lịch biết trước |
| **Seed** | Số khởi tạo bộ sinh ngẫu nhiên; cùng seed → cùng dữ liệu |
| **CASAS** | Dự án nhà thông minh của Washington State University; nguồn gốc của dữ liệu Aruba |
| **STRANDS / LCAS** | Dự án robot châu Âu / phòng thí nghiệm của Đại học Lincoln, nơi công bố bộ dữ liệu theo phút |
| **Mã đánh số từ 0 / từ 1** | Mã 0 hay mã 1 ứng với tên đầu tiên trong file `.names` |

## Bước 1 – Tiền xử lý

| Thuật ngữ | Nghĩa |
|---|---|
| **Làm sạch** | Ép kiểu, bỏ dòng hỏng/trùng, điền giá trị thiếu, chuẩn hoá chữ |
| **Median** | Trung vị: giá trị đứng giữa khi sắp xếp. Ít bị ảnh hưởng bởi giá trị lạ hơn trung bình |
| **Phiên (session)** | Một lần một người ở liên tục trong một phòng. Là **đơn vị quan sát** của đề tài |
| **Khoảng lặng (inactivity gap)** | Thời gian giữa hai sự kiện liên tiếp; > 30 phút thì mở phiên mới |
| **Đặc trưng (feature)** | Con số mô tả một phiên (giờ bắt đầu, thời lượng, số sự kiện...) |
| **dominant_room** | Phòng xuất hiện nhiều nhất trong phiên |

## Bước 2 – Phân cụm

| Thuật ngữ | Nghĩa |
|---|---|
| **Học không giám sát** | Tìm cấu trúc trong dữ liệu **mà không có đáp án** để học theo |
| **Phân cụm (clustering)** | Chia các điểm dữ liệu thành các nhóm, các điểm trong nhóm giống nhau |
| **DBSCAN** | *Density-Based Spatial Clustering of Applications with Noise*: phân cụm theo mật độ, có khái niệm nhiễu (Ester et al., 1996) |
| **eps (ε)** | Bán kính lân cận của DBSCAN. Trong đề tài đơn vị là **giờ**: eps = 0,5 ≈ "lệch nhau 30 phút" |
| **min_samples** | Số điểm tối thiểu (tính cả chính nó) trong bán kính eps để một điểm là **điểm lõi** |
| **Điểm lõi (core point)** | Điểm có ≥ min_samples láng giềng trong bán kính eps; là "trung tâm dày đặc" của cụm |
| **Điểm biên (border point)** | Không phải điểm lõi, nhưng nằm trong lân cận của một điểm lõi → vẫn thuộc cụm |
| **Nhiễu (noise), nhãn −1** | Điểm không thuộc cụm nào: hành vi ngẫu nhiên hoặc khác thường |
| **Chaining (nối cụm)** | Khi các điểm dày liên tục thành dải, DBSCAN nối chúng thành một cụm rất dài (phòng khách Aruba) |
| **k-distance** | Khoảng cách từ mỗi điểm đến láng giềng thứ k; vẽ theo thứ tự tăng dần để chọn eps (chỗ đường cong gãy lên) |
| **Mã hoá vòng tròn (cyclic encoding)** | Đặt giờ lên vòng tròn bằng sin/cos để 23:59 gần 00:01 |
| **Trung bình vòng tròn (circular mean)** | Trung bình đúng cho đại lượng tuần hoàn: atan2(trung bình sin, trung bình cos) |
| **Thói quen (habit)** | Cụm có **support ≥ 50%**: cùng người, cùng phòng, cùng giờ, cùng thời lượng, lặp lại ≥ nửa số ngày |
| **Mẫu không thường xuyên** | Cụm có support < 50% (thể dục, lịch cuối tuần) |
| **Support / tần suất** | Số ngày có mẫu ÷ số ngày quan sát |
| **Khung 80%** | Khoảng giữa phân vị 10% và 90% của giờ bắt đầu |
| **StandardScaler / chuẩn hoá z-score** | Biến mỗi cột về trung bình 0, độ lệch chuẩn 1. Đề tài **không dùng** cho phương pháp chính (các trục đã cùng đơn vị giờ) |
| **K-Means, GMM, HDBSCAN, LDA** | Các thuật toán khác đã cân nhắc (xem [04_vi_sao_lam_the_nay.md](04_vi_sao_lam_the_nay.md#d1-dbscan-không-phải-thuật-toán-khác)) |

## Đánh giá

| Thuật ngữ | Nghĩa | Khoảng giá trị |
|---|---|---|
| **Silhouette** | Mỗi điểm gần cụm của mình hơn cụm khác bao nhiêu. Không cần nhãn | −1 → 1, càng cao càng tốt |
| **ARI** (*Adjusted Rand Index*) | Mức trùng khớp giữa cách chia cụm và nhãn thật, đã trừ phần trùng do may rủi | ~0 = ngẫu nhiên, 1 = khớp hoàn toàn |
| **NMI** (*Normalized Mutual Information*) | Biết cụm thì đoán được nhãn đến mức nào | 0 → 1 |
| **Độ thuần (purity)** | Trong mỗi cụm, nhãn đông nhất chiếm bao nhiêu phần; lấy trung bình có trọng số | 0 → 1 |
| **Độ lệch giờ trong cụm (time spread)** | Độ lệch chuẩn giờ bắt đầu trong cụm (phút). Chỉ số riêng của đề tài: cụm có trả lời được "mấy giờ" không | càng nhỏ càng tốt |
| **Baseline** | Phương pháp đối chứng để so sánh (ở đây là phiên bản đầu của đề tài) | |
| **Ablation** | Bỏ một thành phần để xem nó có cần thiết không | |
| **Phân tích độ nhạy** | Đổi tham số trong một lưới giá trị, xem kết quả thay đổi thế nào | |
| **Tái lập (reproducible)** | Người khác chạy lại ra đúng kết quả | |

## Kỹ thuật phần mềm

| Thuật ngữ | Nghĩa |
|---|---|
| **Pipeline** | Chuỗi các bước xử lý nối tiếp: đọc → làm sạch → phiên → cụm → báo cáo |
| **CLI** | Giao diện dòng lệnh; ở đây là lệnh `smart-home` |
| **Config (YAML)** | File tham số; mỗi thí nghiệm một file |
| **Adapter** | Hàm chuyển một định dạng dữ liệu lạ về schema chung (`strands_adapter.py`) |
| **pytest** | Công cụ chạy kiểm thử tự động |
| **venv** | Môi trường Python riêng của dự án (`.venv/`) |
| **`pip install -e .`** | Cài package ở chế độ "sửa code là có hiệu lực ngay", đồng thời tạo lệnh `smart-home` |
