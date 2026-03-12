#!/bin/bash
# OpenClaw路径修复脚本

echo "=== OpenClaw路径修复 ==="
echo "当前时间: $(date)"
echo ""

# 1. 检查现有openclaw安装
echo "1. 检查OpenClaw安装位置..."
OPENCLAW_PATHS=$(find /home/toufumind -name "openclaw" -type f 2>/dev/null | grep -E "\.bin/openclaw$" | head -5)
echo "找到的openclaw路径:"
echo "$OPENCLAW_PATHS"
echo ""

# 2. 选择主要路径
MAIN_PATH="/home/toufumind/.openclaw/extensions/qqbot/node_modules/.bin/openclaw"
if [ -f "$MAIN_PATH" ]; then
    echo "2. 使用主要路径: $MAIN_PATH"
    
    # 3. 测试openclaw命令
    echo "3. 测试openclaw命令..."
    if "$MAIN_PATH" --version 2>/dev/null; then
        echo "✅ openclaw命令测试成功"
    else
        echo "❌ openclaw命令测试失败，尝试直接调用node..."
        NODE_PATH="/home/toufumind/.openclaw/extensions/qqbot/node_modules/.pnpm/openclaw@2026.3.8_@napi-rs+canvas@0.1.96_@types+express@5.0.6_hono@4.11.4_node-llama-cpp@3.16.2_typescript@5.9.3_/node_modules/openclaw/openclaw.mjs"
        if [ -f "$NODE_PATH" ]; then
            echo "找到openclaw.mjs: $NODE_PATH"
            node "$NODE_PATH" --version 2>/dev/null && echo "✅ 通过node调用成功"
        fi
    fi
else
    echo "❌ 主要路径不存在: $MAIN_PATH"
fi

echo ""

# 4. 创建别名和PATH更新
echo "4. 创建解决方案..."
cat > /home/toufumind/.openclaw/workspace/openclaw-wrapper.sh << 'EOF'
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
EOF

chmod +x /home/toufumind/.openclaw/workspace/openclaw-wrapper.sh

echo "✅ 创建包装脚本: /home/toufumind/.openclaw/workspace/openclaw-wrapper.sh"
echo ""

# 5. 更新.bashrc（可选）
echo "5. PATH更新建议:"
echo ""
echo "临时添加到PATH:"
echo "  export PATH=\$PATH:/home/toufumind/.openclaw/workspace"
echo ""
echo "永久添加到~/.bashrc:"
echo "  echo 'export PATH=\$PATH:/home/toufumind/.openclaw/workspace' >> ~/.bashrc"
echo "  source ~/.bashrc"
echo ""

# 6. 创建符号链接
echo "6. 创建符号链接到/usr/local/bin（需要sudo）:"
echo "  sudo ln -sf /home/toufumind/.openclaw/workspace/openclaw-wrapper.sh /usr/local/bin/openclaw"
echo ""

echo "=== 修复完成 ==="
echo "使用方法:"
echo "1. 临时使用: /home/toufumind/.openclaw/workspace/openclaw-wrapper.sh [命令]"
echo "2. 或直接调用: node /home/toufumind/.openclaw/extensions/qqbot/node_modules/.pnpm/openclaw@2026.3.8_@napi-rs+canvas@0.1.96_@types+express@5.0.6_hono@4.11.4_node-llama-cpp@3.16.2_typescript@5.9.3_/node_modules/openclaw/openclaw.mjs [命令]"
echo ""

# 7. 测试心跳脚本修复
echo "7. 修复心跳脚本..."
HEARTBEAT_SCRIPT="/home/toufumind/.openclaw/workspace/auto-producer.sh"
if [ -f "$HEARTBEAT_SCRIPT" ]; then
    # 备份原脚本
    cp "$HEARTBEAT_SCRIPT" "${HEARTBEAT_SCRIPT}.backup.$(date +%Y%m%d%H%M%S)"
    
    # 修复脚本中的openclaw调用
    sed -i 's|openclaw |/home/toufumind/.openclaw/workspace/openclaw-wrapper.sh |g' "$HEARTBEAT_SCRIPT"
    
    echo "✅ 心跳脚本已修复并备份"
    echo "原脚本备份为: ${HEARTBEAT_SCRIPT}.backup.*"
else
    echo "⚠️ 心跳脚本未找到: $HEARTBEAT_SCRIPT"
fi