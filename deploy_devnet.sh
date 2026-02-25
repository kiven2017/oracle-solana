#!/bin/bash
# 部署到 Devnet 测试网的脚本

export PATH="$HOME/.cargo/bin:$HOME/.local/share/solana/install/active_release/bin:$PATH"

echo "========================================"
echo "  部署到 Solana Devnet 测试网"
echo "========================================"

# 切换到 devnet
solana config set --url devnet
echo ""
echo "当前配置:"
solana config get
echo ""

# 检查余额
echo "检查账户余额..."
solana balance
echo ""

# 如果余额不足，请求空投
read -p "是否需要申请 Devnet SOL 空投? (y/n): " need_airdrop
if [ "$need_airdrop" = "y" ] || [ "$need_airdrop" = "Y" ]; then
    echo "正在申请 2 SOL 空投..."
    solana airdrop 2
    echo "新余额:"
    solana balance
fi

echo ""
echo "开始部署合约..."
cd /home/adminad/my-first-app

# 使用 anchor 部署
source ~/.nvm/nvm.sh
nvm use node
anchor deploy

echo ""
echo "========================================"
echo "  部署完成"
echo "========================================"
