# Embeddings（嵌入）技术深入笔记

## 什么是 Embedding？

**一句话解释：** 把文字（或图片、音频）转换成一串数字（向量），让计算机能理解和比较它们的"相似度"。

### 为什么需要 Embedding？

计算机不认识"猫"、"狗"这些文字，但认识数字。Embedding 就是把文字翻译成数字：

```
"猫" → [0.2, 0.8, 0.3, 0.9, ...]  (1536个数字)
"狗" → [0.3, 0.7, 0.4, 0.8, ...]  (1536个数字)
"汽车" → [0.9, 0.1, 0.2, 0.1, ...]  (1536个数字)
```

**神奇之处：** 意思相近的词，数字也相近！
- "猫" 和 "狗" 的数字很相似（都是动物）
- "猫" 和 "汽车" 的数字差距很大

---

## 底层原理：从词到向量

### 1. 传统方法：One-Hot 编码（笨办法）

假设词汇表只有 3 个词：

```python
词汇表 = ["猫", "狗", "车"]

"猫" → [1, 0, 0]
"狗" → [0, 1, 0]
"车" → [0, 0, 1]
```

**问题：**
- "猫" 和 "狗" 的相似度 = 0（完全不相关）
- 词汇表有 10 万个词，每个词就是 10 万维向量（太浪费）

### 2. 现代方法：Dense Embedding（聪明办法）

使用神经网络训练，把词压缩成低维向量（通常 768 或 1536 维）：

```python
"猫" → [0.2, 0.8, 0.3, 0.9, ...]  (1536维)
"狗" → [0.3, 0.7, 0.4, 0.8, ...]  (1536维)

# 计算相似度（余弦相似度）
相似度("猫", "狗") = 0.92  # 很相似！
相似度("猫", "车") = 0.15  # 不相似
```

---

## OpenAI Embeddings 模型详解

### 可用模型对比

| 模型名称 | 维度 | 价格（每百万 token） | 性能 | 适用场景 |
|---------|------|---------------------|------|---------|
| `text-embedding-3-small` | 1536 | $0.02 | 良好 | 大规模文档（推荐） |
| `text-embedding-3-large` | 3072 | $0.13 | 最佳 | 高精度搜索 |
| `text-embedding-ada-002` | 1536 | $0.10 | 良好 | 旧版模型（不推荐） |

**建议：** 99% 的场景用 `text-embedding-3-small` 就够了。

### 核心参数

```python
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # 模型名称
    openai_api_key="sk-xxx",         # API 密钥
    chunk_size=1000,                 # 每批处理的文本数量
    max_retries=3,                   # 失败重试次数
    timeout=30                       # 超时时间（秒）
)
```

---

## 工作原理图解

```
┌──────────────────────────────────────────────────────────┐
│ 第一步：文本预处理                                          │
├──────────────────────────────────────────────────────────┤
│ 原始文本: "机器学习是人工智能的一个分支"                     │
│    ↓                                                     │
│ 分词: ["机器", "学习", "是", "人工", "智能", "的", "一个", "分支"] │
│    ↓                                                     │
│ Token化: [23401, 28492, 15, 19283, 38291, 21, 4500, 39201] │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│ 第二步：神经网络编码                                        │
├──────────────────────────────────────────────────────────┤
│ Transformer 模型 (12-24层神经网络)                         │
│    ↓                                                     │
│ 注意力机制: 理解词之间的关系                                │
│    ↓                                                     │
│ 上下文编码: 每个词都包含周围词的信息                         │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│ 第三步：生成向量                                            │
├──────────────────────────────────────────────────────────┤
│ 输出: [0.023, -0.145, 0.891, ..., 0.234]  (1536维向量)   │
│                                                          │
│ 这个向量包含了文本的"语义指纹"                               │
└──────────────────────────────────────────────────────────┘
```

---

## 实战示例

### 1. 基础用法：单个文本转向量

```python
from langchain.embeddings import OpenAIEmbeddings

# 初始化
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# 转换单个文本
text = "机器学习是人工智能的分支"
vector = embeddings.embed_query(text)

print(f"向量维度: {len(vector)}")  # 1536
print(f"前5个数字: {vector[:5]}")  # [0.023, -0.145, 0.891, ...]
```

### 2. 批量转换：多个文档

```python
# 批量转换多个文档
documents = [
    "Python 是一种编程语言",
    "机器学习使用 Python",
    "猫是一种动物"
]

vectors = embeddings.embed_documents(documents)

print(f"转换了 {len(vectors)} 个文档")
print(f"每个向量维度: {len(vectors[0])}")
```

### 3. 计算相似度

```python
import numpy as np

def cosine_similarity(vec1, vec2):
    """计算余弦相似度（-1 到 1，越接近 1 越相似）"""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# 获取三个文本的向量
vec1 = embeddings.embed_query("Python 编程语言")
vec2 = embeddings.embed_query("机器学习使用 Python")
vec3 = embeddings.embed_query("猫是动物")

print(f"Python vs 机器学习: {cosine_similarity(vec1, vec2):.3f}")  # 0.85 (很相似)
print(f"Python vs 猫: {cosine_similarity(vec1, vec3):.3f}")        # 0.12 (不相似)
```

