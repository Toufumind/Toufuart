# Python异步编程高级概念
## 2026-03-12 05:10 AM

## 技术学习进展：Python asyncio高级模式

### 1. 异步上下文管理器 (Async Context Managers)

#### 传统上下文管理器 vs 异步上下文管理器
```python
# 同步版本
class SyncResource:
    def __enter__(self):
        print("同步资源初始化")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("同步资源清理")

# 异步版本
class AsyncResource:
    async def __aenter__(self):
        print("异步资源初始化")
        await asyncio.sleep(0.1)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("异步资源清理")
        await asyncio.sleep(0.1)

# 使用方式
async with AsyncResource() as resource:
    await resource.do_something()
```

### 2. 异步迭代器 (Async Iterators)

#### 实现异步迭代协议
```python
class AsyncDataStream:
    def __init__(self, data):
        self.data = data
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.data):
            raise StopAsyncIteration
        
        item = self.data[self.index]
        self.index += 1
        
        # 模拟异步操作
        await asyncio.sleep(0.01)
        return item

# 使用异步for循环
async for item in AsyncDataStream([1, 2, 3, 4, 5]):
    print(f"处理项目: {item}")
```

### 3. 异步生成器 (Async Generators)

#### 使用async def和yield
```python
async def async_generator(limit):
    """异步生成器示例"""
    for i in range(limit):
        # 模拟异步操作
        await asyncio.sleep(0.1)
        yield i * 2

# 使用方式
async def process_async_generator():
    async for value in async_generator(5):
        print(f"生成值: {value}")
```

### 4. 任务组模式 (Task Groups)

#### asyncio.gather的替代方案
```python
import asyncio

async def task_one():
    await asyncio.sleep(1)
    return "任务一完成"

async def task_two():
    await asyncio.sleep(2)
    return "任务二完成"

async def task_three():
    await asyncio.sleep(0.5)
    return "任务三完成"

# 传统方式 - asyncio.gather
async def traditional_way():
    results = await asyncio.gather(
        task_one(),
        task_two(),
        task_three()
    )
    return results

# 现代方式 - asyncio.TaskGroup (Python 3.11+)
async def modern_way():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(task_one())
        task2 = tg.create_task(task_two())
        task3 = tg.create_task(task_three())
    
    return [task1.result(), task2.result(), task3.result()]
```

### 5. 异步队列模式 (Async Queue Patterns)

#### 生产者-消费者模式
```python
import asyncio
from asyncio import Queue

async def producer(queue: Queue, count: int):
    """生产者协程"""
    for i in range(count):
        await asyncio.sleep(0.1)  # 模拟生产时间
        item = f"项目_{i}"
        await queue.put(item)
        print(f"生产: {item}")
    
    # 发送结束信号
    await queue.put(None)

async def consumer(queue: Queue, consumer_id: int):
    """消费者协程"""
    while True:
        item = await queue.get()
        
        if item is None:
            # 将结束信号放回队列，让其他消费者也能看到
            await queue.put(None)
            break
        
        await asyncio.sleep(0.2)  # 模拟处理时间
        print(f"消费者{consumer_id} 处理: {item}")
        queue.task_done()

async def run_producer_consumer():
    queue = Queue(maxsize=10)
    
    # 创建生产者和消费者任务
    producer_task = asyncio.create_task(producer(queue, 10))
    consumer_tasks = [
        asyncio.create_task(consumer(queue, i))
        for i in range(3)  # 3个消费者
    ]
    
    # 等待生产者完成
    await producer_task
    
    # 等待所有项目被处理
    await queue.join()
    
    # 取消消费者任务
    for task in consumer_tasks:
        task.cancel()
```

### 6. 异步锁和信号量

#### 异步互斥锁
```python
import asyncio

class AsyncCounter:
    def __init__(self):
        self.value = 0
        self.lock = asyncio.Lock()
    
    async def increment(self):
        async with self.lock:
            # 临界区
            current = self.value
            await asyncio.sleep(0.01)  # 模拟异步操作
            self.value = current + 1
            return self.value

async def test_async_lock():
    counter = AsyncCounter()
    
    # 并发增加计数器
    tasks = [counter.increment() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    
    print(f"最终值: {counter.value}")
    print(f"所有结果: {results[:5]}...")  # 显示前5个结果
```

