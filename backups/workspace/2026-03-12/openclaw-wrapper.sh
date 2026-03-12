#!/bin/bash
# OpenClaw包装脚本

OPENCLAW_SCRIPT="/home/toufumind/.openclaw/extensions/qqbot/node_modules/.bin/openclaw"

if [ -f "$OPENCLAW_SCRIPT" ]; then
    exec "$OPENCLAW_SCRIPT" "$@"
else
    echo "错误: openclaw脚本未找到"
    echo "请检查安装路径: $OPENCLAW_SCRIPT"
    exit 1
fi
