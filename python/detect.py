import cv2

MODEL = "models/face_detection_yunet.onnx"

# 读照片
img = cv2.imread("test_picture/sample.jpg")
if img is None:
    print("没找到 test_picture/sample.jpg")
    exit(1)
h, w = img.shape[:2]

# 创建 YuNet 人脸检测器
detector = cv2.FaceDetectorYN.create(
    MODEL, "", (w, h),
    score_threshold=0.6,
    nms_threshold=0.3,
    top_k=5000,
)
detector.setInputSize((w, h))

# 检测人脸（faces 是 N×15 的数组）
_, faces = detector.detect(img)

boxes = []
if faces is not None:
    for f in faces:
        x, y, bw, bh = int(f[0]), int(f[1]), int(f[2]), int(f[3])
        boxes.append((x, y, x + bw, y + bh))
        cv2.rectangle(img, (x, y), (x + bw, y + bh), (0, 255, 0), 2)

print(f"检测到 {len(boxes)} 张人脸")
for i, box in enumerate(boxes):
    print(f"  人脸 {i+1}: x1={box[0]}, y1={box[1]}, x2={box[2]}, y2={box[3]}")

cv2.imwrite("out_picture/detect_boxes.png", img)
print("已保存 out_picture/detect_boxes.png")
