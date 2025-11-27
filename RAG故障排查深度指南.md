# RAG 故障排查深度指南

> **逆向学习哲学**: 从生产环境的真实问题出发，倒推底层原理，深挖技术细节
>
> **目标读者**: 已掌握 RAG 基础理论，需要解决实际工程问题的开发者

---

## 目录

1. [问题分类树](#问题分类树)
2. [检索质量问题](#检索质量问题)
3. [生成质量问题](#生成质量问题)
4. [性能与成本问题](#性能与成本问题)
5. [系统稳定性问题](#系统稳定性问题)
6. [调试工具与测试方法](#调试工具与测试方法)

---

## 问题分类树

```
RAG 系统故障
│
├─ 检索质量差 (Retrieval Quality)
│  ├─ 召回率低 (Recall)
│  ├─ 精确率低 (Precision)
│  └─ 相关性判断错误 (Relevance)
│
├─ 生成质量差 (Generation Quality)
│  ├─ 幻觉 (Hallucination)
│  ├─ 上下文丢失 (Context Loss)
│  └─ 答案不准确 (Inaccuracy)
│
├─ 性能问题 (Performance)
│  ├─ 延迟高 (Latency)
│  ├─ 吞吐量低 (Throughput)
│  └─ 成本高 (Cost)
│
└─ 稳定性问题 (Stability)
   ├─ API 限流/超时
   ├─ 内存溢出 (OOM)
   └─ 并发错误
```

---

# 第一部分：检索质量问题

## 案例 1: "为什么检索不到明明存在的文档？"

### 🔴 故障现象

```python
# 知识库中有这段文本
document = """
GPT-4 拥有约 1.76 万亿参数，是 OpenAI 在 2023 年 3 月发布的多模态大模型。
它支持文本和图像输入，在多个基准测试中超越了 GPT-3.5。
"""

# 用户问题
query = "GPT-4 有多少参数？"

# 检索结果
retrieved_docs = [
    "GPT-3 有 175B 参数...",
    "大模型的参数量决定了性能...",
    "OpenAI 是 AI 领域的领导者..."
]

# ❌ 问题：明明文档里有答案，为什么检索不到？
```

### 🔍 根因分析（5 层深挖）

#### 层次 1: 表面原因 - 分块策略失效

```python
# 检查文档分块结果
def debug_chunking(text, chunk_size=200, chunk_overlap=50):
    """调试分块逻辑"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append({
            "chunk": chunk,
            "start": start,
            "end": end,
            "length": len(chunk)
        })
        start += (chunk_size - chunk_overlap)
    return chunks

# 实际输出
chunks = debug_chunking(document, chunk_size=50, chunk_overlap=10)
# [
#   {"chunk": "GPT-4 拥有约 1.76 万亿参数，是 OpenAI 在 2023 年 3 月发布", ...},
#   {"chunk": "在 2023 年 3 月发布的多模态大模型。\n它支持文本和图像输入", ...},
#   {"chunk": "输入，在多个基准测试中超越了 GPT-3.5。", ...}
# ]

# ❌ 问题发现：关键信息 "GPT-4" 和 "1.76 万亿参数" 在同一个块
# ✅ 但如果 chunk_size=30，会被分割：
#   块1: "GPT-4 拥有约 1.76 万亿参数"
#   块2: "是 OpenAI 在 2023 年 3 月发布的多模"
```

**中间结论**: 分块参数不当导致语义完整性被破坏。

---

#### 层次 2: Embedding 语义编码问题

```python
# 检查 Embedding 的语义捕获能力
import openai

# 原文
text = "GPT-4 拥有约 1.76 万亿参数"

# 查询
query = "GPT-4 有多少参数？"

# 获取向量
text_emb = openai.Embedding.create(input=text, model="text-embedding-ada-002")
query_emb = openai.Embedding.create(input=query, model="text-embedding-ada-002")

# 计算余弦相似度
import numpy as np
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

similarity = cosine_sim(
    text_emb['data'][0]['embedding'],
    query_emb['data'][0]['embedding']
)
# 预期: similarity ≈ 0.85 ~ 0.95

# ❓ 如果 similarity < 0.7，说明什么问题？
```

**深入分析**:

1. **词汇差异问题** (Vocabulary Gap)
   ```python
   # 问题: "有多少" vs "拥有约"
   # Embedding 可能无法很好地对齐这种表达差异

   # 解决方案 1: Query Rewriting
   def query_expansion(query):
       """查询扩展"""
       synonyms = {
           "有多少": ["拥有约", "是", "等于", "达到"],
           "参数": ["参数量", "参数规模", "参数数量"]
       }
       expanded_queries = [query]
       for word, syns in synonyms.items():
           if word in query:
               for syn in syns:
                   expanded_queries.append(query.replace(word, syn))
       return expanded_queries

   # 扩展后的查询
   queries = query_expansion("GPT-4 有多少参数？")
   # ["GPT-4 有多少参数？", "GPT-4 拥有约参数？", "GPT-4 是参数？", ...]
   ```

2. **数字表示问题** (Numeric Representation)
   ```python
   # 问题: "1.76 万亿" vs "1.76T" vs "1760B"
   # Embedding 模型对数字的表示能力有限

   # 证明实验
   texts = [
       "GPT-4 有 1.76 万亿参数",
       "GPT-4 有 1.76T 参数",
       "GPT-4 有 1760B 参数",
       "GPT-4 有 1,760,000,000,000 参数"
   ]

   embeddings = [get_embedding(t) for t in texts]

   # 计算相似度矩阵
   # 预期: 所有向量应该非常接近（余弦相似度 > 0.95）
   # 实际: 可能只有 0.75 ~ 0.85

   # 根因: Embedding 模型在预训练时，不同数字表示形式的共现频率不同
   ```

**中间结论**: Embedding 模型的语义捕获能力存在局限性。

---

#### 层次 3: 向量数据库索引问题

```python
# 检查向量数据库的索引配置
from chromadb.config import Settings

# 常见配置错误
config = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db",
    anonymized_telemetry=False
)

# ❌ 问题：没有指定距离度量
# Chroma 默认使用 L2 距离，但很多场景下余弦相似度更好

# 正确配置
collection = client.create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}  # 指定余弦相似度
)

# 对比实验
def compare_distance_metrics(query_vec, doc_vecs):
    """对比不同距离度量的检索结果"""
    import numpy as np

    # L2 距离
    l2_distances = [np.linalg.norm(query_vec - doc) for doc in doc_vecs]
    l2_ranking = np.argsort(l2_distances)

    # 余弦相似度
    cos_similarities = [
        np.dot(query_vec, doc) / (np.linalg.norm(query_vec) * np.linalg.norm(doc))
        for doc in doc_vecs
    ]
    cos_ranking = np.argsort(cos_similarities)[::-1]

    print("L2 排序:", l2_ranking)
    print("Cosine 排序:", cos_ranking)

    # 可能出现不同的排序结果！
```

**深入原理**:

```
L2 距离 vs 余弦相似度的本质区别：

假设有三个向量：
query = [1, 0]  (查询向量)
doc1  = [2, 0]  (方向相同，模长不同)
doc2  = [0.7, 0.7]  (方向不同，模长相近)

L2 距离:
d(query, doc1) = ||[1,0] - [2,0]|| = 1.0
d(query, doc2) = ||[1,0] - [0.7,0.7]|| = 0.72

结论: doc2 更近（❌ 错误，doc2 方向完全不同）

余弦相似度:
cos(query, doc1) = 1.0  (方向完全一致)
cos(query, doc2) = 0.7  (方向偏离)

结论: doc1 更相关（✅ 正确）

为什么会这样？
- L2 距离受向量模长影响（文本长度影响）
- 余弦相似度只关注方向（语义相似性）

适用场景：
- 文本检索 → 余弦相似度
- 图像检索（固定尺寸）→ L2 距离
```

**中间结论**: 距离度量选择不当导致排序错误。

---

#### 层次 4: Top-K 参数调优问题

```python
# 检查检索的 Top-K 设置
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # ❌ 问题：K 值太小
)

# 实验：K 值对召回率的影响
def analyze_recall_at_k(vectorstore, test_queries, ground_truth):
    """分析不同 K 值下的召回率"""
    k_values = [1, 3, 5, 10, 20, 50]
    results = {}

    for k in k_values:
        recall_scores = []
        for query, relevant_docs in zip(test_queries, ground_truth):
            # 检索 Top-K
            retrieved = vectorstore.similarity_search(query, k=k)
            retrieved_ids = {doc.metadata['id'] for doc in retrieved}

            # 计算召回率
            relevant_ids = set(relevant_docs)
            recall = len(retrieved_ids & relevant_ids) / len(relevant_ids)
            recall_scores.append(recall)

        results[k] = np.mean(recall_scores)

    return results

# 典型输出
# {
#   1: 0.42,   # K=1 时，召回率仅 42%
#   3: 0.68,   # K=3 时，召回率 68%
#   5: 0.81,   # K=5 时，召回率 81%
#   10: 0.92,  # K=10 时，召回率 92%
#   20: 0.97,  # K=20 时，召回率 97%（但会引入噪音）
# }

# ⚖️ 权衡点：召回率 vs 精确率 vs LLM 成本
```

**深度分析：K 值的多维影响**

```python
class KValueAnalyzer:
    """K 值的全维度分析器"""

    def __init__(self, vectorstore, llm_cost_per_token=0.0001):
        self.vectorstore = vectorstore
        self.llm_cost_per_token = llm_cost_per_token

    def analyze(self, query, ground_truth_doc_id, k_values=[1, 3, 5, 10]):
        """多维度分析 K 值影响"""
        results = []

        for k in k_values:
            # 检索
            docs = self.vectorstore.similarity_search(query, k=k)

            # 1. 召回率
            retrieved_ids = [doc.metadata['id'] for doc in docs]
            recall = 1.0 if ground_truth_doc_id in retrieved_ids else 0.0

            # 2. 精确率（人工标注前 k 个是否都相关）
            # 简化：假设只有 ground_truth 相关
            precision = recall / k

            # 3. 上下文长度
            total_tokens = sum([len(doc.page_content.split()) for doc in docs])

            # 4. LLM 成本
            llm_cost = total_tokens * self.llm_cost_per_token

            # 5. 答案质量（需要实际调用 LLM，这里模拟）
            # 假设：更多上下文 → 更高质量，但边际效益递减
            quality_score = min(recall * (1 + 0.1 * k), 1.0)

            results.append({
                "k": k,
                "recall": recall,
                "precision": precision,
                "context_tokens": total_tokens,
                "llm_cost": llm_cost,
                "estimated_quality": quality_score,
                "efficiency": quality_score / llm_cost  # 质量/成本比
            })

        return results

# 运行分析
analyzer = KValueAnalyzer(vectorstore)
analysis = analyzer.analyze(
    query="GPT-4 有多少参数？",
    ground_truth_doc_id="doc_123"
)

# 典型输出（格式化为表格）
"""
| K  | Recall | Precision | Context Tokens | LLM Cost | Quality | Efficiency |
|----|--------|-----------|----------------|----------|---------|------------|
| 1  | 0.0    | 0.0       | 150            | $0.015   | 0.0     | 0.0        |
| 3  | 1.0    | 0.33      | 450            | $0.045   | 1.3     | 28.9       |
| 5  | 1.0    | 0.20      | 750            | $0.075   | 1.5     | 20.0       |
| 10 | 1.0    | 0.10      | 1500           | $0.150   | 2.0     | 13.3       |
"""

# 🎯 最优选择：K=3 或 K=5（召回率高 + 效率最佳）
```

**中间结论**: K 值需要根据业务场景权衡召回率、成本和质量。

---

#### 层次 5: 混合检索策略缺失

```python
# 问题：纯向量检索无法处理精确匹配需求
query = "GPT-4 有多少参数？"

# 纯向量检索的问题
vector_results = vectorstore.similarity_search(query, k=5)
# 可能返回：
# - "GPT-3 有 175B 参数"（语义相似但实体错误）
# - "参数量是衡量模型能力的关键指标"（相关但无答案）

# 解决方案：Hybrid Search（向量 + 关键词）
from rank_bpm25 import BM25Okapi

class HybridRetriever:
    """混合检索器"""

    def __init__(self, vectorstore, documents):
        self.vectorstore = vectorstore
        self.documents = documents

        # 构建 BM25 索引
        tokenized_docs = [doc.page_content.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)

    def retrieve(self, query, k=5, alpha=0.5):
        """
        混合检索

        参数:
            query: 查询文本
            k: 返回数量
            alpha: 向量检索权重（0-1），1-alpha 为 BM25 权重
        """
        # 1. 向量检索（语义相似）
        vector_results = self.vectorstore.similarity_search_with_score(query, k=k*2)
        vector_scores = {
            doc.metadata['id']: 1 - score  # 转换距离为相似度
            for doc, score in vector_results
        }

        # 2. BM25 检索（关键词匹配）
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_scores_dict = {
            self.documents[i].metadata['id']: score
            for i, score in enumerate(bm25_scores)
        }

        # 3. 归一化分数
        def normalize(scores):
            max_s = max(scores.values()) if scores else 1
            return {k: v/max_s for k, v in scores.items()}

        vector_scores_norm = normalize(vector_scores)
        bm25_scores_norm = normalize(bm25_scores_dict)

        # 4. 加权融合
        all_doc_ids = set(vector_scores_norm.keys()) | set(bm25_scores_norm.keys())
        hybrid_scores = {}
        for doc_id in all_doc_ids:
            vec_score = vector_scores_norm.get(doc_id, 0)
            bm25_score = bm25_scores_norm.get(doc_id, 0)
            hybrid_scores[doc_id] = alpha * vec_score + (1 - alpha) * bm25_score

        # 5. 排序返回 Top-K
        sorted_ids = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return [self.get_doc_by_id(doc_id) for doc_id, _ in sorted_ids]

# 对比实验
def compare_retrieval_methods(query, ground_truth_id):
    """对比纯向量 vs 混合检索"""
    # 纯向量
    vector_results = vectorstore.similarity_search(query, k=5)
    vector_has_answer = any(doc.metadata['id'] == ground_truth_id for doc in vector_results)

    # 混合检索
    hybrid_retriever = HybridRetriever(vectorstore, all_documents)
    hybrid_results = hybrid_retriever.retrieve(query, k=5, alpha=0.7)
    hybrid_has_answer = any(doc.metadata['id'] == ground_truth_id for doc in hybrid_results)

    return {
        "vector_recall": vector_has_answer,
        "hybrid_recall": hybrid_has_answer
    }

# 典型改进
# Before (纯向量): 召回率 68%
# After (混合检索): 召回率 87%
```

**深度原理：为什么混合检索更好？**

```
纯向量检索的局限性：

1. 实体识别弱
   查询: "GPT-4 有多少参数？"
   向量可能混淆: GPT-3, GPT-3.5, GPT-4

   BM25 优势: 精确匹配 "GPT-4" token

2. 数字表示弱
   查询: "1.76 万亿"
   向量可能匹配: "数万亿", "约 2 万亿"

   BM25 优势: 精确匹配数字

3. 罕见词汇弱
   查询: "RLHF 算法"
   向量可能泛化为: "强化学习算法"

   BM25 优势: 精确匹配专业术语

混合策略的数学基础：

Score_hybrid = α × Score_semantic + (1-α) × Score_lexical

其中：
- Score_semantic: 余弦相似度（捕获语义）
- Score_lexical: BM25 分数（捕获字面匹配）
- α ∈ [0.5, 0.8]: 通常向量权重更高

调优建议：
- 问答场景: α=0.7 (更重语义)
- 代码搜索: α=0.3 (更重精确匹配)
- 学术检索: α=0.5 (均衡)
```

---

### ✅ 完整解决方案

```python
class ProductionRetriever:
    """生产级检索器（集成所有优化）"""

    def __init__(self, documents, embedding_model, chunk_config):
        # 1. 优化分块策略
        self.chunks = self._smart_chunking(documents, chunk_config)

        # 2. 创建向量数据库（指定余弦相似度）
        self.vectorstore = Chroma.from_documents(
            documents=self.chunks,
            embedding=embedding_model,
            collection_metadata={"hnsw:space": "cosine"}
        )

        # 3. 初始化 BM25
        self.bm25 = BM25Okapi([doc.page_content.split() for doc in self.chunks])

    def _smart_chunking(self, documents, config):
        """智能分块（保持语义完整性）"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['chunk_size'],
            chunk_overlap=config['chunk_overlap'],
            separators=["\n\n", "\n", "。", "！", "？", " ", ""],  # 语义边界
            length_function=len
        )

        return splitter.split_documents(documents)

    def retrieve(self, query, k=5, rerank=True):
        """混合检索 + 重排序"""
        # Step 1: 混合检索（取 2*k 候选）
        candidates = self._hybrid_search(query, k=k*2)

        # Step 2: 重排序（可选）
        if rerank:
            candidates = self._rerank(query, candidates)

        # Step 3: 返回 Top-K
        return candidates[:k]

    def _hybrid_search(self, query, k):
        """混合检索实现"""
        # 向量检索
        vector_results = self.vectorstore.similarity_search_with_score(query, k=k)

        # BM25 检索
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # 融合分数（参考上面的实现）
        # ...

        return merged_results

    def _rerank(self, query, candidates):
        """使用交叉编码器重排序"""
        from sentence_transformers import CrossEncoder

        # 加载重排序模型
        reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')

        # 计算查询与每个候选的相关性分数
        pairs = [(query, doc.page_content) for doc in candidates]
        scores = reranker.predict(pairs)

        # 按分数排序
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked]

# 使用示例
retriever = ProductionRetriever(
    documents=all_docs,
    embedding_model=OpenAIEmbeddings(),
    chunk_config={"chunk_size": 500, "chunk_overlap": 50}
)

results = retriever.retrieve("GPT-4 有多少参数？", k=3, rerank=True)
```

---

## 案例 2: "为什么返回的文档相似度很高，但答案却错了？"

### 🔴 故障现象

```python
# 检索结果
retrieved_docs = [
    {
        "content": "GPT-3 拥有 175B 参数，是 2020 年最大的语言模型。",
        "similarity": 0.91  # ✅ 高相似度
    },
    {
        "content": "OpenAI 的 GPT 系列模型不断突破参数规模记录。",
        "similarity": 0.88
    },
    {
        "content": "GPT-4 在多个基准测试中表现优异，但参数量未公开。",
        "similarity": 0.86
    }
]

# 用户问题
query = "GPT-4 有多少参数？"

# LLM 生成答案
answer = "根据检索到的文档，GPT-4 拥有 175B 参数。"
# ❌ 错误！混淆了 GPT-3 和 GPT-4
```

### 🔍 根因分析

#### 问题 1: 相似度≠相关性

```python
# 深入理解：余弦相似度的局限性

def analyze_false_positive(query, doc1, doc2):
    """分析假阳性案例"""

    # 查询和两个文档
    query = "GPT-4 有多少参数？"
    doc1 = "GPT-3 拥有 175B 参数"  # ❌ 错误实体
    doc2 = "GPT-4 的参数量未公开"  # ✅ 正确答案

    # 获取 Embedding
    query_emb = get_embedding(query)
    doc1_emb = get_embedding(doc1)
    doc2_emb = get_embedding(doc2)

    # 计算相似度
    sim1 = cosine_similarity(query_emb, doc1_emb)  # 0.91
    sim2 = cosine_similarity(query_emb, doc2_emb)  # 0.86

    # ❓ 为什么 doc1 分数更高？

    # 原因分析：词汇重叠度
    def lexical_overlap(text1, text2):
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        return len(words1 & words2) / len(words1 | words2)

    overlap1 = lexical_overlap(query, doc1)
    # 共同词: {"参数"} → overlap ≈ 0.25

    overlap2 = lexical_overlap(query, doc2)
    # 共同词: {"GPT-4", "参数"} → overlap ≈ 0.40

    # 🔍 发现：词汇重叠度 doc2 更高，但相似度 doc1 更高
    #    原因：Embedding 捕获了"具体数值"的语义信号
    #         "有多少" 与 "175B" 的语义关联强于 "未公开"
```

**深度原理：Embedding 的统计偏见**

```
Embedding 模型的训练数据中：

高频模式 1:
"XXX 有多少参数？" → "XXX 有 N 参数"
出现频率: 很高

高频模式 2:
"XXX 有多少参数？" → "XXX 的参数量未公开"
出现频率: 较低

结果：
模型学习到的统计关联：
  "有多少" → "具体数值" (强关联)
  "有多少" → "未公开" (弱关联)

即使实体不匹配（GPT-3 vs GPT-4），
语义模式匹配（问数字 → 答数字）导致高相似度。

这就是为什么需要重排序模型（CrossEncoder）来二次验证！
```

#### 问题 2: 缺少实体识别和验证

```python
class EntityAwareRetriever:
    """实体感知的检索器"""

    def __init__(self, vectorstore, entity_extractor):
        self.vectorstore = vectorstore
        self.entity_extractor = entity_extractor  # NER 模型

    def retrieve_with_entity_verification(self, query, k=5):
        """检索 + 实体验证"""
        # Step 1: 从查询中提取关键实体
        query_entities = self.entity_extractor(query)
        # 例如: {"GPT-4": "MODEL", "参数": "ATTRIBUTE"}

        # Step 2: 向量检索
        candidates = self.vectorstore.similarity_search_with_score(query, k=k*3)

        # Step 3: 实体匹配过滤
        filtered_results = []
        for doc, score in candidates:
            doc_entities = self.entity_extractor(doc.page_content)

            # 检查关键实体是否匹配
            entity_match_score = self._calculate_entity_match(
                query_entities,
                doc_entities
            )

            # 调整最终分数
            final_score = 0.6 * score + 0.4 * entity_match_score
            filtered_results.append((doc, final_score))

        # Step 4: 重新排序
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        return filtered_results[:k]

    def _calculate_entity_match(self, query_entities, doc_entities):
        """计算实体匹配度"""
        # 精确匹配关键实体
        key_entities = {k for k, v in query_entities.items() if v in ["MODEL", "ORG"]}
        doc_entity_set = set(doc_entities.keys())

        if not key_entities:
            return 1.0  # 无关键实体，不惩罚

        # 计算匹配比例
        matched = key_entities & doc_entity_set
        return len(matched) / len(key_entities)

# 使用示例
from spacy import load
nlp = load("en_core_web_sm")

def simple_entity_extractor(text):
    """简单的实体提取器"""
    doc = nlp(text)
    return {ent.text: ent.label_ for ent in doc.ents}

entity_retriever = EntityAwareRetriever(vectorstore, simple_entity_extractor)
results = entity_retriever.retrieve_with_entity_verification(
    "GPT-4 有多少参数？",
    k=3
)

# 结果对比：
# Before: [GPT-3 (0.91), GPT 系列 (0.88), GPT-4 未公开 (0.86)]
# After:  [GPT-4 未公开 (0.92), GPT-4 测试 (0.84), ...]
```

---

### ✅ 完整解决方案：多阶段检索管道

```python
class MultiStageRetrievalPipeline:
    """多阶段检索管道"""

    def __init__(self, vectorstore, config):
        self.vectorstore = vectorstore
        self.config = config

        # 加载各种组件
        self.bm25 = None  # BM25 索引
        self.entity_extractor = None  # 实体提取器
        self.reranker = None  # 重排序模型

    def retrieve(self, query, k=5):
        """完整检索流程"""
        # 阶段 1: 粗召回（Recall Stage）
        candidates = self._stage1_recall(query, k=k*10)

        # 阶段 2: 实体过滤（Entity Filtering）
        filtered = self._stage2_entity_filter(query, candidates)

        # 阶段 3: 重排序（Reranking Stage）
        reranked = self._stage3_rerank(query, filtered, k=k*2)

        # 阶段 4: 多样性选择（Diversity Selection）
        final = self._stage4_diversity_select(reranked, k=k)

        return final

    def _stage1_recall(self, query, k):
        """阶段 1: 粗召回（混合检索）"""
        # 向量检索
        vector_results = self.vectorstore.similarity_search_with_score(query, k=k)

        # BM25 检索
        bm25_results = self.bm25.get_top_n(query.split(), k=k)

        # 合并去重
        all_results = self._merge_results(vector_results, bm25_results)
        return all_results[:k]

    def _stage2_entity_filter(self, query, candidates):
        """阶段 2: 实体匹配过滤"""
        query_entities = self.entity_extractor(query)

        scored_candidates = []
        for doc, base_score in candidates:
            doc_entities = self.entity_extractor(doc.page_content)
            entity_score = self._calculate_entity_match(query_entities, doc_entities)

            # 实体不匹配，降低分数
            if entity_score < 0.5:
                final_score = base_score * 0.5
            else:
                final_score = base_score

            scored_candidates.append((doc, final_score))

        return scored_candidates

    def _stage3_rerank(self, query, candidates, k):
        """阶段 3: 重排序（CrossEncoder）"""
        from sentence_transformers import CrossEncoder

        reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')

        # 计算精确相关性分数
        pairs = [(query, doc.page_content) for doc, _ in candidates]
        rerank_scores = reranker.predict(pairs)

        # 合并分数（0.3 初排 + 0.7 重排）
        final_results = []
        for (doc, init_score), rerank_score in zip(candidates, rerank_scores):
            final_score = 0.3 * init_score + 0.7 * rerank_score
            final_results.append((doc, final_score))

        # 排序
        final_results.sort(key=lambda x: x[1], reverse=True)
        return final_results[:k]

    def _stage4_diversity_select(self, candidates, k):
        """阶段 4: 多样性选择（MMR）"""
        # Maximal Marginal Relevance
        # 在保证相关性的同时，增加多样性

        selected = []
        remaining = candidates.copy()

        # 选择第一个（最相关）
        selected.append(remaining.pop(0))

        # 迭代选择剩余
        lambda_param = 0.7  # 相关性 vs 多样性权衡

        while len(selected) < k and remaining:
            mmr_scores = []

            for doc, rel_score in remaining:
                # 计算与已选文档的最大相似度
                max_sim = max([
                    self._doc_similarity(doc, sel_doc)
                    for sel_doc, _ in selected
                ])

                # MMR 分数
                mmr = lambda_param * rel_score - (1 - lambda_param) * max_sim
                mmr_scores.append(mmr)

            # 选择 MMR 最高的
            best_idx = np.argmax(mmr_scores)
            selected.append(remaining.pop(best_idx))

        return selected

    def _doc_similarity(self, doc1, doc2):
        """计算文档间相似度"""
        emb1 = self.vectorstore._embedding_function.embed_query(doc1.page_content)
        emb2 = self.vectorstore._embedding_function.embed_query(doc2.page_content)
        return cosine_similarity(emb1, emb2)
```

**改进效果**:

```
测试集: 1000 个问题

指标                   | Naive RAG | 多阶段管道
-----------------------|-----------|------------
准确率                 | 62%       | 84%
召回率@5               | 71%       | 91%
平均相关性分数         | 0.73      | 0.89
错误实体率             | 23%       | 5%
平均延迟               | 0.8s      | 1.2s
```

---

## 案例 3: "文档被截断，导致关键信息丢失"

### 🔴 故障现象

```python
# 原始文档
original_doc = """
第三章：GPT-4 架构详解

3.1 模型规模
GPT-4 采用 MoE (Mixture of Experts) 架构，总参数量约 1.76 万亿。
其中，每次推理仅激活约 280B 参数，大幅降低了计算成本。

3.2 训练数据
训练数据截止到 2023 年 4 月，包含互联网文本、书籍、学术论文等。
数据量约 13 万亿 token，是 GPT-3 训练数据的 8 倍。

3.3 多模态能力
GPT-4 支持图像输入，能够理解图表、截图等视觉信息。
"""

# 分块后
chunks = chunk_document(original_doc, chunk_size=100, chunk_overlap=0)
# chunks[0]: "第三章：GPT-4 架构详解\n\n3.1 模型规模\nGPT-4 采用 MoE (Mixture of Experts) 架构，总参数"
# chunks[1]: "量约 1.76 万亿。\n其中，每次推理仅激活约 280B 参数，大幅降低了计算成本。\n\n3.2 训练数据"
# chunks[2]: "\n训练数据截止到 2023 年 4 月，包含互联网文本、书籍、学术论文等。\n数据量约 13 万亿 to"

# 用户查询
query = "GPT-4 的总参数量是多少？"

# 检索结果
retrieved_chunks = [chunks[1]]  # ❌ "量约 1.76 万亿..." - 缺少主语 "GPT-4"
```

### 🔍 根因分析 + 解决方案

#### 方案 1: 优化 Chunk Overlap

```python
def analyze_optimal_overlap(documents, queries, chunk_sizes=[200, 500, 1000]):
    """分析最优 overlap 参数"""
    results = []

    for chunk_size in chunk_sizes:
        for overlap_ratio in [0, 0.1, 0.2, 0.3, 0.5]:
            overlap = int(chunk_size * overlap_ratio)

            # 分块
            chunks = chunk_document(documents, chunk_size, overlap)

            # 构建向量库
            vectorstore = build_vectorstore(chunks)

            # 测试检索质量
            recall_scores = []
            for query in queries:
                retrieved = vectorstore.similarity_search(query, k=3)
                # 评估是否包含完整答案
                recall = evaluate_answer_completeness(query, retrieved)
                recall_scores.append(recall)

            results.append({
                "chunk_size": chunk_size,
                "overlap_ratio": overlap_ratio,
                "recall": np.mean(recall_scores)
            })

    return pd.DataFrame(results)

# 典型结果
"""
chunk_size | overlap_ratio | recall
-----------|---------------|--------
200        | 0.0           | 0.62
200        | 0.1           | 0.71
200        | 0.2           | 0.78  ← 显著提升
200        | 0.3           | 0.79
500        | 0.0           | 0.74
500        | 0.2           | 0.86  ← 最优点
1000       | 0.2           | 0.82
"""

# 结论: chunk_size=500, overlap=100 (20%) 最佳
```

#### 方案 2: Parent-Child Chunking

```python
class ParentChildChunker:
    """父子文档分块策略"""

    def __init__(self, parent_size=2000, child_size=500, child_overlap=100):
        self.parent_size = parent_size
        self.child_size = child_size
        self.child_overlap = child_overlap

    def chunk(self, documents):
        """生成父子文档对"""
        parent_chunks = []
        child_chunks = []

        for doc in documents:
            # 父文档：大块（保留完整上下文）
            parents = self._chunk_text(doc, self.parent_size, 0)

            for parent_id, parent in enumerate(parents):
                parent_chunks.append({
                    "id": f"parent_{parent_id}",
                    "content": parent,
                    "type": "parent"
                })

                # 子文档：小块（用于检索）
                children = self._chunk_text(parent, self.child_size, self.child_overlap)

                for child_id, child in enumerate(children):
                    child_chunks.append({
                        "id": f"child_{parent_id}_{child_id}",
                        "content": child,
                        "parent_id": f"parent_{parent_id}",
                        "type": "child"
                    })

        return parent_chunks, child_chunks

    def _chunk_text(self, text, size, overlap):
        """文本分块"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunks.append(text[start:end])
            start += (size - overlap)
        return chunks

class ParentChildRetriever:
    """父子文档检索器"""

    def __init__(self, parent_chunks, child_chunks, embedding_model):
        self.parent_chunks = {p['id']: p for p in parent_chunks}

        # 只为子文档建索引
        self.vectorstore = Chroma.from_texts(
            texts=[c['content'] for c in child_chunks],
            metadatas=[{"parent_id": c['parent_id'], "id": c['id']} for c in child_chunks],
            embedding=embedding_model
        )

    def retrieve(self, query, k=3):
        """检索 → 返回父文档"""
        # Step 1: 检索子文档
        child_results = self.vectorstore.similarity_search(query, k=k*2)

        # Step 2: 获取对应的父文档
        parent_ids = set([doc.metadata['parent_id'] for doc in child_results])

        # Step 3: 返回父文档（完整上下文）
        parent_docs = [self.parent_chunks[pid] for pid in parent_ids]

        return parent_docs[:k]

# 使用示例
chunker = ParentChildChunker(parent_size=2000, child_size=500)
parents, children = chunker.chunk(documents)

retriever = ParentChildRetriever(parents, children, OpenAIEmbeddings())
results = retriever.retrieve("GPT-4 的总参数量是多少？")

# 返回: 完整的父文档（2000 字），包含完整上下文
```

**原理解析**:

```
父子分块的优势：

传统分块:
  检索单元 = 返回单元 = 500 字

  问题：
  - 500 字可能语义不完整
  - 增大 chunk_size → 检索精度下降（噪音多）
  - 减小 chunk_size → 上下文不完整

父子分块:
  检索单元 = 500 字（细粒度，精确匹配）
  返回单元 = 2000 字（完整上下文）

  优势：
  - 检索：小块精确定位
  - 生成：大块提供充分上下文

类比：
  传统方式 = 在整本书中搜索
  父子方式 = 在章节标题中搜索，返回整章内容
```

#### 方案 3: Sentence Window Retrieval

```python
class SentenceWindowRetriever:
    """句子窗口检索器"""

    def __init__(self, documents, window_size=3):
        """
        window_size: 返回目标句子前后各 N 句
        """
        self.window_size = window_size
        self.sentences = self._split_into_sentences(documents)

        # 为每个句子建索引
        self.vectorstore = Chroma.from_texts(
            texts=[s['text'] for s in self.sentences],
            metadatas=[{"idx": s['idx'], "doc_id": s['doc_id']} for s in self.sentences],
            embedding=OpenAIEmbeddings()
        )

    def _split_into_sentences(self, documents):
        """分句并保留位置信息"""
        import nltk
        nltk.download('punkt', quiet=True)

        all_sentences = []
        for doc_id, doc in enumerate(documents):
            sentences = nltk.sent_tokenize(doc.page_content)
            for idx, sent in enumerate(sentences):
                all_sentences.append({
                    "text": sent,
                    "idx": idx,
                    "doc_id": doc_id,
                    "total_sentences": len(sentences)
                })

        return all_sentences

    def retrieve(self, query, k=3):
        """检索 → 返回句子窗口"""
        # 检索最相关的句子
        results = self.vectorstore.similarity_search(query, k=k)

        expanded_results = []
        for doc in results:
            idx = doc.metadata['idx']
            doc_id = doc.metadata['doc_id']

            # 扩展到窗口
            start_idx = max(0, idx - self.window_size)
            end_idx = min(
                idx + self.window_size + 1,
                self.sentences[0]['total_sentences']  # 简化，实际需查找
            )

            # 获取窗口内的句子
            window_sentences = [
                s['text'] for s in self.sentences
                if s['doc_id'] == doc_id and start_idx <= s['idx'] < end_idx
            ]

            expanded_results.append({
                "target_sentence": doc.page_content,
                "window_context": " ".join(window_sentences),
                "metadata": doc.metadata
            })

        return expanded_results

# 使用示例
retriever = SentenceWindowRetriever(documents, window_size=2)
results = retriever.retrieve("GPT-4 的总参数量是多少？")

# 返回示例:
# {
#   "target_sentence": "总参数量约 1.76 万亿。",
#   "window_context": "GPT-4 采用 MoE 架构。总参数量约 1.76 万亿。每次推理仅激活约 280B 参数。",
#   "metadata": {...}
# }
```

---

### ✅ 最佳实践建议

```python
# 根据文档类型选择策略

# 场景 1: 技术文档（结构化强）
# 推荐: Parent-Child Chunking
config = {
    "parent_size": 2000,  # 一个完整小节
    "child_size": 500,    # 一个段落
    "child_overlap": 100
}

# 场景 2: 对话记录（上下文依赖强）
# 推荐: Sentence Window Retrieval
config = {
    "window_size": 5  # 前后各 5 句
}

# 场景 3: 学术论文（逻辑连贯性强）
# 推荐: Recursive Chunking（按章节 → 段落层级分块）
config = {
    "separators": ["\n\n## ", "\n\n### ", "\n\n", "\n", " "],
    "chunk_size": 1000,
    "chunk_overlap": 200
}

# 场景 4: 代码文档（精确匹配重要）
# 推荐: Semantic Chunking（按函数/类边界分块）
config = {
    "language": "python",
    "split_by": "function"  # 按函数定义分块
}
```

---

# 第二部分：生成质量问题

## 案例 4: "LLM 产生幻觉，编造了不存在的信息"

### 🔴 故障现象

```python
# 检索到的上下文
context = """
GPT-4 是 OpenAI 在 2023 年 3 月发布的多模态大模型。
它在多个基准测试中表现优异，超越了 GPT-3.5。
该模型的参数量未公开，但业界推测在万亿级别。
"""

# 用户问题
query = "GPT-4 的具体参数量是多少？"

# LLM 生成答案
answer = """
根据文档，GPT-4 拥有约 1.76 万亿参数，采用 MoE 架构。
每次推理仅激活约 280B 参数，大幅降低了计算成本。
"""

# ❌ 问题：文档中明确说"未公开"，但 LLM 编造了 "1.76 万亿" 这个数字！
```

### 🔍 根因分析

#### 层次 1: Prompt 设计不当

```python
# ❌ 错误的 Prompt 设计
bad_prompt = f"""
根据以下上下文回答问题：

上下文：{context}

问题：{query}

答案：
"""

# 问题：
# 1. 没有明确禁止幻觉
# 2. 没有要求引用来源
# 3. 没有处理"无法回答"的情况

# ✅ 正确的 Prompt 设计
good_prompt = f"""
你是一个严谨的问答助手。请**严格基于**以下上下文回答问题。

【重要规则】
1. 仅使用上下文中的信息，不要添加任何外部知识
2. 如果上下文中没有足够信息，明确回复"根据提供的文档，无法回答该问题"
3. 引用具体的文档编号或段落
4. 对于数字、日期等关键信息，必须直接引用原文

上下文：
{context}

问题：{query}

答案（请遵守上述规则）：
"""
```

**深度分析：Prompt Engineering 的 5 个关键要素**

```python
class GroundedPromptBuilder:
    """基于事实的 Prompt 构建器"""

    def build(self, query, contexts, enable_citation=True):
        """构建防幻觉 Prompt"""

        # 要素 1: 角色定位（System Message）
        system_msg = """
        你是一个专业的文档问答助手。你的回答必须完全基于提供的参考文档，
        不能使用任何训练数据中的知识。
        """

        # 要素 2: 明确禁止幻觉
        constraint = """
        【严格限制】
        - ✅ 允许：总结、归纳、整理文档中的信息
        - ❌ 禁止：添加文档中不存在的信息
        - ❌ 禁止：根据常识或训练数据推测答案
        - ❌ 禁止：编造具体的数字、日期、人名等
        """

        # 要素 3: 无法回答的处理
        fallback = """
        【无法回答时】
        如果文档中没有相关信息，请回复：
        "根据提供的文档，无法回答该问题。文档中缺少关于 [具体缺少什么] 的信息。"
        """

        # 要素 4: 引用格式（可选）
        citation_format = ""
        if enable_citation:
            citation_format = """
            【引用格式】
            回答时，使用 [文档N] 标注信息来源，例如：
            "GPT-4 在 2023 年 3 月发布 [文档1]。"
            """

        # 要素 5: 结构化上下文
        structured_context = self._structure_contexts(contexts)

        # 组合 Prompt
        prompt = f"""
        {system_msg}

        {constraint}

        {fallback}

        {citation_format}

        参考文档：
        {structured_context}

        用户问题：{query}

        你的回答：
        """

        return prompt

    def _structure_contexts(self, contexts):
        """结构化上下文（增强可引用性）"""
        structured = []
        for i, ctx in enumerate(contexts, 1):
            structured.append(f"""
【文档 {i}】
来源：{ctx.metadata.get('source', '未知')}
内容：{ctx.page_content}
            """)
        return "\n".join(structured)

# 使用示例
builder = GroundedPromptBuilder()
prompt = builder.build(query, contexts, enable_citation=True)
```

#### 层次 2: Temperature 参数设置不当

```python
# 实验：Temperature 对幻觉的影响

def test_temperature_impact(prompt, temperatures=[0.0, 0.3, 0.7, 1.0]):
    """测试不同 Temperature 下的幻觉率"""
    results = []

    for temp in temperatures:
        hallucination_count = 0
        total_runs = 10  # 每个温度运行 10 次

        for _ in range(total_runs):
            # 调用 LLM
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=temp
            )

            answer = response.choices[0].message.content

            # 检测幻觉（简化：检查是否包含上下文中不存在的数字）
            if has_hallucination(answer, context):
                hallucination_count += 1

        hallucination_rate = hallucination_count / total_runs
        results.append({
            "temperature": temp,
            "hallucination_rate": hallucination_rate
        })

    return results

# 典型结果
"""
Temperature | Hallucination Rate
------------|-------------------
0.0         | 12%  ← 最低（推荐用于事实性回答）
0.3         | 18%
0.7         | 35%  ← OpenAI 默认值
1.0         | 52%  ← 高度创造性，但幻觉严重
"""

# ✅ 最佳实践
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.0,  # 事实性回答：使用 0 或极低值
    # temperature=0.7  # 创意写作：可以使用较高值
)
```

**深度原理：Temperature 的数学本质**

```
Temperature 的作用机制：

LLM 生成下一个 token 时的概率分布：

原始 logits: [2.3, 1.8, 0.5, 0.1]
           (对应 token: ["万亿", "未公开", "很多", "少量"])

步骤 1: 除以 temperature
  temp=0.1: [23.0, 18.0, 5.0, 1.0]  → 差距被放大
  temp=1.0: [2.3, 1.8, 0.5, 0.1]    → 原始分布
  temp=2.0: [1.15, 0.9, 0.25, 0.05] → 差距被缩小

步骤 2: Softmax 归一化
  temp=0.1: [0.89, 0.10, 0.01, 0.00] → 接近确定性
  temp=1.0: [0.52, 0.32, 0.10, 0.06] → 较为随机
  temp=2.0: [0.42, 0.33, 0.15, 0.10] → 高度随机

影响：
- temp → 0: 总是选择概率最高的 token（确定性，低幻觉）
- temp → ∞: 所有 token 概率趋于相等（随机性，高幻觉）

为什么 temp=0 能减少幻觉？
  → 模型会选择训练数据中最常见的模式
  → "未公开" 在上下文中明确出现，概率最高
  → "万亿" 虽然在知识中存在，但上下文概率低
```

#### 层次 3: 缺少事后验证机制

```python
class FactualityVerifier:
    """事实性验证器"""

    def __init__(self, llm):
        self.llm = llm

    def verify_answer(self, question, context, answer):
        """验证答案是否基于上下文"""

        # 方法 1: 事实提取 + 验证
        verification_prompt = f"""
你是一个严格的事实检查员。请检查答案中的每个陈述是否能在上下文中找到依据。

上下文：
{context}

答案：
{answer}

任务：
1. 提取答案中的所有事实性陈述（数字、日期、人名、事件等）
2. 对每个陈述，检查是否在上下文中有明确依据
3. 输出 JSON 格式的验证结果

输出格式：
{{
  "claims": [
    {{
      "statement": "具体陈述",
      "supported": true/false,
      "evidence": "上下文中的依据（如果有）"
    }}
  ],
  "overall_verdict": "PASS/FAIL",
  "hallucinated_claims": []
}}
"""

        response = self.llm.predict(verification_prompt)
        verification_result = json.loads(response)

        # 如果检测到幻觉，触发警告或重生成
        if verification_result["overall_verdict"] == "FAIL":
            return {
                "verified": False,
                "issues": verification_result["hallucinated_claims"],
                "action": "REGENERATE"
            }

        return {
            "verified": True,
            "action": "ACCEPT"
        }

    def verify_with_entailment(self, context, answer):
        """使用自然语言推理（NLI）验证"""
        from transformers import pipeline

        # 加载 NLI 模型
        nli_model = pipeline(
            "text-classification",
            model="microsoft/deberta-v3-large-mnli"
        )

        # 检查答案是否能从上下文推断出来
        result = nli_model(f"{context} [SEP] {answer}")

        # 结果：entailment (蕴含), neutral (中立), contradiction (矛盾)
        if result[0]['label'] == 'CONTRADICTION':
            return {
                "verified": False,
                "reason": "答案与上下文矛盾"
            }
        elif result[0]['label'] == 'NEUTRAL' and result[0]['score'] > 0.8:
            return {
                "verified": False,
                "reason": "答案无法从上下文推断"
            }

        return {"verified": True}

# 使用示例
verifier = FactualityVerifier(llm)

# 生成答案
answer = qa_chain.run({"question": query, "context": context})

# 验证答案
verification = verifier.verify_answer(query, context, answer)

if not verification["verified"]:
    print(f"❌ 检测到幻觉: {verification['issues']}")
    # 触发重生成，并在 Prompt 中加入警告
    enhanced_prompt = f"""
    {original_prompt}

    【警告】之前的回答存在以下错误：
    {verification['issues']}

    请重新回答，确保严格基于上下文。
    """
    answer = llm.predict(enhanced_prompt)
```

#### 层次 4: 缺少引用约束

```python
class CitationEnforcedQA:
    """强制引用的问答系统"""

    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever

    def answer_with_citation(self, query):
        """生成带引用的答案"""

        # 1. 检索文档
        contexts = self.retriever.retrieve(query, k=3)

        # 2. 构建强制引用的 Prompt
        prompt = self._build_citation_prompt(query, contexts)

        # 3. 生成答案
        raw_answer = self.llm.predict(prompt)

        # 4. 验证引用格式
        validated_answer = self._validate_citations(raw_answer, contexts)

        return validated_answer

    def _build_citation_prompt(self, query, contexts):
        """构建强制引用 Prompt"""

        # 为每个文档编号
        numbered_contexts = []
        for i, ctx in enumerate(contexts, 1):
            numbered_contexts.append(f"[{i}] {ctx.page_content}")

        context_str = "\n\n".join(numbered_contexts)

        prompt = f"""
你是一个专业的问答助手。请基于参考文档回答问题，并使用 [编号] 标注来源。

参考文档：
{context_str}

用户问题：{query}

【强制要求】
1. 每个陈述后必须标注来源，格式：[1] [2] 等
2. 不得使用文档中不存在的信息
3. 示例格式：
   "GPT-4 在 2023 年 3 月发布 [1]，在多个基准测试中表现优异 [2]。"

你的回答：
"""
        return prompt

    def _validate_citations(self, answer, contexts):
        """验证引用的有效性"""
        import re

        # 提取所有引用编号
        citation_pattern = r'\[(\d+)\]'
        citations = re.findall(citation_pattern, answer)

        # 检查引用编号是否有效
        max_index = len(contexts)
        invalid_citations = [int(c) for c in citations if int(c) > max_index]

        if invalid_citations:
            print(f"⚠️  警告：发现无效引用编号 {invalid_citations}")
            # 可以选择移除无效引用或重新生成
            answer = re.sub(r'\[\d+\]', '', answer)  # 简单处理：移除所有引用

        # 检查是否缺少引用
        sentences = answer.split('。')
        uncited_sentences = [s for s in sentences if not re.search(citation_pattern, s)]

        if len(uncited_sentences) > len(sentences) * 0.3:  # 超过 30% 句子无引用
            print(f"⚠️  警告：{len(uncited_sentences)} 个句子缺少引用")

        return {
            "answer": answer,
            "citation_coverage": 1 - len(uncited_sentences) / len(sentences),
            "valid": len(invalid_citations) == 0
        }

# 使用示例
qa_system = CitationEnforcedQA(llm, retriever)
result = qa_system.answer_with_citation("GPT-4 的参数量是多少？")

print(result["answer"])
# 输出示例：
# "根据文档，GPT-4 的参数量未公开 [1]，但业界推测在万亿级别 [1]。"
```

### ✅ 完整防幻觉方案

```python
class HallucinationFreeRAG:
    """防幻觉 RAG 系统"""

    def __init__(self, retriever, llm, config):
        self.retriever = retriever
        self.llm = llm
        self.config = config
        self.verifier = FactualityVerifier(llm)

    def answer(self, query, max_retries=2):
        """生成防幻觉答案（带重试机制）"""

        for attempt in range(max_retries):
            # Step 1: 检索
            contexts = self.retriever.retrieve(query, k=self.config['k'])

            # Step 2: 构建防幻觉 Prompt
            prompt = self._build_grounded_prompt(query, contexts)

            # Step 3: 生成答案（低 temperature）
            answer = self.llm.predict(
                prompt,
                temperature=0.0,  # 确定性生成
                max_tokens=self.config.get('max_tokens', 500)
            )

            # Step 4: 事后验证
            verification = self.verifier.verify_answer(query, contexts, answer)

            if verification["verified"]:
                # 验证通过，返回答案
                return {
                    "answer": answer,
                    "contexts": contexts,
                    "verified": True,
                    "attempt": attempt + 1
                }
            else:
                # 验证失败，记录日志并重试
                print(f"⚠️  第 {attempt + 1} 次尝试验证失败: {verification['issues']}")

                # 在下一次尝试中加强 Prompt
                if attempt < max_retries - 1:
                    self.config['extra_constraint'] = f"""
                    【警告】之前的回答存在错误：{verification['issues']}
                    请严格基于上下文，不要添加任何外部信息。
                    """

        # 所有重试都失败，返回保守答案
        return {
            "answer": "抱歉，我无法基于提供的文档准确回答您的问题。",
            "contexts": contexts,
            "verified": False,
            "attempt": max_retries
        }

    def _build_grounded_prompt(self, query, contexts):
        """构建强化版防幻觉 Prompt"""

        base_constraint = """
        你是一个严谨的文档问答助手。**严格遵守**以下规则：

        【核心规则】
        1. 仅使用参考文档中的信息回答
        2. 对于数字、日期、人名等关键信息，必须在文档中有明确依据
        3. 如果文档中没有相关信息，回复："根据提供的文档，无法回答该问题。"
        4. 不要根据常识或训练数据进行推测

        【示例】
        ✅ 正确：文档明确提到"参数量未公开" → 回答"参数量未公开"
        ❌ 错误：文档说"未公开" → 回答"约 1.76 万亿"（编造数字）
        """

        extra_constraint = self.config.get('extra_constraint', '')

        # 结构化上下文
        context_str = "\n\n".join([
            f"【文档 {i+1}】\n{ctx.page_content}"
            for i, ctx in enumerate(contexts)
        ])

        prompt = f"""
        {base_constraint}

        {extra_constraint}

        参考文档：
        {context_str}

        用户问题：{query}

        你的回答（请遵守上述规则）：
        """

        return prompt

# 使用示例
hallucination_free_rag = HallucinationFreeRAG(
    retriever=retriever,
    llm=ChatOpenAI(model="gpt-4", temperature=0.0),
    config={"k": 3, "max_tokens": 500}
)

result = hallucination_free_rag.answer("GPT-4 的参数量是多少？")

if result["verified"]:
    print(f"✅ 答案（已验证）: {result['answer']}")
else:
    print(f"⚠️  答案（未通过验证）: {result['answer']}")
```

**改进效果**:

```
测试集: 500 个问题（包含 "无法回答" 类型）

指标                   | Naive RAG | 防幻觉 RAG
-----------------------|-----------|------------
幻觉率 (Hallucination) | 23%       | 3%
事实准确率             | 68%       | 94%
"无法回答"处理正确率   | 12%       | 87%
平均引用覆盖率         | 15%       | 82%
```

---

## 案例 5: "上下文窗口超限，关键信息被截断"

### 🔴 故障现象

```python
# 检索到 10 个相关文档，总长度 15,000 tokens
contexts = retrieve_top_k(query, k=10)  # 每个 ~1500 tokens

# 用户的 LLM 配置
llm = ChatOpenAI(model="gpt-3.5-turbo")  # 上下文窗口: 4096 tokens

# 构建 Prompt
prompt = build_prompt(query, contexts)  # 总长度: 16,500 tokens

# 调用 LLM
response = llm.predict(prompt)
# ❌ 错误: InvalidRequestError: maximum context length is 4096 tokens

# 或者：自动截断后，关键信息丢失
truncated_prompt = prompt[:4096]  # 简单截断
response = llm.predict(truncated_prompt)
# ❌ 答案不完整或错误
```

### 🔍 根因分析 + 解决方案

#### 方案 1: 智能压缩上下文

```python
class ContextCompressor:
    """上下文压缩器"""

    def __init__(self, llm, max_tokens=3000):
        self.llm = llm
        self.max_tokens = max_tokens

    def compress(self, query, contexts):
        """压缩上下文（保留最相关部分）"""

        # 方法 1: Extraction-based Compression
        compressed = self._extractive_compression(query, contexts)

        # 方法 2: Abstractive Compression（可选）
        if len(compressed) > self.max_tokens:
            compressed = self._abstractive_compression(query, compressed)

        return compressed

    def _extractive_compression(self, query, contexts):
        """提取式压缩（保留原文句子）"""
        from sentence_transformers import CrossEncoder

        # 加载句子级重排序模型
        reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')

        # Step 1: 句子级分割
        all_sentences = []
        for ctx in contexts:
            sentences = ctx.page_content.split('。')
            for sent in sentences:
                if sent.strip():
                    all_sentences.append({
                        "text": sent + '。',
                        "source": ctx.metadata.get('source', ''),
                        "score": 0.0
                    })

        # Step 2: 计算每个句子与查询的相关性
        if len(all_sentences) > 100:  # 避免计算量过大
            all_sentences = all_sentences[:100]

        pairs = [(query, sent["text"]) for sent in all_sentences]
        scores = reranker.predict(pairs)

        for sent, score in zip(all_sentences, scores):
            sent["score"] = score

        # Step 3: 按相关性排序
        all_sentences.sort(key=lambda x: x["score"], reverse=True)

        # Step 4: 贪心选择（保证总长度不超限）
        selected_sentences = []
        total_tokens = 0

        for sent in all_sentences:
            sent_tokens = len(sent["text"].split()) * 1.3  # 估算 token 数
            if total_tokens + sent_tokens <= self.max_tokens:
                selected_sentences.append(sent)
                total_tokens += sent_tokens
            else:
                break

        # Step 5: 重新排序（保持逻辑连贯性）
        # 按原文档顺序重排（可选）

        compressed_text = "\n".join([s["text"] for s in selected_sentences])
        return compressed_text

    def _abstractive_compression(self, query, text):
        """抽象式压缩（总结重写）"""

        compression_prompt = f"""
请将以下文本压缩为更简洁的版本，保留与问题相关的关键信息。

问题：{query}

原文：
{text}

要求：
1. 保留所有关键事实（数字、日期、人名等）
2. 删除冗余和无关信息
3. 保持逻辑连贯
4. 目标长度：不超过原文的 50%

压缩后的文本：
"""

        compressed = self.llm.predict(compression_prompt, max_tokens=self.max_tokens // 2)
        return compressed

# 使用示例
compressor = ContextCompressor(llm, max_tokens=3000)

# 检索大量文档
raw_contexts = retriever.retrieve(query, k=10)

# 压缩到可用长度
compressed_context = compressor.compress(query, raw_contexts)

# 构建 Prompt
prompt = build_prompt(query, compressed_context)
# 现在 prompt 长度在安全范围内
```

#### 方案 2: Map-Reduce 策略

```python
class MapReduceQA:
    """Map-Reduce 问答系统（处理长文档）"""

    def __init__(self, llm):
        self.llm = llm

    def answer(self, query, contexts):
        """Map-Reduce 回答流程"""

        # Step 1: Map 阶段 - 对每个文档单独提问
        partial_answers = []
        for i, ctx in enumerate(contexts):
            map_prompt = f"""
基于以下文档片段回答问题。如果片段中没有相关信息，回复"无相关信息"。

文档片段：
{ctx.page_content}

问题：{query}

简洁回答：
"""
            answer = self.llm.predict(map_prompt, max_tokens=200)

            if "无相关信息" not in answer:
                partial_answers.append({
                    "answer": answer,
                    "source": ctx.metadata.get('source', f'文档{i+1}')
                })

        # Step 2: Reduce 阶段 - 合并所有部分答案
        if not partial_answers:
            return "根据检索到的文档，无法回答该问题。"

        reduce_prompt = f"""
以下是针对同一问题的多个部分答案。请将它们合并为一个完整、连贯的最终答案。

问题：{query}

部分答案：
{self._format_partial_answers(partial_answers)}

要求：
1. 去除重复信息
2. 整合所有相关信息
3. 保持逻辑连贯
4. 标注信息来源

最终答案：
"""

        final_answer = self.llm.predict(reduce_prompt, max_tokens=500)
        return final_answer

    def _format_partial_answers(self, partial_answers):
        """格式化部分答案"""
        formatted = []
        for i, pa in enumerate(partial_answers, 1):
            formatted.append(f"{i}. [{pa['source']}] {pa['answer']}")
        return "\n\n".join(formatted)

# 使用示例
map_reduce_qa = MapReduceQA(llm)

# 即使有 100 个文档也能处理
many_contexts = retriever.retrieve(query, k=100)

answer = map_reduce_qa.answer(query, many_contexts)
# Map-Reduce 会自动处理超长上下文
```

#### 方案 3: 层级摘要（Refine）

```python
class RefineQA:
    """迭代精炼问答系统"""

    def __init__(self, llm):
        self.llm = llm

    def answer(self, query, contexts):
        """迭代精炼回答"""

        # 初始答案
        initial_prompt = f"""
基于以下文档回答问题：

文档：
{contexts[0].page_content}

问题：{query}

答案：
"""

        current_answer = self.llm.predict(initial_prompt)

        # 迭代精炼（逐个引入新文档）
        for i, ctx in enumerate(contexts[1:], 1):
            refine_prompt = f"""
你之前的答案是：
{current_answer}

现在有新的文档片段：
{ctx.page_content}

问题：{query}

请基于新文档**改进或补充**你的答案：
1. 如果新文档提供了更多信息，添加到答案中
2. 如果新文档纠正了之前的错误，更新答案
3. 如果新文档无关，保持原答案

改进后的答案：
"""

            current_answer = self.llm.predict(refine_prompt, max_tokens=500)

        return current_answer

# 使用示例
refine_qa = RefineQA(llm)
answer = refine_qa.answer(query, contexts)
```

**三种策略对比**:

```
策略            | 适用场景               | 优点                 | 缺点
----------------|------------------------|----------------------|---------------------
压缩 (Compress) | 上下文略超限 (1-2倍)   | 保留最相关信息       | 可能丢失细节
Map-Reduce      | 海量文档 (10+ 个)      | 可扩展性强           | 部分答案可能不连贯
Refine          | 中等数量 (5-10 个)     | 答案质量高、连贯性好 | 需要多次 LLM 调用

成本对比（假设 10 个文档，每个 1000 tokens）：
- 压缩: 1 次 LLM 调用 (压缩) + 1 次 (生成答案) = 2 次
- Map-Reduce: 10 次 (Map) + 1 次 (Reduce) = 11 次
- Refine: 10 次 (迭代精炼) = 10 次
```

### ✅ 自适应策略选择

```python
class AdaptiveContextHandler:
    """自适应上下文处理器"""

    def __init__(self, llm, model_context_limit=4096):
        self.llm = llm
        self.model_context_limit = model_context_limit
        self.compressor = ContextCompressor(llm)
        self.map_reduce_qa = MapReduceQA(llm)
        self.refine_qa = RefineQA(llm)

    def answer(self, query, contexts):
        """根据上下文长度自动选择策略"""

        # 估算总 token 数
        total_tokens = self._estimate_tokens(query, contexts)

        # 决策逻辑
        if total_tokens <= self.model_context_limit * 0.8:
            # 场景 1: 上下文在限制内，直接使用
            print("✅ 策略：直接回答（上下文未超限）")
            return self._direct_answer(query, contexts)

        elif total_tokens <= self.model_context_limit * 2:
            # 场景 2: 轻微超限，使用压缩
            print("⚠️  策略：压缩上下文后回答")
            compressed = self.compressor.compress(query, contexts)
            return self._direct_answer(query, [compressed])

        elif len(contexts) <= 10:
            # 场景 3: 中等数量，使用 Refine
            print("⚠️  策略：迭代精炼回答 (Refine)")
            return self.refine_qa.answer(query, contexts)

        else:
            # 场景 4: 大量文档，使用 Map-Reduce
            print("⚠️  策略：Map-Reduce 回答")
            return self.map_reduce_qa.answer(query, contexts)

    def _estimate_tokens(self, query, contexts):
        """估算总 token 数"""
        # 简化估算：1 token ≈ 0.75 个英文单词 ≈ 1.3 个中文字符
        total_chars = len(query)
        for ctx in contexts:
            total_chars += len(ctx.page_content)

        return int(total_chars * 1.3)  # 保守估计

    def _direct_answer(self, query, contexts):
        """直接回答（不使用特殊策略）"""
        context_str = "\n\n".join([
            ctx.page_content if isinstance(ctx, str) else ctx
            for ctx in contexts
        ])

        prompt = f"""
参考文档：
{context_str}

问题：{query}

答案：
"""

        return self.llm.predict(prompt)

# 使用示例
adaptive_handler = AdaptiveContextHandler(
    llm=ChatOpenAI(model="gpt-3.5-turbo"),
    model_context_limit=4096
)

# 自动适应不同情况
answer = adaptive_handler.answer(query, contexts)
# 系统会自动选择最佳策略
```

---

# 第三部分：性能与成本问题

## 案例 6: "延迟太高，用户等待时间过长"

### 🔴 故障现象

```python
import time

start = time.time()
answer = rag_system.answer("GPT-4 的参数量是多少？")
latency = time.time() - start

print(f"总延迟: {latency:.2f}s")  # 输出: 总延迟: 8.5s
# ❌ 问题：用户体验差，8.5 秒太慢
```

### 🔍 延迟分析（分解各阶段耗时）

```python
class LatencyProfiler:
    """延迟分析器"""

    def __init__(self, rag_system):
        self.rag_system = rag_system
        self.metrics = {}

    def profile(self, query):
        """分析各阶段延迟"""
        import time

        total_start = time.time()

        # 阶段 1: Embedding 查询
        embed_start = time.time()
        query_embedding = self.rag_system.embedding_model.embed_query(query)
        embed_time = time.time() - embed_start

        # 阶段 2: 向量检索
        search_start = time.time()
        contexts = self.rag_system.vectorstore.similarity_search(query, k=5)
        search_time = time.time() - search_start

        # 阶段 3: 重排序（如果有）
        rerank_start = time.time()
        if self.rag_system.reranker:
            contexts = self.rag_system.reranker.rerank(query, contexts)
        rerank_time = time.time() - rerank_start

        # 阶段 4: Prompt 构建
        prompt_start = time.time()
        prompt = self.rag_system.build_prompt(query, contexts)
        prompt_time = time.time() - prompt_start

        # 阶段 5: LLM 生成
        llm_start = time.time()
        answer = self.rag_system.llm.predict(prompt)
        llm_time = time.time() - llm_start

        total_time = time.time() - total_start

        # 返回分析结果
        return {
            "total_latency": total_time,
            "breakdown": {
                "embedding": embed_time,
                "search": search_time,
                "rerank": rerank_time,
                "prompt_build": prompt_time,
                "llm_generation": llm_time
            },
            "percentages": {
                "embedding": embed_time / total_time * 100,
                "search": search_time / total_time * 100,
                "rerank": rerank_time / total_time * 100,
                "prompt_build": prompt_time / total_time * 100,
                "llm_generation": llm_time / total_time * 100
            }
        }

# 使用示例
profiler = LatencyProfiler(rag_system)
profile_result = profiler.profile("GPT-4 的参数量是多少？")

print("=== 延迟分析 ===")
for stage, latency in profile_result["breakdown"].items():
    percentage = profile_result["percentages"][stage]
    print(f"{stage:15s}: {latency:.3f}s ({percentage:.1f}%)")

# 典型输出：
"""
=== 延迟分析 ===
embedding      : 0.080s (0.9%)
search         : 0.350s (4.1%)
rerank         : 1.200s (14.1%)
prompt_build   : 0.020s (0.2%)
llm_generation : 6.850s (80.6%)  ← 主要瓶颈！
---------------------------------
Total          : 8.500s (100.0%)
"""
```

### 🔧 性能优化方案

#### 优化 1: 流式输出（降低感知延迟）

```python
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class StreamingRAG:
    """支持流式输出的 RAG"""

    def __init__(self, llm_streaming, retriever):
        self.llm = llm_streaming
        self.retriever = retriever

    def answer_stream(self, query):
        """流式生成答案"""

        # 1. 检索（这部分仍是批量）
        contexts = self.retriever.retrieve(query, k=3)

        # 2. 构建 Prompt
        prompt = self.build_prompt(query, contexts)

        # 3. 流式生成
        print("💡 答案: ", end="", flush=True)

        for chunk in self.llm.stream(prompt):
            print(chunk.content, end="", flush=True)  # 实时打印
            yield chunk.content  # 流式返回

        print()  # 换行

# 使用示例
from langchain.chat_models import ChatOpenAI

streaming_llm = ChatOpenAI(
    model="gpt-4",
    streaming=True,  # 启用流式
    callbacks=[StreamingStdOutCallbackHandler()]
)

streaming_rag = StreamingRAG(streaming_llm, retriever)

# 流式回答（降低感知延迟）
for chunk in streaming_rag.answer_stream(query):
    pass  # chunk 已被打印
# 用户在 0.5s 后就能看到第一个词，而不是等待 8.5s
```

#### 优化 2: 并行化检索和重排序

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelRAG:
    """并行化 RAG 系统"""

    def __init__(self, vectorstore, reranker, llm):
        self.vectorstore = vectorstore
        self.reranker = reranker
        self.llm = llm
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def answer_async(self, query):
        """异步并行回答"""

        # 并行执行：Embedding + BM25检索（如果有）
        tasks = [
            self._async_vector_search(query),
            # self._async_bm25_search(query)  # 可选
        ]

        search_results = await asyncio.gather(*tasks)
        vector_results = search_results[0]

        # 重排序
        reranked = await self._async_rerank(query, vector_results)

        # 构建 Prompt
        prompt = self.build_prompt(query, reranked)

        # LLM 生成
        answer = await self._async_llm_generate(prompt)

        return answer

    async def _async_vector_search(self, query):
        """异步向量检索"""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            self.executor,
            self.vectorstore.similarity_search,
            query,
            5
        )
        return results

    async def _async_rerank(self, query, candidates):
        """异步重排序"""
        loop = asyncio.get_event_loop()
        reranked = await loop.run_in_executor(
            self.executor,
            self.reranker.rerank,
            query,
            candidates
        )
        return reranked

    async def _async_llm_generate(self, prompt):
        """异步 LLM 生成"""
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            self.executor,
            self.llm.predict,
            prompt
        )
        return answer

# 使用示例
parallel_rag = ParallelRAG(vectorstore, reranker, llm)

# 异步调用
import asyncio
answer = asyncio.run(parallel_rag.answer_async(query))

# 改进效果:
# Before: 8.5s (串行)
# After:  5.2s (并行，节省约 40%)
```

#### 优化 3: 缓存热门查询

```python
from functools import lru_cache
import hashlib

class CachedRAG:
    """带缓存的 RAG 系统"""

    def __init__(self, rag_system, cache_size=100):
        self.rag_system = rag_system
        self.cache_size = cache_size
        self.cache = {}

    def answer(self, query):
        """带缓存的回答"""

        # 计算查询哈希
        query_hash = hashlib.md5(query.encode()).hexdigest()

        # 检查缓存
        if query_hash in self.cache:
            print("✅ 命中缓存")
            return self.cache[query_hash]

        # 未命中，调用原系统
        answer = self.rag_system.answer(query)

        # 写入缓存（LRU策略）
        if len(self.cache) >= self.cache_size:
            # 移除最旧的条目（简化实现）
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[query_hash] = answer

        return answer

# 使用示例
cached_rag = CachedRAG(rag_system, cache_size=100)

# 第一次查询: 8.5s
answer1 = cached_rag.answer("GPT-4 的参数量是多少？")

# 第二次相同查询: < 0.001s（命中缓存）
answer2 = cached_rag.answer("GPT-4 的参数量是多少？")
```

#### 优化 4: 使用更快的 Embedding 模型

```python
# 对比不同 Embedding 模型的速度

models_comparison = [
    {
        "name": "text-embedding-ada-002",
        "dimension": 1536,
        "latency_per_query": "80ms",
        "quality": "⭐⭐⭐⭐⭐",
        "cost": "$$$$"
    },
    {
        "name": "all-MiniLM-L6-v2 (local)",
        "dimension": 384,
        "latency_per_query": "15ms",  # ← 快 5 倍！
        "quality": "⭐⭐⭐⭐",
        "cost": "$0 (本地)"
    },
    {
        "name": "bge-small-zh-v1.5 (中文)",
        "dimension": 512,
        "latency_per_query": "20ms",
        "quality": "⭐⭐⭐⭐",
        "cost": "$0 (本地)"
    }
]

# 使用本地 Embedding 模型
from sentence_transformers import SentenceTransformer

class LocalEmbeddingRAG:
    """使用本地 Embedding 的 RAG"""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # 加载本地模型
        self.embedding_model = SentenceTransformer(model_name)

        # 其他组件保持不变
        # ...

    def embed_query(self, query):
        """本地 Embedding（无网络延迟）"""
        return self.embedding_model.encode(query)

# 使用示例
local_rag = LocalEmbeddingRAG()

# Embedding 延迟: 80ms → 15ms（节省 65ms）
```

#### 优化 5: 减少重排序候选数量

```python
# 重排序是瓶颈之一（CrossEncoder 慢）

# ❌ 低效：重排序所有候选
vector_results = vectorstore.similarity_search(query, k=20)  # 20 个候选
reranked = reranker.rerank(query, vector_results)  # 重排序 20 个（慢！）

# ✅ 高效：只重排序 Top-K
vector_results = vectorstore.similarity_search(query, k=20)
top_candidates = vector_results[:10]  # 只取前 10 个
reranked = reranker.rerank(query, top_candidates)  # 重排序 10 个（快 2 倍）

# 改进效果:
# Rerank 20 个: 1.2s
# Rerank 10 个: 0.6s（节省 50%）
```

### ✅ 完整性能优化方案

```python
class OptimizedRAG:
    """全方位优化的 RAG 系统"""

    def __init__(self, config):
        # 1. 使用本地 Embedding（减少网络延迟）
        self.embedding_model = SentenceTransformer(config['embedding_model'])

        # 2. 向量数据库（使用 HNSW 索引）
        self.vectorstore = Chroma(
            embedding_function=self.embedding_model,
            collection_metadata={"hnsw:space": "cosine"}
        )

        # 3. 轻量级重排序
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')  # 小模型

        # 4. 流式 LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",  # 比 GPT-4 快 3 倍
            streaming=True,
            temperature=0.0
        )

        # 5. 缓存
        self.cache = {}

    def answer(self, query, use_cache=True):
        """优化后的回答流程"""

        # 缓存检查
        if use_cache and query in self.cache:
            return self.cache[query]

        # 并行检索
        contexts = self._parallel_retrieve(query)

        # 构建 Prompt
        prompt = self._build_prompt(query, contexts)

        # 流式生成
        answer = ""
        for chunk in self.llm.stream(prompt):
            answer += chunk.content
            print(chunk.content, end="", flush=True)

        # 写入缓存
        if use_cache:
            self.cache[query] = answer

        return answer

    def _parallel_retrieve(self, query):
        """并行检索（向量 + 重排序）"""
        import time

        # 向量检索
        start = time.time()
        vector_results = self.vectorstore.similarity_search(query, k=10)
        print(f"🔍 向量检索: {time.time() - start:.3f}s")

        # 重排序（只重排前 5 个）
        start = time.time()
        top_candidates = vector_results[:5]
        reranked = self._rerank(query, top_candidates)
        print(f"🔄 重排序: {time.time() - start:.3f}s")

        return reranked[:3]  # 返回 Top-3

# 使用示例
optimized_rag = OptimizedRAG({
    "embedding_model": "all-MiniLM-L6-v2"
})

answer = optimized_rag.answer("GPT-4 的参数量是多少？")

# 性能对比:
# Before: 8.5s
# After:  2.1s（提升 75%）
```

**优化效果汇总**:

```
优化项                  | 延迟减少  | 成本影响
------------------------|-----------|------------
流式输出                | 感知 -90% | 无
本地 Embedding          | -65ms     | 节省 API 费用
并行化                  | -40%      | 无
缓存 (命中时)           | -99%      | 无
减少重排序候选          | -50%      | 无
使用 GPT-3.5 替代 GPT-4 | -70%      | 节省 90% 费用

综合优化后：
- 总延迟: 8.5s → 2.1s（提升 75%）
- 流式首字延迟: < 0.5s
- 成本: 减少约 60%
```

---

## 案例 7: "成本太高，每月 API 费用过万"

### 🔴 故障现象

```python
# 月度成本分析
monthly_stats = {
    "total_queries": 50000,
    "avg_context_tokens": 3000,
    "avg_answer_tokens": 500,
    "model": "gpt-4"
}

# GPT-4 定价
gpt4_pricing = {
    "input": 0.03 / 1000,   # $0.03 per 1K tokens
    "output": 0.06 / 1000   # $0.06 per 1K tokens
}

# 计算月度成本
input_cost = monthly_stats["total_queries"] * monthly_stats["avg_context_tokens"] * gpt4_pricing["input"]
output_cost = monthly_stats["total_queries"] * monthly_stats["avg_answer_tokens"] * gpt4_pricing["output"]

total_cost = input_cost + output_cost
print(f"月度总成本: ${total_cost:.2f}")  # 输出: $6,000

# ❌ 问题：成本过高，需要优化
```

### 🔧 成本优化方案

#### 策略 1: 混合模型策略

```python
class HybridModelRAG:
    """混合模型 RAG（根据难度选择模型）"""

    def __init__(self):
        # 便宜的模型（简单问题）
        self.cheap_llm = ChatOpenAI(
            model="gpt-3.5-turbo",  # $0.001/1K tokens
            temperature=0.0
        )

        # 昂贵的模型（复杂问题）
        self.expensive_llm = ChatOpenAI(
            model="gpt-4",  # $0.03/1K tokens
            temperature=0.0
        )

        self.complexity_classifier = self._load_classifier()

    def answer(self, query, contexts):
        """根据问题复杂度选择模型"""

        # 判断问题复杂度
        complexity = self._classify_complexity(query)

        if complexity == "simple":
            print("✅ 使用 GPT-3.5 (简单问题)")
            llm = self.cheap_llm
        else:
            print("⚠️  使用 GPT-4 (复杂问题)")
            llm = self.expensive_llm

        # 生成答案
        prompt = self._build_prompt(query, contexts)
        answer = llm.predict(prompt)

        return answer

    def _classify_complexity(self, query):
        """分类问题复杂度"""

        # 方法 1: 基于规则
        simple_patterns = [
            "什么是",
            "如何定义",
            "有哪些",
            "列举",
            "多少"
        ]

        for pattern in simple_patterns:
            if pattern in query:
                return "simple"

        # 方法 2: 使用小型分类器（可选）
        # complexity_score = self.complexity_classifier(query)
        # return "simple" if complexity_score < 0.5 else "complex"

        return "complex"  # 默认复杂

# 使用示例
hybrid_rag = HybridModelRAG()

# 简单问题 → GPT-3.5（节省 96% 成本）
answer1 = hybrid_rag.answer("GPT-4 是什么？", contexts)

# 复杂问题 → GPT-4
answer2 = hybrid_rag.answer("比较 GPT-4 和 Claude 的架构差异，并分析各自的优劣势", contexts)

# 成本节省:
# 假设 70% 是简单问题
# Before: 100% 使用 GPT-4 → $6,000/月
# After:  70% GPT-3.5 + 30% GPT-4 → $2,100/月（节省 65%）
```

#### 策略 2: 压缩上下文（减少 Input Tokens）

```python
# 成本分解:
# Input tokens (上下文): 3000 tokens × $0.03/1K = $0.09
# Output tokens (答案): 500 tokens × $0.06/1K = $0.03
# → Input 占总成本的 75%！

class ContextCompressorForCost:
    """专注成本优化的上下文压缩器"""

    def compress(self, contexts, target_ratio=0.5):
        """压缩到原长度的 50%"""

        # 使用轻量级总结模型（更便宜）
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

        compressed_contexts = []
        for ctx in contexts:
            summary = summarizer(
                ctx.page_content,
                max_length=len(ctx.page_content.split()) // 2,
                min_length=30,
                do_sample=False
            )
            compressed_contexts.append(summary[0]['summary_text'])

        return compressed_contexts

# 使用示例
compressor = ContextCompressorForCost()
compressed = compressor.compress(contexts, target_ratio=0.5)

# 成本节省:
# Before: 3000 tokens context × $0.03/1K = $0.09
# After:  1500 tokens context × $0.03/1K = $0.045（节省 50%）
```

#### 策略 3: 批量处理

```python
class BatchRAG:
    """批量处理 RAG（降低请求频率）"""

    def __init__(self, llm, batch_size=10):
        self.llm = llm
        self.batch_size = batch_size
        self.query_buffer = []

    def answer_batch(self, queries):
        """批量回答（一次 API 调用处理多个问题）"""

        # 构建批量 Prompt
        batch_prompt = """
请回答以下 {count} 个问题，每个问题单独回答：

{questions}

格式：
问题1的答案: ...
问题2的答案: ...
...
"""

        questions_text = "\n".join([
            f"问题{i+1}: {q}"
            for i, q in enumerate(queries)
        ])

        formatted_prompt = batch_prompt.format(
            count=len(queries),
            questions=questions_text
        )

        # 一次性调用 LLM
        batch_answer = self.llm.predict(formatted_prompt)

        # 解析批量答案
        answers = self._parse_batch_answer(batch_answer, len(queries))

        return answers

    def _parse_batch_answer(self, batch_answer, num_questions):
        """解析批量答案"""
        # 简化实现：按 "答案N:" 分割
        import re
        pattern = r'问题\d+的答案:\s*(.+?)(?=问题\d+的答案:|$)'
        matches = re.findall(pattern, batch_answer, re.DOTALL)
        return matches[:num_questions]

# 使用示例
batch_rag = BatchRAG(llm, batch_size=10)

# 批量处理 10 个问题
queries = [
    "GPT-4 是什么？",
    "GPT-4 的参数量？",
    # ... 8 more questions
]

answers = batch_rag.answer_batch(queries)

# 成本节省:
# Before: 10 次独立调用 × ($0.09 + $0.03) = $1.20
# After:  1 次批量调用 = $0.15（节省 87%）
```

#### 策略 4: 使用开源模型（自部署）

```python
# 完全消除 API 成本

from transformers import AutoModelForCausalLM, AutoTokenizer

class SelfHostedRAG:
    """自部署开源模型的 RAG"""

    def __init__(self, model_name="meta-llama/Llama-2-13b-chat-hf"):
        # 加载开源模型（需要 GPU）
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",  # 自动分配 GPU
            load_in_8bit=True   # 量化减少显存
        )

    def answer(self, query, contexts):
        """使用本地模型回答"""

        prompt = self._build_prompt(query, contexts)

        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=500,
            temperature=0.7,
            do_sample=True
        )

        answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return answer

# 成本对比:
"""
方案            | 月度成本 (50K queries) | 初期投入      | 性能
----------------|------------------------|---------------|--------
GPT-4 API       | $6,000                 | $0            | ⭐⭐⭐⭐⭐
GPT-3.5 API     | $250                   | $0            | ⭐⭐⭐⭐
Llama-2 (自部署)| $0 (仅电费约 $50)      | GPU 服务器 $2K| ⭐⭐⭐

推荐策略：
- 初创公司/低流量：GPT-3.5 API
- 中等流量（月 10K+ queries）：混合模型
- 高流量（月 100K+ queries）：自部署开源模型
"""
```

### ✅ 完整成本优化方案

```python
class CostOptimizedRAG:
    """全方位成本优化的 RAG"""

    def __init__(self, config):
        self.config = config

        # 1. 混合模型
        self.cheap_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0)
        self.expensive_llm = ChatOpenAI(model="gpt-4", temperature=0.0)

        # 2. 上下文压缩器
        self.compressor = ContextCompressorForCost()

        # 3. 缓存
        self.cache = {}

    def answer(self, query, use_compression=True, use_cache=True):
        """成本优化的回答流程"""

        # Step 1: 检查缓存（成本最低）
        if use_cache and query in self.cache:
            print("✅ 命中缓存（成本: $0）")
            return self.cache[query]

        # Step 2: 检索
        contexts = self._retrieve(query)

        # Step 3: 压缩上下文（减少 input tokens）
        if use_compression:
            contexts = self.compressor.compress(contexts, target_ratio=0.6)
            print("✅ 上下文已压缩（节省 40% input 成本）")

        # Step 4: 选择模型（根据复杂度）
        complexity = self._classify_complexity(query)
        llm = self.cheap_llm if complexity == "simple" else self.expensive_llm

        model_name = "GPT-3.5" if complexity == "simple" else "GPT-4"
        print(f"✅ 使用 {model_name}")

        # Step 5: 生成答案
        prompt = self._build_prompt(query, contexts)
        answer = llm.predict(prompt)

        # Step 6: 写入缓存
        if use_cache:
            self.cache[query] = answer

        return answer

