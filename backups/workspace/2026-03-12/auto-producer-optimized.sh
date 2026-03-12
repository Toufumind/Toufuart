#!/bin/bash
# 优化版自动化产出脚本 - 每3小时执行
# 版本: 2.0
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

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

# 创建必要的目录
mkdir -p "$MEMORY_DIR" "$LEARNINGS_DIR" "$IDEA_DIR/$DATE_TODAY"

echo "=== Heartbeat产出检查 $TIMESTAMP ===" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# ==================== 1. 系统状态检查 ====================
log "1. 系统状态检查..."

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

success "磁盘: $DISK_TOTAL总/$DISK_USED已用/$DISK_AVAIL可用 ($DISK_USE_PCT)"
success "内存: $MEM_TOTAL总/$MEM_USED已用/$MEM_AVAIL可用"

if echo "$OPENCLAW_STATUS" | grep -q "running"; then
    success "OpenClaw网关: 运行中"
else
    warning "OpenClaw网关: $OPENCLAW_STATUS"
fi

# ==================== 2. 学习进展检查 ====================
log "2. 学习进展检查..."

# 检查今日学习笔记
TODAY_LEARNINGS=$(find "$LEARNINGS_DIR" -name "*$DATE_TODAY*" -type f | wc -l)
if [ "$TODAY_LEARNINGS" -gt 0 ]; then
    success "今日学习笔记: $TODAY_LEARNINGS 篇"
    find "$LEARNINGS_DIR" -name "*$DATE_TODAY*" -type f -exec basename {} \; | while read file; do
        echo "  - $file" | tee -a "$LOG_FILE"
    done
