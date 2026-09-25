"""索引构建脚本：扫描 docs/ 下所有 .txt/.md 文件，切分后写入持久化的 Chroma 向量库。

运行方式：
    python ingest.py
"""

import os
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# 路径配置
BASE_DIR = Path(__file__).parent.resolve()
DOCS_DIR = BASE_DIR / "docs"
PERSIST_DIR = BASE_DIR / "chroma_db"

# 模型配置
EMBEDDING_MODEL = "bge-m3"
COLLECTION_NAME = "local_kb"

# 切分参数
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_documents():
    """递归加载 docs/ 目录下所有 .txt 和 .md 文件。"""
    if not DOCS_DIR.exists():
        raise FileNotFoundError(f"文档目录不存在: {DOCS_DIR}")

    docs = []
    for pattern in ("**/*.txt", "**/*.md"):
        loader = DirectoryLoader(
            str(DOCS_DIR),
            glob=pattern,
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
        )
        docs.extend(loader.load())

    if not docs:
        raise RuntimeError(f"在 {DOCS_DIR} 下未找到任何 .txt/.md 文档")

    print(f"共加载 {len(docs)} 个文档文件")
    return docs


def split_documents(docs):
    """将文档切分成较小的 chunk 便于检索。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"切分后共 {len(chunks)} 个 chunk")
    return chunks


def build_vectorstore(chunks):
    """生成向量并写入持久化的 Chroma。

    每次运行都重建 collection，避免旧数据残留。
    """
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    # 如果已存在同名 collection，先删除以避免重复入库
    try:
        Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(PERSIST_DIR),
        ).delete_collection()
        print("已清除旧的 collection")
    except Exception:
        # collection 不存在时忽略
        pass

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(PERSIST_DIR),
    )
    return vectorstore


def main():
    print(f"文档目录: {DOCS_DIR}")
    print(f"持久化目录: {PERSIST_DIR}")
    print(f"Embedding 模型: {EMBEDDING_MODEL}")
    print("-" * 50)

    docs = load_documents()
    chunks = split_documents(docs)
    build_vectorstore(chunks)

    print("-" * 50)
    print(f"入库完成，共 {len(chunks)} 个 chunk 已写入 {PERSIST_DIR}")
    print("现在可以运行 `python app.py` 启动问答界面")


if __name__ == "__main__":
    main()
