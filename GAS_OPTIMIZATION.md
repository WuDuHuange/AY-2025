**合约 Gas 优化报告 — Weixin / Store_Money**

日期：2025-12-15

目的
## Contract Gas Optimization Report — Weixin / Store_Money

Date: 2025-12-15

## Purpose

- Perform a static review of the two contracts in the repository (`weixin` and `store_money`), identify gas-intensive operations, and provide actionable optimization suggestions with example implementations.

## Overview (current state)

- Contract 1: weixin
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

- Contract 2: store_money
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

## Main issues and optimization directions (summary)

- Unnecessary storage writes: Each `SSTORE` is expensive (especially the first write to a new storage slot). These contracts write records directly to state (three state variables). If the data is only needed for off-chain inspection, using events is more appropriate and cheaper.
- Variable layout not optimized: Declaration order and types don't consider storage packing, which can consume more slots.
- Visibility and function types: Using `public` instead of `external` (for external calls `external` can be slightly cheaper); impact is limited for simple types.
- Not using `payable` / `msg.value`: `store_money` accepts `amount` as a function parameter instead of using `msg.value`, which can cause front-end/back-end inconsistencies.
- Debug imports like `hardhat/console.sol` increase bytecode size (use only for testing; remove before deployment).

## Specific suggestions and example implementations

1) If you only need to log a record for off-chain viewing → use an event (recommended)

- Rationale: Emitting an event typically costs much less gas than writing to storage. Events are stored in logs and are easy to query off-chain.

Example (Weixin — use events)
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

Benefits: No storage usage; cheaper deployment and calls; indexed fields allow efficient log filtering.

2) If you must persist the "latest" value but want to reduce slot usage → pack variables and narrow types

- Pack `address` with a suitably sized `uint` to reduce slot usage (for example change `amount` to `uint96` to pack with an address).

Example (Weixin — packing)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract WeixinPacked {
    address public payer;   // 20 bytes
    uint96  public amount;  // 12 bytes -> packed in same slot with payer
    address public payee;   // separate slot

    event TransferRecorded(address indexed payer, address indexed payee, uint96 amount);

    function transfer_money(address payer_input, address payee_input, uint96 amount_input) external {
        payer = payer_input;
        amount = amount_input;
        payee = payee_input;
        emit TransferRecorded(payer_input, payee_input, amount_input);
    }
}
```

Note: Ensure `amount` max value fits within `2^96-1`.

3) For `store_money`: use a `mapping` + `msg.value` (if the contract handles actual ETH)

- Replace the single `customer` overwrite with `mapping(address => uint256) balance;` to support multiple users and a more appropriate data model. Use `msg.value` instead of passing amounts from the caller to avoid unit/UX mismatches.

Example (StoreMoney — mapping + payable)
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

4) Other general suggestions

- Enable the Solidity optimizer during deployment (Hardhat/Foundry settings), for example:
```js
// hardhat.config.js
solidity: {
  version: "0.8.20",
  settings: { optimizer: { enabled: true, runs: 200 } }
}
```
- Remove debugging imports like `console.sol` before deployment to reduce bytecode size.
- Batch frequent writes within a single transaction where possible instead of multiple separate writes.
- Use `indexed` fields in events for better off-chain querying.

## Quantification and verification plan (how to measure savings)
1. Initialize a local Hardhat (or Foundry) project and place the original and optimized contracts in `contracts/`.
2. Write small test scripts (JS/TS or Foundry tests) to measure:
   - deployment gas
   - gas for a single `transfer_money` / `deposit_money` transaction
3. Use `hardhat-gas-reporter` or Foundry's reporting tools to generate comparison tables.

Example commands (Hardhat)
```bash
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox hardhat-gas-reporter
npx hardhat # init
# put the two contracts in contracts/ and write tests/ to compare
npx hardhat test
```

## Expected effects (estimated)

- Changing a record from storage writes to events: per-transaction gas may drop by several thousand to tens of thousands of gas depending on number of fields and whether it was the first write to a slot.
- Variable packing can reduce the number of slots and first-write costs; savings depend on contract complexity (typically saves the cost of a few slot writes).
- Using a mapping instead of overwriting a single variable makes sense for multi-user scenarios; it may not save gas in single-user cases but improves correctness and data modeling.

        pragma solidity ^0.8.0;

        contract WeixinOptimized {
            event TransferRecorded(address indexed payer, address indexed payee, uint256 amount);

            function transfer_money(address payer_input, address payee_input, uint256 amount_input) external {
                emit TransferRecorded(payer_input, payee_input, amount_input);
            }
        }
        ```

        Benefits: No storage usage; cheaper deployment and calls; indexed fields allow efficient log filtering.

        2) If you must persist the "latest" value but want to reduce slot usage → pack variables and narrow types

        - Pack `address` with a suitably sized `uint` to reduce slot usage (for example change `amount` to `uint96` to pack with an address).

        Example (Weixin — packing)
        ```solidity
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.0;

        contract WeixinPacked {
            address public payer;   // 20 bytes
            uint96  public amount;  // 12 bytes -> packed in same slot with payer
            address public payee;   // separate slot

            event TransferRecorded(address indexed payer, address indexed payee, uint96 amount);

            function transfer_money(address payer_input, address payee_input, uint96 amount_input) external {
                payer = payer_input;
                amount = amount_input;
                payee = payee_input;
                emit TransferRecorded(payer_input, payee_input, amount_input);
            }
        }
        ```

        Note: Ensure `amount` max value fits within `2^96-1`.

        3) For `store_money`: use a `mapping` + `msg.value` (if the contract handles actual ETH)

        - Replace the single `customer` overwrite with `mapping(address => uint256) balance;` to support multiple users and a more appropriate data model. Use `msg.value` instead of passing amounts from the caller to avoid unit/UX mismatches.

        Example (StoreMoney — mapping + payable)
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

        4) Other general suggestions

        - Enable the Solidity optimizer during deployment (Hardhat/Foundry settings), for example:
        ```js
        // hardhat.config.js
        solidity: {
          version: "0.8.20",
          settings: { optimizer: { enabled: true, runs: 200 } }
        }
        ```
        - Remove debugging imports like `console.sol` before deployment to reduce bytecode size.
        - Batch frequent writes within a single transaction where possible instead of multiple separate writes.
        - Use `indexed` fields in events for better off-chain querying.

        ## Quantification and verification plan (how to measure savings)
        1. Initialize a local Hardhat (or Foundry) project and place the original and optimized contracts in `contracts/`.
        2. Write small test scripts (JS/TS or Foundry tests) to measure:
           - deployment gas
           - gas for a single `transfer_money` / `deposit_money` transaction
        3. Use `hardhat-gas-reporter` or Foundry's reporting tools to generate comparison tables.

        Example commands (Hardhat)
        ```bash
        npm init -y
        npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox hardhat-gas-reporter
        npx hardhat # init
        # put the two contracts in contracts/ and write tests/ to compare
        npx hardhat test
        ```

        ## Expected effects (estimated)

        - Changing a record from storage writes to events: per-transaction gas may drop by several thousand to tens of thousands of gas depending on number of fields and whether it was the first write to a slot.
        - Variable packing can reduce the number of slots and first-write costs; savings depend on contract complexity (typically saves the cost of a few slot writes).
        - Using a mapping instead of overwriting a single variable makes sense for multi-user scenarios; it may not save gas in single-user cases but improves correctness and data modeling.
