from typing import List
import traceback
from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from fastapi import FastAPI, Body, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from server.db.models.conversation_model import ConversationModel
from sqlalchemy.future import select

from server.db.session import get_async_db

class RequestConversation(BaseModel):
    user_id: str = Field(..., description="The ID of the user creating the conversation")
    name: str = Field(default='New Chat', description="Name of the conversation, defaults to 'New Chat'")
    chat_type: str = Field(default='text', description="Type of chat, defaults to 'text'")

async def create_new_conversation(
        request: RequestConversation = Body(...),
        session: AsyncSession = Depends(get_async_db)
):
    pass
    new_conv = ConversationModel(
        id = str(uuid.uuid4()),
        user_id = request.user_id,
        name = request.name,
        chat_type = request.chat_type,
        create_time = datetime.now()
    )
    try:

        session.add(new_conv)
        await session.commit()
        # await session.refresh(new_conv)

        return JSONResponse(
            status_code=200,
            content={"status": 200, "id":new_conv.id}
        )

    except:
        traceback.print_exc()


async def get_user_conversation(
        conversation_id: str,
        chat_types: List[str] = Query(None),
        session: AsyncSession = Depends(get_async_db)
):
    async with (session as async_session):
        query = select(ConversationModel).where(ConversationModel.id == conversation_id)
        if chat_types:
            query = query.where(ConversationModel.chat_type.in_(chat_types))

        result = await async_session.execute(query)
        messages = result.scalars().all()
        pass
