
## 5. Anti-Rug & Block-Level Copy Execution Skill
- **Mempool Pre-Execution Listener**: Always implement an async WebSocket or gRPC Geyser stream (via Helius/Triton) to inspect incoming block transactions before they land.
- **Malicious Event Triggers**: Trigger an immediate emergency exit when any of the following instructions are parsed:
  1. `remove_liquidity` or `burn_lp` on the underlying pool.
  2. `set_freeze_authority` or mint authority changes.
  3. Creator/Dev wallet dumping > 5% of circulating supply in a single slot.
- **MEV Validator Routing**: Bypasses public RPC nodes during exits. Fire pre-signed transactions directly to block builders (Jito on Solana, Flashbots on EVM) with dynamic priority tip fees to ensure execution in the same block or ahead of the malicious tx.
- **Hybrid Position Exits**: Maintain standard laddered take-profits (+25%, +50%) during normal trading, but automatically override and dump 100% of holdings in a single bundle upon anti-rug detection.

## 6. Layer Composition: How the Alpha Engine and the Anti-Rug Skill Interact
The quant pipeline (`hedge_fund_ai_bot.py`) and the anti-rug skill (section 5) run on
different clocks and must never be chained naively. `risk_gate.py` is the only seam
between them.

- **Never put the safety listener downstream of the prediction engine.** The Ridge core
  in layer 3 runs on a bar cadence; a rug lands in a single slot. The listener runs as an
  independent async task and calls `HedgeFundAIBot.emergency_exit()` directly, bypassing
  layers 1-4. By the next bar the liquidity is already gone.
- **Safety feeds sizing, not signal.** The anti-rug layer produces no alpha. It emits a
  `SafetyState`, whose `rug_probability` enters layer 4 as a catastrophic-loss branch:
  `p' = (1-λ)p`, `q' = λ + (1-λ)q`, `f* = p' - q'/r`. At λ=0 this is exactly the original
  Kelly, so the equity-style path is unaffected.
- **Respect the sizing ceiling.** With p=0.55 and r=1.5 the Kelly fraction reaches zero at
  λ ≈ 27.3%. Past that, no model edge justifies holding the token — do not override.
- **Routing is threat-arbitrated, not alpha-arbitrated.** CLEAR routes VWAP/TWAP.
  ELEVATED goes reduce-only and blocks new entries. CRITICAL discards the model output
  entirely and fires the single-block Jito/Flashbots bundle from section 5. Time-sliced
  routing is the wrong primitive under attack: slicing guarantees only part of the exit
  fills before the pool drains.
- **`rug_probability` is the weak link.** It is currently a hand-tuned heuristic over pool
  age, holder concentration and dev-dump size. The sizing math is only as good as this
  number — fit it on labelled rug outcomes before sizing real capital on it.
- **Keep the threat band monotone.** `threat_level` and `rug_probability` derive from one
  shared `_base_risk_score`, so a token can never report CLEAR while carrying more risk
  than one reporting ELEVATED. Preserve this if you add signals.
