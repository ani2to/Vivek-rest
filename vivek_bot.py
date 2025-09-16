import os
import time
import requests
import telebot
from telebot import types
import time
import json

# Initialize bot with your token
bot = telebot.TeleBot("8494293148:AAES5HFUfXV7iHeEa0OuAyKkHNjZvCGtuyY")

# Channel username (without @)
CHANNEL_USERNAME = "Vivekredirect"
# Group chat username (without @)
GROUP_USERNAME = "VIVEK_CHAT"
# Owner ID
OWNER_ID = 6285946815

# Store user states
user_states = {}

# Instagram reset function from your script
def send_reset_request(username_or_email):
    url = "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/"

    headers = {
        "authority": "www.instagram.com",
        "method": "POST",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/accounts/password/reset/?source=fxcal",
        "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; M2101K786) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "x-asbd-id": "129477",
        "x-csrftoken": "missing",  
        "x-ig-app-id": "1217981644879628",
        "x-ig-www-claim": "0",
        "x-instagram-ajax": "1015181662",
        "x-requested-with": "XMLHttpRequest"
    }

    session = requests.Session()
    session.get("https://www.instagram.com/accounts/password/reset/")
    csrf_token = session.cookies.get_dict().get("csrftoken", "missing")
    headers["x-csrftoken"] = csrf_token

    data = {
        "email_or_username": username_or_email,
        "flow": "fxcal"
    }

    response = session.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return True, f"Reset link successfully sent to: {username_or_email}"
    else:
        return False, response.json()

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

Available commands:
/reset - Send password reset link to your email
/help - Show this help message

How to use:
1. Use /reset command
2. Enter your Instagram username or email
3. Check your email for the reset link

Note: This bot uses Instagram's official API to send reset requests.

Join our channel for updates: @{CHANNEL_USERNAME}
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
    success, result_msg = send_reset_request(username_or_email)
    
    if success:
        bot.send_message(chat_id, f"✅ Reset link successfully sent to: {username_or_email}")
    else:
        # Format error response as JSON
        error_json = json.dumps(result_msg, indent=2)
        bot.send_message(chat_id, f"❌ Error sending reset link:\n\n```json\n{error_json}\n```", parse_mode="Markdown")

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
