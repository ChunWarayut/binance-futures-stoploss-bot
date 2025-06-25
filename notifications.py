import telegram
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
import config
import json

class NotificationSystem:
    def __init__(self):
        self.telegram_bot = None
        if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
            self.telegram_bot = telegram.Bot(token=config.TELEGRAM_BOT_TOKEN)

    async def send_telegram_message(self, message):
        try:
            if self.telegram_bot:
                await self.telegram_bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=message
                )
                logger.info(f"Telegram notification sent: {message}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")

    def send_email(self, subject, message):
        try:
            if config.EMAIL_ADDRESS and config.EMAIL_PASSWORD:
                msg = MIMEMultipart()
                msg['From'] = config.EMAIL_ADDRESS
                msg['To'] = config.EMAIL_ADDRESS
                msg['Subject'] = subject

                msg.attach(MIMEText(message, 'plain'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
                server.send_message(msg)
                server.quit()
                logger.info(f"Email notification sent: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")

    def send_discord_message(self, message):
        try:
            if config.DISCORD_WEBHOOK_URL:
                payload = {
                    "content": message,
                    "username": "Trading Bot",
                    "avatar_url": "https://i.imgur.com/4M34hi2.png"  # Optional: Add your bot's avatar
                }
                
                headers = {
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    config.DISCORD_WEBHOOK_URL,
                    data=json.dumps(payload),
                    headers=headers
                )
                
                if response.status_code == 204:
                    logger.info(f"Discord notification sent: {message}")
                else:
                    logger.error(f"Failed to send Discord notification. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")

    async def notify(self, message, subject="Trading Bot Notification"):
        await self.send_telegram_message(message)
        self.send_email(subject, message)
        self.send_discord_message(message) 