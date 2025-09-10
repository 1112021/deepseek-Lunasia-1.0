# -*- coding: utf-8 -*-
"""
MCP客户端
用于与MCP服务器通信
"""

import asyncio
import json
import aiohttp
from typing import Dict, List, Any, Optional

class MCPClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_tool(self, tool_name: str, **kwargs) -> str:
        """调用MCP工具"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            payload = {
                "tool": tool_name,
                "parameters": kwargs
            }
            
            async with self.session.post(
                f"{self.server_url}/tools/call",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", "调用成功但无返回结果")
                else:
                    return f"调用失败: HTTP {response.status}"
        
        except asyncio.TimeoutError:
            return f"调用超时: {tool_name}"
        except Exception as e:
            return f"调用失败: {str(e)}"
    
    async def list_tools(self) -> List[str]:
        """获取可用工具列表"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                f"{self.server_url}/tools/list",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("tools", [])
                else:
                    return []
        
        except Exception as e:
            print(f"获取工具列表失败: {str(e)}")
            return []
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                f"{self.server_url}/tools/{tool_name}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
        
        except Exception as e:
            print(f"获取工具信息失败: {str(e)}")
            return {}

class LocalMCPClient:
    """本地MCP客户端，直接调用本地函数"""
    
    def __init__(self):
        from mcp_server import LocalMCPServer
        self.server = LocalMCPServer()
    
    async def call_tool(self, tool_name: str, **kwargs) -> str:
        """调用本地工具"""
        return self.server.call_tool(tool_name, **kwargs)
    
    async def list_tools(self) -> List[str]:
        """获取可用工具列表"""
        return self.server.list_tools()
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        return self.server.get_tool_info(tool_name)
    

