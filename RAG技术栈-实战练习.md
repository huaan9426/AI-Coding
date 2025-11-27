# RAG 技术栈 - 实战练习手册

> 基于深度技术笔记的三个核心练习
> 难度递进：基础 → 进阶 → 综合应用

---

## 练习 1: 手写 Embedding 查找表 (基础)

### 🎯 学习目标
- 理解 Embedding 的本质是查找表
- 掌握 BPE 分词流程
- 实现词向量的加载和查询

### 📚 相关笔记
- `Embeddings底层原理.md` - BPE 分词算法章节
- `Embeddings底层原理.md` - Word2Vec 查找表章节

### 📝 任务描述
实现一个简化的 Embedding 系统：
1. 加载预训练的词向量（使用小型词表）
2. 实现 BPE 分词器
3. 将句子转换为向量序列

### 💻 代码框架

```python
import numpy as np
from typing import List, Dict, Tuple

class SimpleEmbedding:
    """简化的 Embedding 查找表实现"""

    def __init__(self, vocab_size: int = 5000, embedding_dim: int = 128):
        """
        初始化 Embedding 层

        参数:
            vocab_size: 词表大小（BPE token 数量）
            embedding_dim: 向量维度
        """
        # TODO: 初始化随机权重矩阵 (vocab_size × embedding_dim)
        # 提示：使用 np.random.randn 并乘以 0.01 进行小范围初始化
        self.embedding_matrix = None  # 你的代码

        # 模拟 BPE 词表（实际应从文件加载）
        self.token_to_id = {
            "<PAD>": 0,
            "<UNK>": 1,
            "hello": 2,
            "world": 3,
            "##ing": 4,  # BPE 子词
            "embed": 5,
            "##ding": 6,
            # ... 更多 token
        }
        self.id_to_token = {v: k for k, v in self.token_to_id.items()}

    def tokenize(self, text: str) -> List[str]:
        """
        简化的 BPE 分词

        参数:
            text: 输入文本

        返回:
            token 列表
        """
        # TODO: 实现简化的 BPE 分词逻辑
        # 提示：
        # 1. 将文本转为小写并分割单词
        # 2. 检查词表中是否存在完整单词
        # 3. 如果不存在，尝试分解为子词（如 "embedding" → ["embed", "##ding"]）
        # 4. 未知词使用 <UNK>

        tokens = []
        # 你的代码
        return tokens

    def encode(self, tokens: List[str]) -> List[int]:
        """
        将 token 转换为 ID

        参数:
            tokens: token 列表

        返回:
            ID 列表
        """
        # TODO: 将每个 token 转换为对应的 ID
        # 提示：使用 token_to_id 字典，未知词映射到 <UNK> (ID=1)
        return [self.token_to_id.get(token, 1) for token in tokens]  # 参考答案

    def lookup(self, token_ids: List[int]) -> np.ndarray:
        """
        查找向量

        参数:
            token_ids: token ID 列表

        返回:
            向量矩阵 (num_tokens × embedding_dim)
        """
        # TODO: 从 embedding_matrix 中查找对应向量
        # 提示：使用 NumPy 的索引功能 embedding_matrix[token_ids]
        return None  # 你的代码

    def forward(self, text: str) -> np.ndarray:
        """
        完整的前向传播：文本 → token → ID → 向量

        参数:
            text: 输入文本

        返回:
            向量序列
        """
        # TODO: 串联上述所有步骤
        # 1. 分词
        # 2. 编码
        # 3. 查找向量
        return None  # 你的代码


# 测试代码
if __name__ == "__main__":
    # 初始化
    embed = SimpleEmbedding(vocab_size=5000, embedding_dim=128)

    # 测试用例
    text = "hello world"

    # 分词
    tokens = embed.tokenize(text)
    print(f"分词结果: {tokens}")  # 预期: ['hello', 'world']

    # 编码
    ids = embed.encode(tokens)
    print(f"ID 序列: {ids}")  # 预期: [2, 3]

    # 查找向量
    vectors = embed.lookup(ids)
    print(f"向量形状: {vectors.shape}")  # 预期: (2, 128)

    # 完整流程
    output = embed.forward(text)
    print(f"最终输出形状: {output.shape}")
```

### ✅ 预期输出
```
分词结果: ['hello', 'world']
ID 序列: [2, 3]
向量形状: (2, 128)
最终输出形状: (2, 128)
```

### 🔍 检查点
- [ ] `embedding_matrix` 形状是否正确？(5000 × 128)
- [ ] 分词逻辑能否处理未知词？
- [ ] 查找的向量是否从正确的行中提取？

---

