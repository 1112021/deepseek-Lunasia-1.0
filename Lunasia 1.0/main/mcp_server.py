# -*- coding: utf-8 -*-
"""
本地MCP服务器
提供各种工具功能供露尼西亚调用
"""

import json
import os
import sys
import subprocess
import platform
import datetime
from typing import Dict, List, Any, Optional

class LocalMCPServer:
    """本地MCP服务器 - 简化版本"""
    
    def __init__(self):
        self.tools = {
            "get_system_info": self.get_system_info,
            "list_files": self.list_files,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "create_folder": self.create_folder,
            "execute_command": self.execute_command,
            "get_process_list": self.get_process_list,
            "create_note": self.create_note,
            "list_notes": self.list_notes,
            "search_notes": self.search_notes,
            "get_weather_info": self.get_weather_info,
            "calculate": self.calculate,
            "get_memory_stats": self.get_memory_stats
        }
        
        # 加载自定义工具
        self.load_custom_tools()
    
    def get_system_info(self) -> str:
        """获取系统信息"""
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": sys.version,
            "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return json.dumps(info, ensure_ascii=False, indent=2)
    
    def list_files(self, directory: str = ".") -> str:
        """列出指定目录的文件"""
        try:
            if not os.path.exists(directory):
                return f"目录不存在: {directory}"
            
            files = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    files.append(f"文件: {item} ({size} bytes)")
                elif os.path.isdir(item_path):
                    files.append(f"目录: {item}/")
            
            return f"目录 {directory} 的内容:\n" + "\n".join(files)
        except Exception as e:
            return f"列出文件失败: {str(e)}"
    
    def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            if not os.path.exists(file_path):
                return f"文件不存在: {file_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"文件 {file_path} 的内容:\n{content}"
        except Exception as e:
            return f"读取文件失败: {str(e)}"
    
    def write_file(self, file_path: str, content: str) -> str:
        """写入文件内容"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"文件 {file_path} 写入成功"
        except Exception as e:
            return f"写入文件失败: {str(e)}"
    
    def create_folder(self, folder_path: str) -> str:
        """创建文件夹"""
        try:
            # 检查文件夹是否已存在
            if os.path.exists(folder_path):
                if os.path.isdir(folder_path):
                    return f"文件夹 {folder_path} 已存在"
                else:
                    return f"路径 {folder_path} 已存在，但不是文件夹"
            
            # 创建文件夹（包括父目录）
            os.makedirs(folder_path, exist_ok=True)
            
            return f"文件夹 {folder_path} 创建成功"
        except Exception as e:
            return f"创建文件夹失败: {str(e)}"
    
    def execute_command(self, command: str) -> str:
        """执行系统命令"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            output = {
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            return json.dumps(output, ensure_ascii=False, indent=2)
        except subprocess.TimeoutExpired:
            return f"命令执行超时: {command}"
        except Exception as e:
            return f"执行命令失败: {str(e)}"
    
    def get_process_list(self) -> str:
        """获取进程列表"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    "tasklist", 
                    capture_output=True, 
                    text=True
                )
            else:
                result = subprocess.run(
                    "ps aux", 
                    capture_output=True, 
                    text=True
                )
            
            return f"进程列表:\n{result.stdout}"
        except Exception as e:
            return f"获取进程列表失败: {str(e)}"
    
    def create_note(self, title: str, content: str, filename_format: str = "timestamp", location: str = None) -> str:
        """创建笔记"""
        try:
            # 确定保存位置
            if location:
                # 用户指定了位置
                if location.lower() in ["d盘", "d:", "d:/", "d:\\"]:
                    save_dir = "D:/"
                elif location.lower() in ["c盘", "c:", "c:/", "c:\\"]:
                    save_dir = "C:/"
                elif location.lower() in ["e盘", "e:", "e:/", "e:\\"]:
                    save_dir = "E:/"
                elif location.lower() in ["f盘", "f:", "f:/", "f:\\"]:
                    save_dir = "F:/"
                else:
                    # 尝试解析其他路径
                    save_dir = location
            else:
                # 默认保存到notes目录
                save_dir = "notes"
            
            # 确保目录存在
            os.makedirs(save_dir, exist_ok=True)
            
            # 根据文件名格式设置生成文件名
            if filename_format == "simple":
                # 简单格式：直接使用标题作为文件名
                filename = os.path.join(save_dir, f"{title}.txt")
                
                # 检查文件是否已存在，如果存在则添加数字后缀
                counter = 1
                original_filename = filename
                while os.path.exists(filename):
                    name_without_ext = original_filename[:-4]  # 移除.txt
                    filename = f"{name_without_ext}_{counter}.txt"
                    counter += 1
            else:
                # 时间戳格式：使用时间戳+标题
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(save_dir, f"{timestamp}_{title}.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"标题: {title}\n")
                f.write(f"创建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"内容:\n{content}\n")
            
            return f"笔记已创建: {filename}"
        except Exception as e:
            return f"创建笔记失败: {str(e)}"
    
    def list_notes(self) -> str:
        """列出所有笔记"""
        try:
            notes_dir = "notes"
            if not os.path.exists(notes_dir):
                return "没有找到笔记目录"
            
            notes = []
            for file in os.listdir(notes_dir):
                if file.endswith('.txt'):
                    file_path = os.path.join(notes_dir, file)
                    stat = os.stat(file_path)
                    notes.append(f"{file} (大小: {stat.st_size} bytes, 修改时间: {datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')})")
            
            if notes:
                return "笔记列表:\n" + "\n".join(notes)
            else:
                return "没有找到笔记"
        except Exception as e:
            return f"列出笔记失败: {str(e)}"
    
    def search_notes(self, keyword: str) -> str:
        """搜索笔记内容"""
        try:
            notes_dir = "notes"
            if not os.path.exists(notes_dir):
                return "没有找到笔记目录"
            
            results = []
            for file in os.listdir(notes_dir):
                if file.endswith('.txt'):
                    file_path = os.path.join(notes_dir, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if keyword.lower() in content.lower():
                                results.append(f"找到关键词 '{keyword}' 在文件: {file}")
                    except:
                        continue
            
            if results:
                return "搜索结果:\n" + "\n".join(results)
            else:
                return f"没有找到包含关键词 '{keyword}' 的笔记"
        except Exception as e:
            return f"搜索笔记失败: {str(e)}"
    
    def get_weather_info(self, city: str = "北京") -> str:
        """获取天气信息（使用和风天气API）"""
        try:
            import requests
            
            # 获取和风天气API密钥
            api_key = self.get_heweather_key()
            if not api_key:
                return "和风天气API密钥未配置，无法获取天气信息"
            
            # 调用和风天气API
            url = f"https://api.heweather.com/v3/weather/now"
            params = {
                "location": city,
                "key": api_key,
                "lang": "zh"
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "ok" and data.get("HeWeather3"):
                weather_data = data["HeWeather3"][0]
                now = weather_data.get("now", {})
                basic = weather_data.get("basic", {})
                update = weather_data.get("update", {})
                
                result = {
                    "city": basic.get("location", city),
                    "region": basic.get("admin_area", ""),
                    "country": basic.get("cnty", ""),
                    "weather": now.get("cond_txt", "未知"),
                    "temperature": f"{now.get('tmp', 'N/A')}°C",
                    "feels_like": f"{now.get('fl', 'N/A')}°C",
                    "wind_direction": now.get("wind_dir", "未知"),
                    "wind_scale": f"{now.get('wind_sc', 'N/A')}级",
                    "wind_speed": f"{now.get('wind_spd', 'N/A')}km/h",
                    "humidity": f"{now.get('hum', 'N/A')}%",
                    "precipitation": f"{now.get('pcpn', 'N/A')}mm",
                    "visibility": f"{now.get('vis', 'N/A')}km",
                    "cloud_cover": f"{now.get('cloud', 'N/A')}%",
                    "update_time": update.get("loc", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return f"获取{city}天气信息失败: {data.get('status', '未知错误')}"
                
        except Exception as e:
            return f"获取天气信息失败: {str(e)}"
    
    def get_heweather_key(self):
        """获取和风天气API密钥"""
        try:
            # 从配置文件读取API密钥
            if os.path.exists("ai_agent_config.json"):
                with open("ai_agent_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("heweather_key", "")
        except:
            pass
        return ""
    
    def calculate_distance(self, location1: str, location2: str) -> str:
        """计算两个地点之间的距离（使用高德地图API）"""
        try:
            import requests
            
            # 高德地图API密钥（需要用户配置）
            api_key = self.get_amap_key()
            if not api_key:
                return "高德地图API密钥未配置，无法计算距离"
            
            # 地理编码API获取坐标
            def get_coordinates(address):
                url = f"https://restapi.amap.com/v3/geocode/geo"
                params = {
                    "address": address,
                    "key": api_key,
                    "output": "json"
                }
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if data["status"] == "1" and data["geocodes"]:
                    location = data["geocodes"][0]["location"]
                    return location.split(",")
                return None
            
            # 获取两个地点的坐标
            coords1 = get_coordinates(location1)
            coords2 = get_coordinates(location2)
            
            if not coords1 or not coords2:
                return f"无法获取地点坐标：{location1} 或 {location2}"
            
            # 计算直线距离
            from math import radians, cos, sin, asin, sqrt
            
            def haversine_distance(lat1, lon1, lat2, lon2):
                """使用Haversine公式计算两点间的直线距离"""
                # 将经纬度转换为弧度
                lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
                
                # Haversine公式
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371  # 地球半径（公里）
                return c * r
            
            distance = haversine_distance(coords1[1], coords1[0], coords2[1], coords2[0])
            
            result = {
                "location1": location1,
                "location2": location2,
                "coordinates1": coords1,
                "coordinates2": coords2,
                "distance_km": round(distance, 2),
                "distance_m": round(distance * 1000, 0),
                "calculation_type": "直线距离（Haversine公式）",
                "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"计算距离失败: {str(e)}"
    
    def get_amap_key(self):
        """获取高德地图API密钥"""
        try:
            # 从配置文件读取API密钥
            if os.path.exists("ai_agent_config.json"):
                with open("ai_agent_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    api_key = config.get("amap_key", "")
                    # 如果API密钥为空或为占位符，返回空字符串
                    if not api_key or api_key == "MYKEY" or api_key == "mykey":
                        return ""
                    return api_key
        except Exception as e:
            print(f"读取高德地图API密钥失败: {str(e)}")
        return ""
    
    def calculate(self, expression: str) -> str:
        """计算数学表达式"""
        try:
            # 安全计算，只允许基本数学运算
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                return "表达式包含不允许的字符"
            
            result = eval(expression)
            return f"计算结果: {expression} = {result}"
        except Exception as e:
            return f"计算失败: {str(e)}"
    
    def get_memory_stats(self) -> str:
        """获取记忆系统统计信息"""
        try:
            memory_file = "memory_lake.json"
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        total_topics = len(data)
                    elif isinstance(data, dict):
                        total_topics = len(data.get("topics", []))
                    else:
                        total_topics = 0
            else:
                total_topics = 0
            
            chat_logs_dir = "chat_logs"
            total_log_files = len([f for f in os.listdir(chat_logs_dir) if f.endswith('.json')]) if os.path.exists(chat_logs_dir) else 0
            
            stats = {
                "total_topics": total_topics,
                "total_log_files": total_log_files,
                "memory_file_size": os.path.getsize(memory_file) if os.path.exists(memory_file) else 0
            }
            
            return json.dumps(stats, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"获取记忆统计失败: {str(e)}"
    
    def call_tool(self, tool_name: str, **kwargs) -> str:
        """调用工具"""
        if tool_name in self.tools:
            try:
                return self.tools[tool_name](**kwargs)
            except Exception as e:
                return f"调用工具失败: {str(e)}"
        else:
            return f"工具不存在: {tool_name}"
    
    def list_tools(self) -> List[str]:
        """列出可用工具"""
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        if tool_name in self.tools:
            return {
                "name": tool_name,
                "description": self.tools[tool_name].__doc__ or "无描述"
            }
        return {}
    
    def load_custom_tools(self):
        """加载自定义工具"""
        try:
            if os.path.exists("custom_tools.json"):
                with open("custom_tools.json", "r", encoding="utf-8") as f:
                    custom_tools = json.load(f)
                    for tool_name, tool_info in custom_tools.items():
                        if tool_info.get("type") == "custom":
                            # 动态创建工具函数
                            self.create_custom_tool(tool_name, tool_info)
        except Exception as e:
            print(f"加载自定义工具失败: {str(e)}")
    
    def create_custom_tool(self, tool_name, tool_info):
        """创建自定义工具"""
        try:
            # 创建工具函数的命名空间
            namespace = {}
            
            # 执行工具代码
            exec(tool_info["code"], namespace)
            
            # 创建包装函数
            def tool_wrapper(**kwargs):
                # 根据工具名称和参数判断调用哪个函数
                if tool_name == "智能文件分析":
                    # 文件分析工具
                    if 'file_path' in kwargs:
                        if 'analyze_file_content' in namespace:
                            # 直接调用analyze_file_content返回JSON格式
                            return namespace['analyze_file_content'](kwargs['file_path'])
                        elif 'upload_and_analyze_file' in namespace:
                            return namespace['upload_and_analyze_file'](kwargs['file_path'])
                        else:
                            return "文件分析功能未找到"
                    else:
                        return "请提供file_path参数"
                elif 'location1' in kwargs and 'location2' in kwargs:
                    # 调用距离计算函数
                    if 'calculate_distance' in namespace:
                        return namespace['calculate_distance'](kwargs['location1'], kwargs['location2'])
                elif 'keyword' in kwargs:
                    # 调用兴趣点搜索函数
                    if 'search_poi' in namespace:
                        city = kwargs.get('city', '北京')
                        return namespace['search_poi'](kwargs['keyword'], city)
                elif 'city' in kwargs and 'keyword' not in kwargs:
                    # 调用天气预报函数
                    if 'get_weather_forecast' in namespace:
                        return namespace['get_weather_forecast'](kwargs['city'])
                else:
                    return f"参数错误，请提供正确的参数。可用功能：距离计算(location1, location2)、兴趣点搜索(keyword, city)、天气预报(city)、文件分析(file_path)"
            
            # 将包装函数添加到工具列表
            self.tools[tool_name] = tool_wrapper
            
        except Exception as e:
            print(f"创建自定义工具 {tool_name} 失败: {str(e)}")
    
    def reload_custom_tools(self):
        """重新加载自定义工具"""
        # 移除现有的自定义工具
        custom_tools = self.get_custom_tools_config()
        for tool_name in custom_tools.keys():
            if tool_name in self.tools:
                del self.tools[tool_name]
        
        # 重新加载
        self.load_custom_tools()
    
    def get_custom_tools_config(self):
        """获取自定义工具配置"""
        try:
            if os.path.exists("custom_tools.json"):
                with open("custom_tools.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}

if __name__ == "__main__":
    server = LocalMCPServer()
    print("本地MCP服务器已启动")
    print("可用工具:", server.list_tools())
    print("\n测试工具调用:")
    print("系统信息:", server.call_tool("get_system_info"))
