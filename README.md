# EurekAnno - 智能物体检测与分割系统

EurekAnno 是一个基于 YOLOe 的高级物体检测和分割平台，支持三种不同的推理方式：

1. **无提示检测** - 利用 YOLOe 内置的 4,500+ 类词汇表自动识别物体
2. **文本提示检测** - 使用您指定的文本提示/类别名称进行检测
3. **图像提示检测** - 通过参考图像中的视觉示例进行智能检测

## 核心功能

- **强大高效**：基于最先进的 YOLOe 检测架构
- **多模态提示**：支持文本提示、图像提示或无提示检测模式
- **实例分割**：提供精确的像素级物体分割掩码
- **高度定制**：可根据具体应用场景调整检测参数
- **易于集成**：RESTful API 设计，轻松集成到各种应用中
- **前端界面**：提供直观的用户界面进行标注和检测
- **导出功能**：支持将检测结果导出为 YOLO 格式

## 安装指南

### 后端设置

1. 克隆此仓库
2. 安装依赖：
```bash
pip install -r requirements.txt
```
3. 启动服务器：
```bash
python main.py
```

服务器默认在 http://0.0.0.0:8000 上运行。

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```
2. 安装依赖：
```bash
npm install
```
3. 启动开发服务器：
```bash
npm start
```

前端界面将在 http://localhost:3000 上可用。

## API 端点

API 提供以下主要端点：

- **POST /api/v1/yoloe/prompt-free**：无提示检测物体
- **POST /api/v1/yoloe/text-prompt**：使用文本提示检测物体
- **POST /api/v1/yoloe/image-prompt**：使用图像提示检测物体
- **POST /api/v1/yoloe/export/yolo**：导出标注为 YOLO 格式
- **POST /api/v1/yoloe/export/yolo-batch**：批量导出标注为 YOLO 格式
- **WS /api/v1/yoloe-stream/prompt-free**：实时无提示检测
- **WS /api/v1/yoloe-stream/text-prompt**：实时文本提示检测
- **WS /api/v1/yoloe-stream/image-prompt**：实时图像提示检测

详细的 API 文档可在 `/app/api/README.md` 中找到。

## 前端使用说明

前端界面提供了直观的用户体验，包括以下功能：

- 图片上传与管理
- 无提示、文本提示和图像提示三种检测模式
- 交互式标注画布
- 检测结果可视化
- 结果导出功能

有关前端集成与使用的详细教程，请参考 `FRONTEND_USAGE.md`。

## 系统要求

- Python 3.10
- PyTorch 2.5+
- Node.js 14+ (前端)
- 4GB+ VRAM
- 支持 CUDA 的 GPU (推荐用于生产环境)

## 许可证

© 2024 EurekAILab. 保留所有权利。

