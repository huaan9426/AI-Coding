# LLM 大语言模型学习笔记

> 理解 AI 的"大脑" - 用最简单的话讲清楚

---

## 📋 目录

1. [LLM 是什么](#1-llm-是什么)
2. [常见的 LLM 模型](#2-常见的-llm-模型)
3. [LLM 的核心参数](#3-llm-的核心参数)
4. [如何调用 LLM](#4-如何调用-llm)
5. [提示词工程](#5-提示词工程)
6. [LLM 的输入输出](#6-llm-的输入输出)
7. [对话 vs 补全](#7-对话-vs-补全)
8. [流式输出](#8-流式输出)
9. [Token 和计费](#9-token-和计费)
10. [常见问题](#10-常见问题)

---

## 1. LLM 是什么

### 一句话

**LLM 就是一个超级聪明的"文字接龙"机器，能理解你说的话并给出回答。**

### 全称

**LLM = Large Language Model（大语言模型）**

### 通俗理解

```
你输入：什么是AI？
LLM 思考：根据训练数据，这个问题应该这样回答...
LLM 输出：AI 是人工智能，指让机器模拟人类智能的技术...
```

**就像：**
- 一个读过全网所有书的超级学霸
- 你问它什么，它都能给你答案
- 但它只是"预测"下一个词应该是什么，不是真正"理解"

---

## 2. 常见的 LLM 模型

### 2.1 OpenAI 系列（最流行）

#### GPT-4
```python
# 最强大，最贵，最聪明
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")
```

**特点：**
- ✅ 最聪明，理解能力最强
- ✅ 能处理复杂任务（写代码、分析文档、推理）
- ❌ 最贵（大约是 GPT-3.5 的 15-30 倍）
- ❌ 速度较慢

**适用场景：**
- 复杂的代码生成
- 深度分析和推理
- 高质量内容创作
- 重要的决策支持

---

#### GPT-3.5-turbo
```python
# 性价比之王
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo")
```

**特点：**
- ✅ 便宜（是 GPT-4 的 1/15 到 1/30）
- ✅ 速度快
- ✅ 日常任务足够用
- ⚠️ 复杂推理能力弱一些

**适用场景：**
- 日常问答
- 简单的文本处理
- 对话机器人
- 快速原型开发

---

#### GPT-4o（新一代）
```python
# GPT-4 的快速版
llm = ChatOpenAI(model="gpt-4o")
```

**特点：**
- ✅ GPT-4 级别的智能
- ✅ 比 GPT-4 快 2 倍
- ✅ 比 GPT-4 便宜一半
- ✅ 支持图片、语音（多模态）

**适用场景：**
- 需要 GPT-4 的智能但预算有限
- 需要快速响应的应用
- 图文混合处理

---

### 2.2 其他流行模型

#### Claude（Anthropic）
```python
# OpenAI 的竞争对手，很强
from langchain.chat_models import ChatAnthropic

llm = ChatAnthropic(model="claude-3-opus")
```

**特点：**
- ✅ 长文档理解能力强（最多 200k token）
- ✅ 逻辑推理能力好
- ✅ 更注重安全性
- ⚠️ 国内访问可能受限

---

#### 本地模型（Ollama）
```python
# 在你自己电脑上运行，不需要 API 密钥
from langchain.llms import Ollama

llm = Ollama(model="llama3")
```

**特点：**
- ✅ 完全免费
- ✅ 数据隐私（不上传到云端）
- ✅ 离线可用
- ❌ 需要好的电脑配置
- ❌ 智能程度不如 GPT-4

**常用本地模型：**
- `llama3` - Meta 开源，性能好
- `mistral` - 欧洲开发，速度快
- `qwen` - 阿里通义千问，中文好

---

### 2.3 国产模型

#### 通义千问（阿里）
```python
from langchain.chat_models import ChatTongyi

llm = ChatTongyi(model="qwen-turbo")
```

#### 文心一言（百度）
```python
# 百度的大模型
llm = ChatBaiduQianfan()
```

#### 智谱 GLM
```python
# 清华系大模型
from langchain.chat_models import ChatGLM

llm = ChatGLM()
```

**国产模型优势：**
- ✅ 中文理解更好
- ✅ 国内访问快
- ✅ 价格便宜
- ⚠️ 英文和编程能力略弱

---

## 3. LLM 的核心参数

### 3.1 temperature（温度）

**一句话：** 控制 AI 回答的"随机性"和"创造性"。

```python
# 保守模式（适合需要准确答案的场景）
llm = ChatOpenAI(temperature=0)

# 中等创造力
llm = ChatOpenAI(temperature=0.7)

# 高创造力（适合写作、头脑风暴）
llm = ChatOpenAI(temperature=1.0)
```

**取值范围：** 0.0 到 2.0

**形象理解：**
```
问题：推荐一部电影

temperature = 0（保守）：
→ 每次都推荐《肖申克的救赎》（经典、安全的选择）

temperature = 0.7（平衡）：
→ 可能推荐《盗梦空间》、《星际穿越》（稍微冒险）

temperature = 1.5（疯狂）：
→ 可能推荐冷门小众电影（有创意但可能不靠谱）
```

**实际使用建议：**
- 📝 **数学题、翻译、数据提取** → `0` 或 `0.1`
- 💬 **日常对话、问答** → `0.5` 到 `0.7`
- ✍️ **创意写作、头脑风暴** → `0.8` 到 `1.2`

---

### 3.2 max_tokens（最大输出长度）

**一句话：** 限制 AI 回答的最大字数。

```python
# 短回答（适合简单问答）
llm = ChatOpenAI(max_tokens=100)

# 中等长度（适合一般对话）
llm = ChatOpenAI(max_tokens=1000)

# 长文章（适合写作、详细分析）
llm = ChatOpenAI(max_tokens=4000)
```

**理解：**
- 1 个 token ≈ 0.75 个英文单词
- 1 个中文字 ≈ 2-3 个 token
- `max_tokens=100` ≈ 约 30-50 个中文字

**实际例子：**
```python
# 只要简短答案
llm = ChatOpenAI(max_tokens=50)
response = llm("什么是AI？")
# 输出："AI是人工智能，让机器模拟人类思维的技术。"

# 要详细解释
llm = ChatOpenAI(max_tokens=500)
response = llm("什么是AI？")
# 输出：详细的多段解释...
```

---

### 3.3 model（模型名称）

**一句话：** 选择用哪个 AI 大脑。

```python
# 不同的模型
llm_cheap = ChatOpenAI(model="gpt-3.5-turbo")  # 便宜快速
llm_smart = ChatOpenAI(model="gpt-4")          # 聪明但贵
llm_balanced = ChatOpenAI(model="gpt-4o")      # 平衡选择
```

---

### 3.4 其他重要参数

#### top_p（核采样）
```python
# 控制词汇多样性
llm = ChatOpenAI(top_p=0.9)
```
- 范围：0.0 到 1.0
- 类似 temperature，但工作方式不同
- 通常和 temperature 只用一个

#### presence_penalty（存在惩罚）
```python
# 鼓励 AI 谈论新话题
llm = ChatOpenAI(presence_penalty=0.6)
```
- 范围：-2.0 到 2.0
- 正值：鼓励谈新内容，避免重复
- 负值：允许重复同一话题

#### frequency_penalty（频率惩罚）
```python
# 减少重复用词
llm = ChatOpenAI(frequency_penalty=0.5)
```
- 范围：-2.0 到 2.0
- 正值：避免重复使用相同词汇
- 负值：允许重复

---

## 4. 如何调用 LLM

### 4.1 方式1：直接调用（最简单）

```python
from langchain.chat_models import ChatOpenAI

# 创建 LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7
)

# 直接提问
response = llm("你好，请介绍一下自己")
print(response)
```

**输出：**
```
你好！我是 ChatGPT，一个由 OpenAI 开发的人工智能助手...
```

---

### 4.2 方式2：对话格式（推荐）

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

llm = ChatOpenAI(model="gpt-3.5-turbo")

# 构建对话
messages = [
    SystemMessage(content="你是一个友好的 Python 老师"),
    HumanMessage(content="什么是变量？")
]

# 调用
response = llm(messages)
print(response.content)
```

**消息类型：**
- **SystemMessage** - 系统指令（设定 AI 的角色和行为）
- **HumanMessage** - 用户说的话
- **AIMessage** - AI 的回复（用于多轮对话）

---

### 4.3 方式3：使用链（LangChain）

```python
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# 创建提示词模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}"),
    ("human", "{question}")
])

# 创建链
llm = ChatOpenAI(model="gpt-3.5-turbo")
chain = LLMChain(llm=llm, prompt=prompt)

# 调用
result = chain.run(role="Python老师", question="什么是函数？")
print(result)
```

---

## 5. 提示词工程

### 一句话

**提示词就是"问问题的艺术" - 问得好，答案才好。**

### 5.1 基本原则

#### 原则1：清晰具体

❌ **不好的提示词：**
```python
"写个代码"
```

✅ **好的提示词：**
```python
"用 Python 写一个函数，接收一个列表，返回列表中的最大值。要有注释。"
```

---

#### 原则2：给 AI 设定角色

❌ **没有角色：**
```python
"什么是机器学习？"
```

✅ **有角色：**
```python
"""
你是一个资深的机器学习工程师，用简单的话向初学者解释概念。

问题：什么是机器学习？
"""
```

---

#### 原则3：提供示例（Few-shot）

```python
prompt = """
将以下句子翻译成英文：

示例1：
中文：你好
英文：Hello

示例2：
中文：谢谢
英文：Thank you

现在翻译：
中文：早上好
英文：
"""
```

---

#### 原则4：分步骤引导

❌ **一次性问：**
```python
"分析这份报告并给出建议"
```

✅ **分步骤：**
```python
"""
请按以下步骤分析这份报告：
1. 总结报告的主要内容
2. 列出报告中的关键数据
3. 指出潜在问题
4. 给出改进建议

报告内容：...
"""
```

---

### 5.2 提示词模板

#### 模板1：角色 + 任务 + 要求
```python
prompt = """
角色：你是一个专业的 Python 代码审查员

任务：审查下面的代码

要求：
1. 指出代码中的问题
2. 解释为什么这是问题
3. 提供改进建议

代码：
{code}
"""
```

#### 模板2：背景 + 问题 + 格式
```python
prompt = """
背景：我正在开发一个 PDF 聊天机器人

问题：如何高效地处理大型 PDF 文件？

请按以下格式回答：
- 方案名称
- 实现步骤
- 优缺点
"""
```

#### 模板3：思维链（Chain of Thought）
```python
prompt = """
问题：一个商店第一天卖了 20 个苹果，第二天卖了第一天的 3 倍，第三天卖了第二天的一半。总共卖了多少个？

请按以下格式思考：
第一步：...
第二步：...
第三步：...
最终答案：...
"""
```

---

### 5.3 实际案例

#### 案例1：代码生成
```python
prompt = """
角色：你是一个 Python 专家

任务：写一个函数

要求：
- 函数名：load_pdf
- 功能：读取 PDF 文件并返回文本内容
- 参数：file_path (字符串)
- 返回：文本内容（字符串）
- 使用 PyPDF2 库
- 包含错误处理
- 添加中文注释

请直接给出代码，不要解释。
"""
```

#### 案例2：文档分析
```python
prompt = """
角色：你是一个文档分析助手

任务：阅读下面的文档并提取关键信息

文档：{document_content}

请按以下 JSON 格式输出：
{{
  "主题": "...",
  "关键人物": ["...", "..."],
  "重要日期": ["...", "..."],
  "核心观点": ["...", "..."]
}}
"""
```

#### 案例3：对话机器人
```python
system_prompt = """
你是一个友好的客服机器人，名字叫小智。

你的职责：
1. 回答用户关于产品的问题
2. 保持礼貌和专业
3. 如果不知道答案，诚实告知并建议联系人工客服
4. 每次回复不超过 100 字

注意：
- 不要提供虚假信息
- 不要讨论与产品无关的话题
"""
```

---

## 6. LLM 的输入输出

### 6.1 输入格式

#### 纯文本输入
```python
llm("什么是Python？")
```

#### 消息列表输入
```python
messages = [
    SystemMessage(content="你是助手"),
    HumanMessage(content="你好"),
    AIMessage(content="你好！有什么可以帮你？"),
    HumanMessage(content="介绍一下Python")
]
llm(messages)
```

#### 结构化输入（高级）
```python
from langchain.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是{role}"),
    ("human", "问题：{question}\n背景：{context}")
])

# 使用时填入变量
prompt.format(
    role="老师",
    question="什么是变量？",
    context="这是Python入门课"
)
```

---

### 6.2 输出格式

#### 普通文本输出
```python
response = llm("你好")
print(response.content)
# 输出：你好！有什么可以帮助你的吗？
```

#### 获取完整信息
```python
response = llm("你好")

print(response.content)           # 回复内容
print(response.response_metadata) # 元数据（token数等）
```

#### 结构化输出（让 AI 返回 JSON）
```python
prompt = """
分析这段文本的情感："{text}"

请以 JSON 格式返回：
{{
  "情感": "正面/负面/中性",
  "置信度": 0.0-1.0,
  "关键词": ["词1", "词2"]
}}
"""

response = llm(prompt)
import json
result = json.loads(response.content)
print(result["情感"])
```

---

## 7. 对话 vs 补全

### 7.1 对话模型（Chat Models）

**特点：** 专门用于对话，理解角色和上下文

```python
from langchain.chat_models import ChatOpenAI

chat = ChatOpenAI(model="gpt-3.5-turbo")

messages = [
    SystemMessage(content="你是助手"),
    HumanMessage(content="我叫张三"),
    AIMessage(content="你好张三！"),
    HumanMessage(content="我叫什么？")
]

response = chat(messages)
# AI 会回答"张三"，因为它记得上文
```

**适用场景：**
- ✅ 聊天机器人
- ✅ 问答系统
- ✅ 需要多轮对话的应用

---

### 7.2 补全模型（Completion Models）

**特点：** 简单的"文字接龙"，给定开头，补全后续

```python
from langchain.llms import OpenAI

llm = OpenAI(model="gpt-3.5-turbo-instruct")

# 给一个开头
prompt = "今天天气真好，我决定"

response = llm(prompt)
# 可能输出："去公园散步"
```

**适用场景：**
- ✅ 文本生成
- ✅ 代码补全
- ✅ 简单的单次调用

---

### 对比

| 特性 | 对话模型 | 补全模型 |
|------|---------|---------|
| 输入格式 | 消息列表 | 纯文本 |
| 多轮对话 | ✅ 支持 | ❌ 不支持 |
| 角色设定 | ✅ 支持 | ⚠️ 有限 |
| 价格 | 稍贵 | 稍便宜 |
| 推荐用途 | 对话应用 | 文本生成 |

**现在的趋势：** 对话模型更流行，功能更强大，推荐使用。

---

## 8. 流式输出

### 一句话

**让 AI 边想边说，不用等它全想完再说。**

### 为什么需要流式输出？

**非流式（普通模式）：**
```
用户：写一篇 1000 字的文章
AI：（思考 10 秒...）
AI：好了，这是完整文章...（一次性输出）
```

**流式：**
```
用户：写一篇 1000 字的文章
AI：关于...（立即开始）
AI：这个话题...（继续）
AI：我们可以...（实时输出）
```

**优势：**
- ✅ 用户体验好（不用等）
- ✅ 感觉更自然（像真人打字）
- ✅ 长文本不会超时

---

### 如何使用流式输出

#### 基本流式输出
```python
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# 启用流式输出
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

# 调用（会边生成边打印）
response = llm("写一首关于春天的诗")
```

#### 自定义流式处理
```python
from langchain.callbacks.base import BaseCallbackHandler

class MyStreamHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs):
        # 每产生一个新 token 就调用这里
        print(token, end="", flush=True)

llm = ChatOpenAI(
    streaming=True,
    callbacks=[MyStreamHandler()]
)

response = llm("讲个笑话")
# 会一个字一个字地输出
```

#### Streamlit 中的流式输出
```python
import streamlit as st
from langchain.chat_models import ChatOpenAI   # 能跟 OpenAI 聊天的工具

st.title("AI 聊天")                            # 页面标题

user_input = st.text_input("你想问什么？")      # 输入框，用户打字的地方

if user_input:                                 # 用户一按回车，就执行下面代码
    llm = ChatOpenAI(streaming=True)           # 重要！告诉 OpenAI：别一次给我全部答案，要一点一点给我！

    with st.chat_message("assistant"):         # 在页面上显示“助手”头像的气泡
        message_placeholder = st.empty()       # 先占个坑（一个空的文字区域），以后要往这里疯狂写字
        full_response = ""                     # 用来攒完整答案的空字符串

        # 关键来了！OpenAI 现在不是一次给完整答案，而是像下饺子一样一个一个给小块！
        for chunk in llm.stream(user_input):
            full_response += chunk.content     # 把收到的这一小块拼到 total 答案里
            message_placeholder.write(full_response + "▌")  # 立刻显示目前收到的内容，后面加个闪烁光标 ▌ 假装在打字

        # 全部收完了，把光标去掉，显示最终完整答案
        message_placeholder.write(full_response)
```

---

## 9. Token 和计费

### 9.1 什么是 Token

**一句话：** Token 是 AI 处理文本的最小单位，类似"字"。

**理解：**
- 1 个英文单词 ≈ 1-2 个 token
- 1 个中文字 ≈ 2-3 个 token
- 标点符号 ≈ 1 个 token

**例子：**
```
"你好世界" ≈ 6-8 个 token
"Hello World" ≈ 2 个 token
```

### 9.2 如何计算 Token

```python
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI()

# 方法1：用官方工具
import tiktoken
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
tokens = encoding.encode("你好世界")
print(f"Token 数量: {len(tokens)}")

# 方法2：估算
text = "你的文本内容"
estimated_tokens = len(text) * 2.5  # 中文粗略估算
```

### 9.3 计费方式

**公式：**
```
总费用 = (输入 token 数 × 输入单价) + (输出 token 数 × 输出单价)
```

**GPT-3.5-turbo 价格（2025年参考）：**
- 输入：$0.0005 / 1K tokens（约 ¥0.0035）
- 输出：$0.0015 / 1K tokens（约 ¥0.010）

**GPT-4 价格：**
- 输入：$0.03 / 1K tokens（约 ¥0.21）
- 输出：$0.06 / 1K tokens（约 ¥0.42）

**实际例子：**
```python
# 场景：用 GPT-3.5 问答
输入："请用 500 字介绍 Python"（约 1500 tokens）
输出：500 字回答（约 1500 tokens）

费用计算：
输入费用 = 1.5K × $0.0005 = $0.00075
输出费用 = 1.5K × $0.0015 = $0.00225
总费用 = $0.003（约 ¥0.02）

结论：一次问答约 2 分钱
```

### 9.4 节省成本技巧

#### 技巧1：减少不必要的上下文
❌ **不好：**
```python
# 每次都发送全部历史
messages = [
    所有历史对话...（可能 10000 tokens）
    最新问题（100 tokens）
]
```

✅ **好：**
```python
# 只保留最近 5 轮对话
messages = recent_messages[-10:]  # 只保留 10 条消息
```

#### 技巧2：使用便宜的模型
```python
# 简单任务用 3.5，复杂任务用 4
if task_type == "simple":
    llm = ChatOpenAI(model="gpt-3.5-turbo")  # 便宜
else:
    llm = ChatOpenAI(model="gpt-4")  # 聪明但贵
```

#### 技巧3：限制输出长度
```python
# 不需要长回答时，限制 token
llm = ChatOpenAI(max_tokens=100)  # 最多 100 tokens
```

#### 技巧4：缓存常见问题
```python
# 用字典缓存常见回答
cache = {}

def ask_with_cache(question):
    if question in cache:
        return cache[question]  # 直接返回，不调用 API

    response = llm(question)
    cache[question] = response
    return response
```

---

## 10. 常见问题

### Q1: 为什么 AI 有时候"胡说八道"？

**原因：** LLM 只是预测下一个词，不是查数据库。它会"编造"听起来合理的答案。

**解决方法：**
```python
# 1. 降低 temperature（减少随机性）
llm = ChatOpenAI(temperature=0)

# 2. 要求 AI 说"不知道"
prompt = """
如果你不确定答案，请说"我不知道"，不要编造。

问题：{question}
"""

# 3. 使用 RAG（检索增强生成）
# 让 AI 基于你的文档回答，而不是凭空想象
```

---

### Q2: 如何让 AI 记住之前的对话？

**方法1：手动传递历史**
```python
from langchain.schema import HumanMessage, AIMessage

# 保存对话历史
history = []

def chat(user_input):
    # 添加用户消息
    history.append(HumanMessage(content=user_input))

    # 调用 LLM（传入全部历史）
    response = llm(history)

    # 保存 AI 回复
    history.append(AIMessage(content=response.content))

    return response.content

# 使用
chat("我叫张三")
chat("我叫什么？")  # AI 会回答"张三"
```

**方法2：使用 LangChain 的 Memory**
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

# 对话会自动记住
conversation.run("我叫张三")
conversation.run("我叫什么？")  # 自动记得
```

---

### Q3: 如何处理超长文本？

**问题：** GPT-3.5 最多 4096 tokens，GPT-4 最多 8192 tokens（或更多），超过会报错。

**解决方法：**

#### 方法1：文本切分
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,  # 每块 2000 字符
    chunk_overlap=200  # 重叠 200 字符
)

chunks = splitter.split_text(long_text)

# 分别处理每块
for chunk in chunks:
    response = llm(f"总结这段文字：{chunk}")
```

#### 方法2：使用支持长文本的模型
```python
# Claude 支持 200K tokens
from langchain.chat_models import ChatAnthropic
llm = ChatAnthropic(model="claude-3-opus")

# GPT-4-turbo 支持 128K tokens
llm = ChatOpenAI(model="gpt-4-turbo")
```

#### 方法3：先总结再分析
```python
# 第一步：分块总结
summaries = []
for chunk in chunks:
    summary = llm(f"总结这段话：{chunk}")
    summaries.append(summary)

# 第二步：总结所有小总结
final_summary = llm(f"总结这些内容：{summaries}")
```

---

### Q4: 如何让输出格式固定（JSON、表格等）？

**方法1：在提示词中明确要求**
```python
prompt = """
分析这段文本的情感："{text}"

请严格按照以下 JSON 格式输出，不要有任何其他内容：
{{
  "情感": "正面/负面/中性",
  "分数": 0-100
}}
"""
```

**方法2：使用输出解析器**
```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# 定义输出结构
class SentimentAnalysis(BaseModel):
    sentiment: str = Field(description="正面/负面/中性")
    score: int = Field(description="情感分数 0-100")

# 创建解析器
parser = PydanticOutputParser(pydantic_object=SentimentAnalysis)

# 添加到提示词
prompt = f"""
分析情感：{text}

{parser.get_format_instructions()}
"""

response = llm(prompt)
result = parser.parse(response.content)  # 自动解析为对象
print(result.sentiment)
print(result.score)
```

---

### Q5: 如何让 AI 基于我的文档回答问题？

**这就是 RAG（检索增强生成）！**

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA

# 1. 加载文档
loader = PyPDFLoader("report.pdf")
documents = loader.load()

# 2. 切分
splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
chunks = splitter.split_documents(documents)

# 3. 向量化并存储
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. 创建问答链
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0),
    retriever=vectorstore.as_retriever()
)

# 5. 提问（AI 会基于你的文档回答）
answer = qa_chain.run("这份报告的主要结论是什么？")
```

**流程：**
```
你的问题 → 搜索相关文档片段 → 把片段给 AI → AI 基于片段回答
```

---

## 总结

### 必须掌握的概念

- ✅ **LLM 是什么** - 文字接龙机器，预测下一个词
- ✅ **常用模型** - GPT-3.5（便宜）、GPT-4（聪明）
- ✅ **核心参数** - temperature（创造性）、max_tokens（长度）
- ✅ **提示词工程** - 清晰、具体、有角色、有示例
- ✅ **对话格式** - SystemMessage、HumanMessage
- ✅ **Token 计费** - 输入 + 输出都要钱

### 学习路径

**第1周：基础使用**
- [ ] 调用 GPT-3.5 问答
- [ ] 理解 temperature 参数
- [ ] 学会写好的提示词

**第2周：进阶功能**
- [ ] 多轮对话
- [ ] 流式输出
- [ ] 角色设定

**第3周：实战应用**
- [ ] 文档问答（RAG）
- [ ] 代码生成
- [ ] 聊天机器人

### 避坑指南

1. **不要过度依赖 AI 的"事实"** - 它会编造
2. **先用 3.5 测试，再用 4 优化** - 省钱
3. **提示词越清晰，答案越好** - 不要偷懒
4. **长对话要控制历史长度** - 避免超 token 限制
5. **重要任务降低 temperature** - 减少随机性

---

**笔记创建时间：** 2025-11-20
**用途：** AI 应用开发 - LLM 基础
**建议：** 配合 LangChain 笔记一起看，理解如何实际使用
