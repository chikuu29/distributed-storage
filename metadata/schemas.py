from pydantic import BaseModel
from typing import List

class FileCreate(BaseModel):
    id: str
    filename: str
    size: int

class ChunkCreate(BaseModel):
    id: str
    file_id: str
    index: int
    replica_nodes: List[str]
