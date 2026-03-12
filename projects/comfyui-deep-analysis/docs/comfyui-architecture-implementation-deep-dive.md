# ComfyUI架构与实现深度解析 - 从节点系统到GPU计算的全链路分析

## 前言

### 文章目标
本文旨在深入分析ComfyUI的内部架构和实现细节，为开发者、工程师和研究人员提供：
1. **源码级理解**：深入ComfyUI核心模块的实现原理
2. **性能优化指南**：掌握ComfyUI的性能瓶颈和优化策略
3. **扩展开发指导**：基于ComfyUI架构进行高级功能扩展
4. **问题排查手册**：提供常见问题的深度分析和解决方案

### 目标读者
- **ComfyUI开发者**：希望深入理解内部机制，开发高性能自定义节点
- **AI应用工程师**：需要优化Stable Diffusion工作流性能
- **系统架构师**：学习复杂系统的设计模式和架构决策
- **技术研究者**：分析开源AI工具的实现细节

### 前置知识
- Python中级水平，熟悉面向对象编程
- 了解PyTorch和深度学习基础概念
- 熟悉Git和基本的命令行操作
- 对Stable Diffusion有基本了解

### 文章结构
本文将按照以下逻辑顺序展开：
1. **架构分析**：从宏观到微观理解系统设计
2. **源码解析**：深入关键模块的实现细节
3. **性能优化**：分析瓶颈并提供优化方案
4. **实际应用**：将理论知识应用于实际问题

---

## 第一部分：核心架构深度解析

### 1.1 节点系统设计模式分析

ComfyUI的核心是节点系统，这是一个基于数据流的可视化编程框架。让我们深入分析其设计模式。

#### 1.1.1 工厂模式：节点动态注册和创建

**设计意图**：支持运行时动态添加新节点类型，实现插件化架构。

**源码分析** (`comfy/nodes.py`)：
```python
# 全局节点映射表 - 工厂模式的核心
NODE_CLASS_MAPPINGS = {}

def register_node(node_class):
    """节点注册装饰器 - 工厂模式的实现"""
    class_name = node_class.__name__
    NODE_CLASS_MAPPINGS[class_name] = node_class
    
    # 同时注册到显示名称映射
    if hasattr(node_class, 'DISPLAY_NAME'):
        NODE_DISPLAY_NAME_MAPPINGS[class_name] = node_class.DISPLAY_NAME
    
    return node_class

# 使用示例：装饰器语法注册节点
@register_node
class KSampler(ComfyNodeABC):
    DISPLAY_NAME = "KSampler"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0}),
                "sampler_name": (["euler", "euler_ancestral", "dpm_2", "dpm_2_ancestral", "lms", "ddim"],),
                "scheduler": (["normal", "karras", "exponential", "sgm_uniform"],),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "latent_image": ("LATENT",),
            }
        }
    
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "sample"
    
    def sample(self, model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent_image):
        # 实际的采样逻辑
        pass
```

**工厂模式的优势**：
1. **扩展性**：新节点只需用`@register_node`装饰即可加入系统
2. **解耦**：节点创建逻辑与使用逻辑分离
3. **统一管理**：所有节点类型在`NODE_CLASS_MAPPINGS`中集中管理

**节点创建流程**：
```python
def create_node_instance(node_type: str, **kwargs) -> ComfyNodeABC:
    """工厂方法：根据节点类型创建实例"""
    if node_type not in NODE_CLASS_MAPPINGS:
        raise ValueError(f"未知节点类型: {node_type}")
    
    node_class = NODE_CLASS_MAPPINGS[node_type]
    
    # 验证输入
    if not node_class.VALIDATE_INPUTS(**kwargs):
        raise ValueError(f"节点 {node_type} 输入验证失败")
    
    # 创建实例
    instance = node_class()
    
    # 设置实例属性
    for key, value in kwargs.items():
        setattr(instance, key, value)
    
    return instance
```

#### 1.1.2 策略模式：节点执行策略实现

**设计意图**：每个节点类型实现自己的执行逻辑，支持多样化的处理策略。

**源码分析**：
```python
class ComfyNodeABC(ABC):
    """节点抽象基类 - 策略模式的接口定义"""
    
    @classmethod
    @abstractmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """定义节点输入类型 - 策略的配置接口"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Tuple[Any, ...]:
        """节点执行逻辑 - 策略的核心实现"""
        pass
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs) -> bool:
        """输入验证 - 策略的验证逻辑"""
        return True
```

**策略模式的具体实现**：
```python
# 不同节点实现不同的执行策略
class CLIPTextEncode(ComfyNodeABC):
    """CLIP文本编码器 - 文本处理策略"""
    
    def encode(self, clip, text):
        # 文本编码策略：分词 → 编码 → 池化
        tokens = clip.tokenize(text)
        encoded = clip.encode_with_transformers(tokens)
        return (encoded,)

class VAEEncode(ComfyNodeABC):
    """VAE编码器 - 图像编码策略"""
    
    def encode(self, vae, pixels):
        # 图像编码策略：预处理 → VAE编码 → 潜在表示
        pixels = self._preprocess_pixels(pixels)
        latent = vae.encode(pixels)
        return (latent,)

class KSampler(ComfyNodeABC):
    """采样器 - 扩散模型采样策略"""
    
    def sample(self, model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent_image):
        # 采样策略：噪声调度 → 迭代去噪 → 结果生成
        # 根据sampler_name选择不同的采样算法
        if sampler_name == "euler":
            return self._euler_sampling(model, steps, cfg, positive, negative, latent_image)
        elif sampler_name == "dpm_2":
            return self._dpm2_sampling(model, steps, cfg, positive, negative, latent_image)
        # ... 其他采样算法
```

**策略模式的优势**：
1. **算法可替换**：不同节点实现不同的处理算法
2. **职责分离**：每个节点只关注自己的核心逻辑
3. **易于测试**：每个策略可以独立测试

#### 1.1.3 模板方法模式：可扩展的验证逻辑

**设计意图**：提供可重用的验证框架，允许子类扩展特定验证逻辑。

**源码分析**：
```python
class ComfyNodeABC(ABC):
    """模板方法模式的基类实现"""
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs) -> bool:
        """模板方法：定义验证流程的骨架"""
        
        # 步骤1：基本类型检查（模板方法的固定部分）
        if not cls._validate_basic_types(kwargs):
            return False
        
        # 步骤2：自定义验证（模板方法的可变部分）
        if hasattr(cls, '_custom_validate'):
            if not cls._custom_validate(**kwargs):
                return False
        
        # 步骤3：依赖关系验证
        if not cls._validate_dependencies(kwargs):
            return False
        
        return True
    
    @classmethod
    def _validate_basic_types(cls, inputs: Dict) -> bool:
        """基本类型验证 - 模板方法的固定实现"""
        input_types = cls.INPUT_TYPES()
        
        for key, value in inputs.items():
            if key in input_types.get("required", {}):
                expected_type = input_types["required"][key]
                if not cls._check_type(value, expected_type):
                    return False
        
        return True
    
    @classmethod
    def _check_type(cls, value, expected_type) -> bool:
        """类型检查实现"""
        if isinstance(expected_type, tuple):
            # 处理类型元组（如 ("IMAGE", "LATENT")）
            return any(cls._check_type(value, t) for t in expected_type)
        elif expected_type == "IMAGE":
            return isinstance(value, torch.Tensor) and value.dim() == 4
        elif expected_type == "LATENT":
            return isinstance(value, dict) and "samples" in value
        # ... 其他类型检查
        
        return True
```

