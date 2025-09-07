from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from matplotlib.pyplot import hist
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import os
from datetime import datetime
import logging

from regex import T
from routers.user_repository import register_user, login_user
from routers.message_repository import add_message_to_db, filter_message, get_message_by_id, update_message
from repository.conversation import create_new_conversation, get_user_conversations, get_conversation_messages
from langchain_core.runnables.history import RunnableWithMessageHistory

from sse_starlette.sse import EventSourceResponse

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
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    timestamp: str

from fastapi.responses import HTMLResponse

from langchain_deepseek import ChatDeepSeek
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts import ChatPromptTemplate, PromptTemplate
import asyncio
from langchain.chains.llm import LLMChain
from typing import Awaitable
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.chat_history import BaseChatMessageHistory

from operator import itemgetter

from langchain_openai.chat_models import ChatOpenAI

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from langchain_core.runnables import (
    RunnableLambda,
    ConfigurableFieldSpec,
    RunnablePassthrough,
)
from langchain_core.runnables.history import RunnableWithMessageHistory

class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""

    messages: list[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: list[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

store = {}

def get_by_session_id(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]

async def wrap_done(fn: Awaitable, event: asyncio.Event):
    """Wrap an awaitable with a event to signal when it's done or an exception is raised."""

    log_verbose = False

    try:
        await fn
    except Exception as e:
        import traceback
        traceback.print_exc()
        msg = f"Caught exception: {e}"
        print(f'{e.__class__.__name__}: {msg}',)
    finally:
        # Signal the aiter to stop.
        event.set()

class ConversationCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM responses."""

    def __init__(self, message_id=None):
        self.message_id = message_id

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(token, end='', flush=True)

    async def on_llm_end(self, response, **kwargs) -> None:
        print(type(response))
        res = response.generations[0][0].text
        await update_message(self.message_id, res)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """根路径，返回HTML页面"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/chat")
async def chat_stream(query: ChatRequest):
    """流式聊天接口"""
    
    print('====' * 50)
    print(query, query.message)
    async def generate_stream():
        try:
            
            # 构造一个新的Message_ID记录
            message_id = await add_message_to_db(query=query.message,
                                             conversation_id=query.conversation_id,
                                             prompt_name='New Chat'
                                             )
            callback = AsyncIteratorCallbackHandler()
            model = ChatDeepSeek(model="deepseek-chat", callbacks=[callback, ConversationCallbackHandler(message_id=message_id)], streaming=True)

            prompt = PromptTemplate.from_template(
                """
            你可以根据用户之前的对话和提出的当前问题，提供专业和详细的技术答案。\n\n
            角色：AI技术顾问\n
            目标：能够结合历史聊天记录，提供专业、准确、详细的AI技术术语解释，增强回答的相关性和个性化。\n
            输出格式：详细的文本解释，包括技术定义、原理和应用案例。\n
            工作流程：\n
              2. 分析用户当前问题：提取关键信息。\n
              3. 如果存在历史聊天记录，请结合历史聊天记录和当前问题提供个性化的技术回答。\n
              4. 如果问题与AI技术无关，以正常方式回应。\n\n
            历史聊天记录:\n
            {history}\n
            当前问题：\n
            {input}\n
                """
            )
            messages = await filter_message(conversation_id=query.conversation_id, limit=10, chat_type="New Chat")
            print(messages)

            history = []
            for m in messages:
                history.append(f"user:{m.query} \n AI:{m.response}")
            
            chain = prompt | model
            # chat_with_history = RunnableWithMessageHistory(
            #     chain,
            #     get_session_history = get_by_session_id,
            #     history_messages_key="history",
            #     input_messages_key='input',
            # )

            task = asyncio.create_task(wrap_done(
                chain.ainvoke({"input": query.message, "history": history}), 
                callback.done))
            async for token in callback.aiter():
                # print(token)
                # print("--------------------------------")
                # 包装成SSE格式的JSON数据
                yield json.dumps(
                    {"text": token,}, ensure_ascii=False)
            
            await task


        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            error_chunk = {
                "type": "error",
                "text": "抱歉，处理您的请求时出现了错误。"
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return EventSourceResponse(generate_stream())


@app.get("/api/conversations/messages")
async def get_conversation_messages_api(conversation_id: str):
    """获取会话详细记录"""
    messages = await get_conversation_messages(conversation_id)
    return messages

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

    
app.post("/api/new_conversation",
        tags=["conversations"],
        summary="创建新会话",
        status_code=201,
        )(create_new_conversation)

app.get("/api/conversations",
        tags=["conversations"],
        summary="获取用户会话列表",
        )(get_user_conversations)

app.get("/api/conversations/messages",
        tags=["conversation_messages"],
        summary="获取用户问答记录",
        )(get_conversation_messages)

# 用户注册
app.post("/api/users/register",
             tags=["Users"],
             summary="用户注册",
             )(register_user)

# 用户登录
app.post("/api/users/login",
             tags=["Users"],
             summary="用户登录",
             )(login_user)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
