# 01 · Bản đồ repo: cái gì ở đâu, từ đâu ra

Mục tiêu của tài liệu này: nhìn vào bất kỳ file nào trong repo, bạn trả lời được ba câu hỏi:

1. **Nó dùng để làm gì?**
2. **Nó từ đâu ra?** Tự viết tay, sinh ra bởi code, hay tải từ internet?
3. **Có được đưa lên git không?** Nếu xoá đi thì lấy lại bằng cách nào?

---

## 1. Toàn cảnh

```text
thuc-tap-doanh-nghiep/
│
├── README.md                 ← cửa chính: đề tài là gì, chạy thế nào, kết quả chính
├── pyproject.toml            ← khai báo package Python + lệnh "smart-home"
├── requirements.txt          ← danh sách thư viện (cách cài thay thế)
│
├── configs/                  ← THAM SỐ của thí nghiệm (không nằm trong code)
│   ├── config.yaml           ←   thí nghiệm 1: dữ liệu mô phỏng
│   └── strands_aruba.yaml    ←   thí nghiệm 2: dữ liệu thật STRANDS Aruba
│
├── src/smart_home_patterns/  ← MÃ NGUỒN (xem docs/05_doc_code.md)
│
├── tests/                    ← 21 kiểm thử tự động (pytest)
│
├── data/                     ← DỮ LIỆU (không đưa lên git, xem mục 3)
│   ├── raw/                  ←   dữ liệu gốc: mô phỏng + STRANDS tải về
│   └── processed/            ←   dữ liệu trung gian do pipeline sinh ra
│
├── reports/                  ← PHẦN NỘP cho hội đồng
│   ├── 01…05_*.md            ←   báo cáo viết tay
│   ├── slide_thuyet_trinh.html
│   └── results/              ←   kết quả do code sinh ra (bảng, hình, số liệu)
│
├── docs/                     ← TÀI LIỆU HỌC (bạn đang đọc): giải thích repo cho chính bạn
│
├── .github/copilot-instructions.md   ← quy ước cho trợ lý AI khi sửa code
├── .vscode/                  ← cấu hình VS Code (chạy test, chạy thí nghiệm bằng Tasks)
└── .venv/                    ← môi trường ảo Python (tự tạo, không đưa lên git)
```

**Quy tắc để nhớ:** `configs/` + `src/` + `tests/` là **đầu vào do con người viết**. `data/processed/` và `reports/results/` là **đầu ra do máy sinh**, và luôn có thể sinh lại bằng lệnh.

---

## 2. Từng file: nguồn gốc và vai trò

### 2.1. File do con người viết (sửa được, là "nguồn sự thật")

| File | Vai trò | Ghi chú |
|---|---|---|
| `README.md` | Giới thiệu, cách chạy, kết quả chính | Đọc đầu tiên |
| `pyproject.toml` | Khai báo package, thư viện, lệnh `smart-home` | Dòng `smart-home = "smart_home_patterns.cli:main"` tạo ra lệnh terminal |
| `requirements.txt` | Danh sách thư viện | Trùng với `pyproject.toml`, để ai quen `pip install -r` cũng cài được |
| `configs/config.yaml` | Tham số thí nghiệm 1 | Mỗi dòng có chú thích |
| `configs/strands_aruba.yaml` | Tham số thí nghiệm 2 | Có ghi đè mã vị trí 9 → `outside` (giải thích ở [02_du_lieu.md](02_du_lieu.md)) |
| `src/smart_home_patterns/*.py` | Toàn bộ thuật toán | Xem [05_doc_code.md](05_doc_code.md) |
| `tests/*.py` | Kiểm thử | Chạy `python -m pytest` |
| `reports/01…05_*.md` | Báo cáo nộp | Viết cho hội đồng |
| `reports/slide_thuyet_trinh.html` | Slide | Tự chứa, ảnh lấy từ `reports/results/` |
| `docs/*.md` | Tài liệu học | Viết cho bạn |

