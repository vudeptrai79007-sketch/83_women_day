# --- SHIM CHO PYTHON 3.12+ (Khắc phục hoàn toàn lỗi thiếu distutils và .version) ---
import sys
import socket
import select
import base64
import io

# Tự động cấu hình mã hóa UTF-8 cho Windows Console tránh lỗi UnicodeEncodeError
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import types
import re
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

import os
import time
import threading
import random
from datetime import datetime
import uuid
import imaplib
import email
from email.header import decode_header
import json
import traceback
import string
import hashlib

# ===== THƯ VIỆN CHROME CHO PC & PYOTP =====
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.common.keys import Keys
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import pyotp
except ImportError:
    print("Đang cài đặt thư viện thiếu (undetected-chromedriver, requests, pyotp)...")
    os.system("pip install undetected-chromedriver selenium requests pyotp")
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.common.keys import Keys
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import pyotp

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

# --- HÀM LẤY ĐÚNG THƯ MỤC CHỨA FILE .EXE HOẶC FILE .PY ---
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_app_dir()
CONFIG_FILE = os.path.join(BASE_DIR, "config_gmail.json")
BASE_YEAR = random.randint(1995, 2005)

# Danh sách lưu toàn bộ Trình duyệt để hỏi đóng vào cuối cùng
ALL_DRIVERS = []

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

# ========== HÀM CƠ BẢN ==========
def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    built_in_print(f"""{Colors.PRIMARY}
 ██████╗ ██╗  ██╗██████╗  ██████╗ ███╗   ███╗███████╗
██╔════╝ ██║  ██║██╔══██╗██╔═══██╗████╗ ████║██╔════╝
██║  ███╗███████║██████╔╝██║   ██║██╔████╔██║█████╗  
██║   ██║██╔══██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══╝  
╚██████╔╝██║  ██║██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
{Colors.RESET}""")
    built_in_print(f"{Colors.INFO}Phiên Bản: v19.0 (Tích Hợp Thuê Mail OTPTRUST.COM + Fix Username & 2FA){Colors.RESET}")
    built_in_print(f"{Colors.LINE}{'─'*70}{Colors.RESET}\n")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception: pass
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
    except Exception: pass

def save_account(thread_id, email_str, password, username, full_name, mode="auto", cookie="", two_fa=""):
    current_dir = get_app_dir()
    file_tong = os.path.join(current_dir, "danh_sach_acc_ig.txt")
    folder_name = os.path.join(current_dir, "Instagram_reg_PC")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder_name, f"account_{thread_id}_{timestamp}.txt")
    dinh_dang_luu = f"{email_str}|{password}|{username}|{two_fa}|{cookie}\n"
    
    with DATA_LOCK:
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name, exist_ok=True)
                
            with open(file_tong, 'a', encoding='utf-8') as f: 
                f.write(dinh_dang_luu)
                
            content = f"Luồng: {thread_id}\nEmail: {email_str}\nPass: {password}\nUser: {username}\n2FA: {two_fa}\nCookie: {cookie}\n"
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(content)
                
            print(f"{Colors.color_text(f'[{thread_id}] Đã xuất tài khoản vào: {file_tong}', Colors.SUCCESS)}")
        except Exception as e: 
            print(f"Lỗi khi lưu file: {e}")

def VietnameseNameGenerator():
    first = random.choice(["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Vu", "Dang", "Bui", "Do"])
    middle = random.choice(["Van", "Thi", "Minh", "Hoang", "Anh", "Bao", "Gia", "Khanh", "Ngoc", "Phuong"])
    last = random.choice(["An", "Binh", "Cuong", "Dung", "Anh", "Bich", "Chi", "Diep", "Dung", "Hai", "Hung"])
    full_name = f"{first} {middle} {last}"
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', full_name.lower())
    
    extra_chars = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=2))
    username = f"{cleaned}{extra_chars}{random.randint(10000, 999999)}"
    
    return full_name, username

# >>> HÀM BÓC TÁCH MÃ OTP THÔNG MINH (HỖ TRỢ CẢ 6 SỐ VÀ 8 SỐ CHO ĐĂNG KÝ & 2FA) <<<
def extract_ig_otp_smart(subject, raw_body, target_email="", allow_8_digits=False):
    subj_str = str(subject or "")
    body_str = str(raw_body or "")

    if target_email:
        email_clean = str(target_email).strip().lower()
        local_part = email_clean.split('@')[0]
        subj_str = re.sub(re.escape(email_clean), ' ', subj_str, flags=re.IGNORECASE)
        body_str = re.sub(re.escape(email_clean), ' ', body_str, flags=re.IGNORECASE)
        if len(local_part) >= 3:
            subj_str = re.sub(re.escape(local_part), ' ', subj_str, flags=re.IGNORECASE)
            body_str = re.sub(re.escape(local_part), ' ', body_str, flags=re.IGNORECASE)

    if allow_8_digits:
        m_sub8 = re.search(r'(?<!\d)(\d{8})(?!\d)', subj_str)
        if m_sub8: return m_sub8.group(1)
    m_sub6 = re.search(r'(?<!\d)(\d{6})(?!\d)', subj_str)
    if m_sub6: return m_sub6.group(1)

    clean_body = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', body_str, flags=re.DOTALL | re.IGNORECASE)
    clean_body = re.sub(r'#[0-9a-fA-F]{6}\b', ' ', clean_body)
    clean_body = re.sub(r'<[^>]+>', ' ', clean_body)
    clean_body = clean_body.replace('&nbsp;', ' ').replace('&#160;', ' ')

    if allow_8_digits:
        m_body8 = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_body)
        if m_body8:
            return m_body8.group(1)
        m_body8_spaced = re.search(r'(?<!\d)(\d{4})[ \t-]+(\d{4})(?!\d)', clean_body)
        if m_body8_spaced:
            return m_body8_spaced.group(1) + m_body8_spaced.group(2)

    candidates_6 = re.findall(r'(?<!\d)(\d{6})(?!\d)', clean_body)
    for cand in candidates_6:
        if cand not in ["000000", "111111"]:
            return cand

    m_body6_spaced = re.search(r'(?<!\d)(\d{3})[ \t]+(\d{3})(?!\d)', clean_body)
    if m_body6_spaced:
        return m_body6_spaced.group(1) + m_body6_spaced.group(2)

    return None

# >>> HỆ THỐNG XỬ LÝ PROXY ĐA NĂNG <<<
def parse_proxy(proxy_str):
    if not proxy_str: return None
    p_str = str(proxy_str).strip()
    if not p_str: return None
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
        except Exception: pass

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
    if not parsed: return None
    if parsed["user"] and parsed["pass"]:
        formatted = f"http://{parsed['user']}:{parsed['pass']}@{parsed['ip']}:{parsed['port']}"
    else:
        formatted = f"http://{parsed['ip']}:{parsed['port']}"
    return {"http": formatted, "https": formatted}

class LocalProxyForwarder:
    def __init__(self, remote_ip, remote_port, username=None, password=None):
        self.remote_ip = remote_ip
        self.remote_port = int(remote_port)
        self.username = username
        self.password = password
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', 0))
        self.local_port = self.server_socket.getsockname()[1]
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.server_socket.listen(100)
        while self.running:
            try:
                client_sock, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except Exception: break

    def _handle_client(self, client_sock):
        try:
            crlf2 = bytes([13, 10, 13, 10])
            crlf = bytes([13, 10])
            req = b""
            while crlf2 not in req:
                chunk = client_sock.recv(4096)
                if not chunk:
                    client_sock.close()
                    return
                req += chunk

            header_part, rest = req.split(crlf2, 1)
            lines = header_part.split(crlf)
            first_line = lines[0].decode("utf-8", "ignore")
            is_connect = first_line.startswith("CONNECT")

            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(15)
            remote_sock.connect((self.remote_ip, self.remote_port))

            auth_header = b""
            if self.username and self.password:
                cred = f"{self.username}:{self.password}"
                b64_cred = base64.b64encode(cred.encode()).decode()
                auth_header = f"Proxy-Authorization: Basic {b64_cred}".encode() + crlf

            if is_connect:
                connect_req = lines[0] + crlf
                for line in lines[1:]:
                    if not line.lower().startswith(b"proxy-authorization"):
                        connect_req += line + crlf
                if auth_header:
                    connect_req += auth_header
                connect_req += crlf
                remote_sock.sendall(connect_req)

                resp = b""
                while crlf2 not in resp:
                    c = remote_sock.recv(4096)
                    if not c: break
                    resp += c

                resp_first_line = resp.split(crlf)[0] if resp else b""
                if b"200" in resp_first_line:
                    client_sock.sendall(b"HTTP/1.1 200 Connection established" + crlf2)
                else:
                    client_sock.sendall(resp)
                    client_sock.close()
                    remote_sock.close()
                    return
            else:
                new_req = lines[0] + crlf
                for line in lines[1:]:
                    if not line.lower().startswith(b"proxy-authorization"):
                        new_req += line + crlf
                if auth_header:
                    new_req += auth_header
                new_req += crlf + rest
                remote_sock.sendall(new_req)

            remote_sock.settimeout(None)
            client_sock.settimeout(None)
            sockets = [client_sock, remote_sock]
            while self.running:
                r, _, _ = select.select(sockets, [], sockets, 30)
                if not r: break
                for s in r:
                    other = remote_sock if s is client_sock else client_sock
                    data = s.recv(16384)
                    if not data: return
                    other.sendall(data)
        except Exception: pass
        finally:
            try: client_sock.close()
            except: pass
            try: remote_sock.close()
            except: pass

    def close(self):
        self.running = False
        try: self.server_socket.close()
        except: pass


# ==================== CÁC CLASS XỬ LÝ EMAIL ====================
class MailService:
    def __init__(self, proxy=None):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.domain = None
        self.email_address = None
        self.seen_msg_ids = set()
        self.seen_codes = set()
        self.proxy = proxy 
        
    def get_domain(self):
        try:
            r = requests.get(f"{self.base_url}/domains", timeout=10, proxies=self.proxy)
            if r.status_code == 200: 
                self.domain = r.json()['hydra:member'][0]['domain']
                return self.domain
        except Exception: return None
            
    def create_account(self, address=None):
        if not self.domain and not self.get_domain(): return None
        name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        time.sleep(random.uniform(0.5, 2.0))
        try:
            r = requests.post(f"{self.base_url}/accounts", json={"address": f"{name}@{self.domain}", "password": "TempPass123!"}, timeout=10, proxies=self.proxy)
            if r.status_code == 201: 
                self.email_address = r.json()['address']
                return self.email_address
        except Exception: return None
            
    def authenticate(self, email=None, password="TempPass123!"):
        if email: self.email_address = email
        time.sleep(random.uniform(0.5, 2.0)) 
        try:
            r = requests.post(f"{self.base_url}/token", json={"address": self.email_address, "password": password}, timeout=10, proxies=self.proxy)
            if r.status_code == 200: 
                self.token = r.json()['token']
                return True
        except Exception: return False
            
    def get_otp_code(self, timeout=120, force_8_digits=False):
        if not self.token: return None
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        start_time = time.time()
        time.sleep(random.uniform(1.0, 3.0))
        
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                r = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10, proxies=self.proxy)
                if r.status_code == 200:
                    for msg in r.json().get('hydra:member', []):
                        msg_id = msg.get('id')
                        if not msg_id or msg_id in self.seen_msg_ids:
                            continue
                            
                        subject = str(msg.get('subject', ''))
                        frm = str(msg.get('from', {}).get('address', '')).lower()
                        subj_low = subject.lower()
                        
                        if any(k in subj_low or k in frm for k in ['instagram', 'meta', 'facebook', 'security', 'code', 'mã', 'xác']):
                            detail = requests.get(f"{self.base_url}/messages/{msg_id}", headers=headers, timeout=10, proxies=self.proxy).json()
                            raw_text = detail.get('text', '') or str(detail.get('html', ''))
                            
                            code = extract_ig_otp_smart(
                                subject=subject,
                                raw_body=raw_text,
                                target_email=self.email_address,
                                allow_8_digits=force_8_digits
                            )

                            if code and code not in self.seen_codes:
                                self.seen_msg_ids.add(msg_id)
                                self.seen_codes.add(code)
                                return code
            except Exception: pass
            time.sleep(random.uniform(4.0, 7.0))
        return None

