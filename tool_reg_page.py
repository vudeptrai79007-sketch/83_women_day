# -*- coding: utf-8 -*-
"""
================================================================================
TOOL ALL-IN-ONE: AUTO LOGIN -> REG PAGE PRO5 -> CHECK LIVE -> BẮN ADMIN (MTOOL CORE)
Quy trình chuẩn cho từng Acc:
0. Tự động Login lấy Token nếu nạp định dạng UID|Pass|2FA (Hoặc dùng luôn Token nếu nạp EAAAAU).
1. Kiểm tra Tài khoản (Nick Reg) & lưu danh sách Page cũ.
2. Tạo Page Pro5 (Hiện rõ Bước 1: Submit Tên -> Bước 2: Submit Danh mục).
3. Tạo xong -> Quét & GET LUÔN TOKEN PAGE vừa tạo (Page ID + Page Token EAAAAU).
4. Đợi đếm ngược 20s -> Check lại xem Tài khoản & Page vừa tạo còn SỐNG (LIVE) không.
5. Nếu SỐNG -> Dùng thuật toán MTOOL MAX (Bloks) bắn lời mời Admin sang UID Nick Mẹ.
================================================================================
"""

import os
import sys
import re
import time
import json
import uuid
import random
import base64
import hmac
import hashlib
import struct
import datetime
import urllib.parse
import threading
from collections import deque
from queue import Queue, Empty
from typing import Optional, Dict, Any, List

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    print("Vui lòng cài đặt requests bằng lệnh: pip install requests urllib3")
    sys.exit(1)

# ==============================================================================
# 1. CẤU HÌNH MÀU SẮC TERMINAL & NHẬT KÝ TIẾN TRÌNH (LIVE LOGS)
# ==============================================================================

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"

if sys.platform == "win32":
    os.system("color")

PRINT_LOCK = threading.Lock()
FILE_LOCK = threading.Lock()
LOG_LOCK = threading.Lock()

# Lưu 18 dòng nhật ký chi tiết gần nhất để hiển thị trực tiếp dưới bảng theo dõi
LIVE_PROCESS_LOGS = deque(maxlen=18)

def safe_print(msg: str):
    """In ra màn hình an toàn đa luồng."""
    with PRINT_LOCK:
        print(msg)
        sys.stdout.flush()

def add_process_log(acc_id: int, uid: str, msg: str):
    """Ghi nhật ký từng bước tạo Page, get Token Page, check Live và bắn UID."""
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    short_uid = (uid or "Unknown")[:15]
    log_line = f"[{now_str}] [Acc #{acc_id:02d} | {short_uid}] {msg}"
    with LOG_LOCK:
        LIVE_PROCESS_LOGS.append(log_line)

def clear_screen():
    os.system("cls" if sys.platform == "win32" else "clear")

def print_banner():
    clear_screen()
    safe_print(f"{Colors.CYAN}{Colors.BOLD}")
    safe_print("=" * 110)
    safe_print("   TOOL ALL-IN-ONE: AUTO LOGIN -> REG PAGE PRO5 -> GET TOKEN PAGE -> BẮN LỜI MỜI ADMIN (MTOOL CORE)   ")
    safe_print("          Chuẩn Katana FB4A Android | Hiện Chi Tiết Từng Bước | Vượt Lỗi Unsupported          ")
    safe_print("=" * 110)
    safe_print(f"{Colors.RESET}")

def input_multiline(prompt: str) -> List[str]:
    """Hỗ trợ dán trực tiếp nhiều dòng trên điện thoại và PC."""
    safe_print(prompt)
    safe_print(f"{Colors.YELLOW}(Dán nội dung vào đây. Dán xong nhấn Enter 2 lần để xác nhận):{Colors.RESET}")
    lines = []
    empty_count = 0
    while True:
        try:
            line = input()
            if not line.strip():
                empty_count += 1
                if empty_count >= 1 and lines:
                    break
                elif empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line.strip())
        except (EOFError, KeyboardInterrupt):
            break
    return lines


# ==============================================================================
# 2. XỬ LÝ PROXY THÔNG MINH (HỖ TRỢ MỌI LOẠI PROXY)
# ==============================================================================

def parse_proxy(proxy_str: Optional[str]) -> Optional[Dict[str, str]]:
    if not proxy_str or not str(proxy_str).strip():
        return None
    p = str(proxy_str).strip()

    if p.startswith(("http://", "https://", "socks5://", "socks4://")):
        scheme, rest = p.split("://", 1)
        if "@" in rest:
            auth, host_port = rest.rsplit("@", 1)
            auth_str = f"{auth}@"
        else:
            auth_str = ""
            host_port = rest

        if not host_port.startswith("[") and host_port.count(":") >= 2:
            hp_parts = host_port.rsplit(":", 1)
            if len(hp_parts) == 2 and hp_parts[1].isdigit():
                host_port = f"[{hp_parts[0]}]:{hp_parts[1]}"
        formatted = f"{scheme}://{auth_str}{host_port}"
        return {"http": formatted, "https": formatted}

    if "@" in p:
        auth, host_port = p.rsplit("@", 1)
        if not host_port.startswith("[") and host_port.count(":") >= 2:
            hp_parts = host_port.rsplit(":", 1)
            if len(hp_parts) == 2 and hp_parts[1].isdigit():
                host_port = f"[{hp_parts[0]}]:{hp_parts[1]}"
        formatted = f"http://{auth}@{host_port}"
        return {"http": formatted, "https": formatted}

    m_bracket = re.match(r"^\[([a-fA-F0-9:]+)\]:(\d+)(?::([^:]+):(.+))?$", p)
    if m_bracket:
        ipv6, port, user, pwd = m_bracket.groups()
        if user and pwd:
            formatted = f"http://{user}:{pwd}@[{ipv6}]:{port}"
        else:
            formatted = f"http://[{ipv6}]:{port}"
        return {"http": formatted, "https": formatted}

    parts = p.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        return {"http": f"http://{parts[0]}:{parts[1]}", "https": f"http://{parts[0]}:{parts[1]}"}
    if len(parts) == 4 and parts[1].isdigit() and parts[0].count(".") == 3:
        ip, port, user, pwd = parts
        formatted = f"http://{user}:{pwd}@{ip}:{port}"
        return {"http": formatted, "https": formatted}

    formatted = f"http://{p}"
    return {"http": formatted, "https": formatted}


# ==============================================================================
# 3. KHO USER-AGENT KATANA FB4A CHUẨN HAR
# ==============================================================================

DEVICE_POOL = [
    ('Samsung', 'samsung', 'Galaxy S24 Ultra', 'SM-S928B', 3.5, 1440, 3120, 14, 14),
    ('Samsung', 'samsung', 'Galaxy S23 Ultra', 'SM-S918B', 3.5, 1440, 3088, 13, 14),
    ('Samsung', 'samsung', 'Galaxy S22 Ultra', 'SM-S908B', 3.5, 1440, 3088, 12, 14),
    ('Samsung', 'samsung', 'Galaxy S21 5G', 'SM-G991B', 3.0, 1080, 2400, 11, 14),
    ('Samsung', 'samsung', 'Galaxy Note 20 Ultra', 'SM-N986B', 3.5, 1440, 3088, 10, 13),
    ('Xiaomi', 'xiaomi', 'Xiaomi 13', '2211133G', 3.0, 1080, 2400, 13, 14),
    ('Xiaomi', 'xiaomi', 'Xiaomi 12T', '22071212AG', 3.25, 1220, 2712, 12, 14),
    ('Xiaomi', 'xiaomi', 'Redmi Note 12 Pro', '22101316G', 3.0, 1080, 2400, 12, 14),
    ('Google', 'google', 'Pixel 8 Pro', 'Pixel 8 Pro', 3.5, 1344, 2992, 14, 14),
]

FBAV_VERSIONS = [
    ('510.0.0.72.41', '725719471'),
    ('543.0.0.55.73', '846638243'),
    ('540.0.0.42.50', '838765431'),
    ('535.0.0.40.114', '825638102'),
]

CARRIERS = ['Viettel', 'Vinaphone', 'MobiFone', 'Vietnamobile']
LOCALES = ['vi_VN', 'en_US']

