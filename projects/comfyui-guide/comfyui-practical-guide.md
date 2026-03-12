# ComfyUI 实战指南 - 从入门到精通

## 🎯 本文档目标
**不是**代码分析，**而是**实用指南：
1. **快速上手** - 10分钟创建第一个工作流
2. **解决实际问题** - 常见问题解决方案
3. **效率提升** - 工作流优化技巧
4. **扩展开发** - 自定义节点开发

## 📦 快速开始

### 1. 安装（最简单的方法）
```bash
# 使用一键安装脚本
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

### 2. 启动
```bash
python main.py --listen  # 允许网络访问
# 打开浏览器访问: http://localhost:8188
```

### 3. 你的第一个工作流（5分钟）
1. **加载模型**：右键 → Load Checkpoint → 选择模型
2. **输入提示词**：添加 CLIP Text Encode 节点
3. **生成图片**：添加 KSampler 节点
4. **保存图片**：添加 Save Image 节点
5. **连接所有节点**，点击 Queue Prompt

## 🔧 常见问题解决方案

### 问题1：显存不足（Out of Memory）
**解决方案**：
```python
# 方法1：启用CPU卸载（配置文件）
# extra_model_paths.yaml
cuda_malloc: false
cpu_only: false
unet_in_cpu: true  # UNET模型放CPU

# 方法2：命令行参数
python main.py --lowvram --normalvram

# 方法3：工作流优化
# 使用 Latent Upscale 而不是直接高分辨率
# 使用 Tile 技术分块处理大图
```

### 问题2：加载模型失败
**检查清单**：
1. ✅ 模型格式正确（.safetensors 或 .ckpt）
2. ✅ 模型放在正确目录：`ComfyUI/models/checkpoints/`
3. ✅ 模型与ComfyUI版本兼容
4. ✅ 有足够的磁盘空间

### 问题3：工作流太卡
**优化技巧**：
1. **节点简化**：删除不必要的节点
2. **缓存利用**：启用节点缓存
3. **批量处理**：使用 Batch 节点
4. **分辨率优化**：先小图生成，再放大

## 🚀 效率提升技巧

### 1. 快捷键大全
```
Ctrl+S: 保存工作流
Ctrl+O: 加载工作流  
Ctrl+Shift+S: 另存为图片
Ctrl+Z: 撤销
Ctrl+Y: 重做
空格键: 拖动画布
鼠标中键: 快速移动
```

### 2. 工作流模板
创建可复用的模板文件（JSON格式）：
```json
{
  "workflow": {
    "nodes": [
      {
        "id": "1",
        "type": "CLIPTextEncode",
        "inputs": {"text": "masterpiece, best quality"}
      }
    ]
  }
}
```

### 3. 自定义节点推荐
```python
# 安装实用节点
cd ComfyUI/custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager  # 节点管理器
git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts  # 自定义脚本
```

## 💻 自定义节点开发（实战）

### 最简单的自定义节点
```python
# custom_nodes/my_node.py
import torch
from comfy.sd import CLIP

class SimpleTextProcessor:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "multiplier": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "process"
    CATEGORY = "My Nodes"
    
    def process(self, text, multiplier):
        # 简单的文本处理：重复文本
        processed = text * int(multiplier)
        return (processed,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "SimpleTextProcessor": SimpleTextProcessor
}
```

### 安装你的节点
1. 将文件放到 `ComfyUI/custom_nodes/`
2. 重启ComfyUI
3. 在节点列表中找到 "My Nodes" → "SimpleTextProcessor"

## 🎨 实际应用案例

### 案例1：批量处理图片
```python
# 工作流设计
1. Load Image (Batch) → 2. Image Preprocess → 3. KSampler → 4. Save Image (Batch)
# 使用 ComfyUI-Impact-Pack 的 Batch 节点
```

### 案例2：风格迁移
```python
# 使用 ControlNet
1. Load Base Image → 2. ControlNet Apply → 3. KSampler → 4. Save
# 推荐节点: ComfyUI-Advanced-ControlNet
```

### 案例3：视频生成
```python
# 使用 AnimateDiff
1. Load Checkpoint (with motion) → 2. Text Encode → 3. AnimateDiff Loader
4. KSampler → 5. VAE Decode → 6. Save Video
# 推荐: ComfyUI-AnimateDiff-Evolved
```

## 📊 性能优化指南

### GPU 优化
```bash
# NVIDIA 显卡优化
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
export CUDA_LAUNCH_BLOCKING=1

# AMD 显卡（Linux）
export HSA_OVERRIDE_GFX_VERSION=10.3.0
```

### 内存管理
```python
# 配置文件优化（extra_model_paths.yaml）
memory_management:
  unet_offload: true      # UNET放CPU
  vae_offload: true       # VAE放CPU  
  clip_offload: false     # CLIP放GPU（需要频繁使用）
  
# 工作流内存优化技巧
1. 使用 Latent Preview 预览而不是完整解码
2. 分阶段处理：先低分辨率，再放大
3. 及时清理缓存：Settings → Clear Cache
```

## 🔗 资源推荐

### 学习资源
1. **官方文档**: https://comfyanonymous.github.io/ComfyUI/
2. **视频教程**: YouTube搜索 "ComfyUI tutorial"
3. **社区**: https://github.com/comfyanonymous/ComfyUI/discussions

### 模型资源
1. **Civitai**: https://civitai.com/ (社区模型)
2. **Hugging Face**: https://huggingface.co/ (官方模型)
3. **模型格式转换**: https://github.com/AUTOMATIC1111/stable-diffusion-webui

### 工具推荐
1. **工作流分享**: https://comfyworkflows.com/
2. **节点管理器**: ComfyUI-Manager
3. **工作流可视化**: ComfyUI-Custom-Scripts

## 🐛 故障排除

### 常见错误及解决
```
错误: "No module named 'comfy'"
解决: 确保在 ComfyUI 目录下运行

错误: "CUDA out of memory"
解决: 降低分辨率，启用 --lowvram

错误: "Model loading failed"
解决: 检查模型路径和格式

错误: "Node not found"
解决: 安装对应的自定义节点
```

### 调试模式
```bash
# 启用详细日志
python main.py --verbose

# 查看GPU状态
nvidia-smi  # NVIDIA
rocm-smi    # AMD

# 检查Python环境
python -c "import torch; print(torch.cuda.is_available())"
```

## 📈 进阶学习路径

### 阶段1：基础掌握（1-2周）
1. 基本节点使用
2. 工作流创建和保存
3. 模型加载和管理

### 阶段2：效率提升（2-4周）
1. 自定义节点安装
2. 工作流优化
3. 批量处理技巧

### 阶段3：深度定制（1-2月）
1. 自定义节点开发
2. 模型训练集成
3. API接口开发

### 阶段4：生产部署
1. 服务器部署
2. 自动化流水线
3. 团队协作配置

## 🎉 总结

ComfyUI 的核心优势：
1. **可视化编程** - 无需写代码即可创建复杂工作流
2. **高性能** - 优化的内存管理和GPU利用
3. **可扩展** - 丰富的自定义节点生态
4. **可复现** - 工作流文件确保结果一致性

**最重要的一点**：不要被复杂的节点吓到，从简单的开始，逐步构建你的工作流库。

---
*文档版本: 2.0 (实战指南版)*
*更新日期: 2026-03-12*
*目标: 提供真正有用的ComfyUI学习资源*