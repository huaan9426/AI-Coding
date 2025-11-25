#!/bin/bash

##############################################################################
# PDF 聊天机器人 - 超级简单启动脚本（绕过 Poetry）
##############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}📚 PDF 聊天机器人 - 超级简单启动（绕过 Poetry）${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

##############################################################################
# 步骤 1: 检查 Python 3.12
##############################################################################
echo -e "${YELLOW}[1/4] 检查 Python 3.12...${NC}"

if ! command -v python3.12 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python 3.12${NC}"
    echo -e "${YELLOW}💡 请安装 Python 3.12: brew install python@3.12${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3.12 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

##############################################################################
# 步骤 2: 创建虚拟环境（使用 venv，不用 Poetry）
##############################################################################
echo ""
echo -e "${YELLOW}[2/4] 创建/激活虚拟环境...${NC}"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  创建新的虚拟环境（使用 Python 3.12）...${NC}"
    python3.12 -m venv venv
    echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"
fi

# 激活虚拟环境
source venv/bin/activate

##############################################################################
# 步骤 3: 安装依赖（使用 pip）
##############################################################################
echo ""
echo -e "${YELLOW}[3/4] 安装依赖（使用 pip）...${NC}"
echo -e "${YELLOW}   这可能需要 1-2 分钟...${NC}"

# 升级 pip
pip install --upgrade pip > /dev/null 2>&1

# 安装核心依赖
pip install python-dotenv
pip install langchain
pip install openai
pip install pydantic-settings  # chromadb 需要
pip install chromadb
pip install pypdf
pip install tiktoken

echo -e "${GREEN}✅ 依赖安装完成${NC}"

# 验证
echo ""
echo -e "${YELLOW}验证依赖...${NC}"
python -c "import dotenv; print('✅ python-dotenv')"
python -c "import langchain; print('✅ langchain')"
python -c "import openai; print('✅ openai')"
python -c "import chromadb; print('✅ chromadb')"

##############################################################################
# 步骤 4: 配置环境变量
##############################################################################
echo ""
echo -e "${YELLOW}[4/4] 检查环境变量...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ 已创建 .env 文件${NC}"

        read -p "请输入你的 OpenAI API Key: " api_key
        if [ -n "$api_key" ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/sk-your-api-key-here/$api_key/g" .env
            else
                sed -i "s/sk-your-api-key-here/$api_key/g" .env
            fi
            echo -e "${GREEN}✅ API Key 已配置${NC}"
        fi
    fi
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

##############################################################################
# 启动程序
##############################################################################
echo ""
echo -e "${YELLOW}启动程序...${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

# 设置 PYTHONPATH
export PYTHONPATH="${PROJECT_DIR}/src:${PYTHONPATH}"

# 启动
python -m pdf_chatbot.main

echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${GREEN}👋 感谢使用！${NC}"
echo -e "${BLUE}=====================================================================${NC}"

# 退出时停用虚拟环境
deactivate