def generate_random_katana_ua(seed: Optional[str] = None) -> str:
    if seed:
        seed_int = int(hashlib.md5(str(seed).encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed_int)
    else:
        rng = random.Random()

    mfg, brand, model_name, dev_code, density, w, h, amin, amax = rng.choice(DEVICE_POOL)
    android_ver = rng.randint(amin, amax)
    fbav, fbbv = rng.choice(FBAV_VERSIONS)
    carrier = rng.choice(CARRIERS)
    locale = rng.choice(LOCALES)

    ua = (
        f"[FBAN/FB4A;FBAV/{fbav};FBBV/{fbbv};FBDM/{{density={density},width={w},height={h}}};"
        f"FBLC/{locale};FBRV/0;FBCR/{carrier};FBMF/{mfg.lower()};FBBD/{brand};FBPN/com.facebook.katana;"
        f"FBDV/{dev_code};FBSV/{android_ver};FBOP/1;FBCA/x86_64:arm64-v8a;]"
    )
    return ua

# ==============================================================================
# 4. KHO TÊN VIỆT THUẦN & TÊN US / QUỐC TẾ
# ==============================================================================

HO_VIET = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
DEM_NAM = ["Văn", "Đức", "Đình", "Hữu", "Tuấn", "Minh", "Quốc", "Thanh", "Trọng", "Duy", "Bảo", "Quang", "Hải"]
DEM_NU = ["Thị", "Ngọc", "Thu", "Thanh", "Khánh", "Phương", "Kim", "Ánh", "Hải", "Hồng", "Bảo", "Mỹ", "Quỳnh"]
TEN_NAM = ["Nam", "Tuấn", "Anh", "Khải", "Dũng", "Quân", "Cường", "Đạt", "Huy", "Hoàng", "Phong", "Long", "Sơn"]
TEN_NU = ["Linh", "Trang", "Hằng", "Mai", "Thảo", "Hương", "Anh", "Vy", "Hà", "Ngọc", "Châu", "Nhi", "Trâm"]

def generate_vietnamese_name() -> str:
    ho = random.choice(HO_VIET)
    if random.choice([True, False]):
        return f"{ho} {random.choice(DEM_NAM)} {random.choice(TEN_NAM)}"
    else:
        return f"{ho} {random.choice(DEM_NU)} {random.choice(TEN_NU)}"

def generate_us_name() -> str:
    return f"John {random.randint(100, 9999)}"

def get_page_name(name_type: str = "viet", custom_names: Optional[List[str]] = None) -> str:
    if name_type == "custom" and custom_names:
        return random.choice(custom_names).strip()
    elif name_type == "us":
        return generate_us_name()
    else:
        return generate_vietnamese_name()

# ==============================================================================
# 5. BỘ LỌC TỰ ĐỘNG BÓC TÁCH HYBRID (TOKEN EAAAAU HOẶC UID|PASS|2FA)
# ==============================================================================

def parse_hybrid_line(line: str) -> Optional[Dict[str, Any]]:
    """Tự động phân loại dòng nạp vào là Token hay Account (UID|Pass|2FA)"""
    raw = str(line).strip()
    if not raw or raw.startswith("#"):
        return None

    # TH1: Nếu chuỗi chứa EAAAAU -> Coi như nạp Token
    tok_match = re.search(r'(EAAAAU[A-Za-z0-9]+)', raw)
    if tok_match:
        token = tok_match.group(1).strip()
        uid = ""
        u_match = re.search(r'\b(1000\d{10,12}|615\d{11,13}|\d{8,16})\b', raw)
        if u_match:
            uid = u_match.group(1)
        pwd = ""
        parts = raw.split("|")
        # Thử tìm pass nếu format là UID|Pass|Token...
        if len(parts) >= 3 and parts[0] == uid and not parts[1].startswith("EAAAAU"):
            pwd = parts[1]
        px = next((p for p in parts if parse_proxy(p)), None)
        return {"type": "token", "uid": uid, "pwd": pwd, "token": token, "proxy": px, "raw": raw}

    # TH2: Không có EAAAAU -> Coi như nạp Account (UID|Pass|2FA|Cookie|Proxy)
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) >= 2 and parts[0].isdigit():
        uid, pwd = parts[0], parts[1]
        twofa = ""
        px = None
        for p in parts[2:]:
            if len(p.replace(" ", "")) in [16, 24, 32] or (len(p) == 6 and p.isdigit()):
                twofa = p
            elif parse_proxy(p):
                px = p
        return {"type": "account", "uid": uid, "pwd": pwd, "twofa": twofa, "token": "", "proxy": px, "raw": raw}

    return None

def parse_hybrid_lines(lines: List[str]) -> List[Dict[str, Any]]:
    results = []
    for line in lines:
        it = parse_hybrid_line(line)
        if it:
            results.append(it)
    return results

def parse_holder_uid(line: str) -> Optional[str]:
    raw = str(line).strip()
    if not raw or raw.startswith("#"): return None
    uid_match = re.search(r'\b(\d{5,20})\b', raw)
    if not uid_match: return None
    return uid_match.group(1)

def parse_account_line(line: str) -> Optional[Dict[str, str]]:
    raw = str(line).strip()
    if not raw or raw.startswith("#"): return None
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 2: return None
    uid, pwd = parts[0], parts[1]
    twofa, cookie, proxy = "", "", None
    for p in parts[2:]:
        if len(p.replace(" ", "")) in [16, 24, 32] or (len(p) == 6 and p.isdigit()):
            twofa = p
        elif "c_user=" in p:
            cookie = p
        elif ":" in p and parse_proxy(p):
            proxy = p
    return {"uid": uid, "pwd": pwd, "twofa": twofa, "cookie": cookie, "proxy": proxy, "raw": raw}

# ==============================================================================
# 6. TỰ SINH MÃ 2FA TOTP THUẦN PYTHON & GET TOKEN EAAAAU TỪ ACC
# ==============================================================================

def generate_totp_code(secret: str) -> str:
    clean_secret = secret.replace(" ", "").upper()
    if len(clean_secret) == 6 and clean_secret.isdigit(): return clean_secret
    missing = len(clean_secret) % 8
    if missing != 0: clean_secret += "=" * (8 - missing)
    try:
        key = base64.b32decode(clean_secret, casefold=True)
        intervals_no = int(time.time()) // 30
        msg = struct.pack(">Q", intervals_no)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[19] & 15
        h_code = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
        return f"{h_code:06d}"
    except Exception:
        return ""

def login_and_get_token(acc: Dict[str, Any], custom_ua: str) -> Dict[str, Any]:
    uid = acc.get("uid", "")
    pwd = acc.get("pwd", "")
    twofa = acc.get("twofa", "")
    proxy = acc.get("proxy", "")

    s = requests.Session()
    s.verify = False
    s.trust_env = False # Ép Python không tự lấy Proxy rác của Windows
    
    # Cơ chế Auto-Retry khi Facebook drop connection (Tránh lỗi HTTPSConnectionPool)
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS", "POST"])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
    s.mount('http://', adapter)
    s.mount('https://', adapter)

    if px := parse_proxy(proxy):
        s.proxies.update(px)

    headers = {
        "User-Agent": custom_ua,
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-FB-Connection-Type": "WIFI",
        "X-FB-HTTP-Engine": "Liger",
    }
    data = {
        "format": "json", "device_id": str(uuid.uuid4()), "email": uid, "password": pwd,
        "credentials_type": "password", "generate_session_cookies": "1", "source": "login",
        "method": "auth.login", "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32"
    }

    try:
        res = s.post("https://b-api.facebook.com/method/auth.login", headers=headers, data=data, timeout=30).json()

        if res.get("error_code") in [406, 405] or "two_factor" in str(res).lower():
            if twofa:
                err_data = res.get("error_data", {})
                if isinstance(err_data, str):
                    try: err_data = json.loads(err_data)
                    except: err_data = {}
                code_2fa = generate_totp_code(twofa)
                if code_2fa:
                    data.update({
                        "email": str(err_data.get("uid", uid)), "password": code_2fa,
                        "credentials_type": "two_factor", "two_factor_code": code_2fa
                    })
                    if "login_first_factor" in err_data:
                        data["first_factor"] = err_data["login_first_factor"]
                    res = s.post("https://b-api.facebook.com/method/auth.login", headers=headers, data=data, timeout=30).json()

        if "access_token" in res:
            return {"success": True, "uid": str(res.get("uid", uid)), "token": res["access_token"], "name": res.get("user_storage", {}).get("name", "")}
        return {"success": False, "uid": uid, "message": res.get("error_msg", res.get("message", "Login lỗi"))}
    except requests.exceptions.RequestException:
        return {"success": False, "uid": uid, "message": "Lỗi Mạng hoặc Proxy Timeout"}
    except Exception as e:
        return {"success": False, "uid": uid, "message": str(e)}

# ==============================================================================
# 7. CORE REG PAGE PRO5 & THUẬT TOÁN MTOOL MAX SHARE QUYỀN (CHỈ GỬI LỜI MỜI)
# ==============================================================================
GRAPHQL_URL = "https://graph.facebook.com/graphql"
CLIENT_DOC_ID = "11994080426203054249997361787"
BLOKS_VERSIONING_ID = "c11a8c0d160df62b2395f6153824f0bc6c6e316a74ab1aff67da02cdd7cc890b"

# Hằng số chuẩn của MTool Bloks
DOC_ID_MTOOL_ACTION = "30749539927629244093798192451"
BLOKS_VER_MTOOL = "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"