**子类扩展示例**：
```python
class AdvancedImageProcessor(ComfyNodeABC):
    """高级图像处理器 - 扩展验证逻辑"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "operation": (["blur", "sharpen", "edge_detect"],),
                "intensity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0}),
            }
        }
    
    @classmethod
    def _custom_validate(cls, **kwargs):
        """自定义验证逻辑 - 模板方法的扩展点"""
        image = kwargs.get("image")
        operation = kwargs.get("operation")
        intensity = kwargs.get("intensity")
        
        # 自定义验证规则
        if operation == "edge_detect" and intensity > 3.0:
            # 边缘检测强度不能太高
            return False
        
        if image is not None:
            # 检查图像尺寸
            height, width = image.shape[2], image.shape[3]
            if height > 4096 or width > 4096:
                # 图像太大，可能内存不足
                return False
        
        return True
```

**模板方法模式的优势**：
1. **代码复用**：公共验证逻辑在基类中实现
2. **扩展灵活**：子类可以重写特定验证步骤
3. **结构清晰**：验证流程有明确的步骤定义

#### 1.1.4 观察者模式：数据流驱动的执行

**设计意图**：节点间通过数据流连接，形成观察链，实现数据驱动的执行。

**实现机制**：
```python
class DataFlowGraph:
    """数据流图 - 观察者模式的实现"""
    
    def __init__(self):
        self.nodes: Dict[str, NodeInfo] = {}
        self.connections: List[Connection] = []
        self.observers: Dict[str, List[str]] = {}  # 观察者映射
        
    def add_connection(self, from_node: str, from_socket: str, to_node: str, to_socket: str):
        """添加数据连接 - 建立观察关系"""
        connection = Connection(from_node, from_socket, to_node, to_socket)
        self.connections.append(connection)
        
        # 建立观察关系
        if from_node not in self.observers:
            self.observers[from_node] = []
        
        if to_node not in self.observers[from_node]:
            self.observers[from_node].append(to_node)
    
    def notify_observers(self, node_id: str, output_data: Dict[str, Any]):
        """通知观察者节点 - 观察者模式的核心"""
        if node_id not in self.observers:
            return
        
        for observer_id in self.observers[node_id]:
            # 获取观察者需要的数据
            required_inputs = self._get_required_inputs(observer_id, node_id)
            
            # 准备输入数据
            inputs = {}
            for socket_name, data_key in required_inputs.items():
                if data_key in output_data:
                    inputs[socket_name] = output_data[data_key]
            
            # 触发观察者执行
            self.execute_node(observer_id, inputs)
    
    def _get_required_inputs(self, observer_id: str, source_id: str) -> Dict[str, str]:
        """获取观察者需要的输入数据"""
        required = {}
        
        for conn in self.connections:
            if conn.from_node == source_id and conn.to_node == observer_id:
                required[conn.to_socket] = conn.from_socket
        
        return required
```

**数据流驱动的执行示例**：
```python
# 构建数据流图
graph = DataFlowGraph()

# 添加节点
graph.add_node("text_encode", CLIPTextEncode)
graph.add_node("ksampler", KSampler)
graph.add_node("vae_decode", VAEDecode)

# 建立观察关系（数据连接）
graph.add_connection("text_encode", "CONDITIONING", "ksampler", "positive")
graph.add_connection("ksampler", "LATENT", "vae_decode", "samples")

# 执行流程
# 1. text_encode执行，生成CONDITIONING
# 2. 通知观察者ksampler：CONDITIONING数据已就绪
# 3. ksampler执行，生成LATENT
# 4. 通知观察者vae_decode：LATENT数据已就绪
# 5. vae_decode执行，生成最终图像
```

**观察者模式的优势**：
1. **松耦合**：节点间不直接依赖，通过数据流连接
2. **动态响应**：数据变化自动触发相关节点执行
3. **可扩展**：新节点可以轻松加入现有数据流

### 1.2 工作流引擎调度机制

工作流引擎是ComfyUI的执行大脑，负责协调所有节点的执行。它基于有向无环图（DAG）实现智能调度。

#### 1.2.1 DAG构建和拓扑排序算法

**DAG构建过程**：
```python
class WorkflowDAG:
    """工作流有向无环图"""
    
    def __init__(self):
        self.nodes: Dict[str, NodeInfo] = {}
        self.edges: Dict[str, List[str]] = {}  # 邻接表
        self.reverse_edges: Dict[str, List[str]] = {}  # 反向邻接表
        
    def build_from_prompt(self, prompt: Dict) -> 'WorkflowDAG':
        """从prompt数据构建DAG"""
        dag = WorkflowDAG()
        
        # 解析节点
        for node_id, node_data in prompt.items():
            if node_id == "last_node":
                continue
            
            node_info = NodeInfo(
                id=node_id,
                class_type=node_data["class_type"],
                inputs=node_data.get("inputs", {})
            )
            dag.nodes[node_id] = node_info
        
        # 构建边（依赖关系）
        for node_id, node_info in dag.nodes.items():
            dag.edges[node_id] = []
            dag.reverse_edges[node_id] = []
            
            for input_name, input_value in node_info.inputs.items():
                if isinstance(input_value, list) and len(input_value) == 2:
                    # 格式: [source_node_id, source_output_index]
                    source_node = input_value[0]
                    if source_node in dag.nodes:
                        # 添加边：source_node → node_id
                        dag.edges[source_node].append(node_id)
                        dag.reverse_edges[node_id].append(source_node)
        
        return dag
```

**拓扑排序算法（Kahn算法）**：
```python
def topological_sort(self) -> List[str]:
    """拓扑排序 - 确定节点执行顺序"""
    
    # 计算入度
    in_degree = {node_id: 0 for node_id in self.nodes}
    for node_id in self.nodes:
        for neighbor in self.edges.get(node_id, []):
            in_degree[neighbor] += 1
    
    # 初始化队列：入度为0的节点
    queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
    sorted_nodes = []
    
    # Kahn算法核心
    while queue:
        current = queue.popleft()
        sorted_nodes.append(current)
        
        # 减少邻居节点的入度
        for neighbor in self.edges.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # 检查是否有环
    if len(sorted_nodes) != len(self.nodes):
        # 有环，无法拓扑排序
        raise ValueError("工作流中存在循环依赖")
    
    return sorted_nodes
```

**拓扑排序示例**：
```
原始依赖关系:
A → B → D
  ↘ C ↗

计算入度:
A: 0, B: 1, C: 1, D: 2

拓扑排序过程:
1. 初始队列: [A] (入度为0)
2. 处理A: 队列 → [], 排序 → [A]
   - 减少B入度: B:1→0, 加入队列
   - 减少C入度: C:1→0, 加入队列
3. 队列: [B, C]
4. 处理B: 队列 → [C], 排序 → [A, B]
   - 减少D入度: D:2→1
5. 处理C: 队列 → [], 排序 → [A, B, C]
   - 减少D入度: D:1→0, 加入队列
6. 处理D: 队列 → [], 排序 → [A, B, C, D]

最终执行顺序: A → B → C → D
```

#### 1.2.2 循环依赖检测和解决

