# Python 基础语法笔记

> AI 应用开发必备 - 只讲最常用的，用最简单的话

---

## 📋 目录

1. [变量和赋值](#1-变量和赋值)
2. [数据类型](#2-数据类型)
3. [字符串操作](#3-字符串操作)
4. [列表](#4-列表)
5. [字典](#5-字典)
6. [导入模块](#6-导入模块)
7. [函数](#7-函数)
8. [类和对象](#8-类和对象)
9. [方法调用](#9-方法调用)
10. [条件判断](#10-条件判断)
11. [循环](#11-循环)
12. [文件操作](#12-文件操作)

---

## 1. 变量和赋值

### 一句话

**把值放进盒子里，盒子就是变量。**

### 语法

```python
变量名 = 值
```

### 解释

- `=` 是赋值符号（不是"等于"，是"把右边的值放进左边的变量"）
- 变量名自己起，见名知意
- Python 不需要声明类型，直接赋值就行

### 例子

```python
# 基本赋值
name = "张三"
age = 25
price = 99.5

# AI 开发中常见
model_name = "gpt-4"
temperature = 0.7
max_tokens = 1000

# 一次赋值多个
x, y, z = 1, 2, 3

# 交换变量
a, b = b, a
```

---

## 2. 数据类型

### 一句话

**不同类型的值，用法不同。**

### 常用类型

#### 2.1 字符串（str）- 文本

```python
# 语法：用引号包起来
text = "这是字符串"
text2 = '单引号也可以'
text3 = """三引号可以
换行写很长的文本"""

# AI 中的使用
prompt = "请用中文解释量子力学"
api_key = "sk-xxxxxxxxxxxxx"
```

#### 2.2 整数（int）- 数字

```python
# 语法：直接写数字
count = 100
age = 25

# AI 中的使用
max_tokens = 2000
chunk_size = 1000
```

#### 2.3 浮点数（float）- 小数

```python
# 语法：带小数点的数字
temperature = 0.7
price = 99.99

# AI 中的使用
similarity_score = 0.85
confidence = 0.92
```

#### 2.4 布尔值（bool）- 真/假

```python
# 语法：True 或 False（首字母大写）
is_active = True
has_error = False

# AI 中的使用
stream = True  # 是否流式输出
verbose = False  # 是否显示详细日志
```

#### 2.5 None - 空值

```python
# 语法：None 表示"没有值"
result = None

# AI 中的使用
error_message = None  # 没有错误时为 None
```

---

## 3. 字符串操作

### 一句话

**文本的各种玩法。**

### 3.1 字符串拼接

```python
# 方法1：用 +
first_name = "张"
last_name = "三"
full_name = first_name + last_name  # "张三"

# 方法2：用 f-string（推荐，AI 开发最常用）
name = "张三"
age = 25
message = f"我叫{name}，今年{age}岁"
# 输出："我叫张三，今年25岁"

# AI 中的使用
model = "gpt-4"
temp = 0.7
prompt = f"使用模型 {model}，温度 {temp}"
```

### 3.2 字符串格式化（占位符）

```python
# 方法1：format() 方法
template = "请用{language}解释{concept}"
result = template.format(language="中文", concept="AI")
# 输出："请用中文解释AI"

# 方法2：f-string（更简洁）
language = "中文"
concept = "AI"
result = f"请用{language}解释{concept}"
```

### 3.3 常用字符串方法

```python
text = "Hello World"

# 转大写
text.upper()  # "HELLO WORLD"

# 转小写
text.lower()  # "hello world"

# 去掉首尾空格
"  hello  ".strip()  # "hello"

# 替换
text.replace("World", "Python")  # "Hello Python"

# 分割成列表
"a,b,c".split(",")  # ["a", "b", "c"]

# 检查是否包含
"World" in text  # True
```

### AI 中的实际使用

```python
# 清理用户输入
user_input = "  什么是 AI？  "
clean_input = user_input.strip()

# 构建提示词
role = "Python老师"
question = "什么是变量"
prompt = f"你是{role}，回答问题：{question}"

# 处理文件路径
file_path = "data/documents/report.pdf"
file_name = file_path.split("/")[-1]  # "report.pdf"
```

---

## 4. 列表（List）

### 一句话

**一串有序的值，用方括号包起来。**

### 语法

```python
列表名 = [值1, 值2, 值3]
```

### 基本操作

```python
# 创建列表
numbers = [1, 2, 3, 4, 5]
names = ["张三", "李四", "王五"]
mixed = [1, "hello", 3.14, True]  # 可以混合类型

# 访问元素（索引从 0 开始）
numbers[0]  # 1（第一个）
numbers[2]  # 3（第三个）
numbers[-1]  # 5（最后一个）

# 修改元素
numbers[0] = 10
# numbers 变成 [10, 2, 3, 4, 5]

# 添加元素
numbers.append(6)  # 在末尾添加
# numbers 变成 [10, 2, 3, 4, 5, 6]

# 删除元素
numbers.remove(10)  # 删除值为 10 的元素

# 列表长度
len(numbers)  # 5

# 切片（取一部分）
numbers[1:3]  # [2, 3]（从索引1到3，不包括3）
numbers[:2]  # [10, 2]（前两个）
numbers[2:]  # [3, 4, 5]（从第三个到最后）
```

### AI 中的实际使用

```python
# 存储多个文档
documents = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

# 存储对话历史
chat_history = [
    "用户: 什么是AI？",
    "助手: AI是人工智能...",
    "用户: 能举个例子吗？"
]

# 存储搜索结果
search_results = [
    "结果1：...",
    "结果2：...",
    "结果3：..."
]

# 遍历列表处理每个文档
for doc in documents:
    print(f"处理文档：{doc}")

# 获取前3个结果
top_3 = search_results[:3]
```

---

## 5. 字典（Dictionary）

### 一句话

**键值对的集合，就像通讯录（名字对应电话）。**

### 语法

```python
字典名 = {"键1": 值1, "键2": 值2}
```

### 基本操作

```python
# 创建字典
person = {
    "name": "张三",
    "age": 25,
    "city": "北京"
}

# 访问值
person["name"]  # "张三"
person["age"]  # 25

# 添加/修改
person["email"] = "zhangsan@example.com"  # 添加
person["age"] = 26  # 修改

# 删除
del person["city"]

# 检查键是否存在
"name" in person  # True

# 获取所有键
person.keys()  # ["name", "age", "email"]

# 获取所有值
person.values()  # ["张三", 26, "zhangsan@example.com"]

# 安全获取（不存在返回默认值）
person.get("phone", "未提供")  # "未提供"
```

### AI 中的实际使用

```python
# API 配置
config = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "stream": True
}

# 访问配置
model_name = config["model"]
temp = config["temperature"]

# 对话消息
message = {
    "role": "user",
    "content": "什么是量子力学？"
}

# 文档元数据
doc_metadata = {
    "file_name": "report.pdf",
    "page_count": 50,
    "author": "张三",
    "created_at": "2025-01-01"
}

# 向量数据库查询结果
result = {
    "document": "...",
    "score": 0.85,
    "metadata": {"page": 3}
}
```

---

## 6. 导入模块

### 一句话

**把别人写好的代码拿来用。**

### 语法

```python
# 方式1：导入整个模块
import 模块名

# 方式2：导入模块中的特定内容
from 模块名 import 类名/函数名

# 方式3：导入并改名
import 模块名 as 别名
from 模块名 import 类名 as 别名
```

### 例子

```python
# 方式1：导入整个模块
import os
os.path.exists("file.txt")  # 使用时要加模块名

# 方式2：导入特定内容（推荐）
from os.path import exists
exists("file.txt")  # 直接用

# 方式3：改名（简化长名字）
import numpy as np
np.array([1, 2, 3])
```

### AI 中的实际使用

```python
# LangChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 文档处理
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 向量数据库
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# 标准库
import os  # 操作系统功能
import json  # JSON 处理
from dotenv import load_dotenv  # 加载环境变量
```

---

## 7. 函数

### 一句话

**把重复的代码打包起来，起个名字，需要时调用。**

### 语法

```python
# 定义函数
def 函数名(参数1, 参数2):
    # 函数体
    return 返回值

# 调用函数
结果 = 函数名(值1, 值2)
```

### 基本例子

```python
# 无参数无返回值
def say_hello():
    print("你好！")

say_hello()  # 调用

# 有参数有返回值
def add(a, b):
    result = a + b
    return result

sum_result = add(3, 5)  # 8

# 默认参数
def greet(name, greeting="你好"):
    return f"{greeting}, {name}!"

greet("张三")  # "你好, 张三!"
greet("张三", "早上好")  # "早上好, 张三!"

# 关键字参数
def create_user(name, age, city):
    return {"name": name, "age": age, "city": city}

user = create_user(name="张三", age=25, city="北京")
```

### AI 中的实际使用

```python
# 加载文档
def load_pdf(file_path):
    from langchain.document_loaders import PyPDFLoader
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return documents

# 切分文档
def split_documents(documents, chunk_size=1000):
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size)
    chunks = splitter.split_documents(documents)
    return chunks

# 调用 GPT
def ask_gpt(question, temperature=0.7):
    from langchain.llms import OpenAI
    llm = OpenAI(temperature=temperature)
    answer = llm(question)
    return answer

# 使用
docs = load_pdf("report.pdf")
chunks = split_documents(docs, chunk_size=500)
answer = ask_gpt("什么是AI？", temperature=0.5)
```

---

## 8. 类和对象

### 一句话

**类是蓝图，对象是根据蓝图造出来的实物。**

### 核心概念

```python
# 类定义（蓝图）
class Car:
    def __init__(self, brand, color):  # 构造函数
        self.brand = brand  # 属性
        self.color = color

    def drive(self):  # 方法
        print(f"{self.color}的{self.brand}开动了")

# 创建对象（造车）
my_car = Car("丰田", "红色")
your_car = Car("本田", "蓝色")

# 访问属性
print(my_car.brand)  # "丰田"
print(my_car.color)  # "红色"

# 调用方法
my_car.drive()  # "红色的丰田开动了"
```

### AI 中的理解（你不需要写类，只需要会用）

```python
# LangChain 已经定义好了类，你只需要用

# 例子1：创建 LLM 对象
from langchain.llms import OpenAI
llm = OpenAI(temperature=0.7)  # 创建对象
response = llm("你好")  # 调用对象

# 例子2：创建 PromptTemplate 对象
from langchain.prompts import PromptTemplate
template = "请用{language}解释{concept}"
prompt = PromptTemplate(
    template=template,
    input_variables=["language", "concept"]
)
result = prompt.format(language="中文", concept="AI")

# 例子3：创建向量数据库对象
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings()
)
```

**你需要理解的：**
- `OpenAI(...)` = 创建对象
- `llm(...)` = 调用对象（对象可以像函数一样被调用）
- `prompt.format(...)` = 调用对象的方法

---

## 9. 方法调用

### 一句话

**对象自带的功能，用 `.` 调用。**

### 语法

```python
对象.方法名(参数)
```

### 字符串方法

```python
text = "hello world"
text.upper()  # "HELLO WORLD"
text.split(" ")  # ["hello", "world"]
```

### 列表方法

```python
numbers = [1, 2, 3]
numbers.append(4)  # 添加元素
numbers.remove(2)  # 删除元素
```

### 链式调用（方法返回对象，继续调用）

```python
text = "  Hello World  "
result = text.strip().lower().replace("world", "python")
# "hello python"

# 拆解：
# 1. text.strip() → "Hello World"
# 2. .lower() → "hello world"
# 3. .replace(...) → "hello python"
```

### AI 中的实际使用

```python
# 文档加载和处理（链式调用）
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = PyPDFLoader("report.pdf")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
chunks = splitter.split_documents(documents)

# 向量数据库操作
vectorstore.similarity_search("查询内容", k=3)  # 搜索相似文档
vectorstore.add_documents(new_docs)  # 添加文档

# LangChain 链式操作
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(language="中文", concept="AI")
```

---

## 10. 条件判断

### 一句话

**根据条件决定做什么。**

### 语法

```python
if 条件:
    # 条件为真时执行
elif 另一个条件:
    # 第二个条件为真时执行
else:
    # 都不满足时执行
```

### 基本例子

```python
age = 18

if age >= 18:
    print("成年人")
else:
    print("未成年")

# 多条件
score = 85

if score >= 90:
    print("优秀")
elif score >= 80:
    print("良好")
elif score >= 60:
    print("及格")
else:
    print("不及格")
```

### 常用条件表达式

```python
# 比较
x == y  # 等于
x != y  # 不等于
x > y   # 大于
x < y   # 小于
x >= y  # 大于等于
x <= y  # 小于等于

# 逻辑运算
a and b  # 并且（都为真才为真）
a or b   # 或者（有一个为真就为真）
not a    # 非（取反）

# 成员判断
"a" in "abc"  # True（字符串包含）
"d" in "abc"  # False
3 in [1, 2, 3]  # True（列表包含）

# 判断空值
x is None
x is not None
```

### AI 中的实际使用

```python
# 检查 API 密钥
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    print("请设置 API 密钥")
else:
    llm = OpenAI(api_key=api_key)

# 根据文件类型选择加载器
if file_path.endswith(".pdf"):
    loader = PyPDFLoader(file_path)
elif file_path.endswith(".txt"):
    loader = TextLoader(file_path)
else:
    print("不支持的文件类型")

# 检查搜索结果
results = vectorstore.similarity_search(query, k=3)
if len(results) == 0:
    print("没有找到相关文档")
else:
    print(f"找到 {len(results)} 个相关文档")

# 根据相似度筛选
for result in results:
    if result.metadata["score"] > 0.8:
        print("高相关度文档")
```

---

## 11. 循环

### 一句话

**重复做同一件事。**

### 11.1 for 循环（遍历列表）

```python
# 语法
for 变量 in 列表:
    # 对每个元素执行的代码
```

```python
# 基本例子
names = ["张三", "李四", "王五"]
for name in names:
    print(name)
# 输出：
# 张三
# 李四
# 王五

# 遍历数字
for i in range(5):  # range(5) 生成 [0, 1, 2, 3, 4]
    print(i)

# 遍历字典
person = {"name": "张三", "age": 25}
for key, value in person.items():
    print(f"{key}: {value}")
# 输出：
# name: 张三
# age: 25
```

### 11.2 while 循环（满足条件就继续）

```python
# 语法
while 条件:
    # 条件为真时执行
```

```python
# 基本例子
count = 0
while count < 5:
    print(count)
    count += 1  # count = count + 1
# 输出：0 1 2 3 4
```

### AI 中的实际使用

```python
# 处理多个文档
pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
all_documents = []

for file in pdf_files:
    loader = PyPDFLoader(file)
    docs = loader.load()
    all_documents.extend(docs)  # 添加到总列表
    print(f"已处理：{file}")

# 切分所有文档
splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
all_chunks = []

for doc in all_documents:
    chunks = splitter.split_documents([doc])
    all_chunks.extend(chunks)

# 批量向量化
for i in range(0, len(all_chunks), 100):  # 每次处理100个
    batch = all_chunks[i:i+100]
    vectorstore.add_documents(batch)
    print(f"已向量化 {i+100} 个文档块")

# 搜索结果处理
results = vectorstore.similarity_search(query, k=5)
for i, result in enumerate(results):  # enumerate 获取索引和值
    print(f"结果 {i+1}:")
    print(result.page_content[:100])  # 打印前100字符
```

---

## 12. 文件操作

### 一句话

**读写电脑上的文件。**

### 12.1 读取文件

```python
# 语法
with open("文件路径", "r", encoding="utf-8") as f:
    content = f.read()
```

```python
# 读取整个文件
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print(content)

# 按行读取
with open("data.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())  # strip() 去掉换行符

# 读取所有行到列表
with open("data.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()  # 返回列表
```

### 12.2 写入文件

```python
# 语法
with open("文件路径", "w", encoding="utf-8") as f:
    f.write("内容")
```

```python
# 写入（覆盖原内容）
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("这是第一行\n")
    f.write("这是第二行\n")

# 追加（保留原内容）
with open("output.txt", "a", encoding="utf-8") as f:
    f.write("追加一行\n")
```

### 12.3 JSON 文件

```python
import json

# 写入 JSON
data = {"name": "张三", "age": 25}
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 读取 JSON
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    print(data["name"])  # "张三"
```

### AI 中的实际使用

```python
# 加载 API 密钥
from dotenv import load_dotenv
import os
load_dotenv()  # 从 .env 文件加载
api_key = os.getenv("OPENAI_API_KEY")

# 读取提示词模板
with open("prompts/qa_template.txt", "r", encoding="utf-8") as f:
    template = f.read()

# 保存对话历史
chat_history = [
    {"role": "user", "content": "什么是AI？"},
    {"role": "assistant", "content": "AI是人工智能..."}
]
with open("history.json", "w", encoding="utf-8") as f:
    json.dump(chat_history, f, ensure_ascii=False, indent=2)

# 批量处理文本文件
import os
txt_files = [f for f in os.listdir("documents") if f.endswith(".txt")]
for file in txt_files:
    with open(f"documents/{file}", "r", encoding="utf-8") as f:
        content = f.read()
        # 处理 content...
```

---

## 13. 常见模式速查

### 模式1：配置字典

```python
# AI 应用配置
config = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "stream": False
}

# 使用
llm = OpenAI(**config)  # ** 解包字典为参数
```

### 模式2：列表推导式（快速创建列表）

```python
# 基本语法
新列表 = [表达式 for 变量 in 旧列表]

# 例子
numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers]  # [1, 4, 9, 16, 25]

# 带条件
evens = [x for x in numbers if x % 2 == 0]  # [2, 4]

# AI 中的使用
pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
file_paths = [f"documents/{file}" for file in pdf_files]
# ["documents/doc1.pdf", "documents/doc2.pdf", ...]
```

### 模式3：异常处理

```python
# 语法
try:
    # 可能出错的代码
except 错误类型:
    # 出错后的处理
```

```python
# 基本例子
try:
    result = 10 / 0
except ZeroDivisionError:
    print("不能除以0")

# AI 中的使用
try:
    llm = OpenAI(api_key=api_key)
    response = llm("你好")
except Exception as e:
    print(f"调用失败：{e}")

# 文件操作
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("配置文件不存在")
    config = {}  # 使用默认配置
```

### 模式4：环境变量

```python
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取环境变量
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("MODEL", "gpt-3.5-turbo")  # 提供默认值

# 检查
if not api_key:
    raise ValueError("请设置 OPENAI_API_KEY")
```

---

## 14. AI 开发常用代码片段

### 片段1：初始化 LangChain

```python
import os
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

# 加载 API 密钥
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 创建 LLM
llm = OpenAI(temperature=0.7)
# 或使用聊天模型
chat = ChatOpenAI(model="gpt-4", temperature=0.7)
```

### 片段2：加载和处理 PDF

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 加载 PDF
loader = PyPDFLoader("document.pdf")
documents = loader.load()

# 切分文档
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(documents)

print(f"切分为 {len(chunks)} 个文档块")
```

### 片段3：创建向量数据库

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# 创建向量数据库
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"  # 持久化保存
)

# 搜索
results = vectorstore.similarity_search("查询内容", k=3)
for result in results:
    print(result.page_content)
```

### 片段4：问答链

```python
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

# 创建问答链
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(temperature=0),
    retriever=vectorstore.as_retriever(),
    return_source_documents=True
)

# 提问
question = "这份文档的主要内容是什么？"
result = qa_chain({"query": question})

print("答案：", result["result"])
print("来源：", result["source_documents"])
```

### 片段5：对话记忆

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# 创建记忆
memory = ConversationBufferMemory()

# 创建对话链
conversation = ConversationChain(
    llm=llm,
    memory=memory
)

# 多轮对话
response1 = conversation.run("我叫张三")
response2 = conversation.run("我叫什么名字？")  # 会记得"张三"
```

---

## 15. 调试技巧

### 技巧1：打印变量

```python
# 查看变量值
name = "张三"
print(name)

# 查看类型
print(type(name))  # <class 'str'>

# 查看对象所有属性和方法
print(dir(name))

# f-string 调试
print(f"name = {name}")
print(f"len(name) = {len(name)}")
```

### 技巧2：检查步骤

```python
# 处理流程中加打印
print("1. 开始加载文档...")
documents = loader.load()
print(f"   加载了 {len(documents)} 个文档")

print("2. 开始切分...")
chunks = splitter.split_documents(documents)
print(f"   切分为 {len(chunks)} 个块")

print("3. 开始向量化...")
vectorstore = Chroma.from_documents(chunks, embeddings)
print("   向量化完成")
```

### 技巧3：查看对象内容

```python
# 查看列表
print(f"列表长度: {len(my_list)}")
print(f"前3个: {my_list[:3]}")

# 查看字典
print(f"字典键: {config.keys()}")
print(f"字典内容: {config}")

# 查看文档内容
print(f"文档内容前100字: {document.page_content[:100]}")
print(f"文档元数据: {document.metadata}")
```

---

## 总结

### 必须掌握（马上就会用到）

- ✅ **变量赋值**：`x = 10`
- ✅ **字符串**：`"文本"` 和 `f"变量{x}"`
- ✅ **字典**：`{"key": "value"}`
- ✅ **列表**：`[1, 2, 3]`
- ✅ **导入**：`from xxx import yyy`
- ✅ **方法调用**：`对象.方法()`
- ✅ **for 循环**：`for x in list:`

### 慢慢学（以后会用到）

- ⏳ **函数定义**：`def function():`
- ⏳ **条件判断**：`if/elif/else`
- ⏳ **类和对象**：理解概念即可
- ⏳ **异常处理**：`try/except`

### 学习方法

1. **先看例子，再理解语法**
2. **不要记语法，多写几遍自然就会**
3. **遇到不懂的就搜索或问我**
4. **从简单改起，慢慢学会写新代码**

---

**笔记创建时间：** 2025-11-19
**用途：** AI 应用开发 Python 基础
**建议：** 边做项目边查这份笔记，用到哪个查哪个
