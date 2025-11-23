# LLM 底层原理

## Transformer Decoder 架构

### GPT 的完整结构

```python
class GPTModel:
    def __init__(self, vocab_size=50257, d_model=768, num_layers=12, num_heads=12):
        # Embedding
        self.token_embedding = Embedding(vocab_size, d_model)
        self.position_embedding = Embedding(context_length, d_model)

        # Transformer blocks
        self.blocks = [TransformerBlock(d_model, num_heads) for _ in range(num_layers)]

        # Output head
        self.ln_f = LayerNorm(d_model)
        self.lm_head = Linear(d_model, vocab_size)

    def forward(self, token_ids):
        # token_ids: [batch_size, seq_len]
        B, T = token_ids.shape

        # Embeddings
        tok_emb = self.token_embedding(token_ids)  # [B, T, d_model]
        pos = torch.arange(T, device=token_ids.device)
        pos_emb = self.position_embedding(pos)  # [T, d_model]
        x = tok_emb + pos_emb  # [B, T, d_model]

        # Transformer blocks
        for block in self.blocks:
            x = block(x)

        # Final layer norm
        x = self.ln_f(x)  # [B, T, d_model]

        # Project to vocabulary
        logits = self.lm_head(x)  # [B, T, vocab_size]

        return logits
```

### Masked Self-Attention（因果注意力）

```python
def masked_self_attention(Q, K, V):
    """
    Causal (masked) self-attention for autoregressive generation

    Q, K, V: [batch_size, seq_len, d_k]
    """
    B, T, d_k = Q.shape

    # 1. Compute attention scores
    scores = Q @ K.transpose(-2, -1) / np.sqrt(d_k)  # [B, T, T]

    # 2. Apply causal mask (prevent attending to future tokens)
    mask = np.tril(np.ones((T, T)))  # Lower triangular matrix
    mask[mask == 0] = -np.inf
    scores = scores + mask  # [B, T, T]

    # 3. Softmax
    attention_weights = softmax(scores, axis=-1)  # [B, T, T]

    # 4. Weighted sum
    output = attention_weights @ V  # [B, T, d_k]

    return output

# Causal mask 示例：
# Token:  I    love  dogs
# Mask:  [[0,  -inf, -inf],    # "I" 只能看到自己
#         [0,   0,   -inf],    # "love" 可以看到 "I" 和 "love"
#         [0,   0,    0  ]]    # "dogs" 可以看到所有
```

---

## 自回归生成过程

### 采样方法

#### 1. Greedy Decoding

```python
def greedy_decode(model, prompt_ids, max_length=50):
    """
    每次选择概率最高的 token

    model: GPT 模型
    prompt_ids: [1, prompt_len]
    """
    generated = prompt_ids.copy()

    for _ in range(max_length):
        # Forward pass
        logits = model(generated)  # [1, seq_len, vocab_size]

        # 只看最后一个 token 的预测
        next_token_logits = logits[0, -1, :]  # [vocab_size]

        # 选择概率最高的 token
        next_token_id = np.argmax(next_token_logits)

        # 拼接
        generated = np.append(generated, next_token_id)

    return generated

# 问题：总是生成相同的结果，缺乏多样性
```

#### 2. Temperature Sampling

```python
def temperature_sampling(logits, temperature=1.0):
    """
    temperature 控制随机性

    temperature → 0: 接近 greedy（确定性）
    temperature = 1: 标准采样
    temperature > 1: 更随机

    logits: [vocab_size]
    """
    # 缩放 logits
    logits = logits / temperature

    # Softmax
    probs = np.exp(logits) / np.sum(np.exp(logits))

    # 采样
    next_token_id = np.random.choice(len(probs), p=probs)

    return next_token_id

# 示例：
logits = np.array([2.0, 1.0, 0.5])  # 3 个候选 token

# temperature = 0.5 (更确定)
probs_low_temp = softmax(logits / 0.5)
print(probs_low_temp)  # [0.84, 0.11, 0.05]  # 更偏向第一个

# temperature = 2.0 (更随机)
probs_high_temp = softmax(logits / 2.0)
print(probs_high_temp)  # [0.52, 0.28, 0.20]  # 更平均
```

