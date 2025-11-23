# RAG（检索增强生成）底层原理

## 核心架构

### Naive RAG（朴素 RAG）

```python
def naive_rag(query, documents, llm, embedding_model):
    """
    最基础的 RAG 流程

    1. 向量化文档
    2. 检索相关文档
    3. 拼接 prompt
    4. 生成答案
    """
    # Step 1: 离线处理 - 文档向量化
    doc_embeddings = []
    for doc in documents:
        emb = embedding_model.encode(doc)
        doc_embeddings.append(emb)

    # Step 2: 查询向量化
    query_emb = embedding_model.encode(query)

    # Step 3: 检索（余弦相似度）
    similarities = []
    for i, doc_emb in enumerate(doc_embeddings):
        sim = cosine_similarity(query_emb, doc_emb)
        similarities.append((i, sim))

    # 排序，取 top-k
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_k = 3
    retrieved_docs = [documents[i] for i, _ in similarities[:top_k]]

    # Step 4: 构造 prompt
    context = "\n\n".join(retrieved_docs)
    prompt = f"""根据以下上下文回答问题：

上下文：
{context}

问题：{query}

答案："""

    # Step 5: 生成
    answer = llm.generate(prompt)

    return answer
```

### Naive RAG 的问题

```python
# 问题 1：文档粒度不当
document = "这是一个非常长的文档..." * 1000  # 10,000 字
# 单个文档太大，包含无关信息
# 解决方案：Chunking

# 问题 2：检索不准确
query = "GPT-4 的参数量是多少？"
retrieved_docs = [
    "GPT-3 有 175B 参数...",  # 相关但不是答案
    "参数量决定了模型能力...",  # 相关但不是答案
    "GPT-4 是 OpenAI 的最新模型..."  # 相关但没有参数量
]
# 检索到相关但无用的文档
# 解决方案：Re-ranking、Hybrid Search

# 问题 3：上下文丢失
chunks = [chunk1, chunk2, chunk3]
# chunk2 包含关键信息，但缺少 chunk1 的背景
# 解决方案：Parent Document Retriever、Sliding Window

# 问题 4：幻觉
# LLM 仍然可能生成不在上下文中的内容
# 解决方案：Grounded Generation、Citation
```

---

## 文档处理策略

### 1. Chunking（分块）

#### Fixed-size Chunking

```python
def fixed_size_chunking(text, chunk_size=500, chunk_overlap=50):
    """
    固定大小分块

    chunk_size: 每块字符数
    chunk_overlap: 重叠字符数
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - chunk_overlap

    return chunks

# 优点：简单
# 缺点：可能切断句子，破坏语义
```

#### Recursive Chunking（LangChain 默认）

```python
def recursive_chunking(text, chunk_size=1000, chunk_overlap=200):
    """
    递归分块：按分隔符优先级切分

    分隔符优先级：\n\n > \n > 。 > ， > 空格
    """
    separators = ["\n\n", "\n", "。", "！", "？", "，", " ", ""]

    def split(text, separator_index):
        if separator_index >= len(separators):
            # 已经到最细粒度，强制切分
            return fixed_size_chunking(text, chunk_size, chunk_overlap)

        separator = separators[separator_index]
        splits = text.split(separator)

        chunks = []
        current_chunk = ""

        for split in splits:
            if len(current_chunk) + len(split) < chunk_size:
                current_chunk += split + separator
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = split + separator

        if current_chunk:
            chunks.append(current_chunk)

        # 检查是否有超大 chunk，递归切分
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size:
                final_chunks.extend(split(chunk, separator_index + 1))
            else:
                final_chunks.append(chunk)

        return final_chunks

    return split(text, 0)

# 优点：尽量保持语义完整
# 缺点：复杂度高
```

#### Semantic Chunking