### 4. 向量搜索（最核心的应用）

```python
# 文档库
docs = [
    "Python 是一种流行的编程语言",
    "机器学习需要大量数据",
    "深度学习是机器学习的子集",
    "猫喜欢吃鱼"
]

# 转换所有文档为向量
doc_vectors = embeddings.embed_documents(docs)

# 用户提问
query = "什么是深度学习？"
query_vector = embeddings.embed_query(query)

# 计算相似度
similarities = [
    cosine_similarity(query_vector, doc_vec)
    for doc_vec in doc_vectors
]

# 找出最相关的文档
best_match_idx = np.argmax(similarities)
print(f"最相关文档: {docs[best_match_idx]}")
print(f"相似度: {similarities[best_match_idx]:.3f}")

# 输出:
# 最相关文档: 深度学习是机器学习的子集
# 相似度: 0.892
```

---

## 向量的数学本质

### 向量在几何空间中的表示

```
假设简化为 2 维（实际是 1536 维）：

"猫" = [0.8, 0.9]
"狗" = [0.7, 0.85]
"车" = [0.1, 0.2]

在二维平面上：
        ↑ (维度2)
      1 |    ● 猫 (0.8, 0.9)
        |   ● 狗 (0.7, 0.85)
    0.5 |
        |
      0 |● 车 (0.1, 0.2)
        └─────────────────→ (维度1)
         0    0.5    1

"猫" 和 "狗" 的距离很近（语义相似）
"车" 离它们很远（语义不同）
```

### 余弦相似度公式

```
cos(θ) = (A · B) / (||A|| × ||B||)

其中：
- A · B = 向量点积
- ||A|| = 向量 A 的模（长度）
- θ = 两个向量的夹角

结果范围：
- 1.0  = 完全相同
- 0.0  = 完全无关
- -1.0 = 完全相反
```

---

## Embedding 在 RAG 中的应用

### 完整流程示例

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader

# ========== 离线阶段：构建向量数据库 ==========

# 1. 加载 PDF
loader = PyPDFLoader("document.pdf")
documents = loader.load()

# 2. 分块
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)
# 假设得到 100 个文本块

# 3. 初始化 Embedding 模型
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# 4. 转换为向量并存储
vectorstore = Chroma.from_documents(
    documents=chunks,        # 100 个文本块
    embedding=embeddings,    # 每个块 → 1536 维向量
    persist_directory="./db" # 保存到磁盘
)
# 现在数据库有 100 个向量

# ========== 在线阶段：检索答案 ==========

# 5. 用户提问
query = "这份文档讲了什么？"

# 6. 问题转向量
query_vector = embeddings.embed_query(query)
# query_vector = [0.123, -0.456, ..., 0.789]  (1536维)

# 7. 向量搜索（找最相似的 3 个文档块）
similar_docs = vectorstore.similarity_search(query, k=3)

# 底层发生了什么：
# - 计算 query_vector 和 100 个文档向量的相似度
# - 排序，取前 3 名
# - 返回对应的原始文本

# 8. 把检索到的文档喂给 LLM
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI()

context = "\n\n".join([doc.page_content for doc in similar_docs])
prompt = f"根据以下内容回答问题：\n\n{context}\n\n问题：{query}"

answer = llm.predict(prompt)
print(answer)
```

### 为什么向量搜索比关键词搜索强？

**关键词搜索（传统方法）：**
```python
问题: "如何减肥？"
文档: "想要瘦身，需要控制饮食和运动"

关键词匹配: 0 个匹配 ❌
（因为文档中没有"减肥"这个词）
```

**向量搜索（语义搜索）：**
```python
问题: "如何减肥？"
query_vector = [0.234, 0.567, ...]

文档: "想要瘦身，需要控制饮食和运动"
doc_vector = [0.241, 0.573, ...]

余弦相似度 = 0.95 ✅
（理解"减肥"和"瘦身"是同一个意思）
```

---

## 向量数据库的存储原理

### Chroma 如何存储向量？

```python
# 简化的数据结构
{
    "id_1": {
        "text": "Python 是编程语言",
        "vector": [0.23, -0.45, 0.89, ..., 0.12],  # 1536 个数字
        "metadata": {"source": "page_1", "page": 1}
    },
    "id_2": {
        "text": "机器学习需要数据",
        "vector": [0.45, 0.12, -0.34, ..., 0.67],
        "metadata": {"source": "page_2", "page": 1}
    },
    ...
}
```

### 快速检索算法：ANN（近似最近邻）

**暴力搜索（太慢）：**
```python
# 对每个文档计算相似度
for doc in all_docs:  # 100万个文档
    similarity = cosine_similarity(query_vector, doc.vector)
# 时间复杂度: O(n) - 太慢！
```

**ANN 算法（快速）：**
```python
# 使用 HNSW（分层导航小世界图）算法
# 把向量空间分成多层索引
# 只需搜索一小部分向量就能找到最相似的

