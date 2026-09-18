import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

from risk_gate import ExecutionMode, SafetyState, survival_adjusted_kelly

class HedgeFundAIBot:
    def __init__(self, portfolio_capital=1000000.0):
        self.capital = portfolio_capital
        self.scaler = StandardScaler()
        # Ridge acts as our proxy prediction engine core
        self.prediction_model = Ridge(alpha=1.0) 
        
    def layer_1_data_ingestion(self):
        """1. INGESTION: Simulates loading direct market feeds and alternative data feeds."""
        np.random.seed(42)
        n_steps = 100
        time_index = pd.date_range("2026-01-01", periods=n_steps, freq="h")
        
        # Simulate Level 2 raw tick aggregates & NLP sentiment extraction
        price_changes = np.random.normal(0, 1, n_steps)
        prices = 100 + np.cumsum(price_changes)
        volumes = np.random.randint(1000, 5000, n_steps)
        sentiment_scores = np.random.uniform(-1, 1, n_steps) + (price_changes * 0.2)
        
        return pd.DataFrame({"price": prices, "volume": volumes, "sentiment": sentiment_scores}, index=time_index)

    def layer_2_feature_engineering(self, raw_data):
        """2. FEATURE ENGINEERING: Translates chaotic raw metrics into clean mathematical features."""
        df = raw_data.copy()
        df['returns'] = df['price'].pct_change()
        df['lagged_returns'] = df['returns'].shift(1)
        df['moving_avg_5'] = df['price'].rolling(window=5).mean()
        df['volatility_5'] = df['returns'].rolling(window=5).std()
        df.dropna(inplace=True)
        return df

    def layer_3_prediction_engine(self, feature_df):
        """3. AI CORE: Trains models and outputs real-time expected alpha returns."""
        feature_cols = ['lagged_returns', 'sentiment', 'volatility_5']
        X = feature_df[feature_cols]
        y = feature_df['returns']
        
        # Scale inputs to remove asset-class volatility bias
        X_scaled = self.scaler.fit_transform(X)
        
        # Train on historical context up to index (t-1) to predict interval (t)
        self.prediction_model.fit(X_scaled[:-1], y.iloc[1:])
        
        # Isolate the newest, incoming real-time feature vector
        latest_feature = self.scaler.transform(X.iloc[[-1]])
        predicted_return = self.prediction_model.predict(latest_feature)[0]
        return predicted_return

    def layer_4_risk_and_optimization(self, predicted_return, safety=None):
        """4. RISK MANAGEMENT: Kelly sizing, haircut by on-chain rug probability."""
        # Dynamic probability assignment driven by AI core output confidence
        win_probability = 0.55 if predicted_return > 0 else 0.45
        win_loss_ratio = 1.5  # Historical average risk reward payload

        # The anti-rug layer contributes a catastrophic-loss branch. With no
        # safety oracle attached this is zero and the classic f* = p - q/r holds.
        rug_probability = safety.rug_probability if safety is not None else 0.0

        # Guardrail circuit breaker: absolute zero-risk limit floor if mathematical edge flips negative
        allocation_fraction = survival_adjusted_kelly(
            win_probability, win_loss_ratio, rug_probability
        )
        allocated_capital = allocation_fraction * self.capital
        return allocated_capital

    def layer_5_execution_routing(self, predicted_return, safe_position_size, safety=None):
        """5. EXECUTION & ROUTING: Direction and size, arbitrated against threat level."""
        alpha_threshold = 0.001
        mode = safety.execution_mode if safety is not None else ExecutionMode.NORMAL

        # A rug lands inside one slot; time-sliced routing cannot outrun it.
        # CLAUDE.md s5 mandates a full exit in a single builder bundle instead.
        if mode is ExecutionMode.EMERGENCY:
            return {
                "Action": "EMERGENCY EXIT - DUMP 100% (JITO/FLASHBOTS BUNDLE)",
                "Target Risk Capital Deployment": "$0.00",
                "AI Alpha Expectation Score": f"{predicted_return:.6f}",
                "Execution Mode": mode.value,
                "Alpha Model Overridden": True,
            }

        if predicted_return > alpha_threshold and safe_position_size > 0:
            if mode is ExecutionMode.DEFENSIVE:
                # Elevated threat: hold what we have, add nothing.
                action = "HOLD POSITION / REDUCE-ONLY (NEW ENTRY BLOCKED)"
                safe_position_size = 0.0
            else:
                action = "EXECUTE ALGORITHMIC BUY ORDER (VWAP ROUTING)"
        elif predicted_return < -alpha_threshold and safe_position_size > 0:
            action = "EXECUTE ALGORITHMIC SELL ORDER (TWAP ROUTING)"
        else:
            action = "HOLD POSITION / REMOVE ACTIVE ORDERS"

        return {
            "Action": action,
            "Target Risk Capital Deployment": f"${safe_position_size:,.2f}",
            "AI Alpha Expectation Score": f"{predicted_return:.6f}",
            "Execution Mode": mode.value,
            "Alpha Model Overridden": False,
        }

    def run_pipeline(self, safety=None):
        """Executes the complete system pipeline synchronously.

        `safety` is the latest SafetyState from the anti-rug listener. It runs on
        a slot cadence in its own task; the pipeline only reads the snapshot. An
        EMERGENCY state must not wait for the next bar - see emergency_exit().
        """
        raw_data = self.layer_1_data_ingestion()
        feature_df = self.layer_2_feature_engineering(raw_data)
        prediction = self.layer_3_prediction_engine(feature_df)
        risk_allocation = self.layer_4_risk_and_optimization(prediction, safety)
        execution_packet = self.layer_5_execution_routing(prediction, risk_allocation, safety)
        return execution_packet

    def emergency_exit(self, safety):
        """Slot-cadence kill switch. Bypasses layers 1-4 entirely.

        The anti-rug listener calls this directly the moment a CRITICAL trigger
        parses. It never touches the Ridge model, because by the next hourly bar
        the liquidity is already gone.
        """
        return self.layer_5_execution_routing(
            predicted_return=0.0, safe_position_size=0.0, safety=safety
        )

# --- Run verification ---
if __name__ == "__main__":
    bot = HedgeFundAIBot(portfolio_capital=1000000.0)
    pipeline_output = bot.run_pipeline()

    for key, value in pipeline_output.items():
        print(f"{key}: {value}")
