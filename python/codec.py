import hashlib
import io
import json

import cv2
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

def _encode_png_with_boxes(img_bgr, boxes, key):
    """把 BGR 图编码成 PNG 字节，并把框 + 密钥指纹写进 PNG 元数据"""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    meta = PngInfo()
    meta.add_text("boxes", json.dumps(boxes))
    meta.add_text("key_sha256", hashlib.sha256(key.encode("ascii")).hexdigest())
    buf = io.BytesIO()
    pil.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def _decode_png_with_boxes(data):
    """把 PNG 字节还原成 BGR 图 + 框 + 密钥指纹"""
    pil = Image.open(io.BytesIO(data))
    boxes = json.loads(pil.info.get("boxes", "[]"))
    key_sha256 = pil.info.get("key_sha256", "")
    rgb = pil.convert("RGB")
    bgr = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
    return bgr, boxes, key_sha256