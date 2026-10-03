import io
import uuid

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from pipeline import KEY, decrypt_faces, encrypt_faces

app = FastAPI(title="AI 可逆脱敏系统", description="上传照片，自动脱敏人脸，可无损还原")

# 允许前端（5173 端口）跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Job-Id", "X-Face-Count"],
)

# 内存存储：job_id -> 人脸框列表（真实系统应存数据库）
JOBS = {}

@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.post("/desensitize")
async def desensitize(file: UploadFile = File(...)):
    """上传照片，返回脱敏图 + job_id（在响应头 X-Job-Id 里）"""
    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return JSONResponse({"error": "无法解析图片，请上传 jpg / png"}, status_code=400)

    h, w = img.shape[:2]
    if max(h, w) > 512:
        s = 512 / max(h, w)
        img = cv2.resize(img, (int(w * s), int(h * s)))

    enc, boxes = encrypt_faces(img, KEY)
    job_id = str(uuid.uuid4())
    JOBS[job_id] = boxes

    ok, buf = cv2.imencode(".png", enc)
    return StreamingResponse(
        io.BytesIO(buf.tobytes()),
        media_type="image/png",
        headers={"X-Job-Id": job_id, "X-Face-Count": str(len(boxes))},
    )


@app.post("/restore")
async def restore(job_id: str, file: UploadFile = File(...)):
    """上传脱敏图 + job_id，还原出原图"""
    boxes = JOBS.get(job_id)
    if boxes is None:
        return JSONResponse({"error": "无效的 job_id，找不到对应的人脸框"}, status_code=400)

    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return JSONResponse({"error": "无法解析图片"}, status_code=400)

    dec = decrypt_faces(img, boxes, KEY)
    ok, buf = cv2.imencode(".png", dec)
    return StreamingResponse(io.BytesIO(buf.tobytes()), media_type="image/png")
