import concurrent.futures
import datetime
import os
import random
import re
import sys
import threading
import time
from typing import Dict, List, Optional, Tuple

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ================== GIAO DIỆN & MÀU SẮC ==================
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRED = "\033[91m"
    BGREEN = "\033[92m"
    BYELLOW = "\033[93m"
    BCYAN = "\033[96m"
    BWHITE = "\033[97m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAG = "\033[45m"
    BG_CYAN = "\033[46m"
    PINK = "\033[38;5;213m"
    TEAL = "\033[38;5;80m"
    LIME = "\033[38;5;154m"
    GRAY = "\033[38;5;245m"
    DGRAY = "\033[38;5;240m"
    GOLD = "\033[38;5;220m"


def color(text: str, code: str) -> str:
    return f"{code}{text}{C.RESET}"


def enable_ansi():
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7
            )
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


_print_lock = threading.Lock()


class Logger:
    TAGS = {
        "INFO": (C.BG_BLUE + C.BWHITE + C.BOLD, " INFO "),
        "LIVE": (C.BG_GREEN + C.BLACK + C.BOLD, " LIVE "),
        "DIE": (C.BG_RED + C.BWHITE + C.BOLD, " DIE  "),
        "CHKPT": (C.BG_MAG + C.BWHITE + C.BOLD, " CP   "),
        "WARN": (C.BG_YELLOW + C.BLACK + C.BOLD, " WARN "),
        "ERR": (C.BG_RED + C.BWHITE + C.BOLD, " ERR  "),
    }

    @staticmethod
    def _now() -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")

    @classmethod
    def emit(cls, tag_key: str, msg: str, msg_color: str = ""):
        ts = color(cls._now(), C.DGRAY)
        sep = color("|", C.DGRAY)
        style, label = cls.TAGS.get(tag_key, cls.TAGS["INFO"])
        tag = color(label, style)
        body = color(msg, msg_color) if msg_color else msg
        with _print_lock:
            print(f" {ts} {sep} {tag} {sep} {body}", flush=True)

    @classmethod
    def info(cls, msg: str):
        cls.emit("INFO", msg, C.BWHITE)

    @classmethod
    def live(cls, msg: str):
        cls.emit("LIVE", msg, C.LIME)

    @classmethod
    def die(cls, msg: str):
        cls.emit("DIE", msg, C.BRED)

    @classmethod
    def checkpoint(cls, msg: str):
        cls.emit("CHKPT", msg, C.PINK)

    @classmethod
    def warn(cls, msg: str):
        cls.emit("WARN", msg, C.GOLD)

    @classmethod
    def error(cls, msg: str):
        cls.emit("ERR", msg, C.BRED)


def prompt(text: str, default: str = "") -> str:
    suffix = f" {color('[' + default + ']', C.DGRAY)}" if default else ""
    raw = input(f" {color('>', C.BCYAN)} {color(text, C.BWHITE)}{suffix}: ").strip()
    return raw if raw else default


# ================== XỬ LÝ PROXY (HỖ TRỢ CẢ 5 PHẦN :HTTP / :SOCKS5) ==================
def format_proxy_url(proxy_str: Optional[str]) -> Optional[str]:
    if not proxy_str:
        return None
    px = str(proxy_str).strip().strip('"').strip("'")
    if not px:
        return None

    if px.startswith(("http://", "https://", "socks5://", "socks5h://")) and "@" in px:
        return px

    scheme = "http"
    for prefix in ("http://", "https://", "socks5://", "socks5h://"):
        if px.lower().startswith(prefix):
            scheme = prefix.rstrip(":/")
            px = px[len(prefix):]
            break

    parts = [p.strip() for p in px.split(":") if p.strip() != ""]

    if len(parts) >= 5 and parts[-1].upper() in ("HTTP", "HTTPS", "SOCKS5", "SOCKS5H", "SOCKS4"):
        tail = parts.pop().lower()
        scheme = "socks5" if tail.startswith("socks") else "http"

    if len(parts) == 4:
        host, port, user, passwd = parts[0], parts[1], parts[2], parts[3]
        return f"{scheme}://{user}:{passwd}@{host}:{port}"
    elif len(parts) == 2:
        host, port = parts[0], parts[1]
        return f"{scheme}://{host}:{port}"
    else:
        return f"{scheme}://{px}"


