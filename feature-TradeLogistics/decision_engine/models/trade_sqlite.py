import sqlite3
import os
import json
from datetime import datetime

SQLITE_PATH = os.getenv('TRADE_SQLITE_PATH', 'trade_recommendations.sqlite')

class TradeRecommendationSQLite:
    def __init__(self, db_path=SQLITE_PATH):
        self.db_path = db_path
        self._ensure_table()
        self._ensure_strategy_activation_table()

    def _ensure_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trade_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL,
                    reasoning TEXT,
                    timeframe TEXT,
                    metadata TEXT,
                    created_at TEXT,
                    strategy_name TEXT,
                    trade_time TEXT,
                    live_price REAL,
                    live_change_percent REAL,
                    live_volume INTEGER,
                    UNIQUE(symbol, action, strategy_name, created_at)
                )
            ''')
            conn.commit()

    def _ensure_strategy_activation_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS strategy_activation (
                    strategy_name TEXT PRIMARY KEY,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            conn.commit()

    def get_strategy_activation(self, strategy_name):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT is_active FROM strategy_activation WHERE strategy_name = ?', (strategy_name,))
            row = cur.fetchone()
            if row is not None:
                return bool(row[0])
            return True  # Default to active if not set

    def set_strategy_activation(self, strategy_name, is_active):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO strategy_activation (strategy_name, is_active)
                VALUES (?, ?)
                ON CONFLICT(strategy_name) DO UPDATE SET is_active=excluded.is_active
            ''', (strategy_name, int(is_active)))
            conn.commit()

    def get_all_strategy_activation(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT strategy_name, is_active FROM strategy_activation')
            return {row[0]: bool(row[1]) for row in cur.fetchall()}

    def insert(self, rec: dict):
        # Only insert if not duplicate (by symbol, action, strategy, created_at)
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO trade_recommendations
                    (symbol, action, confidence, reasoning, timeframe, metadata, created_at, strategy_name, trade_time, live_price, live_change_percent, live_volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rec['symbol'],
                    rec['action'],
                    rec['confidence'],
                    rec['reasoning'],
                    rec['timeframe'],
                    json.dumps(rec.get('metadata', {})),
                    rec.get('created_at'),
                    rec.get('strategy_name'),
                    rec.get('trade_time'),
                    rec['metadata'].get('live_data', {}).get('price'),
                    rec['metadata'].get('live_data', {}).get('change_percent'),
                    rec['metadata'].get('live_data', {}).get('volume'),
                ))
                conn.commit()
            except Exception as e:
                print(f"[SQLite] Error inserting trade recommendation: {e}")

    def fetch_all(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM trade_recommendations ORDER BY created_at DESC')
            cols = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                rec = dict(zip(cols, row))
                # Parse metadata JSON
                if rec.get('metadata'):
                    try:
                        rec['metadata'] = json.loads(rec['metadata'])
                    except Exception:
                        rec['metadata'] = {}
                results.append(rec)
            return results

    def clear_all(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM trade_recommendations')
            conn.commit()

    def update_live_data(self, symbol, action, strategy_name, created_at, live_data):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    UPDATE trade_recommendations
                    SET live_price = ?, live_change_percent = ?, live_volume = ?
                    WHERE symbol = ? AND action = ? AND strategy_name = ? AND created_at = ?
                ''', (
                    live_data.get('price'),
                    live_data.get('change_percent'),
                    live_data.get('volume'),
                    symbol, action, strategy_name, created_at
                ))
                conn.commit()
            except Exception as e:
                print(f"[SQLite] Error updating live data: {e}") 