### 2.2. File do code sinh ra (không sửa tay; muốn đổi thì sửa code/config rồi chạy lại)

| File | Sinh bởi lệnh | Hàm tạo ra | Đưa lên git? |
|---|---|---|---|
| `data/raw/smart_home_events.csv` | `smart-home generate-demo` | `demo.write_demo` | Không |
| `data/processed/<tên>/clean_events.csv` | `smart-home run` (hoặc `preprocess`) | `pipeline.run_pipeline` | Không |
| `data/processed/<tên>/sessions.csv` | `smart-home run` (hoặc `preprocess`) | `pipeline.run_pipeline` | Không |
| `reports/results/<tên>/habits.csv` | `smart-home run` | `discovery.build_profiles` | **Có** |
| `reports/results/<tên>/metrics.json` | `smart-home run` | `discovery.discover_patterns` | **Có** |
| `reports/results/<tên>/habit_report.md` | `smart-home run` | `pipeline.write_habit_report` | **Có** |
| `reports/results/<tên>/figures/*.png` | `smart-home run` | `plots.py` | **Có** |
| `reports/results/experiments/*` | `smart-home experiments` | `experiments.run_experiments` | **Có** |

`<tên>` là giá trị `name:` trong file config: `demo` hoặc `strands_aruba`.

> **Lưu ý:** lệnh `smart-home preprocess` chỉ chạy bước 1, nên nó ghi `sessions.csv` **chưa có** cột `cluster` và `is_habit`. Nếu sau đó bạn mở `sessions.csv` mà không thấy cột cụm, chỉ cần chạy lại `smart-home run`.

### 2.3. File tải từ internet

| File | Nguồn | Lệnh |
|---|---|---|
| `data/raw/strands/aruba/*` và `data/raw/strands/witham/*` | `https://lcas.lincoln.ac.uk/nextcloud/shared/datasets/activity/activity.zip` (≈ 31 kB) | `smart-home download-strands` |

---

## 3. Vì sao có file đưa lên git, có file không?

Quy tắc nằm trong `.gitignore`:

| Loại | Đưa lên git? | Lý do |
|---|---|---|
| Code, config, test, tài liệu | Có | Đây là "nguồn sự thật" |
| `data/raw/` | **Không** | Dữ liệu mô phỏng sinh lại được 100% nhờ seed cố định. Dữ liệu STRANDS thuộc bản quyền của LCAS, nên tải từ nguồn gốc thay vì phát tán lại |
| `data/processed/` | **Không** | Sinh lại được. Riêng `clean_events.csv` của Aruba đã nặng 14,6 MB |
| `reports/results/` | **Có** | Báo cáo và slide trích dẫn các bảng/hình này; người chấm cần xem được mà không phải chạy code |
| `.venv/`, `*.egg-info/`, `__pycache__/`, `.pytest_cache/` | **Không** | Sinh ra khi cài đặt hoặc chạy, phụ thuộc máy |

Hai file `data/raw/.gitkeep` và `data/processed/.gitkeep` là file rỗng. Chúng chỉ có tác dụng giữ lại thư mục trống trên git, vì git không lưu thư mục rỗng.

---

## 4. Tái tạo mọi thứ từ đầu

Nếu xoá sạch `data/` và `reports/results/`, bốn lệnh sau tạo lại tất cả, với số liệu **giống hệt**:

```powershell
smart-home generate-demo                                   # → data/raw/smart_home_events.csv
smart-home run                                             # → data/processed/demo/, reports/results/demo/
smart-home download-strands                                # → data/raw/strands/
smart-home run --config configs/strands_aruba.yaml         # → data/processed/strands_aruba/, reports/results/strands_aruba/
smart-home experiments                                     # → reports/results/experiments/
```

Nếu chưa cài package bằng `pip install -e .`, thay `smart-home` bằng `python -m smart_home_patterns.cli` và đặt biến môi trường `PYTHONPATH=src`. Trong VS Code còn có sẵn các Task (`Terminal → Run Task`) cho từng lệnh.