# ================== BÓC TÁCH DÒNG TÀI KHOẢN ==================
def parse_account_line(line: str) -> Tuple[Optional[str], Optional[str], Dict[str, str]]:
    """
    Trả về (uid, cookie_str, cookie_dict) từ dòng bất kỳ:
    Hỗ trợ: UID|Pass|Cookie, UID|Pass|2FA|Cookie|Mail..., hoặc chỉ Cookie.
    """
    clean = line.strip()
    if not clean or clean.startswith("#"):
        return None, None, {}

    parts = [p.strip() for p in clean.split("|")]
    uid = None
    cookie_str = None

    # 1. Tìm phần chứa cookie (c_user=...)
    for p in parts:
        if "c_user=" in p or "xs=" in p:
            cookie_str = p
            break

    # 2. Tìm UID từ cột đầu tiên nếu là dãy số
    if parts and parts[0].isdigit() and len(parts[0]) >= 8:
        uid = parts[0]

    # 3. Chuyển cookie_str sang dict
    cookie_dict: Dict[str, str] = {}
    if cookie_str:
        for item in cookie_str.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                cookie_dict[k.strip()] = v.strip()

    # 4. Nếu chưa có UID, lấy từ c_user trong cookie
    if not uid and cookie_dict.get("c_user"):
        uid = cookie_dict["c_user"]

    return uid, cookie_str, cookie_dict


def compute_jazoest(token: str) -> str:
    if not token:
        return "2"
    return f"2{sum(ord(c) for c in str(token))}"


# ================== CÁC HÀM CHECK LIVE ==================
def check_uid_graph(uid: str, session: requests.Session) -> Tuple[bool, str]:
    """
    Check nhanh UID qua Graph API Avatar.
    - Redirect về scontent -> LIVE
    - Redirect về static.xx.fbcdn.net / UlIqmHJn-SK.gif -> DIE (282/956/Disabled)
    """
    url = f"https://graph.facebook.com/{uid}/picture?type=normal"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }
    for attempt in range(2):
        try:
            r = session.get(url, headers=headers, allow_redirects=False, timeout=12, verify=False)
            location = r.headers.get("Location", "")
            if r.status_code in (301, 302, 303, 307, 308) and location:
                if "scontent" in location and "UlIqmHJn-SK.gif" not in location:
                    return True, "UID Live (Graph)"
                if "static.xx.fbcdn.net" in location or "UlIqmHJn-SK.gif" in location:
                    return False, "UID Die / Checkpoint"
            # Fallback nếu bị chặn redirect thẳng
            r2 = session.get(url, headers=headers, allow_redirects=True, timeout=12, verify=False)
            final_url = r2.url or ""
            if "scontent" in final_url and "UlIqmHJn-SK.gif" not in final_url:
                return True, "UID Live"
            if "static.xx.fbcdn.net" in final_url or "UlIqmHJn-SK.gif" in final_url:
                return False, "UID Die / Checkpoint"
        except Exception as e:
            if attempt == 1:
                return False, f"Lỗi mạng/Proxy: {str(e)[:40]}"
            time.sleep(1)
    return False, "Không xác định (Die)"


