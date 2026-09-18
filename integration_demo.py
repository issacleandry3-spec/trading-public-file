"""Shows the anti-rug layer and the alpha pipeline arbitrating a single token."""

from hedge_fund_ai_bot import HedgeFundAIBot
from risk_gate import SafetyState, max_tolerable_rug_probability

SCENARIOS = [
    ("Blue-chip pair, nothing on chain",
     SafetyState(pool_age_hours=8760.0)),
    ("Fresh pool, 6h old, concentrated holder",
     SafetyState(pool_age_hours=6.0, holder_concentration=0.22)),
    ("Dev offloading 3% in a slot (ELEVATED)",
     SafetyState(pool_age_hours=48.0, dev_dump_fraction=0.03)),
    ("Dev dumps 7% in one slot (CRITICAL)",
     SafetyState(pool_age_hours=48.0, dev_dump_fraction=0.07)),
    ("set_freeze_authority observed (CRITICAL)",
     SafetyState(pool_age_hours=720.0, authority_changed=True)),
    ("remove_liquidity observed (CRITICAL)",
     SafetyState(pool_age_hours=720.0, lp_removed_or_burned=True)),
]


def main():
    bot = HedgeFundAIBot(portfolio_capital=1_000_000.0)
    ceiling = max_tolerable_rug_probability(0.55, 1.5)
    print(f"Kelly hits zero at rug probability {ceiling:.1%} "
          f"(p=0.55, r=1.5) -- above this, no alpha justifies the position.\n")
    print(f"{'scenario':<42} {'threat':<9} {'P(rug)':>7} {'deploy':>13}  action")
    print("-" * 118)

    for label, safety in SCENARIOS:
        out = bot.run_pipeline(safety=safety)
        print(f"{label:<42} {safety.threat_level.value:<9} "
              f"{safety.rug_probability:>6.1%} {out['Target Risk Capital Deployment']:>13}  "
              f"{out['Action']}")

    print("\n-- slot-cadence kill switch (bypasses layers 1-4) --")
    packet = bot.emergency_exit(SafetyState(lp_removed_or_burned=True))
    for k, v in packet.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
