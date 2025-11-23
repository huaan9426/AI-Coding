# Embeddings 底层原理

## 文字到向量的完整过程

### 第一步：Tokenization（文字 → Token ID）

#### BPE 算法原理

```python
# 训练阶段
corpus = ["low", "lower", "newest", "widest"]

# 1. 初始化：字符级切分
vocab = set()
words = {}
for word in corpus:
    words[word] = list(word) + ['</w>']  # </w> 表示词结束
    vocab.update(words[word])

# words = {
#     "low": ['l', 'o', 'w', '</w>'],
#     "lower": ['l', 'o', 'w', 'e', 'r', '</w>'],
#     ...
# }

# 2. 统计相邻字符对频率
def get_stats(words):
    pairs = {}
    for word, chars in words.items():
        for i in range(len(chars)-1):
            pair = (chars[i], chars[i+1])
            pairs[pair] = pairs.get(pair, 0) + 1
    return pairs

# pairs = {
#     ('l', 'o'): 2,  # "low" 和 "lower"
#     ('o', 'w'): 2,
#     ('w', '</w>'): 1,
#     ('w', 'e'): 1,
#     ...
# }

# 3. 合并最高频pair
def merge_vocab(pair, words):
    new_words = {}
    bigram = ' '.join(pair)
    replacement = ''.join(pair)
    for word, chars in words.items():
        new_chars = []
        i = 0
        while i < len(chars):
            if i < len(chars)-1 and (chars[i], chars[i+1]) == pair:
                new_chars.append(replacement)
                i += 2
            else:
                new_chars.append(chars[i])
                i += 1
        new_words[word] = new_chars
    return new_words

# 第1次迭代：合并 ('l', 'o')
words = merge_vocab(('l', 'o'), words)
vocab.add('lo')
# words = {
#     "low": ['lo', 'w', '</w>'],
#     "lower": ['lo', 'w', 'e', 'r', '</w>'],
#     ...
# }

# 第2次迭代：合并 ('lo', 'w')
words = merge_vocab(('lo', 'w'), words)
vocab.add('low')
# words = {
#     "low": ['low', '</w>'],
#     "lower": ['low', 'e', 'r', '</w>'],
#     ...
# }

# 重复 N 次直到词汇表达到目标大小（如 50,000）
```

#### Tiktoken（OpenAI 的实现）

```python
import tiktoken

encoding = tiktoken.get_encoding("cl100k_base")

# UTF-8 字节级 BPE
text = "狗"
utf8_bytes = text.encode('utf-8')  # b'\xe7\x8b\x97'

# 每个字节先转为 token
# 然后根据预训练的合并规则逐步合并
tokens = encoding.encode(text)

# 中文通常被拆成多个 token
# 因为 BPE 训练语料以英文为主
```

#### Token ID 的数学表示

```
设词汇表 V = {token_0, token_1, ..., token_99999}
设映射函数 f: text → [id_1, id_2, ..., id_n]

f("狗很可爱") = [105939, 104523, 100234, 98765]
```

---

### 第二步：Embedding Layer（Token ID → 初始向量）

#### Embedding 矩阵

```python
import numpy as np

# Embedding 矩阵 W_e ∈ R^(V×d)
# V = vocab_size = 100,256
# d = embedding_dim = 1536

W_e = np.random.randn(100256, 1536) * np.sqrt(2/1536)  # Xavier 初始化

# 查表操作
token_id = 105939
embedding_vector = W_e[token_id, :]  # shape: (1536,)
```

#### 数学表示

```
设 W_e ∈ R^(V×d)
设 token_id = i

embedding(i) = W_e[i, :] ∈ R^d
```

#### One-Hot 到 Embedding 的等价形式

```python
# One-Hot 编码
token_id = 105939
one_hot = np.zeros(100256)
one_hot[token_id] = 1

# Embedding = 矩阵乘法
embedding = one_hot @ W_e  # (100256,) @ (100256, 1536) = (1536,)

# 等价于直接索引
embedding = W_e[token_id, :]
```

#### 位置编码（Sinusoidal）

