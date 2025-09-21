import os
import uuid
import string
import random
import logging
import requests
import sqlite3
import time
import asyncio
import threading
import json
from threading import Thread
from datetime import datetime
from flask import Flask
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set!")
    exit(1)

# Create bot instance FIRST
bot = telebot.TeleBot(BOT_TOKEN)
    
CHANNEL_USERNAME = "Vivekredirect"
# Group chat username (without @)
GROUP_USERNAME = "VIVEK_CHAT"
# Owner ID
OWNER_ID = 6285946815

# Store user states
user_states = {}

# Instagram reset function using the method from reset.py
class PasswordReset:
    def __init__(self, target):
        self.target = target.strip()
        if self.target.startswith("@"):
            self.target = self.target[1:]  # Remove @ if provided

        if "@" in self.target:
            self.data = {
                "_csrftoken": "".join(random.choices(string.ascii_letters + string.digits, k=32)),
                "user_email": self.target,
                "guid": str(uuid.uuid4()),
                "device_id": str(uuid.uuid4())
            }
        else:
            self.data = {
                "_csrftoken": "".join(random.choices(string.ascii_letters + string.digits, k=32)),
                "username": self.target,
                "guid": str(uuid.uuid4()),
                "device_id": str(uuid.uuid4())
            }
        
    def send_password_reset(self):
        try:
            head = {
                "user-agent": f"Instagram 150.0.0.0.000 Android (29/10; 300dpi; 720x1440; {''.join(random.choices(string.ascii_lowercase+string.digits, k=16))}/{''.join(random.choices(string.ascii_lowercase+string.digits, k=16))}; {''.join(random.choices(string.ascii_lowercase+string.digits, k=16))}; {''.join(random.choices(string.ascii_lowercase+string.digits, k=16))}; {''.join(random.choices(string.ascii_lowercase+string.digits, k=16))}; en_GB;)"
            }
            
            start_time = time.time()
            req = requests.post(
                "https://i.instagram.com/api/v1/accounts/send_password_reset/",
                headers=head,
                data=self.data,
                timeout=10)
            end_time = time.time()
            time_taken = round(end_time - start_time, 2)
            
            response_text = req.text
            
            # Extract info from response
            extracted_info = self.extract_info_from_response(response_text)
            
            if "obfuscated_email" in response_text or "username" in response_text:
                return {
                    "success": True,
                    "email": extracted_info if extracted_info else "Not available",
                    "time_taken": time_taken,
                    "target": self.target
                }
            else:
                return {
                    "success": False,
                    "error": response_text if len(response_text) < 100 else response_text[:100] + '...',
                    "time_taken": time_taken,
                    "target": self.target
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "time_taken": round(end_time - start_time, 2),
                "target": self.target
            }
    
    def extract_info_from_response(self, response_text):
        """
        Extract obfuscated email or username from Instagram response
        """
        try:
            # Try to parse JSON response
            data = json.loads(response_text)

            # Check for obfuscated_email first
            if "obfuscated_email" in data:
                return data["obfuscated_email"]

            # Check for username if obfuscated_email not available
            if "username" in data:
                return f"@{data['username']}"

            # If neither is available, return None
            return None
        except:
            # If JSON parsing fails, try string extraction
            try:
                if "obfuscated_email" in response_text:
                    return response_text.split('"obfuscated_email": "')[1].split('"')[0]
                elif "username" in response_text:
                    return f"@{response_text.split('"username": "')[1].split('"')[0]}"
            except:
                pass

            return None

def send_reset_request(username_or_email):
    reset = PasswordReset(username_or_email)
    result = reset.send_password_reset()
    return result["success"], result

# Check if user is a member of the channel
def is_channel_member(user_id):
    try:
        member_status = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member_status.status in ['member', 'administrator', 'creator']
    except:
        return False

# Check if user is a member of the group
def is_group_member(user_id):
    try:
        member_status = bot.get_chat_member(f"@{GROUP_USERNAME}", user_id)
        return member_status.status in ['member', 'administrator', 'creator']
    except:
        return False

# Check if message is from a group chat
def is_group_chat(message):
    return message.chat.type in ['group', 'supergroup']

# Welcome message with channel join requirement
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Don't respond to group messages unless directly mentioned
    if is_group_chat(message) and not message.text.startswith('/start@'):
        return
        
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if user is a member of the channel
    if not is_channel_member(user_id):
        # User is not a member, show join requirement
        welcome_text = """
👋 Welcome to Instagram Password Reset Bot!

To use this bot, you need to join our channel first.

After joining, use /reset to send a password reset link to your Instagram account.
"""
        
        # Create inline keyboard with channel join button and check button
        markup = types.InlineKeyboardMarkup()
        channel_btn = types.InlineKeyboardButton("Join Our Channel", url=f"t.me/{CHANNEL_USERNAME}")
        check_btn = types.InlineKeyboardButton("✅ I've Joined", callback_data="check_join")
        markup.add(channel_btn)
        markup.add(check_btn)
        
        bot.send_message(chat_id, welcome_text, reply_markup=markup)
    else:
        # User is already a member
        welcome_text = """
👋 Welcome to Instagram Password Reset Bot!

I can help you send a password reset link to your Instagram account.

Use /reset to send a password reset link.
"""
        bot.send_message(chat_id, welcome_text)
        
        # Thank user for being part of the community
        bot.send_message(chat_id, "✅ Thank you for being part of our community!")

