"""调用 LLM 做语义风险判断"""
import requests

# 敏感信息（API Key）在 config.py 里，该文件已被 .gitignore 排除，不会上传
from config import API_KEY, BASE_URL, MODEL


def analyze_with_llm(items):
    """把检测结果喂给 LLM，返回一段风险判断报告"""
    if not items:
        return "未检测到敏感信息。"

    # 1) 把检测结果整理成文字
    lines = []
    for it in items:
        if it["type"] == "人脸":
            lines.append(f"- 人脸：位置 {it['box']}")
        elif it["type"] == "车牌":
            lines.append(f"- 车牌：位置 {it['box']}")
        else:
            lines.append(f"- 文字：位置 {it['box']}，内容「{it.get('content', '')}」")
    detail = "\n".join(lines)

    # 2) 构建提示词
    prompt = (
        "你是隐私合规专家。以下是系统在一张图片中检测到的敏感信息：\n"
        f"{detail}\n\n"
        "请用中文，简洁地：\n"
        "1) 判断每项信息的敏感等级（高/中/低）；\n"
        "2) 说明理由（尤其判断文字内容是否属于身份证号、手机号、银行卡号等个人敏感信息）；\n"
        "3) 给出脱敏建议。\n"
        "控制在 150 字以内。"
    )

    # 3) 调 DeepSeek 接口
    resp = requests.post(
        BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]