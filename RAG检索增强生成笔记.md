# RAG 检索增强生成学习笔记

> 让 AI 基于你的文档回答问题 - 不瞎编，有依据

---

## 📋 目录

1. [RAG 是什么](#1-rag-是什么)
2. [为什么需要 RAG](#2-为什么需要-rag)
3. [RAG 工作流程](#3-rag-工作流程)
4. [核心组件详解](#4-核心组件详解)
5. [向量化（Embedding）](#5-向量化embedding)
6. [向量数据库](#6-向量数据库)
7. [检索策略](#7-检索策略)
8. [完整实现案例](#8-完整实现案例)
9. [优化技巧](#9-优化技巧)
10. [常见问题](#10-常见问题)

---

## 1. RAG 是什么

### 一句话

**RAG = 先搜索相关内容，再让 AI 基于搜索结果回答。**

### 全称

**RAG = Retrieval-Augmented Generation（检索增强生成）**

### 形象比喻

**传统 LLM（裸 GPT）：**
```
你：2023年公司营收是多少？
AI：我猜大概是... [胡说八道，因为没训练过你公司的数据]
```

**RAG：**
```
你：2023年公司营收是多少？

系统：
1. 搜索相关文档 → 找到《2023年财报.pdf》第3页
2. 提取内容："2023年营收1.2亿元"
3. 把内容给 AI → AI说："根据文档，2023年营收1.2亿元"

AI：根据财报，2023年公司营收为1.2亿元。[有依据，不瞎编]
```

### 核心价值

- ✅ **不瞎编** - AI 基于你的文档回答
- ✅ **实时更新** - 文档更新，答案就更新
- ✅ **可追溯** - 知道答案来源于哪份文档
- ✅ **私有数据** - 处理公司内部文档、个人笔记

---

## 2. 为什么需要 RAG

### 问题1：LLM 的知识有截止日期

```python
# GPT-4 的训练数据截止到 2023年4月
你问："2024年奥运会在哪里举办？"
GPT-4："我的知识截止到2023年4月，无法回答。"
```

**RAG 解决方案：**
```python
# 你上传最新新闻文档
文档："2024年奥运会将在巴黎举办"

# RAG 系统
1. 搜索文档 → 找到相关内容
2. AI 基于文档回答："2024年奥运会在巴黎举办"
```

---

### 问题2：LLM 不知道你的私有数据

```python
你问："我们公司的请假流程是什么？"
GPT-4："我不知道贵公司的具体流程..."
```

**RAG 解决方案：**
```python
# 你上传《员工手册.pdf》
文档："请假流程：1. 填写申请单 2. 主管审批 3. HR备案"

# RAG 系统
AI："根据员工手册，请假流程为：1. 填写申请单..."
```

---

### 问题3：LLM 会"幻觉"（编造事实）

```python
你问："张三的电话是多少？"
GPT-4："138-xxxx-xxxx"  [随便编的，完全错误]
```

**RAG 解决方案：**
```python
# 你上传通讯录
文档："张三 - 139-1234-5678"

# RAG 系统
AI："根据通讯录，张三的电话是 139-1234-5678"
```

---

## 3. RAG 工作流程

### 3.1 完整流程图

```
┌─────────────────────────────────────────────────────────┐
│                    离线处理（准备阶段）                     │
└─────────────────────────────────────────────────────────┘

你的文档（PDF、Word、网页...）
    ↓
【1. 文档加载】
    ↓
完整文档内容
    ↓
【2. 文本切分】
    ↓
文档块1  文档块2  文档块3  文档块4 ...
    ↓
【3. 向量化（Embedding）】
    ↓
向量1   向量2   向量3   向量4 ...
    ↓
【4. 存入向量数据库】
    ↓
向量数据库（Chroma / FAISS / Pinecone）


┌─────────────────────────────────────────────────────────┐
│                    在线处理（查询阶段）                     │
└─────────────────────────────────────────────────────────┘

用户提问："2023年营收是多少？"
    ↓
【5. 问题向量化】
    ↓
问题向量
    ↓
【6. 向量相似度搜索】在向量数据库中查找最相似的文档块
    ↓
找到最相关的 3 个文档块
    ↓
【7. 构建 Prompt】
    ↓
"根据以下内容回答问题：
 内容1：...
 内容2：...
 内容3：...
 问题：2023年营收是多少？"
    ↓
【8. 调用 LLM】
    ↓
AI 回答："根据财报，2023年营收1.2亿元"
    ↓
返回给用户
```

---

### 3.2 两个关键阶段

#### 阶段1：离线处理（一次性，准备知识库）

```python
# 步骤1：加载文档
from langchain.document_loaders import PyPDFLoader
loader = PyPDFLoader("company_report.pdf")
documents = loader.load()

# 步骤2：切分文档
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# 步骤3：向量化并存储
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)
```

#### 阶段2：在线查询（每次问答时执行）

```python
# 步骤1：用户提问
question = "2023年营收是多少？"

# 步骤2：检索相关文档
relevant_docs = vectorstore.similarity_search(question, k=3)

# 步骤3：构建 Prompt 并调用 LLM
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0),
    retriever=vectorstore.as_retriever()
)

answer = qa_chain.run(question)
print(answer)
```

---

## 4. 核心组件详解

### 4.1 Document Loaders（文档加载器）

**作用：** 把各种格式的文件读成统一的文本格式

#### PDF 文件
```python
from langchain.document_loaders import PyPDFLoader

loader = PyPDFLoader("report.pdf")
documents = loader.load()

# 每个 document 包含：
# - page_content: 文本内容
# - metadata: {'source': 'report.pdf', 'page': 1}
```

#### Word 文档
```python
from langchain.document_loaders import UnstructuredWordDocumentLoader

loader = UnstructuredWordDocumentLoader("doc.docx")
documents = loader.load()
```

#### 网页
```python
from langchain.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://example.com")
documents = loader.load()
```

#### 纯文本
```python
from langchain.document_loaders import TextLoader

loader = TextLoader("notes.txt")
documents = loader.load()
```

#### 多个文件（文件夹）
```python
from langchain.document_loaders import DirectoryLoader

loader = DirectoryLoader("./docs", glob="**/*.pdf")
documents = loader.load()
```

---

### 4.2 Text Splitters（文本切分器）

**作用：** 把长文档切成小块（因为 LLM 有 token 限制）

#### 为什么要切分？

```
原文档：20页PDF，约30000字
→ GPT-3.5 最多处理 4096 tokens（约3000字）
→ 必须切分成小块
```

#### RecursiveCharacterTextSplitter（推荐）

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # 每块最多 1000 字符
    chunk_overlap=200,     # 块之间重叠 200 字符
    length_function=len,   # 用什么函数计算长度
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]  # 优先在这些地方切分
)

chunks = splitter.split_documents(documents)
```

**参数解释：**
- `chunk_size=1000` - 每块大小
- `chunk_overlap=200` - 重叠部分（避免切断完整信息）

**为什么要重叠？**
```
文档：...公司2023年营收1.2亿元，比去年增长20%...

不重叠切分：
块1："...公司2023年营收1.2"
块2："亿元，比去年增长20%..."
→ "1.2亿元"被切断了！

重叠切分：
块1："...公司2023年营收1.2亿元，比去"
块2："营收1.2亿元，比去年增长20%..."
→ 完整信息被保留在两个块中
```

#### CharacterTextSplitter（简单切分）

```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    separator="\n",       # 按换行切分
    chunk_size=1000,
    chunk_overlap=200
)
```

#### 按 Token 切分（精确控制）

```python
from langchain.text_splitter import TokenTextSplitter

splitter = TokenTextSplitter(
    chunk_size=500,       # 每块 500 tokens
    chunk_overlap=50
)
```

---

## 5. 向量化（Embedding）

### 5.1 什么是向量化

**一句话：** 把文字变成一串数字（向量），让计算机能比较相似度。

**形象理解：**
```
文字："苹果很好吃"
向量：[0.2, -0.5, 0.8, 0.1, ..., 0.3]（1536个数字）

文字："苹果味道不错"
向量：[0.19, -0.48, 0.82, 0.09, ..., 0.28]

比较两个向量 → 发现很相似（因为意思接近）
```

**为什么需要向量？**
```
问题："公司去年赚了多少钱？"
文档1："2023年公司营收1.2亿元"
文档2："公司产品介绍..."

怎么知道文档1更相关？
→ 把问题和文档都变成向量
→ 计算向量相似度
→ 文档1的向量和问题更接近
```

---

### 5.2 常用 Embedding 模型

#### OpenAI Embeddings（推荐）

```python
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"  # 新模型，便宜快速
)

# 文字 → 向量
text = "苹果很好吃"
vector = embeddings.embed_query(text)
print(len(vector))  # 1536 个数字
```

**OpenAI Embedding 模型对比：**
| 模型 | 向量维度 | 价格 | 适用场景 |
|------|---------|------|---------|
| text-embedding-3-small | 1536 | $0.02 / 1M tokens | 日常使用（推荐） |
| text-embedding-3-large | 3072 | $0.13 / 1M tokens | 高精度要求 |
| text-embedding-ada-002 | 1536 | $0.10 / 1M tokens | 旧模型 |

#### 本地 Embeddings（免费）

```python
from langchain.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 优点：免费，离线可用
# 缺点：效果略差，需要下载模型
```

#### 中文 Embeddings

```python
# 使用中文优化的模型
embeddings = HuggingFaceEmbeddings(
    model_name="shibing624/text2vec-base-chinese"
)
```

---

### 5.3 向量相似度计算

**核心原理：** 计算两个向量的夹角（余弦相似度）

```python
import numpy as np

# 两个向量
vec1 = np.array([0.2, 0.5, 0.8])
vec2 = np.array([0.19, 0.48, 0.82])

# 计算余弦相似度
similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
print(similarity)  # 0.999（非常相似）

# 相似度范围：-1 到 1
# 1 = 完全相同
# 0 = 无关
# -1 = 完全相反
```

**实际应用：**
```python
# 问题向量
question_vec = embeddings.embed_query("2023年营收多少？")

# 文档向量
doc1_vec = embeddings.embed_query("2023年营收1.2亿元")
doc2_vec = embeddings.embed_query("公司地址在北京")

# 计算相似度
similarity1 = cosine_similarity(question_vec, doc1_vec)  # 0.85（高）
similarity2 = cosine_similarity(question_vec, doc2_vec)  # 0.12（低）

# 结论：doc1 更相关
```

---

## 6. 向量数据库

### 6.1 什么是向量数据库

**一句话：** 专门存储向量并快速搜索相似向量的数据库。

**和普通数据库的区别：**
| 对比 | 普通数据库 | 向量数据库 |
|------|-----------|-----------|
| 存储 | 文字、数字 | 向量（数组） |
| 查询 | 精确匹配 | 相似度搜索 |
| 例子 | `SELECT * WHERE name='张三'` | `找出与[0.2, 0.5, ...]最相似的10个向量` |

---

### 6.2 Chroma（推荐：本地使用）

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# 创建向量数据库
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents=chunks,                  # 文档块列表
    embedding=embeddings,              # 向量化模型
    persist_directory="./chroma_db"   # 保存到磁盘（可选）
)

# 持久化保存
vectorstore.persist()

# 下次加载
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
```

**优点：**
- ✅ 简单易用
- ✅ 本地存储（不需要服务器）
- ✅ 免费开源
- ✅ 支持持久化

**缺点：**
- ⚠️ 单机使用，不支持分布式
- ⚠️ 数据量大（百万级）时性能下降

---

### 6.3 FAISS（推荐：高性能）

```python
from langchain.vectorstores import FAISS

# 创建向量数据库
vectorstore = FAISS.from_documents(chunks, embeddings)

# 保存到本地
vectorstore.save_local("faiss_index")

# 加载
vectorstore = FAISS.load_local("faiss_index", embeddings)
```

**优点：**
- ✅ Meta 开发，性能极高
- ✅ 支持超大规模（亿级）
- ✅ 免费开源

**缺点：**
- ⚠️ 只在内存中（需要手动持久化）
- ⚠️ 配置稍复杂

---

### 6.4 Pinecone（推荐：云服务）

```python
from langchain.vectorstores import Pinecone
import pinecone

# 初始化
pinecone.init(api_key="your-api-key", environment="us-west1-gcp")

# 创建索引
index_name = "my-index"
vectorstore = Pinecone.from_documents(chunks, embeddings, index_name=index_name)
```

**优点：**
- ✅ 全托管，无需维护
- ✅ 支持超大规模
- ✅ 分布式，高可用

**缺点：**
- ❌ 收费（免费版有限制）
- ❌ 需要联网

---

### 6.5 对比总结

| 数据库 | 适用场景 | 价格 | 数据规模 |
|--------|---------|------|---------|
| **Chroma** | 个人项目、原型开发 | 免费 | 小到中（10万级） |
| **FAISS** | 高性能需求、离线使用 | 免费 | 大（百万到亿级） |
| **Pinecone** | 生产环境、需要高可用 | 收费 | 任意规模 |
| **Qdrant** | 需要细粒度控制 | 免费/收费 | 任意规模 |
| **Weaviate** | 复杂查询、图谱集成 | 免费/收费 | 任意规模 |

---

## 7. 检索策略

### 7.1 基础检索（Similarity Search）

```python
# 最简单：找最相似的 k 个文档
results = vectorstore.similarity_search(
    query="2023年营收多少？",
    k=3  # 返回最相关的 3 个文档块
)

for doc in results:
    print(doc.page_content)
    print(doc.metadata)
```

---

### 7.2 带相似度分数的检索

```python
# 返回文档和相似度分数
results = vectorstore.similarity_search_with_score(
    query="2023年营收多少？",
    k=5
)

for doc, score in results:
    print(f"相似度：{score}")
    print(f"内容：{doc.page_content[:100]}")
    print("---")

# 可以根据分数过滤
filtered = [(doc, score) for doc, score in results if score > 0.8]
```

---

### 7.3 MMR（最大边际相关性）

**问题：** 相似度搜索可能返回重复内容

```python
# 问题："介绍一下Python"
# 相似度搜索返回：
文档1："Python是一种编程语言..."
文档2："Python是编程语言..."
文档3："Python是一门编程语言..."
# 三个文档内容几乎一样！
```

**MMR 解决方案：** 平衡相关性和多样性

```python
results = vectorstore.max_marginal_relevance_search(
    query="介绍Python",
    k=3,
    fetch_k=10,  # 先找 10 个相关的
    lambda_mult=0.5  # 多样性权重（0=只要多样性，1=只要相关性）
)

# 返回的 3 个文档：
文档1："Python是编程语言..."
文档2："Python的历史..."（不同角度）
文档3："Python的应用场景..."（更多样化）
```

---

### 7.4 混合检索（Hybrid Search）

**结合关键词搜索和向量搜索**

```python
from langchain.retrievers import BM25Retriever, EnsembleRetriever

# 向量检索器
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 关键词检索器（BM25）
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 3

# 混合检索器
ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.5, 0.5]  # 各占 50%
)

results = ensemble_retriever.get_relevant_documents("2023年营收")
```

---

### 7.5 元数据过滤

```python
# 场景：只搜索特定作者的文档
results = vectorstore.similarity_search(
    query="Python教程",
    k=3,
    filter={"author": "张三"}  # 只搜索张三写的文档
)

# 场景：只搜索特定日期范围
results = vectorstore.similarity_search(
    query="季度报告",
    k=3,
    filter={"date": {"$gte": "2023-01-01", "$lt": "2024-01-01"}}
)
```

---

### 7.6 Self-Query（智能过滤）

**让 AI 自动提取过滤条件**

```python
from langchain.retrievers import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

# 定义元数据字段
metadata_field_info = [
    AttributeInfo(
        name="author",
        description="文档作者",
        type="string"
    ),
    AttributeInfo(
        name="year",
        description="文档年份",
        type="integer"
    )
]

retriever = SelfQueryRetriever.from_llm(
    llm=ChatOpenAI(temperature=0),
    vectorstore=vectorstore,
    document_contents="公司文档",
    metadata_field_info=metadata_field_info
)

# 用户问："张三在2023年写的文档"
# AI 自动提取：author="张三", year=2023
results = retriever.get_relevant_documents("张三在2023年写的文档")
```

---

## 8. 完整实现案例

### 8.1 最简 RAG（50行代码）

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# 1. 加载文档
loader = PyPDFLoader("company_report.pdf")
documents = loader.load()

# 2. 切分
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# 3. 向量化并存储
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. 创建问答链
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0),
    retriever=vectorstore.as_retriever()
)

# 5. 提问
question = "2023年公司营收是多少？"
answer = qa_chain.run(question)
print(answer)
```

---

### 8.2 带引用来源的 RAG

```python
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0),
    retriever=vectorstore.as_retriever(),
    return_source_documents=True  # 返回来源文档
)

result = qa_chain({"query": "2023年营收多少？"})

print("答案：", result["result"])
print("\n来源文档：")
for doc in result["source_documents"]:
    print(f"- {doc.metadata['source']} 第{doc.metadata.get('page', '?')}页")
    print(f"  内容：{doc.page_content[:100]}...\n")
```

**输出：**
```
答案：2023年公司营收为1.2亿元。

来源文档：
- company_report.pdf 第3页
  内容：根据财务报表，2023年度公司实现营业收入1.2亿元...

- company_report.pdf 第15页
  内容：年度总结：营收同比增长20%，达到1.2亿元...
```

---

### 8.3 自定义 Prompt 的 RAG

```python
from langchain.prompts import PromptTemplate

# 自定义提示词模板
template = """
你是一个专业的财务分析师。请基于以下文档内容回答问题。

文档内容：
{context}

问题：{question}

要求：
1. 只基于文档内容回答
2. 如果文档中没有相关信息，说"文档中未提及"
3. 引用具体数字时注明出处

答案：
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)

qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0),
    retriever=vectorstore.as_retriever(),
    chain_type_kwargs={"prompt": prompt}
)

answer = qa_chain.run("2023年营收是多少？")
```

---

### 8.4 对话式 RAG（带历史记忆）

```python
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# 创建记忆
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 创建对话链
conversation_chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(temperature=0),
    retriever=vectorstore.as_retriever(),
    memory=memory
)

# 多轮对话
response1 = conversation_chain({"question": "2023年营收是多少？"})
print(response1["answer"])
# 输出："1.2亿元"

response2 = conversation_chain({"question": "比去年增长了多少？"})
print(response2["answer"])
# 输出："比2022年增长20%"（AI 记得上一轮在说营收）
```

---

### 8.5 多文档 RAG

```python
from langchain.document_loaders import DirectoryLoader

# 加载整个文件夹
loader = DirectoryLoader(
    "./documents",
    glob="**/*.pdf",  # 所有 PDF
    show_progress=True
)

documents = loader.load()
print(f"加载了 {len(documents)} 个文档")

# 切分
chunks = splitter.split_documents(documents)

# 向量化（自动处理所有文档）
vectorstore = Chroma.from_documents(chunks, embeddings)

# 问答（会在所有文档中搜索）
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0),
    retriever=vectorstore.as_retriever()
)

answer = qa_chain.run("总结所有文档的主要内容")
```

---

## 9. 优化技巧

### 9.1 切分优化

#### 问题：切分太大或太小

```python
# 太大（2000字符）
chunk_size=2000
# 问题：包含太多无关信息，AI 找不到重点

# 太小（200字符）
chunk_size=200
# 问题：上下文不完整，理解困难
```

#### 最佳实践

```python
# 推荐范围：500-1500字符
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # 一般文档
    chunk_overlap=200,      # 20% 重叠
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
)

# 技术文档（代码多）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,        # 稍大，保持代码完整
    chunk_overlap=300
)

# 对话记录（短句多）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,         # 稍小
    chunk_overlap=100
)
```

---

### 9.2 检索优化

#### 调整检索数量

```python
# 检索太少（k=1）
retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
# 问题：可能漏掉重要信息

# 检索太多（k=10）
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
# 问题：太多噪音，AI 容易混淆，且浪费 token

# 推荐：3-5 个
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
```

#### 相似度阈值过滤

```python
# 只返回相似度 > 0.7 的文档
results = vectorstore.similarity_search_with_score(query, k=5)
filtered = [doc for doc, score in results if score > 0.7]

if not filtered:
    print("没有找到足够相关的文档")
else:
    # 使用 filtered 构建答案
    ...
```

---

### 9.3 Prompt 优化

```python
# 基础 Prompt（效果一般）
template = "根据：{context}\n回答：{question}"

# 优化 Prompt（效果更好）
template = """
你是专业助手。请基于以下文档片段回答用户问题。

文档片段：
{context}

用户问题：{question}

回答要求：
1. 仅基于文档内容回答，不要编造
2. 如果文档没有相关信息，明确告知用户
3. 引用关键信息时注明来源
4. 用简洁专业的语言回答

你的回答：
"""

prompt = PromptTemplate(template=template, input_variables=["context", "question"])
```

---

### 9.4 元数据增强

```python
# 切分时添加元数据
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = []

for doc in documents:
    # 为每个文档块添加丰富的元数据
    doc_chunks = splitter.split_documents([doc])
    for chunk in doc_chunks:
        chunk.metadata.update({
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page", 0),
            "doc_type": "report",  # 自定义
            "year": 2023,          # 自定义
            "department": "财务部"  # 自定义
        })
        chunks.append(chunk)

# 创建向量库时元数据会一起存储
vectorstore = Chroma.from_documents(chunks, embeddings)

# 检索时可以根据元数据过滤
results = vectorstore.similarity_search(
    "营收",
    filter={"year": 2023, "department": "财务部"}
)
```

---

### 9.5 重排序（Reranking）

**问题：** 向量搜索可能不够精准

**解决方案：** 先用向量搜索找 top 20，再用更精确的模型重新排序

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank

# 基础检索器
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

# 重排序器（使用 Cohere 的 rerank 模型）
compressor = CohereRerank(cohere_api_key="your-api-key")

# 组合
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

# 使用（会自动重排序并返回最相关的 top 3）
results = compression_retriever.get_relevant_documents("2023年营收")
```

---

## 10. 常见问题

### Q1: 向量数据库存在哪里？

**Chroma：**
```python
# 内存模式（程序关闭数据丢失）
vectorstore = Chroma.from_documents(chunks, embeddings)

# 持久化模式（保存到磁盘）
vectorstore = Chroma.from_documents(
    chunks,
    embeddings,
    persist_directory="./chroma_db"  # 保存位置
)
vectorstore.persist()  # 立即保存

# 下次加载
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
```

---

### Q2: 如何更新文档？

**方法1：删除旧的，添加新的**
```python
# 删除所有文档
vectorstore.delete_collection()

# 重新加载和向量化
documents = loader.load()
chunks = splitter.split_documents(documents)
vectorstore = Chroma.from_documents(chunks, embeddings)
```

**方法2：增量更新**
```python
# 只添加新文档
new_docs = loader.load()
new_chunks = splitter.split_documents(new_docs)
vectorstore.add_documents(new_chunks)
```

**方法3：根据 ID 更新**
```python
# 删除特定文档
vectorstore.delete(ids=["doc_id_1", "doc_id_2"])

# 添加更新后的文档
vectorstore.add_documents(updated_chunks)
```

---

### Q3: 如何处理超大文档？

**问题：** 1000页 PDF，切分后有5000个块，全部向量化很慢

**解决方案1：批量处理**
```python
# 分批向量化
batch_size = 100
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    vectorstore.add_documents(batch)
    print(f"处理了 {i+batch_size}/{len(chunks)}")
```

**解决方案2：并行处理**
```python
from concurrent.futures import ThreadPoolExecutor

def process_batch(batch):
    return embeddings.embed_documents([doc.page_content for doc in batch])

with ThreadPoolExecutor(max_workers=4) as executor:
    # 并行向量化
    results = executor.map(process_batch, batches)
```

**解决方案3：使用更快的 Embedding 模型**
```python
# text-embedding-3-small（OpenAI 最新，速度快）
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```

---

### Q4: RAG 回答不准确怎么办？

**问题诊断流程：**

#### 步骤1：检查检索结果
```python
# 看看检索到的文档是否相关
results = vectorstore.similarity_search("你的问题", k=3)
for i, doc in enumerate(results):
    print(f"\n文档 {i+1}:")
    print(doc.page_content)
    print(doc.metadata)

# 如果检索结果不相关 → 问题在检索阶段
# 如果检索结果相关 → 问题在生成阶段
```

#### 步骤2：调整检索参数
```python
# 增加检索数量
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 使用 MMR（提高多样性）
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 20}
)
```

#### 步骤3：优化 Prompt
```python
template = """
严格基于以下文档内容回答问题。

文档：
{context}

问题：{question}

注意：
1. 只使用文档中的信息，不要推测
2. 如果文档没有答案，说"文档中未找到相关信息"
3. 引用原文时加引号

答案：
"""
```

#### 步骤4：调整切分策略
```python
# 如果答案被切断，增加 chunk_size
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,  # 增大
    chunk_overlap=300  # 增加重叠
)
```

---

### Q5: 如何让 RAG 支持多语言？

```python
# 使用多语言 Embedding 模型
from langchain.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 或使用 OpenAI（天然支持多语言）
embeddings = OpenAIEmbeddings()

# 创建向量库（支持中英混合）
vectorstore = Chroma.from_documents(
    documents=[
        Document(page_content="This is English", metadata={"lang": "en"}),
        Document(page_content="这是中文", metadata={"lang": "zh"})
    ],
    embedding=embeddings
)

# 查询（任意语言）
vectorstore.similarity_search("什么是 Python？")  # 中文查询
vectorstore.similarity_search("What is Python?")  # 英文查询
```

---

## 总结

### RAG 核心流程

```
文档 → 切分 → 向量化 → 存储到向量库（离线）
           ↓
问题 → 向量化 → 检索相似文档 → 构建 Prompt → LLM 生成答案（在线）
```

### 必须掌握的概念

- ✅ **RAG 是什么** - 检索 + 生成
- ✅ **为什么需要 RAG** - 解决 LLM 幻觉、知识过期、私有数据问题
- ✅ **核心组件** - Loader、Splitter、Embedding、VectorStore、Retriever
- ✅ **向量化原理** - 文字变数字，计算相似度
- ✅ **向量数据库** - Chroma（本地）、FAISS（高性能）、Pinecone（云服务）
- ✅ **检索策略** - Similarity、MMR、混合检索

### 最佳实践

1. **切分大小** - 500-1500字符，20%重叠
2. **检索数量** - 3-5个文档块
3. **Prompt 优化** - 明确要求、限制幻觉
4. **元数据丰富** - 添加来源、日期等信息
5. **持久化** - Chroma 使用 persist_directory

### 性能优化

- 批量处理大文档
- 使用更快的 Embedding 模型（text-embedding-3-small）
- 合理设置缓存
- 考虑使用重排序（Reranking）

---

**笔记创建时间：** 2025-11-20
**用途：** AI 应用开发 - RAG 实战
**建议：** 配合 LangChain 和 LLM 笔记一起学习