```python
def semantic_chunking(text, embedding_model, similarity_threshold=0.5):
    """
    语义分块：按语义相似度切分

    算法：
    1. 按句子切分
    2. 计算相邻句子的 embedding
    3. 如果相似度 < threshold，则切分
    """
    import re

    # 切分句子
    sentences = re.split(r'[。！？\n]', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # 计算每个句子的 embedding
    embeddings = [embedding_model.encode(s) for s in sentences]

    # 合并相似的句子
    chunks = []
    current_chunk = [sentences[0]]
    current_emb = embeddings[0]

    for i in range(1, len(sentences)):
        sim = cosine_similarity(current_emb, embeddings[i])

        if sim >= similarity_threshold:
            # 相似，合并
            current_chunk.append(sentences[i])
            # 更新 embedding（平均）
            current_emb = (current_emb + embeddings[i]) / 2
        else:
            # 不相似，切分
            chunks.append('。'.join(current_chunk))
            current_chunk = [sentences[i]]
            current_emb = embeddings[i]

    chunks.append('。'.join(current_chunk))

    return chunks

# 优点：语义完整性最好
# 缺点：计算成本高（每个句子都要 embedding）
```

### 2. Metadata Enrichment（元数据增强）

```python
class Document:
    def __init__(self, content, metadata):
        self.page_content = content
        self.metadata = metadata

# 文档结构
doc = Document(
    content="GPT-4 是 OpenAI 的最新模型...",
    metadata={
        "source": "openai_blog.pdf",
        "page": 5,
        "section": "Model Architecture",
        "publish_date": "2023-03-14",
        "author": "OpenAI Team",
        "doc_type": "technical_report",
        "keywords": ["GPT-4", "LLM", "AI"]
    }
)

# 检索时可以利用 metadata 过滤
def retrieve_with_metadata_filter(query, vectorstore, filters):
    """
    filters = {
        "doc_type": "technical_report",
        "publish_date": {"$gte": "2023-01-01"}
    }
    """
    results = vectorstore.similarity_search(
        query,
        k=10,
        filter=filters
    )
    return results
```

### 3. Hypothetical Document Embeddings (HyDE)

```python
def hyde_retrieval(query, llm, embedding_model, vectorstore):
    """
    HyDE: 先让 LLM 生成假设的答案文档，然后检索

    问题：query 和 document 的语义空间可能不同
    解决：生成假设的文档，再检索
    """
    # Step 1: 生成假设文档
    hyde_prompt = f"""请根据以下问题，写一段可能包含答案的文档：

问题：{query}

文档："""

    hypothetical_doc = llm.generate(hyde_prompt)

    # Step 2: 使用假设文档检索
    hypo_emb = embedding_model.encode(hypothetical_doc)
    results = vectorstore.similarity_search_by_vector(hypo_emb, k=5)

    return results

# 示例：
# Query: "什么是量子纠缠？"
# Hypothetical Doc: "量子纠缠是量子力学中的一种现象，指两个粒子..."
# → 检索效果比直接用 query 更好
```

---

## 检索策略

### 1. Dense Retrieval（稠密检索）

```python
# 使用 Embedding 模型
def dense_retrieval(query, documents, embedding_model, k=3):
    # 向量化
    query_emb = embedding_model.encode(query)
    doc_embs = [embedding_model.encode(doc) for doc in documents]

    # 余弦相似度
    scores = [cosine_similarity(query_emb, doc_emb) for doc_emb in doc_embs]

    # Top-k
    top_k_indices = np.argsort(scores)[-k:][::-1]
    return [documents[i] for i in top_k_indices]

# 优点：理解语义
# 缺点：
# - 对关键词不敏感（"GPT-4" vs "GPT-3"）
# - 依赖 embedding 质量
```

### 2. Sparse Retrieval（稀疏检索）

