from pypdf import PdfReader

path = r"C:\Users\35610\DeskBox\File\学业\比赛\宠物情绪翻译器\2025072887-参赛总文件夹\2025072887-03设计与开发文档\作品报告.pdf"
reader = PdfReader(path)

out = [f"总页数: {len(reader.pages)}"]
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    out.append(f"\n\n===== 第 {i + 1} 页 =====\n{text}")

with open("pet_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("总页数:", len(reader.pages))
print("已写入 pet_report.txt")
