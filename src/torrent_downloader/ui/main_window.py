import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QLabel, QInputDialog,
    QSystemTrayIcon, QMenu, QMessageBox, QApplication,
    QFileDialog, QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
    QCheckBox
)
from PySide6.QtCore import QTimer, Qt, QPoint, QEvent
from PySide6.QtGui import QIcon, QAction, QCursor
from ..core.torrent_manager import TorrentManager

def format_speed(speed):
    if speed < 1024:
        return f"{speed:.0f} B/s"
    elif speed < 1024 ** 2:
        return f"{speed / 1024:.1f} KB/s"
    else:
        return f"{speed / (1024 ** 2):.1f} MB/s"

def format_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 ** 3:
        return f"{size / (1024 ** 2):.1f} MB"
    else:
        return f"{size / (1024 ** 3):.1f} GB"

class AddTorrentDialog(QDialog):
    def __init__(self, default_save_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm Magnet Link")
        self.resize(550, 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.txt_magnet = QLineEdit()
        self.txt_magnet.setPlaceholderText("magnet:?xt=urn:btih:...")
        form_layout.addRow("Magnet Link:", self.txt_magnet)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(6)
        self.txt_path = QLineEdit(str(default_save_path))
        self.btn_browse = QPushButton("Duyệt...")
        self.btn_browse.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.txt_path)
        path_layout.addWidget(self.btn_browse)

        form_layout.addRow("Nơi lưu file:", path_layout)
        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Tải xuống")
        button_box.button(QDialogButtonBox.Cancel).setText("Hủy")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file", self.txt_path.text())
        if folder:
            self.txt_path.setText(folder)

    def get_data(self):
        return self.txt_magnet.text().strip(), self.txt_path.text().strip()


class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt ứng dụng")
        self.resize(520, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(6)
        current_download_dir = current_settings.get("download_dir", "downloads")
        self.txt_path = QLineEdit(str(current_download_dir))
        self.btn_browse = QPushButton("Duyệt...")
        self.btn_browse.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.txt_path)
        path_layout.addWidget(self.btn_browse)

        form_layout.addRow("Thư mục lưu mặc định:", path_layout)

        self.chk_minimize_to_tray = QCheckBox("Thu nhỏ cửa sổ [-] sẽ ẩn vào khay hệ thống (System Tray)")
        self.chk_minimize_to_tray.setChecked(current_settings.get("minimize_to_tray", True))
        form_layout.addRow("", self.chk_minimize_to_tray)

        self.chk_close_to_tray = QCheckBox("Đóng cửa sổ [X] sẽ ẩn vào khay hệ thống (tiếp tục tải ngầm)")
        self.chk_close_to_tray.setChecked(current_settings.get("close_to_tray", True))
        form_layout.addRow("", self.chk_close_to_tray)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).setText("Lưu cài đặt")
        button_box.button(QDialogButtonBox.Cancel).setText("Hủy")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục tải về mặc định", self.txt_path.text())
        if folder:
            self.txt_path.setText(folder)

    def get_settings(self):
        return {
            "download_dir": self.txt_path.text().strip(),
            "minimize_to_tray": self.chk_minimize_to_tray.isChecked(),
            "close_to_tray": self.chk_close_to_tray.isChecked()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Torrent Downloader Pro")
        self.resize(1000, 560)
        
        self.is_really_quitting = False
        self.has_shown_tray_hint = False

        # Load Icon
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.icon_path = base_dir / "assets" / "app.ico"
        if not self.icon_path.exists():
            self.icon_path = base_dir / "assets" / "app.png"
        self.app_icon = QIcon(str(self.icon_path)) if self.icon_path.exists() else QIcon()
        if not self.app_icon.isNull():
            self.setWindowIcon(self.app_icon)

        # Initialize Torrent Manager (automatically restores saved session)
        self.manager = TorrentManager()

        # Mapping: info_hash -> row index
        self.hash_to_row = {}

        self.init_ui()
        self.init_tray()
        self.load_initial_torrents()

        # Timer to update stats and process libtorrent alerts
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_torrents)
        self.timer.start(1000)

        # Periodic save timer (every 30s)
        self.save_timer = QTimer(self)
        self.save_timer.timeout.connect(self.manager.request_save_resume_data)
        self.save_timer.start(30000)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        self.btn_add_magnet = QPushButton("+ Thêm Magnet Link")
        self.btn_add_magnet.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 7px 14px; border-radius: 5px;")
        self.btn_add_magnet.clicked.connect(self.add_magnet)
        toolbar_layout.addWidget(self.btn_add_magnet)

        self.btn_pause_all = QPushButton("⏸ Tạm dừng tất cả")
        self.btn_pause_all.setStyleSheet("padding: 7px 12px; border-radius: 5px;")
        self.btn_pause_all.clicked.connect(self.pause_all)
        toolbar_layout.addWidget(self.btn_pause_all)

        self.btn_resume_all = QPushButton("▶ Tiếp tục tất cả")
        self.btn_resume_all.setStyleSheet("padding: 7px 12px; border-radius: 5px;")
        self.btn_resume_all.clicked.connect(self.resume_all)
        toolbar_layout.addWidget(self.btn_resume_all)

        self.btn_open_folder = QPushButton("📁 Thư mục tải về")
        self.btn_open_folder.setStyleSheet("padding: 7px 12px; border-radius: 5px;")
        self.btn_open_folder.clicked.connect(self.open_download_folder)
        toolbar_layout.addWidget(self.btn_open_folder)

        self.btn_minimize_tray = QPushButton("🔻 Ẩn vào khay")
        self.btn_minimize_tray.setStyleSheet("padding: 7px 12px; border-radius: 5px;")
        self.btn_minimize_tray.clicked.connect(self.hide_to_tray)
        toolbar_layout.addWidget(self.btn_minimize_tray)

        self.btn_settings = QPushButton("⚙️ Cài đặt")
        self.btn_settings.setStyleSheet("padding: 7px 12px; border-radius: 5px;")
        self.btn_settings.clicked.connect(self.open_settings)
        toolbar_layout.addWidget(self.btn_settings)

        toolbar_layout.addStretch()

        self.btn_quit = QPushButton("Thoát hẳn")
        self.btn_quit.setStyleSheet("background-color: #dc2626; color: white; padding: 7px 12px; border-radius: 5px;")
        self.btn_quit.clicked.connect(self.quit_application)
        toolbar_layout.addWidget(self.btn_quit)

        layout.addLayout(toolbar_layout)

        # Torrents Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Tên Torrent", "Kích thước", "Đã tải", "Tiến độ", "Tốc độ", "Trạng thái"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 160)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        # Status bar
        self.status_label = QLabel("Sẵn sàng")
        self.statusBar().addWidget(self.status_label)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if not self.app_icon.isNull():
            self.tray_icon.setIcon(self.app_icon)
        self.tray_icon.setToolTip("Torrent Downloader Pro")

        tray_menu = QMenu()
        
        act_open = QAction("Mở ứng dụng", self)
        act_open.triggered.connect(self.show_window)
        tray_menu.addAction(act_open)

        act_hide = QAction("Ẩn vào khay", self)
        act_hide.triggered.connect(self.hide_to_tray)
        tray_menu.addAction(act_hide)

        act_add = QAction("Thêm Magnet Link...", self)
        act_add.triggered.connect(self.add_magnet)
        tray_menu.addAction(act_add)

        tray_menu.addSeparator()

        act_pause_all = QAction("Tạm dừng tất cả", self)
        act_pause_all.triggered.connect(self.pause_all)
        tray_menu.addAction(act_pause_all)

        act_resume_all = QAction("Tiếp tục tất cả", self)
        act_resume_all.triggered.connect(self.resume_all)
        tray_menu.addAction(act_resume_all)

        tray_menu.addSeparator()

        act_settings = QAction("Cài đặt...", self)
        act_settings.triggered.connect(self.open_settings)
        tray_menu.addAction(act_settings)

        tray_menu.addSeparator()

        act_quit = QAction("Thoát hoàn toàn", self)
        act_quit.triggered.connect(self.quit_application)
        tray_menu.addAction(act_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window()

    def show_window(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()
        self.activateWindow()

    def load_initial_torrents(self):
        status_list = self.manager.get_torrents_status()
        for info_hash, info in status_list:
            self.insert_or_update_row(info_hash, info)
        self.status_label.setText(f"Đã khôi phục {len(status_list)} torrent từ phiên làm việc trước.")

    def insert_or_update_row(self, info_hash, info):
        if info_hash not in self.hash_to_row:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.hash_to_row[info_hash] = row

            self.table.setItem(row, 0, QTableWidgetItem(info['name']))
            self.table.setItem(row, 1, QTableWidgetItem("-"))
            self.table.setItem(row, 2, QTableWidgetItem("-"))

            progress_bar = QProgressBar()
            progress_bar.setValue(int(info['progress']))
            progress_bar.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 3, progress_bar)

            self.table.setItem(row, 4, QTableWidgetItem("-"))
            self.table.setItem(row, 5, QTableWidgetItem(info['state']))
        else:
            row = self.hash_to_row[info_hash]
            self.table.item(row, 0).setText(info['name'])
            
            size_str = format_size(info['total_wanted']) if info['total_wanted'] > 0 else "-"
            self.table.item(row, 1).setText(size_str)
            
            done_str = format_size(info['total_done'])
            self.table.item(row, 2).setText(done_str)

            pb = self.table.cellWidget(row, 3)
            if pb:
                pb.setValue(int(info['progress']))

            speed_str = format_speed(info['download_rate'])
            self.table.item(row, 4).setText(speed_str)

            state_str = info['state']
            if state_str == 'downloading':
                state_str += f" ({info['num_peers']} peers)"
            self.table.item(row, 5).setText(state_str)

    def open_settings(self):
        self.show_window()
        dialog = SettingsDialog(self.manager.settings, self)
        if dialog.exec() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            if new_settings.get("download_dir"):
                self.manager.update_settings(new_settings)
                self.status_label.setText(f"Đã lưu cài đặt. Thư mục lưu: {new_settings['download_dir']}")

    def add_magnet(self):
        self.show_window()
        dialog = AddTorrentDialog(self.manager.download_dir, self)

        clipboard_text = QApplication.clipboard().text().strip()
        if clipboard_text.startswith("magnet:?"):
            dialog.txt_magnet.setText(clipboard_text)

        if dialog.exec() == QDialog.Accepted:
            magnet_uri, save_path = dialog.get_data()
            if magnet_uri:
                try:
                    handle, info_hash = self.manager.add_magnet_link(
                        magnet_uri,
                        save_path=save_path if save_path else None
                    )
                    self.update_torrents()
                    self.status_label.setText(f"Đã thêm torrent mới. Tổng: {len(self.manager.handles)}")
                except Exception as e:
                    QMessageBox.warning(self, "Lỗi", f"Không thể thêm Magnet Link: {e}")
            else:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đường link Magnet.")

    def update_torrents(self):
        status_list = self.manager.get_torrents_status()
        total_download_rate = 0

        # Remove deleted rows if any
        active_hashes = set(ih for ih, _ in status_list)
        for ih in list(self.hash_to_row.keys()):
            if ih not in active_hashes:
                row = self.hash_to_row[ih]
                self.table.removeRow(row)
                del self.hash_to_row[ih]
                # Re-index
                self.reindex_table()

        for info_hash, info in status_list:
            self.insert_or_update_row(info_hash, info)
            total_download_rate += info['download_rate']

        if self.manager.handles:
            self.status_label.setText(f"Đang tải: {len(self.manager.handles)} torrent | Tổng tốc độ: {format_speed(total_download_rate)}")

    def reindex_table(self):
        # Update hash_to_row according to actual table row positions
        new_map = {}
        status_list = self.manager.get_torrents_status()
        for row in range(self.table.rowCount()):
            if row < len(status_list):
                ih = status_list[row][0]
                new_map[ih] = row
        self.hash_to_row = new_map

    def get_selected_info_hash(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        for ih, r in self.hash_to_row.items():
            if r == row:
                return ih
        return None

    def show_context_menu(self, pos: QPoint):
        info_hash = self.get_selected_info_hash()
        if not info_hash:
            return

        meta = self.manager.torrents_meta.get(info_hash, {})
        is_paused = meta.get('is_paused', False)

        menu = QMenu(self)
        
        if is_paused:
            act_toggle = QAction("▶ Tiếp tục tải", self)
            act_toggle.triggered.connect(lambda: self.manager.resume_torrent(info_hash))
        else:
            act_toggle = QAction("⏸ Tạm dừng", self)
            act_toggle.triggered.connect(lambda: self.manager.pause_torrent(info_hash))
        menu.addAction(act_toggle)

        act_folder = QAction("📁 Mở thư mục chứa file", self)
        act_folder.triggered.connect(lambda: self.open_torrent_folder(info_hash))
        menu.addAction(act_folder)

        act_copy = QAction("📋 Sao chép Magnet Link", self)
        act_copy.triggered.connect(lambda: self.copy_magnet(info_hash))
        menu.addAction(act_copy)

        menu.addSeparator()

        act_remove = QAction("❌ Xóa khỏi danh sách", self)
        act_remove.triggered.connect(lambda: self.remove_torrent(info_hash, delete_files=False))
        menu.addAction(act_remove)

        act_remove_all = QAction("🗑 Xóa torrent VÀ dữ liệu đã tải", self)
        act_remove_all.triggered.connect(lambda: self.remove_torrent(info_hash, delete_files=True))
        menu.addAction(act_remove_all)

        menu.exec(QCursor.pos())

    def open_torrent_folder(self, info_hash):
        meta = self.manager.torrents_meta.get(info_hash, {})
        folder = meta.get('save_path', str(self.manager.download_dir))
        if os.path.exists(folder):
            os.startfile(folder)

    def open_download_folder(self):
        if os.path.exists(self.manager.download_dir):
            os.startfile(self.manager.download_dir)

    def copy_magnet(self, info_hash):
        meta = self.manager.torrents_meta.get(info_hash, {})
        magnet = meta.get('magnet_uri', '')
        if magnet:
            QApplication.clipboard().setText(magnet)
            self.status_label.setText("Đã sao chép Magnet Link vào Clipboard.")

    def remove_torrent(self, info_hash, delete_files=False):
        msg = "Bạn có chắc chắn muốn xóa torrent này và toàn bộ file đã tải?" if delete_files else "Bạn có muốn xóa torrent này khỏi danh sách tải?"
        reply = QMessageBox.question(self, "Xác nhận xóa", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.manager.remove_torrent(info_hash, delete_files=delete_files)
            self.update_torrents()

    def pause_all(self):
        for ih in list(self.manager.handles.keys()):
            self.manager.pause_torrent(ih)
        self.update_torrents()

    def resume_all(self):
        for ih in list(self.manager.handles.keys()):
            self.manager.resume_torrent(ih)
        self.update_torrents()

    def hide_to_tray(self):
        self.hide()
        if not self.has_shown_tray_hint:
            self.tray_icon.showMessage(
                "Torrent Downloader Pro",
                "Ứng dụng đang chạy ẩn dưới khay hệ thống để tiếp tục tải. Nhấp đúp vào icon để mở lại hoặc chuột phải chọn 'Thoát hoàn toàn'.",
                QSystemTrayIcon.Information,
                3000
            )
            self.has_shown_tray_hint = True

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized() and self.manager.settings.get("minimize_to_tray", True):
                QTimer.singleShot(0, self.hide_to_tray)
        super().changeEvent(event)

    def closeEvent(self, event):
        if not self.is_really_quitting:
            if self.manager.settings.get("close_to_tray", True):
                event.ignore()
                self.hide_to_tray()
            else:
                self.quit_application()
        else:
            # Save all states before exiting
            self.status_label.setText("Đang lưu phiên làm việc...")
            self.manager.request_save_resume_data()
            self.manager.save_session()
            event.accept()

    def quit_application(self):
        reply = QMessageBox.question(
            self,
            "Thoát ứng dụng",
            "Bạn có chắc muốn thoát hoàn toàn ứng dụng? Mọi tiến trình download sẽ được lưu lại và tự động tiếp tục khi mở lại.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.is_really_quitting = True
            self.manager.request_save_resume_data()
            self.manager.save_session()
            QApplication.quit()
            # Fast exit without hanging on libtorrent socket threads
            os._exit(0)