```python
# BM25 算法
from rank_bm25 import BM25Okapi

def sparse_retrieval(query, documents, k=3):
    # Tokenize
    tokenized_docs = [doc.split() for doc in documents]
    tokenized_query = query.split()

    # BM25
    bm25 = BM25Okapi(tokenized_docs)
    scores = bm25.get_scores(tokenized_query)

    # Top-k
    top_k_indices = np.argsort(scores)[-k:][::-1]
    return [documents[i] for i in top_k_indices]

# BM25 公式：
# score(D, Q) = Σ IDF(qi) · (f(qi, D) · (k1 + 1)) / (f(qi, D) + k1 · (1 - b + b · |D| / avgdl))
#
# 其中：
# - f(qi, D): qi 在文档 D 中的词频
# - |D|: 文档 D 的长度
# - avgdl: 平均文档长度
# - IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5))
# - k1, b: 超参数（通常 k1=1.5, b=0.75）

# 优点：精确匹配关键词
# 缺点：不理解语义（"汽车" ≠ "车辆"）
```

### 3. Hybrid Retrieval（混合检索）

```python
def hybrid_retrieval(query, documents, embedding_model, alpha=0.5, k=3):
    """
    混合检索：Dense + Sparse

    alpha: Dense 的权重
    1 - alpha: Sparse 的权重
    """
    # Dense scores
    query_emb = embedding_model.encode(query)
    doc_embs = [embedding_model.encode(doc) for doc in documents]
    dense_scores = [cosine_similarity(query_emb, emb) for emb in doc_embs]

    # Sparse scores (BM25)
    tokenized_docs = [doc.split() for doc in documents]
    tokenized_query = query.split()
    bm25 = BM25Okapi(tokenized_docs)
    sparse_scores = bm25.get_scores(tokenized_query)

    # 归一化（0-1）
    dense_scores = (dense_scores - np.min(dense_scores)) / (np.max(dense_scores) - np.min(dense_scores))
    sparse_scores = (sparse_scores - np.min(sparse_scores)) / (np.max(sparse_scores) - np.min(sparse_scores))

    # 加权融合
    final_scores = alpha * dense_scores + (1 - alpha) * sparse_scores

    # Top-k
    top_k_indices = np.argsort(final_scores)[-k:][::-1]
    return [documents[i] for i in top_k_indices]

# 调优 alpha：
# - 语义问题（"如何减肥？"）→ alpha = 0.7（偏 Dense）
# - 关键词问题（"GPT-4 参数量"）→ alpha = 0.3（偏 Sparse）
```

### 4. Multi-Query Retrieval

```python
def multi_query_retrieval(query, llm, vectorstore, k=5):
    """
    生成多个相似问题，分别检索，合并结果

    目的：覆盖不同的表述方式
    """
    # Step 1: 生成多个 query 变体
    prompt = f"""将以下问题改写成 3 个不同的表述方式：

原问题：{query}

变体 1:
变体 2:
变体 3:"""

    response = llm.generate(prompt)
    queries = parse_queries(response)  # ["变体1", "变体2", "变体3"]
    queries.append(query)  # 加上原问题

    # Step 2: 对每个 query 检索
    all_docs = []
    for q in queries:
        docs = vectorstore.similarity_search(q, k=k)
        all_docs.extend(docs)

    # Step 3: 去重
    unique_docs = []
    seen = set()
    for doc in all_docs:
        if doc.page_content not in seen:
            unique_docs.append(doc)
            seen.add(doc.page_content)

    # Step 4: 重新排序（按出现次数）
    doc_counts = {}
    for doc in all_docs:
        doc_counts[doc.page_content] = doc_counts.get(doc.page_content, 0) + 1

    unique_docs.sort(key=lambda d: doc_counts[d.page_content], reverse=True)

    return unique_docs[:k]
```

### 5. Parent Document Retrieval