**循环依赖检测算法**：
```python
def detect_cycles(self) -> List[List[str]]:
    """检测工作流中的循环依赖"""
    
    def dfs(node_id: str, visited: Set[str], stack: Set[str], path: List[str]) -> List[List[str]]:
        """深度优先搜索检测环"""
        cycles = []
        
        visited.add(node_id)
        stack.add(node_id)
        path.append(node_id)
        
        for neighbor in self.edges.get(node_id, []):
            if neighbor not in visited:
                # 递归搜索
                cycles.extend(dfs(neighbor, visited, stack, path.copy()))
            elif neighbor in stack:
                # 发现环：从neighbor到当前节点的路径
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
        
        stack.remove(node_id)
        return cycles
    
    # 执行DFS检测所有环
    all_cycles = []
    visited = set()
    
    for node_id in self.nodes:
        if node_id not in visited:
            cycles = dfs(node_id, visited, set(), [])
            all_cycles.extend(cycles)
    
    return all_cycles
```

**循环依赖解决策略**：
```python
def resolve_cycles(self, cycles: List[List[str]]) -> bool:
    """尝试解决循环依赖"""
    
    if not cycles:
        return True
    
    # 策略1：自动断开最小权重的边
    for cycle in cycles:
        # 找到权重最小的边（基于启发式规则）
        min_weight_edge = self._find_min_weight_edge_in_cycle(cycle)
        
        if min_weight_edge:
            # 断开这条边
            from_node, to_node = min_weight_edge
            self._remove_edge(from_node, to_node)
            print(f"警告：自动断开循环依赖边 {from_node} → {to_node}")
    
    # 重新检测
    remaining_cycles = self.detect_cycles()
    
    if remaining_cycles:
        # 策略2：提示用户手动解决
        print("无法自动解决的循环依赖：")
        for cycle in remaining_cycles:
            print(f"  → {' → '.join(cycle)}")
        
        return False
    
    return True

def _find_min_weight_edge_in_cycle(self, cycle: List[str]) -> Optional[Tuple[str, str]]:
    """在环中找到权重最小的边"""
    min_weight = float('inf')
    min_edge = None
    
    for i in range(len(cycle) - 1):
        from_node = cycle[i]
        to_node = cycle[i + 1]
        
        # 计算边权重（启发式规则）
        weight = self._calculate_edge_weight(from_node, to_node)
        
        if weight < min_weight:
            min_weight = weight
            min_edge = (from_node, to_node)
    
    return min_edge

def _calculate_edge_weight(self, from_node: str, to_node: str) -> float:
    """计算边权重（启发式规则）"""
    weight = 0.0
    
    # 规则1：数据依赖强度
    # 检查连接的数据类型和数量
    connections = self._get_connections_between(from_node, to_node)
    weight += len(connections) * 10.0
    
    # 规则2：节点重要性
    from_importance = self._get_node_importance(from_node)
    to_importance = self._get_node_importance(to_node)
    weight += (from_importance + to_importance) * 5.0
    
    # 规则3：替代路径存在性
    if self._has_alternative_path(from_node, to_node):
        weight -= 20.0  # 有替代路径，权重降低
    
    return weight
```

#### 1.2.3 并行执行潜力分析

**并行度分析算法**：
```python
def analyze_parallelism(self) -> Dict[str, Any]:
    """分析工作流的并行执行潜力"""
    
    # 计算关键路径
    critical_path = self._find_critical_path()
    
    # 识别可并行执行的节点组
    parallel_groups = self._find_parallel_groups()
    
    # 估计并行加速比
    speedup_estimation = self._estimate_speedup(critical_path, parallel_groups)
    
    return {
        "critical_path": critical_path,
        "parallel_groups": parallel_groups,
        "estimated_speedup": speedup_estimation,
        "parallelism_level": self._calculate_parallelism_level(parallel_groups)
    }

def _find_critical_path(self) -> List[str]:
    """找到关键路径（最长执行路径）"""
    # 使用动态规划计算最长路径
    dp = {node_id: 0 for node_id in self.nodes}
    predecessor = {node_id: None for node_id in self.nodes}
    
    # 按拓扑顺序处理节点
    sorted_nodes = self.topological_sort()
    
    for node_id in sorted_nodes:
        node_info = self.nodes[node_id]
        
        # 估计节点执行时间
        exec_time = self._estimate_execution_time(node_info)
        
        # 更新DP值
        max_time = 0
        best_pred = None
        
        for pred in self.reverse_edges.get(node_id, []):
            pred_time = dp[pred]
            if pred_time > max_time:
                max_time = pred_time
                best_pred = pred
        
        dp[node_id] = max_time + exec_time
        predecessor[node_id] = best_pred
    
    # 找到关键路径终点
    end_node = max(dp.items(), key=lambda x: x[1])[0]
    
    # 回溯构建关键路径
    critical_path = []
    current = end_node
    
    while current is not None:
        critical_path.append(current)
        current = predecessor[current]
    
    return list(reversed(critical_path))

def _find_parallel_groups(self) -> List[List[str]]:
    """识别可以并行执行的节点组"""
    
    # 构建依赖层次
    levels = self._assign_levels()
    
    # 按层次分组
    parallel_groups = []
    
    for level, nodes in levels.items():
        # 检查同一层次的节点是否可以并行
        if self._can_parallelize(nodes):
            parallel_groups.append(nodes)
    
    return parallel_groups

def _assign_levels(self) -> Dict[int, List[str]]:
    """为节点分配层次（基于依赖深度）"""
    levels = {}
    
    for node_id in self.nodes:
        # 计算节点的最大依赖深度
        depth = self._calculate_dependency_depth(node_id)
        
        if depth not in levels:
            levels[depth] = []
        
        levels[depth].append(node_id)
    
    return levels

def _can_parallelize(self, nodes: List[str]) -> bool:
    """检查一组节点是否可以并行执行"""
    
    # 规则1：节点间没有数据依赖
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if self._has_dependency(nodes[i], nodes[j]) or self._has_dependency(nodes[j], nodes[i]):
                return False
    
    # 规则2：资源需求不冲突
    resource_requirements = []
    for node_id in nodes:
        requirements = self._estimate_resource_requirements(node_id)
        resource_requirements.append(requirements)
    
    # 检查资源冲突（如GPU内存、CPU核心等）
    if self._has_resource_conflict(resource_requirements):
        return False
    
    return True
```

#### 1.2.4 错误处理和恢复机制

