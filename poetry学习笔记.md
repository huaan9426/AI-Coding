# Poetry 学习笔记

> 我的 AI 应用开发学习笔记 - Poetry 包管理工具

---

## Poetry 是什么？

Poetry 就是一个**管理 Python 项目的工具**，可以理解为"项目管家"。

**用人话说：**
- 就像你手机上的应用商店，帮你安装、删除、更新软件
- 但它管理的是 Python 代码需要的各种"零件"（库/包）
- 还能确保每个项目的"零件"不互相干扰

**版本：** Poetry 2.2.1 (已安装)

---

## 为什么需要 Poetry？

### 问题1：传统方式很乱

**以前用 pip 的痛点：**

```bash
# 你在项目A安装了某个库
pip install langchain

# 结果影响了整个电脑的Python环境
# 项目B也被迫用同一个版本，可能会冲突
```

**手动管理依赖很麻烦：**
```
requirements.txt  # 需要手动维护
- 版本号经常忘记写
- 不知道哪个库依赖哪个库
- 换台电脑重装一堆问题
```

### 问题2：虚拟环境还要自己创建

```bash
# 传统方式每次都要敲这些命令
python -m venv venv
source venv/bin/activate  # Mac/Linux
.\venv\Scripts\activate   # Windows
pip install xxx
```

### Poetry 的解决方案

✅ **自动管理虚拟环境** - 不用你操心创建和激活
✅ **精准记录依赖** - 自动生成 lock 文件，版本锁死
✅ **项目隔离** - 每个项目独立，互不影响
✅ **一键还原** - 换电脑/给同事，一个命令搞定
✅ **依赖树清晰** - 知道谁依赖谁，升级更安全

---

## Poetry 能做什么？

### 1. 创建新项目（自动配好一切）

```bash
# 创建一个新项目
poetry new my-pdf-chatbot

# 自动生成这些：
my-pdf-chatbot/
├── pyproject.toml      # 项目配置文件（核心）
├── README.md
├── my_pdf_chatbot/     # 你的代码目录
│   └── __init__.py
└── tests/              # 测试目录
    └── __init__.py
```

### 2. 安装依赖（自动管理虚拟环境）

```bash
# 安装包（自动创建虚拟环境）
poetry add langchain

# 安装开发工具（不会打包到生产环境）
poetry add --group dev pytest black

# 指定版本
poetry add "openai>=1.0.0,<2.0.0"
```

**它做了什么：**
1. 检查有没有虚拟环境 → 没有就自动创建
2. 下载你要的包
3. 分析这个包需要哪些其他包（依赖）
4. 全部装好
5. 更新 `pyproject.toml`（需要什么）
6. 更新 `poetry.lock`（具体装了哪些版本）

### 3. 运行你的代码（自动进入虚拟环境）

```bash
# 不用手动激活虚拟环境！
poetry run python main.py

# 运行测试
poetry run pytest

# 启动你的应用
poetry run streamlit run app.py
```

### 4. 进入虚拟环境的命令行（可选）

```bash
# 如果你就是想进去看看
poetry shell

# 现在你在虚拟环境里了，可以直接用：
python main.py
pip list  # 看看装了啥
exit      # 退出虚拟环境
```

### 5. 给别人/换电脑用（一键还原）

```bash
# 你的同事拿到你的代码
git clone 你的项目
cd 项目目录

# 一个命令装好所有依赖（和你电脑一模一样）
poetry install
```

### 6. 管理依赖

```bash
# 看看装了哪些包
poetry show

# 看依赖树（谁依赖谁）
poetry show --tree

# 更新所有包
poetry update

# 只更新某个包
poetry update langchain

# 删除包
poetry remove requests
```

### 7. 导出传统格式（兼容性）

```bash
# 有些老项目需要 requirements.txt
poetry export -f requirements.txt --output requirements.txt
```

---

## 核心文件说明

### pyproject.toml（项目配置）

这是 Poetry 的"大脑"，记录项目所有信息：

```toml
[tool.poetry]
name = "my-pdf-chatbot"          # 项目名
version = "0.1.0"                # 版本号
description = "个人PDF知识库"    # 描述
authors = ["你的名字 <邮箱>"]

[tool.poetry.dependencies]        # 运行时需要的库
python = "^3.9"                   # Python版本要求
langchain = "^0.1.0"              # 自动记录你安装的包
openai = "^1.0.0"

[tool.poetry.group.dev.dependencies]  # 开发时需要的库
pytest = "^7.0.0"
black = "^23.0.0"
```

**翻译成人话：**
- 项目叫什么
- 需要哪个版本的 Python
- 需要哪些库（自动更新，不用手动改）
- 哪些库只在开发时用（比如测试工具）

### poetry.lock（版本锁定）

