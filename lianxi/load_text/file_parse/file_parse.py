from typing import List, Dict, Any, Optional, Sequence
from pathlib import Path
from unstructured.documents.elements import Element
from unstructured.partition.auto import partition

# 自定义解析函数，支持任意类型的文件格式
def parse_file_with_unstructured(file_path: str):
    """
    使用UnstructuredIO解析单个文件

    Args:
        file_path: 文件路径

    Returns:
        Dict: 包含解析结果和统计信息的字典
    """
    print(f"\n 解析文件: {file_path}")

    try:
        # 使用partition函数自动检测文件类型并解析,默认strategy策略是auto，还会有fast策略，速度比image-to-text models的快100倍
        elements: List[Element] = partition(filename=file_path, strategy="auto")

        # 分析解析结果
        analysis = {
            "file_path": file_path,
            "file_extension": Path(file_path).suffix.lower(),
            "total_elements": len(elements),
            "element_types": {},
            "elements": elements,
            "text_content": "",
            "statistics": {}
        }

        # 统计元素类型
        for element in elements:
            element_type = type(element).__name__
            analysis["element_types"][element_type] = analysis["element_types"].get(element_type, 0) + 1

        # 提取文本内容
        text_parts = []

        for element in elements:
            if hasattr(element, 'text') and element.text:
                text_parts.append(element.text)
            # if type(element).__name__ == "Title":
            #     print(element.text)

        analysis["text_content"] = "\n\n".join(text_parts)
        # exit()

        # 计算统计信息
        analysis["statistics"]["total_characters"] = len(analysis["text_content"])

        print(f"   解析完成")
        print(f"   元素总数: {analysis['total_elements']}")
        print(f"   元素类型: {analysis['element_types']}")
        print(f"   总字符数: {analysis['statistics']['total_characters']}")
        print(f"   文本内容: {analysis['text_content'][:200]} ")
        return analysis

    except Exception as e:
        print(f"文件解析失败: {e}")
        return {}

if __name__ == "__main__":
    # analysis = parse_file_with_unstructured('D:/doc/project/my_rag/lianxi/load_text/files/keyan.docx')
    analysis = parse_file_with_unstructured('D:/doc/project/my_rag/lianxi/load_text/files/big_table2.docx')
    a = 1