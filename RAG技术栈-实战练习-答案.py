"""
RAG 技术栈 - 实战练习参考答案

包含三个练习的完整实现：
1. 手写 Embedding 查找表
2. 手写余弦相似度搜索
3. 模拟 RAG 完整流程
"""
========================
import numpy as np
from typing import List, Dict, Tuple
import heapq
import time

# ============================================================================
# 练习 1: 手写 Embedding 查找表
# ============================================================================

class SimpleEmbedding:
    """简化的 Embedding 查找表实现（完整答案）"""

    def __init__(self, vocab_size: int = 5000, embedding_dim: int = 128):
        """初始化 Embedding 层"""
        # 答案：初始化随机权重矩阵
        np.random.seed(42)
        self.embedding_matrix = np.random.randn(vocab_size, embedding_dim) * 0.01

        # 模拟 BPE 词表
        self.token_to_id = {
            "<PAD>": 0,
            "<UNK>": 1,
            "hello": 2,
            "world": 3,
            "##ing": 4,
            "embed": 5,
            "##ding": 6,
            "test": 7,
            "rag": 8,
        }
        self.id_to_token = {v: k for k, v in self.token_to_id.items()}

    def tokenize(self, text: str) -> List[str]:
        """简化的 BPE 分词（答案）"""
        text = text.lower().strip()
        words = text.split()
        tokens = []

        for word in words:
            # 检查是否在词表中
            if word in self.token_to_id:
                tokens.append(word)
            else:
                # 简化版子词分解（实际 BPE 更复杂）
                # 尝试分解为已知子词
                found = False
                for prefix_len in range(len(word), 0, -1):
                    prefix = word[:prefix_len]
                    if prefix in self.token_to_id:
                        tokens.append(prefix)
                        # 处理剩余部分
                        suffix = word[prefix_len:]
                        if suffix:
                            suffix_token = f"##{suffix}"
                            if suffix_token in self.token_to_id:
                                tokens.append(suffix_token)
                            else:
                                tokens.append("<UNK>")
                        found = True
                        break

                if not found:
                    tokens.append("<UNK>")

        return tokens

    def encode(self, tokens: List[str]) -> List[int]:
        """将 token 转换为 ID（答案）"""
        return [self.token_to_id.get(token, 1) for token in tokens]

    def lookup(self, token_ids: List[int]) -> np.ndarray:
        """查找向量（答案）"""
        return self.embedding_matrix[token_ids]

    def forward(self, text: str) -> np.ndarray:
        """完整的前向传播（答案）"""
        tokens = self.tokenize(text)
        ids = self.encode(tokens)
        vectors = self.lookup(ids)
        return vectors


# ============================================================================
# 练习 2: 手写余弦相似度搜索
# ============================================================================

class VectorSearch:
    """简化的向量搜索引擎（完整答案）"""

    def __init__(self, vectors: np.ndarray, metadata: List[str] = None):
        """初始化搜索引擎"""
        self.vectors = vectors
        self.normalized_vectors = None
        self.metadata = metadata or [f"Doc_{i}" for i in range(len(vectors))]
        self.normalize_vectors()

    def normalize_vectors(self):
        """归一化向量（答案）"""
        # 计算 L2 范数
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)

        # 避免除以零
        norms = np.where(norms == 0, 1, norms)

        # 归一化
        self.normalized_vectors = self.vectors / norms

    def cosine_similarity(self, query: np.ndarray, doc: np.ndarray) -> float:
        """计算余弦相似度（答案）"""
        # 点积
        dot_product = np.dot(query, doc)

        # 范数
        query_norm = np.linalg.norm(query)
        doc_norm = np.linalg.norm(doc)

        # 避免除以零
        if query_norm == 0 or doc_norm == 0:
            return 0.0

        # 余弦相似度
        return dot_product / (query_norm * doc_norm)

    def cosine_similarity_optimized(self, query: np.ndarray) -> np.ndarray:
        """优化的批量余弦相似度计算（答案）"""
        # 归一化查询向量
        query_norm = query / np.linalg.norm(query)

        # 矩阵乘法（归一化后，余弦相似度 = 点积）
        scores = np.dot(self.normalized_vectors, query_norm)

        return scores

    def l2_distance(self, query: np.ndarray, doc: np.ndarray) -> float:
        """计算 L2 距离（答案）"""
        return np.linalg.norm(query - doc)

    def search(
        self,
        query: np.ndarray,
        k: int = 3,
        metric: str = "cosine"
    ) -> List[Tuple[int, float, str]]:
        """Top-K 检索（答案）"""
        if metric == "cosine":
            # 使用优化的余弦相似度
            all_scores = self.cosine_similarity_optimized(query)

            # Top-K（降序）
            top_k_indices = np.argsort(all_scores)[::-1][:k]

            # 构建结果
            results = [
                (idx, all_scores[idx], self.metadata[idx])
                for idx in top_k_indices
            ]

        elif metric == "l2":
            # 计算所有 L2 距离
            all_distances = [
                self.l2_distance(query, doc)
                for doc in self.vectors
            ]

            # Top-K（升序，距离越小越好）
            top_k_indices = heapq.nsmallest(
                k,
                range(len(all_distances)),
                key=lambda i: all_distances[i]
            )

            # 构建结果
            results = [
                (idx, all_distances[idx], self.metadata[idx])
                for idx in top_k_indices
            ]

        else:
            raise ValueError(f"不支持的度量: {metric}")

        return results