class GmailIMAPService:
    def __init__(self, base_email, app_password):
        self.base_email = base_email
        self.app_password = app_password.replace(" ", "")
        self.mail = None
        self.seen_uids = set()
        self.seen_codes = set()

    def connect(self):
        try:
            try:
                if self.mail: self.mail.logout()
            except Exception:
                pass
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.mail.login(self.base_email, self.app_password)
            return True
        except Exception as e:
            print(f"{Colors.color_text(f'Lỗi đăng nhập IMAP cho {self.base_email}: {e}', Colors.ERROR)}")
            return False

    def get_latest_uid(self):
        if not self.mail and not self.connect(): return 0
        try:
            self.mail.select("INBOX", readonly=True)
            status, data = self.mail.uid("search", None, 'ALL')
            if status == "OK" and data[0]:
                uids = data[0].split()
                if uids: return int(uids[-1]) 
        except Exception:
            if self.connect():
                try:
                    self.mail.select("INBOX", readonly=True)
                    status, data = self.mail.uid("search", None, 'ALL')
                    if status == "OK" and data[0]:
                        uids = data[0].split()
                        if uids: return int(uids[-1])
                except Exception: pass
        return 0

    def get_text(self, msg):
        plain, html = [], []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment": continue
                ctype = part.get_content_type()
                payload = part.get_payload(decode=True)
                if not payload: continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if ctype == "text/plain": plain.append(text)
                elif ctype == "text/html": html.append(text)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/plain": plain.append(text)
                else: html.append(text)
        if plain: return "\n".join(plain).strip()
        if html: return "\n".join(html).strip()
        return ""

    def decode_msg_header(self, raw_header):
        if not raw_header: return ""
        try:
            decoded = decode_header(raw_header)
            result = ""
            for text, charset in decoded:
                if isinstance(text, bytes):
                    try: result += text.decode(charset or 'utf-8', errors='replace')
                    except: result += text.decode('utf-8', errors='replace')
                else:
                    result += str(text)
            return result
        except: return str(raw_header)

    def get_otp_code(self, target_email, since_uid=0, timeout=120, force_8_digits=False):
        if not self.mail:
            if not self.connect(): return None
        start_time = time.time()
        time.sleep(random.uniform(1.0, 3.0))
        
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                try:
                    self.mail.noop()
                except Exception:
                    self.connect()

                self.mail.select("INBOX", readonly=True)
                status, data = self.mail.uid("search", None, 'ALL')
                if status == "OK" and data[0]:
                    uids = data[0].split()
                    for uid_bytes in reversed(uids[-15:]):
                        try: uid_int = int(uid_bytes)
                        except ValueError: continue
                        
                        if uid_int <= since_uid or uid_bytes in self.seen_uids: 
                            continue
                            
                        status, fetch_data = self.mail.uid("fetch", uid_bytes, "(RFC822)")
                        if status == "OK" and fetch_data:
                            raw = None
                            for item in fetch_data:
                                if isinstance(item, tuple): raw = item[1]; break
                            if raw:
                                msg = email.message_from_bytes(raw)
                                to_addr = (
                                    self.decode_msg_header(msg.get("To", "")) + " " +
                                    self.decode_msg_header(msg.get("Delivered-To", "")) + " " +
                                    self.decode_msg_header(msg.get("X-Original-To", ""))
                                ).lower()
                                subject_raw = self.decode_msg_header(msg.get("Subject", ""))
                                subject = subject_raw.lower()
                                from_addr = self.decode_msg_header(msg.get("From", "")).lower()
                                
                                if target_email.lower() not in to_addr and self.base_email.lower() not in to_addr:
                                    continue
                                
                                is_ig = any(k in subject or k in from_addr for k in ["instagram", "meta", "facebook"])
                                is_security_mail = any(kw in subject for kw in [
                                    "security", "bảo mật", "verify", "xác minh", "xác nhận", "confirm",
                                    "code", "mã", "authenticate", "profile", "account", "tài khoản", "login", "đăng nhập"
                                ]) or bool(re.search(r'\d{6,8}', subject))
                                
                                if is_ig and is_security_mail:
                                    body = self.get_text(msg)
                                    code = extract_ig_otp_smart(
                                        subject=subject_raw,
                                        raw_body=body,
                                        target_email=target_email,
                                        allow_8_digits=force_8_digits
                                    )

                                    if code and code not in self.seen_codes:
                                        self.seen_uids.add(uid_bytes)
                                        self.seen_codes.add(code)
                                        return code
            except Exception:
                try: self.connect()
                except Exception: pass
            time.sleep(random.uniform(4.0, 7.0)) 
        return None

# ==================== DỊCH VỤ HOTMAIL/OUTLOOK API ====================
class HotmailAPIService:
    def __init__(self, data_line, api_mode, proxy=None):
        self.url = "https://smail1s.com/get_messages"
        self.data_line = data_line.strip()
        self.api_mode = api_mode.strip()
        self.email = self.data_line.split('|')[0] if '|' in self.data_line else self.data_line
        self.seen_msg_ids = set()
        self.seen_codes = set()
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

    def init_baseline(self):
        payload = {"mode": self.api_mode, "data": self.data_line}
        time.sleep(random.uniform(1.0, 2.5)) 
        
        for _ in range(3):
            try:
                response = self.session.post(self.url, json=payload, timeout=20)
                if response.status_code == 200:
                    data_array = response.json().get("data", [])
                    if data_array and len(data_array) > 0:
                        messages = data_array[0].get("messages", [])
                        for msg in messages:
                            msg_id = str(msg.get("id", msg.get("uid", "")))
                            if not msg_id: 
                                msg_id = hashlib.md5(str(msg.get("message", "")).encode()).hexdigest()
                            self.seen_msg_ids.add(msg_id)
                    break 
            except Exception:
                time.sleep(2) 

    def get_otp_code(self, timeout=180, force_8_digits=False): 
        start_time = time.time()
        loai_ma = "ĐỌC MÃ XÁC THỰC 2FA (6 HOẶC 8 SỐ)" if force_8_digits else "ĐỌC MÃ ĐĂNG KÝ 6 SỐ"
        print(f"{Colors.color_text(f'[API Smail1s] Đang check hộp thư {self.email} ({loai_ma})...', Colors.INFO)}")
        
        payload = {"mode": self.api_mode, "data": self.data_line}
        time.sleep(random.uniform(1.0, 3.0))
        last_logged = ""
        
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
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
                            if msg_err != last_logged:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_err}', Colors.ERROR)}")
                                last_logged = msg_err
                        else:
                            messages = account_data.get("messages", [])
                            msg_info = f"Tìm thấy {len(messages)} thư."
                            if msg_info != last_logged:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_info} Đang quét thư mới nhất lấy mã...', Colors.INFO)}")
                                last_logged = msg_info
                                
                            for msg in messages:
                                msg_id = str(msg.get("id", msg.get("uid", "")))
                                if not msg_id:
                                    msg_id = hashlib.md5(str(msg.get("message", "")).encode()).hexdigest()
                                
                                if msg_id in self.seen_msg_ids:
                                    continue
                                
                                subject_raw = str(msg.get("subject", ""))
                                subject = subject_raw.lower()
                                from_sender = str(msg.get("from", "")).lower()
                                raw_msg = str(msg.get("message", ""))
                                
                                is_ig = any(k in subject or k in from_sender for k in ["instagram", "meta", "facebook"])
                                is_security_mail = True
                                if force_8_digits:
                                    is_security_mail = any(kw in subject for kw in [
                                        "security", "bảo mật", "verify", "xác minh", "xác nhận", "confirm",
                                        "code", "mã", "factor", "authenticate", "profile", "account", "tài khoản", "login"
                                    ]) or bool(re.search(r'\d{6,8}', subject))
                                
                                if is_ig and is_security_mail:
                                    code = extract_ig_otp_smart(
                                        subject=subject_raw,
                                        raw_body=raw_msg,
                                        target_email=self.email,
                                        allow_8_digits=force_8_digits
                                    )
                                    
                                    if code and code not in self.seen_codes:
                                        self.seen_msg_ids.add(msg_id)
                                        self.seen_codes.add(code)
                                        print(f"{Colors.color_text(f'[API Smail1s] ĐÃ BẮT ĐƯỢC MÃ CHUẨN: {code}', Colors.SUCCESS)}")
                                        return code
                else:
                    status_err = f"Lỗi HTTP {response.status_code}"
                    if status_err != last_logged:
                        print(f"{Colors.color_text(f'[API Smail1s] {status_err}', Colors.WARNING)}")
                        last_logged = status_err
                        
            except requests.exceptions.RequestException as e:
                err_str = "Lỗi kết nối Smail1s. Đang thử lại..."
                if err_str != last_logged:
                    print(f"{Colors.color_text(f'[API Smail1s] {err_str} (Chi tiết: {e})', Colors.WARNING)}")
                    last_logged = err_str
                try: self._init_session() 
                except: pass
                
            except Exception as e:
                err_str = f"Lỗi không xác định: {str(e)}"
                if err_str != last_logged:
                    print(f"{Colors.color_text(f'[API Smail1s] {err_str}', Colors.WARNING)}")
                    last_logged = err_str
            
            time.sleep(random.uniform(4.0, 6.5))
        return None


# ==================== DỊCH VỤ THUÊ SIM AUTOSMS.SITE (MODE 6) ====================
class AutoSMSService:
    def __init__(self, api_key, country="vn", proxy=None):
        self.api_key = api_key
        self.country = country
        self.service = "instagram"
        self.base_url = "https://autosms.site/api"
        self.order_id = None
        self.phone = None
        self.seen_codes = set()
        self.proxy = proxy

    def buy_number(self):
        url = f"{self.base_url}/buy-number/{self.country}/{self.service}?key={self.api_key}"
        try:
            r = requests.get(url, timeout=10, proxies=self.proxy)
            js = r.json()
            if js.get("success"):
                self.phone = js["data"]["phone"]
                self.order_id = js["data"]["order_id"]
                return self.phone
        except Exception: pass
        return None

    def get_otp_code(self, timeout=120):
        if not self.order_id: return None
        start_time = time.time()
        url = f"{self.base_url}/orders/{self.order_id}?key={self.api_key}"
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                r = requests.get(url, timeout=10, proxies=self.proxy)
                js = r.json()
                if js.get("success") and js.get("data") and js["data"].get("code"):
                    code = str(js["data"]["code"]).strip()
                    if code and code not in self.seen_codes:
                        self.seen_codes.add(code)
                        return code
            except Exception: pass
            time.sleep(4)
        return None

    def cancel_order(self):
        if self.order_id:
            try:
                requests.get(f"{self.base_url}/cancel/{self.order_id}?key={self.api_key}", timeout=10, proxies=self.proxy)
            except Exception: pass


