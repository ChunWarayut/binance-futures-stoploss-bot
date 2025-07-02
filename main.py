import asyncio
import time
from binance_sl_manager import BinanceSLManager
from loguru import logger
import config
from notifications import NotificationSystem

async def send_notification(message: str):
    """ส่งการแจ้งเตือนแบบ async"""
    try:
        notification = NotificationSystem()
        await notification.notify(message)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

def main():
    """รัน Stop Loss Manager แบบ synchronous"""
    try:
        # เริ่มต้น Stop Loss Manager
        sl_manager = BinanceSLManager()
        
        logger.info("Starting Stop Loss Manager...")
        
        # ส่งการแจ้งเตือนเริ่มต้น
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_notification(
            "🛡️ Stop Loss Manager Started\n"
            "📊 Monitoring existing positions only\n"
            "🎯 Auto-adjusting Stop Loss based on:\n"
            "• ATR (Average True Range)\n"
            "• Trailing Stop Loss\n"
            "• Profit Protection\n"
            f"• Risk Management: {config.RISK_PERCENTAGE*100}% per trade"
        ))
        
        # รัน Main Loop
        while True:
            try:
                logger.info("=== Starting position monitoring and stop loss adjustment ===")
                
                # Health check
                if not sl_manager.health_check():
                    logger.warning("Health check failed, waiting before retry")
                    retry_interval = sl_manager.config.get('monitoring.retry_interval', 60)
                    time.sleep(float(retry_interval) if isinstance(retry_interval, (int, float)) else 60.0)
                    continue
                
                # Monitor positions
                sl_manager.monitor_positions()
                
                # Auto adjust stop losses
                sl_manager.auto_adjust_all_stop_losses()
                
                # Cleanup
                sl_manager.cleanup()
                
                # Get dynamic interval
                interval = sl_manager.get_monitoring_interval()
                logger.info(f"=== Completed monitoring cycle. Next check in {interval} seconds ===")
                
                # Wait for dynamic interval before next cycle
                sleep_time = float(interval) if isinstance(interval, (int, float)) else 30.0
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                # ส่งแจ้งเตือนข้อผิดพลาด
                loop.run_until_complete(send_notification(f"❌ Stop Loss Manager Error: {str(e)}"))
                retry_interval = sl_manager.config.get('monitoring.retry_interval', 60)
                time.sleep(float(retry_interval) if isinstance(retry_interval, (int, float)) else 60.0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        # ส่งแจ้งเตือนข้อผิดพลาดร้าย
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_notification(f"💀 Fatal Stop Loss Manager Error: {str(e)}"))
        raise

if __name__ == "__main__":
    main() 