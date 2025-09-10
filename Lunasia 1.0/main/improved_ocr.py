#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的OCR处理脚本
专门处理复杂背景下的文字识别
"""

import os
import sys
import json
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def improved_preprocess_image_for_ocr(img):
    """改进的图片预处理，专门处理复杂背景"""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import numpy as np
        
        # 转换为RGB模式
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 转换为灰度图
        img_gray = img.convert('L')
        
        # 多种预处理方法
        processed_images = []
        
        # 方法1：基础增强
        enhancer = ImageEnhance.Contrast(img_gray)
        img_enhanced = enhancer.enhance(2.0)
        sharpness_enhancer = ImageEnhance.Sharpness(img_enhanced)
        img_sharp = sharpness_enhancer.enhance(1.5)
        processed_images.append(("基础增强", img_sharp))
        
        # 方法2：高对比度处理
        enhancer = ImageEnhance.Contrast(img_gray)
        img_high_contrast = enhancer.enhance(3.0)
        brightness_enhancer = ImageEnhance.Brightness(img_high_contrast)
        img_bright = brightness_enhancer.enhance(1.2)
        processed_images.append(("高对比度", img_bright))
        
        # 方法3：边缘增强
        edge_enhancer = ImageEnhance.Sharpness(img_gray)
        img_edge = edge_enhancer.enhance(2.5)
        contrast_enhancer = ImageEnhance.Contrast(img_edge)
        img_edge_contrast = contrast_enhancer.enhance(2.5)
        processed_images.append(("边缘增强", img_edge_contrast))
        
        # 方法4：高斯模糊去噪
        img_blur = img_gray.filter(ImageFilter.GaussianBlur(radius=0.5))
        enhancer = ImageEnhance.Contrast(img_blur)
        img_blur_contrast = enhancer.enhance(2.5)
        processed_images.append(("去噪增强", img_blur_contrast))
        
        # 方法5：自适应阈值处理（模拟）
        try:
            img_array = np.array(img_gray)
            
            # 计算局部平均值
            from scipy import ndimage
            local_mean = ndimage.uniform_filter(img_array, size=15)
            
            # 自适应阈值
            threshold = local_mean - 10
            binary = np.where(img_array > threshold, 255, 0)
            
            # 转回PIL图像
            img_adaptive = Image.fromarray(binary.astype(np.uint8))
            processed_images.append(("自适应阈值", img_adaptive))
        except ImportError:
            # 如果没有scipy，跳过这个方法
            pass
        
        # 方法6：形态学处理（模拟）
        try:
            img_array = np.array(img_gray)
            
            # 简单的形态学操作
            # 膨胀操作
            kernel = np.ones((2,2), np.uint8)
            dilated = ndimage.binary_dilation(img_array < 128, structure=kernel)
            eroded = ndimage.binary_erosion(dilated, structure=kernel)
            
            # 转回PIL图像
            img_morph = Image.fromarray((~eroded * 255).astype(np.uint8))
            processed_images.append(("形态学处理", img_morph))
        except ImportError:
            # 如果没有scipy，跳过这个方法
            pass
        
        return processed_images
        
    except Exception as e:
        print(f"预处理失败: {e}")
        # 如果预处理失败，返回原图
        return [("原图", img)]

def improved_perform_ocr_on_image(img):
    """改进的OCR文字识别，使用多种预处理方法"""
    try:
        import pytesseract
        from PIL import Image
        
        # 设置Tesseract路径
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # 检查可用语言
        try:
            langs = pytesseract.get_languages()
            has_chinese = 'chi_sim' in langs
            has_english = 'eng' in langs
        except:
            has_chinese = False
            has_english = True
        
        # 预处理图片
        processed_images = improved_preprocess_image_for_ocr(img)
        
        # 尝试多种OCR配置
        all_ocr_results = []
        
        for method_name, processed_img in processed_images:
            print(f"尝试 {method_name} 预处理方法...")
            
            # 配置1：默认配置
            if has_chinese and has_english:
                try:
                    text_default = pytesseract.image_to_string(processed_img, lang='chi_sim+eng', config='--psm 6')
                    if text_default.strip():
                        all_ocr_results.append({
                            "method": method_name,
                            "config": "中英文混合",
                            "text": text_default.strip(),
                            "confidence": "标准"
                        })
                except Exception as e:
                    print(f"中英文混合识别失败: {e}")
            
            # 配置2：只识别中文
            if has_chinese:
                try:
                    text_chinese = pytesseract.image_to_string(processed_img, lang='chi_sim', config='--psm 6')
                    if text_chinese.strip():
                        all_ocr_results.append({
                            "method": method_name,
                            "config": "中文识别",
                            "text": text_chinese.strip(),
                            "confidence": "标准"
                        })
                except Exception as e:
                    print(f"中文识别失败: {e}")
            
            # 配置3：只识别英文
            if has_english:
                try:
                    text_english = pytesseract.image_to_string(processed_img, lang='eng', config='--psm 6')
                    if text_english.strip():
                        all_ocr_results.append({
                            "method": method_name,
                            "config": "英文识别",
                            "text": text_english.strip(),
                            "confidence": "标准"
                        })
                except Exception as e:
                    print(f"英文识别失败: {e}")
            
            # 配置4：数字识别
            try:
                text_digits = pytesseract.image_to_string(processed_img, lang='eng', config='--psm 6 -c tessedit_char_whitelist=0123456789')
                if text_digits.strip():
                    all_ocr_results.append({
                        "method": method_name,
                        "config": "数字识别",
                        "text": text_digits.strip(),
                        "confidence": "标准"
                    })
            except Exception as e:
                print(f"数字识别失败: {e}")
            
            # 配置5：单行文本识别
            try:
                text_single = pytesseract.image_to_string(processed_img, lang='eng', config='--psm 7')
                if text_single.strip():
                    all_ocr_results.append({
                        "method": method_name,
                        "config": "单行文本",
                        "text": text_single.strip(),
                        "confidence": "标准"
                    })
            except Exception as e:
                print(f"单行文本识别失败: {e}")
        
        if all_ocr_results:
            # 选择最佳结果（通常是最长的文本）
            best_result = max(all_ocr_results, key=lambda x: len(x["text"]))
            
            return {
                "status": "success",
                "extracted_text": best_result["text"],
                "all_results": all_ocr_results,
                "text_length": len(best_result["text"]),
                "word_count": len(best_result["text"].split()),
                "has_text": True,
                "description": f"成功识别到{len(best_result['text'])}个字符的文字内容（使用{best_result['method']}方法）",
                "best_method": best_result["method"]
            }
        else:
            return {
                "status": "no_text",
                "extracted_text": "",
                "all_results": [],
                "text_length": 0,
                "word_count": 0,
                "has_text": False,
                "description": "未识别到任何文字内容"
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"OCR识别失败: {str(e)}",
            "extracted_text": "",
            "all_results": [],
            "text_length": 0,
            "word_count": 0,
            "has_text": False
        }

def test_improved_ocr():
    """测试改进的OCR功能"""
    try:
        # 检查Tesseract是否可用
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # 检查语言包
        langs = pytesseract.get_languages()
        print(f"可用语言包: {langs}")
        
        if 'chi_sim' in langs:
            print("✅ 中文简体语言包已安装")
        else:
            print("⚠️ 中文简体语言包未安装")
        
        if 'eng' in langs:
            print("✅ 英文语言包已安装")
        else:
            print("⚠️ 英文语言包未安装")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 改进的OCR功能测试")
    print("=" * 50)
    
    success = test_improved_ocr()
    
    if success:
        print("✅ 改进的OCR功能可用")
    else:
        print("❌ 改进的OCR功能不可用")

