import cv2
import os
import glob

MODEL = "models/face_detection_yunet.onnx"
TEST_DIR = "test_picture/faces_test"

# 参考值：来自 face_recognition 仓库文档（它用的是 dlib 检测器，仅供对照）
EXPECTED = {
    "alex-lacamoire.png": 1,
    "biden.jpg": 1,
    "obama.jpg": 1,
    "obama2.jpg": 1,
    "two_people.jpg": 2,
}


def count_faces(img):
    """返回图片中检测到的人脸数"""
    h, w = img.shape[:2]
    detector = cv2.FaceDetectorYN.create(MODEL, "", (w, h), score_threshold=0.6)
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)
    return 0 if faces is None else len(faces)


files = sorted(glob.glob(os.path.join(TEST_DIR, "*")))
files = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]

print("批量人脸检测测试（YuNet，阈值 0.6）")
print("-" * 56)
match = 0
for f in files:
    name = os.path.basename(f)
    img = cv2.imread(f)
    if img is None:
        print(f"{name}  读取失败")
        continue
    n = count_faces(img)
    exp = EXPECTED.get(name)
    if exp is None:
        mark = "--"
    elif n == exp:
        mark = "一致"
        match += 1
    else:
        mark = "不同"
    print(f"{name:<22} 检测到 {n} 张   参考 {exp} 张   [{mark}]")

print("-" * 56)
print(f"与参考一致: {match} / {len(files)}")