```python
class ParentDocumentRetriever:
    """
    检索小块，返回大块（保留上下文）

    结构：
    - 小块用于检索（精确匹配）
    - 大块用于生成（完整上下文）
    """
    def __init__(self, documents):
        self.parent_docs = documents  # 原始大文档

        # 切分成小块
        self.child_chunks = []
        self.child_to_parent = {}  # 映射关系

        for i, doc in enumerate(documents):
            chunks = self.split_to_small_chunks(doc)
            for chunk in chunks:
                self.child_chunks.append(chunk)
                self.child_to_parent[chunk] = i

        # 向量化小块
        self.vectorstore = create_vectorstore(self.child_chunks)

    def split_to_small_chunks(self, doc, size=200):
        # 切成 200 字符的小块
        return [doc[i:i+size] for i in range(0, len(doc), size)]

    def retrieve(self, query, k=3):
        # Step 1: 检索小块
        child_chunks = self.vectorstore.similarity_search(query, k=k*2)

        # Step 2: 获取对应的父文档
        parent_doc_ids = set()
        for chunk in child_chunks:
            parent_id = self.child_to_parent[chunk]
            parent_doc_ids.add(parent_id)

        # Step 3: 返回父文档（完整上下文）
        parent_docs = [self.parent_docs[i] for i in parent_doc_ids]

        return parent_docs[:k]

# 示例：
# 大文档："机器学习是...(1000字)...深度学习...(1000字)..."
# 小块："...深度学习..."（精确匹配 query）
# 返回：整个大文档（包含完整背景）
```

---

## Re-ranking（重排序）

### 1. Cross-Encoder Re-ranking

```python
from sentence_transformers import CrossEncoder

def rerank_with_cross_encoder(query, documents, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
    """
    Cross-Encoder: 联合编码 query 和 document

    Bi-Encoder (Dense Retrieval):
        query → emb_q
        doc   → emb_d
        score = cosine(emb_q, emb_d)

    Cross-Encoder (Re-ranking):
        [query, doc] → Transformer → score
        更准确但更慢
    """
    model = CrossEncoder(model_name)

    # 构造 query-doc 对
    pairs = [[query, doc] for doc in documents]

    # 计算分数
    scores = model.predict(pairs)

    # 排序
    ranked_indices = np.argsort(scores)[::-1]
    ranked_docs = [documents[i] for i in ranked_indices]

    return ranked_docs

# 两阶段检索：
# Stage 1: Bi-Encoder 快速检索 Top-100
# Stage 2: Cross-Encoder 精排 Top-10
```

### 2. LLM-based Re-ranking

```python
def rerank_with_llm(query, documents, llm):
    """
    使用 LLM 重排序

    让 LLM 判断每个文档的相关性
    """
    scored_docs = []

    for doc in documents:
        prompt = f"""评估以下文档与问题的相关性（0-10分）：

问题：{query}

文档：{doc}

相关性评分（0-10）："""

        response = llm.generate(prompt, max_tokens=5)
        score = int(response.strip())

        scored_docs.append((doc, score))

    # 排序
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in scored_docs]

# 问题：成本高、慢
# 优化：批量评分
```

### 3. Maximal Marginal Relevance (MMR)

```python
def mmr_rerank(query_emb, doc_embs, documents, lambda_param=0.5, k=3):
    """
    MMR: 平衡相关性和多样性

    score(d) = λ · sim(q, d) - (1-λ) · max sim(d, selected_d)

    λ = 1: 只考虑相关性
    λ = 0: 只考虑多样性
    """
    selected_docs = []
    selected_embs = []
    remaining_indices = list(range(len(documents)))

    for _ in range(k):
        max_score = -np.inf
        max_idx = None

        for i in remaining_indices:
            # 与 query 的相似度
            relevance = cosine_similarity(query_emb, doc_embs[i])

            # 与已选文档的最大相似度
            if selected_embs:
                diversity = max([cosine_similarity(doc_embs[i], sel_emb)
                                for sel_emb in selected_embs])
            else:
                diversity = 0

            # MMR 分数
            score = lambda_param * relevance - (1 - lambda_param) * diversity

            if score > max_score:
                max_score = score
                max_idx = i

        # 选择最高分的文档
        selected_docs.append(documents[max_idx])
        selected_embs.append(doc_embs[max_idx])
        remaining_indices.remove(max_idx)

    return selected_docs

# 用途：避免返回重复的文档
```

---

## Prompt 构造策略

