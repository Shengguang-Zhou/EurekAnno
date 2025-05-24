# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

EurekAnno 是一个基于 YOLOe 的智能物体检测与分割系统，提供三种检测模式：
1. 无提示检测 - 使用 4,500+ 内置类别
2. 文本提示检测 - 使用自定义文本类别名称
3. 图像提示检测 - 使用视觉示例进行检测

## 常用命令

### 后端开发
```bash
# 启动后端服务器
python main.py  # 默认运行在 http://0.0.0.0:8000

# 运行测试脚本
python test/test_yoloe_api.py

# 安装依赖
pip install -r requirements.txt
```

### 前端开发
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start  # 运行在 http://localhost:3000

# 构建生产版本
npm run build

# 运行 lint 检查
npm run lint

# 运行测试
npm test
```

## 项目架构

### 后端架构
- **FastAPI 应用**: 主入口在 `main.py`，路由定义在 `router/router.py`
- **YOLOe 推理引擎**: 
  - `app/cv/inference/yolo/yoloe.py` - 核心推理实现
  - `app/cv/inference/yolo/yolo_world.py` - YOLO World 模型支持
  - `app/api/yoloe.py` - API 端点实现
- **模型配置**: `app/config/config.yaml` 定义模型路径
- **模型权重**: 存储在 `/weights/` 目录
  - `yoloe-11s-seg.pt` - 标准分割模型
  - `yoloe-11l-seg-pf.pt` - 无提示检测模型

### 前端架构
- **React 18 + Material UI**: 现代化 UI 框架
- **React Konva**: 用于标注画布的交互式图形库
- **组件结构**:
  - `ImageUploader.jsx` - 图片上传功能
  - `AnnotationCanvas.jsx` - 核心标注画布
  - `TextPromptPanel.jsx` - 文本提示界面
  - `ImagePromptPanel.jsx` - 图像提示界面
  - `PromptFreePanel.jsx` - 无提示检测界面
- **状态管理**: 使用 React Context API (`AppContext.jsx`)
- **API 集成**: `api/yoloeApi.js` 封装所有 API 调用

### API 结构
三个主要端点，都支持实例分割和边界框检测：
- `/api/v1/yoloe/prompt-free` - 无提示检测
- `/api/v1/yoloe/text-prompt` - 文本提示检测
- `/api/v1/yoloe/image-prompt` - 图像提示检测
- `/api/v1/yoloe/export/yolo` - 导出 YOLO 格式标注
- `/api/v1/yoloe/export/yolo-batch` - 批量导出标注

## 开发注意事项

1. **模型路径**: 配置在 `app/config/config.yaml`，使用绝对路径
2. **前端代理**: 前端开发时通过 `package.json` 中的 proxy 配置连接后端
3. **图像格式**: API 支持常见图像格式（JPEG、PNG 等）
4. **掩码生成**: 设置 `retina_masks=true` 获取高质量分割掩码
5. **测试**: 使用 `test/test_yoloe_api.py` 进行 API 测试

## 依赖要求

- Python 3.10+
- PyTorch 2.5+
- CUDA GPU（推荐）
- Node.js 16+
- 4GB+ VRAM