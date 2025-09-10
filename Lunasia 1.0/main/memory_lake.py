# -*- coding: utf-8 -*-
"""
记忆系统模块 - 识底深湖
处理对话记忆、主题总结和上下文回忆
"""

import json
import os
import datetime
import re
import openai
from config import load_config
from memory_summary_agent import MemorySummaryAgent

class MemoryLake:
    """记忆系统 - 识底深湖"""
    
    def __init__(self, memory_file="memory_lake.json", chat_logs_dir="chat_logs"):
        self.memory_file = memory_file
        self.chat_logs_dir = chat_logs_dir
        self.memory_index = self.load_memory()
        self.current_conversation = []
        self.last_save_date = None
        self.config = load_config()
        
        # 初始化记忆总结AI代理
        self.summary_agent = MemorySummaryAgent(self.config)
        
        # 🚀 修复：初始化mark_saved_callback属性
        self.mark_saved_callback = None
        
        # 确保目录存在
        if not os.path.exists(self.chat_logs_dir):
            os.makedirs(self.chat_logs_dir)
        
        # 确保第一条记忆是重点记忆
        self.ensure_first_memory_important()

    def load_memory(self):
        """加载记忆索引"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 兼容旧格式：如果是数组，转换为新格式
                    if isinstance(data, list):
                        return {"topics": data, "conversations": {}, "contexts": {}}
                    elif isinstance(data, dict):
                        return data
                    else:
                        return {"topics": [], "conversations": {}, "contexts": {}}
            except:
                return {"topics": [], "conversations": {}, "contexts": {}}
        return {"topics": [], "conversations": {}, "contexts": {}}

    def save_memory(self):
        """保存记忆索引"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory_index, f, ensure_ascii=False, indent=2)

    def add_conversation(self, user_input, ai_response, developer_mode=False, mark_saved_callback=None):
        """添加对话到当前会话"""
        # 开发者模式下不保存到记忆系统
        if developer_mode:
            print("🔧 开发者模式已开启，跳过对话记录到记忆系统")
            return
        
        # 🚀 修复：防重复添加机制
        # 检查是否已经存在相同的对话
        for existing_conv in self.current_conversation:
            if (existing_conv.get('user_input') == user_input and 
                existing_conv.get('ai_response') == ai_response):
                print(f"⚠️ 检测到重复对话，跳过添加: {user_input[:30]}...")
                return
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.current_conversation.append({
            "timestamp": timestamp,
            "user_input": user_input,
            "ai_response": ai_response,
            "full_text": f"指挥官: {user_input}\n露尼西亚: {ai_response}"
        })
        
        print(f"✅ 添加对话到记忆系统: {user_input[:30]}... (当前共{len(self.current_conversation)}条)")
        
        # 🚀 修复：保存回调函数，在对话真正保存到识底深湖后调用
        if mark_saved_callback:
            self.mark_saved_callback = mark_saved_callback

    def should_summarize(self):
        """判断是否应该总结"""
        # 每3条对话总结一次，或者当前对话超过5条
        return len(self.current_conversation) >= 3

    def summarize_and_save_topic(self, ai_client=None, force_save=False):
        """总结并保存主题"""
        if not self.current_conversation:
            return None
        
        # 如果不是强制保存，检查是否满足保存条件
        if not force_save and not self.should_summarize():
            return None
            
        try:
            # 构建对话文本
            conversation_text = "\n".join([
                conv["full_text"] for conv in self.current_conversation
            ])
            
            # 使用AI总结主题
            topic = self._ai_summarize_topic(conversation_text)
            
            # 保存到记忆索引
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
            entry = {
                "topic": topic,
                "timestamp": timestamp,
                "date": date_str,
                "conversation_count": len(self.current_conversation),
                "keywords": self._extract_keywords(conversation_text),
                "conversation_details": self._extract_conversation_details(),
                "is_important": False  # 重点记忆标签
            }
            
            self.memory_index["topics"].append(entry)
            self.save_memory()
            
            # 🚀 修复：在成功保存到识底深湖后，标记所有已保存的对话为已保存
            # 获取AI代理的mark_saved_callback函数
            if hasattr(self, 'mark_saved_callback') and self.mark_saved_callback:
                for conv in self.current_conversation:
                    self.mark_saved_callback(conv['user_input'], conv['ai_response'])
            
            # 清空当前会话
            self.current_conversation = []
            
            return topic
            
        except Exception as e:
            print(f"总结主题失败: {str(e)}")
            return None

    def _ai_summarize_topic(self, conversation_text):
        """使用AI总结主题"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🔄 尝试AI主题总结 (第{attempt + 1}次)")
                # 使用专门的记忆总结AI代理
                topic = self.summary_agent.summarize_topic(conversation_text)
                if topic and len(topic.strip()) >= 2:
                    print(f"✅ AI主题总结成功: {topic}")
                    return topic
                else:
                    print(f"⚠️ AI主题总结返回空结果 (第{attempt + 1}次)")
                    if attempt < max_retries - 1:
                        print("🔄 等待2秒后重试...")
                        import time
                        time.sleep(2)
                        continue
                    else:
                        print("❌ AI主题总结最终失败")
                        return "AI总结失败"
            except Exception as e:
                print(f"⚠️ AI主题总结失败 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    print("🔄 等待2秒后重试...")
                    import time
                    time.sleep(2)
                    continue
                else:
                    print("❌ AI主题总结最终失败")
                    return "AI总结失败，请检查API配置"

    def _ai_summarize_content(self, conversation_text):
        """使用AI总结内容"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🔄 尝试AI上下文总结 (第{attempt + 1}次)")
                # 使用专门的记忆总结AI代理
                summary = self.summary_agent.summarize_context(conversation_text)
                if summary and len(summary.strip()) > 10:
                    print(f"✅ AI上下文总结成功: {summary[:50]}...")
                    return summary
                else:
                    print(f"⚠️ AI上下文总结返回空结果 (第{attempt + 1}次)")
                    if attempt < max_retries - 1:
                        print("🔄 等待2秒后重试...")
                        import time
                        time.sleep(2)
                        continue
                    else:
                        print("❌ AI上下文总结最终失败")
                        return "AI总结失败"
            except Exception as e:
                print(f"⚠️ AI上下文总结失败 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    print("🔄 等待2秒后重试...")
                    import time
                    time.sleep(2)
                    continue
                else:
                    print("❌ AI上下文总结最终失败")
                    return "AI总结失败，请检查API配置"

    def _simple_summarize_topic(self, text):
        """简单主题总结 - 分析整个对话流程"""
        topics = []
        
        # 分析各种主题类型
        if "Python" in text or "python" in text:
            topics.append("Python编程")
        if "C++" in text or "c++" in text:
            topics.append("C++编程")
        if "COBOL" in text or "cobol" in text:
            topics.append("COBOL编程")
        if "java" in text or "Java" in text:
            topics.append("Java编程")
        if "音乐" in text or "歌单" in text or "歌曲" in text:
            topics.append("音乐推荐")
        if "天气" in text:
            topics.append("天气查询")
        if "文件" in text and ("创建" in text or "保存" in text):
            topics.append("文件操作")
        if "文件夹" in text or "目录" in text:
            topics.append("文件夹创建")
        if "计算器" in text:
            topics.append("计算器程序")
        if "俄罗斯方块" in text or "tetris" in text:
            topics.append("俄罗斯方块游戏")
        if "贪吃蛇" in text or "snake" in text:
            topics.append("贪吃蛇游戏")
        if "井字棋" in text or "tic-tac-toe" in text:
            topics.append("井字棋游戏")
        if "爬虫" in text or "crawler" in text:
            topics.append("网络爬虫")
        if "数据分析" in text or "data" in text:
            topics.append("数据分析")
        if "Hello World" in text or "hello" in text:
            topics.append("Hello World程序")
        if "设置" in text:
            topics.append("系统设置")
        if "记忆" in text or "识底深湖" in text:
            topics.append("记忆系统")
        if "MCP" in text or "工具" in text:
            topics.append("MCP工具")
        if "搜索" in text:
            topics.append("网络搜索")
        if "时间" in text:
            topics.append("时间查询")
        # 自我介绍相关（优先识别）
        if "指挥官，您好！我是露尼西亚" in text or "威廉的姐姐" in text:
            return "露尼西亚自我介绍"
        
        if "问候" in text or "你好" in text:
            topics.append("问候")
        if "介绍" in text and any(country in text for country in ["德国", "法国", "英国", "美国", "日本", "韩国", "俄罗斯", "中国", "塔林", "贝尔格莱德"]):
            topics.append("国家介绍")
        if "游记" in text or "旅游" in text or "行程" in text:
            topics.append("游记写作")
        
        # 根据发现的主题数量生成综合主题
        if len(topics) >= 3:
            # 多主题对话，选择最重要的几个，避免过于宽泛
            if "音乐推荐" in topics and "天气查询" in topics:
                return f"{topics[0]}与{topics[1]}等多项讨论"
            else:
                # 对于其他多主题，尝试生成更具体的主题
                main_topics = topics[:3]  # 取前3个主题
                return f"{'、'.join(main_topics)}等多项讨论"
        elif len(topics) == 2:
            # 双主题对话
            return f"{topics[0]}与{topics[1]}讨论"
        elif len(topics) == 1:
            # 单主题对话
            return topics[0]
        else:
            # 没有明确主题，尝试提取关键词
            keywords = self._extract_keywords(text)
            if keywords:
                return f"关于{keywords[0]}的对话"
            else:
                return "日常对话"
                
    def _simple_summarize_content(self, text):
        """简单内容总结"""
        summary_parts = []
        
        # 提取具体信息
        if "你好" in text or "问候" in text:
            summary_parts.append("用户进行了问候")
        
        if "天气" in text:
            # 尝试提取城市信息和具体天气数据
            cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都", "重庆", "西安"]
            city_found = None
            for city in cities:
                if city in text:
                    city_found = city
                    break
            
            # 尝试提取具体的天气信息
            weather_details = []
            if "雷阵雨" in text:
                weather_details.append("雷阵雨")
            if "晴天" in text or "晴" in text:
                weather_details.append("晴天")
            if "多云" in text:
                weather_details.append("多云")
            if "阴" in text:
                weather_details.append("阴天")
            if "雨" in text and "雷阵雨" not in text:
                weather_details.append("雨天")
            
            # 尝试提取温度信息
            import re
            temp_matches = re.findall(r'(\d+)°C', text)
            if temp_matches:
                if len(temp_matches) == 1:
                    weather_details.append(f"{temp_matches[0]}°C")
                else:
                    weather_details.append(f"{temp_matches[0]}-{temp_matches[-1]}°C")
            
            # 尝试提取风力信息
            wind_matches = re.findall(r'([东南西北]风\d+-\d+级)', text)
            if wind_matches:
                weather_details.append(wind_matches[0])
            
            # 构建天气总结
            if city_found and weather_details:
                summary_parts.append(f"查询了{city_found}天气：{', '.join(weather_details[:3])}")
            elif city_found:
                summary_parts.append(f"查询了{city_found}的天气信息")
            elif weather_details:
                summary_parts.append(f"查询了天气信息：{', '.join(weather_details[:3])}")
            else:
                summary_parts.append("查询了天气信息")
        
        if "时间" in text:
            summary_parts.append("查询了当前时间")
        
        if "搜索" in text:
            # 尝试提取搜索关键词
            import re
            search_match = re.search(r'搜索\s*([^，。\s]+)', text)
            if search_match:
                keyword = search_match.group(1)
                summary_parts.append(f"搜索了{keyword}相关信息")
            else:
                summary_parts.append("进行了网络搜索")
        
        # 检查是否是音乐推荐相关的对话（需要更精确的匹配）
        if ("推荐" in text and ("音乐" in text or "歌单" in text or "歌曲" in text)) or \
           ("音乐" in text and ("推荐" in text or "几首" in text)):
            # 尝试提取具体的歌曲信息
            import re
            # 匹配歌曲名字（用《》包围的）
            song_matches = re.findall(r'《([^》]+)》', text)
            if song_matches:
                songs = song_matches[:3]  # 最多取前3首
                if len(songs) == 1:
                    summary_parts.append(f"推荐了音乐《{songs[0]}》")
                elif len(songs) == 2:
                    summary_parts.append(f"推荐了音乐《{songs[0]}》和《{songs[1]}》")
                else:
                    summary_parts.append(f"推荐了音乐《{songs[0]}》等{len(song_matches)}首歌曲")
            else:
                # 如果没有找到《》格式，尝试提取其他格式的歌曲名
                artist_matches = re.findall(r'-\s*([^（\n]+)', text)
                if artist_matches:
                    artists = artist_matches[:2]  # 最多取前2个艺术家
                    summary_parts.append(f"推荐了{artists[0]}等艺术家的音乐")
                else:
                    summary_parts.append("推荐了音乐歌单")
        
        if "Python" in text or "python" in text:
            # 尝试提取具体的Python项目信息
            if "计算器" in text:
                summary_parts.append("讨论了Python计算器程序")
            elif "俄罗斯方块" in text or "tetris" in text:
                summary_parts.append("讨论了Python俄罗斯方块游戏")
            elif "贪吃蛇" in text or "snake" in text:
                summary_parts.append("讨论了Python贪吃蛇游戏")
            elif "井字棋" in text or "tic-tac-toe" in text:
                summary_parts.append("讨论了Python井字棋游戏")
            elif "爬虫" in text or "crawler" in text:
                summary_parts.append("讨论了Python网络爬虫")
            elif "数据分析" in text or "data" in text:
                summary_parts.append("讨论了Python数据分析")
            elif "Hello World" in text or "hello" in text:
                summary_parts.append("讨论了Python Hello World程序")
            else:
                summary_parts.append("讨论了Python编程相关内容")
        
        if "C++" in text or "c++" in text:
            # 尝试提取具体的C++项目信息
            if "计算器" in text:
                summary_parts.append("讨论了C++计算器程序")
            elif "俄罗斯方块" in text or "tetris" in text:
                summary_parts.append("讨论了C++俄罗斯方块游戏")
            elif "贪吃蛇" in text or "snake" in text:
                summary_parts.append("讨论了C++贪吃蛇游戏")
            elif "井字棋" in text or "tic-tac-toe" in text:
                summary_parts.append("讨论了C++井字棋游戏")
            else:
                summary_parts.append("讨论了C++编程相关内容")
        
        if "Java" in text or "java" in text:
            # 尝试提取具体的Java项目信息
            if "计算器" in text:
                summary_parts.append("讨论了Java计算器程序")
            elif "俄罗斯方块" in text or "tetris" in text:
                summary_parts.append("讨论了Java俄罗斯方块游戏")
            elif "贪吃蛇" in text or "snake" in text:
                summary_parts.append("讨论了Java贪吃蛇游戏")
            elif "井字棋" in text or "tic-tac-toe" in text:
                summary_parts.append("讨论了Java井字棋游戏")
            else:
                summary_parts.append("讨论了Java编程相关内容")
        
        if "COBOL" in text or "cobol" in text:
            summary_parts.append("讨论了COBOL编程相关内容")
        
        if "文件" in text and ("创建" in text or "保存" in text):
            # 尝试提取具体的文件信息
            import re
            # 提取文件类型
            if ".py" in text or "Python" in text:
                summary_parts.append("创建或保存了Python文件")
            elif ".cpp" in text or "C++" in text:
                summary_parts.append("创建或保存了C++文件")
            elif ".java" in text or "Java" in text:
                summary_parts.append("创建或保存了Java文件")
            elif ".txt" in text:
                summary_parts.append("创建或保存了文本文件")
            else:
                summary_parts.append("创建或保存了文件")
        
        if "文件夹" in text or "目录" in text:
            summary_parts.append("创建了文件夹")
        
        # 游戏和项目相关的总结已经在编程部分处理了，这里不再重复
        
        # 检查语言介绍相关的对话
        if "希伯来语" in text or "俄语" in text or "英语" in text or "日语" in text or "法语" in text or "德语" in text or "西班牙语" in text:
            if "介绍" in text and "自己" in text:
                language = "希伯来语" if "希伯来语" in text else \
                          "俄语" if "俄语" in text else \
                          "英语" if "英语" in text else \
                          "日语" if "日语" in text else \
                          "法语" if "法语" in text else \
                          "德语" if "德语" in text else \
                          "西班牙语" if "西班牙语" in text else "外语"
                summary_parts.append(f"用{language}进行了自我介绍")
            else:
                summary_parts.append("进行了语言相关的对话")
        
        if "设置" in text:
            summary_parts.append("进行了系统设置相关操作")
        
        if "记忆" in text or "识底深湖" in text:
            summary_parts.append("查看了记忆系统")
        
        if "MCP" in text or "工具" in text:
            summary_parts.append("使用了MCP工具")
        
        # 如果没有找到具体内容，返回通用描述
        if not summary_parts:
            summary_parts.append("进行了日常对话交流")
        
        # 组合总结内容，按时间顺序排列
        if len(summary_parts) > 1:
            # 如果有多个操作，用"然后"连接，表示时间顺序
            summary = "，然后".join(summary_parts)
        else:
            summary = "，".join(summary_parts)
        
        # 控制长度在40-60字之间
        if len(summary) > 60:
            summary = summary[:57] + "..."
        elif len(summary) < 25:
            summary += "，包含具体的对话内容和操作步骤"
        
        return summary

    def _extract_keywords(self, text):
        """提取关键词"""
        keywords = []
        common_words = [
            # 基础功能
            '天气', '时间', '搜索', '打开', '计算', '距离', '系统', '文件', '笔记', '穿衣', '出门', '建议',
            # 旅游景点
            '历史', '景点', '旅游', '参观', '游览', '建筑', '教堂', '大教堂', '广场', '公园', '博物馆', '遗址', '古迹',
            '故宫', '天安门', '红场', '莫斯科', '柏林', '勃兰登堡门', '法兰克福', '铁桥', '桥',
            # 编程相关
            'Python', 'python', 'C++', 'c++', 'COBOL', 'cobol', '编程', '代码', '程序', '开发',
            # 文件操作
            '创建', '保存', '文件夹', '目录', '歌单', '音乐', '歌曲', '推荐',
            # 游戏相关
            '计算器', '俄罗斯方块', 'tetris', '贪吃蛇', 'snake', '井字棋', 'tic-tac-toe', '游戏',
            # 技术相关
            '爬虫', 'crawler', '数据分析', 'data', 'Hello World', 'hello',
            # 系统功能
            '设置', '记忆', '识底深湖', 'MCP', '工具', 'API', '配置'
        ]
        
        for word in common_words:
            if word in text:
                keywords.append(word)
        
        return keywords

    def _extract_conversation_details(self):
        """提取对话详情，生成精简的对话记录"""
        if not self.current_conversation:
            return ""
        
        # 使用AI智能总结整个对话，而不是逐条关键词识别
        conversation_text = ""
        for conv in self.current_conversation:
            user_input = conv.get("user_input", "")
            ai_response = conv.get("ai_response", "")
            
            if user_input == "系统":
                conversation_text += f"露尼西亚: {ai_response}\n"
            else:
                conversation_text += f"指挥官: {user_input}\n露尼西亚: {ai_response}\n"
        
        # 强制使用AI总结，不启用后备方案
        try:
            ai_result = self._ai_summarize_conversation_details(conversation_text)
            if ai_result and len(ai_result.strip()) > 10:  # 确保AI返回了有效结果
                return ai_result
            else:
                print("⚠️ AI总结返回空结果，尝试重新生成")
                # 再次尝试AI总结
                ai_result = self._ai_summarize_conversation_details(conversation_text)
                return ai_result if ai_result and len(ai_result.strip()) > 10 else "AI总结失败"
        except Exception as e:
            print(f"⚠️ AI总结失败: {str(e)}")
            return "AI总结失败，请检查API配置"
    
    def _ai_summarize_conversation_details(self, conversation_text):
        """使用AI总结对话详情"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🔄 尝试AI对话记录总结 (第{attempt + 1}次)")
                # 使用专门的记忆总结AI代理
                details = self.summary_agent.summarize_conversation_details(conversation_text)
                if details and len(details.strip()) > 10:
                    print(f"✅ AI对话记录总结成功: {details[:50]}...")
                    return details
                else:
                    print(f"⚠️ AI对话记录总结返回空结果 (第{attempt + 1}次)")
                    if attempt < max_retries - 1:
                        print("🔄 等待2秒后重试...")
                        import time
                        time.sleep(2)
                        continue
                    else:
                        print("❌ AI对话记录总结最终失败")
                        return "AI总结失败"
            except Exception as e:
                print(f"⚠️ AI对话记录总结失败 (第{attempt + 1}次): {str(e)}")
                if attempt < max_retries - 1:
                    print("🔄 等待2秒后重试...")
                    import time
                    time.sleep(2)
                    continue
                else:
                    print("❌ AI对话记录总结最终失败")
                    return "AI总结失败，请检查API配置"
    
    def _fallback_conversation_details(self):
        """后备方案：使用原来的关键词识别方法"""
        if not self.current_conversation:
            return ""
        
        details = []
        for conv in self.current_conversation:
            user_input = conv.get("user_input", "")
            ai_response = conv.get("ai_response", "")
            
            # 处理系统消息（如自我介绍）
            if user_input == "系统":
                details.append(f"露尼西亚: {ai_response}")
                continue
            
            # 精简用户输入
            if len(user_input) > 20:
                user_input = user_input[:17] + "..."
            
            # 智能精简AI回应，保留具体信息
            ai_response = self._smart_summarize_ai_response(ai_response)
            
            details.append(f"指挥官: {user_input}")
            details.append(f"露尼西亚: {ai_response}")
        
        return "\n".join(details)
    
    def _smart_summarize_ai_response(self, ai_response):
        """智能精简AI回应，保留具体信息"""
        if len(ai_response) <= 50:
            return ai_response
        
        # 自我介绍相关（优先于音乐推荐）
        if "指挥官，您好！我是露尼西亚" in ai_response or "威廉的姐姐" in ai_response:
            return "进行了自我介绍，介绍了身份和能力"
        
        # 音乐推荐相关
        if "推荐" in ai_response and ("音乐" in ai_response or "歌单" in ai_response or "歌曲" in ai_response):
            # 提取具体的歌曲信息
            import re
            song_matches = re.findall(r'《([^》]+)》', ai_response)
            if song_matches:
                # 完整罗列所有歌曲，但控制在200字以内
                if len(song_matches) <= 5:  # 5首以内完整罗列
                    songs_text = "、".join([f"《{song}》" for song in song_matches])
                    return f"推荐了音乐{songs_text}"
                else:  # 超过5首，前5首+总数
                    songs_text = "、".join([f"《{song}》" for song in song_matches[:5]])
                    return f"推荐了音乐{songs_text}等{len(song_matches)}首歌曲"
            else:
                # 尝试提取艺术家信息
                artist_matches = re.findall(r'-\s*([^（\n]+)', ai_response)
                if artist_matches:
                    artists = artist_matches[:3]  # 最多3个艺术家
                    artists_text = "、".join(artists)
                    return f"推荐了{artists_text}等艺术家的音乐"
                else:
                    return "推荐了音乐歌单"
        
        # 国家介绍和科普内容相关（优先于天气信息）
        elif any(keyword in ai_response for keyword in ["德国", "法国", "英国", "美国", "日本", "韩国", "俄罗斯", "中国", "介绍", "位于", "首都", "人口", "面积", "经济", "文化", "历史"]):
            # 提取国家或地区名称
            import re
            country_match = re.search(r'([德国法国英国美国日本韩国俄罗斯中国印度巴西澳大利亚加拿大意大利西班牙荷兰瑞士瑞典挪威丹麦芬兰波兰捷克匈牙利罗马尼亚保加利亚塞尔维亚克罗地亚斯洛文尼亚奥地利比利时卢森堡葡萄牙希腊土耳其以色列埃及南非尼日利亚肯尼亚埃塞俄比亚摩洛哥阿尔及利亚突尼斯利比亚苏丹南苏丹中非共和国刚果民主共和国刚果共和国加蓬赤道几内亚圣多美和普林西比喀麦隆乍得尼日尔马里布基纳法索贝宁多哥加纳科特迪瓦利比里亚塞拉利昂几内亚几内亚比绍塞内加尔冈比亚毛里塔尼亚摩洛哥阿尔及利亚突尼斯利比亚埃及苏丹南苏丹中非共和国刚果民主共和国刚果共和国加蓬赤道几内亚圣多美和普林西比喀麦隆乍得尼日尔马里布基纳法索贝宁多哥加纳科特迪瓦利比里亚塞拉利昂几内亚几内亚比绍塞内加尔冈比亚毛里塔尼亚])(国|共和国|联邦|王国|帝国|公国|大公国|酋长国|苏丹国|哈里发国|共和国|联邦共和国|民主共和国|人民共和国|社会主义共和国|伊斯兰共和国|阿拉伯共和国|联合共和国|联邦共和国|民主联邦共和国|社会主义联邦共和国|伊斯兰联邦共和国|阿拉伯联邦共和国|联合联邦共和国|联邦民主共和国|联邦社会主义共和国|联邦伊斯兰共和国|联邦阿拉伯共和国|联邦联合共和国|民主联邦社会主义共和国|民主联邦伊斯兰共和国|民主联邦阿拉伯共和国|民主联邦联合共和国|社会主义联邦民主共和国|社会主义联邦伊斯兰共和国|社会主义联邦阿拉伯共和国|社会主义联邦联合共和国|伊斯兰联邦民主共和国|伊斯兰联邦社会主义共和国|伊斯兰联邦阿拉伯共和国|伊斯兰联邦联合共和国|阿拉伯联邦民主共和国|阿拉伯联邦社会主义共和国|阿拉伯联邦伊斯兰共和国|阿拉伯联邦联合共和国|联合联邦民主共和国|联合联邦社会主义共和国|联合联邦伊斯兰共和国|联合联邦阿拉伯共和国|联合联邦联合共和国)?', ai_response)
            if country_match:
                country = country_match.group(1)
                # 提取关键信息，生成缩写句子
                summary_parts = []
                
                # 提取地理位置
                if "位于" in ai_response:
                    location_match = re.search(r'位于([^，。\s]+)', ai_response)
                    if location_match:
                        summary_parts.append(f"位于{location_match.group(1)}")
                
                # 提取首都
                if "首都" in ai_response:
                    capital_match = re.search(r'首都([^，。\s]+)', ai_response)
                    if capital_match:
                        summary_parts.append(f"首都{capital_match.group(1)}")
                
                # 提取人口
                if "人口" in ai_response:
                    population_match = re.search(r'人口([^，。\s]+)', ai_response)
                    if population_match:
                        summary_parts.append(f"人口{population_match.group(1)}")
                
                # 提取面积
                if "面积" in ai_response:
                    area_match = re.search(r'面积([^，。\s]+)', ai_response)
                    if area_match:
                        summary_parts.append(f"面积{area_match.group(1)}")
                
                # 构建总结
                if summary_parts:
                    return f"介绍了{country}：{''.join(summary_parts[:3])}"  # 最多3个关键信息
                else:
                    return f"介绍了{country}的基本信息"
            else:
                # 没有找到具体国家，但包含介绍相关内容
                if "介绍" in ai_response:
                    return "进行了知识介绍"
                else:
                    return "提供了科普信息"
        
        # 天气查询相关
        elif "天气" in ai_response:
            # 提取具体的天气信息
            import re
            weather_details = []
            
            # 提取城市信息
            city_match = re.search(r'([北京上海广州深圳成都重庆武汉西安南京杭州苏州天津青岛大连厦门宁波无锡长沙郑州济南福州合肥南昌南宁贵阳昆明太原石家庄哈尔滨长春沈阳呼和浩特银川西宁拉萨乌鲁木齐])(市|省)?', ai_response)
            if city_match:
                city = city_match.group(1)
                weather_details.append(city)
            
            # 提取温度信息
            temp_matches = re.findall(r'(\d+)°C', ai_response)
            if temp_matches:
                if len(temp_matches) == 1:
                    weather_details.append(f"{temp_matches[0]}°C")
                else:
                    weather_details.append(f"{temp_matches[0]}-{temp_matches[-1]}°C")
            
            # 提取天气状况
            if "雷阵雨" in ai_response:
                weather_details.append("雷阵雨")
            elif "多云" in ai_response:
                weather_details.append("多云")
            elif "晴天" in ai_response:
                weather_details.append("晴天")
            elif "阴天" in ai_response:
                weather_details.append("阴天")
            elif "小雨" in ai_response:
                weather_details.append("小雨")
            
            # 提取风力信息
            wind_matches = re.findall(r'([东南西北]风\d+-\d+级)', ai_response)
            if wind_matches:
                weather_details.append(wind_matches[0])
            
            # 构建天气总结
            if weather_details:
                return f"提供了{''.join(weather_details)}的天气信息"
            else:
                return "提供了天气信息"
        
        # 文件操作相关
        elif "文件" in ai_response and ("成功" in ai_response or "写入成功" in ai_response):
            # 提取文件路径和类型
            import re
            file_match = re.search(r'文件\s*([^写入成功]+)', ai_response)
            if file_match:
                file_path = file_match.group(1).strip()
                return f"文件{file_path}创建成功"
            else:
                return "文件创建成功"
        
        # 时间查询相关
        elif "时间" in ai_response:
            # 提取具体时间信息
            import re
            time_match = re.search(r'(\d{1,2}:\d{2})', ai_response)
            if time_match:
                time_str = time_match.group(1)
                return f"提供了{time_str}的时间信息"
            else:
                return "提供了时间信息"
        
        # 编程相关
        elif any(keyword in ai_response for keyword in ["Python", "Java", "C++", "JavaScript", "代码", "程序"]):
            # 提取编程语言和项目类型
            import re
            if "Python" in ai_response:
                if "计算器" in ai_response:
                    return "提供了Python计算器代码"
                elif "俄罗斯方块" in ai_response or "tetris" in ai_response:
                    return "提供了Python俄罗斯方块游戏代码"
                elif "贪吃蛇" in ai_response or "snake" in ai_response:
                    return "提供了Python贪吃蛇游戏代码"
                else:
                    return "提供了Python编程代码"
            elif "Java" in ai_response:
                if "计算器" in ai_response:
                    return "提供了Java计算器代码"
                elif "游戏" in ai_response:
                    return "提供了Java游戏代码"
                else:
                    return "提供了Java编程代码"
            elif "C++" in ai_response:
                if "游戏" in ai_response:
                    return "提供了C++游戏代码"
                else:
                    return "提供了C++编程代码"
            else:
                return "提供了编程代码"
        
        # 语言介绍相关
        elif any(lang in ai_response for lang in ["希伯来语", "俄语", "英语", "日语", "法语", "德语", "西班牙语"]):
            for lang in ["希伯来语", "俄语", "英语", "日语", "法语", "德语", "西班牙语"]:
                if lang in ai_response:
                    return f"用{lang}进行了自我介绍"
            return "进行了语言介绍"
        
        # 其他情况，保留关键信息
        else:
            # 尝试提取关键信息，避免过长
            if len(ai_response) > 100:
                # 寻找句号或逗号作为分割点
                sentences = ai_response.split('。')
                if len(sentences) > 1:
                    first_sentence = sentences[0].strip()
                    if len(first_sentence) <= 50:
                        return first_sentence
                    else:
                        return first_sentence[:47] + "..."
                else:
                    return ai_response[:47] + "..."
            else:
                return ai_response

    def search_relevant_memories(self, user_input, current_context=""):
        """搜索相关记忆"""
        try:
            relevant_memories = []
            user_keywords = self._extract_keywords(user_input)
            
            for entry in self.memory_index["topics"]:
                relevance_score = self._calculate_relevance(entry, user_keywords, current_context)
                if relevance_score > 0.3:  # 相关性阈值
                    entry["relevance_score"] = relevance_score
                    relevant_memories.append(entry)
            
            # 按相关性排序，然后按时间排序（最新的优先）
            relevant_memories.sort(key=lambda x: (x["relevance_score"], x.get("timestamp", "")), reverse=True)
            return relevant_memories[:3]  # 返回最相关的3个记忆
            
        except Exception as e:
            print(f"搜索记忆失败: {str(e)}")
            return []

    def _calculate_relevance(self, memory_entry, user_keywords, current_context):
        """计算相关性分数"""
        score = 0.0
        
        # 关键词匹配
        memory_keywords = memory_entry.get("keywords", [])
        for keyword in user_keywords:
            if keyword in memory_keywords:
                score += 0.4
        
        # 主题匹配
        memory_topic = memory_entry.get("topic", "")
        for keyword in user_keywords:
            if keyword in memory_topic:
                score += 0.3
        
        # 时间相关性（最近7天的记忆权重更高）
        try:
            memory_date = datetime.datetime.strptime(memory_entry.get("date", ""), "%Y-%m-%d")
            current_date = datetime.datetime.now()
            days_diff = (current_date - memory_date).days
            if days_diff <= 7:
                score += 0.2
            elif days_diff <= 30:
                score += 0.1
        except:
            pass
        
        return min(score, 1.0)

    def should_recall_memory(self, user_input):
        """判断是否需要回忆"""
        # 关键词触发 - 更精确的关键词
        recall_keywords = ['记得', '说过', '讨论过', '回忆', '继续', '接着', '历史', '以前', '曾经', '之前', '上个']
        
        # 如果用户询问的是"上一个"相关的问题，优先使用本次会话记忆，不触发历史记忆
        # 但如果是"之前"相关的问题，应该触发历史记忆
        if any(word in user_input for word in ['上一个', '刚才']):
            return False
            
        return any(keyword in user_input for keyword in recall_keywords)

    def generate_memory_context(self, relevant_memories, user_input):
        """生成记忆上下文"""
        if not relevant_memories:
                return ""
            
        try:
            context_parts = []
            
            for memory in relevant_memories:
                topic = memory.get("topic", "")
                timestamp = memory.get("timestamp", "")
                date = memory.get("date", "")
                
                context_part = f"【{date} {timestamp}】{topic}"
                context_parts.append(context_part)
            
            if context_parts:
                return "\n".join(context_parts)
            
            return ""
            
        except Exception as e:
            print(f"生成记忆上下文失败: {str(e)}")
            return ""

    def get_recent_memories(self, limit=100):
        """获取最近的历史记忆"""
        try:
            topics = self.memory_index.get("topics", [])
            # 按日期和时间倒序排列，获取最近的记忆
            sorted_topics = sorted(topics, key=lambda x: (x.get("date", ""), x.get("timestamp", "")), reverse=True)
            return sorted_topics[:limit]
        except Exception as e:
            print(f"获取最近记忆失败: {str(e)}")
            return []

    def get_first_memory(self):
        """获取第一条记忆"""
        try:
            topics = self.memory_index.get("topics", [])
            if not topics:
                return None
            
            # 按日期和时间正序排列，获取最早的记忆
            # 确保日期格式正确，处理可能的空值
            def sort_key(topic):
                date = topic.get("date", "")
                timestamp = topic.get("timestamp", "")
                # 如果日期为空，使用一个很大的日期确保排在最后
                if not date:
                    return ("9999-12-31", timestamp)
                return (date, timestamp)
            
            sorted_topics = sorted(topics, key=sort_key)
            first_memory = sorted_topics[0]
            
            # 添加调试信息
            print(f"🔍 找到第一条记忆: {first_memory.get('date', '未知')} {first_memory.get('timestamp', '未知')} - {first_memory.get('topic', '未知主题')}")
            
            return first_memory
        except Exception as e:
            print(f"获取第一条记忆失败: {str(e)}")
            return None

    def get_memory_stats(self):
        """获取记忆统计信息"""
        try:
            topics = self.memory_index.get("topics", [])
            total_topics = len(topics)
            important_topics = len([topic for topic in topics if topic.get("is_important", False)])
            total_log_files = len([f for f in os.listdir(self.chat_logs_dir) if f.endswith('.json')]) if os.path.exists(self.chat_logs_dir) else 0
            
            stats = {
                "total_topics": total_topics,
                "important_topics": important_topics,
                "total_log_files": total_log_files,
                "memory_file_size": os.path.getsize(self.memory_file) if os.path.exists(self.memory_file) else 0,
                "current_conversation_count": len(self.current_conversation)
            }
            
            return stats
        except Exception as e:
            print(f"获取记忆统计失败: {str(e)}")
            return {"total_topics": 0, "important_topics": 0, "total_log_files": 0, "memory_file_size": 0, "current_conversation_count": 0}

    def mark_as_important(self, topic_index):
        """标记为重点记忆"""
        try:
            topics = self.memory_index.get("topics", [])
            if 0 <= topic_index < len(topics):
                topics[topic_index]["is_important"] = True
                self.save_memory()
                return True
            return False
        except Exception as e:
            print(f"标记重点记忆失败: {str(e)}")
            return False

    def unmark_as_important(self, topic_index):
        """取消重点记忆标记"""
        try:
            topics = self.memory_index.get("topics", [])
            if 0 <= topic_index < len(topics):
                topics[topic_index]["is_important"] = False
                self.save_memory()
                return True
            return False
        except Exception as e:
            print(f"取消重点记忆标记失败: {str(e)}")
            return False

    def get_important_memories(self):
        """获取所有重点记忆"""
        try:
            topics = self.memory_index.get("topics", [])
            important_memories = [topic for topic in topics if topic.get("is_important", False)]
            return important_memories
        except Exception as e:
            print(f"获取重点记忆失败: {str(e)}")
            return []

    def mark_first_memory_as_important(self):
        """将第一条记忆标记为重点记忆"""
        try:
            topics = self.memory_index.get("topics", [])
            if topics:
                topics[0]["is_important"] = True
                self.save_memory()
                return True
            return False
        except Exception as e:
            print(f"标记第一条记忆为重点记忆失败: {str(e)}")
            return False

    def ensure_first_memory_important(self):
        """确保第一条记忆是重点记忆"""
        try:
            topics = self.memory_index.get("topics", [])
            if topics and not topics[0].get("is_important", False):
                topics[0]["is_important"] = True
                self.save_memory()
                return True
            return False
        except Exception as e:
            print(f"确保第一条记忆为重点记忆失败: {str(e)}")
            return False
