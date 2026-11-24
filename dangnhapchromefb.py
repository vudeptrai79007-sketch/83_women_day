# ==================== 1. CẤU HÌNH CONSOLE & SHIM PYTHON 3.12+ ====================
import os
import sys
import types
import re

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        os.system("")  # Kích hoạt hỗ trợ màu ANSI trên Windows CMD
    except Exception:
        pass

if "distutils" not in sys.modules:
    distutils_mod = types.ModuleType("distutils")
    distutils_version_mod = types.ModuleType("distutils.version")

    class LooseVersion:
        def __init__(self, vstring=None):
            if vstring:
                self.parse(vstring)

        def parse(self, vstring):
            self.vstring = vstring
            component_re = re.compile(r"(\d+)")
            self.version = [
                int(x) if x.isdigit() else x
                for x in component_re.split(vstring)
                if x and x != "."
            ]

        def __lt__(self, other): return self.version < (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __le__(self, other): return self.version <= (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __eq__(self, other): return self.version == (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __ne__(self, other): return self.version != (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __gt__(self, other): return self.version > (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __ge__(self, other): return self.version >= (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __str__(self): return self.vstring
        def __repr__(self): return f"LooseVersion ('{self.vstring}')"

    distutils_version_mod.LooseVersion = LooseVersion
    distutils_mod.version = distutils_version_mod
    sys.modules["distutils"] = distutils_mod
    sys.modules["distutils.version"] = distutils_version_mod

# ==================== 2. IMPORT THƯ VIỆN ====================
import time
import hmac
import struct
import hashlib
import socket
import select
import base64
import threading
from urllib.parse import quote

try:
    import requests
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Đang cài đặt thư viện còn thiếu (undetected-chromedriver, selenium, requests)...")
    os.system(f'"{sys.executable}" -m pip install undetected-chromedriver selenium requests')
    import requests
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

# ==================== 3. KHÓA ĐA LUỒNG & BẢNG MÀU ANSI ====================
STOP_EVENT = threading.Event()
BROWSER_LOCK = threading.Lock()
DRIVER_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()
FILE_LOCK = threading.Lock()

ALL_DRIVERS = []        # Lưu (tab_name, driver, forwarder)
TAB_ACCOUNTS = {}       # Lưu thông tin account theo tab_name để xuất file chuẩn định dạng
EXTRACTED_COOKIES = []  # Lưu danh sách (tab_name, c_user, cookie_str) đã trích xuất

FB_LOGIN_URL = "https://www.facebook.com/login/"
COOKIE_OUTPUT_FILE = "fb_cookies_live.txt"

built_in_print = print
PAUSE_FOR_INPUT = threading.Event()
PAUSE_FOR_INPUT.set()


def thread_safe_print(*args, **kwargs):
    PAUSE_FOR_INPUT.wait()
    with PRINT_LOCK:
        built_in_print(*args, **kwargs)


print = thread_safe_print


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
    RESET = "\033[0m"

    @staticmethod
    def color_text(text, color):
        return f"{color}{text}{Colors.RESET}"


def banner():
    os.system("clear" if os.name == "posix" else "cls")
    built_in_print(f"""{Colors.PRIMARY}
 ██████╗ ██╗  ██╗██████╗  ██████╗ ███╗   ███╗███████╗
██╔════╝ ██║  ██║██╔══██╗██╔═══██╗████╗ ████║██╔════╝
██║  ███╗███████║██████╔╝██║   ██║██╔████╔██║█████╗  
██║   ██║██╔══██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══╝  
╚██████╔╝██║  ██║██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
{Colors.RESET}""")
    built_in_print(f"{Colors.INFO}Chrome Ẩn Danh + Proxy Forwarder + Auto Login FB + Auto Lấy UID & Cookie{Colors.RESET}")
    built_in_print(f"{Colors.LINE}{'─' * 78}{Colors.RESET}\n")


# ==================== 4. TÁCH ĐỊNH DẠNG TÀI KHOẢN & TẠO MÃ 2FA ====================
def _looks_like_2fa_secret(val):
    """Kiểm tra chuỗi có giống mã bí mật 2FA (Base32, >= 16 ký tự, có chữ cái) không."""
    if not val:
        return False
    clean = re.sub(r"[\s\-]+", "", str(val)).upper()
    return (
        len(clean) >= 16
        and any(c.isalpha() for c in clean)
        and bool(re.fullmatch(r"[A-Z2-7]+=*", clean))
    )


def _strip_field_label(val):
    """Loại bỏ nhãn tiền tố nếu người dùng dán dạng 'SĐT: +84... | MK: ... | 2FA: ...'."""
    return re.sub(
        r"^(?:tk|tài\s*khoản|tai\s*khoan|uid|user(?:name)?|email|mail|sđt|sdt|phone|mk|mật\s*khẩu|mat\s*khau|pass(?:word)?|2fa|fa|otp)\s*[:=]\s*",
        "",
        str(val).strip(),
        flags=re.IGNORECASE,
    ).strip()


def _normalize_login_id(raw_id):
    """Chuẩn hóa đầu vào đăng nhập (SĐT có dấu +, Email, UID) và trả về (value, id_type)."""
    val = _strip_field_label(raw_id)
    if "@" in val:
        return val, "Email"

    if val.startswith("+") or re.fullmatch(r"[\d\s\-().]{7,22}", val):
        has_plus = val.startswith("+")
        digits = re.sub(r"\D", "", val)
        if has_plus and 7 <= len(digits) <= 15:
            return f"+{digits}", "SĐT"
        if not has_plus and len(digits) in (9, 10, 11) and digits.startswith("0"):
            return digits, "SĐT"
        if not has_plus and digits:
            return digits, "UID"

    return val, "TK"


def _looks_like_identifier(val):
    """Kiểm tra token đầu tiên có phải là Email, SĐT (có/không dấu +), UID hoặc username hợp lệ không."""
    v = str(val).strip()
    if not v or " " in v:
        return False
    if "@" in v:
        return True
    if v.startswith("+") and re.fullmatch(r"\+\d{7,15}", v):
        return True
    if v.isdigit() and len(v) >= 6:
        return True
    return bool(re.fullmatch(r"[A-Za-z0-9._\-]{4,}", v))


def parse_account(raw_line):
    """
    Tự nhận diện đa định dạng đầu vào:
    - +84912345678|mk|2fa  hoặc  +84 912 345 678|mk|2fa
    - email@gmail.com|mk|2fa|...
    - uid|mk|2fa|cookie|mail|...
    - +84912345678:mk:2fa  hoặc  email@gmail.com:mk:2fa
    - Tách bằng: |  ;  Tab  :  hoặc khoảng trắng
    """
    if not raw_line:
        return None
    line = str(raw_line).strip()
    if not line:
        return None

    parts = []
    if "|" in line:
        parts = [_strip_field_label(p) for p in line.split("|") if p.strip()]
    elif "\t" in line:
        parts = [_strip_field_label(p) for p in line.split("\t") if p.strip()]
    elif ";" in line:
        parts = [_strip_field_label(p) for p in line.split(";") if p.strip()]
    elif ":" in line and not line.lower().startswith(("http://", "https://")):
        colon_parts = [p.strip() for p in line.split(":") if p.strip()]
        if len(colon_parts) >= 2 and _looks_like_identifier(colon_parts[0]):
            parts = colon_parts

    if not parts:
        tokens = line.split()
        if not tokens:
            return None

        if tokens[0].startswith("+"):
            first_digits = re.sub(r"\D", "", tokens[0])
            if len(first_digits) < 8:
                merged_phone = [tokens[0]]
                total_digits = len(first_digits)
                idx = 1
                while idx < len(tokens) and re.fullmatch(r"[\d\-().]+", tokens[idx]):
                    d_len = len(re.sub(r"\D", "", tokens[idx]))
                    if total_digits + d_len > 15:
                        break
                    merged_phone.append(tokens[idx])
                    total_digits += d_len
                    idx += 1
                    if total_digits >= 10:
                        break
                tokens = ["".join(merged_phone)] + tokens[idx:]

        if len(tokens) >= 3:
            tail = "".join(tokens[2:])
            if _looks_like_2fa_secret(tail):
                parts = [tokens[0], tokens[1], tail]
            else:
                parts = tokens
        else:
            parts = tokens

    if len(parts) < 2:
        return None

    username, id_type = _normalize_login_id(parts[0])
    password = _strip_field_label(parts[1])
    twofa = None

    if len(parts) >= 3:
        for candidate in parts[2:]:
            cand_clean = _strip_field_label(candidate)
            if _looks_like_2fa_secret(cand_clean):
                twofa = re.sub(r"[\s\-]+", "", cand_clean).upper()
                break
        if not twofa and len(parts) == 3:
            cand_clean = _strip_field_label(parts[2])
            twofa = re.sub(r"[\s\-]+", "", cand_clean).upper()

    return {
        "user": username,
        "id_type": id_type,
        "pass": password,
        "twofa": twofa,
    }


def generate_totp(secret, interval=30, digits=6):
    """Sinh mã 2FA 6 số chuẩn TOTP (RFC 6238) không cần thư viện ngoài."""
    clean_secret = re.sub(r"[^A-Za-z2-7]", "", str(secret)).upper()
    if not clean_secret:
        return None, 0

    padding = (-len(clean_secret)) % 8
    key = base64.b32decode(clean_secret + ("=" * padding), casefold=True)

    now = int(time.time())
    remaining = interval - (now % interval)
    counter = now // interval

    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    code = str(code_int % (10 ** digits)).zfill(digits)
    return code, remaining


def load_accounts_from_input(raw_input):
    raw_input = raw_input.strip().strip('"').strip("'")
    if not raw_input:
        return []
    if os.path.isfile(raw_input):
        with open(raw_input, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    else:
        lines = [line.strip() for line in raw_input.splitlines() if line.strip()]

    accounts = []
    for line in lines:
        parsed = parse_account(line)
        if parsed:
            accounts.append(parsed)
    return accounts


# ==================== 5. TRÍCH XUẤT UID & COOKIE (POLLING 15S) ====================
def extract_uid_and_cookie(driver, tab_name):
    """
    Trích xuất UID và Cookie (Polling trong 15s để Facebook kịp ghi nhận cookie).
    Trả về tuple (c_user, cookie_str).
    """
    print(Colors.color_text(f"[{tab_name}] Đang trích xuất UID và Cookie (tối đa 15s)...", Colors.INFO))
    c_user = ""
    cookie_str = ""

    for check_idx in range(15):
        if STOP_EVENT.is_set():
            break
        try:
            cookies = driver.get_cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
            c_user = cookie_dict.get("c_user", "")
            if c_user:
                break

            cur_url = driver.current_url.lower()
            # TUYỆT ĐỐI không lấy id từ URL nếu vẫn còn đang ở trang confirmemail.php
            if "confirm" not in cur_url and "checkpoint" not in cur_url and "login" not in cur_url:
                m = re.search(r"id=(\d+)", driver.current_url)
                if m:
                    c_user = m.group(1)
                    break

            if "xs" in cookie_dict and "confirm" not in cur_url:
                c_user = f"fb_{int(time.time())}"
                break

            # Nếu sau 5 giây chưa thấy c_user và không còn ở trang confirm, mở facebook.com để đồng bộ session
            if check_idx == 5 and "confirm" not in cur_url:
                try:
                    driver.get("https://www.facebook.com/")
                except Exception:
                    pass
        except Exception:
            pass

        time.sleep(1)

    return c_user, cookie_str


def save_extracted_cookie(tab_name, c_user, cookie_str, account=None):
    """Lưu kết quả UID|PASS|2FA|COOKIE ra file an toàn đa luồng và in ra console."""
    if not c_user:
        print(Colors.color_text(
            f"[{tab_name}] Không trích xuất được UID (c_user) sau 15 giây!",
            Colors.WARNING,
        ))
        return False

    pwd = account.get("pass", "") if account else ""
    twofa = (account.get("twofa") or "") if account else ""
    record_line = f"{c_user}|{pwd}|{twofa}|{cookie_str}"

    with FILE_LOCK:
        with open(COOKIE_OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(record_line + "\n")
        EXTRACTED_COOKIES.append((tab_name, c_user, cookie_str))

    print(Colors.color_text(f"[{tab_name}] LẤY UID & COOKIE THÀNH CÔNG!", Colors.SUCCESS))
    print(Colors.color_text(f"[{tab_name}] UID   : {c_user}", Colors.VALUE))
    print(Colors.color_text(f"[{tab_name}] Cookie: {cookie_str}", Colors.KEY))
    print(Colors.color_text(f"[{tab_name}] Đã lưu vào file: {COOKIE_OUTPUT_FILE}", Colors.INFO))
    return True


# ==================== 6. TỰ ĐỘNG ĐĂNG NHẬP FACEBOOK & NHẬP 2FA ====================
def _safe_type(driver, element, text):
    """Điền văn bản an toàn, đảm bảo giữ nguyên dấu '+', '@' và ký tự đặc biệt."""
    mod_key = Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL
    element.click()
    element.send_keys(mod_key, "a")
    element.send_keys(Keys.BACKSPACE)
    element.send_keys(text)
    if (element.get_attribute("value") or "") != text:
        driver.execute_script(
            """
            const el = arguments[0];
            const val = arguments[1];
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            element,
            text,
        )


def _dismiss_cookie_popup(driver):
    """Đóng thông báo Cookie của Facebook nếu dùng Proxy EU/US."""
    xpaths = [
        "//button[contains(., 'Allow all cookies') or contains(., 'Accept All') or contains(., 'Cho phép tất cả')]",
        "//div[@role='button' and (contains(., 'Allow all cookies') or contains(., 'Cho phép tất cả'))]",
        "//button[@data-cookiebanner='accept_button']",
    ]
    for xp in xpaths:
        try:
            btns = driver.find_elements(By.XPATH, xp)
            for b in btns:
                if b.is_displayed():
                    b.click()
                    time.sleep(0.8)
                    return
        except Exception:
            pass


def _find_visible_2fa_input(driver):
    """Tìm ô nhập mã 6 số trên cả giao diện Checkpoint cũ và 2FA mới của Facebook."""
    selectors = [
        (By.NAME, "approvals_code"),
        (By.CSS_SELECTOR, "input[autocomplete='one-time-code']"),
        (By.CSS_SELECTOR, "input[name='code']"),
    ]
    for by, sel in selectors:
        try:
            elems = driver.find_elements(by, sel)
            for el in elems:
                if el.is_displayed() and el.is_enabled():
                    return el
        except Exception:
            pass

    cur_url = driver.current_url.lower()
    if any(k in cur_url for k in ("two_step_verification", "two_factor", "checkpoint")):
        try:
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='tel'], input[type='number']")
            for el in inputs:
                name_attr = (el.get_attribute("name") or "").lower()
                if name_attr in ("email", "pass", "q"):
                    continue
                if el.is_displayed() and el.is_enabled():
                    return el
        except Exception:
            pass
    return None


def _switch_to_authenticator_app(driver, tab_name):
    """Nếu FB mặc định yêu cầu duyệt trên thiết bị khác/WhatsApp, tự chuyển sang Ứng dụng xác thực."""
    try:
        try_other_xp = (
            "//*[self::button or self::a or @role='button']"
            "[contains(., 'Try another way') or contains(., 'Thử cách khác')]"
        )
        btns = driver.find_elements(By.XPATH, try_other_xp)
        clicked = False
        for b in btns:
            if b.is_displayed():
                b.click()
                clicked = True
                time.sleep(1.5)
                break
        if not clicked:
            return False

        auth_app_xp = (
            "//*[contains(text(), 'Authentication app') or contains(text(), 'Ứng dụng xác thực')]"
        )
        opts = driver.find_elements(By.XPATH, auth_app_xp)
        for opt in opts:
            if opt.is_displayed():
                opt.click()
                time.sleep(1)
                break

        cont_xp = (
            "//*[self::button or @role='button']"
            "[contains(., 'Continue') or contains(., 'Tiếp tục')]"
        )
        cont_btns = driver.find_elements(By.XPATH, cont_xp)
        for cb in cont_btns:
            if cb.is_displayed():
                cb.click()
                print(Colors.color_text(f"[{tab_name}] Đã chuyển phương thức sang Ứng dụng xác thực.", Colors.INFO))
                time.sleep(2)
                return True
    except Exception:
        pass
    return False


def _click_submit_or_continue(driver):
    """Nhấn nút Tiếp tục / Gửi mã trên màn hình 2FA hoặc lưu trình duyệt."""
    xpaths = [
        "//button[@id='checkpointSubmitButton']",
        "//button[@type='submit']",
        "//*[self::button or @role='button'][contains(., 'Continue') or contains(., 'Tiếp tục') or contains(., 'Submit') or contains(., 'Gửi mã') or contains(., 'Trust this device') or contains(., 'Tin cậy thiết bị')]",
    ]
    for xp in xpaths:
        try:
            btns = driver.find_elements(By.XPATH, xp)
            for b in btns:
                if b.is_displayed() and b.is_enabled():
                    b.click()
                    return True
        except Exception:
            pass
    return False


def _is_fb_logged_in(driver):
    try:
        has_c_user = driver.get_cookie("c_user") is not None
        url = driver.current_url.lower()
        blocked = any(k in url for k in ("login", "checkpoint", "two_step_verification", "two_factor", "confirm"))
        return has_c_user and not blocked
    except Exception:
        return False


def login_facebook(driver, account, tab_name):
    """Thực hiện nhập TK (SĐT +, Email, UID), MK, tự nhập 2FA và trích xuất UID + Cookie."""
    TAB_ACCOUNTS[tab_name] = account
    user = account["user"]
    id_type = account.get("id_type", "TK")
    pwd = account["pass"]
    twofa = account.get("twofa")

    masked_2fa = (twofa[:4] + "..." + twofa[-4:]) if twofa and len(twofa) >= 8 else (twofa or "Không có")
    print(Colors.color_text(
        f"[{tab_name}] Bắt đầu đăng nhập | {id_type}: {user} | 2FA: {masked_2fa}",
        Colors.INFO,
    ))

    try:
        if "facebook.com" not in driver.current_url.lower():
            driver.get(FB_LOGIN_URL)

        _dismiss_cookie_popup(driver)

        wait = WebDriverWait(driver, 15)
        email_input = wait.until(EC.visibility_of_element_located((By.NAME, "email")))
        pass_input = wait.until(EC.visibility_of_element_located((By.NAME, "pass")))

        _safe_type(driver, email_input, user)
        time.sleep(0.3)

        _safe_type(driver, pass_input, pwd)
        time.sleep(0.3)

        try:
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[name='login'], #loginbutton, button[type='submit']")
            login_btn.click()
        except Exception:
            pass_input.send_keys(Keys.RETURN)

        print(Colors.color_text(f"[{tab_name}] Đã điền {id_type}/MK, đang chờ phản hồi từ Facebook...", Colors.INFO))

        twofa_submitted = False
        switched_method = False
        deadline = time.time() + 25

        while time.time() < deadline:
            if STOP_EVENT.is_set():
                return False
            time.sleep(1.2)

            if _is_fb_logged_in(driver):
                print(Colors.color_text(f"[{tab_name}] ĐĂNG NHẬP FACEBOOK THÀNH CÔNG! ({user})", Colors.SUCCESS))
                c_user, cookie_str = extract_uid_and_cookie(driver, tab_name)
                save_extracted_cookie(tab_name, c_user, cookie_str, account)
                return True

            cur_url = driver.current_url.lower()

            if not twofa_submitted:
                code_input = _find_visible_2fa_input(driver)

                if not code_input and not switched_method and "two_step_verification" in cur_url:
                    switched_method = True
                    _switch_to_authenticator_app(driver, tab_name)
                    code_input = _find_visible_2fa_input(driver)

                if code_input:
                    if not twofa:
                        print(Colors.color_text(
                            f"[{tab_name}] Facebook yêu cầu 2FA nhưng tài khoản không có mã 2FA!",
                            Colors.WARNING,
                        ))
                        return False

                    otp, remaining = generate_totp(twofa)
                    if not otp:
                        print(Colors.color_text(f"[{tab_name}] Mã bí mật 2FA không hợp lệ!", Colors.ERROR))
                        return False

                    if remaining <= 3:
                        print(Colors.color_text(
                            f"[{tab_name}] Mã 2FA sắp hết hạn ({remaining}s), chờ lấy mã mới...",
                            Colors.WARNING,
                        ))
                        time.sleep(remaining + 1)
                        otp, remaining = generate_totp(twofa)

                    print(Colors.color_text(
                        f"[{tab_name}] Đã tạo mã 2FA: {otp} (còn {remaining}s) -> Đang nhập...",
                        Colors.SUCCESS,
                    ))

                    _safe_type(driver, code_input, otp)
                    time.sleep(0.5)

                    if not _click_submit_or_continue(driver):
                        code_input.send_keys(Keys.RETURN)

                    twofa_submitted = True
                    deadline = time.time() + 20
                    continue

            if twofa_submitted and any(k in cur_url for k in ("checkpoint", "two_step_verification", "remember_browser")):
                _click_submit_or_continue(driver)

        # Kiểm tra bổ sung bằng polling 15s nếu đã vượt qua trang login/checkpoint nhưng cookie ghi nhận chậm
        final_url = driver.current_url.lower()
        if not any(k in final_url for k in ("login", "checkpoint", "two_step_verification", "two_factor")):
            c_user, cookie_str = extract_uid_and_cookie(driver, tab_name)
            if c_user:
                print(Colors.color_text(f"[{tab_name}] ĐĂNG NHẬP FACEBOOK THÀNH CÔNG! ({user})", Colors.SUCCESS))
                save_extracted_cookie(tab_name, c_user, cookie_str, account)
                return True

        print(Colors.color_text(
            f"[{tab_name}] Chưa vào được trang chủ (có thể sai MK, captcha hoặc checkpoint). URL hiện tại: {driver.current_url}",
            Colors.WARNING,
        ))
        return False

    except Exception as e:
        print(Colors.color_text(f"[{tab_name}] Lỗi khi tự động đăng nhập FB: {e}", Colors.ERROR))
        return False


# ==================== 7. XỬ LÝ PROXY ĐA ĐỊNH DẠNG (IP & DOMAIN) ====================
def _is_valid_port(val):
    return val.isdigit() and 1 <= int(val) <= 65535


def _looks_like_host(val):
    return "." in val or val.lower() == "localhost"


def parse_proxy(proxy_str):
    if not proxy_str:
        return None
    p_str = str(proxy_str).strip()
    if not p_str:
        return None

    for proto in ["http://", "https://", "socks5://", "socks4://"]:
        if p_str.lower().startswith(proto):
            p_str = p_str[len(proto):]
            break

    if "@" in p_str:
        try:
            auth_part, host_part = p_str.rsplit("@", 1)
            u, pwd = auth_part.split(":", 1)
            host, port = host_part.rsplit(":", 1)
            if _is_valid_port(port):
                return {"ip": host.strip(), "port": port.strip(), "user": u.strip(), "pass": pwd.strip()}
        except Exception:
            pass

    parts = [x.strip() for x in p_str.split(":") if x.strip()]
    if len(parts) == 2 and _is_valid_port(parts[1]):
        return {"ip": parts[0], "port": parts[1], "user": None, "pass": None}

    if len(parts) >= 4:
        if _looks_like_host(parts[0]) and _is_valid_port(parts[1]):
            return {
                "ip": parts[0],
                "port": parts[1],
                "user": parts[2],
                "pass": ":".join(parts[3:]),
            }
        if _looks_like_host(parts[-2]) and _is_valid_port(parts[-1]):
            return {
                "ip": parts[-2],
                "port": parts[-1],
                "user": parts[0],
                "pass": ":".join(parts[1:-2]),
            }
        return {
            "ip": parts[0],
            "port": parts[1],
            "user": parts[2],
            "pass": ":".join(parts[3:]),
        }

    return None


# ==================== 8. CHECK LIVE PROXY & LẤY IP ====================
def check_proxy_live(raw_proxy, timeout=10):
    parsed = parse_proxy(raw_proxy)
    if not parsed:
        return False, None, "Sai định dạng proxy"

    host = parsed["ip"]
    port = parsed["port"]
    user = parsed.get("user")
    pwd = parsed.get("pass")

    if user and pwd:
        proxy_url = f"http://{quote(user, safe='')}:{quote(pwd, safe='')}@{host}:{port}"
    else:
        proxy_url = f"http://{host}:{port}"

    proxies = {"http": proxy_url, "https": proxy_url}
    endpoints = [
        "https://ipinfo.io/json",
        "https://api.ipify.org?format=json",
    ]

    last_error = "Không kết nối được"
    start_t = time.time()

    for url in endpoints:
        try:
            resp = requests.get(url, proxies=proxies, timeout=timeout)
            latency_ms = int((time.time() - start_t) * 1000)

            if resp.status_code == 200:
                data = resp.json()
                ip = data.get("ip") or data.get("query")
                if ip:
                    return True, {
                        "ip": ip,
                        "country": data.get("country", "N/A"),
                        "city": data.get("city", ""),
                        "latency_ms": latency_ms,
                    }, ""
            elif resp.status_code == 407:
                return False, None, "Lỗi 407: Sai User/Pass hoặc proxy hết hạn"
            else:
                last_error = f"HTTP {resp.status_code}"

        except requests.exceptions.ProxyError as e:
            if "407" in str(e):
                return False, None, "Lỗi 407: Sai User/Pass hoặc chưa whitelist IP"
            last_error = "Proxy từ chối kết nối (sai giao thức HTTP/SOCKS5 hoặc die)"
        except requests.exceptions.ConnectTimeout:
            last_error = f"Quá thời gian kết nối ({timeout}s)"
        except requests.exceptions.ReadTimeout:
            last_error = f"Proxy phản hồi quá chậm (hơn {timeout}s)"
        except Exception as e:
            last_error = str(e)

    return False, None, last_error


# ==================== 9. CẦU NỐI PROXY LOCAL CHO TAB ẨN DANH ====================
class LocalProxyForwarder:
    def __init__(self, remote_ip, remote_port, username=None, password=None):
        self.remote_ip = remote_ip
        self.remote_port = int(remote_port)
        self.username = username
        self.password = password

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("127.0.0.1", 0))
        self.local_port = self.server_socket.getsockname()[1]

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.server_socket.listen(100)
        while self.running:
            try:
                client_sock, _ = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client, args=(client_sock,), daemon=True
                ).start()
            except Exception:
                break

    def _handle_client(self, client_sock):
        remote_sock = None
        try:
            crlf2 = b"\r\n\r\n"
            crlf = b"\r\n"
            req = b""
            while crlf2 not in req:
                chunk = client_sock.recv(4096)
                if not chunk:
                    return
                req += chunk

            header_part, rest = req.split(crlf2, 1)
            lines = header_part.split(crlf)
            first_line = lines[0].decode("utf-8", "ignore")
            is_connect = first_line.startswith("CONNECT")

            remote_sock = socket.create_connection((self.remote_ip, self.remote_port), timeout=15)

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
                    if not c:
                        break
                    resp += c

                resp_first_line = resp.split(crlf)[0] if resp else b""
                if b"200" in resp_first_line:
                    client_sock.sendall(b"HTTP/1.1 200 Connection established" + crlf2)
                else:
                    client_sock.sendall(resp)
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
                if not r:
                    break
                for s in r:
                    other = remote_sock if s is client_sock else client_sock
                    data = s.recv(16384)
                    if not data:
                        return
                    other.sendall(data)
        except Exception:
            pass
        finally:
            try:
                client_sock.close()
            except Exception:
                pass
            if remote_sock:
                try:
                    remote_sock.close()
                except Exception:
                    pass

    def close(self):
        self.running = False
        try:
            self.server_socket.close()
        except Exception:
            pass


# ==================== 10. KHỞI TẠO & ĐÓNG CHROME ẨN DANH ====================
def create_chrome_driver(thread_idx=0, raw_proxy=None, win_width=460, win_height=520, columns=4, scale=0.65):
    tab_name = f"Tab-{thread_idx + 1}"
    col = thread_idx % columns
    row = thread_idx // columns
    x_pos = col * win_width
    y_pos = row * win_height

    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-save-password-bubble")
    options.add_argument("--password-store=basic")
    options.add_argument(f"--window-size={win_width},{win_height}")
    options.add_argument(f"--window-position={x_pos},{y_pos}")
    options.add_argument(f"--force-device-scale-factor={scale}")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
        "autofill.profile_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
    }
    options.add_experimental_option("prefs", prefs)

    forwarder = None
    if raw_proxy:
        parsed_p = parse_proxy(raw_proxy)
        if parsed_p:
            if parsed_p.get("user") and parsed_p.get("pass"):
                forwarder = LocalProxyForwarder(
                    parsed_p["ip"], parsed_p["port"],
                    parsed_p["user"], parsed_p["pass"],
                )
                options.add_argument(f"--proxy-server=http://127.0.0.1:{forwarder.local_port}")
                print(Colors.color_text(
                    f"[{tab_name}] Đã gán Proxy (User/Pass): {parsed_p['ip']}:{parsed_p['port']} -> Local:{forwarder.local_port}",
                    Colors.WARNING,
                ))
            else:
                options.add_argument(f"--proxy-server=http://{parsed_p['ip']}:{parsed_p['port']}")
                print(Colors.color_text(
                    f"[{tab_name}] Đã gán Proxy (IP:Port): {parsed_p['ip']}:{parsed_p['port']}",
                    Colors.WARNING,
                ))

    with BROWSER_LOCK:
        driver = uc.Chrome(options=options)
        with DRIVER_LOCK:
            ALL_DRIVERS.append((tab_name, driver, forwarder))
        try:
            driver.set_window_size(win_width, win_height)
            driver.set_window_position(x_pos, y_pos)
        except Exception:
            pass
        time.sleep(1)

    return driver, forwarder


def open_chrome_safe(thread_idx=0, raw_proxy=None, check_live=True, timeout=10):
    tab_name = f"Tab-{thread_idx + 1}"

    if raw_proxy and check_live:
        print(Colors.color_text(f"[{tab_name}] Đang kiểm tra Proxy...", Colors.INFO))
        is_live, info, err = check_proxy_live(raw_proxy, timeout=timeout)
        if not is_live:
            print(Colors.color_text(f"[{tab_name}] PROXY DIE ({err}) -> Bỏ qua mở Chrome!", Colors.ERROR))
            return None, None

        loc = f"{info['country']}" + (f" - {info['city']}" if info["city"] else "")
        print(Colors.color_text(
            f"[{tab_name}] PROXY LIVE | IP: {info['ip']} | Khu vực: {loc} | Ping: {info['latency_ms']}ms",
            Colors.SUCCESS,
        ))

    return create_chrome_driver(thread_idx=thread_idx, raw_proxy=raw_proxy)


def close_chrome_driver(driver, forwarder=None):
    try:
        if driver:
            driver.quit()
    except Exception:
        pass
    try:
        if forwarder:
            forwarder.close()
    except Exception:
        pass


# ==================== 11. CHƯƠNG TRÌNH CHÍNH ====================
def load_proxies_from_input(raw_input):
    raw_input = raw_input.strip().strip('"').strip("'")
    if not raw_input:
        return []
    if os.path.isfile(raw_input):
        with open(raw_input, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return [p.strip() for p in raw_input.split(",") if p.strip()]


def worker_thread(idx, proxy, account, check_live):
    if STOP_EVENT.is_set():
        return
    tab_name = f"Tab-{idx + 1}"
    driver, forwarder = open_chrome_safe(thread_idx=idx, raw_proxy=proxy, check_live=check_live)
    if not driver:
        return
    try:
        print(Colors.color_text(f"[{tab_name}] Đang mở trang đăng nhập Facebook...", Colors.INFO))
        driver.get(FB_LOGIN_URL)
        _dismiss_cookie_popup(driver)
        print(Colors.color_text(f"[{tab_name}] Đã mở trang đăng nhập Facebook!", Colors.SUCCESS))

        if account:
            login_facebook(driver, account, tab_name)
    except Exception as e:
        print(Colors.color_text(f"[{tab_name}] Lỗi khi tải trang: {e}", Colors.ERROR))


if __name__ == "__main__":
    banner()

    built_in_print(
        f"{Colors.KEY}Nhập đường dẫn file Proxy (.txt) HOẶC dán trực tiếp proxy (Enter để chạy IP máy): {Colors.RESET}",
        end="",
    )
    proxy_in = input()
    proxies_list = load_proxies_from_input(proxy_in)
    if proxies_list:
        built_in_print(f"{Colors.SUCCESS}Đã tải {len(proxies_list)} Proxy.{Colors.RESET}")
    else:
        built_in_print(f"{Colors.INFO}Không dùng Proxy (chạy IP gốc của máy).{Colors.RESET}")

    check_opt = "n"
    if proxies_list:
        built_in_print(
            f"{Colors.KEY}Check live proxy trước khi mở Chrome? (y/n - Enter mặc định y): {Colors.RESET}",
            end="",
        )
        check_opt = input().strip().lower() or "y"

    built_in_print(
        f"{Colors.KEY}Nhập file tài khoản (.txt) HOẶC dán tk|mk|2fa (Enter để mở trang FB trước rồi dán sau): {Colors.RESET}",
        end="",
    )
    acc_in = input()
    accounts_list = load_accounts_from_input(acc_in)
    if accounts_list:
        built_in_print(f"{Colors.SUCCESS}Đã tải {len(accounts_list)} tài khoản Facebook.{Colors.RESET}")
    else:
        built_in_print(f"{Colors.INFO}Chế độ tương tác: Mở sẵn trang đăng nhập FB, sau đó bạn dán SĐT(+)/Email/UID|mk|2fa vào console.{Colors.RESET}")

    default_tabs = len(accounts_list) if accounts_list else 1
    built_in_print(
        f"{Colors.KEY}Nhập số luồng (số tab Chrome chạy cùng lúc - Enter mặc định {default_tabs}): {Colors.RESET}",
        end="",
    )
    tabs_in = input().strip()
    num_tabs = int(tabs_in) if tabs_in.isdigit() and int(tabs_in) > 0 else default_tabs

    built_in_print(f"\n{Colors.LINE}{'─' * 78}{Colors.RESET}")

    threads = []
    for i in range(num_tabs):
        assigned_proxy = proxies_list[i % len(proxies_list)] if proxies_list else None
        assigned_account = accounts_list[i] if i < len(accounts_list) else None
        t = threading.Thread(
            target=worker_thread,
            args=(i, assigned_proxy, assigned_account, check_opt == "y"),
        )
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()

        built_in_print(f"\n{Colors.LINE}{'=' * 78}{Colors.RESET}")
        built_in_print(Colors.color_text("ĐÃ HOÀN THÀNH MỞ TOÀN BỘ CÁC TAB CHROME!", Colors.SUCCESS))

        sorted_drivers = sorted(ALL_DRIVERS, key=lambda x: int(x[0].split("-")[1]))

        if sorted_drivers and len(accounts_list) < len(sorted_drivers):
            built_in_print(f"\n{Colors.TITLE}NHẬP TÀI KHOẢN ĐỂ TỰ ĐỘNG ĐĂNG NHẬP (VD: +84912...|pass|2fa hoặc mail|pass|2fa):{Colors.RESET}")
            login_threads = []
            for idx_tab, (tid, drv, fwd) in enumerate(sorted_drivers):
                if idx_tab < len(accounts_list):
                    continue
                try:
                    drv.title
                except Exception:
                    continue

                while True:
                    built_in_print(
                        f"{Colors.KEY}[{tid}] Dán chuỗi tk|mk|2fa (Enter để bỏ qua tab này): {Colors.RESET}",
                        end="",
                    )
                    raw_acc = input().strip()
                    if not raw_acc:
                        built_in_print(f"{Colors.INFO}>> Bỏ qua tự đăng nhập cho {tid}.{Colors.RESET}")
                        break

                    parsed_acc = parse_account(raw_acc)
                    if not parsed_acc:
                        built_in_print(
                            f"{Colors.ERROR}Không nhận diện được định dạng! Hãy dán dạng SĐT(+)/Email/UID|mk|2fa.{Colors.RESET}"
                        )
                        continue

                    built_in_print(
                        f"{Colors.SUCCESS}>> Đã tách [{parsed_acc['id_type']}]: {parsed_acc['user']} | MK={'*' * len(parsed_acc['pass'])} | 2FA={'Có' if parsed_acc['twofa'] else 'Không'}{Colors.RESET}"
                    )
                    lt = threading.Thread(target=login_facebook, args=(drv, parsed_acc, tid))
                    lt.start()
                    login_threads.append(lt)
                    break

            for lt in login_threads:
                lt.join()

        if EXTRACTED_COOKIES:
            built_in_print(
                f"\n{Colors.SUCCESS}Tổng cộng đã trích xuất {len(EXTRACTED_COOKIES)} Cookie -> Lưu tại: {COOKIE_OUTPUT_FILE}{Colors.RESET}"
            )

        if sorted_drivers:
            built_in_print(f"\n{Colors.TITLE}TIẾN HÀNH RÀ SOÁT VÀ ĐÓNG TRÌNH DUYỆT CỦA TỪNG TAB:{Colors.RESET}")
            kept_with_forwarder = 0

            for tid, drv, fwd in sorted_drivers:
                try:
                    drv.title
                    while True:
                        built_in_print(
                            f"{Colors.WARNING}[{tid}] Đóng Chrome (y) / Giữ lại (n) / Lấy UID & Cookie thủ công (c): {Colors.RESET}",
                            end="",
                        )
                        choice = input().strip().lower()
                        if choice == "c":
                            c_user, cookie_str = extract_uid_and_cookie(drv, tid)
                            save_extracted_cookie(tid, c_user, cookie_str, TAB_ACCOUNTS.get(tid))
                        elif choice == "y":
                            close_chrome_driver(drv, fwd)
                            built_in_print(f"{Colors.SUCCESS}>> Đã đóng trình duyệt & cổng Proxy của {tid}.{Colors.RESET}")
                            break
                        elif choice == "n":
                            if fwd:
                                kept_with_forwarder += 1
                            built_in_print(f"{Colors.INFO}>> Đã giữ lại trình duyệt của {tid}.{Colors.RESET}")
                            break
                        else:
                            built_in_print(f"{Colors.ERROR}Vui lòng chỉ nhập y, n hoặc c!{Colors.RESET}")
                except Exception:
                    if fwd:
                        fwd.close()

            if kept_with_forwarder > 0:
                built_in_print(
                    f"\n{Colors.WARNING}LƯU Ý: Có {kept_with_forwarder} tab đang giữ lại chạy qua Proxy có User/Pass.{Colors.RESET}"
                )
                built_in_print(
                    f"{Colors.WARNING}Hãy giữ nguyên cửa sổ console này cho tới khi bạn dùng xong (tắt console sẽ ngắt cầu nối Proxy).{Colors.RESET}"
                )

        built_in_print(f"\n{Colors.SUCCESS}TOOL ĐÃ KẾT THÚC CÔNG VIỆC!{Colors.RESET}")
        built_in_print(f"{Colors.KEY}Nhấn Enter để thoát chương trình...{Colors.RESET}", end="")
        input()

    except KeyboardInterrupt:
        STOP_EVENT.set()
        built_in_print(f"\n{Colors.ERROR}Đang buộc dừng các luồng và đóng Chrome...{Colors.RESET}")
        for _, drv, fwd in ALL_DRIVERS:
            close_chrome_driver(drv, fwd)
        sys.exit(0)
