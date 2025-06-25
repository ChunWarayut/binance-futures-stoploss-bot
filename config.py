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
TRAILING_STOP_PERCENTAGE = 1.0  # 1% trailing stop
TAKE_PROFIT_PERCENTAGE = 2.0  # 2% take profit

# Notification Settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')  # Discord webhook URL for notifications

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join("logs", "trading_bot.log") 