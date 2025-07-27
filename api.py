"""
API functions for FQNovel
"""
import requests
from typing import Optional
from .models import FqVariable, FqRegisterKeyResponse, FqIBatchFullResponse, FqRegisterKeyPayload


async def batch_full(client: requests.Session, var: FqVariable, item_ids: str, download: bool = False) -> FqIBatchFullResponse:
    """
    批量获取小说内容
    
    :param client: HTTP客户端
    :param var: FQ变量配置
    :param item_ids: 章节ID列表，逗号分隔
    :param download: 是否下载模式
    :return: 批量内容响应
    """
    headers = {
        "Cookie": f"install_id={var.install_id}"
    }
    
    url = "https://api5-normal-sinfonlineb.fqnovel.com/reading/reader/batch_full/v"
    params = {
        "item_ids": item_ids,
        "req_type": "0" if download else "1",
        "aid": var.aid,
        "update_version_code": var.update_version_code
    }
    
    response = client.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    response_data = response.json()
    return FqIBatchFullResponse.from_dict(response_data)


async def register_key(client: requests.Session, var: FqVariable) -> FqRegisterKeyResponse:
    """
    注册获取解密密钥
    
    :param client: HTTP客户端
    :param var: FQ变量配置
    :return: 注册密钥响应
    """
    headers = {
        "Cookie": f"install_id={var.install_id}",
        "Content-Type": "application/json"
    }
    
    url = "https://api5-normal-sinfonlineb.fqnovel.com/reading/crypt/registerkey"
    params = {
        "aid": var.aid
    }
    
    # 创建请求载荷
    payload = FqRegisterKeyPayload.new(var)
    
    response = client.post(url, headers=headers, params=params, json=payload.to_dict())
    response.raise_for_status()
    
    response_data = response.json()
    return FqRegisterKeyResponse.from_dict(response_data)


# 同步版本的函数
def batch_full_sync(client: requests.Session, var: FqVariable, item_ids: str, download: bool = False) -> FqIBatchFullResponse:
    """
    批量获取小说内容 (同步版本)
    """
    headers = {
        "Cookie": f"install_id={var.install_id}"
    }
    
    url = "https://api5-normal-sinfonlineb.fqnovel.com/reading/reader/batch_full/v"
    params = {
        "item_ids": item_ids,
        "req_type": "0" if download else "1",
        "aid": var.aid,
        "update_version_code": var.update_version_code
    }
    
    response = client.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    response_data = response.json()
    return FqIBatchFullResponse.from_dict(response_data)


def register_key_sync(client: requests.Session, var: FqVariable) -> FqRegisterKeyResponse:
    """
    注册获取解密密钥 (同步版本)
    """
    headers = {
        "Cookie": f"install_id={var.install_id}",
        "Content-Type": "application/json"
    }
    
    url = "https://api5-normal-sinfonlineb.fqnovel.com/reading/crypt/registerkey"
    params = {
        "aid": var.aid
    }
    
    # 创建请求载荷
    payload = FqRegisterKeyPayload.new(var)
    
    response = client.post(url, headers=headers, params=params, json=payload.to_dict())
    response.raise_for_status()
    
    response_data = response.json()
    return FqRegisterKeyResponse.from_dict(response_data)