#!/bin/bash
# 修复版自动化产出脚本 - 每3小时执行
# 版本: 2.1
# 功能: 系统检查 + 学习产出 + 项目推进 + 问题分析

set -e  # 遇到错误时退出

# 配置
WORKSPACE="/home/toufumind/.openclaw/workspace"
LOG_FILE="$WORKSPACE/heartbeat-log-$(date +%Y%m%d).txt"
TRACKER_FILE="$WORKSPACE/heartbeat-output-tracker.md"
MEMORY_DIR="$WORKSPACE/memory"
LEARNINGS_DIR="$WORKSPACE/learnings"
IDEA_DIR="$WORKSPACE/idea-factory"
TOUFUART_DIR="$WORKSPACE/Toufuart"

# 工具路径
OPENCLAW_WRAPPER="$WORKSPACE/openclaw-wrapper.sh"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
DATE_TODAY=$(date +%Y-%m-%d)

echo "=== Heartbeat产出检查 $TIMESTAMP ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# ==================== 1. 系统状态检查 ====================
echo "[$(date '+%H:%M:%S')] 1. 系统状态检查..." | tee -a "$LOG_FILE"

# 磁盘使用
DISK_INFO=$(df -h /home/toufumind/.openclaw/workspace | tail -1)
DISK_TOTAL=$(echo "$DISK_INFO" | awk '{print $2}')
DISK_USED=$(echo "$DISK_INFO" | awk '{print $3}')
DISK_AVAIL=$(echo "$DISK_INFO" | awk '{print $4}')
DISK_USE_PCT=$(echo "$DISK_INFO" | awk '{print $5}')

# 内存使用
MEM_INFO=$(free -h | grep Mem)
MEM_TOTAL=$(echo "$MEM_INFO" | awk '{print $2}')
MEM_USED=$(echo "$MEM_INFO" | awk '{print $3}')
MEM_AVAIL=$(echo "$MEM_INFO" | awk '{print $7}')

# OpenClaw状态
OPENCLAW_STATUS=$("$OPENCLAW_WRAPPER" gateway status 2>&1 || echo "gateway status failed")

echo "✅ 磁盘: $DISK_TOTAL总/$DISK_USED已用/$DISK_AVAIL可用 ($DISK_USE_PCT)" | tee -a "$LOG_FILE"
echo "✅ 内存: $MEM_TOTAL总/$MEM_USED已用/$MEM_AVAIL可用" | tee -a "$LOG_FILE"

if echo "$OPENCLAW_STATUS" | grep -q "running"; then
    echo "✅ OpenClaw网关: 运行中" | tee -a "$LOG_FILE"
else
    echo "⚠️  OpenClaw网关: $OPENCLAW_STATUS" | tee -a "$LOG_FILE"
fi

# ==================== 2. 学习进展检查 ====================
echo "[$(date '+%H:%M:%S')] 2. 学习进展检查..." | tee -a "$LOG_FILE"

# 检查今日学习笔记
TODAY_LEARNINGS=$(find "$LEARNINGS_DIR" -name "*$DATE_TODAY*" -type f | wc -l)
if [ "$TODAY_LEARNINGS" -gt 0 ]; then
    echo "✅ 今日学习笔记: $TODAY_LEARNINGS 篇" | tee -a "$LOG_FILE"
    find "$LEARNINGS_DIR" -name "*$DATE_TODAY*" -type f -exec basename {} \; | while read file; do
        echo "  - $file" | tee -a "$LOG_FILE"
    done
else
    echo "⚠️  今日尚无学习笔记，需要创建..." | tee -a "$LOG_FILE"
fi

# ==================== 3. 代码/文档产出检查 ====================
echo "[$(date '+%H:%M:%S')] 3. 代码/文档产出检查..." | tee -a "$LOG_FILE"

