"""人脸框对比：基线 vs 不规则 —— 放大看块结构 + 缩略图指标"""
import cv2
import numpy as np
import tpe
import irregular_tpe as it

KEY = "357538782F413F4428472B4B6250655368566D59703373367639792442264528"
img = cv2.imread("test_picture/obama.jpg")
h, w = img.shape[:2]
s = 400 / max(h, w)
img = cv2.resize(img, (int(w * s), int(h * s)))

x1, y1, x2, y2 = 129, 34, 209, 138          # 已知人脸框
crop = img[y1:y2, x1:x2]
base_enc, _ = tpe.encrypt_image(crop, 8, KEY)
irr_enc, _ = it.encrypt_image_irregular(crop, KEY)

# 放大 3 倍（最近邻），把「块」的结构暴露出来
zoom = lambda a: cv2.resize(a, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
cv2.imwrite("_box_orig.png", zoom(crop))
cv2.imwrite("_box_base.png", zoom(base_enc))
cv2.imwrite("_box_irr.png", zoom(irr_enc))

# 缩略图相似度（越低=低频结构破坏越狠=越看不清）
def thumb_mae(a, b, s):
    ta = cv2.resize(a, (s, s), interpolation=cv2.INTER_AREA)
    tb = cv2.resize(b, (s, s), interpolation=cv2.INTER_AREA)
    return float(np.abs(ta.astype(int) - tb.astype(int)).mean())

print("人脸框尺寸:", crop.shape)
print("基线   人脸框缩略图 MAE:", round(thumb_mae(crop, base_enc, 16), 2))
print("不规则 人脸框缩略图 MAE:", round(thumb_mae(crop, irr_enc, 16), 2))
print("已保存放大 3 倍图: _box_orig / _box_base / _box_irr")
