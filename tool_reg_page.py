#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
TOOL REG PAGE PRO5 VIP (CORE V5) + CHUYỂN PAGE SIÊU MẠNH (FIX CHUẨN PROFILESWITCHER)
- Đầu vào đa năng: Nhận mọi biến thể (UID|Pass|Cookie|Token, UID|Pass|Token,
  UID|Pass|Cookie, UID|Pass|2FA, Token|Proxy...).
- Tự động Login Bloks CAA v5 lấy Token EAAAAU nếu dòng acc chưa có sẵn Token.
- Reg Page Pro5 chuẩn Katana + Regex i64.Const + ProfileSwitcherQuery.
- Khóa cứng ProfileUID (615...) & sw_token từ ProfileSwitcherQuery (chống ghi đè
  bởi additional_profile_id ảo của Graph API).
================================================================================
"""

import os
import sys
import re
import time
import json
import uuid
import random
import string
import secrets
import base64
import hmac
import hashlib
import struct
import logging
import datetime
import threading
import urllib.parse
from collections import deque
from queue import Queue, Empty
from typing import Optional, Dict, Any, List, Tuple, Set

try:
    import requests
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    print("Vui lòng cài đặt requests bằng lệnh: pip install requests")
    sys.exit(1)


# ==============================================================================
# 1. CẤU HÌNH LOGGING, MÀU SẮC TERMINAL & NHẬT KÝ TIẾN TRÌNH (LIVE LOGS)
# ==============================================================================

logger = logging.getLogger("RegTransferVIP")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    file_handler = logging.FileHandler("transfer_page.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


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
    with PRINT_LOCK:
        print(msg)
        sys.stdout.flush()


def add_process_log(acc_id: int, uid: str, msg: str):
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    short_uid = (uid or "Unknown")[:15]
    log_line = f"[{now_str}] [Acc #{acc_id:02d} | {short_uid}] {msg}"
    with LOG_LOCK:
        LIVE_PROCESS_LOGS.append(log_line)
    clean_log = re.sub(r"\033\[[0-9;]*m", "", log_line)
    logger.info(clean_log)


def clear_screen():
    os.system("cls" if sys.platform == "win32" else "clear")


def print_banner():
    clear_screen()
    safe_print(f"{Colors.CYAN}{Colors.BOLD}")
    safe_print("=" * 100)
    safe_print("   TOOL REG PAGE PRO5 VIP (V5) + CHUYỂN PAGE SIÊU MẠNH (DYNAMIC NT_BUNDLE_TREE 4 BƯỚC)   ")
    safe_print("   Đầu Vào Đa Năng (UID|Pass|Cookie|Token) | Chuẩn ProfileUID 615... & Token ProfileSwitcher   ")
    safe_print("=" * 100)
    safe_print(f"{Colors.RESET}")


def input_multiline(prompt: str) -> List[str]:
    safe_print(prompt)
    safe_print(f"{Colors.YELLOW}(Dán danh sách vào đây. Dán xong nhấn Enter 2 lần để xác nhận):{Colors.RESET}")
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


def sleep_with_countdown(seconds: float):
    if seconds <= 0:
        return
    with PRINT_LOCK:
        print(f"Chờ {seconds} giây...", end="", flush=True)
    time.sleep(seconds)
    with PRINT_LOCK:
        print("\r" + " " * 40 + "\r", end="", flush=True)


# ==============================================================================
# 2. BỘ LỌC PROXY & ĐẦU VÀO ĐA NĂNG (CHỐNG NHẬN NHẦM PASS/COOKIE THÀNH PROXY)
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
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", h):
        return all(0 <= int(o) <= 255 for o in h.split("."))
    if ":" in h and re.match(r"^[0-9a-fA-F:]+$", h) and h.count(":") >= 2:
        return True
    if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", h):
        return True
    return False


def parse_proxy(proxy_str: Optional[str]) -> Optional[Dict[str, str]]:
    if not proxy_str or not str(proxy_str).strip():
        return None
    raw = str(proxy_str).strip()

    if any(k in raw for k in ["c_user=", "xs=", "datr=", "fr=", "EAAAA", "EAAG", " ", "|", ";"]):
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
        if ":" not in auth_part or ":" not in host_part:
            return None
        user, password = auth_part.split(":", 1)
        if host_part.startswith("[") and "]:" in host_part:
            h_ipv6, port = host_part[1:].rsplit("]:", 1)
            host = f"[{h_ipv6}]"
        else:
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


def _is_2fa_secret(s: str) -> bool:
    clean = s.replace(" ", "")
    if len(clean) in (16, 24, 32) and re.match(r"^[A-Z2-7]+=*$", clean):
        return True
    return False


def parse_universal_line(line: str) -> Optional[Dict[str, Any]]:
    raw = str(line).strip()
    if not raw or raw.startswith("#"):
        return None

    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if not parts:
        return None

    uid = ""
    pwd = ""
    twofa = ""
    cookie = ""
    token = ""
    proxy = None
    used_indices = set()

    for i, p in enumerate(parts):
        tk_m = re.search(r"(EAAAA[A-Za-z0-9]{20,}|EAAG[A-Za-z0-9]{20,})", p)
        if tk_m and not token and "c_user=" not in p:
            token = tk_m.group(1)
            used_indices.add(i)
            continue

        if any(k in p for k in ("c_user=", "xs=", "datr=", "fr=")) and not cookie:
            cookie = p
            used_indices.add(i)
            c_u = re.search(r"c_user=(\d+)", p)
            if c_u and not uid:
                uid = c_u.group(1)
            continue

        if not proxy and parse_proxy(p):
            proxy = p
            used_indices.add(i)
            continue

    for i, p in enumerate(parts):
        if i in used_indices:
            continue
        if p.isdigit() and 7 <= len(p) <= 20:
            uid = p
            used_indices.add(i)
            break

    for i, p in enumerate(parts):
        if i in used_indices:
            continue
        if _is_2fa_secret(p) and not twofa:
            twofa = p.replace(" ", "")
            used_indices.add(i)
            break

    for i, p in enumerate(parts):
        if i in used_indices:
            continue
        if p.startswith(("DIE_", "KHONG_LEN", "PAGE_", "DA_BAN", "LOI_BAN", "SUCCESS:", "INVITED_ONLY:")):
            continue
        if re.match(r"^\d{4}-\d{2}-\d{2}", p):
            continue
        if not pwd:
            pwd = p
            used_indices.add(i)
            break

    if not uid:
        u_m = re.search(r"\b(1000\d{10,12}|615\d{11,13}|\d{10,16})\b", raw)
        if u_m:
            uid = u_m.group(1)

    if not token and not (uid and (pwd or cookie)):
        return None

    return {
        "uid": uid,
        "pwd": pwd,
        "twofa": twofa,
        "cookie": cookie,
        "token": token,
        "proxy": proxy,
        "raw": raw
    }


def parse_universal_lines(lines: List[str]) -> List[Dict[str, Any]]:
    results = []
    seen = set()
    for line in lines:
        item = parse_universal_line(line)
        if not item:
            continue
        key = item["token"] or item["uid"] or item["raw"]
        if key not in seen:
            seen.add(key)
            results.append(item)
    return results


def parse_holder_target(raw_input: str) -> List[Dict[str, Optional[str]]]:
    """
    Hỗ trợ nhập Nick Mẹ ở mọi định dạng:
    - UID|Pass|Cookie|Token_Me (tự lọc lấy UID_Me và Token_Me)
    - UID_Me|Token_Me
    - Token_Me (EAAAAU...)
    - Chỉ UID_Me
    """
    targets = []
    if not raw_input or not raw_input.strip():
        return targets

    for line in raw_input.splitlines():
        line = line.strip()
        if not line:
            continue
        parsed = parse_universal_line(line)
        if parsed and (parsed.get("uid") or parsed.get("token")):
            if not parsed.get("token") and parsed.get("uid") and parsed.get("pwd"):
                l_res = login_and_get_token(parsed)
                if l_res.get("success"):
                    parsed["token"] = l_res["token"]
            targets.append({
                "uid": parsed.get("uid") or "",
                "token": parsed.get("token") or None,
                "proxy": parsed.get("proxy") or None
            })
            continue

        for chunk in re.split(r"[,;]+", line):
            chunk = chunk.strip()
            if not chunk:
                continue
            uid = None
            token = None
            proxy = None
            for p in chunk.split("|"):
                p = p.strip()
                tk_m = re.search(r"(EAAAA[A-Za-z0-9]+|EAAG[A-Za-z0-9]+)", p)
                if tk_m and not token and "c_user=" not in p:
                    token = tk_m.group(1)
                elif p.isdigit() and 5 <= len(p) <= 20 and not uid:
                    uid = p
                elif parse_proxy(p) and not proxy:
                    proxy = p
            if uid or token:
                targets.append({"uid": uid or "", "token": token, "proxy": proxy})

    return targets


# ==============================================================================
# 3. KHO USER-AGENT & TÊN PAGE (VIỆT / US / CUSTOM)
# ==============================================================================

FBAV_VERSIONS = [
    ("543.0.0.55.73", "846638243"),
    ("540.0.0.42.50", "838765431"),
    ("535.0.0.40.114", "825638102"),
    ("530.0.0.34.82", "812456789"),
    ("510.0.0.72.41", "725719471")
]

DEVICE_POOL = [
    ("Samsung", "samsung", "Galaxy S24 Ultra", "SM-S928B", 3.5, 1440, 3120, 14, 14),
    ("Samsung", "samsung", "Galaxy S23 Ultra", "SM-S918B", 3.5, 1440, 3088, 13, 14),
    ("Samsung", "samsung", "Galaxy S21 5G", "SM-G991B", 3.0, 1080, 2400, 11, 14),
    ("Xiaomi", "xiaomi", "Xiaomi 13", "2211133G", 3.0, 1080, 2400, 13, 14),
    ("Xiaomi", "xiaomi", "Redmi Note 12 Pro", "22101316G", 3.0, 1080, 2400, 12, 14),
    ("Google", "google", "Pixel 8 Pro", "Pixel 8 Pro", 3.5, 1344, 2992, 14, 14),
    ("Google", "google", "Pixel 7 Pro", "Pixel 7 Pro", 3.5, 1440, 3120, 13, 14),
    ("Oppo", "OPPO", "Reno10 Pro 5G", "CPH2525", 3.0, 1080, 2412, 13, 14)
]

CARRIERS = ["Viettel", "Vinaphone", "MobiFone", "Vietnamobile", "VIETTEL"]
LOCALES = ["vi_VN", "en_US"]

HO_VIET = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đoàn", "Mai", "Trịnh", "Đinh", "Lâm", "Phùng", "Cao", "Hà", "Lương", "Tạ", "Thái"]
DEM_NAM = ["Văn", "Đức", "Đình", "Hữu", "Tuấn", "Minh", "Quốc", "Thanh", "Trọng", "Duy", "Bảo", "Quang", "Hải", "Tiến", "Công", "Khắc", "Gia", "Đăng"]
DEM_NU = ["Thị", "Ngọc", "Thu", "Thanh", "Khánh", "Phương", "Kim", "Ánh", "Hải", "Hồng", "Bảo", "Mỹ", "Quỳnh", "Thùy", "Yến", "Lan", "Mai", "Cẩm"]
TEN_NAM = ["Nam", "Tuấn", "Anh", "Khải", "Dũng", "Quân", "Cường", "Đạt", "Huy", "Hoàng", "Phong", "Long", "Sơn", "Thắng", "Phúc", "Lộc", "Trí", "Trung", "Hiếu", "Nghĩa", "Vinh", "Khánh", "Hưng", "Bách", "Đức", "Kiên", "Lâm"]
TEN_NU = ["Linh", "Trang", "Hằng", "Mai", "Thảo", "Hương", "Anh", "Vy", "Hà", "Ngọc", "Châu", "Nhi", "Trâm", "Hiền", "Dung", "Hoa", "Lan", "Huệ", "Cúc", "Trúc", "Ly", "My", "Oanh", "Quyên", "Tâm", "Uyên", "Vân"]
US_FIRST = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Paul", "Andrew", "Joshua", "Kevin", "Brian", "George", "Edward", "Timothy", "Jason", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle", "Carol", "Amanda", "Melissa", "Rebecca", "Sharon", "Laura", "Sophia", "Emma"]
US_LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Hill", "Flores", "Green", "Adams"]


def generate_random_katana_ua(seed: Optional[str] = None) -> str:
    rng = random.Random(int(hashlib.md5(str(seed).encode()).hexdigest(), 16)) if seed else random.Random()
    mfg, brand, _, dev, den, w, h, amin, amax = rng.choice(DEVICE_POOL)
    av = rng.randint(amin, amax)
    fbav, fbbv = rng.choice(FBAV_VERSIONS)
    return (
        f"[FBAN/FB4A;FBAV/{fbav};FBBV/{fbbv};FBDM/{{density={den},width={w},height={h}}};"
        f"FBLC/{rng.choice(LOCALES)};FBRV/0;FBCR/{rng.choice(CARRIERS)};FBMF/{mfg.lower()};"
        f"FBBD/{brand};FBPN/com.facebook.katana;FBDV/{dev};FBSV/{av};FBOP/1;FBCA/x86_64:arm64-v8a;]"
    )


def get_page_name(mode: str = "viet", custom: Optional[List[str]] = None) -> str:
    if mode == "custom" and custom:
        return random.choice(custom).strip()
    if mode == "us":
        return f"{random.choice(US_FIRST)} {random.choice(US_LAST)}"
    ho = random.choice(HO_VIET)
    if random.random() < 0.5:
        return f"{ho} {random.choice(DEM_NAM)} {random.choice(TEN_NAM)}"
    return f"{ho} {random.choice(DEM_NU)} {random.choice(TEN_NU)}"


# ==============================================================================
# 4. AUTO LOGIN LẤY TOKEN EAAAAU TỪ UID|PASS|COOKIE / 2FA (BLOKS CAA V5)
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


def extract_datr_from_cookie(cookie_str: str) -> str:
    if not cookie_str:
        return ""
    m = re.search(r"datr=([^;\s]+)", cookie_str)
    return m.group(1) if m else ""


class BloksCAALoginService:
    def __init__(self, uid: str, password: str, twofa: str = "", cookie: str = "", proxy: Optional[str] = None):
        self.uid = uid
        self.password = password
        self.twofa = twofa
        self.cookie = cookie
        self.machine_id = extract_datr_from_cookie(cookie) or "".join(random.choices(string.ascii_letters + string.digits, k=22))
        self.device_id = str(uuid.uuid4())
        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False
        px = parse_proxy(proxy)
        if px:
            self.session.proxies.update(px)

    def _build_headers(self) -> dict:
        return {
            "User-Agent": "[FBAN/FB4A;FBAV/498.1.0.64.74;FBBV/692621185;FBDM/{density=1.5,width=540,height=960};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/Xiaomi;FBBD/Xiaomi;FBPN/com.facebook.katana;FBDV/2211133C;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]",
            "authorization": "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32",
            "x-fb-sim-hni": "45201",
            "x-fb-net-hni": "45201",
            "x-graphql-client-library": "graphservice",
            "x-fb-friendly-name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.login.async.send_login_request",
            "x-tigon-is-retry": "False",
            "x-graphql-request-purpose": "fetch",
            "x-fb-device-group": "2789",
            "Accept-Encoding": "identity",
            "x-zero-eh": "error",
            "x-fb-connection-type": "WIFI",
            "x-fb-http-engine": "Tigon/Liger",
            "x-fb-client-ip": "True",
            "x-fb-server-cluster": "True"
        }

    def _create_variables(self) -> str:
        nonce = base64.b64encode(secrets.token_bytes(32)).decode("utf-8")
        raw_data = f'{{"challenge_nonce":"{nonce}","username":"{self.uid}"}}'
        enc_data = base64.b64encode(raw_data.encode("utf-8")).decode("utf-8")
        pwd_formatted = f"#PWD_FB4A:0:{int(time.time())}:{self.password}"

        variable = {
            "params": {
                "params": json.dumps({
                    "client_input_params": {
                        "sim_phones": [],
                        "secure_family_device_id": str(uuid.uuid4()),
                        "attestation_result": {
                            "data": enc_data,
                            "signature": "MEYCIQDtz5TqO0pwysy82Ko92FErORasLag9o/pQYlZl8+zaMgIhAKon529upFiPfGgoS6OkPKg0/VahBuSDxwiTgtzpYQA3",
                            "keyHash": "92398b3e4d9ee926bae93a61fd75e18d750100c1e73fd44d4faa7b9ba9353eee"
                        },
                        "has_granted_read_contacts_permissions": 0,
                        "auth_secure_device_id": "",
                        "has_whatsapp_installed": 0,
                        "password": pwd_formatted,
                        "sso_token_map_json_string": "",
                        "event_flow": "login_manual",
                        "password_contains_non_ascii": "false",
                        "sim_serials": [],
                        "client_known_key_hash": "",
                        "encrypted_msisdn": "",
                        "has_granted_read_phone_permissions": 0,
                        "app_manager_id": "null",
                        "should_show_nested_nta_from_aymh": 0,
                        "device_id": self.device_id,
                        "login_attempt_count": 1,
                        "machine_id": self.machine_id,
                        "flash_call_permission_status": {"READ_PHONE_STATE": "DENIED", "READ_CALL_LOG": "DENIED", "ANSWER_PHONE_CALLS": "DENIED"},
                        "accounts_list": [],
                        "family_device_id": self.device_id,
                        "fb_ig_device_id": [],
                        "device_emails": [],
                        "try_num": 2,
                        "lois_settings": {"lois_token": ""},
                        "event_step": "home_page",
                        "headers_infra_flow_id": "",
                        "openid_tokens": {},
                        "contact_point": self.uid
                    },
                    "server_params": {
                        "should_trigger_override_login_2fa_action": 0,
                        "is_from_logged_out": 0,
                        "should_trigger_override_login_success_action": 0,
                        "login_credential_type": "none",
                        "server_login_source": "login",
                        "waterfall_id": str(uuid.uuid4()),
                        "login_source": "Login",
                        "is_platform_login": 0,
                        "pw_encryption_try_count": 1,
                        "INTERNAL__latency_qpl_marker_id": 36707139,
                        "offline_experiment_group": "caa_iteration_v6_perf_fb_2",
                        "is_from_landing_page": 0,
                        "password_text_input_id": "jirv90:99",
                        "is_from_empty_password": 0,
                        "is_from_msplit_fallback": 0,
                        "ar_event_source": "login_home_page",
                        "username_text_input_id": "jirv90:98",
                        "layered_homepage_experiment_group": None,
                        "device_id": self.device_id,
                        "INTERNAL__latency_qpl_instance_id": 118039064400779,
                        "reg_flow_source": "login_home_native_integration_point",
                        "is_caa_perf_enabled": 1,
                        "credential_type": "password",
                        "is_from_password_entry_page": 0,
                        "caller": "gslr",
                        "family_device_id": self.device_id,
                        "is_from_assistive_id": 0,
                        "access_flow_version": "F2_FLOW",
                        "is_from_logged_in_switcher": 0
                    }
                }),
                "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
                "app_id": "com.bloks.www.bloks.caa.login.async.send_login_request"
            },
            "scale": "1.5",
            "nt_context": {
                "using_white_navbar": True,
                "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
                "pixel_ratio": 1.5,
                "is_push_on": True,
                "debug_tooling_metadata_token": None,
                "is_flipper_enabled": False,
                "theme_params": [],
                "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"
            }
        }
        return json.dumps(variable)

    @staticmethod
    def _extract_token_and_cookie(raw_text: str) -> Dict[str, str]:
        cleaned = raw_text.replace("\\", "")
        at_match = re.search(r'"access_token":"(EAAAA[^"]+)"', cleaned)
        token = at_match.group(1) if at_match else ""
        cookie_list = []
        ck_match = re.search(r'"session_cookies":\s*\[([^\]]+)\]', cleaned)
        if ck_match:
            for name, val in re.findall(r'"name":"([^"]+)","value":"([^"]+)"', ck_match.group(1)):
                cookie_list.append(f"{name}={val}")
        return {"token": token, "cookie": "; ".join(cookie_list)}

    def login(self) -> Dict[str, Any]:
        payload = {
            "method": "post", "pretty": "false", "format": "json", "server_timestamps": "true",
            "locale": "vi_VN", "purpose": "fetch",
            "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.login.async.send_login_request",
            "fb_api_caller_class": "graphservice", "client_doc_id": "11994080423986492941384902285",
            "variables": self._create_variables(), "fb_api_analytics_tags": '["GraphServices"]',
            "client_trace_id": str(uuid.uuid4())
        }
        resp = self.session.post("https://b-graph.facebook.com/graphql", headers=self._build_headers(), data=payload, timeout=30)
        text = resp.text

        if "two_step_verification_context" in text or "error_2fa" in text:
            if not self.twofa:
                return {"success": False, "message": "Tài khoản yêu cầu 2FA nhưng thiếu mã 2FA"}
            ctx_m = re.search(r'two_step_verification_context.*?"([A-Za-z0-9_\-]{200,})', text)
            if not ctx_m:
                return {"success": False, "message": "Không lấy được two_step_verification_context"}
            two_step_ctx = ctx_m.group(1)
            mid_m = re.search(r"SaveMachineID[^A-Za-z0-9_-]+([A-Za-z0-9_-]{10,})", text)
            mid_2fa = mid_m.group(1) if mid_m else self.machine_id

            code_6 = generate_totp_code(self.twofa)
            vf_inner = {
                "client_input_params": {
                    "auth_secure_device_id": "", "machine_id": mid_2fa, "code": code_6,
                    "should_trust_device": 1, "family_device_id": self.device_id, "device_id": self.device_id
                },
                "server_params": {
                    "INTERNAL__latency_qpl_marker_id": 36707139, "device_id": self.device_id,
                    "challenge": "totp", "machine_id": mid_2fa,
                    "INTERNAL__latency_qpl_instance_id": random.randint(0x5AF3107A4000, 0x38D7EA4C67FFF),
                    "two_step_verification_context": two_step_ctx, "flow_source": "two_factor_login"
                }
            }
            vf_vars = {
                "params": json.dumps(vf_inner),
                "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
                "app_id": "com.bloks.www.two_step_verification.verify_code.async",
                "using_white_navbar": True, "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
                "pixel_ratio": 1.5, "is_push_on": True, "debug_tooling_metadata_token": None,
                "is_flipper_enabled": False, "theme_params": [],
                "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c", "scale": 1,
                "nt_context": {
                    "using_white_navbar": True, "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
                    "pixel_ratio": 1.5, "is_push_on": True, "debug_tooling_metadata_token": None,
                    "is_flipper_enabled": False, "theme_params": [],
                    "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"
                }
            }
            vf_resp = self.session.post(
                "https://b-graph.facebook.com/graphql",
                headers=self._build_headers(),
                data={
                    "method": "post", "pretty": "false", "format": "json", "server_timestamps": "true",
                    "locale": "vi_VN", "purpose": "fetch",
                    "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.two_step_verification.verify_code.async",
                    "fb_api_caller_class": "graphservice", "client_doc_id": "11994080423986492941384902285",
                    "variables": json.dumps(vf_vars), "fb_api_analytics_tags": '["GraphServices"]',
                    "generate_session_cookies": "1", "client_trace_id": str(uuid.uuid4())
                },
                timeout=30
            )
            extracted = self._extract_token_and_cookie(vf_resp.text)
            if extracted["token"]:
                return {"success": True, "uid": self.uid, "token": extracted["token"], "cookie": extracted["cookie"] or self.cookie}
            return {"success": False, "message": "Xác thực 2FA Bloks thất bại"}

        extracted = self._extract_token_and_cookie(text)
        if extracted["token"]:
            return {"success": True, "uid": self.uid, "token": extracted["token"], "cookie": extracted["cookie"] or self.cookie}
        return {"success": False, "message": "Không trích xuất được Token từ Bloks Login"}


def login_and_get_token(acc: Dict[str, Any], custom_ua: Optional[str] = None) -> Dict[str, Any]:
    uid = acc.get("uid", "")
    pwd = acc.get("pwd", "")
    twofa = acc.get("twofa", "")
    cookie = acc.get("cookie", "")
    proxy = acc.get("proxy")

    if not uid or not pwd:
        return {"success": False, "uid": uid, "message": "Thiếu UID hoặc Mật khẩu để đăng nhập lấy Token"}

    try:
        caa = BloksCAALoginService(uid=uid, password=pwd, twofa=twofa, cookie=cookie, proxy=proxy)
        caa_res = caa.login()
        if caa_res.get("success") and caa_res.get("token"):
            return {
                "success": True, "uid": uid, "pwd": pwd,
                "token": caa_res["token"], "cookie": caa_res.get("cookie", cookie), "name": ""
            }
    except Exception:
        pass

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
    device_id = str(uuid.uuid4())
    data = {
        "adid": str(uuid.uuid4()), "format": "json", "device_id": device_id,
        "email": uid, "password": pwd, "generate_analytics_claim": "1",
        "community_id": "", "cpl": "true", "try_num": "1",
        "family_device_id": device_id, "credentials_type": "password",
        "generate_session_cookies": "1", "error_detail_type": "button_with_disabled",
        "source": "login", "generate_machine_id": "1", "meta_inf_fbmeta": "",
        "advertiser_id": str(uuid.uuid4()), "currently_logged_in_userid": "0",
        "locale": "vi_VN", "client_country_code": "VN", "method": "auth.login",
        "fb_api_req_friendly_name": "authenticate",
        "fb_api_caller_class": "com.facebook.account.login.protocol.Fb4aAuthHandler",
        "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32"
    }
    if cookie:
        datr_val = extract_datr_from_cookie(cookie)
        if datr_val:
            data["machine_id"] = datr_val

    try:
        res = s.post("https://b-api.facebook.com/method/auth.login", headers=headers, data=data, timeout=30).json()
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
                    res = s.post("https://b-api.facebook.com/method/auth.login", headers=headers, data=data, timeout=30).json()

        if "access_token" in res:
            return {
                "success": True, "uid": str(res.get("uid", uid)), "pwd": pwd,
                "token": res["access_token"], "cookie": cookie,
                "name": res.get("user_storage", {}).get("name", "")
            }
        err = res.get("error_msg") or res.get("message") or str(res)
        return {"success": False, "uid": uid, "message": err[:80]}
    except Exception as e:
        return {"success": False, "uid": uid, "message": str(e)[:80]}


# ==============================================================================
# 5. CORE CHUYỂN PAGE SIÊU MẠNH (CHUẨN PROFILE_UID 615... & SW_TOKEN)
# ==============================================================================

def extract_payload_from_tree(nt_bundle_tree: str) -> Optional[str]:
    """Bóc tách URL permissions/update động từ nt_bundle_tree của Step 1."""
    if not nt_bundle_tree:
        return None
    m = re.search(r'(/nt/profile/admin_management/permissions/update\?[^"\'\\}]+)', nt_bundle_tree)
    if m:
        return m.group(1).replace(r"\/", "/")
    try:
        tree = json.loads(nt_bundle_tree)

        def find_update_url(obj):
            if isinstance(obj, dict):
                if "$" in obj and isinstance(obj["$"], str) and "/nt/profile/admin_management/permissions/update" in obj["$"]:
                    return obj["$"].replace(r"\/", "/")
                for v in obj.values():
                    res = find_update_url(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_update_url(item)
                    if res:
                        return res
            return None

        return find_update_url(tree)
    except Exception:
        return None


def check_step1_response(response_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
    if isinstance(response_data, str):
        try:
            res = json.loads(response_data)
        except Exception:
            return False, f"Response không phải JSON: {response_data[:150]}", {}
    elif isinstance(response_data, dict):
        res = response_data
    else:
        return False, f"Kiểu dữ liệu không hợp lệ: {type(response_data)}", {}

    errors = res.get("errors")
    if errors and isinstance(errors, list) and len(errors) > 0:
        err = errors[0]
        code = err.get("code")
        msg = err.get("message", "")
        summary = err.get("summary", "")
        desc = err.get("description", "")
        detail = {"code": code, "message": msg, "summary": summary, "description": desc}
        if "password" in msg.lower() or "mật khẩu" in desc.lower():
            return False, f"Mật khẩu không chính xác (code: {code})", detail
        return False, f"Step 1 thất bại: {desc or summary or msg} (Code: {code})", detail

    data = res.get("data", {})
    nt_async = data.get("native_templates_async") if data else None
    if nt_async is not None:
        return True, "Step 1 thành công: Đã xác thực mật khẩu", {}
    return False, "Step 1 thất bại: Không tìm thấy dữ liệu native_templates_async", {"raw": res}


def check_step2_response(response_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
    if isinstance(response_data, str):
        try:
            res = json.loads(response_data)
        except Exception:
            return False, f"Response không phải JSON: {response_data[:150]}", {}
    elif isinstance(response_data, dict):
        res = response_data
    else:
        return False, f"Kiểu dữ liệu không hợp lệ: {type(response_data)}", {}

    errors = res.get("errors")
    if errors and isinstance(errors, list) and len(errors) > 0:
        err = errors[0]
        code = err.get("code")
        msg = err.get("message", "")
        summary = err.get("summary", "")
        desc = err.get("description", "")
        detail = {"code": code, "message": msg, "summary": summary, "description": desc}
        combined = f"{msg} {summary} {desc}".lower()
        if "already admin" in combined or "đã là quản trị viên" in combined:
            return False, "Tài khoản đích đã là quản trị viên của Page", detail
        if "pending" in combined or "lời mời" in combined:
            return False, "Đã có lời mời đang chờ duyệt", detail
        return False, f"Step 2 thất bại: {desc or summary or msg} (Code: {code})", detail

    data = res.get("data", {})
    nt_async = data.get("native_templates_async") if data else None
    if nt_async is not None:
        return True, "Step 2 thành công: Đã gửi lời mời", {}
    return False, "Step 2 thất bại: Dữ liệu trả về trống", {"raw": res}


def check_step3_response(response_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
    if isinstance(response_data, str):
        try:
            res = json.loads(response_data)
        except Exception:
            raw_text = response_data
            m = re.search(r'invitation_id[\\"\':=]+(\d+)', raw_text)
            if m:
                inv_id = m.group(1)
                return True, f"Step 3 thành công: invitation_id = {inv_id}", {"invitation_id": inv_id}
            return False, f"Response không phải JSON: {response_data[:150]}", {}
    elif isinstance(response_data, dict):
        res = response_data
    else:
        return False, f"Kiểu dữ liệu không hợp lệ: {type(response_data)}", {}

    errors = res.get("errors")
    if errors and isinstance(errors, list) and len(errors) > 0:
        err = errors[0]
        code = err.get("code")
        msg = err.get("message", "")
        return False, f"Step 3 thất bại: {msg} (Code: {code})", {}

    invitation_id = None
    try:
        data = res.get("data", {})
        nt_screen = data.get("native_template_screen", {})
        nt_bundle = nt_screen.get("nt_bundle", {})
        attrs = nt_bundle.get("nt_bundle_attributes", [])
        for attr in attrs:
            if attr.get("name") == "1":
                params_str = attr.get("intent_value", {}).get("query", {}).get("params", "")
                if "invitation_id" in params_str:
                    m = re.search(r"invitation_id[=:]\s*(\d+)", params_str)
                    if m:
                        invitation_id = m.group(1)
                        break
    except Exception:
        pass

    if not invitation_id:
        json_dump = json.dumps(res)
        m = re.search(r'invitation_id[\\"\':=]+(\d+)', json_dump)
        if m:
            invitation_id = m.group(1)

    if invitation_id:
        return True, f"Step 3 thành công: invitation_id = {invitation_id}", {"invitation_id": invitation_id}
    return False, "Step 3 không tìm thấy lời mời (có thể chưa nhận được hoặc đã hết hạn)", {"raw": res}


def check_step4_response(response_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
    if isinstance(response_data, str):
        try:
            res = json.loads(response_data)
        except Exception:
            return False, f"Response không phải JSON: {response_data[:150]}", {}
    elif isinstance(response_data, dict):
        res = response_data
    else:
        return False, f"Kiểu dữ liệu không hợp lệ: {type(response_data)}", {}

    errors = res.get("errors")
    if errors and isinstance(errors, list) and len(errors) > 0:
        err = errors[0]
        code = err.get("code")
        msg = err.get("message", "")
        summary = err.get("summary", "")
        desc = err.get("description", "")
        combined = f"{msg} {summary} {desc}".lower()
        if "accepted" in combined or "đã chấp nhận" in combined:
            return True, "Lời mời này đã được chấp nhận từ trước", {}
        if "expired" in combined or "hết hạn" in combined:
            return False, "Lời mời đã hết hạn hoặc bị hủy", {}
        return False, f"Step 4 thất bại: {desc or msg} (Code: {code})", {}

    data = res.get("data", {})
    nt_async = data.get("native_templates_async") if data else None
    if nt_async is not None:
        return True, "🎉 Chuyển Page thành công! Tài khoản đích đã là Admin", {}
    return False, "Step 4 thất bại: Không nhận được xác nhận", {"raw": res}


def xac_nhan_mk(
    auth_token: str,
    admin_id: str,
    profile_id: str,
    password: str,
    proxy: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """Bước 1: Xác thực mật khẩu bằng sw_token và profile_id (615...) -> trả về nt_bundle_tree."""
    url = "https://graph.facebook.com/graphql"
    clean_token = auth_token.replace("OAuth ", "").replace("Bearer ", "").strip()
    headers = {
        "Accept-Encoding": "gzip",
        "authorization": f"OAuth {clean_token}",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "user-agent": "[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]",
        "x-fb-connection-type": "WIFI",
        "x-fb-device-group": "4789",
        "x-fb-friendly-name": "NativeTemplateAsyncQuery",
        "x-fb-request-analytics-tags": '{"network_tags":{"product":"350685531728","request_category":"graphql","purpose":"none","retry_attempt":"0"},"application_tags":"graphservice"}',
        "x-graphql-client-library": "graphservice"
    }
    nt_context = {
        "using_white_navbar": True,
        "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
        "pixel_ratio": 2,
        "is_push_on": True,
        "debug_tooling_metadata_token": None,
        "is_flipper_enabled": False,
        "theme_params": [{"value": [], "design_system_name": "FDS"}],
        "bloks_version": "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
    }
    payload_string = (
        f"/nt/profile/admin_management/permissions_reauth?"
        f"admin_id={admin_id}&"
        f"admin_rows_container_id=%5B%228bxxoh%3A2%22%2Cnull%5D&"
        f"admin_type=full_access&"
        f"entry_point_screen_id=%5B%227o2xil%3A5%22%2Cnull%5D&"
        f"profile_id={profile_id}&"
        f"state_ids%5Bauthenticated%5D=8csr9g%3A0&"
        f"state_ids%5Bauthentication_attempted%5D=8csr9g%3A1&"
        f"state_ids%5Bshow_entry_point_saving_spinner%5D=8bxxoh%3A0&"
        f"state_ids%5Bshow_saving_spinner%5D=8csr9g%3A3&"
        f"state_ids%5Bads%5D=8clnk7%3A2&"
        f"state_ids%5Bcontent%5D=8clnk7%3A3&"
        f"state_ids%5Binsights%5D=8clnk7%3A4&"
        f"state_ids%5Bmessages%5D=8clnk7%3A5&"
        f"state_ids%5Bmoderate%5D=8clnk7%3A6"
    )
    client_data = {"sensitive_string_value": json.dumps([["password", password]])}
    variables = {
        "params": {
            "nt_context": nt_context,
            "payload": payload_string,
            "client_data": client_data
        },
        "nt_context": nt_context,
        "scale": "2",
        "use_native_entrypoint_for_stars_on_reels": True,
        "profile_image_size": 188,
        "include_image_ranges": True
    }
    data = {
        "fb_api_client_context": '{"is_background":false}',
        "pretty": "false",
        "variables": json.dumps(variables, ensure_ascii=False),
        "method": "post",
        "client_doc_id": "30749539927629244093798192451",
        "format": "json",
        "server_timestamps": "true",
        "locale": "vi_VN",
        "fb_api_req_friendly_name": "NativeTemplateAsyncQuery",
        "fb_api_caller_class": "graphservice"
    }
    try:
        resp = requests.post(url, headers=headers, data=data, proxies=parse_proxy(proxy), timeout=30, verify=False)
        resp_json = resp.json()
    except Exception as e:
        err_str = f"Lỗi request Step 1: {e}"
        logger.error(err_str)
        return None, err_str

    is_ok, msg, _ = check_step1_response(resp_json)
    if not is_ok:
        logger.error(msg)
        return None, msg
    logger.debug(msg)
    try:
        bundles = resp_json["data"]["native_templates_async"]["native_template_bundles"]
        for b in bundles:
            tree_cand = b.get("nt_bundle_tree", "")
            if tree_cand and extract_payload_from_tree(tree_cand):
                return tree_cand, msg
        tree = bundles[0]["nt_bundle_tree"]
        return tree, msg
    except (KeyError, IndexError, TypeError):
        err_str = "Không tìm thấy nt_bundle_tree trong response Step 1."
        logger.error(err_str)
        return None, err_str


def gui_loi_moi(auth_token: str, nt_bundle_tree: str, proxy: Optional[str] = None) -> Tuple[bool, str]:
    """Bước 2: Bóc tách URL permissions/update từ nt_bundle_tree và gửi lời mời Admin."""
    payload = extract_payload_from_tree(nt_bundle_tree)
    if not payload:
        err_str = "Không tìm thấy URL permissions/update trong nt_bundle_tree (Kiểm tra lại mật khẩu/quyền Page)"
        logger.error(err_str)
        return False, err_str

    clean_token = auth_token.replace("OAuth ", "").replace("Bearer ", "").strip()
    state_data = {
        "ads": True,
        "insights": True,
        "messages": True,
        "content": True,
        "moderate": True,
        "show_entry_point_saving_spinner": "NONE"
    }
    nt_context = {
        "using_white_navbar": True,
        "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
        "pixel_ratio": 2,
        "is_push_on": True,
        "debug_tooling_metadata_token": None,
        "is_flipper_enabled": False,
        "theme_params": [{"value": [], "design_system_name": "FDS"}],
        "bloks_version": "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
    }
    variables = {
        "params": {
            "payload": payload,
            "state_data": json.dumps(state_data),
            "nt_context": nt_context
        },
        "nt_context": nt_context,
        "scale": "2",
        "use_native_entrypoint_for_stars_on_reels": True,
        "profile_image_size": 188,
        "include_image_ranges": True
    }
    data = {
        "fb_api_client_context": '{"is_background":false}',
        "pretty": "false",
        "variables": json.dumps(variables, ensure_ascii=False),
        "method": "post",
        "client_doc_id": "30749539927629244093798192451",
        "format": "json",
        "server_timestamps": "true",
        "locale": "vi_VN",
        "fb_api_req_friendly_name": "NativeTemplateAsyncQuery",
        "fb_api_analytics_tags": '["GraphServices"]',
        "client_trace_id": str(uuid.uuid4()),
        "fb_api_caller_class": "graphservice"
    }
    headers = {
        "Accept-Encoding": "gzip",
        "authorization": f"OAuth {clean_token}",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Host": "graph.facebook.com",
        "user-agent": "[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]",
        "x-fb-connection-type": "WIFI",
        "x-fb-device-group": "4789",
        "x-fb-friendly-name": "NativeTemplateAsyncQuery",
        "x-fb-request-analytics-tags": '{"network_tags":{"product":"350685531728","request_category":"graphql","purpose":"none","retry_attempt":"0"},"application_tags":"graphservice"}',
        "x-graphql-client-library": "graphservice"
    }
    url = "https://graph.facebook.com/graphql"
    try:
        resp = requests.post(url, headers=headers, data=data, proxies=parse_proxy(proxy), timeout=30, verify=False)
        resp_json = resp.json()
    except Exception as e:
        err_str = f"Lỗi request Step 2: {e}"
        logger.error(err_str)
        return False, err_str
    is_ok, msg, _ = check_step2_response(resp_json)
    if not is_ok:
        logger.error(msg)
        return False, msg
    logger.debug(msg)
    return True, msg


def ktra_loi_moi(
    auth_token: str,
    profile_id: str,
    invitee_id: str,
    proxy: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """Bước 3: Lấy mã invitation_id từ tài khoản nhận (Nick Mẹ)."""
    url = "https://graph.facebook.com/graphql"
    clean_token = auth_token.replace("OAuth ", "").replace("Bearer ", "").strip()
    headers = {
        "Accept-Encoding": "gzip",
        "authorization": f"OAuth {clean_token}",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Host": "graph.facebook.com",
        "user-agent": "[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]",
        "x-fb-connection-type": "WIFI",
        "x-fb-device-group": "4789",
        "x-fb-friendly-name": "NativeTemplateAsyncQuery",
        "x-fb-request-analytics-tags": '{"network_tags":{"product":"350685531728","request_category":"graphql","purpose":"none","retry_attempt":"0"},"application_tags":"graphservice"}',
        "x-graphql-client-library": "graphservice"
    }
    nt_context = {
        "using_white_navbar": True,
        "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
        "pixel_ratio": 2,
        "is_push_on": True,
        "debug_tooling_metadata_token": None,
        "is_flipper_enabled": False,
        "theme_params": [{"value": [], "design_system_name": "FDS"}],
        "bloks_version": "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
    }
    params_str = json.dumps({
        "screen_id": '["sz9fnp:17",null]',
        "profile_id": str(profile_id),
        "invitee_id": str(invitee_id)
    })
    variables = {
        "params": {
            "nt_context": nt_context,
            "path": "/nt/profile/admin_management/invitation",
            "params": params_str,
            "extra_client_data": {}
        },
        "scale": "2",
        "use_native_entrypoint_for_stars_on_reels": True,
        "nt_context": nt_context
    }
    data = {
        "pretty": "false",
        "variables": json.dumps(variables, ensure_ascii=False),
        "method": "post",
        "client_doc_id": "221080835214205752894689842827",
        "purpose": "fetch",
        "format": "json",
        "server_timestamps": "true",
        "locale": "vi_VN",
        "fb_api_req_friendly_name": "NativeTemplateScreenQuery",
        "client_trace_id": str(uuid.uuid4()),
        "fb_api_client_context": '{"is_background":false}',
        "fb_api_analytics_tags": '["surfaces.fb.GraphServiceEmitter","GraphServices"]',
        "fb_api_caller_class": "graphservice"
    }
    try:
        resp = requests.post(url, headers=headers, data=data, proxies=parse_proxy(proxy), timeout=30, verify=False)
        resp_json = resp.json()
    except Exception as e:
        err_str = f"Lỗi request Step 3: {e}"
        logger.error(err_str)
        return None, err_str
    is_ok, msg, detail = check_step3_response(resp_json)
    if not is_ok:
        logger.error(msg)
        return None, msg
    logger.debug(msg)
    return detail.get("invitation_id"), msg


def xac_nhan_loi_moi(
    auth_token: str,
    invitation_id: str,
    accept_invitation: int = 1,
    proxy: Optional[str] = None
) -> Tuple[bool, str]:
    """Bước 4: Chấp nhận lời mời Admin bằng Token tài khoản nhận (Nick Mẹ)."""
    url = "https://graph.facebook.com/graphql"
    clean_token = auth_token.replace("OAuth ", "").replace("Bearer ", "").strip()
    headers = {
        "Accept-Encoding": "gzip",
        "authorization": f"OAuth {clean_token}",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Host": "graph.facebook.com",
        "user-agent": "[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]",
        "x-fb-connection-type": "WIFI",
        "x-fb-device-group": "4789",
        "x-fb-friendly-name": "NativeTemplateAsyncQuery",
        "x-fb-request-analytics-tags": '{"network_tags":{"product":"350685531728","request_category":"graphql","purpose":"none","retry_attempt":"0"},"application_tags":"graphservice"}',
        "x-graphql-client-library": "graphservice"
    }
    nt_context = {
        "using_white_navbar": True,
        "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
        "pixel_ratio": 2,
        "is_push_on": True,
        "debug_tooling_metadata_token": None,
        "is_flipper_enabled": False,
        "theme_params": [{"value": [], "design_system_name": "FDS"}],
        "bloks_version": "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
    }
    payload = f"/nt/profile/admin_management/invitation_response?accept_invitation={accept_invitation}&invitation_id={invitation_id}&admin_type=full_access"
    variables = {
        "params": {
            "payload": payload,
            "nt_context": nt_context
        },
        "nt_context": nt_context,
        "scale": "2",
        "use_native_entrypoint_for_stars_on_reels": True,
        "profile_image_size": 188,
        "include_image_ranges": True
    }
    data = {
        "fb_api_client_context": '{"is_background":false}',
        "pretty": "false",
        "variables": json.dumps(variables, ensure_ascii=False),
        "method": "post",
        "client_doc_id": "30749539927629244093798192451",
        "format": "json",
        "server_timestamps": "true",
        "locale": "vi_VN",
        "fb_api_req_friendly_name": "NativeTemplateAsyncQuery",
        "fb_api_analytics_tags": '["GraphServices"]',
        "client_trace_id": str(uuid.uuid4()),
        "fb_api_caller_class": "graphservice"
    }
    try:
        resp = requests.post(url, headers=headers, data=data, proxies=parse_proxy(proxy), timeout=30, verify=False)
        resp_json = resp.json()
    except Exception as e:
        err_str = f"Lỗi request Step 4: {e}"
        logger.error(err_str)
        return False, err_str
    is_ok, msg, _ = check_step4_response(resp_json)
    if not is_ok:
        logger.error(msg)
        return False, msg
    logger.debug(msg)
    return True, msg


def get_id(token: str, proxy: Optional[str] = None) -> Optional[Tuple[str, str]]:
    url = "https://graph.facebook.com/v24.0/me"
    headers = {
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Host": "graph.facebook.com",
        "User-Agent": "okhttp/5.1.0",
    }
    params = {"fields": "id,name", "access_token": token}
    try:
        resp = requests.get(url, headers=headers, params=params, proxies=parse_proxy(proxy), timeout=25, verify=False)
        data = resp.json()
    except Exception as e:
        logger.error(f"Lỗi request lấy thông tin tài khoản: {e}")
        return None
    if not isinstance(data, dict) or "error" in data:
        return None
    uid = data.get("id")
    uname = data.get("name")
    if not uid:
        return None
    return str(uid), uname or ""


def get_managed_page_ids(token: str, proxy: Optional[str] = None) -> Set[str]:
    page_ids = set()
    url = "https://graph.facebook.com/v24.0/me/accounts"
    headers = {
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Host": "graph.facebook.com",
        "User-Agent": "okhttp/5.1.0",
    }
    params = {"fields": "id", "access_token": token, "limit": 100}
    proxies = parse_proxy(proxy)
    try:
        resp = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=25, verify=False)
        data = resp.json()
        if isinstance(data, dict) and "error" not in data:
            for page in data.get("data", []):
                if page.get("id"):
                    page_ids.add(str(page["id"]))
    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách page từ token đích: {e}")
    return page_ids


def _fetch_all_pages_raw(token: str, profile_id: str, proxy: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Lấy danh sách Page Pro5 chuẩn:
    - Lấy ProfileUID thật (615...) và sw_token từ ProfileSwitcherQuery (client_doc_id 116912609015732060545213902280).
    - Tuyệt đối KHÔNG lấy additional_profile_id (297858...) từ Graph API /me/accounts để tránh làm hỏng Step 1.
    """
    proxies = parse_proxy(proxy)
    headers_graph = {
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Host": "graph.facebook.com",
        "User-Agent": "okhttp/5.1.0",
    }
    # Không query additional_profile_id từ Graph API vì nó trả về ID ảo 297858...
    params_graph = {
        "fields": "id,name,access_token",
        "access_token": token,
        "limit": 100
    }
    graph_pages = []
    try:
        resp = requests.get(
            "https://graph.facebook.com/v24.0/me/accounts",
            params=params_graph, headers=headers_graph, proxies=proxies, timeout=25, verify=False
        )
        data = resp.json()
        if isinstance(data, dict):
            for p in data.get("data", []):
                pid = str(p.get("id", ""))
                if pid:
                    graph_pages.append({
                        "page_id": pid,
                        "name": str(p.get("name", "")).strip(),
                        "graph_token": str(p.get("access_token", ""))
                    })
    except Exception as e:
        logger.error(f"Lỗi lấy danh sách page qua Graph API: {e}")

    url = "https://b-graph.facebook.com/graphql"
    headers_sw = {
        "Accept-Encoding": "gzip",
        "Authorization": f"OAuth {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": (
            "[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;"
            "FBDM/{density=0.75,width=300,height=540};"
            "FBLC/vi_VN;FBRV/0;FBCR/MobiFone;"
            "FBMF/MTool-Max;FBBD/MTool-Max;"
            "FBPN/com.facebook.katana;FBDV/MTool-Max;"
            "FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]"
        ),
    }
    variables = {
        "profile_switcher_connection_first": 300,
        "additional_profile_picture_size": 80,
        "profileID": str(profile_id),
        "main_profile_picture_size": 80,
        "scale": "2",
        "nt_context": {
            "using_white_navbar": True,
            "styles_id": "588d028b36bed0e1889e09b60e0f9aea",
            "pixel_ratio": 2,
            "is_push_on": True,
            "debug_tooling_metadata_token": None,
            "is_flipper_enabled": False,
            "theme_params": [{"value": [], "design_system_name": "FDS"}],
            "bloks_version": "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
        },
        "overflow_recent_searches_filter_ids": [],
        "use_native_entrypoint_for_stars_on_reels": True
    }
    data_sw = {
        "method": "post",
        "pretty": "false",
        "format": "json",
        "server_timestamps": "true",
        "locale": "vi_VN",
        "client_doc_id": "116912609015732060545213902280",
        "variables": json.dumps(variables, separators=(",", ":"))
    }

    switcher_profiles = []
    try:
        resp = requests.post(url, headers=headers_sw, data=data_sw, proxies=proxies, timeout=25, verify=False)
        result = resp.json()
        if isinstance(result, dict):
            user = result.get("data", {}).get("user", {})
            profiles = user.get("profile_switcher_eligible_profiles", {}).get("edges", [])
            for edge in profiles:
                node = edge.get("node", {})
                prof = node.get("profile", {})
                sinfo = node.get("session_info", {})
                prof_id = str(prof.get("id", ""))
                prof_name = str(prof.get("name", "")).strip()
                sw_token = str(sinfo.get("access_token", ""))

                if not prof_id or prof_id == str(profile_id):
                    continue
                switcher_profiles.append({
                    "prof_id": prof_id,
                    "name": prof_name,
                    "sw_token": sw_token
                })
    except Exception as e:
        logger.error(f"Lỗi gọi ProfileSwitcherQuery: {e}")

    # Ghép ProfileSwitcher (ưu tiên số 1 cho Chuyển Page) với Graph API (cho Page ID truyền thống)
    final_pages = []
    used_graph_indices = set()

    for sw in switcher_profiles:
        matched_graph = None
        for idx, gp in enumerate(graph_pages):
            if idx in used_graph_indices:
                continue
            if gp["page_id"] == sw["prof_id"] or gp["name"].lower() == sw["name"].lower():
                matched_graph = gp
                used_graph_indices.add(idx)
                break

        final_pages.append({
            "page_id": matched_graph["page_id"] if matched_graph else sw["prof_id"],
            "name": sw["name"] or (matched_graph["name"] if matched_graph else ""),
            "additional_profile_id": sw["prof_id"],  # Luôn là ProfileUID 615... từ ProfileSwitcher!
            "access_token": sw["sw_token"] or (matched_graph["graph_token"] if matched_graph else ""),
            "graph_token": matched_graph["graph_token"] if matched_graph else sw["sw_token"]
        })

    # Thêm các Page chỉ có bên Graph API (nếu ProfileSwitcher chưa đồng bộ kịp)
    for idx, gp in enumerate(graph_pages):
        if idx not in used_graph_indices:
            final_pages.append({
                "page_id": gp["page_id"],
                "name": gp["name"],
                "additional_profile_id": gp["page_id"],
                "access_token": gp["graph_token"],
                "graph_token": gp["graph_token"]
            })

    return final_pages


