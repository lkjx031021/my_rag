from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import os
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Chat System", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 数据模型
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    timestamp: str

# 模拟RAG系统
class RAGSystem:
    def __init__(self):
        self.knowledge_base = {
            "FastAPI": "FastAPI是一个现代、快速（高性能）的Web框架，用于基于Python 3.7+构建API，基于标准Python类型提示。",
            "RAG": "RAG（Retrieval-Augmented Generation）是一种结合检索和生成的AI技术，通过检索相关文档来增强语言模型的回答能力。",
            "Python": "Python是一种高级编程语言，以其简洁的语法和强大的库生态系统而闻名。",
            "机器学习": "机器学习是人工智能的一个分支，使计算机能够在没有明确编程的情况下学习和改进。",
            "深度学习": "深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的学习过程。"
        }
    
    async def search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """搜索知识库"""
        query_lower = query.lower()
        results = []
        
        for key, content in self.knowledge_base.items():
            if query_lower in key.lower() or query_lower in content.lower():
                results.append({
                    "title": key,
                    "content": content,
                    "relevance_score": 0.9
                })
        
        return results[:3]  # 返回前3个最相关的结果
    
    async def generate_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        """生成回答"""
        if not context:
            return f"抱歉，我在知识库中没有找到关于'{query}'的相关信息。请尝试其他问题。"
        
        context_text = "\n".join([f"- {item['title']}: {item['content']}" for item in context])
        
        response = f"""基于我的知识库，我找到了以下相关信息：

{context_text}

根据这些信息，我可以回答您的问题：{query}

如果您需要更详细的信息或有其他问题，请随时告诉我。"""
        
        return response

# 初始化RAG系统
rag_system = RAGSystem()

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """根路径，返回HTML页面"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """流式聊天接口"""
    
    async def generate_stream():
        try:
            # 搜索知识库
            sources = await rag_system.search_knowledge_base(request.message)
            
            # 生成回答
            response = await rag_system.generate_response(request.message, sources)
            
            # 模拟流式输出
            words = response.split()
            for i, word in enumerate(words):
                chunk = {
                    "type": "content",
                    "content": word + " ",
                    "done": i == len(words) - 1
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)  # 模拟打字效果
            
            # 发送源信息
            if sources:
                sources_chunk = {
                    "type": "sources",
                    "sources": sources
                }
                yield f"data: {json.dumps(sources_chunk, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            error_chunk = {
                "type": "error",
                "content": "抱歉，处理您的请求时出现了错误。"
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库"""
    try:
        # 这里可以添加文档处理逻辑
        # 目前只是简单的文件接收
        content = await file.read()
        
        return {
            "message": f"文档 {file.filename} 上传成功",
            "filename": file.filename,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/test/{item}")
async def test_route(item: str):
    """测试路由"""
    return {"message": "Hello World", "a": item}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 