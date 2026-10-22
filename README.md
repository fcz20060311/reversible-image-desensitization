# 可逆图像脱敏系统

Reversible Image Desensitization System

结合敏感区域自动检测、可逆图像变换和用户间照片分享的全栈科研实践项目。目标是在遮蔽敏感细节的同时保留一定的轮廓线索，并支持持有密钥的接收者恢复图像。

**项目状态：持续开发中的研究原型。** 当前已实现图像处理页面、账号体系和照片分享接口，正在完善分享业务和论文算法的工程移植。

## 项目要解决的问题

在团队图片交流、教学素材共享等场景中，分享者希望先隐藏照片中的人脸、车牌和文字，接收者仍能浏览图片的大致内容；需要查看细节时，再使用密钥恢复。

```text
选择图片 → 检测敏感区域 → 可逆脱敏 → 预览与下载
                              ↓
                        指定接收者分享
                              ↓
                  接收者身份校验 + 密钥验证 → 恢复
```

其中，接收者查看和恢复的后端接口已实现，收件箱前端页面尚待接入。

## 当前功能

| 模块 | 已实现内容 | 当前说明 |
| --- | --- | --- |
| 用户账号 | 注册、登录、JWT、查询当前用户、退出登录 | 当前用户接口返回 ID、用户名和昵称 |
| 敏感区域检测 | YuNet 人脸检测、YOLO 车牌检测、EasyOCR 文字检测 | 使用预训练模型，检测效果受图片质量和模型能力影响 |
| 批量脱敏 | 区域脱敏、整图处理、检测框预览、PNG 下载 | 每次批量请求生成一把随机密钥 |
| 批量恢复 | 上传脱敏 PNG 和密钥，逐张返回成功或失败结果 | 支持错误密钥提示 |
| 风险分析 | 展示检测信息，调用大模型生成文字报告 | 需要自行配置大模型接口 |
| 照片分享 | 上传原图、指定接收者、服务端脱敏并保存、返回恢复密钥 | 页面目前使用接收者的数字用户 ID |
| 收件与授权恢复 | 查询当前用户收到的照片，校验接收者身份后调用恢复服务 | 后端接口已实现，前端待完善 |
| 操作日志 | 记录脱敏、恢复、风险分析，提供日志查询页面 | 当前是 Python 本地文件日志，尚未按用户隔离 |

## 算法与科研工作的关系

项目以轮廓级可逆图像脱敏研究为基础，包含两类 Python 实现：

- `python/tpe.py`：规则分块的可逆变换基线，包含保和替换、置换和链式密钥更新等步骤。
- `python/irregular_tpe.py`：稀疏锚点引导的不规则区域版本，包含微单元统计、锚点选择、引导图重建、分区和可逆变换。

当前 Python 分区采用分水岭方案，**尚未完整对齐论文 MATLAB 实验中的分区和合并策略**。完整论文、MATLAB 实验工程及实验数据未包含在本仓库中，论文实验结论不能直接视为当前 Web 版本的评测结果。

算法的不规则分区标签由图像中的引导信息重建；Web 输出仍通过 PNG 元数据携带敏感区域框、处理模式和密钥指纹。因此，“无需单独保存分区标签”不等于“不需要任何辅助信息”。

## 技术栈与架构

| 层次 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite 8、Element Plus、Axios |
| 业务后端 | Java 17、Spring Boot 3.3.4、MyBatis-Plus、JWT |
| 数据存储 | MySQL、服务器本地 PNG 文件 |
| 图像服务 | Python、FastAPI、OpenCV、NumPy、Pillow |
| 检测与报告 | YuNet、Ultralytics YOLO、EasyOCR、可配置的大模型接口 |

```text
Vue 前端
├─ 账号 / 照片分享 ──→ Spring Boot :8080
│                      ├─ MySQL：用户与分享记录
│                      ├─ uploads/：脱敏 PNG
│                      └─ HTTP ──→ FastAPI :8000
└─ 批量脱敏 / 恢复 / 风险分析 / 日志 ──→ FastAPI :8000
                                         ├─ 敏感区域检测
                                         ├─ 可逆变换与 PNG 编解码
                                         └─ 大模型风险报告
```

当前图像处理页面直接访问 Python 服务；账号和分享请求经过 Java 服务。

## 目录结构

