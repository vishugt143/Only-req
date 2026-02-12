# app.py
# Don't Remove Credit @teacher_slex
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import asyncio
import logging
from datetime import datetime
from aiohttp import web
from pyrogram import Client, filters, idle, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from pyrogram.errors.exceptions.flood_420 import FloodWait

# Database imports
from database import add_user, add_group, all_users, all_groups, users
from configs import cfg

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------- Pyrogram Client ----------
bot = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

# ------------------ HELPER FUNCTIONS FOR LOG ------------------
def add_to_log(user_id, name):
    """User ko log.txt me add karega"""
    try:
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{user_id} | {name} | {time_now}\n"
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"📝 Log Added: {name}")
    except Exception as e:
        print(f"Log Error: {e}")

def remove_from_log(user_id):
    """User ko log.txt se remove karega (Accept hone ke baad)"""
    try:
        if not os.path.exists("log.txt"):
            return

        # Saari lines padho
        with open("log.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Wapis write karo, lekin us user wali line ko chhod kar
        with open("log.txt", "w", encoding="utf-8") as f:
            for line in lines:
                if str(user_id) not in line:
                    f.write(line)
        print(f"🗑️ Log Removed: {user_id}")
    except Exception as e:
        print(f"Remove Log Error: {e}")

#━━━━━━━━━━━━━━━━━━━━ JOIN REQUEST HANDLER ━━━━━━━━━━━━━━━━━━━━
@bot.on_chat_join_request()
async def approve(client, m: ChatJoinRequest):
    try:
        chat = m.chat
        user = m.from_user
        
        # 1. PEHLE LOG ME SAVE KARO (Pending List)
        add_to_log(user.id, user.first_name)

        # Database me add karo
        add_group(chat.id)
        add_user(user.id)

        # ⏳ 2. 10 SECOND WAIT
        await asyncio.sleep(10)

        # ✅ 3. APPROVE REQUEST
        try:
            await client.approve_chat_join_request(chat.id, user.id)
        except errors.UserAlreadyParticipant:
            pass
        except Exception as e:
            # Agar approve fail hua, to log se mat hatao (optional logic)
            print(f"Approval Failed: {e}")
            return 

        # 🗑️ 4. LOG SE REMOVE KARO (Kyunki Accept ho gaya)
        remove_from_log(user.id)

        # 👋 WELCOME MESSAGE
        try:
            await client.send_message(
                user.id,
                f"👋 Hello {user.first_name}!\n\n"
                "✅ Aapka join request approve ho gaya hai.\n"
                "🎉 Welcome to the group!"
            )
        except Exception:
            pass

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        log.exception(f"Error: {e}")

#━━━━━━━━━━━━━━━━━━━━ ILLEGAL WORD DELETE ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.group & filters.text)
async def illegal_filter(_, m: Message):
    if not m.from_user: return
    if m.from_user.id in cfg.SUDO: return

    text = (m.text or "").lower()

    for word in cfg.ILLEGAL_WORDS:
        pattern = r"\b" + re.escape(word.lower()) + r"\b"
        if re.search(pattern, text):
            try:
                await m.delete()
                try:
                    msg = await m.reply(f"⚠️ {m.from_user.mention}, ye word allowed nahi hai.")
                    await asyncio.sleep(5)
                    await msg.delete()
                except: pass
            except: pass
            break

#━━━━━━━━━━━━━━━━━━━━ START COMMAND ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    add_user(m.from_user.id)
    
    if m.from_user.id not in cfg.SUDO:
        await m.reply_text("👋 Hello! Join my group to get approved.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel", url="https://t.me/lnx_store")]
    ])
    
    await m.reply_photo(
        photo="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhsaR6kRdTPF2ZMEgmgSYjjXU6OcsJhkBe1EWtI1nfbOziINTYzxjlGCMSVh-KoH05Z8MpRWhVV9TIX_ykpjdeGqJ1atXy1TUqrVkohUxlykoZyl67EfMQppHoWYrdHmdi6FMcL9v-Vew2VtaWHWY_eGZt-GN057jLGvYj7UV49g0rXVxoDFXQAYxvaX1xP/s1280/75447.jpg",
        caption=f"**🦊 Admin Panel**\n\nActive! Logs are managed automatically.",
        reply_markup=keyboard
    )

#━━━━━━━━━━━━━━━━━━━━ BROADCAST & STATS ━━━━━━━━━━━━━━━━━━━━
@bot.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def users_count(_, m: Message):
    u = all_users()
    g = all_groups()
    await m.reply_text(f"📊 Total Users: `{u}`\n👥 Total Groups: `{g}`")

@bot.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def bcast(_, m: Message):
    if not m.reply_to_message:
        return await m.reply("Reply to a message to broadcast.")
    
    status = await m.reply("⚡ Broadcasting...")
    ok = fail = 0
    all_db_users = users.find({}) 

    for person in all_db_users:
        try:
            uid = int(person['user_id'])
            await m.reply_to_message.copy(uid)
            ok += 1
            await asyncio.sleep(0.1)
        except:
            fail += 1

    await status.edit(f"✅ Sent: {ok} | ❌ Failed: {fail}")

#━━━━━━━━━━━━━━━━━━━━ WEB SERVER & MAIN ━━━━━━━━━━━━━━━━━━━━
async def handle_index(request):
    return web.Response(text="Bot is Running!")

async def start_web_server():
    port = int(os.environ.get("PORT", "8080"))
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner

async def main():
    await start_web_server()
    await bot.start()
    print("✅ Bot Started! (Log Feature Enabled)")
    await idle()
    await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

