# -*- coding: utf-8 -*-
"""
================================================================================
TOOL REG PAGE PRO5 -> GET TOKEN PAGE -> CHECK LIVE -> CHUYỂN PAGE MTOOL MAX
Tích hợp nguyên bản cơ chế 4 Bước Smali MTool Max (Li2/S, Lh2/X0, Lh2/y, LD2/q):
- Bước 1: Kiểm tra Tài khoản (Nick Reg) & lưu danh sách Page cũ.
- Bước 2: Tạo Page Pro5 (Submit Name -> Submit Category) & Get Token Page EAAAAU.
- Bước 3: Đợi đếm ngược -> Check lại Tài khoản & Page vừa tạo còn SỐNG (LIVE).
- Bước 4: Chuyển Page sang Nick Mẹ bằng chuẩn MTool Max:
    + Step 1: Xác thực mật khẩu Nick Reg (permissions_reauth).
    + Step 2: Kích hoạt cấp quyền full_access & bắn thông báo mời sang UID Mẹ.
    + Step 3: (Tùy chọn nếu có Token Mẹ) Tự động lấy mã invitation_id.
    + Step 4: (Tùy chọn nếu có Token Mẹ) Tự động chấp nhận (Auto Accept) Admin.
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

LIVE_PROCESS_LOGS = deque(maxlen=18)


def safe_print(msg: str):
    """In ra màn hình an toàn đa luồng."""
    with PRINT_LOCK:
        print(msg)
        sys.stdout.flush()


def add_process_log(acc_id: int, uid: str, msg: str):
    """Ghi nhật ký từng bước vào khung theo dõi."""
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
    safe_print("=" * 94)
    safe_print("   TOOL REG PAGE PRO5 -> GET TOKEN PAGE -> CHECK LIVE -> CHUYỂN PAGE & AUTO ACCEPT (MTOOL)   ")
    safe_print("        Chuẩn Katana FB4A & NativeTemplate Smali MTool Max | Đa Luồng | Chống Báo Ảo         ")
    safe_print("=" * 94)
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
# 2. XỬ LÝ PROXY CHẶT CHẼ (CHỐNG NHẬN NHẦM PASSWORD/COOKIE THÀNH PROXY)
# ==============================================================================

def _is_valid_port(port_str: str) -> bool:
    if not port_str or not port_str.isdigit():
        return False
    p_num = int(port_str)
    return 1 <= p_num <= 65535


def _is_valid_host(host_str: str) -> bool:
    if not host_str:
        return False
    h = host_str.strip("[]")
    if any(ch in h for ch in [" ", ";", "=", "|", "/", "\\", "?"]):
        return False
    # IPv4
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", h):
        return all(0 <= int(o) <= 255 for o in h.split("."))
    # IPv6
    if ":" in h and re.match(r"^[0-9a-fA-F:]+$", h):
        return True
    # Tên miền
    if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", h):
        return True
    return False


def parse_proxy(proxy_str: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Chuẩn hóa mọi định dạng Proxy hợp lệ (IPv4, IPv6, HTTP, SOCKS4, SOCKS5).
    Trả về None nếu chuỗi truyền vào là mật khẩu, cookie hoặc dữ liệu không phải Proxy.
    """
    if not proxy_str or not str(proxy_str).strip():
        return None
    raw = str(proxy_str).strip()

    if any(k in raw for k in ["c_user=", "xs=", "datr=", "EAAAA", "EAAG", " ", "|"]):
        return None

    scheme = "http"
    lower = raw.lower()
    for sc in ("http://", "https://", "socks5://", "socks4://"):
        if lower.startswith(sc):
            scheme = sc[:-3]
            raw = raw[len(sc):]
            break

    host, port, user, password = None, None, None, None

    if "@" in raw:
        auth_part, host_part = raw.rsplit("@", 1)
        if ":" in auth_part:
            user, password = auth_part.split(":", 1)
        if host_part.startswith("[") and "]:" in host_part:
            h_ipv6, port = host_part[1:].rsplit("]:", 1)
            host = f"[{h_ipv6}]"
        elif ":" in host_part:
            host, port = host_part.rsplit(":", 1)
    else:
        m_bracket = re.match(r"^\[([a-fA-F0-9:]+)\]:(\d+)(?::([^:]+):(.+))?$", raw)
        if m_bracket:
            ipv6, port, user, password = m_bracket.groups()
            host = f"[{ipv6}]"
        else:
            parts = raw.split(":")
            if len(parts) == 2:
                host, port = parts[0], parts[1]
            elif len(parts) == 4:
                if _is_valid_host(parts[0]) and _is_valid_port(parts[1]):
                    host, port, user, password = parts[0], parts[1], parts[2], parts[3]
                elif _is_valid_host(parts[2]) and _is_valid_port(parts[3]):
                    user, password, host, port = parts[0], parts[1], parts[2], parts[3]
            elif len(parts) > 4:
                if _is_valid_port(parts[-3]):
                    ipv6_cand = ":".join(parts[:-3])
                    if _is_valid_host(ipv6_cand):
                        host, port, user, password = f"[{ipv6_cand}]", parts[-3], parts[-2], parts[-1]
                elif _is_valid_port(parts[-1]):
                    ipv6_cand = ":".join(parts[:-1])
                    if _is_valid_host(ipv6_cand):
                        host, port = f"[{ipv6_cand}]", parts[-1]

    if not host or not port or not _is_valid_host(host) or not _is_valid_port(port):
        return None

    if user is not None and password is not None:
        u_enc = urllib.parse.quote(user.strip())
        p_enc = urllib.parse.quote(password.strip())
        proxy_url = f"{scheme}://{u_enc}:{p_enc}@{host}:{port}"
    else:
        proxy_url = f"{scheme}://{host}:{port}"

    return {"http": proxy_url, "https": proxy_url}


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

    return (
        f"[FBAN/FB4A;FBAV/{fbav};FBBV/{fbbv};FBDM/{{density={density},width={w},height={h}}};"
        f"FBLC/{locale};FBRV/0;FBCR/{carrier};FBMF/{mfg.lower()};FBBD/{brand};FBPN/com.facebook.katana;"
        f"FBDV/{dev_code};FBSV/{android_ver};FBOP/1;FBCA/x86_64:arm64-v8a;]"
    )


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
# 5. BỘ LỌC BÓC TÁCH TOKEN EAAAAU, PASSWORD, PROXY & THÔNG TIN NICK MẸ
# ==============================================================================

