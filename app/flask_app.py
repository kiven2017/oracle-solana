"""
Solana 字符串上链服务 - Flask API
提供 HTTP API 供第三方调用，支持本地网络和测试网络
"""

from flask import Flask, request, jsonify
import base64
import requests
import os
from typing import Dict, Any, Optional

app = Flask(__name__)

# 配置
CONFIG = {
    "localnet": {
        "node_url": "http://localhost:3000",
        "solana_rpc": "http://127.0.0.1:8899",
        "program_id": "CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS",
        "network": "localnet"
    },
    "devnet": {
        "node_url": "http://localhost:3000",
        "solana_rpc": "https://api.devnet.solana.com",
        "program_id": "CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS",
        "network": "devnet"
    }
}

# 当前网络（可通过环境变量或请求参数切换）
DEFAULT_NETWORK = os.getenv("SOLANA_NETWORK", "localnet")


def fnv1a_hash(data: str) -> str:
    """
    与 Solana 合约一致的哈希算法（基于 FNV-1a）
    返回 16 字节（32 字符十六进制）哈希值
    """
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


def get_network_config(network: str = None) -> Dict[str, str]:
    """获取网络配置"""
    network = network or DEFAULT_NETWORK
    return CONFIG.get(network, CONFIG["localnet"])


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    network = request.args.get('network', DEFAULT_NETWORK)
    config = get_network_config(network)
    
    try:
        # 检查 Node 服务状态
        response = requests.get(f"{config['node_url']}/api/health", timeout=5)
        node_status = response.json() if response.status_code == 200 else {"error": "Node service unavailable"}
    except Exception as e:
        node_status = {"error": str(e)}
    
    return jsonify({
        "success": True,
        "code": 0,
        "message": "Flask API 服务正常运行",
        "data": {
            "status": "healthy",
            "network": network,
            "solana_rpc": config["solana_rpc"],
            "node_status": node_status
        }
    })


