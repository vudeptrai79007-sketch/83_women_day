from datetime import datetime
import json
import os
import re
import time
import urllib.parse
import uuid
import requests


class FacebookAdminManager:
  """Chuyển thể nguyên bản 100% từ Li2/S.smali, Lh2/X0.smali, Lh2/y.smali và LD2/q.smali"""

  GRAPHQL_URL = "https://graph.facebook.com/graphql"

  # Hai mã client_doc_id gốc trích xuất từ Smali
  DOC_ID_ACTION = "30749539927629244093798192451"  # Dùng cho STEP 1, STEP 2, STEP 4
  DOC_ID_FETCH_INVITE = "221080835214205752894689842827"  # Dùng cho STEP 3 (Lấy invitation_id)

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
    """Chuyển thể từ hàm Li2/S.b(Ljava/lang/String;)LF2/E;"""
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
    """Chuyển thể từ Li2/S.i(Ljava/lang/String;)Ljava/util/HashMap;"""
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
    """Chuyển thể từ Li2/S.d()Lorg/json/JSONObject;"""
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
    """Chuyển thể từ Li2/S.e()Lorg/json/JSONObject;"""
    return {
        "ads": True,
        "insights": True,
        "messages": True,
        "content": True,
        "moderate": True,
        "show_entry_point_saving_spinner": "NONE",
    }

  @classmethod
  def build_variables(cls, params_obj: dict, nt_context: dict = None) -> dict:
    """Chuyển thể từ Li2/S.f(Lorg/json/JSONObject;Lorg/json/JSONObject;)Lorg/json/JSONObject;"""
    if nt_context is None:
      nt_context = cls.build_nt_context()
    return {
        "params": params_obj,
        "nt_context": nt_context,
        "scale": "2",
        "use_native_entrypoint_for_stars_on_reels": True,
        "profile_image_size": 188,  # 0xbc
        "include_image_ranges": True,
    }

  @staticmethod
  def build_form_data(client_doc_id: str, variables_obj: dict) -> dict:
    """Chuyển thể từ Li2/S.c(Ljava/lang/String;Lorg/json/JSONObject;)Ljava/util/HashMap;"""
    return {
        "method": "post",
        "pretty": "false",
        "format": "json",
        "server_timestamps": "true",
        "locale": "vi_VN",
        "fb_api_req_friendly_name": "NativeTemplateAsyncQuery",
        "fb_api_caller_class": "graphservice",
        "client_doc_id": client_doc_id,
        "fb_api_client_context": json.dumps(
            {"is_background": False}, separators=(",", ":")
        ),
        "variables": json.dumps(variables_obj, separators=(",", ":")),
    }

  @staticmethod
  def extract_invitation_id(resp_json: dict) -> str:
    """Chuyển thể từ Li2/S.h(Lorg/json/JSONObject;)Ljava/lang/String;"""
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
      self, step_name: str, form_data: dict, token: str, is_receiver: bool
  ) -> dict:
    """Chuyển thể từ Li2/S.g(Ljava/lang/String;Ljava/util/HashMap;Ljava/lang/String;LF2/E;)Lorg/json/JSONObject;"""
    headers = self.build_headers(token)
    proxies = self.receiver_proxies if is_receiver else self.sender_proxies

    encoded_parts = []
    for k, v in form_data.items():
      encoded_parts.append(f"{k}={urllib.parse.quote_plus(str(v))}")
    body_str = "&".join(encoded_parts)

    resp = requests.post(
        self.GRAPHQL_URL,
        headers=headers,
        data=body_str,
        proxies=proxies,
        timeout=20,
    )
    if not resp.ok:
      raise RuntimeError(f"[{step_name}] HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    data["_http_status"] = resp.status_code
    return data

  # =========================================================================
  # 4 BƯỚC CHUYỂN PAGE & AUTO ACCEPT NGUYÊN BẢN TỪ SMALI
  # =========================================================================
  def execute_step1(
      self, page_id: str, target_uid: str, password: str, sender_token: str
  ) -> dict:
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
        "sensitive_string_value": json.dumps(
            sensitive_array, separators=(",", ":")
        )
    }
    params_obj = {
        "nt_context": nt_context,
        "payload": payload_path,
        "client_data": client_data,
    }
    variables = self.build_variables(params_obj, nt_context)
    form_data = self.build_form_data(self.DOC_ID_ACTION, variables)
    return self.post_graphql(
        "STEP1", form_data, sender_token, is_receiver=False
    )

  def execute_step2(
      self, page_id: str, target_uid: str, sender_token: str
  ) -> dict:
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
    return self.post_graphql(
        "STEP2", form_data, sender_token, is_receiver=False
    )

  def execute_step3(
      self, page_id: str, target_uid: str, receiver_token: str
  ) -> dict:
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
    form_data["fb_api_analytics_tags"] = (
        '["surfaces.fb.GraphServiceEmitter","GraphServices"]'
    )
    form_data["client_trace_id"] = str(uuid.uuid4())
    return self.post_graphql(
        "STEP3", form_data, receiver_token, is_receiver=True
    )

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
    return self.post_graphql(
        "STEP4", form_data, receiver_token, is_receiver=True
    )

  def transfer_page(
      self,
      page_id: str,
      sender_token: str,
      password: str,
      target_uid: str,
      receiver_token: str = None,
      auto_accept: bool = False,
  ) -> dict:
    result = {
        "page_id": page_id,
        "target_uid": target_uid,
        "invitation_id": None,
        "status": "FAILED",
        "message": "",
    }

    try:
      # --- BƯỚC 1: XÁC THỰC MẬT KHẨU & KHỞI TẠO LỜI MỜI ---
      print(f"[*] [STEP 1] Đang xác thực mật khẩu cho Page {page_id}...")
      resp1 = self.execute_step1(page_id, target_uid, password, sender_token)
      if "errors" in resp1:
        result["message"] = f"Step 1 failed with errors: {resp1['errors']}"
        return result
      print("    -> ✅ Bước 1 hoàn thành (Xác thực thành công)")

      # --- BƯỚC 2: CẬP NHẬT QUYỀN & BẮN THÔNG BÁO ---
      print(f"[*] [STEP 2] Đang kích hoạt gửi thông báo mời UID {target_uid}...")
      resp2 = self.execute_step2(page_id, target_uid, sender_token)
      if "errors" in resp2:
        result["message"] = f"Step 2 failed with errors: {resp2['errors']}"
        return result

      # Nếu không bật Auto Accept thì kết thúc tại Bước 2 như Lw2/e.m()
      if not auto_accept or not receiver_token:
        result["status"] = "SUCCESS"
        result["message"] = (
            "✅ Bước 2 hoàn thành - Đã gửi thông báo lời mời Admin!"
        )
        return result

      # --- ĐỢI 5 GIÂY NHƯ TRONG Lw2/o.m() ---
      for remaining in range(5, 0, -1):
        print(
            f"    -> ✅ Đã kích hoạt nhận thông báo! Chờ {remaining}s để tiếp"
            " tục..."
        )
        time.sleep(1)

      # --- BƯỚC 3: LẤY INVITATION_ID BÊN ACC NHẬN ---
      print(
          "[*] [STEP 3] Đang dùng Token nhận lấy mã invitation_id từ"
          " thông báo..."
      )
      resp3 = self.execute_step3(page_id, target_uid, receiver_token)
      invitation_id = self.extract_invitation_id(resp3)
      if not invitation_id:
        result["status"] = "INVITED_ONLY"
        result["message"] = (
            "Step 3 failed: Không thể extract invitation ID từ response"
        )
        return result

      result["invitation_id"] = invitation_id
      print(f"    -> ✅ Đã tìm thấy invitation_id: {invitation_id}")

      # --- BƯỚC 4: TỰ ĐỘNG CHẤP NHẬN LỜI MỜI ---
      print(
          f"[*] [STEP 4] Đang tự động chấp nhận lời mời ({invitation_id})..."
      )
      resp4 = self.execute_step4(invitation_id, receiver_token)
      if "errors" not in resp4 and resp4.get("_http_status") == 200:
        result["status"] = "SUCCESS"
        result["message"] = "✅ Đã tự động chấp nhận lời mời thành công!"
      else:
        result["status"] = "INVITED_ONLY"
        result["message"] = (
            f"Accept invitation failed: {resp4.get('errors', resp4)}"
        )

      return result

    except Exception as e:
      result["message"] = f"Lỗi ngoại lệ: {str(e)}"
      return result


