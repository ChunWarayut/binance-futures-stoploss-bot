import requests
from loguru import logger
import config
import json
import asyncio
import aiohttp

class NotificationSystem:
    def __init__(self):
        """Initialize Discord-only notification system"""
        self.discord_webhook_url = config.DISCORD_WEBHOOK_URL
        if not self.discord_webhook_url:
            logger.warning("Discord webhook URL not configured. Notifications will be disabled.")

    async def send_discord_message(self, message):
        """Send message to Discord webhook"""
        try:
            if not self.discord_webhook_url:
                logger.warning("Discord webhook URL not configured")
                return

            payload = {
                "content": message,
                "username": "🛡️ Stop Loss Manager",
                "avatar_url": "https://i.imgur.com/4M34hi2.png"
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook_url,
                    data=json.dumps(payload),
                    headers=headers
                ) as response:
                    if response.status == 204:
                        logger.info(f"Discord notification sent successfully")
                    else:
                        logger.error(f"Failed to send Discord notification. Status code: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")

    async def notify(self, message, subject="Stop Loss Manager Notification"):
        """Send notification via Discord only"""
        await self.send_discord_message(message) 