# 使用示例
cost_optimized_rag = CostOptimizedRAG(config={})

answer = cost_optimized_rag.answer(
    "GPT-4 的参数量是多少？",
    use_compression=True,
    use_cache=True
)

# 成本对比（单次查询）:
"""
场景                      | 成本      | 说明
--------------------------|-----------|-----------------------------
原始 (GPT-4, 无优化)      | $0.12     | 3000 input + 500 output
压缩上下文 (GPT-4)        | $0.08     | 1800 input + 500 output
使用 GPT-3.5              | $0.004    | 3000 input + 500 output
压缩 + GPT-3.5            | $0.0024   | 1800 input + 500 output
命中缓存                  | $0        | 无 API 调用

月度成本 (50K queries, 70% simple, 20% cache hit):
- Before: $6,000
- After:  $480（节省 92%）
"""
```

---

# 第四部分：系统稳定性问题

## 案例 8: "API 限流导致服务不可用"

### 🔴 故障现象

```python
# 高并发场景
import time
from concurrent.futures import ThreadPoolExecutor

def process_query(query):
    return rag_system.answer(query)

queries = ["问题1", "问题2", ...] * 100  # 100 个查询

# 并发执行
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_query, queries))

# ❌ 错误: RateLimitError: Rate limit reached for requests
```

### 🔧 解决方案

#### 方案 1: 限流器 (Rate Limiter)

```python
import time
from threading import Lock

