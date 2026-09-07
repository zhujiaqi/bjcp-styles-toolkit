# Review Preview Server / 评审预览服务器

Serve the web app locally behind HTTP Basic Auth, then expose it with a
temporary public URL (password required) so a reviewer can access it.
临时评审预览：本地带密码服务 + 临时公网隧道（需密码才能访问）。

## Usage / 用法
    # 1) start the protected local server (serves ../web by default)
    python3 preview_auth_server.py [DIR] [PORT]     # default: ../web, 8123
    #     prints username/password; or set env PREVIEW_USER / PREVIEW_PASS
    # 2) expose a temporary public URL (pick one):
    #     Cloudflare Quick Tunnel (free, no account):
    #         cloudflared tunnel --url http://127.0.0.1:8123
    #     or ngrok:  ngrok http 8123
    # 3) send the URL + credentials to the reviewer; Ctrl-C to stop.

> More controlled long-term option: Cloudflare Pages + Basic Auth middleware
> on your own domain (see ../cloudflare/DEPLOY-GUIDE.md).
> 更可控的长效方式见 cloudflare/DEPLOY-GUIDE.md（自定义域 + 密码中间件）。