def _is_2fa_secret(s: str) -> bool:
    clean = s.replace(" ", "")
    if len(clean) in (16, 24, 32) and re.match(r"^[A-Z2-7a-z]+=*$", clean):
        if clean.isupper() or (len(clean) == 32 and clean.isalnum()):
            return True
    return False


def parse_token_line(line: str) -> Optional[Dict[str, str]]:
    """
    Tự động bóc tách Token EAAAAU, UID, Password (để dùng cho Step 1 MTool), và Proxy.
    Hỗ trợ mọi thứ tự cột ngăn cách bởi dấu '|':
    - UID|PASS|2FA|COOKIE|EAAAAU...|PROXY
    - UID|PASS|EAAAAU...|PROXY
    - UID|EAAAAU...
    - EAAAAU...|PASS
    """
    raw = str(line).strip()
    if not raw or raw.startswith("#"):
        return None

    token_match = re.search(r"(EAAAA[A-Za-z0-9]+)", raw)
    if not token_match:
        return None

    token = token_match.group(1).strip()
    uid = None
    pwd = ""
    proxy = None

    parts = [p.strip() for p in raw.split("|") if p.strip()]

    # Tìm UID
    for p in parts:
        if p.isdigit() and 8 <= len(p) <= 20:
            uid = p
            break
        elif "c_user=" in p:
            c_u = re.search(r"c_user=(\d+)", p)
            if c_u:
                uid = c_u.group(1)
                break

    if not uid:
        u_match = re.search(r"\b(1000\d{10,12}|615\d{11,13}|\d{10,16})\b", raw)
        if u_match:
            uid = u_match.group(1)

    # Tìm Proxy hợp lệ & Password
    for p in parts:
        if p == token or p == uid:
            continue
        if "EAAAA" in p or "c_user=" in p or "xs=" in p:
            continue
        if p.startswith(("DIE_", "KHONG_LEN", "PAGE_", "DA_BAN", "LOI_BAN")):
            continue
        if re.match(r"^\d{4}-\d{2}-\d{2}", p):
            continue

        if not proxy and parse_proxy(p):
            proxy = p
            continue

        if _is_2fa_secret(p):
            continue

        if not pwd and len(p) >= 4:
            pwd = p

    return {
        "token": token,
        "uid": uid or "",
        "pwd": pwd,
        "proxy": proxy,
        "raw": raw
    }


def parse_tokens_from_lines(lines: List[str]) -> List[Dict[str, str]]:
    results = []
    for line in lines:
        it = parse_token_line(line)
        if it:
            results.append(it)
    return results


def parse_holder_target(raw_input: str) -> List[Dict[str, Optional[str]]]:
    """
    Hỗ trợ nhập Nick Mẹ ở dạng:
    - Chỉ UID: 1000123456789 (Chạy Step 1 + Step 2 bắn thông báo lời mời)
    - Kèm Token Mẹ: 1000123456789|EAAAAU... (Chạy Full 4 Step + Auto Accept tự động)
    - Kèm Proxy Mẹ: 1000123456789|EAAAAU...|ip:port:user:pass
    """
    targets = []
    if not raw_input or not raw_input.strip():
        return targets

    chunks = [c.strip() for c in re.split(r"[\n,;]+", raw_input) if c.strip()]
    for chunk in chunks:
        uid = None
        token = None
        proxy = None

        parts = [p.strip() for p in chunk.split("|") if p.strip()]
        for p in parts:
            tk_m = re.search(r"(EAAAA[A-Za-z0-9]+|EAAG[A-Za-z0-9]+)", p)
            if tk_m and not token:
                token = tk_m.group(1)
            elif p.isdigit() and 5 <= len(p) <= 20 and not uid:
                uid = p
            elif parse_proxy(p) and not proxy:
                proxy = p

        if not uid:
            u_m = re.search(r"\b(\d{6,20})\b", chunk)
            if u_m:
                uid = u_m.group(1)

        if uid or token:
            targets.append({
                "uid": uid or "",
                "token": token,
                "proxy": proxy
            })
    return targets


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
        if "c_user=" in p:
            cookie = p
        elif parse_proxy(p):
            proxy = p
        elif _is_2fa_secret(p) or (len(p.replace(" ", "")) in [16, 24, 32]) or (len(p) == 6 and p.isdigit()):
            twofa = p

    return {"uid": uid, "pwd": pwd, "twofa": twofa, "cookie": cookie, "proxy": proxy, "raw": raw}


# ==============================================================================
# 6. TỰ SINH MÃ 2FA TOTP & ĐĂNG NHẬP GET TOKEN EAAAAU
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
                "pwd": pwd,
                "token": token,
                "name": res.get("user_storage", {}).get("name", "")
            }
        else:
            err = res.get("error_msg") or res.get("message") or str(res)
            return {"success": False, "uid": uid, "message": err}
    except Exception as e:
        return {"success": False, "uid": uid, "message": str(e)}


# ==============================================================================
# 7. MODULE CHUYỂN PAGE & AUTO ACCEPT 4 BƯỚC (NGUYÊN BẢN SMALI MTOOL MAX)
# ==============================================================================

