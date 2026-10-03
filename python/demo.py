import numpy as np
import cv2
from tpe import encrypt_image, decrypt_image

# 1) 读照片（把一张照片放到 test_picture/sample.jpg）
img = cv2.imread("test_picture/sample.jpg")
if img is None:
    print("没找到 test_picture/sample.jpg，请先放一张照片进去！")
    exit(1)

# 灰度图统一转成 3 通道
if len(img.shape) == 2:
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

# 2) 图太大就缩到最长边 256（纯 Python 混沌循环较慢，先跑小图）
max_side = 256
h, w = img.shape[:2]
if max(h, w) > max_side:
    s = max_side / max(h, w)
    img = cv2.resize(img, (int(w * s), int(h * s)))

# 3) 裁成 8 的整数倍（加密要求）
h, w = img.shape[:2]
img = img[: (h // 8) * 8, : (w // 8) * 8]

print("处理图尺寸:", img.shape)

# 4) 加密 → 解密
key = "357538782F413F4428472B4B6250655368566D59703373367639792442264528"
enc, _ = encrypt_image(img, 8, key)
dec, _ = decrypt_image(enc, 8, key)

# 5) 验证 + 保存
print("解密后与原图逐像素一致?", np.array_equal(img, dec))
cv2.imwrite("test_picture/demo_original.png", img)
cv2.imwrite("test_picture/demo_encrypted.png", enc)
cv2.imwrite("test_picture/demo_decrypted.png", dec)
print("已保存 3 张图：demo_original / demo_encrypted / demo_decrypted")
