"""
Moondream 2B 视觉语言模型 API 端点

提供四种模式的 API 接口：
1. /describe - 图像描述
2. /ground - 对象定位
3. /point - 点击查询
4. /answer - 视觉问答

Author: EurekAnno Team
Date: 2025-05-25
"""

import os
import json
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# 导入 Moondream 推理模块
from app.cv.inference.moondream.moondream import MoondreamInference

# 创建路由器
router = APIRouter(
    tags=["moondream"],
    responses={404: {"description": "Not found"}},
)

# 全局模型实例
_model_instance = None


def get_model_instance(compile: bool = False) -> MoondreamInference:
    """获取或创建模型实例（单例模式）"""
    global _model_instance
    if _model_instance is None:
        _model_instance = MoondreamInference(compile=compile)
    return _model_instance


# Pydantic 模型定义
class PointRequest(BaseModel):
    """点击查询请求模型"""
    x: int = Field(..., description="点击的 X 坐标")
    y: int = Field(..., description="点击的 Y 坐标")
    question: str = Field(..., description="关于点击位置的问题")


@router.post("/describe", summary="图像描述", description="""
使用 Moondream 2B 生成图像的详细描述。

该端点接收一张图像，返回对图像内容的全面描述。

**参数说明：**
- file: 要描述的图像文件
- compile: 是否编译模型以加速推理（首次会较慢）
- return_image: 是否返回标注后的图像（base64编码）

**返回格式：**
```json
{
    "mode": "describe",
    "description": "图像的详细描述文本"
}
```
""")
async def describe_image(
    file: UploadFile = File(..., description="要描述的图像文件"),
    compile: bool = Form(default=False, description="是否编译模型"),
    return_image: bool = Form(default=False, description="是否返回标注图像")
):
    """生成图像的详细描述"""
    try:
        # 读取图像
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        
        # 获取模型实例
        model = get_model_instance(compile=compile)
        
        # 执行描述
        result = model.describe(image)
        
        # 如果需要返回图像，将原图编码为 base64
        if return_image:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            result["annotated_image"] = img_str
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


@router.post("/ground", summary="对象定位", description="""
在图像中定位指定的对象。

该端点接收一张图像和对象名称，返回对象在图像中的边界框坐标。

**参数说明：**
- file: 要分析的图像文件
- object_name: 要定位的对象名称（如 "person", "car" 等）
- compile: 是否编译模型
- return_image: 是否返回标注后的图像

**返回格式：**
```json
{
    "mode": "ground",
    "object": "对象名称",
    "bboxes": [[x1, y1, x2, y2], ...],
    "confidence": [0.9, ...]
}
```
""")
async def ground_object(
    file: UploadFile = File(..., description="要分析的图像文件"),
    object_name: str = Form(..., description="要定位的对象名称"),
    compile: bool = Form(default=False, description="是否编译模型"),
    return_image: bool = Form(default=False, description="是否返回标注图像")
):
    """在图像中定位指定对象"""
    try:
        # 读取图像
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        
        # 获取模型实例
        model = get_model_instance(compile=compile)
        
        # 执行定位
        result = model.ground(image, object_name)
        
        # 如果需要返回图像，绘制边界框
        if return_image:
            import cv2
            img_array = np.array(image)
            
            # 绘制边界框
            for bbox in result["bboxes"]:
                x1, y1, x2, y2 = [int(coord) for coord in bbox]
                cv2.rectangle(img_array, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img_array, object_name, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 转换回 PIL 并编码
            annotated_image = Image.fromarray(img_array)
            buffered = BytesIO()
            annotated_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            result["annotated_image"] = img_str
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


@router.post("/point", summary="点击查询", description="""
基于用户点击的位置回答问题。

该端点接收一张图像、点击坐标和问题，返回关于该位置的答案。

**参数说明：**
- file: 要分析的图像文件
- point_data: 包含点击坐标和问题的 JSON 数据
- compile: 是否编译模型
- return_image: 是否返回标注后的图像（会标记点击位置）

**请求体示例：**
```json
{
    "x": 100,
    "y": 200,
    "question": "What is this object?"
}
```

**返回格式：**
```json
{
    "mode": "point",
    "point": [100, 200],
    "question": "What is this object?",
    "answer": "This is a ..."
}
```
""")
async def point_query(
    file: UploadFile = File(..., description="要分析的图像文件"),
    point_data: str = Form(..., description="点击数据 JSON"),
    compile: bool = Form(default=False, description="是否编译模型"),
    return_image: bool = Form(default=False, description="是否返回标注图像")
):
    """基于点击位置回答问题"""
    try:
        # 解析点击数据
        try:
            data = json.loads(point_data)
            x = data["x"]
            y = data["y"]
            question = data["question"]
        except (json.JSONDecodeError, KeyError) as e:
            raise HTTPException(status_code=400, detail=f"无效的点击数据: {str(e)}")
        
        # 读取图像
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        
        # 获取模型实例
        model = get_model_instance(compile=compile)
        
        # 执行点击查询
        result = model.point(image, (x, y), question)
        
        # 如果需要返回图像，标记点击位置
        if return_image:
            import cv2
            img_array = np.array(image)
            
            # 绘制点击位置
            cv2.circle(img_array, (x, y), 5, (255, 0, 0), -1)
            cv2.circle(img_array, (x, y), 10, (255, 0, 0), 2)
            
            # 转换回 PIL 并编码
            annotated_image = Image.fromarray(img_array)
            buffered = BytesIO()
            annotated_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            result["annotated_image"] = img_str
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


@router.post("/answer", summary="视觉问答", description="""
回答关于图像的自由形式问题。

该端点接收一张图像和问题，返回基于视觉内容的答案。

**参数说明：**
- file: 要分析的图像文件
- question: 关于图像的问题
- compile: 是否编译模型
- return_image: 是否返回原图像

**返回格式：**
```json
{
    "mode": "answer",
    "question": "用户的问题",
    "answer": "模型生成的答案"
}
```
""")
async def answer_question(
    file: UploadFile = File(..., description="要分析的图像文件"),
    question: str = Form(..., description="关于图像的问题"),
    compile: bool = Form(default=False, description="是否编译模型"),
    return_image: bool = Form(default=False, description="是否返回原图像")
):
    """回答关于图像的问题"""
    try:
        # 读取图像
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        
        # 获取模型实例
        model = get_model_instance(compile=compile)
        
        # 执行问答
        result = model.answer(image, question)
        
        # 如果需要返回图像，编码原图
        if return_image:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            result["annotated_image"] = img_str
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


# 健康检查端点
@router.get("/health", summary="健康检查", description="检查 Moondream API 服务状态")
async def health_check():
    """检查服务健康状态"""
    try:
        # 尝试获取模型实例
        model = get_model_instance()
        model_loaded = model.model is not None
        
        return {
            "status": "healthy",
            "model_loaded": model_loaded,
            "transformers_available": model.model is not None or "mock mode" 
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }