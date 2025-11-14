#!/usr/bin/env python3
"""
测试即梦MCP服务器是否能正常加载
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from jimeng_mcp import server
    print("✅ 服务器模块加载成功")

    # 检查环境变量
    if server.API_KEY:
        print(f"✅ API密钥已配置: {server.API_KEY[:10]}...")
    else:
        print("❌ API密钥未配置")
        sys.exit(1)

    print(f"✅ API地址: {server.API_BASE_URL}")
    print(f"✅ 默认模型: {server.DEFAULT_MODEL}")

    # 检查工具列表
    import asyncio
    tools = asyncio.run(server.handle_list_tools())
    print(f"\n✅ 成功加载 {len(tools)} 个工具:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description[:50]}...")

    print("\n🎉 服务器配置检查完成,一切正常!")
    print("\n下一步:")
    print("1. 配置Claude Desktop (参见下方配置)")
    print("2. 重启Claude Desktop")
    print("3. 在Claude中测试即梦工具")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
