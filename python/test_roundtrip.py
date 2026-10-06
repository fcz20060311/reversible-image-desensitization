import cv2
import numpy as np
import os

from pipeline import encrypt_sensitive, decrypt_sensitive, KEY

# 1) 读一张带车牌（可能还有文字）的图
img = cv2.imread("test_picture/sample_car.jpg")
if img is None:
    print("没找到 test_picture/sample_car.jpg")
    exit(1)

# 2) 图太大就等比缩小（纯 Python 加密慢，小图跑得快）
max_side = 512
h, w = img.shape[:2]
if max(h, w) > max_side:
    s = max_side / max(h, w)
    img = cv2.resize(img, (int(w * s), int(h * s)))

print("处理图尺寸:", img.shape)

# 3) 加密 → 拿到脱敏图和框列表
enc, boxes = encrypt_sensitive(img, KEY)
print(f"检测并合并后得到 {len(boxes)} 个框: {boxes}")

# 4) 用同样的框解密
dec = decrypt_sensitive(enc, boxes, KEY)
print("解密后与原图逐像素一致?", np.array_equal(img, dec))

# 5) 保存三张图，方便肉眼看
os.makedirs("out_picture", exist_ok=True)
cv2.imwrite("out_picture/sens_original.png", img)
cv2.imwrite("out_picture/sens_encrypted.png", enc)
cv2.imwrite("out_picture/sens_decrypted.png", dec)
print("已保存 out_picture/sens_original / sens_encrypted / sens_decrypted")