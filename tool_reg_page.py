# -*- coding: utf-8 -*-
"""
================================================================================
TOOL REG PAGE PRO5 & GET TOKEN EAAAAU TỰ ĐỘNG - BẢN ALL-IN-ONE (CHẠY MỌI THIẾT BỊ)
Hỗ trợ chạy mượt mà trên cả PC (Windows/Linux/Mac) và Điện thoại (Termux / Pydroid 3).
Toàn bộ tính năng gói gọn trong 1 file duy nhất, chỉ cần duy nhất thư viện requests!
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
import threading
import urllib.parse
from queue import Queue, Empty
from typing import Optional, Dict, Any, List, Tuple

try:
    import requests
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    print("Vui lòng cài đặt requests bằng lệnh: pip install requests")
    sys.exit(1)

# ==============================================================================
# 1. CẤU HÌNH MÀU SẮC TERMINAL & TIỆN ÍCH
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

# Tự động kích hoạt ANSI color trên Windows
if sys.platform == "win32":
    os.system("color")

PRINT_LOCK = threading.Lock()
FILE_LOCK = threading.Lock()
COUNTDOWN_LOCK = threading.Lock()
COUNTDOWN_STATUS = {}
ACTIVE_COUNTDOWN_LINE = False

def safe_print(msg: str):
    """In ra màn hình an toàn đa luồng, không bị đè chữ."""
    global ACTIVE_COUNTDOWN_LINE
    with PRINT_LOCK:
        if ACTIVE_COUNTDOWN_LINE:
            sys.stdout.write("\r" + " " * 110 + "\r")
            ACTIVE_COUNTDOWN_LINE = False
        print(msg)
        sys.stdout.flush()

def update_countdown_display():
    """Vẽ lại dòng trạng thái đếm ngược trực quan từng giây của các luồng."""
    global ACTIVE_COUNTDOWN_LINE
    with PRINT_LOCK:
        with COUNTDOWN_LOCK:
            if not COUNTDOWN_STATUS:
                if ACTIVE_COUNTDOWN_LINE:
                    sys.stdout.write("\r" + " " * 110 + "\r")
                    sys.stdout.flush()
                    ACTIVE_COUNTDOWN_LINE = False
                return

            parts = [COUNTDOWN_STATUS[k] for k in sorted(COUNTDOWN_STATUS.keys())]
            text = " | ".join(parts)
            out = f"\r{Colors.YELLOW}⏳ {text}{Colors.RESET}"
            sys.stdout.write(out + "    ")
            sys.stdout.flush()
            ACTIVE_COUNTDOWN_LINE = True

def sleep_with_countdown(total_seconds: int, thread_id: int, label: str = "Nghỉ", uid: str = ""):
    """Đếm ngược từng giây một cách mượt mà và trực quan trên màn hình."""
    if total_seconds <= 0:
        return

    uid_str = f"[{uid}] " if uid else ""
    end_time = time.time() + total_seconds

    while True:
        remaining = int(end_time - time.time())
        if remaining <= 0:
            break

        with COUNTDOWN_LOCK:
            COUNTDOWN_STATUS[thread_id] = f"[Luồng {thread_id}] {uid_str}{label}: {remaining}s"

        update_countdown_display()
        time.sleep(1)

    with COUNTDOWN_LOCK:
        if thread_id in COUNTDOWN_STATUS:
            del COUNTDOWN_STATUS[thread_id]

    update_countdown_display()

def clear_screen():
    os.system("cls" if sys.platform == "win32" else "clear")

def print_banner():
    clear_screen()
    safe_print(f"{Colors.CYAN}{Colors.BOLD}")
    safe_print("=" * 72)
    safe_print("    TOOL REG PAGE PRO5 & GET TOKEN EAAAAU - BẢN ALL-IN-ONE (MOBILE/PC)  ")
    safe_print("     Chuẩn Katana FB4A Android | Name Việt/US | Đa Luồng | Auto Limit   ")
    safe_print("=" * 72)
    safe_print(f"{Colors.RESET}")

def input_multiline(prompt: str) -> List[str]:
    """Hỗ trợ dán trực tiếp nhiều dòng trên điện thoại và PC."""
    safe_print(prompt)
    safe_print(f"{Colors.YELLOW}(Dán nội dung vào đây. Dán xong nhấn Enter 2 lần để chạy):{Colors.RESET}")
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
    """
    Tự động chuẩn hóa mọi định dạng proxy:
    - IPv4, IPv6 ([ipv6]:port:user:pass, ipv6:port...)
    - HTTP, HTTPS, SOCKS5, SOCKS4
    - Có mật khẩu hoặc không có mật khẩu, proxy xoay IP
    """
    if not proxy_str or not str(proxy_str).strip():
        return None
    p = str(proxy_str).strip()

    # 1. Đã có scheme
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

    # 2. Dạng User:Pass@Host:Port
    if "@" in p:
        auth, host_port = p.rsplit("@", 1)
        if not host_port.startswith("[") and host_port.count(":") >= 2:
            hp_parts = host_port.rsplit(":", 1)
            if len(hp_parts) == 2 and hp_parts[1].isdigit():
                host_port = f"[{hp_parts[0]}]:{hp_parts[1]}"
        formatted = f"http://{auth}@{host_port}"
        return {"http": formatted, "https": formatted}

    # 3. Định dạng ngoặc vuông IPv6: [IPv6]:Port:User:Pass
    m_bracket = re.match(r"^\[([a-fA-F0-9:]+)\]:(\d+)(?::([^:]+):(.+))?$", p)
    if m_bracket:
        ipv6, port, user, pwd = m_bracket.groups()
        if user and pwd:
            formatted = f"http://{user}:{pwd}@[{ipv6}]:{port}"
        else:
            formatted = f"http://[{ipv6}]:{port}"
        return {"http": formatted, "https": formatted}

    parts = p.split(":")
    # 4.1. IPv4: IP:Port hoặc IP:Port:User:Pass
    if len(parts) == 2 and parts[1].isdigit():
        return {"http": f"http://{parts[0]}:{parts[1]}", "https": f"http://{parts[0]}:{parts[1]}"}

    if len(parts) == 4 and parts[1].isdigit() and parts[0].count(".") == 3:
        ip, port, user, pwd = parts
        formatted = f"http://{user}:{pwd}@{ip}:{port}"
        return {"http": formatted, "https": formatted}

    # 4.2. IPv6 trần
    if p.count(":") >= 3:
        if len(parts) >= 4 and parts[-3].isdigit():
            port, user, pwd = parts[-3], parts[-2], parts[-1]
            ipv6_candidate = ":".join(parts[:-3])
            formatted = f"http://{user}:{pwd}@[{ipv6_candidate}]:{port}"
            return {"http": formatted, "https": formatted}
        if len(parts) >= 3 and parts[-1].isdigit():
            port = parts[-1]
            ipv6_candidate = ":".join(parts[:-1])
            formatted = f"http://[{ipv6_candidate}]:{port}"
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
    ('Samsung', 'samsung', 'Galaxy Note 10+', 'SM-N975F', 3.5, 1440, 3040, 10, 12),
    ('Samsung', 'samsung', 'Galaxy Note 9', 'SM-N960N', 3.0, 1080, 1920, 9, 11),
    ('Samsung', 'samsung', 'Galaxy A54 5G', 'SM-A546B', 2.625, 1080, 2340, 13, 14),
    ('Xiaomi', 'xiaomi', 'Xiaomi 13', '2211133G', 3.0, 1080, 2400, 13, 14),
    ('Xiaomi', 'xiaomi', 'Xiaomi 12T', '22071212AG', 3.25, 1220, 2712, 12, 14),
    ('Xiaomi', 'xiaomi', 'Redmi Note 12 Pro', '22101316G', 3.0, 1080, 2400, 12, 14),
    ('Xiaomi', 'xiaomi', 'Redmi Note 11', '2201117TG', 2.75, 1080, 2400, 11, 13),
    ('Xiaomi', 'xiaomi', 'POCO X3 Pro', 'M2102J20SG', 2.75, 1080, 2400, 11, 13),
    ('Oppo', 'OPPO', 'Reno10 Pro 5G', 'CPH2525', 3.0, 1080, 2412, 13, 14),
    ('Oppo', 'OPPO', 'Reno8 5G', 'CPH2359', 3.0, 1080, 2400, 12, 14),
    ('Google', 'google', 'Pixel 8 Pro', 'Pixel 8 Pro', 3.5, 1344, 2992, 14, 14),
    ('Google', 'google', 'Pixel 7 Pro', 'Pixel 7 Pro', 3.5, 1440, 3120, 13, 14),
    ('Google', 'google', 'Pixel 6 Pro', 'Pixel 6 Pro', 3.5, 1440, 3120, 12, 14),
]

FBAV_VERSIONS = [
    ('510.0.0.72.41', '725719471'),
    ('543.0.0.55.73', '846638243'),
    ('540.0.0.42.50', '838765431'),
    ('535.0.0.40.114', '825638102'),
    ('530.0.0.34.82', '812456789'),
]

CARRIERS = ['Viettel', 'Vinaphone', 'MobiFone', 'Vietnamobile', 'VN MOBIFONE', 'VIETTEL']
LOCALES = ['vi_VN', 'en_US']


def generate_random_katana_ua(seed: Optional[str] = None) -> str:
    """
    Sinh User-Agent Katana Android thực tế, chuẩn định dạng 100% như trong file HAR.
    Nếu truyền `seed` (ví dụ Token), UA sẽ được CỐ ĐỊNH DUY NHẤT cho nick đó!
    """
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

HO_VIET = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đoàn", "Mai",
    "Trịnh", "Đinh", "Lâm", "Phùng", "Cao", "Hà", "Lương", "Tạ", "Thái"
]

DEM_NAM = [
    "Văn", "Đức", "Đình", "Hữu", "Tuấn", "Minh", "Quốc", "Thanh", "Trọng",
    "Duy", "Bảo", "Quang", "Hải", "Tiến", "Công", "Khắc", "Gia", "Đăng"
]

DEM_NU = [
    "Thị", "Ngọc", "Thu", "Thanh", "Khánh", "Phương", "Kim", "Ánh", "Hải",
    "Hồng", "Bảo", "Mỹ", "Quỳnh", "Thùy", "Yến", "Lan", "Mai", "Cẩm"
]

TEN_NAM = [
    "Nam", "Tuấn", "Anh", "Khải", "Dũng", "Quân", "Cường", "Đạt", "Huy",
    "Hoàng", "Phong", "Long", "Sơn", "Thắng", "Phúc", "Lộc", "Trí", "Trung",
    "Hiếu", "Nghĩa", "Vinh", "Khánh", "Hưng", "Bách", "Đức", "Kiên", "Lâm"
]

TEN_NU = [
    "Linh", "Trang", "Hằng", "Mai", "Thảo", "Hương", "Anh", "Vy", "Hà",
    "Ngọc", "Châu", "Nhi", "Trâm", "Hiền", "Dung", "Hoa", "Lan", "Huệ",
    "Cúc", "Trúc", "Ly", "My", "Oanh", "Quyên", "Tâm", "Uyên", "Vân"
]

US_FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Paul", "Andrew", "Joshua", "Kevin", "Brian", "George", "Edward", "Ronald",
    "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan",
    "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra",
    "Ashley", "Kimberly", "Emily", "Donna", "Michelle", "Carol", "Amanda",
    "Melissa", "Deborah", "Stephanie", "Rebecca", "Sharon", "Laura", "Sophia", "Emma"
]

US_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams"
]

def generate_vietnamese_name() -> str:
    ho = random.choice(HO_VIET)
    if random.choice([True, False]):
        return f"{ho} {random.choice(DEM_NAM)} {random.choice(TEN_NAM)}"
    else:
        return f"{ho} {random.choice(DEM_NU)} {random.choice(TEN_NU)}"

def generate_us_name() -> str:
    return f"{random.choice(US_FIRST_NAMES)} {random.choice(US_LAST_NAMES)}"

def get_page_name(name_type: str = "viet", custom_names: Optional[List[str]] = None) -> str:
    if name_type == "custom" and custom_names:
        return random.choice(custom_names).strip()
    elif name_type == "us":
        return generate_us_name()
    else:
        return generate_vietnamese_name()


# ==============================================================================
# 5. BỘ LỌC TỰ ĐỘNG BÓC TÁCH TOKEN EAAAAU & ACCOUNT
# ==============================================================================

def parse_token_line(line: str) -> Optional[Dict[str, str]]:
    """Tự động bóc tách Token EAAAAU, UID và Proxy từ một dòng bất kỳ."""
    raw = str(line).strip()
    if not raw or raw.startswith("#"):
        return None

    # Tìm Token EAAAAU
    token_match = re.search(r'(EAAAAU[A-Za-z0-9]+)', raw)
    if not token_match:
        return None

    token = token_match.group(1).strip()
    proxy = None
    uid = None

    # Tìm UID nếu có trong dòng
    parts = raw.split("|")
    for p in parts:
        p_clean = p.strip()
        if p_clean.isdigit() and len(p_clean) >= 10:
            uid = p_clean
            break
        elif "c_user=" in p_clean:
            c_u = re.search(r'c_user=(\d+)', p_clean)
            if c_u:
                uid = c_u.group(1)
                break

    if not uid:
        u_match = re.search(r'\b(1000\d{10,12}|615\d{11,13}|\d{14,16})\b', raw)
        if u_match:
            uid = u_match.group(1)

    # Tìm Proxy nếu có
    for p in parts:
        p_clean = p.strip()
        if p_clean == token or p_clean == uid:
            continue
        if ":" in p_clean and any(c.isdigit() for c in p_clean):
            if not p_clean.startswith("c_user=") and not p_clean.startswith("xs="):
                if parse_proxy(p_clean):
                    proxy = p_clean
                    break

    return {"token": token, "proxy": proxy, "uid": uid, "raw": raw}


def parse_tokens_from_lines(lines: List[str]) -> List[Dict[str, str]]:
    results = []
    for line in lines:
        it = parse_token_line(line)
        if it:
            results.append(it)
    return results


def parse_account_line(line: str) -> Optional[Dict[str, str]]:
    raw = str(line).strip()
    if not raw or raw.startswith("#"):
        return None
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 2:
        return None

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
# 6. TỰ SINH MÃ 2FA TOTP THUẦN PYTHON (KHÔNG CẦN CÀI PYOTP)
# ==============================================================================

def generate_totp_code(secret: str) -> str:
    """Tạo mã 2FA 6 số chuẩn RFC 6238 bằng thư viện chuẩn của Python."""
    clean_secret = secret.replace(" ", "").upper()
    if len(clean_secret) == 6 and clean_secret.isdigit():
        return clean_secret
    missing = len(clean_secret) % 8
    if missing != 0:
        clean_secret += "=" * (8 - missing)
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


# ==============================================================================
# 7. ĐĂNG NHẬP KATANA LẤY TOKEN EAAAAU TỰ ĐỘNG
# ==============================================================================

def login_and_get_token(acc: Dict[str, str], custom_ua: Optional[str] = None) -> Dict[str, Any]:
    """Đăng nhập Facebook Katana Android để lấy Token EAAAAU."""
    uid = acc.get("uid", "")
    pwd = acc.get("pwd", "")
    twofa = acc.get("twofa", "")
    proxy = acc.get("proxy", "")

    s = requests.Session()
    s.verify = False
    s.trust_env = False
    proxies = parse_proxy(proxy)
    if proxies:
        s.proxies.update(proxies)

    ua = custom_ua or generate_random_katana_ua(seed=uid)
    headers = {
        "User-Agent": ua,
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-FB-Connection-Type": "WIFI",
    }

    url = "https://b-api.facebook.com/method/auth.login"
    data = {
        "email": uid,
        "password": pwd,
        "format": "json",
        "generate_session_cookies": "1",
        "generate_machine_id": "1",
        "locale": "vi_VN",
        "client_country_code": "VN",
        "method": "auth.login",
        "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32"
    }

    try:
        res = s.post(url, headers=headers, data=data, timeout=30).json()

        # Nếu cần 2FA
        if res.get("error_code") in [406, 405] or "two_factor" in str(res).lower():
            if twofa:
                code_2fa = generate_totp_code(twofa)
                data["credentials_type"] = "two_factor"
                data["two_factor_code"] = code_2fa
                res = s.post(url, headers=headers, data=data, timeout=30).json()

        if "access_token" in res:
            token = res["access_token"]
            return {"success": True, "uid": uid, "token": token, "name": res.get("user_storage", {}).get("name", "")}
        else:
            err = res.get("error_msg") or res.get("message") or str(res)
            return {"success": False, "uid": uid, "message": err}
    except Exception as e:
        return {"success": False, "uid": uid, "message": str(e)}


# ==============================================================================
# 8. CORE REG PAGE PRO5 (GRAPHQL KATANA BLOKS)
# ==============================================================================

GRAPHQL_URL = "https://graph.facebook.com/graphql"
CLIENT_DOC_ID = "11994080426203054249997361787"
BLOKS_VERSIONING_ID = "c11a8c0d160df62b2395f6153824f0bc6c6e316a74ab1aff67da02cdd7cc890b"

class FbPageCreator:
    def __init__(self, token: str, proxy: Optional[str] = None, user_agent: Optional[str] = None, ua_mode: str = "fixed"):
        self.token = str(token).strip()
        self.proxy = proxy
        self.proxies = parse_proxy(proxy)
        self.ua_mode = ua_mode
        self.user_agent = user_agent or generate_random_katana_ua(seed=self.token)

        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False
        if self.proxies:
            self.session.proxies.update(self.proxies)

        self.mother_uid = ""

    def _get_headers(self, friendly_name: str) -> Dict[str, str]:
        return {
            "authorization": f"OAuth {self.token}",
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

    def get_user_info(self) -> Dict[str, Any]:
        try:
            r = self.session.get(f"https://graph.facebook.com/me?access_token={self.token}", timeout=25).json()
            if "id" in r:
                self.mother_uid = str(r["id"])
                return {"success": True, "uid": str(r["id"]), "name": r.get("name", "Facebook User")}
            err = r.get("error", {})
            err_msg = err.get("message", "Token lỗi hoặc Nick DIE")
            is_die = "OAuthException" in str(r) or err.get("code") in [190, 102] or "checkpoint" in str(r).lower() or "error" in r
            return {"success": False, "is_token_die": is_die, "message": err_msg}
        except Exception as e:
            return {"success": False, "is_token_die": False, "message": str(e)}

    def create_page(self, page_name: str) -> Dict[str, Any]:
        """Tạo Page Pro5 qua 2 bước Katana."""
        if self.ua_mode == "random":
            self.user_agent = generate_random_katana_ua()

        category_ids = ["2700", "2201"]

        # Bước 1: Submit Name
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
                return {"success": False, "is_token_die": True, "message": "Token DIE / Hết hạn"}
            if "Tên này không hợp lệ" in r1.text or "tên không hợp lệ" in r1.text.lower():
                return {"success": False, "is_name_invalid": True, "message": "Tên Page không hợp lệ"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi Bước 1: {e}"}

        # Bước 2: Submit Category & Khởi tạo
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
                return {"success": False, "is_token_die": True, "message": "Token DIE / Hết hạn"}

            if "tạo quá nhiều Trang" in res2 or "tạo quá nhiều trang" in res2.lower() or "thử lại sau" in res2.lower():
                return {"success": False, "is_limit": True, "message": "Gần đây bạn đã tạo quá nhiều Trang. Hãy thử lại sau."}

            if '"severity":"CRITICAL"' in res2 or "field_exception" in res2 or '"fb_bloks_action":null' in res2:
                chk = self.get_user_info()
                if not chk.get("success"):
                    return {"success": False, "is_token_die": True, "message": f"Nick mẹ đã DIE / Checkpoint: {chk.get('message')}"}
                else:
                    return {"success": False, "is_restricted": True, "message": "Nick mẹ bị Facebook chặn tạo Page (CRITICAL)"}

            page_ids = re.findall(r"\(bk\.action\.i64\.Const,\s*(\d{10,})\)", res2)

            # Lấy token Page Pro5 qua me/accounts
            acc_res = self.session.get(f"https://graph.facebook.com/me/accounts?access_token={self.token}", timeout=25).json()
            created_page = None
            if "data" in acc_res and isinstance(acc_res["data"], list):
                for p in acc_res["data"]:
                    if p.get("name") == page_name or str(p.get("id")) in page_ids:
                        created_page = p
                        break
                if not created_page and acc_res["data"]:
                    created_page = acc_res["data"][0]

            if created_page:
                return {
                    "success": True,
                    "page_id": str(created_page.get("id", "")),
                    "page_name": str(created_page.get("name", page_name)),
                    "page_token": str(created_page.get("access_token", "")),
                    "mother_uid": self.mother_uid
                }

            if page_ids:
                return {
                    "success": True,
                    "page_id": str(page_ids[-1]),
                    "page_name": page_name,
                    "page_token": "",
                    "mother_uid": self.mother_uid
                }

            return {"success": False, "message": f"Không tìm thấy Page ID trong kết quả: {res2[:200]}"}

        except Exception as e:
            return {"success": False, "message": f"Lỗi Bước 2: {e}"}


# ==============================================================================
# 9. GIAO DIỆN & TIẾN TRÌNH ĐA LUỒNG
# ==============================================================================

class AccountTask:
    def __init__(self, acc_id: int, item: Dict[str, Any], target_pages: int, ua_mode: str, assigned_proxy: Optional[str] = None):
        self.acc_id = acc_id
        self.token = item.get("token", "")
        self.proxy = item.get("proxy") or assigned_proxy
        self.target_pages = target_pages
        self.pages_created = 0
        self.next_available_time = 0.0
        self.ua_mode = ua_mode
        self.fixed_ua = generate_random_katana_ua(seed=self.token) if ua_mode == "fixed" else None
        self.creator = FbPageCreator(token=self.token, proxy=self.proxy, user_agent=self.fixed_ua, ua_mode=ua_mode)
        self.pre_uid = item.get("uid") or ""
        self.mother_uid = self.pre_uid
        self.mother_name = ""
        self.is_initialized = False
        self.status = "ready"  # ready, running, done, limit, die
        self.current_action = "Chờ đến lượt..."
        self.last_result = ""


class RoundRobinPool:
    def __init__(self, accounts: List[AccountTask]):
        self.accounts = accounts
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def get_account_for_work(self) -> Optional[AccountTask]:
        while not self.stop_event.is_set():
            with self.lock:
                now = time.time()
                all_done = True

                for acc in self.accounts:
                    if acc.status in ("done", "limit", "die"):
                        continue
                    all_done = False

                    if acc.status == "ready":
                        if acc.next_available_time <= now:
                            acc.status = "running"
                            return acc

                if all_done:
                    return None

            time.sleep(0.5)

        return None

    def release_account(self, acc: AccountTask, status: str, cooldown_seconds: float = 0.0):
        with self.lock:
            acc.status = status
            if status == "ready":
                acc.next_available_time = time.time() + cooldown_seconds


def render_dashboard(accounts: List[AccountTask], stats: Dict[str, int], total_threads: int):
    now = time.time()
    lines = []
    w = 104
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(f"{Colors.BOLD}{Colors.YELLOW}             BẢNG THEO DÕI TIẾN ĐỘ REG PAGE PRO5 (REAL-TIME DASHBOARD)         {Colors.RESET}")
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(f"{Colors.BOLD} STT | UID              | Tên Nick         | Tiến độ | Trạng thái / Hành động hiện tại{Colors.RESET}")
    lines.append("-" * w)

    for acc in accounts:
        stt_str = f"{acc.acc_id:^4}"
        display_uid = (acc.mother_uid or acc.pre_uid or "Unknown")[:16]
        uid_str = f"{display_uid:<16}"
        display_name = (acc.mother_name or "Đang tải...")[:16]
        name_str = f"{display_name:<16}"
        prog_str = f"{acc.pages_created}/{acc.target_pages}"
        prog_padded = f"{prog_str:^7}"

        if acc.status == "done":
            status_display = f"{Colors.GREEN}🎉 Hoàn thành đủ {acc.target_pages}/{acc.target_pages} Page!{Colors.RESET}"
        elif acc.status == "die":
            status_display = f"{Colors.RED}❌ {acc.current_action or 'Nick mẹ DIE / Token hỏng (Đã dừng)'}{Colors.RESET}"
        elif acc.status == "limit":
            status_display = f"{Colors.YELLOW}🚫 {acc.current_action or 'Bị Limit Facebook (Đã dừng)'}{Colors.RESET}"
        elif acc.status == "running":
            status_display = f"{Colors.CYAN}🟢 {acc.current_action}{Colors.RESET}"
        elif acc.status == "ready":
            if acc.next_available_time > now:
                rem = max(1, int(acc.next_available_time - now))
                if acc.last_result:
                    status_display = f"{Colors.GREEN}✅ {acc.last_result} -> {Colors.YELLOW}⏳ Nghỉ ({rem}s){Colors.RESET}"
                else:
                    status_display = f"{Colors.YELLOW}⏳ Đang nghỉ delay (còn {rem}s){Colors.RESET}"
            else:
                if acc.last_result:
                    status_display = f"{Colors.GREEN}✅ {acc.last_result} (Sẵn sàng reg tiếp){Colors.RESET}"
                else:
                    status_display = f"{Colors.BLUE}⏸️ Sẵn sàng reg tiếp...{Colors.RESET}"
        else:
            status_display = f"{acc.current_action}"

        lines.append(f" {stt_str}| {uid_str} | {name_str} | {prog_padded} | {status_display}")

    lines.append("-" * w)
    lines.append(
        f" {Colors.BOLD}[THỐNG KÊ]{Colors.RESET} Tổng nick: {len(accounts)} | "
        f"Tạo thành công: {Colors.GREEN}{stats.get('total_success', 0)}{Colors.RESET} Page | "
        f"Limit: {Colors.YELLOW}{stats.get('total_limited', 0)}{Colors.RESET} | "
        f"Nick DIE: {Colors.RED}{stats.get('total_token_die', 0)}{Colors.RESET} | "
        f"Số luồng: {total_threads}"
    )
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")

    buf = "\n".join(lines) + "\n"
    with PRINT_LOCK:
        sys.stdout.write("\033[H\033[J" + buf)
        sys.stdout.flush()


def dashboard_render_loop(accounts: List[AccountTask], stats: Dict[str, int], total_threads: int, stop_event: threading.Event):
    while not stop_event.is_set():
        render_dashboard(accounts, stats, total_threads)
        time.sleep(1.0)
    render_dashboard(accounts, stats, total_threads)


def add_log(msg: str):
    pass


def worker_reg_page_sequential(
    thread_id: int,
    queue: Queue,
    name_type: str,
    custom_names: Optional[List[str]],
    pages_per_nick: int,
    delay_between_pages: int,
    limit_action: int,
    limit_delay_seconds: int,
    stats: Dict[str, int]
):
    while True:
        try:
            acc = queue.get(timeout=2.0)
        except Empty:
            break

        try:
            acc.status = "running"
            acc.current_action = f"[L{thread_id}] Đang kiểm tra nick mẹ..."

            user_info = acc.creator.get_user_info()
            if not user_info.get("success"):
                if user_info.get("is_token_die") or "OAuthException" in str(user_info) or "die" in str(user_info).lower():
                    acc.status = "die"
                    acc.mother_uid = user_info.get("uid") or acc.pre_uid or "Unknown"
                    acc.mother_name = "Nick DIE / Checkpoint"
                    acc.current_action = "Nick mẹ đã DIE / Token hỏng -> Đã dừng nick"
                    with FILE_LOCK:
                        stats["total_token_die"] += 1
                    queue.task_done()
                    # Chuyển ngay sang nick tiếp theo trong hàng đợi
                    continue
                else:
                    acc.current_action = f"[L{thread_id}] Lỗi mạng: {str(user_info.get('message'))[:25]}"
                    queue.task_done()
                    continue

            acc.mother_uid = user_info.get("uid", acc.pre_uid or "Unknown")
            acc.mother_name = user_info.get("name", "Facebook User")
            acc.is_initialized = True

            while acc.pages_created < acc.target_pages:
                cur_idx = acc.pages_created + 1
                page_name = get_page_name(name_type, custom_names)
                acc.current_action = f"[L{thread_id}] Đang reg ({cur_idx}/{acc.target_pages}): '{page_name}'..."

                res = acc.creator.create_page(page_name=page_name)

                if res.get("success"):
                    p_id = res.get("page_id", "")
                    p_token = res.get("page_token", "")
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    out_line = f"{p_id}|{page_name}|{p_token}|{acc.mother_uid}|{now_str}\n"
                    with FILE_LOCK:
                        with open("created_pages.txt", "a", encoding="utf-8") as f:
                            f.write(out_line)
                        stats["total_success"] += 1

                    acc.pages_created += 1
                    acc.last_result = f"Tạo '{page_name}' (ID: {p_id})"

                    if acc.pages_created < acc.target_pages:
                        acc.status = "ready"
                        acc.next_available_time = time.time() + delay_between_pages
                        time.sleep(delay_between_pages)
                        acc.status = "running"
                else:
                    if res.get("is_token_die"):
                        acc.status = "die"
                        acc.current_action = "Nick mẹ đã DIE / Token hỏng -> Đã dừng nick"
                        with FILE_LOCK:
                            stats["total_token_die"] += 1
                        break

                    elif res.get("is_restricted"):
                        acc.status = "die"
                        acc.current_action = "Bị Facebook chặn tạo Page -> Đã dừng nick"
                        with FILE_LOCK:
                            stats["total_token_die"] += 1
                        break

                    elif res.get("is_limit"):
                        with FILE_LOCK:
                            stats["total_limited"] += 1
                        if limit_action == 1:
                            acc.status = "limit"
                            acc.current_action = "Bị Limit tạo Page -> Đã dừng nick"
                            break
                        else:
                            acc.status = "ready"
                            acc.next_available_time = time.time() + limit_delay_seconds
                            time.sleep(limit_delay_seconds)
                            acc.status = "running"
                    else:
                        err_msg = res.get("message", "Thất bại")[:40]
                        acc.current_action = f"Lỗi: {err_msg}"
                        chk = acc.creator.get_user_info()
                        if not chk.get("success") and chk.get("is_token_die"):
                            acc.status = "die"
                            acc.current_action = "Nick mẹ đã DIE -> Đã dừng nick"
                            with FILE_LOCK:
                                stats["total_token_die"] += 1
                            break
                        time.sleep(5)

            if acc.pages_created >= acc.target_pages:
                acc.status = "done"
                acc.current_action = f"Đã hoàn thành {acc.target_pages} Page"

            queue.task_done()
        except Exception as e:
            acc.current_action = f"Lỗi luồng: {str(e)[:30]}"
            queue.task_done()
            time.sleep(1)


def worker_reg_page_round_robin(
    thread_id: int,
    pool: RoundRobinPool,
    name_type: str,
    custom_names: Optional[List[str]],
    delay_between_pages: int,
    limit_action: int,
    limit_delay_seconds: int,
    stats: Dict[str, int]
):
    while True:
        acc = pool.get_account_for_work()
        if not acc:
            break

        try:
            if not acc.is_initialized:
                acc.current_action = f"[L{thread_id}] Đang kiểm tra nick mẹ..."
                user_info = acc.creator.get_user_info()

                if not user_info.get("success"):
                    if user_info.get("is_token_die") or "OAuthException" in str(user_info) or "die" in str(user_info).lower():
                        acc.status = "die"
                        acc.mother_uid = user_info.get("uid") or acc.pre_uid or "Unknown"
                        acc.mother_name = "Nick DIE / Checkpoint"
                        acc.current_action = "Nick mẹ đã DIE / Token hỏng -> Đã dừng nick"
                        with FILE_LOCK:
                            stats["total_token_die"] += 1
                        pool.release_account(acc, status="die")
                        # CHUYỂN NGAY SANG NICK TIẾP THEO
                        continue
                    else:
                        acc.current_action = f"[L{thread_id}] Lỗi mạng: {str(user_info.get('message'))[:25]}"
                        pool.release_account(acc, status="ready", cooldown_seconds=10)
                        continue

                acc.mother_uid = user_info.get("uid", acc.pre_uid or "Unknown")
                acc.mother_name = user_info.get("name", "Facebook User")
                acc.is_initialized = True

            cur_idx = acc.pages_created + 1
            page_name = get_page_name(name_type, custom_names)
            acc.current_action = f"[L{thread_id}] Đang reg ({cur_idx}/{acc.target_pages}): '{page_name}'..."

            res = acc.creator.create_page(page_name=page_name)

            if res.get("success"):
                p_id = res.get("page_id", "")
                p_token = res.get("page_token", "")
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                out_line = f"{p_id}|{page_name}|{p_token}|{acc.mother_uid}|{now_str}\n"
                with FILE_LOCK:
                    with open("created_pages.txt", "a", encoding="utf-8") as f:
                        f.write(out_line)
                    stats["total_success"] += 1

                acc.pages_created += 1
                acc.last_result = f"Tạo '{page_name}' (ID: {p_id})"

                if acc.pages_created >= acc.target_pages:
                    acc.status = "done"
                    acc.current_action = f"Đã hoàn thành {acc.target_pages} Page"
                    pool.release_account(acc, status="done")
                else:
                    acc.current_action = f"Nghỉ delay {delay_between_pages}s (chuyển nick khác...)"
                    pool.release_account(acc, status="ready", cooldown_seconds=delay_between_pages)

            else:
                if res.get("is_token_die"):
                    acc.status = "die"
                    acc.current_action = "Nick mẹ đã DIE / Token hỏng -> Đã dừng nick"
                    with FILE_LOCK:
                        stats["total_token_die"] += 1
                    pool.release_account(acc, status="die")

                elif res.get("is_restricted"):
                    acc.status = "die"
                    acc.current_action = "Bị Facebook chặn tạo Page -> Đã dừng nick"
                    with FILE_LOCK:
                        stats["total_token_die"] += 1
                    pool.release_account(acc, status="die")

                elif res.get("is_limit"):
                    with FILE_LOCK:
                        stats["total_limited"] += 1

                    if limit_action == 1:
                        acc.status = "limit"
                        acc.current_action = "Bị Limit tạo Page -> Đã dừng nick"
                        pool.release_account(acc, status="limit")
                    else:
                        acc.current_action = f"Nghỉ chống limit {limit_delay_seconds}s rồi thử lại"
                        pool.release_account(acc, status="ready", cooldown_seconds=limit_delay_seconds)
                else:
                    err_msg = res.get("message", "Thất bại")[:40]
                    acc.current_action = f"Lỗi: {err_msg}"
                    chk = acc.creator.get_user_info()
                    if not chk.get("success") and chk.get("is_token_die"):
                        acc.status = "die"
                        acc.current_action = "Nick mẹ đã DIE -> Đã dừng nick"
                        with FILE_LOCK:
                            stats["total_token_die"] += 1
                        pool.release_account(acc, status="die")
                    else:
                        pool.release_account(acc, status="ready", cooldown_seconds=10)
        except Exception as e:
            acc.current_action = f"Lỗi luồng: {str(e)[:30]}"
            pool.release_account(acc, status="ready", cooldown_seconds=10)
            time.sleep(1)


def run_reg_page_menu():
    print_banner()
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== CẤU HÌNH REG PAGE PRO5 ĐA LUỒNG ==={Colors.RESET}\n")

    # 1. Nạp token
    safe_print(f"{Colors.CYAN}--- [1/8] NẠP DANH SÁCH TOKEN EAAAAU ---{Colors.RESET}")
    safe_print("[1] Dán trực tiếp vào màn hình (tự động nhận diện EAAAAU)")
    safe_print("[2] Đọc từ file tokens.txt")
    c_tok = input("Chọn cách nạp token (1 hoặc 2, mặc định 1): ").strip() or "1"

    raw_tokens = []
    if c_tok == "1":
        raw_tokens = input_multiline("Hãy dán danh sách Token / Acc vào đây:")
    else:
        fn = input("Nhập tên file token (mặc định tokens.txt): ").strip() or "tokens.txt"
        if os.path.exists(fn):
            with open(fn, "r", encoding="utf-8", errors="ignore") as f:
                raw_tokens = [l.strip() for l in f if l.strip()]
        else:
            safe_print(f"{Colors.RED}Không tìm thấy file {fn}!{Colors.RESET}")
            input("\nNhấn Enter để quay lại...")
            return

    parsed_items = parse_tokens_from_lines(raw_tokens)
    if not parsed_items:
        safe_print(f"{Colors.RED}Không tìm thấy Token EAAAAU nào hợp lệ!{Colors.RESET}")
        input("\nNhấn Enter để quay lại...")
        return

    safe_print(f"{Colors.GREEN}{Colors.BOLD} Đã nhận diện: {len(parsed_items)} Token EAAAAU hợp lệ!{Colors.RESET}\n")

    # 2. Tên Page
    safe_print(f"{Colors.CYAN}--- [2/8] CHỌN LOẠI TÊN PAGE ---{Colors.RESET}")
    safe_print("[1] Tên Việt thuần 100% (Ví dụ: Nguyễn Văn Khải, Trần Thị Mai...)")
    safe_print("[2] Tên Ngoại / US (Ví dụ: Sophia Davis, David Miller...)")
    safe_print("[3] Tự nạp danh sách tên từ file names.txt")
    c_name = input("Chọn loại tên (1, 2 hoặc 3, mặc định 1): ").strip() or "1"

    name_type = "viet"
    custom_names = []
    if c_name == "2":
        name_type = "us"
    elif c_name == "3":
        name_type = "custom"
        fn_name = input("Nhập tên file chứa tên (mặc định names.txt): ").strip() or "names.txt"
        if os.path.exists(fn_name):
            with open(fn_name, "r", encoding="utf-8", errors="ignore") as f:
                custom_names = [l.strip() for l in f if l.strip()]
            safe_print(f"{Colors.GREEN}Đã nạp {len(custom_names)} tên từ {fn_name}!{Colors.RESET}")
        else:
            safe_print(f"{Colors.YELLOW}Không tìm thấy {fn_name}, chuyển sang Tên Việt.{Colors.RESET}")
            name_type = "viet"

    safe_print(f"{Colors.GREEN}Chế độ tên: {name_type.upper()}{Colors.RESET}\n")

    # 3. User-Agent
    safe_print(f"{Colors.CYAN}--- [3/8] CƠ CHẾ USER-AGENT (KATANA ANDROID) ---{Colors.RESET}")
    safe_print("[1] Cố định 1 UA cho mỗi nick (1 nick dùng 1 UA duy nhất cho mọi page - Khuyên dùng)")
    safe_print("[2] Random UA mới mỗi lần tạo Page (Mỗi page tạo ra dùng 1 UA Katana mới ngẫu nhiên)")
    c_ua = input("Chọn cơ chế UA (1 hoặc 2, mặc định 1): ").strip() or "1"
    ua_mode = "random" if c_ua == "2" else "fixed"
    safe_print(f"{Colors.GREEN}Cơ chế UA: {'Random UA mới cho mỗi Page' if ua_mode == 'random' else 'Cố định 1 UA duy nhất cho mỗi Nick'}{Colors.RESET}\n")

    # 4. Proxy
    safe_print(f"{Colors.CYAN}--- [4/8] CẤU HÌNH PROXY ---{Colors.RESET}")
    global_proxies = []
    has_attached = any(it.get("proxy") for it in parsed_items)

    if has_attached:
        safe_print(f"{Colors.GREEN}Phát hiện các token đã có Proxy gắn kèm riêng.{Colors.RESET}\n")
    else:
        use_px = input("Có sử dụng Proxy không? (y/n, mặc định n): ").strip().lower()
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
                if parse_proxy(pl):
                    global_proxies.append(pl)
            safe_print(f"{Colors.GREEN}Đã nhận diện: {len(global_proxies)} Proxy hợp lệ!{Colors.RESET}\n")
        else:
            safe_print(f"{Colors.YELLOW}Chạy trực tiếp mạng máy tính / 4G của điện thoại.{Colors.RESET}\n")

    # 5. Số page & Delay
    safe_print(f"{Colors.CYAN}--- [5/8] SỐ LƯỢNG PAGE & NGHỈ DELAY ---{Colors.RESET}")
    try:
        pages_per_nick = int(input("Số lượng Page muốn reg trên 1 nick (Mặc định 1): ").strip() or "1")
    except ValueError:
        pages_per_nick = 1

    try:
        delay_between = int(input("Thời gian nghỉ trước khi reg page tiếp theo (giây, mặc định 10): ").strip() or "10")
    except ValueError:
        delay_between = 10
    safe_print("")

    # 6. Chế độ điều phối nick
    safe_print(f"{Colors.CYAN}--- [6/8] CHẾ ĐỘ ĐIỀU PHỐI TÀI KHOẢN KHI REG ---{Colors.RESET}")
    safe_print("[1] Tuần tự từng nick (Mỗi luồng hoàn thành xong nick này mới sang nick khác)")
    safe_print("[2] Xoay vòng nick / Round-Robin (Reg 1 page xong chuyển sang nick khác ngay, tận dụng thời gian nghỉ delay - Tối ưu tốc độ) [Khuyên dùng]")
    c_dispatch = input("Chọn chế độ (1 hoặc 2, mặc định 2): ").strip() or "2"
    run_mode = "sequential" if c_dispatch == "1" else "round_robin"
    safe_print(f"{Colors.GREEN}Chế độ điều phối: {'Xoay vòng nick (Round-Robin)' if run_mode == 'round_robin' else 'Tuần tự từng nick'}{Colors.RESET}\n")

    # 7. Xử lý Limit
    safe_print(f"{Colors.CYAN}--- [7/8] XỬ LÝ KHI BỊ LIMIT TẠO PAGE ---{Colors.RESET}")
    safe_print("[1] Dừng tạo trên nick đó ngay lập tức (Bảo vệ nick mẹ tránh DIE) [Khuyên dùng]")
    safe_print("[2] Cho nick nghỉ thêm thời gian rồi thử lại")
    limit_action = input("Chọn cách xử lý (1 hoặc 2, mặc định 1): ").strip() or "1"
    limit_delay = 300
    if limit_action == "2":
        try:
            limit_delay = int(input("Số giây nghỉ khi bị limit (Mặc định 300s): ").strip() or "300")
        except ValueError:
            limit_delay = 300
    limit_action_num = 2 if limit_action == "2" else 1
    safe_print("")

    # 8. Luồng
    safe_print(f"{Colors.CYAN}--- [8/8] SỐ LUỒNG CHẠY SONG SONG ---{Colors.RESET}")
    try:
        num_threads = int(input(f"Nhập số luồng (Mặc định {min(3, len(parsed_items))}): ").strip() or str(min(3, len(parsed_items))))
    except ValueError:
        num_threads = 3
    num_threads = max(1, min(num_threads, 50))

    input(f"\n{Colors.BOLD}{Colors.YELLOW}Bấm Enter để BẮT ĐẦU CHẠY REG PAGE...{Colors.RESET}")
    safe_print("\n" + "=" * 72)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} TIẾN TRÌNH REG PAGE PRO5 BẮT ĐẦU HOẠT ĐỘNG ({run_mode.upper()})...{Colors.RESET}")
    safe_print("=" * 72 + "\n")

    stats = {"total_success": 0, "total_limited": 0, "total_token_die": 0}
    actual_threads = min(num_threads, len(parsed_items))
    worker_threads = []
    stop_dashboard = threading.Event()

    account_tasks = []
    for idx, it in enumerate(parsed_items):
        assigned_px = global_proxies[idx % len(global_proxies)] if global_proxies and not it.get("proxy") else None
        account_tasks.append(AccountTask(
            acc_id=idx + 1,
            item=it,
            target_pages=pages_per_nick,
            ua_mode=ua_mode,
            assigned_proxy=assigned_px
        ))

    # Bật Dashboard theo dõi trạng thái Real-time
    dashboard_thread = threading.Thread(
        target=dashboard_render_loop,
        args=(account_tasks, stats, actual_threads, stop_dashboard),
        daemon=True
    )
    dashboard_thread.start()

    if run_mode == "round_robin":
        pool = RoundRobinPool(account_tasks)
        for t_id in range(1, actual_threads + 1):
            t = threading.Thread(
                target=worker_reg_page_round_robin,
                args=(
                    t_id, pool, name_type, custom_names,
                    delay_between, limit_action_num, limit_delay, stats
                ),
                daemon=True
            )
            worker_threads.append(t)
            t.start()

    else:
        task_queue = Queue()
        for acc in account_tasks:
            task_queue.put(acc)

        for t_id in range(1, actual_threads + 1):
            t = threading.Thread(
                target=worker_reg_page_sequential,
                args=(
                    t_id, task_queue, name_type, custom_names, pages_per_nick,
                    delay_between, limit_action_num, limit_delay, stats
                ),
                daemon=True
            )
            worker_threads.append(t)
            t.start()

    for t in worker_threads:
        t.join()

    # Tắt dashboard và hiển thị tổng kết
    stop_dashboard.set()
    dashboard_thread.join(timeout=1.5)
    render_dashboard(account_tasks, stats, actual_threads)

    safe_print("\n" + "=" * 72)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT TIẾN TRÌNH REG PAGE!{Colors.RESET}")
    safe_print(f"- Số Page tạo thành công: {Colors.GREEN}{stats['total_success']}{Colors.RESET}")
    safe_print(f"- Số nick gặp Limit: {Colors.YELLOW}{stats['total_limited']}{Colors.RESET}")
    safe_print(f"- Số nick bị Token DIE / Bị chặn: {Colors.RED}{stats['total_token_die']}{Colors.RESET}")
    safe_print(f"- Kết quả đã lưu tại: {Colors.CYAN}created_pages.txt{Colors.RESET}")
    safe_print("=" * 72 + "\n")
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
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== GET TOKEN EAAAAU TỪ ACC (UID|PASS|2FA) ==={Colors.RESET}\n")

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

    safe_print("\n" + "=" * 72)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT LẤY TOKEN EAAAAU!{Colors.RESET}")
    safe_print(f"- Lấy thành công: {Colors.GREEN}{stats['success']}{Colors.RESET}")
    safe_print(f"- Thất bại: {Colors.RED}{stats['fail']}{Colors.RESET}")
    safe_print(f"- Đã lưu file: {Colors.CYAN}tokens_eaaau.txt{Colors.RESET}")
    safe_print("=" * 72 + "\n")
    input("Nhấn Enter để quay lại menu chính...")


def main():
    while True:
        print_banner()
        safe_print(f"{Colors.BOLD}VUI LÒNG CHỌN CHỨC NĂNG:{Colors.RESET}")
        safe_print(f"{Colors.GREEN}[1] REG PAGE PRO5 HÀNG LOẠT (ĐA LUỒNG){Colors.RESET}")
        safe_print(f"{Colors.YELLOW}[2] GET TOKEN EAAAAU TỪ TÀI KHOẢN (UID|PASS|2FA){Colors.RESET}")
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