class FbPageCreator:
    def __init__(self, token: str, proxy: Optional[str] = None, user_agent: Optional[str] = None, ua_mode: str = "fixed"):
        self.token = str(token).strip()
        self.proxy = proxy
        self.proxies = parse_proxy(proxy)
        self.ua_mode = ua_mode
        self.user_agent = user_agent or generate_random_katana_ua(seed=self.token)

        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False # Ép Python không lấy Proxy rác của Windows
        
        # Cơ chế Auto-Retry khi Facebook drop connection (Tránh lỗi HTTPSConnectionPool)
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS", "POST"])
        adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        if self.proxies:
            self.session.proxies.update(self.proxies)

        self.mother_uid = ""

    def _get_headers(self, friendly_name: str, token_override: Optional[str] = None) -> Dict[str, str]:
        active_token = token_override or self.token
        return {
            "authorization": f"OAuth {active_token}",
            "x-fb-sim-hni": "45201",
            "x-fb-net-hni": "45201",
            "content-type": "application/x-www-form-urlencoded",
            "x-graphql-client-library": "graphservice",
            "x-tigon-is-retry": "False",
            "x-graphql-request-purpose": "fetch",
            "x-fb-device-group": "2878",
            "x-fb-friendly-name": friendly_name,
            "user-agent": self.user_agent,
            "x-fb-connection-type": "WIFI",
            "x-fb-http-engine": "Tigon/Liger",
            "x-fb-client-ip": "True",
            "x-fb-server-cluster": "True",
        }

    def _get_mtool_headers(self) -> Dict[str, str]:
        """Header dành riêng cho luồng NativeTemplateAsyncQuery của MTool"""
        analytics_tags = {
            "network_tags": {"product": "350685531728", "request_category": "graphql", "purpose": "none", "retry_attempt": "0"},
            "application_tags": "graphservice",
        }
        return {
            "user-agent": self.user_agent,
            "content-type": "application/x-www-form-urlencoded",
            "x-fb-request-analytics-tags": json.dumps(analytics_tags, separators=(",", ":")),
            "x-fb-friendly-name": "NativeTemplateAsyncQuery",
            "x-graphql-client-library": "graphservice",
            "authorization": f"OAuth {self.token}",
            "x-fb-connection-type": "WIFI",
            "x-fb-device-group": "4789",
        }

    def check_account_live(self) -> Dict[str, Any]:
        """Kiểm tra Tài khoản (Nick Reg) còn sống (LIVE) hay đã DIE."""
        try:
            r = self.session.get(
                f"https://graph.facebook.com/me?fields=id,name&access_token={self.token}",
                headers={"User-Agent": self.user_agent},
                timeout=15
            )
            r_json = r.json()
            if "id" in r_json:
                self.mother_uid = str(r_json["id"])
                return {"success": True, "uid": str(r_json["id"]), "name": r_json.get("name", "Facebook User")}
            err = r_json.get("error", {})
            err_msg = err.get("message", "Token lỗi hoặc Nick DIE")
            is_die = "OAuthException" in r.text or "checkpoint" in r.text.lower() or "error" in r_json
            return {"success": False, "is_token_die": is_die, "message": err_msg}
        except requests.exceptions.RequestException:
            # Bắt riêng lỗi Proxy/Mạng để báo chữ Vàng thay vì báo đỏ Nick Die
            return {"success": False, "is_token_die": False, "message": "Lỗi Mạng hoặc Proxy Timeout"}
        except Exception as e:
            return {"success": False, "is_token_die": False, "message": str(e)}

    def get_all_pages_with_tokens(self) -> Dict[str, Any]:
        """Quét me/accounts để lấy danh sách Page kèm theo Page Token (EAAAAU...) và additional_profile_id."""
        try:
            url = (
                f"https://graph.facebook.com/me/accounts"
                f"?fields=id,name,access_token,additional_profile_id,is_published,category"
                f"&limit=100&access_token={self.token}"
            )
            r = self.session.get(url, headers={"User-Agent": self.user_agent}, timeout=25).json()
            if "error" in r:
                err = r.get("error", {})
                err_msg = err.get("message", "Lỗi khi lấy danh sách Page")
                is_die = (
                    "OAuthException" in str(r)
                    or err.get("code") in [190, 102]
                    or "checkpoint" in str(r).lower()
                )
                return {"success": False, "is_token_die": is_die, "pages": [], "message": err_msg}

            pages = r.get("data", []) if isinstance(r.get("data"), list) else []
            return {"success": True, "is_token_die": False, "pages": pages}
        except requests.exceptions.RequestException:
            return {"success": False, "is_token_die": False, "pages": [], "message": "Lỗi Mạng hoặc Proxy Timeout"}
        except Exception as e:
            return {"success": False, "is_token_die": False, "pages": [], "message": str(e)}

    def check_single_page_live(self, page_id: str, page_token: str) -> Dict[str, Any]:
        """Kiểm tra trực tiếp Page vừa tạo và Token của Page đó có sống (LIVE) và hoạt động không."""
        tk_to_check = page_token or self.token
        try:
            url = (
                f"https://graph.facebook.com/{page_id}"
                f"?fields=id,name,is_published,additional_profile_id,access_token"
                f"&access_token={tk_to_check}"
            )
            r = self.session.get(url, headers={"User-Agent": self.user_agent}, timeout=20).json()
            if "id" in r:
                is_pub = r.get("is_published", True)
                if is_pub is False:
                    return {"success": False, "message": "Page bị hủy đăng (Unpublished)"}
                return {
                    "success": True,
                    "page_id": str(r["id"]),
                    "page_name": str(r.get("name", "")),
                    "page_token": str(r.get("access_token") or page_token),
                    "additional_profile_id": str(r.get("additional_profile_id", ""))
                }
            err_msg = r.get("error", {}).get("message", "Page DIE hoặc bị khóa")
            return {"success": False, "message": err_msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def create_page_and_get_token(
        self,
        page_name: str,
        known_page_ids: set,
        step_callback=None
    ) -> Dict[str, Any]:
        """
        Thực hiện tạo 1 Page Pro5, cập nhật từng bước qua callback,
        và lập tức lấy ra Token của Page vừa tạo (page_token).
        """
        if self.ua_mode == "random":
            self.user_agent = generate_random_katana_ua()

        category_ids = ["2700", "2201"]

        # --- BƯỚC 1: SUBMIT TÊN PAGE ---
        if step_callback:
            step_callback(f"Bước 1/2: Đang gửi tên Page '{page_name}'...")

        p1 = {
            "client_input_params": {"name": page_name, "profile_plus_id": "0"},
            "server_params": {
                "variant": 8, "referrer": "bookmark_create_action", "screen": "name",
                "INTERNAL__latency_qpl_marker_id": 36707139, "INTERNAL__latency_qpl_instance_id": 165401559700051,
                "creation_source": "android"
            }
        }
        v1 = {
            "params": {
                "params": json.dumps({"params": json.dumps(p1)}),
                "bloks_versioning_id": BLOKS_VERSIONING_ID,
                "app_id": "com.bloks.www.additional.profile.plus.creation.action.name.submit"
            },
            "scale": "3",
            "nt_context": {
                "using_white_navbar": True, "styles_id": "c433035a5d4cdfd79b9c77d0bcd9006b",
                "pixel_ratio": 3, "is_push_on": True, "debug_tooling_metadata_token": None,
                "is_flipper_enabled": False, "theme_params": [], "bloks_version": BLOKS_VERSIONING_ID
            }
        }
        d1 = {
            "method": "post", "pretty": "false", "format": "json", "server_timestamps": "true",
            "locale": "vi_VN", "purpose": "fetch",
            "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.additional.profile.plus.creation.action.name.submit",
            "fb_api_caller_class": "graphservice", "client_doc_id": CLIENT_DOC_ID,
            "fb_api_client_context": json.dumps({"is_background": False}), "variables": json.dumps(v1),
            "fb_api_analytics_tags": json.dumps(["GraphServices"]), "client_trace_id": str(uuid.uuid4())
        }

        try:
            r1 = self.session.post(GRAPHQL_URL, headers=self._get_headers(d1["fb_api_req_friendly_name"]), data=d1, timeout=30)
            if "OAuthException" in r1.text or r1.status_code == 401:
                return {"success": False, "is_token_die": True, "message": "Token DIE ở Bước 1 (Submit Name)"}
            if "Tên này không hợp lệ" in r1.text or "tên không hợp lệ" in r1.text.lower():
                return {"success": False, "is_name_invalid": True, "message": f"Tên Page '{page_name}' không hợp lệ"}
        except requests.exceptions.RequestException:
            return {"success": False, "message": "Lỗi Mạng hoặc Proxy Timeout ở Bước 1"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi mạng ở Bước 1: {e}"}

        # --- BƯỚC 2: SUBMIT CATEGORY & KHỞI TẠO PAGE ---
        if step_callback:
            step_callback(f"Bước 2/2: Đang chọn Hạng mục & Khởi tạo Page '{page_name}'...")

        p2 = {
            "client_input_params": {
                "entrypoint_logging_data": {"fb_profile_editing_session_entry_point": None, "field_edit_screen_entry_point": None},
                "profile_plus_id": "0", "cp_upsell_declined": 0, "off_platform_creator_reachout_id": "",
                "session_id": None, "category_ids": category_ids,
                "nav_chain": "com.bloks.www.additional.profile.plus.creation,com.bloks.www.additional.profile.plus.creation"
            },
            "server_params": {
                "referrer": "bookmark_create_action", "INTERNAL__latency_qpl_marker_id": 36707139,
                "creation_source": "android", "name": page_name, "variant": 8, "screen": "category",
                "INTERNAL__latency_qpl_instance_id": 165462278000063
            }
        }
        v2 = {
            "params": {
                "params": json.dumps({"params": json.dumps(p2)}),
                "bloks_versioning_id": BLOKS_VERSIONING_ID,
                "app_id": "com.bloks.www.additional.profile.plus.creation.action.category.submit"
            },
            "scale": "3",
            "nt_context": {
                "using_white_navbar": True, "styles_id": "c433035a5d4cdfd79b9c77d0bcd9006b",
                "pixel_ratio": 3, "is_push_on": True, "debug_tooling_metadata_token": None,
                "is_flipper_enabled": False, "theme_params": [], "bloks_version": BLOKS_VERSIONING_ID
            }
        }
        d2 = {
            "method": "post", "pretty": "false", "format": "json", "server_timestamps": "true",
            "locale": "vi_VN", "purpose": "fetch",
            "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.additional.profile.plus.creation.action.category.submit",
            "fb_api_caller_class": "graphservice", "client_doc_id": CLIENT_DOC_ID,
            "fb_api_client_context": json.dumps({"is_background": False}), "variables": json.dumps(v2),
            "fb_api_analytics_tags": json.dumps(["GraphServices"]), "client_trace_id": str(uuid.uuid4())
        }

        try:
            r2 = self.session.post(GRAPHQL_URL, headers=self._get_headers(d2["fb_api_req_friendly_name"]), data=d2, timeout=30)
            res2 = r2.text

            if "OAuthException" in res2 or r2.status_code == 401 or "Session expired" in res2:
                return {"success": False, "is_token_die": True, "message": "Token DIE ở Bước 2 (Submit Category)"}

            if "tạo quá nhiều Trang" in res2 or "tạo quá nhiều trang" in res2.lower() or "thử lại sau" in res2.lower():
                return {"success": False, "is_limit": True, "message": "Gần đây bạn đã tạo quá nhiều Trang (Limit)."}

            if '"severity":"CRITICAL"' in res2 or "field_exception" in res2 or '"fb_bloks_action":null' in res2:
                return {"success": False, "is_restricted": True, "message": "Nick bị chặn tạo Page (CRITICAL)"}
        except requests.exceptions.RequestException:
            return {"success": False, "message": "Lỗi Mạng hoặc Proxy Timeout ở Bước 2"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi mạng ở Bước 2: {e}"}

        # --- BƯỚC 3: LẤY LUÔN TOKEN CỦA PAGE VỪA TẠO ---
        if step_callback:
            step_callback(f"Đang lấy Token EAAAAU của Page '{page_name}' vừa tạo...")

        new_page_obj = None
        # Quét tối đa 3 lần (mỗi lần cách nhau 3s) để Facebook kịp đồng bộ Page mới vào me/accounts
        for attempt in range(1, 4):
            time.sleep(3)
            scan_res = self.get_all_pages_with_tokens()
            if scan_res.get("is_token_die"):
                return {"success": False, "is_token_die": True, "message": "Token DIE khi đang lấy Token Page"}

            pages_list = scan_res.get("pages", [])
            # Ưu tiên tìm Page có ID mới chưa nằm trong known_page_ids
            for p in pages_list:
                pid = str(p.get("id", ""))
                if pid and pid not in known_page_ids:
                    new_page_obj = p
                    break

            # Nếu không lọc được bằng ID cũ, tìm theo tên vừa đặt
            if not new_page_obj:
                for p in pages_list:
                    if str(p.get("name", "")).strip().lower() == page_name.strip().lower():
                        new_page_obj = p
                        break

            if new_page_obj:
                break

        if not new_page_obj:
            return {
                "success": False,
                "is_no_page": True,
                "message": f"Đã gửi lệnh tạo '{page_name}' nhưng chưa ra Page/Token Page"
            }

        page_id = str(new_page_obj.get("id", ""))
        extracted_page_token = str(new_page_obj.get("access_token", ""))
        add_profile_id = str(new_page_obj.get("additional_profile_id", ""))

        # Nếu me/accounts chưa trả về kịp access_token riêng của Page, gọi trực tiếp /{page_id}
        if not extracted_page_token or not add_profile_id:
            p_detail = self.check_single_page_live(page_id, extracted_page_token)
            if p_detail.get("success"):
                extracted_page_token = extracted_page_token or p_detail.get("page_token", "")
                add_profile_id = add_profile_id or p_detail.get("additional_profile_id", "")

        return {
            "success": True,
            "page_id": page_id,
            "page_name": str(new_page_obj.get("name", page_name)),
            "page_token": extracted_page_token,
            "additional_profile_id": add_profile_id
        }

    def invite_holder_mtool(
        self,
        page_id: str,
        holder_uid: str,
        sender_pwd: str = ""
    ) -> Dict[str, Any]:
        """
        [MTOOL MAX CHỈ BẮN THÔNG BÁO] Tích hợp thuật toán MTool Max (NativeTemplate) để gửi lời mời Admin.
        KHÔNG tự động Accept. Bạn sẽ tự dùng Nick Mẹ bấm chấp nhận thủ công.
        """
        holder_uid = str(holder_uid).strip()
        if not holder_uid:
            return {"success": False, "message": "Thiếu UID Nick Mẹ"}

        # 1. BẮT BUỘC: Gửi kết bạn mở khóa share quyền Pro5
        if self.mother_uid and self.mother_uid != holder_uid:
            try:
                vars_fr = {"input": {"friend_requestee_ids": [holder_uid], "source": "profile_button", "actor_id": self.mother_uid, "client_mutation_id": str(uuid.uuid4())}}
                self.session.post(
                    GRAPHQL_URL,
                    headers=self._get_headers("FriendRequestSendCoreMutation"),
                    data={"method": "post", "format": "json", "fb_api_req_friendly_name": "FriendRequestSendCoreMutation", "doc_id": "23999612633015775", "variables": json.dumps(vars_fr)},
                    timeout=15
                )
            except:
                pass

        nt_context = {
            "using_white_navbar": True,
            "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
            "pixel_ratio": 2,
            "is_push_on": True,
            "debug_tooling_metadata_token": None,
            "is_flipper_enabled": False,
            "theme_params": [{"value": [], "design_system_name": "FDS"}],
            "bloks_version": BLOKS_VER_MTOOL
        }

        # 2. STEP 1 MTOOL: RE-AUTH (Nhập lại Mật khẩu ngầm)
        if sender_pwd:
            try:
                payload_auth = (
                    f"/nt/profile/admin_management/permissions_reauth?admin_id={holder_uid}&admin_rows_container_id=%5B%228bxxoh%3A2%22%2Cnull%5D"
                    f"&admin_type=full_access&entry_point_screen_id=%5B%227o2xil%3A5%22%2Cnull%5D&profile_id={page_id}"
                    "&state_ids%5Bauthenticated%5D=8csr9g%3A0&state_ids%5Bauthentication_attempted%5D=8csr9g%3A1&state_ids%5Bshow_entry_point_saving_spinner%5D=8bxxoh%3A0"
                    "&state_ids%5Bshow_saving_spinner%5D=8csr9g%3A3&state_ids%5Bads%5D=8clnk7%3A2&state_ids%5Bcontent%5D=8clnk7%3A3&state_ids%5Binsights%5D=8clnk7%3A4&state_ids%5Bmessages%5D=8clnk7%3A5&state_ids%5Bmoderate%5D=8clnk7%3A6"
                )
                vars_auth = {
                    "params": {"nt_context": nt_context, "payload": payload_auth, "client_data": {"sensitive_string_value": json.dumps([["password", sender_pwd]], separators=(",", ":"))}},
                    "nt_context": nt_context, "scale": "2", "use_native_entrypoint_for_stars_on_reels": True, "profile_image_size": 188, "include_image_ranges": True
                }
                form_auth = {
                    "method": "post", "format": "json", "fb_api_req_friendly_name": "NativeTemplateAsyncQuery",
                    "client_doc_id": DOC_ID_MTOOL_ACTION, "variables": json.dumps(vars_auth, separators=(",", ":")),
                    "fb_api_client_context": json.dumps({"is_background": False}, separators=(",", ":"))
                }
                self.session.post(GRAPHQL_URL, headers=self._get_mtool_headers(), data=form_auth, timeout=20)
            except:
                pass

        # 3. STEP 2 MTOOL: BẮN ADMIN FULL_ACCESS QUA BLOKS
        try:
            payload_upd = (
                f"/nt/profile/admin_management/permissions/update?admin_rows_container_id=%5B%228bxxoh%3A2%22%2Cnull%5D"
                f"&entry_point_screen_id=%5B%227o2xil%3A5%22%2Cnull%5D&admin_type=full_access&profile_id={page_id}&target_admin_id={holder_uid}"
                "&secured_sensitive_actions%5B0%5D=page_admin_access_addition&state_ids%5Bshow_entry_point_saving_spinner%5D=8bxxoh%3A0"
                "&state_ids%5Bads%5D=8clnk7%3A2&state_ids%5Bcontent%5D=8clnk7%3A3&state_ids%5Binsights%5D=8clnk7%3A4&state_ids%5Bmessages%5D=8clnk7%3A5&state_ids%5Bmoderate%5D=8clnk7%3A6"
            )
            perms = {"ads": True, "insights": True, "messages": True, "content": True, "moderate": True, "show_entry_point_saving_spinner": "NONE"}
            vars_upd = {
                "params": {"payload": payload_upd, "state_data": json.dumps(perms, separators=(",", ":")), "nt_context": nt_context},
                "nt_context": nt_context, "scale": "2", "use_native_entrypoint_for_stars_on_reels": True, "profile_image_size": 188, "include_image_ranges": True
            }
            form_upd = {
                "method": "post", "format": "json", "server_timestamps": "true", "locale": "vi_VN",
                "fb_api_req_friendly_name": "NativeTemplateAsyncQuery", "fb_api_caller_class": "graphservice",
                "client_doc_id": DOC_ID_MTOOL_ACTION, "fb_api_client_context": json.dumps({"is_background": False}, separators=(",", ":")),
                "variables": json.dumps(vars_upd, separators=(",", ":"))
            }

            r = self.session.post(GRAPHQL_URL, headers=self._get_mtool_headers(), data=form_upd, timeout=20).json()
            if "errors" in r:
                return {"success": False, "message": f"MTool lỗi: {r['errors'][0].get('message', 'Lỗi không xác định')[:40]}"}
            return {"success": True, "message": f"Đã bắn lời mời FULL_ACCESS sang UID {holder_uid} (Chờ Chấp nhận thủ công)"}
        except requests.exceptions.RequestException:
            return {"success": False, "message": "Lỗi Mạng hoặc Proxy Timeout khi bắn MTool"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi Gửi Yêu Cầu MTool: {str(e)[:40]}"}


# ==============================================================================
# 8. BẢNG THEO DÕI TRỰC TIẾP + KHUNG NHẬT KÝ QUÁ TRÌNH CHI TIẾT
# ==============================================================================

class AccountTask:
    def __init__(
        self,
        acc_id: int,
        item: Dict[str, Any],
        target_pages: int,
        ua_mode: str,
        assigned_proxy: Optional[str] = None,
        holder_uid: Optional[str] = None
    ):
        self.acc_id = acc_id
        self.item = item
        self.type = item.get("type", "token")
        self.pwd = item.get("pwd", "")
        self.token = item.get("token", "")
        self.proxy = item.get("proxy") or assigned_proxy
        self.holder_uid = holder_uid or ""
        self.target_pages = target_pages
        self.pages_created = 0
        self.ua_mode = ua_mode
        self.fixed_ua = generate_random_katana_ua(seed=item.get("uid", "")) if ua_mode == "fixed" else None
        self.creator = None
        self.pre_uid = item.get("uid", "")
        self.mother_uid = self.pre_uid
        self.mother_name = ""
        self.status = "ready"  # ready, running, waiting_check, done, no_page, limit, die
        self.current_action = "Chờ đến lượt..."
        self.last_result = ""


def render_dashboard(accounts: List[AccountTask], stats: Dict[str, int]):
    lines = []
    w = 114
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(f"{Colors.BOLD}{Colors.YELLOW}     BẢNG TIẾN TRÌNH: TẠO PAGE -> GET TOKEN PAGE -> CHECK LIVE ACC & PAGE -> BẮN ADMIN (MTOOL)     {Colors.RESET}")
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(f"{Colors.BOLD} STT | UID Nick Reg     | Tên Nick         | Page Có | Quá trình / Trạng thái hiện tại{Colors.RESET}")
    lines.append("-" * w)

    for acc in accounts:
        stt_str = f"{acc.acc_id:^4}"
        display_uid = (acc.mother_uid or acc.pre_uid or "Unknown")[:16]
        uid_str = f"{display_uid:<16}"
        display_name = (acc.mother_name or "Đang tải...")[:16]
        name_str = f"{display_name:<16}"
        prog_padded = f"{acc.pages_created}/{acc.target_pages}:^7"

        if acc.status == "done":
            status_display = f"{Colors.GREEN}✅ {acc.last_result}{Colors.RESET}"
        elif acc.status == "no_page":
            status_display = f"{Colors.MAGENTA}⚠️ {acc.current_action}{Colors.RESET}"
        elif acc.status == "die":
            status_display = f"{Colors.RED}❌ {acc.current_action}{Colors.RESET}"
        elif acc.status == "limit":
            status_display = f"{Colors.YELLOW}🚫 {acc.current_action}{Colors.RESET}"
        elif acc.status == "waiting_check":
            status_display = f"{Colors.YELLOW}⏳ {acc.current_action}{Colors.RESET}"
        elif acc.status == "running":
            status_display = f"{Colors.CYAN}🟢 {acc.current_action}{Colors.RESET}"
        else:
            status_display = f"{Colors.BLUE}⏸️ {acc.current_action}{Colors.RESET}"

        lines.append(f" {stt_str}| {uid_str} | {name_str} | {prog_padded} | {status_display}")

    lines.append("-" * w)
    lines.append(
        f" {Colors.BOLD}[THỐNG KÊ]{Colors.RESET} Tổng Acc: {len(accounts)} | "
        f"Acc Có Page Sống: {Colors.GREEN}{stats.get('total_holder_acc', 0)}{Colors.RESET} "
        f"(Page Sống: {Colors.GREEN}{stats.get('total_pages', 0)}{Colors.RESET} | "
        f"Đã bắn UID Mẹ: {Colors.CYAN}{stats.get('total_invited', 0)}{Colors.RESET}) | "
        f"Xịt/Die Page: {Colors.MAGENTA}{stats.get('total_no_page', 0)}{Colors.RESET} | "
        f"Limit: {Colors.YELLOW}{stats.get('total_limited', 0)}{Colors.RESET} | "
        f"Acc DIE: {Colors.RED}{stats.get('total_token_die', 0)}{Colors.RESET}"
    )
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")

    lines.append(f"{Colors.BOLD}{Colors.MAGENTA} 📋 NHẬT KÝ QUÁ TRÌNH CHI TIẾT (TẠO PAGE -> GET TOKEN PAGE -> CHECK LIVE -> BẮN LỜI MỜI MTOOL):{Colors.RESET}")
    with LOG_LOCK:
        if not LIVE_PROCESS_LOGS:
            lines.append("   (Đang khởi tạo luồng xử lý...)")
        else:
            for log_item in LIVE_PROCESS_LOGS:
                lines.append(f"   {log_item}")
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")

    buf = "\n".join(lines) + "\n"
    with PRINT_LOCK:
        sys.stdout.write("\033[H\033[J" + buf)
        sys.stdout.flush()

def dashboard_render_loop(accounts: List[AccountTask], stats: Dict[str, int], stop_event: threading.Event):
    while not stop_event.is_set():
        render_dashboard(accounts, stats)
        time.sleep(1.0)
    render_dashboard(accounts, stats)


# ==============================================================================
# 9. LUỒNG XỬ LÝ CHÍNH CHO TỪNG TÀI KHOẢN
# ==============================================================================

def process_single_account_workflow(
    thread_id: int,
    acc: AccountTask,
    name_type: str,
    custom_names: Optional[List[str]],
    verify_delay: int,
    delay_between_pages: int,
    stats: Dict[str, int]
):
    acc.status = "running"
    
    # ==========================================================
    # BƯỚC 0: NẾU LÀ ACCOUNT (UID|PASS) -> AUTO LOGIN LẤY TOKEN
    # ==========================================================
    if acc.type == "account":
        acc.current_action = f"[L{thread_id}] Đang Auto-Login lấy Token..."
        add_process_log(acc.acc_id, acc.pre_uid, "Đang tự động Login bằng UID|Pass|2FA...")
        login_res = login_and_get_token(acc.item, acc.fixed_ua or generate_random_katana_ua(acc.pre_uid))
        if login_res.get("success"):
            acc.token = login_res["token"]
            acc.mother_uid = login_res["uid"]
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}✔ Login thành công, đã lấy Token EAAAAU!{Colors.RESET}")
        else:
            acc.status = "die"
            acc.current_action = f"Login thất bại: {login_res.get('message')}"
            add_process_log(acc.acc_id, acc.pre_uid, f"{Colors.RED}❌ Lỗi Login: {login_res.get('message')}{Colors.RESET}")
            with FILE_LOCK:
                stats["total_token_die"] += 1
            return

    # Khởi tạo Creator với Token (Vừa login được, hoặc token cấp sẵn)
    acc.creator = FbPageCreator(token=acc.token, proxy=acc.proxy, user_agent=acc.fixed_ua, ua_mode=acc.ua_mode)
    
    acc.current_action = f"[L{thread_id}] Bước 1: Đang kiểm tra Tài khoản & quét Page cũ..."
    add_process_log(acc.acc_id, acc.mother_uid, "Bước 1: Đang kiểm tra Token Tài khoản ban đầu...")

    # --- BƯỚC 1: KIỂM TRA TÀI KHOẢN & LƯU DANH SÁCH PAGE CŨ ---
    acc_info = acc.creator.check_account_live()
    if not acc_info.get("success"):
        acc.status = "die"
        acc.mother_name = "Nick DIE / Checkpoint"
        err_msg = acc_info.get("message", "Token DIE")
        acc.current_action = f"Tài khoản DIE từ đầu ({err_msg[:30]}) -> Lưu acc_die.txt"
        add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Tài khoản DIE ngay từ đầu: {err_msg[:45]}{Colors.RESET}")
        with FILE_LOCK:
            stats["total_token_die"] += 1
            with open("acc_die.txt", "a", encoding="utf-8") as f:
                f.write(f"{acc.mother_uid}|{acc.token}|DIE_TRUOC_KHI_REG\n")
        return

    acc.mother_uid = acc_info.get("uid", acc.mother_uid)
    acc.mother_name = acc_info.get("name", "Facebook User")

    pre_pages_res = acc.creator.get_all_pages_with_tokens()
    known_page_ids = {str(p.get("id", "")) for p in pre_pages_res.get("pages", []) if p.get("id")}
    add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}✔ Nick LIVE ({acc.mother_name}) - Đang có sẵn {len(known_page_ids)} Page cũ.{Colors.RESET}")

    # --- BƯỚC 2 & 3: TẠO PAGE VÀ GET LUÔN TOKEN CỦA PAGE VỪA TẠO ---
    newly_created_pages: List[Dict[str, str]] = []
    hit_limit = False
    hit_restricted = False

    for idx in range(1, acc.target_pages + 1):
        page_name = get_page_name(name_type, custom_names)

        def update_step(msg_step: str):
            acc.current_action = f"[L{thread_id}] Reg Page ({idx}/{acc.target_pages}) - {msg_step}"
            add_process_log(acc.acc_id, acc.mother_uid, f"[Page {idx}/{acc.target_pages}] {msg_step}")

        create_res = acc.creator.create_page_and_get_token(page_name=page_name, known_page_ids=known_page_ids, step_callback=update_step)

        if create_res.get("is_token_die"):
            acc.status = "die"
            acc.current_action = "Tài khoản bị DIE trong lúc đang tạo Page -> Lưu acc_die.txt"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Tài khoản bị DIE khi đang tạo Page!{Colors.RESET}")
            with FILE_LOCK:
                stats["total_token_die"] += 1
                with open("acc_die.txt", "a", encoding="utf-8") as f:
                    f.write(f"{acc.mother_uid}|{acc.token}|DIE_KHI_REG\n")
            return

        if create_res.get("is_limit"):
            hit_limit = True
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}🚫 Nick báo Limit: Đã tạo quá nhiều Trang.{Colors.RESET}")
            break

        if create_res.get("is_restricted"):
            hit_restricted = True
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.MAGENTA}⚠️ Nick bị Facebook chặn tạo Page (CRITICAL).{Colors.RESET}")
            break

        if create_res.get("success"):
            p_id = create_res["page_id"]
            p_name = create_res["page_name"]
            p_token = create_res["page_token"]
            add_prof_id = create_res.get("additional_profile_id", "")
            known_page_ids.add(p_id)
            newly_created_pages.append({"id": p_id, "name": p_name, "access_token": p_token, "additional_profile_id": add_prof_id})
            acc.pages_created = len(newly_created_pages)
            short_ptk = f"{p_token[:18]}..." if p_token else "Chưa cấp riêng"
            acc.current_action = f"[L{thread_id}] Đã tạo Page {p_id} & Get Token Page ({short_ptk})"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}🎉 Tạo thành công Page '{p_name}' (ID: {p_id}) | Token Page: {short_ptk}{Colors.RESET}")
        else:
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}⚠️ Lần tạo {idx}: {create_res.get('message', 'Không lên Page')}{Colors.RESET}")

        if idx < acc.target_pages and delay_between_pages > 0:
            for s_rem in range(delay_between_pages, 0, -1):
                acc.current_action = f"[L{thread_id}] Nghỉ {s_rem}s trước khi tạo Page ({idx + 1}/{acc.target_pages})...."
                time.sleep(1)

    if not newly_created_pages:
        if hit_limit:
            acc.status = "limit"
            acc.current_action = "Acc bị Limit tạo Page -> Đã bỏ qua"
            with FILE_LOCK: stats["total_limited"] += 1
            return
        else:
            acc.status = "no_page"
            reason_str = "Nick bị chặn (CRITICAL)" if hit_restricted else "Tạo xong nhưng không ra Page mới"
            acc.current_action = f"{reason_str} -> Lưu acc_reg_xit.txt"
            with FILE_LOCK:
                stats["total_no_page"] += 1
                with open("acc_reg_xit.txt", "a", encoding="utf-8") as f: f.write(f"{acc.mother_uid}|{acc.token}|KHONG_LEN_PAGE\n")
            return

    # --- BƯỚC 4: ĐỢI ĐẾM NGƯỢC & CHECK XEM TÀI KHOẢN VÀ PAGE CÒN SỐNG KHÔNG ---
    acc.status = "waiting_check"
    wait_seconds = max(1, int(verify_delay))
    add_process_log(acc.acc_id, acc.mother_uid, f"⏳ Đang đợi {wait_seconds}s trước khi kiểm tra lại Tài khoản & Page sống/chết...")
    for rem in range(wait_seconds, 0, -1):
        acc.current_action = f"[L{thread_id}] Đợi {rem}s để check lại Tài khoản & {len(newly_created_pages)} Page sống/chết..."
        time.sleep(1)

    acc.status = "running"
    acc.current_action = f"[L{thread_id}] Đang check LIVE Tài khoản & Page vừa tạo..."

    recheck_acc = acc.creator.check_account_live()
    if not recheck_acc.get("success"):
        acc.status = "die"
        acc.current_action = f"Sau {wait_seconds}s: Tài khoản bị DIE / Checkpoint!"
        add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Sau {wait_seconds}s: Tài khoản bị DIE / Checkpoint!{Colors.RESET}")
        with FILE_LOCK:
            stats["total_token_die"] += 1
            with open("acc_die.txt", "a", encoding="utf-8") as f: f.write(f"{acc.mother_uid}|{acc.token}|DIE_SAU_{wait_seconds}S\n")
        return

    live_pages: List[Dict[str, Any]] = []
    for p in newly_created_pages:
        p_id, p_tk = p["id"], p["access_token"]
        page_live_res = acc.creator.check_single_page_live(page_id=p_id, page_token=p_tk)
        if page_live_res.get("success"):
            p["access_token"] = page_live_res.get("page_token") or p_tk
            p["additional_profile_id"] = page_live_res.get("additional_profile_id") or p.get("additional_profile_id", "")
            live_pages.append(p)
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}✔ Check LIVE thành công: Nick SỐNG & Page {p_id} ('{p['name']}') SỐNG!{Colors.RESET}")
        else:
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Page {p_id} bị DIE/Hủy đăng sau {wait_seconds}s: {page_live_res.get('message')}{Colors.RESET}")

    if not live_pages:
        acc.status = "no_page"
        acc.current_action = f"Check sau {wait_seconds}s: Page vừa tạo đã bị hủy đăng/DIE!"
        with FILE_LOCK:
            stats["total_no_page"] += 1
            with open("acc_reg_xit.txt", "a", encoding="utf-8") as f: f.write(f"{acc.mother_uid}|{acc.token}|PAGE_DIE_SAU_{wait_seconds}S\n")
        return

    # --- BƯỚC 5: TÍCH HỢP MTOOL MAX BẮN LỜI MỜI ADMIN ---
    acc.pages_created = len(live_pages)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page_summary_list = []
    transfer_note = "Đã lưu Page & Token vào acc_cam_page.txt"

    for p in live_pages:
        p_id, p_name, p_token = str(p["id"]), str(p["name"]), str(p["access_token"])
        page_summary_list.append(f"{p_id}:{p_name}")

        if acc.holder_uid:
            acc.current_action = f"[L{thread_id}] Đang bắn lời mời Admin Page {p_id} sang UID {acc.holder_uid}..."
            add_process_log(acc.acc_id, acc.mother_uid, f"🚀 Đang bắn lời mời quyền Admin sang UID {acc.holder_uid} bằng thuật toán MTool...")
            
            # GỌI HÀM BẮN MTOOL - Truyền kèm pwd (nếu có) để Re-Auth
            tr_res = acc.creator.invite_holder_mtool(
                page_id=p_id,
                holder_uid=acc.holder_uid,
                sender_pwd=acc.pwd
            )
            
            p["transfer_ok"] = tr_res.get("success", False)
            transfer_note = tr_res.get("message", "")
            if p["transfer_ok"]:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}✅ {transfer_note}{Colors.RESET}")
            else:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Lỗi MTool: {transfer_note}{Colors.RESET}")
        else:
            p["transfer_ok"] = False

    with FILE_LOCK:
        stats["total_holder_acc"] += 1
        stats["total_pages"] += len(live_pages)

        for p in live_pages:
            p_id, p_name, p_token = str(p["id"]), str(p["name"]), str(p["access_token"])
            if p.get("transfer_ok"): stats["total_invited"] += 1
            with open("created_pages.txt", "a", encoding="utf-8") as f_page:
                f_page.write(f"{p_id}|{p_name}|{p_token}|{acc.mother_uid}|{now_str}\n")
            with open("acc_cam_page.txt", "a", encoding="utf-8") as f_holder:
                if acc.holder_uid:
                    tr_tag = f"DA_BAN_UID:{acc.holder_uid}" if p.get("transfer_ok") else f"LOI_BAN_UID:{acc.holder_uid}"
                    f_holder.write(f"{acc.mother_uid}|{acc.token}|{p_id}|{p_name}|{p_token}|{tr_tag}|{now_str}\n")
                else:
                    f_holder.write(f"{acc.mother_uid}|{acc.token}|{p_id}|{p_name}|{p_token}|PAGE_LIVE|{now_str}\n")

    acc.status = "done"
    first_page_str = ", ".join(page_summary_list[:2])
    acc.last_result = f"LIVE {len(live_pages)} Page ({first_page_str}) | {transfer_note}"
    acc.current_action = acc.last_result


