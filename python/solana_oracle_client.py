#!/usr/bin/env python3
"""
Solana Oracle Client - 字符串上链服务 Python SDK

用于与部署在 Render 上的 Solana 字符串存储服务进行交互。
支持字符串存储上链和查询功能。

作者: Xu Fei
版本: 1.0.0
"""

import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class StoreResult:
    """存储结果数据类"""
    success: bool
    signature: Optional[str] = None
    address: Optional[str] = None
    message: str = ""
    error: Optional[str] = None


@dataclass
class QueryResult:
    """查询结果数据类"""
    success: bool
    exists: bool = False
    original_string: Optional[str] = None
    signature: Optional[str] = None
    record: Optional[Dict[str, Any]] = None
    message: str = ""
    error: Optional[str] = None


@dataclass
class HealthStatus:
    """健康状态数据类"""
    success: bool
    status: str = ""
    network: str = ""
    program_id: str = ""
    payer: str = ""
    timestamp: str = ""
    error: Optional[str] = None


class SolanaOracleClient:
    """
    Solana 字符串上链服务客户端
    
    使用示例:
        >>> client = SolanaOracleClient()
        >>> # 存储字符串
        >>> result = client.store_string("Hello Solana!")
        >>> print(result.signature)
        >>> 
        >>> # 查询字符串
        >>> query = client.query_string("Hello Solana!")
        >>> print(query.exists)
    """
    
    def __init__(self, base_url: str = "https://oracle-solana.onrender.com"):
        """
        初始化客户端
        
        Args:
            base_url: 服务基础 URL，默认为 Render 部署地址
        """
        self.base_url = base_url.rstrip('/')
        
    def _make_request(self, url: str, data: Optional[bytes] = None, 
                      headers: Optional[Dict[str, str]] = None,
                      method: str = "GET") -> Dict[str, Any]:
        """发送 HTTP 请求"""
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers or {},
            method=method
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "code": e.code,
                "message": "HTTP 错误",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "code": 500,
                "message": "请求失败",
                "error": str(e)
            }
    
    def health_check(self) -> HealthStatus:
        """
        健康检查
        
        Returns:
            HealthStatus: 服务健康状态
        """
        url = f"{self.base_url}/api/health"
        response = self._make_request(url)
        
        if response.get("success"):
            data = response.get("data", {})
            return HealthStatus(
                success=True,
                status=data.get("status", ""),
                network=data.get("network", ""),
                program_id=data.get("programId", ""),
                payer=data.get("payer", ""),
                timestamp=data.get("timestamp", "")
            )
        else:
            return HealthStatus(
                success=False,
                error=response.get("error", "未知错误")
            )
    
    def store_string(self, data: str) -> StoreResult:
        """
        存储字符串到 Solana 区块链
        
        Args:
            data: 要存储的字符串
            
        Returns:
            StoreResult: 存储结果，包含交易签名
        """
        if not data or not isinstance(data, str):
            return StoreResult(
                success=False,
                error="数据必须是有效的字符串"
            )
        
        url = f"{self.base_url}/api/store"
        payload = json.dumps({"data": data}).encode('utf-8')
        headers = {"Content-Type": "application/json"}
        
        response = self._make_request(url, data=payload, headers=headers, method="POST")
        
        if response.get("success"):
            result_data = response.get("data", {})
            return StoreResult(
                success=True,
                signature=result_data.get("signature"),
                address=result_data.get("address"),
                message=response.get("message", "上链成功")
            )
        else:
            return StoreResult(
                success=False,
                message=response.get("message", ""),
                error=response.get("error", "存储失败")
            )
    
    def query_string(self, data: str) -> QueryResult:
        """
        查询字符串是否已上链
        
        Args:
            data: 要查询的字符串
            
        Returns:
            QueryResult: 查询结果
        """
        if not data or not isinstance(data, str):
            return QueryResult(
                success=False,
                error="查询参数必须是有效的字符串"
            )
        
        # URL 编码字符串
        encoded_data = urllib.parse.quote(data)
        url = f"{self.base_url}/api/query/{encoded_data}"
        
        response = self._make_request(url)
        
        if response.get("success"):
            result_data = response.get("data", {})
            return QueryResult(
                success=True,
                exists=result_data.get("exists", False),
                original_string=result_data.get("originalString"),
                signature=result_data.get("signature"),
                record=result_data.get("record"),
                message=response.get("message", "")
            )
        else:
            return QueryResult(
                success=False,
                message=response.get("message", ""),
                error=response.get("error", "查询失败")
            )


def demo():
    """使用示例"""
    print("=" * 60)
    print("Solana Oracle Client - 使用示例")
    print("=" * 60)
    
    # 初始化客户端
    client = SolanaOracleClient()
    
    # 1. 健康检查
    print("\n【1】健康检查")
    health = client.health_check()
    if health.success:
        print(f"  状态: {health.status}")
        print(f"  网络: {health.network}")
        print(f"  程序 ID: {health.program_id}")
        print(f"  付款账户: {health.payer}")
    else:
        print(f"  错误: {health.error}")
    
    # 2. 存储字符串
    print("\n【2】存储字符串到区块链")
    test_string = "Hello Solana from Python SDK!"
    print(f"  存储内容: {test_string}")
    
    result = client.store_string(test_string)
    if result.success:
        print(f"  ✅ 存储成功!")
        print(f"  交易签名: {result.signature}")
        print(f"  存储地址: {result.address}")
    else:
        print(f"  ❌ 存储失败: {result.error}")
    
    # 3. 查询字符串
    print("\n【3】查询字符串")
    print(f"  查询内容: {test_string}")
    
    query = client.query_string(test_string)
    if query.success:
        if query.exists:
            print(f"  ✅ 找到记录!")
            print(f"  签名: {query.signature}")
            if query.record:
                print(f"  所有者: {query.record.get('owner')}")
                print(f"  时间戳: {query.record.get('timestamp')}")
        else:
            print(f"  ℹ️ 未找到记录")
    else:
        print(f"  ❌ 查询失败: {query.error}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()
