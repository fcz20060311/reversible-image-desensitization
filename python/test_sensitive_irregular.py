"""完整链路测试：检测敏感区 → 不规则加密 → 还原，验证无损"""
import cv2
import numpy as np
import time
from pipeline import encrypt_sensitive, decrypt_sensitive, KEY

img = cv2.imread("test_picture/obama.jpg")
h, w = img.shape[:2]
s = 400 / max(h, w)
img = cv2.resize(img, (int(w * s), int(h * s)))
print("尺寸:", img.shape)

t0 = time.time()
enc, boxes = encrypt_sensitive(img, KEY)
t1 = time.time()
print(f"检测+加密耗时: {t1 - t0:.2f}s")
print(f"敏感框 {len(boxes)} 个: {boxes}")

dec = decrypt_sensitive(enc, boxes, KEY)
print("无损还原?", np.array_equal(img, dec))

cv2.imwrite("_cmp_sens_orig.png", img)
cv2.imwrite("_cmp_sens_enc.png", enc)
print("已保存 _cmp_sens_orig.png / _cmp_sens_enc.png")
