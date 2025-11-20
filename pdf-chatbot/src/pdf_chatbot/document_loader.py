"""文档加载模块"""
from typing import List
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from .config import Config


class DocumentProcessor:
    """文档处理类"""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )

    def load_pdf(self, file_path: str) -> List[Document]:
        """
        加载 PDF 文件

        参数:
            file_path: PDF 文件路径

        返回:
            文档列表
        """
        print(f"📄 正在加载 PDF: {file_path}")
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print(f"✅ 成功加载 {len(documents)} 页")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        切分文档

        参数:
            documents: 文档列表

        返回:
            切分后的文档块列表
        """
        print(f"✂️  正在切分文档...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"✅ 切分为 {len(chunks)} 个文档块")
        return chunks

    def process_pdf(self, file_path: str) -> List[Document]:
        """
        处理 PDF 文件（加载 + 切分）

        参数:
            file_path: PDF 文件路径

        返回:
            切分后的文档块列表
        """
        documents = self.load_pdf(file_path)
        chunks = self.split_documents(documents)
        return chunks