## 练习 2: 手写余弦相似度搜索 (进阶)

### 🎯 学习目标
- 理解向量相似度计算的数学本质
- 实现暴力搜索和索引优化
- 对比 L2 距离和余弦相似度的差异

### 📚 相关笔记
- `向量数据库底层原理.md` - 相似度度量章节
- `向量数据库底层原理.md` - HNSW 索引章节

### 📝 任务描述
实现一个简化的向量搜索引擎：
1. 暴力搜索（Brute Force）
2. 归一化优化
3. Top-K 检索

### 💻 代码框架

```python
import numpy as np
from typing import List, Tuple
import heapq

class VectorSearch:
    """简化的向量搜索引擎"""

    def __init__(self, vectors: np.ndarray, metadata: List[str] = None):
        """
        初始化搜索引擎

        参数:
            vectors: 向量数据库 (num_docs × dim)
            metadata: 文档元数据（如文件名、内容片段）
        """
        self.vectors = vectors  # 原始向量
        self.normalized_vectors = None  # 归一化后的向量
        self.metadata = metadata or [f"Doc_{i}" for i in range(len(vectors))]

        # TODO: 对向量进行归一化（L2 范数）
        # 提示：v_norm = v / ||v||_2
        # 使用 np.linalg.norm(vectors, axis=1, keepdims=True)
        self.normalize_vectors()

    def normalize_vectors(self):
        """归一化向量（用于余弦相似度优化）"""
        # TODO: 计算 L2 范数并归一化
        # 提示：
        # 1. 计算每个向量的 L2 范数: np.linalg.norm(self.vectors, axis=1, keepdims=True)
        # 2. 除以范数: self.vectors / norms
        # 3. 处理零向量（避免除以零）
        pass  # 你的代码

    def cosine_similarity(self, query: np.ndarray, doc: np.ndarray) -> float:
        """
        计算余弦相似度（原始方法）

        参数:
            query: 查询向量 (dim,)
            doc: 文档向量 (dim,)

        返回:
            相似度分数 [-1, 1]

        公式:
            cos(θ) = (A · B) / (||A|| × ||B||)
        """
        # TODO: 实现余弦相似度公式
        # 提示：
        # 1. 点积: np.dot(query, doc)
        # 2. 范数: np.linalg.norm(query) * np.linalg.norm(doc)
        # 3. 相除得到余弦值
        return 0.0  # 你的代码

    def cosine_similarity_optimized(self, query: np.ndarray) -> np.ndarray:
        """
        优化的批量余弦相似度计算

        参数:
            query: 查询向量 (dim,)

        返回:
            与所有文档的相似度 (num_docs,)

        原理:
            归一化后，cos(θ) = A · B（直接点积）
        """
        # TODO: 实现优化版本
        # 提示：
        # 1. 归一化查询向量
        # 2. 使用矩阵乘法 np.dot(normalized_vectors, query_norm)
        # 3. 返回所有相似度分数
        return None  # 你的代码

    def l2_distance(self, query: np.ndarray, doc: np.ndarray) -> float:
        """
        计算 L2 距离（欧几里得距离）

        参数:
            query: 查询向量
            doc: 文档向量

        返回:
            距离值（越小越相似）

        公式:
            d = √(Σ(qi - di)²)
        """
        # TODO: 实现 L2 距离公式
        # 提示：np.linalg.norm(query - doc)
        return 0.0  # 你的代码

    def search(
        self,
        query: np.ndarray,
        k: int = 3,
        metric: str = "cosine"
    ) -> List[Tuple[int, float, str]]:
        """
        Top-K 检索

        参数:
            query: 查询向量 (dim,)
            k: 返回前 K 个结果
            metric: 距离度量 ("cosine" 或 "l2")

        返回:
            [(doc_id, score, metadata), ...] 列表
        """
        scores = []

        if metric == "cosine":
            # TODO: 使用优化的余弦相似度计算
            # 提示：调用 cosine_similarity_optimized
            all_scores = None  # 你的代码

            # TODO: 使用 np.argsort 找到 Top-K
            # 提示：argsort 默认升序，余弦相似度需要降序（[::-1]）
            top_k_indices = None  # 你的代码

        elif metric == "l2":
            # TODO: 计算所有 L2 距离
            all_distances = [
                self.l2_distance(query, doc)
                for doc in self.vectors
            ]

            # TODO: 使用 heapq.nsmallest 找到最小的 K 个
            # 提示：heapq.nsmallest(k, range(len(all_distances)), key=lambda i: all_distances[i])
            top_k_indices = None  # 你的代码

        else:
            raise ValueError(f"不支持的度量: {metric}")

        # 构建结果
        results = [
            (idx, all_scores[idx], self.metadata[idx])
            for idx in top_k_indices
        ]

        return results


# 测试代码
if __name__ == "__main__":
    # 创建模拟数据库（5 个文档，128 维向量）
    np.random.seed(42)
    num_docs = 5
    dim = 128

    vectors = np.random.randn(num_docs, dim)
    metadata = [
        "文档1: RAG 架构介绍",
        "文档2: Embedding 原理",
        "文档3: 向量数据库对比",
        "文档4: LLM 训练技巧",
        "文档5: 数据增强方法"
    ]

    # 初始化搜索引擎
    search_engine = VectorSearch(vectors, metadata)

    # 创建查询向量（与文档2 最相似）
    query = vectors[1] + np.random.randn(dim) * 0.1  # 添加噪声

    # 测试余弦相似度
    print("=== 余弦相似度搜索 ===")
    results_cosine = search_engine.search(query, k=3, metric="cosine")
    for rank, (doc_id, score, meta) in enumerate(results_cosine, 1):
        print(f"{rank}. {meta} (相似度: {score:.4f})")

    # 测试 L2 距离
    print("\n=== L2 距离搜索 ===")
    results_l2 = search_engine.search(query, k=3, metric="l2")
    for rank, (doc_id, dist, meta) in enumerate(results_l2, 1):
        print(f"{rank}. {meta} (距离: {dist:.4f})")

    # 性能对比
    import time

    print("\n=== 性能对比 ===")
    # 暴力法
    start = time.time()
    for i in range(100):
        _ = [search_engine.cosine_similarity(query, doc) for doc in vectors]
    t_brute = time.time() - start
    print(f"暴力法 (100次): {t_brute:.4f}s")

    # 优化法
    start = time.time()
    for i in range(100):
        _ = search_engine.cosine_similarity_optimized(query)
    t_opt = time.time() - start
    print(f"优化法 (100次): {t_opt:.4f}s")
    print(f"加速比: {t_brute / t_opt:.2f}x")
```

