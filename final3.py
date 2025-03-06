
import os
import json
import time
import random
import string
import subprocess
import psutil
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Bot Token and Admin ID
BOT_TOKEN = "7691836789:AAFt_Anb7sgjzOtadhN2vdLCs8Dk7HDurE4"
ADMIN_IDS = [6696347739]
# File paths
USERS_FILE = "users.json"
LOGS_FILE = "logs.txt"
BACKUP_FILE = "backup.txt"

# Check if users file exists, if not create it
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({"free_users": {}, "paid_users": {}, "blocked_users": []}, f)

# Check if logs file exists, if not create it
if not os.path.exists(LOGS_FILE):
    with open(LOGS_FILE, "w") as f:
        f.write("Bot started at {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

# Global variables
running_attack = False
attack_cooldowns = {}  # Store attack cooldowns by user ID
last_attack_ips = {}   # Store last attacked IPs by user ID
pending_feedback = {}  # Store users who need to provide feedback

# Helper functions
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"free_users": {}, "paid_users": {}, "blocked_users": []}

def save_users(users_data):
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

def log_action(user_id, username, action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User {user_id} (@{username}): {action}\n"
    with open(LOGS_FILE, "a") as f:
        f.write(log_entry)

def generate_captcha():
    """Generate a simple math captcha"""
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        result = a + b
    elif operation == '-':
        result = a - b
    else:
        result = a * b
        
    return f"{a} {operation} {b}", str(result)

async def is_admin(user_id):
    return user_id in ADMIN_IDS

async def is_paid_user(user_id):
    users_data = load_users()
    return str(user_id) in users_data["paid_users"]

async def is_blocked(user_id):
    users_data = load_users()
    return str(user_id) in users_data["blocked_users"]

async def send_to_admins(message):
    """Send a message to all admins"""
    for admin_id in ADMIN_IDS:
        try:
            await application.bot.send_message(chat_id=admin_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending message to admin {admin_id}: {e}")

# Command handlers
async def start_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check if user already registered
    users_data = load_users()
    if (str(user_id) in users_data["free_users"] or 
        str(user_id) in users_data["paid_users"]):
        # User is already registered, show help
        await help_command(update, context)
        return
    
    # Send animated loading message
    loading_message = (
        "Initializing System...\n"
        "█████████ 100% [LOADED] ✅\n"
        "🔓 Unlocking Secure Gateway...\n"
    )
    
    message = await update.message.reply_text(loading_message)
    
    # Animate loading bar
    loading_stages = [
        "█▒▒▒▒▒▒▒▒▒▒▒▒ 10%",
        "███▒▒▒▒▒▒▒▒▒▒ 30%",
        "█████▒▒▒▒▒▒▒▒ 50%",
        "███████▒▒▒▒▒▒ 70%",
        "█████████▒▒▒▒ 90%",
        "███████████ 100% ✅"
    ]
    
    for stage in loading_stages:
        await message.edit_text(loading_message + stage)
        time.sleep(0.5)
    
    await message.edit_text(loading_message + "███████████ 100% ✅\nACCESS GRANTED 🟢")
    time.sleep(0.5)
    
    # Welcome message and CAPTCHA
    welcome_text = (
        "🦾 Welcome, Cyber Warrior! Ready to Dominate the DDoS Bot?\n"
        "🔰 But First, Verify Yourself…\n\n"
        "Please complete the CAPTCHA below:"
    )
    
    # Generate CAPTCHA
    captcha_question, captcha_answer = generate_captcha()
    context.user_data["captcha_answer"] = captcha_answer
    
    captcha_text = f"{welcome_text}\n\nSolve: {captcha_question} = ?"
    await update.message.reply_text(captcha_text, reply_markup=ForceReply())
    
    # Set user state to awaiting captcha
    context.user_data["registration_state"] = "awaiting_captcha"

async def process_registration(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    message_text = update.message.text
    
    if "registration_state" not in context.user_data:
        return
    
    state = context.user_data["registration_state"]
    
    if state == "awaiting_captcha":
        # Verify CAPTCHA
        if message_text == context.user_data["captcha_answer"]:
            await update.message.reply_text(
                "✅ CAPTCHA verified successfully!\n\n"
                "Please enter your name to complete registration:"
            )
            context.user_data["registration_state"] = "awaiting_name"
        else:
            await update.message.reply_text(
                "❌ Incorrect CAPTCHA. Please try again.\n\n"
                "Type /start to restart the verification process."
            )
            context.user_data.pop("registration_state", None)
    
    elif state == "awaiting_name":
        # Save user data
        users_data = load_users()
        users_data["free_users"][str(user_id)] = {
            "name": message_text,
            "username": username,
            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users(users_data)
        
        # Log registration
        log_action(user_id, username, f"Registered with name: {message_text}")
        
        # Thank user and show help
        await update.message.reply_text(
            f"✅ Thank you, {message_text}!\n\n"
            "Registration complete. Welcome to the DDoS Bot!\n\n"
            "Use /help to see available commands."
        )
        
        # Send registration details to admin
        admin_notification = (
            f"🔔 New User Registered!\n"
            f"👤 Name: {message_text}\n"
            f"🔹 Username: @{username}\n"
            f"🆔 User ID: {user_id}"
        )
        await send_to_admins(admin_notification)
        
        # Clear registration state
        context.user_data.pop("registration_state", None)
        
        # Show help command
        await help_command(update, context)

async def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if await is_admin(user_id):
        help_text = (
            "🔰 *Available Commands:*\n\n"
            "👤 *User Commands:*\n"
            "/at <ip> <port> <time> - Launch an Attack\n"
            "/buy - Buy a Premium Plan\n"
            "/report <issue> - Report an Issue\n"
            "/ping - Check Server Response Time\n"
            "/info - Check Plan Validity\n\n"
            "⚙️ *Admin Commands:*\n"
            "/cpu - View Server Load\n"
            "/logs - View User Logs\n"
            "/dellogs - Delete Logs & Backup\n"
            "/reset - Reset System\n"
            "/view - See Free & Paid Users\n"
            "/broadcast <msg> - Send Message to All\n"
            "/approve <id> <days> - Approve Paid Access\n"
            "/disapprove <id> - Cancel Paid Access\n"
            "/block <id> - Block Free User\n"
            "/unblock <id> - Unblock Free User"
        )
    # Check if paid user
    elif await is_paid_user(user_id):
        help_text = (
            "🔰 *Available Commands:*\n\n"
            "/at <ip> <port> <time> - Launch an Attack\n"
            "/buy - Buy a Premium Plan\n"
            "/report <issue> - Report an Issue\n"
            "/ping - Check Server Response Time\n"
            "/info - Check Plan Validity"
        )
    # Free user
    else:
        help_text = (
            "🔰 *Available Commands:*\n\n"
            "/at <ip> <port> <time> - Launch an Attack\n"
            "/buy - Buy a Premium Plan\n"
            "/report <issue> - Report an Issue\n"
            "/ping - Check Server Response Time"
        )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def ping_command(update: Update, context: CallbackContext):
    start_time = time.time()
    
    # Simulate bot processing
    await update.message.reply_text("Pinging server...")
    
    # Calculate response time
    bot_response_time = int((time.time() - start_time) * 1000)
    
    # Simulate server latency check
    server_latency = random.randint(50, 150)  # Random value for demonstration
    
    ping_result = (
        "🏓 PING RESULT\n"
        f"⚡ Bot Response: {bot_response_time}ms\n"
        f"🖥 Server Latency: {server_latency}ms"
    )
    
    await update.message.reply_text(ping_result)
    log_action(update.effective_user.id, update.effective_user.username, "Used ping command")

async def report_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check if blocked
    if await is_blocked(user_id):
        await update.message.reply_text("❌ You are blocked from using this bot.")
        return
    
    # Check if user provided an issue
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a description of your issue.\n\n"
            "Format: /report <issue description>\n\n"
            "You can also send a screenshot after submitting your report."
        )
        return
    
    # Log the report
    issue = ' '.join(context.args)
    log_action(user_id, username, f"Reported issue: {issue}")
    
    # Allow user to send a screenshot
    await update.message.reply_text(
        "✅ Your report has been submitted.\n\n"
        "If you have a screenshot of the issue, please send it now. Otherwise, type /cancel."
    )
    
    # Set user state to awaiting screenshot
    context.user_data["awaiting_screenshot"] = True
    context.user_data["report_issue"] = issue
    
    # Send report to admin without waiting for screenshot
    admin_notification = (
        f"⚠️ New Report Received!\n"
        f"🆔 User: @{username} (ID: {user_id})\n"
        f"📌 Issue: \"{issue}\"\n"
        f"🖼 Waiting for possible screenshot..."
    )
    await send_to_admins(admin_notification)

async def process_screenshot(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if "awaiting_screenshot" not in context.user_data or not context.user_data["awaiting_screenshot"]:
        return
    
    # User sent a photo for their report
    if update.message.photo:
        photo = update.message.photo[-1]  # Get the largest version of the photo
        
        # Forward screenshot to admin
        for admin_id in ADMIN_IDS:
            try:
                caption = (
                    f"📷 Screenshot for report from @{username} (ID: {user_id})\n"
                    f"📌 Issue: \"{context.user_data['report_issue']}\""
                )
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo.file_id,
                    caption=caption
                )
            except Exception as e:
                print(f"Error sending screenshot to admin {admin_id}: {e}")
        
        await update.message.reply_text("✅ Your screenshot has been submitted. Thank you for your report!")
        context.user_data.pop("awaiting_screenshot", None)
        context.user_data.pop("report_issue", None)
    
    # User sent text instead of photo
    elif update.message.text and update.message.text.lower() == "/cancel":
        await update.message.reply_text("❌ Screenshot submission canceled.")
        context.user_data.pop("awaiting_screenshot", None)
        context.user_data.pop("report_issue", None)

async def attack_command(update: Update, context: CallbackContext):
    global running_attack
    
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check if blocked
    if await is_blocked(user_id):
        await update.message.reply_text("❌ You are blocked from using this bot.")
        return
    
    # Check if attack is already running
    if running_attack:
        await update.message.reply_text(
            "⚠️ Attack Already in Progress!\n"
            "⏳ Wait Until The Current Attack Finishes Before Starting a New One."
        )
        return
    
    # Check if command has correct arguments
    if len(context.args) != 3:
        await update.message.reply_text(
            "❌ Invalid command format.\n\n"
            "Format: /at <ip> <port> <time>\n"
            "Example: /at 192.168.1.1 80 60"
        )
        return
    
    ip = context.args[0]
    port = context.args[1]
    requested_time = int(context.args[2])
    
    # Validate IP format
    if not all(part.isdigit() and 0 <= int(part) <= 255 for part in ip.split('.')) or len(ip.split('.')) != 4:
        await update.message.reply_text("❌ Invalid IP address format.")
        return
    
    # Validate port
    if not port.isdigit() or not (1 <= int(port) <= 65535):
        await update.message.reply_text("❌ Invalid port number. Must be between 1-65535.")
        return
    
    # Check time limits and cooldowns
    is_paid = await is_paid_user(user_id)
    max_time = 230 if is_paid else 150
    
    if requested_time > max_time:
        await update.message.reply_text(
            f"❌ Maximum attack time for {'premium' if is_paid else 'free'} users is {max_time} seconds."
        )
        return
    
    # Check cooldown for free users
    if not is_paid:
        current_time = time.time()
        
        # Check if user has attacked this IP before and needs to wait
        if str(user_id) in attack_cooldowns and ip in attack_cooldowns[str(user_id)]:
            cooldown_end = attack_cooldowns[str(user_id)][ip]
            if current_time < cooldown_end:
                remaining = int(cooldown_end - current_time)
                await update.message.reply_text(
                    f"⏳ Cooldown active for this IP!\n"
                    f"Please wait {remaining} seconds before attacking this IP again."
                )
                return
        
        # Check if user needs to provide feedback before a new attack
        if str(user_id) in pending_feedback and pending_feedback[str(user_id)]:
            await update.message.reply_text(
                "⚠️ Please provide feedback on your last attack before starting a new one.\n"
                "Was your last attack effective? (Yes/No)"
            )
            context.user_data["awaiting_feedback"] = True
            context.user_data["pending_attack"] = {
                "ip": ip,
                "port": port,
                "time": requested_time
            }
            return
    
    # Start the attack
    attack_time = min(requested_time, max_time)
    
    # Show animation
    attack_message = (
        "🚀 Initiating Cyber Strike...\n"
        f"💣 Locking Target: {ip}\n"
        "⚡ Powering Up The Cannons..."
    )
    
    message = await update.message.reply_text(attack_message)
    time.sleep(1)
    
    await message.edit_text(
        attack_message + "\n🛡 Engaging Attack Protocols..."
    )
    time.sleep(1)
    
    await message.edit_text(
        attack_message + "\n🛡 Engaging Attack Protocols...\n"
        "🔥 ATTACK DEPLOYMENT IN PROGRESS!"
    )
    
    # Mark attack as running
    running_attack = True
    
    # Log the attack
    log_action(user_id, username, f"Started attack on {ip}:{port} for {attack_time} seconds")
    
    # Execute the attack command (simulation for this example)
    attack_command = f"./moul {ip} {port} {attack_time} 70"
    
    # Here we just simulate the command execution
    # In a real scenario, you would use subprocess.Popen to run the actual command
    print(f"[SIMULATION] Executing: {attack_command}")
    
    # Wait for attack to complete
    await update.message.reply_text(
        f"⚡ Attack on {ip}:{port} in progress!\n"
        f"⏱ Duration: {attack_time} seconds\n\n"
        "Please wait for the attack to complete..."
    )
    
    # Simulate attack duration
    await asyncio.sleep(min(10, attack_time))  # Simulate for max 10 seconds
    
    # Mark attack as finished
    running_attack = False
    
    # Set cooldown for free users
    if not is_paid:
        if str(user_id) not in attack_cooldowns:
            attack_cooldowns[str(user_id)] = {}
        
        # Set 60 second cooldown for this IP
        attack_cooldowns[str(user_id)][ip] = time.time() + 60
        
        # Mark user as needing to provide feedback
        pending_feedback[str(user_id)] = True
        last_attack_ips[str(user_id)] = ip
        
        # Ask for feedback
        await update.message.reply_text(
            "✅ Attack completed!\n\n"
            "Please provide feedback: Was the attack effective? (Yes/No)"
        )
        context.user_data["awaiting_feedback"] = True
    else:
        # For paid users, just notify of completion
        await update.message.reply_text("✅ Attack completed!")

async def process_feedback(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    if "awaiting_feedback" not in context.user_data or not context.user_data["awaiting_feedback"]:
        return
    
    feedback = update.message.text.lower()
    
    if feedback in ["yes", "no"]:
        # Log the feedback
        if str(user_id) in last_attack_ips:
            ip = last_attack_ips[str(user_id)]
            log_action(user_id, username, f"Provided feedback on attack to {ip}: {feedback}")
        
        # Clear pending feedback
        if str(user_id) in pending_feedback:
            pending_feedback[str(user_id)] = False
        
        # Thank user for feedback
        await update.message.reply_text("✅ Thank you for your feedback!")
        
        # If user had a pending attack, execute it now
        if "pending_attack" in context.user_data:
            attack_details = context.user_data["pending_attack"]
            context.args = [attack_details["ip"], attack_details["port"], str(attack_details["time"])]
            context.user_data.pop("pending_attack", None)
            await attack_command(update, context)
        
        # Clear awaiting feedback state
        context.user_data.pop("awaiting_feedback", None)
    else:
        await update.message.reply_text("❌ Please answer with 'Yes' or 'No'.")

async def buy_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if already a paid user
    if await is_paid_user(user_id):
        await update.message.reply_text(
            "✅ You are already a premium user!\n\n"
            "Use /info to check your plan details."
        )
        return
    
    # Check if blocked
    if await is_blocked(user_id):
        await update.message.reply_text("❌ You are blocked from using this bot.")
        return
    
    # Show premium plans
    premium_text = (
        "💎 *Premium Plans:*\n\n"
        "🔶 *1 Day* - $5\n"
        "🔶 *7 Days* - $20\n"
        "🔶 *30 Days* - $50\n\n"
        "✅ *Benefits:*\n"
        "- Extended Attack Duration (230 seconds)\n"
        "- No Cooldown Between Attacks\n"
        "- No Feedback Required\n"
        "- Priority Support\n\n"
        "💵 *Payment Methods:*\n"
        "- Bitcoin\n"
        "- Ethereum\n"
        "- PayPal\n\n"
        "Contact @AdminUsername to purchase."
    )
    
    await update.message.reply_text(premium_text, parse_mode="Markdown")

async def info_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if paid user
    if not await is_paid_user(user_id):
        await update.message.reply_text(
            "❌ You are not a premium user.\n\n"
            "Use /buy to see available premium plans."
        )
        return
    
    # Get user data
    users_data = load_users()
    user_info = users_data["paid_users"].get(str(user_id), {})
    
    if "expires_at" in user_info:
        # Calculate remaining days
        expires_at = datetime.strptime(user_info["expires_at"], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        if expires_at > now:
            days_left = (expires_at - now).days
            hours_left = ((expires_at - now).seconds // 3600)
            
            info_text = (
                "💎 *Premium Status:*\n\n"
                f"✅ You are a premium user!\n"
                f"⏱ Your plan expires in: *{days_left} days and {hours_left} hours*\n"
                f"📅 Expiration date: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "✨ Enjoy your premium benefits!"
            )
        else:
            info_text = (
                "⚠️ *Premium Status:*\n\n"
                "❌ Your premium plan has expired.\n\n"
                "Use /buy to purchase a new plan."
            )
    else:
        info_text = (
            "💎 *Premium Status:*\n\n"
            "✅ You are a premium user!\n"
            "⏱ Your plan has no expiration date.\n\n"
            "✨ Enjoy your premium benefits!"
        )
    
    await update.message.reply_text(info_text, parse_mode="Markdown")

# Admin Commands
async def cpu_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Get real system stats
    cpu_percent = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Format stats
    cpu_text = (
        "🖥 SYSTEM STATUS\n"
        f"⚡ CPU Cores: {psutil.cpu_count()}\n"
        f"🔥 Current CPU Usage: {cpu_percent}%\n"
        f"💾 RAM: {ram.total // (1024**3)}GB (Used: {ram.used // (1024**3)}GB | Free: {ram.available // (1024**3)}GB)\n"
        f"📀 Disk: {disk.total // (1024**3)}GB (Used: {disk.used // (1024**3)}GB | Free: {disk.free // (1024**3)}GB)"
    )
    
    await update.message.reply_text(cpu_text)

async def logs_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Read logs
    try:
        with open(LOGS_FILE, "r") as f:
            logs = f.read()
        
        # If logs are too long, send last 50 lines
        logs_lines = logs.split('\n')
        if len(logs_lines) > 50:
            logs = '\n'.join(logs_lines[-50:])
            logs = f"[Showing last 50 log entries...]\n\n{logs}"
        
        # Send logs
        if logs:
            await update.message.reply_text(f"📜 Recent Logs:\n\n```\n{logs}\n```", parse_mode="Markdown")
        else:
            await update.message.reply_text("📜 No logs found.")
    except FileNotFoundError:
        await update.message.reply_text("❌ Logs file not found.")

async def dellogs_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Create backup
    try:
        with open(LOGS_FILE, "r") as f:
            logs = f.read()
        
        with open(BACKUP_FILE, "w") as f:
            f.write(logs)
        
        # Send backup file
        with open(BACKUP_FILE, "rb") as f:
            await update.message.reply_document(document=f, filename="backup.txt")
        
        # Clear logs file
        with open(LOGS_FILE, "w") as f:
            f.write(f"Logs cleared by admin at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        await update.message.reply_text(
            "✅ Logs Backup Created!\n"
            "📂 File: backup.txt (Sent to Admin)\n"
            "🗑 Logs Successfully Deleted from Server."
        )
    except FileNotFoundError:
        await update.message.reply_text("❌ Logs file not found.")

async def reset_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Reset global variables
    global running_attack, attack_cooldowns, last_attack_ips, pending_feedback
    running_attack = False
    attack_cooldowns = {}
    last_attack_ips = {}
    pending_feedback = {}
    
    await update.message.reply_text("✅ System reset completed!")

async def view_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Get user data
    users_data = load_users()
    
    # Format paid users
    paid_users_text = "🟢 Paid Users:\n"
    if users_data["paid_users"]:
        for i, (uid, info) in enumerate(users_data["paid_users"].items(), 1):
            username = info.get("username", "Unknown")
            
            # Check if user has expiration date
            if "expires_at" in info:
                expires_at = datetime.strptime(info["expires_at"], "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                
                if expires_at > now:
                    days_left = (expires_at - now).days
                    paid_users_text += f"{i}️⃣ @{username} (ID: {uid}) - Expires in {days_left} Days\n"
                else:
                    paid_users_text += f"{i}️⃣ @{username} (ID: {uid}) - EXPIRED\n"
            else:
                paid_users_text += f"{i}️⃣ @{username} (ID: {uid}) - No Expiration\n"
    else:
        paid_users_text += "No paid users found.\n"
    
    # Format free users
    free_users_text = "\n🔴 Free Users:\n"
    if users_data["free_users"]:
        for i, (uid, info) in enumerate(users_data["free_users"].items(), 1):
            if uid not in users_data["paid_users"]:
                username = info.get("username", "Unknown")
                free_users_text += f"{i}️⃣ @{username} (ID: {uid})\n"
    else:
        free_users_text += "No free users found.\n"
    
    # Format blocked users
    blocked_users_text = "\n⚫ Blocked Users:\n"
    if users_data["blocked_users"]:
        for i, uid in enumerate(users_data["blocked_users"], 1):
            blocked_users_text += f"{i}️⃣ User ID: {uid}\n"
    else:
        blocked_users_text += "No blocked users found.\n"
    
    await update.message.reply_text(paid_users_text + free_users_text + blocked_users_text)

async def broadcast_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Check if message is provided
    if not context.args:
        await update.message.reply_text("❌ Please provide a message to broadcast.")
        return
    
    broadcast_message = ' '.join(context.args)
    
    # Get all users
    users_data = load_users()
    all_users = list(users_data["free_users"].keys()) + list(users_data["paid_users"].keys())
    unique_users = set(all_users)
    
    # Send message to all users
    sent_count = 0
    failed_count = 0
    
    await update.message.reply_text(f"🔄 Broadcasting message to {len(unique_users)} users...")
    
    for uid in unique_users:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 *BROADCAST MESSAGE*\n\n{broadcast_message}",
                parse_mode="Markdown"
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Error sending broadcast to user {uid}: {e}")
    
    await update.message.reply_text(
        f"✅ Broadcast completed!\n"
        f"✓ Sent to {sent_count} users\n"
        f"✗ Failed to send to {failed_count} users"
    )

async def approve_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Check command format
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Invalid command format.\n\n"
            "Format: /approve <user_id> <days>"
        )
        return
    
    target_id = context.args[0]
    try:
        days = int(context.args[1])
        if days <= 0:
            raise ValueError("Days must be positive")
    except ValueError:
        await update.message.reply_text("❌ Days must be a positive number.")
        return
    
    # Load users data
    users_data = load_users()
    
    # Check if user exists
    if target_id not in users_data["free_users"] and target_id not in users_data["paid_users"]:
        await update.message.reply_text("❌ User not found.")
        return
    
    # Get user info
    if target_id in users_data["free_users"]:
        user_info = users_data["free_users"][target_id]
    else:
        user_info = users_data["paid_users"][target_id]
    
    # Calculate expiration date
    expires_at = datetime.now() + timedelta(days=days)
    
    # Update or add to paid users
    users_data["paid_users"][target_id] = {
        **user_info,
        "approved_by": user_id,
        "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Remove from blocked users if necessary
    if target_id in users_data["blocked_users"]:
        users_data["blocked_users"].remove(target_id)
    
    # Save user data
    save_users(users_data)
    
    # Log action
    log_action(user_id, update.effective_user.username, f"Approved premium for user {target_id} for {days} days")
    
    # Notify target user
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                "🎉 *Congratulations!*\n\n"
                "Your account has been upgraded to premium status!\n\n"
                f"✅ Premium access granted for *{days} days*\n"
                f"📅 Expires on: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "Use /help to see the available commands."
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error notifying user {target_id}: {e}")
    
    await update.message.reply_text(
        f"✅ User {target_id} has been approved for premium access for {days} days.\n"
        f"Expires on: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

async def disapprove_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Check command format
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Invalid command format.\n\n"
            "Format: /disapprove <user_id>"
        )
        return
    
    target_id = context.args[0]
    
    # Load users data
    users_data = load_users()
    
    # Check if user is a paid user
    if target_id not in users_data["paid_users"]:
        await update.message.reply_text("❌ User is not a premium user.")
        return
    
    # Get user info before removing
    user_info = users_data["paid_users"][target_id]
    
    # Remove from paid users
    del users_data["paid_users"][target_id]
    
    # Save user data
    save_users(users_data)
    
    # Log action
    log_action(user_id, update.effective_user.username, f"Removed premium access for user {target_id}")
    
    # Notify target user
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                "⚠️ *Premium Status Update*\n\n"
                "Your premium access has been revoked.\n\n"
                "You have been downgraded to a free user.\n"
                "Contact admin for more information."
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error notifying user {target_id}: {e}")
    
    await update.message.reply_text(f"✅ Premium access for user {target_id} has been revoked.")

async def block_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Check command format
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Invalid command format.\n\n"
            "Format: /block <user_id>"
        )
        return
    
    target_id = context.args[0]
    
    # Load users data
    users_data = load_users()
    
    # Check if user exists
    if target_id not in users_data["free_users"] and target_id not in users_data["paid_users"]:
        await update.message.reply_text("❌ User not found.")
        return
    
    # Add to blocked users if not already blocked
    if target_id not in users_data["blocked_users"]:
        users_data["blocked_users"].append(target_id)
        
        # Save user data
        save_users(users_data)
        
        # Log action
        log_action(user_id, update.effective_user.username, f"Blocked user {target_id}")
        
        # Notify target user
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=(
                    "⚠️ *Account Blocked*\n\n"
                    "Your access to the bot has been blocked by an administrator.\n\n"
                    "Contact admin for more information."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error notifying user {target_id}: {e}")
        
        await update.message.reply_text(f"✅ User {target_id} has been blocked.")
    else:
        await update.message.reply_text(f"⚠️ User {target_id} is already blocked.")

async def unblock_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Check if admin
    if not await is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Check command format
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Invalid command format.\n\n"
            "Format: /unblock <user_id>"
        )
        return
    
    target_id = context.args[0]
    
    # Load users data
    users_data = load_users()
    
    # Check if user is blocked
    if target_id in users_data["blocked_users"]:
        users_data["blocked_users"].remove(target_id)
        
        # Save user data
        save_users(users_data)
        
        # Log action
        log_action(user_id, update.effective_user.username, f"Unblocked user {target_id}")
        
        # Notify target user
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=(
                    "✅ *Account Unblocked*\n\n"
                    "Your access to the bot has been restored.\n\n"
                    "Use /help to see available commands."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error notifying user {target_id}: {e}")
        
        await update.message.reply_text(f"✅ User {target_id} has been unblocked.")
    else:
        await update.message.reply_text(f"⚠️ User {target_id} is not blocked.")

# Set up the application
async def main():
    global application
    
    # Import asyncio here to avoid circular import
    import asyncio
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("at", attack_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("info", info_command))
    
    # Admin commands
    application.add_handler(CommandHandler("cpu", cpu_command))
    application.add_handler(CommandHandler("logs", logs_command))
    application.add_handler(CommandHandler("dellogs", dellogs_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("view", view_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("approve", approve_command))
    application.add_handler(CommandHandler("disapprove", disapprove_command))
    application.add_handler(CommandHandler("block", block_command))
    application.add_handler(CommandHandler("unblock", unblock_command))
    
    # Message handlers for processing registration, screenshots, and feedback
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, 
                                          lambda u, c: asyncio.create_task(process_registration(u, c)) or 
                                                     asyncio.create_task(process_feedback(u, c))))
    application.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE,
                                          process_screenshot))
    
    # Start the Bot
    print("Starting bot...")
    await application.initialize()
    await application.start_polling()
    await application.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())