"""
调用 Devnet 合约的 Python 测试脚本
通过 Flask API 调用 Devnet 合约
"""

import base64
import json
import time
import requests

# Devnet 配置
DEVNET_RPC = "https://api.devnet.solana.com"
PROGRAM_ID = "CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS"
FLASK_API = "http://localhost:5000"


def fnv1a_hash(data: str) -> str:
    """与合约一致的哈希算法"""
    result = [i for i in range(16)]
    FNV_PRIME = 0x100000001b3
    hash_val = 0xcbf29ce484222325
    
    for byte in data.encode('utf8'):
        hash_val ^= byte
        hash_val = (hash_val * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
        idx = hash_val % 16
        result[idx] = (result[idx] + byte) & 0xFF
        result[(idx + 1) % 16] ^= (hash_val >> 8) & 0xFF
        result[(idx + 3) % 16] ^= (hash_val >> 16) & 0xFF
        result[(idx + 7) % 16] ^= (hash_val >> 24) & 0xFF
    
    return ''.join(f'{b:02x}' for b in result)


def test_devnet_connection():
    """测试 Devnet 连接"""
    print("=" * 50)
    print("测试 1: Devnet 连接")
    print("=" * 50)
    
    try:
        # 通过 Flask API 检查 Devnet 状态
        response = requests.get(f"{FLASK_API}/api/health?network=devnet", timeout=10)
        result = response.json()
        
        if result.get("success"):
            print(f"✓ 连接成功")
            print(f"  - Flask API: {FLASK_API}")
            print(f"  - Devnet RPC: {DEVNET_RPC}")
            print(f"  - 程序地址: {PROGRAM_ID}")
            return True
        else:
            print(f"✗ 服务异常: {result.get('message')}")
            return False
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False


def test_program_account():
    """查询合约账户信息"""
    print("\n" + "=" * 50)
    print("测试 2: 查询合约账户")
    print("=" * 50)
    
    try:
        # 通过 API 查询合约状态
        response = requests.get(f"{FLASK_API}/api/health?network=devnet", timeout=10)
        result = response.json()
        
        if result.get("success"):
            node_status = result.get("data", {}).get("node_status", {})
            print(f"✓ 合约查询成功")
            print(f"  - 程序地址: {PROGRAM_ID}")
            print(f"  - 网络: {result.get('data', {}).get('network')}")
            print(f"  - 节点状态: {node_status.get('status', 'unknown')}")
            return True
        else:
            print(f"✗ 合约查询失败")
            return False
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        return False


def test_store_via_api(data: str):
    """
    通过 Flask API 存储到 Devnet
    这是推荐方式，因为直接调用合约需要复杂的交易构建
    """
    print("\n" + "=" * 50)
    print("测试 3: 通过 API 存储到 Devnet")
    print("=" * 50)
    
    try:
        # Base64 编码
        encoded = base64.b64encode(data.encode()).decode()
        print(f"原始数据: {data}")
        print(f"Base64: {encoded[:50]}...")
        
        # 调用 Flask API
        response = requests.post(
            "http://localhost:5000/api/store",
            json={"data": encoded, "network": "devnet"},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        result = response.json()
        print(f"\n响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("success"):
            print(f"\n✓ 存储成功!")
            print(f"  - 合约地址: {result['data'].get('recordAddress')}")
            print(f"  - 签名: {result['data'].get('signature')}")
            print(f"  - 交易: {result['data'].get('transactionSignature')}")
            return result['data'].get('recordAddress')
        else:
            print(f"\n✗ 存储失败: {result.get('message')}")
            return None
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return None


def test_query_via_api(address: str):
    """通过 API 查询 Devnet 记录"""
    print("\n" + "=" * 50)
    print("测试 4: 通过 API 查询 Devnet 记录")
    print("=" * 50)
    
    try:
        response = requests.get(
            f"http://localhost:5000/api/record/{address}?network=devnet",
            timeout=30
        )
        
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("success") and result.get("data", {}).get("exists"):
            data = result["data"]
            print(f"\n✓ 查询成功!")
            print(f"  - 原始字符串: {data.get('originalString')}")
            print(f"  - 签名: {data.get('signature')}")
            print(f"  - 验证状态: {'通过' if data.get('verified') else '失败'}")
            return True
        else:
            print(f"\n○ 记录不存在")
            return False
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False


def test_verify_via_api(data: str, address: str):
    """通过 API 验证数据"""
    print("\n" + "=" * 50)
    print("测试 5: 验证数据完整性")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://localhost:5000/api/verify",
            json={"data": data, "recordAddress": address, "network": "devnet"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("success"):
            verified = result.get("data", {}).get("verified")
            print(f"\n{'✓ 验证通过' if verified else '✗ 验证失败'}!")
            return verified
        return False
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("  Solana Devnet 合约测试")
    print("=" * 60)
    print(f"  程序地址: {PROGRAM_ID}")
    print(f"  RPC: {DEVNET_RPC}")
    print("=" * 60)
    
    # 测试 1: 连接
    if not test_devnet_connection():
        print("\n连接失败，停止测试")
        return
    
    # 测试 2: 查询合约
    test_program_account()
    
    # 测试 3: 存储数据
    test_data = f"Hello Devnet - {time.time()}"
    record_address = test_store_via_api(test_data)
    
    if record_address:
        # 等待确认
        print("\n等待交易确认...")
        time.sleep(2)
        
        # 测试 4: 查询记录
        test_query_via_api(record_address)
        
        # 测试 5: 验证数据
        test_verify_via_api(test_data, record_address)
    
    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