@app.route('/api/store', methods=['POST'])
def store_string():
    """
    存储字符串上链
    
    请求体:
    {
        "data": "要存储的字符串（Base64编码）",
        "network": "localnet" | "devnet"  // 可选，默认 localnet
    }
    
    响应:
    {
        "success": true,
        "data": {
            "signature": "哈希签名",
            "recordAddress": "合约地址",
            "costSol": 0.0028,
            "transactionSignature": "交易签名",
            "originalString": "原始字符串"
        }
    }
    """
    try:
        req_data = request.get_json()
        if not req_data or 'data' not in req_data:
            return jsonify({
                "success": False,
                "code": 400,
                "message": "请求参数错误",
                "error": "data 字段是必需的"
            }), 400
        
        data = req_data['data']
        network = req_data.get('network', DEFAULT_NETWORK)
        config = get_network_config(network)
        
        # 解码验证
        try:
            decoded = base64.b64decode(data).decode('utf8')
            expected_hash = fnv1a_hash(decoded)
        except Exception as e:
            return jsonify({
                "success": False,
                "code": 400,
                "message": "数据格式错误",
                "error": "data 必须是有效的 Base64 编码"
            }), 400
        
        # 调用 Node 服务上链
        payload = {"data": data}
        response = requests.post(
            f"{config['node_url']}/api/store",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        result = response.json()
        
        if result.get("success"):
            # 添加验证信息
            result['data']['expectedHash'] = expected_hash
            result['data']['verified'] = result['data'].get('signature') == expected_hash
        
        return jsonify(result), response.status_code
        
    except Exception as e:
        return jsonify({
            "success": False,
            "code": 500,
            "message": "服务器内部错误",
            "error": str(e)
        }), 500


@app.route('/api/record/<address>', methods=['GET'])
def query_by_address(address: str):
    """
    通过合约地址查询上链记录
    
    参数:
        address: 合约地址
        network: localnet | devnet (查询参数)
    
    响应包含验证结果
    """
    try:
        network = request.args.get('network', DEFAULT_NETWORK)
        config = get_network_config(network)
        
        response = requests.get(
            f"{config['node_url']}/api/record/{address}",
            timeout=10
        )
        
        result = response.json()
        
        # 如果查询成功，添加验证信息
        if result.get("success") and result.get("data", {}).get("exists"):
            data = result["data"]
            original = data.get("originalString", "")
            expected_hash = fnv1a_hash(original)
            stored_signature = data.get("signature", "")
            
            data["expectedHash"] = expected_hash
            data["verified"] = expected_hash == stored_signature
        
        return jsonify(result), response.status_code
        
    except Exception as e:
        return jsonify({
            "success": False,
            "code": 500,
            "message": "服务器内部错误",
            "error": str(e)
        }), 500


@app.route('/api/verify', methods=['POST'])
def verify_string():
    """
    验证字符串是否已上链
    
    请求体:
    {
        "data": "原始字符串",
        "recordAddress": "合约地址"  // 可选，如果提供则验证地址是否匹配
    }
    
    响应:
    {
        "success": true,
        "data": {
            "exists": true,
            "verified": true,
            "signature": "哈希值",
            "recordAddress": "合约地址"
        }
    }
    """
    try:
        req_data = request.get_json()
        if not req_data or 'data' not in req_data:
            return jsonify({
                "success": False,
                "code": 400,
                "message": "请求参数错误",
                "error": "data 字段是必需的"
            }), 400
        
        data = req_data['data']
        record_address = req_data.get('recordAddress')
        network = req_data.get('network', DEFAULT_NETWORK)
        config = get_network_config(network)
        
        # 计算哈希
        expected_hash = fnv1a_hash(data)
        
        # 如果提供了地址，直接查询验证
        if record_address:
            response = requests.get(
                f"{config['node_url']}/api/record/{record_address}",
                timeout=10
            )
            result = response.json()
            
            if result.get("success") and result.get("data", {}).get("exists"):
                stored_data = result["data"]
                verified = (
                    stored_data.get("signature") == expected_hash and
                    stored_data.get("originalString") == data
                )
                
                return jsonify({
                    "success": True,
                    "code": 0,
                    "message": "验证完成",
                    "data": {
                        "exists": True,
                        "verified": verified,
                        "signature": expected_hash,
                        "recordAddress": record_address,
                        "originalString": data
                    }
                })
            else:
                return jsonify({
                    "success": True,
                    "code": 0,
                    "message": "未找到上链记录",
                    "data": {
                        "exists": False,
                        "verified": False,
                        "signature": expected_hash,
                        "recordAddress": record_address
                    }
                })
        
        # 如果没有提供地址，需要通过其他方式查询（如扫描）
        # 这里简化处理，返回哈希值供客户端自行判断
        return jsonify({
            "success": True,
            "code": 0,
            "message": "请提供合约地址进行验证",
            "data": {
                "signature": expected_hash,
                "hint": "请使用 /api/record/<address> 接口查询具体地址"
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "code": 500,
            "message": "服务器内部错误",
            "error": str(e)
        }), 500


@app.route('/api/networks', methods=['GET'])
def list_networks():
    """列出支持的网络"""
    return jsonify({
        "success": True,
        "code": 0,
        "message": "支持的网络列表",
        "data": {
            "networks": [
                {
                    "name": "localnet",
                    "description": "本地测试网络",
                    "rpc": CONFIG["localnet"]["solana_rpc"]
                },
                {
                    "name": "devnet",
                    "description": "Solana 测试网络",
                    "rpc": CONFIG["devnet"]["solana_rpc"]
                }
            ],
            "default": DEFAULT_NETWORK
        }
    })


if __name__ == '__main__':
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"=" * 60)
    print(f"  Solana Flask API 服务")
    print(f"=" * 60)
    print(f"  服务地址: http://localhost:{port}")
    print(f"  默认网络: {DEFAULT_NETWORK}")
    print(f"  调试模式: {debug}")
    print(f"=" * 60)
    print(f"  API 端点:")
    print(f"    GET    /api/health          - 健康检查")
    print(f"    GET    /api/networks        - 网络列表")
    print(f"    POST   /api/store           - 存储字符串")
    print(f"    GET    /api/record/<addr>   - 查询记录")
    print(f"    POST   /api/verify          - 验证字符串")
    print(f"=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