### 1. Context Stuffing（直接拼接）

```python
def context_stuffing(query, retrieved_docs, max_tokens=4000):
    """
    最简单的方法：直接拼接所有文档
    """
    context = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])

    prompt = f"""根据以下上下文回答问题：

{context}

问题：{query}

答案："""

    # 检查是否超过上下文窗口
    if count_tokens(prompt) > max_tokens:
        # 截断
        context = truncate_to_tokens(context, max_tokens - 200)
        prompt = f"根据以下上下文回答问题：\n\n{context}\n\n问题：{query}\n\n答案："

    return prompt
```

### 2. Map-Reduce

```python
def map_reduce_rag(query, retrieved_docs, llm):
    """
    Map-Reduce: 先分别总结，再合并

    适用于：检索到的文档太多，无法一次性放入上下文
    """
    # Map: 对每个文档单独提问
    summaries = []
    for doc in retrieved_docs:
        map_prompt = f"""根据以下文档，回答问题：

文档：{doc.page_content}

问题：{query}

答案："""
        summary = llm.generate(map_prompt)
        summaries.append(summary)

    # Reduce: 合并所有答案
    combined_summaries = "\n\n".join(summaries)
    reduce_prompt = f"""以下是针对同一问题的多个答案，请综合成一个最终答案：

{combined_summaries}

最终答案："""

    final_answer = llm.generate(reduce_prompt)

    return final_answer
```

### 3. Refine

```python
def refine_rag(query, retrieved_docs, llm):
    """
    Refine: 逐步优化答案

    流程：
    1. 用第一个文档生成初始答案
    2. 用第二个文档优化答案
    3. ...
    """
    # 初始答案
    initial_prompt = f"""根据以下文档回答问题：

文档：{retrieved_docs[0].page_content}

问题：{query}

答案："""

    answer = llm.generate(initial_prompt)

    # 逐步优化
    for doc in retrieved_docs[1:]:
        refine_prompt = f"""已有答案：{answer}

新文档：{doc.page_content}

请根据新文档优化答案（如果新文档包含更多信息）：

优化后的答案："""

        answer = llm.generate(refine_prompt)

    return answer
```

### 4. Conversational RAG（对话式 RAG）

```python
class ConversationalRAG:
    def __init__(self, vectorstore, llm):
        self.vectorstore = vectorstore
        self.llm = llm
        self.chat_history = []

    def query(self, user_question):
        # Step 1: 重写问题（考虑历史）
        if self.chat_history:
            rewrite_prompt = f"""对话历史：
{self.format_history()}

最新问题：{user_question}

请将最新问题改写成独立的问题（包含必要的上下文）：

独立问题："""

            standalone_question = self.llm.generate(rewrite_prompt)
        else:
            standalone_question = user_question

        # Step 2: 检索
        docs = self.vectorstore.similarity_search(standalone_question, k=3)

        # Step 3: 生成答案
        context = "\n\n".join([doc.page_content for doc in docs])
        qa_prompt = f"""对话历史：
{self.format_history()}

上下文：
{context}

问题：{user_question}

答案："""

        answer = self.llm.generate(qa_prompt)

        # Step 4: 更新历史
        self.chat_history.append({"question": user_question, "answer": answer})

        return answer

    def format_history(self):
        return "\n".join([f"Q: {item['question']}\nA: {item['answer']}"
                         for item in self.chat_history])

# 示例对话：
# User: "什么是 RAG？"
# Bot: "RAG 是检索增强生成..."

# User: "它有什么优点？"（指代不清）
# Rewrite: "RAG 有什么优点？"（独立问题）
# Bot: "RAG 的优点包括..."
```

---

## 高级技术

### 1. Self-RAG（自我反思 RAG）

