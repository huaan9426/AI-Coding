# PDF 聊天机器人

基于 RAG（检索增强生成）技术的智能 PDF 文档问答系统。

## 核心功能

- ✅ 自动加载和处理 PDF 文档
- ✅ 智能文档分块和向量化
- ✅ 基于语义搜索的精准检索（Chroma）
- ✅ 上下文相关的准确答案生成
- ✅ **多轮对话记忆功能**（新增）

## 技术栈

- **LangChain** - AI 应用开发框架
- **OpenAI GPT-3.5** - 大语言模型
- **Chroma** - 向量数据库
- **PyPDF** - PDF 文档处理

## 快速开始

### 1. 安装依赖

```bash
# 使用 Poetry 安装
poetry install
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 OpenAI API Key
# OPENAI_API_KEY=sk-your-api-key-here
```

### 3. 运行程序

```bash
# 方式1：使用 Poetry
poetry run python -m pdf_chatbot.main

# 方式2：激活虚拟环境后运行
poetry shell
python -m pdf_chatbot.main
```

## 使用说明

### 首次运行

1. 运行程序后，会提示输入 PDF 文件路径
2. 程序会自动处理 PDF（加载 → 分块 → 向量化）
3. 向量数据库保存在 `./chroma_db` 目录
4. 进入提问环节

### 后续运行

- 程序会自动加载已有的向量数据库
- 直接进入提问环节

### 对话命令

在启用记忆功能时，支持以下命令：

```
❓ 你的问题: history        # 查看对话历史
❓ 你的问题: clear          # 清空对话历史
❓ 你的问题: quit/exit      # 退出程序
```

### 使用示例

```
❓ 你的问题: 这份文档的主要内容是什么？

🔍 正在搜索相关文档...

💡 答案: 这份文档主要介绍了...

📚 参考来源:
  1. report.pdf (第1页)
     文档内容摘要...
  2. report.pdf (第3页)
     相关数据...
```

## 项目结构

```
pdf-chatbot/
├── src/
│   └── pdf_chatbot/
│       ├── __init__.py          # 模块导出
│       ├── config.py            # 配置管理
│       ├── document_loader.py   # 文档加载和分块
│       ├── vector_store.py      # 向量数据库管理
│       ├── qa_chain.py          # 问答链（支持记忆）
│       └── main.py              # 命令行入口
├── .env.example                 # 配置模板
├── pyproject.toml               # 项目配置
└── README.md                    # 项目文档
```

## 配置说明

在 `.env` 文件中可以调整以下配置：

```bash
# 模型配置
MODEL_NAME=gpt-3.5-turbo        # 可改为 gpt-4
TEMPERATURE=0.0                 # 0-2，越低越精确

# Embedding 模型
EMBEDDING_MODEL=text-embedding-3-small

# 文档分块
CHUNK_SIZE=1000                 # 单个文本块大小
CHUNK_OVERLAP=200               # 块之间重叠大小

# 对话记忆
ENABLE_MEMORY=true              # true=启用记忆，false=禁用记忆
```

## 对话记忆功能

### 功能说明

启用记忆功能后，AI 可以记住之前的对话上下文，支持连续多轮对话：

**示例场景：**
```
❓ 第1轮：这份文档讲了什么？
💡 AI：这份文档主要介绍了项目架构...

❓ 第2轮：那它的优势有哪些？（AI 记得"它"指的是项目架构）
💡 AI：项目架构的优势包括...

❓ 第3轮：有具体的数据支撑吗？
💡 AI：根据文档第5页的数据显示...
```

### 配置选项

在 `.env` 文件中设置：

```bash
# 启用记忆（默认）
ENABLE_MEMORY=true

# 禁用记忆（每次提问都是独立的）
ENABLE_MEMORY=false
```

### 管理命令

| 命令 | 说明 |
|------|------|
| `history` | 显示完整对话历史记录 |
| `clear` | 清空当前对话历史 |

## 常见问题

### Q: 如何重新加载文档？

删除 `chroma_db` 目录后重新运行程序：

```bash
rm -rf chroma_db
poetry run python -m pdf_chatbot.main
```

### Q: 支持哪些文件格式？

目前仅支持 PDF 文件。后续可扩展 Word、TXT 等格式。

### Q: 如何提高回答质量？

1. 使用更强的模型（GPT-4）
2. 调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP`
3. 降低 `TEMPERATURE`（提高精确性）

### Q: 使用成本如何？

- GPT-3.5-turbo：约 $0.02/千次提问
- Embedding：约 $0.001/1000 文本块

### Q: 对话记忆会影响性能吗？

- 记忆功能对性能影响极小
- 只会略微增加 token 消耗（需要发送历史对话）
- 可通过 `clear` 命令随时清空历史节省成本

## 开发计划

- [ ] 支持更多文档格式（Word、TXT、Markdown）
- [ ] Web UI 界面（Streamlit）
- [ ] 多文档管理
- [ ] 导出对话记录
- [ ] 自定义提示词模板

## 许可证

MIT License

## 作者

huaan
