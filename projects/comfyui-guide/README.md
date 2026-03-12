# ComfyUI 自定义节点实战项目

## 🎯 项目目标
创建一个实用的ComfyUI自定义节点包，包含：
1. **文本处理节点** - 增强提示词功能
2. **图像工具节点** - 常用图像处理
3. **工作流工具** - 提高效率的工具

## 📁 项目结构
```
comfyui-custom-node-project/
├── __init__.py              # 包初始化
├── nodes_text.py           # 文本处理节点
├── nodes_image.py          # 图像处理节点  
├── nodes_utility.py        # 工具节点
├── requirements.txt        # 依赖包
├── README.md              # 说明文档
└── examples/              # 使用示例
    ├── workflow_basic.json
    └── workflow_advanced.json
```

## 🔧 安装和使用

### 1. 安装到ComfyUI
```bash
# 克隆到custom_nodes目录
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/comfyui-custom-node-project
cd comfyui-custom-node-project
pip install -r requirements.txt
```

### 2. 重启ComfyUI
```bash
cd ../..
python main.py
```

### 3. 在节点列表中找到
- **Text Tools** 类别
- **Image Tools** 类别  
- **Utility Tools** 类别

## 📝 节点功能详解

### 1. 文本处理节点 (nodes_text.py)

#### Text Concatenate - 文本拼接
```python
class TextConcatenate:
    """拼接多个文本，支持分隔符"""
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text1": ("STRING", {"default": "", "multiline": True}),
                "text2": ("STRING", {"default": "", "multiline": True}),
                "separator": ("STRING", {"default": ", "}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "concatenate"
    CATEGORY = "Text Tools"
    
    def concatenate(self, text1, text2, separator):
        result = f"{text1}{separator}{text2}"
        return (result,)
```

#### Text Weight Adjust - 权重调整
```python
class TextWeightAdjust:
    """调整提示词权重，如 (word:1.2)"""
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "keyword": ("STRING", {"default": ""}),
                "weight": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "adjust_weight"
    CATEGORY = "Text Tools"
    
    def adjust_weight(self, text, keyword, weight):
        if keyword and weight != 1.0:
            # 替换或添加权重
            pattern = rf'\b{re.escape(keyword)}\b'
            replacement = f'({keyword}:{weight:.1f})'
            result = re.sub(pattern, replacement, text)
            return (result,)
        return (text,)
```

### 2. 图像处理节点 (nodes_image.py)

#### Image Resize Proportional - 等比缩放
```python
class ImageResizeProportional:
    """保持宽高比的图像缩放"""
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "max_size": ("INT", {"default": 1024, "min": 64, "max": 4096}),
                "method": (["lanczos", "bicubic", "bilinear", "nearest"],),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "resize"
    CATEGORY = "Image Tools"
    
    def resize(self, image, max_size, method):
        # 获取原始尺寸
        B, H, W, C = image.shape
        
        # 计算等比缩放后的尺寸
        if H > W:
            new_h = max_size
            new_w = int(W * max_size / H)
        else:
            new_w = max_size
            new_h = int(H * max_size / W)
        
        # 使用PyTorch进行缩放
        image_tensor = image.permute(0, 3, 1, 2)  # BCHW格式
        resized = F.interpolate(
            image_tensor, 
            size=(new_h, new_w), 
            mode=method,
            align_corners=False
        )
        
        resized = resized.permute(0, 2, 3, 1)  # 转回BHWC格式
        return (resized,)
```

#### Image Batch Save - 批量保存
```python
class ImageBatchSave:
    """批量保存图像，自动命名"""
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "output"}),
                "output_dir": ("STRING", {"default": "output"}),
            },
            "optional": {
                "metadata": ("METADATA",),
            }
        }
    
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "save_batch"
    CATEGORY = "Image Tools"
    
    def save_batch(self, images, filename_prefix, output_dir, metadata=None):
        import os
        import datetime
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存每张图片
        saved_paths = []
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, image in enumerate(images):
            filename = f"{filename_prefix}_{timestamp}_{i:04d}.png"
            filepath = os.path.join(output_dir, filename)
            
            # 转换为PIL图像并保存
            pil_image = tensor2pil(image)
            if metadata:
                pil_image.info.update(metadata)
            
            pil_image.save(filepath, "PNG", pnginfo=metadata)
            saved_paths.append(filepath)
        
        # 返回保存的文件路径（用于后续节点）
        return {"ui": {"images": saved_paths}}
```

### 3. 工具节点 (nodes_utility.py)

#### Workflow Timer - 工作流计时器
```python
import time

class WorkflowTimer:
    """测量工作流执行时间"""
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "start_signal": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("STRING", "FLOAT")
    FUNCTION = "measure"
    CATEGORY = "Utility Tools"
    
    def __init__(self):
        self.start_time = None
    
    def measure(self, start_signal):
        if start_signal and self.start_time is None:
            # 开始计时
            self.start_time = time.time()
            return ("Timer started", 0.0)
        elif not start_signal and self.start_time is not None:
            # 结束计时
            elapsed = time.time() - self.start_time
            self.start_time = None
            return (f"Time elapsed: {elapsed:.2f}s", elapsed)
        
        return ("Timer ready", 0.0)
```

