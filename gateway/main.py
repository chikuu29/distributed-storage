from fastapi import FastAPI, UploadFile
from fastapi.responses import Response
import httpx
import uuid
import math

app = FastAPI()

STORAGE_NODES = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

METADATA_URL = "http://localhost:8000"   # metadata server

CHUNK_SIZE = 1024 * 1024 * 2  # 2 MB


@app.post("/upload")
async def upload_file(file: UploadFile):

    file_id = str(uuid.uuid4())
    content = await file.read()
    print("Content length:", content)
    print(f"Uploading file: {file.filename}, size: {len(content)} bytes")
    total_size = len(content)
    total_chunks = math.ceil(total_size / CHUNK_SIZE)

    # save file metadata
    async with httpx.AsyncClient() as client:
        await client.post(f"{METADATA_URL}/files", json={
            "id": file_id,
            "filename": file.filename,
            "size": total_size
        })

    # chunk upload
    for idx in range(total_chunks):
        chunk_id = str(uuid.uuid4())
        start = idx * CHUNK_SIZE
        end = start + CHUNK_SIZE
        chunk_data = content[start:end]

        # pick replica nodes
        selected_nodes = STORAGE_NODES[:2]  # first two as replicas

        # upload chunk to nodes
        for node in selected_nodes:
            async with httpx.AsyncClient() as client:
                await client.put(
                    f"{node}/chunks/{chunk_id}",
                    files={"file": chunk_data}
                )

        # save chunk metadata
        async with httpx.AsyncClient() as client:
            await client.post(f"{METADATA_URL}/chunks", json={
                "id": chunk_id,
                "file_id": file_id,
                "index": idx,
                "replica_nodes": selected_nodes
            })

    return {"file_id": file_id, "status": "uploaded"}


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    async with httpx.AsyncClient() as client:
        chunks = (await client.get(f"{METADATA_URL}/chunks/{file_id}")).json()

    final_data = b""
    print("Chunks metadata:", chunks)
    # download chunks in order
    for c in sorted(chunks, key=lambda x: x["index"]):
        for node in c["replica_nodes"]:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{node}/chunks/{c['id']}")
                    if resp.status_code == 200:
                        print("resp.content",resp.content)
                        print(f"Downloaded chunk {c['id']} from {node}")
                        final_data += resp.content
                        break
            except:
                continue

    # Return the assembled bytes as a binary response with a download header
    return Response(content=final_data, media_type="application/octet-stream", headers={
        "Content-Disposition": f"attachment; filename=\"{file_id}\""
    })
