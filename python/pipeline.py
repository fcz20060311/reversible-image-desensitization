import cv2
import os
import numpy as np
import secrets
from tpe import encrypt_image, decrypt_image

MODEL = "models/face_detection_yunet.onnx"
PLATE_MODEL = "models/license_plate.pt"
KEY = "357538782F413F4428472B4B6250655368566D59703373367639792442264528"
DIMEN = 8

_plate_model = None  # YOLO 车牌模型（懒加载，只加载一次）
_text_reader = None  # EasyOCR 阅读器（懒加载，只加载一次）

def gen_key():
    return secrets.token_hex(32)


def detect_faces(img):
    """用 YuNet 检测人脸，返回夹在图片内、边长是 8 的倍数的框"""
    h, w = img.shape[:2]
    detector = cv2.FaceDetectorYN.create(MODEL, "", (w, h), score_threshold=0.6)
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)
    boxes = []
    if faces is not None:
        for f in faces:
            x1 = max(0, int(f[0]))
            y1 = max(0, int(f[1]))
            x2 = min(w, int(f[0] + f[2]))
            y2 = min(h, int(f[1] + f[3]))
            # 收缩到 8 的倍数（encrypt 要求）
            x2 = x1 + (x2 - x1) // DIMEN * DIMEN
            y2 = y1 + (y2 - y1) // DIMEN * DIMEN
            if x2 > x1 and y2 > y1:
                boxes.append((x1, y1, x2, y2))
    return boxes


def encrypt_faces(img, key):
    """只加密人脸区域，返回 (脱敏图, 人脸框列表)"""
    out = img.copy()
    boxes = detect_faces(img)
    for (x1, y1, x2, y2) in boxes:
        enc, _ = encrypt_image(img[y1:y2, x1:x2], DIMEN, key)
        out[y1:y2, x1:x2] = enc
    return out, boxes


def decrypt_faces(img, boxes, key):
    """用保存的框，把加密的人脸区域还原"""
    out = img.copy()
    for (x1, y1, x2, y2) in boxes:
        dec, _ = decrypt_image(img[y1:y2, x1:x2], DIMEN, key)
        out[y1:y2, x1:x2] = dec
    return out


def detect_plates(img, conf=0.25):
    """用 YOLO 检测车牌，返回夹在图片内、边长是 8 的倍数的框"""
    global _plate_model
    if _plate_model is None:
        from ultralytics import YOLO
        _plate_model = YOLO(PLATE_MODEL)
    h, w = img.shape[:2]
    results = _plate_model(img, verbose=False)
    boxes = []
    if results and results[0].boxes is not None:
        for box in results[0].boxes:
            if float(box.conf[0]) >= conf:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x1 = max(0, int(x1))
                y1 = max(0, int(y1))
                x2 = min(w, int(x2))
                y2 = min(h, int(y2))
                x2 = x1 + (x2 - x1) // DIMEN * DIMEN
                y2 = y1 + (y2 - y1) // DIMEN * DIMEN
                if x2 > x1 and y2 > y1:
                    boxes.append((x1, y1, x2, y2))
    return boxes

def _merge_boxes(boxes):
    """把有重叠的框合并成一个，避免同一块区域被加密两次导致无法还原"""
    boxes = list(boxes)
    changed = True
    while changed:
        changed = False
        merged = []
        skip = [False] * len(boxes)
        for i in range(len(boxes)):
            if skip[i]:
                continue
            x1, y1, x2, y2 = boxes[i]
            for j in range(i + 1, len(boxes)):
                if skip[j]:
                    continue
                a1, b1, a2, b2 = boxes[j]
                # 判断两个框是否有重叠（有交集就算）
                if x1 < a2 and a1 < x2 and y1 < b2 and b1 < y2:
                    x1, y1 = min(x1, a1), min(y1, b1)
                    x2, y2 = max(x2, a2), max(y2, b2)
                    skip[j] = True
                    changed = True
            merged.append((x1, y1, x2, y2))
        boxes = merged

    # 合并后重新对齐到 8 的倍数（encrypt 要求宽高是 8 的倍数）
    out = []
    for x1, y1, x2, y2 in boxes:
        x2 = x1 + (x2 - x1) // DIMEN * DIMEN
        y2 = y1 + (y2 - y1) // DIMEN * DIMEN
        if x2 > x1 and y2 > y1:
            out.append((x1, y1, x2, y2))
    return out

