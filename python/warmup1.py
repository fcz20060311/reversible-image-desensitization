import numpy as np
import cv2
import os

img=np.zeros((256,256,3),dtype=np.uint8)

img[:,:128]=(0,0,255)
img[:,128:]=(255,0,0)

print("形状(高,宽,通道)",img.shape)
print("数据类型",img.dtype)

gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
print("灰度图形状",gray.shape)


OUT_DIR="out_picture"
os.makedirs(OUT_DIR,exist_ok=True)
cv2.imwrite(os.path.join(OUT_DIR,"warmup1.png"),img)
cv2.imwrite(os.path.join(OUT_DIR,"warmup1_gray.png"),gray)
print("已保存 warmup1.png")


