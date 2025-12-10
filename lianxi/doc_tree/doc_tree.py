import uuid  # 添加缺失的uuid导入
import warnings

from docx import Document
from typing import List, Optional, Callable
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document as LangchainDocument
import os

from lianxi.load_text.file_parse.file_parse import parse_file_with_unstructured

# 新增向量化功能
class TreeNode:
    """树节点类，表示投标文件的章节结构"""
    def __init__(self, title: str, content: str = "", level: int = 0):
        self.title = title        # 节点标题（小标题）
        self.title_path = ''      # 连接多层级标题
        self.content = content    # 节点内容（段落文本）
        self.embedding = None     # 节点向量表示
        self.level = level
        self.children: List['TreeNode'] = []  # 子节点列表
        self.parent: TreeNode | None = None # 父节点
        self.doc_id = str(uuid.uuid4())  # 为FAISS向量库准备的文档ID

    def generate_embedding(self, embed_model: OllamaEmbeddings) -> None:
        """生成节点内容的向量表示"""
        if self.content:
            self.embedding = embed_model.embed_query(self.content)
    
    def to_langchain_document(self) -> LangchainDocument:
        """转换为LangChain文档格式用于向量库"""
        return LangchainDocument(
            page_content=self.content,
            metadata={
                "title": self.title,
                "doc_id": self.doc_id
            }
        )

    def __repr__(self):
        return f"TreeNode(title='{self.title}', content='{self.content[:20]}...', children={len(self.children)})"

    def add_node(self, title: str, content: str = ""):
        node = TreeNode(title, content, self.level + 1)
        self.children.append(node)
        node.parent = self

        # 拼接全部层级的title
        title_ls = []
        temp_node = node
        if temp_node.parent:
            while temp_node.parent is not None:
                title_ls.append(temp_node.title)
                temp_node = temp_node.parent
            title_ls.reverse()
            title_path = '-'.join(title_ls)
            node.title_path = title_path
        return node


class TreeBuilder:
    """Word文件树结构构建器"""
    def __init__(self, doc_path: str):
        self.doc = parse_file_with_unstructured(doc_path)  # 加载Word文档
        self.root = TreeNode("根节点")  # 根节点
        self.current_nodes = {0: self.root}  # 当前层级节点映射表
        # self.embed_model = OllamaEmbeddings(model="bge-m3:latest")  # 使用的嵌入模型
        # self.vector_store = self._init_vector_store()  # 初始化向量库
        self.node_map = {}  # 用于存储节点与ID的映射
        
    def _init_vector_store(self) -> FAISS:
        """初始化FAISS向量库"""
        kb_path = os.path.join(os.path.dirname(doc_path), "faiss_index")
        os.makedirs(kb_path, exist_ok=True)
        
        if os.path.exists(os.path.join(kb_path, "index.faiss")):
            return FAISS.load_local(
                kb_path, 
                self.embed_model, 
                distance_strategy="METRIC_INNER_PRODUCT",
                allow_dangerous_deserialization=True
            )
        
        # 创建初始向量库
        init_doc = self.root.to_langchain_document()
        vector_store = FAISS.from_documents(
            [init_doc], 
            self.embed_model,
            distance_strategy="METRIC_INNER_PRODUCT"
        )
        vector_store.save_local(kb_path)
        return vector_store

    def _detech_abstrect(self, element, current_level: int):
        """标题之前皆为摘要内容"""
        if current_level == -1 and element.category != "Title":
            return element.text
        return None

    def build_tree(self):
        """构建投标文件树结构"""
        current_level = -1
        current_node = None
        for idx, ele in enumerate(self.doc["elements"]):
            if ele.category == "PageBreak":
                # 换页符 直接过滤
                continue
            if ele.category == "Footer":
                continue
            if zhaiyao := self._detech_abstrect(ele, current_level):
                # 第一个标题之前的内容，封面、目录、摘要等,均存放在root节点中
                self.root.content += zhaiyao + "\n"
                continue
            if ele.category == "Title":
                # 标题
                last_level = current_level
                last_node = current_node
                current_level = ele.metadata.category_depth
                current_node = None
                parent_node = None # 当前节点的父节点
                if current_level == 0:
                    parent_node = self.root

                # 当前标题层级小于上一标题层级的情况
                elif last_level > current_level:
                    while last_level > current_level:
                        last_node = last_node.parent
                        last_level = last_node.level
                    parent_node = last_node.parent

                # 当前标题层级大于上一标题层级的情况
                elif last_level < current_level:
                    while last_level < current_level:
                        last_level += 1
                        last_node = last_node.add_node(ele.text)
                        current_node = last_node
                # 当前标题与上一标题属于同一级
                else:
                    parent_node = last_node.parent

                if not current_node:
                    current_node = parent_node.add_node(ele.text)
                self.node_map[ele.id] = current_node

            else:
                # 非标题
                # 所有非标题内容都存放在当前node中
                if ele.metadata.parent_id:
                    # 有可能当前文档的parent_id不是当前node，如果有这种问题，后续都会出现异常
                    node = self.node_map.get(ele.metadata.parent_id)
                    node.content += ele.text + "\n"
                    if node is None:
                        warnings.warn(f"Parent ID {ele.metadata.parent_id} not found for element ID {ele.id}. content: {ele.text}. Skipping.")
                        continue
                else:
                    # 如果有文档没有parent_id，则自动更新到当前node中
                    current_node.content += ele.text + "\n"
        return self

    def _process_node_for_vectorization(self, level: int):
        """处理节点的向量化和存储"""
        node = self.current_nodes[level]
        if node.content:
            node.generate_embedding(self.embed_model)
            langchain_doc = node.to_langchain_document()
            self.vector_store.add_documents([langchain_doc])

    def dfs_iterative(self, visit:Callable[[TreeNode], None]):
        stack = [self.root]
        while stack:
            node = stack.pop()
            visit(node)
            if node.children:
                stack.extend(reversed(node.children))

def view(node: TreeNode):
    print(f"{'  '*node.level}{node.level}", node.title_path, '-', node.content)

# 示例用法
if __name__ == "__main__":
    import os
    doc_path = 'D:/doc/project/my_rag/lianxi/load_text/files/keyan.docx'
    builder = TreeBuilder(doc_path)
    tree = builder.build_tree()
    tree_root = tree.root
    
    # 打印树结构（调试用）
    def print_tree(node,  depth: int = 0):
        print(f"{'  '*depth}- {node.title}")
        for child in node.children:
            print_tree(child, depth + 1)
    
    print_tree(tree_root)
    tree.dfs_iterative(view)
    
    # # 测试向量搜索
    # query = "技术方案要求"
    # query_vector = builder.embed_model.embed_query(query)
    # results = builder.vector_store.similarity_search_by_vector(query_vector, k=3)
    # print("\n相关段落搜索结果:")
    # for i, result in enumerate(results, 1):
    #     print(f"{i}. {result.metadata['title']}: {result.page_content[:100]}...")
