"""
测试 Moondream API 端点

该脚本测试所有四个 Moondream API 端点：
1. /describe - 图像描述
2. /ground - 对象定位
3. /point - 点击查询
4. /answer - 视觉问答

Author: EurekAnno Team
Date: 2025-05-25
"""

import requests
import json
import base64
from PIL import Image
import io
import os


def create_test_image():
    """创建一个简单的测试图像"""
    # 创建一个带有简单图形的测试图像
    image = Image.new('RGB', (640, 480), color='white')
    
    # 可以添加一些简单的图形用于测试
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    # 绘制一个红色矩形
    draw.rectangle([100, 100, 200, 200], fill='red', outline='black')
    # 绘制一个蓝色圆形
    draw.ellipse([300, 100, 400, 200], fill='blue', outline='black')
    # 绘制一些文字
    draw.text((250, 250), "Test Image", fill='black')
    
    # 保存到临时文件
    temp_path = "test_image.png"
    image.save(temp_path)
    return temp_path


def test_describe_api(api_url, image_path):
    """测试 describe 端点"""
    print("\n测试 /describe 端点...")
    url = f"{api_url}/api/v1/moondream/describe"
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'compile': 'false',
            'return_image': 'true'
        }
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 成功！模式: {result['mode']}")
        print(f"描述: {result['description'][:100]}...")
        if 'annotated_image' in result:
            print("✅ 返回了标注图像")
        return True
    else:
        print(f"❌ 失败！状态码: {response.status_code}")
        print(f"错误: {response.text}")
        return False


def test_ground_api(api_url, image_path):
    """测试 ground 端点"""
    print("\n测试 /ground 端点...")
    url = f"{api_url}/api/v1/moondream/ground"
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'object_name': 'rectangle',
            'compile': 'false',
            'return_image': 'true'
        }
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 成功！模式: {result['mode']}")
        print(f"对象: {result['object']}")
        print(f"边界框数量: {len(result['bboxes'])}")
        print(f"边界框: {result['bboxes']}")
        if 'annotated_image' in result:
            print("✅ 返回了标注图像")
        return True
    else:
        print(f"❌ 失败！状态码: {response.status_code}")
        print(f"错误: {response.text}")
        return False


def test_point_api(api_url, image_path):
    """测试 point 端点"""
    print("\n测试 /point 端点...")
    url = f"{api_url}/api/v1/moondream/point"
    
    # 点击数据
    point_data = {
        "x": 150,
        "y": 150,
        "question": "What color is this object?"
    }
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'point_data': json.dumps(point_data),
            'compile': 'false',
            'return_image': 'true'
        }
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 成功！模式: {result['mode']}")
        print(f"点击位置: {result['point']}")
        print(f"问题: {result['question']}")
        print(f"答案: {result['answer'][:100]}...")
        if 'annotated_image' in result:
            print("✅ 返回了标注图像")
        return True
    else:
        print(f"❌ 失败！状态码: {response.status_code}")
        print(f"错误: {response.text}")
        return False


def test_answer_api(api_url, image_path):
    """测试 answer 端点"""
    print("\n测试 /answer 端点...")
    url = f"{api_url}/api/v1/moondream/answer"
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'question': 'How many shapes are in this image?',
            'compile': 'false',
            'return_image': 'true'
        }
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 成功！模式: {result['mode']}")
        print(f"问题: {result['question']}")
        print(f"答案: {result['answer'][:100]}...")
        if 'annotated_image' in result:
            print("✅ 返回了原图像")
        return True
    else:
        print(f"❌ 失败！状态码: {response.status_code}")
        print(f"错误: {response.text}")
        return False


def test_health_api(api_url):
    """测试健康检查端点"""
    print("\n测试 /health 端点...")
    url = f"{api_url}/api/v1/moondream/health"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 健康状态: {result['status']}")
        print(f"模型加载: {result.get('model_loaded', 'N/A')}")
        return True
    else:
        print(f"❌ 失败！状态码: {response.status_code}")
        return False


def main():
    """运行所有测试"""
    # API URL
    api_url = "http://localhost:8001"
    
    # 创建测试图像
    print("创建测试图像...")
    test_image_path = create_test_image()
    
    try:
        # 测试健康检查
        test_health_api(api_url)
        
        # 测试所有端点
        all_success = True
        all_success &= test_describe_api(api_url, test_image_path)
        all_success &= test_ground_api(api_url, test_image_path)
        all_success &= test_point_api(api_url, test_image_path)
        all_success &= test_answer_api(api_url, test_image_path)
        
        print("\n" + "="*50)
        if all_success:
            print("✅ 所有测试通过！")
        else:
            print("❌ 部分测试失败！")
            
    finally:
        # 清理测试图像
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print("\n已清理测试图像")


if __name__ == "__main__":
    main()