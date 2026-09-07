#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评审专用预览服务器（Basic Auth 密码保护）
用法：
  1) 启动： python3 preview_auth_server.py [目录，默认 ../web] [端口，默认 8123]
     首次运行会生成一个随机用户名/密码并打印；可用环境变量 PREVIEW_USER/PREVIEW_PASS 固定。
  2) 暴露公网临时链接（二选一）：
     - Cloudflare Quick Tunnel（免费、无需账号）:
         brew install cloudflared     # 只需一次
         cloudflared tunnel --url http://127.0.0.1:8123
       输出 https://xxxx.trycloudflare.com 即评审地址。
     - 或 ngrok（需账号）: ngrok http 8123
  3) 把 临时URL + 用户名/密码 发给 BJCP，注明"仅供评审、非公开、审后即删"。
"""
import base64, hashlib, hmac, os, socket, sys, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parent / "web")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8123

user = os.environ.get("PREVIEW_USER") or "bjcp-review"
if "PREVIEW_PASS" in os.environ:
    pw = os.environ["PREVIEW_PASS"]
else:
    pw = base64.urlsafe_b64encode(os.urandom(9)).decode().rstrip("=")
TOKEN = user + ":" + pw
EXPECT = "Basic " + base64.b64encode(TOKEN.encode()).decode()

CT = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
      ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
      ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".txt": "text/plain; charset=utf-8"}

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Authorization") != EXPECT:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="BJCP review"')
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", ""):
            path = "/index.html"
        target = (ROOT / path.lstrip("/")).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            self.send_response(404); self.end_headers(); return
        if not target.is_file():
            self.send_response(404); self.end_headers(); return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", CT.get(target.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *a):
        pass

srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
print("preview server: http://127.0.0.1:%d  (dir: %s)" % (PORT, ROOT))
print("basic auth -> user: %s  pass: %s" % (user, pw))
print("then run: cloudflared tunnel --url http://127.0.0.1:%d" % PORT)
srv.serve_forever()