```python
def self_rag(query, vectorstore, llm):
    """
    Self-RAG: 让模型决定是否需要检索

    流程：
    1. 判断问题是否需要外部知识
    2. 如果需要，则检索
    3. 生成答案
    4. 反思答案质量
    5. 如果质量不高，重新检索
    """
    # Step 1: 判断是否需要检索
    judge_prompt = f"""判断以下问题是否需要外部知识（回答"是"或"否"）：

问题：{query}

需要外部知识吗？"""

    need_retrieval = llm.generate(judge_prompt, max_tokens=5).strip()

    if need_retrieval.lower() == "否":
        # 直接生成
        answer = llm.generate(f"问题：{query}\n答案：")
        return answer

    # Step 2: 检索
    docs = vectorstore.similarity_search(query, k=5)

    # Step 3: 生成答案
    context = "\n\n".join([doc.page_content for doc in docs])
    answer_prompt = f"""上下文：{context}\n\n问题：{query}\n\n答案："""
    answer = llm.generate(answer_prompt)

    # Step 4: 反思
    reflect_prompt = f"""评估以下答案的质量（0-10分）：

问题：{query}
答案：{answer}

评分（0-10）："""

    score = int(llm.generate(reflect_prompt, max_tokens=5).strip())

    if score < 7:
        # 重新检索（使用不同的 query）
        rewrite_query = llm.generate(f"将以下问题改写：{query}\n改写后：")
        docs = vectorstore.similarity_search(rewrite_query, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
        answer = llm.generate(f"上下文：{context}\n\n问题：{query}\n\n答案：")

    return answer
```

### 2. RAPTOR（递归摘要 RAG）

```python
class RAPTORRetriever:
    """
    RAPTOR: 构建文档的层次化摘要树

    层级：
    Level 0: 原始文档块
    Level 1: 块的摘要
    Level 2: 摘要的摘要
    ...
    """
    def __init__(self, documents, llm, embedding_model):
        self.llm = llm
        self.embedding_model = embedding_model
        self.tree = self.build_tree(documents)

    def build_tree(self, documents, cluster_size=5):
        tree = {}
        tree[0] = documents  # Level 0: 原始文档

        level = 0
        while len(tree[level]) > 1:
            # 聚类
            clusters = self.cluster_documents(tree[level], cluster_size)

            # 对每个簇生成摘要
            summaries = []
            for cluster in clusters:
                cluster_text = "\n\n".join([doc.page_content for doc in cluster])
                summary_prompt = f"总结以下文档：\n\n{cluster_text}\n\n摘要："
                summary = self.llm.generate(summary_prompt)
                summaries.append(Document(page_content=summary, metadata={}))

            tree[level + 1] = summaries
            level += 1

        return tree

    def cluster_documents(self, documents, cluster_size):
        # 使用 embedding 进行聚类
        embs = [self.embedding_model.encode(doc.page_content) for doc in documents]

        from sklearn.cluster import KMeans
        num_clusters = len(documents) // cluster_size
        kmeans = KMeans(n_clusters=num_clusters)
        labels = kmeans.fit_predict(embs)

        clusters = [[] for _ in range(num_clusters)]
        for i, label in enumerate(labels):
            clusters[label].append(documents[i])

        return clusters

    def retrieve(self, query, k=5):
        # 从所有层级检索
        all_docs = []
        for level, docs in self.tree.items():
            level_docs = dense_retrieval(query, docs, self.embedding_model, k=2)
            all_docs.extend(level_docs)

        # 去重 + 重排
        return rerank(query, all_docs, k=k)

# 优点：可以检索不同粒度的信息
# 缺点：构建树的成本高
```

### 3. Corrective RAG（纠正式 RAG）

