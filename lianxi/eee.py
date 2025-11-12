from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

markdown_document = """
# Foo

## Bar

Hi this is Jim
Hi this is Joe

## Baz

Hi this is Molly
"""

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
]

markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
md_header_splits = markdown_splitter.split_text(markdown_document)
print(md_header_splits)

# RecursiveCharacterTextSplitter
rct_splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap=0)
rct_splitter_splits = rct_splitter.split_documents(md_header_splits)
print('---  RCT Splitter ---')
print(rct_splitter_splits)