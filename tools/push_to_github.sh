#!/bin/bash
# 自动推送到GitHub脚本

cd /home/toufumind/.openclaw/workspace

echo "=== 推送到GitHub ==="
echo "时间: $(date)"
echo "分支: $(git branch --show-current)"

# 检查网络连接
if ! curl -s --connect-timeout 5 https://github.com > /dev/null; then
    echo "❌ 网络连接失败，无法访问GitHub"
    echo "本地提交已保存，网络恢复后自动推送"
    exit 1
fi

# 添加所有更改
echo "添加更改..."
git add .

# 检查是否有更改
if git diff --cached --quiet; then
    echo "✅ 没有需要提交的更改"
    exit 0
fi

# 提交更改
COMMIT_MSG="技术美术文章收集更新 - $(date '+%Y年%m月%d日 %H:%M')"
echo "提交: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# 推送到GitHub
echo "推送到GitHub..."
if git push origin master; then
    echo "✅ 推送成功"
    echo "提交哈希: $(git log --oneline -1)"
else
    echo "❌ 推送失败，保留本地提交"
    echo "下次运行时会重试"
fi

echo "=== 完成 ==="