def check_cookie_and_bypass_049(uid: str, cookie_dict: Dict[str, str], session: requests.Session) -> Tuple[bool, str]:
    """
    Check sâu bằng Cookie:
    - Kiểm tra पहले qua Graph UID xem acc có bị khóa cứng không.
    - Sau đó nạp Cookie vào truy cập facebook.com để kiểm tra phiên đăng nhập và gỡ CP 049.
    """
    # Bước 1: Check Graph UID trước
    uid_live, reason = check_uid_graph(uid, session)
    if not uid_live and "Lỗi mạng" not in reason:
        return False, reason

    if not cookie_dict or "c_user" not in cookie_dict or "xs" not in cookie_dict:
        return uid_live, "Thiếu Cookie (Chỉ check UID: Live)"

    # Bước 2: Nạp Cookie kiểm tra phiên thực tế
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": ua,
    }
    session.cookies.update(cookie_dict)

    try:
        r = session.get("https://www.facebook.com/", headers=headers, allow_redirects=True, timeout=15, verify=False)
        final_url = r.url or ""
        html = r.text or ""

        # Nếu bị đá ra trang login hoặc mất c_user
        if "login" in final_url or "c_user" not in session.cookies.get_dict():
            return False, "Cookie Die (Văng phiên đăng nhập)"

        # Nếu dính Checkpoint
        if "checkpoint" in final_url:
            if "601051028565049" in final_url:
                # Tự động gỡ CP 049
                dtsg_match = (
                    re.search(r'name="fb_dtsg" value="(.*?)"', html)
                    or re.search(r'"DTSGInitialData",\[\],\{"token":"(.*?)"\}', html)
                )
                lsd_match = re.search(r'name="lsd" value="(.*?)"', html)
                if dtsg_match:
                    fb_dtsg = dtsg_match.group(1)
                    lsd = lsd_match.group(1) if lsd_match else ""
                    bypass_headers = {
                        "accept": "*/*",
                        "content-type": "application/x-www-form-urlencoded",
                        "origin": "https://www.facebook.com",
                        "referer": final_url,
                        "user-agent": ua,
                    }
                    bypass_data = {
                        "av": uid,
                        "__user": uid,
                        "__a": "1",
                        "__req": "1",
                        "fb_dtsg": fb_dtsg,
                        "jazoest": compute_jazoest(fb_dtsg),
                        "lsd": lsd,
                        "fb_api_caller_class": "RelayModern",
                        "fb_api_req_friendly_name": "FBScrapingWarningMutation",
                        "server_timestamps": "true",
                        "variables": "{}",
                        "doc_id": "24406519995698862",
                    }
                    rb = session.post(
                        "https://www.facebook.com/api/graphql/",
                        headers=bypass_headers,
                        data=bypass_data,
                        timeout=15,
                        verify=False,
                    )
                    if "data" in rb.text:
                        return True, "Live (Đã tự gỡ CP 049)"
                return False, "Checkpoint 049 (Không gỡ được)"
            elif "1501092823525282" in final_url:
                return False, "Checkpoint 282"
            elif "828281030927956" in final_url:
                return False, "Checkpoint 956"
            else:
                return False, f"Checkpoint ({final_url.split('/')[-1][:20]})"

        # Kiểm tra xem trong HTML có chứa UID hoặc DTSG của user đang đăng nhập không
        if f'"USER_ID":"{uid}"' in html or '"DTSGInitialData"' in html or uid in session.cookies.get("c_user", ""):
            return True, "Live (Cookie + UID OK)"

        return False, "Cookie Die / Không vào được Home"
    except Exception as e:
        # Nếu lỗi proxy lúc check web nhưng bước 1 Graph UID đã báo Live
        if uid_live:
            return True, f"UID Live (Bỏ qua web do lỗi mạng: {str(e)[:25]})"
        return False, f"Lỗi kết nối: {str(e)[:40]}"


