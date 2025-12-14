#!/usr/bin/env python3
"""
测试远程 jimeng-free-api-all 服务
诊断为什么返回空数据
"""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("JIMENG_API_KEY")
API_URL = os.getenv("JIMENG_API_URL")

async def test_remote_service():
    """测试远程服务的各个方面"""

    print("=" * 70)
    print("🔍 远程 jimeng-free-api-all 服务诊断")
    print("=" * 70)

    print(f"\n📡 服务地址: {API_URL}")
    print(f"🔑 API Key: {API_KEY[:20]}...")

    # 测试1: 检查服务是否在线
    print("\n" + "=" * 70)
    print("测试1: 检查服务健康状态")
    print("=" * 70)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # 尝试访问 /v1/models 端点
            response = await client.get(f"{API_URL}/v1/models")
            print(f"✅ 服务在线 (HTTP {response.status_code})")
            models = response.json()
            print(f"📋 可用模型数: {len(models.get('data', []))}")

    except Exception as e:
        print(f"❌ 服务离线或无法访问: {e}")
        return

    # 测试2: 测试图像生成（简化参数）
    print("\n" + "=" * 70)
    print("测试2: 图像生成（简化参数）")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 使用最简单的参数
    simple_data = {
        "model": "jimeng-4.5",
        "prompt": "一只猫",
        "ratio": "1:1",
        "resolution": "2k"
    }

    print(f"📦 请求数据: {json.dumps(simple_data, ensure_ascii=False)}")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{API_URL}/v1/images/generations",
                json=simple_data,
                headers=headers
            )

            print(f"📡 HTTP状态: {response.status_code}")
            result = response.json()
            print(f"📦 响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")

            if result.get("data"):
                print(f"✅ 成功! 返回 {len(result['data'])} 张图片")
            else:
                print(f"❌ 失败! data 字段为空")

                # 检查是否有错误信息
                if "error" in result:
                    print(f"🔴 错误信息: {result['error']}")

    except httpx.TimeoutException:
        print(f"❌ 请求超时（120秒）")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 测试3: 测试不同的模型
    print("\n" + "=" * 70)
    print("测试3: 尝试不同模型")
    print("=" * 70)

    for model in ["jimeng-4.5", "jimeng-4.0", "jimeng-3.1"]:
        print(f"\n🧪 测试模型: {model}")

        data = {
            "model": model,
            "prompt": "测试",
            "ratio": "1:1",
            "resolution": "1k"
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{API_URL}/v1/images/generations",
                    json=data,
                    headers=headers
                )

                result = response.json()
                if result.get("data"):
                    print(f"  ✅ {model}: 成功")
                else:
                    print(f"  ❌ {model}: data 为空")
                    if "error" in result:
                        print(f"     错误: {result['error']}")

        except Exception as e:
            print(f"  ❌ {model}: 异常 - {e}")

    # 测试4: 检查 API Key 是否有效
    print("\n" + "=" * 70)
    print("测试4: 验证 API Key")
    print("=" * 70)

    # 尝试不带 Authorization 头
    print("\n🔍 不带 Authorization 测试...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{API_URL}/v1/images/generations",
                json={"model": "jimeng-4.5", "prompt": "测试", "ratio": "1:1", "resolution": "1k"}
            )
            print(f"  HTTP状态: {response.status_code}")
            if response.status_code == 401:
                print(f"  ✅ API Key 验证正常（未授权请求被拒绝）")
            elif response.status_code == 200:
                print(f"  ⚠️ API Key 验证可能未启用")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")

    # 诊断结果
    print("\n" + "=" * 70)
    print("💡 诊断结果与建议")
    print("=" * 70)

    print("\n可能的原因：")
    print("1. 🔑 SessionID 无效或过期")
    print("   - 解决：从浏览器重新获取 sessionid")
    print("   - 步骤：F12 → Application → Cookies → sessionid")

    print("\n2. 💰 积分不足")
    print("   - 解决：检查即梦账号积分余额")
    print("   - 访问：https://jimeng.duckcloud.fun 查看积分")

    print("\n3. 🚫 IP 被限流")
    print("   - 解决：等待一段时间后重试")
    print("   - 或者：联系服务提供商")

    print("\n4. ⚙️ 远程服务配置问题")
    print("   - 解决：检查远程 jimeng-free-api-all 的日志")
    print("   - 验证：服务是否正确配置了 SessionID")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(test_remote_service())
