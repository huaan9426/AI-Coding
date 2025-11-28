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

*（由于内容太长，这里先提供前半部分。是否继续生成后续章节？）*

**已完成章节**：
- ✅ 第一部分：底层原理与执行机制（1-4 章）
- ✅ 第二部分：高级语言特性（5-8 章）
- ✅ 第三部分：工程化实践（9-10 章）

**待生成章节**：
- ⏳ 第三部分续：配置管理、单元测试（11-12 章）
- ⏳ 第四部分：DevOps 脚本编程（13-16 章）
- ⏳ 第五部分：性能优化与调试（17-19 章）

**请告诉我是否继续生成剩余内容？** 🚀
