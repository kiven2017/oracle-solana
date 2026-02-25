#!/bin/bash
# 启动 Devnet Node 服务

cd /home/adminad/my-first-app
export SOLANA_NETWORK=devnet
export ANCHOR_WALLET=/home/adminad/.config/solana/id.json

echo "启动 Node 服务 (Devnet 模式)..."
echo "RPC: https://api.devnet.solana.com"
echo ""

npx ts-node app/server.ts