# ================== LUỒNG XỬ LÝ CHÍNH ==================
def worker_check(
    idx: int,
    total: int,
    line: str,
    mode: str,
    proxies_list: List[str],
) -> Tuple[int, bool, str, str]:
    """
    Trả về: (chỉ_số_dòng, is_live, original_line, thông_báo)
    """
    uid, _, cookie_dict = parse_account_line(line)
    if not uid:
        Logger.warn(f"[{idx}/{total}] Dòng lỗi định dạng -> Bỏ qua: {line[:40]}...")
        return idx, False, line, "Sai định dạng"

    session = requests.Session()
    session.verify = False

    if proxies_list:
        px = random.choice(proxies_list)
        session.proxies.update({"http": px, "https": px})

    if mode == "1":
        is_live, detail = check_cookie_and_bypass_049(uid, cookie_dict, session)
    else:
        is_live, detail = check_uid_graph(uid, session)

    if is_live:
        Logger.live(f"[{idx}/{total}] UID: {uid:<16} | {detail}")
    else:
        if "Checkpoint" in detail:
            Logger.checkpoint(f"[{idx}/{total}] UID: {uid:<16} | {detail}")
        else:
            Logger.die(f"[{idx}/{total}] UID: {uid:<16} | {detail}")

    return idx, is_live, line, detail


def write_lines_atomic(filepath: str, lines: List[str]):
    """Ghi danh sách dòng ra file an toàn."""
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        for ln in lines:
            clean = ln.strip("\r\n")
            if clean:
                f.write(clean + "\n")
    try:
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(tmp_path, filepath)