class FacebookAdminManager:
    """Chuyển thể nguyên bản 100% từ Li2/S.smali, Lh2/X0.smali, Lh2/y.smali và LD2/q.smali"""

    GRAPHQL_URL = "https://graph.facebook.com/graphql"

    DOC_ID_ACTION = "30749539927629244093798192451"        # Dùng cho STEP 1, STEP 2, STEP 4
    DOC_ID_FETCH_INVITE = "221080835214205752894689842827"  # Dùng cho STEP 3 (Lấy invitation_id)

    BLOKS_VERSION = "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
    STYLES_ID = "588d028b36bed0e1889e09b60e0f9aea"
    USER_AGENT = (
        "[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;"
        "FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;"
        "FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;"
        "FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]"
    )

    def __init__(self, sender_proxy: Optional[str] = None, receiver_proxy: Optional[str] = None):
        self.sender_proxies = parse_proxy(sender_proxy)
        self.receiver_proxies = parse_proxy(receiver_proxy) or self.sender_proxies

    @classmethod
    def build_headers(cls, access_token: str) -> dict:
        analytics_tags = {
            "network_tags": {
                "product": "350685531728",
                "request_category": "graphql",
                "purpose": "none",
                "retry_attempt": "0",
            },
            "application_tags": "graphservice",
        }
        return {
            "user-agent": cls.USER_AGENT,
            "content-type": "application/x-www-form-urlencoded",
            "x-fb-request-analytics-tags": json.dumps(analytics_tags, separators=(",", ":")),
            "x-fb-friendly-name": "NativeTemplateAsyncQuery",
            "x-graphql-client-library": "graphservice",
            "x-fb-connection-type": "WIFI",
            "authorization": f"OAuth {access_token}",
            "x-fb-device-group": "4789",
        }

    @classmethod
    def build_nt_context(cls) -> dict:
        return {
            "using_white_navbar": True,
            "styles_id": cls.STYLES_ID,
            "pixel_ratio": 2,
            "is_push_on": True,
            "debug_tooling_metadata_token": None,
            "is_flipper_enabled": False,
            "theme_params": [{"value": [], "design_system_name": "FDS"}],
            "bloks_version": cls.BLOKS_VERSION,
        }

    @staticmethod
    def build_permissions() -> dict:
        return {
            "ads": True,
            "insights": True,
            "messages": True,
            "content": True,
            "moderate": True,
            "show_entry_point_saving_spinner": "NONE",
        }

    @classmethod
    def build_variables(cls, params_obj: dict, nt_context: Optional[dict] = None) -> dict:
        if nt_context is None:
            nt_context = cls.build_nt_context()
        return {
            "params": params_obj,
            "nt_context": nt_context,
            "scale": "2",
            "use_native_entrypoint_for_stars_on_reels": True,
            "profile_image_size": 188,
            "include_image_ranges": True,
        }

    @staticmethod
    def build_form_data(client_doc_id: str, variables_obj: dict) -> dict:
        return {
            "method": "post",
            "pretty": "false",
            "format": "json",
            "server_timestamps": "true",
            "locale": "vi_VN",
            "fb_api_req_friendly_name": "NativeTemplateAsyncQuery",
            "fb_api_caller_class": "graphservice",
            "client_doc_id": client_doc_id,
            "fb_api_client_context": json.dumps({"is_background": False}, separators=(",", ":")),
            "variables": json.dumps(variables_obj, separators=(",", ":")),
        }

    @staticmethod
    def extract_invitation_id(resp_json: dict) -> Optional[str]:
        try:
            attrs = resp_json["data"]["native_template_screen"]["nt_bundle"]["nt_bundle_attributes"]
            for attr in attrs:
                if str(attr.get("name")) == "1":
                    params_str = attr["intent_value"]["query"]["params"]
                    if "invitation_id" in params_str:
                        parts = params_str.split("invitation_id")
                        if len(parts) > 1:
                            cleaned = re.sub(r"[^0-9]", " ", parts[1]).strip()
                            tokens = re.split(r"\s+", cleaned)
                            if tokens and tokens[0]:
                                return tokens[0]
        except Exception:
            pass
        try:
            raw_str = json.dumps(resp_json)
            m = re.search(r"invitation_id[^\d]+(\d{8,25})", raw_str)
            if m:
                return m.group(1)
        except Exception:
            pass
        return None

    def post_graphql(self, step_name: str, form_data: dict, token: str, is_receiver: bool) -> dict:
        headers = self.build_headers(token)
        proxies = self.receiver_proxies if is_receiver else self.sender_proxies

        encoded_parts = [f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in form_data.items()]
        body_str = "&".join(encoded_parts)

        s = requests.Session()
        s.verify = False
        s.trust_env = False
        if proxies:
            s.proxies.update(proxies)

        resp = s.post(
            self.GRAPHQL_URL,
            headers=headers,
            data=body_str,
            timeout=25,
        )
        if not resp.ok:
            raise RuntimeError(f"[{step_name}] HTTP {resp.status_code}: {resp.text[:120]}")

        data = resp.json()
        data["_http_status"] = resp.status_code
        return data

    def execute_step1(self, page_id: str, target_uid: str, password: str, sender_token: str) -> dict:
        """STEP 1 (Lh2/X0 :pswitch_5): Xác thực mật khẩu tài khoản cầm Page"""
        payload_path = (
            "/nt/profile/admin_management/permissions_reauth?admin_id="
            f"{target_uid}"
            "&admin_rows_container_id=%5B%228bxxoh%3A2%22%2Cnull%5D"
            "&admin_type=full_access"
            "&entry_point_screen_id=%5B%227o2xil%3A5%22%2Cnull%5D"
            f"&profile_id={page_id}"
            "&state_ids%5Bauthenticated%5D=8csr9g%3A0"
            "&state_ids%5Bauthentication_attempted%5D=8csr9g%3A1"
            "&state_ids%5Bshow_entry_point_saving_spinner%5D=8bxxoh%3A0"
            "&state_ids%5Bshow_saving_spinner%5D=8csr9g%3A3"
            "&state_ids%5Bads%5D=8clnk7%3A2"
            "&state_ids%5Bcontent%5D=8clnk7%3A3"
            "&state_ids%5Binsights%5D=8clnk7%3A4"
            "&state_ids%5Bmessages%5D=8clnk7%3A5"
            "&state_ids%5Bmoderate%5D=8clnk7%3A6"
        )
        nt_context = self.build_nt_context()
        sensitive_array = [["password", password]]
        client_data = {
            "sensitive_string_value": json.dumps(sensitive_array, separators=(",", ":"))
        }
        params_obj = {
            "nt_context": nt_context,
            "payload": payload_path,
            "client_data": client_data,
        }
        variables = self.build_variables(params_obj, nt_context)
        form_data = self.build_form_data(self.DOC_ID_ACTION, variables)
        return self.post_graphql("STEP1", form_data, sender_token, is_receiver=False)

    def execute_step2(self, page_id: str, target_uid: str, sender_token: str) -> dict:
        """STEP 2 (Lh2/y :pswitch_7): Kích hoạt cấp quyền full_access & bắn thông báo lời mời"""
        payload_path = (
            "/nt/profile/admin_management/permissions/update?"
            "admin_rows_container_id=%5B%228bxxoh%3A2%22%2Cnull%5D"
            "&entry_point_screen_id=%5B%227o2xil%3A5%22%2Cnull%5D"
            f"&admin_type=full_access&profile_id={page_id}"
            f"&target_admin_id={target_uid}"
            "&secured_sensitive_actions%5B0%5D=page_admin_access_addition"
            "&state_ids%5Bshow_entry_point_saving_spinner%5D=8bxxoh%3A0"
            "&state_ids%5Bads%5D=8clnk7%3A2"
            "&state_ids%5Bcontent%5D=8clnk7%3A3"
            "&state_ids%5Binsights%5D=8clnk7%3A4"
            "&state_ids%5Bmessages%5D=8clnk7%3A5"
            "&state_ids%5Bmoderate%5D=8clnk7%3A6"
        )
        nt_context = self.build_nt_context()
        permissions = self.build_permissions()
        params_obj = {
            "payload": payload_path,
            "state_data": json.dumps(permissions, separators=(",", ":")),
            "nt_context": nt_context,
        }
        variables = self.build_variables(params_obj, nt_context)
        form_data = self.build_form_data(self.DOC_ID_ACTION, variables)
        form_data["fb_api_analytics_tags"] = '["GraphServices"]'
        form_data["client_trace_id"] = str(uuid.uuid4())
        return self.post_graphql("STEP2", form_data, sender_token, is_receiver=False)

    def execute_step3(self, page_id: str, target_uid: str, receiver_token: str) -> dict:
        """STEP 3 (LD2/q.d()): Truy vấn màn hình lời mời bên Acc nhận để lấy invitation_id"""
        nt_context = self.build_nt_context()
        inner_params = {
            "screen_id": '["sz9fnp:17",null]',
            "profile_id": str(page_id),
            "invitee_id": str(target_uid),
        }
        outer_params = {
            "nt_context": nt_context,
            "path": "/nt/profile/admin_management/invitation",
            "params": json.dumps(inner_params, separators=(",", ":")),
            "extra_client_data": {},
        }
        variables = {
            "params": outer_params,
            "scale": "2",
            "use_native_entrypoint_for_stars_on_reels": True,
            "nt_context": nt_context,
        }
        form_data = self.build_form_data(self.DOC_ID_FETCH_INVITE, variables)
        form_data["purpose"] = "fetch"
        form_data["fb_api_req_friendly_name"] = "NativeTemplateScreenQuery"
        form_data["fb_api_analytics_tags"] = '["surfaces.fb.GraphServiceEmitter","GraphServices"]'
        form_data["client_trace_id"] = str(uuid.uuid4())
        return self.post_graphql("STEP3", form_data, receiver_token, is_receiver=True)

    def execute_step4(self, invitation_id: str, receiver_token: str) -> dict:
        """STEP 4 (LD2/q.a()): Gửi lệnh chấp nhận lời mời Admin bằng Token Acc nhận"""
        payload_path = (
            "/nt/profile/admin_management/invitation_response?"
            f"accept_invitation=1&invitation_id={invitation_id}&admin_type=full_access"
        )
        nt_context = self.build_nt_context()
        params_obj = {
            "payload": payload_path,
            "nt_context": nt_context,
        }
        variables = self.build_variables(params_obj, nt_context)
        form_data = self.build_form_data(self.DOC_ID_ACTION, variables)
        form_data["fb_api_analytics_tags"] = '["GraphServices"]'
        form_data["client_trace_id"] = str(uuid.uuid4())
        return self.post_graphql("STEP4", form_data, receiver_token, is_receiver=True)

    def transfer_page(
        self,
        page_id: str,
        sender_token: str,
        password: str,
        target_uid: str,
        receiver_token: Optional[str] = None,
        auto_accept: bool = False,
        additional_profile_id: str = "",
        page_token: str = "",
        step_callback=None
    ) -> dict:
        result = {
            "success": False,
            "page_id": page_id,
            "target_uid": target_uid,
            "invitation_id": None,
            "status": "FAILED",
            "message": "",
        }

        candidate_profile_ids = []
        for pid in [page_id, additional_profile_id]:
            if pid and str(pid) not in candidate_profile_ids:
                candidate_profile_ids.append(str(pid))

        candidate_tokens = []
        for tk in [sender_token, page_token]:
            if tk and str(tk) not in candidate_tokens:
                candidate_tokens.append(str(tk))

        step12_ok = False
        last_err = ""

        for pid in candidate_profile_ids:
            if step12_ok:
                break
            for s_tk in candidate_tokens:
                try:
                    if step_callback:
                        step_callback(f"MTool Step 1: Đang xác thực mật khẩu cho Page {pid}...")
                    resp1 = self.execute_step1(pid, target_uid, password, s_tk)
                    if "errors" in resp1:
                        last_err = f"Step 1 lỗi: {resp1['errors'][0].get('message', resp1['errors'])}"
                        continue

                    if step_callback:
                        step_callback(f"MTool Step 2: Đang bắn thông báo mời Full Admin sang UID {target_uid}...")
                    resp2 = self.execute_step2(pid, target_uid, s_tk)
                    if "errors" in resp2:
                        last_err = f"Step 2 lỗi: {resp2['errors'][0].get('message', resp2['errors'])}"
                        continue

                    step12_ok = True
                    break
                except Exception as e:
                    last_err = str(e)

        if not step12_ok:
            result["message"] = last_err or "Không thể thực hiện Step 1 & Step 2 MTool"
            return result

        if not auto_accept or not receiver_token:
            result["success"] = True
            result["status"] = "INVITED_ONLY"
            result["message"] = f"Đã bắn thông báo mời Admin (MTool Step 2) sang UID {target_uid}"
            return result

        for remaining in range(5, 0, -1):
            if step_callback:
                step_callback(f"MTool: Đã bắn lời mời! Chờ {remaining}s để lấy invitation_id...")
            time.sleep(1)

        if step_callback:
            step_callback("MTool Step 3: Đang dùng Token Mẹ lấy invitation_id...")

        invitation_id = None
        for pid in candidate_profile_ids:
            try:
                resp3 = self.execute_step3(pid, target_uid, receiver_token)
                invitation_id = self.extract_invitation_id(resp3)
                if invitation_id:
                    break
            except Exception as e:
                last_err = str(e)

        if not invitation_id:
            result["success"] = True
            result["status"] = "INVITED_ONLY"
            result["message"] = f"Đã bắn lời mời sang UID {target_uid} (Chưa lấy được invitation_id để Auto Accept)"
            return result

        result["invitation_id"] = invitation_id

        if step_callback:
            step_callback(f"MTool Step 4: Đang Auto Accept lời mời ({invitation_id})...")

        try:
            resp4 = self.execute_step4(invitation_id, receiver_token)
            if "errors" not in resp4 and resp4.get("_http_status") == 200:
                result["success"] = True
                result["status"] = "SUCCESS"
                result["message"] = f"Đã chuyển & Auto Accept Full Admin thành công sang UID {target_uid}!"
            else:
                result["success"] = True
                result["status"] = "INVITED_ONLY"
                result["message"] = f"Đã mời (ID: {invitation_id}), lỗi Auto Accept: {resp4.get('errors', '')}"
        except Exception as e:
            result["success"] = True
            result["status"] = "INVITED_ONLY"
            result["message"] = f"Đã mời (ID: {invitation_id}), ngoại lệ Step 4: {e}"

        return result