def worker_reg_account(
    thread_id: int, queue: Queue, name_type: str, custom_names: Optional[List[str]],
    verify_delay: int, delay_between_pages: int, stats: Dict[str, int]
):
    while True:
        try: acc = queue.get(timeout=2.0)
        except Empty: break
        try:
            process_single_account_workflow(thread_id, acc, name_type, custom_names, verify_delay, delay_between_pages, stats)
        except Exception as e:
            acc.status = "die"
            acc.current_action = f"Lỗi ngoại lệ: {str(e)[:40]}"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Lỗi ngoại lệ: {str(e)[:50]}{Colors.RESET}")
        finally: queue.task_done()


# ==============================================================================
# 10. MENU CẤU HÌNH & CHẠY TOOL
# ==============================================================================

def run_reg_page_menu():
    print_banner()
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== CẤU HÌNH: AUTO LOGIN -> REG PAGE -> CHECK LIVE -> BẮN LỜI MỜI SANG UID MẸ (MTOOL) ==={Colors.RESET}\n")

    safe_print(f"{Colors.CYAN}--- [1/7] NẠP DANH SÁCH ACC HOẶC TOKEN CẦN REG ---{Colors.RESET}")
    safe_print("💡 Mẹo: Hỗ trợ dán cả Token EAAAAU hoặc định dạng UID|Pass|2FA (Tool tự login).")
    safe_print("[1] Dán trực tiếp vào màn hình")
    safe_print("[2] Đọc từ file accounts_or_tokens.txt")
    c_tok = input("Chọn cách nạp (1 hoặc 2, mặc định 1): ").strip() or "1"

    raw_tokens = []
    if c_tok == "1":
        raw_tokens = input_multiline("Hãy dán danh sách Token hoặc Account vào đây:")
    else:
        fn = input("Nhập tên file (mặc định accounts_or_tokens.txt): ").strip() or "accounts_or_tokens.txt"
        if os.path.exists(fn):
            with open(fn, "r", encoding="utf-8", errors="ignore") as f:
                raw_tokens = [l.strip() for l in f if l.strip()]
        else:
            safe_print(f"{Colors.RED}Không tìm thấy file {fn}!{Colors.RESET}")
            input("\nNhấn Enter để quay lại...")
            return

    parsed_items = parse_hybrid_lines(raw_tokens)
    if not parsed_items:
        safe_print(f"{Colors.RED}Không tìm thấy Acc (UID|Pass) hoặc Token nào hợp lệ!{Colors.RESET}")
        input("\nNhấn Enter để quay lại...")
        return

    safe_print(f"{Colors.GREEN}{Colors.BOLD}Đã nhận diện: {len(parsed_items)} dữ liệu hợp lệ!{Colors.RESET}\n")

    safe_print(f"{Colors.CYAN}--- [2/7] NHẬP UID NICK MẸ (ACC CẦM PAGE) ĐỂ BẮN LỜI MỜI ---{Colors.RESET}")
    safe_print("Nhập UID của Nick Mẹ (có thể nhập nhiều UID cách nhau dấu phẩy).")
    safe_print("Nếu để trống -> Tool chỉ tạo Page, get Token Page và lưu file.")
    h_raw = input("Nhập UID Nick Mẹ: ").strip()

    holder_uids: List[str] = []
    if h_raw:
        for part in re.split(r"[,;\s]+", h_raw):
            u_parsed = parse_holder_uid(part)
            if u_parsed: holder_uids.append(u_parsed)

    if holder_uids:
        safe_print(f"{Colors.GREEN}✔ Sẽ dùng thuật toán MTool bắn Lời mời Admin sang UID: {', '.join(holder_uids)} (Bạn tự bấm Chấp nhận).{Colors.RESET}\n")
    else:
        safe_print(f"{Colors.YELLOW}Không nhập UID Nick Mẹ -> Bỏ qua bắn Admin.{Colors.RESET}\n")

    safe_print(f"{Colors.CYAN}--- [3/7] CHỌN LOẠI TÊN PAGE ---{Colors.RESET}")
    safe_print("[1] Tên Việt thuần 100%")
    safe_print("[2] Tên Ngoại / US")
    safe_print("[3] Tự nạp danh sách tên từ file names.txt")
    c_name = input("Chọn loại tên (1, 2 hoặc 3, mặc định 1): ").strip() or "1"
    name_type, custom_names = "viet", []
    if c_name == "2": name_type = "us"
    elif c_name == "3":
        name_type = "custom"
        fn_name = input("Nhập file tên (mặc định names.txt): ").strip() or "names.txt"
        if os.path.exists(fn_name):
            with open(fn_name, "r", encoding="utf-8", errors="ignore") as f:
                custom_names = [l.strip() for l in f if l.strip()]
            safe_print(f"{Colors.GREEN}Đã nạp {len(custom_names)} tên!{Colors.RESET}")
        else:
            safe_print(f"{Colors.YELLOW}Không thấy {fn_name}, chuyển sang Tên Việt.{Colors.RESET}")
            name_type = "viet"
    safe_print("")

    safe_print(f"{Colors.CYAN}--- [4/7] CƠ CHẾ USER-AGENT (KATANA ANDROID) ---{Colors.RESET}")
    safe_print("[1] Cố định 1 UA cho mỗi nick [Khuyên dùng]")
    safe_print("[2] Random UA mới mỗi lần tạo Page")
    c_ua = input("Chọn (1 hoặc 2, mặc định 1): ").strip() or "1"
    ua_mode = "random" if c_ua == "2" else "fixed"
    safe_print("")

    safe_print(f"{Colors.CYAN}--- [5/7] CẤU HÌNH PROXY ---{Colors.RESET}")
    global_proxies = []
    if any(it.get("proxy") for it in parsed_items):
        safe_print(f"{Colors.GREEN}Đã gắn Proxy kèm từng nick.{Colors.RESET}\n")
    else:
        use_px = input("Có sử dụng Proxy chung không? (y/n, mặc định n): ").strip().lower()
        if use_px == "y":
            safe_print("[1] Dán danh sách proxy vào màn hình")
            safe_print("[2] Đọc từ file proxies.txt")
            c_px = input("Chọn (1 hoặc 2, mặc định 2): ").strip() or "2"
            px_lines = []
            if c_px == "1":
                px_lines = input_multiline("Dán proxy vào đây (IPv4, IPv6, HTTP, SOCKS5):")
            else:
                p_file = input("Tên file proxy (mặc định proxies.txt): ").strip() or "proxies.txt"
                if os.path.exists(p_file):
                    with open(p_file, "r", encoding="utf-8", errors="ignore") as f:
                        px_lines = [l.strip() for l in f if l.strip()]
            for pl in px_lines:
                if parse_proxy(pl): global_proxies.append(pl)
            safe_print(f"{Colors.GREEN}Đã nhận diện: {len(global_proxies)} Proxy hợp lệ!{Colors.RESET}\n")
        else:
            safe_print(f"{Colors.YELLOW}Chạy trực tiếp mạng máy tính / 4G.{Colors.RESET}\n")

    safe_print(f"{Colors.CYAN}--- [6/7] SỐ PAGE TRÊN 1 ACC & THỜI GIAN ĐỢI ---{Colors.RESET}")
    try: pages_per_nick = int(input("Số Page muốn reg trên 1 Acc (Mặc định 1): ").strip() or "1")
    except ValueError: pages_per_nick = 1
    try: verify_delay = int(input("Đợi bao nhiêu giây để check lại Acc & Page sống/chết? (Mặc định 20): ").strip() or "20")
    except ValueError: verify_delay = 20
    delay_between = 5
    if pages_per_nick > 1:
        try: delay_between = int(input("Thời gian nghỉ giữa các Page (giây, mặc định 5): ").strip() or "5")
        except ValueError: delay_between = 5
    safe_print("")

    safe_print(f"{Colors.CYAN}--- [7/7] SỐ LUỒNG CHẠY SONG SONG ---{Colors.RESET}")
    try: num_threads = int(input(f"Nhập số luồng (Mặc định {min(3, len(parsed_items))}): ").strip() or str(min(3, len(parsed_items))))
    except ValueError: num_threads = 3
    num_threads = max(1, min(num_threads, 50))

    input(f"\n{Colors.BOLD}{Colors.YELLOW}Bấm Enter để BẮT ĐẦU CHẠY...{Colors.RESET}")

    with LOG_LOCK: LIVE_PROCESS_LOGS.clear()

    stats = {
        "total_holder_acc": 0, "total_pages": 0, "total_invited": 0,
        "total_no_page": 0, "total_limited": 0, "total_token_die": 0
    }
    actual_threads = min(num_threads, len(parsed_items))
    worker_threads = []
    stop_dashboard = threading.Event()
    account_tasks = []
    task_queue = Queue()

    for idx, it in enumerate(parsed_items):
        assigned_px = global_proxies[idx % len(global_proxies)] if global_proxies and not it.get("proxy") else None
        assigned_uid = holder_uids[idx % len(holder_uids)] if holder_uids else ""
        task_obj = AccountTask(
            acc_id=idx + 1, item=it, target_pages=pages_per_nick,
            ua_mode=ua_mode, assigned_proxy=assigned_px, holder_uid=assigned_uid
        )
        account_tasks.append(task_obj)
        task_queue.put(task_obj)

    dashboard_thread = threading.Thread(target=dashboard_render_loop, args=(account_tasks, stats, stop_dashboard), daemon=True)
    dashboard_thread.start()

    for t_id in range(1, actual_threads + 1):
        t = threading.Thread(target=worker_reg_account, args=(t_id, task_queue, name_type, custom_names, verify_delay, delay_between, stats), daemon=True)
        worker_threads.append(t)
        t.start()

    for t in worker_threads: t.join()

    stop_dashboard.set()
    dashboard_thread.join(timeout=1.5)
    render_dashboard(account_tasks, stats)

    safe_print("\n" + "=" * 110)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT TIẾN TRÌNH!{Colors.RESET}")
    safe_print(f"- Số Acc sống & có Page sống sau {verify_delay}s: {Colors.GREEN}{stats['total_holder_acc']} Acc ({stats['total_pages']} Page){Colors.RESET}")
    safe_print(f"- Số Page đã gửi lời mời Admin MTool sang UID Nick Mẹ: {Colors.CYAN}{stats['total_invited']} Page{Colors.RESET}")
    safe_print(f"- Số Acc không lên Page hoặc Page bị hủy đăng: {Colors.MAGENTA}{stats['total_no_page']}{Colors.RESET}")
    safe_print(f"- Số Acc gặp Limit: {Colors.YELLOW}{stats['total_limited']}{Colors.RESET}")
    safe_print(f"- Số Acc bị Token DIE / Checkpoint: {Colors.RED}{stats['total_token_die']}{Colors.RESET}")
    safe_print(f"- File lưu Acc + Page + Token Page + Trạng thái bắn UID: {Colors.CYAN}acc_cam_page.txt{Colors.RESET}")
    if holder_uids:
        safe_print(f"- Link duyệt lời mời Admin hàng loạt trên Nick Mẹ: {Colors.YELLOW}https://www.facebook.com/pages/?category=invites{Colors.RESET}")
    safe_print("=" * 110 + "\n")
    input("Nhấn Enter để quay lại menu chính...")