#### 3. Top-K Sampling

```python
def top_k_sampling(logits, k=50):
    """
    只从概率最高的 K 个 token 中采样

    logits: [vocab_size]
    k: 保留的候选数
    """
    # 找出 top-k
    top_k_indices = np.argsort(logits)[-k:]

    # 只保留 top-k 的概率
    top_k_logits = logits[top_k_indices]

    # Softmax
    probs = np.exp(top_k_logits) / np.sum(np.exp(top_k_logits))

    # 采样
    sampled_index = np.random.choice(len(probs), p=probs)
    next_token_id = top_k_indices[sampled_index]

    return next_token_id

# 优点：排除低概率的无意义 token
# 缺点：K 是固定的，不够灵活
```

#### 4. Top-P (Nucleus) Sampling

```python
def top_p_sampling(logits, p=0.9):
    """
    从累积概率 ≥ p 的最小 token 集合中采样

    logits: [vocab_size]
    p: 累积概率阈值
    """
    # 排序（从高到低）
    sorted_indices = np.argsort(logits)[::-1]
    sorted_logits = logits[sorted_indices]

    # Softmax
    probs = np.exp(sorted_logits) / np.sum(np.exp(sorted_logits))

    # 计算累积概率
    cumulative_probs = np.cumsum(probs)

    # 找到累积概率刚好超过 p 的位置
    cutoff_index = np.searchsorted(cumulative_probs, p) + 1

    # 只保留前 cutoff_index 个 token
    top_p_indices = sorted_indices[:cutoff_index]
    top_p_probs = probs[:cutoff_index]

    # 重新归一化
    top_p_probs = top_p_probs / np.sum(top_p_probs)

    # 采样
    sampled_index = np.random.choice(len(top_p_probs), p=top_p_probs)
    next_token_id = top_p_indices[sampled_index]

    return next_token_id

# 优点：动态调整候选集大小
# 缺点：计算稍慢
```

---

## Tokenomics（Token 经济学）

### 上下文窗口

```
模型上下文长度 = 输入 prompt + 生成的 output

GPT-3.5-turbo:     4,096 tokens
GPT-4:             8,192 tokens
GPT-4-32k:        32,768 tokens
GPT-4-turbo:     128,000 tokens
Claude 3:        200,000 tokens
```

### 成本计算

```python
# GPT-4 定价（2024）
input_price_per_1k = 0.03   # $0.03 / 1K input tokens
output_price_per_1k = 0.06  # $0.06 / 1K output tokens

prompt = "请总结以下文档：" + long_document
input_tokens = count_tokens(prompt)  # 假设 5000 tokens

response_tokens = 500  # 模型生成 500 tokens

# 成本
input_cost = (input_tokens / 1000) * input_price_per_1k
output_cost = (response_tokens / 1000) * output_price_per_1k
total_cost = input_cost + output_cost

print(f"输入成本: ${input_cost:.4f}")   # $0.1500
print(f"输出成本: ${output_cost:.4f}")  # $0.0300
print(f"总成本: ${total_cost:.4f}")     # $0.1800
```

### Token 数量与模型性能

```
参数量 = f(d_model, num_layers, num_heads, vocab_size)

GPT-2:
- Small:   117M parameters  (d=768,  L=12, H=12)
- Medium:  345M parameters  (d=1024, L=24, H=16)
- Large:   762M parameters  (d=1280, L=36, H=20)
- XL:      1.5B parameters  (d=1600, L=48, H=25)

GPT-3:
- Ada:     350M
- Babbage: 1.3B
- Curie:   6.7B
- Davinci: 175B  (d=12288, L=96, H=96)

GPT-4:
- 推测 1.7T parameters (1700B)
- Mixture of Experts (MoE) 架构
```

---

## 训练过程

### Pre-training（预训练）

#### 数据准备

