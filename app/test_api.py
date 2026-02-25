#!/usr/bin/env python3
"""
Python 客户端测试脚本 - 用于测试 Solana 字符串上链服务 API

使用方法:
    python3 test_api.py                    # 测试本地服务
    python3 test_api.py http://your-server:3000  # 测试远程服务
"""

import requests
import json
import sys
import os

# 支持通过命令行参数或环境变量配置服务器地址
BASE_URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("API_SERVER", "http://localhost:3000")

def test_health():
    """测试健康检查接口"""
    print("=" * 50)
    print("测试 1: 健康检查 (/api/health)")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get("success", False)
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_store_string(test_string: str):
    """测试存储字符串上链"""
    print("\n" + "=" * 50)
    print(f"测试 2: 存储字符串上链 (/api/store)")
    print(f"输入: '{test_string}'")
    print("=" * 50)
    
    try:
        payload = {"data": test_string}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/store",
            json=payload,
            headers=headers
        )
        data = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get("success"):
            result = data.get("data", {})
            print(f"\n✓ 上链成功!")
            print(f"  - 签名: {result.get('signature', 'N/A')[:32]}...")
            print(f"  - 存储地址: {result.get('recordAddress', 'N/A')}")
            print(f"  - 消耗 SOL: {result.get('costSol', 0):.9f}")
            print(f"  - 交易签名: {result.get('transactionSignature', 'N/A')[:20]}...")
        else:
            print(f"\n✗ 上链失败: {data.get('message')}")
            
        return data.get("success", False)
    except Exception as e:
        print(f"错误: {e}")
        return False

# 保存最后一次存储的合约地址
_last_record_address = None

def fnv1a_hash(data: str) -> str:
    """
    与 Solana 合约一致的哈希算法（基于 FNV-1a）
    返回 16 字节（32 字符十六进制）哈希值
    """
    # 初始化结果数组
    result = [i for i in range(16)]
    
    # FNV-1a 参数
    FNV_PRIME = 0x100000001b3
    hash_val = 0xcbf29ce484222325
    
    # 处理每个字节
    for byte in data.encode('utf8'):
        hash_val ^= byte
        hash_val = (hash_val * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
        
        idx = hash_val % 16
        result[idx] = (result[idx] + byte) & 0xFF
        result[(idx + 1) % 16] ^= (hash_val >> 8) & 0xFF
        result[(idx + 3) % 16] ^= (hash_val >> 16) & 0xFF
        result[(idx + 7) % 16] ^= (hash_val >> 24) & 0xFF
    
    # 转换为十六进制字符串
    return ''.join(f'{b:02x}' for b in result)

def test_store_string(test_string: str):
    """测试存储字符串上链（Base64编码）"""
    global _last_record_address
    print("\n" + "=" * 50)
    print(f"测试 2: 存储字符串上链 (/api/store)")
    print(f"输入: '{test_string}'")
    print("=" * 50)
    
    try:
        import base64
        # Base64 编码
        encoded_data = base64.b64encode(test_string.encode('utf8')).decode('utf8')
        print(f"Base64 编码: {encoded_data[:50]}...")
        
        payload = {"data": encoded_data}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/store",
            json=payload,
            headers=headers
        )
        data = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get("success"):
            result = data.get("data", {})
            _last_record_address = result.get('recordAddress')
            print(f"\n✓ 上链成功!")
            print(f"  - 签名: {result.get('signature', 'N/A')[:32]}...")
            print(f"  - 合约地址: {result.get('recordAddress', 'N/A')}")
            print(f"  - 消耗 SOL: {result.get('costSol', 0):.9f}")
            print(f"  - 交易签名: {result.get('transactionSignature', 'N/A')[:20]}...")
            print(f"\n  [请保存合约地址用于后续查询: {_last_record_address}]")
        else:
            print(f"\n✗ 上链失败: {data.get('message')}")
            
        return data.get("success", False)
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_query_by_address(address: str = None):
    """测试通过合约地址查询上链记录"""
    print("\n" + "=" * 50)
    print(f"测试 3: 通过合约地址查询 (/api/record/:address)")
    
    # 如果没有提供地址，使用最后一次存储的地址
    if address is None:
        address = _last_record_address
    
    if address is None:
        print("没有可用的合约地址，跳过查询测试")
        return False
    
    print(f"查询地址: '{address}'")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/record/{address}")
        data = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get("success"):
            result = data.get("data", {})
            if result.get("exists"):
                print(f"\n✓ 找到上链记录!")
                print(f"  - 签名: {result.get('signature', 'N/A')}")
                print(f"  - 合约地址: {result.get('recordAddress', 'N/A')}")
                print(f"  - 原始字符串: {result.get('originalString', 'N/A')}")
                print(f"  - 上链时间: {result.get('timestamp', 0)}")
                print(f"  - 消耗 SOL: {result.get('costSol', 0):.9f}")
                print(f"  - 所有者: {result.get('owner', 'N/A')}")
                
                # 客户端验证示例
                original = result.get('originalString', '')
                expected_hash = fnv1a_hash(original)
                stored_signature = result.get('signature', '')
                
                print(f"\n  [客户端验证]")
                print(f"  - 计算哈希: {expected_hash}")
                print(f"  - 存储签名: {stored_signature}")
                if expected_hash == stored_signature:
                    print(f"  ✓ 哈希验证通过，数据未被篡改")
                else:
                    print(f"  ✗ 哈希验证失败，数据可能已被篡改!")
            else:
                print(f"\n○ 未找到上链记录")
        
        return data.get("success", False)
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_duplicate_store(test_string: str):
    """测试重复存储（应该失败）"""
    print("\n" + "=" * 50)
    print(f"测试 4: 重复存储测试（应该失败）")
    print(f"输入: '{test_string}'")
    print("=" * 50)
    
    try:
        payload = {"data": test_string}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/store",
            json=payload,
            headers=headers
        )
        data = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if not data.get("success"):
            print(f"\n✓ 正确阻止了重复存储")
            print(f"  - 错误码: {data.get('code')}")
            print(f"  - 错误信息: {data.get('message')}")
            return True
        else:
            print(f"\n✗ 应该阻止重复存储，但成功了")
            return False
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("  Solana 字符串上链服务 - Python 客户端测试")
    print(f"  服务器地址: {BASE_URL}")
    print("=" * 60)
    
    # 测试 1: 健康检查
    if not test_health():
        print("\n✗ 服务未启动或健康检查失败")
        sys.exit(1)
    
    # 测试 2: 存储字符串
    test_string = f"Hello from Python Client - {__import__('time').time()}"
    store_success = test_store_string(test_string)
    if not store_success:
        print("\n✗ 存储字符串失败")
        # 继续测试其他接口
    
    # 测试 3: 通过合约地址查询（使用刚才存储的地址）
    test_query_by_address()
    
    # 测试 4: 再次存储相同字符串（可以上链，因为使用随机地址）
    if store_success:
        print("\n" + "=" * 50)
        print("测试 4: 再次存储相同字符串（可以上链）")
        print("=" * 50)
        test_store_string(test_string)
    
    # 测试 5: 查询不存在的地址
    test_query_by_address("11111111111111111111111111111111")
    
    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