def worker_get_token(thread_id: int, queue: Queue, stats: Dict[str, int]):
    while True:
        try:
            acc = queue.get(timeout=2.0)
        except Empty:
            break

        uid = acc.get("uid", "")
        safe_print(f"{Colors.CYAN}[Luồng {thread_id}] Đang đăng nhập và lấy Token cho UID: {uid}...{Colors.RESET}")

        custom_ua = generate_random_katana_ua(seed=uid)
        res = login_and_get_token(acc, custom_ua=custom_ua)

        if res.get("success"):
            token = res.get("token", "")
            name = res.get("name", "")

            safe_print(f"{Colors.GREEN}{Colors.BOLD}[Luồng {thread_id}] [THÀNH CÔNG] UID: {uid} ({name}){Colors.RESET}")
            safe_print(f"{Colors.GREEN}Token EAAAAU -> {token}{Colors.RESET}")

            with FILE_LOCK:
                with open("tokens_eaaau.txt", "a", encoding="utf-8") as f:
                    f.write(f"{uid}|{token}\n")
                stats["success"] += 1
        else:
            safe_print(f"{Colors.RED}[Luồng {thread_id}] [LỖI] UID: {uid} -> {res.get('message')}{Colors.RESET}")
            with FILE_LOCK:
                stats["fail"] += 1

        queue.task_done()


