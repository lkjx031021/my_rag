import sys
sys.path.append("./")  # 添加上级目录到路径中
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from server.db.base import SQLALCHEMY_DATABASE_URI
from server.db.base import Base
# 显式导入所有模型
from server.db.models.user_model import UserModel
from server.db.models.conversation_model import ConversationModel
from server.db.models.message_model import MessageModel
from server.db.models.knowledge_base_model import KnowledgeBaseModel
from server.db.models.knowledge_file_model import KnowledgeFileModel

from server.db.base import async_engine, AsyncSessionLocal



async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_tables(async_engine))
