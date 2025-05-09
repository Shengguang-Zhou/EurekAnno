# YOLOe API 文档

本模块提供了用于 YOLOe 对象检测和分割的 REST API 端点。

## 端点

### 1. `/api/v1/yoloe/prompt-free`

使用 YOLOe 内置词汇表进行无提示对象检测。

**请求:**
```
POST /api/v1/yoloe/prompt-free
```

**参数:**
- `file`: 要分析的图像文件
- `model_path`: 可选模型路径（默认值: "default"）
- `conf`: 置信度阈值（默认值: 0.25）
- `iou`: IoU 阈值（默认值: 0.7）
- `return_image`: 是否返回标注图像（默认值: false）
- `retina_masks`: 是否生成高质量掩码（默认值: false）

**响应:**
```json
{
  "results": {
    "class": ["person", "car", ...],
    "confidence": [0.98, 0.85, ...],
    "bbox": [[x1, y1, x2, y2], ...],
    "masks": [[points], ...] // 如果启用 retina_masks
  },
  "annotated_image": "base64_encoded_image" // 如果 return_image=true
}
```

### 2. `/api/v1/yoloe/text-prompt`

使用用户指定的类别名称进行文本提示对象检测。

**请求:**
```
POST /api/v1/yoloe/text-prompt
```

**参数:**
- `file`: 要分析的图像文件
- `class_names`: 要检测的类别名称列表
- `model_path`: 可选模型路径（默认值: "default"）
- `conf`: 置信度阈值（默认值: 0.25）
- `iou`: IoU 阈值（默认值: 0.7）
- `return_image`: 是否返回标注图像（默认值: false）
- `retina_masks`: 是否生成高质量掩码（默认值: false）

**响应:**
```json
{
  "results": {
    "class": ["person", "car", ...],
    "confidence": [0.98, 0.85, ...],
    "bbox": [[x1, y1, x2, y2], ...],
    "masks": [[points], ...] // 如果启用 retina_masks
  },
  "annotated_image": "base64_encoded_image" // 如果 return_image=true
}
```

### 3. `/api/v1/yoloe/image-prompt`

使用视觉示例进行图像提示对象检测。

**请求:**
```
POST /api/v1/yoloe/image-prompt
```

**参数:**
- `file`: 用于检测的目标图像文件
- `bboxes`: 边界框数组，格式为 `[[x1,y1,x2,y2], [x1,y1,x2,y2], ...]`
- `cls`: 类别 ID 数组，格式为 `[0, 1, ...]`（必须从 0 开始）
- `refer_file`: 可选的包含视觉提示示例的参考图像
- `model_path`: 可选模型路径（默认值: "default"）
- `conf`: 置信度阈值（默认值: 0.25）
- `iou`: IoU 阈值（默认值: 0.7）
- `return_image`: 是否返回标注图像（默认值: false）
- `retina_masks`: 是否生成高质量掩码（默认值: false）

**注意:** 
- `bboxes` 和 `cls` 的长度必须匹配
- 每个边界框必须正好包含 4 个值 [x1,y1,x2,y2]
- 类别 ID 必须从 0 开始

**响应:**
```json
{
  "results": {
    "class": ["class_0", "class_1", ...],
    "confidence": [0.98, 0.85, ...],
    "bbox": [[x1, y1, x2, y2], ...],
    "masks": [[points], ...] // 如果启用 retina_masks
  },
  "annotated_image": "base64_encoded_image" // 如果 return_image=true
}
```

## 使用示例

### 无提示检测（curl）

```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/api/v1/yoloe/prompt-free' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@image.jpg;type=image/jpeg' \
  -F 'conf=0.25' \
  -F 'return_image=true'
```

### 文本提示检测（curl）

```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/api/v1/yoloe/text-prompt' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@image.jpg;type=image/jpeg' \
  -F 'class_names=["person", "car", "dog"]' \
  -F 'return_image=true'
```

### 图像提示检测（curl）

```bash
# 使用来自单独参考图像的示例对象
curl -X 'POST' \
  'http://0.0.0.0:8000/api/v1/yoloe/image-prompt' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@target.jpg;type=image/jpeg' \
  -F 'refer_file=@reference.jpg;type=image/jpeg' \
  -F 'bboxes=[[100,200,300,400]]' \
  -F 'cls=[0]' \
  -F 'return_image=true'
```

### Python 客户端示例

```python
import requests
import json
import base64
from PIL import Image
import io

# 图像提示检测
def detect_with_visual_prompts(image_path, refer_path=None, bboxes=None, cls=None):
    """使用视觉提示运行检测。"""
    url = "http://0.0.0.0:8000/api/v1/yoloe/image-prompt"
    
    # 准备文件
    files = {'file': open(image_path, 'rb')}
    if refer_path:
        files['refer_file'] = open(refer_path, 'rb')
    
    # 默认边界框，如果未提供
    if bboxes is None:
        bboxes = [[100, 100, 200, 200]]
    if cls is None:
        cls = [0]
    
    # 准备表单数据
    data = {
        'bboxes': json.dumps(bboxes),
        'cls': json.dumps(cls),
        'return_image': 'true'
    }
    
    # 发送请求
    response = requests.post(url, files=files, data=data)
    
    # 关闭文件句柄
    for f in files.values():
        f.close()
    
    if response.status_code == 200:
        result = response.json()
        
        # 打印检测结果
        if "results" in result and "class" in result["results"]:
            classes = result["results"]["class"]
            confidences = result["results"]["confidence"]
            
            print("检测结果:")
            for cls, conf in zip(classes, confidences):
                print(f"  - {cls}: {conf:.2f}")
        
        # 显示标注图像，如果可用
        if "annotated_image" in result:
            image_data = base64.b64decode(result["annotated_image"])
            image = Image.open(io.BytesIO(image_data))
            image.show()
        
        return result
    else:
        print(f"错误: {response.status_code}")
        print(response.text)
        return None

# 示例用法
result = detect_with_visual_prompts(
    "image.jpg",
    refer_path="reference.jpg",
    bboxes=[[221.52, 405.8, 344.98, 857.54]],
    cls=[0]
)
```