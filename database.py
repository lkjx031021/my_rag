from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from configs.config import load_db_config

# 加载数据库配置
db_config = load_db_config()

# 构建数据库连接 URL
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{db_config.get('username')}:{db_config.get('password')}@"
    f"{db_config.get('hostname')}/{db_config.get('database_name')}"
)

# 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 检查数据库是否存在，如果不存在则创建
if not database_exists(engine.url):
    create_database(engine.url)

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 ORM 模型的基类
Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
