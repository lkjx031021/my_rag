import os
from pathlib import Path
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from langchain.schema import Document
from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

# from lianxi.faiss_test import vector_store

from pathlib import Path
current_file = Path(__file__).resolve()

current_path = current_file.parent
kb_path = current_path / 'company_zhidu_index'

# loader = Docx2txtLoader('files/顺义区数据和智慧城市底座项目建议书（代可行性研究报告）_20251110.docx')
loader = Docx2txtLoader('files/企业报销制度.docx')

documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "！", "？", "，", ""],
    # separators=["\n\n", "\n"],
    add_start_index=True,
)
# print(documents[0].page_content)

all_splits = text_splitter.split_documents(documents)
print(len(all_splits))
# print(type(all_splits[0]))
# print(all_splits[100].page_content)

def embed(query):
    embed_model = OllamaEmbeddings(model='bge-m3:latest')
    return embed_model.embed_documents(query)

text_list = [i.page_content for i in all_splits]
for i in text_list:
    print(i)
    print('++++++++++++++++++++++++++++++++')

embed_documents = embed(text_list)
print(embed_documents[:3])

def create_new_kb():
    embed_model = OllamaEmbeddings(model='bge-m3:latest')
    if os.path.exists(Path(kb_path) / 'index.faiss'):
        print(kb_path)
        vector_store = FAISS.load_local(kb_path, embed_model, distance_strategy="METRIC_INNER_PRODUCT", allow_dangerous_deserialization=True)
        return vector_store
    Docs = Document(page_content='init', metadata={})
    vector_store = FAISS.from_documents([Docs], embedding=embed_model)

    ids = list(vector_store.docstore._dict.keys())
    vector_store.delete(ids)
    vector_store.save_local('company_zhidu_index')
    return vector_store

if __name__ == '__main__':
    vs = create_new_kb()
    # vs.add_embeddings(text_embeddings = zip(text_list,embed_documents))
    # vs.save_local('company_zhidu_index')
    docs_with_scores = vs.similarity_search_with_score('培训报销', k=2)
    print('000000000000000000000000000000000000000000000')
    for doc, score in docs_with_scores:
        print(doc)
        print(score)
        print('--------------------------------------------------')
    print(all_splits[0])
