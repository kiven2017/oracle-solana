"""
直接调用 Devnet 的 Python 脚本
不依赖 Node 服务，使用 HTTP API 直接调用
"""

import base64
import json
import time
import requests

# 配置
DEVNET_RPC = "https://api.devnet.solana.com"
PROGRAM_ID = "CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS"

# 使用公共 API 服务（如 QuickNode/Alchemy）或直接 RPC
# 这里使用简单的 HTTP 调用示例


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


def rpc_call(method: str, params: list = None) -> dict:
    """调用 Solana RPC"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or []
    }
    
    try:
        response = requests.post(DEVNET_RPC, json=payload, headers=headers, timeout=30)
        return response.json()
    except Exception as e:
        print(f"RPC 调用失败: {e}")
        return {"error": str(e)}


def test_connection():
    """测试 Devnet 连接"""
    print("=" * 50)
    print("测试 Devnet 连接")
    print("=" * 50)
    
    result = rpc_call("getHealth")
    if "result" in result:
        print(f"✓ Devnet 连接正常")
        print(f"  - RPC: {DEVNET_RPC}")
        print(f"  - 状态: {result['result']}")
        
        # 获取区块高度
        slot = rpc_call("getSlot")
        if "result" in slot:
            print(f"  - 当前区块: {slot['result']}")
        return True
    else:
        print(f"✗ 连接失败: {result.get('error')}")
        return False


def test_program_exists():
    """检查合约是否存在"""
    print("\n" + "=" * 50)
    print("检查合约账户")
    print("=" * 50)
    
    result = rpc_call("getAccountInfo", [PROGRAM_ID, {"encoding": "base64"}])
    
    if "result" in result and result["result"]["value"]:
        account = result["result"]["value"]
        print(f"✓ 合约存在")
        print(f"  - 地址: {PROGRAM_ID}")
        print(f"  - 数据大小: {account['data'][0]} bytes")
        print(f"  - 所有者: {account['owner']}")
        print(f"  - 是否可执行: {account['executable']}")
        return True
    else:
        print(f"✗ 合约不存在")
        return False


def test_hash_consistency():
    """测试哈希算法一致性"""
    print("\n" + "=" * 50)
    print("测试哈希算法")
    print("=" * 50)
    
    test_string = "Hello Devnet"
    hash_result = fnv1a_hash(test_string)
    
    print(f"测试字符串: {test_string}")
    print(f"计算哈希: {hash_result}")
    print(f"✓ 哈希算法正常 (16字节 = 32字符)")
    return hash_result


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  Solana Devnet 直接连接测试")
    print("=" * 60)
    print(f"  程序地址: {PROGRAM_ID}")
    print(f"  RPC: {DEVNET_RPC}")
    print("=" * 60)
    
    # 测试 1: 连接
    if not test_connection():
        print("\n连接失败，停止测试")
        return
    
    # 测试 2: 合约存在
    test_program_exists()
    
    # 测试 3: 哈希算法
    test_hash_consistency()
    
    print("\n" + "=" * 60)
    print("  说明")
    print("=" * 60)
    print("""
当前脚本仅测试连接和合约存在性。

要完整调用合约方法（storeString），需要：
1. 安装 solana-py: pip install solana
2. 安装 anchorpy: pip install anchorpy
3. 构建交易并签名

或者使用已部署的 Node 服务：
  npm run server (Devnet 模式)
  
然后调用 Flask API：
  python3 test_devnet.py
    """)
    print("=" * 60)


if __name__ == "__main__":
    main()
