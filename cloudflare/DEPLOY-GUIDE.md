# Cloudflare Pages Deployment Guide (password-protected)

This guide shows how to publish the generated single-file web app on
Cloudflare Pages behind HTTP Basic Auth (username + password), with a custom
domain. Replace the placeholders with your own values.

> Legal note: if the deployed pages contain the BJCP Style Guidelines text or
> translations of it, do NOT make them publicly linked/accessible without
> BJCP's permission. A password-protected URL used for review or personal use
> is not "public posting" - keep it that way until you have permission.

## 0) Architecture & cost
- Cloudflare Pages hosts the static files (free tier is enough)
- A Pages Functions middleware adds Basic Auth (401 -> browser login prompt)
- Custom domain: e.g. `beer.example.com` (your zone must be on Cloudflare)
- Layout used in this toolkit:
    cloudflare/
      functions/_middleware.js   # auth check
      public/                    # generated index.html / index.zh.html / index.en.html
      sync.sh                    # copy freshly generated pages into public/
- The password lives in the Cloudflare Pages project environment variables
  (REVIEW_USER / REVIEW_PASS). Never commit it.

## 1) Put your domain on Cloudflare (if not already)
1. Create a free Cloudflare account and add your domain (zone).
2. If the zone was previously on another DNS host, keep/import the DNS records
   you still need (existing site A records, email MX/TXT, etc.).
3. Point your domain's nameservers at the two nameservers Cloudflare assigns.
4. Wait until the zone shows **Active**.

## 2) Deploy (either way)

### A) Dashboard
1. Pages -> Create project -> name, e.g. `beer-styles`
2. Upload assets from `public/` (drag the files) -> Deploy
3. Settings -> Environment variables: add
       REVIEW_USER = your chosen username
       REVIEW_PASS = a strong password
4. Settings -> Custom domains -> Add your domain (e.g. `beer.example.com`);
   Cloudflare creates the CNAME automatically.

### B) wrangler CLI (recommended for updates)
    npx wrangler login
    npx wrangler pages project create beer-styles --production-branch=main
    npx wrangler pages secret put REVIEW_USER --project-name beer-styles
    npx wrangler pages secret put REVIEW_PASS --project-name beer-styles
    npx wrangler pages deploy public --project-name beer-styles
    # output prints a *.pages.dev URL

Then add the custom domain in the dashboard (Pages -> your project ->
Custom domains -> Add -> your domain).

## 3) Verify
Open your domain -> a login dialog should appear; correct credentials load
the app; missing/wrong credentials return 401.

## 4) Update the data later
    python3 update.py                       # rebuild locally (fetch official source)
    ./sync.sh                               # inside cloudflare/: refresh public/
    npx wrangler pages deploy public --project-name beer-styles

## 5) Security & compliance reminders
- Use a strong password; store it only in the Pages environment variables.
- Do not commit secrets, nor generated pages that embed the guideline text.
- Get BJCP permission before making any full-text version publicly reachable.

---

# Cloudflare Pages 部署指南（带密码）

> 把生成的单文件网页发布到 Cloudflare Pages 并启用 HTTP Basic Auth
> （用户名+密码）。下面用占位符表示你自己的值，请自行替换。

## 0) 架构与成本
- Cloudflare Pages 托管静态文件（免费额度足够）
- Pages Functions 中间件做整站 Basic Auth
- 自定义域：例如 `beer.example.com`（域名需已在 Cloudflare）
- 密码放在 Pages 项目的环境变量 REVIEW_USER / REVIEW_PASS，**不要提交**

## 1) 把域名放到 Cloudflare（如尚未接入）
1. 注册免费账号并添加你的域名（zone）
2. 迁移前保留你仍需要的 DNS 记录（现有网站的 A 记录、邮箱 MX/TXT 等）
3. 在原注册商把 Nameserver 改成 Cloudflare 分配的两个 NS
4. 等 zone 状态变为 **Active**

## 2) 部署（二选一）

面板：Pages → Create project（如 `beer-styles`）→ 上传 `public/` 内容 →
Settings → Environment variables 加 REVIEW_USER / REVIEW_PASS →
Custom domains 添加你的域名（会自动加 CNAME）。

命令行（便于以后更新）：
    npx wrangler login
    npx wrangler pages project create beer-styles --production-branch=main
    npx wrangler pages secret put REVIEW_USER --project-name beer-styles
    npx wrangler pages secret put REVIEW_PASS --project-name beer-styles
    npx wrangler pages deploy public --project-name beer-styles

## 3) 验证
打开你的域名 → 应弹登录框；账密正确进入，缺失/错误返回 401。

## 4) 以后更新数据
    python3 update.py        # 本地重建（拉官方源→建库→建页）
    ./sync.sh                # 在 cloudflare/ 内刷新 public/
    npx wrangler pages deploy public --project-name beer-styles

## 5) 安全与合规提醒
- 密码只存在 Pages 环境变量；不要提交密钥，也不要提交含正文的生成页。
- 全量正文版本公开发布前，请先取得 BJCP 许可。