### ✅ 预期输出
```
=== 余弦相似度搜索 ===
1. 文档2: Embedding 原理 (相似度: 0.9856)
2. 文档3: 向量数据库对比 (相似度: 0.2341)
3. 文档1: RAG 架构介绍 (相似度: 0.1782)

=== L2 距离搜索 ===
1. 文档2: Embedding 原理 (距离: 1.2345)
2. 文档3: 向量数据库对比 (距离: 15.6782)
3. 文档1: RAG 架构介绍 (距离: 16.2341)

=== 性能对比 ===
暴力法 (100次): 0.0234s
优化法 (100次): 0.0012s
加速比: 19.50x
```

### 🔍 检查点
- [ ] 归一化后向量的 L2 范数是否都为 1？
- [ ] 余弦相似度是否在 [-1, 1] 范围内？
- [ ] Top-K 结果是否正确排序？
- [ ] 优化版本的加速比是否 > 10x？

---

## 练习 3: 模拟 RAG 完整流程 (综合)

### 🎯 学习目标
- 串联 Embedding、检索、生成三个核心组件
- 理解 RAG 的数据流转
- 实现 Prompt 工程技巧

### 📚 相关笔记
- `RAG底层原理.md` - 完整架构章节
- `LLM底层原理.md` - Prompt 工程章节

### 📝 任务描述
实现一个端到端的 RAG 系统：
1. 文档预处理和向量化
2. 检索相关文档
3. 构建增强 Prompt
4. 模拟 LLM 生成（简化）

### 💻 代码框架