```python
# 训练语料：网页、书籍、代码等
corpus = load_massive_dataset()  # 数 TB 级别

# Token 化
tokenizer = GPT2Tokenizer()
tokenized_corpus = []
for text in corpus:
    tokens = tokenizer.encode(text)
    tokenized_corpus.extend(tokens)

# 打包成固定长度
context_length = 2048
training_samples = []
for i in range(0, len(tokenized_corpus) - context_length, context_length):
    sample = tokenized_corpus[i:i+context_length]
    training_samples.append(sample)
```

#### 训练目标：Next Token Prediction

```python
def compute_loss(model, batch):
    """
    自回归语言模型的训练损失

    batch: [batch_size, seq_len] token IDs
    """
    # Forward pass
    logits = model(batch)  # [batch_size, seq_len, vocab_size]

    # Shift for next token prediction
    input_ids = batch[:, :-1]   # [B, T-1]
    target_ids = batch[:, 1:]   # [B, T-1]（右移1位）
    logits = logits[:, :-1, :]  # [B, T-1, V]

    # Cross-entropy loss
    loss = cross_entropy(logits.reshape(-1, vocab_size), target_ids.reshape(-1))

    return loss

# 示例：
# Input:  [The, cat, sits, on, the]
# Target: [cat, sits, on, the, mat]
# 模型学习：给定前面的词，预测下一个词
```

#### 优化器配置

```python
# AdamW optimizer
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=6e-4,           # 学习率
    betas=(0.9, 0.95),
    weight_decay=0.1
)

# Learning rate schedule
def get_lr(iteration, warmup_iters=2000, max_iters=600000):
    # 1. Linear warmup
    if iteration < warmup_iters:
        return (iteration + 1) / warmup_iters * max_lr

    # 2. Cosine decay
    progress = (iteration - warmup_iters) / (max_iters - warmup_iters)
    return min_lr + (max_lr - min_lr) * 0.5 * (1 + np.cos(np.pi * progress))
```

### Fine-tuning（微调）

#### Supervised Fine-Tuning (SFT)

```python
# 指令数据集
instruction_data = [
    {
        "instruction": "将以下文本翻译成英文",
        "input": "我爱机器学习",
        "output": "I love machine learning"
    },
    {
        "instruction": "总结以下文本",
        "input": "机器学习是...",
        "output": "机器学习的核心是..."
    },
    ...
]

# 构造训练样本
def format_instruction(sample):
    prompt = f"### Instruction:\n{sample['instruction']}\n\n"
    if sample['input']:
        prompt += f"### Input:\n{sample['input']}\n\n"
    prompt += "### Response:\n"

    full_text = prompt + sample['output']
    return full_text

# 训练
for sample in instruction_data:
    text = format_instruction(sample)
    tokens = tokenizer.encode(text)

    logits = model(tokens)
    loss = compute_loss(logits, tokens)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

#### RLHF (Reinforcement Learning from Human Feedback)

```python
# 步骤1：训练奖励模型
class RewardModel:
    def __init__(self, base_model):
        self.base_model = base_model
        self.reward_head = Linear(d_model, 1)

    def forward(self, prompt, response):
        # 拼接 prompt 和 response
        full_text = prompt + response
        tokens = tokenizer.encode(full_text)

        # 提取最后一个 token 的隐藏状态
        hidden = self.base_model(tokens)[:, -1, :]

        # 预测奖励分数
        reward = self.reward_head(hidden)  # 标量
        return reward

# 训练数据：人类排序
# 给定 prompt 和两个 response，人类选择哪个更好
training_data = [
    {
        "prompt": "解释量子计算",
        "chosen": "量子计算利用量子比特...",  # 人类偏好
        "rejected": "量子计算是一种..."      # 人类不喜欢
    },
    ...
]

# 损失函数：让 chosen 的奖励 > rejected 的奖励
def reward_loss(prompt, chosen, rejected):
    r_chosen = reward_model(prompt, chosen)
    r_rejected = reward_model(prompt, rejected)

    # Margin ranking loss
    loss = -log_sigmoid(r_chosen - r_rejected)
    return loss

# 步骤2：PPO（Proximal Policy Optimization）
def ppo_step(model, reward_model, prompt):
    # 生成 response
    response = model.generate(prompt)

    # 计算奖励
    reward = reward_model(prompt, response)

    # 计算 PPO loss
    # （复杂，涉及 advantage 估计、KL 散度约束等）
    loss = compute_ppo_loss(model, prompt, response, reward)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

