"""
Email Communication Plugin - Email notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any
import logging

from ..base import BaseCommunication
from src.utils.decorators import async_log_performance


class EmailCommunication(BaseCommunication):
    """Email communication plugin"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = config.get("smtp_port", 587)
        self.sender_email = config.get("sender_email")
        self.sender_password = config.get("sender_password")
        self.default_recipient = config.get("default_recipient")
        self.use_tls = config.get("use_tls", True)
        
    def get_communication_type(self) -> str:
        return "email"
        
    async def connect(self) -> bool:
        """Test SMTP connection"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                self.is_connected = True
                self.logger.info("Email SMTP connection successful")
                return True
        except Exception as e:
            self.logger.error(f"Failed to connect to SMTP server: {e}")
            self.is_connected = False
            return False
            
    async def disconnect(self):
        """Disconnect from email server"""
        self.is_connected = False
        self.logger.info("Disconnected from email server")
        
    @async_log_performance
    async def send_message(self, message: str, **kwargs) -> bool:
        """Send email message"""
        if not self.is_connected:
            self.logger.error("Not connected to email server")
            return False
            
        recipient = kwargs.get("recipient", self.default_recipient)
        subject = kwargs.get("subject", "Crypto Trading Bot Notification")
        message_type = kwargs.get("message_type", "plain")  # 'plain' or 'html'
        
        if not recipient:
            self.logger.error("No recipient specified")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient
            
            # Add message body
            if message_type == "html":
                part = MIMEText(message, "html")
            else:
                part = MIMEText(message, "plain")
            msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient, msg.as_string())
                
            self.logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
            
    async def send_html_alert(self, title: str, content: str, **kwargs) -> bool:
        """Send formatted HTML alert"""
        html_template = f"""
        <html>
        <body>
            <h2 style="color: #2E86AB;">{title}</h2>
            <div style="font-family: Arial, sans-serif;">
                {content}
            </div>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Sent by Crypto Trading Bot
            </p>
        </body>
        </html>
        """
        
        return await self.send_message(
            html_template,
            subject=title,
            message_type="html",
            **kwargs
        )