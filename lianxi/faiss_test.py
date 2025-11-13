import os
from re import split
import uuid
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import Milvus
from langchain_ollama import OllamaEmbeddings, ChatOllama
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
    if os.path.exists(Path(kb_path) / "index.faiss"):
        vector_store = FAISS.load_local(kb_path, embed_model, distance_strategy="METRIC_INNER_PRODUCT", allow_dangerous_deserialization=True)
        print("load local")
        return vector_store
    doc = Document(page_content="init", metadata={})
    vector_store = FAISS.from_documents([doc], embed_model, distance_strategy="METRIC_INNER_PRODUCT")
    ids = list(vector_store.docstore._dict.keys())
    vector_store.delete(ids)
    vector_store.save_local(kb_path)
    return vector_store

def create_new_kb_milvus():
    embed_model = OllamaEmbeddings(model="bge-m3:latest")
    if os.path.exists(Path(kb_path) / "index.milvus"):
        vector_store = Milvus.load_local(kb_path, embed_model, distance_strategy="METRIC_INNER_PRODUCT", allow_dangerous_deserialization=True)
        print("load local")
        return vector_store
    doc = Document(page_content="init", metadata={})
    vector_store = Milvus.from_documents([doc], embed_model, distance_strategy="METRIC_INNER_PRODUCT")
    ids = list(vector_store.docstore._dict.keys())
    vector_store.delete(ids)
    vector_store.save_local(kb_path)
    return vector_store


def load_docs(file_path):
    loader = UnstructuredMarkdownLoader(file_path, mode="single")
    docs = loader.load()
    return docs

def embed(query):
    embed_model = OllamaEmbeddings(model="bge-m3:latest")
    query_vector = embed_model.embed_query(query)
    return query_vector

def text_split(docs):
    from langchain_text_splitters import RecursiveCharacterTextSplitter as rcs

    text_splitter = rcs(chunk_size=500, chunk_overlap=100)
    return text_splitter.split_documents(docs)

if __name__ == "__main__":
    # model = ChatOllama(model="qwen3:4b")
    # print(model.invoke("数学有什么用"))
    # exit()
    # docs = load_docs("lianxi/README.md")
    # texts = text_split(docs)
    # text = [x.page_content for x in texts]
    # embeddings = OllamaEmbeddings(model="bge-m3:latest").embed_documents(text)

    vs = create_new_kb()
    # print(vs)
    # print(vs.docstore._dict)
    # print(len(vs.docstore._dict))
    # vs.add_embeddings(zip(text, embeddings))
    # vs.save_local(kb_path)
    # query = embed("RAG增强可以使用的框架？")
    query = embed("RAG索引算法有哪些")
    res = vs.similarity_search_by_vector(query, k=3)
    # print(docs[0])
    # print(len(docs))

    # print(type(docs[0]))
    print(res)
    # for i in res:
    #     print(i) 
