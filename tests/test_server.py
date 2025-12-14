"""
即梦MCP服务器基础测试

运行测试:
    pytest tests/
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from jimeng_mcp.server import make_api_request


@pytest.mark.asyncio
async def test_make_api_request_success():
    """测试成功的API请求"""
    with patch("jimeng_mcp.server.httpx.AsyncClient") as mock_client:
        # 模拟响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "created": 1763099855,
            "data": [{"url": "https://example.com/image.png"}]
        }
        mock_response.raise_for_status = MagicMock()

        # 模拟客户端上下文管理器
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # 测试请求
        result = await make_api_request(
            "/v1/images/generations",
            {"model": "jimeng-4.5", "prompt": "test"}
        )

        assert "data" in result
        assert len(result["data"]) == 1
        assert "url" in result["data"][0]


@pytest.mark.asyncio
async def test_make_api_request_with_custom_timeout():
    """测试带自定义超时的API请求"""
    with patch("jimeng_mcp.server.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # 使用自定义超时进行测试
        await make_api_request(
            "/v1/videos/generations",
            {"model": "jimeng-video-3.0", "prompt": "test"},
            timeout=600
        )

        # 验证超时参数是否传递给客户端
        mock_client.assert_called_once_with(timeout=600)


def test_environment_variables():
    """测试环境变量加载"""
    import os
    from dotenv import load_dotenv

    # 保存原始值
    original_api_key = os.environ.get("JIMENG_API_KEY")
    original_api_url = os.environ.get("JIMENG_API_URL")

    try:
        # 创建临时.env文件
        with open(".env.test", "w") as f:
            f.write("JIMENG_API_KEY=test_key\n")
            f.write("JIMENG_API_URL=https://test.example.com\n")

        # 清除现有值并加载测试环境变量
        os.environ.pop("JIMENG_API_KEY", None)
        os.environ.pop("JIMENG_API_URL", None)
        load_dotenv(".env.test", override=True)

        # 验证变量可以被读取
        api_key = os.getenv("JIMENG_API_KEY")
        api_url = os.getenv("JIMENG_API_URL")

        assert api_key == "test_key"
        assert api_url == "https://test.example.com"
    finally:
        # 清理并恢复原始值
        os.remove(".env.test")
        if original_api_key:
            os.environ["JIMENG_API_KEY"] = original_api_key
        if original_api_url:
            os.environ["JIMENG_API_URL"] = original_api_url


if __name__ == "__main__":
    pytest.main([__file__])
