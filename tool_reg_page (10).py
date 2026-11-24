#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BẢNG ĐIỀU KHIỂN GUI (CUSTOMTKINTER DARK MODE)
Kết nối trực tiếp với lõi core_tool.py (Reg Page Pro5 VIP V5 + Chuyển Page + Get Token EAAAAU)
"""

import os
import re
import sys
import time
import queue
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, List, Optional

try:
    import customtkinter as ctk
except ImportError:
    print("Vui lòng cài đặt customtkinter bằng lệnh: pip install customtkinter")
    sys.exit(1)

# Import file lõi của bạn (đổi tên file cũ thành core_tool.py đặt cùng thư mục)
try:
    import core_tool as core
except ImportError:
    root_err = tk.Tk()
    root_err.withdraw()
    messagebox.showerror(
        "Thiếu file core_tool.py",
        "Không tìm thấy file 'core_tool.py' cùng thư mục!\n"
        "Hãy đổi tên file code gốc của bạn thành 'core_tool.py' rồi chạy lại."
    )
    sys.exit(1)


# ==============================================================================
# HOOK LOG TỪ CORE SANG GUI (THREAD-SAFE, LỌC MÃ MÀU ANSI)
# ==============================================================================

GUI_LOG_QUEUE: "queue.Queue[tuple]" = queue.Queue()
_ORIG_ADD_LOG = core.add_process_log


def _hooked_add_process_log(acc_id: int, uid: str, msg: str):
    _ORIG_ADD_LOG(acc_id, uid, msg)
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    short_uid = (uid or "Unknown")[:15]

    tag = "info"
    if "\033[92m" in msg or "✅" in msg or "✔" in msg or "🎉" in msg:
        tag = "success"
    elif "\033[91m" in msg or "❌" in msg:
        tag = "error"
    elif "\033[93m" in msg or "⚠️" in msg or "🚫" in msg or "⏳" in msg:
        tag = "warn"
    elif "\033[96m" in msg or "🚀" in msg or "🖼️" in msg or "🔄" in msg:
        tag = "cyan"

    clean_msg = re.sub(r"\033\[[0-9;]*m", "", msg)
    GUI_LOG_QUEUE.put((f"[{now_str}] [Acc #{acc_id:02d} | {short_uid}] {clean_msg}\n", tag))


core.add_process_log = _hooked_add_process_log


def get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def open_path_in_os(path: str):
    if not os.path.exists(path):
        messagebox.showinfo("Thông báo", f"Chưa có file/thư mục:\n{path}")
        return
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Lỗi mở file", str(e))


def configure_dark_treeview(style: ttk.Style):
    style.theme_use("clam")
    style.configure(
        "Dark.Treeview",
        background="#1b1f2a",
        foreground="#e5e7eb",
        fieldbackground="#1b1f2a",
        rowheight=28,
        borderwidth=0,
        font=("Segoe UI", 9),
    )
    style.configure(
        "Dark.Treeview.Heading",
        background="#262c3d",
        foreground="#38bdf8",
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padding=(6, 6),
    )
    style.map(
        "Dark.Treeview",
        background=[("selected", "#2d3b55")],
        foreground=[("selected", "#ffffff")],
    )
    style.map("Dark.Treeview.Heading", background=[("active", "#323a50")])


# ==============================================================================
# CỬA SỔ CHÍNH - CONTROL PANEL
# ==============================================================================

class RegPageControlPanel(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("TOOL REG PAGE PRO5 VIP (CORE V5) + CHUYỂN PAGE SIÊU MẠNH")
        self.geometry("1380x840")
        self.minsize(1180, 720)

        self.app_dir = get_app_dir()
        self.ttk_style = ttk.Style(self)
        configure_dark_treeview(self.ttk_style)

        # Trạng thái Tab 1 (Reg + Chuyển)
        self.reg_running = False
        self.reg_tasks: List[core.AccountTask] = []
        self.reg_tree_iids: Dict[int, str] = {}
        self.reg_queue: Optional[queue.Queue] = None
        self.reg_workers: List[threading.Thread] = []
        self.reg_stats: Dict[str, int] = {
            "total_holder_acc": 0,
            "total_pages": 0,
            "total_invited": 0,
            "total_no_page": 0,
            "total_limited": 0,
            "total_net_err": 0,
            "total_token_die": 0,
        }

        # Trạng thái Tab 2 (Chuyển Page độc lập)
        self.tr_scanning = False
        self.tr_running = False
        self.tr_stop_flag = threading.Event()
        self.tr_pages_data: List[Dict[str, Any]] = []
        self.tr_log_queue: "queue.Queue[tuple]" = queue.Queue()
        self.tr_ui_queue: "queue.Queue[tuple]" = queue.Queue()

        # Trạng thái Tab 3 (Get Token)
        self.tk_running = False
        self.tk_stop_flag = threading.Event()
        self.tk_ui_queue: "queue.Queue[tuple]" = queue.Queue()
        self.tk_success_lines: List[str] = []

        self._build_header()
        self._build_tabs()

        # Vòng lặp cập nhật UI mượt mà (300ms)
        self.after(300, self._ui_poll_loop)

    # --------------------------------------------------------------------------
    # HEADER CHUNG
    # --------------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, height=56, corner_radius=0, fg_color="#141824")
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title_lbl = ctk.CTkLabel(
            header,
            text="⚡ REG PAGE PRO5 VIP (V5) & SUPER TRANSFER CONTROL PANEL",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#38bdf8",
        )
        title_lbl.pack(side="left", padx=18)

        btn_bar = ctk.CTkFrame(header, fg_color="transparent")
        btn_bar.pack(side="right", padx=14)

        ctk.CTkButton(
            btn_bar, text="📂 Thư mục Tool", width=118, height=30,
            fg_color="#262c3d", hover_color="#343d54",
            command=lambda: open_path_in_os(self.app_dir),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_bar, text="📄 acc_cam_page.txt", width=136, height=30,
            fg_color="#262c3d", hover_color="#343d54",
            command=lambda: open_path_in_os(os.path.join(self.app_dir, "acc_cam_page.txt")),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_bar, text="📝 transfer_page.log", width=136, height=30,
            fg_color="#262c3d", hover_color="#343d54",
            command=lambda: open_path_in_os(os.path.join(self.app_dir, "transfer_page.log")),
        ).pack(side="left", padx=4)

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=8)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        self.tab_reg = self.tabview.add("🚀 Reg Page + Chuyển Cuốn Chiếu")
        self.tab_transfer = self.tabview.add("🔄 Quét & Chuyển Page Độc Lập")
        self.tab_token = self.tabview.add("🔑 Get Token EAAAAU (Bloks v5)")

        self._build_tab_reg()
        self._build_tab_transfer()
        self._build_tab_token()

    # ==========================================================================
    # TAB 1: REG PAGE PRO5 VIP + CHUYỂN CUỐN CHIẾU
    # ==========================================================================
    def _build_tab_reg(self):
        container = ctk.CTkFrame(self.tab_reg, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # --- CỘT TRÁI: CẤU HÌNH ---
        left_panel = ctk.CTkScrollableFrame(container, width=410, fg_color="#181c26")
        left_panel.pack(side="left", fill="y", padx=(0, 8), pady=2)

        # 1. Nick mẹ nhận Page
        self._section_label(left_panel, "1. Nick Mẹ nhận Page (Để trống = chỉ tạo Page)")
        self.reg_holder_entry = ctk.CTkEntry(
            left_panel, placeholder_text="UID Nick Mẹ hoặc Token / UID|Pass|Cookie|Token..."
        )
        self.reg_holder_entry.pack(fill="x", padx=10, pady=(2, 4))
        self.reg_transfer_old_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            left_panel, text="Chuyển luôn cả Page cũ có sẵn trên Acc nguồn",
            variable=self.reg_transfer_old_var, font=("Segoe UI", 12)
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # 2. Danh sách Acc nguồn
        acc_hdr = ctk.CTkFrame(left_panel, fg_color="transparent")
        acc_hdr.pack(fill="x", padx=10)
        self.reg_acc_count_lbl = ctk.CTkLabel(
            acc_hdr, text="2. Danh sách Acc nguồn (0 dòng)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8"
        )
        self.reg_acc_count_lbl.pack(side="left")
        ctk.CTkButton(
            acc_hdr, text="Nạp file", width=72, height=24,
            fg_color="#2a3245", hover_color="#39445d",
            command=lambda: self._load_file_to_textbox(self.reg_acc_box, self._update_reg_acc_count)
        ).pack(side="right")

        self.reg_acc_box = ctk.CTkTextbox(left_panel, height=120, font=("Consolas", 11))
        self.reg_acc_box.pack(fill="x", padx=10, pady=(4, 4))
        self.reg_acc_box.bind("<KeyRelease>", lambda _e: self._update_reg_acc_count())

        self.reg_default_pwd = ctk.CTkEntry(
            left_panel, placeholder_text="Mật khẩu mặc định (nếu dòng Acc chưa kèm Pass)"
        )
        self.reg_default_pwd.pack(fill="x", padx=10, pady=(0, 8))

        # 3. Tên Page
        self._section_label(left_panel, "3. Cấu hình tên Page")
        name_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        name_row.pack(fill="x", padx=10, pady=(2, 4))
        self.reg_name_mode = ctk.CTkOptionMenu(
            name_row, values=["Tên Việt", "Tên US", "File names.txt"], width=140
        )
        self.reg_name_mode.pack(side="left", padx=(0, 6))
        self.reg_name_file = ctk.CTkEntry(name_row, placeholder_text="names.txt")
        self.reg_name_file.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            name_row, text="...", width=32,
            command=lambda: self._pick_file_to_entry(self.reg_name_file, [("Text", "*.txt")])
        ).pack(side="right")

        # 4. Kho ảnh Avatar & Cover
        self._section_label(left_panel, "4. Kho ảnh Avatar & Cover Pro5")
        self.reg_buff_media_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            left_panel, text="Tự động Up Avatar + Ảnh bìa + Bài chào mừng",
            variable=self.reg_buff_media_var, font=("Segoe UI", 12)
        ).pack(anchor="w", padx=10, pady=(2, 4))

        media_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        media_row.pack(fill="x", padx=10, pady=(0, 8))
        self.reg_media_path = ctk.CTkEntry(
            media_row, placeholder_text="Để trống = tự quét thư mục avatars/ hoặc .zip"
        )
        self.reg_media_path.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            media_row, text="File", width=44,
            command=lambda: self._pick_file_to_entry(
                self.reg_media_path, [("Ảnh / Zip / Txt", "*.jpg *.jpeg *.png *.webp *.zip *.txt")]
            )
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            media_row, text="Thư mục", width=62,
            command=lambda: self._pick_dir_to_entry(self.reg_media_path)
        ).pack(side="right")

        # 5. User-Agent & Proxy
        self._section_label(left_panel, "5. User-Agent & Proxy (tùy chọn)")
        self.reg_ua_mode = ctk.CTkOptionMenu(
            left_panel, values=["Cố định 1 UA / Nick (Khuyên dùng)", "Random UA mỗi Page"]
        )
        self.reg_ua_mode.pack(fill="x", padx=10, pady=(2, 6))

        px_hdr = ctk.CTkFrame(left_panel, fg_color="transparent")
        px_hdr.pack(fill="x", padx=10)
        ctk.CTkLabel(px_hdr, text="Danh sách Proxy (nếu acc chưa gắn proxy riêng):", font=("Segoe UI", 11)).pack(side="left")
        ctk.CTkButton(
            px_hdr, text="Nạp file", width=72, height=22,
            fg_color="#2a3245", hover_color="#39445d",
            command=lambda: self._load_file_to_textbox(self.reg_proxy_box)
        ).pack(side="right")
        self.reg_proxy_box = ctk.CTkTextbox(left_panel, height=62, font=("Consolas", 11))
        self.reg_proxy_box.pack(fill="x", padx=10, pady=(3, 8))

        # 6. Thông số chạy
        self._section_label(left_panel, "6. Thông số chạy & Luồng")
        grid_cfg = ctk.CTkFrame(left_panel, fg_color="transparent")
        grid_cfg.pack(fill="x", padx=10, pady=(2, 10))
        grid_cfg.columnconfigure((0, 1), weight=1)

        self.reg_pages_per_acc = self._labeled_spin_entry(grid_cfg, "Page / Acc:", "4", 0, 0)
        self.reg_verify_delay = self._labeled_spin_entry(grid_cfg, "Đợi Check Live (s):", "10", 0, 1)
        self.reg_delay_between = self._labeled_spin_entry(grid_cfg, "Nghỉ giữa Page (s):", "5", 1, 0)
        self.reg_threads = self._labeled_spin_entry(grid_cfg, "Số luồng:", "3", 1, 1)

        # Nút điều khiển
        ctrl_row = ctk.CTkFrame(left_panel, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=10, pady=(4, 12))
        self.btn_reg_start = ctk.CTkButton(
            ctrl_row, text="▶ BẮT ĐẦU CHẠY", height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#16a34a", hover_color="#15803d",
            command=self._start_reg_workflow
        )
        self.btn_reg_start.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_reg_stop = ctk.CTkButton(
            ctrl_row, text="⏹ DỪNG HÀNG ĐỢI", height=40, width=130,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c",
            state="disabled",
            command=self._stop_reg_workflow
        )
        self.btn_reg_stop.pack(side="right")

        # --- CỘT PHẢI: DASHBOARD THỐNG KÊ + BẢNG + LIVE LOG ---
        right_panel = ctk.CTkFrame(container, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True)

        # Thẻ thống kê
        stats_bar = ctk.CTkFrame(right_panel, fg_color="transparent")
        stats_bar.pack(fill="x", pady=(0, 8))
        stats_bar.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.stat_cards = {
            "total_acc": self._create_stat_card(stats_bar, "TỔNG ACC", "0", "#38bdf8", 0),
            "total_pages": self._create_stat_card(stats_bar, "PAGE SỐNG", "0", "#22c55e", 1),
            "total_invited": self._create_stat_card(stats_bar, "CHUYỂN OK", "0", "#06b6d4", 2),
            "total_fail": self._create_stat_card(stats_bar, "XỊT / LIMIT", "0", "#eab308", 3),
            "total_net": self._create_stat_card(stats_bar, "LỖI MẠNG", "0", "#f97316", 4),
            "total_die": self._create_stat_card(stats_bar, "ACC DIE", "0", "#ef4444", 5),
        }

        # Bảng tiến trình
        table_frame = ctk.CTkFrame(right_panel, fg_color="#181c26")
        table_frame.pack(fill="both", expand=True, pady=(0, 8))

        cols = ("stt", "uid", "name", "prog", "status")
        self.reg_tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", style="Dark.Treeview"
        )
        self.reg_tree.heading("stt", text="STT")
        self.reg_tree.heading("uid", text="UID Nick Reg")
        self.reg_tree.heading("name", text="Tên Nick")
        self.reg_tree.heading("prog", text="Page Có")
        self.reg_tree.heading("status", text="Quá trình / Trạng thái hiện tại")

        self.reg_tree.column("stt", width=48, anchor="center", stretch=False)
        self.reg_tree.column("uid", width=140, anchor="w", stretch=False)
        self.reg_tree.column("name", width=145, anchor="w", stretch=False)
        self.reg_tree.column("prog", width=72, anchor="center", stretch=False)
        self.reg_tree.column("status", width=460, anchor="w", stretch=True)

        self.reg_tree.tag_configure("done", foreground="#4ade80")
        self.reg_tree.tag_configure("running", foreground="#38bdf8")
        self.reg_tree.tag_configure("waiting_check", foreground="#facc15")
        self.reg_tree.tag_configure("limit", foreground="#fbbf24")
        self.reg_tree.tag_configure("net_err", foreground="#fb923c")
        self.reg_tree.tag_configure("no_page", foreground="#e879f9")
        self.reg_tree.tag_configure("die", foreground="#f87171")
        self.reg_tree.tag_configure("ready", foreground="#94a3b8")

        reg_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.reg_tree.yview)
        self.reg_tree.configure(yscrollcommand=reg_scroll.set)
        self.reg_tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        reg_scroll.pack(side="right", fill="y", pady=6, padx=(0, 4))

        # Khung Live Logs
        log_frame = ctk.CTkFrame(right_panel, height=225, fg_color="#141824")
        log_frame.pack(fill="x")
        log_frame.pack_propagate(False)

        log_hdr = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_hdr.pack(fill="x", padx=8, pady=(4, 0))
        ctk.CTkLabel(
            log_hdr, text="📋 NHẬT KÝ TIẾN TRÌNH TRỰC TIẾP",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#c084fc"
        ).pack(side="left")
        ctk.CTkButton(
            log_hdr, text="Xóa log", width=66, height=22,
            fg_color="#262c3d", hover_color="#343d54",
            command=self._clear_reg_log
        ).pack(side="right")

        self.reg_log_box = ctk.CTkTextbox(
            log_frame, font=("Consolas", 11), fg_color="#0f121a", text_color="#e2e8f0"
        )
        self.reg_log_box.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        self._init_log_tags(self.reg_log_box)

    def _update_reg_acc_count(self):
        lines = [l for l in self.reg_acc_box.get("1.0", "end").splitlines() if l.strip()]
        self.reg_acc_count_lbl.configure(text=f"2. Danh sách Acc nguồn ({len(lines)} dòng)")

    def _clear_reg_log(self):
        self.reg_log_box.configure(state="normal")
        self.reg_log_box.delete("1.0", "end")
        self.reg_log_box.configure(state="disabled")

    def _start_reg_workflow(self):
        if self.reg_running:
            return

        raw_lines = [l.strip() for l in self.reg_acc_box.get("1.0", "end").splitlines() if l.strip()]
        parsed_items = core.parse_universal_lines(raw_lines)
        if not parsed_items:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập danh sách Acc nguồn hợp lệ.")
            return

        # Đọc thông số số nguyên
        try:
            pages_per_nick = max(1, int(self.reg_pages_per_acc.get().strip() or "4"))
            verify_delay = max(1, int(self.reg_verify_delay.get().strip() or "10"))
            delay_between = max(0, int(self.reg_delay_between.get().strip() or "5"))
            num_threads = max(1, min(50, int(self.reg_threads.get().strip() or "3")))
        except ValueError:
            messagebox.showerror("Sai thông số", "Số Page, Delay và Số luồng phải là số nguyên.")
            return

        # Loại tên Page
        name_choice = self.reg_name_mode.get()
        name_type = "viet"
        custom_names: List[str] = []
        if name_choice == "Tên US":
            name_type = "us"
        elif name_choice == "File names.txt":
            fn = self.reg_name_file.get().strip() or "names.txt"
            if os.path.isfile(fn):
                with open(fn, "r", encoding="utf-8", errors="ignore") as f:
                    custom_names = [l.strip() for l in f if l.strip()]
                name_type = "custom" if custom_names else "viet"
            else:
                messagebox.showwarning("Không thấy file tên", f"Không tìm thấy '{fn}', tự chuyển về Tên Việt.")
                name_type = "viet"

        # Proxy toàn cục
        px_lines = [l.strip() for l in self.reg_proxy_box.get("1.0", "end").splitlines() if l.strip()]
        global_proxies = [pl for pl in px_lines if core.parse_proxy(pl)]

        holder_raw = self.reg_holder_entry.get().strip()
        default_pwd = self.reg_default_pwd.get().strip()
        ua_mode = "random" if "Random" in self.reg_ua_mode.get() else "fixed"
        auto_buff_media = self.reg_buff_media_var.get()
        custom_media_path = self.reg_media_path.get().strip()
        transfer_old_pages = self.reg_transfer_old_var.get()

        # Reset UI & stats
        self.reg_running = True
        self.btn_reg_start.configure(state="disabled", text="⏳ ĐANG KHỞI TẠO...")
        self.btn_reg_stop.configure(state="normal")
        self._clear_reg_log()
        for iid in self.reg_tree.get_children():
            self.reg_tree.delete(iid)
        self.reg_tree_iids.clear()
        self.reg_tasks = []
        self.reg_stats = {
            "total_holder_acc": 0,
            "total_pages": 0,
            "total_invited": 0,
            "total_no_page": 0,
            "total_limited": 0,
            "total_net_err": 0,
            "total_token_die": 0,
        }

        # Khởi tạo Nick Mẹ + Tạo Queue trong background thread để không treo UI
        def _bootstrap():
            holder_targets = []
            if holder_raw and holder_raw != "0":
                GUI_LOG_QUEUE.put(("Đang xác thực thông tin Nick Mẹ nhận Page...\n", "cyan"))
                parsed_targets = core.parse_holder_target(holder_raw)
                for t in parsed_targets:
                    if t.get("token") and not t.get("uid"):
                        info_nhan = core.get_id(t["token"], proxy=t.get("proxy"))
                        if info_nhan:
                            t["uid"], t_name = info_nhan
                            GUI_LOG_QUEUE.put((f"✔ Nick Mẹ: {t_name} ({t['uid']}) -> Bật Auto Accept Full 4 Bước!\n", "success"))
                            holder_targets.append(t)
                        else:
                            GUI_LOG_QUEUE.put(("✗ Token Nick Mẹ không hợp lệ hoặc DIE!\n", "error"))
                    elif t.get("uid"):
                        if t.get("token"):
                            info_nhan = core.get_id(t["token"], proxy=t.get("proxy"))
                            t_name = info_nhan[1] if info_nhan else "Nick Mẹ"
                            GUI_LOG_QUEUE.put((f"✔ Nick Mẹ: {t_name} ({t['uid']}) -> Auto Accept Full 4 Bước!\n", "success"))
                        else:
                            GUI_LOG_QUEUE.put((f"✔ UID Nick Mẹ: {t['uid']} -> Bắn lời mời Bước 1 & 2.\n", "success"))
                        holder_targets.append(t)

            task_q: queue.Queue = queue.Queue()
            tasks: List[core.AccountTask] = []
            for idx, it in enumerate(parsed_items):
                assigned_px = global_proxies[idx % len(global_proxies)] if global_proxies and not it.get("proxy") else None
                assigned_target = holder_targets[idx % len(holder_targets)] if holder_targets else None
                t_obj = core.AccountTask(
                    acc_id=idx + 1,
                    item=it,
                    target_pages=pages_per_nick,
                    ua_mode=ua_mode,
                    default_pwd=default_pwd,
                    assigned_proxy=assigned_px,
                    holder_target=assigned_target,
                    auto_buff_media=auto_buff_media,
                    custom_media_path=custom_media_path,
                    transfer_old_pages=transfer_old_pages,
                )
                tasks.append(t_obj)
                task_q.put(t_obj)

            self.reg_tasks = tasks
            self.reg_queue = task_q
            self.after(0, self._populate_reg_tree)

            actual_threads = min(num_threads, len(tasks))
            workers = []
            for t_id in range(1, actual_threads + 1):
                th = threading.Thread(
                    target=core.worker_reg_account,
                    args=(t_id, task_q, name_type, custom_names, verify_delay, delay_between, self.reg_stats),
                    daemon=True,
                )
                workers.append(th)
                th.start()

            self.reg_workers = workers
            self.after(0, lambda: self.btn_reg_start.configure(text="🟢 ĐANG CHẠY..."))

            for th in workers:
                th.join()

            self.reg_running = False
            GUI_LOG_QUEUE.put(("=== HOÀN TẤT TOÀN BỘ TIẾN TRÌNH REG & CHUYỂN PAGE ===\n", "success"))
            self.after(0, self._on_reg_finished)

        threading.Thread(target=_bootstrap, daemon=True).start()

    def _populate_reg_tree(self):
        for acc in self.reg_tasks:
            uid_disp = acc.mother_uid or acc.pre_uid or "Unknown"
            iid = self.reg_tree.insert(
                "", "end",
                values=(acc.acc_id, uid_disp, acc.mother_name or "Chờ...", f"0/{acc.target_pages}", acc.current_action),
                tags=(acc.status,)
            )
            self.reg_tree_iids[acc.acc_id] = iid
        self.stat_cards["total_acc"].configure(text=str(len(self.reg_tasks)))

    def _stop_reg_workflow(self):
        if not self.reg_running or not self.reg_queue:
            return
        cleared = 0
        while True:
            try:
                acc = self.reg_queue.get_nowait()
                acc.status = "limit"
                acc.current_action = "Đã dừng bởi người dùng"
                self.reg_queue.task_done()
                cleared += 1
            except queue.Empty:
                break
        self.btn_reg_stop.configure(state="disabled")
        GUI_LOG_QUEUE.put((f"⏹ Đã hủy {cleared} Acc đang chờ trong hàng đợi. Đang đợi các luồng đang chạy kết thúc bước hiện tại...\n", "warn"))

    def _on_reg_finished(self):
        self._refresh_reg_dashboard()
        self.btn_reg_start.configure(state="normal", text="▶ BẮT ĐẦU CHẠY")
        self.btn_reg_stop.configure(state="disabled")

    def _refresh_reg_dashboard(self):
        if not self.reg_tasks:
            return
        for acc in self.reg_tasks:
            iid = self.reg_tree_iids.get(acc.acc_id)
            if not iid:
                continue
            uid_disp = (acc.mother_uid or acc.pre_uid or "Unknown")[:22]
            name_disp = (acc.mother_name or "Đang xử lý...")[:22]
            prog = f"{acc.pages_created}/{acc.target_pages}"
            status_text = acc.last_result if acc.status == "done" else acc.current_action
            self.reg_tree.item(iid, values=(acc.acc_id, uid_disp, name_disp, prog, status_text), tags=(acc.status,))

        self.stat_cards["total_acc"].configure(text=str(len(self.reg_tasks)))
        self.stat_cards["total_pages"].configure(text=str(self.reg_stats.get("total_pages", 0)))
        self.stat_cards["total_invited"].configure(text=str(self.reg_stats.get("total_invited", 0)))
        fail_lim = self.reg_stats.get("total_no_page", 0) + self.reg_stats.get("total_limited", 0)
        self.stat_cards["total_fail"].configure(text=str(fail_lim))
        self.stat_cards["total_net"].configure(text=str(self.reg_stats.get("total_net_err", 0)))
        self.stat_cards["total_die"].configure(text=str(self.reg_stats.get("total_token_die", 0)))

    # ==========================================================================
    # TAB 2: QUÉT & CHUYỂN PAGE ĐỘC LẬP
    # ==========================================================================
    def _build_tab_transfer(self):
        top_box = ctk.CTkFrame(self.tab_transfer, fg_color="#181c26")
        top_box.pack(fill="x", pady=(0, 8))

        # Trái: Acc cầm Page
        src_frame = ctk.CTkFrame(top_box, fg_color="transparent")
        src_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        src_hdr = ctk.CTkFrame(src_frame, fg_color="transparent")
        src_hdr.pack(fill="x")
        ctk.CTkLabel(
            src_hdr, text="1. Danh sách Nick đang cầm Page (UID|Pass|Cookie|Token...)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8"
        ).pack(side="left")
        ctk.CTkButton(
            src_hdr, text="Nạp file", width=74, height=24,
            fg_color="#2a3245", hover_color="#39445d",
            command=lambda: self._load_file_to_textbox(self.tr_src_box)
        ).pack(side="right")

        self.tr_src_box = ctk.CTkTextbox(src_frame, height=96, font=("Consolas", 11))
        self.tr_src_box.pack(fill="x", pady=(4, 6))

        src_sub = ctk.CTkFrame(src_frame, fg_color="transparent")
        src_sub.pack(fill="x")
        self.tr_default_pwd = ctk.CTkEntry(
            src_sub, placeholder_text="Mật khẩu mặc định nick cầm Page (nếu thiếu trong dòng)"
        )
        self.tr_default_pwd.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.btn_tr_scan = ctk.CTkButton(
            src_sub, text="🔍 QUÉT DANH SÁCH PAGE", width=185, height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._start_scan_pages
        )
        self.btn_tr_scan.pack(side="right")

        # Phải: Nick nhận Page + nút chuyển
        dst_frame = ctk.CTkFrame(top_box, width=430, fg_color="#141824")
        dst_frame.pack(side="right", fill="y", padx=(0, 10), pady=8)
        dst_frame.pack_propagate(False)

        ctk.CTkLabel(
            dst_frame, text="2. Tài khoản nhận Page (UID hoặc Token Auto Accept)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#4ade80"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.tr_target_entry = ctk.CTkEntry(
            dst_frame, placeholder_text="Nhập chỉ UID (bắn mời) hoặc Token/Dòng full (Auto Accept)"
        )
        self.tr_target_entry.pack(fill="x", padx=12, pady=(0, 8))

        d_row = ctk.CTkFrame(dst_frame, fg_color="transparent")
        d_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(d_row, text="Delay giữa mỗi Page (giây):").pack(side="left")
        self.tr_delay_entry = ctk.CTkEntry(d_row, width=70)
        self.tr_delay_entry.insert(0, "2")
        self.tr_delay_entry.pack(side="left", padx=8)

        tr_btn_row = ctk.CTkFrame(dst_frame, fg_color="transparent")
        tr_btn_row.pack(fill="x", padx=12, pady=(4, 10))
        self.btn_tr_run = ctk.CTkButton(
            tr_btn_row, text="🚀 CHUYỂN PAGE ĐÃ CHỌN", height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#16a34a", hover_color="#15803d",
            command=self._start_transfer_selected
        )
        self.btn_tr_run.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_tr_stop = ctk.CTkButton(
            tr_btn_row, text="⏹ DỪNG", width=80, height=38,
            fg_color="#dc2626", hover_color="#b91c1c", state="disabled",
            command=self._stop_transfer_selected
        )
        self.btn_tr_stop.pack(side="right")

        # Thanh công cụ bảng Page
        bar_mid = ctk.CTkFrame(self.tab_transfer, fg_color="transparent")
        bar_mid.pack(fill="x", pady=(0, 4))
        self.tr_summary_lbl = ctk.CTkLabel(
            bar_mid, text="Chưa quét Page nào (Click vào từng dòng để chọn / bỏ chọn Page)",
            font=("Segoe UI", 12), text_color="#cbd5e1"
        )
        self.tr_summary_lbl.pack(side="left")

        ctk.CTkButton(
            bar_mid, text="Bỏ chọn hết", width=95, height=26,
            fg_color="#262c3d", hover_color="#343d54",
            command=lambda: self._toggle_all_tr_pages(False)
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            bar_mid, text="Chọn tất cả", width=95, height=26,
            fg_color="#262c3d", hover_color="#343d54",
            command=lambda: self._toggle_all_tr_pages(True)
        ).pack(side="right")

        # Bảng danh sách Page
        mid_table = ctk.CTkFrame(self.tab_transfer, fg_color="#181c26")
        mid_table.pack(fill="both", expand=True, pady=(0, 8))

        cols = ("chk", "src_uid", "page_name", "page_id", "profile_uid", "status")
        self.tr_tree = ttk.Treeview(mid_table, columns=cols, show="headings", style="Dark.Treeview")
        self.tr_tree.heading("chk", text="Chọn")
        self.tr_tree.heading("src_uid", text="Nick Cầm Page")
        self.tr_tree.heading("page_name", text="Tên Page")
        self.tr_tree.heading("page_id", text="Page ID")
        self.tr_tree.heading("profile_uid", text="ProfileUID (615...)")
        self.tr_tree.heading("status", text="Trạng thái chuyển")

        self.tr_tree.column("chk", width=55, anchor="center", stretch=False)
        self.tr_tree.column("src_uid", width=150, anchor="w", stretch=False)
        self.tr_tree.column("page_name", width=230, anchor="w", stretch=False)
        self.tr_tree.column("page_id", width=145, anchor="w", stretch=False)
        self.tr_tree.column("profile_uid", width=155, anchor="w", stretch=False)
        self.tr_tree.column("status", width=360, anchor="w", stretch=True)

        self.tr_tree.tag_configure("ok", foreground="#4ade80")
        self.tr_tree.tag_configure("warn", foreground="#facc15")
        self.tr_tree.tag_configure("err", foreground="#f87171")
        self.tr_tree.tag_configure("run", foreground="#38bdf8")

        self.tr_tree.bind("<ButtonRelease-1>", self._on_tr_row_click)

        tr_sc = ttk.Scrollbar(mid_table, orient="vertical", command=self.tr_tree.yview)
        self.tr_tree.configure(yscrollcommand=tr_sc.set)
        self.tr_tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        tr_sc.pack(side="right", fill="y", pady=6, padx=(0, 4))

        # Log Tab 2
        self.tr_log_box = ctk.CTkTextbox(
            self.tab_transfer, height=145, font=("Consolas", 11),
            fg_color="#0f121a", text_color="#e2e8f0"
        )
        self.tr_log_box.pack(fill="x")
        self._init_log_tags(self.tr_log_box)

    def _tr_log(self, msg: str, tag: str = "info"):
        now_s = datetime.datetime.now().strftime("%H:%M:%S")
        self.tr_log_queue.put((f"[{now_s}] {msg}\n", tag))

    def _on_tr_row_click(self, event):
        if self.tr_running:
            return
        iid = self.tr_tree.identify_row(event.y)
        if not iid:
            return
        idx = int(iid)
        if 0 <= idx < len(self.tr_pages_data):
            item = self.tr_pages_data[idx]
            item["selected"] = not item["selected"]
            vals = list(self.tr_tree.item(iid, "values"))
            vals[0] = "☑" if item["selected"] else "☐"
            self.tr_tree.item(iid, values=vals)
            self._update_tr_summary()

    def _toggle_all_tr_pages(self, state: bool):
        if self.tr_running:
            return
        for idx, item in enumerate(self.tr_pages_data):
            item["selected"] = state
            iid = str(idx)
            if self.tr_tree.exists(iid):
                vals = list(self.tr_tree.item(iid, "values"))
                vals[0] = "☑" if state else "☐"
                self.tr_tree.item(iid, values=vals)
        self._update_tr_summary()

    def _update_tr_summary(self):
        sel = sum(1 for x in self.tr_pages_data if x["selected"])
        self.tr_summary_lbl.configure(
            text=f"Tổng cộng {len(self.tr_pages_data)} Page | Đang chọn: {sel} Page (Click dòng để bật/tắt)"
        )

    def _start_scan_pages(self):
        if self.tr_scanning or self.tr_running:
            return
        raw_lines = [l.strip() for l in self.tr_src_box.get("1.0", "end").splitlines() if l.strip()]
        creds = core.parse_universal_lines(raw_lines)
        if not creds:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập ít nhất 1 Nick cầm Page hợp lệ.")
            return

        default_pwd = self.tr_default_pwd.get().strip()
        self.tr_scanning = True
        self.btn_tr_scan.configure(state="disabled", text="⏳ ĐANG QUÉT...")
        self.tr_pages_data = []
        for iid in self.tr_tree.get_children():
            self.tr_tree.delete(iid)

        def _worker_scan():
            self._tr_log(f"Bắt đầu quét Page trên {len(creds)} nick nguồn...", "cyan")
            found_items: List[Dict[str, Any]] = []

            for i, cred in enumerate(creds, 1):
                token = cred.get("token", "")
                password = cred.get("pwd") or default_pwd
                uid_file = cred.get("uid", "")
                px = cred.get("proxy")

                if not token and uid_file and password:
                    self._tr_log(f"[Nick #{i}] Chưa có Token -> Tự động Login Bloks CAA v5 cho {uid_file}...", "warn")
                    l_res = core.login_and_get_token(cred)
                    if l_res.get("success"):
                        token = l_res["token"]
                    else:
                        self._tr_log(f"[Nick #{i}] Login thất bại: {l_res.get('message')}", "error")
                        continue

                info = core.get_id(token, proxy=px)
                if info is None and uid_file and password:
                    self._tr_log(f"[Nick #{i}] Token cũ hết hạn -> Đang Login lại...", "warn")
                    l_res = core.login_and_get_token(cred)
                    if l_res.get("success"):
                        token = l_res["token"]
                        info = core.get_id(token, proxy=px)

                if info is None:
                    if not uid_file:
                        self._tr_log(f"[Nick #{i}] Token DIE & không có UID -> Bỏ qua.", "error")
                        continue
                    id_acc, name_acc = str(uid_file), f"UID {uid_file}"
                else:
                    id_acc, name_acc = str(uid_file or info[0]), info[1]

                self._tr_log(f"[Nick #{i}] Đang quét Page của {name_acc} ({id_acc})...", "cyan")
                pages = core.get_all_pages(token, id_acc, proxy=px)
                self._tr_log(f"[Nick #{i}] Tìm thấy {len(pages)} Page.", "success" if pages else "warn")

                for p in pages:
                    found_items.append({
                        "selected": True,
                        "src_uid": id_acc,
                        "src_name": name_acc,
                        "src_token": token,
                        "password": password,
                        "src_proxy": px,
                        "page_id": p["page_id"],
                        "page_uid": p["page_uid"],
                        "page_name": p["page_name"],
                        "page_token": p["page_token"],
                        "status": "Sẵn sàng",
                    })

            self.tr_pages_data = found_items
            self.tr_ui_queue.put(("scan_done", None))

        threading.Thread(target=_worker_scan, daemon=True).start()

    def _start_transfer_selected(self):
        if self.tr_running or self.tr_scanning:
            return
        selected_indices = [i for i, x in enumerate(self.tr_pages_data) if x["selected"]]
        if not selected_indices:
            messagebox.showwarning("Chưa chọn Page", "Hãy quét và chọn ít nhất 1 Page để chuyển.")
            return

        raw_target = self.tr_target_entry.get().strip()
        if not raw_target:
            messagebox.showwarning("Thiếu Nick Nhận", "Vui lòng nhập UID hoặc Token của tài khoản nhận Page.")
            return

        try:
            delay = max(0.0, float(self.tr_delay_entry.get().strip() or "2"))
        except ValueError:
            messagebox.showerror("Sai thông số", "Delay phải là số >= 0.")
            return

        default_pwd = self.tr_default_pwd.get().strip()
        self.tr_running = True
        self.tr_stop_flag.clear()
        self.btn_tr_run.configure(state="disabled", text="🟢 ĐANG CHUYỂN...")
        self.btn_tr_scan.configure(state="disabled")
        self.btn_tr_stop.configure(state="normal")

        def _worker_transfer():
            # Xác định tài khoản đích
            id_acc_nhan = ""
            name_acc_nhan = ""
            token_nhan: Optional[str] = None
            receiver_proxy: Optional[str] = None
            target_page_ids = set()

            if raw_target.isdigit() and 5 <= len(raw_target) <= 22:
                id_acc_nhan = raw_target
                name_acc_nhan = f"UID {id_acc_nhan}"
                self._tr_log(f"Đích nhận: UID {id_acc_nhan} (Bắn lời mời Bước 1 & 2).", "success")
            else:
                targets = core.parse_holder_target(raw_target)
                if not targets:
                    self._tr_log("Dữ liệu Nick Nhận không hợp lệ!", "error")
                    self.tr_ui_queue.put(("transfer_done", None))
                    return
                t0 = targets[0]
                t_uid = t0.get("uid") or ""
                t_tok = t0.get("token")
                receiver_proxy = t0.get("proxy")
                if t_tok:
                    info_n = core.get_id(t_tok, proxy=receiver_proxy)
                    if info_n:
                        id_acc_nhan, name_acc_nhan = info_n
                        token_nhan = t_tok
                        target_page_ids = core.get_managed_page_ids(token_nhan, proxy=receiver_proxy)
                        self._tr_log(
                            f"Đích nhận: {name_acc_nhan} ({id_acc_nhan}) -> Auto Accept Full 4 Bước (Đang cầm {len(target_page_ids)} Page).",
                            "success"
                        )
                    elif t_uid:
                        id_acc_nhan, name_acc_nhan = t_uid, f"UID {t_uid}"
                        self._tr_log(f"Token nhận DIE -> Chuyển sang bắn mời tới UID {id_acc_nhan}.", "warn")
                elif t_uid:
                    id_acc_nhan, name_acc_nhan = t_uid, f"UID {t_uid}"
                    self._tr_log(f"Đích nhận: UID {id_acc_nhan} (Bắn lời mời Bước 1 & 2).", "success")

            if not id_acc_nhan:
                self._tr_log("Không xác định được UID tài khoản nhận!", "error")
                self.tr_ui_queue.put(("transfer_done", None))
                return

            ok_cnt, fail_cnt, skip_cnt = 0, 0, 0
            total = len(selected_indices)

            for pos, idx in enumerate(selected_indices, 1):
                if self.tr_stop_flag.is_set():
                    self._tr_log("⏹ Đã dừng chuyển Page theo yêu cầu.", "warn")
                    break

                item = self.tr_pages_data[idx]
                p_id = item["page_id"]
                p_uid = item["page_uid"]
                p_name = item["page_name"]
                pwd = item["password"] or default_pwd

                if p_id in target_page_ids or p_uid in target_page_ids:
                    skip_cnt += 1
                    self.tr_ui_queue.put(("row_status", (idx, "⏭️ Bỏ qua (Đã là Admin)", "warn")))
                    self._tr_log(f"[{pos}/{total}] Bỏ qua '{p_name}': Đích đã có quyền quản trị.", "warn")
                    continue

                self.tr_ui_queue.put(("row_status", (idx, "🔄 Đang xử lý...", "run")))
                self._tr_log(f"[{pos}/{total}] Đang chuyển '{p_name}' (ID: {p_id} | ProfileUID: {p_uid})...", "cyan")

                tr_res = core.execute_super_transfer(
                    page_uid=p_uid,
                    page_id=p_id,
                    page_token=item["page_token"],
                    sender_token=item["src_token"],
                    password=pwd,
                    target_uid=id_acc_nhan,
                    receiver_token=token_nhan,
                    sender_proxy=item["src_proxy"],
                    receiver_proxy=receiver_proxy,
                    step_callback=lambda m, _i=idx: self.tr_ui_queue.put(("row_status", (_i, m, "run")))
                )

                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st = tr_res.get("status", "FAILED")
                msg_res = tr_res.get("message", "")

                if st == "SUCCESS":
                    ok_cnt += 1
                    target_page_ids.add(p_id)
                    target_page_ids.add(p_uid)
                    self.tr_ui_queue.put(("row_status", (idx, f"✅ Thành công (Auto Accept -> {id_acc_nhan})", "ok")))
                    self._tr_log(f"✅ '{p_name}': Chuyển & Auto Accept thành công!", "success")
                    with core.FILE_LOCK:
                        with open("output_chuyen_page.txt", "a", encoding="utf-8") as f:
                            f.write(f"{now_str}|SUCCESS|{p_id}|{p_uid}|{p_name}|From:{item['src_uid']}|To:{id_acc_nhan}\n")
                elif st == "INVITED_ONLY":
                    if not token_nhan:
                        ok_cnt += 1
                        self.tr_ui_queue.put(("row_status", (idx, f"✅ Đã bắn lời mời sang {id_acc_nhan}", "ok")))
                        self._tr_log(f"✅ '{p_name}': Đã bắn lời mời Full Admin sang UID {id_acc_nhan}!", "success")
                    else:
                        fail_cnt += 1
                        self.tr_ui_queue.put(("row_status", (idx, f"⚠️ {msg_res}", "warn")))
                        self._tr_log(f"⚠️ '{p_name}': {msg_res}", "warn")
                    with core.FILE_LOCK:
                        with open("output_chuyen_page.txt", "a", encoding="utf-8") as f:
                            f.write(f"{now_str}|INVITED_ONLY|{p_id}|{p_uid}|{p_name}|From:{item['src_uid']}|To:{id_acc_nhan}|{msg_res}\n")
                else:
                    fail_cnt += 1
                    self.tr_ui_queue.put(("row_status", (idx, f"❌ {msg_res}", "err")))
                    self._tr_log(f"❌ '{p_name}': {msg_res}", "error")

                if pos < total and delay > 0 and not self.tr_stop_flag.is_set():
                    time.sleep(delay)

            self._tr_log(f"=== XONG: Thành công {ok_cnt} | Thất bại {fail_cnt} | Bỏ qua {skip_cnt} ===", "success")
            self.tr_ui_queue.put(("transfer_done", None))

        threading.Thread(target=_worker_transfer, daemon=True).start()

    def _stop_transfer_selected(self):
        self.tr_stop_flag.set()
        self.btn_tr_stop.configure(state="disabled")

    # ==========================================================================
    # TAB 3: GET TOKEN EAAAAU (BLOKS CAA V5)
    # ==========================================================================
    def _build_tab_token(self):
        container = ctk.CTkFrame(self.tab_token, fg_color="transparent")
        container.pack(fill="both", expand=True)

        left = ctk.CTkFrame(container, width=420, fg_color="#181c26")
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        hdr = ctk.CTkFrame(left, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            hdr, text="Danh sách Acc (UID|Pass|Cookie hoặc UID|Pass|2FA)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#facc15"
        ).pack(side="left")
        ctk.CTkButton(
            hdr, text="Nạp file", width=72, height=24,
            fg_color="#2a3245", hover_color="#39445d",
            command=lambda: self._load_file_to_textbox(self.tk_input_box)
        ).pack(side="right")

        self.tk_input_box = ctk.CTkTextbox(left, font=("Consolas", 11))
        self.tk_input_box.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        cfg_row = ctk.CTkFrame(left, fg_color="transparent")
        cfg_row.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(cfg_row, text="Số luồng chạy:").pack(side="left")
        self.tk_threads_entry = ctk.CTkEntry(cfg_row, width=70)
        self.tk_threads_entry.insert(0, "3")
        self.tk_threads_entry.pack(side="left", padx=8)

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 12))
        self.btn_tk_start = ctk.CTkButton(
            btn_row, text="▶ LẤY TOKEN EAAAAU", height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#16a34a", hover_color="#15803d",
            command=self._start_get_token
        )
        self.btn_tk_start.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.btn_tk_stop = ctk.CTkButton(
            btn_row, text="⏹ DỪNG", width=85, height=38,
            fg_color="#dc2626", hover_color="#b91c1c", state="disabled",
            command=self._stop_get_token
        )
        self.btn_tk_stop.pack(side="right")

        # Phải: Kết quả Token
        right = ctk.CTkFrame(container, fg_color="#181c26")
        right.pack(side="right", fill="both", expand=True)

        top_res = ctk.CTkFrame(right, fg_color="transparent")
        top_res.pack(fill="x", padx=10, pady=8)
        self.tk_stat_lbl = ctk.CTkLabel(
            top_res, text="Tổng: 0  |  Thành công: 0  |  Thất bại: 0  |  Lưu tự động: tokens_eaaau.txt",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#cbd5e1"
        )
        self.tk_stat_lbl.pack(side="left")
        ctk.CTkButton(
            top_res, text="📋 Copy dòng thành công", width=165, height=28,
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._copy_tk_success
        ).pack(side="right")

        cols = ("stt", "uid", "status", "detail")
        self.tk_tree = ttk.Treeview(right, columns=cols, show="headings", style="Dark.Treeview")
        self.tk_tree.heading("stt", text="STT")
        self.tk_tree.heading("uid", text="UID")
        self.tk_tree.heading("status", text="Trạng thái")
        self.tk_tree.heading("detail", text="Token EAAAAU / Chi tiết lỗi")

        self.tk_tree.column("stt", width=50, anchor="center", stretch=False)
        self.tk_tree.column("uid", width=155, anchor="w", stretch=False)
        self.tk_tree.column("status", width=120, anchor="center", stretch=False)
        self.tk_tree.column("detail", width=520, anchor="w", stretch=True)

        self.tk_tree.tag_configure("ok", foreground="#4ade80")
        self.tk_tree.tag_configure("err", foreground="#f87171")
        self.tk_tree.tag_configure("run", foreground="#38bdf8")

        tk_sc = ttk.Scrollbar(right, orient="vertical", command=self.tk_tree.yview)
        self.tk_tree.configure(yscrollcommand=tk_sc.set)
        self.tk_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        tk_sc.pack(side="right", fill="y", pady=(0, 10), padx=(0, 6))

    def _start_get_token(self):
        if self.tk_running:
            return
        raw_lines = [l.strip() for l in self.tk_input_box.get("1.0", "end").splitlines() if l.strip()]
        acc_list = core.parse_universal_lines(raw_lines)
        if not acc_list:
            messagebox.showwarning("Thiếu dữ liệu", "Không tìm thấy tài khoản hợp lệ.")
            return

        try:
            threads = max(1, min(20, int(self.tk_threads_entry.get().strip() or "3")))
        except ValueError:
            threads = 3

        self.tk_running = True
        self.tk_stop_flag.clear()
        self.tk_success_lines = []
        self.btn_tk_start.configure(state="disabled", text="🟢 ĐANG CHẠY...")
        self.btn_tk_stop.configure(state="normal")
        for iid in self.tk_tree.get_children():
            self.tk_tree.delete(iid)

        q_jobs: queue.Queue = queue.Queue()
        for idx, acc in enumerate(acc_list, 1):
            self.tk_tree.insert("", "end", iid=str(idx), values=(idx, acc.get("uid", ""), "Chờ...", ""))
            q_jobs.put((idx, acc))

        stats = {"total": len(acc_list), "ok": 0, "fail": 0}
        lock = threading.Lock()

        def _worker():
            while not self.tk_stop_flag.is_set():
                try:
                    idx, acc = q_jobs.get_nowait()
                except queue.Empty:
                    break
                uid = acc.get("uid", "")
                pwd = acc.get("pwd", "")
                cookie = acc.get("cookie", "")
                proxy = acc.get("proxy", "")

                self.tk_ui_queue.put(("row", (idx, uid, "Đang Login...", "Bloks CAA v5...", "run")))
                res = core.login_and_get_token(acc)

                if res.get("success"):
                    token = res.get("token", "")
                    new_ck = res.get("cookie") or cookie
                    line_out = f"{uid}|{pwd}"
                    if new_ck:
                        line_out += f"|{new_ck}"
                    line_out += f"|{token}"
                    if proxy:
                        line_out += f"|{proxy}"

                    with core.FILE_LOCK:
                        with open("tokens_eaaau.txt", "a", encoding="utf-8") as f:
                            f.write(line_out + "\n")
                    with lock:
                        stats["ok"] += 1
                        self.tk_success_lines.append(line_out)
                    self.tk_ui_queue.put(("row", (idx, uid, "✅ THÀNH CÔNG", token, "ok")))
                else:
                    with lock:
                        stats["fail"] += 1
                    self.tk_ui_queue.put(("row", (idx, uid, "❌ THẤT BẠI", res.get("message", ""), "err")))

                self.tk_ui_queue.put(("stat", dict(stats)))
                q_jobs.task_done()

        def _manager():
            ws = []
            for _ in range(min(threads, len(acc_list))):
                th = threading.Thread(target=_worker, daemon=True)
                ws.append(th)
                th.start()
            for th in ws:
                th.join()
            self.tk_ui_queue.put(("done", dict(stats)))

        threading.Thread(target=_manager, daemon=True).start()

    def _stop_get_token(self):
        self.tk_stop_flag.set()
        self.btn_tk_stop.configure(state="disabled")

    def _copy_tk_success(self):
        if not self.tk_success_lines:
            messagebox.showinfo("Trống", "Chưa có dòng Token thành công nào để copy.")
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(self.tk_success_lines))
        messagebox.showinfo("Đã copy", f"Đã copy {len(self.tk_success_lines)} dòng tài khoản + Token vào Clipboard!")

    # ==========================================================================
    # VÒNG LẶP CẬP NHẬT GIAO DIỆN CHUNG (MAIN THREAD)
    # ==========================================================================
    def _ui_poll_loop(self):
        # 1. Cập nhật Tab 1 Dashboard & Logs
        if self.reg_running:
            self._refresh_reg_dashboard()

        reg_logs = []
        for _ in range(40):
            try:
                reg_logs.append(GUI_LOG_QUEUE.get_nowait())
            except queue.Empty:
                break
        if reg_logs:
            self._append_logs(self.reg_log_box, reg_logs)

        # 2. Cập nhật Tab 2 Logs & Events
        tr_logs = []
        for _ in range(40):
            try:
                tr_logs.append(self.tr_log_queue.get_nowait())
            except queue.Empty:
                break
        if tr_logs:
            self._append_logs(self.tr_log_box, tr_logs)

        for _ in range(30):
            try:
                ev, payload = self.tr_ui_queue.get_nowait()
            except queue.Empty:
                break
            if ev == "scan_done":
                self.tr_scanning = False
                self.btn_tr_scan.configure(state="normal", text="🔍 QUÉT DANH SÁCH PAGE")
                for idx, item in enumerate(self.tr_pages_data):
                    self.tr_tree.insert(
                        "", "end", iid=str(idx),
                        values=(
                            "☑" if item["selected"] else "☐",
                            item["src_uid"],
                            item["page_name"],
                            item["page_id"],
                            item["page_uid"],
                            item["status"],
                        ),
                    )
                self._update_tr_summary()
            elif ev == "row_status":
                idx, txt, tag = payload
                iid = str(idx)
                if self.tr_tree.exists(iid):
                    vals = list(self.tr_tree.item(iid, "values"))
                    vals[5] = txt
                    self.tr_tree.item(iid, values=vals, tags=(tag,))
            elif ev == "transfer_done":
                self.tr_running = False
                self.btn_tr_run.configure(state="normal", text="🚀 CHUYỂN PAGE ĐÃ CHỌN")
                self.btn_tr_scan.configure(state="normal")
                self.btn_tr_stop.configure(state="disabled")

        # 3. Cập nhật Tab 3 Events
        for _ in range(30):
            try:
                ev, payload = self.tk_ui_queue.get_nowait()
            except queue.Empty:
                break
            if ev == "row":
                idx, uid, st, detail, tag = payload
                iid = str(idx)
                if self.tk_tree.exists(iid):
                    self.tk_tree.item(iid, values=(idx, uid, st, detail), tags=(tag,))
            elif ev == "stat":
                self.tk_stat_lbl.configure(
                    text=f"Tổng: {payload['total']}  |  Thành công: {payload['ok']}  |  Thất bại: {payload['fail']}  |  Lưu tự động: tokens_eaaau.txt"
                )
            elif ev == "done":
                self.tk_running = False
                self.btn_tk_start.configure(state="normal", text="▶ LẤY TOKEN EAAAAU")
                self.btn_tk_stop.configure(state="disabled")
                self.tk_stat_lbl.configure(
                    text=f"HOÀN TẤT — Tổng: {payload['total']}  |  Thành công: {payload['ok']}  |  Thất bại: {payload['fail']}  |  tokens_eaaau.txt"
                )

        self.after(300, self._ui_poll_loop)

    # ==========================================================================
    # HÀM PHỤ TRỢ UI
    # ==========================================================================
    def _section_label(self, parent, text: str):
        ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8"
        ).pack(anchor="w", padx=10, pady=(6, 0))

    def _labeled_spin_entry(self, parent, label: str, default: str, row: int, col: int) -> ctk.CTkEntry:
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, sticky="ew", padx=4, pady=3)
        ctk.CTkLabel(box, text=label, font=("Segoe UI", 11)).pack(anchor="w")
        ent = ctk.CTkEntry(box, height=28)
        ent.insert(0, default)
        ent.pack(fill="x", pady=(2, 0))
        return ent

    def _create_stat_card(self, parent, title: str, value: str, color: str, col: int) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent, fg_color="#181c26", corner_radius=8)
        card.grid(row=0, column=col, sticky="ew", padx=4)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8").pack(pady=(6, 0))
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
        val_lbl.pack(pady=(0, 6))
        return val_lbl

    def _init_log_tags(self, textbox: ctk.CTkTextbox):
        inner = textbox._textbox
        inner.tag_config("info", foreground="#e2e8f0")
        inner.tag_config("success", foreground="#4ade80")
        inner.tag_config("error", foreground="#f87171")
        inner.tag_config("warn", foreground="#facc15")
        inner.tag_config("cyan", foreground="#38bdf8")
        textbox.configure(state="disabled")

    def _append_logs(self, textbox: ctk.CTkTextbox, items: List[tuple]):
        textbox.configure(state="normal")
        inner = textbox._textbox
        for text, tag in items:
            inner.insert("end", text, tag)
        # Giới hạn 500 dòng log để chạy lâu không nặng RAM
        line_count = int(inner.index("end-1c").split(".")[0])
        if line_count > 500:
            inner.delete("1.0", f"{line_count - 500}.0")
        inner.see("end")
        textbox.configure(state="disabled")

    def _load_file_to_textbox(self, textbox: ctk.CTkTextbox, callback=None):
        fp = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not fp:
            return
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        textbox.delete("1.0", "end")
        textbox.insert("1.0", content)
        if callback:
            callback()

    def _pick_file_to_entry(self, entry: ctk.CTkEntry, filetypes: list):
        fp = filedialog.askopenfilename(filetypes=filetypes)
        if fp:
            entry.delete(0, "end")
            entry.insert(0, fp)

    def _pick_dir_to_entry(self, entry: ctk.CTkEntry):
        dp = filedialog.askdirectory()
        if dp:
            entry.delete(0, "end")
            entry.insert(0, dp)


if __name__ == "__main__":
    app = RegPageControlPanel()
    app.mainloop()