# ==================== DỊCH VỤ THUÊ EMAIL OTPTRUST.COM (MODE 7) ====================
class OTPTrustService:
    CACHED_IG_SERVICE_ID = None
    SERVICE_LOCK = threading.Lock()

    def __init__(self, api_key, provider="auto", service_id=None, proxy=None):
        self.api_key = api_key.strip()
        self.provider = (provider or "auto").strip().lower()
        self.manual_service_id = service_id
        self.base_url = "https://otptrust.com/api/v1"
        self.order_id = None
        self.email = None
        self.seen_codes = set()
        self.proxy = proxy
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def resolve_instagram_service(self):
        if self.manual_service_id:
            return int(self.manual_service_id), (["hotmail", "outlook"] if self.provider == "auto" else [self.provider])

        with OTPTrustService.SERVICE_LOCK:
            try:
                r = requests.get(f"{self.base_url}/email/services", headers=self.headers, timeout=12, proxies=self.proxy)
                if r.status_code == 200:
                    js = r.json()
                    services = js.get("data", [])
                    if isinstance(services, dict):
                        services = services.get("items") or services.get("services") or [services]

                    for sv in services:
                        sv_name = str(sv.get("name", "")).lower()
                        sv_code = str(sv.get("code", "")).lower()
                        if "instagram" in sv_name or sv_name == "ig" or "instagram" in sv_code:
                            sid = int(sv.get("id"))
                            OTPTrustService.CACHED_IG_SERVICE_ID = sid
                            avail = sv.get("available") or {}
                            if self.provider == "auto" and isinstance(avail, dict):
                                sorted_provs = [k for k, v in sorted(avail.items(), key=lambda item: int(item[1] or 0), reverse=True) if int(v or 0) > 0]
                                if sorted_provs:
                                    return sid, sorted_provs
                            break
            except Exception:
                pass

            fallback_id = OTPTrustService.CACHED_IG_SERVICE_ID if OTPTrustService.CACHED_IG_SERVICE_ID else 5
            provs = ["hotmail", "outlook", "gmail", "icloud"] if self.provider == "auto" else [self.provider]
            return fallback_id, provs

    def rent_email(self):
        service_id, providers_to_try = self.resolve_instagram_service()
        if self.provider != "auto" and self.provider not in providers_to_try:
            providers_to_try = [self.provider] + [p for p in ["hotmail", "outlook"] if p != self.provider]

        for prov in providers_to_try:
            try:
                payload = {"service_id": int(service_id), "provider": prov}
                r = requests.post(
                    f"{self.base_url}/email/rent",
                    headers=self.headers,
                    json=payload,
                    timeout=15,
                    proxies=self.proxy
                )
                js = r.json()
                if js.get("success") and js.get("data"):
                    data = js["data"]
                    self.order_id = data.get("order_id") or data.get("id")
                    self.email = data.get("email")
                    if self.email and self.order_id:
                        print(f"{Colors.color_text(f'[OTPTRUST] Đã thuê thành công ({prov}): {self.email} (Order ID: {self.order_id})', Colors.SUCCESS)}")
                        return self.email
                else:
                    msg = js.get("message") or js.get("error") or f"Hết mail loại {prov}"
                    print(f"{Colors.color_text(f'[OTPTRUST] Không thuê được loại {prov}: {msg}', Colors.WARNING)}")
            except Exception as e:
                print(f"{Colors.color_text(f'[OTPTRUST] Lỗi kết nối khi thuê mail ({prov}): {e}', Colors.WARNING)}")
            time.sleep(1)

        return None

    def get_otp_code(self, timeout=100):
        if not self.order_id:
            return None
        start_time = time.time()
        url = f"{self.base_url}/email/orders/{self.order_id}"
        last_status = ""

        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
            try:
                r = requests.get(url, headers=self.headers, timeout=12, proxies=self.proxy)
                if r.status_code == 200:
                    js = r.json()
                    if js.get("success") and js.get("data"):
                        data = js["data"]
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]

                        status = str(data.get("status", "")).lower()
                        raw_otp = data.get("otp") or data.get("code")

                        if raw_otp:
                            raw_otp_str = str(raw_otp).strip()
                            m_digit = re.search(r'(\d{6,8})', raw_otp_str)
                            code = m_digit.group(1) if m_digit else raw_otp_str
                            if code and code not in self.seen_codes:
                                self.seen_codes.add(code)
                                print(f"{Colors.color_text(f'[OTPTRUST] ĐÃ NHẬN MÃ OTP: {code} (Order #{self.order_id})', Colors.SUCCESS)}")
                                return code

                        if status in ["refunded", "closed", "failed", "canceled", "cancelled"]:
                            print(f"{Colors.color_text(f'[OTPTRUST] Đơn #{self.order_id} đã đóng trên hệ thống (status={status}).', Colors.WARNING)}")
                            return None

                        if status != last_status:
                            last_status = status
            except Exception:
                pass
            time.sleep(2.5)
        return None

    def cancel_order(self):
        if not self.order_id:
            return
        try:
            url = f"{self.base_url}/email/orders/{self.order_id}/cancel"
            r = requests.post(url, headers=self.headers, timeout=10, proxies=self.proxy)
            if r.status_code == 200:
                print(f"{Colors.color_text(f'[OTPTRUST] Đã hủy đơn #{self.order_id} và hoàn tiền tự động!', Colors.INFO)}")
        except Exception:
            pass


def generate_dot_variants(gmail):
    local, sep, domain = gmail.rpartition("@")
    if not sep or domain.lower() != "gmail.com": return [gmail]
    if "." in local: local = local.replace(".", "")
    variants = []
    if local:
        for mask in range(1 << max(0, len(local) - 1)):
            value = local[0]
            for i in range(1, len(local)):
                if mask & (1 << (i - 1)): value += "."
                value += local[i]
            variants.append(value + "@" + domain)
    random.shuffle(variants)
    return variants
  # ==================== CÁC HÀM XỬ LÝ FORM REACT & BẬT 2FA ====================
def slow_scroll_to_element(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.5)
    except Exception:
        pass

def set_react_input_value(driver, element, value_str):
    """
    Ép cập nhật giá trị cho thẻ <input> của React 16/17/18 bằng cách reset _valueTracker
    và gọi native setter của HTMLInputElement.
    """
    driver.execute_script("""
        const input = arguments[0];
        const newValue = arguments[1];
        const lastValue = input.value;
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype,
            'value'
        ).set;
        nativeInputValueSetter.call(input, newValue);
        const tracker = input._valueTracker;
        if (tracker) {
            tracker.setValue(lastValue);
        }
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    """, element, value_str)

def clear_input_completely(driver, element):
    """Xoá sạch tuyệt đối giá trị trong ô input của Instagram (cả bàn phím lẫn React state)."""
    try:
        element.click()
    except Exception:
        try: driver.execute_script("arguments[0].click();", element)
        except Exception: pass
    time.sleep(0.2)
    driver.execute_script("arguments[0].focus();", element)

    try:
        element.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)
        element.send_keys(Keys.BACKSPACE)
        time.sleep(0.1)
        element.send_keys(Keys.END)
        current_val = element.get_attribute("value") or ""
        if current_val:
            for _ in range(len(current_val) + 5):
                element.send_keys(Keys.BACKSPACE)
    except Exception:
        pass

    try:
        set_react_input_value(driver, element, "")
    except Exception:
        pass
    time.sleep(0.3)

def human_type_react(driver, thread_id, element, text, is_username=False):
    """
    Hàm gõ chữ giả lập người thật kết hợp chống React tự động ghi đè ở ô Username.
    """
    with TYPE_LOCK:
        slow_scroll_to_element(driver, element)

        if is_username:
            print(f"{Colors.color_text(f'[{thread_id}] Chờ IG nạp xong gợi ý Username (3s) để xoá triệt để...', Colors.WARNING)}")
            time.sleep(3.0)

        clear_input_completely(driver, element)

        # Gõ từng ký tự như người thật
        for char in text:
            try:
                driver.execute_script("arguments[0].focus();", element)
                element.send_keys(char)
            except Exception:
                pass
            time.sleep(random.uniform(0.05, 0.13))

        time.sleep(0.6)

        # Nếu là ô Username: Kiểm tra hậu kiểm tối đa 3 lần phòng trường hợp IG tự điền đè gợi ý muộn
        if is_username:
            for check_round in range(3):
                time.sleep(1.2)
                actual_val = (element.get_attribute("value") or "").strip()
                if actual_val == text:
                    print(f"{Colors.color_text(f'[{thread_id}] Đã kiểm tra Username khớp 100%: {actual_val}', Colors.SUCCESS)}")
                    break
                else:
                    print(f"{Colors.color_text(f'[{thread_id}] Phát hiện IG tự sửa Username thành \"{actual_val}\". Đang ép ghi đè lại (Lần {check_round+1})...', Colors.WARNING)}")
                    clear_input_completely(driver, element)
                    try:
                        set_react_input_value(driver, element, text)
                        time.sleep(0.4)
                        element.send_keys(Keys.END)
                        element.send_keys(Keys.BACKSPACE)
                        time.sleep(0.15)
                        element.send_keys(text[-1])
                    except Exception:
                        set_react_input_value(driver, element, text)

        try:
            if not is_username:
                element.send_keys(Keys.TAB)
            else:
                driver.execute_script("arguments[0].blur();", element)
        except Exception:
            pass

def find_signup_inputs(driver):
    """
    Định vị chuẩn xác 4 ô: Email/Phone, Password, FullName, Username.
    Ưu tiên tìm theo thuộc tính name/autocomplete/aria-label trước, nếu không có mới dùng index.
    """
    all_inputs = [
        el for el in driver.find_elements(By.TAG_NAME, "input")
        if el.is_displayed() and (el.get_attribute("type") or "text").lower() not in ["hidden", "file", "checkbox", "radio"]
    ]

    email_inp = None
    pass_inp = None
    fullname_inp = None
    user_inp = None

    for el in all_inputs:
        name_attr = (el.get_attribute("name") or "").lower()
        type_attr = (el.get_attribute("type") or "").lower()
        aria_attr = (el.get_attribute("aria-label") or "").lower()
        holder_attr = (el.get_attribute("placeholder") or "").lower()
        combined = f"{name_attr} {aria_attr} {holder_attr}"

        if not pass_inp and (type_attr == "password" or "password" in name_attr or "mật khẩu" in combined):
            pass_inp = el
        elif not user_inp and ("username" in name_attr or "tên người dùng" in combined or "username" in combined):
            user_inp = el
        elif not fullname_inp and ("fullname" in name_attr or "full_name" in name_attr or "tên đầy đủ" in combined or "full name" in combined or "họ và tên" in combined):
            fullname_inp = el
        elif not email_inp and ("email" in name_attr or "contactpoint" in name_attr or "số di động" in combined or "mobile" in combined or "email" in combined):
            email_inp = el

    if len(all_inputs) >= 4:
        if not email_inp: email_inp = all_inputs[0]
        if not pass_inp: pass_inp = all_inputs[1]
        if not fullname_inp: fullname_inp = all_inputs[2]
        if not user_inp: user_inp = all_inputs[3]

    return email_inp, pass_inp, fullname_inp, user_inp

def fill_otp_into_active_inputs(driver, code_str):
    """
    Điền mã OTP (6 hoặc 8 số) thông minh:
    Hỗ trợ cả giao diện 1 ô input duy nhất lẫn giao diện tách 6-8 ô input rời của Meta Accounts Center.
    """
    code_str = str(code_str).strip()
    visible_inputs = [
        inp for inp in driver.find_elements(By.TAG_NAME, "input")
        if inp.is_displayed() and (inp.get_attribute("type") or "text").lower() not in ["hidden", "file", "checkbox", "radio"]
    ]

    if not visible_inputs:
        return False

    if len(visible_inputs) >= len(code_str) and len(code_str) in [6, 8]:
        try:
            visible_inputs[0].click()
            time.sleep(0.2)
            for idx, digit in enumerate(code_str):
                if idx < len(visible_inputs):
                    target = visible_inputs[idx]
                    set_react_input_value(driver, target, digit)
                    try: target.send_keys(digit)
                    except Exception: pass
                    time.sleep(0.08)
            return True
        except Exception:
            pass

    target_inp = visible_inputs[0]
    try:
        clear_input_completely(driver, target_inp)
        for digit in code_str:
            target_inp.send_keys(digit)
            time.sleep(0.07)
        time.sleep(0.3)
        if (target_inp.get_attribute("value") or "").strip() != code_str:
            set_react_input_value(driver, target_inp, code_str)
        return True
    except Exception:
        try:
            set_react_input_value(driver, target_inp, code_str)
            return True
        except Exception:
            return False

