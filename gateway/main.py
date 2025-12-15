
from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import Response,StreamingResponse
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

    # Try to fetch original filename from metadata
    filename = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{METADATA_URL}/files/{file_id}")
            if resp.status_code == 200:
                info = resp.json()
                filename = info.get("filename")
    except Exception:
        filename = None

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

    # Determine media type from filename extension when possible
    media_type = "application/octet-stream"
    if filename:
        lower = filename.lower()
        if lower.endswith('.pdf'):
            media_type = 'application/pdf'
        elif lower.endswith('.txt'):
            media_type = 'text/plain'
        elif lower.endswith('.json'):
            media_type = 'application/json'
        elif lower.endswith('.jpg') or lower.endswith('.jpeg'):
            media_type = 'image/jpeg'
        elif lower.endswith('.png'):
            media_type = 'image/png'

    # Prefer inline disposition for documents so browsers can view them
    disposition = f'inline; filename="{filename or file_id}"'

    return Response(content=final_data, media_type=media_type, headers={
        "Content-Disposition": disposition
    })




@app.get("/files/{file_id}/stream")
async def download_file(file_id: str, request: Request):

    # Fetch chunk metadata
    async with httpx.AsyncClient() as client:
        chunks = (await client.get(f"{METADATA_URL}/chunks/{file_id}")).json()

    # Fetch filename
    filename = file_id
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{METADATA_URL}/files/{file_id}")
            if resp.status_code == 200:
                filename = resp.json().get("filename", file_id)
    except:
        pass

    # Detect Range header
    range_header = request.headers.get("range")
    print("Range header:", range_header)
    start_byte = 0

    if range_header:
        # Example: bytes=1024-
        start_byte = int(range_header.replace("bytes=", "").split("-")[0])

    async def stream_generator():
        nonlocal start_byte
        current_pos = 0

        async with httpx.AsyncClient() as client:
            for chunk in sorted(chunks, key=lambda x: x["index"]):
                for node in chunk["replica_nodes"]:
                    try:
                        resp = await client.get(f"{node}/chunks/{chunk['id']}")
                        if resp.status_code == 200:
                            data = resp.content
                            chunk_len = len(data)

                            # Skip bytes already sent (resume logic)
                            if current_pos + chunk_len <= start_byte:
                                current_pos += chunk_len
                                break

                            # Partial chunk skip
                            if start_byte > current_pos:
                                data = data[start_byte - current_pos:]
                                current_pos = start_byte

                            yield data
                            current_pos += len(data)
                            break
                    except:
                        continue

    # Media type detection
    media_type = "application/octet-stream"
    lower = filename.lower()
    if lower.endswith(".pdf"):
        media_type = "application/pdf"
    elif lower.endswith(".png"):
        media_type = "image/png"
    elif lower.endswith(".jpg") or lower.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif lower.endswith(".txt"):
        media_type = "text/plain"

    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Accept-Ranges": "bytes"
    }

    status_code = 206 if range_header else 200

    return StreamingResponse(
        stream_generator(),
        media_type=media_type,
        headers=headers,
        status_code=status_code
    )