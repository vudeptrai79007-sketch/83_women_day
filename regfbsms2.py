# -*- coding: utf-8 -*-
# ==============================================================================
# TOOL ĐĂNG KÝ FACEBOOK GRAPHQL (CHUẨN LOGIC REGMỒI SĐT & FULL BẢO MẬT CHẤT LƯỢNG CAO)
# TÍCH HỢP TỰ ĐỘNG:
# 1. LOGIC REG1: 1 GMAIL (GMAIL94/GMAIL THẬT) RA 4 ACC FB (HOẶC MAIL.TM / HOTMAIL)
# 2. BƯỚC 1: WARMUP HOMEPAGE & TẢI FULL COMET TOKEN (LSD, JAZOEST, SPIN_R, HSI, HSDP...)
# 3. BƯỚC 2: FIELD VALIDATION TRƯỚC KHI SUBMIT (TRÁNH LỖI INVALID CONTACTPOINT)
# 4. BƯỚC 3: REG MỒI SĐT US CHUẨN (+1 XXX-XXX-XXXX HỢP LỆ VÙNG BẮC MỸ) VƯỢT BOT
# 5. BƯỚC 4: THÊM FAKE INTERMEDIATE MAIL RỒI ADD CONTACT POINT SANG GMAIL / EMAIL MỤC TIÊU
# 6. BƯỚC 5: XÁC THỰC OTP GRAPHQL, KIỂM TRA LIVE/CHECKPOINT 049/282
# 7. BƯỚC 6: ĐÁ GMAIL GIẢI PHÓNG & TỰ ĐỘNG ĐĂNG KÝ 4 ACC DOLA AI NẾU CÓ COOKIE
# 8. [NEW] HỖ TRỢ CHẠY BẰNG 4G/WIFI THẬT (DIRECT — KHÔNG PROXY)
# 9. [NEW] TÍCH HỢP API THUÊ MAIL & HOÀN TIỀN TỰ ĐỘNG MAIL.PSTMMO.CC
# ==============================================================================

import base64
import datetime
import email
import email.utils
import hashlib
import hmac
import imaplib
import io
import json
import os
import random
import re
import string
import struct
import sys
import threading
import tempfile
import time

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import unicodedata
import urllib.parse
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import shutil


# PSTMMO: bảng giá tham khảo từ ảnh, không kết nối API.
def _pstmmo_price_catalog() -> None:
    rates = (
        ("gmail.com", 1232),
        ("gmx.com", 53),
        ("mail.com", 53),
        ("email.com", 53),
        ("icloud.com", 352),
        ("yandex.fi", 176),
        ("yandex.ee", 176),
        ("yandex.kg", 176),
        ("yandex.tm", 176),
        ("yandex.com.ge", 176),
        ("yandex.by", 176),
        ("yandex.lt", 176),
        ("yandex.co.il", 176),
        ("yandex.com.am", 176),
        ("ya.ru", 176),
        ("yandex.uz", 176),
        ("yandex.fr", 176),
        ("yandex.tj", 176),
        ("yandex.az", 176),
        ("yandex.pl", 176),
        ("yandex.kz", 176),
        ("yandex.md", 176),
        ("yandex.com", 176),
        ("yandex.ru", 176),
        ("gmx.ru", 53),
        ("gmx.se", 53),
    )
    options = {str(i): (domain, f"{price:,}".replace(",", "."))
               for i, (domain, price) in enumerate(rates, 1)}
    print("PSTMMO — GIÁ THAM KHẢO TỪ ẢNH (26 ĐUÔI)")
    print("Chỉ xem giá. Không kiểm tra tồn kho, thuê mail hay đọc OTP.\n")
    for number, (domain, price) in options.items():
        print(f"{number:>2}. @{domain:<16} {price:>6} đ/mail")
    print(" 0. Thoát")
    while True:
        try:
            choice = input("\nNhập số để xem giá (0 = thoát): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "0":
            return
        if choice in options:
            domain, price = options[choice]
            print(f"@{domain} — {price} đ/mail (giá tham khảo)")
        else:
            print(f"Chọn số từ 1 đến {len(options)} hoặc 0 để thoát.")


if __name__ == "__main__" and sys.argv[1:] == ["--pstmmo-prices"]:
    _pstmmo_price_catalog()
    raise SystemExit(0)

try:
    from rich.console import Console, Group
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    from rich import box
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

console = Console() if _HAS_RICH else None

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from openpyxl import Workbook, load_workbook
    HAS_OPENPYXL = True
except Exception:
    HAS_OPENPYXL = False

try:
    import reg_dola
    HAS_REG_DOLA = True
except Exception:
    HAS_REG_DOLA = False

try:
    from curl_cffi import requests as curl_requests
    from curl_cffi.requests import Session as CurlSession
    HAS_CURL_CFFI = True
except Exception:
    HAS_CURL_CFFI = False

# ==============================================================================
# PHẦN MODULE EMAILFAKE QUA PROXY ĐƯỢC TỐI ƯU SIÊU NHẸ (GIẢM >90% DUNG LƯỢNG)
# ==============================================================================
class EmailFakeManagerProxied:
    """
    Quản lý tạo Email ảo & đọc mã OTP tự động từ https://emailfake.com qua PROXY.
    """
    DEFAULT_DOMAINS = [
        'fundproceed.com', 'excipientnetwork.com', 'ds4kojima.com', 'anhmaybietchoi.com',
        'past-line.com', 'trevourus.com', 'turnimon.com', 'cckuy.com', 'gohivezone.com',
        'fitbloomlab.com', 'duosakhiy.com', 'savemydinar.com', 'electrolabx.com', 'integrately.net',
        'maxclone.vn', 'inly.vn', 'zhiezmotion.me', 'penghuan.pro', 'cangcutku.pro', 'telecore.in',
        'cityhubz.tokyo', 'mirasync.tokyo', 'tuandinhh.tokyo', 'navermail.kr', 'lebab.nl',
        'reteme.online', 'brightpatha.biz', 'small680.online', 'chirugrow.online', 'tatatutu.site',
        'jasonpost.site', 'makbisah.site', 'premierr.site', 'moryne.site', 'asdfgpooi.online',
        'appcloudmurah.email', 'vodich1.com', 'shopcaunho.com', 'jinam.tech', 'okmabuiyak.tech',
        'webanx.app', 'andalanglobal.app', 'tams.codes', 'hethongtudong.store', 'zumys.store',
        'zavmecor.store', 'j3r8qd.store', 'seller-millionaire.store', 'trialname.shop', 'dyyfin.shop',
        'handcart.online', 'tlcfbmt.online', 'poweradxas.online', 'qavexo.online', 'mailtiktoknew.us',
        'moonikent.us', 'charl.us', 'evilgodshop1.uk', 'evilgodshop2.uk', 'diplom-voronesh.ru'
    ]

    @classmethod
    def get_domains_pool(cls) -> list:
        return cls.DEFAULT_DOMAINS

    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache'
        })
        self.email: Optional[str] = None
        self.username: Optional[str] = None
        self.domain: Optional[str] = None
        self.domains_list = self.get_domains_pool()

    def create_email(self) -> Tuple[Optional[str], Optional[str]]:
        candidate_domains = list(self.domains_list)
        random.shuffle(candidate_domains)

        for domain in candidate_domains[:10]:
            name_chars = string.ascii_lowercase + string.digits
            username = ''.join(random.choices(name_chars, k=random.randint(7, 10)))
            self.username = username
            self.domain = domain
            self.email = f"{username}@{domain}".lower()

            try:
                activate_url = f"https://emailfake.com/{self.domain}/{self.username}"
                r_act = self.session.get(activate_url, proxies=self.proxies, timeout=10)
                if r_act.status_code in (200, 301, 302):
                    return self.email, self.email
            except Exception:
                continue

        domain = random.choice(self.domains_list)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.username = username
        self.domain = domain
        self.email = f"{username}@{domain}".lower()
        return self.email, self.email

    def get_otp(self, max_retries: int = 5, delay: float = 5.0) -> Optional[str]:
        if not self.email or not self.username or not self.domain:
            return None

        inbox_url = f"https://emailfake.com/{self.domain}/{self.username}"

        for attempt in range(1, max_retries + 1):
            time.sleep(delay)
            try:
                r = self.session.get(inbox_url, proxies=self.proxies, timeout=12)
                if r.status_code == 200:
                    html = r.text
                    patterns = [
                        r'(\d{5,8})\s+là mã để bạn xác nhận',
                        r'(\d{5,8})\s+is your confirmation code',
                        r'FB-(\d{5,8})',
                        r'(?:code|mã|xác nhận|confirmation)[\s:]*#?\s*([0-9]{5,8})',
                        r'class=["\']subj["\'][^>]*>.*?([0-9]{5,8})',
                        r'class=["\']subj_div["\'][^>]*>.*?([0-9]{5,8})'
                    ]
                    for pat in patterns:
                        m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
                        if m:
                            code = m.group(1).strip()
                            if len(code) in (5, 6, 8):
                                return code

                    msg_blocks = re.findall(r'<div[^>]*class=["\'][^"\']*(?:subj|email_list|mess_div)[^"\']*["\'][^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
                    for blk in msg_blocks:
                        m_num = re.search(r'\b([0-9]{5,6})\b', blk)
                        if m_num:
                            return m_num.group(1).strip()
            except Exception:
                pass
        return None


class TempMailLolManager:
    """
    Quản lý tạo Email ảo & đọc mã OTP tự động từ https://tempmail.lol/ (API v2)
    """
    BASE_URL = "https://api.tempmail.lol/v2"

    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.email: Optional[str] = None
        self.token: Optional[str] = None

    @classmethod
    def _get_proxies(cls, proxy: Optional[str] = None):
        return {"http": proxy, "https": proxy} if proxy else None

    @classmethod
    def create_account(cls, proxy: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        proxies = cls._get_proxies(proxy)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        attempts_proxies = [proxies, None] if proxies else [None]
        for px in attempts_proxies:
            try:
                r = requests.get(f"{cls.BASE_URL}/inbox/create", headers=headers, timeout=12, proxies=px)
                if r.status_code in (200, 201):
                    data = r.json()
                    addr = data.get("address")
                    tok = data.get("token")
                    if addr and tok:
                        return addr.lower(), tok
            except Exception:
                continue
        return None, None

    def create_email(self) -> Tuple[Optional[str], Optional[str]]:
        addr, tok = self.create_account(proxy=self.proxy)
        if addr and tok:
            self.email = addr
            self.token = tok
            return addr, tok
        return None, None

    @classmethod
    def get_otp(cls, token: str, proxy: Optional[str] = None, max_retries: int = 15, delay: float = 3.0) -> Optional[str]:
        if not token:
            return None
        proxies = cls._get_proxies(proxy)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        attempts_proxies = [proxies, None] if proxies else [None]

        for i in range(max_retries):
            time.sleep(delay)
            for px in attempts_proxies:
                try:
                    r = requests.get(f"{cls.BASE_URL}/inbox?token={token}", headers=headers, timeout=10, proxies=px)
                    if r.status_code != 200:
                        continue
                    m_json = r.json()
                    emails = m_json.get("emails", [])
                    for m in emails:
                        subj = str(m.get('subject', '') or '').strip()
                        body_raw = str(m.get('body', '') or '')
                        html_raw = str(m.get('html', '') or '')

                        if subj:
                            subj_patterns = [
                                r'(\d{5,8})\s*(?:là mã|is your|คือรหัส|es tu|est votre)',
                                r'(?:FB-|mã|code|รหัส|código)\s*[:\s#]?\s*([0-9]{5,8})',
                                r'\b([0-9]{6})\b',
                                r'\b([0-9]{5,8})\b'
                            ]
                            for sp in subj_patterns:
                                sm = re.search(sp, subj, re.IGNORECASE)
                                if sm:
                                    sc = sm.group(1).strip()
                                    if sc != "94025" and 5 <= len(sc) <= 8:
                                        return sc

                        clean_text = re.sub(r'<[^>]+>', ' ', html_raw or body_raw)
                        clean_text = re.sub(r'\s+', ' ', clean_text)

                        body_patterns = [
                            r'(\d{5,8})\s*(?:là mã|is your|คือรหัส|es tu|est votre)',
                            r'(?:FB-|mã xác nhận|confirmation code|รหัสยืนยัน|security code)\s*[:\s#]?\s*([0-9]{5,8})',
                            r'(?:mã|code|รหัส)\s*[:\s#]?\s*([0-9]{5,8})',
                            r'\b([0-9]{6})\b'
                        ]
                        for bp in body_patterns:
                            bm = re.search(bp, clean_text, re.IGNORECASE)
                            if bm:
                                bc = bm.group(1).strip()
                                if bc != "94025" and 5 <= len(bc) <= 8:
                                    return bc
                    break
                except Exception:
                    continue
        return None


# --- Helper dùng chung ---
def compute_jazoest(token: str) -> str:
    if not token:
        return "2"
    return f"2{sum(ord(c) for c in str(token))}"


def format_proxy_url(proxy_str: Optional[str]) -> Optional[str]:
    """Chuẩn hóa mọi định dạng proxy thành URL requests hợp lệ."""
    if not proxy_str:
        return None
    px = str(proxy_str).strip()
    if not px:
        return None
    if not px.startswith(("http://", "https://", "socks5://", "socks5h://")):
        parts = px.split(":")
        if len(parts) == 4:
            return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        elif len(parts) == 2:
            return f"http://{parts[0]}:{parts[1]}"
        else:
            return f"http://{px}"
    return px


# ==============================================================================
# ============================ CẤU HÌNH CHÍNH ==================================
# ==============================================================================
PROXY = "http://rx9l1256575-region-TH:pwma6u1k@us.arxlabs.io:3010"
PROXY_XOAY_KEY = None #"OQuTChILlobJuvzbsRwDBd"

KIOT_API_TOKEN = "88992b2f40694e62bc39840db8d25772"
KIOT_PROXY_KEY = "Ke4161bf08e304ba893d588e068e4df06"

CUSTOM_EMAIL = None
HOTMAIL_REFRESH_TOKEN = "M.C508_SN1.0.U.MsaArtifacts.-CuCkG8Tro62CBejGB7WGk6EZZLC*FI0cUkN2SGzpI8SaONrdmsXyxEp8pVJWK1lKjEg8BwsT4lDVwRYjg6XnkxB2Iuosp5RJQN35Ak!cG6eaN*0DB!*E6QmK5jCjW8r6cMTUI0tHqFLRmkhjHuoIvJqxzbS7ppdzPtNYOG4ZH28Fzhi*Je5XVy*14eTL0OIM1nqnHTRVvP*DblZF7!xgyBe9ZWDwHT7wJvQ1tPUxgMFqIPxBc8j9XCicRoMpX2kGppruWQtzyhVwAccghSvZhENkZo!AvGFhkUlLX7vvWg2lzPfwe4gyad3VLdotNmEclPGYA3uCmSwrHXvIscq45SQLf2gEILaMoyZhFuuefAej"
HOTMAIL_CLIENT_ID = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"

#------ PHẦN 1: MODULE 4G/WIFI — KIỂM TRA MẠNG THẬT (KHÔNG PROXY) ------
# ==============================================================================
# MODULE 4G/WIFI — KIỂM TRA MẠNG THẬT (KHÔNG PROXY)
# Dùng khi user muốn reg bằng mạng data 4G/5G hoặc WiFi thật của máy.
# Session chạy DIRECT 100%: trust_env=False + proxies={} để không dính proxy hệ thống.
# ==============================================================================

def check_real_network_ip(timeout: int = 8) -> Dict[str, Any]:
    """
    Kiểm tra IP + quốc gia + ISP của mạng THẬT (4G/WiFi) — KHÔNG qua proxy.
    Trả về dict: {ip, country, countryCode, timezone, isp, ok}
    """
    result = {
        "ip": "unknown",
        "country": "Unknown",
        "countryCode": "TH",
        "timezone": "Asia/Bangkok",
        "isp": "Unknown",
        "ok": False,
    }

    probe = requests.Session()
    probe.trust_env = False
    probe.proxies = {}

    endpoints = [
        ("http://ip-api.com/json/?fields=status,country,countryCode,timezone,isp,query", "ip-api"),
        ("https://ipinfo.io/json", "ipinfo"),
        ("https://api.myip.com", "myip"),
    ]
    for url, kind in endpoints:
        try:
            r = probe.get(url, timeout=timeout)
            if r.status_code != 200:
                continue
            data = r.json()
            if not isinstance(data, dict):
                continue

            if kind == "ip-api":
                if data.get("status") != "success":
                    continue
                result["ip"] = data.get("query") or result["ip"]
                result["country"] = data.get("country") or result["country"]
                result["countryCode"] = (data.get("countryCode") or "TH").upper()
                result["timezone"] = data.get("timezone") or result["timezone"]
                result["isp"] = data.get("isp") or result["isp"]

            elif kind == "ipinfo":
                cc = (data.get("country") or "").upper()
                if len(cc) == 2:
                    result["countryCode"] = cc
                result["ip"] = data.get("ip") or result["ip"]
                result["timezone"] = data.get("timezone") or result["timezone"]
                result["country"] = data.get("country") or result["country"]

            elif kind == "myip":
                cc = (data.get("country") or "").upper()
                if len(cc) == 2:
                    result["countryCode"] = cc
                result["ip"] = data.get("ip") or result["ip"]
                result["country"] = data.get("country") or result["country"]

            result["ok"] = True
            return result
        except Exception:
            continue

    return result


def print_network_info_direct() -> Dict[str, Any]:
    """In thông tin mạng thật (4G/5G/WiFi) của máy để user kiểm tra trước khi chạy."""
    try:
        AppLogger.section("KIỂM TRA MẠNG THẬT (4G/5G/WIFI)")
    except Exception:
        print("=== KIỂM TRA MẠNG THẬT (4G/5G/WIFI) ===")

    try:
        AppLogger.wait("Đang kiểm tra IP thật (không qua proxy)...")
    except Exception:
        print("[*] Đang kiểm tra IP thật...")

    net = check_real_network_ip()
    if net["ok"]:
        try:
            AppLogger.success(f"✅ IP thật: {net['ip']}")
            AppLogger.geo(
                f"Quốc gia: {net['country']} ({net['countryCode']}) | TZ: {net['timezone']}"
            )
            AppLogger.info(f"Nhà mạng (ISP): {net['isp']}")
        except Exception:
            print(f"[+] IP thật: {net['ip']} | {net['country']} ({net['countryCode']}) | ISP: {net['isp']}")
    else:
        try:
            AppLogger.warn("⚠️ Không detect được IP thật (mạng chậm hoặc API bị block).")
            AppLogger.warn("    → Fallback country = TH, sẽ dùng SĐT mồi Thái Lan.")
        except Exception:
            print("[!] Không detect được IP thật → fallback country=TH")

    return net


def _local_config_path(filename: str) -> str:
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = xdg if os.path.isabs(xdg) else os.path.join(home, ".config")
    return os.path.join(base, "RegFbSms1", filename)


def _read_local_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Expected an object")
    return data


def _save_local_config(path: str, data: dict) -> bool:
    temp_path = None
    try:
        directory = os.path.dirname(path)
        os.makedirs(directory, mode=0o700, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         prefix=".settings-", delete=False) as f:
            temp_path = f.name
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
        return True
    except OSError:
        print(f"[!] Không ghi được {os.path.basename(path)}. Cài đặt chỉ dùng trong phiên này.")
        return False
    finally:
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def _network_config() -> dict:
    path = _local_config_path("network_config.json")
    try:
        return _read_local_config(path)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        print("[!] Không đọc được cấu hình mạng đã lưu.")
        return {}


def _choose_proxy_file() -> Optional[str]:
    path = _local_config_path("network_config.json")
    cfg = _network_config()
    saved = str(cfg.get("proxy_file") or "")
    hint = "dùng file đã lưu" if saved else "bỏ qua"
    value = input(f"[?] Đường dẫn file proxy (Enter = {hint}, - = bỏ file): ").strip().strip('"').strip("'")
    if value == "-":
        cfg.pop("proxy_file", None)
        _save_local_config(path, cfg)
        return None
    chosen = value or saved
    if not chosen:
        return None
    chosen = os.path.abspath(os.path.expanduser(chosen))
    if not os.path.isfile(chosen):
        print(f"[-] Không thấy file: {chosen}")
        return None
    if value and chosen != saved:
        cfg["proxy_file"] = chosen
        _save_local_config(path, cfg)
    return chosen


def resolve_network_choice_interactive(default_proxy: Optional[str] = None) -> Tuple[Optional[str], str]:
    path = _local_config_path("network_config.json")
    cfg = _network_config()
    saved_mode = cfg.get("mode")
    saved_proxy = str(cfg.get("proxy") or "").strip()

    AppLogger.section("CHỌN KIỂU MẠNG KẾT NỐI")
    safe_print(color("  1. Proxy Residential (Arxlabs / Kiot / file proxy)", C.GRAY))
    safe_print(color("  2. 4G/5G/WiFi THẬT của máy (DIRECT — KHÔNG proxy)", C.LIME))
    default_choice = "2" if saved_mode == "direct" else "1"
    choice = input(color(f"[?] Chọn kiểu mạng (Enter = {default_choice}): ", C.BWHITE + C.BOLD)).strip()
    if choice == "2" or (not choice and saved_mode == "direct"):
        if saved_mode != "direct":
            cfg["mode"] = "direct"
            _save_local_config(path, cfg)
        print_network_info_direct()
        AppLogger.success("Đã chọn mode: 4G/WiFi DIRECT (0 byte proxy)")
        return None, "4G/WiFi (Direct)"

    px_in = ""
    if choice or saved_mode != "proxy":
        hint = "proxy đã lưu" if saved_proxy else "proxy mặc định"
        px_in = input(color(f"[?] Nhập proxy (Enter = {hint}): ", C.BWHITE)).strip()
    proxy = px_in or saved_proxy or default_proxy
    if proxy:
        if saved_mode != "proxy" or (px_in and px_in != saved_proxy):
            cfg["mode"] = "proxy"
            if px_in:
                cfg["proxy"] = px_in
            _save_local_config(path, cfg)
        return proxy, "Proxy (đã cấu hình)"

    AppLogger.warn("Không có proxy → sẽ chạy DIRECT (mạng thật máy)")
    print_network_info_direct()
    return None, "4G/WiFi (Direct — proxy trống)"
#------ HẾT PHẦN 1 MODULE ------

# ================= CẤU HÌNH GMAIL94.COM =================
GMAIL94_TOKEN = "fd1c1abe05a79fff8678e4541d12f835f1f92bb1fae22918eef090183b5055ab"

MAX_REG_PER_GMAIL = 4

# ==============================================================================
# CODETEXTNOW.SITE — API THUÊ SỐ SMS V6 (REG THẲNG, KHÔNG MỒI)
# ==============================================================================
CODETEXTNOW_API_KEY = "f196fac48c2f44f28cd1d516e656bd1a"
CODETEXTNOW_BASE = "https://codetextnow.site/api"
CODETEXTNOW_DEFAULT_SERVICE_ID = 6000001
CODETEXTNOW_DEFAULT_SERVICE_NAME = "Facebook US V6"


class CodeTextNowSMS:
    """Client API Codetextnow SIM V6 — thuê số + nhận OTP."""

    def __init__(self, api_key: str = None):
        self.api_key = (api_key or CODETEXTNOW_API_KEY or "").strip()
        self.base = CODETEXTNOW_BASE
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "User-Agent": "RegFB-SMS/1.0"})
        self.last_request_id = None
        self.last_phone = None
        self.last_service_id = None

    def _get(self, params: dict, timeout: int = 20) -> dict:
        params = dict(params or {})
        params["key"] = self.api_key
        r = self.session.get(self.base, params=params, timeout=timeout)
        try:
            return r.json()
        except Exception:
            return {"success": False, "message": f"Non-JSON: {r.text[:200]}", "raw": r.text[:300]}

    def get_balance(self):
        data = self._get({"action": "get_balance"})
        if isinstance(data, dict) and "balance" in data:
            return True, data.get("balance"), data
        return False, None, data

    def get_services(self):
        data = self._get({"action": "get_all_services_v6"})
        if isinstance(data, list):
            return True, data
        if isinstance(data, dict) and "message" in data:
            return False, data
        return False, data

    def rent_number(self, service_id: int = None):
        sid = int(service_id or CODETEXTNOW_DEFAULT_SERVICE_ID)
        data = self._get({"action": "get_number_v6", "id": sid})
        if not isinstance(data, dict):
            return False, None, None, data
        if data.get("success") is True or data.get("phone") or data.get("number"):
            phone = data.get("phone") or data.get("number")
            req_id = data.get("request_id") or data.get("lease_id") or data.get("id")
            self.last_request_id = req_id
            self.last_phone = phone
            self.last_service_id = sid
            return True, phone, req_id, data
        return False, None, None, data

    def get_otp(self, request_id=None, prefer_latest: bool = True):
        rid = request_id or self.last_request_id
        if not rid:
            return False, None, {"message": "missing request_id"}
        data = self._get({"action": "get_code_v6", "id": rid})
        if not isinstance(data, dict):
            return False, None, data

        code_flag = str(data.get("code") or "")
        otp_code = data.get("otp_code") or data.get("otp") or ""
        if isinstance(otp_code, str) and otp_code.strip().lower() in ("", "is_coming", "null", "none"):
            otp_code = ""
        otp_list = data.get("otp_list") or []
        if not isinstance(otp_list, list):
            otp_list = []

        chosen = None
        if otp_list:
            chosen = str(otp_list[-1] if prefer_latest else otp_list[0]).strip()
        elif otp_code:
            parts = [x.strip() for x in str(otp_code).replace(";", ",").split(",") if x.strip().isdigit()]
            if parts:
                chosen = parts[-1] if prefer_latest else parts[0]
            elif str(otp_code).strip().isdigit():
                chosen = str(otp_code).strip()

        if chosen and chosen.isdigit() and 4 <= len(chosen) <= 8:
            return True, chosen, data
        return False, None, data

    def wait_otp(self, request_id=None, max_wait: int = 120, poll_every: float = 3.0,
                 resend_callback=None, resend_times: int = 4, resend_interval: float = 12.0):
        rid = request_id or self.last_request_id
        if not rid:
            return None
        start = time.time()
        resend_done = 0
        next_resend_at = start + 8.0
        attempt = 0
        while time.time() - start < max_wait:
            attempt += 1
            ok, otp, raw = self.get_otp(rid)
            if ok and otp:
                return otp

            now = time.time()
            if resend_callback and resend_done < resend_times and now >= next_resend_at:
                try:
                    AppLogger.mail(f"[SMS] Gửi lại mã OTP Facebook lần {resend_done + 1}/{resend_times}...")
                    resend_callback()
                except Exception as e:
                    AppLogger.warn(f"[SMS] Resend lỗi: {e}")
                resend_done += 1
                next_resend_at = now + resend_interval

            left = int(max_wait - (time.time() - start))
            status = ""
            if isinstance(raw, dict):
                status = raw.get("code") or raw.get("status") or ""
            print(f"    ... Chờ OTP SMS ({attempt}) còn ~{left}s | status={status}", end="\r")
            time.sleep(poll_every)
        print()
        return None


def pick_sms_service_interactive(api_key: str = None) -> tuple:
    client = CodeTextNowSMS(api_key=api_key)
    ok_bal, bal, _ = client.get_balance()
    if ok_bal:
        print(f"[+] Codetextnow số dư: {bal}")
    else:
        print(f"[-] Không lấy được số dư Codetextnow (key có thể sai). Vẫn tiếp tục...")

    ok, services = client.get_services()
    default_id = CODETEXTNOW_DEFAULT_SERVICE_ID
    default_name = CODETEXTNOW_DEFAULT_SERVICE_NAME

    if not ok or not isinstance(services, list) or not services:
        print(f"[*] Không tải được danh sách dịch vụ. Dùng mặc định: {default_name} (id={default_id})")
        return default_id, default_name

    services_sorted = sorted(
        services,
        key=lambda s: (0 if "facebook" in str(s.get("name", "")).lower() else 1, str(s.get("name", ""))),
    )
    print("\n" + "-" * 72)
    print("📌 DANH SÁCH DỊCH VỤ SMS V6 (Codetextnow):")
    print(f"{'#':<4} {'ID':<10} {'Tên':<28} {'Giá':>6} {'Kho':>5} {'Reuse':>5}")
    fb_indexes = []
    for i, s in enumerate(services_sorted, 1):
        sid = s.get("id")
        name = str(s.get("name", ""))[:28]
        price = s.get("price", "-")
        count = s.get("count", 0)
        reuse = s.get("reuse_count", 0)
        mark = " ← mặc định" if sid == default_id else ""
        print(f"{i:<4} {sid:<10} {name:<28} {price:>6} {count:>5} {reuse:>5}{mark}")
        if "facebook" in name.lower():
            fb_indexes.append(i)
    print("-" * 72)
    print("  Enter = mặc định Facebook US V6 (nếu có trong list)")
    choice = input("[?] Chọn số thứ tự dịch vụ (hoặc nhập ID dịch vụ): ").strip()
    if not choice:
        for s in services_sorted:
            if s.get("id") == default_id:
                return int(s["id"]), str(s.get("name", default_name))
        for s in services_sorted:
            if "facebook" in str(s.get("name", "")).lower():
                return int(s["id"]), str(s.get("name"))
        s0 = services_sorted[0]
        return int(s0["id"]), str(s0.get("name", "Unknown"))

    if choice.isdigit():
        num = int(choice)
        if 1 <= num <= len(services_sorted):
            s = services_sorted[num - 1]
            return int(s["id"]), str(s.get("name", ""))
        for s in services_sorted:
            if int(s.get("id", 0)) == num:
                return num, str(s.get("name", ""))
        return num, f"Service#{num}"

    print(f"[*] Lựa chọn không hợp lệ → mặc định {default_name}")
    return default_id, default_name


# ==============================================================================
# OTPTRUST.COM — API THUÊ EMAIL NHẬN OTP
# ==============================================================================
OTPTRUST_API_KEY = ""
OTPTRUST_BASE = "https://otptrust.com"
OTPTRUST_DEFAULT_PROVIDER = "outlook"

# ==============================================================================
# TELEGRAM — GỬI ACC LIVE VỀ BOT
# ==============================================================================
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
TELEGRAM_ENABLED = False


def telegram_load_config():
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED
    path = _local_config_path("telegram_config.json")
    legacy_paths = (os.path.join(os.path.dirname(os.path.realpath(__file__)), "telegram_config.json"),
                    os.path.join(os.getcwd(), "telegram_config.json"))
    for candidate in dict.fromkeys((path, *legacy_paths)):
        try:
            data = _read_local_config(candidate)
        except FileNotFoundError:
            continue
        except (OSError, ValueError):
            print("[!] Không đọc được tệp cấu hình Telegram.")
            continue
        TELEGRAM_BOT_TOKEN = str(data.get("bot_token") or "").strip()
        TELEGRAM_CHAT_ID = str(data.get("chat_id") or "").strip()
        TELEGRAM_ENABLED = bool(data.get("enabled", True)) and bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        if candidate != path and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            _save_local_config(path, data)
        return candidate, data
    return None, {}


def telegram_save_config(bot_token: str, chat_id: str, enabled: bool = True):
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED
    TELEGRAM_BOT_TOKEN = (bot_token or "").strip()
    TELEGRAM_CHAT_ID = str(chat_id or "").strip()
    TELEGRAM_ENABLED = bool(enabled) and bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    path = _local_config_path("telegram_config.json")
    saved = _save_local_config(path, {"bot_token": TELEGRAM_BOT_TOKEN,
                                     "chat_id": TELEGRAM_CHAT_ID, "enabled": TELEGRAM_ENABLED})
    return path if saved else None


def _configure_telegram_interactive() -> bool:
    """Return True only when the user enabled or edited Telegram for this run."""
    path, _ = telegram_load_config()
    hint = ("Enter = giữ BẬT" if TELEGRAM_ENABLED else "Enter = giữ TẮT") if path else "Enter = nhập cấu hình"
    choice = input(color(f"\n[?] Telegram ({hint}, y = bật/sửa, n = tắt): ", C.BWHITE)).strip().lower()
    if choice in ("n", "no", "0"):
        telegram_save_config(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, enabled=False)
        AppLogger.warn("Telegram: TẮT")
        return False
    if path and not choice:
        AppLogger.info(f"Telegram: {'BẬT (dùng cấu hình đã lưu)' if TELEGRAM_ENABLED else 'TẮT'}")
        return False

    tok_hint = " (Enter = dùng token đã lưu)" if TELEGRAM_BOT_TOKEN else ""
    chat_hint = " (Enter = dùng Chat ID đã lưu)" if TELEGRAM_CHAT_ID else ""
    token = input(color(f"[?] Bot Token{tok_hint}: ", C.BWHITE)).strip() or TELEGRAM_BOT_TOKEN
    chat = input(color(f"[?] Chat ID{chat_hint}: ", C.BWHITE)).strip() or TELEGRAM_CHAT_ID
    if not (token and chat):
        AppLogger.warn("Thiếu Bot Token hoặc Chat ID. Telegram không được bật.")
        return False
    saved = telegram_save_config(token, chat, enabled=True)
    AppLogger.success("Telegram: BẬT (đã lưu)" if saved else "Telegram: BẬT (chỉ phiên này)")
    return True


def send_telegram_live(
    uid: str,
    password: str,
    cookie: str = "",
    email: str = "",
    phone: str = "",
    mode: str = "",
    totp: str = "",
    eaau_token: str = "",
    extra: str = "",
) -> bool:
    if not TELEGRAM_ENABLED:
        return False
    token = (TELEGRAM_BOT_TOKEN or "").strip()
    chat_id = str(TELEGRAM_CHAT_ID or "").strip()
    if not token or not chat_id:
        return False
    try:
        lines = [
            f"✅ <b>LIVE</b> | <code>{mode or 'FB'}</code>",
            f"🆔 <code>{uid}</code>",
            f"🔑 <code>{password}</code>",
        ]
        if email:
            lines.append(f"📧 <code>{email}</code>")
        if phone:
            lines.append(f"📱 <code>{phone}</code>")
        if totp:
            lines.append(f"🔐 2FA: <code>{totp}</code>")
        if eaau_token:
            lines.append(f"🎫 Token: <code>{eaau_token}</code>")
        if cookie:
            lines.append(f"🍪 Cookie:\n<pre>{cookie[:3500]}</pre>")
        copy_line = f"{uid}|{password}"
        if totp:
            copy_line += f"|{totp}"
        if cookie:
            copy_line += f"|{cookie[:500]}"
        if eaau_token:
            copy_line += f"|{eaau_token}"
        lines.append(f"📋 <code>{copy_line[:900]}</code>")
        if extra:
            lines.append(str(extra)[:300])

        text = "\n".join(lines)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        r = requests.post(url, json=payload, timeout=15)
        ok = r.status_code == 200 and (r.json() or {}).get("ok") is True
        if ok:
            try:
                AppLogger.success("Đã gửi LIVE → Telegram")
            except Exception:
                pass
        else:
            try:
                AppLogger.warn(f"Telegram gửi fail: {r.status_code} {r.text[:120]}")
            except Exception:
                pass
        return bool(ok)
    except Exception as e:
        try:
            AppLogger.warn(f"Telegram lỗi: {e}")
        except Exception:
            pass
        return False


class OTPTrustEmail:
    """Client thuê email + lấy OTP từ otptrust.com."""

    def __init__(self, api_key: str = None):
        self.api_key = (api_key or OTPTRUST_API_KEY or "").strip()
        self.base = OTPTRUST_BASE.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RegFB-OTPTrust/1.0",
        })
        self.last_order_id = None
        self.last_email = None

    def _url(self, path: str) -> str:
        return f"{self.base}{path}"

    def list_services(self, domain: str = None):
        params = {"api_key": self.api_key}
        if domain:
            params["domain"] = domain
        try:
            r = self.session.get(self._url("/api/v1/email/services"), params=params, timeout=20)
            data = r.json()
        except Exception as e:
            return False, str(e)
        if isinstance(data, dict) and data.get("success"):
            return True, data.get("data") or []
        return False, data

    def rent(self, service_id: int, provider: str = "outlook"):
        payload = {
            "service_id": int(service_id),
            "provider": str(provider).lower().strip(),
        }
        params = {"api_key": self.api_key}
        try:
            r = self.session.post(
                self._url("/api/v1/email/rent"),
                params=params,
                json=payload,
                timeout=30,
            )
            data = r.json()
        except Exception as e:
            return False, None, None, str(e)
        if isinstance(data, dict) and data.get("success"):
            d = data.get("data") or {}
            order_id = d.get("order_id") or d.get("id")
            email = d.get("email")
            self.last_order_id = order_id
            self.last_email = email
            return True, email, order_id, data
        msg = (data.get("message") if isinstance(data, dict) else None) or data
        return False, None, None, msg

    def get_order(self, order_id=None):
        oid = order_id or self.last_order_id
        if not oid:
            return False, None, {"message": "missing order_id"}
        params = {"api_key": self.api_key}
        try:
            r = self.session.get(self._url(f"/api/v1/email/orders/{oid}"), params=params, timeout=20)
            data = r.json()
        except Exception as e:
            return False, None, str(e)
        if isinstance(data, dict) and data.get("success"):
            d = data.get("data") or {}
            otp = d.get("otp")
            if otp is not None and str(otp).strip() and str(otp).lower() not in ("null", "none"):
                return True, str(otp).strip(), d
            return False, None, d
        return False, None, data

    def reorder(self, order_id=None):
        oid = order_id or self.last_order_id
        if not oid:
            return False, "missing order_id"
        params = {"api_key": self.api_key}
        try:
            r = self.session.post(self._url(f"/api/v1/email/orders/{oid}/reorder"), params=params, timeout=20)
            data = r.json()
        except Exception as e:
            return False, str(e)
        if isinstance(data, dict) and data.get("success"):
            return True, data.get("message") or "Reorder OK"
        return False, (data.get("message") if isinstance(data, dict) else data)

    def cancel(self, order_id=None):
        oid = order_id or self.last_order_id
        if not oid:
            return False, "missing order_id"
        params = {"api_key": self.api_key}
        try:
            r = self.session.post(self._url(f"/api/v1/email/orders/{oid}/cancel"), params=params, timeout=20)
            data = r.json()
        except Exception as e:
            return False, str(e)
        if isinstance(data, dict) and data.get("success"):
            return True, data.get("message") or "Cancelled"
        return False, (data.get("message") if isinstance(data, dict) else data)

    def wait_otp(self, order_id=None, max_wait: int = 180, poll_every: float = 3.0,
                 resend_callback=None, resend_times: int = 4, resend_interval: float = 15.0,
                 reorder_on_resend: bool = True):
        oid = order_id or self.last_order_id
        if not oid:
            return None
        start = time.time()
        resend_done = 0
        next_resend_at = start + 10.0
        attempt = 0
        while time.time() - start < max_wait:
            attempt += 1
            ok, otp, raw = self.get_order(oid)
            if ok and otp and otp.isdigit() and 4 <= len(otp) <= 8:
                return otp
            if ok and otp:
                m = re.search(r"(\\d{5,8})", str(otp))
                if m:
                    return m.group(1)

            now = time.time()
            if resend_callback and resend_done < resend_times and now >= next_resend_at:
                try:
                    AppLogger.mail(f"[OTPTrust] Resend OTP Facebook lần {resend_done + 1}/{resend_times}...")
                    resend_callback()
                except Exception as e:
                    AppLogger.warn(f"[OTPTrust] Resend FB lỗi: {e}")
                if reorder_on_resend:
                    try:
                        rok, rmsg = self.reorder(oid)
                        AppLogger.mail(f"[OTPTrust] Reorder: {rmsg}")
                    except Exception as e:
                        AppLogger.warn(f"[OTPTrust] Reorder lỗi: {e}")
                resend_done += 1
                next_resend_at = now + resend_interval

            status = ""
            if isinstance(raw, dict):
                status = raw.get("status") or ""
            left = int(max_wait - (time.time() - start))
            print(f"    ... Chờ OTP email ({attempt}) còn ~{left}s | status={status}", end="\r")
            time.sleep(poll_every)
        print()
        return None