def detect_text(img):
    """用 EasyOCR 检测文字区域，返回框列表"""
    global _text_reader
    if _text_reader is None:
        import easyocr
        _text_reader = easyocr.Reader(
            ["ch_sim", "en"], gpu=False, verbose=False,
            model_storage_directory="models/easyocr/model",
            user_network_directory="models/easyocr/user_network",
        )
    h, w = img.shape[:2]
    results = _text_reader.readtext(img)
    boxes = []
    for pts, text, conf in results:
        # pts 是四个角点 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]（文字可能是斜的）
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x1 = max(0, int(min(xs)))
        y1 = max(0, int(min(ys)))
        x2 = min(w, int(max(xs)))
        y2 = min(h, int(max(ys)))
        x2 = x1 + (x2 - x1) // DIMEN * DIMEN
        y2 = y1 + (y2 - y1) // DIMEN * DIMEN
        if x2 > x1 and y2 > y1:
            boxes.append((x1, y1, x2, y2))
    return boxes

def analyze_sensitive(img):
    """检测敏感信息，返回详细列表（含文字内容），供 LLM 做语义风险分析"""
    global _text_reader
    if _text_reader is None:
        import easyocr
        _text_reader = easyocr.Reader(
            ["ch_sim", "en"], gpu=False, verbose=False,
            model_storage_directory="models/easyocr/model",
            user_network_directory="models/easyocr/user_network",
        )

    h, w = img.shape[:2]
    items = []

    for box in detect_faces(img):
        items.append({"type": "人脸", "box": list(box)})

    for box in detect_plates(img):
        items.append({"type": "车牌", "box": list(box)})

    for pts, text, conf in _text_reader.readtext(img):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x1 = max(0, int(min(xs)))
        y1 = max(0, int(min(ys)))
        x2 = min(w, int(max(xs)))
        y2 = min(h, int(max(ys)))
        items.append({"type": "文字", "box": [x1, y1, x2, y2], "content": text})

    return items

def detect_sensitive(img):
    """检测所有人脸 + 车牌 + 文字"""
    return _merge_boxes(detect_faces(img) + detect_plates(img) + detect_text(img))

def encrypt_sensitive(img, key):
    """加密所有人脸 + 车牌区域，返回 (脱敏图, 框列表)"""
    out = img.copy()
    boxes = detect_sensitive(img)
    for (x1, y1, x2, y2) in boxes:
        enc, _ = encrypt_image(img[y1:y2, x1:x2], DIMEN, key)
        out[y1:y2, x1:x2] = enc
    return out, boxes


def decrypt_sensitive(img, boxes, key):
    """用保存的框，把敏感区域还原"""
    out = img.copy()
    for (x1, y1, x2, y2) in boxes:
        dec, _ = decrypt_image(img[y1:y2, x1:x2], DIMEN, key)
        out[y1:y2, x1:x2] = dec
    return out


if __name__ == "__main__":
    img = cv2.imread("test_picture/sample.jpg")
    if img is None:
        print("没找到 test_picture/sample.jpg")
        exit(1)

    # 图太大就缩小（纯 Python 加密较慢）
    max_side = 512
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        s = max_side / max(h, w)
        img = cv2.resize(img, (int(w * s), int(h * s)))
    print("处理图尺寸:", img.shape)

    enc, boxes = encrypt_faces(img, KEY)
    print(f"检测并加密了 {len(boxes)} 张人脸")
    for i, b in enumerate(boxes):
        print(f"  人脸 {i+1}: {b}")

    dec = decrypt_faces(enc, boxes, KEY)
    print("解密后与原图一致?", np.array_equal(img, dec))

    os.makedirs("out_picture", exist_ok=True)
    cv2.imwrite("out_picture/face_original.png", img)
    cv2.imwrite("out_picture/face_encrypted.png", enc)
    cv2.imwrite("out_picture/face_decrypted.png", dec)
    print("已保存 3 张图：face_original / face_encrypted / face_decrypted")
