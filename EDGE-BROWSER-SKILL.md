# Edge Browser Control Skill

## 功能概述
通过命令行控制 Microsoft Edge 浏览器，支持截图、网页内容提取、PDF 生成等操作。

## 核心功能

### 1. 网页截图
```bash
# 基本截图
microsoft-edge --headless --disable-gpu --no-sandbox --screenshot https://example.com

# 自定义尺寸
microsoft-edge --headless --screenshot --window-size=1280,720 https://example.com

# 指定文件名
microsoft-edge --headless --screenshot=custom.png https://example.com
```

### 2. 内容提取
```bash
# 获取网页 DOM
microsoft-edge --headless --dump-dom https://example.com

# 提取特定内容
microsoft-edge --headless --dump-dom https://news.baidu.com | grep -i "热点"
```

### 3. PDF 生成
```bash
# 生成 PDF
microsoft-edge --headless --print-to-pdf https://example.com

# 指定输出文件
microsoft-edge --headless --print-to-pdf --output=report.pdf https://example.com
```

## 常用参数

### 性能优化
- `--disable-gpu` - 禁用 GPU 加速
- `--no-sandbox` - 禁用沙盒（某些环境需要）
- `--disable-dev-shm-usage` - 解决共享内存问题

### 网络设置
- `--proxy-server="http://proxy:port"` - 设置代理
- `--user-agent="自定义UA"` - 自定义用户代理

## 与 OpenClaw 集成

### 截图并发送到 QQ
```bash
# 截图
microsoft-edge --headless --screenshot --window-size=800,600 https://zhihu.com

# 发送
<qqimg>/tmp/screenshot.png</qqimg>
```

### 定时监控
```bash
# 每天9点截图
0 9 * * * microsoft-edge --headless --screenshot --window-size=1024,768 https://target.com -o /var/screenshots/daily.png
```

## 示例脚本

### 批量截图
```bash
#!/bin/bash
# batch-screenshot.sh
SITES=("https://baidu.com" "https://zhihu.com" "https://github.com")

for site in "${SITES[@]}"; do
  filename=$(echo $site | sed 's|https://||' | sed 's|/|_|g').png
  microsoft-edge --headless --screenshot=$filename --window-size=1024,768 $site
  echo "Screenshot saved: $filename"
done
```

### 网站监控
```bash
#!/bin/bash
# monitor-website.sh
URL="https://target.com"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="/tmp/monitor_${TIMESTAMP}.png"

# 截图
microsoft-edge --headless --disable-gpu --no-sandbox --screenshot=$FILENAME --window-size=1280,720 $URL

# 检查文件大小（确保截图成功）
if [ -s $FILENAME ]; then
  echo "监控成功: $FILENAME"
  # 可以在这里添加发送逻辑
else
  echo "监控失败"
fi
```

## 故障排除

### 常见问题
1. **GPU 警告**：总是使用 `--disable-gpu`
2. **内存问题**：添加 `--disable-dev-shm-usage`
3. **超时**：使用 `timeout` 命令限制执行时间

### 性能建议
1. 小窗口尺寸渲染更快
2. 避免 JavaScript 重的网站
3. 定期清理临时文件

## 使用场景

### 1. 网站监控
- 每日截图对比
- 内容更新检测
- 可用性检查

### 2. 文档归档
- 网页转 PDF
- 重要页面存档
- 视觉参考创建

### 3. 数据收集
- 表格数据提取
- 价格/股票监控
- 新闻标题跟踪

## 限制说明
1. **无交互控制**：不能点击按钮或填写表单
2. **JavaScript 有限**：重度依赖 JS 的网站可能无法完全渲染
3. **仅限无头模式**：无 GUI 交互
4. **性能限制**：大页面可能超时或占用大量内存

---

**技能创建完成**：Edge 浏览器控制技能已就绪，包含完整的命令行操作指南和集成示例。