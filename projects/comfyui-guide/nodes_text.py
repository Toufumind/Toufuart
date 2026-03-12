"""
ComfyUI 文本处理自定义节点
提供实用的文本处理功能，增强提示词工作流
"""

import re
import random
from typing import Dict, Tuple, List, Any

class TextConcatenate:
    """
    文本拼接节点
    将多个文本按照指定的分隔符拼接在一起
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "text1": ("STRING", {
                    "default": "", 
                    "multiline": True,
                    "placeholder": "输入第一段文本"
                }),
                "text2": ("STRING", {
                    "default": "", 
                    "multiline": True,
                    "placeholder": "输入第二段文本"
                }),
                "separator": ("STRING", {
                    "default": ", ",
                    "tooltip": "用于分隔文本的字符串"
                }),
            },
            "optional": {
                "text3": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入第三段文本（可选）"
                }),
                "text4": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入第四段文本（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("concatenated_text",)
    FUNCTION = "concatenate"
    CATEGORY = "Text Tools"
    DESCRIPTION = "将多个文本拼接成一个文本"
    
    def concatenate(self, text1: str, text2: str, separator: str, 
                   text3: str = "", text4: str = "") -> Tuple[str]:
        """
        拼接文本
        
        Args:
            text1: 第一段文本
            text2: 第二段文本
            separator: 分隔符
            text3: 第三段文本（可选）
            text4: 第四段文本（可选）
            
        Returns:
            拼接后的文本
        """
        # 收集所有非空文本
        texts = [text1, text2]
        if text3:
            texts.append(text3)
        if text4:
            texts.append(text4)
        
        # 过滤空文本
        non_empty_texts = [t.strip() for t in texts if t.strip()]
        
        # 使用分隔符拼接
        result = separator.join(non_empty_texts)
        
        return (result,)


class TextWeightAdjust:
    """
    文本权重调整节点
    调整提示词中特定关键词的权重
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入原始文本"
                }),
                "keyword": ("STRING", {
                    "default": "",
                    "placeholder": "要调整权重的关键词"
                }),
                "weight": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.1,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "mode": (["add", "replace", "remove"], {
                    "default": "add"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("adjusted_text",)
    FUNCTION = "adjust_weight"
    CATEGORY = "Text Tools"
    DESCRIPTION = "调整文本中关键词的权重"
    
    def adjust_weight(self, text: str, keyword: str, weight: float, 
                     mode: str = "add") -> Tuple[str]:
        """
        调整关键词权重
        
        Args:
            text: 原始文本
            keyword: 要调整的关键词
            weight: 权重值（0.1-2.0）
            mode: 调整模式（add/replace/remove）
            
        Returns:
            调整后的文本
        """
        if not keyword or weight == 1.0:
            return (text,)
        
        # 清理关键词
        keyword = keyword.strip()
        if not keyword:
            return (text,)
        
        # 根据模式处理
        if mode == "remove":
            # 移除权重标记
            pattern = rf'\({re.escape(keyword)}:[0-9.]+\)'
            result = re.sub(pattern, keyword, text)
        elif mode == "replace":
            # 替换现有权重或添加新权重
            pattern = rf'\b{re.escape(keyword)}\b'
            replacement = f'({keyword}:{weight:.1f})'
            result = re.sub(pattern, replacement, text)
        else:  # add
            # 检查是否已有权重
            weight_pattern = rf'\({re.escape(keyword)}:[0-9.]+\)'
            if re.search(weight_pattern, text):
                # 已有权重，替换权重值
                result = re.sub(
                    rf'\({re.escape(keyword)}:([0-9.]+)\)',
                    f'({keyword}:{weight:.1f})',
                    text
                )
            else:
                # 没有权重，添加权重
                pattern = rf'\b{re.escape(keyword)}\b'
                replacement = f'({keyword}:{weight:.1f})'
                result = re.sub(pattern, replacement, text)
        
        return (result,)


class TextRandomizer:
    """
    文本随机化节点
    从多个选项中选择一个随机文本
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "option1": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "选项1"
                }),
                "option2": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "选项2"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2**32-1
                }),
            },
            "optional": {
                "option3": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "选项3（可选）"
                }),
                "option4": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "选项4（可选）"
                }),
                "option5": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "选项5（可选）"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("selected_text", "used_seed")
    FUNCTION = "random_select"
    CATEGORY = "Text Tools"
    DESCRIPTION = "从多个文本选项中随机选择一个"
    
    def random_select(self, option1: str, option2: str, seed: int,
                     option3: str = "", option4: str = "", 
                     option5: str = "") -> Tuple[str, int]:
        """
        随机选择一个文本选项
        
        Args:
            option1-option5: 文本选项
            seed: 随机种子
            
        Returns:
            选中的文本和使用的种子
        """
        # 收集所有非空选项
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        if option5:
            options.append(option5)
        
        # 过滤空选项
        valid_options = [opt.strip() for opt in options if opt.strip()]
        
        if not valid_options:
            return ("", seed)
        
        # 使用种子进行随机选择
        if seed:
            random.seed(seed)
        
        selected = random.choice(valid_options)
        used_seed = seed if seed else random.randint(0, 2**32-1)
        
        return (selected, used_seed)


class TextTemplate:
    """
    文本模板节点
    使用模板和变量生成文本
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "template": ("STRING", {
                    "default": "A {style} {subject} in {setting}",
                    "multiline": True,
                    "placeholder": "使用 {变量名} 作为占位符"
                }),
                "style": ("STRING", {
                    "default": "realistic",
                    "placeholder": "风格变量"
                }),
                "subject": ("STRING", {
                    "default": "cat",
                    "placeholder": "主体变量"
                }),
                "setting": ("STRING", {
                    "default": "garden",
                    "placeholder": "场景变量"
                }),
            },
            "optional": {
                "var1_name": ("STRING", {
                    "default": "",
                    "placeholder": "额外变量1名称"
                }),
                "var1_value": ("STRING", {
                    "default": "",
                    "placeholder": "额外变量1值"
                }),
                "var2_name": ("STRING", {
                    "default": "",
                    "placeholder": "额外变量2名称"
                }),
                "var2_value": ("STRING", {
                    "default": "",
                    "placeholder": "额外变量2值"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("generated_text",)
    FUNCTION = "generate_from_template"
    CATEGORY = "Text Tools"
    DESCRIPTION = "使用模板和变量生成文本"
    
    def generate_from_template(self, template: str, style: str, subject: str, 
                              setting: str, var1_name: str = "", var1_value: str = "",
                              var2_name: str = "", var2_value: str = "") -> Tuple[str]:
        """
        从模板生成文本
        
        Args:
            template: 模板字符串，使用 {变量名} 作为占位符
            style, subject, setting: 基本变量
            var1_name, var1_value: 额外变量1
            var2_name, var2_value: 额外变量2
            
        Returns:
            生成的文本
        """
        # 准备变量字典
        variables = {
            "style": style,
            "subject": subject,
            "setting": setting,
        }
        
        # 添加额外变量
        if var1_name and var1_value:
            variables[var1_name] = var1_value
        if var2_name and var2_value:
            variables[var2_name] = var2_value
        
        # 替换模板中的变量
        result = template
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            result = result.replace(placeholder, var_value)
        
        return (result,)


class TextStatistics:
    """
    文本统计节点
    分析文本的统计信息
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入要分析的文本"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "INT", "INT")
    RETURN_NAMES = ("statistics", "char_count", "word_count", "line_count")
    FUNCTION = "analyze"
    CATEGORY = "Text Tools"
    DESCRIPTION = "分析文本的统计信息"
    
    def analyze(self, text: str) -> Tuple[str, int, int, int]:
        """
        分析文本统计信息
        
        Args:
            text: 要分析的文本
            
        Returns:
            统计信息字符串、字符数、单词数、行数
        """
        # 计算统计信息
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.splitlines())
        
        # 计算平均单词长度
        words = text.split()
        avg_word_len = sum(len(word) for word in words) / max(len(words), 1)
        
        # 生成统计信息字符串
        stats = (
            f"字符数: {char_count}\n"
            f"单词数: {word_count}\n"
            f"行数: {line_count}\n"
            f"平均单词长度: {avg_word_len:.1f}"
        )
        
        return (stats, char_count, word_count, line_count)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "Text Concatenate": TextConcatenate,
    "Text Weight Adjust": TextWeightAdjust,
    "Text Randomizer": TextRandomizer,
    "Text Template": TextTemplate,
    "Text Statistics": TextStatistics,
}

# 节点显示名称（可选）
NODE_DISPLAY_NAME_MAPPINGS = {
    "Text Concatenate": "文本拼接",
    "Text Weight Adjust": "权重调整",
    "Text Randomizer": "文本随机化",
    "Text Template": "文本模板",
    "Text Statistics": "文本统计",
}