**错误处理框架**：
```python
class ExecutionErrorHandler:
    """执行错误处理器"""
    
    ERROR_CATEGORIES = {
        "memory": ["OutOfMemoryError", "CUDA out of memory"],
        "computation": ["RuntimeError", "ValueError", "TypeError"],
        "io": ["FileNotFoundError", "PermissionError", "IOError"],
        "network": ["ConnectionError", "TimeoutError"],
        "model": ["ModelLoadingError", "ModelFormatError"],
    }
    
    def handle_error(self, error: Exception, context: Dict) -> Dict:
        """处理执行错误"""
        
        error_type = self._classify_error(error)
        
        # 根据错误类型选择处理策略
        if error_type == "memory":
            return self._handle_memory_error(error, context)
        elif error_type == "computation":
            return self._handle_computation_error(error, context)
        elif error_type == "io":
            return self._handle_io_error(error, context)
        elif error_type == "network":
            return self._handle_network_error(error, context)
        elif error_type == "model":
            return self._handle_model_error(error, context)
        else:
            return self._handle_unknown_error(error, context)
    
    def _handle_memory_error(self, error: Exception, context: Dict) -> Dict:
        """处理内存错误"""
        suggestions = []
        recovery_actions = []
        
        # 分析内存使用情况
        memory_info = self._analyze_memory_usage(context)
        
        # 根据分析结果提供建议
        if memory_info["vram_usage"] > 0.9:
            suggestions.append("VRAM使用率超过90%，建议：")
            suggestions.append("  1. 降低图像分辨率或批处理大小")
            suggestions.append("  2. 启用--lowvram模式")
            suggestions.append("  3. 使用更小的模型")
            
            recovery_actions.append({
                "action": "reduce_batch_size",
                "parameters": {"factor": 0.5}
            })
        
        if memory_info["system_memory"] > 0.8:
            suggestions.append("系统内存使用率高，建议：")
            suggestions.append("  1. 关闭其他应用程序")
            suggestions.append("  2. 增加系统交换空间")
            suggestions.append("  3. 优化工作流减少中间结果")
        
        return {
            "error_type": "memory",
            "error_message": str(error),
            "suggestions": suggestions,
            "recovery_actions": recovery_actions,
            "can_retry": True
        }
    
    def _handle_computation_error(self, error: Exception, context: Dict) -> Dict:
        """处理计算错误"""
        error_msg = str(error)
        
        if "shape" in error_msg.lower():
            # 形状不匹配错误
            return {
                "error_type": "computation.shape_mismatch",
                "error_message": error_msg,
                "suggestions": [
                    "检查节点输入输出的形状匹配",
                    "确保数据类型一致",
                    "验证工作流连接是否正确"
                ],
                "recovery_actions": [
                    {"action": "validate_connections", "node": context.get("node_id")}
                ],
                "can_retry": False  # 需要用户干预
            }
        
        # 其他计算错误
        return {
            "error_type": "computation.general",
            "error_message": error_msg,
            "suggestions": ["检查计算参数和输入数据"],
            "can_retry": True
        }
```

**自动恢复机制**：
```python
class AutoRecoverySystem:
    """自动恢复系统"""
    
    def __init__(self):
        self.retry_count = {}
        self.max_retries = 3
    
    def execute_with_recovery(self, executor, workflow, max_retries: int = 3) -> Dict:
        """带自动恢复的执行"""
        
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            try:
                result = executor.execute(workflow)
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1,
                    "recovery_actions": []
                }
                
            except Exception as e:
                attempt += 1
                last_error = e
                
                # 分析错误并尝试恢复
                recovery_plan = self._create_recovery_plan(e, workflow, attempt)
                
                if not recovery_plan["can_recover"]:
                    # 无法自动恢复
                    break
                
                # 执行恢复操作
                workflow = self._apply_recovery_actions(workflow, recovery_plan["actions"])
                print(f"尝试 {attempt}/{max_retries}: {recovery_plan['message']}")
        
        # 所有重试都失败
        return {
            "success": False,
            "error": str(last_error),
            "attempts": attempt,
            "recovery_actions": self._get_final_suggestions(last_error)
        }
    
    def _create_recovery_plan(self, error: Exception, workflow: Dict, attempt: int) -> Dict:
        """创建恢复计划"""
        
        error_handler = ExecutionErrorHandler()
        error_analysis = error_handler.handle_error(error, {"workflow": workflow})
        
        if attempt == 1:
            # 第一次重试：尝试简单恢复
            if error_analysis["error_type"] == "memory":
                return {
                    "can_recover": True,
                    "message": "内存不足，尝试优化内存使用",
                    "actions": [
                        {"type": "clear_cache", "scope": "all"},
                        {"type": "reduce_batch_size", "factor": 0.5}
                    ]
                }
        
        elif attempt == 2:
            # 第二次重试：更激进的恢复
            if error_analysis["error_type"] == "memory":
                return {
                    "can_recover": True,
                    "message": "内存严重不足，启用低内存模式",
                    "actions": [
                        {"type": "enable_lowvram_mode"},
                        {"type": "reduce_resolution", "factor": 0.7},
                        {"type": "split_workflow", "chunks": 2}
                    ]
                }
        
        # 无法自动恢复
        return {
            "can_recover": False,
            "message": "需要用户干预",
            "actions": []
        }
```

### 1.3 内存管理系统设计

ComfyUI的内存管理系统是其性能关键，特别是在处理大型模型和高分辨率图像时。

#### 1.3.1 智能VRAM管理策略

**设备选择策略**：
```python
class DeviceManager:
    """设备管理器 - 智能选择计算设备"""
    
    DEVICE_PRIORITY = [
        ("cuda", self._check_cuda),      # NVIDIA GPU
        ("mps", self._check_mps),        # Apple Silicon
        ("cpu", lambda: True)            # CPU回退
    ]
    
    @staticmethod
    def get_optimal_device(tensor_size: int = 0) -> torch.device:
        """获取最优计算设备"""
        
        for device_name, check_func in DeviceManager.DEVICE_PRIORITY:
            if check_func():
                device = torch.device(device_name)
                
                # 检查设备是否适合当前任务
                if DeviceManager._is_device_suitable(device, tensor_size):
                    return device
        
        return torch.device("cpu")
    
    @staticmethod
    def _check_cuda() -> bool:
        """检查CUDA可用性"""
        if not torch.cuda.is_available():
            return False
        
        # 检查CUDA版本兼容性
        cuda_version = torch.version.cuda
        if cuda_version < "11.0":
            print(f"警告：CUDA版本 {cuda_version} 可能不兼容")
        
        return True
    
    @staticmethod
    def _check_mps() -> bool:
        """检查MPS可用性（Apple Silicon）"""
        return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    
    @staticmethod
    def _is_device_suitable(device: torch.device, tensor_size: int) -> bool:
        """检查设备是否适合当前任务"""
        
        if device.type == "cuda":
            # 检查VRAM是否足够
            free_vram = DeviceManager._get_free_vram()
            
            # 估计所需VRAM：张量大小 + 模型内存 + 开销
            estimated_need = tensor_size * 4  # 假设float32
            estimated_need += 512 * 1024 * 1024  # 模型基础开销
            estimated_need *= 1.2  # 20%安全边际
            
            if estimated_need > free_vram:
                print(f"VRAM不足：需要{estimated_need/1024/1024:.1f}MB，可用{free_vram/1024/1024:.1f}MB")
                return False
        
        return True
    
    @staticmethod
    def _get_free_vram() -> int:
        """获取可用VRAM"""
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()
        return 0
```