```text
.
├─ frontend/                    # Vue 前端
│  └─ src/
│     ├─ App.vue                # 分享、脱敏、风险分析、恢复、日志页面
│     ├─ LoginView.vue          # 登录与注册
│     └─ api.ts                 # 请求封装及类型定义
├─ desensitization-server/      # Spring Boot 业务后端
│  └─ src/main/
│     ├─ java/                  # 用户、分享、Python 服务调用
│     └─ resources/             # 应用配置与 MyBatis Mapper
├─ python/                      # 图像算法与 FastAPI 服务
│  ├─ api.py                    # HTTP 接口
│  ├─ pipeline.py               # 检测与敏感区域处理
│  ├─ tpe.py                    # 规则分块基线
│  ├─ irregular_tpe.py          # 不规则区域可逆变换
│  ├─ codec.py                  # PNG 图像及元数据编解码
│  ├─ llm.py                    # 风险报告接口调用
│  ├─ models/                   # 检测模型权重
│  └─ static/                   # Python 服务的简易页面
└─ docs/                        # 项目笔记
```

测试照片、本地配置、输出图片及上传文件不纳入版本管理。

## 本地运行

以下命令均从仓库根目录开始，使用三个独立终端分别启动服务。当前主要用于本机开发，尚未提供一键部署。

### 1. 准备环境

- Node.js：满足 Vite 8 的要求（`20.19+` 的 20.x，或 `22.12+`）。
- JDK 17、Maven、MySQL。
- Python：当前本地开发环境使用 Python 3.13；其他版本需确认 PyTorch、Ultralytics 和 EasyOCR 的依赖兼容性。

### 2. 配置与启动 Python 服务

```powershell
cd python
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install fastapi uvicorn python-multipart numpy opencv-python pillow requests ultralytics easyocr
```

仓库暂未提供锁定版本的 Python 依赖清单；以上命令列出服务使用的主要依赖。

在 `python/` 下自行创建 `config.py`：

```python
API_KEY = "替换为自己的 API Key"
BASE_URL = "https://your-provider.example/v1/chat/completions"
MODEL = "替换为服务商提供的模型名称"
```

`BASE_URL` 应填写完整的聊天补全接口地址。当前服务启动时会导入此配置，因此即使暂时不使用风险分析，也需要提供这三个变量；实际调用报告功能时才需要可用的凭据。`config.py` 已被 Git 忽略。

确认以下模型文件存在：

```text
python/models/face_detection_yunet.onnx
python/models/license_plate.pt
python/models/easyocr/model/craft_mlt_25k.pth
python/models/easyocr/model/zh_sim_g2.pth
```

在 `python/` 目录启动，保证模型和静态文件的相对路径正确：

```powershell
.\.venv\Scripts\python.exe api.py
```

服务地址：<http://127.0.0.1:8000>；交互接口文档：<http://127.0.0.1:8000/docs>。

### 3. 配置与启动 Java 服务

当前仓库未提供独立 SQL 初始化文件。下面是依据现有实体和查询整理的最小建表示例，可在新的本地数据库中执行：

```sql
CREATE DATABASE IF NOT EXISTS desensitization
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE desensitization;

CREATE TABLE IF NOT EXISTS `user` (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(20) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  nickname VARCHAR(100),
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS photo_share (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  sender_id BIGINT NOT NULL,
  receiver_id BIGINT NOT NULL,
  filename VARCHAR(255) NOT NULL,
  file_path VARCHAR(512) NOT NULL,
  key_sha256 CHAR(64) NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_receiver_time (receiver_id, create_time)
);
```

按照自己的环境修改 `desensitization-server/src/main/resources/application.yml` 中的 MySQL 地址、用户名和密码；`python.base-url` 默认是 `http://127.0.0.1:8000`。如果需要上传较大的源文件，可在 `spring` 下配置 `servlet.multipart.max-file-size` 和 `servlet.multipart.max-request-size`。

```powershell
cd desensitization-server
mvn spring-boot:run
```

业务服务地址：<http://127.0.0.1:8080>。分享生成的 PNG 保存在 Java 服务工作目录的 `uploads/` 中。

### 4. 启动前端

```powershell
cd frontend
npm ci
npm run dev
```

浏览器打开终端显示的地址，通常为 <http://localhost:5173>。先注册账号再登录。

