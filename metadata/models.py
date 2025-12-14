from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from .database import Base

class File(Base):
    __tablename__ = "files"
    id = Column(String, primary_key=True)
    filename = Column(String)
    size = Column(Integer)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(String, primary_key=True)
    file_id = Column(String, ForeignKey("files.id"))
    index = Column(Integer)
    replica_nodes = Column(JSON)  # ["http://localhost:8001", "http://localhost:8002"]
