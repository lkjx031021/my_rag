import os
from re import split
import uuid
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
    loader = UnstructuredMarkdownLoader(file_path, mode="single")
    docs = loader.load()
    return docs

def text_splitter(docs):
    from langchain.text_splitter import MarkdownHeaderTextSplitter as mht
    from langchain.text_splitter import RecursiveCharacterTextSplitter as rcs

    # text_splitter = mht(headers_to_split_on=[
    #             ("#", "head1"),
    #             ("##", "head2"),
    #             ("###", "head3"),
    #             ("####", "head4"),
    #         ])
    text_splitter = rcs(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(docs)
    return texts



if __name__ == "__main__":
    docs = load_docs("lianxi/README2.md")
    splits = text_splitter(docs)
    vs = create_new_kb()
    print(splits)
    print(len(splits))
    exit()
    splits = text_splitter(docs[0].page_content)
    print(docs[0])
    print(len(docs))
    print(splits)
    print(len(splits))
    # for i in docs:
    #     print(i)
    #     print("-----")

    print(type(docs[0]))
    # vs.add_embeddings(text_embeddings=)
    # vs.add_documents(docs)
