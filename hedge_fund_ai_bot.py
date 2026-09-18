import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

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

    def layer_4_risk_and_optimization(self, predicted_return):
        """4. RISK MANAGEMENT: Calculates optimal position sizing via the Kelly Criterion formula."""
        # Dynamic probability assignment driven by AI core output confidence
        win_probability = 0.55 if predicted_return > 0 else 0.45
        win_loss_ratio = 1.5  # Historical average risk reward payload
        
        # Kelly Criterion: f* = p - (q / r)
        kelly_fraction = win_probability - ((1 - win_probability) / win_loss_ratio)
        
        # Guardrail circuit breaker: absolute zero-risk limit floor if mathematical edge flips negative
        allocation_fraction = max(0.0, kelly_fraction)
        allocated_capital = allocation_fraction * self.capital
        return allocated_capital

    def layer_5_execution_routing(self, predicted_return, safe_position_size):
        """5. EXECUTION & ROUTING: Determines the transaction direction and deployment size."""
        alpha_threshold = 0.001
        
        if predicted_return > alpha_threshold and safe_position_size > 0:
            action = "EXECUTE ALGORITHMIC BUY ORDER (VWAP ROUTING)"
        elif predicted_return < -alpha_threshold and safe_position_size > 0:
            action = "EXECUTE ALGORITHMIC SELL ORDER (TWAP ROUTING)"
        else:
            action = "HOLD POSITION / REMOVE ACTIVE ORDERS"
            
        return {
            "Action": action,
            "Target Risk Capital Deployment": f"${safe_position_size:,.2f}",
            "AI Alpha Expectation Score": f"{predicted_return:.6f}"
        }

    def run_pipeline(self):
        """Executes the complete system pipeline synchronously."""
        raw_data = self.layer_1_data_ingestion()
        feature_df = self.layer_2_feature_engineering(raw_data)
        prediction = self.layer_3_prediction_engine(feature_df)
        risk_allocation = self.layer_4_risk_and_optimization(prediction)
        execution_packet = self.layer_5_execution_routing(prediction, risk_allocation)
        return execution_packet

# --- Run verification ---
bot = HedgeFundAIBot(portfolio_capital=1000000.0)
pipeline_output = bot.run_pipeline()

for key, value in pipeline_output.items():
    print(f"{key}: {value}")
