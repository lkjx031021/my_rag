from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker

from configs import SQLALCHEMY_DATABASE_URI
from configs.config import cfg
import json

# db
db_username = cfg['db'].get("username")
db_password = cfg['db'].get("password")
db_hostname = cfg['db'].get("hostname")
db_database_name = cfg['db'].get("database_name")


SQLALCHEMY_DATABASE_URI=f"mysql+asyncmy://{db_username}:{db_password}@{db_hostname}/{db_database_name}?charset=utf8mb4"

async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URI,
    echo=True,
)


AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

Base: DeclarativeMeta = declarative_base()

