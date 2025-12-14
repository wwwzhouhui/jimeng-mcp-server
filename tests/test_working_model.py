#!/usr/bin/env python3
"""测试使用 jimeng-3.1 模型"""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("JIMENG_API_KEY")
API_URL = os.getenv("JIMENG_API_URL")
MODEL = os.getenv("JIMENG_MODEL")

async def test_with_working_model():
    print(f"🧪 测试模型: {MODEL}")
    print(f"📡 服务: {API_URL}")
    print(f"🔑 API Key: {API_KEY[:20]}...\n")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "prompt": "一只可爱的小猫咪",
        "ratio": "1:1",
        "resolution": "2k"
    }

    print(f"📦 请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    print(f"\n⏳ 发送请求...\n")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{API_URL}/v1/images/generations",
                json=data,
                headers=headers
            )

            print(f"📡 HTTP状态: {response.status_code}")
            result = response.json()

            if result.get("data"):
                print(f"\n✅ 成功! 生成了 {len(result['data'])} 张图片\n")
                for i, item in enumerate(result['data'], 1):
                    print(f"图片 {i}: {item.get('url', 'N/A')}")
            else:
                print(f"\n❌ 失败! 返回数据为空")
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_with_working_model())
