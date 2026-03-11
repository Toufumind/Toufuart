#!/usr/bin/env python3
"""
深度性能分析器 - OpenClaw技能实现
"""

import torch
import torch.cuda as cuda
import time
import json
import numpy as np
from typing import Dict, List, Optional, Any
import subprocess
import sys
import os

class DeepPerformanceAnalyzer:
    """深度性能分析器主类"""
    
    def __init__(self):
        self.results = {}
        
    def analyze_cuda_device(self) -> Dict:
        """分析CUDA设备性能"""
        if not torch.cuda.is_available():
            return {"error": "CUDA不可用"}
        
        device_count = torch.cuda.device_count()
        devices_info = []
        
        for i in range(device_count):
            props = cuda.get_device_properties(i)
            
            device_info = {
                "id": i,
                "name": props.name,
                "compute_capability": f"{props.major}.{props.minor}",
                "total_memory_gb": props.total_memory / (1024**3),
                "multi_processor_count": props.multi_processor_count,
                "max_threads_per_block": props.max_threads_per_block,
                "clock_rate_ghz": props.clock_rate / 1e6,
            }
            
            # 基准测试
            benchmarks = self._benchmark_device(i)
            device_info.update(benchmarks)
            
            devices_info.append(device_info)
        
        return {
            "cuda_available": True,
            "device_count": device_count,
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__,
            "devices": devices_info,
        }
    
    def _benchmark_device(self, device_id: int) -> Dict:
        """对单个设备进行基准测试"""
        device = torch.device(f"cuda:{device_id}")
        torch.cuda.set_device(device)
        
        benchmarks = {}
        
        # 1. 内存带宽测试
        benchmarks["memory_bandwidth"] = self._benchmark_memory_bandwidth(device)
        
        # 2. 计算性能测试
        benchmarks["compute_performance"] = self._benchmark_compute_performance(device)
        
        # 3. 内核启动开销
        benchmarks["kernel_overhead"] = self._benchmark_kernel_overhead(device)
        
        return benchmarks
    
    def _benchmark_memory_bandwidth(self, device: torch.device) -> Dict:
        """测试内存带宽"""
        size_mb = 100
        size = int(size_mb * 1024 * 1024 // 4)  # float32
        
        a = torch.randn(size, device=device, dtype=torch.float32)
        b = torch.randn(size, device=device, dtype=torch.float32)
        
        # 预热
        for _ in range(10):
            _ = a + b
        
        # 正式测试
        cuda.synchronize()
        start = time.perf_counter()
        
        iterations = 100
        for _ in range(iterations):
            c = a + b
        
        cuda.synchronize()
        end = time.perf_counter()
        
        # 计算带宽
        data_transferred = size * 4 * 3 * iterations  # 读取a,b,写入c
        time_seconds = end - start
        bandwidth_gb_s = (data_transferred / time_seconds) / (1024**3)
        
        return {
            "test_size_mb": size_mb,
            "bandwidth_gb_s": bandwidth_gb_s,
            "time_seconds": time_seconds,
        }
    
    def _benchmark_compute_performance(self, device: torch.device) -> Dict:
        """测试计算性能"""
        size = 1024 * 1024
        a = torch.randn(size, device=device)
        b = torch.randn(size, device=device)
        c = torch.randn(size, device=device)
        
        # 预热
        for _ in range(10):
            _ = a * b + c
        
        # FMA测试
        cuda.synchronize()
        start = time.perf_counter()
        
        iterations = 1000
        for _ in range(iterations):
            result = a * b + c
        
        cuda.synchronize()
        end = time.perf_counter()
        
        time_seconds = end - start
        flops = size * 2 * iterations  # FMA = 2浮点操作
        gflops = flops / time_seconds / 1e9
        
        return {
            "gflops": gflops,
            "time_seconds": time_seconds,
            "test_size": size,
        }
    
    def _benchmark_kernel_overhead(self, device: torch.device) -> Dict:
        """测试内核启动开销"""
        size = 1024
        a = torch.randn(size, device=device)
        b = torch.randn(size, device=device)
        
        cuda.synchronize()
        start = time.perf_counter()
        
        iterations = 10000
        for _ in range(iterations):
            _ = a + b
        
        cuda.synchronize()
        end = time.perf_counter()
        
        time_per_iteration_ms = (end - start) * 1000 / iterations
        
        return {
            "time_per_kernel_ms": time_per_iteration_ms,
            "total_iterations": iterations,
        }
    
    def analyze_pytorch_model(self, model: torch.nn.Module, input_shape: tuple) -> Dict:
        """分析PyTorch模型性能"""
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        
        # 准备输入
        input_tensor = torch.randn(*input_shape, device=device)
        
        # 预热
        with torch.no_grad():
            for _ in range(10):
                _ = model(input_tensor)
        
        # 前向传播性能
        cuda.synchronize()
        start = time.perf_counter()
        
        iterations = 100
        with torch.no_grad():
            for _ in range(iterations):
                output = model(input_tensor)
        
        cuda.synchronize()
        end = time.perf_counter()
        
        # 内存分析
        initial_memory = cuda.memory_allocated() if torch.cuda.is_available() else 0
        peak_memory = cuda.max_memory_allocated() if torch.cuda.is_available() else 0
        
        # 计算参数数量
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        return {
            "forward_time_ms": (end - start) * 1000 / iterations,
            "throughput_samples_s": iterations / (end - start),
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "initial_memory_mb": initial_memory / (1024**2),
            "peak_memory_mb": peak_memory / (1024**2),
            "memory_increase_mb": (peak_memory - initial_memory) / (1024**2),
            "device": str(device),
        }
    
    def analyze_comfyui_workflow(self, workflow_file: str) -> Dict:
        """分析ComfyUI工作流性能"""
        # 这里需要实际集成ComfyUI
        # 简化实现：解析工作流文件并估计性能
        
        try:
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
            
            # 分析工作流结构
            node_count = len(workflow)
            
            # 估计计算需求
            estimated_flops = node_count * 1e9  # 简化估计
            
            # 估计内存需求
            estimated_memory_mb = node_count * 100  # 简化估计
            
            return {
                "workflow_file": workflow_file,
                "node_count": node_count,
                "estimated_flops": estimated_flops,
                "estimated_memory_mb": estimated_memory_mb,
                "complexity": "简单" if node_count < 10 else "中等" if node_count < 30 else "复杂",
            }
            
        except Exception as e:
            return {
                "error": f"分析工作流失败: {str(e)}",
                "workflow_file": workflow_file,
            }
    
    def generate_optimization_suggestions(self, analysis_results: Dict) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # CUDA设备优化建议
        if "cuda_device" in analysis_results:
            device_info = analysis_results["cuda_device"]
            
            # 内存带宽优化
            if "memory_bandwidth" in device_info:
                bw = device_info["memory_bandwidth"].get("bandwidth_gb_s", 0)
                if bw < 100:  # 低于100 GB/s
                    suggestions.append("内存带宽较低，考虑优化内存访问模式")
            
            # 计算性能优化
            if "compute_performance" in device_info:
                gflops = device_info["compute_performance"].get("gflops", 0)
                if gflops < 1000:  # 低于1 TFLOPS
                    suggestions.append("计算性能较低，考虑使用Tensor Core或优化算法")
        
        # PyTorch模型优化建议
        if "pytorch_model" in analysis_results:
            model_info = analysis_results["pytorch_model"]
            
            # 内存优化
            memory_increase = model_info.get("memory_increase_mb", 0)
            if memory_increase > 1000:  # 超过1GB
                suggestions.append("模型内存使用较高，考虑使用梯度检查点或模型分片")
            
            # 性能优化
            forward_time = model_info.get("forward_time_ms", 0)
            if forward_time > 100:  # 超过100ms
                suggestions.append("前向传播时间较长，考虑使用混合精度或内核融合")
        
        # ComfyUI工作流优化建议
        if "comfyui_workflow" in analysis_results:
            workflow_info = analysis_results["comfyui_workflow"]
            
            node_count = workflow_info.get("node_count", 0)
            if node_count > 50:
                suggestions.append("工作流节点过多，考虑拆分为多个子工作流")
            
            estimated_memory = workflow_info.get("estimated_memory_mb", 0)
            if estimated_memory > 8000:  # 超过8GB
                suggestions.append("工作流内存需求较高，考虑优化节点顺序或使用内存优化节点")
        
        # 通用优化建议
        suggestions.extend([
            "使用混合精度训练（FP16）减少内存使用和提高速度",
            "增加批处理大小以提高GPU利用率",
            "使用梯度累积模拟大批次训练",
            "定期清理CUDA缓存：torch.cuda.empty_cache()",
            "使用torch.compile()优化模型（PyTorch 2.0+）",
            "考虑使用量化（INT8/FP8）减少模型大小",
        ])
        
        return suggestions
    
    def run_full_analysis(self) -> Dict:
        """运行完整分析"""
        print("开始深度性能分析...")
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": self._get_system_info(),
        }
        
        # 1. CUDA设备分析
        print("1. 分析CUDA设备...")
        results["cuda_device"] = self.analyze_cuda_device()
        
        # 2. 示例PyTorch模型分析
        print("2. 分析示例PyTorch模型...")
        example_model = self._create_example_model()
        results["pytorch_model"] = self.analyze_pytorch_model(
            example_model, 
            input_shape=(4, 3, 224, 224)  # batch=4, 3通道, 224x224
        )
        
        # 3. 优化建议
        print("3. 生成优化建议...")
        results["optimization_suggestions"] = self.generate_optimization_suggestions(results)
        
        # 4. 性能评分
        print("4. 计算性能评分...")
        results["performance_score"] = self._calculate_performance_score(results)
        
        print("分析完成!")
        return results
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        import platform
        
        return {
            "python_version": platform.python_version(),
            "system": platform.system(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
        }
    
    def _create_example_model(self) -> torch.nn.Module:
        """创建示例模型"""
        class ExampleModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = torch.nn.Conv2d(3, 64, kernel_size=3, padding=1)
                self.conv2 = torch.nn.Conv2d(64, 128, kernel_size=3, padding=1)
                self.conv3 = torch.nn.Conv2d(128, 256, kernel_size=3, padding=1)
                self.pool = torch.nn.MaxPool2d(2)
                self.fc1 = torch.nn.Linear(256 * 28 * 28, 512)
                self.fc2 = torch.nn.Linear(512, 10)
                
            def forward(self, x):
                x = torch.relu(self.conv1(x))
                x = self.pool(x)
                x = torch.relu(self.conv2(x))
                x = self.pool(x)
                x = torch.relu(self.conv3(x))
                x = self.pool(x)
                x = x.view(x.size(0), -1)
                x = torch.relu(self.fc1(x))
                x = self.fc2(x)
                return x
        
        return ExampleModel()
    
    def _calculate_performance_score(self, results: Dict) -> Dict:
        """计算性能评分（0-100）"""
        score = 50  # 基础分
        
        # CUDA设备评分
        if "cuda_device" in results:
            device_info = results["cuda_device"]
            if device_info.get("cuda_available", False):
                score += 20
                
                # 内存带宽评分
                if "devices" in device_info and device_info["devices"]:
                    device = device_info["devices"][0]
                    if "memory_bandwidth" in device:
                        bw = device["memory_bandwidth"].get("bandwidth_gb_s", 0)
                        if bw > 200:
                            score += 10
                        elif bw > 100:
                            score += 5
                
                # 计算性能评分
                if "compute_performance" in device:
                    gflops = device["compute_performance"].get("gflops", 0)
                    if gflops > 5000:
                        score += 10
                    elif gflops > 1000:
                        score += 5
        
        # 模型性能评分
        if "pytorch_model" in results:
            model_info = results["pytorch_model"]
            forward_time = model_info.get("forward_time_ms", 0)
            if forward_time < 10:
                score += 10
            elif forward_time < 50:
                score += 5
            
            memory_increase = model_info.get("memory_increase_mb", 0)
            if memory_increase < 500:
                score += 5
        
        # 确保分数在0-100之间
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "rating": self._score_to_rating(score),
            "interpretation": self._interpret_score(score),
        }
    
    def _score_to_rating(self, score: int) -> str:
        """分数转换为评级"""
        if score >= 90:
            return "优秀"
        elif score >= 75:
            return "良好"
        elif score >= 60:
            return "中等"
        elif score >= 40:
            return "需要改进"
        else:
            return "较差"
    
    def _interpret_score(self, score: int) -> str:
        """解释分数含义"""
        if score >= 80:
            return "系统性能优秀，适合运行复杂的AI工作流"
        elif score >= 60:
            return "系统性能良好，可以运行大多数AI任务"
        elif score >= 40:
            return "系统性能中等，可能需要优化才能运行复杂任务"
        else:
            return "系统性能较差，建议进行硬件升级或深度优化"
    
    def save_report(self, results: Dict, filename: str = "deep_performance_report.json"):
        """保存分析报告"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"分析报告已保存到: {filename}")
    
    def print_report_summary(self, results: Dict):
        """打印报告摘要"""
        print("\n" + "="*60)
        print("深度性能分析报告摘要")
        print("="*60)
        
        # 系统信息
        print(f"\n分析时间: {results.get('timestamp', 'N/A')}")
        
        # CUDA设备信息
        if "cuda_device" in results:
            device_info = results["cuda_device"]
            if device_info.get("cuda_available", False):
                print(f"\nCUDA设备: {device_info['device_count']}个可用")
                for i, device in enumerate(device_info.get("devices", [])):
                    print(f"  设备{i}: {device.get('name', 'N/A')}")
                    print(f"    内存: {device.get('total_memory_gb', 0):.1f} GB")
                    if "memory_bandwidth" in device:
                        bw = device["memory_bandwidth"].get("bandwidth_gb_s", 0)
                        print(f"    内存带宽: {bw:.1f} GB/s")
                    if "compute_performance" in device:
                        g