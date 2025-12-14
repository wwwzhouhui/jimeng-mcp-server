"""
即梦MCP服务器

本服务器为即梦AI图像和视频生成提供MCP工具:
- text_to_image: 文本生成图像
- image_composition: 多图合成
- text_to_video: 文本生成视频
- image_to_video: 图像生成视频

支持三种通信模式:
- stdio: 标准输入/输出 (默认,用于Claude Desktop)
- sse: Server-Sent Events (用于Web客户端)
- http: HTTP REST API (用于API集成)
"""

import asyncio
import os
import sys
import argparse
from typing import Any, Optional
from dotenv import load_dotenv
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# 尝试导入SSE和HTTP支持(可选依赖)
try:
    from mcp.server.sse import SseServerTransport
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

try:
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False

# 加载环境变量
load_dotenv()

# 配置
API_BASE_URL = os.getenv("JIMENG_API_URL", "https://jimeng.duckcloud.fun")
API_KEY = os.getenv("JIMENG_API_KEY", "")
DEFAULT_MODEL = os.getenv("JIMENG_MODEL", "jimeng-4.5")

if not API_KEY:
    raise ValueError("JIMENG_API_KEY 环境变量是必需的")

# 创建服务器实例
server = Server("jimeng-mcp")


async def make_api_request(
    endpoint: str,
    data: dict[str, Any],
    timeout: int = 300
) -> dict[str, Any]:
    """向即梦API发起请求

    Args:
        endpoint: API端点
        data: 请求数据
        timeout: 超时时间(秒),默认300秒

    Returns:
        API响应数据
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print(f"🔄 正在请求即梦API: {endpoint}")
    print(f"⏱️  超时时间: {timeout}秒")

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            print(f"✅ API请求成功")
            print(f"📦 返回数据: {result}")
            return result
    except httpx.TimeoutException as e:
        print(f"❌ API请求超时: {timeout}秒")
        raise Exception(f"API请求超时({timeout}秒)，即梦API可能响应较慢，请稍后重试") from e
    except httpx.HTTPStatusError as e:
        print(f"❌ API请求失败: HTTP {e.response.status_code}")
        raise Exception(f"API请求失败: {e.response.text}") from e
    except Exception as e:
        print(f"❌ API请求异常: {str(e)}")
        raise


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="text_to_image",
            description=(
                "使用即梦4.5根据文本提示生成图像。"
                "基于详细的文本描述创建高质量图像。"
                "支持多种宽高比和分辨率，jimeng-4.5/4.1/4.0支持智能多图生成。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "要生成图像的详细文本描述，jimeng-4.x支持多图生成（如'生成4张连续场景的图片'）"
                    },
                    "negative_prompt": {
                        "type": "string",
                        "description": "在生成的图像中要避免的内容(可选)",
                        "default": ""
                    },
                    "ratio": {
                        "type": "string",
                        "description": "图像宽高比",
                        "default": "1:1",
                        "enum": ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9"]
                    },
                    "resolution": {
                        "type": "string",
                        "description": "图像分辨率",
                        "default": "2k",
                        "enum": ["1k", "2k", "4k"]
                    },
                    "sample_strength": {
                        "type": "number",
                        "description": "精细度(0.0-1.0),数值越高越精细",
                        "default": 0.5,
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "model": {
                        "type": "string",
                        "description": "用于生成的模型(jimeng-4.5推荐, jimeng-4.1, jimeng-4.0等)",
                        "default": DEFAULT_MODEL
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="image_composition",
            description=(
                "使用即梦4.5合成/融合多张图像。"
                "接受1-10张图像,根据文本提示将它们组合在一起。"
                "适用于图像混合、风格迁移或创建合成图像。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "如何合成图像的描述"
                    },
                    "images": {
                        "type": "array",
                        "description": "要合成的图像URL数组(1-10张图像)",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1,
                        "maxItems": 10
                    },
                    "ratio": {
                        "type": "string",
                        "description": "输出图像宽高比",
                        "default": "1:1",
                        "enum": ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9"]
                    },
                    "resolution": {
                        "type": "string",
                        "description": "输出图像分辨率",
                        "default": "2k",
                        "enum": ["1k", "2k", "4k"]
                    },
                    "sample_strength": {
                        "type": "number",
                        "description": "精细度(0.0-1.0)",
                        "default": 0.5,
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "model": {
                        "type": "string",
                        "description": "用于合成的模型",
                        "default": DEFAULT_MODEL
                    }
                },
                "required": ["prompt", "images"]
            }
        ),
        Tool(
            name="text_to_video",
            description=(
                "使用即梦视频3.0根据文本提示生成视频。"
                "基于文本描述创建短视频剪辑。"
                "支持多种宽高比、分辨率和时长设置。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "要生成视频的详细文本描述"
                    },
                    "ratio": {
                        "type": "string",
                        "description": "视频宽高比",
                        "default": "1:1",
                        "enum": ["1:1", "4:3", "3:4", "16:9", "9:16"]
                    },
                    "resolution": {
                        "type": "string",
                        "description": "视频分辨率",
                        "default": "720p",
                        "enum": ["480p", "720p", "1080p"]
                    },
                    "duration": {
                        "type": "integer",
                        "description": "视频时长(秒)",
                        "default": 5,
                        "enum": [5, 10]
                    },
                    "model": {
                        "type": "string",
                        "description": "用于视频生成的模型",
                        "default": "jimeng-video-3.0"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="image_to_video",
            description=(
                "使用即梦视频3.0从图像生成视频。"
                "接受一张或多张图像作为首帧/尾帧,根据文本提示为它们添加动画效果。"
                "适用于从静态图像创建动画。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "如何为图像添加动画效果的描述"
                    },
                    "file_paths": {
                        "type": "array",
                        "description": "首帧/尾帧图像URL数组",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1
                    },
                    "ratio": {
                        "type": "string",
                        "description": "视频宽高比",
                        "default": "1:1",
                        "enum": ["1:1", "4:3", "3:4", "16:9", "9:16"]
                    },
                    "resolution": {
                        "type": "string",
                        "description": "视频分辨率",
                        "default": "720p",
                        "enum": ["480p", "720p", "1080p"]
                    },
                    "duration": {
                        "type": "integer",
                        "description": "视频时长(秒)",
                        "default": 5,
                        "enum": [5, 10]
                    },
                    "model": {
                        "type": "string",
                        "description": "用于视频生成的模型",
                        "default": "jimeng-video-3.0"
                    }
                },
                "required": ["prompt", "file_paths"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict[str, Any] | None
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """处理工具调用"""

    if not arguments:
        raise ValueError("参数是必需的")

    try:
        if name == "text_to_image":
            # 准备请求数据
            model = arguments.get("model", DEFAULT_MODEL)
            prompt = arguments["prompt"]
            ratio = arguments.get("ratio", "1:1")
            resolution = arguments.get("resolution", "2k")
            data = {
                "model": model,
                "prompt": prompt,
                "negative_prompt": arguments.get("negative_prompt", ""),
                "ratio": ratio,
                "resolution": resolution,
                "sample_strength": arguments.get("sample_strength", 0.5)
            }

            print(f"\n{'='*60}")
            print(f"🎨 开始生成图像")
            print(f"📝 模型: {model}")
            print(f"💬 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"📐 宽高比: {ratio}, 分辨率: {resolution}")
            print(f"{'='*60}\n")

            # 发起API请求
            # 服务端 generateImages 无超时限制，客户端设置15分钟保护
            # 理由: 服务端每秒轮询一次，理论上无限循环，客户端必须设置合理超时
            print(f"⏳ 正在生成图像，这可能需要1-3分钟，请耐心等待...")
            result = await make_api_request("/v1/images/generations", data, timeout=900)

            # 格式化响应
            urls = [item["url"] for item in result.get("data", [])]

            if not urls:
                error_msg = "图像生成失败,未返回任何URL"
                print(f"❌ {error_msg}")
                return [TextContent(type="text", text=error_msg)]

            print(f"✅ 图像生成成功! 共生成 {len(urls)} 张图像\n")

            response_text = f"✅ 成功生成 {len(urls)} 张图像\n\n"
            response_text += "📷 图像URL列表:\n"
            response_text += "=" * 60 + "\n"
            for i, url in enumerate(urls, 1):
                response_text += f"\n图像 {i}:\n{url}\n"
            response_text += "\n" + "=" * 60
            response_text += "\n\n💡 提示: 点击URL即可在浏览器中查看图像"

            return [TextContent(type="text", text=response_text)]

        elif name == "image_composition":
            # 准备请求数据
            model = arguments.get("model", DEFAULT_MODEL)
            prompt = arguments["prompt"]
            ratio = arguments.get("ratio", "1:1")
            resolution = arguments.get("resolution", "2k")
            data = {
                "model": model,
                "prompt": prompt,
                "images": arguments["images"],
                "ratio": ratio,
                "resolution": resolution,
                "sample_strength": arguments.get("sample_strength", 0.5)
            }

            print(f"\n{'='*60}")
            print(f"🎨 开始图像合成")
            print(f"📝 模型: {model}")
            print(f"💬 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"🖼️  输入图像数: {len(arguments['images'])}")
            print(f"📐 宽高比: {ratio}, 分辨率: {resolution}")
            print(f"{'='*60}\n")

            # 发起API请求
            # 服务端 generateImageComposition 最大轮询600次(10分钟)，客户端设置11分钟
            # 理由: 服务端每秒轮询一次，最多600秒，客户端需要略大于此值以接收完整响应
            print(f"⏳ 正在合成图像，这可能需要1-3分钟，请耐心等待...")
            result = await make_api_request("/v1/images/compositions", data, timeout=660)

            # 格式化响应
            urls = [item["url"] for item in result.get("data", [])]
            input_count = result.get("input_images", len(arguments["images"]))
            comp_type = result.get("composition_type", "composition")

            if not urls:
                error_msg = "图像合成失败,未返回任何URL"
                print(f"❌ {error_msg}")
                return [TextContent(type="text", text=error_msg)]

            print(f"✅ 图像合成成功! 共生成 {len(urls)} 张图像\n")

            response_text = f"✅ 成功将 {input_count} 张图像合成为 {len(urls)} 个结果\n"
            response_text += f"🎨 合成类型: {comp_type}\n\n"
            response_text += "📷 合成结果URL列表:\n"
            response_text += "=" * 60 + "\n"
            for i, url in enumerate(urls, 1):
                response_text += f"\n合成图像 {i}:\n{url}\n"
            response_text += "\n" + "=" * 60
            response_text += "\n\n💡 提示: 点击URL即可在浏览器中查看合成图像"

            return [TextContent(type="text", text=response_text)]

        elif name == "text_to_video":
            # 准备请求数据
            model = arguments.get("model", "jimeng-video-3.0")
            prompt = arguments["prompt"]
            ratio = arguments.get("ratio", "1:1")
            resolution = arguments.get("resolution", "720p")
            duration = arguments.get("duration", 5)
            data = {
                "model": model,
                "prompt": prompt,
                "ratio": ratio,
                "resolution": resolution,
                "duration": duration
            }

            print(f"\n{'='*60}")
            print(f"🎬 开始生成视频")
            print(f"📝 模型: {model}")
            print(f"💬 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"📐 宽高比: {ratio}, 分辨率: {resolution}, 时长: {duration}秒")
            print(f"{'='*60}\n")

            # 发起API请求
            print(f"⏳ 正在生成视频，这可能需要较长时间，请耐心等待...")
            result = await make_api_request("/v1/videos/generations", data, timeout=600)

            # 格式化响应
            videos = result.get("data", [])

            if not videos:
                error_msg = "视频生成失败,未返回任何URL"
                print(f"❌ {error_msg}")
                return [TextContent(type="text", text=error_msg)]

            print(f"✅ 视频生成成功! 共生成 {len(videos)} 个视频\n")

            response_text = f"✅ 成功生成 {len(videos)} 个视频\n\n"
            response_text += "🎬 视频URL列表:\n"
            response_text += "=" * 60 + "\n"

            for i, video in enumerate(videos, 1):
                url = video.get("url", "")
                revised_prompt = video.get("revised_prompt", arguments["prompt"])
                response_text += f"\n视频 {i}:\n"
                response_text += f"URL: {url}\n"
                response_text += f"提示词: {revised_prompt}\n"

            response_text += "\n" + "=" * 60
            response_text += "\n\n💡 提示: 点击URL即可在浏览器中查看视频"

            return [TextContent(type="text", text=response_text)]

        elif name == "image_to_video":
            # 准备请求数据
            model = arguments.get("model", "jimeng-video-3.0")
            prompt = arguments["prompt"]
            file_paths = arguments["file_paths"]
            ratio = arguments.get("ratio", "1:1")
            resolution = arguments.get("resolution", "720p")
            duration = arguments.get("duration", 5)
            data = {
                "model": model,
                "prompt": prompt,
                "file_paths": file_paths,
                "ratio": ratio,
                "resolution": resolution,
                "duration": duration
            }

            print(f"\n{'='*60}")
            print(f"🎬 开始图像生成视频")
            print(f"📝 模型: {model}")
            print(f"💬 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            print(f"🖼️  输入图像数: {len(file_paths)}")
            print(f"📐 宽高比: {ratio}, 分辨率: {resolution}, 时长: {duration}秒")
            print(f"{'='*60}\n")

            # 发起API请求
            print(f"⏳ 正在生成视频，这可能需要较长时间，请耐心等待...")
            result = await make_api_request("/v1/videos/generations", data, timeout=600)

            # 格式化响应
            videos = result.get("data", [])

            if not videos:
                error_msg = "视频生成失败,未返回任何URL"
                print(f"❌ {error_msg}")
                return [TextContent(type="text", text=error_msg)]

            print(f"✅ 视频生成成功! 共生成 {len(videos)} 个视频\n")

            response_text = f"✅ 成功从 {len(file_paths)} 张图像生成 {len(videos)} 个视频\n\n"
            response_text += "🎬 视频URL列表:\n"
            response_text += "=" * 60 + "\n"

            for i, video in enumerate(videos, 1):
                url = video.get("url", "")
                revised_prompt = video.get("revised_prompt", arguments["prompt"])
                response_text += f"\n视频 {i}:\n"
                response_text += f"URL: {url}\n"
                response_text += f"提示词: {revised_prompt}\n"

            response_text += "\n" + "=" * 60
            response_text += "\n\n💡 提示: 点击URL即可在浏览器中查看视频"

            return [TextContent(type="text", text=response_text)]

        else:
            raise ValueError(f"未知工具: {name}")

    except httpx.HTTPStatusError as e:
        error_msg = f"API请求失败,状态码 {e.response.status_code}: {e.response.text}"
        return [TextContent(type="text", text=error_msg)]
    except Exception as e:
        error_msg = f"执行 {name} 时出错: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def run_stdio_server():
    """运行stdio模式的MCP服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jimeng-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


