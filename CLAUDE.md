
## 5. Anti-Rug & Block-Level Copy Execution Skill
- **Mempool Pre-Execution Listener**: Always implement an async WebSocket or gRPC Geyser stream (via Helius/Triton) to inspect incoming block transactions before they land.
- **Malicious Event Triggers**: Trigger an immediate emergency exit when any of the following instructions are parsed:
  1. `remove_liquidity` or `burn_lp` on the underlying pool.
  2. `set_freeze_authority` or mint authority changes.
  3. Creator/Dev wallet dumping > 5% of circulating supply in a single slot.
- **MEV Validator Routing**: Bypasses public RPC nodes during exits. Fire pre-signed transactions directly to block builders (Jito on Solana, Flashbots on EVM) with dynamic priority tip fees to ensure execution in the same block or ahead of the malicious tx.
- **Hybrid Position Exits**: Maintain standard laddered take-profits (+25%, +50%) during normal trading, but automatically override and dump 100% of holdings in a single bundle upon anti-rug detection.