def pick_otptrust_service_interactive(api_key: str) -> tuple:
    client = OTPTrustEmail(api_key=api_key)
    print("\\n" + "-" * 72)
    print("📌 CHỌN PROVIDER EMAIL (OTPTrust):")
    print("    1. Outlook  (catalog Hotmail/Outlook)")
    print("    2. Hotmail  (catalog Hotmail/Outlook)")
    print("    3. Gmail    (catalog riêng)")
    print("    4. iCloud   (catalog riêng)")
    print("-" * 72)
    p_in = input("[?] Provider (1-4, Enter=1 Outlook): ").strip() or "1"
    provider_map = {"1": "outlook", "2": "hotmail", "3": "gmail", "4": "icloud"}
    provider = provider_map.get(p_in, "outlook")

    domain = None
    if provider in ("gmail", "icloud"):
        domain = provider

    ok, services = client.list_services(domain=domain)
    if not ok or not isinstance(services, list) or not services:
        print(f"[-] Không lấy được danh sách dịch vụ: {services}")
        return 1, "Facebook", provider

    services_sorted = sorted(
        services,
        key=lambda s: (0 if "facebook" in str(s.get("name", "") or s.get("service_code", "")).lower() else 1,
                       str(s.get("name", ""))),
    )
    print("\\n" + "-" * 72)
    print(f"📌 DỊCH VỤ EMAIL OTPTrust ({provider}):")
    print(f"{'#':<4} {'ID':<8} {'Tên':<24} {'Giá VN':>10} {'Kho':>8}")
    for i, s in enumerate(services_sorted, 1):
        sid = s.get("id")
        name = str(s.get("name") or s.get("service_code") or "")[:24]
        price = s.get("price_vn") or s.get("price_us") or "-"
        if "available_hotmail" in s or "available_outlook" in s:
            stock = f"H:{s.get('available_hotmail', '-')} O:{s.get('available_outlook', '-')}"
        else:
            av = s.get("available")
            stock = "∞" if av is None else str(av)
        mark = " ← FB" if "facebook" in name.lower() or str(s.get("service_code", "")).lower() == "facebook" else ""
        print(f"{i:<4} {sid:<8} {name:<24} {str(price):>10} {stock:>8}{mark}")
    print("-" * 72)
    print("  Enter = Facebook (nếu có)")
    choice = input("[?] Chọn số thứ tự hoặc ID: ").strip()

    def _pick_facebook():
        for s in services_sorted:
            code = str(s.get("service_code", "")).lower()
            name = str(s.get("name", "")).lower()
            if code == "facebook" or "facebook" in name:
                return int(s["id"]), str(s.get("name") or "Facebook"), provider
        s0 = services_sorted[0]
        return int(s0["id"]), str(s0.get("name") or "Unknown"), provider

    if not choice:
        return _pick_facebook()
    if choice.isdigit():
        num = int(choice)
        if 1 <= num <= len(services_sorted):
            s = services_sorted[num - 1]
            return int(s["id"]), str(s.get("name") or ""), provider
        for s in services_sorted:
            if int(s.get("id", 0)) == num:
                return num, str(s.get("name") or ""), provider
        return num, f"Service#{num}", provider
    return _pick_facebook()


# --- PHẦN 2: MODULE FB EMAIL MANAGER (THÊM MAIL ẢO & RE-AUTH ĐÁ GMAIL) ---

class FacebookEmailManagerAPI:
    """
    Quản lý thêm Email ảo và đá / xóa Gmail cũ 100% bằng HTTP requests.post() thuần túy.
    """
    GRAPHQL_URL = "https://accountscenter.facebook.com/api/graphql/"
    AC_BASE_URL = "https://accountscenter.facebook.com"
    
    DOC_ID_ADD = "24024219683917897"
    DOC_ID_VERIFY = "24829010190041566"
    DOC_ID_DELETE = "29312208161761302"
    DOC_ID_REAUTH = "24388548824069198"
    DOC_ID_QUERY = "24648808718130740"

    def __init__(self, session: requests.Session, uid: str, ua: Optional[str] = None, proxy: Optional[str] = None):
        self.session = session
        self.uid = str(uid)
        self.ua = ua or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        
        norm_px = format_proxy_url(proxy)
        if norm_px:
            self.proxy = norm_px
            self.proxies = {"http": norm_px, "https": norm_px}
        elif getattr(session, 'proxies', None):
            self.proxy = session.proxies.get('http') or session.proxies.get('https')
            self.proxies = session.proxies
        else:
            self.proxy = None
            self.proxies = None
        
        self.fb_dtsg: Optional[str] = None
        self.lsd: Optional[str] = None

    @staticmethod
    def compute_jazoest(dtsg: str) -> str:
        if not dtsg:
            return "2"
        return f"2{sum(ord(c) for c in str(dtsg))}"

    def get_security_tokens(self) -> Tuple[Optional[str], Optional[str]]:
        if self.fb_dtsg and self.lsd:
            return self.fb_dtsg, self.lsd

        headers = {
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Dest': 'document',
        }

        endpoints = [
            f"{self.AC_BASE_URL}/personal_info/contact_points/",
            f"{self.AC_BASE_URL}/password_and_security/two_factor",
            f"{self.AC_BASE_URL}/",
            "https://www.facebook.com/"
        ]

        for target_url in endpoints:
            try:
                r = self.session.get(target_url, headers=headers, proxies=self.proxies, timeout=10)
                html = r.text or ""
                if not self.fb_dtsg:
                    dtsg_m = (
                        re.search(r'"DTSGInitialData"[^>]*?"token":"([^"]+)"', html) or
                        re.search(r'"DTSGInitialData",\[\],{"token":"([^"]+)"}', html) or
                        re.search(r'"f":"([^"]+:\d+:\d+)"', html) or
                        re.search(r'"dtsg"[^>]*?"token":"([^"]+)"', html) or
                        re.search(r'name="fb_dtsg"\s+value="([^"]+)"', html)
                    )
                    if dtsg_m:
                        self.fb_dtsg = dtsg_m.group(1)

                if not self.lsd:
                    lsd_m = (
                        re.search(r'\["LSD",\[\],\{"token":"([^"]+)"', html) or
                        re.search(r'"LSD",\[\],{"token":"([^"]+)"}', html) or
                        re.search(r'name="lsd"\s+value="([^"]+)"', html) or
                        re.search(r'"lsd":\s*"([^"]+)"', html)
                    )
                    if lsd_m:
                        self.lsd = lsd_m.group(1)

                if self.fb_dtsg and self.lsd:
                    break
            except Exception as e:
                pass

        return self.fb_dtsg, self.lsd

    def _build_gql_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        return {
            'User-Agent': self.ua,
            'Origin': self.AC_BASE_URL,
            'Referer': referer or f"{self.AC_BASE_URL}/personal_info/contact_points/",
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-fb-lsd': self.lsd or '',
            'x-asbd-id': '359341',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
        }

    def _post_graphql(self, friendly_name: str, doc_id: str, variables: dict, referer: Optional[str] = None) -> Dict[str, Any]:
        dtsg, lsd = self.get_security_tokens()
        if not dtsg or not lsd:
            return {'success': False, 'error': 'Không trích xuất được fb_dtsg hoặc lsd'}

        headers = self._build_gql_headers(referer=referer)
        data = {
            'av': self.uid,
            '__user': self.uid,
            '__a': '1',
            '__req': '1',
            'fb_dtsg': dtsg,
            'jazoest': self.compute_jazoest(dtsg),
            'lsd': lsd,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': friendly_name,
            'variables': json.dumps(variables, ensure_ascii=False),
            'doc_id': doc_id,
            'server_timestamps': 'true'
        }

        try:
            resp = self.session.post(
                self.GRAPHQL_URL,
                data=data,
                headers=headers,
                proxies=self.proxies,
                timeout=25
            )
            raw_text = resp.text.replace("for (;;);", "", 1).strip()
            res_json = json.loads(raw_text)
            return {'success': True, 'data': res_json, 'raw': raw_text}
        except Exception as e:
            return {'success': False, 'error': f'Lỗi gọi GraphQL {friendly_name}: {e}'}

    def add_email(self, new_email: str, account_password: Optional[str] = None) -> Dict[str, Any]:
        print(f"[*] [API POST] Gửi yêu cầu thêm Email mới: {new_email}...")
        variables = {
            "client_mutation_id": f"mutation_id_{int(time.time() * 1000)}",
            "contact_point": str(new_email).strip(),
            "contact_point_type": "EMAIL",
            "country": "",
            "family_device_id": str(uuid.uuid4()),
            "selected_accounts": [self.uid]
        }
        ref = f"{self.AC_BASE_URL}/youraccount/contact_points/?contact_point_type=email&dialog_type=add_contact_point"
        res = self._post_graphql("FXAccountsCenterAddContactPointMutation", self.DOC_ID_ADD, variables, referer=ref)

        raw_text = res.get('raw', '')
        if ("SecuredAction" in raw_text or "2136001" in raw_text) and account_password:
            print("[+] [Add Email] Phát hiện SecuredAction Challenge! Tự động Re-Authenticate mật khẩu...")
            reauth_res = self.reauthenticate_password(account_password, category_name="SecuredActionAddMetaContactPointCategory")
            if reauth_res.get('success'):
                print("[+] [Add Email] Re-Auth thành công! Gửi lại yêu cầu thêm email...")
                time.sleep(1)
                variables["client_mutation_id"] = f"mutation_id_{int(time.time() * 1000)}"
                res = self._post_graphql("FXAccountsCenterAddContactPointMutation", self.DOC_ID_ADD, variables, referer=ref)

        if not res.get('success'):
            return res

        data = res.get('data', {})
        add_result = data.get('data', {}).get('xfb_add_contact_point', {})
        is_success = add_result.get('success', False)
        err_text = add_result.get('error_text')
        
        cp_results = add_result.get('add_cp_result', [])
        if is_success is True and cp_results:
            first_mut = cp_results[0].get('mutation_data', {})
            if first_mut.get('success') is True:
                return {
                    'success': True,
                    'normalized_email': add_result.get('normalized_contact_point', new_email),
                    'details': add_result
                }
            elif first_mut.get('error_text'):
                err_text = first_mut.get('error_text')

        errors = data.get('errors', [])
        if not err_text and errors:
            err_text = errors[0].get('message') or errors[0].get('summary') or str(errors[0])
        err_msg = err_text or data.get('errorDescription')
        if not err_msg:
            err_msg = f"FB Response: {str(raw_text)[:200]}"
        return {'success': False, 'error': err_msg, 'data': data, 'raw': raw_text}

    def verify_email_otp(self, email: str, pin_code: str) -> Dict[str, Any]:
        print(f"[*] [API POST] Xác thực mã OTP [{pin_code}] cho Email: {email}...")
        variables = {
            "client_mutation_id": f"mutation_id_{int(time.time() * 1000)}",
            "contact_point": str(email).strip(),
            "contact_point_event_type": "ADD",
            "contact_point_type": "EMAIL",
            "family_device_id": str(uuid.uuid4()),
            "normalized_contact_point_to_replace": None,
            "pin_code": str(pin_code).strip(),
            "selected_accounts": [self.uid]
        }
        ref = f"{self.AC_BASE_URL}/youraccount/contact_points/?contact_point_type=email&dialog_type=add_contact_point"
        res = self._post_graphql("FXAccountsCenterContactPointConfirmationDialogVerifyContactPointMutation", self.DOC_ID_VERIFY, variables, referer=ref)
        
        if not res.get('success'):
            return res

        data = res.get('data', {})
        verify_list = data.get('data', {}).get('xfb_verify_contact_point', [])
        if isinstance(verify_list, list) and verify_list:
            mut_data = verify_list[0].get('mutation_data', {})
            if mut_data.get('success') is True:
                return {'success': True, 'data': verify_list}
            else:
                return {'success': False, 'error': mut_data.get('error_text', 'Mã xác thực không hợp lệ'), 'data': data}

        errors = data.get('errors', [])
        err_msg = errors[0].get('message') if errors else data.get('errorDescription', 'Mã xác thực không hợp lệ')
        return {'success': False, 'error': err_msg, 'data': data}

    def reauthenticate_password(self, password: str, category_name: str = "SecuredActionDeleteMetaContactPointCategory") -> Dict[str, Any]:
        print(f"[*] [API POST] Đang giải SecuredAction Challenge bằng mật khẩu...")
        timestamp_now = int(time.time())
        pwd_val = f"#PWD_BROWSER:0:{timestamp_now}:{password}"
        variables = {
            "input": {
                "category_name": category_name,
                "password": {
                    "sensitive_string_value": pwd_val
                },
                "actor_id": str(self.uid),
                "client_mutation_id": str(uuid.uuid4())
            }
        }
        ref = f"{self.AC_BASE_URL}/personal_info/contact_points/"
        return self._post_graphql("FXMetaPasswordReauthenticationMutation", self.DOC_ID_REAUTH, variables, referer=ref)

    def delete_email(self, email_to_delete: str, account_password: Optional[str] = None) -> Dict[str, Any]:
        print(f"[*] [API POST] Gửi yêu cầu gỡ bỏ/đá Email cũ: {email_to_delete}...")
        contact_point_id = base64.b64encode(email_to_delete.strip().encode()).decode()
        variables = {
            "contact_point_id": contact_point_id,
            "contact_point_type": "EMAIL",
            "client_mutation_id": f"mutation_id_{int(time.time() * 1000)}",
            "family_device_id": "device_id_fetch_datr"
        }
        ref = f"{self.AC_BASE_URL}/personal_info/contact_points/"
        res = self._post_graphql("FXAccountsCenterUnifiedDeleteContactPointMutation", self.DOC_ID_DELETE, variables, referer=ref)
        
        raw_text = res.get('raw', '')
        if ("SecuredAction" in raw_text or "2136001" in raw_text) and account_password:
            print("[+] Phát hiện SecuredAction Challenge (Yêu cầu mật khẩu)! Tiến hành tự động Re-Authenticate...")
            reauth_res = self.reauthenticate_password(account_password)
            if reauth_res.get('success'):
                print("[+] Re-Authentication mật khẩu THÀNH CÔNG! Gửi lại yêu cầu xóa email...")
                time.sleep(1)
                variables["client_mutation_id"] = f"mutation_id_{int(time.time() * 1000)}"
                res = self._post_graphql("FXAccountsCenterUnifiedDeleteContactPointMutation", self.DOC_ID_DELETE, variables, referer=ref)

        if not res.get('success'):
            return res

        data = res.get('data', {})
        del_data = data.get('data', {}).get('xfb_delete_contact_point', {})
        if del_data:
            return {'success': True, 'details': del_data}

        errors = data.get('errors', [])
        err_msg = errors[0].get('message') if errors else data.get('errorDescription', 'Không thể xóa email')
        if not errors:
            return {'success': True, 'details': data}
        return {'success': False, 'error': err_msg, 'data': data}

    def query_contact_points(self) -> Dict[str, Any]:
        variables = {"id": "CONTACT_POINT"}
        return self._post_graphql(
            "FXAccountsCenterContactPointsInProfilesRouteResolverQuery",
            self.DOC_ID_QUERY,
            variables
        )


# ==============================================================================
# DASHBOARD ĐA LUỒNG (style chuyen_xoa_page) + PROXY FILE POOL
# ==============================================================================
dashboard_lines = {}
dashboard_stats = {
    "total_ok": 0,
    "total_fail": 0,
    "total_jobs": 0,
    "start_ts": 0,
}
log_buffer = []
MAX_LOG_LINES = 5
_stop_flag = False
COUNTER_LOCK = threading.Lock()
success_count_global = 0
fail_count_global = 0


def _term_width():
    try:
        return shutil.get_terminal_size((120, 30)).columns
    except Exception:
        return 120


def _dash_update(idx, **kw):
    st = dashboard_lines.setdefault(idx, {
        "status": "Chờ",
        "success": 0,
        "fail": 0,
        "finished": False,
        "bar": None,
        "flag": None,
        "uid": None,
        "start_ts": time.time(),
        "end_ts": None,
        "job": 0,
        "job_total": 0,
    })
    for k, v in kw.items():
        if k == "done":
            if v and not st["finished"]:
                st["finished"] = True
                st["end_ts"] = time.time()
        else:
            st[k] = v


def _dash_bump_ok(n=1):
    with COUNTER_LOCK:
        dashboard_stats["total_ok"] += n


def _dash_bump_fail(n=1):
    with COUNTER_LOCK:
        dashboard_stats["total_fail"] += n


def _push_log(idx, msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S") if hasattr(datetime, "datetime") else time.strftime("%H:%M:%S")
    try:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
    except Exception:
        ts = time.strftime("%H:%M:%S")
    log_buffer.append(f"[dim]{ts}[/] [bold cyan]>>> [L{idx}][/] {msg}")
    if len(log_buffer) > MAX_LOG_LINES:
        log_buffer.pop(0)


def _shorten(text, max_len):
    if text is None:
        return ""
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _gradient_bar(current, total, length=10):
    if not _HAS_RICH:
        return "-" * length
    if total <= 0:
        return Text("-" * length, style="grey37")
    ratio = max(0.0, min(1.0, current / total))
    n_filled = int(length * ratio)
    t = Text()
    for i in range(n_filled):
        pos = i / max(1, length - 1)
        if pos < 0.5:
            r, g, b = 255, int(255 * pos * 2), 0
        else:
            r, g, b = int(255 * (1 - (pos - 0.5) * 2)), 255, 0
        t.append("▰", style=f"rgb({r},{g},{b})")
    t.append("▱" * (length - n_filled), style="grey30")
    return t


def render_dashboard_reg():
    if not _HAS_RICH:
        return ""
    now = time.time()
    elapsed = now - dashboard_stats["start_ts"] if dashboard_stats["start_ts"] else 0
    done = sum(1 for s in dashboard_lines.values() if s["finished"])
    total_ok = dashboard_stats["total_ok"]
    total_fail = dashboard_stats["total_fail"]
    total_jobs = dashboard_stats["total_jobs"]
    n_threads = len(dashboard_lines)
    speed = total_ok / elapsed if elapsed > 0 else 0

    elements = []
    head = (
        f"[bold green]REG[/] [dim]|[/] "
        f"[yellow]{n_threads}L[/] [dim]|[/] "
        f"[cyan]{total_ok + total_fail}/{total_jobs}[/] [dim]|[/] "
        f"[green]{total_ok}ok[/] [red]{total_fail}f[/] [dim]|[/] "
        f"[magenta]{int(elapsed)}s[/] [dim]|[/] [yellow]{speed:.1f}/s[/]"
    )
    elements.append(Panel(
        head, border_style="dim cyan", box=box.MINIMAL, padding=(0, 0),
        title="[dim]dash[/]", title_align="left",
    ))

    tbl = Table(
        show_header=True,
        header_style="dim cyan",
        expand=True,
        box=box.MINIMAL,
        border_style="dim",
        padding=(0, 0),
        collapse_padding=True,
        pad_edge=False,
    )
    tbl.add_column("#", width=2, justify="right", no_wrap=True, style="dim")
    tbl.add_column("L", width=3, justify="right", no_wrap=True, style="dim cyan")
    tbl.add_column("STT", ratio=1, no_wrap=True, overflow="ellipsis", style="dim")
    tbl.add_column("J", width=5, no_wrap=True, style="dim")
    tbl.add_column("O", width=2, justify="right", no_wrap=True)
    tbl.add_column("F", width=2, justify="right", no_wrap=True)
    tbl.add_column("T", width=5, justify="right", no_wrap=True, style="dim")

    if not dashboard_lines:
        tbl.add_row("-", "-", "wait...", "-", "0", "0", "0s")
    else:
        for idx in sorted(dashboard_lines.keys()):
            st = dashboard_lines[idx]
            flag = st.get("flag")
            s, f = st["success"], st["fail"]
            if flag == "die":
                icon = "[red]D[/]"
            elif st["finished"]:
                icon = "[blue]v[/]"
            else:
                icon = "[cyan]*[/]"

            status_raw = _shorten(st.get("status", ""), 18)
            if flag == "die":
                status = f"[red]{status_raw}[/]"
            elif st["finished"]:
                status = f"[blue]{status_raw}[/]"
            elif s > 0:
                status = f"[green]{status_raw}[/]"
            elif f > 0:
                status = f"[yellow]{status_raw}[/]"
            else:
                status = f"[dim]{status_raw}[/]"

            jt = st.get("job_total") or 0
            jc = st.get("job") or 0
            job_txt = f"{jc}/{jt}" if jt else "-"

            start_ts = st.get("start_ts", now)
            if st["finished"] and st.get("end_ts"):
                el = int(st["end_ts"] - start_ts)
            else:
                el = int(now - start_ts)
            time_txt = f"{el}s" if el < 60 else f"{el // 60}m"

            ok_s = f"[green]{s}[/]" if s else "[dim]0[/]"
            fail_s = f"[red]{f}[/]" if f else "[dim]0[/]"
            tbl.add_row(icon, str(idx), status, job_txt, ok_s, fail_s, time_txt)

    elements.append(tbl)
    recent = log_buffer[-3:] if log_buffer else ["[dim]...[/]"]
    elements.append(Panel(
        "\n".join(f"[dim]{x}[/]" for x in recent),
        border_style="dim green", box=box.MINIMAL, padding=(0, 0),
        title="[dim]log[/]", title_align="left",
    ))
    return Group(*elements)


class ProxyFilePool:
    """Proxy từ file — mỗi acc mới lấy 1 proxy (round-robin, thread-safe)."""

    def __init__(self, proxies: List[str]):
        self._proxies = [p.strip() for p in proxies if p and str(p).strip()]
        self._i = 0
        self._lock = threading.Lock()

    def __len__(self):
        return len(self._proxies)

    def next(self) -> Optional[str]:
        if not self._proxies:
            return None
        with self._lock:
            px = self._proxies[self._i % len(self._proxies)]
            self._i += 1
            return px


def load_proxies_from_file(filepath: str) -> List[str]:
    path = (filepath or "").strip().strip('"').strip("'")
    if not path or not os.path.isfile(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            if not s.startswith(("http://", "https://", "socks")):
                parts = s.split(":")
                if len(parts) == 4:
                    s = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                elif len(parts) == 2:
                    s = f"http://{s}"
                else:
                    s = f"http://{s}"
            out.append(s)
    return out


def otptrust_resolve_facebook_service(api_key: str, provider: str = "outlook") -> tuple:
    """Tự chọn service Facebook — không hỏi lại."""
    client = OTPTrustEmail(api_key=api_key)
    domain = provider if provider in ("gmail", "icloud") else None
    ok, services = client.list_services(domain=domain)
    if ok and isinstance(services, list):
        for s in services:
            code = str(s.get("service_code", "")).lower()
            name = str(s.get("name", "")).lower()
            if code == "facebook" or "facebook" in name:
                return int(s["id"]), str(s.get("name") or "Facebook"), provider
        if services:
            s0 = services[0]
            return int(s0["id"]), str(s0.get("name") or "Unknown"), provider
    return 1, "Facebook", provider


# ==============================================================================
# VIETMAIL API
# ==============================================================================
VIETMAIL_BASE = "http://103.28.35.20:3443"
VIETMAIL_API_KEY_B64 = "QjhHNC0wQzNGLTVEOUUtMkc3Qi1MME4z"
VIETMAIL_CONFIG_FILE = "vietmail_config.json"
_VIETMAIL_RENT_LOCK = threading.Lock()


def vietmail_load_config() -> dict:
    cfg = {"api_key_b64": VIETMAIL_API_KEY_B64, "base_url": VIETMAIL_BASE}
    try:
        if os.path.isfile(VIETMAIL_CONFIG_FILE):
            with open(VIETMAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if data.get("api_key_b64"):
                    cfg["api_key_b64"] = str(data["api_key_b64"]).strip()
                if data.get("base_url"):
                    cfg["base_url"] = str(data["base_url"]).strip().rstrip("/")
    except Exception:
        pass
    return cfg


def vietmail_save_config(api_key_b64: str = None, base_url: str = None):
    cfg = vietmail_load_config()
    if api_key_b64:
        cfg["api_key_b64"] = api_key_b64.strip()
    if base_url:
        cfg["base_url"] = base_url.strip().rstrip("/")
    try:
        with open(VIETMAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        try:
            AppLogger.warn(f"[VietMail] Khong luu config: {e}")
        except Exception:
            print(f"[VietMail] Khong luu config: {e}")


class VietMailClient:
    """VietMail: /thue /doc /tra /thuelai"""

    def __init__(self, api_key_b64: str = None, base_url: str = None):
        cfg = vietmail_load_config()
        self.api_key = (api_key_b64 or cfg.get("api_key_b64") or VIETMAIL_API_KEY_B64 or "").strip()
        self.base = (base_url or cfg.get("base_url") or VIETMAIL_BASE or "").rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key-B64": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RegFB-VietMail/2.0",
        })
        self.last_email = None
        self.last_token = None
        self.last_name = None
        self.last_domain = None

    def _post(self, path: str, json_body=None, timeout: int = 60) -> dict:
        url = f"{self.base}{path}"
        r = self.session.post(url, json=json_body if json_body is not None else {}, timeout=timeout)
        try:
            data = r.json()
        except Exception:
            data = {"_raw": r.text, "status": "error", "message": (r.text or "")[:300]}
        if not isinstance(data, dict):
            data = {"_raw": data, "status": "error"}
        data["_http"] = r.status_code
        return data

    def thue(self) -> tuple:
        try:
            data = self._post("/thue", {}, timeout=60)
        except Exception as e:
            return False, None, None, f"Request error: {e}"
        if data.get("status") == "success":
            d = data.get("data") or {}
            email = (d.get("email") or "").strip()
            token = d.get("token") or ""
            self.last_email = email
            self.last_token = token
            self.last_name = d.get("name")
            self.last_domain = d.get("domain")
            if email and "@" in email:
                return True, email, str(token), data
            return False, None, None, data.get("message") or "Thue OK nhung khong co email"
        return False, None, None, data.get("message") or str(data)[:200]

    def rent(self, service: str = "facebook") -> tuple:
        return self.thue()

    def doc(self) -> tuple:
        try:
            data = self._post("/doc", {}, timeout=30)
        except Exception as e:
            return False, [], str(e)
        if data.get("status") == "success":
            d = data.get("data") or {}
            msgs = d.get("messages") or []
            if not isinstance(msgs, list):
                msgs = []
            if d.get("email"):
                self.last_email = d.get("email")
            return True, msgs, data
        return False, [], data

    def get_otp(self, email: str = None, order_id=None) -> tuple:
        ok, msgs, raw = self.doc()
        if not ok:
            return False, None, raw
        otp = self._extract_otp_from_messages(msgs)
        if otp:
            return True, otp, raw
        otp2 = self._extract_otp_text(str(raw))
        if otp2:
            return True, otp2, raw
        return False, None, raw

    def _extract_otp_from_messages(self, messages) -> Optional[str]:
        if not messages:
            return None
        for msg in reversed(list(messages)):
            if isinstance(msg, dict):
                parts = [msg.get("subject"), msg.get("body"), msg.get("content"),
                         msg.get("text"), msg.get("html"), msg.get("snippet"), str(msg)]
            else:
                parts = [str(msg)]
            for part in parts:
                otp = self._extract_otp_text(str(part or ""))
                if otp:
                    return otp
        return None

    def _extract_otp_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        for pat in [r"(?:code|mã|ma|otp|confirmation)[^\d]{0,20}(\d{5,8})", r"\b(\d{5,8})\b"]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    def tra(self) -> dict:
        last_err = None
        for attempt in range(1, 4):
            try:
                data = self._post("/tra", {}, timeout=120)
                if data.get("status") == "success":
                    d = data.get("data") or {}
                    email = d.get("email_da_tra") or d.get("email") or self.last_email
                    self.last_email = None
                    return {"ok": True, "status": "success", "email": email,
                            "message": data.get("message") or "Da tra mail", "raw": data}
                msg = data.get("message") or ""
                return {"ok": True, "status": "empty", "email": None,
                        "message": msg or "Khong co mail de tra", "raw": data}
            except Exception as e:
                last_err = str(e)
                time.sleep(2)
        return {"ok": False, "status": "error", "email": None, "message": last_err or "error", "raw": None}

    def thuelai(self, token: str = None) -> tuple:
        token = token or self.last_token
        if not token:
            return False, None, None, "Thieu token"
        try:
            data = self._post("/thuelai", {"token": token}, timeout=60)
        except Exception as e:
            return False, None, None, str(e)
        if data.get("status") == "success":
            d = data.get("data") or {}
            email = (d.get("email") or "").strip()
            tok = d.get("token") or token
            self.last_email = email
            self.last_token = tok
            return True, email, tok, data
        return False, None, None, data.get("message") or str(data)[:200]

    def tra_all(self, max_rounds: int = 50, empty_stop: int = 3) -> int:
        total = 0
        empty = 0
        for _ in range(max_rounds):
            r = self.tra()
            if r.get("status") == "success" and r.get("email"):
                total += 1
                empty = 0
                try:
                    AppLogger.info(f"[VietMail] Tra: {r.get('email')} (tong={total})")
                except Exception:
                    print(f"[VietMail] Tra: {r.get('email')} (tong={total})")
            else:
                empty += 1
                if empty >= empty_stop:
                    break
            time.sleep(1)
        return total

    def wait_otp(self, email: str = None, order_id=None, max_wait: int = 180,
                 poll_every: float = 3.0, resend_callback=None, resend_times: int = 4,
                 resend_interval: float = 15.0):
        start = time.time()
        resend_done = 0
        next_resend = start + 10.0
        attempt = 0
        while time.time() - start < max_wait:
            attempt += 1
            ok, otp, raw = self.get_otp()
            if ok and otp:
                print()
                return otp
            now = time.time()
            if resend_callback and resend_done < resend_times and now >= next_resend:
                try:
                    AppLogger.mail(f"[VietMail] Resend OTP FB lan {resend_done + 1}/{resend_times}...")
                    resend_callback()
                except Exception as e:
                    AppLogger.warn(f"[VietMail] Resend loi: {e}")
                resend_done += 1
                next_resend = now + resend_interval
            left = int(max_wait - (time.time() - start))
            print(f"    ... Cho OTP VietMail ({attempt}) con ~{left}s", end="\r", flush=True)
            time.sleep(poll_every)
        print()
        return None


# ==============================================================================
# PSTMMO.CC — API THUÊ EMAIL NHẬN OTP & HOÀN TIỀN TỰ ĐỘNG
# ==============================================================================
PSTMMO_BASE = "https://mail.pstmmo.cc"
PSTMMO_API_KEY = "pst_10f41a8e89b2c28d96fc999791e3a3f3"
PSTMMO_DEFAULT_SITE = "facebook.com"


def pstmmo_load_config() -> dict:
    path = _local_config_path("pstmmo_config.json")
    cfg = {
        "api_key": PSTMMO_API_KEY,
        "base_url": PSTMMO_BASE,
        "domain": "",
    }
    try:
        data = _read_local_config(path)
        if isinstance(data, dict):
            if data.get("api_key"):
                cfg["api_key"] = str(data["api_key"]).strip()
            if data.get("base_url"):
                cfg["base_url"] = str(data["base_url"]).strip().rstrip("/")
            if "domain" in data:
                cfg["domain"] = str(data.get("domain") or "").strip()
    except Exception:
        pass
    return cfg


def pstmmo_save_config(api_key: str = None, domain: str = None, base_url: str = None):
    cfg = pstmmo_load_config()
    if api_key is not None and api_key.strip():
        cfg["api_key"] = api_key.strip()
    if domain is not None:
        cfg["domain"] = domain.strip()
    if base_url is not None and base_url.strip():
        cfg["base_url"] = base_url.strip().rstrip("/")
    _save_local_config(_local_config_path("pstmmo_config.json"), cfg)


class PSTMMOEmail:
    """Client tích hợp API https://mail.pstmmo.cc (User, Services, Buy, Check OTP, Cancel/Refund)."""

    def __init__(self, api_key: str = None, base_url: str = None):
        cfg = pstmmo_load_config()
        self.api_key = (api_key or cfg.get("api_key") or PSTMMO_API_KEY or "").strip()
        self.base = (base_url or cfg.get("base_url") or PSTMMO_BASE or "").rstrip("/")
        if self.base.endswith("/api"):
            self.base = self.base[:-4]

        self.session = requests.Session()
        self.session.trust_env = False
        self.session.proxies = {}
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "RegFB-PSTMMO/1.0",
        })
        self.last_order_id = None
        self.last_order_code = None
        self.last_email = None

    def get_user_info(self) -> Tuple[bool, dict]:
        """GET /api/user — Kiểm tra thông tin tài khoản & số dư ví."""
        try:
            r = self.session.get(f"{self.base}/api/user", timeout=15)
            data = r.json()
            if r.status_code == 200 and data.get("status") == "success":
                return True, data.get("data") or data
            return False, data
        except Exception as e:
            return False, {"message": str(e)}

    def get_services(self) -> Tuple[bool, list]:
        """GET /api/services — Lấy danh sách dịch vụ, tồn kho và supported_domains."""
        try:
            r = self.session.get(f"{self.base}/api/services", timeout=15)
            data = r.json()
            if r.status_code == 200 and data.get("status") == "success":
                return True, data.get("data") or []
            return False, []
        except Exception:
            return False, []

    def rent(self, site: str = PSTMMO_DEFAULT_SITE, domain: str = "") -> Tuple[bool, Optional[str], Optional[Any], Any]:
        """
        GET /{token}/{site}/{domain} hoặc /{token}/{site}
        Hỗ trợ tự động fallback sang domain ngẫu nhiên nếu domain chỉ định hết hàng (HTTP 503).
        """
        site_clean = (site or PSTMMO_DEFAULT_SITE).strip()
        dom_clean = (domain or "").strip().lstrip("@")

        urls_to_try = []
        if dom_clean:
            urls_to_try.append(f"{self.base}/{self.api_key}/{site_clean}/{dom_clean}")
        urls_to_try.append(f"{self.base}/{self.api_key}/{site_clean}")

        last_err = None
        for idx, url in enumerate(urls_to_try):
            try:
                r = self.session.get(url, timeout=20)
                try:
                    data = r.json()
                except Exception:
                    data = {"message": (r.text or "")[:200], "code": r.status_code}

                if r.status_code == 200 and data.get("status") == "success":
                    d = data.get("data") or {}
                    email_addr = (data.get("email") or d.get("email") or "").strip()
                    order_id = (
                        data.get("order_id")
                        or data.get("id")
                        or d.get("order_id")
                        or d.get("id")
                        or data.get("order_code")
                        or d.get("order_code")
                    )
                    self.last_email = email_addr
                    self.last_order_id = order_id
                    self.last_order_code = data.get("order_code") or d.get("order_code")
                    if email_addr and order_id is not None:
                        return True, email_addr, order_id, data

                if r.status_code == 503 and idx == 0 and len(urls_to_try) > 1:
                    AppLogger.warn(f"[PSTMMO] Domain '{dom_clean}' tạm hết hàng (503) -> Tự động lấy domain sẵn hàng khác...")
                    continue
                if r.status_code == 402:
                    return False, None, None, "Hết số dư ví (HTTP 402 Payment Required)"
                if r.status_code == 401:
                    return False, None, None, "API Key không hợp lệ (HTTP 401 Unauthorized)"

                last_err = data.get("message") or f"HTTP {r.status_code}: {str(data)[:150]}"
            except Exception as e:
                last_err = str(e)

        return False, None, None, last_err

    def check_otp(self, order_id=None) -> Tuple[str, Optional[str], dict]:
        """
        GET /{token}/check/{order_id}
        Trả về tuple: (state, otp_code, raw_dict)
        state thuộc: 'completed' | 'waiting' | 'expired' | 'error'
        """
        oid = order_id if order_id is not None else self.last_order_id
        if not oid:
            return "error", None, {"message": "missing order_id"}

        url = f"{self.base}/{self.api_key}/check/{oid}"
        try:
            r = self.session.get(url, timeout=15)
            res = r.json()
        except Exception as e:
            return "error", None, {"message": str(e)}

        if not isinstance(res, dict):
            return "error", None, {}

        d = res.get("data") if isinstance(res.get("data"), dict) else {}
        status_top = str(res.get("status") or "").lower()
        status_data = str(d.get("status") or "").lower()

        raw_otp = (
            res.get("otp")
            or res.get("otp_code")
            or d.get("otp")
            or d.get("otp_code")
        )
        if raw_otp and str(raw_otp).strip().lower() not in ("none", "null", ""):
            otp_str = str(raw_otp).strip()
            m_digits = re.search(r"\b(\d{5,8})\b", otp_str)
            return "completed", (m_digits.group(1) if m_digits else otp_str), res

        if status_data == "completed":
            msg_text = str(d.get("message") or "")
            m_msg = re.search(r"\b(\d{5,8})\b", msg_text)
            if m_msg:
                return "completed", m_msg.group(1), res

        if status_data in ("refunded", "failed", "expired") or status_top in ("refunded", "failed", "expired"):
            return "expired", None, res

        return "waiting", None, res

    def cancel(self, order_id=None) -> Tuple[bool, str]:
        """GET /{token}/cancel/{order_id} — Hủy đơn & hoàn tiền 100% vào ví."""
        oid = order_id if order_id is not None else self.last_order_id
        if not oid:
            return False, "Thiếu order_id"
        url = f"{self.base}/{self.api_key}/cancel/{oid}"
        try:
            r = self.session.get(url, timeout=15)
            data = r.json()
            if r.status_code == 200 and data.get("status") == "success":
                d = data.get("data") or {}
                new_bal = d.get("new_balance_formatted") or d.get("new_balance") or ""
                msg = data.get("message") or "Đã hủy và hoàn tiền"
                return True, f"{msg} (Số dư: {new_bal})" if new_bal else msg
            return False, str(data.get("message") or data)
        except Exception as e:
            return False, str(e)

    def wait_otp(
        self,
        order_id=None,
        max_wait: int = 180,
        poll_every: float = 3.5,
        resend_callback: Optional[Callable[[], bool]] = None,
        resend_times: int = 4,
        resend_interval: float = 15.0,
        auto_cancel_on_timeout: bool = True,
    ) -> Optional[str]:
        oid = order_id if order_id is not None else self.last_order_id
        if not oid:
            return None

        start = time.time()
        resend_done = 0
        next_resend_at = start + 12.0
        attempt = 0

        while time.time() - start < max_wait:
            attempt += 1
            state, otp, raw = self.check_otp(oid)
            if state == "completed" and otp:
                print()
                return otp
            if state == "expired":
                print()
                AppLogger.warn(f"[PSTMMO] Đơn hàng #{oid} đã hết hạn hoặc đã được hoàn tiền.")
                return None

            now = time.time()
            if resend_callback and resend_done < resend_times and now >= next_resend_at:
                try:
                    AppLogger.mail(f"[PSTMMO] Gửi lại mã OTP Facebook lần {resend_done + 1}/{resend_times}...")
                    resend_callback()
                except Exception as e:
                    AppLogger.warn(f"[PSTMMO] Lỗi resend OTP: {e}")
                resend_done += 1
                next_resend_at = now + resend_interval

            left = int(max_wait - (time.time() - start))
            d_status = ((raw.get("data") or {}).get("status") if isinstance(raw, dict) else "") or state
            print(f"    ... Chờ OTP PSTMMO ({attempt}) còn ~{left}s | status={d_status}", end="\r", flush=True)
            time.sleep(poll_every)

        print()
        if auto_cancel_on_timeout:
            ok_c, msg_c = self.cancel(oid)
            if ok_c:
                AppLogger.info(f"[PSTMMO] Tự động hủy đơn #{oid} & hoàn tiền: {msg_c}")
        return None