```python
def positional_encoding(position, d_model):
    """
    PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
    """
    pe = np.zeros(d_model)
    for i in range(0, d_model, 2):
        denominator = np.power(10000, 2*i / d_model)
        pe[i] = np.sin(position / denominator)
        pe[i+1] = np.cos(position / denominator)
    return pe

# 最终输入
token_emb = W_e[token_id, :]
pos_emb = positional_encoding(position, d_model=1536)
final_emb = token_emb + pos_emb  # 逐元素相加
```

#### 为什么使用 sin/cos？

```
1. 连续性：相邻位置的编码相似
2. 可外推：可以处理训练时未见过的长度
3. 线性关系：PE(pos+k) 可以表示为 PE(pos) 的线性函数

证明：
sin(α + β) = sin(α)cos(β) + cos(α)sin(β)
cos(α + β) = cos(α)cos(β) - sin(α)sin(β)

因此 PE(pos+k) 可以由 PE(pos) 和 PE(k) 计算得出
```

---

### 第三步：Transformer Encoder（初始向量 → 语义向量）

#### 注意力机制（Self-Attention）

```python
def scaled_dot_product_attention(Q, K, V):
    """
    Attention(Q, K, V) = softmax(QK^T / √d_k) V

    Q: Query  [seq_len, d_k]
    K: Key    [seq_len, d_k]
    V: Value  [seq_len, d_v]
    """
    d_k = Q.shape[-1]

    # 1. 计算相似度：QK^T
    scores = Q @ K.T  # [seq_len, seq_len]

    # 2. 缩放：除以 √d_k
    scores = scores / np.sqrt(d_k)

    # 3. Softmax 归一化
    attention_weights = softmax(scores, axis=-1)

    # 4. 加权求和
    output = attention_weights @ V  # [seq_len, d_v]

    return output, attention_weights
```

#### Multi-Head Attention

```python
def multi_head_attention(X, num_heads=12, d_model=1536):
    """
    X: [seq_len, d_model]
    """
    d_k = d_model // num_heads  # 1536 / 12 = 128

    # 线性投影矩阵
    W_q = np.random.randn(d_model, d_model)
    W_k = np.random.randn(d_model, d_model)
    W_v = np.random.randn(d_model, d_model)
    W_o = np.random.randn(d_model, d_model)

    # 投影
    Q = X @ W_q  # [seq_len, d_model]
    K = X @ W_k
    V = X @ W_v

    # 分成多个头
    seq_len = X.shape[0]
    Q = Q.reshape(seq_len, num_heads, d_k).transpose(1, 0, 2)  # [num_heads, seq_len, d_k]
    K = K.reshape(seq_len, num_heads, d_k).transpose(1, 0, 2)
    V = V.reshape(seq_len, num_heads, d_k).transpose(1, 0, 2)

    # 每个头独立计算 attention
    outputs = []
    for i in range(num_heads):
        output, _ = scaled_dot_product_attention(Q[i], K[i], V[i])
        outputs.append(output)

    # 拼接所有头
    concat = np.concatenate(outputs, axis=-1)  # [seq_len, d_model]

    # 输出投影
    final_output = concat @ W_o  # [seq_len, d_model]

    return final_output
```

#### Feed-Forward Network

```python
def feed_forward(X, d_ff=6144):
    """
    FFN(x) = max(0, xW_1 + b_1)W_2 + b_2

    d_model = 1536
    d_ff = 4 * d_model = 6144
    """
    W_1 = np.random.randn(1536, d_ff)
    b_1 = np.random.randn(d_ff)
    W_2 = np.random.randn(d_ff, 1536)
    b_2 = np.random.randn(1536)

    # 第一层：线性 + ReLU
    hidden = np.maximum(0, X @ W_1 + b_1)  # [seq_len, d_ff]

    # 第二层：线性
    output = hidden @ W_2 + b_2  # [seq_len, d_model]

    return output
```

#### Layer Normalization

```python
def layer_norm(X, eps=1e-6):
    """
    LN(x) = γ * (x - μ) / (σ + ε) + β

    X: [seq_len, d_model]
    """
    mean = X.mean(axis=-1, keepdims=True)  # [seq_len, 1]
    std = X.std(axis=-1, keepdims=True)

    # 归一化
    X_norm = (X - mean) / (std + eps)

    # 可学习的缩放和平移
    gamma = np.ones(X.shape[-1])
    beta = np.zeros(X.shape[-1])

    output = gamma * X_norm + beta

    return output
```

