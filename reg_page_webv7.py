#!/usr/bin/env python3
"""Reg Page Web v5 — Đăng ký Facebook Page hàng loạt & Get Token từ Cookie/Pass."""
import os, sys, re, json, time, uuid, random, base64, hmac, hashlib, string, secrets
import threading, argparse, errno, socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from queue import Queue, Empty
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    print("Cài: pip install requests"); sys.exit(1)

try:
    import pyotp
except ImportError:
    print("Thiếu thư viện 2FA. Cài: pip install pyotp"); sys.exit(1)

try:
    from http.server import ThreadingHTTPServer
except ImportError:
    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

DEFAULT_PORT = 8770
DATA_DIR = os.environ.get("REG_WEB_DIR", os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(DATA_DIR, "reg_page_config.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "created_pages.txt")
LOG_FILE = os.path.join(DATA_DIR, "reg_page_log.txt")

BLOKS_VERSIONING_ID = "c11a8c0d160df62b2395f6153824f0bc6c6e316a74ab1aff67da02cdd7cc890b"
CLIENT_DOC_ID = "11994080426203054249997361787"
GRAPHQL_URL = "https://graph.facebook.com/graphql"
FB_TOKEN_DEAD = {190, 102, 463, 467, 458, 460, 464, 2500}
NET = -1

FBAV_VERSIONS = [("543.0.0.55.73", "846638243"), ("540.0.0.42.50", "838765431"), ("535.0.0.40.114", "825638102"), ("530.0.0.34.82", "812456789"), ("510.0.0.72.41", "725719471")]
DEVICE_POOL = [("Samsung", "samsung", "Galaxy S24 Ultra", "SM-S928B", 3.5, 1440, 3120, 14, 14), ("Samsung", "samsung", "Galaxy S23 Ultra", "SM-S918B", 3.5, 1440, 3088, 13, 14), ("Samsung", "samsung", "Galaxy S21 5G", "SM-G991B", 3.0, 1080, 2400, 11, 14), ("Xiaomi", "xiaomi", "Xiaomi 13", "2211133G", 3.0, 1080, 2400, 13, 14), ("Xiaomi", "xiaomi", "Redmi Note 12 Pro", "22101316G", 3.0, 1080, 2400, 12, 14), ("Google", "google", "Pixel 8 Pro", "Pixel 8 Pro", 3.5, 1344, 2992, 14, 14), ("Google", "google", "Pixel 7 Pro", "Pixel 7 Pro", 3.5, 1440, 3120, 13, 14), ("Oppo", "OPPO", "Reno10 Pro 5G", "CPH2525", 3.0, 1080, 2412, 13, 14)]
CARRIERS = ["Viettel", "Vinaphone", "MobiFone", "Vietnamobile", "VIETTEL"]
LOCALES = ["vi_VN", "en_US"]

HO_VIET = ["Nguyễn","Trần","Lê","Phạm","Hoàng","Huỳnh","Phan","Vũ","Võ","Đặng","Bùi","Đỗ","Hồ","Ngô","Dương","Lý","Đào","Đoàn","Mai","Trịnh","Đinh","Lâm","Phùng","Cao","Hà","Lương","Tạ","Thái"]
DEM_NAM = ["Văn","Đức","Đình","Hữu","Tuấn","Minh","Quốc","Thanh","Trọng","Duy","Bảo","Quang","Hải","Tiến","Công","Khắc","Gia","Đăng"]
DEM_NU = ["Thị","Ngọc","Thu","Thanh","Khánh","Phương","Kim","Ánh","Hải","Hồng","Bảo","Mỹ","Quỳnh","Thùy","Yến","Lan","Mai","Cẩm"]
TEN_NAM = ["Nam","Tuấn","Anh","Khải","Dũng","Quân","Cường","Đạt","Huy","Hoàng","Phong","Long","Sơn","Thắng","Phúc","Lộc","Trí","Trung","Hiếu","Nghĩa","Vinh","Khánh","Hưng","Bách","Đức","Kiên","Lâm"]
TEN_NU = ["Linh","Trang","Hằng","Mai","Thảo","Hương","Anh","Vy","Hà","Ngọc","Châu","Nhi","Trâm","Hiền","Dung","Hoa","Lan","Huệ","Cúc","Trúc","Ly","My","Oanh","Quyên","Tâm","Uyên","Vân"]
US_FIRST = ["James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Daniel","Matthew","Anthony","Mark","Steven","Paul","Andrew","Joshua","Kevin","Brian","George","Edward","Timothy","Jason","Ryan","Jacob","Gary","Nicholas","Eric","Mary","Patricia","Jennifer","Linda","Elizabeth","Barbara","Susan","Jessica","Sarah","Karen","Lisa","Nancy","Betty","Margaret","Sandra","Ashley","Kimberly","Emily","Donna","Michelle","Carol","Amanda","Melissa","Rebecca","Sharon","Laura","Sophia","Emma"]
US_LAST = ["Smith","Johnson","Williams","Brown","Jones","Miller","Davis","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker","Young","Allen","King","Wright","Scott","Torres","Hill","Flores","Green","Adams"]

def say(m):
    try: sys.stdout.buffer.write((str(m) + "\n").encode("utf-8", "replace")); sys.stdout.flush()
    except Exception: pass

def ensure_data_dir():
    for d in (DATA_DIR, os.path.join(os.path.expanduser("~"), ".reg_page_web")):
        try:
            os.makedirs(d, exist_ok=True); t = os.path.join(d, ".wtest"); open(t, "w").write("ok"); os.remove(t); return d
        except Exception: continue
    raise OSError("Không ghi được file")

def parse_proxy(px):
    if not px: return None
    p = px.strip()
    if not p: return None
    if "://" in p: return p
    parts = p.split(":")
    if len(parts) == 4: return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    if len(parts) == 2: return f"http://{p}"
    if "@" in p: return f"http://{p}"
    return None

def gen_ua(seed=None):
    rng = random.Random(int(hashlib.md5(str(seed).encode()).hexdigest(), 16)) if seed else random.Random()
    mfg, brand, _, dev, den, w, h, amin, amax = rng.choice(DEVICE_POOL)
    av = rng.randint(amin, amax); fbav, fbbv = rng.choice(FBAV_VERSIONS)
    return (f"[FBAN/FB4A;FBAV/{fbav};FBBV/{fbbv};FBDM/{{density={den},width={w},height={h}}};FBLC/{rng.choice(LOCALES)};FBRV/0;FBCR/{rng.choice(CARRIERS)};FBMF/{mfg.lower()};FBBD/{brand};FBPN/com.facebook.katana;FBDV/{dev};FBSV/{av};FBOP/1;FBCA/x86_64:arm64-v8a;]")

def gen_vn_name():
    ho = random.choice(HO_VIET)
    return f"{ho} {random.choice(DEM_NAM if random.random()<0.5 else DEM_NU)} {random.choice(TEN_NAM if random.random()<0.5 else TEN_NU)}"
def gen_us_name(): return f"{random.choice(US_FIRST)} {random.choice(US_LAST)}"
def get_page_name(mode, custom=None):
    if mode == "us": return gen_us_name()
    if mode == "custom" and custom: return random.choice(custom)
    return gen_vn_name()

class InforN:
    def __init__(self):
        self.uid = None
        self.password = None
        self.authencation = None
        self.machine_id = None
        self.cookie = None
        self.token = None

class giai_str:
    @staticmethod
    def tao_nn_c(length: int) -> str:
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def pwd_format(password: str) -> str:
        timestamp = int(time.time())
        return f"#PWD_FB4A:0:{timestamp}:{password}"

class get_inf:
    @staticmethod
    def lay_nonce(size: int) -> str:
        return base64.b64encode(secrets.token_bytes(size)).decode('utf-8')
    
    @staticmethod
    def encbs4(text: str) -> str:
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def hash_data(uid: str) -> str:
        nonce = get_inf.lay_nonce(32)
        raw_data = f'{{"challenge_nonce":"{nonce}","username":"{uid}"}}'
        return get_inf.encbs4(raw_data)
    
    @staticmethod
    def create_vari(account: InforN) -> str:
        shared_guid = str(uuid.uuid4())
        device_id = shared_guid
        family_device_id = shared_guid
        secure_family_device_id = str(uuid.uuid4())
        waterfall_id = str(uuid.uuid4())
        data = get_inf.hash_data(account.uid)
        machine_id = account.machine_id if account.machine_id else giai_str.tao_nn_c(22)
        variable = {
            "params": {
                "params": json.dumps({
                    "client_input_params": {
                        "sim_phones": [], "secure_family_device_id": secure_family_device_id,
                        "attestation_result": {
                            "data": data,
                            "signature": "MEYCIQDtz5TqO0pwysy82Ko92FErORasLag9o/pQYlZl8+zaMgIhAKon529upFiPfGgoS6OkPKg0/VahBuSDxwiTgtzpYQA3",
                            "keyHash": "92398b3e4d9ee926bae93a61fd75e18d750100c1e73fd44d4faa7b9ba9353eee"
                        },
                        "has_granted_read_contacts_permissions": 0, "auth_secure_device_id": "",
                        "has_whatsapp_installed": 0, "password": giai_str.pwd_format(account.password),
                        "sso_token_map_json_string": "", "event_flow": "login_manual",
                        "password_contains_non_ascii": "false", "sim_serials": [], "client_known_key_hash": "",
                        "encrypted_msisdn": "", "has_granted_read_phone_permissions": 0, "app_manager_id": "null",
                        "should_show_nested_nta_from_aymh": 0, "device_id": device_id, "login_attempt_count": 1,
                        "machine_id": machine_id,
                        "flash_call_permission_status": {"READ_PHONE_STATE": "DENIED", "READ_CALL_LOG": "DENIED", "ANSWER_PHONE_CALLS": "DENIED"},
                        "accounts_list": [], "family_device_id": family_device_id, "fb_ig_device_id": [],
                        "device_emails": [], "try_num": 2, "lois_settings": {"lois_token": ""},
                        "event_step": "home_page", "headers_infra_flow_id": "", "openid_tokens": {},
                        "contact_point": account.uid
                    },
                    "server_params": {
                        "should_trigger_override_login_2fa_action": 0, "is_from_logged_out": 0,
                        "should_trigger_override_login_success_action": 0, "login_credential_type": "none",
                        "server_login_source": "login", "waterfall_id": waterfall_id, "login_source": "Login",
                        "is_platform_login": 0, "pw_encryption_try_count": 1, "INTERNAL__latency_qpl_marker_id": 36707139,
                        "offline_experiment_group": "caa_iteration_v6_perf_fb_2", "is_from_landing_page": 0,
                        "password_text_input_id": "jirv90:99", "is_from_empty_password": 0, "is_from_msplit_fallback": 0,
                        "ar_event_source": "login_home_page", "username_text_input_id": "jirv90:98",
                        "layered_homepage_experiment_group": None, "device_id": device_id,
                        "INTERNAL__latency_qpl_instance_id": 118039064400779, "reg_flow_source": "login_home_native_integration_point",
                        "is_caa_perf_enabled": 1, "credential_type": "password", "is_from_password_entry_page": 0,
                        "caller": "gslr", "family_device_id": family_device_id, "is_from_assistive_id": 0,
                        "access_flow_version": "F2_FLOW", "is_from_logged_in_switcher": 0
                    }
                }),
                "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
                "app_id": "com.bloks.www.bloks.caa.login.async.send_login_request"
            },
            "scale": "1.5",
            "nt_context": {
                "using_white_navbar": True, "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e",
                "pixel_ratio": 1.5, "is_push_on": True, "debug_tooling_metadata_token": None,
                "is_flipper_enabled": False, "theme_params": [],
                "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"
            }
        }
        return json.dumps(variable)

class extractck_tk:
    @staticmethod
    def extract_cookie_token(data: str) -> InforN:
        access_token = ""
        cookie_list = []
        try:
            at_pattern = r'"access_token":"([^"]+)"'
            at_match = re.search(at_pattern, data)
            access_token = at_match.group(1) if at_match else ""
            cookies_pattern = r'"session_cookies":\s*\[([^\]]+)\]'
            cookies_match = re.search(cookies_pattern, data)
            if cookies_match:
                cookie_str = cookies_match.group(1)
                cookie_pattern = r'"name":"([^"]+)","value":"([^"]+)"'
                for name, value in re.findall(cookie_pattern, cookie_str):
                    cookie_list.append(f"{name}={value}")
        except Exception as e:
            raise Exception(f"Lỗi parse response: {e}")
        result = InforN()
        result.cookie = "; ".join(cookie_list)
        result.token = access_token
        return result

class LoginService:
    def __init__(self, account: InforN, proxy=None):
        self._account = account
        self._session = requests.Session()
        if proxy: self._session.proxies = {"http": parse_proxy(proxy), "https": parse_proxy(proxy)}
        self.device_id = str(uuid.uuid4())
        self.family_device_id = self.device_id
    
    def _call_2fa_entrypoint(self, two_step_context: str, machine_id_2fa: str):
        screen_id = f"{uuid.uuid4().hex[:6]}:5"
        inner_params = {
            "client_input_params": {"device_id": self.device_id, "is_whatsapp_installed": 0, "machine_id": machine_id_2fa},
            "server_params": {"family_device_id": self.device_id, "device_id": self.device_id, "two_step_verification_context": two_step_context, "INTERNAL_INFRA_THEME": "harm_f,default,harm_f", "flow_source": "two_factor_login", "INTERNAL_INFRA_screen_id": screen_id},
        }
        variables = {
            "params": json.dumps(inner_params), "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
            "is_on_load_actions_supported": True, "app_id": "com.bloks.www.two_step_verification.entrypoint", "using_white_navbar": True,
            "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e", "pixel_ratio": 1.5, "is_push_on": True, "debug_tooling_metadata_token": None,
            "is_flipper_enabled": False, "theme_params": [], "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c", "scale": 1,
            "nt_context": {"using_white_navbar": True, "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e", "pixel_ratio": 1.5, "is_push_on": True, "debug_tooling_metadata_token": None, "is_flipper_enabled": False, "theme_params": [], "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"},
        }
        payload = {"method": "post", "pretty": "false", "format": "json", "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch", "fb_api_req_friendly_name": "FbBloksAppRootQuery-com.bloks.www.two_step_verification.entrypoint", "fb_api_caller_class": "graphservice", "client_doc_id": "105373461558397492702779496", "variables": json.dumps(variables), "fb_api_analytics_tags": '["GraphServices"]', "client_trace_id": str(uuid.uuid4())}
        self._session.post("https://b-graph.facebook.com/graphql", headers=self._build_headers(), data=payload)
    
    def _build_headers(self) -> dict:
        return {
            "User-Agent": "[FBAN/FB4A;FBAV/498.1.0.64.74;FBBV/692621185;FBDM/{density=1.5,width=540,height=960};FBLC/vi_VN;FBRV/0;FBCR/MobiFone;FBMF/Xiaomi;FBBD/Xiaomi;FBPN/com.facebook.katana;FBDV/2211133C;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]",
            "authorization": "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32",
            "x-fb-sim-hni": "45201", "x-fb-net-hni": "45201", "x-graphql-client-library": "graphservice",
            "x-fb-friendly-name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.login.async.send_login_request",
            "x-tigon-is-retry": "False", "x-graphql-request-purpose": "fetch", "x-fb-device-group": "2789",
            "Accept-Encoding": "identity", "x-zero-eh": "error", "x-fb-connection-type": "WIFI",
            "x-fb-http-engine": "Tigon/Liger", "x-fb-client-ip": "True", "x-fb-server-cluster": "True"
        }
    
    def _build_verify_payload(self, two_step_context: str, machine_id_2fa: str, code: str) -> dict:
        inner_params = {
            "client_input_params": {"auth_secure_device_id": "", "machine_id": machine_id_2fa, "code": code, "should_trust_device": 1, "family_device_id": self.device_id, "device_id": self.device_id},
            "server_params": {"INTERNAL__latency_qpl_marker_id": 36707139, "device_id": self.device_id, "challenge": "totp", "machine_id": machine_id_2fa, "INTERNAL__latency_qpl_instance_id": random.randint(0x5AF3107A4000, 0x38D7EA4C67FFF), "two_step_verification_context": two_step_context, "flow_source": "two_factor_login"},
        }
        variables = {
            "params": json.dumps(inner_params), "bloks_versioning_id": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c",
            "app_id": "com.bloks.www.two_step_verification.verify_code.async", "using_white_navbar": True,
            "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e", "pixel_ratio": 1.5, "is_push_on": True, "debug_tooling_metadata_token": None,
            "is_flipper_enabled": False, "theme_params": [], "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c", "scale": 1,
            "nt_context": {"using_white_navbar": True, "styles_id": "55d2af294359fa6bbdb8e045ff01fc5e", "pixel_ratio": 1.5, "is_push_on": True, "debug_tooling_metadata_token": None, "is_flipper_enabled": False, "theme_params": [], "bloks_version": "cb6ac324faea83da28649a4d5046c3a4f0486cb987f8ab769765e316b075a76c"},
        }
        return {"method": "post", "pretty": "false", "format": "json", "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch", "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.two_step_verification.verify_code.async", "fb_api_caller_class": "graphservice", "client_doc_id": "11994080423986492941384902285", "variables": json.dumps(variables), "fb_api_analytics_tags": '["GraphServices"]', "generate_session_cookies": "1", "client_trace_id": str(uuid.uuid4())}
    
    def login(self):
        variable = get_inf.create_vari(self._account)
        data = {"method": "post", "pretty": "false", "format": "json", "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch", "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.bloks.caa.login.async.send_login_request", "fb_api_caller_class": "graphservice", "client_doc_id": "11994080423986492941384902285", "variables": variable, "fb_api_analytics_tags": '["GraphServices"]', "client_trace_id": str(uuid.uuid4())}
        resp = self._session.post("https://b-graph.facebook.com/graphql", headers=self._build_headers(), data=data)
        resp.raise_for_status()
        text = resp.text
        
        if "two_step_verification_context" in text or "error_2fa" in text:
            if not self._account.authencation: raise Exception("Yêu cầu 2FA nhưng chưa nhập mã")
            ctx_match = re.search(r'two_step_verification_context.*?"([A-Za-z0-9_\-]{200,})', text)
            if not ctx_match: raise Exception("Không tìm thấy two_step_verification_context")
            two_step_context = ctx_match.group(1)
            mid_match = re.search(r'SaveMachineID[^A-Za-z0-9_-]+([A-Za-z0-9_-]{10,})', text)
            machine_id_2fa = mid_match.group(1) if mid_match else (self._account.machine_id or giai_str.tao_nn_c(22))
            self._call_2fa_entrypoint(two_step_context, machine_id_2fa)
            code = pyotp.TOTP(self._account.authencation).now()
            verify_payload = self._build_verify_payload(two_step_context, machine_id_2fa, code)
            verify_resp = self._session.post("https://b-graph.facebook.com/graphql", headers=self._build_headers(), data=verify_payload)
            verify_resp.raise_for_status()
            info = extractck_tk.extract_cookie_token(verify_resp.text.replace("\\", ""))
            self._account.cookie = info.cookie
            self._account.token = info.token
            return
        info = extractck_tk.extract_cookie_token(text.replace("\\", ""))
        self._account.cookie = info.cookie
        self._account.token = info.token
def extract_datr_from_cookie(cookie_str: str) -> str:
    if not cookie_str: return ""
    match = re.search(r'datr=([^;]+)', cookie_str)
    return match.group(1) if match else cookie_str

class FbPageCreator:
    def __init__(self, token, proxy=None, ua_mode="fixed", bloks_version=None, client_doc_id=None):
        self.token = token; self.proxy = proxy
        self.proxies = {"http": parse_proxy(proxy), "https": parse_proxy(proxy)} if proxy else None
        self.ua_mode = ua_mode; self.fixed_ua = gen_ua(seed=token) if ua_mode == "fixed" else None
        self.session = requests.Session(); self.session.verify = False; self.session.trust_env = False
        if self.proxies: self.session.proxies.update(self.proxies)
        self.mother_uid = ""; self.bloks_version = bloks_version or BLOKS_VERSIONING_ID; self.client_doc_id = client_doc_id or CLIENT_DOC_ID

    def _ua(self): return self.fixed_ua if self.ua_mode == "fixed" and self.fixed_ua else gen_ua()
    def _headers(self, friendly):
        return {"authorization": f"OAuth {self.token}", "x-fb-sim-hni": "45201", "x-fb-net-hni": "45201", "content-type": "application/x-www-form-urlencoded", "x-graphql-client-library": "graphservice", "x-tigon-is-retry": "False", "x-graphql-request-purpose": "fetch", "x-fb-device-group": "2878", "x-fb-friendly-name": friendly, "user-agent": self._ua(), "x-fb-connection-type": "WIFI", "x-fb-http-engine": "Tigon/Liger"}

    def get_user_info(self):
        try:
            r = self.session.get(f"https://graph.facebook.com/me?fields=id,name,picture.type(large)&access_token={self.token}", timeout=25).json()
            if isinstance(r, dict) and "id" in r:
                self.mother_uid = str(r["id"])
                avatar = r.get("picture", {}).get("data", {}).get("url", "")
                return {"success": True, "uid": str(r["id"]), "name": r.get("name", ""), "avatar": avatar}
            err = r.get("error") if isinstance(r, dict) else {}
            code = (err or {}).get("code", 0)
            return {"success": False, "is_token_die": code in FB_TOKEN_DEAD, "code": code, "message": (err or {}).get("message", "Token không hợp lệ")}
        except Exception as e:
            return {"success": False, "is_token_die": False, "code": NET, "message": str(e)[:80]}

    def _fb_fetch_profile_info(self, profile_id):
        variables = {
            'profile_switcher_connection_first': 300, 'additional_profile_picture_size': 80, 'profileID': str(profile_id),
            'main_profile_picture_size': 80, 'scale': '2',
            'nt_context': {'using_white_navbar': True, 'styles_id': '588d028b36bed0e1889e09b60e0f9aea', 'pixel_ratio': 2, 'is_push_on': True, 'debug_tooling_metadata_token': None, 'is_flipper_enabled': False, 'theme_params': [{'value': [], 'design_system_name': 'FDS'}], 'bloks_version': '338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d'},
            'overflow_recent_searches_filter_ids': [], 'use_native_entrypoint_for_stars_on_reels': True
        }
        payload = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true', 'locale': 'vi_VN', 'client_doc_id': '116912609015732060545213902280', 'variables': json.dumps(variables)}
        try:
            resp = self.session.post('https://b-graph.facebook.com/graphql', data=payload, headers=self._headers('ProfileSwitcherRootQuery'), timeout=15)
            return resp.json()
        except: return None

    def get_all_pages(self):
        pages_result = []
        try:
            r = self.session.get(f"https://graph.facebook.com/me/accounts?fields=id,name,access_token,picture.type(large)&access_token={self.token}&limit=100", timeout=25).json()
            pages_data = r.get("data", []) if isinstance(r, dict) else []
            
            if self.mother_uid:
                gql = self._fb_fetch_profile_info(self.mother_uid)
                if gql:
                    edges = gql.get('data', {}).get('user', {}).get('profile_switcher_eligible_profiles', {}).get('edges', [])
                    ps_map = []
                    for edge in edges:
                        node = edge.get('node', {})
                        profile = node.get('profile', {})
                        token_profile = node.get('session_info', {}).get('access_token', '')
                        p_id = str(profile.get('id', ''))
                        if p_id and token_profile and p_id != str(self.mother_uid):
                            ps_map.append({'id': p_id, 'name': profile.get('name', '').strip().lower(), 'token': token_profile})

                    for page in pages_data:
                        page_id = str(page.get("id", ""))
                        page_name = page.get("name", "").strip().lower()
                        real_uid = page_id
                        real_token = page.get("access_token")
                        for ps in ps_map:
                            if ps['name'] == page_name or ps['id'] == page_id:
                                real_uid = ps['id']; real_token = ps['token']; break
                        pages_result.append({
                            "id": real_uid, "name": page.get("name"), "token": real_token,
                            "avatar": page.get("picture", {}).get("data", {}).get("url", "")
                        })
                    return pages_result
            for page in pages_data:
                pages_result.append({
                    "id": str(page.get("id", "")), "name": page.get("name"), "token": page.get("access_token"),
                    "avatar": page.get("picture", {}).get("data", {}).get("url", "")
                })
            return pages_result
        except Exception:
            return pages_result

    def _get_new_page(self, page_name, response_text, retries=3):
        import time
        for attempt in range(retries):
            try: 
                r = self.session.get(f"https://graph.facebook.com/me/accounts?access_token={self.token}&limit=100", timeout=25).json()
            except Exception: 
                time.sleep(2); continue
                
            pages = (r.get("data") or []) if isinstance(r, dict) else []
            for p in pages:
                if p.get("name") == page_name and p.get("access_token"): return p
                
            candidate_ids = set(re.findall(r"\(bk\.action\.i64\.Const,\s*(\d{10,})\)", response_text or ""))
            for p in pages:
                if str(p.get("id")) in candidate_ids and p.get("access_token"): return p
                
            time.sleep(3)
        return None

    def create_page(self, page_name):
        p1 = {"client_input_params": {"name": page_name, "profile_plus_id": "0"}, "server_params": {"variant": 8, "referrer": "bookmark_create_action", "screen": "name", "INTERNAL__latency_qpl_marker_id": 36707139, "INTERNAL__latency_qpl_instance_id": 165401559700051, "creation_source": "android"}}
        v1 = {"params": {"params": json.dumps({"params": json.dumps(p1)}), "bloks_versioning_id": self.bloks_version, "app_id": "com.bloks.www.additional.profile.plus.creation.action.name.submit"}, "scale": "3", "nt_context": {"using_white_navbar": True, "styles_id": "c433035a5d4cdfd79b9c77d0bcd9006b", "pixel_ratio": 3, "is_push_on": True, "is_flipper_enabled": False, "theme_params": [], "bloks_version": self.bloks_version}}
        d1 = {"method": "post", "pretty": "false", "format": "json", "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch", "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.additional.profile.plus.creation.action.name.submit", "fb_api_caller_class": "graphservice", "client_doc_id": self.client_doc_id, "fb_api_client_context": json.dumps({"is_background": False}), "variables": json.dumps(v1), "fb_api_analytics_tags": json.dumps(["GraphServices"]), "client_trace_id": str(uuid.uuid4())}
        try:
            r1 = self.session.post(GRAPHQL_URL, headers=self._headers(d1["fb_api_req_friendly_name"]), data=d1, timeout=30)
            body1 = r1.text
            if "OAuthException" in body1 or r1.status_code == 401: return {"success": False, "is_token_die": True, "message": "Token DIE/hết hạn"}
            if "versioning_id" in body1.lower() and "invalid" in body1.lower(): return {"success": False, "message": "Bloks versioning_id lỗi thời"}
            if "tên này không hợp lệ" in body1.lower() or "name is invalid" in body1.lower(): return {"success": False, "is_name_invalid": True, "message": "Tên Page không hợp lệ"}
        except Exception as e: return {"success": False, "message": f"Lỗi bước 1: {e}"}

        p2 = {"client_input_params": {"entrypoint_logging_data": {"fb_profile_editing_session_entry_point": None, "field_edit_screen_entry_point": None}, "profile_plus_id": "0", "cp_upsell_declined": 0, "off_platform_creator_reachout_id": "", "session_id": None, "category_ids": ["2700", "2201"], "nav_chain": "com.bloks.www.additional.profile.plus.creation,com.bloks.www.additional.profile.plus.creation"}, "server_params": {"referrer": "bookmark_create_action", "INTERNAL__latency_qpl_marker_id": 36707139, "creation_source": "android", "name": page_name, "variant": 8, "screen": "category", "INTERNAL__latency_qpl_instance_id": 165462278000063}}
        v2 = {"params": {"params": json.dumps({"params": json.dumps(p2)}), "bloks_versioning_id": self.bloks_version, "app_id": "com.bloks.www.additional.profile.plus.creation.action.category.submit"}, "scale": "3", "nt_context": {"using_white_navbar": True, "styles_id": "c433035a5d4cdfd79b9c77d0bcd9006b", "pixel_ratio": 3, "is_push_on": True, "is_flipper_enabled": False, "theme_params": [], "bloks_version": self.bloks_version}}
        d2 = {"method": "post", "pretty": "false", "format": "json", "server_timestamps": "true", "locale": "vi_VN", "purpose": "fetch", "fb_api_req_friendly_name": "FbBloksActionRootQuery-com.bloks.www.additional.profile.plus.creation.action.category.submit", "fb_api_caller_class": "graphservice", "client_doc_id": self.client_doc_id, "fb_api_client_context": json.dumps({"is_background": False}), "variables": json.dumps(v2), "fb_api_analytics_tags": json.dumps(["GraphServices"]), "client_trace_id": str(uuid.uuid4())}
        try:
            r2 = self.session.post(GRAPHQL_URL, headers=self._headers(d2["fb_api_req_friendly_name"]), data=d2, timeout=30)
            body2 = r2.text
            if "OAuthException" in body2 or r2.status_code == 401 or "Session expired" in body2: return {"success": False, "is_token_die": True, "message": "Token DIE/hết hạn"}
            if "tạo quá nhiều Trang" in body2.lower() or "too many" in body2.lower(): return {"success": False, "is_limit": True, "message": "Bị limit tạo Page"}
            if "versioning_id" in body2.lower() and "invalid" in body2.lower(): return {"success": False, "message": "Bloks versioning_id lỗi thời"}
            if '"severity":"CRITICAL"' in body2 or "field_exception" in body2 or '"fb_bloks_action":null' in body2:
                chk = self.get_user_info()
                if not chk["success"] and chk.get("is_token_die"): return {"success": False, "is_token_die": True, "message": f"Nick mẹ DIE: {chk.get('message')}"}
                return {"success": False, "is_restricted": True, "message": "Nick mẹ bị chặn tạo Page (CRITICAL)"}
        except Exception as e: return {"success": False, "message": f"Lỗi bước 2: {e}"}

        page = self._get_new_page(page_name, body2)
        if not page: return {"success": False, "message": "Bloks OK nhưng không tìm thấy page"}
        return {"success": True, "page_id": str(page.get("id", "")), "page_name": str(page.get("name", page_name)), "page_token": str(page.get("access_token", "")), "mother_uid": self.mother_uid}

    def upload_media(self, page_id, page_token, media_type="avatar"):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        if media_type == "avatar":
            sources = [
                f"https://i.pravatar.cc/1000?u={uuid.uuid4()}",
                f"https://randomuser.me/api/portraits/men/{random.randint(1, 99)}.jpg",
                f"https://randomuser.me/api/portraits/women/{random.randint(1, 99)}.jpg",
                f"https://thispersondoesnotexist.com/?u={uuid.uuid4()}"
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
            except Exception: pass
            
        if not img_bytes:
            return {"success": False, "message": "Không tải được ảnh từ mọi nguồn"}

        try:
            if media_type == "avatar":
                r = self.session.post(
                    f"https://graph.facebook.com/v19.0/{page_id}/picture",
                    data={"access_token": page_token},
                    files={"source": ("avatar.jpg", img_bytes, "image/jpeg")},
                    timeout=30
                ).json()
                if "error" in r: return {"success": False, "message": r["error"].get("message", "Lỗi FB API")}
                return {"success": True}
                
            elif media_type == "cover":
                r1 = self.session.post(
                    f"https://graph.facebook.com/v19.0/{page_id}/photos",
                    data={"published": "false", "access_token": page_token},
                    files={"source": ("cover.jpg", img_bytes, "image/jpeg")},
                    timeout=30
                ).json()
                if "error" in r1: return {"success": False, "message": r1["error"].get("message", "Lỗi upload ảnh")}
                
                r2 = self.session.post(
                    f"https://graph.facebook.com/v19.0/{page_id}",
                    data={"cover": r1["id"], "access_token": page_token},
                    timeout=30
                ).json()
                if "error" in r2: return {"success": False, "message": r2["error"].get("message", "Lỗi set cover")}
                return {"success": True}
                
        except Exception as e:
            return {"success": False, "message": str(e)[:80]}

    def post_welcome(self, page_id, page_token):
        try:
            payload = {"message": "Chào mừng mọi người đến với Page! Hãy ấn theo dõi để cập nhật những thông tin mới nhất nhé!", "access_token": page_token}
            r = self.session.post(f"https://graph.facebook.com/v19.0/{page_id}/feed", data=payload, timeout=30).json()
            if "error" in r: return {"success": False, "message": r["error"].get("message", "Lỗi FB API")}
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)[:80]}
class State:
    def __init__(self):
        self.lock = threading.RLock(); self.start_ts = time.time()
        self.total_ok = 0; self.total_die = 0; self.total_limit = 0; self.total_err = 0
        self.accounts = {}; self.logs = []; self._fh_lock = threading.Lock(); self._writes = 0
    def acc(self, token):
        if token not in self.accounts:
            self.accounts[token] = {"token": token, "name": "", "uid": "", "proxy": None, "avatar": "", "pages_created": 0, "target": 1, "status": "idle", "current_action": "", "last_result": "", "since": time.time(), "until": None, "note": "", "page_list": []}
        return self.accounts[token]
    def set_status(self, token, status, action="", until=None, note=""):
        with self.lock:
            a = self.acc(token)
            if a["status"] != status: a["status"] = status; a["since"] = time.time()
            a["current_action"] = action; a["until"] = until
            if note: a["note"] = note
    def log(self, lvl, who, text):
        with self.lock:
            self.logs.append({"t": time.time(), "lvl": lvl, "who": who, "text": text})
            if len(self.logs) > 500: del self.logs[:100]
        self._write_file(lvl, who, text)
    def _write_file(self, lvl, who, text):
        try:
            line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {lvl.upper():4} [{who}] {text}\n"
            with self._fh_lock:
                self._writes += 1
                if self._writes % 200 == 0 and os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 2_000_000: os.replace(LOG_FILE, LOG_FILE + ".old")
                with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line)
        except Exception: pass