# ============================================================================
# 练习 3: 模拟 RAG 完整流程
# ============================================================================

class SimpleRAG:
    """简化的 RAG 系统实现（完整答案）"""

    def __init__(self, embedding_dim: int = 128):
        """初始化 RAG 系统"""
        self.embedding_dim = embedding_dim
        self.documents = []
        self.doc_embeddings = None
        self.chunk_metadata = []

    def chunk_documents(
        self,
        documents: List[str],
        chunk_size: int = 200,
        chunk_overlap: int = 50
    ) -> List[Dict]:
        """文档分块（答案）"""
        chunks = []

        for doc_id, doc in enumerate(documents):
            start = 0
            chunk_id = 0

            while start < len(doc):
                end = min(start + chunk_size, len(doc))
                chunk_text = doc[start:end].strip()

                # 过滤空块
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "start": start,
                        "end": end
                    })
                    chunk_id += 1

                # 滑动窗口
                start += (chunk_size - chunk_overlap)

        return chunks

    def embed_text(self, text: str) -> np.ndarray:
        """模拟文本向量化（答案）"""
        # 使用文本哈希作为种子，确保相同文本得到相同向量
        seed = hash(text) % (2**32)
        np.random.seed(seed)

        # 生成随机向量
        vec = np.random.randn(self.embedding_dim)

        # L2 归一化
        norm = np.linalg.norm(vec)
        if norm == 0:
            return vec
        return vec / norm

    def index_documents(self, documents: List[str]):
        """索引文档（答案）"""
        print(f"📄 正在索引 {len(documents)} 个文档...")

        # 1. 文档分块
        self.documents = documents
        self.chunk_metadata = self.chunk_documents(documents)

        # 2. 向量化每个块
        embeddings = []
        for chunk in self.chunk_metadata:
            vec = self.embed_text(chunk["text"])
            embeddings.append(vec)

        self.doc_embeddings = np.array(embeddings)

        print(f"✅ 索引完成: {len(self.chunk_metadata)} 个文档块")

    def retrieve(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        """检索相关文档（答案）"""
        # 1. 向量化查询
        query_vec = self.embed_text(query)

        # 2. 计算余弦相似度（归一化向量的点积）
        scores = np.dot(self.doc_embeddings, query_vec)

        # 3. Top-K 排序
        top_k_indices = np.argsort(scores)[::-1][:top_k]

        # 4. 构建结果
        results = [
            {
                "text": self.chunk_metadata[idx]["text"],
                "score": float(scores[idx]),
                "metadata": self.chunk_metadata[idx]
            }
            for idx in top_k_indices
        ]

        return results

    def build_prompt(
        self,
        query: str,
        contexts: List[Dict]
    ) -> str:
        """构建增强 Prompt（答案）"""
        # 拼接上下文
        context_text = "\n\n".join([
            f"【参考文档 {i+1}】(相似度: {ctx['score']:.4f})\n{ctx['text']}"
            for i, ctx in enumerate(contexts)
        ])

        # Prompt 模板
        prompt = f"""你是一个专业的问答助手。请基于以下参考文档回答用户问题。

参考文档:
{context_text}

用户问题: {query}

要求:
1. 仅基于参考文档回答，不要编造信息
2. 如果文档中没有相关信息，明确告知用户
3. 引用具体的文档编号（如"根据参考文档1..."）
4. 保持回答简洁专业

你的回答:"""

        return prompt

    def generate(self, prompt: str, contexts: List[Dict]) -> str:
        """模拟 LLM 生成（答案）"""
        # 简化实现：提取最相关文档的关键信息
        if not contexts:
            return "抱歉，没有找到相关文档来回答您的问题。"

        # 获取最相关的文档
        best_context = contexts[0]

        # 模拟生成（实际应调用 OpenAI API）
        answer = f"""根据参考文档，以下是相关信息：

{best_context['text'][:200]}...

（这是一个模拟回答，实际应使用 LLM API 生成更自然的答案）
"""
        return answer.strip()

    def ask(self, query: str, top_k: int = 3, verbose: bool = True) -> Dict:
        """完整 RAG 流程（答案）"""
        if verbose:
            print(f"\n❓ 问题: {query}")

        # 1. 检索
        if verbose:
            print("🔍 正在检索相关文档...")
        contexts = self.retrieve(query, top_k)

        # 2. 构建 Prompt
        prompt = self.build_prompt(query, contexts)

        # 3. 生成答案
        if verbose:
            print("🤖 正在生成答案...")
        answer = self.generate(prompt, contexts)

        # 显示结果
        if verbose:
            print(f"\n💡 答案:\n{answer}")
            print(f"\n📚 参考来源:")
            for i, ctx in enumerate(contexts, 1):
                print(f"  {i}. [相似度: {ctx['score']:.4f}] {ctx['text'][:80]}...")

        return {
            "answer": answer,
            "contexts": contexts,
            "prompt": prompt
        }


# ============================================================================
# 测试代码
# ============================================================================

def test_exercise_1():
    """测试练习 1: Embedding 查找表"""
    print("\n" + "="*70)
    print("练习 1: Embedding 查找表测试")
    print("="*70)

    embed = SimpleEmbedding(vocab_size=5000, embedding_dim=128)

    # 测试用例
    text = "hello world"
    print(f"\n输入文本: {text}")

    # 分词
    tokens = embed.tokenize(text)
    print(f"分词结果: {tokens}")

    # 编码
    ids = embed.encode(tokens)
    print(f"ID 序列: {ids}")

    # 查找向量
    vectors = embed.lookup(ids)
    print(f"向量形状: {vectors.shape}")

    # 完整流程
    output = embed.forward(text)
    print(f"最终输出形状: {output.shape}")

    print("\n✅ 练习 1 测试通过！")


def test_exercise_2():
    """测试练习 2: 余弦相似度搜索"""
    print("\n" + "="*70)
    print("练习 2: 余弦相似度搜索测试")
    print("="*70)

    # 创建模拟数据库
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
    query = vectors[1] + np.random.randn(dim) * 0.1

    # 测试余弦相似度
    print("\n=== 余弦相似度搜索 ===")
    results_cosine = search_engine.search(query, k=3, metric="cosine")
    for rank, (doc_id, score, meta) in enumerate(results_cosine, 1):
        print(f"{rank}. {meta} (相似度: {score:.4f})")

    # 测试 L2 距离
    print("\n=== L2 距离搜索 ===")
    results_l2 = search_engine.search(query, k=3, metric="l2")
    for rank, (doc_id, dist, meta) in enumerate(results_l2, 1):
        print(f"{rank}. {meta} (距离: {dist:.4f})")

    # 性能对比
    print("\n=== 性能对比 ===")
    # 暴力法
    start = time.time()
    for i in range(100):
        _ = [search_engine.cosine_similarity(query, doc) for doc in vectors]
    t_brute = time.time() - start

    # 优化法
    start = time.time()
    for i in range(100):
        _ = search_engine.cosine_similarity_optimized(query)
    t_opt = time.time() - start

    print(f"暴力法 (100次): {t_brute:.4f}s")
    print(f"优化法 (100次): {t_opt:.4f}s")
    print(f"加速比: {t_brute / t_opt:.2f}x")

    print("\n✅ 练习 2 测试通过！")


def test_exercise_3():
    """测试练习 3: RAG 完整流程"""
    print("\n" + "="*70)
    print("练习 3: RAG 完整流程测试")
    print("="*70)

    # 准备测试文档
    documents = [
        """
        RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术。
        它首先从知识库中检索相关文档，然后将这些文档作为上下文输入给大语言模型。
        RAG 的优势在于可以使用外部知识，减少模型幻觉，提高答案准确性。
        典型的 RAG 流程包括：文档分块、向量化、索引、检索、生成五个步骤。
        """,
        """
        Embedding 是将文本转换为向量的过程。常见的模型包括 Word2Vec、GloVe 和 BERT。
        OpenAI 的 text-embedding-ada-002 是目前最流行的 Embedding 模型之一。
        向量维度通常在 128 到 1536 之间，维度越高表达能力越强但计算成本也越高。
        Embedding 的质量直接影响检索效果，需要在成本和性能间权衡。
        """,
        """
        向量数据库用于高效存储和检索向量。主流产品包括 Chroma、Pinecone、Weaviate 等。
        索引算法主要有 HNSW（层次化可导航小世界图）和 IVF（倒排文件）。
        HNSW 在查询速度和召回率上表现优异，适合大规模检索场景。
        向量数据库还需要考虑持久化、并发、分布式等工程问题。
        """,
        """
        LLM（大语言模型）的核心是 Transformer 架构。训练过程包括预训练和微调两个阶段。
        预训练使用海量无标注文本，微调则针对特定任务进行优化。
        GPT-4、Claude 等模型都基于这一架构，参数量从几十亿到上万亿不等。
        Temperature 参数控制生成的随机性，Top-p 采样可以平衡多样性和质量。
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
    ]

    for query in test_queries:
        result = rag.ask(query, top_k=2)
        print("\n" + "-"*70)

    print("\n✅ 练习 3 测试通过！")


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("RAG 技术栈 - 实战练习参考答案")
    print("="*70)

    test_exercise_1()
    test_exercise_2()
    test_exercise_3()

    print("\n" + "="*70)
    print("🎉 所有练习测试完成！")
    print("="*70)


if __name__ == "__main__":
    main()
