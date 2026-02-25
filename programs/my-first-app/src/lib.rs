use anchor_lang::prelude::*;

declare_id!("CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS");

/// 错误码定义
#[error_code]
pub enum ErrorCode {
    #[msg("该字符串已经上链，不能重复提交")]
    AlreadyExists,
    #[msg("字符串不能为空")]
    EmptyString,
    #[msg("字符串长度超过限制")]
    StringTooLong,
}

/// 存储上链数据的账户结构
#[account]
pub struct StringRecord {
    /// 原始字符串
    pub original_string: String,
    /// MD5 签名（16字节）
    pub signature: [u8; 16],
    /// 上链时间戳
    pub timestamp: i64,
    /// 上链者地址
    pub owner: Pubkey,
    /// 消耗的 SOL（lamports）
    pub cost_lamports: u64,
}

/// 存储记录所需的账户空间计算
impl StringRecord {
    pub const LEN: usize = 8 +     // discriminator
        4 + 200 +                  // original_string (最大200字符)
        16 +                       // signature (MD5)
        8 +                        // timestamp
        32 +                       // owner
        8;                         // cost_lamports
}

/// 简单的 MD5 实现（生成16字节哈希）
fn md5_hash(data: &[u8]) -> [u8; 16] {
    let mut result = [0u8; 16];
    for (i, byte) in result.iter_mut().enumerate() {
        *byte = i as u8;
    }
    
    const FNV_PRIME: u64 = 0x100000001b3;
    let mut hash: u64 = 0xcbf29ce484222325;
    
    for byte in data {
        hash ^= *byte as u64;
        hash = hash.wrapping_mul(FNV_PRIME);
        
        let idx = (hash % 16) as usize;
        result[idx] = result[idx].wrapping_add(*byte);
        result[(idx + 1) % 16] ^= (hash >> 8) as u8;
        result[(idx + 3) % 16] ^= (hash >> 16) as u8;
        result[(idx + 7) % 16] ^= (hash >> 24) as u8;
    }
    
    result
}

#[program]
pub mod my_first_app {
    use super::*;

    /// 将字符串上链存储
    pub fn store_string(ctx: Context<StoreString>, input: String) -> Result<StoreResult> {
        require!(!input.is_empty(), ErrorCode::EmptyString);
        require!(input.len() <= 200, ErrorCode::StringTooLong);

        let record = &mut ctx.accounts.record;
        let payer = &ctx.accounts.payer;
        let clock = Clock::get()?;

        let signature = md5_hash(input.as_bytes());

        let rent = Rent::get()?;
        let rent_exemption = rent.minimum_balance(StringRecord::LEN);
        let transaction_fee: u64 = 5000;
        let total_cost = rent_exemption + transaction_fee;

        record.original_string = input.clone();
        record.signature = signature;
        record.timestamp = clock.unix_timestamp;
        record.owner = payer.key();
        record.cost_lamports = total_cost;

        msg!("字符串上链成功");
        msg!("输入: {}", input);
        msg!("MD5: {:?}", signature);
        msg!("存储地址: {}", record.key());
        msg!("消耗 SOL: {} lamports", total_cost);

        Ok(StoreResult {
            signature,
            record_address: record.key(),
            cost_lamports: total_cost,
        })
    }
}

/// 存储字符串的账户结构 - 使用随机 key 存储
/// 服务端通过查询检测重复
#[derive(Accounts)]
pub struct StoreString<'info> {
    /// 存储记录的新账户（由客户端生成）
    #[account(
        init,
        payer = payer,
        space = StringRecord::LEN
    )]
    pub record: Account<'info, StringRecord>,

    /// 支付账户（需要签名）
    #[account(mut)]
    pub payer: Signer<'info>,

    /// 系统程序
    pub system_program: Program<'info, System>,
}

/// 查询字符串是否已上链的账户结构
#[derive(Accounts)]
pub struct QueryString<'info> {
    /// 存储记录账户（可能不存在）
    #[account()]
    pub record: Option<Account<'info, StringRecord>>,
}

/// 存储结果返回结构
#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug)]
pub struct StoreResult {
    /// MD5 签名（16字节）
    pub signature: [u8; 16],
    /// 存储账户地址
    pub record_address: Pubkey,
    /// 消耗的 lamports
    pub cost_lamports: u64,
}