```python
def corrective_rag(query, vectorstore, llm, web_search_api):
    """
    CRAG: 如果检索质量不高，使用 Web 搜索补充

    流程：
    1. 检索
    2. 评估检索质量
    3. 如果质量低，使用 Web 搜索
    4. 生成答案
    """
    # Step 1: 向量检索
    docs = vectorstore.similarity_search(query, k=5)

    # Step 2: 评估检索质量
    relevance_scores = []
    for doc in docs:
        eval_prompt = f"""评估文档与问题的相关性（0-10）：

问题：{query}
文档：{doc.page_content[:200]}...

相关性（0-10）："""

        score = int(llm.generate(eval_prompt, max_tokens=5).strip())
        relevance_scores.append(score)

    avg_score = np.mean(relevance_scores)

    # Step 3: 如果质量低，使用 Web 搜索
    if avg_score < 6:
        web_results = web_search_api.search(query, num_results=3)
        docs.extend(web_results)

    # Step 4: 生成答案
    context = "\n\n".join([doc.page_content for doc in docs])
    answer = llm.generate(f"上下文：{context}\n\n问题：{query}\n\n答案：")

    return answer
```

---

## 评估指标

### 1. Retrieval Metrics

```python
def retrieval_recall_at_k(retrieved_docs, ground_truth_docs, k):
    """
    Recall@K: 前 K 个结果中包含正确答案的比例

    retrieved_docs: 检索到的文档
    ground_truth_docs: 真实相关的文档
    """
    retrieved_set = set(retrieved_docs[:k])
    ground_truth_set = set(ground_truth_docs)

    recall = len(retrieved_set & ground_truth_set) / len(ground_truth_set)
    return recall

def retrieval_precision_at_k(retrieved_docs, ground_truth_docs, k):
    """
    Precision@K: 前 K 个结果中正确答案的比例
    """
    retrieved_set = set(retrieved_docs[:k])
    ground_truth_set = set(ground_truth_docs)

    precision = len(retrieved_set & ground_truth_set) / k
    return precision

def mean_reciprocal_rank(retrieved_docs, ground_truth_docs):
    """
    MRR: 第一个正确答案的位置的倒数的平均值

    例如：
    - 第1个位置找到答案：MRR = 1/1 = 1.0
    - 第3个位置找到答案：MRR = 1/3 = 0.33
    """
    for i, doc in enumerate(retrieved_docs):
        if doc in ground_truth_docs:
            return 1 / (i + 1)
    return 0

def ndcg_at_k(retrieved_docs, ground_truth_relevance, k):
    """
    NDCG@K: 归一化折损累计增益

    考虑了排序的质量（越靠前的文档权重越高）

    DCG = Σ (2^relevance - 1) / log2(position + 1)
    NDCG = DCG / IDCG（理想情况下的 DCG）
    """
    dcg = 0
    for i, doc in enumerate(retrieved_docs[:k]):
        relevance = ground_truth_relevance.get(doc, 0)
        dcg += (2**relevance - 1) / np.log2(i + 2)

    # 计算理想 DCG
    ideal_relevance = sorted(ground_truth_relevance.values(), reverse=True)
    idcg = 0
    for i, rel in enumerate(ideal_relevance[:k]):
        idcg += (2**rel - 1) / np.log2(i + 2)

    return dcg / idcg if idcg > 0 else 0
```

### 2. Generation Metrics

```python
# Faithfulness（忠实度）
def faithfulness_score(answer, context, llm):
    """
    答案是否基于上下文（没有幻觉）

    方法：让 LLM 判断答案中的每个陈述是否在上下文中
    """
    prompt = f"""上下文：{context}

答案：{answer}

答案中的所有陈述都基于上下文吗？（回答"是"或"否"）

判断："""

    result = llm.generate(prompt, max_tokens=5).strip()
    return 1.0 if result.lower() == "是" else 0.0

# Answer Relevance（答案相关性）
def answer_relevance(question, answer, embedding_model):
    """
    答案是否回答了问题

    方法：计算 question 和 answer 的语义相似度
    """
    q_emb = embedding_model.encode(question)
    a_emb = embedding_model.encode(answer)
    return cosine_similarity(q_emb, a_emb)

# Context Relevance（上下文相关性）
def context_relevance(question, retrieved_docs, embedding_model):
    """
    检索到的文档是否与问题相关

    方法：计算 question 和每个 doc 的相似度
    """
    q_emb = embedding_model.encode(question)
    scores = []
    for doc in retrieved_docs:
        doc_emb = embedding_model.encode(doc.page_content)
        scores.append(cosine_similarity(q_emb, doc_emb))
    return np.mean(scores)
```