def verify_2fa_security_code_if_needed(driver, thread_id, used_email, mode, mail_service, imap_service, hotmail_service, autosms_service, uid_moc):
    """
    Kiểm tra và xử lý màn hình bắt xác thực OTP (Email / SĐT) trước khi cho phép bật 2FA.
    - Nếu là Mode 7 (Thuê mail OTPTRUST): Khi phát hiện tài khoản đòi xác thực OTP thì trả về "SKIP_2FA"
      để bỏ qua 2FA luôn theo đúng yêu cầu (chỉ bật 2FA cho những con không bắt xác thực lại).
    - Nếu là Mode 1..6: Tự động lấy mã OTP (6 hoặc 8 số), hỗ trợ bấm gửi lại tối đa 2 lần.
    """
    time.sleep(3)

    # Bước A: Kiểm tra màn hình chọn phương thức nhận mã xác minh ("Confirm it's you / Xác nhận đó là bạn")
    try:
        is_confirm_choice = driver.execute_script("""
            const bodyTxt = (document.body.innerText || '').toLowerCase();
            return (
                bodyTxt.includes('confirm it') ||
                bodyTxt.includes('xác nhận đó là bạn') ||
                bodyTxt.includes('verify your account') ||
                bodyTxt.includes('xác minh tài khoản') ||
                bodyTxt.includes('chọn cách khôi phục') ||
                bodyTxt.includes('choose a way')
            );
        """)
        if is_confirm_choice:
            if mode == "7":
                print(f"{Colors.color_text(f'[{thread_id}] [Mode 7 - OTPTRUST] Tài khoản bắt xác minh lại danh tính trước khi bật 2FA -> Bỏ qua 2FA và lưu acc luôn!', Colors.WARNING)}")
                return "SKIP_2FA"

            driver.execute_script("""
                const radios = Array.from(document.querySelectorAll('input[type="radio"], [role="radio"]'));
                if (radios.length > 0) {
                    try { radios[0].click(); } catch(e) {}
                }
                const btns = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                for (let b of btns) {
                    let t = (b.innerText || b.textContent || '').trim().toLowerCase();
                    if (['tiếp tục', 'continue', 'send code', 'gửi mã', 'next', 'tiếp'].includes(t)) {
                        let clickable = b.closest('button, [role="button"]') || b;
                        if (!clickable.disabled) {
                            clickable.click();
                            break;
                        }
                    }
                }
            """)
            time.sleep(3)
    except Exception:
        pass

    # Bước B: Kiểm tra xem màn hình hiện tại có phải là màn hình đòi nhập OTP bảo mật không
    is_otp_screen = False
    for _ in range(5):
        try:
            is_otp_screen = driver.execute_script("""
                const txt = (document.body.innerText || document.body.textContent || '').toLowerCase();
                if (txt.includes('sao chép khóa') || txt.includes('copy key') || txt.includes('quét mã qr') || txt.includes('scan the qr')) {
                    return false;
                }
                const hasOtpKeywords = (
                    txt.includes('kiểm tra email') ||
                    txt.includes('check your email') ||
                    txt.includes('kiểm tra tin nhắn') ||
                    txt.includes('check your text') ||
                    txt.includes('check your whatsapp') ||
                    txt.includes('mã bảo mật') ||
                    txt.includes('security code') ||
                    txt.includes('mã xác nhận') ||
                    txt.includes('confirmation code') ||
                    txt.includes('nhập mã') ||
                    txt.includes('enter the code') ||
                    txt.includes('enter code') ||
                    txt.includes('chúng tôi đã gửi mã') ||
                    txt.includes('we sent a code')
                );
                const visibleInputs = Array.from(document.querySelectorAll('input')).filter(
                    i => i.offsetHeight > 0 && !['hidden', 'file', 'radio', 'checkbox'].includes((i.type || '').toLowerCase())
                );
                return hasOtpKeywords && visibleInputs.length > 0;
            """)
            if is_otp_screen:
                break
        except Exception:
            pass
        time.sleep(1.5)

    if not is_otp_screen:
        return True

    # NẾU LÀ MODE 7 (OTPTRUST): BỎ QUA 2FA NGAY KHI BỊ ĐÒI OTP XÁC THỰC EMAIL
    if mode == "7":
        print(f"{Colors.color_text(f'[{thread_id}] [Mode 7 - OTPTRUST] Tài khoản bắt nhập OTP email trước khi bật 2FA -> Bỏ qua 2FA và lưu acc luôn!', Colors.WARNING)}")
        return "SKIP_2FA"

    print(f"{Colors.color_text(f'[{thread_id}] PHÁT HIỆN MÀN HÌNH XÁC THỰC BẢO MẬT TRƯỚC KHI BẬT 2FA! Đang lấy mã OTP (6 hoặc 8 số)...', Colors.WARNING)}")

    max_2fa_resend = 2  # 1 lần chờ đầu + 2 lần bấm gửi lại mã
    verify_code = None

    for attempt in range(max_2fa_resend + 1):
        if STOP_EVENT.is_set():
            return False

        if mode == "2" and not (mail_service and mail_service.token):
            with OTP_LOCK:
                PAUSE_FOR_INPUT.clear()
                built_in_print(f"\n{Colors.color_text(f'[{thread_id}] [XÁC THỰC 2FA - Lần {attempt+1}] NHẬP MÃ BẢO MẬT CHO [{used_email}]: ', Colors.SUCCESS)}", end="")
                verify_code = input().strip()
                PAUSE_FOR_INPUT.set()
        else:
            print(f"{Colors.color_text(f'[{thread_id}] [XÁC THỰC 2FA - Lần {attempt+1}/{max_2fa_resend+1}] Đang quét hộp thư lấy mã bảo mật mới nhất...', Colors.INFO)}")
            wait_timeout = 75
            if mode == "1" or (mode == "2" and mail_service and mail_service.token):
                verify_code = mail_service.get_otp_code(timeout=wait_timeout, force_8_digits=True)
            elif mode in ["3", "4"] and imap_service:
                verify_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=wait_timeout, force_8_digits=True)
            elif mode == "5" and hotmail_service:
                verify_code = hotmail_service.get_otp_code(timeout=90, force_8_digits=True)
            elif mode == "6" and autosms_service:
                verify_code = autosms_service.get_otp_code(timeout=75)

        if verify_code:
            break

        if attempt < max_2fa_resend:
            print(f"{Colors.color_text(f'[{thread_id}] Chưa thấy mã xác thực 2FA ở lần {attempt+1}. Đang bấm \"Lấy mã mới / Gửi lại mã\"...', Colors.WARNING)}")
            clicked_resend_2fa = driver.execute_script("""
                const els = Array.from(document.querySelectorAll('a, button, div[role="button"], span'));
                for (let el of els) {
                    let t = (el.innerText || el.textContent || '').trim().toLowerCase();
                    if (
                        t.includes('lấy mã mới') ||
                        t.includes('gửi lại mã') ||
                        t.includes('gửi mã mới') ||
                        t.includes('get a new code') ||
                        t.includes('resend code') ||
                        t.includes('send code again') ||
                        t.includes('gửi lại') ||
                        t.includes('resend')
                    ) {
                        let btn = el.closest('button, [role="button"], a') || el;
                        try { btn.click(); return true; } catch(e) {}
                    }
                }
                return false;
            """)
            if clicked_resend_2fa:
                print(f"{Colors.color_text(f'[{thread_id}] Đã bấm yêu cầu gửi lại mã xác thực 2FA thành công! Đợi 5s...', Colors.INFO)}")
                time.sleep(5)
            else:
                print(f"{Colors.color_text(f'[{thread_id}] Không tìm thấy nút gửi lại mã trên màn hình, tiếp tục quét hộp thư...', Colors.WARNING)}")
                time.sleep(3)

    if not verify_code:
        print(f"{Colors.color_text(f'[{thread_id}] Lỗi: Không lấy được mã OTP xác thực bảo mật 2FA sau {max_2fa_resend+1} lần thử!', Colors.ERROR)}")
        return False

    print(f"{Colors.color_text(f'[{thread_id}] ĐÃ LẤY ĐƯỢC MÃ XÁC THỰC BẢO MẬT 2FA: {verify_code}. Đang điền...', Colors.SUCCESS)}")
    fill_otp_into_active_inputs(driver, verify_code)
    time.sleep(1.5)

    driver.execute_script("""
        const btns = Array.from(document.querySelectorAll('button, div[role="button"], span'));
        for (let b of btns) {
            let t = (b.innerText || b.textContent || '').trim().toLowerCase();
            if (['tiếp tục', 'next', 'continue', 'gửi', 'tiếp', 'xác nhận', 'confirm', 'submit', 'xong', 'done'].includes(t)) {
                let clickable = b.closest('button, [role="button"]') || b;
                let rect = clickable.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && !clickable.disabled && clickable.getAttribute('aria-disabled') !== 'true') {
                    clickable.click();
                    return;
                }
            }
        }
    """)
    try:
        active_inps = [i for i in driver.find_elements(By.TAG_NAME, "input") if i.is_displayed()]
        if active_inps:
            active_inps[-1].send_keys(Keys.ENTER)
    except Exception:
        pass

    print(f"{Colors.color_text(f'[{thread_id}] Đã gửi mã xác thực bảo mật! Chờ 8s để chuyển tiếp...', Colors.INFO)}")
    time.sleep(8)
    return True

def setup_instagram_2fa(driver, thread_id, username, used_email, mode, mail_service, imap_service, hotmail_service, autosms_service, uid_moc):
    """
    Quy trình bật 2FA hoàn chỉnh:
    - Với Mode 7 (OTPTRUST): Nếu không bắt xác thực OTP thì bật 2FA, nếu bắt xác thực OTP thì thoát ra lưu acc luôn.
    - Với Mode 1..6: Tự động vượt OTP xác thực (ở cả trước và sau bước chọn Ứng dụng xác thực) rồi bật 2FA.
    """
    print(f"{Colors.color_text(f'[{thread_id}] Đang tiến hành cài đặt 2FA (Hỗ trợ song ngữ Anh - Việt)...', Colors.INFO)}")
    two_fa_secret = ""
    try:
        driver.get("https://accountscenter.instagram.com/password_and_security/two_factor/")
        time.sleep(7)

        # 1. Chọn tài khoản trong Trung tâm tài khoản Meta
        print(f"{Colors.color_text(f'[{self_id if (self_id := thread_id) else thread_id}] Xử lý chọn tài khoản / màn hình đệm Meta...', Colors.INFO)}")
        for _ in range(4):
            try:
                clicked_buffer = driver.execute_script("""
                    let targetUser = arguments[0].toLowerCase();
                    let allElements = Array.from(document.querySelectorAll('*'));
                    for (let el of allElements) {
                        let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                        if (txt.includes(targetUser) && txt.length < 60) {
                            let clickable = el.closest('div[role="button"], a[role="link"], button, li');
                            if (clickable) { clickable.click(); return 'CLICK_USER'; }
                        }
                    }
                    return 'NOT_FOUND';
                """, username)
                if clicked_buffer != 'NOT_FOUND':
                    time.sleep(4)
                    break
                time.sleep(2)
            except Exception:
                pass

        # 2. Bấm nút "Bắt đầu" (Get started) nếu có
        for _ in range(4):
            clicked_start = driver.execute_script("""
                let allElements = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                for (let el of allElements) {
                    let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                    if (txt === 'bắt đầu' || txt === 'get started') {
                        let btn = el.closest('button, [role="button"]') || el;
                        btn.click();
                        return true;
                    }
                }
                return false;
            """)
            if clicked_start:
                print(f"{Colors.color_text(f'[{thread_id}] ĐÃ BẤM NÚT \"Bắt đầu\" THÀNH CÔNG!', Colors.SUCCESS)}")
                time.sleep(4)
                break
            time.sleep(1)

        # 3. Kiểm tra xác thực OTP lần 1
        step1_status = verify_2fa_security_code_if_needed(
            driver, thread_id, used_email, mode,
            mail_service, imap_service, hotmail_service, autosms_service, uid_moc
        )
        if step1_status == "SKIP_2FA" or step1_status is False:
            return ""

        # 4. Chọn phương thức "Ứng dụng xác thực" (Authentication App) và bấm Tiếp tục
        try:
            clicked_app = driver.execute_script("""
                let all = Array.from(document.querySelectorAll('div, span, label'));
                for (let el of all) {
                    let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                    if (txt === 'authentication app' || txt === 'ứng dụng xác thực' || txt.includes('duo mobile') || txt.includes('google authenticator')) {
                        let clickable = el.closest('div[role="button"], label, div[tabindex], button, [role="radio"]') || el;
                        clickable.click();
                        return true;
                    }
                }
                return false;
            """)
            if clicked_app:
                print(f"{Colors.color_text(f'[{thread_id}] Đã chọn phương thức \"Ứng dụng xác thực\". Đang bấm Tiếp tục...', Colors.INFO)}")
                time.sleep(2)
                driver.execute_script("""
                    let btns = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                    for (let b of btns) {
                        let txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                        if (['continue', 'next', 'tiếp tục', 'tiếp'].includes(txt)) {
                            let clickable = b.closest('button, [role="button"]') || b;
                            if (!clickable.disabled) { clickable.click(); return; }
                        }
                    }
                """)
                time.sleep(5)
        except Exception:
            pass

        # 5. Kiểm tra xác thực OTP lần 2 (Nếu Meta bắt nhập OTP SAU KHI chọn "Ứng dụng xác thực")
        step2_status = verify_2fa_security_code_if_needed(
            driver, thread_id, used_email, mode,
            mail_service, imap_service, hotmail_service, autosms_service, uid_moc
        )
        if step2_status == "SKIP_2FA" or step2_status is False:
            return ""

        # 6. Bóc tách Secret Key 2FA bằng Clipboard Hook + Regex
        print(f"{Colors.color_text(f'[{thread_id}] Đang tìm và bóc tách Secret Key 2FA...', Colors.INFO)}")
        driver.execute_script("""
            window.hooked2FAKey = "";
            if (navigator.clipboard && !window.clipboardHooked) {
                const originalWriteText = navigator.clipboard.writeText;
                navigator.clipboard.writeText = function(text) {
                    let clean = (text || '').replace(/\\s+/g, '').toUpperCase();
                    if (clean.length >= 16 && /^[A-Z2-7]+$/.test(clean)) {
                        window.hooked2FAKey = clean;
                    }
                    return originalWriteText.apply(this, arguments);
                };
                window.clipboardHooked = true;
            }
        """)

        for _ in range(7):
            if STOP_EVENT.is_set():
                return ""

            driver.execute_script("""
                let els = Array.from(document.querySelectorAll('span, div, button, a'));
                for (let el of els) {
                    let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                    if (txt === 'sao chép khóa' || txt === 'copy key' || txt.includes('sao chép khóa') || txt.includes('copy key') || txt.includes("can't scan") || txt.includes("không quét được")) {
                        try { el.click(); } catch(e) {}
                    }
                }
            """)
            time.sleep(2)

            key_from_clipboard = driver.execute_script("return window.hooked2FAKey;")
            if key_from_clipboard and len(key_from_clipboard) >= 16:
                two_fa_secret = key_from_clipboard
                break

            extracted_key = driver.execute_script("""
                let text = document.body.innerText || "";
                let match = text.match(/\\b([A-Z2-7]{4}[\\s-]*){8}\\b/);
                if (match) {
                    return match[0].replace(/[^A-Z2-7]/g, '').toUpperCase();
                }
                let match2 = text.match(/\\b([A-Z2-7]{4}\\s+){3,7}[A-Z2-7]{4}\\b/);
                if (match2) {
                    return match2[0].replace(/[^A-Z2-7]/g, '').toUpperCase();
                }
                return null;
            """)
            if extracted_key and len(extracted_key) >= 16:
                two_fa_secret = extracted_key
                break

            time.sleep(2)

        if two_fa_secret:
            print(f"{Colors.color_text(f'[{thread_id}] ĐÃ LẤY CHUẨN XÁC SECRET KEY 2FA: {two_fa_secret}', Colors.SUCCESS)}")

            # Bấm nút "Nhập mã" / "Tiếp"
            driver.execute_script("""
                let btns = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                for (let b of btns) {
                    let txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                    if (['nhập mã', 'enter code', 'next', 'continue', 'tiếp tục', 'tiếp'].includes(txt)) {
                        let clickable = b.closest('button, [role="button"]') || b;
                        let rect = clickable.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && !clickable.disabled) {
                            clickable.click();
                            return;
                        }
                    }
                }
            """)
            time.sleep(4)

            # Sinh mã TOTP 6 số từ pyotp và điền
            totp = pyotp.TOTP(two_fa_secret)
            current_otp = totp.now()
            print(f"{Colors.color_text(f'[{thread_id}] Đã sinh mã TOTP 6 số ({current_otp}). Đang điền xác nhận 2FA...', Colors.INFO)}")

            fill_otp_into_active_inputs(driver, current_otp)
            time.sleep(1.5)

            # Bấm Tiếp / Xác nhận mã TOTP
            driver.execute_script("""
                let btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                btns.reverse();
                for (let b of btns) {
                    let t = (b.innerText || b.textContent || "").trim().toLowerCase();
                    if (['tiếp', 'tiếp tục', 'next', 'continue', 'submit', 'xác nhận', 'confirm', 'xong', 'done'].includes(t)) {
                        let rect = b.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && !b.disabled && b.getAttribute('aria-disabled') !== 'true') {
                            b.click();
                            return;
                        }
                    }
                }
            """)
            time.sleep(5)

            # Bấm nút "Xong" / "Done" ở màn hình mã dự phòng cuối cùng (nếu có)
            driver.execute_script("""
                let btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                btns.reverse();
                for (let b of btns) {
                    let t = (b.innerText || b.textContent || "").trim().toLowerCase();
                    if (['xong', 'done', 'đóng', 'close'].includes(t)) {
                        let rect = b.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && !b.disabled) {
                            b.click();
                            return;
                        }
                    }
                }
            """)
            time.sleep(3)
            print(f"{Colors.color_text(f'[{thread_id}] BẬT 2FA THÀNH CÔNG RỰC RỠ!', Colors.SUCCESS)}")
        else:
            print(f"{Colors.color_text(f'[{thread_id}] Không nhận diện được Secret Key 2FA trên giao diện.', Colors.WARNING)}")
    except Exception as e:
        print(f"{Colors.color_text(f'[{thread_id}] Quá trình 2FA gặp lỗi: {e}', Colors.WARNING)}")

    return two_fa_secret
  # ==================== MAIN THREAD ====================