**模型懒加载机制**：
```python
class LazyModelLoader:
    """懒加载模型管理器"""
    
    def __init__(self):
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.model_cache: Dict[str, Any] = {}
        self.access_history: Dict[str, float] = {}  # 最近访问时间
    
    def load_model(self, model_path: str, force_reload: bool = False) -> Any:
        """懒加载模型"""
        
        model_key = self._get_model_key(model_path)
        
        # 检查是否已加载
        if not force_reload and model_key in self.loaded_models:
            # 更新访问时间
            self.access_history[model_key] = time.time()
            return self.loaded_models[model_key].model
        
        # 检查缓存
        if model_key in self.model_cache:
            print(f"从缓存加载模型: {model_path}")
            model_data = self.model_cache[model_key]
        else:
            # 从磁盘加载
            print(f"从磁盘加载模型: {model_path}")
            model_data = self._load_from_disk(model_path)
            self.model_cache[model_key] = model_data
        
        # 创建模型信息
        model_info = ModelInfo(
            path=model_path,
            model=model_data,
            load_time=time.time(),
            memory_usage=self._estimate_model_memory(model_data)
        )
        
        # 检查内存是否足够
        if not self._has_enough_memory(model_info.memory_usage):
            # 需要卸载一些模型
            self._unload_least_recently_used()
        
        # 加载到设备
        device = DeviceManager.get_optimal_device(model_info.memory_usage)
        model_info.model.to(device)
        
        # 记录加载
        self.loaded_models[model_key] = model_info
        self.access_history[model_key] = time.time()
        
        return model_info.model
    
    def _unload_least_recently_used(self):
        """卸载最近最少使用的模型"""
        if not self.access_history:
            return
        
        # 找到最近最少访问的模型
        lru_key = min(self.access_history.items(), key=lambda x: x[1])[0]
        
        if lru_key in self.loaded_models:
            model_info = self.loaded_models[lru_key]
            
            print(f"卸载模型以释放内存: {model_info.path}")
            
            # 移动到CPU（保留在缓存中）
            model_info.model.to("cpu")
            
            # 从已加载列表中移除
            del self.loaded_models[lru_key]
            del self.access_history[lru_key]
            
            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def _has_enough_memory(self, required_memory: int) -> bool:
        """检查是否有足够内存"""
        if torch.cuda.is_available():
            free_memory = DeviceManager._get_free_vram()
            return required_memory * 1.2 <= free_memory  # 20%安全边际
        
        return True  # CPU模式总有"足够"内存
```

#### 1.3.2 张量内存池优化

**内存池实现**：
```python
class TensorMemoryPool:
    """张量内存池 - 重用内存减少分配开销"""
    
    def __init__(self, max_pool_size: int = 100):
        self.pool: Dict[Tuple[int, torch.dtype, torch.device], List[torch.Tensor]] = {}
        self.max_pool_size = max_pool_size
        self.allocation_stats = {
            "total_allocated": 0,
            "total_reused": 0,
            "memory_saved": 0
        }
    
    def allocate(self, shape: Tuple[int, ...], dtype: torch.dtype = torch.float32, 
                 device: torch.device = None) -> torch.Tensor:
        """分配张量，优先重用池中内存"""
        
        if device is None:
            device = DeviceManager.get_optimal_device()
        
        key = (shape, dtype, device)
        
        # 尝试从池中获取
        if key in self.pool and self.pool[key]:
            tensor = self.pool[key].pop()
            
            # 清空内容（重要！）
            tensor.zero_()
            
            self.allocation_stats["total_reused"] += 1
            self.allocation_stats["memory_saved"] += tensor.numel() * tensor.element_size()
            
            return tensor
        
        # 分配新张量
        tensor = torch.empty(shape, dtype=dtype, device=device)
        
        self.allocation_stats["total_allocated"] += 1
        
        return tensor
    
    def release(self, tensor: torch.Tensor):
        """释放张量到内存池"""
        
        if tensor is None:
            return
        
        key = (tensor.shape, tensor.dtype, tensor.device)
        
        # 初始化池（如果不存在）
        if key not in self.pool:
            self.pool[key] = []
        
        # 限制池大小，避免内存泄漏
        if len(self.pool[key]) < self.max_pool_size:
            self.pool[key].append(tensor)
        else:
            # 池已满，直接释放
            del tensor
    
    def clear(self):
        """清空内存池"""
        for tensors in self.pool.values():
            for tensor in tensors:
                del tensor
        
        self.pool.clear()
        
        # 清理GPU缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取内存池统计信息"""
        total_pooled = sum(len(tensors) for tensors in self.pool.values())
        total_memory = sum(
            sum(t.numel() * t.element_size() for t in tensors)
            for tensors in self.pool.values()
        )
        
        return {
            **self.allocation_stats,
            "pooled_tensors": total_pooled,
            "pooled_memory_mb": total_memory / (1024 * 1024),
            "reuse_rate": self.allocation_stats["total_reused"] / max(1, self.allocation_stats["total_allocated"])
        }
```

**内存访问模式优化**：
```python
class MemoryAccessOptimizer:
    """内存访问模式优化器"""
    
    def optimize_access_pattern(self, operations: List[Operation]) -> List[Operation]:
        """优化内存访问模式以减少缓存未命中"""
        
        # 分析访问模式
        access_patterns = self._analyze_access_patterns(operations)
        
        # 重新排序操作
        reordered = self._reorder_for_cache_locality(operations, access_patterns)
        
        # 合并连续操作
        merged = self._merge_contiguous_operations(reordered)
        
        # 添加预取提示
        optimized = self._add_prefetch_hints(merged)
        
        return optimized
    
    def _analyze_access_patterns(self, operations: List[Operation]) -> Dict[str, Any]:
        """分析内存访问模式"""
        patterns = {
            "sequential": [],      # 顺序访问
            "random": [],          # 随机访问
            "strided": [],         # 跨步访问
            "gather_scatter": []   # 聚集-分散访问
        }
        
        for op in operations:
            if self._is_sequential_access(op):
                patterns["sequential"].append(op)
            elif self._is_random_access(op):
                patterns["random"].append(op)
            elif self._is_strided_access(op):
                patterns["strided"].append(op)
            else:
                patterns["gather_scatter"].append(op)
        
        return patterns
    
    def _reorder_for_cache_locality(self, operations: List[Operation], 
                                   patterns: Dict[str, Any]) -> List[Operation]:
        """重新排序操作以提高缓存局部性"""
        
        optimized = []
        
        # 策略1：将顺序访问的操作放在一起
        optimized.extend(patterns["sequential"])
        
        # 策略2：处理相同数据的操作连续执行
        data_groups = self._group_by_data(operations)
        for data_id, ops in data_groups.items():
            if len(ops) > 1:
                # 相同数据的操作连续执行
                optimized.extend(ops)
        
        # 策略3：随机访问操作放在最后（缓存污染最小）
        optimized.extend(patterns["random"])
        
        return optimized
    
    def _is_sequential_access(self, op: Operation) -> bool:
        """检查是否为顺序访问"""
        # 启发式规则：连续内存地址访问
        if hasattr(op, "access_pattern"):
            pattern = op.access_pattern
            
            # 检查是否访问连续内存块
            if pattern.get("stride", 1) == 1:
                return True
        
        return False
```

### 1.4 插件系统架构

ComfyUI的插件系统支持动态扩展，是其生态繁荣的关键。

#### 1.4.1 扩展点设计模式

