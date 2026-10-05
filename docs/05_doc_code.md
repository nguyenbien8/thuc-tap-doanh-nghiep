# 05 · Đọc code: thứ tự, sơ đồ và các dòng then chốt

Mã nguồn nằm trong [src/smart_home_patterns/](../src/smart_home_patterns/), khoảng 900 dòng Python, gồm 9 file. Không cần đọc hết một lượt. Hãy đọc **theo thứ tự dưới đây**, mỗi file trả lời một câu hỏi.

## 1. Sơ đồ gọi hàm

```text
Terminal: smart-home run --config configs/strands_aruba.yaml
   │
   ▼
cli.py: main()                                   đọc tham số dòng lệnh, đọc config
   │
   ▼
pipeline.py: run_pipeline(config)
   ├─ load_events(config)
   │     ├─ CSV:     io.read_events(path)
   │     └─ STRANDS: strands_adapter.load_strands(folder, ...)
   │
   ├─ run_preprocessing(config, events)          ══ BƯỚC 1 ══
   │     └─ preprocessing.preprocess(...)
   │           ├─ clean_events()                 làm sạch
   │           ├─ create_sessions()              gom phiên
   │           └─ build_session_features()       1 dòng / phiên
   │
   ├─ run_discovery(config, sessions)            ══ BƯỚC 2 ══
   │     └─ discovery.discover_patterns(...)
   │           ├─ habit_feature_matrix()         không gian "giờ"
   │           ├─ DBSCAN theo từng (người, phòng)
   │           ├─ build_profiles()               mô tả cụm + tần suất
   │           └─ external_scores()              so với nhãn (nếu có)
   │
   ├─ write_habit_report()                       habit_report.md
   └─ plots.plot_*()                             các hình PNG
```

Hai nhánh phụ: `smart-home generate-demo` → `demo.write_demo()`; `smart-home experiments` → `experiments.run_experiments()`.

## 2. Thứ tự đọc đề xuất

| # | File | Câu hỏi nó trả lời | Thời gian |
|---|---|---|---|
| 1 | [configs/config.yaml](../configs/config.yaml) | Có những tham số nào, nghĩa là gì? | 5' |
| 2 | [preprocessing.py](../src/smart_home_patterns/preprocessing.py) | **Bước 1** làm gì với dữ liệu? | 20' |
| 3 | [discovery.py](../src/smart_home_patterns/discovery.py) | **Bước 2**: thói quen được tìm thế nào? | 30' |
| 4 | [pipeline.py](../src/smart_home_patterns/pipeline.py) | Các bước được nối với nhau ra sao? | 10' |
| 5 | [demo.py](../src/smart_home_patterns/demo.py) | Dữ liệu mô phỏng được tạo thế nào? | 10' |
| 6 | [strands_adapter.py](../src/smart_home_patterns/strands_adapter.py) | Dữ liệu thật được đọc thế nào? | 10' |
| 7 | [experiments.py](../src/smart_home_patterns/experiments.py) | Baseline và độ nhạy được làm thế nào? | 10' |
| 8 | [tests/](../tests/) | Những hành vi nào được bảo đảm? | 10' |
| 9 | `cli.py`, `io.py`, `plots.py` | Phần "ống nước": dòng lệnh, đọc/ghi file, vẽ hình | tuỳ ý |

---

## 3. `preprocessing.py`: Bước 1

