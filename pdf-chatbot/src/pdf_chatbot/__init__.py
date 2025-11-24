"""PDF 聊天机器人 - 基于 RAG 的文档问答系统"""

from .config import Config
from .document_loader import DocumentProcessor
from .vector_store import VectorStoreManager
from .qa_chain import QASystem

__version__ = "0.1.0"

__all__ = [
    "Config",
    "DocumentProcessor",
    "VectorStoreManager",
    "QASystem",
]