**扩展点注册机制**：
```python
class ExtensionPointRegistry:
    """扩展点注册表"""
    
    def __init__(self):
        self.extension_points: Dict[str, List[Callable]] = {
            # 核心扩展点
            "node_registration": [],      # 节点注册
            "model_loading": [],          # 模型加载
            "workflow_execution": [],     # 工作流执行
            "ui_initialization": [],      # UI初始化
            
            # 生命周期扩展点
            "pre_node_execute": [],       # 节点执行前
            "post_node_execute": [],      # 节点执行后
            "pre_workflow_execute": [],   # 工作流执行前
            "post_workflow_execute": [],  # 工作流执行后
            
            # 数据扩展点
            "data_validation": [],        # 数据验证
            "data_transformation": [],    # 数据转换
            "data_persistence": [],       # 数据持久化
        }
    
    def register_extension(self, point_name: str, extension_func: Callable):
        """注册扩展函数"""
        
        if point_name not in self.extension_points:
            # 动态创建新的扩展点
            self.extension_points[point_name] = []
        
        self.extension_points[point_name].append(extension_func)
        
        print(f"注册扩展: {point_name} -> {extension_func.__name__}")
    
    def execute_extensions(self, point_name: str, *args, **kwargs) -> List[Any]:
        """执行所有注册的扩展"""
        
        if point_name not in self.extension_points:
            return []
        
        results = []
        
        for extension in self.extension_points[point_name]:
            try:
                result = extension(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                print(f"扩展执行失败 {extension.__name__}: {e}")
                # 继续执行其他扩展
        
        return results
    
    def get_extension_points(self) -> List[str]:
        """获取所有扩展点"""
        return list(self.extension_points.keys())
```

**插件加载器**：
```python
class PluginLoader:
    """插件加载器"""
    
    def __init__(self, extension_registry: ExtensionPointRegistry):
        self.registry = extension_registry
        self.loaded_plugins: Dict[str, PluginInfo] = {}
        self.plugin_directories = [
            "custom_nodes",
            "comfyui_plugins",
            os.path.expanduser("~/.comfyui/plugins")
        ]
    
    def discover_plugins(self) -> List[str]:
        """发现可用插件"""
        
        plugins = []
        
        for plugin_dir in self.plugin_directories:
            if not os.path.exists(plugin_dir):
                continue
            
            # 扫描目录
            for item in os.listdir(plugin_dir):
                plugin_path = os.path.join(plugin_dir, item)
                
                if self._is_plugin_directory(plugin_path):
                    plugins.append(plugin_path)
        
        return plugins
    
    def load_plugin(self, plugin_path: str) -> bool:
        """加载插件"""
        
        plugin_name = os.path.basename(plugin_path)
        
        # 检查是否已加载
        if plugin_name in self.loaded_plugins:
            print(f"插件已加载: {plugin_name}")
            return True
        
        try:
            # 加载插件模块
            module = self._load_plugin_module(plugin_path)
            
            # 执行插件初始化
            if hasattr(module, "initialize"):
                module.initialize(self.registry)
            
            # 注册插件提供的节点
            if hasattr(module, "NODE_CLASS_MAPPINGS"):
                for node_name, node_class in module.NODE_CLASS_MAPPINGS.items():
                    self.registry.register_extension("node_registration", 
                                                    lambda nc=node_class: register_node(nc))
            
            # 记录插件信息
            plugin_info = PluginInfo(
                name=plugin_name,
                path=plugin_path,
                module=module,
                load_time=time.time()
            )
            
            self.loaded_plugins[plugin_name] = plugin_info
            
            print(f"成功加载插件: {plugin_name}")
            return True
            
        except Exception as e:
            print(f"加载插件失败 {plugin_path}: {e}")
            return False
    
    def _load_plugin_module(self, plugin_path: str) -> Any:
        """加载插件Python模块"""
        
        # 将插件目录添加到Python路径
        plugin_dir = os.path.dirname(plugin_path)
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        
        # 导入插件模块
        plugin_name = os.path.basename(plugin_path)
        module_name = f"{plugin_name}.main" if os.path.exists(os.path.join(plugin_path, "main.py")) else plugin_name
        
        return importlib.import_module(module_name)
    
    def _is_plugin_directory(self, path: str) -> bool:
        """检查是否为插件目录"""
        
        if not os.path.isdir(path):
            return False
        
        # 检查必要的文件
        required_files = ["__init__.py", "nodes.py"]
        
        for file in required_files:
            if not os.path.exists(os.path.join(path, file)):
                return False
        
        return True
```

#### 1.4.2 动态模块加载机制

**热重载支持**：
```python
class HotReloadManager:
    """热重载管理器"""
    
    def __init__(self, plugin_loader: PluginLoader):
        self.loader = plugin_loader
        self.watchers: Dict[str, FileWatcher] = {}
        self.last_reload_time: Dict[str, float] = {}
        
    def watch_plugin(self, plugin_path: str):
        """监视插件文件变化"""
        
        if plugin_path in self.watchers:
            return
        
        watcher = FileWatcher(plugin_path)
        watcher.on_change = lambda: self._reload_plugin(plugin_path)
        
        self.watchers[plugin_path] = watcher
        watcher.start()
        
        print(f"开始监视插件: {plugin_path}")
    
    def _reload_plugin(self, plugin_path: str):
        """重新加载插件"""
        
        current_time = time.time()
        plugin_name = os.path.basename(plugin_path)
        
        # 防抖：避免频繁重载
        if plugin_name in self.last_reload_time:
            time_since_last = current_time - self.last_reload_time[plugin_name]
            if time_since_last < 2.0:  # 2秒内不重载
                return
        
        print(f"检测到插件变化，重新加载: {plugin_name}")
        
        try:
            # 卸载旧模块
            if plugin_name in self.loader.loaded_plugins:
                old_module = self.loader.loaded_plugins[plugin_name].module
                
                # 从sys.modules中移除
                for key in list(sys.modules.keys()):
                    if key.startswith(plugin_name):
                        del sys.modules[key]
            
            # 重新加载
            success = self.loader.load_plugin(plugin_path)
            
            if success:
                self.last_reload_time[plugin_name] = current_time
                print(f"插件重载成功: {plugin_name}")
            else:
                print(f"插件重载失败: {plugin_name}")
                
        except Exception as e:
            print(f"插件重载错误 {plugin_name}: {e}")
```

**插件间通信机制**：
```python
class PluginCommunicationBus:
    """插件间通信总线"""
    
    def __init__(self):
        self.channels: Dict[str, List[Callable]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.event_loop = asyncio.new_event_loop()
    
    def subscribe(self, channel: str, callback: Callable):
        """订阅频道"""
        
        if channel not in self.channels:
            self.channels[channel] = []
        
        self.channels[channel].append(callback)
    
    def unsubscribe(self, channel: str, callback: Callable):
        """取消订阅"""
        
        if channel in self.channels:
            if callback in self.channels[channel]:
                self.channels[channel].remove(callback)
    
    async def publish_async(self, channel: str, message: Any):
        """异步发布消息"""
        
        if channel not in self.channels:
            return
        
        # 创建任务并行调用所有回调
        tasks = []
        for callback in self.channels[channel]:
            task = asyncio.create_task(self._safe_call(callback, message))
            tasks.append(task)
        
        # 等待所有回调完成
        if tasks:
            await asyncio.gather(*tasks)
    
    def publish(self, channel: str, message: Any):
        """同步发布消息"""
        
        # 在事件循环中运行
        if not self.event_loop.is_running():
            asyncio.set_event_loop(self.event_loop)
        
        self.event_loop.run_until_complete(self.publish_async(channel, message))
    
    async def _safe_call(self, callback: Callable, message: Any):
        """安全调用回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
        except Exception as e:
            print(f"插件回调错误: {e}")
```

---

## 第一部分总结

### 技术收获