def execute_super_transfer(
    page_uid: str,
    page_id: str,
    page_token: str,
    sender_token: str,
    password: str,
    target_uid: str,
    receiver_token: Optional[str] = None,
    sender_proxy: Optional[str] = None,
    receiver_proxy: Optional[str] = None,
    step_callback=None
) -> Dict[str, Any]:
    """
    Điều phối Chuyển Page Siêu Mạnh 4 Bước:
    - Ưu tiên số 1: (page_uid [615... từ ProfileSwitcher], page_token [sw_token từ ProfileSwitcher])
    - Chỉ dừng vòng lặp Bước 1 khi nt_bundle_tree thực sự có chứa URL permissions/update!
    """
    res_out = {
        "success": False,
        "status": "FAILED",
        "invitation_id": None,
        "message": ""
    }

    if not password:
        res_out["message"] = "Thiếu mật khẩu tài khoản nguồn cho Bước 1 (xac_nhan_mk)"
        return res_out

    candidate_tokens = []
    for tk in [page_token, sender_token]:
        if tk and str(tk) not in candidate_tokens:
            candidate_tokens.append(str(tk))

    candidate_pids = []
    for pid in [page_uid, page_id]:
        if pid and str(pid) not in candidate_pids:
            candidate_pids.append(str(pid))

    valid_nt_tree = None
    active_token = page_token or sender_token
    active_pid = page_uid or page_id
    last_msg = ""

    # --- BƯỚC 1: XÁC THỰC MẬT KHẨU & KIỂM TRA CÓ URL PERMISSIONS/UPDATE TRONG TREE ---
    for p_uid_try in candidate_pids:
        if valid_nt_tree:
            break
        for tk_try in candidate_tokens:
            if step_callback:
                step_callback(f"Bước 1/4: Đang xác thực mật khẩu cho Page (ProfileUID: {p_uid_try})...")
            tree, msg1 = xac_nhan_mk(
                auth_token=tk_try,
                admin_id=target_uid,
                profile_id=p_uid_try,
                password=password,
                proxy=sender_proxy
            )
            last_msg = msg1
            if tree and extract_payload_from_tree(tree):
                valid_nt_tree = tree
                active_token = tk_try
                active_pid = p_uid_try
                break

    if not valid_nt_tree:
        res_out["message"] = (
            f"Bước 1 không mở được quyền chuyển (ProfileUID={page_uid}). "
            f"Chi tiết: {last_msg or 'Không có URL permissions/update trong nt_bundle_tree'}"
        )
        return res_out

    # --- BƯỚC 2: TRÍCH XUẤT PAYLOAD TỪ NT_BUNDLE_TREE & GỬI LỜI MỜI ---
    if step_callback:
        step_callback(f"Bước 2/4: Đang trích xuất URL từ nt_bundle_tree & gửi lời mời tới {target_uid}...")
    ok2, msg2 = gui_loi_moi(auth_token=active_token, nt_bundle_tree=valid_nt_tree, proxy=sender_proxy)
    if not ok2:
        res_out["message"] = msg2
        return res_out

    if not receiver_token:
        res_out["success"] = True
        res_out["status"] = "INVITED_ONLY"
        res_out["message"] = f"Đã gửi lời mời Admin sang UID {target_uid} (Chờ bấm chấp nhận)"
        return res_out

    # --- BƯỚC 3: LẤY INVITATION_ID TỪ TÀI KHOẢN ĐÍCH ---
    if step_callback:
        step_callback(f"Bước 3/4: Đang lấy mã invitation_id bên tài khoản nhận ({target_uid})...")

    invitation_id = None
    msg3 = ""
    for attempt in range(3):
        if attempt > 0:
            time.sleep(3)
        for p_uid_try in [active_pid] + [x for x in candidate_pids if x != active_pid]:
            inv_id, m3 = ktra_loi_moi(
                auth_token=receiver_token,
                profile_id=p_uid_try,
                invitee_id=target_uid,
                proxy=receiver_proxy or sender_proxy
            )
            msg3 = m3
            if inv_id:
                invitation_id = inv_id
                break
        if invitation_id:
            break

    if not invitation_id:
        res_out["success"] = True
        res_out["status"] = "INVITED_ONLY"
        res_out["message"] = f"Đã gửi lời mời nhưng chưa lấy được invitation_id ({msg3})"
        return res_out

    res_out["invitation_id"] = invitation_id

    # --- BƯỚC 4: CHẤP NHẬN LỜI MỜI (AUTO ACCEPT) ---
    if step_callback:
        step_callback(f"Bước 4/4: Đang chấp nhận lời mời (invitation_id: {invitation_id})...")
    ok4, msg4 = xac_nhan_loi_moi(
        auth_token=receiver_token,
        invitation_id=invitation_id,
        accept_invitation=1,
        proxy=receiver_proxy or sender_proxy
    )
    if ok4:
        res_out["success"] = True
        res_out["status"] = "SUCCESS"
        res_out["message"] = f"🎉 Chuyển Page & Auto Accept thành công sang {target_uid}!"
    else:
        res_out["success"] = True
        res_out["status"] = "INVITED_ONLY"
        res_out["message"] = f"Đã mời (ID: {invitation_id}), lỗi bước 4: {msg4}"

    return res_out
  # ==============================================================================
