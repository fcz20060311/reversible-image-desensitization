"""量化评测：可逆性（无损率）+ 速度（每张耗时）"""
import os
import time

import cv2
import numpy as np

from pipeline import KEY, decrypt_sensitive, encrypt_sensitive

test_dir = "test_picture"
exts = (".jpg", ".jpeg", ".png", ".bmp")

paths = []
for root, _, files in os.walk(test_dir):
    for f in files:
        if f.lower().endswith(exts):
            paths.append(os.path.join(root, f))

print(f"共找到 {len(paths)} 张测试图\n")


def load_resize(p):
    img = cv2.imread(p)
    if img is None:
        return None
    h, w = img.shape[:2]
    if max(h, w) > 512:
        s = 512 / max(h, w)
        img = cv2.resize(img, (int(w * s), int(h * s)))
    return img


# 预热：处理一张，触发 YOLO/EasyOCR 模型加载（不计时）
if paths:
    warm = load_resize(paths[0])
    if warm is not None:
        encrypt_sensitive(warm, KEY)
    print("模型已预热\n")

lossless = 0
n = 0
enc_times = []
dec_times = []
region_counts = []

for p in paths:
    img = load_resize(p)
    if img is None:
        print(f"跳过（读不了）: {p}")
        continue

    t0 = time.perf_counter()
    enc, boxes = encrypt_sensitive(img, KEY)
    t1 = time.perf_counter()
    dec = decrypt_sensitive(enc, boxes, KEY)
    t2 = time.perf_counter()

    ok = np.array_equal(img, dec)
    n += 1
    if ok:
        lossless += 1
    enc_times.append(t1 - t0)
    dec_times.append(t2 - t1)
    region_counts.append(len(boxes))
    print(f"{os.path.basename(p):30s} 区域={len(boxes):2d}  无损={ok}")

print("\n===== 评测结果 =====")
print(f"可逆性（无损率）: {lossless}/{n} = {lossless / n * 100:.1f}%")
print(f"平均检测区域: {sum(region_counts) / n:.1f} 个/张")
print(f"平均加密(含检测)耗时: {sum(enc_times) / n * 1000:.1f} ms/张")
print(f"平均解密耗时: {sum(dec_times) / n * 1000:.1f} ms/张")
