import os
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document

from langchain_community.document_loaders import UnstructuredMarkdownLoader

from pathlib import Path
current_file = Path(__file__).resolve()

current_path = current_file.parent

kb_path = current_path / "faiss_index"

if not kb_path.exists():
    os.makedirs(kb_path)



def create_new_kb():
    embed_model = OllamaEmbeddings(model="bge-m3:latest")
    doc = Document(page_content="init", metadata={})
    vector_store = FAISS.from_documents([doc], embed_model, distance_strategy="METRIC_INNER_PRODUCT")
    ids = list(vector_store.docstore._dict.keys())
    vector_store.delete(ids)
    vector_store.save_local(kb_path)
    return vector_store


def load_docs(file_path):
    loader = UnstructuredMarkdownLoader(file_path)
    docs = loader.load()
    return docs

if __name__ == "__main__":
    docs = load_docs("lianxi/README.md")
    print(docs[0])
    print(len(docs))

    print(type(docs[0]))