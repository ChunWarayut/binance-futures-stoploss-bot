from binance.client import Client
from binance.enums import *
import pandas as pd
import numpy as np
from loguru import logger
import config
import asyncio
from notifications import NotificationSystem
import time

class TradingBot:
    def __init__(self):
        self.client = Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        self.notification = NotificationSystem()
        self.setup_logging()
        self.last_heartbeat = time.time()

    def setup_logging(self):
        logger.add(
            config.LOG_FILE,
            rotation="1 day",
            retention="7 days",
            level=config.LOG_LEVEL
        )

    async def initialize(self):
        for symbol in config.TRADING_PAIRS:
            try:
                # Set leverage
                self.client.futures_change_leverage(
                    symbol=symbol,
                    leverage=config.LEVERAGE
                )
                logger.info(f"Set leverage for {symbol} to {config.LEVERAGE}x")
                
                # Get current price
                ticker = self.client.futures_symbol_ticker(symbol=symbol)
                logger.info(f"Current price for {symbol}: {ticker['price']}")
                
                # Send notification for each pair initialization
                await self.notification.notify(
                    f"✅ Initialized {symbol}\n"
                    f"Leverage: {config.LEVERAGE}x\n"
                    f"Current Price: {ticker['price']}"
                )
            except Exception as e:
                logger.error(f"Failed to set leverage for {symbol}: {str(e)}")
                await self.notification.notify(f"❌ Failed to initialize {symbol}: {str(e)}")

    def send_heartbeat(self):
        current_time = time.time()
        if current_time - self.last_heartbeat >= 60:  # Send heartbeat every minute
            logger.info("Bot is running and monitoring markets...")
            self.last_heartbeat = current_time

    async def check_market_conditions(self, symbol):
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            logger.info(f"Monitoring {symbol} - Current price: {current_price}")
            
            # Add your trading strategy logic here
            # For example:
            # if some_condition:
            #     await self.place_order(symbol, SIDE_BUY, quantity)
            
        except Exception as e:
            logger.error(f"Error checking market conditions for {symbol}: {str(e)}")

    async def place_order(self, symbol, side, quantity):
        """Place order without TP/SL management (handled by separate system)"""
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            entry_price = float(order['avgPrice'])
            position_side = "LONG" if side == SIDE_BUY else "SHORT"
            
            await self.notification.notify(
                f"📈 New {position_side} position opened for {symbol}\n"
                f"Entry Price: {entry_price}\n"
                f"Quantity: {quantity}\n"
                f"💡 TP/SL managed by separate system"
            )
            
            logger.info(f"Order placed successfully: {order}")
            return order
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            await self.notification.notify(f"❌ Failed to place order: {str(e)}")
            return None

    async def run(self):
        await self.initialize()
        await self.notification.notify(
            "🎯 Trading Bot Active (Pure Trading)\n"
            "💡 TP/SL managed by separate system\n"
            "📊 Monitoring market conditions..."
        )
        
        while True:
            try:
                self.send_heartbeat()
                
                for symbol in config.TRADING_PAIRS:
                    await self.check_market_conditions(symbol)
                    
                await asyncio.sleep(30)  # Check every 30 seconds (reduced frequency)
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await self.notification.notify(f"❌ Error in main loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying 