from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI()
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


@app.put("/chunks/{chunk_id}")
async def upload_chunk(chunk_id: str, file: UploadFile):
    filepath = os.path.join(DATA_DIR, chunk_id)
    # Ensure bytes are written
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return {"status": "stored", "chunk_id": chunk_id}


@app.get("/chunks/{chunk_id}")
def download_chunk(chunk_id: str):
    filepath = os.path.join(DATA_DIR, chunk_id)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="not found")
    # Serve the chunk as a file response with explicit binary content type
    return FileResponse(filepath, media_type="application/octet-stream")