async def run_sse_server(host: str = "0.0.0.0", port: int = 8000):
    """运行SSE模式的MCP服务器"""
    if not SSE_AVAILABLE:
        raise RuntimeError(
            "SSE模式需要安装SSE相关依赖。\n"
            "请运行: pip install starlette uvicorn sse-starlette"
        )

    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import Response
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn

    # 创建 SSE 传输层
    sse_transport = SseServerTransport("/messages")

    # 定义 SSE 处理函数
    async def handle_sse(request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                InitializationOptions(
                    server_name="jimeng-mcp",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )
        # 返回空响应以避免 TypeError
        return Response()

    # 启动事件
    async def startup():
        print(f"\n🚀 即梦MCP服务器 (SSE模式) 运行在 http://{host}:{port}/sse")
        print(f"📝 消息端点: http://{host}:{port}/messages\n")

    # 创建路由
    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages", app=sse_transport.handle_post_message),
        ],
        on_startup=[startup]
    )

    # 添加CORS支持
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 启动 uvicorn 服务器
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


async def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """运行HTTP REST API模式的MCP服务器"""
    if not HTTP_AVAILABLE:
        raise RuntimeError(
            "HTTP模式需要安装额外依赖。\n"
            "请运行: pip install starlette uvicorn"
        )

    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse

    async def handle_text_to_image(request):
        """处理文本生成图像请求"""
        try:
            data = await request.json()
            result = await handle_call_tool("text_to_image", data)
            return JSONResponse({
                "success": True,
                "result": result[0].text if result else ""
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": str(e)
            }, status_code=500)

    async def handle_image_composition(request):
        """处理图像合成请求"""
        try:
            data = await request.json()
            result = await handle_call_tool("image_composition", data)
            return JSONResponse({
                "success": True,
                "result": result[0].text if result else ""
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": str(e)
            }, status_code=500)

    async def handle_text_to_video(request):
        """处理文本生成视频请求"""
        try:
            data = await request.json()
            result = await handle_call_tool("text_to_video", data)
            return JSONResponse({
                "success": True,
                "result": result[0].text if result else ""
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": str(e)
            }, status_code=500)

    async def handle_image_to_video(request):
        """处理图像生成视频请求"""
        try:
            data = await request.json()
            result = await handle_call_tool("image_to_video", data)
            return JSONResponse({
                "success": True,
                "result": result[0].text if result else ""
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": str(e)
            }, status_code=500)

    async def handle_health(request):
        """健康检查端点"""
        return JSONResponse({
            "status": "healthy",
            "server": "jimeng-mcp",
            "version": "0.1.0",
            "mode": "http"
        })

    async def handle_tools(request):
        """列出可用工具"""
        tools = await handle_list_tools()
        return JSONResponse({
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        })

    app = Starlette(
        routes=[
            Route("/health", endpoint=handle_health, methods=["GET"]),
            Route("/tools", endpoint=handle_tools, methods=["GET"]),
            Route("/text-to-image", endpoint=handle_text_to_image, methods=["POST"]),
            Route("/image-composition", endpoint=handle_image_composition, methods=["POST"]),
            Route("/text-to-video", endpoint=handle_text_to_video, methods=["POST"]),
            Route("/image-to-video", endpoint=handle_image_to_video, methods=["POST"]),
        ]
    )

    # 添加CORS支持
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    import uvicorn
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)

    print(f"🚀 即梦MCP服务器 (HTTP模式) 运行在 http://{host}:{port}")
    print(f"📚 API文档:")
    print(f"   - 健康检查: GET  http://{host}:{port}/health")
    print(f"   - 工具列表: GET  http://{host}:{port}/tools")
    print(f"   - 文本生成图像: POST http://{host}:{port}/text-to-image")
    print(f"   - 图像合成: POST http://{host}:{port}/image-composition")
    print(f"   - 文本生成视频: POST http://{host}:{port}/text-to-video")
    print(f"   - 图像生成视频: POST http://{host}:{port}/image-to-video")
    await server_instance.serve()


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="即梦MCP服务器 - 支持stdio/sse/http三种模式"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="服务器模式 (默认: stdio)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="SSE/HTTP模式的主机地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="SSE/HTTP模式的端口号 (默认: 8000)"
    )
    return parser.parse_args()


async def main():
    """服务器主入口"""
    args = parse_args()

    if args.mode == "stdio":
        print("🚀 即梦MCP服务器启动 (stdio模式)", file=sys.stderr)
        await run_stdio_server()
    elif args.mode == "sse":
        await run_sse_server(args.host, args.port)
    elif args.mode == "http":
        await run_http_server(args.host, args.port)
    else:
        print(f"❌ 未知的模式: {args.mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