state = State()
ACC_LOCK = threading.RLock()
RUNNER = {"running": False, "stop_ev": None, "threads": []}
RUNNER_LOCK = threading.Lock()
CFG = {"tokens": [], "selected_tokens": [], "name_type": "viet", "custom_names": [], "pages_per_nick": 1, "delay_between": 10, "ua_mode": "fixed", "threads": 3, "limit_action": "stop", "limit_cooldown": 300, "bloks_version": BLOKS_VERSIONING_ID, "client_doc_id": CLIENT_DOC_ID, "auto_avatar": True, "auto_cover": True, "auto_post": True, "delay_before_media": 5}

def load_cfg():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f: d = json.load(f)
        if isinstance(d, dict):
            for k in CFG:
                if k in d: CFG[k] = d[k]
    except Exception: pass

def save_cfg():
    with ACC_LOCK:
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(CFG, f, indent=2, ensure_ascii=False)
        try: os.chmod(tmp, 0o600)
        except Exception: pass
        os.replace(tmp, CONFIG_FILE)

def parse_tokens_from_text(text):
    out = []; seen = set()
    for line in str(text).splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = [p.strip() for p in line.split("|")]
        
        token = None; proxy = None; acc_data = None
        
        m = re.search(r"(EAAAAU[A-Za-z0-9]{20,})", parts[0])
        if m:
            token = m.group(1)
            if len(parts) > 1 and parse_proxy(parts[1]): proxy = parts[1]
        else:
            if len(parts) >= 2 and parts[0].isdigit():
                uid = parts[0]; pwd = parts[1]; tfa = None
                
                if len(parts) == 3:
                    if parse_proxy(parts[2]): proxy = parts[2]
                    else: tfa = parts[2]
                elif len(parts) >= 4:
                    tfa = parts[2]
                    if parse_proxy(parts[3]): proxy = parts[3]
                
                acc_data = {"uid": uid, "pwd": pwd, "tfa": tfa}
        
        if token and token not in seen:
            seen.add(token)
            out.append({"type": "token", "token": token, "proxy": proxy})
        elif acc_data and acc_data["uid"] not in seen:
            seen.add(acc_data["uid"])
            out.append({"type": "login", "uid": acc_data["uid"], "pwd": acc_data["pwd"], "tfa": acc_data["tfa"], "proxy": proxy})
            
    return out