#### Random Seed Generator - 随机种子生成器
```python
import random

class RandomSeedGenerator:
    """生成随机种子，支持范围限制"""
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "min_value": ("INT", {"default": 0, "min": 0, "max": 2**32}),
                "max_value": ("INT", {"default": 2**32-1, "min": 0, "max": 2**32}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 100}),
            }
        }
    
    RETURN_TYPES = ("INT",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "generate"
    CATEGORY = "Utility Tools"
    
    def generate(self, min_value, max_value, batch_size):
        seeds = [random.randint(min_value, max_value) for _ in range(batch_size)]
        return (seeds,)
```

## 🚀 使用示例

### 示例1：增强提示词工作流
```
[Load Checkpoint] → [CLIP Text Encode Positive] 
                    ↓
[Text Concatenate] ← [Text Weight Adjust] ← [输入关键词]
                    ↓
[KSampler] → [VAE Decode] → [Save Image]
```

### 示例2：批量处理工作流
```
[Load Image Batch] → [Image Resize Proportional] 
                     ↓
[KSampler Batch] → [VAE Decode] → [Image Batch Save]
```

### 示例3：性能测试工作流
```
[Workflow Timer Start] → [完整生成流程] → [Workflow Timer End]
                         ↓
                    [显示耗时统计]
```

## 🔧 开发指南

### 1. 节点开发规范
```python
# 1. 必须的类属性
CATEGORY = "Your Category"      # 节点分类
FUNCTION = "your_function"      # 执行函数名
RETURN_TYPES = ("TYPE",)        # 返回类型

# 2. 输入类型定义
@classmethod
def INPUT_TYPES(s):
    return {
        "required": {
            "input1": ("STRING", {"default": ""}),
            "input2": ("INT", {"default": 0, "min": 0, "max": 100}),
        },
        "optional": {
            "optional_input": ("IMAGE",),
        }
    }

# 3. 执行函数
def your_function(self, input1, input2, optional_input=None):
    # 你的逻辑
    return (output,)
```

### 2. 调试技巧
```python
# 启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)

# 打印调试信息
print(f"Debug: input shape = {image.shape}")
print(f"Debug: text = {text}")

# 使用ComfyUI的日志系统
from comfy.utils import ProgressBar
progress_bar = ProgressBar(100)
for i in range(100):
    # 处理...
    progress_bar.update(1)
```

### 3. 性能优化
```python
# 使用GPU加速
image = image.to(torch.device("cuda"))

# 批量处理
if len(images) > 1:
    # 使用向量化操作
    result = torch.stack([process(img) for img in images])
    
# 内存优化
with torch.no_grad():
    # 不需要梯度的操作
    output = model(input)
```

## 📦 打包和发布

### 1. 创建setup.py
```python
from setuptools import setup, find_packages

setup(
    name="comfyui-custom-tools",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "Pillow>=9.0.0",
    ],
)
```

### 2. 发布到GitHub
```bash
# 创建仓库
git init
git add .
git commit -m "Initial release"
git remote add origin https://github.com/yourusername/comfyui-custom-node-project
git push -u origin main

# 创建发布
git tag v1.0.0
git push origin v1.0.0
```

### 3. 提交到ComfyUI Manager
1. 在 `comfyui-custom-node-project` 目录创建 `__init__.py`
2. 在GitHub创建Release
3. 提交到ComfyUI Manager的节点列表

## 🐛 常见问题

### Q: 节点不显示？
A: 检查：
1. 文件是否在 `custom_nodes` 目录
2. 是否有 `__init__.py`
3. 是否导入了 `NODE_CLASS_MAPPINGS`

### Q: 导入错误？
A: 检查依赖：
```bash
pip install -r requirements.txt
```

### Q: 性能问题？
A: 优化建议：
1. 使用 `torch.no_grad()`
2. 避免在循环中创建新张量
3. 使用GPU加速

### Q: 如何更新节点？
A: 
```bash
cd ComfyUI/custom_nodes/comfyui-custom-node-project
git pull
pip install -r requirements.txt --upgrade
```

## 📚 学习资源

### 官方文档
- ComfyUI GitHub: https://github.com/comfyanonymous/ComfyUI
- 节点开发指南: https://github.com/comfyanonymous/ComfyUI/discussions/631

### 社区资源
- ComfyUI Discord: https://discord.gg/comfyui
- 节点开发示例: https://github.com/pythongosssss/ComfyUI-Custom-Scripts

### 进阶学习
- PyTorch官方教程: https://pytorch.org/tutorials/
- 图像处理基础: OpenCV, PIL文档

## 🎉 贡献指南

### 如何贡献
1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/awesome-node`)
3. 提交更改 (`git commit -m 'Add awesome node'`)
4. 推送到分支 (`git push origin feature/awesome-node`)
5. 创建Pull Request

### 代码规范
- 遵循PEP 8代码风格
- 添加类型提示
- 编写文档字符串
- 包含单元测试

### 测试要求
```python
# 添加测试用例
def test_text_concatenate():
    node = TextConcatenate()
    result = node.concatenate("Hello", "World", ", ")
    assert result[0] == "Hello, World"
```

## 📞 支持与反馈

### 问题反馈
1. GitHub Issues: https://github.com/yourusername/comfyui-custom-node-project/issues
2. 邮件: your.email@example.com
3. Discord: YourDiscordUsername

### 功能请求
欢迎提交功能请求，请描述：
1. 你想要什么功能
2. 为什么需要这个功能
3. 预期的使用场景

## 📄 许可证
MIT License - 详见 LICENSE 文件

---
*项目状态: 活跃开发中*
*最后更新: 2026-03-12*
*目标: 提供高质量、实用的ComfyUI自定义节点*