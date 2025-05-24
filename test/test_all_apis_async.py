"""
测试所有 API 端点的异步性能

该脚本测试 YOLOe 和 Moondream 的所有 API 端点，
并验证它们是否正确实现了异步操作。

Author: EurekAnno Team
Date: 2025-05-25
"""

import asyncio
import aiohttp
import json
import time
from PIL import Image
import io
import os


def create_test_image():
    """创建测试图像"""
    # 创建一个带有简单图形的测试图像
    image = Image.new('RGB', (640, 480), color='white')
    
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    # 绘制一个红色矩形（模拟 person）
    draw.rectangle([100, 100, 200, 300], fill='red', outline='black')
    # 绘制一个蓝色矩形（模拟 car）
    draw.rectangle([300, 200, 450, 350], fill='blue', outline='black')
    
    # 保存到内存
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue(), image


async def test_yoloe_prompt_free(session, url_base, image_data):
    """测试 YOLOe 无提示检测"""
    url = f"{url_base}/api/v1/yoloe/prompt-free"
    
    data = aiohttp.FormData()
    data.add_field('file', image_data, filename='test.png', content_type='image/png')
    data.add_field('conf', '0.25')
    data.add_field('return_image', 'false')
    
    async with session.post(url, data=data) as response:
        result = await response.json()
        return response.status, result


async def test_yoloe_text_prompt(session, url_base, image_data):
    """测试 YOLOe 文本提示检测"""
    url = f"{url_base}/api/v1/yoloe/text-prompt"
    
    data = aiohttp.FormData()
    data.add_field('file', image_data, filename='test.png', content_type='image/png')
    data.add_field('class_names', '["person", "car"]')
    data.add_field('conf', '0.25')
    data.add_field('return_image', 'false')
    
    async with session.post(url, data=data) as response:
        result = await response.json()
        return response.status, result


async def test_yoloe_image_prompt(session, url_base, image_data):
    """测试 YOLOe 图像提示检测"""
    url = f"{url_base}/api/v1/yoloe/image-prompt"
    
    data = aiohttp.FormData()
    data.add_field('file', image_data, filename='test.png', content_type='image/png')
    data.add_field('bboxes', '[[100, 100, 200, 300]]')
    data.add_field('cls', '[0]')
    data.add_field('conf', '0.25')
    data.add_field('return_image', 'false')
    
    async with session.post(url, data=data) as response:
        result = await response.json()
        return response.status, result


async def test_moondream_describe(session, url_base, image_data):
    """测试 Moondream 描述"""
    url = f"{url_base}/api/v1/moondream/describe"
    
    data = aiohttp.FormData()
    data.add_field('file', image_data, filename='test.png', content_type='image/png')
    data.add_field('compile', 'false')
    data.add_field('return_image', 'false')
    
    async with session.post(url, data=data) as response:
        result = await response.json()
        return response.status, result


async def test_moondream_ground(session, url_base, image_data):
    """测试 Moondream 定位"""
    url = f"{url_base}/api/v1/moondream/ground"
    
    data = aiohttp.FormData()
    data.add_field('file', image_data, filename='test.png', content_type='image/png')
    data.add_field('object_name', 'rectangle')
    data.add_field('compile', 'false')
    data.add_field('return_image', 'false')
    
    async with session.post(url, data=data) as response:
        result = await response.json()
        return response.status, result


async def test_moondream_point(session, url_base, image_data):
    """测试 Moondream 点击查询"""
    url = f"{url_base}/api/v1/moondream/point"
    
    point_data = {"x": 150, "y": 200, "question": "What color is this?"}
    
    data = aiohttp.FormData()
    data.add_field('file', image_data, filename='test.png', content_type='image/png')
    data.add_field('point_data', json.dumps(point_data))
    data.add_field('compile', 'false')
    data.add_field('return_image', 'false')
    
    async with session.post(url, data=data) as response:
        result = await response.json()
        return response.status, result


async def test_moondream_answer(session, url_base, image_data):
    """测试 Moondream 问答"""
    url = f"{url_base}/api/v1/moondream/answer"
    
    data = aiohttp.FormData()
    data.add_field('file', image_data, filename='test.png', content_type='image/png')
    data.add_field('question', 'How many rectangles are in this image?')
    data.add_field('compile', 'false')
    data.add_field('return_image', 'false')
    
    async with session.post(url, data=data) as response:
        result = await response.json()
        return response.status, result