def mask_token(t): return (t[:6] + "…" + t[-4:]) if len(t) > 12 else "•••"
def token_key(t): return hashlib.sha1(t.encode()).hexdigest()[:16]

def check_token_bg(item):
    tk_or_uid = item.get("token") or item.get("uid")
    px = item.get("proxy")
    
    if item["type"] == "login":
        with state.lock: state.set_status(tk_or_uid, "checking", "Đang đăng nhập B-api...")
        acc_info = InforN()
        acc_info.uid = item["uid"]; acc_info.password = item["pwd"]; acc_info.authencation = item["tfa"]
        try:
            svc = LoginService(acc_info, proxy=px)
            svc.login()
            if not acc_info.token: raise Exception("Không lấy được token")
            item["token"] = acc_info.token 
        except Exception as e:
            with state.lock:
                a = state.acc(tk_or_uid)
                a["status"] = "die"; a["note"] = str(e)[:80]
            return

    creator = FbPageCreator(item["token"], proxy=px)
    info = creator.get_user_info()
    with state.lock:
        a = state.acc(item["token"])
        if info["success"]:
            a["name"] = info["name"] or info["uid"]; a["uid"] = info["uid"]; a["avatar"] = info["avatar"]
            a["status"] = "idle"; a["current_action"] = "Sẵn sàng"
            a["page_list"] = creator.get_all_pages()
        else:
            a["status"] = "die" if info.get("is_token_die") else "error"; a["note"] = info.get("message", "Lỗi check")[:80]
