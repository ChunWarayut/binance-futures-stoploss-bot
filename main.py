import asyncio
from trading_bot import TradingBot
from loguru import logger
import config
from notifications import NotificationSystem

async def main():
    try:
        notification = NotificationSystem()
        bot = TradingBot()
        logger.info("Starting trading bot...")
        
        # Send notification when bot starts
        await notification.notify(
            "🤖 Trading Bot Started\n"
            f"Trading Pairs: {', '.join(config.TRADING_PAIRS)}\n"
            f"Leverage: {config.LEVERAGE}x\n"
            f"Position Size: {config.POSITION_SIZE} BTC"
        )
        
        await bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 