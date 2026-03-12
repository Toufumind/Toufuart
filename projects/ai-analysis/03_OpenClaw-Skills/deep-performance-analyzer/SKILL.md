# 深度性能分析技能

## 描述
深度分析AI系统性能，从应用层（ComfyUI）到硬件层（CUDA/GPU）的完整栈性能分析。

## 命令分发
command-dispatch: tool
command-tool: deep_performance_analyzer

## 功能
1. **系统级分析**: CUDA设备性能基准测试
2. **应用级分析**: PyTorch模型性能分析
3. **工作流分析**: ComfyUI工作流性能优化
4. **优化建议**: 基于性能数据的优化策略

## 使用示例
```
/deep-analyze cuda           # 分析CUDA设备性能
/deep-analyze pytorch-model  # 分析PyTorch模型性能  
/deep-analyze comfyui-workflow # 分析ComfyUI工作流
/deep-analyze optimize       # 生成优化建议
```

## 技术栈
- Python 3.8+
- PyTorch 2.0+
- CUDA Toolkit 11.8+
- Nsight Systems (可选)

## 输出格式
- JSON性能报告
- 可视化性能图表
- 优化建议文档
- 基准测试结果