| Hàm | Dòng | Việc làm |
|---|---|---|
| `REQUIRED_COLUMNS`, `LABEL_COLUMN` | [10–17](../src/smart_home_patterns/preprocessing.py#L10-L17) | 7 cột bắt buộc; tên cột nhãn (chỉ để đánh giá) |
| `clean_events` | [37](../src/smart_home_patterns/preprocessing.py#L37) | 7 bước làm sạch (xem docstring của hàm) |
| `create_sessions` | [90](../src/smart_home_patterns/preprocessing.py#L90) | Gán `session_id`, `session_key` |
| `build_session_features` | [127](../src/smart_home_patterns/preprocessing.py#L127) | Gộp mỗi phiên thành 1 dòng |
| `preprocess` | [193](../src/smart_home_patterns/preprocessing.py#L193) | Gọi 3 hàm trên + bỏ phiên ngắn + đếm số liệu |

**Các dòng then chốt: quy tắc mở phiên** ([preprocessing.py:108-115](../src/smart_home_patterns/preprocessing.py#L108-L115)):

```python
gap = by_resident["timestamp"].diff().dt.total_seconds().div(60)     # phút kể từ sự kiện trước (của cùng người)
is_new = gap.isna() | gap.gt(inactivity_gap_minutes)                 # sự kiện đầu tiên, hoặc lặng > 30'
if split_on_room_change:
    previous_room = by_resident["room"].shift()
    is_new |= previous_room.notna() & ordered["room"].ne(previous_room)  # hoặc đổi phòng
ordered["session_id"] = is_new.astype(int).groupby(ordered["resident_id"]).cumsum() - 1
```

Mẹo đọc: `is_new` là cột True/False ("dòng này mở phiên mới?"). **Cộng dồn** (`cumsum`) cột này sẽ cho số thứ tự phiên: mỗi lần gặp True thì số tăng thêm 1. Đây là cách xử lý kinh điển trong pandas, không cần vòng lặp.

---

## 4. `discovery.py`: Bước 2 (quan trọng nhất)

| Hàm | Dòng | Việc làm |
|---|---|---|
| `HOURS_PER_RADIAN` | [44](../src/smart_home_patterns/discovery.py#L44) | R = 24/2π |
| `habit_feature_matrix` | [56](../src/smart_home_patterns/discovery.py#L56) | Phiên → điểm 3D đơn vị giờ |
| `observed_days` | [67](../src/smart_home_patterns/discovery.py#L67) | Số ngày quan sát của mỗi người |
| `min_samples_for` | [74](../src/smart_home_patterns/discovery.py#L74) | max(5, ⌈0,2 × số ngày⌉) |
| `circular_hour_stats` | [84](../src/smart_home_patterns/discovery.py#L84) | Trung bình vòng tròn của giờ |
| `build_profiles` | [103](../src/smart_home_patterns/discovery.py#L103) | Mô tả từng cụm, tính `support`, `is_habit` |
| `_relabel_by_time` | [149](../src/smart_home_patterns/discovery.py#L149) | Đánh số lại cụm theo người → phòng → giờ cho dễ đọc |
| `_within_group_silhouette` | [162](../src/smart_home_patterns/discovery.py#L162) | Silhouette trong từng phòng |
| `external_scores` | [179](../src/smart_home_patterns/discovery.py#L179) | ARI, NMI, độ thuần so với nhãn |
| `discover_patterns` | [199](../src/smart_home_patterns/discovery.py#L199) | **Hàm chính của bước 2** |

**Các dòng then chốt: không gian "giờ"** ([discovery.py:56-64](../src/smart_home_patterns/discovery.py#L56-L64)):

```python
angle = 2 * np.pi * sessions["start_hour"] / 24               # giờ → góc trên đồng hồ 24h
return np.column_stack([
    HOURS_PER_RADIAN * np.cos(angle),                          # x  ┐ điểm trên vòng tròn chu vi 24
    HOURS_PER_RADIAN * np.sin(angle),                          # y  ┘ → khoảng cách ≈ số giờ lệch
    duration_weight * np.log2(1 + duration),                   # z: thời lượng gấp đôi = +0,5 "giờ"
])
```

**Các dòng then chốt: DBSCAN theo nhóm** ([discovery.py:231-242](../src/smart_home_patterns/discovery.py#L231-L242)):

```python
for (resident, _room), idx in sessions.groupby(GROUP_COLUMNS).indices.items():   # mỗi (người, phòng)
    k = min_samples_for(days[str(resident)], min_samples, min_samples_day_ratio)
    if len(idx) < k:
        continue                                   # quá ít phiên → cả nhóm là nhiễu
    points = matrix[idx]
    ...                                            # (tính k-distance để vẽ biểu đồ chọn eps)
    local = DBSCAN(eps=eps_hours, min_samples=k).fit_predict(points)
    labels[idx[found]] = local[found] + next_id    # đổi nhãn cục bộ 0,1,2… thành mã cụm toàn cục
```

**Dòng quyết định "thói quen hay không"** ([discovery.py:129](../src/smart_home_patterns/discovery.py#L129)):

```python
"is_habit": bool(support >= min_support),          # support = số ngày có mẫu / số ngày quan sát
```

---

## 5. `pipeline.py`: nối các bước

`run_pipeline` ([dòng 103](../src/smart_home_patterns/pipeline.py#L103)) đọc gần như một bản tóm tắt của đề tài: đọc dữ liệu → bước 1 → ghi `clean_events.csv` → bước 2 → ghi `sessions.csv`, `habits.csv`, `metrics.json`, `habit_report.md` → vẽ 4 hình. `load_events` ([dòng 14](../src/smart_home_patterns/pipeline.py#L14)) chọn cách đọc dựa trên `data.source` trong config (`csv` hay `strands`).

## 6. `demo.py`: bộ sinh dữ liệu mô phỏng

Đọc `RESIDENTS` ([dòng 49](../src/smart_home_patterns/demo.py#L49)) là thấy đáp án: mỗi `Activity(...)` là một thói quen cài sẵn (tên, phòng, giờ, thời lượng, xác suất, lệch cuối tuần). Sau đó đọc `generate_demo_events` ([dòng 144](../src/smart_home_patterns/demo.py#L144)), đúng như giả mã trong [02_du_lieu.md](02_du_lieu.md#22-cách-một-ngày-được-sinh-ra).

## 7. `strands_adapter.py`: đọc dữ liệu thật

`load_strands` ([dòng 65](../src/smart_home_patterns/strands_adapter.py#L65)) đọc 4 file, áp dụng mã đánh số từ 1 và phần ghi đè, rồi tạo mỗi phút một dòng. Docstring đầu file ghi lại nguồn, cách trích dẫn và bằng chứng về cách đánh số mã.

## 8. `experiments.py`: so sánh

`baseline_clusters` ([dòng 34](../src/smart_home_patterns/experiments.py#L34)) chính là cách làm của phiên bản đầu: StandardScaler trên 10 đặc trưng + DBSCAN với eps = phân vị 90% k-distance. `time_spread_minutes` ([dòng 42](../src/smart_home_patterns/experiments.py#L42)) tính độ lệch giờ trong cụm, chỉ số làm lộ ra điểm yếu của baseline.

## 9. Các file "ống nước"

| File | Vai trò |
|---|---|
| `cli.py` | Định nghĩa 5 lệnh con: `generate-demo`, `download-strands`, `preprocess`, `run`, `experiments` |
| `io.py` | Đọc config YAML, đọc/ghi CSV (tự tạo thư mục) |
| `plots.py` | 4 hình. Bảng màu cố định: **xanh = thói quen**, **cam = mẫu không thường xuyên**, **xám = nhiễu** |
| `__init__.py` | Số phiên bản |

## 10. Kiểm thử: đọc test để hiểu code muốn làm gì

Test là "tài liệu có thể chạy được". Mỗi test mô tả một hành vi được bảo đảm:

| Test | Bảo đảm điều gì |
|---|---|
| `test_create_sessions_splits_on_room_change` | Đổi phòng thì mở phiên mới; tắt tuỳ chọn thì không |
| `test_min_session_minutes_filters_short_sessions` | Phiên quá ngắn bị bỏ và được đếm vào báo cáo |
| `test_activity_label_is_carried_for_evaluation_only` | Nhãn được mang theo đến bảng phiên |
| `test_feature_space_is_measured_in_hours` | Lệch 30 phút → khoảng cách 0,5; 23:54 và 00:06 ở rất gần nhau |
| `test_circular_mean_handles_midnight` | Trung bình của 23:30 và 00:30 là 00:00 |
| `test_discovers_daily_habits_and_separates_rare_pattern` | Tìm đúng 2 thói quen hằng ngày; mẫu 30% số ngày không thành thói quen |
| `test_rooms_are_clustered_separately` | Cùng giờ nhưng khác phòng → 2 cụm |
| `test_isolated_sessions_are_noise` | Phiên lẻ loi → −1 |
| `test_all_noise_returns_empty_but_typed_profiles` | Không có cụm nào cũng không lỗi |
| `test_end_to_end_pipeline_recovers_demo_habits` | Chạy trọn pipeline: đủ file đầu ra, ≥ 8 thói quen, độ thuần > 95% |
| `test_strands_adapter_reads_minute_files` | Đọc đúng định dạng STRANDS, mã từ 1, ghi đè, mã lạ → `unknown_7` |

Chạy: `python -m pytest` (thêm `-v` để xem tên từng test).
