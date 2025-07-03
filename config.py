import os
from dotenv import load_dotenv

load_dotenv()

# Binance API Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Trading Parameters
TRADING_PAIRS = [
    'BTCUSDT',    # Bitcoin - คู่เงินหลักที่มีความเสถียร
    'ETHUSDT',    # Ethereum - คู่เงินหลักที่มีความเสถียร
    'BNBUSDT',    # Binance Coin - Volume สูง
    'SOLUSDT',    # Solana - Volume สูง, DeFi
    'XRPUSDT',    # Ripple - Volume สูง
    'DOGEUSDT',   # Dogecoin - ความผันผวนสูง
    'AVAXUSDT',   # Avalanche - ความผันผวนปานกลาง
    'ADAUSDT',    # Cardano - ความเสถียรปานกลาง
    'DOTUSDT',    # Polkadot - ความเสถียร
    'LINKUSDT'    # Chainlink - Volume สูง, ความเสถียร
]
LEVERAGE = 5  # Default leverage
POSITION_SIZE = 0.01  # Position size in BTC
TRAILING_STOP_PERCENTAGE = 0.001  # 0.1% ultra-tight trailing
TAKE_PROFIT_PERCENTAGE = 2.0  # 2% take profit

# Enhanced Stop Loss Configuration (optimized settings)
INITIAL_STOP_PERCENTAGE = 0.50  # 50% initial stop loss
PROFIT_PROTECTION_PERCENTAGE = 0.005  # 0.5% profit protection threshold
AGGRESSIVE_TRAILING_AFTER = 0.01  # Aggressive trailing after 1% profit
BREAKEVEN_BUFFER = 0.002  # 0.2% buffer above breakeven
MIN_STOP_DISTANCE = 0.001  # 0.1% minimum stop distance
ATR_MULTIPLIER = 1.0  # ATR multiplier for initial stops (reduced from default)
RISK_PERCENTAGE = 0.015  # 1.5% risk per trade (reduced from 2%)

# Discord Notification Settings
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')  # Discord webhook URL for notifications

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join("logs", "trading_bot.log") 