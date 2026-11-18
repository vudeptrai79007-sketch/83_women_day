# -*- coding: utf-8 -*-
"""
================================================================================
TOOL REG PAGE PRO5 & GET TOKEN PAGE TỰ ĐỘNG - BẢN HIỂN THỊ CHI TIẾT QUÁ TRÌNH
Quy trình chuẩn cho từng Acc:
1. Kiểm tra Tài khoản (Nick Reg) & lưu danh sách Page cũ.
2. Tạo Page Pro5 (Hiện rõ Bước 1: Submit Tên -> Bước 2: Submit Danh mục).
3. Tạo xong -> Quét & GET LUÔN TOKEN PAGE vừa tạo (Page ID + Page Token EAAAAU).
4. Đợi đếm ngược 20s -> Check lại xem Tài khoản & Page vừa tạo còn SỐNG (LIVE) không.
5. Nếu Tài khoản & Page SỐNG -> Bắn lời mời Admin Page sang UID Nick Mẹ
   (Chỉ cần nhập UID Nick Mẹ, tự bấm Chấp nhận thủ công bên Nick Mẹ).
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
from collections import deque
from queue import Queue, Empty
from typing import Optional, Dict, Any, List

try:
    import requests
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    print("Vui lòng cài đặt requests bằng lệnh: pip install requests")
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
    safe_print("=" * 88)
    safe_print("   TOOL REG PAGE PRO5 -> GET TOKEN PAGE -> CHECK LIVE ACC & PAGE -> BẮN SANG UID MẸ   ")
    safe_print("          Chuẩn Katana FB4A Android | Hiện Chi Tiết Từng Bước | Đa Luồng               ")
    safe_print("=" * 88)
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
    """
    Tự động chuẩn hóa mọi định dạng proxy:
    - IPv4, IPv6 ([ipv6]:port:user:pass, ipv6:port...)
    - HTTP, HTTPS, SOCKS5, SOCKS4
    """
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
# 5. BỘ LỌC TỰ ĐỘNG BÓC TÁCH TOKEN EAAAAU, UID NICK MẸ & ACCOUNT
# ==============================================================================

def parse_token_line(line: str) -> Optional[Dict[str, str]]:
    """Tự động bóc tách Token EAAAAU, UID và Proxy từ một dòng bất kỳ."""
    raw = str(line).strip()
    if not raw or raw.startswith("#"):
        return None

    token_match = re.search(r'(EAAAAU[A-Za-z0-9]+)', raw)
    if not token_match:
        return None

    token = token_match.group(1).strip()
    proxy = None
    uid = None

    parts = raw.split("|")
    for p in parts:
        p_clean = p.strip()
        if p_clean.isdigit() and len(p_clean) >= 8:
            uid = p_clean
            break
        elif "c_user=" in p_clean:
            c_u = re.search(r'c_user=(\d+)', p_clean)
            if c_u:
                uid = c_u.group(1)
                break

    if not uid:
        u_match = re.search(r'\b(1000\d{10,12}|615\d{11,13}|\d{10,16})\b', raw)
        if u_match:
            uid = u_match.group(1)

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


def parse_holder_uid(line: str) -> Optional[str]:
    """Chỉ bóc tách UID của Nick Mẹ (chấp nhận mọi độ dài UID từ 5 đến 20 số)."""
    raw = str(line).strip()
    if not raw or raw.startswith("#"):
        return None
    uid_match = re.search(r'\b(\d{5,20})\b', raw)
    if not uid_match:
        return None
    return uid_match.group(1)


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
# 6. TỰ SINH MÃ 2FA TOTP THUẦN PYTHON & GET TOKEN EAAAAU TỪ ACC
# ==============================================================================

def generate_totp_code(secret: str) -> str:
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


def login_and_get_token(acc: Dict[str, str], custom_ua: Optional[str] = None) -> Dict[str, Any]:
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
        "X-FB-HTTP-Engine": "Liger",
    }

    url = "https://b-api.facebook.com/method/auth.login"
    device_id = str(uuid.uuid4())
    family_device_id = str(uuid.uuid4())

    data = {
        "adid": str(uuid.uuid4()),
        "format": "json",
        "device_id": device_id,
        "email": uid,
        "password": pwd,
        "generate_analytics_claim": "1",
        "community_id": "",
        "cpl": "true",
        "try_num": "1",
        "family_device_id": family_device_id,
        "credentials_type": "password",
        "generate_session_cookies": "1",
        "error_detail_type": "button_with_disabled",
        "source": "login",
        "generate_machine_id": "1",
        "meta_inf_fbmeta": "",
        "advertiser_id": str(uuid.uuid4()),
        "currently_logged_in_userid": "0",
        "locale": "vi_VN",
        "client_country_code": "VN",
        "method": "auth.login",
        "fb_api_req_friendly_name": "authenticate",
        "fb_api_caller_class": "com.facebook.account.login.protocol.Fb4aAuthHandler",
        "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32"
    }

    try:
        res = s.post(url, headers=headers, data=data, timeout=30).json()

        if res.get("error_code") in [406, 405] or "two_factor" in str(res).lower():
            if twofa:
                err_data = res.get("error_data", {})
                if isinstance(err_data, str):
                    try:
                        err_data = json.loads(err_data)
                    except Exception:
                        err_data = {}

                first_factor = err_data.get("login_first_factor", "")
                real_uid = str(err_data.get("uid", uid))
                code_2fa = generate_totp_code(twofa)

                if code_2fa:
                    data["email"] = real_uid
                    data["password"] = code_2fa
                    data["credentials_type"] = "two_factor"
                    data["two_factor_code"] = code_2fa
                    if first_factor:
                        data["first_factor"] = first_factor
                    res = s.post(url, headers=headers, data=data, timeout=30).json()

        if "access_token" in res:
            token = res["access_token"]
            return {
                "success": True,
                "uid": str(res.get("uid", uid)),
                "token": token,
                "name": res.get("user_storage", {}).get("name", "")
            }
        else:
            err = res.get("error_msg") or res.get("message") or str(res)
            return {"success": False, "uid": uid, "message": err}
    except Exception as e:
        return {"success": False, "uid": uid, "message": str(e)}


# ==============================================================================
# 7. CORE REG PAGE PRO5 -> GET TOKEN PAGE -> CHECK LIVE -> BẮN SANG UID MẸ
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

    def check_account_live(self) -> Dict[str, Any]:
        """Kiểm tra Tài khoản (Nick Reg) còn sống (LIVE) hay đã DIE."""
        try:
            r = self.session.get(
                f"https://graph.facebook.com/me?fields=id,name&access_token={self.token}",
                headers={"User-Agent": self.user_agent},
                timeout=25
            ).json()
            if "id" in r:
                self.mother_uid = str(r["id"])
                return {"success": True, "uid": str(r["id"]), "name": r.get("name", "Facebook User")}
            err = r.get("error", {})
            err_msg = err.get("message", "Token lỗi hoặc Nick DIE")
            is_die = (
                "OAuthException" in str(r)
                or err.get("code") in [190, 102]
                or "checkpoint" in str(r).lower()
                or "error" in r
            )
            return {"success": False, "is_token_die": is_die, "message": err_msg}
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

    def invite_holder_by_uid(
        self,
        page_id: str,
        page_token: str,
        holder_uid: str,
        additional_profile_id: str = ""
    ) -> Dict[str, Any]:
        """
        Bắn lời mời Admin Page sang UID Nick Mẹ (Chỉ dùng UID Nick Mẹ):
        - Gửi kết bạn từ Nick Reg sang UID Nick Mẹ để mở khóa mời Pro5.
        - Bắn lời mời FULL_ADMIN qua GraphQL Pro5 (có doc_id chuẩn) bằng Page Token.
        - Dự phòng bắn qua Graph API /v19.0/{page_id}/roles (với tasks chuẩn Pro5).
        - Kiểm tra kết quả phản hồi thật từ Facebook (không báo ảo).
        """
        holder_uid = str(holder_uid).strip()
        if not holder_uid:
            return {"success": False, "message": "Thiếu UID Nick Mẹ"}

        # 1. Đảm bảo có đủ page_token và additional_profile_id
        if not page_token or not additional_profile_id:
            info_p = self.check_single_page_live(page_id, page_token)
            if info_p.get("success"):
                page_token = page_token or info_p.get("page_token", "")
                additional_profile_id = additional_profile_id or info_p.get("additional_profile_id", "")

        # 2. Nick Reg tự động gửi lời mời kết bạn tới UID Nick Mẹ qua GraphQL
        if self.mother_uid and self.mother_uid != holder_uid:
            try:
                add_friend_vars = {
                    "input": {
                        "friend_requestee_ids": [str(holder_uid)],
                        "source": "profile_button",
                        "actor_id": str(self.mother_uid),
                        "client_mutation_id": str(uuid.uuid4())
                    }
                }
                self.session.post(
                    GRAPHQL_URL,
                    headers=self._get_headers("FriendRequestSendCoreMutation", token_override=self.token),
                    data={
                        "method": "post",
                        "pretty": "false",
                        "format": "json",
                        "fb_api_req_friendly_name": "FriendRequestSendCoreMutation",
                        "fb_api_caller_class": "graphservice",
                        "doc_id": "23999612633015775",
                        "variables": json.dumps(add_friend_vars)
                    },
                    timeout=15
                )
            except Exception:
                pass

        invited_ok = False
        last_err = "Không rõ nguyên nhân"
        actor_pro5 = str(additional_profile_id or page_id)

        # 3. CÁCH 1: Bắn lời mời FULL_ADMIN Pro5 qua GraphQL
        invite_doc_ids = ["6022111457862078", "5367441956638909", "7219129478152946"]
        auth_pairs = [
            (page_token, actor_pro5),
            (self.token, actor_pro5),
            (self.token, str(self.mother_uid or page_id))
        ]

        for tk, act_id in auth_pairs:
            if not tk or invited_ok:
                continue
            for doc_id in invite_doc_ids:
                try:
                    variables = {
                        "input": {
                            "additional_profile_id": actor_pro5,
                            "page_id": str(page_id),
                            "invitee_id": str(holder_uid),
                            "admin_type": "FULL_ADMIN",
                            "actor_id": act_id,
                            "client_mutation_id": str(uuid.uuid4())
                        }
                    }
                    gql_data = {
                        "method": "post",
                        "pretty": "false",
                        "format": "json",
                        "server_timestamps": "true",
                        "locale": "vi_VN",
                        "fb_api_req_friendly_name": "ProfilePlusCoreAdminInviteMutation",
                        "fb_api_caller_class": "graphservice",
                        "doc_id": doc_id,
                        "variables": json.dumps(variables),
                        "client_trace_id": str(uuid.uuid4())
                    }
                    r_gql = self.session.post(
                        GRAPHQL_URL,
                        headers=self._get_headers("ProfilePlusCoreAdminInviteMutation", token_override=tk),
                        data=gql_data,
                        timeout=20
                    )
                    res_json = r_gql.json()
                    if (
                        "error" not in res_json
                        and "errors" not in res_json
                        and res_json.get("data")
                        and any(res_json["data"].values())
                    ):
                        invited_ok = True
                        break
                    else:
                        err_obj = res_json.get("error") or (res_json.get("errors", [{}])[0])
                        if isinstance(err_obj, dict) and err_obj.get("message"):
                            last_err = err_obj.get("message")
                except Exception as e:
                    last_err = str(e)

        # 4. CÁCH 2 (Dự phòng): Bắn lời mời qua Graph API /roles với tasks chuẩn Pro5
        if not invited_ok:
            tasks_json = json.dumps(["MANAGE", "CREATE_CONTENT", "MODERATE", "ADVERTISE", "ANALYZE"])
            for tk in [page_token, self.token]:
                if not tk or invited_ok:
                    continue
                try:
                    r_role = self.session.post(
                        f"https://graph.facebook.com/v19.0/{page_id}/roles",
                        data={
                            "user": holder_uid,
                            "tasks": tasks_json,
                            "access_token": tk
                        },
                        headers={"User-Agent": self.user_agent},
                        timeout=20
                    ).json()
                    if r_role is True or r_role.get("success") is True:
                        invited_ok = True
                        break
                    elif "error" in r_role:
                        last_err = r_role["error"].get("message", last_err)
                except Exception as e:
                    last_err = str(e)

        if invited_ok:
            return {
                "success": True,
                "message": f"Đã bắn lời mời Admin sang UID {holder_uid} (Chờ bấm Chấp nhận)"
            }
        else:
            return {
                "success": False,
                "message": f"Lỗi bắn sang UID {holder_uid}: {last_err[:50]}"
            }


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
        self.token = item.get("token", "")
        self.proxy = item.get("proxy") or assigned_proxy
        self.holder_uid = holder_uid or ""
        self.target_pages = target_pages
        self.pages_created = 0
        self.ua_mode = ua_mode
        self.fixed_ua = generate_random_katana_ua(seed=self.token) if ua_mode == "fixed" else None
        self.creator = FbPageCreator(token=self.token, proxy=self.proxy, user_agent=self.fixed_ua, ua_mode=ua_mode)
        self.pre_uid = item.get("uid") or ""
        self.mother_uid = self.pre_uid
        self.mother_name = ""
        self.status = "ready"  # ready, running, waiting_check, done, no_page, limit, die
        self.current_action = "Chờ đến lượt..."
        self.last_result = ""


def render_dashboard(accounts: List[AccountTask], stats: Dict[str, int]):
    lines = []
    w = 114
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(
        f"{Colors.BOLD}{Colors.YELLOW}"
        f"     BẢNG TIẾN TRÌNH: TẠO PAGE -> GET TOKEN PAGE -> CHECK LIVE ACC & PAGE -> BẮN SANG UID NICK MẸ     "
        f"{Colors.RESET}"
    )
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(f"{Colors.BOLD} STT | UID Nick Reg     | Tên Nick         | Page Có | Quá trình / Trạng thái hiện tại{Colors.RESET}")
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

    # Khung hiển thị chi tiết từng bước tạo Page, Get Token Page, Check Live và Bắn UID
    lines.append(f"{Colors.BOLD}{Colors.MAGENTA} 📋 NHẬT KÝ QUÁ TRÌNH CHI TIẾT (TẠO PAGE -> GET TOKEN PAGE -> CHECK LIVE -> BẮN UID):{Colors.RESET}")
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
    """
    Quy trình 5 bước rõ ràng cho mỗi Acc:
    1. Check Live Tài khoản ban đầu & ghi nhận các Page cũ đã có sẵn.
    2. Tạo từng Page -> Tạo xong lấy luôn Token EAAAAU của Page đó (`page_token`).
    3. Đợi đếm ngược (ví dụ 20s).
    4. Check lại xem Tài khoản & từng Page vừa tạo còn SỐNG (LIVE) không.
    5. Nếu sống -> Bắn lời mời Admin sang UID Nick Mẹ & lưu file.
    """
    acc.status = "running"
    acc.current_action = f"[L{thread_id}] Bước 1: Đang kiểm tra Tài khoản & quét Page cũ..."
    add_process_log(acc.acc_id, acc.pre_uid, "Bước 1: Đang kiểm tra Token Tài khoản ban đầu...")

    # --- BƯỚC 1: KIỂM TRA TÀI KHOẢN & LƯU DANH SÁCH PAGE CŨ ---
    acc_info = acc.creator.check_account_live()
    if not acc_info.get("success"):
        acc.status = "die"
        acc.mother_uid = acc.pre_uid or "Unknown"
        acc.mother_name = "Nick DIE / Checkpoint"
        err_msg = acc_info.get("message", "Token DIE")
        acc.current_action = f"Tài khoản DIE từ đầu ({err_msg[:30]}) -> Lưu acc_die.txt"
        add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Tài khoản DIE ngay từ đầu: {err_msg[:45]}{Colors.RESET}")
        with FILE_LOCK:
            stats["total_token_die"] += 1
            with open("acc_die.txt", "a", encoding="utf-8") as f:
                f.write(f"{acc.mother_uid}|{acc.token}|DIE_TRUOC_KHI_REG\n")
        return

    acc.mother_uid = acc_info.get("uid", acc.pre_uid)
    acc.mother_name = acc_info.get("name", "Facebook User")

    pre_pages_res = acc.creator.get_all_pages_with_tokens()
    known_page_ids = {str(p.get("id", "")) for p in pre_pages_res.get("pages", []) if p.get("id")}
    add_process_log(
        acc.acc_id,
        acc.mother_uid,
        f"{Colors.GREEN}✔ Nick LIVE ({acc.mother_name}) - Đang có sẵn {len(known_page_ids)} Page cũ.{Colors.RESET}"
    )

    # --- BƯỚC 2 & 3: TẠO PAGE VÀ GET LUÔN TOKEN CỦA PAGE VỪA TẠO ---
    newly_created_pages: List[Dict[str, str]] = []
    hit_limit = False
    hit_restricted = False

    for idx in range(1, acc.target_pages + 1):
        page_name = get_page_name(name_type, custom_names)

        def update_step(msg_step: str):
            acc.current_action = f"[L{thread_id}] Reg Page ({idx}/{acc.target_pages}) - {msg_step}"
            add_process_log(acc.acc_id, acc.mother_uid, f"[Page {idx}/{acc.target_pages}] {msg_step}")

        create_res = acc.creator.create_page_and_get_token(
            page_name=page_name,
            known_page_ids=known_page_ids,
            step_callback=update_step
        )

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
            newly_created_pages.append({
                "id": p_id,
                "name": p_name,
                "access_token": p_token,
                "additional_profile_id": add_prof_id
            })
            acc.pages_created = len(newly_created_pages)

            short_ptk = f"{p_token[:18]}..." if p_token else "Chưa cấp riêng"
            acc.current_action = f"[L{thread_id}] Đã tạo Page {p_id} & Get Token Page ({short_ptk})"
            add_process_log(
                acc.acc_id,
                acc.mother_uid,
                f"{Colors.GREEN}🎉 Tạo thành công Page '{p_name}' (ID: {p_id}) | Token Page: {short_ptk}{Colors.RESET}"
            )
        else:
            err_detail = create_res.get("message", "Không lên Page")
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}⚠️ Lần tạo {idx}: {err_detail}{Colors.RESET}")

        if idx < acc.target_pages and delay_between_pages > 0:
            for s_rem in range(delay_between_pages, 0, -1):
                acc.current_action = f"[L{thread_id}] Nghỉ {s_rem}s trước khi tạo Page ({idx + 1}/{acc.target_pages})..."
                time.sleep(1)

    # Nếu không tạo được Page mới nào
    if not newly_created_pages:
        if hit_limit:
            acc.status = "limit"
            acc.current_action = "Acc bị Limit tạo Page -> Đã bỏ qua"
            with FILE_LOCK:
                stats["total_limited"] += 1
            return
        else:
            acc.status = "no_page"
            reason_str = "Nick bị chặn (CRITICAL)" if hit_restricted else "Tạo xong nhưng không ra Page mới"
            acc.current_action = f"{reason_str} -> Lưu acc_reg_xit.txt"
            with FILE_LOCK:
                stats["total_no_page"] += 1
                with open("acc_reg_xit.txt", "a", encoding="utf-8") as f:
                    f.write(f"{acc.mother_uid}|{acc.token}|KHONG_LEN_PAGE\n")
            return

    # --- BƯỚC 4: ĐỢI ĐẾM NGƯỢC & CHECK XEM TÀI KHOẢN VÀ PAGE CÒN SỐNG KHÔNG ---
    acc.status = "waiting_check"
    wait_seconds = max(1, int(verify_delay))
    add_process_log(
        acc.acc_id,
        acc.mother_uid,
        f"⏳ Đang đợi {wait_seconds}s trước khi kiểm tra lại Tài khoản & Page sống/chết..."
    )
    for rem in range(wait_seconds, 0, -1):
        acc.current_action = f"[L{thread_id}] Đợi {rem}s để check lại Tài khoản & {len(newly_created_pages)} Page sống/chết..."
        time.sleep(1)

    acc.status = "running"
    acc.current_action = f"[L{thread_id}] Đang check LIVE Tài khoản & Page vừa tạo..."

    # 4.1: Check lại Tài khoản (Nick Reg)
    recheck_acc = acc.creator.check_account_live()
    if not recheck_acc.get("success"):
        acc.status = "die"
        acc.current_action = f"Sau {wait_seconds}s: Tài khoản bị DIE / Checkpoint!"
        add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Sau {wait_seconds}s: Tài khoản bị DIE / Checkpoint!{Colors.RESET}")
        with FILE_LOCK:
            stats["total_token_die"] += 1
            with open("acc_die.txt", "a", encoding="utf-8") as f:
                f.write(f"{acc.mother_uid}|{acc.token}|DIE_SAU_{wait_seconds}S\n")
        return

    # 4.2: Check lại từng Page vừa tạo xem còn sống (LIVE) và lấy lại Token Page mới nhất
    live_pages: List[Dict[str, Any]] = []
    for p in newly_created_pages:
        p_id = p["id"]
        p_tk = p["access_token"]
        page_live_res = acc.creator.check_single_page_live(page_id=p_id, page_token=p_tk)
        if page_live_res.get("success"):
            p["access_token"] = page_live_res.get("page_token") or p_tk
            p["additional_profile_id"] = page_live_res.get("additional_profile_id") or p.get("additional_profile_id", "")
            live_pages.append(p)
            add_process_log(
                acc.acc_id,
                acc.mother_uid,
                f"{Colors.GREEN}✔ Check LIVE thành công: Nick SỐNG & Page {p_id} ('{p['name']}') SỐNG!{Colors.RESET}"
            )
        else:
            add_process_log(
                acc.acc_id,
                acc.mother_uid,
                f"{Colors.RED}❌ Page {p_id} bị DIE/Hủy đăng sau {wait_seconds}s: {page_live_res.get('message')}{Colors.RESET}"
            )

    if not live_pages:
        acc.status = "no_page"
        acc.current_action = f"Check sau {wait_seconds}s: Page vừa tạo đã bị hủy đăng/DIE!"
        with FILE_LOCK:
            stats["total_no_page"] += 1
            with open("acc_reg_xit.txt", "a", encoding="utf-8") as f:
                f.write(f"{acc.mother_uid}|{acc.token}|PAGE_DIE_SAU_{wait_seconds}S\n")
        return

    # --- BƯỚC 5: BẮN PAGE SANG UID NICK MẸ (CHỈ DÙNG UID NICK MẸ) ---
    acc.pages_created = len(live_pages)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page_summary_list = []
    transfer_note = "Đã lưu Page & Token vào acc_cam_page.txt"

    for p in live_pages:
        p_id = str(p["id"])
        p_name = str(p["name"])
        p_token = str(p["access_token"])
        add_prof_id = str(p.get("additional_profile_id", ""))
        page_summary_list.append(f"{p_id}:{p_name}")

        if acc.holder_uid:
            acc.current_action = f"[L{thread_id}] Đang bắn lời mời Admin Page {p_id} sang UID {acc.holder_uid}..."
            add_process_log(
                acc.acc_id,
                acc.mother_uid,
                f"🚀 Đang bắn lời mời Admin Page {p_id} sang UID Nick Mẹ ({acc.holder_uid})..."
            )
            tr_res = acc.creator.invite_holder_by_uid(
                page_id=p_id,
                page_token=p_token,
                holder_uid=acc.holder_uid,
                additional_profile_id=add_prof_id
            )
            p["transfer_ok"] = tr_res.get("success", False)
            transfer_note = tr_res.get("message", "")
            if p["transfer_ok"]:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}✅ {transfer_note}{Colors.RESET}")
            else:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}⚠️ {transfer_note}{Colors.RESET}")
        else:
            p["transfer_ok"] = False

    # Ghi kết quả đầy đủ (kèm Page Token EAAAAU vừa get) vào file
    with FILE_LOCK:
        stats["total_holder_acc"] += 1
        stats["total_pages"] += len(live_pages)

        for p in live_pages:
            p_id = str(p["id"])
            p_name = str(p["name"])
            p_token = str(p["access_token"])
            if p.get("transfer_ok"):
                stats["total_invited"] += 1

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
    thread_id: int,
    queue: Queue,
    name_type: str,
    custom_names: Optional[List[str]],
    verify_delay: int,
    delay_between_pages: int,
    stats: Dict[str, int]
):
    while True:
        try:
            acc = queue.get(timeout=2.0)
        except Empty:
            break

        try:
            process_single_account_workflow(
                thread_id=thread_id,
                acc=acc,
                name_type=name_type,
                custom_names=custom_names,
                verify_delay=verify_delay,
                delay_between_pages=delay_between_pages,
                stats=stats
            )
        except Exception as e:
            acc.status = "die"
            acc.current_action = f"Lỗi ngoại lệ: {str(e)[:40]}"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Lỗi ngoại lệ: {str(e)[:50]}{Colors.RESET}")
        finally:
            queue.task_done()


# ==============================================================================
# 10. MENU CẤU HÌNH & CHẠY TOOL
# ==============================================================================

def run_reg_page_menu():
    print_banner()
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== CẤU HÌNH: TẠO PAGE -> GET TOKEN PAGE -> CHECK LIVE -> BẮN SANG UID NICK MẸ ==={Colors.RESET}\n")

    # 1. Nạp Token
    safe_print(f"{Colors.CYAN}--- [1/7] NẠP DANH SÁCH TOKEN EAAAAU CẦN REG ---{Colors.RESET}")
    safe_print("[1] Dán trực tiếp vào màn hình (tự động lọc EAAAAU)")
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

    safe_print(f"{Colors.GREEN}{Colors.BOLD}Đã nhận diện: {len(parsed_items)} Acc (Token EAAAAU) hợp lệ!{Colors.RESET}\n")

    # 2. Nhập UID Nick Mẹ để nhận lời mời Admin (Chỉ cần nhập UID)
    safe_print(f"{Colors.CYAN}--- [2/7] NHẬP UID NICK MẸ (ACC CẦM PAGE) ĐỂ BẮN PAGE SANG ---{Colors.RESET}")
    safe_print("Nhập UID của Nick Mẹ (chỉ cần gửi UID, có thể nhập 1 hoặc nhiều UID cách nhau bằng dấu phẩy).")
    safe_print("Nếu để trống và nhấn Enter -> Tool chỉ tạo Page, get Token Page và lưu vào file.")
    h_raw = input("Nhập UID Nick Mẹ: ").strip()

    holder_uids: List[str] = []
    if h_raw:
        for part in re.split(r"[,;\s]+", h_raw):
            u_parsed = parse_holder_uid(part)
            if u_parsed:
                holder_uids.append(u_parsed)

    if holder_uids:
        safe_print(f"{Colors.GREEN}✔ Sẽ tự động bắn lời mời Admin Page sang UID Nick Mẹ: {', '.join(holder_uids)} (Bạn tự bấm Chấp nhận bên Nick Mẹ).{Colors.RESET}\n")
    else:
        safe_print(f"{Colors.YELLOW}Không nhập UID Nick Mẹ -> Chỉ tạo Page, Get Token Page và lưu vào acc_cam_page.txt.{Colors.RESET}\n")

    # 3. Tên Page
    safe_print(f"{Colors.CYAN}--- [3/7] CHỌN LOẠI TÊN PAGE ---{Colors.RESET}")
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

    # 4. User-Agent
    safe_print(f"{Colors.CYAN}--- [4/7] CƠ CHẾ USER-AGENT (KATANA ANDROID) ---{Colors.RESET}")
    safe_print("[1] Cố định 1 UA cho mỗi nick [Khuyên dùng]")
    safe_print("[2] Random UA mới mỗi lần tạo Page")
    c_ua = input("Chọn cơ chế UA (1 hoặc 2, mặc định 1): ").strip() or "1"
    ua_mode = "random" if c_ua == "2" else "fixed"
    safe_print("")

    # 5. Proxy
    safe_print(f"{Colors.CYAN}--- [5/7] CẤU HÌNH PROXY ---{Colors.RESET}")
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

    # 6. Số page trên 1 acc & Thời gian đợi check Live
    safe_print(f"{Colors.CYAN}--- [6/7] SỐ PAGE TRÊN 1 ACC & THỜI GIAN ĐỢI CHECK LIVE ACC + PAGE ---{Colors.RESET}")
    try:
        pages_per_nick = int(input("Số lượng Page muốn reg trên 1 Acc (Mặc định 1): ").strip() or "1")
    except ValueError:
        pages_per_nick = 1

    try:
        verify_delay = int(input("Sau khi tạo & get Token Page xong, đợi bao nhiêu giây để check lại Acc & Page sống/chết? (Mặc định 20): ").strip() or "20")
    except ValueError:
        verify_delay = 20

    delay_between = 5
    if pages_per_nick > 1:
        try:
            delay_between = int(input("Thời gian nghỉ giữa các Page trong cùng 1 Acc (giây, mặc định 5): ").strip() or "5")
        except ValueError:
            delay_between = 5
    safe_print("")

    # 7. Luồng
    safe_print(f"{Colors.CYAN}--- [7/7] SỐ LUỒNG CHẠY SONG SONG ---{Colors.RESET}")
    try:
        num_threads = int(input(f"Nhập số luồng (Mặc định {min(3, len(parsed_items))}): ").strip() or str(min(3, len(parsed_items))))
    except ValueError:
        num_threads = 3
    num_threads = max(1, min(num_threads, 50))

    input(f"\n{Colors.BOLD}{Colors.YELLOW}Bấm Enter để BẮT ĐẦU CHẠY...{Colors.RESET}")

    with LOG_LOCK:
        LIVE_PROCESS_LOGS.clear()

    stats = {
        "total_holder_acc": 0,
        "total_pages": 0,
        "total_invited": 0,
        "total_no_page": 0,
        "total_limited": 0,
        "total_token_die": 0
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
            acc_id=idx + 1,
            item=it,
            target_pages=pages_per_nick,
            ua_mode=ua_mode,
            assigned_proxy=assigned_px,
            holder_uid=assigned_uid
        )
        account_tasks.append(task_obj)
        task_queue.put(task_obj)

    dashboard_thread = threading.Thread(
        target=dashboard_render_loop,
        args=(account_tasks, stats, stop_dashboard),
        daemon=True
    )
    dashboard_thread.start()

    for t_id in range(1, actual_threads + 1):
        t = threading.Thread(
            target=worker_reg_account,
            args=(t_id, task_queue, name_type, custom_names, verify_delay, delay_between, stats),
            daemon=True
        )
        worker_threads.append(t)
        t.start()

    for t in worker_threads:
        t.join()

    stop_dashboard.set()
    dashboard_thread.join(timeout=1.5)
    render_dashboard(account_tasks, stats)

    safe_print("\n" + "=" * 88)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT TIẾN TRÌNH!{Colors.RESET}")
    safe_print(f"- Số Acc sống & có Page sống sau {verify_delay}s: {Colors.GREEN}{stats['total_holder_acc']} Acc ({stats['total_pages']} Page){Colors.RESET}")
    safe_print(f"- Số Page đã bắn lời mời Admin thành công sang UID Nick Mẹ: {Colors.CYAN}{stats['total_invited']} Page{Colors.RESET}")
    safe_print(f"- Số Acc không lên Page hoặc Page bị hủy đăng: {Colors.MAGENTA}{stats['total_no_page']}{Colors.RESET}")
    safe_print(f"- Số Acc gặp Limit: {Colors.YELLOW}{stats['total_limited']}{Colors.RESET}")
    safe_print(f"- Số Acc bị Token DIE / Checkpoint: {Colors.RED}{stats['total_token_die']}{Colors.RESET}")
    safe_print(f"- File lưu Acc + Page + Token Page + Trạng thái bắn UID: {Colors.CYAN}acc_cam_page.txt{Colors.RESET}")
    safe_print(f"- File lưu danh sách Page & Token Page riêng: {Colors.CYAN}created_pages.txt{Colors.RESET}")
    if holder_uids:
        safe_print(f"- Link vào Nick Mẹ bấm Chấp nhận lời mời Trang: {Colors.YELLOW}https://www.facebook.com/pages/?category=invites{Colors.RESET}")
    safe_print("=" * 88 + "\n")
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
        safe_print(f"{Colors.GREEN}[1] REG PAGE PRO5 -> GET TOKEN PAGE -> CHECK LIVE ACC & PAGE -> BẮN SANG UID NICK MẸ{Colors.RESET}")
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
