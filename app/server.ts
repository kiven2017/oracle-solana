import express, { Request, Response } from "express";
import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { MyFirstApp } from "../target/types/my_first_app";
import cors from "cors";
import fetch from "node-fetch";

// 全局替换 fetch 为 node-fetch
(global as any).fetch = fetch;

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// 请求日志中间件
app.use((req: Request, res: Response, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  console.log("  Content-Type:", req.headers['content-type']);
  next();
});

// 内存缓存：已上链的签名集合（用于重复检测）
const uploadedSignatures = new Set<string>();

// 配置 Solana 连接
// 支持通过环境变量配置网络: localnet | devnet | mainnet
const NETWORK = process.env.SOLANA_NETWORK || "localnet";
const NETWORK_URLS: { [key: string]: string } = {
  localnet: "http://127.0.0.1:8899",
  devnet: "https://api.devnet.solana.com",
  mainnet: "https://api.mainnet-beta.solana.com",
};

const connection = new anchor.web3.Connection(NETWORK_URLS[NETWORK] || NETWORK_URLS.localnet, "confirmed");
const wallet = anchor.Wallet.local();
const provider = new anchor.AnchorProvider(connection, wallet, {
  commitment: "confirmed",
});
anchor.setProvider(provider);

// 加载程序 - 使用 workspace 方式（Anchor 自动处理 IDL）
const program = anchor.workspace.myFirstApp as Program<MyFirstApp>;
const payer = provider.wallet as anchor.Wallet;

console.log(`使用 RPC: ${connection.rpcEndpoint}`);

// 计算 MD5 哈希（与合约一致，16字节）
function md5Hash(data: string): Buffer {
  const result = Buffer.alloc(16);
  
  // 初始化 - 与合约一致
  for (let i = 0; i < 16; i++) {
    result[i] = i;
  }
  
  // FNV-1a 哈希 - 使用 u64 运算（与合约一致）
  const FNV_PRIME = 0x100000001b3;
  let hash = 0xcbf29ce484222325;
  
  const bytes = Buffer.from(data, "utf8");
  for (const byte of bytes) {
    hash ^= byte;
    // 使用 BigInt 进行乘法，然后转回 Number 保持 64 位
    hash = Number((BigInt(hash) * BigInt(FNV_PRIME)) & BigInt("0xFFFFFFFFFFFFFFFF"));
    
    const idx = hash % 16;
    result[idx] = (result[idx] + byte) & 0xFF;
    result[(idx + 1) % 16] ^= (hash >> 8) & 0xFF;
    result[(idx + 3) % 16] ^= (hash >> 16) & 0xFF;
    result[(idx + 7) % 16] ^= (hash >> 24) & 0xFF;
  }
  
  return result;
}

// 错误码映射
const ERROR_CODES: { [key: string]: { code: number; message: string } } = {
  AlreadyExists: { code: 1001, message: "该字符串已经上链，不能重复提交" },
  EmptyString: { code: 1002, message: "字符串不能为空" },
  StringTooLong: { code: 1003, message: "字符串长度超过限制（最大200字符）" },
  AccountNotFound: { code: 1004, message: "账户不存在" },
  InsufficientFunds: { code: 1005, message: "SOL 余额不足" },
};

/**
 * 标准响应格式
 */
interface ApiResponse<T = any> {
  success: boolean;
  code: number;
  message: string;
  data?: T;
  error?: string;
}

/**
 * 存储结果数据结构
 */
interface StoreResult {
  signature: string; // 十六进制格式的签名
  recordAddress: string; // 存储账户地址
  costLamports: number; // 消耗的 lamports
  costSol: number; // 消耗的 SOL
  transactionSignature: string; // 交易签名
  timestamp: number; // 上链时间戳
  originalString: string; // 原始字符串
}

/**
 * 查询结果数据结构
 */
interface QueryResult {
  exists: boolean;
  recordAddress?: string;
  signature?: string;
  timestamp?: number;
  owner?: string;
  costLamports?: number;
  costSol?: number;
  originalString?: string;
}

