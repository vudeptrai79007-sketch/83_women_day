import re
import json
import html
import aiohttp
import asyncio
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timezone, timedelta

TZ_VN = timezone(timedelta(hours=7))

HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Check Info TikTok Hàng Loạt</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; }
        .container { max-width: 1050px; margin: auto; background: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        h2 { margin-top: 0; color: #111; }
        textarea { width: 100%; height: 140px; padding: 12px; font-size: 14px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; resize: vertical; }
        button { margin-top: 10px; padding: 10px 22px; font-size: 15px; font-weight: bold; color: #fff; background: #fe2c55; border: none; border-radius: 6px; cursor: pointer; }
        button:hover { background: #e0244a; }
        button:disabled { background: #aaa; cursor: not-allowed; }
        .summary { margin: 15px 0; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { border: 1px solid #e0e0e0; padding: 8px 10px; text-align: left; }
        th { background: #f8f9fa; }
        .live { color: #16a34a; font-weight: bold; }
        .die { color: #dc2626; font-weight: bold; }
        img.avatar { width: 36px; height: 36px; border-radius: 50%; vertical-align: middle; }
    </style>
</head>
<body>
<div class="container">
    <h2>Công Cụ Check Info TikTok Hàng Loạt</h2>
    <p>Nhập danh sách username (mỗi dòng 1 nick hoặc cách nhau bằng dấu phẩy):</p>
    <textarea id="usernames" placeholder="linh.anh9257&#10;on.hi.kin2&#10;ng.mnh.hng541&#10;user8327162261534&#10;tun.kit5889"></textarea>
    <br>
    <button id="btnCheck" onclick="checkBulk()">Check Hàng Loạt</button>
    <div id="summary" class="summary"></div>
    <div id="result"></div>
</div>

<script>
async function checkBulk() {
    const raw = document.getElementById("usernames").value.trim();
    if (!raw) return alert("Vui lòng nhập ít nhất 1 username!");
    const btn = document.getElementById("btnCheck");
    const summary = document.getElementById("summary");
    const resultDiv = document.getElementById("result");

    btn.disabled = true;
    btn.innerText = "Đang kiểm tra...";
    summary.innerText = "";
    resultDiv.innerHTML = "";

    try {
        const res = await fetch("/tiktok", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ usernames: raw })
        });
        const data = await res.json();
        if (!data.success) {
            summary.innerText = "Lỗi: " + (data.error || "Không xác định");
            return;
        }
        summary.innerText = `Tổng: ${data.total} | LIVE: ${data.live} | DIE/Lỗi: ${data.die}`;
        let html = `<table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Trạng thái</th>
                    <th>Username</th>
                    <th>Tên hiển thị</th>
                    <th>Ngày tạo</th>
                    <th>Follower</th>
                    <th>Đang follow</th>
                    <th>Tim</th>
                    <th>Video</th>
                    <th>Riêng tư</th>
                </tr>
            </thead><tbody>`;
        data.results.forEach((item, idx) => {
            if (item.success) {
                const u = item.user;
                html += `<tr>
                    <td>${idx + 1}</td>
                    <td class="live">LIVE</td>
                    <td><a href="${u.url}" target="_blank">@${u.username}</a></td>
                    <td>${u.nickname || ""}</td>
                    <td>${u.created || "Không rõ"}</td>
                    <td>${u.followers.toLocaleString()}</td>
                    <td>${u.following.toLocaleString()}</td>
                    <td>${u.likes.toLocaleString()}</td>
                    <td>${u.videos.toLocaleString()}</td>
                    <td>${u.private ? "Có" : "Không"}</td>
                </tr>`;
            } else {
                html += `<tr>
                    <td>${idx + 1}</td>
                    <td class="die">DIE / LỖI</td>
                    <td>@${item.username}</td>
                    <td colspan="7">${item.error} (Mã: ${item.status})</td>
                </tr>`;
            }
        });
        html += "</tbody></table>";
        resultDiv.innerHTML = html;
    } catch (e) {
        summary.innerText = "Lỗi kết nối tới server: " + e;
    } finally {
        btn.disabled = false;
        btn.innerText = "Check Hàng Loạt";
    }
}
</script>
</body>
</html>
"""


class amdtsmodz:
    def __init__(self):
        self.app = Flask(__name__)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.tiktok.com/",
        }
        self._register_routes()

    @staticmethod
    def parse_usernames(raw_input):
        if isinstance(raw_input, list):
            items = raw_input
        elif isinstance(raw_input, str):
            items = re.split(r"[\s,;]+", raw_input.strip())
        else:
            items = []

        cleaned = []
        seen = set()
        for item in items:
            u = str(item).strip().lstrip("@")
            if u and u.lower() not in seen:
                seen.add(u.lower())
                cleaned.append(u)
        return cleaned

    async def _fetch_one(self, session, sem, username):
        username = username.strip().lstrip("@")
        if not re.fullmatch(r"[A-Za-z0-9._]{1,24}", username):
            return {
                "username": username,
                "success": False,
                "status": 400,
                "error": "Invalid TikTok username.",
            }

        async with sem:
            try:
                async with session.get(
                    f"https://www.tiktok.com/@{username}", headers=self.headers
                ) as r:
                    status = r.status
                    if status == 404:
                        return {
                            "username": username,
                            "success": False,
                            "status": 404,
                            "error": "TikTok account not found.",
                        }
                    if status != 200:
                        return {
                            "username": username,
                            "success": False,
                            "status": status,
                            "error": f"TikTok returned HTTP {status}.",
                        }
                    page = await r.text()

                raw = None
                for pattern in (
                    r'<script[^>]*id=["\']__UNIVERSAL_DATA_FOR_REHYDRATION__["\'][^>]*>(.*?)</script>',
                    r'<script[^>]*id=["\']SIGI_STATE["\'][^>]*>(.*?)</script>',
                ):
                    m = re.search(pattern, page, re.S | re.I)
                    if m:
                        try:
                            raw = json.loads(html.unescape(m.group(1)))
                            break
                        except Exception:
                            pass

                if not isinstance(raw, dict):
                    return {
                        "username": username,
                        "success": False,
                        "status": 502,
                        "error": "Unable to retrieve TikTok account data.",
                    }

                detail = raw.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
                if detail.get("statusCode") in (10202, 10221, 10222):
                    return {
                        "username": username,
                        "success": False,
                        "status": 404,
                        "error": "Account does not exist or banned.",
                    }

                info = detail.get("userInfo", {})
                u = info.get("user", {})
                st = info.get("stats", {})
                st2 = info.get("statsV2", {})

                if not u:
                    module = raw.get("UserModule", {})
                    users_dict = module.get("users", {})
                    stats_dict = module.get("stats", {})
                    u = users_dict.get(username.lower()) or users_dict.get(username, {})
                    st = stats_dict.get(username.lower()) or stats_dict.get(username, {})
                    st2 = {}

                if not u:
                    return {
                        "username": username,
                        "success": False,
                        "status": 404,
                        "error": "Account information not found.",
                    }

                created = None
                if u.get("createTime"):
                    try:
                        created = (
                            datetime.fromtimestamp(int(u["createTime"]), timezone.utc)
                            .astimezone(TZ_VN)
                            .strftime("%H:%M:%S %d/%m/%Y")
                        )
                    except Exception:
                        created = None

                uid = u.get("uniqueId") or username
                return {
                    "username": uid,
                    "success": True,
                    "status": 200,
                    "user": {
                        "id": u.get("id"),
                        "username": uid,
                        "nickname": u.get("nickname"),
                        "bio": u.get("signature") or "No bio",
                        "avatar": u.get("avatarLarger")
                        or u.get("avatarMedium")
                        or u.get("avatarThumb"),
                        "private": u.get("privateAccount", False),
                        "created": created,
                        "followers": st.get("followerCount", st2.get("followerCount", 0)),
                        "following": st.get("followingCount", st2.get("followingCount", 0)),
                        "likes": st.get(
                            "heartCount",
                            st.get("heart", st2.get("heartCount", st2.get("heart", 0))),
                        ),
                        "videos": st.get("videoCount", st2.get("videoCount", 0)),
                        "url": f"https://www.tiktok.com/@{uid}",
                    },
                }
            except Exception as e:
                return {
                    "username": username,
                    "success": False,
                    "status": 500,
                    "error": str(e)[:300],
                }

    def Sc_amdtsmodz_bulk(self, usernames, max_concurrency=5):
        async def run_all():
            sem = asyncio.Semaphore(max_concurrency)
            timeout = aiohttp.ClientTimeout(total=25)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                tasks = [self._fetch_one(session, sem, u) for u in usernames]
                return await asyncio.gather(*tasks)

        results = asyncio.run(run_all())
        live_count = sum(1 for r in results if r.get("success"))
        return {
            "success": True,
            "total": len(results),
            "live": live_count,
            "die": len(results) - live_count,
            "results": results,
        }, 200

    def _register_routes(self):
        @self.app.route("/", methods=["GET"])
        def index():
            return render_template_string(HTML_PAGE)

        @self.app.route("/tiktok", methods=["GET", "POST"])
        def tiktok():
            raw_list = None
            if request.method == "POST":
                if request.is_json:
                    body = request.get_json(silent=True) or {}
                    raw_list = body.get("usernames") or body.get("username")
                else:
                    raw_list = (
                        request.form.get("usernames")
                        or request.form.get("username")
                        or request.get_data(as_text=True)
                    )
            else:
                if "usernames" in request.args:
                    raw_list = request.args.get("usernames", "")
                elif "username" in request.args:
                    single = request.args.get("username", "")
                    if "," not in single and "\n" not in single:
                        # Giữ nguyên cấu trúc trả về cũ nếu chỉ truyền ?username=1_nick
                        res, _ = self.Sc_amdtsmodz_bulk([single])
                        item = res["results"][0]
                        if item["success"]:
                            return jsonify({"success": True, "user": item["user"]}), 200
                        return (
                            jsonify({"success": False, "error": item["error"]}),
                            item["status"],
                        )
                    raw_list = single

            usernames = self.parse_usernames(raw_list)
            if not usernames:
                return (
                    jsonify({"success": False, "error": "Vui lòng truyền danh sách usernames."}),
                    400,
                )

            data, status = self.Sc_amdtsmodz_bulk(usernames)
            return jsonify(data), status

    def run(self):
        self.app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    amdtsmodz().run()