class RateLimiter:
    """速率限制器（令牌桶算法）"""

    def __init__(self, max_requests_per_minute=60):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = Lock()

    def acquire(self):
        """获取令牌（阻塞直到可用）"""
        with self.lock:
            now = time.time()

            # 移除 1 分钟前的请求记录
            self.requests = [req for req in self.requests if now - req < 60]

            # 检查是否达到限制
            if len(self.requests) >= self.max_requests:
                # 计算需要等待的时间
                oldest_request = self.requests[0]
                wait_time = 60 - (now - oldest_request) + 0.1
                print(f"⚠️  达到速率限制，等待 {wait_time:.1f}s")
                time.sleep(wait_time)

                # 递归重试
                return self.acquire()

            # 记录本次请求
            self.requests.append(now)

class RateLimitedRAG:
    """带限流的 RAG"""

    def __init__(self, rag_system, rpm_limit=60):
        self.rag_system = rag_system
        self.rate_limiter = RateLimiter(max_requests_per_minute=rpm_limit)

    def answer(self, query):
        """限流后的回答"""
        # 获取令牌（可能阻塞）
        self.rate_limiter.acquire()

        # 执行实际请求
        return self.rag_system.answer(query)

# 使用示例
rate_limited_rag = RateLimitedRAG(rag_system, rpm_limit=60)

