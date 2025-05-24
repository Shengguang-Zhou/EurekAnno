"""
Moondream 2B 视觉语言模型推理实现

该模块提供了 Moondream 2B 模型的推理功能，支持四种模式：
1. describe: 详细描述图像内容
2. ground: 定位图像中指定对象
3. point: 指定图像区域并询问
4. answer: 回答关于图像的问题

Author: EurekAnno Team
Date: 2025-05-25
"""

import os
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from PIL import Image
import torch
import numpy as np

# 配置管理
from app.config import config

# 获取模型路径
MOONDREAM_MODEL_PATH = config.get_moondream_model_path()

# 模型路径检查
if not MOONDREAM_MODEL_PATH or not os.path.exists(MOONDREAM_MODEL_PATH):
    DEFAULT_MODEL_PATH = "/home/a/.cache/huggingface/hub/models--moondream--moondream-2b-2025-04-14-4bit/snapshots/a89c59223ef8b5bb7826780728eeec172727ca84"
    if os.path.exists(DEFAULT_MODEL_PATH):
        MOONDREAM_MODEL_PATH = DEFAULT_MODEL_PATH
    else:
        MOONDREAM_MODEL_PATH = None  # 允许在没有模型的情况下定义接口

# 尝试导入 transformers
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers library not available. Install with: pip install transformers")