def process_account(acc, stop_ev, cfg_snapshot):
    token = acc["token"]
    creator = FbPageCreator(token=token, proxy=acc["proxy"], ua_mode=cfg_snapshot["ua_mode"], bloks_version=cfg_snapshot["bloks_version"], client_doc_id=cfg_snapshot["client_doc_id"])
    state.set_status(token, "checking", "Đang kiểm tra token...")
    info = creator.get_user_info()
    if not info["success"]:
        if info.get("is_token_die"):
            state.set_status(token, "die", "", note=info["message"][:80]); state.total_die += 1; return
        if stop_ev.wait(5): return
        info = creator.get_user_info()
        if not info["success"]: state.set_status(token, "error", "", note=info["message"][:80]); return

    acc["uid"] = info["uid"]; acc["name"] = info["name"] or info["uid"]; acc["avatar"] = info["avatar"]
    state.acc(token)["name"] = acc["name"]; state.acc(token)["uid"] = acc["uid"]; state.acc(token)["avatar"] = acc["avatar"]
    state.log("info", acc["name"], f"Bắt đầu (UID {acc['uid']}) · target {acc['target']} page")

    custom_names = cfg_snapshot.get("custom_names") or []
    while not stop_ev.is_set() and acc["pages_created"] < acc["target"]:
        cur = acc["pages_created"] + 1
        page_name = get_page_name(cfg_snapshot["name_type"], custom_names)
        state.set_status(token, "working", f"Đang tạo ({cur}/{acc['target']}): '{page_name}'...")
        res = creator.create_page(page_name)

        if res.get("success"):
            p_id = res["page_id"]; p_token = res["page_token"]; p_name = res["page_name"]
            
            wait_time = float(cfg_snapshot.get("delay_before_media", 5))
            if wait_time > 0:
                state.set_status(token, "working", f"Chờ {wait_time:.0f}s cho FB khởi tạo page...")
                if stop_ev.wait(wait_time): return

            if cfg_snapshot.get("auto_avatar", True) and p_token:
                state.set_status(token, "working", f"Đang up avatar '{p_name}'...")
                av_res = creator.upload_media(p_id, p_token, "avatar")
                if av_res.get("success"): state.log("ok", acc["name"], f"Đã up avatar '{p_name}'")
                else: state.log("warn", acc["name"], f"Lỗi up avatar: {av_res.get('message')}")

            if cfg_snapshot.get("auto_cover", True) and p_token:
                state.set_status(token, "working", f"Đang up bìa '{p_name}'...")
                cv_res = creator.upload_media(p_id, p_token, "cover")
                if cv_res.get("success"): state.log("ok", acc["name"], f"Đã up bìa '{p_name}'")
                else: state.log("warn", acc["name"], f"Lỗi up bìa: {cv_res.get('message')}")

            if cfg_snapshot.get("auto_post", True) and p_token:
                state.set_status(token, "working", f"Đang đăng bài '{p_name}'...")
                post_res = creator.post_welcome(p_id, p_token)
                if post_res.get("success"): state.log("ok", acc["name"], f"Đã đăng bài '{p_name}'")
                else: state.log("warn", acc["name"], f"Lỗi đăng bài: {post_res.get('message')}")

            acc["pages_created"] += 1; state.total_ok += 1
            state.acc(token)["pages_created"] = acc["pages_created"]; state.acc(token)["last_result"] = f"OK '{p_name}'"
            
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f: f.write(f"{p_id}|{p_name}|{p_token}|{acc['uid']}|{ts}\n")
            except Exception: pass
            
            state.acc(token)["page_list"] = creator.get_all_pages()
            
            state.log("ok", acc["name"], f"Tạo '{p_name}' → ID {p_id}")
            if acc["pages_created"] >= acc["target"]: state.set_status(token, "done", f"Hoàn thành {acc['target']}/{acc['target']} page"); return
            delay = float(cfg_snapshot["delay_between"])
            if delay > 0:
                state.set_status(token, "delay", f"Nghỉ {delay:.0f}s", until=time.time() + delay)
                if stop_ev.wait(delay): return
            continue

        if res.get("is_token_die") or res.get("is_restricted"):
            state.set_status(token, "die", "", note=res.get("message", "")[:80]); state.total_die += 1; return
        if res.get("is_name_invalid"):
            state.log("warn", acc["name"], f"Tên '{page_name}' bị reject"); stop_ev.wait(2); continue
        if res.get("is_limit"):
            state.total_limit += 1
            if cfg_snapshot["limit_action"] == "stop":
                state.set_status(token, "limit", "", note="Bị limit"); return
            cd = int(cfg_snapshot["limit_cooldown"])
            state.set_status(token, "delay", f"Bị limit - nghỉ {cd}s", until=time.time() + cd)
            if stop_ev.wait(cd): return
            continue

        state.total_err += 1; msg = res.get("message", "Lỗi")[:60]; state.set_status(token, "error", "", note=msg)
        state.log("err", acc["name"], f"Lỗi: {msg}"); stop_ev.wait(15)