# 即使并发 100 个请求，也不会触发限流错误
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(rate_limited_rag.answer, queries))
# 会自动限速，确保不超过 60 RPM
```

#### 方案 2: 指数退避重试

```python
import time
import random
from functools import wraps

def retry_with_exponential_backoff(
    max_retries=5,
    initial_delay=1,
    exponential_base=2,
    jitter=True
):
    """指数退避装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    error_message = str(e)

                    # 检测是否是限流错误
                    if "rate limit" in error_message.lower():
                        if attempt == max_retries - 1:
                            raise  # 最后一次尝试，抛出异常

                        # 添加随机抖动
                        if jitter:
                            delay = delay * exponential_base * (0.5 + random.random())
                        else:
                            delay = delay * exponential_base

                        print(f"⚠️  限流错误，{delay:.1f}s 后重试（第 {attempt+1}/{max_retries} 次）")
                        time.sleep(delay)
                    else:
                        # 非限流错误，直接抛出
                        raise

            raise Exception(f"达到最大重试次数 ({max_retries})")

        return wrapper
    return decorator

class RetryRAG:
    """带重试的 RAG"""

    def __init__(self, rag_system):
        self.rag_system = rag_system

    @retry_with_exponential_backoff(max_retries=5, initial_delay=1)
    def answer(self, query):
        """带自动重试的回答"""
        return self.rag_system.answer(query)

# 使用示例
retry_rag = RetryRAG(rag_system)

try:
    answer = retry_rag.answer(query)
except Exception as e:
    print(f"❌ 所有重试都失败: {e}")
```

#### 方案 3: 请求队列

```python
import queue
import threading
import time

class QueuedRAG:
    """队列化 RAG（控制并发）"""

    def __init__(self, rag_system, max_workers=3):
        self.rag_system = rag_system
        self.max_workers = max_workers

        # 请求队列
        self.request_queue = queue.Queue()
        self.result_queue = queue.Queue()

        # 启动工作线程
        self.workers = []
        for _ in range(max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)

    def _worker(self):
        """工作线程（从队列中取任务）"""
        while True:
            try:
                # 从队列获取任务
                task = self.request_queue.get(timeout=1)

                if task is None:  # 结束信号
                    break

                query, result_id = task

                # 处理任务
                try:
                    answer = self.rag_system.answer(query)
                    self.result_queue.put((result_id, answer, None))
                except Exception as e:
                    self.result_queue.put((result_id, None, e))

                # 标记任务完成
                self.request_queue.task_done()

            except queue.Empty:
                continue

    def answer(self, query, timeout=30):
        """异步提交任务"""
        result_id = id(query)

        # 提交到队列
        self.request_queue.put((query, result_id))

        # 等待结果
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                rid, answer, error = self.result_queue.get(timeout=0.1)

                if rid == result_id:
                    if error:
                        raise error
                    return answer

            except queue.Empty:
                continue

        raise TimeoutError(f"查询超时（{timeout}s）")

    def shutdown(self):
        """关闭队列"""
        for _ in self.workers:
            self.request_queue.put(None)

        for worker in self.workers:
            worker.join()

# 使用示例
queued_rag = QueuedRAG(rag_system, max_workers=3)

# 并发提交 100 个请求（但只有 3 个并发执行）
with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(queued_rag.answer, q) for q in queries]
    results = [f.result() for f in futures]

queued_rag.shutdown()
```

### ✅ 完整容错方案

```python
class RobustRAG:
    """健壮的 RAG 系统（集成限流、重试、降级）"""

    def __init__(self, rag_system, config):
        self.rag_system = rag_system
        self.config = config

        # 限流器
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=config.get('rpm_limit', 60)
        )

        # 缓存
        self.cache = {}

        # 降级响应
        self.fallback_enabled = config.get('enable_fallback', True)

    @retry_with_exponential_backoff(max_retries=3)
    def answer(self, query, timeout=30):
        """健壮的回答流程"""

        # Step 1: 检查缓存
        if query in self.cache:
            return self.cache[query]

        # Step 2: 限流
        self.rate_limiter.acquire()

        try:
            # Step 3: 执行查询（带超时）
            answer = self._answer_with_timeout(query, timeout)

            # Step 4: 写入缓存
            self.cache[query] = answer

            return answer

        except Exception as e:
            # Step 5: 降级策略
            if self.fallback_enabled:
                return self._fallback_answer(query, e)
            else:
                raise

    def _answer_with_timeout(self, query, timeout):
        """带超时的回答"""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("查询超时")

        # 设置超时
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            answer = self.rag_system.answer(query)
            signal.alarm(0)  # 取消超时
            return answer
        except:
            signal.alarm(0)
            raise

    def _fallback_answer(self, query, error):
        """降级响应"""
        print(f"⚠️  主系统故障，使用降级响应: {error}")

        # 降级策略 1: 返回简化答案
        return f"抱歉，系统暂时无法回答您的问题。请稍后重试。\n错误信息: {str(error)[:100]}"

        # 降级策略 2: 使用备用模型（可选）
        # return self.backup_llm.predict(f"简单回答：{query}")

# 使用示例
robust_rag = RobustRAG(
    rag_system=rag_system,
    config={
        "rpm_limit": 60,
        "enable_fallback": True
    }
)

# 即使在高并发、网络不稳定的情况下也能正常运行
answer = robust_rag.answer(query, timeout=30)
```

---

# 第五部分：调试工具与测试方法

## 工具 1: RAG 可视化调试器

```python
import json
from datetime import datetime

class RAGDebugger:
    """RAG 调试器（记录完整执行链路）"""

    def __init__(self, rag_system):
        self.rag_system = rag_system
        self.debug_logs = []

    def debug_answer(self, query):
        """调试模式回答（记录所有中间步骤）"""

        debug_session = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "steps": []
        }

        # Step 1: Embedding
        step1_start = time.time()
        query_embedding = self.rag_system.embedding_model.embed_query(query)
        debug_session["steps"].append({
            "name": "embedding",
            "duration": time.time() - step1_start,
            "output_preview": f"Vector dimension: {len(query_embedding)}"
        })

        # Step 2: Retrieval
        step2_start = time.time()
        contexts = self.rag_system.vectorstore.similarity_search_with_score(query, k=5)
        debug_session["steps"].append({
            "name": "retrieval",
            "duration": time.time() - step2_start,
            "output": [
                {
                    "content": doc.page_content[:100],
                    "score": float(score),
                    "metadata": doc.metadata
                }
                for doc, score in contexts
            ]
        })

        # Step 3: Prompt Building
        step3_start = time.time()
        prompt = self.rag_system.build_prompt(query, [doc for doc, _ in contexts])
        debug_session["steps"].append({
            "name": "prompt_building",
            "duration": time.time() - step3_start,
            "output": {
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:200]
            }
        })

        # Step 4: LLM Generation
        step4_start = time.time()
        answer = self.rag_system.llm.predict(prompt)
        debug_session["steps"].append({
            "name": "llm_generation",
            "duration": time.time() - step4_start,
            "output": answer
        })

        # 保存调试日志
        self.debug_logs.append(debug_session)

        # 生成可视化报告
        self._generate_debug_report(debug_session)

        return answer

    def _generate_debug_report(self, session):
        """生成可视化调试报告"""
        print("\n" + "="*70)
        print("🔍 RAG 调试报告")
        print("="*70)

        print(f"\n❓ 查询: {session['query']}")
        print(f"🕐 时间: {session['timestamp']}")

        print("\n📊 执行步骤:")
        for i, step in enumerate(session['steps'], 1):
            print(f"\n{i}. {step['name'].upper()}")
            print(f"   ⏱️  耗时: {step['duration']:.3f}s")

            if 'output' in step:
                if step['name'] == 'retrieval':
                    print(f"   📄 检索到 {len(step['output'])} 个文档:")
                    for j, doc in enumerate(step['output'][:3], 1):
                        print(f"      {j}. 相似度: {doc['score']:.3f}")
                        print(f"         内容: {doc['content']}...")

                elif step['name'] == 'llm_generation':
                    print(f"   💡 答案: {step['output'][:200]}...")

        print("\n" + "="*70)

    def export_debug_logs(self, filepath="rag_debug_logs.json"):
        """导出调试日志"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.debug_logs, f, ensure_ascii=False, indent=2)

        print(f"✅ 调试日志已导出到: {filepath}")

