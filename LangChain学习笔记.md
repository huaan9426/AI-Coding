# LangChain 学习笔记

> 我的 AI 应用开发学习笔记 - LangChain 框架

---

## LangChain 是什么？

LangChain 就是一个**帮你快速搭建 AI 应用的工具箱**。

**用人话说：**
- 就像乐高积木，提供了一堆现成的"零件"
- 你可以把 GPT、文档、数据库这些东西快速组合起来
- 不用自己从零写复杂的代码

**官方定义：**
一个用于开发由大语言模型（LLM）驱动的应用程序的框架。

**版本：** langchain 1.0.7（已安装）

---

## 为什么需要 LangChain？

### 问题1：直接调用 GPT 很原始

```python
# 没有 LangChain，你得这样写：
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)

# 问题：
# - 每次都要处理 API 返回格式
# - 没有历史对话记忆
# - 不能读取文档、联网搜索
# - 没有错误重试机制
```

### 问题2：想让 AI 读 PDF 很麻烦

```python
# 传统做法：
# 1. 手动读 PDF（PyPDF2）
# 2. 手动切分文本（避免超过 token 限制）
# 3. 手动转成向量（调用 Embedding API）
# 4. 手动存向量数据库（写一堆代码）
# 5. 手动搜索相关内容
# 6. 手动拼接 prompt 发给 GPT
# 代码量 200+ 行，容易出错
```

### LangChain 的解决方案

✅ **封装好的组件** - 几行代码搞定复杂功能
✅ **链式调用** - 把多个步骤串起来自动执行
✅ **内置记忆** - 自动管理对话历史
✅ **多种数据源** - 支持 PDF、网页、数据库等
✅ **Agent 系统** - AI 自己决定调用什么工具
✅ **向量数据库集成** - 无缝对接 Chroma、FAISS 等

---

## LangChain 核心概念（必须理解）

### 1. LLM（大语言模型）- 大脑

```python
from langchain.llms import OpenAI

# 连接到 GPT
llm = OpenAI(temperature=0.7)  # temperature 控制创造性
response = llm("介绍一下 Python")
print(response)
```

**作用：** 接入各种 AI 模型（GPT、Claude、本地模型等）

---

### 2. Prompt Template（提示词模板）- 说话的方式

```python
from langchain.prompts import PromptTemplate

# 定义模板（带变量）
template = "请用{language}解释什么是{concept}"
prompt = PromptTemplate(template=template, input_variables=["language", "concept"])

# 使用
final_prompt = prompt.format(language="中文", concept="量子力学")
# 输出："请用中文解释什么是量子力学"
```

**作用：** 复用提示词，避免每次手写

---

### 3. Chain（链）- 流水线

把多个步骤串起来自动执行。

```python
from langchain.chains import LLMChain

# 创建一个链：模板 + 模型
chain = LLMChain(llm=llm, prompt=prompt)

# 一键执行
result = chain.run(language="中文", concept="黑洞")
# 自动：填充模板 → 发给 GPT → 返回结果
```

**作用：** 自动化多步骤流程

---

### 4. Document Loaders（文档加载器）- 读取各种文件

```python
from langchain.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader

# 读 PDF
pdf_loader = PyPDFLoader("report.pdf")
pdf_docs = pdf_loader.load()

# 读网页
web_loader = WebBaseLoader("https://example.com")
web_docs = web_loader.load()

# 读 txt
text_loader = TextLoader("notes.txt")
text_docs = text_loader.load()
```

**作用：** 统一接口读取各种格式的文档

---

### 5. Text Splitters（文本分割器）- 切成小块

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 一本书太长，GPT 读不完，需要切分
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # 每块 1000 字符
    chunk_overlap=200     # 块之间重叠 200 字符（避免信息丢失）
)

docs = splitter.split_documents(pdf_docs)
# 把长文档切成小块，每块都能让 GPT 处理
```

**作用：** 把长文档切成适合 GPT 处理的小块

---

### 6. Embeddings（嵌入）- 把文字变成数字

```python
from langchain.embeddings import OpenAIEmbeddings

# 把文字转成向量（一串数字）
embeddings = OpenAIEmbeddings()
vector = embeddings.embed_query("你好世界")
# 输出：[0.123, -0.456, 0.789, ...]（1536 个数字）
```

**为什么要变成数字？**
- 方便计算相似度
- "苹果好吃" 和 "苹果很美味" 的向量很接近
- 能用数学方法找到相关内容

---

### 7. Vector Stores（向量数据库）- 存储和搜索

```python
from langchain.vectorstores import Chroma

