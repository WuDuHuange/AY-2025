**合约 Gas 优化报告 — Weixin / Store_Money**

日期：2025-12-15

目的
- 对仓库中的两个合约（`weixin` 与 `store_money`）进行静态审查，指出高消耗操作并给出可执行的优化建议与示例实现。

概览（现状）
- 合约 1: weixin
```solidity
contract weixin{
    address payer;
    address payee;
    uint amount;
    function transfer_money(address payer_input, address payee_input,uint amount_input) public{
        payer = payer_input;
        payee = payee_input;
        amount = amount_input;
    }

    function transfer_view() public view returns ( address, address, uint){
        return (payer,payee,amount);
    }
}
```
- 合约 2: store_money
```solidity
contract store_money {
    address customer;
    uint amount;

    function deposit_money(address customer_input, uint amount_input)
        public
    {
        customer = customer_input;
        amount = amount_input;
    }

    function deposit_view() public view returns (address, uint) {
        return (customer, amount);
    }
}
```

主要问题与优化方向（总结）
- 不必要地使用 storage 写操作：每次 `SSTORE` 写入都很昂贵（尤其是首次写入新 storage slot）。合约把记录直接写入 state（3 个 state 变量），如果只是用于链下查看，事件（event）更合适且更便宜。
- 变量布局未优化：声明顺序与类型未考虑 storage packing，可能占用更多 slot。
- 可见性与函数类型：使用 `public` 而非 `external`（对外部调用，`external` 通常更省一点 gas）；但对简单类型影响有限。
- 没有使用 `payable` / `msg.value`：`store_money` 接受 amount 作为参数而不是 `msg.value`，容易造成前端/后端不一致。
- 包含 debug 导入 `hardhat/console.sol`：会增加字节码大小（仅测试时使用，部署前应移除）。

具体建议与示例实现

1) 如果只是记录一次“事件”供链下查看 → 使用 event（推荐）
- 原理：写 event 的 gas 成本通常远低于写 storage。事件存到日志，方便链下检索。

示例（Weixin — 事件化）
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract WeixinOptimized {
    event TransferRecorded(address indexed payer, address indexed payee, uint256 amount);

    function transfer_money(address payer_input, address payee_input, uint256 amount_input) external {
        emit TransferRecorded(payer_input, payee_input, amount_input);
    }
}
```
好处：不占用 storage，部署与调用更省 gas；能通过 indexed 字段高效检索日志。

2) 若需保存“当前最新值”但希望降低 slot 数量 → 打包变量并缩小类型
- 将 `address` 与合适的小 `uint` 打包以减少 slot 数量（例如把 `amount` 改为 `uint96` 与 address 一起打包）。

示例（Weixin — 打包）
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract WeixinPacked {
    address public payer;   // 20 bytes
    uint96  public amount;  // 12 bytes -> 打包到同一 slot（与 payer 一起）
    address public payee;   // 单独 slot

    event TransferRecorded(address indexed payer, address indexed payee, uint96 amount);

    function transfer_money(address payer_input, address payee_input, uint96 amount_input) external {
        payer = payer_input;
        amount = amount_input;
        payee = payee_input;
        emit TransferRecorded(payer_input, payee_input, amount_input);
    }
}
```
注意：需确认 `amount` 的最大值不超过 `2^96-1`。

3) 对 `store_money` 的建议：使用 mapping + msg.value（如果合约处理实际以太值）
- 将单一 `customer` 覆盖改为 `mapping(address => uint256) balance;` 支持多用户并降低写槽复杂度；使用 `msg.value` 而不是外部传入的数值参数，避免前端单位错误。

示例（StoreMoney — mapping + payable）
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract StoreMoneyOptimized {
    mapping(address => uint256) public balance;
    event Deposit(address indexed payer, uint256 amount);

    receive() external payable {
        balance[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    function deposit_money() external payable {
        require(msg.value > 0, "no value");
        balance[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    function deposit_view(address customer) external view returns (uint256) {
        return balance[customer];
    }
}
```

4) 其它通用建议
- 在部署时启用 solc optimizer（Hardhat/Foundry 设置），示例：
```js
// hardhat.config.js
solidity: {
  version: "0.8.20",
  settings: { optimizer: { enabled: true, runs: 200 } }
}
```
- 移除 `console.sol` 等调试代码，减少部署字节码大小。
- 对频繁写入的数据尽量合并写入（在一笔 tx 内批量写入而不是多次写）。
- 使用 `indexed` 的 event 字段便于链下检索。

量化与验证方案（如何衡量节省）
1. 在本地初始化 Hardhat（或 Foundry），把原始合约与优化合约作为两个合约文件。
2. 写小测试脚本（JavaScript/TS 或 Foundry test）：测量
   - 部署 gas
   - 执行 `transfer_money` / `deposit_money` 单次交易 gas
3. 使用 `hardhat-gas-reporter` 或 Foundry 自带报告生成对比表。

示例命令（Hardhat）
```bash
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox hardhat-gas-reporter
npx hardhat # init
# 把两个合约放到 contracts/ 下，写 tests/ 对比
npx hardhat test
```

预期效果（经验估计）
- 将单次记录从 storage 写入改为 event：部署后每次记录交易 gas 可能降低数千到上万 gas（取决于字段数量与是否为首次写 slot）。
- 变量打包可减少部署时的 slot 数量和首次写入成本，节省程度依合约复杂度而定（通常节省几个 slot 的写入成本）。
- 使用 mapping 替代单变量覆盖对于多用户场景是功能必要的，但在单用户场景不一定节省 gas；优势在于功能正确性与更合理的数据结构。