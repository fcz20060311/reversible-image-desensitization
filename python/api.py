import base64
import hashlib
import io
import uuid
import os
from typing import List

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from codec import _decode_png_with_boxes, _encode_png_with_boxes
from pipeline import KEY, gen_key, decrypt_sensitive, encrypt_sensitive
app = FastAPI(title="AI 可逆脱敏系统", description="上传照片，自动脱敏人脸、车牌等敏感信息，可无损还原")

# 允许前端跨域调用（开发阶段放行所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Job-Id", "X-Region-Count"],
)

# 内存存储：job_id -> 人脸框列表（真实系统应存数据库）
JOBS = {}
BATCHES = {}

def _save_batch(key, names, pngs):
    """把一批脱敏结果保存到 out_picture/test_N/，并写密钥.txt，返回文件夹名"""
    os.makedirs("out_picture", exist_ok=True)
    nums = []
    for d in os.listdir("out_picture"):
        if d.startswith("test_") and d[5:].isdigit():
            nums.append(int(d[5:]))
    n = max(nums, default=0) + 1
    folder = os.path.join("out_picture", f"test_{n}")
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join(folder, "密钥.txt"), "w", encoding="utf-8") as f:
        f.write(key + "\n")

    for name, png in zip(names, pngs):
        safe = os.path.basename(name)
        with open(os.path.join(folder, safe), "wb") as f:
            f.write(png)

    return folder

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

    enc, boxes = encrypt_sensitive(img, KEY)
    job_id = str(uuid.uuid4())
    JOBS[job_id] = boxes

    ok, buf = cv2.imencode(".png", enc)
    return StreamingResponse(
        io.BytesIO(buf.tobytes()),
        media_type="image/png",
        headers={"X-Job-Id": job_id, "X-Region-Count": str(len(boxes))},
    )


@app.post("/restore")
async def restore(job_id: str, file: UploadFile = File(...)):
    """上传脱敏图 + job_id，还原出原图"""
    boxes = JOBS.get(job_id)
    if boxes is None:
        return JSONResponse({"error": "无效的 job_id，找不到对应的敏感区域"}, status_code=400)

    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return JSONResponse({"error": "无法解析图片"}, status_code=400)

    dec = decrypt_sensitive(img, boxes, KEY)
    ok, buf = cv2.imencode(".png", dec)
    return StreamingResponse(io.BytesIO(buf.tobytes()), media_type="image/png")

@app.post("/batch_desensitize")
async def batch_desensitize(files: List[UploadFile] = File(...)):
    """批量脱敏：一次收多张图，生成一把共享密钥，框写进图片元数据"""
    key = gen_key()
    images = []

    for f in files:
        data = await f.read()
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return JSONResponse({"error": f"无法解析 {f.filename}"}, status_code=400)

        h, w = img.shape[:2]
        if max(h, w) > 512:
            s = 512 / max(h, w)
            img = cv2.resize(img, (int(w * s), int(h * s)))

        enc, boxes = encrypt_sensitive(img, key)

        png_bytes = _encode_png_with_boxes(enc, boxes, key)
        images.append({
            "filename": f.filename,
            "region_count": len(boxes),
            "image_base64": base64.b64encode(png_bytes).decode("ascii"),
        })

    return {"key": key, "images": images}

@app.post("/batch_restore")
async def batch_restore(key: str = Form(...), files: List[UploadFile] = File(...)):
    """批量还原：逐张处理，失败的单独标注，不影响其它张"""
    results = []
    for f in files:
        try:
            data = await f.read()
            img, boxes, key_sha256 = _decode_png_with_boxes(data)

            if hashlib.sha256(key.encode("ascii")).hexdigest() != key_sha256:
                results.append({"filename": f.filename, "ok": False, "error": "密钥错误"})
                continue

            dec = decrypt_sensitive(img, boxes, key)
            ok, buf = cv2.imencode(".png", dec)
            results.append({
                "filename": f.filename,
                "ok": True,
                "image_base64": base64.b64encode(buf.tobytes()).decode("ascii"),
            })
        except Exception:
            results.append({"filename": f.filename, "ok": False, "error": "无法解析或还原"})

    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
