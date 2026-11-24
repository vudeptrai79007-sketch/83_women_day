#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
TOOL REG PAGE PRO5 VIP (CORE V5) + CHUYỂN PAGE SIÊU MẠNH (BẢN TÍCH HỢP GUI)
- Đầu vào đa năng: Nhận mọi biến thể (UID|Pass|Cookie|Token, UID|Pass|Token,
  UID|Pass|Cookie, UID|Pass|2FA, Token|Proxy...).
- Tự động Login Bloks CAA v5 lấy Token EAAAAU nếu dòng acc chưa có sẵn Token.
- Luồng cuốn chiếu thông minh:
    Tạo xong Page nào -> Đợi Check Live Page đó -> Đồng bộ ProfileUID (615...)
    & sw_token từ ProfileSwitcherQuery -> Up Cover & Up Avatar 2 bước chuẩn Pro5
    -> Chuyển luôn sang Nick Mẹ (Full 4 Bước nt_bundle_tree & Auto Accept)!
- Giao diện điều khiển CustomTkinter Dark Mode 3 Tab (1 file duy nhất).
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
import subprocess
import urllib.parse
from collections import deque
from queue import Queue, Empty
from typing import Optional, Dict, Any, List, Tuple, Set

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import requests
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    print("Vui lòng cài đặt requests bằng lệnh: pip install requests")
    sys.exit(1)

try:
    import customtkinter as ctk
except ImportError:
    print("Vui lòng cài đặt customtkinter bằng lệnh: pip install customtkinter")
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


if sys.platform == "win32" and sys.stdout is not None:
    os.system("color")

PRINT_LOCK = threading.Lock()
FILE_LOCK = threading.Lock()
LOG_LOCK = threading.Lock()

LIVE_PROCESS_LOGS = deque(maxlen=18)
GUI_LOG_QUEUE: "Queue[Tuple[str, str]]" = Queue()


def safe_print(msg: str):
    with PRINT_LOCK:
        if sys.stdout is not None:
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

    tag = "info"
    if "\033[92m" in msg or "✅" in msg or "✔" in msg or "🎉" in msg:
        tag = "success"
    elif "\033[91m" in msg or "❌" in msg:
        tag = "error"
    elif "\033[93m" in msg or "⚠️" in msg or "🚫" in msg or "⏳" in msg:
        tag = "warn"
    elif "\033[96m" in msg or "🚀" in msg or "🖼️" in msg or "🔄" in msg:
        tag = "cyan"
    GUI_LOG_QUEUE.put((f"{clean_log}\n", tag))


def clear_screen():
    os.system("cls" if sys.platform == "win32" else "clear")


def print_banner():
    clear_screen()
    safe_print(f"{Colors.CYAN}{Colors.BOLD}")
    safe_print("=" * 102)
    safe_print("   TOOL REG PAGE PRO5 VIP (V5) + CHUYỂN PAGE SIÊU MẠNH (REG XONG PAGE NÀO CHUYỂN LUÔN PAGE ĐÓ)   ")
    safe_print("    Đầu Vào Đa Năng (UID|Pass|Cookie|Token) | Chuẩn ProfileUID 615... & Dynamic nt_bundle_tree    ")
    safe_print("=" * 102)
    safe_print(f"{Colors.RESET}")


def input_multiline(prompt: str) -> List[str]:
    safe_print(prompt)
    safe_print(f"{Colors.YELLOW}(Dán danh sách vào đây. Dán xong nhấn Enter ở dòng trống để xác nhận):{Colors.RESET}")
    lines = []
    while True:
        try:
            line = input()
            if not line.strip():
                if lines:
                    break
            else:
                lines.append(line.strip())
        except (EOFError, KeyboardInterrupt):
            break
    return lines


def sleep_with_countdown(seconds: float):
    if seconds <= 0:
        return
    with PRINT_LOCK:
        if sys.stdout is not None:
            print(f"Chờ {seconds} giây...", end="", flush=True)
    time.sleep(seconds)
    with PRINT_LOCK:
        if sys.stdout is not None:
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
    proxies = parse_proxy(proxy)
    headers_graph = {
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Host": "graph.facebook.com",
        "User-Agent": "okhttp/5.1.0",
    }
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
            "additional_profile_id": sw["prof_id"],
            "access_token": sw["sw_token"] or (matched_graph["graph_token"] if matched_graph else ""),
            "graph_token": matched_graph["graph_token"] if matched_graph else sw["sw_token"]
        })

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