---

## KV Cache（推理加速）

### 问题：重复计算

```python
# 生成过程（无 cache）
prompt = "I love"

# Step 1: 生成 "machine"
tokens = ["I", "love"]
hidden = transformer(tokens)  # 计算 "I" 和 "love" 的表示
next_token = sample(hidden[-1])  # "machine"

# Step 2: 生成 "learning"
tokens = ["I", "love", "machine"]
hidden = transformer(tokens)  # 重复计算 "I" 和 "love" ❌
next_token = sample(hidden[-1])  # "learning"

# 问题：每次都重新计算所有 token 的表示
```

### 解决方案：缓存 K 和 V

```python
class GPTWithKVCache:
    def __init__(self):
        self.kv_cache = {}  # {layer_idx: (K, V)}

    def forward(self, token_ids, use_cache=True):
        B, T = token_ids.shape

        # Embeddings
        x = self.embed(token_ids)  # [B, T, d_model]

        # Transformer blocks
        for i, block in enumerate(self.blocks):
            if use_cache and i in self.kv_cache:
                # 使用缓存的 K, V
                cached_K, cached_V = self.kv_cache[i]

                # 只计算新 token 的 Q, K, V
                Q_new = x @ block.W_q  # [B, 1, d_model]（假设只有1个新token）
                K_new = x @ block.W_k
                V_new = x @ block.W_v

                # 拼接缓存
                K = torch.cat([cached_K, K_new], dim=1)  # [B, T_total, d_model]
                V = torch.cat([cached_V, V_new], dim=1)

                # 更新缓存
                self.kv_cache[i] = (K, V)

                # 计算 attention（只计算新 token）
                x = attention(Q_new, K, V)

            else:
                # 正常计算（首次）
                Q = x @ block.W_q
                K = x @ block.W_k
                V = x @ block.W_v

                self.kv_cache[i] = (K, V)

                x = attention(Q, K, V)

        return x

# 加速效果：
# 无 cache: O(T^2) 每步
# 有 cache: O(T) 每步（T 是当前总长度）
```

---

## Scaling Laws

### Kaplan et al. (2020) 的发现

```
模型性能 L（Loss）与三个因素的幂律关系：

L(N, D, C) = A / N^α + B / D^β + C / C^γ

N = 参数量（Number of parameters）
D = 数据集大小（Dataset size）
C = 计算量（Compute budget）

α ≈ 0.076
β ≈ 0.095
γ ≈ 0.050

关键结论：
1. 参数量最重要（α 最大）
2. 数据和计算量也很重要
3. 三者需要平衡扩展
```

### Chinchilla 定律（2022）

```
最优模型大小与训练 token 数应该成比例：

N_optimal(C) ∝ C^(α/(α+β))
D_optimal(C) ∝ C^(β/(α+β))

其中 α ≈ β ≈ 0.5

结论：
- GPT-3 (175B) 训练数据太少（300B tokens）
- 应该用 80B 参数 + 1.4T tokens（Chinchilla）
- Llama-2 遵循了这个规律
```

---

## 提示词工程（Prompt Engineering）

### Few-Shot Prompting

```python
prompt = """
Translate English to French:

sea otter => loutre de mer
peppermint => menthe poivrée
plush girafe => girafe peluche
cheese =>
"""

# 模型补全：fromage
```

### Chain-of-Thought (CoT)

```python
# 标准提示
prompt = "Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?"

# CoT 提示
prompt = """
Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?

Let's think step by step:
1. Roger started with 5 balls.
2. He bought 2 cans of 3 balls each, so 2 × 3 = 6 balls.
3. Total = 5 + 6 = 11 balls.

Therefore, Roger has 11 tennis balls.
"""

# 效果：显著提升数学推理能力
```

### ReAct（Reasoning + Acting）