#### 1. 设计模式应用
- **工厂模式**：实现节点的动态注册和创建
- **策略模式**：支持多样化的节点执行算法
- **模板方法模式**：提供可扩展的验证框架
- **观察者模式**：实现数据流驱动的执行

#### 2. 算法实现
- **拓扑排序**：Kahn算法确定节点执行顺序
- **循环检测**：DFS算法检测工作流中的环
- **内存管理**：LRU缓存淘汰和内存池优化
- **并行分析**：关键路径识别和并行组划分

#### 3. 系统架构
- **模块化设计**：清晰的职责分离
- **扩展性设计**：插件系统支持动态扩展
- **性能优化**：智能内存管理和懒加载
- **容错设计**：错误处理和自动恢复机制

---

## 第二部分：关键调用链追踪

理解ComfyUI的完整执行路径对于性能优化和问题排查至关重要。本部分将追踪从用户点击到GPU计算的完整调用链。

### 2.1 完整执行路径分析

#### 2.1.1 前端交互到后端处理

**前端发起请求流程** (`frontend/javascript/ui.js`)：
```javascript
// 用户点击"Queue Prompt"时的完整流程
class PromptQueue {
    async queuePrompt(prompt, clientId) {
        // 1. 序列化工作流数据
        const serialized = this._serializePrompt(prompt);
        
        // 2. 验证工作流结构
        if (!this._validatePrompt(serialized)) {
            throw new Error("工作流验证失败");
        }
        
        // 3. 创建执行请求
        const request = {
            type: "execution",
            prompt: serialized,
            client_id: clientId,
            extra_data: {
                timestamp: Date.now(),
                workflow_version: "1.0",
                execution_mode: "normal"
            }
        };
        
        // 4. 通过WebSocket发送
        return await this._sendViaWebSocket(request);
    }
    
    _serializePrompt(prompt) {
        // 深度复制并清理数据
        const cloned = JSON.parse(JSON.stringify(prompt));
        
        // 移除前端特定字段
        delete cloned._frontend_metadata;
        delete cloned._ui_state;
        
        // 标准化节点ID
        this._normalizeNodeIds(cloned);
        
        return cloned;
    }
    
    _sendViaWebSocket(request) {
        return new Promise((resolve, reject) => {
            const ws = this._getWebSocket();
            
            // 设置超时
            const timeout = setTimeout(() => {
                reject(new Error("WebSocket响应超时"));
            }, 30000);
            
            // 发送请求
            ws.send(JSON.stringify(request));
            
            // 监听响应
            ws.onmessage = (event) => {
                const response = JSON.parse(event.data);
                
                if (response.type === "executing" && response.data.node === null) {
                    // 执行完成
                    clearTimeout(timeout);
                    resolve(response.data);
                } else if (response.type === "status") {
                    // 状态更新
                    this._handleStatusUpdate(response.data);
                } else if (response.type === "execution_error") {
                    // 执行错误
                    clearTimeout(timeout);
                    reject(new Error(response.data.message));
                }
            };
        });
    }
}
```

**WebSocket通信协议**：
```python
# comfy/server.py - WebSocket消息处理
class WebSocketHandler:
    """WebSocket消息处理器"""
    
    async def handle_message(self, websocket, message):
        """处理WebSocket消息"""
        
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "execution":
                # 执行工作流
                await self._handle_execution(websocket, data)
            elif message_type == "interrupt":
                # 中断执行
                await self._handle_interrupt(websocket, data)
            elif message_type == "ping":
                # 心跳检测
                await self._handle_ping(websocket, data)
            else:
                # 未知消息类型
                await self._send_error(websocket, f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "JSON解析失败")
        except Exception as e:
            await self._send_error(websocket, f"处理消息失败: {str(e)}")
    
    async def _handle_execution(self, websocket, data):
        """处理执行请求"""
        
        # 验证客户端权限
        client_id = data.get("client_id")
        if not self._validate_client(client_id):
            await self._send_error(websocket, "客户端验证失败")
            return
        
        # 解析工作流
        prompt = data.get("prompt", {})
        
        try:
            # 创建工作流执行器
            executor = PromptExecutor()
            
            # 注册进度回调
            def progress_callback(progress_data):
                asyncio.create_task(
                    self._send_progress(websocket, progress_data)
                )
            
            executor.set_progress_callback(progress_callback)
            
            # 执行工作流
            result = await executor.execute_async(prompt)
            
            # 发送完成通知
            await self._send_execution_complete(websocket, result)
            
        except Exception as e:
            # 发送错误信息
            await self._send_execution_error(websocket, str(e))
```

#### 2.1.2 工作流解析和验证

**工作流解析器** (`comfy/execution.py`)：
```python
class PromptParser:
    """工作流解析器"""
    
    def parse(self, prompt_data: Dict) -> ParsedWorkflow:
        """解析工作流数据"""
        
        parsed = ParsedWorkflow()
        
        # 1. 提取节点信息
        for node_id, node_data in prompt_data.items():
            if node_id == "last_node":
                # 特殊字段，记录最后输出的节点
                parsed.last_node = node_data
                continue
            
            # 解析节点
            node = self._parse_node(node_id, node_data)
            parsed.nodes[node_id] = node
        
        # 2. 构建依赖关系
        parsed.dependencies = self._build_dependencies(parsed.nodes)
        
        # 3. 验证工作流
        validation_result = self._validate_workflow(parsed)
        if not validation_result["valid"]:
            raise ValueError(f"工作流验证失败: {validation_result['errors']}")
        
        return parsed
    
    def _parse_node(self, node_id: str, node_data: Dict) -> NodeInfo:
        """解析单个节点"""
        
        class_type = node_data.get("class_type")
        inputs = node_data.get("inputs", {})
        
        # 获取节点类
        if class_type not in NODE_CLASS_MAPPINGS:
            raise ValueError(f"未知节点类型: {class_type}")
        
        node_class = NODE_CLASS_MAPPINGS[class_type]
        
        # 创建节点信息
        return NodeInfo(
            id=node_id,
            class_type=class_type,
            node_class=node_class,
            inputs=inputs,
            metadata={
                "position": node_data.get("_meta", {}).get("title", node_id),
                "version": node_data.get("_meta", {}).get("version", "1.0")
            }
        )
    
    def _build_dependencies(self, nodes: Dict[str, NodeInfo]) -> DependencyGraph:
        """构建依赖关系图"""
        
        graph = DependencyGraph()
        
        for node_id, node_info in nodes.items():
            # 分析输入依赖
            for input_name, input_value in node_info.inputs.items():
                if isinstance(input_value, list) and len(input_value) == 2:
                    # 格式: [source_node_id, output_index]
                    source_node = input_value[0]
                    output_index = input_value[1]
                    
                    if source_node in nodes:
                        # 添加依赖边
                        graph.add_edge(
                            from_node=source_node,
                            to_node=node_id,
                            from_socket=output_index,
                            to_socket=input_name
                        )
        
        return graph
    
    def _validate_workflow(self, workflow: ParsedWorkflow) -> Dict[str, Any]:
        """验证工作流"""
        
        errors = []
        warnings = []
        
        # 1. 检查节点类型
        for node_id, node_info in workflow.nodes.items():
            if not hasattr(node_info.node_class, 'INPUT_TYPES'):
                errors.append(f"节点 {node_id} 缺少 INPUT_TYPES 定义")
        
        # 2. 检查循环依赖
        cycles = workflow.dependencies.detect_cycles()
        if cycles:
            errors.append(f"检测到循环依赖: {cycles}")
        
        # 3. 检查数据流完整性
        for node_id, node_info in workflow.nodes.items():
            required_inputs = node_info.node_class.INPUT_TYPES().get("required", {})
            
            for input_name in required_inputs:
                if input_name not in node_info.inputs:
                    # 检查是否有默认值
                    if "default" not in required_inputs[input_name]:
                        errors.append(f"节点 {node_id} 缺少必需输入: {input_name}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
```

