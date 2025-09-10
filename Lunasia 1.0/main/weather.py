# -*- coding: utf-8 -*-
"""
天气功能模块
处理天气相关的API调用和数据处理
"""

import requests

class WeatherTool:
    """天气API工具类"""
    
    @staticmethod
    def get_weather(location="北京", api_key=""):
        """获取天气信息"""
        # 使用API获取天气
        if not api_key:
            return "天气服务未配置API密钥"

        # 使用和风天气API
        try:
            # 正确的和风天气API URL格式
            url = f"https://devapi.qweather.com/v7/weather/now"
            params = {
                "location": location,
                "key": api_key,
                "lang": "zh"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('code') != '200':
                return f"获取天气数据失败: {data.get('code', '未知错误')}"

            weather_data = data['now']
            location_data = data.get('location', [{}])[0] if 'location' in data else {}

            # 提取天气信息
            weather_info = {
                '城市': location_data.get('name', location),
                '地区': location_data.get('adm1', ''),
                '国家': location_data.get('country', ''),
                '天气状况': weather_data.get('text', '未知'),
                '温度': f"{weather_data.get('temp', 'N/A')}°C",
                '体感温度': f"{weather_data.get('feelsLike', 'N/A')}°C",
                '风向': weather_data.get('windDir', '未知'),
                '风力等级': f"{weather_data.get('windScale', 'N/A')}级",
                '风速': f"{weather_data.get('windSpeed', 'N/A')}km/h",
                '湿度': f"{weather_data.get('humidity', 'N/A')}%",
                '降水量': f"{weather_data.get('precip', 'N/A')}mm",
                '能见度': f"{weather_data.get('vis', 'N/A')}km",
                '云量': f"{weather_data.get('cloud', 'N/A')}%",
                '更新时间': weather_data.get('obsTime', '未知')
            }

            # 格式化输出
            result = "📍 当前天气信息:\n"
            for key, value in weather_info.items():
                if value and value != 'N/A' and value != '未知':
                    result += f"🌤️ {key}: {value}\n"

            return result
        except Exception as e:
            print(f"获取天气数据失败: {str(e)}")
            return f"{location}的天气：获取失败，请检查API配置"
