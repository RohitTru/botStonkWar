from datetime import datetime
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class TradeRecommendationMySQL:
    def __init__(self, engine):
        self.engine = engine
        self._ensure_tables()

    def _ensure_tables(self):
        with self.engine.connect() as conn:
            # Create trade recommendations table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trade_recommendations (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    action VARCHAR(10) NOT NULL,
                    confidence FLOAT,
                    reasoning TEXT,
                    timeframe VARCHAR(20),
                    metadata JSON,
                    created_at TIMESTAMP,
                    strategy_name VARCHAR(50),
                    trade_time TIMESTAMP,
                    live_price FLOAT,
                    live_change_percent FLOAT,
                    live_volume BIGINT,
                    UNIQUE KEY unique_trade (symbol, action, strategy_name, created_at)
                )
            """))

            # Create strategy activation table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS strategy_activation (
                    strategy_name VARCHAR(50) PRIMARY KEY,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_run TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()

    def get_strategy_activation(self, strategy_name):
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT is_active FROM strategy_activation WHERE strategy_name = :name"),
                {"name": strategy_name}
            ).fetchone()
            return bool(result[0]) if result else True

    def set_strategy_activation(self, strategy_name, is_active):
        with self.engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO strategy_activation (strategy_name, is_active, last_run)
                    VALUES (:name, :active, NOW())
                    ON DUPLICATE KEY UPDATE 
                        is_active = :active,
                        last_run = NOW()
                """),
                {"name": strategy_name, "active": is_active}
            )
            conn.commit()

    def get_all_strategy_activation(self):
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT strategy_name, is_active FROM strategy_activation"))
            return {row[0]: bool(row[1]) for row in result}

    def insert(self, rec: dict):
        with self.engine.connect() as conn:
            try:
                conn.execute(
                    text("""
                        INSERT IGNORE INTO trade_recommendations
                        (symbol, action, confidence, reasoning, timeframe, metadata,
                         created_at, strategy_name, trade_time, live_price,
                         live_change_percent, live_volume)
                        VALUES
                        (:symbol, :action, :confidence, :reasoning, :timeframe, :metadata,
                         :created_at, :strategy_name, :trade_time, :live_price,
                         :live_change_percent, :live_volume)
                    """),
                    {
                        "symbol": rec['symbol'],
                        "action": rec['action'],
                        "confidence": rec['confidence'],
                        "reasoning": rec['reasoning'],
                        "timeframe": rec['timeframe'],
                        "metadata": json.dumps(rec.get('metadata', {})),
                        "created_at": rec.get('created_at'),
                        "strategy_name": rec.get('strategy_name'),
                        "trade_time": rec.get('trade_time'),
                        "live_price": rec['metadata'].get('live_data', {}).get('price'),
                        "live_change_percent": rec['metadata'].get('live_data', {}).get('change_percent'),
                        "live_volume": rec['metadata'].get('live_data', {}).get('volume')
                    }
                )
                conn.commit()
            except Exception as e:
                print(f"[MySQL] Error inserting trade recommendation: {e}")

    def fetch_all(self):
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM trade_recommendations ORDER BY created_at DESC")
            )
            recommendations = []
            for row in result:
                rec = dict(row._mapping)
                # Parse metadata JSON
                if rec.get('metadata'):
                    try:
                        rec['metadata'] = json.loads(rec['metadata'])
                    except Exception:
                        rec['metadata'] = {}
                recommendations.append(rec)
            return recommendations

    def clear_all(self):
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM trade_recommendations"))
            conn.commit()

    def update_live_data(self, symbol, action, strategy_name, created_at, live_data):
        with self.engine.connect() as conn:
            try:
                conn.execute(
                    text("""
                        UPDATE trade_recommendations
                        SET live_price = :price,
                            live_change_percent = :change,
                            live_volume = :volume
                        WHERE symbol = :symbol 
                          AND action = :action 
                          AND strategy_name = :strategy 
                          AND created_at = :created_at
                    """),
                    {
                        "price": live_data.get('price'),
                        "change": live_data.get('change_percent'),
                        "volume": live_data.get('volume'),
                        "symbol": symbol,
                        "action": action,
                        "strategy": strategy_name,
                        "created_at": created_at
                    }
                )
                conn.commit()
            except Exception as e:
                print(f"[MySQL] Error updating live data: {e}") 