---

## 生产环境优化

### 1. Caching（缓存）

```python
import hashlib
import json

class RAGCache:
    def __init__(self):
        self.cache = {}  # {query_hash: (retrieved_docs, answer)}

    def get_hash(self, query):
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query):
        query_hash = self.get_hash(query)
        return self.cache.get(query_hash)

    def set(self, query, retrieved_docs, answer):
        query_hash = self.get_hash(query)
        self.cache[query_hash] = (retrieved_docs, answer)

# 使用
cache = RAGCache()

def cached_rag(query, vectorstore, llm):
    # 检查缓存
    cached_result = cache.get(query)
    if cached_result:
        return cached_result[1]  # 返回 answer

    # 执行 RAG
    docs = vectorstore.similarity_search(query)
    answer = generate_answer(query, docs, llm)

    # 存入缓存
    cache.set(query, docs, answer)

    return answer
```

### 2. Streaming（流式输出）

```python
def streaming_rag(query, vectorstore, llm):
    """
    流式生成答案

    好处：用户体验更好（边生成边显示）
    """
    # 检索（不流式）
    docs = vectorstore.similarity_search(query)
    context = "\n\n".join([doc.page_content for doc in docs])

    # 构造 prompt
    prompt = f"上下文：{context}\n\n问题：{query}\n\n答案："

    # 流式生成
    for chunk in llm.stream(prompt):
        yield chunk  # 逐块返回

# FastAPI 示例
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/rag")
async def rag_endpoint(query: str):
    return StreamingResponse(
        streaming_rag(query, vectorstore, llm),
        media_type="text/plain"
    )
```

### 3. Async Processing（异步处理）

```python
import asyncio

async def async_rag(query, vectorstore, llm):
    """
    异步 RAG：并行处理多个步骤
    """
    # 并行：检索 + 生成 query 变体
    retrieval_task = asyncio.create_task(
        vectorstore.asimilarity_search(query)
    )

    query_variations_task = asyncio.create_task(
        llm.agenerate("改写问题：" + query)
    )

    # 等待两个任务完成
    docs, query_variations = await asyncio.gather(
        retrieval_task,
        query_variations_task
    )

    # 生成答案
    answer = await llm.agenerate(f"上下文：{docs}\n问题：{query}\n答案：")

    return answer
```

---

## 完整代码示例

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader

class ProductionRAG:
    def __init__(self, pdf_path):
        # 加载文档
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # 切分
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)

        # 创建向量数据库
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )

        # LLM
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)

        # Cache
        self.cache = {}

    def retrieve(self, query, k=5):
        # Hybrid retrieval
        dense_docs = self.vectorstore.similarity_search(query, k=k*2)

        # Re-rank with MMR
        from langchain.vectorstores.utils import maximal_marginal_relevance
        query_emb = self.embeddings.embed_query(query)
        doc_embs = [self.embeddings.embed_query(doc.page_content) for doc in dense_docs]

        selected_indices = maximal_marginal_relevance(
            query_emb, doc_embs, lambda_mult=0.5, k=k
        )

        return [dense_docs[i] for i in selected_indices]

    def generate(self, query, docs):
        context = "\n\n---\n\n".join([doc.page_content for doc in docs])

        prompt = f"""根据以下上下文回答问题。如果上下文中没有答案，请回答"我不知道"。

上下文：
{context}

问题：{query}

答案："""

        response = self.llm.predict(prompt)
        return response

    def query(self, query):
        # Check cache
        if query in self.cache:
            return self.cache[query]

        # Retrieve
        docs = self.retrieve(query)

        # Generate
        answer = self.generate(query, docs)

        # Cache
        self.cache[query] = answer

        return answer

# 使用
rag = ProductionRAG("document.pdf")
answer = rag.query("什么是 RAG？")
print(answer)
```