class starts(threading.Thread):
    def __init__(
        self,
        thread_id,
        mode,
        account_count,
        data_source,
        manual_password=None,
        base_gmail=None,
        app_password=None,
        api_mode=None,
        avatar_folder="",
        proxies_list=None,
        autosms_api_key=None,
        autosms_country="vn",
        otptrust_api_key=None,
        otptrust_provider="auto",
        otptrust_service_id=None
    ):
        super().__init__()
        self.thread_id = f"Tab-{thread_id}"
        self.mode = mode
        self.account_count = account_count
        self.data_source = data_source
        self.manual_password = manual_password 
        self.base_gmail = base_gmail
        self.app_password = app_password
        self.api_mode = api_mode
        self.avatar_folder = avatar_folder
        self.proxies_list = proxies_list or [] 
        self.autosms_api_key = autosms_api_key
        self.autosms_country = autosms_country
        self.otptrust_api_key = otptrust_api_key
        self.otptrust_provider = otptrust_provider
        self.otptrust_service_id = otptrust_service_id
    
    def run(self):
        global BASE_YEAR
        
        # --- LẤY PROXY LOCAL DÀNH CHO LUỒNG NÀY ---
        raw_proxy = None
        req_proxy = None
        if self.proxies_list:
            thread_idx_for_proxy = int(self.thread_id.split("-")[1]) - 1
            raw_proxy = self.proxies_list[thread_idx_for_proxy % len(self.proxies_list)]
            req_proxy = format_proxy(raw_proxy)
            p_info = parse_proxy(raw_proxy)
            
            if p_info and p_info.get("user"):
                p_ip = p_info["ip"]
                p_port = p_info["port"]
                p_user = p_info["user"]
                print(Colors.color_text(f"[{self.thread_id}] Đã gán Proxy (Có User/Pass): {p_ip}:{p_port} (User: {p_user})", Colors.WARNING))
            elif p_info:
                p_ip = p_info["ip"]
                p_port = p_info["port"]
                print(Colors.color_text(f"[{self.thread_id}] Đã gán Proxy (IP:Port): {p_ip}:{p_port}", Colors.WARNING))
            else:
                print(Colors.color_text(f"[{self.thread_id}] Đã gán Proxy: {raw_proxy}", Colors.WARNING))
        
        def create_one_account(account_index):
            global BASE_YEAR
            if STOP_EVENT.is_set(): return False
                
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{self.thread_id}] BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            used_email = ""
            imap_service = None
            mail_service = None
            hotmail_service = None
            autosms_service = None
            otptrust_service = None
            full_name, username = VietnameseNameGenerator()
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
            secure_pass = "".join(random.choice(chars) for _ in range(12))

            if self.mode == "1":
                mail_service = MailService(proxy=req_proxy)
                used_email = mail_service.create_account(username)
                if not used_email: return False
                mail_service.authenticate()
                
            elif self.mode == "2":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    used_email = self.data_source.pop(0)
                if "mail.tm" in used_email.lower():
                    mail_service = MailService(proxy=req_proxy)
                    pass_to_use = self.manual_password if self.manual_password else "TempPass123!"
                    mail_service.authenticate(used_email, pass_to_use)
                
            elif self.mode == "3":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    used_email, app_pass = self.data_source.pop(0)
                imap_service = GmailIMAPService(used_email, app_pass)
                
            elif self.mode == "4":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    used_email = self.data_source.pop(0)
                imap_service = GmailIMAPService(self.base_gmail, self.app_password)

            elif self.mode == "5":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    data_line = self.data_source.pop(0)
                used_email = data_line.split('|')[0]
                hotmail_service = HotmailAPIService(data_line, self.api_mode, proxy=req_proxy)

            elif self.mode == "6":
                autosms_service = AutoSMSService(self.autosms_api_key, self.autosms_country, proxy=req_proxy)
                used_email = autosms_service.buy_number()
                if not used_email:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không thể thuê số điện thoại từ API (Hết số hoặc Sai Key)!', Colors.ERROR)}")
                    return False

            elif self.mode == "7":
                otptrust_service = OTPTrustService(
                    api_key=self.otptrust_api_key,
                    provider=self.otptrust_provider,
                    service_id=self.otptrust_service_id,
                    proxy=req_proxy
                )
                used_email = otptrust_service.rent_email()
                if not used_email:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không thể thuê Email từ OTPTRUST (Hết mail, hết số dư hoặc sai API Key)!', Colors.ERROR)}")
                    return False

            print(f"{Colors.color_text(f'[{self.thread_id}] Đang dùng Email/SĐT: {used_email}', Colors.INFO)}")

            driver = None
            try:
                # ========================================================
                # MỞ CỬA SỔ DẠNG HÌNH CHỮ NHẬT DỌC ĐỂ XẾP 8 Ô
                # ========================================================
                thread_idx = int(self.thread_id.split("-")[1]) - 1 
                
                win_width = 460   
                win_height = 520  
                
                columns = 4       
                col = thread_idx % columns
                row = thread_idx // columns
                
                x_pos = col * win_width
                y_pos = row * win_height
                
                options = uc.ChromeOptions()
                options.add_argument('--mute-audio')
                options.add_argument('--disable-notifications')
                options.add_argument('--disable-save-password-bubble')
                options.add_argument('--password-store=basic')
                
                # TẮT TRIỆT ĐỂ BẢNG HỎI LƯU MẬT KHẨU & AUTOFILL CỦA CHROME
                prefs = {
                    'credentials_enable_service': False,
                    'profile.password_manager_enabled': False,
                    'profile.password_manager_leak_detection': False,
                    'autofill.profile_enabled': False,
                    'profile.default_content_setting_values.notifications': 2
                }
                options.add_experimental_option('prefs', prefs)
                
                options.add_argument(f'--window-size={win_width},{win_height}')
                options.add_argument(f'--window-position={x_pos},{y_pos}')
                options.add_argument('--force-device-scale-factor=0.65')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-software-rasterizer')
                options.add_argument('--disable-dev-shm-usage')
                
                # >>> XỬ LÝ PROXY ĐA NĂNG & AN TOÀN CHO CHROME (CHẠY 100% TAB ẨN DANH & ĐỔI IP THẬT) <<<
                forwarder = None
                options.add_argument('--incognito')
                
                if raw_proxy:
                    parsed_p = parse_proxy(raw_proxy)
                    if parsed_p:
                        if parsed_p.get("user") and parsed_p.get("pass"):
                            forwarder = LocalProxyForwarder(parsed_p["ip"], parsed_p["port"], parsed_p["user"], parsed_p["pass"])
                            options.add_argument(f'--proxy-server=http://127.0.0.1:{forwarder.local_port}')
                        else:
                            options.add_argument(f'--proxy-server=http://{parsed_p["ip"]}:{parsed_p["port"]}')
                
                with BROWSER_LOCK:
                    driver = uc.Chrome(options=options)
                    with DRIVER_LOCK:
                        ALL_DRIVERS.append((self.thread_id, driver))
                    try:
                        driver.set_window_size(win_width, win_height)
                        driver.set_window_position(x_pos, y_pos)
                    except Exception:
                        pass
                    time.sleep(1) 
                    
                wait = WebDriverWait(driver, 15)
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang truy cập Instagram Web qua Proxy...', Colors.INFO)}")
                driver.get("https://www.instagram.com/accounts/emailsignup/")
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang chờ trang tải hoàn tất (10s)...', Colors.WARNING)}")
                time.sleep(10)
                
                try:
                    cookie_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept') or contains(text(), 'Cho phép') or contains(text(), 'Đồng ý')]")
                    if cookie_btns:
                        driver.execute_script("arguments[0].click();", cookie_btns[0])
                        time.sleep(2)
                except Exception:
                    pass

                current_year = str(BASE_YEAR + random.randint(-3, 3))
                if int(current_year) > 2005: current_year = "2005"
                current_day = str(random.randint(2, 28))
                current_month = str(random.randint(1, 12))
                
                BASE_YEAR -= 1
                if BASE_YEAR < 1990: BASE_YEAR = random.randint(1995, 2005)

                try:
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, '//select | //*[@role="combobox"] | //input')))
                    email_inp, pass_inp, fullname_inp, user_inp = find_signup_inputs(driver)
                    
                    if email_inp and pass_inp and fullname_inp and user_inp:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Email/SĐT...', Colors.INFO)}")
                        human_type_react(driver, self.thread_id, email_inp, used_email, is_username=False)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Mật khẩu...', Colors.INFO)}")
                        human_type_react(driver, self.thread_id, pass_inp, secure_pass, is_username=False)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Bắt đầu chọn Ngày Sinh bằng Script Console...', Colors.INFO)}")
                        try:
                            driver.set_script_timeout(15)
                            js_script = '''
                            const day = arguments[0];
                            const month = arguments[1];
                            const year = arguments[2];
                            const callback = arguments[arguments.length - 1];

                            (async function() {
                                try {
                                    const selects = Array.from(document.querySelectorAll('select'));
                                    if (selects.length >= 3) {
                                        function setSelectVal(el, val) {
                                            let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set;
                                            nativeSetter.call(el, val);
                                            el.dispatchEvent(new Event('change', { bubbles: true }));
                                        }
                                        
                                        for (let sel of selects) {
                                            const t = (sel.title || "").toLowerCase();
                                            if (t.includes("tháng") || t.includes("month")) {
                                                setSelectVal(sel, month);
                                            } else if (t.includes("ngày") || t.includes("day")) {
                                                setSelectVal(sel, day);
                                            } else if (t.includes("năm") || t.includes("year")) {
                                                setSelectVal(sel, year);
                                            }
                                        }
                                        await new Promise(r => setTimeout(r, 1000));
                                        return callback("SUCCESS");
                                    }

                                    const comboboxes = Array.from(document.querySelectorAll('[role="combobox"]'));
                                    if (comboboxes.length < 3) return callback("ERROR: Không tìm thấy 3 ô combobox!");

                                    const monthNum = parseInt(month, 10);
                                    const enMonths = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
                                    const viMonths = ["tháng 1", "tháng 2", "tháng 3", "tháng 4", "tháng 5", "tháng 6", "tháng 7", "tháng 8", "tháng 9", "tháng 10", "tháng 11", "tháng 12"];
                                    const possibleMonths = [String(monthNum), "0" + monthNum, enMonths[monthNum-1], viMonths[monthNum-1]];

                                    async function clickOption(box, possibleValues) {
                                        box.scrollIntoView({ block: 'center' });
                                        box.click();
                                        await new Promise(r => setTimeout(r, 600));
                                        
                                        const options = Array.from(document.querySelectorAll('div, span, li, option'));
                                        const matched = options.filter(el => {
                                            if (el.offsetHeight === 0 && !el.getClientRects().length) return false;
                                            const txt = el.innerText?.trim().toLowerCase() || "";
                                            return possibleValues.includes(txt);
                                        });

                                        if (matched.length > 0) {
                                            const target = matched[matched.length - 1];
                                            target.scrollIntoView({ block: 'nearest' });
                                            target.click();
                                            await new Promise(r => setTimeout(r, 400));
                                            return true;
                                        }
                                        
                                        document.body.click(); 
                                        await new Promise(r => setTimeout(r, 200));
                                        return false;
                                    }

                                    const htmlLang = document.documentElement.lang.toLowerCase();
                                    if (htmlLang.includes('vi')) {
                                        await clickOption(comboboxes[0], [String(day), "0" + day]);
                                        await clickOption(comboboxes[1], possibleMonths);
                                        await clickOption(comboboxes[2], [String(year)]);
                                    } else {
                                        await clickOption(comboboxes[0], possibleMonths);
                                        await clickOption(comboboxes[1], [String(day), "0" + day]);
                                        await clickOption(comboboxes[2], [String(year)]);
                                    }

                                    callback("SUCCESS");
                                } catch (err) {
                                    callback("ERROR: " + err.toString());
                                }
                            })();
                            '''
                            result = driver.execute_async_script(js_script, current_day, current_month, current_year)
                            if result == "SUCCESS":
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã chạy xong JS chọn: {current_day}/{current_month}/{current_year}', Colors.SUCCESS)}")
                            else:
                                print(f"{Colors.color_text(f'[{self.thread_id}] JS chạy lỗi: {result}', Colors.WARNING)}")
                                
                        except Exception as e:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi tải khối Ngày Sinh (JS): {e}', Colors.ERROR)}")
                            
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Họ Tên...', Colors.INFO)}")
                        human_type_react(driver, self.thread_id, fullname_inp, full_name, is_username=False)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Xử lý form Username...', Colors.INFO)}")
                        _, _, _, user_inp = find_signup_inputs(driver)
                        human_type_react(driver, self.thread_id, user_inp, username, is_username=True)
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Giao diện IG bị thay đổi, không đủ 4 ô input!', Colors.ERROR)}")
                        return False
                    
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã điền xong. Ngâm form 10s trước khi bấm nút Đăng Ký...', Colors.WARNING)}")
                    time.sleep(10)

                    # KIỂM TRA LẠI USERNAME LẦN CUỐI SAU KHI NGÂM 10S ĐỂ CHỐNG IG GHI ĐÈ MUỘN
                    try:
                        _, _, _, latest_user_inp = find_signup_inputs(driver)
                        if latest_user_inp:
                            curr_u = (latest_user_inp.get_attribute("value") or "").strip()
                            if curr_u != username:
                                print(f"{Colors.color_text(f'[{self.thread_id}] Phát hiện Username bị đổi sau khi ngâm ({curr_u}). Đang điền lại chuẩn xác...', Colors.WARNING)}")
                                human_type_react(driver, self.thread_id, latest_user_inp, username, is_username=True)
                    except Exception:
                        pass

                    uid_moc = 0
                    if self.mode in ["3", "4"] and imap_service:
                        uid_moc = imap_service.get_latest_uid()
                    elif self.mode == "5" and hotmail_service:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Khởi tạo mốc hộp thư để tránh đọc thư cũ...', Colors.INFO)}")
                        hotmail_service.init_baseline()

                    print(f"{Colors.color_text(f'[{self.thread_id}] Cuộn trang xuống cuối để tìm nút Gửi...', Colors.INFO)}")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

                    print(f"{Colors.color_text(f'[{self.thread_id}] Click ra ngoài form để kích hoạt Validate...', Colors.INFO)}")
                    driver.execute_script("document.body.click();")
                    
                    print(f"{Colors.color_text(f'[{self.thread_id}] Chờ form validate (Check Username)... (5s)', Colors.WARNING)}")
                    time.sleep(5)
                    
                    with SUBMIT_LOCK:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đang tìm và nhấn nút Gửi/Đăng Ký (Sign up)...', Colors.INFO)}")
                        try:
                            click_result = driver.execute_script("""
                                let submitBtn = document.querySelector('button[type="submit"]');

                                if (!submitBtn) {
                                    const allClickables = Array.from(document.querySelectorAll('button, div[role="button"]'));
                                    submitBtn = allClickables.find(b => {
                                        const text = (b.innerText || b.textContent || "").trim().toLowerCase();
                                        return text === "submit" || text === "sign up" || text === "đăng ký" || text === "gửi" || text === "next" || text === "tiếp"
                                            || text.includes("submit") || text.includes("sign up") || text.includes("đăng ký");
                                    });
                                }

                                if (!submitBtn) {
                                    const spans = Array.from(document.querySelectorAll('span')).filter(s => {
                                        const t = s.innerText?.trim().toLowerCase() || "";
                                        return t === "submit" || t === "sign up" || t === "đăng ký" || t === "gửi" || t === "next" || t === "tiếp";
                                    });
                                    if (spans.length > 0) {
                                        let p = spans[0].closest('button, div[role="button"]');
                                        if (p) submitBtn = p;
                                    }
                                }

                                if (submitBtn) {
                                    submitBtn.disabled = false;
                                    submitBtn.removeAttribute('disabled');
                                    submitBtn.style.pointerEvents = 'auto';
                                    submitBtn.scrollIntoView({ block: 'center' });
                                    
                                    submitBtn.focus();
                                    submitBtn.click(); 

                                    ['mousedown', 'mouseup', 'click'].forEach(eventType => {
                                        var evt = new MouseEvent(eventType, {
                                            view: window,
                                            bubbles: true,
                                            cancelable: true,
                                            clientX: submitBtn.getBoundingClientRect().x + 20,
                                            clientY: submitBtn.getBoundingClientRect().y + 10
                                        });
                                        submitBtn.dispatchEvent(evt);
                                    });
                                    
                                    return "CLICKED";
                                }
                                
                                const form = document.querySelector('form');
                                if (form) {
                                    form.submit();
                                    return "FORM_SUBMITTED";
                                }

                                return "NOT_FOUND";
                            """)
                            
                            if click_result in ["CLICKED", "FORM_SUBMITTED"]:
                                print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ BẤM NÚT SUBMIT/GỬI THÀNH CÔNG (Bằng Script)!', Colors.SUCCESS)}")
                            else:
                                print(f"{Colors.color_text(f'[{self.thread_id}] JS không tìm thấy, thử click qua Selenium button[type=submit]...', Colors.WARNING)}")
                                try:
                                    btn_selenium = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                                    driver.execute_script("arguments[0].click();", btn_selenium)
                                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã click nút Submit qua Selenium thành công!', Colors.SUCCESS)}")
                                except Exception:
                                    print(f"{Colors.color_text(f'[{self.thread_id}] Không tìm thấy nút qua Selenium, fallback phím ENTER...', Colors.WARNING)}")
                                    try:
                                        user_inp.send_keys(Keys.ENTER)
                                        print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm ENTER thành công!', Colors.SUCCESS)}")
                                    except Exception:
                                        pass

                        except Exception as ex:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi khi chạy Script click nút: {ex}', Colors.WARNING)}")
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm gửi form, chờ load OTP (15s)...', Colors.SUCCESS)}")
                        time.sleep(15) 
                    
                except Exception as e:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi quá trình điền form: {e}', Colors.ERROR)}")
                    if self.mode == "7" and otptrust_service:
                        otptrust_service.cancel_order()
                    time.sleep(5)
                    return False

                # ==================== NHẬN DIỆN Ô NHẬP OTP ĐA LỚP ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Chờ giao diện nhập OTP...', Colors.INFO)}")
                otp_input = None
                locators = [
                    (By.NAME, "email_confirmation_code"),
                    (By.NAME, "confirmationCode"),
                    (By.XPATH, "//input[contains(@aria-label, 'Mã')]"),
                    (By.XPATH, "//input[contains(@aria-label, 'Code')]"),
                    (By.XPATH, "//input[@type='text']")
                ]
                time.sleep(3)
                
                for loc in locators:
                    try:
                        otp_input = WebDriverWait(driver, 3).until(EC.presence_of_element_located(loc))
                        if otp_input: break
                    except Exception:
                        pass
                
                if not otp_input:
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                        time.sleep(1)
                        otp_input = driver.execute_script("return document.querySelector('input');")
                    except Exception:
                        pass

                if not otp_input:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không thể tìm thấy ô nhập OTP trên giao diện.', Colors.ERROR)}")
                    if self.mode == "7" and otptrust_service:
                        otptrust_service.cancel_order()
                    time.sleep(5)
                    return False
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đã nhận diện được ô nhập OTP thành công!', Colors.SUCCESS)}")
                
                # ==================== CƠ CHẾ LẤY & NGÂM OTP ĐĂNG KÝ (6 SỐ) VỚI VÒNG LẶP RETRY ====================
                otp_code = None
                max_resend_attempts = 2 # 1 Lần thử gốc + 2 lần bấm gửi lại
                
                for attempt in range(max_resend_attempts + 1):
                    if STOP_EVENT.is_set(): return False
                    
                    start_otp_wait = time.time()
                    
                    if self.mode == "2" and not (mail_service and mail_service.token):
                        with OTP_LOCK:
                            PAUSE_FOR_INPUT.clear()
                            built_in_print(f"\n{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: MỜI SẾP NHẬP OTP CHO [{used_email}] TỪ BÀN PHÍM: ', Colors.SUCCESS)}", end="")
                            otp_code = input().strip()
                            PAUSE_FOR_INPUT.set()
                    else:
                        target_wait = 60 if self.mode in ["3", "4", "5", "6", "7"] else 0
                        if target_wait > 0:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: Bắt đầu quét OTP và ngâm form {target_wait}s...', Colors.INFO)}")
                        else:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: Đang chờ lấy mã OTP...', Colors.INFO)}")

                        timeout_per_attempt = 100 
                        if self.mode == "1" or (self.mode == "2" and mail_service and mail_service.token):
                            otp_code = mail_service.get_otp_code(timeout=timeout_per_attempt, force_8_digits=False)
                        elif self.mode in ["3", "4"]:
                            otp_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=timeout_per_attempt, force_8_digits=False)
                        elif self.mode == "5":
                            otp_code = hotmail_service.get_otp_code(timeout=100, force_8_digits=False) 
                        elif self.mode == "6" and autosms_service:
                            otp_code = autosms_service.get_otp_code(timeout=120)
                        elif self.mode == "7" and otptrust_service:
                            otp_code = otptrust_service.get_otp_code(timeout=100)
                    
                    if otp_code:
                        if self.mode in ["3", "4", "5", "6", "7"]:
                            elapsed = time.time() - start_otp_wait
                            remaining = target_wait - elapsed
                            if remaining > 0:
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã lấy được mã ({otp_code}) ở giây thứ {int(elapsed)}! Đang ngâm form đợi hết {target_wait}s...', Colors.WARNING)}")
                                for w in range(int(remaining), 0, -5):
                                    if STOP_EVENT.is_set(): return False
                                    print(f"{Colors.color_text(f'[{self.thread_id}] Thời gian ngâm OTP còn lại: {w}s...', Colors.INFO)}")
                                    time.sleep(min(5, w))
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã ngâm đủ {target_wait}s. Chuẩn bị điền mã OTP!', Colors.SUCCESS)}")
                        break 
                    
                    if attempt < max_resend_attempts:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1} không thấy mã. Tiến hành click yêu cầu Gửi lại mã...', Colors.WARNING)}")
                        
                        clicked_didnt_receive = driver.execute_script("""
                            let btns = Array.from(document.querySelectorAll('button, div[role="button"], a, span'));
                            for (let b of btns) {
                                let txt = (b.innerText || b.textContent || "").trim().toLowerCase();
                                if (txt.includes('không nhận được mã') || txt.includes("didn't receive") || txt.includes("did not receive") || txt.includes('lấy mã mới') || txt.includes('get a new code')) {
                                    let clickable = b.closest('button, [role="button"], a') || b;
                                    clickable.click();
                                    return true;
                                }
                            }
                            return false;
                        """)
                        
                        if clicked_didnt_receive:
                            time.sleep(3) 
                            clicked_resend = driver.execute_script("""
                                let btns = Array.from(document.querySelectorAll('button, div[role="button"], a, span'));
                                for (let b of btns) {
                                    let txt = (b.innerText || b.textContent || "").trim().toLowerCase();
                                    if (txt.includes('gửi lại') || txt.includes('resend') || txt.includes('lấy mã mới') || txt.includes('new code')) {
                                        let clickable = b.closest('button, [role="button"], a') || b;
                                        clickable.click();
                                        return true;
                                    }
                                }
                                return false;
                            """)
                            if clicked_resend:
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã yêu cầu GỬI LẠI MÃ thành công. Chờ thư/sim mới...', Colors.INFO)}")
                                time.sleep(5)
                            else:
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm nút yêu cầu mã mới, tiếp tục quét hộp thư...', Colors.INFO)}")
                                time.sleep(5)
                        else:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không tìm thấy nút \"Tôi không nhận được mã\"!', Colors.ERROR)}")

                if not otp_code:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Đã thử Gửi lại {max_resend_attempts} lần nhưng vẫn KHÔNG CÓ MÃ. Báo Mail/Sim Die và bỏ qua acc!', Colors.ERROR)}")
                    if self.mode == "6" and autosms_service:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đang hoàn tiền đơn thuê sim...', Colors.INFO)}")
                        autosms_service.cancel_order()
                    elif self.mode == "7" and otptrust_service:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đang hủy đơn và hoàn tiền trên OTPTRUST...', Colors.INFO)}")
                        otptrust_service.cancel_order()
                    time.sleep(5)
                    return False

                # ==================== TIẾN HÀNH ĐIỀN MÃ LÊN WEB ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Bắt đầu điền mã OTP: {otp_code} vào trang Web...', Colors.SUCCESS)}")
                
                try:
                    fresh_input = None
                    for loc in locators:
                        try:
                            els = driver.find_elements(*loc)
                            for el in els:
                                if el.is_displayed():
                                    fresh_input = el
                                    break
                            if fresh_input: break
                        except Exception:
                            pass
                    
                    target_input = fresh_input if fresh_input else otp_input
                    
                    try:
                        human_type_react(driver, self.thread_id, target_input, otp_code, is_username=False)
                    except Exception:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Selenium bị chặn, đang ép điền mã bằng JavaScript...', Colors.WARNING)}")
                        set_react_input_value(driver, target_input, otp_code)
                except Exception as ex:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi nghiêm trọng lúc điền ({ex}), dùng JS quét toàn cục...', Colors.WARNING)}")
                    fill_otp_into_active_inputs(driver, otp_code)
                    
                time.sleep(1.5)
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang tiến hành Gửi mã OTP...', Colors.INFO)}")
                time.sleep(2)

                click_success = False

                try:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Thử submit bằng phím ENTER...', Colors.INFO)}")
                    target_input.send_keys(Keys.ENTER)
                    click_success = True
                    time.sleep(1)
                except Exception:
                    pass

                if not click_success:
                    try:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Thử click nút Tiếp tục bằng Selenium...', Colors.INFO)}")
                        btn_xpath = "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tiếp tục') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next') or @type='submit']"
                        submit_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", submit_btn)
                        click_success = True
                    except Exception:
                        pass

                if not click_success:
                    try:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Thử click bằng vòng lặp JavaScript...', Colors.WARNING)}")
                        click_result = driver.execute_script("""
                            const btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                            for (let b of btns) {
                                const text = (b.innerText || b.textContent || "").trim().toLowerCase();
                                if (text === "tiếp tục" || text === "next" || text === "confirm" || b.type === "submit") {
                                    b.disabled = false;
                                    b.removeAttribute('disabled');
                                    b.click();
                                    return "CLICKED";
                                }
                            }
                            return "NOT_FOUND";
                        """)
                        if click_result == "CLICKED": click_success = True
                    except Exception:
                        pass

                if click_success:
                    print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ BẤM GỬI OTP THÀNH CÔNG!', Colors.SUCCESS)}")
                else:
                    print(f"{Colors.color_text(f'[{self.thread_id}] KHÔNG THỂ BẤM NÚT, trình duyệt có thể bị treo.', Colors.ERROR)}")

                # ==================== CHỜ TẢI TRANG CHỦ & KIỂM TRA ACC DIE ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Chờ IG xử lý OTP và load trang chủ (40s để tránh lag mạng)...', Colors.INFO)}")
                time.sleep(40)
                
                # 1. KIỂM TRA SỚM ĐỂ XÁC ĐỊNH ACC SỐNG/CHẾT TRƯỚC KHI UP AVATAR
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang kiểm tra xem acc có bị Checkpoint/Die không...', Colors.INFO)}")
                cookies_list = driver.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies_list}
                
                current_url = driver.current_url.lower()
                page_source = driver.page_source.lower()
                
                is_dead = False
                if "challenge" in current_url or "suspended" in current_url:
                    is_dead = True
                elif "tài khoản của bạn đã bị tạm ngưng" in page_source or "we suspended your account" in page_source:
                    is_dead = True
                elif not cookie_dict.get('sessionid') or not cookie_dict.get('ds_user_id'):
                    is_dead = True
                    
                if is_dead:
                    print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                    print(f"{Colors.color_text(f'[{self.thread_id}] LỖI: TÀI KHOẢN ĐÃ DIE / CHECKPOINT!', Colors.ERROR)}")
                    print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                    return "DEAD" 

                print(f"{Colors.color_text(f'[{self.thread_id}] TÀI KHOẢN SỐNG! Chuẩn bị up Avatar...', Colors.SUCCESS)}")

                # --- 2. LOGIC UP AVATAR DESKTOP ---
                if self.avatar_folder and os.path.exists(self.avatar_folder):
                    images = [f for f in os.listdir(self.avatar_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                    if images:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Bắt đầu quy trình up Avatar từ URL trang cá nhân...', Colors.INFO)}")
                        try:
                            image_path = os.path.abspath(os.path.join(self.avatar_folder, random.choice(images)))
                            
                            driver.get(f"https://www.instagram.com/{username}/")
                            time.sleep(8)
                            
                            if "challenge" in driver.current_url.lower() or "suspended" in driver.current_url.lower():
                                print(f"{Colors.color_text(f'[{self.thread_id}] Acc vừa die (Checkpoint) khi truy cập profile! Bỏ qua up avatar.', Colors.ERROR)}")
                            else:
                                driver.execute_script("""
                                    if (!window.hookedFileClick) {
                                        window.originalClick = window.HTMLInputElement.prototype.click;
                                        window.HTMLInputElement.prototype.click = function() {
                                            if (this.type === 'file') {
                                                this.style.display = 'block';
                                                this.style.opacity = '1';
                                                this.style.visibility = 'visible';
                                                this.style.position = 'fixed';
                                                this.style.top = '0';
                                                this.style.left = '0';
                                                this.style.zIndex = '99999';
                                            } else {
                                                window.originalClick.call(this);
                                            }
                                        };
                                        window.hookedFileClick = true;
                                    }

                                    let header = document.querySelector('header');
                                    if (header) {
                                        let btns = header.querySelectorAll('button, div[role="button"]');
                                        if (btns.length > 0) {
                                            btns[0].click(); 
                                        }
                                    }
                                """)
                                time.sleep(3)
                                
                                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                                
                                if file_inputs:
                                    file_inputs[-1].send_keys(image_path) 
                                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã chèn file ảnh avatar thành công! Chờ 10s để IG lưu ảnh...', Colors.SUCCESS)}")
                                    time.sleep(10) 
                                else:
                                    print(f"{Colors.color_text(f'[{self.thread_id}] Không tìm thấy khung upload ảnh trên trang cá nhân.', Colors.WARNING)}")
                                    
                        except Exception as e:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi trong quá trình up avatar: {e}', Colors.WARNING)}")
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Thư mục avatar trống, không có ảnh nào để up.', Colors.WARNING)}")
                else:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Không cấu hình Up Avatar, bỏ qua bước này.', Colors.INFO)}")

                # ==================== CẬP NHẬT MỐC HỘP THƯ & TỰ ĐỘNG BẬT 2FA ====================
                if self.mode in ["3", "4"] and imap_service:
                    uid_moc = imap_service.get_latest_uid()
                elif self.mode == "5" and hotmail_service:
                    hotmail_service.init_baseline()

                two_fa_secret = setup_instagram_2fa(
                    driver=driver,
                    thread_id=self.thread_id,
                    username=username,
                    used_email=used_email,
                    mode=self.mode,
                    mail_service=mail_service,
                    imap_service=imap_service,
                    hotmail_service=hotmail_service,
                    autosms_service=autosms_service,
                    uid_moc=uid_moc
                )

                # ==================== LẤY LẠI COOKIE LẦN CUỐI & LƯU ACC ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang tiến hành lấy Cookie lưu tài khoản...', Colors.INFO)}")
                
                cookies_list = driver.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies_list}
                
                cookie_str = (
                    f"datr={cookie_dict.get('datr', '')}; "
                    f"ig_did={cookie_dict.get('ig_did', '')}; "
                    f"mid={cookie_dict.get('mid', '')}; "
                    f"wd={cookie_dict.get('wd', '1920x1080')}; "
                    f"dpr={cookie_dict.get('dpr', '1')}; "
                    f"csrftoken={cookie_dict.get('csrftoken', '')}; "
                    f"ds_user_id={cookie_dict.get('ds_user_id', '')}; "
                    f"sessionid={cookie_dict.get('sessionid', '')}; "
                    f"rur={cookie_dict.get('rur', '')}"
                )
                
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{self.thread_id}] THÀNH CÔNG ACC {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}Email/SĐT: {Colors.EMAIL}{used_email}{Colors.RESET}")
                print(f"{Colors.KEY}Pass: {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
                print(f"{Colors.KEY}User: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}2FA:  {Colors.WARNING}{two_fa_secret if two_fa_secret else 'Bỏ qua / Không có'}{Colors.RESET}")
                print(f"{Colors.KEY}Cookie: {Colors.VALUE}{cookie_str if cookie_str else 'Trống'}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                
                save_account(self.thread_id, used_email, secure_pass, username, full_name, f"mode_{self.mode}", cookie_str, two_fa_secret)
                
                return True
                
            except Exception as e:
                print(f"{Colors.color_text(f'[{self.thread_id}] Gặp Lỗi Ngoại Lệ: {e}', Colors.ERROR)}")
                return False
        
        success_count = 0
        for i in range(1, self.account_count + 1):
            if STOP_EVENT.is_set(): break
            
            status = create_one_account(i)
            
            if status == True: 
                success_count += 1
            elif status == "DEAD":
                print(f"{Colors.color_text(f'[{self.thread_id}] Dừng luồng này vì acc đã Die, bảo toàn các tài nguyên còn lại!', Colors.WARNING)}")
                break 
            else:
                print(f"{Colors.color_text(f'[{self.thread_id}] Dừng luồng do lỗi quá trình tạo, bảo toàn tài nguyên!', Colors.WARNING)}")
                break 
                
            time.sleep(random.uniform(5, 10))
        
        print(f"\n{Colors.color_text(f'[{self.thread_id}] TỔNG KẾT TAB: {success_count}/{self.account_count} THÀNH CÔNG', Colors.TITLE)}")


# ==================== MENU CHÍNH ====================
def select_mode():
    built_in_print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list thường (Có Mail.tm thì Tự động) ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Biến thể ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}5. {Colors.VALUE}HOTMAIL/OUTLOOK     \033[97m[ Dùng API Smail1s.com ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}6. {Colors.VALUE}THUÊ SỐ ĐIỆN THOẠI  \033[97m[ Dùng API AutoSMS.site ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}7. {Colors.VALUE}THUÊ EMAIL OTPTRUST \033[97m[ Dùng API Otptrust.com - Tự thuê & lấy OTP ]{Colors.RESET}")
    while True:
        built_in_print(f"{Colors.KEY}Nhập lựa chọn [1-7]: {Colors.RESET}", end="")
        choice = input().strip()
        if choice in ["1", "2", "3", "4", "5", "6", "7"]: return choice


def process_file_input(config_key, default_prompt):
    config_data = load_config()
    saved_file = config_data.get(config_key)
    file_path = ""

    if saved_file and os.path.isfile(saved_file):
        built_in_print(f"{Colors.INFO}Phát hiện tệp danh sách cũ: {Colors.VALUE}{saved_file}{Colors.RESET}")
        use_old = input(f"{Colors.KEY}Bạn có muốn sử dụng lại tệp này không? (y/n): {Colors.RESET}").strip().lower()
        if use_old == 'y':
            file_path = saved_file

    if not file_path:
        built_in_print(default_prompt, end="")
        file_path = input().strip().strip('"')
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
                built_in_print(f"{Colors.WARNING}Gợi ý: Nếu không có sẵn file Email, hãy chạy Mode 1 (Tự động tạo email tạm thời).{Colors.RESET}")
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

        start_idx = int(start_line) if start_line.isdigit() else 1
        end_idx = int(end_line) if end_line.isdigit() else total

        start_idx = max(1, start_idx)
        end_idx = min(total, end_idx)

        if start_idx > end_idx:
            built_in_print(f"{Colors.WARNING}Số thứ tự không hợp lệ, sẽ tự động chạy tất cả!{Colors.RESET}")
            return lines
        else:
            selected_lines = lines[start_idx-1:end_idx]
            built_in_print(f"{Colors.INFO}=> Đã chọn {len(selected_lines)} data (Từ số {start_idx} đến {end_idx}){Colors.RESET}")
            return selected_lines
    else:
        return [e.strip() for e in file_path.split(",") if e.strip()]


if __name__ == "__main__":
    banner()
    config_data = load_config()
    mode = select_mode()
    
    data_source = []
    base_gmail = None
    app_password = None
    manual_password = None
    api_mode = None
    autosms_api_key = None
    autosms_country = "vn"
    otptrust_api_key = None
    otptrust_provider = "auto"
    otptrust_service_id = None

    if mode == "1":
        pass 
        
    elif mode == "2":
        prompt_txt = f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}" 
        data_source = process_file_input("last_file_mode2", prompt_txt)
        if any("mail.tm" in e.lower() for e in data_source):
            built_in_print(f"{Colors.KEY}Nhập mật khẩu chung cho Mail.tm (Để trống dùng TempPass123!): {Colors.RESET}", end="")
            manual_password = input().strip()
            
    elif mode == "3":
        prompt_txt = f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}"
        raw_list = process_file_input("last_file_mode3", prompt_txt)
        for line in raw_list:
            parts = re.split(r'[|:]', line.strip())
            if len(parts) >= 2: data_source.append((parts[0].strip(), parts[1].strip()))
        if not data_source: sys.exit()

    elif mode == "4":
        built_in_print(f"{Colors.KEY}Nhập Gmail gốc (VD: test@gmail.com): {Colors.RESET}", end="")
        base_gmail = input().strip()
        built_in_print(f"{Colors.KEY}Nhập App Password: {Colors.RESET}", end="")
        app_password = input().strip()
        data_source = generate_dot_variants(base_gmail)

    elif mode == "5":
        built_in_print("1. OAuth | 2. Graph API | 3. Roundcube\n>> ", end="")
        c = input().strip()
        api_mode = "oauth" if c=="1" else "graph" if c=="2" else "roundcube"
        prompt_txt = f"{Colors.KEY}Nhập đường dẫn file/list Hotmail: {Colors.RESET}"
        data_source = process_file_input("last_file_mode5", prompt_txt)

    elif mode == "6":
        built_in_print(f"{Colors.KEY}Nhập API Key của web Autosms.site: {Colors.RESET}", end="")
        autosms_api_key = input().strip()
        built_in_print(f"{Colors.KEY}Nhập Mã Quốc Gia thuê sim (VD: vn, us, kh - Bỏ trống mặc định là vn): {Colors.RESET}", end="")
        autosms_country = input().strip()
        if not autosms_country: autosms_country = "vn"
        data_source = ["dummy_for_sms"] * 999999

    elif mode == "7":
        saved_otptrust_key = config_data.get("otptrust_api_key", "")
        if saved_otptrust_key:
            masked_key = saved_otptrust_key[:6] + "..." + saved_otptrust_key[-4:] if len(saved_otptrust_key) > 10 else saved_otptrust_key
            built_in_print(f"{Colors.INFO}Phát hiện API Key OTPTRUST đã lưu: {Colors.VALUE}{masked_key}{Colors.RESET}")
            use_old_key = input(f"{Colors.KEY}Bạn có muốn dùng lại API Key này không? (y/n): {Colors.RESET}").strip().lower()
            if use_old_key == 'y':
                otptrust_api_key = saved_otptrust_key

        if not otptrust_api_key:
            built_in_print(f"{Colors.KEY}Nhập API Key của web Otptrust.com: {Colors.RESET}", end="")
            otptrust_api_key = input().strip()
            if otptrust_api_key:
                config_data["otptrust_api_key"] = otptrust_api_key
                save_config(config_data)

        built_in_print(f"{Colors.KEY}Chọn loại hộp thư (hotmail / outlook / gmail / icloud - Nhấn Enter để tự động chọn loại còn hàng): {Colors.RESET}", end="")
        prov_in = input().strip().lower()
        otptrust_provider = prov_in if prov_in in ["hotmail", "outlook", "gmail", "icloud"] else "auto"

        built_in_print(f"{Colors.KEY}Nhập Service ID của Instagram trên OTPTRUST (Nhấn Enter để tool tự động dò ID): {Colors.RESET}", end="")
        sid_in = input().strip()
        otptrust_service_id = int(sid_in) if sid_in.isdigit() else None
        data_source = ["dummy_for_otptrust"] * 999999

    if not data_source and mode not in ["1", "4", "6", "7"]:
        built_in_print(f"{Colors.ERROR}Danh sách đầu vào trống! Thoát chương trình.{Colors.RESET}")
        sys.exit()
        
    saved_avatar_folder = config_data.get("last_avatar_folder", "")
    avatar_folder_input = ""

    if saved_avatar_folder and os.path.isdir(saved_avatar_folder):
        built_in_print(f"\n{Colors.INFO}Phát hiện thư mục Avatar cũ: {Colors.VALUE}{saved_avatar_folder}{Colors.RESET}")
        use_old_avatar = input(f"{Colors.KEY}Bạn có muốn dùng lại thư mục này không? (y/n): {Colors.RESET}").strip().lower()
        if use_old_avatar == 'y':
            avatar_folder_input = saved_avatar_folder

    if not avatar_folder_input:
        built_in_print(f"\n{Colors.KEY}Nhập đường dẫn thư mục chứa ảnh làm Avatar (Bỏ trống nếu không muốn up): {Colors.RESET}", end="")
        avatar_folder_input = input().strip()
        avatar_folder_input = avatar_folder_input.strip('"').strip("'")
        
        if avatar_folder_input and os.path.isdir(avatar_folder_input):
            config_data["last_avatar_folder"] = avatar_folder_input
            save_config(config_data)

    built_in_print(f"\n{Colors.KEY}Nhập đường dẫn file Proxy (.txt) (Hỗ trợ định dạng: IP:Port, IP:Port:User:Pass, User:Pass@IP:Port): {Colors.RESET}", end="")
    proxy_file_input = input().strip().strip('"').strip("'")
    proxies_list = []
    if proxy_file_input and os.path.isfile(proxy_file_input):
        with open(proxy_file_input, 'r', encoding='utf-8') as f_proxy:
            proxies_list = [line.strip() for line in f_proxy if line.strip()]
        built_in_print(f"{Colors.SUCCESS}Đã tải {len(proxies_list)} Proxy từ tệp.{Colors.RESET}")

    built_in_print(f"\n{Colors.KEY}Nhập số luồng (số tab Chrome chạy cùng lúc): {Colors.RESET}", end="")
    threads_count = int(input().strip())
    
    built_in_print(f"{Colors.KEY}Nhập số tài khoản cần tạo MỖI LUỒNG: {Colors.RESET}", end="")
    accs_per_thread = int(input().strip())
    
    threads = []
    for i in range(threads_count):
        t = starts(
            i + 1,
            mode,
            accs_per_thread,
            data_source,
            manual_password,
            base_gmail,
            app_password,
            api_mode,
            avatar_folder_input,
            proxies_list,
            autosms_api_key,
            autosms_country,
            otptrust_api_key,
            otptrust_provider,
            otptrust_service_id
        )
        threads.append(t)
        
    for t in threads: t.start()
    
    try:
        # CHỜ TẤT CẢ CÁC LUỒNG CHẠY XONG XUÔI HẾT MỚI ĐI TIẾP
        for t in threads: t.join()
        
        built_in_print(f"\n{Colors.LINE}={'='*68}{Colors.RESET}")
        built_in_print(f"{Colors.color_text('AUTO ĐÃ HOÀN THÀNH TOÀN BỘ NHIỆM VỤ!', Colors.SUCCESS)}")
        built_in_print(f"{Colors.TITLE}TIẾN HÀNH RÀ SOÁT VÀ ĐÓNG TRÌNH DUYỆT CỦA TỪNG TAB:{Colors.RESET}")
        
        # --- HỎI TẮT TRÌNH DUYỆT TẠI ĐÂY ---
        for tid, drv in ALL_DRIVERS:
            try:
                drv.title # Test xem Chrome có lỡ tay bị tắt trước đó chưa
                while True:
                    built_in_print(f"{Colors.WARNING}[{tid}] Bạn có muốn đóng Chrome của luồng này không? (y/n): {Colors.RESET}", end="")
                    choice = input().strip().lower()
                    if choice == 'y':
                        try: drv.quit()
                        except Exception: pass
                        built_in_print(f"{Colors.SUCCESS}>> Đã đóng trình duyệt của {tid}.{Colors.RESET}")
                        break
                    elif choice == 'n':
                        built_in_print(f"{Colors.INFO}>> Đã giữ lại trình duyệt của {tid}.{Colors.RESET}")
                        break
                    else:
                        built_in_print(f"{Colors.ERROR}Vui lòng chỉ nhập y hoặc n!{Colors.RESET}")
            except Exception: 
                pass # Đã bị tắt tay từ trước
                
        built_in_print(f"\n{Colors.SUCCESS}TOOL ĐÃ KẾT THÚC CÔNG VIỆC!{Colors.RESET}")
        built_in_print(f"{Colors.KEY}Nhấn Enter để thoát chương trình...{Colors.RESET}", end="")
        input()
        
    except KeyboardInterrupt:
        STOP_EVENT.set() 
        built_in_print(f"\n{Colors.ERROR}Đang buộc dừng các luồng...{Colors.RESET}")
        sys.exit(0)
