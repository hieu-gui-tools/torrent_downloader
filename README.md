# 🚀 Torrent Downloader Pro

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt)-green.svg)
![Engine](https://img.shields.io/badge/Engine-libtorrent%202.1+-red.svg)
![Package Manager](https://img.shields.io/badge/uv-Package%20Manager-purple.svg)
![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)

**Ứng dụng tải Torrent & Magnet Link chuyên nghiệp, giao diện Dark Mode hiện đại, hiệu năng cao và chạy ngầm tiện lợi trên Windows.**

[Tính Năng](#-tính-năng-nổi-bật) • [Cài Đặt](#-cài-đặt--hướng-dẫn-sử-dụng) • [Cấu Trúc Dự Án](#-cấu-trúc-dự-án) • [Công Nghệ](#-công-nghệ-sử-dụng)

</div>

---

## 🌟 Tính Năng Nổi Bật

- ⚡ **Tốc độ cao với Libtorrent**: Sử dụng lõi `libtorrent` (C++ bindings) tối ưu hóa kết nối P2P, DHT, PeX, không giới hạn băng thông.
- 🎨 **Giao diện Fusion Dark Mode**: Giao diện người dùng đồ họa (GUI) xây dựng bằng `PySide6 (Qt)`, trực quan, hiển thị chi tiết tiến trình (Tên, Tiến độ %, Tốc độ Tải/Gửi, Kích thước, Số Peers, Trạng thái).
- 📥 **Hỗ trợ Magnet Link & Đổi Thư Mục Tải**: Hộp thoại thêm torrent cho phép tùy biến thư mục lưu cho từng tác vụ riêng biệt.
- 💾 **Khôi phục phiên làm việc (Fast Resume & Persistence)**: Tự động lưu trạng thái tải vào file JSON và dữ liệu `fastresume`, khởi động lại ứng dụng sẽ tiếp tục tải mượt mà không cần quét lại dữ liệu.
- 🔔 **Chạy ngầm ở Khay Hệ Thống (System Tray)**:
  - Tùy chọn thu nhỏ `[-]` hoặc đóng `[X]` ẩn xuống System Tray để tải ngầm liên tục mà không vướng thanh tác vụ.
  - Menu chuột phải ở System Tray hỗ trợ mở nhanh giao diện hoặc thoát hoàn toàn ứng dụng.
- 🖱️ **Menu ngữ cảnh chuột phải phong phú**:
  - Tạm dừng (Pause) / Tiếp tục (Resume).
  - Mở trực tiếp thư mục chứa file sau khi tải xong.
  - Sao chép lại Magnet Link vào Clipboard.
  - Xóa torrent khỏi danh sách hoặc xóa kèm dữ liệu đã tải trên ổ cứng.
- ⚙️ **Bảng Cài Đặt (Settings Dialog)**: Quản lý thư mục tải mặc định, bật/tắt hành vi đóng/thu nhỏ xuống khay hệ thống.
- 🖥️ **Tiện ích Khởi Chạy Nhanh trên Windows**: Đi kèm các script VBS / Batch giúp tạo Shortcut ra Desktop với icon riêng và khởi chạy ngầm hoàn toàn không hiện cửa sổ console màu đen.

---

## 📦 Cài Đặt & Hướng Dẫn Sử Dụng

### 1. Yêu Cầu Môi Trường
- **Hệ điều hành**: Windows 10 / 11 (64-bit).
- **Python**: Phiên bản 3.12 trở lên.
- **uv** (Khuyên dùng - Package Manager cực nhanh của Astral) hoặc **pip**.

### 2. Cài Đặt Bằng `uv` (Khuyên dùng)

1. **Clone repository**:
   ```bash
   git clone https://github.com/hieu-gui-tools/torrent_downloader.git
   cd torrent_downloader
   ```

2. **Cài đặt dependencies và đồng bộ môi trường**:
   ```bash
   uv sync
   ```

3. **Chạy ứng dụng**:
   ```bash
   uv run torrent-downloader
   ```

### 3. Cài Đặt Bằng `pip` Truyền Thống

```bash
# Tạo môi trường ảo
python -m venv .venv
.venv\Scripts\activate

# Cài đặt thư viện
pip install -e .
# Hoặc: pip install libtorrent pyside6

# Khởi chạy
python -m torrent_downloader
```

---

## 💡 Tiện Ích Khởi Chạy Nhanh Cho Windows

Trong thư mục dự án đã chuẩn bị sẵn các file script hỗ trợ Windows:

- **`create_shortcut.vbs`**: Click đúp vào file này để tự động tạo một Shortcut mang icon ứng dụng ngay trên màn hình **Desktop**.
- **`run.vbs`**: Khởi chạy ứng dụng hoàn toàn không hiện màn hình đen dòng lệnh (Console-less).
- **`run.cmd`**: Khởi chạy ứng dụng qua Command Prompt với thông báo lỗi rõ ràng nếu có sự cố môi trường.

---

## 📂 Cấu Trúc Dự Án

```text
torrent_downloader/
├── assets/                    # Biểu tượng ứng dụng (.ico, .png) & thư viện runtime
│   ├── app.ico
│   ├── app.png
│   └── msvcp140.dll
├── data/                      # Lưu trữ phiên làm việc (Được gitignore tự động)
│   ├── fastresume/
│   ├── settings.json
│   └── torrents.json
├── downloads/                 # Thư mục lưu file tải về mặc định
├── scripts/                   # Script tiện ích bổ trợ
│   └── generate_icon.py
├── src/
│   └── torrent_downloader/
│       ├── core/
│       │   ├── __init__.py
│       │   └── torrent_manager.py  # Quản lý libtorrent session, alerts, persistence
│       ├── ui/
│       │   ├── __init__.py
│       │   └── main_window.py      # Giao diện PySide6, System Tray, bảng điều khiển
│       └── __init__.py             # Entry point & cấu hình ứng dụng Qt
├── .gitignore                 # Bỏ qua file tạm, virtualenv, data runtime
├── create_shortcut.vbs        # Script tạo Desktop shortcut
├── pyproject.toml             # Khai báo metadata dự án và dependencies
├── README.md                  # Tài liệu hướng dẫn dự án
├── run.cmd                    # File batch khởi chạy với logging
├── run.vbs                    # File VBS khởi chạy ngầm không hiện console
└── uv.lock                    # Khóa phiên bản dependencies chính xác
```

---

## 🛠️ Công Nghệ Sử Dụng

- **Ngôn ngữ**: [Python 3.12+](https://www.python.org/)
- **Giao diện**: [PySide6 (Qt for Python)](https://doc.qt.io/qtforpython/)
- **Lõi BitTorrent**: [libtorrent (Rasterbar)](https://libtorrent.org/)
- **Đóng gói & Quản lý**: [uv](https://docs.astral.sh/uv/)

---

## 📄 License

Dự án được phân phối dưới giấy phép [MIT License](LICENSE).