# 使用示例
debugger = RAGDebugger(rag_system)

# 调试模式回答
answer = debugger.debug_answer("GPT-4 的参数量是多少？")

# 导出日志
debugger.export_debug_logs()
```

## 工具 2: RAG 评估框架

```python
class RAGEvaluator:
    """RAG 评估框架"""

    def __init__(self, rag_system):
        self.rag_system = rag_system

    def evaluate(self, test_set):
        """
        评估 RAG 系统

        test_set: [{"query": "...", "expected_answer": "...", "ground_truth_docs": [...]}, ...]
        """
        metrics = {
            "retrieval": {
                "recall@3": [],
                "recall@5": [],
                "precision@3": [],
                "mrr": []  # Mean Reciprocal Rank
            },
            "generation": {
                "accuracy": [],
                "hallucination_rate": [],
                "citation_coverage": []
            },
            "latency": []
        }

        for test_case in test_set:
            # 评估检索
            retrieval_metrics = self._evaluate_retrieval(
                test_case["query"],
                test_case["ground_truth_docs"]
            )

            metrics["retrieval"]["recall@3"].append(retrieval_metrics["recall@3"])
            metrics["retrieval"]["recall@5"].append(retrieval_metrics["recall@5"])
            metrics["retrieval"]["mrr"].append(retrieval_metrics["mrr"])

            # 评估生成
            generation_metrics = self._evaluate_generation(
                test_case["query"],
                test_case["expected_answer"]
            )

            metrics["generation"]["accuracy"].append(generation_metrics["accuracy"])
            metrics["generation"]["hallucination_rate"].append(generation_metrics["hallucination"])

            # 评估延迟
            start = time.time()
            self.rag_system.answer(test_case["query"])
            metrics["latency"].append(time.time() - start)

        # 计算平均值
        final_metrics = {
            "retrieval_recall@3": np.mean(metrics["retrieval"]["recall@3"]),
            "retrieval_recall@5": np.mean(metrics["retrieval"]["recall@5"]),
            "generation_accuracy": np.mean(metrics["generation"]["accuracy"]),
            "hallucination_rate": np.mean(metrics["generation"]["hallucination_rate"]),
            "avg_latency": np.mean(metrics["latency"])
        }

        return final_metrics

    def _evaluate_retrieval(self, query, ground_truth_docs):
        """评估检索质量"""
        # 检索 Top-5
        retrieved = self.rag_system.retriever.retrieve(query, k=5)
        retrieved_ids = [doc.metadata.get('id') for doc in retrieved]

        # 计算 Recall@K
        recall_at_3 = len(set(retrieved_ids[:3]) & set(ground_truth_docs)) / len(ground_truth_docs)
        recall_at_5 = len(set(retrieved_ids[:5]) & set(ground_truth_docs)) / len(ground_truth_docs)

        # 计算 MRR
        mrr = 0.0
        for i, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in ground_truth_docs:
                mrr = 1 / i
                break

        return {
            "recall@3": recall_at_3,
            "recall@5": recall_at_5,
            "mrr": mrr
        }

    def _evaluate_generation(self, query, expected_answer):
        """评估生成质量"""
        # 生成答案
        generated_answer = self.rag_system.answer(query)

        # 计算相似度（作为准确率代理）
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')

        emb1 = model.encode(generated_answer)
        emb2 = model.encode(expected_answer)

        accuracy = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

        # 检测幻觉（简化）
        hallucination = self._detect_hallucination(generated_answer)

        return {
            "accuracy": accuracy,
            "hallucination": hallucination
        }

    def _detect_hallucination(self, answer):
        """简化的幻觉检测"""
        # 实际应使用 NLI 模型
        hallucination_keywords = ["据我所知", "一般来说", "可能", "大概"]
        return any(kw in answer for kw in hallucination_keywords)

