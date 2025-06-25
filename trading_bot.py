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
        self.active_trades = {}
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

    def calculate_trailing_stop(self, entry_price, current_price, position_side):
        if position_side == "LONG":
            return current_price * (1 - config.TRAILING_STOP_PERCENTAGE / 100)
        else:
            return current_price * (1 + config.TRAILING_STOP_PERCENTAGE / 100)

    async def place_order(self, symbol, side, quantity):
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            entry_price = float(order['avgPrice'])
            position_side = "LONG" if side == SIDE_BUY else "SHORT"
            
            self.active_trades[symbol] = {
                'entry_price': entry_price,
                'position_side': position_side,
                'quantity': quantity,
                'trailing_stop': self.calculate_trailing_stop(
                    entry_price,
                    entry_price,
                    position_side
                )
            }
            
            await self.notification.notify(
                f"New {position_side} position opened for {symbol}\n"
                f"Entry Price: {entry_price}\n"
                f"Quantity: {quantity}"
            )
            
            logger.info(f"Order placed successfully: {order}")
            return order
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            await self.notification.notify(f"Failed to place order: {str(e)}")
            return None

    async def check_trailing_stop(self, symbol):
        if symbol not in self.active_trades:
            return

        trade = self.active_trades[symbol]
        current_price = float(self.client.futures_symbol_ticker(symbol=symbol)['price'])
        
        new_trailing_stop = self.calculate_trailing_stop(
            trade['entry_price'],
            current_price,
            trade['position_side']
        )

        # Update trailing stop if price moved in favorable direction
        if trade['position_side'] == "LONG" and new_trailing_stop > trade['trailing_stop']:
            trade['trailing_stop'] = new_trailing_stop
        elif trade['position_side'] == "SHORT" and new_trailing_stop < trade['trailing_stop']:
            trade['trailing_stop'] = new_trailing_stop

        # Check if trailing stop is hit
        if (trade['position_side'] == "LONG" and current_price <= trade['trailing_stop']) or \
           (trade['position_side'] == "SHORT" and current_price >= trade['trailing_stop']):
            await self.close_position(symbol)

    async def close_position(self, symbol):
        try:
            trade = self.active_trades[symbol]
            side = SIDE_SELL if trade['position_side'] == "LONG" else SIDE_BUY
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=trade['quantity']
            )
            
            current_price = float(order['avgPrice'])
            pnl = (current_price - trade['entry_price']) * trade['quantity']
            if trade['position_side'] == "SHORT":
                pnl = -pnl
                
            await self.notification.notify(
                f"Position closed for {symbol}\n"
                f"Exit Price: {current_price}\n"
                f"P&L: {pnl:.2f} USDT"
            )
            
            del self.active_trades[symbol]
            logger.info(f"Position closed successfully: {order}")
        except Exception as e:
            logger.error(f"Failed to close position: {str(e)}")
            await self.notification.notify(f"Failed to close position: {str(e)}")

    async def run(self):
        await self.initialize()
        while True:
            try:
                self.send_heartbeat()
                
                for symbol in config.TRADING_PAIRS:
                    await self.check_market_conditions(symbol)
                    await self.check_trailing_stop(symbol)
                    
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await self.notification.notify(f"Error in main loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying 