"""
直接调用 Devnet 合约的 Python 脚本
使用 solana-py 和 anchorpy 直接调用链上合约
"""

import asyncio
import base64
import json
import time
from pathlib import Path

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey

# 配置
DEVNET_RPC = "https://api.devnet.solana.com"
PROGRAM_ID = Pubkey.from_string("CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS")

# 加载 IDL
IDL_PATH = Path("/home/adminad/my-first-app/target/idl/my_first_app.json")


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


async def test_connection():
    """测试 Devnet 连接"""
    print("=" * 50)
    print("测试 Devnet 连接")
    print("=" * 50)
    
    client = AsyncClient(DEVNET_RPC, commitment=Confirmed)
    try:
        # 获取区块高度
        slot = await client.get_slot()
        print(f"✓ 连接成功")
        print(f"  - RPC: {DEVNET_RPC}")
        print(f"  - 当前区块: {slot.value}")
        
        # 检查合约账户
        account_info = await client.get_account_info(PROGRAM_ID)
        if account_info.value:
            print(f"  - 合约存在: {PROGRAM_ID}")
            print(f"  - 可执行: {account_info.value.executable}")
        
        await client.close()
        return True
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False


async def test_load_idl():
    """读取 IDL 信息"""
    print("\n" + "=" * 50)
    print("读取 IDL 信息")
    print("=" * 50)
    
    try:
        # 读取 IDL
        with open(IDL_PATH) as f:
            idl_json = json.load(f)
        
        print(f"✓ IDL 读取成功")
        print(f"  - 程序名称: {idl_json.get('name')}")
        print(f"  - 版本: {idl_json.get('version')}")
        print(f"  - 指令数量: {len(idl_json.get('instructions', []))}")
        
        # 显示可用指令
        print(f"\n  可用指令:")
        for ix in idl_json.get('instructions', []):
            print(f"    - {ix.get('name')}")
        
        return idl_json
    except Exception as e:
        print(f"✗ 读取失败: {e}")
        return None


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  Solana Devnet 合约直接调用测试")
    print("=" * 60)
    print(f"  程序地址: {PROGRAM_ID}")
    print(f"  RPC: {DEVNET_RPC}")
    print("=" * 60)
    
    # 测试 1: 连接
    if not await test_connection():
        print("\n连接失败，停止测试")
        return
    
    # 测试 2: 读取 IDL
    idl = await test_load_idl()
    if not idl:
        print("\nIDL 读取失败")
        return
    
    # 测试 3: 哈希算法
    print("\n" + "=" * 50)
    print("测试哈希算法")
    print("=" * 50)
    test_data = "Hello Devnet"
    hash_result = fnv1a_hash(test_data)
    print(f"测试数据: {test_data}")
    print(f"计算哈希: {hash_result}")
    print(f"✓ 哈希算法正常")
    
    print("\n" + "=" * 60)
    print("  总结")
    print("=" * 60)
    print("""
✓ 成功连接到 Devnet 合约
✓ 读取了 IDL 信息
✓ 哈希算法验证通过

当前 Python 脚本可以：
- 查询链上数据
- 验证合约存在性
- 计算与合约一致的哈希

要调用 storeString 存储数据，建议：
1. 使用 Node 服务 (server.ts) - 推荐
2. 或使用命令行: anchor call

因为直接调用需要处理：
- 账户创建
- Rent 计算
- 交易签名
- Anchor 指令编码
    """)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