def _worker_loop(q, stop_ev, cfg_snapshot):
    while not stop_ev.is_set():
        try: token = q.get(timeout=1)
        except Empty: return
        if stop_ev.is_set(): return
        process_account(state.acc(token), stop_ev, cfg_snapshot)

def runner_start(tokens):
    global RUNNER
    with RUNNER_LOCK:
        if RUNNER["running"]: return 0, "Đang chạy rồi"
        cfg_snapshot = {"name_type": CFG["name_type"], "custom_names": list(CFG.get("custom_names") or []), "pages_per_nick": int(CFG["pages_per_nick"]), "delay_between": float(CFG["delay_between"]), "ua_mode": CFG["ua_mode"], "limit_action": CFG["limit_action"], "limit_cooldown": int(CFG["limit_cooldown"]), "bloks_version": CFG["bloks_version"], "client_doc_id": CFG["client_doc_id"], "auto_avatar": CFG.get("auto_avatar", True), "auto_cover": CFG.get("auto_cover", True), "auto_post": CFG.get("auto_post", True), "delay_before_media": float(CFG.get("delay_before_media", 5))}
        stop_ev = threading.Event(); q = Queue(); parsed = parse_tokens_from_text("\n".join(tokens))
        for it in parsed:
            tk = it.get("token") or it.get("uid")
            acc = state.acc(tk); acc["proxy"] = it["proxy"]; acc["target"] = cfg_snapshot["pages_per_nick"]; acc["pages_created"] = 0
            state.set_status(tk, "idle", "Đang chờ..."); q.put(tk)
        threads = []
        for _ in range(max(1, min(int(CFG["threads"]), len(parsed)))):
            t = threading.Thread(target=_worker_loop, args=(q, stop_ev, cfg_snapshot), daemon=True); t.start(); threads.append(t)
        RUNNER = {"running": True, "stop_ev": stop_ev, "threads": threads}
        return len(threads), None

def runner_stop():
    with RUNNER_LOCK:
        if not RUNNER["running"]: return 0
        RUNNER["stop_ev"].set(); n = len([t for t in RUNNER["threads"] if t.is_alive()]); RUNNER["running"] = False; return n

def runner_check_done():
    with RUNNER_LOCK:
        if RUNNER["running"] and not any(t.is_alive() for t in RUNNER["threads"]): RUNNER["running"] = False

def snapshot():
    runner_check_done(); now = time.time()
    with state.lock:
        accounts = []
        for tk, a in state.accounts.items():
            accounts.append({"token": tk, "token_mask": mask_token(tk), "token_key": token_key(tk), "name": a["name"], "uid": a["uid"], "proxy": bool(a["proxy"]), "pages_created": a["pages_created"], "target": a["target"], "status": a["status"], "current_action": a["current_action"], "last_result": a["last_result"], "since": a["since"], "until": a["until"], "note": a["note"], "avatar": a["avatar"], "page_list": a.get("page_list", []), "selected": tk in CFG.get("selected_tokens", [])})
        logs = state.logs[-100:]; tot = {"ok": state.total_ok, "die": state.total_die, "limit": state.total_limit, "err": state.total_err}; uptime = now - state.start_ts
    return {"now": now, "uptime": uptime, "running": RUNNER["running"], "accounts": accounts, "logs": logs, "totals": tot, "cfg": {k: CFG[k] for k in CFG if k not in ("custom_names", "selected_tokens")}, "tokens": [{"mask": mask_token(t.split("|")[0]), "line": t} for t in CFG["tokens"]]}

class ApiError(Exception):
    def __init__(self, msg, code=400): super().__init__(msg); self.code = code

def r_config(b):
    for k in ["name_type", "pages_per_nick", "delay_between", "threads", "ua_mode", "limit_action", "limit_cooldown", "bloks_version", "client_doc_id", "delay_before_media"]:
        if k in b:
            if k in ["pages_per_nick", "threads", "limit_cooldown"]: CFG[k] = int(b[k])
            elif k in ["delay_between", "delay_before_media"]: CFG[k] = float(b[k])
            else: CFG[k] = b[k]
    if "auto_avatar" in b: CFG["auto_avatar"] = bool(b["auto_avatar"])
    if "auto_cover" in b: CFG["auto_cover"] = bool(b["auto_cover"])
    if "auto_post" in b: CFG["auto_post"] = bool(b["auto_post"])
    if "custom_names" in b: CFG["custom_names"] = [str(x).strip() for x in (b["custom_names"].splitlines() if isinstance(b["custom_names"], str) else b["custom_names"]) if str(x).strip()]
    save_cfg(); return {"ok": True}

def r_start(b):
    with state.lock:
        if RUNNER["running"]: raise ApiError("Đang chạy rồi")
    target_token = b.get("token")
    tokens = [target_token] if target_token else [t for t in CFG["tokens"] if t.split("|")[0] in CFG.get("selected_tokens", [])] if CFG.get("selected_tokens") else CFG["tokens"]
    if not tokens: raise ApiError("Không có token nào")
    n, err = runner_start(tokens)
    if err: raise ApiError(err)
    return {"ok": True, "threads": n}

def r_stop(b): return {"ok": True, "stopped": runner_stop()}

def r_toggle(b):
    tk = b.get("token"); on = bool(b.get("selected", True))
    with ACC_LOCK:
        sel = CFG.setdefault("selected_tokens", [])
        if on and tk not in sel: sel.append(tk)
        elif not on and tk in sel: sel.remove(tk)
        save_cfg()
    return {"ok": True}

def r_check(b):
    tk_line = b.get("token"); tk = tk_line.split("|")[0]; px = tk_line.split("|")[1] if "|" in tk_line else None
    threading.Thread(target=check_token_bg, args=({"type": "token", "token": tk, "proxy": px},), daemon=True).start()
    return {"ok": True}

def r_page_action(b):
    pid = b.get("pid"); ptk = b.get("ptk"); act = b.get("action")
    creator = FbPageCreator(token="", proxy=None) 
    res = {"success": False, "message": "Hành động không hợp lệ"}
    if act == "avatar": res = creator.upload_media(pid, ptk, "avatar")
    elif act == "cover": res = creator.upload_media(pid, ptk, "cover")
    elif act == "post": res = creator.post_welcome(pid, ptk)
    
    if res.get("success"): return {"ok": True}
    raise ApiError(res.get("message", "Lỗi"))

def r_add_tokens(b):
    parsed = parse_tokens_from_text(b.get("text", ""))
    if not parsed: raise ApiError("Không tìm thấy dữ liệu hợp lệ")
    added = []
    with ACC_LOCK:
        have = {re.search(r"(EAAAAU[A-Za-z0-9]{20,})", l).group(1) for l in CFG["tokens"] if re.search(r"(EAAAAU[A-Za-z0-9]{20,})", l)}
        for p in parsed:
            tk_id = p.get("token") or p.get("uid")
            if tk_id in have: continue
            line = f"{p['token']}|{p['proxy']}" if p["type"] == "token" and p["proxy"] else (p["token"] if p["type"] == "token" else f"{p['uid']}|{p['pwd']}" + (f"|{p['tfa']}" if p['tfa'] else "") + (f"|{p['proxy']}" if p['proxy'] else ""))
            CFG["tokens"].append(line); CFG.setdefault("selected_tokens", []).append(tk_id); have.add(tk_id); added.append(p)
        save_cfg()
    for p in added:
        threading.Thread(target=check_token_bg, args=(p,), daemon=True).start()
    return {"ok": True, "added": len(added), "total": len(CFG["tokens"])}

def r_remove_token(b):
    idx = int(b.get("index", -1))
    with ACC_LOCK:
        if not (0 <= idx < len(CFG["tokens"])): raise ApiError("index sai")
        removed = CFG["tokens"].pop(idx); tk = removed.split("|")[0]
        if "selected_tokens" in CFG and tk in CFG["selected_tokens"]: CFG["selected_tokens"].remove(tk)
        save_cfg()
    return {"ok": True}

def r_clear_tokens(b):
    with ACC_LOCK: CFG["tokens"] = []; CFG["selected_tokens"] = []; save_cfg()
    return {"ok": True}

def r_read_output(b):
    try:
        if not os.path.exists(OUTPUT_FILE): return {"ok": True, "content": "", "lines": 0}
        with open(OUTPUT_FILE, "r", encoding="utf-8", errors="replace") as f: content = f.read()
        return {"ok": True, "content": content, "lines": content.count("\n")}
    except Exception as e: return {"ok": False, "msg": str(e)}

def r_clear_output(b):
    try:
        if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
        return {"ok": True}
    except Exception as e: return {"ok": False, "msg": str(e)}

def r_reset_state(b):
    with state.lock: state.total_ok = state.total_die = state.total_limit = state.total_err = 0; state.accounts.clear(); state.logs.clear()
    return {"ok": True}

ROUTES = {"/api/config": r_config, "/api/start": r_start, "/api/stop": r_stop, "/api/toggle": r_toggle, "/api/check": r_check, "/api/tokens/add": r_add_tokens, "/api/tokens/remove": r_remove_token, "/api/tokens/clear": r_clear_tokens, "/api/output": r_read_output, "/api/output/clear": r_clear_output, "/api/reset": r_reset_state, "/api/page_action": r_page_action}

class Handler(BaseHTTPRequestHandler):
    server_version = "RegPageWeb"
    def log_message(self, *a): pass
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)): body = json.dumps(body, ensure_ascii=True)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-store"); self.send_header("X-Frame-Options", "DENY")
        if ctype.startswith("text/html"): self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'")
        self.end_headers(); self.wfile.write(data)
    def _guard(self, parsed):
        host_hdr = self.headers.get("Host", ""); host = host_hdr.rsplit(":", 1)[0]
        if self.server.allowed_hosts is not None and host not in self.server.allowed_hosts: self._send(403, {"error": "Host"}); return False
        if self.server.key:
            supplied = self.headers.get("X-Key") or parse_qs(parsed.query).get("key", [""])[0]
            if not hmac.compare_digest(str(supplied).encode(), self.server.key.encode()): self._send(401, {"error": "Sai key"}); return False
        return True
    def do_GET(self):
        p = urlparse(self.path)
        if not self._guard(p): return
        if p.path == "/": self._send(200, INDEX_HTML, "text/html; charset=utf-8")
        elif p.path == "/api/state": self._send(200, snapshot())
        else: self._send(404, {"error": "Not found"})
    def do_POST(self):
        p = urlparse(self.path)
        if not self._guard(p): return
        fn = ROUTES.get(p.path)
        if not fn: self._send(404, {"error": "Not found"}); return
        try: n = int(self.headers.get("Content-Length", "0"))
        except ValueError: n = 0
        try: body = json.loads(self.rfile.read(n) or b"{}")
        except Exception: self._send(400, {"error": "JSON lỗi"}); return
        try: self._send(200, fn(body))
        except ApiError as e: self._send(e.code, {"error": str(e)})
        except Exception as e: self._send(500, {"error": f"Lỗi server: {e}"})

