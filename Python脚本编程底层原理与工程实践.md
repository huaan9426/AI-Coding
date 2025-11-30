# Python 脚本编程底层原理与工程实践

> **从 Java 转 Python 的硬核指南** - 深入底层、工程化实践、DevOps 必备

---

## 📋 目录

### 第一部分：底层原理与执行机制
1. [Python 解释器与字节码](#1-python-解释器与字节码)
2. [内存管理与垃圾回收](#2-内存管理与垃圾回收)
3. [变量与对象模型](#3-变量与对象模型)
4. [可变对象 vs 不可变对象](#4-可变对象-vs-不可变对象)

### 第二部分：高级语言特性
5. [装饰器深度解析](#5-装饰器深度解析)
6. [上下文管理器](#6-上下文管理器)
7. [生成器与迭代器](#7-生成器与迭代器)
8. [协程与异步编程](#8-协程与异步编程)

### 第三部分：工程化实践
9. [异常处理最佳实践](#9-异常处理最佳实践)
10. [日志系统设计](#10-日志系统设计)
11. [配置管理与环境变量](#11-配置管理与环境变量)
12. [单元测试与代码质量](#12-单元测试与代码质量)

### 第四部分：DevOps 脚本编程
13. [系统调用与子进程管理](#13-系统调用与子进程管理)
14. [文件系统操作](#14-文件系统操作)
15. [网络编程基础](#15-网络编程基础)
16. [多线程与多进程](#16-多线程与多进程)

### 第五部分：性能优化与调试
17. [性能分析与优化](#17-性能分析与优化)
18. [调试技巧](#18-调试技巧)
19. [常见陷阱与最佳实践](#19-常见陷阱与最佳实践)

---

## 第一部分：底层原理与执行机制

---

## 1. Python 解释器与字节码

### 1.1 执行流程（vs Java）

#### Java 执行流程
```
.java 源文件 → javac 编译 → .class 字节码 → JVM 执行
```

#### Python 执行流程
```
.py 源文件 → CPython 编译 → .pyc 字节码 → 解释器执行
```

**关键区别**：
- Java 是**编译型**（提前编译成字节码）
- Python 是**解释型**（运行时编译 + 解释执行）

### 1.2 查看 Python 字节码

```python
import dis

def add(a, b):
    return a + b

# 查看字节码
dis.dis(add)
```

**输出示例**：
```
  2           0 LOAD_FAST                0 (a)
              2 LOAD_FAST                1 (b)
              4 BINARY_ADD
              6 RETURN_VALUE
```

**解读**：
1. `LOAD_FAST 0` - 加载局部变量 a 到栈顶
2. `LOAD_FAST 1` - 加载局部变量 b 到栈顶
3. `BINARY_ADD` - 弹出两个值相加，结果压栈
4. `RETURN_VALUE` - 返回栈顶值

### 1.3 .pyc 文件（字节码缓存）

```python
# 运行时自动生成 __pycache__/*.pyc
# 加快下次启动速度（无需重新编译）

# 主动编译
import py_compile
py_compile.compile('script.py')

# 编译整个目录
import compileall
compileall.compile_dir('.', force=True)
```

**生产环境技巧**：
- ✅ Docker 镜像构建时预编译 → 减少启动时间
- ✅ 部署时删除 .py 文件，仅保留 .pyc → 代码保护

### 1.4 CPython vs PyPy vs Jython

| 解释器 | 语言实现 | 优势 | 劣势 |
|--------|---------|------|------|
| **CPython** | C 语言 | 默认、兼容性强 | 较慢、GIL 锁 |
| **PyPy** | Python + JIT | **快 5-10 倍** | 部分库不兼容 |
| **Jython** | Java | 调用 Java 库 | 慢、Python 3 支持差 |

**特斯拉项目选择**：
- 数据处理脚本 → **PyPy**（快）
- 深度学习 → **CPython**（库兼容性）
- 集成 Java 系统 → **Jython**

---

## 2. 内存管理与垃圾回收

### 2.1 Python 内存管理机制

#### 对象的内存结构
```python
# 每个 Python 对象都包含：
# 1. 引用计数（ref_count）
# 2. 类型指针（type_ptr）
# 3. 实际数据（value）

import sys

x = 42
print(sys.getsizeof(x))  # 28 字节（int 对象）

y = "hello"
print(sys.getsizeof(y))  # 54 字节（str 对象 + 元数据）
```

### 2.2 引用计数（Reference Counting）

```python
import sys

x = [1, 2, 3]
print(sys.getrefcount(x))  # 2（1 个变量 + 1 个临时引用）

y = x  # 引用计数 +1
print(sys.getrefcount(x))  # 3

del y  # 引用计数 -1
print(sys.getrefcount(x))  # 2
```

**优点**：
- ✅ 即时回收（引用计数为 0 立即释放）

**缺点**：
- ❌ 循环引用无法回收

### 2.3 循环引用与垃圾回收

```python
# 循环引用示例
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

a = Node(1)
b = Node(2)
a.next = b
b.next = a  # 循环引用：a → b → a

# 即使删除变量，内存也不会立即释放
del a
del b
```

**解决方案：分代垃圾回收**
```python
import gc

# 手动触发垃圾回收
gc.collect()

# 查看垃圾回收统计
print(gc.get_stats())

# 禁用垃圾回收（性能优化）
gc.disable()
# ... 执行密集计算 ...
gc.enable()
```

### 2.4 内存泄漏排查

```python
import tracemalloc

# 开始追踪内存分配
tracemalloc.start()

# 执行可能泄漏的代码
data = []
for i in range(1000000):
    data.append([i] * 100)

# 查看内存快照
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:3]:
    print(stat)
```

**生产环境技巧**：
```python
# 装饰器自动追踪内存
import functools
import tracemalloc

def track_memory(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"{func.__name__}: 当前 {current/1024/1024:.2f}MB, 峰值 {peak/1024/1024:.2f}MB")
        return result
    return wrapper

@track_memory
def process_data():
    data = [i for i in range(1000000)]
    return len(data)
```

---

## 3. 变量与对象模型

### 3.1 Python 变量的本质（vs Java）

#### Java 变量
```java
// Java: 变量是"容器"（存储值）
int x = 5;      // x 直接存储 5
String s = "hello";  // s 存储对象引用
```

#### Python 变量
```python
# Python: 变量是"标签"（指向对象）
x = 5       # x 是指向整数对象 5 的标签
y = x       # y 也指向同一个对象
z = 5       # z 也指向同一个对象（整数缓存）

print(id(x), id(y), id(z))  # 三个 ID 相同！
```

### 3.2 对象身份、类型、值

```python
x = [1, 2, 3]
y = [1, 2, 3]

# 1. 身份（identity）- 内存地址
print(id(x))        # 4312345678
print(id(y))        # 4312345789（不同对象）
print(x is y)       # False

# 2. 类型（type）
print(type(x))      # <class 'list'>

# 3. 值（value）
print(x == y)       # True（值相同）
```

**判等规则**：
```python
# is: 判断身份（同一对象）
# ==: 判断值（内容相同）

a = [1, 2]
b = [1, 2]
c = a

print(a == b)  # True（值相同）
print(a is b)  # False（不同对象）
print(a is c)  # True（同一对象）
```

### 3.3 整数缓存机制

```python
# Python 缓存小整数 [-5, 256]
a = 100
b = 100
print(a is b)  # True（同一对象）

c = 1000
d = 1000
print(c is d)  # False（不同对象）
```

**原因**：小整数使用频繁，预先创建避免重复分配。

### 3.4 字符串驻留（String Interning）

```python
# 字符串驻留：相同字符串共享内存
s1 = "hello"
s2 = "hello"
print(s1 is s2)  # True

# 但动态创建的字符串不驻留
s3 = "hel" + "lo"
print(s1 is s3)  # False（CPython 实现细节）

# 强制驻留
import sys
s4 = sys.intern("hello")
print(s1 is s4)  # True
```

---

## 4. 可变对象 vs 不可变对象

### 4.1 核心概念

| 不可变对象 | 可变对象 |
|-----------|---------|
| int, float, str | list, dict, set |
| tuple | 自定义类（默认） |
| frozenset | bytearray |

### 4.2 不可变对象的陷阱

```python
# 字符串拼接的性能陷阱
# ❌ 低效：每次拼接创建新对象
result = ""
for i in range(10000):
    result += str(i)  # 创建 10000 个临时字符串对象

# ✅ 高效：先存列表，最后一次拼接
parts = []
for i in range(10000):
    parts.append(str(i))
result = "".join(parts)  # 仅创建 1 个最终字符串

# 性能对比
import timeit
print(timeit.timeit('s = ""; [s := s + str(i) for i in range(1000)]', number=100))  # ~0.5s
print(timeit.timeit('s = []; [s.append(str(i)) for i in range(1000)]; "".join(s)', number=100))  # ~0.02s
```

### 4.3 可变对象的陷阱

#### 陷阱 1：默认参数
```python
# ❌ 错误：默认参数是可变对象
def add_item(item, items=[]):  # 危险！
    items.append(item)
    return items

print(add_item(1))  # [1]
print(add_item(2))  # [1, 2]（预期是 [2]）
print(add_item(3))  # [1, 2, 3]（预期是 [3]）

# ✅ 正确
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

#### 陷阱 2：浅拷贝 vs 深拷贝
```python
import copy

# 原始列表
original = [[1, 2], [3, 4]]

# 浅拷贝（仅复制外层）
shallow = copy.copy(original)
shallow[0][0] = 999
print(original)  # [[999, 2], [3, 4]]（被修改！）

# 深拷贝（递归复制所有层）
deep = copy.deepcopy(original)
deep[0][0] = 777
print(original)  # [[999, 2], [3, 4]]（未改变）
```

### 4.4 生产环境最佳实践

```python
# 规则 1：函数参数不使用可变默认值
def process_data(data, config=None):
    if config is None:
        config = {"timeout": 30}
    # ...

# 规则 2：返回副本而非原对象
class DataProcessor:
    def __init__(self):
        self._data = []

    def get_data(self):
        # ✅ 返回副本，防止外部修改
        return self._data.copy()

# 规则 3：使用不可变数据结构
from typing import Tuple

def get_config() -> Tuple[str, int]:
    # 返回 tuple 而非 list
    return ("localhost", 8080)
```

---

## 第二部分：高级语言特性

---

## 5. 装饰器深度解析

### 5.1 装饰器本质

**装饰器 = 高阶函数（接收函数，返回函数）**

```python
# 基础装饰器
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function")
        result = func(*args, **kwargs)
        print("After function")
        return result
    return wrapper

@my_decorator
def greet(name):
    print(f"Hello, {name}")

# 等价于：greet = my_decorator(greet)
```

### 5.2 保留原函数元数据

```python
import functools

def my_decorator(func):
    @functools.wraps(func)  # ← 保留原函数的 __name__, __doc__ 等
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def greet(name):
    """Say hello"""
    print(f"Hello, {name}")

print(greet.__name__)  # "greet"（不加 @wraps 会是 "wrapper"）
print(greet.__doc__)   # "Say hello"
```

### 5.3 带参数的装饰器

```python
def repeat(times):
    """重复执行装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def say_hello():
    print("Hello!")

# say_hello()  # 打印 3 次 "Hello!"
```

### 5.4 DevOps 常用装饰器

#### 5.4.1 重试装饰器
```python
import time
import functools

def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
    """自动重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    print(f"❌ 失败（第 {attempt} 次），{delay}s 后重试...")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3, delay=2, exceptions=(ConnectionError,))
def fetch_data(url):
    import requests
    response = requests.get(url, timeout=5)
    return response.json()
```

#### 5.4.2 性能计时装饰器
```python
import time
import functools

def timer(func):
    """函数执行时间统计"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱️  {func.__name__} 耗时: {elapsed:.3f}s")
        return result
    return wrapper

@timer
def process_data():
    time.sleep(2)
    return "done"
```

#### 5.4.3 日志装饰器
```python
import logging
import functools

def log_call(logger=None):
    """记录函数调用日志"""
    if logger is None:
        logger = logging.getLogger(__name__)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"调用 {func.__name__}，参数: args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"{func.__name__} 返回: {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} 异常: {e}")
                raise
        return wrapper
    return decorator

@log_call()
def divide(a, b):
    return a / b
```

#### 5.4.4 类装饰器（单例模式）
```python
def singleton(cls):
    """单例模式装饰器"""
    instances = {}
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class Config:
    def __init__(self):
        self.settings = {"timeout": 30}

config1 = Config()
config2 = Config()
print(config1 is config2)  # True（同一实例）
```

---

## 6. 上下文管理器

### 6.1 with 语句的原理

```python
# 传统方式（易出错）
file = open("data.txt", "r")
try:
    content = file.read()
finally:
    file.close()  # 确保关闭

# with 语句（自动管理）
with open("data.txt", "r") as file:
    content = file.read()
# 自动调用 file.close()
```

### 6.2 自定义上下文管理器

#### 方法 1：类实现
```python
class Timer:
    def __enter__(self):
        self.start = time.time()
        print("⏱️  开始计时")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start
        print(f"⏱️  结束计时: {elapsed:.3f}s")
        # 返回 False 表示异常继续传播
        # 返回 True 表示压制异常
        return False

with Timer():
    time.sleep(2)
    print("执行任务")
```

#### 方法 2：@contextmanager 装饰器
```python
from contextlib import contextmanager

@contextmanager
def timer():
    start = time.time()
    print("⏱️  开始计时")
    try:
        yield  # 让出控制权给 with 块
    finally:
        elapsed = time.time() - start
        print(f"⏱️  结束计时: {elapsed:.3f}s")

with timer():
    time.sleep(2)
```

### 6.3 DevOps 常用上下文管理器

#### 6.3.1 临时切换目录
```python
import os
from contextlib import contextmanager

@contextmanager
def cd(path):
    """临时切换工作目录"""
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)

# 使用
with cd("/tmp"):
    print(os.getcwd())  # /tmp
    # 执行操作
print(os.getcwd())  # 恢复原目录
```

#### 6.3.2 临时修改环境变量
```python
@contextmanager
def set_env(**kwargs):
    """临时设置环境变量"""
    old_env = {}
    for key, value in kwargs.items():
        old_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

with set_env(DEBUG="1", LOG_LEVEL="DEBUG"):
    print(os.environ["DEBUG"])  # "1"
print(os.environ.get("DEBUG"))  # None（已恢复）
```

#### 6.3.3 数据库事务管理
```python
class DatabaseConnection:
    def __enter__(self):
        self.conn = self.connect()
        self.conn.begin_transaction()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()  # 成功则提交
        else:
            self.conn.rollback()  # 异常则回滚
        self.conn.close()
        return False

with DatabaseConnection() as conn:
    conn.execute("INSERT ...")
    conn.execute("UPDATE ...")
# 自动提交或回滚
```

---

## 7. 生成器与迭代器

### 7.1 迭代器协议

```python
# 手动实现迭代器
class CountDown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self  # 返回自身

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

for num in CountDown(5):
    print(num)  # 5, 4, 3, 2, 1
```

### 7.2 生成器（简化版迭代器）

```python
# 使用 yield 关键字
def countdown(start):
    while start > 0:
        yield start  # 暂停并返回值
        start -= 1

for num in countdown(5):
    print(num)
```

### 7.3 生成器的内存优势

```python
# ❌ 低效：一次性加载到内存
def read_large_file_bad(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()  # 一次性读取全部
    return lines

# ✅ 高效：按需生成（惰性求值）
def read_large_file_good(file_path):
    with open(file_path, "r") as f:
        for line in f:  # 逐行读取
            yield line.strip()

# 处理 10GB 文件也不会占用大量内存
for line in read_large_file_good("huge.log"):
    if "ERROR" in line:
        print(line)
```

### 7.4 生成器表达式

```python
# 列表推导式（一次性创建）
squares_list = [x**2 for x in range(1000000)]  # 占用大量内存

# 生成器表达式（按需生成）
squares_gen = (x**2 for x in range(1000000))   # 几乎不占内存

# 内存对比
import sys
print(sys.getsizeof(squares_list))  # 8448728 字节
print(sys.getsizeof(squares_gen))   # 120 字节
```

### 7.5 DevOps 应用：日志文件处理

```python
def parse_nginx_log(file_path):
    """解析 nginx 日志（生成器）"""
    with open(file_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 9:
                yield {
                    "ip": parts[0],
                    "method": parts[5].strip('"'),
                    "path": parts[6],
                    "status": parts[8],
                }

def filter_errors(logs):
    """筛选错误日志（生成器链）"""
    for log in logs:
        if log["status"].startswith("5"):
            yield log

def group_by_ip(logs):
    """按 IP 分组统计（生成器消费）"""
    from collections import Counter
    ips = (log["ip"] for log in logs)
    return Counter(ips).most_common(10)

# 流式处理：文件 → 解析 → 筛选 → 统计
logs = parse_nginx_log("/var/log/nginx/access.log")
errors = filter_errors(logs)
top_ips = group_by_ip(errors)
print(top_ips)
```

---

## 8. 协程与异步编程

### 8.1 同步 vs 异步

```python
import time

# 同步（阻塞）
def download_sync(url):
    print(f"开始下载 {url}")
    time.sleep(2)  # 模拟网络请求
    print(f"完成下载 {url}")
    return f"Data from {url}"

start = time.time()
download_sync("url1")
download_sync("url2")
download_sync("url3")
print(f"总耗时: {time.time() - start:.1f}s")  # ~6s

# 异步（非阻塞）
import asyncio

async def download_async(url):
    print(f"开始下载 {url}")
    await asyncio.sleep(2)  # 模拟异步网络请求
    print(f"完成下载 {url}")
    return f"Data from {url}"

async def main():
    start = time.time()
    tasks = [
        download_async("url1"),
        download_async("url2"),
        download_async("url3"),
    ]
    await asyncio.gather(*tasks)  # 并发执行
    print(f"总耗时: {time.time() - start:.1f}s")  # ~2s

asyncio.run(main())
```

### 8.2 async/await 关键字

```python
import asyncio
import aiohttp  # 异步 HTTP 库

async def fetch_url(session, url):
    """异步获取 URL 内容"""
    async with session.get(url) as response:
        return await response.text()

async def fetch_multiple_urls(urls):
    """并发获取多个 URL"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# 运行
urls = ["https://example.com", "https://github.com", "https://python.org"]
results = asyncio.run(fetch_multiple_urls(urls))
```

### 8.3 异步文件 I/O

```python
import aiofiles

async def read_file_async(file_path):
    """异步读取文件"""
    async with aiofiles.open(file_path, "r") as f:
        content = await f.read()
    return content

async def write_file_async(file_path, content):
    """异步写入文件"""
    async with aiofiles.open(file_path, "w") as f:
        await f.write(content)

async def process_files():
    """并发处理多个文件"""
    tasks = [
        read_file_async("file1.txt"),
        read_file_async("file2.txt"),
        read_file_async("file3.txt"),
    ]
    contents = await asyncio.gather(*tasks)
    return contents

asyncio.run(process_files())
```

### 8.4 异步任务调度

```python
import asyncio

async def task1():
    await asyncio.sleep(1)
    return "Task 1 done"

async def task2():
    await asyncio.sleep(2)
    return "Task 2 done"

async def main():
    # 方法 1: gather（全部完成后返回）
    results = await asyncio.gather(task1(), task2())
    print(results)  # ['Task 1 done', 'Task 2 done']

    # 方法 2: as_completed（按完成顺序处理）
    for coro in asyncio.as_completed([task1(), task2()]):
        result = await coro
        print(result)  # Task 1 done (1s 后), Task 2 done (2s 后)

    # 方法 3: 超时控制
    try:
        result = await asyncio.wait_for(task2(), timeout=1.0)
    except asyncio.TimeoutError:
        print("超时！")

asyncio.run(main())
```

### 8.5 DevOps 应用：批量 SSH 操作

```python
import asyncio
import asyncssh

async def run_command_on_host(host, command):
    """异步执行 SSH 命令"""
    async with asyncssh.connect(host) as conn:
        result = await conn.run(command)
        return {
            "host": host,
            "stdout": result.stdout,
            "exit_status": result.exit_status,
        }

async def batch_ssh_commands(hosts, command):
    """批量执行 SSH 命令"""
    tasks = [run_command_on_host(host, command) for host in hosts]
    results = await asyncio.gather(*tasks)
    return results

# 并发操作 100 台服务器
hosts = [f"server{i}.example.com" for i in range(100)]
results = asyncio.run(batch_ssh_commands(hosts, "df -h"))
```

---

## 第三部分：工程化实践

---

## 9. 异常处理最佳实践

### 9.1 异常层次结构

```python
BaseException
 ├── SystemExit
 ├── KeyboardInterrupt
 └── Exception
      ├── ValueError
      ├── TypeError
      ├── FileNotFoundError
      ├── ConnectionError
      └── ...
```

### 9.2 精确捕获异常

```python
# ❌ 错误：捕获所有异常
try:
    result = 10 / 0
except:  # 危险！连 KeyboardInterrupt 都捕获
    pass

# ❌ 错误：捕获过于宽泛
try:
    result = 10 / 0
except Exception:  # 捕获所有业务异常
    pass

# ✅ 正确：捕获具体异常
try:
    result = 10 / 0
except ZeroDivisionError:
    print("除数不能为 0")

# ✅ 正确：捕获多个具体异常
try:
    with open("data.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print("文件不存在")
except json.JSONDecodeError:
    print("JSON 格式错误")
```

### 9.3 异常链与上下文

```python
# ❌ 错误：丢失原始异常信息
try:
    data = json.load(open("config.json"))
except Exception:
    raise ValueError("配置文件加载失败")  # 原始异常信息丢失

# ✅ 正确：保留异常链
try:
    data = json.load(open("config.json"))
except Exception as e:
    raise ValueError("配置文件加载失败") from e  # 使用 from 保留原因
```

### 9.4 自定义异常

```python
# 基础异常类
class APIError(Exception):
    """API 基础异常"""
    pass

# 具体异常
class AuthenticationError(APIError):
    """认证失败"""
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class RateLimitError(APIError):
    """速率限制"""
    def __init__(self, retry_after):
        self.retry_after = retry_after
        super().__init__(f"请 {retry_after} 秒后重试")

# 使用
def call_api(token):
    if not token:
        raise AuthenticationError("Token 缺失")
    # ...

try:
    call_api(None)
except AuthenticationError as e:
    print(f"错误码: {e.status_code}, 消息: {e.message}")
```

### 9.5 上下文管理器 + 异常处理

```python
from contextlib import contextmanager

@contextmanager
def safe_transaction(conn):
    """安全事务上下文"""
    try:
        conn.begin()
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"事务回滚: {e}")
        raise
    finally:
        conn.close()

# 使用
with safe_transaction(db_connection) as conn:
    conn.execute("INSERT ...")
    conn.execute("UPDATE ...")
```

### 9.6 生产环境异常处理模式

```python
import logging
import traceback

logger = logging.getLogger(__name__)

def robust_api_call(url, max_retries=3):
    """健壮的 API 调用"""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            logger.warning(f"请求超时（第 {attempt} 次）")
            if attempt == max_retries:
                raise

        except requests.ConnectionError as e:
            logger.error(f"连接失败: {e}")
            if attempt == max_retries:
                raise

        except requests.HTTPError as e:
            if e.response.status_code >= 500:
                # 服务器错误 → 重试
                logger.warning(f"服务器错误 {e.response.status_code}，重试中...")
                if attempt == max_retries:
                    raise
            else:
                # 客户端错误 → 不重试
                logger.error(f"客户端错误: {e}")
                raise

        except Exception as e:
            # 未知异常 → 记录详细堆栈
            logger.error(f"未知异常:\n{traceback.format_exc()}")
            raise

# 全局异常捕获（守护进程）
def main():
    try:
        # 主逻辑
        run_application()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在退出...")
    except Exception:
        logger.critical(f"致命错误:\n{traceback.format_exc()}")
        sys.exit(1)
```

---

## 10. 日志系统设计

### 10.1 日志级别

```python
import logging

# 日志级别（由低到高）
# DEBUG < INFO < WARNING < ERROR < CRITICAL

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug("调试信息")      # 开发环境
logger.info("正常信息")       # 生产环境
logger.warning("警告信息")    # 需要注意
logger.error("错误信息")      # 需要处理
logger.critical("严重错误")   # 系统崩溃
```

### 10.2 结构化日志配置

```python
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
```

### 10.3 JSON 格式日志（生产推荐）

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON 格式日志（便于 ELK 采集）"""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常堆栈
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加自定义字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data, ensure_ascii=False)

# 配置
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 使用（带上下文）
logger.info("用户登录", extra={"request_id": "abc123"})
```

### 10.4 分布式追踪（Request ID）

```python
import uuid
import contextvars

# 线程安全的上下文变量
request_id_var = contextvars.ContextVar("request_id", default=None)

class RequestIDFilter(logging.Filter):
    """自动添加 Request ID"""
    def filter(self, record):
        record.request_id = request_id_var.get() or "N/A"
        return True

# 配置
logger = logging.getLogger(__name__)
logger.addFilter(RequestIDFilter())

# 使用
def handle_request():
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

    logger.info("开始处理请求")  # 自动包含 request_id
    # ... 业务逻辑 ...
    logger.info("请求处理完成")
```

### 10.5 DevOps 日志实践

```python
import logging
from logging.handlers import RotatingFileHandler, SysLogHandler

def setup_production_logging(app_name):
    """生产环境日志配置"""
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)

    # 1. 控制台输出（Docker/K8s 收集）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # 2. 文件滚动（本地备份）
    file_handler = RotatingFileHandler(
        f"/var/log/{app_name}/app.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10,
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # 3. 错误单独文件
    error_handler = RotatingFileHandler(
        f"/var/log/{app_name}/error.log",
        maxBytes=50*1024*1024,
        backupCount=10,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)

    # 4. Syslog（发送到日志服务器）
    syslog_handler = SysLogHandler(address=("logserver", 514))
    syslog_handler.setFormatter(JSONFormatter())
    logger.addHandler(syslog_handler)

    return logger
```

---

## 11. 配置管理与环境变量

### 11.1 环境变量最佳实践

#### 基础用法
```python
import os

# 读取环境变量
api_key = os.getenv("API_KEY")  # 返回 None 如果不存在
api_key = os.getenv("API_KEY", "default_value")  # 提供默认值
api_key = os.environ["API_KEY"]  # KeyError 如果不存在

# 设置环境变量
os.environ["DEBUG"] = "1"

# 删除环境变量
os.environ.pop("TEMP_VAR", None)
```

#### .env 文件管理（推荐）
```python
# .env 文件内容
"""
# 开发环境配置
DEBUG=1
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost/dev_db
API_KEY=sk-dev-xxxxxxxxx
REDIS_HOST=localhost
REDIS_PORT=6379
"""

# Python 代码
from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()

# 读取配置
DEBUG = os.getenv("DEBUG") == "1"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATABASE_URL = os.getenv("DATABASE_URL")
```

### 11.2 多环境配置管理

#### 方案 1：环境变量切换
```bash
# .env.dev
DEBUG=1
DATABASE_URL=postgresql://localhost/dev_db

# .env.staging
DEBUG=0
DATABASE_URL=postgresql://staging-server/staging_db

# .env.prod
DEBUG=0
DATABASE_URL=postgresql://prod-server/prod_db
```

```python
import os
from dotenv import load_dotenv

# 根据环境加载不同配置文件
env = os.getenv("ENV", "dev")
env_file = f".env.{env}"
load_dotenv(env_file)

print(f"当前环境: {env}")
print(f"数据库: {os.getenv('DATABASE_URL')}")
```

#### 方案 2：配置类继承
```python
class BaseConfig:
    """基础配置"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = False
    TESTING = False

    # 数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 日志
    LOG_LEVEL = "INFO"

class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    DATABASE_URL = "postgresql://localhost/dev_db"
    LOG_LEVEL = "DEBUG"

class StagingConfig(BaseConfig):
    """预发布环境配置"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    LOG_LEVEL = "INFO"

class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    LOG_LEVEL = "WARNING"

    # 生产环境额外配置
    SENTRY_DSN = os.getenv("SENTRY_DSN")

# 配置映射
config_map = {
    "dev": DevelopmentConfig,
    "staging": StagingConfig,
    "prod": ProductionConfig,
}

# 获取当前配置
env = os.getenv("ENV", "dev")
Config = config_map[env]
```

### 11.3 配置验证（Pydantic）

```python
from pydantic import BaseSettings, Field, validator
from typing import Optional

class Settings(BaseSettings):
    """应用配置（带验证）"""

    # 基础配置
    app_name: str = "MyApp"
    debug: bool = False

    # 数据库配置
    database_url: str = Field(..., env="DATABASE_URL")  # 必填
    database_pool_size: int = Field(10, ge=1, le=100)  # 1-100

    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = Field(6379, ge=1, le=65535)
    redis_db: int = Field(0, ge=0, le=15)

    # API 配置
    api_key: Optional[str] = None
    api_timeout: int = Field(30, ge=1)

    # 日志配置
    log_level: str = Field("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    @validator("database_url")
    def validate_database_url(cls, v):
        """验证数据库 URL"""
        if not v.startswith(("postgresql://", "mysql://")):
            raise ValueError("数据库 URL 格式错误")
        return v

    @validator("api_key")
    def validate_api_key(cls, v):
        """验证 API Key"""
        if v and not v.startswith("sk-"):
            raise ValueError("API Key 必须以 sk- 开头")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 使用
try:
    settings = Settings()
    print(f"配置加载成功: {settings.app_name}")
except Exception as e:
    print(f"配置验证失败: {e}")
    sys.exit(1)
```

### 11.4 敏感信息管理

#### 方案 1：环境变量 + .env（开发）
```python
# .env
API_KEY=sk-xxxxxxxx
DATABASE_PASSWORD=secret123

# .gitignore
.env
.env.*
```

#### 方案 2：系统密钥管理（生产）
```python
import keyring

# 存储密钥
keyring.set_password("myapp", "api_key", "sk-xxxxxxxx")

# 读取密钥
api_key = keyring.get_password("myapp", "api_key")

# 删除密钥
keyring.delete_password("myapp", "api_key")
```

#### 方案 3：云服务密钥管理
```python
# AWS Secrets Manager
import boto3
import json

def get_secret(secret_name):
    """从 AWS Secrets Manager 获取密钥"""
    client = boto3.client("secretsmanager", region_name="us-east-1")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

# 使用
secrets = get_secret("myapp/prod/database")
DATABASE_URL = secrets["url"]
DATABASE_PASSWORD = secrets["password"]
```

```python
# HashiCorp Vault
import hvac

def get_vault_secret(path):
    """从 Vault 获取密钥"""
    client = hvac.Client(url="https://vault.example.com")
    client.token = os.getenv("VAULT_TOKEN")

    secret = client.secrets.kv.v2.read_secret_version(path=path)
    return secret["data"]["data"]

# 使用
secrets = get_vault_secret("myapp/database")
DATABASE_URL = secrets["url"]
```

### 11.5 配置热加载

```python
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigReloader(FileSystemEventHandler):
    """配置文件热加载"""

    def __init__(self, config_file, callback):
        self.config_file = config_file
        self.callback = callback

    def on_modified(self, event):
        if event.src_path.endswith(self.config_file):
            print(f"检测到配置文件变更: {self.config_file}")
            self.callback()

def reload_config():
    """重新加载配置"""
    load_dotenv(override=True)
    print("配置已重新加载")

# 启动监控
observer = Observer()
handler = ConfigReloader(".env", reload_config)
observer.schedule(handler, path=".", recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
```

### 11.6 生产环境配置清单

```python
class ProductionConfig:
    """生产环境配置检查清单"""

    @classmethod
    def validate(cls):
        """验证生产环境配置"""
        errors = []

        # 1. 检查必需环境变量
        required_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "API_KEY",
        ]
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"缺少必需环境变量: {var}")

        # 2. 检查 DEBUG 模式
        if os.getenv("DEBUG") == "1":
            errors.append("生产环境不能开启 DEBUG 模式")

        # 3. 检查密钥强度
        secret_key = os.getenv("SECRET_KEY", "")
        if len(secret_key) < 32:
            errors.append("SECRET_KEY 长度不足（至少 32 位）")

        # 4. 检查数据库连接
        database_url = os.getenv("DATABASE_URL", "")
        if "localhost" in database_url:
            errors.append("生产环境不应使用 localhost 数据库")

        # 5. 检查日志级别
        log_level = os.getenv("LOG_LEVEL", "INFO")
        if log_level == "DEBUG":
            errors.append("生产环境日志级别不应为 DEBUG")

        if errors:
            raise ValueError(f"配置验证失败:\n" + "\n".join(errors))

        print("✅ 生产环境配置验证通过")

# 启动时验证
if os.getenv("ENV") == "prod":
    ProductionConfig.validate()
```

---

## 12. 单元测试与代码质量

### 12.1 pytest 基础

#### 简单测试
```python
# test_math.py
def add(a, b):
    return a + b

def test_add():
    """测试加法函数"""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_add_negative():
    """测试负数"""
    assert add(-5, -3) == -8

# 运行测试
# pytest test_math.py
```

#### 参数化测试
```python
import pytest

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (-1, 1, 0),
    (0, 0, 0),
    (100, 200, 300),
    (-5, -3, -8),
])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
```

### 12.2 Fixture（测试装置）

```python
import pytest
import tempfile
import os

@pytest.fixture
def temp_file():
    """创建临时文件（自动清理）"""
    fd, path = tempfile.mkstemp()
    yield path  # 提供给测试用例
    os.close(fd)
    os.remove(path)  # 测试后自动删除

def test_file_write(temp_file):
    """测试文件写入"""
    with open(temp_file, "w") as f:
        f.write("Hello")

    with open(temp_file, "r") as f:
        assert f.read() == "Hello"

@pytest.fixture(scope="module")
def database():
    """模块级别的数据库连接（仅创建一次）"""
    db = create_database_connection()
    yield db
    db.close()

@pytest.fixture(scope="session")
def app_config():
    """会话级别的配置（整个测试期间仅一次）"""
    config = load_config()
    yield config
```

### 12.3 Mock 与 Patch

```python
from unittest.mock import Mock, patch, MagicMock
import requests

# 被测试函数
def fetch_user(user_id):
    """从 API 获取用户信息"""
    response = requests.get(f"https://api.example.com/users/{user_id}")
    response.raise_for_status()
    return response.json()

# 测试（Mock HTTP 请求）
@patch("requests.get")
def test_fetch_user(mock_get):
    """测试获取用户（不实际发送 HTTP 请求）"""
    # 设置 Mock 返回值
    mock_response = Mock()
    mock_response.json.return_value = {"id": 1, "name": "张三"}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # 执行测试
    user = fetch_user(1)

    # 断言
    assert user["name"] == "张三"
    mock_get.assert_called_once_with("https://api.example.com/users/1")

# Mock 类方法
class DataProcessor:
    def process(self, data):
        # 复杂处理逻辑
        return data.upper()

def test_data_processor():
    processor = DataProcessor()
    processor.process = Mock(return_value="MOCKED")

    result = processor.process("test")
    assert result == "MOCKED"
    processor.process.assert_called_once_with("test")
```

### 12.4 异步测试

```python
import pytest
import asyncio

async def async_fetch_data(url):
    """异步获取数据"""
    await asyncio.sleep(1)
    return f"Data from {url}"

@pytest.mark.asyncio
async def test_async_fetch_data():
    """测试异步函数"""
    result = await async_fetch_data("https://example.com")
    assert result == "Data from https://example.com"

@pytest.mark.asyncio
async def test_concurrent_fetch():
    """测试并发请求"""
    urls = ["url1", "url2", "url3"]
    tasks = [async_fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)

    assert len(results) == 3
    assert all("Data from" in r for r in results)
```

### 12.5 测试覆盖率

```bash
# 安装
pip install pytest-cov

# 运行并生成覆盖率报告
pytest --cov=myapp --cov-report=html tests/

# 查看报告
open htmlcov/index.html
```

```python
# pytest.ini 配置
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts =
    --cov=myapp
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

### 12.6 代码质量工具

#### Black（代码格式化）
```bash
# 安装
pip install black

# 格式化代码
black myapp/

# 检查（不修改）
black --check myapp/
```

#### Flake8（代码检查）
```bash
# 安装
pip install flake8

# 检查代码
flake8 myapp/

# .flake8 配置
[flake8]
max-line-length = 88
exclude = .git,__pycache__,venv
ignore = E203, W503
```

#### MyPy（类型检查）
```bash
# 安装
pip install mypy

# 类型检查
mypy myapp/
```

```python
# 类型注解示例
from typing import List, Dict, Optional

def process_users(users: List[Dict[str, str]]) -> Optional[str]:
    """处理用户列表"""
    if not users:
        return None

    names: List[str] = [u["name"] for u in users]
    return ", ".join(names)
```

### 12.7 CI/CD 集成

#### GitHub Actions 示例
```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.12

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov black flake8 mypy

    - name: Code formatting check
      run: black --check .

    - name: Linting
      run: flake8 .

    - name: Type checking
      run: mypy .

    - name: Run tests
      run: pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

### 12.8 测试最佳实践

```python
# ✅ 好的测试
def test_user_registration():
    """测试用户注册功能"""
    # Arrange（准备）
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    }

    # Act（执行）
    user = register_user(user_data)

    # Assert（断言）
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.password != "securepass123"  # 密码应该被加密

# ❌ 不好的测试
def test_everything():
    """测试所有功能（太宽泛）"""
    user = create_user()
    assert user is not None  # 断言太弱
    # 测试太多功能，难以定位问题

# ✅ 测试边界条件
@pytest.mark.parametrize("age", [-1, 0, 150, 200])
def test_age_validation_invalid(age):
    """测试无效年龄"""
    with pytest.raises(ValueError):
        validate_age(age)

@pytest.mark.parametrize("age", [1, 18, 65, 120])
def test_age_validation_valid(age):
    """测试有效年龄"""
    assert validate_age(age) is True
```

---

## 第四部分：DevOps 脚本编程

---

## 13. 系统调用与子进程管理

### 13.1 subprocess 模块基础

#### 运行简单命令
```python
import subprocess

# 方法 1：run()（推荐，Python 3.5+）
result = subprocess.run(
    ["ls", "-la"],
    capture_output=True,  # 捕获输出
    text=True,            # 文本模式（非字节）
    check=True,           # 非零退出码抛出异常
)

print("标准输出:", result.stdout)
print("标准错误:", result.stderr)
print("退出码:", result.returncode)

# 方法 2：运行 shell 命令
result = subprocess.run(
    "ls -la | grep .py",
    shell=True,
    capture_output=True,
    text=True,
)
```

#### 错误处理
```python
try:
    result = subprocess.run(
        ["nonexistent-command"],
        capture_output=True,
        text=True,
        check=True,  # 非零退出码抛出 CalledProcessError
    )
except subprocess.CalledProcessError as e:
    print(f"命令失败，退出码: {e.returncode}")
    print(f"错误输出: {e.stderr}")
except FileNotFoundError:
    print("命令不存在")
```

### 13.2 实时输出流

```python
import subprocess

def run_with_realtime_output(cmd):
    """实时打印命令输出"""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # 行缓冲
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()
    return process.returncode

# 使用
exit_code = run_with_realtime_output(["ping", "-c", "5", "google.com"])
print(f"退出码: {exit_code}")
```

### 13.3 超时控制

```python
import subprocess

try:
    result = subprocess.run(
        ["sleep", "10"],
        timeout=5,  # 5 秒超时
        check=True,
    )
except subprocess.TimeoutExpired:
    print("命令执行超时")
```

### 13.4 进程管道

```python
# 等价于：cat file.txt | grep "error" | wc -l

# 方法 1：手动管道
p1 = subprocess.Popen(["cat", "file.txt"], stdout=subprocess.PIPE)
p2 = subprocess.Popen(["grep", "error"], stdin=p1.stdout, stdout=subprocess.PIPE)
p1.stdout.close()  # 允许 p1 在 p2 完成前退出
p3 = subprocess.Popen(["wc", "-l"], stdin=p2.stdout, stdout=subprocess.PIPE)
p2.stdout.close()

output, _ = p3.communicate()
print(f"错误行数: {output.decode().strip()}")

# 方法 2：使用 shell（简单但不安全）
result = subprocess.run(
    "cat file.txt | grep error | wc -l",
    shell=True,
    capture_output=True,
    text=True,
)
print(f"错误行数: {result.stdout.strip()}")
```

### 13.5 交互式命令

```python
import subprocess

def run_interactive_command(cmd, inputs):
    """运行交互式命令"""
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # 发送输入
    stdout, stderr = process.communicate(input=inputs)

    return stdout, stderr, process.returncode

# 示例：自动化 SSH 密钥生成
stdout, stderr, code = run_interactive_command(
    ["ssh-keygen", "-t", "rsa"],
    inputs="\n\n\n",  # 三次回车（默认值）
)
```

### 13.6 子进程管理工具类

```python
import subprocess
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class CommandExecutor:
    """命令执行器（生产级）"""

    @staticmethod
    def run(
        cmd: List[str],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[int] = None,
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        执行命令

        Args:
            cmd: 命令列表
            cwd: 工作目录
            env: 环境变量
            timeout: 超时时间（秒）
            check: 失败时抛出异常
            capture_output: 捕获输出
        """
        logger.info(f"执行命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                timeout=timeout,
                check=check,
                capture_output=capture_output,
                text=True,
            )

            logger.debug(f"命令输出: {result.stdout}")
            return result

        except subprocess.TimeoutExpired as e:
            logger.error(f"命令超时: {e}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"命令失败: {e.stderr}")
            raise
        except FileNotFoundError as e:
            logger.error(f"命令不存在: {e}")
            raise

    @staticmethod
    def run_shell(
        cmd: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> subprocess.CompletedProcess:
        """运行 shell 命令"""
        logger.warning(f"使用 shell 执行命令（安全风险）: {cmd}")

        return subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def run_async(cmd: List[str]) -> subprocess.Popen:
        """异步执行命令（后台运行）"""
        logger.info(f"异步执行: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        return process

# 使用示例
executor = CommandExecutor()

# 同步执行
result = executor.run(["git", "status"])
print(result.stdout)

# 异步执行
process = executor.run_async(["ping", "-c", "100", "google.com"])
print(f"进程 PID: {process.pid}")

# 稍后检查状态
if process.poll() is None:
    print("进程仍在运行")
else:
    print(f"进程已结束，退出码: {process.returncode}")
```

### 13.7 DevOps 实战案例

#### 案例 1：批量服务器部署
```python
import subprocess
import concurrent.futures

def deploy_to_server(host, app_path):
    """部署应用到服务器"""
    commands = [
        f"rsync -avz {app_path} {host}:/opt/app/",
        f"ssh {host} 'systemctl restart myapp'",
        f"ssh {host} 'systemctl status myapp'",
    ]

    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            print(f"✅ {host}: {cmd}")
        except subprocess.CalledProcessError as e:
            print(f"❌ {host}: {cmd} 失败\n{e.stderr}")
            return False

    return True

# 并发部署到多台服务器
servers = ["server1.example.com", "server2.example.com", "server3.example.com"]
app_path = "./dist/"

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(deploy_to_server, host, app_path): host for host in servers}

    for future in concurrent.futures.as_completed(futures):
        host = futures[future]
        try:
            success = future.result()
            if success:
                print(f"✅ {host} 部署成功")
            else:
                print(f"❌ {host} 部署失败")
        except Exception as e:
            print(f"❌ {host} 异常: {e}")
```

#### 案例 2：Docker 容器管理
```python
class DockerManager:
    """Docker 容器管理"""

    @staticmethod
    def build_image(tag, dockerfile_path="."):
        """构建镜像"""
        result = subprocess.run(
            ["docker", "build", "-t", tag, dockerfile_path],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"✅ 镜像构建成功: {tag}")
        else:
            print(f"❌ 构建失败:\n{result.stderr}")

        return result.returncode == 0

    @staticmethod
    def run_container(image, name, ports=None, env=None):
        """运行容器"""
        cmd = ["docker", "run", "-d", "--name", name]

        if ports:
            for host_port, container_port in ports.items():
                cmd.extend(["-p", f"{host_port}:{container_port}"])

        if env:
            for key, value in env.items():
                cmd.extend(["-e", f"{key}={value}"])

        cmd.append(image)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            container_id = result.stdout.strip()
            print(f"✅ 容器启动成功: {name} ({container_id[:12]})")
            return container_id
        else:
            print(f"❌ 容器启动失败:\n{result.stderr}")
            return None

    @staticmethod
    def stop_container(name):
        """停止容器"""
        result = subprocess.run(
            ["docker", "stop", name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    @staticmethod
    def logs(name, tail=100):
        """查看容器日志"""
        result = subprocess.run(
            ["docker", "logs", "--tail", str(tail), name],
            capture_output=True,
            text=True,
        )
        return result.stdout

# 使用
docker = DockerManager()

# 构建镜像
docker.build_image("myapp:latest")

# 运行容器
container_id = docker.run_container(
    "myapp:latest",
    "myapp-container",
    ports={8080: 80},
    env={"DEBUG": "0", "DATABASE_URL": "postgresql://db/prod"},
)

# 查看日志
logs = docker.logs("myapp-container", tail=50)
print(logs)
```

#### 案例 3：Git 自动化
```python
class GitAutomation:
    """Git 自动化操作"""

    def __init__(self, repo_path):
        self.repo_path = repo_path

    def _run_git(self, *args):
        """运行 git 命令"""
        result = subprocess.run(
            ["git", "-C", self.repo_path] + list(args),
            capture_output=True,
            text=True,
        )
        return result

    def clone(self, url):
        """克隆仓库"""
        result = subprocess.run(
            ["git", "clone", url, self.repo_path],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def pull(self):
        """拉取更新"""
        result = self._run_git("pull")
        return result.returncode == 0

    def commit(self, message):
        """提交变更"""
        self._run_git("add", ".")
        result = self._run_git("commit", "-m", message)
        return result.returncode == 0

    def push(self, branch="main"):
        """推送到远程"""
        result = self._run_git("push", "origin", branch)
        return result.returncode == 0

    def get_current_branch(self):
        """获取当前分支"""
        result = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip()

    def get_status(self):
        """获取仓库状态"""
        result = self._run_git("status", "--porcelain")
        return result.stdout

    def has_uncommitted_changes(self):
        """检查是否有未提交的变更"""
        return bool(self.get_status())

# 使用
git = GitAutomation("/path/to/repo")

if git.has_uncommitted_changes():
    print("检测到未提交的变更")
    git.commit("自动提交：定时备份")
    git.push()
else:
    print("没有变更")
```

---

## 14. 文件系统操作

### 14.1 pathlib 现代路径处理

```python
from pathlib import Path

# 创建路径对象
path = Path("/Users/huaan/Projects/AI")

# 路径拼接（跨平台）
config_path = path / "config" / "settings.json"
print(config_path)  # /Users/huaan/Projects/AI/config/settings.json

# 路径属性
print(path.name)       # AI
print(path.stem)       # AI
print(path.suffix)     # （空）
print(path.parent)     # /Users/huaan/Projects
print(path.parts)      # ('/', 'Users', 'huaan', 'Projects', 'AI')

# 文件操作
file_path = Path("data.txt")
file_path.write_text("Hello World")      # 写入
content = file_path.read_text()          # 读取
file_path.unlink()                        # 删除

# 目录操作
dir_path = Path("new_dir")
dir_path.mkdir(parents=True, exist_ok=True)  # 创建目录
dir_path.rmdir()                              # 删除空目录

# 检查
print(path.exists())        # 是否存在
print(path.is_file())       # 是否文件
print(path.is_dir())        # 是否目录
print(path.is_symlink())    # 是否符号链接
```

### 14.2 遍历文件

```python
from pathlib import Path

# 遍历当前目录
for item in Path(".").iterdir():
    print(item)

# 递归遍历（查找所有 .py 文件）
for py_file in Path(".").rglob("*.py"):
    print(py_file)

# 查找特定模式
for log_file in Path("/var/log").glob("*.log"):
    print(log_file)

# 过滤文件
py_files = [f for f in Path("src").rglob("*.py") if f.is_file()]
print(f"找到 {len(py_files)} 个 Python 文件")
```

### 14.3 文件元数据

```python
from pathlib import Path
import time

file = Path("example.txt")

# 文件大小
size = file.stat().st_size
print(f"文件大小: {size} 字节")

# 修改时间
mtime = file.stat().st_mtime
print(f"最后修改: {time.ctime(mtime)}")

# 权限
mode = file.stat().st_mode
print(f"权限: {oct(mode)}")

# 修改权限
file.chmod(0o644)  # rw-r--r--
```

### 14.4 批量文件操作

```python
from pathlib import Path
import shutil

class FileManager:
    """文件管理工具"""

    @staticmethod
    def copy_files(source_dir, dest_dir, pattern="*.py"):
        """批量复制文件"""
        source = Path(source_dir)
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)

        count = 0
        for file in source.rglob(pattern):
            if file.is_file():
                # 保持目录结构
                relative_path = file.relative_to(source)
                dest_file = dest / relative_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(file, dest_file)
                count += 1

        print(f"✅ 复制了 {count} 个文件")
        return count

    @staticmethod
    def clean_old_files(directory, days=30, pattern="*"):
        """删除旧文件"""
        import time

        cutoff = time.time() - (days * 24 * 60 * 60)
        count = 0

        for file in Path(directory).rglob(pattern):
            if file.is_file() and file.stat().st_mtime < cutoff:
                file.unlink()
                count += 1
                print(f"删除: {file}")

        print(f"✅ 删除了 {count} 个文件")
        return count

    @staticmethod
    def get_directory_size(directory):
        """计算目录大小"""
        total_size = 0
        for file in Path(directory).rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size

        # 格式化输出
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if total_size < 1024:
                return f"{total_size:.2f} {unit}"
            total_size /= 1024

        return f"{total_size:.2f} PB"

# 使用
fm = FileManager()

# 备份 Python 文件
fm.copy_files("src", "backup/src", "*.py")

# 清理 30 天前的日志
fm.clean_old_files("/var/log/myapp", days=30, pattern="*.log")

# 查看目录大小
size = fm.get_directory_size("/var/log")
print(f"日志目录大小: {size}")
```

### 14.5 文件监控（watchdog）

```python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    """文件变更处理器"""

    def on_created(self, event):
        if not event.is_directory:
            print(f"✨ 新建文件: {event.src_path}")

    def on_modified(self, event):
        if not event.is_directory:
            print(f"📝 修改文件: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"🗑️  删除文件: {event.src_path}")

    def on_moved(self, event):
        if not event.is_directory:
            print(f"📦 移动文件: {event.src_path} → {event.dest_path}")

# 启动监控
observer = Observer()
handler = FileChangeHandler()
observer.schedule(handler, path="./watch_dir", recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()
```

### 14.6 DevOps 实战案例

#### 案例 1：日志归档
```python
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class LogArchiver:
    """日志归档工具"""

    def __init__(self, log_dir, archive_dir):
        self.log_dir = Path(log_dir)
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def archive_old_logs(self, days=7):
        """归档旧日志"""
        cutoff = datetime.now() - timedelta(days=days)

        for log_file in self.log_dir.glob("*.log"):
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            if mtime < cutoff:
                self._compress_and_move(log_file)

    def _compress_and_move(self, log_file):
        """压缩并移动日志"""
        # 生成归档文件名
        archive_name = f"{log_file.stem}_{datetime.now():%Y%m%d}.log.gz"
        archive_path = self.archive_dir / archive_name

        # 压缩
        with open(log_file, "rb") as f_in:
            with gzip.open(archive_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # 删除原文件
        log_file.unlink()
        print(f"✅ 归档: {log_file} → {archive_path}")

    def cleanup_old_archives(self, days=90):
        """清理旧归档"""
        cutoff = datetime.now() - timedelta(days=days)

        for archive in self.archive_dir.glob("*.log.gz"):
            mtime = datetime.fromtimestamp(archive.stat().st_mtime)

            if mtime < cutoff:
                archive.unlink()
                print(f"🗑️  删除旧归档: {archive}")

# 使用
archiver = LogArchiver("/var/log/myapp", "/var/log/myapp/archive")
archiver.archive_old_logs(days=7)
archiver.cleanup_old_archives(days=90)
```

#### 案例 2：配置文件同步
```python
import hashlib
from pathlib import Path

def file_hash(file_path):
    """计算文件 MD5"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def sync_config_files(source_dir, dest_dir):
    """同步配置文件"""
    source = Path(source_dir)
    dest = Path(dest_dir)

    synced = 0
    skipped = 0

    for source_file in source.rglob("*"):
        if not source_file.is_file():
            continue

        # 计算目标路径
        relative_path = source_file.relative_to(source)
        dest_file = dest / relative_path

        # 检查是否需要同步
        if dest_file.exists():
            if file_hash(source_file) == file_hash(dest_file):
                skipped += 1
                continue

        # 同步文件
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, dest_file)
        synced += 1
        print(f"✅ 同步: {relative_path}")

    print(f"\n同步完成: {synced} 个文件同步, {skipped} 个文件跳过")

# 使用
sync_config_files("/etc/myapp", "/backup/config")
```

---

## 第 15 章：网络编程基础

### 15.1 Socket 编程核心概念

#### 基础 TCP 服务器
```python
import socket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TCPServer:
    """基础 TCP 服务器"""

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None

    def start(self):
        """启动服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 设置 SO_REUSEADDR（允许立即重启）
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 绑定地址并监听
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # backlog=5

        logger.info(f"🚀 服务器启动: {self.host}:{self.port}")

        try:
            while True:
                # 接受客户端连接
                client_socket, client_address = self.server_socket.accept()
                logger.info(f"📞 客户端连接: {client_address}")

                # 处理客户端请求
                self.handle_client(client_socket, client_address)
        except KeyboardInterrupt:
            logger.info("⛔ 服务器关闭")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        """处理客户端请求"""
        try:
            # 接收数据（最多 1024 字节）
            data = client_socket.recv(1024)

            if not data:
                logger.warning(f"客户端 {client_address} 未发送数据")
                return

            message = data.decode('utf-8')
            logger.info(f"📨 收到消息: {message}")

            # 响应客户端
            response = f"服务器收到: {message}"
            client_socket.sendall(response.encode('utf-8'))

        except Exception as e:
            logger.error(f"处理客户端失败: {e}")
        finally:
            client_socket.close()

# 启动服务器
if __name__ == "__main__":
    server = TCPServer()
    server.start()
```

#### TCP 客户端
```python
import socket

def tcp_client(host='localhost', port=8888, message='Hello Server'):
    """TCP 客户端"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接服务器
        client_socket.connect((host, port))
        print(f"✅ 连接服务器: {host}:{port}")

        # 发送数据
        client_socket.sendall(message.encode('utf-8'))

        # 接收响应
        response = client_socket.recv(1024).decode('utf-8')
        print(f"📥 服务器响应: {response}")

    except ConnectionRefusedError:
        print(f"❌ 无法连接到 {host}:{port}")
    except Exception as e:
        print(f"❌ 客户端错误: {e}")
    finally:
        client_socket.close()

# 测试
tcp_client(message="测试消息")
```

---

### 15.2 多客户端并发处理

#### 方案 1：多线程服务器
```python
import socket
import threading
import logging

class MultiThreadTCPServer:
    """多线程 TCP 服务器"""

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_count = 0
        self.lock = threading.Lock()

    def start(self):
        """启动服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)  # 更大的 backlog

        logger.info(f"🚀 多线程服务器启动: {self.host}:{self.port}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()

                # 为每个客户端创建线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True  # 守护线程（主进程退出时自动结束）
                )
                client_thread.start()

                # 线程安全计数
                with self.lock:
                    self.client_count += 1
                    logger.info(f"📞 客户端 {self.client_count} 连接: {client_address}")

        except KeyboardInterrupt:
            logger.info("⛔ 服务器关闭")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        """处理客户端（在独立线程中）"""
        try:
            while True:
                data = client_socket.recv(1024)

                if not data:
                    break

                message = data.decode('utf-8')
                logger.info(f"📨 [{client_address}] {message}")

                # Echo 响应
                response = f"Echo: {message}"
                client_socket.sendall(response.encode('utf-8'))

        except Exception as e:
            logger.error(f"客户端 {client_address} 错误: {e}")
        finally:
            client_socket.close()
            logger.info(f"👋 客户端 {client_address} 断开连接")
```

#### 方案 2：异步服务器 (asyncio)
```python
import asyncio
import logging

class AsyncTCPServer:
    """异步 TCP 服务器（性能更优）"""

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port

    async def start(self):
        """启动异步服务器"""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )

        addr = server.sockets[0].getsockname()
        logger.info(f"🚀 异步服务器启动: {addr}")

        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        """处理客户端（异步协程）"""
        addr = writer.get_extra_info('peername')
        logger.info(f"📞 客户端连接: {addr}")

        try:
            while True:
                # 异步读取数据
                data = await reader.read(1024)

                if not data:
                    break

                message = data.decode('utf-8')
                logger.info(f"📨 [{addr}] {message}")

                # 异步写入响应
                response = f"Echo: {message}"
                writer.write(response.encode('utf-8'))
                await writer.drain()  # 确保发送完成

        except Exception as e:
            logger.error(f"客户端 {addr} 错误: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"👋 客户端 {addr} 断开连接")

# 启动异步服务器
if __name__ == "__main__":
    server = AsyncTCPServer()
    asyncio.run(server.start())
```

---

### 15.3 HTTP 客户端编程

#### 使用 requests 库
```python
import requests
from typing import Optional, Dict
import logging

class HTTPClient:
    """HTTP 客户端封装"""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

        # 设置默认 headers
        self.session.headers.update({
            'User-Agent': 'MyApp/1.0',
            'Accept': 'application/json'
        })

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET 请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()  # 检查 HTTP 错误

            logger.info(f"✅ GET {url} - {response.status_code}")
            return response.json()

        except requests.Timeout:
            logger.error(f"⏱️  请求超时: {url}")
            raise
        except requests.HTTPError as e:
            logger.error(f"❌ HTTP 错误: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"❌ 请求失败: {e}")
            raise

    def post(self, endpoint: str, data: Dict) -> Dict:
        """POST 请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.post(
                url,
                json=data,  # 自动序列化为 JSON
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"✅ POST {url} - {response.status_code}")
            return response.json()

        except Exception as e:
            logger.error(f"❌ POST 失败: {e}")
            raise

    def download_file(self, url: str, save_path: str):
        """下载文件（流式传输）"""
        try:
            with self.session.get(url, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()

                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))

                with open(save_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 显示进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r下载进度: {progress:.1f}%", end='')

                print(f"\n✅ 文件已下载: {save_path}")

        except Exception as e:
            logger.error(f"❌ 下载失败: {e}")
            raise

# 使用示例
client = HTTPClient("https://api.github.com")

# GET 请求
user = client.get("/users/torvalds")
print(f"用户: {user['name']}")

# POST 请求（示例）
# data = client.post("/api/v1/users", data={"name": "张三", "email": "test@example.com"})

# 下载文件
client.download_file(
    "https://example.com/file.pdf",
    "/tmp/downloaded.pdf"
)
```

---

### 15.4 简易 HTTP 服务器

#### 使用 http.server 模块
```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging

class SimpleHTTPHandler(BaseHTTPRequestHandler):
    """简易 HTTP 请求处理器"""

    def do_GET(self):
        """处理 GET 请求"""
        logger.info(f"GET {self.path}")

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            html = """
            <html>
            <head><title>测试服务器</title></head>
            <body>
                <h1>欢迎访问测试服务器</h1>
                <p>尝试访问: <a href="/api/status">/api/status</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

        elif self.path == '/api/status':
            self.send_json_response({
                'status': 'ok',
                'message': '服务器运行正常'
            })
        else:
            self.send_error(404, "页面不存在")

    def do_POST(self):
        """处理 POST 请求"""
        # 读取 POST 数据
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            logger.info(f"POST {self.path} - {data}")

            # 响应
            self.send_json_response({
                'status': 'success',
                'received': data
            })
        except Exception as e:
            self.send_error(400, f"Invalid JSON: {e}")

    def send_json_response(self, data):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        """自定义日志格式"""
        logger.info(f"{self.address_string()} - {format % args}")

# 启动服务器
def start_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPHandler)
    logger.info(f"🚀 HTTP 服务器启动: http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    start_server()
```

---

### 15.5 WebSocket 实时通信

#### 使用 websockets 库
```python
import asyncio
import websockets
import json
import logging

class WebSocketServer:
    """WebSocket 服务器"""

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()  # 连接的客户端集合

    async def start(self):
        """启动 WebSocket 服务器"""
        async with websockets.serve(self.handler, self.host, self.port):
            logger.info(f"🚀 WebSocket 服务器启动: ws://{self.host}:{self.port}")
            await asyncio.Future()  # 永久运行

    async def handler(self, websocket, path):
        """处理 WebSocket 连接"""
        # 注册客户端
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"📞 客户端连接: {client_id}")

        try:
            # 发送欢迎消息
            await websocket.send(json.dumps({
                'type': 'welcome',
                'message': '欢迎连接 WebSocket 服务器'
            }))

            # 持续接收消息
            async for message in websocket:
                logger.info(f"📨 [{client_id}] {message}")

                # 解析消息
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON'
                    }))

        except websockets.ConnectionClosed:
            logger.info(f"👋 客户端断开: {client_id}")
        finally:
            self.clients.remove(websocket)

    async def handle_message(self, websocket, data):
        """处理消息"""
        msg_type = data.get('type')

        if msg_type == 'broadcast':
            # 广播消息给所有客户端
            await self.broadcast(data.get('message'))
        elif msg_type == 'echo':
            # 回显消息
            await websocket.send(json.dumps({
                'type': 'echo',
                'message': data.get('message')
            }))

    async def broadcast(self, message):
        """广播消息给所有客户端"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps({
                    'type': 'broadcast',
                    'message': message
                })) for client in self.clients]
            )

# 启动服务器
if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.run(server.start())
```

#### WebSocket 客户端
```python
import asyncio
import websockets
import json

async def websocket_client():
    """WebSocket 客户端"""
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:
        print(f"✅ 连接到 {uri}")

        # 接收欢迎消息
        welcome = await websocket.recv()
        print(f"📥 {welcome}")

        # 发送消息
        await websocket.send(json.dumps({
            'type': 'echo',
            'message': 'Hello WebSocket!'
        }))

        # 接收响应
        response = await websocket.recv()
        print(f"📥 {response}")

        # 广播消息
        await websocket.send(json.dumps({
            'type': 'broadcast',
            'message': '这是一条广播消息'
        }))

        # 持续接收消息
        while True:
            message = await websocket.recv()
            print(f"📥 {message}")

# 运行客户端
asyncio.run(websocket_client())
```

---

### 15.6 生产级网络编程实践

#### 1. 连接池管理
```python
import urllib3
from urllib3.util.retry import Retry

# 创建连接池
http = urllib3.PoolManager(
    maxsize=10,  # 最大连接数
    block=True,  # 连接池满时阻塞
    retries=Retry(
        total=3,
        backoff_factor=0.3,  # 重试延迟
        status_forcelist=[500, 502, 503, 504]
    )
)

# 使用连接池
response = http.request('GET', 'https://api.example.com/data')
print(response.status)
```

#### 2. 超时与重试
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry():
    """创建带重试机制的 Session"""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1  # 1s, 2s, 4s
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

# 使用
session = create_session_with_retry()
response = session.get(
    "https://api.example.com/data",
    timeout=(3, 10)  # (连接超时, 读取超时)
)
```

#### 3. 安全性实践
```python
import requests
import certifi

# ✅ 使用 SSL 证书验证
response = requests.get(
    "https://api.example.com",
    verify=certifi.where()  # 使用 certifi 证书库
)

# ✅ 禁用不安全的警告（仅开发环境）
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ⚠️  仅开发环境使用
# response = requests.get("https://example.com", verify=False)
```

---

## 第 16 章:多线程与多进程

### 16.1 全局解释器锁 (GIL) 理解

#### GIL 的影响
```python
import threading
import time

# ❌ CPU 密集任务：GIL 限制，多线程无性能提升
def cpu_bound_task():
    """CPU 密集任务"""
    result = 0
    for i in range(10_000_000):
        result += i
    return result

# 单线程
start = time.time()
cpu_bound_task()
cpu_bound_task()
single_time = time.time() - start
print(f"单线程耗时: {single_time:.2f}s")

# 多线程（GIL 限制，几乎无提升）
start = time.time()
t1 = threading.Thread(target=cpu_bound_task)
t2 = threading.Thread(target=cpu_bound_task)
t1.start()
t2.start()
t1.join()
t2.join()
multi_time = time.time() - start
print(f"多线程耗时: {multi_time:.2f}s")  # 几乎不比单线程快

# ✅ I/O 密集任务：多线程有效
import requests

def io_bound_task(url):
    """I/O 密集任务"""
    requests.get(url, timeout=5)

urls = ["https://example.com"] * 10

# 单线程
start = time.time()
for url in urls:
    io_bound_task(url)
single_io_time = time.time() - start

# 多线程（有明显提升）
start = time.time()
threads = [threading.Thread(target=io_bound_task, args=(url,)) for url in urls]
for t in threads:
    t.start()
for t in threads:
    t.join()
multi_io_time = time.time() - start

print(f"\nI/O 任务 - 单线程: {single_io_time:.2f}s, 多线程: {multi_io_time:.2f}s")
```

**结论**：
- **CPU 密集任务**：使用 `multiprocessing`（多进程）
- **I/O 密集任务**：使用 `threading` 或 `asyncio`

---

### 16.2 多线程编程

#### 基础线程操作
```python
import threading
import time

def worker(name, delay):
    """工作线程"""
    print(f"🔧 线程 {name} 启动")
    time.sleep(delay)
    print(f"✅ 线程 {name} 完成")

# 创建线程
threads = []
for i in range(3):
    t = threading.Thread(
        target=worker,
        args=(f"Worker-{i}", i + 1),
        daemon=True  # 守护线程
    )
    threads.append(t)
    t.start()

# 等待所有线程完成
for t in threads:
    t.join()

print("🎉 所有线程已完成")
```

#### 线程同步 - Lock
```python
import threading

# ❌ 线程不安全（存在竞态条件）
counter = 0

def increment_unsafe():
    global counter
    for _ in range(100000):
        counter += 1  # 非原子操作！

threads = [threading.Thread(target=increment_unsafe) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"❌ 线程不安全结果: {counter}")  # 可能小于 500000

# ✅ 线程安全（使用 Lock）
counter_safe = 0
lock = threading.Lock()

def increment_safe():
    global counter_safe
    for _ in range(100000):
        with lock:  # 自动加锁/解锁
            counter_safe += 1

threads = [threading.Thread(target=increment_safe) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"✅ 线程安全结果: {counter_safe}")  # 总是 500000
```

#### 线程池 - ThreadPoolExecutor
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def task(n):
    """模拟任务"""
    time.sleep(1)
    return n * n

# 使用线程池
with ThreadPoolExecutor(max_workers=5) as executor:
    # 方式 1: map()
    results = executor.map(task, range(10))
    print("Map 结果:", list(results))

    # 方式 2: submit()
    futures = [executor.submit(task, i) for i in range(10)]

    # 获取完成的结果
    for future in as_completed(futures):
        result = future.result()
        print(f"完成任务: {result}")
```

---

### 16.3 多进程编程

#### 基础进程操作
```python
from multiprocessing import Process
import os
import time

def worker(name):
    """工作进程"""
    print(f"🔧 进程 {name} 启动 (PID: {os.getpid()})")
    time.sleep(2)
    print(f"✅ 进程 {name} 完成")

if __name__ == "__main__":
    processes = []

    for i in range(3):
        p = Process(target=worker, args=(f"Worker-{i}",))
        processes.append(p)
        p.start()

    # 等待所有进程
    for p in processes:
        p.join()

    print("🎉 所有进程已完成")
```

#### 进程池 - ProcessPoolExecutor
```python
from concurrent.futures import ProcessPoolExecutor
import time

def cpu_intensive_task(n):
    """CPU 密集任务"""
    result = 0
    for i in range(n):
        result += i * i
    return result

if __name__ == "__main__":
    # ✅ 多进程处理 CPU 密集任务
    with ProcessPoolExecutor(max_workers=4) as executor:
        tasks = [10_000_000] * 8

        start = time.time()
        results = list(executor.map(cpu_intensive_task, tasks))
        elapsed = time.time() - start

        print(f"✅ 处理完成，耗时: {elapsed:.2f}s")
        print(f"CPU 核心数: {os.cpu_count()}")
```

---

### 16.4 进程间通信 (IPC)

#### 1. Queue（队列）
```python
from multiprocessing import Process, Queue

def producer(queue, items):
    """生产者"""
    for item in items:
        queue.put(item)
        print(f"📤 生产: {item}")
    queue.put(None)  # 结束信号

def consumer(queue):
    """消费者"""
    while True:
        item = queue.get()
        if item is None:
            break
        print(f"📥 消费: {item}")

if __name__ == "__main__":
    q = Queue()

    p1 = Process(target=producer, args=(q, range(5)))
    p2 = Process(target=consumer, args=(q,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
```

#### 2. Pipe（管道）
```python
from multiprocessing import Process, Pipe

def sender(conn, messages):
    """发送进程"""
    for msg in messages:
        conn.send(msg)
        print(f"📤 发送: {msg}")
    conn.close()

def receiver(conn):
    """接收进程"""
    while True:
        try:
            msg = conn.recv()
            print(f"📥 接收: {msg}")
        except EOFError:
            break

if __name__ == "__main__":
    parent_conn, child_conn = Pipe()

    p1 = Process(target=sender, args=(parent_conn, ["Hello", "World", "!"]))
    p2 = Process(target=receiver, args=(child_conn,))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
```

#### 3. Manager（共享状态）
```python
from multiprocessing import Process, Manager

def worker(shared_dict, shared_list, worker_id):
    """工作进程"""
    shared_dict[worker_id] = f"Worker {worker_id}"
    shared_list.append(worker_id)

if __name__ == "__main__":
    with Manager() as manager:
        shared_dict = manager.dict()
        shared_list = manager.list()

        processes = []
        for i in range(5):
            p = Process(target=worker, args=(shared_dict, shared_list, i))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        print("共享字典:", dict(shared_dict))
        print("共享列表:", list(shared_list))
```

---

### 16.5 异步编程 (asyncio)

#### 基础协程
```python
import asyncio

async def fetch_data(n):
    """异步获取数据"""
    print(f"🔄 开始获取数据 {n}")
    await asyncio.sleep(1)  # 模拟 I/O 操作
    print(f"✅ 数据 {n} 获取完成")
    return n * 2

async def main():
    """主协程"""
    # 并发执行多个任务
    tasks = [fetch_data(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    print(f"所有结果: {results}")

# 运行
asyncio.run(main())
```

#### 异步 HTTP 请求
```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    """异步获取 URL"""
    async with session.get(url) as response:
        return await response.text()

async def fetch_multiple_urls(urls):
    """并发获取多个 URL"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# 使用
urls = [
    "https://example.com",
    "https://httpbin.org/get",
    "https://api.github.com"
]

results = asyncio.run(fetch_multiple_urls(urls))
print(f"获取了 {len(results)} 个响应")
```

---

### 16.6 线程/进程选择指南

#### 决策流程图
```python
"""
                    开始
                     |
            任务类型是什么？
           /       |       \
        CPU 密集  I/O 密集  混合
          |         |        |
     多进程(MP)  异步(asyncio)  |
                     |         |
              需要并发数？    分析瓶颈
                /    \         |
              低(<100) 高(>100) 针对性优化
               |        |
          多线程    asyncio
          (Thread)
"""

# 示例：批量处理任务
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import requests

def choose_executor(task_type, task_count):
    """根据任务类型选择执行器"""

    if task_type == "cpu":
        # CPU 密集：使用进程池
        return ProcessPoolExecutor(max_workers=os.cpu_count())

    elif task_type == "io" and task_count < 100:
        # I/O 密集 + 中等并发：使用线程池
        return ThreadPoolExecutor(max_workers=20)

    else:
        # I/O 密集 + 高并发：建议使用 asyncio
        print("⚠️  建议使用 asyncio 替代")
        return ThreadPoolExecutor(max_workers=50)

# 使用
def cpu_task(n):
    return sum(i * i for i in range(n))

def io_task(url):
    return requests.get(url, timeout=5).status_code

# CPU 密集任务
with choose_executor("cpu", 8) as executor:
    results = list(executor.map(cpu_task, [10_000_000] * 8))

# I/O 密集任务
with choose_executor("io", 50) as executor:
    urls = ["https://httpbin.org/delay/1"] * 50
    results = list(executor.map(io_task, urls))
```

---

## 第 17 章：性能分析与优化

### 17.1 性能分析工具

#### 1. cProfile - 函数级性能分析
```python
import cProfile
import pstats
from io import StringIO

def slow_function():
    """慢函数示例"""
    result = 0
    for i in range(1000000):
        result += i
    return result

def medium_function():
    """中速函数"""
    return [i ** 2 for i in range(10000)]

def main():
    slow_function()
    medium_function()

# 方式 1：直接分析
cProfile.run('main()')

# 方式 2：保存到文件
cProfile.run('main()', 'profile_stats.prof')

# 方式 3：程序化分析
profiler = cProfile.Profile()
profiler.enable()

main()

profiler.disable()

# 输出统计
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')  # 按累计时间排序
stats.print_stats(10)  # 显示前 10 个函数
```

**输出解读**：
```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     1    0.052    0.052    0.052    0.052 script.py:5(slow_function)
     1    0.003    0.003    0.003    0.003 script.py:11(medium_function)
```
- `ncalls`: 调用次数
- `tottime`: 函数内部耗时（不含子函数）
- `cumtime`: 累计耗时（含子函数）

---

#### 2. line_profiler - 行级性能分析
```python
# 安装: pip install line_profiler

@profile  # 添加装饰器
def analyze_me():
    """需要分析的函数"""
    result = []
    for i in range(10000):
        result.append(i ** 2)  # 这行慢

    result2 = [i ** 2 for i in range(10000)]  # 这行快

    return result, result2

# 运行: kernprof -l -v script.py
```

**输出示例**：
```
Line #  Hits    Time    Per Hit   % Time  Line Contents
=======================================================
     3                                    def analyze_me():
     4     1       2.0      2.0      0.0      result = []
     5 10001    5234.0      0.5     52.3      for i in range(10000):
     6 10000    4756.0      0.5     47.6          result.append(i ** 2)
     7     1      10.0     10.0      0.1      result2 = [i ** 2 for i in range(10000)]
```

---

#### 3. memory_profiler - 内存分析
```python
# 安装: pip install memory_profiler

from memory_profiler import profile

@profile
def memory_hog():
    """内存占用分析"""
    # ❌ 内存浪费
    big_list = [i for i in range(1000000)]

    # ✅ 内存优化（生成器）
    big_gen = (i for i in range(1000000))

    return sum(big_gen)

# 运行: python -m memory_profiler script.py
```

**输出示例**：
```
Line #  Mem usage  Increment  Line Contents
==============================================
     3   38.6 MiB   38.6 MiB  def memory_hog():
     4   76.3 MiB   37.7 MiB      big_list = [i for i in range(1000000)]
     5   76.3 MiB    0.0 MiB      big_gen = (i for i in range(1000000))
     6   76.3 MiB    0.0 MiB      return sum(big_gen)
```

---

### 17.2 性能优化技巧

#### 1. 列表推导式 vs 循环
```python
import timeit

# ❌ 慢：循环 + append
def loop_append():
    result = []
    for i in range(10000):
        result.append(i ** 2)
    return result

# ✅ 快：列表推导式
def list_comp():
    return [i ** 2 for i in range(10000)]

print("循环:", timeit.timeit(loop_append, number=1000))  # ~0.5s
print("推导:", timeit.timeit(list_comp, number=1000))    # ~0.3s (快 40%)
```

---

#### 2. 生成器节省内存
```python
import sys

# ❌ 内存占用大
big_list = [i for i in range(1000000)]
print(f"列表内存: {sys.getsizeof(big_list) / 1024 / 1024:.2f} MB")  # ~8 MB

# ✅ 内存占用小
big_gen = (i for i in range(1000000))
print(f"生成器内存: {sys.getsizeof(big_gen) / 1024:.2f} KB")  # ~0.1 KB
```

---

#### 3. 字典查找 vs 列表查找
```python
import timeit

# 创建测试数据
items = list(range(10000))
items_set = set(items)
items_dict = {i: True for i in items}

# ❌ 慢：列表查找 O(n)
def list_lookup():
    return 9999 in items

# ✅ 快：集合查找 O(1)
def set_lookup():
    return 9999 in items_set

# ✅ 快：字典查找 O(1)
def dict_lookup():
    return 9999 in items_dict

print("列表:", timeit.timeit(list_lookup, number=10000))   # ~0.5s
print("集合:", timeit.timeit(set_lookup, number=10000))    # ~0.001s (快 500 倍)
print("字典:", timeit.timeit(dict_lookup, number=10000))   # ~0.001s
```

---

#### 4. 字符串拼接优化
```python
import timeit

# ❌ 慢：+ 拼接（每次创建新字符串）
def string_concat():
    result = ""
    for i in range(1000):
        result += str(i)  # O(n²)
    return result

# ✅ 快：join()
def string_join():
    return "".join(str(i) for i in range(1000))  # O(n)

# ✅ 快：列表 + join
def list_join():
    parts = []
    for i in range(1000):
        parts.append(str(i))
    return "".join(parts)

print("拼接:", timeit.timeit(string_concat, number=1000))  # ~0.3s
print("join:", timeit.timeit(string_join, number=1000))    # ~0.1s (快 3 倍)
print("列表:", timeit.timeit(list_join, number=1000))      # ~0.1s
```

---

#### 5. 缓存计算结果
```python
from functools import lru_cache
import time

# ❌ 无缓存：重复计算
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# ✅ 使用缓存
@lru_cache(maxsize=128)
def fibonacci_cached(n):
    if n < 2:
        return n
    return fibonacci_cached(n - 1) + fibonacci_cached(n - 2)

# 性能对比
start = time.time()
fibonacci(30)
print(f"无缓存: {time.time() - start:.3f}s")  # ~0.3s

start = time.time()
fibonacci_cached(30)
print(f"有缓存: {time.time() - start:.6f}s")  # ~0.000030s (快 10000 倍)
```

---

### 17.3 NumPy 向量化优化

#### 纯 Python vs NumPy
```python
import numpy as np
import timeit

# ❌ 慢：纯 Python 循环
def python_sum():
    data = list(range(1000000))
    return sum(x ** 2 for x in data)

# ✅ 快：NumPy 向量化
def numpy_sum():
    data = np.arange(1000000)
    return np.sum(data ** 2)

print("Python:", timeit.timeit(python_sum, number=10))  # ~1.2s
print("NumPy:", timeit.timeit(numpy_sum, number=10))    # ~0.01s (快 120 倍)
```

---

### 17.4 数据库查询优化

#### 批量操作 vs 单条操作
```python
import sqlite3
import time

# ❌ 慢：单条插入
def slow_insert(conn):
    cursor = conn.cursor()
    for i in range(1000):
        cursor.execute("INSERT INTO users (name) VALUES (?)", (f"User{i}",))
    conn.commit()

# ✅ 快：批量插入
def fast_insert(conn):
    cursor = conn.cursor()
    data = [(f"User{i}",) for i in range(1000)]
    cursor.executemany("INSERT INTO users (name) VALUES (?)", data)
    conn.commit()

# 性能对比
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

start = time.time()
slow_insert(conn)
print(f"单条插入: {time.time() - start:.2f}s")  # ~0.5s

conn.execute("DELETE FROM users")

start = time.time()
fast_insert(conn)
print(f"批量插入: {time.time() - start:.2f}s")  # ~0.01s (快 50 倍)
```

---

### 17.5 C 扩展加速

#### 使用 Cython
```python
# setup.py
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("fast_module.pyx")
)

# fast_module.pyx
def fast_sum(int n):
    """Cython 优化函数"""
    cdef int i
    cdef long long result = 0

    for i in range(n):
        result += i * i

    return result

# 编译: python setup.py build_ext --inplace

# 使用
from fast_module import fast_sum
print(fast_sum(1000000))  # 比纯 Python 快 10-100 倍
```

---

## 第 18 章：调试技巧

### 18.1 pdb 调试器

#### 基础使用
```python
import pdb

def buggy_function(x, y):
    """有 bug 的函数"""
    pdb.set_trace()  # 设置断点

    result = x + y
    result = result * 2
    result = result / x  # 可能除以 0

    return result

# 运行时会进入调试模式
buggy_function(5, 10)
```

**常用 pdb 命令**：
```
(Pdb) h           # 帮助
(Pdb) n           # 下一行
(Pdb) s           # 进入函数
(Pdb) c           # 继续执行
(Pdb) p x         # 打印变量 x
(Pdb) pp locals() # 打印所有局部变量
(Pdb) l           # 显示当前代码
(Pdb) b 10        # 在第 10 行设置断点
(Pdb) q           # 退出
```

---

#### 条件断点
```python
import pdb

def process_items(items):
    """处理列表项"""
    for i, item in enumerate(items):
        # 仅当 item > 100 时中断
        if item > 100:
            pdb.set_trace()

        result = item * 2
        print(f"处理 {item} -> {result}")

process_items([10, 50, 150, 200])
```

---

#### Post-Mortem 调试（异常后调试）
```python
import pdb

def divide(x, y):
    return x / y

try:
    divide(10, 0)
except Exception:
    pdb.post_mortem()  # 在异常发生处进入调试器
```

---

### 18.2 日志调试

#### 详细日志记录
```python
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

logger = logging.getLogger(__name__)

def complex_function(data):
    """复杂函数"""
    logger.debug(f"输入数据: {data}")

    try:
        result = process_data(data)
        logger.info(f"处理成功: {result}")
        return result
    except Exception as e:
        logger.exception("处理失败")  # 自动记录堆栈信息
        raise

def process_data(data):
    logger.debug("开始处理数据")

    if not data:
        logger.warning("数据为空")
        return None

    logger.debug(f"数据长度: {len(data)}")
    return data.upper()
```

---

### 18.3 断言调试

#### 使用 assert
```python
def calculate_average(numbers):
    """计算平均值"""
    # 前置条件检查
    assert isinstance(numbers, list), "输入必须是列表"
    assert len(numbers) > 0, "列表不能为空"
    assert all(isinstance(n, (int, float)) for n in numbers), "所有元素必须是数字"

    total = sum(numbers)
    avg = total / len(numbers)

    # 后置条件检查
    assert min(numbers) <= avg <= max(numbers), "平均值超出范围"

    return avg

# ✅ 正常
print(calculate_average([1, 2, 3, 4, 5]))

# ❌ 触发断言
# calculate_average([])  # AssertionError: 列表不能为空
```

---

### 18.4 远程调试

#### 使用 pdb 远程调试
```python
# 服务器端（被调试程序）
import pdb
import sys

# 监听调试连接
pdb.Pdb(stdin=sys.stdin, stdout=sys.stdout).set_trace()

def server_function():
    x = 10
    y = 20
    result = x + y
    return result

server_function()
```

#### 使用 debugpy (VS Code 远程调试)
```python
import debugpy

# 启动调试服务器
debugpy.listen(("0.0.0.0", 5678))
print("等待调试器连接...")
debugpy.wait_for_client()  # 阻塞等待

# 之后的代码可以被远程调试
def main():
    x = 10
    y = 20
    result = x + y
    print(result)

main()
```

---

### 18.5 生产环境调试

#### 1. 错误追踪（Sentry 集成）
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-sentry-dsn",
    traces_sample_rate=1.0,
    environment="production"
)

def production_function():
    """生产环境函数"""
    try:
        # 业务逻辑
        result = risky_operation()
        return result
    except Exception as e:
        # 自动上报到 Sentry
        sentry_sdk.capture_exception(e)
        raise
```

---

#### 2. 性能监控
```python
import time
import logging

def performance_monitor(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        start = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start

            # 慢查询告警
            if elapsed > 1.0:
                logging.warning(
                    f"慢函数告警: {func.__name__} 耗时 {elapsed:.2f}s"
                )

            return result
        except Exception as e:
            elapsed = time.time() - start
            logging.error(
                f"函数异常: {func.__name__} 在 {elapsed:.2f}s 后失败"
            )
            raise

    return wrapper

@performance_monitor
def slow_api_call():
    time.sleep(2)
    return "完成"
```

---

## 第 19 章：常见陷阱与最佳实践

### 19.1 可变默认参数陷阱

#### ❌ 错误示例
```python
def append_to_list(item, target=[]):
    """❌ 危险：可变默认参数"""
    target.append(item)
    return target

# 问题：默认参数在函数定义时创建，所有调用共享同一个列表
print(append_to_list(1))  # [1]
print(append_to_list(2))  # [1, 2] ← 意外！
print(append_to_list(3))  # [1, 2, 3] ← 继续累积
```

#### ✅ 正确做法
```python
def append_to_list(item, target=None):
    """✅ 使用 None 作为默认值"""
    if target is None:
        target = []
    target.append(item)
    return target

print(append_to_list(1))  # [1]
print(append_to_list(2))  # [2] ← 正确
print(append_to_list(3))  # [3] ← 正确
```

---

### 19.2 闭包变量绑定陷阱

#### ❌ 错误示例
```python
# ❌ 所有函数引用同一个变量
functions = []
for i in range(3):
    functions.append(lambda: i)

print([f() for f in functions])  # [2, 2, 2] ← 意外！
```

#### ✅ 正确做法
```python
# ✅ 方式 1：使用默认参数
functions = []
for i in range(3):
    functions.append(lambda x=i: x)  # 立即绑定 i 的值

print([f() for f in functions])  # [0, 1, 2] ← 正确

# ✅ 方式 2：使用 functools.partial
from functools import partial

functions = []
for i in range(3):
    functions.append(partial(lambda x: x, i))

print([f() for f in functions])  # [0, 1, 2]
```

---

### 19.3 浅拷贝 vs 深拷贝

#### ❌ 浅拷贝陷阱
```python
import copy

original = [[1, 2], [3, 4]]

# ❌ 浅拷贝：嵌套对象仍然共享
shallow = copy.copy(original)
shallow[0][0] = 999

print(original)  # [[999, 2], [3, 4]] ← 意外修改！
print(shallow)   # [[999, 2], [3, 4]]
```

#### ✅ 深拷贝
```python
original = [[1, 2], [3, 4]]

# ✅ 深拷贝：完全独立
deep = copy.deepcopy(original)
deep[0][0] = 999

print(original)  # [[1, 2], [3, 4]] ← 未受影响
print(deep)      # [[999, 2], [3, 4]]
```

---

### 19.4 异常处理最佳实践

#### ❌ 过度捕获
```python
# ❌ 捕获所有异常（掩盖错误）
try:
    result = risky_operation()
except:
    pass  # 静默失败，难以调试
```

#### ✅ 精准捕获
```python
# ✅ 精准捕获预期异常
try:
    result = int(user_input)
except ValueError as e:
    logger.error(f"输入无效: {e}")
    result = 0  # 提供默认值
except Exception as e:
    logger.exception("未预期的错误")
    raise  # 重新抛出
```

---

### 19.5 资源管理最佳实践

#### ❌ 手动关闭资源
```python
# ❌ 容易忘记关闭
f = open("file.txt", "w")
f.write("data")
# 如果中间抛出异常，文件不会关闭
f.close()
```

#### ✅ 使用上下文管理器
```python
# ✅ 自动关闭资源
with open("file.txt", "w") as f:
    f.write("data")
# 退出 with 块时自动关闭

# ✅ 自定义上下文管理器
class DatabaseConnection:
    def __enter__(self):
        self.conn = connect_to_db()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()  # 自动关闭连接
        return False

with DatabaseConnection() as conn:
    conn.execute("SELECT * FROM users")
```

---

### 19.6 代码审查清单

#### 安全性检查
```python
# ✅ 永远不要在代码中硬编码密钥
# ❌ API_KEY = "sk-1234567890abcdef"
# ✅ API_KEY = os.getenv("API_KEY")

# ✅ 验证用户输入
def process_user_input(user_input):
    # ❌ eval(user_input)  # 极度危险！
    # ✅ 使用 ast.literal_eval() 或 json.loads()
    import ast
    try:
        data = ast.literal_eval(user_input)
    except (ValueError, SyntaxError):
        raise ValueError("输入无效")

    return data

# ✅ SQL 注入防护
# ❌ cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
# ✅ cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

---

#### 性能检查
```python
# ✅ 避免循环中的重复计算
# ❌
for item in items:
    if item in expensive_function():  # 每次循环都调用
        ...

# ✅
cached_result = expensive_function()
for item in items:
    if item in cached_result:
        ...

# ✅ 使用生成器处理大数据
# ❌
def read_large_file(path):
    with open(path) as f:
        return f.readlines()  # 全部加载到内存

# ✅
def read_large_file(path):
    with open(path) as f:
        for line in f:  # 逐行处理
            yield line.strip()
```

---

#### 可维护性检查
```python
# ✅ 函数单一职责
# ❌ 一个函数做太多事
def process_user_data_and_send_email(user_data):
    # 验证数据
    # 保存到数据库
    # 生成报告
    # 发送邮件
    pass

# ✅ 拆分为多个函数
def validate_user_data(user_data):
    ...

def save_to_database(user_data):
    ...

def generate_report(user_data):
    ...

def send_email(report):
    ...

# ✅ 使用类型提示
from typing import List, Dict, Optional

def process_users(users: List[Dict[str, str]]) -> Optional[int]:
    """
    处理用户列表

    Args:
        users: 用户字典列表

    Returns:
        处理的用户数量，失败返回 None
    """
    ...
```

---

### 19.7 Python 之禅（生产实践）

```python
import this  # 输出 "The Zen of Python"

"""
核心原则应用：

1. 明确优于隐晦
   ✅ def calculate_total(price, tax_rate):
   ❌ def calc(p, t):

2. 简单优于复杂
   ✅ if user.is_active:
   ❌ if user.status == "active" and user.deleted_at is None and not user.banned:

3. 扁平优于嵌套
   ❌ if a:
          if b:
              if c:
                  do_something()

   ✅ if not a:
          return
      if not b:
          return
      if not c:
          return
      do_something()

4. 可读性很重要
   ✅ SECONDS_IN_DAY = 86400
   ❌ magic_number = 86400

5. 错误不应被静默忽略
   ❌ try: ... except: pass
   ✅ try: ... except ValueError as e: logger.error(f"Error: {e}")

6. 面对歧义，拒绝猜测
   ✅ 使用明确的参数名: send_email(to="user@example.com", subject="Hello")
   ❌ send_email("user@example.com", "Hello")

7. 应该有一种——最好只有一种——明显的方法来做一件事
   ✅ 统一使用 pathlib 处理路径
   ❌ 混用 os.path 和 pathlib
"""
```

---

## 总结与学习路径

### 📚 已完成的知识体系

**第一部分：底层原理与执行机制（1-4 章）** ✅
- 字节码与执行流程
- 变量与命名空间
- 函数调用机制
- 模块与包管理

**第二部分：高级语言特性（5-8 章）** ✅
- 装饰器与元编程
- 上下文管理器
- 生成器与迭代器
- 异常处理与错误设计

**第三部分：工程化实践（9-12 章）** ✅
- 命令行参数解析
- 日志系统设计
- 配置管理与环境变量
- 单元测试与代码质量

**第四部分：DevOps 脚本编程（13-16 章）** ✅
- 系统调用与子进程管理
- 文件系统操作
- 网络编程基础
- 多线程与多进程

**第五部分：性能优化与调试（17-19 章）** ✅
- 性能分析与优化
- 调试技巧
- 常见陷阱与最佳实践

---

### 🎯 7 个月学习路线（Tesla 面试准备）

#### 第 1-2 月：Python 基础强化
- 深入理解底层原理（第 1-4 章）
- 掌握高级特性（第 5-8 章）
- **练习项目**：构建 CLI 工具、日志分析器

#### 第 3-4 月：DevOps 实战
- 系统编程（第 13-14 章）
- 网络编程（第 15 章）
- **练习项目**：
  - 批量服务器部署工具
  - 日志聚合系统
  - Docker 容器管理脚本

#### 第 5-6 月：并发与性能
- 多线程/多进程/异步（第 16 章）
- 性能优化（第 17 章）
- **练习项目**：
  - 高并发 HTTP 服务器
  - 分布式任务队列
  - 性能监控系统

#### 第 7 月：综合项目 + 面试准备
- 调试与最佳实践（第 18-19 章）
- **综合项目**：
  - 完整的微服务监控系统
  - CI/CD 自动化流水线
- **面试准备**：
  - LeetCode Python 题目
  - 系统设计案例
  - Tesla 面试真题

---

### 💡 关键能力清单

**核心技能**：
- ✅ 编写生产级 Python 脚本
- ✅ 自动化运维任务
- ✅ 性能分析与优化
- ✅ 并发编程
- ✅ 网络编程
- ✅ 系统集成

**软技能**：
- ✅ 代码审查能力
- ✅ 问题排查能力
- ✅ 文档编写能力
- ✅ 团队协作能力

---

**🎉 恭喜完成全部 19 章学习内容！现在您已经掌握了从底层原理到工程实践的完整 Python 脚本编程知识体系。**

**下一步建议**：
1. 选择感兴趣的章节深入实践
2. 构建个人项目组合（GitHub）
3. 参与开源项目
4. 准备 Tesla DevOps 岗位面试

**Good luck! 🚀**