# 把文档存进向量数据库
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings
)

# 搜索相关内容
results = vectorstore.similarity_search("Python 是什么？", k=3)
# 自动找出最相关的 3 段内容
```

**作用：** 快速找到与问题相关的文档片段

---

### 8. Retrieval QA（检索问答）- 基于文档回答

```python
from langchain.chains import RetrievalQA

# 创建一个"能读文档回答问题"的 AI
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever()
)

# 提问
answer = qa_chain.run("这份报告的主要结论是什么？")
# 自动：搜索相关段落 → 发给 GPT → 生成答案
```

**作用：** 让 AI 基于你的文档回答问题

---

### 9. Memory（记忆）- 记住对话历史

```python
from langchain.memory import ConversationBufferMemory

# 创建记忆
memory = ConversationBufferMemory()

# 使用记忆的链
from langchain.chains import ConversationChain
conversation = ConversationChain(llm=llm, memory=memory)

# 多轮对话
conversation.run("我叫张三")
conversation.run("我叫什么名字？")  # AI会回答"张三"
```

**作用：** 让 AI 记住之前说过的话

---

### 10. Agents（智能体）- 自主决策

```python
from langchain.agents import load_tools, initialize_agent

# 给 AI 提供工具
tools = load_tools(["wikipedia", "calculator"], llm=llm)

# 创建智能体
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

# AI 会自己决定用什么工具
agent.run("2024年奥运会在哪里举办？那里的人口是多少的平方根？")
# AI 会：
# 1. 用 Wikipedia 查奥运会地点
# 2. 用 Wikipedia 查人口
# 3. 用 Calculator 算平方根
```

**作用：** AI 自己决定调用什么工具完成任务

---

## LangChain 完整工作流程

以"PDF 知识库聊天机器人"为例：

```
用户上传 PDF
    ↓
[Document Loader] 读取 PDF
    ↓
[Text Splitter] 切分成小块
    ↓
[Embeddings] 转成向量
    ↓
[Vector Store] 存入向量数据库
    ↓
用户提问："这份报告讲了什么？"
    ↓
[Retriever] 搜索相关片段
    ↓
[LLM] GPT 基于片段生成答案
    ↓
返回答案
```

---

## 实际代码示例：最小可用的 PDF 聊天机器人

```python
# 1. 导入所需库
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

# 2. 读取 PDF
loader = PyPDFLoader("report.pdf")
documents = loader.load()

# 3. 切分文本
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = splitter.split_documents(documents)

# 4. 创建向量数据库
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(docs, embeddings)

# 5. 创建问答链
llm = OpenAI(temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever()
)

# 6. 提问
answer = qa_chain.run("报告的主要内容是什么？")
print(answer)
```

**就这么简单！** 不到 20 行代码实现了 PDF 问答。

---

## LangChain 主要模块

| 模块 | 作用 | 常用类 |
|------|------|--------|
| **Models** | 连接各种 AI 模型 | OpenAI, ChatOpenAI, HuggingFace |
| **Prompts** | 管理提示词 | PromptTemplate, ChatPromptTemplate |
| **Chains** | 组合多个步骤 | LLMChain, RetrievalQA, ConversationChain |
| **Document Loaders** | 读取文档 | PyPDFLoader, WebBaseLoader, TextLoader |
| **Text Splitters** | 切分文本 | RecursiveCharacterTextSplitter |
| **Embeddings** | 文本向量化 | OpenAIEmbeddings, HuggingFaceEmbeddings |
| **Vector Stores** | 向量数据库 | Chroma, FAISS, Pinecone |
| **Memory** | 对话记忆 | ConversationBufferMemory |
| **Agents** | 智能决策 | initialize_agent, load_tools |

---

## LangChain 的依赖包（自动安装的 32 个包）

Poetry 安装 langchain 时自动安装了这些：

**核心依赖：**
- `langchain-core` - LangChain 核心功能
- `langsmith` - LangChain 监控和调试工具
- `langgraph` - 构建复杂 Agent 工作流
- `pydantic` - 数据验证（LangChain 大量使用）

**网络请求：**
- `httpx`, `requests` - 发送 HTTP 请求（调用 API）
- `certifi`, `urllib3` - HTTPS 安全连接

**数据处理：**
- `pyyaml` - 读取配置文件
- `jsonpatch`, `jsonpointer` - JSON 操作
- `orjson`, `ormsgpack` - 高速数据序列化

**其他工具：**
- `tenacity` - 自动重试机制
- `packaging` - 版本管理
- `xxhash`, `zstandard` - 数据压缩和哈希

---

## 常见使用场景

### 1. 聊天机器人

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

chat = ChatOpenAI()
messages = [
    SystemMessage(content="你是一个友好的助手"),
    HumanMessage(content="你好！")
]
response = chat(messages)
```

