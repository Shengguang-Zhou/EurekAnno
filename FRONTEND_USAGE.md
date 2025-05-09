# EurekAnno 前端开发与集成指南

本文档提供了如何在前端应用中集成和使用 EurekAnno API 的详细说明和示例。以下内容将帮助您理解如何调用三个主要 API 端点并处理其返回的数据。

## 目录

- [API 基础知识](#api-基础知识)
- [无提示检测 API](#无提示检测-api)
- [文本提示检测 API](#文本提示检测-api)
- [图像提示检测 API](#图像提示检测-api)
- [处理返回结果](#处理返回结果)
- [常见问题与解决方案](#常见问题与解决方案)

## API 基础知识

所有 API 端点使用 `multipart/form-data` 格式接收请求，便于传输图像文件和其他参数。基本 URL 为：`http://[服务器地址]:8000/api/v1/yoloe/`

## 无提示检测 API

### 端点

```
POST /api/v1/yoloe/prompt-free
```

### 描述

无提示检测 API 使用 YOLOe 内置的词汇表自动检测图像中的对象，无需提供任何类别名称或参考。

### 示例代码

#### JavaScript/React 示例

```javascript
import axios from 'axios';

// 无提示检测函数
async function performPromptFreeDetection(imageFile) {
  try {
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('return_image', 'true'); // 可选，返回标注后的图像
    
    const response = await axios.post(
      'http://localhost:8000/api/v1/yoloe/prompt-free',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    // 处理响应
    const results = response.data.results;
    const annotatedImage = response.data.annotated_image; // Base64 编码的图像
    
    // 显示检测结果
    displayResults(results, annotatedImage);
    
  } catch (error) {
    console.error('检测失败:', error);
  }
}

// 在组件中使用
function MyDetectionComponent() {
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      performPromptFreeDetection(file);
    }
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleFileUpload} />
      {/* 显示结果的其他 UI 元素 */}
    </div>
  );
}
```

#### 使用 fetch API 的示例

```javascript
// 使用原生 fetch API 的无提示检测
async function detectWithPromptFree(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('conf', '0.25'); // 可选，设置置信度阈值
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/yoloe/prompt-free', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP 错误: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error('API 调用失败:', error);
    throw error;
  }
}
```

## 文本提示检测 API

### 端点

```
POST /api/v1/yoloe/text-prompt
```

### 描述

文本提示 API 允许您通过提供自定义类别名称列表来检测特定类型的对象。

### 示例代码

#### JavaScript/React 示例

```javascript
import axios from 'axios';

// 文本提示检测函数
async function performTextPromptDetection(imageFile, classNames) {
  try {
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('class_names', JSON.stringify(classNames)); // 重要：必须序列化为 JSON 字符串
    formData.append('return_image', 'true');
    
    const response = await axios.post(
      'http://localhost:8000/api/v1/yoloe/text-prompt',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    return response.data;
    
  } catch (error) {
    console.error('文本提示检测失败:', error);
    throw error;
  }
}

// 在组件中使用
function TextPromptComponent() {
  const [classNames, setClassNames] = useState(['人', '车', '猫']);
  const [results, setResults] = useState(null);
  
  const handleAddClass = (newClass) => {
    setClassNames([...classNames, newClass]);
  };
  
  const handleDetection = async (imageFile) => {
    if (imageFile && classNames.length > 0) {
      const data = await performTextPromptDetection(imageFile, classNames);
      setResults(data.results);
    }
  };

  return (
    <div>
      {/* 类别输入和图像上传 UI */}
      <div className="class-list">
        {classNames.map((cls, index) => (
          <span key={index} className="class-tag">{cls}</span>
        ))}
      </div>
      
      <button onClick={() => handleDetection(selectedImage)}>
        开始检测
      </button>
      
      {/* 结果显示 */}
    </div>
  );
}
```

## 图像提示检测 API

### 端点

```
POST /api/v1/yoloe/image-prompt
```

### 描述

图像提示 API 允许您通过提供参考图像和边界框来检测与视觉示例相似的对象。

### 示例代码

#### JavaScript/React 示例

```javascript
import axios from 'axios';

// 图像提示检测函数
async function performImagePromptDetection(imageFile, referenceImage, bboxes, cls) {
  try {
    const formData = new FormData();
    formData.append('file', imageFile);
    
    if (referenceImage) {
      formData.append('refer_file', referenceImage);
    }
    
    formData.append('bboxes', JSON.stringify(bboxes)); // 格式: [[x1,y1,x2,y2], ...]
    formData.append('cls', JSON.stringify(cls)); // 格式: [0, 1, ...]
    formData.append('return_image', 'true');
    
    const response = await axios.post(
      'http://localhost:8000/api/v1/yoloe/image-prompt',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    return response.data;
    
  } catch (error) {
    console.error('图像提示检测失败:', error);
    throw error;
  }
}

// 在画布上绘制和选择边界框的组件
function ImagePromptCanvas() {
  const [bboxes, setBboxes] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [referenceImage, setReferenceImage] = useState(null);
  
  // 处理画布绘制和边界框选择
  const handleCanvasDraw = (newBbox) => {
    setBboxes([...bboxes, newBbox]);
  };
  
  // 执行检测
  const handleDetection = async () => {
    if (selectedImage && bboxes.length > 0) {
      // 为每个边界框分配类别 ID (从 0 开始)
      const classIds = bboxes.map((_, index) => index);
      
      const results = await performImagePromptDetection(
        selectedImage,
        referenceImage,
        bboxes,
        classIds
      );
      
      // 处理结果
      displayResults(results);
    }
  };

  return (
    <div>
      {/* 图像上传和画布 UI */}
      <canvas ref={canvasRef} />
      
      <div className="bbox-list">
        {bboxes.map((bbox, index) => (
          <div key={index} className="bbox-item">
            边界框 {index+1}: [{bbox.join(', ')}]
          </div>
        ))}
      </div>
      
      <button onClick={handleDetection} disabled={!selectedImage || bboxes.length === 0}>
        使用图像提示检测
      </button>
    </div>
  );
}
```

## 处理返回结果

所有三个 API 端点都返回类似结构的 JSON 数据：

```javascript
{
  "results": {
    "class": ["人", "车", ...],
    "confidence": [0.98, 0.85, ...],
    "bbox": [[x1, y1, x2, y2], ...],
    "masks": [[点坐标], ...] // 如果启用了 retina_masks
  },
  "annotated_image": "base64编码的图像" // 如果 return_image=true
}
```

### 显示结果示例代码

```javascript
function displayResults(apiResults) {
  if (!apiResults || !apiResults.results) return;
  
  const { class: classes, confidence, bbox } = apiResults.results;
  
  // 创建结果列表
  return (
    <div className="detection-results">
      <h3>检测到 {classes.length} 个物体</h3>
      
      <ul className="result-list">
        {classes.map((className, index) => (
          <li key={index} className="result-item">
            <span className="class-name">{className}</span>
            <span className="confidence">{(confidence[index] * 100).toFixed(1)}%</span>
            <span className="bbox">位置: {bbox[index].map(v => Math.round(v)).join(', ')}</span>
          </li>
        ))}
      </ul>
      
      {apiResults.annotated_image && (
        <div className="annotated-image">
          <img src={`data:image/jpeg;base64,${apiResults.annotated_image}`} alt="检测结果" />
        </div>
      )}
    </div>
  );
}
```

## 常见问题与解决方案

### 1. 图像上传问题

**问题**: 上传大图像时超时或失败

**解决方案**:
- 在前端增加图像压缩逻辑
- 使用分块上传 API
- 增加服务器超时设置

```javascript
// 图像压缩示例
async function compressImage(file, maxWidth = 1024) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;
        
        if (width > maxWidth) {
          height = (maxWidth / width) * height;
          width = maxWidth;
        }
        
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob((blob) => {
          resolve(new File([blob], file.name, { type: 'image/jpeg' }));
        }, 'image/jpeg', 0.85);
      };
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// 使用方法
const compressedImage = await compressImage(originalImageFile);
```

### 2. 检测延迟处理

**问题**: 检测需要较长时间，UI 可能无响应

**解决方案**:
- 使用加载状态和进度指示
- 实现轮询机制检查长时间运行任务的状态

```javascript
// 添加加载状态和超时处理
async function performDetectionWithTimeout(apiFunction, ...args) {
  const [setLoading, setProgress] = useState(false, 0);
  
  setLoading(true);
  
  try {
    // 设置超时
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('请求超时')), 30000);
    });
    
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 5, 95));
    }, 500);
    
    // 执行 API 调用
    const result = await Promise.race([
      apiFunction(...args),
      timeoutPromise
    ]);
    
    setProgress(100);
    return result;
    
  } catch (error) {
    console.error('检测过程中出错:', error);
    throw error;
  } finally {
    setLoading(false);
    clearInterval(progressInterval);
  }
}
```

### 3. 处理多个边界框和类别

**问题**: 图像提示 API 需要正确处理多个边界框和类别 ID

**解决方案**:
- 确保边界框和类别数组长度匹配
- 类别 ID 必须从 0 开始

```javascript
// 校验边界框和类别 ID
function validateBboxesAndClasses(bboxes, cls) {
  if (bboxes.length !== cls.length) {
    throw new Error('边界框和类别 ID 数量必须相同');
  }
  
  // 验证边界框格式 (每个必须是 [x1, y1, x2, y2])
  for (const bbox of bboxes) {
    if (!Array.isArray(bbox) || bbox.length !== 4) {
      throw new Error('边界框格式错误，必须是 [x1, y1, x2, y2]');
    }
  }
  
  // 验证类别 ID 从 0 开始
  const minClassId = Math.min(...cls);
  if (minClassId !== 0) {
    throw new Error('类别 ID 必须从 0 开始');
  }
  
  return true;
}
```

## 高级用法与自定义

### 自定义检测参数

所有 API 端点都支持额外的参数来调整检测行为：

```javascript
// 设置更详细的参数
const advancedFormData = new FormData();
advancedFormData.append('file', imageFile);
advancedFormData.append('conf', '0.15'); // 降低置信度阈值以检测更多物体
advancedFormData.append('iou', '0.5'); // 调整 IoU 阈值
advancedFormData.append('retina_masks', 'true'); // 启用高质量掩码生成

// 设置自定义模型路径
advancedFormData.append('model_path', 'custom/model.pt');
```

### 集成到大型应用程序

对于复杂应用程序，建议创建专用的 API 服务层：

```javascript
// API 服务层示例
const yoloeService = {
  API_URL: 'http://localhost:8000/api/v1/yoloe',
  
  // 基本调用方法
  async callApi(endpoint, formData) {
    try {
      const response = await axios.post(`${this.API_URL}/${endpoint}`, formData);
      return response.data;
    } catch (error) {
      this.handleApiError(error);
      throw error;
    }
  },
  
  // 错误处理
  handleApiError(error) {
    if (error.response) {
      // 服务器返回错误
      console.error('API 错误:', error.response.status, error.response.data);
    } else if (error.request) {
      // 请求发送但未收到响应
      console.error('网络错误 - 未收到响应');
    } else {
      // 请求设置过程中出错
      console.error('请求错误:', error.message);
    }
  },
  
  // 不同端点的专用方法
  async promptFree(imageFile, params = {}) {
    const formData = this.createFormData(imageFile, params);
    return this.callApi('prompt-free', formData);
  },
  
  async textPrompt(imageFile, classNames, params = {}) {
    const formData = this.createFormData(imageFile, {
      ...params,
      class_names: JSON.stringify(classNames)
    });
    return this.callApi('text-prompt', formData);
  },
  
  async imagePrompt(imageFile, bboxes, cls, referImage = null, params = {}) {
    // 验证输入
    this.validateImagePromptInputs(bboxes, cls);
    
    const formData = this.createFormData(imageFile, {
      ...params,
      bboxes: JSON.stringify(bboxes),
      cls: JSON.stringify(cls)
    });
    
    if (referImage) {
      formData.append('refer_file', referImage);
    }
    
    return this.callApi('image-prompt', formData);
  },
  
  // 辅助方法
  createFormData(image, params = {}) {
    const formData = new FormData();
    formData.append('file', image);
    
    Object.entries(params).forEach(([key, value]) => {
      formData.append(key, value);
    });
    
    return formData;
  },
  
  validateImagePromptInputs(bboxes, cls) {
    if (!Array.isArray(bboxes) || !Array.isArray(cls)) {
      throw new Error('边界框和类别必须是数组');
    }
    
    if (bboxes.length !== cls.length) {
      throw new Error('边界框和类别数量必须匹配');
    }
    
    if (cls.some(id => id < 0 || !Number.isInteger(id))) {
      throw new Error('类别 ID 必须是从 0 开始的整数');
    }
  }
};
```

## 总结

通过本指南中提供的示例和技巧，您应该能够轻松地将 EurekAnno API 集成到您的前端应用程序中。

请记住：
- 始终验证用户输入
- 处理网络错误和服务器异常
- 提供清晰的用户反馈
- 对大型图像进行预处理
- 根据您的应用需求调整检测参数

如需更多支持或有其他问题，请参考 API 文档或联系开发团队。