# ══════════════════════════════════════════════════════════════════════════
#                    HẾT PHẦN 1/3
# ══════════════════════════════════════════════════════════════════════════
# ==============================================================================
# GMAIL POOL — mua Gmail94, cache, dot-trick
# ==============================================================================
GMAIL_USAGE_FILE = "gmail_pool.json"

# Session chạy DIRECT 100% qua mạng chính / 4G (0 byte dữ liệu Proxy)
direct_http_session = requests.Session()
direct_http_session.proxies = {}
direct_http_session.trust_env = False


def clear_gmail_pool():
    if os.path.exists(GMAIL_USAGE_FILE):
        try:
            os.remove(GMAIL_USAGE_FILE)
            print("[*] [Gmail94] Đã xóa bộ nhớ Gmail cũ (gmail_pool.json) -> Tiến trình mới sẵn sàng!")
        except Exception as e:
            print(f"[-] Không thể xóa {GMAIL_USAGE_FILE}: {e}")


try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

from contextlib import contextmanager


@contextmanager
def pool_file_lock():
    lock_file_path = GMAIL_USAGE_FILE + ".lock"
    lock_file = open(lock_file_path, "a+")
    start_time = time.time()
    while True:
        try:
            if HAS_MSVCRT:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            break
        except (IOError, OSError):
            if time.time() - start_time > 15:
                break
            time.sleep(random.uniform(0.1, 0.3))
    try:
        yield
    finally:
        try:
            if HAS_MSVCRT:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
        try:
            lock_file.close()
        except Exception:
            pass


def read_pool_locked() -> Dict[str, Any]:
    with pool_file_lock():
        if not os.path.exists(GMAIL_USAGE_FILE):
            return {}
        try:
            with open(GMAIL_USAGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}


