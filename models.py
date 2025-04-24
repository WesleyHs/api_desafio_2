from sqlalchemy import Column, Integer, String, JSON
from database import Base

class BancoApi(Base):
    __tablename__ = 'api'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    name = Column(String(250))
    orders = Column(JSON) 