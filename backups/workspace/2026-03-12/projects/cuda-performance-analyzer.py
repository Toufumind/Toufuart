#!/usr/bin/env python3
"""
CUDA性能分析工具 - 深度分析PyTorch到CUDA性能
"""

import torch
import torch.cuda as cuda
import time
import numpy as np
from typing import Dict, List, Tuple
import json
import sys

class CUDAPerformanceAnalyzer:
    """CUDA性能分析器"""
    
    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.device = torch.device(f"cuda:{device_id}")
        torch.cuda.set_device(self.device)
        
        # 获取设备信息
        self.device_props = cuda.get_device_properties(self.device_id)
        
    def get_device_info(self) -> Dict:
        """获取CUDA设备信息"""
        return {
            "name": self.device_props.name,
            "compute_capability": f"{self.device_props.major}.{self.device_props.minor}",
            "total_memory_gb": self.device_props.total_memory / (1024**3),
            "multi_processor_count": self.device_props.multi_processor_count,
            "max_threads_per_block": self.device_props.max_threads_per_block,
            "max_threads_per_multiprocessor": self.device_props.max_threads_per_multiprocessor,
            "warp_size": self.device_props.warp_size,
            "cuda_version": torch.version.cuda,
        }
    
    def benchmark_memory_bandwidth(self, size_mb: int = 100) -> Dict:
        """测试内存带宽"""
        size = int(size_mb * 1024 * 1024 // 4)  # float32 = 4字节
        a = torch.randn(size, device=self.device, dtype=torch.float32)
        b = torch.randn(size, device=self.device, dtype=torch.float32)
        
        # 预热
        for _ in range(10):
            c = a + b
        
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
            "iterations": iterations,
            "time_seconds": time_seconds,
            "bandwidth_gb_s": bandwidth_gb_s,
            "theoretical_max_gb_s": self.device_props.memory_clock_rate * 2 * self.device_props.memory_bus_width / 8 / 1e9,
        }
    
    def benchmark_compute_performance(self, ops: str = "fma") -> Dict:
        """测试计算性能（FMA = Fused Multiply-Add）"""
        size = 1024 * 1024  # 1M元素
        a = torch.randn(size, device=self.device, dtype=torch.float32)
        b = torch.randn(size, device=self.device, dtype=torch.float32)
        c = torch.randn(size, device=self.device, dtype=torch.float32)
        
        # 预热
        for _ in range(10):
            if ops == "fma":
                result = a * b + c
            elif ops == "add":
                result = a + b
            elif ops == "mul":
                result = a * b
        
        # 正式测试
        cuda.synchronize()
        start = time.perf_counter()
        
        iterations = 1000
        for _ in range(iterations):
            if ops == "fma":
                result = a * b + c
            elif ops == "add":
                result = a + b
            elif ops == "mul":
                result = a * b
        
        cuda.synchronize()
        end = time.perf_counter()
        
        # 计算性能
        time_seconds = end - start
        if ops == "fma":
            flops = size * 2 * iterations  # FMA = 2浮点操作
        else:
            flops = size * 1 * iterations
        
        flops_g = flops / time_seconds / 1e9
        
        return {
            "operation": ops,
            "size_elements": size,
            "iterations": iterations,
            "time_seconds": time_seconds,
            "gflops": flops_g,
            "theoretical_max_tflops": self._calculate_theoretical_tflops(),
        }
    
    def _calculate_theoretical_tflops(self) -> float:
        """计算理论TFLOPS"""
        # 简化计算：SM数量 × 每时钟周期操作数 × 频率
        sm_count = self.device_props.multi_processor_count
        clock_rate_ghz = self.device_props.clock_rate / 1e6 / 1000
        
        # FP32每SM每时钟周期操作数
        if self.device_props.major >= 8:  # Ampere+
            ops_per_sm_per_cycle = 128  # 简化估计
        elif self.device_props.major >= 7:  # Turing/Volta
            ops_per_sm_per_cycle = 64
        else:
            ops_per_sm_per_cycle = 32
        
        theoretical_tflops = sm_count * ops_per_sm_per_cycle * clock_rate_ghz / 1000
        return theoretical_tflops
    
    def benchmark_kernel_launch_overhead(self) -> Dict:
        """测试内核启动开销"""
        size = 1024
        a = torch.randn(size, device=self.device)
        b = torch.randn(size, device=self.device)
        
        # 小操作测试内核启动开销
        cuda.synchronize()
        start = time.perf_counter()
        
        iterations = 10000
        for _ in range(iterations):
            c = a + b  # 小操作，主要开销是内核启动
        
        cuda.synchronize()
        end = time.perf_counter()
        
        time_per_iteration_ms = (end - start) * 1000 / iterations
        
        return {
            "iterations": iterations,
            "total_time_ms": (end - start) * 1000,
            "time_per_kernel_ms": time_per_iteration_ms,
            "kernel_launch_overhead_estimate_ms": time_per_iteration_ms * 0.8,  # 估计80%是启动开销
        }
    
    def benchmark_pytorch_operations(self) -> Dict:
        """测试常见PyTorch操作性能"""
        results = {}
        
        # 测试1: 矩阵乘法
        size = 1024
        a = torch.randn(size, size, device=self.device)
        b = torch.randn(size, size, device=self.device)
        
        cuda.synchronize()
        start = time.perf_counter()
        
        iterations = 100
        for _ in range(iterations):
            c = torch.matmul(a, b)
        
        cuda.synchronize()
        end = time.perf_counter()
        
        results["matmul"] = {
            "size": f"{size}x{size}",
            "iterations": iterations,
            "time_ms": (end - start) * 1000,
            "time_per_matmul_ms": (end - start) * 1000 / iterations,
        }
        
        # 测试2: 卷积操作
        batch = 4
        channels = 64
        height = 128
        width = 128
        
        input_tensor = torch.randn(batch, channels, height, width, device=self.device)
        conv = torch.nn.Conv2d(channels, channels, kernel_size=3, padding=1).cuda()
        
        cuda.synchronize()
        start = time.perf_counter()
        
        iterations = 50
        for _ in range(iterations):
            output = conv(input_tensor)
        
        cuda.synchronize()
        end = time.perf_counter()
        
        results["conv2d"] = {
            "shape": f"{batch}x{channels}x{height}x{width}",
            "kernel": "3x3",
            "iterations": iterations,
            "time_ms": (end - start) * 1000,
            "time_per_conv_ms": (end - start) * 1000 / iterations,
        }
        
        return results
    
    def analyze_memory_patterns(self, model: torch.nn.Module, input_shape: Tuple) -> Dict:
        """分析模型内存使用模式"""
        # 记录初始内存
        initial_memory = cuda.memory_allocated()
        
        # 创建输入
        input_tensor = torch.randn(*input_shape, device=self.device)
        
        # 前向传播
        with torch.no_grad():
            output = model(input_tensor)
        
        # 记录峰值内存
        peak_memory = cuda.max_memory_allocated()
        
        # 清理
        del input_tensor, output
        cuda.empty_cache()
        
        return {
            "initial_memory_mb": initial_memory / (1024**2),
            "peak_memory_mb": peak_memory / (1024**2),
            "memory_increase_mb": (peak_memory - initial_memory) / (1024**2),
            "memory_efficiency": initial_memory / peak_memory if peak_memory > 0 else 0,
        }
    
    def generate_performance_report(self) -> Dict:
        """生成完整性能报告"""
        print("开始CUDA性能分析...")
        
        report = {
            "device_info": self.get_device_info(),
            "memory_bandwidth": self.benchmark_memory_bandwidth(),
            "compute_performance": {
                "fma": self.benchmark_compute_performance("fma"),
                "add": self.benchmark_compute_performance("add"),
                "mul": self.benchmark_compute_performance("mul"),
            },
            "kernel_launch_overhead": self.benchmark_kernel_launch_overhead(),
            "pytorch_operations": self.benchmark_pytorch_operations(),
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = "cuda_performance_report.json"):
        """保存性能报告"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"性能报告已保存到: {filename}")
    
    def print_summary(self, report: Dict):
        """打印性能摘要"""
        print("\n" + "="*60)
        print("CUDA性能分析摘要")
        print("="*60)
        
        # 设备信息
        info = report["device_info"]
        print(f"\n设备: {info['name']}")
        print(f"计算能力: {info['compute_capability']}")
        print(f"总内存: {info['total_memory_gb']:.1f} GB")
        print(f"SM数量: {info['multi_processor_count']}")
        
        # 内存带宽
        bw = report["memory_bandwidth"]
        print(f"\n内存带宽: {bw['bandwidth_gb_s']:.1f} GB/s")
        print(f"理论最大带宽: {bw['theoretical_max_gb_s']:.1f} GB/s")
        print(f"带宽利用率: {bw['bandwidth_gb_s']/bw['theoretical_max_gb_s']*100:.1f}%")
        
        # 计算性能
        compute = report["compute_performance"]["fma"]
        print(f"\n计算性能: {compute['gflops']:.1f} GFLOPS")
        print(f"理论最大性能: {compute['theoretical_max_tflops']:.1f} TFLOPS")
        
        # 内核启动开销
        kernel = report["kernel_launch_overhead"]
        print(f"\n内核启动开销: {kernel['time_per_kernel_ms']:.3f} ms/内核")
        print(f"估计启动开销: {kernel['kernel_launch_overhead_estimate_ms']:.3f} ms")
        
        print("\n" + "="*60)

# 示例：测试简单模型
class SimpleModel(torch.nn.Module):
    """简单测试模型"""
    def __init__(self):
        super().__init__()
        self.conv1 = torch.nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = torch.nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.fc = torch.nn.Linear(128 * 32 * 32, 10)
        
    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

def main():
    """主函数"""
    print("CUDA性能分析工具 v1.0")
    print("="*60)
    
    # 检查CUDA可用性
    if not torch.cuda.is_available():
        print("错误: CUDA不可用")
        return
    
    # 创建分析器
    analyzer = CUDAPerformanceAnalyzer(device_id=0)
    
    try:
        # 生成性能报告
        report = analyzer.generate_performance_report()
        
        # 打印摘要
        analyzer.print_summary(report)
        
        # 保存详细报告
        analyzer.save_report(report)
        
        # 测试模型内存分析
        print("\n测试模型内存分析...")
        model = SimpleModel().cuda()
        memory_analysis = analyzer.analyze_memory_patterns(
            model, 
            input_shape=(4, 3, 64, 64)  # batch=4, channels=3, 64x64
        )
        
        print(f"模型内存使用:")
        print(f"  初始内存: {memory_analysis['initial_memory_mb']:.1f} MB")
        print(f"  峰值内存: {memory_analysis['peak_memory_mb']:.1f} MB")
        print(f"  内存增加: {memory_analysis['memory_increase_mb']:.1f} MB")
        print(f"  内存效率: {memory_analysis['memory_efficiency']*100:.1f}%")
        
        # 性能优化建议
        print("\n" + "="*60)
        print("性能优化建议:")
        print("="*60)
        
        bw_utilization = report["memory_bandwidth"]["bandwidth_gb_s"] / report["memory_bandwidth"]["theoretical_max_gb_s"]
        if bw_utilization < 0.5:
            print("1. 内存带宽利用率低，考虑:")
            print("   - 增加批处理大小")
            print("   - 使用内存访问更友好的算法")
            print("   - 减少小内存操作")
        
        kernel_overhead = report["kernel_launch_overhead"]["time_per_kernel_ms"]
        if kernel_overhead > 0.01:  # 10微秒
            print("2. 内核启动开销较高，考虑:")
            print("   - 合并小操作")
            print("   - 使用内核融合技术")
            print("   - 增加每次内核的计算量")
        
        compute_utilization = report["compute_performance"]["fma"]["gflops"] / (report["compute_performance"]["fma"]["theoretical_max_tflops"] * 1000)
        if compute_utilization < 0.3:
            print("3. 计算单元利用率低，考虑:")
            print("   - 使用Tensor Core（FP16）")
            print("   - 优化线程块大小")
            print("   - 减少分支和内存等待")
        
        print("\n" + "="*60)
        print("分析完成!")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()