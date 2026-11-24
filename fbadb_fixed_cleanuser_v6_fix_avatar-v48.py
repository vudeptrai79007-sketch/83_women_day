# ==================== PHẦN 1/2 ====================
# --- SHIM CHO PYTHON 3.12+ (Khắc phục hoàn toàn lỗi thiếu distutils và .version) ---
import sys
import socket
import select
import base64
import io
import types
import re
import hmac

# Tự động cấu hình mã hóa UTF-8 & tắt QuickEdit Mode cho Windows Console (chống đứng CMD khi lỡ bấm chuột)
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    try:
        import ctypes
        _kernel32 = ctypes.windll.kernel32
        _h_stdin = _kernel32.GetStdHandle(-10)
        _mode = ctypes.c_uint32()
        if _kernel32.GetConsoleMode(_h_stdin, ctypes.byref(_mode)):
            # Bỏ cờ ENABLE_QUICK_EDIT_MODE (0x0040) và bật ENABLE_EXTENDED_FLAGS (0x0080)
            _new_mode = (_mode.value & ~0x0040) | 0x0080
            _kernel32.SetConsoleMode(_h_stdin, _new_mode)
    except Exception:
        pass

if 'distutils' not in sys.modules:
    distutils_mod = types.ModuleType('distutils')
    distutils_version_mod = types.ModuleType('distutils.version')

    class LooseVersion:
        def __init__(self, vstring=None):
            if vstring:
                self.parse(vstring)

        def parse(self, vstring):
            self.vstring = vstring
            component_re = re.compile(r'(\d+)')
            components = [int(x) if x.isdigit() else x for x in component_re.split(vstring) if x and x != '.']
            self.version = components

        def __lt__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version < other_v

        def __le__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version <= other_v

        def __eq__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version == other_v

        def __ne__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version != other_v

        def __gt__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version > other_v

        def __ge__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version >= other_v

        def __str__(self):
            return self.vstring

        def __repr__(self):
            return f"LooseVersion ('{self.vstring}')"

    distutils_version_mod.LooseVersion = LooseVersion
    distutils_mod.version = distutils_version_mod
    sys.modules['distutils'] = distutils_mod
    sys.modules['distutils.version'] = distutils_version_mod
# -----------------------------------------------------------------------------------

import uiautomator2 as u2
import time
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import subprocess
import urllib.parse
import string
import json
import html
import xml.etree.ElementTree as ET
import uuid
import struct
import threading
import imaplib
import email
import tempfile
from email.header import decode_header
import hashlib
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style

try:
    import pyotp
except ImportError:
    os.system("pip install pyotp")
    import pyotp

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

os.system('cls' if os.name == 'nt' else 'clear')
trang = Style.BRIGHT + Fore.WHITE
xanh = Style.BRIGHT + Fore.GREEN
do = Style.BRIGHT + Fore.RED
vang = Style.BRIGHT + Fore.YELLOW
xanh_duong = Style.BRIGHT + Fore.CYAN

# CỜ CHỐNG BẬT CỬA SỔ CMD NGẦM GÂY LAG TRÊN WINDOWS
ADB_CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

# BIẾN TOÀN CỤC & CÁC KHÓA (LOCK)
STOP_EVENT = threading.Event()
OTP_LOCK = threading.Lock()
DATA_LOCK = threading.Lock()
BROWSER_LOCK = threading.Lock()
INPUT_LOCK = threading.Lock()
TYPE_LOCK = threading.Lock()
SUBMIT_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()
DRIVER_LOCK = threading.Lock()
log_lock = threading.Lock()
email_lock = threading.Lock()

# CẤU HÌNH USER PHỤ SẠCH (MULTIPLE USERS - TỰ ĐỘNG 2 TRONG 1: ƯU TIÊN MÁY CHÍNH -> DỰ PHÒNG FACEBOOK.APK)
CLEAN_FB_USER_NAME = "CleanFB"
FB_PACKAGE_NAME = "com.facebook.katana"
# Giới hạn tối đa 3 máy đẩy file facebook.apk song song cùng lúc (khi máy chính chưa cài FB) để tránh nghẽn Hub USB
APK_INSTALL_LOCK = threading.Semaphore(3)

# --- CƠ CHẾ ĐÓNG BĂNG MÀN HÌNH CHỐNG TRÔI LỆNH TRONG ĐA LUỒNG ---
built_in_print = print
PAUSE_FOR_INPUT = threading.Event()
PAUSE_FOR_INPUT.set()


def thread_safe_print(*args, **kwargs):
    PAUSE_FOR_INPUT.wait()
    with PRINT_LOCK:
        built_in_print(*args, **kwargs)


print = thread_safe_print


# ========== BẢNG MÀU ==========
class Colors:
    PRIMARY = "\033[38;2;255;100;150m"
    SUCCESS = "\033[38;2;0;255;127m"
    ERROR = "\033[38;2;255;50;50m"
    WARNING = "\033[38;2;255;200;50m"
    INFO = "\033[38;2;100;255;200m"
    KEY = "\033[38;2;200;160;255m"
    VALUE = "\033[38;2;120;255;220m"
    LINE = "\033[38;2;190;235;210m"
    TITLE = "\033[38;2;255;215;0m"
    NUMBER = "\033[38;2;255;165;0m"
    EMAIL = "\033[38;2;100;200;255m"
    USERNAME = "\033[38;2;0;255;255m"
    PASSWORD = "\033[38;2;255;105;180m"
    RESET = "\033[0m"

    @staticmethod
    def color_text(text, color):
        return f"{color}{text}{Colors.RESET}"


# LẤY CHÍNH XÁC THƯ MỤC ĐANG CHỨA FILE TOOL (.PY HOẶC .EXE) ĐỂ LƯU FILE TXT, AVATAR VÀ FACEBOOK.APK
try:
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except Exception:
    BASE_DIR = os.getcwd()

CONFIG_FILE = os.path.join(BASE_DIR, 'config_reg_fb.json')
CONFIG_GMAIL_FILE = os.path.join(BASE_DIR, 'config_gmail.json')
GOM_HOTMAIL_FILE = os.path.join(BASE_DIR, 'Gom_Hotmail_Dongvan.txt')
FB_ACCOUNT_FILE = os.path.join(BASE_DIR, 'FB_NhaTrong.txt')
FB_DIE_FILE = os.path.join(BASE_DIR, 'FB_Die_Checkpoint.txt')
USED_EMAILS_FILE = os.path.join(BASE_DIR, 'Email_Da_Dung.txt')
TELE_FILE = os.path.join(BASE_DIR, 'Token-ID-Tele.txt')


def chuan_hoa_email_key(raw_item):
    """Trích xuất và chuẩn hóa địa chỉ email (chữ thường, bỏ BOM/khoảng trắng) từ 1 dòng data bất kỳ."""
    if not raw_item:
        return ""
    if isinstance(raw_item, (tuple, list)):
        raw_str = str(raw_item[0]) if raw_item else ""
    else:
        raw_str = str(raw_item)
    raw_str = raw_str.strip().lstrip('\ufeff')
    if not raw_str:
        return ""
    # Tách phần đầu trước dấu | (chuẩn Hotmail/FB_NhaTrong) hoặc : nếu có @ ở phần đầu
    if '|' in raw_str:
        cand = raw_str.split('|', 1)[0].strip()
    elif ':' in raw_str and '@' in raw_str.split(':', 1)[0]:
        cand = raw_str.split(':', 1)[0].strip()
    else:
        cand = raw_str.strip()
    return cand.lower() if '@' in cand else ""


def lay_tap_email_da_dung():
    """
    Đọc tập hợp toàn bộ email đã từng sử dụng (kể cả sau khi tắt tool bật lại) từ:
    1. Email_Da_Dung.txt (ghi nhận ngay khi lấy email ra chạy)
    2. FB_NhaTrong.txt (tài khoản tạo thành công)
    3. FB_Die_Checkpoint.txt (tài khoản bị Die/Checkpoint)
    """
    da_dung = set()
    with DATA_LOCK:
        for path in [USED_EMAILS_FILE, FB_ACCOUNT_FILE, FB_DIE_FILE]:
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            em = chuan_hoa_email_key(line)
                            if em:
                                da_dung.add(em)
                except Exception:
                    pass
    return da_dung


def danh_dau_email_da_dung(raw_item):
    """Ghi ngay email vào Email_Da_Dung.txt (flush tức thì) để tắt tool bật lại vẫn nhớ không dùng trùng."""
    em = chuan_hoa_email_key(raw_item)
    if not em:
        return
    with DATA_LOCK:
        try:
            da_co = False
            if os.path.isfile(USED_EMAILS_FILE):
                with open(USED_EMAILS_FILE, 'r', encoding='utf-8', errors='ignore') as f_r:
                    for line in f_r:
                        if chuan_hoa_email_key(line) == em:
                            da_co = True
                            break
            if not da_co:
                with open(USED_EMAILS_FILE, 'a', encoding='utf-8') as f_a:
                    f_a.write(em + '\n')
                    f_a.flush()
        except Exception:
            pass


class AccountDieError(Exception):
    """Ném ra ngay khi phát hiện tài khoản bị đình chỉ / checkpoint / vô hiệu hóa để dừng mọi bước tiếp theo."""
    pass
DEFAULT_AVATAR_DIR = os.path.join(BASE_DIR, 'avatars')
DEFAULT_FB_APK_FILE = os.path.join(BASE_DIR, 'facebook.apk')

# CẤU HÌNH THỜI GIAN & ANTI-CHECKPOINT TỐI ƯU NHẤT
DEFAULT_CONFIG = {
    'dung_user_phu_cleanfb': False,
    'fb_apk_path': DEFAULT_FB_APK_FILE,
    'doi_ip_may_bay': False,
    'tat_bat_4g_khi_xoa_du_lieu': True,
    'xoa_du_lieu_noi': True,
    'xoa_tu_dong_dien_va_khoa_truy_cap': True,
    'dung_proxy_adb': True,
    'thoi_gian_bat_may_bay': 5.0,
    'thoi_gian_cho_4g': 6.0,
    'doi_android_id': True,
    'delay_mo_facebook': 8.0,
    'delay_chon_khong_cho_phep': 0.8,
    'delay_click_khoang_trong': 0.6,
    'delay_chon_toi_co_tai_khoan_roi': 0.8,
    'delay_click_tao_tk_lan1': 1.2,
    'delay_click_tao_tk_lan2': 1.0,
    'delay_chon_khong_cho_phep_lan2': 0.6,
    'delay_nhap_ho': 0.6,
    'delay_nhap_ten': 0.6,
    'delay_click_tiep_lan1': 1.2,
    'delay_click_chon': 0.8,
    'delay_click_tiep_lan2': 1.0,
    'delay_click_tiep_lan3': 1.0,
    'delay_nhap_tuoi': 0.7,
    'delay_click_tiep_lan4': 1.0,
    'delay_click_ok': 0.8,
    'delay_chon_gioi_tinh': 0.8,
    'delay_click_tiep_lan5': 1.2,
    'delay_nhap_sdt': 0.8,
    'delay_click_tiep_sdt': 2.0,
    'delay_click_tiep_tuc_tao_tk': 1.0,
    'delay_kiem_tra_sdt': 0.8,
    'delay_nhap_mat_khau': 1.2,
    'delay_click_tiep_sau_mk': 1.8,
    'delay_click_luu': 1.0,
    'delay_cho_toi_dong_y': 12.0,
    'delay_kiem_tra_loi': 1.2,
    'delay_click_tiep_tuc': 1.0,
    'delay_click_khong_cho_phep': 0.6,
    'delay_click_khong_cho_phep_lan2': 0.5,
    'delay_buoc_dung_fb': 0.5,
    'delay_mo_lai_fb': 7.0,
    'delay_click_toi_khong_nhan_duoc_ma': 1.0,
    'delay_click_xac_nhan_email': 0.8,
    'delay_nhap_email': 1.0,
    'delay_click_tiep_sau_email': 2.5,
    'delay_get_code': 2.5,
    'delay_nhap_code': 1.2,
    'delay_click_tiep_cuoi': 6.0,
    'delay_up_avatar': 4.5,
    'delay_giua_cac_lan_chay': 4.0,
    'delay_thu_lai_khi_loi': 5.0,
    'so_lan_thu_get_code': 20,
    'so_lan_spam_gui_lai_otp_sms': 8,
    'thoi_gian_cho_moi_nhip_otp_sms': 22,
    'so_lan_spam_gui_lai_otp_email': 5,
    'thoi_gian_cho_moi_nhip_otp_email': 28,
    'so_lan_doi_sdt_khi_khong_ve_otp': 5,
    'mat_khau_fb': '@Letien09',
    'api_chuyen_link_sang_uid': '',
    'deeplink_cai_dat_trang_ca_nhan': ''
}

device_steps = {}
device_last_step = {}
multi_mode = False
stop_flag = STOP_EVENT


def nghi_ngau_nhien(thoi_gian_goc, dao_dong=0.2):
    """Tạo độ trễ ngẫu nhiên +-20% quanh mốc cấu hình để chống thuật toán phát hiện bot của Meta"""
    try:
        t = float(thoi_gian_goc)
        if t <= 0:
            return
        min_t = max(0.05, t * (1.0 - dao_dong))
        max_t = t * (1.0 + dao_dong)
        time.sleep(random.uniform(min_t, max_t))
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        time.sleep(1)


# ========== HÀM CHUYỂN ĐỔI KÝ TỰ 2FA SANG MÃ OTP 6 SỐ CHUẨN TOTP ==========
def lam_sach_key_2fa(raw_key):
    """Lọc bỏ khoảng trắng, dấu gạch ngang và chỉ giữ lại ký tự Base32 hợp lệ (A-Z, 2-7)"""
    if not raw_key:
        return ""
    return re.sub(r'[^A-Z2-7]', '', str(raw_key).upper())


def chuyen_doi_2fa_sang_otp(secret_key, doi_chu_ky_moi=True):
    """
    Chuyển đổi chuỗi Secret Key 2FA thành mã OTP 6 chữ số.
    Nếu thời gian hiệu lực của mã hiện tại còn dưới 5 giây, tự động chờ sang chu kỳ 30s mới.
    """
    clean_key = lam_sach_key_2fa(secret_key)
    if len(clean_key) < 8:
        return None

    if doi_chu_ky_moi:
        con_lai = 30 - (int(time.time()) % 30)
        if con_lai < 5:
            time.sleep(con_lai + 0.5)

    try:
        padding = (8 - (len(clean_key) % 8)) % 8
        padded_key = clean_key + ('=' * padding)
        key_bytes = base64.b32decode(padded_key, casefold=True)
        counter = int(time.time()) // 30
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key_bytes, msg, hashlib.sha1).digest()
        offset = digest[19] & 0x0F
        code_int = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
        return f"{code_int:06d}"
    except Exception:
        pass

    try:
        padding = (8 - (len(clean_key) % 8)) % 8
        return pyotp.TOTP(clean_key + ('=' * padding)).now()
    except Exception:
        return None


# ========== HÀM CƠ BẢN & HỆ THỐNG XỬ LÝ PROXY ĐA NĂNG ==========
def load_config():
    if os.path.exists(CONFIG_GMAIL_FILE):
        try:
            with open(CONFIG_GMAIL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(data):
    try:
        with open(CONFIG_GMAIL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def parse_proxy(proxy_str):
    if not proxy_str:
        return None
    # Chỉ lấy phần IP:Port:User:Pass trước dấu |
    p_str = str(proxy_str).strip().split("|", 1)[0].strip()
    if not p_str:
        return None
    for proto in ["http://", "https://", "socks5://", "socks4://"]:
        if p_str.lower().startswith(proto):
            p_str = p_str[len(proto):]
            break

    if "@" in p_str:
        try:
            auth_part, host_part = p_str.split("@", 1)
            u, pwd = auth_part.split(":", 1)
            ip, port = host_part.split(":", 1)
            return {"ip": ip.strip(), "port": port.strip(), "user": u.strip(), "pass": pwd.strip()}
        except Exception:
            pass

    parts = [x.strip() for x in p_str.split(":") if x.strip()]
    if len(parts) == 2:
        return {"ip": parts[0], "port": parts[1], "user": None, "pass": None}
    elif len(parts) == 4:
        if parts[1].isdigit() and not parts[2].isdigit():
            return {"ip": parts[0], "port": parts[1], "user": parts[2], "pass": parts[3]}
        elif parts[3].isdigit():
            return {"ip": parts[2], "port": parts[3], "user": parts[0], "pass": parts[1]}
        else:
            return {"ip": parts[0], "port": parts[1], "user": parts[2], "pass": parts[3]}
    return None


def format_proxy(proxy_str):
    parsed = parse_proxy(proxy_str)
    if not parsed:
        return None
    if parsed["user"] and parsed["pass"]:
        formatted = f"http://{parsed['user']}:{parsed['pass']}@{parsed['ip']}:{parsed['port']}"
    else:
        formatted = f"http://{parsed['ip']}:{parsed['port']}"
    return {"http": formatted, "https": formatted}


def tach_proxy_va_link(raw_line):
    """Tách chuỗi 'ip:port:user:pass|link_xoay' thành (proxy_str, rotate_url)."""
    if not raw_line:
        return None, None
    if "|" in raw_line:
        p_str, r_url = raw_line.split("|", 1)
        return p_str.strip(), r_url.strip()
    return raw_line.strip(), None


# ==================== HỆ THỐNG GẮN & ĐỔI PROXY XOAY QUA ADB ====================
ADB_PROXY_BRIDGES = {}
ADB_PROXY_LOCK = threading.Lock()


class LocalProxyBridge:
    """
    Mở proxy cục bộ trên PC (không cần user/pass) rồi tự chèn Proxy-Authorization
    chuyển tiếp sang proxy xoay có user:pass. Dùng kèm adb reverse để Android truy cập 127.0.0.1.
    """

    def __init__(self, local_port, upstream_ip, upstream_port, user, password):
        self.local_port = int(local_port)
        self.upstream_ip = upstream_ip
        self.upstream_port = int(upstream_port)
        self.user = user
        self.password = password
        self._running = False
        self._server = None
        self._thread = None

    def update_upstream(self, upstream_ip, upstream_port, user, password):
        self.upstream_ip = upstream_ip
        self.upstream_port = int(upstream_port)
        self.user = user
        self.password = password

    def start(self):
        if self._running:
            return
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(('127.0.0.1', self.local_port))
        self._server.listen(64)
        self._server.settimeout(1.0)
        self._running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass
            self._server = None

    def _accept_loop(self):
        while self._running:
            try:
                client_sock, _ = self._server.accept()
                threading.Thread(
                    target=self._handle_client, args=(client_sock,), daemon=True
                ).start()
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception:
                continue

    def _inject_auth_header(self, head_bytes, user, password):
        lines = head_bytes.split(b"\r\n")
        if not lines:
            return head_bytes
        req_line = lines[0]
        is_connect = req_line.upper().startswith(b"CONNECT ")
        new_lines = [req_line]
        for h_line in lines[1:]:
            lower_h = h_line.lower()
            if lower_h.startswith(b"proxy-authorization:"):
                continue
            if not is_connect and lower_h.startswith(b"proxy-connection:"):
                continue
            new_lines.append(h_line)
        if user and password:
            token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
            new_lines.append(f"Proxy-Authorization: Basic {token}".encode("ascii"))
        if not is_connect:
            new_lines.append(b"Proxy-Connection: close")
        return b"\r\n".join(new_lines)

    def _handle_client(self, client_sock):
        upstream_sock = None
        try:
            client_sock.settimeout(15.0)
            buffer = b""
            while b"\r\n\r\n" not in buffer and len(buffer) < 65536:
                chunk = client_sock.recv(4096)
                if not chunk:
                    return
                buffer += chunk

            if not buffer:
                return

            if b"\r\n\r\n" in buffer:
                head_bytes, rest = buffer.split(b"\r\n\r\n", 1)
                up_ip = self.upstream_ip
                up_port = self.upstream_port
                up_user = self.user
                up_pass = self.password
                out_head = self._inject_auth_header(head_bytes, up_user, up_pass)
                out_payload = out_head + b"\r\n\r\n" + rest
            else:
                up_ip = self.upstream_ip
                up_port = self.upstream_port
                out_payload = buffer

            upstream_sock = socket.create_connection((up_ip, up_port), timeout=15.0)
            upstream_sock.settimeout(30.0)
            client_sock.settimeout(30.0)
            upstream_sock.sendall(out_payload)

            sockets = [client_sock, upstream_sock]
            while self._running:
                readable, _, exceptional = select.select(sockets, [], sockets, 30.0)
                if exceptional or not readable:
                    break
                for s in readable:
                    data = s.recv(16384)
                    if not data:
                        return
                    target = upstream_sock if s is client_sock else client_sock
                    target.sendall(data)
        except Exception:
            pass
        finally:
            if upstream_sock:
                try:
                    upstream_sock.close()
                except Exception:
                    pass
            try:
                client_sock.close()
            except Exception:
                pass


def goi_link_xoay_proxy(rotate_url, device_name="Device"):
    """Gọi link xoay IP của nhà cung cấp và chờ cổng proxy cập nhật IP mới."""
    if not rotate_url:
        return False
    try:
        r = requests.get(rotate_url, timeout=15)
        phan_hoi = r.text.strip().replace("\n", " ")[:80]
        update_step(device_name, f"🔄 Đã gọi Link xoay ({r.status_code}): {phan_hoi}")
        time.sleep(3.5)
        return True
    except Exception as e:
        update_step(device_name, f"⚠️ Lỗi gọi Link xoay: {str(e)[:40]}")
        return False


def kiem_tra_ip_qua_proxy_pc(proxy_str):
    """Kiểm tra nhanh IP thực tế đi qua cổng proxy từ PC."""
    proxies = format_proxy(proxy_str)
    if not proxies:
        return None
    headers = {"Connection": "close", "User-Agent": "curl/8.0"}
    try:
        r = requests.get("https://api.ipify.org", proxies=proxies, headers=headers, timeout=10)
        ip = r.text.strip()
        if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', ip):
            return ip
    except Exception:
        pass
    return None


def gan_proxy_adb(serial, proxy_entry, device_idx=0, device_name="Device", xoay_ip=False):
    """
    Gắn cầu nối Proxy lên điện thoại Android đang dùng Wi-Fi.
    Hỗ trợ định dạng: ip:port:user:pass hoặc ip:port:user:pass|link_xoay.
    """
    if not proxy_entry:
        return None
    chay_lenh_adb('shell "svc wifi enable"', serial, timeout=8)
    raw_proxy, rotate_url = tach_proxy_va_link(str(proxy_entry))
    parsed = parse_proxy(raw_proxy)
    if not parsed:
        update_step(device_name, f"⚠️ Sai định dạng Proxy: {str(raw_proxy)[:30]}")
        return None

    if xoay_ip and rotate_url and rotate_url.lower().startswith(("http://", "https://")):
        goi_link_xoay_proxy(rotate_url, device_name)

    ip_thuc = None
    for _ in range(3):
        ip_thuc = kiem_tra_ip_qua_proxy_pc(raw_proxy)
        if ip_thuc:
            break
        time.sleep(1.5)

    local_port = 18000 + int(device_idx)
    bridge_key = serial if serial else f"dev_{device_idx}"

    try:
        with ADB_PROXY_LOCK:
            bridge = ADB_PROXY_BRIDGES.get(bridge_key)
            if bridge and bridge.local_port == local_port:
                bridge.update_upstream(parsed["ip"], parsed["port"], parsed["user"], parsed["pass"])
                bridge.start()
            else:
                if bridge:
                    bridge.stop()
                bridge = LocalProxyBridge(
                    local_port=local_port,
                    upstream_ip=parsed["ip"],
                    upstream_port=parsed["port"],
                    user=parsed["user"],
                    password=parsed["pass"],
                )
                bridge.start()
                ADB_PROXY_BRIDGES[bridge_key] = bridge

        chay_lenh_adb(f'reverse tcp:{local_port} tcp:{local_port}', serial, timeout=8)
        chay_lenh_adb(f'shell "settings put global http_proxy 127.0.0.1:{local_port}"', serial, timeout=8)
        update_step(device_name, f"🌐 Proxy ADB (:{local_port}) sẵn sàng | IP: {ip_thuc or parsed['ip']}")
        return ip_thuc or parsed["ip"]
    except Exception as e:
        update_step(device_name, f"⚠️ Lỗi gắn Proxy ADB (:{local_port}): {str(e)[:40]}")
        return None


def go_proxy_adb(serial, device_idx=0):
    """Gỡ Proxy toàn cục trên thiết bị Android, xóa adb reverse và dừng LocalProxyBridge."""
    local_port = 18000 + int(device_idx)
    bridge_key = serial if serial else f"dev_{device_idx}"
    try:
        chay_lenh_adb('shell "settings put global http_proxy :0"', serial, timeout=8)
        chay_lenh_adb(f'reverse --remove tcp:{local_port}', serial, timeout=5)
    except Exception:
        pass
    with ADB_PROXY_LOCK:
        bridge = ADB_PROXY_BRIDGES.pop(bridge_key, None)
        if bridge:
            bridge.stop()


class DynamicBatchRotator:
    """
    Điều phối Chế độ 2 (Proxy chung xoay đồng bộ theo đợt):
    - Điểm danh động các máy đang sống (tránh treo dàn nếu có máy ngắt/hết data).
    - Check IP cũ qua cổng Proxy -> Chờ cooldown -> Gọi API xoay -> Xác minh IP mới đã lên.
    - Đánh thức đồng loạt toàn bộ thiết bị sang đợt tiếp theo.
    """

    IP_CHECK_URLS = [
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://ifconfig.me/ip",
    ]

    def __init__(
        self,
        proxy_str,
        rotate_url,
        stop_event,
        min_interval=65,
        stabilize_delay=4,
        verify_timeout=35,
        max_rotate_retries=2,
    ):
        self.proxy_str = proxy_str.strip() if proxy_str else ""
        self.proxies = format_proxy(self.proxy_str) if self.proxy_str else None
        self.rotate_url = rotate_url.strip() if rotate_url else ""
        self.stop_event = stop_event
        self.min_interval = min_interval
        self.stabilize_delay = stabilize_delay
        self.verify_timeout = verify_timeout
        self.max_rotate_retries = max_rotate_retries
        self.last_rotate_time = 0.0
        self.current_ip = None
        self.cond = threading.Condition()
        self.active_devices = set()
        self.finished_in_round = set()
        self.round_id = 0
        self.is_rotating = False

    def _sleep_interruptible(self, seconds):
        """Ngủ theo nhịp nhỏ 0.5s để dừng tức thì khi nhấn Ctrl+C."""
        end_time = time.time() + max(0.0, float(seconds))
        while time.time() < end_time and not self.stop_event.is_set():
            time.sleep(min(0.5, end_time - time.time()))

    def _get_current_ip(self, timeout=8):
        """Kiểm tra IP đầu ra đi xuyên qua cổng Proxy (ép mở kết nối mới bằng Connection: close)."""
        if not self.proxies:
            return None
        headers = {"Connection": "close", "User-Agent": "curl/8.0"}
        for url in self.IP_CHECK_URLS:
            if self.stop_event.is_set():
                return None
            try:
                r = requests.get(url, proxies=self.proxies, headers=headers, timeout=timeout)
                ip = r.text.strip()
                if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', ip):
                    return ip
            except Exception:
                continue
        return None

    def register(self, device_name):
        with self.cond:
            self.active_devices.add(device_name)

    def unregister(self, device_name):
        with self.cond:
            self.active_devices.discard(device_name)
            self.finished_in_round.discard(device_name)
            self.cond.notify_all()

    def notify_stop(self):
        with self.cond:
            self.cond.notify_all()

    def _call_rotate_and_verify(self, leader_device):
        old_ip = self._get_current_ip() or self.current_ip
        if old_ip:
            self.current_ip = old_ip

        if self.last_rotate_time > 0:
            elapsed = time.time() - self.last_rotate_time
            if elapsed < self.min_interval:
                wait_sec = self.min_interval - elapsed
                update_step(leader_device, f"⏳ Chờ cooldown xoay IP ({int(wait_sec)}s)...")
                self._sleep_interruptible(wait_sec)

        if self.stop_event.is_set():
            return False

        if not self.rotate_url:
            return True

        for attempt in range(1, self.max_rotate_retries + 1):
            if self.stop_event.is_set():
                return False

            update_step(
                leader_device,
                f"🔄 Gọi API xoay IP chung (lần {attempt}/{self.max_rotate_retries}) | IP cũ: {old_ip or 'N/A'}..."
            )
            try:
                r = requests.get(self.rotate_url, timeout=15)
                phan_hoi = r.text.strip().replace("\n", " ")[:70]
                update_step(leader_device, f"🔄 API xoay ({r.status_code}): {phan_hoi}")
            except Exception as e:
                update_step(leader_device, f"⚠️ Lỗi gọi API xoay IP chung: {str(e)[:40]}")

            self.last_rotate_time = time.time()
            self._sleep_interruptible(self.stabilize_delay)

            verify_deadline = time.time() + self.verify_timeout
            while time.time() < verify_deadline and not self.stop_event.is_set():
                new_ip = self._get_current_ip(timeout=8)
                if new_ip and (not old_ip or new_ip != old_ip):
                    self.current_ip = new_ip
                    update_step(leader_device, f"🌐 ĐỔI IP THÀNH CÔNG: {old_ip or 'N/A'} -> {new_ip}")
                    return True
                self._sleep_interruptible(2.0)

            if attempt < self.max_rotate_retries and not self.stop_event.is_set():
                update_step(leader_device, f"⚠️ IP chưa đổi ({old_ip or 'N/A'}), thử gọi xoay lại...")
                self._sleep_interruptible(3.0)

        update_step(leader_device, f"⚠️ Hết thời gian xác minh IP mới (hiện tại: {self.current_ip or old_ip or 'N/A'}), tiếp tục đợt mới...")
        return False

    def wait_for_next_round(self, device_name):
        if self.stop_event.is_set():
            return
        should_rotate = False
        with self.cond:
            if device_name not in self.active_devices:
                self.active_devices.add(device_name)
            my_round = self.round_id
            self.finished_in_round.add(device_name)
            done_cnt = len(self.finished_in_round & self.active_devices)
            total_cnt = len(self.active_devices)
            update_step(device_name, f"⏳ Xong lượt ({done_cnt}/{total_cnt} máy), chờ đồng bộ xoay IP...")

            while not self.stop_event.is_set() and self.round_id == my_round:
                if self.active_devices and self.active_devices.issubset(self.finished_in_round) and not self.is_rotating:
                    self.is_rotating = True
                    should_rotate = True
                    break
                self.cond.wait(timeout=0.5)

        if should_rotate:
            try:
                if not self.stop_event.is_set():
                    self._call_rotate_and_verify(device_name)
            finally:
                with self.cond:
                    self.round_id += 1
                    self.finished_in_round.clear()
                    self.is_rotating = False
                    self.cond.notify_all()


# ==================== CÁC CLASS XỬ LÝ EMAIL & SĐT (6 CHẾ ĐỘ) ====================
class MailService:
    def __init__(self, proxy=None):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.domain = None
        self.email_address = None
        self.seen_msg_ids = set()
        self.proxy = proxy

    def get_domain(self):
        try:
            r = requests.get(f"{self.base_url}/domains", timeout=10, proxies=self.proxy)
            if r.status_code == 200:
                self.domain = r.json()['hydra:member'][0]['domain']
                return self.domain
        except Exception:
            return None

    def create_account(self, address=None):
        if not self.domain and not self.get_domain():
            return None
        name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        time.sleep(random.uniform(0.5, 2.0))
        try:
            r = requests.post(
                f"{self.base_url}/accounts",
                json={"address": f"{name}@{self.domain}", "password": "TempPass123!"},
                timeout=10,
                proxies=self.proxy
            )
            if r.status_code == 201:
                self.email_address = r.json()['address']
                return self.email_address
        except Exception:
            return None

    def authenticate(self, email_addr=None, password="TempPass123!"):
        if email_addr:
            self.email_address = email_addr
        time.sleep(random.uniform(0.5, 2.0))
        try:
            r = requests.post(
                f"{self.base_url}/token",
                json={"address": self.email_address, "password": password},
                timeout=10,
                proxies=self.proxy
            )
            if r.status_code == 200:
                self.token = r.json()['token']
                return True
        except Exception:
            return False

    def get_otp_code(self, timeout=120, force_8_digits=False, expected_digits=None):
        if not self.token:
            return None
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        start_time = time.time()
        time.sleep(random.uniform(1.0, 4.0))
        if force_8_digits and not expected_digits:
            expected_digits = 8

        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
            try:
                r = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10, proxies=self.proxy)
                if r.status_code == 200:
                    for msg in r.json().get('hydra:member', []):
                        msg_id = msg.get('id')
                        if not msg_id or msg_id in self.seen_msg_ids:
                            continue

                        subject = str(msg.get('subject', '')).lower()
                        frm = str(msg.get('from', {}).get('address', '')).lower()
                        if any(k in subject or k in frm for k in ['facebook', 'fb', 'instagram', 'meta']):
                            detail = requests.get(f"{self.base_url}/messages/{msg_id}", headers=headers, timeout=10, proxies=self.proxy).json()
                            raw_text = detail.get('text', '') or re.sub('<[^<]+?>', ' ', str(detail.get('html', '')))
                            safe_body = raw_text.lower().replace(str(self.email_address).lower(), "")
                            clean_body = re.sub(r'\s+', '', safe_body)

                            code = None
                            if expected_digits in (6, 8):
                                pat = rf'(?<!\d)(\d{{{expected_digits}}})(?!\d)'
                                m_sub = re.search(pat, subject)
                                m_body = re.search(pat, safe_body) or re.search(pat, clean_body)
                                if m_sub:
                                    code = m_sub.group(1)
                                elif m_body:
                                    code = m_body.group(1)
                            else:
                                match_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', subject)
                                if match_sub:
                                    code = match_sub.group(1)
                                else:
                                    cands = re.findall(r'(?<!\d)(\d{5,8})(?!\d)', safe_body) or re.findall(r'(?<!\d)(\d{5,8})(?!\d)', clean_body)
                                    cands_filtered = [c for c in cands if c != '94025']
                                    if cands_filtered:
                                        code = cands_filtered[0]
                                    elif cands:
                                        code = cands[0]

                            if code:
                                self.seen_msg_ids.add(msg_id)
                                return code
            except Exception:
                pass
            time.sleep(random.uniform(5.0, 8.0))
        return None


class GmailIMAPService:
    def __init__(self, base_email, app_password):
        self.base_email = base_email
        self.app_password = app_password.replace(" ", "")
        self.mail = None
        self.seen_uids = set()

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.mail.login(self.base_email, self.app_password)
            return True
        except Exception as e:
            print(f"{Colors.color_text(f'Lỗi đăng nhập IMAP cho {self.base_email}: {e}', Colors.ERROR)}")
            return False

    def close(self):
        if self.mail:
            try:
                self.mail.logout()
            except Exception:
                pass
            self.mail = None

    def get_latest_uid(self):
        if not self.mail and not self.connect():
            return 0
        try:
            self.mail.select("INBOX", readonly=True)
            status, data = self.mail.uid("search", None, 'ALL')
            if status == "OK" and data[0]:
                uids = data[0].split()
                if uids:
                    return int(uids[-1])
        except Exception:
            pass
        return 0

    def get_text(self, msg):
        plain, html_parts = [], []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    continue
                ctype = part.get_content_type()
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if ctype == "text/plain":
                    plain.append(text)
                elif ctype == "text/html":
                    html_parts.append(text)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/plain":
                    plain.append(text)
                else:
                    html_parts.append(text)
        if plain:
            return "\n".join(plain).strip()
        if html_parts:
            return re.sub(r'<[^>]+>', ' ', "\n".join(html_parts)).strip()
        return ""

    def decode_msg_header(self, raw_header):
        if not raw_header:
            return ""
        try:
            decoded = decode_header(raw_header)
            result = ""
            for text, charset in decoded:
                if isinstance(text, bytes):
                    try:
                        result += text.decode(charset or 'utf-8', errors='replace')
                    except Exception:
                        result += text.decode('utf-8', errors='replace')
                else:
                    result += str(text)
            return result
        except Exception:
            return str(raw_header)

    def get_otp_code(self, target_email, since_uid=0, timeout=120, force_8_digits=False, expected_digits=None):
        if not self.mail:
            if not self.connect():
                return None
        start_time = time.time()
        time.sleep(random.uniform(1.0, 4.0))
        if force_8_digits and not expected_digits:
            expected_digits = 8

        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
            try:
                self.mail.select("INBOX", readonly=True)
                status, data = self.mail.uid("search", None, 'ALL')
                if status == "OK" and data[0]:
                    uids = data[0].split()
                    for uid_bytes in reversed(uids[-10:]):
                        try:
                            uid_int = int(uid_bytes)
                        except ValueError:
                            continue

                        if uid_int <= since_uid or uid_bytes in self.seen_uids:
                            continue

                        status, fetch_data = self.mail.uid("fetch", uid_bytes, "(RFC822)")
                        if status == "OK" and fetch_data:
                            raw = None
                            for item in fetch_data:
                                if isinstance(item, tuple):
                                    raw = item[1]
                                    break
                            if raw:
                                msg = email.message_from_bytes(raw)
                                to_addr = self.decode_msg_header(msg.get("To", "")).lower()
                                subject = self.decode_msg_header(msg.get("Subject", "")).lower()
                                from_addr = self.decode_msg_header(msg.get("From", "")).lower()

                                if target_email.lower() not in to_addr:
                                    continue

                                is_target_service = any(k in subject or k in from_addr for k in ["facebook", "fb", "instagram", "meta"])
                                is_security_mail = any(kw in subject for kw in [
                                    "security", "bảo mật", "verify", "xác minh", "xác nhận", "code", "mã",
                                    "authenticate", "profile", "fb-", "confirm", "meta", "account", "tài khoản",
                                    "login", "đăng nhập", "two-factor", "2 yếu tố"
                                ])

                                if is_target_service and (is_security_mail or not force_8_digits):
                                    body = self.get_text(msg)
                                    raw_safe = body.lower().replace(target_email.lower(), "")
                                    clean_safe = re.sub(r'\s+', '', raw_safe)
                                    code = None

                                    if expected_digits in (6, 8):
                                        pat = rf'(?<!\d)(\d{{{expected_digits}}})(?!\d)'
                                        m_sub = re.search(pat, subject)
                                        m_body = re.search(pat, raw_safe) or re.search(pat, clean_safe)
                                        if m_sub:
                                            code = m_sub.group(1)
                                        elif m_body:
                                            code = m_body.group(1)
                                    else:
                                        match_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', subject)
                                        if match_sub:
                                            code = match_sub.group(1)
                                        else:
                                            cands = re.findall(r'(?<!\d)(\d{5,8})(?!\d)', raw_safe) or re.findall(r'(?<!\d)(\d{5,8})(?!\d)', clean_safe)
                                            cands_filtered = [c for c in cands if c != '94025']
                                            if cands_filtered:
                                                code = cands_filtered[0]
                                            elif cands:
                                                code = cands[0]

                                    if code:
                                        self.seen_uids.add(uid_bytes)
                                        return code
            except Exception:
                pass
            time.sleep(random.uniform(5.0, 8.0))
        return None


class HotmailAPIService:
    def __init__(self, data_line, api_mode, proxy=None):
        self.url = "https://smail1s.com/get_messages"
        self.data_line = data_line.strip().lstrip('\ufeff')
        self.api_mode = api_mode.strip()
        self.email = (self.data_line.split('|', 1)[0] if '|' in self.data_line else self.data_line).strip()
        self.seen_msg_ids = set()
        self.used_codes = set()
        self.proxy = proxy
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        if self.proxy:
            self.session.proxies.update(self.proxy)

        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _tao_msg_id_chuan(self, msg):
        """Tạo ID thư duy nhất chống lỗi id=None thành chuỗi 'None' làm bỏ sót toàn bộ thư OTP mới!"""
        raw_id = None
        for k in ("id", "uid", "message_id", "msg_id"):
            val = msg.get(k)
            if val is not None and str(val).strip() not in ("", "None", "null"):
                raw_id = str(val).strip()
                break
        if raw_id:
            return raw_id
        sig_src = f"{msg.get('date', msg.get('created_at', msg.get('timestamp', '')))}|{msg.get('from', '')}|{msg.get('subject', '')}|{str(msg.get('message', ''))[:500]}"
        return hashlib.md5(sig_src.encode('utf-8', errors='ignore')).hexdigest()

    def _lay_moc_thoi_gian_thu(self, msg):
        """Lấy timestamp sắp xếp thư mới nhất lên đầu."""
        for k in ("timestamp", "date", "created_at", "receivedDateTime", "time"):
            v = msg.get(k)
            if v is None or v == "":
                continue
            if isinstance(v, (int, float)):
                return float(v)
            s = str(v).strip()
            if s.isdigit():
                return float(s)
            try:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(s).timestamp()
            except Exception:
                pass
            try:
                return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()
            except Exception:
                pass
        return 0.0

    def _trich_xuat_code_tu_thu(self, subject, raw_msg, expected_digits=None):
        """Loại bỏ thẻ style/script/URL/entity HTML để tách chính xác mã OTP mới nhất."""
        no_style = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', str(raw_msg or ''), flags=re.IGNORECASE | re.DOTALL)
        no_tags = re.sub(r'<[^>]+>', ' ', no_style)
        plain_text = html.unescape(no_tags)
        plain_low = plain_text.lower().replace(self.email.lower(), ' ')
        # Bỏ URL tránh bắt nhầm ID số dài trong link facebook.com
        plain_low = re.sub(r'https?://\S+', ' ', plain_low)
        sub_low = html.unescape(str(subject or '')).lower()
        clean_text = re.sub(r'\s+', '', plain_low)

        if expected_digits in (6, 8):
            pat = rf'(?<!\d)(\d{{{expected_digits}}})(?!\d)'
            m_sub = re.search(pat, sub_low)
            if m_sub:
                return m_sub.group(1)
            # Ưu tiên mã nằm ngay sau từ khóa 'mã' / 'code' / 'fb-'
            m_kw = re.search(rf'(?:fb-|code|mã|otp)[^\d]{{0,25}}(\d{{{expected_digits}}})(?!\d)', plain_low)
            if m_kw:
                return m_kw.group(1)
            m_body = re.search(pat, plain_low) or re.search(pat, clean_text)
            if m_body:
                return m_body.group(1)
            return None

        # Không ép cố định số chữ số (5-8 số)
        m_fb = re.search(r'fb[-\s]*(\d{5,8})\b', sub_low) or re.search(r'fb[-\s]*(\d{5,8})\b', plain_low)
        if m_fb:
            return m_fb.group(1)
        m_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', sub_low)
        if m_sub:
            return m_sub.group(1)
        m_kw = re.search(r'(?:code|mã|otp|xác nhận|confirmation)[^\d]{0,25}(\d{5,8})(?!\d)', plain_low)
        if m_kw and m_kw.group(1) != '94025':
            return m_kw.group(1)
        cands = re.findall(r'(?<!\d)(\d{5,8})(?!\d)', plain_low) or re.findall(r'(?<!\d)(\d{5,8})(?!\d)', clean_text)
        cands_filtered = [c for c in cands if c not in ('94025', '1601')]
        if cands_filtered:
            return cands_filtered[0]
        return cands[0] if cands else None

    def init_baseline(self):
        payload = {"mode": self.api_mode, "data": self.data_line}
        time.sleep(random.uniform(0.8, 1.8))

        for _ in range(3):
            try:
                response = self.session.post(self.url, json=payload, timeout=20)
                if response.status_code == 200:
                    data_array = response.json().get("data", [])
                    if data_array and len(data_array) > 0:
                        messages = data_array[0].get("messages", [])
                        for msg in messages:
                            self.seen_msg_ids.add(self._tao_msg_id_chuan(msg))
                    break
            except Exception:
                time.sleep(1.5)

    def get_otp_code(self, timeout=180, force_8_digits=False, expected_digits=None):
        start_time = time.time()
        if force_8_digits and not expected_digits:
            expected_digits = 8
        loai_ma = f"MÃ MỚI NHẤT {expected_digits} SỐ" if expected_digits in (6, 8) else "MÃ MỚI NHẤT"
        if not multi_mode:
            print(f"{Colors.color_text(f'[API Smail1s] Đang check hộp thư {self.email} ({loai_ma})...', Colors.INFO)}")

        payload = {"mode": self.api_mode, "data": self.data_line}
        time.sleep(random.uniform(1.0, 2.5))
        last_logged = ""

        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
            try:
                response = self.session.post(self.url, json=payload, timeout=20)

                if response.status_code == 200:
                    res_json = response.json()
                    data_array = res_json.get("data", [])

                    if data_array and len(data_array) > 0:
                        account_data = data_array[0]
                        err = account_data.get("error")

                        if err:
                            msg_err = f"Lỗi hộp thư: {err}"
                            if msg_err != last_logged and not multi_mode:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_err}', Colors.ERROR)}")
                                last_logged = msg_err
                        else:
                            messages = list(account_data.get("messages", []))
                            # Luôn ưu tiên kiểm tra THƯ MỚI NHẤT TRƯỚC (dựa trên timestamp nếu có)
                            ts_list = [self._lay_moc_thoi_gian_thu(m) for m in messages]
                            if any(t > 0 for t in ts_list):
                                messages = [m for _, m in sorted(enumerate(messages), key=lambda pair: (ts_list[pair[0]], -pair[0]), reverse=True)]

                            for msg in messages:
                                msg_id = self._tao_msg_id_chuan(msg)
                                if msg_id in self.seen_msg_ids:
                                    continue

                                subject = str(msg.get("subject", "")).lower()
                                from_sender = str(msg.get("from", "")).lower()
                                raw_msg = str(msg.get("message", ""))

                                is_target = any(k in subject or k in from_sender or k in raw_msg.lower()[:400] for k in ["facebook", "fb", "instagram", "meta"])
                                if not is_target:
                                    continue

                                code = self._trich_xuat_code_tu_thu(subject, raw_msg, expected_digits=expected_digits)
                                if code and code in self.used_codes:
                                    # Đánh dấu thư cũ trùng mã đã dùng để không kẹt lại mã cũ
                                    self.seen_msg_ids.add(msg_id)
                                    continue

                                if code:
                                    self.seen_msg_ids.add(msg_id)
                                    self.used_codes.add(code)
                                    if not multi_mode:
                                        print(f"{Colors.color_text(f'[API Smail1s] ĐÃ BẮT ĐƯỢC MÃ MỚI NHẤT: {code}', Colors.SUCCESS)}")
                                    return code
            except Exception:
                try:
                    self._init_session()
                except Exception:
                    pass

            time.sleep(random.uniform(4.0, 6.5))
        return None


class AutoSMSService:
    def __init__(self, api_key, country="vn", proxy=None, service="facebook"):
        self.api_key = api_key
        self.country = country
        self.service = service
        self.base_url = "https://autosms.site/api"
        self.order_id = None
        self.phone = None
        self.proxy = proxy
        self.last_order_ended = False
        self.last_status = None

    def _mask_key(self, text):
        s = str(text or "")
        if self.api_key:
            s = s.replace(str(self.api_key), "***")
        return s

    def _emit_log(self, msg, log_fn=None):
        safe_msg = self._mask_key(msg)
        if log_fn is not None:
            try:
                log_fn(safe_msg)
                return
            except Exception:
                pass
        if not multi_mode:
            print(safe_msg)

    def _trich_xuat_ma_tu_chuoi(self, raw_text):
        if raw_text is None:
            return None
        s = str(raw_text).strip()
        if not s:
            return None
        # Bỏ số điện thoại đang thuê khỏi chuỗi để tránh bắt nhầm số ĐT thành mã OTP
        phone_digits = re.sub(r'\D', '', str(self.phone or ''))
        s_clean = s
        if phone_digits:
            s_clean = s_clean.replace(str(self.phone), ' ').replace(phone_digits, ' ')
            if len(phone_digits) > 9:
                s_clean = s_clean.replace(phone_digits[-9:], ' ')
        # Ưu tiên mẫu FB-12345 / mã 5-8 chữ số
        m_fb = re.search(r'fb[-\s]*(\d{5,8})\b', s_clean, re.IGNORECASE)
        if m_fb:
            return m_fb.group(1)
        m_digits = re.search(r'(?<!\d)(\d{5,8})(?!\d)', s_clean)
        if m_digits:
            return m_digits.group(1)
        return None

    def _trich_xuat_ma_tu_json(self, js):
        """
        Đọc mã OTP linh hoạt từ nhiều cấu trúc JSON của AutoSMS:
        - data.code / data.otp / data.otp_code / data.sms_code / data.verification_code
        - data.sms / data.message / data.messages / data.content / data.text / data.body (str, dict hoặc list)
        - Top-level otp / otp_code / sms_code / sms / message (không nhận nhầm HTTP status code 3 chữ số).
        Trả về (otp_code, ten_truong) hoặc (None, None).
        """
        if not isinstance(js, dict):
            return None, None

        data_obj = js.get("data")
        # 1. Kiểm tra trực tiếp trong data (dict)
        if isinstance(data_obj, dict):
            for k in ("code", "otp", "otp_code", "sms_code", "verification_code"):
                val = data_obj.get(k)
                if val is not None and str(val).strip():
                    val_s = str(val).strip()
                    if re.fullmatch(r'\d{4,8}', val_s):
                        return val_s, f"data.{k}"
                    parsed = self._trich_xuat_ma_tu_chuoi(val_s)
                    if parsed:
                        return parsed, f"data.{k}"

            for k in ("sms", "message", "messages", "content", "text", "body", "full_sms"):
                val = data_obj.get(k)
                if isinstance(val, str):
                    parsed = self._trich_xuat_ma_tu_chuoi(val)
                    if parsed:
                        return parsed, f"data.{k}"
                elif isinstance(val, dict):
                    for sub_k in ("code", "otp", "text", "message", "content", "body", "sms"):
                        parsed = self._trich_xuat_ma_tu_chuoi(val.get(sub_k))
                        if parsed:
                            return parsed, f"data.{k}.{sub_k}"
                elif isinstance(val, list):
                    for idx, item in enumerate(val):
                        if isinstance(item, str):
                            parsed = self._trich_xuat_ma_tu_chuoi(item)
                            if parsed:
                                return parsed, f"data.{k}[{idx}]"
                        elif isinstance(item, dict):
                            for sub_k in ("code", "otp", "text", "message", "content", "body", "sms"):
                                parsed = self._trich_xuat_ma_tu_chuoi(item.get(sub_k))
                                if parsed:
                                    return parsed, f"data.{k}[{idx}].{sub_k}"

        # 2. Nếu data là danh sách (list)
        elif isinstance(data_obj, list):
            for idx, item in enumerate(data_obj):
                if isinstance(item, dict):
                    for k in ("code", "otp", "otp_code", "sms_code", "sms", "message", "content", "text"):
                        parsed = self._trich_xuat_ma_tu_chuoi(item.get(k))
                        if parsed:
                            return parsed, f"data[{idx}].{k}"
                elif isinstance(item, str):
                    parsed = self._trich_xuat_ma_tu_chuoi(item)
                    if parsed:
                        return parsed, f"data[{idx}]"

        # 3. Kiểm tra top-level (tránh nhận nhầm 'code': 200 là HTTP status)
        for k in ("otp", "otp_code", "sms_code", "sms", "message", "content", "text"):
            val = js.get(k)
            if isinstance(val, (str, int)):
                parsed = self._trich_xuat_ma_tu_chuoi(val)
                if parsed:
                    return parsed, k

        return None, None

    def buy_number(self, log_fn=None):
        url = f"{self.base_url}/buy-number/{self.country}/{self.service}?key={self.api_key}"
        try:
            r = requests.get(url, timeout=10, proxies=self.proxy)
            try:
                js = r.json()
            except Exception:
                self._emit_log(f"⚠️ [AutoSMS buy-number | HTTP {r.status_code}] Không phải JSON: {r.text[:250]}", log_fn)
                return None

            raw_json = json.dumps(js, ensure_ascii=False)[:350]
            if js.get("success") and isinstance(js.get("data"), dict):
                self.phone = js["data"].get("phone")
                self.order_id = js["data"].get("order_id")
                self.last_order_ended = False
                self.last_status = None
                self._emit_log(f"📡 [AutoSMS buy-number | HTTP {r.status_code}] OK -> order_id={self.order_id} | phone={self.phone} | JSON: {raw_json}", log_fn)
                return self.phone
            else:
                self._emit_log(f"⚠️ [AutoSMS buy-number | HTTP {r.status_code}] Thuê số thất bại | JSON: {raw_json}", log_fn)
        except Exception as e:
            self._emit_log(f"⚠️ [AutoSMS buy-number] Lỗi gọi API: {type(e).__name__}: {str(e)[:180]}", log_fn)
        return None

    def get_otp_code(self, timeout=120, log_fn=None, poll_interval=2.5):
        self.last_order_ended = False
        self.last_status = None
        if not self.order_id:
            self._emit_log("⚠️ [AutoSMS get_otp_code] Chưa có order_id -> Không thể check OTP!", log_fn)
            self.last_order_ended = True
            return None

        start_time = time.time()
        url = f"{self.base_url}/orders/{self.order_id}?key={self.api_key}"
        self._emit_log(
            f"🔍 [AutoSMS] Check đơn #{self.order_id} (SĐT: {self.phone or 'N/A'}) | Tối đa {int(timeout)}s (giữ nguyên đơn, không hủy sớm)...",
            log_fn
        )

        poll_idx = 0
        last_json_str = None
        terminal_statuses = {
            "cancelled", "canceled", "expired", "refunded", "failed", "timeout", "closed", "error"
        }

        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
            poll_idx += 1
            elapsed = int(time.time() - start_time)

            try:
                r = requests.get(url, timeout=10, proxies=self.proxy)
                try:
                    js = r.json()
                except Exception:
                    raw_txt = (r.text or "").strip().replace("\n", " ")[:300]
                    self._emit_log(
                        f"⚠️ [AutoSMS #{self.order_id} | {elapsed}s | HTTP {r.status_code}] Phản hồi không phải JSON: {raw_txt}",
                        log_fn
                    )
                    js = None

                if js is not None:
                    raw_json_str = json.dumps(js, ensure_ascii=False)
                    json_preview = raw_json_str if len(raw_json_str) <= 420 else (raw_json_str[:420] + "...")

                    # In log ngay ở lần đầu, khi JSON thay đổi, khi HTTP != 200, hoặc định kỳ mỗi 4 nhịp (~16s)
                    if poll_idx == 1 or raw_json_str != last_json_str or r.status_code != 200 or (poll_idx % 4 == 0):
                        self._emit_log(
                            f"📡 [AutoSMS #{self.order_id} | Lần {poll_idx} | {elapsed}s | HTTP {r.status_code}] JSON: {json_preview}",
                            log_fn
                        )
                    last_json_str = raw_json_str

                    otp_code, nguon_truong = self._trich_xuat_ma_tu_json(js)
                    if otp_code:
                        self._emit_log(
                            f"✅ [AutoSMS #{self.order_id} | {elapsed}s] Đã trích xuất OTP={otp_code} từ [{nguon_truong}] | JSON: {json_preview}",
                            log_fn
                        )
                        return otp_code

                    # Nếu API trả trạng thái đơn đã hủy / hết hạn / hoàn tiền -> dừng chờ sớm để chuyển bước đổi số ngay
                    data_obj = js.get("data") if isinstance(js, dict) else None
                    st_raw = None
                    if isinstance(data_obj, dict):
                        st_raw = data_obj.get("status") or data_obj.get("state")
                    if not st_raw and isinstance(js, dict):
                        st_raw = js.get("status")
                    if st_raw:
                        self.last_status = str(st_raw).strip().lower()
                    if self.last_status in terminal_statuses:
                        self.last_order_ended = True
                        self._emit_log(
                            f"🛑 [AutoSMS #{self.order_id} | {elapsed}s] Đơn trên web đã kết thúc (status={st_raw}) -> Dừng spam số này để thuê số mới!",
                            log_fn
                        )
                        return None

            except Exception as e:
                self._emit_log(
                    f"⚠️ [AutoSMS #{self.order_id} | {elapsed}s] Lỗi kết nối API: {type(e).__name__}: {str(e)[:180]}",
                    log_fn
                )

            # Chờ theo nhịp ngắn (mặc định 2.5s) để bắt OTP tức thì và Ctrl+C dừng ngay
            sleep_until = time.time() + max(1.0, float(poll_interval))
            while time.time() < sleep_until and not STOP_EVENT.is_set():
                time.sleep(min(0.5, sleep_until - time.time()))

        final_preview = (last_json_str[:350] + "...") if (last_json_str and len(last_json_str) > 350) else (last_json_str or "KHÔNG CÓ PHẢN HỒI")
        self._emit_log(
            f"⏰ [AutoSMS #{self.order_id}] Hết nhịp chờ {int(timeout)}s chưa thấy OTP (vẫn GIỮ ĐƠN) | JSON cuối: {final_preview}",
            log_fn
        )
        return None

    def cancel_order(self, log_fn=None, ly_do=""):
        if self.order_id:
            oid = self.order_id
            ph = self.phone
            tag_ly_do = f" ({ly_do})" if ly_do else ""
            try:
                r = requests.get(f"{self.base_url}/cancel/{oid}?key={self.api_key}", timeout=10, proxies=self.proxy)
                try:
                    phan_hoi = json.dumps(r.json(), ensure_ascii=False)[:260]
                except Exception:
                    phan_hoi = (r.text or "").strip().replace("\n", " ")[:200]
                self._emit_log(
                    f"🗑️ [AutoSMS cancel #{oid} | SĐT {ph or 'N/A'}{tag_ly_do} | HTTP {r.status_code}] {phan_hoi}",
                    log_fn
                )
            except Exception as e:
                self._emit_log(
                    f"⚠️ [AutoSMS cancel #{oid}{tag_ly_do}] Lỗi gọi hủy đơn: {type(e).__name__}: {str(e)[:140]}",
                    log_fn
                )
            finally:
                self.order_id = None
                self.phone = None
                self.last_order_ended = False
                self.last_status = None


def generate_dot_variants(gmail, max_limit=5000):
    """Giới hạn số lượng biến thể tránh tràn RAM & đơ CPU khi tên Gmail quá dài"""
    local, sep, domain = gmail.rpartition("@")
    if not sep or domain.lower() != "gmail.com":
        return [gmail]
    local = local.replace(".", "")
    if not local:
        return [gmail]

    variants = []
    total_masks = 1 << max(0, min(len(local) - 1, 14))
    for mask in range(total_masks):
        value = local[0]
        for i in range(1, len(local)):
            if mask & (1 << (i - 1)):
                value += "."
            value += local[i]
        variants.append(value + "@" + domain)
        if len(variants) >= max_limit:
            break
    random.shuffle(variants)
    return variants


def select_mode(default_mode=None):
    built_in_print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list thường (Có Mail.tm thì Tự động) ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Biến thể ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}5. {Colors.VALUE}HOTMAIL/OUTLOOK     \033[97m[ Dùng API Smail1s.com ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}6. {Colors.VALUE}THUÊ SỐ ĐIỆN THOẠI  \033[97m[ Dùng API AutoSMS.site ]{Colors.RESET}")
    hint = f" (Enter dùng lại [{default_mode}])" if default_mode in ["1", "2", "3", "4", "5", "6"] else ""
    while True:
        built_in_print(f"{Colors.KEY}Nhập lựa chọn [1-6]{hint}: {Colors.RESET}", end="")
        choice = input().strip()
        if not choice and default_mode in ["1", "2", "3", "4", "5", "6"]:
            return default_mode
        if choice in ["1", "2", "3", "4", "5", "6"]:
            return choice


def process_file_input(config_key, default_prompt):
    config_data = load_config()
    saved_file = config_data.get(config_key)
    file_path = ""

    if saved_file and os.path.isfile(saved_file):
        built_in_print(f"{Colors.INFO}Phát hiện tệp danh sách cũ: {Colors.VALUE}{saved_file}{Colors.RESET}")
        use_old = input(f"{Colors.KEY}Bạn có muốn sử dụng lại tệp này không? (y/n, Enter=y): {Colors.RESET}").strip().lower()
        if use_old in ['', 'y']:
            file_path = saved_file

    if not file_path:
        built_in_print(default_prompt, end="")
        file_path = input().strip().strip('"').strip("'")
        if file_path and not os.path.isabs(file_path):
            cand_path = os.path.join(BASE_DIR, file_path)
            if os.path.isfile(cand_path):
                file_path = cand_path
        if os.path.isfile(file_path):
            config_data[config_key] = file_path
            save_config(config_data)

    if os.path.isfile(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if config_key == 'last_file_mode2':
            is_proxy_format = any(':' in l and '@' not in l for l in lines)
            if is_proxy_format:
                built_in_print(f"{Colors.ERROR}LỖI: Tệp này chứa Proxy, KHÔNG PHẢI danh sách Email!{Colors.RESET}")
                config_data.pop(config_key, None)
                save_config(config_data)
                return []

        total = len(lines)
        if total == 0:
            built_in_print(f"{Colors.ERROR}File trống!{Colors.RESET}")
            return []

        built_in_print(f"{Colors.SUCCESS}Đã tải {total} dòng từ tệp.{Colors.RESET}")
        start_line = input(f"{Colors.KEY}Bạn muốn chạy TỪ dòng số mấy? (Nhấn Enter để chạy từ đầu [1]): {Colors.RESET}").strip()
        end_line = input(f"{Colors.KEY}Bạn muốn chạy ĐẾN dòng số mấy? (Nhấn Enter để chạy đến cuối [{total}]): {Colors.RESET}").strip()

        start_idx = max(1, int(start_line) if start_line.isdigit() else 1)
        end_idx = min(total, int(end_line) if end_line.isdigit() else total)

        if start_idx > end_idx:
            selected_lines = lines
        else:
            selected_lines = lines[start_idx - 1:end_idx]

        # Tự động lọc bỏ toàn bộ email đã từng dùng (tắt tool bật lại vẫn nhớ!)
        tap_da_dung = lay_tap_email_da_dung()
        if tap_da_dung:
            chua_dung = []
            so_bo_qua = 0
            for ln in selected_lines:
                em_k = chuan_hoa_email_key(ln)
                if em_k and em_k in tap_da_dung:
                    so_bo_qua += 1
                    continue
                chua_dung.append(ln)
            selected_lines = chua_dung
            built_in_print(
                f"{Colors.WARNING}📌 Tự động nhớ lịch sử: Đã bỏ qua {so_bo_qua} email từng dùng trước đó "
                f"-> Còn lại {len(selected_lines)} email MỚI chưa dùng!{Colors.RESET}"
            )
        else:
            built_in_print(f"{Colors.INFO}=> Đã chọn {len(selected_lines)} data (Từ số {start_idx} đến {end_idx}){Colors.RESET}")
        return selected_lines
    else:
        manual_items = [e.strip() for e in file_path.split(",") if e.strip()]
        tap_da_dung = lay_tap_email_da_dung()
        if tap_da_dung:
            filtered = [x for x in manual_items if not (chuan_hoa_email_key(x) in tap_da_dung)]
            if len(filtered) < len(manual_items):
                built_in_print(
                    f"{Colors.WARNING}📌 Đã tự bỏ qua {len(manual_items) - len(filtered)} email từng dùng "
                    f"-> Còn {len(filtered)} email mới!{Colors.RESET}"
                )
            return filtered
        return manual_items


# ==================== CẤU HÌNH DELAY & TIỆN ÍCH ADB (ĐÃ TỐI ƯU CHỐNG LAG) ====================
def doc_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception:
            return DEFAULT_CONFIG.copy()
    else:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG.copy()


def luu_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def ap_dung_config_chong_checkpoint():
    config_moi = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cu = json.load(f)
                if cu.get('mat_khau_fb'):
                    config_moi['mat_khau_fb'] = cu['mat_khau_fb']
                if 'doi_ip_may_bay' in cu:
                    config_moi['doi_ip_may_bay'] = cu['doi_ip_may_bay']
                if 'tat_bat_4g_khi_xoa_du_lieu' in cu:
                    config_moi['tat_bat_4g_khi_xoa_du_lieu'] = cu['tat_bat_4g_khi_xoa_du_lieu']
                if 'xoa_du_lieu_noi' in cu:
                    config_moi['xoa_du_lieu_noi'] = cu['xoa_du_lieu_noi']
                if 'xoa_tu_dong_dien_va_khoa_truy_cap' in cu:
                    config_moi['xoa_tu_dong_dien_va_khoa_truy_cap'] = cu['xoa_tu_dong_dien_va_khoa_truy_cap']
                if 'dung_proxy_adb' in cu:
                    config_moi['dung_proxy_adb'] = cu['dung_proxy_adb']
                if 'doi_android_id' in cu:
                    config_moi['doi_android_id'] = cu['doi_android_id']
                if 'dung_user_phu_cleanfb' in cu:
                    config_moi['dung_user_phu_cleanfb'] = cu['dung_user_phu_cleanfb']
                if cu.get('fb_apk_path'):
                    config_moi['fb_apk_path'] = cu['fb_apk_path']
                if cu.get('api_chuyen_link_sang_uid'):
                    config_moi['api_chuyen_link_sang_uid'] = cu['api_chuyen_link_sang_uid']
                if cu.get('deeplink_cai_dat_trang_ca_nhan'):
                    config_moi['deeplink_cai_dat_trang_ca_nhan'] = cu['deeplink_cai_dat_trang_ca_nhan']
        except Exception:
            pass
    luu_config(config_moi)
    return config_moi


def nhap_delay(tieu_de, gia_tri_mac_dinh):
    try:
        nhap = input(f'   {tieu_de} ({gia_tri_mac_dinh} giây): ').strip()
        if nhap:
            return float(nhap)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        pass
    return gia_tri_mac_dinh


def cau_hinh_delay():
    print('\n──────────────────────────────────────────────────────────────────────')
    print(f'{trang}⚙️  CẤU HÌNH DELAY & ANTI-CHECKPOINT (ĐỔI IP MÁY BAY + ANDROID ID)')
    print('──────────────────────────────────────────────────────────────────────')
    config = doc_config()

    hoi_xoa_noi = input(f"   Bật Xóa Dữ Liệu NỔI trên màn hình (mở Thông tin ứng dụng, chạy được mọi điện thoại)? (y/n, Enter={'y' if config.get('xoa_du_lieu_noi', True) else 'n'}): ").strip().lower()
    if hoi_xoa_noi in ['y', 'n']:
        config['xoa_du_lieu_noi'] = (hoi_xoa_noi == 'y')

    hoi_xoa_af = input(f"   Tự động Xóa sạch Dịch vụ Tự động điền & Trình quản lý khóa truy cập? (y/n, Enter={'y' if config.get('xoa_tu_dong_dien_va_khoa_truy_cap', True) else 'n'}): ").strip().lower()
    if hoi_xoa_af in ['y', 'n']:
        config['xoa_tu_dong_dien_va_khoa_truy_cap'] = (hoi_xoa_af == 'y')

    hoi_4g_xoa = input(f"   Tự động Tắt/Bật 4G đổi IP sau khi gỡ trang FB & xóa dữ liệu? (y/n, Enter={'y' if config.get('tat_bat_4g_khi_xoa_du_lieu', True) else 'n'}): ").strip().lower()
    if hoi_4g_xoa in ['y', 'n']:
        config['tat_bat_4g_khi_xoa_du_lieu'] = (hoi_4g_xoa == 'y')

    hoi_may_bay = input(f"   Bật tự động đổi IP 4G bằng Chế độ máy bay đầu mỗi lượt? (y/n, Enter={'y' if config.get('doi_ip_may_bay', False) else 'n'}): ").strip().lower()
    if hoi_may_bay in ['y', 'n']:
        config['doi_ip_may_bay'] = (hoi_may_bay == 'y')

    hoi_user_phu = input(f"   Bật chế độ tạo User phụ CleanFB (Ưu tiên máy chính -> dự phòng APK) mỗi acc? (y/n, Enter={'y' if config.get('dung_user_phu_cleanfb', False) else 'n'}): ").strip().lower()
    if hoi_user_phu in ['y', 'n']:
        config['dung_user_phu_cleanfb'] = (hoi_user_phu == 'y')

    if config.get('dung_user_phu_cleanfb', False):
        apk_hien_tai = config.get('fb_apk_path') or DEFAULT_FB_APK_FILE
        nhap_apk = input(f"   Đường dẫn file facebook.apk dự phòng (Enter giữ '{apk_hien_tai}'): ").strip().strip('"').strip("'")
        if nhap_apk:
            if not os.path.isabs(nhap_apk):
                nhap_apk = os.path.join(BASE_DIR, nhap_apk)
            config['fb_apk_path'] = nhap_apk

    hoi_android_id = input(f"   Bật tự động đổi mã phần cứng Android ID mỗi acc? (y/n, Enter={'y' if config.get('doi_android_id', True) else 'n'}): ").strip().lower()
    if hoi_android_id in ['y', 'n']:
        config['doi_android_id'] = (hoi_android_id == 'y')

    mat_khau_moi = input(f"   Nhập mật khẩu FB muốn đặt (Enter giữ '{config['mat_khau_fb']}'): ").strip()
    if mat_khau_moi:
        config['mat_khau_fb'] = mat_khau_moi

    if config.get('doi_ip_may_bay', False) or config.get('tat_bat_4g_khi_xoa_du_lieu', True):
        config['thoi_gian_bat_may_bay'] = nhap_delay('Thời gian ngâm tắt 4G / Chế độ máy bay để nhả IP cũ', config.get('thoi_gian_bat_may_bay', 5.0))
        config['thoi_gian_cho_4g'] = nhap_delay('Thời gian chờ 4G kết nối lại sau khi bật lại', config.get('thoi_gian_cho_4g', 6.0))

    config['delay_mo_facebook'] = nhap_delay('Delay chờ mở Facebook', config.get('delay_mo_facebook', 8.0))
    config['delay_up_avatar'] = nhap_delay('Delay chờ tải xong Avatar', config.get('delay_up_avatar', 8.0))
    config['delay_giua_cac_lan_chay'] = nhap_delay('Delay giữa các lần chạy', config.get('delay_giua_cac_lan_chay', 4.0))

    luu_config(config)
    print('\n✅ Đã lưu cấu hình!')
    return config


def print_multi_status():
    PAUSE_FOR_INPUT.wait()
    with log_lock:
        if device_steps:
            for _ in range(len(device_steps)):
                sys.stdout.write('\x1b[F\x1b[K')
            sys.stdout.flush()
            for i, (device, step) in enumerate(device_steps.items(), 1):
                if '✅' in step or '🎉' in step:
                    color = xanh
                elif '❌' in step:
                    color = do
                elif '⚠️' in step or '⏰' in step:
                    color = vang
                else:
                    color = xanh_duong
                built_in_print(f"{color}{i}. {device:<25} | {step}{trang}")
            sys.stdout.flush()


def update_step(device_name, step):
    if not multi_mode:
        print(f"[{device_name}] {step}")
        return
    PAUSE_FOR_INPUT.wait()
    with log_lock:
        if device_name in device_last_step and device_last_step[device_name] == step:
            return
        device_last_step[device_name] = step
        device_steps[device_name] = step
    print_multi_status()


def doc_tele():
    if os.path.exists(TELE_FILE):
        with open(TELE_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            token, id_tele = None, None
            for line in lines:
                if line.startswith('Token:'):
                    token = line.replace('Token:', '').strip()
                elif line.startswith('ID:'):
                    id_tele = line.replace('ID:', '').strip()
            return (token, id_tele)
    return (None, None)


def luu_tele(token, id_tele):
    with open(TELE_FILE, 'w', encoding='utf-8') as f:
        f.write(f'Token: {token}\n')
        f.write(f'ID: {id_tele}\n')


def gui_tele(token, id_tele, noi_dung):
    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        payload = {'chat_id': id_tele, 'text': noi_dung, 'parse_mode': 'HTML'}
        requests.post(url, json=payload, timeout=10)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        pass


def luu_tai_khoan_fb(email_or_phone, ten_fb, password, two_fa, uid=None):
    """Lưu & in NGAY LẬP TỨC định dạng chuẩn UID (hoặc Link FB đầy đủ) | MK | 2FA vào FB_NhaTrong.txt."""
    uid_clean = str(uid).strip() if uid else ""
    la_link_fb = uid_clean.lower().startswith(('http://', 'https://')) or ('facebook.com' in uid_clean.lower()) or ('fb.com' in uid_clean.lower()) or ('fb.me' in uid_clean.lower())
    uid_str = uid_clean if uid_clean else (str(email_or_phone).strip() if email_or_phone else 'NO_UID')
    if uid_clean:
        uid_status = f"{uid_clean} (Link FB đầy đủ - chưa tách được UID số)" if la_link_fb else uid_clean
    else:
        uid_status = f"NO_UID (dự phòng: {uid_str})"
    nhan_uid = "🔗 Link FB   " if la_link_fb else "🆔 UID       "
    two_fa_str = two_fa if two_fa else 'NO_2FA'
    ten_fb_str = ten_fb if ten_fb else 'NO_NAME'
    dong_tk = f'{uid_str} | {password} | {two_fa_str}'
    with DATA_LOCK:
        with open(FB_ACCOUNT_FILE, 'a', encoding='utf-8') as f:
            f.write(dong_tk + '\n')
            f.flush()
    print(f"\n{xanh}══════════════════════════════════════════════════════════════════════{trang}")
    print(f"{xanh}🎉 TÀI KHOẢN MỚI (IN & LƯU NGAY SAU BƯỚC LẤY UID):{trang}")
    print(f"   {nhan_uid} : {xanh}{uid_status}{trang}")
    print(f"   📧 Mail / SĐT : {vang}{email_or_phone}{trang}")
    print(f"   👤 Tên FB     : {xanh_duong}{ten_fb_str}{trang}")
    print(f"   🔑 Mật khẩu   : {vang}{password}{trang}")
    print(f"   🛡️ Mã 2FA     : {xanh}{two_fa_str}{trang}")
    print(f"   📄 ĐỊNH DẠNG  : {vang}{dong_tk}{trang}")
    print(f"   📂 File lưu   : {xanh_duong}{FB_ACCOUNT_FILE}{trang}")
    print(f"{xanh}══════════════════════════════════════════════════════════════════════{trang}\n", flush=True)
    return dong_tk


def in_luu_va_gui_tele_tai_khoan_ngay(email_or_phone, ten_fb, password, two_fa, uid=None, device_name=None):
    """Gọi ngay sau bước lay_uid_fb (dù lấy được hay không lấy được UID): In ra màn hình + Lưu file + Gửi Telegram tức thì."""
    dong_tk = luu_tai_khoan_fb(email_or_phone, ten_fb, password, two_fa, uid=uid)
    uid_display = str(uid).strip() if uid else (str(email_or_phone).strip() if email_or_phone else 'NO_UID')
    two_fa_display = two_fa if two_fa else 'NO_2FA'
    try:
        token_tele, id_tele = doc_tele()
        if token_tele and id_tele:
            noi_dung = (
                f'<code>{html.escape(str(uid_display))}</code> | '
                f'<code>{html.escape(str(password))}</code> | '
                f'<code>{html.escape(str(two_fa_display))}</code>'
            )
            gui_tele(token_tele, id_tele, noi_dung)
    except Exception:
        pass
    if multi_mode and device_name:
        update_step(device_name, f'✅ ĐÃ IN & LƯU: {dong_tk}')
    return dong_tk


def luu_tai_khoan_die(email_or_phone, ten_fb, password, ly_do):
    """Lưu riêng các tài khoản bị Die/Checkpoint vào FB_Die_Checkpoint.txt (tuyệt đối KHÔNG lưu vào FB_NhaTrong.txt)."""
    ten_fb_str = ten_fb if ten_fb else 'NO_NAME'
    ly_do_str = str(ly_do or 'CHECKPOINT').replace('\n', ' ').strip()
    dong_die = f'{email_or_phone} | {ten_fb_str} | {password} | DIE: {ly_do_str}'
    with DATA_LOCK:
        with open(FB_DIE_FILE, 'a', encoding='utf-8') as f:
            f.write(dong_die + '\n')
            f.flush()
    print(f"\n{do}══════════════════════════════════════════════════════════════════════{trang}")
    print(f"{do}💀 TÀI KHOẢN BỊ DIE / CHECKPOINT (ĐÃ DỪNG NGAY & KHÔNG LƯU NICK LIVE):{trang}")
    print(f"   📧 Mail / SĐT : {vang}{email_or_phone}{trang}")
    print(f"   👤 Tên FB     : {xanh_duong}{ten_fb_str}{trang}")
    print(f"   ⚠️ Lý do      : {do}{ly_do_str}{trang}")
    print(f"   📂 Log Die    : {vang}{FB_DIE_FILE}{trang}")
    print(f"{do}══════════════════════════════════════════════════════════════════════{trang}\n")


def chay_lenh_adb(cmd, serial=None, timeout=15):
    """Chạy lệnh ADB ẩn hoàn toàn cửa sổ ngầm trên Windows (CREATE_NO_WINDOW) kèm timeout chống đơ"""
    try:
        full_cmd = f'adb -s {serial} {cmd}' if serial else f'adb {cmd}'
        subprocess.run(
            full_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=ADB_CREATION_FLAGS,
            timeout=timeout
        )
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        pass


def chay_lenh_adb_lay_ket_qua(cmd, serial=None, timeout=5):
    try:
        full_cmd = f'adb -s {serial} {cmd}' if serial else f'adb {cmd}'
        res = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            creationflags=ADB_CREATION_FLAGS,
            timeout=timeout
        )
        return (res.stdout or '').strip()
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        return ''


def lay_ip_hien_tai_adb(serial=None):
    """Kiểm tra nhanh IP 4G trong tối đa 2 giây để không làm treo luồng"""
    out = chay_lenh_adb_lay_ket_qua(
        'shell "curl -s --max-time 2 https://api.ipify.org || wget -qO- -T 2 https://api.ipify.org"',
        serial,
        timeout=3
    )
    if out and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', out.strip()):
        return out.strip()
    return None


def chay_lenh_adb_list(args, serial=None, timeout=30):
    """Chạy lệnh ADB theo dạng list an toàn với đường dẫn có dấu cách, trả về (ok, output)."""
    cmd = ['adb']
    if serial:
        cmd += ['-s', str(serial)]
    cmd += [str(a) for a in args]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=ADB_CREATION_FLAGS,
            timeout=timeout
        )
        output = ((res.stdout or '') + '\n' + (res.stderr or '')).strip()
        return res.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, 'ADB_TIMEOUT'
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        return False, str(e)


def lay_danh_sach_user_cleanfb(serial=None, user_name=CLEAN_FB_USER_NAME):
    """Liệt kê tất cả User ID có tên CleanFB (tuyệt đối bảo vệ ID 0 và 999 của Xiaomi Dual Apps)."""
    ok, out = chay_lenh_adb_list(['shell', 'pm', 'list', 'users'], serial, timeout=15)
    if not ok and not out:
        return []
    pattern = rf"UserInfo\{{(\d+):{re.escape(user_name)}:"
    ids = []
    for m in re.finditer(pattern, out):
        uid = int(m.group(1))
        if uid > 0 and uid != 999:
            ids.append(uid)
    return ids


def don_sach_user_cleanfb(serial=None, device_name="Device", user_name=CLEAN_FB_USER_NAME):
    """Chuyển màn hình về User 0, dừng tiến trình và xóa sạch toàn bộ User CleanFB trên thiết bị."""
    chay_lenh_adb_list(['shell', 'am', 'switch-user', '0'], serial, timeout=15)
    time.sleep(2.0)

    user_ids = lay_danh_sach_user_cleanfb(serial, user_name)
    for uid in user_ids:
        update_step(device_name, f"🧹 Đang dừng và xóa sạch User phụ {user_name} (ID: {uid})...")
        chay_lenh_adb_list(['shell', 'am', 'stop-user', '-f', str(uid)], serial, timeout=20)
        time.sleep(0.5)
        chay_lenh_adb_list(['shell', 'pm', 'remove-user', str(uid)], serial, timeout=25)

    return len(lay_danh_sach_user_cleanfb(serial, user_name)) == 0


def ket_noi_lai_u2(serial=None, retries=3):
    """Kết nối lại uiautomator2 sau khi chuyển User để tránh rớt phiên hoặc sai ngữ cảnh màn hình."""
    last_err = None
    for lan in range(retries):
        try:
            d = u2.connect(serial) if serial else u2.connect()
            _ = d.window_size()
            return d
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            last_err = e
            time.sleep(1.5 + lan)
    if last_err:
        raise last_err
    return u2.connect(serial) if serial else u2.connect()


def kiem_tra_fb_tren_may_chinh(serial=None):
    """Kiểm tra xem máy chính (User 0) đã cài sẵn ứng dụng Facebook hay chưa."""
    ok, out = chay_lenh_adb_list(['shell', 'pm', 'path', '--user', '0', FB_PACKAGE_NAME], serial, timeout=15)
    if ok and 'package:' in out:
        return True
    ok2, out2 = chay_lenh_adb_list(['shell', 'pm', 'path', FB_PACKAGE_NAME], serial, timeout=15)
    return ok2 and 'package:' in out2


def tao_va_cai_user_cleanfb(serial, apk_path=None, device_name="Device", user_name=CLEAN_FB_USER_NAME):
    """
    Tự động 2 trong 1: Xóa User CleanFB cũ -> Tạo User mới sạch hoàn toàn (SSAID mới) -> Bỏ qua Setup
    -> Ưu tiên nhân bản bộ cài FB trắng từ máy chính (install-existing, ~1s);
       nếu máy chính chưa cài FB (hoặc install-existing lỗi) sẽ tự động đẩy file facebook.apk dự phòng
    -> Chuyển sang User mới.
    """
    co_fb_may_chinh = kiem_tra_fb_tren_may_chinh(serial)
    co_file_apk = bool(apk_path and os.path.isfile(apk_path))
    if not co_fb_may_chinh and not co_file_apk:
        raise FileNotFoundError(
            f"Máy chính chưa cài Facebook ({FB_PACKAGE_NAME}) và cũng không tìm thấy file APK dự phòng tại: {apk_path}"
        )

    # 1. Dọn sạch User CleanFB cũ nếu còn sót
    don_sach_user_cleanfb(serial, device_name, user_name)

    # 2. Tạo User phụ mới
    update_step(device_name, f"🆕 Đang tạo User phụ sạch ({user_name})...")
    ok, out = chay_lenh_adb_list(['shell', 'pm', 'create-user', user_name], serial, timeout=25)
    m = re.search(r"created user id\s+(\d+)", out, re.IGNORECASE)
    if not ok or not m:
        raise RuntimeError(f"Không tạo được User {user_name} (kiểm tra giới hạn User hoặc quyền ADB): {out[:120]}")

    new_id = int(m.group(1))
    if new_id <= 0 or new_id == 999:
        raise RuntimeError(f"User ID trả về không hợp lệ: {new_id}")

    try:
        # 3. Khởi tạo User, bỏ qua Setup ban đầu và tắt Autofill/Backup cho riêng User mới
        update_step(device_name, f"⚙️ Khởi tạo User {new_id} & bỏ qua màn hình Setup...")
        chay_lenh_adb_list(['shell', 'am', 'start-user', str(new_id)], serial, timeout=20)
        time.sleep(2.0)

        setup_cmds = (
            f"settings put --user {new_id} secure user_setup_complete 1; "
            f"settings put --user {new_id} secure backup_auto_restore 0; "
            f"settings put --user {new_id} system accelerometer_rotation 0"
        )
        chay_lenh_adb(f'shell "{setup_cmds}"', serial, timeout=15)
        xoa_sach_tu_dong_dien_va_khoa_truy_cap_adb(serial, user_id=new_id)

        # 4. Tự động 2 trong 1: Ưu tiên nhân bản từ máy chính (1s), chưa có FB mới đẩy facebook.apk
        da_cai_fb = False
        if co_fb_may_chinh:
            update_step(device_name, f"⚡ Nhân bản bộ cài FB sạch từ máy chính sang User {new_id}...")
            ok_ex, out_ex = chay_lenh_adb_list(
                ['shell', 'cmd', 'package', 'install-existing', '--user', str(new_id), FB_PACKAGE_NAME],
                serial,
                timeout=30
            )
            if ok_ex and ('installed for user' in out_ex.lower() or 'success' in out_ex.lower()):
                da_cai_fb = True
            else:
                ok_chk, out_chk = chay_lenh_adb_list(
                    ['shell', 'pm', 'path', '--user', str(new_id), FB_PACKAGE_NAME],
                    serial,
                    timeout=15
                )
                if ok_chk and 'package:' in out_chk:
                    da_cai_fb = True
                elif co_file_apk:
                    update_step(device_name, f"⚠️ Lấy từ máy chính lỗi ({out_ex[:40]}), chuyển sang đẩy facebook.apk...")
                else:
                    raise RuntimeError(
                        f"Nhân bản FB từ máy chính sang User {new_id} thất bại và không có file APK dự phòng: {out_ex[:120]}"
                    )

        if not da_cai_fb:
            if not co_file_apk:
                raise FileNotFoundError(f"Không tìm thấy file APK Facebook dự phòng tại: {apk_path}")
            update_step(device_name, f"📦 Đang chờ/cài facebook.apk vào User {new_id}...")
            with APK_INSTALL_LOCK:
                update_step(device_name, f"📲 Đang đẩy và cài facebook.apk vào User {new_id}...")
                ok_ins, out_ins = chay_lenh_adb_list(
                    ['install', '--user', str(new_id), apk_path],
                    serial,
                    timeout=180
                )
            if not ok_ins or 'Success' not in out_ins:
                raise RuntimeError(
                    f"Cài facebook.apk vào User {new_id} thất bại (bật 'Cài đặt qua USB' trên Xiaomi): {out_ins[:120]}"
                )

        # Đóng Facebook ở User 0 (nếu đang chạy ngầm) để giải phóng RAM, giảm lỗi FB tự tắt/ANR trên User phụ
        chay_lenh_adb_list(['shell', 'am', 'force-stop', '--user', '0', FB_PACKAGE_NAME], serial, timeout=10)

        # 5. Chuyển màn hình điện thoại sang User mới và chờ User mới giải nén & ổn định hoàn toàn
        update_step(device_name, f"🔀 Chuyển sang User sạch ID {new_id} & chờ hệ thống ổn định...")
        ok_sw, out_sw = chay_lenh_adb_list(['shell', 'am', 'switch-user', str(new_id)], serial, timeout=20)
        if not ok_sw:
            raise RuntimeError(f"Không chuyển được sang User {new_id}: {out_sw[:120]}")

        # Chờ cho tới khi User mới thực sự là current user và đạt trạng thái RUNNING_UNLOCKED (tối đa 16s)
        deadline_u = time.time() + 16.0
        while time.time() < deadline_u and not STOP_EVENT.is_set():
            ok_cur, out_cur = chay_lenh_adb_list(['shell', 'am', 'get-current-user'], serial, timeout=8)
            if ok_cur and out_cur.strip() == str(new_id):
                ok_du, out_du = chay_lenh_adb_list(['shell', 'dumpsys', 'user'], serial, timeout=10)
                if not ok_du or f"UserInfo{{{new_id}:" not in out_du or "RUNNING_UNLOCKED" in out_du:
                    break
            time.sleep(1.0)

        # Chờ thêm 3.5s để MIUI Launcher / WebView / MediaProvider của User mới tải xong, tránh crash & ANR khi mở FB
        time.sleep(3.5)
        chay_lenh_adb('shell "input keyevent 224; input keyevent 82"', serial, timeout=6)
        # Cấp quyền bộ nhớ 1 lần duy nhất TRƯỚC khi mở app Facebook (không cấp lại khi app đang chạy)
        cap_quyen_bo_nho_fb(serial, user_id=new_id)
        update_step(device_name, f"✅ User sạch ID {new_id} đã sẵn sàng!")
        return new_id
    except Exception:
        don_sach_user_cleanfb(serial, device_name, user_name)
        raise


def lam_moi_thong_so_thiet_bi_adb(serial=None, config=None, user_id=0):
    if config and not config.get('doi_android_id', True):
        return
    new_android_id = ''.join(random.choices('0123456789abcdef', k=16))
    u_flag = f"--user {int(user_id)} " if user_id and int(user_id) > 0 else ""
    chay_lenh_adb(f'shell "settings put {u_flag}secure android_id {new_android_id}; logcat -c"', serial, timeout=8)


_LAST_4G_RESET_TS = {}
_LAST_4G_LOCK = threading.Lock()


def tat_bat_4g_doi_ip_adb(serial=None, device_name="Device", config=None, bo_qua_cooldown=False):
    """
    Tắt/Bật 4G (kết hợp Chế độ máy bay để nhà mạng cấp IP 4G mới 100%) sau khi đã gỡ hết trang FB, đóng tab và xóa dữ liệu:
    - Nếu thiết bị đang gắn Proxy Wi-Fi ADB (`serial in ADB_PROXY_BRIDGES`) và không bật `doi_ip_may_bay` -> giữ nguyên Wi-Fi Proxy.
    - Ngược lại: Tắt 4G (`svc data disable` + `mobile_data 0` + bật máy bay) -> chờ -> Tắt máy bay + Bật 4G (`svc data enable` + `mobile_data 1`) -> chờ 4G có IP mới!
    """
    if config is not None:
        cho_phep_4g = config.get('tat_bat_4g_khi_xoa_du_lieu', True) or config.get('doi_ip_may_bay', False)
        if not cho_phep_4g:
            return False

    bridge_key = serial if serial else "dev_0"
    with ADB_PROXY_LOCK:
        dang_dung_proxy_wifi = bridge_key in ADB_PROXY_BRIDGES
    if dang_dung_proxy_wifi and not (config and config.get('doi_ip_may_bay', False)):
        update_step(device_name, "🌐 Đang dùng Proxy Wi-Fi ADB -> Giữ nguyên kết nối Proxy (không tắt Wi-Fi).")
        return False

    if not bo_qua_cooldown:
        with _LAST_4G_LOCK:
            last_ts = _LAST_4G_RESET_TS.get(bridge_key, 0.0)
            if (time.time() - last_ts) < 25.0:
                return False

    tg_tat_4g = float(config.get('thoi_gian_bat_may_bay', 5.0)) if config else 5.0
    tg_cho_4g = float(config.get('thoi_gian_cho_4g', 6.0)) if config else 6.0

    ip_cu = lay_ip_hien_tai_adb(serial)
    update_step(device_name, f"📴 Đang TẮT 4G & bật Chế độ máy bay ({tg_tat_4g}s) | IP cũ: {ip_cu or 'Đang lấy'}...")
    chay_lenh_adb(
        'shell "svc wifi disable; svc data disable; settings put global mobile_data 0; '
        'cmd connectivity airplane-mode enable; settings put global airplane_mode_on 1; '
        'am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true"',
        serial,
        timeout=10
    )

    time.sleep(max(2.0, tg_tat_4g))

    update_step(device_name, f"📡 Đang tắt Chế độ máy bay & BẬT LẠI 4G (chờ {tg_cho_4g}s lên mạng)...")
    chay_lenh_adb(
        'shell "cmd connectivity airplane-mode disable; settings put global airplane_mode_on 0; '
        'am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false; '
        'svc wifi disable; settings put global mobile_data 1; svc data enable"',
        serial,
        timeout=10
    )

    time.sleep(max(3.0, tg_cho_4g))

    # Xác minh 4G đã thực sự kết nối lại Internet (tối đa thêm 8s)
    ip_moi = None
    for _ in range(4):
        if STOP_EVENT.is_set():
            break
        ip_moi = lay_ip_hien_tai_adb(serial)
        if ip_moi:
            break
        chay_lenh_adb('shell "svc data enable"', serial, timeout=6)
        time.sleep(2.0)

    with _LAST_4G_LOCK:
        _LAST_4G_RESET_TS[bridge_key] = time.time()

    if ip_moi:
        update_step(device_name, f"🌐 Tắt/Bật 4G đổi IP thành công: {ip_cu or 'N/A'} -> {ip_moi}")
    else:
        update_step(device_name, "✅ Đã Tắt/Bật 4G xong (4G đang kết nối ổn định)")
    return True


def doi_ip_che_do_may_bay_adb(serial=None, device_name="Device", config=None):
    if not config or not config.get('doi_ip_may_bay', False):
        return
    tat_bat_4g_doi_ip_adb(serial=serial, device_name=device_name, config=config, bo_qua_cooldown=False)


def cap_quyen_bo_nho_fb(serial=None, user_id=0):
    """Cấp quyền bộ nhớ/Camera/Media chuẩn cho mọi đời Android (hỗ trợ User phụ) và chặn quyền đọc danh bạ/tài khoản máy"""
    u_flag = f"--user {int(user_id)} " if user_id and int(user_id) > 0 else ""
    lenh_gop_quyen = (
        f"pm grant {u_flag}com.facebook.katana android.permission.READ_EXTERNAL_STORAGE; "
        f"pm grant {u_flag}com.facebook.katana android.permission.WRITE_EXTERNAL_STORAGE; "
        f"pm grant {u_flag}com.facebook.katana android.permission.READ_MEDIA_IMAGES; "
        f"pm grant {u_flag}com.facebook.katana android.permission.READ_MEDIA_VISUAL_USER_SELECTED; "
        f"pm grant {u_flag}com.facebook.katana android.permission.CAMERA; "
        f"cmd appops set {u_flag}com.facebook.katana READ_EXTERNAL_STORAGE allow; "
        f"cmd appops set {u_flag}com.facebook.katana WRITE_EXTERNAL_STORAGE allow; "
        f"cmd appops set {u_flag}com.facebook.katana READ_MEDIA_IMAGES allow; "
        f"cmd appops set {u_flag}com.facebook.katana MANAGE_EXTERNAL_STORAGE allow; "
        f"cmd appops set {u_flag}com.facebook.katana LEGACY_STORAGE allow; "
        f"cmd appops set {u_flag}com.facebook.katana GET_ACCOUNTS ignore; "
        f"cmd appops set {u_flag}com.facebook.katana READ_CONTACTS ignore; "
        f"cmd appops set {u_flag}com.facebook.katana READ_PHONE_STATE ignore; "
        f"cmd appops set {u_flag}com.facebook.katana READ_PHONE_NUMBERS ignore"
    )
    chay_lenh_adb(f'shell "{lenh_gop_quyen}"', serial, timeout=10)


def khoa_xoay_man_hinh(serial=None, user_id=0):
    u_flag = f"--user {int(user_id)} " if user_id and int(user_id) > 0 else ""
    chay_lenh_adb(f'shell settings put {u_flag}system accelerometer_rotation 0', serial, timeout=5)


def xoa_task_fb_bang_adb(serial=None, xoa_ca_cai_dat=False, user_id=0):
    """
    Rút an toàn các thẻ (task) Facebook ra khỏi hàng đợi Đa nhiệm (Recents) bằng ADB:
    - CHỈ đụng gói Facebook (`com.facebook.katana`, `com.facebook.lite`), TUYỆT ĐỐI KHÔNG động vào tiến trình hệ thống
      (`com.miui.securitycenter`, `com.android.settings`) và KHÔNG dùng `am stack remove` (tránh crash system_server gây khởi động lại máy).
    Trả về số task ID đã gửi lệnh xóa.
    """
    try:
        target_pkgs = ['com.facebook.katana', 'com.facebook.lite']

        ok, out = chay_lenh_adb_list(['shell', 'dumpsys', 'activity', 'recents'], serial, timeout=8)
        if not ok or not out:
            return 0

        task_ids = set()
        blocks = re.split(r'(?=\*\s*Recent\s+#\d+)', out)
        for blk in blocks:
            blk_low = blk.lower()
            if not any(pkg in blk_low for pkg in target_pkgs):
                continue
            for pat in [
                r'Task(?:Record)?\{[^\n\}]*?#(\d+)\b',
                r'\bid=(\d+)\b',
                r'\btaskId=(\d+)\b',
            ]:
                for m in re.finditer(pat, blk):
                    tid = int(m.group(1))
                    if 0 < tid < 1000000:
                        task_ids.add(tid)

        if task_ids:
            cmds = []
            for tid in sorted(task_ids):
                cmds.append(f'am task remove {tid}')
                cmds.append(f'cmd activity remove-task {tid}')
            chay_lenh_adb(f'shell "{"; ".join(cmds)}"', serial, timeout=10)
        return len(task_ids)
    except Exception:
        return 0


def kiem_tra_tu_dong_dien_va_khoa_truy_cap_da_sach(serial=None, user_id=0):
    """
    Kiểm tra thực tế 3 khóa hệ thống Android:
    - `autofill_service` (Dịch vụ tự động điền)
    - `credential_service` (Trình quản lý khóa truy cập / mật khẩu bổ sung)
    - `credential_service_primary` (Trình quản lý khóa truy cập / mật khẩu chính - Android 14+)
    Trả về (da_sach_het: bool, danh_sach_con_lai: list[str]).
    """
    uid = int(user_id) if user_id else 0
    u_args = ['--user', str(uid)] if uid > 0 else []
    con_lai = []
    for key in ['autofill_service', 'credential_service', 'credential_service_primary']:
        ok, out = chay_lenh_adb_list(['shell', 'settings', 'get'] + u_args + ['secure', key], serial, timeout=6)
        val = (out or '').strip()
        if ok and val and val.lower() not in {'null', 'none', '""', "''"} and 'exception' not in val.lower() and 'error' not in val.lower():
            con_lai.append(f'{key}={val}')
    return (len(con_lai) == 0), con_lai


def xoa_sach_tu_dong_dien_va_khoa_truy_cap_adb(serial=None, user_id=0):
    """
    Xóa sạch hoàn toàn Dịch vụ Tự động điền (Autofill) và Trình quản lý khóa truy cập (Credential Manager / Passkeys) qua ADB:
    - Dùng `settings delete` (xóa hẳn khóa về null, không để chuỗi rác "null") cho:
      * `autofill_service`
      * `credential_service`
      * `credential_service_primary`
      * `autofill_field_classification`
    - Tắt luôn `backup_auto_restore 0`, `auto_sync 0`, hủy phiên Autofill trong RAM (`cmd autofill destroy`, `cmd autofill reset`).
    - Kiểm tra xác minh lại bằng `settings get` xem đã thực sự sạch 100% hay bị ROM chặn quyền WRITE_SECURE_SETTINGS.
    Trả về (da_sach_het: bool, danh_sach_con_lai: list[str]).
    """
    uid = int(user_id) if user_id else 0
    u_flag = f"--user {uid} " if uid > 0 else ""

    lenh_xoa_s = (
        f'settings delete {u_flag}secure autofill_service; '
        f'settings delete {u_flag}secure credential_service; '
        f'settings delete {u_flag}secure credential_service_primary; '
        f'settings delete {u_flag}secure autofill_field_classification; '
        f'settings put {u_flag}secure credential_service_enabled 0; '
        f'settings put {u_flag}secure backup_auto_restore 0; '
        f'settings put global auto_sync 0; '
        f'cmd autofill destroy; '
        f'cmd autofill reset'
    )
    chay_lenh_adb(f'shell "{lenh_xoa_s}"', serial, timeout=10)

    da_sach, con_lai = kiem_tra_tu_dong_dien_va_khoa_truy_cap_da_sach(serial, user_id=uid)
    if not da_sach:
        # Một số bản Android / MIUI giữ giá trị mặc định nếu delete không được -> ghi đè chuỗi rỗng "" để vô hiệu hóa
        lenh_ghi_rong = (
            f'settings put {u_flag}secure autofill_service ""; '
            f'settings put {u_flag}secure credential_service ""; '
            f'settings put {u_flag}secure credential_service_primary ""; '
            f'cmd autofill destroy'
        )
        chay_lenh_adb(f'shell "{lenh_ghi_rong}"', serial, timeout=8)
        da_sach, con_lai = kiem_tra_tu_dong_dien_va_khoa_truy_cap_da_sach(serial, user_id=uid)

    return da_sach, con_lai


def xoa_du_lieu_fb(serial=None, user_id=0):
    """
    Làm sạch triệt để toàn bộ dữ liệu Facebook + Meta Companion Services (tách riêng từng lệnh, CÓ XÁC MINH Success):
    1. Tắt Autofill/SmartLock riêng (không làm chết dây chuyền lệnh xóa nếu MIUI chặn settings).
    2. Force-stop & rút task Facebook khỏi Đa nhiệm.
    3. Chạy riêng `pm clear com.facebook.katana` có xác minh 'Success' (thử tối đa 2 lần).
    4. Xóa luôn dữ liệu các dịch vụ Meta đi kèm (appmanager, services, system) để chống tự khôi phục nick cũ.
    5. Xóa sạch thư mục rác Facebook trên bộ nhớ trong.
    Trả về True nếu `pm clear com.facebook.katana` trả về Success.
    """
    uid = int(user_id) if user_id else 0
    u_args = ['--user', str(uid)] if uid > 0 else []
    u_flag = f"--user {uid} " if uid > 0 else ""
    storage_root = f"/storage/emulated/{uid}" if uid > 0 else "/sdcard"

    # 1. Xóa sạch dịch vụ Tự động điền & Trình quản lý khóa truy cập (best-effort riêng lẻ)
    xoa_sach_tu_dong_dien_va_khoa_truy_cap_adb(serial, user_id=uid)

    # 2. Dừng hẳn Facebook và các dịch vụ Meta đi kèm + rút task khỏi Đa nhiệm
    meta_pkgs = ['com.facebook.katana', 'com.facebook.appmanager', 'com.facebook.services', 'com.facebook.system']
    for pkg in meta_pkgs:
        chay_lenh_adb_list(['shell', 'am', 'force-stop'] + u_args + [pkg], serial, timeout=8)
    xoa_task_fb_bang_adb(serial)

    # 3. Chạy riêng `pm clear com.facebook.katana` có kiểm tra kết quả Success
    pm_clear_ok = False
    for _ in range(2):
        ok_cl, out_cl = chay_lenh_adb_list(['shell', 'pm', 'clear'] + u_args + ['com.facebook.katana'], serial, timeout=15)
        if ok_cl and 'success' in (out_cl or '').lower():
            pm_clear_ok = True
            break
        time.sleep(0.5)

    # 4. Dọn luôn dữ liệu các dịch vụ Meta đi kèm (tránh tự đăng nhập lại / hiện lại nick cũ qua SSO)
    for companion_pkg in ['com.facebook.appmanager', 'com.facebook.services', 'com.facebook.system']:
        chay_lenh_adb_list(['shell', 'pm', 'clear'] + u_args + [companion_pkg], serial, timeout=10)

    # 5. Xóa sạch thư mục rác trên bộ nhớ
    chay_lenh_adb(
        f'shell "rm -rf {storage_root}/Android/data/com.facebook.* '
        f'{storage_root}/Android/media/com.facebook.* '
        f'{storage_root}/Android/obb/com.facebook.* '
        f'{storage_root}/.facebook* {storage_root}/facebook*; '
        f'am broadcast {u_flag}-a android.intent.action.CLOSE_SYSTEM_DIALOGS"',
        serial,
        timeout=10
    )
    time.sleep(0.4)
    return pm_clear_ok


def chuan_bi_may_chinh_khong_user_ao(serial=None, device_name="Device", config=None):
    """
    Chuẩn bị chạy tạo tài khoản trực tiếp bên ngoài máy chính (User 0):
    Tuyệt đối không tạo / chuyển / xóa User ảo CleanFB.
    Trả về True nếu `pm clear` thành công.
    """
    if not kiem_tra_fb_tren_may_chinh(serial):
        raise FileNotFoundError(
            f"Máy chính chưa cài ứng dụng Facebook ({FB_PACKAGE_NAME})! Hãy cài Facebook trên máy chính trước."
        )

    update_step(device_name, "🧹 [Bên ngoài - User 0] Đang dọn sạch dữ liệu Facebook & tắt Autofill...")
    chay_lenh_adb('shell "input keyevent 224; input keyevent 82"', serial, timeout=6)
    pm_ok = xoa_du_lieu_fb(serial, user_id=0)
    lam_moi_thong_so_thiet_bi_adb(serial, config, user_id=0)
    khoa_xoay_man_hinh(serial, user_id=0)
    cap_quyen_bo_nho_fb(serial, user_id=0)
    update_step(device_name, "✅ [Bên ngoài - User 0] Máy chính đã sạch, sẵn sàng tạo tài khoản!")
    return pm_ok


def get_devices():
    try:
        result = subprocess.run(
            'adb devices',
            shell=True,
            capture_output=True,
            text=True,
            creationflags=ADB_CREATION_FLAGS,
            timeout=10
        )
        lines = result.stdout.strip().split('\n')[1:]
        devices = []
        for line in lines:
            if line.strip() and 'device' in line and 'offline' not in line:
                serial = line.split()[0]
                devices.append((serial, serial))
        return devices
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        return []


# ==================== CLASS ĐIỀU KHIỂN GIAO DIỆN FACEBOOK ====================
class FacebookUI:

    def __init__(self, serial=None, device_name=None, config=None, avatar_folder="", d_instance=None, user_id=0, req_proxy=None):
        if d_instance is not None:
            self.d = d_instance
            self.serial = serial
            self.device_name = device_name if device_name else (serial or "Device")
        elif serial:
            self.d = u2.connect(serial)
            self.serial = serial
            self.device_name = device_name if device_name else serial
        else:
            self.d = u2.connect()
            self.serial = None
            self.device_name = "Device"
        self.package = 'com.facebook.katana'
        self.config = config
        self.avatar_folder = avatar_folder
        self.user_id = int(user_id) if user_id else 0
        self.req_proxy = req_proxy
        self._window_size_cache = None
        self._consecutive_dump_errors = 0

    def _u_flag(self):
        return f"--user {self.user_id} " if self.user_id > 0 else ""

    def _mo_app_fb_theo_user(self):
        """
        Mở Facebook chuẩn theo đúng User ID:
        Ưu tiên Intent LAUNCHER gốc để app khởi tạo đầy đủ trên User mới (tránh crash khi nhảy thẳng LoginActivity),
        chỉ fallback sang LoginActivity nếu lệnh đầu không mở được.
        """
        uf = self._u_flag()
        ok_main, out_main = chay_lenh_adb_list(
            ['shell', 'am', 'start']
            + (['--user', str(self.user_id)] if self.user_id > 0 else [])
            + ['-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.LAUNCHER', 'com.facebook.katana'],
            self.serial,
            timeout=15
        )
        if not ok_main or 'error' in out_main.lower():
            self.chay_shell_nhanh(
                f'am start {uf}-n com.facebook.katana/com.facebook.katana.LoginActivity || '
                f'monkey -p com.facebook.katana -c android.intent.category.LAUNCHER 1'
            )

    def _lay_app_dang_hien_thi(self):
        """Lấy (package, activity) đang hiển thị ở foreground một cách an toàn."""
        try:
            cur = self.d.app_current() or {}
            return str(cur.get('package', '') or ''), str(cur.get('activity', '') or '')
        except Exception:
            return '', ''

    def _lay_kich_thuoc_man_hinh(self):
        """Lưu đệm kích thước màn hình tránh gọi RPC window_size() lặp lại liên tục."""
        if self._window_size_cache is None:
            self._window_size_cache = self.d.window_size()
        return self._window_size_cache

    def _phuc_hoi_u2_nhe(self):
        """Kết nối lại uiautomator2 nhẹ nhàng khi đọc XML bị nghẽn — TUYỆT ĐỐI KHÔNG tắt Facebook hay tắt Wi-Fi/4G."""
        try:
            self.log('🔌 [UI] Đọc màn hình XML bị nghẽn -> Kết nối lại uiautomator2 nhẹ nhàng (giữ nguyên FB)...')
            self.d = ket_noi_lai_u2(self.serial, retries=2)
            self._window_size_cache = None
            self._consecutive_dump_errors = 0
            return True
        except Exception:
            return False

    def _tom_tat_man_hinh(self, snap, max_items=5):
        """Trích ngắn gọn các chữ chính đang hiển thị trên màn hình để dễ nhận biết khi gặp màn lạ."""
        if not snap or not snap.get('nodes'):
            return 'TRỐNG (DUMP_ERROR)' if (snap and snap.get('dump_error')) else 'TRỐNG'
        seen = []
        for n in snap['nodes']:
            lbl = (n.get('text') or n.get('desc') or '').strip()
            if lbl and lbl not in seen:
                seen.append(lbl[:38])
                if len(seen) >= max_items:
                    break
        return ' | '.join(seen) if seen else 'KHÔNG CÓ TEXT'

    def quet_snapshot(self):
        """
        Đọc toàn bộ màn hình hiện tại chỉ bằng 1 lần dump XML (~0.2s) và phân tích tức thì trên RAM (<2ms):
        - Tách bạch rõ `dump_error` (lỗi đọc XML của u2) với `is_blank_or_loading` (màn đang trắng/xoay tải thật).
        - Fix nhận diện Bloks UI của Facebook (nơi `clickable=true` nằm ở ViewGroup cha, còn text nằm ở TextView con)
          để không bao giờ bị báo nhầm là màn hình đang tải khi giao diện đã hiện rõ.
        """
        try:
            w, h = self._lay_kich_thuoc_man_hinh()
        except Exception:
            w, h = 1080, 2400

        snap = {
            'w': w, 'h': h, 'nodes': [], 'all_texts_low': [], 'full_text_low': '',
            'exact_texts_low': set(), 'edit_texts': [], 'has_progress': False,
            'has_number_picker': False, 'has_media_grid': False, 'packages': set(),
            'is_blank_or_loading': True, 'dump_error': True, 'sig': '', 'raw_xml': ''
        }
        try:
            xml_str = self.d.dump_hierarchy() or ''
        except Exception:
            self._consecutive_dump_errors += 1
            return snap

        snap['raw_xml'] = xml_str
        if not xml_str.strip():
            self._consecutive_dump_errors += 1
            return snap

        bounds_re = re.compile(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]')
        try:
            root = ET.fromstring(xml_str.encode('utf-8'))
        except Exception:
            self._consecutive_dump_errors += 1
            return snap

        self._consecutive_dump_errors = 0
        nodes = []
        all_texts_low = []
        exact_low = set()
        edit_texts = []
        packages = set()
        has_progress = False
        has_number_picker = False
        co_nut_tuong_tac = False
        has_any_clickable = False
        so_o_anh = 0

        for el in root.iter('node'):
            attrib = el.attrib
            pkg = (attrib.get('package') or '').strip()
            if pkg:
                packages.add(pkg)

            # Bỏ qua thanh trạng thái / thanh điều hướng hệ thống khi kiểm tra màn hình trắng
            if pkg == 'com.android.systemui':
                continue

            cls = (attrib.get('class') or '').strip()
            rid = (attrib.get('resource-id') or '').strip()
            txt = (attrib.get('text') or '').strip()
            desc = (attrib.get('content-desc') or '').strip()
            m_b = bounds_re.match(attrib.get('bounds') or '')
            if not m_b:
                continue
            l, t, r, b = int(m_b.group(1)), int(m_b.group(2)), int(m_b.group(3)), int(m_b.group(4))
            bw, bh = r - l, b - t
            if bw <= 0 or bh <= 0 or r <= 0 or b <= 0 or l >= w or t >= h:
                continue

            cx, cy = (l + r) // 2, (t + b) // 2
            enabled = (attrib.get('enabled') != 'false')
            clickable = (attrib.get('clickable') == 'true')
            focused = (attrib.get('focused') == 'true')
            password = (attrib.get('password') == 'true')
            checked = (attrib.get('checked') == 'true')

            if 'ProgressBar' in cls:
                has_progress = True
            if 'NumberPicker' in cls:
                has_number_picker = True
            if clickable or 'Button' in cls:
                has_any_clickable = True
            if ('ImageView' in cls or 'Image' in cls) and clickable and bw >= int(w * 0.14) and bh >= int(w * 0.14) and int(h * 0.12) <= cy <= int(h * 0.85):
                so_o_anh += 1

            txt_low = txt.lower()
            desc_low = desc.lower()
            if txt_low:
                all_texts_low.append(txt_low)
                exact_low.add(txt_low)
            if desc_low and desc_low != txt_low:
                all_texts_low.append(desc_low)
                exact_low.add(desc_low)

            node = {
                'text': txt, 'desc': desc, 'text_low': txt_low, 'desc_low': desc_low,
                'rid': rid, 'cls': cls, 'pkg': pkg,
                'l': l, 't': t, 'r': r, 'b': b, 'cx': cx, 'cy': cy, 'bw': bw, 'bh': bh,
                'enabled': enabled, 'clickable': clickable, 'focused': focused,
                'password': password, 'checked': checked
            }
            nodes.append(node)

            if cls == 'android.widget.EditText' and bw >= 40 and bh >= 20 and int(h * 0.08) <= cy <= int(h * 0.88):
                edit_texts.append(node)
            if (clickable or 'Button' in cls) and (txt_low or desc_low):
                co_nut_tuong_tac = True

        full_text_low = ' | '.join(all_texts_low)
        has_media_grid = so_o_anh >= 2
        dau_hieu_dang_tai = [
            'đang tải', 'đang tạo tài khoản', 'đang đăng nhập', 'đang xác minh',
            'đang đăng xuất', 'đang xóa', 'đang gỡ',
            'vui lòng đợi', 'vui lòng chờ', 'loading', 'please wait',
            'creating account', 'signing in', 'logging in', 'verifying',
            'logging out', 'signing out', 'removing', 'deleting'
        ]
        non_loading_texts = [t for t in all_texts_low if not any(k in t for k in dau_hieu_dang_tai)]
        if not co_nut_tuong_tac and has_any_clickable and len(non_loading_texts) >= 2:
            co_nut_tuong_tac = True

        chi_co_chu_tai = (
            len(non_loading_texts) == 0
            and len(all_texts_low) > 0
            and len(edit_texts) == 0
        )

        is_blank_or_loading = (
            (len(all_texts_low) == 0 and not has_media_grid)
            or chi_co_chu_tai
            or (has_progress and len(edit_texts) == 0 and not has_number_picker and not co_nut_tuong_tac and not has_media_grid and len(non_loading_texts) <= 1)
        )

        sig = hashlib.md5(f"{full_text_low}|{len(edit_texts)}|{int(has_number_picker)}".encode('utf-8', errors='ignore')).hexdigest()[:12]
        snap.update({
            'nodes': nodes,
            'all_texts_low': all_texts_low,
            'full_text_low': full_text_low,
            'exact_texts_low': exact_low,
            'edit_texts': edit_texts,
            'has_progress': has_progress,
            'has_number_picker': has_number_picker,
            'has_media_grid': has_media_grid,
            'packages': packages,
            'is_blank_or_loading': is_blank_or_loading,
            'dump_error': False,
            'sig': sig
        })
        return snap

    def _snap_has(self, snap, keywords, exact=False):
        if not snap or not snap['all_texts_low']:
            return False
        if exact:
            ex = snap['exact_texts_low']
            return any(k.lower() in ex for k in keywords)
        full = snap['full_text_low']
        return any(k.lower() in full for k in keywords)

    def _snap_find(self, snap, keywords, exact=False, click_duoi=False, min_y=0.0, max_y=1.0, min_x=0.0, max_x=1.0):
        """Tìm phần tử khớp từ khóa trực tiếp trên snapshot (0 lệnh RPC)."""
        if not snap or not snap['nodes']:
            return None
        w, h = snap['w'], snap['h']
        y1, y2 = int(h * min_y), int(h * max_y)
        x1, x2 = int(w * min_x), int(w * max_x)
        kws = [k.lower() for k in keywords]
        matches = []

        for n in snap['nodes']:
            if not (x1 <= n['cx'] <= x2 and y1 <= n['cy'] <= y2):
                continue
            tl, dl = n['text_low'], n['desc_low']
            if exact:
                hit = (tl in kws) or (dl in kws)
            else:
                hit = any((k in tl or k in dl) for k in kws)
            if hit:
                matches.append(n)

        if not matches:
            return None
        return matches[-1] if click_duoi else matches[0]

    def _snap_click(self, snap, keywords, exact=False, click_duoi=False, min_y=0.0, max_y=1.0, min_x=0.0, max_x=1.0):
        node = self._snap_find(snap, keywords, exact=exact, click_duoi=click_duoi, min_y=min_y, max_y=max_y, min_x=min_x, max_x=max_x)
        if node:
            self.click_toa_do_an_toan(node['cx'], node['cy'])
            return True
        return False

    def _snap_find_rid(self, snap, rid_list):
        if not snap:
            return None
        rid_set = set(rid_list)
        for n in snap['nodes']:
            if n['rid'] in rid_set:
                return n
        return None

    def cho_man_hinh_san_sang(self, timeout=35.0, ngu_canh="", check_die=True, allow_media_grid=False):
        """
        Đợi đến khi màn hình KHÔNG còn trắng / lag / đang tải mới trả về snapshot.
        - Nếu lỗi đọc XML (`dump_error`) liên tiếp >= 3 lần: tự reconnect nhẹ u2 (KHÔNG tắt FB, KHÔNG tắt Wi-Fi/4G).
        - Tự động đóng lớp phủ Google Credential & xử lý ANR/Crash thực sự.
        - Nếu FB bị đẩy xuống nền: chỉ đưa FB lên foreground (KHÔNG force-stop làm mất bước đang dở).
        """
        deadline = time.time() + float(timeout)
        last_log = 0.0
        last_app_chk = time.time()
        last_overlay_chk = 0.0
        while time.time() < deadline and not STOP_EVENT.is_set():
            snap = self.quet_snapshot()
            if snap.get('dump_error'):
                if self._consecutive_dump_errors >= 3:
                    self._phuc_hoi_u2_nhe()
                time.sleep(0.45)
                continue

            if self.xu_ly_anr_va_crash(tu_mo_lai_fb=True, snap=snap) == 'restarted':
                time.sleep(0.8)
                continue
            if 'com.google.android.gms' in snap['packages']:
                if self.dong_goi_y_google(max_thu=3):
                    last_overlay_chk = time.time()
                    continue
            san_sang = (not snap['is_blank_or_loading']) or (allow_media_grid and snap['has_media_grid'])
            if san_sang:
                if check_die:
                    ly_do_die = self.kiem_tra_tai_khoan_die(snap=snap)
                    if ly_do_die:
                        tag = f' [{ngu_canh}]' if ngu_canh else ''
                        self.log(f'💀 PHÁT HIỆN TÀI KHOẢN DIE/CHECKPOINT{tag}: {ly_do_die} -> DỪNG NGAY!')
                        raise AccountDieError(ly_do_die)
                return snap

            now = time.time()
            if now - last_overlay_chk >= 2.0:
                last_overlay_chk = now
                if self.dong_goi_y_google(max_thu=2):
                    continue
            if now - last_app_chk >= 7.0:
                last_app_chk = now
                self.dam_bao_fb_dang_chay(max_retry=1, cho_len_giay=3.5, cho_phep_force_stop=False, snap=snap)
            if now - last_log >= 4.0:
                tag = f' ({ngu_canh})' if ngu_canh else ''
                self.log(f'⏳ Màn hình đang trắng / tải dữ liệu{tag} -> Đợi hiện ra mới thao tác...')
                last_log = now
            time.sleep(0.35)
        return self.quet_snapshot()

    def _cho_chuyen_man_hinh(self, prev_sig, timeout=4.0, old_screen_keywords=None):
        """
        Sau khi bấm nút chuyển bước, chờ màn hình THỰC SỰ rời khỏi trang cũ:
        - Nếu truyền `old_screen_keywords`: CHỈ thoát khi các từ khóa nhận diện trang cũ đã BIẾN MẤT khỏi màn hình
          (tránh trường hợp bàn phím ẩn/hiện hoặc nút đổi trạng thái làm đổi `sig` nhưng vẫn đang ở trang cũ -> gõ lặp đè sang trang mới!).
        """
        deadline = time.time() + float(timeout)
        time.sleep(0.45)
        while time.time() < deadline and not STOP_EVENT.is_set():
            snap = self.quet_snapshot()
            if snap['is_blank_or_loading']:
                return snap
            if old_screen_keywords:
                if not self._snap_has(snap, old_screen_keywords) and not snap['has_progress']:
                    return snap
            else:
                if snap['sig'] != prev_sig and not snap['has_progress']:
                    return snap
            time.sleep(0.28)
        return self.quet_snapshot()

    def _nhap_vao_node_va_xac_minh(self, node, text, is_password=False, placeholders=None):
        """
        Nhấn đúng tọa độ EditText đọc được từ snapshot rồi nhập chính xác chuỗi text:
        - Nếu bàn phím bật lên làm dịch vị trí EditText > 40px, tự tìm đúng EditText đang focused / gần nhất (tránh elem=None).
        - Tắt Google Autofill trước khi nhập mật khẩu để không bao giờ bị điền mật khẩu gợi ý ngẫu nhiên.
        """
        if is_password:
            try:
                self.chay_shell_nhanh('cmd autofill destroy')
            except Exception:
                pass
        self.click_toa_do_an_toan(node['cx'], node['cy'])
        time.sleep(0.3)
        elem = None
        try:
            edits = self.d(className='android.widget.EditText')
            cnt = edits.count
            if cnt == 1:
                elem = edits[0]
            elif cnt > 1:
                best_dist = 999999
                for i in range(cnt):
                    info_i = edits[i].info
                    b = info_i.get('bounds') or {}
                    cx = (b.get('left', 0) + b.get('right', 0)) // 2
                    cy = (b.get('top', 0) + b.get('bottom', 0)) // 2
                    if is_password and info_i.get('password'):
                        elem = edits[i]
                        break
                    if info_i.get('focused'):
                        elem = edits[i]
                        break
                    dist = abs(cx - node['cx']) + abs(cy - node['cy'])
                    if dist < best_dist:
                        best_dist = dist
                        elem = edits[i]
        except Exception:
            pass
        self.xoa_o_nhap(elem)
        self.nhap_text(text, elem=elem, is_password=is_password, placeholders=placeholders)

    def xu_ly_anr_va_crash(self, tu_mo_lai_fb=True, snap=None):
        """
        Phát hiện & xử lý ngay hộp thoại hệ thống Android/MIUI ('Facebook không phản hồi' / 'liên tục dừng')
        trực tiếp từ 1 snapshot duy nhất (không gọi 8 lần RPC .exists).
        """
        s = snap if snap is not None else self.quet_snapshot()
        co_anr = (
            self._snap_find_rid(s, ['android:id/aerr_wait']) is not None
            or self._snap_has(s, ['không phản hồi', "isn't responding", 'isn’t responding'])
        )
        co_crash = (
            self._snap_find_rid(s, ['android:id/aerr_close']) is not None
            or self._snap_has(s, ['liên tục dừng', 'đã dừng', 'keeps stopping', 'has stopped'])
        )

        if co_anr or co_crash:
            loai_loi = 'Facebook không phản hồi (ANR)' if co_anr else 'Facebook đã dừng / liên tục dừng'
            self.log(f'🔄 Phát hiện "{loai_loi}" -> Tắt hẳn Facebook và bật lại ngay...')
            btn_close = self._snap_find_rid(s, ['android:id/aerr_close'])
            if btn_close:
                self.click_toa_do_an_toan(btn_close['cx'], btn_close['cy'])
            else:
                self._snap_click(s, ['Đóng ứng dụng', 'Close app', 'Đóng', 'Close', 'OK', 'Hủy'], exact=True)
            time.sleep(0.8)
            self.chay_shell_nhanh(f'am force-stop {self._u_flag()}com.facebook.katana')
            if self.user_id > 0:
                chay_lenh_adb_list(['shell', 'am', 'force-stop', '--user', str(self.user_id), FB_PACKAGE_NAME], self.serial, timeout=10)
            time.sleep(1.2)

            if tu_mo_lai_fb:
                self.log('🚀 Đang bật lại Facebook sau khi tắt hẳn...')
                self._mo_app_fb_theo_user()
                time.sleep(2.5)
                self.xu_ly_man_hinh_dieu_khoan_meta()
            return 'restarted'

        return ''

    def dam_bao_fb_dang_chay(self, max_retry=2, cho_len_giay=5.0, cho_phep_force_stop=False, snap=None):
        """
        Kiểm tra ANR/Crash thực sự và đảm bảo Facebook đang hiển thị ở foreground:
        - Nếu `app_current()` bị lag trả về rỗng -> KHÔNG bao giờ force-stop Facebook.
        - Nếu Facebook chỉ bị đẩy xuống nền (ví dụ ra Home/Launcher) -> chỉ gọi `_mo_app_fb_theo_user()` đưa lên lại
          để GIỮ NGUYÊN màn hình đang dở, TUYỆT ĐỐI KHÔNG gọi `am force-stop` trừ khi `cho_phep_force_stop=True` hoặc ANR.
        """
        cac_goi_hop_le = {
            'com.facebook.katana',
            'com.android.permissioncontroller',
            'com.google.android.permissioncontroller',
            'com.lbe.security.miui',
            'com.google.android.gms',
            'com.android.documentsui',
            'com.miui.gallery',
            'com.google.android.providers.media.module',
            'com.android.providers.media.module',
            'com.android.vending',
            'com.android.settings',
            'com.miui.securitycenter',
            'com.google.android.webview',
            'com.android.chrome',
            'android',
        }
        for lan in range(1, max_retry + 1):
            s_cur = snap if (lan == 1 and snap is not None) else None
            self.dong_goi_y_google(max_thu=2)
            if s_cur is not None:
                self.dong_bang_google_play_tai_bo_sung(snap=s_cur)
            kq_anr = self.xu_ly_anr_va_crash(tu_mo_lai_fb=True, snap=s_cur)
            if kq_anr == 'restarted':
                time.sleep(0.8)
                continue

            pkg, _ = self._lay_app_dang_hien_thi()
            pkg_low = pkg.lower().strip()

            # Khi app_current() trả rỗng do máy lag -> giữ nguyên, không giết FB!
            if not pkg_low:
                return True

            if pkg_low in cac_goi_hop_le or any(k in pkg_low for k in ('facebook', 'permission', 'gallery', 'media', 'vending', 'webview', 'packageinstaller')):
                return True

            if cho_phep_force_stop:
                self.log(f'⚠️ Facebook đang ở nền ({pkg}) -> Khởi động lại Facebook (lần {lan}/{max_retry})...')
                self.chay_shell_nhanh(f'am force-stop {self._u_flag()}com.facebook.katana')
                time.sleep(1.0)
            else:
                self.log(f'🔄 Facebook bị đẩy xuống nền (đang ở: {pkg}) -> Đưa Facebook lên lại (giữ nguyên bước hiện tại)...')

            self._mo_app_fb_theo_user()

            end_wait = time.time() + max(2.5, float(cho_len_giay))
            while time.time() < end_wait and not STOP_EVENT.is_set():
                time.sleep(0.6)
                cur_pkg, _ = self._lay_app_dang_hien_thi()
                if 'facebook' in cur_pkg.lower():
                    return True

        pkg_cuoi, _ = self._lay_app_dang_hien_thi()
        return (not pkg_cuoi) or ('facebook' in pkg_cuoi.lower()) or (pkg_cuoi.lower() in cac_goi_hop_le)

    def kiem_tra_tai_khoan_die(self, snap=None):
        """
        Quét toàn bộ giao diện hiện tại từ snapshot (0 RPC phụ nếu truyền snap) để nhận diện Die / Đình chỉ / Checkpoint.
        """
        if snap is None:
            try:
                _, cur_act = self._lay_app_dang_hien_thi()
                if 'checkpoint' in cur_act.lower():
                    return f'Activity Checkpoint ({cur_act})'
            except Exception:
                pass
            s = self.quet_snapshot()
        else:
            s = snap

        if not s or not s['all_texts_low']:
            return ''

        toan_man_hinh = s['full_text_low']
        cac_nut_chinh_xac = s['exact_texts_low']

        # CHỐNG BÁO NHẦM ACC DIE TRÊN TRANG CÀI ĐẶT / TRUNG TÂM TÀI KHOẢN / ĐĂNG NHẬP VÀ BẢO MẬT / 2FA:
        # Trên giao diện mới của Meta, trong mục "Đăng nhập và bảo mật" có sẵn dòng cài đặt tên "Video selfie" / "Xác nhận danh tính".
        # Nếu đang ở trang Cài đặt / Bảo mật hợp lệ thì tuyệt đối không coi các tên mục cài đặt đó là checkpoint!
        la_man_cai_dat_bao_mat_hop_le = any(kw in toan_man_hinh for kw in [
            'xác thực 2 yếu tố', 'xác thực hai yếu tố', 'two-factor authentication',
            'đăng nhập và bảo mật', 'mật khẩu và bảo mật', 'sign-in and security',
            'login and security', 'password and security',
            'trung tâm tài khoản', 'accounts center', 'tài khoản meta', 'meta accounts',
            'đổi mật khẩu', 'change password', 'thông tin đăng nhập đã lưu', 'saved login',
            'nơi bạn đã đăng nhập', "where you're logged in", 'where you’re logged in',
            'cảnh báo đăng nhập', 'login alerts', 'kiểm tra bảo mật', 'security checkup',
            'khóa truy cập', 'passkey', 'ứng dụng xác thực', 'authentication app',
            'sao chép khóa', 'copy key', 'thiết lập phương thức bảo vệ tăng cường',
            'chọn phương thức bảo mật', 'cài đặt và quyền riêng tư', 'settings and privacy',
        ])

        dau_hieu_die_chac_chan = [
            'chúng tôi đã đình chỉ tài khoản của bạn',
            'tài khoản của bạn đã bị đình chỉ',
            'tài khoản đã bị đình chỉ',
            'đã bị đình chỉ',
            'tài khoản của bạn đã bị vô hiệu hóa',
            'tài khoản đã bị vô hiệu hóa',
            'đã bị vô hiệu hóa',
            'tài khoản của bạn đã bị khóa',
            'tài khoản đã bị khóa',
            '180 ngày',
            'để kháng nghị',
            'gửi kháng nghị',
            'phản đối quyết định',
            'không tuân thủ tiêu chuẩn cộng đồng',
            'tiêu chuẩn cộng đồng về tính toàn vẹn',
            'xác nhận bạn là người thật',
            'không thể tạo tài khoản',
            'chúng tôi không thể tạo tài khoản',
            'bạn không thể sử dụng facebook',
            'chúng tôi đã nhận được thông tin của bạn',
            'đang xem xét thông tin của bạn',
            'we suspended your account',
            'your account has been suspended',
            'your account has been disabled',
            'your account has been locked',
            '180 days',
            'submit an appeal',
            'disagree with decision',
            'community standards on account integrity',
            "confirm you're human",
            'confirm you’re human',
            'we received your information',
            'reviewing your info',
            "we couldn't create your account",
            'we couldn’t create your account',
            "you can't use facebook",
            'you can’t use facebook',
        ]
        for kw in dau_hieu_die_chac_chan:
            if kw in toan_man_hinh:
                return kw

        # Các cụm từ chỉ coi là checkpoint khi KHÔNG đứng ở màn hình Cài đặt / Đăng nhập và bảo mật / 2FA
        if not la_man_cai_dat_bao_mat_hop_le:
            dau_hieu_checkpoint_ngoai_cai_dat = [
                'giúp chúng tôi xác nhận đó là bạn',
                'xác nhận danh tính của bạn',
                'quay video selfie',
                'tải lên video selfie',
                'gửi video selfie',
                'record a video selfie',
                'take a video selfie',
                'upload a video selfie',
                'tải lên ảnh tự chụp',
                'tải giấy tờ tùy thân',
                'confirm your identity',
                'upload a selfie',
            ]
            for kw in dau_hieu_checkpoint_ngoai_cai_dat:
                if kw in toan_man_hinh:
                    return kw
            if 'video selfie' in toan_man_hinh and any(
                c in toan_man_hinh for c in ['xác nhận', 'đình chỉ', 'khóa', 'kháng nghị', 'người thật', 'confirm', 'suspend', 'lock', 'appeal', 'human']
            ):
                return 'video selfie'

        for nut_die in ['kháng nghị', 'appeal', 'yêu cầu xem xét lại', 'request a review']:
            if nut_die in cac_nut_chinh_xac:
                return f'Nút "{nut_die}"'

        return ''

    def kiem_tra_va_dung_neu_die(self, ngu_canh="", snap=None):
        """Nếu phát hiện tài khoản DIE/Checkpoint thì lập tức dừng toàn bộ các bước tiếp theo."""
        ly_do = self.kiem_tra_tai_khoan_die(snap=snap)
        if ly_do:
            tag = f' [{ngu_canh}]' if ngu_canh else ''
            self.log(f'💀 PHÁT HIỆN TÀI KHOẢN DIE/CHECKPOINT{tag}: {ly_do} -> DỪNG NGAY!')
            raise AccountDieError(ly_do)
        return False

    def log(self, text):
        if multi_mode and self.device_name:
            update_step(self.device_name, text)
        else:
            print(text)

    def chay_shell_nhanh(self, shell_cmd):
        """Gửi lệnh trực tiếp qua socket u2.shell kèm timeout=5s chống treo cứng luồng"""
        try:
            self.d.shell(shell_cmd, timeout=5)
        except Exception:
            chay_lenh_adb(f'shell "{shell_cmd}"', self.serial, timeout=8)

    def click_toa_do_an_toan(self, x, y):
        """Bắn tap trực tiếp qua socket shell để mượt và không bị MIUI chặn ngầm trên Xiaomi"""
        x, y = int(x), int(y)
        self.chay_shell_nhanh(f'input tap {x} {y}')

    def vuot_toa_do_an_toan(self, x1, y1, x2, y2, duration_ms=220):
        """Vuốt trực tiếp qua socket shell để cuộn mượt không lag PC"""
        x1, y1, x2, y2, duration_ms = int(x1), int(y1), int(x2), int(y2), int(duration_ms)
        self.chay_shell_nhanh(f'input swipe {x1} {y1} {x2} {y2} {duration_ms}')

    def _click_phan_tu_an_toan(self, elem):
        """Lấy tâm tọa độ của phần tử để tap qua socket shell + fallback u2.click"""
        try:
            b = elem.info['bounds']
            cx = (b['left'] + b['right']) // 2
            cy = (b['top'] + b['bottom']) // 2
            if cx > 0 and cy > 0:
                self.chay_shell_nhanh(f'input tap {cx} {cy}')
                return True
        except Exception:
            pass
        try:
            elem.click()
            return True
        except Exception:
            return False

    def click_text_chua(self, text, ten_nut="", so_lan_thu=2, delay=0.35, click_duoi=False):
        for i in range(so_lan_thu):
            snap = self.quet_snapshot()
            if self._snap_click(snap, [text], exact=False, click_duoi=click_duoi):
                return True
            if i < so_lan_thu - 1:
                time.sleep(delay)
        return False

    def click_text(self, text, ten_nut="", so_lan_thu=2, delay=0.35):
        for i in range(so_lan_thu):
            snap = self.quet_snapshot()
            if self._snap_click(snap, [text], exact=True):
                return True
            if i < so_lan_thu - 1:
                time.sleep(delay)
        return False

    def click_truong(self, ten_truong, double=False, so_lan_thu=2, delay=0.35):
        for i in range(so_lan_thu):
            snap = self.quet_snapshot()
            node = self._snap_find(snap, [ten_truong], exact=True) or self._snap_find(snap, [ten_truong], exact=False)
            if node:
                if double:
                    self.click_toa_do_an_toan(node['cx'], node['cy'])
                    time.sleep(0.15)
                self.click_toa_do_an_toan(node['cx'], node['cy'])
                return True
            if i < so_lan_thu - 1:
                time.sleep(delay)
        return False

    def _go_chu_bang_adb_input(self, text):
        """
        Gõ chuỗi trực tiếp qua `adb shell input text` (bơm phím cứng qua InputManager, TUYỆT ĐỐI KHÔNG đụng Clipboard):
        - Tách dấu cách thành KEYCODE_SPACE (62).
        - Tách ký tự '%' riêng để Android không biến '%s' thành dấu cách.
        - Trả về True nếu toàn bộ lệnh shell đều trả exit_code == 0 và không báo lỗi.
        """
        s = str(text)
        if not s:
            return False
        parts = s.split(' ')
        all_ok = True
        for idx, part in enumerate(parts):
            if part:
                # Tách riêng '%' để tránh Android Input.java dịch '%s' thành khoảng trắng
                sub_parts = re.split(r'(%)', part) if '%s' in part else [part]
                for sp in sub_parts:
                    if not sp:
                        continue
                    sh_quoted = "'" + sp.replace("'", "'\\''") + "'"
                    cmd = f"input text {sh_quoted}"
                    da_gui = False
                    try:
                        res = self.d.shell(cmd, timeout=6)
                        out_s = (getattr(res, 'output', '') or '').lower()
                        if getattr(res, 'exit_code', 0) == 0 and 'exception' not in out_s and 'permission' not in out_s:
                            da_gui = True
                    except Exception:
                        pass
                    if not da_gui:
                        ok_adb, out_adb = chay_lenh_adb_list(['shell', cmd], self.serial, timeout=10)
                        if not ok_adb or 'exception' in (out_adb or '').lower():
                            all_ok = False
                    time.sleep(0.08)
            if idx < len(parts) - 1:
                da_space = False
                try:
                    res_sp = self.d.shell('input keyevent 62', timeout=5)
                    if getattr(res_sp, 'exit_code', 0) == 0:
                        da_space = True
                except Exception:
                    pass
                if not da_space:
                    ok_sp, _ = chay_lenh_adb_list(['shell', 'input', 'keyevent', '62'], self.serial, timeout=8)
                    if not ok_sp:
                        all_ok = False
                time.sleep(0.06)
        return all_ok

    def _go_mot_ky_tu_adb(self, ch):
        """
        Gõ CHÍNH XÁC 1 ký tự duy nhất qua InputManager của Android (TUYỆT ĐỐI không dán, không dùng Clipboard):
        - Chữ số 0-9 và chữ thường a-z: dùng mã phím cứng `input keyevent` trực tiếp (ổn định 100%).
        - Chữ hoa A-Z và ký tự đặc biệt (@, !, #, $, ., _, -, %...): dùng `input text` 1 ký tự riêng lẻ.
        """
        if not ch:
            return False
        if ch == ' ':
            cmd = 'input keyevent 62'
        elif '0' <= ch <= '9':
            cmd = f'input keyevent {7 + int(ch)}'
        elif 'a' <= ch <= 'z':
            cmd = f'input keyevent {29 + ord(ch) - ord("a")}'
        elif ch == "'":
            cmd = 'input text "\'"'
        else:
            cmd = f"input text '{ch}'"

        try:
            res = self.d.shell(cmd, timeout=5)
            out_s = (getattr(res, 'output', '') or '').lower()
            if getattr(res, 'exit_code', 0) == 0 and 'exception' not in out_s and 'permission' not in out_s:
                return True
        except Exception:
            pass

        ok_adb, out_adb = chay_lenh_adb_list(['shell', cmd], self.serial, timeout=8)
        return bool(ok_adb and 'exception' not in (out_adb or '').lower())

    def _go_tung_ky_tu_cham(self, text, elem=None, is_password=True, delay_ky_tu=0.14, placeholders=None):
        """
        Gõ từ từ từng ký tự một (0.12s - 0.18s / ký tự) dành riêng cho bước nhập Mật khẩu:
        - Không dán chuỗi, không đụng Clipboard, không dùng send_keys.
        - Xóa sạch hoàn toàn ô nhập trước khi gõ để chắc chắn không dính chữ cũ / email.
        """
        s = str(text or '')
        if not s:
            return False

        self.xoa_o_nhap(elem)
        if elem is not None:
            self._click_phan_tu_an_toan(elem)
            time.sleep(0.35)

        all_ok = True
        for ch in s:
            if STOP_EVENT.is_set():
                return False
            if not self._go_mot_ky_tu_adb(ch):
                all_ok = False
            time.sleep(random.uniform(max(0.08, delay_ky_tu - 0.02), delay_ky_tu + 0.04))

        time.sleep(0.35)
        if elem is None:
            return all_ok

        if self._kiem_tra_o_da_co_chu(elem, s, is_password=is_password, placeholders=placeholders):
            return True

        try:
            cur_txt = (elem.info.get('text') or '').strip()
        except Exception:
            cur_txt = ''

        # Một số máy Android ẩn hẳn text ô password (trả về "") dù đã gõ đủ phím cứng
        if is_password and all_ok and cur_txt == '':
            return True

        return False

    def _la_placeholder_o_nhap(self, text, placeholders=None):
        """Kiểm tra text đọc từ EditText có phải chữ gợi ý (placeholder) mặc định hay không."""
        cur = (text or '').strip().lower()
        if not cur:
            return True
        default_ph = {
            'họ', 'tên', 'first name', 'last name', 'surname',
            'mật khẩu', 'mật khẩu của bạn', 'nhập mật khẩu', 'nhập lại mật khẩu',
            'password', 'your password', 'enter your password', 're-enter your password',
            'email', 'địa chỉ email', 'số di động', 'mobile number',
            'mã xác nhận', 'nhập mã', 'confirmation code'
        }
        if placeholders:
            default_ph.update(p.lower() for p in placeholders)
        return cur in default_ph

    def _kiem_tra_o_da_co_chu(self, elem, expected_text, is_password=False, placeholders=None):
        """
        Kiểm tra chính xác EditText đã nhận ĐÚNG chuỗi cần nhập chưa:
        - Với ô Mật khẩu (is_password=True): BẮT BUỘC kiểm tra ĐÚNG ĐỘ DÀI (len(cur) == len(expected_text))
          để chống tuyệt đối lỗi dán nhầm Email dài ngoằng hoặc bị gõ thừa/thiếu ký tự!
        - Với ô thường (Email/Họ/Tên/OTP): khớp chính xác toàn bộ chuỗi.
        """
        if elem is None:
            return False
        try:
            cur = (elem.info.get('text') or '').strip()
        except Exception:
            return False
        if self._la_placeholder_o_nhap(cur, placeholders=placeholders):
            return False
        exp_raw = str(expected_text)
        if is_password:
            return len(cur) == len(exp_raw)
        return cur.lower() == exp_raw.strip().lower()

    def xoa_o_nhap(self, elem=None):
        """
        Xóa sạch nội dung trong ô nhập liệu (KHÔNG dùng d.clear_text() để tránh kích hoạt u2 FastInputIME/Clipboard):
        1. Nếu ô đang có text khác rỗng/placeholder -> dùng `elem.set_text('')`
        2. Nếu vẫn còn chữ -> đưa con trỏ về cuối (`KEYCODE_MOVE_END = 123`) & xóa sạch bằng `KEYCODE_DEL (67)`.
        """
        if elem is not None:
            try:
                cur_before = (elem.info.get('text') or '').strip()
                if self._la_placeholder_o_nhap(cur_before):
                    return
                elem.set_text('')
                time.sleep(0.15)
                cur_after = (elem.info.get('text') or '').strip()
                if self._la_placeholder_o_nhap(cur_after):
                    return
            except Exception:
                pass
        try:
            self.chay_shell_nhanh('input keyevent 123; input keyevent --longpress 67')
            time.sleep(0.18)
            if elem is not None and not self._la_placeholder_o_nhap(elem.info.get('text') or ''):
                del_cmds = '; '.join(['input keyevent 67'] * 45)
                self.chay_shell_nhanh(f'input keyevent 123; {del_cmds}')
                time.sleep(0.15)
        except Exception:
            pass

    def nhap_text(self, text, elem=None, is_password=False, placeholders=None):
        """
        Nhập chữ chính xác 100% — CHỐNG TUYỆT ĐỐI LỖI DÁN NHẦM EMAIL VÀO Ô MẬT KHẨU TRÊN XIAOMI/MIUI:
        - Nguyên nhân gốc ở các bản trước: `d.send_keys()` của uiautomator2 trên MIUI dùng Clipboard + Paste ngầm,
          nên bước Email đưa Email vào Clipboard, sang bước Mật khẩu MIUI chặn ghi Clipboard đè lên -> Paste bắn nguyên Email vào ô Mật khẩu!
        - Cơ chế mới:
          * Mọi chuỗi ASCII (Email, Mật khẩu, Họ, Tên, SĐT, OTP): ƯU TIÊN 100% `_go_chu_bang_adb_input(s)` (`adb shell input text`),
            bơm phím cứng trực tiếp qua InputManager -> KHÔNG BAO GIỜ chạm Clipboard & KHÔNG BAO GIỜ gọi `d.send_keys()`!
          * Chỉ fallback sang `elem.set_text(s)` nếu `input text` không ăn chữ (ô vẫn trống/placeholder).
        """
        s = str(text)
        if not s:
            return

        la_ascii = all(32 <= ord(ch) <= 126 for ch in s)

        # ===== TẦNG 1 (ƯU TIÊN TUYỆT ĐỐI): GÕ TRỰC TIẾP BẰNG ADB SHELL INPUT TEXT (0% CLIPBOARD) =====
        if la_ascii:
            for lan_go in range(1, 3):
                if lan_go > 1:
                    self.xoa_o_nhap(elem)
                    if elem is not None:
                        self._click_phan_tu_an_toan(elem)
                        time.sleep(0.3)
                ok_adb = self._go_chu_bang_adb_input(s)
                time.sleep(0.35)

                if elem is None:
                    if ok_adb:
                        return
                    continue

                if self._kiem_tra_o_da_co_chu(elem, s, is_password=is_password, placeholders=placeholders):
                    time.sleep(0.15)
                    return

                try:
                    cur_txt = (elem.info.get('text') or '').strip()
                except Exception:
                    cur_txt = ''

                # Với ô mật khẩu: một số bản Android ẩn hẳn text (trả về "") dù đã gõ thành công bằng input text
                if is_password and ok_adb and cur_txt == '':
                    time.sleep(0.15)
                    return

                # Nếu ô có text nhưng sai (VD gõ thiếu/thừa) -> xóa sạch và thử lại ở vòng 2
                if cur_txt and not self._la_placeholder_o_nhap(cur_txt, placeholders=placeholders):
                    self.xoa_o_nhap(elem)
                    continue

            # Tầng 2 (chỉ chạy nếu adb input text vẫn để ô trống/placeholder): Accessibility set_text trực tiếp
            if elem is not None:
                try:
                    self.xoa_o_nhap(elem)
                    self._click_phan_tu_an_toan(elem)
                    time.sleep(0.25)
                    elem.set_text(s)
                    time.sleep(0.35)
                    if self._kiem_tra_o_da_co_chu(elem, s, is_password=is_password, placeholders=placeholders):
                        return
                except Exception:
                    pass
            return

        # ===== CHUỖI CÓ DẤU TIẾNG VIỆT (NON-ASCII): DÙNG ACCESSIBILITY set_text TRƯỚC =====
        if elem is not None:
            try:
                elem.set_text(s)
                time.sleep(0.35)
                if self._kiem_tra_o_da_co_chu(elem, s, is_password=is_password, placeholders=placeholders):
                    return
            except Exception:
                pass
        if not is_password:
            try:
                self.xoa_o_nhap(elem)
                self.d.send_keys(s)
                time.sleep(0.3)
            except Exception:
                pass

    def xu_ly_man_hinh_dieu_khoan_meta(self, snap=None):
        """
        Xử lý màn hình 'Điều khoản và Chính sách quyền riêng tư của Meta' từ snapshot (0 RPC phụ).
        """
        s = snap if snap is not None else self.quet_snapshot()
        dau_hieu_dieu_khoan = [
            'Điều khoản và Chính sách quyền riêng tư của Meta',
            'Điều khoản của Meta',
            'Chính sách quyền riêng tư của chúng tôi',
            'dịch vụ được cài đặt sẵn để tự động cập nhật',
            'tự động cập nhật ứng dụng',
            "Meta's Terms and Privacy Policy",
            'Meta Terms and Privacy Policy',
            'automatically update apps'
        ]
        if self._snap_has(s, dau_hieu_dieu_khoan):
            self.log('📜 Phát hiện màn hình "Điều khoản và Chính sách quyền riêng tư của Meta" -> Bấm nút "Tiếp tục"...')
            da_bam = (
                self._snap_click(s, ['Tiếp tục', 'Continue', 'Đồng ý', 'Agree'], exact=True, click_duoi=True)
                or self._snap_click(s, ['Tiếp tục', 'Continue'], exact=False, click_duoi=True)
            )
            if not da_bam:
                self.click_toa_do_an_toan(int(s['w'] * 0.50), int(s['h'] * 0.845))
            self._cho_chuyen_man_hinh(s['sig'], timeout=3.0)
            return True
        return False

    def kiem_tra_text(self, danh_sach_text, so_lan_thu=1, delay=0.35):
        for i in range(so_lan_thu):
            snap = self.quet_snapshot()
            if self._snap_has(snap, danh_sach_text, exact=False):
                return True
            if i < so_lan_thu - 1:
                time.sleep(delay)
        return False

    def tat_quyen_khong_cho_phep(self, snap=None):
        """Quét 1 snapshot duy nhất để bấm Lúc khác / KHÔNG CHO PHÉP khi hiện bảng xin quyền."""
        s = snap if snap is not None else self.quet_snapshot()
        if s['is_blank_or_loading']:
            return False
        cac_nut_tu_choi = [
            'Lúc khác', 'LÚC KHÁC', 'Not now', 'NOT NOW',
            'KHÔNG CHO PHÉP', 'Không cho phép',
            "DON'T ALLOW", 'Don’t allow', "Don't allow", 'Deny', 'DENY'
        ]
        if not self._snap_has(s, ['thư viện ảnh']):
            cac_nut_tu_choi += ['TỪ CHỐI', 'Từ chối']
        if self._snap_click(s, cac_nut_tu_choi, exact=True, click_duoi=True):
            time.sleep(0.45)
            return True
        return False

    def _bam_luc_khac_neu_co(self, snap=None):
        """
        CHỈ bấm khi trên màn hình thực sự có NÚT có nhãn chính xác là 'Lúc khác' / 'Not now' (exact=True, <= 15 ký tự).
        Tuyệt đối KHÔNG dùng exact=False để tránh bấm nhầm đoạn mô tả 'vào lúc khác' ở trang Ngày sinh & Giới tính!
        """
        s = snap if snap is not None else self.quet_snapshot()
        if s['is_blank_or_loading']:
            return False
        node = self._snap_find(s, ['Lúc khác', 'LÚC KHÁC', 'Not now', 'NOT NOW'], exact=True, click_duoi=True)
        if node:
            label = (node.get('text') or node.get('desc') or '').strip()
            if len(label) <= 15:
                self.log(f'🚫 Quét thấy nút "{label}" -> Bấm ngay...')
                self.click_toa_do_an_toan(node['cx'], node['cy'])
                self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
                return True
        return False

    def bo_qua_luu_thong_tin_dang_nhap(self, snap=None):
        """
        Luôn bấm nút 'LÚC KHÁC' / 'Lúc khác' khi hiện bảng 'Lưu thông tin đăng nhập Facebook?' (Ảnh 1)
        hoặc 'Lưu thông tin đăng nhập?' (Ảnh 5). Chỉ tốn 1 snapshot (~0.2s) và không bao giờ dính chữ mô tả.
        """
        s = snap if snap is not None else self.quet_snapshot()
        if s['is_blank_or_loading']:
            return False
        if self._bam_luc_khac_neu_co(snap=s):
            return True

        if self._snap_has(s, [
            'Lưu thông tin đăng nhập Facebook',
            'Lưu thông tin đăng nhập?',
            'Lưu thông tin đăng nhập',
            'bản sao lưu trên đám mây',
            'khôi phục từ bản sao lưu',
            'để bạn không cần nhập vào lần sau'
        ]):
            self.log('🚫 Phát hiện bảng Lưu thông tin đăng nhập -> Bấm "Lúc khác" (Không lưu)')
            if not self._snap_click(s, ['Lúc khác', 'LÚC KHÁC', 'Không lưu', 'KHÔNG LƯU', 'Not now', 'NOT NOW'], exact=True, click_duoi=True):
                w, h = s['w'], s['h']
                if self._snap_has(s, ['khôi phục từ bản sao lưu', 'Bạn sẽ không cần nhập lại']):
                    self.click_toa_do_an_toan(int(w * 0.56), int(h * 0.60))
                else:
                    self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.845))
            self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
            return True
        return False

    def dong_bang_google_play_tai_bo_sung(self, snap=None):
        """
        Phát hiện & đóng ngay bảng Google Play che nửa dưới màn hình Facebook (Ảnh 2):
        ('Google Play' + 'Facebook cần tải các tệp bổ sung xuống...' + nút 'Tải xuống qua Play' / 'Tìm hiểu thêm')
        Tìm ĐỘNG nút dấu X (×) ở góc phải trên của bảng trắng (XML -> icon cùng hàng 'Google Play' -> nhận diện ảnh dấu × -> Back).
        KHÔNG dùng tọa độ cứng.
        """
        s = snap if snap is not None else self.quet_snapshot()
        if not s:
            return False

        dau_hieu_play = [
            'tải xuống qua play', 'download via play', 'download on play',
            'tải các tệp bổ sung xuống', 'tệp bổ sung xuống', 'additional files',
            'xuất hiện trong thư viện play', 'tính năng bổ sung qua play', 'play library'
        ]
        la_bang_play = (
            self._snap_has(s, dau_hieu_play)
            or (self._snap_has(s, ['google play']) and self._snap_has(s, ['tìm hiểu thêm', 'learn more', 'tải xuống', 'download']))
            or ('com.android.vending' in s['packages'] and self._snap_has(s, ['google play', 'play', 'tải xuống', 'tệp bổ sung']))
        )
        if not la_bang_play:
            return False

        w, h = s['w'], s['h']
        self.log('🛡️ Phát hiện bảng "Google Play - tải tệp bổ sung" -> Tìm bấm dấu × đóng bảng...')

        # Xác định hàng ngang của chữ 'Google Play' để khoanh đúng nút × trên bảng trắng
        node_gp = self._snap_find(s, ['Google Play'], exact=False, min_y=0.30, max_y=0.80)
        gp_cy = node_gp['cy'] if node_gp is not None else int(h * 0.57)
        band_min_y = max(0.35, (gp_cy / float(h)) - 0.08)
        band_max_y = min(0.75, (gp_cy / float(h)) + 0.08)

        # 1. Tìm nút × theo text / content-desc / resource-id trong vùng bảng Google Play
        nut_x = (
            self._snap_find(s, ['Đóng', 'Close', 'Dismiss', '×', '✕', '✖', 'X'], exact=True, min_x=0.68, min_y=band_min_y, max_y=band_max_y)
            or self._snap_find(s, ['đóng', 'close', 'dismiss'], exact=False, min_x=0.68, min_y=band_min_y, max_y=band_max_y)
        )
        if nut_x is None:
            for n in s['nodes']:
                rid_low = (n.get('rid') or '').lower()
                if n['cx'] >= int(w * 0.68) and int(h * band_min_y) <= n['cy'] <= int(h * band_max_y):
                    if any(k in rid_low for k in ['close', 'dismiss', 'cancel']):
                        nut_x = n
                        break

        # 2. Tìm node icon clickable nằm góc phải cùng hàng ngang với chữ 'Google Play'
        if nut_x is None:
            ung_vien_x = [
                n for n in s['nodes']
                if n['clickable']
                and n['cx'] >= int(w * 0.72)
                and int(h * band_min_y) <= n['cy'] <= int(h * band_max_y)
                and n['bw'] <= int(w * 0.25)
                and n['bh'] <= int(h * 0.12)
            ]
            if ung_vien_x:
                ung_vien_x.sort(key=lambda n: abs(n['cy'] - gp_cy))
                nut_x = ung_vien_x[0]

        if nut_x is not None:
            self.log(f'✖️ Bấm dấu × đóng bảng Google Play tại ({nut_x["cx"]}, {nut_x["cy"]}) (XML)...')
            self.click_toa_do_an_toan(nut_x['cx'], nut_x['cy'])
            self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
            time.sleep(0.5)
            return True

        # 3. Nhận diện HÌNH ẢNH dấu × ở góc phải trên cùng hàng ngang với 'Google Play' (khi Play không gán nhãn XML)
        if HAS_PIL:
            try:
                shot = self.d.screenshot()
                if shot is not None:
                    img_gray = shot.convert('L')
                    iw, ih = img_gray.size
                    sx = iw / float(w)
                    sy = ih / float(h)
                    cl, cr = int(iw * 0.75), iw
                    ct, cb = int(ih * max(0.38, band_min_y)), int(ih * min(0.72, band_max_y + 0.04))
                    win_s = max(48, int(iw * 0.11))
                    step = max(10, win_s // 3)
                    for wy in range(ct, max(ct + 1, cb - win_s + 1), step):
                        for wx in range(cl, max(cl + 1, cr - win_s + 1), step):
                            ok_x, rcx, rcy = self._la_icon_dau_x(
                                img_gray.crop((wx, wy, min(iw, wx + win_s), min(ih, wy + win_s)))
                            )
                            if ok_x:
                                tx = int((wx + rcx) / sx)
                                ty = int((wy + rcy) / sy)
                                self.log(f'✖️ Bấm dấu × đóng bảng Google Play tại ({tx}, {ty}) (nhận diện ảnh)...')
                                self.click_toa_do_an_toan(tx, ty)
                                self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
                                time.sleep(0.5)
                                return True
            except Exception:
                pass

        # 4. Dự phòng an toàn: bấm Back để hạ bảng Google Play nếu không bắt được nút ×
        self.log('↩️ Bấm Back đóng bảng Google Play...')
        try:
            self.d.press('back')
        except Exception:
            self.chay_shell_nhanh('input keyevent 4')
        self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
        time.sleep(0.5)
        return True

    def quet_va_xoa_man_hinh_chan(self, so_vong_quet=6, snap=None):
        """
        Quét màn hình siêu nhanh (dùng lại `snap` ở vòng đầu để không dump XML lặp) dọn sạch các bảng chắn theo ưu tiên:
        - Ưu tiên 0: Bảng Google Play tải tệp bổ sung (Ảnh 2) -> Bấm dấu × đóng ngay
        - Ưu tiên 1: Nút chính xác 'Bỏ qua' / 'Skip' (trừ màn hình Thêm ảnh đại diện)
        - Ưu tiên 2: Nút chính xác 'Lúc khác' / 'Not now' (tuyệt đối không khớp đoạn văn mô tả)
        - Ưu tiên 3: Nút chính xác 'Không cho phép' / 'Từ chối' (trừ hộp thoại xin quyền thư viện ảnh)
        """
        da_xu_ly = False
        for vong_idx in range(so_vong_quet):
            s = snap if (vong_idx == 0 and snap is not None) else self.quet_snapshot()
            if s['is_blank_or_loading']:
                break

            # ƯU TIÊN 0: Bảng Google Play che phía dưới màn hình FB -> Bấm dấu × đóng ngay!
            if self.dong_bang_google_play_tai_bo_sung(snap=s):
                da_xu_ly = True
                continue

            dang_o_man_avatar = self._snap_has(s, ['thêm ảnh đại diện', 'thêm ảnh', 'add profile picture', 'add picture', 'add photo'])

            # ƯU TIÊN 1: Nút 'Bỏ qua' (CHỈ exact=True)
            if not dang_o_man_avatar and (
                self._snap_has(s, ['Bỏ qua', 'BỎ QUA', 'Skip'], exact=True)
                or self._snap_has(s, ['Bạn có chắc chắn muốn bỏ qua'])
            ):
                self.log('🛡️ [Ưu tiên 1] Phát hiện nút "Bỏ qua" -> Bấm ngay...')
                if not self._snap_click(s, ['Bỏ qua', 'BỎ QUA', 'Skip'], exact=True):
                    self.click_toa_do_an_toan(int(s['w'] * 0.525), int(s['h'] * 0.605))
                da_xu_ly = True
                self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
                continue

            # ƯU TIÊN 2: Nút 'Lúc khác' (CHỈ exact=True)
            if (
                self._snap_has(s, ['Lúc khác', 'LÚC KHÁC', 'Not now', 'NOT NOW'], exact=True)
                or self._snap_has(s, ['cấp quyền truy cập vào danh bạ', 'Để tìm bạn bè nhanh hơn'])
            ):
                self.log('🛡️ [Ưu tiên 2] Phát hiện nút "Lúc khác" -> Bấm ngay...')
                if not self._snap_click(s, ['Lúc khác', 'LÚC KHÁC', 'Not now', 'NOT NOW'], exact=True, click_duoi=True):
                    self.click_toa_do_an_toan(int(s['w'] * 0.50), int(s['h'] * 0.91))
                da_xu_ly = True
                self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
                continue

            # ƯU TIÊN 3: Không cho phép / Từ chối
            la_quyen_thu_vien = self._snap_has(s, ['thư viện ảnh', 'ảnh và video', 'photos and videos'])
            btn_deny = self._snap_find_rid(s, [
                'com.android.permissioncontroller:id/permission_deny_button',
                'com.android.permissioncontroller:id/permission_deny_and_dont_ask_again_button',
                'com.lbe.security.miui:id/permission_deny_button_1'
            ])
            if btn_deny and not la_quyen_thu_vien:
                self.log('🛡️ [Ưu tiên 3] Phát hiện hộp thoại quyền hệ thống -> Bấm "Không cho phép"...')
                self.click_toa_do_an_toan(btn_deny['cx'], btn_deny['cy'])
                da_xu_ly = True
                self._cho_chuyen_man_hinh(s['sig'], timeout=2.0)
                continue

            ds_tu_choi = ['KHÔNG CHO PHÉP', 'Không cho phép', "DON'T ALLOW", 'Don’t allow', "Don't allow", 'DENY', 'Deny']
            if not la_quyen_thu_vien:
                ds_tu_choi += ['TỪ CHỐI', 'Từ chối']
            if self._snap_click(s, ds_tu_choi, exact=True, click_duoi=True):
                self.log('🛡️ [Ưu tiên 3] Phát hiện nút từ chối quyền -> Bấm ngay...')
                da_xu_ly = True
                self._cho_chuyen_man_hinh(s['sig'], timeout=2.0)
                continue

            break
        return da_xu_ly

    def _lay_mcurrentfocus_raw(self):
        """Đọc nhanh các dòng mCurrentFocus từ `dumpsys window` (nhanh qua u2.shell, fallback ADB)."""
        try:
            res = self.d.shell('dumpsys window | grep mCurrentFocus', timeout=4)
            out = getattr(res, 'output', '') if res is not None else ''
            if out and 'mCurrentFocus' in out:
                return out.strip()
        except Exception:
            pass
        try:
            return chay_lenh_adb_lay_ket_qua('shell "dumpsys window | grep mCurrentFocus"', self.serial, timeout=4)
        except Exception:
            return ''

    def _phat_hien_lop_phu_google_fb(self, focus_text=None):
        """
        Kiểm tra trực tiếp `mCurrentFocus` (kể cả khi máy có nhiều dòng mCurrentFocus) và `app_current()`
        để bắt đích danh lớp phủ trong suốt chắn màn hình Facebook:
        - `com.google.android.gms/...SignInCredentialChooserActivity`
        - `com.facebook.katana/androidx.credentials.playservices.controllers.identityauth.HiddenActivity`
        - Các cửa sổ Google Identity / Credential / One-Tap / Smart Lock khác.
        Trả về tên lớp phủ nếu phát hiện, ngược lại trả về chuỗi rỗng ''.
        """
        if focus_text is None:
            focus_text = self._lay_mcurrentfocus_raw()
        check_blobs = []
        if focus_text:
            check_blobs.extend(focus_text.splitlines())
        try:
            pkg_cur, act_cur = self._lay_app_dang_hien_thi()
            if pkg_cur or act_cur:
                check_blobs.append(f'{pkg_cur}/{act_cur}')
        except Exception:
            pass

        mau_lop_phu = [
            ('SignInCredentialChooserActivity', 'signincredentialchooseractivity'),
            ('HiddenActivity (Facebook Credential)', 'identityauth.hiddenactivity'),
            ('HiddenActivity (Facebook Credential)', 'credentials.playservices'),
            ('Google IdentityCredentials', 'identitycredentials'),
            ('Google CredentialPicker', 'credentialpicker'),
            ('Google HintPicker', 'hintpicker'),
            ('Google OneTap', 'onetap'),
            ('Google Auth Credentials', 'auth.api.credentials'),
            ('Google SmartLock', 'smartlock'),
            ('Google Play Services Overlay', 'com.google.android.gms/'),
        ]

        for line in check_blobs:
            low = (line or '').lower()
            if not low:
                continue
            for ten_hien_thi, kw in mau_lop_phu:
                if kw in low:
                    return ten_hien_thi
            if 'hiddenactivity' in low and ('facebook' in low or 'credentials' in low or 'gms' in low):
                return 'HiddenActivity'

        return ''

    def dong_goi_y_google(self, max_thu=4):
        """
        Quét trực tiếp `dumpsys window | grep mCurrentFocus` để phát hiện và bắn Back (`input keyevent 4`)
        đóng ngay lớp phủ trong suốt `SignInCredentialChooserActivity` và `HiddenActivity` (kể cả khi XML trống).
        Trả về True nếu đã phát hiện & đóng ít nhất 1 lớp phủ.
        """
        da_dong = False
        try:
            for lan in range(1, max(1, int(max_thu)) + 1):
                ten_lop_phu = self._phat_hien_lop_phu_google_fb()
                if not ten_lop_phu:
                    break
                self.log(f'🛡️ [mCurrentFocus - Lần {lan}/{max_thu}] Phát hiện lớp phủ "{ten_lop_phu}" -> Bắn Back (keyevent 4) đóng ngay!')
                self.chay_shell_nhanh('cmd autofill destroy; input keyevent 4')
                da_dong = True
                time.sleep(0.75)
        except Exception:
            pass
        return da_dong

    def cho_va_dong_lop_phu_sau_mo_fb(self, thoi_gian_quet=4.5):
        """
        Theo dõi ngay sau khi mở Facebook (đặc biệt sau khi xóa dữ liệu):
        Google Play Services thường bung lớp phủ `SignInCredentialChooserActivity` / `HiddenActivity` sau 1–4s.
        Hàm sẽ quét `mCurrentFocus` định kỳ và bắn Back đóng tức thì ngay khi vừa xuất hiện.
        """
        deadline = time.time() + max(1.5, float(thoi_gian_quet))
        da_tung_dong = False
        so_nhip_fb_sach = 0
        while time.time() < deadline and not STOP_EVENT.is_set():
            if self.dong_goi_y_google(max_thu=4):
                da_tung_dong = True
                so_nhip_fb_sach = 0
                time.sleep(0.7)
                continue
            focus_raw = self._lay_mcurrentfocus_raw().lower()
            if 'com.facebook.katana/' in focus_raw and 'hiddenactivity' not in focus_raw:
                so_nhip_fb_sach += 1
                # Nếu đã từng đóng lớp phủ và FB giữ focus sạch 2 nhịp (~1.2s) -> thoát sớm đi tiếp ngay
                if da_tung_dong and so_nhip_fb_sach >= 2:
                    break
            time.sleep(0.6)
        return da_tung_dong

    def tao_ho_ten(self, used_names=None):
        """Tạo 100% Họ & Tên Nữ chuẩn Việt Nam để đồng bộ giới tính Nữ"""
        if used_names is not None and len(used_names) >= 500:
            used_names.clear()
        while True:
            ho_list = [
                'Nguyen', 'Tran', 'Le', 'Pham', 'Hoang', 'Huynh', 'Phan',
                'Vu', 'Vo', 'Dang', 'Bui', 'Do', 'Ngo', 'Duong', 'Ly', 'Truong'
            ]
            dem_nu_list = [
                'Thi', 'Ngoc', 'Thanh', 'Thu', 'Minh', 'Bao', 'Khanh', 'Phuong',
                'Thuy', 'Hoang', 'Kieu', 'My', 'Anh', 'Quynh', 'Mai', 'Kim', 'Dieu', 'Gia'
            ]
            ten_nu_list = [
                'Anh', 'Linh', 'Trang', 'Huong', 'Thao', 'Nhung', 'Nga', 'Mai',
                'Lan', 'Chi', 'Vy', 'Nhi', 'Han', 'Ngoc', 'Tram', 'Huyen',
                'Yen', 'Duyen', 'Quynh', 'Phuong', 'Uyen', 'Van', 'Dung', 'Hanh',
                'My', 'Ngan', 'Tam', 'Thu', 'Ha', 'Trinh', 'Nhung', 'Tien'
            ]
            ho = random.choice(ho_list)
            dem = random.choice(dem_nu_list)
            ten_chinh = random.choice([t for t in ten_nu_list if t != dem])
            ten = f"{dem} {ten_chinh}"
            full_name = f'{ho} {ten}'
            if used_names is not None and full_name in used_names:
                continue
            if used_names is not None:
                used_names.add(full_name)
            return (ho, ten)

    def tao_so_dien_thoai(self, used_phones=None):
        if used_phones is not None and len(used_phones) >= 10000:
            used_phones.clear()
        while True:
            dau_so = ['033', '034', '035', '036', '037', '038', '039', '070', '077', '078', '079', '083', '084', '085', '096', '097', '098']
            phone = random.choice(dau_so) + ''.join(random.choices(string.digits, k=7))
            if used_phones is not None and phone in used_phones:
                continue
            if used_phones is not None:
                used_phones.add(phone)
            return phone

    def _la_man_hinh_gioi_tinh(self, snap):
        """
        Nhận diện chuẩn xác 100% màn hình 'Giới tính của bạn là gì?' (cả Tiếng Việt & Tiếng Anh, kể cả khi nút radio có nhãn phụ).
        """
        if not snap or snap.get('is_blank_or_loading'):
            return False
        dau_hieu_gt = [
            'giới tính của bạn là gì',
            "what's your gender",
            'what’s your gender',
            'chọn giới tính',
            'người nhìn thấy giới tính',
            'who sees your gender',
            'chọn tùy chọn khác để chọn giới tính',
            'select more options to choose another gender',
        ]
        if self._snap_has(snap, dau_hieu_gt):
            return True

        # Kiểm tra sự xuất hiện đồng thời của lựa chọn Nữ & Nam (cả exact lẫn tiền tố như "Nữ, chưa chọn" / "Female, not selected")
        w, h = snap['w'], snap['h']
        co_nu = False
        co_nam = False
        for n in snap['nodes']:
            if not (int(h * 0.14) <= n['cy'] <= int(h * 0.78)):
                continue
            for val in (n['text_low'], n['desc_low']):
                if not val:
                    continue
                if val in {'nữ', 'female'} or val.startswith(('nữ,', 'nữ ', 'female,', 'female ')):
                    if len(val) <= 32:
                        co_nu = True
                if val in {'nam', 'male'} or val.startswith(('nam,', 'nam ', 'male,', 'male ')):
                    if len(val) <= 32:
                        co_nam = True
        return co_nu and co_nam

    def _da_roi_man_hinh_ngay_sinh(self, snap):
        """
        Trả về True ngay lập tức nếu Facebook ĐÃ chuyển sang màn hình Giới tính hoặc các bước phía sau
        (SĐT / Email / Mật khẩu / Điều khoản / OTP / Nhập tuổi) -> Chặn tuyệt đối lỗi chọn lại Ngày sinh trên trang Giới tính!
        """
        if not snap or snap.get('is_blank_or_loading'):
            return False
        if self._la_man_hinh_gioi_tinh(snap):
            return True
        cac_man_sau_ngay_sinh = [
            'số di động của bạn là gì', "what's your mobile number", 'what’s your mobile number',
            'đăng ký bằng email', 'sign up with email',
            'email của bạn là gì', "what's your email", 'what’s your email', 'nhập email của bạn',
            'tạo mật khẩu', 'create a password',
            'tôi đồng ý', 'i agree', 'đồng ý với các điều khoản',
            'mã xác nhận', 'nhập mã xác nhận', 'confirmation code',
            'bạn bao nhiêu tuổi', 'how old are you',
        ]
        if self._snap_has(snap, cac_man_sau_ngay_sinh):
            return True
        return False

    def _la_man_hinh_ngay_sinh(self, snap):
        """
        CHỈ trả về True khi thực sự đang đứng ở màn hình Ngày sinh (hoặc bảng chọn ngày 3 cột)
        và CHƯA chuyển sang màn Giới tính hay bất kỳ bước nào phía sau.
        """
        if not snap or snap.get('is_blank_or_loading'):
            return False
        if self._da_roi_man_hinh_ngay_sinh(snap):
            return False
        if self._snap_has(snap, [
            'ngày sinh của bạn là khi nào',
            "what's your birthday",
            'what’s your birthday',
            'ngày sinh (',
            'chọn ngày',
            'set date',
        ]):
            return True
        if snap.get('has_number_picker'):
            return True
        return False

    def _dang_hien_bang_chon_ngay(self, snap=None):
        """Chỉ xác nhận đang mở bảng chọn ngày 3 cột khi thực sự có NumberPicker/Chọn ngày và CHƯA sang trang Giới tính."""
        s = snap if snap is not None else self.quet_snapshot()
        if self._da_roi_man_hinh_ngay_sinh(s):
            return False
        if s.get('has_number_picker'):
            return True
        if self._snap_find_rid(s, ['android:id/datePicker']) is not None:
            return True
        if self._snap_has(s, ['chọn ngày', 'set date']) and self._snap_has(s, ['chọn', 'set', 'ok', 'hủy', 'cancel'], exact=True):
            return True
        return False

    def _lay_toa_do_vung_to_do_ngay_sinh(self):
        w, h = self.d.window_size()
        x_do = int(w * 0.65)
        y_do = None

        for dau_hieu in ['Ngày sinh (', 'tuổi)', 'tháng', '2026', '2025']:
            for selector in [self.d(textContains=dau_hieu), self.d(descriptionContains=dau_hieu)]:
                try:
                    if selector.exists:
                        for i in range(selector.count):
                            b = selector[i].info['bounds']
                            cy = (b['top'] + b['bottom']) // 2
                            if int(h * 0.22) <= cy <= int(h * 0.42):
                                y_do = cy
                                break
                    if y_do:
                        break
                except Exception:
                    pass
            if y_do:
                break

        if not y_do:
            for sel_tiep in [self.d(text='Tiếp'), self.d(description='Tiếp'), self.d(textContains='Tiếp')]:
                try:
                    if sel_tiep.exists:
                        b_tiep = sel_tiep[0].info['bounds']
                        if b_tiep['top'] > int(h * 0.28):
                            y_do = b_tiep['top'] - int(h * 0.062)
                            break
                except Exception:
                    pass

        if not y_do:
            y_do = int(h * 0.30)

        return x_do, y_do

    def mo_bang_chon_ngay(self):
        w, h = self._lay_kich_thuoc_man_hinh()
        self._ha_ban_phim_an_toan()
        snap_bd = self.cho_man_hinh_san_sang(timeout=20.0, ngu_canh='Chờ màn hình Ngày sinh')
        if self._da_roi_man_hinh_ngay_sinh(snap_bd):
            return False
        if self._dang_hien_bang_chon_ngay(snap=snap_bd):
            return True

        for _ in range(8):
            s_cur = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Kiểm tra bảng Chọn ngày')
            if self._da_roi_man_hinh_ngay_sinh(s_cur):
                return False
            if self._dang_hien_bang_chon_ngay(snap=s_cur):
                return True
            if self._snap_has(s_cur, ['Ngày sinh của bạn là khi nào', "What's your birthday", 'Ngày sinh (', 'tuổi)']):
                break
            time.sleep(0.35)

        for lan_bam in range(5):
            s_chk = self.quet_snapshot()
            if self._da_roi_man_hinh_ngay_sinh(s_chk):
                return False
            if self._dang_hien_bang_chon_ngay(snap=s_chk):
                return True
            # Tuyệt đối KHÔNG bấm tọa độ mở bảng ngày nếu không xác nhận đang đứng ở trang Ngày sinh!
            if not self._la_man_hinh_ngay_sinh(s_chk):
                return False

            x_do, y_do = self._lay_toa_do_vung_to_do_ngay_sinh()
            x_tap = x_do if lan_bam % 2 == 0 else int(w * 0.68)
            self.log(f'📅 Bấm vào vùng ô Ngày sinh ({x_tap}, {y_do}) để mở bảng 3 cột...')
            self.click_toa_do_an_toan(x_tap, y_do)
            time.sleep(1.0)

            s_sau_tap = self.quet_snapshot()
            if self._da_roi_man_hinh_ngay_sinh(s_sau_tap):
                return False
            if self._dang_hien_bang_chon_ngay(snap=s_sau_tap):
                return True

        return self._dang_hien_bang_chon_ngay()

    def _lay_nam_hien_tai_trong_bang_3_cot(self):
        try:
            pickers = self.d(className='android.widget.NumberPicker')
            if pickers.count >= 3:
                ds_picker = []
                for i in range(pickers.count):
                    b = pickers[i].info['bounds']
                    ds_picker.append((b['left'], pickers[i]))
                ds_picker.sort(key=lambda item: item[0])
                cot_nam = ds_picker[2][1]

                edit_nam = cot_nam.child(className='android.widget.EditText')
                if edit_nam.exists:
                    txt = (edit_nam.info.get('text') or '').strip()
                    if txt.isdigit() and len(txt) == 4:
                        return int(txt)
        except Exception:
            pass

        try:
            inputs = self.d(resourceId='android:id/numberpicker_input')
            if inputs.count >= 3:
                ds_in = []
                for i in range(inputs.count):
                    b = inputs[i].info['bounds']
                    ds_in.append((b['left'], inputs[i].info.get('text') or ''))
                ds_in.sort(key=lambda item: item[0])
                txt_nam = ds_in[2][1].strip()
                if txt_nam.isdigit() and len(txt_nam) == 4:
                    return int(txt_nam)
        except Exception:
            pass
        return None

    def _kiem_tra_tuoi_hop_le_ngoai_man_hinh(self, snap=None):
        """
        Kiểm tra tuổi hiển thị trên trang Ngày sinh CHỈ TỪ CHỮ HIỂN THỊ (`snap['all_texts_low']`),
        TUYỆT ĐỐI KHÔNG regex trên raw XML (vì tọa độ `bounds="[0,2040]..."` chứa số 2040/2088 làm báo sai tuổi!).
        """
        try:
            s = snap if snap is not None else self.quet_snapshot()
            if not s or not s.get('all_texts_low'):
                return False
            nam_toi_da = datetime.now().year - 18  # VD năm 2026 -> <= 2008 là đủ >= 18 tuổi

            # 1. Ưu tiên đọc trực tiếp số tuổi trong ngoặc: VD "Ngày sinh (24 tuổi)" hoặc "(24 years old)"
            for txt in s['all_texts_low']:
                m_tuoi = re.search(r'\(?\b(\d{1,2})\s*(?:tuổi|years?\s*old)\b\)?', txt, re.IGNORECASE)
                if m_tuoi:
                    return int(m_tuoi.group(1)) >= 18

            # 2. Đọc năm sinh 4 chữ số CHỈ trong text/desc nhìn thấy (không bao giờ dính tọa độ pixel!)
            co_nam_hop_le = False
            co_nam_chua_du = False
            for txt in s['all_texts_low']:
                for m_nam in re.finditer(r'\b(19[5-9]\d|20[0-2]\d)\b', txt):
                    nam_val = int(m_nam.group(1))
                    if 1950 <= nam_val <= nam_toi_da:
                        co_nam_hop_le = True
                    elif nam_val > nam_toi_da:
                        co_nam_chua_du = True
            if co_nam_hop_le:
                return True
            if co_nam_chua_du:
                return False
        except Exception:
            pass
        return False

    def vuot_chon_ngay_thang_nam_sinh(self):
        """
        Chọn Ngày/Tháng/Năm sinh AN TOÀN TUYỆT ĐỐI — CHỐNG TRIỆT ĐỂ LỖI CHẠY ĐÈ LÊN TRANG GIỚI TÍNH:
        - Kiểm tra `_da_roi_man_hinh_ngay_sinh()` ở mọi điểm chốt: hễ đã sang trang Giới tính (hoặc bước sau) -> THOÁT NGAY!
        - Nếu trên màn hình Ngày sinh đã hiển thị tuổi >= 18 sẵn -> KHÔNG mở lại bảng 3 cột, chỉ bấm 'Tiếp' 1 lần.
        - Không bao giờ vuốt mù 3 cột khi bảng Chọn ngày không thực sự đang hiển thị.
        - Sau khi bấm 'Tiếp', đợi rời hẳn trang Ngày sinh bằng `_cho_chuyen_man_hinh(..., old_screen_keywords=...)`.
        Trả về 'MOVED' | 'DONE' | 'RETRY'.
        """
        w, h = self._lay_kich_thuoc_man_hinh()

        for lan_thu in range(4):
            if STOP_EVENT.is_set():
                return 'RETRY'

            s_dau = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh=f'Ngày sinh lần {lan_thu + 1}')
            if self._da_roi_man_hinh_ngay_sinh(s_dau):
                self.log('✅ Đã chuyển sang màn hình tiếp theo (Giới tính/SĐT/Email) -> Dừng ngay bước Ngày sinh!')
                return 'MOVED'

            # Nếu đang ở ngoài trang Ngày sinh và tuổi đã hợp lệ (>= 18) -> đi thẳng xuống bấm 'Tiếp', không mở lại bảng chọn ngày!
            if not self._dang_hien_bang_chon_ngay(snap=s_dau) and self._kiem_tra_tuoi_hop_le_ngoai_man_hinh(snap=s_dau):
                self.log('✅ Ngày tháng năm sinh trên màn hình đã hợp lệ (>= 18 tuổi) -> Bấm Tiếp luôn!')
                break

            if not self.mo_bang_chon_ngay():
                s_fail = self.quet_snapshot()
                if self._da_roi_man_hinh_ngay_sinh(s_fail):
                    self.log('✅ Màn hình đã chuyển sang trang Giới tính -> Dừng ngay bước Ngày sinh!')
                    return 'MOVED'
                if self._kiem_tra_tuoi_hop_le_ngoai_man_hinh(snap=s_fail):
                    break
                if not self._la_man_hinh_ngay_sinh(s_fail):
                    return 'MOVED'
                self.log('⚠️ Chưa mở được bảng Chọn ngày 3 cột -> Không vuốt mù, thử kiểm tra lại...')
                time.sleep(0.8)
                continue

            # Xác nhận LẦN CUỐI bảng 3 cột thực sự đang mở trước khi vuốt
            s_picker = self.quet_snapshot()
            if self._da_roi_man_hinh_ngay_sinh(s_picker):
                return 'MOVED'
            if not self._dang_hien_bang_chon_ngay(snap=s_picker):
                continue

            x_day = int(w * 0.295)
            x_month = int(w * 0.500)
            x_year = int(w * 0.705)
            y_top = int(h * 0.405)
            y_bot = int(h * 0.575)

            pickers = self.d(className='android.widget.NumberPicker')
            if pickers.count >= 3:
                try:
                    ds_bounds = [pickers[i].info['bounds'] for i in range(pickers.count)]
                    ds_bounds.sort(key=lambda b: b['left'])
                    b_day, b_month, b_year = ds_bounds[0], ds_bounds[1], ds_bounds[2]

                    x_day = (b_day['left'] + b_day['right']) // 2
                    x_month = (b_month['left'] + b_month['right']) // 2
                    x_year = (b_year['left'] + b_year['right']) // 2
                    y_top = b_year['top'] + int((b_year['bottom'] - b_year['top']) * 0.18)
                    y_bot = b_year['top'] + int((b_year['bottom'] - b_year['top']) * 0.82)
                except Exception:
                    pass

            self.log('📅 Đang vuốt chọn Cột 1 (Ngày) & Cột 2 (Tháng)...')
            for _ in range(random.randint(2, 4)):
                if random.choice([True, False]):
                    self.vuot_toa_do_an_toan(x_day, y_top, x_day, y_bot, 180)
                else:
                    self.vuot_toa_do_an_toan(x_day, y_bot, x_day, y_top, 180)
                time.sleep(0.25)

            for _ in range(random.randint(2, 4)):
                if random.choice([True, False]):
                    self.vuot_toa_do_an_toan(x_month, y_top, x_month, y_bot, 180)
                else:
                    self.vuot_toa_do_an_toan(x_month, y_bot, x_month, y_top, 180)
                time.sleep(0.25)

            nam_muc_tieu = random.randint(1994, 2004)
            self.log(f'📅 Đang cuộn Cột 3 (Năm) lùi về khoảng {nam_muc_tieu}...')
            for nhip in range(14):
                self.vuot_toa_do_an_toan(x_year, y_top, x_year, y_bot, 130)
                time.sleep(0.28)
                if nhip >= 4:
                    nam_hien_tai = self._lay_nam_hien_tai_trong_bang_3_cot()
                    if nam_hien_tai and 1985 <= nam_hien_tai <= 2005:
                        self.log(f'✅ Đã cuộn Cột 3 tới năm: {nam_hien_tai}')
                        break

            time.sleep(0.45)
            s_btn_pick = self.quet_snapshot()
            if self._da_roi_man_hinh_ngay_sinh(s_btn_pick):
                return 'MOVED'

            self.log('📅 Bấm nút CHỌN trên bảng Chọn ngày')
            da_bam_chon = (
                self._snap_click(s_btn_pick, ['CHỌN', 'Chọn', 'SET', 'Set', 'OK'], exact=True, click_duoi=True)
                or self.click_text('CHỌN', 'CHỌN', 1, 0.4)
                or self.click_text('OK', 'OK', 1, 0.3)
            )
            if not da_bam_chon and self._dang_hien_bang_chon_ngay(snap=s_btn_pick):
                self.click_toa_do_an_toan(int(w * 0.72), int(h * 0.633))
            time.sleep(0.9)

            s_sau_chon = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Sau khi bấm CHỌN ngày sinh')
            if self._da_roi_man_hinh_ngay_sinh(s_sau_chon):
                self.log('✅ Đã tự chuyển sang trang Giới tính sau khi bấm CHỌN!')
                return 'MOVED'

            if self._kiem_tra_tuoi_hop_le_ngoai_man_hinh(snap=s_sau_chon):
                self.log('✅ Ngày tháng năm sinh đã hợp lệ (>= 18 tuổi)!')
                break
            self.log('⚠️ Năm sinh chưa lùi đủ 18 tuổi, mở lại bảng Chọn ngày để cuộn thêm...')

        # CHỐT AN TOÀN TRƯỚC KHI BẤM TIẾP: Nếu đã sang trang Giới tính -> TUYỆT ĐỐI KHÔNG bấm Tiếp ở đây!
        s_pre_next = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Trước khi bấm Tiếp Ngày sinh')
        if self._da_roi_man_hinh_ngay_sinh(s_pre_next):
            self.log('✅ Đã ở màn hình tiếp theo -> Không bấm Tiếp của bước Ngày sinh nữa!')
            return 'MOVED'

        if not self._la_man_hinh_ngay_sinh(s_pre_next):
            return 'MOVED'

        self.log('⏩ Bấm nút Tiếp (sau khi chọn xong Ngày tháng năm sinh) & chờ rời hẳn trang Ngày sinh...')
        prev_sig_ns = s_pre_next['sig']
        da_bam_tiep_ns = (
            self._snap_click(s_pre_next, ['Tiếp', 'Next'], exact=True)
            or self._snap_click(s_pre_next, ['Tiếp', 'Next'], exact=False)
        )
        if not da_bam_tiep_ns:
            self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.388))

        # ĐỢI THỰC SỰ RỜI KHỎI TRANG NGÀY SINH (tối đa 10s, thoát tức thì ngay khi sang trang Giới tính!)
        s_after_next = self._cho_chuyen_man_hinh(
            prev_sig_ns,
            timeout=10.0,
            old_screen_keywords=['Ngày sinh của bạn là khi nào', "What's your birthday", 'What’s your birthday']
        )

        # Nếu hiện hộp thoại phụ xác nhận tuổi ("Bạn có chắc..." -> OK / Xác nhận) thì bấm và đợi chuyển trang tiếp
        if self._snap_has(s_after_next, ['bạn có chắc', 'xác nhận tuổi', 'confirm your age']) and self._snap_has(s_after_next, ['OK', 'Xác nhận'], exact=True):
            self._snap_click(s_after_next, ['OK', 'Xác nhận'], exact=True)
            self._cho_chuyen_man_hinh(
                s_after_next['sig'],
                timeout=8.0,
                old_screen_keywords=['bạn có chắc', 'xác nhận tuổi', 'Ngày sinh của bạn là khi nào', "What's your birthday"]
            )
        return 'DONE' 

    def _tao_ban_sao_anh_sach_exif(self, src_path):
        """
        Tạo file ảnh tạm đã xóa sạch EXIF (DateTaken cũ) trên PC để khi đẩy vào điện thoại,
        Android MediaStore luôn coi đây là bức ảnh mới chụp nhất (đứng đầu Thư viện).
        """
        temp_clean_path = os.path.join(
            tempfile.gettempdir(),
            f"fb_clean_avt_{self.serial or 'dev'}_{int(time.time() * 1000)}.jpg"
        )
        if HAS_PIL:
            try:
                with PILImage.open(src_path) as img:
                    rgb_img = img.convert('RGB')
                    rgb_img.save(temp_clean_path, format='JPEG', quality=95)
                return temp_clean_path
            except Exception:
                pass

        try:
            with open(src_path, 'rb') as f_in:
                raw_bytes = f_in.read()
            if len(raw_bytes) > 20 and raw_bytes[0:2] == b'\xff\xd8' and raw_bytes[2:4] == b'\xff\xe1':
                exif_len = struct.unpack('>H', raw_bytes[4:6])[0]
                raw_bytes = b'\xff\xd8' + raw_bytes[4 + exif_len:]
            with open(temp_clean_path, 'wb') as f_out:
                f_out.write(raw_bytes)
            return temp_clean_path
        except Exception:
            return src_path

    def _lay_dung_luong_file_tren_dt(self, remote_path):
        """Kiểm tra file có thực sự tồn tại trên điện thoại và lấy dung lượng (bytes) > 0."""
        ok_sz, out_sz = chay_lenh_adb_list(
            ['shell', f'stat -c %s "{remote_path}" 2>/dev/null || wc -c < "{remote_path}" 2>/dev/null'],
            self.serial,
            timeout=8
        )
        if ok_sz and out_sz:
            m_sz = re.search(r'\b(\d+)\b', out_sz.strip())
            if m_sz:
                return int(m_sz.group(1))
        return 0

    def _kiem_tra_anh_trong_mediastore(self, filename, uid=0):
        """
        Kiểm tra file đã xuất hiện trong MediaStore với dung lượng > 0 (dùng đúng cú pháp 1 chuỗi Android shell,
        KHÔNG bị Android /bin/sh cắt mất dấu nháy quanh --where).
        Trả về (co_trong_ms: bool, ms_size: int).
        """
        uf = f"--user {int(uid)} " if uid and int(uid) > 0 else ""
        sh_q = (
            f'content query {uf}--uri content://media/external/images/media '
            f'--projection _id:_display_name:_size '
            f"--where \"_display_name='{filename}'\""
        )
        ok_q, out_q = chay_lenh_adb_list(['shell', sh_q], self.serial, timeout=8)
        if not ok_q or not out_q or filename not in out_q:
            return False, 0
        m_s = re.search(r'_size=(\d+)', out_q)
        sz = int(m_s.group(1)) if m_s else -1
        return True, sz

    def _lay_moc_thoi_gian_anh_moi_nhat_tren_may(self, uid=0):
        """
        Đọc đồng hồ điện thoại + mốc thời gian lớn nhất (datetaken / date_added / date_modified) của ảnh hiện có
        trong MediaStore (đóng ngoặc chuẩn Android shell cho --sort) để ảnh mới LUÔN đứng #1 đầu Thư viện.
        """
        uf = f"--user {int(uid)} " if uid and int(uid) > 0 else ""
        ok_t, out_t = chay_lenh_adb_list(['shell', 'date +%s'], self.serial, timeout=6)
        now_sec = int(out_t.strip()) if (ok_t and out_t.strip().isdigit()) else int(time.time())
        max_sec = now_sec
        max_ms = now_sec * 1000

        for sort_col in ['datetaken DESC', 'date_added DESC', 'date_modified DESC']:
            sh_q = (
                f'content query {uf}--uri content://media/external/images/media '
                f'--projection datetaken:date_added:date_modified '
                f'--sort "{sort_col}"'
            )
            ok_q, out_q = chay_lenh_adb_list(['shell', sh_q], self.serial, timeout=8)
            if not ok_q or not out_q:
                continue
            for line in out_q.splitlines()[:3]:
                for k_ms in re.findall(r'datetaken=(\d+)', line):
                    v = int(k_ms)
                    # Bỏ qua giá trị rác vượt quá 5 năm tương lai
                    if 1000000000000 <= v <= (now_sec + 157680000) * 1000:
                        max_ms = max(max_ms, v)
                        max_sec = max(max_sec, v // 1000)
                for k_s in re.findall(r'(?:date_added|date_modified)=(\d+)', line):
                    v = int(k_s)
                    if 1000000000 <= v <= (now_sec + 157680000):
                        max_sec = max(max_sec, v)
                        max_ms = max(max_ms, v * 1000)

        target_sec = max_sec + 15
        target_ms = max(max_ms + 15000, target_sec * 1000)
        return target_sec, target_ms

    def day_anh_qua_adb(self):
        """
        Đẩy ảnh từ PC sang điện thoại và ÉP ĐỨNG VỊ TRÍ #1 ĐẦU THƯ VIỆN 100% (khắc phục hoàn toàn lỗi Windows cmd.exe & Android sh quoting):
        - Dùng 100% `chay_lenh_adb_list(['shell', sh_cmd])` để KHÔNG BAO GIỜ bị Windows cmd.exe làm vỡ dấu ngoặc kép
          và KHÔNG BAO GIỜ bị Android /bin/sh cắt sai --where / --sort.
        - Xác minh dung lượng file thực tế trên máy > 0 bytes; nếu DCIM/Camera bị chặn sẽ tự chuyển sang Pictures/.
        - Chạy đủ bộ quét MediaStore (`scan_file` -> `MEDIA_SCANNER_SCAN_FILE` -> `scan_volume`) và kiểm tra `_size > 0`.
        - Fallback `content insert` + `content write` an toàn: TUYỆT ĐỐI KHÔNG xóa file đã đẩy hợp lệ trước khi ghi mới thành công!
        """
        folder_pc = self.avatar_folder.strip() if self.avatar_folder else DEFAULT_AVATAR_DIR
        if not os.path.isabs(folder_pc):
            folder_pc = os.path.join(BASE_DIR, folder_pc)

        if not os.path.isdir(folder_pc):
            try:
                os.makedirs(folder_pc, exist_ok=True)
            except Exception:
                pass
            self.log(f'⚠️ Chưa có thư mục ảnh trên PC: {folder_pc}')
            return None

        images = [f for f in os.listdir(folder_pc) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not images:
            self.log(f'⚠️ Thư mục "{folder_pc}" trên máy tính đang trống! Hãy bỏ ảnh .jpg/.png vào đó.')
            return None

        chosen_img = random.choice(images)
        local_path = os.path.abspath(os.path.join(folder_pc, chosen_img))
        clean_local_path = self._tao_ban_sao_anh_sach_exif(local_path)

        remote_filename = f"FB_AVT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}.jpg"
        uid = self.user_id
        uf = self._u_flag()
        base_emulated = f"/storage/emulated/{uid}" if uid > 0 else "/storage/emulated/0"
        rm_root = base_emulated if uid > 0 else "/sdcard"

        try:
            self.log(f'💻 [Chuẩn bị Avatar #1] Truyền ảnh PC: {chosen_img} -> {remote_filename} (User {uid})...')

            # 1. Xóa sạch ảnh tạm `FB_AVT_*` cũ ở cả MediaStore lẫn ổ đĩa (đúng cú pháp Android shell, không đụng ảnh người dùng!)
            chay_lenh_adb_list(
                ['shell', f"content delete {uf}--uri content://media/external/images/media --where \"_display_name LIKE 'FB_AVT_%'\""],
                self.serial,
                timeout=10
            )
            chay_lenh_adb_list(
                ['shell', f'mkdir -p "{rm_root}/DCIM/Camera" "{rm_root}/Pictures"; rm -f "{rm_root}/DCIM/Camera"/FB_AVT_* "{rm_root}/Pictures"/FB_AVT_*'],
                self.serial,
                timeout=10
            )

            target_sec, target_ms = self._lay_moc_thoi_gian_anh_moi_nhat_tren_may(uid=uid)

            # 2. Đẩy file bằng `adb push` (ưu tiên DCIM/Camera, dự phòng Pictures) & XÁC MINH dung lượng thực tế trên điện thoại > 0!
            cac_dich_thu = [
                (f"{rm_root}/DCIM/Camera/{remote_filename}", f"{base_emulated}/DCIM/Camera/{remote_filename}", "DCIM/Camera/"),
                (f"{rm_root}/Pictures/{remote_filename}", f"{base_emulated}/Pictures/{remote_filename}", "Pictures/"),
            ]
            remote_path_ok = None
            real_path_ok = None
            rel_dir_ok = "DCIM/Camera/"
            file_bytes = 0
            last_push_err = ""

            for cand_remote, cand_real, cand_rel in cac_dich_thu:
                ok_p, out_p = chay_lenh_adb_list(['push', clean_local_path, cand_remote], self.serial, timeout=25)
                if not ok_p:
                    last_push_err = out_p
                    try:
                        self.d.push(clean_local_path, cand_remote)
                    except Exception as e_u2p:
                        last_push_err = str(e_u2p)
                sz_chk = self._lay_dung_luong_file_tren_dt(cand_remote)
                if sz_chk <= 0 and cand_real != cand_remote:
                    sz_chk = self._lay_dung_luong_file_tren_dt(cand_real)
                if sz_chk > 0:
                    remote_path_ok = cand_remote
                    real_path_ok = cand_real
                    rel_dir_ok = cand_rel
                    file_bytes = sz_chk
                    break

            active_filename = remote_filename
            da_co_trong_mediastore = False
            phuong_thuc_ms = "PushOnly"

            # 3. Quét MediaStore chuẩn (KHÔNG dùng cmd.exe -> KHÔNG bao giờ vỡ dấu ngoặc kép!)
            if file_bytes > 0 and remote_path_ok:
                scan_sh = (
                    f'chmod 644 "{remote_path_ok}" 2>/dev/null; '
                    f'touch -d @{target_sec} "{remote_path_ok}" 2>/dev/null || touch "{remote_path_ok}" 2>/dev/null; '
                    f'content call {uf}--uri content://media --method scan_file --arg "{real_path_ok}"; '
                    f'am broadcast {uf}-a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{real_path_ok}"'
                )
                chay_lenh_adb_list(['shell', scan_sh], self.serial, timeout=15)

                for _ in range(3):
                    time.sleep(0.7)
                    co_ms, sz_ms = self._kiem_tra_anh_trong_mediastore(remote_filename, uid=uid)
                    if co_ms and (sz_ms > 0 or sz_ms == -1):
                        da_co_trong_mediastore = True
                        phuong_thuc_ms = "ScanFile"
                        break

                # Nếu scan_file chưa kịp index -> kích hoạt thêm scan_volume toàn bộ external_primary (Android 11-15)
                if not da_co_trong_mediastore:
                    chay_lenh_adb_list(
                        ['shell', f'content call {uf}--uri content://media --method scan_volume --arg external_primary'],
                        self.serial,
                        timeout=15
                    )
                    time.sleep(1.2)
                    co_ms2, sz_ms2 = self._kiem_tra_anh_trong_mediastore(remote_filename, uid=uid)
                    if co_ms2 and (sz_ms2 > 0 or sz_ms2 == -1):
                        da_co_trong_mediastore = True
                        phuong_thuc_ms = "ScanVolume"

            # 4. Fallback AN TOÀN (chỉ chạy nếu MediaStore vẫn chưa nhận): chèn qua `content insert` + `content write`
            #    TUYỆT ĐỐI KHÔNG xóa file đã đẩy hợp lệ ở bước 2 trước khi xác minh bản mới ghi đủ byte > 0!
            if not da_co_trong_mediastore:
                ms_filename = remote_filename.replace("FB_AVT_", "FB_AVT_MS_") if file_bytes > 0 else remote_filename
                tmp_remote = f"/data/local/tmp/{ms_filename}"
                ok_tmp, _ = chay_lenh_adb_list(['push', clean_local_path, tmp_remote], self.serial, timeout=20)
                if ok_tmp and self._lay_dung_luong_file_tren_dt(tmp_remote) > 0:
                    ins_sh = (
                        f'content insert {uf}--uri content://media/external/images/media '
                        f'--bind _display_name:s:{ms_filename} '
                        f'--bind mime_type:s:image/jpeg '
                        f'--bind relative_path:s:{rel_dir_ok} '
                        f'--bind datetaken:l:{target_ms} '
                        f'--bind date_added:l:{target_sec} '
                        f'--bind date_modified:l:{target_sec}'
                    )
                    ok_ins, out_ins = chay_lenh_adb_list(['shell', ins_sh], self.serial, timeout=15)
                    m_uri = re.search(r'(content://media/[^\s]+)', out_ins or '')
                    if ok_ins and m_uri:
                        media_uri = m_uri.group(1).strip()
                        ok_wr, _ = chay_lenh_adb_list(['shell', f'content write {uf}--uri "{media_uri}" < "{tmp_remote}"'], self.serial, timeout=20)
                        time.sleep(0.5)
                        co_ms_w, sz_ms_w = self._kiem_tra_anh_trong_mediastore(ms_filename, uid=uid)
                        if ok_wr and co_ms_w and sz_ms_w > 0:
                            # Ghi MediaStore mới thành công > 0 byte -> lúc này mới xóa file chưa index cũ để không trùng
                            if remote_path_ok:
                                chay_lenh_adb_list(['shell', f'rm -f "{remote_path_ok}"'], self.serial, timeout=8)
                            active_filename = ms_filename
                            remote_path_ok = f"{rm_root}/{rel_dir_ok}{ms_filename}"
                            real_path_ok = f"{base_emulated}/{rel_dir_ok}{ms_filename}"
                            file_bytes = sz_ms_w
                            da_co_trong_mediastore = True
                            phuong_thuc_ms = "ContentWrite"
                        else:
                            # Nếu ghi thất bại / 0 byte -> XÓA NGAY dòng rác 0-byte để không tạo ô ảnh xám lỗi trong Thư viện!
                            chay_lenh_adb_list(['shell', f'content delete {uf}--uri "{media_uri}"'], self.serial, timeout=8)
                    chay_lenh_adb_list(['shell', f'rm -f "{tmp_remote}"'], self.serial, timeout=8)

            # Xóa file tạm trên PC
            if clean_local_path != local_path and os.path.exists(clean_local_path):
                try:
                    os.remove(clean_local_path)
                except Exception:
                    pass

            if file_bytes <= 0 or not remote_path_ok:
                self.log(f'❌ Không thể truyền ảnh từ PC sang điện thoại (0 byte)! ({str(last_push_err)[:80]})')
                return None

            # 5. Ép cập nhật `datetaken` / `date_added` / `date_modified` cao nhất trong MediaStore (đúng cú pháp Android shell) -> ĐỨNG #1 TUYỆT ĐỐI!
            upd_sh = (
                f'content update {uf}--uri content://media/external/images/media '
                f'--bind datetaken:l:{target_ms} '
                f'--bind date_added:l:{target_sec} '
                f'--bind date_modified:l:{target_sec} '
                f"--where \"_display_name='{active_filename}'\""
            )
            chay_lenh_adb_list(['shell', upd_sh], self.serial, timeout=10)
            time.sleep(0.35)
            kb_size = max(1, file_bytes // 1024)
            self.log(
                f'✅ Đã nạp ảnh {active_filename} ({kb_size} KB) lên ĐẦU Thư viện '
                f'(vị trí #1 | {rel_dir_ok} | MediaStore={phuong_thuc_ms if da_co_trong_mediastore else "DiskOnly"})!'
            )
            return [remote_path_ok, real_path_ok, active_filename]
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            self.log(f'⚠️ Lỗi truyền ảnh: {str(e)[:60]}')
            return None

    def xoa_anh_tam_tren_dt(self, remote_paths):
        """Xóa sạch ảnh tạm `FB_AVT_*` vừa đẩy từ PC ở cả MediaStore lẫn ổ đĩa (đúng cú pháp Android shell, không chạm ảnh người dùng)."""
        if not remote_paths:
            return
        try:
            uid = self.user_id
            uf = self._u_flag()
            base_emulated = f"/storage/emulated/{uid}" if uid > 0 else "/storage/emulated/0"
            rm_root = base_emulated if uid > 0 else "/sdcard"
            chay_lenh_adb_list(
                ['shell', f"content delete {uf}--uri content://media/external/images/media --where \"_display_name LIKE 'FB_AVT_%'\""],
                self.serial,
                timeout=10
            )
            chay_lenh_adb_list(
                ['shell', f'rm -f "{rm_root}/DCIM/Camera"/FB_AVT_* "{rm_root}/Pictures"/FB_AVT_*'],
                self.serial,
                timeout=10
            )
        except Exception:
            pass

    def _dang_o_man_hinh_them_anh_2_nut(self):
        """Kiểm tra có đang đứng ở màn hình gồm dòng trên 'Thêm ảnh' và dòng dưới 'Bỏ qua' hay không."""
        co_them_anh = self.kiem_tra_text(
            ['Thêm ảnh đại diện', 'Thêm ảnh', 'THÊM ẢNH', 'Add profile picture', 'Add picture', 'Add photo'], 1, 0.1
        )
        co_bo_qua = (
            self.d(text='Bỏ qua').exists
            or self.d(description='Bỏ qua').exists
            or self.d(text='BỎ QUA').exists
            or self.d(description='BỎ QUA').exists
            or self.d(text='Skip').exists
            or self.d(description='Skip').exists
            or self.d(text='SKIP').exists
        )
        return co_them_anh and co_bo_qua

    def _lay_bounds_nut_bo_qua(self):
        """Lấy tọa độ khung của nút 'Bỏ qua' / 'Skip' ở dưới màn hình để khóa vùng an toàn, tránh bấm trúng."""
        w, h = self.d.window_size()
        ket_qua = None
        for sel in [
            self.d(text='Bỏ qua'),
            self.d(description='Bỏ qua'),
            self.d(text='BỎ QUA'),
            self.d(description='BỎ QUA'),
            self.d(text='Skip'),
            self.d(description='Skip'),
            self.d(text='SKIP'),
        ]:
            if sel.exists:
                for i in range(sel.count - 1, -1, -1):
                    try:
                        b = sel[i].info['bounds']
                        cy = (b['top'] + b['bottom']) // 2
                        if cy > int(h * 0.30):
                            if ket_qua is None or cy > ((ket_qua['top'] + ket_qua['bottom']) // 2):
                                ket_qua = b
                    except Exception:
                        pass
        return ket_qua

    def _tim_va_bam_nut_them_anh(self):
        """
        Tìm và bấm chính xác nút 'Thêm ảnh' (dòng trên), loại trừ tiêu đề ở đầu trang
        và khóa vùng an toàn hoàn toàn phía trên nút 'Bỏ qua' (dòng dưới) — KHÔNG dùng tọa độ cứng.
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        b_skip = self._lay_bounds_nut_bo_qua()
        gioi_han_duoi = (b_skip['top'] - 6) if b_skip else int(h * 0.89)
        gioi_han_tren = int(h * 0.25)

        ung_vien = []
        danh_sach_exact = [
            'Thêm ảnh', 'THÊM ẢNH', 'Add picture', 'Add photo', 'ADD PICTURE', 'ADD PHOTO',
            'Thêm ảnh đại diện', 'Add profile picture', 'Thêm', 'THÊM', 'Add'
        ]
        danh_sach_contains = ['Thêm ảnh', 'THÊM ẢNH', 'Add picture', 'Add photo']

        # Ưu tiên 1: Khớp chính xác text/description nằm ở dưới tiêu đề và phía trên nút Bỏ qua
        for tu_khoa in danh_sach_exact:
            for sel in [self.d(text=tu_khoa), self.d(description=tu_khoa)]:
                if sel.exists:
                    for i in range(sel.count):
                        try:
                            b = sel[i].info['bounds']
                            cx = (b['left'] + b['right']) // 2
                            cy = (b['top'] + b['bottom']) // 2
                            if gioi_han_tren <= cy <= gioi_han_duoi and cx > 0:
                                diem_uu_tien = 2 if tu_khoa.lower() in ['thêm ảnh', 'add picture', 'add photo'] else 1
                                ung_vien.append((diem_uu_tien, cy, cx))
                        except Exception:
                            pass

        # Ưu tiên 2: Khớp chứa chuỗi nằm phía trên nút Bỏ qua
        if not ung_vien:
            for tu_khoa in danh_sach_contains:
                for sel in [self.d(textContains=tu_khoa), self.d(descriptionContains=tu_khoa)]:
                    if sel.exists:
                        for i in range(sel.count):
                            try:
                                b = sel[i].info['bounds']
                                cx = (b['left'] + b['right']) // 2
                                cy = (b['top'] + b['bottom']) // 2
                                if gioi_han_tren <= cy <= gioi_han_duoi and cx > 0:
                                    ung_vien.append((1, cy, cx))
                            except Exception:
                                pass

        # Ưu tiên 3: Quét XML trực tiếp (không phân biệt hoa/thường) đề phòng layout lồng ViewGroup
        if not ung_vien:
            try:
                xml_dump = self.d.dump_hierarchy()
                for m in re.finditer(
                    r'(?:text|content-desc)="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                    xml_dump
                ):
                    label = html.unescape(m.group(1)).strip().lower()
                    if any(kw in label for kw in ['thêm ảnh', 'add picture', 'add photo']) and 'bỏ qua' not in label:
                        l, t, r, bot = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
                        cx = (l + r) // 2
                        cy = (t + bot) // 2
                        if gioi_han_tren <= cy <= gioi_han_duoi and cx > 0:
                            diem_uu_tien = 2 if label in ['thêm ảnh', 'add picture', 'add photo'] else 1
                            ung_vien.append((diem_uu_tien, cy, cx))
            except Exception:
                pass

        if ung_vien:
            ung_vien.sort(key=lambda item: (item[0], item[1]), reverse=True)
            _, cy, cx = ung_vien[0]
            self.log(f'🎯 Bấm đúng nút "Thêm ảnh" tại ({cx}, {cy}) [khóa trên Bỏ qua: y < {gioi_han_duoi}]')
            self.click_toa_do_an_toan(cx, cy)
            return True

        # Dự phòng theo mốc nút 'Bỏ qua' (tính động theo nút Bỏ qua thực tế trên màn hình)
        if b_skip:
            skip_h = max(b_skip['bottom'] - b_skip['top'], int(h * 0.045))
            cx = (b_skip['left'] + b_skip['right']) // 2
            cy = b_skip['top'] - int(skip_h * 0.85)
            if cy > gioi_han_tren:
                self.log(f'🎯 Bấm dòng trên "Thêm ảnh" theo mốc nút Bỏ qua tại ({cx}, {cy})')
                self.click_toa_do_an_toan(cx, cy)
                return True

        return False

    def _xu_ly_tat_ca_hop_thoai_quyen_anh(self, snap=None):
        """
        Xử lý hộp thoại cấp quyền thư viện ảnh & menu chọn nguồn ảnh từ snapshot (0% tọa độ cố định):
        1. Ưu tiên cao nhất: Quyền Android 13/14/15 ('Cho phép tất cả' / 'Allow all' / permission_allow_all_button)
           để Facebook thấy toàn bộ ảnh vừa đẩy trong DCIM/Camera (không bị giới hạn ảnh).
        2. Hộp thoại trắng Facebook ('Cho phép') hoặc nút chấp nhận quyền hệ thống.
        3. Menu dưới đáy ('Chọn từ thư viện' / 'Choose from gallery').
        4. Nút xanh 'Cho phép truy cập' / 'Allow access'.
        """
        s = snap if snap is not None else self.quet_snapshot()
        if s['is_blank_or_loading']:
            return False

        # ƯU TIÊN 1: Android 13/14/15 -> Luôn chọn 'Cho phép tất cả' / 'Allow all' trước để thấy ảnh mới đẩy!
        btn_allow_all = self._snap_find_rid(s, [
            'com.android.permissioncontroller:id/permission_allow_all_button',
            'com.android.permissioncontroller:id/permission_allow_button',
            'com.android.permissioncontroller:id/permission_allow_foreground_only_button',
            'com.lbe.security.miui:id/permission_allow_button_1'
        ])
        if btn_allow_all:
            self.log(f'🔓 Bấm cấp quyền ảnh hệ thống ("{btn_allow_all["text"] or btn_allow_all["desc"] or "Allow All"}")...')
            self.click_toa_do_an_toan(btn_allow_all['cx'], btn_allow_all['cy'])
            self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
            return True

        if self._snap_click(s, [
            'Cho phép tất cả', 'Cho phép truy cập tất cả', 'Luôn cho phép',
            'Allow all', 'Allow access to all', 'ALLOW ALL',
            'CHO PHÉP', 'ALLOW', 'Allow', 'Trong khi dùng ứng dụng', 'Chỉ lần này'
        ], exact=True):
            self.log('🔓 Bấm cấp quyền truy cập toàn bộ thư viện ảnh...')
            self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
            return True

        # ƯU TIÊN 2: Nút 'Cho phép' trên hộp thoại trắng Facebook hoặc android:id/button1
        if (
            self._snap_has(s, ['Cho phép'], exact=True)
            or self._snap_find_rid(s, ['android:id/button1']) is not None
            or self._snap_has(s, ['Cho phép Facebook truy cập vào', 'Khi đó, bạn có thể chia sẻ từ thư viện', 'sử dụng bộ nhớ điện thoại'])
        ):
            self.log('🔓 Bấm "Cho phép" trên hộp thoại truy cập thư viện ảnh...')
            if not self._snap_click(s, ['Cho phép'], exact=True, click_duoi=True):
                b1 = self._snap_find_rid(s, ['android:id/button1'])
                if b1:
                    self.click_toa_do_an_toan(b1['cx'], b1['cy'])
            self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
            return True

        # ƯU TIÊN 3: Menu chọn nguồn ảnh dưới đáy
        if self._snap_click(s, [
            'Chọn từ thư viện', 'Chọn từ Thư viện', 'Chọn từ cuộn camera', 'Chọn ảnh',
            'Choose from gallery', 'Choose from Gallery', 'Choose from Library', 'Choose from camera roll'
        ], exact=False):
            self.log('🖼️ Bấm "Chọn từ thư viện"...')
            self._cho_chuyen_man_hinh(s['sig'], timeout=2.5)
            return True

        # ƯU TIÊN 4: Nút xanh 'Cho phép truy cập' (exact=True phía dưới, tránh tiêu đề đầu trang)
        if not self._snap_has(s, ['Từ chối'], exact=True) and (
            self._snap_has(s, ['Cho phép truy cập', 'Allow access'], exact=True)
            or self._snap_has(s, ['Cho phép truy cập vào thư viện ảnh'])
        ):
            self.log('🔓 Bấm nút xanh "Cho phép truy cập"...')
            self._snap_click(s, ['Cho phép truy cập', 'Allow access'], exact=True, click_duoi=True) or self._snap_click(s, ['Cho phép truy cập', 'Allow access'], exact=False, click_duoi=True, min_y=0.48)
            self._cho_chuyen_man_hinh(s['sig'], timeout=2.8)
            return True

        return False

    def _tim_o_anh_dau_tien_trong_thu_vien(self, snap):
        """
        Quét XML ĐỘNG (0% tọa độ cố định) để tìm CHÍNH XÁC ô ảnh ĐẦU TIÊN (vị trí #1, hàng trên cùng bên trái)
        trong mọi loại Thư viện (Thư viện Facebook, Android 13/14/15 Photo Picker bottom-sheet, MIUI Gallery, DocumentsUI):
        - Chỉ loại trừ ô nào BẢN THÂN Ô ĐÓ là ô Máy ảnh / Camera hoặc Video (tuyệt đối KHÔNG bị đánh lừa bởi chữ 'Camera' trên tiêu đề album!).
        - Tự lọc bỏ khung cha bọc nhiều ô (RecyclerView/GridView) để lấy đúng ô ảnh con đầu tiên.
        - Trả về danh sách các ô ảnh đã sắp xếp theo đúng thứ tự (hàng trên -> dưới, trái -> phải), phần tử [0] LUÔN là ảnh #1.
        """
        if not snap or not snap.get('nodes'):
            return []

        w, h = snap['w'], snap['h']
        min_tile = int(w * 0.14)
        max_tile_w = int(w * 0.56)
        max_tile_h = int(h * 0.42)

        tu_cam_trong_o = [
            'máy ảnh', 'camera', 'chụp ảnh', 'take photo', 'take a photo', 'quay video', 'record',
            'video', 'bỏ qua', 'skip', 'thêm ảnh', 'add photo', 'add picture',
            'chọn từ thư viện', 'choose from gallery', 'cho phép', 'allow', 'từ chối', 'deny',
            'hủy', 'cancel', 'lưu', 'save', 'xong', 'done', 'tiếp', 'next',
            'đóng', 'close', 'album', 'albums', 'thư viện', 'gallery', 'tất cả ảnh', 'ảnh gần đây',
            'recent', 'chọn nhiều', 'select multiple', 'tìm kiếm', 'search', 'cài đặt', 'settings'
        ]
        tu_mo_ta_anh = ['ảnh', 'photo', 'image', 'hình ảnh', 'chụp vào', 'taken on', 'fb_avt', 'picture']
        rid_o_anh = ['thumb', 'photo', 'media', 'image', 'picker', 'grid', 'gallery', 'item_root', 'icon_mime']
        lop_khung_lon = ('RecyclerView', 'GridView', 'ScrollView', 'ListView', 'ViewPager')
        re_thoi_luong_video = re.compile(r'^\d{1,2}:\d{2}(?::\d{2})?$')

        # Thu thập tất cả nhãn text/desc trên màn hình để kiểm tra xem bên trong 1 ô có chữ Camera / Thời lượng video không
        text_nodes = [
            n for n in snap['nodes']
            if (n['text_low'] or n['desc_low'])
        ]

        def _o_bi_loai_tru(node):
            rid_l = (node.get('rid') or '').lower()
            if any(k in rid_l for k in ['camera', 'video_duration', 'close', 'back', 'cancel', 'skip']):
                return True
            comb = f"{node['text_low']} {node['desc_low']}".strip()
            if comb:
                if re_thoi_luong_video.match(node['text_low']):
                    return True
                for bad in tu_cam_trong_o:
                    if bad == comb or (bad in comb and bad not in ['ảnh', 'photo', 'image', 'picture']):
                        # Riêng từ 'chụp vào' / 'ảnh chụp vào' là mô tả ảnh hợp lệ, không phải nút chụp ảnh!
                        if bad == 'camera' and 'camera' in comb:
                            return True
                        if bad != 'camera':
                            return True
            # Kiểm tra các node chữ nằm gọn bên trong khung ô này (VD: ô Camera có icon + chữ 'Máy ảnh', hoặc ô Video có '0:15')
            for tn in text_nodes:
                if tn is node:
                    continue
                if tn['l'] >= node['l'] - 4 and tn['r'] <= node['r'] + 4 and tn['t'] >= node['t'] - 4 and tn['b'] <= node['b'] + 4:
                    t_comb = f"{tn['text_low']} {tn['desc_low']}".strip()
                    if re_thoi_luong_video.match(tn['text_low']):
                        return True
                    if any(k in t_comb for k in ['máy ảnh', 'camera', 'chụp ảnh', 'take photo', 'video']):
                        return True
            return False

        raw_candidates = []
        for n in snap['nodes']:
            cls = n.get('cls') or ''
            if any(bad_cls in cls for bad_cls in lop_khung_lon):
                continue
            bw, bh = n['bw'], n['bh']
            if not (min_tile <= bw <= max_tile_w and min_tile <= bh <= max_tile_h):
                continue
            ratio = bw / float(bh)
            if not (0.45 <= ratio <= 2.2):
                continue
            if n['t'] < int(h * 0.09) or n['b'] > int(h * 0.95):
                continue
            if _o_bi_loai_tru(n):
                continue

            rid_l = (n.get('rid') or '').lower()
            comb = f"{n['text_low']} {n['desc_low']}".strip()
            la_mo_ta_anh = any(k in comb for k in tu_mo_ta_anh) and not any(b in comb for b in ['thêm ảnh', 'tất cả ảnh', 'ảnh gần đây', 'chọn ảnh', 'máy ảnh', 'chụp ảnh'])
            la_rid_anh = any(k in rid_l for k in rid_o_anh)
            la_img_hoac_o_click = ('ImageView' in cls or 'Image' in cls) or (n['clickable'] and ('View' in cls or 'Layout' in cls or 'CheckBox' in cls))

            if not (la_mo_ta_anh or la_rid_anh or la_img_hoac_o_click):
                continue

            tier = 2 if (la_mo_ta_anh or la_rid_anh) else 1
            raw_candidates.append((tier, n))

        if not raw_candidates:
            return []

        # Lọc bỏ các node cha bọc quanh một node ảnh nhỏ hơn bên trong
        filtered = []
        for tier_a, a in raw_candidates:
            boc_con_nho = False
            area_a = a['bw'] * a['bh']
            for _, b in raw_candidates:
                if b is a:
                    continue
                area_b = b['bw'] * b['bh']
                if area_b < area_a * 0.85 and b['l'] >= a['l'] - 6 and b['r'] <= a['r'] + 6 and b['t'] >= a['t'] - 6 and b['b'] <= a['b'] + 6:
                    boc_con_nho = True
                    break
            if not boc_con_nho:
                filtered.append((tier_a, a))

        # Gộp trùng tọa độ tâm (trong phạm vi 28px), ưu tiên node có tier cao hơn / clickable hơn
        dedup = []
        for tier_n, n in sorted(filtered, key=lambda it: (it[0], int(it[1]['clickable']), -(it[1]['bw'] * it[1]['bh'])), reverse=True):
            if any(abs(n['cx'] - x[1]['cx']) <= 28 and abs(n['cy'] - x[1]['cy']) <= 28 for x in dedup):
                continue
            dedup.append((tier_n, n))

        # Ưu tiên cụm tier 2 (ảnh có nhãn/ID rõ ràng) nếu có; nếu không dùng toàn bộ các ô lưới tier 1
        tier2_nodes = [n for t_val, n in dedup if t_val == 2]
        pool = tier2_nodes if tier2_nodes else [n for _, n in dedup]

        # Nếu có nhiều ô, ưu tiên các ô thuộc hàng lưới thực sự (cùng kích thước & nằm trên cùng hàng y với ít nhất 1 ô khác)
        if len(pool) >= 2:
            grid_nodes = []
            for a in pool:
                co_hang_xom = any(
                    (b is not a)
                    and abs(a['t'] - b['t']) <= max(28, int(a['bh'] * 0.25))
                    and abs(a['bw'] - b['bw']) <= max(35, int(a['bw'] * 0.30))
                    for b in pool
                )
                if co_hang_xom:
                    grid_nodes.append(a)
            if grid_nodes:
                pool = grid_nodes

        # Sắp xếp TUYỆT ĐỐI theo thứ tự đọc: Hàng trên cùng trước -> Cột bên trái nhất trước (VỊ TRÍ #1 ĐẦU TIÊN!)
        avg_h = max(40, sum(n['bh'] for n in pool) // len(pool))
        row_step = max(35, avg_h // 2)
        pool.sort(key=lambda n: (n['t'] // row_step, n['l']))
        return pool

    def _la_man_hinh_luu_avatar(self, snap):
        """Kiểm tra đã thực sự vào màn hình Xem trước / Cắt / Lưu ảnh đại diện của Facebook (KHÔNG phải màn 'Thêm ảnh' + 'Bỏ qua')."""
        if not snap or snap.get('is_blank_or_loading'):
            return False
        if self._snap_has(snap, ['Thêm ảnh đại diện', 'Add profile picture']) and self._snap_has(snap, ['Bỏ qua', 'Skip'], exact=True):
            return False
        return self._snap_has(snap, [
            'Lưu', 'Save', 'Áp dụng', 'Apply', 'Chỉnh sửa', 'Edit', 'Cắt', 'Crop',
            'Chia sẻ lên bảng feed', 'Share your update to News Feed', 'Xem trước ảnh đại diện'
        ]) or (
            self._snap_has(snap, ['Xong', 'Done'], exact=True)
            and not self._snap_has(snap, ['Thư viện', 'Gallery', 'Ảnh gần đây', 'Tất cả ảnh', 'Album', 'Albums'])
        )

    def _la_man_hinh_chon_anh_thu_vien(self, snap):
        """Nhận diện đang đứng trong màn hình Thư viện / Android Photo Picker."""
        if not snap or snap.get('is_blank_or_loading'):
            return False
        if self._la_man_hinh_luu_avatar(snap):
            return False
        if any(p in snap['packages'] for p in [
            'com.google.android.providers.media.module',
            'com.android.providers.media.module',
            'com.miui.gallery',
            'com.android.documentsui'
        ]):
            return True
        if self._snap_has(snap, ['Thư viện', 'Gallery', 'Ảnh gần đây', 'Tất cả ảnh', 'Recent', 'Album', 'Albums', 'Chọn ảnh']):
            return True
        if snap.get('has_media_grid') and not (self._snap_has(snap, ['Thêm ảnh đại diện', 'Add profile picture']) and self._snap_has(snap, ['Bỏ qua', 'Skip'], exact=True)):
            return True
        return False

    def up_avatar_fb(self, preloaded_remote_paths=None):
        """
        Xử lý màn hình Thêm ảnh đại diện CHUẨN 100% (0% TỌA ĐỘ CỐ ĐỊNH):
        - Ảnh từ PC đã được nạp sẵn & ép đứng VỊ TRÍ #1 đầu Thư viện ở `day_anh_qua_adb()`.
        - Quét XML động tìm đúng Ô ẢNH ĐẦU TIÊN (hàng 1, cột 1 sau ô Camera nếu có) — tuyệt đối không bấm nhầm ảnh cũ hay làm tụt Photo Picker!
        - Hỗ trợ cả Facebook Gallery chọn 1 chạm lẫn Android 13/14/15 Photo Picker (chọn ảnh #1 -> bấm 'Thêm / Xong' -> bấm 'Lưu').
        - Xác minh thật sự đã chọn & bấm 'Lưu' mới báo thành công (nếu picker bị đóng nhầm sẽ tự mở lại thử lần 2).
        """
        snap_init = self.cho_man_hinh_san_sang(timeout=20.0, ngu_canh='Trước Up Avatar')
        if self.bo_qua_luu_thong_tin_dang_nhap(snap=snap_init):
            snap_init = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Sau đóng Lưu thông tin')

        remote_paths = preloaded_remote_paths
        if not remote_paths:
            self.log('⚠️ Chưa có ảnh nạp sẵn từ PC -> Bỏ qua bước Avatar (không đẩy ảnh giữa chừng để tránh out FB)!')
            self.quet_va_xoa_man_hinh_chan(so_vong_quet=2, snap=snap_init)
            return False

        try:
            # 1. Đợi đúng màn hình "Thêm ảnh đại diện" xuất hiện
            da_thay_man_avatar = False
            snap_cur = snap_init
            deadline_avt = time.time() + 18.0
            while time.time() < deadline_avt and not STOP_EVENT.is_set():
                if snap_cur is None:
                    snap_cur = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Chờ màn hình Thêm ảnh')
                if self.bo_qua_luu_thong_tin_dang_nhap(snap=snap_cur):
                    snap_cur = None
                    continue
                if self._snap_has(snap_cur, ['Thêm ảnh đại diện', 'Thêm ảnh', 'THÊM ẢNH', 'Add profile picture', 'Add picture', 'Add photo']):
                    da_thay_man_avatar = True
                    break
                if self._snap_has(snap_cur, ['Bạn đang nghĩ gì', 'Tạo tin', 'Tìm bạn bè từ danh bạ', 'cấp quyền truy cập vào danh bạ']):
                    break
                if not snap_cur['edit_texts'] and self._snap_has(snap_cur, ['Tiếp', 'Next'], exact=True):
                    self.log('⏩ [Avatar] Bấm nút "Tiếp" chuyển tiếp...')
                    self._snap_click(snap_cur, ['Tiếp', 'Next'], exact=True)
                    self._cho_chuyen_man_hinh(snap_cur['sig'], timeout=2.0)
                    snap_cur = None
                    continue
                time.sleep(0.25)
                snap_cur = None

            if not da_thay_man_avatar:
                self.log('⚠️ Không thấy màn hình Thêm ảnh đại diện -> Thoát bước Avatar.')
                return False

            # Vòng thử tổng thể (tối đa 2 lượt đề phòng lần 1 bị bảng quyền hoặc picker đóng lại)
            for luot_up in range(1, 3):
                if STOP_EVENT.is_set():
                    return False

                # 2. Bấm nút "Thêm ảnh" (dòng trên, khóa trên nút Bỏ qua) để mở Thư viện
                da_mo_chon_anh = False
                snap_sau = None
                for lan_bam in range(1, 4):
                    snap_b1 = snap_cur if (luot_up == 1 and lan_bam == 1 and snap_cur is not None) else self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Trước bấm Thêm ảnh')
                    if self._la_man_hinh_chon_anh_thu_vien(snap_b1) or self._la_man_hinh_luu_avatar(snap_b1):
                        da_mo_chon_anh = True
                        snap_sau = snap_b1
                        break
                    self.log(f'🖼️ [Avatar Lượt {luot_up} - Lần {lan_bam}/3] Bấm nút "Thêm ảnh"...')
                    if not self._tim_va_bam_nut_them_anh():
                        time.sleep(0.5)
                        continue
                    snap_sau = self._cho_chuyen_man_hinh(snap_b1['sig'], timeout=2.5)
                    if snap_sau['is_blank_or_loading']:
                        snap_sau = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Mở chọn ảnh', allow_media_grid=True)

                    if self._xu_ly_tat_ca_hop_thoai_quyen_anh(snap=snap_sau):
                        da_mo_chon_anh = True
                        snap_sau = None
                        break
                    if self._la_man_hinh_chon_anh_thu_vien(snap_sau) or self._la_man_hinh_luu_avatar(snap_sau):
                        da_mo_chon_anh = True
                        break
                    if not (self._snap_has(snap_sau, ['Thêm ảnh đại diện', 'Thêm ảnh', 'Add picture', 'Add photo']) and self._snap_has(snap_sau, ['Bỏ qua', 'Skip'], exact=True)):
                        da_mo_chon_anh = True
                        break

                if not da_mo_chon_anh:
                    self.log('⚠️ Bấm "Thêm ảnh" chưa mở được Thư viện -> Thử lại hoặc thoát.')
                    continue

                # 3. Xử lý hộp thoại cấp quyền ảnh / menu nguồn ảnh cho tới khi Thư viện hiện rõ lưới ảnh
                snap_gal = snap_sau
                for _ in range(12):
                    if snap_gal is None:
                        snap_gal = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Chờ Thư viện ảnh', allow_media_grid=True)
                    if self._la_man_hinh_luu_avatar(snap_gal):
                        break
                    if self._xu_ly_tat_ca_hop_thoai_quyen_anh(snap=snap_gal):
                        snap_gal = None
                        continue
                    if self._snap_has(snap_gal, ['Cho phép truy cập vào thư viện ảnh', 'Cho phép truy cập', 'Allow access']):
                        time.sleep(0.3)
                        snap_gal = None
                        continue
                    if self._la_man_hinh_chon_anh_thu_vien(snap_gal):
                        # Đợi thêm 0.6s cho ảnh #1 vừa đẩy hiện đầy đủ trong lưới trước khi quét XML
                        time.sleep(0.6)
                        snap_gal = self.quet_snapshot()
                        break
                    time.sleep(0.25)
                    snap_gal = None

                if snap_gal is None:
                    snap_gal = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Đọc lưới Thư viện', allow_media_grid=True)

                # 4. Quét XML ĐỘNG chọn CHÍNH XÁC ẢNH ĐẦU TIÊN (#1) — 0% tọa độ cố định!
                snap_save = snap_gal if self._la_man_hinh_luu_avatar(snap_gal) else None
                if snap_save is None:
                    for lan_chon in range(1, 4):
                        if lan_chon > 1:
                            time.sleep(0.7)
                            snap_gal = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh=f'Quét lại lưới ảnh lần {lan_chon}', allow_media_grid=True)
                        if self._la_man_hinh_luu_avatar(snap_gal):
                            snap_save = snap_gal
                            break
                        if self._xu_ly_tat_ca_hop_thoai_quyen_anh(snap=snap_gal):
                            continue
                        ds_o_anh = self._tim_o_anh_dau_tien_trong_thu_vien(snap_gal)
                        if not ds_o_anh:
                            self.log(f'⚠️ [Avatar] Chưa quét thấy ô ảnh trong lưới Thư viện (lần {lan_chon}/3)...')
                            continue

                        o_dau_tien = ds_o_anh[0]
                        self.log(
                            f'🖼️ [Avatar - Quét động] Bấm CHÍNH XÁC ẢNH ĐẦU TIÊN #1 tại ({o_dau_tien["cx"]}, {o_dau_tien["cy"]}) '
                            f'[tìm thấy {len(ds_o_anh)} ô ảnh, không dùng tọa độ cố định]...'
                        )
                        prev_s = snap_gal['sig']
                        self.click_toa_do_an_toan(o_dau_tien['cx'], o_dau_tien['cy'])
                        snap_chk = self._cho_chuyen_man_hinh(prev_s, timeout=2.8)
                        if snap_chk['is_blank_or_loading']:
                            snap_chk = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Sau khi chọn ảnh #1')

                        # Trường hợp Android 13/14/15 Photo Picker chọn tick vào ảnh #1 rồi hiện nút 'Thêm' / 'Thêm (1)' / 'Xong' / 'Chọn'
                        if self._la_man_hinh_chon_anh_thu_vien(snap_chk):
                            nhan_xac_nhan_picker = self._tim_va_bam_chu_dong(
                                snap_chk,
                                ['Thêm (1)', 'Thêm', 'Xong', 'Chọn', 'Add (1)', 'Add', 'Done', 'Select'],
                                exclude_keywords=['thêm ảnh', 'add photo', 'add picture'],
                                min_y=0.05,
                                max_y=0.96,
                                click_duoi=True
                            )
                            if nhan_xac_nhan_picker:
                                self.log(f'✅ [Photo Picker] Đã chọn ảnh #1 -> Bấm "{nhan_xac_nhan_picker}"...')
                                snap_chk = self._cho_chuyen_man_hinh(snap_chk['sig'], timeout=3.0)
                                if snap_chk['is_blank_or_loading']:
                                    snap_chk = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Chờ màn hình Lưu Avatar')

                        if self._la_man_hinh_luu_avatar(snap_chk):
                            snap_save = snap_chk
                            break

                        # Nếu bị văng ngược về màn 'Thêm ảnh đại diện' + 'Bỏ qua' -> dừng vòng chọn để lượt 2 mở lại Thư viện!
                        if self._snap_has(snap_chk, ['Thêm ảnh đại diện', 'Add profile picture']) and self._snap_has(snap_chk, ['Bỏ qua', 'Skip'], exact=True):
                            self.log('⚠️ Picker bị đóng về lại màn "Thêm ảnh đại diện" -> Mở lại Thư viện để chọn lại ảnh #1!')
                            snap_save = None
                            break

                if snap_save is None:
                    continue

                # 5. Bấm nút 'Lưu' / 'Xong' / 'Save' / 'Done' bằng quét chữ động (0% tọa độ cố định)
                self.log('💾 [Avatar - Bước cuối] Quét chữ bấm "Lưu / Xong" ảnh đại diện...')
                da_bam_luu = False
                for lan_luu in range(1, 5):
                    s_luu = snap_save if (lan_luu == 1 and snap_save is not None) else self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Chờ nút Lưu Avatar')
                    if self._snap_has(s_luu, ['Bạn đang nghĩ gì', 'Tạo tin', 'Tìm bạn bè từ danh bạ', 'cấp quyền truy cập vào danh bạ']):
                        da_bam_luu = True
                        break
                    nhan_luu = self._tim_va_bam_chu_dong(
                        s_luu,
                        ['Lưu', 'Xong', 'Save', 'Done', 'Áp dụng', 'Apply', 'Tiếp', 'Next'],
                        exclude_keywords=['lưu thông tin', 'bỏ qua', 'skip'],
                        min_y=0.04,
                        max_y=0.96,
                        click_duoi=True
                    )
                    if nhan_luu:
                        self.log(f'💾 [Avatar - Quét chữ] Đã bấm "{nhan_luu}"!')
                        da_bam_luu = True
                        self._cho_chuyen_man_hinh(s_luu['sig'], timeout=3.0)
                        break
                    time.sleep(0.4)

                if not da_bam_luu:
                    self.log('⚠️ Không thấy nút "Lưu / Xong" trên màn hình Avatar -> Thử lại!')
                    continue

                # 6. Chờ động tải xong Avatar (kiểm tra thật sự đã rời màn hình Thêm ảnh/Đang lưu)
                delay_max_avt = max(2.5, float(self.config.get('delay_up_avatar', 4.5)))
                moc_avt = time.time() + delay_max_avt
                time.sleep(0.6)
                while time.time() < moc_avt and not STOP_EVENT.is_set():
                    snap_done = self.quet_snapshot()
                    self.kiem_tra_va_dung_neu_die('Đang tải Avatar', snap=snap_done)
                    if not snap_done['is_blank_or_loading'] and not snap_done['has_progress'] and not self._snap_has(snap_done, ['Đang lưu', 'Đang tải lên', 'Saving', 'Uploading', 'Thêm ảnh đại diện', 'Add profile picture']):
                        break
                    time.sleep(0.3)

                self.log('✅ ĐÃ CẬP NHẬT AVATAR TỪ ẢNH ĐẦU TIÊN THÀNH CÔNG!')
                return True

            self.log('⚠️ Không thể hoàn tất thêm Avatar sau 2 lượt thử -> Tiếp tục sang bước Bật 2FA!')
            return False
        except AccountDieError:
            raise
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            self.log(f'⚠️ Lỗi up Avatar: {str(e)[:40]}')
            return False
# ==================== KẾT THÚC PHẦN 1/2 ====================
# ==================== PHẦN 2/2 (DÁN NỐI TIẾP NGAY DƯỚI PHẦN 1/2) ====================
    def _la_icon_dau_x(self, crop_gray):
        """
        Nhận diện chính xác icon dấu X (×) (VD nút tròn đóng tất cả tab trong Đa nhiệm):
        - Hai đường chéo (\ và /) đều có nét rõ qua tâm, còn 4 điểm rìa trên/dưới/trái/phải là nền trống.
        - Loại bỏ hoàn toàn dấu '+', hình tròn 'O', hình vuông đặc và icon 2 gạch ngang '='.
        Trả về (la_x: bool, rel_cx, rel_cy).
        """
        cw, ch = crop_gray.size
        if cw < 18 or ch < 18:
            return False, 0, 0
        try:
            px = crop_gray.load()
            vals = []
            for y in range(int(ch * 0.15), int(ch * 0.85), max(1, ch // 14)):
                for x in range(int(cw * 0.15), int(cw * 0.85), max(1, cw // 14)):
                    vals.append(px[x, y])
            if not vals:
                return False, 0, 0
            vals.sort()
            bg = vals[len(vals) // 2]
            la_nen_sang = (bg >= 128)

            xs, ys = [], []
            fg_set = set()
            x0, x1 = int(cw * 0.16), int(cw * 0.84)
            y0, y1 = int(ch * 0.16), int(ch * 0.84)
            for y in range(y0, y1):
                for x in range(x0, x1):
                    v = px[x, y]
                    if (v <= bg - 38) if la_nen_sang else (v >= bg + 38):
                        xs.append(x)
                        ys.append(y)
                        fg_set.add((x, y))

            if len(fg_set) < 16:
                return False, 0, 0

            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            bw, bh = max_x - min_x + 1, max_y - min_y + 1
            if bw < 10 or bh < 10:
                return False, 0, 0
            ratio = bw / float(bh)
            if not (0.65 <= ratio <= 1.55):
                return False, 0, 0

            fill_ratio = len(fg_set) / float(bw * bh)
            if not (0.08 <= fill_ratio <= 0.55):
                return False, 0, 0

            steps = 14
            hit_d1 = 0
            hit_d2 = 0
            tol = max(2, int(min(bw, bh) * 0.14))

            def has_fg_near(tx, ty):
                for dy in range(-tol, tol + 1):
                    for dx in range(-tol, tol + 1):
                        if (tx + dx, ty + dy) in fg_set:
                            return True
                return False

            for i in range(steps):
                t = i / float(steps - 1)
                x1p = int(min_x + t * (bw - 1))
                y1p = int(min_y + t * (bh - 1))
                x2p = int(max_x - t * (bw - 1))
                if has_fg_near(x1p, y1p):
                    hit_d1 += 1
                if has_fg_near(x2p, y1p):
                    hit_d2 += 1

            if hit_d1 < int(steps * 0.78) or hit_d2 < int(steps * 0.78):
                return False, 0, 0

            cx = (min_x + max_x) // 2
            cy = (min_y + max_y) // 2
            cardinals = [
                (cx, min_y + max(1, int(bh * 0.08))),
                (cx, max_y - max(1, int(bh * 0.08))),
                (min_x + max(1, int(bw * 0.08)), cy),
                (max_x - max(1, int(bw * 0.08)), cy),
            ]
            if sum(1 for (pxc, pyc) in cardinals if has_fg_near(pxc, pyc)) >= 2:
                return False, 0, 0

            return True, cx, cy
        except Exception:
            return False, 0, 0

    def _tim_nut_x_hoac_dong_tat_ca_da_nhiem(self, snap, clear_rids):
        """
        Tìm ĐỘNG nút 'Đóng tất cả' / 'Xóa tất cả' hoặc nút dấu X (×) trong màn hình Đa nhiệm (KHÔNG dùng tọa độ cứng):
        1. Theo Resource-ID chuẩn của mọi hãng Android (Xiaomi, Samsung, Oppo, Realme, Vivo, Huawei, Pixel, AOSP...).
        2. Theo chữ / mô tả ('Đóng tất cả', 'Xóa tất cả', 'Close all', 'Clear all', '×', 'X'...).
        3. Theo nhận diện ảnh dấu X (×) trên các node nút bấm hoặc vùng đáy Đa nhiệm (khi ROM ẩn chữ/ID của nút tròn ×).
        Trả về (mo_ta: str, cx: int, cy: int) hoặc None.
        """
        if not snap or not snap['nodes']:
            return None
        w, h = snap['w'], snap['h']

        # 1. Tìm theo Resource-ID chính xác hoặc chứa từ khóa clear_all / close_all / clearanim
        btn_rid = self._snap_find_rid(snap, clear_rids)
        if btn_rid is not None:
            return (btn_rid['text'] or btn_rid['desc'] or 'nút × / Đóng tất cả (ID)', btn_rid['cx'], btn_rid['cy'])

        for n in snap['nodes']:
            rid_low = (n.get('rid') or '').lower()
            if rid_low and any(k in rid_low for k in ['clear_all', 'close_all', 'clearanim', 'dismiss_all', 'recent_clean']):
                return (n['text'] or n['desc'] or f'nút {rid_low.split("/")[-1]}', n['cx'], n['cy'])

        # 2. Tìm theo chữ / content-desc ('Đóng tất cả', 'Xóa tất cả', 'Close all', 'Clear all', dấu '×')
        btn_txt = (
            self._snap_find(
                snap,
                ['Đóng tất cả', 'Xóa tất cả', 'Xoá tất cả', 'Xóa hết', 'Dọn sạch tất cả', 'Close all', 'Clear all', 'Clear all apps', 'Dismiss all'],
                exact=False,
                click_duoi=True,
                min_y=0.06
            )
            or self._snap_find(
                snap,
                ['×', '✕', '✖', 'X'],
                exact=True,
                click_duoi=True,
                min_y=0.08
            )
            or self._snap_find(
                snap,
                ['Đóng', 'Xóa', 'Xoá', 'Clear', 'Close'],
                exact=True,
                click_duoi=True,
                min_y=0.65
            )
        )
        if btn_txt is not None:
            nhan = (btn_txt['text'] or btn_txt['desc'] or 'Đóng tất cả').strip()
            if not any(bad in nhan.lower() for bad in ['dọn dẹp', 'quét bảo mật', 'cửa sổ nổi']):
                return (f'nút "{nhan}"', btn_txt['cx'], btn_txt['cy'])

        # 3. Nhận diện HÌNH ẢNH dấu X (×) (dành cho máy ẩn text/ID nút tròn × ở đáy Đa nhiệm)
        if HAS_PIL:
            try:
                shot = self.d.screenshot()
                if shot is not None:
                    img_gray = shot.convert('L')
                    iw, ih = img_gray.size
                    sx = iw / float(w)
                    sy = ih / float(h)

                    # 3A. Kiểm tra các node clickable dạng icon nằm ở nửa dưới (y >= 0.68*h)
                    for n in snap['nodes']:
                        if n['clickable'] and n['cy'] >= int(h * 0.68) and n['cy'] <= int(h * 0.95):
                            if 24 <= n['bw'] <= int(w * 0.30) and 24 <= n['bh'] <= int(h * 0.16):
                                cl = max(0, int(n['l'] * sx))
                                ct = max(0, int(n['t'] * sy))
                                cr = min(iw, int(n['r'] * sx))
                                cb = min(ih, int(n['b'] * sy))
                                ok_x, rcx, rcy = self._la_icon_dau_x(img_gray.crop((cl, ct, cr, cb)))
                                if ok_x:
                                    return ('nút dấu × (XML+Ảnh)', int((cl + rcx) / sx), int((ct + rcy) / sy))

                    # 3B. Quét cửa sổ vùng giữa đáy Đa nhiệm (x = 25%..75%, y = 72%..93%) tìm tâm dấu ×
                    cl, cr = int(iw * 0.25), int(iw * 0.75)
                    ct, cb = int(ih * 0.72), int(ih * 0.93)
                    win_s = max(64, int(iw * 0.14))
                    step = max(16, win_s // 3)
                    for wy in range(ct, max(ct + 1, cb - win_s + 1), step):
                        for wx in range(cl, max(cl + 1, cr - win_s + 1), step):
                            ok_x, rcx, rcy = self._la_icon_dau_x(
                                img_gray.crop((wx, wy, min(iw, wx + win_s), min(ih, wy + win_s)))
                            )
                            if ok_x:
                                return ('nút dấu × (nhận diện ảnh)', int((wx + rcx) / sx), int((wy + rcy) / sy))
            except Exception:
                pass

        return None

    def _da_dong_het_tab_da_nhiem(self, snap, clear_rids):
        """Kiểm tra màn hình Đa nhiệm hiện tại đã thực sự trống hết tab chưa."""
        if not snap:
            return False
        dau_hieu_trong = [
            'không có mục gần đây', 'không có mục nào gần đây',
            'không có ứng dụng nào gần đây', 'không có ứng dụng nào được sử dụng gần đây',
            'không có ứng dụng gần đây', 'no recent items', 'no recently used apps', 'no recent apps'
        ]
        if self._snap_has(snap, dau_hieu_trong):
            return True
        return False

    def _dang_mo_app_google_foreground(self):
        """
        Kiểm tra CHÍNH XÁC ứng dụng Google (`com.google.android.googlequicksearchbox`) có đang mở toàn màn hình ở foreground hay không.
        TUYỆT ĐỐI KHÔNG đọc từ `snap['packages']` vì thanh tìm kiếm Google (Widget) nằm sẵn trên màn hình chính Home luôn có gói này!
        """
        pkg, _ = self._lay_app_dang_hien_thi()
        if (pkg or '').strip().lower() == 'com.google.android.googlequicksearchbox':
            return True
        return False

    def _dang_o_man_hinh_chinh_home_sach(self, snap, clear_rids, dau_hieu_da_nhiem_co_tab, launcher_pkgs):
        """
        Xác nhận thiết bị đang đứng yên ở màn hình chính Home (Launcher), KHÔNG còn thẻ Đa nhiệm hay nút × / Đóng tất cả.
        """
        if not snap:
            return False
        pkg, _ = self._lay_app_dang_hien_thi()
        pkg_low = (pkg or '').strip().lower()
        la_launcher = (pkg_low in launcher_pkgs) or ('launcher' in pkg_low) or (pkg_low == 'com.miui.home')
        if not la_launcher:
            return False
        if self._tim_nut_x_hoac_dong_tat_ca_da_nhiem(snap, clear_rids) is not None:
            return False
        if self._snap_has(snap, dau_hieu_da_nhiem_co_tab):
            return False
        return True

    def _kiem_tra_lai_da_nhiem_da_sach_chua(self, clear_rids, dau_hieu_da_nhiem_co_tab, launcher_pkgs):
        """
        Mở lại Đa nhiệm để KIỂM TRA THỰC TẾ xem đã đóng hết sạch tab chưa:
        1. Nếu thấy chữ trống ('Không có mục gần đây'...) -> SẠCH (True) ngay lập tức.
        2. Chỉ báo lạc vào Google khi app Google thực sự đang chạy foreground (KHÔNG nhận nhầm Widget thanh tìm kiếm Google trên màn hình Home!).
        3. Nếu vẫn còn nút dấu × / 'Đóng tất cả' hoặc thanh tiêu đề Đa nhiệm -> CHƯA SẠCH (False).
        4. Nếu bấm Đa nhiệm xong máy đứng nguyên ở Home Launcher (không có nút × / không có thẻ) -> SẠCH (True).
        """
        try:
            self.d.press('recent')
        except Exception:
            self.chay_shell_nhanh('input keyevent 187')
        time.sleep(1.3)

        snap_v = self.quet_snapshot()

        if self._da_dong_het_tab_da_nhiem(snap_v, clear_rids):
            return True, snap_v

        if self._dang_mo_app_google_foreground():
            self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
            time.sleep(0.8)
            return False, snap_v

        if self._tim_nut_x_hoac_dong_tat_ca_da_nhiem(snap_v, clear_rids) is not None:
            return False, snap_v

        if self._snap_has(snap_v, dau_hieu_da_nhiem_co_tab):
            return False, snap_v

        if self._dang_o_man_hinh_chinh_home_sach(snap_v, clear_rids, dau_hieu_da_nhiem_co_tab, launcher_pkgs):
            return True, snap_v

        return False, snap_v

    def _tim_khung_the_ung_dung_da_nhiem(self, snap):
        """
        Tìm chính xác vị trí (card_cx, card_cy, la_the_giua) của thẻ ứng dụng trong màn Đa nhiệm:
        - Nếu thẻ nằm chính giữa (38%w .. 62%w, như kiểu Đa nhiệm Ngang MIUI) -> la_the_giua = True (vuốt LÊN từ trong thân thẻ là chuẩn nhất).
        - Nếu thẻ nằm cột trái hoặc cột phải (<38%w hoặc >62%w, kiểu Đa nhiệm Dọc 2 cột) -> la_the_giua = False (vuốt NGANG từ tâm thẻ ra mép là chuẩn nhất).
        - Luôn đảm bảo điểm đặt tay nằm BÊN TRONG thân thẻ (không bao giờ trượt ra nền mờ bên ngoài thẻ!).
        """
        w, h = snap['w'], snap['h']
        best_node = None
        best_area = 0
        for n in snap['nodes']:
            rid_low = (n.get('rid') or '').lower()
            if any(k in rid_low for k in ['task_view', 'snapshot', 'thumbnail', 'recent_card', 'task_item']):
                if int(h * 0.25) <= n['cy'] <= int(h * 0.80) and n['bw'] >= int(w * 0.25) and n['bh'] >= int(h * 0.18):
                    area = n['bw'] * n['bh']
                    if area > best_area:
                        best_area = area
                        best_node = n

        if best_node is not None:
            cx = max(int(w * 0.15), min(int(w * 0.85), best_node['cx']))
            cy = max(int(h * 0.42), min(int(h * 0.68), best_node['cy']))
            la_the_giua = (int(w * 0.38) <= cx <= int(w * 0.62))
            return cx, cy, la_the_giua

        # Nếu tìm thấy tên app trên đầu thẻ ('Facebook' / 'Cài đặt' / 'Settings') -> lấy x theo chữ, y hạ xuống chính giữa thân thẻ
        node_lbl = self._snap_find(snap, ['Facebook', 'Cài đặt', 'Settings'], exact=True, min_y=0.20, max_y=0.55)
        if node_lbl is not None:
            cx = max(int(w * 0.22), min(int(w * 0.78), node_lbl['cx']))
            cy = min(int(h * 0.64), node_lbl['cy'] + int(h * 0.20))
            la_the_giua = (int(w * 0.36) <= cx <= int(w * 0.64))
            return cx, cy, la_the_giua

        # Mặc định giữa thân thẻ (khớp thẻ đơn chính giữa x=28%..72%, y=37%..79%)
        return int(w * 0.50), int(h * 0.58), True

    def _vuot_gat_the_nhanh(self, x1, y1, x2, y2, dung_u2_truoc=True):
        """
        Thực hiện cú hất tay nhanh (fast fling ~120ms) để vượt ngưỡng vận tốc đóng thẻ của MIUI/HyperOS/OneUI:
        - Hỗ trợ cả UiAutomation `d.swipe(duration=0.12)` (mượt, có quán tính thật) lẫn `input swipe ... 130`.
        """
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        if dung_u2_truoc:
            try:
                self.d.swipe(x1, y1, x2, y2, duration=0.12)
                return
            except Exception:
                pass
        self.vuot_toa_do_an_toan(x1, y1, x2, y2, 130)

    def _bam_nut_dong_tat_ca_bang_ca_u2_va_tap(self, snap, clear_rids):
        """Bấm nút dấu × / 'Đóng tất cả' bằng UiAutomation native click (ổn định trên MIUI) + fallback input tap."""
        btn_rid = self._snap_find_rid(snap, clear_rids)
        if btn_rid is not None and btn_rid.get('rid'):
            try:
                el = self.d(resourceId=btn_rid['rid'])
                if el.exists:
                    el.click()
                    return f'nút {btn_rid["rid"].split("/")[-1]} (u2)'
            except Exception:
                pass
            self.click_toa_do_an_toan(btn_rid['cx'], btn_rid['cy'])
            return f'nút {btn_rid["rid"].split("/")[-1]}'

        nut_dong = self._tim_nut_x_hoac_dong_tat_ca_da_nhiem(snap, clear_rids)
        if nut_dong is not None:
            mo_ta, cx, cy = nut_dong
            try:
                self.d.click(cx, cy)
            except Exception:
                self.click_toa_do_an_toan(cx, cy)
            return mo_ta
        return ''

    def dong_sach_tab_da_nhiem(self, force_stop_fb=True):
        """
        Đóng sạch tab Đa nhiệm (Recents) TRIỆT ĐỂ 100% — XỬ LÝ ĐƯỢC CẢ THẺ ĐƠN GIỮA MÀN HÌNH (MIUI NGANG) LẪN DỌC 2 CỘT:
        1. RÚT TẬN GỐC QUA ADB TRƯỚC: Về Home -> `am force-stop` -> `xoa_task_fb_bang_adb` rút thẳng task khỏi Android Recents.
        2. Mở Đa nhiệm kiểm tra: nếu đã trống hoặc đứng yên ở màn Home -> XONG NGAY (1 giây)!
        3. Nếu thẻ vẫn còn trên màn Đa nhiệm:
           - Tự nhận diện vị trí khung thẻ `(card_cx, card_cy)` (luôn đặt tay ĐÚNG TRONG THÂN THẺ).
           - CHỈ vuốt NGANG TRÁI SANG PHẢI hoặc PHẢI SANG TRÁI (bỏ hoàn toàn vuốt lên trên).
           - Nếu vẫn còn nút `×` / `Đóng tất cả` -> bấm thêm bằng `u2` native click.
        4. Chốt hạ: Về Home + `am force-stop` + rút task ADB lần cuối -> bảo đảm ứng dụng tắt sạch 100%!
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        uf = self._u_flag()

        # BƯỚC 0: RÚT TẬN GỐC QUA ADB TRƯỚC (đưa về Home trước để Android cho phép remove-task ngay lập tức!)
        self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
        time.sleep(0.45)
        so_task_rut = 0
        if force_stop_fb:
            self.chay_shell_nhanh(f'am force-stop {uf}com.facebook.katana')
            so_task_rut = xoa_task_fb_bang_adb(self.serial, xoa_ca_cai_dat=False, user_id=self.user_id)
        if so_task_rut > 0:
            self.log(f'⚡ [ADB] Đã rút trực tiếp {so_task_rut} task khỏi hàng đợi Đa nhiệm!')
            time.sleep(0.5)

        dau_hieu_da_nhiem_co_tab = [
            'cửa sổ nổi', 'floating windows',
            'đóng tất cả', 'xóa tất cả', 'xoá tất cả', 'close all', 'clear all',
            'clear all apps', 'dismiss all'
        ]
        clear_rids = [
            # Xiaomi MIUI / HyperOS
            'com.miui.home:id/clearAnimView',
            'com.miui.home:id/clear_all',
            'com.miui.home:id/recent_clean_button',
            'com.miui.home:id/btn_clear_all',
            # Samsung OneUI
            'com.sec.android.app.launcher:id/clear_all_button',
            'com.sec.android.app.launcher:id/clear_all',
            # Oppo / Realme / OnePlus (ColorOS / RealmeUI / OxygenOS)
            'com.android.launcher:id/btn_clear',
            'com.oppo.launcher:id/btn_clear',
            'com.oplus.launcher:id/btn_clear',
            'com.coloros.recents:id/clear_all_button',
            'com.oneplus.launcher:id/clear_all_button',
            # Vivo (FunTouchOS / OriginOS)
            'com.bbk.launcher2:id/clear_all',
            'com.bbk.launcher2:id/clear_button',
            'com.vivo.upslide:id/clear_all',
            # Huawei / Honor
            'com.huawei.android.launcher:id/clear_all_recents_image_button',
            'com.hihonor.android.launcher:id/clear_all_recents_image_button',
            # AOSP / Pixel / Generic
            'com.android.systemui:id/clear_all',
            'com.google.android.apps.nexuslauncher:id/clear_all',
            'com.android.launcher3:id/clear_all',
        ]
        launcher_pkgs = {
            'com.miui.home', 'com.sec.android.app.launcher', 'com.android.launcher',
            'com.android.launcher3', 'com.oppo.launcher', 'com.oplus.launcher',
            'com.bbk.launcher2', 'com.huawei.android.launcher', 'com.hihonor.android.launcher',
            'com.google.android.apps.nexuslauncher', 'com.oneplus.launcher'
        }

        def da_sach_tab(s_chk):
            return (
                self._da_dong_het_tab_da_nhiem(s_chk, clear_rids)
                or self._dang_o_man_hinh_chinh_home_sach(s_chk, clear_rids, dau_hieu_da_nhiem_co_tab, launcher_pkgs)
            )

        snap_rec = None
        for vong in range(1, 3):
            if STOP_EVENT.is_set():
                break

            if snap_rec is None:
                try:
                    self.d.press('recent')
                except Exception:
                    self.chay_shell_nhanh('input keyevent 187')
                time.sleep(1.2)
                snap_rec = self.quet_snapshot()

            if self._dang_mo_app_google_foreground():
                self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
                time.sleep(0.7)
                snap_rec = None
                continue

            if da_sach_tab(snap_rec):
                self.log('✅ Màn hình Đa nhiệm đã trống sạch hoàn toàn!')
                break

            # BƯỚC 1: CHỈ vuốt NGANG TRÁI SANG PHẢI hoặc PHẢI SANG TRÁI qua tâm thẻ (TUYỆT ĐỐI BỎ VUỐT LÊN TRÊN!)
            card_cx, card_cy, _ = self._tim_khung_the_ung_dung_da_nhiem(snap_rec)
            x_trai_bat_dau = max(int(w * 0.12), min(card_cx, int(w * 0.45)))
            x_phai_bat_dau = min(int(w * 0.88), max(card_cx, int(w * 0.55)))

            if card_cx >= w // 2:
                # Thẻ ở giữa hoặc cột phải -> ưu tiên vuốt TRÁI -> PHẢI trước, rồi PHẢI -> TRÁI
                ds_huong_hat = [
                    ('vuốt TRÁI -> PHẢI (u2)', x_trai_bat_dau, card_cy, int(w * 0.96), card_cy, True),
                    ('vuốt PHẢI -> TRÁI (u2)', x_phai_bat_dau, card_cy, int(w * 0.04), card_cy, True),
                    ('vuốt TRÁI -> PHẢI (shell)', x_trai_bat_dau, card_cy, int(w * 0.96), card_cy, False),
                    ('vuốt PHẢI -> TRÁI (shell)', x_phai_bat_dau, card_cy, int(w * 0.04), card_cy, False),
                ]
            else:
                # Thẻ ở cột trái -> ưu tiên vuốt PHẢI -> TRÁI ra mép trái trước, rồi TRÁI -> PHẢI
                ds_huong_hat = [
                    ('vuốt PHẢI -> TRÁI (u2)', x_phai_bat_dau, card_cy, int(w * 0.04), card_cy, True),
                    ('vuốt TRÁI -> PHẢI (u2)', x_trai_bat_dau, card_cy, int(w * 0.96), card_cy, True),
                    ('vuốt PHẢI -> TRÁI (shell)', x_phai_bat_dau, card_cy, int(w * 0.04), card_cy, False),
                    ('vuốt TRÁI -> PHẢI (shell)', x_trai_bat_dau, card_cy, int(w * 0.96), card_cy, False),
                ]

            for mo_ta_hat, sx, sy, ex, ey, dung_u2 in ds_huong_hat:
                if STOP_EVENT.is_set() or da_sach_tab(snap_rec):
                    break
                # Chỉ cho phép vuốt khi ĐÃ XÁC NHẬN đang ở màn Đa nhiệm (không bao giờ vuốt ngoài màn Home!)
                if self._dang_mo_app_google_foreground():
                    self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
                    time.sleep(0.6)
                    break

                self.log(f'💨 [Đa nhiệm - Vòng {vong}] {mo_ta_hat} ({sx}, {sy}) -> ({ex}, {ey})...')
                self._vuot_gat_the_nhanh(sx, sy, ex, ey, dung_u2_truoc=dung_u2)
                time.sleep(0.85)

                snap_rec = self.quet_snapshot()
                if self._dang_mo_app_google_foreground():
                    self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
                    time.sleep(0.6)
                    snap_rec = None
                    break
                if da_sach_tab(snap_rec):
                    self.log('✅ Đã hất tắt sạch tab Đa nhiệm!')
                    break

            if snap_rec is not None and da_sach_tab(snap_rec):
                break

            # BƯỚC 2: Nếu thẻ vẫn còn -> Bấm nút × / Đóng tất cả bằng UiAutomation native click
            if snap_rec is not None and not da_sach_tab(snap_rec):
                mo_ta_btn = self._bam_nut_dong_tat_ca_bang_ca_u2_va_tap(snap_rec, clear_rids)
                if mo_ta_btn:
                    self.log(f'🧹 [Đa nhiệm - Vòng {vong}] Bấm bổ sung {mo_ta_btn}...')
                    time.sleep(1.1)
                    snap_rec = self.quet_snapshot()
                    if da_sach_tab(snap_rec):
                        self.log('✅ Đã đóng sạch toàn bộ tab Đa nhiệm!')
                        break

            # Kiểm tra lại lần nữa trước khi sang vòng 2
            da_het, snap_verify = self._kiem_tra_lai_da_nhiem_da_sach_chua(clear_rids, dau_hieu_da_nhiem_co_tab, launcher_pkgs)
            if da_het:
                self.log('✅ Xác nhận đã đóng sạch toàn bộ tab Đa nhiệm!')
                break
            snap_rec = snap_verify

        # BƯỚC 3 (CHỐT HẠ TUYỆT ĐỐI): Về Home + Force-stop + Rút sạch task ADB lần cuối
        self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
        time.sleep(0.45)
        if force_stop_fb:
            self.chay_shell_nhanh(f'am force-stop {uf}com.facebook.katana')
            xoa_task_fb_bang_adb(self.serial, xoa_ca_cai_dat=False, user_id=self.user_id)
        time.sleep(0.5)

    def xoa_tat_ca_du_lieu_fb_qua_cai_dat(self):
        """
        XÓA DỮ LIỆU NỔI TRỰC TIẾP TRÊN MÀN HÌNH (KHÔNG CẦN XÓA NGẦM — HOẠT ĐỘNG TRÊN MỌI HÃNG ĐIỆN THOẠI):
        Mở thẳng trang Thông tin ứng dụng Facebook (`APPLICATION_DETAILS_SETTINGS`) rồi thao tác chậm & chắc:
        - Xiaomi (MIUI/HyperOS): Xóa dữ liệu -> Xóa tất cả dữ liệu -> OK
        - Samsung (OneUI): Lưu trữ -> Xóa dữ liệu -> Xóa / OK
        - Oppo / Realme / OnePlus (ColorOS/OxygenOS): Mức sử dụng dung lượng lưu trữ / Lưu trữ -> Xóa dữ liệu -> Xóa / OK
        - Vivo (FunTouchOS/OriginOS): Bộ nhớ và bộ nhớ đệm / Lưu trữ -> Xóa bộ nhớ / Xóa dữ liệu -> OK
        - Pixel / AOSP / Huawei / Honor / Motorola / Nokia / Tecno: Bộ nhớ và bộ nhớ đệm / Lưu trữ -> Xóa bộ nhớ -> OK
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        uf = self._u_flag()
        self.log('🗑️ [Xóa dữ liệu NỔI] Mở Thông tin ứng dụng Facebook (hiển thị trực tiếp trên màn hình)...')
        self.chay_shell_nhanh(
            f'am start {uf}-a android.settings.APPLICATION_DETAILS_SETTINGS -d "package:com.facebook.katana"'
        )
        time.sleep(2.0)

        da_xac_nhan_xoa = False
        so_lan_cuon = 0

        for buoc in range(1, 14):
            if STOP_EVENT.is_set():
                break

            snap = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh=f'Xóa dữ liệu nổi bước {buoc}', check_die=False)
            if snap['is_blank_or_loading']:
                time.sleep(0.8)
                continue

            # ===== 1. HỘP THOẠI XÁC NHẬN CUỐI: "Xóa tất cả dữ liệu?" / "Xóa dữ liệu ứng dụng?" -> BẤM OK / XÓA =====
            if self._snap_has(snap, [
                'xóa tất cả dữ liệu?', 'xóa dữ liệu ứng dụng?', 'xóa dữ liệu?', 'xóa bộ nhớ?',
                'tất cả dữ liệu của ứng dụng', 'tất cả dữ liệu ứng dụng', 'toàn bộ dữ liệu',
                'bao gồm các tệp', 'bao gồm tất cả tệp', 'cài đặt, tài khoản', 'xóa vĩnh viễn',
                'delete app data', 'clear app data', 'clear all data?', 'delete all data',
                'permanently deleted', 'all of this app', 'files, settings, accounts'
            ]):
                # Chờ 0.8s cho hộp thoại hiện đứng yên rồi quét lại tọa độ chuẩn
                time.sleep(0.8)
                snap = self.quet_snapshot()
                self.log('✅ [Xóa dữ liệu NỔI] Hiện bảng xác nhận -> Bấm "OK / Xóa" để xóa sạch toàn bộ dữ liệu FB!')
                # Ưu tiên nút xác nhận chính xác (tránh tuyệt đối bấm nhầm nút Hủy / Cancel)
                nut_xac_nhan = (
                    self._snap_find_rid(snap, ['android:id/button1'])
                    or self._snap_find(
                        snap,
                        ['OK', 'Ok', 'Xóa', 'XÓA', 'Xóa tất cả', 'Xóa dữ liệu', 'Xác nhận', 'Đồng ý', 'Delete', 'DELETE', 'Clear', 'CLEAR', 'Confirm'],
                        exact=True,
                        click_duoi=True
                    )
                )
                if nut_xac_nhan is not None:
                    self.click_toa_do_an_toan(nut_xac_nhan['cx'], nut_xac_nhan['cy'])
                else:
                    self.click_toa_do_an_toan(int(w * 0.72), int(h * 0.88))
                time.sleep(2.4)
                da_xac_nhan_xoa = True
                break

            # ===== 2. BẢNG CHỌN 2 DÒNG (MIUI/HyperOS): 'Xóa tất cả dữ liệu' vs 'Xóa bộ nhớ đệm' -> CHỌN 'Xóa tất cả dữ liệu' =====
            node_all_data = self._snap_find(
                snap,
                ['Xóa tất cả dữ liệu', 'Xoá tất cả dữ liệu', 'Clear all data', 'Delete all data'],
                exact=False
            )
            if node_all_data is not None:
                time.sleep(0.7)
                snap = self.quet_snapshot()
                node_all_data = self._snap_find(
                    snap,
                    ['Xóa tất cả dữ liệu', 'Xoá tất cả dữ liệu', 'Clear all data', 'Delete all data'],
                    exact=False
                )
                if node_all_data is not None:
                    self.log('🗑️ [Xóa dữ liệu NỔI] Bấm chọn "Xóa tất cả dữ liệu"...')
                    self.click_toa_do_an_toan(node_all_data['cx'], node_all_data['cy'])
                    time.sleep(1.5)
                    continue

            # ===== 3. NÚT 'Xóa dữ liệu' / 'Xóa bộ nhớ' / 'Clear data' / 'Clear storage' (LOẠI TRỪ 'bộ nhớ đệm' / 'cache') =====
            btn_clear_data = None
            cac_nhan_xoa_dl = ['xóa dữ liệu', 'xoá dữ liệu', 'xóa bộ nhớ', 'xoá bộ nhớ', 'clear data', 'clear storage', 'delete data']
            ung_vien_xoa = []
            for n in snap['nodes']:
                tl, dl = n['text_low'], n['desc_low']
                # Tuyệt đối loại trừ nút 'Xóa bộ nhớ đệm' / 'Clear cache'
                if any(bo_qua in tl or bo_qua in dl for bo_qua in ['đệm', 'cache', 'bộ nhớ đệm']):
                    continue
                if any(k == tl or k == dl for k in cac_nhan_xoa_dl):
                    ung_vien_xoa.append((2, n['cy'], n))
                elif any(k in tl or k in dl for k in cac_nhan_xoa_dl) and len(tl or dl) <= 28:
                    ung_vien_xoa.append((1, n['cy'], n))
            if ung_vien_xoa:
                ung_vien_xoa.sort(key=lambda item: (item[0], item[1]), reverse=True)
                btn_clear_data = ung_vien_xoa[0][2]

            if btn_clear_data is not None:
                if not btn_clear_data.get('enabled', True):
                    self.log('✅ [Xóa dữ liệu NỔI] Nút "Xóa dữ liệu" đã mờ (dữ liệu FB đã sạch 0B)!')
                    da_xac_nhan_xoa = True
                    break
                self.log(f'🗑️ [Xóa dữ liệu NỔI] Bấm nút "{btn_clear_data["text"] or btn_clear_data["desc"]}" ({btn_clear_data["cx"]}, {btn_clear_data["cy"]})...')
                self.click_toa_do_an_toan(btn_clear_data['cx'], btn_clear_data['cy'])
                time.sleep(1.6)
                continue

            # ===== 4. MỤC 'Lưu trữ' / 'Bộ nhớ' / 'Mức sử dụng dung lượng lưu trữ' / 'Storage' (Samsung, Oppo, Vivo, Realme, Pixel, AOSP...) =====
            cac_nhan_luu_tru = [
                'mức sử dụng dung lượng lưu trữ', 'sử dụng dung lượng lưu trữ', 'sử dụng bộ nhớ',
                'bộ nhớ và bộ nhớ đệm', 'dung lượng lưu trữ', 'lưu trữ và bộ nhớ đệm',
                'lưu trữ', 'bộ nhớ',
                'storage & cache', 'storage and cache', 'storage usage', 'internal storage', 'storage'
            ]
            node_storage = None
            for kw in cac_nhan_luu_tru:
                for n in snap['nodes']:
                    tl, dl = n['text_low'], n['desc_low']
                    if any(bo_qua in tl or bo_qua in dl for bo_qua in ['xóa bộ nhớ đệm', 'xoá bộ nhớ đệm', 'clear cache']):
                        continue
                    if (kw == tl or kw == dl or kw in tl or kw in dl) and int(h * 0.14) <= n['cy'] <= int(h * 0.88):
                        node_storage = n
                        break
                if node_storage is not None:
                    break

            if node_storage is not None:
                self.log(f'📂 [Xóa dữ liệu NỔI] Mở mục "{node_storage["text"] or node_storage["desc"]}"...')
                self.click_toa_do_an_toan(node_storage['cx'], node_storage['cy'])
                time.sleep(1.7)
                continue

            # ===== 5. NẾU CHƯA THẤY MỤC LƯU TRỮ / XÓA DỮ LIỆU (MÀN HÌNH NHỎ HOẶC SAMSUNG/OPPO PHẢI CUỘN) -> CUỘN NHẸ XUỐNG =====
            if so_lan_cuon < 3:
                so_lan_cuon += 1
                self.log(f'📜 [Xóa dữ liệu NỔI] Cuộn nhẹ tìm mục "Lưu trữ / Xóa dữ liệu" (lần {so_lan_cuon}/3)...')
                self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.74), int(w * 0.50), int(h * 0.28), 340)
                time.sleep(1.3)
                continue

            # Dự phòng cuối cùng riêng cho thanh đáy MIUI nếu XML không trả chữ nút góc phải dưới
            if buoc <= 2 and self._snap_has(snap, ['thông tin ứng dụng', 'app info', 'buộc dừng', 'force stop']) and 'com.miui.securitycenter' in snap['packages']:
                self.click_toa_do_an_toan(int(w * 0.83), int(h * 0.90))
                time.sleep(1.5)
                continue

            break

        # Về Home & đóng sạch tab Cài đặt khỏi Đa nhiệm (chạy chuẩn trên mọi hãng máy, không bó buộc MIUI)
        time.sleep(0.8)
        self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
        time.sleep(1.0)
        self.dong_sach_tab_da_nhiem(force_stop_fb=False)
        if da_xac_nhan_xoa:
            self.log('✅ [Xóa dữ liệu NỔI] Đã xóa tất cả dữ liệu Facebook hoàn tất trên màn hình!')
        else:
            self.log('⚠️ [Xóa dữ liệu NỔI] Chưa thấy hộp thoại xác nhận OK (có thể dữ liệu FB đã trống sẵn).')
        return da_xac_nhan_xoa

    def _chon_khong_co_tu_dong_dien_ui(self):
        """Chọn 'Không có' / 'None' trên màn hình chọn Dịch vụ Tự động điền (chậm mà chắc, hỗ trợ mọi hãng máy)."""
        for buoc in range(1, 5):
            snap = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh=f'Tắt Tự động điền bước {buoc}', check_die=False)
            if snap['is_blank_or_loading']:
                break
            # Nếu hiện bảng xác nhận ('OK' / 'Thay đổi' / 'Tắt') -> bấm xác nhận
            if self._snap_has(snap, ['đảm bảo bạn tin tưởng', 'bạn có chắc', 'make sure you trust', 'change autofill', 'tắt dịch vụ']):
                time.sleep(0.6)
                snap = self.quet_snapshot()
                nut_ok = (
                    self._snap_find_rid(snap, ['android:id/button1'])
                    or self._snap_find(snap, ['OK', 'Ok', 'Thay đổi', 'Tắt', 'Xác nhận', 'Change', 'Turn off'], exact=True, click_duoi=True)
                )
                if nut_ok is not None:
                    self.click_toa_do_an_toan(nut_ok['cx'], nut_ok['cy'])
                    time.sleep(1.2)
                return True

            node_none = (
                self._snap_find(snap, ['Không có', 'Không', 'Tắt', 'None', 'Off'], exact=True, min_y=0.10, max_y=0.85)
                or self._snap_find(snap, ['Không có dịch vụ', 'Không sử dụng', 'No service'], exact=False, min_y=0.10, max_y=0.85)
            )
            if node_none is not None:
                self.log(f'🧹 [Tự động điền NỔI] Chọn "{node_none["text"] or node_none["desc"]}"...')
                self.click_toa_do_an_toan(node_none['cx'], node_none['cy'])
                time.sleep(1.3)
                # Kiểm tra nếu có hộp thoại xác nhận hiện ra ở vòng kế tiếp
                snap_after = self.quet_snapshot()
                if self._snap_has(snap_after, ['OK', 'Thay đổi', 'Xác nhận', 'Change'], exact=True):
                    continue
                return True
            break
        return False

    def xoa_tu_dong_dien_va_khoa_truy_cap_qua_cai_dat(self):
        """
        Xóa/Tắt NỔI trực tiếp trên màn hình Cài đặt (chỉ chạy khi máy chặn ADB hoặc vẫn còn dịch vụ đang bật):
        1. Mở màn hình chọn Dịch vụ Tự động điền -> chọn 'Không có' / 'None'.
        2. Mở màn hình Trình quản lý khóa truy cập / Mật khẩu, khóa truy cập và tự động điền -> tắt toàn bộ công tắc đang bật (Google, Samsung Pass, v.v.).
        3. Về Home & đóng sạch tab Cài đặt.
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        uf = self._u_flag()
        self.log('🔐 [NỔI - Mọi máy] Mở Cài đặt tắt Dịch vụ Tự động điền & Trình quản lý khóa truy cập...')

        # PHẦN 1: Tắt Dịch vụ Tự động điền (Autofill Service)
        self.chay_shell_nhanh(
            f'am start {uf}-a android.settings.REQUEST_SET_AUTOFILL_SERVICE -d "package:com.android.settings" '
            f'|| am start {uf}-a android.settings.AUTOFILL_SETTINGS'
        )
        time.sleep(1.8)
        snap_af = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Mở Dịch vụ tự động điền', check_die=False)
        if self._snap_has(snap_af, ['dịch vụ tự động điền', 'tự động điền', 'autofill service', 'không có', 'none']):
            self._chon_khong_co_tu_dong_dien_ui()

        # PHẦN 2: Tắt Trình quản lý khóa truy cập & Mật khẩu (Android 14+ Credential Manager / Passkeys)
        self.chay_shell_nhanh(
            f'am start {uf}-a android.settings.CREDENTIAL_PROVIDER '
            f'|| am start {uf}-a android.settings.SYNC_SETTINGS'
        )
        time.sleep(1.8)

        for buoc in range(1, 9):
            if STOP_EVENT.is_set():
                break
            snap = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh=f'Tắt Trình quản lý khóa truy cập bước {buoc}', check_die=False)
            if snap['is_blank_or_loading']:
                break

            # Nếu đang đứng ở trang Mật khẩu, khóa truy cập và tự động điền -> bấm vào 'Thay đổi' / 'Dịch vụ ưu tiên' nếu còn dịch vụ
            if self._snap_has(snap, ['mật khẩu, khóa truy cập', 'trình quản lý khóa truy cập', 'khóa truy cập', 'passwords, passkeys', 'credential']):
                # 2A. Nếu có nút 'Thay đổi' / 'Change' cạnh Dịch vụ ưu tiên (khi chưa phải Không có)
                if not self._snap_has(snap, ['không có', 'none'], exact=True):
                    node_change = self._snap_find(snap, ['Thay đổi', 'Change', 'Dịch vụ ưu tiên', 'Dịch vụ tự động điền', 'Preferred service'], exact=False, min_y=0.14, max_y=0.65)
                    if node_change is not None and buoc <= 2:
                        self.log(f'🔐 [Khóa truy cập NỔI] Mở "{node_change["text"] or node_change["desc"]}" để chọn Không có...')
                        self.click_toa_do_an_toan(node_change['cx'], node_change['cy'])
                        time.sleep(1.5)
                        self._chon_khong_co_tu_dong_dien_ui()
                        time.sleep(1.0)
                        continue

                # 2B. Quét & TẮT tất cả công tắc (Switch / CheckBox đang bật checked=True) của các trình quản lý khóa truy cập
                cac_cong_tac_bat = [
                    n for n in snap['nodes']
                    if n.get('checked')
                    and ('Switch' in n['cls'] or 'CheckBox' in n['cls'])
                    and int(h * 0.14) <= n['cy'] <= int(h * 0.88)
                ]
                if cac_cong_tac_bat:
                    cac_cong_tac_bat.sort(key=lambda n: n['cy'])
                    sw = cac_cong_tac_bat[0]
                    self.log(f'🔐 [Khóa truy cập NỔI] Tắt công tắc Trình quản lý khóa truy cập tại ({sw["cx"]}, {sw["cy"]})...')
                    self.click_toa_do_an_toan(sw['cx'], sw['cy'])
                    time.sleep(1.3)
                    # Xử lý hộp thoại xác nhận tắt (nếu có)
                    snap_cf = self.quet_snapshot()
                    if self._snap_has(snap_cf, ['tắt', 'turn off', 'ok', 'xác nhận', 'ngừng sử dụng'], exact=False):
                        nut_tat = (
                            self._snap_find_rid(snap_cf, ['android:id/button1'])
                            or self._snap_find(snap_cf, ['Tắt', 'OK', 'Ok', 'Xác nhận', 'Turn off', 'Disable'], exact=True, click_duoi=True)
                        )
                        if nut_tat is not None:
                            self.click_toa_do_an_toan(nut_tat['cx'], nut_tat['cy'])
                            time.sleep(1.2)
                    continue
            break

        # Về Home & đóng sạch tab Cài đặt
        self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
        time.sleep(0.9)
        self.dong_sach_tab_da_nhiem(force_stop_fb=False)

    def xoa_sach_tu_dong_dien_va_khoa_truy_cap(self, cho_phep_mo_cai_dat_noi=True):
        """
        Xóa sạch triệt để Dịch vụ Tự động điền (Autofill) & Trình quản lý khóa truy cập (Passkeys / Credential Manager):
        1. Chạy xóa sạch bằng ADB (`settings delete` + `cmd autofill destroy/reset`) & xác minh kết quả.
        2. Nếu thiết bị chặn quyền ADB (hoặc vẫn còn dịch vụ đang bật) và `cho_phep_mo_cai_dat_noi=True`
           -> tự động mở giao diện Cài đặt nổi để chọn 'Không có' & tắt sạch công tắc Trình quản lý khóa truy cập.
        """
        if self.config is not None and not self.config.get('xoa_tu_dong_dien_va_khoa_truy_cap', True):
            return True

        self.log('🔐 Đang xóa sạch Dịch vụ Tự động điền & Trình quản lý khóa truy cập...')
        da_sach, con_lai = xoa_sach_tu_dong_dien_va_khoa_truy_cap_adb(self.serial, user_id=self.user_id)
        if da_sach:
            self.log('✅ Đã xóa sạch Dịch vụ Tự động điền & Trình quản lý khóa truy cập (Autofill/Passkey = Trống)!')
            return True

        self.log(f'⚠️ Vẫn còn dịch vụ Tự động điền/Khóa truy cập ({", ".join(con_lai)[:65]})...')
        if cho_phep_mo_cai_dat_noi and self.user_id == 0:
            self.xoa_tu_dong_dien_va_khoa_truy_cap_qua_cai_dat()
            da_sach_sau, _ = xoa_sach_tu_dong_dien_va_khoa_truy_cap_adb(self.serial, user_id=self.user_id)
            if da_sach_sau:
                self.log('✅ Đã tắt sạch Dịch vụ Tự động điền & Trình quản lý khóa truy cập qua Cài đặt!')
            return da_sach_sau
        return False

    def dong_tab_va_mo_lai_fb_giu_nick(self):
        """
        Mở Đa nhiệm đóng sạch tab Facebook hiện tại rồi mở lại Facebook (KHÔNG xóa data)
        để thoát hoàn toàn khỏi màn hình cài đặt 2FA và quay về trang chủ có nút 3 gạch.
        """
        self.log('🔄 Thoát tab Facebook hiện tại rồi mở lại để ra màn hình chính...')
        self.dong_sach_tab_da_nhiem(force_stop_fb=True)

        self.log('🚀 Đang mở lại Facebook để thực hiện Đăng xuất & Gỡ trang cá nhân...')
        self._mo_app_fb_theo_user()
        nghi_ngau_nhien(self.config.get('delay_mo_lai_fb', 6.5), 0.1)
        self.tat_quyen_khong_cho_phep()
        self.bo_qua_luu_thong_tin_dang_nhap()
        self.quet_va_xoa_man_hinh_chan()

    def xoa_tab_da_nhiem_va_lam_moi_fb(self):
        """
        Đóng sạch tab Đa nhiệm, xóa tất cả dữ liệu ứng dụng Facebook và mở lại như mới (Không đổi lại IP).
        """
        self.xoa_du_lieu_dong_tab_va_mo_lai_fb_sach(mo_lai_fb=True)

    def _la_man_hinh_menu_fb(self, snap):
        """
        Xác nhận CHÍNH XÁC đang đứng trong trang Menu / Bookmarks của Facebook
        (loại trừ trang 'Cài đặt và quyền riêng tư' có 'Tài khoản Meta' / 'Tìm kiếm cài đặt'!).
        """
        if not snap or snap['is_blank_or_loading']:
            return False
        # Nếu đang ở form Đăng nhập trống hoặc màn hình chờ chọn nick -> KHÔNG phải Menu
        if self._co_dau_hieu_con_trang_fb_luu(snap) or self._la_man_hinh_dang_nhap_sach_hoan_toan(snap):
            return False
        # Loại trừ trang Cài đặt và quyền riêng tư (có 'Tìm kiếm cài đặt', 'Tài khoản Meta', 'Công cụ và nguồn lực')
        if (
            not self._snap_has(snap, ['đăng xuất', 'log out'])
            and self._snap_has(snap, [
                'tìm kiếm cài đặt', 'search settings',
                'tài khoản meta', 'meta accounts',
                'công cụ và nguồn lực', 'kiểm tra quyền riêng tư',
                'cài đặt đối tượng mặc định', 'tools and resources'
            ])
        ):
            return False
        dau_hieu_menu_chuan = [
            'đăng xuất', 'log out',
            'cài đặt và quyền riêng tư', 'cài đặt & quyền riêng tư',
            'settings & privacy', 'settings and privacy',
            'trợ giúp và hỗ trợ', 'trợ giúp & hỗ trợ', 'help & support', 'help and support',
            'cũng từ meta', 'also from meta',
            'lối tắt của bạn', 'your shortcuts',
            'xem trang cá nhân của bạn', 'see your profile',
            'quyền truy cập chuyên nghiệp', 'trung tâm hỗ trợ'
        ]
        if self._snap_has(snap, dau_hieu_menu_chuan):
            return True
        # Tiêu đề 'Menu' nằm ở phần đầu trang (y < 0.18*h) và KHÔNG còn chữ bảng tin 'Bạn đang nghĩ gì'
        if (
            not self._snap_has(snap, ['bạn đang nghĩ gì', 'tạo tin', "what's on your mind", 'create story'])
            and self._snap_find(snap, ['Menu'], exact=True, min_y=0.03, max_y=0.18, max_x=0.50) is not None
        ):
            return True
        return False

    def _dem_so_gach_ngang_icon(self, crop_gray):
        """
        Nhận diện hình ảnh chuẩn xác icon 3 gạch ngang (≡) hoặc 2 gạch ngang (=) ở góc trên cao màn hình:
        - Lấy màu nền theo trung vị vùng lõi (hoạt động cả nền sáng, nền tối và nút tròn có viền xám).
        - Khoảng hở giữa các gạch PHẢI sạch tuyệt đối (hàng giữa khoảng hở <= 2px nét) và gọn (<= 0.65 * rộng gạch),
          loại bỏ 100% vòng tròn icon Tìm kiếm (🔍), Messenger, Profile, dấu cộng (+), mũi tên Back (<).
        Trả về (so_gach: 0|2|3, rel_cx, rel_cy).
        """
        cw, ch = crop_gray.size
        if cw < 16 or ch < 16:
            return 0, 0, 0
        try:
            px = crop_gray.load()
            sample_vals = []
            x0, x1 = max(0, int(cw * 0.12)), min(cw, int(cw * 0.88))
            y0, y1 = max(0, int(ch * 0.12)), min(ch, int(ch * 0.88))
            step_x = max(1, (x1 - x0) // 16)
            step_y = max(1, (y1 - y0) // 16)
            for yy in range(y0, y1, step_y):
                for xx in range(x0, x1, step_x):
                    sample_vals.append(px[xx, yy])
            if not sample_vals:
                return 0, 0, 0
            sample_vals.sort()
            bg = sample_vals[len(sample_vals) // 2]

            row_runs = []
            la_nen_sang = (bg >= 128)
            for y in range(ch):
                best_len = 0
                best_s = 0
                cur_len = 0
                cur_s = 0
                total_fg = 0
                for x in range(cw):
                    val = px[x, y]
                    la_net = (val <= bg - 40) if la_nen_sang else (val >= bg + 40)
                    if la_net:
                        total_fg += 1
                        if cur_len == 0:
                            cur_s = x
                        cur_len += 1
                        if cur_len > best_len:
                            best_len = cur_len
                            best_s = cur_s
                    else:
                        cur_len = 0
                row_runs.append((best_len, best_s, best_s + best_len, total_fg))

            min_bar_w = max(8, int(cw * 0.24))
            max_bar_w = int(cw * 0.90)

            bands = []
            in_band = False
            b_start = 0
            for y, (blen, bs, be, tfg) in enumerate(row_runs):
                is_bar_row = (min_bar_w <= blen <= max_bar_w) and (tfg <= blen + max(2, int(cw * 0.08)))
                if is_bar_row and not in_band:
                    in_band = True
                    b_start = y
                elif not is_bar_row and in_band:
                    in_band = False
                    bands.append((b_start, y - 1))
            if in_band:
                bands.append((b_start, ch - 1))

            valid_bands = []
            for y1_b, y2_b in bands:
                bh = y2_b - y1_b + 1
                if 1 <= bh <= max(5, int(ch * 0.22)):
                    mid_y = (y1_b + y2_b) // 2
                    blen, bs, be, _ = row_runs[mid_y]
                    valid_bands.append((y1_b, y2_b, blen, (bs + be) // 2))

            if len(valid_bands) not in (2, 3):
                return 0, 0, 0

            widths = [b[2] for b in valid_bands]
            cxs = [b[3] for b in valid_bands]
            avg_w = sum(widths) / float(len(widths))
            if min(widths) < max(widths) * 0.58:
                return 0, 0, 0
            if max(cxs) - min(cxs) > int(cw * 0.18):
                return 0, 0, 0

            # Kiểm tra khoảng hở giữa các gạch: hàng giữa khoảng hở PHẢI sạch (<= 2px) — loại 100% vòng tròn Tìm kiếm / Messenger / '+'
            gaps = []
            for i in range(len(valid_bands) - 1):
                g1 = valid_bands[i][1] + 1
                g2 = valid_bands[i + 1][0] - 1
                if g2 < g1:
                    return 0, 0, 0
                gap_h = g2 - g1 + 1
                if gap_h > max(6, int(avg_w * 0.65)):
                    return 0, 0, 0
                gaps.append(gap_h)
                mid_g = (g1 + g2) // 2
                if row_runs[mid_g][3] > 2:
                    return 0, 0, 0
                clean_rows = sum(1 for gy in range(g1, g2 + 1) if row_runs[gy][3] <= 2)
                if clean_rows < max(1, int(gap_h * 0.55)):
                    return 0, 0, 0

            if len(gaps) == 2 and (max(gaps) > min(gaps) * 2.2 + 3):
                return 0, 0, 0

            rel_cx = sum(cxs) // len(cxs)
            rel_cy = (valid_bands[0][0] + valid_bands[-1][1]) // 2
            return len(valid_bands), rel_cx, rel_cy
        except Exception:
            return 0, 0, 0

    def _tim_ung_vien_nut_menu_goc_tren_cao(self, snap):
        """
        Tìm ĐỘNG nút Menu (3 gạch ngang ≡ hoặc 2 gạch ngang =) ở CẢ GÓC TRÁI LẪN GÓC PHẢI trên cao — TUYỆT ĐỐI KHÔNG CỐ ĐỊNH TỌA ĐỘ:
        1. Quét node XML đối xứng cả góc trên-trái (x <= 25%) lẫn góc trên-phải (x >= 75%), xác minh hình ảnh 3/2 gạch ngang.
        2. Quét ảnh trực tiếp đối xứng cả 2 góc trên-trái & trên-phải với 2 cỡ cửa sổ gọn (không dính chữ 'facebook' bên cạnh như Ảnh 2).
        3. KHÔNG dùng tọa độ cứng — nếu không tìm thấy nút thực tế nào sẽ chuyển thẳng sang DeepLink fb://bookmarks.
        """
        w, h = snap['w'], snap['h']
        loai_tru = [
            'tìm kiếm', 'search', 'tạo', 'create', 'messenger', 'tin nhắn', 'chat', 'message',
            'thông báo', 'notification', 'bạn bè', 'friends', 'video', 'reels', 'marketplace',
            'trang chủ', 'home', 'feed', 'bảng feed', 'quay lại', 'back', 'đóng', 'close', 'camera', 'profile', 'trang cá nhân'
        ]

        img_gray = None
        if HAS_PIL:
            try:
                shot = self.d.screenshot()
                if shot is not None:
                    img_gray = shot.convert('L')
            except Exception:
                img_gray = None

        ket_qua = []
        da_co_diem = []

        def them_diem(diem_uu_tien, mo_ta, cx, cy):
            if cx <= 0 or cy <= 0 or cx >= w or cy >= h:
                return
            for px_old, py_old in da_co_diem:
                if abs(px_old - cx) <= int(w * 0.045) and abs(py_old - cy) <= int(h * 0.025):
                    return
            da_co_diem.append((cx, cy))
            ket_qua.append((diem_uu_tien, mo_ta, cx, cy))

        # --- TẦNG 1: QUÉT NODE XML ĐỐI XỨNG CẢ GÓC TRÁI & GÓC PHẢI (0.025*h <= cy <= 0.24*h) ---
        for n in snap['nodes']:
            cy, cx = n['cy'], n['cx']
            if not (int(h * 0.025) <= cy <= int(h * 0.24)):
                continue
            if n['bw'] > int(w * 0.35) or n['bh'] > int(h * 0.14):
                continue

            tl, dl = n['text_low'], n['desc_low']
            comb = f'{tl} {dl}'.strip()
            ben_goc = 'trái' if cx <= w // 2 else 'phải'
            o_goc_cao = (cy <= int(h * 0.165)) and (cx <= int(w * 0.25) or cx >= int(w * 0.75))

            if comb and any(bad in comb for bad in loai_tru) and 'menu' not in comb:
                continue

            la_nhan_menu = any(k in comb for k in [
                'menu', 'mở menu', 'open menu', 'ngăn điều hướng', 'navigation', 'bookmarks', 'lối tắt'
            ])

            if img_gray is not None and (o_goc_cao or la_nhan_menu) and n['bw'] >= 20 and n['bh'] >= 20:
                try:
                    iw, ih = img_gray.size
                    sx = iw / float(w)
                    sy = ih / float(h)
                    pad = 2
                    cl = max(0, int(n['l'] * sx) - pad)
                    ct = max(0, int(n['t'] * sy) - pad)
                    cr = min(iw, int(n['r'] * sx) + pad)
                    cb = min(ih, int(n['b'] * sy) + pad)
                    so_gach, rcx, rcy = self._dem_so_gach_ngang_icon(img_gray.crop((cl, ct, cr, cb)))
                    if so_gach in (2, 3):
                        abs_cx = int((cl + rcx) / sx)
                        abs_cy = int((ct + rcy) / sy)
                        uu_tien = 104 if o_goc_cao else 94
                        if la_nhan_menu:
                            uu_tien += 10
                        if so_gach == 3:
                            uu_tien += 4
                        them_diem(uu_tien, f'Icon {so_gach} gạch ngang góc trên-{ben_goc} (XML+Ảnh)', abs_cx, abs_cy)
                        continue
                except Exception:
                    pass

            if la_nhan_menu:
                uu_tien = 88 if o_goc_cao else 78
                them_diem(uu_tien, f'Nút Menu góc {ben_goc} "{n["text"] or n["desc"]}"', cx, cy)
            elif o_goc_cao and n['clickable'] and n['bw'] <= int(w * 0.22) and n['bh'] <= int(h * 0.11):
                them_diem(55, f'Nút góc trên-{ben_goc} (XML)', cx, cy)

        # --- TẦNG 2: QUÉT ẢNH ĐỐI XỨNG CẢ 2 GÓC TRÊN-TRÁI & TRÊN-PHẢI (2 CỠ CỬA SỔ GỌN, KHÔNG TỌA ĐỘ CỐ ĐỊNH) ---
        if img_gray is not None:
            try:
                iw, ih = img_gray.size
                sx = iw / float(w)
                sy = ih / float(h)
                vung_goc = [
                    ('góc trên-trái cao', 0.00, 0.22, 0.032, 0.145),
                    ('góc trên-phải cao', 0.78, 1.00, 0.032, 0.145),
                    ('góc tab trên-trái', 0.00, 0.22, 0.085, 0.200),
                    ('góc tab trên-phải', 0.78, 1.00, 0.085, 0.200),
                ]
                for ten_vung, rx1, rx2, ry1, ry2 in vung_goc:
                    cl, cr = int(iw * rx1), int(iw * rx2)
                    ct, cb = int(ih * ry1), int(ih * ry2)
                    da_thay_vung = False
                    for wf, hf in [(0.095, 0.045), (0.125, 0.062)]:
                        win_w = max(44, int(iw * wf))
                        win_h = max(44, int(ih * hf))
                        step_x = max(10, win_w // 4)
                        step_y = max(10, win_h // 4)
                        for wy in range(ct, max(ct + 1, cb - win_h + 1), step_y):
                            for wx in range(cl, max(cl + 1, cr - win_w + 1), step_x):
                                so_g, rcx, rcy = self._dem_so_gach_ngang_icon(
                                    img_gray.crop((wx, wy, min(iw, wx + win_w), min(ih, wy + win_h)))
                                )
                                if so_g in (2, 3):
                                    abs_cx = int((wx + rcx) / sx)
                                    abs_cy = int((wy + rcy) / sy)
                                    uu_tien = 99 if so_g == 3 else 95
                                    them_diem(uu_tien, f'Nhận diện ảnh {so_g} gạch ngang ({ten_vung})', abs_cx, abs_cy)
                                    da_thay_vung = True
                                    break
                            if da_thay_vung:
                                break
                        if da_thay_vung:
                            break
            except Exception:
                pass

        ket_qua.sort(key=lambda item: item[0], reverse=True)
        return ket_qua

    def _bam_nut_3_gach_goc_trai(self):
        """
        Tìm và bấm CHUẨN XÁC nút Menu (3 gạch ngang ≡ hoặc 2 gạch ngang = ở góc trên màn hình — cả TRÁI & PHẢI, KHÔNG cố định):
        - Đóng ngay bảng Google Play tải tệp bổ sung (dấu × ở Ảnh 2), lớp phủ Google & các bảng chắn TRƯỚC khi quét.
        - Kết hợp XML + nhận diện ảnh 3 gạch ngang (≡) / 2 gạch ngang (=) đối xứng 2 góc trên cao.
        - Nếu lỡ bấm nhầm sang màn khác không phải Menu -> tự bấm Back quay lại trang chủ rồi thử ứng viên tiếp theo.
        - Dự phòng chắc ăn 100% bằng DeepLink `fb://bookmarks`.
        Trả về True khi thực sự đã vào trang Menu Facebook.
        """
        self.dong_goi_y_google(max_thu=3)
        snap0 = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Trước khi mở Menu đăng xuất', check_die=False)
        self.dong_bang_google_play_tai_bo_sung(snap=snap0)
        self.bo_qua_luu_thong_tin_dang_nhap(snap=snap0)
        self.quet_va_xoa_man_hinh_chan(so_vong_quet=3)

        snap = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Quét nút 2 gạch ngang Menu', check_die=False)
        if self._la_man_hinh_menu_fb(snap):
            return True

        ung_vien = self._tim_ung_vien_nut_menu_goc_tren_cao(snap)[:5]
        tong_uv = len(ung_vien)
        for idx, (score, mo_ta, cx, cy) in enumerate(ung_vien, 1):
            if STOP_EVENT.is_set():
                return False
            self.log(f'☰ [Menu {idx}/{tong_uv}] Bấm {mo_ta} tại ({cx}, {cy})...')
            prev_sig = snap['sig']
            self.click_toa_do_an_toan(cx, cy)
            time.sleep(1.8)

            snap_sau = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Kiểm tra đã mở Menu chưa', check_die=False)
            if self._bam_luc_khac_neu_co(snap=snap_sau):
                time.sleep(0.8)
                snap_sau = self.quet_snapshot()

            if self._la_man_hinh_menu_fb(snap_sau):
                self.log(f'✅ Đã mở chuẩn trang Menu từ {mo_ta}!')
                return True

            # Nếu bấm nhầm sang màn khác (Tìm kiếm, Tin nhắn, Tạo bài, Thông báo...) -> bấm Back quay lại Trang chủ ngay!
            if snap_sau['sig'] != prev_sig and not self._snap_has(snap_sau, ['bạn đang nghĩ gì', 'tạo tin', "what's on your mind"]):
                self.log('↩️ Điểm bấm không mở Menu -> Bấm Back quay lại trang chủ để thử điểm kế tiếp...')
                try:
                    self.d.press('back')
                except Exception:
                    self.chay_shell_nhanh('input keyevent 4')
                time.sleep(1.3)
                snap = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Quay lại trang chủ FB', check_die=False)
                if self._la_man_hinh_menu_fb(snap):
                    return True

        # Fallback cuối cùng: DeepLink native mở thẳng trang Menu Facebook
        self.log('⚡ Mở trực tiếp trang Menu bằng DeepLink fb://bookmarks...')
        self.chay_shell_nhanh(f'am start {self._u_flag()}-a android.intent.action.VIEW -d "fb://bookmarks"')
        time.sleep(2.5)
        snap_dl = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Chờ DeepLink Menu', check_die=False)
        return self._la_man_hinh_menu_fb(snap_dl)

    def _dang_dang_nhap_trong_app_fb(self, snap):
        """
        Xác nhận tài khoản HIỆN VẪN ĐANG ĐĂNG NHẬP BÊN TRONG Facebook (Bảng tin / Trang chủ / Menu / Bạn bè / Thông báo),
        CHƯA đăng xuất ra màn hình chờ chọn nick.
        -> Dùng để chặn tuyệt đối lỗi nhận nhầm nút "Gỡ" gợi ý kết bạn trên Bảng tin ("Những người bạn có thể biết")
           thành màn hình "Gỡ trang cá nhân khỏi thiết bị này"!
        """
        if not snap or snap.get('is_blank_or_loading'):
            return False
        dau_hieu_da_dang_nhap = [
            'bạn đang nghĩ gì', "what's on your mind", 'what’s on your mind',
            'tạo tin', 'create story', 'tin của bạn', 'your story',
            'những người bạn có thể biết', 'people you may know',
            'tìm bạn bè từ danh bạ', 'find friends from contacts',
            'thêm bạn bè', 'add friend',
            'đăng xuất', 'log out',
            'cài đặt và quyền riêng tư', 'cài đặt & quyền riêng tư',
            'settings & privacy', 'settings and privacy',
            'lối tắt của bạn', 'your shortcuts',
            'xem trang cá nhân của bạn', 'see your profile',
            'cũng từ meta', 'also from meta',
            'mở menu', 'open menu', 'menu, tab',
        ]
        if self._snap_has(snap, dau_hieu_da_dang_nhap):
            return True
        # Kiểm tra thanh tab trên cùng của Facebook đã đăng nhập (Bảng feed / Thông báo / Bạn bè / Video / Menu)
        w, h = snap['w'], snap['h']
        so_tab_fb = 0
        for n in snap['nodes']:
            if int(h * 0.03) <= n['cy'] <= int(h * 0.20):
                comb = f"{n['text_low']} {n['desc_low']}"
                if any(k in comb for k in ['bảng feed', 'trang chủ', 'home', 'thông báo', 'notifications', 'bạn bè', 'friends', 'reels', 'video', 'menu']):
                    so_tab_fb += 1
        if so_tab_fb >= 3:
            return True
        return False

    def _co_dau_hieu_con_trang_fb_luu(self, snap):
        """
        Kiểm tra màn hình ĐÃ ĐĂNG XUẤT có còn hiển thị trang cá nhân / tài khoản FB nào lưu sẵn ngoài màn hình chờ hay không.
        - TUYỆT ĐỐI trả False nếu đang ở trong Bảng tin / Menu Facebook đã đăng nhập (phải bấm 3 gạch Đăng xuất trước!).
        - KHÔNG bao giờ chỉ dựa vào nút 'Gỡ' / 'Remove' đơn lẻ (vì Bảng tin gợi ý kết bạn cũng có nút 'Gỡ'!).
        """
        if not snap:
            return False
        if self._dang_dang_nhap_trong_app_fb(snap):
            return False
        dau_hieu_con_nick = [
            'dùng trang cá nhân khác',
            'dùng tài khoản khác',
            'đăng nhập bằng tài khoản khác',
            'đăng nhập vào tài khoản khác',
            'use another profile',
            'use another account',
            'log into another account',
            'log in to another account',
            'chọn trang cá nhân',
            'chọn tài khoản',
            'tiếp tục với tư cách',
            'continue as',
            'gỡ trang cá nhân khỏi thiết bị này',
            'gỡ trang cá nhân',
            'remove profiles from this device',
            'remove profile from this device',
            'remove profile',
            'quản lý trang cá nhân',
            'manage profiles',
            'xóa khỏi thiết bị này',
            'remove from this device',
            'tin nhắn được mã hóa đầu cuối',
            'lần đăng nhập tiếp theo',
        ]
        if self._snap_has(snap, dau_hieu_con_nick):
            return True
        # Trường hợp thẻ 1 trang cá nhân chỉ có nút 'Tiếp tục' + 'Tạo tài khoản mới' (không có ô nhập Email/SĐT)
        if (
            self._snap_has(snap, ['tiếp tục', 'continue'], exact=True)
            and self._snap_has(snap, ['tạo tài khoản mới', 'create new account'])
            and not self._snap_has(snap, ['số di động hoặc email', 'mobile number or email', 'điều khoản của meta', 'điều khoản và chính sách'])
            and len(snap['edit_texts']) == 0
        ):
            return True
        return False

    def _la_man_hinh_dang_nhap_sach_hoan_toan(self, snap):
        """Chỉ trả về True khi màn hình FB đã hoàn toàn trống tài khoản (form đăng nhập trắng hoặc Tham gia Facebook trắng)."""
        if not snap or snap['is_blank_or_loading']:
            return False
        if self._co_dau_hieu_con_trang_fb_luu(snap):
            return False
        if self._snap_has(snap, ['số di động hoặc email', 'mobile number or email', 'mật khẩu', 'password']) and len(snap['edit_texts']) >= 1:
            return True
        if self._snap_has(snap, ['tham gia facebook', 'join facebook']) and self._snap_has(snap, ['tạo tài khoản mới', 'bắt đầu', 'create new account', 'get started']):
            return True
        return False

    def _cho_dang_xuat_hoan_tat(self, timeout=30.0):
        """
        Chờ Facebook thực sự hoàn tất quá trình 'Đang đăng xuất...' / vòng xoay tải
        cho tới khi ra hẳn màn hình chờ (còn trang FB để gỡ) HOẶC màn hình đăng nhập trống,
        rồi nghỉ thêm 1.6s để giao diện đứng yên hoàn toàn trước khi thao tác tiếp.
        """
        self.log('⏳ Đợi Facebook đăng xuất xong hẳn (chậm mà chắc)...')
        deadline = time.time() + float(timeout)
        time.sleep(2.0)
        while time.time() < deadline and not STOP_EVENT.is_set():
            snap = self.quet_snapshot()
            if self._bam_luc_khac_neu_co(snap=snap):
                time.sleep(1.4)
                continue
            if self.tat_quyen_khong_cho_phep(snap=snap):
                time.sleep(1.2)
                continue
            if snap['is_blank_or_loading'] or snap['has_progress'] or self._snap_has(snap, [
                'đang đăng xuất', 'logging out', 'signing out', 'đang tải', 'vui lòng đợi'
            ]):
                time.sleep(0.9)
                continue
            if self._co_dau_hieu_con_trang_fb_luu(snap) or self._la_man_hinh_dang_nhap_sach_hoan_toan(snap):
                time.sleep(1.6)
                return True
            time.sleep(0.9)
        return False

    def _cho_giao_dien_xoa_trang_hoan_tat(self, prev_sig, so_nut_go_truoc=0, timeout=22.0):
        """
        Chờ Facebook thực sự GỠ XONG trang cá nhân sau khi bấm nút xanh 'Xóa khỏi thiết bị này' (chậm mà chắc):
        - Chờ bảng xác nhận biến mất hoàn toàn & hết mọi vòng xoay tải.
        - Nghỉ thêm 1.8s – 2.0s cho giao diện và dữ liệu ghi xong xuôi rồi mới chuyển sang trang tiếp theo.
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        deadline = time.time() + float(timeout)
        time.sleep(2.0)
        while time.time() < deadline and not STOP_EVENT.is_set():
            snap = self.quet_snapshot()
            con_bang_xac_nhan = self._snap_has(snap, [
                'xóa khỏi thiết bị này', 'khỏi thiết bị này?', 'remove from this device',
                'tin nhắn được mã hóa đầu cuối', 'lần đăng nhập tiếp theo'
            ])
            dang_xu_ly = (
                snap['is_blank_or_loading']
                or snap['has_progress']
                or self._snap_has(snap, ['đang xóa', 'đang gỡ', 'removing', 'deleting', 'đang tải', 'vui lòng đợi'])
            )
            if con_bang_xac_nhan or dang_xu_ly:
                time.sleep(0.8)
                continue

            if self._la_man_hinh_dang_nhap_sach_hoan_toan(snap):
                time.sleep(2.0)
                return True

            nut_go_hien_tai = [
                n for n in snap['nodes']
                if (n['text_low'] in {'gỡ', 'remove'} or n['desc_low'] in {'gỡ', 'remove'})
                and int(h * 0.12) <= n['cy'] <= int(h * 0.93)
            ]
            if so_nut_go_truoc > 0 and len(nut_go_hien_tai) < so_nut_go_truoc:
                time.sleep(1.8)
                return True

            if snap['sig'] != prev_sig:
                time.sleep(1.8)
                return True

            time.sleep(0.8)
        time.sleep(1.5)
        return False

    def _go_trang_ca_nhan_ngoai_man_hinh_cho(self):
        """
        GỠ BẰNG HẾT TẤT CẢ TRANG CÁ NHÂN FB THEO NHỊP CHẬM NHƯNG CHẮC (1 thao tác / nhịp, không bắn nhanh):
        - Đợi mọi bảng đáy / danh sách trượt lên đứng yên (1.0s) và quét lại tọa độ tươi trước khi bấm.
        - Ở màn hình Ảnh 7 (nút 3 chấm ...): mỗi vòng chỉ thử ĐÚNG 1 điểm rồi đợi 2.0s kiểm tra (không spam loạt tọa độ).
        - Ở danh sách nhiều trang FB: bấm từng nút 'Gỡ' -> đợi 1.8s -> bấm 'Xóa khỏi thiết bị này' -> chờ xóa xong hẳn -> lặp tới khi sạch 100%.
        - CHỈ trả về True khi xác minh 2 lần liên tiếp (cách nhau 2.5s) màn hình đã về hẳn form đăng nhập trống.
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        self.log('🗑️ [Gỡ hết trang FB - Chậm mà chắc] Quét & gỡ lần lượt toàn bộ trang cá nhân FB...')

        so_trang_da_go = 0
        so_nut_go_gan_nhat = 0
        so_vong_khong_thao_tac = 0
        buoc_thu_3_cham = 0
        han_chot_go = time.time() + 240.0

        for vong_go in range(1, 71):
            if STOP_EVENT.is_set() or time.time() > han_chot_go:
                break

            snap = self.cho_man_hinh_san_sang(timeout=20.0, ngu_canh=f'Gỡ hết trang FB vòng {vong_go}', check_die=False)

            # Nếu Facebook vẫn đang quay vòng tải / đang đăng xuất / đang gỡ -> CHỜ ÊM, không thao tác!
            if snap['is_blank_or_loading'] or snap['has_progress'] or self._snap_has(snap, [
                'đang đăng xuất', 'đang xóa', 'đang gỡ', 'logging out', 'removing', 'deleting', 'đang tải'
            ]):
                self.log('⏳ Facebook đang xử lý -> Đứng đợi ổn định...')
                time.sleep(1.2)
                continue

            if self.dong_bang_google_play_tai_bo_sung(snap=snap):
                so_vong_khong_thao_tac = 0
                time.sleep(1.0)
                continue

            # CHỐT AN TOÀN: Nếu vẫn đang đăng nhập trong Bảng tin / Menu FB (chưa đăng xuất) -> THOÁT NGAY, không bấm nhầm nút "Gỡ" gợi ý kết bạn!
            if self._dang_dang_nhap_trong_app_fb(snap):
                self.log('⚠️ Phát hiện vẫn đang đăng nhập trong Facebook (chưa đăng xuất) -> Thoát bước Gỡ để đi tìm nút 3 gạch Đăng xuất!')
                return False

            if self._bam_luc_khac_neu_co(snap=snap):
                so_vong_khong_thao_tac = 0
                time.sleep(1.2)
                continue
            if self.tat_quyen_khong_cho_phep(snap=snap):
                so_vong_khong_thao_tac = 0
                time.sleep(1.2)
                continue

            # ===== ĐIỀU KIỆN DỪNG DUY NHẤT: XÁC MINH 2 LẦN LIÊN TIẾP (CÁCH NHAU 2.5s) ĐÃ VỀ FORM ĐĂNG NHẬP TRẮNG 100% =====
            if self._la_man_hinh_dang_nhap_sach_hoan_toan(snap):
                self.log(f'🔎 Đã gỡ {so_trang_da_go} trang -> Chờ 2.5s xác minh màn hình trống ổn định 100%...')
                time.sleep(2.5)
                snap_recheck = self.quet_snapshot()
                if (
                    not snap_recheck['has_progress']
                    and not snap_recheck['is_blank_or_loading']
                    and self._la_man_hinh_dang_nhap_sach_hoan_toan(snap_recheck)
                ):
                    self.log(f'🎉 XÁC NHẬN ĐÃ GỠ XONG BẰNG HẾT {so_trang_da_go} TRANG FB! Sẵn sàng Xóa tab & Xóa dữ liệu nổi!')
                    return True
                snap = snap_recheck

            # ===== ẢNH 10 (BẢNG XÁC NHẬN ĐÁY 'Xóa <Tên> khỏi thiết bị này?') -> ĐỢI ĐỨNG IM 1.0s RỒI BẤM NÚT XANH =====
            if self._snap_has(snap, [
                'xóa khỏi thiết bị này',
                'khỏi thiết bị này?',
                'tin nhắn được mã hóa đầu cuối',
                'remove from this device',
                'lần đăng nhập tiếp theo',
                'bạn sẽ cần nhập email hoặc số di động',
            ]):
                buoc_thu_3_cham = 0
                time.sleep(1.0)
                snap = self.quet_snapshot()
                self.log(f'✅ [Gỡ trang #{so_trang_da_go + 1}] Bấm nút xanh "Xóa khỏi thiết bị này" & chờ FB gỡ xong...')
                prev_sig = snap['sig']
                da_bam_xoa = (
                    self._snap_click(snap, ['Xóa khỏi thiết bị này', 'Remove from this device'], exact=True, click_duoi=True)
                    or self._snap_click(snap, ['Xóa khỏi thiết bị này', 'Xóa khỏi thiết bị', 'Remove from this device'], exact=False, click_duoi=True, min_y=0.55)
                    or self._snap_click(snap, ['Gỡ', 'GỠ', 'Xóa', 'XÓA', 'Remove', 'Delete'], exact=True, click_duoi=True, min_y=0.60)
                )
                if not da_bam_xoa:
                    self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.755))
                so_trang_da_go += 1
                so_vong_khong_thao_tac = 0
                self._cho_giao_dien_xoa_trang_hoan_tat(prev_sig, so_nut_go_truoc=so_nut_go_gan_nhat, timeout=22.0)
                continue

            # ===== ẢNH 8 (BẢNG ĐÁY 'Trang cá nhân') -> ĐỢI ĐỨNG IM 1.0s RỒI BẤM 'Gỡ trang cá nhân khỏi thiết bị này' =====
            node_dong_go_day = self._snap_find(
                snap,
                ['Gỡ trang cá nhân khỏi thiết bị này', 'Remove profiles from this device', 'Remove profile from this device', 'Gỡ tài khoản khỏi thiết bị', 'Gỡ trang cá nhân'],
                exact=False,
                click_duoi=True,
                min_y=0.48
            )
            if node_dong_go_day is not None:
                buoc_thu_3_cham = 0
                time.sleep(1.0)
                snap = self.quet_snapshot()
                node_dong_go_day = self._snap_find(
                    snap,
                    ['Gỡ trang cá nhân khỏi thiết bị này', 'Remove profiles from this device', 'Remove profile from this device', 'Gỡ tài khoản khỏi thiết bị', 'Gỡ trang cá nhân'],
                    exact=False,
                    click_duoi=True,
                    min_y=0.48
                )
                if node_dong_go_day is not None:
                    self.log('📋 [Ảnh 8] Bấm "Gỡ trang cá nhân khỏi thiết bị này"...')
                    prev_sig = snap['sig']
                    self.click_toa_do_an_toan(node_dong_go_day['cx'], node_dong_go_day['cy'])
                    so_vong_khong_thao_tac = 0
                    self._cho_chuyen_man_hinh(prev_sig, timeout=5.0)
                    time.sleep(1.8)
                continue

            # ===== ẢNH 9 (DANH SÁCH CÁC TRANG CÁ NHÂN) -> ĐỢI 1.0s RỒI BẤM TỪNG NÚT 'Gỡ' MỘT CÁCH TỪ TỐN =====
            dang_o_ds_go = self._snap_has(snap, [
                'gỡ trang cá nhân khỏi thiết bị này',
                'remove profiles from this device',
                'remove profile from this device',
                'quản lý trang cá nhân',
                'manage profiles',
            ])
            cac_nut_go = [
                n for n in snap['nodes']
                if (n['text_low'] in {'gỡ', 'remove'} or n['desc_low'] in {'gỡ', 'remove'})
                and int(h * 0.12) <= n['cy'] <= int(h * 0.93)
            ]
            if dang_o_ds_go and cac_nut_go:
                buoc_thu_3_cham = 0
                time.sleep(1.0)
                snap = self.quet_snapshot()
                cac_nut_go = [
                    n for n in snap['nodes']
                    if (n['text_low'] in {'gỡ', 'remove'} or n['desc_low'] in {'gỡ', 'remove'})
                    and int(h * 0.12) <= n['cy'] <= int(h * 0.93)
                ]
                if not cac_nut_go:
                    continue
                cac_nut_go.sort(key=lambda n: n['cy'])
                so_nut_go_gan_nhat = len(cac_nut_go)
                nut_dau = cac_nut_go[0]
                self.log(f'👤 [Ảnh 9 - Đã gỡ {so_trang_da_go}] Còn {len(cac_nut_go)} trang -> Bấm từ từ nút "Gỡ" ({nut_dau["cx"]}, {nut_dau["cy"]})...')
                prev_sig = snap['sig']
                self.click_toa_do_an_toan(nut_dau['cx'], nut_dau['cy'])
                so_vong_khong_thao_tac = 0
                self._cho_chuyen_man_hinh(prev_sig, timeout=5.0)
                time.sleep(1.6)
                continue

            if dang_o_ds_go:
                buoc_thu_3_cham = 0
                self.log('⏳ Chờ danh sách "Gỡ trang cá nhân" cập nhật xong hoàn toàn...')
                da_thay_thay_doi = False
                for _ in range(7):
                    time.sleep(1.0)
                    snap_chk_ds = self.quet_snapshot()
                    if self._la_man_hinh_dang_nhap_sach_hoan_toan(snap_chk_ds):
                        time.sleep(2.0)
                        if self._la_man_hinh_dang_nhap_sach_hoan_toan(self.quet_snapshot()):
                            self.log(f'🎉 XÁC NHẬN ĐÃ GỠ XONG BẰNG HẾT {so_trang_da_go} TRANG FB!')
                            return True
                    nut_go_sau = [
                        n for n in snap_chk_ds['nodes']
                        if (n['text_low'] in {'gỡ', 'remove'} or n['desc_low'] in {'gỡ', 'remove'})
                        and int(h * 0.12) <= n['cy'] <= int(h * 0.93)
                    ]
                    if nut_go_sau:
                        da_thay_thay_doi = True
                        break
                    if not self._snap_has(snap_chk_ds, ['gỡ trang cá nhân', 'remove profile', 'quản lý trang cá nhân']):
                        da_thay_thay_doi = True
                        break
                if da_thay_thay_doi:
                    continue

                self.log('📜 Cuộn chậm kiểm tra cuối danh sách rồi bấm Back về kiểm tra màn hình chờ...')
                self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.76), int(w * 0.50), int(h * 0.28), 340)
                time.sleep(1.3)
                snap_sau_cuon = self.quet_snapshot()
                if any((n['text_low'] in {'gỡ', 'remove'} or n['desc_low'] in {'gỡ', 'remove'}) and int(h * 0.12) <= n['cy'] <= int(h * 0.93) for n in snap_sau_cuon['nodes']):
                    continue
                try:
                    self.d.press('back')
                except Exception:
                    self.chay_shell_nhanh('input keyevent 4')
                time.sleep(2.0)
                so_vong_khong_thao_tac += 1
                if so_vong_khong_thao_tac >= 5:
                    break
                continue

            # ===== ẢNH 7 (MÀN HÌNH CHỜ 1 HOẶC NHIỀU TRANG FB) -> MỖI VÒNG CHỈ BẤM ĐÚNG 1 ĐIỂM, ĐỢI 2.0s RỒI MỚI THỬ TIẾP =====
            if self._co_dau_hieu_con_trang_fb_luu(snap):
                so_nut_go_gan_nhat = 0
                time.sleep(0.9)
                snap = self.quet_snapshot()

                # Xây dựng danh sách điểm bấm ưu tiên (chỉ chọn ĐÚNG 1 điểm ứng với buoc_thu_3_cham!)
                cac_diem_menu = []
                node_menu_top = self._snap_find(
                    snap,
                    ['Tùy chọn khác', 'More options', 'Tùy chọn', 'Cài đặt', 'Settings', 'Quản lý trang cá nhân', 'Menu'],
                    exact=False,
                    min_x=0.68,
                    max_y=0.26
                )
                if node_menu_top is not None:
                    cac_diem_menu.append((f'nút "{node_menu_top["text"] or node_menu_top["desc"]}"', node_menu_top['cx'], node_menu_top['cy']))

                for n in snap['nodes']:
                    if n['clickable'] and n['cx'] >= int(w * 0.78) and int(h * 0.03) <= n['cy'] <= int(h * 0.22) and n['bw'] <= int(w * 0.26):
                        cac_diem_menu.append(('nút 3 chấm góc trên phải', n['cx'], n['cy']))
                        break

                cac_diem_menu += [
                    ('tọa độ 3 chấm cao (91.5%, 7.5%)', int(w * 0.915), int(h * 0.075)),
                    ('tọa độ 3 chấm giữa (91.5%, 10.5%)', int(w * 0.915), int(h * 0.105)),
                    ('tọa độ 3 chấm thấp (91.5%, 14.0%)', int(w * 0.915), int(h * 0.140)),
                    ('tọa độ 3 chấm dưới (91.5%, 17.0%)', int(w * 0.915), int(h * 0.170)),
                ]

                row_dots = [
                    n for n in snap['nodes']
                    if n['clickable'] and n['cx'] >= int(w * 0.78) and int(h * 0.22) <= n['cy'] <= int(h * 0.80) and n['bw'] <= int(w * 0.22)
                ]
                if row_dots:
                    row_dots.sort(key=lambda n: n['cy'])
                    cac_diem_menu.append(('nút 3 chấm bên cạnh dòng tài khoản', row_dots[0]['cx'], row_dots[0]['cy']))

                if buoc_thu_3_cham >= len(cac_diem_menu):
                    buoc_thu_3_cham = 0
                    so_vong_khong_thao_tac += 1
                    if so_vong_khong_thao_tac >= 3:
                        break

                mo_ta_pt, tx, ty = cac_diem_menu[buoc_thu_3_cham]
                self.log(f'⋮ [Ảnh 7 - Đã gỡ {so_trang_da_go}] Bấm chậm 1 phát vào {mo_ta_pt} ({tx}, {ty}) & đợi 2.0s...')
                self.click_toa_do_an_toan(tx, ty)
                buoc_thu_3_cham += 1
                time.sleep(2.0)
                continue

            so_vong_khong_thao_tac += 1
            if so_vong_khong_thao_tac >= 6:
                break
            time.sleep(1.2)

        # Kiểm tra chốt lần cuối: CHỈ trả về True nếu màn hình thực sự đã trống hoàn toàn!
        time.sleep(2.0)
        snap_cuoi = self.quet_snapshot()
        if not snap_cuoi['has_progress'] and self._la_man_hinh_dang_nhap_sach_hoan_toan(snap_cuoi):
            self.log(f'🎉 XÁC NHẬN ĐÃ GỠ XONG HẾT {so_trang_da_go} TRANG FB!')
            return True

        self.log(f'⚠️ CHƯA XÁC NHẬN GỠ XONG HẾT TRANG FB (đã gỡ {so_trang_da_go} trang, màn hình chưa về form trống)!')
        return False

    def xoa_du_lieu_dong_tab_va_mo_lai_fb_sach(self, mo_lai_fb=True, tat_bat_4g=True, bo_qua_cooldown_4g=True, kiem_tra_go_het_truoc=True):
        """
        Quy trình dọn sạch CHẬM MÀ CHẮC — MẶC ĐỊNH XÓA DỮ LIỆU NỔI (CHẠY ĐƯỢC MỌI ĐIỆN THOẠI, KHÔNG CẦN XÓA NGẦM):
        0. CHỐT AN TOÀN: Nếu `kiem_tra_go_het_truoc=True` trên User 0 và vẫn thấy còn trang FB đang hiện/chưa gỡ xong
           -> BẮT BUỘC CHỜ GỠ XONG BẰNG HẾT RỒI MỚI ĐƯỢC XÓA TAB & XÓA DỮ LIỆU!
        1. Đóng sạch tab Facebook trong Đa nhiệm (hỗ trợ mọi hãng điện thoại).
        2. XÓA DỮ LIỆU NỔI: Mở Thông tin ứng dụng Facebook trên màn hình -> Lưu trữ (nếu có) -> Xóa dữ liệu -> Xóa tất cả dữ liệu -> OK -> Đóng tab Cài đặt.
           (Chỉ dùng `pm clear` ngầm nếu người dùng tự tắt `xoa_du_lieu_noi` trong Cấu hình).
        3. TẮT / BẬT 4G đổi IP sạch.
        4. Cấp sẵn quyền bộ nhớ & bật lại Facebook sạch (nếu `mo_lai_fb=True`).
        """
        if kiem_tra_go_het_truoc and self.user_id == 0:
            snap_pre = self.quet_snapshot()
            if self._co_dau_hieu_con_trang_fb_luu(snap_pre) or snap_pre['has_progress'] or self._snap_has(snap_pre, ['đang xóa', 'đang gỡ', 'đang đăng xuất']):
                self.log('🛑 Phát hiện trang FB chưa gỡ xong -> Chờ gỡ bằng hết TRƯỚC khi xóa dữ liệu!')
                da_go_het = self._go_trang_ca_nhan_ngoai_man_hinh_cho()
                if not da_go_het:
                    self.log('⛔ CHƯA GỠ XONG HẾT TRANG FB -> TẠM HỦY BƯỚC XÓA DỮ LIỆU (tránh xóa dữ liệu sớm)!')
                    return False

        # Chờ 1.5s bảo đảm Facebook đã lưu xong trạng thái gỡ trang
        time.sleep(1.5)

        self.log('🧹 [1/3] Đóng sạch tab Facebook trong Đa nhiệm...')
        self.dong_sach_tab_da_nhiem(force_stop_fb=True)

        dung_xoa_noi = True if self.config is None else bool(self.config.get('xoa_du_lieu_noi', True))
        if dung_xoa_noi:
            self.log('🗑️ [2/3] Chạy XÓA DỮ LIỆU NỔI trực tiếp qua Thông tin ứng dụng (chạy được mọi điện thoại)...')
            self.xoa_tat_ca_du_lieu_fb_qua_cai_dat()
        else:
            self.log('🗑️ [2/3] Chạy xóa dữ liệu ngầm qua ADB...')
            pm_ok = xoa_du_lieu_fb(self.serial, user_id=self.user_id)
            if not pm_ok and self.user_id == 0:
                self.xoa_tat_ca_du_lieu_fb_qua_cai_dat()

        self.xoa_sach_tu_dong_dien_va_khoa_truy_cap(cho_phep_mo_cai_dat_noi=dung_xoa_noi)
        lam_moi_thong_so_thiet_bi_adb(self.serial, self.config, user_id=self.user_id)
        khoa_xoay_man_hinh(self.serial, user_id=self.user_id)
        cap_quyen_bo_nho_fb(self.serial, user_id=self.user_id)

        if tat_bat_4g:
            self.log('📶 [3/3] Tắt / Bật 4G để đổi IP sạch sau khi xóa dữ liệu...')
            tat_bat_4g_doi_ip_adb(self.serial, self.device_name, self.config, bo_qua_cooldown=bo_qua_cooldown_4g)

        if mo_lai_fb:
            self.log('🚀 Bật lại Facebook sạch sẽ như mới...')
            self._mo_app_fb_theo_user()
            nghi_ngau_nhien(self.config.get('delay_mo_lai_fb', 6.0), 0.1)
            self.cho_va_dong_lop_phu_sau_mo_fb(thoi_gian_quet=4.0)
            self.xu_ly_man_hinh_dieu_khoan_meta()
            self._bam_luc_khac_neu_co()
            self.tat_quyen_khong_cho_phep()
            self.dong_goi_y_google()
            self.log('✨ Facebook đã sạch sẽ như mới!')
        return True

    def dang_xuat_va_go_trang_ca_nhan(self, thoat_tab_truoc=False, xoa_data_truoc=False, xoa_data_dong_tab_cuoi=True, mo_lai_fb_cuoi=True, tat_bat_4g_cuoi=True):
        """
        Thực hiện chuẩn quy trình CHẬM MÀ CHẮC:
        Đăng xuất -> CHỜ ĐĂNG XUẤT XONG -> Gỡ bằng hết mọi trang FB -> CHỜ GỠ XONG 100% -> Xóa tab FB -> Xóa dữ liệu NỔI -> Tắt/Bật 4G.
        """
        w, h = self.d.window_size()

        if xoa_data_truoc:
            self.log('🧹 [Bước 1] Đóng sạch tab & xóa dữ liệu nổi rồi mở lại FB kiểm tra...')
            self.dong_sach_tab_da_nhiem(force_stop_fb=True)
            if self.config is None or self.config.get('xoa_du_lieu_noi', True):
                self.xoa_tat_ca_du_lieu_fb_qua_cai_dat()
            else:
                pm_ok_b1 = xoa_du_lieu_fb(self.serial, user_id=self.user_id)
                if self.user_id == 0 and not pm_ok_b1:
                    self.xoa_tat_ca_du_lieu_fb_qua_cai_dat()
            khoa_xoay_man_hinh(self.serial, user_id=self.user_id)
            cap_quyen_bo_nho_fb(self.serial, user_id=self.user_id)
            self._mo_app_fb_theo_user()
            nghi_ngau_nhien(self.config.get('delay_mo_facebook', 7.5), 0.1)
        elif thoat_tab_truoc:
            self.dong_tab_va_mo_lai_fb_giu_nick()

        # Đóng ngay lớp phủ SignInCredentialChooserActivity / HiddenActivity nếu vừa bật FB lên bị che
        self.cho_va_dong_lop_phu_sau_mo_fb(thoi_gian_quet=3.5)

        # Quét chậm rãi Bảng Google Play (×), 'Lúc khác', 'KHÔNG CHO PHÉP' cho tới khi vào hẳn màn hình chính sạch sẽ
        for _ in range(8):
            self.dam_bao_fb_dang_chay(max_retry=2, cho_len_giay=5.0)
            if self.dong_bang_google_play_tai_bo_sung():
                time.sleep(1.0)
                continue
            if self.xu_ly_man_hinh_dieu_khoan_meta():
                time.sleep(1.0)
                continue
            if self.bo_qua_luu_thong_tin_dang_nhap():
                time.sleep(1.2)
                continue
            if self.tat_quyen_khong_cho_phep():
                time.sleep(1.2)
                continue
            if self.quet_va_xoa_man_hinh_chan(so_vong_quet=2):
                time.sleep(1.0)
                continue
            if self.kiem_tra_text([
                'Bạn đang nghĩ gì', 'Tạo tin', 'Tìm bạn bè từ danh bạ',
                'Dùng trang cá nhân khác', 'Dùng tài khoản khác',
                'Gỡ trang cá nhân khỏi thiết bị này', 'Xóa khỏi thiết bị này',
                'Số di động hoặc email', 'Tạo tài khoản mới'
            ], 1, 0.35):
                break
            time.sleep(1.0)

        # Đảm bảo đã đóng sạch bảng Google Play trước khi xác định trạng thái màn hình
        snap_dx_chk = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Kiểm tra trạng thái trước Đăng xuất', check_die=False)
        if self.dong_bang_google_play_tai_bo_sung(snap=snap_dx_chk):
            time.sleep(0.8)
            snap_dx_chk = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Sau đóng Google Play', check_die=False)

        # Chỉ bấm nút phụ 'Xong' / 'Done' khi KHÔNG đứng trên Bảng tin chính (tránh bấm nhầm dấu × gợi ý bạn bè)
        if not self._dang_dang_nhap_trong_app_fb(snap_dx_chk):
            for nut_phu in ['Xong', 'Done']:
                if self._snap_click(snap_dx_chk, [nut_phu], exact=True):
                    time.sleep(1.0)
                    snap_dx_chk = self.quet_snapshot()

        # Nếu FB đã hoàn toàn trống (không còn bất kỳ trang cá nhân nào) -> chuyển sang Xóa tab -> Xóa dữ liệu nổi -> Tắt bật 4G
        if self._la_man_hinh_dang_nhap_sach_hoan_toan(snap_dx_chk):
            self.log('✅ Facebook đã ở màn hình đăng nhập trống (không còn trang cá nhân nào)!')
            if xoa_data_dong_tab_cuoi:
                self.xoa_du_lieu_dong_tab_va_mo_lai_fb_sach(
                    mo_lai_fb=mo_lai_fb_cuoi,
                    tat_bat_4g=tat_bat_4g_cuoi,
                    bo_qua_cooldown_4g=True,
                    kiem_tra_go_het_truoc=True
                )
            return True

        # Nếu CHƯA đăng nhập trong FB và đang đứng sẵn ở Ảnh 8/9/10 -> GỠ BẰNG HẾT rồi MỚI Xóa tab -> Xóa dữ liệu nổi -> Tắt bật 4G
        if (not self._dang_dang_nhap_trong_app_fb(snap_dx_chk)) and self._snap_has(
            snap_dx_chk,
            ['Gỡ trang cá nhân khỏi thiết bị này', 'Xóa khỏi thiết bị này', 'lần đăng nhập tiếp theo']
        ):
            da_go_het_ngay = self._go_trang_ca_nhan_ngoai_man_hinh_cho()
            if da_go_het_ngay and xoa_data_dong_tab_cuoi:
                self.xoa_du_lieu_dong_tab_va_mo_lai_fb_sach(
                    mo_lai_fb=mo_lai_fb_cuoi,
                    tat_bat_4g=tat_bat_4g_cuoi,
                    bo_qua_cooldown_4g=True,
                    kiem_tra_go_het_truoc=True
                )
            return da_go_het_ngay

        dang_o_man_cho_anh_7 = (not self._dang_dang_nhap_trong_app_fb(snap_dx_chk)) and self._co_dau_hieu_con_trang_fb_luu(snap_dx_chk)

        if not dang_o_man_cho_anh_7:
            for lan_dx in range(1, 3):
                if STOP_EVENT.is_set():
                    return False
                snap_chk_dx = self.quet_snapshot()
                if self._co_dau_hieu_con_trang_fb_luu(snap_chk_dx) or self._la_man_hinh_dang_nhap_sach_hoan_toan(snap_chk_dx):
                    break

                self.log(f'🚪 [Đăng xuất - Lần {lan_dx}/2] Tìm nút 2 gạch ngang / Menu góc trên cao -> Lướt xuống bấm "Đăng xuất"...')
                time.sleep(0.8)
                da_mo_menu = self._bam_nut_3_gach_goc_trai()
                if not da_mo_menu:
                    self.log('⚡ Chưa mở được Menu bằng nút góc -> Thử mở trực tiếp fb://bookmarks...')
                    self.chay_shell_nhanh(f'am start {self._u_flag()}-a android.intent.action.VIEW -d "fb://bookmarks"')
                    time.sleep(2.4)
                    snap_m = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Chờ mở Menu Đăng xuất', check_die=False)
                    da_mo_menu = self._la_man_hinh_menu_fb(snap_m)

                if not da_mo_menu:
                    self.log(f'⚠️ [Đăng xuất - Lần {lan_dx}/2] Chưa vào được trang Menu -> Mở lại FB rồi thử lại...')
                    self.dong_tab_va_mo_lai_fb_giu_nick()
                    continue

                time.sleep(1.0)

                # Cuộn chậm rãi xuống đáy Menu để tìm chính xác nút 'Đăng xuất' / 'Log out'
                nut_dx_menu = None
                for lan_cuon in range(10):
                    snap_m = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh=f'Cuộn Menu tìm Đăng xuất #{lan_cuon + 1}', check_die=False)
                    if self._bam_luc_khac_neu_co(snap=snap_m):
                        time.sleep(0.8)
                        continue
                    if self._co_dau_hieu_con_trang_fb_luu(snap_m) or self._la_man_hinh_dang_nhap_sach_hoan_toan(snap_m):
                        break
                    nut_dx_menu = (
                        self._snap_find(snap_m, ['Đăng xuất', 'ĐĂNG XUẤT', 'Log out', 'LOG OUT'], exact=True, click_duoi=True, min_y=0.12, max_y=0.95)
                        or self._snap_find(snap_m, ['Đăng xuất', 'Log out'], exact=False, click_duoi=True, min_y=0.12, max_y=0.95)
                    )
                    if nut_dx_menu is not None:
                        break
                    self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.80), int(w * 0.50), int(h * 0.22), 340)
                    time.sleep(0.95)

                if nut_dx_menu is None:
                    self.log('⚠️ Không thấy nút "Đăng xuất" trên Menu -> Thử tải lại fb://bookmarks...')
                    self.chay_shell_nhanh(f'am start {self._u_flag()}-a android.intent.action.VIEW -d "fb://bookmarks"')
                    time.sleep(2.2)
                    continue

                # Đợi cuộn đứng yên hẳn rồi quét lại tọa độ tươi trước khi bấm 'Đăng xuất'
                time.sleep(0.7)
                snap_m_fresh = self.quet_snapshot()
                nut_dx_fresh = (
                    self._snap_find(snap_m_fresh, ['Đăng xuất', 'ĐĂNG XUẤT', 'Log out', 'LOG OUT'], exact=True, click_duoi=True, min_y=0.12, max_y=0.95)
                    or self._snap_find(snap_m_fresh, ['Đăng xuất', 'Log out'], exact=False, click_duoi=True, min_y=0.12, max_y=0.95)
                    or nut_dx_menu
                )
                self.log(f'🚪 [Menu] Bấm nút "{nut_dx_fresh["text"] or nut_dx_fresh["desc"]}" tại ({nut_dx_fresh["cx"]}, {nut_dx_fresh["cy"]})...')
                self.click_toa_do_an_toan(nut_dx_fresh['cx'], nut_dx_fresh['cy'])
                time.sleep(1.8)

                # Vòng lặp chậm rãi xử lý Ảnh 5 ('Lưu thông tin đăng nhập?' -> 'LÚC KHÁC') & Ảnh 6 (Hộp thoại / Bảng đáy xác nhận 'ĐĂNG XUẤT')
                da_dang_xuat_xong = False
                for _ in range(9):
                    snap_cf = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Xác nhận Đăng xuất', check_die=False)

                    if self._co_dau_hieu_con_trang_fb_luu(snap_cf) or self._la_man_hinh_dang_nhap_sach_hoan_toan(snap_cf):
                        da_dang_xuat_xong = True
                        break

                    if snap_cf['has_progress'] or self._snap_has(snap_cf, ['đang đăng xuất', 'logging out', 'signing out']):
                        self._cho_dang_xuat_hoan_tat(timeout=30.0)
                        da_dang_xuat_xong = True
                        break

                    # Bảng 'Lưu thông tin đăng nhập?' -> Bấm 'LÚC KHÁC' / 'Không lưu'
                    if self.bo_qua_luu_thong_tin_dang_nhap(snap=snap_cf):
                        time.sleep(1.6)
                        continue

                    # Hộp thoại giữa màn hình HOẶC Bảng đáy xác nhận 'Đăng xuất khỏi tài khoản của bạn?'
                    la_bang_xac_nhan_dx = (
                        self._snap_has(snap_cf, [
                            'đăng xuất khỏi tài khoản', 'bạn có chắc chắn muốn đăng xuất',
                            'log out of your account', 'are you sure you want to log out',
                            'log out of facebook'
                        ])
                        or self._snap_has(snap_cf, ['ĐĂNG XUẤT', 'LOG OUT'], exact=True)
                        or (
                            self._snap_has(snap_cf, ['Hủy', 'HỦY', 'Cancel', 'CANCEL'], exact=True)
                            and self._snap_has(snap_cf, ['Đăng xuất', 'Log out'], exact=True)
                        )
                    )
                    if la_bang_xac_nhan_dx:
                        time.sleep(0.8)
                        snap_cf = self.quet_snapshot()
                        self.log('🚪 [Ảnh 6] Hiện bảng xác nhận -> Bấm nút "ĐĂNG XUẤT" & chờ đăng xuất xong hẳn...')
                        # Hỗ trợ cả hộp thoại giữa màn hình lẫn bảng đáy (y = 0.25..0.95), chọn nút exact thấp nhất (không bấm nhầm tiêu đề)
                        nut_xn_dx = (
                            self._snap_find(snap_cf, ['ĐĂNG XUẤT', 'LOG OUT'], exact=True, click_duoi=True, min_y=0.25, max_y=0.95)
                            or self._snap_find(snap_cf, ['Đăng xuất', 'Log out'], exact=True, click_duoi=True, min_y=0.25, max_y=0.95)
                            or self._snap_find_rid(snap_cf, ['android:id/button1'])
                        )
                        if nut_xn_dx is not None:
                            self.click_toa_do_an_toan(nut_xn_dx['cx'], nut_xn_dx['cy'])
                        else:
                            self.click_toa_do_an_toan(int(w * 0.71), int(h * 0.535))
                        self._cho_dang_xuat_hoan_tat(timeout=30.0)
                        da_dang_xuat_xong = True
                        break

                    # Nếu vẫn còn đứng nguyên ở Menu (chưa bấm ăn nút Đăng xuất lần 1) -> bấm lại 1 lần
                    if self._la_man_hinh_menu_fb(snap_cf):
                        nut_dx_lai = self._snap_find(snap_cf, ['Đăng xuất', 'ĐĂNG XUẤT', 'Log out', 'LOG OUT'], exact=True, click_duoi=True, min_y=0.12, max_y=0.95)
                        if nut_dx_lai is not None:
                            self.click_toa_do_an_toan(nut_dx_lai['cx'], nut_dx_lai['cy'])
                            time.sleep(1.8)
                            continue

                    time.sleep(1.0)

                if da_dang_xuat_xong:
                    break

        # Gỡ BẰNG HẾT tất cả trang cá nhân FB ngoài màn hình chờ (chậm mà chắc) & CHỜ XÁC NHẬN GỠ XONG 100%
        da_go_xong_het = self._go_trang_ca_nhan_ngoai_man_hinh_cho()
        if not da_go_xong_het:
            self.log('🔄 Chưa xác nhận gỡ xong hết trang FB -> Nghỉ 3.0s & quét gỡ lại thêm 1 vòng...')
            time.sleep(3.0)
            da_go_xong_het = self._go_trang_ca_nhan_ngoai_man_hinh_cho()

        if not da_go_xong_het:
            self.log('⛔ CHƯA GỠ XONG HẾT TRANG FB -> KHÔNG XÓA DỮ LIỆU để tránh mất bước gỡ trang!')
            return False

        # CHỈ KHI ĐÃ XÁC NHẬN GỠ XONG HẾT TRANG FB -> MỚI ĐƯỢC XÓA TAB FB -> XÓA DỮ LIỆU NỔI -> TẮT BẬT 4G!
        if xoa_data_dong_tab_cuoi:
            self.xoa_du_lieu_dong_tab_va_mo_lai_fb_sach(
                mo_lai_fb=mo_lai_fb_cuoi,
                tat_bat_4g=tat_bat_4g_cuoi,
                bo_qua_cooldown_4g=True,
                kiem_tra_go_het_truoc=True
            )
        return True

    def dam_bao_man_hinh_tao_tai_khoan_moi(self):
        """
        Kiểm tra ngay khi vào Facebook:
        - Tự động bấm 'Tiếp tục' nếu hiện màn hình 'Điều khoản và Chính sách quyền riêng tư của Meta'.
        - Quét thấy 'Lúc khác' (Ảnh 1) -> Bấm 'Lúc khác'; thấy hỏi quyền thông báo (Ảnh 2) -> Bấm 'KHÔNG CHO PHÉP'.
        - Trên User 0: kiểm tra dấu hiệu tự đăng nhập / kẹt nick cũ (Ảnh 3, Ảnh 7...) TRƯỚC khi coi là sạch;
          nếu bị dính nick cũ sẽ tự chạy trọn bộ Đăng xuất -> Gỡ trang cá nhân -> Xóa dữ liệu & đóng tab -> Mở lại FB sạch.
        """
        dau_hieu_san_sang = [
            'Tạo tài khoản mới',
            'Create new account',
            'Tham gia Facebook',
            'Join Facebook',
            'Bắt đầu',
            'Get started',
            'Bạn tên gì',
            "What's your name"
        ]
        dau_hieu_ket_nick_cu = [
            'Bạn đang nghĩ gì',
            'Tạo tin',
            'Tin của bạn',
            'Tìm bạn bè từ danh bạ',
            'đã giúp bạn đăng nhập vào Facebook',
            'Gỡ trang cá nhân khỏi thiết bị này',
            'Xóa khỏi thiết bị này',
            'Dùng trang cá nhân khác',
            'Dùng tài khoản khác',
            'Use another account'
        ]
        self.cho_va_dong_lop_phu_sau_mo_fb(thoi_gian_quet=3.5)
        so_vong_cho = 12 if self.user_id > 0 else 10
        for _ in range(so_vong_cho):
            self.dam_bao_fb_dang_chay(max_retry=2, cho_len_giay=5.0)
            if self.xu_ly_man_hinh_dieu_khoan_meta():
                continue
            if self.bo_qua_luu_thong_tin_dang_nhap():
                time.sleep(0.8)
                continue
            if self.tat_quyen_khong_cho_phep():
                time.sleep(0.8)
                continue

            # Trên User 0 phải kiểm tra kẹt nick cũ / màn hình Ảnh 7 TRƯỚC (vì Ảnh 7 cũng có nút 'Tạo tài khoản mới')
            if self.user_id == 0 and self.kiem_tra_text(dau_hieu_ket_nick_cu, 1, 0.25):
                break

            if self.kiem_tra_text(dau_hieu_san_sang, 1, 0.3):
                return True

            time.sleep(0.8)

        if self.xu_ly_man_hinh_dieu_khoan_meta():
            time.sleep(1.5)

        if self.user_id == 0 and self.kiem_tra_text(dau_hieu_ket_nick_cu, 1, 0.3):
            self.log('⚠️ Phát hiện Facebook tự động đăng nhập / dính nick cũ -> Chạy quy trình Đăng xuất & Gỡ sạch khỏi thiết bị...')
            self.dang_xuat_va_go_trang_ca_nhan(
                thoat_tab_truoc=False,
                xoa_data_truoc=False,
                xoa_data_dong_tab_cuoi=True,
                mo_lai_fb_cuoi=True
            )
            return True

        if self.kiem_tra_text(dau_hieu_san_sang, 1, 0.3):
            return True

        self.log('🔄 Chưa thấy nút Tạo tài khoản mới -> Gọi mở lại Facebook & kiểm tra Điều khoản Meta...')
        self._mo_app_fb_theo_user()
        time.sleep(3.5)
        self.xu_ly_man_hinh_dieu_khoan_meta()
        self.bo_qua_luu_thong_tin_dang_nhap()
        self.tat_quyen_khong_cho_phep()
        return True

    def _mo_menu_khong_nhan_duoc_ma_otp(self):
        """
        Quét chữ động (0% tọa độ cố định) để mở bảng đáy 'Tôi không nhận được mã' trên màn hình Nhập mã xác nhận.
        Trả về snapshot mới nhất của bảng đáy (hoặc màn hình hiện tại).
        """
        dau_hieu_bang_day = [
            'Gửi lại mã đến SMS', 'Gửi lại mã qua SMS', 'Gửi lại mã đến email', 'Gửi lại mã qua email',
            'Đổi số di động', 'Thay đổi số di động', 'Đổi địa chỉ email', 'Thay đổi địa chỉ email', 'Đổi email',
            'Resend code via SMS', 'Resend code via email', 'Change mobile number', 'Change email address', 'Change email'
        ]
        self._ha_ban_phim_an_toan()
        snap = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Mở menu Tôi không nhận được mã')
        if self._snap_has(snap, dau_hieu_bang_day):
            return snap

        prev_sig = snap['sig']
        nhan_btn = self._tim_va_bam_chu_dong(
            snap,
            [
                'Tôi không nhận được mã',
                'Không nhận được mã',
                "I didn't get the code",
                'I didn’t get the code',
                "I didn't receive the code",
                'Didn’t get a code',
                "Didn't get a code",
                'Gửi lại mã',
                'Resend code',
            ],
            exclude_keywords=['đăng xuất', 'log out'],
            min_y=0.20,
            max_y=0.95
        )
        if nhan_btn:
            self.log(f'📩 [OTP - Quét chữ] Bấm "{nhan_btn}"...')
            self._cho_chuyen_man_hinh(prev_sig, timeout=3.5)
            time.sleep(0.7)
            snap = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Chờ bảng đáy OTP hiện ra')
        return snap

    def _bam_gui_lai_ma_otp(self, la_che_do_sms=False):
        """
        Quét chữ động (0% tọa độ cố định):
        1. Bấm 'Tôi không nhận được mã'
        2. Tùy chế độ SMS hay Email mà bấm đúng mục 'Gửi lại mã đến SMS' hoặc 'Gửi lại mã đến email'
        """
        snap_sheet = self._mo_menu_khong_nhan_duoc_ma_otp()
        if la_che_do_sms:
            ds_gui_lai = [
                'Gửi lại mã đến SMS',
                'Gửi lại mã qua SMS',
                'Gửi mã qua SMS',
                'Nhận mã qua SMS',
                'Resend code via SMS',
                'Send code via SMS',
                'Resend SMS',
                'Gửi lại mã',
                'Gửi lại',
                'Nhận mã mới',
                'Resend code',
            ]
            loai_tru = [
                'email', 'thư điện tử', 'đổi số', 'thay đổi số', 'change mobile', 'change phone',
                'xác nhận bằng email', 'đăng xuất', 'log out', 'whatsapp'
            ]
        else:
            ds_gui_lai = [
                'Gửi lại mã đến email',
                'Gửi lại mã qua email',
                'Gửi mã qua email',
                'Gửi lại email',
                'Gửi lại mã đến địa chỉ email',
                'Resend code via email',
                'Send code via email',
                'Resend email',
                'Gửi lại mã',
                'Gửi lại',
                'Nhận mã mới',
                'Resend code',
            ]
            loai_tru = [
                'sms', 'tin nhắn', 'số di động', 'đổi địa chỉ', 'đổi email', 'thay đổi email',
                'change email', 'xác nhận bằng số', 'đăng xuất', 'log out', 'whatsapp'
            ]

        prev_sig = snap_sheet['sig']
        nhan_gl = self._tim_va_bam_chu_dong(
            snap_sheet,
            ds_gui_lai,
            exclude_keywords=loai_tru,
            min_y=0.15,
            max_y=0.95
        )
        if nhan_gl:
            che_do_txt = 'SMS' if la_che_do_sms else 'Email'
            self.log(f'🔄 [Spam OTP {che_do_txt}] Đã bấm "{nhan_gl}" -> Đợi phản hồi & check mã...')
            self._cho_chuyen_man_hinh(prev_sig, timeout=3.5)
            time.sleep(1.2)
            snap_ok = self.quet_snapshot()

            # Kiểm tra Facebook báo chặn cứng không cho gửi lại mã cho số/mail này nữa
            dau_hieu_chan_cung = [
                'đã yêu cầu quá nhiều mã', 'yêu cầu quá nhiều mã', 'gửi quá nhiều mã',
                'quá nhiều yêu cầu', 'quá nhiều lần', 'không thể gửi mã đến số này',
                'không thể gửi mã đến', 'không thể gửi tin nhắn', 'thử số khác', 'thử số di động khác',
                'too many codes', 'too many requests', 'too many attempts',
                'cannot send code', "couldn't send code", 'couldn’t send code',
                'unable to send', 'try another number', 'limit reached'
            ]
            dau_hieu_cho_tam = [
                'đợi một lát', 'đợi vài giây', 'đợi vài phút', 'chờ một lát', 'chờ một chút',
                'vui lòng đợi trước khi', 'thử lại sau vài', 'thử lại sau',
                'wait a moment', 'wait a few', 'please wait before', 'try again in', 'try again later'
            ]
            la_chan_cung = self._snap_has(snap_ok, dau_hieu_chan_cung)
            la_cho_tam = (not la_chan_cung) and self._snap_has(snap_ok, dau_hieu_cho_tam)

            if self._snap_has(snap_ok, ['OK', 'Đóng', 'Close'], exact=True) and (
                la_chan_cung or la_cho_tam or self._snap_has(snap_ok, ['đã gửi', 'sent', 'mã mới', 'new code', 'lỗi', 'error'])
            ):
                self._tim_va_bam_chu_dong(snap_ok, ['OK', 'Đóng', 'Close'], min_y=0.25, max_y=0.90)
                time.sleep(0.5)

            if la_chan_cung:
                self.log(f'🚫 [Spam OTP {che_do_txt}] Facebook báo giới hạn/không thể gửi thêm mã cho liên hệ này -> Chuẩn bị đổi số/mail mới!')
                return 'BLOCKED'
            if la_cho_tam:
                self.log(f'⏳ [Spam OTP {che_do_txt}] Facebook yêu cầu đợi một chút trước lần gửi tiếp -> Giữ nguyên đơn & tiếp tục check OTP!')
                return 'COOLDOWN'
            return 'SENT'

        self.log('⚠️ [OTP] Không tìm thấy nút Gửi lại mã phù hợp trên bảng tùy chọn!')
        return 'NO_BTN'

    def _bam_doi_sdt_hoac_email_tu_otp(self, la_che_do_sms=False):
        """
        Khi đã gửi lại mã nhưng mãi vẫn không có OTP về (0% tọa độ cố định):
        1. Bấm 'Tôi không nhận được mã'
        2. Quét chữ bấm 'Đổi số di động' (chế độ SMS) hoặc 'Đổi địa chỉ email' / 'Đổi email' (chế độ Email)
        Trả về True nếu đã bấm và rời khỏi bảng đáy / màn hình Nhập mã xác nhận thành công.
        """
        snap_sheet = self._mo_menu_khong_nhan_duoc_ma_otp()
        if la_che_do_sms:
            ds_doi = [
                'Đổi số di động',
                'Thay đổi số di động',
                'Đổi số điện thoại',
                'Thay đổi số điện thoại',
                'Cập nhật số di động',
                'Change mobile number',
                'Change phone number',
                'Update mobile number',
            ]
            loai_tru = ['email', 'gửi lại', 'resend', 'xác nhận bằng', 'đăng xuất', 'log out']
        else:
            ds_doi = [
                'Đổi địa chỉ email',
                'Thay đổi địa chỉ email',
                'Đổi email',
                'Thay đổi email',
                'Cập nhật địa chỉ email',
                'Cập nhật email',
                'Change email address',
                'Change email',
                'Update email address',
                'Update email',
            ]
            loai_tru = ['sms', 'số di động', 'gửi lại', 'resend', 'xác nhận bằng', 'đăng xuất', 'log out']

        prev_sig = snap_sheet['sig']
        nhan_doi = self._tim_va_bam_chu_dong(
            snap_sheet,
            ds_doi,
            exclude_keywords=loai_tru,
            min_y=0.15,
            max_y=0.95
        )
        if not nhan_doi:
            self.log(f'⚠️ [OTP] Không thấy mục "{"Đổi số di động" if la_che_do_sms else "Đổi địa chỉ email"}" trên màn hình!')
            return False

        self.log(f'🔀 [OTP - Quét chữ] Đã bấm "{nhan_doi}" -> Chuyển sang màn hình nhập {"SĐT" if la_che_do_sms else "Email"} mới...')
        self._cho_chuyen_man_hinh(
            prev_sig,
            timeout=6.0,
            old_screen_keywords=[
                'Gửi lại mã đến SMS', 'Gửi lại mã đến email',
                'Resend code via SMS', 'Resend code via email',
                'Nhập mã xác nhận', 'Confirmation code'
            ]
        )
        time.sleep(0.8)
        return True

    def lay_otp_theo_che_do(self, mode, used_email, mail_service=None, imap_service=None, hotmail_service=None, uid_moc=0, force_8_digits=False, expected_digits=None, wait_timeout=None, max_resend_attempts=2):
        if force_8_digits and not expected_digits:
            expected_digits = 8
        loai_otp_str = f"{expected_digits} số bảo mật" if expected_digits in (6, 8) else "xác nhận"
        to_mail_tm = int(wait_timeout) if wait_timeout else 95
        to_imap = int(wait_timeout) if wait_timeout else 95
        to_hotmail = int(wait_timeout) if wait_timeout else 110

        for attempt in range(max_resend_attempts + 1):
            if STOP_EVENT.is_set():
                return None

            otp_code = None
            if mode == "2" and not (mail_service and mail_service.token):
                with OTP_LOCK:
                    PAUSE_FOR_INPUT.clear()
                    try:
                        built_in_print(f"\n{Colors.color_text(f'[{self.device_name}] Lần {attempt+1}: NHẬP MÃ OTP ({loai_otp_str}) CHO [{used_email}]: ', Colors.SUCCESS)}", end="")
                        otp_code = input().strip()
                    finally:
                        PAUSE_FOR_INPUT.set()
            elif mode == "1" or (mode == "2" and mail_service and mail_service.token):
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Mail.tm (Lần {attempt+1}/{max_resend_attempts+1}, tối đa {to_mail_tm}s)...')
                otp_code = mail_service.get_otp_code(timeout=to_mail_tm, force_8_digits=force_8_digits, expected_digits=expected_digits)
            elif mode in ["3", "4"] and imap_service:
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Gmail IMAP (Lần {attempt+1}/{max_resend_attempts+1}, tối đa {to_imap}s)...')
                otp_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=to_imap, force_8_digits=force_8_digits, expected_digits=expected_digits)
            elif mode == "5" and hotmail_service:
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Smail1s (Lần {attempt+1}/{max_resend_attempts+1}, tối đa {to_hotmail}s)...')
                otp_code = hotmail_service.get_otp_code(timeout=to_hotmail, force_8_digits=force_8_digits, expected_digits=expected_digits)

            if otp_code:
                self.log(f'🔢 ĐÃ LẤY ĐƯỢC OTP ({loai_otp_str}): {otp_code}')
                return otp_code

            self.kiem_tra_va_dung_neu_die(f'Chờ OTP Email lần {attempt+1}')

            if attempt < max_resend_attempts:
                self.log(f'⚠️ Chưa có OTP Email (Lần {attempt+1}/{max_resend_attempts+1}) -> Spam bấm "Tôi không nhận được mã" -> Gửi lại qua Email...')
                kq_gl_em = self._bam_gui_lai_ma_otp(la_che_do_sms=False)
                if kq_gl_em == 'BLOCKED':
                    self.log('🚫 Facebook chặn gửi thêm mã Email này -> Dừng spam để chuyển sang đổi Email mới!')
                    break
                time.sleep(2.0 if kq_gl_em == 'SENT' else 5.0)

        self.log(f'❌ Không lấy được OTP ({loai_otp_str}) sau {max_resend_attempts + 1} lần chờ!')
        return None

    def trich_xuat_key_2fa_tu_man_hinh(self, snap=None):
        """
        Trích xuất dòng code 2FA (VD: VAEI HQNR I2PH Z4HZ XV3D IN3M BKL4 6IAS) ở Hình 3:
        1. Đọc trực tiếp từ snapshot XML (không gọi lại dump_hierarchy nếu đã có snap)
        2. Nếu cần sẽ bấm Sao chép khóa để lấy từ Clipboard
        """
        try:
            xml_dump = snap['raw_xml'] if (snap and snap.get('raw_xml')) else self.d.dump_hierarchy()
            cac_chuoi = re.findall(r'(?:text|content-desc)="([^"]+)"', xml_dump)
            for s in cac_chuoi:
                s_clean = s.strip()
                m_group = re.search(r'\b(?:[A-Z2-7]{4}[\s-]+){3,7}[A-Z2-7]{4}\b', s_clean.upper())
                if m_group:
                    key_cand = lam_sach_key_2fa(m_group.group(0))
                    if 16 <= len(key_cand) <= 64:
                        return key_cand

                if re.fullmatch(r'[A-Z2-7\s-]{16,45}', s_clean):
                    key_cand = lam_sach_key_2fa(s_clean)
                    if len(key_cand) in [16, 24, 32] and any(c.isalpha() for c in key_cand):
                        return key_cand
        except Exception:
            pass

        try:
            for nut_copy in ['Sao chép khóa', 'Copy key', 'Sao chép mã', 'Sao chép', 'Copy']:
                if self.d(textContains=nut_copy).exists or self.d(descriptionContains=nut_copy).exists:
                    self.click_text_chua(nut_copy, nut_copy, 1, 0.4)
                    time.sleep(0.8)
                    clip_text = ""
                    try:
                        clip_text = self.d.clipboard or ""
                    except Exception:
                        pass
                    if not clip_text:
                        clip_text = chay_lenh_adb_lay_ket_qua('shell cmd clipboard get-text', self.serial)
                    clean_clip = lam_sach_key_2fa(clip_text)
                    if 16 <= len(clean_clip) <= 64:
                        return clean_clip
        except Exception:
            pass

        return None

    def _kiem_tra_va_xu_ly_loi_mang_2fa(self, snap=None):
        """
        Kiểm tra lỗi tải trang tại chỗ (TUYỆT ĐỐI KHÔNG tắt/bật Wi-Fi hay 4G, KHÔNG thoát Facebook):
        - Ưu tiên bấm nút 'Thử lại' / 'Tải lại' / 'Try again' ngay trên màn hình để giữ nguyên ngữ cảnh.
        - Chỉ bấm Back 1 bước nếu đúng là trang lỗi cụt 'Error Facebook / Sự cố tải'.
        """
        s = snap if snap is not None else self.quet_snapshot()
        if not s or s.get('is_blank_or_loading'):
            return False

        # Không kích hoạt nhầm nếu màn hình đang có form nhập hoặc màn 2FA hợp lệ
        if s.get('edit_texts') or self._la_man_hinh_qr_key_2fa(s):
            return False

        dau_hieu_loi_chac_chan = [
            'error facebook',
            'sự cố tải',
            'nhấn để thử lại',
            'không có kết nối',
            'không thể kết nối',
            'không thể tải',
            'đã xảy ra lỗi',
            'lỗi kết nối',
            'no internet',
            'connection lost',
            'something went wrong',
            'trang này không hiển thị',
        ]
        if not self._snap_has(s, dau_hieu_loi_chac_chan):
            return False

        self.log('🌐 [Xử lý tại chỗ] Phát hiện lỗi tải trang -> Thử tải lại tại chỗ (không tắt Wi-Fi/FB)...')
        # Ưu tiên bấm nút Thử lại / Tải lại ngay tại chỗ trước
        if self._snap_click(s, ['Thử lại', 'Tải lại', 'Try again', 'Reload', 'Nhấn để thử lại'], exact=False):
            self._cho_chuyen_man_hinh(s['sig'], timeout=4.0)
            return True

        # Nếu là trang lỗi cụt không có nút thử lại -> Back 1 bước nhẹ nhàng
        if self._snap_has(s, ['error facebook', 'sự cố tải', 'trang này không hiển thị']):
            try:
                self.d.press('back')
            except Exception:
                self.chay_shell_nhanh('input keyevent 4')
            time.sleep(1.0)
            return True

        return False

    def _tim_va_bam_chu_dong(self, snap, keywords, exclude_keywords=None, min_y=0.05, max_y=0.95, click_duoi=False):
        """
        Quét & bấm chính xác vào tọa độ ĐỘNG của dòng chữ trên màn hình (TUYỆT ĐỐI KHÔNG dùng tọa độ cố định):
        1. Quét trong snapshot hiện tại: ưu tiên khớp chính xác (exact) trước, sau đó khớp chứa chuỗi (contains),
           loại bỏ hoàn toàn các chuỗi bị cấm trong `exclude_keywords` (VD: loại trừ 'Facebook Plus' khi tìm tài khoản).
        2. Nếu snapshot chưa bắt được (layout lồng phức tạp) -> quét bổ sung bằng u2 selector `textContains`/`descriptionContains`.
        Trả về nhãn chữ đã bấm (str) nếu bấm thành công, hoặc '' nếu không tìm thấy.
        """
        ex_kws = [e.lower() for e in (exclude_keywords or [])]
        if snap and snap.get('nodes'):
            w, h = snap['w'], snap['h']
            y1, y2 = int(h * min_y), int(h * max_y)
            kws_low = [k.lower() for k in keywords]

            for exact_mode in (True, False):
                for kw_cur in kws_low:
                    matches = []
                    for n in snap['nodes']:
                        if not (y1 <= n['cy'] <= y2):
                            continue
                        tl, dl = n['text_low'], n['desc_low']
                        if not tl and not dl:
                            continue
                        if ex_kws and any(ex in tl or ex in dl for ex in ex_kws):
                            continue
                        if exact_mode:
                            hit = (tl == kw_cur) or (dl == kw_cur)
                        else:
                            hit = (kw_cur in tl) or (kw_cur in dl)
                        if hit:
                            matches.append(n)
                    if matches:
                        node = matches[-1] if click_duoi else matches[0]
                        nhan = (node.get('text') or node.get('desc') or keywords[0]).strip()
                        self.click_toa_do_an_toan(node['cx'], node['cy'])
                        return nhan

        # Dự phòng quét trực tiếp bằng u2 selector (vẫn 100% theo chữ, KHÔNG tọa độ cố định)
        w, h = self._lay_kich_thuoc_man_hinh()
        y1, y2 = int(h * min_y), int(h * max_y)
        for kw in keywords:
            for sel in (self.d(text=kw), self.d(description=kw), self.d(textContains=kw), self.d(descriptionContains=kw)):
                try:
                    if not sel.exists:
                        continue
                    indices = range(sel.count - 1, -1, -1) if click_duoi else range(sel.count)
                    for idx in indices:
                        info = sel[idx].info
                        txt_i = ((info.get('text') or '') + ' ' + (info.get('contentDescription') or '')).lower()
                        if ex_kws and any(ex in txt_i for ex in ex_kws):
                            continue
                        b = info.get('bounds') or {}
                        cx = (b.get('left', 0) + b.get('right', 0)) // 2
                        cy = (b.get('top', 0) + b.get('bottom', 0)) // 2
                        if cx > 0 and y1 <= cy <= y2:
                            self.click_toa_do_an_toan(cx, cy)
                            return (info.get('text') or info.get('contentDescription') or kw).strip()
                except Exception:
                    continue
        return ''

    def dieu_huong_vao_man_hinh_2fa(self, ten_fb=""):
        """
        Điều hướng vào trang 2FA theo mô hình QUÉT CHỮ ĐỘNG 100% (TUYỆT ĐỐI KHÔNG dùng tọa độ cố định):
        - Đọc màn hình bằng `cho_man_hinh_san_sang()` -> thấy bước nào quét đúng chữ bước đó và bấm:
          * Trung tâm tài khoản Meta -> quét & bấm chữ "Đăng nhập và bảo mật" / "Mật khẩu và bảo mật"
          * Bên trong Đăng nhập và bảo mật -> quét & bấm chữ "Xác thực 2 yếu tố"
          * Màn hình Cài đặt -> quét & bấm chữ "Xem thêm trong Trung tâm tài khoản" / "Trung tâm tài khoản"
          * Màn hình Chọn tài khoản (loại trừ nhầm '1 trang cá nhân' / 'Facebook Plus') -> quét & bấm tên FB
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        uf = self._u_flag()

        cac_dau_hieu_trang_2fa = [
            'Thiết lập phương thức bảo vệ tăng cường',
            'bảo vệ tăng cường cho Tài khoản Meta',
            'Thêm một bước đăng nhập cho thiết bị mới',
            'Set up extra protection',
            'extra protection for your Meta',
            'Chọn phương thức bảo mật',
            'Dùng ứng dụng xác thực',
            'Sử dụng ứng dụng xác thực',
            'Ứng dụng xác thực',
            'Authentication app',
            'Use authentication app',
            'Thiết lập ứng dụng',
            'Hướng dẫn thiết lập',
            'Sao chép khóa',
            'Copy key',
            'Bắt đầu',
            'Get started',
            'Giúp bảo vệ tài khoản của bạn',
            'Vì lý do bảo mật',
            'Nhập lại mật khẩu',
            'Nhập mật khẩu',
            'For your security',
            'Enter your password',
            'Re-enter your password'
        ]
        cac_muc_bao_mat = [
            'Đăng nhập và bảo mật',
            'Mật khẩu và bảo mật',
            'Sign-in and security',
            'Login and security',
            'Password and security'
        ]
        cac_muc_2fa = [
            'Xác thực 2 yếu tố',
            'Xác thực hai yếu tố',
            'Two-factor authentication'
        ]
        cac_muc_tt_tk = [
            'Tài khoản Meta',
            'Xem thêm trong Trung tâm tài khoản',
            'Trung tâm tài khoản',
            'Mật khẩu, bảo mật, thông tin cá nhân',
            'Meta Accounts Center',
            'Meta Accounts',
            'See more in Accounts Center',
            'Accounts Center',
            'Password, security, personal details'
        ]
        loai_tru_tt_tk = [
            'meta đã xác minh', 'meta verified', 'meta pay',
            'sản phẩm khác của meta', 'cũng từ meta', 'also from meta',
            'facebook plus', 'tìm kiếm cài đặt', 'search settings',
            'thiết lập phương thức', 'bảo vệ tăng cường', 'tăng cường cho tài khoản',
            'extra protection', 'set up extra'
        ]

        # 1. Dọn sạch hết popup chắn sau bước Avatar TRƯỚC khi gọi mở thẳng trang Cài đặt và quyền riêng tư
        snap0 = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Trước khi mở Cài đặt 2FA')
        self.bo_qua_luu_thong_tin_dang_nhap(snap=snap0)
        self.quet_va_xoa_man_hinh_chan(so_vong_quet=4, snap=snap0)
        snap_now = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Xác nhận trước khi mở Cài đặt và quyền riêng tư')
        if self._snap_has(snap_now, cac_dau_hieu_trang_2fa):
            return True

        # ==================== GỌI 1 PHÁT RA THẲNG TRANG "CÀI ĐẶT VÀ QUYỀN RIÊNG TƯ" (fb://settings) ====================
        # KHÔNG gọi link 2FA trực tiếp (facewebmodal) vì dễ gây lỗi tải trang; vào thẳng Cài đặt -> Tài khoản Meta -> Bảo mật -> 2FA!
        da_o_trong_cai_dat_hoac_meta = self._snap_has(
            snap_now,
            cac_muc_2fa + cac_muc_bao_mat + cac_muc_tt_tk + ['tìm kiếm cài đặt', 'search settings', 'chọn tài khoản', 'select an account']
        )
        if not da_o_trong_cai_dat_hoac_meta:
            self.log('⚡ [Điều hướng 2FA] Gọi thẳng 1 phát ra trang "Cài đặt và quyền riêng tư" (fb://settings)...')
            self.chay_shell_nhanh(f'am start {uf}-a android.intent.action.VIEW -d "fb://settings" com.facebook.katana')
            time.sleep(1.5)
        else:
            self.log('✅ Đã đứng sẵn trong Cài đặt / Trung tâm tài khoản Meta -> Bấm tiếp vào Xác thực 2 yếu tố...')

        # ==================== STATE MACHINE QUÉT CHỮ ĐỘNG (0% TỌA ĐỘ CỐ ĐỊNH) ====================
        han_chot_dh = time.time() + 55.0
        so_lan_cuon_tim_chu = 0
        so_lan_goi_lai_settings = 0
        da_thu_menu_3_gach = False
        da_mo_nhom_cai_dat_menu = False

        while time.time() < han_chot_dh and not STOP_EVENT.is_set():
            self.dam_bao_fb_dang_chay(max_retry=1, cho_len_giay=4.0, cho_phep_force_stop=False)
            snap = self.cho_man_hinh_san_sang(timeout=15.0, ngu_canh='Quét chữ điều hướng 2FA')
            if snap.get('is_blank_or_loading'):
                time.sleep(0.5)
                continue

            if self.quet_va_xoa_man_hinh_chan(so_vong_quet=2, snap=snap):
                continue
            if self._kiem_tra_va_xu_ly_loi_mang_2fa(snap=snap):
                continue

            # 1. Đã tới trang thiết lập 2FA hoặc nhập lại mật khẩu
            if self._snap_has(snap, cac_dau_hieu_trang_2fa):
                self.log('✅ Đã vào trang thiết lập 2FA thành công!')
                return True

            # 2. Thấy mục "Xác thực 2 yếu tố" -> Quét & bấm đúng chữ đó
            if self._snap_has(snap, cac_muc_2fa):
                prev_s = snap['sig']
                nhan_2fa = self._tim_va_bam_chu_dong(snap, cac_muc_2fa, min_y=0.10, max_y=0.92)
                if nhan_2fa:
                    self.log(f'🛡️ [Quét chữ] Bấm "{nhan_2fa}"...')
                    so_lan_cuon_tim_chu = 0
                    self._cho_chuyen_man_hinh(prev_s, timeout=5.0)
                    continue

            # 3. Đang ở màn Trung tâm tài khoản Meta (như ảnh) có chữ "Đăng nhập và bảo mật" / "Mật khẩu và bảo mật"
            #    (CHÚ Ý: phân biệt rõ với tiêu đề trang khi đã ở BÊN TRONG trang "Đăng nhập và bảo mật"!)
            la_trang_tt_tk_meta = self._snap_has(snap, [
                'trải nghiệm liên trang cá nhân', 'thông tin và quyền của bạn',
                'quản lý tài khoản', 'tùy chọn quảng cáo', 'meta pay',
                'connected experiences', 'your information and permissions', 'accounts center',
                'trung tâm tài khoản', 'hành động đề xuất'
            ])
            node_bao_mat = self._snap_find(snap, cac_muc_bao_mat, exact=False, min_y=0.12, max_y=0.92)
            # Chỉ bấm "Đăng nhập và bảo mật" nếu nó là mục menu (nằm dưới thanh tiêu đề y >= 0.14*h hoặc trên trang Trung tâm TK)
            if node_bao_mat is not None and (la_trang_tt_tk_meta or node_bao_mat['cy'] >= int(h * 0.15)):
                prev_s = snap['sig']
                nhan_bm = self._tim_va_bam_chu_dong(snap, cac_muc_bao_mat, min_y=0.12, max_y=0.92)
                if nhan_bm:
                    self.log(f'🔐 [Quét chữ] Bấm "{nhan_bm}" (không dùng tọa độ cố định)...')
                    so_lan_cuon_tim_chu = 0
                    self._cho_chuyen_man_hinh(prev_s, timeout=5.0)
                    continue

            # 4. Đang ở bên trong trang "Đăng nhập và bảo mật" (tiêu đề ở trên cùng) nhưng chưa thấy "Xác thực 2 yếu tố" -> cuộn nhẹ tìm chữ
            if self._snap_has(snap, ['đăng nhập và bảo mật', 'mật khẩu và bảo mật', 'đăng nhập và khôi phục', 'password and security', 'sign-in and security']):
                if so_lan_cuon_tim_chu < 4:
                    so_lan_cuon_tim_chu += 1
                    self.log(f'📜 [Đăng nhập và bảo mật] Cuộn nhẹ tìm chữ "Xác thực 2 yếu tố" (lần {so_lan_cuon_tim_chu}/4)...')
                    self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.76), int(w * 0.50), int(h * 0.30), 260)
                    time.sleep(0.8)
                    continue

            # 5. Đang ở màn hình "Chọn tài khoản" thực sự (LOẠI TRỪ hoàn toàn trang Trung tâm TK có "1 trang cá nhân" / "Facebook Plus"!)
            if (
                not la_trang_tt_tk_meta
                and not self._snap_has(snap, cac_muc_bao_mat)
                and self._snap_has(snap, ['chọn tài khoản', 'select an account', 'chọn trang cá nhân', 'choose an account'])
            ):
                prev_s = snap['sig']
                ds_tk = ([ten_fb] if ten_fb else []) + ['Facebook']
                nhan_tk = self._tim_va_bam_chu_dong(
                    snap,
                    ds_tk,
                    exclude_keywords=['facebook plus', 'facebook pay', 'chọn tài khoản', 'select an account', 'meta'],
                    min_y=0.15,
                    max_y=0.80
                )
                if nhan_tk:
                    self.log(f'👤 [Quét chữ] Chọn tài khoản "{nhan_tk}"...')
                    self._cho_chuyen_man_hinh(prev_s, timeout=5.0)
                    continue

            # 6. Đang ở màn hình Cài đặt và quyền riêng tư -> Quét & bấm chữ "Tài khoản Meta" / "Trung tâm tài khoản" (0% tọa độ cố định!)
            if self._snap_has(snap, cac_muc_tt_tk):
                prev_s = snap['sig']
                nhan_tt = self._tim_va_bam_chu_dong(
                    snap,
                    cac_muc_tt_tk,
                    exclude_keywords=loai_tru_tt_tk,
                    min_y=0.10,
                    max_y=0.85
                )
                if nhan_tt:
                    self.log(f'⚙️ [Quét chữ] Bấm "{nhan_tt}" (không dùng tọa độ cố định)...')
                    so_lan_cuon_tim_chu = 0
                    self._cho_chuyen_man_hinh(prev_s, timeout=5.5)
                    continue

            # 7. Đang ở màn hình Menu Facebook -> Ưu tiên bấm thẳng nút/dòng "Cài đặt" (KHÔNG bấm lặp đóng/mở "Cài đặt và quyền riêng tư"!)
            if self._la_man_hinh_menu_fb(snap):
                prev_s = snap['sig']
                # 7A. Ưu tiên tìm CHÍNH XÁC nút "Cài đặt" / "Settings" (kể cả icon bánh răng góc trên phải hoặc dòng con sau khi xổ)
                node_cd_chuan = self._snap_find(
                    snap,
                    ['Cài đặt', 'Settings'],
                    exact=True,
                    min_y=0.04,
                    max_y=0.93
                )
                if node_cd_chuan is not None:
                    self.log(f'⚙️ [Quét chữ Menu] Bấm thẳng "{node_cd_chuan["text"] or node_cd_chuan["desc"]}"...')
                    self.click_toa_do_an_toan(node_cd_chuan['cx'], node_cd_chuan['cy'])
                    self._cho_chuyen_man_hinh(prev_s, timeout=4.5)
                    continue

                # 7B. Nếu chưa từng xổ nhóm "Cài đặt và quyền riêng tư" -> CHỈ bấm xổ ĐÚNG 1 LẦN rồi cuộn nhẹ lộ ra dòng "Cài đặt"
                if not da_mo_nhom_cai_dat_menu:
                    nhan_nhom = self._tim_va_bam_chu_dong(
                        snap,
                        ['Cài đặt và quyền riêng tư', 'Cài đặt & quyền riêng tư', 'Settings & privacy', 'Settings and privacy'],
                        min_y=0.10,
                        max_y=0.93
                    )
                    if nhan_nhom:
                        da_mo_nhom_cai_dat_menu = True
                        self.log(f'⚙️ [Quét chữ Menu] Mở nhóm "{nhan_nhom}" (chỉ 1 lần) để lộ mục "Cài đặt"...')
                        time.sleep(0.9)
                        snap_after_exp = self.quet_snapshot()
                        if self._snap_find(snap_after_exp, ['Cài đặt', 'Settings'], exact=True, min_y=0.04, max_y=0.93) is None:
                            self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.78), int(w * 0.50), int(h * 0.42), 260)
                            time.sleep(0.7)
                        continue

                # 7C. Đã xổ nhóm rồi nhưng vẫn đứng ở Menu -> Gọi thẳng DeepLink fb://settings thoát vòng lặp Menu ngay!
                self.log('⚡ [Menu] Gọi thẳng fb://settings để vào trang Cài đặt (tránh bấm lặp Cài đặt và quyền riêng tư)...')
                self.chay_shell_nhanh(f'am start {uf}-a android.intent.action.VIEW -d "fb://settings" com.facebook.katana')
                time.sleep(1.5)
                continue

            # 8. Chưa thấy trang "Cài đặt và quyền riêng tư" -> Ưu tiên gọi lại thẳng `fb://settings` trước, dự phòng mới mở Menu 3 gạch
            if so_lan_goi_lai_settings < 2:
                so_lan_goi_lai_settings += 1
                self.log(f'🔄 [Điều hướng 2FA] Gọi lại thẳng trang "Cài đặt và quyền riêng tư" (fb://settings, lần {so_lan_goi_lai_settings}/2)...')
                self.chay_shell_nhanh(f'am start {uf}-a android.intent.action.VIEW -d "fb://settings" com.facebook.katana')
                time.sleep(1.6)
            elif not da_thu_menu_3_gach:
                da_thu_menu_3_gach = True
                self.log(f'🔄 [Điều hướng 2FA] Chưa vào được Cài đặt ({self._tom_tat_man_hinh(snap)}) -> Mở Menu vào Cài đặt...')
                self._bam_nut_3_gach_goc_trai()
                time.sleep(1.2)
            else:
                self.chay_shell_nhanh(f'am start {uf}-a android.intent.action.VIEW -d "fb://settings" com.facebook.katana')
                time.sleep(1.5)

        return True

    def _dang_o_man_hinh_xac_thuc_mk_2fa(self, so_lan_thu=1, delay=0.25):
        """Kiểm tra có đang đứng ở màn hình 'Vì lý do bảo mật, vui lòng nhập lại mật khẩu của bạn' hay không."""
        return self.kiem_tra_text([
            'Vì lý do bảo mật',
            'vui lòng nhập lại mật khẩu',
            'nhập lại mật khẩu của bạn',
            'Nhập lại mật khẩu',
            'Nhập mật khẩu',
            'Mật khẩu của bạn',
            'Quên mật khẩu',
            'Xác nhận đó là bạn',
            'For your security',
            'Enter your password',
            'Re-enter your password',
            'Forgot password'
        ], so_lan_thu, delay)

    def _nut_tiep_tuc_da_bat(self):
        """Kiểm tra nhanh nút 'Tiếp tục' / 'Continue' đã chuyển sang trạng thái bật (enabled=True) hay chưa."""
        for sel in [
            self.d(text='Tiếp tục'),
            self.d(description='Tiếp tục'),
            self.d(text='Continue'),
            self.d(description='Continue')
        ]:
            if sel.exists:
                try:
                    return bool(sel[0].info.get('enabled', True))
                except Exception:
                    return True
        return True

    def _nhap_mat_khau_xac_nhan_2fa_hinh_2(self, mat_khau_fb=None, snap=None):
        """
        Xử lý chuẩn 1 NHỊP DUY NHẤT cho màn hình xác thực lại mật khẩu khi bật 2FA (chống gõ 2 lần):
        - Nếu ô mật khẩu ĐÃ có đủ độ dài mật khẩu & nút 'Tiếp tục' đang sáng -> KHÔNG gõ lại, chỉ bấm 'Tiếp tục'.
        - Sau khi bấm 'Tiếp tục' -> đợi động rời khỏi màn mật khẩu (tối đa 9s), để vòng State Machine tự đọc màn kế tiếp.
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        s_now = snap if snap is not None else self.quet_snapshot()
        self.quet_va_xoa_man_hinh_chan(so_vong_quet=1, snap=s_now)
        if not self._snap_has(s_now, [
            'Vì lý do bảo mật', 'vui lòng nhập lại mật khẩu', 'nhập lại mật khẩu của bạn',
            'Nhập lại mật khẩu', 'Nhập mật khẩu', 'Mật khẩu của bạn', 'For your security',
            'Enter your password', 'Re-enter your password'
        ]):
            return False

        mk_can_nhap = str(mat_khau_fb or self.config.get('mat_khau_fb') or '').strip()
        if not mk_can_nhap:
            self.log('⚠️ Không tìm thấy mật khẩu tài khoản để xác thực 2FA!')
            return False

        o_mk_2fa = None
        edits = self.d(className='android.widget.EditText')
        if edits.exists:
            for i in range(edits.count):
                try:
                    info_e = edits[i].info
                    if info_e.get('password') or info_e.get('focused'):
                        o_mk_2fa = edits[i]
                        break
                except Exception:
                    pass
            if o_mk_2fa is None:
                o_mk_2fa = edits[0]

        da_co_san_mk = (o_mk_2fa is not None and self._kiem_tra_o_da_co_chu(o_mk_2fa, mk_can_nhap, is_password=True))
        if not da_co_san_mk:
            self.log('🔑 [Xác thực 2FA] Nhập lại mật khẩu lúc tạo tài khoản (1 nhịp sạch)...')
            if o_mk_2fa is not None:
                self._click_phan_tu_an_toan(o_mk_2fa)
            else:
                self.click_toa_do_an_toan(int(w * 0.45), int(h * 0.355))
            time.sleep(0.35)

            ok_adb_2fa = self._go_tung_ky_tu_cham(mk_can_nhap, elem=o_mk_2fa, is_password=True, delay_ky_tu=0.13)
            time.sleep(0.3)
            da_nhap_thanh_cong = ok_adb_2fa and (
                (o_mk_2fa is None)
                or self._kiem_tra_o_da_co_chu(o_mk_2fa, mk_can_nhap, is_password=True)
                or (self._nut_tiep_tuc_da_bat() and not (o_mk_2fa.info.get('text') or '').strip())
            )
            if not da_nhap_thanh_cong and o_mk_2fa is not None:
                try:
                    self.xoa_o_nhap(o_mk_2fa)
                    self._click_phan_tu_an_toan(o_mk_2fa)
                    time.sleep(0.2)
                    o_mk_2fa.set_text(mk_can_nhap)
                    time.sleep(0.35)
                except Exception:
                    pass
        else:
            self.log('🔑 [Xác thực 2FA] Ô mật khẩu đã có sẵn đủ ký tự -> Không gõ lại, chỉ bấm Tiếp tục...')

        self._ha_ban_phim_an_toan()
        s_btn = self.quet_snapshot()
        prev_sig = s_btn['sig']
        self.log('⏩ [Xác thực 2FA] Bấm nút xanh "Tiếp tục" & chờ chuyển trang...')
        da_bam_tt = (
            self._snap_click(s_btn, ['Tiếp tục', 'Continue', 'Tiếp', 'Next'], exact=True, click_duoi=True)
            or self._snap_click(s_btn, ['Tiếp tục', 'Continue'], exact=False, click_duoi=True)
        )
        if not da_bam_tt:
            y_tt = int(h * 0.418)
            if o_mk_2fa is not None:
                try:
                    b_mk = o_mk_2fa.info['bounds']
                    y_tt = b_mk['bottom'] + int(h * 0.055)
                except Exception:
                    pass
            self.click_toa_do_an_toan(int(w * 0.50), y_tt)

        # Chờ động tối đa 9s cho màn hình thực sự rời khỏi trang nhập mật khẩu
        self._cho_chuyen_man_hinh(
            prev_sig,
            timeout=9.0,
            old_screen_keywords=['Vì lý do bảo mật', 'vui lòng nhập lại mật khẩu', 'nhập lại mật khẩu của bạn', 'For your security', 'Enter your password']
        )
        return True

    def _xu_ly_man_hinh_bat_dau_bao_ve_meta(self, snap=None):
        """
        Xử lý màn hình 2FA chỉ có nút 'Bắt đầu' / 'Get started' (không phải 'Tiếp tục'):
        - Màn hình 'Thiết lập phương thức bảo vệ tăng cường cho Tài khoản Meta'
        - Hoặc bất kỳ màn hình mở đầu bật 2FA nào có nút chính xác 'Bắt đầu' (và không phải trang QR/Key hay ô nhập mã).
        """
        s = snap if snap is not None else self.quet_snapshot()
        if s['is_blank_or_loading'] or s['edit_texts']:
            return False
        if self._la_man_hinh_qr_key_2fa(s) or self._doc_key_2fa_tu_xml_nhanh(s):
            return False

        dau_hieu_bat_dau_meta = [
            'Thiết lập phương thức bảo vệ tăng cường',
            'bảo vệ tăng cường cho Tài khoản Meta',
            'Thêm một bước đăng nhập cho thiết bị mới',
            'Luôn bảo vệ bạn ngay cả khi mật khẩu của bạn',
            'Set up extra protection',
            'extra protection for your Meta',
            'Add an extra step'
        ]
        co_nut_bat_dau = self._snap_has(s, ['Bắt đầu', 'Get started'], exact=True)
        if self._snap_has(s, dau_hieu_bat_dau_meta) or co_nut_bat_dau:
            self.log('🛡️ [2FA] Phát hiện màn bảo vệ tăng cường -> Bấm chính xác nút xanh "Bắt đầu"...')
            da_bam = (
                self._snap_click(s, ['Bắt đầu', 'Get started'], exact=True, click_duoi=True, min_y=0.50)
                or self._snap_click(s, ['Bắt đầu', 'Get started'], exact=True, click_duoi=True)
                or bool(self._tim_va_bam_chu_dong(
                    s,
                    ['Bắt đầu', 'Get started'],
                    exclude_keywords=['thiết lập phương thức', 'bảo vệ tăng cường', 'tài khoản meta'],
                    min_y=0.55,
                    max_y=0.97,
                    click_duoi=True
                ))
            )
            if not da_bam:
                self.click_toa_do_an_toan(int(s['w'] * 0.50), int(s['h'] * 0.892))
            self._cho_chuyen_man_hinh(
                s['sig'],
                timeout=5.0,
                old_screen_keywords=['Thiết lập phương thức bảo vệ tăng cường', 'Set up extra protection']
            )
            return True
        return False

    def _dang_o_man_hinh_otp_phu_2fa(self, so_lan_thu=1, delay=0.25):
        """Nhận diện màn hình yêu cầu nhập mã OTP gửi về Email/SMS khi bật 2FA (loại trừ màn hình TOTP ứng dụng xác thực)."""
        if self.kiem_tra_text(['ứng dụng xác thực', 'authentication app', 'quét mã qr', 'sao chép khóa', 'copy key'], 1, 0.1):
            return False
        return self.kiem_tra_text([
            'Kiểm tra email',
            'Kiểm tra hộp thư',
            'Check your email',
            'Kiểm tra tin nhắn',
            'Kiểm tra điện thoại',
            'Check your text',
            'Nhập mã gồm',
            'Nhập mã xác nhận',
            'Nhập mã bảo mật',
            'Nhập mã',
            'Chúng tôi đã gửi mã',
            'chúng tôi đã gửi mã',
            'gửi mã đến',
            'gửi mã tới',
            'We sent a code',
            'Enter code',
            'Enter the code',
            'confirmation code',
            'mã gồm 6 chữ số',
            'mã gồm 8 chữ số'
        ], so_lan_thu, delay)

    def _ban_phim_dang_mo(self):
        """Kiểm tra chính xác bàn phím ảo có đang hiển thị hay không (nhanh qua u2.shell, fallback ADB)."""
        try:
            res = self.d.shell('dumpsys input_method | grep mInputShown', timeout=4)
            out = getattr(res, 'output', '') if res is not None else ''
            if out:
                return 'mInputShown=true' in out
        except Exception:
            pass
        try:
            out = chay_lenh_adb_lay_ket_qua('shell "dumpsys input_method | grep mInputShown"', self.serial, timeout=4)
            return 'mInputShown=true' in (out or '')
        except Exception:
            return False

    def _ha_ban_phim_an_toan(self, max_thu=2):
        """Chỉ hạ bàn phím khi bàn phím ảo thực sự đang mở và CHỜ ĐỢI tới khi bàn phím đóng hẳn (tránh che nút bước sau)."""
        for _ in range(max_thu):
            if not self._ban_phim_dang_mo():
                return True
            try:
                self.d.press('back')
            except Exception:
                self.chay_shell_nhanh('input keyevent 4')
            # Chờ tối đa 1.4s để hiệu ứng trượt xuống của bàn phím đóng hoàn toàn
            moc_dong = time.time() + 1.4
            while time.time() < moc_dong:
                time.sleep(0.22)
                if not self._ban_phim_dang_mo():
                    time.sleep(0.2)
                    return True
        return not self._ban_phim_dang_mo()

    def _go_chuoi_so_bang_keyevent(self, digits_str):
        """
        Gõ từng chữ số 0-9 bằng mã phím cứng Android (KEYCODE_0 = 7 .. KEYCODE_9 = 16).
        Hoạt động 100% trên mọi ô nhập mã 2FA Bloks UI (cả 1 ô gộp lẫn 6 ô tách rời) không phụ thuộc FastInputIME.
        """
        s = re.sub(r'[^0-9]', '', str(digits_str or ''))
        if not s:
            return False
        cmds = [f'input keyevent {7 + int(ch)}' for ch in s]
        joined = '; '.join(cmds)
        try:
            self.d.shell(joined, timeout=8)
            return True
        except Exception:
            ok_adb, _ = chay_lenh_adb_list(['shell', joined], self.serial, timeout=10)
            return ok_adb

    def _tim_edittext_hien_thi(self):
        """
        Tìm ô EditText THỰC SỰ hiển thị trên màn hình (lọc bỏ hoàn toàn node ẩn / kích thước 0 / ngoài màn hình
        từ các màn hình trước còn sót trong view hierarchy của Facebook).
        """
        w, h = self.d.window_size()
        edits = self.d(className='android.widget.EditText')
        if not edits.exists:
            return None

        ung_vien = []
        for i in range(edits.count):
            try:
                elem = edits[i]
                info = elem.info
                b = info.get('bounds') or {}
                l, t, r, bot = b.get('left', 0), b.get('top', 0), b.get('right', 0), b.get('bottom', 0)
                bw, bh = r - l, bot - t
                cx, cy = (l + r) // 2, (t + bot) // 2
                if bw >= 40 and bh >= 20 and 0 <= l and r <= w + 5 and int(h * 0.10) <= cy <= int(h * 0.85):
                    txt_low = ((info.get('text') or '') + ' ' + (info.get('contentDescription') or '')).lower()
                    diem = 0
                    if info.get('focused'):
                        diem += 3
                    if any(k in txt_low for k in ['mã', 'code', 'nhập', '6 chữ số', '8 chữ số']):
                        diem += 2
                    ung_vien.append((diem, cy, elem))
            except Exception:
                pass

        if not ung_vien:
            return None
        ung_vien.sort(key=lambda item: (item[0], -item[1]), reverse=True)
        return ung_vien[0][2]

    def _kiem_tra_ma_so_da_nhap(self, elem, ma_so):
        """Kiểm tra chính xác ô nhập mã đã thực sự chứa đủ chữ số của mã 2FA/OTP hay chưa."""
        if elem is None:
            return False
        try:
            cur = re.sub(r'[^0-9]', '', (elem.info.get('text') or ''))
            exp = re.sub(r'[^0-9]', '', str(ma_so or ''))
            return bool(exp) and (exp in cur or cur == exp)
        except Exception:
            return False

    def _bam_nut_xanh_duoi_day_2fa(self, ds_nhan=None, fallback_y_ratio=0.872):
        """
        Tìm và bấm chính xác nút xanh hành động ở dưới màn hình 2FA ('Tiếp', 'Tiếp tục', 'Next', 'Continue', 'Xác nhận').
        Quét toàn bộ phần tử hiển thị trên màn hình (ưu tiên nút thấp nhất nằm ở nửa dưới y >= 0.35*h),
        sau đó fallback sang XML dump và cuối cùng là tọa độ đáy (0.50*w, 0.872*h) chuẩn giao diện Meta mới.
        """
        w, h = self.d.window_size()
        if ds_nhan is None:
            ds_nhan = ['Tiếp tục', 'Tiếp', 'Continue', 'Next', 'Xác nhận', 'Confirm']

        ung_vien = []
        for idx_uu_tien, nhan in enumerate(ds_nhan):
            for sel in [self.d(text=nhan), self.d(description=nhan)]:
                if sel.exists:
                    for i in range(sel.count):
                        try:
                            info = sel[i].info
                            b = info.get('bounds') or {}
                            l, t, r, bot = b.get('left', 0), b.get('top', 0), b.get('right', 0), b.get('bottom', 0)
                            cx, cy = (l + r) // 2, (t + bot) // 2
                            if (r - l) >= 30 and (bot - t) >= 20 and int(h * 0.32) <= cy <= int(h * 0.94):
                                enabled_score = 1 if info.get('enabled', True) else 0
                                # Ưu tiên nút đang enabled và nằm thấp nhất ở nửa dưới màn hình
                                ung_vien.append((enabled_score, cy, -idx_uu_tien, cx, nhan))
                        except Exception:
                            pass

        # Quét bổ sung bằng XML dump đề phòng Bloks UI lồng text trong ViewGroup
        if not ung_vien:
            try:
                xml_dump = self.d.dump_hierarchy()
                ds_low = {n.lower() for n in ds_nhan}
                for m in re.finditer(
                    r'(?:text|content-desc)="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                    xml_dump
                ):
                    label = html.unescape(m.group(1)).strip()
                    if label.lower() in ds_low:
                        l, t, r, bot = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
                        cx, cy = (l + r) // 2, (t + bot) // 2
                        if (r - l) >= 30 and (bot - t) >= 20 and int(h * 0.32) <= cy <= int(h * 0.94):
                            ung_vien.append((1, cy, 0, cx, label))
            except Exception:
                pass

        if ung_vien:
            ung_vien.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
            _, cy, _, cx, ten_nut = ung_vien[0]
            self.log(f'⏩ Bấm nút "{ten_nut}" tại ({cx}, {cy})...')
            self.click_toa_do_an_toan(cx, cy)
            return True

        # Fallback trực tiếp tọa độ nút xanh ở đáy màn hình (khớp chuẩn giao diện Meta mới)
        fx, fy = int(w * 0.50), int(h * fallback_y_ratio)
        self.log(f'⏩ Bấm nút xanh đáy màn hình theo tọa độ dự phòng ({fx}, {fy})...')
        self.click_toa_do_an_toan(fx, fy)
        return True

    def _dang_o_man_hinh_chon_phuong_thuc_2fa(self, so_lan_thu=1, delay=0.2):
        """Kiểm tra có đang đứng ở màn hình 'Chọn phương thức bảo mật' (radio Ứng dụng xác thực + nút Tiếp ở đáy) hay không."""
        if self._tim_edittext_hien_thi() is not None:
            return False
        if self.kiem_tra_text([
            'Sao chép khóa', 'Copy key', 'quét mã QR', 'Thiết lập ứng dụng xác thực',
            'Nhập mã', 'Mã xác nhận', 'Đã bật xác thực', 'Xong'
        ], 1, 0.1):
            return False
        return self.kiem_tra_text([
            'Chọn phương thức bảo mật',
            'Choose a security method',
            'Thiết lập cách chứng minh đó là bạn',
            'Giúp bảo vệ tài khoản của bạn',
            'Dùng ứng dụng xác thực',
            'Sử dụng ứng dụng xác thực',
            'Ứng dụng xác thực',
            'Authentication app',
            'Use authentication app'
        ], so_lan_thu, delay)

    def _xu_ly_chon_phuong_thuc_bao_mat_2fa(self, snap=None):
        """
        Xử lý chuẩn màn hình 'Chọn phương thức bảo mật' (CHỐNG bấm đúp làm nhảy vọt qua màn QR/Key 2FA):
        - Luôn dừng ngay lập tức nếu đã thấy dấu hiệu màn QR/Key 2FA.
        - Bấm đúng 1 lần nút xanh đáy ('Tiếp' / 'Bắt đầu' / 'Next') rồi đợi trang sau tải ổn định hẳn mới trả về cho vòng lặp đọc Key.
        """
        for lan in range(1, 3):
            s = snap if (lan == 1 and snap is not None) else self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Chọn phương thức bảo mật')
            # Tuyệt đối dừng ngay nếu đã sang màn hình QR/Key hoặc ô nhập mã
            if s['is_blank_or_loading'] or s['edit_texts'] or self._la_man_hinh_qr_key_2fa(s) or self._doc_key_2fa_tu_xml_nhanh(s):
                return True

            la_man_chon_pt = self._snap_has(s, [
                'Chọn phương thức bảo mật', 'Choose a security method',
                'Thiết lập cách chứng minh đó là bạn',
                'Dùng ứng dụng xác thực', 'Sử dụng ứng dụng xác thực', 'Use authentication app'
            ])
            if not la_man_chon_pt:
                return lan > 1

            # 1. Nếu là giao diện nút hành động trực tiếp 'Dùng ứng dụng xác thực' (không có nút Tiếp/Bắt đầu ở đáy)
            if self._snap_has(s, ['Dùng ứng dụng xác thực', 'Sử dụng ứng dụng xác thực', 'Use authentication app']) and not self._snap_has(s, ['Tiếp', 'Bắt đầu', 'Next', 'Get started'], exact=True):
                self.log(f'🛡️ [Chọn phương thức bảo mật - Lần {lan}/2] Bấm "Dùng ứng dụng xác thực"...')
                self._snap_click(s, ['Dùng ứng dụng xác thực', 'Sử dụng ứng dụng xác thực', 'Use authentication app'], exact=False)
                self._cho_chuyen_man_hinh(s['sig'], timeout=4.5)
                return True

            # 2. Màn hình Radio Button 'Chọn phương thức bảo mật': kiểm tra xem 'Ứng dụng xác thực' đã tích sẵn chưa
            da_tich_san = False
            node_app = self._snap_find(s, ['Ứng dụng xác thực', 'Authentication app'], exact=False, max_y=0.55)
            if node_app is not None:
                for n in s['nodes']:
                    if n['checked'] and abs(n['cy'] - node_app['cy']) <= int(s['h'] * 0.12):
                        da_tich_san = True
                        break
            if da_tich_san or (lan == 1 and self._snap_has(s, ['Khuyên dùng', 'Recommended'])):
                self.log(f'🛡️ [Chọn phương thức bảo mật - Lần {lan}/2] "Ứng dụng xác thực" đã tích sẵn -> Bấm nút xanh dưới đáy...')
            else:
                self.log(f'🛡️ [Chọn phương thức bảo mật - Lần {lan}/2] Tích chọn "Ứng dụng xác thực" rồi bấm nút xanh...')
                if node_app is not None:
                    self.click_toa_do_an_toan(node_app['cx'], node_app['cy'])
                    time.sleep(0.5)
                    s = self.quet_snapshot()

            # 3. Bấm chính xác nút xanh ở đáy màn hình (hỗ trợ cả 'Tiếp', 'Bắt đầu', 'Tiếp tục', 'Next') — CHỈ bấm khi tìm thấy trên đúng màn hình này!
            prev_sig = s['sig']
            btn_next = self._snap_find(s, ['Tiếp', 'Bắt đầu', 'Tiếp tục', 'Next', 'Get started', 'Continue'], exact=True, click_duoi=True, min_y=0.65)
            if btn_next is not None:
                self.log(f'⏩ Bấm nút "{btn_next["text"] or btn_next["desc"]}" tại ({btn_next["cx"]}, {btn_next["cy"]})...')
                self.click_toa_do_an_toan(btn_next['cx'], btn_next['cy'])
            else:
                self._bam_nut_xanh_duoi_day_2fa(['Tiếp', 'Bắt đầu', 'Tiếp tục', 'Next', 'Get started', 'Continue'], fallback_y_ratio=0.895)

            # Đợi màn hình thực sự chuyển & tải hoàn tất (tối thiểu 1.2s để màn QR/Key kịp render đủ chữ Key)
            s_sau = self._cho_chuyen_man_hinh(prev_sig, timeout=5.0)
            if s_sau['is_blank_or_loading']:
                s_sau = self.cho_man_hinh_san_sang(timeout=18.0, ngu_canh='Chờ màn hình QR/Key 2FA tải xong')
            time.sleep(1.0)
            s_sau = self.quet_snapshot()
            if (
                self._la_man_hinh_qr_key_2fa(s_sau)
                or self._doc_key_2fa_tu_xml_nhanh(s_sau)
                or not self._snap_has(s_sau, ['Chọn phương thức bảo mật', 'Choose a security method'])
            ):
                self.log('✅ Đã chuyển sang bước tiếp theo sau "Chọn phương thức bảo mật"!')
                return True

        return True

    def _nhap_ma_so_va_bam_tiep_2fa(self, ma_so, nhan_log="2FA 6 số", totp_secret=None, max_attempts=1):
        """
        Hàm nhập mã số (TOTP 6 số hoặc OTP Email 6/8 số) chuẩn xác cho Bloks UI của Meta:
        1. Tìm và bấm đúng ô EditText đang hiển thị trên màn hình (chống bấm trúng node ẩn).
        2. Nhập mã đa tầng có xác minh (set_text -> hardware keyevent 0-9 -> adb input text -> send_keys -> clipboard paste).
        3. Hạ bàn phím an toàn (chỉ hạ khi mInputShown=true) -> Bấm chính xác nút xanh 'Tiếp tục' / 'Tiếp' ở đáy màn hình.
        4. Xác minh đã rời màn hình nhập mã; nếu chưa qua sẽ tự thử lại (tự sinh mã TOTP mới nếu có totp_secret).
        """
        w, h = self.d.window_size()
        ma_hien_tai = str(ma_so or '').strip()
        if not ma_hien_tai:
            return False

        for lan in range(1, max_attempts + 1):
            if lan > 1 and totp_secret:
                ma_moi = chuyen_doi_2fa_sang_otp(totp_secret, doi_chu_ky_moi=True)
                if ma_moi:
                    ma_hien_tai = ma_moi

            self.log(f'🔢 [{nhan_log} - Lần {lan}/{max_attempts}] Nhấn vào ô nhập mã & nhập: {ma_hien_tai}...')

            # Bước 1: Tìm ô EditText thực sự hiển thị trên màn hình
            o_nhap = self._tim_edittext_hien_thi()
            if o_nhap is not None:
                self._click_phan_tu_an_toan(o_nhap)
                time.sleep(0.4)
            else:
                da_click_label = (
                    self.click_truong('Nhập mã', False, 1, 0.3)
                    or self.click_truong('Mã xác nhận', False, 1, 0.3)
                    or self.click_truong('Mã gồm 6 chữ số', False, 1, 0.3)
                    or self.click_truong('Mã gồm 8 chữ số', False, 1, 0.3)
                    or self.click_truong('Nhập mã gồm', False, 1, 0.3)
                    or self.click_truong('Enter code', False, 1, 0.3)
                    or self.click_truong('Confirmation code', False, 1, 0.3)
                    or self.click_truong('Code', False, 1, 0.3)
                )
                if not da_click_label:
                    # Quét 2 vị trí phổ biến của ô nhập mã trên Meta Accounts Center
                    y_box = int(h * 0.345) if lan % 2 == 1 else int(h * 0.405)
                    self.click_toa_do_an_toan(int(w * 0.50), y_box)
                time.sleep(0.5)
                o_nhap = self._tim_edittext_hien_thi()
                if o_nhap is not None:
                    self._click_phan_tu_an_toan(o_nhap)
                    time.sleep(0.35)

            # Xóa sạch nếu đang còn ký tự cũ
            if lan > 1 or (o_nhap is not None and len(re.sub(r'[^0-9]', '', o_nhap.info.get('text') or '')) > 0):
                self.xoa_o_nhap(o_nhap)
                time.sleep(0.25)

            da_nhap_duoc = False

            # Tầng 1: set_text trực tiếp qua Accessibility (nhanh & ăn chắc trên Bloks UI)
            if o_nhap is not None:
                try:
                    o_nhap.set_text(ma_hien_tai)
                    time.sleep(0.45)
                    if self._kiem_tra_ma_so_da_nhap(o_nhap, ma_hien_tai):
                        da_nhap_duoc = True
                except Exception:
                    pass

            # Tầng 2: Nhấn lại ô + Gõ từng chữ số 0-9 bằng hardware keyevent (ăn cả 1 ô lẫn 6 ô tách rời)
            if not da_nhap_duoc:
                if o_nhap is not None:
                    self.xoa_o_nhap(o_nhap)
                    self._click_phan_tu_an_toan(o_nhap)
                    try:
                        o_nhap.click()
                    except Exception:
                        pass
                else:
                    self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.355))
                time.sleep(0.4)
                self._go_chuoi_so_bang_keyevent(ma_hien_tai)
                time.sleep(0.5)
                o_nhap = self._tim_edittext_hien_thi() or o_nhap
                if o_nhap is None or self._kiem_tra_ma_so_da_nhap(o_nhap, ma_hien_tai):
                    da_nhap_duoc = True

            # Tầng 3: Fallback ADB input text
            if not da_nhap_duoc:
                if o_nhap is not None:
                    self.xoa_o_nhap(o_nhap)
                    self._click_phan_tu_an_toan(o_nhap)
                time.sleep(0.35)
                self._go_chu_bang_adb_input(ma_hien_tai)
                time.sleep(0.5)
                if o_nhap is None or self._kiem_tra_ma_so_da_nhap(o_nhap, ma_hien_tai):
                    da_nhap_duoc = True

            # Tầng 4: Fallback u2.send_keys (KHÔNG dùng Clipboard Paste để tránh dán nhầm rác vào ô mã số)
            if not da_nhap_duoc:
                try:
                    if o_nhap is not None:
                        self.xoa_o_nhap(o_nhap)
                        self._click_phan_tu_an_toan(o_nhap)
                    time.sleep(0.3)
                    self.d.send_keys(ma_hien_tai)
                    time.sleep(0.45)
                except Exception:
                    pass

            time.sleep(0.6)

            # Hạ bàn phím ảo (CHỈ khi bàn phím đang mở) để lộ nút xanh 'Tiếp tục' / 'Tiếp' ở đáy màn hình
            self._ha_ban_phim_an_toan()

            # Bước 3: Bấm chính xác nút xanh 'Tiếp tục' / 'Tiếp' / 'Continue' / 'Next' / 'Xác nhận'
            s_before_submit = self.quet_snapshot()
            prev_code_sig = s_before_submit['sig']
            self.log(f'⏩ [{nhan_log}] Bấm nút "Tiếp tục / Tiếp" & chờ chuyển trang...')
            self._bam_nut_xanh_duoi_day_2fa(['Tiếp tục', 'Tiếp', 'Continue', 'Next', 'Xác nhận', 'Confirm'], fallback_y_ratio=0.872)

            # Chờ động tối đa 9s cho màn hình xử lý mã và chuyển sang bước kế tiếp (tránh gõ lặp 2 lần!)
            deadline_code = time.time() + 9.0
            time.sleep(0.8)
            while time.time() < deadline_code and not STOP_EVENT.is_set():
                s_chk_c = self.quet_snapshot()
                if s_chk_c.get('is_blank_or_loading') or s_chk_c.get('has_progress'):
                    time.sleep(0.35)
                    continue
                if self._snap_has(s_chk_c, [
                    'Xong', 'Done', 'Hoàn tất', 'Đã bật xác thực', 'Two-factor authentication is on',
                    'Mã khôi phục', 'Recovery codes', 'Chọn phương thức bảo mật', 'Thiết lập ứng dụng'
                ]) or not s_chk_c.get('edit_texts'):
                    return True
                if s_chk_c['sig'] != prev_code_sig and self._snap_has(s_chk_c, ['không hợp lệ', 'không đúng', 'sai mã', 'invalid', 'incorrect']):
                    break
                time.sleep(0.35)

            if lan < max_attempts:
                self.log(f'⚠️ [{nhan_log}] Màn hình vẫn còn ô nhập mã (Lần {lan}/{max_attempts}), thử lại...')

        return True

    def _nhap_otp_hoac_mk_phu_2fa(self, used_email, mode, mail_service, imap_service, hotmail_service, autosms_service, ten_fb="", mat_khau_fb=None, uid_moc_2fa=None):
        """
        Xử lý chuẩn các bước trung gian khi bật 2FA:
        1. Màn hình 'Thiết lập phương thức bảo vệ tăng cường cho Tài khoản Meta' -> Bấm 'Bắt đầu'.
        2. Màn hình nhập lại Mật khẩu -> Điền mật khẩu tài khoản & bấm 'Tiếp tục'.
        3. Màn hình chọn cách gửi mã (nếu chưa có ô nhập mã) -> Bấm chọn Email (Modes 1-5) & bấm 'Tiếp tục' / 'Gửi mã'.
        4. Màn hình yêu cầu OTP gửi về Email/SMS:
           - Chế độ 6 (Thuê SIM AutoSMS): SIM thuê chỉ được nhận 1 lần OTP lúc đăng ký -> Trả về 'SKIP_2FA_MODE6' để bỏ qua 2FA ngay, không treo chờ.
           - Các chế độ khác (Modes 1, 2, 3, 4, 5): Đọc màn hình (6 số hay 8 số) -> Tự động đi lấy OTP mới nhất -> Nhập vào & bấm 'Tiếp tục'.
        """
        # Các bước 'Bắt đầu' và 'Nhập lại mật khẩu' đã do State Machine bat_2fa_fb() xử lý riêng (không gọi lặp ở đây).
        # Bước C: Nếu hiện màn hình xác nhận phương thức gửi mã (chưa hiện ô EditText) -> Bấm Tiếp tục / Gửi mã
        if (
            self._tim_edittext_hien_thi() is None
            and not self._dang_o_man_hinh_chon_phuong_thuc_2fa(1, 0.15)
            and not self.kiem_tra_text(['Thiết lập ứng dụng', 'Sao chép khóa', 'quét mã QR'], 1, 0.15)
            and self.kiem_tra_text(['Gửi mã', 'Nhận mã', 'Chọn cách xác nhận', 'Xác nhận rằng đó là bạn', 'Chúng tôi có thể gửi mã', 'Chúng tôi sẽ gửi mã', 'Send code', 'Get a code'], 1, 0.25)
        ):
            if mode == "6":
                self.log('⚠️ [Mode 6 - Thuê SIM] Meta yêu cầu gửi mã OTP lần 2 (SIM thuê chỉ nhận được 1 OTP lúc đăng ký) -> Bỏ qua 2FA!')
                return 'SKIP_2FA_MODE6'
            self.log('📧 Phát hiện màn hình xác nhận gửi mã OTP 2FA -> Chốt mốc mail, chọn Email & bấm "Tiếp tục"...')
            # Chốt mốc hộp thư ngay trước khi bấm gửi mã để bắt đúng mã OTP 2FA mới nhất
            if mode == "5" and hotmail_service:
                hotmail_service.init_baseline()
            elif mode in ["3", "4"] and imap_service:
                uid_moc_2fa = imap_service.get_latest_uid()
            s_send = self.quet_snapshot()
            self._snap_click(s_send, ['Email', 'email', '@'], exact=False, max_y=0.70)
            time.sleep(0.4)
            prev_send_sig = s_send['sig']
            self._bam_nut_xanh_duoi_day_2fa(['Tiếp tục', 'Gửi mã', 'Tiếp', 'Bắt đầu', 'Continue', 'Next'], fallback_y_ratio=0.872)
            self._cho_chuyen_man_hinh(prev_send_sig, timeout=4.5)
            self.cho_man_hinh_san_sang(timeout=15.0, ngu_canh='Chờ trang nhập OTP Email 2FA')

        # Bước D: Nếu đang ở màn hình nhập OTP bảo mật (sau khi bấm Bắt đầu / Tiếp tục)
        if self._dang_o_man_hinh_otp_phu_2fa(1, 0.4):
            # Chế độ 6 (Thuê SIM) chỉ nhận được 1 lần OTP khi đăng ký -> Không chờ/nhập lại OTP cũ
            if mode == "6":
                self.log('⚠️ [Mode 6 - Thuê SIM] Phát hiện màn hình yêu cầu OTP 2FA lần 2 (SIM thuê chỉ được 1 lần OTP) -> Dừng bước 2FA (lưu NO_2FA)!')
                return 'SKIP_2FA_MODE6'

            s_otp_m = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Đọc yêu cầu OTP Email 2FA')
            co_yeu_cau_8_so = self._snap_has(s_otp_m, ['8 chữ số', '8-digit', 'gồm 8', '8 số', 'mã gồm 8'])
            co_yeu_cau_6_so = (not co_yeu_cau_8_so) and self._snap_has(s_otp_m, ['6 chữ số', '6-digit', 'gồm 6', '6 số', 'mã gồm 6'])
            expected_digits = 8 if co_yeu_cau_8_so else (6 if co_yeu_cau_6_so else None)
            mo_ta_ma = f'{expected_digits} chữ số' if expected_digits else 'mới nhất'
            self.log(f'📧 Phát hiện màn hình nhập OTP bảo mật 2FA ({mo_ta_ma}) [Mode {mode}] -> Vào mail lấy mã mới nhất...')

            moc_uid = uid_moc_2fa if (uid_moc_2fa is not None) else (imap_service.get_latest_uid() if (mode in ["3", "4"] and imap_service) else 0)
            verify_code = self.lay_otp_theo_che_do(
                mode=mode,
                used_email=used_email,
                mail_service=mail_service,
                imap_service=imap_service,
                hotmail_service=hotmail_service,
                uid_moc=moc_uid,
                force_8_digits=co_yeu_cau_8_so,
                expected_digits=expected_digits
            )
            if verify_code:
                self._nhap_ma_so_va_bam_tiep_2fa(verify_code, nhan_log="OTP Email 2FA", max_attempts=1)
                # Để vòng lặp State Machine bat_2fa_fb() tự nhận diện mượt màn hình tiếp theo (chống bấm vọt qua Key 2FA!)
                self.cho_man_hinh_san_sang(timeout=15.0, ngu_canh='Sau nhập OTP Email 2FA')
                return 'OTP_OK'
            else:
                self.log('⚠️ Không lấy được mã OTP bảo mật 2FA từ hộp thư!')
                return 'OTP_FAIL'

        return ''

    def _la_man_hinh_qr_key_2fa(self, snap):
        """Nhận diện chắc chắn màn hình Hình 3 (mã QR / Khóa thiết lập / nút Sao chép khóa)."""
        if not snap or snap.get('edit_texts'):
            return False
        if self._snap_has(snap, ['Chọn phương thức bảo mật', 'Choose a security method']):
            return False
        return self._snap_has(snap, [
            'Sao chép khóa', 'Sao chép mã', 'Copy key', 'Copy code',
            'quét mã QR', 'Scan QR', 'Thiết lập ứng dụng', 'Hướng dẫn thiết lập',
            'khóa thiết lập', 'setup key', 'nhập khóa', 'enter the key',
            'thêm tài khoản của bạn vào ứng dụng xác thực'
        ])

    def _la_man_hinh_o_nhap_ma_totp_2fa(self, snap):
        """
        CHỈ nhận diện màn hình Hình 4 (ô nhập mã 6 số từ Ứng dụng xác thực) khi thực sự có chữ nhắc đến ứng dụng xác thực
        và TUYỆT ĐỐI loại trừ màn hình OTP Email/SMS (tránh bấm Back nhầm làm văng khỏi trang nhập OTP Email ở Chế độ 5!).
        """
        if not snap or not snap.get('edit_texts'):
            return False
        if self._snap_has(snap, [
            '@', 'email', 'hotmail', 'outlook', 'gmail', 'hộp thư', 'tin nhắn', 'sms',
            'số điện thoại', 'gửi mã đến', 'gửi mã tới', 'chúng tôi đã gửi mã',
            'check your email', 'check your text', 'we sent a code', '8 chữ số', '8-digit'
        ]):
            return False
        return self._snap_has(snap, [
            'ứng dụng xác thực', 'authentication app', 'google authenticator', 'duo mobile',
            'ứng dụng tạo mã', 'code generator'
        ])

    def _doc_key_2fa_tu_xml_nhanh(self, snap):
        """Đọc nhanh Key 2FA trực tiếp từ XML của snapshot (0 click, 0 RPC) và kiểm tra sinh được OTP 6 số hợp lệ."""
        if not snap or not snap.get('raw_xml'):
            return None
        try:
            cac_chuoi = re.findall(r'(?:text|content-desc)="([^"]+)"', snap['raw_xml'])
            for s in cac_chuoi:
                s_clean = html.unescape(s).strip()
                if not s_clean or len(s_clean) < 16:
                    continue
                s_up = s_clean.upper()
                # Dạng cụm 4 ký tự cách nhau bằng khoảng trắng / gạch ngang (VD: VAEI HQNR I2PH Z4HZ XV3D IN3M BKL4 6IAS)
                m_group = re.search(r'(?<![A-Z0-9])(?:[A-Z2-7]{4}[\s-]+){3,15}[A-Z2-7]{4}(?![A-Z0-9])', s_up)
                if m_group:
                    key_cand = lam_sach_key_2fa(m_group.group(0))
                    if 16 <= len(key_cand) <= 64 and any(c.isalpha() for c in key_cand) and chuyen_doi_2fa_sang_otp(key_cand, doi_chu_ky_moi=False):
                        return key_cand
                # Dạng chuỗi liền mạch Base32 (16, 24, 32, 52, 64 ký tự)
                if re.fullmatch(r'[A-Z2-7\s-]{16,72}', s_up):
                    key_cand = lam_sach_key_2fa(s_up)
                    if 16 <= len(key_cand) <= 64 and any(c.isalpha() for c in key_cand) and chuyen_doi_2fa_sang_otp(key_cand, doi_chu_ky_moi=False):
                        return key_cand
                # Dạng nằm trong câu dài có chuỗi liền >= 16 ký tự Base32 (chứa cả chữ và số để tránh khớp từ tiếng Anh)
                for m_tok in re.finditer(r'([A-Z2-7]{16,64})', s_up):
                    tok = m_tok.group(1)
                    if any(c.isalpha() for c in tok) and any(c.isdigit() for c in tok) and chuyen_doi_2fa_sang_otp(tok, doi_chu_ky_moi=False):
                        return tok
        except Exception:
            pass
        return None

    def _lay_key_2fa_chac_chan_truoc_khi_di_tiep(self, snap_ban_dau=None):
        """
        Dừng lại trên màn hình Hình 3 (QR / Key 2FA), CHỜ hiển thị đầy đủ và đọc/sao chép CHẮC CHẮN Key 2FA
        (xác minh đổi được sang OTP 6 số hợp lệ) TRƯỚC KHI cho phép bấm nút sang ô nhập mã!
        """
        w, h = self._lay_kich_thuoc_man_hinh()
        # Chờ ngắn 1.0s để màn hình QR/Key tải trọn vẹn text & nút 'Sao chép khóa'
        time.sleep(1.0)
        for lan in range(1, 5):
            s = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh=f'Đọc Key 2FA lần {lan}')
            # Nếu lỡ không còn ở màn hình QR/Key mà đã sang ô nhập mã -> dừng trả None để vòng lặp tự Back lấy lại
            if s['edit_texts']:
                return None

            # Bước 1: Đọc thẳng từ XML (không click gì)
            key_xml = self._doc_key_2fa_tu_xml_nhanh(s)
            if key_xml:
                return key_xml

            # Bước 2: Bấm nút 'Sao chép khóa' / 'Sao chép mã' / 'Copy key' rồi đọc Clipboard (TUYỆT ĐỐI không bấm 'Tiếp')
            btn_copy = self._snap_find(s, ['Sao chép khóa', 'Sao chép mã', 'Copy key', 'Copy code', 'Sao chép', 'Copy'], exact=False)
            if btn_copy is not None:
                self.log(f'📋 [Hình 3 - Lần {lan}/4] Bấm "{btn_copy["text"] or btn_copy["desc"]}" để lấy Key 2FA vào bộ nhớ...')
                self.click_toa_do_an_toan(btn_copy['cx'], btn_copy['cy'])
                time.sleep(0.9)
                clip_text = ""
                try:
                    clip_text = self.d.clipboard or ""
                except Exception:
                    pass
                if not clip_text:
                    clip_text = chay_lenh_adb_lay_ket_qua('shell cmd clipboard get-text', self.serial)
                clean_clip = lam_sach_key_2fa(clip_text)
                if 16 <= len(clean_clip) <= 64 and chuyen_doi_2fa_sang_otp(clean_clip, doi_chu_ky_moi=False):
                    return clean_clip

            # Bước 3: Nếu chưa thấy Key trên màn hình hiện tại -> cuộn nhẹ xuống dưới mã QR để lộ dòng Key & nút Sao chép
            if lan <= 2:
                self.log(f'📜 [Hình 3 - Lần {lan}/4] Cuộn nhẹ xuống dưới mã QR để đọc Key 2FA...')
                self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.72), int(w * 0.50), int(h * 0.35), 240)
                time.sleep(0.9)
            else:
                time.sleep(0.8)

        return None

    def bat_2fa_fb(self, used_email, ten_fb="", mode="1", mail_service=None, imap_service=None, hotmail_service=None, autosms_service=None, mat_khau_fb=None):
        """
        Luồng bật 2FA theo mô hình Bám Sát Màn Hình (State Machine - chống mất Key & chuẩn nút 'Bắt đầu'):
        - Luôn đợi màn hình hết trắng / hết lag (cho_man_hinh_san_sang) trước khi nhận diện & thao tác.
        - Ở màn mở đầu bật 2FA: ưu tiên bấm đúng nút 'Bắt đầu' (không tìm nhầm 'Tiếp tục').
        - Ở màn QR/Key 2FA: CHẮC CHẮN đọc + lưu + xác minh được Key 2FA sinh ra OTP 6 số rồi MỚI bấm sang ô nhập mã.
        - Nếu lỡ sang ô nhập mã 6 số mà chưa kịp nhớ Key -> tự bấm Back quay lại màn QR/Key để đọc lại Key.
        """
        self.log('🛡️ Đang mở cài đặt Xác thực 2 yếu tố (2FA)...')
        two_fa_secret = ""
        ma_otp_6_so = ""
        da_nhap_totp_2fa = False
        so_lan_quay_lai_lay_key = 0
        w, h = self._lay_kich_thuoc_man_hinh()
        mk_tk = mat_khau_fb or self.config.get('mat_khau_fb', '')

        try:
            self.dam_bao_fb_dang_chay(max_retry=2, cho_len_giay=5.0)
            snap_bd = self.cho_man_hinh_san_sang(timeout=20.0, ngu_canh='Trước khi bật 2FA')
            self.bo_qua_luu_thong_tin_dang_nhap(snap=snap_bd)
            self.quet_va_xoa_man_hinh_chan()

            # Chốt mốc hộp thư TRƯỚC khi mở 2FA / bấm 'Bắt đầu'
            uid_moc_2fa = 0
            if mode in ["3", "4"] and imap_service:
                uid_moc_2fa = imap_service.get_latest_uid()
            elif mode == "5" and hotmail_service:
                hotmail_service.init_baseline()

            self.dieu_huong_vao_man_hinh_2fa(ten_fb=ten_fb)

            han_chot_2fa = time.time() + 180.0
            moc_doi_buoc = time.time()
            last_2fa_state = ''
            last_2fa_sig = ''
            last_2fa_ts = 0.0
            so_lan_phuc_hoi_la_2fa = 0

            def _dang_cho_chuyen_2fa(ten_buoc, cur_sig, nguong_giay=6.5):
                return (
                    last_2fa_state == ten_buoc
                    and last_2fa_sig == cur_sig
                    and (time.time() - last_2fa_ts) < nguong_giay
                )

            def _danh_dau_2fa(ten_buoc, cur_sig):
                nonlocal last_2fa_state, last_2fa_sig, last_2fa_ts, moc_doi_buoc, so_lan_phuc_hoi_la_2fa
                last_2fa_state = ten_buoc
                last_2fa_sig = cur_sig
                last_2fa_ts = time.time()
                moc_doi_buoc = time.time()
                so_lan_phuc_hoi_la_2fa = 0

            while time.time() < han_chot_2fa and not STOP_EVENT.is_set():
                try:
                    # 1. ĐỢI màn hình hết trắng / hết lag trước khi nhận diện!
                    snap = self.cho_man_hinh_san_sang(timeout=25.0, ngu_canh='Bám sát 2FA')
                    if snap['is_blank_or_loading']:
                        self.log('⚠️ Màn hình 2FA treo trắng quá lâu -> Dừng bước 2FA!')
                        return two_fa_secret if da_nhap_totp_2fa else ""

                    # Nếu vừa thao tác xong và màn hình vẫn đang có vòng xoay tải -> đứng chờ chuyển trang, KHÔNG làm lại lần 2!
                    if snap.get('has_progress') and (time.time() - last_2fa_ts) < 8.0:
                        time.sleep(0.45)
                        continue

                    # 2. Dọn popup chắn / lỗi tải tại chỗ (truyền `snap`, không dump thừa, KHÔNG tắt Wi-Fi/FB!)
                    if self.quet_va_xoa_man_hinh_chan(so_vong_quet=2, snap=snap):
                        moc_doi_buoc = time.time()
                        continue
                    if self._kiem_tra_va_xu_ly_loi_mang_2fa(snap=snap):
                        moc_doi_buoc = time.time()
                        continue

                    # 3. Màn hình HOÀN TẤT bật 2FA (chỉ khi đã lấy Key & nhập mã TOTP 6 số xong)
                    if da_nhap_totp_2fa and self._snap_has(snap, [
                        'Đã bật xác thực', 'Two-factor authentication is on',
                        'Xong', 'Done', 'Hoàn tất', 'Mã khôi phục', 'Recovery codes'
                    ]):
                        for _ in range(3):
                            s_end = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Hoàn tất 2FA')
                            if self._snap_click(s_end, ['Xong', 'Done', 'Hoàn tất', 'OK'], exact=True, click_duoi=True):
                                self._cho_chuyen_man_hinh(s_end['sig'], timeout=2.2)
                            else:
                                break
                        self.log(f'✅ ĐÃ BẬT 2FA HOÀN TẤT! Key: {two_fa_secret} (OTP: {ma_otp_6_so})')
                        return two_fa_secret

                    # 4. ĐÃ nhớ Key 2FA & đang ở ô nhập mã TOTP 6 số -> Sinh OTP 6 số, nhập 1 lần sạch & chờ chuyển trang
                    if two_fa_secret and (snap['edit_texts'] or self._snap_has(snap, ['Nhập mã', 'Mã xác nhận', '6 chữ số', 'Enter code', 'Confirmation code'])):
                        if _dang_cho_chuyen_2fa('2FA_TOTP', snap['sig'], 8.0):
                            time.sleep(0.5)
                            continue
                        ma_otp_6_so = chuyen_doi_2fa_sang_otp(two_fa_secret, doi_chu_ky_moi=True)
                        if ma_otp_6_so:
                            self._nhap_ma_so_va_bam_tiep_2fa(
                                ma_otp_6_so,
                                nhan_log="Hình 4 - Mã 2FA 6 số",
                                totp_secret=two_fa_secret,
                                max_attempts=1
                            )
                            da_nhap_totp_2fa = True
                            _danh_dau_2fa('2FA_TOTP', snap['sig'])
                            continue

                    # 4B. TỰ PHỤC HỒI: Lỡ sang ô nhập mã 6 số của Ứng dụng xác thực mà CHƯA có Key -> Back lại màn QR/Key đọc Key!
                    if not two_fa_secret and self._la_man_hinh_o_nhap_ma_totp_2fa(snap) and so_lan_quay_lai_lay_key < 2:
                        so_lan_quay_lai_lay_key += 1
                        self.log(f'↩️ [2FA] Đang ở ô nhập mã 6 số nhưng chưa có Key -> Quay lại màn QR/Key để đọc Key (lần {so_lan_quay_lai_lay_key}/2)...')
                        self._ha_ban_phim_an_toan()
                        try:
                            self.d.press('back')
                        except Exception:
                            self.chay_shell_nhanh('input keyevent 4')
                        time.sleep(1.2)
                        _danh_dau_2fa('2FA_BACK_KEY', snap['sig'])
                        continue

                    # 5. Màn hình Hình 3 (QR + Secret Key 2FA): ĐỌC & NHỚ CHẮC CHẮN Key 2FA rồi MỚI bấm sang ô nhập mã!
                    if self._la_man_hinh_qr_key_2fa(snap) or self._doc_key_2fa_tu_xml_nhanh(snap):
                        if two_fa_secret and _dang_cho_chuyen_2fa('2FA_QR_NEXT', snap['sig'], 6.0):
                            time.sleep(0.5)
                            continue
                        key_chuan = two_fa_secret or self._lay_key_2fa_chac_chan_truoc_khi_di_tiep(snap_ban_dau=snap)
                        if key_chuan:
                            two_fa_secret = key_chuan
                            otp_test = chuyen_doi_2fa_sang_otp(two_fa_secret, doi_chu_ky_moi=False)
                            self.log(f'🔑 [Hình 3] ĐÃ NHỚ CHẮC CHẮN Key 2FA: {two_fa_secret} (OTP thử: {otp_test}) -> Chuyển sang ô nhập mã...')
                            s_now = self.quet_snapshot()
                            prev_s = s_now['sig']
                            btn_di_tiep = self._snap_find(s_now, ['Tiếp', 'Tiếp tục', 'Bắt đầu', 'Next', 'Continue', 'Get started'], exact=True, click_duoi=True, min_y=0.60)
                            if btn_di_tiep is not None:
                                self.log(f'⏩ [Hình 3] Bấm nút "{btn_di_tiep["text"] or btn_di_tiep["desc"]}" sang ô nhập mã...')
                                self.click_toa_do_an_toan(btn_di_tiep['cx'], btn_di_tiep['cy'])
                            else:
                                self._bam_nut_xanh_duoi_day_2fa(['Tiếp', 'Tiếp tục', 'Bắt đầu', 'Next', 'Continue', 'Get started'], fallback_y_ratio=0.892)
                            self._cho_chuyen_man_hinh(prev_s, timeout=5.0)
                            _danh_dau_2fa('2FA_QR_NEXT', prev_s)
                            continue
                        else:
                            self.log('⚠️ [Hình 3] Chưa đọc được Key 2FA trên màn hình -> Dừng lại chờ đọc lại, KHÔNG bấm sang ô nhập mã!')
                            time.sleep(0.9)
                            continue

                    # 5.0 (ƯU TIÊN CAO): Màn hình mở đầu bảo vệ tăng cường ("Thiết lập phương thức bảo vệ tăng cường cho Tài khoản Meta") -> Bấm nút xanh "Bắt đầu" NGAY!
                    if not _dang_cho_chuyen_2fa('2FA_START', snap['sig'], 6.0) and self._xu_ly_man_hinh_bat_dau_bao_ve_meta(snap=snap):
                        _danh_dau_2fa('2FA_START', snap['sig'])
                        continue

                    # 5A. Nếu đang đứng ở màn Trung tâm tài khoản Meta (có "Đăng nhập và bảo mật" nhưng chưa thấy "Xác thực 2 yếu tố") -> Quét & bấm đúng chữ "Đăng nhập và bảo mật"!
                    if (
                        not da_nhap_totp_2fa
                        and not snap['edit_texts']
                        and not self._snap_has(snap, ['Xác thực 2 yếu tố', 'Xác thực hai yếu tố', 'Two-factor authentication'])
                        and self._snap_has(snap, ['Đăng nhập và bảo mật', 'Mật khẩu và bảo mật', 'Sign-in and security', 'Login and security', 'Password and security'])
                    ):
                        la_menu_meta = self._snap_has(snap, [
                            'trải nghiệm liên trang cá nhân', 'thông tin và quyền của bạn',
                            'quản lý tài khoản', 'tùy chọn quảng cáo', 'meta pay',
                            'hành động đề xuất', 'connected experiences', 'accounts center', 'trung tâm tài khoản'
                        ])
                        node_bm_2fa = self._snap_find(
                            snap,
                            ['Đăng nhập và bảo mật', 'Mật khẩu và bảo mật', 'Sign-in and security', 'Login and security', 'Password and security'],
                            exact=False,
                            min_y=0.12,
                            max_y=0.92
                        )
                        if node_bm_2fa is not None and (la_menu_meta or node_bm_2fa['cy'] >= int(h * 0.15)):
                            if _dang_cho_chuyen_2fa('2FA_SECURITY_ROW', snap['sig'], 5.5):
                                time.sleep(0.45)
                                continue
                            prev_s = snap['sig']
                            nhan_bm = self._tim_va_bam_chu_dong(
                                snap,
                                ['Đăng nhập và bảo mật', 'Mật khẩu và bảo mật', 'Sign-in and security', 'Login and security', 'Password and security'],
                                min_y=0.12,
                                max_y=0.92
                            )
                            if nhan_bm:
                                self.log(f'🔐 [2FA - Quét chữ] Đang ở Trung tâm TK Meta -> Bấm "{nhan_bm}"...')
                                self._cho_chuyen_man_hinh(prev_s, timeout=5.0)
                                _danh_dau_2fa('2FA_SECURITY_ROW', prev_s)
                                continue

                    # 5B. Nếu đang đứng ở màn có mục "Xác thực 2 yếu tố" -> Quét & bấm đúng chữ "Xác thực 2 yếu tố"
                    if (
                        not da_nhap_totp_2fa
                        and not snap['edit_texts']
                        and self._snap_has(snap, ['Xác thực 2 yếu tố', 'Xác thực hai yếu tố', 'Two-factor authentication'])
                    ):
                        if _dang_cho_chuyen_2fa('2FA_MENU_ENTRY', snap['sig'], 5.0):
                            time.sleep(0.45)
                            continue
                        prev_s = snap['sig']
                        nhan_2fa = self._tim_va_bam_chu_dong(
                            snap,
                            ['Xác thực 2 yếu tố', 'Xác thực hai yếu tố', 'Two-factor authentication'],
                            exclude_keywords=['đã bật xác thực', 'is on'],
                            min_y=0.10,
                            max_y=0.92
                        )
                        if nhan_2fa:
                            self.log(f'🔄 [2FA - Quét chữ] Bấm vào "{nhan_2fa}"...')
                            self._cho_chuyen_man_hinh(prev_s, timeout=4.5)
                            _danh_dau_2fa('2FA_MENU_ENTRY', prev_s)
                            continue

                    # 5C. Nếu hiện màn hình "Chọn tài khoản" thực sự để thiết lập 2FA -> Quét chữ tên FB (KHÔNG dùng tọa độ cố định!)
                    if (
                        not da_nhap_totp_2fa
                        and not snap['edit_texts']
                        and self._snap_has(snap, ['Chọn tài khoản', 'Select an account', 'Chọn trang cá nhân', 'Choose an account'])
                        and not self._snap_has(snap, ['Chọn phương thức bảo mật', 'Thiết lập phương thức bảo vệ tăng cường', 'Đăng nhập và bảo mật', 'Quản lý tài khoản'])
                    ):
                        if _dang_cho_chuyen_2fa('2FA_PICK_ACC', snap['sig'], 5.0):
                            time.sleep(0.45)
                            continue
                        prev_s = snap['sig']
                        ds_tk_2fa = ([ten_fb] if ten_fb else []) + ['Facebook']
                        nhan_tk = self._tim_va_bam_chu_dong(
                            snap,
                            ds_tk_2fa,
                            exclude_keywords=['facebook plus', 'facebook pay', 'chọn tài khoản', 'select an account', 'meta'],
                            min_y=0.15,
                            max_y=0.80
                        )
                        if nhan_tk:
                            self.log(f'👤 [2FA - Quét chữ] Màn hình Chọn tài khoản -> Chọn "{nhan_tk}"...')
                            self._cho_chuyen_man_hinh(prev_s, timeout=4.5)
                            _danh_dau_2fa('2FA_PICK_ACC', prev_s)
                            continue

                    # 5D. Nếu đang ở trang Cài đặt và quyền riêng tư có "Tài khoản Meta" / "Trung tâm tài khoản" -> Quét & bấm đúng chữ đó (TUYỆT ĐỐI loại trừ màn hình "Thiết lập phương thức bảo vệ tăng cường cho Tài khoản Meta"!)
                    if (
                        not da_nhap_totp_2fa
                        and not self._snap_has(snap, ['Đăng nhập và bảo mật', 'Mật khẩu và bảo mật', 'Xác thực 2 yếu tố', 'Xác thực hai yếu tố', 'Two-factor authentication'])
                        and not self._snap_has(snap, [
                            'Vì lý do bảo mật', 'Nhập lại mật khẩu', 'Nhập mật khẩu', 'Nhập mã', 'Mã xác nhận', 'Enter code', 'Enter your password',
                            'Thiết lập phương thức bảo vệ tăng cường', 'bảo vệ tăng cường', 'Set up extra protection',
                            'Chọn phương thức bảo mật', 'Ứng dụng xác thực', 'Sao chép khóa', 'Copy key'
                        ])
                        and not self._snap_has(snap, ['Bắt đầu', 'Get started'], exact=True)
                        and self._snap_has(snap, [
                            'Tài khoản Meta', 'Xem thêm trong Trung tâm tài khoản', 'Trung tâm tài khoản',
                            'Mật khẩu, bảo mật, thông tin cá nhân',
                            'Meta Accounts Center', 'Meta Accounts', 'See more in Accounts Center', 'Accounts Center'
                        ])
                    ):
                        if _dang_cho_chuyen_2fa('2FA_ACCOUNTS_CENTER', snap['sig'], 5.5):
                            time.sleep(0.45)
                            continue
                        prev_s = snap['sig']
                        nhan_tt = self._tim_va_bam_chu_dong(
                            snap,
                            [
                                'Tài khoản Meta', 'Xem thêm trong Trung tâm tài khoản', 'Trung tâm tài khoản',
                                'Mật khẩu, bảo mật, thông tin cá nhân',
                                'Meta Accounts Center', 'Meta Accounts', 'See more in Accounts Center', 'Accounts Center'
                            ],
                            exclude_keywords=[
                                'meta đã xác minh', 'meta verified', 'meta pay',
                                'sản phẩm khác của meta', 'cũng từ meta', 'also from meta',
                                'facebook plus', 'tìm kiếm cài đặt', 'search settings',
                                'thiết lập phương thức', 'bảo vệ tăng cường', 'tăng cường cho tài khoản',
                                'extra protection', 'set up extra'
                            ],
                            min_y=0.10,
                            max_y=0.85
                        )
                        if nhan_tt:
                            self.log(f'⚙️ [2FA - Quét chữ] Bấm "{nhan_tt}" (không dùng tọa độ cố định)...')
                            self._cho_chuyen_man_hinh(prev_s, timeout=5.0)
                            _danh_dau_2fa('2FA_ACCOUNTS_CENTER', prev_s)
                            continue

                    # 7. Màn hình yêu cầu nhập lại Mật khẩu ('Vì lý do bảo mật...')
                    if self._snap_has(snap, [
                        'Vì lý do bảo mật', 'vui lòng nhập lại mật khẩu', 'nhập lại mật khẩu của bạn',
                        'Nhập lại mật khẩu', 'Nhập mật khẩu', 'For your security', 'Enter your password', 'Re-enter your password'
                    ]):
                        if _dang_cho_chuyen_2fa('2FA_PASS', snap['sig'], 8.0):
                            time.sleep(0.5)
                            continue
                        self._nhap_mat_khau_xac_nhan_2fa_hinh_2(mat_khau_fb=mk_tk, snap=snap)
                        _danh_dau_2fa('2FA_PASS', snap['sig'])
                        continue

                    # 8. Màn hình 'Chọn phương thức bảo mật' -> Đã tích sẵn 'Ứng dụng xác thực' thì bấm 1 lần nút xanh 'Tiếp'
                    if (
                        not snap['edit_texts']
                        and not self._la_man_hinh_qr_key_2fa(snap)
                        and self._snap_has(snap, [
                            'Chọn phương thức bảo mật', 'Choose a security method',
                            'Thiết lập cách chứng minh đó là bạn', 'Giúp bảo vệ tài khoản của bạn',
                            'Dùng ứng dụng xác thực', 'Sử dụng ứng dụng xác thực',
                            'Use authentication app'
                        ])
                    ):
                        if _dang_cho_chuyen_2fa('2FA_METHOD', snap['sig'], 6.5):
                            time.sleep(0.5)
                            continue
                        self._xu_ly_chon_phuong_thuc_bao_mat_2fa(snap=snap)
                        _danh_dau_2fa('2FA_METHOD', snap['sig'])
                        continue

                    # 9. Màn hình xác nhận gửi mã OTP Email/SMS phụ hoặc nhập OTP Email phụ
                    if not two_fa_secret and (
                        (not snap['edit_texts'] and self._snap_has(snap, [
                            'Gửi mã', 'Nhận mã', 'Chọn cách xác nhận', 'Xác nhận rằng đó là bạn',
                            'Chúng tôi có thể gửi mã', 'Chúng tôi sẽ gửi mã', 'Send code', 'Get a code'
                        ]))
                        or (
                            not self._la_man_hinh_o_nhap_ma_totp_2fa(snap)
                            and not self._la_man_hinh_qr_key_2fa(snap)
                            and (
                                self._snap_has(snap, [
                                    'Kiểm tra email', 'Kiểm tra hộp thư', 'Check your email',
                                    'Kiểm tra tin nhắn', 'Kiểm tra điện thoại', 'Check your text',
                                    'Chúng tôi đã gửi mã', 'gửi mã đến', 'gửi mã tới',
                                    'We sent a code', 'mã gồm 8 chữ số', '8 chữ số', '8-digit'
                                ])
                                or (
                                    bool(snap['edit_texts'])
                                    and self._snap_has(snap, ['Nhập mã', 'Mã xác nhận', 'Mã bảo mật', 'Enter code', 'Confirmation code'])
                                )
                            )
                        )
                    ):
                        if _dang_cho_chuyen_2fa('2FA_EMAIL_OTP', snap['sig'], 8.0):
                            time.sleep(0.5)
                            continue
                        kq_otp_phu = self._nhap_otp_hoac_mk_phu_2fa(
                            used_email, mode, mail_service, imap_service, hotmail_service, autosms_service,
                            ten_fb=ten_fb, mat_khau_fb=mk_tk, uid_moc_2fa=uid_moc_2fa
                        )
                        if kq_otp_phu == 'SKIP_2FA_MODE6':
                            return ""
                        _danh_dau_2fa('2FA_EMAIL_OTP', snap['sig'])
                        continue

                    # 10. Nếu đã nhập xong TOTP 6 số nhưng màn hình quay về trang 2FA/Cài đặt không có nút Xong -> coi như xong!
                    if da_nhap_totp_2fa and not snap['edit_texts'] and self._snap_has(snap, ['Xác thực 2 yếu tố', 'Ứng dụng xác thực', 'Two-factor authentication']):
                        self.log(f'✅ ĐÃ BẬT 2FA HOÀN TẤT! Key: {two_fa_secret} (OTP: {ma_otp_6_so})')
                        return two_fa_secret

                    # 11. Xử lý màn hình lạ tại chỗ (KHÔNG tắt Wi-Fi / KHÔNG thoát FB)
                    thoi_gian_dung = time.time() - moc_doi_buoc
                    if thoi_gian_dung > 12.0 and so_lan_phuc_hoi_la_2fa < 2:
                        so_lan_phuc_hoi_la_2fa += 1
                        self.log(f'🔎 [2FA - Màn lạ lần {so_lan_phuc_hoi_la_2fa}/2] Đang thấy: {self._tom_tat_man_hinh(snap)}')
                        self._ha_ban_phim_an_toan()
                        self.dong_goi_y_google(max_thu=2)
                        if self._snap_click(snap, ['OK', 'Đóng', 'Close', 'Thử lại', 'Try again'], exact=True):
                            time.sleep(1.0)
                        else:
                            self.dieu_huong_vao_man_hinh_2fa(ten_fb=ten_fb)
                        moc_doi_buoc = time.time()
                        continue

                    if thoi_gian_dung > 35.0:
                        self.log(f'⚠️ Quá 35s màn hình 2FA không chuyển bước [{self._tom_tat_man_hinh(snap)}] -> Thoát bước 2FA!')
                        return two_fa_secret if da_nhap_totp_2fa else ""

                    time.sleep(0.35)
                except (AccountDieError, KeyboardInterrupt):
                    raise
                except Exception as err_2fa_step:
                    self.log(f'⚠️ [2FA - Phục hồi tại chỗ] Lỗi tạm thời ({str(err_2fa_step)[:40]}) -> Đọc lại màn hình làm tiếp...')
                    time.sleep(0.8)
                    if self._consecutive_dump_errors >= 2:
                        self._phuc_hoi_u2_nhe()

            return two_fa_secret if da_nhap_totp_2fa else ""
        except AccountDieError:
            raise
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            self.log(f'⚠️ Lỗi khi bật 2FA: {str(e)[:40]}')
            return two_fa_secret if da_nhap_totp_2fa else ""

    def _tach_uid_tu_chuoi_url(self, text_blob):
        """Giải mã URL-encode 2 lần rồi tách chính xác UID số Facebook (chống sót `%3Fid%3D615...` khi FB redirect về /login/?next=...)."""
        if not text_blob:
            return ""
        cand_raw = str(text_blob)
        cand_dec1 = urllib.parse.unquote(cand_raw)
        cand_dec2 = urllib.parse.unquote(cand_dec1)
        cand_compact = re.sub(r'\s+', '', cand_dec2)
        for blob in (cand_raw, cand_dec1, cand_dec2, cand_compact):
            for pat in [
                r'(?:[?&]id=|/profile\.php\?id=|fb://profile/|fb://page/)\s*(\d{9,20})\b',
                r'/people/[^/?#]+/(\d{9,20})(?:/|\?|$)',
                r'"(?:userID|actorID|entity_id|profile_id|selectedID|uid|user_id|delegate_page_id|fbid|owner_id)"\s*:\s*"?(\d{9,20})"?',
                r'(?:profile_id|entity_id|fbid)(?:=|%3D)\s*(\d{9,20})\b',
            ]:
                m = re.search(pat, blob, re.IGNORECASE)
                if m:
                    uid_cand = m.group(1)
                    if not uid_cand.startswith('0'):
                        return uid_cand
        return ""

    def _chuan_hoa_link_fb(self, raw_text):
        """Trích xuất và chuẩn hóa URL Facebook sạch (facebook.com / fb.com / fb.me) từ một chuỗi bất kỳ."""
        if not raw_text:
            return ""
        s = str(raw_text).strip()
        m_u = re.search(r'(?:https?://)?(?:www\.|m\.|mbasic\.|web\.)?(?:facebook\.com|fb\.com|fb\.me)/[^\s"<>]+', s, re.IGNORECASE)
        if not m_u:
            return ""
        url = m_u.group(0).rstrip('.,;)')
        low = url.lower()
        if any(bad in low for bad in ('/help', '/policies', '/privacy', '/terms', '/settings', '/login', '/legal', '/business')):
            return ""
        if not low.startswith(('http://', 'https://')):
            url = 'https://' + url.lstrip('/')
        return url

    def _xoa_clipboard_truoc_khi_copy(self):
        """Làm trống Clipboard trước khi bấm Sao chép để không đọc nhầm link của tài khoản cũ."""
        try:
            self.d.set_clipboard('')
        except Exception:
            pass

    def _doc_clipboard_nhanh(self):
        """Đọc nhanh Clipboard không mở chuyển màn hình (trả về URL Facebook sạch nếu có)."""
        for getter in [
            lambda: (self.d.clipboard or '').strip(),
            lambda: chay_lenh_adb_lay_ket_qua('shell cmd clipboard get-text', self.serial, timeout=4).strip(),
        ]:
            try:
                val = getter()
                link_clean = self._chuan_hoa_link_fb(val)
                if link_clean:
                    return link_clean
                if val and self._tach_uid_tu_chuoi_url(val):
                    return val
            except Exception:
                pass
        return ""

    def _doc_clipboard_vong_qua_android10(self):
        """
        Đọc Clipboard an toàn trên mọi đời Android 10-15 (kể cả MIUI/HyperOS chặn đọc clipboard nền):
        1. Thử `d.clipboard` và `cmd clipboard get-text`.
        2. Nếu vẫn rỗng -> mở nhanh ô tìm kiếm của chính Facebook (`fb://search` đang ở foreground),
           dán bằng `KEYCODE_PASTE (279)` rồi đọc toàn văn đường link từ `EditText` trong snapshot!
        """
        fast_val = self._doc_clipboard_nhanh()
        if fast_val:
            return fast_val

        # Cách vượt chặn Clipboard Android 10-15: dán trực tiếp vào ô EditText của Facebook Search (foreground!)
        try:
            uf = self._u_flag()
            self.chay_shell_nhanh(f'am start {uf}-a android.intent.action.VIEW -d "fb://search" com.facebook.katana')
            time.sleep(1.3)
            snap_s = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Đọc link từ Clipboard qua Search', check_die=False)
            ed = snap_s['edit_texts'][0] if snap_s.get('edit_texts') else None
            if ed is not None:
                self.click_toa_do_an_toan(ed['cx'], ed['cy'])
                time.sleep(0.35)
                self.chay_shell_nhanh('input keyevent 279')
                time.sleep(0.55)
                snap_pasted = self.quet_snapshot()
                for ed2 in snap_pasted.get('edit_texts') or []:
                    t_ed = (ed2.get('text') or '').strip()
                    link_clean = self._chuan_hoa_link_fb(t_ed)
                    if link_clean:
                        self._ha_ban_phim_an_toan()
                        return link_clean
                    if self._tach_uid_tu_chuoi_url(t_ed):
                        self._ha_ban_phim_an_toan()
                        return t_ed
                self._ha_ban_phim_an_toan()
        except Exception:
            pass
        return ""

    def _trich_xuat_uid_tu_phan_hoi_api(self, resp):
        """
        Trích xuất an toàn UID số (9-20 chữ số, không bắt đầu bằng 0) từ phản hồi JSON hoặc HTML của API/web tra cứu UID.
        Tránh tuyệt đối nhận nhầm HTTP status code (200/404) hoặc chuỗi rác.
        """
        if resp is None:
            return ""

        def _la_uid_hop_le(val):
            s = str(val or '').strip()
            return bool(re.fullmatch(r'[1-9]\d{8,19}', s))

        # 1. Ưu tiên đọc JSON (id, uid, fbid, user_id, profile_id, data.id, data.uid, result.id...)
        try:
            js = resp.json()
            if isinstance(js, dict):
                objs_to_check = [js]
                for sub_k in ('data', 'result', 'profile', 'user', 'response'):
                    sub_v = js.get(sub_k)
                    if isinstance(sub_v, dict):
                        objs_to_check.append(sub_v)
                    elif isinstance(sub_v, str) and _la_uid_hop_le(sub_v):
                        return sub_v.strip()

                for obj in objs_to_check:
                    for key in ('uid', 'id', 'fbid', 'user_id', 'profile_id', 'numeric_id', 'facebook_id'):
                        if key in obj:
                            cand = obj.get(key)
                            if _la_uid_hop_le(cand):
                                return str(cand).strip()
                            if isinstance(cand, str):
                                uid_u = self._tach_uid_tu_chuoi_url(cand)
                                if uid_u:
                                    return uid_u
        except Exception:
            pass

        # 2. Đọc từ HTML / văn bản (VD: lookup-id.com trả `<p id="code">615...</p>` hoặc plain text)
        txt = (getattr(resp, 'text', '') or '')[:120000]
        if not txt.strip():
            return ""

        txt_strip = txt.strip()
        if _la_uid_hop_le(txt_strip):
            return txt_strip

        for pat_html in [
            r'id=["\']code["\'][^>]*>\s*([1-9]\d{8,19})\s*<',
            r'id=["\'](?:uid|fbid|result_uid)["\'][^>]*>\s*([1-9]\d{8,19})\s*<',
            r'value=["\']([1-9]\d{8,19})["\'][^>]*id=["\'](?:uid|code|fbid)["\']',
            r'class=["\'][^"\']*(?:uid|code-result|fb-id)[^"\']*["\'][^>]*>\s*([1-9]\d{8,19})\s*<',
        ]:
            m_h = re.search(pat_html, txt, re.IGNORECASE)
            if m_h:
                return m_h.group(1)

        uid_blob = self._tach_uid_tu_chuoi_url(txt)
        if uid_blob:
            return uid_blob

        return ""

    def _tra_cuu_uid_qua_api_web(self, raw_url, proxies=None):
        """
        Hàm dự phòng gọi các API / web chuyển đổi link Facebook (kể cả dạng `/share/1...` hoặc username) sang UID số
        khi cách đọc Redirect 302 mặc định không lấy được UID:
        1. API tùy chỉnh do người dùng cấu hình trong `config_reg_fb.json` (`api_chuyen_link_sang_uid`).
        2. `id.traodoisub.com/api.php` (POST form `link=...`).
        3. `ffb.vn/api/tool/get-id-fb` (POST form `idfb=...`).
        4. `fbuid.mktsoftware.net/api/v1/fbprofile` (POST JSON `url=...`).
        5. `lookup-id.com/` (POST form `fburl=...&check=Lookup`).
        6. `api.findids.net/api/get-uid-from-username` (khi URL có username).
        """
        if not raw_url:
            return ""
        url = str(raw_url).strip()
        if not url:
            return ""

        self.log('🌐 [Lấy UID - Dự phòng API/Web] Redirect 302 chưa ra UID -> Chuyển sang tra cứu qua API/Web...')

        common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        }

        # Danh sách nhà cung cấp API/web (ưu tiên mạng PC trực tiếp trước, nếu lỗi mới thử qua proxy)
        proxy_order = [None, proxies] if proxies else [None]
        providers = []

        # 1. API tùy chỉnh trong config_reg_fb.json (nếu người dùng tự cấu hình)
        custom_api = ""
        try:
            if isinstance(self.config, dict):
                custom_api = str(self.config.get('api_chuyen_link_sang_uid') or '').strip()
        except Exception:
            custom_api = ""

        if custom_api:
            if '{url}' in custom_api:
                enc_u = urllib.parse.quote(url, safe='')
                providers.append(('Custom API (GET)', 'GET', custom_api.replace('{url}', enc_u), None, None, common_headers))
            else:
                providers.append(('Custom API (POST)', 'POST', custom_api, {'link': url, 'url': url}, None, common_headers))

        # 2. Các API/Web công khai phổ biến hỗ trợ link Facebook /share/1... & profile
        providers.extend([
            (
                'TraoDoiSub API',
                'POST',
                'https://id.traodoisub.com/api.php',
                {'link': url},
                None,
                {**common_headers, 'Origin': 'https://id.traodoisub.com', 'Referer': 'https://id.traodoisub.com/'}
            ),
            (
                'FFB.vn API',
                'POST',
                'https://ffb.vn/api/tool/get-id-fb',
                {'idfb': url},
                None,
                {**common_headers, 'Origin': 'https://ffb.vn', 'Referer': 'https://ffb.vn/get-uid-facebook'}
            ),
            (
                'MKTSoftware FBUID API',
                'POST',
                'https://fbuid.mktsoftware.net/api/v1/fbprofile',
                None,
                {'url': url},
                {**common_headers, 'Content-Type': 'application/json'}
            ),
            (
                'Lookup-ID Web',
                'POST',
                'https://lookup-id.com/',
                {'fburl': url, 'check': 'Lookup'},
                None,
                {**common_headers, 'Origin': 'https://lookup-id.com', 'Referer': 'https://lookup-id.com/'}
            ),
        ])

        # Nếu link có dạng username (facebook.com/<username>, không phải /share/ hay profile.php) -> bổ sung FindIDs API
        m_user = re.match(r'^https?://(?:www\.|m\.|mbasic\.)?(?:facebook\.com|fb\.com)/([A-Za-z0-9._-]{3,60})/?(?:\?.*)?$', url, re.IGNORECASE)
        if m_user:
            uname = m_user.group(1)
            if uname.lower() not in ('share', 'profile.php', 'people', 'pages', 'groups', 'watch', 'reel', 'reels', 'p', 'story.php'):
                providers.append((
                    'FindIDs API',
                    'POST',
                    'https://api.findids.net/api/get-uid-from-username',
                    {'username': uname},
                    None,
                    common_headers
                ))

        for ten_api, method, ep_url, form_data, json_data, hdrs in providers:
            if STOP_EVENT.is_set():
                return ""
            for px in proxy_order:
                try:
                    if method == 'GET':
                        r = requests.get(ep_url, headers=hdrs, proxies=px, timeout=8)
                    elif json_data is not None:
                        r = requests.post(ep_url, json=json_data, headers=hdrs, proxies=px, timeout=8)
                    else:
                        r = requests.post(ep_url, data=form_data, headers=hdrs, proxies=px, timeout=8)

                    uid_api = self._trich_xuat_uid_tu_phan_hoi_api(r)
                    if uid_api:
                        self.log(f'✅ [Dự phòng {ten_api}] Chuyển đổi thành công -> UID: {uid_api}')
                        return uid_api
                    # Nếu server phản hồi bình thường (HTTP 200) nhưng không ra UID thì chuyển sang API kế tiếp luôn
                    if r.status_code == 200:
                        break
                except Exception:
                    continue

        return ""

    def _giai_ma_uid_tu_link_fb(self, raw_url, proxies=None):
        """
        Tách UID số chuẩn 100% từ mọi dạng link trang cá nhân Facebook:
        1. `facebook.com/profile.php?id=615...` -> tách trực tiếp (0 request).
        2. Đọc Redirect 302 hop-by-hop & HTML/Meta (www / m / mbasic + User-Agent facebookexternalhit cho link `/share/1...`).
        3. Dự phòng `curl -sI -L` trực tiếp từ chính điện thoại Android (đang có 4G/Proxy sạch).
        4. Dự phòng gọi API/Web chuyển đổi link `/share/1...` -> UID số (`_tra_cuu_uid_qua_api_web`).
        """
        if not raw_url:
            return ""
        url = str(raw_url).strip()
        if not url:
            return ""
        if not url.lower().startswith(('http://', 'https://')):
            if any(d in url.lower() for d in ('facebook.com', 'fb.com', 'fb.me')):
                url = 'https://' + url.lstrip('/')
            else:
                return ""

        # 1. Tách thẳng nếu đã có UID ngay trong link
        uid_direct = self._tach_uid_tu_chuoi_url(url)
        if uid_direct:
            return uid_direct

        # Tạo các biến thể URL (www / m / mbasic) để vượt login wall của link /share/1...
        url_variants = [url]
        m_dom = re.match(r'^https?://(?:www\.|m\.|mbasic\.)?(facebook\.com/.*)$', url, re.IGNORECASE)
        if m_dom:
            tail = m_dom.group(1)
            for host in ('https://www.', 'https://m.', 'https://mbasic.'):
                cand_u = host + tail
                if cand_u not in url_variants:
                    url_variants.append(cand_u)

        header_sets = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            },
        ]

        proxy_candidates = [proxies, None] if proxies else [None]
        resolved_link_alt = ""

        # 2. Thử bắt Redirect 302 hop-by-hop & HTML/Meta trên PC (giới hạn timeout gọn để nhanh chuyển sang dự phòng API/Web)
        for px in proxy_candidates:
            for target_u in url_variants[:3]:
                for hdr in header_sets:
                    if STOP_EVENT.is_set():
                        return ""
                    try:
                        sess = requests.Session()
                        # 2A. Kiểm tra Location hop đầu tiên (allow_redirects=False) — link /share/ thường trả thẳng profile.php?id=...
                        r0 = sess.get(target_u, headers=hdr, proxies=px, allow_redirects=False, timeout=6)
                        loc0 = str(r0.headers.get('Location', '') or '')
                        uid_loc0 = self._tach_uid_tu_chuoi_url(loc0)
                        if uid_loc0:
                            return uid_loc0
                        if loc0 and 'facebook.com/' in loc0.lower() and '/login' not in loc0.lower() and '/share/' not in loc0.lower():
                            resolved_link_alt = resolved_link_alt or self._chuan_hoa_link_fb(loc0)

                        # 2B. Theo dõi redirect đầy đủ + quét history + quét body HTML/Meta/JSON
                        r = sess.get(target_u, headers=hdr, proxies=px, allow_redirects=True, timeout=8)
                        for check_u in [str(getattr(r, 'url', '') or '')] + [
                            str(h_item.headers.get('Location', '') or '') for h_item in (getattr(r, 'history', None) or [])
                        ]:
                            uid_h = self._tach_uid_tu_chuoi_url(check_u)
                            if uid_h:
                                return uid_h
                            if check_u and 'facebook.com/' in check_u.lower() and '/login' not in check_u.lower() and '/share/' not in check_u.lower():
                                resolved_link_alt = resolved_link_alt or self._chuan_hoa_link_fb(check_u)

                        body = (r.text or '')[:220000]
                        uid_body = self._tach_uid_tu_chuoi_url(body)
                        if uid_body:
                            return uid_body
                    except Exception:
                        continue

        # 3. Dự phòng trực tiếp từ điện thoại (dùng mạng 4G/Proxy đang chạy trên máy Android qua curl -sI)
        try:
            safe_u = url.replace("'", "")
            _, out_curl = chay_lenh_adb_list(
                ['shell', 'curl', '-sI', '-L', '--max-redirs', '3', '--max-time', '8', '-A', 'Mozilla/5.0', safe_u],
                self.serial,
                timeout=10
            )
            uid_c = self._tach_uid_tu_chuoi_url(out_curl)
            if uid_c:
                return uid_c
        except Exception:
            pass

        # 4. Dự phòng gọi API / Web chuyển đổi link `/share/1...` (và link đích nếu có) sang UID số
        for cand_api_u in ([url, resolved_link_alt] if (resolved_link_alt and resolved_link_alt != url) else [url]):
            uid_web = self._tra_cuu_uid_qua_api_web(cand_api_u, proxies=proxies)
            if uid_web:
                return uid_web

        return ""

    def _trich_xuat_link_hoac_uid_tu_snap(self, snap):
        """
        Quét snapshot XML hiện tại để lấy UID số trực tiếp hoặc đường link trang cá nhân Facebook:
        - Quét toàn bộ thuộc tính `text` & `content-desc` trực tiếp từ `raw_xml` (BẮT ĐƯỢC CẢ NODE `bounds="[0,0][0,0]"`
          như `https://www.facebook.com/profile.php?id=615...` trên màn hình 'Cài đặt trang cá nhân' mà không cần cuộn!).
        - Hỗ trợ cả link bị xuống dòng hoặc tách ra 2 node liền kề (`profile.php?id=\n615...`).
        """
        if not snap:
            return "", ""
        raw_blobs = []
        raw_xml = snap.get('raw_xml') or ''
        if raw_xml:
            # Ưu tiên quét toàn bộ raw_xml trước (bao gồm mọi node ẩn/bounds="[0,0][0,0]")
            for m in re.findall(r'(?:text|content-desc)="([^"]+)"', raw_xml):
                val_u = html.unescape(m).strip()
                if val_u:
                    raw_blobs.append(val_u)
        raw_blobs.extend(snap.get('all_texts_low') or [])

        # Gộp thêm các cặp text node đứng sát nhau (chống trường hợp Facebook tách "profile.php?id=" và "615..." thành 2 dòng/2 node!)
        node_texts = []
        for n in (snap.get('nodes') or []):
            t_n = (n.get('text') or n.get('desc') or '').strip()
            if t_n:
                node_texts.append(t_n)
        for idx in range(len(node_texts) - 1):
            t1, t2 = node_texts[idx], node_texts[idx + 1]
            if ('facebook.com' in t1.lower() or 'profile.php' in t1.lower() or 'fb.com' in t1.lower()):
                raw_blobs.append(t1.rstrip() + t2.lstrip())

        # Ưu tiên 1: Có sẵn profile.php?id=... hoặc fb://profile/... ngay trên màn hình (kể cả khi ngắt dòng)
        for blob in raw_blobs:
            uid_direct = self._tach_uid_tu_chuoi_url(blob)
            if uid_direct:
                return uid_direct, re.sub(r'\s+', '', str(blob))

        # Ưu tiên 2: Link trang cá nhân (share/... hoặc username — ghép lại nếu có xuống dòng giữa chừng)
        for blob in raw_blobs:
            blob_norm = re.sub(r'[\r\n]+', '', str(blob)).strip()
            m_url = re.search(r'(?:https?://)?(?:www\.|m\.|mbasic\.)?facebook\.com/[^\s"<>]+', blob_norm, re.IGNORECASE)
            if m_url:
                cand = m_url.group(0).rstrip('.,;)')
                low_c = cand.lower()
                if any(bad in low_c for bad in ('/help', '/policies', '/privacy', '/terms', '/settings', '/login', '/legal', '/business')):
                    continue
                if low_c.endswith(('profile.php?id=', 'profile.php?', 'facebook.com/', 'facebook.com')):
                    continue
                return "", cand
        return "", ""

    def _lay_uid_nhanh_tu_dumpsys(self):
        """Kiểm tra nhanh dumpsys activity xem Facebook có đang giữ sẵn URI `fb://profile/<uid>` hay không (~0.2s, 0 click)."""
        try:
            out = chay_lenh_adb_lay_ket_qua('shell "dumpsys activity activities | grep -i profile"', self.serial, timeout=4)
            if out:
                uid_d = self._tach_uid_tu_chuoi_url(out)
                if uid_d:
                    return uid_d
        except Exception:
            pass
        return ""

    def _la_man_hinh_cai_dat_trang_ca_nhan(self, snap):
        """
        Xác nhận CHÍNH XÁC đang ở BÊN TRONG trang 'Cài đặt trang cá nhân' (không nhầm với Trang cá nhân có nút 3 chấm mang desc 'Cài đặt trang cá nhân'!).
        """
        if not snap or snap.get('is_blank_or_loading'):
            return False
        # Nếu vẫn thấy các nút đặc trưng của Trang cá nhân chính -> CHẮC CHẮN chưa vào 'Cài đặt trang cá nhân'!
        if self._snap_has(snap, [
            'thêm vào tin', 'add to story',
            'chỉnh sửa trang cá nhân', 'edit profile',
            'cập nhật trang cá nhân', 'update profile',
            'khai thác facebook hiệu quả hơn'
        ]):
            return False

        dau_hieu_menu_cai_dat_pf = [
            'liên kết đến trang cá nhân của bạn', 'your profile link',
            'sao chép liên kết', 'sao chép đường dẫn', 'copy link',
            'chia sẻ trang cá nhân', 'share profile',
            'cài đặt theo dõi', 'follow settings',
            'thêm tin nổi bật', 'trạng thái trang cá nhân', 'profile status',
            'kho lưu trữ', 'chế độ xem', 'view as',
            'khóa bảo vệ trang cá nhân', 'lock profile',
            'nhật ký hoạt động', 'activity log',
            'quản lý bài viết', 'xem lại bài viết và thẻ',
            'bật chế độ chuyên nghiệp', 'turn on professional mode'
        ]
        if self._snap_has(snap, dau_hieu_menu_cai_dat_pf):
            return True

        # Tiêu đề 'Cài đặt trang cá nhân' nằm chính giữa thanh đầu trang (KHÔNG phải góc phải của nút 3 chấm!)
        w, h = snap['w'], snap['h']
        for n in snap['nodes']:
            if int(h * 0.03) <= n['cy'] <= int(h * 0.16) and int(w * 0.15) <= n['cx'] <= int(w * 0.85):
                if n['text_low'] in ('cài đặt trang cá nhân', 'profile settings'):
                    return True
        return False

    def _la_trang_chinh_sua_hoac_hoi_thong_tin_fb(self, snap):
        """
        Phát hiện màn hình con bị bấm nhầm khi đang ở Trang cá nhân (VD: màn 'Chỉnh sửa trang cá nhân',
        wizard 'Cập nhật trang cá nhân' hỏi tiểu sử/quê quán/trường học/nơi ở, màn Tìm kiếm, bảng chọn ảnh bìa...).
        """
        if not snap or snap.get('is_blank_or_loading'):
            return False
        # Nếu vẫn thấy nút 'Thêm vào tin' / 'Add to story' thì đang ở đúng Trang cá nhân chính, không phải màn con!
        if self._snap_has(snap, ['thêm vào tin', 'add to story']):
            return False

        w, h = snap['w'], snap['h']
        for n in snap['nodes']:
            if int(h * 0.03) <= n['cy'] <= int(h * 0.16) and int(w * 0.10) <= n['cx'] <= int(w * 0.90):
                tl = n['text_low']
                if any(k in tl for k in [
                    'chỉnh sửa trang cá nhân', 'edit profile',
                    'cập nhật trang cá nhân', 'update profile',
                    'chỉnh sửa chi tiết', 'edit details',
                    'tìm kiếm', 'search', 'chọn ảnh bìa', 'chọn ảnh đại diện'
                ]):
                    return True

        dau_hieu_wizard_hoi = [
            'thêm tiểu sử', 'tỉnh/thành phố hiện tại', 'quê quán', 'nơi làm việc',
            'trường trung học', 'trường đại học', 'tình trạng mối quan hệ',
            'tùy chỉnh phần giới thiệu', 'bạn đến từ đâu', 'bạn sống ở đâu',
            'bạn học ở đâu', 'add bio', 'current city', 'hometown', 'workplace',
            'high school', 'relationship status', 'customize your intro'
        ]
        if self._snap_has(snap, dau_hieu_wizard_hoi):
            return True
        return False

    def _la_trang_ca_nhan_fb(self, snap):
        """Nhận diện đang đứng tại Trang cá nhân chính (loại trừ 'Cài đặt trang cá nhân' VÀ loại trừ màn 'Chỉnh sửa / Cập nhật trang cá nhân' hỏi thông tin!)."""
        if not snap or snap.get('is_blank_or_loading'):
            return False
        if self._la_man_hinh_cai_dat_trang_ca_nhan(snap):
            return False
        if self._la_trang_chinh_sua_hoac_hoi_thong_tin_fb(snap):
            return False
        if self._snap_has(snap, ['thêm vào tin', 'add to story', 'chỉnh sửa chi tiết công khai', 'edit public details']):
            return True
        # Chỉ nhận 'Chỉnh sửa trang cá nhân' nếu nó là NÚT nằm ở thân trang (y >= 0.25*h), không phải tiêu đề trên cùng!
        if self._snap_find(snap, ['Chỉnh sửa trang cá nhân', 'Edit profile'], exact=False, min_y=0.25, max_y=0.82) is not None:
            return True
        return False

    def _tim_ds_ung_vien_3_cham_trang_ca_nhan(self, snap, da_thu_diem=None):
        """
        Trả về danh sách ứng viên nút tròn 3 chấm (...) trên Trang cá nhân theo thứ tự ưu tiên CHẶT CHẼ:
        - Loại bỏ hoàn toàn: Cây bút [✏️] (Chỉnh sửa), Kính lúp [🔍] (Tìm kiếm), Cập nhật trang cá nhân,
          Camera ảnh bìa, nút [v] đổi trang cá nhân, thanh Tab Facebook trên cùng, nút 'Thêm vào tin'.
        - Hỗ trợ cả giao diện mới (góc trên-phải thanh ảnh bìa sát bên phải Kính lúp/Cây bút) lẫn giao diện cũ.
        - Trả về list[(mo_ta, cx, cy)] đã khử trùng tọa độ & loại bỏ các điểm đã bấm nhầm trước đó.
        """
        if not snap or not snap.get('nodes'):
            return []
        w, h = snap['w'], snap['h']
        tried = list(da_thu_diem or [])

        # Xác định ranh giới ĐÁY của thanh Tab Facebook trên cùng (nếu mở trong FbMainTabActivity có 5 tab)
        # Khi mở từ `fb://profile` bằng ImmersiveActivity (KHÔNG có thanh 5 tab), thanh nút `[<] ... [✏️] [🔍] [•••]`
        # nằm NGAY dưới thanh trạng thái (~0.063h / ~150px trên 1080x2400)!
        tab_nodes = []
        for n in snap['nodes']:
            if int(h * 0.02) <= n['cy'] <= int(h * 0.13):
                comb = f"{n['text_low']} {n['desc_low']}"
                if any(k in comb for k in [
                    'bảng feed', 'bảng tin', 'trang chủ', 'home',
                    'thông báo', 'notification', 'bạn bè', 'friends',
                    'reels', 'video', 'trang cá nhân', 'profile', 'tab '
                ]):
                    tab_nodes.append(n)
        co_thanh_tab_tren = (len(tab_nodes) >= 2)
        if co_thanh_tab_tren:
            tab_bottom = max(int(h * 0.06), min(int(h * 0.135), max(n['b'] for n in tab_nodes)))
            header_min_y = max(int(h * 0.082), tab_bottom + 2)
            header_max_y = min(int(h * 0.22), tab_bottom + int(h * 0.115))
        else:
            status_bottom = int(h * 0.038)
            for n in snap['nodes']:
                if n.get('rid') == 'android:id/statusBarBackground' and n['b'] > 0:
                    status_bottom = max(status_bottom, n['b'])
                    break
            tab_bottom = status_bottom
            header_min_y = max(int(h * 0.038), status_bottom + 2)
            header_max_y = int(h * 0.19)

        tu_cam_tuyet_doi = [
            'chỉnh sửa', 'edit', 'cập nhật', 'update', 'tìm kiếm', 'search',
            'máy ảnh', 'camera', 'ảnh bìa', 'cover', 'ảnh đại diện', 'avatar',
            'thêm vào tin', 'add to story', 'khai thác facebook',
            'bảng feed', 'bảng tin', 'trang chủ', 'home', 'thông báo', 'notification',
            'bạn bè', 'friends', 'reels', 'video', 'marketplace',
            'quay lại', 'back', 'đóng', 'close', 'hủy', 'cancel',
            'chuyển trang cá nhân', 'switch profile',
            'tạo trang cá nhân', 'create profile', 'tin nhắn', 'messenger'
        ]
        nhan_3_cham_chuan = [
            'cài đặt trang cá nhân', 'mở cài đặt trang cá nhân', 'profile settings',
            'tùy chọn trang cá nhân', 'xem thêm tùy chọn', 'tùy chọn khác',
            'more options', 'see more options', '...', '•••', '⋯'
        ]

        def _la_nhan_3_cham_ro_rang(comb):
            return any(k in comb for k in nhan_3_cham_chuan)

        def _bi_cam(n):
            comb = f"{n['text_low']} {n['desc_low']}".strip()
            if not comb:
                return False
            if _la_nhan_3_cham_ro_rang(comb):
                return False
            if 'menu' in comb:
                return True
            return any(bad in comb for bad in tu_cam_tuyet_doi)

        # Nhận diện tọa độ icon Kính lúp [🔍], Cây bút [✏️] và nút góc trên-trái ([≡] Menu hoặc [<] Quay lại)
        search_icon = None
        pencil_icon = None
        left_header_icon = None
        for n in snap['nodes']:
            if not (header_min_y <= n['cy'] <= header_max_y):
                continue
            if n['bw'] > int(w * 0.22) or n['bh'] > int(h * 0.11):
                continue
            comb = f"{n['text_low']} {n['desc_low']}".strip()
            if n['cx'] >= int(w * 0.55):
                if any(k in comb for k in ['tìm kiếm', 'search']):
                    if search_icon is None or n['cx'] > search_icon['cx']:
                        search_icon = n
                elif any(k in comb for k in ['chỉnh sửa', 'edit']) and not _la_nhan_3_cham_ro_rang(comb):
                    if pencil_icon is None or n['cx'] > pencil_icon['cx']:
                        pencil_icon = n
            elif n['cx'] <= int(w * 0.22):
                if any(k in comb for k in ['quay lại', 'back', 'menu']) or n['clickable']:
                    if left_header_icon is None or n['cx'] < left_header_icon['cx']:
                        left_header_icon = n

        def _trung_nut_cam_header(cx, cy):
            for bad_n in (search_icon, pencil_icon, left_header_icon):
                if bad_n is not None and abs(cx - bad_n['cx']) <= int(w * 0.045) and abs(cy - bad_n['cy']) <= int(h * 0.035):
                    return True
            return False

        ket_qua = []

        def them_uv(mo_ta, cx, cy):
            cx, cy = int(cx), int(cy)
            if not (int(w * 0.05) <= cx <= int(w * 0.98) and int(h * 0.038) <= cy <= int(h * 0.88)):
                return
            if _trung_nut_cam_header(cx, cy):
                return
            for tx, ty in tried:
                if abs(cx - tx) <= 35 and abs(cy - ty) <= 35:
                    return
            for _, ex, ey in ket_qua:
                if abs(cx - ex) <= 32 and abs(cy - ey) <= 32:
                    return
            ket_qua.append((mo_ta, cx, cy))

        # ===== ƯU TIÊN 1: Node XML mang đúng nhãn 3 chấm / Cài đặt trang cá nhân TRÊN DẢI ẢNH BÌA TRƯỚC (chống bám nhầm nút ở thân trang!) =====
        p1_header_nodes = []
        p1_body_nodes = []
        for n in snap['nodes']:
            if not (header_min_y - 10 <= n['cy'] <= int(h * 0.80)):
                continue
            if n['bw'] > int(w * 0.26) or n['bh'] > int(h * 0.12):
                continue
            tl, dl = n['text_low'], n['desc_low']
            comb = f"{tl} {dl}".strip()
            if not comb or _bi_cam(n):
                continue
            in_header = (header_min_y - 10 <= n['cy'] <= header_max_y)
            if _la_nhan_3_cham_ro_rang(comb):
                on_right = 1 if n['cx'] >= int(w * 0.78) else 0
                if in_header:
                    p1_header_nodes.append((on_right, n['cx'], -n['cy'], n))
                else:
                    p1_body_nodes.append((on_right, n['cx'], -n['cy'], n))
            elif (tl in ('xem thêm', 'more') or dl in ('xem thêm', 'more')) and n['cx'] >= int(w * 0.78) and in_header:
                p1_header_nodes.append((1, n['cx'], -n['cy'], n))
        p1_header_nodes.sort(key=lambda it: (it[0], it[1], it[2]), reverse=True)
        for _, _, _, n in p1_header_nodes:
            lbl = (n['text'] or n['desc'] or '3 chấm').strip()
            them_uv(f'nhãn XML góc trên "{lbl}"', n['cx'], n['cy'])

        # ===== ƯU TIÊN 2 (Giao diện mới như ảnh): Thanh icon trên ảnh bìa [≡] ... [✏️] [🔍] [•••] =====
        # 2A. Nếu tìm thấy icon Kính lúp [🔍] -> nút 3 chấm nằm SÁT BÊN PHẢI cùng hàng ngang!
        if search_icon is not None:
            right_of_search = [
                n for n in snap['nodes']
                if abs(n['cy'] - search_icon['cy']) <= int(h * 0.04)
                and n['cx'] > search_icon['cx'] + int(w * 0.04)
                and n['cx'] >= int(w * 0.83)
                and n['bw'] <= int(w * 0.18)
                and n['bh'] <= int(h * 0.10)
                and not _bi_cam(n)
            ]
            right_of_search.sort(key=lambda n: (int(n['clickable']), n['cx']), reverse=True)
            for n in right_of_search:
                them_uv('icon phải Kính lúp (XML)', n['cx'], n['cy'])

            # Suy ra tọa độ hình học chuẩn từ khoảng cách [✏️] -> [🔍] -> [•••] phòng trường hợp XML ẩn hẳn node 3 chấm
            if pencil_icon is not None and search_icon['cx'] > pencil_icon['cx'] + 15:
                step_x = search_icon['cx'] - pencil_icon['cx']
                est_x = min(int(w * 0.94), search_icon['cx'] + step_x)
                them_uv('đối xứng bên phải [✏️][🔍]', est_x, search_icon['cy'])
            elif int(w * 0.72) <= search_icon['cx'] <= int(w * 0.87):
                est_x = min(int(w * 0.94), search_icon['cx'] + int(w * 0.095))
                them_uv('bên phải Kính lúp [🔍]', est_x, search_icon['cy'])

        # 2B. Node icon nhỏ nằm ngoài cùng bên phải dải ảnh bìa (cx >= 0.84w, header_min_y <= cy <= header_max_y, KHÔNG thuộc danh sách cấm!)
        top_right_icons = [
            n for n in snap['nodes']
            if (n['clickable'] or 'Button' in n['cls'] or 'Image' in n['cls'])
            and header_min_y <= n['cy'] <= header_max_y
            and n['cx'] >= int(w * 0.84)
            and n['bw'] <= int(w * 0.18)
            and n['bh'] <= int(h * 0.10)
            and not _bi_cam(n)
        ]
        top_right_icons.sort(key=lambda n: (int(n['clickable']), n['cx'], -n['cy']), reverse=True)
        for n in top_right_icons:
            them_uv('icon góc trên-phải ảnh bìa', n['cx'], n['cy'])

        # 2C. Nếu thấy icon góc trên-trái ([≡] Menu hoặc [<] Quay lại) -> nút 3 chấm nằm đối xứng cùng hàng ở góc trên-phải (~91%w)
        if left_header_icon is not None:
            them_uv('đối xứng cùng hàng nút góc trên-trái', int(w * 0.91), left_header_icon['cy'])

        # ===== ƯU TIÊN 3 (Giao diện cũ): Nút 3 chấm nằm NGAY BÊN PHẢI nút 'Chỉnh sửa trang cá nhân' (TUYỆT ĐỐI không neo theo 'Thêm vào tin'!) =====
        edit_btn = self._snap_find(
            snap,
            ['Chỉnh sửa trang cá nhân', 'Edit profile'],
            exact=False,
            min_y=0.22,
            max_y=0.80
        )
        if edit_btn is not None and edit_btn['r'] <= int(w * 0.85):
            row_cands = [
                n for n in snap['nodes']
                if (n['clickable'] or 'Button' in n['cls'] or 'Image' in n['cls'])
                and abs(n['cy'] - edit_btn['cy']) <= int(h * 0.05)
                and n['cx'] > edit_btn['r'] + 5
                and n['cx'] >= int(w * 0.82)
                and n['bw'] <= int(w * 0.20)
                and not _bi_cam(n)
            ]
            row_cands.sort(key=lambda n: n['cx'], reverse=True)
            for n in row_cands:
                them_uv('bên phải nút Chỉnh sửa trang cá nhân', n['cx'], n['cy'])

        # Bổ sung nhãn XML 3 chấm nằm ở thân trang (giao diện cũ) sau khi đã ưu tiên hết dải ảnh bìa trên-phải
        p1_body_nodes.sort(key=lambda it: (it[0], it[1], it[2]), reverse=True)
        for _, _, _, n in p1_body_nodes:
            lbl = (n['text'] or n['desc'] or '3 chấm').strip()
            them_uv(f'nhãn XML thân trang "{lbl}"', n['cx'], n['cy'])

        # ===== ƯU TIÊN 4 (Dự phòng cuối trên dải ảnh bìa khi FB ẩn hẳn node 3 chấm khỏi XML) =====
        if co_thanh_tab_tren:
            est_header_y = min(header_max_y - 4, max(header_min_y + 4, tab_bottom + int(h * 0.043)))
            them_uv('vị trí góc trên-phải ảnh bìa (có tab)', int(w * 0.91), est_header_y)
        else:
            them_uv('vị trí góc trên-phải Immersive (91%, 6.3%)', int(w * 0.91), int(h * 0.063))
            them_uv('vị trí góc trên-phải ảnh bìa (91%, 13.1%)', int(w * 0.91), int(h * 0.131))

        return ket_qua

    def _bam_sao_chep_hoac_chia_se_va_xu_ly_tiep_tuc(self, target_node, ten_nut_bam=""):
        """
        Bấm vào nút 'Sao chép liên kết / Sao chép đường dẫn' HOẶC 'Chia sẻ trang cá nhân',
        sau đó tự động xử lý:
        - Nếu hiện bảng hỏi / bảng xác nhận có nút 'Tiếp tục' / 'Continue' -> bấm 'Tiếp tục' ngay!
        - Nếu mở bảng Chia sẻ (bottom-sheet) -> tìm bấm 'Sao chép liên kết / Sao chép đường dẫn / Sao chép / Copy link'.
        - Nếu sau khi bấm Sao chép lại hiện bảng 'Tiếp tục' -> bấm 'Tiếp tục' lần nữa rồi mới đọc Clipboard!
        Trả về (uid_truc_tiep, link_fb_doc_duoc).
        """
        self._xoa_clipboard_truoc_khi_copy()
        self.log(f'📋 [Lấy UID] Bấm "{ten_nut_bam}" ({target_node["cx"]}, {target_node["cy"]})...')
        self.click_toa_do_an_toan(target_node['cx'], target_node['cy'])
        time.sleep(1.0)

        ds_tiep_tuc = ['Tiếp tục', 'Continue', 'OK', 'Đồng ý', 'Xác nhận']
        ds_copy_sheet = [
            'Sao chép liên kết', 'Sao chép đường dẫn', 'Sao chép URL',
            'Sao chép liên kết trang cá nhân', 'Sao chép',
            'Copy link', 'Copy profile link', 'Copy URL', 'Copy'
        ]

        link_tu_xml = ""
        da_bam_copy_trong_sheet = False
        so_lan_bam_tiep_tuc = 0

        for _ in range(4):
            if STOP_EVENT.is_set():
                break
            snap_pop = self.cho_man_hinh_san_sang(timeout=6.0, ngu_canh='Chờ bảng Tiếp tục / Sao chép link', check_die=False)

            # Kiểm tra xem link / UID đã vào Clipboard ngay chưa
            clip_fast = self._doc_clipboard_nhanh()
            if clip_fast:
                uid_c = self._tach_uid_tu_chuoi_url(clip_fast)
                return uid_c, clip_fast

            # Kiểm tra XML xem có sẵn UID số đầy đủ không
            uid_x, lnk_x = self._trich_xuat_link_hoac_uid_tu_snap(snap_pop)
            if uid_x:
                return uid_x, lnk_x
            if lnk_x and ('...' not in lnk_x) and ('…' not in lnk_x):
                link_tu_xml = self._chuan_hoa_link_fb(lnk_x) or lnk_x

            # 1. Nếu hiện bảng yêu cầu bấm "Tiếp tục" / "Continue" thì mới cho copy -> Bấm ngay!
            btn_continue = (
                self._snap_find(snap_pop, ['Tiếp tục', 'Continue'], exact=True, click_duoi=True, min_y=0.35)
                or self._snap_find(snap_pop, ['Tiếp tục', 'Continue'], exact=True, click_duoi=True)
            )
            if btn_continue is not None and so_lan_bam_tiep_tuc < 2:
                so_lan_bam_tiep_tuc += 1
                self.log(f'⏩ [Lấy UID] Hiện bảng xác nhận -> Bấm "{btn_continue["text"] or btn_continue["desc"]}" để hoàn tất sao chép...')
                prev_c = snap_pop['sig']
                self.click_toa_do_an_toan(btn_continue['cx'], btn_continue['cy'])
                self._cho_chuyen_man_hinh(prev_c, timeout=3.5)
                time.sleep(0.9)
                continue

            # 2. Nếu mở ra bảng Chia sẻ (bottom-sheet) có nút "Sao chép liên kết / Sao chép đường dẫn / Copy link" -> Bấm ngay!
            if not da_bam_copy_trong_sheet:
                btn_copy_sh = (
                    self._snap_find(snap_pop, ds_copy_sheet, exact=True, click_duoi=True, min_y=0.25)
                    or self._snap_find(snap_pop, ['Sao chép liên kết', 'Sao chép đường dẫn', 'Copy link', 'Copy URL'], exact=False, click_duoi=True, min_y=0.25)
                )
                # Tránh bấm lại chính nút cũ trên cùng trang Cài đặt trang cá nhân nếu không có bảng chia sẻ mới
                la_nut_copy_moi = (
                    btn_copy_sh is not None
                    and (
                        abs(btn_copy_sh['cx'] - target_node['cx']) > 25
                        or abs(btn_copy_sh['cy'] - target_node['cy']) > 25
                    )
                )
                if la_nut_copy_moi:
                    da_bam_copy_trong_sheet = True
                    nhan_cp = (btn_copy_sh['text'] or btn_copy_sh['desc'] or 'Sao chép liên kết').strip()
                    self.log(f'📋 [Lấy UID - Bảng chia sẻ] Bấm "{nhan_cp}"...')
                    prev_sh = snap_pop['sig']
                    self.click_toa_do_an_toan(btn_copy_sh['cx'], btn_copy_sh['cy'])
                    self._cho_chuyen_man_hinh(prev_sh, timeout=3.0)
                    time.sleep(0.9)
                    continue

            break

        # Sau khi đã bấm Sao chép & Tiếp tục xong -> Đọc Clipboard (bao gồm vượt chặn Android 10-15 qua fb://search)
        clip_final = self._doc_clipboard_vong_qua_android10()
        if clip_final:
            return self._tach_uid_tu_chuoi_url(clip_final), clip_final
        return "", link_tu_xml

    def lay_uid_fb(self, req_proxy=None, ten_fb=""):
        """
        Lấy UID hoặc Link FB đầy đủ KHÔNG CẦN ROOT (chạy ngay sau bước 2FA và trước lúc lưu file / đăng xuất):
        - Đã bỏ các DeepLink không tồn tại trong APK Facebook (`fb://profile_settings`, `fb://profile_more`, `fb://profile/settings`).
        - Mở thẳng Trang cá nhân (`fb://profile`) -> bấm đúng nút 3 chấm (`•••`) vào `Cài đặt trang cá nhân`
          (hỗ trợ cả `ImmersiveActivity` không thanh tab lẫn `FbMainTabActivity` có thanh 5 tab).
        - Vừa vào `Cài đặt trang cá nhân`: đọc thẳng `https://www.facebook.com/profile.php?id=615...` từ `raw_xml`
          ngay cả khi node đang ở `bounds="[0,0][0,0]"` -> lấy UID số tức thì trong ~0.2s (0 cuộn, 0 Copy, 0 API)!
        - Nếu máy nào không hiển thị sẵn `profile.php?id=...` trong XML -> tự dự phòng cuộn / Copy / Chia sẻ / API chuyển link.
        """
        self.log('🆔 [Không Root] Đang mở Trang cá nhân (fb://profile) -> bấm 3 chấm (...) đọc thẳng UID từ raw_xml...')
        uf = self._u_flag()
        px_use = req_proxy if req_proxy is not None else self.req_proxy

        uid_quick = self._lay_uid_nhanh_tu_dumpsys()
        if uid_quick:
            self.log(f'✅ ĐÃ LẤY ĐƯỢC UID NHANH (từ dumpsys): {uid_quick}')
            return uid_quick

        # Chỉ chạy DeepLink tùy chỉnh vào 'Cài đặt trang cá nhân' nếu người dùng tự cấu hình trong config_reg_fb.json
        custom_uri = ""
        try:
            custom_uri = str((self.config or {}).get('deeplink_cai_dat_trang_ca_nhan') or '').strip()
        except Exception:
            custom_uri = ""

        da_vao_thang_custom = False
        if custom_uri:
            self.log(f'⚡ [Lấy UID] Gọi DeepLink tùy chỉnh: {custom_uri}...')
            self.chay_shell_nhanh(f'am start {uf}-a android.intent.action.VIEW -d "{custom_uri}" com.facebook.katana')
            time.sleep(1.5)
            snap_cus = self.cho_man_hinh_san_sang(timeout=6.0, ngu_canh='Mở DeepLink Cài đặt trang cá nhân', check_die=False)
            uid_cus, _ = self._trich_xuat_link_hoac_uid_tu_snap(snap_cus)
            if uid_cus:
                self.log(f'✅ ĐÃ LẤY ĐƯỢC UID (từ DeepLink tùy chỉnh): {uid_cus}')
                return uid_cus
            if self._la_man_hinh_cai_dat_trang_ca_nhan(snap_cus):
                da_vao_thang_custom = True

        if not da_vao_thang_custom:
            self.chay_shell_nhanh(f'am start {uf}-a android.intent.action.VIEW -d "fb://profile" com.facebook.katana')
            time.sleep(1.6)
            uid_quick2 = self._lay_uid_nhanh_tu_dumpsys()
            if uid_quick2:
                self.log(f'✅ ĐÃ LẤY ĐƯỢC UID NHANH (từ dumpsys): {uid_quick2}')
                return uid_quick2

        han_chot_uid = time.time() + 55.0
        da_mo_cai_dat_profile = False
        da_thu_vao_qua_menu = False
        so_lan_cuon = 0
        so_lan_bam_copy = 0
        so_lan_bam_chia_se = 0
        so_lan_bam_3_cham = 0
        da_thu_diem_3_cham = []
        link_da_thu = set()
        link_cuoi_doc_duoc = ""

        while time.time() < han_chot_uid and not STOP_EVENT.is_set():
            try:
                snap = self.cho_man_hinh_san_sang(timeout=12.0, ngu_canh='Lấy UID trang cá nhân')
                if snap.get('is_blank_or_loading'):
                    time.sleep(0.5)
                    continue

                if self.quet_va_xoa_man_hinh_chan(so_vong_quet=2, snap=snap):
                    continue

                # 1. Quét xem UID số hoặc Link FB đầy đủ đã xuất hiện ngay trên XML chưa
                uid_xml, link_xml = self._trich_xuat_link_hoac_uid_tu_snap(snap)
                if uid_xml:
                    self.log(f'✅ ĐÃ LẤY ĐƯỢC UID (từ XML): {uid_xml}')
                    return uid_xml

                if link_xml and ('...' not in link_xml) and ('…' not in link_xml):
                    link_norm = self._chuan_hoa_link_fb(link_xml) or link_xml
                    if link_norm not in link_da_thu:
                        link_da_thu.add(link_norm)
                        link_cuoi_doc_duoc = link_norm
                        self.log(f'🔗 [Lấy UID] Đọc thấy link trên màn hình: {link_norm} -> Đang giải mã UID...')
                        uid_res = self._giai_ma_uid_tu_link_fb(link_norm, proxies=px_use)
                        if uid_res:
                            self.log(f'✅ ĐÃ LẤY ĐƯỢC UID (từ link XML): {uid_res}')
                            return uid_res

                # 2. Đang ở đúng BÊN TRONG trang 'Cài đặt trang cá nhân' (loại trừ nhầm Trang cá nhân có nút 3 chấm mang desc 'Cài đặt trang cá nhân'!)
                la_cai_dat_profile = self._la_man_hinh_cai_dat_trang_ca_nhan(snap)
                if la_cai_dat_profile:
                    da_mo_cai_dat_profile = True

                    # 2A. Ưu tiên nút 'Sao chép liên kết / Sao chép đường dẫn / Copy link' nếu đã hiển thị
                    btn_copy = self._snap_find(
                        snap,
                        ['Sao chép liên kết', 'Sao chép đường dẫn', 'Copy link', 'Copy URL', 'Sao chép liên kết trang cá nhân'],
                        exact=False,
                        click_duoi=True
                    )
                    if btn_copy is not None and so_lan_bam_copy < 2:
                        so_lan_bam_copy += 1
                        nhan_cp = (btn_copy['text'] or btn_copy['desc'] or 'Sao chép liên kết').strip()
                        uid_got, link_got = self._bam_sao_chep_hoac_chia_se_va_xu_ly_tiep_tuc(btn_copy, ten_nut_bam=nhan_cp)
                        if uid_got:
                            self.log(f'✅ ĐÃ LẤY ĐƯỢC UID (từ {nhan_cp}): {uid_got}')
                            return uid_got
                        if link_got:
                            link_norm = self._chuan_hoa_link_fb(link_got) or link_got
                            link_cuoi_doc_duoc = link_norm
                            self.log(f'🔗 [Lấy UID] Link đã copy: {link_norm} -> Đang chuyển sang UID số...')
                            uid_clip = self._giai_ma_uid_tu_link_fb(link_norm, proxies=px_use)
                            if uid_clip:
                                self.log(f'✅ ĐÃ LẤY ĐƯỢC UID (từ link đã copy): {uid_clip}')
                                return uid_clip
                            # Đã copy được link FB thật nhưng không chuyển được sang UID số -> thoát vòng để trả về & in CẢ LINK FB!
                            break
                        else:
                            self.log('⚠️ [Lấy UID] Chưa đọc được Clipboard sau khi bấm Sao chép -> Thử kiểm tra tiếp...')
                        continue

                    # 2B. Cuộn xuống đáy để lộ nút 'Sao chép liên kết / Sao chép đường dẫn' (tự dừng cuộn sớm nếu đã chạm đáy màn hình!)
                    if so_lan_cuon < 3:
                        so_lan_cuon += 1
                        w, h = snap['w'], snap['h']
                        prev_sc_sig = snap['sig']
                        self.log(f'📜 [Cài đặt trang cá nhân] Cuộn xuống tìm "Sao chép liên kết / Chia sẻ" (lần {so_lan_cuon}/3)...')
                        self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.78), int(w * 0.50), int(h * 0.24), 260)
                        time.sleep(0.85)
                        snap_after_sc = self.quet_snapshot()
                        uid_after_sc, _ = self._trich_xuat_link_hoac_uid_tu_snap(snap_after_sc)
                        if uid_after_sc:
                            self.log(f'✅ ĐÃ ĐỌC THẲNG UID TỪ XML SAU KHI CUỘN: {uid_after_sc}')
                            return uid_after_sc
                        if snap_after_sc['sig'] != prev_sc_sig:
                            continue
                        # Đã chạm đáy danh sách mà vẫn không có nút Sao chép liên kết -> chuyển ngay sang bấm "Chia sẻ trang cá nhân" ở 2C!
                        so_lan_cuon = 3

                    # 2C. Đã cuộn xuống đáy nhưng máy KHÔNG hiện mục 'Liên kết đến trang cá nhân / Sao chép liên kết' -> tìm bấm 'Chia sẻ trang cá nhân' / 'Chia sẻ'!
                    btn_share = self._snap_find(
                        snap,
                        ['Chia sẻ trang cá nhân', 'Share profile', 'Chia sẻ', 'Share'],
                        exact=False,
                        click_duoi=True,
                        min_y=0.10,
                        max_y=0.92
                    )
                    if btn_share is not None and so_lan_bam_chia_se < 2:
                        so_lan_bam_chia_se += 1
                        nhan_sh = (btn_share['text'] or btn_share['desc'] or 'Chia sẻ trang cá nhân').strip()
                        uid_sh, link_sh = self._bam_sao_chep_hoac_chia_se_va_xu_ly_tiep_tuc(btn_share, ten_nut_bam=nhan_sh)
                        if uid_sh:
                            self.log(f'✅ ĐÃ LẤY ĐƯỢC UID (từ {nhan_sh}): {uid_sh}')
                            return uid_sh
                        if link_sh:
                            link_norm = self._chuan_hoa_link_fb(link_sh) or link_sh
                            link_cuoi_doc_duoc = link_norm
                            self.log(f'🔗 [Lấy UID - Chia sẻ] Link đã copy: {link_norm} -> Đang chuyển sang UID số...')
                            uid_clip = self._giai_ma_uid_tu_link_fb(link_norm, proxies=px_use)
                            if uid_clip:
                                self.log(f'✅ ĐÃ LẤY ĐƯỢC UID (từ Chia sẻ trang cá nhân): {uid_clip}')
                                return uid_clip
                            break
                        continue
                    break

                # 3. Đang ở trang Menu (`fb://bookmarks`) -> bấm vào 'Xem trang cá nhân của bạn' hoặc tên FB
                if self._la_man_hinh_menu_fb(snap):
                    self.log(f'👤 [Lấy UID] Đang ở Menu -> Bấm mở Trang cá nhân ({ten_fb or "Xem trang cá nhân"})...')
                    prev_m = snap['sig']
                    da_click_pf = (
                        (ten_fb and self._snap_click(snap, [ten_fb], exact=False, min_y=0.08, max_y=0.45))
                        or self._snap_click(snap, ['Xem trang cá nhân của bạn', 'See your profile'], exact=False, min_y=0.08, max_y=0.45)
                    )
                    if da_click_pf:
                        self._cho_chuyen_man_hinh(prev_m, timeout=4.5)
                        continue

                # 4. Đang ở Trang cá nhân -> tìm & bấm ĐÚNG nút 3 chấm (...) góc trên-phải + KIỂM TRA SAU KHI BẤM (mở nhầm trang khác -> Back ngay!)
                if not da_mo_cai_dat_profile and so_lan_bam_3_cham < 5:
                    ds_uv_3_cham = self._tim_ds_ung_vien_3_cham_trang_ca_nhan(snap, da_thu_diem=da_thu_diem_3_cham) if self._la_trang_ca_nhan_fb(snap) else []
                    if ds_uv_3_cham:
                        mo_ta_3c, tx_3c, ty_3c = ds_uv_3_cham[0]
                        so_lan_bam_3_cham += 1
                        da_thu_diem_3_cham.append((tx_3c, ty_3c))
                        prev_p_sig = snap['sig']
                        self.log(f'⋮ [Lấy UID - Thử {so_lan_bam_3_cham}/5] Bấm 3 chấm (...) theo {mo_ta_3c} tại ({tx_3c}, {ty_3c})...')
                        self.click_toa_do_an_toan(tx_3c, ty_3c)
                        self._cho_chuyen_man_hinh(prev_p_sig, timeout=4.5)

                        # Xác minh NGAY sau khi bấm: vừa vào 'Cài đặt trang cá nhân' là đọc thẳng UID số từ raw_xml (kể cả bounds="[0,0][0,0]") -> TRẢ VỀ TỨC THÌ!
                        snap_sau_3c = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Kiểm tra sau bấm 3 chấm Trang cá nhân', check_die=False)
                        uid_ngay_3c, _ = self._trich_xuat_link_hoac_uid_tu_snap(snap_sau_3c)
                        if uid_ngay_3c:
                            self.log(f'✅ ĐÃ ĐỌC THẲNG UID SỐ TỪ raw_xml "Cài đặt trang cá nhân" (0 cuộn, 0 Copy): {uid_ngay_3c}')
                            return uid_ngay_3c
                        if self._la_man_hinh_cai_dat_trang_ca_nhan(snap_sau_3c):
                            continue

                        if not self._la_trang_ca_nhan_fb(snap_sau_3c):
                            self.log(f'↩️ [Lấy UID] Điểm ({tx_3c}, {ty_3c}) mở nhầm trang khác ({self._tom_tat_man_hinh(snap_sau_3c)}) -> Bấm Back về Trang cá nhân thử điểm kế tiếp!')
                            for _ in range(2):
                                try:
                                    self.d.press('back')
                                except Exception:
                                    self.chay_shell_nhanh('input keyevent 4')
                                time.sleep(1.0)
                                s_bk = self.quet_snapshot()
                                # Nếu hiện bảng hỏi 'Bỏ thay đổi?' -> bấm Bỏ / Hủy bỏ để thoát hẳn
                                if self._snap_has(s_bk, ['bỏ thay đổi', 'hủy thay đổi', 'discard changes', 'thoát không lưu']):
                                    self._snap_click(s_bk, ['Bỏ', 'Hủy bỏ', 'Thoát', 'Discard', 'Leave'], exact=True, click_duoi=True)
                                    time.sleep(0.9)
                                    s_bk = self.quet_snapshot()
                                if self._la_trang_ca_nhan_fb(s_bk) or self._la_man_hinh_cai_dat_trang_ca_nhan(s_bk):
                                    break
                        continue

                    # Nếu `fb://profile` chưa mở đúng trang cá nhân -> mở qua Menu `fb://bookmarks` để bấm vào tên FB!
                    if not da_thu_vao_qua_menu:
                        da_thu_vao_qua_menu = True
                        self.log(f'🔄 [Lấy UID] Chưa thấy nút 3 chấm Trang cá nhân ({self._tom_tat_man_hinh(snap)}) -> Mở Menu vào Trang cá nhân...')
                        self.chay_shell_nhanh(f'am start {uf}-a android.intent.action.VIEW -d "fb://bookmarks" com.facebook.katana')
                        time.sleep(1.8)
                        continue
                    break

                time.sleep(0.5)
            except (AccountDieError, KeyboardInterrupt):
                raise
            except Exception as err_uid:
                self.log(f'⚠️ [Lấy UID] Lỗi tạm thời ({str(err_uid)[:35]}) -> Đọc lại màn hình...')
                time.sleep(0.6)

        if link_cuoi_doc_duoc:
            link_final = self._chuan_hoa_link_fb(link_cuoi_doc_duoc) or link_cuoi_doc_duoc
            self.log(f'🔗 Không chuyển được sang UID số -> Giữ & in toàn bộ link FB: {link_final}')
            return link_final

        self.log('⚠️ Không trích xuất được UID hay Link FB -> Sẽ dùng Email/SĐT dự phòng khi lưu nick.')
        return ""

    def _xoa_sach_o_sdt(self, snap, o_sdt_node):
        """
        Xóa sạch số điện thoại cũ trong ô "Số di động" (0% tọa độ cố định):
        1. Quét động nút dấu X xóa nhanh nằm cùng hàng bên phải trong ô "Số di động" (nếu có) -> bấm 1 phát.
        2. Xác minh lại EditText; nếu vẫn còn chữ số cũ -> bấm vào ô EditText và xóa sạch bằng xoa_o_nhap().
        """
        w, h = snap['w'], snap['h']
        if o_sdt_node is not None:
            # 1. Tìm nút dấu X xóa nhanh nằm cùng hàng ngang bên phải ô nhập SĐT
            nut_x_o = None
            for n in snap['nodes']:
                if n is o_sdt_node or n['cls'] == 'android.widget.EditText':
                    continue
                if not (n['cx'] > o_sdt_node['cx'] and abs(n['cy'] - o_sdt_node['cy']) <= max(55, o_sdt_node['bh'])):
                    continue
                if n['bw'] > int(w * 0.25) or n['bh'] > int(h * 0.12):
                    continue
                comb = f"{n['text_low']} {n['desc_low']}".strip()
                rid_l = (n.get('rid') or '').lower()
                if (
                    any(k in comb for k in ['xóa', 'xoá', 'clear', 'delete', 'hủy', 'đóng'])
                    or comb in {'x', '×', '✕', '✖'}
                    or any(k in rid_l for k in ['clear', 'delete', 'close', 'cancel'])
                    or (n['clickable'] and n['l'] >= o_sdt_node['cx'] and n['r'] <= o_sdt_node['r'] + 40)
                ):
                    nut_x_o = n
                    break

            if nut_x_o is not None:
                self.log(f'🧹 [SĐT lỗi] Bấm nút Xóa (×) trong ô SĐT tại ({nut_x_o["cx"]}, {nut_x_o["cy"]})...')
                self.click_toa_do_an_toan(nut_x_o['cx'], nut_x_o['cy'])
                time.sleep(0.45)

        # 2. Xác minh lại ô EditText đã sạch chữ số cũ chưa; nếu vẫn còn -> xóa triệt để bằng set_text('') + DEL
        snap_after = self.quet_snapshot()
        o_moi = snap_after['edit_texts'][0] if snap_after['edit_texts'] else self._snap_find(snap_after, ['Số di động', 'Mobile number'], exact=False)
        con_so_cu = bool(o_moi and re.sub(r'\D', '', (o_moi.get('text') or '')))
        if con_so_cu:
            self.click_toa_do_an_toan(o_moi['cx'], o_moi['cy'])
            time.sleep(0.3)
            elem = None
            try:
                edits = self.d(className='android.widget.EditText')
                if edits.exists:
                    elem = edits[0]
            except Exception:
                pass
            self.xoa_o_nhap(elem)
            time.sleep(0.25)
            # Xác minh lần 2 đề phòng vẫn còn dấu '+' hoặc số
            try:
                if elem is not None and re.sub(r'\D', '', (elem.info.get('text') or '')):
                    elem.set_text('')
                    time.sleep(0.2)
            except Exception:
                pass

    def _thue_sdt_moi_khac_so_cu(self, autosms_service, ds_sdt_loi, max_thu_thue=3):
        """Hủy đơn số cũ trên AutoSMS.site và thuê 1 số mới khác hoàn toàn các số đã bị Facebook báo lỗi."""
        try:
            autosms_service.cancel_order(log_fn=self.log, ly_do='Đổi sang số mới')
        except Exception:
            pass
        time.sleep(0.6)

        for lan in range(1, max_thu_thue + 1):
            if STOP_EVENT.is_set():
                return None
            so_moi = autosms_service.buy_number(log_fn=self.log)
            if not so_moi:
                time.sleep(1.2)
                continue
            so_moi_digits = re.sub(r'\D', '', str(so_moi))
            if so_moi_digits and so_moi_digits in ds_sdt_loi:
                self.log(f'⚠️ [AutoSMS] Trả về trùng số cũ bị lỗi ({so_moi}) -> Hủy & thuê số khác ({lan}/{max_thu_thue})...')
                try:
                    autosms_service.cancel_order(log_fn=self.log, ly_do='Trùng số cũ bị lỗi')
                except Exception:
                    pass
                time.sleep(1.0)
                continue
            return so_moi
        return None

    def chay_dang_ky(self, used_email=None, mode="1", mail_service=None, imap_service=None, hotmail_service=None, autosms_service=None, used_phones=None, used_names=None, refill_email_fn=None):
        """
        Quy trình Đăng ký theo mô hình BÁM SÁT MÀN HÌNH (State Machine - ưu tiên bước cụ thể trước):
        - Quét toàn màn hình chỉ bằng 1 dump XML (~0.2s), không chạy cố định theo delay mù.
        - Màn hình đang trắng / lag / có vòng xoay tải -> Đứng đợi nhận diện, tuyệt đối KHÔNG bấm mù.
        - Đảo thứ tự kiểm tra: nhận diện các màn hình form cụ thể (OTP -> Tôi đồng ý -> Mật khẩu -> Email -> SĐT -> Giới tính -> Ngày sinh -> Họ Tên)
          TRƯỚC màn hình mở đầu (Tham gia Facebook / Đăng nhập) và bỏ hẳn từ khóa trùng 'Tìm tài khoản của tôi' ở chân mọi trang.
        """
        if self.user_id > 0:
            self.log(f'✨ Đang chạy trên User sạch CleanFB (ID {self.user_id}) -> Cấu hình thông số...')
            lam_moi_thong_so_thiet_bi_adb(self.serial, self.config, user_id=self.user_id)
            khoa_xoay_man_hinh(self.serial, user_id=self.user_id)
        else:
            if not kiem_tra_fb_tren_may_chinh(self.serial):
                raise FileNotFoundError(
                    f"Máy chính chưa cài ứng dụng Facebook ({FB_PACKAGE_NAME})! Hãy cài Facebook trên máy chính trước."
                )
            chay_lenh_adb('shell "input keyevent 224; input keyevent 82"', self.serial, timeout=6)
            self.xoa_sach_tu_dong_dien_va_khoa_truy_cap(
                cho_phep_mo_cai_dat_noi=bool(self.config.get('xoa_du_lieu_noi', True) if self.config else True)
            )
            lam_moi_thong_so_thiet_bi_adb(self.serial, self.config, user_id=0)
            khoa_xoay_man_hinh(self.serial, user_id=0)
            cap_quyen_bo_nho_fb(self.serial, user_id=0)

        if self.config and self.config.get('doi_ip_may_bay', False):
            doi_ip_che_do_may_bay_adb(self.serial, self.device_name, self.config)

        # NẠP SẴN ẢNH AVATAR TRƯỚC KHI MỞ FACEBOOK (tránh tuyệt đối việc truyền ảnh / quét MediaStore sau OTP làm out FB!)
        preloaded_avatar_paths = self.day_anh_qua_adb()

        self.log(f'🚀 Mở Facebook ({"User ảo " + str(self.user_id) if self.user_id > 0 else "Bên ngoài - User 0"})...')
        self._mo_app_fb_theo_user()
        self.cho_va_dong_lop_phu_sau_mo_fb(thoi_gian_quet=4.5)

        ho, ten = self.tao_ho_ten(used_names)
        ten_fb = f'{ho} {ten}'
        mat_khau_fb = self.config['mat_khau_fb']
        so_dt = None
        tai_khoan_lien_he = used_email
        uid_moc = 0
        da_chot_moc_mail = False
        da_nhap_ten_xong = False
        thoi_diem_bam_tiep_ten = 0.0
        da_chon_ngay_sinh_xong = False
        thoi_diem_bam_tiep_ns = 0.0
        da_chon_gioi_tinh_xong = False
        thoi_diem_bam_tiep_gt = 0.0
        da_nhap_sdt_xong = False
        thoi_diem_bam_tiep_sdt = 0.0
        so_lan_doi_sdt = 0
        ds_sdt_loi = set()
        max_lan_doi_sdt = 5
        da_nhap_email_xong = False
        thoi_diem_bam_tiep_email = 0.0
        da_nhap_mk_xong = False
        thoi_diem_bam_tiep_mk = 0.0
        da_nhap_otp = False
        so_lan_doi_lien_he_otp = 0
        max_lan_doi_lien_he_otp = int((self.config or {}).get('so_lan_doi_sdt_khi_khong_ve_otp', 5))
        imap_moi_tao_trong_ham = []
        buoc_cuoi = ''
        last_step_sig = ''
        last_step_ts = 0.0
        so_lan_phuc_hoi_man_la = 0
        thoi_diem_buoc_cuoi = time.time()
        thoi_diem_log_trang = 0.0
        thoi_diem_kiem_tra_app = time.time()
        thoi_diem_quet_lop_phu = 0.0
        han_chot_tong = time.time() + 280.0

        def _dang_cho_chuyen_buoc(ten_buoc, cur_sig, nguong_giay=6.0):
            return (
                buoc_cuoi == ten_buoc
                and last_step_sig == cur_sig
                and (time.time() - last_step_ts) < nguong_giay
            )

        def _chot_buoc(ten_buoc, cur_sig):
            nonlocal buoc_cuoi, last_step_sig, last_step_ts, thoi_diem_buoc_cuoi, so_lan_phuc_hoi_man_la
            buoc_cuoi = ten_buoc
            last_step_sig = cur_sig
            last_step_ts = time.time()
            thoi_diem_buoc_cuoi = time.time()
            so_lan_phuc_hoi_man_la = 0

        da_don_sach_luot = False
        bi_ngat_thu_cong = False

        def _don_sach_khi_that_bai(ly_do="Đăng ký thất bại"):
            nonlocal da_don_sach_luot
            if da_don_sach_luot:
                return
            da_don_sach_luot = True
            try:
                if mode == "6" and autosms_service and getattr(autosms_service, 'order_id', None):
                    autosms_service.cancel_order(log_fn=self.log, ly_do=ly_do)
            except Exception:
                pass
            if self.user_id > 0:
                self.log(f'🧹 [{ly_do}] Đang chạy User ảo CleanFB (ID {self.user_id}) -> Sẽ xóa sạch User làm lại từ đầu!')
            else:
                self.log(f'🧹 [{ly_do}] Đóng tab FB -> Xóa tất cả dữ liệu FB -> Tắt bật 4G để làm lại từ đầu!')
                try:
                    self.xoa_du_lieu_dong_tab_va_mo_lai_fb_sach(
                        mo_lai_fb=False,
                        tat_bat_4g=True,
                        bo_qua_cooldown_4g=True,
                        kiem_tra_go_het_truoc=False
                    )
                except Exception as err_clean_fail:
                    self.log(f'⚠️ Lỗi xóa dữ liệu nổi ({str(err_clean_fail)[:35]}) -> Ép xóa sạch dữ liệu FB qua ADB!')
                    try:
                        xoa_du_lieu_fb(self.serial, user_id=0)
                    except Exception:
                        pass
                if preloaded_avatar_paths:
                    self.xoa_anh_tam_tren_dt(preloaded_avatar_paths)

        try:
            while time.time() < han_chot_tong and not STOP_EVENT.is_set():
                try:
                    snap = self.quet_snapshot()

                    # 0A. Nếu uiautomator2 lỗi đọc XML -> reconnect nhẹ u2 (KHÔNG giết FB, KHÔNG tắt Wi-Fi/4G!)
                    if snap.get('dump_error'):
                        if self._consecutive_dump_errors >= 3:
                            self._phuc_hoi_u2_nhe()
                        time.sleep(0.45)
                        continue

                    # 0. Bắt ANR / Crash thực sự trên snapshot
                    if self.xu_ly_anr_va_crash(tu_mo_lai_fb=True, snap=snap) == 'restarted':
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    # 0B. Nếu thấy gói Google Play Services trong snapshot -> kiểm tra mCurrentFocus & đóng lớp phủ ngay lập tức
                    if 'com.google.android.gms' in snap['packages']:
                        thoi_diem_quet_lop_phu = time.time()
                        if self.dong_goi_y_google(max_thu=3):
                            thoi_diem_buoc_cuoi = time.time()
                            continue

                    # 1. Màn hình đang TRẮNG / LAG / ĐANG TẢI hoặc vừa bấm nút đang quay vòng -> ĐỢI CHUYỂN TRANG (KHÔNG bấm lại / KHÔNG giết FB!)
                    if snap['is_blank_or_loading'] or (snap['has_progress'] and (time.time() - last_step_ts) < 7.5):
                        now = time.time()
                        if now - thoi_diem_quet_lop_phu >= 2.0:
                            thoi_diem_quet_lop_phu = now
                            if self.dong_goi_y_google(max_thu=2):
                                thoi_diem_buoc_cuoi = time.time()
                                continue
                        if now - thoi_diem_kiem_tra_app >= 7.0:
                            thoi_diem_kiem_tra_app = now
                            self.dam_bao_fb_dang_chay(max_retry=1, cho_len_giay=3.5, cho_phep_force_stop=False, snap=snap)
                        if now - thoi_diem_log_trang >= 4.0:
                            self.log('⏳ Màn hình đang trắng / tải dữ liệu -> Đợi nhận diện xong mới thao tác...')
                            thoi_diem_log_trang = now
                        if now - thoi_diem_buoc_cuoi > 55.0:
                            self.log('❌ Màn hình treo trắng quá 55s -> Hủy lượt này!')
                            return None
                        time.sleep(0.35)
                        continue

                    # 2. Kiểm tra Die / Checkpoint tức thì trên snapshot
                    ly_do_die = self.kiem_tra_tai_khoan_die(snap=snap)
                    if ly_do_die:
                        raise AccountDieError(ly_do_die)

                    # 2B. Khi mới mở FB (màn Đăng nhập / Tham gia FB), quét định kỳ mCurrentFocus đề phòng lớp phủ trong suốt đè lên trên giao diện FB
                    if buoc_cuoi in ('', 'LOGIN_CREATE', 'JOIN_FB') and (time.time() - thoi_diem_quet_lop_phu) >= 1.8:
                        thoi_diem_quet_lop_phu = time.time()
                        if self.dong_goi_y_google(max_thu=4):
                            thoi_diem_buoc_cuoi = time.time()
                            continue

                    # 3. Xử lý các màn hình trung gian / popup ngay khi vừa xuất hiện
                    if self.dong_bang_google_play_tai_bo_sung(snap=snap):
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    if self.xu_ly_man_hinh_dieu_khoan_meta(snap=snap):
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    if self.bo_qua_luu_thong_tin_dang_nhap(snap=snap):
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    if not self._snap_has(snap, ['thêm ảnh đại diện', 'thêm ảnh', 'add profile picture']):
                        if self._snap_click(snap, ['Bỏ qua', 'BỎ QUA', 'Skip'], exact=True):
                            self.log('🛡️ [Nhận diện] Bấm "Bỏ qua"...')
                            self._cho_chuyen_man_hinh(snap['sig'], timeout=2.0)
                            thoi_diem_buoc_cuoi = time.time()
                            continue
                        btn_deny = self._snap_find_rid(snap, [
                            'com.android.permissioncontroller:id/permission_deny_button',
                            'com.android.permissioncontroller:id/permission_deny_and_dont_ask_again_button',
                            'com.lbe.security.miui:id/permission_deny_button_1'
                        ])
                        if btn_deny:
                            self.log('🛡️ [Nhận diện] Bấm "Không cho phép" (quyền hệ thống)...')
                            self.click_toa_do_an_toan(btn_deny['cx'], btn_deny['cy'])
                            self._cho_chuyen_man_hinh(snap['sig'], timeout=2.0)
                            thoi_diem_buoc_cuoi = time.time()
                            continue
                        if self._snap_click(snap, ['KHÔNG CHO PHÉP', 'Không cho phép', "DON'T ALLOW", 'Don’t allow', 'TỪ CHỐI', 'Từ chối'], exact=True, click_duoi=True):
                            self.log('🛡️ [Nhận diện] Bấm "Không cho phép"...')
                            self._cho_chuyen_man_hinh(snap['sig'], timeout=2.0)
                            thoi_diem_buoc_cuoi = time.time()
                            continue

                    # 4. Nếu dính 1 hoặc nhiều trang FB / nick cũ trên User 0 -> Gỡ BẰNG HẾT mọi trang FB -> Xóa tab FB -> Xóa dữ liệu -> Tắt bật 4G -> Mở lại FB sạch!
                    if self.user_id == 0 and (
                        self._snap_has(snap, [
                            'Bạn đang nghĩ gì', 'Tạo tin', 'Tìm bạn bè từ danh bạ',
                            'đã giúp bạn đăng nhập vào Facebook',
                        ])
                        or self._co_dau_hieu_con_trang_fb_luu(snap)
                    ):
                        self.log('⚠️ [Nhận diện] Phát hiện trang FB / nick cũ -> Gỡ BẰNG HẾT -> Xóa tab FB -> Xóa dữ liệu -> Tắt bật 4G...')
                        self.dang_xuat_va_go_trang_ca_nhan(
                            thoat_tab_truoc=False,
                            xoa_data_truoc=False,
                            xoa_data_dong_tab_cuoi=True,
                            mo_lai_fb_cuoi=True,
                            tat_bat_4g_cuoi=True
                        )
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    # ==================== NHẬN DIỆN TỪNG MÀN HÌNH ĐĂNG KÝ (CỤ THỂ TRƯỚC -> MỞ ĐẦU SAU) ====================

                    # BƯỚC 11: Màn hình "Nhập mã xác nhận" (OTP)
                    if self._snap_has(snap, ['Mã xác nhận', 'Nhập mã xác nhận', 'Nhập mã gồm', 'Xác nhận tài khoản', 'Confirmation code']):
                        # CHỐNG KẸT PHIÊN CŨ: Nếu vừa mở FB lên (chưa nhập Tên/SĐT/Email/MK ở lượt này) đã hiện sẵn trang OTP cũ
                        # -> Xóa sạch tab + xóa dữ liệu FB rồi mở lại làm lại từ đầu (không mất oan lượt mới!)
                        la_man_otp_cu_con_sot = (
                            (not da_nhap_sdt_xong and not da_nhap_email_xong and not da_nhap_mk_xong and buoc_cuoi in ('', 'LOGIN_CREATE', 'JOIN_FB'))
                            or (mode == "6" and not so_dt)
                        )
                        if la_man_otp_cu_con_sot:
                            self.log('⚠️ [Phiên cũ còn sót] Vừa mở FB đã dính trang Nhập mã OTP của lượt cũ -> Xóa sạch dữ liệu FB & mở lại làm từ đầu!')
                            if self.user_id > 0:
                                return None
                            self.xoa_du_lieu_dong_tab_va_mo_lai_fb_sach(
                                mo_lai_fb=True,
                                tat_bat_4g=True,
                                bo_qua_cooldown_4g=True,
                                kiem_tra_go_het_truoc=False
                            )
                            buoc_cuoi = ''
                            last_step_sig = ''
                            thoi_diem_buoc_cuoi = time.time()
                            continue

                        o_otp_node = snap['edit_texts'][0] if snap['edit_texts'] else self._snap_find(snap, ['Mã xác nhận', 'Nhập mã', 'Confirmation code'], exact=False)
                        if o_otp_node is None:
                            time.sleep(0.3)
                            continue
                        self.log('📩 [Nhận diện] Đã vào trang Nhập mã OTP!')
                        code = None
                        if mode == "6" and autosms_service:
                            # SPAM GỬI LẠI MÃ OTP LIÊN TỤC TRÊN CÙNG 1 ĐƠN (KHÔNG HỦY ĐƠN SỚM!):
                            # - Chỉ khi spam hết số lần gửi lại / FB chặn gửi hẳn / đơn hết hạn trên web -> MỚI bấm "Đổi số di động" & thuê số mới!
                            max_gui_lai_sms = max(1, int((self.config or {}).get('so_lan_spam_gui_lai_otp_sms', 8)))
                            tg_nhip_sms = max(12, int((self.config or {}).get('thoi_gian_cho_moi_nhip_otp_sms', 22)))
                            for lan_sms in range(max_gui_lai_sms + 1):
                                if STOP_EVENT.is_set():
                                    break
                                # Gia hạn han_chot_tong liên tục để vòng lặp tổng KHÔNG BAO GIỜ tự hủy đơn khi đang spam OTP!
                                han_chot_tong = max(han_chot_tong, time.time() + 180.0)
                                thoi_diem_buoc_cuoi = time.time()
                                tg_cho_sms = (tg_nhip_sms + 4) if lan_sms in (0, max_gui_lai_sms) else tg_nhip_sms
                                self.log(
                                    f'📱 [Spam OTP SMS - Nhịp {lan_sms + 1}/{max_gui_lai_sms + 1}] '
                                    f'Giữ nguyên đơn #{autosms_service.order_id} ({so_dt}) -> Chờ tối đa {tg_cho_sms}s...'
                                )
                                code = autosms_service.get_otp_code(timeout=tg_cho_sms, log_fn=self.log, poll_interval=2.5)
                                if code:
                                    self.log(f'🔢 ĐÃ LẤY ĐƯỢC OTP SMS: {code}')
                                    break
                                self.kiem_tra_va_dung_neu_die(f'Chờ OTP SMS nhịp {lan_sms + 1}')
                                if getattr(autosms_service, 'last_order_ended', False):
                                    self.log('🛑 Đơn thuê số trên AutoSMS đã hết hạn/đóng -> Dừng spam số này để đổi sang số mới!')
                                    break
                                if lan_sms < max_gui_lai_sms:
                                    self.log(
                                        f'🔁 [Spam gửi lại lần {lan_sms + 1}/{max_gui_lai_sms}] Chưa thấy OTP -> '
                                        f'Bấm "Tôi không nhận được mã" -> "Gửi lại mã đến SMS" (KHÔNG hủy đơn)...'
                                    )
                                    kq_resend = self._bam_gui_lai_ma_otp(la_che_do_sms=True)
                                    if kq_resend == 'BLOCKED':
                                        self.log('🚫 Facebook đã chặn gửi lại mã cho số này -> Chuyển sang Đổi số di động & thuê số mới!')
                                        break
                                    if kq_resend == 'COOLDOWN':
                                        # Vẫn GIỮ ĐƠN, kiểm tra API liên tục thêm 15s trong lúc chờ hết cooldown FB
                                        code = autosms_service.get_otp_code(timeout=15, log_fn=self.log, poll_interval=2.5)
                                        if code:
                                            self.log(f'🔢 ĐÃ LẤY ĐƯỢC OTP SMS TRONG LÚC CHỜ COOLDOWN: {code}')
                                            break
                                    elif kq_resend == 'NO_BTN':
                                        time.sleep(2.0)
                                    else:
                                        time.sleep(1.5)
                        else:
                            # Chế độ Email: spam gửi lại mã nhiều lần trên cùng email -> mãi không về mới đổi email mới
                            max_gui_lai_em = max(1, int((self.config or {}).get('so_lan_spam_gui_lai_otp_email', 5)))
                            tg_nhip_em = max(15, int((self.config or {}).get('thoi_gian_cho_moi_nhip_otp_email', 28)))
                            han_chot_tong = max(han_chot_tong, time.time() + (max_gui_lai_em + 2) * tg_nhip_em + 90.0)
                            code = self.lay_otp_theo_che_do(
                                mode=mode,
                                used_email=tai_khoan_lien_he,
                                mail_service=mail_service,
                                imap_service=imap_service,
                                hotmail_service=hotmail_service,
                                uid_moc=uid_moc,
                                force_8_digits=False,
                                wait_timeout=tg_nhip_em,
                                max_resend_attempts=max_gui_lai_em
                            )

                        # CHỈ KHI ĐÃ SPAM HẾT CÁC LẦN GỬI LẠI MÀ VẪN KHÔNG CÓ OTP (HOẶC BỊ CHẶN/HẾT HẠN) -> MỚI BẤM ĐỔI SỐ / ĐỔI EMAIL & THUÊ SỐ MỚI!
                        if not code:
                            if so_lan_doi_lien_he_otp < max_lan_doi_lien_he_otp and not STOP_EVENT.is_set():
                                so_lan_doi_lien_he_otp += 1
                                if mode == "6" and autosms_service:
                                    self.log(
                                        f'🔄 [Đã spam hết mà không về OTP - Đổi số lần {so_lan_doi_lien_he_otp}/{max_lan_doi_lien_he_otp}] '
                                        f'Bấm "Tôi không nhận được mã" -> "Đổi số di động" để thuê số mới...'
                                    )
                                    if self._bam_doi_sdt_hoac_email_tu_otp(la_che_do_sms=True):
                                        so_cu_digits = re.sub(r'\D', '', str(so_dt or ''))
                                        if so_cu_digits:
                                            ds_sdt_loi.add(so_cu_digits)
                                        try:
                                            autosms_service.cancel_order(log_fn=self.log, ly_do='Spam hết không về OTP -> Đổi số mới')
                                        except Exception:
                                            pass
                                        so_dt = None
                                        da_nhap_sdt_xong = False
                                        thoi_diem_bam_tiep_sdt = 0.0
                                        han_chot_tong = max(han_chot_tong, time.time() + 240.0)
                                        _chot_buoc('OTP_CHANGE_PHONE', snap['sig'])
                                        continue
                                elif refill_email_fn is not None:
                                    self.log(
                                        f'🔄 [Đã spam hết mà không về OTP Email - Đổi mail lần {so_lan_doi_lien_he_otp}/{max_lan_doi_lien_he_otp}] '
                                        f'Bấm "Tôi không nhận được mã" -> "Đổi địa chỉ email"...'
                                    )
                                    if self._bam_doi_sdt_hoac_email_tu_otp(la_che_do_sms=False):
                                        new_em, new_ms, new_imap, new_hm, _ = refill_email_fn()
                                        if not new_em:
                                            self.log('❌ Đã hết Email mới để đổi khi không về OTP!')
                                            return None
                                        if imap_service and imap_service is not new_imap:
                                            try:
                                                imap_service.close()
                                            except Exception:
                                                pass
                                        if new_imap:
                                            imap_moi_tao_trong_ham.append(new_imap)
                                        used_email = new_em
                                        tai_khoan_lien_he = new_em
                                        mail_service = new_ms
                                        imap_service = new_imap
                                        hotmail_service = new_hm
                                        da_chot_moc_mail = False
                                        da_nhap_email_xong = False
                                        thoi_diem_bam_tiep_email = 0.0
                                        han_chot_tong = max(han_chot_tong, time.time() + 240.0)
                                        self.log(f'📧 Đã lấy Email mới để đổi: {used_email}')
                                        _chot_buoc('OTP_CHANGE_EMAIL', snap['sig'])
                                        continue

                            if mode == "6" and autosms_service:
                                autosms_service.cancel_order(log_fn=self.log, ly_do='Hết lượt đổi số mà vẫn không về OTP')
                            return None

                        snap_otp_now = self.cho_man_hinh_san_sang(timeout=15.0, ngu_canh='Trước khi gõ OTP')
                        o_otp_now = snap_otp_now['edit_texts'][0] if snap_otp_now['edit_texts'] else self._snap_find(snap_otp_now, ['Mã xác nhận', 'Nhập mã', 'Confirmation code'], exact=False)
                        if o_otp_now is None:
                            continue
                        self.log(f'🔢 Nhập mã OTP: {code}')
                        self._nhap_vao_node_va_xac_minh(o_otp_now, code)
                        self._ha_ban_phim_an_toan()
                        snap_otp_btn = self.quet_snapshot()
                        self.log('⏩ Bấm Tiếp / Gửi mã OTP')
                        if not self._snap_click(snap_otp_btn, ['Tiếp', 'Next', 'Gửi', 'Xác nhận', 'Confirm'], exact=True, click_duoi=True):
                            self._snap_click(snap_otp_btn, ['Tiếp', 'Gửi', 'Xác nhận'], exact=False, click_duoi=True)
                        self._cho_chuyen_man_hinh(
                            snap_otp_btn['sig'],
                            timeout=6.0,
                            old_screen_keywords=['Nhập mã xác nhận', 'Nhập mã gồm', 'Confirmation code']
                        )
                        da_nhap_otp = True
                        break

                    # BƯỚC 10: Màn hình chọn gửi mã qua SMS
                    if self._snap_has(snap, ['Gửi mã qua SMS', 'Nhận mã qua SMS']):
                        self.log('📩 [Nhận diện] Bấm "Gửi mã qua SMS"...')
                        self._snap_click(snap, ['Gửi mã qua SMS', 'Nhận mã qua SMS'], exact=False)
                        self._cho_chuyen_man_hinh(snap['sig'], timeout=3.0)
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    # BƯỚC 9: Màn hình Điều khoản & Chính sách ("Tôi đồng ý") — loại trừ mọi màn hình có ô nhập (Mật khẩu / SĐT / Email)!
                    if (
                        not snap['edit_texts']
                        and not _dang_cho_chuyen_buoc('AGREE', snap['sig'], 10.0)
                        and not self._snap_has(snap, ['Tạo mật khẩu', 'Create a password', 'Số di động của bạn là gì', 'Email của bạn là gì'])
                        and self._snap_has(snap, [
                            'Tôi đồng ý', 'I agree',
                            'Để đăng ký, hãy đọc cũng như đồng ý',
                            'đồng ý với các điều khoản và chính sách',
                            'Các điểm chính bạn nên biết',
                            'To sign up, read and agree', 'Agree to Facebook'
                        ])
                    ):
                        # Nếu bàn phím từ bước mật khẩu vẫn đang kẹt mở -> hạ bàn phím trước để lộ nút "Tôi đồng ý"
                        if self._ban_phim_dang_mo():
                            self.log('⌨️ [Điều khoản] Đóng bàn phím đang che nút "Tôi đồng ý"...')
                            self._ha_ban_phim_an_toan()
                            snap = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Sau đóng bàn phím Điều khoản')

                        btn_agree = self._snap_find(snap, ['Tôi đồng ý', 'I agree'], exact=True, click_duoi=True) or self._snap_find(snap, ['Tôi đồng ý', 'I agree'], exact=False, click_duoi=True)
                        if btn_agree is None:
                            # Nếu nút "Tôi đồng ý" vẫn nằm dưới nếp cuộn -> vuốt xuống nhẹ để lộ nút rồi quét lại
                            w_cur, h_cur = snap['w'], snap['h']
                            self.vuot_toa_do_an_toan(int(w_cur * 0.50), int(h_cur * 0.78), int(w_cur * 0.50), int(h_cur * 0.30), 220)
                            time.sleep(0.5)
                            snap = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Cuộn tìm nút Tôi đồng ý')
                            btn_agree = self._snap_find(snap, ['Tôi đồng ý', 'I agree'], exact=True, click_duoi=True) or self._snap_find(snap, ['Tôi đồng ý', 'I agree'], exact=False, click_duoi=True)

                        if btn_agree is not None:
                            self.log('✅ [Nhận diện] Màn hình Điều khoản -> Bấm "Tôi đồng ý" (tự đợi trang OTP tải xong)...')
                            self.click_toa_do_an_toan(btn_agree['cx'], btn_agree['cy'])
                            self._cho_chuyen_man_hinh(snap['sig'], timeout=4.0)
                            _chot_buoc('AGREE', snap['sig'])
                        else:
                            time.sleep(0.4)
                        continue

                    # BƯỚC 8: Màn hình "Tạo mật khẩu" -> Khóa chống lặp, đợi màn ổn định, xóa sạch ô (chống dính SĐT/Email), GÕ TỪ TỪ TỪNG KÝ TỰ MỘT
                    if self._snap_has(snap, ['Tạo mật khẩu', 'Create a password']):
                        if da_nhap_mk_xong and (time.time() - thoi_diem_bam_tiep_mk) < 12.0:
                            self.log('⏳ [Mật khẩu] Đã nhập xong Mật khẩu & bấm Tiếp -> Đợi Facebook chuyển sang bước tiếp theo...')
                            time.sleep(0.7)
                            continue
                        # Chờ 0.7s cho giao diện "Tạo mật khẩu" ổn định hẳn trước khi chạm vào ô nhập
                        time.sleep(0.7)
                        snap_p0 = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Ổn định màn hình Tạo mật khẩu')
                        if not self._snap_has(snap_p0, ['Tạo mật khẩu', 'Create a password']):
                            continue

                        o_mk_node = None
                        for ed_n in snap_p0['edit_texts']:
                            if ed_n.get('password') or any(k in (ed_n.get('text_low') or '') or k in (ed_n.get('desc_low') or '') for k in ['mật khẩu', 'password']):
                                o_mk_node = ed_n
                                break
                        if o_mk_node is None:
                            o_mk_node = snap_p0['edit_texts'][-1] if snap_p0['edit_texts'] else self._snap_find(snap_p0, ['Mật khẩu', 'Password'], exact=True)
                        if o_mk_node is None:
                            time.sleep(0.3)
                            continue

                        self.log(f'🔑 [Nhận diện] Màn hình Mật khẩu -> Gõ từ từ từng ký tự ({len(mat_khau_fb)} ký tự, không dán): {mat_khau_fb}')
                        mk_hop_le = False
                        for lan_mk in range(1, 4):
                            try:
                                self.chay_shell_nhanh('cmd autofill destroy')
                            except Exception:
                                pass
                            self.click_toa_do_an_toan(o_mk_node['cx'], o_mk_node['cy'])
                            time.sleep(0.45)

                            # Tìm đúng phần tử EditText mật khẩu đang hiển thị
                            elem_mk = None
                            try:
                                edits_mk = self.d(className='android.widget.EditText')
                                cnt_mk = edits_mk.count
                                if cnt_mk == 1:
                                    elem_mk = edits_mk[0]
                                elif cnt_mk > 1:
                                    for idx_e in range(cnt_mk):
                                        inf_e = edits_mk[idx_e].info
                                        if inf_e.get('password') or inf_e.get('focused'):
                                            elem_mk = edits_mk[idx_e]
                                            break
                                    if elem_mk is None:
                                        elem_mk = edits_mk[-1]
                            except Exception:
                                pass

                            # Gõ từ từ từng chữ một (0.14s/ký tự)
                            ok_go_mk = self._go_tung_ky_tu_cham(mat_khau_fb, elem=elem_mk, is_password=True, delay_ky_tu=0.14)
                            time.sleep(0.4)

                            snap_chk_mk = self.quet_snapshot()
                            ed_chk = None
                            for ed_n in snap_chk_mk['edit_texts']:
                                if ed_n.get('password') or abs(ed_n['cy'] - o_mk_node['cy']) <= 120:
                                    ed_chk = ed_n
                                    break
                            if ed_chk is None and snap_chk_mk['edit_texts']:
                                ed_chk = snap_chk_mk['edit_texts'][-1]

                            txt_mk_hien_tai = (ed_chk.get('text') or '').strip() if ed_chk is not None else ''
                            # Nếu ô vẫn trống/placeholder sau khi gõ phím cứng -> fallback set_text ở lần cuối
                            if self._la_placeholder_o_nhap(txt_mk_hien_tai):
                                if ok_go_mk and txt_mk_hien_tai == '':
                                    # Android ẩn hẳn text ô password thành "" dù đã gõ thành công bằng phím cứng
                                    mk_hop_le = True
                                    break
                                if lan_mk >= 2 and elem_mk is not None:
                                    self.log('⚠️ Phím cứng ADB không ăn vào ô Mật khẩu -> Thử ghi trực tiếp set_text...')
                                    try:
                                        self.xoa_o_nhap(elem_mk)
                                        elem_mk.set_text(mat_khau_fb)
                                        time.sleep(0.45)
                                        if self._kiem_tra_o_da_co_chu(elem_mk, mat_khau_fb, is_password=True):
                                            mk_hop_le = True
                                            break
                                    except Exception:
                                        pass
                                continue

                            # Kiểm tra chặt: tuyệt đối không chấp nhận nếu dính Email, dính SĐT hoặc lệch độ dài mật khẩu
                            dinh_email_hoac_sdt = (
                                (used_email and used_email.lower() in txt_mk_hien_tai.lower())
                                or (so_dt and re.sub(r'\D', '', str(so_dt)) and re.sub(r'\D', '', str(so_dt)) in re.sub(r'\D', '', txt_mk_hien_tai))
                            )
                            if dinh_email_hoac_sdt or len(txt_mk_hien_tai) != len(mat_khau_fb):
                                self.log(
                                    f'⚠️ Ô Mật khẩu sai nội dung/độ dài ({len(txt_mk_hien_tai)} != {len(mat_khau_fb)}) '
                                    f'-> Xóa sạch & gõ lại từng ký tự lần {lan_mk + 1}/3...'
                                )
                                self.xoa_o_nhap(elem_mk)
                                o_mk_node = ed_chk if ed_chk is not None else o_mk_node
                                continue

                            mk_hop_le = True
                            break

                        if not mk_hop_le:
                            self.log('❌ Ô Mật khẩu chưa khớp sau 3 lần gõ từng ký tự -> Chưa bấm Tiếp để tránh sai mật khẩu!')
                            time.sleep(0.6)
                            continue

                        time.sleep(0.35)
                        self._ha_ban_phim_an_toan()
                        snap_mk = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Sau đóng bàn phím Mật khẩu')
                        if self._snap_has(snap_mk, ['Tạo mật khẩu', 'Create a password']):
                            self._snap_click(snap_mk, ['Tiếp', 'Next'], exact=True, click_duoi=True)
                            da_nhap_mk_xong = True
                            thoi_diem_bam_tiep_mk = time.time()
                            self._cho_chuyen_man_hinh(snap_mk['sig'], timeout=9.0, old_screen_keywords=['Tạo mật khẩu', 'Create a password'])
                        _chot_buoc('PASSWORD', snap['sig'])
                        continue

                    # BƯỚC 7: Màn hình "Email của bạn là gì?" hoặc "Đổi địa chỉ email" (sau khi đổi từ màn OTP)
                    cac_man_email = [
                        'Email của bạn là gì', "What's your email", 'What’s your email',
                        'Nhập email của bạn', 'Địa chỉ email',
                        'Đổi địa chỉ email', 'Thay đổi địa chỉ email', 'Đổi email', 'Thay đổi email',
                        'Nhập email mới', 'Email mới', 'Cập nhật địa chỉ email',
                        'Change email address', 'Change email', 'Update email address', 'New email'
                    ]
                    dang_mo_bang_day_otp = self._snap_has(snap, [
                        'Gửi lại mã đến SMS', 'Gửi lại mã qua SMS', 'Gửi lại mã đến email', 'Gửi lại mã qua email',
                        'Xác nhận bằng email', 'Resend code via SMS', 'Resend code via email'
                    ])
                    if (not dang_mo_bang_day_otp) and self._snap_has(snap, cac_man_email):
                        o_em_node = snap['edit_texts'][0] if snap['edit_texts'] else self._snap_find(snap, ['Email', 'Địa chỉ email'], exact=False)
                        if o_em_node is None:
                            time.sleep(0.3)
                            continue

                        txt_em_hien_tai = (o_em_node.get('text') or '').strip().lower()
                        email_da_nam_trong_o = bool(used_email and txt_em_hien_tai == used_email.strip().lower())

                        # KHÓA CHỐNG LẶP: Nếu đã nhập Email & vừa bấm "Tiếp" trong vòng 12s -> ĐỨNG ĐỢI chuyển trang, TUYỆT ĐỐI KHÔNG GÕ LẠI!
                        if da_nhap_email_xong and (time.time() - thoi_diem_bam_tiep_email) < 12.0:
                            if email_da_nam_trong_o:
                                self.log('⏳ [Email] Đã nhập xong Email & bấm Tiếp -> Đợi Facebook chuyển trang tiếp theo...')
                                time.sleep(0.8)
                                continue

                        if not da_chot_moc_mail:
                            if mode in ["3", "4"] and imap_service:
                                uid_moc = imap_service.get_latest_uid()
                            elif mode == "5" and hotmail_service:
                                hotmail_service.init_baseline()
                            da_chot_moc_mail = True

                        tai_khoan_lien_he = used_email

                        # Chỉ gõ Email nếu ô Email CHƯA chứa đúng địa chỉ used_email
                        if not email_da_nam_trong_o:
                            # Xác minh lần cuối ngay trước khi gõ rằng màn hình CHƯA nhảy sang "Tạo mật khẩu"
                            snap_pre_em = self.quet_snapshot()
                            if self._snap_has(snap_pre_em, ['Tạo mật khẩu', 'Create a password']):
                                continue
                            # Nếu trong ô đang có email cũ -> xóa sạch bằng nút X hoặc EditText trước khi gõ email mới
                            if txt_em_hien_tai and not self._la_placeholder_o_nhap(txt_em_hien_tai):
                                self._xoa_sach_o_sdt(snap_pre_em, o_em_node)
                                snap_pre_em = self.quet_snapshot()
                                o_em_node = snap_pre_em['edit_texts'][0] if snap_pre_em['edit_texts'] else o_em_node
                            self.log(f'📧 [Nhận diện] Màn hình Email -> Nhập: {used_email}')
                            self._nhap_vao_node_va_xac_minh(o_em_node, used_email)
                            time.sleep(0.35)
                            self._ha_ban_phim_an_toan()

                        # Xác minh lại màn hình TRƯỚC khi bấm "Tiếp / Cập nhật"
                        snap_em = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Sau nhập Email')
                        if self._snap_has(snap_em, ['Tạo mật khẩu', 'Create a password']):
                            self.log('⚡ Màn hình đã chuyển sang "Tạo mật khẩu" -> Chuyển ngay sang Bước 8!')
                            continue
                        if not self._snap_has(snap_em, cac_man_email):
                            continue

                        nhan_em_next = self._tim_va_bam_chu_dong(
                            snap_em,
                            ['Tiếp', 'Tiếp tục', 'Cập nhật', 'Xác nhận', 'Lưu', 'Next', 'Continue', 'Update', 'Confirm', 'Save'],
                            exclude_keywords=['đăng ký bằng', 'số di động', 'tìm tài khoản'],
                            min_y=0.25,
                            max_y=0.92
                        )
                        self.log(f'⏩ [Email] Đã bấm "{nhan_em_next or "Tiếp"}" và chờ chuyển trang...')
                        da_nhap_email_xong = True
                        thoi_diem_bam_tiep_email = time.time()
                        _chot_buoc('EMAIL', snap['sig'])
                        self._cho_chuyen_man_hinh(snap_em['sig'], timeout=10.0, old_screen_keywords=cac_man_email)
                        continue

                    # BƯỚC 6B: Màn hình "Tiếp tục tạo tài khoản"
                    if self._snap_has(snap, ['Tiếp tục tạo tài khoản', 'Continue creating account']):
                        self.log('⏩ [Nhận diện] Bấm "Tiếp tục tạo tài khoản"...')
                        self._snap_click(snap, ['Tiếp tục tạo tài khoản', 'Continue creating account'], exact=False, click_duoi=True)
                        self._cho_chuyen_man_hinh(snap['sig'], timeout=3.0)
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    # BƯỚC 6: Màn hình "Số di động của bạn là gì?" hoặc "Đổi số di động" (sau khi đổi từ màn OTP) -> TỰ ĐỔI SỐ MỚI KHI FB BÁO LỖI!
                    cac_man_sdt = [
                        'Số di động của bạn là gì', "What's your mobile number", 'What’s your mobile number',
                        'Đăng ký bằng email', 'Sign up with email',
                        'Đổi số di động', 'Thay đổi số di động', 'Đổi số điện thoại', 'Thay đổi số điện thoại',
                        'Nhập số di động mới', 'Số di động mới', 'Cập nhật số di động',
                        'Change mobile number', 'Change phone number', 'Update mobile number', 'New mobile number'
                    ]
                    if (not dang_mo_bang_day_otp) and self._snap_has(snap, cac_man_sdt):
                        if mode == "6" and autosms_service:
                            cac_dau_hieu_loi_sdt = [
                                'có vẻ như số di động của bạn không đúng',
                                'số di động của bạn không đúng',
                                'số di động không hợp lệ',
                                'số điện thoại không hợp lệ',
                                'hãy nhập đầy đủ số của bạn',
                                'bao gồm mã quốc gia',
                                'vui lòng nhập số di động hợp lệ',
                                'nhập số di động hợp lệ',
                                'số này không hợp lệ',
                                'không thể gửi mã đến số này',
                                'số di động này đã được sử dụng',
                                'looks like your mobile number',
                                'does not seem to be valid',
                                "doesn't seem to be valid",
                                'doesn’t seem to be valid',
                                'enter a valid mobile number',
                                'enter a valid phone number',
                                'include your country code',
                                'including the country code',
                                'invalid mobile number',
                                'invalid phone number',
                                'number is not valid',
                                "number isn't valid",
                                'number isn’t valid',
                            ]
                            o_sdt_node = snap['edit_texts'][0] if snap['edit_texts'] else self._snap_find(snap, ['Số di động', 'Mobile number'], exact=False)
                            if o_sdt_node is None:
                                time.sleep(0.3)
                                continue

                            co_loi_sdt = self._snap_has(snap, cac_dau_hieu_loi_sdt)

                            # PHÁT HIỆN LỖI SĐT (VD: "Có vẻ như số di động của bạn không đúng...") -> HỦY & THUÊ SỐ KHÁC -> XÓA SỐ CŨ -> NHẬP SỐ MỚI -> BẤM TIẾP!
                            if co_loi_sdt:
                                so_lan_doi_sdt += 1
                                so_cu_digits = re.sub(r'\D', '', str(so_dt or (o_sdt_node.get('text') or '')))
                                if so_cu_digits:
                                    ds_sdt_loi.add(so_cu_digits)
                                if so_lan_doi_sdt > max_lan_doi_sdt:
                                    self.log(f'❌ [SĐT lỗi] Đã đổi quá {max_lan_doi_sdt} số liên tiếp vẫn bị Facebook từ chối -> Hủy lượt & xóa dữ liệu làm lại!')
                                    return None

                                self.log(f'⚠️ [SĐT lỗi lần {so_lan_doi_sdt}/{max_lan_doi_sdt}] Facebook báo số "{so_dt or o_sdt_node.get("text")}" không đúng -> Hủy số cũ & thuê số mới...')
                                so_moi = self._thue_sdt_moi_khac_so_cu(autosms_service, ds_sdt_loi, max_thu_thue=3)
                                if not so_moi:
                                    self.log('❌ Không thuê được SĐT mới khác số cũ từ AutoSMS.site!')
                                    return None

                                so_dt = so_moi
                                tai_khoan_lien_he = so_dt
                                da_nhap_sdt_xong = False
                                thoi_diem_bam_tiep_sdt = 0.0

                                # Xóa sạch số cũ trong ô (ưu tiên bấm nút X trong ô rồi xác minh xóa trắng EditText)
                                self._xoa_sach_o_sdt(snap, o_sdt_node)
                                snap_sau_xoa = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Sau khi xóa số cũ bị lỗi')
                                o_sdt_node = snap_sau_xoa['edit_texts'][0] if snap_sau_xoa['edit_texts'] else self._snap_find(snap_sau_xoa, ['Số di động', 'Mobile number'], exact=False)
                                if o_sdt_node is None:
                                    continue

                            if not so_dt:
                                self.log('📞 [Nhận diện] Màn hình SĐT -> Thuê số từ AutoSMS.site...')
                                if ds_sdt_loi:
                                    so_dt = self._thue_sdt_moi_khac_so_cu(autosms_service, ds_sdt_loi, max_thu_thue=3)
                                else:
                                    so_dt = autosms_service.buy_number(log_fn=self.log)
                                if not so_dt:
                                    self.log('❌ Không thuê được SĐT!')
                                    return None
                                tai_khoan_lien_he = so_dt

                            so_dt_digits = re.sub(r'\D', '', str(so_dt))
                            txt_sdt_hien_tai = re.sub(r'\D', '', (o_sdt_node.get('text') or ''))
                            sdt_da_nam_trong_o = bool(so_dt_digits and txt_sdt_hien_tai == so_dt_digits)

                            # KHÓA CHỐNG LẶP: CHỈ đứng đợi khi KHÔNG có thông báo lỗi SĐT và vừa bấm Tiếp trong 12s!
                            if (not co_loi_sdt) and da_nhap_sdt_xong and (time.time() - thoi_diem_bam_tiep_sdt) < 12.0:
                                if sdt_da_nam_trong_o:
                                    self.log('⏳ [SĐT] Đã nhập xong SĐT & bấm Tiếp -> Đợi Facebook chuyển trang tiếp theo...')
                                    time.sleep(0.7)
                                    continue

                            if not sdt_da_nam_trong_o:
                                # Xác minh lần cuối màn hình chưa chuyển trang trước khi gõ SĐT
                                snap_pre_sdt = self.quet_snapshot()
                                if not self._snap_has(snap_pre_sdt, cac_man_sdt):
                                    continue
                                if txt_sdt_hien_tai:
                                    self._xoa_sach_o_sdt(snap_pre_sdt, o_sdt_node)
                                    snap_pre_sdt = self.quet_snapshot()
                                    o_sdt_node = snap_pre_sdt['edit_texts'][0] if snap_pre_sdt['edit_texts'] else o_sdt_node
                                self.log(f'📞 [Nhận diện] Nhập SĐT thuê mới: {so_dt}')
                                self._nhap_vao_node_va_xac_minh(o_sdt_node, so_dt)
                                time.sleep(0.3)
                                self._ha_ban_phim_an_toan()

                            snap_sdt = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Sau nhập SĐT')
                            if not self._snap_has(snap_sdt, cac_man_sdt):
                                continue
                            nhan_sdt_next = self._tim_va_bam_chu_dong(
                                snap_sdt,
                                ['Tiếp', 'Tiếp tục', 'Cập nhật', 'Xác nhận', 'Lưu', 'Next', 'Continue', 'Update', 'Confirm', 'Save'],
                                exclude_keywords=['đăng ký bằng email', 'sign up with email', 'tìm tài khoản'],
                                min_y=0.25,
                                max_y=0.92
                            )
                            self.log(f'⏩ [SĐT] Đã bấm "{nhan_sdt_next or "Tiếp"}" và chờ phản hồi (chuyển trang hoặc báo lỗi SĐT)...')
                            da_nhap_sdt_xong = True
                            thoi_diem_bam_tiep_sdt = time.time()

                            # Chờ động tối đa 10s: thoát TỨC THÌ khi sang màn mới HOẶC ngay khi hiện dòng lỗi đỏ SĐT!
                            moc_cho_sdt = time.time() + 10.0
                            time.sleep(0.7)
                            while time.time() < moc_cho_sdt and not STOP_EVENT.is_set():
                                s_chk_sdt = self.quet_snapshot()
                                if s_chk_sdt.get('is_blank_or_loading') or s_chk_sdt.get('has_progress'):
                                    time.sleep(0.3)
                                    continue
                                if not self._snap_has(s_chk_sdt, cac_man_sdt):
                                    break
                                if self._snap_has(s_chk_sdt, cac_dau_hieu_loi_sdt):
                                    self.log('🚨 [SĐT] Vừa bấm Tiếp đã hiện lỗi SĐT không đúng -> Chuyển sang thuê số khác ngay!')
                                    break
                                time.sleep(0.3)
                        else:
                            self.log('📧 [Nhận diện] Màn hình SĐT -> Bấm "Đăng ký bằng email"...')
                            self._snap_click(snap, ['Đăng ký bằng email', 'Sign up with email'], exact=False)
                            self._cho_chuyen_man_hinh(snap['sig'], timeout=6.0, old_screen_keywords=['Số di động của bạn là gì', "What's your mobile number"])
                        _chot_buoc('PHONE', snap['sig'])
                        continue

                    # BƯỚC 5: Màn hình "Giới tính của bạn là gì?" -> Chọn 100% Giới tính Nữ (khóa chống bấm đúp & chống rơi ngược về Ngày sinh)
                    if self._la_man_hinh_gioi_tinh(snap):
                        da_chon_ngay_sinh_xong = True
                        if da_chon_gioi_tinh_xong and (time.time() - thoi_diem_bam_tiep_gt) < 10.0:
                            self.log('⏳ [Giới tính] Đã chọn Nữ & bấm Tiếp -> Đợi Facebook chuyển sang bước tiếp theo...')
                            time.sleep(0.6)
                            continue
                        self.log('👩 [Nhận diện] Màn hình Giới tính -> Chọn Nữ & bấm Tiếp...')
                        # Tìm chính xác nút 'Nữ' / 'Female' (ưu tiên exact, dự phòng node bắt đầu bằng 'nữ'/'female' trong vùng danh sách)
                        da_bam_nu = self._snap_click(snap, ['Nữ', 'Female'], exact=True, min_y=0.14, max_y=0.78)
                        if not da_bam_nu:
                            h_gt = snap['h']
                            for n_gt in snap['nodes']:
                                if not (int(h_gt * 0.14) <= n_gt['cy'] <= int(h_gt * 0.78)):
                                    continue
                                if any(
                                    v in {'nữ', 'female'} or v.startswith(('nữ,', 'nữ ', 'female,', 'female '))
                                    for v in (n_gt['text_low'], n_gt['desc_low']) if v and len(v) <= 32
                                ):
                                    self.click_toa_do_an_toan(n_gt['cx'], n_gt['cy'])
                                    da_bam_nu = True
                                    break
                        time.sleep(0.45)
                        snap_gt = self.quet_snapshot()
                        if not self._la_man_hinh_gioi_tinh(snap_gt):
                            continue
                        self._snap_click(snap_gt, ['Tiếp', 'Next'], exact=True)
                        da_chon_gioi_tinh_xong = True
                        thoi_diem_bam_tiep_gt = time.time()
                        self._cho_chuyen_man_hinh(
                            snap_gt['sig'],
                            timeout=8.0,
                            old_screen_keywords=['Giới tính của bạn là gì', "What's your gender", 'What’s your gender', 'Chọn giới tính']
                        )
                        _chot_buoc('GENDER', snap['sig'])
                        continue

                    # BƯỚC 4B: Hộp thoại xác nhận tuổi ("OK" / "Xác nhận")
                    if self._snap_has(snap, ['Bạn có chắc', 'xác nhận tuổi', 'confirm your age']) and self._snap_has(snap, ['OK', 'Xác nhận'], exact=True):
                        self._snap_click(snap, ['OK', 'Xác nhận'], exact=True)
                        self._cho_chuyen_man_hinh(snap['sig'], timeout=4.0, old_screen_keywords=['Bạn có chắc', 'xác nhận tuổi', 'confirm your age'])
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    # BƯỚC 4A: Màn hình nhập Tuổi trực tiếp
                    if self._snap_has(snap, ['Bạn bao nhiêu tuổi', 'How old are you']) and snap['edit_texts']:
                        tuoi = str(random.randint(22, 31))
                        self.log(f'📅 [Nhận diện] Màn hình Nhập tuổi -> Nhập {tuoi}...')
                        self._nhap_vao_node_va_xac_minh(snap['edit_texts'][0], tuoi)
                        self._ha_ban_phim_an_toan()
                        snap_tuoi = self.quet_snapshot()
                        if self._snap_has(snap_tuoi, ['Bạn bao nhiêu tuổi', 'How old are you']):
                            self._snap_click(snap_tuoi, ['Tiếp', 'Next'], exact=True)
                            self._cho_chuyen_man_hinh(snap_tuoi['sig'], timeout=6.0, old_screen_keywords=['Bạn bao nhiêu tuổi', 'How old are you'])
                        buoc_cuoi = 'AGE'
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    # BƯỚC 4: Màn hình "Ngày sinh của bạn là khi nào?" hoặc bảng chọn ngày 3 cột (KHÓA CHẶT CHỐNG CHẠY LẠI LÊN TRANG GIỚI TÍNH!)
                    if self._la_man_hinh_ngay_sinh(snap):
                        if da_chon_ngay_sinh_xong and (time.time() - thoi_diem_bam_tiep_ns) < 12.0:
                            self.log('⏳ [Ngày sinh] Đã chọn xong Ngày sinh & bấm Tiếp -> Đợi Facebook chuyển sang màn "Giới tính"...')
                            time.sleep(0.7)
                            continue
                        self.log('📅 [Nhận diện] Màn hình Ngày sinh -> Chọn ngày tháng năm sinh...')
                        kq_ns = self.vuot_chon_ngay_thang_nam_sinh()
                        if kq_ns in ('DONE', 'MOVED'):
                            da_chon_ngay_sinh_xong = True
                            thoi_diem_bam_tiep_ns = time.time()
                        _chot_buoc('BIRTHDAY', snap['sig'])
                        continue

                    # BƯỚC 3: Màn hình "Bạn tên gì?" -> KHÓA CHẶT CHỐNG LẶP ĐIỀN TÊN SANG TRANG NGÀY SINH!
                    if self._snap_has(snap, ['Bạn tên gì', "What's your name", 'Nhập tên bạn sử dụng trong đời thực']):
                        node_ho = None
                        node_ten = None
                        if len(snap['edit_texts']) >= 2:
                            edits_sorted = sorted(snap['edit_texts'][:2], key=lambda n: n['l'])
                            node_ho, node_ten = edits_sorted[0], edits_sorted[1]
                        else:
                            node_ho = self._snap_find(snap, ['Họ', 'First name', 'Surname'], exact=True, max_y=0.55)
                            node_ten = self._snap_find(snap, ['Tên', 'Last name'], exact=True, max_y=0.55)
                        if node_ho is None or node_ten is None:
                            time.sleep(0.3)
                            continue

                        ho_da_nhap = ((node_ho.get('text') or '').strip().lower() == ho.strip().lower())
                        ten_da_nhap = ((node_ten.get('text') or '').strip().lower() == ten.strip().lower())

                        # KHÓA CHỐNG LẶP: Vừa điền Họ Tên & bấm Tiếp trong 10s -> ĐỨNG ĐỢI chuyển sang Ngày sinh, TUYỆT ĐỐI KHÔNG GÕ LẠI!
                        if da_nhap_ten_xong and (time.time() - thoi_diem_bam_tiep_ten) < 10.0:
                            if ho_da_nhap and ten_da_nhap:
                                self.log('⏳ [Họ Tên] Đã nhập xong Họ Tên & bấm Tiếp -> Đợi Facebook chuyển sang màn "Ngày sinh"...')
                                time.sleep(0.6)
                                continue

                        if not (ho_da_nhap and ten_da_nhap):
                            self.log(f'📝 [Nhận diện] Màn hình Họ Tên -> Nhập {ho} | {ten}')
                            if not ho_da_nhap:
                                self._nhap_vao_node_va_xac_minh(node_ho, ho, placeholders=['Họ', 'First name', 'Surname'])
                            # Xác minh lại màn hình vẫn là Họ Tên trước khi gõ ô Tên
                            snap_mid_name = self.quet_snapshot()
                            if not self._snap_has(snap_mid_name, ['Bạn tên gì', "What's your name", 'Nhập tên bạn sử dụng trong đời thực']):
                                continue
                            if not ten_da_nhap:
                                if len(snap_mid_name['edit_texts']) >= 2:
                                    node_ten = sorted(snap_mid_name['edit_texts'][:2], key=lambda n: n['l'])[1]
                                self._nhap_vao_node_va_xac_minh(node_ten, ten, placeholders=['Tên', 'Last name', 'First name'])
                            time.sleep(0.25)
                            self._ha_ban_phim_an_toan()

                        snap_sau_ten = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Sau nhập Họ Tên')
                        if not self._snap_has(snap_sau_ten, ['Bạn tên gì', "What's your name", 'Nhập tên bạn sử dụng trong đời thực']):
                            continue
                        self.log('⏩ [Họ Tên] Bấm "Tiếp" và chờ rời hẳn trang Họ Tên...')
                        self._snap_click(snap_sau_ten, ['Tiếp', 'Next'], exact=True)
                        da_nhap_ten_xong = True
                        thoi_diem_bam_tiep_ten = time.time()
                        self._cho_chuyen_man_hinh(snap_sau_ten['sig'], timeout=8.0, old_screen_keywords=['Bạn tên gì', "What's your name", 'Nhập tên bạn sử dụng trong đời thực'])
                        _chot_buoc('NAME', snap['sig'])
                        continue

                    # BƯỚC 2: Màn hình "Tham gia Facebook" (CHỈ khớp khi thực sự có chữ 'Tham gia Facebook' & nút bấm)
                    if not _dang_cho_chuyen_buoc('JOIN_FB', snap['sig'], 6.0) and self._snap_has(snap, ['Tham gia Facebook', 'Join Facebook']) and self._snap_find(snap, ['Tạo tài khoản mới', 'Bắt đầu', 'Create new account', 'Get started'], exact=False) is not None:
                        if self.dong_goi_y_google(max_thu=4):
                            thoi_diem_quet_lop_phu = time.time()
                            continue
                        self.log('🔵 [Nhận diện] Màn hình Tham gia Facebook -> Bấm "Tạo tài khoản mới / Bắt đầu"...')
                        if not self._snap_click(snap, ['Tạo tài khoản mới', 'Bắt đầu', 'Create new account', 'Get started'], exact=True):
                            self._snap_click(snap, ['Tạo tài khoản mới', 'Bắt đầu'], exact=False)
                        self._cho_chuyen_man_hinh(snap['sig'], timeout=3.0)
                        _chot_buoc('JOIN_FB', snap['sig'])
                        continue

                    # BƯỚC 1: Màn hình đăng nhập đầu tiên có nút "Tạo tài khoản mới"
                    if not _dang_cho_chuyen_buoc('LOGIN_CREATE', snap['sig'], 6.0) and self._snap_has(snap, ['Tạo tài khoản mới', 'Create new account'], exact=True):
                        if self.dong_goi_y_google(max_thu=4):
                            thoi_diem_quet_lop_phu = time.time()
                            continue
                        self.log('🔵 [Nhận diện] Màn hình Đăng nhập -> Bấm "Tạo tài khoản mới"...')
                        self._snap_click(snap, ['Tạo tài khoản mới', 'Create new account'], exact=True, click_duoi=True)
                        self._cho_chuyen_man_hinh(snap['sig'], timeout=3.0)
                        _chot_buoc('LOGIN_CREATE', snap['sig'])
                        continue

                    # Phục hồi tại chỗ khi gặp màn hình lạ (KHÔNG tắt Wi-Fi / KHÔNG thoát FB!)
                    thoi_gian_cho_la = time.time() - thoi_diem_buoc_cuoi
                    if thoi_gian_cho_la > 10.0 and so_lan_phuc_hoi_man_la < 3:
                        so_lan_phuc_hoi_man_la += 1
                        self.log(
                            f'🔎 [Màn lạ sau bước {buoc_cuoi or "MỞ APP"} - Thử phục hồi {so_lan_phuc_hoi_man_la}/3] '
                            f'Đang thấy: {self._tom_tat_man_hinh(snap)}'
                        )
                        self._ha_ban_phim_an_toan()
                        self.dong_goi_y_google(max_thu=2)
                        if self._snap_click(snap, ['Thử lại', 'Try again', 'OK', 'Đóng', 'Close'], exact=True):
                            self._cho_chuyen_man_hinh(snap['sig'], timeout=3.0)
                        elif so_lan_phuc_hoi_man_la >= 2 and not snap.get('edit_texts'):
                            try:
                                self.d.press('back')
                            except Exception:
                                self.chay_shell_nhanh('input keyevent 4')
                            time.sleep(1.0)
                        thoi_diem_buoc_cuoi = time.time()
                        continue

                    if thoi_gian_cho_la > 45.0:
                        self.log(f'⚠️ Quá 45s màn hình không chuyển tiếp sau bước [{buoc_cuoi or "MỞ APP"}] ({self._tom_tat_man_hinh(snap)}) -> Hủy lượt!')
                        return None

                    time.sleep(0.32)
                except (AccountDieError, KeyboardInterrupt):
                    raise
                except Exception as step_err:
                    self.log(f'⚠️ [Phục hồi tại chỗ sau {buoc_cuoi or "MỞ APP"}] Lỗi tạm thời ({str(step_err)[:45]}) -> Đọc lại màn hình làm tiếp...')
                    time.sleep(0.8)
                    if self._consecutive_dump_errors >= 2:
                        self._phuc_hoi_u2_nhe()

            if not da_nhap_otp:
                self.log('❌ Hết thời gian chờ mà chưa tới bước nhập OTP!')
                return None

            # Đợi động sau khi gửi OTP: chờ hết trắng / hết màn hình OTP / bỏ qua bảng Lưu thông tin đăng nhập
            self.log('⏳ Đợi xác minh OTP & nhận diện màn hình tiếp theo...')
            moc_sau_otp = time.time() + 35.0
            while time.time() < moc_sau_otp and not STOP_EVENT.is_set():
                snap_post = self.cho_man_hinh_san_sang(timeout=20.0, ngu_canh='Sau khi gửi OTP')
                if self._snap_has(snap_post, ['Nhập mã xác nhận', 'Nhập mã gồm', 'Confirmation code']) and snap_post['edit_texts']:
                    time.sleep(0.45)
                    continue
                if self.bo_qua_luu_thong_tin_dang_nhap(snap=snap_post):
                    continue
                break

            self.kiem_tra_va_dung_neu_die('Xác nhận tài khoản sống sau OTP')
            self.log(f'🎉 XÁC MINH OTP THÀNH CÔNG ({tai_khoan_lien_he} | {ten_fb}) -> Tiến hành Thêm ảnh đại diện & Bật 2FA...')

            self.up_avatar_fb(preloaded_remote_paths=preloaded_avatar_paths)
            snap_sau_avt = self.cho_man_hinh_san_sang(timeout=10.0, ngu_canh='Sau Up Avatar')
            self.bo_qua_luu_thong_tin_dang_nhap(snap=snap_sau_avt)
            self.quet_va_xoa_man_hinh_chan(so_vong_quet=2)

            # Xử lý màn hình trung gian chỉ có nút "Tiếp" / "Next" đứng một mình sau khi xong Avatar
            for _ in range(2):
                snap_mid = self.quet_snapshot()
                if snap_mid['is_blank_or_loading']:
                    snap_mid = self.cho_man_hinh_san_sang(timeout=8.0, ngu_canh='Sau Avatar - Kiểm tra Tiếp')
                if not snap_mid['edit_texts'] and self._snap_has(snap_mid, ['Tiếp', 'Next'], exact=True):
                    self.log('⏩ Phát hiện nút "Tiếp" đứng một mình sau bước Avatar -> Bấm "Tiếp"...')
                    self._snap_click(snap_mid, ['Tiếp', 'Next'], exact=True)
                    self._cho_chuyen_man_hinh(snap_mid['sig'], timeout=2.2)
                    self.quet_va_xoa_man_hinh_chan(so_vong_quet=2)
                else:
                    break

            two_fa_key = self.bat_2fa_fb(
                used_email=tai_khoan_lien_he,
                ten_fb=ten_fb,
                mode=mode,
                mail_service=mail_service,
                imap_service=imap_service,
                hotmail_service=hotmail_service,
                autosms_service=autosms_service,
                mat_khau_fb=mat_khau_fb
            )

            self.kiem_tra_va_dung_neu_die('Kiểm tra cuối sau khi bật 2FA')

            # LẤY UID KHÔNG CẦN ROOT (ngay sau bước 2FA) -> IN, LƯU FILE & GỬI TELE NGAY LẬP TỨC (dù có lấy được UID hay không!)
            uid_fb = ""
            try:
                uid_fb = self.lay_uid_fb(req_proxy=self.req_proxy, ten_fb=ten_fb)
            except (AccountDieError, KeyboardInterrupt):
                raise
            except Exception as err_uid_call:
                self.log(f'⚠️ Lỗi lấy UID ({str(err_uid_call)[:35]}) -> Vẫn in & lưu ngay định dạng tài khoản!')

            in_luu_va_gui_tele_tai_khoan_ngay(
                email_or_phone=tai_khoan_lien_he,
                ten_fb=ten_fb,
                password=mat_khau_fb,
                two_fa=two_fa_key,
                uid=uid_fb,
                device_name=self.device_name
            )

            if self.user_id > 0:
                self.log(f'🧹 Đang chạy trên User phụ CleanFB (ID {self.user_id}) -> Bỏ qua Đăng xuất UI (đã in & lưu nick, chuẩn bị xóa sạch User)...')
            else:
                self.log('🧹 [Bên ngoài - User 0] Đã in & lưu nick -> Tiến hành Đăng xuất -> Gỡ BẰNG HẾT trang FB -> Xóa tab FB -> Xóa dữ liệu -> Tắt bật 4G...')
                self.dang_xuat_va_go_trang_ca_nhan(
                    thoat_tab_truoc=False,
                    xoa_data_truoc=False,
                    xoa_data_dong_tab_cuoi=True,
                    mo_lai_fb_cuoi=False,
                    tat_bat_4g_cuoi=True
                )

            if preloaded_avatar_paths and self.user_id == 0:
                self.xoa_anh_tam_tren_dt(preloaded_avatar_paths)

            da_don_sach_luot = True
            return (uid_fb, tai_khoan_lien_he, ten_fb, mat_khau_fb, two_fa_key)

        except AccountDieError as die_err:
            luu_tai_khoan_die(tai_khoan_lien_he or used_email, ten_fb, mat_khau_fb, str(die_err))
            if self.user_id > 0:
                self.log(f'💀 ACC DIE ({str(die_err)[:35]}) -> Dừng lượt & xóa User CleanFB!')
            else:
                self.log(f'💀 ACC DIE ({str(die_err)[:35]}) -> Dừng lượt -> Xóa tab FB -> Xóa tất cả dữ liệu -> Tắt bật 4G!')
                self.xoa_du_lieu_dong_tab_va_mo_lai_fb_sach(
                    mo_lai_fb=False,
                    tat_bat_4g=True,
                    bo_qua_cooldown_4g=True,
                    kiem_tra_go_het_truoc=False
                )
                if preloaded_avatar_paths:
                    self.xoa_anh_tam_tren_dt(preloaded_avatar_paths)
            da_don_sach_luot = True
            return None
        except KeyboardInterrupt:
            bi_ngat_thu_cong = True
            raise
        finally:
            for _im_extra in imap_moi_tao_trong_ham:
                try:
                    _im_extra.close()
                except Exception:
                    pass
            if not da_don_sach_luot and not bi_ngat_thu_cong and not STOP_EVENT.is_set():
                _don_sach_khi_that_bai('Đăng ký thất bại')


def khoi_tao_dich_vu_theo_mode(mode, data_source, manual_password, base_gmail, app_password, api_mode, req_proxy, autosms_api_key, autosms_country):
    used_email = ""
    mail_service = None
    imap_service = None
    hotmail_service = None
    autosms_service = None

    if mode == "1":
        for lan_thu in range(5):
            if STOP_EVENT.is_set():
                return None, None, None, None, None
            mail_service = MailService(proxy=req_proxy)
            random_user = f"fb_{uuid.uuid4().hex[:8]}{random.randint(10, 99)}"
            used_email = mail_service.create_account(random_user)
            if used_email and mail_service.authenticate():
                break
            used_email = None
            print(f"{vang}⚠️ Lỗi tạo/xác thực Mail.tm (lần {lan_thu + 1}/5), thử lại sau 3s...{trang}")
            time.sleep(3)
        if not used_email:
            return None, None, None, None, None

    elif mode == "2":
        tap_da_dung = lay_tap_email_da_dung()
        with DATA_LOCK:
            while len(data_source) > 0:
                cand = data_source.pop(0).strip().lstrip('\ufeff')
                em_k = chuan_hoa_email_key(cand)
                if em_k and em_k in tap_da_dung:
                    continue
                used_email = cand
                break
        if not used_email:
            return None, None, None, None, None
        danh_dau_email_da_dung(used_email)
        if "mail.tm" in used_email.lower():
            mail_service = MailService(proxy=req_proxy)
            pass_to_use = manual_password if manual_password else "TempPass123!"
            mail_service.authenticate(used_email, pass_to_use)

    elif mode == "3":
        tap_da_dung = lay_tap_email_da_dung()
        app_pass = ""
        with DATA_LOCK:
            while len(data_source) > 0:
                cand_em, cand_pass = data_source.pop(0)
                cand_em = cand_em.strip().lstrip('\ufeff')
                em_k = chuan_hoa_email_key(cand_em)
                if em_k and em_k in tap_da_dung:
                    continue
                used_email, app_pass = cand_em, cand_pass.strip()
                break
        if not used_email:
            return None, None, None, None, None
        danh_dau_email_da_dung(used_email)
        imap_service = GmailIMAPService(used_email, app_pass)

    elif mode == "4":
        tap_da_dung = lay_tap_email_da_dung()
        with DATA_LOCK:
            while len(data_source) > 0:
                cand = data_source.pop(0).strip().lstrip('\ufeff')
                em_k = chuan_hoa_email_key(cand)
                if em_k and em_k in tap_da_dung:
                    continue
                used_email = cand
                break
        if not used_email:
            return None, None, None, None, None
        danh_dau_email_da_dung(used_email)
        imap_service = GmailIMAPService(base_gmail, app_password)

    elif mode == "5":
        tap_da_dung = lay_tap_email_da_dung()
        data_line = ""
        with DATA_LOCK:
            while len(data_source) > 0:
                cand_line = data_source.pop(0).strip().lstrip('\ufeff')
                em_k = chuan_hoa_email_key(cand_line)
                if not cand_line or (em_k and em_k in tap_da_dung):
                    continue
                data_line = cand_line
                break
        if not data_line:
            return None, None, None, None, None
        used_email = data_line.split('|', 1)[0].strip().lstrip('\ufeff')
        danh_dau_email_da_dung(used_email)
        hotmail_service = HotmailAPIService(data_line, api_mode, proxy=req_proxy)

    elif mode == "6":
        autosms_service = AutoSMSService(autosms_api_key, autosms_country, proxy=req_proxy, service="facebook")
        used_email = "AUTOSMS_MODE_6"

    return used_email, mail_service, imap_service, hotmail_service, autosms_service


def chay_mot_thiet_bi_loop(
    serial, device_name, config, mode, data_source,
    manual_password=None, base_gmail=None, app_password=None,
    api_mode=None, avatar_folder="", proxies_list=None,
    autosms_api_key=None, autosms_country="vn", device_idx=0,
    proxy_mode="1", shared_rotator=None, fb_apk_path=DEFAULT_FB_APK_FILE
):
    used_names = set()
    used_phones = set()
    raw_line = None
    if proxies_list:
        raw_line = proxies_list[0] if proxy_mode == "2" else proxies_list[device_idx % len(proxies_list)]
    proxy_str, own_rotate_url = tach_proxy_va_link(raw_line)
    req_proxy = format_proxy(proxy_str) if proxy_str else None
    dung_user_phu = config.get('dung_user_phu_cleanfb', False)

    # Gắn cầu nối Proxy ADB 1 LẦN DUY NHẤT trước vòng lặp
    if proxy_str and config.get('dung_proxy_adb', True):
        gan_proxy_adb(serial, proxy_str, device_idx, device_name, xoay_ip=False)

    if proxy_mode == "2" and shared_rotator:
        shared_rotator.register(device_name)

    d_conn = None
    try:
        while not stop_flag.is_set():
            current_user_id = 0
            imap_service = None
            try:
                used_email, mail_service, imap_service, hotmail_service, autosms_service = khoi_tao_dich_vu_theo_mode(
                    mode, data_source, manual_password, base_gmail, app_password, api_mode, req_proxy, autosms_api_key, autosms_country
                )
                if not used_email:
                    update_step(device_name, '⚠️ Đã hết dữ liệu đầu vào! Dừng luồng máy này...')
                    break

                # ĐẦU VÒNG LẶP (TRƯỚC KHI MỞ APP): Tạo User phụ CleanFB mới + cài FB (Ưu tiên máy chính -> dự phòng APK)
                if dung_user_phu:
                    current_user_id = tao_va_cai_user_cleanfb(serial, fb_apk_path, device_name=device_name)
                    d_conn = ket_noi_lai_u2(serial)
                elif d_conn is None:
                    d_conn = ket_noi_lai_u2(serial)

                # Chế độ 1 (Proxy riêng): mỗi máy tự gọi link xoay riêng trước lượt mới
                if proxy_mode == "1" and own_rotate_url:
                    goi_link_xoay_proxy(own_rotate_url, device_name)

                fb_ui = FacebookUI(
                    serial, device_name, config,
                    avatar_folder=avatar_folder,
                    d_instance=d_conn,
                    user_id=current_user_id,
                    req_proxy=req_proxy
                )
                nhan_user = f'User ảo {current_user_id}' if current_user_id > 0 else 'Bên ngoài - User 0'
                if mode != "6":
                    update_step(device_name, f'📧 [{nhan_user}] Dùng: {used_email[:25]}')
                else:
                    update_step(device_name, f'📱 [{nhan_user}] Đang chạy Mode 6 (AutoSMS)...')

                _refill_email_multi = lambda: khoi_tao_dich_vu_theo_mode(
                    mode, data_source, manual_password, base_gmail, app_password,
                    api_mode, req_proxy, autosms_api_key, autosms_country
                )
                ket_qua = fb_ui.chay_dang_ky(
                    used_email=used_email,
                    mode=mode,
                    mail_service=mail_service,
                    imap_service=imap_service,
                    hotmail_service=hotmail_service,
                    autosms_service=autosms_service,
                    used_phones=used_phones,
                    used_names=used_names,
                    refill_email_fn=_refill_email_multi
                )

                if ket_qua:
                    uid_fb, email_or_phone, ten_fb, mat_khau_fb, two_fa_key = ket_qua
                    uid_display = uid_fb if uid_fb else (email_or_phone or 'NO_UID')
                    # Đã in, lưu file và gửi Telegram ngay sau bước lấy UID trong chay_dang_ky()
                    update_step(device_name, f'✅ HOÀN TẤT LƯỢT: {uid_display} | {mat_khau_fb} | {two_fa_key if two_fa_key else "NO_2FA"}')
                else:
                    update_step(device_name, '❌ ĐĂNG KÝ THẤT BẠI')

            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                d_conn = None
                update_step(device_name, f'❌ Lỗi: {str(e)[:45]}')
            finally:
                if imap_service:
                    try:
                        imap_service.close()
                    except Exception:
                        pass
                # NGAY KHI TẠO XONG 1 TÀI KHOẢN (HOẶC LỖI): Quay về User 0 & xóa sạch User CleanFB
                if dung_user_phu and current_user_id > 0:
                    don_sach_user_cleanfb(serial, device_name=device_name)
                    d_conn = None

            if not stop_flag.is_set():
                if proxy_mode == "2" and shared_rotator:
                    shared_rotator.wait_for_next_round(device_name)
                else:
                    nghi_ngau_nhien(config['delay_giua_cac_lan_chay'])
    finally:
        if dung_user_phu:
            try:
                don_sach_user_cleanfb(serial, device_name=device_name)
            except Exception:
                pass
        if proxy_mode == "2" and shared_rotator:
            shared_rotator.unregister(device_name)


def main():
    global multi_mode, FB_ACCOUNT_FILE
    os.makedirs(DEFAULT_AVATAR_DIR, exist_ok=True)
    print('\n──────────────────────────────────────────────────────────────────────')
    print(f'{trang}🤖 𝗧𝗢𝗢𝗟 𝗖𝗥𝗘𝗔𝗧𝗘 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗙𝗔𝗖𝗘𝗕𝗢𝗢𝗞 𝗔𝗗𝗕 (𝗡𝗘𝗪 𝗨𝗜 + 𝗔𝗨𝗧𝗢 𝟮𝗙𝗔 𝗧𝗢𝗧𝗣){trang}')
    print(f'{xanh_duong}📂 Thư mục chứa Tool : {BASE_DIR}{trang}')
    print(f'{xanh}📝 File lưu TK | MK  : {FB_ACCOUNT_FILE} (UID | MK | 2FA){trang}')
    print('──────────────────────────────────────────────────────────────────────')

    if os.path.exists(CONFIG_FILE):
        chon_config = input('Chọn cấu hình Delay: [a = Chuẩn Anti-Checkpoint + Đổi IP 4G (Khuyên dùng) / y = Giữ file cũ / n = Tự chỉnh] (Enter=a): ').strip().lower()
        if chon_config == 'y':
            config = doc_config()
            print('✅ Đã tải cấu hình cũ!')
        elif chon_config == 'n':
            config = cau_hinh_delay()
        else:
            config = ap_dung_config_chong_checkpoint()
            print('✅ Đã nạp cấu hình Chuẩn Anti-Checkpoint + Tự động đổi IP 4G & Android ID!')
    else:
        config = ap_dung_config_chong_checkpoint()
        print('✅ Đã khởi tạo cấu hình Chuẩn Anti-Checkpoint + Tự động đổi IP 4G & Android ID!')

    while True:
        token_tele, id_tele = doc_tele()
        trang_thai_ip = f"{xanh}✔ Bật{trang}" if (config.get('tat_bat_4g_khi_xoa_du_lieu', True) or config.get('doi_ip_may_bay', False)) else f"{do}✘ Tắt{trang}"
        trang_thai_user = f"{vang}User ảo CleanFB{trang}" if config.get('dung_user_phu_cleanfb', False) else f"{xanh}Bên ngoài (User 0){trang}"
        print('\n──────────────────────────────────────────────────────────────────────')
        print(f'{trang}📋  MENU CHÍNH')
        print('──────────────────────────────────────────────────────────────────────')
        print(f'{xanh}1. Chạy Reg FB BÊN NGOÀI Máy Chính (User 0 - Không gọi User ảo){trang}')
        print('2. Chạy Reg FB Trên User Ảo CleanFB (Tạo & Xóa User Phụ)')
        print(f"3. Gửi Về Tele    │ {(f'{xanh}✔{trang} Đã cấu hình' if token_tele and id_tele else f'{do}✘{trang} Chưa cấu hình')}")
        trang_thai_xoa = f"{xanh}NỔI (Mọi máy){trang}" if config.get('xoa_du_lieu_noi', True) else f"{vang}Ngầm ADB{trang}"
        trang_thai_af = f"{xanh}✔ Sạch{trang}" if config.get('xoa_tu_dong_dien_va_khoa_truy_cap', True) else f"{do}✘ Tắt{trang}"
        print(f"4. Cấu Hình Delay │ {trang_thai_user} • Xóa DL: {trang_thai_xoa} • Autofill/Passkey: {trang_thai_af} • 4G: {trang_thai_ip} • MK: {vang}{config.get('mat_khau_fb', '')}{trang}")
        print('5. Công Cụ Đổi Chuỗi Ký Tự 2FA -> Mã OTP 6 Số (Lấy mã nhanh)')
        print('──────────────────────────────────────────────────────────────────────')

        chon = input('Chọn chức năng (1, 2, 3, 4 hoặc 5): ').strip()

        if chon == '1':
            config['dung_user_phu_cleanfb'] = False
            luu_config(config)
            print(f'{xanh}✅ Đã chọn chế độ: TẠO TÀI KHOẢN BÊN NGOÀI MÁY CHÍNH (Không gọi User ảo)!{trang}')
            break

        elif chon == '2':
            config['dung_user_phu_cleanfb'] = True
            luu_config(config)
            print(f'{vang}✅ Đã chọn chế độ: CHẠY TRÊN USER ẢO CLEANFB!{trang}')
            break

        elif chon == '5':
            print('\n──────────────────────────────────────────────────────────────────────')
            print('🔢 CHUYỂN ĐỔI KÝ TỰ SECRET KEY 2FA SANG MÃ OTP 6 SỐ')
            print('──────────────────────────────────────────────────────────────────────')
            raw_2fa = input('Nhập chuỗi 2FA (VD: ABCD EFGH IJKL...): ').strip()
            otp_6 = chuyen_doi_2fa_sang_otp(raw_2fa, doi_chu_ky_moi=False)
            if otp_6:
                con_lai = 30 - (int(time.time()) % 30)
                print(f'✅ Key sạch : {lam_sach_key_2fa(raw_2fa)}')
                print(f'🔢 Mã OTP   : {xanh}{otp_6}{trang} (Còn hiệu lực: {con_lai} giây)')
            else:
                print(f'{do}❌ Chuỗi 2FA không hợp lệ!{trang}')
            input('\nNhấn Enter để quay lại Menu chính...')
            continue

        elif chon == '3':
            print('\n──────────────────────────────────────────────────────────────────────')
            print('📧 CẤU HÌNH TELEGRAM')
            print('──────────────────────────────────────────────────────────────────────')
            token_tele, id_tele = doc_tele()
            if token_tele and id_tele:
                print(f'🔑 Token hiện tại: {token_tele}')
                print(f'🆔 ID hiện tại: {id_tele}')
                print('\n1. Dùng Lại Token Và ID Cũ')
                print('2. Cấu Hình Lại')
                print('3. Hủy Cấu Hình')
                chon_tele = input('Chọn: ').strip()
                if chon_tele == '2':
                    token_tele_moi = input('Nhập Token mới: ').strip()
                    id_tele_moi = input('Nhập ID Acc Tele Của Bạn: ').strip()
                    if token_tele_moi and id_tele_moi:
                        luu_tele(token_tele_moi, id_tele_moi)
                        print('✅ Đã cập nhật cấu hình Telegram!')
                elif chon_tele == '3' and os.path.exists(TELE_FILE):
                    os.remove(TELE_FILE)
                    print('🗑️ Đã xóa cấu hình Telegram!')
            else:
                token_tele_moi = input('Nhập Token: ').strip()
                id_tele_moi = input('Nhập ID Acc Tele Của Bạn: ').strip()
                if token_tele_moi and id_tele_moi:
                    luu_tele(token_tele_moi, id_tele_moi)
                    print('✅ Đã lưu cấu hình Telegram!')
            input('\nNhấn Enter để quay lại Menu chính...')
            continue

        elif chon == '4':
            config = cau_hinh_delay()
            input('\nNhấn Enter để quay lại Menu chính...')
            continue

        else:
            print('❌ Lựa chọn không hợp lệ!')

    # Xác nhận nhanh mật khẩu FB sẽ đặt cho các nick (tránh chạy nhầm mật khẩu mặc định cũ)
    mk_hien_tai = config.get('mat_khau_fb', '@Letien09')
    nhap_mk_nhanh = input(f"{Colors.KEY}🔑 Mật khẩu FB muốn đặt cho các nick (Enter giữ '{mk_hien_tai}'): {Colors.RESET}").strip()
    if nhap_mk_nhanh:
        config['mat_khau_fb'] = nhap_mk_nhanh
        luu_config(config)
    print(f"{xanh}✅ Chốt mật khẩu FB sẽ nhập: {vang}{config['mat_khau_fb']}{trang}")

    print('\n──────────────────────────────────────────────────────────────────────')
    print(f'{trang}🔥 CHỌN CHẾ ĐỘ XÁC MINH (6 MODES)')
    print('──────────────────────────────────────────────────────────────────────')
    config_data = load_config()
    mode = select_mode(default_mode=config_data.get("last_mode"))
    config_data["last_mode"] = mode
    save_config(config_data)

    data_source = []
    base_gmail = None
    app_password = None
    manual_password = None
    api_mode = None
    autosms_api_key = None
    autosms_country = "vn"

    if mode == "2":
        prompt_txt = f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}"
        data_source = process_file_input("last_file_mode2", prompt_txt)
        config_data = load_config()
        if any("mail.tm" in e.lower() for e in data_source):
            saved_mtm_pass = config_data.get("last_mailtm_password", "")
            hint_mtm = f"Enter giữ '{saved_mtm_pass}'" if saved_mtm_pass else "Để trống dùng TempPass123!"
            built_in_print(f"{Colors.KEY}Nhập mật khẩu chung cho Mail.tm ({hint_mtm}): {Colors.RESET}", end="")
            nhap_mtm = input().strip()
            manual_password = nhap_mtm if nhap_mtm else saved_mtm_pass
            if manual_password:
                config_data["last_mailtm_password"] = manual_password
                save_config(config_data)

    elif mode == "3":
        prompt_txt = f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}"
        raw_list = process_file_input("last_file_mode3", prompt_txt)
        config_data = load_config()
        for line in raw_list:
            parts = re.split(r'[|:]', line.strip())
            if len(parts) >= 2:
                data_source.append((parts[0].strip(), parts[1].strip()))
        if not data_source:
            built_in_print(f"{Colors.ERROR}Danh sách Gmail IMAP không hợp lệ!{Colors.RESET}")
            input('Nhấn Enter để thoát...')
            sys.exit()

    elif mode == "4":
        saved_gmail = config_data.get("last_base_gmail", "")
        saved_app_pass = config_data.get("last_app_password", "")
        if saved_gmail:
            built_in_print(f"{Colors.INFO}Phát hiện Gmail gốc đã lưu: {Colors.VALUE}{saved_gmail}{Colors.RESET}")
            built_in_print(f"{Colors.KEY}Nhập Gmail gốc mới (Enter để dùng lại '{saved_gmail}'): {Colors.RESET}", end="")
        else:
            built_in_print(f"{Colors.KEY}Nhập Gmail gốc (VD: test@gmail.com): {Colors.RESET}", end="")
        nhap_gmail = input().strip()
        base_gmail = nhap_gmail if nhap_gmail else saved_gmail

        if saved_app_pass:
            an_pass = saved_app_pass[:4] + "****" + saved_app_pass[-2:] if len(saved_app_pass) > 6 else "****"
            built_in_print(f"{Colors.KEY}Nhập App Password mới (Enter để dùng lại '{an_pass}'): {Colors.RESET}", end="")
        else:
            built_in_print(f"{Colors.KEY}Nhập App Password: {Colors.RESET}", end="")
        nhap_app_pass = input().strip()
        app_password = nhap_app_pass if nhap_app_pass else saved_app_pass

        if base_gmail:
            config_data["last_base_gmail"] = base_gmail
        if app_password:
            config_data["last_app_password"] = app_password
        save_config(config_data)
        all_dot_vars = generate_dot_variants(base_gmail)
        tap_da_dung_m4 = lay_tap_email_da_dung()
        data_source = [e for e in all_dot_vars if chuan_hoa_email_key(e) not in tap_da_dung_m4]
        if len(data_source) < len(all_dot_vars):
            built_in_print(
                f"{Colors.WARNING}📌 [Mode 4] Đã tự bỏ qua {len(all_dot_vars) - len(data_source)} biến thể Gmail từng dùng "
                f"-> Còn {len(data_source)} email mới!{Colors.RESET}"
            )

    elif mode == "5":
        saved_hm_mode = config_data.get("last_hotmail_api_mode", "")
        mode_map = {"1": "oauth", "2": "graph", "3": "roundcube"}
        rev_map = {"oauth": "1", "graph": "2", "roundcube": "3"}
        hint_hm = f" (Enter dùng lại [{rev_map[saved_hm_mode]} - {saved_hm_mode}])" if saved_hm_mode in rev_map else ""
        built_in_print(f"1. OAuth | 2. Graph API | 3. Roundcube{hint_hm}\n>> ", end="")
        c = input().strip()
        if not c and saved_hm_mode in rev_map:
            api_mode = saved_hm_mode
        else:
            api_mode = mode_map.get(c, "roundcube")
        config_data["last_hotmail_api_mode"] = api_mode
        save_config(config_data)
        prompt_txt = f"{Colors.KEY}Nhập đường dẫn file/list Hotmail: {Colors.RESET}"
        data_source = process_file_input("last_file_mode5", prompt_txt)
        config_data = load_config()

    elif mode == "6":
        saved_sms_key = config_data.get("autosms_api_key", "")
        saved_sms_country = config_data.get("autosms_country", "vn")

        if saved_sms_key:
            an_key = f"{saved_sms_key[:6]}...{saved_sms_key[-4:]}" if len(saved_sms_key) > 12 else saved_sms_key
            built_in_print(f"{Colors.INFO}🔑 Phát hiện API Key AutoSMS đã lưu: {Colors.VALUE}{an_key}{Colors.RESET}")
            built_in_print(f"{Colors.KEY}Nhấn Enter để dùng lại Key cũ (hoặc dán API Key mới để đổi): {Colors.RESET}", end="")
        else:
            built_in_print(f"{Colors.KEY}Nhập API Key của web Autosms.site: {Colors.RESET}", end="")
        nhap_sms_key = input().strip()
        autosms_api_key = nhap_sms_key if nhap_sms_key else saved_sms_key

        built_in_print(
            f"{Colors.KEY}Nhập Mã Quốc Gia thuê sim (VD: vn, us, kh - Enter giữ '{saved_sms_country}'): {Colors.RESET}",
            end=""
        )
        nhap_country = input().strip()
        autosms_country = nhap_country if nhap_country else saved_sms_country

        if autosms_api_key:
            config_data["autosms_api_key"] = autosms_api_key
        config_data["autosms_country"] = autosms_country
        save_config(config_data)
        built_in_print(f"{Colors.SUCCESS}=> Đã lưu cấu hình AutoSMS (Quốc gia: {autosms_country}) vào {CONFIG_GMAIL_FILE}{Colors.RESET}")
        data_source = ["dummy_for_sms"] * 999999

    if not data_source and mode not in ["1", "4", "6"]:
        built_in_print(f"{Colors.ERROR}Danh sách đầu vào trống! Thoát chương trình.{Colors.RESET}")
        input('Nhấn Enter để thoát...')
        sys.exit()

    saved_avatar_folder = config_data.get("last_avatar_folder", "")
    avatar_folder_input = ""

    built_in_print(f"\n{Colors.TITLE}📁 CẤU HÌNH THƯ MỤC ẢNH AVATAR TRÊN MÁY TÍNH:{Colors.RESET}")
    built_in_print(f"   • Tool đã tạo sẵn thư mục mặc định tại: {Colors.VALUE}{DEFAULT_AVATAR_DIR}{Colors.RESET}")
    built_in_print(f"   • Bạn chỉ cần copy các ảnh (.jpg, .png) trên máy tính bỏ vào thư mục đó (hoặc nhập đường dẫn thư mục bất kỳ trên PC).")

    if saved_avatar_folder and os.path.isdir(saved_avatar_folder):
        built_in_print(f"   • Phát hiện thư mục Avatar lần trước: {Colors.VALUE}{saved_avatar_folder}{Colors.RESET}")
        use_old_avatar = input(f"{Colors.KEY}Bạn có muốn dùng lại thư mục này không? (y/n, Enter=y): {Colors.RESET}").strip().lower()
        if use_old_avatar in ['', 'y']:
            avatar_folder_input = saved_avatar_folder

    if not avatar_folder_input:
        built_in_print(f"{Colors.KEY}Nhập đường dẫn thư mục chứa ảnh trên PC (Nhấn Enter để dùng thư mục '{DEFAULT_AVATAR_DIR}'): {Colors.RESET}", end="")
        nhap_folder = input().strip().strip('"').strip("'")
        if nhap_folder and not os.path.isabs(nhap_folder):
            nhap_folder = os.path.join(BASE_DIR, nhap_folder)
        avatar_folder_input = nhap_folder if nhap_folder else DEFAULT_AVATAR_DIR
        if os.path.isdir(avatar_folder_input):
            config_data["last_avatar_folder"] = avatar_folder_input
            save_config(config_data)

    so_anh_pc = 0
    if os.path.isdir(avatar_folder_input):
        so_anh_pc = len([f for f in os.listdir(avatar_folder_input) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
    built_in_print(f"{Colors.SUCCESS}=> Đang dùng thư mục PC: {avatar_folder_input} (Tìm thấy {so_anh_pc} ảnh){Colors.RESET}")

    saved_proxy_file = config_data.get("last_proxy_file", "")
    proxy_file_input = ""
    if saved_proxy_file and os.path.isfile(saved_proxy_file):
        built_in_print(f"\n{Colors.INFO}🌐 Phát hiện file Proxy đã lưu: {Colors.VALUE}{saved_proxy_file}{Colors.RESET}")
        nhap_proxy = input(
            f"{Colors.KEY}Nhấn Enter để dùng lại | nhập đường dẫn file Proxy mới | gõ 'off' để không dùng Proxy: {Colors.RESET}"
        ).strip().strip('"').strip("'")
        if nhap_proxy.lower() == 'off':
            proxy_file_input = ""
            config_data["last_proxy_file"] = ""
            save_config(config_data)
        elif not nhap_proxy:
            proxy_file_input = saved_proxy_file
        else:
            proxy_file_input = nhap_proxy
    else:
        built_in_print(f"\n{Colors.KEY}Nhập đường dẫn file Proxy (.txt) cho API Mail/SMS (Bỏ trống nếu không dùng): {Colors.RESET}", end="")
        proxy_file_input = input().strip().strip('"').strip("'")

    if proxy_file_input and not os.path.isabs(proxy_file_input):
        cand_proxy = os.path.join(BASE_DIR, proxy_file_input)
        if os.path.isfile(cand_proxy):
            proxy_file_input = cand_proxy

    proxies_list = []
    if proxy_file_input and os.path.isfile(proxy_file_input):
        config_data["last_proxy_file"] = proxy_file_input
        save_config(config_data)
        with open(proxy_file_input, 'r', encoding='utf-8') as f_proxy:
            proxies_list = [line.strip() for line in f_proxy if line.strip()]
        built_in_print(f"{Colors.SUCCESS}Đã tải {len(proxies_list)} Proxy từ tệp.{Colors.RESET}")

    saved_proxy_mode = config_data.get("last_proxy_mode", "2")
    saved_proxy_cd = int(config_data.get("last_proxy_cooldown", 65))
    proxy_mode = "1"  # 1 = Proxy riêng từng máy | 2 = Proxy chung xoay đồng bộ theo đợt
    shared_rotator = None
    if proxies_list:
        built_in_print(f"\n{Colors.TITLE}🌐 CHỌN CHẾ ĐỘ CHẠY PROXY XOAY:{Colors.RESET}")
        built_in_print("   1. Proxy RIÊNG (Mỗi máy 1 proxy + link xoay độc lập)")
        built_in_print("   2. Proxy CHUNG xoay đồng bộ (Chờ tất cả máy xong lượt rồi gọi API xoay 1 lần)")
        chon_pm = input(f"{Colors.KEY}Chọn chế độ Proxy [1/2] (Enter giữ '{saved_proxy_mode}'): {Colors.RESET}").strip()
        proxy_mode = chon_pm if chon_pm in ["1", "2"] else saved_proxy_mode
        config_data["last_proxy_mode"] = proxy_mode
        save_config(config_data)
        if proxy_mode == "2":
            first_proxy_str, rotate_url = tach_proxy_va_link(proxies_list[0])
            cooldown_in = input(
                f"{Colors.KEY}Thời gian tối thiểu giữa 2 lần xoay IP (giây, Enter giữ {saved_proxy_cd}): {Colors.RESET}"
            ).strip()
            min_cd = int(cooldown_in) if cooldown_in.isdigit() else saved_proxy_cd
            config_data["last_proxy_cooldown"] = min_cd
            save_config(config_data)
            shared_rotator = DynamicBatchRotator(
                proxy_str=first_proxy_str,
                rotate_url=rotate_url,
                stop_event=stop_flag,
                min_interval=min_cd,
                stabilize_delay=4,
                verify_timeout=35,
                max_rotate_retries=2,
            )

    # KIỂM TRA FILE facebook.apk DỰ PHÒNG CHO CHẾ ĐỘ USER PHỤ CLEANFB (TỰ ĐỘNG 2 TRONG 1)
    fb_apk_path = config.get('fb_apk_path') or DEFAULT_FB_APK_FILE
    if fb_apk_path and not os.path.isabs(fb_apk_path):
        fb_apk_path = os.path.join(BASE_DIR, fb_apk_path)

    if config.get('dung_user_phu_cleanfb', False):
        if os.path.isfile(fb_apk_path):
            built_in_print(f"\n{Colors.SUCCESS}⚡ [User CleanFB - 2 trong 1] Ưu tiên lấy FB từ máy chính (1s) | Dự phòng APK: {fb_apk_path}{Colors.RESET}")
        else:
            built_in_print(f"\n{Colors.INFO}⚡ [User CleanFB - 2 trong 1] Ưu tiên nhân bản FB sẵn trên máy chính (không cần file APK).{Colors.RESET}")
            built_in_print(f"   • File APK dự phòng (chỉ dùng cho máy chưa cài FB) chưa có tại: {fb_apk_path}")
            nhap_apk = input(f"{Colors.KEY}Nhấn Enter để chạy luôn bằng FB máy chính (hoặc kéo file facebook.apk vào / gõ 'off' để tắt User phụ): {Colors.RESET}").strip().strip('"').strip("'")
            if nhap_apk.lower() == 'off':
                config['dung_user_phu_cleanfb'] = False
                built_in_print(f"{Colors.WARNING}=> Đã tạm tắt chế độ User phụ CleanFB cho phiên chạy này.{Colors.RESET}")
            elif nhap_apk:
                cand_apk = nhap_apk if os.path.isabs(nhap_apk) else os.path.join(BASE_DIR, nhap_apk)
                if os.path.isfile(cand_apk):
                    fb_apk_path = cand_apk
                    config['fb_apk_path'] = fb_apk_path
                    luu_config(config)
                    built_in_print(f"{Colors.SUCCESS}=> Đã lưu file APK dự phòng: {fb_apk_path}{Colors.RESET}")
                else:
                    built_in_print(f"{Colors.WARNING}⚠️ Không tìm thấy '{cand_apk}', sẽ chạy bằng FB có sẵn trên máy chính.{Colors.RESET}")

    try:
        devices = get_devices()
        if not devices:
            print(f'{do}❌ Không tìm thấy thiết bị ADB nào!{trang}')
            return

        print(f'\n{xanh}📱 TÌM THẤY {len(devices)} THIẾT BỊ:{trang}')
        for i, (serial, name) in enumerate(devices, 1):
            print(f'   {i}. {serial}')

        if len(devices) > 1:
            print(f'\n{vang}🚀 PHÁT HIỆN NHIỀU THIẾT BỊ{trang}')
            chon_multi = input('Bạn có muốn chạy đồng thời tất cả? (y/n): ').strip().lower()
            if chon_multi == 'y':
                multi_mode = True
                device_steps.clear()
                device_last_step.clear()
                stop_flag.clear()
                print(f'\n{xanh}✅ ĐANG CHẠY ĐỒNG THỜI TRÊN {len(devices)} THIẾT BỊ...{trang}')
                threads = []
                for idx_dev, (serial, device_name) in enumerate(devices):
                    t = threading.Thread(
                        target=chay_mot_thiet_bi_loop,
                        args=(
                            serial, serial, config, mode, data_source, manual_password,
                            base_gmail, app_password, api_mode, avatar_folder_input,
                            proxies_list, autosms_api_key, autosms_country, idx_dev,
                            proxy_mode, shared_rotator, fb_apk_path
                        )
                    )
                    t.daemon = True
                    t.start()
                    threads.append(t)
                while any(t.is_alive() for t in threads):
                    time.sleep(1)
                print(f'\n{vang}🏁 Đã hoàn tất chạy trên tất cả thiết bị!{trang}')
                return
            else:
                multi_mode = False
                chon_device = input(f'Chọn thiết bị (1-{len(devices)}): ').strip()
                try:
                    serial, device_name = devices[int(chon_device) - 1]
                except Exception:
                    serial, device_name = devices[0]
        else:
            multi_mode = False
            serial, device_name = devices[0]

        used_names = set()
        used_phones = set()
        lan_chay = 0
        raw_single_proxy = proxies_list[0] if proxies_list else None
        single_proxy_str, single_rotate_url = tach_proxy_va_link(raw_single_proxy)
        req_proxy = format_proxy(single_proxy_str) if single_proxy_str else None

        # Gắn cầu nối Proxy ADB 1 LẦN DUY NHẤT trước vòng lặp 1 thiết bị
        if single_proxy_str and config.get('dung_proxy_adb', True):
            gan_proxy_adb(serial, single_proxy_str, 0, device_name, xoay_ip=False)

        d_conn_single = None
        dung_user_phu_single = config.get('dung_user_phu_cleanfb', False)

        while not stop_flag.is_set():
            current_user_id = 0
            imap_service = None
            loop_co_loi = False
            try:
                used_email, mail_service, imap_service, hotmail_service, autosms_service = khoi_tao_dich_vu_theo_mode(
                    mode, data_source, manual_password, base_gmail, app_password, api_mode, req_proxy, autosms_api_key, autosms_country
                )
                if not used_email:
                    print(f'\n{vang}⚠️ Đã hết dữ liệu đầu vào hoặc lỗi tạo mail! Dừng chương trình.{trang}')
                    break

                lan_chay += 1
                print('\n──────────────────────────────────────────────────────────────────────')
                print(f'🔄 LẦN CHẠY THỨ {lan_chay} (MODE {mode})')
                print('──────────────────────────────────────────────────────────────────────')

                # ĐẦU VÒNG LẶP (TRƯỚC KHI MỞ APP): Tạo User phụ CleanFB mới + cài FB (Ưu tiên máy chính -> dự phòng APK)
                if dung_user_phu_single:
                    current_user_id = tao_va_cai_user_cleanfb(serial, fb_apk_path, device_name=device_name)
                    d_conn_single = ket_noi_lai_u2(serial)
                elif d_conn_single is None:
                    d_conn_single = ket_noi_lai_u2(serial)

                # Xoay IP đầu lượt nếu có link xoay
                if single_rotate_url:
                    if proxy_mode == "2" and shared_rotator and lan_chay > 1:
                        shared_rotator._call_rotate_and_verify(device_name)
                    else:
                        goi_link_xoay_proxy(single_rotate_url, device_name)
                        if shared_rotator:
                            shared_rotator.last_rotate_time = time.time()

                fb_ui = FacebookUI(
                    serial, device_name, config,
                    avatar_folder=avatar_folder_input,
                    d_instance=d_conn_single,
                    user_id=current_user_id,
                    req_proxy=req_proxy
                )

                nhan_user_single = f'User ảo {current_user_id}' if current_user_id > 0 else 'Bên ngoài - User 0'
                if mode != "6":
                    print(f'📧 [{nhan_user_single}] Đang sử dụng Email: {used_email}')
                else:
                    print(f'📱 [{nhan_user_single}] Đang sử dụng Chế độ 6 (Thuê SĐT AutoSMS.site)')

                _refill_email_single = lambda: khoi_tao_dich_vu_theo_mode(
                    mode, data_source, manual_password, base_gmail, app_password,
                    api_mode, req_proxy, autosms_api_key, autosms_country
                )
                ket_qua_dang_ky = fb_ui.chay_dang_ky(
                    used_email=used_email,
                    mode=mode,
                    mail_service=mail_service,
                    imap_service=imap_service,
                    hotmail_service=hotmail_service,
                    autosms_service=autosms_service,
                    used_phones=used_phones,
                    used_names=used_names,
                    refill_email_fn=_refill_email_single
                )

                if ket_qua_dang_ky:
                    uid_fb, email_or_phone, ten_fb, mat_khau_fb, two_fa_key = ket_qua_dang_ky
                    uid_display = uid_fb if uid_fb else (email_or_phone or 'NO_UID')
                    # Đã in, lưu file và gửi Telegram ngay sau bước lấy UID trong chay_dang_ky()
                    print(f'{xanh}✅ Hoàn tất dọn dẹp lượt cho tài khoản: {uid_display} | {mat_khau_fb} | {two_fa_key if two_fa_key else "NO_2FA"}{trang}')
                else:
                    print('\n❌ Đăng ký thất bại!')

            except KeyboardInterrupt:
                raise
            except Exception as loop_err:
                loop_co_loi = True
                d_conn_single = None
                print(f'\n{do}❌ Lỗi trong vòng lặp chạy 1 thiết bị: {loop_err}{trang}')
                traceback.print_exc()
            finally:
                if imap_service:
                    try:
                        imap_service.close()
                    except Exception:
                        pass
                # NGAY KHI TẠO XONG 1 TÀI KHOẢN (HOẶC LỖI): Quay về User 0 & xóa sạch User CleanFB
                if dung_user_phu_single and current_user_id > 0:
                    don_sach_user_cleanfb(serial, device_name=device_name)
                    d_conn_single = None

            if not stop_flag.is_set():
                if loop_co_loi:
                    print(f"\n⏳ Tự phục hồi sau {config.get('delay_thu_lai_khi_loi', 5.0)} giây...")
                    nghi_ngau_nhien(config.get('delay_thu_lai_khi_loi', 5.0))
                else:
                    print(f"\n⏳ CHỜ {config['delay_giua_cac_lan_chay']} GIÂY...")
                    nghi_ngau_nhien(config['delay_giua_cac_lan_chay'])

    except KeyboardInterrupt:
        print(f'\n\n{do}🛑 ĐÃ DỪNG{trang}')
        stop_flag.set()
        if shared_rotator:
            shared_rotator.notify_stop()
    except Exception as e:
        print(f'{do}❌ Lỗi: {e}{trang}')
        traceback.print_exc()
    finally:
        stop_flag.set()
        if shared_rotator:
            try:
                shared_rotator.notify_stop()
            except Exception:
                pass
        try:
            ds_don_dep = get_devices()
            for idx_d, (ser_d, _) in enumerate(ds_don_dep):
                if config.get('dung_user_phu_cleanfb', False):
                    try:
                        don_sach_user_cleanfb(ser_d, device_name=ser_d)
                    except Exception:
                        pass
                go_proxy_adb(ser_d, idx_d)
            with ADB_PROXY_LOCK:
                for b in list(ADB_PROXY_BRIDGES.values()):
                    b.stop()
                ADB_PROXY_BRIDGES.clear()
            if config.get('dung_user_phu_cleanfb', False):
                print(f"{xanh}✅ Đã dọn sạch User CleanFB & gỡ Proxy khỏi toàn bộ thiết bị ADB.{trang}")
            else:
                print(f"{xanh}✅ Đã gỡ Proxy khỏi toàn bộ thiết bị ADB (Chế độ máy chính User 0).{trang}")
        except Exception:
            pass
        input('\nNhấn Enter để đóng cửa sổ...')


if __name__ == '__main__':
    main()
# ==================== KẾT THÚC PHẦN 2/2 ====================