def run_get_token_menu():
    print_banner()
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== CHỨC NĂNG PHỤ: CHỈ GET TOKEN EAAAAU TỪ ACC (UID|PASS|2FA) ==={Colors.RESET}\n")

    safe_print("[1] Dán danh sách tài khoản vào màn hình")
    safe_print("[2] Đọc từ file accounts.txt")
    c = input("Chọn (1 hoặc 2, mặc định 1): ").strip() or "1"

    lines = []
    if c == "1":
        lines = input_multiline("Dán tài khoản (UID|Pass|2FA hoặc UID|Pass|2FA|Cookie):")
    else:
        fn = input("Nhập tên file (mặc định accounts.txt): ").strip() or "accounts.txt"
        if os.path.exists(fn):
            with open(fn, "r", encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f if l.strip()]
        else:
            safe_print(f"{Colors.RED}Không tìm thấy file {fn}!{Colors.RESET}")
            input("\nNhấn Enter để quay lại...")
            return

    acc_list = [parse_account_line(l) for l in lines if parse_account_line(l)]
    if not acc_list:
        safe_print(f"{Colors.RED}Không tìm thấy tài khoản nào hợp lệ!{Colors.RESET}")
        input("\nNhấn Enter để quay lại...")
        return

    safe_print(f"{Colors.GREEN}Đã nhận diện: {len(acc_list)} tài khoản hợp lệ!{Colors.RESET}")

    try:
        threads = int(input(f"Số luồng (Mặc định {min(3, len(acc_list))}): ").strip() or str(min(3, len(acc_list))))
    except ValueError:
        threads = 3
    threads = max(1, min(threads, 20))

    input(f"\n{Colors.YELLOW}Bấm Enter để BẮT ĐẦU LẤY TOKEN...{Colors.RESET}\n")

    task_queue = Queue()
    for a in acc_list:
        task_queue.put(a)

    stats = {"success": 0, "fail": 0}
    worker_threads = []
    for t_id in range(1, min(threads, len(acc_list)) + 1):
        t = threading.Thread(target=worker_get_token, args=(t_id, task_queue, stats), daemon=True)
        worker_threads.append(t)
        t.start()

    for t in worker_threads:
        t.join()

    safe_print("\n" + "=" * 88)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT LẤY TOKEN EAAAAU!{Colors.RESET}")
    safe_print(f"- Lấy thành công: {Colors.GREEN}{stats['success']}{Colors.RESET}")
    safe_print(f"- Thất bại: {Colors.RED}{stats['fail']}{Colors.RESET}")
    safe_print(f"- Đã lưu file: {Colors.CYAN}tokens_eaaau.txt{Colors.RESET}")
    safe_print("=" * 88 + "\n")
    input("Nhấn Enter để quay lại menu chính...")


def main():
    while True:
        print_banner()
        safe_print(f"{Colors.BOLD}VUI LÒNG CHỌN CHỨC NĂNG:{Colors.RESET}")
        safe_print(f"{Colors.GREEN}[1] REG PAGE PRO5 -> GET TOKEN PAGE -> CHECK LIVE ACC & PAGE -> BẮN LỜI MỜI ADMIN{Colors.RESET}")
        safe_print(f"{Colors.YELLOW}[2] CHỈ GET TOKEN EAAAAU TỪ TÀI KHOẢN (Tính năng phụ){Colors.RESET}")
        safe_print(f"{Colors.RED}[0] THOÁT TOOL{Colors.RESET}\n")

        choice = input("Nhập lựa chọn của bạn (0 - 2): ").strip()

        if choice == "1":
            run_reg_page_menu()
        elif choice == "2":
            run_get_token_menu()
        elif choice == "0":
            safe_print(f"\n{Colors.CYAN}Cảm ơn bạn đã sử dụng Tool. Tạm biệt!{Colors.RESET}\n")
            sys.exit(0)
        else:
            safe_print(f"{Colors.RED}Lựa chọn không hợp lệ.{Colors.RESET}")
            time.sleep(1)


if __name__ == "__main__":
    main()
