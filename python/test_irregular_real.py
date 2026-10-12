"""真实图片对比测试：基线 TPE（8x8 块保和）vs 不规则 TPE（稀疏锚点 + 区域打散）

验证三件事：
  1) 不规则 TPE 能无损还原
  2) 密文与原图的差异（差异越大 = 打散越狠 = 越看不清）
  3) 保存对比图，供人工查看
"""
import numpy as np
import cv2
import time
import tpe
import irregular_tpe as it

KEY = "357538782F413F4428472B4B6250655368566D59703373367639792442264528"
SIZE = 256   # 统一缩到 256x256（方便对比、也加快速度）

path = "test_picture/obama.jpg"
img = cv2.imread(path, cv2.IMREAD_COLOR)
img = cv2.resize(img, (SIZE, SIZE))
print("图片尺寸:", img.shape)

# 基线 TPE
t0 = time.time()
base_enc, _ = tpe.encrypt_image(img, 8, KEY)
print(f"基线  TPE 加密耗时: {time.time() - t0:.2f}s")

# 不规则 TPE
t0 = time.time()
irr_enc, _ = it.encrypt_image_irregular(img, KEY, cell_size=2, anchor_stride=2, target_area=256)
print(f"不规则TPE 加密耗时: {time.time() - t0:.2f}s")

# 不规则解密，验证无损
irr_dec, _ = it.decrypt_image_irregular(irr_enc, KEY, cell_size=2, anchor_stride=2, target_area=256)
print("不规则 TPE 无损还原:", np.array_equal(img, irr_dec))

# 密文与原图差异（越大越看不清）
mae_base = float(np.abs(base_enc.astype(int) - img.astype(int)).mean())
mae_irr = float(np.abs(irr_enc.astype(int) - img.astype(int)).mean())
print(f"基线  TPE 密文与原图 MAE: {mae_base:.1f}")
print(f"不规则TPE 密文与原图 MAE: {mae_irr:.1f}")

cv2.imwrite("_cmp_orig.png", img)
cv2.imwrite("_cmp_base.png", base_enc)
cv2.imwrite("_cmp_irr.png", irr_enc)
print("已保存: _cmp_orig.png / _cmp_base.png / _cmp_irr.png")