# 使用示例
evaluator = RAGEvaluator(rag_system)

test_set = [
    {
        "query": "GPT-4 的参数量是多少？",
        "expected_answer": "GPT-4 的参数量未公开",
        "ground_truth_docs": ["doc_123", "doc_456"]
    },
    # ... 更多测试用例
]

results = evaluator.evaluate(test_set)

print("=== RAG 评估结果 ===")
for metric, value in results.items():
    print(f"{metric}: {value:.3f}")
```

---

## 总结：故障排查决策树

```
RAG 系统故障
│
├─ 答案质量差
│  ├─ 检索不到相关文档
│  │  ├─ 检查 1: 分块策略（chunk_size, overlap）
│  │  ├─ 检查 2: Embedding 模型质量
│  │  ├─ 检查 3: 距离度量（L2 vs Cosine）
│  │  ├─ 检查 4: Top-K 设置
│  │  └─ 解决方案: 混合检索 + 重排序
│  │
│  ├─ 检索到相关但实体不匹配
│  │  └─ 解决方案: 实体验证 + CrossEncoder 重排序
│  │
│  ├─ 答案包含幻觉
│  │  ├─ 检查 1: Prompt 设计
│  │  ├─ 检查 2: Temperature 参数
│  │  └─ 解决方案: 防幻觉 Prompt + 事后验证 + 引用约束
│  │
│  └─ 上下文被截断
│     └─ 解决方案: 上下文压缩 / Map-Reduce / Refine
│
├─ 性能问题
│  ├─ 延迟高
│  │  ├─ 检查 1: 各阶段耗时分析
│  │  ├─ 解决方案 1: 流式输出（降低感知延迟）
│  │  ├─ 解决方案 2: 并行化
│  │  ├─ 解决方案 3: 缓存
│  │  └─ 解决方案 4: 本地 Embedding
│  │
│  └─ 成本高
│     ├─ 解决方案 1: 混合模型策略
│     ├─ 解决方案 2: 压缩上下文
│     ├─ 解决方案 3: 批量处理
│     └─ 解决方案 4: 自部署开源模型
│
└─ 稳定性问题
   ├─ API 限流
   │  ├─ 解决方案 1: 速率限制器
   │  ├─ 解决方案 2: 指数退避重试
   │  └─ 解决方案 3: 请求队列
   │
   ├─ 超时
   │  └─ 解决方案: 超时控制 + 降级策略
   │
   └─ 并发错误
      └─ 解决方案: 线程安全 + 队列化
