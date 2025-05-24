# Moondream 2B API 文档

## 概述

Moondream 2B 是一个轻量级的视觉语言模型，支持四种推理模式：

1. **描述模式 (describe)** - 生成图像的详细描述
2. **定位模式 (ground)** - 在图像中定位指定对象
3. **点击模式 (point)** - 基于点击位置回答问题
4. **问答模式 (answer)** - 回答关于图像的自由形式问题

## API 端点

基础 URL: `http://localhost:8001/api/v1/moondream`

### 1. 图像描述 - `/describe`

**方法**: POST

**参数**:
- `file` (required): 图像文件
- `compile` (optional, default=false): 是否编译模型加速
- `return_image` (optional, default=false): 是否返回标注图像

**示例**:
```bash
curl -X POST http://localhost:8001/api/v1/moondream/describe \
  -F "file=@image.jpg" \
  -F "compile=false" \
  -F "return_image=true"
```

**响应**:
```json
{
  "mode": "describe",
  "description": "A detailed description of the image...",
  "annotated_image": "base64_encoded_image" // 如果 return_image=true
}
```

### 2. 对象定位 - `/ground`

**方法**: POST

**参数**:
- `file` (required): 图像文件
- `object_name` (required): 要定位的对象名称
- `compile` (optional, default=false): 是否编译模型
- `return_image` (optional, default=false): 是否返回标注图像

**示例**:
```bash
curl -X POST http://localhost:8001/api/v1/moondream/ground \
  -F "file=@image.jpg" \
  -F "object_name=person" \
  -F "compile=false"
```

**响应**:
```json
{
  "mode": "ground",
  "object": "person",
  "bboxes": [[x1, y1, x2, y2], ...],
  "confidence": [0.9, ...]
}
```

### 3. 点击查询 - `/point`

**方法**: POST

**参数**:
- `file` (required): 图像文件
- `point_data` (required): JSON 格式的点击数据
  - `x`: X 坐标
  - `y`: Y 坐标
  - `question`: 关于该位置的问题
- `compile` (optional, default=false): 是否编译模型
- `return_image` (optional, default=false): 是否返回标注图像

**示例**:
```bash
curl -X POST http://localhost:8001/api/v1/moondream/point \
  -F "file=@image.jpg" \
  -F 'point_data={"x":100,"y":200,"question":"What is this?"}' \
  -F "compile=false"
```

**响应**:
```json
{
  "mode": "point",
  "point": [100, 200],
  "question": "What is this?",
  "answer": "This is a..."
}
```

### 4. 视觉问答 - `/answer`

**方法**: POST

**参数**:
- `file` (required): 图像文件
- `question` (required): 关于图像的问题
- `compile` (optional, default=false): 是否编译模型
- `return_image` (optional, default=false): 是否返回原图像

**示例**:
```bash
curl -X POST http://localhost:8001/api/v1/moondream/answer \
  -F "file=@image.jpg" \
  -F "question=How many people are in this image?" \
  -F "compile=false"
```

**响应**:
```json
{
  "mode": "answer",
  "question": "How many people are in this image?",
  "answer": "There are 3 people in the image..."
}
```

### 5. 健康检查 - `/health`

**方法**: GET

**示例**:
```bash
curl http://localhost:8001/api/v1/moondream/health
```

**响应**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "transformers_available": true
}
```

## 配置

模型路径在 `app/config/config.yaml` 中配置：

```yaml
models:
  moondream:
    model: /path/to/moondream/model
```

## 注意事项

1. 首次加载模型可能需要一些时间
2. 设置 `compile=true` 可以加速推理，但首次编译会较慢
3. 模型返回的边界框格式为 `[x1, y1, x2, y2]`
4. 所有端点都支持常见图像格式（JPEG, PNG 等）

## 测试

运行测试脚本：
```bash
python test/test_moondream_api.py
```