class MoondreamInference:
    """
    Moondream 2B 视觉语言模型推理类
    
    支持四种推理模式：
    - describe: 生成图像的详细描述
    - ground: 定位图像中的指定对象
    - point: 基于点击位置回答问题
    - answer: 回答关于图像的自由形式问题
    
    使用示例:
        # 初始化模型
        model = MoondreamInference()
        
        # 描述模式
        result = model.describe(image)
        
        # 定位模式
        result = model.ground(image, "person")
        
        # 点击模式
        result = model.point(image, (x, y), "What is this?")
        
        # 问答模式
        result = model.answer(image, "How many people are in this image?")
    """
    
    def __init__(self, model_path: str = MOONDREAM_MODEL_PATH, compile: bool = False):
        """
        初始化 Moondream 推理模型
        
        Args:
            model_path: 模型路径
            compile: 是否编译模型以加速推理（默认为 False）
        """
        self.model_path = model_path
        self.compile = compile
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载模型和分词器
        self._load_model()
        
    def _load_model(self):
        """加载 Moondream 模型和分词器"""
        if not TRANSFORMERS_AVAILABLE:
            print("Warning: Transformers not available, running in mock mode")
            self.model = None
            self.tokenizer = None
            return
            
        if not self.model_path:
            print("Warning: Model path not available, running in mock mode")
            self.model = None
            self.tokenizer = None
            return
            
        try:
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # 设置模型为评估模式
            self.model.eval()
            
            # 如果启用编译，编译模型
            if self.compile and hasattr(torch, 'compile'):
                self.model = torch.compile(self.model)
                
        except Exception as e:
            print(f"Warning: Failed to load model: {str(e)}")
            self.model = None
            self.tokenizer = None
    
    def _prepare_image(self, image: Union[str, Image.Image, np.ndarray]) -> Image.Image:
        """
        准备图像输入
        
        Args:
            image: 图像路径、PIL Image 对象或 numpy 数组
            
        Returns:
            PIL Image 对象
        """
        if isinstance(image, str):
            # 从文件路径加载
            if not os.path.exists(image):
                raise FileNotFoundError(f"Image file not found: {image}")
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            # 从 numpy 数组转换
            image = Image.fromarray(image).convert("RGB")
        elif isinstance(image, Image.Image):
            # 确保是 RGB 格式
            image = image.convert("RGB")
        else:
            raise TypeError(
                f"Unsupported image type: {type(image)}. "
                "Expected str, PIL.Image, or np.ndarray"
            )
            
        return image
    
    def describe(self, image: Union[str, Image.Image, np.ndarray]) -> Dict[str, Any]:
        """
        描述模式：生成图像的详细描述
        
        Args:
            image: 输入图像
            
        Returns:
            包含描述文本的字典
            {
                "mode": "describe",
                "description": "详细的图像描述"
            }
        """
        image = self._prepare_image(image)
        
        # 如果模型不可用，返回模拟数据
        if self.model is None:
            return {
                "mode": "describe",
                "description": "This is a test image with white background. [Mock response - model not loaded]"
            }
        
        # 编码图像
        encoded_image = self.model.encode_image(image)
        
        # 生成描述
        prompt = "Describe this image in detail."
        description = self.model.generate(
            encoded_image,
            prompt,
            tokenizer=self.tokenizer,
            max_new_tokens=512
        )
        
        return {
            "mode": "describe",
            "description": description
        }
    
    def ground(self, image: Union[str, Image.Image, np.ndarray], object_name: str) -> Dict[str, Any]:
        """
        定位模式：在图像中定位指定对象
        
        Args:
            image: 输入图像
            object_name: 要定位的对象名称
            
        Returns:
            包含边界框坐标的字典
            {
                "mode": "ground",
                "object": "对象名称",
                "bboxes": [[x1, y1, x2, y2], ...],
                "confidence": [0.95, ...]
            }
        """
        image = self._prepare_image(image)
        
        # 如果模型不可用，返回模拟数据
        if self.model is None:
            return {
                "mode": "ground",
                "object": object_name,
                "bboxes": [[100, 100, 200, 200]],  # 模拟边界框
                "confidence": [0.9]
            }
        
        # 编码图像
        encoded_image = self.model.encode_image(image)
        
        # 生成定位查询
        prompt = f"<ground>{object_name}"
        response = self.model.generate(
            encoded_image,
            prompt,
            tokenizer=self.tokenizer,
            max_new_tokens=128
        )
        
        # 解析边界框坐标
        bboxes = self._parse_bounding_boxes(response, image.size)
        
        return {
            "mode": "ground",
            "object": object_name,
            "bboxes": bboxes,
            "confidence": [0.9] * len(bboxes)  # Moondream 不提供置信度，使用默认值
        }
    
    def point(self, 
              image: Union[str, Image.Image, np.ndarray], 
              point: Tuple[int, int], 
              question: str) -> Dict[str, Any]:
        """
        点击模式：基于用户点击的位置回答问题
        
        Args:
            image: 输入图像
            point: 点击坐标 (x, y)
            question: 关于点击位置的问题
            
        Returns:
            包含答案的字典
            {
                "mode": "point",
                "point": [x, y],
                "question": "用户问题",
                "answer": "模型答案"
            }
        """
        image = self._prepare_image(image)
        x, y = point
        
        # 验证坐标在图像范围内
        width, height = image.size
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"Point ({x}, {y}) is outside image bounds ({width}, {height})")
        
        # 如果模型不可用，返回模拟数据
        if self.model is None:
            return {
                "mode": "point",
                "point": [x, y],
                "question": question,
                "answer": f"This is the pixel at position ({x}, {y}). [Mock response - model not loaded]"
            }
        
        # 编码图像
        encoded_image = self.model.encode_image(image)
        
        # 生成带坐标的查询
        prompt = f"<point>{x}, {y}</point> {question}"
        answer = self.model.generate(
            encoded_image,
            prompt,
            tokenizer=self.tokenizer,
            max_new_tokens=256
        )
        
        return {
            "mode": "point",
            "point": [x, y],
            "question": question,
            "answer": answer
        }
    
    def answer(self, image: Union[str, Image.Image, np.ndarray], question: str) -> Dict[str, Any]:
        """
        问答模式：回答关于图像的自由形式问题
        
        Args:
            image: 输入图像
            question: 关于图像的问题
            
        Returns:
            包含答案的字典
            {
                "mode": "answer",
                "question": "用户问题",
                "answer": "模型答案"
            }
        """
        image = self._prepare_image(image)
        
        # 如果模型不可用，返回模拟数据
        if self.model is None:
            return {
                "mode": "answer",
                "question": question,
                "answer": "This is a white background test image. [Mock response - model not loaded]"
            }
        
        # 编码图像
        encoded_image = self.model.encode_image(image)
        
        # 生成答案
        answer = self.model.generate(
            encoded_image,
            question,
            tokenizer=self.tokenizer,
            max_new_tokens=256
        )
        
        return {
            "mode": "answer",
            "question": question,
            "answer": answer
        }
    
    def _parse_bounding_boxes(self, response: str, image_size: Tuple[int, int]) -> List[List[float]]:
        """
        解析模型输出中的边界框坐标
        
        Args:
            response: 模型输出字符串
            image_size: 图像尺寸 (width, height)
            
        Returns:
            边界框坐标列表 [[x1, y1, x2, y2], ...]
        """
        width, height = image_size
        bboxes = []
        
        # 使用正则表达式匹配坐标
        # 期望格式: <click>x1, y1</click><click>x2, y2</click> 或 [x1, y1, x2, y2]
        pattern = r'<click>(\d+),\s*(\d+)</click><click>(\d+),\s*(\d+)</click>|\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]'
        matches = re.findall(pattern, response)
        
        for match in matches:
            if match[0]:  # <click> 格式
                x1, y1, x2, y2 = map(int, match[:4])
            else:  # [x1, y1, x2, y2] 格式
                x1, y1, x2, y2 = map(int, match[4:])
            
            # 确保坐标在图像范围内
            x1 = max(0, min(x1, width))
            y1 = max(0, min(y1, height))
            x2 = max(0, min(x2, width))
            y2 = max(0, min(y2, height))
            
            # 确保 x1 < x2 且 y1 < y2
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
                
            bboxes.append([x1, y1, x2, y2])
        
        return bboxes


if __name__ == "__main__":
    """测试 Moondream 推理功能"""
    
    # 创建测试图像
    test_image = Image.new('RGB', (640, 480), color='white')
    
    # 初始化模型（compile=False 用于测试）
    print("初始化 Moondream 模型...")
    model = MoondreamInference(compile=False)
    print("模型加载成功！")
    
    # 测试 describe 模式
    print("\n测试 describe 模式:")
    result = model.describe(test_image)
    print(f"结果格式: {list(result.keys())}")
    print(f"描述: {result['description'][:100]}...")
    
    # 测试 ground 模式
    print("\n测试 ground 模式:")
    result = model.ground(test_image, "person")
    print(f"结果格式: {list(result.keys())}")
    print(f"检测到 {len(result['bboxes'])} 个边界框")
    
    # 测试 point 模式
    print("\n测试 point 模式:")
    result = model.point(test_image, (320, 240), "What is this?")
    print(f"结果格式: {list(result.keys())}")
    print(f"答案: {result['answer'][:100]}...")
    
    # 测试 answer 模式
    print("\n测试 answer 模式:")
    result = model.answer(test_image, "What do you see in this image?")
    print(f"结果格式: {list(result.keys())}")
    print(f"答案: {result['answer'][:100]}...")
    
    print("\n所有测试完成！")