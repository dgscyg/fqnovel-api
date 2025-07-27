"""
Data structures for FQNovel API
"""
from typing import Dict, Any, Optional


class FqVariable:
    """FQNovel 变量配置"""
    
    def __init__(self, install_id: str, server_device_id: str, aid: str, update_version_code: str):
        self.install_id = install_id
        self.server_device_id = server_device_id
        self.aid = aid
        self.update_version_code = update_version_code


class FqRegisterKeyPayload:
    """注册密钥请求载荷"""
    
    def __init__(self, content: str, keyver: int = 1):
        self.content = content  # 也叫 key
        self.keyver = keyver
    
    @classmethod
    def new(cls, var: FqVariable) -> 'FqRegisterKeyPayload':
        """创建新的注册密钥载荷"""
        from .crypto_utils import FqCrypto
        
        # 使用固定的注册密钥
        REG_KEY = "ac25c67ddd8f38c1b37a2348828e222e"
        crypto = FqCrypto(REG_KEY)
        content = crypto.new_register_key_content(var.server_device_id, "0")
        return cls(content, 1)
    
    def get_key(self) -> str:
        """从载荷中获取密钥"""
        from .crypto_utils import FqCrypto, bytes_to_hex_upper
        
        REG_KEY = "ac25c67ddd8f38c1b37a2348828e222e"
        crypto = FqCrypto(REG_KEY)
        byte_key = crypto.decrypt(self.content)
        return bytes_to_hex_upper(byte_key)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式用于JSON序列化"""
        return {
            "key": self.content,
            "keyver": self.keyver
        }


class FqRegisterKeyResponse:
    """注册密钥响应"""
    
    def __init__(self, code: int, message: str, data: Dict[str, Any]):
        self.code = code
        self.message = message
        self.data = FqRegisterKeyPayload(data.get("key", ""), data.get("keyver", 1))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FqRegisterKeyResponse':
        """从字典创建响应对象"""
        return cls(
            code=data.get("code", 0),
            message=data.get("message", ""),
            data=data.get("data", {})
        )


class ItemContent:
    """章节内容"""
    
    def __init__(self, code: int, title: str, content: str, novel_data: Any, 
                 text_type: int, crypt_status: int, compress_status: int, 
                 key_version: int, paragraphs_num: int):
        self.code = code
        self.title = title
        self.content = content
        self.novel_data = novel_data
        self.text_type = text_type
        self.crypt_status = crypt_status
        self.compress_status = compress_status
        self.key_version = key_version
        self.paragraphs_num = paragraphs_num
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItemContent':
        """从字典创建内容对象"""
        return cls(
            code=data.get("code", 0),
            title=data.get("title", ""),
            content=data.get("content", ""),
            novel_data=data.get("novel_data"),
            text_type=data.get("text_type", 0),
            crypt_status=data.get("crypt_status", 0),
            compress_status=data.get("compress_status", 0),
            key_version=data.get("key_version", 0),
            paragraphs_num=data.get("paragraphs_num", 0)
        )


class FqIBatchFullResponse:
    """批量获取内容响应"""
    
    def __init__(self, code: int, message: str, data: Dict[str, ItemContent]):
        self.code = code
        self.message = message
        self.data = data
    
    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'FqIBatchFullResponse':
        """从字典创建响应对象"""
        data = {}
        for item_id, item_data in response_data.get("data", {}).items():
            data[item_id] = ItemContent.from_dict(item_data)
        
        return cls(
            code=response_data.get("code", 0),
            message=response_data.get("message", ""),
            data=data
        )
    
    async def get_decrypt_contents(self, client, var: FqVariable) -> list:
        """获取解密后的内容"""
        from .api import register_key
        from .crypto_utils import chapter_decrypt
        
        # 获取注册密钥
        register_key_response = await register_key(client, var)
        key = register_key_response.data.get_key()
        
        # 解密前16字节作为实际密钥
        actual_key = key[:32]  # 前16字节的hex表示是32个字符
        
        result = []
        for item_id, content in self.data.items():
            decrypted_content = chapter_decrypt(content.content, actual_key, save_files=False)
            if decrypted_content:
                result.append((item_id, decrypted_content))
        
        return result