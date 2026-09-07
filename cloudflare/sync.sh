#!/bin/bash
# 从本地 web/ 刷新待部署页面（数据更新后运行）
set -e
cd "$(dirname "$0")"
cp ../web/index.html ../web/index.zh.html ../web/index.en.html public/
echo "public/ 已更新："
ls -la public/