#### 完整的 Transformer Block

```python
def transformer_block(X):
    """
    一个 Transformer 编码器层

    X: [seq_len, d_model]
    """
    # 1. Multi-Head Self-Attention + Residual + LN
    attn_output = multi_head_attention(X)
    X = layer_norm(X + attn_output)  # Add & Norm

    # 2. Feed-Forward + Residual + LN
    ff_output = feed_forward(X)
    X = layer_norm(X + ff_output)  # Add & Norm

    return X

# OpenAI text-embedding-3-small 使用 12 层
def transformer_encoder(X, num_layers=12):
    for _ in range(num_layers):
        X = transformer_block(X)
    return X
```

---

### 第四步：Pooling（序列向量 → 单一向量）

```python
# 输入：[seq_len, d_model] 的序列
# 输出：[d_model] 的单一向量

# 方法 1：CLS token（BERT 使用）
sentence_vector = X[0, :]  # 取第一个 token

# 方法 2：Mean Pooling（OpenAI 使用）
sentence_vector = X.mean(axis=0)  # [d_model]

# 方法 3：Max Pooling
sentence_vector = X.max(axis=0)

# 方法 4：Last token
sentence_vector = X[-1, :]
```

---

## 完整流程代码

```python
import numpy as np
import tiktoken

class TextEmbeddingModel:
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.vocab_size = 100256
        self.d_model = 1536
        self.num_heads = 12
        self.num_layers = 12

        # 初始化权重
        self.W_embed = np.random.randn(self.vocab_size, self.d_model) * 0.02

    def tokenize(self, text):
        return self.tokenizer.encode(text)

    def embed(self, token_ids):
        # Token embedding + Positional encoding
        embeddings = []
        for pos, token_id in enumerate(token_ids):
            token_emb = self.W_embed[token_id, :]
            pos_emb = positional_encoding(pos, self.d_model)
            embeddings.append(token_emb + pos_emb)
        return np.array(embeddings)  # [seq_len, d_model]

    def encode(self, text):
        # 1. Tokenization
        token_ids = self.tokenize(text)

        # 2. Embedding
        X = self.embed(token_ids)  # [seq_len, d_model]

        # 3. Transformer layers
        X = transformer_encoder(X, num_layers=self.num_layers)

        # 4. Pooling
        sentence_vector = X.mean(axis=0)  # [d_model]

        return sentence_vector


# 使用
model = TextEmbeddingModel()
text = "狗很可爱"
vector = model.encode(text)
print(vector.shape)  # (1536,)
```

---

## 训练过程

### 对比学习（Contrastive Learning）

OpenAI 使用对比学习训练 Embedding 模型：

```python
# 训练数据：(query, positive_doc, negative_doc) 三元组
# 目标：让 query 和 positive_doc 的向量相似
#      让 query 和 negative_doc 的向量不相似

def contrastive_loss(query_vec, pos_vec, neg_vec, temperature=0.05):
    """
    InfoNCE Loss
    """
    # 计算相似度（余弦相似度）
    sim_pos = cosine_similarity(query_vec, pos_vec)  # 标量
    sim_neg = cosine_similarity(query_vec, neg_vec)  # 标量

    # 缩放
    sim_pos /= temperature
    sim_neg /= temperature

    # 对比损失
    loss = -np.log(
        np.exp(sim_pos) / (np.exp(sim_pos) + np.exp(sim_neg))
    )

    return loss

# 梯度下降更新 W_embed 和 Transformer 权重
```

### 大规模训练

```
训练数据规模：数百 GB 文本对
- 搜索查询 ↔ 文档
- 问题 ↔ 答案
- 句子 ↔ 同义句

负样本采样策略：
1. Batch 内负样本（同一 batch 的其他文档）
2. Hard negative（相似但不相关的文档）

优化器：AdamW
学习率：1e-5 到 1e-4（warmup + decay）
Batch size：1024-4096
训练步数：数十万步
```

