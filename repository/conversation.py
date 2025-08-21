from typing import List
import traceback
from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from fastapi import FastAPI, Body, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from server.db.models.conversation_model import ConversationModel
from server.db.models.message_model import MessageModel
from server.db import *
from sqlalchemy.future import select
from sqlalchemy import desc

from server.db.session import get_async_db

class RequestConversation(BaseModel):
    user_id: str = Field(..., description="The ID of the user creating the conversation")
    name: str = Field(default='New Chat', description="Name of the conversation, defaults to 'New Chat'")
    chat_type: str = Field(default='text', description="Type of chat, defaults to 'text'")

class MessageResponse(BaseModel):
    id: str = Field(..., description="消息的唯一标识符")
    conversation_id: str = Field(..., description="关联的会话ID")
    chat_type: str = Field(..., description="对话类型（普通问答、知识库问答、AI搜索、推荐系统、Agent问答）")
    query: str = Field(..., description="用户的问题")
    response: str = Field(..., description="大模型的回答")
    meta_data: dict = Field(..., description="其他元数据")
    create_time: datetime | None = Field(..., description="消息创建时间")

class ConversationResponse(BaseModel):
    id: str
    name: str
    chat_type: str
    create_time: datetime | None = None
    user_id: str



async def create_new_conversation(
        request: RequestConversation = Body(...),
        session: AsyncSession = Depends(get_async_db)
):
    """
    创建新会话
    """
    new_conv = ConversationModel(
        id = str(uuid.uuid4()),
        user_id = request.user_id,
        name = request.name,
        chat_type = request.chat_type
    )
    try:
        session.add(new_conv)
        await session.commit()
        await session.refresh(new_conv)

        return JSONResponse(
            status_code=200,
            content={
                "status": 200, 
                "id": str(new_conv.id),
                "name": str(new_conv.name),
                "chat_type": str(new_conv.chat_type),
                "create_time": new_conv.create_time.isoformat() if new_conv.create_time else None
            }
        )
    except Exception as e:
        await session.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")

async def get_user_conversations(
        user_id: str,
        chat_types: str = Query(...),
        session: AsyncSession = Depends(get_async_db)
):
    """
    用来获取指定用户名的历史对话窗口
    """
    async with session as async_session:
        result = await async_session.execute(
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id,
                   ConversationModel.chat_type == chat_types)
            .order_by(desc(ConversationModel.create_time))
        )
        conversations = result.scalars().all()

        if conversations == []:
            return {"status": 200, "msg": "success", "data": []}
        else:
            data = [ConversationResponse(
                id=str(conv.id),
                name=str(conv.name),
            chat_type=str(conv.chat_type),
            create_time=conv.create_time,
            user_id=str(conv.user_id)
        ) for conv in conversations]

            return {"status": 200, "msg": "success", "data": data}

async def get_conversation_messages(
        conversation_id: str,
        chat_types: List[str] = Query(None),
        session: AsyncSession = Depends(get_async_db)
):
    async with (session as async_session):
        query = select(MessageModel).where(MessageModel.conversation_id == conversation_id)
        if chat_types:
            query = query.where(MessageModel.chat_type.in_(chat_types))

        result = await async_session.execute(query)
        messages = result.scalars().all()
        if not messages:
            return {"status_code": 200, "msg": "success", "data": []}
        data = [
            MessageResponse(
                id=str(msg.id),
                conversation_id=str(msg.conversation_id),
                chat_type=str(msg.chat_type),
                query=str(msg.query),
                response=str(msg.response),
                meta_data=msg.meta_data or {},
                create_time=msg.create_time
            ) 
            for msg in messages
        ]

        return {"status": 200, "msg": "success", "data": data}