# 检查最近3小时修改的文件
RECENT_FILES=$(find "$WORKSPACE" -type f \( -name "*.py" -o -name "*.md" -o -name "*.sh" -o -name "*.js" -o -name "*.json" \) -mmin -180 2>/dev/null | wc -l)

if [ "$RECENT_FILES" -gt 0 ]; then
    echo "✅ 最近3小时修改文件数: $RECENT_FILES 个" | tee -a "$LOG_FILE"
    
    # 显示部分文件
    find "$WORKSPACE" -type f \( -name "*.py" -o -name "*.md" -o -name "*.sh" \) -mmin -180 2>/dev/null | head -5 | while read file; do
        echo "  - $(basename "$file")" | tee -a "$LOG_FILE"
    done
else
    echo "⚠️  最近3小时无代码/文档修改，需要创建产出..." | tee -a "$LOG_FILE"
fi

# ==================== 4. 项目推进检查 ====================
echo "[$(date '+%H:%M:%S')] 4. 项目推进检查..." | tee -a "$LOG_FILE"

# 检查TechArt资源收集器
RESOURCE_COUNT=0
if [ -d "$TOUFUART_DIR/$DATE_TODAY" ]; then
    RESOURCE_COUNT=$(find "$TOUFUART_DIR/$DATE_TODAY" -name "*.md" ! -name "README.md" 2>/dev/null | wc -l)
    echo "✅ TechArt资源收集器: 今日已收集 $RESOURCE_COUNT 篇资源" | tee -a "$LOG_FILE"
else
    echo "⚠️  TechArt资源收集器: 今日未运行" | tee -a "$LOG_FILE"
fi

# 检查创意点子生成器
IDEA_COUNT=0
if [ -d "$IDEA_DIR/$DATE_TODAY" ]; then
    IDEA_COUNT=$(find "$IDEA_DIR/$DATE_TODAY" -name "*.md" 2>/dev/null | wc -l)
    if [ "$IDEA_COUNT" -gt 0 ]; then
        echo "✅ 创意点子生成器: 今日已生成 $IDEA_COUNT 个点子" | tee -a "$LOG_FILE"
    else
        if [ -f "$IDEA_DIR/$DATE_TODAY/README.md" ]; then
            echo "✅ 创意点子生成器: 今日已生成汇总文件" | tee -a "$LOG_FILE"
        else
            echo "⚠️  创意点子生成器: 今日未运行" | tee -a "$LOG_FILE"
        fi
    fi
else
    echo "⚠️  创意点子生成器: 今日目录未创建" | tee -a "$LOG_FILE"
fi

# ==================== 5. 问题分析检查 ====================
echo "[$(date '+%H:%M:%S')] 5. 问题分析检查..." | tee -a "$LOG_FILE"

# 检查错误日志
ERROR_COUNT=0
if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -i "error\|failed\|❌" "$LOG_FILE" 2>/dev/null | tail -5 | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "⚠️  发现 $ERROR_COUNT 个错误/警告" | tee -a "$LOG_FILE"
        grep -i "error\|failed\|❌" "$LOG_FILE" 2>/dev/null | tail -3 | while read error; do
            echo "  - $error" | tee -a "$LOG_FILE"
        done
    else
        echo "✅ 无错误日志" | tee -a "$LOG_FILE"
    fi
fi

# ==================== 6. 更新产出跟踪器 ====================
echo "[$(date '+%H:%M:%S')] 6. 更新产出跟踪器..." | tee -a "$LOG_FILE"

# 创建跟踪器条目
TRACKER_ENTRY="### $TIMESTAMP 产出检查\n"
TRACKER_ENTRY+="- **系统状态**: 磁盘 $DISK_USE_PCT, 内存 $MEM_AVAIL 可用\n"
TRACKER_ENTRY+="- **学习进展**: $TODAY_LEARNINGS 篇学习笔记\n"
TRACKER_ENTRY+="- **代码产出**: $RECENT_FILES 个文件修改\n"
TRACKER_ENTRY+="- **项目推进**: TechArt($RESOURCE_COUNT篇) 点子($IDEA_COUNT个)\n"
TRACKER_ENTRY+="- **问题分析**: $ERROR_COUNT 个错误/警告\n"
TRACKER_ENTRY+="- **产出质量**: 持续改进中\n\n"