# ==============================================================================
# 8. CORE REG PAGE PRO5 -> GET TOKEN PAGE -> CHECK LIVE -> BẮN ADMIN MTOOL
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

    def check_account_live(self, retries: int = 3) -> Dict[str, Any]:
        """Kiểm tra Tài khoản (Nick Reg) còn sống (LIVE), phân biệt rõ lỗi Mạng/Proxy với Token DIE."""
        last_err = ""
        for attempt in range(1, retries + 1):
            try:
                r = self.session.get(
                    f"https://graph.facebook.com/me?fields=id,name&access_token={self.token}",
                    headers={"User-Agent": self.user_agent},
                    timeout=20
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
                    or "session" in err_msg.lower()
                    or "error" in r
                )
                return {"success": False, "is_token_die": is_die, "is_network_error": False, "message": err_msg}
            except requests.exceptions.RequestException as e:
                last_err = str(e)
                if attempt < retries:
                    time.sleep(2)
            except Exception as e:
                last_err = str(e)
                break

        return {
            "success": False,
            "is_token_die": False,
            "is_network_error": True,
            "message": f"Lỗi kết nối mạng/Proxy: {last_err[:65]}"
        }

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
        """Kiểm tra trực tiếp Page vừa tạo và Token của Page đó còn LIVE không."""
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
        """Thực hiện tạo 1 Page Pro5 và lấy luôn Token EAAAAU của Page đó."""
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
        for _ in range(1, 4):
            time.sleep(3)
            scan_res = self.get_all_pages_with_tokens()
            if scan_res.get("is_token_die"):
                return {"success": False, "is_token_die": True, "message": "Token DIE khi đang lấy Token Page"}

            pages_list = scan_res.get("pages", [])
            for p in pages_list:
                pid = str(p.get("id", ""))
                if pid and pid not in known_page_ids:
                    new_page_obj = p
                    break

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
        page_token: str,
        password: str,
        holder_uid: str,
        holder_token: Optional[str] = None,
        holder_proxy: Optional[str] = None,
        additional_profile_id: str = "",
        step_callback=None
    ) -> Dict[str, Any]:
        """
        Kết hợp chuẩn MTool Max 4 Bước (Ưu tiên số 1) + Dự phòng GraphQL/Graph API nếu thiếu mật khẩu.
        """
        holder_uid = str(holder_uid).strip()
        if not holder_uid and holder_token:
            try:
                r_me = requests.get(
                    f"https://graph.facebook.com/me?fields=id&access_token={holder_token}",
                    proxies=parse_proxy(holder_proxy) or self.proxies,
                    timeout=15,
                    verify=False
                ).json()
                holder_uid = str(r_me.get("id", ""))
            except Exception:
                pass

        if not holder_uid:
            return {"success": False, "message": "Thiếu UID Nick Mẹ"}

        # 1. Nếu có Mật khẩu Nick Reg -> Chạy chuẩn 4 Bước MTool Max Smali
        if password:
            manager = FacebookAdminManager(sender_proxy=self.proxy, receiver_proxy=holder_proxy or self.proxy)
            auto_acc = bool(holder_token)
            mtool_res = manager.transfer_page(
                page_id=page_id,
                sender_token=self.token,
                password=password,
                target_uid=holder_uid,
                receiver_token=holder_token,
                auto_accept=auto_acc,
                additional_profile_id=additional_profile_id,
                page_token=page_token,
                step_callback=step_callback
            )
            if mtool_res.get("success"):
                return {
                    "success": True,
                    "status": mtool_res.get("status"),
                    "invitation_id": mtool_res.get("invitation_id"),
                    "message": mtool_res.get("message")
                }
            mtool_err = mtool_res.get("message", "Lỗi MTool")
        else:
            mtool_err = "Thiếu mật khẩu Nick Reg cho Step 1 MTool"

        # 2. Dự phòng (Fallback) qua GraphQL nếu người dùng không nhập Password
        if step_callback:
            step_callback(f"Đang thử phương thức dự phòng cho UID {holder_uid} ({mtool_err[:35]})...")

        invited_ok = False
        last_err = mtool_err
        actor_pro5 = str(additional_profile_id or page_id)

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
                except Exception:
                    pass

        if invited_ok:
            return {
                "success": True,
                "status": "INVITED_ONLY",
                "invitation_id": None,
                "message": f"Đã bắn lời mời Admin (GraphQL) sang UID {holder_uid}"
            }
        return {
            "success": False,
            "status": "FAILED",
            "invitation_id": None,
            "message": f"Lỗi bắn sang UID {holder_uid}: {last_err[:55]}"
        }