```python
prompt = """
Question: What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?

Thought 1: I need to search Colorado orogeny, find the area that the eastern sector extends into, then find the elevation range of that area.
Action 1: Search[Colorado orogeny]
Observation 1: The Colorado orogeny was an episode of mountain building...

Thought 2: It does not mention the eastern sector. I need to search eastern sector.
Action 2: Lookup[eastern sector]
Observation 2: (Result 1 / 1) The eastern sector extends into the High Plains...

Thought 3: The eastern sector extends into High Plains. I need to search High Plains and find its elevation range.
Action 3: Search[High Plains]
Observation 3: High Plains refers to one of two distinct land regions: ...

Thought 4: I need to instead search High Plains (United States).
Action 4: Search[High Plains (United States)]
Observation 5: The High Plains are a subregion of the Great Plains... elevations range from 1,800 to 7,000 ft...

Thought 5: High Plains have an elevation range of 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
Action 5: Finish[1,800 to 7,000 ft]
"""
```

---

## 量化（Quantization）

### FP16 vs INT8

```python
# FP32（全精度）
weight_fp32 = 0.123456789  # 4 bytes

# FP16（半精度）
weight_fp16 = 0.1235  # 2 bytes (精度下降)

# INT8（8位整数）
# 量化公式：
# w_int8 = round((w_fp32 - min) / (max - min) * 255)
# w_fp32 = w_int8 / 255 * (max - min) + min

def quantize_to_int8(weights):
    w_min = weights.min()
    w_max = weights.max()

    # 映射到 [0, 255]
    scale = (w_max - w_min) / 255
    zero_point = -round(w_min / scale)

    weights_int8 = np.round(weights / scale + zero_point).astype(np.int8)

    return weights_int8, scale, zero_point

# 内存节省：
# FP32: 175B × 4 bytes = 700 GB
# INT8: 175B × 1 byte = 175 GB（4倍减少）
```

### GPTQ / AWQ（高级量化）

```python
# GPTQ: 逐层量化 + 最小化重构误差
# AWQ: 保护重要的激活值权重

# Llama-2-7B 量化：
# FP16: 14 GB
# GPTQ 4-bit: 3.9 GB
# AWQ 4-bit: 4.2 GB（更高质量）
```

---

## 推理优化

### Flash Attention

```python
# 标准 Attention: O(N^2) 内存
def standard_attention(Q, K, V):
    # [B, N, d] @ [B, d, N] = [B, N, N]（存储整个矩阵）
    scores = Q @ K.T
    attention = softmax(scores / sqrt(d_k))
    output = attention @ V
    return output

# Flash Attention: O(N) 内存
# 核心思想：分块计算，不存储完整的 attention 矩阵
def flash_attention(Q, K, V, block_size=128):
    N, d = Q.shape
    num_blocks = N // block_size

    output = np.zeros_like(Q)
    for i in range(num_blocks):
        # 只计算一个 block 的 attention
        Q_block = Q[i*block_size:(i+1)*block_size]
        scores_block = Q_block @ K.T  # 只存储部分
        attention_block = softmax(scores_block / sqrt(d_k))
        output_block = attention_block @ V
        output[i*block_size:(i+1)*block_size] = output_block

    return output

# 加速：2-4 倍（特别是长上下文）
```

### Speculative Decoding（推测解码）

```python
# 使用小模型（快）生成草稿，大模型（准）验证

def speculative_decoding(large_model, small_model, prompt, k=4):
    tokens = prompt.copy()

    while len(tokens) < max_length:
        # 小模型生成 k 个 tokens（快）
        draft_tokens = small_model.generate(tokens, num_tokens=k)

        # 大模型并行验证
        large_logits = large_model(tokens + draft_tokens)

        # 检查每个 draft token 是否被大模型接受
        accepted = 0
        for i in range(k):
            large_prob = softmax(large_logits[len(tokens) + i])[draft_tokens[i]]
            small_prob = ...  # 小模型的概率

            # 接受/拒绝
            if random.random() < large_prob / small_prob:
                tokens.append(draft_tokens[i])
                accepted += 1
            else:
                # 拒绝，从大模型重新采样
                new_token = sample(large_logits[len(tokens)])
                tokens.append(new_token)
                break

    return tokens

# 加速：1.5-2 倍（无精度损失）
```
