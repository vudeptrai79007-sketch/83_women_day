from datetime import datetime
import json
import os
import re
import time
import urllib.parse
import requests


class FacebookAdminManager:
  """Class chuyển thể từ Li2/S.smali (FacebookAdminManager) trong MTool Max"""

  GRAPHQL_URL = "https://graph.facebook.com/graphql"

  # Hằng số từ Li2/S.smali
  BLOKS_VERSION = (
      "338f8ead5977a2c41eba3e92584dcf1d132e8b7928f1f5796662ec064023047d"
  )
  STYLES_ID = "588d028b36bed0e1889e09b60e0f9aea"
  USER_AGENT = (
      "[FBAN/FB4A;FBAV/542.0.0.46.151;FBBV/840338789;"
      "FBDM/{density=0.75,width=300,height=540};FBLC/vi_VN;FBRV/0;"
      "FBCR/MobiFone;FBMF/MTool-Max;FBBD/MTool-Max;FBPN/com.facebook.katana;"
      "FBDV/MTool-Max;FBSV/9;FBOP/1;FBCA/x86_64:arm64-v8a;]"
  )

  def __init__(self, sender_proxy: str = None, receiver_proxy: str = None):
    self.sender_proxies = self.parse_proxy(sender_proxy)
    self.receiver_proxies = self.parse_proxy(receiver_proxy)

  @staticmethod
  def parse_proxy(proxy_str: str) -> dict:
    """Chuyển thể từ hàm Li2/S.b(Ljava/lang/String;)LF2/E;

    Hỗ trợ các định dạng:
      - host:port
      - user:pass@host:port
      - host:port:user:pass
      - http://..., socks4://..., socks5://...
    """
    if not proxy_str or not proxy_str.strip():
      return None

    raw = proxy_str.strip()
    scheme = "http"

    lower = raw.lower()
    if lower.startswith("http://"):
      scheme = "http"
      raw = raw[7:]
    elif lower.startswith("socks4://"):
      scheme = "socks4"
      raw = raw[9:]
    elif lower.startswith("socks5://"):
      scheme = "socks5"
      raw = raw[9:]

    host, port, user, password = None, None, None, None

    if "@" in raw:
      auth_part, host_part = raw.rsplit("@", 1)
      if ":" in auth_part:
        user, password = auth_part.split(":", 1)
      if ":" in host_part:
        host, port = host_part.rsplit(":", 1)
    else:
      parts = raw.split(":")
      if len(parts) == 2:
        host, port = parts[0], parts[1]
      elif len(parts) == 4:
        if parts[1].isdigit():
          host, port, user, password = parts[0], parts[1], parts[2], parts[3]
        else:
          user, password, host, port = parts[0], parts[1], parts[2], parts[3]

    if not host or not port:
      raise ValueError(f"Định dạng proxy không hợp lệ: {proxy_str}")

    if user and password:
      proxy_url = f"{scheme}://{urllib.parse.quote(user)}:{urllib.parse.quote(password)}@{host}:{port}"
    else:
      proxy_url = f"{scheme}://{host}:{port}"

    return {"http": proxy_url, "https": proxy_url}

  @classmethod
  def build_headers(cls, access_token: str) -> dict:
    """Chuyển thể từ hàm Li2/S.i(Ljava/lang/String;)Ljava/util/HashMap;"""
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
        "x-fb-request-analytics-tags": json.dumps(
            analytics_tags, separators=(",", ":")
        ),
        "x-fb-friendly-name": "NativeTemplateAsyncQuery",
        "x-graphql-client-library": "graphservice",
        "x-fb-connection-type": "WIFI",
        "authorization": f"OAuth {access_token}",
        "x-fb-device-group": "4789",
    }

  @classmethod
  def build_nt_context(cls) -> dict:
    """Chuyển thể từ hàm Li2/S.d()Lorg/json/JSONObject;"""
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
    """Chuyển thể từ hàm Li2/S.e()Lorg/json/JSONObject;"""
    return {
        "ads": True,
        "insights": True,
        "messages": True,
        "content": True,
        "moderate": True,
        "show_entry_point_saving_spinner": "NONE",
    }

  @classmethod
  def build_variables(cls, params_obj: dict) -> dict:
    """Chuyển thể từ hàm Li2/S.f(Lorg/json/JSONObject;Lorg/json/JSONObject;)Lorg/json/JSONObject;"""
    return {
        "params": params_obj,
        "nt_context": cls.build_nt_context(),
        "scale": "2",
        "use_native_entrypoint_for_stars_on_reels": True,
        "profile_image_size": 188,
        "include_image_ranges": True,
    }

  @staticmethod
  def build_form_data(client_doc_id: str, variables_obj: dict) -> dict:
    """Chuyển thể từ hàm Li2/S.c(Ljava/lang/String;Lorg/json/JSONObject;)Ljava/util/HashMap;"""
    return {
        "method": "post",
        "pretty": "false",
        "format": "json",
        "server_timestamps": "true",
        "locale": "vi_VN",
        "fb_api_req_friendly_name": "NativeTemplateAsyncQuery",
        "fb_api_caller_class": "graphservice",
        "client_doc_id": client_doc_id,
        "fb_api_client_context": json.dumps({"is_background": False}),
        "variables": json.dumps(variables_obj, separators=(",", ":")),
    }

  @staticmethod
  def extract_invitation_id(resp_json: dict) -> str:
    """Chuyển thể từ hàm Li2/S.h(Lorg/json/JSONObject;)Ljava/lang/String;"""
    try:
      attrs = resp_json["data"]["native_template_screen"]["nt_bundle"][
          "nt_bundle_attributes"
      ]
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
    return None

  def post_graphql(
      self, client_doc_id: str, params_obj: dict, token: str, is_receiver=False
  ) -> dict:
    """Chuyển thể từ hàm Li2/S.g(...)"""
    variables = self.build_variables(params_obj)
    form_data = self.build_form_data(client_doc_id, variables)
    headers = self.build_headers(token)
    proxies = self.receiver_proxies if is_receiver else self.sender_proxies

    resp = requests.post(
        self.GRAPHQL_URL,
        headers=headers,
        data=form_data,
        proxies=proxies,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    data["_http_status"] = resp.status_code
    return data

  # =========================================================================
  # LUỒNG CHUYỂN PAGE (GỬI LỜI MỜI ADMIN & AUTO ACCEPT)
  # =========================================================================
  def transfer_page(
      self,
      page_id: str,
      page_or_admin_token: str,
      password: str,
      target_uid: str,
      receiver_token: str = None,
      auto_accept: bool = False,
      client_doc_id_step1: str = "119940804239956818821550724",
  ) -> dict:
    """Thực hiện chuyển Page và trả về dict kết quả (Output)."""
    result = {
        "page_id": page_id,
        "target_uid": target_uid,
        "step1_invite": False,
        "invitation_id": None,
        "step2_accept": False,
        "status": "FAILED",
        "message": "",
    }

    try:
      print(
          f"[*] Đang gửi lời mời quản trị Page {page_id} tới UID"
          f" {target_uid}..."
      )

      # Cách 1: Gọi qua Graph API chuẩn cho Page truyền thống / Profile Plus
      url_roles = f"https://graph.facebook.com/v19.0/{page_id}/roles"
      payload_roles = {
          "admin": target_uid,
          "role": "ADMIN",
          "password": password,
          "tasks": json.dumps(
              ["MANAGE", "CREATE_CONTENT", "MODERATE", "ADVERTISE", "ANALYZE"]
          ),
          "access_token": page_or_admin_token,
      }
      resp1 = requests.post(
          url_roles,
          data=payload_roles,
          proxies=self.sender_proxies,
          timeout=20,
      )
      resp1_json = resp1.json()

      # Nếu Graph API /roles không hỗ trợ (Page Profile Plus yêu cầu NativeTemplateAsyncQuery)
      if not resp1.ok or "error" in resp1_json:
        # Fallback sang cấu trúc NativeTemplateAsyncQuery trong Li2/S.smali
        inner_params = {
            "page_id": str(page_id),
            "admin_id": str(target_uid),
            " invitee_id": str(target_uid),
            "password": password,
            **self.build_permissions(),
        }
        nt_params = {
            "path": "/pages/settings/admin_management/invite/",
            "params": json.dumps(inner_params),
        }
        resp1_json = self.post_graphql(
            client_doc_id=client_doc_id_step1,
            params_obj=nt_params,
            token=page_or_admin_token,
            is_receiver=False,
        )

      if "error" in resp1_json or "errors" in resp1_json:
        err_msg = resp1_json.get("error", {}).get("message") or str(
            resp1_json.get("errors")
        )
        result["message"] = f"Bước 1 thất bại: {err_msg}"
        return result

      result["step1_invite"] = True
      result["invitation_id"] = self.extract_invitation_id(resp1_json)
      print("[+] Bước 1 hoàn thành - Đã gửi lời mời Admin!")

      # Bước 2 & 3: Tự động chấp nhận nếu có bật Auto Accept và có Token nhận
      if auto_accept and receiver_token:
        print(
            "[*] Chờ 3 giây trước khi tự động chấp nhận lời mời bên tài khoản"
            " nhận..."
        )
        time.sleep(3)

        # Thử accept qua endpoint page_admin_invite hoặc GraphQL
        accept_url = f"https://graph.facebook.com/v19.0/{page_id}/roles"
        accept_payload = {
            "access_token": receiver_token,
            "method": "POST",
        }
        resp_acc = requests.post(
            accept_url,
            data=accept_payload,
            proxies=self.receiver_proxies,
            timeout=20,
        )
        acc_json = resp_acc.json()

        if resp_acc.ok and acc_json.get("success"):
          result["step2_accept"] = True
          result["status"] = "SUCCESS"
          result["message"] = (
              "Đã gửi lời mời và Auto Accept thành công!"
          )
        else:
          result["status"] = "INVITED_ONLY"
          result["message"] = (
              f"Đã gửi lời mời thành công, nhưng Auto Accept trả về: {acc_json}"
          )
      else:
        result["status"] = "SUCCESS"
        result["message"] = (
            "Đã gửi lời mời thành công (Chế độ không Auto Accept)."
        )

      return result

    except Exception as e:
      result["message"] = f"Lỗi ngoại lệ: {str(e)}"
      return result


# =====================================================================
# CHƯƠNG TRÌNH CHÍNH: XỬ LÝ ĐẦU VÀO (INPUT) & ĐẦU RA (OUTPUT)
# =====================================================================
def process_line(line: str) -> dict:
  """Định dạng dòng đầu vào:

  PAGE_ID|TOKEN_GOC|PASS_GOC|UID_NHAN|TOKEN_NHAN(tùy chọn)|PROXY_GOC(tùy
  chọn)|PROXY_NHAN(tùy chọn)
  """
  parts = [p.strip() for p in line.split("|")]
  if len(parts) < 4:
    raise ValueError(
        "Dòng dữ liệu thiếu trường bắt buộc (Cần ít nhất:"
        " PAGE_ID|TOKEN_GOC|PASS_GOC|UID_NHAN)"
    )

  return {
      "page_id": parts[0],
      "sender_token": parts[1],
      "password": parts[2],
      "target_uid": parts[3],
      "receiver_token": parts[4] if len(parts) > 4 and parts[4] else None,
      "sender_proxy": parts[5] if len(parts) > 5 and parts[5] else None,
      "receiver_proxy": parts[6] if len(parts) > 6 and parts[6] else None,
  }


def main():
  print("=" * 65)
  print("        TOOL CHUYỂN PAGE FACEBOOK (PORT TỪ MTOOL MAX)        ")
  print("=" * 65)
  print("Chọn chế độ Đầu Vào (Input):")
  print("  1. Nhập thủ công từng Page trên màn hình")
  print("  2. Đọc hàng loạt từ file 'input_chuyen_page.txt'")
  mode = input("Lựa chọn của bạn (1/2): ").strip()

  tasks = []
  if mode == "2":
    input_file = "input_chuyen_page.txt"
    if not os.path.exists(input_file):
      with open(input_file, "w", encoding="utf-8") as f:
        f.write(
            "# Định dạng:"
            " PAGE_ID|TOKEN_GOC|PASS_GOC|UID_NHAN|TOKEN_NHAN|PROXY_GOC|PROXY_NHAN\n"
        )
      print(
          f"[!] Chưa có file '{input_file}'. Đã tạo file mẫu, hãy điền dữ liệu"
          " vào rồi chạy lại!"
      )
      return

    with open(input_file, "r", encoding="utf-8") as f:
      for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
          try:
            tasks.append(process_line(line))
          except Exception as e:
            print(f"[!] Bỏ qua dòng lỗi: {line} ({e})")
  else:
    page_id = input("- Nhập ID Page cần chuyển: ").strip()
    sender_token = input(
        "- Nhập Token Acc cầm Page (EAAG.../EAAAA...): "
    ).strip()
    password = input("- Nhập Mật khẩu Acc cầm Page: ").strip()
    target_uid = input("- Nhập UID Acc nhận Page: ").strip()
    receiver_token = input(
        "- Nhập Token Acc nhận (Để trống nếu không Auto Accept): "
    ).strip()
    sender_proxy = input("- Nhập Proxy Acc gửi (Để trống nếu không dùng): ").strip()
    receiver_proxy = input(
        "- Nhập Proxy Acc nhận (Để trống nếu không dùng): "
    ).strip()

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
    print("[!] Không có dữ liệu đầu vào để xử lý.")
    return

  success_file = "output_chuyen_page_success.txt"
  error_file = "output_chuyen_page_error.txt"

  print(f"\n[*] Bắt đầu xử lý {len(tasks)} yêu cầu chuyển Page...\n")

  for idx, item in enumerate(tasks, 1):
    print(
        f"--- [{idx}/{len(tasks)}] Page: {item['page_id']} -> UID:"
        f" {item['target_uid']} ---"
    )
    auto_accept = bool(item["receiver_token"])

    manager = FacebookAdminManager(
        sender_proxy=item["sender_proxy"],
        receiver_proxy=item["receiver_proxy"],
    )

    res = manager.transfer_page(
        page_id=item["page_id"],
        page_or_admin_token=item["sender_token"],
        password=item["password"],
        target_uid=item["target_uid"],
        receiver_token=item["receiver_token"],
        auto_accept=auto_accept,
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = (
        f"{timestamp} | Page: {res['page_id']} | To: {res['target_uid']} |"
        f" Status: {res['status']} | InviteID: {res['invitation_id']} | Msg:"
        f" {res['message']}"
    )

    print(f"=> KẾT QUẢ: {log_line}\n")

    # Ghi Đầu Ra (Output) ra file
    target_file = (
        success_file
        if res["status"] in ("SUCCESS", "INVITED_ONLY")
        else error_file
    )
    with open(target_file, "a", encoding="utf-8") as f:
      f.write(log_line + "\n")

  print("=" * 65)
  print("HOÀN TẤT! Kết quả đầu ra đã được lưu vào:")
  print(f"  - Thành công : {os.path.abspath(success_file)}")
  print(f"  - Thất bại   : {os.path.abspath(error_file)}")
  print("=" * 65)


if __name__ == "__main__":
  main()