#### 2.1.3 节点执行调度流程

**执行调度器**：
```python
class ExecutionScheduler:
    """执行调度器"""
    
    def __init__(self, executor: PromptExecutor):
        self.executor = executor
        self.task_queue = asyncio.Queue()
        self.worker_tasks = []
        self.max_workers = 4  # 最大并发数
    
    async def schedule_execution(self, workflow: ParsedWorkflow) -> Dict[str, Any]:
        """调度工作流执行"""
        
        # 1. 计算执行顺序
        execution_order = self.executor.calculate_execution_order(workflow)
        
        # 2. 创建执行任务
        tasks = []
        for node_id in execution_order:
            task = ExecutionTask(
                node_id=node_id,
                node_info=workflow.nodes[node_id],
                dependencies=workflow.dependencies.get_dependencies(node_id)
            )
            tasks.append(task)
        
        # 3. 启动工作线程
        await self._start_workers(tasks)
        
        # 4. 等待所有任务完成
        results = await self._wait_for_completion()
        
        return results
    
    async def _start_workers(self, tasks: List[ExecutionTask]):
        """启动工作线程"""
        
        # 将任务加入队列
        for task in tasks:
            await self.task_queue.put(task)
        
        # 创建工作线程
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.append(worker_task)
    
    async def _worker_loop(self, worker_name: str):
        """工作线程循环"""
        
        print(f"{worker_name}: 启动")
        
        while True:
            try:
                # 获取任务
                task = await self.task_queue.get()
                
                # 检查任务是否可执行（依赖是否满足）
                if not self._check_dependencies(task):
                    # 依赖未满足，放回队列
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.1)  # 短暂等待
                    continue
                
                # 执行任务
                print(f"{worker_name}: 执行节点 {task.node_id}")
                
                try:
                    result = await self.executor.execute_node(task.node_info)
                    task.set_result(result)
                except Exception as e:
                    task.set_error(e)
                
                # 标记任务完成
                self.task_queue.task_done()
                
                # 通知依赖此节点的任务
                self._notify_dependents(task.node_id)
                
            except asyncio.CancelledError:
                # 工作线程被取消
                break
            except Exception as e:
                print(f"{worker_name}: 错误 - {e}")
    
    def _check_dependencies(self, task: ExecutionTask) -> bool:
        """检查任务依赖是否满足"""
        
        for dep_node_id in task.dependencies:
            dep_task = self._get_task(dep_node_id)
            if dep_task is None or not dep_task.is_completed():
                return False
        
        return True
    
    def _notify_dependents(self, node_id: str):
        """通知依赖此节点的任务"""
        
        # 找到所有依赖此节点的任务
        for task in self._get_all_tasks():
            if node_id in task.dependencies:
                # 检查该任务是否现在可以执行
                if self._check_dependencies(task):
                    # 可以执行，重新加入队列前端
                    asyncio.create_task(self._requeue_task_priority(task))
    
    async def _wait_for_completion(self) -> Dict[str, Any]:
        """等待所有任务完成"""
        
        # 等待队列清空
        await self.task_queue.join()
        
        # 停止工作线程
        for worker in self.worker_tasks:
            worker.cancel()
        
        # 等待工作线程结束
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # 收集结果
        results = {}
        for task in self._get_all_tasks():
            if task.is_completed():
                results[task.node_id] = task.get_result()
            else:
                results[task.node_id] = {"error": str(task.get_error())}
        
        return results
```

### 2.2 节点执行生命周期

每个节点的执行都经过严格的生命周期管理，确保正确性和性能。

#### 2.2.1 输入验证和类型转换

**输入处理器**：
```python
class InputProcessor:
    """输入处理器"""
    
    def process_inputs(self, node_class, raw_inputs: Dict) -> Dict:
        """处理节点输入"""
        
        # 1. 获取输入类型定义
        input_types = node_class.INPUT_TYPES()
        required_inputs = input_types.get("required", {})
        optional_inputs = input_types.get("optional", {})
        
        processed = {}
        
        # 2. 处理必需输入
        for input_name, type_def in required_inputs.items():
            if input_name not in raw_inputs:
                # 检查是否有默认值
                if isinstance(type_def, dict) and "default" in type_def:
                    processed[input_name] = type_def["default"]
                else:
                    raise ValueError(f"缺少必需输入: {input_name}")
            else:
                # 类型转换
                processed[input_name] = self._convert_input(
                    raw_inputs[input_name], 
                    type_def
                )
        
        # 3. 处理可选输入
        for input_name, type_def in optional_inputs.items():
            if input_name in raw_inputs:
                processed[input_name] = self._convert_input(
                    raw_inputs[input_name],
                    type_def
                )
            elif isinstance(type_def, dict) and "default" in type_def:
                processed[input_name] = type_def["default"]
        
        return processed
    
    def _convert_input(self, value, type_def):
        """类型转换"""
        
        if isinstance(type_def, tuple):
            # 类型元组，尝试每个类型
            for t in type_def:
                try:
                    return self._convert_to_type(value, t)
                except (ValueError, TypeError):
                    continue
            raise ValueError(f"无法将值转换为任何指定类型: {type_def}")
        
        return self._convert_to_type(value, type_def)
    
    def _convert_to_type(self, value, type_spec):
        """转换为特定类型"""
        
        if isinstance(type_spec, str):
            # 类型字符串，如 "IMAGE", "LATENT"
            return self._convert_by_type_name(value, type_spec)
        elif isinstance(type_spec, dict):
            # 类型定义字典
            actual_type = type_spec.get("type", type_spec)
            return self._convert_to_type(value, actual_type)
        else:
            # 未知类型，原样返回
            return value
    
    def _convert_by_type_name(self, value, type_name: str):
        """根据类型名称转换"""
        
        if type_name == "IMAGE":
            # 图像类型：4D张量 [batch, channels, height, width]
            if isinstance(value, torch.Tensor):
                if value.dim() == 3:
                    # 3D -> 4D
                    return value.unsqueeze(0)
                elif value.dim() == 4:
                    return value
                else:
                    raise ValueError(f"图像张量维度错误: {value.dim()}D")
            else:
                # 尝试转换为张量
                return torch.tensor(value).unsqueeze(0)
        
        elif type_name == "LATENT":
            # 潜在表示：字典包含"samples"键
            if isinstance(value, dict) and "samples" in value:
                return value
            elif isinstance(value, torch.Tensor):
                return {"samples": value}
            else:
                raise ValueError("LATENT类型必须是字典或张量")
        
        elif type_name == "CONDITIONING":
            # 条件向量
            if isinstance(value, torch.Tensor):
                return value
            elif isinstance(value, list):
                return torch.stack(value)
            else:
                raise ValueError("CONDITIONING类型必须是张量或列表")
        
        elif type_name == "MASK":
