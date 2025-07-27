"""
File utilities for saving decrypted content
"""
import os
import re
from datetime import datetime


def save_decrypted_content(content, output_dir="output"):
    """
    保存解密后的内容到指定目录
    :param content: 解密后的内容
    :param output_dir: 输出目录，默认为当前目录下的output文件夹
    """
    if not content:
        print("内容为空，无法保存")
        return None, None
    
    # 创建时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
    
    # 创建输出目录结构
    html_dir = os.path.join(output_dir, "html")
    txt_dir = os.path.join(output_dir, "txt")
    
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(txt_dir, exist_ok=True)
    
    # 文件名
    html_filename = f"{timestamp}.html"
    txt_filename = f"{timestamp}.txt"
    
    html_path = os.path.join(html_dir, html_filename)
    txt_path = os.path.join(txt_dir, txt_filename)
    
    try:
        # 保存HTML文件
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"HTML文件已保存: {html_path}")
        
        # 提取纯文本内容并保存TXT文件
        txt_content = extract_text_from_html(content)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        print(f"TXT文件已保存: {txt_path}")
        
        return html_path, txt_path
        
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return None, None


def extract_text_from_html(html_content):
    """
    从HTML内容中提取纯文本
    """
    try:
        # 简单的文本提取，移除HTML标签
        
        # 提取标题
        title_match = re.search(r'<blk[^>]*?e_order="0"[^>]*?>(.*?)</blk>', html_content, re.DOTALL)
        title = ""
        if title_match:
            title_text = title_match.group(1)
            # 移除HTML标签
            title_text = re.sub(r'<[^>]+>', '', title_text)
            title = title_text.strip()
        
        # 提取所有段落内容
        paragraphs = []
        blk_pattern = r'<blk[^>]*?e_order="(\d+)"[^>]*?>(.*?)</blk>'
        matches = re.findall(blk_pattern, html_content, re.DOTALL)
        
        for order, text in matches:
            # 移除HTML标签
            clean_text = re.sub(r'<[^>]+>', '', text)
            clean_text = clean_text.strip()
            if clean_text and order != "0":  # 跳过标题（e_order="0"）
                paragraphs.append(clean_text)
        
        # 组合文本
        result = ""
        if title:
            result += f"{title}\n\n"
        
        result += "\n\n".join(paragraphs)
        
        return result
        
    except Exception as e:
        print(f"提取文本时出错: {e}")
        # 如果提取失败，返回原始HTML
        return html_content