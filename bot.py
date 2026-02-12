# app.py
# Don't Remove Credit @teacher_slex
# Subscribe YouTube ƈɦǟռռɛʟ For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters, idle, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from pyrogram.errors.exceptions.flood_420 import FloodWait

# Aapki database aur config files waisi ki waisi rahengi
from database import add_user, add_group, all_users, all_groups, users
from configs import cfg

# Logging Setup (Render logs dekhne ke liye zaroori hai)
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

#━━━━━━━━━━━━━━━━━━━━ HELPER ━━━━━━━━━━━━━━━━━━━━
def parse_post_link(link: str):
    parts = link.split("/")
    chat = parts[-2]
    msg_id = int(parts[-1])
    return chat, msg_id

#━━━━━━━━━━━━━━━━━━━━ JOIN REQUEST (10 SEC DELAY + WELCOME) ━━━━━━━━━━━━━━━━━━━━
@bot.on_chat_join_request()
async def approve(client: Client, m: ChatJoinRequest):
    try:
        chat = m.chat
        user = m.from_user
        
        # Log print karega
        log.info(f"📥 New Request: {user.first_name} in {chat.title}")

        # Database update
        add_group(chat.id)
        add_user(user.id)

        # ⏳ 10 SECOND WAIT
        await asyncio.sleep(10)

        # ✅ APPROVE REQUEST
        try:
            await client.approve_chat_join_request(chat.id, user.id)
            log.info(f"✅ Approved: {user.first_name}")
        except errors.UserAlreadyParticipant:
            pass
        except Exception as e:
            log.error(f"Approval Error: {e}")
            return

        # ✅ WELCOME MESSAGE (DM)
        try:
            await client.send_message(
                user.id,
                f"👋 Hello {user.first_name}!\n\n"
                f"✅ Aapka join request **{chat.title}** me approve ho gaya hai.\n"
                "🎉 Welcome to the group!"
            )
        except Exception:
            # Agar user ne bot block kiya ho to ignore karo
            pass

    except FloodWait as e:
        log.warning(f"FloodWait: Sleeping for {e.value}s")
        await asyncio.sleep(e.value)
        # Retry logic optional
    except Exception as e:
        log.exception("Error in approve handler")

#━━━━━━━━━━━━━━━━━━━━ ILLEGAL WORD DELETE (BAN WORDS) ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.group & filters.text)
async def illegal_filter(_, m: Message):
    if not m.from_user:
        return

    # 🔹 SUDO exempt (Admin ko ignore karega)
    if m.from_user.id in cfg.SUDO:
        return

    text = (m.text or "").lower()

    for word in cfg.ILLEGAL_WORDS:
        # Regex taaki "hello" me "hell" match na kare (Sirf exact word pakdega)
        pattern = r"\b" + re.escape(word.lower()) + r"\b"
        
        if re.search(pattern, text):
            try:
                # Delete message
                await m.delete()

                # Warning message
                try:
                    sent = await m.chat.send_message(
                        f"⚠️ {m.from_user.mention}, ye shabd allowed nahi hain. Aapka message delete kar diya gaya."
                    )
                    # 5 second baad warning delete kar do taaki chat gandi na ho
                    await asyncio.sleep(5)
                    await sent.delete()
                except Exception:
                    pass
            except Exception:
                pass
            break

#━━━━━━━━━━━━━━━━━━━━ AUTO-DELETE FOR MY MESSAGES (filters.me) ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.me)
async def auto_delete_illegal(_, m: Message):
    try:
        content = ""
        if m.text:
            content = m.text.lower()
        elif m.caption:
            content = m.caption.lower()

        for word in cfg.ILLEGAL_WORDS:
            if word.lower() in content:
                await asyncio.sleep(0.1)
                await m.delete()
                return
    except Exception:
        pass

#━━━━━━━━━━━━━━━━━━━━ START COMMAND ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    add_user(m.from_user.id)

    # Agar user SUDO list me nahi hai
    if m.from_user.id not in cfg.SUDO:
        await m.reply_text(
            "𝐁𝐇𝐀𝐈 𝐇𝐀𝐂𝐊 𝐒𝐄 𝐏𝐋𝐀𝐘 𝐊𝐑𝐎\n\n💸𝐏𝐑𝐎𝐅𝐈𝐓 𝐊𝐑𝐎🍻"
        )
        return

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🗯 ƈɦǟռռɛʟ", url="https://t.me/lnx_store"),
            InlineKeyboardButton("💬 Support", url="https://t.me/teacher_slex")
        ]]
    )

    await m.reply_photo(
        photo="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhsaR6kRdTPF2ZMEgmgSYjjXU6OcsJhkBe1EWtI1nfbOziINTYzxjlGCMSVh-KoH05Z8MpRWhVV9TIX_ykpjdeGqJ1atXy1TUqrVkohUxlykoZyl67EfMQppHoWYrdHmdi6FMcL9v-Vew2VtaWHWY_eGZt-GN057jLGvYj7UV49g0rXVxoDFXQAYxvaX1xP/s1280/75447.jpg",
        caption=(
            f"**🦊 Hello {m.from_user.mention}!**\n\n"
            "I'm an auto approve bot.\n"
            "I handle join requests & DM users.\n\n"
            "📢 Broadcast : /bcast\n"
            "📊 Users : /users\n\n"
            "__Powered By : @teacher_slex__"
        ),
        reply_markup=keyboard
    )

#━━━━━━━━━━━━━━━━━━━━ USERS COUNT ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def users_count(_, m: Message):
    u = all_users()
    g = all_groups()
    await m.reply_text(f"🙋 Users : `{u}`\n👥 Groups : `{g}`\n📊 Total : `{u+g}`")

#━━━━━━━━━━━━━━━━━━━━ BROADCAST ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def bcast(_, m: Message):
    if not m.reply_to_message:
        return await m.reply("Reply to a message to broadcast.")

    status = await m.reply("⚡ Broadcasting...")
    ok = fail = 0

    # Database se saare users ko fetch karke message bhejna
    all_db_users = users.find()  # Aapke database variable ka naam
    
    for u in all_db_users:
        try:
            await m.reply_to_message.copy(u["user_id"])
            ok += 1
            await asyncio.sleep(0.1) # Thoda delay taaki floodwait na aaye
        except Exception:
            fail += 1

    await status.edit(f"✅ Success: {ok} | ❌ Failed: {fail}")

# ---------- Web Server for Render (Keep Alive) ----------
async def handle_index(request):
    return web.Response(text="🤖 Bot is alive and running!")

async def start_web_server():
    # Render PORT env variable automatic utha lega
    port = int(os.environ.get("PORT", "8080"))
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"🌍 Web server started on port {port}")
    return runner

# ---------- Main Loop ----------
async def main():
    # 1. Start Web Server
    web_runner = await start_web_server()

    # 2. Start Bot
    print("🤖 Bot Starting...")
    await bot.start()
    print("✅ Bot is Online!")

    # 3. Idle Loop
    try:
        await idle()
    except KeyboardInterrupt:
        pass
    finally:
        await bot.stop()
        await web_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

