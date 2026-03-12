#!/usr/bin/env python3
"""
ComfyUI自定义节点示例 - TechArt图像处理节点
演示如何创建自定义ComfyUI节点
"""

import torch
import numpy as np
from PIL import Image
import io
import base64

# 模拟ComfyUI节点基类
class ComfyNodeABC:
    """ComfyUI节点抽象基类"""
    CATEGORY = "custom"
    
    @classmethod
    def INPUT_TYPES(cls):
        raise NotImplementedError
    
    @classmethod 
    def RETURN_TYPES(cls):
        raise NotImplementedError
    
    @classmethod
    def FUNCTION(cls):
        raise NotImplementedError

# 示例1: 简单文本处理节点
class TextRepeaterNode(ComfyNodeABC):
    """文本重复节点 - 演示基础节点结构"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "repeat_times": ("INT", {"default": 3, "min": 1, "max": 100}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("repeated_text",)
    FUNCTION = "repeat_text"
    CATEGORY = "text"
    DESCRIPTION = "重复文本指定次数"
    
    def repeat_text(self, text, repeat_times):
        """重复文本"""
        result = text * repeat_times
        return (result,)

# 示例2: 图像颜色调整节点
class ColorAdjustNode(ComfyNodeABC):
    """图像颜色调整节点 - 演示图像处理"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "brightness": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1}),
                "contrast": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1}),
                "saturation": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("adjusted_image",)
    FUNCTION = "adjust_colors"
    CATEGORY = "image"
    DESCRIPTION = "调整图像亮度、对比度和饱和度"
    
    def adjust_colors(self, image, brightness, contrast, saturation):
        """调整图像颜色"""
        # 简化实现 - 实际需要处理tensor格式
        print(f"调整图像: brightness={brightness}, contrast={contrast}, saturation={saturation}")
        # 返回原始图像（实际应处理）
        return (image,)

# 示例3: TechArt专用节点 - 材质生成器
class MaterialGeneratorNode(ComfyNodeABC):
    """材质生成器节点 - TechArt专用"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "material_type": (["metal", "plastic", "wood", "fabric", "glass"],),
                "roughness": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "metallic": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "base_color": ("STRING", {"default": "#808080"}),
            },
            "optional": {
                "normal_map": ("IMAGE",),
                "height_map": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("STRING", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("material_config", "albedo_map", "roughness_map", "normal_map")
    FUNCTION = "generate_material"
    CATEGORY = "techart"
    DESCRIPTION = "生成PBR材质贴图"
    
    def generate_material(self, material_type, roughness, metallic, base_color, normal_map=None, height_map=None):
        """生成材质配置和贴图"""
        # 生成材质配置JSON
        config = {
            "type": material_type,
            "roughness": roughness,
            "metallic": metallic,
            "base_color": base_color,
            "has_normal": normal_map is not None,
            "has_height": height_map is not None,
        }
        
        config_json = str(config)
        
        # 简化实现 - 实际应生成贴图
        print(f"生成{material_type}材质: roughness={roughness}, metallic={metallic}")
        
        # 返回占位值
        return (config_json, None, None, normal_map)

# 示例4: 工作流分析节点
class WorkflowAnalyzerNode(ComfyNodeABC):
    """工作流分析节点 - 分析ComfyUI工作流"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "workflow_json": ("STRING", {"multiline": True, "default": "{}"}),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "INT", "STRING")
    RETURN_NAMES = ("analysis_report", "node_count", "connection_count", "suggestions")
    FUNCTION = "analyze_workflow"
    CATEGORY = "utility"
    DESCRIPTION = "分析ComfyUI工作流结构"
    
    def analyze_workflow(self, workflow_json):
        """分析工作流"""
        try:
            import json
            workflow = json.loads(workflow_json)
            
            # 统计信息
            node_count = len(workflow) if isinstance(workflow, dict) else 0
            
            # 计算连接数（简化）
            connection_count = 0
            for node_id, node_data in workflow.items():
                if isinstance(node_data, dict) and "inputs" in node_data:
                    connection_count += len(node_data["inputs"])
            
            # 生成报告
            report = f"""工作流分析报告:
- 节点数量: {node_count}
- 连接数量: {connection_count}
- 工作流复杂度: {'简单' if node_count < 10 else '中等' if node_count < 30 else '复杂'}
"""
            
            # 优化建议
            suggestions = ""
            if node_count > 50:
                suggestions = "建议: 工作流过于复杂，考虑拆分为多个子工作流"
            elif connection_count / max(node_count, 1) > 3:
                suggestions = "建议: 连接密度较高，检查是否有循环依赖"
            else:
                suggestions = "工作流结构良好"
            
            return (report, node_count, connection_count, suggestions)
            
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            return (error_msg, 0, 0, "请检查JSON格式")

# 节点注册函数（模拟ComfyUI注册机制）
def register_custom_nodes():
    """注册自定义节点到ComfyUI"""
    node_mappings = {
        "TextRepeater": TextRepeaterNode,
        "ColorAdjust": ColorAdjustNode,
        "MaterialGenerator": MaterialGeneratorNode,
        "WorkflowAnalyzer": WorkflowAnalyzerNode,
    }
    
    print("注册自定义节点:")
    for name, node_class in node_mappings.items():
        print(f"  - {name}: {node_class.CATEGORY}类别")
    
    return node_mappings

# 测试函数
def test_custom_nodes():
    """测试自定义节点"""
    print("=== 测试自定义ComfyUI节点 ===")
    
    # 注册节点
    nodes = register_custom_nodes()
    
    # 测试文本重复节点
    print("\n1. 测试TextRepeater节点:")
    text_node = nodes["TextRepeater"]
    result = text_node().repeat_text("Hello ", 3)
    print(f"   输入: 'Hello ', 重复3次")
    print(f"   输出: {result[0]}")
    
    # 测试工作流分析节点
    print("\n2. 测试WorkflowAnalyzer节点:")
    analyzer = nodes["WorkflowAnalyzer"]
    test_workflow = '{"node1": {"class_type": "KSampler", "inputs": {"model": "model1"}}}'
    report, count, connections, suggestions = analyzer().analyze_workflow(test_workflow)
    print(f"   节点数: {count}")
    print(f"   连接数: {connections}")
    print(f"   建议: {suggestions}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 运行测试
    test_custom_nodes()
    
    print("\n=== 节点开发指南 ===")
    print("1. 继承ComfyNodeABC或io.ComfyNode")
    print("2. 定义INPUT_TYPES()指定输入类型")
    print("3. 定义RETURN_TYPES()指定输出类型")  
    print("4. 实现FUNCTION指定的方法")
    print("5. 设置CATEGORY和DESCRIPTION")
    print("6. 将节点文件放入custom_nodes/目录")
    print("7. ComfyUI会自动加载节点")