# === HẾT PHẦN 1/2 — DÁN PHẦN 2/2 NGAY BÊN DƯỚI DÒNG NÀY ===
# ==============================================================================
# 6. CÁC HÀM HỖ TRỢ CHỌN PAGE & LÕI REG PAGE PRO5 VIP V5 (TỰ BÓC FILE ẢNH / ZIP)
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

    safe_print(f"\n{Colors.CYAN}Danh sách {len(parsed)} Page đang cầm trên nick:{Colors.RESET}")
    for i, p in enumerate(parsed, 1):
        safe_print(f"  {Colors.YELLOW}[{i}]{Colors.RESET} {p['name']} (Page ID: {p['page_id']} | ProfileUID: {p['additional_profile_id']})")

    max_idx = len(parsed)
    while True:
        choice = input("Chọn Page muốn chuyển (Enter hoặc 'all' = Chọn tất cả, VD: 1-5, 1,3,5, 'q' để hủy): ").strip() or "all"
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

    @staticmethod
    def _decode_fb_body(resp: requests.Response) -> str:
        raw_text = resp.text or ""
        try:
            decoded_json = json.dumps(resp.json(), ensure_ascii=False)
            return raw_text + "\n" + decoded_json
        except Exception:
            try:
                return raw_text + "\n" + raw_text.encode("utf-8").decode("unicode_escape", errors="ignore")
            except Exception:
                return raw_text

    def create_page_and_get_token(
        self,
        page_name: str,
        known_page_ids: set,
        step_callback=None
    ) -> Dict[str, Any]:
        if self.ua_mode == "random":
            self.user_agent = generate_random_katana_ua()

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
            r1 = self.session.post(GRAPHQL_URL, headers=self._get_headers(d1["fb_api_req_friendly_name"]), data=d1, timeout=25)
            body1 = self._decode_fb_body(r1)
            body1_low = body1.lower()
            if "oauthexception" in body1_low or r1.status_code == 401:
                return {"success": False, "is_token_die": True, "message": "Token DIE ở Bước 1 (Submit Name)"}
            if any(k in body1_low for k in ["tên này không hợp lệ", "name is invalid", "không hợp lệ", "chọn tên khác"]):
                return {"success": False, "is_name_invalid": True, "message": f"Tên Page '{page_name}' không hợp lệ"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi mạng Bước 1: {e}"}

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
            r2 = self.session.post(GRAPHQL_URL, headers=self._get_headers(d2["fb_api_req_friendly_name"]), data=d2, timeout=25)
            body2 = self._decode_fb_body(r2)
            body2_low = body2.lower()

            if "oauthexception" in body2_low or r2.status_code == 401 or "session expired" in body2_low:
                return {"success": False, "is_token_die": True, "message": "Token DIE ở Bước 2 (Submit Category)"}

            if any(k in body2_low for k in ["tạo quá nhiều trang", "too many", "thử lại sau", "try again later", "giới hạn", "limit"]):
                return {"success": False, "is_limit": True, "message": "Gần đây bạn đã tạo quá nhiều Trang (Limit)."}

            if '"severity":"critical"' in body2_low or "field_exception" in body2_low or '"fb_bloks_action":null' in body2_low:
                return {"success": False, "is_restricted": True, "message": "Nick bị chặn tạo Page (CRITICAL)"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi mạng Bước 2: {e}"}

        candidate_ids = set(re.findall(r"\(bk\.action\.i64\.Const,\s*(\d{10,})\)", body2 or ""))
        max_scans = 3 if candidate_ids else 1
        wait_scan = 2

        if step_callback:
            step_callback(f"Đang bóc ID & lấy Token Page Pro5 của '{page_name}'...")

        new_page_obj = None
        for _ in range(max_scans):
            time.sleep(wait_scan)
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
                    if (
                        str(p.get("name", "")).strip().lower() == page_name.strip().lower()
                        and str(p.get("id", "")) not in known_page_ids
                    ):
                        new_page_obj = p
                        break

            if new_page_obj:
                break

        if not new_page_obj:
            if not candidate_ids:
                return {
                    "success": False,
                    "is_limit": True,
                    "message": f"Facebook không cấp thêm Page mới cho '{page_name}' (Nick đã đầy Page hoặc chạm Limit)"
                }
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

    def _get_image_from_local_repo(self, media_type: str = "avatar", custom_path: str = "") -> Tuple[Optional[bytes], str]:
        """
        Tự động nhận diện và bóc tách ảnh từ mọi loại file người dùng đưa vào:
        1. File nén (.zip): Tự động đọc ngầm bên trong file .zip và bốc ngẫu nhiên 1 ảnh (không cần giải nén).
        2. File ảnh đơn (.jpg, .jpeg, .png, .webp): Tự lấy ảnh đó và biến đổi mã MD5 mỗi lần up.
        3. File văn bản (.txt): Tự bóc tách các link ảnh (http/https) hoặc đường dẫn ảnh bên trong.
        4. Không truyền gì: Tự động quét ngay thư mục chứa file code (.py), thư mục 'avatars', 'covers'
           để tìm bất kỳ file .zip hoặc file ảnh nào đang có sẵn và lấy ra dùng luôn.
        """
        import zipfile

        valid_img_exts = (".jpg", ".jpeg", ".png", ".webp")
        base_dir = os.path.dirname(os.path.abspath(__file__))

        clean_path = (custom_path or "").strip().strip('"').strip("'")
        if clean_path.startswith("& "):
            clean_path = clean_path[2:].strip().strip('"').strip("'")

        def _salt_image_bytes(raw_data: bytes) -> bytes:
            return raw_data + os.urandom(random.randint(12, 32))

        def _extract_from_zip(zip_filepath: str) -> Tuple[Optional[bytes], str]:
            try:
                with zipfile.ZipFile(zip_filepath, "r") as zf:
                    img_names = [
                        name for name in zf.namelist()
                        if name.lower().endswith(valid_img_exts)
                        and not os.path.basename(name).startswith((".", "_"))
                    ]
                    if not img_names:
                        return None, f"Trong file {os.path.basename(zip_filepath)} không có ảnh (.jpg/.png)"
                    chosen_name = random.choice(img_names)
                    raw_bytes = zf.read(chosen_name)
                    if len(raw_bytes) > 1000:
                        return _salt_image_bytes(raw_bytes), f"{os.path.basename(zip_filepath)} -> {os.path.basename(chosen_name)}"
            except Exception as e:
                return None, f"Lỗi bóc file zip: {e}"
            return None, "Ảnh trong zip bị rỗng"

        def _extract_from_txt(txt_filepath: str) -> Tuple[Optional[bytes], str]:
            try:
                with open(txt_filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                urls = re.findall(r"(https?://[^\s|\"'<>]+)", content)
                local_lines = [
                    ln.strip().strip('"').strip("'")
                    for ln in content.splitlines()
                    if ln.strip() and not ln.strip().startswith("#") and os.path.isfile(ln.strip().strip('"').strip("'"))
                ]
                if local_lines:
                    p_chosen = random.choice(local_lines)
                    with open(p_chosen, "rb") as img_f:
                        return _salt_image_bytes(img_f.read()), os.path.basename(p_chosen)
                if urls:
                    random.shuffle(urls)
                    for u in urls[:5]:
                        try:
                            r = self.session.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                            if r.status_code == 200 and len(r.content) > 1000:
                                return _salt_image_bytes(r.content), u[:35]
                        except Exception:
                            continue
            except Exception as e:
                return None, f"Lỗi đọc file txt: {e}"
            return None, "Không lấy được ảnh từ file txt"

        # --- TRƯỜNG HỢP 1: NGƯỜI DÙNG CHỈ ĐỊNH TRỰC TIẾP 1 FILE (ẢNH / ZIP / TXT) ---
        if clean_path and os.path.isfile(clean_path):
            low_p = clean_path.lower()
            if low_p.endswith(".zip"):
                return _extract_from_zip(clean_path)
            elif low_p.endswith(".txt"):
                return _extract_from_txt(clean_path)
            elif low_p.endswith(valid_img_exts):
                try:
                    with open(clean_path, "rb") as f:
                        return _salt_image_bytes(f.read()), os.path.basename(clean_path)
                except Exception as e:
                    return None, f"Lỗi đọc file ảnh: {e}"

        # --- TRƯỜNG HỢP 2: TỰ ĐỘNG QUÉT TRONG THƯ MỤC CHỨA TOOL & THƯ MỤC CON ---
        avt_dir = os.path.join(base_dir, "avatars")
        cov_dir = os.path.join(base_dir, "covers")
        os.makedirs(avt_dir, exist_ok=True)
        os.makedirs(cov_dir, exist_ok=True)

        search_dirs = []
        if clean_path and os.path.isdir(clean_path):
            search_dirs.append(clean_path)
        if media_type == "avatar":
            search_dirs.extend([avt_dir, base_dir, cov_dir])
        else:
            search_dirs.extend([cov_dir, base_dir, avt_dir])

        image_files = []
        zip_files = []
        txt_img_files = []

        for d in search_dirs:
            if not os.path.isdir(d):
                continue
            for fname in os.listdir(d):
                low_f = fname.lower()
                full_p = os.path.join(d, fname)
                if not os.path.isfile(full_p):
                    continue
                if low_f.endswith(valid_img_exts) and os.path.getsize(full_p) > 1000:
                    image_files.append(full_p)
                elif low_f.endswith(".zip"):
                    zip_files.append(full_p)
                elif low_f in ("images.txt", "avatars.txt", "anh.txt", "links_anh.txt"):
                    txt_img_files.append(full_p)
            if image_files or zip_files or txt_img_files:
                break

        if image_files:
            chosen_img = random.choice(image_files)
            try:
                with open(chosen_img, "rb") as f:
                    return _salt_image_bytes(f.read()), os.path.basename(chosen_img)
            except Exception as e:
                return None, f"Lỗi đọc ảnh: {e}"

        if zip_files:
            return _extract_from_zip(random.choice(zip_files))

        if txt_img_files:
            return _extract_from_txt(random.choice(txt_img_files))

        return None, f"Chưa có file ảnh! Hãy bỏ 1 file ảnh (.jpg/.png) hoặc file .zip cạnh tool ({base_dir})"

    def upload_media(
        self,
        page_id: str,
        page_token: str,
        media_type: str = "avatar",
        profile_uid: str = "",
        graph_token: str = "",
        custom_path: str = ""
    ) -> Dict[str, Any]:
        """
        Tự động bóc ảnh từ file của người dùng -> Đổi MD5 -> Đóng dấu vào Avatar/Cover Page Pro5.
        """
        img_bytes, img_info = self._get_image_from_local_repo(media_type=media_type, custom_path=custom_path)
        if not img_bytes:
            return {"success": False, "message": img_info}

        sw_tk = page_token or graph_token
        g_tk = graph_token or page_token
        target_prof_uid = str(profile_uid or page_id)

        try:
            # --- 1. UP ẢNH BÌA (COVER) ---
            if media_type == "cover":
                for tk_try in [sw_tk, g_tk]:
                    if not tk_try:
                        continue
                    r1 = self.session.post(
                        f"https://graph.facebook.com/v24.0/{page_id}/photos",
                        data={"published": "false", "access_token": tk_try},
                        files={"source": ("cover.jpg", img_bytes, "image/jpeg")},
                        timeout=30
                    ).json()
                    if isinstance(r1, dict) and "id" in r1:
                        r2 = self.session.post(
                            f"https://graph.facebook.com/v24.0/{page_id}",
                            data={"cover": r1["id"], "access_token": tk_try},
                            timeout=30
                        ).json()
                        if isinstance(r2, dict) and "error" not in r2:
                            return {"success": True, "file": img_info}
                return {"success": False, "message": "Lỗi gắn ảnh bìa"}

            # --- 2. UP AVATAR PRO5 ---
            avatar_locked = False
            photo_id = None
            last_err = ""

            crop_rect = json.dumps({"x": 0, "y": 0, "width": 1, "height": 1})
            for pic_ep, tk_use in [
                (f"https://graph.facebook.com/v24.0/{page_id}/picture", sw_tk),
                (f"https://graph.facebook.com/v24.0/{page_id}/picture", g_tk),
                ("https://graph.facebook.com/v24.0/me/picture", sw_tk),
                (f"https://graph.facebook.com/v24.0/{target_prof_uid}/picture", sw_tk),
            ]:
                if not tk_use:
                    continue
                try:
                    r_pic = self.session.post(
                        pic_ep,
                        data={
                            "access_token": tk_use,
                            "scaled_crop_rect": crop_rect,
                            "suppress_stories": "false"
                        },
                        files={"source": ("avatar.jpg", img_bytes, "image/jpeg")},
                        headers={"User-Agent": self.user_agent},
                        timeout=30
                    ).json()
                    if isinstance(r_pic, dict) and "error" not in r_pic:
                        avatar_locked = True
                        break
                    elif isinstance(r_pic, dict) and "error" in r_pic:
                        last_err = r_pic["error"].get("message", "")
                except Exception as e:
                    last_err = str(e)

            for ep_url, tk_use in [
                ("https://graph.facebook.com/v24.0/me/photos", sw_tk),
                (f"https://graph.facebook.com/v24.0/{page_id}/photos", g_tk)
            ]:
                if not tk_use or photo_id:
                    continue
                try:
                    r_up = self.session.post(
                        ep_url,
                        data={"published": "false", "access_token": tk_use},
                        files={"source": ("avatar.jpg", img_bytes, "image/jpeg")},
                        headers={"User-Agent": self.user_agent},
                        timeout=30
                    ).json()
                    if isinstance(r_up, dict) and r_up.get("id"):
                        photo_id = str(r_up["id"])
                        break
                except Exception:
                    pass

            if photo_id:
                set_pic_doc_ids = ["7251203121614451", "5915022358574157", "6623819204340452"]
                for actor_try in [target_prof_uid, str(page_id)]:
                    for doc_id in set_pic_doc_ids:
                        try:
                            variables = {
                                "input": {
                                    "actor_id": actor_try,
                                    "profile_id": actor_try,
                                    "photo_id": photo_id,
                                    "focus": {"x": 0.5, "y": 0.5},
                                    "profile_pic_method": "UPLOAD",
                                    "profile_pic_source": "TIMELINE",
                                    "client_mutation_id": str(uuid.uuid4())
                                }
                            }
                            gql_data = {
                                "method": "post",
                                "pretty": "false",
                                "format": "json",
                                "server_timestamps": "true",
                                "locale": "vi_VN",
                                "fb_api_req_friendly_name": "ProfilePictureSetMutation",
                                "fb_api_caller_class": "graphservice",
                                "doc_id": doc_id,
                                "variables": json.dumps(variables),
                                "client_trace_id": str(uuid.uuid4())
                            }
                            r_gql = self.session.post(
                                GRAPHQL_URL,
                                headers=self._get_headers("ProfilePictureSetMutation", token_override=sw_tk),
                                data=gql_data,
                                timeout=20
                            ).json()
                            if isinstance(r_gql, dict) and "error" not in r_gql and "errors" not in r_gql:
                                avatar_locked = True
                                break
                        except Exception:
                            pass

            if avatar_locked:
                return {"success": True, "file": img_info}
            return {"success": False, "message": last_err or "Không gắn được Avatar"}
        except Exception as e:
            return {"success": False, "message": str(e)[:60]}

    def post_welcome(self, page_id: str, page_token: str) -> Dict[str, Any]:
        try:
            payload = {
                "message": "Chào mừng mọi người đến với Page! Hãy ấn theo dõi để cập nhật những thông tin mới nhất nhé!",
                "access_token": page_token
            }
            r = self.session.post(f"https://graph.facebook.com/v24.0/{page_id}/feed", data=payload, timeout=25).json()
            if "error" in r:
                return {"success": False, "message": r["error"].get("message", "Lỗi đăng bài")}
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)[:60]}


# ==============================================================================
# 7. ĐỐI TƯỢNG ACCOUNT TASK & LUỒNG XỬ LÝ CUỐN CHIẾU TỪNG PAGE
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
        auto_buff_media: bool = False,
        custom_media_path: str = "",
        transfer_old_pages: bool = False
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
        self.custom_media_path = custom_media_path
        self.transfer_old_pages = transfer_old_pages
        self.fixed_ua = generate_random_katana_ua(seed=self.token or self.pre_uid) if ua_mode == "fixed" else None
        self.creator: Optional[FbPageCreator] = None
        self.mother_uid = self.pre_uid
        self.mother_name = ""
        self.status = "ready"
        self.current_action = "Chờ đến lượt..."
        self.last_result = ""


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
    existing_old_pages = pre_pages_res.get("pages", [])
    known_page_ids = set()
    for p in existing_old_pages:
        if p.get("id"):
            known_page_ids.add(str(p["id"]))
        if p.get("additional_profile_id"):
            known_page_ids.add(str(p["additional_profile_id"]))

    add_process_log(
        acc.acc_id,
        acc.mother_uid,
        f"{Colors.GREEN}✔ Nick LIVE ({acc.mother_name}) - Có sẵn {len(existing_old_pages)} Page cũ.{Colors.RESET}"
    )

    has_counted_holder_acc = False
    page_summary_list = []
    last_transfer_note = "Đã lưu vào acc_cam_page.txt"
    hit_limit = False
    hit_restricted = False
    wait_seconds = max(1, int(verify_delay))
    consecutive_fails = 0

    if acc.transfer_old_pages and existing_old_pages and (acc.holder_uid or acc.holder_token):
        add_process_log(
            acc.acc_id,
            acc.mother_uid,
            f"{Colors.CYAN}🔄 Đang chuyển {len(existing_old_pages)} Page cũ có sẵn trên Acc sang Nick Mẹ...{Colors.RESET}"
        )
        for old_idx, old_p in enumerate(existing_old_pages, 1):
            p_id = str(old_p.get("id", ""))
            p_name = str(old_p.get("name", ""))
            p_token = str(old_p.get("access_token", ""))
            p_uid = str(old_p.get("additional_profile_id") or p_id)

            def old_cb(msg_step: str):
                acc.current_action = f"[L{thread_id}] [Page Cũ {old_idx}/{len(existing_old_pages)}] {msg_step}"
                add_process_log(acc.acc_id, acc.mother_uid, f"🚀 [Page Cũ {old_idx}] {msg_step}")

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
                step_callback=old_cb
            )
            transfer_ok = tr_res.get("success", False)
            transfer_status = tr_res.get("status", "FAILED")
            invitation_id = tr_res.get("invitation_id") or ""
            last_transfer_note = tr_res.get("message", "")

            if transfer_ok:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}✅ [Page Cũ {old_idx}] {last_transfer_note}{Colors.RESET}")
            else:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}⚠️ [Page Cũ {old_idx}] {last_transfer_note}{Colors.RESET}")

            acc.pages_created += 1
            page_summary_list.append(f"{p_id}:{p_name}")
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with FILE_LOCK:
                if not has_counted_holder_acc:
                    stats["total_holder_acc"] += 1
                    has_counted_holder_acc = True
                stats["total_pages"] += 1
                if transfer_ok:
                    stats["total_invited"] += 1
                tr_tag = f"{transfer_status}:{acc.holder_uid}" + (f"(InviteID:{invitation_id})" if invitation_id else "")
                with open("acc_cam_page.txt", "a", encoding="utf-8") as f_holder:
                    f_holder.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|{p_id}|{p_uid}|{p_name}|{p_token}|{tr_tag}|{now_str}\n")

    for idx in range(1, acc.target_pages + 1):
        acc.status = "running"
        page_name = get_page_name(name_type, custom_names)

        def update_step(msg_step: str):
            acc.current_action = f"[L{thread_id}] [Page {idx}/{acc.target_pages}] {msg_step}"
            add_process_log(acc.acc_id, acc.mother_uid, f"[Page {idx}/{acc.target_pages}] {msg_step}")

        create_res = acc.creator.create_page_and_get_token(
            page_name=page_name,
            known_page_ids=known_page_ids,
            step_callback=update_step
        )

        if create_res.get("is_token_die"):
            acc.status = "die"
            acc.current_action = f"Nick bị DIE ở Page {idx}/{acc.target_pages} (Đã giữ được {acc.pages_created} Page trước)"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ Nick bị DIE khi đang tạo Page {idx}!{Colors.RESET}")
            with FILE_LOCK:
                stats["total_token_die"] += 1
                with open("acc_die.txt", "a", encoding="utf-8") as f:
                    f.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|DIE_O_PAGE_{idx}\n")
            return

        if create_res.get("is_limit"):
            hit_limit = True
            err_lim = create_res.get("message", "Nick đã chạm Limit tạo Page")
            acc.current_action = f"[L{thread_id}] Dừng Reg ở Page {idx}: {err_lim}"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}🚫 [Page {idx}] {err_lim} -> Dừng tạo thêm!{Colors.RESET}")
            break

        if create_res.get("is_restricted"):
            hit_restricted = True
            acc.current_action = f"[L{thread_id}] Nick bị chặn tạo Page (CRITICAL) ở Page {idx}"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.MAGENTA}⚠️ Nick bị chặn tạo Page (CRITICAL) ở Page {idx}.{Colors.RESET}")
            break

        if not create_res.get("success"):
            consecutive_fails += 1
            err_detail = create_res.get("message", "Không lên Page")
            acc.current_action = f"[L{thread_id}] Lần tạo {idx} xịt: {err_detail}"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}⚠️ Lần tạo {idx}: {err_detail}{Colors.RESET}")

            if consecutive_fails >= 2:
                hit_limit = True
                add_process_log(
                    acc.acc_id,
                    acc.mother_uid,
                    f"{Colors.YELLOW}🚫 Xịt {consecutive_fails} lần liên tiếp -> Tự động dừng Reg nick này để không treo luồng!{Colors.RESET}"
                )
                break

            if idx < acc.target_pages and delay_between_pages > 0:
                for s_rem in range(delay_between_pages, 0, -1):
                    acc.current_action = f"[L{thread_id}] Lần {idx} xịt. Nghỉ {s_rem}s trước khi thử lần {idx + 1}..."
                    time.sleep(1)
            continue

        consecutive_fails = 0
        p_id = str(create_res["page_id"])
        p_name = str(create_res["page_name"])
        p_token = str(create_res["page_token"])
        g_token = str(create_res.get("graph_token") or p_token)
        p_uid = str(create_res.get("additional_profile_id") or p_id)

        known_page_ids.add(p_id)
        known_page_ids.add(p_uid)

        short_ptk = f"{p_token[:16]}..." if p_token else "Chưa cấp riêng"
        add_process_log(
            acc.acc_id,
            acc.mother_uid,
            f"{Colors.GREEN}🎉 [Page {idx}] Tạo thành công '{p_name}' (ID: {p_id} | ProfileUID: {p_uid}) | Token: {short_ptk}{Colors.RESET}"
        )

        acc.status = "waiting_check"
        add_process_log(
            acc.acc_id,
            acc.mother_uid,
            f"⏳ [Page {idx}] Đang đợi {wait_seconds}s để FB khởi tạo xong nhân Pro5 & Check Live '{p_name}'..."
        )
        for rem in range(wait_seconds, 0, -1):
            acc.current_action = f"[L{thread_id}] [Page {idx}/{acc.target_pages}] Đợi {rem}s để Check Live & Đồng bộ Page {p_id}..."
            time.sleep(1)

        acc.status = "running"
        acc.current_action = f"[L{thread_id}] [Page {idx}] Đang Check Live Acc & Page '{p_name}'..."

        recheck_acc = acc.creator.check_account_live(retries=2)
        if not recheck_acc.get("success") and recheck_acc.get("is_token_die"):
            acc.status = "die"
            acc.current_action = f"Sau {wait_seconds}s ở Page {idx}: Tài khoản bị DIE / Checkpoint!"
            add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.RED}❌ [Page {idx}] Sau {wait_seconds}s: Tài khoản bị DIE!{Colors.RESET}")
            with FILE_LOCK:
                stats["total_token_die"] += 1
                with open("acc_die.txt", "a", encoding="utf-8") as f:
                    f.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|DIE_SAU_{wait_seconds}S_PAGE_{idx}\n")
            return

        fresh_raw_pages = _fetch_all_pages_raw(acc.token, acc.mother_uid, proxy=acc.proxy)
        for sw_item in fresh_raw_pages:
            if (
                sw_item["page_id"] == p_id
                or sw_item["additional_profile_id"] == p_uid
                or sw_item["name"].strip().lower() == p_name.strip().lower()
            ):
                if sw_item.get("access_token"):
                    p_token = sw_item["access_token"]
                if sw_item.get("graph_token"):
                    g_token = sw_item["graph_token"]
                if sw_item.get("additional_profile_id"):
                    p_uid = sw_item["additional_profile_id"]
                break

        page_live_res = acc.creator.check_single_page_live(page_id=p_id, page_token=p_token)
        if not page_live_res.get("success"):
            add_process_log(
                acc.acc_id,
                acc.mother_uid,
                f"{Colors.RED}❌ [Page {idx}] Page {p_id} bị DIE/Hủy đăng sau {wait_seconds}s: {page_live_res.get('message')}{Colors.RESET}"
            )
            if idx < acc.target_pages and delay_between_pages > 0:
                time.sleep(delay_between_pages)
            continue

        add_process_log(
            acc.acc_id,
            acc.mother_uid,
            f"{Colors.GREEN}✔ [Page {idx}] Check LIVE OK: Page {p_id} (ProfileUID: {p_uid}) SỐNG!{Colors.RESET}"
        )

        if acc.auto_buff_media and (p_token or g_token):
            acc.current_action = f"[L{thread_id}] [Page {idx}] Đang bóc ảnh từ kho & Up Ảnh bìa cho '{p_name}'..."
            cv_res = acc.creator.upload_media(
                page_id=p_id,
                page_token=p_token,
                media_type="cover",
                profile_uid=p_uid,
                graph_token=g_token,
                custom_path=acc.custom_media_path
            )
            time.sleep(2)

            acc.current_action = f"[L{thread_id}] [Page {idx}] Đang bóc ảnh từ kho & Up Avatar Pro5 cho '{p_name}'..."
            av_res = acc.creator.upload_media(
                page_id=p_id,
                page_token=p_token,
                media_type="avatar",
                profile_uid=p_uid,
                graph_token=g_token,
                custom_path=acc.custom_media_path
            )
            time.sleep(1)

            acc.creator.post_welcome(p_id, p_token or g_token)

            av_status = f"OK ({av_res.get('file', '')})" if av_res.get("success") else f"Lỗi ({av_res.get('message')})"
            cv_status = f"OK ({cv_res.get('file', '')})" if cv_res.get("success") else f"Lỗi ({cv_res.get('message')})"
            add_process_log(
                acc.acc_id,
                acc.mother_uid,
                f"{Colors.CYAN}🖼️ [Page {idx}] Kho Ảnh -> Avatar: {av_status} | Cover: {cv_status}{Colors.RESET}"
            )

        transfer_ok = False
        transfer_status = "NO_TARGET"
        invitation_id = ""

        if acc.holder_uid or acc.holder_token:
            def super_cb(msg_step: str):
                acc.current_action = f"[L{thread_id}] [Page {idx}] {msg_step}"
                add_process_log(acc.acc_id, acc.mother_uid, f"🚀 [Page {idx}] {msg_step}")

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
            transfer_ok = tr_res.get("success", False)
            transfer_status = tr_res.get("status", "FAILED")
            invitation_id = tr_res.get("invitation_id") or ""
            last_transfer_note = tr_res.get("message", "")
            if transfer_ok:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.GREEN}✅ [Page {idx}] {last_transfer_note}{Colors.RESET}")
            else:
                add_process_log(acc.acc_id, acc.mother_uid, f"{Colors.YELLOW}⚠️ [Page {idx}] {last_transfer_note}{Colors.RESET}")

        acc.pages_created += 1
        page_summary_list.append(f"{p_id}:{p_name}")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with FILE_LOCK:
            if not has_counted_holder_acc:
                stats["total_holder_acc"] += 1
                has_counted_holder_acc = True
            stats["total_pages"] += 1
            if transfer_ok:
                stats["total_invited"] += 1

            with open("created_pages.txt", "a", encoding="utf-8") as f_page:
                f_page.write(f"{p_id}|{p_uid}|{p_name}|{p_token}|{acc.mother_uid}|{acc.password}|{now_str}\n")

            with open("acc_cam_page.txt", "a", encoding="utf-8") as f_holder:
                if acc.holder_uid or acc.holder_token:
                    tr_tag = f"{transfer_status}:{acc.holder_uid}" + (f"(InviteID:{invitation_id})" if invitation_id else "")
                    f_holder.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|{p_id}|{p_uid}|{p_name}|{p_token}|{tr_tag}|{now_str}\n")
                else:
                    f_holder.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|{p_id}|{p_uid}|{p_name}|{p_token}|PAGE_LIVE|{now_str}\n")

        if idx < acc.target_pages and delay_between_pages > 0:
            for s_rem in range(delay_between_pages, 0, -1):
                acc.current_action = f"[L{thread_id}] Đã xong Page {idx}/{acc.target_pages}! Nghỉ {s_rem}s trước khi Reg Page {idx + 1}..."
                time.sleep(1)

    if acc.pages_created == 0:
        if hit_limit:
            acc.status = "limit"
            acc.current_action = f"Nick chạm Limit Page (Đang có sẵn {len(existing_old_pages)} Page cũ) -> Đã dừng"
            with FILE_LOCK:
                stats["total_limited"] += 1
        else:
            acc.status = "no_page"
            reason_str = "Nick bị chặn (CRITICAL)" if hit_restricted else "Tạo xong nhưng không có Page mới nào"
            acc.current_action = f"{reason_str} -> Lưu acc_reg_xit.txt"
            with FILE_LOCK:
                stats["total_no_page"] += 1
                with open("acc_reg_xit.txt", "a", encoding="utf-8") as f:
                    f.write(f"{acc.mother_uid}|{acc.password}|{acc.token}|KHONG_LEN_PAGE\n")
        return

    acc.status = "done"
    first_page_str = ", ".join(page_summary_list[:2])
    acc.last_result = f"LIVE & Xử lý {acc.pages_created} Page ({first_page_str}) | {last_transfer_note}"
    acc.current_action = acc.last_result