def main():
    enable_ansi()
    os.system("cls" if os.name == "nt" else "clear")

    print(color("+" + "=" * 74 + "+", C.BCYAN))
    print(color("|", C.BCYAN) + color("          TOOL CHECK LIVE FACEBOOK (UID | PASS | COOKIE)          ", C.BOLD + C.BWHITE) + color("        |", C.BCYAN))
    print(color("|", C.BCYAN) + color("     Tự động lọc acc Sống - Xóa acc Chết - Gỡ Checkpoint 049     ", C.GRAY) + color("         |", C.BCYAN))
    print(color("+" + "=" * 74 + "+", C.BCYAN))
    print()

    # 1. Nhận file đầu vào (từ tham số dòng lệnh hoặc kéo thả vào CMD)
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1].strip('"').strip("'")):
        file_path = sys.argv[1].strip('"').strip("'")
        Logger.info(f"Đã nhận file: {file_path}")
    else:
        while True:
            raw_path = prompt("Kéo thả file .txt chứa acc vào đây (hoặc nhập tên file)", default="success..txt")
            file_path = raw_path.strip().strip('"').strip("'")
            if os.path.isfile(file_path):
                break
            Logger.error(f"Không tìm thấy file: {file_path} — Vui lòng thử lại!")

    file_path = os.path.abspath(file_path)
    base_dir = os.path.dirname(file_path)
    base_name, ext = os.path.splitext(os.path.basename(file_path))

    # Đọc toàn bộ dòng hợp lệ và lọc trùng
    raw_lines: List[str] = []
    seen = set()
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            s = ln.strip()
            if s and not s.startswith("#") and s not in seen:
                seen.add(s)
                raw_lines.append(s)

    total_acc = len(raw_lines)
    if total_acc == 0:
        Logger.error("File trống hoặc không có tài khoản nào!")
        return

    Logger.info(f"Đã tải {color(str(total_acc), C.LIME)} tài khoản từ file: {color(os.path.basename(file_path), C.TEAL)}")
    print()

    # 2. Chọn chế độ Check
    print(f"   {color('*', C.BCYAN)} {color('[1]', C.BOLD + C.TEAL)} {color('Check Sâu (Cookie + UID + Tự gỡ CP 049)', C.BWHITE)} {color('(Khuyên dùng - Mặc định)', C.GOLD)}")
    print(f"   {color('o', C.DGRAY)} {color('[2]', C.BOLD + C.TEAL)} {color('Check Nhanh bằng Graph UID', C.BWHITE)} {color('(Siêu tốc, không cần Proxy, check khóa 282/956)', C.GRAY)}")
    print()
    mode = prompt("Chọn chế độ check [1/2]", default="1")
    if mode not in ("1", "2"):
        mode = "1"

    # 3. Tuỳ chọn Proxy
    proxies_list: List[str] = []
    px_input = prompt("Nhập đường dẫn file Proxy hoặc dán 1 Proxy (Enter = Chạy IP máy)", default="")
    if px_input:
        px_clean = px_input.strip().strip('"').strip("'")
        if os.path.isfile(px_clean):
            with open(px_clean, "r", encoding="utf-8", errors="ignore") as pf:
                for pln in pf:
                    fmt = format_proxy_url(pln)
                    if fmt:
                        proxies_list.append(fmt)
            Logger.info(f"Đã nạp {len(proxies_list)} proxy từ file.")
        else:
            fmt = format_proxy_url(px_clean)
            if fmt:
                proxies_list.append(fmt)
                Logger.info(f"Sử dụng Proxy: {fmt}")

    # 4. Chọn số luồng
    default_threads = "15" if mode == "1" else "30"
    try:
        max_workers = int(prompt("Số luồng chạy cùng lúc", default=default_threads))
        max_workers = max(1, min(max_workers, 100))
    except Exception:
        max_workers = int(default_threads)

    print()
    print(color("-" * 76, C.DGRAY))
    Logger.info(f"Bắt đầu kiểm tra {total_acc} tài khoản với {max_workers} luồng...")
    print(color("-" * 76, C.DGRAY))

    start_time = time.time()
    results: List[Tuple[int, bool, str, str]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(worker_check, i + 1, total_acc, line, mode, proxies_list)
            for i, line in enumerate(raw_lines)
        ]
        for fut in concurrent.futures.as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                Logger.error(f"Lỗi luồng: {e}")

    # Sắp xếp lại đúng thứ tự ban đầu trong file
    results.sort(key=lambda x: x[0])

    live_lines = [r[2] for r in results if r[1]]
    die_lines = [r[2] for r in results if not r[1]]

    # 5. Ghi kết quả:
    # - Cập nhật trực tiếp file gốc (chỉ giữ lại con sống, xóa con chết)
    # - Tạo thêm file mới <tên_file>_live.txt và <tên_file>_die.txt
    new_live_file = os.path.join(base_dir, f"{base_name}_live{ext}")
    new_die_file = os.path.join(base_dir, f"{base_name}_die{ext}")

    write_lines_atomic(file_path, live_lines)
    write_lines_atomic(new_live_file, live_lines)
    if die_lines:
        write_lines_atomic(new_die_file, die_lines)

    elapsed = time.time() - start_time
    print()
    print(color("=" * 76, C.BCYAN))
    print(f"  {color('HOÀN TẤT KIỂM TRA', C.BOLD + C.BWHITE)} (Thời gian: {elapsed:.1f}s)")
    print(color("-" * 76, C.DGRAY))
    print(f"  * Tổng tài khoản đã check : {color(str(total_acc), C.BWHITE)}")
    print(f"  * Tài khoản SỐNG (LIVE)   : {color(str(len(live_lines)), C.LIME)}")
    print(f"  * Tài khoản CHẾT (DIE/CP) : {color(str(len(die_lines)), C.BRED)}")
    print(color("-" * 76, C.DGRAY))
    print(f"  [+] Đã xóa acc chết & cập nhật trực tiếp file gốc : {color(file_path, C.TEAL)}")
    print(f"  [+] Đã xuất file mới chỉ chứa acc LIVE            : {color(new_live_file, C.LIME)}")
    if die_lines:
        print(f"  [+] File lưu riêng các acc DIE/Checkpoint         : {color(new_die_file, C.GOLD)}")
    print(color("=" * 76, C.BCYAN))
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{color('[!] Đã dừng chương trình.', C.BYELLOW)}")
