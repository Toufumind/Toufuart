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