前端服务地址目前定义在 `frontend/src/api.ts` 中：Python 为 `http://127.0.0.1:8000`，Java 为 `http://127.0.0.1:8080`。更改端口时需要同步修改。

## 使用流程

1. **脱敏与恢复**：登录后选择图片，选择区域脱敏或整图处理，保存密钥并下载脱敏 PNG；在恢复页上传该 PNG 并输入对应密钥。
2. **照片分享**：准备两个已注册账号，在分享页输入接收者用户 ID、上传原图并提交，保存返回的密钥。当前接收者需通过后端收件和恢复接口操作。
3. **风险分析**：配置可用的大模型接口后上传图片，查看检测结果和文字报告。
4. **日志查看**：在审计日志页主动加载最近的处理记录。

恢复时应使用下载的脱敏 PNG。截图、转成 JPEG、编辑像素或移除 PNG 元数据都会影响恢复；检测框预览图用于查看定位结果，不应作为恢复输入。

## 主要接口

Java 服务：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/api/user/register` | 注册 |
| POST | `/api/user/login` | 登录并返回 Token |
| GET | `/api/user/me` | 查询当前用户 |
| POST | `/api/photo/share` | 分享图片，表单字段为 `receiverId`、`file` |
| GET | `/api/photo/inbox` | 查询当前接收者的分享记录 |
| POST | `/api/photo/{id}/decrypt` | 恢复收到的图片，表单字段为 `key` |

除注册和登录外，上述 Java 接口需要 `Authorization` 请求头。**当前实现直接传入 Token 字符串，不加 `Bearer ` 前缀。** 业务响应采用 `{ code, msg, data }`，`code = 1` 表示成功。

Python 服务：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/batch_desensitize` | 批量脱敏，表单字段为 `files`、`mode`（`region` / `whole`） |
| POST | `/batch_restore` | 批量恢复，表单字段为 `files`、`key` |
| POST | `/report` | 风险分析，表单字段为 `file` |
| GET | `/audit` | 查询本地处理日志，可传 `limit` |

`/desensitize` 与 `/restore` 是保留的早期单图接口，采用固定演示密钥和内存任务记录；当前 Vue 处理页面使用批量接口。

## 验证入口

前端类型检查与构建：

```powershell
cd frontend
npm run build
```

Python 不规则变换的内置自检，可在 `python/` 下运行：

```powershell
.\.venv\Scripts\python.exe irregular_tpe.py
```

敏感区域往返处理示例：自行准备 `python/test_picture/sample_car.jpg`，在 `python/` 下运行 `test_roundtrip.py`，检查输出中的逐像素一致性结果。该示例依赖检测模型；测试图片未随仓库分发。现有脚本属于开发验证入口，尚未整理成统一自动化测试套件。

## 当前边界与后续计划

- **恢复范围**：当前 Web 接口会把最长边超过 512 像素的图片等比缩小。恢复目标是处理前的缩放后图像，不是上传文件的原始分辨率、编码字节或 EXIF 信息。
- **检测与隐私效果**：自动检测可能漏检；保留轮廓与隐藏细节之间的取舍仍需专项评测，不能仅凭密文外观或恢复成功判断隐私保护强度。
- **访问与数据处理**：Python 接口目前未统一鉴权；本地日志也未隔离用户。风险报告会把检测信息（包括 OCR 文字）发送至配置的大模型服务。当前适合本地研究与演示。
- **部署完善**：密码存储、JWT 配置、跨域策略、文件与元数据完整性保护、密钥使用策略等仍需进一步完善。

后续方向（尚未完成，具体安排随开发调整）：

- [ ] 使用唯一公开身份编码查找接收者，并在发送前确认身份。
- [ ] 完善分享页面、收件箱、已发送记录与恢复下载流程。
- [ ] 增加敏感区域人工复核与修正。
- [ ] 对齐论文算法，整理可复现的评测与对比实验。
- [ ] 统一服务鉴权、用户日志隔离和错误处理。
- [ ] 补充独立数据库初始化脚本、依赖锁定与部署说明。

## 资源说明

本项目使用第三方预训练模型和开源依赖，使用与再分发前应分别核对其来源和许可。请使用拥有处理权限的测试图片，本地凭据和个人照片不应提交到仓库。