def write_pool_locked(pool_data: Dict[str, Any]):
    with pool_file_lock():
        try:
            with open(GMAIL_USAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(pool_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[-] Lỗi ghi file pool: {e}")


def _find_pool_key(pool: dict, email_addr: str) -> Optional[str]:
    if not email_addr or not isinstance(pool, dict):
        return None
    if email_addr in pool:
        return email_addr
    clean = email_addr.lower().replace(".", "")
    for k in pool:
        if k.lower().replace(".", "") == clean:
            return k
    return None


def generate_4_gmail_dots(gmail_address: str) -> List[str]:
    email_clean = str(gmail_address).strip().lower()
    if "@" not in email_clean:
        return [email_clean] * 4
    username, domain = email_clean.split("@", 1)
    username = username.replace(".", "")

    if len(username) < 3:
        username = username + "fb"

    dots = []
    dots.append(f"{username}@{domain}")
    dots.append(f"{username[:1]}.{username[1:]}@{domain}")
    if len(username) > 2:
        dots.append(f"{username[:2]}.{username[2:]}@{domain}")
    else:
        dots.append(f"{username[:1]}.{username[1:]}.1@{domain}")
    if len(username) >= 4:
        dots.append(f"{username[:1]}.{username[1:3]}.{username[3:]}@{domain}")
    elif len(username) == 3:
        dots.append(f"{username[:1]}.{username[1:2]}.{username[2:]}@{domain}")
    else:
        dots.append(f"{username[:1]}.{username[1:]}.2@{domain}")

    uniq = list(dict.fromkeys(dots))
    while len(uniq) < 4:
        uniq.append(f"{username}.{len(uniq)}@{domain}")
    return uniq[:4]


def release_gmail_claim(email_addr: str):
    if not email_addr:
        return
    with pool_file_lock():
        pool = {}
        if os.path.exists(GMAIL_USAGE_FILE):
            try:
                with open(GMAIL_USAGE_FILE, 'r', encoding='utf-8') as f:
                    pool = json.load(f)
            except Exception:
                pool = {}
        key = _find_pool_key(pool, email_addr)
        if key and key in pool:
            pool[key]['in_use'] = False
            try:
                with open(GMAIL_USAGE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(pool, f, indent=2, ensure_ascii=False)
            except Exception:
                pass


def increment_gmail_usage(email_addr: str):
    if not email_addr:
        return
    with pool_file_lock():
        pool = {}
        if os.path.exists(GMAIL_USAGE_FILE):
            try:
                with open(GMAIL_USAGE_FILE, 'r', encoding='utf-8') as f:
                    pool = json.load(f)
            except Exception:
                pool = {}
        key = _find_pool_key(pool, email_addr)
        if key and key in pool:
            pool[key]['used'] = pool[key].get('used', 0) + 1
            print(f"[*] [Gmail94 Pool] Đã ghi nhận sử dụng {key}: {pool[key]['used']}/{MAX_REG_PER_GMAIL} lượt.")
            try:
                with open(GMAIL_USAGE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(pool, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[-] Lỗi cập nhật gmail pool: {e}")


def mark_gmail_failed(email_addr: str):
    if not email_addr:
        return
    with pool_file_lock():
        pool = {}
        if os.path.exists(GMAIL_USAGE_FILE):
            try:
                with open(GMAIL_USAGE_FILE, 'r', encoding='utf-8') as f:
                    pool = json.load(f)
            except Exception:
                pool = {}
        key = _find_pool_key(pool, email_addr)
        if key and key in pool:
            del pool[key]
            try:
                with open(GMAIL_USAGE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(pool, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[-] Lỗi cập nhật gmail pool: {e}")
            print(f"[*] [Gmail94 Pool] Đã loại bỏ đơn không nhận được OTP: {key}. Lần sau sẽ tự động mua Gmail mới!")


def _format_kiotproxy_dict(d: dict) -> Optional[str]:
    if not isinstance(d, dict):
        return None
    raw_addr = d.get('http') or d.get('httpStaticProxy')
    addr = re.sub(r'(?i)^[a-z0-9+.-]+://', '', str(raw_addr or '').strip()).strip().rstrip('/')
    if not addr and d.get('host') and d.get('httpPort'):
        host = re.sub(r'(?i)^[a-z0-9+.-]+://', '', str(d.get('host') or '').strip()).strip().rstrip('/')
        port = str(d.get('httpPort') or '').strip()
        if host and port:
            addr = f"{host}:{port}"
    if not addr:
        return None
    user = str(d.get('proxyUser') or '').strip()
    pwd = str(d.get('proxyPass') or '').strip()
    if '@' not in addr and user and pwd:
        return f"http://{user}:{pwd}@{addr}"
    return f"http://{addr}"


def get_kiotproxy(proxy_key: Optional[str] = None, api_token: Optional[str] = None, wait_for_new: bool = False) -> Optional[str]:
    p_key = proxy_key if proxy_key is not None else KIOT_PROXY_KEY
    token = api_token if api_token is not None else KIOT_API_TOKEN
    p_key = str(p_key).strip() if p_key else None
    if not p_key:
        return None
    
    token = str(token).strip() if token and str(token).strip() else None
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    url_new = f"https://api.kiotproxy.com/api/v1/proxies/new?key={p_key}"
    should_fallback = False
    try:
        r = requests.get(url_new, headers=headers, timeout=12)
        try:
            res = r.json()
        except Exception:
            res = {}

        if res.get('success') and 'data' in res:
            d = res['data']
            proxy_str = _format_kiotproxy_dict(d)
            if proxy_str:
                loc = d.get('location', '') if isinstance(d, dict) else ''
                ttc = d.get('packageTtc', 0) if isinstance(d, dict) else 0
                print(f"[*] [KiotProxy] Lấy IP mới thành công: {proxy_str} | Vị trí: {loc} (TTC: {ttc}s)")
                return proxy_str
            else:
                print(f"[-] [KiotProxy] Dữ liệu IP mới không hợp lệ hoặc thiếu proxy: {d}")
                should_fallback = True
        else:
            msg = str(res.get('message', '') or '')
            err = str(res.get('error', '') or '')
            code = res.get('code', 0)
            status_code = getattr(r, 'status_code', 0)
            print(f"[*] [KiotProxy] Thông báo: {msg or err or status_code}")

            msg_lower = msg.lower()
            res_str_upper = str(res).upper()

            if wait_for_new and ('chưa đến hạn' in msg_lower or err.upper() == 'TIME_TO_CHANGE_INVALID'):
                m_sec = re.search(r'(\d+)', msg)
                wait_sec = int(m_sec.group(1)) + 2 if m_sec else 15
                print(f"[*] [KiotProxy] IP đang trong thời gian chờ. Đang đợi {wait_sec}s để lấy IP MỚI SẠCH (tránh Facebook chặn)...")
                for s in range(wait_sec, 0, -1):
                    if s % 10 == 0 or s <= 5:
                        print(f"    ... Đợi đổi IP: còn {s}s")
                    time.sleep(1)
                return get_kiotproxy(proxy_key=p_key, api_token=token, wait_for_new=False)

            fatal_errors = {'INVALID_KEY', 'KEY_NOT_FOUND', 'EXPIRED_KEY', 'UNAUTHORIZED', 'FORBIDDEN'}
            if err.upper() not in fatal_errors and code not in (401, 403, 404) and status_code not in (401, 403, 404):
                if (
                    err.upper() in (
                        'TIME_TO_CHANGE_INVALID',
                        'RATE_LIMIT_GET_NEW_PROXY',
                        'ALLOCATE_PROXY_FAIL',
                        'SYSTEM_IS_HAVING_TROUBLE_ALLOCATING_RESOURCES'
                    )
                    or 'TIME_TO_CHANGE_INVALID' in res_str_upper
                    or 'RATE_LIMIT' in res_str_upper
                    or 'ALLOCAT' in res_str_upper
                    or 'RESOURCE' in res_str_upper
                    or 'chưa đến hạn' in msg_lower
                    or 'giới hạn' in msg_lower
                    or 'phân bổ' in msg_lower
                    or 'too many requests' in msg_lower
                    or code in (40001038, 40001130, 40001178, 50001001, 429)
                    or status_code in (429, 500, 502, 503, 504)
                ):
                    should_fallback = True
    except Exception as e:
        print(f"[-] [KiotProxy] Lỗi gọi API new proxy: {e}")
        should_fallback = True

    if should_fallback:
        url_curr = f"https://api.kiotproxy.com/api/v1/proxies/current?key={p_key}"
        try:
            r = requests.get(url_curr, headers=headers, timeout=12)
            try:
                res = r.json()
            except Exception:
                res = {}

            if res.get('success') and res.get('data'):
                d = res['data']
                proxy_str = _format_kiotproxy_dict(d)
                if proxy_str:
                    loc = d.get('location', '') if isinstance(d, dict) else ''
                    ttc = d.get('ttc', 0) if isinstance(d, dict) else 0
                    print(f"[*] [KiotProxy] Dùng proxy hiện tại: {proxy_str} | Vị trí: {loc} (Chờ đổi IP sau: {ttc}s)")
                    return proxy_str
                else:
                    print(f"[-] [KiotProxy] Dữ liệu proxy hiện tại không hợp lệ hoặc thiếu proxy: {d}")
            else:
                msg = res.get('message') or res.get('error') or getattr(r, 'status_code', '')
                print(f"[-] [KiotProxy] Lấy proxy hiện tại thất bại: {msg}")
        except Exception as e:
            print(f"[-] [KiotProxy] Lỗi gọi API current proxy: {e}")
        
    return None


def parse_proxy(proxy_str: Optional[str]) -> Optional[Dict[str, str]]:
    if not proxy_str or not str(proxy_str).strip():
        return None
    p = str(proxy_str).strip()
    raw_host = re.sub(r'(?i)^[a-z0-9+.-]+://', '', p).strip()
    if not raw_host:
        return None
    if p.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
        return {'http': p, 'https': p}
    parts = p.split(':')
    if len(parts) == 4:
        host, port, user, pwd = parts
        formatted = f"http://{user}:{pwd}@{host}:{port}"
        return {'http': formatted, 'https': formatted}
    elif len(parts) == 2:
        host, port = parts
        formatted = f"http://{host}:{port}"
        return {'http': formatted, 'https': formatted}
    else:
        formatted = f"http://{p}"
        return {'http': formatted, 'https': formatted}


def get_proxyxoay():
    if not PROXY_XOAY_KEY:
        return None
    url = f"https://proxyxoay.shop/api/get.php?key={PROXY_XOAY_KEY}&nhamang=Random&tinhthanh=0"
    for _ in range(3):
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if str(data.get("status")) == "100":
                proxy = data.get("proxyhttp", "")
                if proxy:
                    proxy = proxy.strip(":")
                    print(f"[*] Đã xoay IP thành công. Proxy mới: {proxy} - {data.get('Nha Mang')} ({data.get('Vi Tri')})")
                    return f"http://{proxy}"
            else:
                print(f"[-] Lỗi xoay IP: {data.get('message', 'Unknown error')}")
                if "vui lòng đợi" in data.get("message", "").lower() or "die sau" in data.get("message", "").lower():
                    time.sleep(3)
        except Exception as e:
            print(f"[-] Lỗi kết nối Proxy Xoay: {e}")
        time.sleep(2)
    return None


# ==============================================================================
# MODULE LẤY TOKEN FACEBOOK — FacebookPasswordEncryptor + FacebookLogin
# ==============================================================================
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5, AES
    from Crypto.Random import get_random_bytes
    HAS_CRYPTO = True
except Exception:
    RSA = None
    AES = None
    PKCS1_v1_5 = None
    get_random_bytes = None
    HAS_CRYPTO = False

class FacebookPasswordEncryptor:
    @staticmethod
    def get_public_key(proxy: Optional[str] = None) -> Tuple[str, str, float]:
        url = 'https://b-graph.facebook.com/pwd_key_fetch'
        params = {
            'version': '2',
            'flow': 'CONTROLLER_INITIALIZATION',
            'method': 'GET',
            'fb_api_req_friendly_name': 'pwdKeyFetch',
            'fb_api_caller_class': 'com.facebook.auth.login.AuthOperations',
            'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32'
        }
        headers = {
            'User-Agent': 'okhttp/5.1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'content-length': '0'
        }
        r = requests.post(url, params=params, headers=headers, proxies=parse_proxy(proxy), timeout=15)
        response = r.json()
        pub_key = response.get('public_key')
        key_id = str(response.get('key_id', '25'))

        server_ts = time.time()
        date_hdr = r.headers.get('Date')
        if date_hdr:
            try:
                server_ts = email.utils.parsedate_to_datetime(date_hdr).timestamp()
            except Exception:
                pass

        if not pub_key:
            raise Exception(f"Không nhận được public key: {response}")
        return pub_key, key_id, server_ts

    @staticmethod
    def encrypt(password: str, proxy: Optional[str] = None) -> Tuple[str, float]:
        if not RSA or not AES:
            raise Exception("Thiếu thư viện pycryptodome. Hãy chạy: pip install pycryptodome")
        public_key, key_id, server_ts = FacebookPasswordEncryptor.get_public_key(proxy)

        rand_key = get_random_bytes(32)
        iv = get_random_bytes(12)

        pubkey = RSA.import_key(public_key)
        cipher_rsa = PKCS1_v1_5.new(pubkey)
        encrypted_rand_key = cipher_rsa.encrypt(rand_key)

        cipher_aes = AES.new(rand_key, AES.MODE_GCM, nonce=iv)
        current_time = int(server_ts)
        cipher_aes.update(str(current_time).encode('utf-8'))
        (encrypted_passwd, auth_tag) = cipher_aes.encrypt_and_digest(password.encode('utf-8'))

        buf = io.BytesIO()
        buf.write(bytes([1, int(key_id)]))
        buf.write(iv)
        buf.write(struct.pack('<h', len(encrypted_rand_key)))
        buf.write(encrypted_rand_key)
        buf.write(auth_tag)
        buf.write(encrypted_passwd)

        encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f'#PWD_FB4A:2:{current_time}:{encoded}', server_ts

    @staticmethod
    def encrypt_web_password(password: str, proxy: Optional[str] = None) -> Tuple[str, float]:
        if not RSA or not AES:
            current_time = int(time.time())
            return f'#PWD_BROWSER:0:{current_time}:{password}', float(current_time)
        try:
            public_key, key_id, server_ts = FacebookPasswordEncryptor.get_public_key(proxy)
            rand_key = get_random_bytes(32)
            iv = get_random_bytes(12)

            pubkey = RSA.import_key(public_key)
            cipher_rsa = PKCS1_v1_5.new(pubkey)
            encrypted_rand_key = cipher_rsa.encrypt(rand_key)

            cipher_aes = AES.new(rand_key, AES.MODE_GCM, nonce=iv)
            current_time = int(server_ts)
            cipher_aes.update(str(current_time).encode('utf-8'))
            (encrypted_passwd, auth_tag) = cipher_aes.encrypt_and_digest(password.encode('utf-8'))

            buf = io.BytesIO()
            buf.write(bytes([1, int(key_id)]))
            buf.write(iv)
            buf.write(struct.pack('<h', len(encrypted_rand_key)))
            buf.write(encrypted_rand_key)
            buf.write(auth_tag)
            buf.write(encrypted_passwd)

            encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f'#PWD_BROWSER:5:{current_time}:{encoded}', server_ts
        except Exception as e:
            print(f"[-] Cảnh báo: Lỗi mã hóa Web RSA/AES ({e}). Fallback sang plain format.")
            current_time = int(time.time())
            return f'#PWD_BROWSER:0:{current_time}:{password}', float(current_time)


class FacebookLogin:
    GQL_URL = 'https://b-graph.facebook.com/graphql'
    AUTH_URL = 'https://b-graph.facebook.com/auth/login'
    ACCESS_TOKEN = '350685531728|62f8ce9f74b12f84c123cc23437a4a32'
    BLOKS_VERSION = '3469837656910fc29c9aa968ab33845cd52eb5253ae110610b944c8e9028d8f6'
    CLIENT_DOC_ID = '119940804214876861379510865434'
    TWO_FA_ENTRYPOINT_DOC_ID = '105373461558397492702779496'
    ATTESTATION_SIG = 'MEQCIDHrmQ86yvC7yeVBi0eYpIr2cnhtaSWxYm8I ZcZ081fAiBLzhHez6CMvaQqaFrCvfCMYker7WNLiQ4L99JpVR9K Q=='
    ATTESTATION_KEY = '9c620c1c59a053c07d9ce2f1166b1385e359254b6c461b3b55ca256d75e0976e'
    FB4A_UA = '[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]'

    def __init__(self, uid_phone_mail: str, password: str, twofa_secret: Optional[str] = None, machine_id: Optional[str] = None, proxy: Optional[str] = None, custom_ua: Optional[str] = None):
        self.uid_phone_mail = str(uid_phone_mail).strip()
        self.twofa_secret = re.sub(r'[\s\-]+', '', str(twofa_secret or '')).upper()
        self.raw_password = password
        self.proxy = proxy
        self.px_dict = parse_proxy(proxy)
        self.ua = custom_ua or self.FB4A_UA
        self.server_time_offset = 0.0

        if password.startswith('#PWD_FB4A'):
            self.password = password
        else:
            self.password, server_ts = FacebookPasswordEncryptor.encrypt(password, proxy=proxy)
            self.server_time_offset = server_ts - time.time()

        self.session = requests.Session()
        self.device_id = str(uuid.uuid4())
        self.secure_family_device_id = str(uuid.uuid4())
        self.waterfall_id = str(uuid.uuid4())
        self.infra_flow_id = str(uuid.uuid4())
        self.client_trace_id = str(uuid.uuid4())
        self.machine_id = machine_id or ''

    def _get_server_now(self) -> float:
        return time.time() + self.server_time_offset

    def _build_attestation(self):
        nonce = base64.b64encode(get_random_bytes(32)).decode()
        data_json = json.dumps({'challenge_nonce': nonce, 'username': self.uid_phone_mail})
        return {
            'data': base64.b64encode(data_json.encode()).decode(),
            'signature': self.ATTESTATION_SIG,
            'keyHash': self.ATTESTATION_KEY
        }

    def _build_gql_headers(self):
        return {
            'User-Agent': getattr(self, 'ua', self.FB4A_UA),
            'Accept': 'application/json, text/json, text/x-json, text/javascript, application/xml, text/xml',
            'Accept-Encoding': 'gzip',
            'x-fb-connection-type': 'WIFI',
            'x-fb-http-engine': 'Tigon/Liger',
            'x-fb-client-ip': 'True',
            'x-fb-server-cluster': 'True',
            'x-tigon-is-retry': 'False',
            'x-fb-device-group': '5427',
            'x-graphql-request-purpose': 'fetch',
            'x-fb-privacy-context': '3643298472347298',
            'x-graphql-client-library': 'graphservice',
            'x-fb-net-hni': '45201',
            'x-fb-sim-hni': '45201',
            'authorization': f'OAuth {self.ACCESS_TOKEN}',
            'x-fb-request-analytics-tags': json.dumps({
                'network_tags': {
                    'product': '350685531728',
                    'purpose': 'fetch',
                    'request_category': 'graphql',
                    'retry_attempt': '0'
                },
                'application_tags': 'graphservice'
            })
        }

    def _build_client_input_params(self):
        return {
            'password': self.password,
            'device_id': self.device_id,
            'family_device_id': self.device_id,
            'contact_point': self.uid_phone_mail,
            'login_attempt_count': 1,
            'event_flow': 'login_manual',
            'sim_phones': [],
            'secure_family_device_id': self.secure_family_device_id,
            'attestation_result': self._build_attestation(),
            'auth_secure_device_id': '',
            'has_whatsapp_installed': 0,
            'sso_token_map_json_string': '',
            'password_contains_non_ascii': 'false',
            'sim_serials': [],
            'client_known_key_hash': '',
            'encrypted_msisdn': '',
            'should_show_nested_nta_from_aymh': 0,
            'machine_id': self.machine_id,
            'flash_call_permission_status': {
                'READ_PHONE_STATE': 'DENIED',
                'READ_CALL_LOG': 'DENIED',
                'ANSWER_PHONE_CALLS': 'DENIED'
            },
            'accounts_list': [],
            'fb_ig_device_id': [],
            'device_emails': [],
            'try_num': 1,
            'lois_settings': {'lois_token': '', 'lara_override': ''},
            'event_step': 'home_page',
            'headers_infra_flow_id': self.infra_flow_id,
            'openid_tokens': {}
        }

    def _build_server_params(self):
        return {
            'should_trigger_override_login_2fa_action': 0,
            'is_from_logged_out': 0,
            'should_trigger_override_login_success_action': 0,
            'login_credential_type': 'none',
            'server_login_source': 'login',
            'waterfall_id': self.waterfall_id,
            'login_source': 'Login',
            'is_platform_login': 0,
            'pw_encryption_try_count': 1,
            'INTERNAL__latency_qpl_marker_id': 36707139,
            'offline_experiment_group': 'caa_iteration_v6_perf_fb_2',
            'is_from_landing_page': 0,
            'password_text_input_id': 'nmi7ws:95',
            'is_from_empty_password': 0,
            'ar_event_source': 'login_home_page',
            'username_text_input_id': 'nmi7ws:94',
            'layered_homepage_experiment_group': None,
            'device_id': self.device_id,
            'INTERNAL__latency_qpl_instance_id': random.randint(100000000000000, 999999999999999),
            'reg_flow_source': 'login_home_native_integration_point',
            'is_caa_perf_enabled': 1,
            'credential_type': 'password',
            'is_from_password_entry_page': 0,
            'caller': 'gslr',
            'family_device_id': self.device_id,
            'INTERNAL_INFRA_THEME': 'harm_f',
            'is_from_assistive_id': 0,
            'access_flow_version': 'F2_FLOW',
            'is_from_logged_in_switcher': 0
        }

    def _build_payload(self):
        inner_params = json.dumps({
            'client_input_params': self._build_client_input_params(),
            'server_params': self._build_server_params()
        })
        variables = json.dumps({
            'params': {
                'params': inner_params,
                'bloks_versioning_id': self.BLOKS_VERSION,
                'app_id': 'com.bloks.www.bloks.caa.login.async.send_login_request'
            },
            'scale': '2',
            'nt_context': {
                'using_white_navbar': True,
                'styles_id': '964d559c1e2aa0142b5069bc8cb1adea',
                'pixel_ratio': 2,
                'is_push_on': True,
                'debug_tooling_metadata_token': None,
                'is_flipper_enabled': False,
                'theme_params': [],
                'bloks_version': self.BLOKS_VERSION
            }
        })
        return {
            'method': 'post',
            'pretty': 'false',
            'format': 'json',
            'server_timestamps': 'true',
            'locale': 'vi_VN',
            'purpose': 'fetch',
            'fb_api_req_friendly_name': 'FbBloksActionRootQuery-com.bloks.www.bloks.caa.login.async.send_login_request',
            'fb_api_caller_class': 'graphservice',
            'client_doc_id': self.CLIENT_DOC_ID,
            'variables': variables,
            'fb_api_analytics_tags': '["GraphServices"]',
            'client_trace_id': self.client_trace_id,
            'generate_session_cookies': '1'
        }

    def _extract_token(self, text: str) -> Optional[str]:
        match = re.search(r'"access_token"\s*:\s*"([^"]+)"', text)
        if not match:
            match = re.search(r'access_token=([^&"\s]+)', text)
        if not match:
            match = re.search(r'access_token.*?([A-Za-z0-9:_-]{20,})', text)
        if match:
            return match.group(1)
        return None

    def _extract_cookies(self, text: str) -> str:
        try:
            data = json.loads(text)
            cookies = []
            def find_cookies(obj):
                if isinstance(obj, dict):
                    if 'session_cookies' in obj and isinstance(obj['session_cookies'], list):
                        for c in obj['session_cookies']:
                            if 'name' in c and 'value' in c:
                                cookies.append(f"{c['name']}={c['value']}")
                    for v in obj.values():
                        find_cookies(v)
                elif isinstance(obj, list):
                    for item in obj:
                        find_cookies(item)
            find_cookies(data)
            if cookies:
                return '; '.join(cookies)
        except Exception:
            pass
        match = re.search(r'"session_cookies":\s*\[(.*?)\]', text, re.DOTALL)
        if match:
            cookie_part = match.group(1)
            pairs = re.findall(r'"name":"([^"]+)","value":"([^"]+)"', cookie_part)
            if pairs:
                return '; '.join([f"{name}={value}" for name, value in pairs])
        return ""

    def _get_cookies_from_token(self, token: str) -> str:
        url = 'https://api.facebook.com/method/auth.getSessionforApp'
        payload = {
            'access_token': token,
            'format': 'json',
            'new_app_id': '350685531728',
            'generate_session_cookies': '1'
        }
        try:
            resp = self.session.post(url, data=payload, proxies=self.px_dict, timeout=30)
            data = resp.json()
            if 'error' in data:
                return ""
            cookies = data.get('session_cookies', [])
            if cookies:
                return '; '.join(f"{c['name']}={c['value']}" for c in cookies)
            return ""
        except Exception:
            return ""

    def _build_success_result(self, token: str, response_text: str = "") -> dict:
        cookies = self._get_cookies_from_token(token)
        if not cookies:
            if response_text:
                cookies = self._extract_cookies(response_text)
            if not cookies:
                cookie_jar = self.session.cookies
                if cookie_jar:
                    cookies = '; '.join([f"{c.name}={c.value}" for c in cookie_jar])
        return {
            'success': True,
            'access_token': token,
            'cookies': cookies
        }

    def login(self) -> dict:
        try:
            headers = self._build_gql_headers()
            payload = self._build_payload()
            resp = self.session.post(self.GQL_URL, data=payload, headers=headers, proxies=self.px_dict, timeout=30)
            text = resp.text

            token = self._extract_token(text)
            if token:
                return self._build_success_result(token, text)

            try:
                data = resp.json()
                errors = data.get('errors', [])
                if errors:
                    return {
                        'success': False,
                        'api_failed': 'LOGIN_GRAPHQL_ERROR',
                        'error': errors[0].get('message', 'Lỗi không xác định'),
                        'response_raw': text
                    }
            except Exception:
                pass

            err_match = re.search(r'"error_message":"([^"]*)"', text)
            if err_match:
                return {'success': False, 'api_failed': 'LOGIN_SEND_REQUEST', 'error': err_match.group(1), 'response_raw': text}

            return {
                'success': False,
                'api_failed': 'LOGIN_NO_TOKEN',
                'error': 'Đăng nhập không thành công, không nhận được token',
                'response_raw': text
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'api_failed': 'REQUEST_CONNECTION_ERROR',
                'error': f'Lỗi kết nối mạng/proxy: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'api_failed': 'UNKNOWN_EXCEPTION',
                'error': str(e)
            }


API_KEY_B64 = "QTdGMy05QjJFLTRDOEQtMUY2QS1LOU0y"

# ==============================================================================
# DANH SÁCH TÊN MỞ RỘNG (~30 họ + 50 tên nam + 50 tên nữ Việt Nam)
# + Tên quốc tế / Thái Lan / US Latinh khi IP không phải Việt Nam
# ==============================================================================
SURNAMES_VN = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
    "Bùi", "Đỗ", "Ngô", "Đinh", "Dương", "Lý", "Trương", "Lưu", "Lâm", "Mai",
    "Tô", "Hồ", "Đào", "Đoàn", "Trịnh", "Vương", "Phùng", "Cao", "Lương", "Thái",
]

MALE_VN = [
    "An", "Anh", "Bảo", "Bình", "Cường", "Dũng", "Duy", "Đạt", "Đức", "Hải",
    "Hiếu", "Hòa", "Hoàng", "Hùng", "Huy", "Hưng", "Khang", "Khánh", "Khoa", "Kiên",
    "Long", "Lộc", "Minh", "Nam", "Nghĩa", "Nguyên", "Nhân", "Phong", "Phúc", "Quang",
    "Quân", "Sang", "Sơn", "Tài", "Tấn", "Thành", "Thắng", "Thiện", "Thịnh", "Thông",
    "Toàn", "Trí", "Trung", "Tú", "Tuấn", "Tùng", "Vinh", "Vũ", "Vỹ", "Xuân",
]

FEMALE_VN = [
    "An", "Anh", "Chi", "Dung", "Duyên", "Giang", "Hà", "Hằng", "Hạnh", "Hiền",
    "Hoa", "Hồng", "Hương", "Huyền", "Khánh", "Lam", "Lan", "Linh", "Loan", "Mai",
    "Minh", "My", "Nga", "Ngân", "Ngọc", "Nguyệt", "Nhi", "Nhung", "Oanh", "Phương",
    "Quỳnh", "Sa", "Tâm", "Thảo", "Thắm", "Thi", "Thu", "Thủy", "Thương", "Tiên",
    "Trang", "Trinh", "Trúc", "Tuyết", "Vân", "Vi", "Vy", "Yến", "Ý", "Hân",
]

INTL_FIRST_NAMES_MALE = ["Somchai", "Arthit", "Kittisak", "Thanawat", "Chaiwat", "Alex", "David", "John", "Michael", "James"]
INTL_FIRST_NAMES_FEMALE = ["Sunisa", "Pornthip", "Kanya", "Siriporn", "Apinya", "Emma", "Sarah", "Emily", "Jessica", "Sophia"]
INTL_LAST_NAMES = ["Prasert", "Suksom", "Wongsuwan", "Rattana", "Thongdee", "Smith", "Johnson", "Brown", "Miller", "Davis"]

SURNAMES_US = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson"]
MALE_US = ["James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Charles","Christopher","Daniel","Matthew","Anthony","Donald"]
FEMALE_US = ["Mary","Patricia","Jennifer","Linda","Barbara","Elizabeth","Susan","Jessica","Sarah","Karen","Lisa","Nancy","Betty","Margaret","Sandra"]

# ==============================================================================
# BẢNG MÃ KHU VỰC US + BỘ TẠO SĐT THÔNG MINH THEO GEO IP PROXY
# ==============================================================================
US_AREA_CODES = [
    "205","251","256","334","938","907","480","520","602","623","928","479","501","870",
    "209","213","310","323","408","415","424","442","510","530","559","562","619","626",
    "650","657","661","669","707","714","747","760","805","818","831","858","909","916",
    "925","949","951","303","719","720","970","203","475","860","959","302","239","305",
    "321","352","386","407","561","727","754","772","786","813","850","863","904","941",
    "954","229","404","470","478","678","706","762","770","912","808","208","986","217",
    "224","309","312","331","618","630","708","773","779","815","847","872","219","260",
    "317","463","574","765","812","930","319","515","563","641","712","316","620","785",
    "913","270","364","502","606","859","225","318","337","504","985","207","227","240",
    "301","410","443","667","339","351","413","508","617","774","781","857","978","231",
    "248","269","313","517","586","616","734","810","906","947","989","218","320","507",
    "612","651","763","952","228","601","662","769","314","417","557","573","636","660",
    "816","406","308","402","531","702","725","775","603","201","551","609","640","732",
    "848","856","862","908","973","505","575","212","315","332","347","516","518","585",
    "607","631","646","680","716","718","838","845","914","917","929","934","252","336"
]
US_INVALID_AREA_CODES = {
    "800","833","844","855","866","877","888","889","900","911","411",
    "500","522","533","544","555","566","577","588"
}
VALID_US_AREA_CODES = [c for c in US_AREA_CODES if c not in US_INVALID_AREA_CODES]


# ==============================================================================
# GIAO DIỆN TERMINAL VÀ BẢNG MÀU CHUẨN
# ==============================================================================
def _init_windows_vt():
    """Kích hoạt Virtual Terminal Processing trên Windows console để hỗ trợ màu ANSI."""
    if os.name == 'nt':
        try:
            os.system('')
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hOut = kernel32.GetStdHandle(-11)
            out_mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(hOut, ctypes.byref(out_mode)):
                if kernel32.SetConsoleMode(hOut, out_mode.value | 0x0004):
                    return True
        except Exception:
            pass
        try:
            import colorama
            colorama.just_fix_windows_console()
            return True
        except Exception:
            pass
        return False
    return True

_VT_SUPPORTED = _init_windows_vt()


class C:
    if _VT_SUPPORTED:
        RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
        BLACK = "\033[30m"; RED = "\033[31m"; GREEN = "\033[32m"; YELLOW = "\033[33m"
        BLUE = "\033[34m"; MAGENTA = "\033[35m"; CYAN = "\033[36m"; WHITE = "\033[37m"
        BRED = "\033[91m"; BGREEN = "\033[92m"; BYELLOW = "\033[93m"; BBLUE = "\033[94m"
        BMAGENTA = "\033[95m"; BCYAN = "\033[96m"; BWHITE = "\033[97m"
        BG_RED = "\033[41m"; BG_GREEN = "\033[42m"; BG_YELLOW = "\033[43m"
        BG_BLUE = "\033[44m"; BG_MAG = "\033[45m"; BG_CYAN = "\033[46m"
        PINK = "\033[38;5;213m"; TEAL = "\033[38;5;80m"; LIME = "\033[38;5;154m"
        LAV = "\033[38;5;141m"; GRAY = "\033[38;5;245m"; DGRAY = "\033[38;5;240m"
        GOLD = "\033[38;5;220m"; ORANGE = "\033[38;5;208m"; SKY = "\033[38;5;117m"
        MINT = "\033[38;5;121m"
        BG_STEP = "\033[48;5;30m"; BG_OK = "\033[48;5;28m"; BG_INFO = "\033[48;5;25m"
        BG_WARN = "\033[48;5;136m"; BG_ERR = "\033[48;5;88m"; BG_TLS = "\033[48;5;54m"
        BG_COOKIE = "\033[48;5;94m"; BG_TOKEN = "\033[48;5;31m"; BG_LIVE = "\033[48;5;22m"
        BG_PROXY = "\033[48;5;24m"; BG_MAIL = "\033[48;5;90m"; BG_CHECK = "\033[48;5;23m"
        BG_DIALOG = "\033[48;5;91m"
    else:
        RESET = BOLD = DIM = ""
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""
        BRED = BGREEN = BYELLOW = BBLUE = BMAGENTA = BCYAN = BWHITE = ""
        BG_RED = BG_GREEN = BG_YELLOW = BG_BLUE = BG_MAG = BG_CYAN = ""
        PINK = TEAL = LIME = LAV = GRAY = DGRAY = GOLD = ORANGE = SKY = MINT = ""
        BG_STEP = BG_OK = BG_INFO = BG_WARN = BG_ERR = BG_TLS = ""
        BG_COOKIE = BG_TOKEN = BG_LIVE = BG_PROXY = BG_MAIL = BG_CHECK = BG_DIALOG = ""

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(s: str) -> str:
    return ANSI_ESCAPE_RE.sub('', str(s))

def safe_print(*args, **kwargs):
    if not _VT_SUPPORTED:
        clean_args = [strip_ansi(a) for a in args]
        print(*clean_args, **kwargs)
    else:
        print(*args, **kwargs)

def color(text, code):
    if not _VT_SUPPORTED or not code:
        return strip_ansi(text)
    return f"{code}{text}{C.RESET}"


class AppLogger:
    TAGS = {
        "INFO":   (C.BG_INFO + C.BWHITE + C.BOLD,   " INFO "),
        "STEP":   (C.BG_STEP + C.BWHITE + C.BOLD,   " STEP "),
        "OK":     (C.BG_OK + C.BLACK + C.BOLD,      "  OK  "),
        "WARN":   (C.BG_WARN + C.BLACK + C.BOLD,    " WARN "),
        "ERR":    (C.BG_ERR + C.BWHITE + C.BOLD,    " ERR  "),
        "CHKPT":  (C.BG_MAG + C.BWHITE + C.BOLD,    "CHKPT "),
        "TOKN":   (C.BG_TOKEN + C.BWHITE + C.BOLD,  "TOKEN "),
        "MEDIA":  (C.BG_MAG + C.BWHITE + C.BOLD,    "MEDIA "),
        "PROXY":  (C.BG_PROXY + C.BWHITE + C.BOLD,  "PROXY "),
        "MAIL":   (C.BG_MAIL + C.BWHITE + C.BOLD,   " MAIL "),
        "WAIT":   (C.BG_WARN + C.BLACK + C.BOLD,    " WAIT "),
        "LIVE":   (C.BG_LIVE + C.BWHITE + C.BOLD,   " LIVE "),
        "CHECK":  (C.BG_CHECK + C.BWHITE + C.BOLD,  "CHECK "),
        "DIALOG": (C.BG_DIALOG + C.BWHITE + C.BOLD, "DIALOG"),
        "COOKIE": (C.BG_COOKIE + C.BWHITE + C.BOLD, "COOKIE"),
        "TLS":    (C.BG_TLS + C.BWHITE + C.BOLD,    " TLS  "),
        "HTTP":   (C.BG_STEP + C.BWHITE + C.BOLD,   " HTTP "),
        "GEO":    (C.BG_INFO + C.BWHITE + C.BOLD,   " GEO  "),
    }

    @staticmethod
    def _now():
        return datetime.datetime.now().strftime("%H:%M:%S")

    @classmethod
    def _tag(cls, key: str) -> str:
        style, label = cls.TAGS.get(key, (C.BOLD, f"{key[:6]:<6}"))
        return color(f"[{label}]", style)

    @classmethod
    def _emit(cls, key, msg, msg_color=""):
        ts = color(cls._now(), C.DGRAY)
        tag = cls._tag(key)
        body = color(str(msg), msg_color) if msg_color else str(msg)
        safe_print(f"{ts} {tag} {body}")

    @classmethod
    def info(cls, msg):
        cls._emit("INFO", msg, C.BWHITE)

    @classmethod
    def step(cls, n, name, detail=""):
        ts = color(cls._now(), C.DGRAY)
        tag = cls._tag("STEP")
        num = color(f"{int(n):02d}", C.BOLD + C.BCYAN)
        title = color(str(name), C.BOLD + C.BWHITE)
        if detail:
            arrow = color(" -> ", C.DGRAY)
            det = color(str(detail), C.BYELLOW)
            safe_print(f"{ts} {tag} {num} {title}{arrow}{det}")
        else:
            safe_print(f"{ts} {tag} {num} {title}")

    @classmethod
    def success(cls, msg):
        cls._emit("OK", msg, C.LIME)

    @classmethod
    def warn(cls, msg):
        cls._emit("WARN", msg, C.GOLD)

    @classmethod
    def error(cls, msg):
        cls._emit("ERR", msg, C.BRED)

    @classmethod
    def checkpoint(cls, msg):
        cls._emit("CHKPT", msg, C.PINK)

    @classmethod
    def check(cls, msg):
        cls._emit("CHECK", msg, C.MINT)

    @classmethod
    def dialog(cls, msg):
        cls._emit("DIALOG", msg, C.LAV)

    @classmethod
    def token(cls, name, value):
        v = str(value or "")
        short = (v[:40] + "...") if len(v) > 40 else v
        cls._emit("TOKN", f"{name}: {short}", C.SKY)

    @classmethod
    def proxy(cls, msg):
        cls._emit("PROXY", msg, C.TEAL)

    @classmethod
    def mail(cls, msg):
        cls._emit("MAIL", msg, C.PINK)

    @classmethod
    def wait(cls, msg):
        cls._emit("WAIT", msg, C.GOLD)

    @classmethod
    def cookie(cls, msg):
        cls._emit("COOKIE", msg, C.ORANGE)

    @classmethod
    def tls(cls, msg):
        cls._emit("TLS", msg, C.LAV)

    @classmethod
    def live(cls, msg):
        cls._emit("LIVE", msg, C.LIME)

    @classmethod
    def http(cls, msg):
        cls._emit("HTTP", msg, C.MINT)

    @classmethod
    def geo(cls, msg):
        cls._emit("GEO", msg, C.BCYAN)

    @classmethod
    def banner(cls, title: str, color_code=None):
        cc = color_code or (C.BOLD + C.BGREEN)
        line = color("=" * 78, C.BGREEN)
        safe_print(line)
        safe_print(color(f"  {title}", cc))
        safe_print(line)

    @classmethod
    def section(cls, title: str):
        width = 78
        inner = f" * {title} * "
        side = max(2, (width - len(inner)) // 2)
        right_n = max(2, width - side - len(inner))
        safe_print(
            color("=" * side, C.DGRAY)
            + color(inner, C.BOLD + C.BYELLOW)
            + color("=" * right_n, C.DGRAY)
        )

    @classmethod
    def phase_header(cls, phase_no: int, title: str):
        width = 78
        plain = f" * PHASE {phase_no}: {title} * "
        side = max(2, (width - len(plain)) // 2)
        right_n = max(2, width - side - len(plain))
        mid = (
            color(" * ", C.GOLD)
            + color(f"PHASE {phase_no}: ", C.BOLD + C.BYELLOW)
            + color(str(title), C.BOLD + C.BWHITE)
            + color(" * ", C.GOLD)
        )
        safe_print(
            color("=" * side, C.DGRAY)
            + mid
            + color("=" * right_n, C.DGRAY)
        )

    @classmethod
    def persona_box(cls, country, device, name, phone, password, proxy):
        sep = color("-" * 78, C.DGRAY)
        safe_print(sep)
        def row(k, v, vc=C.BWHITE):
            safe_print(f"  {color(f'{k:<10}', C.GRAY)} {color(str(v), vc)}")
        row("Country", country, C.BYELLOW)
        row("Device", device, C.BCYAN)
        row("Name", name, C.BWHITE)
        row("SDT MOI", phone, C.LIME)
        row("Password", password, C.GOLD)
        row("Proxy", proxy or "DIRECT", C.TEAL)
        safe_print(sep)

    @classmethod
    def job_header(cls, thread_idx, job_no, live_cur, live_target, proxy):
        ts = color(cls._now(), C.DGRAY)
        tag = color(f"[L{thread_idx}]", C.BOLD + C.BCYAN)
        msg = f"===== thu #{job_no}  live {live_cur}/{live_target}  px={proxy or 'DIRECT'} ====="
        safe_print(f"{ts} {tag} {color(msg, C.DGRAY)}")

    @classmethod
    def config_box(cls, title: str, rows: list):
        line = color("=" * 78, C.BGREEN)
        safe_print(line)
        safe_print(color(f"  {title}", C.BOLD + C.BGREEN))
        for k, v in rows:
            safe_print(f"   {color('•', C.LIME)} {color(f'{k:<16}', C.GRAY)} {color(str(v), C.BWHITE)}")
        safe_print(line)

    @classmethod
    def live_banner(cls, thread_idx, cur_ok, target_live, job_no, extra: str = ""):
        deep_green = "\033[38;5;34m\033[1m" if _VT_SUPPORTED else ""
        deep_bg = "\033[48;5;22m\033[38;5;154m\033[1m" if _VT_SUPPORTED else ""
        reset = C.RESET if _VT_SUPPORTED else ""
        width = 56
        msg = f"[L{thread_idx}] ✓ LIVE #{cur_ok}/{target_live} (thu #{job_no})"
        if extra:
            msg = f"{msg}  {extra}"
        if len(msg) > width - 4:
            msg = msg[: width - 7] + "..."
        pad = width - 2 - len(msg)
        left = pad // 2
        right = pad - left
        top = "╔" + "═" * (width - 2) + "╗"
        mid = "║" + " " * left + msg + " " * right + "║"
        bot = "╚" + "═" * (width - 2) + "╝"
        outer_pad = max(0, (78 - width) // 2)
        sp = " " * outer_pad
        safe_print("")
        safe_print(sp + deep_green + top + reset)
        safe_print(sp + deep_bg + mid + reset)
        safe_print(sp + deep_green + bot + reset)
        safe_print("")


# ==============================================================================
# PATHS & FILE SAVE (CROSS-PROCESS SAFE)
# ==============================================================================
try:
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
except Exception:
    BASE_DIR = os.path.abspath(os.path.dirname(sys.argv[0])) if sys.argv and sys.argv[0] else os.getcwd()

ACCOUNTS_FULL_FILE = os.path.join(BASE_DIR, "accounts_full.txt")
ACCOUNTS_2FA_FILE = os.path.join(BASE_DIR, "accounts_2fa.txt")
ACCOUNTS_EXCEL_FILE = os.path.join(BASE_DIR, "accounts_success.xlsx")


@contextmanager
def cross_process_file_lock(lock_name="save_account.lock"):
    lock_path = os.path.join(BASE_DIR, lock_name)
    lock_f = None
    start_t = time.time()
    try:
        lock_f = open(lock_path, "a+")
        while True:
            try:
                if HAS_MSVCRT:
                    msvcrt.locking(lock_f.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except (IOError, OSError):
                if time.time() - start_t > 15:
                    break
                time.sleep(random.uniform(0.05, 0.2))
        yield
    finally:
        if lock_f:
            try:
                if HAS_MSVCRT:
                    lock_f.seek(0)
                    msvcrt.locking(lock_f.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                pass
            try:
                lock_f.close()
            except Exception:
                pass


def safe_append_account_line(file_path: str, line: str) -> bool:
    try:
        with cross_process_file_lock("accounts_save.lock"):
            needs_leading_newline = False
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                try:
                    with open(file_path, "rb") as rf:
                        rf.seek(-1, os.SEEK_END)
                        last_char = rf.read(1)
                        if last_char not in (b'\n', b'\r'):
                            needs_leading_newline = True
                except Exception:
                    pass

            with open(file_path, "a", encoding="utf-8") as f:
                if needs_leading_newline:
                    f.write("\n")
                clean_line = line.strip("\r\n")
                f.write(f"{clean_line}\n")
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
        return True
    except Exception as e:
        AppLogger.error(f"❌ Lỗi ghi an toàn vào {file_path}: {e}")
        return False


def save_to_excel(uid, pwd, twofa, mail, cookie, token):
    if not HAS_OPENPYXL:
        return
    try:
        with cross_process_file_lock("excel_save.lock"):
            if not os.path.exists(ACCOUNTS_EXCEL_FILE):
                wb = Workbook()
                ws = wb.active
                ws.append(["UID", "Pass", "2FA", "Email", "Cookie", "Token"])
            else:
                wb = load_workbook(ACCOUNTS_EXCEL_FILE)
                ws = wb.active
            ws.append([uid, pwd, twofa, mail, cookie, token])
            wb.save(ACCOUNTS_EXCEL_FILE)
    except Exception as e:
        AppLogger.warn(f"Lỗi khi lưu file Excel '{ACCOUNTS_EXCEL_FILE}': {e}")


# ==============================================================================
# FINGERPRINT TRÌNH DUYỆT
# ==============================================================================
def generate_random_browser_profile(thread_seed: int = None) -> Tuple[Dict[str, str], Dict[str, str]]:
    rng = random.Random()
    if thread_seed is not None:
        rng.seed(hash((int(thread_seed), time.time_ns(), random.getrandbits(32))) & 0xFFFFFFFF)

    chrome_versions = [
        {"v": "133", "full": "133.0.6943.127", "ua": "133.0.0.0"},
        {"v": "133", "full": "133.0.6943.98", "ua": "133.0.0.0"},
        {"v": "132", "full": "132.0.6834.160", "ua": "132.0.0.0"},
        {"v": "132", "full": "132.0.6834.111", "ua": "132.0.0.0"},
        {"v": "131", "full": "131.0.6778.205", "ua": "131.0.0.0"},
        {"v": "131", "full": "131.0.6778.109", "ua": "131.0.0.0"},
        {"v": "130", "full": "130.0.6723.117", "ua": "130.0.0.0"},
        {"v": "129", "full": "129.0.6668.100", "ua": "129.0.0.0"},
        {"v": "128", "full": "128.0.6613.137", "ua": "128.0.0.0"},
    ]
    ch = rng.choice(chrome_versions)

    os_profiles = [
        {"ua_os": "Windows NT 10.0; Win64; x64", "platform": '"Windows"', "platform_version": rng.choice(['"10.0.0"', '"15.0.0"'])},
        {"ua_os": "Windows NT 10.0; Win64; x64", "platform": '"Windows"', "platform_version": '"14.0.0"'},
        {"ua_os": "Macintosh; Intel Mac OS X 10_15_7", "platform": '"macOS"', "platform_version": rng.choice(['"14.5.0"', '"13.6.0"', '"12.7.0"'])},
        {"ua_os": "X11; Linux x86_64", "platform": '"Linux"', "platform_version": '""'},
    ]
    osp = rng.choice(os_profiles)

    screens = [
        {"wd": "1920x1080", "dpr": "1"},
        {"wd": "1920x1080", "dpr": "1.25"},
        {"wd": "1536x864", "dpr": "1.25"},
        {"wd": "1366x768", "dpr": "1"},
        {"wd": "1440x900", "dpr": "1"},
        {"wd": "1600x900", "dpr": "1"},
        {"wd": "2560x1440", "dpr": "1.5"},
        {"wd": "1280x720", "dpr": "1"},
        {"wd": "1680x1050", "dpr": "1"},
        {"wd": "2560x1600", "dpr": "2"},
        {"wd": "3840x2160", "dpr": "1.5"},
    ]
    sc = rng.choice(screens)

    device_id = str(uuid.uuid4())
    family_device_id = str(uuid.uuid4())
    machine_id = "".join(rng.choices(string.ascii_letters + string.digits, k=24))
    client_id = str(uuid.uuid4())

    brands = [
        f'"Not(A:Brand";v="99", "Google Chrome";v="{ch["v"]}", "Chromium";v="{ch["v"]}"',
        f'"Chromium";v="{ch["v"]}", "Not=A?Brand";v="24", "Google Chrome";v="{ch["v"]}"',
        f'"Google Chrome";v="{ch["v"]}", "Chromium";v="{ch["v"]}", "Not_A Brand";v="99"',
    ]
    sec_ch = rng.choice(brands)

    profile = {
        "ua": f"Mozilla/5.0 ({osp['ua_os']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ch['ua']} Safari/537.36",
        "sec_ch_ua": sec_ch,
        "sec_ch_ua_full": f'"Not(A:Brand";v="99.0.0.0", "Google Chrome";v="{ch["full"]}", "Chromium";v="{ch["full"]}"',
        "platform": osp["platform"],
        "platform_version": osp["platform_version"],
        "is_mobile": "?0",
        "model": '""',
        "device_id": device_id,
        "family_device_id": family_device_id,
        "machine_id": machine_id,
        "client_id": client_id,
        "chrome_v": ch["v"],
    }
    screen_info = {"wd": sc["wd"], "dpr": sc["dpr"]}
    return profile, screen_info


# ==============================================================================
# SĐT MỒI THEO QUỐC GIA (TỰ ĐỘNG KHỚP IP PROXY)
# ==============================================================================
def generate_phone_by_country(country_code: str = "TH") -> str:
    cc = (country_code or "TH").upper()
    if cc == "TH":
        th_prefixes = [
            "61", "62", "63", "64", "65", "66",
            "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
            "90", "91", "92", "93", "94", "95", "96", "97", "98", "99"
        ]
        pfx = random.choice(th_prefixes)
        suffix = "".join(random.choices(string.digits, k=7))
        return f"+66{pfx}{suffix}"
    elif cc == "VN":
        prefixes = ['32','33','34','35','36','37','38','39','96','97','98','86','88','91','94','83','84','85','81','82','89','90','93','70','79','77','76','78','92','56','58','99','59']
        pfx = random.choice(prefixes)
        suffix = "".join(random.choices(string.digits, k=7))
        return f"+84{pfx}{suffix}"
    elif cc == "PH":
        pfx = random.choice(["905", "906", "915", "916", "917", "926", "927", "935", "936", "995", "918", "919", "920", "921", "928", "929", "939", "947", "949", "970", "981"])
        suffix = "".join(random.choices(string.digits, k=7))
        return f"+63{pfx}{suffix}"
    elif cc == "ID":
        pfx = random.choice(["812", "813", "821", "822", "852", "853", "811", "817", "818", "819", "859", "877", "878", "896", "897", "898", "899"])
        suffix = "".join(random.choices(string.digits, k=7))
        return f"+62{pfx}{suffix}"
    elif cc == "MY":
        pfx = random.choice(["11", "12", "13", "14", "16", "17", "18", "19"])
        suffix = "".join(random.choices(string.digits, k=7))
        return f"+60{pfx}{suffix}"
    elif cc == "IN":
        pfx = random.choice(["98", "99", "97", "96", "95", "94", "93", "92", "91", "90", "88", "87", "86", "85", "84", "83", "82", "81", "80", "79", "78", "77", "76", "75", "74", "73", "72", "70", "63", "62"])
        suffix = "".join(random.choices(string.digits, k=8))
        return f"+91{pfx}{suffix}"
    else:
        area = random.choice(VALID_US_AREA_CODES)
        n1 = random.randint(2, 9)
        x1 = random.randint(0, 9)
        x2 = random.randint(0, 9)
        n2 = random.randint(2, 9)
        suffix = f"{n1}{x1}{x2}{n2}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
        return f"+1{area}{suffix}"


def generate_valid_phone_for_country(country_code: str = "TH") -> str:
    return generate_phone_by_country(country_code)


def generate_fake_phone(area_code=None):
    return generate_phone_by_country("US")


def validate_us_phone(phone):
    return True


def generate_valid_us_phone(max_attempts=20):
    return generate_phone_by_country("US")


def generate_fake_intermediate_email():
    providers = ["gmail.com", "icloud.com", "outlook.com"]
    pfx = ["john", "sarah", "alex", "david", "emma", "lucas", "sophia", "ryan", "olivia", "noah"]
    sfx = ["smith", "miller", "taylor", "brown", "davis", "wilson", "moore", "clark", "walker"]
    return f"{random.choice(pfx)}{random.choice(sfx)}{random.randint(100, 9999)}@{random.choice(providers)}"


# ==============================================================================
# GEO DETECTION — KHÓA CỨNG COUNTRY THEO PROXY
# ==============================================================================
def detect_proxy_geo(session: requests.Session, proxy_str: str = "") -> dict:
    """
    Nhận diện quốc gia KHÓA CỨNG theo proxy — không nhảy nước:
      1. region-XX / country-XX trong chuỗi proxy
      2. Keyword quốc gia trong proxy
      3. GeoIP API — CHỈ khi chưa khóa được từ proxy
      4. Fallback: TH
    """
    detected_cc = None
    detected_tz = "Asia/Bangkok"
    locked_from_proxy = False
    search_target = (proxy_str or str(session.proxies.get("http", "") or "") or "").strip()

    if search_target:
        m_region = re.search(
            r"(?:^|[-_./?&=])(?:region|country|cc|geo|loc)[-_=]([a-zA-Z]{2})(?:$|[-_./?&=])",
            search_target,
            re.IGNORECASE,
        )
        if not m_region:
            m_region = re.search(r"[-_](?:region|country)[-_]([a-zA-Z]{2})\b", search_target, re.IGNORECASE)
        if m_region:
            detected_cc = m_region.group(1).upper()
            locked_from_proxy = True
            try:
                AppLogger.geo(f"KHÓA quốc gia từ Proxy config: {detected_cc} (GeoIP không ghi đè)")
            except Exception:
                print(f"[GEO] KHÓA quốc gia từ Proxy: {detected_cc}")

    if not detected_cc and search_target:
        low = search_target.lower()
        kw_map = [
            (r"(?:thailand|bangkok|region-th|country-th|(?:^|[-_])th(?:[-_]|$))", "TH"),
            (r"(?:vietnam|saigon|hanoi|region-vn|country-vn|(?:^|[-_])vn(?:[-_]|$))", "VN"),
            (r"(?:indonesia|jakarta|region-id|country-id)", "ID"),
            (r"(?:philippines|manila|region-ph|country-ph)", "PH"),
            (r"(?:malaysia|kuala|region-my|country-my)", "MY"),
            (r"(?:india|mumbai|region-in|country-in)", "IN"),
            (r"(?:united.?states|america|region-us|country-us|(?:^|[-_])us(?:[-_]|$))", "US"),
            (r"(?:singapore|region-sg|country-sg)", "SG"),
            (r"(?:laos|region-la|country-la)", "LA"),
            (r"(?:cambodia|region-kh|country-kh)", "KH"),
        ]
        for pat, cc in kw_map:
            if re.search(pat, low, re.IGNORECASE):
                detected_cc = cc
                locked_from_proxy = True
                try:
                    AppLogger.geo(f"KHÓA quốc gia từ keyword Proxy: {detected_cc}")
                except Exception:
                    print(f"[GEO] KHÓA từ keyword Proxy: {detected_cc}")
                break

    endpoints = [
        ("http://ip-api.com/json", 3),
        ("https://ipinfo.io/json", 3),
        ("https://api.myip.com", 3),
    ]
    ip_addr = "unknown"
    country_name = ""
    api_cc = None

    for url, t_out in endpoints:
        try:
            r = session.get(url, timeout=t_out)
            if r.status_code != 200:
                continue
            data = r.json() if r.text else {}
            if not isinstance(data, dict):
                continue
            cc = (data.get("countryCode") or data.get("country") or data.get("cc") or "").upper()
            if len(cc) != 2:
                cc = ""
            if cc:
                api_cc = cc
            if data.get("timezone") and not locked_from_proxy:
                detected_tz = data.get("timezone")
            ip_addr = data.get("query") or data.get("ip") or ip_addr
            country_name = data.get("country") or data.get("country_name") or country_name
            break
        except Exception:
            continue

    if locked_from_proxy and detected_cc:
        if api_cc and api_cc != detected_cc:
            try:
                AppLogger.warn(
                    f"GeoIP báo {api_cc} nhưng Proxy khóa {detected_cc} → giữ {detected_cc}"
                )
            except Exception:
                print(f"[!] GeoIP={api_cc} != Proxy={detected_cc} → giữ {detected_cc}")
    elif api_cc:
        detected_cc = api_cc
        try:
            AppLogger.geo(f"Quốc gia từ GeoIP (proxy không có region): {detected_cc}")
        except Exception:
            print(f"[GEO] Từ GeoIP: {detected_cc}")

    if not detected_cc:
        up = search_target.upper()
        if "VN" in up:
            detected_cc = "VN"
        elif re.search(r"(?:^|[-_])US(?:[-_]|$)", up):
            detected_cc = "US"
        else:
            detected_cc = "TH"
        try:
            AppLogger.warn(f"Không detect được region → fallback {detected_cc}")
        except Exception:
            print(f"[!] fallback country={detected_cc}")

    _GEO_TABLE = {
        "TH": ("th_TH", "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7", "th,en-US;q=0.9,en;q=0.8", "Thailand", "Asia/Bangkok"),
        "VN": ("vi_VN", "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7", "vi,en-US;q=0.9,en;q=0.8", "Vietnam", "Asia/Ho_Chi_Minh"),
        "US": ("en_US", "en-US,en;q=0.9", "en-US,en;q=0.8", "United States", "America/New_York"),
        "ID": ("id_ID", "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7", "id,en-US;q=0.9,en;q=0.8", "Indonesia", "Asia/Jakarta"),
        "PH": ("en_PH", "en-PH,en;q=0.9,fil;q=0.8", "en-PH,en;q=0.9", "Philippines", "Asia/Manila"),
        "MY": ("ms_MY", "ms-MY,ms;q=0.9,en-US;q=0.8,en;q=0.7", "ms,en-US;q=0.9,en;q=0.8", "Malaysia", "Asia/Kuala_Lumpur"),
        "IN": ("en_IN", "en-IN,en;q=0.9,hi;q=0.8", "en-IN,en;q=0.9", "India", "Asia/Kolkata"),
        "SG": ("en_SG", "en-SG,en;q=0.9", "en-SG,en;q=0.9", "Singapore", "Asia/Singapore"),
        "LA": ("lo_LA", "lo-LA,lo;q=0.9,en;q=0.8", "lo,en;q=0.9", "Laos", "Asia/Vientiane"),
        "KH": ("km_KH", "km-KH,km;q=0.9,en;q=0.8", "km,en;q=0.9", "Cambodia", "Asia/Phnom_Penh"),
    }
    if detected_cc in _GEO_TABLE:
        locale, accept_lang, accept_lang_simple, country_name, detected_tz = _GEO_TABLE[detected_cc]
    else:
        locale = "en_US"
        accept_lang = f"{detected_cc.lower()}-{detected_cc},en-US;q=0.9,en;q=0.8"
        accept_lang_simple = "en-US,en;q=0.8"
        country_name = country_name or detected_cc
        detected_tz = detected_tz or "UTC"

    res = {
        "countryCode": detected_cc,
        "country": country_name,
        "timezone": detected_tz,
        "query": ip_addr,
        "locale": locale,
        "accept_lang": accept_lang,
        "accept_lang_simple": accept_lang_simple,
        "locked": locked_from_proxy,
        "api_cc": api_cc,
    }
    lock_tag = "LOCKED" if locked_from_proxy else "geo"
    try:
        AppLogger.geo(
            f"IP={ip_addr} | Country={country_name} ({detected_cc}) [{lock_tag}] | TZ={detected_tz} | Locale={locale}"
        )
    except Exception:
        print(f"[GEO] IP={ip_addr} | {country_name} ({detected_cc}) [{lock_tag}] | TZ={detected_tz}")
    return res


# ==============================================================================
# CHECK ACCOUNT LIVE + BYPASS 049
# ==============================================================================
def check_account_and_bypass_049(session, browser_profile, uid):
    print("\n[+] Đang thực hiện: 3. Check Account & Bypass 049")
    time.sleep(random.uniform(2.0, 3.5))
    url = "https://www.facebook.com/"
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
        'sec-ch-ua': browser_profile['sec_ch_ua'],
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': browser_profile['platform'],
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': browser_profile['ua']
    }
    try:
        r = session.get(url, headers=headers, allow_redirects=True, timeout=15)
        final_url = r.url
        if "checkpoint" in final_url:
            if "601051028565049" in final_url:
                print("    - Cảnh báo: Dính CheckPoint 049 (Scraping Warning). Đang tiến hành gỡ...")
                dtsg_match = re.search(r'name="fb_dtsg" value="(.*?)"', r.text)
                lsd_match = re.search(r'name="lsd" value="(.*?)"', r.text)
                if not dtsg_match:
                    dtsg_match = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"}', r.text)
                if not dtsg_match:
                    print("    - Không tìm thấy fb_dtsg để gỡ 049.")
                    return False
                fb_dtsg = dtsg_match.group(1)
                lsd = lsd_match.group(1) if lsd_match else ""
                
                jazoest = compute_jazoest(fb_dtsg)
                
                bypass_url = "https://www.facebook.com/api/graphql/"
                bypass_headers = {
                    'accept': '*/*',
                    'content-type': 'application/x-www-form-urlencoded',
                    'origin': 'https://www.facebook.com',
                    'referer': final_url,
                    'user-agent': browser_profile['ua'],
                    'sec-ch-ua': browser_profile['sec_ch_ua'],
                    'sec-ch-ua-platform': browser_profile['platform']
                }
                bypass_data = {
                    'av': uid, '__user': uid, '__a': '1', '__req': '1',
                    'fb_dtsg': fb_dtsg, 'jazoest': jazoest, 'lsd': lsd,
                    'fb_api_caller_class': 'RelayModern',
                    'fb_api_req_friendly_name': 'FBScrapingWarningMutation',
                    'server_timestamps': 'true',
                    'variables': '{}',
                    'doc_id': '24406519995698862'
                }
                rb = session.post(bypass_url, headers=bypass_headers, data=bypass_data)
                if "data" in rb.text:
                    print("    - Gỡ CheckPoint 049 THÀNH CÔNG!")
                    return True
                else:
                    print("    - Gỡ CheckPoint 049 thất bại.")
                    return False
            elif "1501092823525282" in final_url:
                print("    - Cảnh báo: Facebook bắt CheckPoint 282 (Yêu cầu tải lên ảnh xác minh). Tài khoản bị tạm khóa!")
                return False
            else:
                print(f"    - Cảnh báo: Chuyển hướng CheckPoint: {final_url}. Tài khoản chưa sẵn sàng!")
                return False
        else:
            print("    - Tài khoản Live sạch sẽ.")
            return True
    except Exception as e:
        print(f"    - Lỗi khi check account: {e}")
        return False


# ==============================================================================
# 2FA TOTP & KATANA BLOKS GRAPHQL UP 2FA (CHUẨN 100% TỪ HAR)
# ==============================================================================
def get_totp_token(secret: str) -> str:
    """Sinh mã TOTP 6 số từ secret base32, hỗ trợ cả pyotp và thuật toán thuần RFC 6238."""
    if not secret:
        return ""
    clean_secret = secret.replace(" ", "").strip().upper()
    try:
        import pyotp
        return pyotp.TOTP(clean_secret).now()
    except Exception:
        pass
    
    try:
        missing_padding = len(clean_secret) % 8
        if missing_padding:
            clean_secret += '=' * (8 - missing_padding)
        key = base64.b32decode(clean_secret, casefold=True)
        counter = int(time.time() // 30)
        counter_bytes = struct.pack(">Q", counter)
        mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = mac[-1] & 0x0F
        binary = struct.unpack(">I", mac[offset:offset+4])[0] & 0x7FFFFFFF
        token = str(binary % 1000000).zfill(6)
        return token
    except Exception as e:
        print(f"[-] Lỗi sinh mã TOTP: {e}")
        return ""


def wait_for_new_totp(secret: str, old_code: Optional[str] = None):
    if not secret or secret == "NO_2FA":
        return
    if old_code is None:
        old_code = get_totp_token(secret)
    print(f"\n[*] Đang chờ chu kỳ mã TOTP mới (tránh trùng mã vừa bật 2FA: {old_code})...")
    start = time.time()
    while time.time() - start < 35:
        now_code = get_totp_token(secret)
        if now_code != old_code:
            time.sleep(2)
            print(f"    - Đã chuyển sang mã TOTP mới: {now_code}")
            return
        remaining = 30 - (int(time.time()) % 30)
        print(f"    ... Đang chờ mã mới đổi (còn khoảng {remaining}s)")
        time.sleep(3)
    time.sleep(2)


# ==============================================================================
# KHO THIẾT BỊ USER-AGENT KATANA ANDROID CHUẨN THẬT 100%
# ==============================================================================
KATANA_DEVICE_POOL = [
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

KATANA_FBAV_VERSIONS = [
    ('510.0.0.72.41', '725719471'),
    ('543.0.0.55.73', '846638243'),
    ('540.0.0.42.50', '838765431'),
    ('535.0.0.40.114', '825638102'),
    ('530.0.0.34.82', '812456789'),
]

KATANA_CARRIERS = ['Viettel', 'Vinaphone', 'MobiFone', 'Vietnamobile', 'VN MOBIFONE', 'VIETTEL']
KATANA_LOCALES = ['vi_VN', 'en_US']


def generate_random_katana_ua(seed: Optional[str] = None) -> str:
    """
    Sinh User-Agent Katana Android ngẫu nhiên từ kho thiết bị thực tế.
    Nếu có `seed` (ví dụ UID), UA sẽ CỐ ĐỊNH DUY NHẤT cho nick đó suốt mọi bước (lấy token -> reauth -> up 2FA).
    """
    if seed:
        seed_int = int(hashlib.md5(str(seed).encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed_int)
    else:
        rng = random.Random()

    mfg, brand, model_name, dev_code, density, w, h, amin, amax = rng.choice(KATANA_DEVICE_POOL)
    android_ver = rng.randint(amin, amax)
    fbav, fbbv = rng.choice(KATANA_FBAV_VERSIONS)
    carrier = rng.choice(KATANA_CARRIERS)
    locale = rng.choice(KATANA_LOCALES)

    ua = (
        f"[FBAN/FB4A;FBAV/{fbav};FBBV/{fbbv};FBDM/{{density={density},width={w},height={h}}};"
        f"FBLC/{locale};FBRV/0;FBCR/{carrier};FBMF/{mfg.lower()};FBBD/{brand};FBPN/com.facebook.katana;"
        f"FBDV/{dev_code};FBSV/{android_ver};FBOP/1;FBCA/x86_64:arm64-v8a;]"
    )
    return ua


def get_account_token_eaaau(session, uid: str, password: str, proxy: Optional[str] = None, katana_ua: Optional[str] = None) -> Optional[str]:
    """
    Tự động lấy Token EAAAAU cho tài khoản Facebook mới reg:
    1. Ưu tiên lấy trực tiếp qua Cookie/Session (m.facebook.com composer async loader)
    2. Fallback đăng nhập qua Katana FB4A Bloks CAA (FacebookLogin) dùng đúng katana_ua
    3. Fallback qua auth.login Katana API dùng đúng katana_ua
    """
    if not katana_ua:
        katana_ua = generate_random_katana_ua(seed=uid)

    px_dict = None
    if proxy:
        if isinstance(proxy, dict):
            px_dict = proxy
        else:
            p_str = str(proxy).strip()
            if p_str.startswith(('http://', 'https://', 'socks5://')):
                px_dict = {'http': p_str, 'https': p_str}
            else:
                parts = p_str.split(':')
                if len(parts) == 4:
                    px_dict = {'http': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}', 'https': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'}
                elif len(parts) == 2:
                    px_dict = {'http': f'http://{parts[0]}:{parts[1]}', 'https': f'http://{parts[0]}:{parts[1]}'}
                else:
                    px_dict = {'http': f'http://{p_str}', 'https': f'http://{p_str}'}
    elif session and hasattr(session, 'proxies') and session.proxies:
        px_dict = session.proxies

    # --- CÁCH 1: Lấy Token EAAAAU trực tiếp từ Cookie Session hiện tại ---
    try:
        if session and hasattr(session, 'cookies') and session.cookies.get('c_user'):
            url_composer = "https://m.facebook.com/composer/ocelot/async_loader/?publisher=feed"
            headers_c = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                'accept': '*/*',
                'referer': 'https://m.facebook.com/'
            }
            r_c = session.get(url_composer, headers=headers_c, proxies=px_dict, timeout=15)
            match_tok = re.search(r'accessToken["\']?\s*:\s*["\'](EAAAAU[a-zA-Z0-9_-]+)', r_c.text)
            if match_tok:
                token = match_tok.group(1)
                print(f"[+] Lấy Token EAAAAU từ Cookie Session thành công: {token[:25]}... (Độ dài: {len(token)})")
                return token
    except Exception:
        pass

    # --- CÁCH 2: Đăng nhập Katana FB4A (FacebookLogin) bằng đúng katana_ua ---
    try:
        proxy_arg = None
        if px_dict:
            proxy_arg = px_dict.get('https') or px_dict.get('http')
        fb_login = FacebookLogin(uid_phone_mail=str(uid), password=password, proxy=proxy_arg, custom_ua=katana_ua)
        res_login = fb_login.login()
        if res_login.get('success') and res_login.get('access_token'):
            token = res_login['access_token']
            print(f"[+] Đăng nhập Katana FB4A lấy Token thành công: {token[:25]}... (Độ dài: {len(token)})")
            return token
    except Exception:
        pass

    # --- CÁCH 3: Gọi auth.login Katana API bằng đúng katana_ua ---
    try:
        url_auth = "https://b-api.facebook.com/method/auth.login"
        headers_auth = {
            "User-Agent": katana_ua,
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-FB-Connection-Type": "WIFI",
        }
        data_auth = {
            "email": str(uid),
            "password": password,
            "format": "json",
            "generate_session_cookies": "1",
            "generate_machine_id": "1",
            "locale": "vi_VN",
            "client_country_code": "VN",
            "method": "auth.login",
            "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32"
        }
        r_auth = requests.post(url_auth, headers=headers_auth, data=data_auth, proxies=px_dict, timeout=15)
        res_auth_json = r_auth.json()
        if "access_token" in res_auth_json:
            token = res_auth_json["access_token"]
            print(f"[+] Lấy Token EAAAAU qua auth.login thành công: {token[:25]}...")
            return token
    except Exception:
        pass

    return None


def generate_totp_code_6(secret: str) -> str:
    cleaned = re.sub(r'[\s\-]+', '', secret).upper()
    missing_padding = len(cleaned) % 8
    if missing_padding != 0:
        cleaned += '=' * (8 - missing_padding)
    key = base64.b32decode(cleaned, casefold=True)
    t = int(time.time() // 30)
    msg = struct.pack(">Q", t)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    code = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return f"{code:06d}"

def enable_2fa_katana_graphql(token: str, uid: str, password: str, proxy: Optional[str] = None, katana_ua: Optional[str] = None) -> Optional[str]:
    """
    Kích hoạt 2FA TOTP cho tài khoản Facebook bằng GraphQL Katana FB4A Bloks (Chuẩn 100% 7 bước từ HAR mới):
    Thứ tự chuẩn xác tuyệt đối:
      1. Entry [72]: two_factor.select_method (Doc ID: 10537346116771029123037277298)
      2. Entry [76]: secured_action.reauth_async (Doc ID: 11994080426203054249997361787)
      3. Entry [77]: two_factor.select_method DEFAULT (Doc ID: 10537346116771029123037277298)
      4. Entry [83]: meta_security_checkup.write_status (Doc ID: 11994080426203054249997361787)
      5. Entry [84]: navigation.log (Doc ID: 11994080426203054249997361787)
      6. Entry [85]: two_factor.totp.generate_key (Doc ID: 11994080426203054249997361787)
      7. Entry [91]: two_factor.totp.enable (Doc ID: 11994080426203054249997361787)
    """
    if not katana_ua:
        katana_ua = '[FBAN/FB4A;FBAV/510.0.0.72.41;FBBV/725719471;FBDM/{density=2.0,width=900,height=1600};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/samsung;FBBD/samsung;FBPN/com.facebook.katana;FBDV/SM-A805N;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]'

    px_dict = None
    if proxy:
        if isinstance(proxy, dict):
            px_dict = proxy
        else:
            p_str = str(proxy).strip()
            if p_str.startswith(('http://', 'https://', 'socks5://')):
                px_dict = {'http': p_str, 'https': p_str}
            else:
                parts = p_str.split(':')
                if len(parts) == 4:
                    px_dict = {'http': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}', 'https': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'}
                elif len(parts) == 2:
                    px_dict = {'http': f'http://{parts[0]}:{parts[1]}', 'https': f'http://{parts[0]}:{parts[1]}'}
                else:
                    px_dict = {'http': f'http://{p_str}', 'https': f'http://{p_str}'}

    s = requests.Session()
    s.verify = False
    s.trust_env = False
    if px_dict:
        s.proxies.update(px_dict)

    device_id = str(uuid.uuid4())
    family_device_id = device_id
    machine_id = "AS_" + base64.b64encode(os.urandom(16)).decode('ascii').rstrip('=').replace('/', '_').replace('+', '-')
    session_id = str(uuid.uuid4())
    account_id_int = int(uid) if str(uid).isdigit() else uid
    gql_url = "https://graph.facebook.com/graphql"
    bloks_versioning_id = "c11a8c0d160df62b2395f6153824f0bc6c6e316a74ab1aff67da02cdd7cc890b"

    headers_base = {
        'authorization': f'OAuth {token}',
        'x-fb-sim-hni': '45201',
        'x-fb-net-hni': '45201',
        'content-type': 'application/x-www-form-urlencoded',
        'x-graphql-client-library': 'graphservice',
        'x-tigon-is-retry': 'False',
        'x-graphql-request-purpose': 'fetch',
        'x-fb-device-group': '8013',
        'user-agent': katana_ua,
        'app-scope-id-header': device_id,
        'x-fb-connection-type': 'WIFI',
        'x-fb-http-engine': 'Tigon/Liger',
        'x-fb-client-ip': 'True',
        'x-fb-server-cluster': 'True',
        'priority': 'u=0'
    }

    nt_context = {
        "using_white_navbar": True,
        "styles_id": "c433035a5d4cdfd79b9c77d0bcd9006b",
        "pixel_ratio": 2,
        "is_push_on": True,
        "debug_tooling_metadata_token": None,
        "is_flipper_enabled": False,
        "theme_params": [],
        "bloks_version": bloks_versioning_id
    }

    def post_step(friendly_name: str, client_doc_id: str, variables: dict, tags: str = '["GraphServices"]') -> requests.Response:
        h = headers_base.copy()
        h['x-fb-friendly-name'] = friendly_name
        data = {
            'method': 'post',
            'pretty': 'false',
            'format': 'json',
            'server_timestamps': 'true',
            'locale': 'vi_VN',
            'purpose': 'fetch',
            'fb_api_req_friendly_name': friendly_name,
            'fb_api_caller_class': 'graphservice',
            'client_doc_id': client_doc_id,
            'fb_api_client_context': '{"is_background":false}',
            'variables': json.dumps(variables),
            'fb_api_analytics_tags': tags,
            'client_trace_id': str(uuid.uuid4())
        }
        return s.post(gql_url, headers=h, data=data, timeout=25)

    print("    [2FA Katana] Bước 1/6: Khởi tạo phiên Two-Factor (Select Method)...")
    v72 = {
        "params": {
            "params": f"{{params:{{\"client_input_params\":{{\"machine_id\":\"{machine_id}\"}},\"server_params\":{{\"should_show_done_button\":0,\"account_type\":0,\"account_id\":{account_id_int},\"INTERNAL_INFRA_screen_id\":\"0\"}}}}}}",
            "bloks_versioning_id": bloks_versioning_id,
            "app_id": "com.bloks.www.fx.settings.security.two_factor.select_method"
        },
        "scale": "2",
        "nt_context": nt_context
    }
    r72 = post_step("FbBloksAppRootQuery-com.bloks.www.fx.settings.security.two_factor.select_method", "10537346116771029123037277298", v72, tags='["surfaces.fb.GraphServiceEmitter","GraphServices"]')
    r72_text = r72.text

    req_data_str = json.dumps({
        "account_id": account_id_int,
        "account_type": 0,
        "on_completion_landing_app_id": None,
        "machine_id": machine_id,
        "should_dismiss_on_completion": False,
        "use_case": "DEFAULT"
    })
    mid_match = re.search(r'\"machine_id\"[\\\":\s]+(AS_[a-zA-Z0-9_\-]+)', r72_text)
    if mid_match:
        machine_id = mid_match.group(1)

    print("    [2FA Katana] Bước 2/6: Xác thực mật khẩu bảo mật (Secured Action Re-auth)...")
    enc_pwd, pw_ts = FacebookPasswordEncryptor.encrypt(password, proxy=proxy)
    reauth_inner = {
        "client_input_params": {"password": enc_pwd, "machine_id": machine_id},
        "server_params": {
            "account_type": 0,
            "controller": "BloksFXSettingsTwoFactorSelectMethodController",
            "INTERNAL__latency_qpl_marker_id": 36707139,
            "account_id": str(uid),
            "category_name": "SecuredActionInteractWithTwoFactorCategory",
            "requested_screen_component_type": None,
            "machine_id": machine_id,
            "INTERNAL__latency_qpl_instance_id": int(time.time() * 1000),
            "node_identifier": "two_factor",
            "request_data": req_data_str,
            "on_success_override": 0
        }
    }
    v76 = {
        "params": {
            "params": json.dumps({"params": json.dumps(reauth_inner)}),
            "bloks_versioning_id": bloks_versioning_id,
            "app_id": "com.bloks.www.fx.settings.security.secured_action.reauth_async"
        },
        "scale": "2",
        "nt_context": nt_context
    }
    r76 = post_step("FbBloksActionRootQuery-com.bloks.www.fx.settings.security.secured_action.reauth_async", "11994080426203054249997361787", v76)
    if '"initial":false' in r76.text and 'BLOKS_SECURED_ACTION_REAUTH_PASSWORD_ENTRY:success' in r76.text:
        print("    [-] Mật khẩu không chính xác hoặc Re-auth bị từ chối.")
        return None

    print("    [2FA Katana] Bước 3/6: Cập nhật điều hướng chọn phương thức (Select Method DEFAULT)...")
    v77 = {
        "params": {
            "params": f"{{params:{{\"server_params\":{{\"use_case\":\"DEFAULT\",\"account_type\":0,\"machine_id\":\"{machine_id}\",\"account_id\":{account_id_int},\"should_dismiss_on_completion\":0,\"INTERNAL_INFRA_screen_id\":\"0\"}}}}}}",
            "bloks_versioning_id": bloks_versioning_id,
            "app_id": "com.bloks.www.fx.settings.security.two_factor.select_method"
        },
        "scale": "2",
        "nt_context": nt_context
    }
    r77 = post_step("FbBloksAppRootQuery-com.bloks.www.fx.settings.security.two_factor.select_method", "10537346116771029123037277298", v77, tags='["surfaces.fb.GraphServiceEmitter","GraphServices"]')

    print("    [2FA Katana] Bước 4/6: Đồng bộ trạng thái bảo mật (Security Status Write)...")
    v83 = {
        "params": {
            "params": json.dumps({"params": json.dumps({
                "client_input_params": {},
                "server_params": {
                    "requested_screen_component_type": None,
                    "two_factor_last_review_time": int(pw_ts) if pw_ts else int(time.time()),
                    "machine_id": machine_id,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": int(time.time() * 1000)
                }
            })}),
            "bloks_versioning_id": bloks_versioning_id,
            "app_id": "com.bloks.www.fx.settings.meta_security_checkup.write_status"
        },
        "scale": "2",
        "nt_context": nt_context
    }
    r83 = post_step("FbBloksActionRootQuery-com.bloks.www.fx.settings.meta_security_checkup.write_status", "11994080426203054249997361787", v83)

    print("    [2FA Katana] Bước 5/6: Ghi nhận sự kiện xem 2FA (Navigation Log)...")
    v84 = {
        "params": {
            "params": json.dumps({"params": json.dumps({
                "client_input_params": {"session_id": session_id},
                "server_params": {
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": int(time.time() * 1000),
                    "event": "setting_account_view",
                    "node_id": "two_factor"
                }
            })}),
            "bloks_versioning_id": bloks_versioning_id,
            "app_id": "com.bloks.www.fx.settings.navigation.log"
        },
        "scale": "2",
        "nt_context": nt_context
    }
    r84 = post_step("FbBloksActionRootQuery-com.bloks.www.fx.settings.navigation.log", "11994080426203054249997361787", v84)

    print("    [2FA Katana] Bước 6/6: Đang gọi API tạo khóa bí mật (Generate Key)...")
    v85 = {
        "params": {
            "params": json.dumps({"params": json.dumps({
                "client_input_params": {
                    "device_id": device_id,
                    "machine_id": machine_id,
                    "family_device_id": family_device_id
                },
                "server_params": {
                    "requested_screen_component_type": None,
                    "account_type": 0,
                    "machine_id": machine_id,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": int(time.time() * 1000),
                    "account_id": account_id_int
                }
            })}),
            "bloks_versioning_id": bloks_versioning_id,
            "app_id": "com.bloks.www.fx.settings.security.two_factor.totp.generate_key"
        },
        "scale": "2",
        "nt_context": nt_context
    }
    r85 = post_step("FbBloksActionRootQuery-com.bloks.www.fx.settings.security.two_factor.totp.generate_key", "11994080426203054249997361787", v85)
    r85_text = r85.text

    totp_secret = None
    k_matches = re.findall(r'([A-Z2-7]{4}(?:\s+[A-Z2-7]{4}){7})', r85_text)
    if k_matches:
        totp_secret = re.sub(r'\s+', '', k_matches[0]).upper()
    else:
        k_32 = re.findall(r'\"([A-Z2-7]{32})\"', r85_text)
        if k_32:
            totp_secret = k_32[0].upper()

    if not totp_secret:
        v86 = {
            "params": {
                "params": f"{{params:{{\"client_input_params\":{{\"machine_id\":\"{machine_id}\"}},\"server_params\":{{\"machine_id\":\"{machine_id}\",\"account_id\":{account_id_int}}}}}}}",
                "bloks_versioning_id": bloks_versioning_id,
                "app_id": "com.bloks.www.fx.settings.security.two_factor.totp.key"
            },
            "scale": "2",
            "nt_context": nt_context
        }
        r86 = post_step("FbBloksAppRootQuery-com.bloks.www.fx.settings.security.two_factor.totp.key", "10537346116771029123037277298", v86, tags='["surfaces.fb.GraphServiceEmitter","GraphServices"]')
        k86_matches = re.findall(r'([A-Z2-7]{4}(?:\s+[A-Z2-7]{4}){7})', r86.text)
        if k86_matches:
            totp_secret = re.sub(r'\s+', '', k86_matches[0]).upper()
        else:
            k86_32 = re.findall(r'\"([A-Z2-7]{32})\"', r86.text)
            if k86_32:
                totp_secret = k86_32[0].upper()

    if not totp_secret:
        print(f"    [-] Không tìm thấy Secret Key trong phản hồi: {r85_text[:200]}")
        return None

    print(f"    [+] Đã lấy được Secret Key 2FA: {totp_secret}")

    totp_code = generate_totp_code_6(totp_secret)
    print(f"    [2FA Katana] Bước 7/7: Gửi mã TOTP ({totp_code}) xác nhận kích hoạt...")
    enable_inner = {
        "client_input_params": {
            "machine_id": machine_id,
            "ap_entrypoint": None,
            "family_device_id": family_device_id,
            "device_id": device_id,
            "verification_code": str(totp_code)
        },
        "server_params": {
            "account_type": 0,
            "INTERNAL__latency_qpl_marker_id": 36707139,
            "INTERNAL__latency_qpl_instance_id": int(time.time() * 1000),
            "account_id": account_id_int
        }
    }
    v91 = {
        "params": {
            "params": json.dumps({"params": json.dumps(enable_inner)}),
            "bloks_versioning_id": bloks_versioning_id,
            "app_id": "com.bloks.www.fx.settings.security.two_factor.totp.enable"
        },
        "scale": "2",
        "nt_context": nt_context
    }
    r91 = post_step("FbBloksActionRootQuery-com.bloks.www.fx.settings.security.two_factor.totp.enable", "11994080426203054249997361787", v91)
    if '"fb_bloks_action":null' in r91.text or ('"code_input_error"' in r91.text and '"initial":"error"' in r91.text):
        print(f"    [-] Lỗi khi kích hoạt 2FA: {r91.text[:160]}")
        return None

    print("    🎉 BẬT 2FA THÀNH CÔNG (CHUẨN 100% KATANA GRAPHQL BLOKS)!")
    return totp_secret


def auto_enable_2fa(session, browser_profile, uid, password, proxy: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Hàm giao tiếp chính được gọi sau khi tạo acc xong:
    1. Sinh ngẫu nhiên 1 User-Agent Katana Android thực tế (chuẩn thiết bị thật)
    2. Dùng chính xác UA này để lấy Token EAAAAU
    3. Dùng tiếp ĐÚNG UA này để kích hoạt 2FA (chuẩn HAR mới)
    4. Trả về (Secret Key, Token EAAAAU) để xuất theo định dạng UID|PASS|2FA|COOKIE|TOKEN
    """
    katana_ua = generate_random_katana_ua(seed=uid)
    print(f"\n[+] TIẾN TRÌNH UP 2FA TỰ ĐỘNG CHO UID: {uid}")
    print(f"    - User-Agent Katana cố định cho nick: {katana_ua[:85]}...")
    
    if not proxy and session and hasattr(session, 'proxies') and session.proxies:
        proxy = session.proxies.get('https') or session.proxies.get('http')

    token = get_account_token_eaaau(session=session, uid=uid, password=password, proxy=proxy, katana_ua=katana_ua)
    if not token:
        print(f"    [-] Không thể lấy Token EAAAAU cho UID {uid} -> Bỏ qua khâu 2FA để bảo toàn tài khoản.")
        return None, None

    totp_secret = enable_2fa_katana_graphql(token=token, uid=uid, password=password, proxy=proxy, katana_ua=katana_ua)
    return totp_secret, token


# ==============================================================================
# PASSWORD GENERATOR (dạng Abc123#)
# ==============================================================================
def generate_strong_password() -> str:
    specials = "#@!$%&*"

    upper   = random.choice(string.ascii_uppercase)
    lower   = ''.join(random.choices(string.ascii_lowercase, k=random.randint(2, 3)))
    digits  = ''.join(random.choices(string.digits,          k=random.randint(2, 3)))
    special = random.choice(specials)

    return f"{upper}{lower}{digits}{special}"


# ==============================================================================
# FACEBOOK GRAPHQL DOC IDs — REG MỒI
# ==============================================================================
DOC_CHECK_VALID = "26387190147557007"
FRIENDLY_CHECK_VALID = "useCAARegistrationFieldValidationQuery"

DOC_REGISTER = "27029416779977343"
FRIENDLY_REGISTER = "useCAARegistrationFormSubmitMutation"

DOC_OPTIONS_DIALOG = "10033443530048902"
FRIENDLY_OPTIONS_DIALOG = "CAAConfirmationOptionsDialogQuery"

DOC_UPDATE_CP_DIALOG = "26687407570897492"
FRIENDLY_UPDATE_CP_DIALOG = "CAAFBConfirmationUpdateCPDialogQuery"

DOC_ADD_CONTACT = "25556223974027527"
FRIENDLY_ADD_CONTACT = "useCAAFBConfirmationAddContactPointMutation"

DOC_RESEND = "9554972464608847"
FRIENDLY_RESEND = "useCAAConfirmationResendConfCodeMutation"

DOC_VERIFY = "24050931851170558"
FRIENDLY_VERIFY = "useCAAFBConfirmationFormSubmitMutation"

# ==============================================================================
# NETNIT API — CHECK GMAIL LIVE/DEAD
# ==============================================================================
NETNIT_API_KEY = "netnit_UOTEmvc1dSKLTQnk0rPe8rIOZWwPi0EV"

def check_gmail_live_netnit(email_addr: str, api_key: str = NETNIT_API_KEY) -> Tuple[bool, str]:
    if not api_key:
        return True, "skipped"
    url = "https://apikey.netnit.net/fastcheck"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    try:
        r = direct_http_session.post(url, json={"mail": [email_addr]}, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                status = results[0].get("status", "").lower()
                if status == "good":
                    return True, "good"
                elif status == "bad":
                    return False, "bad (Inactive / Die)"
                elif status == "failed":
                    return True, "failed (Netnit timeout)"
            return True, "unknown"
    except Exception as e:
        return True, f"error ({e})"
    return True, "skipped"


# ==============================================================================
# CORE ENGINE — AdvancedAccountRegEngine
# ==============================================================================
class AdvancedAccountRegEngine:
    REG_PAGE = "https://www.facebook.com/reg/?entry_point=aymh"
    CONFIRM_PAGE = "https://www.facebook.com/confirmemail.php?next=undefined"
    GRAPHQL_URL = "https://www.facebook.com/api/graphql/"

    def __init__(self, session: requests.Session, ua_profile: dict, proxy_str: Optional[str] = None):
        self.session = session
        self.ua = ua_profile.get("ua")
        self.browser_profile = ua_profile
        self.proxy_str = proxy_str
        self._req_counter = 0

        self.lsd = ""
        self.jazoest = "22508"
        self.fb_dtsg = ""
        self.hs = "20720.HYP:comet_plat_default_pkg.2.1...0"
        self.rev = "1048354754"
        self.hsi = ""
        self.s = ""
        self.dyn = ""
        self.csr = ""
        self.hsdp = ""
        self.hblp = ""
        self.sjsp = ""
        self.spin_r = "1048354754"
        self.spin_t = str(int(time.time()))

    def _next_req(self) -> str:
        self._req_counter += 1
        n = self._req_counter
        if n < 10:
            return str(n)
        return chr(ord('a') + (n - 10))

    def _search(self, html: str, pat: str, default: str = "") -> str:
        m = re.search(pat, html)
        return m.group(1) if m else default

    def warmup_and_extract_tokens(self) -> bool:
        AppLogger.step(1, "Khởi tạo kết nối", "Warmup Comet Web & bóc tách Token sạch")
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "upgrade-insecure-requests": "1",
            "user-agent": self.ua,
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1"
        }
        for attempt in range(3):
            try:
                r = self.session.get(self.REG_PAGE, headers=headers, timeout=25)
                html = r.text or ""
                if r.status_code == 200 and len(html) > 5000:
                    self.lsd = (
                        self._search(html, r'name="lsd"\s+value="([^"]+)"') or
                        self._search(html, r'"LSD"\s*,\s*\[\s*\]\s*,\s*\{\s*"token"\s*:\s*"([^"]+)"')
                    )
                    if self.lsd:
                        self.jazoest = f"2{sum(ord(c) for c in self.lsd)}"

                    self.fb_dtsg = (
                        self._search(html, r'name="fb_dtsg"\s+value="([^"]+)"') or
                        self._search(html, r'"DTSGInitialData"\s*,\s*\[\s*\]\s*,\s*\{\s*"token"\s*:\s*"([^"]+)"')
                    )

                    rev = self._search(html, r'"server_revision"\s*:\s*(\d+)')
                    if rev: self.rev = rev

                    self.hsi = self._search(html, r'"hsi"\s*:\s*"(\d+)"', self.hsi)
                    self.spin_r = self._search(html, r'"__spin_r"\s*:\s*(\d+)', self.spin_r)
                    self.spin_t = self._search(html, r'"__spin_t"\s*:\s*(\d+)') or str(int(time.time()))
                    self.hs = self._search(html, r'"haste_session"\s*:\s*"([^"]+)"', self.hs)
                    self.s = self._search(html, r'"__s"\s*:\s*"([^"]+)"', self.s)
                    self.dyn = self._search(html, r'"__dyn"\s*:\s*"([^"]+)"', self.dyn)
                    self.csr = self._search(html, r'"__csr"\s*:\s*"([^"]+)"', self.csr)
                    self.hsdp = self._search(html, r'"__hsdp"\s*:\s*"([^"]+)"', self.hsdp)
                    self.hblp = self._search(html, r'"__hblp"\s*:\s*"([^"]+)"', self.hblp)
                    self.sjsp = self._search(html, r'"__sjsp"\s*:\s*"([^"]+)"', self.sjsp)

                    if self.lsd:
                        AppLogger.token("LSD", self.lsd)
                        AppLogger.token("JAZOEST", self.jazoest)
                        return True
            except Exception as e:
                AppLogger.warn(f"Lỗi cào token lần {attempt+1}: {e}")
            time.sleep(1.5)
        return False

    def _gql_guest_headers(self, friendly: str) -> dict:
        return {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.facebook.com",
            "referer": self.REG_PAGE,
            "x-asbd-id": "359341",
            "x-fb-friendly-name": friendly,
            "x-fb-lsd": self.lsd,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.ua,
            "sec-ch-ua": self.browser_profile.get("sec_ch_ua", '"Google Chrome";v="133"'),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": self.browser_profile.get("platform", '"Windows"'),
            "sec-ch-ua-full-version-list": self.browser_profile.get("sec_ch_ua_full", '"Google Chrome";v="133.0.0.0"'),
            "sec-ch-ua-model": '""',
            "accept-language": "en-US,en;q=0.9"
        }

    def _gql_guest_body(self, variables: dict, friendly: str, doc_id: str, qpl="516759801") -> dict:
        self.spin_t = str(int(time.time()))
        return {
            "av": "0", "__user": "0", "__a": "1", "__req": self._next_req(),
            "__hs": self.hs, "dpr": "1", "__ccg": "EXCELLENT", "__rev": self.rev,
            "__s": self.s, "__hsi": self.hsi, "__dyn": self.dyn, "__csr": self.csr,
            "__hsdp": self.hsdp, "__hblp": self.hblp, "__sjsp": self.sjsp,
            "__comet_req": "102",
            "lsd": self.lsd, "jazoest": self.jazoest,
            "__spin_r": self.spin_r, "__spin_b": "trunk", "__spin_t": self.spin_t,
            "qpl_active_flow_ids": qpl,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": friendly,
            "server_timestamps": "true",
            "variables": json.dumps(variables, separators=(",", ":")),
            "doc_id": doc_id,
            "fb_api_analytics_tags": f'["qpl_active_flow_ids={qpl}"]'
        }

    def _body_user(self, uid: str, variables: dict, friendly: str, doc_id: str, qpl="516759801") -> dict:
        self.spin_t = str(int(time.time()))
        data = {
            "av": str(uid), "__user": str(uid), "__a": "1", "__req": self._next_req(),
            "__hs": self.hs, "dpr": "1", "__ccg": "EXCELLENT", "__rev": self.rev,
            "__s": self.s, "__hsi": self.hsi, "__dyn": self.dyn, "__csr": self.csr,
            "__hsdp": self.hsdp, "__hblp": self.hblp, "__sjsp": self.sjsp,
            "__comet_req": "102",
            "fb_dtsg": self.fb_dtsg, "jazoest": self.jazoest, "lsd": self.lsd,
            "__spin_r": self.spin_r, "__spin_b": "trunk", "__spin_t": self.spin_t,
            "qpl_active_flow_ids": qpl,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": friendly,
            "server_timestamps": "true",
            "variables": json.dumps(variables, separators=(",", ":")),
            "doc_id": doc_id,
            "fb_api_analytics_tags": f'["qpl_active_flow_ids={qpl}"]'
        }
        return data

    def _user_headers(self, friendly: str) -> dict:
        h = self._gql_guest_headers(friendly)
        h["referer"] = self.CONFIRM_PAGE
        return h

    def check_field_validation(self, phone: str, first_name: str, last_name: str) -> bool:
        AppLogger.step(2, "Field Validation", f"Xác minh tính hợp lệ của SĐT mồi: {phone}")
        vars_payload = {
            "input": {
                "contactpoint": {"sensitive_string_value": phone},
                "contactpoint_type": "PHONE",
                "fetch_username_suggestions": True,
                "field_name": "CONTACTPOINT",
                "firstname": {"sensitive_string_value": first_name},
                "fullname": {"sensitive_string_value": ""},
                "lastname": {"sensitive_string_value": last_name},
                "machine_id": ""
            },
            "scale": 1
        }
        try:
            body = self._gql_guest_body(vars_payload, FRIENDLY_CHECK_VALID, DOC_CHECK_VALID)
            r = self.session.post(self.GRAPHQL_URL, data=body, headers=self._gql_guest_headers(FRIENDLY_CHECK_VALID), timeout=15)
            text = r.text[9:] if (r.text or "").startswith("for (;;);") else (r.text or "")
            resp = json.loads(text)
            node = resp.get("data", {}).get("xfb_caa_registration_field_validation", {}) or {}
            if node.get("status") == "SUCCESS":
                AppLogger.check("SĐT mồi hoàn toàn hợp lệ trong hệ thống Facebook CAA!")
                return True
        except Exception as e:
            AppLogger.warn(f"Kiểm tra field validation lỗi nhẹ: {e}")
        return False

    def submit_phone_reg(self, phone: str, password: str, first_name: str, last_name: str, gender: str, dob: Tuple[int, int, int]) -> Tuple[bool, Optional[str]]:
        AppLogger.step(3, "Reg Mồi SĐT US", f"Bắn GraphQL tạo acc bằng số ảo {phone}")
        timestamp_now = int(time.time())
        pwd_payload = f"#PWD_BROWSER:0:{timestamp_now}:{password}"
        variables = {
            "input": {
                "actor_id": "0",
                "client_mutation_id": str(uuid.uuid4()),
                "machine_id": "",
                "next_uri": "undefined",
                "reg_data": {
                    "birthday_day": dob[0],
                    "birthday_month": dob[1],
                    "birthday_year": dob[2],
                    "contactpoint": {"sensitive_string_value": phone},
                    "contactpoint_type": "PHONE",
                    "custom_gender": "",
                    "did_use_age": False,
                    "firstname": {"sensitive_string_value": first_name},
                    "fullname": {"sensitive_string_value": ""},
                    "ig_age_block_data": None,
                    "lastname": {"sensitive_string_value": last_name},
                    "preferred_pronoun": None,
                    "reg_passwd__": {"sensitive_string_value": pwd_payload},
                    "sex": "FEMALE" if gender.upper() == "FEMALE" else "MALE",
                    "use_custom_gender": False,
                    "username": {"sensitive_string_value": ""}
                },
                "sk_pipa_consent_given": None,
                "waterfall_id": str(uuid.uuid4())
            },
            "scale": 1
        }

        try:
            body = self._gql_guest_body(variables, FRIENDLY_REGISTER, DOC_REGISTER, qpl="250359044,516759801")
            r = self.session.post(self.GRAPHQL_URL, data=body, headers=self._gql_guest_headers(FRIENDLY_REGISTER), timeout=20)
            text = r.text[9:] if (r.text or "").startswith("for (;;);") else (r.text or "")
            resp = json.loads(text)
            
            if resp.get("error") == 1357004:
                AppLogger.warn("Facebook báo lỗi phiên (error 1357004). Đang warmup làm mới token LSD...")
                self.warmup_and_extract_tokens()
                self.req_num = 1
                return False, None

            node = resp.get("data", {}).get("caa_registration_homepage_submit", {}) or {}
            status = node.get("status")
            created_uid = node.get("created_user_id")
            if status == "SUCCESS" and created_uid:
                AppLogger.success(f"Reg Mồi Thành Công! Được cấp UID: {created_uid}")
                return True, str(created_uid)
            else:
                err_detail = node.get("error_message") or node.get("validation_errors") or text
                AppLogger.warn(f"Facebook phản hồi status={status}: {err_detail[:400]}")
        except Exception as e:
            AppLogger.error(f"Lỗi submit registration: {e}")
            try:
                self.warmup_and_extract_tokens()
                self.req_num = 1
            except Exception:
                pass
        return False, None

    def submit_email_reg(self, email_addr: str, password: str, first_name: str, last_name: str, gender: str, dob: Tuple[int, int, int]) -> Tuple[bool, Optional[str]]:
        AppLogger.step(3, "Reg Mồi Bằng Email", f"Bắn GraphQL tạo acc bằng email mồi: {email_addr}")
        timestamp_now = int(time.time())
        pwd_payload = f"#PWD_BROWSER:0:{timestamp_now}:{password}"
        variables = {
            "input": {
                "actor_id": "0",
                "client_mutation_id": str(uuid.uuid4()),
                "machine_id": "",
                "next_uri": "undefined",
                "reg_data": {
                    "birthday_day": dob[0],
                    "birthday_month": dob[1],
                    "birthday_year": dob[2],
                    "contactpoint": {"sensitive_string_value": email_addr},
                    "contactpoint_type": "EMAIL",
                    "custom_gender": "",
                    "did_use_age": False,
                    "firstname": {"sensitive_string_value": first_name},
                    "fullname": {"sensitive_string_value": ""},
                    "ig_age_block_data": None,
                    "lastname": {"sensitive_string_value": last_name},
                    "preferred_pronoun": None,
                    "reg_passwd__": {"sensitive_string_value": pwd_payload},
                    "sex": "FEMALE" if gender.upper() == "FEMALE" else "MALE",
                    "use_custom_gender": False,
                    "username": {"sensitive_string_value": ""}
                },
                "sk_pipa_consent_given": None,
                "waterfall_id": str(uuid.uuid4())
            },
            "scale": 1
        }

        try:
            body = self._gql_guest_body(variables, FRIENDLY_REGISTER, DOC_REGISTER, qpl="250359044,516759801")
            r = self.session.post(self.GRAPHQL_URL, data=body, headers=self._gql_guest_headers(FRIENDLY_REGISTER), timeout=20)
            text = r.text[9:] if (r.text or "").startswith("for (;;);") else (r.text or "")
            resp = json.loads(text)

            if resp.get("error") == 1357004:
                AppLogger.warn("Facebook báo lỗi phiên (error 1357004). Đang warmup làm mới token LSD...")
                self.warmup_and_extract_tokens()
                self.req_num = 1
                return False, None

            node = resp.get("data", {}).get("caa_registration_homepage_submit", {}) or {}
            status = node.get("status")
            created_uid = node.get("created_user_id")
            if status == "SUCCESS" and created_uid:
                AppLogger.success(f"Reg Mồi Email Thành Công! Được cấp UID: {created_uid}")
                return True, str(created_uid)
            else:
                err_detail = node.get("error_message") or node.get("validation_errors") or text
                AppLogger.warn(f"Facebook phản hồi status={status}: {err_detail[:400]}")
        except Exception as e:
            AppLogger.error(f"Lỗi submit registration bằng Email: {e}")
            try:
                self.warmup_and_extract_tokens()
                self.req_num = 1
            except Exception:
                pass
        return False, None

    def refresh_fb_dtsg_from_confirm(self) -> bool:
        AppLogger.info("Đang đồng bộ lại fb_dtsg & lsd từ confirmemail.php...")
        headers = {
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        }
        try:
            r = self.session.get(self.CONFIRM_PAGE, headers=headers, timeout=12)
            html = r.text or ""
            AppLogger.info(f"confirm page URL: {r.url} | status={r.status_code} | len={len(html)}")
            
            m_dtsg = (re.search(r'"DTSGInitialData",\[\],{"token":"([^"]+)"}', html) or
                      re.search(r'name="fb_dtsg"\s+value="([^"]+)"', html) or
                      re.search(r'"fbdtsg",\[\],\{"token":"([^"]+)"\}', html))
            if m_dtsg: 
                self.fb_dtsg = m_dtsg.group(1)
            else:
                eqmc_match = re.search(r'id="__eqmc"[^>]*>(\{[^<]+\})</script>', html)
                if eqmc_match:
                    try:
                        eqmc_data = json.loads(eqmc_match.group(1))
                        self.fb_dtsg = eqmc_data.get('f') or ""
                    except Exception:
                        pass

            if self.fb_dtsg:
                AppLogger.info(f"Bóc được fb_dtsg: {self.fb_dtsg[:20]}...")
            else:
                AppLogger.warn("KHÔNG tìm thấy fb_dtsg trong html confirmemail!")

            m_lsd = (re.search(r'"LSD",\[\],{"token":"([^"]+)"}', html) or
                     re.search(r'name="lsd"\s+value="([^"]+)"', html))
            if m_lsd:
                self.lsd = m_lsd.group(1)
                AppLogger.info(f"Bóc được lsd: {self.lsd[:15]}...")

            if self.fb_dtsg:
                self.jazoest = f"2{sum(ord(c) for c in self.fb_dtsg)}"
            elif self.lsd:
                self.jazoest = f"2{sum(ord(c) for c in self.lsd)}"
            return bool(self.fb_dtsg and self.lsd)
        except Exception as e:
            AppLogger.warn(f"Lỗi refresh confirm: {e}")
            return False

    def open_options_dialog(self, uid: str) -> bool:
        AppLogger.dialog("Mở hộp thoại tùy chọn (CAAConfirmationOptionsDialogQuery)...")
        try:
            body = self._body_user(uid, {"args": {}}, FRIENDLY_OPTIONS_DIALOG, DOC_OPTIONS_DIALOG)
            r = self.session.post(self.GRAPHQL_URL, data=body, headers=self._user_headers(FRIENDLY_OPTIONS_DIALOG), timeout=15)
            AppLogger.info(f"options_dialog HTTP {r.status_code}: {r.text[:120]}")
            return r.status_code == 200
        except Exception as e:
            AppLogger.warn(f"options_dialog error: {e}")
            return False

    def open_update_cp_dialog(self, uid: str) -> bool:
        AppLogger.dialog("Mở hộp thoại đổi thông tin liên hệ (CAAFBConfirmationUpdateCPDialogQuery)...")
        try:
            body = self._body_user(uid, {"args": {}}, FRIENDLY_UPDATE_CP_DIALOG, DOC_UPDATE_CP_DIALOG)
            r = self.session.post(self.GRAPHQL_URL, data=body, headers=self._user_headers(FRIENDLY_UPDATE_CP_DIALOG), timeout=15)
            AppLogger.info(f"update_cp_dialog HTTP {r.status_code}: {r.text[:120]}")
            return r.status_code == 200
        except Exception as e:
            AppLogger.warn(f"update_cp_dialog error: {e}")
            return False

    def add_contact_point(self, uid: str, new_contact: str) -> bool:
        if not self.fb_dtsg or not self.lsd:
            self.refresh_fb_dtsg_from_confirm()

        self.open_options_dialog(uid)
        time.sleep(random.uniform(1.2, 2.0))
        self.open_update_cp_dialog(uid)
        time.sleep(random.uniform(1.5, 2.5))

        AppLogger.step(4, "Gắn Email Vào Acc", f"Gán địa chỉ [{new_contact}] vào Facebook")
        variables = {
            "input": {
                "actor_id": str(uid),
                "client_mutation_id": str(uuid.uuid4()),
                "contact_point": new_contact,
                "machine_id": ""
            },
            "scale": 1
        }

        try:
            body = self._body_user(uid, variables, FRIENDLY_ADD_CONTACT, DOC_ADD_CONTACT)
            r = self.session.post(self.GRAPHQL_URL, data=body, headers=self._user_headers(FRIENDLY_ADD_CONTACT), timeout=15)
            text = r.text[9:] if (r.text or "").startswith("for (;;);") else (r.text or "")
            try:
                resp = json.loads(text)
            except Exception:
                resp = {}
            node = (resp.get("data") or {}).get("xfb_caa_registration_add_contactpoint") or {}
            cp = node.get("contact_point")
            if cp:
                AppLogger.success(f"Gán Email Thành Công: {cp}")
                return True
            
            if "1357004" in text or "error" in text or "errors" in resp:
                AppLogger.warn("Lỗi token/session từ Facebook (1357004), đang làm mới fb_dtsg & jazoest từ confirmemail.php...")
                time.sleep(2.0)
                self.refresh_fb_dtsg_from_confirm()
                
                r2 = self.session.post(self.GRAPHQL_URL, data=self._body_user(uid, variables, FRIENDLY_ADD_CONTACT, DOC_ADD_CONTACT), headers=self._user_headers(FRIENDLY_ADD_CONTACT), timeout=15)
                text2 = r2.text[9:] if (r2.text or "").startswith("for (;;);") else (r2.text or "")
                try:
                    resp2 = json.loads(text2)
                except Exception:
                    resp2 = {}
                node2 = (resp2.get("data") or {}).get("xfb_caa_registration_add_contactpoint") or {}
                cp2 = node2.get("contact_point")
                if cp2:
                    AppLogger.success(f"Gán Email Thành Công (sau khi làm mới): {cp2}")
                    return True
                text = text2

            AppLogger.warn(f"Phản hồi thêm contact point: {text[:160]}")
        except Exception as e:
            AppLogger.error(f"Lỗi add_contact_point: {e}")
        return False

    def verify_otp(self, uid: str, otp_code: str) -> bool:
        AppLogger.step(5, "Xác Thực OTP", f"Submit mã xác minh [{otp_code}] lên Facebook")
        if not self.fb_dtsg or not self.lsd:
            self.refresh_fb_dtsg_from_confirm()

        variables = {
            "input": {
                "actor_id": str(uid),
                "client_mutation_id": str(uuid.uuid4()),
                "conf_code": {"sensitive_string_value": str(otp_code).strip()},
                "ig_reg_data": None,
                "machine_id": None
            }
        }
        try:
            body = self._body_user(uid, variables, FRIENDLY_VERIFY, DOC_VERIFY, qpl="250360002,516759801")
            r = self.session.post(self.GRAPHQL_URL, data=body, headers=self._user_headers(FRIENDLY_VERIFY), timeout=15)
            text = r.text[9:] if (r.text or "").startswith("for (;;);") else (r.text or "")
            if self.session.cookies.get("c_user"):
                AppLogger.success("XÁC MINH OTP THÀNH CÔNG! Đã nhận diện Cookie c_user.")
                return True
            if '"status":"SUCCESS"' in text or '"is_confirmed":true' in text:
                AppLogger.success("GraphQL xác nhận OTP hợp lệ!")
                self.session.get("https://www.facebook.com/confirmemail.php?next=https%3A%2F%2Fwww.facebook.com%2F", timeout=10)
                return True
            AppLogger.warn(f"Phản hồi verify OTP: {text[:160]}")
        except Exception as e:
            AppLogger.error(f"Lỗi khi verify OTP: {e}")
        return False

    def resend_otp(self, uid: str) -> bool:
        AppLogger.mail("[RESEND] Đang gửi yêu cầu gửi lại mã xác nhận (useCAAConfirmationResendConfCodeMutation)...")
        if not self.fb_dtsg or not self.lsd:
            self.refresh_fb_dtsg_from_confirm()
            time.sleep(random.uniform(0.5, 1.0))

        try:
            self.open_options_dialog(uid)
            time.sleep(random.uniform(1.0, 1.8))

            variables = {
                "input": {
                    "actor_id": str(uid),
                    "client_mutation_id": str(uuid.uuid4()),
                    "machine_id": ""
                }
            }
            body = self._body_user(uid, variables, FRIENDLY_RESEND, DOC_RESEND, qpl="516759801")
            r = self.session.post(self.GRAPHQL_URL, data=body, headers=self._user_headers(FRIENDLY_RESEND), timeout=15)
            text = r.text[9:] if (r.text or "").startswith("for (;;);") else (r.text or "")
            try:
                resp = json.loads(text)
            except Exception:
                resp = {}

            ok = (resp.get("data") or {}).get("caa_registration_resend_conf_code", {}).get("success") is True
            if ok:
                AppLogger.success("[RESEND] Đã gửi lại mã OTP Facebook thành công!")
                return True
            
            if "error" in text or "errors" in resp:
                AppLogger.warn("[RESEND] Gặp lỗi session/token. Đang làm mới và thử lại...")
                self.refresh_fb_dtsg_from_confirm()
                time.sleep(1.0)
                body2 = self._body_user(uid, variables, FRIENDLY_RESEND, DOC_RESEND, qpl="516759801")
                r2 = self.session.post(self.GRAPHQL_URL, data=body2, headers=self._user_headers(FRIENDLY_RESEND), timeout=15)
                text2 = r2.text[9:] if (r2.text or "").startswith("for (;;);") else (r2.text or "")
                try:
                    resp2 = json.loads(text2)
                except Exception:
                    resp2 = {}
                ok2 = (resp2.get("data") or {}).get("caa_registration_resend_conf_code", {}).get("success") is True
                if ok2:
                    AppLogger.success("[RESEND] Đã gửi lại mã OTP Facebook thành công (sau khi làm mới)!")
                    return True

            AppLogger.warn(f"[RESEND] Facebook phản hồi: {text[:160]}")
        except Exception as e:
            AppLogger.error(f"[RESEND] Lỗi gửi lại mã OTP: {e}")
        return False
# ══════════════════════════════════════════════════════════════════════════
#                    HẾT PHẦN 2/3
# ══════════════════════════════════════════════════════════════════════════
# ==============================================================================
# GMAIL POOL — DIRECT (4G/WiFi)
# ==============================================================================
active_dola_threads: List[threading.Thread] = []


def get_gmail_from_pool_direct() -> Tuple[Optional[str], Optional[str]]:
    with pool_file_lock():
        pool = {}
        if os.path.exists(GMAIL_USAGE_FILE):
            try:
                with open(GMAIL_USAGE_FILE, 'r', encoding='utf-8') as f:
                    pool = json.load(f)
            except Exception:
                pool = {}

        for email_addr, info in list(pool.items()):
            if info.get('used', 0) < MAX_REG_PER_GMAIL and not info.get('in_use', False):
                order_id = info.get('order_id', '')
                try:
                    chk_url = f"https://gmail94.com/api/otp/read?token={GMAIL94_TOKEN}&order_id={order_id}&service=facebook"
                    chk_r = direct_http_session.get(chk_url, timeout=5)
                    chk_res = chk_r.json()
                    if chk_res.get('message') == "This order has been refunded." or chk_r.status_code != 200:
                        AppLogger.warn(f"[4G/Direct] Đơn {order_id} của {email_addr} đã hết hạn/refunded trên Gmail94. Xóa khỏi Pool!")
                        del pool[email_addr]
                        with open(GMAIL_USAGE_FILE, 'w', encoding='utf-8') as f:
                            json.dump(pool, f, indent=2, ensure_ascii=False)
                        continue
                except Exception:
                    pass

                pool[email_addr]['in_use'] = True
                with open(GMAIL_USAGE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(pool, f, indent=2, ensure_ascii=False)

                AppLogger.mail(f"[4G/Direct] Độc quyền nhận Gmail trong Pool: {email_addr} (Đã dùng: {info['used']}/{MAX_REG_PER_GMAIL})")
                return email_addr, order_id

    AppLogger.mail("[4G/Direct] Bắt đầu gọi API thuê Gmail mới từ gmail94.com qua mạng chính...")
    url = f"https://gmail94.com/api/otp/create?token={GMAIL94_TOKEN}&service=facebook"
    attempt = 0
    while True:
        attempt += 1
        try:
            r = direct_http_session.get(url, timeout=12)
            try:
                data = r.json()
            except Exception:
                data = {}
            if data.get('success') and 'data' in data:
                email_addr = data['data']['email']
                order_id = data['data']['order_id']
                AppLogger.success(f"[4G/Direct] Thuê Gmail THÀNH CÔNG: {email_addr} | Order ID: {order_id}")

                if NETNIT_API_KEY:
                    AppLogger.check(f"Đang kiểm tra chất lượng Gmail qua Netnit: {email_addr}...")
                    is_live_mail, mail_status = check_gmail_live_netnit(email_addr, NETNIT_API_KEY)
                    if not is_live_mail:
                        AppLogger.warn(f"❌ Gmail {email_addr} bị Netnit báo DIE/INACTIVE ({mail_status})! Hủy đơn và thuê Gmail khác ngay...")
                        time.sleep(2.0)
                        continue
                    else:
                        AppLogger.success(f"✅ Netnit xác nhận Gmail LIVE ({mail_status})! Tiến hành đưa vào quy trình reg Facebook.")

                with pool_file_lock():
                    pool = {}
                    if os.path.exists(GMAIL_USAGE_FILE):
                        try:
                            with open(GMAIL_USAGE_FILE, 'r', encoding='utf-8') as f:
                                pool = json.load(f)
                        except Exception:
                            pool = {}
                    pool[email_addr] = {
                        'order_id': order_id,
                        'used': 0,
                        'in_use': True,
                        'created_at': time.time()
                    }
                    with open(GMAIL_USAGE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(pool, f, indent=2, ensure_ascii=False)
                return email_addr, order_id
            else:
                msg = data.get('message', 'Không có phản hồi')
                AppLogger.warn(f"[4G/Direct] Gmail94 lần {attempt}: {msg}. Thử lại sau 4s...")
        except Exception as e:
            AppLogger.error(f"[4G/Direct] Lỗi kết nối Gmail94 (Lần {attempt}): {e}. Thử lại sau 4s...")
        time.sleep(4)


def get_gmail94_otp_direct(order_id: str, email_addr: str = "", max_retries: int = 40, delay: float = 2.0, resend_callback: Optional[Callable[[], bool]] = None) -> Optional[str]:
    AppLogger.mail(f"[4G/Direct] Bắt đầu quét mã OTP Gmail94 cho Order ID: {order_id} (Tối đa {max_retries} lần)...")
    url = f"https://gmail94.com/api/otp/read?token={GMAIL94_TOKEN}&order_id={order_id}&service=facebook"

    initial_otps = set()
    try:
        r_init = direct_http_session.get(url, timeout=10)
        d_init = r_init.json()
        if isinstance(d_init, dict):
            if isinstance(d_init.get('otps'), list):
                for x in d_init['otps']:
                    if str(x).strip():
                        initial_otps.add(str(x).strip())
            if d_init.get('otp'):
                initial_otps.add(str(d_init['otp']).strip())
    except Exception:
        pass

    def extract_otp_candidates(obj) -> List[str]:
        found = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                found.extend(extract_otp_candidates(v))
        elif isinstance(obj, list):
            for item in obj:
                found.extend(extract_otp_candidates(item))
        elif isinstance(obj, (str, int)):
            s = str(obj).strip()
            if s.isdigit() and 5 <= len(s) <= 8:
                found.append(s)
            else:
                matches = re.findall(r'\b\d{5,8}\b', s)
                found.extend(matches)
        return found

    for i in range(max_retries):
        time.sleep(delay)
        try:
            r = direct_http_session.get(url, timeout=10)
            res = r.json()
            if not isinstance(res, dict):
                continue

            candidates = extract_otp_candidates(res)
            new_candidates = [c for c in candidates if c not in initial_otps and c != "94025"]

            if new_candidates:
                otp_found = new_candidates[-1]
                AppLogger.success(f"[4G/Direct] Bắt được mã OTP từ Gmail94: {otp_found}")
                return otp_found

            if res.get('success') and res.get('data'):
                c_data = extract_otp_candidates(res['data'])
                new_c_data = [c for c in c_data if c not in initial_otps and c != "94025"]
                if new_c_data:
                    return new_c_data[-1]

        except Exception:
            pass

        if (i + 1) % 10 == 0:
            AppLogger.info(f"[4G/Direct] Vẫn đang chờ Gmail94 nhả mã OTP Facebook... (Lần {i+1}/{max_retries})")
            if (i + 1) < max_retries and resend_callback:
                AppLogger.mail(f"🔔 [Tự Động Gửi Lại Mã] Đã quét {i+1} lần chưa có mã -> Gọi API Facebook gửi lại mã OTP...")
                try:
                    resend_callback()
                except Exception as ex:
                    AppLogger.warn(f"Lỗi khi gọi API gửi lại mã OTP: {ex}")

    AppLogger.error("[4G/Direct] Quá thời gian chờ OTP từ Gmail94.")
    return None


def swap_to_temp_email_dual_network(
    fb_proxied_session: requests.Session,
    browser_profile: dict,
    uid: str,
    password: str,
    current_gmail: str,
    proxy_str: Optional[str] = None
) -> Optional[str]:
    AppLogger.step(6, "Đá Gmail Bằng Email Ảo", f"Bắt đầu quy trình gỡ bỏ {current_gmail} để giải phóng...")
    time.sleep(2.0)

    email_api = FacebookEmailManagerAPI(session=fb_proxied_session, uid=uid, ua=browser_profile.get('ua'), proxy=proxy_str)

    providers = ["tempmail_lol", "emailfake"]
    for provider in providers:
        AppLogger.info(f"[*] Thử dùng nguồn email ảo: {provider.upper()}...")
        for attempt in range(1, 4):
            temp_email = None
            mail_tok = None
            fake_mgr = None

            try:
                if provider == "tempmail_lol":
                    temp_email, mail_tok = TempMailLolManager.create_account(proxy=None)
                    if temp_email:
                        AppLogger.mail(f"[Direct] [TempMail.lol] Đã tạo hòm thư ảo: {temp_email} (Lần {attempt}/3)")
                else:
                    fake_mgr = EmailFakeManagerProxied(proxy=None)
                    res_cr = fake_mgr.create_email()
                    temp_email = res_cr[0] if isinstance(res_cr, tuple) else res_cr
                    if temp_email:
                        AppLogger.mail(f"[Direct] [EmailFake] Đã tạo hòm thư ảo: {temp_email} (Lần {attempt}/3)")
            except Exception as e_cr:
                AppLogger.warn(f"[Direct] Lỗi tạo email ({provider}): {e_cr}")

            if not temp_email:
                time.sleep(1.0)
                continue

            try:
                AppLogger.proxy(f"[Proxy] Gửi yêu cầu thêm Email ảo [{temp_email}] vào Facebook Accounts Center...")
                add_res = email_api.add_email(temp_email, account_password=password)
                if not add_res.get('success'):
                    err_msg = add_res.get('error', 'Thêm email không thành công')
                    AppLogger.warn(f"[Proxy] Facebook từ chối thêm mail {temp_email}: {err_msg}. Đổi email khác...")
                    time.sleep(1.5)
                    continue

                AppLogger.success(f"[Proxy] Đã add Email ảo [{temp_email}] vào Facebook! Đang chờ OTP gửi về...")

                AppLogger.mail(f"[Direct] Chờ mã xác minh gửi về {temp_email} qua mạng máy Direct...")
                otp_code = None
                if provider == "tempmail_lol" and mail_tok:
                    otp_code = TempMailLolManager.get_otp(mail_tok, proxy=None, max_retries=15, delay=3.0)
                elif fake_mgr:
                    otp_code = fake_mgr.get_otp(max_retries=6, delay=4.0)

                if not otp_code:
                    AppLogger.warn(f"[Direct] Quá thời gian chờ OTP từ {temp_email}. Đổi hòm thư ảo khác...")
                    continue

                AppLogger.success(f"[Direct] ĐÃ BẮT ĐƯỢC OTP EMAIL ẢO: {otp_code}")

                AppLogger.proxy(f"[Proxy] Bắn OTP [{otp_code}] xác nhận Email ảo lên Facebook...")
                verify_res = email_api.verify_email_otp(temp_email, otp_code)
                if not verify_res.get('success'):
                    AppLogger.warn(f"[Proxy] Xác thực OTP mail ảo không thành công: {verify_res.get('error')}. Đổi email khác...")
                    continue

                AppLogger.success(f"🎉 Xác thực Email ảo [{temp_email}] THÀNH CÔNG! Chờ 1.5s trước khi đá Gmail...")
                time.sleep(1.5)

                AppLogger.proxy(f"[Proxy] Gửi lệnh xóa/đá Gmail gốc {current_gmail} khỏi Facebook...")
                del_res = email_api.delete_email(current_gmail, account_password=password)
                if not del_res.get('success'):
                    AppLogger.warn(f"[Proxy] Lỗi đá Gmail cũ: {del_res.get('error')}")
                else:
                    AppLogger.success(f"🎉 ĐÃ ĐÁ THÀNH CÔNG GMAIL {current_gmail}! SẴN SÀNG TÁI SỬ DỤNG CHO ACC KHÁC.")
                    return temp_email
            except Exception as e_swap:
                AppLogger.error(f"Lỗi ngoại lệ trong quá trình đá Gmail: {e_swap}")
                time.sleep(1.0)

    return None


# ==============================================================================
# RUN ONE ACCOUNT — ADVANCED (GMAIL MODE, có fix 4G/WiFi)
# ==============================================================================
def run_one_account_advanced(target_email: str, email_token: str, proxy_str: Optional[str] = None, enable_2fa: bool = False, enable_dola: bool = True, root_gmail: Optional[str] = None, swap_email: bool = True) -> bool:
    print("\n" + "="*70)
    print(f"🚀 BẮT ĐẦU CHU TRÌNH TẠO ACC: EMAIL = {target_email}")
    print("="*70)

    session = requests.Session()
    try:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        retries = Retry(total=3, backoff_factor=0.8, status_forcelist=[500, 502, 503, 504], raise_on_status=False)
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    except Exception:
        pass

    formatted_proxy = None
    if proxy_str:
        curr_px = proxy_str.strip()
        if not curr_px.startswith(("http://", "https://", "socks5://")):
            parts = curr_px.split(":")
            if len(parts) == 4:
                formatted_proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            elif len(parts) == 2:
                formatted_proxy = f"http://{parts[0]}:{parts[1]}"
            else:
                formatted_proxy = f"http://{curr_px}"
        else:
            formatted_proxy = curr_px

        if "us.arxlabs.io" in formatted_proxy:
            sess_rand = uuid.uuid4().hex[:10]
            if "sessid-" in formatted_proxy:
                formatted_proxy = re.sub(r'sessid-[a-zA-Z0-9]+', 'sessid-' + sess_rand, formatted_proxy)
            else:
                formatted_proxy = re.sub(r'(rx9l[a-zA-Z0-9\-]+)', r'\1-sessid-' + sess_rand, formatted_proxy, count=1)
        session.proxies.update({"http": formatted_proxy, "https": formatted_proxy})
        AppLogger.proxy(f"Sử dụng Proxy: {formatted_proxy}")
    else:
        session.proxies = {}
        session.trust_env = False
        AppLogger.proxy("Chạy 4G/WiFi THẬT (Direct — không proxy)")

    browser_profile, screen_info = generate_random_browser_profile()
    AppLogger.info(f"Vân tay thiết bị: Chrome v{browser_profile.get('sec_ch_ua').split(';v=')[1].replace(chr(34), '')} | Màn hình: {screen_info['wd']} @ DPR {screen_info['dpr']}")

    geo_info = detect_proxy_geo(session, proxy_str=proxy_str or "")
    country_cc = geo_info.get("countryCode", "TH")
    country_locale = geo_info.get("locale", "th_TH" if country_cc == "TH" else "en_US")
    session.cookies.set('locale', country_locale, domain='.facebook.com')

    session.cookies.set('wd', screen_info['wd'], domain='.facebook.com')
    session.cookies.set('dpr', screen_info['dpr'], domain='.facebook.com')
    session.cookies.set('ps_l', '1', domain='.facebook.com')
    session.cookies.set('ps_n', '1', domain='.facebook.com')
    session.cookies.set('cpo', '1', domain='.facebook.com')

    engine = AdvancedAccountRegEngine(session, browser_profile, proxy_str=proxy_str)

    if not engine.warmup_and_extract_tokens():
        AppLogger.error("Không thể warmup trang chủ Facebook / Proxy bị nghẽn mạng.")
        return False

    fake_phone = generate_phone_by_country(country_cc)
    fake_inter_mail = generate_fake_intermediate_email()
    new_password = generate_strong_password()

    gender = random.choice(["MALE", "FEMALE"])
    if country_cc == "VN":
        first_name = random.choice(MALE_VN) if gender == "MALE" else random.choice(FEMALE_VN)
        last_name = random.choice(SURNAMES_VN)
    elif country_cc == "TH":
        th_male_names = ["Somchai", "Arthit", "Kittisak", "Thanawat", "Chaiwat", "Anan", "Nat", "Tawatchai", "Prasert"]
        th_female_names = ["Sunisa", "Pornthip", "Kanya", "Siriporn", "Apinya", "Natcha", "Supaporn", "Malee"]
        th_last_names = ["Prasert", "Suksom", "Wongsuwan", "Rattana", "Thongdee", "Saetang", "Chaiyaphum", "Boonma"]
        first_name = random.choice(th_male_names) if gender == "MALE" else random.choice(th_female_names)
        last_name = random.choice(th_last_names)
    else:
        first_name = random.choice(MALE_US) if gender == "MALE" else random.choice(FEMALE_US)
        last_name = random.choice(SURNAMES_US)

    dob = (random.randint(1, 28), random.randint(1, 12), random.randint(1990, 2004))

    AppLogger.info(f"Hồ sơ Persona [{country_cc}]: {last_name} {first_name} | {dob[0]}/{dob[1]}/{dob[2]} | {gender}")
    AppLogger.info(f"Mật khẩu ngẫu nhiên: {new_password}")
    AppLogger.info(f"SĐT mồi theo IP ({country_cc}): {fake_phone} | Email trung gian: {fake_inter_mail}")

    engine.check_field_validation(fake_phone, first_name, last_name)
    time.sleep(random.uniform(1.2, 2.5))

    ok_reg, created_uid = False, None
    for attempt in range(1, 3):
        ok_reg, created_uid = engine.submit_phone_reg(fake_phone, new_password, first_name, last_name, gender, dob)
        if ok_reg and created_uid:
            break
        if attempt < 2:
            fake_phone = generate_phone_by_country(country_cc)
            AppLogger.warn(f"Facebook phản hồi lỗi với số cũ, đổi sang SĐT ({country_cc}) mới: {fake_phone} (Lần thử {attempt + 1}/2)...")
            time.sleep(random.uniform(2.0, 3.0))

    if not ok_reg or not created_uid:
        AppLogger.warn("SĐT ảo bị Facebook từ chối trên dải IP Proxy này. KÍCH HOẠT FALLBACK: Reg mồi bằng Email ảo (EmailFake)...")
        temp_bait_mail = None
        try:
            ef_bait = EmailFakeManagerProxied(proxy=None)
            temp_bait_mail, _ = ef_bait.create_email()
        except Exception:
            temp_bait_mail = None

        if not temp_bait_mail:
            temp_bait_mail = f"fb_{uuid.uuid4().hex[:8]}@mail.com"

        ok_reg, created_uid = engine.submit_email_reg(temp_bait_mail, new_password, first_name, last_name, gender, dob)

    used_target_directly = False
    if not ok_reg or not created_uid:
        AppLogger.warn(f"KÍCH HOẠT FALLBACK 2: Tạo acc trực tiếp bằng chính Gmail mục tiêu {target_email}...")
        ok_reg, created_uid = engine.submit_email_reg(target_email, new_password, first_name, last_name, gender, dob)
        if ok_reg and created_uid:
            used_target_directly = True

    if not ok_reg or not created_uid:
        AppLogger.error("Toàn bộ các phương thức tạo UID ban đầu đều thất bại. Bỏ qua lượt này và thử lại.")
        return False

    reg_warm_delay = random.uniform(5.0, 8.0)
    AppLogger.wait(f"Chờ {reg_warm_delay:.1f}s để Facebook thiết lập phiên session sau khi tạo UID...")
    time.sleep(reg_warm_delay)

    if used_target_directly:
        AppLogger.step(4, "Email Chính Thức", f"Đã đăng ký trực tiếp bằng {target_email}. Sẵn sàng nhận OTP.")
    else:
        add_ok = engine.add_contact_point(created_uid, target_email)
        if not add_ok:
            AppLogger.warn("Thêm email chính chưa thành công, chờ 3s thử lại lần 2...")
            time.sleep(3.0)
            add_ok2 = engine.add_contact_point(created_uid, target_email)
            if not add_ok2:
                AppLogger.error(f"❌ Không thể gán Gmail {target_email} vào Facebook! Loại bỏ Gmail này khỏi Pool để mua Gmail mới...")
                if target_email.endswith("@gmail.com"):
                    mark_gmail_failed(target_email)
                return False

    actual_root = root_gmail or target_email
    if actual_root.endswith("@gmail.com") and NETNIT_API_KEY:
        AppLogger.check(f"[Netnit] Kiểm tra trạng thái hòm thư {actual_root} trước khi nhận OTP...")
        is_live_mail, mail_status = check_gmail_live_netnit(actual_root, NETNIT_API_KEY)
        if not is_live_mail:
            AppLogger.error(f"❌ [Netnit] Phát hiện Gmail {actual_root} đã bị DIE ({mail_status})! Hủy nhận mã và loại bỏ Gmail...")
            mark_gmail_failed(actual_root)
            return False
        else:
            AppLogger.success(f"✅ [Netnit] Hòm thư {actual_root} LIVE tốt ({mail_status})! Tiếp tục chờ mã OTP...")

    AppLogger.mail(f"Đang chờ mã OTP gửi về hòm thư {target_email} (chạy qua 4G / mạng chính)...")
    otp_code = None
    resend_fn = (lambda: engine.resend_otp(created_uid)) if created_uid else None
    if email_token.startswith("GMAIL94:"):
        order_id = email_token.split(":", 1)[1]
        otp_code = get_gmail94_otp_direct(order_id, email_addr=target_email, max_retries=40, delay=2.0, resend_callback=resend_fn)
    else:
        otp_code = get_gmail94_otp_direct(email_token, email_addr=target_email, max_retries=40, resend_callback=resend_fn)

    if not otp_code:
        AppLogger.error(f"Hết thời gian chờ OTP từ email {target_email}!")
        if target_email.endswith("@gmail.com"):
            mark_gmail_failed(target_email)
        return False

    AppLogger.success(f"ĐÃ BẮT ĐƯỢC MÃ OTP FACEBOOK: {otp_code}")
    time.sleep(random.uniform(1.0, 2.0))

    if not engine.verify_otp(created_uid, otp_code):
        AppLogger.error("Xác thực mã OTP thất bại hoặc Facebook yêu cầu thêm bước.")
        return False

    if target_email.endswith("@gmail.com"):
        increment_gmail_usage(target_email)

    is_live = check_account_and_bypass_049(session, browser_profile, created_uid)
    if not is_live:
        AppLogger.checkpoint(f"Tài khoản dính Checkpoint 282! Loại bỏ Gmail {target_email}")
        if target_email.endswith("@gmail.com"):
            mark_gmail_failed(target_email)
        return False

    if swap_email and target_email.endswith("@gmail.com"):
        AppLogger.step(6, "Đá Gmail Ban Đầu", f"Gỡ {target_email} để tái sử dụng sang acc tiếp theo")
        new_temp_mail = swap_to_temp_email_dual_network(
            fb_proxied_session=session,
            browser_profile=browser_profile,
            uid=created_uid,
            password=new_password,
            current_gmail=target_email,
            proxy_str=formatted_proxy
        )
        if new_temp_mail:
            AppLogger.success(f"Đã đá Gmail thành công! Tài khoản hiện giữ mail ảo: {new_temp_mail}")
    elif not swap_email:
        AppLogger.step(6, "Bảo Toàn Gmail", f"Chế độ 1 Gmail 1 Acc: Giữ nguyên Gmail chính chủ [{target_email}], không thêm email ảo!")

    cookie_dict = session.cookies.get_dict()
    core_keys = ['c_user', 'xs', 'fr', 'datr', 'sb']
    cookie_parts = [f"{k}={cookie_dict[k]}" for k in core_keys if k in cookie_dict and cookie_dict[k]]
    ignored_keys = {'wd', 'dpr', 'locale', 'ps_l', 'ps_n', 'm_pixel_ratio', 'vpd'}
    for k, v in cookie_dict.items():
        if k not in core_keys and k not in ignored_keys and v:
            cookie_parts.append(f"{k}={v}")
    cookie_str = "; ".join(cookie_parts)

    if not created_uid and cookie_dict.get('c_user'):
        created_uid = cookie_dict['c_user']

    final_account_line = f"{created_uid}|{new_password}|{cookie_str}"
    AppLogger.success(f"TẠO ACC FACEBOOK THÀNH CÔNG:\n{final_account_line}")

    totp_secret = None
    token_eaaau = None
    if enable_2fa:
        AppLogger.step(7, "Bật 2FA Pure API", f"Tiến hành kích hoạt 2FA GraphQL 100% API cho UID {created_uid}...")
        try:
            res_2fa = auto_enable_2fa(session, browser_profile, created_uid, new_password)
            if isinstance(res_2fa, tuple):
                totp_secret, token_eaaau = res_2fa
            else:
                totp_secret, token_eaaau = res_2fa, None

            if totp_secret:
                AppLogger.success(f"🎉 KÍCH HOẠT 2FA THÀNH CÔNG! Secret Key: {totp_secret}")
                line_2fa = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}" if token_eaaau else f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
                safe_append_account_line(ACCOUNTS_2FA_FILE, line_2fa)
                AppLogger.info(f"Đã lưu tài khoản 2FA vào: {ACCOUNTS_2FA_FILE}")
            else:
                AppLogger.warn(f"Không thể kích hoạt 2FA tự động cho UID {created_uid} (sẽ lưu thông tin cơ bản).")
        except Exception as e_2fa:
            AppLogger.error(f"Lỗi ngoại lệ khi bật 2FA: {e_2fa}")

    if totp_secret and token_eaaau:
        account_save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}"
    elif totp_secret:
        account_save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
    elif token_eaaau:
        account_save_line = f"{created_uid}|{new_password}||{cookie_str}|{token_eaaau}"
    else:
        account_save_line = final_account_line
    
    saved_main = safe_append_account_line(ACCOUNTS_FULL_FILE, account_save_line)

    if saved_main:
        AppLogger.success(f"💾 [100% LƯU THÀNH CÔNG] ĐÃ LƯU VÀO: {ACCOUNTS_FULL_FILE}")
    else:
        AppLogger.error(f"❌ CẢNH BÁO: Lỗi lưu tài khoản {created_uid} vào {ACCOUNTS_FULL_FILE}")

    try:
        save_to_excel(created_uid, new_password, totp_secret if totp_secret else "NO_2FA", target_email, cookie_str, token_eaaau or "NO_TOKEN")
    except Exception as e_xl:
        AppLogger.warn(f"Lỗi khi ghi Excel: {e_xl}")
    try:
        send_telegram_live(
            uid=str(created_uid),
            password=new_password,
            cookie=cookie_str,
            email=str(target_email or ""),
            mode="GMAIL",
            totp=totp_secret or "",
            eaau_token=token_eaaau or "",
        )
    except Exception:
        pass

    if HAS_REG_DOLA and enable_dola:
        def background_dola_task(c_str: str, px_str: Optional[str], u_id: str):
            AppLogger.info(f"[Dola-Background] Tài khoản {u_id} sẽ chờ 10 giây ngâm acc rồi mới đăng ký Dola AI...")
            time.sleep(10)
            
            attempt = 0
            current_proxy = px_str
            if current_proxy:
                curr_px_clean = current_proxy.strip()
                if not curr_px_clean.startswith(("http://", "https://", "socks5://")):
                    parts = curr_px_clean.split(":")
                    if len(parts) == 4:
                        current_proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                    elif len(parts) == 2:
                        current_proxy = f"http://{parts[0]}:{parts[1]}"
                    else:
                        current_proxy = f"http://{curr_px_clean}"
            while True:
                attempt += 1
                if current_proxy and "us.arxlabs.io" in current_proxy:
                    sess_rand = uuid.uuid4().hex[:10]
                    if "sessid-" in current_proxy:
                        current_proxy = re.sub(r'sessid-[a-zA-Z0-9]+', 'sessid-' + sess_rand, current_proxy)
                    else:
                        current_proxy = re.sub(r'(rx9l[a-zA-Z0-9\-]+)', r'\1-sessid-' + sess_rand, current_proxy, count=1)

                AppLogger.info(f"[Dola-Background] Đang thực hiện đăng ký Dola AI cho UID {u_id} (Lần thử {attempt})...")
                try:
                    ok_dola, sid, dola_cookies, err_msg = reg_dola.register_dola(c_str, proxy=current_proxy, uid=u_id)
                    if ok_dola and dola_cookies:
                        dola_cookie_str = reg_dola.format_dola_cookie_string(dola_cookies)
                        reg_dola.save_dola_cookies(dola_cookie_str)
                        AppLogger.success(f"🎉 [Dola-Background] ĐĂNG KÝ DOLA AI THÀNH CÔNG cho UID {u_id}! Đã lưu Cookie vào: dola_cookies.txt (Session ID: {str(sid)[:12]}...)")
                        break

                    err_str = str(err_msg or "")
                    is_cookie_dead = (
                        "COOKIE_EXPIRED" in err_str or
                        "ACCOUNT_CONFIRM_EMAIL" in err_str or
                        "confirmemail" in err_str.lower() or
                        "checkpoint" in err_str.lower() or
                        "login.php" in err_str.lower() or
                        "không còn hiệu lực" in err_str.lower()
                    )
                    if is_cookie_dead:
                        AppLogger.error(f"[Dola-Background] ❌ Dừng retry UID {u_id}: Trạng thái không thể OAuth ({err_str})!")
                        break

                    if attempt >= 5:
                        AppLogger.error(f"[Dola-Background] ❌ Dừng retry UID {u_id} sau 5 lần thử: {err_str}!")
                        break

                    AppLogger.warn(f"[Dola-Background] UID {u_id} lần {attempt} chưa hoàn tất: {err_str}. Đổi IP Proxy và thử lại sau 8s...")
                    time.sleep(8)
                except Exception as e_dola:
                    if attempt >= 5:
                        AppLogger.error(f"[Dola-Background] ❌ Dừng retry UID {u_id} do gặp lỗi ngoại lệ liên tục: {e_dola}")
                        break
                    AppLogger.warn(f"[Dola-Background] Lỗi ngoại lệ Dola AI UID {u_id} (Lần {attempt}): {e_dola}. Thử lại sau 8s...")
                    time.sleep(8)

        t_dola = threading.Thread(target=background_dola_task, args=(cookie_str, proxy_str, created_uid), daemon=True)
        active_dola_threads.append(t_dola)
        t_dola.start()
        AppLogger.info(f"🚀 Đã chuyển tác vụ đăng ký Dola AI cho UID {created_uid} vào luồng chạy ngầm độc lập!")

    return True


# ==============================================================================
# RUN ONE ACCOUNT — SMS (fix 4G/WiFi)
# ==============================================================================
def run_one_account_sms(
    proxy_str: Optional[str] = None,
    enable_2fa: bool = False,
    enable_dola: bool = True,
    sms_service_id: int = None,
    sms_api_key: str = None,
    resend_times: int = 4,
) -> bool:
    global active_dola_threads

    sms = CodeTextNowSMS(api_key=sms_api_key or CODETEXTNOW_API_KEY)
    sid = int(sms_service_id or CODETEXTNOW_DEFAULT_SERVICE_ID)

    session = requests.Session()
    session.verify = False
    formatted_proxy = None
    if proxy_str:
        curr_px = proxy_str.strip()
        if not curr_px.startswith(("http://", "https://", "socks5://", "socks5h://")):
            parts = curr_px.split(":")
            if len(parts) == 4:
                formatted_proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            elif len(parts) == 2:
                formatted_proxy = f"http://{parts[0]}:{parts[1]}"
            else:
                formatted_proxy = f"http://{curr_px}"
        else:
            formatted_proxy = curr_px
        if "us.arxlabs.io" in formatted_proxy:
            sess_rand = uuid.uuid4().hex[:10]
            if "sessid-" in formatted_proxy:
                formatted_proxy = re.sub(r'sessid-[a-zA-Z0-9]+', 'sessid-' + sess_rand, formatted_proxy)
            else:
                formatted_proxy = re.sub(r'(rx9l[a-zA-Z0-9\-]+)', r'\1-sessid-' + sess_rand, formatted_proxy, count=1)
        session.proxies.update({"http": formatted_proxy, "https": formatted_proxy})
        AppLogger.proxy(f"Sử dụng Proxy: {formatted_proxy}")
    else:
        session.proxies = {}
        session.trust_env = False
        AppLogger.proxy("Chạy 4G/WiFi THẬT (Direct — không proxy)")

    browser_profile, screen_info = generate_random_browser_profile()
    device_label = (
        f"{browser_profile.get('device_model') or browser_profile.get('platform') or 'Device'} "
        f"Chrome/{browser_profile.get('chrome_v')} {screen_info.get('wd')}@{screen_info.get('dpr')}"
    )
    AppLogger.cookie(f"Live Meta DATR: {(browser_profile.get('device_id') or '')[:24]}...")
    AppLogger.tls("Active Engine: Requests Standard (HTTP/1.1 Fallback)")
    AppLogger.info(f"datr: {(browser_profile.get('device_id') or '')[:28]}...")

    geo_info = detect_proxy_geo(session, proxy_str=proxy_str or "")
    country_cc = geo_info.get("countryCode", "TH")
    country_locale = geo_info.get("locale", "en_US")
    session.cookies.set('locale', country_locale, domain='.facebook.com')
    session.cookies.set('wd', screen_info['wd'], domain='.facebook.com')
    session.cookies.set('dpr', screen_info['dpr'], domain='.facebook.com')

    engine = AdvancedAccountRegEngine(session, browser_profile, proxy_str=proxy_str)
    AppLogger.phase_header(1, "CREATE moi SDT (warmup + submit)")
    if not engine.warmup_and_extract_tokens():
        AppLogger.error("Warmup Facebook thất bại / proxy nghẽn.")
        return False

    new_password = generate_strong_password()
    gender = random.choice(["MALE", "FEMALE"])
    if country_cc == "VN":
        first_name = random.choice(MALE_VN) if gender == "MALE" else random.choice(FEMALE_VN)
        last_name = random.choice(SURNAMES_VN)
    elif country_cc == "TH":
        th_male = ["Somchai", "Arthit", "Kittisak", "Thanawat", "Chaiwat", "Anan"]
        th_female = ["Sunisa", "Pornthip", "Kanya", "Siriporn", "Apinya"]
        th_last = ["Prasert", "Suksom", "Wongsuwan", "Rattana", "Thongdee"]
        first_name = random.choice(th_male) if gender == "MALE" else random.choice(th_female)
        last_name = random.choice(th_last)
    else:
        first_name = random.choice(MALE_US) if gender == "MALE" else random.choice(FEMALE_US)
        last_name = random.choice(SURNAMES_US)
    dob = (random.randint(1, 28), random.randint(1, 12), random.randint(1990, 2004))
    gender_code = "1" if gender == "FEMALE" else "2"

    bait_phone = generate_phone_by_country(country_cc)
    AppLogger.persona_box(
        country=country_cc,
        device=device_label.strip(),
        name=f"{last_name} {first_name} (g={gender_code})",
        phone=bait_phone,
        password=new_password,
        proxy=formatted_proxy or proxy_str,
    )

    engine.check_field_validation(bait_phone, first_name, last_name)
    time.sleep(random.uniform(1.0, 2.0))

    AppLogger.step(1, "Init App & Tokens", "HTTP warmup")
    AppLogger.step(2, "Field Validation", f"SĐT mồi {bait_phone}")
    AppLogger.step(3, "Reg Mồi SĐT", f"Submit GraphQL với SĐT mồi {bait_phone}")
    ok_reg, created_uid = False, None
    for attempt in range(1, 3):
        ok_reg, created_uid = engine.submit_phone_reg(bait_phone, new_password, first_name, last_name, gender, dob)
        if ok_reg and created_uid:
            break
        if attempt < 2:
            bait_phone = generate_phone_by_country(country_cc)
            AppLogger.warn(f"SĐT mồi bị từ chối → đổi số mồi mới: {bait_phone}")
            time.sleep(random.uniform(1.5, 2.5))

    if not ok_reg or not created_uid:
        AppLogger.error("Reg mồi SĐT thất bại (2 lần). Bỏ lượt này.")
        return False

    AppLogger.success(f"Created UID={created_uid} | SĐT mồi: {bait_phone}")
    AppLogger.token("UID", str(created_uid))
    time.sleep(random.uniform(3.0, 5.0))

    AppLogger.phase_header(2, "SMS CODETEXTNOW + GẮN SĐT THẬT")
    AppLogger.step(4, "Thuê SĐT Thật", f"Codetextnow service_id={sid}")
    ok_rent, real_phone, req_id, rent_data = sms.rent_number(sid)
    if not ok_rent or not real_phone:
        AppLogger.error(f"Thuê số thật thất bại: {rent_data}")
        return False
    AppLogger.success(f"SĐT THẬT: {real_phone} | request_id={req_id}")

    phone_for_fb = str(real_phone).strip()
    if phone_for_fb and not phone_for_fb.startswith("+"):
        digits = re.sub(r"\D", "", phone_for_fb)
        if digits.startswith("1") and len(digits) == 11:
            phone_for_fb = f"+{digits}"
        elif len(digits) == 10:
            phone_for_fb = f"+1{digits}"
        else:
            phone_for_fb = f"+{digits}" if digits else phone_for_fb

    AppLogger.step(4, "Gắn SĐT Chính", f"add_contact_point → {phone_for_fb}")
    add_ok = engine.add_contact_point(created_uid, phone_for_fb)
    if not add_ok:
        AppLogger.warn("Gắn SĐT thật lần 1 fail → thử lại sau 3s...")
        time.sleep(3.0)
        add_ok = engine.add_contact_point(created_uid, phone_for_fb)
    if not add_ok:
        alt = re.sub(r"\D", "", phone_for_fb)
        AppLogger.warn(f"Thử format số khác: {alt}")
        add_ok = engine.add_contact_point(created_uid, alt) or engine.add_contact_point(created_uid, f"+{alt}")
    if not add_ok:
        AppLogger.error(f"Không gắn được SĐT thật {phone_for_fb} vào UID {created_uid}")
        return False

    AppLogger.success(f"Đã gắn SĐT chính {phone_for_fb} — chờ OTP SMS")
    time.sleep(random.uniform(2.0, 3.5))

    AppLogger.step(5, "OTP SMS", f"Chờ mã về {phone_for_fb} | resend FB x{resend_times}")
    resend_fn = (lambda: engine.resend_otp(created_uid)) if created_uid else None
    timeout = int((rent_data or {}).get("timeout") or 600)
    wait_sec = min(timeout, 180)
    otp_code = sms.wait_otp(
        request_id=req_id,
        max_wait=wait_sec,
        poll_every=3.0,
        resend_callback=resend_fn,
        resend_times=resend_times,
        resend_interval=12.0,
    )
    if not otp_code:
        AppLogger.error(f"Hết thời gian chờ OTP SMS ({phone_for_fb}, request_id={req_id})")
        return False

    AppLogger.success(f"OTP SMS: {otp_code}")
    time.sleep(random.uniform(1.0, 2.0))

    if not engine.verify_otp(created_uid, otp_code):
        AppLogger.error("Verify OTP thất bại.")
        return False

    is_live = check_account_and_bypass_049(session, browser_profile, created_uid)
    if not is_live:
        AppLogger.checkpoint("Checkpoint 282 — acc không live.")
        return False

    cookie_dict = session.cookies.get_dict()
    core_keys = ['c_user', 'xs', 'fr', 'datr', 'sb']
    cookie_parts = [f"{k}={cookie_dict[k]}" for k in core_keys if k in cookie_dict and cookie_dict[k]]
    ignored = {'wd', 'dpr', 'locale', 'ps_l', 'ps_n', 'm_pixel_ratio', 'vpd'}
    for k, v in cookie_dict.items():
        if k not in core_keys and k not in ignored and v:
            cookie_parts.append(f"{k}={v}")
    cookie_str = "; ".join(cookie_parts)
    if not created_uid and cookie_dict.get('c_user'):
        created_uid = cookie_dict['c_user']

    final_line = f"{created_uid}|{new_password}|{cookie_str}"
    AppLogger.success(f"TẠO ACC SMS THÀNH CÔNG (mồi={bait_phone} → xác minh={phone_for_fb}):\n{final_line}")

    totp_secret = None
    token_eaaau = None
    if enable_2fa:
        try:
            res_2fa = auto_enable_2fa(session, browser_profile, created_uid, new_password)
            if isinstance(res_2fa, tuple):
                totp_secret, token_eaaau = res_2fa
            else:
                totp_secret, token_eaaau = res_2fa, None

            if totp_secret:
                AppLogger.success(f"2FA OK: {totp_secret}")
                line_2fa = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}" if token_eaaau else f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
                safe_append_account_line(ACCOUNTS_2FA_FILE, line_2fa)
        except Exception as e:
            AppLogger.warn(f"2FA lỗi: {e}")

    if totp_secret and token_eaaau:
        save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}"
    elif totp_secret:
        save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
    elif token_eaaau:
        save_line = f"{created_uid}|{new_password}||{cookie_str}|{token_eaaau}"
    else:
        save_line = final_line

    if safe_append_account_line(ACCOUNTS_FULL_FILE, save_line):
        AppLogger.success(f"Đã lưu: {ACCOUNTS_FULL_FILE}")
    try:
        save_to_excel(created_uid, new_password, totp_secret or "NO_2FA", phone_for_fb, cookie_str, token_eaaau or "SMS")
    except Exception:
        pass
    try:
        send_telegram_live(
            uid=str(created_uid),
            password=new_password,
            cookie=cookie_str,
            phone=str(phone_for_fb or ""),
            mode="SMS",
            totp=totp_secret or "",
            eaau_token=token_eaaau or "",
        )
    except Exception:
        pass

    if HAS_REG_DOLA and enable_dola:
        def background_dola_task(c_str, px_str, u_id):
            time.sleep(10)
            try:
                ok_dola, sid2, dola_cookies, err = reg_dola.register_dola(c_str, proxy=px_str, uid=u_id)
                if ok_dola and dola_cookies:
                    reg_dola.save_dola_cookies(reg_dola.format_dola_cookie_string(dola_cookies))
                    AppLogger.success(f"[Dola] OK UID {u_id}")
                else:
                    AppLogger.warn(f"[Dola] Fail UID {u_id}: {err}")
            except Exception as e:
                AppLogger.warn(f"[Dola] Exception: {e}")
        t = threading.Thread(target=background_dola_task, args=(cookie_str, proxy_str, created_uid), daemon=True)
        active_dola_threads.append(t)
        t.start()

    return True


# ==============================================================================
# RUN ONE ACCOUNT — OTPTRUST (fix 4G/WiFi)
# ==============================================================================
def run_one_account_otptrust(
    proxy_str=None,
    enable_2fa=False,
    enable_dola=True,
    otptrust_api_key=None,
    service_id=1,
    provider="outlook",
    resend_times=4,
    thread_idx=None,
):
    global active_dola_threads

    api_key = (otptrust_api_key or OTPTRUST_API_KEY or "").strip()
    if not api_key:
        AppLogger.error("Thiếu OTPTrust API Key")
        return False
    mail_client = OTPTrustEmail(api_key=api_key)

    session = requests.Session()
    session.verify = False
    formatted_proxy = None
    if proxy_str:
        curr_px = proxy_str.strip()
        if not curr_px.startswith(("http://", "https://", "socks5://", "socks5h://")):
            parts = curr_px.split(":")
            if len(parts) == 4:
                formatted_proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            elif len(parts) == 2:
                formatted_proxy = f"http://{parts[0]}:{parts[1]}"
            else:
                formatted_proxy = f"http://{curr_px}"
        else:
            formatted_proxy = curr_px
        if "us.arxlabs.io" in formatted_proxy:
            sess_rand = uuid.uuid4().hex[:10]
            if "sessid-" in formatted_proxy:
                formatted_proxy = re.sub(r"sessid-[a-zA-Z0-9]+", "sessid-" + sess_rand, formatted_proxy)
            else:
                formatted_proxy = re.sub(r"(rx9l[a-zA-Z0-9\-]+)", r"\1-sessid-" + sess_rand, formatted_proxy, count=1)
        session.proxies.update({"http": formatted_proxy, "https": formatted_proxy})
        AppLogger.proxy(f"Sử dụng Proxy: {formatted_proxy}")
    else:
        session.proxies = {}
        session.trust_env = False
        AppLogger.proxy("Chạy 4G/WiFi THẬT (Direct — không proxy)")

    browser_profile, screen_info = generate_random_browser_profile(thread_seed=thread_idx)
    device_label = (
        f"{browser_profile.get('device_model') or browser_profile.get('platform') or 'Device'} "
        f"Chrome/{browser_profile.get('chrome_v')} {screen_info.get('wd')}@{screen_info.get('dpr')}"
    )
    AppLogger.cookie(f"Live Meta DATR: {(browser_profile.get('device_id') or '')[:24]}...")
    AppLogger.tls("Active Engine: Requests Standard (HTTP/1.1 Fallback)")
    AppLogger.info(f"datr: {(browser_profile.get('device_id') or '')[:28]}...")

    geo_info = detect_proxy_geo(session, proxy_str=proxy_str or "")
    country_cc = geo_info.get("countryCode", "TH")
    country_locale = geo_info.get("locale", "en_US")
    session.cookies.set("locale", country_locale, domain=".facebook.com")
    session.cookies.set("wd", screen_info["wd"], domain=".facebook.com")
    session.cookies.set("dpr", screen_info["dpr"], domain=".facebook.com")

    engine = AdvancedAccountRegEngine(session, browser_profile, proxy_str=proxy_str)
    AppLogger.phase_header(1, "CREATE moi SDT (warmup + submit)")
    if not engine.warmup_and_extract_tokens():
        AppLogger.error("Warmup Facebook thất bại / proxy nghẽn.")
        return False

    new_password = generate_strong_password()
    gender = random.choice(["MALE", "FEMALE"])
    if country_cc == "VN":
        first_name = random.choice(MALE_VN) if gender == "MALE" else random.choice(FEMALE_VN)
        last_name = random.choice(SURNAMES_VN)
    elif country_cc == "TH":
        th_male = ["Somchai", "Arthit", "Kittisak", "Thanawat", "Chaiwat", "Anan"]
        th_female = ["Sunisa", "Pornthip", "Kanya", "Siriporn", "Apinya"]
        th_last = ["Prasert", "Suksom", "Wongsuwan", "Rattana", "Thongdee"]
        first_name = random.choice(th_male) if gender == "MALE" else random.choice(th_female)
        last_name = random.choice(th_last)
    else:
        first_name = random.choice(MALE_US) if gender == "MALE" else random.choice(FEMALE_US)
        last_name = random.choice(SURNAMES_US)
    dob = (random.randint(1, 28), random.randint(1, 12), random.randint(1990, 2004))
    gender_code = "1" if gender == "FEMALE" else "2"

    bait_phone = generate_phone_by_country(country_cc)
    AppLogger.persona_box(
        country=country_cc,
        device=device_label.strip(),
        name=f"{last_name} {first_name} (g={gender_code})",
        phone=bait_phone,
        password=new_password,
        proxy=formatted_proxy or proxy_str,
    )

    engine.check_field_validation(bait_phone, first_name, last_name)
    time.sleep(random.uniform(1.0, 2.0))

    AppLogger.step(1, "Init App & Tokens", "HTTP warmup")
    AppLogger.step(2, "Field Validation", f"SĐT mồi {bait_phone}")
    AppLogger.step(3, "Reg Mồi SĐT", f"Submit GraphQL với SĐT mồi {bait_phone}")
    ok_reg, created_uid = False, None
    for attempt in range(1, 3):
        ok_reg, created_uid = engine.submit_phone_reg(bait_phone, new_password, first_name, last_name, gender, dob)
        if ok_reg and created_uid:
            break
        if attempt < 2:
            bait_phone = generate_phone_by_country(country_cc)
            AppLogger.warn(f"SĐT mồi bị từ chối → đổi số mồi: {bait_phone}")
            time.sleep(random.uniform(1.5, 2.5))

    if not ok_reg or not created_uid:
        AppLogger.error("Reg mồi SĐT thất bại.")
        return False
    AppLogger.success(f"Created UID={created_uid}")
    AppLogger.token("UID", str(created_uid))
    time.sleep(random.uniform(3.0, 5.0))

    AppLogger.phase_header(2, "OTPTRUST + CHANGE EMAIL")
    AppLogger.step(4, "Thuê Email OTPTrust", f"provider={provider} service_id={service_id}")
    ok_rent, email_addr, order_id, rent_data = mail_client.rent(service_id, provider=provider)
    if not ok_rent or not email_addr:
        AppLogger.error(f"Thuê email thất bại: {rent_data}")
        return False
    AppLogger.success(f"Email: {email_addr} | order_id={order_id}")

    AppLogger.step(4, "Gắn Email Chính", f"add_contact_point → {email_addr}")
    add_ok = engine.add_contact_point(created_uid, email_addr)
    if not add_ok:
        AppLogger.warn("Gắn email lần 1 fail → thử lại sau 3s...")
        time.sleep(3.0)
        add_ok = engine.add_contact_point(created_uid, email_addr)
    if not add_ok:
        AppLogger.error(f"Không gắn được email {email_addr}")
        try:
            mail_client.cancel(order_id)
        except Exception:
            pass
        return False
    AppLogger.success(f"Đã gắn {email_addr} — chờ OTP")
    time.sleep(random.uniform(2.0, 3.5))

    AppLogger.step(5, "OTP Email", f"Chờ mã về {email_addr} | resend x{resend_times}")
    resend_fn = (lambda: engine.resend_otp(created_uid)) if created_uid else None
    otp_code = mail_client.wait_otp(
        order_id=order_id,
        max_wait=180,
        poll_every=3.0,
        resend_callback=resend_fn,
        resend_times=resend_times,
        resend_interval=15.0,
        reorder_on_resend=True,
    )
    if not otp_code:
        AppLogger.error(f"Hết thời gian chờ OTP email ({email_addr})")
        try:
            mail_client.cancel(order_id)
        except Exception:
            pass
        return False

    AppLogger.success(f"OTP Email: {otp_code}")
    time.sleep(random.uniform(1.0, 2.0))

    if not engine.verify_otp(created_uid, otp_code):
        AppLogger.error("Verify OTP thất bại.")
        return False

    is_live = check_account_and_bypass_049(session, browser_profile, created_uid)
    if not is_live:
        AppLogger.checkpoint("Checkpoint 282 — acc không live.")
        return False

    cookie_dict = session.cookies.get_dict()
    core_keys = ["c_user", "xs", "fr", "datr", "sb"]
    cookie_parts = [f"{k}={cookie_dict[k]}" for k in core_keys if k in cookie_dict and cookie_dict[k]]
    ignored = {"wd", "dpr", "locale", "ps_l", "ps_n", "m_pixel_ratio", "vpd"}
    for k, v in cookie_dict.items():
        if k not in core_keys and k not in ignored and v:
            cookie_parts.append(f"{k}={v}")
    cookie_str = "; ".join(cookie_parts)
    if not created_uid and cookie_dict.get("c_user"):
        created_uid = cookie_dict["c_user"]

    final_line = f"{created_uid}|{new_password}|{cookie_str}"
    AppLogger.success(f"TẠO ACC OTPTRUST OK (mồi={bait_phone} → mail={email_addr}):\n{final_line}")

    totp_secret = None
    token_eaaau = None
    if enable_2fa:
        try:
            res_2fa = auto_enable_2fa(session, browser_profile, created_uid, new_password)
            if isinstance(res_2fa, tuple):
                totp_secret, token_eaaau = res_2fa
            else:
                totp_secret, token_eaaau = res_2fa, None

            if totp_secret:
                AppLogger.success(f"2FA OK: {totp_secret}")
                line_2fa = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}" if token_eaaau else f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
                safe_append_account_line(ACCOUNTS_2FA_FILE, line_2fa)
        except Exception as e:
            AppLogger.warn(f"2FA lỗi: {e}")

    if totp_secret and token_eaaau:
        save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}"
    elif totp_secret:
        save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
    elif token_eaaau:
        save_line = f"{created_uid}|{new_password}||{cookie_str}|{token_eaaau}"
    else:
        save_line = final_line

    if safe_append_account_line(ACCOUNTS_FULL_FILE, save_line):
        AppLogger.success(f"Đã lưu: {ACCOUNTS_FULL_FILE}")
    try:
        save_to_excel(created_uid, new_password, totp_secret or "NO_2FA", email_addr, cookie_str, token_eaaau or "OTPTRUST")
    except Exception:
        pass
    try:
        send_telegram_live(
            uid=str(created_uid),
            password=new_password,
            cookie=cookie_str,
            email=str(email_addr or ""),
            mode="OTPTRUST",
            totp=totp_secret or "",
            eaau_token=token_eaaau or "",
        )
    except Exception:
        pass

    if HAS_REG_DOLA and enable_dola:
        def background_dola_task(c_str, px_str, u_id):
            time.sleep(10)
            try:
                ok_dola, sid2, dola_cookies, err = reg_dola.register_dola(c_str, proxy=px_str, uid=u_id)
                if ok_dola and dola_cookies:
                    reg_dola.save_dola_cookies(reg_dola.format_dola_cookie_string(dola_cookies))
                    AppLogger.success(f"[Dola] OK UID {u_id}")
                else:
                    AppLogger.warn(f"[Dola] Fail UID {u_id}: {err}")
            except Exception as e:
                AppLogger.warn(f"[Dola] Exception: {e}")
        t = threading.Thread(target=background_dola_task, args=(cookie_str, proxy_str, created_uid), daemon=True)
        active_dola_threads.append(t)
        t.start()

    return True


# ==============================================================================
# RUN ONE ACCOUNT — VIETMAIL (fix 4G/WiFi)
# ==============================================================================
def run_one_account_vietmail(
    proxy_str=None,
    enable_2fa=False,
    enable_dola=True,
    vietmail_key=None,
    vietmail_base=None,
    resend_times=4,
    thread_idx=None,
) -> bool:
    global active_dola_threads

    key = (vietmail_key or VIETMAIL_API_KEY_B64 or "").strip()
    base = (vietmail_base or VIETMAIL_BASE or "").strip()
    mail_client = VietMailClient(api_key_b64=key, base_url=base)

    session = requests.Session()
    session.verify = False
    formatted_proxy = None
    if proxy_str:
        curr_px = proxy_str.strip()
        if not curr_px.startswith(("http://", "https://", "socks5://", "socks5h://")):
            parts = curr_px.split(":")
            if len(parts) == 4:
                formatted_proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            elif len(parts) == 2:
                formatted_proxy = f"http://{parts[0]}:{parts[1]}"
            else:
                formatted_proxy = f"http://{curr_px}"
        else:
            formatted_proxy = curr_px
        session.proxies.update({"http": formatted_proxy, "https": formatted_proxy})
        AppLogger.proxy(f"Su dung Proxy: {formatted_proxy}")
    else:
        session.proxies = {}
        session.trust_env = False
        AppLogger.proxy("Chay 4G/WiFi THAT (Direct — khong proxy)")

    browser_profile, screen_info = generate_random_browser_profile(thread_seed=thread_idx)
    device_label = (
        f"{browser_profile.get('device_model') or browser_profile.get('platform') or 'Device'} "
        f"Chrome/{browser_profile.get('chrome_v')} {screen_info.get('wd')}@{screen_info.get('dpr')}"
    )
    AppLogger.cookie(f"Live Meta DATR: {(browser_profile.get('device_id') or '')[:24]}...")
    AppLogger.tls("Active Engine: Requests Standard (HTTP/1.1 Fallback)")
    AppLogger.info(f"datr: {(browser_profile.get('device_id') or '')[:28]}...")

    geo_info = detect_proxy_geo(session, proxy_str=proxy_str or "")
    country_cc = geo_info.get("countryCode", "TH")
    country_locale = geo_info.get("locale", "en_US")
    session.cookies.set("locale", country_locale, domain=".facebook.com")
    session.cookies.set("wd", screen_info["wd"], domain=".facebook.com")
    session.cookies.set("dpr", screen_info["dpr"], domain=".facebook.com")

    engine = AdvancedAccountRegEngine(session, browser_profile, proxy_str=proxy_str)
    AppLogger.phase_header(1, "CREATE moi SDT (warmup + submit)")
    if not engine.warmup_and_extract_tokens():
        AppLogger.error("Warmup Facebook that bai / proxy nghe.")
        return False

    new_password = generate_strong_password()
    gender = random.choice(["MALE", "FEMALE"])
    if country_cc == "VN":
        first_name = random.choice(MALE_VN) if gender == "MALE" else random.choice(FEMALE_VN)
        last_name = random.choice(SURNAMES_VN)
    elif country_cc == "TH":
        th_male = ["Somchai", "Arthit", "Kittisak", "Thanawat", "Chaiwat", "Anan"]
        th_female = ["Sunisa", "Pornthip", "Kanya", "Siriporn", "Apinya"]
        th_last = ["Prasert", "Suksom", "Wongsuwan", "Rattana", "Thongdee"]
        first_name = random.choice(th_male) if gender == "MALE" else random.choice(th_female)
        last_name = random.choice(th_last)
    else:
        first_name = random.choice(MALE_US) if gender == "MALE" else random.choice(FEMALE_US)
        last_name = random.choice(SURNAMES_US)
    dob = (random.randint(1, 28), random.randint(1, 12), random.randint(1990, 2004))
    gender_code = "1" if gender == "FEMALE" else "2"

    bait_phone = generate_phone_by_country(country_cc)
    AppLogger.persona_box(
        country=country_cc,
        device=device_label.strip(),
        name=f"{last_name} {first_name} (g={gender_code})",
        phone=bait_phone,
        password=new_password,
        proxy=formatted_proxy or proxy_str,
    )

    engine.check_field_validation(bait_phone, first_name, last_name)
    time.sleep(random.uniform(1.0, 2.0))

    AppLogger.step(1, "Init App & Tokens", "HTTP warmup")
    AppLogger.step(2, "Field Validation", f"SĐT mồi {bait_phone}")
    AppLogger.step(3, "Reg Moi SDT", f"Submit GraphQL voi SDT moi {bait_phone}")
    ok_reg, created_uid = False, None
    for attempt in range(1, 3):
        ok_reg, created_uid = engine.submit_phone_reg(bait_phone, new_password, first_name, last_name, gender, dob)
        if ok_reg and created_uid:
            break
        if attempt < 2:
            bait_phone = generate_phone_by_country(country_cc)
            AppLogger.warn(f"SDT moi bi tu choi -> doi so moi: {bait_phone}")
            time.sleep(random.uniform(1.5, 2.5))

    if not ok_reg or not created_uid:
        AppLogger.error("Reg moi SDT that bai.")
        return False
    AppLogger.success(f"Created UID={created_uid}")
    AppLogger.token("UID", str(created_uid))
    time.sleep(random.uniform(3.0, 5.0))

    AppLogger.phase_header(2, "VIETMAIL + CHANGE EMAIL")
    AppLogger.step(4, "Thue Email VietMail", f"base={base}")
    _VIETMAIL_RENT_LOCK.acquire()
    try:
        mail_client.tra()
    except Exception:
        pass
    ok_rent, email_addr, order_id, rent_data = mail_client.thue()
    if not ok_rent or not email_addr:
        AppLogger.error(f"Thue email VietMail that bai: {rent_data}")
        try:
            _VIETMAIL_RENT_LOCK.release()
        except Exception:
            pass
        return False
    AppLogger.success(f"Email: {email_addr} | token={(str(order_id)[:20]+'...') if order_id else '-'}")
    if order_id:
        try:
            with open("vietmail_tokens.txt", "a", encoding="utf-8") as tf:
                tf.write(f"{email_addr}|{order_id}\n")
        except Exception:
            pass

    AppLogger.step(5, "OPEN_CHANGE_EMAIL / SUBMIT", f"add_contact_point -> {email_addr}")
    add_ok = engine.add_contact_point(created_uid, email_addr)
    if not add_ok:
        time.sleep(3.0)
        add_ok = engine.add_contact_point(created_uid, email_addr)
    if not add_ok:
        AppLogger.error(f"Khong gan duoc email {email_addr}")
        try:
            mail_client.tra()
        except Exception:
            pass
        try:
            _VIETMAIL_RENT_LOCK.release()
        except Exception:
            pass
        return False
    AppLogger.success(f"Da gan {email_addr} — cho OTP")
    time.sleep(random.uniform(2.0, 3.5))

    AppLogger.phase_header(3, "OTP VIETMAIL")
    AppLogger.step(6, "Cho OTP Email", f"mail={email_addr} | resend x{resend_times}")
    resend_fn = (lambda: engine.resend_otp(created_uid)) if created_uid else None
    otp_code = mail_client.wait_otp(
        email=email_addr,
        order_id=order_id,
        max_wait=180,
        poll_every=3.0,
        resend_callback=resend_fn,
        resend_times=resend_times,
        resend_interval=15.0,
    )
    if not otp_code:
        AppLogger.error(f"Het thoi gian cho OTP email ({email_addr})")
        try:
            mail_client.tra()
        except Exception:
            pass
        try:
            _VIETMAIL_RENT_LOCK.release()
        except Exception:
            pass
        return False

    AppLogger.success(f"OTP Email: {otp_code}")
    time.sleep(random.uniform(1.0, 2.0))

    if not engine.verify_otp(created_uid, otp_code):
        AppLogger.error("Verify OTP that bai.")
        try:
            mail_client.tra()
        except Exception:
            pass
        try:
            _VIETMAIL_RENT_LOCK.release()
        except Exception:
            pass
        return False

    try:
        tr = mail_client.tra()
        AppLogger.info(f"[VietMail] Tra mail: {tr.get('message')} | {tr.get('email')}")
    except Exception:
        pass
    finally:
        try:
            _VIETMAIL_RENT_LOCK.release()
        except Exception:
            pass

    is_live = check_account_and_bypass_049(session, browser_profile, created_uid)
    if not is_live:
        AppLogger.checkpoint("Checkpoint 282 — acc khong live.")
        return False

    cookie_dict = session.cookies.get_dict()
    core_keys = ["c_user", "xs", "fr", "datr", "sb"]
    cookie_parts = [f"{k}={cookie_dict[k]}" for k in core_keys if k in cookie_dict and cookie_dict[k]]
    ignored = {"wd", "dpr", "locale", "ps_l", "ps_n", "m_pixel_ratio", "vpd"}
    for k, v in cookie_dict.items():
        if k not in core_keys and k not in ignored and v:
            cookie_parts.append(f"{k}={v}")
    cookie_str = "; ".join(cookie_parts)
    if not created_uid and cookie_dict.get("c_user"):
        created_uid = cookie_dict["c_user"]

    final_line = f"{created_uid}|{new_password}|{cookie_str}"
    AppLogger.live(f"VIETMAIL LIVE OK: {created_uid}|{email_addr}")
    AppLogger.success(f"Saved LIVE -> accounts_full.txt | {final_line[:90]}...")

    totp_secret = None
    token_eaaau = None
    if enable_2fa:
        try:
            res_2fa = auto_enable_2fa(session, browser_profile, created_uid, new_password)
            if isinstance(res_2fa, tuple):
                totp_secret, token_eaaau = res_2fa
            else:
                totp_secret, token_eaaau = res_2fa, None

            if totp_secret:
                AppLogger.success(f"2FA OK: {totp_secret}")
                line_2fa = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}" if token_eaaau else f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
                safe_append_account_line(ACCOUNTS_2FA_FILE, line_2fa)
        except Exception as e:
            AppLogger.warn(f"2FA loi: {e}")

    if totp_secret and token_eaaau:
        save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}"
    elif totp_secret:
        save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
    elif token_eaaau:
        save_line = f"{created_uid}|{new_password}||{cookie_str}|{token_eaaau}"
    else:
        save_line = final_line

    if safe_append_account_line(ACCOUNTS_FULL_FILE, save_line):
        AppLogger.success(f"Da luu: {ACCOUNTS_FULL_FILE}")
    try:
        save_to_excel(created_uid, new_password, totp_secret or "NO_2FA", email_addr, cookie_str, token_eaaau or "VIETMAIL")
    except Exception:
        pass
    try:
        send_telegram_live(
            uid=str(created_uid),
            password=new_password,
            cookie=cookie_str,
            email=str(email_addr or ""),
            mode="VIETMAIL",
            totp=totp_secret or "",
            eaau_token=token_eaaau or "",
        )
    except Exception:
        pass

    if HAS_REG_DOLA and enable_dola:
        def background_dola_task(c_str, px_str, u_id):
            time.sleep(10)
            try:
                ok_dola, sid2, dola_cookies, err = reg_dola.register_dola(c_str, proxy=px_str, uid=u_id)
                if ok_dola and dola_cookies:
                    reg_dola.save_dola_cookies(reg_dola.format_dola_cookie_string(dola_cookies))
                    AppLogger.success(f"[Dola] OK UID {u_id}")
                else:
                    AppLogger.warn(f"[Dola] Fail UID {u_id}: {err}")
            except Exception as e:
                AppLogger.warn(f"[Dola] Exception: {e}")
        th = threading.Thread(target=background_dola_task, args=(cookie_str, proxy_str, created_uid), daemon=True)
        active_dola_threads.append(th)
        th.start()

    return True


# ==============================================================================
# RUN ONE ACCOUNT & BATCH RUNNER — PSTMMO.CC
# ==============================================================================
def run_one_account_pstmmo(
    proxy_str: Optional[str] = None,
    enable_2fa: bool = False,
    enable_dola: bool = True,
    pstmmo_key: str = None,
    pstmmo_domain: str = "",
    resend_times: int = 4,
    thread_idx: Optional[int] = None,
) -> bool:
    global active_dola_threads

    mail_client = PSTMMOEmail(api_key=pstmmo_key)

    session = requests.Session()
    session.verify = False
    formatted_proxy = None
    if proxy_str:
        curr_px = proxy_str.strip()
        if not curr_px.startswith(("http://", "https://", "socks5://", "socks5h://")):
            parts = curr_px.split(":")
            if len(parts) == 4:
                formatted_proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            elif len(parts) == 2:
                formatted_proxy = f"http://{parts[0]}:{parts[1]}"
            else:
                formatted_proxy = f"http://{curr_px}"
        else:
            formatted_proxy = curr_px
        if "us.arxlabs.io" in formatted_proxy:
            sess_rand = uuid.uuid4().hex[:10]
            if "sessid-" in formatted_proxy:
                formatted_proxy = re.sub(r"sessid-[a-zA-Z0-9]+", "sessid-" + sess_rand, formatted_proxy)
            else:
                formatted_proxy = re.sub(r"(rx9l[a-zA-Z0-9\-]+)", r"\1-sessid-" + sess_rand, formatted_proxy, count=1)
        session.proxies.update({"http": formatted_proxy, "https": formatted_proxy})
        AppLogger.proxy(f"Sử dụng Proxy: {formatted_proxy}")
    else:
        session.proxies = {}
        session.trust_env = False
        AppLogger.proxy("Chạy 4G/WiFi THẬT (Direct — không proxy)")

    browser_profile, screen_info = generate_random_browser_profile(thread_seed=thread_idx)
    device_label = (
        f"{browser_profile.get('device_model') or browser_profile.get('platform') or 'Device'} "
        f"Chrome/{browser_profile.get('chrome_v')} {screen_info.get('wd')}@{screen_info.get('dpr')}"
    )

    geo_info = detect_proxy_geo(session, proxy_str=proxy_str or "")
    country_cc = geo_info.get("countryCode", "TH")
    country_locale = geo_info.get("locale", "en_US")
    session.cookies.set("locale", country_locale, domain=".facebook.com")
    session.cookies.set("wd", screen_info["wd"], domain=".facebook.com")
    session.cookies.set("dpr", screen_info["dpr"], domain=".facebook.com")

    engine = AdvancedAccountRegEngine(session, browser_profile, proxy_str=proxy_str)
    AppLogger.phase_header(1, "CREATE MỒI SĐT (WARMUP + SUBMIT)")
    if not engine.warmup_and_extract_tokens():
        AppLogger.error("Warmup Facebook thất bại / proxy nghẽn.")
        return False

    new_password = generate_strong_password()
    gender = random.choice(["MALE", "FEMALE"])
    if country_cc == "VN":
        first_name = random.choice(MALE_VN) if gender == "MALE" else random.choice(FEMALE_VN)
        last_name = random.choice(SURNAMES_VN)
    elif country_cc == "TH":
        th_male = ["Somchai", "Arthit", "Kittisak", "Thanawat", "Chaiwat", "Anan"]
        th_female = ["Sunisa", "Pornthip", "Kanya", "Siriporn", "Apinya"]
        th_last = ["Prasert", "Suksom", "Wongsuwan", "Rattana", "Thongdee"]
        first_name = random.choice(th_male) if gender == "MALE" else random.choice(th_female)
        last_name = random.choice(th_last)
    else:
        first_name = random.choice(MALE_US) if gender == "MALE" else random.choice(FEMALE_US)
        last_name = random.choice(SURNAMES_US)
    dob = (random.randint(1, 28), random.randint(1, 12), random.randint(1990, 2004))
    gender_code = "1" if gender == "FEMALE" else "2"

    bait_phone = generate_phone_by_country(country_cc)
    AppLogger.persona_box(
        country=country_cc,
        device=device_label.strip(),
        name=f"{last_name} {first_name} (g={gender_code})",
        phone=bait_phone,
        password=new_password,
        proxy=formatted_proxy or proxy_str,
    )

    engine.check_field_validation(bait_phone, first_name, last_name)
    time.sleep(random.uniform(1.0, 2.0))

    ok_reg, created_uid = False, None
    for attempt in range(1, 3):
        ok_reg, created_uid = engine.submit_phone_reg(bait_phone, new_password, first_name, last_name, gender, dob)
        if ok_reg and created_uid:
            break
        if attempt < 2:
            bait_phone = generate_phone_by_country(country_cc)
            AppLogger.warn(f"SĐT mồi bị từ chối -> đổi số mồi: {bait_phone}")
            time.sleep(random.uniform(1.5, 2.5))

    if not ok_reg or not created_uid:
        AppLogger.error("Reg mồi SĐT thất bại.")
        return False

    AppLogger.success(f"Created UID={created_uid}")
    time.sleep(random.uniform(3.0, 5.0))

    AppLogger.phase_header(2, "PSTMMO.CC + CHANGE EMAIL")
    AppLogger.step(4, "Thuê Email PSTMMO", f"site=facebook.com | domain={pstmmo_domain or 'AUTO'}")
    ok_rent, email_addr, order_id, rent_data = mail_client.rent(site="facebook.com", domain=pstmmo_domain)
    if not ok_rent or not email_addr:
        AppLogger.error(f"Thuê email PSTMMO thất bại: {rent_data}")
        return False

    AppLogger.success(f"Đã thuê Email: {email_addr} | order_id={order_id}")

    AppLogger.step(4, "Gắn Email Chính", f"add_contact_point -> {email_addr}")
    add_ok = engine.add_contact_point(created_uid, email_addr)
    if not add_ok:
        AppLogger.warn("Gắn email lần 1 fail -> chờ 3s thử lại...")
        time.sleep(3.0)
        add_ok = engine.add_contact_point(created_uid, email_addr)
    if not add_ok:
        AppLogger.error(f"Không gắn được email {email_addr} -> Gọi hủy đơn hoàn tiền 100%...")
        ok_c, msg_c = mail_client.cancel(order_id)
        AppLogger.info(f"[PSTMMO Cancel] {msg_c}")
        return False

    AppLogger.success(f"Đã gắn {email_addr} — bắt đầu chờ OTP...")
    time.sleep(random.uniform(2.0, 3.5))

    AppLogger.step(5, "Chờ OTP PSTMMO", f"mail={email_addr} | order_id={order_id} | resend x{resend_times}")
    resend_fn = (lambda: engine.resend_otp(created_uid)) if created_uid else None
    otp_code = mail_client.wait_otp(
        order_id=order_id,
        max_wait=180,
        poll_every=3.5,
        resend_callback=resend_fn,
        resend_times=resend_times,
        resend_interval=15.0,
        auto_cancel_on_timeout=True,
    )
    if not otp_code:
        AppLogger.error(f"Hết thời gian chờ OTP từ {email_addr}")
        return False

    AppLogger.success(f"OTP PSTMMO: {otp_code}")
    time.sleep(random.uniform(1.0, 2.0))

    if not engine.verify_otp(created_uid, otp_code):
        AppLogger.error("Verify OTP thất bại.")
        return False

    is_live = check_account_and_bypass_049(session, browser_profile, created_uid)
    if not is_live:
        AppLogger.checkpoint("Checkpoint 282 — acc không live.")
        return False

    cookie_dict = session.cookies.get_dict()
    core_keys = ["c_user", "xs", "fr", "datr", "sb"]
    cookie_parts = [f"{k}={cookie_dict[k]}" for k in core_keys if k in cookie_dict and cookie_dict[k]]
    ignored = {"wd", "dpr", "locale", "ps_l", "ps_n", "m_pixel_ratio", "vpd"}
    for k, v in cookie_dict.items():
        if k not in core_keys and k not in ignored and v:
            cookie_parts.append(f"{k}={v}")
    cookie_str = "; ".join(cookie_parts)
    if not created_uid and cookie_dict.get("c_user"):
        created_uid = cookie_dict["c_user"]

    final_line = f"{created_uid}|{new_password}|{cookie_str}"
    AppLogger.live(f"PSTMMO LIVE OK: {created_uid}|{email_addr}")

    totp_secret = None
    token_eaaau = None
    if enable_2fa:
        try:
            res_2fa = auto_enable_2fa(session, browser_profile, created_uid, new_password)
            if isinstance(res_2fa, tuple):
                totp_secret, token_eaaau = res_2fa
            else:
                totp_secret, token_eaaau = res_2fa, None

            if totp_secret:
                AppLogger.success(f"2FA OK: {totp_secret}")
                line_2fa = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}" if token_eaaau else f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
                safe_append_account_line(ACCOUNTS_2FA_FILE, line_2fa)
        except Exception as e:
            AppLogger.warn(f"2FA lỗi: {e}")

    if totp_secret and token_eaaau:
        save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}|{token_eaaau}"
    elif totp_secret:
        save_line = f"{created_uid}|{new_password}|{totp_secret}|{cookie_str}"
    elif token_eaaau:
        save_line = f"{created_uid}|{new_password}||{cookie_str}|{token_eaaau}"
    else:
        save_line = final_line

    if safe_append_account_line(ACCOUNTS_FULL_FILE, save_line):
        AppLogger.success(f"Đã lưu: {ACCOUNTS_FULL_FILE}")
    try:
        save_to_excel(created_uid, new_password, totp_secret or "NO_2FA", email_addr, cookie_str, token_eaaau or "PSTMMO")
    except Exception:
        pass
    try:
        send_telegram_live(
            uid=str(created_uid),
            password=new_password,
            cookie=cookie_str,
            email=str(email_addr or ""),
            mode="PSTMMO",
            totp=totp_secret or "",
            eaau_token=token_eaaau or "",
        )
    except Exception:
        pass

    if HAS_REG_DOLA and enable_dola:
        def background_dola_task(c_str, px_str, u_id):
            time.sleep(10)
            try:
                ok_dola, sid2, dola_cookies, err = reg_dola.register_dola(c_str, proxy=px_str, uid=u_id)
                if ok_dola and dola_cookies:
                    reg_dola.save_dola_cookies(reg_dola.format_dola_cookie_string(dola_cookies))
                    AppLogger.success(f"[Dola] OK UID {u_id}")
                else:
                    AppLogger.warn(f"[Dola] Fail UID {u_id}: {err}")
            except Exception as e:
                AppLogger.warn(f"[Dola] Exception: {e}")
        th = threading.Thread(target=background_dola_task, args=(cookie_str, proxy_str, created_uid), daemon=True)
        active_dola_threads.append(th)
        th.start()

    return True


def main_batch_runner_pstmmo(
    num_accs: int = 1,
    proxy_str: Optional[str] = None,
    enable_2fa: bool = False,
    enable_dola: bool = True,
    pstmmo_key: str = None,
    pstmmo_domain: str = "",
    resend_times: int = 4,
    max_workers: int = 1,
    proxy_file: str = None,
):
    global success_count_global, fail_count_global, _stop_flag
    print_lock = threading.Lock()
    job_counter = {"n": 0}
    job_lock = threading.Lock()
    target_live = max(1, int(num_accs))

    def _plog(msg: str):
        with print_lock:
            print(msg, flush=True)

    def _next_job_no():
        with job_lock:
            job_counter["n"] += 1
            return job_counter["n"]

    def _worker(thread_idx, proxy_pool, fallback_proxy):
        global success_count_global, fail_count_global, _stop_flag
        ok_local = 0
        fail_local = 0
        _plog(f"[L{thread_idx}] sẵn sàng — mục tiêu {target_live} acc LIVE (PSTMMO)")
        while not _stop_flag:
            with COUNTER_LOCK:
                if success_count_global >= target_live:
                    break
            job_no = _next_job_no()
            px = proxy_pool.next() if (proxy_pool and len(proxy_pool) > 0) else fallback_proxy
            with COUNTER_LOCK:
                cur_ok = success_count_global
            _plog(f"[L{thread_idx}] ===== Lần thử #{job_no} | live {cur_ok}/{target_live} | px={px or 'DIRECT'} =====")
            try:
                success = run_one_account_pstmmo(
                    proxy_str=px,
                    enable_2fa=enable_2fa,
                    enable_dola=enable_dola,
                    pstmmo_key=pstmmo_key,
                    pstmmo_domain=pstmmo_domain,
                    resend_times=resend_times,
                    thread_idx=thread_idx,
                )
            except Exception as e:
                success = False
                _plog(f"[L{thread_idx}] Exception: {e}")

            if success:
                ok_local += 1
                with COUNTER_LOCK:
                    success_count_global += 1
                    cur_ok = success_count_global
                    if cur_ok >= target_live:
                        _stop_flag = True
                with print_lock:
                    AppLogger.live_banner(thread_idx, cur_ok, target_live, job_no)
                if cur_ok >= target_live:
                    with print_lock:
                        AppLogger.live_banner(thread_idx, cur_ok, target_live, job_no, extra=f"ĐÃ ĐỦ {target_live} LIVE")
                    break
            else:
                fail_local += 1
                with COUNTER_LOCK:
                    fail_count_global += 1
                _plog(f"[L{thread_idx}] ✗ FAIL thử #{job_no} | live {success_count_global}/{target_live}")
        _plog(f"[L{thread_idx}] kết thúc: {ok_local} OK / {fail_local} FAIL")

    _stop_flag = False
    success_count_global = 0
    fail_count_global = 0

    proxies = load_proxies_from_file(proxy_file) if proxy_file else []
    proxy_pool = ProxyFilePool(proxies) if proxies else None

    workers = max(1, int(max_workers or 1))
    print(f"[+] Luồng: {workers} | Mục tiêu LIVE: {target_live} | Domain: {pstmmo_domain or 'Tự chọn (Auto)'}")
    print("=" * 70)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_worker, i + 1, proxy_pool, proxy_str) for i in range(workers)]
        for f in as_completed(futs):
            try:
                f.result()
            except Exception as e:
                print(f"[!] Worker error: {e}")

    print("\n" + "=" * 70)
    AppLogger.success(f"HOÀN TẤT PSTMMO: LIVE={success_count_global}/{target_live} | FAIL={fail_count_global} | Tổng thử={job_counter['n']}")
    print("=" * 70)


# ==============================================================================
# BATCH RUNNERS (SMS / OTPTRUST / VIETMAIL / GMAIL)
# ==============================================================================
def main_batch_runner_sms(num_accs: int = 1, proxy_str: Optional[str] = None, enable_2fa: bool = False, enable_dola: bool = True, sms_service_id: int = None, sms_api_key: str = None, resend_times: int = 4):
    ok_count = 0
    fail_count = 0
    for i in range(1, num_accs + 1):
        print("\n" + "=" * 70)
        AppLogger.info(f"SMS REG [{i}/{num_accs}]")
        print("=" * 70)
        success = run_one_account_sms(
            proxy_str=proxy_str,
            enable_2fa=enable_2fa,
            enable_dola=enable_dola,
            sms_service_id=sms_service_id,
            sms_api_key=sms_api_key,
            resend_times=resend_times,
        )
        if success:
            ok_count += 1
            AppLogger.success(f"Acc SMS {i} OK (tổng OK={ok_count})")
        else:
            fail_count += 1
            AppLogger.error(f"Acc SMS {i} FAIL (tổng FAIL={fail_count})")
        if i < num_accs:
            delay = random.uniform(3.0, 6.0)
            AppLogger.wait(f"Nghỉ {delay:.1f}s...")
            time.sleep(delay)

    if enable_dola and active_dola_threads:
        while any(t.is_alive() for t in active_dola_threads):
            AppLogger.wait("Chờ Dola background...")
            time.sleep(5)

    print("\n" + "=" * 70)
    AppLogger.success(f"HOÀN TẤT SMS REG: OK={ok_count} | FAIL={fail_count}")
    print("=" * 70)


def main_batch_runner_otptrust(
    num_accs: int = 1, proxy_str: Optional[str] = None, enable_2fa: bool = False, enable_dola: bool = True,
    otptrust_api_key: str = None, service_id: int = 1, provider: str = "outlook",
    resend_times: int = 4, max_workers: int = 1, proxy_file: str = None,
):
    global success_count_global, fail_count_global, _stop_flag
    print_lock = threading.Lock()
    job_counter = {"n": 0}
    job_lock = threading.Lock()
    target_live = max(1, int(num_accs))

    def _plog(msg: str):
        with print_lock:
            print(msg, flush=True)

    def _next_job_no():
        with job_lock:
            job_counter["n"] += 1
            return job_counter["n"]

    def _worker(thread_idx, proxy_pool, fallback_proxy):
        global success_count_global, fail_count_global, _stop_flag
        ok_local = 0
        fail_local = 0
        _plog(f"[L{thread_idx}] sẵn sàng — mục tiêu {target_live} acc LIVE")
        while not _stop_flag:
            with COUNTER_LOCK:
                if success_count_global >= target_live:
                    break
            job_no = _next_job_no()
            px = proxy_pool.next() if (proxy_pool and len(proxy_pool) > 0) else fallback_proxy
            with COUNTER_LOCK:
                cur_ok = success_count_global
            _plog(f"[L{thread_idx}] ===== Lần thử #{job_no} | live {cur_ok}/{target_live} | px={px or 'DIRECT'} =====")
            try:
                success = run_one_account_otptrust(
                    proxy_str=px, enable_2fa=enable_2fa, enable_dola=enable_dola,
                    otptrust_api_key=otptrust_api_key, service_id=service_id,
                    provider=provider, resend_times=resend_times, thread_idx=thread_idx,
                )
            except Exception as e:
                success = False
                _plog(f"[L{thread_idx}] Exception: {e}")

            if success:
                ok_local += 1
                with COUNTER_LOCK:
                    success_count_global += 1
                    cur_ok = success_count_global
                    if cur_ok >= target_live:
                        _stop_flag = True
                with print_lock:
                    AppLogger.live_banner(thread_idx, cur_ok, target_live, job_no, extra=f"L-ok={ok_local}")
                if cur_ok >= target_live:
                    with print_lock:
                        AppLogger.live_banner(thread_idx, cur_ok, target_live, job_no, extra=f"ĐÃ ĐỦ {target_live} LIVE")
                    break
            else:
                fail_local += 1
                with COUNTER_LOCK:
                    fail_count_global += 1
                    cur_ok = success_count_global
                _plog(f"[L{thread_idx}] ✗ FAIL thử #{job_no} | live vẫn {cur_ok}/{target_live} | L-ok={ok_local} L-fail={fail_local}")
        _plog(f"[L{thread_idx}] kết thúc: local {ok_local} OK / {fail_local} FAIL")

    _stop_flag = False
    success_count_global = 0
    fail_count_global = 0

    proxies = load_proxies_from_file(proxy_file) if proxy_file else []
    proxy_pool = ProxyFilePool(proxies) if proxies else None
    if proxy_pool:
        print(f"[+] Proxy file: {len(proxy_pool)} proxy")
    elif proxy_str:
        print(f"[+] Proxy chung: {proxy_str}")
    else:
        print("[*] Không proxy")

    workers = max(1, int(max_workers or 1))
    print(f"[+] Luồng: {workers} | Mục tiêu LIVE: {target_live} | FB id={service_id} | {provider}")
    print(f"[+] Chạy đến khi đủ {target_live} acc LIVE (fail không tính, tiếp tục tạo)")
    print("=" * 70)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_worker, i + 1, proxy_pool, proxy_str) for i in range(workers)]
        for f in as_completed(futs):
            try:
                f.result()
            except Exception as e:
                print(f"[!] Worker error: {e}")

    print("\n" + "=" * 70)
    AppLogger.success(f"HOÀN TẤT OTPTRUST: LIVE={success_count_global}/{target_live} | FAIL={fail_count_global} | Tổng thử={job_counter['n']}")
    print("=" * 70)


def main_batch_runner_vietmail(
    num_accs: int = 1, proxy_str: Optional[str] = None, enable_2fa: bool = False, enable_dola: bool = True,
    vietmail_key: str = None, vietmail_base: str = None, resend_times: int = 4,
    max_workers: int = 1, proxy_file: str = None,
):
    global success_count_global, fail_count_global, _stop_flag
    print_lock = threading.Lock()
    job_counter = {"n": 0}
    job_lock = threading.Lock()
    target_live = max(1, int(num_accs))

    def _plog(msg: str):
        with print_lock:
            print(msg, flush=True)

    def _next_job_no():
        with job_lock:
            job_counter["n"] += 1
            return job_counter["n"]

    def _worker(thread_idx, proxy_pool, fallback_proxy):
        global success_count_global, fail_count_global, _stop_flag
        ok_local = 0
        fail_local = 0
        _plog(f"[L{thread_idx}] san sang — muc tieu {target_live} acc LIVE (VietMail)")
        while not _stop_flag:
            with COUNTER_LOCK:
                if success_count_global >= target_live:
                    break
            job_no = _next_job_no()
            px = proxy_pool.next() if (proxy_pool and len(proxy_pool) > 0) else fallback_proxy
            with COUNTER_LOCK:
                cur_ok = success_count_global
            _plog(f"[L{thread_idx}] ===== Lan thu #{job_no} | live {cur_ok}/{target_live} | px={px or 'DIRECT'} =====")
            try:
                success = run_one_account_vietmail(
                    proxy_str=px, enable_2fa=enable_2fa, enable_dola=enable_dola,
                    vietmail_key=vietmail_key, vietmail_base=vietmail_base,
                    resend_times=resend_times, thread_idx=thread_idx,
                )
            except Exception as e:
                success = False
                _plog(f"[L{thread_idx}] Exception: {e}")
            if success:
                ok_local += 1
                with COUNTER_LOCK:
                    success_count_global += 1
                    cur_ok = success_count_global
                    if cur_ok >= target_live:
                        _stop_flag = True
                with print_lock:
                    AppLogger.live_banner(thread_idx, cur_ok, target_live, job_no)
                if cur_ok >= target_live:
                    with print_lock:
                        AppLogger.live_banner(thread_idx, cur_ok, target_live, job_no, extra=f"ĐÃ ĐỦ {target_live} LIVE")
                    break
            else:
                fail_local += 1
                with COUNTER_LOCK:
                    fail_count_global += 1
                _plog(f"[L{thread_idx}] ✗ FAIL thu #{job_no} | live {success_count_global}/{target_live}")
        _plog(f"[L{thread_idx}] ket thuc: {ok_local} OK / {fail_local} FAIL")

    _stop_flag = False
    success_count_global = 0
    fail_count_global = 0

    proxies = load_proxies_from_file(proxy_file) if proxy_file else []
    proxy_pool = ProxyFilePool(proxies) if proxies else None
    if proxy_pool:
        print(f"[+] Proxy file: {len(proxy_pool)} proxy")
    elif proxy_str:
        print(f"[+] Proxy chung: {proxy_str}")
    else:
        print("[*] Khong proxy")

    workers = max(1, int(max_workers or 1))
    print(f"[+] Luong: {workers} | Muc tieu LIVE: {target_live} | VietMail {vietmail_base or VIETMAIL_BASE}")
    print("=" * 70)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_worker, i + 1, proxy_pool, proxy_str) for i in range(workers)]
        for f in as_completed(futs):
            try:
                f.result()
            except Exception as e:
                print(f"[!] Worker error: {e}")

    print("\n" + "=" * 70)
    AppLogger.success(f"HOAN TAT VIETMAIL: LIVE={success_count_global}/{target_live} | FAIL={fail_count_global} | Tong thu={job_counter['n']}")
    print("=" * 70)


def main_batch_runner(num_gmails: int = 1, proxy_str: Optional[str] = None, enable_2fa: bool = False, enable_dola: bool = True, accs_per_gmail: int = 1):
    global MAX_REG_PER_GMAIL
    MAX_REG_PER_GMAIL = accs_per_gmail
    is_single_acc_mode = (accs_per_gmail == 1)

    completed_gmails = 0
    total_acc_created = 0
    max_consecutive_fails = 10

    while completed_gmails < num_gmails:
        email_addr, order_token = get_gmail_from_pool_direct()
        if not email_addr or not order_token:
            AppLogger.error("Không thể thuê được Gmail từ Gmail94. Thử lại sau 5s...")
            time.sleep(5)
            continue

        email_token = f"GMAIL94:{order_token}"
        pool = {}
        if os.path.exists(GMAIL_USAGE_FILE):
            try:
                with open(GMAIL_USAGE_FILE, 'r', encoding='utf-8') as f:
                    pool = json.load(f)
            except Exception:
                pool = {}
        
        gmail_info = pool.get(email_addr, {})
        current_gmail_accs = gmail_info.get('used', 0)
        target_accs_for_this_gmail = accs_per_gmail

        AppLogger.info(f"👉 BẮT ĐẦU VỚI GMAIL [{completed_gmails + 1}/{num_gmails}]: {email_addr} (Mục tiêu: {target_accs_for_this_gmail} Acc)")

        fail_count = 0
        dots = [email_addr] if is_single_acc_mode else generate_4_gmail_dots(email_addr)
        while current_gmail_accs < target_accs_for_this_gmail:
            attempt_idx = current_gmail_accs + 1
            dot_target_email = email_addr if is_single_acc_mode else (dots[current_gmail_accs] if current_gmail_accs < len(dots) else email_addr)
            print(f"\n{'='*70}")
            AppLogger.info(f"TIẾN TRÌNH TẠO ACC [{attempt_idx}/{target_accs_for_this_gmail}] CHO GMAIL: {dot_target_email} (Gốc: {email_addr})")
            AppLogger.info(f"(Đã hoàn thành toàn bộ đợt: {total_acc_created} acc | Gmail hiện tại: {current_gmail_accs}/{target_accs_for_this_gmail})")
            print(f"{'='*70}")

            success = run_one_account_advanced(
                target_email=dot_target_email,
                email_token=email_token,
                proxy_str=proxy_str,
                enable_2fa=enable_2fa,
                enable_dola=enable_dola,
                root_gmail=email_addr,
                swap_email=not is_single_acc_mode
            )
            if success:
                current_gmail_accs += 1
                total_acc_created += 1
                fail_count = 0
                AppLogger.success(f"HOÀN TẤT ACC [{current_gmail_accs}/{target_accs_for_this_gmail}] CHO GMAIL {dot_target_email}!")
            else:
                fail_count += 1
                AppLogger.error(f"ACC THẤT BẠI! Hệ thống kiểm tra trạng thái Gmail...")
                
                pool_check = {}
                if os.path.exists(GMAIL_USAGE_FILE):
                    try:
                        with open(GMAIL_USAGE_FILE, 'r', encoding='utf-8') as f:
                            pool_check = json.load(f)
                    except Exception:
                        pass
                
                if email_addr not in pool_check:
                    AppLogger.warn(f"⚠️ Gmail {email_addr} đã bị loại bỏ! Hệ thống sẽ mua Gmail mới và BẮT ĐẦU LẠI TỪ ĐẦU {target_accs_for_this_gmail} ACC.")
                    break

                if fail_count >= max_consecutive_fails:
                    AppLogger.error(f"Đã đạt giới hạn lỗi liên tiếp ({max_consecutive_fails} lần). Tạm dừng batch runner.")
                    return

            if current_gmail_accs < target_accs_for_this_gmail:
                delay_between = random.uniform(3.0, 5.0)
                AppLogger.wait(f"Nghỉ {delay_between:.1f}s trước khi chuyển sang acc tiếp theo...")
                time.sleep(delay_between)

        if current_gmail_accs >= target_accs_for_this_gmail:
            completed_gmails += 1
            release_gmail_claim(email_addr)
            AppLogger.success(f"🎉 HOÀN THÀNH ĐỦ {target_accs_for_this_gmail} ACC CHO GMAIL [{completed_gmails}/{num_gmails}]: {email_addr}!")
        else:
            release_gmail_claim(email_addr)

    if enable_dola and active_dola_threads:
        while True:
            pending_dola = [t for t in active_dola_threads if t.is_alive()]
            if not pending_dola:
                break
            AppLogger.wait(f"Đang chờ {len(pending_dola)} tiến trình Dola AI ngầm hoàn tất (đang retry cho tới khi thành công hoặc cookie die)...")
            time.sleep(5)

    print("\n" + "="*70)
    AppLogger.success(f"🎉 HOÀN TẤT TOÀN BỘ CHU TRÌNH! Tổng thành công: {total_acc_created} Acc từ {completed_gmails} Gmail.")
    print("="*70)


# ══════════════════════════════════════════════════════════════════════════
#                             __MAIN__
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    AppLogger.banner("🔥 TOOL REG FACEBOOK — GMAIL / SMS / OTPTRUST / VIETMAIL / PSTMMO 🔥", C.BOLD + C.BYELLOW)
    safe_print(color("  ⚡ Moi SDT proxy | SMS | OTPTrust | VietMail | PSTMMO | Dola AI", C.BOLD + C.BWHITE))
    safe_print(color("  ⚡ Hỗ trợ cả Proxy Residential và 4G/5G/WiFi thật (DIRECT)", C.BOLD + C.LIME))
    safe_print(color("=" * 78, C.BGREEN))

    DEFAULT_PROXY = "http://rx9l1256575-region-TH:pwma6u1k@us.arxlabs.io:3010"

    # ================== CHỌN KIỂU MẠNG: PROXY vs 4G/WIFI ==================
    proxy_target, network_mode_label = resolve_network_choice_interactive(default_proxy=DEFAULT_PROXY)
    safe_print("")
    if proxy_target is None:
        AppLogger.success(f"🌐 Mạng: {network_mode_label}")
    else:
        AppLogger.proxy(f"🌐 Mạng: {network_mode_label}")

    safe_print("")
    safe_print(color("-" * 78, C.DGRAY))
    safe_print(color("📌 CHỌN KIỂU REG:", C.BWHITE + C.BOLD))
    safe_print(color("  1. Reg Gmail (moi SDT ao / email — logic cu)", C.GRAY))
    safe_print(color("  2. Reg SMS Codetextnow (moi SDT proxy -> xac minh SDT that)", C.GRAY))
    safe_print(color("  3. Reg Email OTPTrust (moi SDT proxy -> email thue)", C.GRAY))
    safe_print(color("  4. Reg Email VietMail (moi SDT proxy -> mail API)", C.GRAY))
    safe_print(color("  5. VietMail Cleaner — chi /tra don mail cu", C.GRAY))
    safe_print(color("  6. Reg Email PSTMMO (mail.pstmmo.cc — Auto OTP & Refund) <- mặc định", C.LIME))
    mode_input = input(color("[?] Chon (1-6, Enter = 6 PSTMMO): ", C.BWHITE)).strip()
    if mode_input == "1":
        reg_mode = "gmail"
    elif mode_input == "2":
        reg_mode = "sms"
    elif mode_input == "3":
        reg_mode = "otptrust"
    elif mode_input == "4":
        reg_mode = "vietmail"
    elif mode_input == "5":
        reg_mode = "vietmail_clean"
    else:
        reg_mode = "pstmmo"

    enable_2fa_choice = input("\n[?] Bật 2FA API? (y/n, mặc định: n): ").strip().lower()
    enable_2fa_flag = enable_2fa_choice in ("y", "yes", "1", "ok")

    enable_dola_choice = input("\n[?] Tự đăng ký Dola AI? (y/n, mặc định: y): ").strip().lower()
    enable_dola_flag = enable_dola_choice not in ("n", "no", "0")

    if _configure_telegram_interactive():
        try:
            tr = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ Reg FB Tool đã kết nối Telegram"},
                timeout=10,
            )
            if tr.status_code == 200 and (tr.json() or {}).get("ok"):
                AppLogger.success("Telegram test OK")
            else:
                AppLogger.warn(f"Telegram test fail (HTTP {tr.status_code})")
        except Exception as e:
            AppLogger.warn(f"Telegram test lỗi ({type(e).__name__})")

    if reg_mode == "sms":
        print("\n" + color("-" * 72, C.DGRAY))
        print(color("📱 CHẾ ĐỘ REG THẲNG SMS (Codetextnow V6)", C.BGREEN + C.BOLD))
        ct_key_in = input(f"[?] API Key Codetextnow (Enter = mặc định {CODETEXTNOW_API_KEY[:8]}...): ").strip()
        if ct_key_in:
            CODETEXTNOW_API_KEY = ct_key_in
            sms_key = ct_key_in
        else:
            sms_key = CODETEXTNOW_API_KEY

        sms_service_id, sms_service_name = pick_sms_service_interactive(api_key=sms_key)
        print(f"[+] Dịch vụ SMS: {sms_service_name} (id={sms_service_id})")

        resend_in = input("[?] Số lần spam gửi lại OTP Facebook (mặc định 4): ").strip()
        try:
            resend_times = int(resend_in) if resend_in else 4
            if resend_times < 0:
                resend_times = 4
        except ValueError:
            resend_times = 4

        while True:
            n_in = input("\n[?] Số lượng Acc FB muốn tạo bằng SMS: ").strip()
            if not n_in:
                num_acc = 1
                break
            try:
                num_acc = int(n_in)
                if num_acc > 0:
                    break
            except ValueError:
                pass
            print("[-] Nhập số > 0")

        print("\n" + color("=" * 72, C.BGREEN))
        print("📊 CẤU HÌNH SMS REG:")
        print(f"   • Mode:            MỒI SĐT → XÁC MINH SMS THẬT")
        print(f"   • Dịch vụ:         {sms_service_name} ({sms_service_id})")
        print(f"   • Resend OTP FB:   {resend_times} lần")
        print(f"   • Mạng:            {network_mode_label}")
        print(f"   • 2FA:             {'BẬT' if enable_2fa_flag else 'TẮT'}")
        print(f"   • Dola AI:         {'BẬT' if enable_dola_flag else 'TẮT'}")
        print(f"   • Số Acc:          {num_acc}")
        print(color("=" * 72, C.BGREEN))

        main_batch_runner_sms(
            num_accs=num_acc,
            proxy_str=proxy_target,
            enable_2fa=enable_2fa_flag,
            enable_dola=enable_dola_flag,
            sms_service_id=sms_service_id,
            sms_api_key=sms_key,
            resend_times=resend_times,
        )

    elif reg_mode == "otptrust":
        print("\n" + color("-" * 72, C.DGRAY))
        print(color("EMAIL OTPTRUST (moi SDT -> OTP email | da luong)", C.BGREEN + C.BOLD))
        ot_key = input("[?] OTPTrust API Key (Bearer): ").strip()
        if not ot_key:
            print("[-] Thieu API Key OTPTrust. Thoat.")
            raise SystemExit(1)
        OTPTRUST_API_KEY = ot_key

        print("\n[?] Provider email:")
        print("    1. Outlook  2. Hotmail  3. Gmail  4. iCloud  (Enter=1)")
        p_in = input("[?] Provider: ").strip() or "1"
        provider = {"1": "outlook", "2": "hotmail", "3": "gmail", "4": "icloud"}.get(p_in, "outlook")
        svc_id, svc_name, provider = otptrust_resolve_facebook_service(ot_key, provider=provider)
        print(f"[+] Dich vu mac dinh Facebook: {svc_name} (id={svc_id}) | {provider}")

        resend_in = input("[?] So lan resend OTP FB + reorder (mac dinh 4): ").strip()
        try:
            resend_times = int(resend_in) if resend_in else 4
            if resend_times < 0:
                resend_times = 4
        except ValueError:
            resend_times = 4

        while True:
            n_in = input("\n[?] So Acc LIVE can dat: ").strip()
            if not n_in:
                num_acc = 1
                break
            try:
                num_acc = int(n_in)
                if num_acc > 0:
                    break
            except ValueError:
                pass
            print("[-] Nhap so > 0")

        while True:
            w_in = input("[?] So luong song song (Enter=1): ").strip()
            if not w_in:
                max_workers = 1
                break
            try:
                max_workers = int(w_in)
                if max_workers >= 1:
                    break
            except ValueError:
                pass
            print("[-] Nhap so >= 1")

        if proxy_target is None:
            px_file = None
            AppLogger.info("[*] Mode 4G/WiFi: bỏ qua Proxy file.")
        else:
            px_file = _choose_proxy_file()

        print("\n" + color("=" * 72, C.BGREEN))
        print("CAU HINH OTPTRUST DA LUONG:")
        print(f"   Mode:       MOI SDT -> EMAIL OTPTRUST")
        print(f"   Provider:   {provider}")
        print(f"   Dich vu:    {svc_name} ({svc_id}) [Facebook]")
        print(f"   Resend:     {resend_times}")
        print(f"   Luong:      {max_workers} | chay den du {num_acc} LIVE")
        print(f"   Mang:       {network_mode_label}")
        print(f"   Proxy file: {px_file or 'Khong'}")
        print(f"   2FA:        {'BAT' if enable_2fa_flag else 'TAT'}")
        print(f"   Dola:       {'BAT' if enable_dola_flag else 'TAT'}")
        print(color("=" * 72, C.BGREEN))

        main_batch_runner_otptrust(
            num_accs=num_acc,
            proxy_str=proxy_target,
            enable_2fa=enable_2fa_flag,
            enable_dola=enable_dola_flag,
            otptrust_api_key=ot_key,
            service_id=svc_id,
            provider=provider,
            resend_times=resend_times,
            max_workers=max_workers,
            proxy_file=px_file,
        )

    elif reg_mode == "vietmail_clean":
        print("\n" + color("-" * 72, C.DGRAY))
        print(color("VIETMAIL CLEANER — /tra don mail cu", C.BGREEN + C.BOLD))
        _vm_cfg = vietmail_load_config()
        _saved_key = _vm_cfg.get("api_key_b64") or VIETMAIL_API_KEY_B64
        _saved_base = _vm_cfg.get("base_url") or VIETMAIL_BASE
        vk = input(f"[?] API Key B64 (Enter = {_saved_key[:16]}...): ").strip() or _saved_key
        vb = input(f"[?] Base URL (Enter = {_saved_base}): ").strip() or _saved_base
        vietmail_save_config(api_key_b64=vk, base_url=vb)
        client = VietMailClient(api_key_b64=vk, base_url=vb)
        print("[*] Loop /tra den khi sach...")
        n = client.tra_all(max_rounds=100, empty_stop=3)
        print(f"[+] Da tra {n} mail")

    elif reg_mode == "vietmail":
        print("\n" + color("-" * 72, C.DGRAY))
        print(color("VIETMAIL REG (moi SDT -> OTP email)", C.BGREEN + C.BOLD))
        _vm_cfg = vietmail_load_config()
        _saved_key = _vm_cfg.get("api_key_b64") or VIETMAIL_API_KEY_B64
        _saved_base = _vm_cfg.get("base_url") or VIETMAIL_BASE
        print(f"   [saved] key={_saved_key[:16]}... | base={_saved_base}")
        vk = input(f"[?] API Key B64 (Enter = dung key da luu): ").strip()
        if not vk:
            vk = _saved_key
        vb = input(f"[?] Base URL (Enter = {_saved_base}): ").strip() or _saved_base
        vietmail_save_config(api_key_b64=vk, base_url=vb)
        print(f"[+] Da luu config -> {VIETMAIL_CONFIG_FILE}")

        resend_in = input("[?] So lan resend OTP FB (mac dinh 4): ").strip()
        try:
            resend_times = int(resend_in) if resend_in else 4
            if resend_times < 0:
                resend_times = 4
        except ValueError:
            resend_times = 4

        while True:
            n_in = input("\n[?] So Acc LIVE can dat: ").strip()
            if not n_in:
                num_acc = 1
                break
            try:
                num_acc = int(n_in)
                if num_acc > 0:
                    break
            except ValueError:
                pass
            print("[-] Nhap so > 0")

        while True:
            w_in = input("[?] So luong song song (Enter=1): ").strip()
            if not w_in:
                max_workers = 1
                break
            try:
                max_workers = int(w_in)
                if max_workers >= 1:
                    break
            except ValueError:
                pass
            print("[-] Nhap so >= 1")

        if proxy_target is None:
            px_file = None
            AppLogger.info("[*] Mode 4G/WiFi: bỏ qua Proxy file.")
        else:
            px_file = _choose_proxy_file()

        print("\n" + color("=" * 72, C.BGREEN))
        print("CAU HINH VIETMAIL REG:")
        print(f"   Mode:     MOI SDT -> VIETMAIL")
        print(f"   Base:     {vb}")
        print(f"   Resend:   {resend_times}")
        print(f"   Luong:    {max_workers} | LIVE target {num_acc}")
        print(f"   Mang:     {network_mode_label}")
        print(f"   Proxy file: {px_file or 'Khong'}")
        print(color("=" * 72, C.BGREEN))

        main_batch_runner_vietmail(
            num_accs=num_acc,
            proxy_str=proxy_target,
            enable_2fa=enable_2fa_flag,
            enable_dola=enable_dola_flag,
            vietmail_key=vk,
            vietmail_base=vb,
            resend_times=resend_times,
            max_workers=max_workers,
            proxy_file=px_file,
        )

    elif reg_mode == "pstmmo":
        print("\n" + color("-" * 72, C.DGRAY))
        print(color("📧 CHẾ ĐỘ REG EMAIL PSTMMO (https://mail.pstmmo.cc)", C.BGREEN + C.BOLD))
        _pst_cfg = pstmmo_load_config()
        _saved_key = _pst_cfg.get("api_key") or PSTMMO_API_KEY
        _saved_dom = _pst_cfg.get("domain") or ""

        pk = input(f"[?] API Key PSTMMO (Enter = dùng key đã lưu {_saved_key[:14]}...): ").strip() or _saved_key
        pst_client = PSTMMOEmail(api_key=pk)

        ok_u, u_info = pst_client.get_user_info()
        if ok_u:
            bal_fmt = u_info.get("balance_formatted") or u_info.get("balance")
            uname = u_info.get("username") or u_info.get("email") or "User"
            AppLogger.success(f"[PSTMMO] Tài khoản: {uname} | Số dư: {bal_fmt}")
        else:
            AppLogger.warn(f"[PSTMMO] Không kiểm tra được số dư: {u_info}")

        ref_prices = {
            "gmail.com": "1.232 đ",
            "gmx.com": "53 đ",
            "mail.com": "53 đ",
            "email.com": "53 đ",
            "hotmail.com": "53 đ",
            "outlook.com": "53 đ",
            "icloud.com": "352 đ",
            "yandex.com": "176 đ",
            "yandex.ru": "176 đ",
            "ya.ru": "176 đ",
            "gmx.ru": "53 đ",
            "gmx.se": "53 đ",
            "yandex.fi": "176 đ",
            "yandex.ee": "176 đ",
            "yandex.kg": "176 đ",
            "yandex.tm": "176 đ",
            "yandex.com.ge": "176 đ",
            "yandex.by": "176 đ",
            "yandex.lt": "176 đ",
            "yandex.co.il": "176 đ",
            "yandex.com.am": "176 đ",
            "yandex.uz": "176 đ",
            "yandex.fr": "176 đ",
            "yandex.tj": "176 đ",
            "yandex.az": "176 đ",
            "yandex.pl": "176 đ",
            "yandex.kz": "176 đ",
            "yandex.md": "176 đ",
        }

        ok_s, svcs = pst_client.get_services()
        fb_domains = []
        fb_price_str = "53 đ"
        if ok_s and isinstance(svcs, list):
            for s in svcs:
                if str(s.get("code") or "").lower() == "facebook" or "facebook" in str(s.get("site") or "").lower():
                    fb_domains = s.get("supported_domains") or []
                    fb_price_str = str(s.get("price_formatted") or s.get("price") or "53 đ")
                    print(f"[+] Kho Facebook: {s.get('available_quantity', 0):,} mail | Giá cơ bản: {fb_price_str}")
                    break

        domain_catalog = []
        for d in fb_domains:
            d_clean = str(d).strip().lower()
            if d_clean and d_clean not in domain_catalog:
                domain_catalog.append(d_clean)
        for d in ref_prices.keys():
            if d not in domain_catalog:
                domain_catalog.append(d)

        print("\n" + color("-" * 72, C.DGRAY))
        print(color("📌 BẢNG CHỌN ĐUÔI EMAIL PSTMMO:", C.BYELLOW + C.BOLD))
        print(f"  {color(' 0.', C.LIME)} {'AUTO (Tự chọn đuôi sẵn hàng nhất)':<34} | Khuyên dùng")
        for idx, dom in enumerate(domain_catalog, 1):
            p_label = ref_prices.get(dom, fb_price_str)
            in_api_tag = " [Sẵn kho FB]" if dom in fb_domains else ""
            saved_tag = " <- đang lưu" if dom == _saved_dom else ""
            print(f"  {idx:>2}. @{dom:<20} {p_label:>10}/mail{in_api_tag}{saved_tag}")
        print(color("-" * 72, C.DGRAY))

        default_label = f"@{_saved_dom}" if _saved_dom else "0 = AUTO"
        dom_in = input(color(f"[?] Nhập số thứ tự (0-{len(domain_catalog)}) hoặc tên đuôi (Enter = {default_label}): ", C.BWHITE + C.BOLD)).strip()

        if not dom_in:
            chosen_domain = _saved_dom
        elif dom_in in ("0", "-", "auto", "AUTO"):
            chosen_domain = ""
        elif dom_in.isdigit() and 1 <= int(dom_in) <= len(domain_catalog):
            chosen_domain = domain_catalog[int(dom_in) - 1]
        else:
            chosen_domain = dom_in.lstrip("@").lower()

        if chosen_domain:
            AppLogger.success(f"Đã chọn thuê đuôi: @{chosen_domain}")
        else:
            AppLogger.success("Đã chọn chế độ: AUTO (Hệ thống tự cấp đuôi sẵn hàng nhất)")

        pstmmo_save_config(api_key=pk, domain=chosen_domain)

        resend_in = input("[?] Số lần resend OTP FB (mặc định 4): ").strip()
        try:
            resend_times = int(resend_in) if resend_in else 4
            if resend_times < 0:
                resend_times = 4
        except ValueError:
            resend_times = 4

        while True:
            n_in = input("\n[?] Số Acc LIVE cần đạt: ").strip()
            if not n_in:
                num_acc = 1
                break
            try:
                num_acc = int(n_in)
                if num_acc > 0:
                    break
            except ValueError:
                pass
            print("[-] Nhập số > 0")

        while True:
            w_in = input("[?] Số luồng song song (Enter=1): ").strip()
            if not w_in:
                max_workers = 1
                break
            try:
                max_workers = int(w_in)
                if max_workers >= 1:
                    break
            except ValueError:
                pass
            print("[-] Nhập số >= 1")

        if proxy_target is None:
            px_file = None
            AppLogger.info("[*] Mode 4G/WiFi: bỏ qua Proxy file.")
        else:
            px_file = _choose_proxy_file()

        print("\n" + color("=" * 72, C.BGREEN))
        print("📊 CẤU HÌNH PSTMMO REG:")
        print(f"   • Mode:       MỒI SĐT -> EMAIL PSTMMO (mail.pstmmo.cc)")
        print(f"   • Domain:     {('@' + chosen_domain) if chosen_domain else 'Tự chọn sẵn hàng (Auto)'}")
        print(f"   • Resend:     {resend_times} lần")
        print(f"   • Luồng:      {max_workers} | Mục tiêu LIVE: {num_acc}")
        print(f"   • Mạng:       {network_mode_label}")
        print(f"   • Proxy file: {px_file or 'Không'}")
        print(f"   • 2FA:        {'BẬT' if enable_2fa_flag else 'TẮT'}")
        print(f"   • Dola AI:    {'BẬT' if enable_dola_flag else 'TẮT'}")
        print(color("=" * 72, C.BGREEN))

        main_batch_runner_pstmmo(
            num_accs=num_acc,
            proxy_str=proxy_target,
            enable_2fa=enable_2fa_flag,
            enable_dola=enable_dola_flag,
            pstmmo_key=pk,
            pstmmo_domain=chosen_domain,
            resend_times=resend_times,
            max_workers=max_workers,
            proxy_file=px_file,
        )

    else:
        gmail94_input = input(f"\n[?] Key Gmail94 (Enter = mặc định {GMAIL94_TOKEN[:10]}...): ").strip()
        if gmail94_input:
            GMAIL94_TOKEN = gmail94_input
            print(f"[+] Gmail94: {GMAIL94_TOKEN[:10]}...")
        else:
            print(f"[+] Gmail94 mặc định")

        print("\n" + color("-" * 72, C.DGRAY))
        print(color("📌 CHẾ ĐỘ GMAIL:", C.BWHITE + C.BOLD))
        print("    1. 1 Gmail = 1 Acc (giữ Gmail)")
        print("    2. 1 Gmail = 4 Acc (dot + đá email ảo)")
        mode_reg_input = input("[?] (1/2, Enter=1): ").strip()
        if mode_reg_input == "2":
            accs_per_gmail_choice = 4
            mode_desc = "1 GMAIL = 4 ACC"
        else:
            accs_per_gmail_choice = 1
            mode_desc = "1 GMAIL = 1 ACC"
        print(f"[+] {mode_desc}")

        while True:
            num_gmail_input = input(f"\n[?] Số Gmail thuê (mỗi Gmail = {accs_per_gmail_choice} Acc): ").strip()
            if not num_gmail_input:
                num_gmail = 1
                break
            try:
                num_gmail = int(num_gmail_input)
                if num_gmail > 0:
                    break
            except ValueError:
                pass
            print("[-] Nhập số > 0")

        total_accs = num_gmail * accs_per_gmail_choice
        print("\n" + color("=" * 72, C.BGREEN))
        print("📊 CẤU HÌNH GMAIL REG:")
        print(f"   • Mode:   {mode_desc}")
        print(f"   • Mạng:   {network_mode_label}")
        print(f"   • 2FA:    {'BẬT' if enable_2fa_flag else 'TẮT'}")
        print(f"   • Dola:   {'BẬT' if enable_dola_flag else 'TẮT'}")
        print(f"   • Gmail:  {num_gmail} → {total_accs} Acc FB")
        print(color("=" * 72, C.BGREEN))

        main_batch_runner(
            num_gmails=num_gmail,
            proxy_str=proxy_target,
            enable_2fa=enable_2fa_flag,
            enable_dola=enable_dola_flag,
            accs_per_gmail=accs_per_gmail_choice,
        )
# ══════════════════════════════════════════════════════════════════════════
#                          END OF FILE
# ══════════════════════════════════════════════════════════════════════════
