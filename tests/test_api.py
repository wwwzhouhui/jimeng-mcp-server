#!/usr/bin/env python3
"""测试即梦API返回数据"""
import asyncio
import httpx
import json
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("JIMENG_API_KEY")
API_BASE_URL = os.getenv("JIMENG_API_URL", "https://jimeng1.duckcloud.fun")

async def test_text_to_image():
    """测试文生图API"""
    url = f"{API_BASE_URL}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "jimeng-4.5",
        "prompt": "一只可爱的小猫",
        "ratio": "1:1",
        "resolution": "2k",
        "sample_strength": 0.5
    }

    print(f"🔄 正在请求: {url}")
    print(f"📦 请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    print(f"🔑 API Key前缀: {API_KEY[:20]}..." if API_KEY else "❌ 未配置API_KEY")
    print(f"\n⏳ 等待响应...\n")

    try:
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(url, json=data, headers=headers)
            print(f"📡 HTTP状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")

            response.raise_for_status()
            result = response.json()

            print(f"\n✅ 请求成功!")
            print(f"📦 完整响应数据:")
            print(json.dumps(result, ensure_ascii=False, indent=2))

            # 分析数据结构
            print(f"\n🔍 数据分析:")
            print(f"  - 响应类型: {type(result)}")
            print(f"  - 顶层键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

            if isinstance(result, dict) and "data" in result:
                data_field = result["data"]
                print(f"  - data 类型: {type(data_field)}")
                print(f"  - data 长度: {len(data_field) if isinstance(data_field, (list, dict)) else 'N/A'}")
                if isinstance(data_field, list) and data_field:
                    print(f"  - data[0] 键: {list(data_field[0].keys()) if isinstance(data_field[0], dict) else 'N/A'}")

    except httpx.TimeoutException:
        print(f"❌ 请求超时")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP错误: {e.response.status_code}")
        print(f"响应内容: {e.response.text}")
    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_text_to_image())
