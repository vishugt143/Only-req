# app.py
# Don't Remove Credit @teacher_slex
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from pyrogram.errors import FloodWait, UserAlreadyParticipant, PeerIdInvalid

# Database aur Config imports
# Make sure database.py aur configs.py same folder me ho
from database import add_user, add_group, all_users, all_groups, users as users_collection
from configs import cfg

# Logging Setup (Error dekhne ke liye)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot Client Setup
bot = Client(
    "approver_bot",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

# ------------------ WEB SERVER (RENDER KEEP ALIVE) ------------------
async def web_handler(request):
    return web.Response(text="🤖 Bot is Running Successfully!")

async def start_web_server():
    # Render environment se PORT uthayega, warna 8080 use karega
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", web_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌍 Web Server started on Port {port}")

# ------------------ JOIN REQUEST HANDLER ------------------
@bot.on_chat_join_request()
async def auto_approve(client: Client, req: ChatJoinRequest):
    try:
        chat = req.chat
        user = req.from_user
        
        logger.info(f"📥 New Request: {user.first_name} | Chat: {chat.title}")

        # Database Update
        try:
            add_user(user.id)
            add_group(chat.id)
        except Exception as e:
            logger.error(f"DB Error: {e}")

        # ⏳ 10 Seconds Wait
        await asyncio.sleep(10)

        # ✅ Approve Request
        try:
            await client.approve_chat_join_request(chat.id, user.id)
            logger.info(f"✅ Approved: {user.first_name}")
        except UserAlreadyParticipant:
            pass # Already approved
        except Exception as e:
            logger.error(f"Approval Failed: {e}")
            return # Agar approve nahi hua to welcome msg mat bhejo

        # 👋 Welcome Message
        try:
            await client.send_message(
                chat_id=user.id,
                text=(
                    f"👋 Hello {user.mention}!\n\n"
                    f"✅ Your request to join **{chat.title}** has been approved.\n"
                    "🎉 Welcome to the community!"
                )
            )
        except (PeerIdInvalid, Exception):
            # User ne bot start nahi kiya ya block kiya hai
            pass

    except FloodWait as e:
        logger.warning(f"FloodWait: Sleeping for {e.value}s")
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Handler Error: {e}")

# ------------------ ILLEGAL WORDS FILTER ------------------
@bot.on_message(filters.group & filters.text)
async def delete_banned_words(_, m: Message):
    if not m.from_user:
        return
        
    # Admin (SUDO) ko ignore karo
    if m.from_user.id in cfg.SUDO:
        return

    text = m.text.lower()
    
    for word in cfg.ILLEGAL_WORDS:
        # Regex check for exact word match
        if re.search(r"\b" + re.escape(word.lower()) + r"\b", text):
            try:
                await m.delete()
                warning = await m.reply(f"⚠️ {m.from_user.mention}, using '{word}' is not allowed!")
                await asyncio.sleep(5)
                await warning.delete()
            except Exception:
                pass
            return # Ek word mil gaya to loop band karo

# ------------------ START COMMAND ------------------
@bot.on_message(filters.private & filters.command("start"))
async def start_cmd(_, m: Message):
    add_user(m.from_user.id)
    
    # Buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel", url="https://t.me/lnx_store")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/teacher_slex")]
    ])

    if m.from_user.id in cfg.SUDO:
        await m.reply_text(
            f"👋 **Hello Admin!**\n\nBot is running.\n/users - Check Stats\n/bcast - Broadcast Message",
            reply_markup=buttons
        )
    else:
        await m.reply_text(
            "👋 **Hello!**\nI am an Auto Approver Bot.\nJoin my groups and I will accept you automatically.",
            reply_markup=buttons
        )

# ------------------ ADMIN COMMANDS ------------------
@bot.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    # Database.py functions use kar rahe hain
    try:
        u = all_users()
        g = all_groups()
        await m.reply_text(f"📊 **Stats:**\n\n👤 Users: `{u}`\n👥 Groups: `{g}`")
    except Exception as e:
        await m.reply_text(f"Error fetching stats: {e}")

@bot.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def broadcast_msg(_, m: Message):
    if not m.reply_to_message:
        return await m.reply("❌ Reply to a message to broadcast.")

    msg = await m.reply("⏳ Broadcasting...")
    count, fail = 0, 0
    
    # Database se users fetch karo
    # Note: Aapke DB me user_id String hai, usko Int banana padega
    try:
        # Cursor object return hota hai, us par loop chalayenge
        all_users_cursor = users_collection.find({})
        
        for user_doc in all_users_cursor:
            try:
                user_id = int(user_doc['user_id'])
                await m.reply_to_message.copy(user_id)
                count += 1
                await asyncio.sleep(0.1) # Floodwait prevention
            except FloodWait as e:
                await asyncio.sleep(e.value)
                # Retry logic
                try:
                    await m.reply_to_message.copy(user_id)
                    count += 1
                except:
                    fail += 1
            except Exception:
                fail += 1
                
        await msg.edit(f"✅ **Broadcast Completed**\n\nSent: `{count}`\nFailed: `{fail}`")
    except Exception as e:
        await msg.edit(f"❌ Broadcast Error: {e}")

# ------------------ MAIN LOOP ------------------
async def main():
    # 1. Start Web Server first
    await start_web_server()
    
    # 2. Start Bot
    logger.info("🤖 Starting Bot...")
    await bot.start()
    logger.info("✅ Bot is Online!")
    
    # 3. Keep running
    await idle()
    
    # 4. Stop
    await bot.stop()

if __name__ == "__main__":
    # Windows/Linux compatibility
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Critical Error: {e}")