# 6. CÁC HÀM HỖ TRỢ CHỌN PAGE & LÕI REG PAGE PRO5 VIP V5
# ==============================================================================

def parse_selection(selection_str: str, max_index: int) -> List[int]:
    indices = []
    parts = selection_str.replace(" ", "").split(",")
    for part in parts:
        if not part:
            continue
        if part.lower() == "all":
            return list(range(1, max_index + 1))
        if "-" in part:
            try:
                start, end = part.split("-")
                start, end = int(start), int(end)
                if 1 <= start <= end <= max_index:
                    indices.extend(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                idx = int(part)
                if 1 <= idx <= max_index:
                    indices.append(idx)
            except ValueError:
                continue
    return sorted(set(indices))


def get_token_pages(token: str, profile_id: str, proxy: Optional[str] = None) -> List[Dict[str, str]]:
    parsed = _fetch_all_pages_raw(token, profile_id, proxy=proxy)
    if not parsed:
        logger.error("Không tìm thấy Page nào.")
        return []

    safe_print("\nDanh sách Page có thể chuyển:")
    for i, p in enumerate(parsed, 1):
        safe_print(f"  [{i}] {p['name']} (Page ID: {p['page_id']} | ProfileUID: {p['additional_profile_id']})")

    max_idx = len(parsed)
    while True:
        choice = input("Chọn Page (ví dụ: 1-5, 1,3,5, hoặc all để chọn tất cả, q để thoát): ").strip()
        if choice.lower() == "q":
            return []
        indices = parse_selection(choice, max_idx)
        if indices:
            selected_pages = []
            for idx in indices:
                p = parsed[idx - 1]
                selected_pages.append({
                    "page_uid": p["additional_profile_id"] or p["page_id"],
                    "page_token": p["access_token"],
                    "page_name": p["name"],
                    "page_id": p["page_id"]
                })
            return selected_pages
        safe_print(f"{Colors.YELLOW}Lựa chọn không hợp lệ, vui lòng nhập lại.{Colors.RESET}")


def get_all_pages(token: str, profile_id: str, proxy: Optional[str] = None) -> List[Dict[str, str]]:
    parsed = _fetch_all_pages_raw(token, profile_id, proxy=proxy)
    result = []
    for p in parsed:
        result.append({
            "page_uid": p["additional_profile_id"] or p["page_id"],
            "page_token": p["access_token"],
            "page_name": p["name"],
            "page_id": p["page_id"]
        })
    return result


GRAPHQL_URL = "https://graph.facebook.com/graphql"
CLIENT_DOC_ID = "11994080426203054249997361787"
BLOKS_VERSIONING_ID = "c11a8c0d160df62b2395f6153824f0bc6c6e316a74ab1aff67da02cdd7cc890b"
FB_TOKEN_DEAD_CODES = {190, 102, 463, 467, 458, 460, 464, 2500}


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
        last_err = ""
        for attempt in range(1, retries + 1):
            try:
                r = self.session.get(
                    f"https://graph.facebook.com/v24.0/me?fields=id,name&access_token={self.token}",
                    headers={"User-Agent": "okhttp/5.1.0"},
                    timeout=20
                ).json()
                if isinstance(r, dict) and "id" in r:
                    self.mother_uid = str(r["id"])
                    return {"success": True, "uid": str(r["id"]), "name": r.get("name", "Facebook User")}

                err = r.get("error", {}) if isinstance(r, dict) else {}
                code = err.get("code", 0)
                err_msg = err.get("message", "Token không hợp lệ")
                is_die = (
                    code in FB_TOKEN_DEAD_CODES
                    or "OAuthException" in str(r)
                    or "checkpoint" in str(r).lower()
                    or "session" in err_msg.lower()
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
        """Lấy danh sách Page từ _fetch_all_pages_raw (ưu tiên ProfileUID 615... & sw_token từ ProfileSwitcher)."""
        try:
            raw_list = _fetch_all_pages_raw(self.token, self.mother_uid, proxy=self.proxy)
            pages = []
            for p in raw_list:
                pages.append({
                    "id": str(p.get("page_id", "")),
                    "name": str(p.get("name", "")),
                    "access_token": str(p.get("access_token", "")),
                    "graph_token": str(p.get("graph_token", "") or p.get("access_token", "")),
                    "additional_profile_id": str(p.get("additional_profile_id", "") or p.get("page_id", ""))
                })
            return {"success": True, "is_token_die": False, "pages": pages}
        except Exception as e:
            return {"success": False, "is_token_die": False, "pages": [], "message": str(e)}

    def check_single_page_live(self, page_id: str, page_token: str) -> Dict[str, Any]:
        """
        Kiểm tra Page còn sống (LIVE) sau thời gian chờ.
        TUYỆT ĐỐI KHÔNG query 'additional_profile_id' từ Graph API để tránh lấy nhầm ID ảo 297858...
        """
        tk_to_check = page_token or self.token
        try:
            url = (
                f"https://graph.facebook.com/v24.0/{page_id}"
                f"?fields=id,name,is_published"
                f"&access_token={tk_to_check}"
            )
            r = self.session.get(url, headers={"User-Agent": "okhttp/5.1.0"}, timeout=20).json()
            if isinstance(r, dict) and "id" in r:
                if r.get("is_published", True) is False:
                    return {"success": False, "message": "Page bị hủy đăng (Unpublished)"}
                return {
                    "success": True,
                    "page_id": str(r["id"]),
                    "page_name": str(r.get("name", ""))
                }
            err_msg = (r.get("error") or {}).get("message", "Page DIE hoặc bị khóa") if isinstance(r, dict) else "Page lỗi"
            return {"success": False, "message": err_msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def create_page_and_get_token(
        self,
        page_name: str,
        known_page_ids: set,
        step_callback=None
    ) -> Dict[str, Any]:
        """Tạo Page Pro5 chuẩn Katana + Bắt Page mới qua bk.action.i64.Const & ProfileSwitcherQuery."""
        if self.ua_mode == "random":
            self.user_agent = generate_random_katana_ua()

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
            body1 = r1.text
            if "OAuthException" in body1 or r1.status_code == 401:
                return {"success": False, "is_token_die": True, "message": "Token DIE ở Bước 1 (Submit Name)"}
            if "tên này không hợp lệ" in body1.lower() or "name is invalid" in body1.lower():
                return {"success": False, "is_name_invalid": True, "message": f"Tên Page '{page_name}' không hợp lệ"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi mạng Bước 1: {e}"}

        # --- BƯỚC 2: SUBMIT CATEGORY & KHỞI TẠO PAGE ---
        if step_callback:
            step_callback(f"Bước 2/2: Đang chọn Hạng mục & Khởi tạo Page '{page_name}'...")

        p2 = {
            "client_input_params": {
                "entrypoint_logging_data": {"fb_profile_editing_session_entry_point": None, "field_edit_screen_entry_point": None},
                "profile_plus_id": "0", "cp_upsell_declined": 0, "off_platform_creator_reachout_id": "",
                "session_id": None, "category_ids": ["2700", "2201"],
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

        body2 = ""
        try:
            r2 = self.session.post(GRAPHQL_URL, headers=self._get_headers(d2["fb_api_req_friendly_name"]), data=d2, timeout=30)
            body2 = r2.text

            if "OAuthException" in body2 or r2.status_code == 401 or "Session expired" in body2:
                return {"success": False, "is_token_die": True, "message": "Token DIE ở Bước 2 (Submit Category)"}

            if "tạo quá nhiều trang" in body2.lower() or "too many" in body2.lower() or "thử lại sau" in body2.lower():
                return {"success": False, "is_limit": True, "message": "Gần đây bạn đã tạo quá nhiều Trang (Limit)."}

            if '"severity":"CRITICAL"' in body2 or "field_exception" in body2 or '"fb_bloks_action":null' in body2:
                return {"success": False, "is_restricted": True, "message": "Nick bị chặn tạo Page (CRITICAL)"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi mạng Bước 2: {e}"}

        # --- BƯỚC 3: QUÉT LẤY PAGE_UID (615... TỪ PROFILESWITCHER) & SW_TOKEN ---
        if step_callback:
            step_callback(f"Đang bóc ID & lấy Token Page Pro5 của '{page_name}'...")

        candidate_ids = set(re.findall(r"\(bk\.action\.i64\.Const,\s*(\d{10,})\)", body2 or ""))
        new_page_obj = None

        for _ in range(1, 5):
            time.sleep(3)
            scan_res = self.get_all_pages_with_tokens()
            pages_list = scan_res.get("pages", [])

            for p in pages_list:
                pid = str(p.get("id", ""))
                add_id = str(p.get("additional_profile_id", ""))
                if (pid in candidate_ids or add_id in candidate_ids) and p.get("access_token"):
                    new_page_obj = p
                    break

            if not new_page_obj:
                for p in pages_list:
                    pid = str(p.get("id", ""))
                    add_id = str(p.get("additional_profile_id", ""))
                    if pid and pid not in known_page_ids and add_id not in known_page_ids:
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
                "message": f"Đã gửi lệnh tạo '{page_name}' nhưng chưa lên Page"
            }

        page_id = str(new_page_obj.get("id", ""))
        extracted_page_token = str(new_page_obj.get("access_token", ""))
        graph_page_token = str(new_page_obj.get("graph_token", "") or extracted_page_token)
        add_profile_id = str(new_page_obj.get("additional_profile_id", "") or page_id)

        return {
            "success": True,
            "page_id": page_id,
            "page_name": str(new_page_obj.get("name", page_name)),
            "page_token": extracted_page_token,
            "graph_token": graph_page_token,
            "additional_profile_id": add_profile_id
        }

    def upload_media(self, page_id: str, page_token: str, media_type: str = "avatar") -> Dict[str, Any]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        if media_type == "avatar":
            sources = [
                f"https://i.pravatar.cc/1000?u={uuid.uuid4()}",
                f"https://randomuser.me/api/portraits/men/{random.randint(1, 99)}.jpg",
                f"https://randomuser.me/api/portraits/women/{random.randint(1, 99)}.jpg"
            ]
        else:
            sources = [
                f"https://picsum.photos/1920/1080?random={uuid.uuid4()}",
                "https://picsum.photos/1920/1080"
            ]

        img_bytes = None
        for src in sources:
            try:
                r = self.session.get(src, headers=headers, timeout=15)
                if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image/"):
                    img_bytes = r.content
                    break
            except Exception:
                pass

        if not img_bytes:
            return {"success": False, "message": "Không tải được nguồn ảnh"}

        try:
            if media_type == "avatar":
                r = self.session.post(
                    f"https://graph.facebook.com/v19.0/{page_id}/picture",
                    data={"access_token": page_token},
                    files={"source": ("avatar.jpg", img_bytes, "image/jpeg")},
                    timeout=30
                ).json()
                if "error" in r:
                    return {"success": False, "message": r["error"].get("message", "Lỗi up Avatar")}
                return {"success": True}
            else:
                r1 = self.session.post(
                    f"https://graph.facebook.com/v19.0/{page_id}/photos",
                    data={"published": "false", "access_token": page_token},
                    files={"source": ("cover.jpg", img_bytes, "image/jpeg")},
                    timeout=30
                ).json()
                if "error" in r1 or "id" not in r1:
                    return {"success": False, "message": "Lỗi upload ảnh bìa"}
                r2 = self.session.post(
                    f"https://graph.facebook.com/v19.0/{page_id}",
                    data={"cover": r1["id"], "access_token": page_token},
                    timeout=30
                ).json()
                if "error" in r2:
                    return {"success": False, "message": "Lỗi set ảnh bìa"}
                return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)[:60]}

    def post_welcome(self, page_id: str, page_token: str) -> Dict[str, Any]:
        try:
            payload = {
                "message": "Chào mừng mọi người đến với Page! Hãy ấn theo dõi để cập nhật những thông tin mới nhất nhé!",
                "access_token": page_token
            }
            r = self.session.post(f"https://graph.facebook.com/v19.0/{page_id}/feed", data=payload, timeout=25).json()
            if "error" in r:
                return {"success": False, "message": r["error"].get("message", "Lỗi đăng bài")}
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)[:60]}


# ==============================================================================
# 7. BẢNG THEO DÕI TRỰC TIẾP + KHUNG NHẬT KÝ QUÁ TRÌNH CHI TIẾT
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
        holder_target: Optional[Dict[str, Optional[str]]] = None,
        auto_buff_media: bool = False
    ):
        self.acc_id = acc_id
        self.pre_uid = item.get("uid") or ""
        self.password = item.get("pwd") or default_pwd
        self.twofa = item.get("twofa") or ""
        self.cookie = item.get("cookie") or ""
        self.token = item.get("token") or ""
        self.proxy = item.get("proxy") or assigned_proxy
        self.holder_uid = (holder_target or {}).get("uid") or ""
        self.holder_token = (holder_target or {}).get("token") or None
        self.holder_proxy = (holder_target or {}).get("proxy") or None
        self.target_pages = target_pages
        self.pages_created = 0
        self.ua_mode = ua_mode
        self.auto_buff_media = auto_buff_media
        self.fixed_ua = generate_random_katana_ua(seed=self.token or self.pre_uid) if ua_mode == "fixed" else None
        self.creator: Optional[FbPageCreator] = None
        self.mother_uid = self.pre_uid
        self.mother_name = ""
        self.status = "ready"
        self.current_action = "Chờ đến lượt..."
        self.last_result = ""


def render_dashboard(accounts: List[AccountTask], stats: Dict[str, int]):
    lines = []
    w = 118
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(
        f"{Colors.BOLD}{Colors.YELLOW}"
        f"   BẢNG TIẾN TRÌNH VIP: NẠP ACC -> REG PAGE V5 -> CHECK LIVE -> CHUYỂN PAGE SIÊU MẠNH (NT_BUNDLE_TREE)   "
        f"{Colors.RESET}"
    )
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")
    lines.append(f"{Colors.BOLD} STT | UID Nick Reg     | Tên Nick         | Page Có | Quá trình / Trạng thái hiện tại{Colors.RESET}")
    lines.append("-" * w)

    for acc in accounts:
        stt_str = f"{acc.acc_id:^4}"
        display_uid = (acc.mother_uid or acc.pre_uid or "Unknown")[:16]
        uid_str = f"{display_uid:<16}"
        display_name = (acc.mother_name or "Đang xử lý...")[:16]
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
        f"Chuyển Page OK: {Colors.CYAN}{stats.get('total_invited', 0)}{Colors.RESET}) | "
        f"Xịt/Die Page: {Colors.MAGENTA}{stats.get('total_no_page', 0)}{Colors.RESET} | "
        f"Limit: {Colors.YELLOW}{stats.get('total_limited', 0)}{Colors.RESET} | "
        f"Lỗi Mạng: {Colors.YELLOW}{stats.get('total_net_err', 0)}{Colors.RESET} | "
        f"Acc DIE: {Colors.RED}{stats.get('total_token_die', 0)}{Colors.RESET}"
    )
    lines.append(f"{Colors.BOLD}{Colors.CYAN}" + "=" * w + f"{Colors.RESET}")

    lines.append(f"{Colors.BOLD}{Colors.MAGENTA} 📋 NHẬT KÝ QUÁ TRÌNH CHI TIẾT (LOGIN/CHECK -> TẠO PAGE V5 -> CHECK LIVE -> CHUYỂN PAGE 4 BƯỚC):{Colors.RESET}")
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
# 8. LUỒNG XỬ LÝ CHÍNH CHO TỪNG TÀI KHOẢN (BẢO TOÀN PROFILE_UID 615... & SW_TOKEN)
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

    # --- BƯỚC 0: TỰ ĐỘNG LOGIN BLOKS CAA V5 NẾU CHƯA CÓ TOKEN EAAAAU ---
    if not acc.token:
        acc.current_action = f"[L{thread_id}] Đang tự động Login lấy Token EAAAAU cho UID {acc.pre_uid}..."
        add_process_log(acc.acc_id, acc.pre_uid, "Chưa có sẵn EAAAAU -> Đang tự động Login Bloks CAA v5 để lấy Token...")
        login_res = login_and_get_token({
            "uid": acc.pre_uid,
            "pwd": acc.password,
            "twofa": acc.twofa,
            "cookie": acc.cookie,
            "proxy": acc.proxy
        }, custom_ua=acc.fixed_ua)

        if not login_res.get("success") or not login_res.get("token"):
            acc.status = "die"
            err_l = login_res.get("message", "Không lấy được Token")
            acc.mother_name = "Login Thất Bại"
            acc.current_action = f"Lỗi Login lấy Token: {err_l[:40]}"
            add_process_log(acc.acc_id, acc.pre_uid, f"{Colors.RED}❌ Lỗi Login lấy Token: {err_l}{Colors.RESET}")
            with FILE_LOCK:
                stats["total_token_die"] += 1
                with open("acc_die.txt", "a", encoding="utf-8") as f:
                    f.write(f"{acc.pre_uid}|{acc.password}|LOGIN_FAIL:{err_l}\n")
            return

        acc.token = login_res["token"]
        add_process_log(acc.acc_id, acc.pre_uid, f"{Colors.GREEN}✔ Đã lấy thành công Token EAAAAU ({acc.token[:15]}...){Colors.RESET}")

    acc.creator = FbPageCreator(
        token=acc.token,
        proxy=acc.proxy,
        user_agent=acc.fixed_ua,
        ua_mode=acc.ua_mode
    )

    # --- BƯỚC 1: KIỂM TRA TÀI KHOẢN & QUÉT PAGE CŨ ---
    acc.current_action = f"[L{thread_id}] Bước 1: Đang kiểm tra Tài khoản & quét Page cũ..."
    acc_info = acc.creator.check_account_live(retries=3)

    if not acc_info.get("success"):
        if acc_info.get("is_token_die") and acc.pre_uid and acc.password:
            add_process_log(acc.acc_id, acc.pre_uid, f"{Colors.YELLOW}⚠️ Token cũ hết hạn -> Đang Login lại bằng Pass để lấy Token mới...{Colors.RESET}")
            re_login = login_and_get_token({
                "uid": acc.pre_uid,
                "pwd": acc.password,
                "twofa": acc.twofa,
                "cookie": acc.cookie,
                "proxy": acc.proxy
            }, custom_ua=acc.fixed_ua)
            if re_login.get("success") and re_login.get("token"):
                acc.token = re_login["token"]
                acc.creator = FbPageCreator(token=acc.token, proxy=acc.proxy, user_agent=acc.fixed_ua, ua_mode=acc.ua_mode)
                acc_info = acc.creator.check_account_live(retries=2)

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
        acc.current_action = f"Tài khoản DIE ({err_msg[:35]}) -> Lưu acc_die.txt"
        add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Tài khoản DIE: {err_msg[:45]}{Colors.RESET}")
        with FILE_LOCK:
            stats["total_token_die"] += 1
            with open("acc_die.txt", "a", encoding="utf-8") as f:
                f.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|DIE_TRUOC_KHI_REG\n")
        return

    acc.mother_uid = acc_info.get("uid", acc.pre_uid)
    acc.mother_name = acc_info.get("name", "Facebook User")

    pre_pages_res = acc.creator.get_all_pages_with_tokens()
    known_page_ids = set()
    for p in pre_pages_res.get("pages", []):
        if p.get("id"):
            known_page_ids.add(str(p["id"]))
        if p.get("additional_profile_id"):
            known_page_ids.add(str(p["additional_profile_id"]))

    add_process_log(
        acc.acc_id,
        acc.mother_uid,
        f"{Colors.GREEN}✔ Nick LIVE ({acc.mother_name}) - Có sẵn {len(pre_pages_res.get('pages', []))} Page cũ.{Colors.RESET}"
    )

    # --- BƯỚC 2 & 3: TẠO PAGE PRO5 V5 VÀ GET LUÔN PAGE_TOKEN (SW_TOKEN) + PROFILE_UID (615...) ---
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
                    f.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|DIE_KHI_REG\n")
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
            g_token = create_res.get("graph_token") or p_token
            add_prof_id = create_res.get("additional_profile_id", "") or p_id

            known_page_ids.add(p_id)
            known_page_ids.add(add_prof_id)

            newly_created_pages.append({
                "id": p_id,
                "name": p_name,
                "access_token": p_token,
                "graph_token": g_token,
                "additional_profile_id": add_prof_id
            })
            acc.pages_created = len(newly_created_pages)

            short_ptk = f"{p_token[:16]}..." if p_token else "Chưa cấp riêng"
            acc.current_action = f"[L{thread_id}] Đã tạo Page {p_id} (ProfileUID: {add_prof_id})"
            add_process_log(
                acc.acc_id,
                acc.mother_uid,
                f"{Colors.GREEN}🎉 Tạo thành công Page '{p_name}' (ID: {p_id} | ProfileUID: {add_prof_id}) | Token: {short_ptk}{Colors.RESET}"
            )

            if acc.auto_buff_media and g_token:
                acc.current_action = f"[L{thread_id}] Đang Up Avatar & Ảnh bìa cho Page '{p_name}'..."
                av_res = acc.creator.upload_media(p_id, g_token, "avatar")
                cv_res = acc.creator.upload_media(p_id, g_token, "cover")
                acc.creator.post_welcome(p_id, g_token)
                if av_res.get("success") or cv_res.get("success"):
                    add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.CYAN}🖼️ Đã Up Avatar/Cover & Đăng bài cho Page {p_id}{Colors.RESET}")
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
                    f.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|KHONG_LEN_PAGE\n")
            return

    # --- BƯỚC 4: ĐỢI ĐẾM NGƯỢC & CHECK LIVE LẠI TÀI KHOẢN + PAGE (BẢO TOÀN PROFILE_UID 615...) ---
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
    acc.current_action = f"[L{thread_id}] Đang check LIVE Tài khoản & đồng bộ lại ProfileSwitcher..."

    recheck_acc = acc.creator.check_account_live(retries=2)
    if not recheck_acc.get("success") and recheck_acc.get("is_token_die"):
        acc.status = "die"
        acc.current_action = f"Sau {wait_seconds}s: Tài khoản bị DIE / Checkpoint!"
        add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Sau {wait_seconds}s: Tài khoản bị DIE / Checkpoint!{Colors.RESET}")
        with FILE_LOCK:
            stats["total_token_die"] += 1
            with open("acc_die.txt", "a", encoding="utf-8") as f:
                f.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|DIE_SAU_{wait_seconds}S\n")
        return

    # Quét lại ProfileSwitcher sau 20s để cập nhật sw_token & ProfileUID (615...) mới nhất
    fresh_raw_pages = _fetch_all_pages_raw(acc.token, acc.mother_uid, proxy=acc.proxy)

    live_pages: List[Dict[str, Any]] = []
    for p in newly_created_pages:
        p_id = p["id"]
        p_name_lower = p["name"].strip().lower()
        orig_prof_uid = p.get("additional_profile_id") or p_id

        # Khớp với kết quả ProfileSwitcher mới nhất mà không làm mất ProfileUID 615...
        for sw_item in fresh_raw_pages:
            if (
                sw_item["page_id"] == p_id
                or sw_item["additional_profile_id"] == orig_prof_uid
                or sw_item["name"].strip().lower() == p_name_lower
            ):
                if sw_item.get("access_token"):
                    p["access_token"] = sw_item["access_token"]
                if sw_item.get("additional_profile_id"):
                    p["additional_profile_id"] = sw_item["additional_profile_id"]
                break

        page_live_res = acc.creator.check_single_page_live(page_id=p_id, page_token=p["access_token"])
        if page_live_res.get("success"):
            live_pages.append(p)
            add_process_log(
                acc.acc_id,
                acc.mother_uid,
                f"{Colors.GREEN}✔ Check LIVE thành công: Nick SỐNG & Page {p_id} (ProfileUID: {p['additional_profile_id']}) SỐNG!{Colors.RESET}"
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
                f.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|PAGE_DIE_SAU_{wait_seconds}S\n")
        return

    # --- BƯỚC 5: CHUYỂN PAGE SIÊU MẠNH (DÙNG ĐÚNG PROFILE_UID 615... & SW_TOKEN) ---
    acc.pages_created = len(live_pages)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page_summary_list = []
    transfer_note = "Đã lưu Page & Token vào acc_cam_page.txt"

    for p in live_pages:
        p_id = str(p["id"])
        p_name = str(p["name"])
        p_token = str(p["access_token"])
        p_uid = str(p.get("additional_profile_id") or p_id)
        page_summary_list.append(f"{p_id}:{p_name}")

        if acc.holder_uid or acc.holder_token:
            def super_cb(msg_step: str):
                acc.current_action = f"[L{thread_id}] {msg_step}"
                add_process_log(acc.acc_id, acc.mother_uid, f"🚀 {msg_step}")

            tr_res = execute_super_transfer(
                page_uid=p_uid,
                page_id=p_id,
                page_token=p_token,
                sender_token=acc.token,
                password=acc.password,
                target_uid=acc.holder_uid,
                receiver_token=acc.holder_token,
                sender_proxy=acc.proxy,
                receiver_proxy=acc.holder_proxy,
                step_callback=super_cb
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
            p_uid = str(p.get("additional_profile_id") or p_id)
            p_name = str(p["name"])
            p_token = str(p["access_token"])
            if p.get("transfer_ok"):
                stats["total_invited"] += 1

            with open("created_pages.txt", "a", encoding="utf-8") as f_page:
                f_page.write(f"{p_id}|{p_uid}|{p_name}|{p_token}|{acc.mother_uid}|{acc.password}|{now_str}\n")

            with open("acc_cam_page.txt", "a", encoding="utf-8") as f_holder:
                if acc.holder_uid or acc.holder_token:
                    st_code = p.get("transfer_status", "")
                    inv_id = p.get("invitation_id") or ""
                    tr_tag = f"{st_code}:{acc.holder_uid}" + (f"(InviteID:{inv_id})" if inv_id else "")
                    f_holder.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|{p_id}|{p_uid}|{p_name}|{p_token}|{tr_tag}|{now_str}\n")
                else:
                    f_holder.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|{p_id}|{p_uid}|{p_name}|{p_token}|PAGE_LIVE|{now_str}\n")

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
# 9. MENU [1]: REG PAGE VIP V5 -> CHECK LIVE -> CHUYỂN PAGE SIÊU MẠNH 4 BƯỚC
# ==============================================================================

def run_reg_page_menu():
    print_banner()
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== [1] REG PAGE VIP V5 -> CHECK LIVE -> CHUYỂN PAGE SIÊU MẠNH (NT_BUNDLE_TREE) ==={Colors.RESET}\n")

    safe_print(f"{Colors.CYAN}--- [1/8] NẠP DANH SÁCH ACC NGUỒN (NHẬN MỌI BIẾN THỂ ĐỊNH DẠNG) ---{Colors.RESET}")
    safe_print("Hỗ trợ: UID|Pass|Cookie|Token, UID|Pass|Token, UID|Pass|Cookie, UID|Pass|2FA, hoặc chỉ Token")
    safe_print("[1] Dán trực tiếp vào màn hình (tự động bóc tách)")
    safe_print("[2] Đọc từ file (mặc định tokens.txt hoặc accounts.txt)")
    c_tok = input("Chọn cách nạp (1 hoặc 2, mặc định 1): ").strip() or "1"

    raw_lines = []
    if c_tok == "1":
        raw_lines = input_multiline("Hãy dán danh sách Acc / Token vào đây:")
    else:
        fn = input("Nhập tên file (mặc định tokens.txt): ").strip() or "tokens.txt"
        if os.path.exists(fn):
            with open(fn, "r", encoding="utf-8", errors="ignore") as f:
                raw_lines = [l.strip() for l in f if l.strip()]
        else:
            safe_print(f"{Colors.RED}Không tìm thấy file {fn}!{Colors.RESET}")
            input("\nNhấn Enter để quay lại...")
            return

    parsed_items = parse_universal_lines(raw_lines)
    if not parsed_items:
        safe_print(f"{Colors.RED}Không tìm thấy dữ liệu Acc hoặc Token hợp lệ!{Colors.RESET}")
        input("\nNhấn Enter để quay lại...")
        return

    has_tk_count = sum(1 for it in parsed_items if it.get("token"))
    has_pwd_count = sum(1 for it in parsed_items if it.get("pwd"))
    safe_print(
        f"{Colors.GREEN}{Colors.BOLD}✔ Đã nhận diện: {len(parsed_items)} Acc hợp lệ! "
        f"(Có sẵn Token: {has_tk_count} | Có sẵn Mật khẩu: {has_pwd_count} | Cần tự Login lấy Token: {len(parsed_items) - has_tk_count}){Colors.RESET}\n"
    )

    # 2. Cấu hình Nick Mẹ nhận Page
    safe_print(f"{Colors.CYAN}--- [2/8] CẤU HÌNH TÀI KHOẢN ĐÍCH (NICK MẸ NHẬN PAGE) ---{Colors.RESET}")
    safe_print("- Nhập TOKEN Nick Mẹ (EAAAAU...) hoặc dòng UID|Pass|Cookie|Token_Mẹ -> Chạy FULL 4 BƯỚC (Auto Accept)")
    safe_print("- Nhập chỉ UID_ME (VD: 100012345678)                                -> Chạy Bước 1 + Bước 2 (Gửi lời mời)")
    safe_print("- Để trống và nhấn Enter                                            -> Chỉ tạo Page và lưu file.")
    h_raw = input("Nhập Token (hoặc UID) Nick Mẹ nhận Page: ").strip()

    holder_targets = parse_holder_target(h_raw)
    valid_targets = []
    for t in holder_targets:
        if t.get("token") and not t.get("uid"):
            info_nhan = get_id(t["token"], proxy=t.get("proxy"))
            if info_nhan:
                t["uid"], t_name = info_nhan
                safe_print(f"{Colors.GREEN}✔ Đã xác thực Token Nick Mẹ: {t_name} (ID: {t['uid']}) -> Bật Auto Accept Full 4 Bước!{Colors.RESET}")
                valid_targets.append(t)
            else:
                safe_print(f"{Colors.RED}✗ Token Nick Mẹ không hợp lệ hoặc đã DIE!{Colors.RESET}")
        elif t.get("uid"):
            if t.get("token"):
                info_nhan = get_id(t["token"], proxy=t.get("proxy"))
                t_name = info_nhan[1] if info_nhan else "Nick Mẹ"
                safe_print(f"{Colors.GREEN}✔ Đã nhận diện Nick Mẹ: {t_name} (ID: {t['uid']}) -> Bật Auto Accept Full 4 Bước!{Colors.RESET}")
            else:
                safe_print(f"{Colors.GREEN}✔ Đã nhận diện UID Nick Mẹ: {t['uid']} -> Chế độ bắn lời mời Bước 1 & 2.{Colors.RESET}")
            valid_targets.append(t)

    holder_targets = valid_targets
    default_pwd = ""

    if holder_targets:
        if has_pwd_count < len(parsed_items):
            safe_print(f"{Colors.YELLOW}Lưu ý: Bước 1 (xac_nhan_mk) bắt buộc phải có mật khẩu của Nick Reg để lấy nt_bundle_tree.{Colors.RESET}")
            default_pwd = input("Nhập Mật khẩu mặc định cho các Acc chưa kèm pass (Enter nếu bỏ qua): ").strip()
        safe_print("")
    else:
        safe_print(f"{Colors.YELLOW}Không cấu hình Nick Mẹ -> Chỉ tạo Page, Get Token Page và lưu vào acc_cam_page.txt.{Colors.RESET}\n")

    # 3. Tên Page
    safe_print(f"{Colors.CYAN}--- [3/8] CHỌN LOẠI TÊN PAGE ---{Colors.RESET}")
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
    safe_print("")

    # 4. Tự động Up Avatar/Cover/Post
    safe_print(f"{Colors.CYAN}--- [4/8] TỰ ĐỘNG UP AVATAR, ẢNH BÌA & BÀI ĐĂNG CHO PAGE MỚI ---{Colors.RESET}")
    buff_choice = input("Có tự động Up Avatar + Ảnh bìa + Đăng bài Welcome sau khi tạo Page không? (y/n, mặc định n): ").strip().lower()
    auto_buff_media = (buff_choice == "y")
    safe_print("")

    # 5. User-Agent
    safe_print(f"{Colors.CYAN}--- [5/8] CƠ CHẾ USER-AGENT (KATANA ANDROID) ---{Colors.RESET}")
    safe_print("[1] Cố định 1 UA cho mỗi nick [Khuyên dùng]")
    safe_print("[2] Random UA mới mỗi lần tạo Page")
    c_ua = input("Chọn cơ chế UA (1 hoặc 2, mặc định 1): ").strip() or "1"
    ua_mode = "random" if c_ua == "2" else "fixed"
    safe_print("")

    # 6. Proxy
    safe_print(f"{Colors.CYAN}--- [6/8] CẤU HÌNH PROXY ---{Colors.RESET}")
    global_proxies = []
    has_attached = any(it.get("proxy") for it in parsed_items)

    if has_attached:
        safe_print(f"{Colors.GREEN}Phát hiện các Acc đã có Proxy hợp lệ gắn kèm riêng.{Colors.RESET}\n")
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
            safe_print(f"{Colors.YELLOW}Chạy trực tiếp mạng máy tính / 4G.{Colors.RESET}\n")

    # 7. Số page & Thời gian đợi check Live
    safe_print(f"{Colors.CYAN}--- [7/8] SỐ PAGE TRÊN 1 ACC & THỜI GIAN ĐỢI CHECK LIVE ACC + PAGE ---{Colors.RESET}")
    try:
        pages_per_nick = int(input("Số lượng Page muốn reg trên 1 Acc (Mặc định 1): ").strip() or "1")
    except ValueError:
        pages_per_nick = 1

    try:
        verify_delay = int(input("Sau khi tạo Page xong, đợi bao nhiêu giây để check lại Acc & Page sống/chết? (Mặc định 20): ").strip() or "20")
    except ValueError:
        verify_delay = 20

    delay_between = 5
    if pages_per_nick > 1:
        try:
            delay_between = int(input("Thời gian nghỉ giữa các Page trong cùng 1 Acc (giây, mặc định 5): ").strip() or "5")
        except ValueError:
            delay_between = 5
    safe_print("")

    # 8. Luồng
    safe_print(f"{Colors.CYAN}--- [8/8] SỐ LUỒNG CHẠY SONG SONG ---{Colors.RESET}")
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
            holder_target=assigned_target,
            auto_buff_media=auto_buff_media
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

    safe_print("\n" + "=" * 100)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT TIẾN TRÌNH!{Colors.RESET}")
    safe_print(f"- Số Acc sống & có Page sống sau {verify_delay}s: {Colors.GREEN}{stats['total_holder_acc']} Acc ({stats['total_pages']} Page){Colors.RESET}")
    safe_print(f"- Số Page đã chuyển / gửi lời mời thành công sang Nick Mẹ: {Colors.CYAN}{stats['total_invited']} Page{Colors.RESET}")
    safe_print(f"- Số Acc không lên Page hoặc Page bị hủy đăng: {Colors.MAGENTA}{stats['total_no_page']}{Colors.RESET}")
    safe_print(f"- Số Acc gặp Limit: {Colors.YELLOW}{stats['total_limited']}{Colors.RESET}")
    safe_print(f"- Số Acc gặp lỗi Mạng/Proxy (đã bảo toàn, không ghi vào acc_die): {Colors.YELLOW}{stats['total_net_err']}{Colors.RESET}")
    safe_print(f"- Số Acc bị Token DIE / Checkpoint: {Colors.RED}{stats['total_token_die']}{Colors.RESET}")
    safe_print(f"- File lưu đầy đủ (UID|Pass|Token|PageID|ProfileUID|PageName|PageToken|TrạngThái): {Colors.CYAN}acc_cam_page.txt{Colors.RESET}")
    safe_print(f"- File lưu danh sách Page riêng: {Colors.CYAN}created_pages.txt{Colors.RESET}")
    safe_print(f"- File nhật ký chi tiết chuyển Page: {Colors.CYAN}transfer_page.log{Colors.RESET}")
    safe_print("=" * 100 + "\n")
    input("Nhấn Enter để quay lại menu chính...")


# ==============================================================================
# 10. MENU [2]: CÔNG CỤ CHUYỂN QUYỀN QUẢN TRỊ PAGE SIÊU MẠNH (CHẾ ĐỘ ĐỘC LẬP)
# ==============================================================================

def setup_source_account_interactive(account_index: int, allow_cancel: bool = True) -> Optional[Dict[str, Any]]:
    safe_print(f"\n{Colors.BLUE}===== TÀI KHOẢN NGUỒN {account_index} ====={Colors.RESET}")
    if allow_cancel:
        safe_print("(Nhấn Enter để bỏ trống và kết thúc nhập tài khoản nguồn)")

    while True:
        raw_in = input(f"Nhập Token (hoặc dòng UID|Pass|Cookie|Token) của tài khoản nguồn {account_index}: ").strip()
        if not raw_in:
            if allow_cancel:
                return None
            safe_print("Dữ liệu không được để trống.")
            continue

        parsed = parse_universal_line(raw_in)
        token_acc_page = parsed["token"] if parsed and parsed.get("token") else raw_in
        pwd_parsed = parsed.get("pwd", "") if parsed else ""
        px_parsed = parsed.get("proxy") if parsed else None

        if not token_acc_page.startswith("EAAAA") and parsed and parsed.get("uid") and parsed.get("pwd"):
            safe_print(f"{Colors.YELLOW}Đang tự động Login lấy Token cho UID {parsed['uid']}...{Colors.RESET}")
            l_res = login_and_get_token(parsed)
            if l_res.get("success"):
                token_acc_page = l_res["token"]

        info = get_id(token_acc_page, proxy=px_parsed)
        if info is None:
            safe_print(f"{Colors.RED}✗ Token không hợp lệ hoặc không lấy được thông tin tài khoản. Vui lòng nhập lại.{Colors.RESET}")
            continue

        id_acc, name_acc = info
        safe_print(f"{Colors.GREEN}✓ Tài khoản nguồn {account_index}: {name_acc} (ID: {id_acc}){Colors.RESET}")
        break

    while True:
        safe_print(f"\nĐang lấy danh sách Page của tài khoản nguồn {account_index}...")
        selected_pages = get_token_pages(token_acc_page, id_acc, proxy=px_parsed)
        if selected_pages:
            break
        retry = input(
            f"\n{Colors.YELLOW}! Không có Page nào được chọn cho tài khoản nguồn {account_index}.{Colors.RESET}\n"
            f"  Nhập 'r' để thử lại, 't' để đổi token khác, hoặc 'q' để hủy: "
        ).strip().lower()
        if retry == "q":
            return None
        if retry == "t":
            return setup_source_account_interactive(account_index, allow_cancel=allow_cancel)

    if pwd_parsed:
        safe_print(f"{Colors.GREEN}✓ Đã tự động nhận mật khẩu từ dòng nhập: {pwd_parsed}{Colors.RESET}")
        mk = pwd_parsed
    else:
        mk = input(f"\nNhập mật khẩu của tài khoản nguồn {account_index}: ").strip()

    return {
        "index": account_index,
        "id": id_acc,
        "name": name_acc,
        "token": token_acc_page,
        "password": mk,
        "proxy": px_parsed,
        "pages": selected_pages
    }


def setup_source_from_universal_lines(lines: List[str]) -> List[Dict[str, Any]]:
    creds = parse_universal_lines(lines)
    if not creds:
        safe_print(f"{Colors.RED}✗ Không tìm thấy tài khoản hợp lệ nào.{Colors.RESET}")
        return []

    safe_print(f"\n{Colors.CYAN}→ Bắt đầu quét Page trên {len(creds)} tài khoản nguồn...{Colors.RESET}")
    accounts: List[Dict[str, Any]] = []

    for i, cred in enumerate(creds, 1):
        token = cred.get("token", "")
        password = cred.get("pwd", "")
        uid_file = cred.get("uid", "")
        px = cred.get("proxy")

        safe_print(f"\n{Colors.BLUE}--- Tài khoản nguồn #{i} (UID: {uid_file or 'Unknown'}) ---{Colors.RESET}")

        if not token and uid_file and password:
            safe_print(f"  {Colors.YELLOW}Chưa có sẵn Token EAAAAU -> Đang tự động Login Bloks CAA v5...{Colors.RESET}")
            l_res = login_and_get_token(cred)
            if l_res.get("success"):
                token = l_res["token"]
                safe_print(f"  {Colors.GREEN}✓ Đã lấy được Token EAAAAU mới!{Colors.RESET}")
            else:
                safe_print(f"  {Colors.RED}✗ Lỗi Login lấy Token: {l_res.get('message')} -> Bỏ qua.{Colors.RESET}")
                continue

        info = get_id(token, proxy=px)
        if info is None and uid_file and password:
            safe_print(f"  {Colors.YELLOW}! Token cũ không verify được -> Thử Login lại bằng mật khẩu...{Colors.RESET}")
            l_res = login_and_get_token(cred)
            if l_res.get("success"):
                token = l_res["token"]
                info = get_id(token, proxy=px)

        if info is None:
            if not uid_file:
                safe_print(f"  {Colors.RED}✗ Token DIE và không có UID -> Bỏ qua.{Colors.RESET}")
                continue
            safe_print(f"  {Colors.YELLOW}! Token không verify được qua /me — dùng UID từ dữ liệu: {uid_file}{Colors.RESET}")
            id_acc = str(uid_file)
            name_acc = f"(unknown - uid {uid_file})"
        else:
            id_acc_api, name_acc = info
            id_acc = str(uid_file or id_acc_api)
            safe_print(f"  {Colors.GREEN}✓ Tài khoản: {name_acc} (UID: {id_acc}){Colors.RESET}")

        safe_print("  Đang lấy tất cả Page (ProfileSwitcherQuery + Graph API v24.0)...")
        all_pages = get_all_pages(token, id_acc, proxy=px)
        if not all_pages:
            safe_print(f"  {Colors.YELLOW}! Tài khoản UID {id_acc} không có Page nào. Bỏ qua.{Colors.RESET}")
            continue

        safe_print(f"  {Colors.GREEN}→ Tìm thấy {len(all_pages)} Page. Sẽ chuyển TẤT CẢ {len(all_pages)} Page.{Colors.RESET}")
        accounts.append({
            "index": i,
            "id": id_acc,
            "name": name_acc,
            "token": token,
            "password": password,
            "proxy": px,
            "pages": all_pages
        })

    return accounts


def run_standalone_super_transfer_menu():
    print_banner()
    safe_print(f"{Colors.GREEN}{Colors.BOLD}=== [2] CÔNG CỤ CHUYỂN QUYỀN QUẢN TRỊ PAGE SIÊU MẠNH (FULL 4 BƯỚC NT_BUNDLE_TREE) ==={Colors.RESET}\n")

    # ===== BƯỚC 1: NHẬP TÀI KHOẢN NHẬN PAGE =====
    safe_print(f"{Colors.BLUE}===== BƯỚC 1: TÀI KHOẢN NHẬN PAGE (NICK MẸ) ====={Colors.RESET}")
    token_nhan = ""
    id_acc_nhan = ""
    name_acc_nhan = ""

    while True:
        raw_nhan = input("Nhập Token (hoặc UID|Pass|Cookie|Token) của tài khoản nhận Page: ").strip()
        if not raw_nhan:
            safe_print("Token nhận không được để trống.")
            continue

        parsed_nhan = parse_universal_line(raw_nhan)
        token_nhan = parsed_nhan["token"] if parsed_nhan and parsed_nhan.get("token") else raw_nhan
        if not token_nhan.startswith("EAAAA") and parsed_nhan and parsed_nhan.get("uid") and parsed_nhan.get("pwd"):
            l_res = login_and_get_token(parsed_nhan)
            if l_res.get("success"):
                token_nhan = l_res["token"]

        info_nhan = get_id(token_nhan)
        if info_nhan is None:
            safe_print(f"{Colors.RED}✗ Token không hợp lệ hoặc không lấy được thông tin tài khoản nhận. Vui lòng nhập lại.{Colors.RESET}")
            continue

        id_acc_nhan, name_acc_nhan = info_nhan
        safe_print(f"{Colors.GREEN}✓ Tài khoản đích: {name_acc_nhan} (ID: {id_acc_nhan}){Colors.RESET}")
        break

    logger.info("Đang kiểm tra danh sách Page mà tài khoản đích đang quản lý...")
    target_page_ids = get_managed_page_ids(token_nhan)
    if target_page_ids:
        safe_print(f"{Colors.GREEN}✓ Tài khoản đích đang quản lý {len(target_page_ids)} Page (Sẽ tự động bỏ qua các Page đã có quyền).{Colors.RESET}")
    else:
        safe_print(f"{Colors.YELLOW}! Tài khoản đích hiện chưa quản lý Page nào (hoặc không bỏ qua Page nào).{Colors.RESET}")

    # ===== BƯỚC 2: THIẾT LẬP CÁC TÀI KHOẢN NGUỒN =====
    safe_print(f"\n{Colors.BLUE}===== BƯỚC 2: THIẾT LẬP TÀI KHOẢN NGUỒN (ACC CẦM PAGE) ====={Colors.RESET}")
    safe_print("Chọn phương thức nhập tài khoản nguồn:")
    safe_print(f"  {Colors.YELLOW}[1]{Colors.RESET} Nhập thủ công từng Acc/Token & tự chọn Page (1-5, 1,3,5, all)")
    safe_print(f"  {Colors.YELLOW}[2]{Colors.RESET} Dán trực tiếp nhiều dòng (UID|Pass|Cookie|Token, UID|Pass|Token...) — tự chuyển TẤT CẢ Page")
    safe_print(f"  {Colors.YELLOW}[3]{Colors.RESET} Đọc từ file (hỗ trợ mọi định dạng uid|pass|token / acc_cam_page.txt) — tự chuyển TẤT CẢ Page")

    while True:
        mode = input("Lựa chọn (1/2/3, mặc định 2): ").strip() or "2"
        if mode in ("1", "2", "3"):
            break
        safe_print("Vui lòng nhập 1, 2 hoặc 3.")

    source_accounts: List[Dict[str, Any]] = []

    if mode == "2":
        raw_lines = input_multiline("Dán danh sách tài khoản nguồn vào đây:")
        source_accounts = setup_source_from_universal_lines(raw_lines)
    elif mode == "3":
        while True:
            filepath = input("Nhập đường dẫn file tài khoản nguồn (mặc định acc_cam_page.txt): ").strip().strip('"').strip("'") or "acc_cam_page.txt"
            if not os.path.isfile(filepath):
                safe_print(f"{Colors.RED}✗ File không tồn tại: {filepath}{Colors.RESET}")
                continue
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                raw_lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
            source_accounts = setup_source_from_universal_lines(raw_lines)
            if source_accounts:
                break
            retry_f = input("Không đọc được tài khoản nào có Page. Nhập 'q' để quay lại hoặc Enter để chọn file khác: ").strip().lower()
            if retry_f == "q":
                return
    else:
        safe_print(f"Nhập từng tài khoản nguồn. {Colors.YELLOW}Nhấn Enter (bỏ trống) để kết thúc nhập.{Colors.RESET}")
        idx = 1
        while True:
            acc = setup_source_account_interactive(idx, allow_cancel=True)
            if acc is None:
                if idx == 1:
                    safe_print(f"{Colors.RED}! Cần ít nhất 1 tài khoản nguồn để chuyển.{Colors.RESET}")
                    input("\nNhấn Enter để quay lại...")
                    return
                safe_print(f"\n{Colors.GREEN}✓ Đã nhập xong {len(source_accounts)} tài khoản nguồn.{Colors.RESET}")
                break
            source_accounts.append(acc)
            safe_print(f"{Colors.GREEN}✓ Đã thiết lập tài khoản nguồn {idx}: {acc['name']} với {len(acc['pages'])} Page.{Colors.RESET}")
            idx += 1

    if not source_accounts:
        safe_print(f"{Colors.RED}! Không có tài khoản nguồn nào có Page để xử lý.{Colors.RESET}")
        input("\nNhấn Enter để quay lại...")
        return

    missing_pwd = any(not a.get("password") for a in source_accounts)
    if missing_pwd:
        default_mk = input(f"\n{Colors.YELLOW}Phát hiện có Acc nguồn chưa kèm mật khẩu. Nhập mật khẩu chung cho các Acc đó: {Colors.RESET}").strip()
        for a in source_accounts:
            if not a.get("password"):
                a["password"] = default_mk

    # ===== BƯỚC 3: NHẬP DELAY =====
    while True:
        delay_str = input("\nNhập số giây delay giữa các lần chuyển Page (mặc định 2, nhập 0 để không delay): ").strip() or "2"
        try:
            delay = float(delay_str)
            if delay >= 0:
                break
        except ValueError:
            pass
        safe_print("Vui lòng nhập số >= 0.")

    # ===== BƯỚC 4: BẮT ĐẦU CHUYỂN =====
    total = sum(len(acc["pages"]) for acc in source_accounts)
    safe_print(f"\n{Colors.GREEN}{Colors.BOLD}===== BẮT ĐẦU CHUYỂN {total} PAGE TỪ {len(source_accounts)} TÀI KHOẢN NGUỒN ====={Colors.RESET}")

    success_count = 0
    fail_count = 0
    skip_count = 0
    processed = 0

    for acc in source_accounts:
        id_acc_src = acc["id"]
        name_acc_src = acc["name"]
        mk = acc["password"]
        src_token = acc.get("token", "")
        src_proxy = acc.get("proxy")

        safe_print(f"\n{Colors.CYAN}--- Tài khoản nguồn: {name_acc_src} (UID: {id_acc_src}) ---{Colors.RESET}")

        for page in acc["pages"]:
            processed += 1
            page_uid = page["page_uid"]
            page_token = page["page_token"]
            page_name = page["page_name"]
            page_id = page["page_id"]

            safe_print(f"\n[{processed}/{total}] Đang xử lý: {Colors.BOLD}{page_name}{Colors.RESET} (Page ID: {page_id} | ProfileUID: {page_uid})")
            logger.info(f"===== [{processed}/{total}] Xử lý Page: {page_name} (ID: {page_id} | ProfileUID: {page_uid}) từ nguồn {name_acc_src} =====")

            if page_id in target_page_ids or page_uid in target_page_ids:
                msg = f"⏭️  Page {page_name}: Tài khoản đích đã có quyền quản trị, bỏ qua."
                safe_print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
                logger.info(msg)
                skip_count += 1
                if processed < total:
                    sleep_with_countdown(delay)
                continue

            tr_res = execute_super_transfer(
                page_uid=page_uid,
                page_id=page_id,
                page_token=page_token,
                sender_token=src_token,
                password=mk,
                target_uid=id_acc_nhan,
                receiver_token=token_nhan,
                sender_proxy=src_proxy,
                step_callback=lambda m: safe_print(f"  {Colors.CYAN}→ {m}{Colors.RESET}")
            )

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if tr_res.get("status") == "SUCCESS":
                msg = f"✅ Page {page_name}: Chuyển quyền & Auto Accept thành công!"
                safe_print(f"{Colors.GREEN}{Colors.BOLD}{msg}{Colors.RESET}")
                logger.info(msg)
                success_count += 1
                target_page_ids.add(page_id)
                target_page_ids.add(page_uid)
                with open("output_chuyen_page.txt", "a", encoding="utf-8") as f:
                    f.write(f"{now_str}|SUCCESS|{page_id}|{page_uid}|{page_name}|From:{id_acc_src}|To:{id_acc_nhan}\n")
            elif tr_res.get("status") == "INVITED_ONLY":
                msg = f"⚠️ Page {page_name}: {tr_res.get('message')}"
                safe_print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
                logger.warning(msg)
                fail_count += 1
                with open("output_chuyen_page.txt", "a", encoding="utf-8") as f:
                    f.write(f"{now_str}|INVITED_ONLY|{page_id}|{page_uid}|{page_name}|From:{id_acc_src}|To:{id_acc_nhan}|{tr_res.get('message')}\n")
            else:
                msg = f"❌ Page {page_name}: {tr_res.get('message')}"
                safe_print(f"{Colors.RED}{msg}{Colors.RESET}")
                logger.error(msg)
                fail_count += 1

            if processed < total:
                sleep_with_countdown(delay)

    safe_print(f"\n{Colors.GREEN}{Colors.BOLD}===== KẾT QUẢ TỔNG KẾT ====={Colors.RESET}")
    safe_print(f"- Tổng số tài khoản nguồn: {len(source_accounts)}")
    safe_print(f"- Thành công (Full Admin): {Colors.GREEN}{success_count} Page{Colors.RESET}")
    safe_print(f"- Thất bại / Chưa nhận:    {Colors.RED}{fail_count} Page{Colors.RESET}")
    safe_print(f"- Bỏ qua (đã có quyền):    {Colors.YELLOW}{skip_count} Page{Colors.RESET}")
    safe_print(f"- File kết quả:            {Colors.CYAN}output_chuyen_page.txt{Colors.RESET}")
    safe_print(f"- File log chi tiết:       {Colors.CYAN}transfer_page.log{Colors.RESET}")
    input("\nNhấn Enter để quay lại menu chính...")


# ==============================================================================
# 11. MENU [3]: GET TOKEN EAAAAU TỪ MỌI ĐỊNH DẠNG ACC (BLOKS CAA V5)
# ==============================================================================

def worker_get_token(thread_id: int, queue: Queue, stats: Dict[str, int]):
    while True:
        try:
            acc = queue.get(timeout=2.0)
        except Empty:
            break

        uid = acc.get("uid", "")
        pwd = acc.get("pwd", "")
        cookie = acc.get("cookie", "")
        proxy = acc.get("proxy", "")
        safe_print(f"{Colors.CYAN}[Luồng {thread_id}] Đang lấy Token EAAAAU cho UID: {uid}...{Colors.RESET}")

        res = login_and_get_token(acc)

        if res.get("success"):
            token = res.get("token", "")
            new_ck = res.get("cookie") or cookie
            safe_print(f"{Colors.GREEN}{Colors.BOLD}[Luồng {thread_id}] [THÀNH CÔNG] UID: {uid} -> {token[:28]}...{Colors.RESET}")

            with FILE_LOCK:
                with open("tokens_eaaau.txt", "a", encoding="utf-8") as f:
                    line_out = f"{uid}|{pwd}"
                    if new_ck:
                        line_out += f"|{new_ck}"
                    line_out += f"|{token}"
                    if proxy:
                        line_out += f"|{proxy}"
                    f.write(line_out + "\n")
                stats["success"] += 1
        else:
            safe_print(f"{Colors.RED}[Luồng {thread_id}] [LỖI] UID: {uid} -> {res.get('message')}{Colors.RESET}")
            with FILE_LOCK:
                stats["fail"] += 1

        queue.task_done()


def run_get_token_menu():
    print_banner()
    safe_print(f"{Colors.BOLD}{Colors.MAGENTA}=== [3] GET TOKEN EAAAAU TỪ ACC (BLOKS CAA V5 - HỖ TRỢ UID|PASS|COOKIE / 2FA) ==={Colors.RESET}\n")

    raw_lines = input_multiline("Dán danh sách tài khoản (UID|Pass|Cookie hoặc UID|Pass|2FA):")
    acc_list = parse_universal_lines(raw_lines)
    if not acc_list:
        safe_print(f"{Colors.RED}Không tìm thấy tài khoản nào hợp lệ!{Colors.RESET}")
        input("\nNhấn Enter để quay lại...")
        return

    safe_print(f"{Colors.GREEN}Đã nhận diện: {len(acc_list)} tài khoản!{Colors.RESET}")
    try:
        threads = int(input(f"Số luồng (Mặc định {min(3, len(acc_list))}): ").strip() or str(min(3, len(acc_list))))
    except ValueError:
        threads = 3
    threads = max(1, min(threads, 20))

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

    safe_print("\n" + "=" * 100)
    safe_print(f"{Colors.GREEN}{Colors.BOLD} HOÀN TẤT LẤY TOKEN EAAAAU!{Colors.RESET}")
    safe_print(f"- Thành công: {Colors.GREEN}{stats['success']}{Colors.RESET} | Thất bại: {Colors.RED}{stats['fail']}{Colors.RESET}")
    safe_print(f"- File lưu (UID|Pass|Cookie|Token): {Colors.CYAN}tokens_eaaau.txt{Colors.RESET}")
    safe_print("=" * 100 + "\n")
    input("Nhấn Enter để quay lại menu chính...")


def main():
    while True:
        print_banner()
        safe_print(f"{Colors.BOLD}VUI LÒNG CHỌN CHỨC NĂNG:{Colors.RESET}")
        safe_print(f"{Colors.GREEN}[1] REG PAGE PRO5 VIP (CORE V5) -> CHECK LIVE -> CHUYỂN PAGE SIÊU MẠNH (NT_BUNDLE_TREE){Colors.RESET}")
        safe_print(f"{Colors.CYAN}[2] CHUYỂN QUYỀN QUẢN TRỊ PAGE SIÊU MẠNH ĐỘC LẬP (CHỌN PAGE 1-5, ALL / ĐỌC FILE){Colors.RESET}")
        safe_print(f"{Colors.YELLOW}[3] GET TOKEN EAAAAU TỪ UID|PASS|COOKIE / 2FA (BLOKS CAA V5){Colors.RESET}")
        safe_print(f"{Colors.RED}[0] THOÁT TOOL{Colors.RESET}\n")

        choice = input("Nhập lựa chọn của bạn (0 - 3): ").strip()

        if choice == "1":
            run_reg_page_menu()
        elif choice == "2":
            run_standalone_super_transfer_menu()
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
