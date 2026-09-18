"""Bridge between the on-chain safety layer and the quant pipeline.

CLAUDE.md section 5 defines an anti-rug listener that reacts in a single slot.
hedge_fund_ai_bot.py defines an alpha pipeline that reacts on hourly bars.
This module is the seam between them: it converts on-chain safety signals into
(a) a position-sizing haircut and (b) an execution-mode override.
"""

from dataclasses import dataclass
from enum import Enum


class ThreatLevel(Enum):
    """Severity of the current on-chain picture for a single token."""

    CLEAR = "CLEAR"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"


class ExecutionMode(Enum):
    """How layer 5 is allowed to touch the market."""

    NORMAL = "NORMAL"        # VWAP/TWAP slicing, new exposure permitted
    DEFENSIVE = "DEFENSIVE"  # reduce-only, no new exposure
    EMERGENCY = "EMERGENCY"  # single-block bundle via Jito/Flashbots, full exit


@dataclass
class SafetyState:
    """Snapshot of the anti-rug triggers from CLAUDE.md section 5.

    Populated by the Geyser/WebSocket listener. The three CRITICAL triggers map
    one-to-one onto the documented malicious events.
    """

    lp_removed_or_burned: bool = False      # remove_liquidity / burn_lp
    authority_changed: bool = False         # set_freeze_authority / mint authority
    dev_dump_fraction: float = 0.0          # share of supply dumped in one slot
    holder_concentration: float = 0.0       # largest non-LP wallet share
    pool_age_hours: float = float("inf")

    # CLAUDE.md fixes the dev-dump trigger at >5% of circulating supply per slot.
    DEV_DUMP_CRITICAL: float = 0.05

    ELEVATED_RISK_BAND: float = 0.12

    @property
    def _base_risk_score(self) -> float:
        """Continuous risk from soft signals only. No CRITICAL short-circuit,
        so threat_level can consume it without recursing."""
        score = 0.0
        score += min(self.dev_dump_fraction / self.DEV_DUMP_CRITICAL, 1.0) * 0.25
        score += max(0.0, self.holder_concentration - 0.10) * 0.60
        if self.pool_age_hours < 24.0:
            score += 0.15 * (1.0 - self.pool_age_hours / 24.0)
        return min(score, 1.0)

    @property
    def threat_level(self) -> ThreatLevel:
        # The three hard triggers from CLAUDE.md s5 are non-negotiable.
        if (
            self.lp_removed_or_burned
            or self.authority_changed
            or self.dev_dump_fraction > self.DEV_DUMP_CRITICAL
        ):
            return ThreatLevel.CRITICAL
        # Otherwise the label tracks the same score that drives sizing, so a
        # token can never read CLEAR while carrying more risk than an ELEVATED one.
        if self._base_risk_score > self.ELEVATED_RISK_BAND:
            return ThreatLevel.ELEVATED
        return ThreatLevel.CLEAR

    @property
    def rug_probability(self) -> float:
        """Heuristic P(total loss) over the holding period.

        This is deliberately crude and is the weakest link in the chain: the
        sizing math below is only as good as this number. Replace it with a
        calibrated model fitted on labelled rug outcomes before trusting size.
        """
        if self.threat_level is ThreatLevel.CRITICAL:
            return 1.0
        return self._base_risk_score

    @property
    def execution_mode(self) -> ExecutionMode:
        return {
            ThreatLevel.CRITICAL: ExecutionMode.EMERGENCY,
            ThreatLevel.ELEVATED: ExecutionMode.DEFENSIVE,
            ThreatLevel.CLEAR: ExecutionMode.NORMAL,
        }[self.threat_level]


def survival_adjusted_kelly(win_probability, win_loss_ratio, rug_probability):
    """Kelly fraction with a catastrophic-loss branch folded in.

    The base pipeline uses f* = p - q/r, whose 'loss' branch forfeits the whole
    staked fraction. A rug forfeits the same staked fraction, so the two loss
    branches merge and the closed form survives intact with reweighted
    probabilities:

        p' = (1 - lambda) * p
        q' = lambda + (1 - lambda) * q
        f* = p' - q'/r

    lambda = 0 reproduces the original formula exactly.
    """
    if not 0.0 <= rug_probability <= 1.0:
        raise ValueError(f"rug_probability must be in [0, 1], got {rug_probability}")
    if win_loss_ratio <= 0.0:
        raise ValueError(f"win_loss_ratio must be positive, got {win_loss_ratio}")

    survival = 1.0 - rug_probability
    p_win = survival * win_probability
    p_loss = rug_probability + survival * (1.0 - win_probability)
    return max(0.0, p_win - p_loss / win_loss_ratio)


def max_tolerable_rug_probability(win_probability, win_loss_ratio):
    """Rug probability at which survival-adjusted Kelly first returns zero.

    Above this, no edge in the alpha model justifies holding the token at all.
    """
    edge = win_loss_ratio * win_probability - (1.0 - win_probability)
    if edge <= 0.0:
        return 0.0
    return edge / (1.0 + edge)