#### 异步信号量
```python
async def limited_resource(semaphore: asyncio.Semaphore, task_id: int):
    """限制并发访问的资源"""
    async with semaphore:
        print(f"任务{task_id} 获取资源")
        await asyncio.sleep(1)  # 模拟资源使用
        print(f"任务{task_id} 释放资源")
        return f"任务{task_id}完成"

async def test_semaphore():
    # 限制最多3个并发
    semaphore = asyncio.Semaphore(3)
    
    # 创建10个任务
    tasks = [
        limited_resource(semaphore, i)
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    print(f"所有任务完成: {results}")
```

### 7. 异步超时和取消

#### 超时控制
```python
async def slow_operation():
    """模拟慢操作"""
    await asyncio.sleep(5)
    return "操作完成"

async def with_timeout():
    try:
        # 设置3秒超时
        result = await asyncio.wait_for(slow_operation(), timeout=3)
        return result
    except asyncio.TimeoutError:
        return "操作超时"

#### 可取消任务
async def cancellable_operation():
    """可取消的操作"""
    try:
        await asyncio.sleep(10)  # 长时间运行
        return "操作完成"
    except asyncio.CancelledError:
        print("操作被取消")
        raise  # 重新抛出异常

async def test_cancellation():
    task = asyncio.create_task(cancellable_operation())
    
    # 等待2秒后取消
    await asyncio.sleep(2)
    task.cancel()
    
    try:
        await task
    except asyncio.CancelledError:
        print("任务已成功取消")
```

### 8. 异步错误处理模式

#### 错误聚合
```python
async def task_with_possible_error(task_id: int):
    """可能失败的任务"""
    await asyncio.sleep(0.1)
    
    if task_id % 3 == 0:
        raise ValueError(f"任务{task_id}故意失败")
    
    return f"任务{task_id}成功"

async def gather_with_exceptions():
    """收集所有结果，包括异常"""
    tasks = [
        asyncio.create_task(task_with_possible_error(i))
        for i in range(10)
    ]
    
    results = []
    for task in asyncio.as_completed(tasks):
        try:
            result = await task
            results.append(("成功", result))
        except Exception as e:
            results.append(("失败", str(e)))
    
    return results
```

### 9. 性能优化技巧

#### 1. 避免阻塞操作
```python
# 错误：在异步函数中使用阻塞调用
async def bad_example():
    import time
    time.sleep(1)  # 阻塞整个事件循环！
    
# 正确：使用异步版本
async def good_example():
    await asyncio.sleep(1)  # 非阻塞
```

#### 2. 批量处理
```python
async def process_batch(items, batch_size=10):
    """批量处理项目"""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # 并行处理批次
        tasks = [process_item(item) for item in batch]
        results = await asyncio.gather(*tasks)
        
        yield results
```

#### 3. 连接池管理
```python
from aiohttp import ClientSession

async def fetch_with_session_pool(urls):
    """使用会话池高效获取URL"""
    async with ClientSession() as session:
        tasks = [
            fetch_url(session, url)
            for url in urls
        ]
        return await asyncio.gather(*tasks)

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()
```

### 10. 学习收获总结

1. **异步上下文管理器**: 使用`__aenter__`和`__aexit__`管理异步资源
2. **异步迭代器**: 实现`__aiter__`和`__anext__`支持异步for循环
3. **任务组模式**: 使用`asyncio.TaskGroup`更好地管理相关任务
4. **队列模式**: 实现高效的生产者-消费者模式
5. **并发控制**: 使用锁和信号量管理共享资源
6. **错误处理**: 正确处理异步环境中的异常
7. **性能优化**: 避免阻塞，使用批量处理和连接池

### 11. 实践建议

1. **从简单开始**: 先掌握基本`async/await`语法
2. **逐步深入**: 按需学习高级模式
3. **测试驱动**: 为异步代码编写充分的测试
4. **监控性能**: 使用`asyncio`的调试工具
5. **错误处理**: 设计健壮的错误处理策略

### 12. 常见陷阱

1. **忘记await**: 调用异步函数时忘记使用await
2. **阻塞事件循环**: 在异步代码中使用阻塞操作
3. **资源泄漏**: 未正确关闭异步资源
4. **死锁**: 不当使用锁导致死锁
5. **取消传播**: 未正确处理任务取消

通过掌握这些高级概念，可以编写更高效、更健壮的异步Python应用程序。