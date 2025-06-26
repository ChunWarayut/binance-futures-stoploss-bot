import os
import logging
import time
import yaml
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv
import numpy as np
from cache_manager import CacheManager
from rate_limiter import RateLimiter, RetryHandler

class ConfigManager:
    """Configuration manager for the application"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Config file {self.config_path} not found. Using default config.")
            return self.get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            'api': {'rate_limit_calls_per_second': 10, 'max_retries': 3, 'retry_delay': 1},
            'monitoring': {'normal_interval': 30, 'aggressive_interval': 10, 'retry_interval': 60, 'health_check_interval': 300},
            'stop_loss': {'atr_period': 14, 'atr_multiplier': 2.0, 'risk_percentage': 0.02, 'trailing_stop_percentage': 0.01, 'min_stop_distance': 0.005, 'min_net_profit_to_move_sl': 0.005, 'breakeven_buffer': 0.001, 'mode': 'both'},
            'cache': {'position_cache_ttl': 30, 'price_cache_ttl': 5, 'atr_cache_ttl': 300},
            'logging': {'level': 'INFO', 'max_file_size': '10MB', 'backup_count': 5, 'format': '%(asctime)s - %(levelname)s - %(message)s'},
            'trading': {'max_positions': 10, 'min_position_size': 0.001, 'enable_trailing_stop': True, 'enable_atr_stop': True, 'enable_percentage_stop': True}
        }
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'api.rate_limit_calls_per_second')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value

class BinanceSLManager:
    def __init__(self, config_path: str = 'config.yaml'):
        # Load configuration
        self.config = ConfigManager(config_path)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize cache manager
        self.cache = CacheManager()
        
        # Setup rate limiters
        self.rate_limiter = RateLimiter(self.config.get('api.rate_limit_calls_per_second', 10))
        self.retry_handler = RetryHandler(
            self.config.get('api.max_retries', 3),
            self.config.get('api.retry_delay', 1.0)
        )
        
        # Initialize Binance client
        self.initialize_binance_client()
        
        # Health check
        self.last_health_check = 0
        self.health_check_interval = self.config.get('monitoring.health_check_interval', 300)
        
        logger.info("BinanceSLManager initialized successfully")

    def setup_logging(self):
        """Setup logging configuration"""
        global logger
        
        log_level = getattr(logging, self.config.get('logging.level', 'INFO'))
        log_format = self.config.get('logging.format', '%(asctime)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler('sl_manager.log'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)

    def initialize_binance_client(self):
        """Initialize Binance client with API credentials"""
        load_dotenv()
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret must be set in .env file")
        
        self.client = Client(self.api_key, self.api_secret)
        
        # Cache for symbol info
        self.symbol_info_cache = {}

    @RateLimiter(10)
    @RetryHandler(3, 1.0)
    def get_symbol_info(self, symbol: str):
        """Get symbol information including price precision"""
        if symbol in self.symbol_info_cache:
            return self.symbol_info_cache[symbol]
        
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    self.symbol_info_cache[symbol] = s
                    return s
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None

    def round_price(self, symbol: str, price: float) -> float:
        """Round price to the correct precision for the symbol"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                # Default precision if symbol info not available
                return round(price, 2)
            
            # Get price precision from symbol info
            price_precision = symbol_info.get('pricePrecision', 2)
            return round(price, price_precision)
        except Exception as e:
            logger.error(f"Error rounding price: {e}")
            return round(price, 2)

    def round_quantity(self, symbol: str, quantity: float) -> float:
        """Round quantity to the correct precision for the symbol"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                # Default precision if symbol info not available
                return round(quantity, 3)
            
            # Get quantity precision from symbol info
            quantity_precision = symbol_info.get('quantityPrecision', 3)
            return round(quantity, quantity_precision)
        except Exception as e:
            logger.error(f"Error rounding quantity: {e}")
            return round(quantity, 3)

    @RateLimiter(10)
    @RetryHandler(3, 1.0)
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100):
        """Get historical klines for ATR calculation with caching"""
        cache_key = f"klines_{symbol}_{interval}_{limit}"
        cached_data = self.cache.get(cache_key, self.config.get('cache.atr_cache_ttl', 300))
        
        if cached_data:
            return cached_data
        
        try:
            klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
            self.cache.set(cache_key, klines, self.config.get('cache.atr_cache_ttl', 300))
            return klines
        except BinanceAPIException as e:
            logger.error(f"Error getting klines: {e}")
            return []

    def calculate_atr(self, symbol: str, period: int = 14):
        """Calculate Average True Range (ATR) with caching"""
        cache_key = f"atr_{symbol}_{period}"
        cached_atr = self.cache.get(cache_key, self.config.get('cache.atr_cache_ttl', 300))
        if cached_atr:
            return cached_atr
        try:
            interval = self.config.get('stop_loss.timeframe', '1h')
            klines = self.get_klines(symbol, interval=interval, limit=period+1)
            if len(klines) < period+1:
                return None
            high_prices = [float(k[2]) for k in klines]
            low_prices = [float(k[3]) for k in klines]
            close_prices = [float(k[4]) for k in klines]
            true_ranges = []
            for i in range(1, len(klines)):
                high_low = high_prices[i] - low_prices[i]
                high_close = abs(high_prices[i] - close_prices[i-1])
                low_close = abs(low_prices[i] - close_prices[i-1])
                true_range = max(high_low, high_close, low_close)
                true_ranges.append(true_range)
            atr = np.mean(true_ranges[-period:])
            self.cache.set(cache_key, atr, self.config.get('cache.atr_cache_ttl', 300))
            return atr
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return None

    def get_taker_fee_rate(self, symbol: str) -> float:
        """Return taker fee rate from config.yaml if set, otherwise use default 0.0005 (0.05%)."""
        return self.config.get('stop_loss.taker_fee_rate', 0.0005)

    def calculate_fee(self, symbol: str, entry_price: float, quantity: float) -> float:
        """Calculate taker fee for the position using fixed rate (0.05%). Commission = Notional Value × Fee Rate"""
        taker_fee_rate = self.get_taker_fee_rate(symbol)
        return entry_price * quantity * taker_fee_rate

    def calculate_net_profit(self, symbol: str, position: dict) -> float:
        """Calculate net profit (Unrealized PnL - Fee) for a position."""
        entry_price = float(position['entryPrice'])
        position_amt = float(position['positionAmt'])
        quantity = abs(position_amt)
        unrealized_pnl = float(position['unRealizedProfit'])
        fee = self.calculate_fee(symbol, entry_price, quantity)
        return unrealized_pnl - fee

    def get_position_high_low(self, symbol: str, position: dict, current_price: float):
        """Get and update the highest (for long) or lowest (for short) price since position opened."""
        cache_key = f"highlow_{symbol}_{position['positionAmt']}"
        cached = self.cache.get(cache_key, 86400)  # 1 day
        is_long = float(position['positionAmt']) > 0
        if cached:
            high, low = cached.get('high', current_price), cached.get('low', current_price)
        else:
            high, low = current_price, current_price
        if is_long:
            high = max(high, current_price)
        else:
            low = min(low, current_price)
        self.cache.set(cache_key, {'high': high, 'low': low}, 86400)
        return high, low

    def calculate_optimal_stop_loss(self, symbol: str, position: dict, current_price: float):
        """Calculate optimal stop loss using multiple strategies, including step-by-step SL adjustment every 0.1% net profit."""
        try:
            entry_price = float(position['entryPrice'])
            position_amt = float(position['positionAmt'])
            is_long = position_amt > 0
            quantity = abs(position_amt)
            unrealized_pnl = float(position['unRealizedProfit'])

            stop_loss_candidates = []

            # Config
            mode = self.config.get('stop_loss.mode', 'both')
            min_net_profit_to_move_sl = self.config.get('stop_loss.min_net_profit_to_move_sl', 0.001)
            breakeven_buffer = self.config.get('stop_loss.breakeven_buffer', 0.001)
            trailing_percentage = self.config.get('stop_loss.trailing_stop_percentage', 0.01)
            step_percent = min_net_profit_to_move_sl  # ใช้ step เดียวกับ threshold

            # Step-by-step SL adjustment logic
            net_profit = self.calculate_net_profit(symbol, position)
            step_value = entry_price * quantity * step_percent
            cache_key = f"last_sl_profit_step_{symbol}_{position['positionAmt']}"
            last_step = self.cache.get(cache_key, 86400) or 0.0

            logger.info(f"[SL-DEBUG] Net profit: {net_profit:.4f}, Step value: {step_value:.4f}, Last step: {last_step:.4f}")

            # ถ้ากำไรสุทธิ >= 0 (ไม่ขาดทุน) ให้ขยับ SL มาปิดการขาดทุน (breakeven+buffer) ทันที
            if net_profit >= 0:
                if is_long:
                    sl_breakeven = entry_price + (self.calculate_fee(symbol, entry_price, quantity) / quantity) + (entry_price * breakeven_buffer)
                else:
                    sl_breakeven = entry_price - (self.calculate_fee(symbol, entry_price, quantity) / quantity) - (entry_price * breakeven_buffer)
                sl_breakeven = self.round_price(symbol, sl_breakeven)
                stop_loss_candidates.append(("BreakevenNoLoss", sl_breakeven))
                logger.info(f"[SL-DEBUG] ขยับ SL มาปิดการขาดทุน (breakeven+buffer) ที่ {sl_breakeven}")

            # ขยับ SL ทุก ๆ step_value ที่กำไรสุทธิเพิ่มขึ้น
            if net_profit > last_step + step_value:
                if is_long:
                    sl_move = entry_price + (self.calculate_fee(symbol, entry_price, quantity) / quantity) + (entry_price * breakeven_buffer) + ((net_profit // step_value) * step_value / quantity)
                else:
                    sl_move = entry_price - (self.calculate_fee(symbol, entry_price, quantity) / quantity) - (entry_price * breakeven_buffer) - ((net_profit // step_value) * step_value / quantity)
                sl_move = self.round_price(symbol, sl_move)
                stop_loss_candidates.append(("StepByStepSL", sl_move))
                self.cache.set(cache_key, (net_profit // step_value) * step_value, 86400)
                logger.info(f"[SL-DEBUG] ขยับ SL แล้ว (step-by-step) ที่ {sl_move}")

            # 2. Trailing Stop (True High/Low)
            if mode in ('trailing', 'both'):
                high, low = self.get_position_high_low(symbol, position, current_price)
                if is_long:
                    trailing_sl = high * (1 - trailing_percentage)
                else:
                    trailing_sl = low * (1 + trailing_percentage)
                trailing_sl = self.round_price(symbol, trailing_sl)
                stop_loss_candidates.append(("TrueTrailing", trailing_sl))

            # 3. Add other strategies as before (ATR, Percentage)
            if self.config.get('trading.enable_atr_stop', True):
                atr = self.calculate_atr(symbol, self.config.get('stop_loss.atr_period', 14))
                if atr:
                    atr_multiplier = self.config.get('stop_loss.atr_multiplier', 2.0)
                    if is_long:
                        atr_stop = entry_price - (atr * atr_multiplier)
                    else:
                        atr_stop = entry_price + (atr * atr_multiplier)
                    stop_loss_candidates.append(('ATR', atr_stop))
            if self.config.get('trading.enable_percentage_stop', True):
                risk_percentage = self.config.get('stop_loss.risk_percentage', 0.02)
                if is_long:
                    percentage_stop = entry_price * (1 - risk_percentage)
                else:
                    percentage_stop = entry_price * (1 + risk_percentage)
                stop_loss_candidates.append(('Percentage', percentage_stop))

            # 4. Max 3% from entry if no existing stop
            existing_stop = self.get_existing_stop_loss(symbol)
            max_sl_distance = 0.03  # 3%
            if existing_stop is None:
                if is_long:
                    sl_3pct = entry_price * (1 - max_sl_distance)
                else:
                    sl_3pct = entry_price * (1 + max_sl_distance)
                sl_3pct = self.round_price(symbol, sl_3pct)
                stop_loss_candidates.append(("Max3Percent", sl_3pct))

            # เลือก SL ที่ดีที่สุด (Long = สูงสุด, Short = ต่ำสุด)
            if stop_loss_candidates:
                if is_long:
                    best_stop = max(stop_loss_candidates, key=lambda x: x[1])
                else:
                    best_stop = min(stop_loss_candidates, key=lambda x: x[1])
                final_stop = best_stop[1]
            else:
                final_stop = super().calculate_optimal_stop_loss(symbol, position, current_price)

            logger.info(f"[Custom SL] Stop Loss calculation for {symbol}: {final_stop}")
            return final_stop
        except Exception as e:
            logger.error(f"Error calculating optimal stop loss (custom): {e}")
            return None

    @RateLimiter(10)
    @RetryHandler(3, 1.0)
    def get_current_price(self, symbol: str):
        """Get current price for a symbol with caching"""
        cache_key = f"price_{symbol}"
        cached_price = self.cache.get(cache_key, self.config.get('cache.price_cache_ttl', 5))
        
        if cached_price:
            return cached_price
        
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            self.cache.set(cache_key, price, self.config.get('cache.price_cache_ttl', 5))
            return price
        except BinanceAPIException as e:
            logger.error(f"Error getting current price: {e}")
            return None

    @RateLimiter(10)
    @RetryHandler(3, 1.0)
    def get_open_positions(self):
        """Get all open positions with caching"""
        cache_key = "open_positions"
        cached_positions = self.cache.get(cache_key, self.config.get('cache.position_cache_ttl', 30))
        
        if cached_positions:
            return cached_positions
        
        try:
            positions = self.client.futures_position_information()
            open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
            logger.info(f"Found {len(open_positions)} open positions")
            
            self.cache.set(cache_key, open_positions, self.config.get('cache.position_cache_ttl', 30))
            return open_positions
        except BinanceAPIException as e:
            logger.error(f"Error getting positions: {e}")
            return []

    @RateLimiter(5)
    @RetryHandler(3, 1.0)
    def adjust_stop_loss(self, symbol: str, stop_price: float, quantity: float = None):
        """Adjust stop loss for a position"""
        try:
            # Get current position
            positions = self.get_open_positions()
            position = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not position:
                logger.error(f"No open position found for {symbol}")
                return False

            # If quantity not specified, use current position size
            if quantity is None:
                quantity = abs(float(position['positionAmt']))

            # Round price and quantity to correct precision
            rounded_stop_price = self.round_price(symbol, stop_price)
            rounded_quantity = self.round_quantity(symbol, quantity)

            # Check stop price is on the correct side of current price
            current_price = self.get_current_price(symbol)
            is_long = float(position['positionAmt']) > 0
            if is_long:
                if rounded_stop_price >= current_price:
                    logger.warning(f"Skip SL for {symbol}: stop_price ({rounded_stop_price}) >= current_price ({current_price})")
                    return False
            else:
                if rounded_stop_price <= current_price:
                    logger.warning(f"Skip SL for {symbol}: stop_price ({rounded_stop_price}) <= current_price ({current_price})")
                    return False

            # Cancel existing stop loss orders
            self.client.futures_cancel_all_open_orders(symbol=symbol)
            logger.info(f"Cancelled existing orders for {symbol}")

            # Place new stop loss order
            side = "SELL" if float(position['positionAmt']) > 0 else "BUY"
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP_MARKET',
                stopPrice=rounded_stop_price,
                closePosition=True
            )
            
            # Invalidate position cache after order placement
            self.cache.invalidate("open_positions")
            
            logger.info(f"Successfully set new stop loss for {symbol} at {rounded_stop_price}")
            return True

        except BinanceAPIException as e:
            logger.error(f"Error adjusting stop loss: {e}")
            return False

    def auto_adjust_all_stop_losses(self):
        """Automatically adjust stop loss for all open positions"""
        try:
            positions = self.get_open_positions()
            
            for position in positions:
                symbol = position['symbol']
                current_price = self.get_current_price(symbol)
                
                if current_price is None:
                    continue
                
                # Calculate optimal stop loss
                optimal_stop = self.calculate_optimal_stop_loss(symbol, position, current_price)
                
                if optimal_stop is None:
                    continue
                
                # Check if we need to adjust the stop loss
                existing_stop = self.get_existing_stop_loss(symbol)
                
                if existing_stop is None or self.should_update_stop_loss(existing_stop, optimal_stop, position):
                    logger.info(f"Updating stop loss for {symbol} to {optimal_stop}")
                    self.adjust_stop_loss(symbol, optimal_stop)
                else:
                    logger.info(f"Stop loss for {symbol} is already optimal")
                    
        except Exception as e:
            logger.error(f"Error in auto adjust stop losses: {e}")

    @RateLimiter(10)
    @RetryHandler(3, 1.0)
    def get_existing_stop_loss(self, symbol: str):
        """Get existing stop loss order for a symbol"""
        try:
            orders = self.client.futures_get_open_orders(symbol=symbol)
            stop_orders = [order for order in orders if order['type'] == 'STOP_MARKET']
            if stop_orders:
                return float(stop_orders[0]['stopPrice'])
            return None
        except BinanceAPIException as e:
            logger.error(f"Error getting existing stop loss: {e}")
            return None

    def should_update_stop_loss(self, existing_stop: float, new_stop: float, position: dict):
        """Determine if stop loss should be updated"""
        position_amt = float(position['positionAmt'])
        is_long = position_amt > 0
        
        if is_long:
            # For long positions, only update if new stop is higher (better protection)
            return new_stop > existing_stop
        else:
            # For short positions, only update if new stop is lower (better protection)
            return new_stop < existing_stop

    def monitor_positions(self):
        """Monitor and log current positions"""
        positions = self.get_open_positions()
        for pos in positions:
            current_price = self.get_current_price(pos['symbol'])
            logger.info(f"Position: {pos['symbol']}, "
                       f"Size: {pos['positionAmt']}, "
                       f"Entry Price: {pos['entryPrice']}, "
                       f"Current Price: {current_price}, "
                       f"Unrealized PNL: {pos['unRealizedProfit']}")

    def should_use_aggressive_monitoring(self):
        """Check if we should use aggressive monitoring (when positions are in profit)"""
        try:
            positions = self.get_open_positions()
            for position in positions:
                unrealized_pnl = float(position['unRealizedProfit'])
                if unrealized_pnl > 0:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking aggressive monitoring: {e}")
            return False

    def get_monitoring_interval(self):
        """Get appropriate monitoring interval based on market conditions"""
        if self.should_use_aggressive_monitoring():
            return self.config.get('monitoring.aggressive_interval', 10)
        return self.config.get('monitoring.normal_interval', 30)

    def health_check(self):
        """Check system health and API connectivity"""
        current_time = time.time()
        if current_time - self.last_health_check < self.health_check_interval:
            return True
        
        try:
            # Test API connection
            self.client.futures_ping()
            # Check account status
            account = self.client.futures_account()
            self.last_health_check = current_time
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.cache.cleanup_expired()
            cache_stats = self.cache.get_stats()
            logger.info(f"Cache stats: {cache_stats}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    try:
        manager = BinanceSLManager()
        
        while True:
            try:
                logger.info("=== Starting position monitoring and stop loss adjustment ===")
                
                # Health check
                if not manager.health_check():
                    logger.warning("Health check failed, waiting before retry")
                    time.sleep(manager.config.get('monitoring.retry_interval', 60))
                    continue
                
                # Monitor positions
                manager.monitor_positions()
                
                # Auto adjust stop losses
                manager.auto_adjust_all_stop_losses()
                
                # Cleanup
                manager.cleanup()
                
                # Get dynamic interval
                interval = manager.get_monitoring_interval()
                logger.info(f"=== Completed monitoring cycle. Next check in {interval} seconds ===")
                
                # Wait for dynamic interval before next cycle
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(manager.config.get('monitoring.retry_interval', 60))
                
    except Exception as e:
        logger.error(f"Main error: {e}")

if __name__ == "__main__":
    main() 