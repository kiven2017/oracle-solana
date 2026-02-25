#!/usr/bin/env python3
"""
Solana Oracle Flask Server - 字符串上链服务代理

为第三方提供 HTTP API 接口，将字符串存储到 Solana 区块链。
部署在 Render 或其他 Python 服务器环境。

作者: Xu Fei
版本: 1.0.0
"""

from flask import Flask, request, jsonify
from solana_oracle_client import SolanaOracleClient, StoreResult, QueryResult
import os

app = Flask(__name__)

# 初始化 Solana Oracle 客户端
# 从环境变量读取服务地址，默认使用 Render 部署地址
ORACLE_BASE_URL = os.environ.get("ORACLE_BASE_URL", "https://oracle-solana.onrender.com")
oracle_client = SolanaOracleClient(base_url=ORACLE_BASE_URL)


@app.route("/", methods=["GET"])
def index():
    """根路径 - 服务信息"""
    return jsonify({
        "service": "Solana Oracle Flask Server",
        "version": "1.0.0",
        "description": "字符串上链服务代理",
        "upstream": ORACLE_BASE_URL,
        "endpoints": {
            "health": "GET /health",
            "store": "POST /api/store",
            "query": "GET /api/query/<data>"
        }
    })


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查 - 检查上游服务状态"""
    try:
        health = oracle_client.health_check()
        if health.success:
            return jsonify({
                "success": True,
                "code": 0,
                "message": "服务正常运行",
                "data": {
                    "status": health.status,
                    "network": health.network,
                    "programId": health.program_id,
                    "payer": health.payer,
                    "upstream": ORACLE_BASE_URL
                }
            })
        else:
            return jsonify({
                "success": False,
                "code": 503,
                "message": "上游服务不可用",
                "error": health.error
            }), 503
    except Exception as e:
        return jsonify({
            "success": False,
            "code": 500,
            "message": "健康检查失败",
            "error": str(e)
        }), 500


@app.route("/api/store", methods=["POST"])
def store_string():
    """
    存储字符串到 Solana 区块链
    
    请求体:
        {"data": "要存储的字符串"}
    
    响应:
        {
            "success": true/false,
            "code": 0,
            "message": "上链成功",
            "data": {
                "signature": "交易签名",
                "address": "存储地址"
            }
        }
    """
    try:
        # 获取请求数据
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                "success": False,
                "code": 400,
                "message": "请求参数错误",
                "error": "请求体必须是 JSON 格式"
            }), 400
        
        data = request_data.get("data")
        if not data or not isinstance(data, str):
            return jsonify({
                "success": False,
                "code": 400,
                "message": "请求参数错误",
                "error": "data 字段是必需的且必须是字符串"
            }), 400
        
        # 调用上游服务存储字符串
        result = oracle_client.store_string(data)
        
        if result.success:
            return jsonify({
                "success": True,
                "code": 0,
                "message": result.message,
                "data": {
                    "signature": result.signature,
                    "address": result.address
                }
            })
        else:
            return jsonify({
                "success": False,
                "code": 400,
                "message": result.message,
                "error": result.error
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "code": 500,
            "message": "服务器内部错误",
            "error": str(e)
        }), 500


@app.route("/api/query/<path:data>", methods=["GET"])
def query_string(data):
    """
    查询字符串是否已上链
    
    路径参数:
        data: 要查询的字符串 (URL 编码)
    
    响应:
        {
            "success": true/false,
            "code": 0,
            "message": "查询成功",
            "data": {
                "exists": true/false,
                "originalString": "原始字符串",
                "signature": "签名",
                "record": { ... }
            }
        }
    """
    try:
        if not data:
            return jsonify({
                "success": False,
                "code": 400,
                "message": "请求参数错误",
                "error": "查询参数不能为空"
            }), 400
        
        # 调用上游服务查询
        result = oracle_client.query_string(data)
        
        if result.success:
            response_data = {
                "exists": result.exists,
                "originalString": result.original_string,
                "signature": result.signature
            }
            
            if result.record:
                response_data["record"] = result.record
            
            return jsonify({
                "success": True,
                "code": 0,
                "message": result.message,
                "data": response_data
            })
        else:
            return jsonify({
                "success": False,
                "code": 400,
                "message": result.message,
                "error": result.error
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "code": 500,
            "message": "服务器内部错误",
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({
        "success": False,
        "code": 404,
        "message": "接口不存在",
        "error": "请求的接口不存在，请检查 URL"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """405 错误处理"""
    return jsonify({
        "success": False,
        "code": 405,
        "message": "方法不允许",
        "error": "该接口不支持此 HTTP 方法"
    }), 405


if __name__ == "__main__":
    # 本地开发模式
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    print(f"=" * 60)
    print(f"Solana Oracle Flask Server")
    print(f"=" * 60)
    print(f"上游服务: {ORACLE_BASE_URL}")
    print(f"监听端口: {port}")
    print(f"调试模式: {debug}")
    print(f"=" * 60)
    
    app.run(host="0.0.0.0", port=port, debug=debug)
