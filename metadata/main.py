from fastapi import FastAPI
from .database import Base, engine, SessionLocal
from .models import File, Chunk
from .schemas import FileCreate, ChunkCreate

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/files")
def create_file(file: FileCreate):
    db = SessionLocal()
    db_file = File(**file.dict())
    db.add(db_file)
    db.commit()
    return {"status": "file created"}

@app.post("/chunks")
def create_chunk(chunk: ChunkCreate):
    db = SessionLocal()
    db_chunk = Chunk(**chunk.dict())
    db.add(db_chunk)
    db.commit()
    return {"status": "chunk created"}

@app.get("/chunks/{file_id}")
def get_chunks(file_id: str):
    db = SessionLocal()
    chunks = db.query(Chunk).filter(Chunk.file_id == file_id).all()
    # Convert ORM objects to JSON-serializable dicts
    result = []
    for c in chunks:
        result.append({
            "id": c.id,
            "file_id": c.file_id,
            "index": c.index,
            "replica_nodes": c.replica_nodes,
        })
    return result
