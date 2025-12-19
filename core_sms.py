"""
Twilio SMS integration for OTP and notifications
"""

from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import structlog

from core.config import settings

logger = structlog.get_logger(__name__)

# Initialize Twilio client
client = None
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {str(e)}")
        client = None

async def send_sms(to_phone: str, message: str) -> bool:
    """
    Send SMS using Twilio
    
    Args:
        to_phone: Recipient phone number (with country code)
        message: SMS message content
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not client or not settings.TWILIO_PHONE_NUMBER:
        logger.warning("Twilio not configured, SMS not sent", to_phone=to_phone)
        return False
    
    try:
        # Format phone number
        if not to_phone.startswith("+"):
            # Assume Indian number if no country code
            if to_phone.startswith("0"):
                to_phone = "+91" + to_phone[1:]
            else:
                to_phone = "+91" + to_phone
        
        # Send SMS
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        logger.info(f"SMS sent successfully", 
                   to_phone=to_phone, 
                   message_sid=message.sid)
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio error sending SMS: {str(e)}", to_phone=to_phone)
        return False
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}", to_phone=to_phone)
        return False

async def send_otp_sms(phone: str, otp: str, order_id: Optional[int] = None) -> bool:
    """
    Send OTP SMS for order delivery
    
    Args:
        phone: Customer phone number
        otp: 4-digit OTP
        order_id: Order ID (optional)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if order_id:
        message = f"Your Bite Me Buddy order #{order_id} is out for delivery. OTP: {otp}. Valid for 5 minutes."
    else:
        message = f"Your Bite Me Buddy OTP: {otp}. Valid for 5 minutes."
    
    return await send_sms(phone, message)

async def send_order_confirmation_sms(phone: str, order_id: int) -> bool:
    """
    Send order confirmation SMS
    
    Args:
        phone: Customer phone number
        order_id: Order ID
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    message = f"Thank you for ordering with Bite Me Buddy! Your order #{order_id} has been confirmed and is being prepared."
    return await send_sms(phone, message)

async def send_order_delivered_sms(phone: str, order_id: int) -> bool:
    """
    Send order delivered SMS
    
    Args:
        phone: Customer phone number
        order_id: Order ID
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    message = f"Your Bite Me Buddy order #{order_id} has been delivered. Thank you for ordering with us!"
    return await send_sms(phone, message)

async def send_team_member_assignment_sms(phone: str, order_id: int) -> bool:
    """
    Send team member assignment SMS
    
    Args:
        phone: Team member phone number
        order_id: Order ID
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    message = f"New order #{order_id} has been assigned to you. Please check your dashboard for details."
    return await send_sms(phone, message)