# ==============================================================================
# 9. BẢNG THEO DÕI TRỰC TIẾP + KHUNG NHẬT KÝ QUÁ TRÌNH CHI TIẾT
# ==============================================================================

class AccountTask:
    def __init__(
        self,
        acc_id: int,
        item: Dict[str, Any],
        target_pages: int,
        ua_mode: str,
        default_pwd: str = "",
        assigned_proxy: Optional[str] = None,
        holder_target: Optional[Dict[str, Optional[str]]] = None
    ):
        self.acc_id = acc_id
        self.token = item.get("token", "")
        self.password = item.get("pwd") or default_pwd
        self.proxy = item.get("proxy") or assigned_proxy
        self.holder_uid = (holder_target or {}).get("uid") or ""
        self.holder_token = (holder_target or {}).get("token") or None
        self.holder_proxy = (holder_target or {}).get("proxy") or None
        self.target_pages = target_pages
        self.pages_created = 0
        self.ua_mode = ua_mode
        self.fixed_ua = generate_random_katana_ua(seed=self.token) if ua_mode == "fixed" else None
        self.creator = FbPageCreator(token=self.token, proxy=self.proxy, user_agent=self.fixed_ua, ua_mode=ua_mode)
        self.pre_uid = item.get("uid") or ""
        self.mother_uid = self.pre_uid
        self.mother_name = ""
        self.status = "ready"  # ready, running, waiting_check, done, no_page, limit, die, net_err
        self.current_action = "Chờ đến lượt..."
        self.last_result = ""


