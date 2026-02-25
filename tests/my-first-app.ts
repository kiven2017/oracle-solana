import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { MyFirstApp } from "../target/types/my_first_app";
import { assert } from "chai";

describe("my-first-app - 字符串上链服务", () => {
  // 配置客户端使用本地集群
  anchor.setProvider(anchor.AnchorProvider.env());

  const program = anchor.workspace.myFirstApp as Program<MyFirstApp>;
  const provider = anchor.getProvider();
  const payer = provider.wallet as anchor.Wallet;

  it("成功存储字符串并返回签名和地址", async () => {
    const testString = "Hello Solana! " + Date.now();

    // 获取 PDA 地址
    const [recordPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("string_record"), Buffer.from(testString)],
      program.programId
    );

    console.log("测试字符串:", testString);
    console.log("预期存储地址:", recordPda.toBase58());

    // 调用存储方法
    const tx = await program.methods
      .storeString(testString)
      .accounts({
        record: recordPda,
        payer: payer.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    console.log("交易签名:", tx);

    // 获取存储的记录
    const record = await program.account.stringRecord.fetch(recordPda);

    console.log("存储的记录:");
    console.log("  原始字符串:", record.originalString);
    console.log("  签名:", Buffer.from(record.signature).toString("hex"));
    console.log("  上链时间:", new Date(record.timestamp.toNumber() * 1000).toISOString());
    console.log("  所有者:", record.owner.toBase58());
    console.log("  消耗 SOL:", record.costLamports.toNumber(), "lamports");

    // 验证数据
    assert.equal(record.originalString, testString);
    assert.equal(record.owner.toBase58(), payer.publicKey.toBase58());
    assert.isTrue(record.costLamports.toNumber() > 0);
  });

  it("重复存储相同字符串应该失败", async () => {
    const testString = "Duplicate Test " + Date.now();

    const [recordPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("string_record"), Buffer.from(testString)],
      program.programId
    );

    // 第一次存储 - 应该成功
    await program.methods
      .storeString(testString)
      .accounts({
        record: recordPda,
        payer: payer.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    console.log("第一次存储成功");

    // 第二次存储 - 应该失败
    try {
      await program.methods
        .storeString(testString)
        .accounts({
          record: recordPda,
          payer: payer.publicKey,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .rpc();
      assert.fail("应该抛出重复错误");
    } catch (error: any) {
      console.log("重复存储被阻止，错误信息:", error.message);
      // 错误码 0x0 表示账户已存在（System Program 的错误）
      assert.include(error.message, "custom program error: 0x0");
    }
  });

  it("空字符串应该被拒绝", async () => {
    const testString = "";

    const [recordPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("string_record"), Buffer.from(testString)],
      program.programId
    );

    try {
      await program.methods
        .storeString(testString)
        .accounts({
          record: recordPda,
          payer: payer.publicKey,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .rpc();
      assert.fail("应该抛出空字符串错误");
    } catch (error: any) {
      console.log("空字符串被拒绝，错误信息:", error.message);
      assert.include(error.message, "EmptyString");
    }
  });

  it("获取记录地址", async () => {
    const testString = "Address Test";

    const tx = await program.methods
      .getRecordAddress(testString)
      .accounts({})
      .rpc();

    console.log("获取地址交易:", tx);
  });
});
