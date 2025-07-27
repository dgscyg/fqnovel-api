#!/usr/bin/env python3
"""
FQNovel API - Python版本
小说内容解密工具

使用方法:
python main.py <item_id> [--install-id INSTALL_ID] [--server-device-id SERVER_DEVICE_ID] [--aid AID] [--version VERSION]
"""

import argparse
import requests
import sys
from api import batch_full_sync, register_key_sync
from models import FqVariable
from crypto_utils import chapter_decrypt
from file_utils import save_decrypted_content


def main():
    parser = argparse.ArgumentParser(description='FQNovel内容解密工具')
    parser.add_argument('item_id', help='章节ID')
    parser.add_argument('--install-id', default='', help='安装ID')
    parser.add_argument('--server-device-id', default='', help='服务器设备ID')
    parser.add_argument('--aid', default='', help='应用ID')
    parser.add_argument('--version', default='', help='版本代码')
    parser.add_argument('--output-dir', default='output', help='输出目录')
    parser.add_argument('--no-save', action='store_true', help='不保存文件到磁盘')
    
    args = parser.parse_args()
    
    # 检查必需的参数
    if not all([args.install_id, args.server_device_id, args.aid, args.version]):
        print("错误: 需要提供所有必需的参数")
        print("请使用 --help 查看使用方法")
        print("\n注意: 你需要从Android设备获取这些参数:")
        print("- install_id: 安装ID")
        print("- server_device_id: 服务器设备ID") 
        print("- aid: 应用ID")
        print("- version: 更新版本代码")
        return 1
    
    # 创建变量配置
    var = FqVariable(
        install_id=args.install_id,
        server_device_id=args.server_device_id,
        aid=args.aid,
        update_version_code=args.version
    )
    
    # 创建HTTP客户端
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36'
    })
    
    try:
        print(f"正在获取章节内容: {args.item_id}")
        
        # 获取章节内容
        batch_response = batch_full_sync(session, var, args.item_id, download=False)
        
        if batch_response.code != 0:
            print(f"获取章节内容失败: {batch_response.message}")
            return 1
        
        if not batch_response.data:
            print("未找到章节内容")
            return 1
        
        print(f"成功获取 {len(batch_response.data)} 个章节")
        
        # 获取解密密钥
        print("正在获取解密密钥...")
        register_response = register_key_sync(session, var)
        
        if register_response.code != 0:
            print(f"获取解密密钥失败: {register_response.message}")
            return 1
        
        # 获取实际密钥
        full_key = register_response.data.get_key()
        # 取前16字节作为实际密钥
        actual_key = full_key[:32]  # 前16字节的hex表示
        print(f"解密密钥: {actual_key}")
        
        # 解密内容
        for item_id, content_obj in batch_response.data.items():
            print(f"\n正在解密章节: {item_id}")
            print(f"章节标题: {content_obj.title}")
            
            # 解密章节内容
            save_files = not args.no_save
            decrypted_content = chapter_decrypt(
                content_obj.content, 
                actual_key, 
                output_dir=args.output_dir,
                save_files=save_files
            )
            
            if decrypted_content:
                print(f"解密成功! 内容长度: {len(decrypted_content)} 字符")
                
                # 如果没有保存文件，则打印部分内容
                if args.no_save:
                    preview = decrypted_content[:500] + "..." if len(decrypted_content) > 500 else decrypted_content
                    print("内容预览:")
                    print("-" * 50)
                    print(preview)
                    print("-" * 50)
            else:
                print("解密失败!")
                return 1
        
        print("\n解密完成!")
        return 0
        
    except requests.RequestException as e:
        print(f"网络请求错误: {e}")
        return 1
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())