def worker_reg_account(
    thread_id: int,
    queue_obj: Queue,
    name_type: str,
    custom_names: Optional[List[str]],
    verify_delay: int,
    delay_between_pages: int,
    stats: Dict[str, int]
):
    while True:
        try:
            acc = queue_obj.get(timeout=2.0)
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
            queue_obj.task_done()


# ==============================================================================
# 8. BẢNG ĐIỀU KHIỂN GUI (CUSTOMTKINTER DARK MODE - 3 TAB ĐẦY ĐỦ)
# ==============================================================================

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

        # Trạng thái Tab 1 (Reg + Chuyển Cuốn Chiếu)
        self.reg_running = False
        self.reg_tasks: List[AccountTask] = []
        self.reg_tree_iids: Dict[int, str] = {}
        self.reg_queue: Optional[Queue] = None
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
        self.tr_log_queue: "Queue[Tuple[str, str]]" = Queue()
        self.tr_ui_queue: "Queue[Tuple[str, Any]]" = Queue()

        # Trạng thái Tab 3 (Get Token EAAAAU)
        self.tk_running = False
        self.tk_stop_flag = threading.Event()
        self.tk_ui_queue: "Queue[Tuple[str, Any]]" = Queue()
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
        parsed_items = parse_universal_lines(raw_lines)
        if not parsed_items:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập danh sách Acc nguồn hợp lệ.")
            return

        try:
            pages_per_nick = max(1, int(self.reg_pages_per_acc.get().strip() or "4"))
            verify_delay = max(1, int(self.reg_verify_delay.get().strip() or "10"))
            delay_between = max(0, int(self.reg_delay_between.get().strip() or "5"))
            num_threads = max(1, min(50, int(self.reg_threads.get().strip() or "3")))
        except ValueError:
            messagebox.showerror("Sai thông số", "Số Page, Delay và Số luồng phải là số nguyên.")
            return

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

        px_lines = [l.strip() for l in self.reg_proxy_box.get("1.0", "end").splitlines() if l.strip()]
        global_proxies = [pl for pl in px_lines if parse_proxy(pl)]

        holder_raw = self.reg_holder_entry.get().strip()
        default_pwd = self.reg_default_pwd.get().strip()
        ua_mode = "random" if "Random" in self.reg_ua_mode.get() else "fixed"
        auto_buff_media = self.reg_buff_media_var.get()
        custom_media_path = self.reg_media_path.get().strip()
        transfer_old_pages = self.reg_transfer_old_var.get()

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

        def _bootstrap():
            holder_targets = []
            if holder_raw and holder_raw != "0":
                GUI_LOG_QUEUE.put(("Đang xác thực thông tin Nick Mẹ nhận Page...\n", "cyan"))
                parsed_targets = parse_holder_target(holder_raw)
                for t in parsed_targets:
                    if t.get("token") and not t.get("uid"):
                        info_nhan = get_id(t["token"], proxy=t.get("proxy"))
                        if info_nhan:
                            t["uid"], t_name = info_nhan
                            GUI_LOG_QUEUE.put((f"✔ Nick Mẹ: {t_name} ({t['uid']}) -> Bật Auto Accept Full 4 Bước!\n", "success"))
                            holder_targets.append(t)
                        else:
                            GUI_LOG_QUEUE.put(("✗ Token Nick Mẹ không hợp lệ hoặc DIE!\n", "error"))
                    elif t.get("uid"):
                        if t.get("token"):
                            info_nhan = get_id(t["token"], proxy=t.get("proxy"))
                            t_name = info_nhan[1] if info_nhan else "Nick Mẹ"
                            GUI_LOG_QUEUE.put((f"✔ Nick Mẹ: {t_name} ({t['uid']}) -> Auto Accept Full 4 Bước!\n", "success"))
                        else:
                            GUI_LOG_QUEUE.put((f"✔ UID Nick Mẹ: {t['uid']} -> Bắn lời mời Bước 1 & 2.\n", "success"))
                        holder_targets.append(t)

            task_q: Queue = Queue()
            tasks: List[AccountTask] = []
            for idx, it in enumerate(parsed_items):
                assigned_px = global_proxies[idx % len(global_proxies)] if global_proxies and not it.get("proxy") else None
                assigned_target = holder_targets[idx % len(holder_targets)] if holder_targets else None
                t_obj = AccountTask(
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
                    target=worker_reg_account,
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
            except Empty:
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
        creds = parse_universal_lines(raw_lines)
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
                    l_res = login_and_get_token(cred)
                    if l_res.get("success"):
                        token = l_res["token"]
                    else:
                        self._tr_log(f"[Nick #{i}] Login thất bại: {l_res.get('message')}", "error")
                        continue

                info = get_id(token, proxy=px)
                if info is None and uid_file and password:
                    self._tr_log(f"[Nick #{i}] Token cũ hết hạn -> Đang Login lại...", "warn")
                    l_res = login_and_get_token(cred)
                    if l_res.get("success"):
                        token = l_res["token"]
                        info = get_id(token, proxy=px)

                if info is None:
                    if not uid_file:
                        self._tr_log(f"[Nick #{i}] Token DIE & không có UID -> Bỏ qua.", "error")
                        continue
                    id_acc, name_acc = str(uid_file), f"UID {uid_file}"
                else:
                    id_acc, name_acc = str(uid_file or info[0]), info[1]

                self._tr_log(f"[Nick #{i}] Đang quét Page của {name_acc} ({id_acc})...", "cyan")
                pages = get_all_pages(token, id_acc, proxy=px)
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
                targets = parse_holder_target(raw_target)
                if not targets:
                    self._tr_log("Dữ liệu Nick Nhận không hợp lệ!", "error")
                    self.tr_ui_queue.put(("transfer_done", None))
                    return
                t0 = targets[0]
                t_uid = t0.get("uid") or ""
                t_tok = t0.get("token")
                receiver_proxy = t0.get("proxy")
                if t_tok:
                    info_n = get_id(t_tok, proxy=receiver_proxy)
                    if info_n:
                        id_acc_nhan, name_acc_nhan = info_n
                        token_nhan = t_tok
                        target_page_ids = get_managed_page_ids(token_nhan, proxy=receiver_proxy)
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

                tr_res = execute_super_transfer(
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
                    with FILE_LOCK:
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
                    with FILE_LOCK:
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
        acc_list = parse_universal_lines(raw_lines)
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

        q_jobs: Queue = Queue()
        for idx, acc in enumerate(acc_list, 1):
            self.tk_tree.insert("", "end", iid=str(idx), values=(idx, acc.get("uid", ""), "Chờ...", ""))
            q_jobs.put((idx, acc))

        stats = {"total": len(acc_list), "ok": 0, "fail": 0}
        lock = threading.Lock()

        def _worker():
            while not self.tk_stop_flag.is_set():
                try:
                    idx, acc = q_jobs.get_nowait()
                except Empty:
                    break
                uid = acc.get("uid", "")
                pwd = acc.get("pwd", "")
                cookie = acc.get("cookie", "")
                proxy = acc.get("proxy", "")

                self.tk_ui_queue.put(("row", (idx, uid, "Đang Login...", "Bloks CAA v5...", "run")))
                res = login_and_get_token(acc)

                if res.get("success"):
                    token = res.get("token", "")
                    new_ck = res.get("cookie") or cookie
                    line_out = f"{uid}|{pwd}"
                    if new_ck:
                        line_out += f"|{new_ck}"
                    line_out += f"|{token}"
                    if proxy:
                        line_out += f"|{proxy}"

                    with FILE_LOCK:
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
        if self.reg_running:
            self._refresh_reg_dashboard()

        reg_logs = []
        for _ in range(40):
            try:
                reg_logs.append(GUI_LOG_QUEUE.get_nowait())
            except Empty:
                break
        if reg_logs:
            self._append_logs(self.reg_log_box, reg_logs)

        tr_logs = []
        for _ in range(40):
            try:
                tr_logs.append(self.tr_log_queue.get_nowait())
            except Empty:
                break
        if tr_logs:
            self._append_logs(self.tr_log_box, tr_logs)

        for _ in range(30):
            try:
                ev, payload = self.tr_ui_queue.get_nowait()
            except Empty:
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

        for _ in range(30):
            try:
                ev, payload = self.tk_ui_queue.get_nowait()
            except Empty:
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

    def _append_logs(self, textbox: ctk.CTkTextbox, items: List[Tuple[str, str]]):
        textbox.configure(state="normal")
        inner = textbox._textbox
        for text, tag in items:
            inner.insert("end", text, tag)
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