def make_server(host, port, key="", tries=20):
    busy = {errno.EADDRINUSE}
    srv, last = None, None
    for p in range(port, port + tries):
        try: srv = ThreadingHTTPServer((host, p), Handler); break
        except OSError as e:
            last = e
            if e.errno not in busy: raise
    if srv is None: raise last
    srv.daemon_threads = True; srv.key = key or ""; srv.allowed_hosts = {"127.0.0.1", "localhost", "[::1]"} if host in ("127.0.0.1", "localhost", "::1") else None
    return srv
INDEX_HTML = r'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reg Page Web v5</title>
<style>
:root{--bg:#f4f6fb;--card:#fff;--tx:#1b2430;--mut:#6b7686;--bd:#e3e8f0;--pri:#2f6bff;--ok:#12a150;--err:#d93636;--warn:#b87a00;--info:#0e8fb3}
@media(prefers-color-scheme:dark){:root{--bg:#0f1319;--card:#1a212b;--tx:#e8edf3;--mut:#93a0b1;--bd:#2a3340;--pri:#5b8cff;--ok:#3ccf7d;--err:#ff6b6b;--warn:#f2b13d;--info:#4cc3e6}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding-bottom:64px}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--bd);padding:10px 12px 0}
.top{display:flex;align-items:center;justify-content:space-between;gap:8px}.top b{font-size:16px}
.dot{width:9px;height:9px;border-radius:50%;background:var(--err);display:inline-block;margin-right:6px}.dot.on{background:var(--ok)}
.tabs{display:flex;gap:6px;overflow-x:auto;padding:10px 0}
.tab{border:1px solid var(--bd);background:var(--bg);color:var(--tx);padding:8px 14px;border-radius:999px;font-weight:600;white-space:nowrap;cursor:pointer;font-size:13px}
.tab.on{background:var(--pri);border-color:var(--pri);color:#fff}
main{padding:12px;max-width:1000px;margin:0 auto}.pane{display:none}.pane.on{display:block}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:12px}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.btn{border:1px solid var(--bd);background:var(--card);color:var(--tx);padding:9px 14px;border-radius:10px;font-weight:600;cursor:pointer;font-size:14px}
.btn.pri{background:var(--pri);border-color:var(--pri);color:#fff}.btn.danger{background:var(--err);border-color:var(--err);color:#fff}.btn.ok{background:var(--ok);border-color:var(--ok);color:#fff}
.btn.sm{padding:5px 10px;font-size:12px}.btn:disabled{opacity:.5;cursor:not-allowed}
input,select,textarea{width:100%;padding:9px 10px;border:1px solid var(--bd);border-radius:10px;background:var(--bg);color:var(--tx);font:inherit}
textarea{min-height:100px;font-family:ui-monospace,monospace;font-size:12px}
label{display:block;font-weight:600;margin:10px 0 4px;font-size:13px}
small,.mut{color:var(--mut);font-size:12px}.mono{font-family:ui-monospace,monospace;font-size:12px}
.acc{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:14px;margin-bottom:12px;cursor:pointer}
.acc:hover{border-color:var(--pri)}
.acc.sel{border-color:var(--ok);box-shadow:0 0 0 2px rgba(18,161,80,.15)}
.acc-head{display:flex;align-items:flex-start;gap:10px}
.acc-avatar{width:52px;height:52px;border-radius:50%;background:var(--bd);display:flex;align-items:center;justify-content:center;flex:none;font-weight:700;font-size:20px;color:var(--mut);overflow:hidden}
.acc-avatar img{width:100%;height:100%;object-fit:cover}
.acc-info{flex:1;min-width:0}
.acc-info .nm{font-weight:700;font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.acc-info .uid{font-size:12px;color:var(--ok);font-family:ui-monospace,monospace}
.acc-info .tk{font-size:11px;color:var(--mut);font-family:ui-monospace,monospace}
.acc-actions{display:flex;gap:6px;flex:none}
.icon-btn{width:36px;height:36px;border-radius:50%;border:1px solid var(--bd);background:var(--bg);color:var(--tx);cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}
.icon-btn.danger{color:var(--err)}
.acc-check{display:flex;align-items:center;gap:8px;margin-top:10px;padding-top:10px;border-top:1px solid var(--bd)}
.acc-check input[type=checkbox]{width:20px;height:20px;cursor:pointer}
.acc-check label{font-weight:600;margin:0;font-size:13px;cursor:pointer}
.acc-toolbar{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.acc-toolbar .btn{padding:8px 4px;font-size:12px;font-weight:600}
.acc-status{margin-top:10px;padding:8px 10px;border-radius:8px;background:var(--bg);font-size:12px}
.acc-status .st-lbl{font-weight:700}.acc-status .st-sub{color:var(--mut);margin-top:2px;font-family:ui-monospace,monospace;font-size:11px}
.acc-status .bar{height:4px;background:var(--bd);border-radius:2px;overflow:hidden;margin-top:6px}
.acc-status .bar > div{height:100%;background:var(--pri);transition:width .3s}.acc-status .bar.done > div{background:var(--ok)}.acc-status .bar.die > div{background:var(--err)}
.pages-section{margin-top:10px;border-top:1px dashed var(--bd);padding-top:10px}
.pages-header{display:flex;align-items:center;justify-content:space-between;cursor:pointer}
.pages-header .title{font-weight:700;font-size:14px}
.pages-header .arrow{font-size:16px;transition:transform 0.2s;color:var(--mut)}
.pages-header .arrow.open{transform:rotate(180deg)}
.pages-list{display:none;margin-top:10px;flex-direction:column;gap:8px}
.pages-list.open{display:flex}
.page-item{display:flex;align-items:center;gap:10px;background:var(--bg);border:1px solid var(--bd);border-radius:10px;padding:8px 10px}
.page-item .p-avatar{width:36px;height:36px;border-radius:50%;background:var(--bd);display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--mut);flex:none;overflow:hidden}
.page-item .p-avatar img{width:100%;height:100%;object-fit:cover}
.page-item .p-info{flex:1;min-width:0}
.page-item .p-name{font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.page-item .p-uid{font-size:11px;color:var(--mut);font-family:ui-monospace,monospace}
.page-item .p-actions{display:flex;gap:6px}
.page-item .icon-btn{width:28px;height:28px;font-size:13px}
.kpi{background:var(--bg);border:1px solid var(--bd);border-radius:10px;padding:10px}.kpi small{display:block;font-size:11px}.kpi b{font-size:20px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:12px}@media(max-width:520px){.kpis{grid-template-columns:repeat(2,1fr)}}
.c-ok{color:var(--ok);font-weight:700}.c-err{color:var(--err);font-weight:700}.c-warn{color:var(--warn);font-weight:700}.c-info{color:var(--info);font-weight:700}.c-mut{color:var(--mut)}
.log{font:12px/1.5 ui-monospace,monospace;padding:4px 0;border-bottom:1px dashed var(--bd);word-break:break-word}
.empty{padding:24px;text-align:center;color:var(--mut)}
.tk-row{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--bd);font-family:ui-monospace,monospace;font-size:12px}
.tk-row:last-child{border-bottom:0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media(max-width:520px){.grid2{grid-template-columns:1fr}}
.warn{background:rgba(184,122,0,.1);border:1px solid var(--warn);border-radius:8px;padding:10px;margin-bottom:10px;font-size:13px}
.outbox{background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:10px;max-height:60vh;overflow:auto;font:12px/1.5 ui-monospace,monospace;white-space:pre-wrap;word-break:break-all}
footer{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--bd);padding:10px 12px;display:flex;gap:14px;justify-content:center;font-weight:600;font-size:13px;flex-wrap:wrap}
#toast{position:fixed;left:50%;transform:translateX(-50%);bottom:76px;background:#222;color:#fff;padding:9px 14px;border-radius:10px;opacity:0;pointer-events:none;transition:opacity .2s;max-width:90vw;z-index:30}#toast.show{opacity:.95}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;z-index:20;padding:16px}
.modal.show{display:flex}.mbox{background:var(--card);border-radius:14px;padding:16px;width:100%;max-width:460px}
</style></head><body>
<header><div class="top"><b>Reg Page Web v5</b><span class="mut"><span class="dot" id="dot"></span><span id="conn">đang kết nối…</span></span></div>
<div class="tabs" id="tabs">
<button class="tab on" data-tab="acc">Tài khoản</button>
<button class="tab" data-tab="cfg">Cấu hình</button>
<button class="tab" data-tab="out">Output</button>
<button class="tab" data-tab="log">Log</button>
</div></header>
<main>
<section class="pane on" id="p-acc">
<div class="kpis" id="kpis"></div>
<div class="row">
<button class="btn ok" id="bStart">▶ Bắt đầu (acc đã tích)</button>
<button class="btn danger" id="bStop">■ Dừng</button>
<button class="btn" id="bCheckAll">⟳ Check tất cả</button>
<button class="btn" id="bReset">↺ Reset state</button>
</div>
<div id="acclist"></div>
</section>
<section class="pane" id="p-cfg">
<div class="card">
<b>Token Facebook / Tài khoản</b> <small id="tkCount"></small>
<div id="tklist"></div>
<label for="tkAdd">Thêm dữ liệu (Mỗi dòng 1 acc. Hỗ trợ: EAAAAU... | EAAAAU...|proxy | UID|pass | UID|pass|2fa | UID|pass|2fa|proxy)</label>
<textarea id="tkAdd" placeholder="EAAAAU...&#10;6159...|matkhau123&#10;6159...|matkhau123|2FA_KEY|ip:port:user:pass"></textarea>
<div class="row" style="margin-top:10px"><button class="btn pri" id="bAdd">Thêm</button><button class="btn danger" id="bClear">Xóa tất cả</button></div>
</div>
<div class="card">
<b>Cài đặt reg page</b>
<div class="grid2">
<div><label for="cName">Loại tên Page</label><select id="cName"><option value="viet">Tên Việt</option><option value="us">Tên US / Quốc tế</option><option value="custom">Custom (từ danh sách)</option></select></div>
<div><label for="cPages">Số page / nick</label><input type="number" id="cPages" min="1" max="1000" step="1"></div>
<div><label for="cDelay">Nghỉ giữa page (giây)</label><input type="number" id="cDelay" min="0" max="3600" step="1"></div>
<div><label for="cThreads">Số luồng</label><input type="number" id="cThreads" min="1" max="20" step="1"></div>
<div><label for="cUA">Chế độ User-Agent</label><select id="cUA"><option value="fixed">Cố định / nick (khuyến nghị)</option><option value="random">Random / page</option></select></div>
<div><label for="cLimit">Xử lý khi bị limit</label><select id="cLimit"><option value="stop">Dừng nick</option><option value="cooldown">Nghỉ rồi thử lại</option></select></div>
<div><label for="cLimitCd">Cooldown khi limit (giây)</label><input type="number" id="cLimitCd" min="30" max="86400" step="1"></div>
<div><label for="cDelayMedia">Chờ trước khi up ảnh (giây)</label><input type="number" id="cDelayMedia" min="0" max="300" step="1"></div>
</div>
<div style="margin-top:15px; display:flex; flex-direction:column; gap:10px;">
<label style="display:flex;align-items:center;gap:8px;cursor:pointer;margin:0;"><input type="checkbox" id="cAvatar" style="width:20px;height:20px;margin:0;"> Tự động up Avatar AI (Pravatar)</label>
<label style="display:flex;align-items:center;gap:8px;cursor:pointer;margin:0;"><input type="checkbox" id="cCover" style="width:20px;height:20px;margin:0;"> Tự động up Ảnh bìa (Picsum)</label>
<label style="display:flex;align-items:center;gap:8px;cursor:pointer;margin:0;"><input type="checkbox" id="cPost" style="width:20px;height:20px;margin:0;"> Tự động đăng bài Welcome</label>
</div>
<label for="cNames" style="margin-top:15px;">Custom names (mỗi dòng 1 tên)</label><textarea id="cNames" placeholder="Nguyễn Văn A&#10;Trần Thị B"></textarea>
</div>
<div class="card">
<b>Bloks version (nâng cao)</b>
<div class="warn">⚠ Nếu tool báo "Bloks versioning_id lỗi thời" — cần extract bloks_versioning_id + client_doc_id mới.</div>
<label for="cBloks">BLOKS_VERSIONING_ID (64 hex)</label><input type="text" id="cBloks" class="mono">
<label for="cDoc">CLIENT_DOC_ID (số)</label><input type="text" id="cDoc" class="mono">
</div>
<div class="row"><button class="btn pri" id="bSave" style="width:100%">Lưu cấu hình</button></div>
</section>
<section class="pane" id="p-out">
<div class="row"><button class="btn" id="bReadOut">⟳ Đọc lại</button><button class="btn danger" id="bClearOut">Xóa file</button></div>
<div class="card"><small id="outInfo"></small><div class="outbox" id="outBox"></div></div>
</section>
<section class="pane" id="p-log">
<div class="row"><label style="margin:0;display:flex;align-items:center;gap:6px"><input type="checkbox" id="onlyErr" style="width:auto"> Chỉ cảnh báo/lỗi</label></div>
<div class="card" id="loglist"></div>
</section>
</main>
<footer id="foot"></footer>
<div id="toast"></div>
<div class="modal" id="tokenModal">
  <div class="mbox">
    <b id="mTitle">Thông tin Token</b>
    <div class="mut" id="mUid" style="margin-top:5px;font-size:13px"></div>
    <label for="mToken" style="margin-top:15px">Full Token / Cookie</label>
    <textarea id="mToken" readonly style="min-height:80px;font-size:14px;font-family:ui-monospace,monospace"></textarea>
    <div class="row" style="margin-top:15px">
      <button class="btn pri" id="mCopy" style="flex:1">📋 Copy Token</button>
      <button class="btn" id="mClose" style="flex:1">Đóng</button>
    </div>
  </div>
</div>
<script>
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KEY=new URLSearchParams(location.search).get('key')||'';
const ST={idle:['Chờ','c-mut'],checking:['Kiểm tra','c-info'],working:['Đang tạo','c-ok'],delay:['Nghỉ','c-warn'],done:['Hoàn thành','c-ok'],die:['Token die','c-err'],limit:['Bị limit','c-warn'],error:['Lỗi','c-err']};
const BAD=new Set(['die','limit','error']);
let S=null,cfgFilled=false;
let openPages = {}; 

async function api(path,body){
  const r=await fetch(path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-Key':KEY},body:body===undefined?undefined:JSON.stringify(body)});
  const j=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(j.error||('HTTP '+r.status));
  return j;
}
let tt;function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');clearTimeout(tt);tt=setTimeout(()=>t.classList.remove('show'),3000);}
async function act(fn){try{return await fn();}catch(e){toast('Lỗi: '+e.message);}}
function left(s){s=Math.max(0,Math.round(s));const m=Math.floor(s/60);return m>0?m+'p'+(s%60)+'s':s+'s';}

document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll('.pane').forEach(p=>p.classList.toggle('on',p.id==='p-'+b.dataset.tab));
});

function fillCfg(){
  if(cfgFilled||!S||!S.cfg)return;
  const c=S.cfg;
  $('#cName').value=c.name_type;$('#cPages').value=c.pages_per_nick;$('#cDelay').value=c.delay_between;
  $('#cThreads').value=c.threads;$('#cUA').value=c.ua_mode;$('#cLimit').value=c.limit_action;
  $('#cLimitCd').value=c.limit_cooldown;$('#cBloks').value=c.bloks_version;$('#cDoc').value=c.client_doc_id;
  $('#cDelayMedia').value=c.delay_before_media;
  $('#cAvatar').checked = c.auto_avatar !== false;
  $('#cCover').checked = c.auto_cover !== false;
  $('#cPost').checked = c.auto_post !== false;
  cfgFilled=true;
}
function readCfg(){
  return {name_type:$('#cName').value,pages_per_nick:+$('#cPages').value,delay_between:+$('#cDelay').value,threads:+$('#cThreads').value,ua_mode:$('#cUA').value,limit_action:$('#cLimit').value,limit_cooldown:+$('#cLimitCd').value,bloks_version:$('#cBloks').value.trim(),client_doc_id:$('#cDoc').value.trim(),auto_avatar:$('#cAvatar').checked,auto_cover:$('#cCover').checked,auto_post:$('#cPost').checked,custom_names:$('#cNames').value,delay_before_media:+$('#cDelayMedia').value};
}

function getAvatarHtml(a) {
  const initial = (a.name||'?').trim().charAt(0).toUpperCase();
  if (a.avatar) return `<img src="${esc(a.avatar)}" alt="avt">`;
  return initial;
}

function renderPage(p, token) {
  const initial = (p.name||'?').trim().charAt(0).toUpperCase();
  const avtHtml = p.avatar ? `<img src="${esc(p.avatar)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">` : initial;
  return `<div class="page-item">
    <input type="checkbox" style="width:18px;height:18px;margin:0;">
    <div class="p-avatar">${avtHtml}</div>
    <div class="p-info">
      <div class="p-name">${esc(p.name)}</div>
      <div class="p-uid">ID: ${esc(p.id)}</div>
    </div>
    <div class="p-actions">
      <button class="icon-btn" data-pact="avatar" data-pid="${esc(p.id)}" data-ptk="${esc(p.token)}" title="Up Avatar">👤</button>
      <button class="icon-btn" data-pact="cover" data-pid="${esc(p.id)}" data-ptk="${esc(p.token)}" title="Up Bìa">🖼️</button>
      <button class="icon-btn" data-pact="post" data-pid="${esc(p.id)}" data-ptk="${esc(p.token)}" title="Đăng bài">➕</button>
    </div>
  </div>`;
}

function accCard(a){
  const st=ST[a.status]||[a.status,'c-mut'];
  const pct=a.target>0?Math.min(100,Math.round(a.pages_created/a.target*100)):0;
  const barCls=a.status==='done'?'done':a.status==='die'?'die':'';
  const seld=a.selected?'sel':'';
  let label=st[0];
  if(a.until&&a.until>S.now&&a.status==='delay')label+=' · '+left(a.until-S.now);
  
  const isOpen = openPages[a.token] ? 'open' : '';
  const pageCount = a.page_list ? a.page_list.length : 0;
  const pagesHtml = pageCount > 0 ? `<div class="pages-section">
      <div class="pages-header" data-pact="toggle">
        <div class="title">Pages <span class="c-mut" style="font-size:12px">(${pageCount})</span></div>
        <div class="arrow ${isOpen}">▼</div>
      </div>
      <div class="pages-list ${isOpen}">
        ${a.page_list.map(p => renderPage(p, a.token)).join('')}
      </div>
    </div>` : `<div class="pages-section"><div class="pages-header"><div class="title">Pages <span class="c-mut" style="font-size:12px">(0)</span></div></div></div>`;

  return `<div class="acc ${seld}" data-token="${esc(a.token)}">
    <div class="acc-head">
      <div class="acc-avatar">${getAvatarHtml(a)}</div>
      <div class="acc-info">
        <div class="nm">${esc(a.name||'(Chưa check)')}</div>
        <div class="uid">ID: ${esc(a.uid||'—')}</div>
        <div class="tk">${esc(a.token_mask)}${a.proxy?' · proxy':''}</div>
      </div>
      <div class="acc-actions">
        <button class="icon-btn" data-act="check" title="Check token">⟳</button>
        <button class="icon-btn danger" data-act="del" title="Xóa">🗑</button>
      </div>
    </div>
    <div class="acc-check">
      <input type="checkbox" id="sel_${esc(a.token_key)}" data-act="toggle-sel" ${a.selected?'checked':''}>
      <label for="sel_${esc(a.token_key)}">Chọn acc này để chạy</label>
    </div>
    <div class="acc-toolbar">
      <button class="btn pri" data-act="reg">+ Reg acc này</button>
      <button class="btn ${a.running?'danger':'ok'}" data-act="stop" ${a.running?'':'disabled'}>■ Stop</button>
    </div>
    <div class="acc-status">
      <div class="st-lbl ${st[1]}">${esc(label)} · ${a.pages_created}/${a.target} page</div>
      <div class="st-sub">${esc(a.current_action||'')}</div>
      ${a.note?`<div class="st-sub c-warn">${esc(a.note)}</div>`:''}
      <div class="bar ${barCls}"><div style="width:${pct}%"></div></div>
    </div>
    ${pagesHtml}
  </div>`;
}

function render(){
  $('#dot').classList.add('on');$('#conn').textContent='đã kết nối';
  fillCfg();
  const T=S.totals;
  $('#kpis').innerHTML=`
    <div class="kpi"><small>Page tạo được</small><b class="c-ok">${T.ok}</b></div>
    <div class="kpi"><small>Token die</small><b class="c-err">${T.die}</b></div>
    <div class="kpi"><small>Bị limit</small><b class="c-warn">${T.limit}</b></div>
    <div class="kpi"><small>Lỗi khác</small><b>${T.err}</b></div>`;
  $('#bStart').disabled=S.running;$('#bStop').disabled=!S.running;
  $('#acclist').innerHTML=S.accounts.length?S.accounts.map(accCard).join(''):'<div class="empty">Chưa có token. Vào tab Cấu hình để thêm.</div>';
  
  const tl=$('#tklist');
  if(!S.tokens||!S.tokens.length){
    tl.innerHTML='<div class="mut" style="padding:8px 0">Chưa có token</div>';$('#tkCount').textContent='';
  } else {
    $('#tkCount').textContent='('+S.tokens.length+')';
    tl.innerHTML=S.tokens.map((t,i)=>{
      const acc = S.accounts.find(a => a.token === t.line.split('|')[0]);
      const uidDisplay = acc && acc.uid ? `[${acc.uid}] ` : '';
      const nameDisplay = acc && acc.name ? ` - ${acc.name}` : '';
      return `<div class="tk-row"><span>#${i+1} ${uidDisplay}${esc(t.mask)}${nameDisplay}${t.line.includes('|')?' · proxy':''}</span>
       <button class="btn sm danger" data-rm="${i}">Xóa</button></div>`;
    }).join('');
  }
  
  const bad=S.accounts.filter(a=>BAD.has(a.status)).length;
  $('#foot').innerHTML=`<span>Tổng: ${S.accounts.length}</span>
    <span class="c-ok">Hoàn thành: ${S.accounts.filter(a=>a.status==='done').length}</span>
    <span class="c-err">Lỗi: ${bad}</span>
    <span>${S.running?'🟢 Đang chạy':'⚪ Dừng'}</span>`;
  const only=$('#onlyErr').checked;
  const ic={ok:'✅',err:'❌',warn:'⚠️',info:'•',stop:'🚫'};
  const cl={ok:'c-ok',err:'c-err',warn:'c-warn',info:'',stop:'c-err'};
  const L=S.logs.filter(e=>!only||['err','warn','stop'].includes(e.lvl)).slice(-80).reverse();
  $('#loglist').innerHTML=L.length?L.map(e=>`<div class="log ${cl[e.lvl]||''}">${new Date(e.t*1000).toLocaleTimeString('vi-VN')} ${ic[e.lvl]||''} ${e.who?esc(e.who)+': ':''}${esc(e.text)}</div>`).join(''):'<div class="empty">Chưa có log</div>';
}
async function tick(){
  if(document.hidden)return;
  try{S=await api('/api/state');render();}
  catch(e){$('#dot').classList.remove('on');$('#conn').textContent='mất kết nối';}
}
setInterval(tick,1500);tick();

$('#acclist').addEventListener('click',ev=>{
  const card=ev.target.closest('.acc'); if(!card) return;
  const token=card.dataset.token;
  
  const toggleBtn = ev.target.closest('[data-pact="toggle"]');
  if (toggleBtn) {
      openPages[token] = !openPages[token];
      const arrow = toggleBtn.querySelector('.arrow');
      const list = toggleBtn.nextElementSibling;
      if (openPages[token]) { arrow.classList.add('open'); list.classList.add('open'); }
      else { arrow.classList.remove('open'); list.classList.remove('open'); }
      return;
  }

  const pBtn = ev.target.closest('[data-pact]');
  if (pBtn && pBtn.dataset.pact !== 'toggle') {
      const pid = pBtn.dataset.pid; const ptk = pBtn.dataset.ptk;
      const actName = pBtn.dataset.pact;
      act(async()=>{
          toast(`Đang up ${actName}...`);
          await api('/api/page_action', {pid, ptk, action: actName});
          toast(`Up ${actName} thành công!`);
      });
      return;
  }

  const pageItem = ev.target.closest('.page-item');
  if (pageItem) {
      const pName = pageItem.querySelector('.p-name').textContent;
      const pUid = pageItem.querySelector('.p-uid').textContent.replace('ID: ', '');
      const pToken = pageItem.querySelector('[data-ptk]').dataset.ptk;
      $('#mTitle').textContent = "Token Page: " + pName;
      $('#mUid').textContent = "UID Page: " + pUid;
      $('#mToken').value = pToken;
      $('#tokenModal').classList.add('show');
      return;
  }

  const btn=ev.target.closest('[data-act]'); 
  const label=ev.target.closest('label');
  const inp=ev.target.closest('input');
  
  if(btn || label || inp) {
    if(!btn) return;
    const a=btn.dataset.act;
    if(a==='check') act(async()=>{await api('/api/check',{token});toast('Đang check...');tick();});
    else if(a==='del'){
      if(!confirm('Xóa acc này?'))return;
      act(async()=>{
        const r=await fetch('/api/state',{headers:{'X-Key':KEY}}).then(x=>x.json());
        const idx=r.tokens.findIndex(t=>t.line.startsWith(token));
        if(idx<0){toast('Lỗi');return;}
        await api('/api/tokens/remove',{index:idx});toast('Đã xóa');tick();
      });
    } else if(a==='reg') act(async()=>{await api('/api/start',{token});toast('Bắt đầu reg');tick();});
    else if(a==='stop') act(async()=>{await api('/api/stop',{});toast('Đang dừng...');tick();});
    else if(a==='toggle-sel') act(async()=>{await api('/api/toggle',{token,selected:btn.checked});tick();});
    return;
  }

  const acc = S.accounts.find(x => x.token === token);
  if(!acc) return;
  $('#mTitle').textContent = "Token Account";
  $('#mUid').textContent = (acc.name || 'Chưa rõ tên') + ' | UID: ' + (acc.uid || 'Chưa check');
  $('#mToken').value = acc.token;
  $('#tokenModal').classList.add('show');
});

$('#mCopy').onclick=()=>{
  const tk=$('#mToken').value;
  navigator.clipboard.writeText(tk).then(()=>{
    toast('Đã copy!');
    $('#tokenModal').classList.remove('show');
  }).catch(()=>toast('Lỗi copy, hãy copy thủ công'));
};
$('#mClose').onclick=()=>$('#tokenModal').classList.remove('show');

$('#acclist').addEventListener('change',ev=>{
  const cb=ev.target.closest('[data-act="toggle-sel"]'); if(!cb) return;
  const card=cb.closest('.acc'); const token=card.dataset.token;
  act(async()=>{await api('/api/toggle',{token,selected:cb.checked});tick();});
});
$('#bCheckAll').onclick=()=>act(async()=>{
  if(!S||!S.tokens)return;
  for(const t of S.tokens){ await api('/api/check',{token:t.line}).catch(()=>{}); }
  toast('Đã gửi check tất cả');
});
$('#tklist').addEventListener('click',ev=>{
  const b=ev.target.closest('[data-rm]');if(!b)return;
  if(!confirm('Xóa token này?'))return;
  act(async()=>{await api('/api/tokens/remove',{index:+b.dataset.rm});toast('Đã xóa');tick();});
});
$('#bAdd').onclick=()=>act(async()=>{
  const v=$('#tkAdd').value.trim();if(!v){toast('Chưa dán token');return;}
  const r=await api('/api/tokens/add',{text:v});
  $('#tkAdd').value='';toast('Đã thêm '+r.added+' token, đang tự check...');tick();
});
$('#bClear').onclick=()=>act(async()=>{
  if(!confirm('Xóa tất cả token?'))return;
  const r=await api('/api/tokens/clear',{});toast('Đã xóa hết');tick();
});
$('#bStart').onclick=()=>act(async()=>{
  const r=await api('/api/start',{});toast('Đã bắt đầu '+r.threads+' luồng');tick();
});
$('#bStop').onclick=()=>act(async()=>{
  const r=await api('/api/stop',{});toast('Đang dừng '+r.stopped+' luồng…');tick();
});
$('#bReset').onclick=()=>act(async()=>{
  if(!confirm('Reset toàn bộ thống kê?'))return;
  await api('/api/reset',{});toast('Đã reset');tick();
});
$('#bSave').onclick=()=>act(async()=>{
  await api('/api/config',readCfg());toast('Đã lưu cấu hình');cfgFilled=false;tick();
});
$('#bReadOut').onclick=()=>act(async()=>{
  const r=await api('/api/output',{});
  $('#outBox').textContent=r.content||'(file rỗng)';
  $('#outInfo').textContent=r.lines?`${r.lines} dòng`:'';
});
$('#bClearOut').onclick=()=>act(async()=>{
  if(!confirm('Xóa file output?'))return;
  await api('/api/output/clear',{});toast('Đã xóa');
  $('#outBox').textContent='';$('#outInfo').textContent='';
});
$('#onlyErr').onchange=()=>S&&render();
</script></body></html>
'''

def run_check(port):
    say(f"Data dir: {DATA_DIR}")
    s = socket.socket()
    try: s.bind(("127.0.0.1", port)); say(f"Cổng {port}: trống")
    except OSError as e: say(f"Cổng {port}: BẬN ({e})")
    finally: s.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--key", default="")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    global DATA_DIR, CONFIG_FILE, OUTPUT_FILE, LOG_FILE
    DATA_DIR = ensure_data_dir()
    CONFIG_FILE = os.path.join(DATA_DIR, "reg_page_config.json")
    OUTPUT_FILE = os.path.join(DATA_DIR, "created_pages.txt")
    LOG_FILE = os.path.join(DATA_DIR, "reg_page_log.txt")

    if args.check: run_check(args.port); return
    if args.host not in ("127.0.0.1", "localhost", "::1") and not args.key:
        say("Phải có --key nếu mở ra ngoài"); sys.exit(1)

    load_cfg()
    try: srv = make_server(args.host, args.port, args.key)
    except OSError as e: say(f"Lỗi cổng: {e}"); sys.exit(1)
    
    port = srv.server_address[1]
    suffix = f"/?key={args.key}" if args.key else ""
    show = "127.0.0.1" if args.host in ("0.0.0.0", "") else args.host
    say(f"Reg Page Web v5: http://{show}:{port}{suffix}")
    say("Ctrl+C để thoát")
    
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
    finally: runner_stop(); srv.server_close()

if __name__ == "__main__":
    main()