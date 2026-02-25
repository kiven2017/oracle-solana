# Solana Oracle - 区块链字符串存储预言机

一个基于 Solana 区块链的字符串存储预言机系统，提供 HTTP API 接口，允许任何设备或应用将数据永久存储到区块链上。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        第三方应用/设备                            │
│              (IoT设备/Web应用/移动应用/脚本等)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    HTTP/HTTPS 请求
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    API 服务层 (二选一)                            │
├─────────────────────────┬───────────────────────────────────────┤
│   Node.js 服务           │   Python Flask 服务 (可选代理层)       │
│   (Render已部署)         │   python/app.py                       │
│   app/server.ts          │                                       │
└─────────────────────────┴───────────────────────────────────────┘
                              ↓
                    Solana 区块链交互
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Solana 区块链 (Devnet/Mainnet)                      │
│              程序 ID: CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS │
│              programs/my-first-app/src/lib.rs                    │
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
my-first-app/
├── app/                          # Node.js 服务源码
│   └── server.ts                 # Express HTTP 服务器
├── programs/                     # Solana 智能合约
│   └── my-first-app/
│       ├── src/
│       │   └── lib.rs            # Rust 合约代码
│       └── Cargo.toml
├── python/                       # Python 客户端和代理服务
│   ├── app.py                    # Flask HTTP 服务器 (可选)
│   ├── solana_oracle_client.py   # Python SDK 客户端
│   └── requirements.txt          # Python 依赖
├── target/                       # 编译输出 (包含 IDL 和类型定义)
│   ├── idl/
│   │   └── my_first_app.json     # Anchor IDL 文件
│   └── types/
│       └── my_first_app.ts       # TypeScript 类型定义
├── tests/                        # 测试文件
│   └── my-first-app.ts           # Anchor 测试
├── migrations/                   # 部署脚本
│   └── deploy.ts
├── .anchor/                      # Anchor 配置
├── Anchor.toml                   # Anchor 配置文件
├── package.json                  # Node.js 依赖
├── tsconfig.json                 # TypeScript 配置
└── README.md                     # 本文件
```

## 已部署服务

### Render 部署 (Node.js)
- **地址**: https://oracle-solana.onrender.com
- **网络**: Solana Devnet
- **状态**: 运行中

## API 接口

### 1. 健康检查
```http
GET /api/health
```

**响应示例**:
```json
{
  "success": true,
  "code": 0,
  "message": "服务正常运行",
  "data": {
    "status": "healthy",
    "network": "https://api.devnet.solana.com",
    "programId": "CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS",
    "payer": "3BF8UR6by4vsoEhLjBKSqoohZwzJRGCP8wt8K7t1oUTD"
  }
}
```

### 2. 存储字符串 (上链)
```http
POST /api/store
Content-Type: application/json

{
  "data": "要存储的字符串内容"
}
```

**响应示例**:
```json
{
  "success": true,
  "code": 0,
  "message": "上链成功",
  "data": {
    "signature": "d0d531129b988cbf2b4d89547bc15d55",
    "address": "..."
  }
}
```

### 3. 查询字符串
```http
GET /api/query/{data}
```

**响应示例**:
```json
{
  "success": true,
  "code": 0,
  "message": "查询成功",
  "data": {
    "exists": true,
    "originalString": "要存储的字符串内容",
    "signature": "...",
    "record": {
      "owner": "...",
      "timestamp": "...",
      "signature": "..."
    }
  }
}
```

## 使用方式

### 方式 1: 直接使用 HTTP API

```bash
# 健康检查
curl https://oracle-solana.onrender.com/api/health

# 存储字符串
curl -X POST https://oracle-solana.onrender.com/api/store \
  -H "Content-Type: application/json" \
  -d '{"data":"Hello Solana!"}'

# 查询字符串
curl https://oracle-solana.onrender.com/api/query/Hello%20Solana!
```

### 方式 2: Python SDK

```python
from solana_oracle_client import SolanaOracleClient

# 初始化客户端
client = SolanaOracleClient("https://oracle-solana.onrender.com")

# 健康检查
health = client.health_check()
print(f"状态: {health.status}")

# 存储字符串
result = client.store_string("Hello Solana!")
print(f"交易签名: {result.signature}")

# 查询字符串
query = client.query_string("Hello Solana!")
print(f"是否存在: {query.exists}")
```

### 方式 3: 部署自己的 Flask 代理服务

```bash
cd python
pip install -r requirements.txt
python app.py
```

然后访问: http://localhost:5000

## 本地开发

### 环境要求
- Node.js 18+
- Python 3.8+
- Rust
- Solana CLI
- Anchor 0.32+

### 安装依赖

```bash
# Node.js 依赖
npm install

# Python 依赖 (可选)
cd python
pip install -r requirements.txt
```

### 本地运行

```bash
# 1. 启动本地 Solana 节点
solana-test-validator

# 2. 部署合约
anchor deploy

# 3. 启动 Node.js 服务
npm run dev

# 或启动 Python Flask 服务
cd python
python app.py
```

## 部署指南

### 部署到 Render (Node.js)

1. Fork 本仓库到 GitHub
2. 在 Render 创建新的 Web Service
3. 选择 GitHub 仓库
4. 配置:
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `node dist/app/server.js`
5. 添加环境变量:
   - `SOLANA_NETWORK`: `devnet`
   - `ANCHOR_WALLET`: `[你的钱包私钥数组]`

### 部署到阿里云 ECS

```bash
# 1. 克隆代码
git clone https://github.com/kiven2017/oracle-solana.git
cd oracle-solana

# 2. 安装依赖
npm install
npm run build

# 3. 设置环境变量
export SOLANA_NETWORK=devnet
export ANCHOR_WALLET='[你的钱包私钥数组]'

# 4. 启动服务
npm start
```

### Docker 部署

```bash
# 构建镜像
docker build -t oracle-solana .

# 运行容器
docker run -d \
  -p 3000:3000 \
  -e SOLANA_NETWORK=devnet \
  -e ANCHOR_WALLET='[你的钱包私钥数组]' \
  --name oracle-solana \
  oracle-solana
```

## 技术栈

- **区块链**: Solana (Devnet/Mainnet)
- **智能合约**: Rust + Anchor Framework
- **后端服务**: Node.js + Express + TypeScript
- **Python 服务**: Flask (可选代理层)
- **Python SDK**: 标准库 urllib (零依赖)

## 作者

- **Name**: Xu Fei (徐飞)
- **GitHub**: https://github.com/kiven2017
- **Project**: oracle-solana

## 许可证

MIT