这是"详细账单"，记录每个库的确切版本和哈希值：

```
langchain 0.1.5
├── 它需要 pydantic 2.0.0
├── 它需要 requests 2.31.0
└── 每个库的下载地址和校验码
```

**作用：**
- 确保你和同事装的**完全一样**
- 避免"我电脑能跑，你电脑跑不了"
- 不要手动编辑这个文件！

---

## 实际使用流程（AI项目示例）

### 场景：开始做"PDF知识库聊天机器人"

```bash
# 第1步：创建项目
poetry new pdf-chatbot
cd pdf-chatbot

# 第2步：安装AI相关的库
poetry add langchain          # AI框架
poetry add openai             # GPT API
poetry add chromadb           # 向量数据库
poetry add pypdf              # 读PDF
poetry add streamlit          # 做界面

# 第3步：安装开发工具
poetry add --group dev pytest ipython black

# 第4步：写代码
# 创建 main.py ...

# 第5步：运行
poetry run python main.py

# 第6步：提交到 GitHub
# pyproject.toml 和 poetry.lock 都要提交
git add pyproject.toml poetry.lock
git commit -m "项目依赖配置"

# 第7步：别人克隆你的项目
# 他只需要运行：
poetry install  # 一模一样的环境就好了
```

---

## 常用命令速查表

| 命令 | 作用 | 什么时候用 |
|------|------|-----------|
| `poetry new 项目名` | 创建新项目 | 开始新项目 |
| `poetry init` | 在现有目录初始化 | 已有代码想用Poetry |
| `poetry add 包名` | 安装包 | 需要新功能 |
| `poetry add --group dev 包名` | 安装开发工具 | 装测试/格式化工具 |
| `poetry remove 包名` | 删除包 | 不需要某个库了 |
| `poetry install` | 安装所有依赖 | 克隆项目后首次运行 |
| `poetry update` | 更新所有包 | 定期维护 |
| `poetry run 命令` | 在虚拟环境运行 | 运行你的代码 |
| `poetry shell` | 进入虚拟环境 | 想在里面调试 |
| `poetry show` | 查看已安装的包 | 检查环境 |
| `poetry show --tree` | 查看依赖树 | 了解包关系 |
| `poetry env info` | 查看虚拟环境信息 | 找虚拟环境在哪 |

---

## 虚拟环境在哪？

```bash
# 查看虚拟环境位置
poetry env info --path

# 通常在：
# Mac: ~/Library/Caches/pypoetry/virtualenvs/项目名-随机码-py3.9
# 你不需要手动管理它，Poetry自动处理
```

---

## Poetry vs 传统方式对比

| 操作 | 传统方式 (pip + venv) | Poetry方式 |
|------|---------------------|-----------|
| 创建虚拟环境 | `python -m venv venv` | 自动创建 |
| 激活环境 | `source venv/bin/activate` | `poetry shell` 或 `poetry run` |
| 安装包 | `pip install xxx` | `poetry add xxx` |
| 记录依赖 | 手动写 requirements.txt | 自动更新 pyproject.toml |
| 锁定版本 | 手动指定或用 pip freeze | 自动生成 poetry.lock |
| 换电脑安装 | `pip install -r requirements.txt`<br>(经常出问题) | `poetry install`<br>(完全一致) |
| 区分开发依赖 | 手动维护多个txt文件 | `--group dev` 自动区分 |

---

## 注意事项

### ✅ 应该做的

1. **提交这两个文件到 Git：**
   - `pyproject.toml`（配置）
   - `poetry.lock`（版本锁定）

2. **用 Poetry 管理依赖：**
   - 不要再用 `pip install`
   - 统一用 `poetry add`

3. **运行代码用 poetry run：**
   ```bash
   poetry run python main.py
   poetry run pytest
   ```

### ❌ 不要做的

1. **不要手动编辑 poetry.lock**
   - 这是自动生成的，改了会出问题

2. **不要混用 pip 和 poetry**
   - 选一个就好，别两个都用

3. **不要提交虚拟环境到 Git**
   - `.gitignore` 里加上虚拟环境目录

---

## 总结：一句话记住 Poetry

> **Poetry = 自动管理虚拟环境 + 自动记录依赖 + 确保环境一致**

你只需要：
1. `poetry add 包名` → 装东西
2. `poetry run python xxx.py` → 运行代码
3. `poetry install` → 别人用你的项目

就这么简单！

---

## 下一步学习

- [ ] 用 Poetry 创建第一个 AI 项目
- [ ] 理解 pyproject.toml 的配置项
- [ ] 学习如何发布 Python 包（进阶）

---

**笔记创建时间：** 2025-11-19
**Poetry 版本：** 2.2.1
**用途：** AI 应用开发学习
