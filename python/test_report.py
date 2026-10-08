"""测试 /report 接口：把一张图发给后端，让 LLM 生成风险报告"""
import requests

BASE = "http://127.0.0.1:8000"

# 换一张你 test_picture 里的图（最好带文字，比如身份证/名片/路牌，最能看出效果）
path = "test_picture/sample_car.jpg"

with open(path, "rb") as f:
    files = [("files", (path, f.read(), "image/jpeg"))]

resp = requests.post(f"{BASE}/report", files=files)
print("状态码:", resp.status_code)
if resp.status_code == 200:
    print("LLM 报告：\n")
    print(resp.json()["report"])
else:
    print("返回：", resp.json())
