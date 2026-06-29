'''
This file is to get the DB connection
'''

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings


url = settings.async_database_url
engine = create_async_engine(url)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False) #the expire on commit is due to fix async in SQLAlchemy since without it it will expire all ORM attributes after a commit

class Base(DeclarativeBase):
    pass


'''
Get DB is a FastAPI dependency that yields a session per request and automatically closes when the request is done
'''
async def get_db():
    async with async_session_factory() as session:
        yield session