# 时间复杂度: O(log n) - 快得多！
# 100万文档只需检索约 20 次
```

---

## 实战技巧

### 1. 如何选择 chunk_size？

```python
# 太小（100 字符）
"机器学习"  # 上下文不足，语义不完整

# 太大（5000 字符）
"机器学习是...深度学习...神经网络...大数据..."  # 信息太杂，降低精准度

# 推荐（1000 字符）
"机器学习是人工智能的一个分支，通过算法让计算机从数据中学习..."  # 刚好一个完整段落
```

### 2. chunk_overlap 的作用

```python
# 不重叠（chunk_overlap=0）
chunk1: "机器学习是 AI 的分支。"
chunk2: "深度学习使用神经网络。"
# 问题：如果关键信息在边界，可能被切断

# 重叠 200 字符（推荐）
chunk1: "机器学习是 AI 的分支。深度学习使用"
chunk2: "深度学习使用神经网络。"
# 好处：保证边界信息不丢失
```

### 3. 成本优化

```python
# 假设 1 本书 = 10 万字 = 约 15 万 token
# 分成 150 个 chunk（每个 1000 字）

# text-embedding-3-small
# 成本 = 150,000 token × $0.02 / 1,000,000 = $0.003
# 一本书只需 0.3 分钱！

# text-embedding-3-large
# 成本 = 150,000 token × $0.13 / 1,000,000 = $0.0195
# 一本书需 2 分钱
```

---

## 高级话题

### 1. 多语言 Embedding

```python
# OpenAI 的 Embedding 支持 100+ 种语言
embeddings = OpenAIEmbeddings()

vec_cn = embeddings.embed_query("你好")      # 中文
vec_en = embeddings.embed_query("Hello")     # 英文
vec_jp = embeddings.embed_query("こんにちは") # 日文

# 神奇之处：不同语言的相同意思，向量也相似！
cosine_similarity(vec_cn, vec_en) ≈ 0.85
```

### 2. Fine-tuning Embeddings（自定义训练）

OpenAI 支持用你自己的数据训练专属 Embedding 模型：

```python
# 场景：医学文档检索
# 默认模型："心脏病" 和 "心血管疾病" 的相似度 = 0.75

# Fine-tune 后：
# "心脏病" 和 "心血管疾病" 的相似度 = 0.95
# （因为用医学数据训练过）

# 成本：训练费用约 $10-100（取决于数据量）
```

### 3. 本地化 Embedding（免费方案）

```python
from langchain.embeddings import HuggingFaceEmbeddings

# 使用开源模型（完全免费，但需要本地显卡）
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 优点：免费、隐私
# 缺点：质量稍逊、需要 GPU
```

---

## 常见问题

### Q1: 向量存储在哪里？

```python
# Chroma 本地存储
vectorstore = Chroma(
    persist_directory="./chroma_db"  # 存在磁盘
)

# 数据库结构：
./chroma_db/
├── chroma.sqlite3      # 元数据（文本、metadata）
└── index/              # 向量索引（二进制文件）
    └── id_to_uuid/
```

### Q2: 为什么向量是 1536 维？

- 这是 OpenAI 训练模型时的架构决定
- 维度越高，能表达的语义越丰富
- 但维度太高会浪费存储和计算资源
- 1536 是经过实验验证的最佳平衡点

### Q3: 能直接看懂向量的含义吗？

不能。向量是高维空间的"黑盒表示"：

```python
[0.023, -0.145, 0.891, ...]
# 人类无法直接解读每个数字的含义
# 只能通过相似度比较来理解
```

### Q4: 向量数据库能存多少文档？

| 数据库 | 免费额度 | 收费方案 |
|--------|---------|---------|
| Chroma（本地） | 无限制 | 无（本地存储） |
| Pinecone | 100 万向量 | $0.096/百万向量/月 |
| Weaviate | 无限制 | 自托管或云服务 |

---

## 总结：Embedding 的核心价值

```
┌─────────────────────────────────────────┐
│ Embedding = 语义理解的桥梁                │
├─────────────────────────────────────────┤
│ 输入: 人类语言（文字）                     │
│   ↓                                     │
│ 处理: 神经网络编码                        │
│   ↓                                     │
│ 输出: 数学向量（数字）                     │
│   ↓                                     │
│ 应用: 语义搜索、推荐系统、RAG             │
└─────────────────────────────────────────┘
```

**关键记忆点：**
1. Embedding = 把文字变成数字（向量）
2. 相似的文字 → 相似的向量
3. 用余弦相似度衡量语义相似性
4. RAG 的核心就是向量搜索
5. `text-embedding-3-small` 够用且便宜

---

## 延伸阅读

- OpenAI Embeddings 官方文档：https://platform.openai.com/docs/guides/embeddings
- Chroma 向量数据库教程：https://docs.trychroma.com/
- 向量搜索算法（HNSW）：https://arxiv.org/abs/1603.09320