def render_dashboard(accounts: List[AccountTask], stats: Dict[str, int]):
    lines = []
    w = 116
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(
        f"{Colors.BOLD}{Colors.YELLOW}"
        f"     BẢNG TIẾN TRÌNH: TẠO PAGE -> GET TOKEN PAGE -> CHECK LIVE ACC & PAGE -> BẮN ADMIN (MTOOL)     "
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
        prog_raw = f"{acc.pages_created}/{acc.target_pages}"
        prog_padded = f"{prog_raw:^7}"

        if acc.status == "done":
            status_display = f"{Colors.GREEN}✅ {acc.last_result}{Colors.RESET}"
        elif acc.status == "no_page":
            status_display = f"{Colors.MAGENTA}⚠️ {acc.current_action}{Colors.RESET}"
        elif acc.status == "net_err":
            status_display = f"{Colors.YELLOW}🌐 {acc.current_action}{Colors.RESET}"
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
        f"Bắn/Accept MTool: {Colors.CYAN}{stats.get('total_invited', 0)}{Colors.RESET}) | "
        f"Xịt/Die Page: {Colors.MAGENTA}{stats.get('total_no_page', 0)}{Colors.RESET} | "
        f"Limit: {Colors.YELLOW}{stats.get('total_limited', 0)}{Colors.RESET} | "
        f"Lỗi Mạng: {Colors.YELLOW}{stats.get('total_net_err', 0)}{Colors.RESET} | "
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
# 10. LUỒNG XỬ LÝ CHÍNH CHO TỪNG TÀI KHOẢN
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
    acc.current_action = f"[L{thread_id}] Bước 1: Đang kiểm tra Tài khoản & quét Page cũ..."
    add_process_log(acc.acc_id, acc.pre_uid, "Bước 1: Đang kiểm tra Token Tài khoản ban đầu...")

    # --- BƯỚC 1: KIỂM TRA TÀI KHOẢN & LƯU DANH SÁCH PAGE CŨ ---
    acc_info = acc.creator.check_account_live(retries=3)
    if not acc_info.get("success"):
        err_msg = acc_info.get("message", "Lỗi kiểm tra tài khoản")
        if acc_info.get("is_network_error"):
            acc.status = "net_err"
            acc.mother_uid = acc.pre_uid or "Unknown"
            acc.mother_name = "Lỗi Mạng/Proxy"
            acc.current_action = f"{err_msg[:55]} (Không ghi vào acc_die.txt)"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}🌐 {err_msg}{Colors.RESET}")
            with FILE_LOCK:
                stats["total_net_err"] += 1
            return

        acc.status = "die"
        acc.mother_uid = acc.pre_uid or "Unknown"
        acc.mother_name = "Nick DIE / Check"
        acc.current_action = f"Tài khoản DIE từ đầu ({err_msg[:35]}) -> Lưu acc_die.txt"
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

    recheck_acc = acc.creator.check_account_live(retries=2)
    if not recheck_acc.get("success") and recheck_acc.get("is_token_die"):
        acc.status = "die"
        acc.current_action = f"Sau {wait_seconds}s: Tài khoản bị DIE / Checkpoint!"
        add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Sau {wait_seconds}s: Tài khoản bị DIE / Checkpoint!{Colors.RESET}")
        with FILE_LOCK:
            stats["total_token_die"] += 1
            with open("acc_die.txt", "a", encoding="utf-8") as f:
                f.write(f"{acc.mother_uid}|{acc.token}|DIE_SAU_{wait_seconds}S\n")
        return

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

    # --- BƯỚC 5: CHUYỂN PAGE & AUTO ACCEPT SANG NICK MẸ BẰNG MTOOL MAX ---
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

        if acc.holder_uid or acc.holder_token:
            def mtool_cb(msg_step: str):
                acc.current_action = f"[L{thread_id}] {msg_step}"
                add_process_log(acc.acc_id, acc.mother_uid, f"🚀 {msg_step}")

            tr_res = acc.creator.invite_holder_mtool(
                page_id=p_id,
                page_token=p_token,
                password=acc.password,
                holder_uid=acc.holder_uid,
                holder_token=acc.holder_token,
                holder_proxy=acc.holder_proxy,
                additional_profile_id=add_prof_id,
                step_callback=mtool_cb
            )
            p["transfer_ok"] = tr_res.get("success", False)
            p["transfer_status"] = tr_res.get("status", "FAILED")
            p["invitation_id"] = tr_res.get("invitation_id")
            transfer_note = tr_res.get("message", "")
            if p["transfer_ok"]:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}✅ {transfer_note}{Colors.RESET}")
            else:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}⚠️ {transfer_note}{Colors.RESET}")
        else:
            p["transfer_ok"] = False
            p["transfer_status"] = "NO_TARGET"

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
                f_page.write(f"{p_id}|{p_name}|{p_token}|{acc.mother_uid}|{acc.password}|{now_str}\n")

            with open("acc_cam_page.txt", "a", encoding="utf-8") as f_holder:
                if acc.holder_uid or acc.holder_token:
                    st_code = p.get("transfer_status", "")
                    inv_id = p.get("invitation_id") or ""
                    tr_tag = f"{st_code}:{acc.holder_uid}" + (f"(InviteID:{inv_id})" if inv_id else "")
                    f_holder.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|{p_id}|{p_name}|{p_token}|{tr_tag}|{now_str}\n")
                else:
                    f_holder.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|{p_id}|{p_name}|{p_token}|PAGE_LIVE|{now_str}\n")

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
# 11. MENU [1]: REG PAGE -> GET TOKEN PAGE -> CHECK LIVE -> CHUYỂN PAGE MTOOL
# ==============================================================================

