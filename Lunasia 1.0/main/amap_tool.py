#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高德地图API工具类
"""

import requests
import json
from typing import Optional

class AmapTool:
    """高德地图API工具类"""
    
    @staticmethod
    def get_weather(location="北京", api_key=""):
        """获取天气信息"""
        if not api_key:
            return "高德地图API密钥未配置"
        
        try:
            # 第一步：地理编码，获取城市代码
            geocode_url = "https://restapi.amap.com/v3/geocode/geo"
            geocode_params = {
                "address": location,
                "key": api_key,
                "output": "json"
            }
            
            geocode_response = requests.get(geocode_url, params=geocode_params, timeout=10)
            geocode_data = geocode_response.json()
            
            if geocode_data["status"] != "1" or not geocode_data["geocodes"]:
                return f"无法找到城市 '{location}' 的地理信息"
            
            # 获取城市代码
            adcode = geocode_data["geocodes"][0]["adcode"]
            city_name = geocode_data["geocodes"][0]["formatted_address"]
            
            # 第二步：获取天气预报
            weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
            weather_params = {
                "key": api_key,
                "city": adcode,
                "extensions": "all",
                "output": "json"
            }
            
            weather_response = requests.get(weather_url, params=weather_params, timeout=10)
            weather_data = weather_response.json()
            
            if weather_data["status"] != "1":
                return f"获取天气信息失败: {weather_data.get('info', '未知错误')}"
            
            # 解析天气数据
            forecasts = weather_data.get("forecasts", [])
            if not forecasts:
                return "未获取到天气预报数据"
            
            forecast = forecasts[0]
            city_info = forecast.get("city", "")
            report_time = forecast.get("report_time", "")
            
            # 获取实时天气
            casts = forecast.get("casts", [])
            if not casts:
                return "未获取到天气数据"
            
            today_weather = casts[0]
            
            # 构建天气信息
            weather_info = f"📍 {city_info}\n"
            weather_info += f"🕐 更新时间: {report_time}\n\n"
            
            # 今日天气
            date = today_weather.get("date", "")
            week = today_weather.get("week", "")
            dayweather = today_weather.get("dayweather", "")
            nightweather = today_weather.get("nightweather", "")
            daytemp = today_weather.get("daytemp", "")
            nighttemp = today_weather.get("nighttemp", "")
            daywind = today_weather.get("daywind", "")
            nightwind = today_weather.get("nightwind", "")
            daypower = today_weather.get("daypower", "")
            nightpower = today_weather.get("nightpower", "")
            
            weather_info += f"📅 {date} ({week})\n"
            weather_info += f"🌅 白天: {dayweather} {daytemp}°C {daywind}风{daypower}级\n"
            weather_info += f"🌙 夜间: {nightweather} {nighttemp}°C {nightwind}风{nightpower}级\n\n"
            
            # 未来几天预报
            if len(casts) > 1:
                weather_info += "📊 未来几天预报:\n"
                for i, cast in enumerate(casts[1:4], 1):  # 显示未来3天
                    date = cast.get("date", "")
                    week = cast.get("week", "")
                    dayweather = cast.get("dayweather", "")
                    daytemp = cast.get("daytemp", "")
                    nighttemp = cast.get("nighttemp", "")
                    weather_info += f"  {i}. {date}({week}) {dayweather} {nighttemp}°C~{daytemp}°C\n"
            
            return weather_info
            
        except requests.exceptions.Timeout:
            return "请求超时，请检查网络连接"
        except requests.exceptions.RequestException as e:
            return f"网络请求失败: {str(e)}"
        except json.JSONDecodeError:
            return "API响应格式错误"
        except Exception as e:
            return f"获取天气信息时发生错误: {str(e)}"
    
    @staticmethod
    def get_location_info(location="北京", api_key=""):
        """获取位置信息"""
        if not api_key:
            return "高德地图API密钥未配置"
        
        try:
            geocode_url = "https://restapi.amap.com/v3/geocode/geo"
            geocode_params = {
                "address": location,
                "key": api_key,
                "output": "json"
            }
            
            response = requests.get(geocode_url, params=geocode_params, timeout=10)
            data = response.json()
            
            if data["status"] != "1" or not data["geocodes"]:
                return f"无法找到位置 '{location}' 的信息"
            
            geocode = data["geocodes"][0]
            formatted_address = geocode.get("formatted_address", "")
            province = geocode.get("province", "")
            city = geocode.get("city", "")
            district = geocode.get("district", "")
            location_coords = geocode.get("location", "")
            
            location_info = f"📍 位置信息:\n"
            location_info += f"   详细地址: {formatted_address}\n"
            location_info += f"   省份: {province}\n"
            location_info += f"   城市: {city}\n"
            location_info += f"   区县: {district}\n"
            location_info += f"   坐标: {location_coords}"
            
            return location_info
            
        except Exception as e:
            return f"获取位置信息时发生错误: {str(e)}"
