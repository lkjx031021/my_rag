import uuid  # 添加缺失的uuid导入
import warnings

from docx import Document
from typing import List, Optional
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

    def add_node(self, title: str, content: str = "", level : int = 0):
        node = TreeNode(title, content, level)
        self.children.append(node)
        return node


class TreeBuilder:
    """投标文件树结构构建器"""
    def __init__(self, doc_path: str):
        self.doc = parse_file_with_unstructured(doc_path)  # 加载Word文档
        self.root = TreeNode("根节点")  # 根节点
        self.current_nodes = {0: self.root}  # 当前层级节点映射表
        self.embed_model = OllamaEmbeddings(model="bge-m3:latest")  # 使用的嵌入模型
        self.vector_store = self._init_vector_store()  # 初始化向量库
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

    def _get_heading_level(self, paragraph) -> Optional[int]:
        """获取段落的标题级别（1-9）"""
        if paragraph.style and paragraph.style.name.startswith('Heading '):
            try:
                level = int(paragraph.style.name.split()[-1])
                return level if 1 <= level <= 9 else None
            except (IndexError, ValueError):
                return None
        return None

    def _detech_abstrect(self, element, current_level: int):
        """标题之前皆为摘要内容"""
        if current_level == -1:
            return element["text"]
        return None

    def build_tree(self) -> TreeNode:
        """构建投标文件树结构"""
        current_content = []
        current_level = -1
        current_node = None
        for idx, ele in enumerate(self.doc["elements"]):
            if ele["category"] == "PageBreak":
                continue
            if zhaiyao := self._detech_abstrect(ele, current_level):
                self.root.content += zhaiyao + "\n"
                continue
            if ele["category"] == "Title":
                if current_level != ele["metadata"]["category_depth"]:
                    pass
                else:
                    current_level = ele["metadata"]["category_depth"]
                    if current_level == 0:
                        parent_node = self.root
                    else:
                        if parent_node := self.node_map.get(ele["metadata"]["parent_id"]):
                            ...
                        else:
                            warnings.warn(f"Parent ID {ele['metadata']['parent_id']} not found for element ID {ele['id']}. content: {ele['text']}. Skipping.")
                            continue
                    current_node = parent_node.add_node(ele["title"], ele["content"], current_level)
                    self.node_map[ele["id"]] = current_node

            else:
                if ele["metadata"]["parent_id"]:
                    current_node = self.node_map.get(ele["metadata"]["parent_id"])
                    if current_node is None:
                        warnings.warn(f"Parent ID {ele['metadata']['parent_id']} not found for element ID {ele['id']}. content: {ele['text']}. Skipping.")
                        continue
                    current_node.content += ele["content"] + "\n"
        
        for para in self.doc["elements"]:
            heading_level = self._get_heading_level(para)
            
            if heading_level is not None:
                # 保存之前积累的段落内容到最近的节点
                if current_content and current_level in self.current_nodes:
                    self.current_nodes[current_level].content = '\n'.join(current_content)
                    self._process_node_for_vectorization(current_level)
                    current_content = []
                
                # 创建新节点
                new_node = TreeNode(title=para.text)
                
                # 找到父节点（当前级别-1）
                parent_level = heading_level - 1
                if parent_level in self.current_nodes:
                    self.current_nodes[parent_level].add_child(new_node)
                else:
                    # 如果父节点不存在，使用最近的有效父节点
                    valid_levels = [l for l in self.current_nodes if l < heading_level]
                    if valid_levels:
                        parent_level = max(valid_levels)
                        self.current_nodes[parent_level].add_child(new_node)
                
                # 更新当前节点映射
                self.current_nodes[heading_level] = new_node
                current_level = heading_level
                
            elif para.text.strip():  # 非标题段落
                if para.text.strip():  # 非空段落
                    current_content.append(para.text)
        
        # 处理最后剩余的段落内容
        if current_content and current_level in self.current_nodes:
            self.current_nodes[current_level].content = '\n'.join(current_content)
            self._process_node_for_vectorization(current_level)
        
        # 保存向量库（使用文档所在目录的faiss_index）
        kb_path = os.path.join(os.path.dirname(doc_path), "faiss_index")
        self.vector_store.save_local(
            kb_path,
            distance_strategy="METRIC_INNER_PRODUCT"
        )
        
        return self.root

    def _process_node_for_vectorization(self, level: int):
        """处理节点的向量化和存储"""
        node = self.current_nodes[level]
        if node.content:
            node.generate_embedding(self.embed_model)
            langchain_doc = node.to_langchain_document()
            self.vector_store.add_documents([langchain_doc])

# 示例用法
if __name__ == "__main__":
    import os
    doc_path = os.path.join("lianxi", "load_text", "files", "keyan.docx")
    builder = TreeBuilder(doc_path)
    tree_root = builder.build_tree()
    
    # 打印树结构（调试用）
    def print_tree(node: TreeNode, depth: int = 0):
        print(f"{'  '*depth}- {node.title}")
        for child in node.children:
            print_tree(child, depth + 1)
    
    print_tree(tree_root)
    
    # 测试向量搜索
    query = "技术方案要求"
    query_vector = builder.embed_model.embed_query(query)
    results = builder.vector_store.similarity_search_by_vector(query_vector, k=3)
    print("\n相关段落搜索结果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.metadata['title']}: {result.page_content[:100]}...")