```

---

## 附录：快速诊断检查清单

### 检索质量问题
- [ ] 分块参数合理？（chunk_size: 500-1000, overlap: 10-20%）
- [ ] 距离度量正确？（文本推荐 cosine）
- [ ] Top-K 值合理？（推荐 3-5）
- [ ] 是否需要混合检索？（精确匹配场景）
- [ ] 是否需要重排序？（CrossEncoder）

### 生成质量问题
- [ ] Prompt 是否禁止幻觉？
- [ ] Temperature 是否过高？（事实性回答推荐 0-0.3）
- [ ] 是否强制引用？
- [ ] 是否有事后验证？
- [ ] 上下文是否超限？

### 性能问题
- [ ] 是否使用流式输出？
- [ ] Embedding 是否可本地化？
- [ ] 重排序候选数是否过多？
- [ ] 是否启用缓存？
- [ ] 模型选择是否合理？

### 成本问题
- [ ] 是否可使用更便宜的模型？
- [ ] 上下文是否可压缩？
- [ ] 是否启用缓存？
- [ ] 是否考虑自部署？

### 稳定性问题
- [ ] 是否有速率限制？
- [ ] 是否有重试机制？
- [ ] 是否有降级策略？
- [ ] 是否有超时控制？

---

**本指南涵盖 RAG 系统 90% 的常见故障及解决方案，适合作为生产环境的排查手册。**
