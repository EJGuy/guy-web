# -*- coding: utf-8 -*-
"""
API 额度查询服务器（本机用）
- 读取同目录 keys/ 下的三个 Key 文件，实时查询各家额度
- 供资料库.html 等本地网页通过 /api/quota 拉取（带 CORS）
- 用法：python quota_server.py [端口]   （默认 8720）
"""
import json
import urllib.request
import urllib.error
import io
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY_DIR = None


def _resolve_key_dir():
    """Key 目录解析：环境变量 QUOTA_KEY_DIR 优先，其次脚本同目录 keys/"""
    cand = os.environ.get("QUOTA_KEY_DIR")
    if cand and os.path.isdir(cand):
        return cand
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")


KEY_DIR = _resolve_key_dir()
PORT = 8720
CACHE_SECONDS = 15  # 两次查询间的最小间隔，避免频繁打 API

_cache = {"t": 0, "data": None}


def _read_key(fname, pat):
    try:
        with io.open(os.path.join(KEY_DIR, fname), encoding="utf-8") as f:
            for line in f.read().splitlines():
                line = line.strip()
                if line.startswith(pat):
                    return line
    except Exception:
        return None
    return None


def _get(url, key, timeout=12):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return {"_http_error": e.code, "_body": json.loads(body)}
        except Exception:
            return {"_http_error": e.code, "_body": body[:300]}
    except Exception as e:
        return {"_error": str(e)}


def _query():
    result = {"updated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "providers": {}}

    # DeepSeek：余额
    dk = _read_key("deepseek.txt", "sk-")
    if dk:
        r = _get("https://api.deepseek.com/user/balance", dk)
        if "balance_infos" in r:
            bi = r["balance_infos"][0]
            result["providers"]["deepseek"] = {
                "available": r.get("is_available", False),
                "total": bi.get("total_balance", "0.00"),
                "granted": bi.get("granted_balance", "0.00"),
                "topped_up": bi.get("topped_up_balance", "0.00"),
                "currency": bi.get("currency", "CNY"),
            }
        else:
            result["providers"]["deepseek"] = {"error": r.get("_error") or r.get("_http_error") or "查询失败"}
    else:
        result["providers"]["deepseek"] = {"error": "未找到 Key 文件"}

    # OpenRouter：用量 / 限额 / 免费模型次数
    ok = _read_key("openrouter.txt", "sk-or-")
    if ok:
        r = _get("https://openrouter.ai/api/v1/auth/key", ok)
        d = r.get("data") or {}
        if d:
            b = d.get("budgets") or []
            budget = b[0] if b else {}
            fm = d.get("free_model_daily_requests") or {}
            result["providers"]["openrouter"] = {
                "usage_usd": d.get("usage", 0),
                "limit_usd": d.get("limit", None),
                "limit_remaining": d.get("limit_remaining", None),
                "budget_limit": budget.get("limit_usd"),
                "budget_spend": budget.get("spend_usd"),
                "budget_remaining": budget.get("remaining_usd"),
                "free_used_today": fm.get("used", 0),
                "free_limit_today": fm.get("limit", 0),
                "free_remaining_today": fm.get("remaining", 0),
                "expires": d.get("expires_at"),
                "is_free_tier": d.get("is_free_tier"),
            }
        else:
            result["providers"]["openrouter"] = {"error": r.get("_error") or r.get("_http_error") or "查询失败"}
    else:
        result["providers"]["openrouter"] = {"error": "未找到 Key 文件"}

    # 智谱：无公开查询接口，返回静态说明
    result["providers"]["zhipu"] = {
        "note": "智谱无公开用量 API，请登录 open.bigmodel.cn 控制台「用量统计」查看",
        "console_url": "https://open.bigmodel.cn/console/quota",
        "resource": "200 万 tokens 通用模型推理资源包（生效中）",
    }
    return result


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-store")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] != "/api/quota":
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')
            return
        now = time.time()
        if now - _cache["t"] >= CACHE_SECONDS or _cache["data"] is None:
            _cache["t"] = now
            _cache["data"] = _query()
        body = json.dumps(_cache["data"], ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("quota server on http://127.0.0.1:%d/api/quota" % PORT)
    srv.serve_forever()
