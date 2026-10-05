# 02 · Dữ liệu: lấy từ đâu, trông như thế nào, biến đổi ra sao

Đây là tài liệu quan trọng nhất trong bộ. Mọi quyết định thuật toán đều xuất phát từ việc **dữ liệu trông như thế nào**. Tất cả ví dụ dưới đây là **dòng thật**, copy từ các file trong repo.

Nội dung:

1. [Hai bộ dữ liệu và lý do dùng cả hai](#1-hai-bộ-dữ-liệu-và-lý-do-dùng-cả-hai)
2. [Bộ 1 – Dữ liệu mô phỏng](#2-bộ-1--dữ-liệu-mô-phỏng)
3. [Bộ 2 – STRANDS Aruba (dữ liệu thật)](#3-bộ-2--strands-aruba-dữ-liệu-thật)
4. [Schema chung: 7 cột + 1 cột nhãn](#4-schema-chung-7-cột--1-cột-nhãn)
5. [Dữ liệu qua từng giai đoạn của pipeline](#5-dữ-liệu-qua-từng-giai-đoạn-của-pipeline)
6. [Cột nhãn: vì sao có mà không dùng](#6-cột-nhãn-vì-sao-có-mà-không-dùng)
7. [Vì sao chọn các bộ dữ liệu này mà không phải bộ khác](#7-vì-sao-chọn-các-bộ-dữ-liệu-này-mà-không-phải-bộ-khác)
8. [Dùng dữ liệu của riêng bạn](#8-dùng-dữ-liệu-của-riêng-bạn)
9. [Các "bẫy" dữ liệu cần biết](#9-các-bẫy-dữ-liệu-cần-biết)

---

## 1. Hai bộ dữ liệu và lý do dùng cả hai

| | Bộ 1 – Mô phỏng | Bộ 2 – STRANDS Aruba |
|---|---|---|
| **Câu hỏi nó trả lời** | "Nếu thói quen *chắc chắn* tồn tại, phương pháp có tìm ra không?" | "Trên người thật, phương pháp tìm ra được gì?" |
| **Nguồn** | Tự sinh bằng code (`demo.py`) | Tải từ Đại học Lincoln (dự án STRANDS) |
| **Loại tín hiệu** | Sự kiện cảm biến rời rạc (chuyển động, cửa, nhiệt độ...) | Vị trí (phòng) của người, **mỗi phút một dòng** |
| **Có đáp án?** | Có, biết chính xác từng thói quen | Có nhãn do chuyên gia gán, nhưng 34% thời gian là `None` |
| **Quy mô** | 2 người × 28 ngày, 3.397 dòng | 1 người × 112 ngày, 161.280 dòng |
| **File gốc** | `data/raw/smart_home_events.csv` | `data/raw/strands/aruba/*.min`, `*.names` |

**Vì sao cần cả hai?** Chỉ có dữ liệu thật thì khi kết quả không đẹp, bạn không biết lỗi do phương pháp hay do dữ liệu (người đó vốn không có thói quen rõ). Chỉ có dữ liệu mô phỏng thì bị chê "tự ra đề tự giải". Dùng cả hai là cách làm chuẩn trong nghiên cứu: **kiểm chứng trên dữ liệu có đáp án, rồi áp dụng lên dữ liệu thật**.

---

## 2. Bộ 1 – Dữ liệu mô phỏng

### 2.1. Lấy từ đâu

Không tải về đâu cả, mà được **sinh bằng code** tại [src/smart_home_patterns/demo.py](../src/smart_home_patterns/demo.py):

```powershell
smart-home generate-demo        # ghi ra data/raw/smart_home_events.csv
```

Tham số lấy từ `configs/config.yaml`: `random_seed: 42`, `demo_days: 28`. Ngày bắt đầu cố định là **thứ Hai 02/06/2025** (`START_DATE` trong `demo.py`). Cùng seed thì chạy trên máy nào, bao nhiêu lần cũng ra **đúng từng dòng giống nhau**; có test `test_demo_is_reproducible` kiểm tra điều này.

### 2.2. Cách một ngày được sinh ra

Với mỗi ngày, với mỗi cư dân, code đi qua lịch sinh hoạt (`RESIDENTS` trong `demo.py`):

```text
for mỗi ngày d trong 28 ngày:
    for mỗi cư dân:
        for mỗi hoạt động trong lịch của người đó:
            tung xúc xác: nếu > xác suất của hoạt động → hôm nay bỏ qua
            giờ bắt đầu = giờ trung bình (+1,5h nếu cuối tuần và hoạt động có lệch cuối tuần)
                          + nhiễu ngẫu nhiên ~ N(0, 10 phút)
            nếu trùng với hoạt động trước → dời ra sau 3 phút   (một người không làm 2 việc cùng lúc)
            thời lượng = thời lượng trung bình × hệ số ngẫu nhiên (log-normal, σ = 0,2 ≈ ±20%)
            sinh các sự kiện cảm biến của hoạt động (mục 2.3)
        thêm 3 "lần đi ngang ngẫu nhiên" (mục 2.4)
thêm lỗi dữ liệu (mục 2.5), rồi xáo trộn thứ tự toàn bộ file
```

Lịch sinh hoạt đầy đủ nằm trong [reports/02_du_lieu.md](../reports/02_du_lieu.md#lịch-sinh-hoạt-cài-sẵn). Tóm tắt: resident_01 là người hưu trí rất đều (8 hoạt động, có **uống thuốc 20:30**, có **tập thể dục chỉ 30% số ngày**); resident_02 là người đi làm (5 hoạt động, **dậy muộn 1,5 giờ vào cuối tuần**).

### 2.3. Một hoạt động sinh ra những dòng nào

Mỗi phòng có một bộ cảm biến cố định (`_ROOM_SENSORS`):

| Phòng | Cảm biến | Giá trị |
|---|---|---|
| bedroom | motion, light, door | 1 · ~120 lux · 1 |
| kitchen | motion, door, temperature, light | 1 · 1 · ~23 °C · ~320 lux |
| living_room | motion, power (TV), light | 1 · 1 · ~250 lux |
| bathroom, hallway | motion | 1 |
| *riêng hoạt động take_medicine* | + **pillbox** (hộp thuốc) | 1 |

Khi một hoạt động bắt đầu: **mọi cảm biến của phòng kích hoạt**, cách nhau 30 giây. Sau đó **cảm biến chuyển động kích hoạt lại khoảng 5 phút một lần** (±1 phút) cho đến khi hết thời lượng, và có một lần chuyển động cuối cùng lúc rời phòng.

Ví dụ thật: lần uống thuốc ngày 03/06 của resident_01 (6 dòng, lấy từ `data/raw/smart_home_events.csv` rồi sắp xếp theo giờ):

```csv
timestamp,resident_id,room,sensor_type,sensor_id,value,event_type,activity_label
2025-06-03 20:28:26,resident_01,kitchen,motion,kitchen_motion,1.00,motion,take_medicine
2025-06-03 20:28:56,resident_01,kitchen,door,kitchen_door,1.00,open,take_medicine
2025-06-03 20:29:26,resident_01,kitchen,temperature,kitchen_temperature,22.48,reading,take_medicine
2025-06-03 20:29:56,resident_01,kitchen,light,kitchen_light,333.38,reading,take_medicine
2025-06-03 20:30:26,resident_01,kitchen,pillbox,kitchen_pillbox,1.00,open,take_medicine
2025-06-03 20:31:24,resident_01,kitchen,motion,kitchen_motion,1.00,motion,take_medicine
```

Hoạt động này ngắn (~3 phút) nên chỉ có một lượt "mọi cảm biến" và một lần chuyển động cuối. Bữa tối 35 phút sẽ có thêm khoảng 7 lần chuyển động xen giữa.

### 2.4. Nhiễu hành vi

Mỗi người, mỗi ngày có **3 lần đi ngang ngẫu nhiên** (`_random_visits`): một giờ bất kỳ trong 24h, một phòng bất kỳ trong {bathroom, hallway, living_room}, gồm 1–3 sự kiện chuyển động cách nhau 2 phút. Nhãn là `random_visit`. Đây là "đi uống nước lúc nửa đêm", "đi ngang hành lang", tức những thứ **không phải thói quen**. Phương pháp tốt phải gán chúng là nhiễu (kết quả: 164/164 phiên như vậy bị gán nhiễu).

### 2.5. Lỗi dữ liệu được cài cố ý

Dữ liệu cảm biến thật luôn bẩn. Hàm `_inject_quality_issues` cài các lỗi sau để bước tiền xử lý có việc thật để làm:

| Lỗi | Số dòng | Dòng thật trong file | Cách bước 1 xử lý |
|---|---:|---|---|
| Timestamp hỏng | 8 | `not-a-timestamp,resident_02,kitchen,motion,kitchen_motion,1.0,motion,breakfast` | Ép kiểu thành NaT → **bỏ dòng** |
| Thiếu giá trị | 33 | `2025-06-13 18:37:07,resident_01,kitchen,light,kitchen_light,,reading,dinner` | **Điền** median của loại cảm biến `light` |
| Tên phòng lộn xộn | 67 | `2025-06-14 06:47:22,resident_01, Bedroom ,motion,...` | Cắt khoảng trắng + chữ thường → `bedroom` |
| Dòng trùng lặp | 50 | (một dòng xuất hiện 2 lần) | **Bỏ** bản trùng |
| Thứ tự lộn xộn | toàn bộ | 5 dòng đầu file thuộc 5 ngày khác nhau | Sắp xếp theo cư dân → thời gian |

Kết quả: 3.397 dòng thô → **3.339 dòng sạch** (bỏ 50 dòng trùng + 8 dòng hỏng giờ).

### 2.6. Thống kê

| | |
|---|---|
| Dòng theo cư dân | resident_01: 1.925 · resident_02: 1.472 |
| Dòng theo loại cảm biến | motion 2.550 · light 329 · door 277 · temperature 161 · power 54 · pillbox 26 |
| Dòng theo nhãn | watch_tv 809 · dinner 586 · breakfast 445 · wake_up 358 · random_visit 343 · go_to_bed 311 · lunch 291 · take_medicine 154 · exercise 100 |

---

## 3. Bộ 2 – STRANDS Aruba (dữ liệu thật)

### 3.1. Lấy từ đâu: chuỗi nguồn gốc

```text
CASAS (Washington State University)          ← thu thập gốc: căn hộ "Aruba", một phụ nữ cao tuổi sống một mình,
   │                                            hàng chục cảm biến chuyển động/cửa, có chuyên gia gán nhãn hoạt động
   ▼
STRANDS / LCAS (University of Lincoln, UK)   ← trích 16 tuần, chuyển thành "mỗi phút: người ở phòng nào, làm gì"
   │                                            dùng trong bài Coppola et al., ECAI 2016
   ▼
activity.zip (31 kB) trên trang dataset      ← link được đưa trong đề bài
   │
   ▼  smart-home download-strands            ← hàm download_strands() trong strands_adapter.py
data/raw/strands/aruba/, data/raw/strands/witham/
```

- Trang dữ liệu: <https://lcas.lincoln.ac.uk/nextcloud/shared/datasets/activity.html>
- File tải: `https://lcas.lincoln.ac.uk/nextcloud/shared/datasets/activity/activity.zip`
- **Điều kiện sử dụng** (ghi trên trang): trích dẫn Coppola et al. (2016); nếu dùng Aruba thì trích dẫn thêm bài CASAS của Cook (2010). Cả hai đều có trong phần tài liệu tham khảo của báo cáo.

STRANDS là dự án robot châu Âu. Bài báo tham khảo của đề tài (Duckworth et al., 2019) cũng thuộc dự án này, nhưng dùng dữ liệu **camera trên robot**. Bộ *Long-term person activity* ở link đề bài là một bộ dữ liệu khác của cùng dự án, và nó mới là dữ liệu **nhà thông minh**.

### 3.2. Trong file zip có gì

```text
data/raw/strands/
├── aruba/                  ← ĐỀ TÀI DÙNG
│   ├── location.min        161.280 dòng  (322 kB)
│   ├── activity.min        161.280 dòng  (325 kB)
│   ├── location.names      10 dòng
│   └── activity.names      12 dòng
└── witham/                 ← KHÔNG dùng (văn phòng, xem mục 7)
    ├── location.min         30.782 dòng  (~21 ngày)
    ├── activity.min         30.782 dòng
    ├── location.names
    └── activity.names
```

### 3.3. Đọc file `.min` như thế nào

Mỗi file `.min` chỉ có **một số nguyên trên mỗi dòng**, không có tiêu đề, không có giờ. **Dòng thứ N là phút thứ N−1 tính từ 00:00 ngày đầu tiên.**

- Dòng 1 → 00:00 ngày 1; dòng 61 → 01:00 ngày 1; dòng 1.441 → 00:00 ngày 2.
- 161.280 dòng ÷ 1.440 phút/ngày = **112 ngày** = 16 tuần.

Số trong `location.min` là **mã phòng**, số trong `activity.min` là **mã hoạt động**. Tên tương ứng nằm trong file `.names`:

| Mã hoạt động | `activity.names` | | Mã vị trí | `location.names` (đã hiệu chỉnh) |
|---:|---|---|---:|---|
| 0 | None *(không gán nhãn)* | | 1 | Master Bedroom *(phòng ngủ chính)* |
| 1 | Bed_to_Toilet | | 2 | Master Bathroom *(phòng tắm chính)* |
| 2 | Eating | | 3 | Living Room |
| 3 | Enter_Home | | 4 | Kitchen |
| 4 | Housekeeping | | 5 | Junction *(chỗ giao lối đi)* |
| 5 | Leave_Home | | 6 | Corridor |
| 6 | Meal_Preparation | | 7 | Second Bedroom |
| 7 | Relax | | 8 | Office |
| 8 | Resperate *(thiết bị thở, sai chính tả gốc)* | | 9 | ~~Second Bathroom~~ → **outside** |
| 9 | Sleeping | | 10 | Outside *(không xuất hiện)* |
| 10 | Wash_Dishes | | | |
| 11 | Work | | | |
| 13 | *(không có tên, 53 phút)* → `unknown_13` | | | |

Hai điểm bất thường trong bảng (mã vị trí đánh số từ 1, mã 9 bị đổi tên) được giải thích ở mục 3.5.

### 3.4. "Đọc" một buổi sáng thật của bà cụ

Ghép hai file theo từng dòng, rồi chỉ in những phút mà *vị trí hoặc hoạt động thay đổi* trong ngày đầu tiên:

```text
dòng    giờ     vị trí → tên            hoạt động → tên
   1    00:00   1 master_bedroom        0 None
   5    00:04   1 master_bedroom        9 Sleeping           ← ngủ (đã ngủ từ trước nửa đêm)
 342    05:41   2 master_bathroom       1 Bed_to_Toilet      ← dậy đi vệ sinh
 345    05:44   1 master_bedroom        9 Sleeping           ← ngủ tiếp
 483    08:02   2 master_bathroom       0 None               ← thức dậy
 488    08:07   3 living_room           0 None
 492    08:11   4 kitchen               0 None
 493    08:12   4 kitchen               6 Meal_Preparation   ← nấu bữa sáng
 508    08:27   3 living_room           6 Meal_Preparation
 ...
 571    09:30   3 living_room           7 Relax              ← ngồi phòng khách
```

Bạn có thể tự tái hiện bảng trên bằng lệnh bash:

```bash
paste data/raw/strands/aruba/location.min data/raw/strands/aruba/activity.min \
  | awk 'NR<=1440 && ($0!=p){printf "%d %02d:%02d %s\n", NR, int((NR-1)/60), (NR-1)%60, $0} {p=$0}'
```

Đoạn này cho thấy ngay đặc điểm của dữ liệu: **người thật đi lại lắt nhắt**. Từ 08:02 đến 09:30, bà đổi phòng hơn 15 lần, nhiều lần chỉ ở 1–2 phút. Đó là lý do bước 1 phải **bỏ các phiên dưới 5 phút** (mục 5.3).

### 3.5. Kiểm định mã phòng: đánh số từ 0 hay từ 1?

Trang dữ liệu nói *"số 0 ở dòng 10 của location.min nghĩa là Master bedroom"*, tức là đánh số từ 0. Nhưng trong `location.min` của Aruba, **mã 0 không xuất hiện lần nào**, còn mã 9 lại xuất hiện 22.648 lần. Hai cách hiểu cho ra kết quả rất khác nhau, nên đề tài kiểm tra bằng cách **đếm xem mỗi mã vị trí đi kèm hoạt động nào nhiều nhất**:

| Mã vị trí | Hoạt động đi kèm nhiều nhất | Nếu đánh số từ **0** | Nếu đánh số từ **1** | Hợp lý? |
|---:|---|---|---|---|
| 1 | Sleeping (49.004 phút) | Master **Bathroom** | Master **Bedroom** | Từ 1 ✔ (không ai ngủ 49.000 phút trong nhà tắm) |
| 2 | Bed_to_Toilet (196) | Living Room | Master Bathroom | Từ 1 ✔ |
| 3 | Relax (44.216), Eating (1.563) | Kitchen | Living Room | Từ 1 ✔ |
| 4 | Meal_Preparation (4.911), Wash_Dishes (285) | Junction | Kitchen | Từ 1 ✔ |
| 9 | None (22.496) | Outside | Second Bathroom | **Mâu thuẫn** ✘ |

Kết luận: **mã vị trí đánh số từ 1**. Mã hoạt động thì đánh số từ 0, vì mã 0 = None xuất hiện rất nhiều và mọi hoạt động khớp với phòng tương ứng.

Riêng **mã 9**: theo cách đánh từ 1, đó là "Second Bathroom". Nhưng mỗi lần ở đó kéo dài trung vị **146 phút**, **100% không có hoạt động nào**, và các hoạt động `Leave_Home` / `Enter_Home` (rời nhà / về nhà) xảy ra ở đó. Ở phòng tắm phụ 2,5 giờ không làm gì là vô lý, nên mã 9 gần như chắc chắn là **ra ngoài**. Đề tài ghi đè có chủ đích và minh bạch trong `configs/strands_aruba.yaml`:

```yaml
location_base: 1
location_overrides: {9: outside}
```

Code đếm trên có thể chạy lại bằng lệnh: `paste data/raw/strands/aruba/activity.min data/raw/strands/aruba/location.min | sort | uniq -c | sort -k2n -k1nr`.

> Đây là một điểm rất đáng kể khi bảo vệ: **bạn không tin mù quáng vào tài liệu của dataset, mà kiểm tra chéo bằng chính dữ liệu**.

### 3.6. Chuyển sang schema của đề tài

Hàm `load_strands` trong [strands_adapter.py](../src/smart_home_patterns/strands_adapter.py) biến **mỗi phút thành một sự kiện "presence"** (người có mặt ở phòng):

| Cột | Cách tạo | Ví dụ |
|---|---|---|
| `timestamp` | ngày danh nghĩa `2010-11-04` + (số dòng − 1) phút | `2010-11-04 06:58:00` |
| `resident_id` | tên thư mục, hoặc giá trị trong config | `aruba` |
| `room` | tên vị trí theo mã (đánh số từ 1, có ghi đè), chữ thường, `_` thay khoảng trắng | `master_bedroom` |
| `sensor_type`, `event_type` | cố định | `presence` |
| `sensor_id` | `loc_` + mã gốc, giữ lại để truy vết | `loc_1` |
| `value` | cố định | `1.0` |
| `activity_label` | tên hoạt động theo mã, **chỉ để đánh giá** | `Sleeping` |

Dòng thật sau khi chuyển đổi (trong `data/processed/strands_aruba/clean_events.csv`, đã có thêm 2 cột phiên của bước 1):

```csv
timestamp,resident_id,room,sensor_type,sensor_id,value,event_type,activity_label,session_id,session_key
2010-11-04 06:58:00,aruba,master_bedroom,presence,loc_1,1.0,presence,Sleeping,2,aruba_2
2010-11-04 06:59:00,aruba,master_bedroom,presence,loc_1,1.0,presence,Sleeping,2,aruba_2
```

**Vì sao mỗi phút một sự kiện**, thay vì chỉ ghi lúc đổi phòng? Vì như vậy nó giống hệt tín hiệu của một cảm biến định vị thật: cứ đều đặn báo "người đang ở đây". Nhờ đó cùng một pipeline xử lý được cả hai bộ dữ liệu mà không cần viết nhánh code riêng. Cái giá phải trả là file `clean_events.csv` nặng 14,6 MB, chấp nhận được.

**Ngày tháng là danh nghĩa.** File `.min` không có ngày thật. `2010-11-04` chỉ là ngày giả định cho dễ đọc (bộ CASAS Aruba gốc bắt đầu khoảng thời gian này, nhưng không chắc tập con 16 tuần bắt đầu đúng ngày đó). Vì vậy đề tài **không kết luận gì về thứ trong tuần** trên Aruba.

### 3.7. Thống kê sau chuyển đổi

| Phòng | Số phút | % | | Hoạt động (nhãn) | Số phút |
|---|---:|---:|---|---|---:|
| living_room | 57.999 | 36,0% | | None | 55.036 (34%) |
| master_bedroom | 55.645 | 34,5% | | Sleeping | 50.426 |
| outside | 22.648 | 14,0% | | Relax | 45.397 |
| kitchen | 8.847 | 5,5% | | Meal_Preparation | 5.738 |
| corridor | 6.147 | 3,8% | | Work | 1.656 |
| master_bathroom | 4.936 | 3,1% | | Eating | 1.614 |
| second_bedroom | 3.309 | 2,1% | | *các nhãn khác* | < 700 mỗi nhãn |
| junction + office | 1.749 | 1,1% | | | |

---

## 4. Schema chung: 7 cột + 1 cột nhãn

Cả hai bộ dữ liệu đều được đưa về một bảng sự kiện có 7 cột bắt buộc (`REQUIRED_COLUMNS` trong `preprocessing.py`):

| Cột | Kiểu | Ý nghĩa | Mô phỏng | Aruba |
|---|---|---|---|---|
| `timestamp` | ngày giờ | Lúc xảy ra sự kiện | giây | phút |
| `resident_id` | chuỗi | Ai gây ra sự kiện | resident_01/02 | aruba |
| `room` | chuỗi | Ở phòng nào | 5 phòng | 9 vị trí |
| `sensor_type` | chuỗi | Loại cảm biến | motion, door, light... | presence |
| `sensor_id` | chuỗi | Thiết bị cụ thể | kitchen_pillbox | loc_4 |
| `value` | số | Giá trị đo | 1 hoặc số đo | 1 |
| `event_type` | chuỗi | Kiểu sự kiện | motion, open, reading, on | presence |
| `activity_label` | chuỗi, **tuỳ chọn** | Nhãn thật, chỉ để chấm điểm | tên hoạt động cài sẵn | nhãn của CASAS |

**Vì sao cần một schema chung?** Để thuật toán không phụ thuộc vào nguồn dữ liệu. Muốn thêm nguồn mới, bạn chỉ cần viết một hàm chuyển đổi (như `load_strands`), không phải sửa bước 1 hay bước 2.

**Giả định ngầm quan trọng:** mỗi sự kiện đều biết thuộc về ai (`resident_id`). Với cảm biến môi trường ở nhà có nhiều người, điều này cần thêm thiết bị định danh (thẻ, vòng đeo tay). Aruba là nhà một người nên không có vấn đề này.

---

## 5. Dữ liệu qua từng giai đoạn của pipeline

```text
 data/raw/…                    data/processed/<tên>/          data/processed/<tên>/         reports/results/<tên>/
 ┌──────────────┐  làm sạch   ┌──────────────────┐  gộp    ┌─────────────────┐  DBSCAN  ┌──────────────┐
 │ sự kiện thô  │ ──────────► │ clean_events.csv │ ──────► │  sessions.csv   │ ───────► │  habits.csv  │
 │ 1 dòng =     │  gom phiên  │ 1 dòng = 1 sự    │  theo   │ 1 dòng = 1 phiên│  + mô tả │ 1 dòng = 1   │
 │ 1 sự kiện    │             │ kiện + mã phiên  │  phiên  │ + cột cluster   │          │ mẫu thói quen│
 └──────────────┘             └──────────────────┘         └─────────────────┘          └──────────────┘
  mô phỏng: 3.397               3.339                         501                          15 (12 thói quen)
  Aruba:  161.280               161.280                       15.176 → giữ 3.015           11 (5 thói quen)
```

### 5.1. Giai đoạn 0 → 1: `clean_events.csv`

Giữ nguyên các cột gốc (đã được làm sạch) và **thêm 2 cột**:

| Cột thêm | Ý nghĩa | Ví dụ |
|---|---|---|
| `session_id` | Số thứ tự phiên của cư dân đó, bắt đầu từ 0 | `2` |
| `session_key` | `resident_id` + `_` + `session_id`, là khoá duy nhất của phiên | `aruba_2` |

Quy tắc mở phiên mới (hàm `create_sessions`): với cùng một người, dòng hiện tại mở phiên mới nếu **cách dòng trước > 30 phút** HOẶC **ở phòng khác dòng trước**.

### 5.2. Giai đoạn 1 → 2: `sessions.csv`, một dòng cho mỗi phiên

Đây là bảng quan trọng nhất. Có 25 cột, chia theo **mục đích sử dụng**:

| Nhóm | Cột | Ý nghĩa | Dùng để |
|---|---|---|---|
| Định danh | `session_key`, `resident_id` | Phiên nào, của ai | Chia nhóm |
| **Thời gian** | `start_time`, `end_time` | Giờ đầu, giờ cuối của phiên | |
| | **`start_hour`** | Giờ bắt đầu dạng số thập phân (20:28:26 → 20,47) | **Phân cụm** |
| | **`duration_minutes`** | `end_time − start_time` (phút) | **Phân cụm** |
| | `hour_sin`, `hour_cos` | Giờ bắt đầu đặt trên vòng tròn | Baseline, tham khảo |
| **Ngữ cảnh** | **`dominant_room`** | Phòng xuất hiện nhiều nhất trong phiên | **Chia nhóm trước khi phân cụm** |
| Mô tả | `event_count` | Số sự kiện | Diễn giải, baseline |
| | `unique_rooms`, `unique_sensors` | Số phòng / số thiết bị khác nhau | Diễn giải, baseline |
| | `motion_count`, `door_count` | Số lần chuyển động / mở cửa | Baseline |
| | `temperature_mean`, `light_mean` | Nhiệt độ, ánh sáng trung bình | Baseline |
| | `dominant_event_type`, `sensor_types` | Loại sự kiện chính; tổ hợp cảm biến (vd `door|light|motion|pillbox|temperature`) | Diễn giải ("có hộp thuốc") |
| Lịch | `date` | Ngày của giờ bắt đầu | **Đếm số ngày** (tần suất) |
| | `weekday`, `weekday_sin`, `weekday_cos` | Thứ trong tuần | Chưa dùng (hướng phát triển) |
| Đánh giá | `activity_label` | Nhãn chiếm đa số trong phiên | **Chỉ chấm điểm** |
| **Kết quả** | **`cluster`** | Mã cụm; **−1 = nhiễu** | Do bước 2 thêm vào |
| | **`is_habit`** | Cụm có đạt ngưỡng ≥ 50% số ngày không | Do bước 2 thêm vào |

Chú ý: trong 25 cột, **thuật toán phân cụm chỉ dùng 2 cột** (`start_hour`, `duration_minutes`), cộng thêm 2 cột để chia nhóm (`resident_id`, `dominant_room`) và `date` để đếm ngày. Các cột còn lại phục vụ việc diễn giải và so sánh với baseline. Lý do cho lựa chọn này nằm ở [04_vi_sao_lam_the_nay.md](04_vi_sao_lam_the_nay.md).

Nếu phiên không có cảm biến nhiệt độ/ánh sáng, `temperature_mean`/`light_mean` được điền **giá trị trung bình của toàn bộ dữ liệu**, không điền 0, vì 0 °C là một nhiệt độ có thật. Aruba không có cảm biến nhiệt độ nào nên toàn bộ cột này bằng 0; điều đó không ảnh hưởng gì vì phương pháp chính không dùng cột này.

**Ví dụ thật: phiên của Aruba sáng ngày đầu** (khớp với mục 3.4):

| session_key | start → end | phút | phòng | nhãn | cluster | Chuyện gì xảy ra |
|---|---|---:|---|---|---:|---|
| aruba_0 | 00:00 → 05:40 | 340 | master_bedroom | Sleeping | 7 | Thói quen *đi ngủ* (thật ra bà ngủ từ trước 00:00; dữ liệu bắt đầu lúc nửa đêm nên phiên đầu bị cắt) |
| aruba_1 | 05:41 → 05:43 | 2 | master_bathroom | Bed_to_Toilet | — | **Bị bỏ** vì < 5 phút |
| aruba_2 | 05:44 → 08:01 | 137 | master_bedroom | Sleeping | 8 | Mẫu "ngủ tiếp sau khi dậy giữa đêm" (22% số ngày) |
| aruba_6 | 08:11 → 08:26 | 15 | kitchen | Meal_Preparation | 0 | Thói quen *nấu bữa sáng* |
| aruba_13 | 08:40 → 08:57 | 17 | corridor | None | −1 | Nhiễu |
| aruba_18 | 09:28 → 09:35 | 7 | living_room | Relax | 3 | Thói quen *phòng khách buổi sáng* |

### 5.3. Vì sao Aruba bỏ tới 12.161 / 15.176 phiên?

Vì 80% số phiên (12.161/15.176) ngắn hơn 5 phút. Phần lớn là **đi ngang qua** (hành lang 1 phút, ghé bếp 2 phút), như đã thấy ở buổi sáng trong mục 3.4. Với `min_session_minutes: 5`, những phiên này bị loại khỏi bảng phiên. Chúng **vẫn còn** trong `clean_events.csv`, chỉ không đưa vào phân cụm. Trung vị thời lượng các phiên còn lại là 15 phút, lớn nhất 646 phút (một đêm ngủ dài).

Dữ liệu mô phỏng thì đặt `min_session_minutes: 0`. Đây là chủ đích: để các lần đi ngang ngẫu nhiên (thường chỉ 0–4 phút) **đi tiếp vào bước 2**, nhằm kiểm tra khả năng tự đánh dấu nhiễu của DBSCAN.

### 5.4. Giai đoạn 2 → 3: `habits.csv`, một dòng cho mỗi mẫu

Dòng thật: thói quen uống thuốc (cụm 5 của dữ liệu mô phỏng):

| Cột | Giá trị | Ý nghĩa |
|---|---|---|
| `cluster` | 5 | Mã cụm |
| `resident_id`, `room` | resident_01, kitchen | Ai, ở đâu |
| `typical_start` | **20:32** | Giờ điển hình (trung bình *vòng tròn*) |
| `window_start` – `window_end` | 20:20 – 20:40 | 80% số lần bắt đầu trong khoảng này |
| `start_std_minutes` | 7,7 | Độ lệch chuẩn giờ bắt đầu, càng nhỏ càng đúng giờ |
| `median_duration_minutes` | 2,6 | Thời lượng trung vị |
| `sessions` | 25 | Số phiên trong cụm |
| `days_present` / `days_observed` | 25 / 28 | Số ngày có mẫu / số ngày quan sát |
| `support` | 0,893 | = 25/28 |
| `is_habit` | True | support ≥ 0,5 |
| `sensor_types` | door\|light\|motion\|**pillbox**\|temperature | Cảm biến đặc trưng |
| `mean_start_hour` | 20,5261 | Giờ điển hình dạng số (dùng để vẽ) |
| `dominant_label`, `label_purity` | take_medicine, 1,0 | **Chỉ để đánh giá**: 100% phiên trong cụm đúng là uống thuốc |

### 5.5. `metrics.json`

| Trường | Ý nghĩa |
|---|---|
| `preprocessing` | Số dòng thô / sạch / bị bỏ; số phiên tạo ra / giữ lại / bỏ vì quá ngắn |
| `n_sessions`, `n_clusters`, `n_habits` | Số phiên đưa vào phân cụm, số cụm, số cụm đạt ngưỡng thói quen |
| `noise_ratio` | Tỷ lệ phiên bị gán −1 |
| `habit_session_ratio` | Tỷ lệ phiên thuộc một thói quen |
| `silhouette_within_room` | Mức tách biệt giữa các cụm trong cùng một phòng (−1 đến 1, càng cao càng tốt) |
| `ari`, `nmi`, `purity` | Mức khớp với nhãn thật (chỉ có khi dữ liệu có cột nhãn) |
| `parameters` | Toàn bộ tham số đã dùng, kể cả `min_samples` thực tế theo từng người và số ngày quan sát |

---

## 6. Cột nhãn: vì sao có mà không dùng

`activity_label` là **đáp án**. Đề tài là học **không giám sát**, nên nguyên tắc là:

1. Thuật toán **không bao giờ nhìn thấy** cột này. Hàm phân cụm `habit_feature_matrix` chỉ đọc `start_hour` và `duration_minutes`.
2. Cột này được **mang theo** suốt pipeline chỉ để, sau khi phân cụm xong, so sánh cụm tìm được với đáp án (ARI, NMI, độ thuần, ma trận `label_matrix.png`).

**Bằng chứng thực nghiệm:** khi xoá hẳn cột `activity_label` khỏi dữ liệu mô phỏng rồi chạy lại, kết quả **vẫn là 15 cụm, 12 thói quen, giống hệt**. Thứ duy nhất biến mất là các chỉ số ARI/NMI và hình `label_matrix.png`. Bạn có thể tự kiểm tra bằng bài tập ở [07_tu_kiem_tra.md](07_tu_kiem_tra.md).

**Vì sao không dùng nhãn để học có giám sát cho chính xác hơn?** Vì trong thực tế, nhà của người dùng **không có nhãn**: không ai ngồi ghi lại "tôi đang uống thuốc". Một phương pháp cần nhãn sẽ không triển khai được. Nhãn ở đây chỉ là "giáo viên chấm bài", không phải "giáo viên dạy bài".

---

## 7. Vì sao chọn các bộ dữ liệu này mà không phải bộ khác

| Phương án | Vì sao không chọn (hoặc chọn) |
|---|---|
| **STRANDS Aruba** ✔ | Đúng link đề bài; là nhà thông minh thật; 16 tuần đủ dài để thấy thói quen lặp lại; đã được chuẩn hoá về mức phòng; có nhãn để đánh giá; nhẹ (31 kB) |
| STRANDS Witham (cùng file zip) | Văn phòng chứ không phải nhà ở; chỉ ~3 tuần; khi đối chiếu mã vị trí thì không nhất quán (một số mã khớp đánh số từ 0, số khác khớp đánh số từ 1). Không đáng tin bằng Aruba |
| Dữ liệu của chính bài Duckworth et al. (2019) | Là dữ liệu camera/khung xương người do robot quay. Cần cả một hệ thống thị giác máy tính để xử lý, và không phải dữ liệu cảm biến nhà thông minh; nằm ngoài phạm vi |
| CASAS Aruba bản gốc (sự kiện từng cảm biến) | Chi tiết hơn (hơn 30 cảm biến, khoảng 7 tháng), nhưng phải tự ánh xạ từng cảm biến vào phòng và làm sạch nhiều hơn nhiều. Bản STRANDS đã làm việc đó; là hướng mở rộng hợp lý |
| **Dữ liệu mô phỏng** ✔ | Là cách duy nhất có **đáp án chắc chắn** để đo phương pháp đúng hay sai; điều khiển được độ khó (nhiễu, bỏ lỡ, cuối tuần, lỗi dữ liệu) |

---

## 8. Dùng dữ liệu của riêng bạn

1. Chuẩn bị CSV có đủ 7 cột ở mục 4 (tên cột phải đúng như vậy). Cột `activity_label` có thì tốt, không có cũng không sao.
2. Chạy: `smart-home run --input đường/dẫn/file.csv`. Kết quả ghi vào `reports/results/demo/` (theo `name` trong config). Muốn tách riêng thì copy `configs/config.yaml` thành file mới, đổi `name` và `output`, rồi chạy với `--config`.
3. Điều chỉnh config theo loại dữ liệu:

| Nếu dữ liệu của bạn… | Chỉnh |
|---|---|
| là sự kiện rời rạc (cảm biến chuyển động, cửa) | Giữ `inactivity_gap_minutes: 30`, `min_session_minutes: 0` |
| là vị trí đều đặn theo phút/giây (như Aruba) | `split_on_room_change: true` **bắt buộc**; `min_session_minutes: 5` để bỏ các lần đi ngang |
| kéo dài nhiều tháng | Không cần sửa: `min_samples` tự tăng theo số ngày |
| có nhiều người nhưng không có `resident_id` | Phải tự bổ sung; đề tài không giải quyết bài toán tách người |

---

## 9. Các "bẫy" dữ liệu cần biết

| Bẫy | Hiện tượng | Cách xử lý |
|---|---|---|
| Nhãn `"None"` của Aruba | Khi mở `sessions.csv` bằng `pd.read_csv`, pandas tự hiểu chữ `None` là ô trống (NaN) | Pipeline không bị ảnh hưởng (nhãn nằm trong bộ nhớ dạng chuỗi). Khi tự phân tích, dùng `pd.read_csv(..., keep_default_na=False)` |
| `preprocess` ghi đè `sessions.csv` | File mất cột `cluster`, `is_habit` | Chạy lại `smart-home run` |
| Phiên đầu tiên của Aruba bắt đầu 00:00 | Do dữ liệu bắt đầu đúng nửa đêm, giấc ngủ đang diễn ra bị cắt | Chỉ ảnh hưởng 1 phiên / 3.015 |
| Ngày tháng Aruba là giả định | Thứ trong tuần không có ý nghĩa | Không dùng `weekday` cho Aruba |
| `clean_events.csv` của Aruba nặng 14,6 MB | Mở bằng Excel sẽ chậm | Dùng pandas, hoặc xem `sessions.csv` (0,7 MB) |
| Giấc ngủ bị tách làm hai | Đi vệ sinh ban đêm làm đổi phòng → cắt phiên | Là hệ quả đúng của định nghĩa phiên; thể hiện thành 2 mẫu (00:18 và 05:46) |