```python
import numpy as np
from typing import List, Dict, Tuple

class SimpleRAG:
    """简化的 RAG 系统实现"""

    def __init__(self, embedding_dim: int = 128):
        """
        初始化 RAG 系统

        参数:
            embedding_dim: 向量维度
        """
        self.embedding_dim = embedding_dim
        self.documents = []  # 原始文档
        self.doc_embeddings = None  # 文档向量
        self.chunk_metadata = []  # 文档块元数据

    def chunk_documents(
        self,
        documents: List[str],
        chunk_size: int = 200,
        chunk_overlap: int = 50
    ) -> List[Dict]:
        """
        文档分块（滑动窗口）

        参数:
            documents: 原始文档列表
            chunk_size: 块大小（字符数）
            chunk_overlap: 重叠大小

        返回:
            块信息列表 [{"text": ..., "doc_id": ..., "chunk_id": ...}, ...]
        """
        chunks = []

        for doc_id, doc in enumerate(documents):
            # TODO: 实现滑动窗口分块
            # 提示：
            # 1. 使用 range(0, len(doc), chunk_size - chunk_overlap)
            # 2. 每次截取 doc[i:i+chunk_size]
            # 3. 保存块信息到 chunks 列表

            start = 0
            chunk_id = 0
            while start < len(doc):
                end = min(start + chunk_size, len(doc))
                chunk_text = doc[start:end]

                chunks.append({
                    "text": chunk_text,
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "start": start,
                    "end": end
                })

                chunk_id += 1
                start += (chunk_size - chunk_overlap)

        return chunks

    def embed_text(self, text: str) -> np.ndarray:
        """
        模拟文本向量化（实际应调用 OpenAI Embeddings）

        参数:
            text: 输入文本

        返回:
            向量 (embedding_dim,)
        """
        # TODO: 模拟 Embedding（简化为文本哈希 + 归一化）
        # 提示：
        # 1. 使用 hash(text) 作为随机种子
        # 2. 生成随机向量 np.random.randn(self.embedding_dim)
        # 3. L2 归一化

        np.random.seed(hash(text) % (2**32))  # 确保相同文本得到相同向量
        vec = np.random.randn(self.embedding_dim)
        return vec / np.linalg.norm(vec)  # 参考答案

    def index_documents(self, documents: List[str]):
        """
        索引文档（分块 + 向量化）

        参数:
            documents: 文档列表
        """
        print(f"📄 正在索引 {len(documents)} 个文档...")

        # TODO: 实现文档索引流程
        # 1. 文档分块
        self.documents = documents
        self.chunk_metadata = self.chunk_documents(documents)

        # 2. 向量化每个块
        # TODO: 调用 embed_text 为每个块生成向量
        self.doc_embeddings = np.array([
            self.embed_text(chunk["text"])
            for chunk in self.chunk_metadata
        ])

        print(f"✅ 索引完成: {len(self.chunk_metadata)} 个文档块")

    def retrieve(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        检索相关文档

        参数:
            query: 用户问题
            top_k: 返回块数

        返回:
            相关块列表 [{"text": ..., "score": ..., "metadata": ...}, ...]
        """
        # TODO: 实现检索逻辑
        # 1. 向量化查询
        query_vec = self.embed_text(query)

        # 2. 计算余弦相似度（使用归一化向量的点积）
        scores = np.dot(self.doc_embeddings, query_vec)

        # 3. Top-K 排序
        top_k_indices = np.argsort(scores)[::-1][:top_k]

        # 4. 构建结果
        results = [
            {
                "text": self.chunk_metadata[idx]["text"],
                "score": scores[idx],
                "metadata": self.chunk_metadata[idx]
            }
            for idx in top_k_indices
        ]

        return results  # 参考答案

    def build_prompt(
        self,
        query: str,
        contexts: List[Dict]
    ) -> str:
        """
        构建增强 Prompt

        参数:
            query: 用户问题
            contexts: 检索到的上下文

        返回:
            完整 Prompt
        """
        # TODO: 实现 Prompt 模板
        # 提示：
        # 1. 拼接所有上下文
        # 2. 插入到 Prompt 模板中
        # 3. 模板格式参考 RAG 最佳实践

        context_text = "\n\n".join([
            f"【参考文档 {i+1}】\n{ctx['text']}"
            for i, ctx in enumerate(contexts)
        ])

        prompt = f"""你是一个专业的问答助手。请基于以下参考文档回答用户问题。

参考文档:
{context_text}

用户问题: {query}

要求:
1. 仅基于参考文档回答，不要编造信息
2. 如果文档中没有相关信息，明确告知用户
3. 引用具体的文档编号

你的回答:"""

        return prompt  # 参考答案

    def generate(self, prompt: str) -> str:
        """
        模拟 LLM 生成（简化版）

        参数:
            prompt: 增强后的 Prompt

        返回:
            生成的答案
        """
        # TODO: 模拟生成逻辑（实际应调用 OpenAI API）
        # 提示：
        # 1. 简化版：提取 Prompt 中的关键信息
        # 2. 返回模板化答案

        # 简化实现：直接返回检索到的第一个文档片段
        return "【模拟生成】基于参考文档，这是一个示例答案。"

    def ask(self, query: str, top_k: int = 3) -> Dict:
        """
        完整 RAG 流程

        参数:
            query: 用户问题
            top_k: 检索块数

        返回:
            {"answer": ..., "contexts": ..., "prompt": ...}
        """
        print(f"\n❓ 问题: {query}")

        # TODO: 串联完整流程
        # 1. 检索
        print("🔍 正在检索相关文档...")
        contexts = self.retrieve(query, top_k)

        # 2. 构建 Prompt
        prompt = self.build_prompt(query, contexts)

        # 3. 生成答案
        print("🤖 正在生成答案...")
        answer = self.generate(prompt)

        # 显示结果
        print(f"\n💡 答案: {answer}")
        print(f"\n📚 参考来源:")
        for i, ctx in enumerate(contexts, 1):
            print(f"  {i}. [相似度: {ctx['score']:.4f}] {ctx['text'][:100]}...")

        return {
            "answer": answer,
            "contexts": contexts,
            "prompt": prompt
        }


# 测试代码
if __name__ == "__main__":
    # 准备测试文档
    documents = [
        """
        RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术。
        它首先从知识库中检索相关文档，然后将这些文档作为上下文输入给大语言模型。
        RAG 的优势在于可以使用外部知识，减少模型幻觉，提高答案准确性。
        """,
        """
        Embedding 是将文本转换为向量的过程。常见的模型包括 Word2Vec、GloVe 和 BERT。
        OpenAI 的 text-embedding-ada-002 是目前最流行的 Embedding 模型之一。
        向量维度通常在 128 到 1536 之间，维度越高表达能力越强但计算成本也越高。
        """,
        """
        向量数据库用于高效存储和检索向量。主流产品包括 Chroma、Pinecone、Weaviate 等。
        索引算法主要有 HNSW（层次化可导航小世界图）和 IVF（倒排文件）。
        HNSW 在查询速度和召回率上表现优异，适合大规模检索场景。
        """,
        """
        LLM（大语言模型）的核心是 Transformer 架构。训练过程包括预训练和微调两个阶段。
        预训练使用海量无标注文本，微调则针对特定任务进行优化。
        GPT-4、Claude 等模型都基于这一架构，参数量从几十亿到上万亿不等。
        """
    ]

    # 初始化 RAG 系统
    rag = SimpleRAG(embedding_dim=128)

    # 索引文档
    rag.index_documents(documents)

    # 测试问答
    test_queries = [
        "什么是 RAG？",
        "Embedding 模型有哪些？",
        "HNSW 索引的优势是什么？",
        "LLM 的训练分几个阶段？"
    ]

    for query in test_queries:
        result = rag.ask(query, top_k=2)
        print("\n" + "="*70 + "\n")
```

