#!/usr/bin/env python3
"""
即梦MCP HTTP API使用示例

演示如何使用Python调用即梦MCP的HTTP API
"""

import requests
import sys
import json
from typing import Dict, Any


class JiMengClient:
    """即梦MCP HTTP客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化客户端

        Args:
            base_url: API基础URL
        """
        self.base_url = base_url

    def check_health(self) -> Dict[str, Any]:
        """检查服务器健康状态"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def list_tools(self) -> Dict[str, Any]:
        """获取可用工具列表"""
        response = requests.get(f"{self.base_url}/tools")
        response.raise_for_status()
        return response.json()

    def text_to_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1536,
        height: int = 864,
        sample_strength: float = 0.5
    ) -> Dict[str, Any]:
        """
        文本生成图像

        Args:
            prompt: 图像描述
            negative_prompt: 负面提示词
            width: 图像宽度
            height: 图像高度
            sample_strength: 采样强度 (0.0-1.0)

        Returns:
            API响应
        """
        response = requests.post(
            f"{self.base_url}/text-to-image",
            json={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "sample_strength": sample_strength
            }
        )
        response.raise_for_status()
        return response.json()

    def image_composition(
        self,
        prompt: str,
        images: list,
        width: int = 1536,
        height: int = 864,
        sample_strength: float = 0.5
    ) -> Dict[str, Any]:
        """
        图像合成

        Args:
            prompt: 合成描述
            images: 图像URL列表
            width: 输出宽度
            height: 输出高度
            sample_strength: 合成强度

        Returns:
            API响应
        """
        response = requests.post(
            f"{self.base_url}/image-composition",
            json={
                "prompt": prompt,
                "images": images,
                "width": width,
                "height": height,
                "sample_strength": sample_strength
            }
        )
        response.raise_for_status()
        return response.json()

    def text_to_video(
        self,
        prompt: str,
        resolution: str = "720p",
        width: int = 720,
        height: int = 480
    ) -> Dict[str, Any]:
        """
        文本生成视频

        Args:
            prompt: 视频描述
            resolution: 分辨率 (480p/720p/1080p)
            width: 视频宽度
            height: 视频高度

        Returns:
            API响应
        """
        response = requests.post(
            f"{self.base_url}/text-to-video",
            json={
                "prompt": prompt,
                "resolution": resolution,
                "width": width,
                "height": height
            }
        )
        response.raise_for_status()
        return response.json()

    def image_to_video(
        self,
        prompt: str,
        file_paths: list,
        resolution: str = "720p",
        width: int = 720,
        height: int = 480
    ) -> Dict[str, Any]:
        """
        图像生成视频

        Args:
            prompt: 动画描述
            file_paths: 图像URL列表
            resolution: 分辨率
            width: 视频宽度
            height: 视频高度

        Returns:
            API响应
        """
        response = requests.post(
            f"{self.base_url}/image-to-video",
            json={
                "prompt": prompt,
                "file_paths": file_paths,
                "resolution": resolution,
                "width": width,
                "height": height
            }
        )
        response.raise_for_status()
        return response.json()


def demo_basic_usage():
    """演示基本使用"""
    print("="*60)
    print("即梦MCP HTTP API - 基本使用演示")
    print("="*60)

    client = JiMengClient()

    # 1. 健康检查
    print("\n1. 检查服务器状态...")
    try:
        health = client.check_health()
        print(f"✅ 服务器状态: {health['status']}")
        print(f"   版本: {health['version']}")
        print(f"   模式: {health['mode']}")
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        print("\n请确保服务器正在运行:")
        print("   python -m jimeng_mcp.server --mode http")
        sys.exit(1)

    # 2. 获取工具列表
    print("\n2. 获取可用工具...")
    tools = client.list_tools()
    print(f"✅ 可用工具数量: {len(tools['tools'])}")
    for tool in tools['tools']:
        print(f"   - {tool['name']}: {tool['description'][:50]}...")

    # 3. 文本生成图像
    print("\n3. 文本生成图像...")
    print("   提示词: 可爱的卡通小马在花园里玩耍")
    try:
        result = client.text_to_image(
            prompt="可爱的卡通小马在花园里玩耍",
            width=1536,
            height=864,
            sample_strength=0.6
        )
        if result['success']:
            print("✅ 图像生成成功!")
            print(f"   结果:\n{result['result']}")
        else:
            print(f"❌ 生成失败: {result['error']}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")


def demo_image_generation():
    """演示图像生成功能"""
    print("\n" + "="*60)
    print("图像生成演示")
    print("="*60)

    client = JiMengClient()

    prompts = [
        "一只可爱的橙色小猫在阳光下睡觉",
        "未来城市的霓虹灯夜景",
        "水彩画风格的山水风景"
    ]

    for i, prompt in enumerate(prompts, 1):
        print(f"\n示例 {i}: {prompt}")
        try:
            result = client.text_to_image(
                prompt=prompt,
                sample_strength=0.7
            )
            if result['success']:
                print("✅ 生成成功")
                # 只显示前100个字符
                print(f"   {result['result'][:100]}...")
            else:
                print(f"❌ 生成失败: {result['error']}")
        except Exception as e:
            print(f"❌ 请求失败: {e}")


def main():
    """主函数"""
    print("\n即梦MCP HTTP API使用示例\n")

    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo-basic":
            demo_basic_usage()
        elif sys.argv[1] == "--demo-images":
            demo_image_generation()
        else:
            print("使用方法:")
            print("  python example_client.py              # 运行基本演示")
            print("  python example_client.py --demo-basic # 基本功能演示")
            print("  python example_client.py --demo-images # 图像生成演示")
    else:
        demo_basic_usage()


if __name__ == "__main__":
    main()