/**
 * POST /api/store - 存储字符串上链
 * 
 * 请求体: { "data": "要存储的字符串" }
 * 
 * 成功响应:
 * {
 *   success: true,
 *   code: 0,
 *   message: "上链成功",
 *   data: {
 *     signature: "32字节哈希（十六进制）",
 *     recordAddress: "存储地址",
 *     costLamports: 消耗的原生代币数量,
 *     costSol: 消耗的 SOL 数量,
 *     transactionSignature: "交易签名",
 *     timestamp: 时间戳,
 *     originalString: "原始字符串"
 *   }
 * }
 * 
 * 错误响应:
 * {
 *   success: false,
 *   code: 错误码,
 *   message: "错误描述",
 *   error: "详细错误信息"
 * }
 */
app.post("/api/store", async (req: Request, res: Response) => {
  try {
    console.log("收到请求体:", req.body);
    const { data } = req.body;

    // 参数验证
    if (data === undefined || data === null || typeof data !== "string") {
      const response: ApiResponse = {
        success: false,
        code: 400,
        message: "请求参数错误",
        error: `data 字段是必需的且必须是字符串，收到: ${JSON.stringify(req.body)}`,
      };
      return res.status(400).json(response);
    }

    // 检查长度
    if (data.length > 200) {
      const response: ApiResponse = {
        success: false,
        code: ERROR_CODES.StringTooLong.code,
        message: ERROR_CODES.StringTooLong.message,
        error: `字符串长度 ${data.length} 超过最大限制 200`,
      };
      return res.status(400).json(response);
    }

    console.log(`[${new Date().toISOString()}] 收到存储请求`);

    // 解码 Base64 数据
    let decodedData: string;
    try {
      decodedData = Buffer.from(data, 'base64').toString('utf8');
      console.log(`解码后数据: "${decodedData}"`);
    } catch (e) {
      const response: ApiResponse = {
        success: false,
        code: 400,
        message: "数据格式错误",
        error: "数据必须是 Base64 编码",
      };
      return res.status(400).json(response);
    }

    // 计算字符串的 MD5 哈希
    const signatureBuffer = md5Hash(decodedData);
    const signatureHex = signatureBuffer.toString('hex');
    console.log(`字符串 MD5: ${signatureHex}`);

    // 生成新的 keypair 作为存储账户
    const recordKeypair = anchor.web3.Keypair.generate();
    const recordAddress = recordKeypair.publicKey;

    console.log(`生成的存储地址: ${recordAddress.toBase58()}`);

    // 调用合约存储字符串（传入解码后的原始数据）
    const txSignature = await program.methods
      .storeString(decodedData)
      .accounts({
        record: recordAddress,
        payer: payer.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      } as any)
      .signers([recordKeypair])
      .rpc();

    console.log(`交易已提交: ${txSignature}`);

    // 确认交易
    await provider.connection.confirmTransaction(txSignature, "confirmed");

    // 等待一小段时间确保账户数据可用
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 使用原始 RPC 获取账户数据（更可靠）
    let accountInfo = null;
    let retries = 5;
    while (retries > 0) {
      accountInfo = await provider.connection.getAccountInfo(recordAddress);
      if (accountInfo !== null) {
        console.log(`成功获取账户数据，剩余重试次数: ${retries}`);
        break;
      }
      retries--;
      console.log(`获取账户失败，剩余重试次数: ${retries}`);
      if (retries === 0) {
        throw new Error(`Account does not exist: ${recordAddress.toBase58()}`);
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // 手动解析账户数据
    // 数据格式: discriminator(8) + original_string(len:4 + data) + signature(16) + timestamp(8) + owner(32) + cost_lamports(8)
    const accountData = accountInfo!.data;
    let offset = 8; // 跳过 discriminator
    
    // 读取字符串长度
    const strLen = accountData.readUInt32LE(offset);
    offset += 4;
    // 读取字符串
    const originalString = accountData.slice(offset, offset + strLen).toString('utf8');
    offset += strLen;
    
    // 读取 signature (16 bytes)
    const signature = accountData.slice(offset, offset + 16);
    offset += 16;
    
    // 读取 timestamp (i64, 8 bytes)
    const timestamp = Number(accountData.readBigInt64LE(offset));
    offset += 8;
    
    // 读取 owner (32 bytes)
    const owner = new anchor.web3.PublicKey(accountData.slice(offset, offset + 32));
    offset += 32;
    
    // 读取 cost_lamports (u64, 8 bytes)
    const costLamports = Number(accountData.readBigUInt64LE(offset));

    const record = {
      originalString,
      signature: signature as Buffer,
      timestamp,
      owner,
      costLamports
    };

    const result: StoreResult = {
      signature: Buffer.from(record.signature).toString("hex"),
      recordAddress: recordAddress.toBase58(),
      costLamports: record.costLamports,
      costSol: record.costLamports / anchor.web3.LAMPORTS_PER_SOL,
      transactionSignature: txSignature,
      timestamp: record.timestamp,
      originalString: decodedData,
    };

    console.log(`存储成功:`, result);

    const response: ApiResponse<StoreResult> = {
      success: true,
      code: 0,
      message: "上链成功",
      data: result,
    };

    return res.status(200).json(response);
  } catch (error: any) {
    console.error("存储失败:", error);

    // 解析合约错误
    let errorCode = 500;
    let errorMessage = "服务器内部错误";
    let errorDetail = error.message || String(error);

    // 检查是否是已知的合约错误
    for (const [key, value] of Object.entries(ERROR_CODES)) {
      if (error.message?.includes(key)) {
        errorCode = value.code;
        errorMessage = value.message;
        break;
      }
    }

    // 特殊错误处理
    if (error.message?.includes("0x1")) {
      errorCode = ERROR_CODES.InsufficientFunds.code;
      errorMessage = ERROR_CODES.InsufficientFunds.message;
    }

    const response: ApiResponse = {
      success: false,
      code: errorCode,
      message: errorMessage,
      error: errorDetail,
    };

    return res.status(errorCode === 500 ? 500 : 400).json(response);
  }
});

/**
 * GET /api/query/:data - 通过原始字符串查询上链记录
 * 
 * 注意：由于使用 PDA 存储，相同字符串会生成相同地址
 * 通过传递原始字符串（URL 编码）即可查询
 * 
 * 成功响应:
 * {
 *   success: true,
 *   code: 0,
 *   message: "查询成功",
 *   data: {
 *     exists: true/false,
 *     recordAddress: "PDA 地址",
 *     signature: "MD5 签名",
 *     timestamp: 时间戳,
 *     owner: "所有者地址",
 *     costLamports: 消耗的原生代币,
 *     costSol: 消耗的 SOL,
 *     originalString: "原始字符串"
 *   }
 * }
 */
app.get("/api/query/:data", async (req: Request, res: Response) => {
  try {
    const { data } = req.params;

    if (!data) {
      const response: ApiResponse = {
        success: false,
        code: 400,
        message: "请求参数错误",
        error: "data 参数是必需的",
      };
      return res.status(400).json(response);
    }

    console.log(`[${new Date().toISOString()}] 查询请求，数据: "${data}"`);

    // 解码 URL 编码的字符串
    const originalString = decodeURIComponent(data);
    
    // 计算 MD5 哈希
    const signatureBuffer = md5Hash(originalString);
    const signatureHex = signatureBuffer.toString('hex');
    
    console.log(`查询字符串: "${originalString}"`);
    console.log(`MD5 哈希: ${signatureHex}`);
    
    // 先检查内存缓存（快速路径）
    if (!uploadedSignatures.has(signatureHex)) {
      console.log(`缓存中未找到，该字符串未上链`);
      const response: ApiResponse<QueryResult> = {
        success: true,
        code: 0,
        message: "未找到上链记录",
        data: {
          exists: false,
          originalString: originalString,
          signature: signatureHex,
        },
      };
      return res.status(200).json(response);
    }
    
    console.log(`缓存中找到签名，扫描链上数据...`);

    // 获取程序所有账户并查找匹配的记录
    const accounts = await provider.connection.getProgramAccounts(program.programId, {
      commitment: "confirmed",
    });

    console.log(`扫描 ${accounts.length} 个账户...`);

    // 遍历账户查找匹配的记录
    for (const account of accounts) {
      const accountData = account.account.data;
      
      // 检查账户数据长度是否足够
      if (accountData.length < 8 + 4 + 16 + 8 + 32 + 8) {
        continue;
      }

      // 解析账户数据
      let offset = 8; // 跳过 discriminator
      
      // 读取字符串长度
      const strLen = accountData.readUInt32LE(offset);
      offset += 4;
      
      // 检查字符串长度是否合理
      if (strLen > 200 || strLen + offset > accountData.length) {
        continue;
      }
      
      // 读取字符串
      const storedString = accountData.slice(offset, offset + strLen).toString('utf8');
      offset += strLen;
      
      // 读取 signature (16 bytes)
      const storedSignature = accountData.slice(offset, offset + 16);
      const storedSignatureHex = storedSignature.toString('hex');
      
      // 比较签名
      if (storedSignatureHex === signatureHex) {
        // 找到匹配的记录
        offset += 16;
        
        // 读取 timestamp
        const timestamp = Number(accountData.readBigInt64LE(offset));
        offset += 8;
        
        // 读取 owner
        const owner = new anchor.web3.PublicKey(accountData.slice(offset, offset + 32));
        offset += 32;
        
        // 读取 cost_lamports
        const costLamports = Number(accountData.readBigUInt64LE(offset));

        const response: ApiResponse<QueryResult> = {
          success: true,
          code: 0,
          message: "查询成功，记录已上链",
          data: {
            exists: true,
            recordAddress: account.pubkey.toBase58(),
            signature: signatureHex,
            timestamp: timestamp,
            owner: owner.toBase58(),
            costLamports: costLamports,
            costSol: costLamports / anchor.web3.LAMPORTS_PER_SOL,
            originalString: storedString,
          },
        };

        return res.status(200).json(response);
      }
    }

    // 未找到匹配的记录（虽然缓存中有，但链上可能已被清理）
    const response: ApiResponse<QueryResult> = {
      success: true,
      code: 0,
      message: "未找到上链记录（缓存过期）",
      data: {
        exists: false,
        originalString: originalString,
        signature: signatureHex,
      },
    };

    return res.status(200).json(response);
  } catch (error: any) {
    console.error("查询失败:", error);

    const response: ApiResponse = {
      success: false,
      code: 500,
      message: "服务器内部错误",
      error: error.message || String(error),
    };

    return res.status(500).json(response);
  }
});

/**
 * GET /api/record/:address - 通过合约地址查询上链记录
 * 
 * 用于客户端验证：通过存储的合约地址查询原始数据，验证 MD5 签名
 */
app.get("/api/record/:address", async (req: Request, res: Response) => {
  try {
    const { address } = req.params;

    if (!address) {
      const response: ApiResponse = {
        success: false,
        code: 400,
        message: "请求参数错误",
        error: "address 参数是必需的",
      };
      return res.status(400).json(response);
    }

    console.log(`[${new Date().toISOString()}] 查询记录，地址: "${address}"`);

    // 解析地址
    let recordAddress: anchor.web3.PublicKey;
    try {
      recordAddress = new anchor.web3.PublicKey(address);
    } catch (e) {
      const response: ApiResponse = {
        success: false,
        code: 400,
        message: "地址格式错误",
        error: "无效的 Solana 地址",
      };
      return res.status(400).json(response);
    }

    // 查询账户数据
    const accountInfo = await provider.connection.getAccountInfo(recordAddress);

    if (accountInfo === null) {
      const response: ApiResponse<QueryResult> = {
        success: true,
        code: 0,
        message: "未找到上链记录",
        data: {
          exists: false,
          recordAddress: address,
        },
      };
      return res.status(200).json(response);
    }

    // 解析账户数据
    const accountData = accountInfo.data;
    
    // 验证数据长度
    if (accountData.length < 8 + 4 + 16 + 8 + 32 + 8) {
      const response: ApiResponse = {
        success: false,
        code: 400,
        message: "账户数据格式错误",
        error: "账户数据长度不足，可能不是有效的存储记录",
      };
      return res.status(400).json(response);
    }
    
    let offset = 8; // 跳过 discriminator
    
    // 读取字符串长度
    const strLen = accountData.readUInt32LE(offset);
    offset += 4;
    
    // 验证字符串长度
    if (strLen > 1000 || strLen + offset > accountData.length - 16 - 8 - 32 - 8) {
      const response: ApiResponse = {
        success: false,
        code: 400,
        message: "账户数据格式错误",
        error: "字符串长度无效",
      };
      return res.status(400).json(response);
    }
    
    // 读取字符串
    const storedString = accountData.slice(offset, offset + strLen).toString('utf8');
    offset += strLen;
    
    // 读取 signature (16 bytes)
    const signatureBytes = accountData.slice(offset, offset + 16);
    const signatureHex = signatureBytes.toString('hex');
    offset += 16;
    
    // 读取 timestamp
    const timestamp = Number(accountData.readBigInt64LE(offset));
    offset += 8;
    
    // 读取 owner
    const owner = new anchor.web3.PublicKey(accountData.slice(offset, offset + 32));
    offset += 32;
    
    // 读取 cost_lamports
    const costLamports = Number(accountData.readBigUInt64LE(offset));

    const response: ApiResponse<QueryResult> = {
      success: true,
      code: 0,
      message: "查询成功，记录已上链",
      data: {
        exists: true,
        recordAddress: address,
        signature: signatureHex,
        timestamp: timestamp,
        owner: owner.toBase58(),
        costLamports: costLamports,
        costSol: costLamports / anchor.web3.LAMPORTS_PER_SOL,
        originalString: storedString,
      },
    };

    return res.status(200).json(response);
  } catch (error: any) {
    console.error("查询失败:", error);

    const response: ApiResponse = {
      success: false,
      code: 500,
      message: "服务器内部错误",
      error: error.message || String(error),
    };

    return res.status(500).json(response);
  }
});

/**
 * GET /api/health - 健康检查
 */
app.get("/api/health", (req: Request, res: Response) => {
  const response = {
    success: true,
    code: 0,
    message: "服务正常运行",
    data: {
      status: "healthy",
      network: provider.connection.rpcEndpoint,
      programId: program.programId.toBase58(),
      payer: payer.publicKey.toBase58(),
      timestamp: new Date().toISOString(),
    },
  };
  return res.status(200).json(response);
});

/**
 * GET /api/address/:data - 获取字符串对应的存储地址
 */
app.get("/api/address/:data", async (req: Request, res: Response) => {
  try {
    const { data } = req.params;

    if (!data) {
      const response: ApiResponse = {
        success: false,
        code: 400,
        message: "请求参数错误",
        error: "data 参数是必需的",
      };
      return res.status(400).json(response);
    }

    // 生成示例地址（实际存储时会生成随机地址）
    const exampleKeypair = anchor.web3.Keypair.generate();

    const response: ApiResponse = {
      success: true,
      code: 0,
      message: "说明：每次存储会生成新的随机地址",
      data: {
        input: data,
        exampleAddress: exampleKeypair.publicKey.toBase58(),
        note: "实际存储地址会在调用 /api/store 时生成并返回",
        programId: program.programId.toBase58(),
      },
    };

    return res.status(200).json(response);
  } catch (error: any) {
    console.error("获取地址失败:", error);

    const response: ApiResponse = {
      success: false,
      code: 500,
      message: "服务器内部错误",
      error: error.message || String(error),
    };

    return res.status(500).json(response);
  }
});

// 启动服务器
app.listen(PORT, () => {
  console.log("========================================");
  console.log("  Solana 字符串上链服务已启动");
  console.log("========================================");
  console.log(`  网络环境: ${NETWORK}`);
  console.log(`  服务地址: http://localhost:${PORT}`);
  console.log(`  Solana RPC: ${provider.connection.rpcEndpoint}`);
  console.log(`  程序 ID: ${program.programId.toBase58()}`);
  console.log(`  支付账户: ${payer.publicKey.toBase58()}`);
  console.log("========================================");
  console.log("  API 端点:");
  console.log(`    POST   /api/store         - 存储字符串上链（Base64编码）`);
  console.log(`    GET    /api/record/:address - 通过合约地址查询上链记录`);
  console.log(`    GET    /api/query/:data   - 通过原始字符串查询上链记录`);
  console.log(`    GET    /api/address/:data - 获取存储地址`);
  console.log(`    GET    /api/health        - 健康检查`);
  console.log("========================================");
  console.log("  环境变量:");
  console.log(`    SOLANA_NETWORK=${NETWORK}`);
  console.log("========================================");
});

export default app;