# Handle callback queries (for join check button)
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if is_channel_member(user_id):
        # User has joined the channel
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="✅ Thank you for joining our channel!\n\nNow you can use /reset to send a password reset link to your Instagram account."
        )
    else:
        # User hasn't joined yet
        bot.answer_callback_query(call.id, "You haven't joined the channel yet. Please join and try again.")

# Help command
@bot.message_handler(commands=['help'])
def show_help(message):
    # Don't respond to group messages unless directly mentioned
    if is_group_chat(message) and not message.text.startswith('/help@'):
        return
        
    help_text = f"""
🤖 *Instagram Password Reset Bot*

*Available commands:*
/reset - Send password reset link to your email
/help - Show this help message

*How to use:*
1. Use /reset command
2. Enter your Instagram username or email
3. Check your email for the reset link

*Note:* This bot uses Instagram's official API to send reset requests.

Join our channel for updates: @{CHANNEL_USERNAME}

*Developer:* [ViVek](tg://user?id={OWNER_ID})
"""
    
    # Create inline keyboard with channel join button
    markup = types.InlineKeyboardMarkup()
    channel_btn = types.InlineKeyboardButton("Join Our Channel", url=f"t.me/{CHANNEL_USERNAME}")
    markup.add(channel_btn)
    
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown", reply_markup=markup)

# Reset command
@bot.message_handler(commands=['reset'])
def reset_command(message):
    # Don't respond to group messages unless directly mentioned
    if is_group_chat(message) and not message.text.startswith('/reset@'):
        return
        
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if user is a member of the channel
    if not is_channel_member(user_id):
        # User is not a member, show join requirement
        markup = types.InlineKeyboardMarkup()
        channel_btn = types.InlineKeyboardButton("Join Our Channel", url=f"t.me/{CHANNEL_USERNAME}")
        check_btn = types.InlineKeyboardButton("✅ I've Joined", callback_data="check_join_reset")
        markup.add(channel_btn)
        markup.add(check_btn)
        
        bot.send_message(chat_id, "❌ You need to join our channel to use this feature.", reply_markup=markup)
        return
    
    # Ask for username/email
    msg = bot.send_message(chat_id, "Please enter your Instagram username or email:")
    bot.register_next_step_handler(msg, process_reset_request)

# Handle callback for join check during reset
@bot.callback_query_handler(func=lambda call: call.data == "check_join_reset")
def check_join_reset_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if is_channel_member(user_id):
        # User has joined the channel
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="✅ Thank you for joining our channel!\n\nPlease enter your Instagram username or email:"
        )
        bot.register_next_step_handler_by_chat_id(chat_id, process_reset_request)
    else:
        # User hasn't joined yet
        bot.answer_callback_query(call.id, "You haven't joined the channel yet. Please join and try again.")

# Process reset request
def process_reset_request(message):
    # Don't process if this is a group message
    if is_group_chat(message):
        return
        
    username_or_email = message.text.strip()
    chat_id = message.chat.id
    
    # Show typing action
    bot.send_chat_action(chat_id, 'typing')
    
    # Send reset request
    success, result = send_reset_request(username_or_email)
    
    if success:
        response_text = f"""```json
🔐 Instagram Reset

👤 Username - {result['target']}
📧 Mail - {result['email']}
⏱️ Time taken : {result['time_taken']}s

✅ Reset sent successfully```
        
Dev: [ViVek](tg://user?id={OWNER_ID})"""
        
        bot.send_message(chat_id, response_text, parse_mode="Markdown")
    else:
        # Format error response
        error_msg = "Invalid username or email" if "user" in result.get("error", "").lower() else "Account not found or server error"
        
        response_text = f"""```json
🔐 Instagram Reset

👤 Username - {result['target']}
❌ {error_msg}

Status: Failed```
        
Dev: [ViVek](tg://user?id={OWNER_ID})"""
        
        bot.send_message(chat_id, response_text, parse_mode="Markdown")

# Handle messages in private chats only
@bot.message_handler(func=lambda message: message.chat.type == 'private')
def handle_private_messages(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "Unknown command. Use /help to see available commands.")
    else:
        # Suggest channel join for any other message
        markup = types.InlineKeyboardMarkup()
        channel_btn = types.InlineKeyboardButton("Join Our Channel", url=f"t.me/{CHANNEL_USERNAME}")
        markup.add(channel_btn)
        
        bot.send_message(message.chat.id, "I'm just a simple bot. Use /help to see what I can do!\n\n"
                         "Join our channel for updates:", reply_markup=markup)

from threading import Thread
from datetime import datetime
from flask import Flask

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot is running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    # Start Flask in a separate thread
    Thread(target=run_flask).start()
    
    # Start the bot
    logger.info("Starting bot...")
    bot.infinity_polling()