---

## 数学公式总结

```
1. Token Embedding:
   e_i = W_e[i, :] ∈ R^d

2. Positional Encoding:
   PE(pos, 2i) = sin(pos / 10000^(2i/d))
   PE(pos, 2i+1) = cos(pos / 10000^(2i/d))

3. Self-Attention:
   Attention(Q, K, V) = softmax(QK^T / √d_k) V

4. Multi-Head Attention:
   MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
   where head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)

5. Feed-Forward:
   FFN(x) = max(0, xW_1 + b_1)W_2 + b_2

6. Layer Normalization:
   LN(x) = γ * (x - μ) / σ + β

7. Residual Connection:
   output = LayerNorm(x + Sublayer(x))

8. Final Pooling:
   s = (1/N) Σ h_i  (Mean Pooling)
```

---

## 参数量计算

```
Embedding 层：
W_e: 100,256 × 1,536 = 154,793,216 参数

Transformer 层（每层）：
- Multi-Head Attention:
  W_q, W_k, W_v: 3 × (1536 × 1536) = 7,077,888
  W_o: 1536 × 1536 = 2,359,296
- Feed-Forward:
  W_1: 1536 × 6144 = 9,437,184
  W_2: 6144 × 1536 = 9,437,184
- Layer Norm: 2 × (1536 × 2) = 6,144

每层总计: ≈ 28,317,696 参数

12 层: 12 × 28,317,696 = 339,812,352 参数

总参数: 154,793,216 + 339,812,352 ≈ 495M 参数

模型大小: 495M × 4 字节 = 1.98 GB (float32)
```

---

## Tiktoken 实战

```python
import tiktoken

# 查看不同 tokenizer 的差异
text = "我爱机器学习"

for encoding_name in ["r50k_base", "p50k_base", "cl100k_base", "o200k_base"]:
    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    print(f"{encoding_name:15s}: {len(tokens):2d} tokens | {tokens}")

# 输出（示例）:
# r50k_base     : 12 tokens | [...]
# p50k_base     : 12 tokens | [...]
# cl100k_base   :  8 tokens | [...]
# o200k_base    :  5 tokens | [...]  (最新，对中文优化)
```

---

## 维度对性能的影响

```python
from openai import OpenAI
import numpy as np

client = OpenAI()

# 测试不同维度的相似度保持
text1 = "机器学习"
text2 = "深度学习"
text3 = "汽车"

# 1536 维
emb1_full = client.embeddings.create(input=text1, model="text-embedding-3-small").data[0].embedding
emb2_full = client.embeddings.create(input=text2, model="text-embedding-3-small").data[0].embedding
emb3_full = client.embeddings.create(input=text3, model="text-embedding-3-small").data[0].embedding

sim_12_full = np.dot(emb1_full, emb2_full) / (np.linalg.norm(emb1_full) * np.linalg.norm(emb2_full))
sim_13_full = np.dot(emb1_full, emb3_full) / (np.linalg.norm(emb1_full) * np.linalg.norm(emb3_full))

# 512 维
emb1_small = client.embeddings.create(input=text1, model="text-embedding-3-small", dimensions=512).data[0].embedding
emb2_small = client.embeddings.create(input=text2, model="text-embedding-3-small", dimensions=512).data[0].embedding
emb3_small = client.embeddings.create(input=text3, model="text-embedding-3-small", dimensions=512).data[0].embedding

sim_12_small = np.dot(emb1_small, emb2_small) / (np.linalg.norm(emb1_small) * np.linalg.norm(emb2_small))
sim_13_small = np.dot(emb1_small, emb3_small) / (np.linalg.norm(emb1_small) * np.linalg.norm(emb3_small))

print(f"1536维: 机器学习 vs 深度学习 = {sim_12_full:.3f}")
print(f"1536维: 机器学习 vs 汽车 = {sim_13_full:.3f}")
print(f"512维:  机器学习 vs 深度学习 = {sim_12_small:.3f}")
print(f"512维:  机器学习 vs 汽车 = {sim_13_small:.3f}")

# 相似度排序通常保持一致，但绝对值会有变化
```
