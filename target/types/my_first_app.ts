/**
 * Program IDL in camelCase format in order to be used in JS/TS.
 *
 * Note that this is only a type helper and is not the actual IDL. The original
 * IDL can be found at `target/idl/my_first_app.json`.
 */
export type MyFirstApp = {
  "address": "CaFmnYF44xfY9Ed95m5ydzc2VS8uNGwmFwDmC6YYnmdS",
  "metadata": {
    "name": "myFirstApp",
    "version": "0.1.0",
    "spec": "0.1.0",
    "description": "Created with Anchor"
  },
  "instructions": [
    {
      "name": "storeString",
      "docs": [
        "将字符串上链存储"
      ],
      "discriminator": [
        103,
        6,
        3,
        225,
        166,
        148,
        155,
        166
      ],
      "accounts": [
        {
          "name": "record",
          "docs": [
            "存储记录的新账户（由客户端生成）"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "payer",
          "docs": [
            "支付账户（需要签名）"
          ],
          "writable": true,
          "signer": true
        },
        {
          "name": "systemProgram",
          "docs": [
            "系统程序"
          ],
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "input",
          "type": "string"
        }
      ],
      "returns": {
        "defined": {
          "name": "storeResult"
        }
      }
    }
  ],
  "accounts": [
    {
      "name": "stringRecord",
      "discriminator": [
        72,
        85,
        57,
        84,
        139,
        0,
        181,
        63
      ]
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "alreadyExists",
      "msg": "该字符串已经上链，不能重复提交"
    },
    {
      "code": 6001,
      "name": "emptyString",
      "msg": ""
    },
    {
      "code": 6002,
      "name": "stringTooLong",
      "msg": ""
    }
  ],
  "types": [
    {
      "name": "storeResult",
      "docs": [
        "存储结果返回结构"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "signature",
            "docs": [
              "MD5 签名（16字节）"
            ],
            "type": {
              "array": [
                "u8",
                16
              ]
            }
          },
          {
            "name": "recordAddress",
            "docs": [
              "存储账户地址"
            ],
            "type": "pubkey"
          },
          {
            "name": "costLamports",
            "docs": [
              "消耗的 lamports"
            ],
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "stringRecord",
      "docs": [
        "存储上链数据的账户结构"
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "originalString",
            "docs": [
              "原始字符串"
            ],
            "type": "string"
          },
          {
            "name": "signature",
            "docs": [
              "MD5 签名（16字节）"
            ],
            "type": {
              "array": [
                "u8",
                16
              ]
            }
          },
          {
            "name": "timestamp",
            "docs": [
              "上链时间戳"
            ],
            "type": "i64"
          },
          {
            "name": "owner",
            "docs": [
              "上链者地址"
            ],
            "type": "pubkey"
          },
          {
            "name": "costLamports",
            "docs": [
              "消耗的 SOL（lamports）"
            ],
            "type": "u64"
          }
        ]
      }
    }
  ]
};