### 2. 文档问答（你的项目）

```python
# 已经在上面展示过完整代码
```

### 3. 数据分析

```python
from langchain.agents import create_pandas_dataframe_agent
import pandas as pd

df = pd.read_csv("sales.csv")
agent = create_pandas_dataframe_agent(llm, df)
agent.run("去年销售额最高的是哪个月？")
```

### 4. 联网搜索

```python
from langchain.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()
result = search.run("2024年AI最新进展")
```

### 5. 代码生成

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

template = "用 Python 写一个函数：{description}"
prompt = PromptTemplate(template=template, input_variables=["description"])
chain = LLMChain(llm=llm, prompt=prompt)
code = chain.run("计算斐波那契数列")
```

---

## LangChain vs 直接用 OpenAI API

| 维度 | 直接用 OpenAI API | 用 LangChain |
|------|------------------|-------------|
| 代码量 | 多（每个功能都要自己写） | 少（封装好的组件） |
| 学习成本 | 低（只需懂 API） | 中（需要学习框架概念） |
| 功能复杂度 | 简单场景够用 | 适合复杂应用 |
| 文档处理 | 需要自己写大量代码 | 几行代码搞定 |
| 向量数据库 | 手动集成 | 无缝对接 |
| Agent 功能 | 需要完全自己实现 | 内置支持 |
| 维护性 | 代码多，难维护 | 结构清晰，易维护 |

**建议：**
- 简单的 GPT 对话 → 直接用 API
- 复杂的 AI 应用（文档问答、Agent 等）→ 用 LangChain

---

## 环境变量配置

LangChain 需要 API 密钥：

```bash
# Mac/Linux
export OPENAI_API_KEY="sk-xxxxx"

# 或者在代码里设置
import os
os.environ["OPENAI_API_KEY"] = "sk-xxxxx"

# 推荐：创建 .env 文件
# .env
OPENAI_API_KEY=sk-xxxxx
```

然后在代码里加载：

```python
from dotenv import load_dotenv
load_dotenv()  # 自动读取 .env
```

---

## 进阶概念（以后学）

- **Chains 进阶：** SequentialChain, RouterChain
- **自定义工具：** 让 Agent 调用你自己的函数
- **LangGraph：** 构建复杂的多步骤工作流
- **LangSmith：** 监控和调试 LangChain 应用
- **本地模型：** 使用 Ollama 运行本地 LLM
- **流式输出：** 实时显示 AI 生成的内容
- **Few-shot Learning：** 给 AI 提供示例

---

## 学习路径建议

### 第 1 周：基础概念
- [ ] 理解 LLM、Prompt、Chain 的概念
- [ ] 尝试最简单的 LLM 调用
- [ ] 练习 PromptTemplate 的使用

### 第 2 周：文档处理
- [ ] 学习 Document Loaders
- [ ] 理解 Embeddings 和向量数据库
- [ ] 完成简单的 PDF 问答 Demo

### 第 3 周：记忆和对话
- [ ] 学习 Memory 机制
- [ ] 实现多轮对话机器人
- [ ] 理解不同的 Memory 类型

### 第 4 周：Agent 系统
- [ ] 理解 Agent 的工作原理
- [ ] 给 Agent 添加工具
- [ ] 完成一个能自主决策的 AI

---

## 常见错误和解决

### 1. API 密钥未设置

```
Error: No API key provided
解决：设置 OPENAI_API_KEY 环境变量
```

### 2. Token 超限

```
Error: Token limit exceeded
解决：使用 Text Splitter 切分文本
```

### 3. 向量数据库路径问题

```
Error: Permission denied
解决：检查 Chroma 的 persist_directory 权限
```

---

## 总结：一句话记住 LangChain

> **LangChain = 预制的 AI 应用积木，帮你快速搭建复杂的 GPT 应用**

**核心价值：**
1. 少写代码（封装好的组件）
2. 易于组合（链式调用）
3. 功能强大（文档、记忆、Agent）

---

## 下一步行动

- [ ] 创建第一个 LangChain 项目
- [ ] 实现 PDF 问答功能
- [ ] 添加对话记忆
- [ ] 尝试不同的向量数据库

---

**笔记创建时间：** 2025-11-19
**LangChain 版本：** 1.0.7
**依赖包数量：** 32 个（自动安装）
**用途：** AI 应用开发 - PDF 知识库聊天机器人
