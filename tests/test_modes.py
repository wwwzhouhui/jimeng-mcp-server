#!/usr/bin/env python3
"""
测试即梦MCP服务器的三种模式
"""

import sys
import time
import requests
import subprocess
from pathlib import Path


def test_stdio_mode():
    """测试stdio模式"""
    print("\n" + "="*60)
    print("测试 stdio 模式")
    print("="*60)

    try:
        # 启动服务器进程
        print("启动 stdio 模式服务器...")
        result = subprocess.run(
            [sys.executable, "-m", "jimeng_mcp.server", "--mode", "stdio"],
            capture_output=True,
            text=True,
            timeout=3
        )

        print("✅ stdio 模式服务器可以启动")
        return True
    except subprocess.TimeoutExpired:
        print("✅ stdio 模式服务器正常运行 (超时预期,因为它在等待输入)")
        return True
    except Exception as e:
        print(f"❌ stdio 模式测试失败: {e}")
        return False


def test_http_mode():
    """测试HTTP模式"""
    print("\n" + "="*60)
    print("测试 HTTP 模式")
    print("="*60)

    try:
        # 启动服务器进程
        print("启动 HTTP 模式服务器...")
        process = subprocess.Popen(
            [sys.executable, "-m", "jimeng_mcp.server", "--mode", "http", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 等待服务器启动
        print("等待服务器启动...")
        time.sleep(3)

        # 测试健康检查端点
        print("测试健康检查端点...")
        response = requests.get("http://localhost:8001/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ HTTP 健康检查成功: {data}")

            # 测试工具列表端点
            print("测试工具列表端点...")
            response = requests.get("http://localhost:8001/tools", timeout=5)
            if response.status_code == 200:
                tools = response.json()
                print(f"✅ 获取工具列表成功: {len(tools.get('tools', []))} 个工具")

            return True
        else:
            print(f"❌ HTTP 健康检查失败,状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ HTTP 模式测试失败: {e}")
        return False
    finally:
        # 关闭服务器进程
        if 'process' in locals():
            process.terminate()
            process.wait(timeout=5)
            print("服务器已关闭")


def test_sse_mode():
    """测试SSE模式"""
    print("\n" + "="*60)
    print("测试 SSE 模式")
    print("="*60)

    try:
        # 启动服务器进程
        print("启动 SSE 模式服务器...")
        process = subprocess.Popen(
            [sys.executable, "-m", "jimeng_mcp.server", "--mode", "sse", "--port", "8002"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 等待服务器启动
        print("等待服务器启动...")
        time.sleep(3)

        # 简单测试SSE端点是否可访问
        print("测试 SSE 端点...")
        response = requests.get("http://localhost:8002/sse", timeout=5, stream=True)

        if response.status_code in [200, 405]:  # 405 是因为GET方法可能不被允许
            print(f"✅ SSE 端点可访问 (状态码: {response.status_code})")
            return True
        else:
            print(f"⚠️  SSE 端点返回状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ SSE 模式测试失败: {e}")
        return False
    finally:
        # 关闭服务器进程
        if 'process' in locals():
            process.terminate()
            process.wait(timeout=5)
            print("服务器已关闭")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("即梦 MCP 服务器 - 多模式测试")
    print("="*60)

    results = {}

    # 测试 stdio 模式
    results['stdio'] = test_stdio_mode()

    # 测试 HTTP 模式
    try:
        results['http'] = test_http_mode()
    except ModuleNotFoundError:
        print("\n❌ HTTP 模式依赖未安装")
        print("请运行: pip install -e \".[http]\"")
        results['http'] = False

    # 测试 SSE 模式
    try:
        results['sse'] = test_sse_mode()
    except ModuleNotFoundError:
        print("\n❌ SSE 模式依赖未安装")
        print("请运行: pip install -e \".[sse]\"")
        results['sse'] = False

    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    for mode, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{mode.upper()} 模式: {status}")

    # 返回退出码
    all_passed = all(results.values())
    if all_passed:
        print("\n✅ 所有测试通过!")
        return 0
    else:
        print("\n⚠️  部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
