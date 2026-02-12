# app.py
# Don't Remove Credit @teacher_slex
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters, idle, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from pyrogram.errors.exceptions.flood_420 import FloodWait

# Aapka database.py import
from database import add_user, add_group, all_users, all_groups, users
from configs import cfg

# Logging Setup (Debugging ke liye zaroori hai)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# ---------- Pyrogram Client ----------
bot = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

# ---------- Helper Functions ----------

async def handle_index(request):
    """Web Server ka response taaki Render sota na rahe"""
    return web.Response(text="Bot is Running Successfully!")

async def start_web_server():
    """Render ke liye Fake Web Server"""
    port = int(os.environ.get("PORT", "8080"))
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"🌍 Web Server Started on Port {port}")
    return runner

#━━━━━━━━━━━━━━━━━━━━ JOIN REQUEST (10 SEC DELAY) ━━━━━━━━━━━━━━━━━━━━
@bot.on_chat_join_request()
async def approve(client: Client, m: ChatJoinRequest):
    try:
        chat = m.chat
        user = m.from_user
        
        log.info(f"📥 New Request: {user.first_name} in {chat.title}")

        # Database me add karo
        try:
            add_group(chat.id)
            add_user(user.id)
        except Exception as e:
            log.error(f"DB Error: {e}")

        # ⏳ 10 SECOND WAIT
        await asyncio.sleep(10)

        # ✅ APPROVE REQUEST
        try:
            await client.approve_chat_join_request(chat.id, user.id)
            log.info(f"✅ Approved: {user.first_name}")
        except errors.UserAlreadyParticipant:
            pass
        except Exception as e:
            log.error(f"Approval Failed: {e}")
            return

        # ✅ WELCOME MESSAGE (DM)
        try:
            await client.send_message(
                user.id,
                f"👋 Hello {user.first_name}!\n\n"
                f"✅ Your request to join **{chat.title}** has been approved.\n"
                "🎉 Welcome!"
            )
        except Exception:
            pass # User blocked bot or privacy settings

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        log.error(f"Error in approve: {e}")

#━━━━━━━━━━━━━━━━━━━━ ILLEGAL WORDS (BAN FILTER) ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.group & filters.text)
async def illegal_filter(_, m: Message):
    if not m.from_user:
        return

    # Admin (SUDO) ko ignore karo
    if m.from_user.id in cfg.SUDO:
        return

    text = (m.text or "").lower()

    for word in cfg.ILLEGAL_WORDS:
        # Sirf exact word match karega (e.g. "Hell" won't delete "Hello")
        pattern = r"\b" + re.escape(word.lower()) + r"\b"
        
        if re.search(pattern, text):
            try:
                await m.delete()
                # Optional Warning
                msg = await m.reply(f"⚠️ {m.from_user.mention}, illegal words are not allowed!")
                await asyncio.sleep(5)
                await msg.delete()
            except Exception:
                pass
            break

#━━━━━━━━━━━━━━━━━━━━ START COMMAND ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    add_user(m.from_user.id)

    if m.from_user.id not in cfg.SUDO:
        await m.reply_text(
            "👋 **Hello!**\n"
            "I am an Auto Approver Bot.\n"
            "Join any of my groups and I will accept you after 10 seconds!"
        )
        return

    # Admin Panel
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("📢 Channel", url="https://t.me/lnx_store"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/teacher_slex")
        ]]
    )

    await m.reply_photo(
        photo="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhsaR6kRdTPF2ZMEgmgSYjjXU6OcsJhkBe1EWtI1nfbOziINTYzxjlGCMSVh-KoH05Z8MpRWhVV9TIX_ykpjdeGqJ1atXy1TUqrVkohUxlykoZyl67EfMQppHoWYrdHmdi6FMcL9v-Vew2VtaWHWY_eGZt-GN057jLGvYj7UV49g0rXVxoDFXQAYxvaX1xP/s1280/75447.jpg",
        caption=f"**👮‍♂️ Admin Panel**\n\nHello Boss {m.from_user.mention}!",
        reply_markup=keyboard
    )

#━━━━━━━━━━━━━━━━━━━━ USERS & GROUPS STATS ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def users_count(_, m: Message):
    # Aapke database.py ke functions call ho rahe hain
    u_count = all_users()
    g_count = all_groups()
    await m.reply_text(f"📊 **Stats:**\n\n👤 Users: `{u_count}`\n👥 Groups: `{g_count}`")

#━━━━━━━━━━━━━━━━━━━━ BROADCAST COMMAND ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def bcast(_, m: Message):
    if not m.reply_to_message:
        return await m.reply("❌ Please reply to a message to broadcast.")

    msg = await m.reply("⚡ Broadcasting started...")
    ok = 0
    fail = 0
    
    # Aapka database 'users' collection hai.
    # Aapke DB me user_id STRING format me hai, Pyrogram ko INT chahiye.
    all_users_cursor = users.find({}) 

    for person in all_users_cursor:
        try:
            # String ID ko Int me convert karna zaroori hai
            uid = int(person['user_id'])
            await m.reply_to_message.copy(uid)
            ok += 1
            await asyncio.sleep(0.1) # Floodwait se bachne ke liye
        except FloodWait as e:
            await asyncio.sleep(e.value)
            # Retry logic
            try:
                await m.reply_to_message.copy(uid)
                ok += 1
            except:
                fail += 1
        except Exception:
            fail += 1

    await msg.edit(f"✅ **Broadcast Complete**\n\nSuccess: {ok}\nFailed: {fail}")

# ---------- Main Execution ----------
async def main():
    # Web Server Start
    web_runner = await start_web_server()

    # Bot Start
    print("🤖 Bot Started...")
    await bot.start()
    
    # Idle state me rakhna
    await idle()

    # Stop process
    await bot.stop()
    await web_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")

