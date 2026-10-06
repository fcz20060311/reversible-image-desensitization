"""批量脱敏/还原 后端往返测试"""
import base64
import cv2
import numpy as np
import requests

BASE = "http://127.0.0.1:8000"

# 1) 挑 3 张测试图
paths = [
    "test_picture/sample_car.jpg",
    "test_picture/faces_test/two_people.jpg",
    "test_picture/faces_test/obama.jpg",
]

# 2) 本地也按后端同样的规则缩小，用来做还原后的对比基准
originals = []
for p in paths:
    img = cv2.imread(p)
    h, w = img.shape[:2]
    if max(h, w) > 512:
        s = 512 / max(h, w)
        img = cv2.resize(img, (int(w * s), int(h * s)))
    originals.append(img)

# 3) 批量脱敏
files = []
for p in paths:
    with open(p, "rb") as f:
        files.append(("files", (p.split("/")[-1], f.read(), "image/jpeg")))

resp = requests.post(f"{BASE}/batch_desensitize", files=files)
print("脱敏状态码:", resp.status_code)
data = resp.json()
key = data["key"]
print("生成的密钥:", key)
print("脱敏图数量:", len(data["images"]))
for it in data["images"]:
    print("  ", it["filename"], "→ 检测到", it["region_count"], "个区域")

# 4) 把脱敏图 base64 解回字节，作为还原的输入
enc_files = []
for it in data["images"]:
    raw = base64.b64decode(it["image_base64"])
    enc_files.append(("files", (it["filename"], raw, "image/png")))

# 5) 用正确密钥批量还原
resp2 = requests.post(f"{BASE}/batch_restore", data={"key": key}, files=enc_files)
print("还原状态码:", resp2.status_code)
restored = resp2.json()["images"]

all_ok = True
for i, b64 in enumerate(restored):
    raw = base64.b64decode(b64)
    dec = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    ok = np.array_equal(originals[i], dec)
    print(f"  图{i + 1} 还原后与原图一致? {ok}")
    all_ok = all_ok and ok

print("全部逐像素一致?", all_ok)

# 6) 用错误密钥还原，应返回 400
resp3 = requests.post(f"{BASE}/batch_restore", data={"key": "0" * 64}, files=enc_files)
print("错误密钥状态码:", resp3.status_code, "→", resp3.json())