# =====================================================================
# GIAO DIỆN ĐẦU VÀO (INPUT) & ĐẦU RA (OUTPUT)
# =====================================================================
def parse_input_line(line: str) -> dict:
  """Định dạng mỗi dòng:

  PAGE_ID|TOKEN_CAM_PAGE|MAT_KHAU|UID_NHAN|TOKEN_NHAN(tùy chọn)|PROXY_GUI(tùy
  chọn)|PROXY_NHAN(tùy chọn)
  """
  parts = [p.strip() for p in line.split("|")]
  if len(parts) < 4:
    raise ValueError(
        "Thiếu thông tin! Cần tối thiểu:"
        " PAGE_ID|TOKEN_CAM_PAGE|MAT_KHAU|UID_NHAN"
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
  print("=" * 68)
  print("   TOOL CHUYỂN PAGE & AUTO ACCEPT FULL 4 BƯỚC (MTOOL MAX PORT)   ")
  print("=" * 68)
  print("1. Nhập trực tiếp trên màn hình")
  print("2. Chạy hàng loạt từ file 'input_chuyen_page.txt'")
  choice = input("Chọn chế độ (1/2): ").strip()

  tasks = []
  if choice == "2":
    infile = "input_chuyen_page.txt"
    if not os.path.exists(infile):
      with open(infile, "w", encoding="utf-8") as f:
        f.write(
            "# PAGE_ID|TOKEN_CAM_PAGE|MAT_KHAU|UID_NHAN|TOKEN_NHAN|PROXY_GUI|PROXY_NHAN\n"
        )
      print(
          f"[!] Đã tạo file mẫu '{infile}'. Hãy dán dữ liệu vào rồi chạy lại."
      )
      return
    with open(infile, "r", encoding="utf-8") as f:
      for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
          try:
            tasks.append(parse_input_line(line))
          except Exception as e:
            print(f"[!] Bỏ qua dòng lỗi: {line} ({e})")
  else:
    page_id = input("- ID Page (profile_id): ").strip()
    sender_token = input("- Token Acc cầm Page: ").strip()
    password = input("- Mật khẩu Acc cầm Page: ").strip()
    target_uid = input("- UID Acc nhận Page: ").strip()
    receiver_token = input(
        "- Token Acc nhận Page (Enter nếu không Auto Accept): "
    ).strip()
    sender_proxy = input("- Proxy Acc cầm Page (Enter nếu không dùng): ").strip()
    receiver_proxy = input(
        "- Proxy Acc nhận Page (Enter nếu không dùng): "
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
    print("[!] Không có dữ liệu để chạy.")
    return

  success_out = "output_success.txt"
  failed_out = "output_failed.txt"

  for idx, item in enumerate(tasks, 1):
    print(
        f"\n--- [{idx}/{len(tasks)}] Chuyển Page {item['page_id']} ->"
        f" {item['target_uid']} ---"
    )
    auto_accept = bool(item["receiver_token"])
    manager = FacebookAdminManager(
        sender_proxy=item["sender_proxy"],
        receiver_proxy=item["receiver_proxy"],
    )
    res = manager.transfer_page(
        page_id=item["page_id"],
        sender_token=item["sender_token"],
        password=item["password"],
        target_uid=item["target_uid"],
        receiver_token=item["receiver_token"],
        auto_accept=auto_accept,
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = (
        f"{now} | Page: {res['page_id']} | UID Nhận: {res['target_uid']} |"
        f" InviteID: {res['invitation_id']} | Status: {res['status']} |"
        f" {res['message']}"
    )
    print(f"=> {log_line}")

    out_path = (
        success_out
        if res["status"] in ("SUCCESS", "INVITED_ONLY")
        else failed_out
    )
    with open(out_path, "a", encoding="utf-8") as f:
      f.write(log_line + "\n")

  print("\n" + "=" * 68)
  print(f"Hoàn tất! Kết quả lưu tại: {os.path.abspath(success_out)}")
  print("=" * 68)


if __name__ == "__main__":
  main()