async def test_concurrent_requests(url_base, image_data, num_concurrent=5):
    """测试并发请求"""
    print(f"\n测试 {num_concurrent} 个并发请求...")
    
    async with aiohttp.ClientSession() as session:
        # 创建多个并发任务
        tasks = []
        
        # 混合不同的 API 调用
        for i in range(num_concurrent):
            if i % 4 == 0:
                task = test_yoloe_prompt_free(session, url_base, image_data)
            elif i % 4 == 1:
                task = test_moondream_describe(session, url_base, image_data)
            elif i % 4 == 2:
                task = test_yoloe_text_prompt(session, url_base, image_data)
            else:
                task = test_moondream_answer(session, url_base, image_data)
            
            tasks.append(task)
        
        # 测量并发执行时间
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"并发执行时间: {end_time - start_time:.2f} 秒")
        
        # 检查结果
        success_count = sum(1 for status, _ in results if status == 200)
        print(f"成功请求: {success_count}/{num_concurrent}")
        
        return results


async def test_all_endpoints(url_base):
    """测试所有端点"""
    print("创建测试图像...")
    image_data, _ = create_test_image()
    
    async with aiohttp.ClientSession() as session:
        print("\n=== 测试 YOLOe API ===")
        
        # 测试 YOLOe 端点
        print("\n1. 测试 prompt-free...")
        status, result = await test_yoloe_prompt_free(session, url_base, image_data)
        print(f"状态码: {status}")
        if status == 200 and "results" in result:
            print(f"✅ 成功！检测到 {len(result['results'].get('class', []))} 个对象")
        else:
            print(f"❌ 失败！{result}")
        
        print("\n2. 测试 text-prompt...")
        status, result = await test_yoloe_text_prompt(session, url_base, image_data)
        print(f"状态码: {status}")
        if status == 200 and "results" in result:
            print(f"✅ 成功！检测到 {len(result['results'].get('class', []))} 个对象")
        else:
            print(f"❌ 失败！{result}")
        
        print("\n3. 测试 image-prompt...")
        status, result = await test_yoloe_image_prompt(session, url_base, image_data)
        print(f"状态码: {status}")
        if status == 200 and "results" in result:
            print(f"✅ 成功！检测到 {len(result['results'].get('class', []))} 个对象")
        else:
            print(f"❌ 失败！{result}")
        
        print("\n=== 测试 Moondream API ===")
        
        # 测试 Moondream 端点
        print("\n4. 测试 describe...")
        status, result = await test_moondream_describe(session, url_base, image_data)
        print(f"状态码: {status}")
        if status == 200 and "description" in result:
            print(f"✅ 成功！描述: {result['description'][:50]}...")
        else:
            print(f"❌ 失败！{result}")
        
        print("\n5. 测试 ground...")
        status, result = await test_moondream_ground(session, url_base, image_data)
        print(f"状态码: {status}")
        if status == 200 and "bboxes" in result:
            print(f"✅ 成功！找到 {len(result['bboxes'])} 个边界框")
        else:
            print(f"❌ 失败！{result}")
        
        print("\n6. 测试 point...")
        status, result = await test_moondream_point(session, url_base, image_data)
        print(f"状态码: {status}")
        if status == 200 and "answer" in result:
            print(f"✅ 成功！答案: {result['answer'][:50]}...")
        else:
            print(f"❌ 失败！{result}")
        
        print("\n7. 测试 answer...")
        status, result = await test_moondream_answer(session, url_base, image_data)
        print(f"状态码: {status}")
        if status == 200 and "answer" in result:
            print(f"✅ 成功！答案: {result['answer'][:50]}...")
        else:
            print(f"❌ 失败！{result}")
    
    # 测试并发请求
    await test_concurrent_requests(url_base, image_data, num_concurrent=10)


async def main():
    """主函数"""
    url_base = "http://localhost:8001"
    
    try:
        await test_all_endpoints(url_base)
        print("\n✅ 所有异步测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())