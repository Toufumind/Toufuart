#!/bin/bash
# Toufuart仓库整理脚本
# 目标：清理混乱的文件夹结构，重新组织内容

set -e

echo "=== 开始整理Toufuart仓库 ==="
echo "当前目录: $(pwd)"
echo ""

# 1. 备份当前状态
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
echo "1. 创建备份目录: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 2. 整理articles文件夹
echo "2. 整理articles文件夹..."
if [ -d "articles" ]; then
    echo "  找到articles文件夹，包含文件:"
    find articles/ -type f -name "*.md" | while read file; do
        echo "    - $(basename "$file")"
    done
    
    # 将articles中的文件移动到按日期组织的目录
    for article_file in articles/*.md; do
        if [ -f "$article_file" ]; then
            # 从文件名提取日期
            filename=$(basename "$article_file")
            if [[ "$filename" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})\.md$ ]]; then
                date_dir="${BASH_REMATCH[1]}"
                echo "    移动 $filename 到 $date_dir/"
                
                # 如果目标目录不存在，创建它
                if [ ! -d "$date_dir" ]; then
                    mkdir -p "$date_dir"
                    echo "    创建目录: $date_dir"
                fi
                
                # 移动文件
                mv "$article_file" "$date_dir/article-summary.md"
                
                # 如果目标目录已有README，合并内容
                if [ -f "$date_dir/README.md" ]; then
                    echo "    $date_dir/README.md已存在，合并内容..."
                    echo -e "\n## 早期文章收集\n" >> "$date_dir/README.md"
                    cat "$date_dir/article-summary.md" >> "$date_dir/README.md"
                    rm "$date_dir/article-summary.md"
                else
                    # 重命名为README
                    mv "$date_dir/article-summary.md" "$date_dir/README.md"
                fi
            else
                echo "    跳过非标准命名的文件: $filename"
                mv "$article_file" "$BACKUP_DIR/"
            fi
        fi
    done
    
    # 检查articles是否为空，如果是则删除
    if [ -z "$(ls -A articles/ 2>/dev/null)" ]; then
        echo "   articles文件夹为空，删除..."
        rmdir articles/
    else
        echo "   articles文件夹仍有内容，移动到备份..."
        mv articles/ "$BACKUP_DIR/"
    fi
else
    echo "   articles文件夹不存在"
fi

echo ""

# 3. 整理qa文件夹
echo "3. 整理qa文件夹..."
if [ -d "qa" ]; then
    echo "  找到qa文件夹"
    # 创建专门的问答目录
    mkdir -p "knowledge-base"
    
    # 移动qa内容到knowledge-base
    if [ -n "$(ls -A qa/ 2>/dev/null)" ]; then
        echo "  移动qa内容到knowledge-base/qa/"
        mv qa/ "knowledge-base/qa/"
    else
        rmdir qa/
    fi
fi

echo ""

# 4. 整理备份文件夹
echo "4. 整理备份文件夹..."
if [ -d "workspace-backup" ] || [ -d "idea-factory-backup" ]; then
    echo "  创建统一的backups目录..."
    mkdir -p "backups"
    
    if [ -d "workspace-backup" ]; then
        echo "  移动workspace-backup到backups/"
        mv workspace-backup/ "backups/workspace/"
    fi
    
    if [ -d "idea-factory-backup" ]; then
        echo "  移动idea-factory-backup到backups/"
        mv idea-factory-backup/ "backups/idea-factory/"
    fi
fi

echo ""

# 5. 创建新的目录结构
echo "5. 创建新的目录结构..."
mkdir -p "resources"           # 资源收集
mkdir -p "projects"           # 项目文件
mkdir -p "docs"               # 文档
mkdir -p "tools"              # 工具脚本
mkdir -p "templates"          # 模板

echo "  创建目录:"
echo "    - resources/     # 每日资源收集"
echo "    - projects/      # 项目文件"
echo "    - docs/          # 文档"
echo "    - tools/         # 工具脚本"
echo "    - templates/     # 模板"

echo ""

# 6. 移动现有内容到新结构
echo "6. 移动现有内容到新结构..."

# 移动每日资源到resources/
for dir in 2026-*; do
    if [ -d "$dir" ] && [[ "$dir" =~ ^2026-[0-9]{2}-[0-9]{2} ]]; then
        echo "  移动 $dir 到 resources/"
        mv "$dir" "resources/"
    fi
done

# 移动AI分析到projects/
if [ -d "resources/2026-03-11-12_AI-Assistant-Analysis" ]; then
    echo "  移动AI分析到 projects/ai-analysis/"
    mkdir -p "projects/ai-analysis"
    mv "resources/2026-03-11-12_AI-Assistant-Analysis/"* "projects/ai-analysis/" 2>/dev/null || true
    rmdir "resources/2026-03-11-12_AI-Assistant-Analysis" 2>/dev/null || true
fi

# 移动工具脚本到tools/
if [ -f "push_to_github.sh" ]; then
    echo "  移动 push_to_github.sh 到 tools/"
    mv push_to_github.sh tools/
fi

if [ -f "keywords.txt" ]; then
    echo "  移动 keywords.txt 到 docs/"
    mv keywords.txt docs/
fi

echo ""

# 7. 创建README文件说明新结构
echo "7. 创建README文件..."
cat > README.md << 'EOF'
# Toufuart - TechArt资源仓库

## 📁 仓库结构

```
Toufuart/
├── README.md              # 本文件
├── resources/             # 每日资源收集
│   ├── 2026-03-10/       # 按日期组织的资源
│   ├── 2026-03-11/       # 每日收集的TechArt资源
│   └── 2026-03-12/       # 包含README和具体资源文件
├── projects/              # 项目文件
│   └── ai-analysis/      # AI助手分析项目
├── docs/                  # 文档
│   └── keywords.txt      # 关键词库
├── tools/                 # 工具脚本
│   └── push_to_github.sh # GitHub推送工具
├── knowledge-base/        # 知识库
│   └── qa/               # 问答记录
├── backups/               # 备份文件
│   ├── workspace/        # 工作空间备份
│   └── idea-factory/     # 创意点子备份
└── templates/            # 模板文件（空）
```

## 🎯 项目目标

收集、整理和分享高质量的技术美术（TechArt）学习资源，包括：
- 渲染技术、着色器编程
- 工具开发（Blender、Unity、Unreal插件）
- 性能优化、图形学原理
- AI在美术工作流中的应用

## 📅 每日收集流程

1. **关键词匹配**：基于keywords.txt中的关键词
2. **资源验证**：检查链接可访问性和内容质量
3. **摘要生成**：提取核心技术和学习要点
4. **分类整理**：按主题和技术领域分类
5. **Git提交**：每日自动提交到仓库

## 🔧 使用说明

### 查看资源
```bash
# 查看某日资源
cd resources/2026-03-12/
cat README.md

# 查看具体资源文件
cat 01_GPU_Gems_3:_并行前缀和扫描.md
```

### 添加新资源
1. 在对应日期的目录创建Markdown文件
2. 按照模板格式编写内容
3. 更新README.md中的资源列表
4. 提交到GitHub

### 更新关键词库
编辑 `docs/keywords.txt`，每行一个关键词。

## 📊 统计信息

- **开始时间**: 2026年3月
- **资源总数**: 持续增长中
- **覆盖领域**: 渲染技术、工具开发、性能优化等
- **更新频率**: 每日自动收集

## 🤝 贡献指南

欢迎提交：
1. 高质量TechArt资源链接
2. 技术文章和教程
3. 工具和脚本
4. 项目经验和心得

请确保内容：
- 真实可访问
- 技术先进实用
- 格式规范清晰

## 📄 许可证

本仓库内容遵循 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可证。

## 📞 联系方式

- GitHub: [Toufumind](https://github.com/Toufumind)
- 项目主页: https://github.com/Toufumind/Toufuart

---
*最后更新: $(date +%Y-%m-%d)*
*自动化维护中...*
EOF

echo "✅ README.md已创建"

echo ""

# 8. 创建.gitignore更新
echo "8. 更新.gitignore..."
cat >> .gitignore << 'EOF'

# 备份目录
backup_*/
backups/workspace/  # 工作空间备份，通常很大
backups/idea-factory/  # 点子备份

# 临时文件
*.tmp
*.temp
*.log

# 系统文件
.DS_Store
Thumbs.db
EOF

echo "✅ .gitignore已更新"

echo ""

# 9. 显示整理后的结构
echo "9. 整理后的目录结构:"
tree -L 2 --dirsfirst 2>/dev/null || find . -maxdepth 2 -type d | sort

echo ""

# 10. Git操作
echo "10. 准备Git提交..."
echo "  当前分支: $(git branch --show-current 2>/dev/null || echo '未知')"
echo "  状态:"
git status --short 2>/dev/null || echo "  未在Git仓库中"

echo ""
echo "=== 整理完成 ==="
echo ""
echo "下一步操作建议:"
echo "1. 检查整理结果: ls -la"
echo "2. 查看新结构: tree -L 2"
echo "3. 提交更改: git add . && git commit -m '整理仓库结构'"
echo "4. 推送到GitHub: git push origin main"
echo ""
echo "备份文件保存在: $BACKUP_DIR/"
echo "如有问题可以从备份恢复"