### ✅ 预期输出
```
📄 正在索引 4 个文档...
✅ 索引完成: 8 个文档块

❓ 问题: 什么是 RAG？
🔍 正在检索相关文档...
🤖 正在生成答案...

💡 答案: 【模拟生成】基于参考文档，这是一个示例答案。

📚 参考来源:
  1. [相似度: 0.8765] RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术...
  2. [相似度: 0.3421] 向量数据库用于高效存储和检索向量...

======================================================================
```

### 🔍 检查点
- [ ] 文档分块是否有重叠？
- [ ] 检索结果是否按相似度降序排列?
- [ ] Prompt 中是否包含所有检索到的上下文？
- [ ] 完整流程是否能够运行？

---

## 🎯 进阶挑战

完成以上三个练习后，尝试以下挑战：

### 挑战 1: 集成真实 API
- 将练习 1 的模拟 Embedding 替换为 OpenAI Embeddings API
- 将练习 3 的模拟生成替换为 GPT-4 API
- 对比模拟和真实 API 的效果差异

### 挑战 2: 性能优化
- 为练习 2 添加 HNSW 索引（使用 hnswlib 库）
- 测试在 10,000 个文档上的检索速度
- 分析召回率 vs 速度的权衡

### 挑战 3: 可视化
- 使用 t-SNE 降维可视化文档向量的分布
- 绘制查询向量与候选文档的相似度热力图
- 展示 Top-K 检索的决策过程

### 挑战 4: 评估指标
- 实现 MRR (Mean Reciprocal Rank) 评估检索质量
- 实现 BLEU/ROUGE 评估生成质量
- 创建测试集并计算端到端准确率

---

## 📖 参考答案

完整的参考答案代码请见：`RAG技术栈-实战练习-答案.py`

---

## 🔗 相关学习资源

- **笔记索引**: `RAG技术栈-多维学习指南.md`
- **深度技术笔记**:
  - `Embeddings底层原理.md`
  - `向量数据库底层原理.md`
  - `RAG底层原理.md`
  - `LLM底层原理.md`

---

**建议学习路径**:
练习 1 (1-2小时) → 练习 2 (2-3小时) → 练习 3 (3-4小时) → 进阶挑战 (可选)

**完成标志**:
所有 TODO 部分实现完毕，且预期输出与实际一致 ✅