# 添加到跟踪器文件
if [ -f "$TRACKER_FILE" ]; then
    # 在文件末尾添加
    echo -e "$TRACKER_ENTRY" >> "$TRACKER_FILE"
else
    # 创建新文件
    cat > "$TRACKER_FILE" << EOF
# Heartbeat产出跟踪器

## 产出要求（每小时）
- [ ] 技术学习进展（至少一个知识点）
- [ ] 代码/文档产出（至少一个文件）
- [ ] 项目推进（至少一个任务）
- [ ] 问题解决（至少一个分析）

$TRACKER_ENTRY
EOF
fi

echo "✅ 产出跟踪器已更新" | tee -a "$LOG_FILE"

# ==================== 7. 生成汇总报告 ====================
echo "[$(date '+%H:%M:%S')] 7. 生成汇总报告..." | tee -a "$LOG_FILE"

REPORT_FILE="$MEMORY_DIR/${DATE_TODAY}-heartbeat-report.md"
cat > "$REPORT_FILE" << EOF
# $DATE_TODAY Heartbeat检查报告

## 检查时间
$TIMESTAMP

## 系统状态
- **磁盘**: $DISK_TOTAL总 / $DISK_USED已用 / $DISK_AVAIL可用 ($DISK_USE_PCT)
- **内存**: $MEM_TOTAL总 / $MEM_USED已用 / $MEM_AVAIL可用
- **OpenClaw**: $(echo "$OPENCLAW_STATUS" | head -1)

## 学习进展
- **今日学习笔记**: $TODAY_LEARNINGS 篇

## 代码/文档产出
- **最近3小时修改**: $RECENT_FILES 个文件

## 项目推进
- **TechArt资源收集器**: $RESOURCE_COUNT 篇资源
- **创意点子生成器**: $IDEA_COUNT 个点子

## 问题分析
- **错误/警告数量**: $ERROR_COUNT 个

## 产出质量评估
- **完整性**: $([ $TODAY_LEARNINGS -gt 0 ] && [ $RECENT_FILES -gt 0 ] && echo "✅ 完整" || echo "⚠️ 待完善")
- **及时性**: ✅ 按时检查
- **实用性**: $([ $RESOURCE_COUNT -gt 0 ] || [ $IDEA_COUNT -gt 0 ] && echo "✅ 有实际产出" || echo "⚠️ 需加强")

## 改进建议
1. $([ $TODAY_LEARNINGS -eq 0 ] && echo "创建今日学习笔记" || echo "深化学习内容")
2. $([ $RECENT_FILES -eq 0 ] && echo "增加代码/文档产出" || echo "优化现有代码")
3. $([ $RESOURCE_COUNT -eq 0 ] && echo "运行TechArt资源收集器" || echo "分析资源质量")
4. $([ $IDEA_COUNT -eq 0 ] && echo "生成创意点子" || echo "评估点子可行性")

## 下一步行动
1. 执行改进建议
2. 准备下一次检查
3. 优化自动化流程

---
*报告生成时间: $TIMESTAMP*
*脚本版本: 2.1*
EOF

echo "✅ 汇总报告已生成: $(basename "$REPORT_FILE")" | tee -a "$LOG_FILE"

# ==================== 完成 ====================
echo "" | tee -a "$LOG_FILE"
echo "✅ Heartbeat检查完成！" | tee -a "$LOG_FILE"
echo "详细日志: $LOG_FILE" | tee -a "$LOG_FILE"
echo "汇总报告: $REPORT_FILE" | tee -a "$LOG_FILE"
echo "产出跟踪: $TRACKER_FILE" | tee -a "$LOG_FILE"

# 退出状态
exit 0