def run_reg_page_menu():
    print_banner()
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== CẤU HÌNH: TẠO PAGE -> GET TOKEN PAGE -> CHECK LIVE -> CHUYỂN PAGE MTOOL ==={Colors.RESET}\n")

    # 1. Nạp Token
    safe_print(f"{Colors.CYAN}--- [1/7] NẠP DANH SÁCH ACC / TOKEN EAAAAU CẦN REG ---{Colors.RESET}")
    safe_print("Hỗ trợ định dạng: UID|PASS|TOKEN hoặc UID|PASS|2FA|COOKIE|TOKEN|PROXY hoặc UID|TOKEN")
    safe_print("[1] Dán trực tiếp vào màn hình (tự động lọc EAAAAU & Password)")
    safe_print("[2] Đọc từ file tokens.txt (hoặc tokens_eaaau.txt)")
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

    has_pwd_count = sum(1 for it in parsed_items if it.get("pwd"))
    safe_print(
        f"{Colors.GREEN}{Colors.BOLD}Đã nhận diện: {len(parsed_items)} Acc (Token EAAAAU) hợp lệ "
        f"(Có sẵn mật khẩu: {has_pwd_count}/{len(parsed_items)} Acc)!{Colors.RESET}\n"
    )

    # 2. Nhập UID Nick Mẹ (và Token Nick Mẹ nếu muốn Auto Accept)
    safe_print(f"{Colors.CYAN}--- [2/7] CẤU HÌNH NICK MẸ NHẬN PAGE (CHUẨN MTOOL MAX 4 BƯỚC) ---{Colors.RESET}")
    safe_print("- Cách 1 (Chỉ bắn lời mời Step 1+2, tự bấm chấp nhận): Nhập UID_ME (VD: 100012345678)")
    safe_print("- Cách 2 (Bắn lời mời + Auto Accept Full 4 bước): Nhập UID_ME|TOKEN_ME")
    safe_print("- Nếu để trống và nhấn Enter -> Chỉ tạo Page, Get Token Page và lưu file.")
    h_raw = input("Nhập thông tin Nick Mẹ: ").strip()

    holder_targets = parse_holder_target(h_raw)
    default_pwd = ""

    if holder_targets:
        has_auto_acc = any(t.get("token") for t in holder_targets)
        mode_str = "FULL 4 BƯỚC (Bắn lời mời + Auto Accept)" if has_auto_acc else "2 BƯỚC ĐẦU (Xác thực Pass + Bắn thông báo mời)"
        safe_print(f"{Colors.GREEN}✔ Đã bật chế độ chuyển Page MTool Max: {mode_str}{Colors.RESET}")

        if has_pwd_count < len(parsed_items):
            safe_print(f"{Colors.YELLOW}Lưu ý: Step 1 của MTool cần mật khẩu của Nick Reg để xác thực cấp quyền Admin.{Colors.RESET}")
            default_pwd = input("Nhập Mật khẩu mặc định cho các Nick Reg chưa kèm pass (Enter nếu bỏ qua): ").strip()
        safe_print("")
    else:
        safe_print(f"{Colors.YELLOW}Không nhập Nick Mẹ -> Chỉ tạo Page, Get Token Page và lưu vào acc_cam_page.txt.{Colors.RESET}\n")

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
        safe_print(f"{Colors.GREEN}Phát hiện các token đã có Proxy hợp lệ gắn kèm riêng.{Colors.RESET}\n")
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
        "total_net_err": 0,
        "total_token_die": 0
    }
    actual_threads = min(num_threads, len(parsed_items))
    worker_threads = []
    stop_dashboard = threading.Event()

    account_tasks = []
    task_queue = Queue()

    for idx, it in enumerate(parsed_items):
        assigned_px = global_proxies[idx % len(global_proxies)] if global_proxies and not it.get("proxy") else None
        assigned_target = holder_targets[idx % len(holder_targets)] if holder_targets else None
        task_obj = AccountTask(
            acc_id=idx + 1,
            item=it,
            target_pages=pages_per_nick,
            ua_mode=ua_mode,
            default_pwd=default_pwd,
            assigned_proxy=assigned_px,
            holder_target=assigned_target
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

    safe_print("\n" + "=" * 94)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT TIẾN TRÌNH!{Colors.RESET}")
    safe_print(f"- Số Acc sống & có Page sống sau {verify_delay}s: {Colors.GREEN}{stats['total_holder_acc']} Acc ({stats['total_pages']} Page){Colors.RESET}")
    safe_print(f"- Số Page đã gửi lời mời / Auto Accept MTool sang Nick Mẹ: {Colors.CYAN}{stats['total_invited']} Page{Colors.RESET}")
    safe_print(f"- Số Acc không lên Page hoặc Page bị hủy đăng: {Colors.MAGENTA}{stats['total_no_page']}{Colors.RESET}")
    safe_print(f"- Số Acc gặp Limit: {Colors.YELLOW}{stats['total_limited']}{Colors.RESET}")
    safe_print(f"- Số Acc gặp lỗi Mạng/Proxy (đã bảo toàn, không ghi vào acc_die): {Colors.YELLOW}{stats['total_net_err']}{Colors.RESET}")
    safe_print(f"- Số Acc bị Token DIE / Checkpoint: {Colors.RED}{stats['total_token_die']}{Colors.RESET}")
    safe_print(f"- File lưu Acc + Pass + Page + Token Page + Trạng thái: {Colors.CYAN}acc_cam_page.txt{Colors.RESET}")
    safe_print(f"- File lưu danh sách Page riêng: {Colors.CYAN}created_pages.txt{Colors.RESET}")
    if holder_targets:
        safe_print(f"- Link duyệt lời mời Admin trên Nick Mẹ (nếu không bật Auto Accept): {Colors.YELLOW}https://www.facebook.com/pages/?category=invites{Colors.RESET}")
    safe_print("=" * 94 + "\n")
    input("Nhấn Enter để quay lại menu chính...")


# ==============================================================================
# 12. MENU [2]: CHUYỂN PAGE RỜI & AUTO ACCEPT 4 BƯỚC (MTOOL MAX PORT)
# ==============================================================================

def run_standalone_mtool_transfer_menu():
    print_banner()
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== CHUYỂN PAGE & AUTO ACCEPT FULL 4 BƯỚC (MTOOL MAX PORT) ==={Colors.RESET}\n")
    safe_print("[1] Nhập trực tiếp từng thông tin trên màn hình")
    safe_print("[2] Chạy hàng loạt từ file 'input_chuyen_page.txt' (Định dạng: PAGE_ID|TOKEN_CAM_PAGE|MAT_KHAU|UID_NHAN|TOKEN_NHAN|PROXY_GUI|PROXY_NHAN)")
    choice = input("Chọn chế độ (1 hoặc 2, mặc định 1): ").strip() or "1"

    tasks = []
    if choice == "2":
        infile = "input_chuyen_page.txt"
        if not os.path.exists(infile):
            with open(infile, "w", encoding="utf-8") as f:
                f.write("# PAGE_ID|TOKEN_CAM_PAGE|MAT_KHAU|UID_NHAN|TOKEN_NHAN(tùy chọn)|PROXY_GUI(tùy chọn)|PROXY_NHAN(tùy chọn)\n")
            safe_print(f"{Colors.YELLOW}[!] Đã tạo file mẫu '{infile}'. Hãy dán dữ liệu vào rồi chạy lại.{Colors.RESET}")
            input("\nNhấn Enter để quay lại...")
            return
        with open(infile, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        tasks.append({
                            "page_id": parts[0],
                            "sender_token": parts[1],
                            "password": parts[2],
                            "target_uid": parts[3],
                            "receiver_token": parts[4] if len(parts) > 4 and parts[4] else None,
                            "sender_proxy": parts[5] if len(parts) > 5 and parts[5] else None,
                            "receiver_proxy": parts[6] if len(parts) > 6 and parts[6] else None,
                        })
                    else:
                        safe_print(f"{Colors.RED}[!] Bỏ qua dòng thiếu thông tin: {line}{Colors.RESET}")
    else:
        page_id = input("- ID Page (profile_id): ").strip()
        sender_token = input("- Token Acc cầm Page (EAAAAU...): ").strip()
        password = input("- Mật khẩu Acc cầm Page: ").strip()
        target_uid = input("- UID Acc nhận Page (Nick Mẹ): ").strip()
        receiver_token = input("- Token Acc nhận Page (Enter nếu chỉ bắn lời mời, không Auto Accept): ").strip()
        sender_proxy = input("- Proxy Acc cầm Page (Enter nếu không dùng): ").strip()
        receiver_proxy = input("- Proxy Acc nhận Page (Enter nếu không dùng): ").strip()

        if page_id and sender_token and target_uid:
            tasks.append({
                "page_id": page_id,
                "sender_token": sender_token,
                "password": password,
                "target_uid": target_uid,
                "receiver_token": receiver_token or None,
                "sender_proxy": sender_proxy or None,
                "receiver_proxy": receiver_proxy or None,
            })

    if not tasks:
        safe_print(f"{Colors.RED}[!] Không có dữ liệu hợp lệ để chạy.{Colors.RESET}")
        input("\nNhấn Enter để quay lại...")
        return

    success_out = "output_success.txt"
    failed_out = "output_failed.txt"

    for idx, item in enumerate(tasks, 1):
        safe_print(f"\n{Colors.CYAN}--- [{idx}/{len(tasks)}] Chuyển Page {item['page_id']} -> UID {item['target_uid']} ---{Colors.RESET}")
        auto_accept = bool(item["receiver_token"])
        manager = FacebookAdminManager(
            sender_proxy=item["sender_proxy"],
            receiver_proxy=item["receiver_proxy"],
        )

        def print_step(msg: str):
            safe_print(f"  {Colors.YELLOW}[*] {msg}{Colors.RESET}")

        res = manager.transfer_page(
            page_id=item["page_id"],
            sender_token=item["sender_token"],
            password=item["password"],
            target_uid=item["target_uid"],
            receiver_token=item["receiver_token"],
            auto_accept=auto_accept,
            step_callback=print_step
        )

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = (
            f"{now} | Page: {res['page_id']} | UID Nhận: {res['target_uid']} | "
            f"InviteID: {res['invitation_id']} | Status: {res['status']} | {res['message']}"
        )
        color = Colors.GREEN if res["status"] in ("SUCCESS", "INVITED_ONLY") else Colors.RED
        safe_print(f"{color}=> {log_line}{Colors.RESET}")

        out_path = success_out if res["status"] in ("SUCCESS", "INVITED_ONLY") else failed_out
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

    safe_print("\n" + "=" * 94)
    safe_print(f"{Colors.GREEN}Hoàn tất! Kết quả thành công lưu tại: {os.path.abspath(success_out)}{Colors.RESET}")
    safe_print("=" * 94)
    input("\nNhấn Enter để quay lại menu chính...")


# ==============================================================================
# 13. MENU [3]: GET TOKEN EAAAAU TỪ ACC (LƯU KÈM PASSWORD ĐỂ DÙNG CHO MTOOL)
# ==============================================================================

def worker_get_token(thread_id: int, queue: Queue, stats: Dict[str, int]):
    while True:
        try:
            acc = queue.get(timeout=2.0)
        except Empty:
            break

        uid = acc.get("uid", "")
        pwd = acc.get("pwd", "")
        proxy = acc.get("proxy", "")
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
                    if proxy:
                        f.write(f"{uid}|{pwd}|{token}|{proxy}\n")
                    else:
                        f.write(f"{uid}|{pwd}|{token}\n")
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
        lines = input_multiline("Dán tài khoản (UID|Pass|2FA hoặc UID|Pass|2FA|Cookie|Proxy):")
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

    safe_print("\n" + "=" * 94)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT LẤY TOKEN EAAAAU!{Colors.RESET}")
    safe_print(f"- Lấy thành công: {Colors.GREEN}{stats['success']}{Colors.RESET}")
    safe_print(f"- Thất bại: {Colors.RED}{stats['fail']}{Colors.RESET}")
    safe_print(f"- Đã lưu file (kèm Pass cho MTool): {Colors.CYAN}tokens_eaaau.txt{Colors.RESET}")
    safe_print("=" * 94 + "\n")
    input("Nhấn Enter để quay lại menu chính...")


def main():
    while True:
        print_banner()
        safe_print(f"{Colors.BOLD}VUI LÒNG CHỌN CHỨC NĂNG:{Colors.RESET}")
        safe_print(f"{Colors.GREEN}[1] REG PAGE PRO5 -> GET TOKEN PAGE -> CHECK LIVE -> BẮN ADMIN & AUTO ACCEPT (MTOOL){Colors.RESET}")
        safe_print(f"{Colors.CYAN}[2] CHUYỂN PAGE PRO5 RỜI & AUTO ACCEPT FULL 4 BƯỚC (MTOOL MAX PORT){Colors.RESET}")
        safe_print(f"{Colors.YELLOW}[3] GET TOKEN EAAAAU TỪ TÀI KHOẢN (UID|PASS|2FA -> LƯU KÈM PASS){Colors.RESET}")
        safe_print(f"{Colors.RED}[0] THOÁT TOOL{Colors.RESET}\n")

        choice = input("Nhập lựa chọn của bạn (0 - 3): ").strip()

        if choice == "1":
            run_reg_page_menu()
        elif choice == "2":
            run_standalone_mtool_transfer_menu()
        elif choice == "3":
            run_get_token_menu()
        elif choice == "0":
            safe_print(f"\n{Colors.CYAN}Cảm ơn bạn đã sử dụng Tool. Tạm biệt!{Colors.RESET}\n")
            sys.exit(0)
        else:
            safe_print(f"{Colors.RED}Lựa chọn không hợp lệ.{Colors.RESET}")
            time.sleep(1)


if __name__ == "__main__":
    main()
