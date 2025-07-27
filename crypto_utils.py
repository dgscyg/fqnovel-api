"""
FQNovel API - Crypto utilities for encryption/decryption
"""
import base64
import gzip
import struct
import os
from datetime import datetime
from io import BytesIO
from Crypto.Cipher import AES


def bytes_to_hex_upper(barr):
    """Java等价：每个字节转两位hex，大写"""
    return ''.join(['{:02X}'.format(x) for x in barr])


def decrypt_registerkey(registerkey_response_key, aes_key):
    """解密注册密钥"""
    raw = base64.b64decode(registerkey_response_key)
    iv = raw[:16]
    cipher_text = raw[16:]
    # 关键修复：Rust用hex decode
    key_bytes = bytes.fromhex(aes_key)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(cipher_text)
    # 直接转hex
    key_hex = bytes_to_hex_upper(decrypted)
    print("解密后原始内容 hex:", key_hex)
    # 通常取前16字节或全部看业务
    print("前16字节 hex:", bytes_to_hex_upper(decrypted[:16]))
    print("后16字节 hex:", bytes_to_hex_upper(decrypted[16:32]))
    return key_hex


def find_gzip_end(data):
    """
    通过分析 Gzip 文件结构找到真正的结束位置
    """
    if len(data) < 18:  # 至少需要头部(10) + 尾部(8)
        return None
        
    # 检查 Gzip 魔术字节
    if data[:2] != b'\x1f\x8b':
        return None
    
    # 解析头部信息
    if len(data) < 10:
        return None
        
    flags = data[3]
    header_size = 10
    
    # 跳过可选字段
    if flags & 0x04:  # FEXTRA
        if len(data) < header_size + 2:
            return None
        extra_len = struct.unpack('<H', data[header_size:header_size+2])[0]
        header_size += 2 + extra_len
        
    if flags & 0x08:  # FNAME
        null_pos = data.find(b'\x00', header_size)
        if null_pos == -1:
            return None
        header_size = null_pos + 1
        
    if flags & 0x10:  # FCOMMENT
        null_pos = data.find(b'\x00', header_size)
        if null_pos == -1:
            return None
        header_size = null_pos + 1
        
    if flags & 0x02:  # FHCRC
        header_size += 2
    
    # 现在我们需要找到压缩数据的结束位置
    # 从后往前查找有效的 CRC32 + ISIZE 组合
    for end_pos in range(len(data) - 7, header_size + 7, -1):
        try:
            # 尝试解压这个长度的数据
            test_data = data[:end_pos]
            gzip.decompress(test_data)
            return end_pos
        except:
            continue
    
    return None


def chapter_decrypt(content, key, output_dir="output", save_files=True):
    """
    解密章节内容
    :param content: 加密的内容
    :param key: 解密密钥
    :param output_dir: 输出目录
    :param save_files: 是否保存文件
    """
    if not content:
        return content
    
    # Step 1: 解密
    enc_bytes = base64.b64decode(content)
    iv = enc_bytes[:16]
    enc_data = enc_bytes[16:]
    key_bytes = bytes.fromhex(key)
    
    print("key_bytes:", key_bytes.hex())
    print("iv:", iv.hex())
    print("encrypted data length:", len(enc_data))
    
    # AES CBC 解密，无填充
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(enc_data)
    
    print("decrypted data length:", len(decrypted))
    print("decrypted first 16 bytes:", decrypted[:16].hex())
    
    result_content = None
    
    # Step 2: 智能处理 Gzip 数据
    if len(decrypted) >= 2 and decrypted[:2] == b'\x1f\x8b':
        # 先尝试直接解压
        try:
            decompressed = gzip.decompress(decrypted)
            result_content = decompressed.decode("utf-8")
        except Exception as e:
            print(f"直接Gzip解压失败: {e}")
            
            # 使用智能方法找到真正的 Gzip 结束位置
            gzip_end = find_gzip_end(decrypted)
            if gzip_end:
                try:
                    truncated = decrypted[:gzip_end]
                    decompressed = gzip.decompress(truncated)
                    print(f"智能分析：去除 {len(decrypted) - gzip_end} 字节后解压成功")
                    result_content = decompressed.decode("utf-8")
                except Exception as e2:
                    print(f"智能分析解压失败: {e2}")
            
            # 如果智能方法失败，回退到简单遍历（限制范围）
            if not result_content:
                for trim_bytes in range(1, min(16, len(decrypted))):
                    try:
                        truncated = decrypted[:-trim_bytes]
                        decompressed = gzip.decompress(truncated)
                        print(f"回退方法：成功去除 {trim_bytes} 字节后解压")
                        result_content = decompressed.decode("utf-8")
                        break
                    except:
                        continue
                        
    else:
        # 不是 Gzip 格式，直接解码
        try:
            result_content = decrypted.decode("utf-8")
        except UnicodeDecodeError:
            # 去除可能的尾部垃圾字节
            for trim_bytes in range(1, min(16, len(decrypted))):
                try:
                    truncated = decrypted[:-trim_bytes]
                    result_content = truncated.decode("utf-8")
                    break
                except UnicodeDecodeError:
                    continue
    
    if not result_content:
        print("所有解压/解码尝试都失败")
        return None
    
    # Step 3: 保存文件（如果需要）
    if save_files:
        from .file_utils import save_decrypted_content
        html_path, txt_path = save_decrypted_content(result_content, output_dir)
        if html_path and txt_path:
            print(f"解密成功并已保存文件")
        else:
            print("解密成功但保存文件失败")
    
    return result_content


class FqCrypto:
    """FQNovel 加密解密工具类"""
    
    def __init__(self, key: str):
        """
        初始化加密工具
        :param key: 十六进制密钥字符串
        """
        self.key_bytes = bytes.fromhex(key)
        if len(self.key_bytes) != 16:
            raise ValueError(f"密钥长度必须是16字节，当前: {len(self.key_bytes)}")
    
    def encrypt(self, data: bytes, iv: bytes) -> bytes:
        """AES CBC 加密"""
        cipher = AES.new(self.key_bytes, AES.MODE_CBC, iv)
        return cipher.encrypt(data)
    
    def decrypt(self, content: str) -> bytes:
        """解密Base64编码的内容"""
        decoded_data = base64.b64decode(content)
        iv = decoded_data[:16]
        encrypted_data = decoded_data[16:]
        
        cipher = AES.new(self.key_bytes, AES.MODE_CBC, iv)
        return cipher.decrypt(encrypted_data)
    
    def new_register_key_content(self, server_device_id: str, str_val: str = "0") -> str:
        """生成注册密钥内容"""
        import random
        
        server_device_id_int = int(server_device_id)
        str_val_int = int(str_val)
        
        # 组合数据 (little endian)
        combined_bytes = server_device_id_int.to_bytes(8, 'little') + str_val_int.to_bytes(8, 'little')
        
        # 生成随机IV
        iv = bytes([random.randint(0, 255) for _ in range(16)])
        
        # 加密
        encrypted = self.encrypt(combined_bytes, iv)
        
        # 组合IV和加密数据
        result = iv + encrypted
        
        return base64.b64encode(result).decode('utf-8')