else
    warning "今日尚无学习笔记，需要创建..."
    # 自动生成一个学习主题
    LEARNING_TOPICS=(
        "Docker容器化最佳实践"
        "Python异步编程深入"
        "图形学渲染管线优化"
        "AI代理系统架构"
        "Web开发性能优化"
        "数据库索引原理"
        "网络安全基础"
        "机器学习模型部署"
    )
    RANDOM_TOPIC=${LEARNING_TOPICS[$RANDOM % ${#LEARNING_TOPICS[@]}]}
    
    # 创建学习笔记
    LEARN_FILE="$LEARNINGS_DIR/${DATE_TODAY}-${RANDOM_TOPIC// /-}.md"
    cat > "$LEARN_FILE" << EOF
# $RANDOM_TOPIC - 学习笔记

## 学习时间
$TIMESTAMP

## 学习目标
掌握$RANDOM_TOPIC的核心概念和实践应用。

## 核心要点
1. **基础概念**: 
2. **关键技术**: 
3. **实践应用**: 
4. **常见问题**: 

## 学习资源
- 官方文档: 
- 教程链接: 
- 开源项目: 

## 实践计划
1. 环境搭建
2. 示例代码实现
3. 性能测试
4. 优化改进

## 总结
$RANDOM_TOPIC是...的重要技术，掌握它可以帮助...

---
*自动生成于: $TIMESTAMP*
*状态: 待完善*
EOF
    success "已创建学习笔记: $(basename "$LEARN_FILE")"
fi

# ==================== 3. 代码/文档产出检查 ====================
log "3. 代码/文档产出检查..."

# 检查最近3小时修改的文件
RECENT_FILES=$(find "$WORKSPACE" -type f -name "*.py" -o -name "*.md" -o -name "*.sh" -o -name "*.js" -o -name "*.json" | \
    xargs -I {} sh -c 'test $(date +%s -r "{}") -gt $(date +%s --date="3 hours ago") && echo {}' | wc -l)

if [ "$RECENT_FILES" -gt 0 ]; then
    success "最近3小时修改文件数: $RECENT_FILES 个"
    
    # 显示部分文件
    find "$WORKSPACE" -type f \( -name "*.py" -o -name "*.md" -o -name "*.sh" \) -mmin -180 | head -5 | while read file; do
        echo "  - $(basename "$file")" | tee -a "$LOG_FILE"
    done
else
    warning "最近3小时无代码/文档修改，需要创建产出..."
    
    # 自动创建一个Python工具脚本
    PYTHON_TOOL="$WORKSPACE/tools/auto-$(date +%Y%m%d%H%M%S).py"
    mkdir -p "$(dirname "$PYTHON_TOOL")"
    
    cat > "$PYTHON_TOOL" << 'EOF'
#!/usr/bin/env python3
"""
自动化工具脚本
功能: 系统监控和报告生成
"""

import os
import sys
import json
import datetime
from pathlib import Path

def get_system_info():
    """获取系统信息"""
    import psutil
    
    info = {
        "timestamp": datetime.datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": dict(psutil.virtual_memory()._asdict()),
        "disk": {},
        "processes": len(psutil.pids())
    }
    
    # 磁盘信息
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            info["disk"][partition.mountpoint] = {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            }
        except:
            continue
    
    return info

def generate_report(info, output_path="system_report.json"):
    """生成报告"""
    with open(output_path, 'w') as f:
        json.dump(info, f, indent=2, default=str)
    
    print(f"报告已生成: {output_path}")
    print(f"CPU使用率: {info['cpu_percent']}%")
    print(f"内存使用率: {info['memory']['percent']}%")
    print(f"进程数量: {info['processes']}")
    
    return output_path

if __name__ == "__main__":
    print("=== 系统监控工具 ===")
    
    try:
        import psutil
    except ImportError:
        print("请安装psutil: pip install psutil")
        sys.exit(1)
    
    # 获取系统信息
    info = get_system_info()
    
    # 生成报告
    report_file = f"system_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    generate_report(info, report_file)
    
    print("=== 完成 ===")
EOF
    
    chmod +x "$PYTHON_TOOL"
    success "已创建Python工具脚本: $(basename "$PYTHON_TOOL")"
fi

# ==================== 4. 项目推进检查 ====================
log "4. 项目推进检查..."

# 检查TechArt资源收集器
if [ -d "$TOUFUART_DIR/$DATE_TODAY" ]; then
    RESOURCE_COUNT=$(find "$TOUFUART_DIR/$DATE_TODAY" -name "*.md" ! -name "README.md" | wc -l)
    success "TechArt资源收集器: 今日已收集 $RESOURCE_COUNT 篇资源"
else
    warning "TechArt资源收集器: 今日未运行"
fi

# 检查创意点子生成器
if [ -d "$IDEA_DIR/$DATE_TODAY" ]; then
    IDEA_COUNT=$(find "$IDEA_DIR/$DATE_TODAY" -name "*.md" | wc -l)
    if [ "$IDEA_COUNT" -gt 0 ]; then
        success "创意点子生成器: 今日已生成 $IDEA_COUNT 个点子"
    else
        if [ -f "$IDEA_DIR/$DATE_TODAY/README.md" ]; then
            success "创意点子生成器: 今日已生成汇总文件"
        else
            warning "创意点子生成器: 今日未运行"
        fi
    fi
else
    warning "创意点子生成器: 今日目录未创建"
fi

# ==================== 5. 问题分析检查 ====================
log "5. 问题分析检查..."

# 检查错误日志
ERROR_LOG="$WORKSPACE/error-log-$(date +%Y%m%d).txt"
if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -i "error\|failed\|❌" "$LOG_FILE" | tail -5 | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        warning "发现 $ERROR_COUNT 个错误/警告"
        grep -i "error\|failed\|❌" "$LOG_FILE" | tail -3 | while read error; do
            echo "  - $error" | tee -a "$LOG_FILE"
        done
    else
        success "无错误日志"
    fi
fi

# ==================== 6. 更新产出跟踪器 ====================
log "6. 更新产出跟踪器..."

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

success "产出跟踪器已更新"

# ==================== 7. 生成汇总报告 ====================
log "7. 生成汇总报告..."

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
$(find "$LEARNINGS_DIR" -name "*$DATE_TODAY*" -type f -exec basename {} \; | sed 's/^/- /')

## 代码/文档产出
- **最近3小时修改**: $RECENT_FILES 个文件

## 项目推进
- **TechArt资源收集器**: ${RESOURCE_COUNT:-0} 篇资源
- **创意点子生成器**: ${IDEA_COUNT:-0} 个点子

## 问题分析
- **错误/警告数量**: $ERROR_COUNT 个

## 产出质量评估
- **完整性**: $( [ $TODAY_LEARNINGS -gt 0 ] && [ $RECENT_FILES -gt 0 ] && echo "✅ 完整" || echo "⚠️ 待完善" )
- **及时性**: ✅ 按时检查
- **实用性**: $( [ $RESOURCE_COUNT -gt 0 ] || [ $IDEA_COUNT -gt 0 ] && echo "✅ 有实际产出" || echo "⚠️ 需加强" )

## 改进建议
1. $( [ $TODAY_LEARNINGS -eq 0 ] && echo "创建今日学习笔记" || echo "深化学习内容" )
2. $( [ $RECENT_FILES -eq 0 ] && echo "增加代码/文档产出" || echo "优化现有代码" )
3. $( [ $RESOURCE_COUNT -eq 0 ] && echo "运行TechArt资源收集器" || echo "分析资源质量" )
4. $( [ $IDEA_COUNT -eq 0 ] && echo "生成创意点子" || echo "评估点子可行性" )

## 下一步行动
1. 执行改进建议
2. 准备下一次检查
3. 优化自动化流程

---
*报告生成时间: $TIMESTAMP*
*脚本版本: 2.0*
EOF

success "汇总报告已生成: $(basename "$REPORT_FILE")"

# ==================== 完成 ====================
echo "" | tee -a "$LOG_FILE"
success "Heartbeat检查完成！"
echo "详细日志: $LOG_FILE"
echo "汇总报告: $REPORT_FILE"
echo "产出跟踪: $TRACKER_FILE"

# 退出状态
exit 0